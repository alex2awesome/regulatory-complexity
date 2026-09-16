"""Marginal-prior stationarity checks for individual interwoven MCMC updates.

With likelihood constant, independent prior draws must stay prior distributed.
This is a necessary check, not a proof of posterior stationarity or mixing.
"""
import argparse
from dataclasses import asdict
import json
import pathlib
import time

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .run_hierarchical import write
from .validate_hierarchy import generated_evidence


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--replicates', type=int, default=10000)
    ap.add_argument('--with-likelihood', action='store_true',
                    help='Generate new data from each prior state and test joint data/state stationarity')
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    e, _ = generated_evidence(n_cases=3)
    cfg = Config(max_unseen=0, unseen_mean=0, population_size=32)
    model = HierarchicalModel([e], cfg)
    if not args.with_likelihood:
        model.log_likelihood = lambda *a, **kw: 0.
    kernels = {
        'source_location': lambda z, ll, rng: model.source_location_update(z, [(0,0)], ll, rng)[0],
        'centered_step': lambda z, ll, rng: model.centered_step_update(z, [(0,0)], ll, rng)[0],
        'decomposition': lambda z, ll, rng: model.decomposition_update(z, rng),
        'centered_scales': lambda z, ll, rng: model.centered_scale_update(z, rng),
        'centered_cases': lambda z, ll, rng: model.centered_case_update(z, [(0,0)], ll, rng)[0],
        'exchange': lambda z, ll, rng: model.exchange_unmeasured_steps(z, [(0,0)], ll, rng)[0]}
    results = {}
    start = time.monotonic()
    for name, kernel in kernels.items():
        rng = np.random.default_rng(87213)
        first = rng.normal(size=(args.replicates, model.layout.size))
        second, data_means = [], []
        for z in first:
            if args.with_likelihood:
                pred, scale = model.predictions(z, [(0,0)])
                scale = np.where(rng.random(len(pred)) < cfg.outlier_probability, 2., scale)
                logs = pred + scale * rng.standard_t(4, size=len(pred))
                mid = np.round(logs / .25) * .25
                model.bounds = np.column_stack((mid-.125, mid+.125))
                data_means.append(np.mean(mid))
            second.append(kernel(z, model.log_likelihood(z, [(0,0)]), rng))
        second = np.array(second)
        delta = second - first
        # Paired differences are more sensitive than comparing two sample means.
        se = delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
        stat = delta.mean(axis=0) / np.maximum(se, 1e-100)
        square_delta = second ** 2 - first ** 2
        sqse = square_delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
        sqstat = square_delta.mean(axis=0) / np.maximum(sqse, 1e-100)
        results[name] = {'max_abs_paired_mean_z': float(np.max(np.abs(stat))),
            'max_abs_paired_second_moment_z': float(np.max(np.abs(sqstat))),
            'global_mean_shift_z': float(stat[0]), 'global_second_moment_shift_z': float(sqstat[0]),
            'mean_test_by_coordinate': stat.tolist(), 'second_moment_test_by_coordinate': sqstat.tolist()}
        if args.with_likelihood:
            cross_delta = delta * np.array(data_means)[:,None]
            cross_se = cross_delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
            cross_stat = cross_delta.mean(axis=0) / np.maximum(cross_se,1e-100)
            results[name]['max_abs_data_cross_moment_z'] = float(np.max(np.abs(cross_stat)))
            results[name]['data_cross_moment_test_by_coordinate'] = cross_stat.tolist()
        print(json.dumps({name: {k: v for k,v in results[name].items() if not isinstance(v,list)}}), flush=True)
    write(out/'checks.json', dict(config=asdict(cfg), replicates=args.replicates,
        with_likelihood=args.with_likelihood,
        results=results, seconds=time.monotonic()-start,
        caveat='Many coordinates tested; inspect systematic large shifts, not a single unadjusted p-value'))


if __name__ == '__main__':
    main()
