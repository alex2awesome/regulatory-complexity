"""Paired controlled recovery of joint agency/task timing and repeat counts."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import math
import multiprocessing
import pathlib

import numpy as np

from .bayes_repeat_timing import Config, fit_repeat_timing, refinement_check
from .phase_mixture import quantile_density
from .reconcile_evidence import digest, write
from .rework_counts import ReworkLaw


def generate_data(replicates, seed, cfg):
    law = ReworkLaw(.6, cfg.probability_continue)
    jobs = []
    for replicate in range(replicates):
        rng = np.random.default_rng(seed+104729*replicate)
        rounds = np.array([law.quantile(float(u)) for u in rng.random(100)])
        cycles = np.exp(math.log(7.)+cfg.case_log_sd*rng.normal(size=100))
        total = cfg.fixed_other_days+(1+rounds)*cycles
        tasks = np.exp(math.log(7.)+cfg.case_log_sd*rng.normal(size=5))
        independent_cohort = [int(rng.binomial(20, law.probability_any)), 20]
        for label, n, direct, cohort in (
                ('10_totals', 10, [], None),
                ('10_totals_plus_20_rework_cases', 10, [], independent_cohort),
                ('10_totals_plus_5_task_times', 10, tasks.tolist(), None),
                ('100_totals', 100, [], None)):
            jobs.append(dict(replicate=replicate, condition=label, total_days=total[:n].tolist(),
                             task_cycle_days=direct, independent_rework_cohort=cohort))
    return jobs


def worker(job, cfg, out):
    folder = pathlib.Path(out)/f"{job['replicate']:02d}_{job['condition']}"
    def fit(configuration):
        return fit_repeat_timing(job['total_days'], job['task_cycle_days'],
                                 job['independent_rework_cohort'], configuration)
    base = fit(cfg)
    checks = []
    for _ in range(3):
        refined = replace(cfg, location_points=2*cfg.location_points-1,
                          probability_points=2*cfg.probability_points,
                          max_additional_rounds=2*cfg.max_additional_rounds)
        finer = fit(refined)
        check = dict(base_config=asdict(cfg), finer_config=asdict(refined),
                     **refinement_check(base, finer))
        checks.append(check)
        cfg = refined
        if check['acceptable']:
            break
        base = finer
    result = {k: v for k, v in finer.items()
              if k not in {'location_grid', 'probability_grid', 'posterior_mass'}}
    result.update(replicate=job['replicate'], condition=job['condition'],
                  config=asdict(cfg), numerical_checks=checks, numerically_usable=checks[-1]['acceptable'])
    write(folder/'posterior.json', result)
    np.savez_compressed(folder/'grid.npz', **{k: finer[k] for k in
                        ('location_grid', 'probability_grid', 'posterior_mass')})
    print(json.dumps(dict(replicate=job['replicate'], condition=job['condition'],
                          numerically_usable=result['numerically_usable'])), flush=True)
    return result


def score(interval, truth):
    lo, hi = np.log(interval['ci90'])
    target = math.log(truth)
    return dict(absolute_log_error=abs(math.log(interval['median'])-target),
                interval_score90_log=float(hi-lo+20*max(lo-target, 0)+20*max(target-hi, 0)),
                covers90=bool(lo <= target <= hi))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--replicates', type=int, default=8)
    ap.add_argument('--seed', type=int, default=2026091901)
    ap.add_argument('--workers', type=int, default=2)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists() or args.replicates < 1 or args.workers < 1:
        raise ValueError('Choose a fresh output directory and positive run counts')
    cfg = Config()
    jobs = generate_data(args.replicates, args.seed, cfg)
    source = pathlib.Path(__file__).parent
    names = ['validate_repeat_timing.py', 'bayes_repeat_timing.py', 'rework_counts.py',
             'phase_mixture.py', 'measurement_kernel.py']
    manifest = dict(started_utc=datetime.now(timezone.utc).isoformat(), seed=args.seed,
        replicates=args.replicates, initial_config=asdict(cfg),
        scope='Favorable joint timing/rework component recovery, not text-pipeline calibration or held-out W1 evaluation',
        source_sha256={name: digest((source/name).read_bytes()) for name in names})
    write(out/'manifest.json', manifest)
    write(out/'datasets.json', jobs)
    for name in names:
        target = out/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source/name).read_bytes())
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = [pool.submit(worker, job, cfg, str(out)) for job in jobs]
        fits = [future.result() for future in futures]
    # Score only after the saved fits and their numerical checks are available.
    law = ReworkLaw(.6, cfg.probability_continue)
    indices = np.arange(cfg.max_additional_rounds+1)
    probabilities = np.array([law.probability(int(k)) for k in indices])
    cycle_quantile, _ = quantile_density(.5, np.log1p(indices), probabilities, cfg.case_log_sd)
    truth = dict(agency_mean_cycle_days=7*math.exp(.5*cfg.case_log_sd**2),
                 expected_visit_count=4+law.mean_additional_rounds,
                 population_process_median_days=cfg.fixed_other_days+7*math.exp(cycle_quantile))
    rows = []
    for fit in fits:
        rows.append(dict(replicate=fit['replicate'], condition=fit['condition'],
            numerically_usable=fit['numerically_usable'],
            posterior_location_rework_correlation=fit['posterior_location_rework_correlation'],
            scores={target: score(fit[target], value) for target, value in truth.items()}))
    aggregate = {}
    for condition in sorted({r['condition'] for r in rows}):
        selected = [r for r in rows if r['condition'] == condition]
        aggregate[condition] = dict(replicates=len(selected),
            all_numerically_usable=all(r['numerically_usable'] for r in selected),
            mean_posterior_location_rework_correlation=float(np.mean([
                r['posterior_location_rework_correlation'] for r in selected])),
            scores={target: dict(
                mean_absolute_log_error=float(np.mean([r['scores'][target]['absolute_log_error'] for r in selected])),
                mean_interval_score90_log=float(np.mean([r['scores'][target]['interval_score90_log'] for r in selected])),
                covered90=sum(r['scores'][target]['covers90'] for r in selected)) for target in truth})
    write(out/'results.json', rows)
    write(out/'summary.json', dict(truth=truth, conditions=aggregate,
        caveats=['Known case spread, continuation rate, fixed other work and complete unselected observations are favorable assumptions.',
                 'Within-case repeat cycle durations are perfectly correlated in this component.',
                 'The shared parameter describes one agency/task family; the full multi-agency/task hierarchy is not fitted here.',
                 'Independent rework-cohort counts are real simulated counts, not informal frequency denominators.',
                 'One fixed truth and eight replicates do not establish calibration or LLM superiority.']))
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),
        all_numerically_usable=all(r['numerically_usable'] for r in rows),
        summary_sha256=digest((out/'summary.json').read_bytes()))
    write(out/'manifest.json', manifest)
    print(json.dumps(aggregate), flush=True)


if __name__ == '__main__':
    main()
