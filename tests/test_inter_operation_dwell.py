"""Inter-operation dwell: waiting between steps, with its own scale, off by default.

`CompactTrace` used to concatenate blocks with no gap term, so every day of a
modelled process belonged to some operation and regulatory delay had nowhere to
live but inside the step beside it. The first real solar fit showed exactly that:
permit review inflated from a published 4 days to 39.5, inspection from 11 to
28.6, the phases with little waiting around them landed close, and the assembled
whole-process clock overshot 113 days by 82% because the waiting was counted
once inside the inflated steps and again in case variance.

These tests pin the primitive that gives that time its own home, and pin that it
stays entirely dormant until a route asks for it.
"""
import math

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compact_visit_trace import (Block, CompactTrace, Operation,
                                                    UnavailableTraceQuantity, unit_dwell_array)
from procbench_fixtures import data_fixture, observation


# The fixture's historical receipt, recorded against the pre-change source: three
# channels, three operations, one case, one repeat key.
HISTORICAL_SIZE = 48
HISTORICAL_BLOCKS = {'location': 3, 'agency': 6, 'task': 9, 'operation': 9, 'case_sigma': 3,
                     'source': 3, 'J__P:repeat': 2, 'J__P:selection': 0, 'J__P:cases': 13}
HISTORICAL_CASE_DIMENSION = 13


def dwell_fixture(sites=('review', 'decide')):
    """`data_fixture()` with a declared dwell before each named operation."""
    data = data_fixture()
    for block in data['programs'][0]['routes'][0]['blocks']:
        declared = [aid for aid in block['operations'] if aid in sites]
        if declared:
            block['dwells'] = declared
    return data


def trace_route(dwell_sites=(), rounds=0, dwell_days=None, durations=None, supply=True):
    """One realized case: [file, review] repeat once per round, then [decide].

    `dwell_sites` names the operations a declared dwell precedes; `dwell_days` is
    the waiting supplied for them. Deliberately built without the hierarchy so the
    timing contract is pinned independently of how a dwell gets drawn.
    """
    names = ('file', 'review', 'decide')
    spec = dict(file=('payer', 'payer', 'filing', ('submission',)),
                review=('A', 'agency', 'review', ()),
                decide=('A', 'agency', 'decision', ('decision',)))
    operations = [Operation(name, *spec[name]) for name in names]
    blocks = [Block('loop', ('file', 'review'), None, 'retry',
                    tuple(n for n in ('file', 'review') if n in dwell_sites) or None),
              Block('end', ('decide',), None, None,
                    ('decide',) if 'decide' in dwell_sites else None)]
    dwells = None
    if dwell_sites and supply:
        dwells = np.full((1, len(names)), math.nan)
        for aid, value in (dwell_days or {aid: 5. for aid in dwell_sites}).items():
            dwells[0, names.index(aid)] = value
    return CompactTrace(operations, blocks,
                        np.ones((1, len(names))) if durations is None else durations,
                        {'retry': np.array([rounds])}, dwells=dwells)


def test_dwell_is_off_by_default_and_the_flag_alone_changes_nothing():
    """Pins that the whole primitive is historically inert.

    If this regressed, every saved V6 layout, checkpoint, seed replay and
    `--diagnose-run` receipt in `runs/` would silently refer to a different
    parameterization, and every historical control fit would become
    unreproducible. The flag defaults to off; turning it on for a route that
    declares no gap must also change nothing, so the code path cannot leak into
    a fit that did not ask for waiting.
    """
    assert Config().inter_operation_dwell is False
    base = VisitHierarchy(data_fixture(), Config(population_size=16))
    assert base.dwell_coordinates is None and base.dwell_sites == []
    assert base.layout.size == HISTORICAL_SIZE
    assert {name: len(idx) for name, idx in base.layout.slices.items()} == HISTORICAL_BLOCKS
    assert base.programs[0]['case_dimension'] == HISTORICAL_CASE_DIMENSION

    enabled = VisitHierarchy(data_fixture(), Config(population_size=16, inter_operation_dwell=True))
    assert enabled.dwell_coordinates is None and enabled.dwell_sites == []
    assert enabled.layout.size == base.layout.size
    for name, indices in base.layout.slices.items():
        assert np.array_equal(enabled.layout.slices[name], indices)
    assert enabled.programs[0]['case_dimension'] == HISTORICAL_CASE_DIMENSION
    rng = np.random.default_rng(20260918)
    for z in [np.zeros(base.layout.size)] + [rng.normal(size=base.layout.size) for _ in range(6)]:
        # bit-for-bit, not approximately: an identical target, not a similar one
        assert enabled.log_likelihood(z, [0]) == base.log_likelihood(z, [0])
        assert enabled.log_likelihood_reference(z, [0]) == base.log_likelihood_reference(z, [0])

    replay = dict(seed=4242, chains=2, warmup=3, draws=12, population_size=16)
    before = VisitHierarchy(data_fixture(), Config(**replay)).sample()
    after = VisitHierarchy(data_fixture(), Config(**replay, inter_operation_dwell=True)).sample()
    for x, y in zip(before[:3], after[:3]):
        assert np.array_equal(x, y)


