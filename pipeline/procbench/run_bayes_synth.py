"""Reproducible, offline W1 pilot. Inference reads extracted documents, never truth.

python3 -m pipeline.procbench.run_bayes_synth --out runs/bayes_v3

Saved baselines are rescored into the new output directory, preserving originals.
Evaluation loads ground truth ONLY after the posterior has been written.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
import pathlib
import statistics
import time

from . import align, metrics, score
from .bayes_evidence import load_cached
from .bayes_process import Config, fit

ROOT = pathlib.Path(__file__).resolve().parents[2]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def crps(samples, actual):
    """Empirical CRPS, O(n log n), in the outcome's units (lower is better)."""
    xs = sorted(samples)
    if not xs:
        return None
    n = len(xs)
    first = sum(abs(x - actual) for x in xs) / n
    second = sum((2 * i - n + 1) * x for i, x in enumerate(xs)) / (n * n)
    return first - second


def evaluation(posterior, draws, cases, gold, log_summary):
    pred = align.load_model(posterior["model"])
    truth = align.load_model(gold)
    pairs = align.offline_align(pred, truth)
    n = len(gold["activities"])
    pmass = posterior["step_count"]["pmf"].get(str(n), 0)
    lo, hi = posterior["step_count"]["ci90"]
    timing = []
    for pair in pairs:
        act = pred["by_id"][pair["pred"]]["raw"]
        gt = truth["by_id"][pair["gold"]]["median_days"]
        t = act["timing"]
        if gt is not None:
            timing.append({"pred": pair["pred"], "gold": pair["gold"], "gold_median": gt,
                           "pred_median": t["median_days"], "prior_only": t["prior_only"],
                           "covered_by_median_ci90": t["median_ci90"][0] <= gt <= t["median_ci90"][1]})
    actual_e2e = log_summary["elapsed_days"]["median"]
    return {"step_count": {"truth": n, "posterior_median": posterior["step_count"]["median"],
                           "ci90": [lo, hi], "covered": lo <= n <= hi,
                           "empirical_probability_at_truth": pmass,
                           "negative_log_probability": -math.log(pmass) if pmass else None,
                           "zero_mass_note": "zero Monte Carlo hits is not proof of zero posterior probability" if not pmass else None,
                           "crps": crps([d["n_steps"] for d in draws], n)},
            "activity": metrics.activity_metrics(pred, truth, pairs, None),
            "actor": metrics.actor_accuracy(pairs),
            "order": metrics.order_agreement(pred, truth, pairs),
            "rework": metrics.rework_metrics(pred, truth, pairs),
            "timing": metrics.timing_metrics(pred, truth, pairs, log_summary={"median_days": actual_e2e}),
            "step_median_intervals": timing,
            "median_interval_coverage_on_aligned_steps": statistics.mean(t["covered_by_median_ci90"] for t in timing) if timing else None,
            "end_to_end_scope_warning": "Posterior is conditional on represented steps/decision reached; gold includes all simulated steps. Descriptive comparison, not a calibrated matched estimand.",
            "unavailable_validation": ["agency hands-on hours", "applicant hands-on hours", "true source error rates"],
            "alignment": pairs}


