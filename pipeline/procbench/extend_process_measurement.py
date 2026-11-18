"""Numerically extend a saved v5 fit without changing its statistical target."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
from datetime import datetime,timezone
import json
import multiprocessing
import pathlib
import time

import numpy as np

from .extend_hierarchy import check_fresh_seed
from .infra.manifest import digest, write
from .run_process_measurement import finer_config, make_model, saved_config


def worker(evidence,audits,outcomes,cfg,index,initial,out,preparations=None):
    model=make_model(evidence,audits,replace(cfg,chains=1,seed=cfg.seed+104729*index),outcomes,preparations)
    target=pathlib.Path(out)
    with (target/f'chain_{index}.progress.jsonl').open('w') as log:
        def progress(value):
            value['chain']=index+1
            log.write(json.dumps(value)+'\n')
            log.flush()
            if value['iteration']==1 or value['iteration']%1000==0:
                print(json.dumps(value),flush=True)
        z,ll,calls=model.sample(progress,initial=np.asarray(initial)[None,:])
    path=target/f'continuation_{index}.npz'
    np.savez_compressed(path,z=z,log_likelihood=ll)
    return str(path),calls[0]


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--extra-draws',type=int,default=4000)
    ap.add_argument('--seed',type=int,default=20261917)
    ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args(argv)
    root,out=pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving prior extension: choose a new output directory')
    original=json.loads((root/'manifest.json').read_text())
    if not original.get('completed_utc') or original.get('posterior_sha256')!=digest((root/'posterior.json').read_bytes()):
        raise ValueError('Cannot extend an incomplete or changed fit')
    config=original['config']
    check_fresh_seed(original,args.seed,config['chains'])
    cfg=saved_config(config)
    base=original
    while 'input_sha256' not in base:
        base=base['base_manifest']
    for path,expected in base['input_sha256'].items():
        if digest(pathlib.Path(path).read_bytes())!=expected:
            raise ValueError('An original inference input changed; cannot silently extend')
    evidence=json.loads((root/'evidence.json').read_text())
    audits=json.loads((root/'audits.json').read_text())
    outcomes=json.loads((root/'outcomes.json').read_text()) if (root/'outcomes.json').exists() else None
    preparations=json.loads((root/'preparations.json').read_text()) if (root/'preparations.json').exists() else None
    model=make_model(evidence,audits,cfg,outcomes,preparations)
    old=np.load(root/'draws.npz')
    z0,ll0=old['z'],old['log_likelihood']
    positions=np.linspace(0,z0.shape[1]-1,min(50,z0.shape[1])).astype(int)
    errors=[abs(model.log_likelihood(z0[c,i])-ll0[c,i]) for c in range(len(z0)) for i in positions]
    if not np.all(np.isfinite(errors)) or max(errors)>1e-7:
        raise ValueError('Statistical target changed: saved likelihood disagrees')
    continuation=replace(cfg,seed=args.seed,warmup=0,draws=args.extra_draws,accelerate=True,ridge_move=True)
    combined=replace(cfg,draws=z0.shape[1]+args.extra_draws,accelerate=True,ridge_move=True)
    source=pathlib.Path(__file__).parent
    names=['extend_process_measurement.py','run_process_measurement.py','bayes_process_measurement.py',
        'bayes_outcome_measurement.py','measurement_kernel.py','latent_gaussian.py','bayes_hierarchy.py',
        'evidence_contract.py','audit_measurement_semantics.py','audit_case_outcomes.py','timing_contract.py']
    if preparations is not None:
        names+=['bayes_preparation_measurement.py','audit_preparation_clocks.py']
    if hasattr(cfg,'case_preparation_logit_sd'):
        names+=['bayes_variable_preparation.py','phase_mixture.py']
    manifest=dict(config=asdict(combined),continuation_config=asdict(continuation),base_run=str(root),
        base_manifest=original,started_utc=datetime.now(timezone.utc).isoformat(),
        saved_likelihood_checks=len(errors),saved_likelihood_max_error=max(errors),
        source_sha256={name:digest((source/name).read_bytes()) for name in names},
        hidden_truth_read_during_inference=False)
    write(out/'manifest.json',manifest)
    write(out/'evidence.json',evidence)
    write(out/'audits.json',audits)
    if outcomes is not None:
        write(out/'outcomes.json',outcomes)
    if preparations is not None:
        write(out/'preparations.json',preparations)
    for name in names:
        target=out/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source/name).read_bytes())
    start=time.monotonic()
    with ProcessPoolExecutor(max_workers=min(args.workers,cfg.chains),mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs=[pool.submit(worker,evidence,audits,outcomes,continuation,i,z0[i,-1],str(out),preparations) for i in range(cfg.chains)]
        pieces=[job.result() for job in jobs]
    arrays=[np.load(path) for path,_ in pieces]
    z=np.concatenate((z0,np.concatenate([a['z'] for a in arrays])),axis=1)
    ll=np.concatenate((ll0,np.concatenate([a['log_likelihood'] for a in arrays])),axis=1)
    np.savez_compressed(out/'draws.npz',z=z,log_likelihood=ll)
    model.cfg=combined
    report=model.report(z,ll)
    finer=make_model(evidence,audits,finer_config(combined),outcomes,preparations)
    flat=z.reshape(-1,z.shape[-1])
    ids=np.linspace(0,len(flat)-1,min(200,len(flat))).astype(int)
    differences=[finer.log_likelihood(flat[i])-model.log_likelihood(flat[i]) for i in ids]
    report['quadrature_check']=dict(n=len(ids),base_nodes=cfg.quadrature,doubled_nodes=cfg.quadrature*2,
        max_absolute_log_likelihood_change=float(np.max(np.abs(differences))),
        acceptable=bool(np.max(np.abs(differences))<.01))
    if hasattr(cfg,'fraction_quadrature'):
        report['quadrature_check'].update(base_fraction_nodes=cfg.fraction_quadrature,
                                          doubled_fraction_nodes=cfg.fraction_quadrature*2)
    report['numerically_usable']=report['posterior_converged'] and report['quadrature_check']['acceptable']
    write(out/'posterior.json',report)
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-start,
        likelihood_calls=[n for _,n in pieces],posterior_sha256=digest((out/'posterior.json').read_bytes()))
    write(out/'manifest.json',manifest)
    print(json.dumps(dict(out=str(out),numerically_usable=report['numerically_usable'],
        flagged=report['diagnostics_flagged'],quadrature=report['quadrature_check'],
        timing={p:r['median_days'] for p,r in report['programs'].items()})),flush=True)


if __name__=='__main__':
    main()
