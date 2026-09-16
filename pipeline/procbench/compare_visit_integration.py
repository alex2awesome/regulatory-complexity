"""Evaluate the frozen v6 development integration, not a matched-LLM benchmark.

Every condition and failure is retained. Scoring requires completed fits passing
their declared numerical gates and checks that mixed evidence adds to, rather than
changes, the timing-only observations. This evaluator is never imported by inference.
"""
import argparse
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import json
import math
import pathlib

import numpy as np

from .bayes_trace_hierarchy import Config, VisitHierarchy
from .latent_gaussian import diagnostics
from .reconcile_evidence import digest, write


TARGETS = {
    'mean_visit_count': ('expected_visits', True),
    'mean_operation_count': ('distinct_operations', True),
    'mean_agency_count': ('agencies', True),
    'mean_payer_hours': ('mean_payer_hours', True),
    'mean_agency_hours': ('mean_agency_hours', True),
    'repeat_any:corrections': ('probability_any_correction', False),
    'repeat_continue:corrections': ('probability_continue', False),
}


def interval_score(estimate, truth, logarithmic):
    median, (lo, hi) = estimate['median'], estimate['ci90']
    if (not all(math.isfinite(v) for v in (median, lo, hi, truth)) or not lo <= median <= hi
            or (logarithmic and min(lo, hi, median, truth) <= 0)):
        raise ValueError('Invalid posterior interval or truth')
    transform = math.log if logarithmic else float
    m, lower, upper, target = map(transform, (median, lo, hi, truth))
    score = upper - lower + 20 * max(0., lower - target, target - upper)
    return dict(truth=truth, posterior=estimate, scale='log' if logarithmic else 'probability',
                absolute_error=abs(m - target), interval_score_90=score,
                covered_90=lo <= truth <= hi)


def assert_nested_evidence(timing, mixed):
    a = {p['id']: p for p in timing['programs']}
    b = {p['id']: p for p in mixed['programs']}
    if set(a) != set(b):
        raise ValueError('The conditions do not contain the same programs')
    for pid, p in a.items():
        q = b[pid]
        if p['routes'] != q['routes']:
            raise ValueError('Route hypotheses or their priors changed between conditions')
        larger = {o['id']: o for o in q['observations']}
        if len(larger) != len(q['observations']) or any(larger.get(o['id']) != o for o in p['observations']):
            raise ValueError('Mixed evidence changed or removed an original timing claim')
        if any(r not in q.get('rate_observations', []) for r in p.get('rate_observations', [])):
            raise ValueError('Mixed evidence removed an original counted cohort')


def verified_fit(path, expected_data):
    root = pathlib.Path(path)
    manifest = json.loads((root / 'manifest.json').read_text())
    if (not manifest.get('completed_utc') or
            manifest.get('posterior_sha256') != digest((root / 'posterior.json').read_bytes())):
        raise ValueError('Only a completed, unchanged fit can be evaluated')
    report = json.loads((root / 'posterior.json').read_text())
    if (not report.get('numerically_usable') or not report.get('posterior_converged') or
            report.get('diagnostics_flagged') or not report['precision']['likelihood_acceptable'] or
            not report['precision']['predictions_acceptable']):
        raise ValueError('Numerical gates failed; do not score this fit as validated inference')
    data = json.loads((root / 'data.json').read_text())
    if data != expected_data:
        raise ValueError('Fit input differs from the frozen development condition')
    base = manifest
    while 'input_sha256' not in base:
        base = base['base_manifest']
    for name, expected in base['input_sha256'].items():
        if digest(pathlib.Path(name).read_bytes()) != expected:
            raise ValueError('Original inference input changed')
    with np.load(root / 'draws.npz') as draws:
        model = VisitHierarchy(data, replace(Config(**manifest['config']), population_size=16))
        report['agency_inventory_diagnostics'] = agency_diagnostics(model, draws['z'], draws['structures'])
    flagged = {name: row for name, row in report['agency_inventory_diagnostics'].items()
               if row['rhat'] is None or row['rhat'] > 1.01 or row['ess_bulk'] < 400 or row['ess_tail'] < 200}
    if flagged:
        raise ValueError('Derived agency-inventory diagnostics failed: ' + json.dumps(flagged))
    return manifest, report


