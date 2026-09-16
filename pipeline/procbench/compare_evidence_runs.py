"""Compare saved Bayesian fits with exact-evidence direct-LLM controls.

Gold is accessed only after checking persisted fits, evidence hashes, and control
separation. This evaluation command never changes priors, ledgers, or inference.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import pathlib

import numpy as np

from .evaluate_burden import compare_burden
from .evidence_support import burden_support
from .run_hierarchical import evaluate, write


def input_hashes(manifest):
    """Follow unchanged-target extensions back to their original input ledger.

    Every extension keeps the complete preceding manifest. Missing provenance is
    an error, not permission to label two models as having equal information.
    """
    current = manifest
    while 'input_sha256' not in current:
        current = current.get('base_manifest')
        if not isinstance(current, dict):
            raise ValueError('Missing input hashes: cannot verify an equal-information comparison')
    hashes = current['input_sha256']
    if not isinstance(hashes, dict) or not hashes or not all(isinstance(v, str) for v in hashes.values()):
        raise ValueError('Invalid input hashes: cannot verify an equal-information comparison')
    return Counter(hashes.values())


def check_matched_inputs(fit, baseline):
    if input_hashes(fit) != input_hashes(baseline):
        raise ValueError('Evidence contents/grouping differ: not an equal-information comparison')
    if baseline.get('hidden_truth_provided') is not False or baseline.get('bayesian_predictions_provided') is not False:
        raise ValueError('Baseline provenance does not establish separation from gold/Bayesian answers')


def score_baseline(program, actual):
    """An interval score needs quantiles, not an invented LLM full distribution."""
    point = program['median_days']
    lo,hi = program['median_lower90_days'],program['median_upper90_days']
    for value in (actual,point,lo,hi):
        if value is not None and (not np.isfinite(value) or value<=0):
            raise ValueError('Log timing scores require finite positive durations')
    if lo is not None and hi is not None and lo>hi:
        raise ValueError('Reversed baseline interval')
    interval_score = None
    if lo is not None and hi is not None:
        lower,upper,target = np.log([lo,hi,actual])
        interval_score = float(upper-lower+20*max(lower-target,0.)+20*max(target-upper,0.))
    return {'median_days':point,
        'absolute_log_error':None if point is None else float(abs(np.log(point/actual))),
        'self_assessed_median_interval':[lo,hi],
        'interval_covers_truth':None if lo is None or hi is None else bool(lo<=actual<=hi),
        'interval_score90_log_median':interval_score}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--world', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    run, baseline, world, out = map(pathlib.Path, (args.run,args.baseline,args.world,args.out))
    if out.exists():
        raise ValueError('Preserving previous evaluation; choose a new directory')
    posterior = run/'posterior.json'
    report = json.loads(posterior.read_text())
    manifest = json.loads((run/'manifest.json').read_text())
    base_manifest = json.loads((baseline/'manifest.json').read_text())
    expected = manifest.get('posterior_sha256')
    digest = hashlib.sha256(posterior.read_bytes()).hexdigest()
    if expected != digest or not manifest.get('completed_utc'):
        raise ValueError('Fit must be saved and complete, with a valid posterior hash, before evaluation')
    check_matched_inputs(manifest,base_manifest)
    repeats = json.loads((baseline/'estimates.json').read_text())
    support = burden_support(json.loads((run/'evidence.json').read_text()))
    programs = set(report['programs'])
    if any({p['program_id'] for p in r['programs']} != programs for r in repeats):
        raise ValueError('Control and Bayesian program groupings differ')
    # All input/provenance checks are completed before the first truth read.
    evaluation_started_utc = datetime.now(timezone.utc).isoformat()
    scored = evaluate(report,world)
    rows = {}
    for pid, program in report['programs'].items():
        actual = scored[pid]['posterior_timing']['truth_median_days']
        controls = [next(p for p in r['programs'] if p['program_id']==pid) for r in repeats]
        points = [p['median_days'] for p in controls if p['median_days'] is not None]
        baseline_rows = [score_baseline(p,actual) for p in controls]
        truth = json.loads((world/'truth/processes'/f'{pid}.json').read_text())
        records = [json.loads(line) for line in (world/'truth/log'/f'{pid}.jsonl').read_text().splitlines() if line.strip()]
        logs = json.loads((world/'truth/log'/f'{pid}.summary.json').read_text())
        rows[pid] = {'truth_median_days': actual, 'bayesian': program['model']['process_timing'],
            'bayesian_scores': scored[pid]['posterior_timing'],
            'bayesian_process_diagnostics': report['diagnostics'][f'process:{pid}'],
            'elapsed_posterior_converged': report['posterior_converged'],
            'convergence_scope': 'Elapsed hierarchy only; work-hour fits have separate diagnostics',
            'llm_repeats': baseline_rows,
            'llm_point_range': [min(points),max(points)] if points else None,
            'llm_point_sample_sd': float(np.std(points,ddof=1)) if len(points)>1 else None,
            'direct_evidence_support': support[pid],
            'work_hour_posteriors': {channel:report.get('effort',{}).get(channel,{}).get('programs',{}).get(pid)
                                     for channel in ('payer_work','agency_work')},
            'burden': compare_burden(program,truth,records,logs)}
    write(out/'comparison.json',{'programs':rows,
        'caveats':['Three LLM repeats do not establish general determinism or interval calibration',
            'Shared extraction removes one source of variability; semantic uncertainty remains conditional',
            'No LLM predictive distribution is assumed, so it has no distributional CRPS score',
            'A small benchmark comparison is not evidence of general superiority']})
    write(out/'evaluation.json',scored)
    write(out/'manifest.json',{'fit':str(run),'baseline':str(baseline),'world':str(world),
        'evaluation_started_utc':evaluation_started_utc,
        'evaluation_completed_utc':datetime.now(timezone.utc).isoformat(),
        'posterior_sha256':digest,'equal_evidence_hashes_checked':True,
        'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'no_model_changes_performed':True})
    for pid,r in rows.items():
        print(json.dumps({'program':pid,'truth':r['truth_median_days'],
            'bayesian':r['bayesian']['median_days'],'llm':[p['median_days'] for p in r['llm_repeats']],
            'elapsed_converged':r['elapsed_posterior_converged']}),flush=True)


if __name__ == '__main__':
    main()
