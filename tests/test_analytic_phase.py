"""Source-free checks of the exact one-phase restriction, not real recovery."""
import copy
from dataclasses import replace
import math

import numpy as np
import pytest
from scipy.stats import lognorm, multinomial

from pipeline.procbench.analytic_phase import (phase_histogram_log_probability, phase_quantile,
                                               phase_spread_sensitive_factors)
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compact_visit_trace import population_statistic, population_quantile
from pipeline.procbench.run_visit_hierarchy import precision_check
from test_cohort_histograms import histogram_fixture
from test_typical_range_reports import reporting_model


def phase_data(histogram=False):
    operation=dict(id='phase',actor_id='agency',actor_role='agency',task_type='review',
                   markers=['decision'],payer_work=False,agency_work=False)
    operator=dict(basis='single_visit_cycle',activity_ids=['phase'])
    p=dict(id='p',inventory_granularity='aggregate_phases',
        clock_estimand='Synthetic test receipt to approval phase, not an empirical population',
        routes=[dict(id='one',prior_weight=1.,operations=[operation],
                     blocks=[dict(id='phase',operations=['phase'])])],
        observations=[dict(id='median',case_id=None,source_family='source',sampling='unselected',
            statistic='median',lower=6.,upper=8.,operators=[operator],operator_weights=[1.])])
    if histogram:
        c=histogram_fixture()
        c.update(operators=[operator],operator_weights=[1.],bin_counts=[250,500,250],
                 sample_size=1000)
        p.update(observations=[],histogram_cohorts=[c])
    return dict(programs=[p])


def config(**kw):
    return Config(population_size=16,modeled_channels=('elapsed',),
                  population_integration='analytic_single_phase',**kw)


@pytest.mark.parametrize('mu,sd',[(-3.,.4),(0.,1.),(4.,2.)])
def test_exact_quantiles_and_multinomial_against_independent_scipy(mu,sd):
    edges=[0.,1.,3.,7.,None]
    counts=[1,3,5,2]
    distribution=lognorm(s=sd,scale=math.exp(mu))
    bounds=[0,1,3,7,np.inf]
    probabilities=np.array([(distribution.sf(lo)-distribution.sf(hi)
        if distribution.cdf(lo)>.5 else distribution.cdf(hi)-distribution.cdf(lo))
        for lo,hi in zip(bounds[:-1],bounds[1:])])
    expected=multinomial.logpmf(counts,sum(counts),probabilities)
    assert phase_histogram_log_probability(counts,edges,mu,sd)==pytest.approx(expected,abs=1e-8)
    for q in (.1,.5,.9):
        assert phase_quantile(mu,sd,q)==pytest.approx(distribution.ppf(q))


def test_tiny_right_tail_mass_remains_finite_without_pseudocount():
    value=phase_histogram_log_probability([0,1],[0,math.exp(40),None],0.,1.)
    assert np.isfinite(value)
    assert value==pytest.approx(lognorm.logsf(math.exp(40),s=1),abs=1e-10)


@pytest.mark.parametrize('mu,sd',[(0,-1),(0,0),(0,np.inf),(np.nan,1)])
def test_invalid_direct_phase_distribution_is_rejected(mu,sd):
    with pytest.raises(ValueError,match='positive scale'):
        phase_quantile(mu,sd,.5)


@pytest.mark.parametrize('histogram',[False,True])
def test_likelihood_matches_reference_and_is_exactly_grid_independent(histogram):
    model=VisitHierarchy(phase_data(histogram),config())
    fine=VisitHierarchy(phase_data(histogram),replace(model.cfg,population_size=4096))
    for seed in range(4):
        z=np.random.default_rng(seed).normal(scale=.25,size=model.layout.size)
        ll=model.log_likelihood(z,[0])
        assert ll==model.log_likelihood_reference(z,[0])
        assert ll==fine.log_likelihood(z,[0])
    states=np.zeros((1,8,model.layout.size)); routes=np.zeros((1,8,1),dtype=int)
    precision=precision_check(model,fine,states,routes)
    assert precision['max_absolute_log_likelihood_change']==0.
    assert precision['max_relative_clock_quantile_change']==0.
    assert precision['likelihood_acceptable'] and precision['predictions_acceptable']
    assert precision['population_approximation_check']=='analytic_by_contract_grid_independent'
    assert not precision['analytic_formula_independently_validated_by_this_check']
    if histogram:
        assert precision_check(model,model,states,routes)['histogram_integration_refined_or_unused']


