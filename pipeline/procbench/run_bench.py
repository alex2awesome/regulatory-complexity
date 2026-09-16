#!/usr/bin/env python3
"""Run tasks.json x conditions x k through solve.py, then score if score.py exists.

  python3 pipeline/procbench/run_bench.py --world _fixture --dry-run
  python3 pipeline/procbench/run_bench.py --world _fixture --tasks J1 \
      --conditions search,oracle_docs --k 2 --backend glm

Writes runs/summary.json (one row per run + per-condition means of every numeric
score field). Codex is minutes per call: --dry-run first, and keep k small.
"""

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipeline import llm                                    # noqa: E402
from pipeline.procbench import solve, web                   # noqa: E402

SCORE = pathlib.Path(__file__).parent / "score.py"
# Default invocation of the scorer's own CLI (score.py --pred --gold ... --out).
# Override with --score-cmd "<template>"; placeholders: score pred gold out task
# condition run_id ceiling statute distractors align.
SCORE_CMD = ("python3 {score} --pred {pred} --gold {gold} --out {out} --task {task} "
             "--condition {condition} --run-id {run_id} --align {align} {ceiling} {statute} {distractors}")


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}{k}."))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix.rstrip(".")] = float(obj)
    return out


def sh(cmd, timeout=1800):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stderr or p.stdout).strip()[-400:]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def score_run(row, task, world_dir, cmd_tmpl, align):
    """Shell out to score.py (another agent's file: its CLI is read, not assumed).
    Returns (score_dict|None, error|None)."""
    if not SCORE.exists():
        return None, "score.py not present"
    truth = world_dir / "truth" / "processes"
    gold = truth / f"{task.get('jur')}__{task.get('stat_id')}.json"
    if not gold.exists():
        return None, f"no gold process_truth at {gold} (generator has not produced it yet)"
    out = pathlib.Path(row["run_dir"]) / "score.json"
    ceiling = world_dir / "ceiling.json"
    statute = world_dir / "truth" / "statutes" / f"{task.get('stat_id')}.json"
    others = [str(p) for p in sorted(truth.glob("*.json")) if p != gold]
    cmd = cmd_tmpl.format(score=SCORE, pred=pathlib.Path(row["run_dir"]) / "pred.json", gold=gold, out=out,
                          task=task.get("task_id"), condition=row["condition"], run_id=row["run_id"], align=align,
                          ceiling=f"--ceiling {ceiling}" if ceiling.exists() else "",
                          statute=f"--statute {statute}" if statute.exists() else "",
                          distractors=("--distractors " + " ".join(others)) if others else "")
    rc, err = sh(cmd)
    if out.exists():
        try:
            return json.loads(out.read_text()), None
        except Exception as e:
            return None, f"unreadable score.json: {e}"
    return None, f"score.py rc={rc}: {err}  (override with --score-cmd)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--tasks", default=None, help="comma-separated task_id substrings to keep")
    ap.add_argument("--conditions", default=None, help=f"default: each task's own list, else {web.CONDITIONS}")
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--mode", default=None, choices=["oracle", "agent", "manual"])
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--backend", default=None, choices=["codex", "glm", "anthropic"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-score", action="store_true")
    ap.add_argument("--align", default="offline", choices=["offline", "llm", "both"],
                    help="score.py alignment mode; llm costs extra model calls")
    ap.add_argument("--score-cmd", default=SCORE_CMD)
    ap.add_argument("--out", default=None, help="summary path (default <runs-root>/summary.json)")
    ap.add_argument("--worlds-root", default=None); ap.add_argument("--runs-root", default=None)
    a = ap.parse_args(argv)
    if a.backend or a.model:
        llm.set_backend(a.backend, a.model)

    world_dir = pathlib.Path(a.worlds_root or web.WORLDS_ROOT) / a.world
    tasks = json.loads((world_dir / "tasks.json").read_text())
    if a.tasks:
        keep = [s.strip() for s in a.tasks.split(",") if s.strip()]
        tasks = [t for t in tasks if any(s in t["task_id"] for s in keep)]
    grid = []
    for t in tasks:
        conds = ([c.strip() for c in a.conditions.split(",")] if a.conditions
                 else t.get("conditions") or web.CONDITIONS)
        for c in conds:
            for i in range(1, a.k + 1):
                run_id = f"{t['task_id']}__{c}" + (f"__r{i}" if a.k > 1 else "")
                grid.append({"task_id": t["task_id"], "condition": c, "k_index": i, "run_id": run_id,
                             "mode": a.mode or solve.MODE_FOR[c]})
    if a.dry_run:
        print(f"{len(grid)} runs on world {a.world} ({llm.model_desc()}):")
        for g in grid:
            print(f"  {g['run_id']:<55} mode={g['mode']}")
        return grid

    runs_root = pathlib.Path(a.runs_root or web.RUNS_ROOT)
    rows = []
    for g in grid:
        sa = solve.build_parser().parse_args(
            ["--world", a.world, "--task", g["task_id"], "--condition", g["condition"],
             "--mode", g["mode"], "--run-id", g["run_id"], "--max-steps", str(a.max_steps)]
            + (["--worlds-root", a.worlds_root] if a.worlds_root else [])
            + (["--runs-root", a.runs_root] if a.runs_root else [])
            + (["--model", a.model] if a.model else []))
        print(f"[{len(rows)+1}/{len(grid)}] {g['run_id']} ({g['mode']}, {llm.model_desc()})", flush=True)
        meta = solve.solve(sa, g["run_id"])
        row = {**g, **{k: meta[k] for k in ("finished", "error", "seconds", "steps", "backend")},
               "run_dir": str(runs_root / g["run_id"])}
        if not a.no_score and row["finished"]:
            task = next(t for t in tasks if t["task_id"] == g["task_id"])
            row["score"], row["score_error"] = score_run(row, task, world_dir, a.score_cmd, a.align)
        rows.append(row)

    by_cond = {}
    for r in rows:
        acc = by_cond.setdefault(r["condition"], {"n": 0, "n_finished": 0, "sums": {}, "counts": {}})
        acc["n"] += 1
        acc["n_finished"] += bool(r["finished"])
        for k, v in flatten(r.get("score") or {}).items():
            acc["sums"][k] = acc["sums"].get(k, 0.0) + v
            acc["counts"][k] = acc["counts"].get(k, 0) + 1
    means = {c: {"n": v["n"], "n_finished": v["n_finished"],
                 **{k: round(v["sums"][k] / v["counts"][k], 4) for k in v["sums"]}}
             for c, v in by_cond.items()}
    # score.py has its own aggregator; use it for the authoritative roll-up when scores exist.
    agg, scored = None, [str(pathlib.Path(r["run_dir"]) / "score.json") for r in rows if r.get("score")]
    if scored and SCORE.exists():
        agg_out = runs_root / "score_aggregate.json"
        rc, err = sh(f"python3 {SCORE} aggregate --runs {' '.join(scored)} --out {agg_out}")
        agg = json.loads(agg_out.read_text()) if agg_out.exists() else {"error": f"rc={rc}: {err}"}
    summary = {"world": a.world, "backend": llm.model_desc(), "k": a.k,
               "generated": dt.datetime.now().isoformat(timespec="seconds"),
               "by_condition": means, "aggregate": agg, "runs": rows}
    out = pathlib.Path(a.out) if a.out else runs_root / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1))
    print(json.dumps(means, indent=1))
    print(f"wrote {out}")
    return summary


if __name__ == "__main__":
    main()
