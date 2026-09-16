#!/usr/bin/env python3
"""Pack one batch into a single self-contained input file for a renderer (or verifier) agent.

  python3 benchmark/synth/render/prepare_batch.py --world W1 --batch T00            # -> batches/T00.input.json
  python3 benchmark/synth/render/prepare_batch.py --world W1 --batch T00 --verify   # -> batches/T00.verify_input.json
Render input: {batch_id, style_guides: {kind: path}, render_context: {jur: {...}}, specs: [full spec...]}.
Verify input: adds artifacts: {id: text} and hidden_elements: {id: [...]} (from verify_context, only the
must_not_reveal ids of each spec) — the verifier sees hidden descriptions, the renderer never does.
"""
import argparse, copy, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
STYLE = {"program_page": "municipal_pages.md", "generic_permits_page": "municipal_pages.md", "faq": "municipal_pages.md",
         "form": "forms.md", "checklist": "forms.md", "fee_schedule": "legal_text.md", "fee_resolution": "legal_text.md",
         "ordinance": "legal_text.md", "bill_analysis": "staff_reports.md", "staff_report": "staff_reports.md",
         "sop": "staff_reports.md", "audit_excerpt": "staff_reports.md", "council_minutes": "staff_reports.md",
         "official_stats": "municipal_pages.md", "news": "news_and_forums.md", "third_party_guide": "news_and_forums.md",
         "forum_thread": "reddit_style.md", "reddit_thread": "reddit_style.md"}


def renderer_spec(spec):
    """A renderer gets noisy reported amounts, never the persona's exact log values.

    Full specs remain available to the independent verifier. This copy does not
    alter the world/specification or substitute true amounts for noisy reports.
    """
    result=copy.deepcopy(spec)
    persona=result.get('persona')
    if persona:
        persona.pop('true_timeline',None)
        reported=persona.get('reported_timeline',{})
        # This internal numeric helper can differ from the deliberately noisy
        # rendered phrase; it is not a second public numerical claim.
        reported.pop('total_days_reported',None)
        for step in reported.get('steps',[]):
            step.pop('true_days',None)
    return result


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--world", default="W1"); ap.add_argument("--batch", required=True)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    wd = ROOT / "benchmark/synth/worlds" / a.world
    b = json.load(open(wd / "batches" / f"{a.batch}.json"))
    specs = [json.load(open(wd / "specs" / f"{sid}.json")) for sid in b["spec_ids"]]
    jurs = sorted({s.get("jur") for s in specs if s.get("jur")})
    rc = {}
    for j in jurs:
        f = wd / "render_context" / f"{j}.json"
        if f.exists():
            rc[j] = json.load(open(f))
    kinds = sorted({s["kind"] for s in specs})
    # Legal-text kinds are public documents whose *content* is the truth: give the renderer the statute /
    # local-rule truth files (never the process truth) plus state-level context.
    LEGAL = {"ordinance", "bill_analysis", "fee_resolution"}
    legal_truth = {"statutes": {}, "local_rules": {}}
    for s in specs:
        if s["kind"] in LEGAL:
            st = s.get("stat_id")
            if st and st not in legal_truth["statutes"]:
                f = wd / "truth/statutes" / f"{st}.json"
                if f.exists():
                    legal_truth["statutes"][st] = json.load(open(f))
            if s.get("jur") and st and s.get("subkind") != "statute_text":
                key = f"{s['jur']}__{st}"
                f = wd / "truth/local_rules" / f"{key}.json"
                if f.exists() and key not in legal_truth["local_rules"]:
                    legal_truth["local_rules"][key] = json.load(open(f))
    world = json.load(open(wd / "world.json"))
    out = {"batch_id": a.batch, "world": a.world, "group": b["group"],
           "style_guides": {k: str((ROOT / "benchmark/synth/style" / STYLE.get(k, "municipal_pages.md")).relative_to(ROOT)) for k in kinds},
           "brief": "benchmark/synth/briefs/RENDER_BRIEF.md", "artifacts_dir": str((wd / "artifacts").relative_to(ROOT)),
           "render_context": rc, "states": world.get("states"), "legal_truth": legal_truth,
           "specs": specs if a.verify else [renderer_spec(s) for s in specs]}
    name = f"{a.batch}.input.json"
    if a.verify:
        out["brief"] = "benchmark/synth/briefs/VERIFY_BRIEF.md"
        out["artifacts"], out["hidden_elements"] = {}, {}
        vc_cache = {}
        for s in specs:
            f = wd / "artifacts" / f"{s['artifact_id']}.md"
            out["artifacts"][s["artifact_id"]] = f.read_text() if f.exists() else None
            hidden = []
            for hid in s.get("must_not_reveal") or []:
                mid, _, aid = hid.rpartition(":") if ":" in hid else (f"{s.get('jur')}__{s.get('stat_id')}", "", hid)
                if mid not in vc_cache:
                    vf = wd / "verify_context" / f"{mid}.json"
                    vc_cache[mid] = {h["id"]: h for h in json.load(open(vf))["hidden_elements"]} if vf.exists() else {}
                if aid in vc_cache[mid]:
                    hidden.append(dict(vc_cache[mid][aid], process=mid))
            out["hidden_elements"][s["artifact_id"]] = hidden
        name = f"{a.batch}.verify_input.json"
    p = wd / "batches" / name
    p.write_text(json.dumps(out, indent=1))
    print(f"{p.relative_to(ROOT)}: {len(specs)} specs, {len(rc)} jurisdictions, kinds={kinds}, {p.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