def test_population_median_likelihood_cannot_spuriously_learn_case_spread():
    model=VisitHierarchy(phase_data(),config())
    z=np.zeros(model.layout.size)
    ll=model.log_likelihood(z,[0])
    # Locate sigma coordinates through the layout, not assumed numeric positions.
    changed=z.copy()
    changed[model.sigma[0]]=3.
    assert model.log_likelihood(changed,[0])==ll
    changed_model=VisitHierarchy(phase_data(),replace(model.cfg,common_case_sd=2.))
    assert changed_model.log_likelihood(z,[0])==ll


def test_exact_elapsed_law_is_not_applied_to_other_arrays():
    model=VisitHierarchy(phase_data(),config())
    z=np.zeros(model.layout.size)
    trace=model.trace(model.programs[0],z,model.parameters(z),0,True)
    values=np.log(trace.durations[:,0])
    assert population_statistic(trace,values,'mean')==float(np.mean(values))
    assert population_quantile(trace,values,.9)==float(np.quantile(values,.9))


@pytest.mark.parametrize('change',['individual','multiple_operations','repeat','granularity',
                                 'wrong_operator','wrong_start','phase_fraction','labor'])
def test_unsupported_subcases_fail_closed(change):
    data=phase_data(); p=data['programs'][0]; r=p['routes'][0]; cfg=config()
    if change=='individual': p['observations'][0].update(case_id='case',statistic='individual')
    elif change=='multiple_operations':
        r['operations'].append(dict(copy.deepcopy(r['operations'][0]),id='second'))
        r['blocks'][0]['operations'].append('second')
    elif change=='repeat': r['blocks'][0]['repeat_key']='correction'
    elif change=='granularity': p['inventory_granularity']='detailed_operations'
    elif change=='wrong_operator': p['observations'][0]['operators'][0]['basis']='sum_visit_cycles'
    elif change=='wrong_start':
        p['observations'][0]['operators']=[dict(basis='whole_case_clock',start='initial_decision',end='modeled_work_end')]
    elif change=='phase_fraction':
        with pytest.raises(ValueError,match='Analytic single-phase'):
            replace(cfg,within_visit_phases=True)
        return
    else: cfg=replace(cfg,modeled_channels=('elapsed','payer_hours'))
    with pytest.raises(ValueError,match='Analytic single-phase'):
        VisitHierarchy(data,cfg)


def test_subjective_quantile_range_uses_the_same_exact_population():
    data=phase_data()
    data['programs'][0]['observations'][0].update(statistic='typical_range',
                                                typical_range_model=reporting_model())
    model=VisitHierarchy(data,config())
    fine=VisitHierarchy(data,replace(model.cfg,population_size=1024))
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==model.log_likelihood_reference(z,[0])
    assert model.log_likelihood(z,[0])==fine.log_likelihood(z,[0])


def test_report_retains_numerical_method_and_prior_sensitive_tail_warning():
    model=VisitHierarchy(phase_data(),config(chains=1,warmup=1,draws=8))
    states,routes,ll,_=model.sample()
    report=model.report(states,routes,ll)
    assert report['population_integration']=='analytic_single_phase'
    assert not report['programs']['p']['population_tail_support']['tail_headline_eligible']
    assert not report['identification']['blocks']['agency:elapsed']['headline_eligible']


def test_all_duration_bin_has_no_timing_information_or_tail_headline():
    data=phase_data(True)
    data['programs'][0]['histogram_cohorts'][0].update(bin_edges=[0,None],bin_counts=[1000])
    model=VisitHierarchy(data,config(chains=1,warmup=0,draws=8))
    states,routes,ll,_=model.sample()
    assert np.array_equal(ll,np.zeros_like(ll))
    assert phase_spread_sensitive_factors(model.programs[0])==[]
    report=model.report(states,routes,ll)
    assert not report['programs']['p']['population_tail_support']['tail_headline_eligible']
    concentrated=np.random.default_rng(8).normal(scale=.1,size=(2,8,model.layout.size))
    info=model.information_report(concentrated,sampling_converged=True)
    for kind in ('agency','task','operation'):
        assert not info['blocks'][kind+':elapsed']['headline_eligible']
    assert 'aggregate phases' in info['blocks']['location:elapsed']['estimand_qualification']
