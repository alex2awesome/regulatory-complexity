"""Independent grid-recovery check of normalized delay ascertainment.

This deliberately favorable component test knows the case log-SD and observation
clock and has no reporting noise. It is NOT calibration of the full text model.
Sample sizes count independent cases, not documents repeating the same cases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import pathlib

import numpy as np
from scipy.special import logsumexp, ndtr, ndtri

from .bayes_process_measurement import log_selection_weight
from .reconcile_evidence import digest, write


def selected_cases(rng,n,mu,sigma,strength,width=.35):
    accepted=[]
    threshold=ndtri(.75)*math.sqrt(1+width*width)
    while len(accepted)<n:
        z=rng.normal(size=max(64,2*(n-len(accepted))))
        flag=ndtr((z-threshold)/width)
        probability=math.exp(-strength)+(1-math.exp(-strength))*flag
        accepted.extend(z[rng.random(len(z))<probability].tolist())
    return mu+sigma*np.array(accepted[:n])


def grid_posterior(log_days,sigma,selected,mu_grid,kappa_grid,prior_mu,prior_sd=2.,selection_sd=1.5):
    """Exact point-observation likelihood evaluated on a reproducible 2D grid."""
    z=(np.asarray(log_days)[:,None]-mu_grid[None,:])/sigma
    likelihood=(-.5*z*z).sum(axis=0)[:,None]
    if selected:
        likelihood=np.broadcast_to(likelihood,(len(mu_grid),len(kappa_grid))).copy()
        threshold=ndtri(.75)*math.sqrt(1+.35**2)
        for start in range(0,len(z),25):
            flag=ndtr((z[start:start+25]-threshold)/.35)
            with np.errstate(divide='ignore'):
                block=np.logaddexp(np.log1p(-flag)[:,:,None],
                                   np.log(flag)[:,:,None]+kappa_grid[None,None,:])
            likelihood+=block.sum(axis=0)
        likelihood-=len(z)*np.logaddexp(math.log(.75),math.log(.25)+kappa_grid)[None,:]
        likelihood-=.5*(kappa_grid/selection_sd)[None,:]**2
        # Trapezoidal half-weights on a nonnegative half-normal prior boundary.
        likelihood[:,[0,-1]]+=math.log(.5)
    likelihood-=.5*((mu_grid-prior_mu)/prior_sd)[:,None]**2
    likelihood[[0,-1],:]+=math.log(.5)
    weights=np.exp(likelihood-logsumexp(likelihood))
    return weights.sum(axis=1),weights.sum(axis=0)


def weighted_quantile(grid,weights,probabilities):
    return np.interp(probabilities,np.cumsum(weights)-.5*weights,grid)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--replicates',type=int,default=32)
    ap.add_argument('--sizes',nargs='+',type=int,default=[10,100,1000])
    ap.add_argument('--seed',type=int,default=202609180)
    args=ap.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve prior validation; use a fresh directory')
    mu,sigma,strength=math.log(30.),.6,1.5
    # Grid spacing is fixed before generation; endpoint mass is audited below.
    mus=np.linspace(mu-2.5,mu+2.5,501)
    kappas=np.linspace(0,7.5,151)
    write(out/'manifest.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),
        seed=args.seed,replicates=args.replicates,sizes=args.sizes,
        truth=dict(median_days=math.exp(mu),log_sd=sigma,log_relative_posting_rate=strength),
        source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        scope='known-spread, exact-clock selection component, not full-model SBC or held-out text performance'))
    rows=[]
    with (out/'replicates.jsonl').open('w') as log:
        for n in args.sizes:
            for rep in range(args.replicates):
                rng=np.random.default_rng(np.random.SeedSequence([args.seed,n,rep]))
                observations=selected_cases(rng,n,mu,sigma,strength)
                estimates={}
                for selected in [False,True]:
                    weights,kweights=grid_posterior(observations,sigma,selected,mus,kappas,mu)
                    lo,point,hi=weighted_quantile(mus,weights,[.05,.5,.95])
                    estimates['selection' if selected else 'no_selection']=dict(
                        median_days=float(np.exp(point)),ci90=np.exp([lo,hi]).tolist(),
                        absolute_log_error=float(abs(point-mu)),covers=bool(lo<=mu<=hi),
                        interval_score90=float(hi-lo+20*max(lo-mu,0)+20*max(mu-hi,0)),
                        mu_edge_mass=float(weights[:2].sum()+weights[-2:].sum()),
                        kappa_upper_edge_mass=float(kweights[-2:].sum()) if selected else None,
                        kappa=weighted_quantile(kappas,kweights,[.05,.5,.95]).tolist() if selected else None)
                row=dict(n=n,replicate=rep,log_days=observations.tolist(),estimates=estimates)
                rows.append(row)
                log.write(json.dumps(row)+'\n')
                log.flush()
                if rep%8==0:
                    print(json.dumps(dict(n=n,replicate=rep)),flush=True)
    result={}
    for n in args.sizes:
        result[n]={}
        for method in ['no_selection','selection']:
            values=[r['estimates'][method] for r in rows if r['n']==n]
            result[n][method]=dict(replicates=len(values),coverage90=sum(v['covers'] for v in values),
                mean_absolute_log_error=float(np.mean([v['absolute_log_error'] for v in values])),
                mean_interval_score90=float(np.mean([v['interval_score90'] for v in values])),
                maximum_mu_grid_edge_mass=max(v['mu_edge_mass'] for v in values),
                mean_median_days=float(np.mean([v['median_days'] for v in values])))
    write(out/'summary.json',result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
