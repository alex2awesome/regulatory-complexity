"""Render a world's structured evidence as free text (blind process round, 2026-09-30).

  PYTHONPATH=. python3 -m pipeline.procbench.toy_statute.render_text --world runs/toy_statute3_20260930/HEN3

Deterministic templates, no LLM. Web pages become prose with town-specific synonyms for each step;
applicant reports become short first-person narratives; admin records become one CSV per town with
town-specific column labels. Writes <world>/evidence_text/ (public) and <world>/truth/render_key.json
(evaluator only: which phrase stood for which step/event).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

# agency-voice phrases for web pages, one chosen per town
WEB = {
    "completeness_check": ["Staff first check that your application is complete.",
                           "We review the submission for completeness before anything else.",
                           "An intake clerk confirms the application package is complete."],
    "signature_collection": ["You must collect signed consent forms from every adjoining property owner and file them with us.",
                             "Before review, obtain signatures from all abutting neighbours on our consent form.",
                             "Applicants gather neighbour sign-off sheets from adjacent owners and submit them."],
    "neighbor_notice": ["We mail a notice to the owners of adjoining properties.",
                        "Courtesy letters go out to abutting neighbours.",
                        "The department notifies adjacent property owners by mail."],
    "comment_period": ["Neighbours then have 14 days to send comments.",
                       "A two-week public comment window follows.",
                       "There is a 14-day period for neighbour comments."],
    "desk_review": ["Planning staff review your site plan.",
                    "A plan check of the coop location is done in the office.",
                    "Staff conduct a desk review of the site plan and setbacks."],
    "hearing": ["If a neighbour objects, the application goes to a hearing before the zoning board.",
                "Objections are heard by the board of appeals at a public hearing.",
                "Should anyone object, a hearing is scheduled before a decision."],
    "site_inspection": ["An inspector visits the property to look at the coop site.",
                        "A field inspection of the proposed coop location is required.",
                        "Code enforcement makes a site visit."],
    "decision_issue": ["You will receive a written decision.",
                       "The permit (or denial) is mailed to you.",
                       "A decision letter is issued at the end."],
}
SHARED_DECISION_WEB = ["The inspector issues the permit on the spot if everything checks out.",
                       "Permits are handed over at the site visit when the coop location passes."]
# applicant-voice phrases
MENTION = {
    "correction": ["Had to fix something on my application and resubmit.", "They bounced my application once for a missing item."],
    "signature_collection": ["I had to go door to door to get my neighbours to sign a form.", "Getting the neighbour signatures was the annoying part."],
    "neighbor_notice": ["They sent letters to my neighbours.", "My neighbours got a notice in the mail about it."],
    "site_inspection": ["Someone came out to look at where the coop would go.", "They did a site visit."],
    "hearing": ["A neighbour objected so I had to go to a hearing.", "Ended up at a board hearing because of an objection."],
}
EVENT = {
    "told_incomplete": ["they told me my application was incomplete", "I got a notice that something was missing"],
    "app_complete": ["they said my application was complete", "my application was accepted as complete"],
    "signatures_filed": ["I turned in the neighbour signatures", "I finally had all my neighbours' signatures filed"],
    "notice_mailed": ["they mailed the neighbour notices", "the letters to my neighbours went out"],
    "review_complete": ["they finished reviewing my site plan", "the plan review was done"],
    "hearing": ["I had my hearing", "the board heard my case"],
    "inspection": ["the inspector came out", "they did the site visit"],
    "decision": ["I got the decision", "my permit decision came through"],
}
ADMIN_LABELS = {
    "case_id": ["Case No", "Permit #", "Record ID"],
    "submitted": ["Date Received", "Applied", "Intake Date"],
    "deemed_complete": ["Deemed Complete", "App Complete Date", "Completeness Determination"],
    "inspection": ["Insp Date", "Site Visit", "Field Inspection"],
    "hearing": ["Hearing Date", "ZBA Hearing", "Board Date"],
    "decided": ["Final Action Date", "Decision Date", "Issued/Denied"],
}
FEE_LABELS = {"application": ["Application fee", "Permit application fee"],
              "notice": ["Neighbour notification fee", "Mailing fee"],
              "inspection": ["Inspection fee", "Site visit fee"],
              "course": ["Course fee"]}


def _dur(v, unit):
    if unit == "day":
        return "1 day" if v == 1 else f"{v} days"
    if unit == "week":
        return "a week" if v == 1 else f"{v} weeks"
    return "a month" if v == 1 else f"{v} months"


def render(world_dir: Path, seed: int = 7):
    world_dir = Path(world_dir)
    ev = world_dir / "evidence"
    out = world_dir / "evidence_text"
    if out.exists():
        raise FileExistsError(out)
    out.mkdir()
    w = json.loads((world_dir / "truth" / "world.json").read_text())
    rng = np.random.default_rng(seed)
    key = {"web": {}, "reports": {}, "admin": {}}
    # web pages
    pages = json.loads((ev / "webpages.json").read_text())
    order = ["completeness_check", "signature_collection", "neighbor_notice", "comment_period", "desk_review",
             "hearing", "site_inspection", "decision_issue"]
    lines = []
    for town, pg in pages.items():
        choice = {s: int(rng.integers(len(WEB[s]))) for s in WEB}
        shared = w["structure"][town] in {k for k, v in _designs(w).items() if v["shared_decision"]}
        sents = ["Submit the application form together with a site plan of the coop."]
        used = {}
        for s in order:
            if pg["listed_steps"].get(s):
                if s == "decision_issue":
                    continue
                sents.append(WEB[s][choice[s]]); used[s] = WEB[s][choice[s]]
        if pg["listed_steps"].get("decision_issue"):
            sents.append(WEB["decision_issue"][choice["decision_issue"]]); used["decision_issue"] = WEB["decision_issue"][choice["decision_issue"]]
        elif shared and pg["listed_steps"].get("site_inspection"):
            sd = SHARED_DECISION_WEB[int(rng.integers(len(SHARED_DECISION_WEB)))]
            sents.append(sd); used["shared_decision_at_inspection"] = sd
        fees = []
        for item, amt in pg["fee_schedule"].items():
            lab = FEE_LABELS.get(item, [item.capitalize() + " fee"])[int(rng.integers(len(FEE_LABELS.get(item, [0]))))]
            fees.append(f"{lab}: ${amt}."); used[f"fee:{item}"] = lab
        lines.append(f"## {town} — backyard hen permit\n\n" + " ".join(sents) + ("\n\nFees. " + " ".join(fees) if fees else "") + "\n")
        key["web"][town] = used
    (out / "webpages.md").write_text("# Town web pages\n\n" + "\n".join(lines))
    # reports
    reps = json.loads((ev / "reports.json").read_text())
    rows = []
    for r in reps:
        k = {}
        if r["status"] == "pending":
            text = f"Applied for a hen permit about {r['days_since_submission']} days ago and still waiting to hear back."
        else:
            timed = {g["to"] for g in r["gaps"]}
            ev_of = {"correction": "told_incomplete", "signature_collection": "signatures_filed",
                     "hearing": "hearing", "site_inspection": "inspection"}
            parts = []
            for i, g in enumerate(r["gaps"]):
                ph = EVENT[g["to"]][int(rng.integers(2))]
                lead = "after I applied" if i == 0 else "after that"
                parts.append(f"{_dur(g['value'], g['unit']).capitalize()} {lead}, {ph}.")
                k[f"gap{i}"] = {"from": g["from"], "to": g["to"], "phrase": ph}
            extra = []
            for m, on in r["mentions"].items():
                if on and ev_of.get(m) not in timed:
                    s_ = MENTION[m][int(rng.integers(2))]; extra.append(s_); k[f"mention:{m}"] = s_
            if extra:
                pos = int(rng.integers(0, len(parts) + 1))
                parts = parts[:pos] + extra + parts[pos:]
            if "hours_total" in r:
                parts.append(f"All in, about {r['hours_total']:g} hours of my time.")
            if "fees_paid_total" in r:
                parts.append(f"Paid ${r['fees_paid_total']} in fees.")
            text = " ".join(parts)
        rows.append({"report_id": r["report_id"], "town": r["town"], "text": text})
        key["reports"][r["report_id"]] = k
    with (out / "reports.jsonl").open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    # admin
    adm = json.loads((ev / "admin_records.json").read_text())
    for town in sorted({a["town"] for a in adm}):
        labs = {f: ADMIN_LABELS[f][int(rng.integers(len(ADMIN_LABELS[f])))] for f in ADMIN_LABELS}
        key["admin"][town] = labs
        fields = ["case_id", "submitted", "deemed_complete", "inspection", "hearing", "decided"]
        with (out / f"admin_{town}.csv").open("w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow([labs[x] for x in fields])
            for a in adm:
                if a["town"] != town:
                    continue
                ms = a.get("milestones", {})
                wr.writerow([a["case_id"], a["submitted"], ms.get("deemed_complete", ""), ms.get("inspection", ""),
                             ms.get("hearing", ""), a["decided"]])
    ps = json.loads((ev / "public_spec.json").read_text())
    pub = {"statute": ps["statute"], "d_steps": ps["d_steps"], "towns": ps["towns"], "posting": ps["posting"],
           "reporting_note": "Applicant reports are free text posted online; admin CSVs are exports from the towns that keep records.",
           "files": sorted(p.name for p in out.iterdir())}
    (out / "public_context.json").write_text(json.dumps(pub, indent=1) + "\n")
    (world_dir / "truth" / "render_key.json").write_text(json.dumps(key, indent=1) + "\n")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}


def _designs(w):
    return json.loads(Path(w["package_path"]).read_text())["design_space"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    a = ap.parse_args()
    print(json.dumps(render(Path(a.world)), indent=1))


if __name__ == "__main__":
    main()
