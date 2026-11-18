"""Per-case paths inside V6 inventory hypotheses; source-free mechanics fixtures."""
import copy
from dataclasses import replace

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.bayes_trace_hierarchy import (Config, VisitHierarchy,
    duration_log_probability, duration_report_log_probability)
from pipeline.procbench.compact_visit_trace import (Block, CompactTrace, Operation,
    UnavailableTraceQuantity, observation_population, population_statistic, validate_operator)
from procbench_fixtures import observation


def path_data():
    operations = [
        dict(id='file', actor_id='payer', actor_role='payer', task_type='filing',
             markers=['submission'], payer_work=True, agency_work=False),
        dict(id='review', actor_id='J:Review', actor_role='agency', task_type='review',
             payer_work=False, agency_work=True),
        dict(id='approve', actor_id='J:Review', actor_role='agency', task_type='decision',
             markers=['decision'], payer_work=False, agency_work=True),
        dict(id='deny', actor_id='J:Review', actor_role='agency', task_type='decision',
             markers=['decision'], payer_work=False, agency_work=True),
    ]
    return dict(programs=[dict(id='J__P', routes=[dict(id='inventory', prior_weight=1.,
        operations=operations, paths=[
            dict(id='approved', probability_weight=3., blocks=[dict(id='a', operations=['file','review','approve'])]),
            dict(id='denied', probability_weight=1., blocks=[dict(id='d', operations=['file','deny'])]),
        ])], observations=[
            observation('approval', 'single_visit_cycle', 4., 10., case='a', activities=['approve']),
            observation('denial', 'single_visit_cycle', 1., 6., case='b', activities=['deny']),
        ], case_path_scope={'a':['approved'], 'b':['denied']})])


def cfg(**kwargs):
    return Config(population_size=16, modeled_channels=('elapsed',), **kwargs)


def test_opposite_outcomes_in_two_cases_do_not_require_one_global_route():
    model=VisitHierarchy(path_data(),cfg())
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    p=model.programs[0]
    with pytest.raises(ValueError,match='marginalized jointly'):
        model.trace(p,z,model.parameters(z),0)
    assert len(model.operations)==4  # shared filing is one hierarchical operation
    assert model.expected_burden(p,z,model.parameters(z),0)['mean_operation_count']==pytest.approx(2.75)


def test_known_outcome_labels_do_not_become_prevalence_counts():
    model=VisitHierarchy(path_data(),cfg())
    z=np.zeros(model.layout.size)
    initial=model.log_likelihood(z,[0])
    z[model.programs[0]['routes'][0]['path_coordinates']]=2.5
    assert model.log_likelihood(z,[0])==pytest.approx(initial,abs=1e-12)
    # Actual population burden still depends on the declared/learned path mix.
    assert model.expected_burden(model.programs[0],z,model.parameters(z),0)['mean_operation_count']!=pytest.approx(2.75)


def test_same_case_reports_are_marginalized_jointly_not_one_path_per_report():
    data=path_data()
    p=data['programs'][0]
    p['case_path_scope']={}
    p['observations'][1]['case_id']='a'
    model=VisitHierarchy(data,cfg())
    z=np.zeros(model.layout.size)
    # Approval and denial are mutually exclusive on every candidate case path.
    assert model.log_likelihood(z,[0])==-np.inf


def test_unconditioned_joint_case_likelihood_matches_explicit_enumeration():
    data=path_data()
    p=data['programs'][0]
    p['case_path_scope']={}
    # Both reports must depend on the branch; shared filing time alone factors
    # out of the path sum and would not distinguish joint from separate mixtures.
    p['observations']=[observation('count','operation_count',3,3),
                       observation('total','whole_case_clock',10.,30.)]
    model=VisitHierarchy(data,cfg())
    z=np.random.default_rng(42).normal(size=model.layout.size)
    program=model.programs[0]
    par=model.parameters(z)
    likelihoods=[]
    for j in range(2):
        trace=model.trace(program,z,par,0,path_index=j)
        parts=model._observation_parts(program,trace,None,par)
        likelihoods.append(sum(parts.values()))
    probabilities=model.path_probabilities(program['routes'][0],z)
    expected=logsumexp(np.log(probabilities)+likelihoods)
    assert model.log_likelihood(z,[0])==pytest.approx(expected,abs=1e-12)
    incorrectly_independent=sum(logsumexp(np.log(probabilities)+[
        model._observation_parts(program,model.trace(program,z,par,0,path_index=j),None,par)[key]
        for j in range(2)]) for key in parts)
    assert expected!=pytest.approx(incorrectly_independent,abs=1e-6)


