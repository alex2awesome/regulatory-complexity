"""Applicant fee totals as a path functional, and the count likelihood's reachability.

Money is deliberately not a resource channel: a published fee is an input, so its
only uncertainty is which path a case took and how often it repeated a block.
These tests pin that contract, the hard refusals that keep an unstated fee out of
a total, and the fact that a well-formed individual count observation reaches
`count_log_probability`.
"""
import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compact_visit_trace import (MONEY_BASES, Block, CompactTrace,
                                                    Operation, UnavailableTraceQuantity)
from procbench_fixtures import observation


FEE = dict(file=100., review=0., inspect=250., decide=50.)


def route_trace(names=('file', 'review', 'inspect', 'decide'), rounds=1, fees=FEE, durations=None):
    """One realized case over the named operations; 'file'/'review' are the repeat block."""
    spec = dict(
        file=dict(actor_id='payer', actor_role='payer', task_type='filing', markers=('submission',)),
        review=dict(actor_id='A', actor_role='agency', task_type='review', markers=()),
        inspect=dict(actor_id='A', actor_role='agency', task_type='inspection', markers=()),
        decide=dict(actor_id='A', actor_role='agency', task_type='decision', markers=('decision',)))
    operations = [Operation(name, spec[name]['actor_id'], spec[name]['actor_role'],
                            spec[name]['task_type'], spec[name]['markers'],
                            fee=fees.get(name)) for name in names]
    loop = tuple(n for n in names if n in ('file', 'review'))
    tail = tuple(n for n in names if n not in loop)
    blocks = ([Block('loop', loop, None, 'retry')] if loop else []) + ([Block('end', tail)] if tail else [])
    supplied = {'retry': np.array([rounds])} if loop else None
    if durations is None:
        durations = np.ones((1, len(names)))
    return CompactTrace(operations, blocks, durations, supplied)


def operation_dicts(with_fees, scale=1.):
    def fee(name):
        return scale*FEE[name] if with_fees else None
    return [dict(id='file', actor_id='payer', actor_role='payer', task_type='filing',
                 markers=['submission'], payer_work=True, agency_work=False, fee=fee('file')),
            dict(id='review', actor_id='J:Review', actor_role='agency', task_type='review',
                 payer_work=False, agency_work=True, fee=fee('review')),
            dict(id='decide', actor_id='J:Review', actor_role='agency', task_type='decision',
                 markers=['decision'], payer_work=False, agency_work=True, fee=fee('decide'))]


def money_data(observations, with_fees=True, scale=1.):
    """Source-free single-route program; no truth, specs or scores are read."""
    return dict(programs=[dict(id='J__P', routes=[dict(id='simple', prior_weight=1.,
        operations=operation_dicts(with_fees, scale), blocks=[
            dict(id='loop', operations=['file', 'review'], repeat_key='corrections'),
            dict(id='end', operations=['decide'])])],
        observations=observations, rate_observations=[])])


def test_reported_fee_mean_and_case_spread_include_repeat_multiplicity():
    model=VisitHierarchy(money_data([]),Config(population_size=16,modeled_channels=('elapsed',)))
    z=np.zeros(model.layout.size)
    p=model.programs[0]
    q,r=model.repeat_parameters(p,z)
    result=model.expected_burden(p,z,model.parameters(z),0)
    assert result['mean_fee_total']==pytest.approx(150+100*q[0]/(1-r[0]))
    assert result['fee_total_case_sd']==pytest.approx(100*np.sqrt(q[0]*(1+r[0]-q[0]))/(1-r[0]))
    assert result['mean_applicant_visit_count']==pytest.approx(1+q[0]/(1-r[0]))
    assert result['mean_applicant_operation_count']==1
    assert 'mean_payer_hours' not in result  # No invented labor channel.
    unknown=VisitHierarchy(money_data([],with_fees=False),model.cfg)
    result=unknown.expected_burden(unknown.programs[0],z,unknown.parameters(z),0)
    assert 'mean_fee_total' not in result and 'fee_total_case_sd' not in result


