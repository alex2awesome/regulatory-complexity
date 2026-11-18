import copy
import itertools
from dataclasses import replace

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy, duration_report_log_probability
from pipeline.procbench.cohort_quantiles import CohortQuantileGrid
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.run_visit_hierarchy import preflight_report, precision_check
from procbench_fixtures import data_fixture
from test_compile_visit_durations import inputs


def cohort_fixture(n=20):
    return dict(id='dashboard',cohort_id='J__P:decided_2025',sample_size=n,quantile_method='linear',
        sampling='iid_within_declared_population',independent_of_other_evidence=True,
        conditional_report_independence=True,source_family='dashboard',
        operators=[dict(basis='whole_case_clock',start='process_start',end='initial_decision')],
        operator_weights=[1.],reports=[dict(id='median',statistic='median',lower=12.,upper=20.),
                                    dict(id='p90',statistic='p90',lower=25.,upper=40.)])


def model_data(n=20):
    data=data_fixture()
    data['programs'][0].update(observations=[],quantile_cohorts=[cohort_fixture(n)])
    return data


@pytest.mark.parametrize('method',['linear','inverted_cdf'])
@pytest.mark.parametrize('n',[1,2,5])
def test_joint_grid_matches_exact_enumeration_not_independent_quantiles(n,method):
    population=np.array([2.,10.,40.])
    weights=np.array([.2,.5,.3])
    reports=[dict(lower=4.,upper=15.),dict(lower=15.,upper=45.)]
    exact=0.
    for positions in itertools.product(range(3),repeat=n):
        values=np.quantile(population[list(positions)],[.5,.9],method=method)
        probability=np.prod(weights[list(positions)])
        exact+=probability*np.exp(sum(float(duration_report_log_probability(r,v,scale=.3,contamination=0.))
                                     for r,v in zip(reports,values)))
    grid=CohortQuantileGrid(n,['median','p90'],method,size=16384)
    sampled=grid.values(population,weights)
    curves=np.column_stack([duration_report_log_probability(r,sampled[:,j],scale=.3,contamination=0.)
                            for j,r in enumerate(reports)])
    assert np.mean(np.exp(curves.sum(axis=1))) == pytest.approx(exact,abs=2e-4)
    if n==1:
        assert not np.isclose(np.mean(np.exp(curves.sum(axis=1))),np.prod(np.mean(np.exp(curves),axis=0)),rtol=.02)


def test_even_sample_median_interpolates_durations_not_log_durations():
    grid=CohortQuantileGrid(2,['median'],'linear',size=4096)
    values=grid.values([2.,10.])[:,0]
    assert set(values)=={2.,6.,10.}
    assert np.mean(values==6.)==pytest.approx(.5,abs=.002)


def test_joint_uniform_order_statistics_have_correct_covariance():
    grid=CohortQuantileGrid(10,['median','p90'],'inverted_cdf',size=16384)
    assert grid.ranks==(5,9)
    u=grid.uniform_order_statistics
    np.testing.assert_allclose(u.mean(axis=0),np.array([5,9])/11,atol=2e-5)
    assert np.cov(u.T,ddof=0)[0,1]==pytest.approx(5*2/(11**2*12),abs=2e-5)
    assert np.all(u[:,0]<=u[:,1])


def test_sampling_uncertainty_decreases_with_n_and_grid_refinement_preserves_prefix():
    small=CohortQuantileGrid(11,['median'],'linear',size=4096)
    large=CohortQuantileGrid(101,['median'],'linear',size=4096)
    assert np.var(large.uniform_order_statistics)<.2*np.var(small.uniform_order_statistics)
    finer=CohortQuantileGrid(11,['median'],'linear',size=16384)
    np.testing.assert_array_equal(finer.uniform_order_statistics[:4096],small.uniform_order_statistics)