@pytest.mark.parametrize('selection',[0.,1.])
def test_vectorized_and_scalar_path_reporting_agree(selection):
    data=path_data()
    if selection:
        for o in data['programs'][0]['observations']:
            o['sampling']='delay_selected'
    data['programs'][0]['observations'].append(observation('population','whole_case_clock',8.,40.,case=None))
    model=VisitHierarchy(data,cfg(selection_sd=selection))
    rng=np.random.default_rng(72)
    for _ in range(12):
        z=rng.normal(size=model.layout.size)
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-10)


def test_population_summary_uses_path_weights_and_explicit_scope():
    data=path_data()
    p=data['programs'][0]
    p['observations']=[observation('population','whole_case_clock',8.,40.,case=None)]
    p['case_path_scope']={}
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    z=np.zeros(model.layout.size)
    program=model.programs[0]
    trace=model.trace(program,z,model.parameters(z),0,True)
    values=trace.event('initial_decision')
    individual=[t.event('initial_decision') for t in trace.traces]
    assert population_statistic(trace,values,'mean')==pytest.approx(.75*np.mean(individual[0])+.25*np.mean(individual[1]))
    conditioned=trace.select(['denied'])
    assert population_statistic(conditioned,conditioned.event('initial_decision'),'median')==pytest.approx(np.median(individual[1]))
    p['observations'][0]['population_path_scope']=['denied']
    conditional_model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    assert np.isfinite(conditional_model.log_likelihood(np.zeros(conditional_model.layout.size),[0]))


def test_missing_event_on_one_path_is_not_silently_renormalized_away():
    data=path_data()
    p=data['programs'][0]
    p['observations']=[observation('population','whole_case_clock',8.,40.,case=None)]
    p['case_path_scope']={}
    p['routes'][0]['operations'][-1]['markers']=[]
    model=VisitHierarchy(data,cfg())
    assert model.log_likelihood(np.zeros(model.layout.size),[0])==-np.inf
    p['observations'][0]['population_path_scope']=['approved']
    conditioned=VisitHierarchy(data,cfg())
    assert np.isfinite(conditioned.log_likelihood(np.zeros(conditioned.layout.size),[0]))


def test_first_visit_union_selects_existing_outcome_and_not_both_decisions():
    data=path_data()
    p=data['programs'][0]
    o=observation('decision_first','single_visit_cycle',4.,10.,case=None,activities=['approve','deny'])
    o['operators'][0].update(activity_selection='first_present',visits='first')
    o['population_condition']='first_visit'
    p.update(observations=[o],case_path_scope={})
    model=VisitHierarchy(data,cfg())
    rng=np.random.default_rng(1123)
    for _ in range(8):
        z=rng.normal(size=model.layout.size)
        assert np.isfinite(model.log_likelihood(z,[0]))
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)
        pop=model.trace(model.programs[0],z,model.parameters(z),0,True)
        values=pop.values(o['operators'][0])
        expected=np.concatenate([t.durations[:,t.index[op]] for t,op in zip(pop.traces,['approve','deny'])])
        np.testing.assert_array_equal(values,expected)


def test_first_visit_population_conditions_on_occurrence_not_zero_for_absent_path():
    data=path_data()
    p=data['programs'][0]
    o=observation('review_first','single_visit_cycle',4.,10.,case=None,activities=['review'])
    o['operators'][0]['visits']='first'
    p.update(observations=[o],case_path_scope={})
    unconditioned=VisitHierarchy(data,cfg())
    assert unconditioned.log_likelihood(np.zeros(unconditioned.layout.size),[0])==-np.inf
    o['population_condition']='first_visit'
    model=VisitHierarchy(data,cfg())
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)
    pop=model.trace(model.programs[0],z,model.parameters(z),0,True)
    selected=observation_population(pop,o['operators'][0],o)
    assert selected.path_ids==('approved',)
    # Conditioning is not evidence that the unconditional approval rate is one.
    z[model.programs[0]['routes'][0]['path_coordinates']]=4.
    assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood(np.zeros(model.layout.size),[0]),abs=1e-12)


