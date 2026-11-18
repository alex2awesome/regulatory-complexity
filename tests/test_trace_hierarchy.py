import copy
from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy,count_log_probability,repeat_quantiles
from pipeline.procbench.rework_counts import ReworkLaw
from procbench_fixtures import data_fixture, observation


def test_report_progress_does_not_change_scientific_outputs_or_inputs():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    states=np.random.default_rng(210).normal(0,.02,(4,8,model.layout.size))
    routes=np.zeros((4,8,1),dtype=int)
    likelihood=np.array([model.log_likelihood(z,r) for z,r in
        zip(states.reshape(-1,model.layout.size),routes.reshape(-1,1))]).reshape(4,8)
    before=states.copy()
    ordinary=model.report(states,routes,likelihood)
    events=[]
    traced=model.report(states,routes,likelihood,progress=events.append)
    assert ordinary == traced
    np.testing.assert_array_equal(states,before)
    assert events[0]['stage']=='posterior_coordinate_diagnostics'
    assert events[-1]['stage']=='posterior_report_complete'
    assert [e['completed_draws'] for e in events if e['stage']=='posterior_predictions']==[0,1,32]
    assert all(e['total_draws']==32 for e in events)


def test_fit_progress_log_preserves_events_and_refuses_existing_file(tmp_path):
    import json
    from pipeline.procbench.run_visit_hierarchy import make_progress_logger
    progress=make_progress_logger(tmp_path)
    progress(dict(stage='sampling'))
    progress(dict(stage='posterior_predictions',completed_draws=1,total_draws=32))
    rows=[json.loads(line) for line in (tmp_path/'run_progress.jsonl').read_text().splitlines()]
    assert [r['stage'] for r in rows]==['sampling','posterior_predictions']
    assert 0 <= rows[0]['elapsed_seconds'] <= rows[1]['elapsed_seconds']
    assert rows[1]['completed_draws']==1 and rows[1]['total_draws']==32
    with pytest.raises(FileExistsError):
        make_progress_logger(tmp_path)


def test_clock_support_reports_missing_markers_without_changing_likelihood():
    data = data_fixture()
    row = data['programs'][0]['observations'][0]
    row['operators'] = [dict(basis='whole_case_clock', start='first_complete_submission',
                             end='initial_decision'),
                        dict(basis='unmodeled_duration', median_days=30., log_scale=2.)]
    row['operator_weights'] = [.8, .2]
    model = VisitHierarchy(data, Config(population_size=16))
    z = np.zeros(model.layout.size)
    before = model.log_likelihood(z, [0])
    report = model.clock_support_report()
    assert report['affected_observations'] == ['J__P:total']
    assert report['unsupported_clock_alternatives_by_inventory'] == 1
    assert report['alternatives'][0]['path_checks'] == [
        dict(path_id='simple', missing_events=['first_complete_submission'])]
    assert report['alternatives'][0]['declared_operator_weight'] == .8
    assert report['inference_changed'] is False
    assert np.isfinite(before)
    assert model.log_likelihood(z, [0]) == before
    assert row['operator_weights'] == [.8, .2]


@pytest.mark.parametrize('case,scope,expected', [
    ('c', None, True), ('c', ['no_submission'], False),
    (None, None, False), (None, ['with_submission'], True)])
def test_clock_support_respects_case_and_population_scopes(case, scope, expected):
    data = data_fixture()
    p = data['programs'][0]
    r = p['routes'][0]
    r['paths'] = [dict(id='with_submission', probability_weight=1., blocks=r.pop('blocks')),
                  dict(id='no_submission', probability_weight=1.,
                       blocks=[dict(id='end', operations=['review', 'decide'])])]
    row = observation('submission_clock', 'whole_case_clock', 2., 10., case=case)
    row['operators'][0]['start'] = 'first_submission'
    row['operators'].append(dict(basis='unmodeled_duration', median_days=30., log_scale=2.))
    row['operator_weights'] = [.8, .2]
    p['observations'] = [row]
    if scope is not None:
        if case is None:
            row['population_path_scope'] = scope
        else:
            p['case_path_scope'] = {case: scope}
    report = VisitHierarchy(data, Config(population_size=16)).clock_support_report()
    assert report['alternatives'][0]['event_presence_requirement_satisfied'] is expected


