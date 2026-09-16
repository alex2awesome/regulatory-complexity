#!/usr/bin/env python3
"""Harvest duration observations from STRUCTURED sources — no LLM needed.

Gold process models (`benchmark/realworld/gold/*.json`) carry per-activity `timing` blocks and a
`timing_gold` object; recon manifests (`corpus/realworld/<slug>/sources.json`) carry `timing_summary`
rows and `reveals.timing` entries. All of that is machine-readable, so the verifiable_official /
designed_document / statutory tiers can be extracted deterministically. Only free-text forum mining
(the community_reported tier) needs a model.

  python3 pipeline/priors/harvest_structured.py [--slugs a b c] [--force]

Writes `pipeline/priors/observations/<slug>.structured.json`, skipping any slug that already has an
agent-produced `<slug>.json` (so agent output is never double-counted) unless --force.
"""
import argparse, glob, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
OBS = ROOT / "pipeline/priors/observations"

AGENCY_BY_ACTOR = [
    (r"counter|permit (center|services)|intake|clerk|technician|front", "front_counter"),
    (r"plan (check|review)|reviewer|examiner|plans", "plan_review"),
    (r"inspect", "field_inspection"),
    (r"background|doj|bof|fbi|nics|criminal", "background_check"),
    (r"caseworker|eligibility|worker|adjudicat|examiner|officer", "caseworker"),
    (r"fire|health|assessor|county|environmental", "specialist_referral"),
    (r"utility|pg&e|sce|sdg&e|interconnect", "utility"),
    (r"contractor|third.?party|certifier|installer|commissary|dealer", "third_party"),
    (r"council|board|commission", "legislative_body"),
    (r"hearing|alj|appeal", "hearing_officer"),
    (r"records|cpra|custodian|disclosure", "records_unit"),
    (r"cashier|finance|billing|fiscal", "fiscal"),
    (r"uscis|federal", "federal_agency"),
    (r"edd|cslb|state|registrar|cdss|doj", "state_agency"),
]
TASK_BY_NAME = [
    (r"reinspect|re-inspect", "reinspection"),
    (r"inspect", "inspection"),
    (r"interview", "interview"),
    (r"exam|test", "test_or_exam"),
    (r"complete|screen|intake", "intake_screen"),
    (r"plan check|plan review|review|examine|verify.*document", "document_review"),
    (r"background|records check|database|registry check|clearance", "records_check"),
    (r"decide|decision|determin|grant|deny|approve", "decision"),
    (r"notice|notify|mail|inform", "notice"),
    (r"schedul|appoint|queue|assign", "scheduling"),
    (r"fee|pay|invoice|cashier|reconcil", "payment"),
    (r"issue|issuance|certificate|permit issu", "issuance"),
    (r"correct|resubmit|revis", "correction_cycle"),
    (r"appeal|hearing", "appeal"),
    (r"archiv|retain|record|report|registry", "recordkeeping"),
    (r"refer|route|forward|transfer", "referral"),
    (r"interconnect|permission to operate|pto", "interconnection"),
]
JCLASS = [(r"county", "county"), (r"uscis|federal|u\.s\.", "federal"),
          (r"state|california \(statewide|edd|cslb|doj", "state"),
          (r"pg&e|sce|sdg&e|utility", "utility_territory"),
          (r"los angeles|san francisco|san diego|san jos", "large_city")]


def pick(pats, text, default):
    t = (text or "").lower()
    for pat, val in pats:
        if re.search(pat, t):
            return val
    return default


def jclass(jur):
    return pick(JCLASS, jur, "mid_city")


def tier_of(src):
    s = (src or "").lower()
    if re.search(r"statut|penal code|gov\. code|cfr|u\.s\.c|§|regulation", s):
        return "statutory"
    if re.search(r"audit|official|dataset|solartrace|performance|board packet|dashboard|muckrock|statistic|xlsx|census", s):
        return "verifiable_official"
    if re.search(r"manual|sop|staff report|policy|handbook|guide|epolicy|acl|consultant", s):
        return "designed_document"
    return "designed_document"


def num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        m = re.search(r"(\d+(?:\.\d+)?)", x.replace(",", ""))
        if m:
            return float(m.group(1))
    return None


