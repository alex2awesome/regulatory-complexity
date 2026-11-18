"""Score preserved v5 development timing fits against exact-input LLM controls.

This command is intentionally development-only. A new reserved evaluation needs
its own frozen model/baseline/input selection protocol before any outcome is read.
"""
import argparse
from datetime import datetime,timezone
import json
import pathlib

import numpy as np

from .compare_evidence_runs import check_matched_inputs,score_baseline
from .latent_gaussian import effective_size
from .infra.manifest import digest, write
from .run_hierarchical import posterior_timing_score
from .timing_contract import INITIAL_POPULATION_MEDIAN, LEGACY_SUMMARY_MEDIAN, verify_declared_initial_target


def load_verified(run,baseline_root):
    run=pathlib.Path(run)
    report=json.loads((run/'posterior.json').read_text())
    manifest=json.loads((run/'manifest.json').read_text())
    if not manifest.get('completed_utc') or manifest.get('posterior_sha256')!=digest((run/'posterior.json').read_bytes()):
        raise ValueError('Complete saved posterior and matching hash required before reading outcomes')
    pid=next(iter(report['programs']))
    baseline=pathlib.Path(baseline_root)
    if not (baseline/'manifest.json').exists():
        if len(report['programs'])!=1:
            raise ValueError('A joint fit requires the matching joint baseline directory')
        baseline=baseline/pid
    baseline_manifest=json.loads((baseline/'manifest.json').read_text())
    check_matched_inputs(manifest,baseline_manifest)
    verify_declared_initial_target(manifest)
    verify_declared_initial_target(baseline_manifest)
    repeats=json.loads((baseline/'estimates.json').read_text())
    if not repeats or any(sorted(p['program_id'] for p in r['programs'])!=sorted(report['programs']) for r in repeats):
        raise ValueError('Baseline program grouping differs or has no repeats')
    arrays=np.load(run/'draws.npz')
    shape=arrays['z'].shape[:2]
    if any(len(program['process_median_draws'])!=np.prod(shape) for program in report['programs'].values()):
        raise ValueError('Saved report/draw count mismatch')
    return run,report,manifest,repeats,shape


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs',nargs='+',required=True)
    ap.add_argument('--baseline-root',required=True,help='Per-program baseline root, or a matching joint baseline directory')
    ap.add_argument('--world',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--allow-legacy-clock-mismatch',action='store_true',
                    help='Explicitly acknowledge development-only comparison of different clocks/cohorts')
    args=ap.parse_args(argv)
    if not args.allow_legacy_clock_mismatch:
        raise ValueError('Legacy summaries use a different decision clock/cohort. '
                         'Use --allow-legacy-clock-mismatch only for development diagnostics, not validation.')
    out=pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving earlier comparison; choose a new output directory')
    prepared=[load_verified(path,args.baseline_root) for path in args.runs]
    started=datetime.now(timezone.utc).isoformat()
    rows=[]
    for run,report,manifest,repeats,shape,pid in [(*entry,pid) for entry in prepared for pid in entry[1]['programs']]:
        program=report['programs'][pid]
        logs=json.loads((pathlib.Path(args.world)/'truth/log'/f'{pid}.summary.json').read_text())
        truth=logs['elapsed_days']['median']
        samples=np.log(program['process_median_draws'])
        q40,q60=np.quantile(samples,[.4,.6])
        density=.2/max(q60-q40,1e-12)
        median_ess=effective_size((samples.reshape(shape)<=np.median(samples)).astype(float))
        controls=[next(v for v in r['programs'] if v['program_id']==pid) for r in repeats]
        baseline=[score_baseline(control,truth) for control in controls]
        rows.append(dict(run=str(run),program=pid,config=manifest['config'],
            truth_median_days=truth,truth_p90_days=logs['elapsed_days']['p90'],
            bayesian=program['median_days'],bayesian_p90=program['p90_days'],
            bayesian_scores=posterior_timing_score(program['process_median_draws'],truth),
            log_median_mcse=float(np.sqrt(.25/median_ess)/density),median_indicator_ess=median_ess,
            llm_repeats=baseline,llm_p90=[control['p90_days'] for control in controls],
            numerically_usable=report['numerically_usable'],diagnostics_flagged=report['diagnostics_flagged'],
            estimand_compatible=False,usable_for_accuracy_validation=False,
            quadrature_check=report['quadrature_check'],
            evidence=dict(cases=program['n_independent_cases'],population_claims=program['n_population_claims'],
                          excluded=program['excluded'])))
    write(out/'comparison.json',dict(rows=rows,scope='development timing comparison, not full-burden validation',
        estimator_target=dict(INITIAL_POPULATION_MEDIAN),comparand_target=dict(LEGACY_SUMMARY_MEDIAN),
        estimand_compatible=False,usable_for_accuracy_validation=False,
        caveats=['All W1 outcomes are development information; these are not new held-out successes.',
                 'Legacy truth uses last recorded decision, while these estimator prompts target initial decision; repeat-decision cases have a known estimand mismatch.',
                 'Unusable numerical fits are retained but cannot support accuracy claims.',
                 'LLM intervals are self-assessed; no LLM predictive distribution or CRPS is invented.',
                 'Activity counts, agency identity, per-task transfer and labor are not scored by this channel.']))
    write(out/'manifest.json',dict(evaluation_started_utc=started,
        evaluation_completed_utc=datetime.now(timezone.utc).isoformat(),development_only=True,
        legacy_clock_mismatch_explicitly_acknowledged=True,
        posterior_sha256={str(run):manifest['posterior_sha256'] for run,_,manifest,_,_ in prepared},
        equal_input_hashes_checked=True,source_sha256=digest(pathlib.Path(__file__).read_bytes())))
    for row in rows:
        print(json.dumps({k:row[k] for k in ['run','program','truth_median_days','bayesian',
                          'bayesian_scores','numerically_usable']}),flush=True)


if __name__=='__main__':
    main()
