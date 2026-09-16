"""Reproducible independent-chain runner for the v5 whole-process timing channel."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import multiprocessing
import pathlib
import sys
import time

import numpy as np
import scipy

from .bayes_process_measurement import Config, ProcessMeasurementModel
from .reconcile_evidence import digest, write
from .measurement_kernel import ACCELERATOR
from .timing_contract import INITIAL_POPULATION_MEDIAN


def make_model(evidence,audits,cfg,outcomes=None,preparations=None):
    if preparations is not None:
        if outcomes is None:
            raise ValueError('Preparation extension requires the explicit outcome audit')
        if hasattr(cfg,'case_preparation_logit_sd'):
            from .bayes_variable_preparation import VariablePreparationModel
            return VariablePreparationModel(evidence,audits,outcomes,preparations,cfg)
        from .bayes_preparation_measurement import PreparationMeasurementModel
        return PreparationMeasurementModel(evidence,audits,outcomes,preparations,cfg)
    if outcomes is not None:
        from .bayes_outcome_measurement import OutcomeMeasurementModel
        return OutcomeMeasurementModel(evidence,audits,outcomes,cfg)
    return ProcessMeasurementModel(evidence,audits,cfg)


def saved_config(values):
    if 'case_preparation_logit_sd' in values:
        from .bayes_variable_preparation import Config as SavedConfig
    elif 'preparation_span_alpha' in values:
        from .bayes_preparation_measurement import Config as SavedConfig
    elif 'outcome_contrast_sd' in values:
        from .bayes_outcome_measurement import Config as SavedConfig
    else:
        SavedConfig=Config
    return SavedConfig(**values)


def finer_config(cfg):
    changes=dict(quadrature=cfg.quadrature*2)
    if hasattr(cfg,'fraction_quadrature'):
        changes['fraction_quadrature']=cfg.fraction_quadrature*2
    return replace(cfg,**changes)


def worker(evidence, audits, cfg, index, out, outcomes=None,preparations=None):
    model = make_model(evidence, audits, replace(cfg, chains=1, seed=cfg.seed+104729*index),outcomes,preparations)
    out = pathlib.Path(out)
    with (out/f'chain_{index}.progress.jsonl').open('w') as log:
        def progress(value):
            value['chain'] = index+1
            log.write(json.dumps(value)+'\n')
            log.flush()
            if value['iteration'] == 1 or value['iteration'] % 1000 == 0:
                print(json.dumps(value), flush=True)
        z, ll, calls = model.sample(progress)
    target = out/f'chain_{index}.npz'
    np.savez_compressed(target, z=z, log_likelihood=ll)
    return str(target), calls[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--evidence', nargs='+', required=True)
    ap.add_argument('--audits', nargs='+', required=True)
    ap.add_argument('--outcome-audits',nargs='+',help='Optional typed outcomes and administrative denominators; enables the outcome mixture')
    ap.add_argument('--preparation-audits',nargs='+',help='Optional partial pre-filing clocks; requires outcome audits')
    ap.add_argument('--variable-preparation',action='store_true',help='Allow case-varying preparation fractions with population clock convolution')
    ap.add_argument('--preparation-budget-mode',choices=['dirichlet','coverage_partition'],default='coverage_partition')
    ap.add_argument('--out', required=True)
    ap.add_argument('--include-ambiguous', action='store_true', help='Integrate uncertain completion/progress for individual whole-case reports')
    ap.add_argument('--no-accelerator',dest='accelerate',action='store_false',help='Use the independently checked SciPy likelihood')
    ap.add_argument('--no-ridge-move',dest='ridge_move',action='store_false',help='Disable the exact likelihood-invariant source/location Gibbs transition')
    for name, default in [('chains',4), ('warmup',1000), ('draws',2000), ('thin',1),
                          ('seed',20260917), ('quadrature',128), ('fraction-quadrature',64), ('workers',4)]:
        ap.add_argument('--'+name, type=int, default=default)
    for name, default in [('selection-sd',0.), ('source-sd',.35), ('prior-median',30.),
                          ('prep-fraction',.10), ('clock-logit-sd',1.2),
                          ('outcome-contrast-sd',.7), ('outcome-posting-sd',1.5), ('admin-logit-sd',.35),
                          ('preparation-report-sd',.35),('preparation-span-alpha',1.),
                          ('preparation-remainder-alpha',1.), ('case-preparation-logit-sd',1.),
                          ('preparation-coverage-alpha',1.),('preparation-coverage-beta',1.)]:
        ap.add_argument('--'+name, type=float, default=default)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving existing run; choose a fresh directory')
    config_class=Config
    if args.outcome_audits:
        from .bayes_outcome_measurement import Config as OutcomeConfig
        config_class=OutcomeConfig
    if args.preparation_audits:
        if not args.outcome_audits:
            raise ValueError('Preparation extension requires outcome audits')
        from .bayes_preparation_measurement import Config as PreparationConfig
        config_class=PreparationConfig
    if args.variable_preparation:
        if not args.preparation_audits:
            raise ValueError('Variable preparation requires preparation and outcome audits')
        from .bayes_variable_preparation import Config as VariableConfig
        config_class=VariableConfig
    cfg = config_class(**{k: getattr(args,k) for k in asdict(config_class()) if hasattr(args,k)})
    paths = [pathlib.Path(p) for p in args.evidence+args.audits+(args.outcome_audits or [])+(args.preparation_audits or [])]
    evidence = [json.loads(pathlib.Path(p).read_text()) for p in args.evidence]
    audits = [json.loads(pathlib.Path(p).read_text()) for p in args.audits]
    outcomes=[json.loads(pathlib.Path(p).read_text()) for p in args.outcome_audits] if args.outcome_audits else None
    preparations=[json.loads(pathlib.Path(p).read_text()) for p in args.preparation_audits] if args.preparation_audits else None
    model = make_model(evidence, audits, cfg,outcomes,preparations)
    code = pathlib.Path(__file__).parent
    sources = ['bayes_process_measurement.py', 'run_process_measurement.py', 'latent_gaussian.py',
               'bayes_hierarchy.py', 'evidence_contract.py', 'audit_measurement_semantics.py','measurement_kernel.py',
               'timing_contract.py']
    if outcomes is not None:
        sources+=['bayes_outcome_measurement.py','audit_case_outcomes.py']
    if preparations is not None:
        sources+=['bayes_preparation_measurement.py','audit_preparation_clocks.py']
    if args.variable_preparation:
        sources+=['bayes_variable_preparation.py','phase_mixture.py']
    manifest = dict(config=asdict(cfg), started_utc=datetime.now(timezone.utc).isoformat(),
        timing_target=dict(INITIAL_POPULATION_MEDIAN),
        input_sha256={str(p): digest(p.read_bytes()) for p in paths},
        source_sha256={name: digest((code/name).read_bytes()) for name in sources},
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,measurement_backend=ACCELERATOR),
        hidden_truth_read_during_inference=False, dimensions=model.layout.size)
    write(out/'manifest.json',manifest)
    write(out/'evidence.json',evidence)
    write(out/'audits.json',audits)
    if outcomes is not None:
        write(out/'outcomes.json',outcomes)
    if preparations is not None:
        write(out/'preparations.json',preparations)
    for name in sources:
        target = out/'source'/name
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_bytes((code/name).read_bytes())
    start = time.monotonic()
    with ProcessPoolExecutor(max_workers=min(args.workers,cfg.chains),
                             mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs = [pool.submit(worker,evidence,audits,cfg,i,str(out),outcomes,preparations) for i in range(cfg.chains)]
        pieces = [job.result() for job in jobs]
    loaded = [np.load(path) for path,_ in pieces]
    z = np.concatenate([p['z'] for p in loaded])
    ll = np.concatenate([p['log_likelihood'] for p in loaded])
    np.savez_compressed(out/'draws.npz',z=z,log_likelihood=ll)
    report = model.report(z,ll)
    # Audit quadrature approximation at evenly spaced saved states before any score.
    finer = make_model(evidence,audits,finer_config(cfg),outcomes,preparations)
    flat = z.reshape(-1,z.shape[-1])
    ids = np.linspace(0,len(flat)-1,min(200,len(flat))).astype(int)
    differences = [finer.log_likelihood(flat[i])-model.log_likelihood(flat[i]) for i in ids]
    report['quadrature_check'] = dict(n=len(ids), base_nodes=cfg.quadrature,
        doubled_nodes=cfg.quadrature*2, max_absolute_log_likelihood_change=float(np.max(np.abs(differences))),
        acceptable=bool(np.max(np.abs(differences)) < .01))
    if hasattr(cfg,'fraction_quadrature'):
        report['quadrature_check'].update(base_fraction_nodes=cfg.fraction_quadrature,
                                          doubled_fraction_nodes=cfg.fraction_quadrature*2)
    report['numerically_usable'] = report['posterior_converged'] and report['quadrature_check']['acceptable']
    write(out/'posterior.json',report)
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-start,
        likelihood_calls=[n for _,n in pieces],posterior_sha256=digest((out/'posterior.json').read_bytes()))
    write(out/'manifest.json',manifest)
    print(json.dumps(dict(out=str(out),numerically_usable=report['numerically_usable'],
        quadrature=report['quadrature_check'],flagged=len(report['diagnostics_flagged']),
        timing={p:r['median_days'] for p,r in report['programs'].items()})),flush=True)


if __name__ == '__main__':
    main()