def test_clock_support_decision_alias_is_only_asserted_for_one_nonrepeated_event():
    data = data_fixture()
    cfg = Config(population_size=16)
    assert VisitHierarchy(data, cfg).clock_support_report()['paths'][0][
        'initial_final_guaranteed_same_event'] is True
    # A single operation can still have multiple decision events if it repeats.
    data['programs'][0]['routes'][0]['blocks'][1]['repeat_key'] = 'appeals'
    assert VisitHierarchy(data, cfg).clock_support_report()['paths'][0][
        'initial_final_guaranteed_same_event'] is False
    # Missing markers are not inferred from a task type or operation ID.
    data['programs'][0]['routes'][0]['operations'][-1]['markers'] = []
    row = VisitHierarchy(data, cfg).clock_support_report()['paths'][0]
    assert row['initial_final_guaranteed_same_event'] is False
    assert 'initial_decision' in row['absent_events']


def project_active_channels(full, reduced, z):
    """Same retained prior/case variables, not a new draw or fitted-prior shortcut."""
    projected = np.zeros(reduced.layout.size)
    for name in ('location', 'agency', 'task', 'operation', 'sigma', 'source'):
        old, new = getattr(full, name), getattr(reduced, name)
        mask = new >= 0
        projected[new[mask]] = z[old[mask]]
    if full.phase_coordinates is not None:
        projected[reduced.phase_coordinates] = z[full.phase_coordinates]
    for pf, pr in zip(full.programs, reduced.programs):
        n = len(pf['global_indices'])
        columns = [i for ch in reduced.active_channels for i in range(ch*(n+1), (ch+1)*(n+1))]
        columns += list(range(pf['noise_dimension'], pf['case_dimension']))
        projected[pr['case_coordinates']] = z[pf['case_coordinates'][:, columns]]
        projected[pr['repeat']] = z[pf['repeat']]
        projected[pr['selection']] = z[pf['selection']]
        # A dimension change changes the production Sobol grid. Here align it
        # explicitly to test equality of the mathematical likelihood/operator.
        pr['population_normals'] = pf['population_normals'][:, columns].copy()
    return projected


@pytest.mark.parametrize('channels', [(), ('payer_hours',), ('elapsed', 'unknown'),
                                    ('elapsed', 'elapsed'), ('elapsed', 'agency_hours', 'payer_hours')])
def test_invalid_modeled_channel_declarations_fail(channels):
    with pytest.raises(ValueError, match='Modeled channels'):
        Config(modeled_channels=channels)


@pytest.mark.parametrize('channels', [('elapsed',), ('elapsed', 'agency_hours')])
@pytest.mark.parametrize('phases', [False, True])
def test_omitting_unobserved_channels_preserves_retained_likelihood(channels, phases):
    data = data_fixture()
    if 'agency_hours' not in channels:
        data['programs'][0]['observations'] = [o for o in data['programs'][0]['observations']
            if all(op['basis'] != 'agency_hours' for op in o['operators'])]
    data['programs'][0]['observations'].append(observation('population', 'whole_case_clock', 5., 40., case=None))
    cfg = Config(population_size=16, within_visit_phases=phases)
    full = VisitHierarchy(data, cfg)
    reduced = VisitHierarchy(data, replace(cfg, modeled_channels=channels))
    rng = np.random.default_rng(8432)
    for _ in range(8):
        z = rng.normal(size=full.layout.size)
        zr = project_active_channels(full, reduced, z)
        assert reduced.log_likelihood(zr, [0]) == pytest.approx(full.log_likelihood(z, [0]), abs=1e-10)
        assert reduced.log_likelihood_reference(zr, [0]) == pytest.approx(full.log_likelihood(z, [0]), abs=1e-10)
        original = full.trace(full.programs[0], z, full.parameters(z), 0)
        current = reduced.trace(reduced.programs[0], zr, reduced.parameters(zr), 0)
        np.testing.assert_allclose(original.durations, current.durations, rtol=1e-13)
    assert reduced.layout.size < full.layout.size
    assert all(np.all(block >= 0) for block in reduced.blocks)