def agency_diagnostics(model, states, structures):
    """Check derived inventory means, in addition to the fitter's coordinate gates.

    For an agency absent under some routes, presence and conditional-mean chains
    are both checked. Conditional chains contain successive presence visits and
    are truncated to their common length solely for equal-length diagnostics.
    These are diagnostic sequences, not replacements for the posterior samples.
    """
    c = model.cfg
    mu = (math.log(c.elapsed_prior_median) + c.location_sd * states[..., model.location[0], None]
          + c.agency_sd * states[..., model.agency[0]][..., model.agency_indices]
          + c.task_sd * states[..., model.task[0]][..., model.task_indices]
          + c.operation_sd * states[..., model.operation[0]])
    sigma = np.exp(math.log(c.case_log_sd_median) + c.case_log_sd_prior * states[..., model.sigma[0]])
    means = np.exp(mu + .5 * (sigma ** 2 + c.common_case_sd ** 2)[..., None])
    result = {}
    agencies = {o['op'].actor_id for o in model.operations
                if o['op'].actor_role == 'agency' and o['op'].actor_id is not None}
    for agency in sorted(agencies):
        numerator, count = np.zeros(states.shape[:2]), np.zeros(states.shape[:2])
        for pi, p in enumerate(model.programs):
            for ri, route in enumerate(p['routes']):
                indices = [idx for idx, op in zip(route['indices'], route['operations'])
                           if op.actor_role == 'agency' and op.actor_id == agency]
                if indices:
                    mask = structures[..., pi] == ri
                    numerator += mask * means[..., indices].sum(axis=-1)
                    count += mask * len(indices)
        present = count > 0
        result[agency + ':presence'] = diagnostics(present.astype(float))
        conditional = [numerator[i, p] / count[i, p] for i, p in enumerate(present)]
        length = min(map(len, conditional))
        row = (diagnostics(np.stack([v[:length] for v in conditional])) if length >= 8 else
               dict(rhat=None, ess_bulk=0., ess_tail=0.))
        row['conditional_draws_per_chain_checked'] = length
        result[agency + ':inventory_mean_conditional'] = row
    return result