@pytest.mark.parametrize('field,value',[
    ('sample_size',None),('sample_size',0),('sample_size',True),('sample_size',1.5),
    ('quantile_method','unknown'),('sampling','completed_by_date'),
    ('independent_of_other_evidence',False),('conditional_report_independence',False)])
def test_cohort_does_not_invent_sampling_contract(field,value):
    data=model_data()
    data['programs'][0]['quantile_cohorts'][0][field]=value
    with pytest.raises(ValueError):
        VisitHierarchy(data,Config(population_size=16))


def test_same_cohort_cannot_be_split_across_independent_programs_or_rate_reports():
    data=model_data()
    second=copy.deepcopy(data['programs'][0])
    second['id']='J__Q'
    data['programs'].append(second)
    with pytest.raises(ValueError,match='overlapping cohort'):
        VisitHierarchy(data)
    data=model_data()
    data['programs'][0]['observations']=data_fixture()['programs'][0]['observations']
    data['programs'][0]['observations'][0]['cohort_id']='J__P:decided_2025'
    with pytest.raises(ValueError,match='overlaps explicitly'):
        VisitHierarchy(data)


@pytest.mark.parametrize('change',['mean','duplicate_statistic','duplicate_claim'])
def test_unsupported_or_duplicated_cohort_statistics_fail(change):
    data=model_data()
    reports=data['programs'][0]['quantile_cohorts'][0]['reports']
    if change=='mean': reports[0]['statistic']='mean'
    elif change=='duplicate_statistic': reports[1]['statistic']='median'
    else: reports[1]['id']=reports[0]['id']
    with pytest.raises(ValueError):
        VisitHierarchy(data)


def test_joint_cohort_likelihood_matches_scalar_reference_and_source_bias_is_separate():
    model=VisitHierarchy(model_data(),Config(population_size=16,cohort_quadrature_size=16,modeled_channels=('elapsed',)))
    rng=np.random.default_rng(491)
    for _ in range(4):
        z=rng.normal(size=model.layout.size)
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)
    z=np.zeros(model.layout.size)
    p=model.programs[0]
    before=model.trace(p,z,model.parameters(z),0,True).durations.copy()
    ll=model.log_likelihood(z,[0])
    z[model.source[0,0]]=1.
    np.testing.assert_array_equal(before,model.trace(p,z,model.parameters(z),0,True).durations)
    assert model.log_likelihood(z,[0])!=ll
    assert list(model.log_likelihood(z,[0],parts=True))==['J__P:quantile_cohort:dashboard']


def test_shared_interpretation_prior_is_applied_once_to_joint_cohort():
    data=model_data()
    c=data['programs'][0]['quantile_cohorts'][0]
    c['operators'].append(dict(basis='single_visit_cycle',activity_ids=['review']))
    c['operator_weights']=[.3,.7]
    cfg=Config(population_size=16,cohort_quadrature_size=16)
    model=VisitHierarchy(data,cfg)
    z=np.zeros(model.layout.size)
    components=[]
    for operator in c['operators']:
        single=copy.deepcopy(data)
        single['programs'][0]['quantile_cohorts'][0].update(operators=[operator],operator_weights=[1.])
        m=VisitHierarchy(single,cfg)
        components.append(m.log_likelihood(z,[0]))
    assert model.log_likelihood(z,[0])==pytest.approx(logsumexp(np.log([.3,.7])+components))


def test_cohort_uses_weighted_path_population_not_one_independent_cohort_per_path():
    data=model_data()
    r=data['programs'][0]['routes'][0]
    blocks=r.pop('blocks')
    r['paths']=[dict(id='full',probability_weight=.8,blocks=blocks),
                dict(id='short',probability_weight=.2,blocks=[dict(id='short_end',operations=['decide'])])]
    cfg=Config(population_size=16,cohort_quadrature_size=16)
    model=VisitHierarchy(data,cfg)
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]))
    expected=model._quantile_cohort_parts(model.programs[0],model.trace(model.programs[0],z,model.parameters(z),0,True),model.parameters(z))
    assert model.log_likelihood(z,[0],parts=True)==expected