def from_gold(path, i0):
    g = json.load(open(path))
    slug = pathlib.Path(path).stem.split("__")[0]
    jur = g.get("jurisdiction") or ""
    out, i = [], i0
    for a in g.get("activities", []):
        t = a.get("timing") or {}
        med, p90 = num(t.get("median_days")), num(t.get("p90_days"))
        if med is None and p90 is None:
            continue
        i += 1
        src = str(t.get("source") or "")
        ev = (a.get("evidence") or [{}])[0] or {}
        out.append({
            "obs_id": f"{slug}-struct-{i:04d}", "slug": slug, "jurisdiction": jur,
            "step_key": {"agency_class": pick(AGENCY_BY_ACTOR, a.get("actor"), "state_agency"),
                         "task_type": pick(TASK_BY_NAME, a.get("name"), "document_review"),
                         "channel": (a.get("occasion") or "internal").split()[0],
                         "blocking_party": "applicant" if pick(AGENCY_BY_ACTOR, a.get("actor"), "") == "third_party" else "agency",
                         "cadence": "statutory_clock" if a.get("element_ref") and "statut" in src.lower() else "continuous",
                         "jurisdiction_class": jclass(jur)},
            "step_label": f"{a.get('name','')[:88]} ({a['id']})",
            "value": {"elapsed_days": med, "touch_days": None, "queue_days": None,
                      "statutory_cap_days": None, "range_days": [None, None], "p50": med, "p90": p90},
            "n": 1, "evidence_tier": tier_of(src or str(ev.get("doc"))),
            "source_id": f"{pathlib.Path(path).stem}:{a['id']}",
            "quote": str(ev.get("quote") or "")[:220], "date": g.get("gold_date"),
            "notes": f"from gold activity timing; timing source: {src[:90]}" if src else "from gold activity timing",
        })
    tg = g.get("timing_gold") or {}
    e2e = num(tg.get("end_to_end_median_days")) or num(tg.get("end_to_end_to_pto_median_days"))
    if e2e:
        i += 1
        out.append({
            "obs_id": f"{slug}-struct-{i:04d}", "slug": slug, "jurisdiction": jur,
            "step_key": {"agency_class": "front_counter", "task_type": "decision", "channel": "internal",
                         "blocking_party": "shared", "cadence": "continuous", "jurisdiction_class": jclass(jur)},
            "step_label": "END TO END (whole process)",
            "value": {"elapsed_days": e2e, "touch_days": None, "queue_days": None,
                      "statutory_cap_days": None, "range_days": [None, None],
                      "p50": e2e, "p90": num(tg.get("p90_days")) or num(tg.get("end_to_end_to_pto_p90_days"))},
            "n": 1, "evidence_tier": tier_of(str(tg.get("source"))),
            "source_id": f"{pathlib.Path(path).stem}:timing_gold",
            "quote": str(tg.get("quote") or "")[:220], "date": g.get("gold_date"),
            "notes": f"whole-process figure; scope: {str(tg.get('end_to_end_scope') or tg.get('source') or '')[:120]}",
        })
    return out, i


def from_manifest(slug, i0):
    f = ROOT / f"corpus/realworld/{slug}/sources.json"
    if not f.exists():
        return [], i0
    m = json.load(open(f))
    jur = (m.get("jurisdictions") or [""])[0]
    out, i = [], i0
    for r in (m.get("timing_summary") or []):
        if not isinstance(r, dict):
            continue
        seg = str(r.get("segment") or "")
        off, cap = num(r.get("official")), None
        if isinstance(r.get("official"), str) and re.search(r"statut|shall|within|cap|deadline", r["official"], re.I):
            cap, off = num(r["official"]), None
        if off is None and cap is None:
            continue
        i += 1
        out.append({
            "obs_id": f"{slug}-struct-{i:04d}", "slug": slug, "jurisdiction": jur,
            "step_key": {"agency_class": pick(AGENCY_BY_ACTOR, seg, "state_agency"),
                         "task_type": pick(TASK_BY_NAME, seg, "document_review"),
                         "channel": "internal", "blocking_party": "agency",
                         "cadence": "statutory_clock" if cap else "continuous",
                         "jurisdiction_class": jclass(jur)},
            "step_label": seg[:90],
            "value": {"elapsed_days": off, "touch_days": None, "queue_days": None,
                      "statutory_cap_days": cap, "range_days": [None, None], "p50": off, "p90": None},
            "n": r.get("n") or 1,
            "evidence_tier": "statutory" if cap else tier_of(str(r.get("official"))),
            "source_id": f"{slug}:timing_summary", "quote": str(r.get("official") or "")[:220],
            "date": None, "notes": "from manifest timing_summary (official/statutory column only; "
                                   "the user_reported column needs free-text mining)",
        })
    return out, i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    slugs = a.slugs or sorted(p.name for p in (ROOT / "corpus/realworld").iterdir()
                              if p.is_dir() and not p.name.startswith("_"))
    OBS.mkdir(parents=True, exist_ok=True)
    tot = 0
    for slug in slugs:
        if (OBS / f"{slug}.json").exists() and not a.force:
            print(f"  {slug:22} skipped — agent-produced observations already present")
            continue
        obs, i = [], 0
        for gp in sorted(glob.glob(str(ROOT / f"benchmark/realworld/gold/{slug}__*.json"))):
            o, i = from_gold(gp, i); obs += o
        o, i = from_manifest(slug, i); obs += o
        if not obs:
            print(f"  {slug:22} no structured timing found"); continue
        by = {}
        for x in obs:
            by[x["evidence_tier"]] = by.get(x["evidence_tier"], 0) + 1
        (OBS / f"{slug}.structured.json").write_text(json.dumps(
            {"slug": slug, "source": "harvest_structured.py (no LLM)", "observations": obs,
             "coverage": {"by_evidence_tier": by, "total_observations": len(obs),
                          "distinct_step_keys": len({tuple(sorted(x["step_key"].items())) for x in obs}),
                          "missing": "community_reported tier — forum free text still to be mined"}}, indent=1))
        tot += len(obs)
        print(f"  {slug:22} {len(obs):4} observations  {by}")
    print(f"{tot} structured observations written")


if __name__ == "__main__":
    main()
