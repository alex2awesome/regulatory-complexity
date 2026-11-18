"""Fixed-seed ten-case waiting/service integration data, not a full-burden benchmark.

This generator is independent of the inference implementation. Separate cycle-only
and mixed inputs share the identical cases and cycle reports. Truth is saved for
evaluation only and is never a fitter input.
"""
import argparse
import copy
from datetime import datetime,timezone
import json
import math
import pathlib

import numpy as np
from scipy.integrate import quad
from scipy.special import expit

from .infra.manifest import digest, write


def generate(seed=2026092011):
    rng=np.random.default_rng(seed)
    count=10
    cycle_median,cycle_sd,fraction_sd=14.,.35,.60
    fraction_median=(20/1440)/cycle_median
    fraction_location=math.log(fraction_median/(1-fraction_median))
    cycles=np.exp(math.log(cycle_median)+cycle_sd*rng.normal(size=count))
    fractions=expit(fraction_location+fraction_sd*rng.normal(size=count))
    route=dict(id='appointment',prior_weight=1.,operations=[dict(id='appointment',
        actor_id='J:Appointments',actor_role='agency',task_type='appointment',markers=['decision'],
        payer_work=None,agency_work=None)],blocks=[dict(id='visit',operations=['appointment'])])
    observations=[]
    for i,(cycle,fraction) in enumerate(zip(cycles,fractions)):
        for basis,value in [('single_visit_cycle',cycle),('wait_elapsed',cycle*(1-fraction)),
                            ('service_elapsed',cycle*fraction)]:
            report=value*math.exp(.10*rng.normal())
            op=dict(basis=basis,activity_ids=['appointment'],visits='first')
            observations.append(dict(id=f'case-{i}:{basis}',case_id=f'case-{i}',
                source_family=f'interview-{i}',sampling='unselected',statistic='individual',
                lower=float(report*.95),upper=float(report*1.05),operators=[op],operator_weights=[1.]))
    mixed=dict(schema_version='joint-visit-phase-development/1',programs=[dict(id='J__appointment',
        routes=[route],observations=observations,rate_observations=[])])
    cycle_only=copy.deepcopy(mixed)
    cycle_only['programs'][0]['observations']=[o for o in cycle_only['programs'][0]['observations']
                                            if o['operators'][0]['basis']=='single_visit_cycle']
    def integrand(z):
        return float(expit(fraction_location+fraction_sd*z))*math.exp(-z*z/2)/math.sqrt(2*math.pi)
    mean_fraction,error=quad(integrand,-math.inf,math.inf,epsabs=1e-13,epsrel=1e-11)
    cycle_mean=cycle_median*math.exp(cycle_sd**2/2)
    truth=dict(seed=seed,cases=count,cycle_median_days=cycle_median,cycle_log_sd=cycle_sd,
        service_fraction_logit_location=fraction_location,service_fraction_logit_sd=fraction_sd,
        mean_cycle_days=cycle_mean,mean_wait_days=cycle_mean*(1-mean_fraction),
        mean_service_elapsed_days=cycle_mean*mean_fraction,fraction_integral_error=error,
        realized_cases=[dict(case_id=f'case-{i}',cycle_days=float(d),service_fraction=float(f))
                        for i,(d,f) in enumerate(zip(cycles,fractions))],
        scope='Fixed favorable measurement test; no agency/task identification or full-burden/LLM claim')
    return cycle_only,mixed,truth


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh directory; generated cases and truth are immutable')
    cycle,mixed,truth=generate()
    for name,value in [('cycle_only',cycle),('mixed',mixed),('truth',truth)]:
        write(out/(name+'.json'),value)
    source=pathlib.Path(__file__)
    target=out/'source'/source.name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(source.read_bytes())
    write(out/'manifest.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        seed=truth['seed'],source_sha256=digest(source.read_bytes()),
        artifacts_sha256={name:digest((out/(name+'.json')).read_bytes()) for name in ('cycle_only','mixed','truth')},
        scope=truth['scope'],truth_is_inference_input=False))
    print(json.dumps(dict(out=str(out),cases=truth['cases'],observations=len(mixed['programs'][0]['observations']))))


if __name__=='__main__':
    main()
