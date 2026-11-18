"""Phase 2: render structured evidence as text, extract it back, measure extraction error.

  python -m pipeline.procbench.toy_statute.text_roundtrip render  --world runs/.../W0
  python -m pipeline.procbench.toy_statute.text_roundtrip extract --world runs/.../W0
  python -m pipeline.procbench.toy_statute.text_roundtrip compare --world runs/.../W0

render:  evidence/*.json -> text_evidence/{posts.json, webpages_text.json, admin_records.json}
extract: text_evidence -> extracted_evidence/ (same schema as evidence/, fit-ready)
compare: extraction error vs the structured records (field-level)

Rendering and extraction are separate tool-less `claude -p` calls. The
extractor sees only text_evidence/ (plus the public spec), never evidence/.
"""

from __future__ import annotations

import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import spec
from .llm_baseline import call_claude, extract_json

RENDER_MODEL = "sonnet"
EXTRACT_MODEL = "sonnet"

EVENT_GLOSS = {"submitted": "sent in the application", "told_incomplete": "was told the application was incomplete / asked for corrections",
               "inspection": "the inspector visited", "hearing": "the hearing was held", "decision": "got the permit decision"}
MENTION_GLOSS = {"correction": "having to correct/resubmit the application", "neighbor_notice": "neighbours being sent notice letters",
                 "site_inspection": "a site inspection visit", "hearing": "a public hearing"}


def render_posts_prompt(town, reports):
    return f"""You are generating synthetic forum posts for a research benchmark. Each record below is one resident of {town} describing their own backyard-hen permit application.
Write each as a short, casual post in a local forum (like a subreddit for {town}). Rules — follow exactly:
- status "pending": they applied `days_since_submission` days ago and have no decision yet. State that number of days (you may phrase it as "{{n}} days ago"). Mention no other steps or numbers.
- status "decided": they got their decision.
- Each gap is the time between two events; express it with the SAME value and unit (value 3 unit week -> "3 weeks"/"about three weeks"; value 9 unit day -> "9 days"; value 0 unit day -> "the same day"; value 2 unit month -> "2 months"). Events: {json.dumps(EVENT_GLOSS)}.
- Mention exactly the steps whose mentions flag is true ({json.dumps(MENTION_GLOSS)}), and say nothing that implies the false ones happened. A mentioned step need not have a time.
- If hours_total is present, say roughly how many hours of their own time it took in total, using that number. If fees_paid_total is present, say they paid that many dollars in fees in total.
- Add no other numbers, dates, fees, durations or steps. Vary the tone and wording; typos are fine; keep each under 120 words.
Return ONLY a JSON list: [{{"report_id": ..., "text": ...}}, ...] in the same order.
RECORDS:
{json.dumps(reports)}"""


def render_web_prompt(webpages):
    return f"""You are generating synthetic municipal web pages for a research benchmark. For each town below, write a short "Backyard hen permits" page (under 150 words) in plain agency language.
Describe as process steps ONLY the steps whose listed_steps flag is true (step names: completeness_check = staff check that the application is complete; neighbor_notice = notice mailed to adjoining neighbours; comment_period = neighbour comment period; desk_review = staff review of the site plan; hearing = public hearing if a neighbour objects; site_inspection = inspector visits the site; decision_issue = permit decision letter issued).
Do not describe or hint at steps whose flag is false. State the fee schedule exactly (item and dollar amount) and no other fees. Do not state durations.
Return ONLY a JSON object {{"<town>": "<page text>", ...}}.
TOWNS:
{json.dumps(webpages)}"""


def extract_posts_prompt(town, posts):
    return f"""Extract structured records from forum posts by backyard-hen permit applicants in {town}. Use ONLY what each post states.
For each post output:
{{"report_id", "status": "decided" or "pending",
 "days_since_submission": integer (pending only: days since they applied),
 "mentions": {{"correction": bool, "neighbor_notice": bool, "site_inspection": bool, "hearing": bool}}  (true only if the post says it happened),
 "gaps": [{{"from": event, "to": event, "value": number, "unit": "day"|"week"|"month"}}]  (decided only; consecutive stated intervals between events; events: submitted, told_incomplete, inspection, hearing, decision; keep the post's own unit and number; "same day" = value 0 unit day),
 "hours_total": number (only if stated), "fees_paid_total": number (only if stated)}}
Omit hours_total / fees_paid_total if not stated. Return ONLY a JSON list in input order.
POSTS:
{json.dumps(posts)}"""