def test_omitted_labor_is_unknown_not_zero_or_a_reported_posterior():
    data = data_fixture()
    data['programs'][0]['observations'] = [data['programs'][0]['observations'][0]]
    cfg = Config(chains=1, warmup=1, draws=8, population_size=16, modeled_channels=('elapsed',))
    model = VisitHierarchy(data, cfg)
    full = VisitHierarchy(data, replace(cfg, modeled_channels=('elapsed', 'payer_hours', 'agency_hours')))
    assert model.layout.size < .4*full.layout.size
    z = np.zeros(model.layout.size)
    trace = model.trace(model.programs[0], z, model.parameters(z), 0)
    assert np.isnan(trace.resources['payer_hours']).all()
    assert np.isnan(trace.resources['agency_hours']).all()
    states, routes, likelihood, _ = model.sample()
    report = model.report(states, routes, likelihood)
    program = report['programs']['J__P']
    assert program['omitted_resource_channels'] == ['payer_hours', 'agency_hours']
    assert 'mean_payer_hours' not in program['metrics']
    assert 'mean_agency_hours' not in program['metrics']
    assert 'agency:elapsed' in report['identification']['blocks']
    assert 'agency:agency_hours' not in report['identification']['blocks']
    assert not report['posterior_converged']  # mechanics-only fixture
    from pipeline.procbench.run_visit_hierarchy import preflight_report
    preflight = preflight_report(model)
    assert preflight['modeled_channels'] == ['elapsed']
    assert preflight['omitted_resource_channels'] == ['payer_hours', 'agency_hours']


def test_cannot_prune_a_resource_channel_that_has_observations():
    with pytest.raises(ValueError, match='Cannot omit'):
        VisitHierarchy(data_fixture(), Config(modeled_channels=('elapsed',)))


def test_saved_config_channel_list_round_trips():
    assert Config(modeled_channels=['elapsed', 'agency_hours']).modeled_channels == ('elapsed', 'agency_hours')


def route_missing_measured_review(route):
    result = copy.deepcopy(route)
    result['id'] = 'missing_measured_review'
    result['operations'] = [op for op in result['operations'] if op['id'] != 'review']
    result['blocks'] = [dict(block, operations=[a for a in block['operations'] if a != 'review'], edges=None)
        for block in result['blocks'] if any(a != 'review' for a in block['operations'])]
    return result


@pytest.mark.parametrize('seed', [0, 1, 2, 3])
def test_fresh_chain_finds_supported_route_instead_of_failing_on_random_bad_start(seed):
    data = data_fixture()
    data['programs'][0]['routes'].append(route_missing_measured_review(data['programs'][0]['routes'][0]))
    model = VisitHierarchy(data, Config(seed=seed, chains=1, warmup=0, draws=8, population_size=16))
    states, routes, likelihood, _ = model.sample()
    assert np.isfinite(likelihood).all()
    assert np.all(routes == 0)
    assert np.isfinite(states).all()


def test_route_initialization_factors_programs_even_when_ids_have_shared_prefixes():
    data = data_fixture()
    other = copy.deepcopy(data['programs'][0])
    other['id'] += ':child'
    data['programs'].append(other)
    for p in data['programs']:
        p['routes'].append(route_missing_measured_review(p['routes'][0]))
    model = VisitHierarchy(data, Config(population_size=16))
    z = np.zeros(model.layout.size)
    result, routes, value = model._finite_initial_routes(z, np.array([1, 1]), np.random.default_rng(42))
    assert np.array_equal(result, z)
    assert np.array_equal(routes, [0, 0])
    assert value == model.log_likelihood(z, [0, 0])
    assert value == pytest.approx(sum(model.log_likelihood(z, [0, 0], _program_index=i) for i in range(2)))