def test_applicant_count_keeps_unknown_applicability_unknown():
    data=money_data([])
    data['programs'][0]['routes'][0]['operations'][1]['payer_work']=None
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    result=model.expected_burden(model.programs[0],z,model.parameters(z),0)
    assert 'mean_applicant_visit_count' not in result
    assert 'mean_applicant_operation_count' not in result
    assert 'mean_fee_total' in result


def test_case_path_fee_spread_uses_total_variance_not_average_standard_deviation():
    data=money_data([])
    route=data['programs'][0]['routes'][0]
    route.pop('blocks')
    route['paths']=[dict(id='full',probability_weight=.75,
                        blocks=[dict(id='all',operations=['file','review','decide'])]),
                    dict(id='short',probability_weight=.25,
                        blocks=[dict(id='partial',operations=['file','review'])])]
    model=VisitHierarchy(data,Config(population_size=16,case_path_logit_sd=0.))
    z=np.zeros(model.layout.size)
    result=model.expected_burden(model.programs[0],z,model.parameters(z),0)
    assert result['mean_fee_total']==pytest.approx(.75*150+.25*100)
    assert result['fee_total_case_sd']==pytest.approx(np.sqrt(.75*.25)*50)


def test_fee_total_is_the_sum_over_traversed_visits_not_a_route_constant():
    """Pins cost as a path functional.

    If this regressed to a per-route constant, a case that stopped at the first
    gate would be charged for the inspection it never reached, and a case that
    went round the correction block three times would be charged once. Both are
    the burden claim the project rests on, so both must be read off the trace.
    """
    operator = dict(basis='payer_fee_total')
    once = route_trace(rounds=0)
    assert once.values(operator)[0] == sum(FEE.values())
    twice = route_trace(rounds=1)
    # the repeat block replays 'file' and 'review', so their fees are paid again
    assert twice.values(operator)[0] == sum(FEE.values()) + FEE['file'] + FEE['review']
    assert route_trace(rounds=3).values(operator)[0] == sum(FEE.values()) + 3*(FEE['file'] + FEE['review'])
    # a path that never reaches the inspection never pays for it
    without = route_trace(names=('file', 'review', 'decide'), rounds=1)
    assert without.values(operator)[0] == twice.values(operator)[0] - FEE['inspect']
    # an explicit operation subset is charged like the resource channels are
    assert once.values(dict(basis='payer_fee_total', activity_ids=['inspect']))[0] == FEE['inspect']
    assert twice.values(dict(basis='payer_fee_total', activity_ids=['file']))[0] == 2*FEE['file']


def test_an_unstated_fee_is_a_hard_error_and_never_an_unavailable_quantity():
    """Pins the refusal that keeps a silent zero out of a money total.

    A step whose fee is unknown is not a free step. If this were softened to
    `UnavailableTraceQuantity`, the caught exception would make the observation
    -inf on that route only (money has no residual alternative), so a route that
    honestly recorded an unknown fee would lose its posterior mass to a rival for
    the encoding alone. If it silently became zero instead, the reported total
    would understate burden with no record that it did.
    """
    fees = dict(FEE, inspect=None)
    trace = route_trace(fees=fees)
    with pytest.raises(ValueError, match='no stated fee') as caught:
        trace.values(dict(basis='payer_fee_total'))
    assert not isinstance(caught.value, UnavailableTraceQuantity)
    with pytest.raises(ValueError, match='no stated fee') as caught:
        trace.values(dict(basis='payer_fee_total', activity_ids=['file', 'inspect']))
    assert not isinstance(caught.value, UnavailableTraceQuantity)
    # an unstated fee elsewhere does not poison an explicitly selected subset,
    # which is still summed over visits ('file' is inside the repeated block)
    assert trace.values(dict(basis='payer_fee_total', activity_ids=['file', 'decide']))[0] == (
        2*FEE['file'] + FEE['decide'])
    # and no fee stated anywhere is still a refusal, not an implicit free process
    with pytest.raises(ValueError, match='no stated fee'):
        route_trace(fees={}).values(dict(basis='payer_fee_total'))