def test_a_dwell_adds_elapsed_time_to_every_clock_event_after_it():
    """Pins that a dwell is real elapsed time on the case clock.

    This is the whole point: the between-phase days must land in the gap and push
    the events after it later. If a dwell did not move the clock, the fit would go
    on attributing the waiting to the step beside it, which is how a published
    4-day permit review came back as a 39.5-day posterior.
    """
    plain = trace_route()
    waited = trace_route(dwell_sites=('review',), dwell_days={'review': 11.})
    assert plain.event('initial_decision')[0] == 3.
    assert waited.event('initial_decision')[0] == 14.
    assert waited.event('modeled_work_end')[0] - plain.event('modeled_work_end')[0] == 11.
    # the dwell sits before 'review' and after 'file', so a submission marker
    # recorded on 'file' is untouched while the later decision moves
    assert waited.event('first_submission')[0] == plain.event('first_submission')[0]
    assert waited.first_start[0, waited.index['review']] == 12.
    # a whole-case clock that spans the gap grows by exactly the wait; one that
    # ends before it does not move at all
    clock = dict(basis='whole_case_clock', start='process_start', end='initial_decision')
    assert waited.values(clock)[0] - plain.values(clock)[0] == 11.
    early = dict(basis='whole_case_clock', start='process_start', end='first_submission')
    assert waited.values(early)[0] == plain.values(early)[0]
    # and a span across the gap carries it, while the operation's own cycle does not
    span = dict(basis='first_to_last_activity_span', activity_ids=['file', 'review'])
    assert waited.values(span)[0] - plain.values(span)[0] == 11.
    assert waited.values(dict(basis='single_visit_cycle', activity_ids=['review']))[0] == 1.


def test_a_dwell_is_not_a_visit_not_an_operation_and_not_work():
    """Pins that nobody did anything during a dwell.

    A dwell that incremented a visit or operation count would corrupt the model's
    one well-identified output, and a dwell that entered payer or agency hours
    would invent labour out of queue time -- turning "the file sat in a tray for
    three weeks" into three weeks of somebody's effort.
    """
    hours = dict(payer_hours=np.ones((1, 3)), agency_hours=np.full((1, 3), 2.))
    def build(sites):
        names = ('file', 'review', 'decide')
        operations = [Operation('file', 'payer', 'payer', 'filing', ('submission',), True, False),
                      Operation('review', 'A', 'agency', 'review', (), False, True),
                      Operation('decide', 'A', 'agency', 'decision', ('decision',), False, True)]
        blocks = [Block('loop', ('file', 'review'), None, 'retry',
                        tuple(n for n in names if n in sites and n != 'decide') or None),
                  Block('end', ('decide',), None, None, ('decide',) if 'decide' in sites else None)]
        dwells = None
        if sites:
            dwells = np.full((1, 3), math.nan)
            for aid in sites:
                dwells[0, names.index(aid)] = 9.
        return CompactTrace(operations, blocks, np.ones((1, 3)), {'retry': np.array([2])},
                            hours, dwells=dwells)
    plain, waited = build(()), build(('review', 'decide'))
    assert waited.event('modeled_work_end')[0] > plain.event('modeled_work_end')[0]
    for operator in (dict(basis='visit_count'), dict(basis='operation_count'),
                     dict(basis='agency_count'), dict(basis='payer_hours'),
                     dict(basis='agency_hours'), dict(basis='sum_visit_cycles',
                                                      activity_ids=['file', 'review', 'decide'])):
        assert waited.values(operator)[0] == plain.values(operator)[0]
    assert np.array_equal(waited.visits, plain.visits)
    # the reference expansion shows the dwell as a gap between visits, never as a
    # visit row of its own
    assert len(waited.materialize().visits) == len(plain.materialize().visits)
    rows = sorted(waited.materialize().visits, key=lambda v: v.start)
    assert rows[1].start - rows[0].end == 9.


