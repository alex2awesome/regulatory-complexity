"""Materialize the SOL001 whole-thread semantic review packet.

This is a staging review (root_adopted=false), not model input.  It binds exact
quotes to the retained raw JSON and records full 11-step narrative checklists.
"""
from __future__ import annotations

import csv, hashlib, json
from pathlib import Path

from .solar_forum_bridge import BLOCK, PANEL, ROOT, slug

THREADS = "10abxg7 10bdub6 10ez6hd 10gqvoq 10h78kd 10i1jgy 10n3277 11102ka 111n7q4 11azrsl 11kqeg2 11ttrzl 123j7fu 1240ozt 12bmk4h 15gur8l 15hitou 17hf4j7 1aezusd 1dzc6i0".split()
DESCRIPTIVE_ONLY = {"10abxg7", "10n3277", "111n7q4", "11ttrzl"}
RAW = ROOT / "runs/solar_forum_20260922/acquisition/forum/posts"
OUT = ROOT / "runs/solar_forum_20260922/model_bridge/parse"

# thread, author, California/context quote, {step: occurrence quote}, note
SPECS = [
 ("10abxg7","mathakoot","PG&E",{},"California pre-installation design inquiry; no AHJ act reported as completed."),
 ("10abxg7","bripsu","Bay Area",{},"Own Bay Area solar/battery system; no AHJ act narrated."),
 ("10abxg7","Panda_Pam","solar quotes",{},"Own pending quote process; no performed AHJ act."),
 ("10bdub6","drgath","Marin County, CA",{"solar_permit__ahj_permit_application_submission":"the county permit was filed"},"Own Marin installation; final inspection explicitly blocked, not counted as performed."),
 ("10bdub6","SisyphusRuns","SGIP rebate",{},"Own operational California SGIP case; no AHJ action narrated."),
 ("10ez6hd","ideal2545","north of los angeles",{"solar_permit__ahj_final_inspection":"They scheduled an inspection about a week later and of course, it failed"},"Own installation; one failed inspection occurred. Plural complaint language is not enough to assert a separate reinspection."),
 ("10ez6hd","Acefr","Bay Area",{},"Own Bay Area installation experience, but no AHJ act in the reviewed comments."),
 ("10ez6hd","treo650","LA solar group",{},"Own installation/roof problem; no AHJ action narrated."),
 ("10gqvoq","Stuporchampion","Santa Barbara, CA area",{},"Own planned installation; billing/interconnection discussion only."),
 ("10h78kd","jukaszor","California",{},"Own pending order; no completed AHJ act."),
 ("10h78kd","Puzzleheaded_Look959","Final inspection next Friday",{},"Own installation, but inspection is future and therefore not an occurrence."),
 ("10n3277","xanatos666","Norcal SF Bay Area",{},"Quote evaluation; no completed AHJ act."),
 ("11102ka","YoungGrassahsh","PG&E",{},"Own existing system; utility PTO only, no AHJ occurrence narrated."),
 ("111n7q4","Hogriderrr10291","SoCal",{},"Pre-installation inquiry; no AHJ occurrence."),
 ("111n7q4","humjaba","Southern California",{},"Own installed system; no AHJ occurrence narrated."),
 ("111n7q4","positiverealm","approved NEM application",{},"Own California-policy-context new build; utility application only."),
 ("111n7q4","OompaOrangeFace","Tesla only took 3 weeks from order to install for me",{},"Own installation; no AHJ action narrated."),
 ("111n7q4","ash_274","SDG&E",{},"Own installer-selection experience; no AHJ action narrated."),
 ("111n7q4","fatlardo","nem 2",{},"Own pending Tesla project; no performed AHJ action."),
 ("11azrsl","holdyourthrow","April 13",{},"California-policy context is probable but locality is weak; unrelated permit issue is not recoded as solar action."),
 ("11ttrzl","bonzie","SF Bay Area",{},"Quote selection; promised future paperwork is not occurrence."),
 ("123j7fu","bakchodbaba","PGE",{},"Hypothetical permit question; no permit submission occurrence."),
 ("1240ozt","Random_Fotographer","bay area",{"solar_permit__ahj_final_inspection":"city inspection passed two days later","solar_permit__ahj_final_approval":"city inspection passed two days later"},"Own project; passed city inspection."),
 ("1240ozt","Unusual_Meringue_703","southern Cal",{"solar_permit__ahj_final_approval":"copy of my final permit"},"Own project; final permit existed. The phrase 'without the final inspection' describes application timing and is not inspection-occurrence evidence."),
 ("1240ozt","Chris4AMC_TO-DA-MOON","PG&E",{"solar_permit__ahj_final_inspection":"I just passed inspection","solar_permit__ahj_final_approval":"I just passed inspection"},"Own California/PG&E project; final inspection passed."),
 ("15gur8l","TransportationNo8071","NEM 2.0",{"solar_permit__ahj_permit_application_submission":"He quickly got permits submitted","solar_permit__ahj_permit_issuance":"they were issued THE NEXT DAY","solar_permit__inspection_scheduling_request":"I paid the $300 and scheduled the inspection"},"Own California-policy-era project; distinguishes acts that occurred from contractor claims that did not."),
 ("15hitou","Logical-Specific2573","Los Angeles",{},"Own project; repeated engineering plans and claimed permit delay do not establish an AHJ act."),
 ("17hf4j7","ryushi32","city of San Diego",{"solar_permit__ahj_final_inspection":"The inspection by the city of San Diego happened on 6/23/2023"},"Own San Diego project; failed final inspection occurred; failure establishes need for a repeat path but does not show reinspection occurred."),
 ("1aezusd","Original1620","California State Contractor's Licensing Board",{},"Own California project; narrated inspection was by utility and is not converted to AHJ evidence."),
 ("1dzc6i0","paradox249","state of California",{},"Own installation; city inspection is explicitly still pending."),
]