def test_impossible_evidence_is_not_silently_dropped_to_start_sampler():
    data = data_fixture()
    data['programs'][0]['routes'] = [route_missing_measured_review(data['programs'][0]['routes'][0])]
    model = VisitHierarchy(data, Config(chains=1, warmup=0, draws=8, population_size=16))
    with pytest.raises(ValueError, match='No finite initial state.*J__P'):
        model.sample()


def test_unsupported_saved_checkpoint_is_not_reinitialized():
    data = data_fixture()
    data['programs'][0]['routes'].append(route_missing_measured_review(data['programs'][0]['routes'][0]))
    model = VisitHierarchy(data, Config(chains=1, warmup=0, draws=8, population_size=16))
    with pytest.raises(ValueError, match='Checkpoint latent route'):
        model.sample(initial=(np.zeros((1, model.layout.size)), np.array([[1]])))


def test_discrete_reporting_error_is_normalized_including_zero_counts():
    for center in (0,1,5,50):
        mass=sum(np.exp(count_log_probability(k,k,center)) for k in range(300))
        assert mass==pytest.approx(1.,abs=1e-12)
        assert count_log_probability(0,None,center)==pytest.approx(0.,abs=1e-12)


def test_vector_repeat_quantiles_match_normalized_unbounded_reference():
    u=np.linspace(0,.999999,999)
    for q in (0.,.25,1.):
        for r in (0.,.35,.99):
            np.testing.assert_array_equal(repeat_quantiles(u,q,r),[ReworkLaw(q,r).quantile(float(x)) for x in u])


def test_total_cycle_count_and_work_use_one_shared_case_trace():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    first=model.trace(p,z,model.parameters(z),0)
    before=model.log_likelihood(z,[0],parts=True)
    z[p['repeat'][0,0]]=1.5  # same latent case now has additional visits
    after_trace=model.trace(p,z,model.parameters(z),0)
    after=model.log_likelihood(z,[0],parts=True)
    assert after_trace.event('initial_decision')[0]>first.event('initial_decision')[0]
    assert after['J__P:task']==before['J__P:task']  # first-visit duration is NOT cycle sum
    assert after['J__P:total']!=before['J__P:total']
    assert after['J__P:visits']!=before['J__P:visits']
    assert after['J__P:labor']!=before['J__P:labor']


def test_agency_effect_propagates_across_programs_without_converting_days_to_hours():
    data=data_fixture()
    second=copy.deepcopy(data['programs'][0])
    second['id']='J__Q'
    data['programs'].append(second)
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    initial=model.log_likelihood(z,[0,0],parts=True)
    z[model.agency[0,model.agencies.index('J:Review')]]=1.
    changed=model.log_likelihood(z,[0,0],parts=True)
    for pid in ('J__P','J__Q'):
        assert initial[pid+':task']!=changed[pid+':task']
        assert initial[pid+':total']!=changed[pid+':total']
        assert initial[pid+':labor']==changed[pid+':labor']


def test_independent_count_cohort_is_not_an_informal_frequency():
    data=data_fixture()
    rate=dict(repeat_key='corrections',event='any_correction_per_case',successes=6,trials=10,
              cohort_scope='completed_cases_for_repeat_block',independent_cohort=False)
    data['programs'][0]['rate_observations']=[rate]
    with pytest.raises(ValueError,match='real counted'):
        VisitHierarchy(data)
    rate['independent_cohort']=True
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    parts=model.log_likelihood(z,[0],parts=True)
    assert parts['J__P:cohort:0']==pytest.approx(10*np.log(.5))
    rate['cohort_scope']='received_cases_by_observation'
    with pytest.raises(ValueError,match='observed-by-date'):
        VisitHierarchy(data)