def extract_web_prompt(pages):
    steps = spec.LISTABLE
    return f"""For each town's permit web page below, output which process steps the page describes and the fee schedule it states.
Steps (true/false each): {steps}. Meanings: completeness_check = check the application is complete; neighbor_notice = notice to neighbours; comment_period = neighbour comment period; desk_review = staff review of site plan; hearing = hearing; site_inspection = inspector site visit; decision_issue = separate decision letter/issuance.
Fee items: application, notice, inspection (dollar amounts; include only fees stated).
Return ONLY JSON: {{"<town>": {{"listed_steps": {{step: bool}}, "fee_schedule": {{item: amount}}}}}}
PAGES:
{json.dumps(pages)}"""


def _call(prompt, model):
    rc, so, se = call_claude(prompt, model)
    res = json.loads(so)
    return extract_json_any(res["result"]), res.get("total_cost_usd")


def extract_json_any(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1].rsplit("```", 1)[0]
    i = min([x for x in (t.find("["), t.find("{")) if x >= 0])
    j = max(t.rfind("]"), t.rfind("}"))
    return json.loads(t[i:j + 1])


def render(world):
    ev = world / "evidence"
    out = world / "text_evidence"
    out.mkdir(exist_ok=True)
    reports = json.loads((ev / "reports.json").read_text())
    towns = json.loads((ev / "public_spec.json").read_text())["towns"]
    webp = json.loads((ev / "webpages.json").read_text())
    jobs = [("posts", t, render_posts_prompt(t, [r for r in reports if r["town"] == t])) for t in towns]
    jobs.append(("web", None, render_web_prompt(webp)))
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda j: (j[0], j[1], _call(j[2], RENDER_MODEL)), jobs))
    posts, cost = [], 0.0
    pages = None
    for kind, t, (obj, c) in res:
        cost += c or 0
        if kind == "posts":
            for r in obj:
                posts.append({"report_id": r["report_id"], "town": t, "text": r["text"]})
        else:
            pages = obj
    (out / "posts.json").write_text(json.dumps(posts, indent=1))
    (out / "webpages_text.json").write_text(json.dumps(pages, indent=1))
    shutil.copy(ev / "admin_records.json", out / "admin_records.json")
    shutil.copy(ev / "public_spec.json", out / "public_spec.json")
    (out / "render_manifest.json").write_text(json.dumps({"model": RENDER_MODEL, "cost_usd": cost,
                                                           "n_posts": len(posts)}, indent=1))
    print(f"rendered {len(posts)} posts, {len(pages)} pages, cost ${cost:.2f}")


def extract(world):
    te = world / "text_evidence"
    out = world / "extracted_evidence"
    out.mkdir(exist_ok=True)
    posts = json.loads((te / "posts.json").read_text())
    pages = json.loads((te / "webpages_text.json").read_text())
    towns = json.loads((te / "public_spec.json").read_text())["towns"]
    jobs = [("posts", t, extract_posts_prompt(t, [{"report_id": p["report_id"], "text": p["text"]}
                                                  for p in posts if p["town"] == t])) for t in towns]
    jobs.append(("web", None, extract_web_prompt(pages)))
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda j: (j[0], j[1], _call(j[2], EXTRACT_MODEL)), jobs))
    reports, cost, web = [], 0.0, {}
    for kind, t, (obj, c) in res:
        cost += c or 0
        if kind == "posts":
            for r in obj:
                r["town"] = t
                reports.append(r)
        else:
            for town, v in obj.items():
                ls = {s: bool(v.get("listed_steps", {}).get(s, False)) for s in spec.LISTABLE}
                web[town] = {"town": town, "listed_steps": ls, "fee_schedule": v.get("fee_schedule", {})}
    order = {p["report_id"]: i for i, p in enumerate(posts)}
    reports.sort(key=lambda r: order.get(r["report_id"], 1e9))
    for r in reports:  # normalize to evidence schema
        if r.get("status") == "pending":
            for k in ("mentions", "gaps", "hours_total", "fees_paid_total"):
                r.pop(k, None)
        else:
            r.pop("days_since_submission", None)
            r["mentions"] = {m: bool(r.get("mentions", {}).get(m, False)) for m in spec.MENTIONABLE}
            r["gaps"] = [g for g in r.get("gaps", []) if g.get("from") in spec.TIMEABLE_EVENTS
                         and g.get("to") in spec.TIMEABLE_EVENTS and g.get("unit") in ("day", "week", "month")]
    (out / "reports.json").write_text(json.dumps(reports, indent=1))
    (out / "webpages.json").write_text(json.dumps(web, indent=1))
    shutil.copy(te / "admin_records.json", out / "admin_records.json")
    shutil.copy(te / "public_spec.json", out / "public_spec.json")
    (out / "extract_manifest.json").write_text(json.dumps({"model": EXTRACT_MODEL, "cost_usd": cost,
                                                            "n_reports": len(reports)}, indent=1))
    print(f"extracted {len(reports)} reports, cost ${cost:.2f}")


