from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_hierarchy import Config, HierarchicalModel, Process, timing_interval, log_interval, agency_registry
from pipeline.procbench.evidence_contract import VERSION, validate


def fixture():
    ref = {"doc_id": "document", "quote": "Evidence"}
    evidence = {"schema_version": VERSION, "program_id": "test__permit",
        "actors": [{"id": "payer", "name": "Applicant", "role": "payer", "aliases": [], "evidence": [ref]},
                   {"id": "agency", "name": "Revenue", "role": "agency", "aliases": [], "evidence": [ref]}],
        "activities": [], "relations": [], "measurements": [], "ambiguities": [], "excluded": []}
    for aid, stage, task, actor in [("file", "submission", "filing", "payer"),
            ("review", "review", "technical_review", "agency"),
            ("decide", "decision", "decision", "agency")]:
        evidence["activities"].append({"id": aid, "name": aid, "stage": stage,
            "task_type": task, "actor_id": actor, "scope": "core", "condition": None,
            "existence": "explicit", "evidence": [ref], "notes": ""})
    return evidence


def test_generic_city_names_do_not_accidentally_pool_distinct_registry_roots():
    import copy
    first,second = fixture(),fixture()
    first['program_id'],second['program_id'] = 'J1__one','J1__two'
    for e in (first,second):
        e['actors'][1].update(name='City of Halvern',aliases=['City','local agency'])
    registry = agency_registry([first,second])
    assert registry[('J1__one','agency')] != registry[('J1__two','agency')]
    assert agency_registry([second,first]) == registry
    # Distinctive, supported department aliases still pool within a jurisdiction.
    first['actors'][1].update(name='Halvern Revenue Division',aliases=['Revenue Division'])
    second['actors'][1].update(name='Revenue Division',aliases=[])
    registry = agency_registry([first,second])
    assert registry[('J1__one','agency')] == registry[('J1__two','agency')]
    third = copy.deepcopy(second)
    third['program_id'] = 'J2__two'
    registry = agency_registry([first,second,third])
    assert registry[('J1__one','agency')] != registry[('J2__two','agency')]


def measurement(aid="review", scope="step", value=12., case="c1", statistic="individual", ident="m1"):
    return {"id": ident, "metric": "elapsed", "scope": scope, "activity_ids": [aid] if aid else [],
            "start": "activity_start" if scope == "step" else "preparation_start",
            "end": "activity_end" if scope == "step" else "decision",
            "statistic": statistic, "value": value, "lower": None, "upper": None,
            "unit": "calendar_days", "qualitative": False, "n": None, "case_id": case,
            "cohort": None, "source_family": "document", "doc_id": "document",
            "quote": "Evidence", "interpretation": ""}


def add_context(evidence, mid, **kwargs):
    evidence['schema_version'] = 'process-evidence/3'
    context = dict(measurement_id=mid, temporal_scope='unspecified',
                   required_activity_ids=[], excluded_activity_ids=[], decision_activity_id=None,
                   segment_mode='not_segment', evidence=[{'doc_id': 'document', 'quote': 'Evidence'}], notes='')
    context.update(kwargs)
    evidence.setdefault('observation_contexts', []).append(context)


def test_historical_claims_retained_but_not_current_likelihood():
    e = fixture()
    e['measurements'] = [measurement(ident='old'), measurement(ident='now')]
    add_context(e, 'old', temporal_scope='historical')
    model = HierarchicalModel([e])
    assert [m['id'] for _, m in model.observations] == ['now']
    assert 'historical' in model.processes[0].excluded[0]['reason']
    assert len(model.processes[0].evidence['measurements']) == 2