def test_interpretation_prior_marginalizes_likelihood_not_predicted_durations():
    data=data_fixture()
    o=data['programs'][0]['observations'][1]
    o['operators'].append(dict(basis='sum_visit_cycles',activity_ids=['review']))
    o['operator_weights']=[.3,.7]
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    z[model.programs[0]['repeat'][0,0]]=1.
    mixed=model.log_likelihood(z,[0],parts=True)['J__P:task']
    values=[]
    for op in o['operators']:
        d=copy.deepcopy(data)
        d['programs'][0]['observations'][1].update(operators=[op],operator_weights=[1.])
        m=VisitHierarchy(d,Config(population_size=16))
        values.append(m.log_likelihood(z,[0],parts=True)['J__P:task'])
    assert mixed==pytest.approx(np.log(.3*np.exp(values[0])+.7*np.exp(values[1])))


def test_source_bias_changes_likelihood_without_changing_latent_trace():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    first=model.trace(p,z,model.parameters(z),0)
    ll=model.log_likelihood(z,[0])
    z[model.source[0,0]]=2
    assert model.trace(p,z,model.parameters(z),0) is first
    assert model.log_likelihood(z,[0])!=ll


def test_centered_update_preserves_realized_durations_not_population_parameters():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    z=np.random.default_rng(64).normal(size=model.layout.size)
    p=model.programs[0]
    par=model.parameters(z)
    initial=model.trace(p,z,par,0)
    current=model.log_likelihood(z,[0])
    changed,value=model.centered_duration_update(z,[0],current,np.random.default_rng(33))
    after=model.trace(p,changed,model.parameters(changed),0)
    assert value==pytest.approx(current,abs=1e-8)
    np.testing.assert_allclose(initial.durations,after.durations,rtol=1e-12)
    np.testing.assert_allclose(initial.resources['agency_hours'],after.resources['agency_hours'],rtol=1e-12)
    assert not np.allclose(par['mu'],model.parameters(changed)['mu'])


def test_centered_update_matches_known_gaussian_conditional_moments():
    cfg=Config(agency_sd=0.,task_sd=0.,operation_sd=0.,common_case_sd=0.,case_log_sd_prior=0.,population_size=16)
    model=VisitHierarchy(data_fixture(),cfg)
    z=np.full(model.layout.size,.2)
    current=model.log_likelihood(z,[0])
    rng=np.random.default_rng(8734)
    draws=[model.centered_duration_update(z,[0],current,rng)[0][model.location[0]] for _ in range(400)]
    n=3
    eta=cfg.location_sd*.2+cfg.case_log_sd_median*.2
    precision=1+n*cfg.location_sd**2/cfg.case_log_sd_median**2
    mean=n*cfg.location_sd*eta/cfg.case_log_sd_median**2/precision
    assert np.mean(draws)==pytest.approx(mean,abs=.035)
    assert np.var(draws)==pytest.approx(1/precision,rel=.2)


def test_source_location_conditional_preserves_likelihood():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    z=np.random.default_rng(6).normal(size=model.layout.size)
    ll=model.log_likelihood(z,[0])
    moved,updated=model.source_location_update(z,[0],ll,np.random.default_rng(7))
    assert updated==pytest.approx(ll,abs=1e-9)
    assert not np.allclose(z,moved)


def test_population_count_resource_means_do_not_depend_on_quadrature_size():
    data=data_fixture()
    cfg=Config(population_size=16)
    model=VisitHierarchy(data,cfg)
    finer=VisitHierarchy(data,replace(cfg,population_size=1024))
    z=np.random.default_rng(88).normal(size=model.layout.size)
    a=model.expected_burden(model.programs[0],z,model.parameters(z),0)
    b=finer.expected_burden(finer.programs[0],z,finer.parameters(z),0)
    assert a==b
    q,r=model.repeat_parameters(model.programs[0],z)
    assert a['mean_visit_count']==pytest.approx(3+2*q[0]/(1-r[0]))


