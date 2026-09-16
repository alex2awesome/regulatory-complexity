#!/usr/bin/env python3
"""Score a reconstructed process model against `process_truth` (+ its ceiling).

    python3 pipeline/procbench/score.py --pred pred.json \
        --gold truth/processes/J2__S03.json \
        [--ceiling ceiling.json --task W1__J2__S03] \
        [--distractors truth/processes/J2__S07.json ...] \
        [--align llm|offline|both] [--k 3] [--log-summary log_summary.json] \
        [--statute truth/statutes/S03.json] [--condition oracle_docs] --out score.json

    python3 pipeline/procbench/score.py aggregate --runs runs/*/score.json --out summary.json

Writes `score.json` (every metric with numerator/denominator) and, next to it,
`alignment.json` (pair list with scores/votes — human-checkable, because
alignment noise is itself error source #8).
"""

import argparse
import glob
import json
import pathlib
import sys
from itertools import combinations

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))            # pipeline/ — for llm.py, process_model.py

try:
    from procbench import align as A, metrics as M                        # noqa: E402
except ImportError:                       # imported as pipeline.procbench.score
    from pipeline.procbench import align as A, metrics as M               # noqa: E402

# /2 repaired explicit process timing; /3 added structural/count scores.
# /4 also rejects normative process timing and uses explicit summary paths.
VERSION = "procbench-score/4"

def _load(p):
    return json.loads(pathlib.Path(p).read_text())

def signature(a):
    return f"{a['actor']}|{' '.join(sorted(a['toks']))}"

# --------------------------------------------------------------------- score