def test_selected_population_context_does_not_change_unconditional_route_prevalence():
    e = fixture()
    e['activities'][1].update(scope='conditional', condition='missing information')
    e['measurements'] = [measurement(None, 'process', 20., None, 'median', 'generic'),
                         measurement(None, 'process', 20., None, 'median', 'clean')]
    add_context(e, 'clean', excluded_activity_ids=['review'])
    model = HierarchicalModel([e], Config(max_unseen=0, population_size=32))
    z = np.ones(model.layout.size) * .25
    p = model.processes[0]
    generic = model.process_state(p, z, model.parameters(z), (0,0), True)[1]
    clean = model.process_state(p, z, model.parameters(z), (0,0), True, p.measurements[1]['route_context'])[1]
    assert generic[:, 1].any() and not generic[:, 1].all()
    assert not clean[:, 1].any()
    prediction, _ = model.predictions(z, [(0,0)])
    assert prediction[0] > prediction[1]
    for actual, expected in zip(model.predictions(z, [(0,0)], True), model.predictions_reference(z, [(0,0)], True)):
        np.testing.assert_array_equal(actual, expected)
    z[p.zg] -= .4
    for actual, expected in zip(model.predictions(z, [(0,0)], True), model.predictions_reference(z, [(0,0)], True)):
        np.testing.assert_array_equal(actual, expected)


def test_same_case_context_shared_and_conflicting_outcomes_rejected():
    import copy
    e = fixture()
    deny = copy.deepcopy(e['activities'][-1])
    deny.update(id='deny', scope='conditional', condition='denied')
    e['activities'].append(deny)
    e['measurements'] = [measurement(), measurement(None, 'process', 30., ident='total')]
    add_context(e, 'total', decision_activity_id='deny')
    model = HierarchicalModel([e], Config(max_unseen=0))
    p = model.processes[0]
    z = np.zeros(model.layout.size)
    mask = model.process_state(p, z, model.parameters(z), (0,0))[1]
    assert mask[0, p.index['deny']] and not mask[0, p.index['decide']]
    add_context(e, 'm1', decision_activity_id='decide')
    with pytest.raises(ValueError, match='mutually exclusive'):
        HierarchicalModel([e])


@pytest.mark.parametrize('channel', ['elapsed', 'agency_work'])
def test_off_route_executed_segments_are_not_zero(channel):
    import copy
    e = fixture()
    enforce = copy.deepcopy(e['activities'][1])
    enforce.update(id='enforce', stage='enforcement', scope='conditional', condition='violation')
    e['activities'].append(enforce)
    claim = measurement('enforce', 'segment', 12., None, 'median')
    claim.update(metric=channel, unit='calendar_days' if channel == 'elapsed' else 'hours')
    e['measurements'] = [claim]
    add_context(e, 'm1', segment_mode='performed_operations')
    model = HierarchicalModel([e], Config(channel=channel, max_unseen=0))
    z = np.zeros(model.layout.size)
    pred, _ = model.predictions(z, [(0,0)])
    assert np.exp(pred[0]) > 6
    p = model.processes[0]
    assert not model.process_state(p, z, model.parameters(z), (0,0), True)[1][:, p.index['enforce']].any()
    for actual, expected in zip(model.predictions(z, [(0,0)], True), model.predictions_reference(z, [(0,0)], True)):
        np.testing.assert_array_equal(actual, expected)


def test_context_quote_and_identifier_validation():
    e = fixture()
    e['measurements'] = [measurement()]
    add_context(e, 'm1', required_activity_ids=['review'])
    validate(e, [{'id': 'document', 'text': 'Evidence'}])
    e['observation_contexts'][0]['excluded_activity_ids'] = ['review']
    with pytest.raises(ValueError, match='contradictory'):
        validate(e)