def test_union_first_cycle_can_precede_a_later_opposite_decision():
    ops=[Operation('deny','A','agency','decision'),Operation('approve','A','agency','decision')]
    trace=CompactTrace(ops,[Block('decisions',['deny','approve'])],np.array([[3.,7.],[8.,2.]]))
    operator=dict(basis='single_visit_cycle',activity_ids=['approve','deny'],
                  visits='first',activity_selection='first_present')
    np.testing.assert_array_equal(trace.values(operator),[3.,8.])
    parallel=CompactTrace(ops,[Block('decisions',['deny','approve'],edges=[])],np.array([[3.,7.]]))
    with pytest.raises(UnavailableTraceQuantity,match='Simultaneous'):
        parallel.values(operator)
    operator['visits']='last'
    with pytest.raises(ValueError,match='first single-visit'):
        validate_operator(operator)


def test_disjoint_report_intervals_add_probability_not_log_likelihood_or_envelope_mass():
    o=dict(lower=1.,upper=20.,report_intervals=[[1.,2.],[10.,20.]])
    exact=logsumexp([duration_log_probability(1.,2.,7.),duration_log_probability(10.,20.,7.)])
    assert duration_report_log_probability(o,7.)==pytest.approx(exact)
    assert exact<duration_log_probability(1.,20.,7.)
    # A partition of the positive half-line has normalized probability one.
    whole=dict(lower=0.,upper=None,report_intervals=[[0.,7.],[7.,None]])
    assert duration_report_log_probability(whole,7.)==pytest.approx(0.,abs=1e-12)


@pytest.mark.parametrize('paths',[True,False])
@pytest.mark.parametrize('residual',[True,False])
def test_grouped_report_kernels_match_scalar_for_paths_and_legacy_routes(paths,residual):
    data=path_data()
    p=data['programs'][0]
    o=observation('report','single_visit_cycle',1.,20.,activities=['file'])
    o['report_intervals']=[[1.,2.],[10.,20.]]
    if residual:
        o.update(case_id=None,statistic='report_only',
            operators=[dict(basis='unmodeled_duration',median_days=7.,log_scale=3.)])
    p.update(observations=[o],case_path_scope={})
    if not paths:
        route=p['routes'][0]
        route.pop('paths')
        route['blocks']=[dict(id='all',operations=[a['id'] for a in route['operations']])]
    model=VisitHierarchy(data,cfg())
    rng=np.random.default_rng(4203)
    for _ in range(6):
        z=rng.normal(size=model.layout.size)
        assert np.isfinite(model.log_likelihood(z,[0]))
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)


@pytest.mark.parametrize('intervals',[[[0.,2.],[1.,3.]],[[2.,3.],[0.,1.]],[[0.,None],[2.,3.]],[[0.,0.]]])
def test_model_rejects_overlapping_unsorted_or_invalid_report_intervals(intervals):
    data=path_data()
    data['programs'][0]['observations'][0]['report_intervals']=intervals
    with pytest.raises(ValueError,match='Report intervals'):
        VisitHierarchy(data,cfg())


def test_centered_update_preserves_all_case_path_report_likelihoods():
    model=VisitHierarchy(path_data(),cfg())
    rng=np.random.default_rng(156)
    z=rng.normal(size=model.layout.size)
    initial=model.log_likelihood(z,[0])
    updated,value=model.centered_duration_update(z,[0],initial,rng)
    assert not np.array_equal(updated,z)
    assert value==pytest.approx(initial,abs=1e-10)