def compare(world):
    a = {r["report_id"]: r for r in json.loads((world / "evidence" / "reports.json").read_text())}
    b = {r["report_id"]: r for r in json.loads((world / "extracted_evidence" / "reports.json").read_text())}
    stats = {"reports": len(a), "missing": [k for k in a if k not in b], "status_err": 0,
             "pending_N_err": 0, "mention_err": 0, "mention_n": 0, "gap_set_err": 0, "gap_value_err": 0,
             "hours_err": 0, "hours_n": 0, "fees_err": 0, "fees_n": 0, "records_exact": 0, "errors": []}
    for k, r in a.items():
        e = b.get(k)
        if e is None:
            continue
        exact = True
        if e.get("status") != r["status"]:
            stats["status_err"] += 1
            stats["errors"].append((k, "status"))
            continue
        if r["status"] == "pending":
            if int(e.get("days_since_submission", -1)) != r["days_since_submission"]:
                stats["pending_N_err"] += 1
                exact = False
                stats["errors"].append((k, "pending_N"))
        else:
            for m in spec.MENTIONABLE:
                stats["mention_n"] += 1
                if bool(e["mentions"][m]) != r["mentions"][m]:
                    stats["mention_err"] += 1
                    exact = False
                    stats["errors"].append((k, f"mention:{m}"))
            ga = [(g["from"], g["to"]) for g in r["gaps"]]
            gb = [(g["from"], g["to"]) for g in e["gaps"]]
            if ga != gb:
                stats["gap_set_err"] += 1
                exact = False
                stats["errors"].append((k, f"gaps:{ga}->{gb}"))
            else:
                for x, y in zip(r["gaps"], e["gaps"]):
                    if (x["value"], x["unit"]) != (float(y["value"]) if float(y["value"]) % 1 else int(y["value"]), y["unit"]):
                        stats["gap_value_err"] += 1
                        exact = False
                        stats["errors"].append((k, f"gapval:{x}->{y}"))
            for fld, cnt, err in (("hours_total", "hours_n", "hours_err"), ("fees_paid_total", "fees_n", "fees_err")):
                if fld in r or fld in e:
                    stats[cnt] += 1
                    if fld not in r or fld not in e or abs(float(r[fld]) - float(e[fld])) > 1e-9:
                        stats[err] += 1
                        exact = False
                        stats["errors"].append((k, fld))
        stats["records_exact"] += int(exact)
    wa = json.loads((world / "evidence" / "webpages.json").read_text())
    wb = json.loads((world / "extracted_evidence" / "webpages.json").read_text())
    stats["web_step_err"] = sum(int(wa[t]["listed_steps"][s] != wb.get(t, {}).get("listed_steps", {}).get(s))
                                for t in wa for s in spec.LISTABLE)
    stats["web_fee_err"] = sum(int({k: float(v) for k, v in wa[t]["fee_schedule"].items()}
                                   != {k: float(v) for k, v in wb.get(t, {}).get("fee_schedule", {}).items()}) for t in wa)
    (world / "extracted_evidence" / "extraction_error.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps({k: v for k, v in stats.items() if k != "errors"}, indent=1))
    print("errors:", stats["errors"][:40])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "extract", "compare"])
    ap.add_argument("--world", required=True)
    a = ap.parse_args()
    {"render": render, "extract": extract, "compare": compare}[a.cmd](Path(a.world))


if __name__ == "__main__":
    main()