def test_case_facts_cross_channels_without_turning_elapsed_days_into_work():
    import copy
    e = fixture()
    deny = copy.deepcopy(e['activities'][-1])
    deny.update(id='deny',scope='conditional',condition='denial')
    e['activities'].append(deny)
    work = measurement(value=2.,ident='work')
    work.update(metric='agency_work',unit='hours')
    e['measurements'] = [measurement(None,'process',30.,ident='elapsed_total'),work]
    add_context(e,'elapsed_total',decision_activity_id='deny')
    model = HierarchicalModel([e],Config(channel='agency_work',max_unseen=0))
    assert len(model.observations) == 1 and model.observations[0][1]['id'] == 'work'
    p = model.processes[0]
    z = np.zeros(model.layout.size)
    mask = model.process_state(p,z,model.parameters(z),(0,0))[1]
    assert mask[0,p.index['deny']] and not mask[0,p.index['decide']]


def test_after_signoff_clock_excludes_signoff_work():
    e = fixture()
    m = measurement('review', 'segment', 1., None, 'typical')
    m['activity_ids'] = ['review', 'decide']
    e['measurements'] = [m]
    add_context(e, 'm1', segment_mode='performed_operations', clock_start_after_activity_ids=['review'])
    model = HierarchicalModel([e], Config(max_unseen=0))
    p = model.processes[0]
    duration = np.array([[3., 13., 2.]])
    for graph in range(len(p.graphs)):
        values = p.segment_values(duration, np.ones_like(duration, dtype=bool), p.measurements[0], graph)
        assert values[0] == 2.
    z = np.zeros(model.layout.size)
    for a, b in zip(model.predictions(z, [(0,0)], True), model.predictions_reference(z, [(0,0)], True)):
        np.testing.assert_array_equal(a, b)


def test_historical_case_context_propagates_but_counterfactual_step_does_not():
    e = fixture()
    e['measurements'] = [measurement(), measurement(None, 'process', 30., ident='total')]
    add_context(e, 'total', temporal_scope='historical')
    assert len(HierarchicalModel([e]).observations) == 0
    e['observation_contexts'] = []
    add_context(e, 'm1', temporal_scope='hypothetical')
    assert [m['id'] for _, m in HierarchicalModel([e]).observations] == ['total']


def test_contract_requires_verbatim_support_and_actor_role():
    e = fixture()
    validate(e, [{"id": "document", "text": "Evidence"}])
    with pytest.raises(ValueError, match="verbatim"):
        validate(e, [{"id": "document", "text": "Fabricated"}])
    assert e["actors"][0]["role"] == "payer"
    validate(e, [{'id': 'document', 'text': '*Evidence*'}])


def test_missing_dependencies_cannot_make_a_root_decision():
    p = Process(fixture(), Config())
    durations = np.array([[2., 11., 3.]])
    for g in range(len(p.graphs)):
        ends = p.scheduled(durations, np.ones_like(durations, bool), g)
        assert ends[0, p.decision] >= 14  # never decision-only 3 days
    assert len(p.graphs) > 1  # unknown file/review ordering, not falsely certain


def test_skipped_step_preserves_upstream_dependencies():
    e = fixture()
    e["relations"] = [{"source": "file", "target": "review", "kind": "precedes",
                       "support": "explicit", "condition": None, "evidence": []},
                      {"source": "review", "target": "decide", "kind": "precedes",
                       "support": "explicit", "condition": None, "evidence": []}]
    p = Process(e, Config())
    ends = p.scheduled(np.array([[12., 6., 1.]]), np.array([[True, False, True]]), 0)
    assert ends[0, p.decision] == 13


def test_parallel_evidence_is_not_overridden_by_inferred_order():
    e = fixture()
    e['relations'] = [dict(source='file',target='review',kind='parallel',support='explicit',
                           condition=None,evidence=[]),
                      dict(source='file',target='review',kind='precedes',support='inferred',
                           condition=None,evidence=[])]
    p = Process(e,Config())
    for gi in range(len(p.graphs)):
        ends = p.scheduled(np.array([[12.,6.,1.]]),np.ones((1,3),dtype=bool),gi)
        assert ends[0,p.decision] == 13
    e['relations'][1]['support'] = 'explicit'
    with pytest.raises(ValueError,match='parallel relation contradicts'):
        Process(e,Config())