def test_a_repeated_block_replays_its_dwell_on_every_round():
    """Pins that waiting happens again on each correction round.

    A dwell computed once per block rather than once per traversal would model a
    case that went round the correction loop three times as having queued once,
    understating precisely the burden that repeated rounds impose. The cycle
    length must carry the wait, so `(rounds + 1)` cycles carry it that many times.
    """
    def end(rounds, sites=(), wait=5.):
        return trace_route(dwell_sites=sites, rounds=rounds,
                           dwell_days={aid: wait for aid in sites}).event('modeled_work_end')[0]
    # 'review' is inside the repeat block; 'decide' is in the block after it
    for rounds in (0, 1, 3):
        assert end(rounds, ('review',)) - end(rounds) == 5.*(rounds + 1)
        assert end(rounds, ('decide',)) - end(rounds) == 5.
    inner = trace_route(dwell_sites=('review',), rounds=2, dwell_days={'review': 5.})
    # each round starts one full cycle later, and the cycle now includes the wait
    assert inner.first_start[0, inner.index['review']] == 6.
    assert inner.last_start[0, inner.index['review']] == 6. + 2*7.
    assert inner.visits[0, inner.index['review']] == 3


def test_dwells_have_their_own_scale_and_do_not_inherit_the_operation_hierarchy():
    """Pins that waiting is not distributed like work.

    Reusing the operation's duration parameters is the failure mode this exists to
    fix: a gap forced onto the step's own prior and random effects would let a long
    wait drag that step's estimate up, which is the tenfold review inflation again
    with extra steps. Moving the operation priors must not move a dwell, moving the
    dwell prior must not move an operation duration, and the dwell coordinates
    must be separately addressable in `z`.
    """
    data = dwell_fixture()
    cfg = Config(population_size=16, inter_operation_dwell=True)
    model = VisitHierarchy(data, cfg)
    assert model.dwell_sites == [('J__P', 'review'), ('J__P', 'decide')]
    # two levels only: a population wait and one effect per gap, no agency or task
    assert len(model.layout.slices['dwell_location']) == 1
    assert len(model.layout.slices['dwell_site']) == len(model.dwell_sites)

    def realized(config, z=None):
        m = VisitHierarchy(dwell_fixture(), config)
        z = np.zeros(m.layout.size) if z is None else z
        par = m.parameters(z)
        trace = m.trace(m.programs[0], z, par, 0)
        return trace.dwell_days[0], trace.durations[0]

    dwell, duration = realized(cfg)
    assert dwell == pytest.approx([0., cfg.dwell_prior_median, cfg.dwell_prior_median])
    # a different operation-duration prior leaves the waiting untouched
    other_work, other_duration = realized(Config(population_size=16, inter_operation_dwell=True,
        elapsed_prior_median=40., operation_sd=3., case_log_sd_median=1.5))
    assert np.array_equal(other_work, dwell) and not np.array_equal(other_duration, duration)
    # a different waiting prior leaves every operation duration untouched
    other_wait, same_duration = realized(Config(population_size=16, inter_operation_dwell=True,
        dwell_prior_median=60., dwell_site_sd=2.5))
    assert np.array_equal(same_duration, duration) and not np.array_equal(other_wait, dwell)
    assert other_wait == pytest.approx([0., 60., 60.])

    # perturbing only the dwell coordinates moves the clock and not the step
    rng = np.random.default_rng(31)
    z = rng.normal(size=model.layout.size)
    shifted = z.copy()
    shifted[model.dwell_coordinates] += 1.
    for state, other in ((z, shifted), (shifted, z)):
        a = model.trace(model.programs[0], state, model.parameters(state), 0)
        b = model.trace(model.programs[0], other, model.parameters(other), 0)
        assert np.array_equal(a.durations, b.durations)
        assert not np.array_equal(a.dwell_days, b.dwell_days)
        assert a.event('initial_decision')[0] != b.event('initial_decision')[0]
    assert model.log_likelihood(z, [0]) != model.log_likelihood(shifted, [0])