def test_an_unstated_fee_reaches_the_sampler_as_an_error_not_as_minus_infinity():
    """Pins that the hard refusal survives the likelihood's exception handling.

    `_observation_parts` catches `KeyError`/`UnavailableTraceQuantity` and turns
    them into -inf. A money observation against a route with an unstated fee is a
    construction error, so it must escape that handler and fail loudly at the
    first likelihood call rather than silently zeroing the route.
    """
    data = money_data([observation('fee', 'payer_fee_total', 140., 160.)], with_fees=False)
    model = VisitHierarchy(data, Config(population_size=16))
    z = np.zeros(model.layout.size)
    with pytest.raises(ValueError, match='no stated fee'):
        model.log_likelihood(z, [0])
    with pytest.raises(ValueError, match='no stated fee'):
        model.log_likelihood_reference(z, [0])


def test_a_malformed_money_operator_is_rejected_by_syntax_validation():
    """Pins that money joins the validated bases rather than the unknown ones.

    A basis absent from validation would be accepted at construction and then
    fail deep inside `values`, or worse, be read as an unknown operator whose
    activity IDs were never checked.
    """
    assert MONEY_BASES == ('payer_fee_total',)
    with pytest.raises(ValueError, match='activity IDs must be distinct'):
        VisitHierarchy(money_data([dict(observation('fee', 'payer_fee_total', 140., 160.),
            operators=[dict(basis='payer_fee_total', activity_ids=['file', 'file'])],
            operator_weights=[1.])]), Config(population_size=16))
    with pytest.raises(ValueError, match='unknown basis'):
        VisitHierarchy(money_data([observation('fee', 'payer_fee_totals', 140., 160.)]),
                       Config(population_size=16))


@pytest.mark.parametrize('other', [dict(basis='whole_case_clock', start='process_start',
                                        end='initial_decision'),
                                   dict(basis='visit_count'),
                                   dict(basis='unmodeled_duration', median_days=30., log_scale=1.)])
def test_money_cannot_be_an_alternative_reading_of_a_duration_or_a_count(other):
    """Pins that one phrase's readings cannot change units into or out of dollars.

    Mixing a fee total with a duration density, a count probability or the
    unmodeled-duration residual would add a log-dollar density to a log-day one
    inside a single logsumexp, producing an unnormalised and meaningless factor
    while looking like ordinary interpretation weighting.
    """
    claim = dict(observation('fee', 'payer_fee_total', 140., 160.),
                 operators=[dict(basis='payer_fee_total'), other], operator_weights=[.5, .5])
    with pytest.raises(ValueError, match='Cannot mix money amounts with durations or counts'):
        VisitHierarchy(money_data([claim]), Config(population_size=16))


def test_a_reported_fee_total_must_be_an_individual_case_report():
    """Pins money as an observation of one applicant, not of a schedule.

    A published fee schedule is an input to the trace; the observation is what an
    applicant says they paid. A population median fee would re-observe the model's
    own input as if it were evidence, double counting the schedule.
    """
    population = dict(observation('fee', 'payer_fee_total', 140., 160.), case_id=None,
                      statistic='median')
    with pytest.raises(ValueError, match='not individual fee-total reports'):
        VisitHierarchy(money_data([population]), Config(population_size=16))


def test_fees_add_no_coordinates_and_do_not_move_a_fee_free_likelihood():
    """Pins that money is not a fourth channel.

    A published amount is not random, so it must allocate no hierarchy
    coordinate. If fees ever grew a channel, every saved layout and every
    saved-seed replay would shift, and a fee schedule would start competing with
    the duration hierarchy for the same evidence.
    """
    claims = [observation('total', 'whole_case_clock', 15., 25.),
              observation('visits', 'visit_count', 3, 3)]
    plain = VisitHierarchy(money_data(claims, with_fees=False), Config(population_size=16))
    priced = VisitHierarchy(money_data(claims, with_fees=True), Config(population_size=16))
    with_report = VisitHierarchy(money_data(claims + [observation('fee', 'payer_fee_total', 140., 160.)]),
                                 Config(population_size=16))
    assert plain.layout.size == priced.layout.size == with_report.layout.size
    assert len(plain.operations) == len(priced.operations) == len(with_report.operations)
    assert len(plain.agencies) == len(priced.agencies) and len(plain.tasks) == len(priced.tasks)
    rng = np.random.default_rng(4711)
    for _ in range(8):
        z = rng.normal(size=plain.layout.size)
        assert priced.log_likelihood(z, [0]) == plain.log_likelihood(z, [0])


