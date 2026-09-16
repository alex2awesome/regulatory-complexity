import copy
from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy,count_log_probability,repeat_quantiles
from pipeline.procbench.rework_counts import ReworkLaw


def observation(ident,basis,lower,upper,case='c',activities=None):
    operator=dict(basis=basis)
    if activities:
        operator['activity_ids']=activities
    if basis=='whole_case_clock':
        operator.update(start='process_start',end='initial_decision')
    return dict(id=ident,case_id=case,source_family='source',sampling='unselected',
        statistic='individual' if case else 'median',lower=lower,upper=upper,
        operators=[operator],operator_weights=[1.])


def data_fixture():
    return dict(programs=[dict(id='J__P',routes=[dict(id='simple',prior_weight=1.,operations=[
        dict(id='file',actor_id='payer',actor_role='payer',task_type='filing',markers=['submission'],
             payer_work=True,agency_work=False),
        dict(id='review',actor_id='J:Review',actor_role='agency',task_type='review',
             payer_work=False,agency_work=True),
        dict(id='decide',actor_id='J:Review',actor_role='agency',task_type='decision',markers=['decision'],
             payer_work=False,agency_work=True)],blocks=[
        dict(id='loop',operations=['file','review'],repeat_key='corrections'),
        dict(id='end',operations=['decide'])])],observations=[
            observation('total','whole_case_clock',15.,25.),
            observation('task','single_visit_cycle',4.,10.,activities=['review']),
            observation('visits','visit_count',3,3),
            observation('labor','agency_hours',1.,3.)],rate_observations=[])])


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