def test_parallel_decision_cannot_silently_skip_required_work():
    e = fixture()
    e['relations'] = [dict(source='review',target='decide',kind='parallel',support='explicit',
                           condition=None,evidence=[])]
    with pytest.raises(ValueError,match='parallel relation contradicts'):
        Process(e,Config())


def test_reduced_schedule_parents_preserve_full_edge_schedule():
    from pipeline.procbench.validate_hierarchy import generated_evidence
    e, _ = generated_evidence()
    p = Process(e, Config(max_unseen=0))
    rng = np.random.default_rng(918)
    duration = rng.lognormal(size=(100, p.n))
    mask = rng.random((100, p.n)) < .7
    for gi, graph in enumerate(p.graphs):
        full = np.zeros_like(duration)
        for i in graph['order']:
            parents = [a for a, b in graph['edges'] if b == i]
            start = full[:, parents].max(axis=1) if parents else 0.
            full[:, i] = start + duration[:, i] * mask[:, i]
        np.testing.assert_allclose(p.scheduled(duration, mask, gi), full, atol=1e-13)
        np.testing.assert_array_equal(p.scheduled(duration, mask, gi), p.scheduled_numpy(duration, mask, gi))


def test_approval_denial_are_alternative_outcomes_not_two_prerequisites():
    import copy
    e = fixture()
    other = copy.deepcopy(e['activities'][-1])
    other.update(id='deny', name='Deny the application', scope='conditional', condition='denial')
    e['activities'].append(other)
    e['measurements'] = [measurement(None, 'process', 25., ident='total')]
    m = HierarchicalModel([e], Config(max_unseen=0, population_size=32))
    z = np.ones(m.layout.size) * .5
    p = m.processes[0]
    _, mask, ends, _, _ = m.process_state(p, z, m.parameters(z), (0,0), population=True)
    assert np.all(mask[:, p.decisions].sum(axis=1) == 1)
    assert np.all(p.decision_time(ends, mask) > 0)


def test_unknown_outcome_mix_is_uncertain_but_known_case_does_not_teach_frequency():
    import copy
    e = fixture()
    other = copy.deepcopy(e['activities'][-1])
    other.update(id='deny', scope='conditional', condition='denial')
    e['activities'].append(other)
    e['measurements'] = [measurement(None,'process',25.,ident='total')]
    add_context(e,'total',decision_activity_id='deny')
    model = HierarchicalModel([e],Config(max_unseen=0,population_size=128))
    p = model.processes[0]
    z = np.zeros(model.layout.size)
    first = model.log_likelihood(z,[(0,0)])
    np.testing.assert_allclose(p.outcome_probabilities(z,model.cfg),[.5,.5])
    z[p.zo] = 2.
    probs = p.outcome_probabilities(z,model.cfg)
    assert probs[0] > .95 and probs[1] < .05
    assert model.log_likelihood(z,[(0,0)]) == first
    mask = model.process_state(p,z,model.parameters(z),(0,0),True)[1]
    assert np.mean(mask[:,p.index['decide']]) > .93
    known = model.process_state(p,z,model.parameters(z),(0,0))[1]
    assert known[0,p.index['deny']]
    for a,b in zip(model.predictions(z,[(0,0)],True),model.predictions_reference(z,[(0,0)],True)):
        np.testing.assert_array_equal(a,b)


def test_excluded_outcome_conditions_on_remaining_options_not_zero_decision():
    import copy
    e = fixture()
    deny = copy.deepcopy(e['activities'][-1])
    deny.update(id='deny',scope='conditional',condition='denial')
    e['activities'].append(deny)
    e['measurements'] = [measurement(None,'process',25.,ident='case'),
                         measurement(None,'process',25.,None,'median','pop')]
    for mid in ('case','pop'):
        add_context(e,mid,excluded_activity_ids=['deny'])
    model = HierarchicalModel([e],Config(max_unseen=0,population_size=32))
    p = model.processes[0]
    z = np.zeros(model.layout.size)
    z[p.zo] = -3  # Most prior predictive cases would choose denial without context.
    par = model.parameters(z)
    for population,context in ((False,((),(),-1)),(True,p.measurements[1]['route_context'])):
        mask = model.process_state(p,z,par,(0,0),population,context)[1]
        assert np.all(mask[:,p.index['decide']]) and not np.any(mask[:,p.index['deny']])
    e['observation_contexts'][0]['excluded_activity_ids'] = ['deny','decide']
    with pytest.raises(ValueError,match='all terminal outcomes excluded'):
        HierarchicalModel([e])