def test_correction_cohort_uses_its_explicit_path_population():
    data=path_data()
    p=data['programs'][0]
    p['routes'][0]['paths'][0]['blocks'][0]['repeat_key']='corrections'
    p['rate_observations']=[dict(repeat_key='corrections',event='any_correction_per_case',
        cohort_scope='completed_cases_for_repeat_block',independent_cohort=True,
        successes=2,trials=10,population_path_scope=['approved'])]
    model=VisitHierarchy(data,cfg())
    z=np.zeros(model.layout.size)
    terms=model.log_likelihood(z,[0],parts=True)
    assert terms['J__P:cohort:0']==pytest.approx(10*np.log(.5))
    z[model.programs[0]['routes'][0]['path_coordinates']]=3.
    assert model.log_likelihood(z,[0],parts=True)['J__P:cohort:0']==pytest.approx(terms['J__P:cohort:0'])


@pytest.mark.parametrize('bad',['unknown_case','unknown_path','empty','duplicate','individual_population_scope','both_blocks_and_paths','unused_operation'])
def test_invalid_path_contracts_fail_before_sampling(bad):
    data=path_data()
    p=data['programs'][0]
    if bad=='unknown_case': p['case_path_scope']['missing']=['approved']
    elif bad=='unknown_path': p['case_path_scope']['a']=['missing']
    elif bad=='empty': p['case_path_scope']['a']=[]
    elif bad=='duplicate': p['routes'][0]['paths'][1]['id']='approved'
    elif bad=='individual_population_scope': p['observations'][0]['population_path_scope']=['approved']
    elif bad=='both_blocks_and_paths': p['routes'][0]['blocks']=[]
    elif bad=='unused_operation':
        p['routes'][0]['operations'].append(dict(p['routes'][0]['operations'][0],id='unused'))
    with pytest.raises(ValueError):
        VisitHierarchy(data,cfg())


def test_unknown_labor_or_agency_on_one_path_is_not_dropped():
    data=path_data()
    data['programs'][0]['routes'][0]['operations'][-1].update(actor_role='unknown',actor_id=None,agency_work=None)
    model=VisitHierarchy(data,Config(population_size=16))
    z=np.zeros(model.layout.size)
    burden=model.expected_burden(model.programs[0],z,model.parameters(z),0)
    assert 'mean_agency_count' not in burden
    assert 'mean_agency_hours' not in burden


def test_inventory_hypotheses_remain_program_shared_outside_case_paths():
    data=path_data()
    second=copy.deepcopy(data['programs'][0]['routes'][0])
    second['id']='other_inventory'
    second['operations'][1]['actor_id']='J:Other'
    data['programs'][0]['routes'].append(second)
    model=VisitHierarchy(data,cfg())
    z=np.random.default_rng(123).normal(size=model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    assert np.isfinite(model.log_likelihood(z,[1]))
    assert model.programs[0]['routes'][0]['paths'][0]['indices'][0]==model.programs[0]['routes'][1]['paths'][0]['indices'][0]


def test_sampler_report_and_precision_support_path_mixtures():
    from pipeline.procbench.run_visit_hierarchy import precision_check, preflight_report
    data=path_data()
    # Include ambiguous operator interpretation on the same case as another claim.
    o=observation('uncertain','single_visit_cycle',1.,8.,case='a',activities=['review'])
    o['operators'].append(dict(basis='unmodeled_duration',median_days=7.,log_scale=3.))
    o['operator_weights']=[.8,.2]
    data['programs'][0]['observations'].append(o)
    config=cfg(chains=1,warmup=1,draws=8)
    model=VisitHierarchy(data,config)
    states,routes,likelihood,_=model.sample()
    report=model.report(states,routes,likelihood)
    program=report['programs']['J__P']
    assert 'case_path_probability:inventory:approved' in program['metrics']
    assert np.sum(program['interpretations']['uncertain']['posterior_mean_weights'])==pytest.approx(1.)
    assert program['case_path_scope']=={'a':['approved'],'b':['denied']}
    assert not report['posterior_converged']
    assert preflight_report(model)['finite_at_all_probe_points']
    precision=precision_check(model,VisitHierarchy(data,replace(config,population_size=32)),states,routes)
    assert precision['states_checked']==8
