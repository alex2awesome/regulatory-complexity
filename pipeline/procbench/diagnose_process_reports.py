"""Posterior robust-component attribution, without benchmark outcomes.

A high value means the fitted model assigns a report to its broad error
component. It is not proof the source is wrong: misspecified clocks, selection,
or process structure can produce the same signal. Same-case reports share the
joint conditional distribution over durations and outcome components.
"""
import argparse
from dataclasses import replace
from datetime import datetime,timezone
import json
import math
import pathlib

import numpy as np
from scipy.special import logsumexp,ndtri

from .bayes_outcome_measurement import mixture_quantile,shifted_selection_normalizer
from .bayes_process_measurement import log_selection_weight
from .reconcile_evidence import digest,write
from .run_process_measurement import make_model, saved_config


def broad_probability(mixed,core,epsilon):
    """P(broad | report, latent duration); integrating ratios separately is wrong."""
    if epsilon==0:
        return np.zeros_like(mixed)
    log_regular=np.minimum(0.,math.log1p(-epsilon)+core-mixed)
    return -np.expm1(log_regular)


def conditional_attributions(model,core_model,z):
    result={}
    epsilon=model.cfg.contamination
    for p in model.programs:
        par=model.parameters(p,z)
        has_outcome='locations' in par
        locations=par['locations'] if has_outcome else np.array([par['mu']])
        pi=par.get('approval_probability',1.)
        logmix=np.log([pi,1-pi]) if has_outcome else np.array([0.])
        shifts=(locations-par['mu'])/par['sigma']
        normalizers=np.array([shifted_selection_normalizer(s,par['strength'],model.cfg.selection_width) for s in shifts])
        posting=np.array([0.,par['denial_posting']]) if has_outcome else np.array([0.])
        global_normalizer=logsumexp(logmix+posting+normalizers)
        for case,rows in p['cases'].items():
            outcome=p.get('outcomes',{}).get(case)
            branches=[0] if outcome=='approved' or not has_outcome else [1] if outcome=='denied' else [0,1]
            selected=any(m['audit']['reporting_sample']=='forum_selected' for m in rows)
            weights,attributions=[],[]
            for branch in branches:
                base=locations[branch]+par['sigma']*model.nodes
                mixed=np.array([model.observation_probability(m,base,par) for m in rows])
                core=np.array([core_model.observation_probability(m,base,par) for m in rows])
                logw=model.log_weights+mixed.sum(axis=0)
                if selected:
                    logw=logw+log_selection_weight(model.nodes+shifts[branch],par['strength'],model.cfg.selection_width)
                if len(branches)==1:
                    if selected:
                        logw=logw-normalizers[branch]
                else:
                    logw=logw+logmix[branch]+(posting[branch]-global_normalizer if selected else 0.)
                weights.append(logw)
                attributions.append(broad_probability(mixed,core,epsilon))
            logw=np.concatenate(weights)
            weight=np.exp(logw-logsumexp(logw))
            probabilities=np.concatenate(attributions,axis=1)@weight
            result.update({(p['id'],m['measurement']['id']):float(value) for m,value in zip(rows,probabilities)})
        for m in p['summaries']:
            stat=m['audit']['statistic_interpretation']
            if not has_outcome:
                base=par['mu']
            elif stat=='population_mean':
                base=float(logsumexp(logmix+locations))
            elif stat=='population_p90':
                base=mixture_quantile(.9,locations,par['sigma'],pi)-ndtri(.9)*par['sigma']
            else:
                base=mixture_quantile(.5,locations,par['sigma'],pi)
            mixed=model.observation_probability(m,base,par)
            core=core_model.observation_probability(m,base,par)
            result[(p['id'],m['measurement']['id'])]=float(broad_probability(mixed,core,epsilon))
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--states',type=int,default=400)
    args=ap.parse_args(argv)
    root,out=pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists() or args.states<1:
        raise ValueError('Use a fresh destination and at least one posterior state')
    manifest=json.loads((root/'manifest.json').read_text())
    if not manifest.get('completed_utc') or manifest.get('posterior_sha256')!=digest((root/'posterior.json').read_bytes()):
        raise ValueError('A completed saved posterior with matching hash is required')
    config=manifest['config']
    cfg=saved_config(config)
    inputs={name:json.loads((root/f'{name}.json').read_text()) if (root/f'{name}.json').exists() else None
            for name in ['evidence','audits','outcomes','preparations']}
    def create(configuration):
        return make_model(inputs['evidence'],inputs['audits'],configuration,inputs['outcomes'],inputs['preparations'])
    model,core=create(cfg),create(replace(cfg,contamination=0))
    arrays=np.load(root/'draws.npz')
    z=arrays['z'].reshape(-1,model.layout.size)
    ll=arrays['log_likelihood'].ravel()
    positions=np.linspace(0,len(z)-1,min(args.states,len(z))).astype(int)
    values={}
    max_error=0.
    for i in positions:
        error=abs(model.log_likelihood(z[i])-ll[i])
        if not math.isfinite(error) or error>1e-7:
            raise ValueError('Current likelihood does not reproduce saved fit')
        max_error=max(max_error,error)
        for key,value in conditional_attributions(model,core,z[i]).items():
            values.setdefault(key,[]).append(value)
    rows=[]
    for p in model.programs:
        for row in p['observations']:
            mid=row['measurement']['id']
            sample=values[(p['id'],mid)]
            rows.append(dict(program=p['id'],measurement_id=mid,
                mean_broad_component_probability=float(np.mean(sample)),
                conditional_probability_ci90=np.quantile(sample,[.05,.95]).tolist(),
                source=row['source'],case_id=row['measurement']['case_id'],quote=row['measurement']['quote'],
                preparation_anchor=bool(row.get('preparation_anchor'))))
    rows.sort(key=lambda r:-r['mean_broad_component_probability'])
    write(out/'attributions.json',dict(rows=rows,n_posterior_states=len(positions),
        warning='A model error component is not evidence that the source is false; misspecification can explain conflict.'))
    write(out/'manifest.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),base_run=str(root),
        posterior_sha256=manifest['posterior_sha256'],saved_likelihood_max_error=max_error,
        hidden_truth_read=False,source_sha256=digest(pathlib.Path(__file__).read_bytes())))
    print(json.dumps(rows[:10]),flush=True)


if __name__=='__main__':
    main()