def test_submission_offset_excludes_preparation_not_payment():
    import copy
    e = fixture()
    pay = copy.deepcopy(e['activities'][0])
    pay.update(id='pay', name='Pay fee', task_type='payment')
    e['activities'].insert(1, pay)
    p = Process(e, Config())
    assert p.prepare.tolist() == [True, False, False, False]
    assert p.start_offset(np.array([[3.,5.,9.,10.]]), 'submission')[0] == 3


def test_same_case_total_and_step_share_duration_coordinates():
    e = fixture()
    e["measurements"] = [measurement(), measurement(None, "process", 25., ident="total")]
    m = HierarchicalModel([e], Config(max_unseen=0))
    z = np.ones(m.layout.size) * .25
    p = m.processes[0]
    first, _ = m.predictions(z, [(0, 0)])
    z[p.zcase[1]] += 1
    second, _ = m.predictions(z, [(0, 0)])
    assert second[0] > first[0] and second[1] > first[1]
    assert len(p.cases) == 1


def test_same_source_bias_shared_between_distinct_cases():
    e = fixture()
    e["measurements"] = [measurement(), measurement(case="c2", ident="m2")]
    m = HierarchicalModel([e], Config(max_unseen=0))
    z = np.ones(m.layout.size) * .25
    first, _ = m.predictions(z, [(0, 0)])
    z[m.zs] += 1
    second, _ = m.predictions(z, [(0, 0)])
    np.testing.assert_allclose(second - first, m.cfg.source_bias_sd)


@pytest.mark.parametrize('channel', ['elapsed', 'agency_work'])
def test_cached_predictions_match_reference_when_any_parent_changes(channel):
    import copy
    e = fixture()
    e['measurements'] = [measurement(), measurement(case='c2', ident='othercase'),
                         measurement(None, 'process', 25., ident='total')]
    for k, stat in enumerate(('mean', 'median', 'p90', 'typical')):
        meas = measurement(None, 'process', 25., None, stat, f'pop{k}')
        meas.update(n=20 if k < 3 else None, start='unspecified')
        e['measurements'].append(meas)
    for meas in e['measurements']:
        meas.update(metric=channel, unit='calendar_days' if channel == 'elapsed' else 'hours')
    other = copy.deepcopy(e)
    other['program_id'] = 'test__second'
    model = HierarchicalModel([e, other], Config(channel=channel, max_unseen=2))
    rng = np.random.default_rng(991)
    z = rng.normal(size=model.layout.size)
    structures = [(0,1), (0,2)]
    for index in range(model.layout.size):
        z[index] += rng.normal(scale=.1)
        structures[0] = (index % len(model.processes[0].graphs), index % 3)
        actual = model.predictions(z, structures, include_alternatives=True)
        expected = model.predictions_reference(z, structures, include_alternatives=True)
        for a, b in zip(actual, expected):
            np.testing.assert_allclose(a, b, rtol=1e-13, atol=1e-12)


def test_caps_not_observations_and_duplicate_totals_deduplicated():
    e = fixture()
    e["measurements"] = [measurement(statistic="statutory_cap"),
                         measurement(None, "process", 30., ident="total1"),
                         measurement(None, "process", 30., ident="total2")]
    m = HierarchicalModel([e])
    assert len(m.observations) == 1
    assert len(m.processes[0].excluded) == 2


