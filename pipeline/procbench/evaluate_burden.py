"""Post-fit evaluation of matched-clock operation and organization counts.

This module reads benchmark truth; it must never be imported by inference.
Inventory size, distinct operations on a case, and repeated visits are different
targets. This supplementary evaluation does not alter a saved model or score.
"""
import argparse
import hashlib
import json
import pathlib

import numpy as np

from .run_hierarchical import write


def realized_burden(truth, records):
    activities = {a['id']: a for a in truth['activities']}
    actors = {a['id']: a for a in truth['actors']}
    # Same terminal-artifact criterion used by the benchmark's simulator.
    decision_ids = {a['id'] for a in activities.values() if a.get('element_ref', '')
        and a['element_ref'].startswith('E') and a.get('visibility') == 'applicant_facing'
        and truth['terminal_artifact'] in a.get('artifacts_out', [])}
    if not decision_ids:
        raise ValueError('No benchmark decision endpoint; refusing to guess a case clock')
    rows = []
    unresolved_endpoints = 0
    for record in records:
        if record['censored'] or record['outcome'] not in {'approved', 'denied'}:
            continue
        positions = [i for i, visit in enumerate(record['path']) if visit['a'] in decision_ids]
        if not positions:
            unresolved_endpoints += 1
            continue
        # The simulator's decision_end is updated at each terminal visit.
        initial_path = record['path'][:positions[-1] + 1]
        distinct = {visit['a'] for visit in initial_path}
        agencies = {activities[a]['actor'] for a in distinct
                    if actors[activities[a]['actor']]['type'] in {'agency', 'external_government'}}
        agency_ops = {a for a in distinct if activities[a]['actor'] in agencies}
        rows.append({'distinct_operations': len(distinct), 'operation_visits': len(initial_path),
            'distinct_agency_operations': len(agency_ops), 'distinct_agencies': len(agencies)})
    if not rows:
        raise ValueError('No uncensored decided cases for burden evaluation')
    return {'n_cases': len(rows),
        'decided_cases_without_resolved_endpoint':unresolved_endpoints,
        'means': {key: float(np.mean([r[key] for r in rows])) for key in rows[0]},
        'scope': 'uncensored approved/denied cases with a resolved decision endpoint; arrival through decision, excluding later closeout/enforcement',
        'agency_identity_scope': 'distinct designed actor IDs; parent/division aliases are not collapsed',
        'work_hours': None, 'work_hours_reason': 'benchmark event logs contain elapsed time, not hands-on hours'}


def compare_burden(program, truth, records, log_summary):
    realized = realized_burden(truth, records)
    mapping = {'distinct_operations': 'expected_steps_per_case',
               'distinct_agency_operations': 'represented_agency_tasks_per_case',
               'distinct_agencies': 'expected_agencies_executing_work_per_case'}
    comparisons = {}
    for target, field in mapping.items():
        actual, estimate = realized['means'][target], program[field]
        lo, hi = estimate['ci90']
        comparisons[target] = {'truth_sample_mean': actual, 'posterior': estimate,
            'absolute_error_of_posterior_median': abs(estimate['median'] - actual),
            'interval_score90': hi-lo+20*max(lo-actual,0.)+20*max(actual-hi,0.),
            'ci90_covers_sample_mean': bool(lo <= actual <= hi)}
    timing = program['model']['process_timing']
    actual_p90 = log_summary['elapsed_days']['p90']
    lo, hi = timing['p90_ci90']
    return {'truth': realized, 'count_comparisons': comparisons,
        'p90': {'truth_days': actual_p90, 'estimate_days': timing['p90_days'],
                'ci90': [lo,hi], 'ci90_covers_truth': bool(lo <= actual_p90 <= hi),
                'absolute_log_error': float(abs(np.log(timing['p90_days'] / actual_p90)))},
        'caveats': ['Semantic activity granularity and agency identity differ between rendered evidence and designed truth',
            'Represented agency-task count excludes undocumented stages whose actor is unknown',
            'Distinct operation counts do not evaluate repeated-visit burden; repeated visits remain unmodeled',
            'Log-summary quantiles and count means are finite-simulation estimates, not noise-free population constants']}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    run, world, out = map(pathlib.Path, (args.run, args.world, args.out))
    if out.exists():
        raise ValueError('Choose a fresh evaluation directory')
    posterior = run / 'posterior.json'
    report = json.loads(posterior.read_text())  # Must exist before any gold read.
    manifest = json.loads((run / 'manifest.json').read_text())
    expected = manifest.get('posterior_sha256')
    actual = hashlib.sha256(posterior.read_bytes()).hexdigest()
    if expected and expected != actual:
        raise ValueError('Posterior differs from its saved manifest')
    results = {}
    for pid, program in report['programs'].items():
        truth = json.loads((world / 'truth/processes' / f'{pid}.json').read_text())
        records = [json.loads(line) for line in (world / 'truth/log' / f'{pid}.jsonl').read_text().splitlines() if line.strip()]
        logs = json.loads((world / 'truth/log' / f'{pid}.summary.json').read_text())
        results[pid] = compare_burden(program, truth, records, logs)
    write(out / 'burden.json', results)
    write(out / 'manifest.json', {'posterior_sha256': actual,
        'source_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'purpose': 'supplementary post-fit evaluation; no inference changes'})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