def verified_truth(data_root, data, generator):
    """Replay the hashed, saved development generator rather than trust edited truth."""
    data_root = pathlib.Path(data_root)
    source = data_root / 'generator_source.py'
    if digest(source.read_bytes()) != generator['source_sha256']:
        raise ValueError('Saved development generator changed')
    spec = importlib.util.spec_from_file_location('pipeline.procbench._frozen_visit_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    regenerated, truth = module.generate(seed=generator['seed'])
    if regenerated != data:
        raise ValueError('Saved generator no longer reproduces the frozen observations')
    if json.loads((data_root / 'truth.json').read_text()) != truth:
        raise ValueError('Saved truth disagrees with the frozen generating process')
    return truth


def compare(reports, truth):
    conditions = {}
    for condition, report in reports.items():
        if set(report['programs']) != set(truth):
            raise ValueError('Posterior and truth program sets differ')
        programs, aggregate = {}, defaultdict(list)
        for pid, row in report['programs'].items():
            metrics = {}
            for name, (target, logarithmic) in TARGETS.items():
                score = interval_score(row['metrics'][name], truth[pid][target], logarithmic)
                if name in {'mean_payer_hours', 'mean_agency_hours'}:
                    channel = name.removeprefix('mean_')
                    score['direct_resource_evidence'] = channel not in row['resource_channels_without_direct_evidence']
                metrics[name] = score
                aggregate[name].append(score)
            probability = row['route_probabilities'][truth[pid]['route']]
            programs[pid] = dict(metrics=metrics, true_route_posterior_frequency=probability,
                true_route_binary_brier_score=(1 - probability) ** 2,
                process_predictions_without_truth_score={k: v for k, v in row['metrics'].items()
                    if k.endswith('_days')},
                resource_channels_without_direct_evidence=row['resource_channels_without_direct_evidence'])
        averages = {name: dict(programs=len(rows),
            mean_absolute_error=sum(r['absolute_error'] for r in rows) / len(rows),
            mean_interval_score_90=sum(r['interval_score_90'] for r in rows) / len(rows))
            for name, rows in aggregate.items()}
        agency_truth = {}
        for row in truth.values():
            for agency, target in row['agency_inventory_mean_cycle_days'].items():
                if agency in agency_truth and agency_truth[agency] != target:
                    raise ValueError('This evaluator expects the same generating agency inventory across programs')
                agency_truth[agency] = target
        agency_metrics = {agency: interval_score(report['agencies'][agency]['inventory_mean_cycle_days'], target, True)
                          for agency, target in agency_truth.items()}
        conditions[condition] = dict(programs=programs, averages_by_metric=averages,
            agency_inventory_metrics=agency_metrics, agency_reports=report['agencies'],
            agency_inventory_diagnostics=report.get('agency_inventory_diagnostics'),
            hierarchy_design=report['hierarchy_design'])
    return dict(conditions=conditions, matched_llm_comparison=False,
        held_out_text_pipeline_validation=False, calibration_certificate=False,
        limitations=['Two programs in one favorable fixed-truth development experiment, not independent replications.',
            'Explicit complete counts and independent rework cohorts are supplied to the mixed condition.',
            'Timing-only work amounts have no direct resource evidence; their wide intervals are prior-driven.',
            'Agency inventory summaries are conditional on represented operations, not intrinsic causal effects.',
            'Process timing quantiles are reported but not scored: the frozen truth artifact has no such targets.',
            'Route frequencies are Monte Carlo estimates; a sampled frequency of one is not proof of certainty.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('timing-run', 'mixed-run', 'data', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    out, data_root = pathlib.Path(args.out), pathlib.Path(args.data)
    if out.exists():
        raise ValueError('Choose a fresh comparison directory')
    generator = json.loads((data_root / 'manifest.json').read_text())
    data = {}
    for name in ('timing_only', 'mixed_evidence'):
        path = data_root / (name + '.json')
        if digest(path.read_bytes()) != generator['input_sha256'][name]:
            raise ValueError('Frozen development input changed')
        data[name] = json.loads(path.read_text())
    assert_nested_evidence(data['timing_only'], data['mixed_evidence'])
    manifests, reports = {}, {}
    for name, path in [('timing_only', args.timing_run), ('mixed_evidence', args.mixed_run)]:
        manifests[name], reports[name] = verified_fit(path, data[name])
    numerical = {'seed', 'draws', 'warmup', 'population_size'}
    configs = [{k: v for k, v in m['config'].items() if k not in numerical} for m in manifests.values()]
    if configs[0] != configs[1]:
        raise ValueError('Statistical settings changed between the two conditions')
    truth_path = data_root / 'truth.json'
    result = compare(reports, verified_truth(data_root, data, generator))
    write(out / 'comparison.json', result)
    write(out / 'manifest.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        timing_run=args.timing_run, mixed_run=args.mixed_run, inference_manifests=manifests,
        frozen_generator_replay_verified=True, generator_manifest=generator,
        truth_sha256=digest(truth_path.read_bytes()), source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        comparison_sha256=digest((out / 'comparison.json').read_bytes())))
    print(json.dumps({name: row['averages_by_metric'] for name, row in result['conditions'].items()}), flush=True)


if __name__ == '__main__':
    main()