def test_interval_units_zero_and_extreme_tails():
    m = measurement(value=2)
    m['unit'] = 'weeks'
    lo, hi = timing_interval(m)
    assert np.exp(lo) < 14 < np.exp(hi)
    m.update(value=None, lower=0, upper=1, unit='business_days')
    assert np.exp(timing_interval(m)[1]) == pytest.approx(3)
    assert np.isfinite(log_interval(10, 11, 0, .1))
    assert log_interval(10, 11, 0, .1) == pytest.approx(log_interval(-11, -10, 0, .1))
    m.update(value=24, lower=None, upper=None, unit='hours')
    lo, hi = timing_interval(m)
    assert np.exp(lo) < 1 < np.exp(hi)


def test_effort_channel_does_not_consume_elapsed_or_invent_missing_hours():
    from pipeline.procbench.bayes_effort import fit_effort
    e = fixture()
    e['measurements'] = [measurement()]
    missing, arrays = fit_effort([e], Config())
    assert missing['agency_work']['hours'] is None
    assert not arrays
    work = measurement(value=2., ident='hours')
    work.update(metric='agency_work', unit='hours')
    e['measurements'].append(work)
    m = HierarchicalModel([e], Config(channel='agency_work', global_median=.5))
    assert len(m.observations) == 1
    assert m.observations[0][1]['metric'] == 'agency_work'
    lo, hi = m.observations[0][1]['interval']
    assert np.exp(lo) < 2 < np.exp(hi)


def test_agency_effect_propagates_to_all_its_steps_not_payer():
    m = HierarchicalModel([fixture()], Config(max_unseen=0))
    z = np.ones(m.layout.size) * .5
    before = m.parameters(z)['mu']
    agency = m.agency_names.index('test:revenue')
    z[m.za[agency]] += 1
    after = m.parameters(z)['mu']
    assert after[0] == before[0]
    assert after[1] > before[1] and after[2] > before[2]


def test_finite_joint_sampler_smoke():
    e = fixture()
    e['measurements'] = [measurement(), measurement(None, 'process', 25., ident='total')]
    cfg = Config(warmup=5, draws=10, thin=1, chains=2, max_unseen=1, population_size=16)
    m = HierarchicalModel([e], cfg)
    z, s, ll, calls = m.sample()
    assert z.shape[:2] == (2, 10)
    assert np.all(np.isfinite(ll))
    assert min(calls) > 0
    report = m.report(z, s, ll)
    assert report['programs']['test__permit']['model']['process_timing']['median_days'] > 0
    assert report['agencies'][0]['work_hours'] is None


def test_configuration_is_validated_and_not_mutated_under_prediction_cache():
    from dataclasses import FrozenInstanceError
    with pytest.raises(ValueError, match='eight'):
        Config(draws=2)
    with pytest.raises(ValueError, match='contamination'):
        Config(outlier_probability=1.)
    cfg = Config()
    with pytest.raises(FrozenInstanceError):
        cfg.report_sd = 99


def test_saved_chain_can_continue_without_reinitializing_parameters():
    e = fixture()
    e['measurements'] = [measurement()]
    m = HierarchicalModel([e], Config(chains=2, draws=8, warmup=0, thin=1, max_unseen=0))
    z, s, _, _ = m.sample()
    initial = z[:, -1], s[:, -1]
    a, structure, ll, _ = m.sample(initial=initial)
    b, _, _, _ = m.sample(initial=initial)
    np.testing.assert_allclose(a, b)  # deterministic replay of a continuation seed
    assert np.all(np.isfinite(ll)) and structure.shape == (2, 8, 1, 2)