def test_disconnected_agency_task_design_is_flagged_even_with_many_documents():
    data=data_fixture()
    other=copy.deepcopy(data['programs'][0])
    other['id']='K__Q'
    for op in other['routes'][0]['operations']:
        if op['actor_role']=='agency':
            op['actor_id']='K:Other'
            op['task_type']='different_'+op['task_type']
    data['programs'].append(other)
    model=VisitHierarchy(data,Config(population_size=16))
    assert model.hierarchy_design_audit()['prior_dependent_contrasts']==[['J:Review','K:Other']]
    # A genuinely shared task type supplies the missing cross-agency comparison.
    other['routes'][0]['operations'][1]['task_type']='review'
    model=VisitHierarchy(data,Config(population_size=16))
    assert not model.hierarchy_design_audit()['prior_dependent_contrasts']


def test_population_only_input_has_no_invented_individual_case():
    data=data_fixture()
    data['programs'][0]['observations']=[observation('median','whole_case_clock',15.,30.,case=None)]
    model=VisitHierarchy(data,Config(population_size=16))
    assert model.programs[0]['case_coordinates'].shape[0]==0
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))


def test_joint_sampler_smoke_is_reproducible_not_a_convergence_certificate():
    cfg=Config(chains=1,warmup=1,draws=8,population_size=16)
    model=VisitHierarchy(data_fixture(),cfg)
    a=model.sample()
    b=VisitHierarchy(data_fixture(),cfg).sample()
    for x,y in zip(a[:3],b[:3]):
        np.testing.assert_array_equal(x,y)
    report=model.report(*a[:3])
    assert not report['posterior_converged']
    assert report['programs']['J__P']['metrics']['mean_agency_hours']['median']>0
    continued=VisitHierarchy(data_fixture(),replace(cfg,warmup=0,seed=cfg.seed+99))
    z,s,ll,_=continued.sample(initial=(a[0][:,-1,:],a[1][:,-1,:]))
    np.testing.assert_allclose(ll[0],[continued.log_likelihood(zz,ss) for zz,ss in zip(z[0],s[0])],atol=1e-10)
    with pytest.raises(ValueError,match='Checkpoint'):
        continued.sample(initial=(a[0][:,-1,:],np.array([[3]])))


def test_clock_count_and_cohort_contract_errors_fail_fast():
    data=data_fixture()
    data['programs'][0]['observations'][1]['sampling']='delay_selected'
    with pytest.raises(ValueError,match='Same-case'):
        VisitHierarchy(data)
    data=data_fixture()
    data['programs'][0]['observations'][0]['operator_weights']=[2.]
    with pytest.raises(ValueError,match='sum to one'):
        VisitHierarchy(data)


def test_batched_likelihood_matches_reference_with_mixtures_and_cache_changes():
    data=data_fixture()
    alternate=copy.deepcopy(data['programs'][0]['routes'][0])
    alternate['id']='parallel'
    alternate['blocks'][0]['edges']=[]
    data['programs'][0]['routes'].append(alternate)
    o=data['programs'][0]['observations'][1]
    o['operators'].append(dict(basis='sum_visit_cycles',activity_ids=['review']))
    o['operator_weights']=[.3,.7]
    data['programs'][0]['observations'].append(observation('population','whole_case_clock',5.,40.,case=None))
    data['programs'][0]['observations'][0]['upper']=None  # right-censoring interval
    model=VisitHierarchy(data,Config(population_size=16))
    rng=np.random.default_rng(8114)
    for _ in range(60):
        z=rng.normal(size=model.layout.size)
        route=[int(rng.integers(2))]
        actual=model.log_likelihood(z,route,parts=True)
        expected=model.log_likelihood_reference(z,route,parts=True)
        assert actual.keys()==expected.keys()
        np.testing.assert_allclose(list(actual.values()),list(expected.values()),atol=1e-10,rtol=1e-10)


def test_batched_count_likelihood_matches_scalar_calls():
    lo=np.array([0,0,1,4,3])
    hi=np.array([0,2,5,np.inf,2])
    center=np.array([0,4,2,9,3])
    actual=count_log_probability(lo,hi,center)
    expected=[count_log_probability(a,b,c) for a,b,c in zip(lo,hi,center)]
    np.testing.assert_allclose(actual,expected,atol=1e-13)