def rescore_baselines(out):
    rows = []
    world = ROOT / "benchmark/synth/worlds/W1"
    for condition, folder, prefix in (("oracle_docs", "synth", "synth_"), ("search", "synth_search", "s_")):
        for old_path in sorted((ROOT / "runs" / folder).glob("*.score.json")):
            old = json.loads(old_path.read_text())
            task = old_path.name.removesuffix(".score.json")
            pred = ROOT / "runs" / folder / f"{prefix}{task}" / "pred.json"
            target = out / "rescored" / condition / f"{task}.score.json"
            args = ["--pred", str(pred), "--gold", str(ROOT / old["gold_path"]),
                    "--ceiling", str(world / "ceiling.json"), "--task", task,
                    "--condition", condition, "--align", "offline", "--out", str(target)]
            result = score.main(args)
            e2e = result["metrics"]["timing"]["end_to_end"]
            rows.append({"task": task, "condition": condition, "old_score": str(old_path.relative_to(ROOT)),
                         "new_score": str(target), "old_end_to_end": old["metrics"]["timing"]["end_to_end"],
                         "end_to_end": e2e,
                         "f1": result["metrics"]["activity"]["f1"]})
    aggregates = {}
    for cond in ("oracle_docs", "search"):
        selected = [r for r in rows if r["condition"] == cond]
        aggregates[cond] = {"n": len(selected)}
        for label, key in (("old_factor_error", "old_end_to_end"), ("corrected_factor_error", "end_to_end")):
            errors = [abs(math.log(r[key]["pred_median_days"] / r[key]["gold_median_days"])) for r in selected
                      if r[key]["pred_median_days"] and r[key]["gold_median_days"]]
            aggregates[cond][label] = math.exp(statistics.median(errors)) if errors else None
    return {"scorer_version": score.VERSION, "rows": rows, "aggregates": aggregates}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="runs/bayes_v3")
    ap.add_argument("--sweeps", type=int, default=400)
    ap.add_argument("--burn", type=int, default=150)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--cases", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--sensitivity", action="store_true")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    cfg = Config(sweeps=args.sweeps, burn=args.burn, chains=args.chains,
                 cases_per_draw=args.cases, seed=args.seed)
    source = ROOT / "runs/incremental/extract_synth"
    artifacts = ROOT / "benchmark/synth/worlds/W1/artifacts"
    evidence = load_cached(source, artifacts)
    write(out / "evidence.json", evidence)
    source_hashes = {name: hashlib.sha256((pathlib.Path(__file__).parent / name).read_bytes()).hexdigest()
                     for name in ("bayes_process.py", "bayes_evidence.py", "run_bayes_synth.py", "align.py", "metrics.py", "score.py")}
    start = time.monotonic()
    posterior, draws, cases = fit(evidence, cfg)
    posterior["model"]["model_id"] = "bayes_W1__J1__S03"
    for name, value in (("posterior.json", posterior), ("model.json", posterior["model"]),
                        ("draws.json", draws), ("case_draws.json", cases)):
        write(out / name, value)
    # Boundary: nothing above this line reads gold, ceilings, specs or solver answers.
    truth_root = ROOT / "benchmark/synth/worlds/W1/truth"
    gold = json.loads((truth_root / "processes/J1__S03.json").read_text())
    logs = json.loads((truth_root / "log/J1__S03.summary.json").read_text())
    evaluated = evaluation(posterior, draws, cases, gold, logs)
    write(out / "evaluation.json", evaluated)
    baselines = rescore_baselines(out)
    write(out / "baseline_rescoring.json", baselines)
    sensitivity = []
    if args.sensitivity:
        # Prespecified prior sensitivity, never selected by gold performance.
        for mean in (10., 40.):
            variant = replace(cfg, count_mean=mean, seed=cfg.seed)
            post, ds, cs = fit(evidence, variant)
            write(out / f"sensitivity_count_{int(mean)}.json", post)
            sensitivity.append({"count_prior_mean": mean, "step_count": post["step_count"],
                                "elapsed": post["model"]["process_timing"], "diagnostics": post["diagnostics"]})
    write(out / "manifest.json", {"task": "W1__J1__S03", "config": asdict(cfg),
                                   "seconds": time.monotonic() - start, "inference_inputs": ["evidence.json"],
                                   "evidence_sha256": hashlib.sha256((out / "evidence.json").read_bytes()).hexdigest(),
                                   "source_sha256": source_hashes,
                                   "baseline_comparison": "Same program, NOT equal information: legacy cache has 10 documents, omits process-level claims. No new LLM calls.",
                                   "sensitivity": sensitivity})
    print(json.dumps({"step_count": evaluated["step_count"], "f1": evaluated["activity"]["f1"],
                      "timing": evaluated["timing"]["end_to_end"], "diagnostics": posterior["diagnostics"],
                      "baselines": baselines["aggregates"]}, indent=2))
    return evaluated


if __name__ == "__main__":
    main()