def test_a_reported_fee_total_is_a_relative_error_report_with_no_source_offset():
    """Pins the chosen likelihood form for money.

    The report kernel is the log-scale relative-error duration kernel (same
    reporting scale and same normalised contamination mixture) at a zero offset.
    A published price misreported by an applicant is rounding, not a systematic
    per-source bias, so `par['source']` must not touch it: an offset here would
    reintroduce a learned hierarchy through the back door and would be identified
    only by how wrong applicants are about a number the agency published.
    """
    fee_claim = observation('fee', 'payer_fee_total', 140., 160.)
    clock_claim = observation('total', 'whole_case_clock', 15., 25.)
    model = VisitHierarchy(money_data([fee_claim, clock_claim]), Config(population_size=16))
    rng = np.random.default_rng(99)
    for _ in range(4):
        z = .25*rng.normal(size=model.layout.size)
        shifted = z.copy()
        shifted[model.source[model.source >= 0]] += 1.5
        base, moved = model.log_likelihood(z, [0], parts=True), model.log_likelihood(shifted, [0], parts=True)
        assert np.isfinite(base['J__P:fee']) and np.isfinite(base['J__P:total'])
        assert base['J__P:fee'] == moved['J__P:fee']
        assert base['J__P:total'] != moved['J__P:total']
        # every code path agrees on the money factor
        assert model.log_likelihood_reference(z, [0], parts=True)['J__P:fee'] == pytest.approx(
            base['J__P:fee'], abs=1e-12)
    # relative error, not absolute: doubling the schedule and the reported total
    # together leaves the factor unchanged, so "$10 out" on a $190 fee and on a
    # $1900 fee are not treated as the same size of mistake.
    doubled = VisitHierarchy(money_data([observation('fee', 'payer_fee_total', 280., 320.)], scale=2.),
                             Config(population_size=16))
    z = np.zeros(model.layout.size)
    assert doubled.layout.size == model.layout.size
    assert doubled.log_likelihood(z, [0], parts=True)['J__P:fee'] == pytest.approx(
        model.log_likelihood(z, [0], parts=True)['J__P:fee'], abs=1e-9)


def test_a_point_fee_report_is_refused_until_its_rounding_interval_is_declared():
    """Pins that money uses the continuous-report contract, not the count one.

    A log-scale density gives an exact point zero probability. Accepting
    lower == upper for a fee would make every "$190" claim -inf and silently kill
    whatever route it was attached to.
    """
    with pytest.raises(ValueError, match='rounded continuous report'):
        VisitHierarchy(money_data([observation('fee', 'payer_fee_total', 190., 190.)]),
                       Config(population_size=16))


def test_a_money_observation_fits_for_a_few_draws():
    """Pins reachability end to end: construction, likelihood, and the sampler.

    A finite chain here is what distinguishes a basis that exists from a basis
    the model can actually use.
    """
    data = money_data([observation('total', 'whole_case_clock', 15., 25.),
                       observation('fee', 'payer_fee_total', 140., 160.)])
    model = VisitHierarchy(data, Config(seed=17, chains=1, warmup=1, draws=8, population_size=16))
    states, routes, likelihood, _ = model.sample()
    assert np.isfinite(likelihood).all() and np.isfinite(states).all()
    assert np.all(routes == 0)


@pytest.mark.parametrize('basis,bounds', [('visit_count', (3, 9)), ('operation_count', (3, 3)),
                                          ('agency_count', (1, 1))])