def _walk(value, path="$", out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        out.append((path, value))
        for k, v in value.items(): _walk(v, path + "." + k, out)
    elif isinstance(value, list):
        for i, v in enumerate(value): _walk(v, path + f"[{i}]", out)
    return out


def _quote(blob, author, text, path, digest):
    matches = []
    for jp, obj in _walk(blob):
        # Refreshed captures keep authoritative comments at $.comments.  Some
        # files also retain an older embedded $.post.comments snapshot; never
        # bind review quotes to that stale duplicate tree.
        if jp.startswith("$.post.comments"):
            continue
        if not isinstance(obj, dict) or obj.get("author") != author: continue
        for field in ("selftext", "body", "title"):
            value = obj.get(field)
            if isinstance(value, str) and text.lower() in value.lower():
                start = value.lower().index(text.lower()); exact = value[start:start+len(text)]
                matches.append({"path": str(path.relative_to(ROOT)), "sha256": digest,
                                "json_path": jp + "." + field, "char_start": start,
                                "char_end": start + len(exact), "quote": exact})
    if not matches:
        raise ValueError(f"expected a quote for {author} {text!r}, got none")
    return matches[0]


def build():
    jurisdictions, county_by_j = [], {}
    with PANEL.open(newline="", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            if row["owner_scope"] == "ahj":
                jid = slug(row["owner_name"]); jurisdictions.append(jid); county_by_j[jid] = row["county"]
    jurisdictions = sorted(set(jurisdictions))
    episodes, included = [], set()
    for thread, author, context, positives, note in SPECS:
        if thread in DESCRIPTIVE_ONLY:
            continue
        path = RAW / f"{thread}.json"; blob = json.loads(path.read_text())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        context_ref = _quote(blob, author, context, path, digest)
        quote_by_step = {step: _quote(blob, author, text, path, digest)
                         for step, text in positives.items()}
        eid = f"reddit_{thread}__{author}__installation_1"
        scope = {"path": str(path.relative_to(ROOT)), "sha256": digest,
                 "locator": f"$case[{json.dumps(eid)}]"}
        resolved = ({("10bdub6", "drgath"): "marin_county",
                     ("17hf4j7", "ryushi32"): "san_diego_city",
                     ("15hitou", "Logical-Specific2573"): "los_angeles_city"}.get((thread, author)))
        if resolved:
            candidate_rows = []
        elif "bay area" in context.lower():
            bay = {"Alameda", "Contra Costa", "Marin", "Napa", "San Francisco",
                   "San Mateo", "Santa Clara", "Solano", "Sonoma"}
            candidate_rows = [{"jurisdiction_id": j, "prior_weight": 1.0}
                              for j in jurisdictions if county_by_j.get(j) in bay]
        elif "santa barbara" in context.lower():
            candidate_rows = [{"jurisdiction_id": j, "prior_weight": 1.0}
                              for j in jurisdictions if county_by_j.get(j) == "Santa Barbara"]
        else:
            candidate_rows = [{"jurisdiction_id": j, "prior_weight": 1.0} for j in jurisdictions]
        episodes.append({
            "episode_id": eid, "thread_id": thread, "author": author,
            "dependence_group_id": eid, "identity_scope_id": eid,
            "identity_scope_refs": [scope], "root_adopted": False,
            "complete_capture_read": True, "actor_and_lifecycle_reviewed": True,
            "occurrence_reviewed": True, "statistic": "individual",
            "reading_scope_kind": "complete_fixed_universe", "reviewed_step_ids": BLOCK,
            "jurisdiction_id": resolved, "county_quotes": [context_ref] if resolved else [],
            "assignment_prior_kind": "reviewed_candidate_weights",
            "assignment_prior_basis": ("Resolved from the author's own explicit operative city/county language."
                if resolved else "Uniform over the reviewed contextual geography (nine-county Bay Area, named county context, or broad California). Utility service fields were not treated as a reliable spatial boundary."),
            "identity_context_quotes": [context_ref],
            "candidates": candidate_rows,
            "readings": [{"step_id": step, "detected": step in quote_by_step,
                          "quotes": [quote_by_step[step]] if step in quote_by_step else []}
                         for step in BLOCK],
            "review_metadata": {"semantic_note": note, "secondhand": False,
                                "no_mention_means": "reviewed_nondetection_not_absence"},
        })
        included.add(thread)
    coverage = []
    for thread in THREADS:
        if thread == "12bmk4h": route = "excluded_out_of_state_missouri"
        elif thread in DESCRIPTIVE_ONLY: route = "descriptive_or_not_initiated_stratum_not_occupancy"
        elif thread == "10i1jgy": route = "procedural_discussion_no_adopted_individual_episode"
        elif thread == "11kqeg2": route = "procedural_policy_claim_no_adopted_individual_episode"
        else: route = "reviewed_with_one_or_more_episode" if thread in included else "reviewed_no_episode"
        coverage.append({"thread_id": thread, "route": route})
    packet = {"schema_version": "reviewed-forum-occupancy-episodes/1",
              "packet_id": "reviewed_sol001", "root_adopted": False,
              "dependence_reviewed": True,
              "dependence_qualification": "One unit per author-installation; updates by the same author are merged. Secondhand and procedural claims are not primary episodes.",
              "selected_thread_count": len(THREADS), "jurisdictions": jurisdictions,
              "episodes": episodes, "review_status": "awaiting_root_representative_spot_check"}
    return packet, coverage


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    packet, coverage = build()
    (OUT / "reviewed_sol001.json").write_text(json.dumps(packet, indent=2) + "\n")
    lines = ["# SOL001 coverage", "", f"Threads reviewed: {len(coverage)}", f"Episodes: {len(packet['episodes'])}", ""]
    lines += [f"- `{r['thread_id']}` — {r['route']}" for r in coverage]
    (OUT / "reviewed_sol001_coverage.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"threads": len(coverage), "episodes": len(packet["episodes"]),
                      "positive_readings": sum(r["detected"] for e in packet["episodes"] for r in e["readings"]),
                      "root_adopted": packet["root_adopted"]}, indent=2))


if __name__ == "__main__": main()
