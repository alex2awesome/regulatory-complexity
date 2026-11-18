"""Independent ambiguous-clock data and truth; no inference-module imports.

Two operations repeat together. A review report may measure one cycle, summed
review cycles, or its first-to-last span. Inference is not told which generated it.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
import math
import pathlib

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import ndtr

from .infra.manifest import digest, write


BASES = ('single_visit_cycle', 'sum_visit_cycles', 'first_to_last_activity_span')


def cycle_cdf(value, sd=.35):
    """CDF of independent Lognormal(log 2, sd) + Lognormal(log 8, sd)."""
    if value <= 0:
        return 0.
    upper = (math.log(value)-math.log(2.))/sd
    def integrand(z):
        first = math.exp(math.log(2.)+sd*z)
        if first >= value:
            return 0.
        remaining = math.log(value-first)
        return math.exp(-z*z/2)/math.sqrt(2*math.pi)*ndtr((remaining-math.log(8.))/sd)
    return quad(integrand, -math.inf, upper, epsabs=1e-11, epsrel=1e-10)[0]


def clock_truth():
    """Independent continuous integration with a bounded omitted geometric tail."""
    q, r, terms = .4, .2, 24
    weights = np.r_[1-q, [q*(1-r)*r**(k-1) for k in range(1, terms)]]
    def cdf(value, repeated):
        if not repeated:
            return cycle_cdf(value)
        return sum(weight*cycle_cdf(value/(i+1)) for i, weight in enumerate(weights))
    result = {}
    for event, repeated in [('initial_decision', False), ('final_decision', True)]:
        for label, probability in [('median', .5), ('p90', .9)]:
            result[event+'_'+label+'_days'] = brentq(lambda value: cdf(value, repeated)-probability,
                                                    1e-5, 1000., xtol=1e-10)
    return result, float(q*r**(terms-1))


def generate(seed=2026092023):
    rng = np.random.default_rng(seed)
    count, sd, q, r = 10, .35, .4, .2
    cycles = np.exp(np.log([2., 8.])[None, :] + sd*rng.normal(size=(count, 2)))
    rounds = (rng.random(count) < q) * rng.geometric(1-r, size=count)
    interpretations = rng.integers(0, 3, size=count)
    route = dict(id='serial_repeat', prior_weight=1., operations=[
        dict(id='file', actor_id='payer', actor_role='payer', task_type='filing', markers=['submission'],
             payer_work=None, agency_work=False),
        dict(id='review', actor_id='J:Review', actor_role='agency', task_type='technical_review',
             markers=['decision'], payer_work=False, agency_work=None)],
        blocks=[dict(id='cycle', operations=['file', 'review'], repeat_key='corrections')])
    base, extra, realized = [], [], []
    for i, ((filing, review), repeat, interpretation) in enumerate(zip(cycles, rounds, interpretations)):
        visits = int(repeat)+1
        total = visits*(filing+review)
        values = [review, visits*review, total-filing]
        def observation(ident, lower, upper, operators, weights):
            return dict(id=f'case-{i}:{ident}', case_id=f'case-{i}', source_family=f'interview-{i}',
                sampling='unselected', statistic='individual', lower=float(lower),
                upper=float(upper), operators=operators, operator_weights=weights)
        report = total*math.exp(.10*rng.normal())
        base.append(observation('total', report*.95, report*1.05,
            [dict(basis='whole_case_clock', start='process_start', end='final_decision')], [1.]))
        base.append(observation('visits', 2*visits, 2*visits, [dict(basis='visit_count')], [1.]))
        report = values[int(interpretation)]*math.exp(.10*rng.normal())
        operators = [dict(basis=basis, activity_ids=['review'],
            visits='one_unspecified' if j == 0 else 'all_in_completed_case') for j, basis in enumerate(BASES)]
        operators.append(dict(basis='unmodeled_duration', median_days=7., log_scale=3.))
        extra.append(observation('ambiguous_review', report*.95, report*1.05, operators, [.25]*4))
        realized.append(dict(case_id=f'case-{i}', filing_cycle_days=float(filing), review_cycle_days=float(review),
            additional_rounds=int(repeat), interpretation=int(interpretation), generating_basis=BASES[int(interpretation)]))
    base_data = dict(schema_version='joint-visit-interpretation-development/1', programs=[dict(
        id='J__ambiguous', routes=[route], observations=base, rate_observations=[])])
    conditions = {'timing_count_only': base_data}
    for weight, name in [(.1, 'mixed_residual10'), (.25, 'mixed_residual25'), (.5, 'mixed_residual50')]:
        data = copy.deepcopy(base_data)
        additions = copy.deepcopy(extra)
        for row in additions:
            row['operator_weights'] = [(1-weight)/3]*3 + [weight]
        data['programs'][0]['observations'].extend(additions)
        conditions[name] = data
    clocks, tail = clock_truth()
    truth = dict(seed=seed, cases=count, realized_cases=realized, process_quantiles=clocks,
        mean_review_cycle_days=8*math.exp(sd*sd/2), mean_visit_count=2*(1+q/(1-r)),
        mean_operation_count=2., mean_agency_count=1., probability_any_correction=q,
        probability_continue=r, geometric_tail_bound=tail,
        scope='Fixed ten-case ambiguous-measurement integration; not text-pipeline calibration or an LLM comparison')
    return conditions, truth


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh immutable data directory')
    conditions, truth = generate()
    for name, value in {**conditions, 'truth': truth}.items():
        write(out/(name+'.json'), value)
    source = pathlib.Path(__file__)
    target = out/'source'/source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    write(out/'manifest.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(), seed=truth['seed'],
        conditions=list(conditions), source_sha256=digest(source.read_bytes()),
        artifacts_sha256={name: digest((out/(name+'.json')).read_bytes()) for name in [*conditions, 'truth']},
        truth_is_inference_input=False, scope=truth['scope']))
    print(json.dumps(dict(out=str(out), cases=truth['cases'], conditions=list(conditions))), flush=True)


if __name__ == '__main__':
    main()