def test_each_individual_count_basis_reaches_a_finite_count_likelihood(basis, bounds):
    """Pins that `count_log_probability` is reachable from a well-formed claim.

    The count likelihood has been implemented and unused because nothing compiled
    an observation onto these bases. If a count observation stopped producing a
    finite factor -- through the channel check, the mixing rule or the operator
    validator -- the compiler now emitting count claims would silently lose every
    one of them, or zero a route.
    """
    lower, upper = bounds
    claim = observation('counted', basis, lower, upper)
    model = VisitHierarchy(money_data([claim]), Config(seed=23, chains=1, warmup=1, draws=8,
                                                       population_size=16))
    rng = np.random.default_rng(5)
    for _ in range(4):
        z = rng.normal(size=model.layout.size)
        parts = model.log_likelihood(z, [0], parts=True)
        assert np.isfinite(parts['J__P:counted'])
        assert model.log_likelihood_reference(z, [0], parts=True)['J__P:counted'] == pytest.approx(
            parts['J__P:counted'], abs=1e-12)
    states, routes, likelihood, _ = model.sample()
    assert np.isfinite(likelihood).all() and np.isfinite(states).all() and np.all(routes == 0)


def test_counts_and_a_fee_total_can_be_observed_on_the_same_case():
    """Pins that the two new evidence paths compose on one case.

    They are separate observations of the same visits, so they must multiply into
    one case factor. If either had been routed through the resource-channel check,
    supplying both would demand a payer/agency-hours channel that neither needs.
    """
    data = money_data([observation('visits', 'visit_count', 3, 9),
                       observation('agencies', 'agency_count', 1, 1),
                       observation('fee', 'payer_fee_total', 140., 160.)])
    model = VisitHierarchy(data, Config(population_size=16, modeled_channels=('elapsed',)))
    z = np.zeros(model.layout.size)
    parts = model.log_likelihood(z, [0], parts=True)
    assert set(parts) == {'J__P:visits', 'J__P:agencies', 'J__P:fee'}
    assert all(np.isfinite(value) for value in parts.values())


def path_money_data(lower, upper):
    """Two declared case paths that differ only by a fee-bearing inspection."""
    operations = operation_dicts(True) + [dict(id='inspect', actor_id='J:Review', actor_role='agency',
        task_type='inspection', payer_work=False, agency_work=True, fee=FEE['inspect'])]
    return dict(programs=[dict(id='J__P', routes=[dict(id='inventory', prior_weight=1.,
        operations=operations, paths=[
            dict(id='inspected', probability_weight=1.,
                 blocks=[dict(id='a', operations=['file', 'review', 'inspect', 'decide'])]),
            dict(id='straight_through', probability_weight=1.,
                 blocks=[dict(id='b', operations=['file', 'review', 'decide'])])])],
        observations=[observation('fee', 'payer_fee_total', lower, upper)], rate_observations=[])])


def test_a_reported_total_identifies_which_path_a_case_took():
    """Pins the payoff: money is path-dependent, so a fee report is evidence about structure.

    The two declared paths differ only by an inspection that costs $250. If the
    fee total were computed off the inventory rather than off the traversed
    trace, both paths would predict the same dollars and a reported total would
    carry no information about which path the case took -- which is the whole
    reason for making cost a path functional.
    """
    cfg = Config(population_size=16, modeled_channels=('elapsed',))
    posterior = {}
    for report, expected in ((140., 'straight_through'), (380., 'inspected')):
        model = VisitHierarchy(path_money_data(report, report + 40.), cfg)
        program = model.programs[0]
        z = np.zeros(model.layout.size)
        output, details = model._case_path_likelihood(program, z, model.parameters(z), 0, details=True)
        assert np.isfinite(output['J__P:case:c'])
        weights = dict(zip([path['id'] for path in program['routes'][0]['paths']],
                           details['case_weights']['c']))
        # the declared path prior is 1:1, so any separation here is the fee report
        assert weights[expected] > .9 and sum(weights.values()) == pytest.approx(1.)
        posterior[report] = weights['inspected']
    # the same two paths, the same prior, opposite conclusions from the dollars
    assert posterior[140.] < .1 < .9 < posterior[380.]
