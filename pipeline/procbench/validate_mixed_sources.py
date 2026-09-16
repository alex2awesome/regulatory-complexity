"""Unknown-spread recovery: more selected cases versus an unselected source.

Exact case clocks, fixed truth and correctly specified ascertainment make this a
favorable component experiment, not full-pipeline SBC or an LLM comparison.
Conditions share nested selected samples and the same independent admin sample.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import json
import math
import multiprocessing
import pathlib

import numpy as np

from .bayes_process_measurement import log_selection_weight
from .latent_gaussian import diagnostics,elliptical_slice,summary
from .reconcile_evidence import digest,write
from .validate_process_selection import selected_cases


CONDITIONS=[(10,0),(100,0),(1000,0),(100,20)]


class ExactSourceModel:
    def __init__(self,selected,administrative):
        self.selected=np.asarray(selected,dtype=float)
        self.administrative=np.asarray(administrative,dtype=float)
        if not all(np.all(np.isfinite(x)) for x in (self.selected,self.administrative)):
            raise ValueError('Case log durations must be finite')

    @staticmethod
    def parameters(z):
        return math.log(30.)+2*z[0],math.exp(math.log(.6)+.7*z[1]),1.5*abs(z[2])

    def log_likelihood(self,z):
        try:
            mu,sigma,strength=self.parameters(z)
            selected=(self.selected-mu)/sigma
            admin=(self.administrative-mu)/sigma
            return float(-.5*(selected@selected+admin@admin)
                -(len(selected)+len(admin))*math.log(sigma)
                +log_selection_weight(selected,strength).sum())
        except (OverflowError,FloatingPointError,ZeroDivisionError):
            return -float('inf')


def fit(rep,n_selected,n_admin,selected,admin,seed,warmup,draws,out):
    model=ExactSourceModel(selected[:n_selected],admin[:n_admin])
    z=np.empty((4,draws,3))
    ll=np.empty((4,draws))
    for chain in range(4):
        rng=np.random.default_rng(np.random.SeedSequence([seed,rep,n_selected,n_admin,chain,1]))
        state=rng.normal(size=3)
        value=model.log_likelihood(state)
        for iteration in range(warmup+draws):
            for block in [[0,1],[2]]:
                state,value,_=elliptical_slice(state,block,model.log_likelihood,value,rng)
            if iteration>=warmup:
                z[chain,iteration-warmup]=state
                ll[chain,iteration-warmup]=value
    mu=math.log(30.)+2*z[:,:,0]
    strength=1.5*np.abs(z[:,:,2])
    diags={f'coordinate:{i}':diagnostics(z[:,:,i]) for i in range(3)}
    diags.update(log_likelihood=diagnostics(ll),log_median=diagnostics(mu),strength=diagnostics(strength))
    flagged={k:v for k,v in diags.items() if v['rhat'] is None or v['rhat']>1.01 or v['ess_bulk']<400 or v['ess_tail']<200}
    lo,point,hi=np.quantile(mu,[.05,.5,.95])
    name=f'selected_{n_selected}_admin_{n_admin}_rep_{rep:03d}'
    target=pathlib.Path(out)/name
    target.mkdir()
    np.savez_compressed(target/'draws.npz',z=z,log_likelihood=ll)
    result=dict(replicate=rep,n_selected=n_selected,n_admin=n_admin,median_days=float(np.exp(point)),
        ci90_days=np.exp([lo,hi]).tolist(),absolute_log_error=float(abs(point-math.log(30))),
        covers=bool(lo<=math.log(30)<=hi),interval_score90=float(hi-lo+20*max(lo-math.log(30),0)+20*max(math.log(30)-hi,0)),
        log_case_sd=summary(.6*np.exp(.7*z[:,:,1])),log_relative_posting_rate=summary(strength),
        diagnostics=diags,diagnostics_flagged=flagged,numerically_usable=not flagged)
    write(target/'result.json',result)
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--replicates',type=int,default=16)
    ap.add_argument('--seed',type=int,default=202609190)
    ap.add_argument('--warmup',type=int,default=1000)
    ap.add_argument('--draws',type=int,default=4000)
    ap.add_argument('--workers',type=int,default=2)
    args=ap.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists() or args.replicates<1 or args.draws<8 or args.warmup<0 or args.workers<1:
        raise ValueError('Fresh destination and valid sampling/replication settings required')
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),config=vars(args),conditions=CONDITIONS,
        truth=dict(median_days=30,log_case_sd=.6,log_relative_posting_rate=1.5),
        priors=dict(log_median='Normal(log(30), 2^2)',log_sigma='Normal(log(.6), .7^2)',strength='HalfNormal(1.5)'),
        scope='fixed-parameter exact-observation unknown-spread recovery, not full-pipeline calibration or held-out text performance',
        source_sha256=digest(pathlib.Path(__file__).read_bytes()))
    write(out/'manifest.json',manifest)
    datasets=[]
    for rep in range(args.replicates):
        rng=np.random.default_rng(np.random.SeedSequence([args.seed,rep,0]))
        selected=selected_cases(rng,1000,math.log(30),.6,1.5)
        admin=math.log(30)+.6*rng.normal(size=20)
        datasets.append(dict(replicate=rep,selected_log_days=selected.tolist(),administrative_log_days=admin.tolist()))
    write(out/'datasets.json',datasets)
    rows=[]
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs=[pool.submit(fit,d['replicate'],n,a,d['selected_log_days'],d['administrative_log_days'],
                         args.seed,args.warmup,args.draws,str(out)) for d in datasets for n,a in CONDITIONS]
        with (out/'results.jsonl').open('w') as log:
            for job in as_completed(jobs):
                row=job.result()
                rows.append(row)
                log.write(json.dumps(row)+'\n')
                log.flush()
                print(json.dumps({k:row[k] for k in ['replicate','n_selected','n_admin','median_days','numerically_usable']}),flush=True)
    result=[]
    for n,a in CONDITIONS:
        group=[r for r in rows if r['n_selected']==n and r['n_admin']==a]
        result.append(dict(n_selected=n,n_admin=a,replicates=len(group),
            all_numerically_usable=all(r['numerically_usable'] for r in group),
            flagged_replicates=[r['replicate'] for r in group if not r['numerically_usable']],
            mean_median_days=float(np.mean([r['median_days'] for r in group])),coverage90=sum(r['covers'] for r in group),
            mean_absolute_log_error=float(np.mean([r['absolute_log_error'] for r in group])),
            mean_interval_score90=float(np.mean([r['interval_score90'] for r in group]))))
    write(out/'summary.json',dict(conditions=result,
        warning='Failed numerical fits remain in aggregates and are flagged; do not selectively drop them or claim validation.'))
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),
                    results_sha256=digest((out/'results.jsonl').read_bytes()))
    write(out/'manifest.json',manifest)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