def score_one(args):
    pred = A.load_model(args.pred)
    gold = A.load_model(args.gold)
    distractors = [A.load_model(p) for p in (args.distractors or [])]
    ceiling = M.pick_ceiling(_load(args.ceiling), args.task) if args.ceiling else None
    ceil_ids = M.ceiling_refs(ceiling, gold)
    log_summary = _load(args.log_summary) if args.log_summary else None
    statute = _load(args.statute) if args.statute else None

    off = A.offline_align(pred, gold)
    llm_pairs, llm_info, agree = None, None, None
    used = "offline"
    if args.align == "file":
        # a prepared alignment (agent-backed k-vote; see align_agent.py)
        if not args.alignment_in:
            sys.exit("--align file needs --alignment-in <alignment.json>")
        _d = json.load(open(args.alignment_in))
        llm_pairs = _d["pairs"]
        llm_info = {"source": args.alignment_in, "k": _d.get("k"),
                    "votes_used": _d.get("votes_used"), "min_votes": _d.get("min_votes")}
        used = _d.get("mode_used", "file")
        agree = A.agreement(off, llm_pairs)
    elif args.align in ("llm", "both"):
        import llm as llm_mod
        llm_mod.set_backend(args.backend, args.model)
        llm_pairs, llm_info = A.llm_align(pred, gold, k=args.k, model=args.model)
        agree = A.agreement(off, llm_pairs)
        used = "llm"
    pairs = llm_pairs if llm_pairs is not None else off

    act = M.activity_metrics(pred, gold, pairs, ceil_ids)
    mp = {d["pred"] for d in pairs}
    halluc = M.frac(len(pred["activities"]) - len(mp), len(pred["activities"]),
                    unmatched=[[a["id"], a["name"][:80]] for a in pred["activities"]
                               if a["id"] not in mp][:25])
    out = {
        "procbench_version": VERSION,
        "task_id": args.task, "condition": args.condition,
        "run_id": args.run_id or pathlib.Path(args.out).resolve().parent.name,
        "pred_path": str(args.pred), "gold_path": str(args.gold),
        "gold_model_id": gold["model_id"], "pred_model_id": pred["model_id"],
        "alignment": {"mode_used": used, "requested": args.align, "k": args.k,
                      "n_pairs": len(pairs),
                      "n_many_to_one": sum(1 for d in pairs if d["relation"] == "split"),
                      "n_one_to_many": sum(1 for d in pairs if d["relation"] == "merge"),
                      "llm": llm_info, "offline_vs_llm_agreement": agree,
                      "file": _alignment_path(args.out)},
        "counts": {"n_pred_activities": len(pred["activities"]),
                   "n_gold_activities": len(gold["activities"]),
                   "n_gold_staff_only": sum(1 for a in gold["activities"]
                                            if a["visibility"] == "staff_only"),
                   "n_ceiling_activities": None if ceil_ids is None else len(ceil_ids),
                   "n_distractor_models": len(distractors)},
        "metrics": {
            "activity": act,
            "actor_accuracy": M.actor_accuracy(pairs),
            "order_agreement": M.order_agreement(pred, gold, pairs),
            "rework": M.rework_metrics(pred, gold, pairs),
            "fee": M.fee_metrics(pred, gold, pairs),
            "timing": M.timing_metrics(pred, gold, pairs, ceiling, log_summary),
            "hallucination": halluc,
            "disentanglement": M.disentanglement(pred, gold, pairs, distractors),
            "staleness": M.staleness(pred, gold, pairs),
            "confidence_evidence": M.confidence_evidence(pred, pairs),
        },
        "for_aggregation": {
            "matched_gold_ids": sorted({d["gold"] for d in pairs}),
            "pred_signatures": sorted(signature(a) for a in pred["activities"]),
            "truth_size": len(gold["activities"]),
            "ceiling_size": None if ceil_ids is None else len(ceil_ids),
            "availability_gap": (None if ceil_ids is None else
                                 round(1 - len(ceil_ids) / len(gold["activities"]), 4)),
            "recall_all": act["recall_all"]["value"],
            "ceiling_relative_recall": act["recall_ceiling"]["value"],
        },
    }
    uni = None
    if args.actor_universe:
        _u = json.load(open(args.actor_universe))
        if isinstance(_u, dict):
            _d = _u.get("departments") or _u.get("actors") or []
            uni = list(_d.keys()) if isinstance(_d, dict) else list(_d)
        else:
            uni = list(_u)
    out["metrics"]["actor_selection"] = M.actor_selection(pred, gold, pairs, uni)

    if statute:
        out["metrics"]["element_coverage"] = M.element_coverage(pred, gold, statute, pairs)

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2))
    alp = pathlib.Path(args.alignment_out) if args.alignment_out else pathlib.Path(_alignment_path(args.out))
    alp.write_text(json.dumps(
        {"pred": str(args.pred), "gold": str(args.gold), "mode_used": used,
         "requested": args.align, "k": args.k, "pairs": pairs,
         "unmatched_pred": [[a["id"], a["actor"], a["name"][:100]]
                            for a in pred["activities"] if a["id"] not in mp],
         "unmatched_gold": [[a["id"], a["actor"], (a["name"] or a["local_name"])[:100],
                             a["visibility"]] for a in gold["activities"]
                            if a["id"] not in {d["gold"] for d in pairs}],
         "offline_pairs": [[d["pred"], d["gold"], d["score"]] for d in off],
         "offline_vs_llm_agreement": agree}, indent=2))
    a = out["metrics"]
    print(f"P={a['activity']['precision']['value']} R={a['activity']['recall_all']['value']} "
          f"F1={a['activity']['f1']} R_visible={a['activity']['recall_visible']['value']} "
          f"R_ceiling={a['activity']['recall_ceiling']['value']} "
          f"actor={a['actor_accuracy']['value']} order={a['order_agreement']['value']} "
          f"rework_R={a['rework']['recall']['value']} halluc={a['hallucination']['value']} "
          f"disent={a['disentanglement']['failures']['value']} "
          f"stale={a['staleness']['total_stale_facts']} "
          f"timing_log={a['timing']['mean_abs_log_ratio']}"
          + (f" align_jaccard={agree['jaccard']}" if agree else ""))
    print(f"-> {outp}  |  {alp}")
    return out

# ----------------------------------------------------------------- aggregate

