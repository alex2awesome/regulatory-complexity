#!/usr/bin/env python3
"""Build Benchmark-1 tasks from the Wave-1 reconnaissance manifests and the gold-candidate list.

A task = (slug, implementer) with: a gold document (gold_quality >= 3 from _gold/gold_candidates.json or a
designed-tier source in the slug's sources.json), and a declared-tier footprint (>= 3 declared sources).
Emits benchmark/realworld/tasks.json with, per task and per information condition, the list of source files
the solver may see (paths under corpus/realworld/).
  python3 benchmark/realworld/build_tasks.py
"""
import json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[2]
RW = ROOT / "corpus/realworld"
DECLARED = {"statute", "regulation", "local_ordinance", "program_page", "form", "checklist", "faq", "fee_schedule", "handout", "guide"}
USERS = {"reddit_post", "reddit_comment", "forum_post", "news"}
DESIGNED = {"staff_report", "sop", "audit", "consultant_study", "grand_jury", "manual", "controller_report", "guidance", "board_packet", "policy_manual"}
OBSERVED = {"dataset", "official_stats"}


def tier_of(s):
    t = s.get("tier"); k = s.get("kind")
    if t == "statute" or k in DECLARED or t == "declared":
        return "declared"
    if t == "user_report" or k in USERS:
        return "users"
    if t == "designed" or k in DESIGNED:
        return "designed"
    if t == "observed" or k in OBSERVED:
        return "observed"
    return "other"


def main():
    gold = json.load(open(RW / "_gold/gold_candidates.json"))
    gold = gold.get("candidates", gold) if isinstance(gold, dict) else gold
    if isinstance(gold, dict):
        gold = list(gold.values())
    gold_by_slug = collections.defaultdict(list)
    for g in gold:
        for slug in str(g.get("benchmark_slug", "")).replace("/", " ").split():
            slug = slug.strip("(),")
            if (RW / slug).exists():
                gold_by_slug[slug].append(g)
    tasks, report = [], []
    for sdir in sorted(p for p in RW.iterdir() if p.is_dir() and not p.name.startswith("_")):
        mf = sdir / "sources.json"
        if not mf.exists():
            report.append((sdir.name, "no sources.json yet")); continue
        m = json.load(open(mf))
        srcs = [s for s in m["sources"] if s.get("kept", True)]
        by = collections.defaultdict(list)
        for s in srcs:
            by[tier_of(s)].append(s)
        designed = [s for s in by["designed"]]
        golds = [{"id": g["id"], "title": g.get("title"), "url": g.get("url"), "quality": g.get("gold_quality"),
                  "saved_as": g.get("saved_as"), "timing_data": g.get("timing_data")} for g in gold_by_slug.get(sdir.name, [])
                 if (g.get("gold_quality") or 0) >= 3]
        golds += [{"id": s["source_id"], "title": s.get("title"), "url": s.get("url"), "quality": None,
                   "saved_as": s.get("saved_as"), "timing_data": "see reveals"} for s in designed]
        n_decl = len(by["declared"])
        ok = bool(golds) and n_decl >= 3
        report.append((sdir.name, f"declared={n_decl} users={len(by['users'])} designed={len(designed)} observed={len(by['observed'])} gold_candidates={len(golds)} -> {'TASK' if ok else 'skip'}"))
        if not ok:
            continue
        for jur in (m.get("jurisdictions") or ["(single implementer)"])[:3]:
            tasks.append({
                "task_id": f"RW__{sdir.name}__{jur.replace(' ', '_')[:40]}",
                "slug": sdir.name, "implementer": jur,
                "statute": m.get("statute"),
                "prompt": f"Construct the process model (actors, activities incl. any staff-side steps you can evidence, handoffs, rework loops, fees, terminal artifact) and the expected timeline for: {sdir.name.replace('_', ' ')} as implemented by {jur}. Mark each activity's visibility and cite evidence.",
                "gold": golds,
                "conditions": {
                    "declared_only": [s.get("saved_as") for s in by["declared"] if s.get("saved_as")],
                    "declared_plus_users": [s.get("saved_as") for s in by["declared"] + by["users"] if s.get("saved_as")] + [f"{sdir.name}/reddit/"],
                    "oracle_docs": [s.get("saved_as") for s in by["declared"] + by["users"] + designed + by["observed"] if s.get("saved_as")] + [f"{sdir.name}/reddit/"],
                    "search": [],
                },
                "sibling_processes_for_disentanglement": m.get("cross_process_contamination", "")[:300],
                "process_draft": f"{sdir.name}/process_draft.json" if (sdir / "process_draft.json").exists() else None,
            })
    out = ROOT / "benchmark/realworld/tasks.json"
    out.write_text(json.dumps({"built": "2026-09-15", "n_tasks": len(tasks), "tasks": tasks}, indent=1))
    for r in report:
        print(f"{r[0]:22} {r[1]}")
    print(f"\n{len(tasks)} tasks -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
