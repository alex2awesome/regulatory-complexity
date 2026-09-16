"""Simulation-based calibration of the joint hierarchy on its own generative model.

Not a benchmark fit, not a claim of real-world calibration. Log-space reporting
bins form a genuine partition, so the interval likelihood is exactly the data
generating observation model in this check. Tests source/case/agency propagation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing
import pathlib
import time

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .latent_gaussian import diagnostics
from .run_hierarchical import write
from .validate_hierarchy import generated_evidence


def inference_seed(seed, rep):
    """Domain-separate inference from the truth/report generation stream.

    SeedSequence([seed, 0]) is identical to SeedSequence(seed). Reusing ``seed``
    for chain initialization therefore started legacy replicate zero at truth.
    Use a distinct stream even for zero, and keep the old artifacts for audit.
    """
    return int(np.random.SeedSequence([seed, rep, 0x5BC]).generate_state(1, dtype=np.uint64)[0])


def score_replicate(fitted, z, true_z):
    pars = [fitted.parameters(zz) for zz in z.reshape((-1, z.shape[-1]))]
    truth = fitted.parameters(true_z)
    rows = {}
    for name, true, samples in (
        ('global_location', truth['location'], np.array([p['location'] for p in pars])),
        ('agency_effect', truth['agency'][0], np.array([p['agency'][0] for p in pars])),
        ('observed_step', truth['mu'][0], np.array([p['mu'][0] for p in pars])),
        ('unmeasured_step', truth['mu'][3], np.array([p['mu'][3] for p in pars])),
        ('case_sigma', truth['sigma'], np.array([p['sigma'] for p in pars]))):
        lo, hi = np.quantile(samples, [.05, .95])
        rows[name] = {'covered90': bool(lo <= true <= hi),
                      'rank_fraction': float((samples < true).mean()),
                      'diagnostics': diagnostics(samples.reshape(z.shape[:2]))}
    return rows


def calibrate_one(rep, seed, cfg, out):
    rng = np.random.default_rng(np.random.SeedSequence([seed, rep]))
    cfg = replace(cfg, seed=inference_seed(seed, rep))
    e, _ = generated_evidence(seed=rep + 8, n_cases=3)
    model = HierarchicalModel([e], cfg)
    true_z = rng.normal(size=model.layout.size)
    pred, scales = model.predictions(true_z, [(0, 0)])
    for (_, m), prediction, scale in zip(model.observations, pred, scales):
        spread = 2. if rng.random() < cfg.outlier_probability else scale
        reported_log = prediction + spread * rng.standard_t(4)
        midpoint = round(reported_log / .25) * .25
        raw = next(x for x in e['measurements'] if x['id'] == m['id'])
        raw.update(value=None, lower=math.exp(midpoint - .125), upper=math.exp(midpoint + .125))
    fitted = HierarchicalModel([e], cfg)
    z, s, ll, _ = fitted.sample()
    rows = score_replicate(fitted, z, true_z)
    target = pathlib.Path(out) / f'replicate_{rep:03d}'
    write(target / 'evidence.json', e)
    write(target / 'result.json', rows)
    np.savez_compressed(target / 'draws.npz', z=z, true_z=true_z, structure=s, log_likelihood=ll)
    return rep, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replicates', type=int, default=20)
    ap.add_argument('--draws', type=int, default=500)
    ap.add_argument('--warmup', type=int, default=500)
    ap.add_argument('--seed', type=int, default=48210)
    ap.add_argument('--out', required=True)
    ap.add_argument('--workers', type=int, default=1)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving prior or unfinished calibration: choose a fresh output directory')
    cfg = Config(warmup=args.warmup, draws=args.draws, thin=1, chains=2,
                 max_unseen=0, unseen_mean=0, population_size=32)
    source_dir = pathlib.Path(__file__).parent
    names = ('calibrate_hierarchy.py', 'validate_hierarchy.py', 'bayes_hierarchy.py',
             'latent_gaussian.py', 'evidence_contract.py', 'schedule_kernel.py')
    write(out / 'manifest.json', {'seed': args.seed, 'config': asdict(cfg),
        'rng_protocol': 'domain-separated inference stream; data/truth stream unchanged',
        'source_sha256': {n: hashlib.sha256((source_dir / n).read_bytes()).hexdigest() for n in names}})
    for name in names:
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source_dir / name).read_bytes())
    completed = {}
    start = time.monotonic()
    def record(result):
        rep, rows = result
        completed[rep] = rows
        write(out / 'progress.json', {'completed': len(completed), 'replicates': completed})
        print(json.dumps({'replicate': rep + 1, 'completed': len(completed), 'seconds': time.monotonic() - start,
                          'coverage': {k: v['covered90'] for k, v in rows.items()}}), flush=True)
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as pool:
            jobs = [pool.submit(calibrate_one, rep, args.seed, cfg, str(out)) for rep in range(args.replicates)]
            for future in as_completed(jobs):
                record(future.result())
    else:
        for rep in range(args.replicates):
            record(calibrate_one(rep, args.seed, cfg, str(out)))
    results = [completed[i] for i in range(args.replicates)]
    aggregate = {key: {'coverage90': float(np.mean([r[key]['covered90'] for r in results])),
                       'rank_fractions': [r[key]['rank_fraction'] for r in results],
                       'runs_rhat_above_1_05': sum(r[key]['diagnostics']['rhat'] is None or
                                                 r[key]['diagnostics']['rhat'] > 1.05 for r in results)}
                 for key in results[0]}
    write(out / 'calibration.json', {'config': asdict(cfg), 'replicates': args.replicates,
          'aggregate': aggregate, 'runs': results, 'seconds': time.monotonic() - start, 'seed': args.seed,
          'scope': 'small simulation-based computational check; not enough replicates to certify calibration; does not test extraction, unknown DAGs, selection bias, or population-summary quadrature'})
    print(json.dumps(aggregate, indent=2))


if __name__ == '__main__':
    main()