AGG = [("precision", "activity.precision"), ("recall_all", "activity.recall_all"),
       ("recall_visible", "activity.recall_visible"),
       ("ceiling_relative_recall", "activity.recall_ceiling"),
       ("f1", "activity.f1"), ("actor_accuracy", "actor_accuracy"),
       ("order_agreement", "order_agreement"), ("rework_recall", "rework.recall"),
       ("fee_mean_rel_err", "fee.mean_rel_err"),
       ("timing_mean_abs_log_ratio", "timing.mean_abs_log_ratio"),
       ("timing_end_to_end_abs_log_ratio", "timing.end_to_end.abs_log_ratio"),
       ("hallucination_rate", "hallucination"),
       ("disentanglement_failure_rate", "disentanglement.failures"),
       ("stale_facts", "staleness.total_stale_facts")]

def dig(metrics, path, node=False):
    """Fetch a dotted metric path; `node=True` returns the {num,den} dict (for
    re-aggregation), else the scalar value."""
    d = metrics
    for k in path.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    if node:
        return d if isinstance(d, dict) and "num" in d and "den" in d else None
    return d.get("value") if isinstance(d, dict) else d

def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else None

def aggregate(paths, out_path):
    runs = []
    for p in paths:
        r = _load(p)
        r["_path"] = str(p)
        runs.append(r)
    by_cond = {}
    for r in runs:
        by_cond.setdefault(r.get("condition") or "unspecified", []).append(r)
    conds = {}
    for c, rs in sorted(by_cond.items()):
        means, pooled = {}, {}
        for label, path in AGG:
            vals = [dig(r["metrics"], path) for r in rs]
            vals = [v for v in vals if v is not None]
            means[label] = round(sum(vals) / len(vals), 4) if vals else None
            nums = [d for d in (dig(r["metrics"], path, node=True) for r in rs) if d]
            if nums:      # re-aggregate from numerators/denominators, not means of means
                n = sum(d["num"] for d in nums if d.get("num") is not None)
                dd = sum(d["den"] for d in nums if d.get("den") is not None)
                pooled[label] = {"num": n, "den": dd,
                                 "value": round(n / dd, 4) if dd else None}
        conds[c] = {"n_runs": len(rs), "tasks": sorted({r.get("task_id") for r in rs
                                                        if r.get("task_id")}),
                    "means": means, "pooled": pooled}

    # ---- error decomposition, per task
    crr, avail = {}, {}
    for r in runs:
        fa = r.get("for_aggregation", {})
        t, c = r.get("task_id") or r.get("gold_model_id"), r.get("condition") or "unspecified"
        if fa.get("ceiling_relative_recall") is not None:
            crr.setdefault((t, c), []).append(fa["ceiling_relative_recall"])
        if fa.get("availability_gap") is not None:
            avail[t] = fa["availability_gap"]
    tasks = sorted({t for t, _ in crr} | set(avail))
    per_task = []
    for t in tasks:
        cs = {c: sum(v) / len(v) for (tt, c), v in crr.items() if tt == t}
        orc = next((cs[c] for c in ("oracle_no_distractors", "oracle_docs", "oracle")
                    if c in cs), None)
        if orc is None:
            orc = next((v for c, v in sorted(cs.items()) if "oracle" in c), None)
        srch = next((v for c, v in sorted(cs.items()) if "search" in c), None)
        per_task.append({
            "task_id": t, "availability": avail.get(t),
            "ceiling_relative_recall_by_condition": {c: round(v, 4) for c, v in sorted(cs.items())},
            "reconciliation": round(1 - orc, 4) if orc is not None else None,
            "retrieval": round(orc - srch, 4) if (orc is not None and srch is not None) else None})
    dec_means = {k: round(sum(v) / len(v), 4) for k in ("availability", "reconciliation", "retrieval")
                 for v in [[d[k] for d in per_task if d.get(k) is not None]] if v}

    # ---- reliability across repeated runs of the same (task, condition)
    groups, rel = {}, []
    for r in runs:
        groups.setdefault((r.get("task_id"), r.get("condition")), []).append(r)
    for (t, c), rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(rs) < 2:
            continue
        gj = [jaccard(a["for_aggregation"]["matched_gold_ids"],
                      b["for_aggregation"]["matched_gold_ids"]) for a, b in combinations(rs, 2)]
        pj = [jaccard(a["for_aggregation"]["pred_signatures"],
                      b["for_aggregation"]["pred_signatures"]) for a, b in combinations(rs, 2)]
        rel.append({"task_id": t, "condition": c, "n_runs": len(rs),
                    "matched_gold_jaccard": M.mean([x for x in gj if x is not None]),
                    "pred_signature_jaccard": M.mean([x for x in pj if x is not None])})

    summary = {"procbench_version": VERSION, "n_runs": len(runs),
               "runs": [{"path": r["_path"], "task_id": r.get("task_id"),
                         "condition": r.get("condition"), "run_id": r.get("run_id"),
                         "align_mode": r.get("alignment", {}).get("mode_used")} for r in runs],
               "by_condition": conds,
               "decomposition": {"note": "availability = 1 - |ceiling|/|truth|; "
                                         "reconciliation = 1 - ceiling-relative recall (oracle); "
                                         "retrieval = crr(oracle) - crr(search)",
                                 "per_task": per_task, "means": dec_means},
               "reliability": {"per_task_condition": rel,
                               "mean_matched_gold_jaccard":
                                   M.mean([d["matched_gold_jaccard"] for d in rel
                                           if d["matched_gold_jaccard"] is not None]),
                               "mean_pred_signature_jaccard":
                                   M.mean([d["pred_signature_jaccard"] for d in rel
                                           if d["pred_signature_jaccard"] is not None])}}
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2))
    for c, d in conds.items():
        m = d["means"]
        print(f"{c:24} n={d['n_runs']:2}  F1={m['f1']} R_all={m['recall_all']} "
              f"R_ceil={m['ceiling_relative_recall']} order={m['order_agreement']} "
              f"halluc={m['hallucination_rate']}")
    print("decomposition:", dec_means, "| reliability:",
          summary["reliability"]["mean_matched_gold_jaccard"], f"-> {p}")
    return summary

