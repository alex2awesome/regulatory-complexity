"""Immutable independent-chain runner for the experimental joint visit hierarchy."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import multiprocessing
import pathlib
import sys

import numpy as np
import scipy
from scipy.special import roots_hermitenorm

from .bayes_trace_hierarchy import Config,VisitHierarchy
from .reconcile_evidence import digest,write
from .approximation_checks import likelihood_weight_check


def worker(data,cfg,index,out,initial=None):
    model=VisitHierarchy(data,replace(cfg,chains=1,seed=cfg.seed+104729*index))
    out=pathlib.Path(out)
    with (out/f'chain_{index}.progress.jsonl').open('w') as stream:
        def progress(row):
            row['chain']=index+1
            stream.write(json.dumps(row)+'\n')
            stream.flush()
            if row['iteration']==1 or row['iteration']%500==0:
                print(json.dumps(row),flush=True)
        z,structures,ll,calls=model.sample(progress,initial=initial)
    path=out/f'chain_{index}.npz'
    np.savez_compressed(path,z=z,structures=structures,log_likelihood=ll)
    return str(path),calls[0]


def precision_check(model,finer,states,structures):
    flat=states.reshape(-1,states.shape[-1])
    routes=structures.reshape(-1,len(model.programs))
    chosen=np.linspace(0,len(flat)-1,min(256,len(flat)),dtype=int)
    prediction_chosen=set(np.linspace(0,len(flat)-1,min(32,len(flat)),dtype=int))
    chosen=np.unique(np.r_[chosen,list(prediction_chosen)])
    likelihood_changes=[]
    relative_changes=[]
    phase_changes=[]
    phase_nodes,phase_weights=roots_hermitenorm(64)
    phase_weights/=np.sqrt(2*np.pi)
    for i in chosen:
        z,ss=flat[i],routes[i]
        likelihood_changes.append(finer.log_likelihood(z,ss)-model.log_likelihood(z,ss))
        if i not in prediction_chosen:
            continue
        a,b=model.parameters(z),finer.parameters(z)
        if model.cfg.within_visit_phases:
            base_phases=model.phase_means(a)
            fine_phases=model.phase_means(a,phase_nodes,phase_weights)
            phase_changes.extend(float(np.max(np.abs(x-y)/np.maximum(y,np.finfo(float).tiny)))
                                 for x,y in zip(base_phases,fine_phases))
        for pi,(p,pf) in enumerate(zip(model.programs,finer.programs)):
            first=model.trace(p,z,a,int(ss[pi]),True)
            second=finer.trace(pf,z,b,int(ss[pi]),True)
            for event in ('initial_decision','final_decision','modeled_work_end'):
                try:
                    x,y=first.event(event),second.event(event)
                except ValueError:
                    continue
                for q in (.5,.9):
                    relative_changes.append(abs(float(np.quantile(x,q)/np.quantile(y,q))-1))
    weights=likelihood_weight_check(likelihood_changes)
    max_ll=weights['max_absolute_log_likelihood_change']
    max_prediction=max(relative_changes,default=0.)
    max_phase=max(phase_changes,default=0.)
    return dict(states_checked=len(chosen),base_population_size=model.cfg.population_size,
        refined_population_size=finer.cfg.population_size,max_absolute_log_likelihood_change=max_ll,
        max_relative_clock_quantile_change=max_prediction,
        max_relative_phase_mean_change=max_phase,
        posterior_weight_check=weights, checked_draw_fraction=len(chosen)/len(flat),
        prediction_states_checked=len(prediction_chosen),
        likelihood_acceptable=weights['acceptable'],predictions_acceptable=max_prediction<.02 and max_phase<1e-6,
        caveat='Finite checked posterior states, not a uniform error bound or full calibration')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--data')
    mode.add_argument('--diagnose-run', help='Information report on saved V6 draws; no sampling or score changes')
    parser.add_argument('--draws-file', help='Saved draws when a prediction-only run references another directory')
    parser.add_argument('--out',required=True)
    parser.add_argument('--within-visit-phases',action='store_true',
                        help='Explicitly enable a weak logistic-normal service-fraction hierarchy')
    for name,default in [('chains',4),('warmup',1000),('draws',2000),('workers',2),
                         ('population-size',256),('seed',2026092001)]:
        parser.add_argument('--'+name,type=int,default=default)
    args=parser.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists() or args.workers<1:
        raise ValueError('Choose a fresh directory and positive worker count')
    if args.diagnose_run:
        run=pathlib.Path(args.diagnose_run)
        posterior=json.loads((run/'posterior.json').read_text())
        data=json.loads((run/'data.json').read_text())
        model=VisitHierarchy(data,Config(**posterior['config']))
        draws_path=pathlib.Path(args.draws_file) if args.draws_file else run/'draws.npz'
        with np.load(draws_path) as saved:
            states,structures,ll=saved['z'],saved['structures'],saved['log_likelihood']
        if states.shape[-1]!=model.layout.size:
            raise ValueError('Saved parameterization differs from the current layout')
        flat=states.reshape(-1,states.shape[-1])
        routes=structures.reshape(-1,len(model.programs))
        chosen=np.linspace(0,len(flat)-1,min(8,len(flat)),dtype=int)
        difference=max(abs(model.log_likelihood(flat[i],routes[i])-ll.ravel()[i]) for i in chosen)
        if not np.isfinite(difference) or difference>1e-8:
            raise ValueError('Saved target does not match; use its frozen source for information diagnostics')
        report=model.information_report(states, sampling_converged=posterior['posterior_converged'])
        write(out/'identification.json',report)
        write(out/'manifest.json',dict(mode='saved_draw_information_only', original_run=str(run),
            input_sha256={str(p):digest(p.read_bytes()) for p in (run/'data.json',run/'posterior.json',draws_path)},
            source_sha256={name:digest(pathlib.Path(__file__).with_name(name).read_bytes()) for name in
                          ('latent_gaussian.py','bayes_trace_hierarchy.py','run_visit_hierarchy.py')},
            saved_likelihood_states_checked=len(chosen),max_likelihood_difference=difference,
            no_sampling=True,no_scores_changed=True,hidden_truth_read=False))
        print(json.dumps(dict(coordinates=report['coordinates'],
            below_10_percent=report['coordinates_below_10_percent'],
            blocks={name:row['mean_variance_contraction'] for name,row in report['blocks'].items()})),flush=True)
        return
    if args.draws_file:
        raise ValueError('--draws-file is only for --diagnose-run')
    path=pathlib.Path(args.data)
    data=json.loads(path.read_text())
    cfg=Config(**{key:getattr(args,key) for key in ('chains','warmup','draws','population_size','seed',
                                                 'within_visit_phases')})
    model=VisitHierarchy(data,cfg)
    source=pathlib.Path(__file__).parent
    names=['bayes_trace_hierarchy.py','compact_visit_trace.py','run_visit_hierarchy.py',
           'bayes_hierarchy.py','latent_gaussian.py','visit_clocks.py','evidence_contract.py','schedule_kernel.py',
           'approximation_checks.py']
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),config=asdict(cfg),
        input_sha256={str(path):digest(path.read_bytes())},
        source_sha256={name:digest((source/name).read_bytes()) for name in names},
        hidden_truth_read_during_inference=False,dimensions=model.layout.size,
        scope='Joint visit/agency/task development; no text-pipeline or LLM-superiority claim',
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__))
    write(out/'manifest.json',manifest)
    write(out/'data.json',data)
    for name in names:
        target=out/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((source/name).read_bytes())
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=[pool.submit(worker,data,cfg,index,str(out)) for index in range(cfg.chains)]
        completed=[future.result() for future in futures]
    arrays=[np.load(path) for path,_ in completed]
    z=np.concatenate([a['z'] for a in arrays])
    structures=np.concatenate([a['structures'] for a in arrays])
    ll=np.concatenate([a['log_likelihood'] for a in arrays])
    np.savez_compressed(out/'draws.npz',z=z,structures=structures,log_likelihood=ll)
    report=model.report(z,structures,ll)
    finer=VisitHierarchy(data,replace(cfg,population_size=cfg.population_size*4))
    report['precision']=precision_check(model,finer,z,structures)
    report['numerically_usable']=(report['posterior_converged'] and report['precision']['likelihood_acceptable']
                                   and report['precision']['predictions_acceptable'])
    write(out/'posterior.json',report)
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),calls=[c for _,c in completed],
                    posterior_sha256=digest((out/'posterior.json').read_bytes()))
    write(out/'manifest.json',manifest)
    print(json.dumps(dict(numerically_usable=report['numerically_usable'],precision=report['precision'],
                         flagged=len(report['diagnostics_flagged']),programs=report['programs'])),flush=True)


if __name__=='__main__':
    main()