def test_a_declared_dwell_with_no_supplied_wait_is_a_hard_construction_error():
    """Pins the refusal discipline: an unstated dwell is not zero.

    Softened to `UnavailableTraceQuantity`, this would be swallowed by the
    `KeyError`/`UnavailableTraceQuantity` handler in `_observation_parts` and make
    the observation -inf on that route alone. Two routes differing only in whether
    a declared gap's wait was supplied would then resolve in favour of the gapless
    one for the encoding alone -- the same silent structural inference the audit
    caught for hours, counts and money. Zero-filling instead would be worse: it
    would reinstate the gapless model while claiming to have modelled waiting.
    """
    # every one of these must escape all four exception types on the likelihood
    # path: `_observation_parts` swallows KeyError/UnavailableTraceQuantity and
    # `log_likelihood` swallows FloatingPointError/OverflowError into -inf
    swallowed = (KeyError, UnavailableTraceQuantity, FloatingPointError, OverflowError)
    with pytest.raises(ValueError, match='unstated dwell is not zero') as caught:
        trace_route(dwell_sites=('review',), supply=False)
    assert not isinstance(caught.value, swallowed)
    for bad in (0., -1., math.nan, math.inf):
        with pytest.raises(ValueError, match='finite positive wait') as caught:
            trace_route(dwell_sites=('review', 'decide'), dwell_days={'review': 5., 'decide': bad})
        assert not isinstance(caught.value, swallowed)
    # and the converse: time cannot be smuggled into a gap nobody declared
    with pytest.raises(ValueError, match='undeclared gap') as caught:
        trace_route(dwell_sites=('review',), dwell_days={'review': 5., 'decide': 8.})
    assert not isinstance(caught.value, swallowed)
    with pytest.raises(ValueError, match='declares no dwell') as caught:
        CompactTrace([Operation('only', 'A', 'agency', 'review')], [Block('b', ('only',))],
                     np.ones((1, 1)), dwells=np.ones((1, 1)))
    assert not isinstance(caught.value, swallowed)
    # a declaration that names an operation of another block is malformed syntax,
    # which must fail validation rather than become an impossible interpretation
    operations = [Operation('a', 'A', 'agency', 'review'), Operation('b', 'A', 'agency', 'review')]
    blocks = [Block('one', ('a',), None, None, ('b',)), Block('two', ('b',))]
    with pytest.raises(ValueError, match='distinct operation of its own block') as caught:
        CompactTrace(operations, blocks, np.ones((1, 2)),
                     dwells=unit_dwell_array(operations, blocks))
    assert not isinstance(caught.value, swallowed)


def test_a_dwell_the_model_cannot_value_fails_loudly_instead_of_zeroing_a_route():
    """Pins that a registration bug cannot become a silent structural inference.

    A route whose declared gap the hierarchy cannot supply is a construction
    error, and `log_likelihood` must raise rather than return -inf for that route
    and a finite value for its gapless rival. Emptying the program's site map
    stands in for a future refactor that forgets to register a declared gap; if
    that were swallowed, the encoding alone would decide the inventory, which is
    the exact failure the audit recorded above `agency_count`.
    """
    model = VisitHierarchy(dwell_fixture(sites=('review',)),
                           Config(population_size=16, inter_operation_dwell=True))
    z = np.zeros(model.layout.size)
    assert math.isfinite(model.log_likelihood(z, [0]))
    model.programs[0]['cache'].clear()
    model.programs[0]['dwell_local'] = {}
    with pytest.raises(KeyError):
        model.log_likelihood(z, [0])


def test_declaring_a_dwell_without_the_flag_is_refused_rather_than_ignored():
    """Pins that a declaration cannot be silently dropped.

    Ignoring `dwells` when the flag is off would model the route as gapless while
    the input said otherwise, and the waiting would reappear inside the steps with
    nothing recording that the declaration had been discarded. Refusing keeps the
    default-off guarantee honest in both directions.
    """
    with pytest.raises(ValueError, match='require the explicit inter_operation_dwell model'):
        VisitHierarchy(dwell_fixture(), Config(population_size=16))
    with pytest.raises(ValueError, match='Invalid sampling/contamination settings'):
        Config(inter_operation_dwell=1)


