"""CLI: build a synthetic world.

    python3 -m benchmark.synth.generator.build --world WNEW --seed 101 \
        --out benchmark/synth/worlds/WNEW

Equivalent (from the repo root):  python3 benchmark/synth/generator/build.py ...

Knobs can be overridden on the command line:
    --knob p_publish_sop=0.4 --knob distractor_ratio=2 --knob n_applicants=50
No LLM calls; stdlib only; deterministic given --seed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

if __package__ in (None, ""):                      # allow running as a plain script
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "benchmark.synth.generator"

from .ceiling import build_ceiling                         # noqa: E402
from .local_rules import build_local_rules                 # noqa: E402
from .processes import build_processes                      # noqa: E402
from .simulate import simulate_all                          # noqa: E402
from .specs import build_specs                              # noqa: E402
from .statutes import build_statutes                        # noqa: E402
from .world import build_world, render_context               # noqa: E402


def _w(path: pathlib.Path, obj, pretty=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2 if pretty else None, ensure_ascii=False,
                               sort_keys=False) + "\n", encoding="utf-8")


def _wl(path: pathlib.Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def _parse_knobs(pairs: list[str]) -> dict:
    out = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def build(world_id: str, seed: int, out_dir: str, knobs: dict | None = None) -> dict:
    out = pathlib.Path(out_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('Preserving existing world/files: choose a fresh or empty destination')
    prov: list[dict] = []

    def log(obj_type, oid, inputs, draws, why):
        prov.append({"object": obj_type, "id": oid, "world": world_id, "seed": seed,
                     "inputs": inputs, "draws": draws, "why": why})

    world = build_world(world_id, seed, knobs)
    statutes = build_statutes(world)
    rules = build_local_rules(world, statutes)
    processes = build_processes(world, statutes, rules)
    logs, summaries = simulate_all(world, processes, rules)
    specs = build_specs(world, statutes, rules, processes, logs, summaries)
    ceilings, tasks = build_ceiling(world, statutes, processes, summaries, specs)

    # ---------------------------------------------------------------- write
    _w(out / "world.json", world)
    log("world", world_id, ["benchmark/synth/DESIGN.md"],
        {"knobs": world["knobs"], "target_processes": world["counts"]["target_processes"]},
        "6 jurisdictions in 2 states; %d statutes; each Marisol jurisdiction implements 6-8"
        % len(world["statutes"]))

    for sid, stat in sorted(statutes.items()):
        _w(out / ("truth/statutes/%s.json" % sid), stat)
        log("statute", sid, ["domains.py:%s" % stat["domain"]],
            {"shape": stat["shape"], "n_elements": len(stat["skeleton"]),
             "n_optional": sum(1 for e in stat["skeleton"] if e["optional"]),
             "n_choices": len(stat["open_choices"]),
             "differences_from_lookalike": stat.get("differences_from_lookalike")},
            "%s (%s), %s shape: %d mandated elements, %d open choices%s"
            % (stat["cite"], stat["bill"], stat["shape"],
               sum(1 for e in stat["skeleton"] if not e["optional"]), len(stat["open_choices"]),
               "; look-alike of %s" % stat["lookalike_of"] if stat.get("lookalike_of") else ""))

    for mid, rule in sorted(rules.items()):
        _w(out / ("truth/local_rules/%s.json" % mid), rule)
        log("local_rule", mid, [rule["stat_id"], "world.implementations"],
            {"instrument": rule["instrument"], "adopted": rule["adopted"],
             "fee": rule["fee"]["amount"], "fee_derivation": rule["fee"]["derivation"],
             "n_added_elements": len(rule["added_elements"]),
             "n_stricter": len(rule["stricter_standards"]),
             "lineage_from": rule["lineage_from"], "retrofit": rule["retrofit"],
             "has_prior_version": bool(rule["prior_version"])},
            "%s adopted %s by %s; %s%s"
            % (rule["program_name"], rule["adopted"], rule["cite"],
               "retrofit of a pre-statute program" if rule["retrofit"] else "first adoption",
               "; " + rule["lineage_note"] if rule.get("lineage_note") else ""))

    for mid, proc in sorted(processes.items()):
        _w(out / ("truth/processes/%s.json" % mid), proc)
        log("process", mid, [proc["stat_id"], "truth/local_rules/%s.json" % mid],
            {"n_activities": len(proc["activities"]), "n_actors": len(proc["actors"]),
             "visibility": {v: sum(1 for a in proc["activities"] if a["visibility"] == v)
                            for v in ("applicant_facing", "applicant_inferable", "staff_only")},
             "n_rework_loops": sum(1 for a in proc["activities"] if a["rework"]),
             "denial_rate": proc["denial_rate"],
             "backoffice": [a.get("backoffice_tag") for a in proc["activities"] if a.get("backoffice_tag")],
             "unimplemented_elements": [e["element_id"] for e in proc["unimplemented_elements"]],
             "deviations": [d["element_id"] for d in proc["deviations"]]},
            proc["notes"])
        _wl(out / ("truth/log/%s.jsonl" % mid), logs[mid])
        _w(out / ("truth/log/%s.summary.json" % mid), summaries[mid])
        s = summaries[mid]
        log("log", mid, ["truth/processes/%s.json" % mid],
            {"n": s["n_applicants"], "median_elapsed": s["elapsed_days"]["median"],
             "p90_elapsed": s["elapsed_days"]["p90"], "denial_rate": s["denial_rate"],
             "abandon_rate": s["abandon_rate"], "mean_rework_rounds": s["mean_rework_rounds"],
             "censored": s["n_censored"]},
            "Monte-Carlo over the designed graph: lognormal per-activity cycle times, rework "
            "p_trigger, denial at the decision step, %s abandonment" % s["abandon_rate"])

    for spec in specs:
        _w(out / ("specs/%s.json" % spec["artifact_id"]), spec)
        log("spec", spec["artifact_id"], [k for k in ("stat_id", "jur") if spec.get(k)],
            {"kind": spec["kind"], "target": spec["target"], "stale": spec.get("stale", False),
             "n_reveals": len(spec.get("reveals", [])),
             "n_must_not_reveal": len(spec.get("must_not_reveal", [])),
             "n_contamination": len(spec.get("contamination", [])),
             "thread_len": len(spec["thread"]) if spec.get("thread") else 0,
             "persona": spec["persona"]["applicant_id"] if spec.get("persona") else None},
            spec["why"])

    _w(out / "ceiling.json", ceilings)
    for c in ceilings:
        log("ceiling", c["task_id"], c["artifacts_about_process"],
            {"exists_exact": c["coverage"]["exists_exact"], "hidden": len(c["hidden"]),
             "staff_only_recovered": c["coverage"]["staff_only_recovered"],
             "timing": c["timing_ceiling"]["best_estimate_from_posts"],
             "true_median": c["timing_ceiling"]["true_median_days"]}, c["why"])
    _w(out / "tasks.json", tasks)
    log("tasks", "tasks.json", ["ceiling.json"], {"n_tasks": len(tasks)},
        "one task per target process, five information conditions each")

    # render_context (Wave 2) and verify_context (Wave 3)
    for jur in world["jurisdictions"]:
        _w(out / ("render_context/%s.json" % jur["id"]),
           render_context(world, jur, statutes, rules, processes))
    for mid, proc in sorted(processes.items()):
        _w(out / ("verify_context/%s.json" % mid), {
            "model_id": mid,
            "hidden_elements": [{"id": a["id"], "name": a["name"], "local_name": a["local_name"],
                                 "actor": next(x["name"] for x in proc["actors"] if x["id"] == a["actor"]),
                                 "visibility": a["visibility"], "notes": a["notes"],
                                 # a step mandated by public law: restating the mandate in an
                                 # ordinance/fee resolution/staff report/bill analysis/minutes is
                                 # a note, not a leak (DESIGN.md Wave-2/3 finding)
                                 "statutorily_disclosed": a.get("statutorily_disclosed", False),
                                 "element_ref": a["element_ref"],
                                 "element_text": a.get("element_text")}
                                for a in proc["activities"] if a["visibility"] == "staff_only"],
            "inferable_elements": [{"id": a["id"], "name": a["name"]}
                                   for a in proc["activities"] if a["visibility"] == "applicant_inferable"],
            "prior_version": proc["prior_version"],
        })

    _wl(out / "provenance.jsonl", prov)

    # ---------------------------------------------------------------- counts
    n_t = sum(1 for s in specs if s["target"])
    counts = {
        "world": world_id, "seed": seed, "out": str(out),
        "jurisdictions": len(world["jurisdictions"]),
        "statutes": len(statutes),
        "statutes_marisol": sum(1 for s in statutes.values() if s["state"] == "Marisol"),
        "processes": len(processes),
        "target_processes": len(tasks),
        "lookalike_processes": len(processes) - len(tasks),
        "activities": sum(len(p["activities"]) for p in processes.values()),
        "activities_by_visibility": {
            v: sum(1 for p in processes.values() for a in p["activities"] if a["visibility"] == v)
            for v in ("applicant_facing", "applicant_inferable", "staff_only")},
        "actors_total": sum(len(p["actors"]) for p in processes.values()),
        "rework_loops": sum(1 for p in processes.values() for a in p["activities"] if a["rework"]),
        "local_rules_with_lineage": sum(1 for r in rules.values() if r["lineage_from"]),
        "local_rules_with_prior_version": sum(1 for r in rules.values() if r["prior_version"]),
        "retrofits": sum(1 for r in rules.values() if r["retrofit"]),
        "log_records": sum(len(v) for v in logs.values()),
        "specs_total": len(specs), "specs_target": n_t, "specs_distractor": len(specs) - n_t,
        "distractor_ratio_achieved": round((len(specs) - n_t) / max(1, n_t), 2),
        "specs_by_kind": {k: sum(1 for s in specs if s["kind"] == k)
                          for k in sorted({s["kind"] for s in specs})},
        "stale_specs": sum(1 for s in specs if s.get("stale")),
        "reddit_threads": sum(1 for s in specs if s["kind"] == "reddit_thread"),
        "insider_comments": sum(1 for s in specs if s.get("thread")
                                and any(c["is_staff_insider"] for c in s["thread"])),
        "tasks": len(tasks),
        "provenance_lines": len(prov),
        "ceiling_mean_exists_exact": round(sum(c["coverage"]["exists_exact"] for c in ceilings) / max(1, len(ceilings)), 3),
        "ceiling_mean_hidden_share": round(sum(c["coverage"]["hidden_share"] for c in ceilings) / max(1, len(ceilings)), 3),
    }
    _w(out / "counts.json", counts)
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a synthetic process-ecosystem world.")
    ap.add_argument("--world", default="W1")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None, help="default: benchmark/synth/worlds/<world>")
    ap.add_argument("--knob", action="append", help="override a knob, e.g. --knob p_publish_sop=0.5")
    args = ap.parse_args(argv)
    out = args.out or "benchmark/synth/worlds/%s" % args.world
    counts = build(args.world, args.seed, out, _parse_knobs(args.knob))
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
