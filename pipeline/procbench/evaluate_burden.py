"""Post-fit evaluation of matched-clock operation and organization counts.

This module reads benchmark truth; it must never be imported by inference.
Inventory size, distinct operations on a case, and repeated visits are different
targets. This supplementary evaluation does not alter a saved model or score.
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
from datetime import datetime, timezone

import numpy as np
from .infra.scoring import interval_score, log_interval_score

from .infra.manifest import RunManifest, write


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
            'interval_score90': interval_score(lo, hi, actual),
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


V6_CLOCKS = {'initial_decision':'initial_decision', 'final_decision':'last_decision',
             'modeled_work_end':'modeled_work_end'}


def _finite_number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def _event_value(record,event,*,observed_only):
    """Do not substitute the legacy last-decision clock for a missing first one."""
    clock=record.get('event_clocks',{}).get(event)
    if not isinstance(clock,dict):
        return None
    value=clock.get('elapsed_days')
    if not _finite_number(value) or value<0 or clock.get('end_date') is None:
        return None
    if observed_only and clock.get('censored') is not False:
        return None
    return float(value)


def realized_v6_burden(truth,records):
    """Full-path counts and explicitly named event clocks on a stated cohort.

    Primary cohort matches the published development audit: cases whose legacy
    final status is uncensored approved/denied. Counts include their whole
    simulated path, not just visits before the first decision. Event-specific
    observed cohorts are also reported; these populations are not interchangeable.
    """
    activities={a['id']:a for a in truth['activities']}
    actors={a['id']:a for a in truth['actors']}
    decided=[r for r in records if r.get('censored') is False and
             r.get('outcome') in ('approved','denied')]
    if not decided:
        raise ValueError('No uncensored decided cases for V6 evaluation')
    count_rows=[]
    for record in decided:
        path=record['path']
        ids={v['a'] for v in path}
        if ids-activities.keys():
            raise ValueError('Event log references an unknown designed activity')
        agencies={activities[a]['actor'] for a in ids
                  if actors[activities[a]['actor']]['type'] in {'agency','external_government'}}
        applicant={a for a in ids if activities[a].get('visibility')=='applicant_facing'}
        count_rows.append(dict(mean_visit_count=len(path),mean_operation_count=len(ids),
            mean_agency_count=len(agencies),mean_applicant_visit_count=sum(v['a'] in applicant for v in path),
            mean_applicant_operation_count=len(applicant)))
    clocks={}
    for model_clock,event in V6_CLOCKS.items():
        values=[v for record in decided
                if (v:=_event_value(record,event,observed_only=True)) is not None]
        event_values=[v for record in records
                      if (v:=_event_value(record,event,observed_only=True)) is not None]
        def stats(values):
            return dict(n=len(values),median=float(np.median(values)) if values else None,
                        p90=float(np.quantile(values,.9)) if values else None)
        clocks[model_clock]=dict(generator_event=event,primary=stats(values),
            primary_cases_without_observed_event=len(decided)-len(values),
            all_observed_events=stats(event_values))
    fees=[r['fees_paid'] for r in decided if _finite_number(r.get('fees_paid'))]
    return dict(n_records=len(records),n_cases=len(decided),
        primary_cohort='uncensored finally approved/denied cases; finite simulated cohort, not an unconditional population',
        count_scope='complete simulated paths, including repeats and post-decision work; not a decision-truncated visit count',
        means={key:float(np.mean([r[key] for r in count_rows])) for key in count_rows[0]},
        clocks=clocks,
        mean_fee_total=float(np.mean(fees)) if len(fees)==len(decided) else None,
        fee_scope='all recorded fees_paid over the complete simulated case path',
        legacy_elapsed_median_days=float(np.median([r['elapsed_days'] for r in decided])),
        work_hours=None,work_hours_reason='No independent hands-on labor measurements in these event logs')


def _compare_scalar(estimate,actual):
    if 'conditional_on_defined' in estimate:
        return dict(scored=False,reason='Route-conditional prediction requires a matching conditional truth population',
                    posterior=estimate)
    if actual is None:
        return dict(scored=False,reason='Matching truth quantity is unavailable',posterior=estimate)
    point=estimate.get('median')
    bounds=estimate.get('ci90',[])
    if len(bounds)!=2 or not all(_finite_number(v) for v in (point,*bounds,actual)):
        raise ValueError('Evaluation requires finite posterior medians and 90-percent intervals')
    lo,hi=bounds
    if lo>hi or not lo<=point<=hi:
        raise ValueError('Invalid posterior central interval')
    positive=min(lo,hi,point,actual)>0
    return dict(scored=True,truth=actual,posterior=estimate,
        posterior_median_over_truth=point/actual if actual else None,
        absolute_error_of_posterior_median=abs(point-actual),
        absolute_log_error=abs(math.log(point/actual)) if point>0 and actual>0 else None,
        interval_score90=interval_score(lo,hi,actual),
        interval_score90_log=log_interval_score(lo,hi,actual) if positive else None,
        ci90_covers_truth=bool(lo<=actual<=hi))


def compare_burden_v6(program,truth,records):
    if program.get('elapsed_time_unit','calendar_days') != 'calendar_days':
        raise ValueError('This evaluator requires calendar_days; business-day truth conversion is not implemented')
    if program.get('inventory_granularity','detailed_operations') != 'detailed_operations':
        raise ValueError('Aggregate phases require a separately matched phase truth estimand')
    realized=realized_v6_burden(truth,records)
    comparisons={}
    unsupported={}
    for name,prediction in program['metrics'].items():
        if name in realized['means']:
            actual=realized['means'][name]
        elif name=='mean_fee_total':
            actual=realized['mean_fee_total']
        else:
            clock=next((event for event in V6_CLOCKS if name in
                        (event+'_median_days',event+'_p90_days')),None)
            if clock is None:
                unsupported[name]='No matched truth estimand implemented; not counted as a successful score'
                continue
            quantile='p90' if name.endswith('_p90_days') else 'median'
            actual=realized['clocks'][clock]['primary'][quantile]
        comparisons[name]=_compare_scalar(prediction,actual)
    clock=comparisons.get('initial_decision_median_days',{})
    ratio=clock.get('posterior_median_over_truth')
    recovery=bool(clock.get('scored') and ratio is not None and .7<=ratio<=1.4 and
                  clock['ci90_covers_truth'])
    return dict(truth=realized,comparisons=comparisons,unsupported_metrics=unsupported,
        absent_burden_channels=[name for name in ('mean_fee_total','mean_applicant_visit_count',
            'mean_applicant_operation_count','mean_payer_hours','mean_agency_hours') if name not in program['metrics']],
        development_phase1_clock_recovery_pass=recovery,
        recovery_gate_definition='Named plan gate only: initial-decision median ratio 0.7–1.4 and CI90 coverage; not a held-out score',
        caveats=['Counts use full simulated paths, unlike the legacy decision-truncated evaluator.',
                 'Applicant-facing truth is visibility-based; payer-work flags are a different proxy unless aligned.',
                 'Agency identity and activity granularity may differ between inferred and designed inventories.',
                 'Clock cohorts are cutoff-conditioned; finite observed-cohort values are not noise-free population parameters.',
                 'A missing clock is not replaced by elapsed_days or zero.',
                 'No fee, labor, or route-conditional score is manufactured when its matching quantity is absent.'])


def synthetic_release_gate(posterior,evaluation=None,*,posterior_sha256=None):
    """A necessary scoring/recovery gate for development, never a publication certificate."""
    failures=[]
    if (posterior.get('elapsed_time_unit','calendar_days') != 'calendar_days'
            or posterior.get('config',{}).get('elapsed_time_unit','calendar_days') != 'calendar_days'
            or any(p.get('elapsed_time_unit','calendar_days') != 'calendar_days'
                   for p in posterior.get('programs',{}).values())):
        failures.append('unmatched_truth_time_unit')
    if any(p.get('inventory_granularity','detailed_operations') != 'detailed_operations'
           for p in posterior.get('programs',{}).values()):
        failures.append('unmatched_aggregate_phase_estimand')
    if posterior.get('posterior_converged') is not True:
        failures.append('posterior_not_converged')
    if posterior.get('numerically_usable') is not True:
        failures.append('numerical_gate_not_passed')
    if evaluation is None:
        failures.append('missing_completed_truth_evaluation')
    elif (evaluation.get('schema_version')!='v6-burden-evaluation/1' or
          not evaluation.get('completed_utc') or
          evaluation.get('reserved_truth_read') is not False or
          evaluation.get('inference_modified') is not False):
        failures.append('invalid_or_unfinished_development_evaluation')
    elif evaluation.get('posterior_sha256')!=posterior_sha256 or not posterior_sha256:
        failures.append('evaluation_not_bound_to_this_posterior')
    elif set(evaluation.get('programs',{}))!=set(posterior['programs']):
        failures.append('evaluation_does_not_cover_all_programs')
    else:
        for pid,row in evaluation['programs'].items():
            clock=row.get('comparisons',{}).get('initial_decision_median_days',{})
            ratio=clock.get('posterior_median_over_truth')
            if not (row.get('development_phase1_clock_recovery_pass') is True and
                    clock.get('scored') is True and _finite_number(ratio) and .7<=ratio<=1.4 and
                    clock.get('ci90_covers_truth') is True):
                failures.append(pid+':development_clock_recovery_gate_failed')
    return dict(development_clock_gate_passed=not failures,failures=failures,
        synthetic_posterior_quotable_as_validated=False,
        reason='Development scoring is necessary, not sufficient: source semantics, matched populations and untouched evaluation remain required')


def check_development_partitions(world,program_ids):
    """Check every program before opening any truth. Reserved and unassigned stay closed."""
    path=world/'render_manifest.json'
    if not path.is_file():
        raise ValueError('V6 development evaluation requires a render partition manifest')
    manifest=json.loads(path.read_text())
    partitions=manifest.get('partitions',{})
    allowed=set(partitions.get('calibration',[]))|set(partitions.get('development',[]))
    reserved=set(partitions.get('reserved',[]))
    if not allowed or allowed & reserved:
        raise ValueError('Missing or conflicting development partition declarations')
    assignments={}
    for pid in program_ids:
        if not re.fullmatch(r'[A-Za-z0-9_:-]+',pid):
            raise ValueError('Unsafe program identity')
        county=pid.split('__')[0]
        if county in reserved or county not in allowed:
            raise ValueError('Reserved or unassigned program is not allowed in development evaluation: '+pid)
        assignments[pid]='calibration' if county in partitions.get('calibration',[]) else 'development'
    return path,assignments


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    run, world, out = map(pathlib.Path, (args.run, args.world, args.out))
    if not world.exists() and len(world.parts)==1:
        world=pathlib.Path(__file__).resolve().parents[2]/'benchmark/synth/worlds'/world
    if out.exists():
        raise ValueError('Choose a fresh evaluation directory')
    posterior = run / 'posterior.json'
    report = json.loads(posterior.read_text())  # Must exist before any gold read.
    manifest = json.loads((run / 'manifest.json').read_text())
    expected = manifest.get('posterior_sha256')
    actual = hashlib.sha256(posterior.read_bytes()).hexdigest()
    if not manifest.get('completed_utc') or manifest.get('status','completed')!='completed':
        raise ValueError('Only a completed saved fit can be evaluated')
    if not expected or expected != actual:
        raise ValueError('Posterior differs from its saved manifest')
    v6=report.get('model','').startswith('joint-visit-hierarchy/6')
    if not report.get('programs'):
        raise ValueError('No programs to evaluate')
    inputs=[posterior,run/'manifest.json']
    assignments={}
    if v6:
        # Fail before opening private truth, not after comparing incompatible clocks.
        mismatch=synthetic_release_gate(report)['failures']
        if 'unmatched_truth_time_unit' in mismatch or 'unmatched_aggregate_phase_estimand' in mismatch:
            raise ValueError('V6 truth evaluation requires matched calendar-day detailed-operation clocks')
        partition_path,assignments=check_development_partitions(world,report['programs'])
        inputs.append(partition_path)
    results = {}
    for pid, program in report['programs'].items():
        if not re.fullmatch(r'[A-Za-z0-9_:-]+',pid):
            raise ValueError('Unsafe program identity')
        truth_path=world/'truth/processes'/f'{pid}.json'
        records_path=world/'truth/log'/f'{pid}.jsonl'
        inputs.extend([truth_path,records_path])
        truth = json.loads(truth_path.read_text())
        records = [json.loads(line) for line in records_path.read_text().splitlines() if line.strip()]
        if v6:
            results[pid]=compare_burden_v6(program,truth,records)
        else:
            log_path=world/'truth/log'/f'{pid}.summary.json'
            inputs.append(log_path)
            logs=json.loads(log_path.read_text())
            results[pid] = compare_burden(program, truth, records, logs)
    if v6:
        evaluation=dict(schema_version='v6-burden-evaluation/1',
            completed_utc=datetime.now(timezone.utc).isoformat(),posterior_sha256=actual,
            world=world.name,partitions=assignments,reads_development_truth=True,
            reserved_truth_read=False,programs=results,
            posterior_converged=report.get('posterior_converged'),
            numerically_usable=report.get('numerically_usable'),
            inference_modified=False,counts_from_full_paths=True,
            conditional_clock_cohort='uncensored finally decided cases with an observed named event',
            limitations=['Development/calibration evaluation is not an untouched held-out benchmark.',
                         'Passing source-extraction, compiler and matched-population reviews remains a separate requirement.'])
        record=RunManifest(out,dict(posterior_sha256=actual,world=world.name),
            operation='v6.evaluate_development',inputs=inputs,
            config=dict(evaluation_role='calibration_and_development_only',partitions=assignments),
            seeds={},hidden_truth_read=True,source_root=pathlib.Path(__file__).parent,
            sources=['evaluate_burden.py'])
        write(out/'burden.json',results)
        write(out/'evaluation.json',evaluation)
        release=synthetic_release_gate(report,evaluation,posterior_sha256=actual)
        write(out/'release_gate.json',release)
        record.complete(evaluation_sha256=hashlib.sha256((out/'evaluation.json').read_bytes()).hexdigest(),
                        inference_modified=False,reserved_truth_read=False)
        print(json.dumps(dict(world=world.name,programs={pid:dict(
            clock=row['comparisons'].get('initial_decision_median_days'),
            phase1_gate=row['development_phase1_clock_recovery_pass']) for pid,row in results.items()},
            release_gate=release),indent=2))
        return 0
    write(out / 'burden.json', results)
    write(out / 'manifest.json', {'posterior_sha256': actual,
        'source_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'purpose': 'supplementary post-fit evaluation; no inference changes'})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