def test_attribution_and_scale_updates_preserve_all_predictions():
    e = fixture()
    e['measurements'] = [measurement(), measurement(None, 'process', 25., ident='total'),
                         measurement(None, 'process', 25., None, 'median', 'population')]
    m = HierarchicalModel([e], Config(max_unseen=2))
    rng = np.random.default_rng(87)
    z = rng.normal(size=m.layout.size)
    initial, _ = m.predictions(z, [(0, 1)])
    for _ in range(30):
        z = m.decomposition_update(z, rng)
        z = m.centered_scale_update(z, rng)
        actual, _ = m.predictions(z, [(0, 1)])
        np.testing.assert_allclose(initial, actual, atol=1e-10)


def test_source_location_move_preserves_report_predictions_and_joint_prior():
    e = fixture()
    e['measurements'] = [measurement(), measurement(None, 'process', 25., ident='total'),
                         measurement(None, 'process', 25., None, 'median', 'population')]
    m = HierarchicalModel([e], Config(max_unseen=1))
    rng = np.random.default_rng(841)
    z = rng.normal(size=m.layout.size)
    s = [(0,1)]
    before, _ = m.predictions(z, s)
    value = m.log_likelihood(z, s)
    for _ in range(30):
        z, value = m.source_location_update(z, s, value, rng)
        after, _ = m.predictions(z, s)
        np.testing.assert_allclose(after, before, atol=1e-10)
    # For a prior-distributed starting point, the Gaussian projection refresh
    # must remain prior-distributed, even though it rotates multiple coordinates.
    original = m.log_likelihood
    m.log_likelihood = lambda *args, **kwargs: 0.
    output = []
    for _ in range(2000):
        x = rng.normal(size=m.layout.size)
        x, _ = m.source_location_update(x, s, 0., rng)
        output.append(x[np.r_[m.hyper[0], m.zs]])
    output = np.asarray(output)
    assert np.max(np.abs(output.mean(axis=0))) < .08
    np.testing.assert_allclose(np.cov(output.T), np.eye(output.shape[1]), atol=.10)
    m.log_likelihood = original


def test_interwoven_sampler_preserves_joint_prior_without_evidence():
    cfg = Config(warmup=100, draws=1500, thin=1, chains=2, max_unseen=1, population_size=16)
    m = HierarchicalModel([fixture()], cfg)
    z, _, _, _ = m.sample()
    flat = z.reshape((-1, z.shape[-1]))
    assert np.max(np.abs(flat.mean(axis=0))) < .12
    assert np.max(np.abs(flat.var(axis=0) - 1)) < .18


@pytest.mark.parametrize('options', [{}, {'match_case_means': True}, {'case_id': 0}])
@pytest.mark.parametrize('pair', [(0,1), (2,3)])
def test_duration_redistribution_is_reversible_and_preserves_case_sum(options, pair):
    e = fixture()
    e['measurements'] = [measurement(None, 'process', 25., ident='total')]
    m = HierarchicalModel([e], Config(max_unseen=1))
    rng = np.random.default_rng(142)
    z = rng.normal(size=m.layout.size)
    p = m.processes[0]
    moved = m.redistribute_pair(z, p, *pair, .9, **options)
    restored = m.redistribute_pair(moved, p, *pair, -.9, **options)
    np.testing.assert_allclose(z, restored, atol=1e-12)
    before = m.process_state(p, z, m.parameters(z), (0, 0))[0]
    after = m.process_state(p, moved, m.parameters(moved), (0, 0))[0]
    np.testing.assert_allclose(before.sum(axis=1), after.sum(axis=1))
    # MH uses the standard-Normal density ratio only: verify the promised
    # volume preservation in the actual unconstrained sampler coordinates.
    eps = 1e-5
    eye = np.eye(len(z)) * eps
    jac = np.column_stack([(m.redistribute_pair(z + v, p, *pair, .9, **options)
                            - m.redistribute_pair(z - v, p, *pair, .9, **options)) / (2 * eps) for v in eye])
    assert np.linalg.slogdet(jac)[1] == pytest.approx(0., abs=1e-7)