# ---------------------------------------------------------------------- CLI

def _alignment_path(out):
    """alignment.json lives next to the score file: <out stem>.alignment.json (was a fixed cwd name)."""
    import pathlib as _pl
    o = _pl.Path(out) if out else _pl.Path("score.json")
    return str(o.with_name(o.stem.replace(".score", "") + ".alignment.json"))

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "aggregate":
        ap = argparse.ArgumentParser(prog="score.py aggregate")
        ap.add_argument("--runs", nargs="+", required=True)
        ap.add_argument("--out", required=True)
        a = ap.parse_args(argv[1:])
        paths = [q for p in a.runs for q in (sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p])]
        if not paths:
            sys.exit("no run files matched --runs")
        return aggregate(paths, a.out)

    ap = argparse.ArgumentParser(prog="score.py", description=__doc__)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--ceiling")
    ap.add_argument("--task")
    ap.add_argument("--distractors", nargs="*", default=[])
    ap.add_argument("--statute")
    ap.add_argument("--actor-universe", dest="actor_universe", default=None,
                    help="JSON list of the jurisdiction's departments (or a render_context file with a "
                         "'departments' key): scores actor attribution as selection with a chance baseline")
    ap.add_argument("--log-summary", dest="log_summary")
    ap.add_argument("--align", choices=["llm", "offline", "both", "file"], default="offline")
    ap.add_argument("--alignment-in", dest="alignment_in", default=None,
                    help="with --align file: a prepared alignment file (see align_agent.py)")
    ap.add_argument("-k", "--k", type=int, default=3)
    ap.add_argument("--condition", default=None)
    ap.add_argument("--run-id", dest="run_id", default=None)
    ap.add_argument("--backend", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--alignment-out", dest="alignment_out", default=None)
    ap.add_argument("--out", required=True)
    return score_one(ap.parse_args(argv))

if __name__ == "__main__":
    main()
