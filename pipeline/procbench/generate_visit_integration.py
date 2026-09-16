"""Frozen favorable development data for the joint visit-hierarchy integration.

Not a reserved synthetic-text benchmark. The fixed generating settings are in
docs/2026-09-16-bayesian-process-v6-protocol.md; inference reads observations, never truth.json.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
import math
import pathlib

import numpy as np

from .compact_visit_trace import Block,CompactTrace,Operation
from .rework_counts import ReworkLaw
from .reconcile_evidence import digest,write


def routes():
    ops=[dict(id='file',actor_id='payer',actor_role='payer',task_type='filing',markers=['submission'],
              payer_work=True,agency_work=False),
         dict(id='review',actor_id='J:Review',actor_role='agency',task_type='review',markers=[],
              payer_work=False,agency_work=True),
         dict(id='check',actor_id='J:Records',actor_role='agency',task_type='records',markers=[],
              payer_work=False,agency_work=True),
         dict(id='decide',actor_id='J:Review',actor_role='agency',task_type='decision',markers=['decision'],
              payer_work=False,agency_work=True)]
    full=dict(id='with_records_check',prior_weight=.5,operations=ops,blocks=[
        dict(id='review_cycle',operations=['file','review'],repeat_key='corrections'),
        dict(id='finalize',operations=['check','decide'])])
    simple=copy.deepcopy(full)
    simple.update(id='without_records_check',operations=[o for o in simple['operations'] if o['id']!='check'])
    simple['blocks'][-1]['operations']=['decide']
    return [simple,full]


def generate(seed=2026092007):
    rng=np.random.default_rng(seed)
    totals,mixed,truth=[],[],{}
    for program,n,q,r in [('J__P',10,.55,.35),('J__Q',3,.25,.20)]:
        templates=routes()
        means=np.log(np.array([[2.,8.,3.,1.],[.75,1.,1.,1.],[1.,1.5,.6,.2]]))
        values=np.exp(means[None,:,:]+.45*rng.normal(size=(n,3,4))+.20*rng.normal(size=(n,3,1)))
        payer=values[:,1,:].copy()
        payer[:,1:]=0.
        staff=values[:,2,:].copy()
        staff[:,0]=0.
        law=ReworkLaw(q,r)
        counts=np.array([law.quantile(float(u)) for u in rng.random(n)])
        full=templates[1]
        trace=CompactTrace([Operation(**o) for o in full['operations']],[Block(**b) for b in full['blocks']],
            values[:,0,:],{'corrections':counts},{'payer_hours':payer,'agency_hours':staff})
        base=dict(id=program,routes=templates,observations=[],rate_observations=[])
        rich=copy.deepcopy(base)
        def claim(case,ident,operator,count=False):
            actual=float(trace.values(operator)[case])
            reported=actual if count else actual*math.exp(.15*rng.normal())
            half=0. if count else .05*reported
            return dict(id=f'{case}:{ident}',case_id=f'case_{case}',source_family=f'{program}:interview:{case}',
                sampling='unselected',statistic='individual',lower=max(0.,reported-half),upper=reported+half,
                operators=[operator],operator_weights=[1.])
        for ci in range(n):
            o=claim(ci,'total',dict(basis='whole_case_clock',start='process_start',end='initial_decision'))
            base['observations'].append(o)
            rich['observations'].append(copy.deepcopy(o))
        for ci in range(min(n,3)):
            for ident,operator,is_count in [
                ('first_review',dict(basis='single_visit_cycle',activity_ids=['review']),False),
                ('visits',dict(basis='visit_count'),True),
                ('agency_work',dict(basis='agency_hours'),False),
                ('payer_work',dict(basis='payer_hours'),False)]:
                rich['observations'].append(claim(ci,ident,operator,is_count))
        for basis in ('operation_count','agency_count'):
            rich['observations'].append(claim(0,basis,dict(basis=basis),True))
        rich['rate_observations'].append(dict(repeat_key='corrections',event='any_correction_per_case',
            cohort_scope='completed_cases_for_repeat_block',independent_cohort=True,
            successes=int(rng.binomial(20,q)),trials=20))
        totals.append(base)
        mixed.append(rich)
        # These summaries are not supplied to the fitting runner.
        truth[program]=dict(route='with_records_check',first_visit_medians_days=[2.,8.,3.,1.],
            agency_inventory_mean_cycle_days={'J:Review':4.5*math.exp(.5*(.45**2+.20**2)),
                                             'J:Records':3.*math.exp(.5*(.45**2+.20**2))},
            probability_any_correction=q,probability_continue=r,distinct_operations=4,agencies=2,
            expected_visits=4+2*law.mean_additional_rounds,
            mean_agency_hours=(1.5*(1+law.mean_additional_rounds)+.6+.2)*math.exp(.5*(.45**2+.20**2)),
            mean_payer_hours=.75*(1+law.mean_additional_rounds)*math.exp(.5*(.45**2+.20**2)))
    return dict(timing_only=dict(programs=totals),mixed_evidence=dict(programs=mixed)),truth


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    parser.add_argument('--seed',type=int,default=2026092007)
    args=parser.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh development directory')
    datasets,truth=generate(args.seed)
    for name,data in datasets.items():
        write(out/(name+'.json'),data)
    write(out/'truth.json',truth)
    source=pathlib.Path(__file__)
    write(out/'manifest.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,
        scope='Favorable fixed-truth development integration, not reserved evaluation or full calibration',
        source_sha256=digest(source.read_bytes()),
        input_sha256={name:digest((out/(name+'.json')).read_bytes()) for name in datasets}))
    (out/'generator_source.py').write_bytes(source.read_bytes())
    print(json.dumps({name:{p['id']:len(p['observations']) for p in data['programs']} for name,data in datasets.items()}))


if __name__=='__main__':
    main()