def test_process_staff_hours_do_not_include_payer_work():
    e = fixture()
    total = measurement(None, 'process', 2., None, 'estimate', 'staff')
    total.update(metric='agency_work', unit='hours')
    e['measurements'] = [total]
    m = HierarchicalModel([e], Config(channel='agency_work', max_unseen=0))
    z = np.ones(m.layout.size) * .5
    before, _ = m.predictions(z, [(0, 0)])
    z[m.zi[0]] += 3  # applicant filing work, not agency work
    after, _ = m.predictions(z, [(0, 0)])
    np.testing.assert_allclose(before, after)
    assert m.processes[0].active.tolist() == [False, True, True]


def test_conditional_withdrawal_not_added_to_every_completed_case():
    import copy
    e = fixture()
    a = copy.deepcopy(e['activities'][0])
    a.update(id='withdraw', name='Withdraw', stage='closeout', scope='conditional', task_type='other')
    e['activities'].append(a)
    total = measurement(None, 'process', 30., None, 'median', 'closeout')
    total['end'] = 'closeout'
    e['measurements'] = [total]
    m = HierarchicalModel([e], Config(max_unseen=0))
    z = np.ones(m.layout.size) * .5
    before, _ = m.predictions(z, [(0, 0)])
    z[m.zi[-1]] += 3
    after, _ = m.predictions(z, [(0, 0)])
    np.testing.assert_allclose(before, after)
    assert not m.processes[0].active[-1]


def test_bad_metric_units_and_nonfinite_numbers_fail_contract():
    e = fixture()
    e['measurements'] = [measurement()]
    e['measurements'][0]['unit'] = 'USD'
    with pytest.raises(ValueError, match='metric/unit'):
        validate(e)
    e['measurements'][0].update(unit='calendar_days', value=float('nan'))
    with pytest.raises(ValueError, match='non-finite'):
        validate(e)


def test_posterior_timing_score_is_proper_and_not_width_only():
    from pipeline.procbench.run_hierarchical import posterior_timing_score
    exact = posterior_timing_score([10.] * 50, 10.)
    wide = posterior_timing_score([1., 10., 100.], 10.)
    wrong = posterior_timing_score([2.] * 50, 10.)
    assert exact['crps_log_median'] == pytest.approx(0.)
    assert wide['crps_log_median'] > 0
    assert wrong['crps_log_median'] > wide['crps_log_median']
    assert wide['interval_score90_log_median'] > exact['interval_score90_log_median']


def test_importance_helpers_normalize_count_prior_and_empty_weights():
    from pipeline.procbench.sensitivity_hierarchy import count_log_mass, weighted_quantiles
    assert np.exp(count_log_mass(np.arange(9), 2., 8)).sum() == pytest.approx(1.)
    assert np.exp(count_log_mass(np.arange(9), 0., 8)).tolist() == [1.] + [0.] * 8
    assert weighted_quantiles([1,2,3], np.ones(3), [.5]) == [2.]
    assert weighted_quantiles([1,2,3], np.zeros(3)) == [None, None, None]


def test_granularity_mapping_preserves_measurements_and_responsible_actors():
    from pipeline.procbench.audit_granularity import apply_groups
    import copy
    e = fixture()
    e['measurements'] = [measurement()]
    groups = [{k: a[k] for k in ('id','name','actor_id','task_type','stage','scope','condition')} |
              {'members': [a['id']], 'rationale': 'same operation'} for a in e['activities']]
    grouping = {'groups': groups, 'attributes': [], 'unresolved': []}
    canonical, audit = apply_groups(e, grouping)
    assert canonical['measurements'] == e['measurements']
    bad = copy.deepcopy(grouping)
    bad['groups'].pop(1)
    bad['attributes'] = [{'member': 'review', 'owner': None, 'kind': 'out_of_scope', 'rationale': 'bad'}]
    with pytest.raises(ValueError, match='realized timing'):
        apply_groups(e, bad)
    bad['attributes'][0].update(owner='file', kind='requirement')
    with pytest.raises(ValueError, match='different actor'):
        apply_groups(e, bad)