def test_cohort_model_samples_without_allocating_n_case_latents_and_reports_dependencies():
    cfg=Config(chains=1,warmup=0,draws=8,population_size=16,cohort_quadrature_size=16,modeled_channels=('elapsed',))
    model=VisitHierarchy(model_data(20),cfg)
    assert model.layout.size==VisitHierarchy(model_data(4000),cfg).layout.size
    assert model.programs[0]['case_coordinates'].size==0
    states,routes,ll,_=model.sample()
    assert np.isfinite(ll).all()
    report=model.report(states,routes,ll)
    assert report['programs']['J__P']['quantile_cohorts']['dashboard']['sample_size']==20
    preflight=preflight_report(model)
    assert preflight['observation_rows']==2
    assert preflight['independent_quantile_cohorts']==1
    finer=VisitHierarchy(model_data(20),replace(cfg,population_size=64,cohort_quadrature_size=64))
    precision=precision_check(model,finer,states,routes)
    assert precision['refined_cohort_quadrature_size']==64
    unrefined=precision_check(model,model,states,routes)
    assert not unrefined['cohort_integration_refined_or_unused']
    assert not unrefined['likelihood_acceptable']


def compiler_inputs():
    e,v,s,d,p=inputs()
    p={}
    e['measurements'][0].update(case_id=None,statistic='median',n=20)
    s['measurements'][0].update(statistic_interpretation='population_median',population_scope='all_cases')
    e['measurements'].append(dict(e['measurements'][0],id='m2',statistic='p90',value=20.))
    v['measurements'].append(dict(copy.deepcopy(v['measurements'][0]),measurement_id='m2'))
    s['measurements'].append(dict(copy.deepcopy(s['measurements'][0]),measurement_id='m2',statistic_interpretation='population_p90'))
    binding=dict(schema_version='joint-visit-cohort-bindings/1',program_id=e['program_id'],cohorts=[dict(
        id='summary',cohort_id='document:cohort',measurement_ids=['m1','m2'],quantile_method='linear',
        sampling='iid_within_declared_population',independent_of_other_evidence=True,
        conditional_report_independence=True,evidence=[dict(doc_id='document',quote='Evidence')],
        assumptions=['Explicit test-fixture sampling/quantile-method assumptions, not inferred from n.'])])
    return e,v,s,d,p,binding


def test_source_compiler_preserves_n_and_joins_summaries_into_one_v6_factor():
    e,v,s,d,p,b=compiler_inputs()
    original=copy.deepcopy((e,v,s,b))
    compiled=compile_durations(e,v,s,d,p,cohort_bindings=b)
    assert (e,v,s,b)==original
    assert compiled['observations']==[]
    assert compiled['coverage']['compiled_elapsed']==2
    assert compiled['coverage']['informative_elapsed']==2
    assert compiled['coverage']['likelihood_factors']==1
    assert compiled['quantile_cohorts'][0]['sample_size']==20
    data=model_data()
    data['programs'][0]['quantile_cohorts']=compiled['quantile_cohorts']
    model=VisitHierarchy(data,Config(population_size=16,cohort_quadrature_size=16))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))


@pytest.mark.parametrize('change',['different_n','missing_n','mean','unquoted','different_clock'])
def test_compiler_never_invents_or_splits_a_joint_cohort(change):
    e,v,s,d,p,b=compiler_inputs()
    if change=='different_n': e['measurements'][1]['n']=21
    elif change=='missing_n': e['measurements'][1]['n']=None
    elif change=='mean':
        e['measurements'][1]['statistic']='mean'
        s['measurements'][1]['statistic_interpretation']='population_mean'
    elif change=='unquoted': b['cohorts'][0]['evidence'][0]['quote']='Invented support'
    else: v['measurements'][1]['operators'][0]['activity_ids']=['file']
    with pytest.raises(ValueError):
        compile_durations(e,v,s,d,p,cohort_bindings=b)