def test_a_dwell_enabled_model_allocates_its_own_coordinates_and_fits_for_a_few_draws():
    """Pins the size of the primitive and that it is reachable end to end.

    One population coordinate, one per declared gap, and one per case per gap: if
    that grew to a full agency/task design the dimension would rise with the
    inventory rather than with the number of gaps actually declared, and a fit on
    a 35-operation real route would pay for waiting it never modelled. A finite
    chain here is what separates a primitive that exists from one a fit can use.
    """
    base = VisitHierarchy(data_fixture(), Config(population_size=16))
    model = VisitHierarchy(dwell_fixture(), Config(population_size=16, inter_operation_dwell=True))
    gaps, cases = len(model.dwell_sites), len(model.programs[0]['cases'])
    assert (gaps, cases) == (2, 1)
    assert model.layout.size == base.layout.size + 1 + gaps + cases*gaps == 53
    assert model.programs[0]['case_dimension'] == HISTORICAL_CASE_DIMENSION + gaps
    # one gap declared instead of two costs one site and one case coordinate less
    single = VisitHierarchy(dwell_fixture(sites=('review',)),
                            Config(population_size=16, inter_operation_dwell=True))
    assert single.layout.size == base.layout.size + 1 + 1 + cases*1
    # and a zero case spread allocates no per-case waiting latent at all, which is
    # the sizing knob for a real route with many gaps and many cases
    flat = VisitHierarchy(dwell_fixture(), Config(population_size=16, inter_operation_dwell=True,
                                                  dwell_case_sd=0.))
    assert flat.layout.size == base.layout.size + 1 + gaps
    assert flat.programs[0]['case_dimension'] == HISTORICAL_CASE_DIMENSION
    z = np.zeros(flat.layout.size)
    waits = flat.trace(flat.programs[0], z, flat.parameters(z), 0).dwell_days
    assert np.isfinite(waits).all() and np.all(waits[:, 1:] > 0.)

    fitted = VisitHierarchy(dwell_fixture(), Config(seed=19, chains=1, warmup=1, draws=8,
                                                    population_size=16, inter_operation_dwell=True))
    states, routes, likelihood, _ = fitted.sample()
    assert np.isfinite(likelihood).all() and np.isfinite(states).all() and np.all(routes == 0)
    report = fitted.report(states, routes, likelihood)
    metrics = report['programs']['J__P']['metrics']
    assert 'mean_dwell_days:review' in metrics and 'mean_dwell_days:decide' in metrics
    assert metrics['mean_dwell_days:review']['mean'] > 0.
    assert report['config']['inter_operation_dwell'] is True
    assert any('inter-operation dwells are elapsed waiting only' in line
               for line in report['limitations'])
    # the dwell is reported as its own quantity, never folded into the step
    plain = VisitHierarchy(data_fixture(), Config(seed=19, chains=1, warmup=1, draws=8,
                                                  population_size=16))
    plain_report = plain.report(*plain.sample()[:3])
    assert not any(key.startswith('mean_dwell_days')
                   for key in plain_report['programs']['J__P']['metrics'])
    assert not any('inter-operation dwells' in line for line in plain_report['limitations'])


def test_a_dwell_is_declarable_on_a_case_path_and_pooled_across_route_hypotheses():
    """Pins that waiting is one parameter per gap, not one per hypothesis.

    Alternative inventories describe the same reality, so the wait before a given
    operation must be the same site in every one of them; otherwise each extra
    route hypothesis would duplicate the waiting parameters and the evidence about
    a gap would be split across coordinates that nothing ties together.
    """
    operations = [dict(id='file', actor_id='payer', actor_role='payer', task_type='filing',
                       markers=['submission'], payer_work=True, agency_work=False),
                  dict(id='review', actor_id='J:Review', actor_role='agency', task_type='review',
                       payer_work=False, agency_work=True),
                  dict(id='decide', actor_id='J:Review', actor_role='agency', task_type='decision',
                       markers=['decision'], payer_work=False, agency_work=True)]
    data = dict(programs=[dict(id='J__P', routes=[
        dict(id='paths', prior_weight=1., operations=operations, paths=[
            dict(id='short', probability_weight=1., blocks=[
                dict(id='a', operations=['file', 'review', 'decide'], dwells=['review'])]),
            dict(id='long', probability_weight=1., blocks=[
                dict(id='b', operations=['file', 'review'], dwells=['review']),
                dict(id='c', operations=['decide'], dwells=['decide'])])]),
        dict(id='serial', prior_weight=1., operations=operations, blocks=[
            dict(id='d', operations=['file', 'review', 'decide'], dwells=['review'])])],
        observations=[observation('total', 'whole_case_clock', 15., 45.)], rate_observations=[])])
    model = VisitHierarchy(data, Config(population_size=16, inter_operation_dwell=True,
                                        modeled_channels=('elapsed',)))
    assert model.dwell_sites == [('J__P', 'review'), ('J__P', 'decide')]
    assert model.programs[0]['dwell_ops'] == ['decide', 'review']
    z = np.zeros(model.layout.size)
    for route in (0, 1):
        assert np.isfinite(model.log_likelihood(z, [route]))
        assert model.log_likelihood_reference(z, [route], parts=True) == pytest.approx(
            model.log_likelihood(z, [route], parts=True))
    # the gap before 'review' is on both declared paths, so it is one coordinate
    par = model.parameters(z)
    site = model.dwell_index[('J__P', 'review')]
    for path in (0, 1):
        trace = model.trace(model.programs[0], z, par, 0, path_index=path)
        assert trace.dwell_days[0, trace.index['review']] == math.exp(par['dwell_log'][site])
