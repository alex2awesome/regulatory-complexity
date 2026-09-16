"""Extend completed v6 chains, checking identical target and fresh RNG streams."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
from datetime import datetime,timezone
import json
import multiprocessing
import pathlib

import numpy as np

from .bayes_trace_hierarchy import Config,VisitHierarchy
from .extend_hierarchy import check_fresh_seed
from .reconcile_evidence import digest,write
from .run_visit_hierarchy import precision_check,worker


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--extra-draws',type=int,default=4000)
    parser.add_argument('--seed',type=int,default=2026392001)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--population-size',type=int,
                        help='Increase prediction resolution only when population quadrature is absent from the likelihood')
    args=parser.parse_args(argv)
    root,out=pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists() or args.workers<1:
        raise ValueError('Choose a fresh output directory and positive worker count')
    original=json.loads((root/'manifest.json').read_text())
    if not original.get('completed_utc') or original.get('posterior_sha256')!=digest((root/'posterior.json').read_bytes()):
        raise ValueError('Only a completed, unchanged fit can be extended')
    cfg=Config(**original['config'])
    check_fresh_seed(original,args.seed,cfg.chains)
    base=original
    while 'input_sha256' not in base:
        base=base['base_manifest']
    for path,expected in base['input_sha256'].items():
        if digest(pathlib.Path(path).read_bytes())!=expected:
            raise ValueError('An inference input changed')
    data=json.loads((root/'data.json').read_text())
    prior_resolution=cfg.population_size
    if args.population_size is not None and args.population_size!=cfg.population_size:
        if args.population_size<cfg.population_size or cfg.selection_sd or any(
                o['case_id'] is None for p in data['programs'] for o in p.get('observations',[])):
            raise ValueError('Can only increase output resolution when no population integral occurs in the likelihood')
        cfg=replace(cfg,population_size=args.population_size)
    model=VisitHierarchy(data,cfg)
    raw=np.load(root/'draws.npz')
    z0,s0,ll0=raw['z'],raw['structures'],raw['log_likelihood']
    if z0.shape[:2]!=ll0.shape or s0.shape[:2]!=ll0.shape or z0.shape[-1]!=model.layout.size:
        raise ValueError('Saved state layout disagrees with model')
    positions=np.linspace(0,z0.shape[1]-1,min(50,z0.shape[1]),dtype=int)
    errors=[abs(model.log_likelihood(z0[c,i],s0[c,i])-ll0[c,i]) for c in range(len(z0)) for i in positions]
    if not np.isfinite(errors).all() or max(errors)>1e-7:
        raise ValueError('Statistical target changed; cannot extend these chains')
    continuation=replace(cfg,seed=args.seed,warmup=0,draws=args.extra_draws)
    combined=replace(cfg,draws=z0.shape[1]+args.extra_draws)
    source=pathlib.Path(__file__).parent
    names=['extend_visit_hierarchy.py','run_visit_hierarchy.py','bayes_trace_hierarchy.py',
           'compact_visit_trace.py','latent_gaussian.py','visit_clocks.py','bayes_hierarchy.py',
           'evidence_contract.py','schedule_kernel.py','extend_hierarchy.py','approximation_checks.py']
    manifest=dict(config=asdict(combined),continuation_config=asdict(continuation),base_run=str(root),
        base_manifest=original,started_utc=datetime.now(timezone.utc).isoformat(),
        saved_likelihood_checks=len(errors),saved_likelihood_max_difference=max(errors),
        saved_draws_sha256=digest((root/'draws.npz').read_bytes()),
        original_population_size=prior_resolution,
        prediction_resolution_only=cfg.population_size!=prior_resolution,
        hidden_truth_read_during_inference=False,
        source_sha256={name:digest((source/name).read_bytes()) for name in names})
    write(out/'manifest.json',manifest)
    write(out/'data.json',data)
    for name in names:
        target=out/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source/name).read_bytes())
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs=[pool.submit(worker,data,continuation,c,str(out),(z0[c,-1][None,:],s0[c,-1][None,:]))
              for c in range(cfg.chains)]
        completed=[job.result() for job in jobs]
    pieces=[np.load(path) for path,_ in completed]
    z=np.concatenate((z0,np.concatenate([p['z'] for p in pieces])),axis=1)
    s=np.concatenate((s0,np.concatenate([p['structures'] for p in pieces])),axis=1)
    ll=np.concatenate((ll0,np.concatenate([p['log_likelihood'] for p in pieces])),axis=1)
    np.savez_compressed(out/'draws.npz',z=z,structures=s,log_likelihood=ll)
    model.cfg=combined
    report=model.report(z,s,ll)
    report['precision']=precision_check(model,VisitHierarchy(data,replace(combined,population_size=cfg.population_size*4)),z,s)
    report['numerically_usable']=report['posterior_converged'] and report['precision']['likelihood_acceptable'] and report['precision']['predictions_acceptable']
    write(out/'posterior.json',report)
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),calls=[calls for _,calls in completed],
                    posterior_sha256=digest((out/'posterior.json').read_bytes()))
    write(out/'manifest.json',manifest)
    print(json.dumps(dict(numerically_usable=report['numerically_usable'],flagged=report['diagnostics_flagged'],
                         precision=report['precision'])),flush=True)


if __name__=='__main__':
    main()
