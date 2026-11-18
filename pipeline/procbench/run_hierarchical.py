"""Fit versioned evidence, save draws/provenance, optionally evaluate AFTER fitting.

Example:
  python -m pipeline.procbench.run_hierarchical --evidence runs/.../evidence.json \
      --out runs/bayes_v4/main --warmup 1000 --draws 1000
Inference inputs are explicit, public-evidence files; no task/spec lookup occurs.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from datetime import datetime, timezone
import hashlib
import json
import pathlib
import time
import sys
import scipy

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .schedule_kernel import ACCELERATOR
from .infra.manifest import write  # compatibility export for historical drivers
from .infra.scoring import interval_score


def sample_chain(evidence, cfg, index, out):
    """Independent CPU worker, not an LLM agent; identical per-chain RNG streams."""
    out = pathlib.Path(out)
    one = replace(cfg, chains=1, seed=cfg.seed + 104729 * index)
    model = HierarchicalModel(evidence, one)
    with (out / f'chain_{index}.progress.jsonl').open('w') as log:
        def progress(value):
            value['chain'] = index + 1
            log.write(json.dumps(value) + '\n')
            log.flush()
            if value['iteration'] == 1 or value['iteration'] % 1000 == 0:
                print(json.dumps(value), flush=True)
        z, structure, ll, calls = model.sample(progress)
    path = out / f'chain_{index}.npz'
    np.savez_compressed(path, z=z, structure=structure, log_likelihood=ll)
    return str(path), calls[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--thin", type=int, default=2)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--workers", type=int, default=1, help="Independent CPU chains, up to --chains")
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--population-size", type=int, default=128)
    ap.add_argument("--population-seed", type=int, default=817)
    ap.add_argument("--global-median", type=float, default=7.)
    ap.add_argument("--source-bias-sd", type=float, default=.35)
    ap.add_argument("--outcome-logit-sd", type=float, default=1.5,
                    help="Prior spread of unknown outcome proportions; zero fixes equal proportions")
    ap.add_argument("--unseen-mean", type=float, default=2.)
    ap.add_argument("--max-unseen", type=int, default=8)
    ap.add_argument("--no-process-claims", action="store_true")
    ap.add_argument("--no-hierarchy", action="store_true")
    ap.add_argument("--evaluate-world", help="Optional evaluation only after posterior saved, e.g. benchmark/synth/worlds/W1")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError("Preserving existing or unfinished run: choose a fresh output directory")
    out.mkdir(parents=True, exist_ok=True)
    cfg = Config(warmup=args.warmup, draws=args.draws, thin=args.thin, chains=args.chains,
                 seed=args.seed, population_size=args.population_size, population_seed=args.population_seed,
                 global_median=args.global_median, source_bias_sd=args.source_bias_sd,
                 outcome_logit_sd=args.outcome_logit_sd,
                 unseen_mean=args.unseen_mean, max_unseen=args.max_unseen,
                 use_process_claims=not args.no_process_claims, use_hierarchy=not args.no_hierarchy)
    inputs = [pathlib.Path(p) for p in args.evidence]
    evidence = [json.loads(p.read_text()) for p in inputs]
    model = HierarchicalModel(evidence, cfg)
    start = time.monotonic()
    code = pathlib.Path(__file__).parent
    manifest = {"config": asdict(cfg), "started_utc": datetime.now(timezone.utc).isoformat(),
                "environment": {"python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__,
                                "scheduling_backend": ACCELERATOR},
                "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                "source_sha256": {name: hashlib.sha256((code / name).read_bytes()).hexdigest()
                                  for name in ("bayes_hierarchy.py", "bayes_effort.py", "latent_gaussian.py", "evidence_contract.py", "run_hierarchical.py", "schedule_kernel.py")},
                "n_observations": len(model.observations), "dimensions": model.layout.size,
                "hidden_truth_read_during_inference": False}
    write(out / "manifest.json", manifest)
    for name in manifest['source_sha256']:
        snapshot = out / 'source' / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((code / name).read_bytes())
    write(out / "evidence.json", evidence)
    print(json.dumps({"dimensions": model.layout.size, "observations": len(model.observations),
                      "blocks": len(model.blocks), "programs": [p.id for p in model.processes]}), flush=True)
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=min(args.workers, cfg.chains),
                                 mp_context=multiprocessing.get_context('spawn')) as pool:
            jobs = [pool.submit(sample_chain, evidence, cfg, i, str(out)) for i in range(cfg.chains)]
            completed = [job.result() for job in jobs]
        pieces = [np.load(path) for path, _ in completed]
        chains = np.concatenate([p['z'] for p in pieces])
        structure = np.concatenate([p['structure'] for p in pieces])
        likelihood = np.concatenate([p['log_likelihood'] for p in pieces])
        calls = [c for _, c in completed]
    else:
        with (out / "progress.jsonl").open("w") as log:
            def progress(value):
                line = json.dumps(value)
                log.write(line + "\n")
                log.flush()
                print(line, flush=True)
            chains, structure, likelihood, calls = model.sample(progress)
    np.savez_compressed(out / "draws.npz", z=chains, structure=structure, log_likelihood=likelihood)
    report = model.report(chains, structure, likelihood)
    report['posterior_converged_scope'] = 'elapsed hierarchy; work-hour channels need separate diagnostics'
    # A potentially slower work-hour stage must not hide completed elapsed
    # diagnostics. This is explicitly partial, not the final composite result.
    write(out / 'elapsed_posterior.json',report)
    manifest.update(elapsed_completed_utc=datetime.now(timezone.utc).isoformat(),
        elapsed_posterior_sha256=hashlib.sha256((out/'elapsed_posterior.json').read_bytes()).hexdigest())
    write(out/'manifest.json',manifest)
    from .bayes_effort import fit_effort
    with (out/'work_progress.jsonl').open('w') as work_log:
        def work_progress(value):
            work_log.write(json.dumps(value)+'\n')
            work_log.flush()
            if value['iteration']==1 or value['iteration']%1000==0:
                print(json.dumps(dict(value,phase='separate work-hour inference')),flush=True)
        effort, effort_arrays = fit_effort(evidence, cfg,progress=work_progress)
    report['effort'] = effort
    for channel, array in effort_arrays.items():
        np.savez_compressed(out / f'{channel}.npz', **array)
    write(out / "posterior.json", report)
    for pid, result in report["programs"].items():
        write(out / f"{pid}.model.json", result["model"])
    manifest.update({"seconds": time.monotonic() - start, "likelihood_calls": calls,
                     "completed_utc": datetime.now(timezone.utc).isoformat(),
                     "posterior_sha256": hashlib.sha256((out / "posterior.json").read_bytes()).hexdigest()})
    write(out / "manifest.json", manifest)
    # Explicit boundary: all inference artifacts persisted before ANY truth read.
    if args.evaluate_world:
        evaluated = evaluate(report, pathlib.Path(args.evaluate_world))
        write(out / "evaluation.json", evaluated)
    print(json.dumps({"out": str(out), "seconds": manifest["seconds"],
                      "converged": report["posterior_converged"], "flagged": len(report["diagnostics_flagged"]),
                      "timing": {pid: r['model']['process_timing'] for pid, r in report['programs'].items()}}), flush=True)
    return report


def evaluate(report, world):
    from . import align, metrics
    results = {}
    for pid, result in report["programs"].items():
        truth = json.loads((world / "truth/processes" / f"{pid}.json").read_text())
        logs = json.loads((world / "truth/log" / f"{pid}.summary.json").read_text())
        pred, gold = align.load_model(result["model"]), align.load_model(truth)
        pairs = align.offline_align(pred, gold)
        primary = [pair for pair in pairs if pair['relation'] == 'primary']
        actual = logs["elapsed_days"]["median"]
        interval = result["model"]["process_timing"]["median_ci90"]
        results[pid] = {"scoring_version": "procbench-score/3", "activity": metrics.activity_metrics(pred, gold, pairs, None),
                       "activity_one_to_one_backbone": metrics.activity_metrics(pred, gold, primary, None),
                       "timing": metrics.timing_metrics(pred, gold, pairs, log_summary={"median_days": actual}),
                       "posterior_timing": posterior_timing_score(result['process_median_draws'], actual),
                       "median_ci90_covers_truth": interval[0] <= actual <= interval[1],
                       "count_truth": len(truth["activities"]), "count_posterior": result["step_count"],
                       "represented_count_absolute_error": abs(result['represented_count'] - len(truth['activities'])),
                       "alignment": pairs,
                       "scope_note": "Legacy log-summary elapsed_days ends at the last recorded decision, whereas this model targets the initial decision. Repeat-decision cases therefore have an estimand mismatch; secondary submission-start estimate also reported. Undisclosed-stage and route misspecification remain possible."}
    return results


def posterior_timing_score(draws, actual):
    """Proper scores on log median days, not sums of per-step medians.

    The target is the generator's reported sample median, which itself can have
    simulation noise; this is not a score on an observed individual case.
    """
    x = np.sort(np.log(np.asarray(draws)))
    y, n = np.log(actual), len(x)
    lo, hi = np.quantile(x, [.05, .95])
    crps = np.mean(np.abs(x - y)) - np.sum((2 * np.arange(1, n + 1) - n - 1) * x) / n ** 2
    interval = interval_score(lo, hi, y)
    return {'truth_median_days': actual, 'absolute_log_error': float(abs(np.median(x) - y)),
            'crps_log_median': float(crps), 'interval_score90_log_median': float(interval),
            'target': 'generator log-summary sample median, not a new individual-case duration'}


if __name__ == "__main__":
    main()
