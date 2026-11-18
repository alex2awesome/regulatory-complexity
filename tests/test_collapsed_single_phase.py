"""Finite source-free checks of opt-in one-phase case quadrature."""
from dataclasses import replace
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy, duration_report_log_probability
from pipeline.procbench.run_visit_hierarchy import precision_check
from test_analytic_phase import phase_data


def individual_data(two=False):
    data=phase_data(); o=data['programs'][0]['observations'][0]
    o.update(id='case-report',case_id='case-1',statistic='individual',lower=3.,upper=11.)
    if two: data['programs'][0]['observations'].append(dict(o,id='case-report-2'))
    return data


def cfg(size=64, contamination=.05):
    return Config(population_size=16,modeled_channels=('elapsed',),
        population_integration='collapsed_single_phase_quadrature',
        collapsed_case_quadrature_size=size,contamination=contamination)


@pytest.mark.parametrize('bounds',[(0.,4.),(3.,11.),(8.,None)])
@pytest.mark.parametrize('contamination',[0.,.05])
def test_quadrature_refines_to_independent_adaptive_integral(bounds,contamination):
    data=individual_data(); o=data['programs'][0]['observations'][0]
    o.update(lower=bounds[0],upper=bounds[1])
    model=VisitHierarchy(data,cfg(128,contamination)); z=np.linspace(-.3,.3,model.layout.size)
    par=model.parameters(z); p=model.programs[0]; row=p['compiled']['entries'][0]
    actual=model._collapsed_observation_log_probability(p,row,par)
    mu=float(par['mu'][0,p['global_indices'][0]])
    sd=math.hypot(float(par['sigma'][0]),model.cfg.common_case_sd)
    offset=model._report_offset(par,row['channel'],row['source'],False)
    def integrand(x):
        ll=duration_report_log_probability(o,math.exp(x),offset,row['report_scale'],contamination)
        return math.exp(float(ll))*norm.pdf(x,mu,sd)
    expected=math.log(quad(integrand,mu-12*sd,mu+12*sd,epsabs=1e-12)[0])
    assert actual==pytest.approx(expected,abs=1e-6)
    values=[]
    for size in (32,64,128):
        m=VisitHierarchy(data,cfg(size,contamination)); zz=np.linspace(-.3,.3,m.layout.size)
        values.append(m.log_likelihood(zz,[0]))
    assert abs(values[2]-values[1]) <= abs(values[1]-values[0])+1e-12


def test_union_scalar_batch_and_layout_guards():
    data=individual_data(); data['programs'][0]['observations'][0].update(
        lower=1.,upper=9.,report_intervals=[[1.,2.],[6.,9.]])
    collapsed=VisitHierarchy(data,cfg()); z=np.zeros(collapsed.layout.size)
    assert collapsed.log_likelihood(z,[0])==pytest.approx(collapsed.log_likelihood_reference(z,[0]))
    legacy=VisitHierarchy(data,replace(cfg(),population_integration='qmc'))
    p0,p1=legacy.programs[0],collapsed.programs[0]
    assert p1['case_coordinates'].shape==(1,0)
    assert legacy.layout.size-collapsed.layout.size==p0['case_dimension']
    assert p1['uncollapsed_case_dimension']==p0['case_dimension']
    with pytest.raises(ValueError,match='exactly one informative observation globally'):
        VisitHierarchy(individual_data(True),cfg())


def test_individual_and_unknown_n_median_coexist_and_report():
    data=individual_data()
    median=dict(data['programs'][0]['observations'][0],id='unknown-n-median',case_id=None,
                statistic='median',lower=5.,upper=9.)
    data['programs'][0]['observations'].append(median)
    model=VisitHierarchy(data,cfg())
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    states=np.tile(z,(1,8,1)); routes=np.zeros((1,8,1),dtype=int)
    ll=np.tile(model.log_likelihood(z,[0]),(1,8))
    report=model.report(states,routes,ll)
    collapsed=report['programs']['p']['collapsed_single_phase_cases']
    assert collapsed['sampled_case_duration_coordinates']==0
    assert collapsed['report_kernel']=='existing_student_t_df4_mixture'


def test_same_size_precision_comparison_is_refused():
    model=VisitHierarchy(individual_data(),cfg(256))
    same=VisitHierarchy(individual_data(),cfg(256))
    states=np.zeros((1,8,model.layout.size)); routes=np.zeros((1,8,1),dtype=int)
    result=precision_check(model,same,states,routes)
    assert not result['collapsed_case_integration_strictly_refined_or_unused']
    assert not result['likelihood_acceptable']
    assert not result['predictions_acceptable']


def test_1024_node_zero_tail_weights_are_stable():
    model=VisitHierarchy(individual_data(),cfg(1024))
    assert np.isfinite(model.collapsed_case_log_weights).any()
    assert not np.isnan(model.collapsed_case_log_weights).any()
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))


def test_operation_centered_sampler_skips_only_absent_case_centering():
    collapsed=VisitHierarchy(individual_data(),replace(cfg(32),chains=1,warmup=0,
        draws=8,hierarchy_sampler='operation_centered'))
    collapsed.centered_duration_update=lambda *args: (_ for _ in ()).throw(
        AssertionError('collapsed case-centering must not run'))
    collapsed.sample()
    legacy=VisitHierarchy(individual_data(),replace(cfg(32),chains=1,warmup=0,
        draws=8,hierarchy_sampler='operation_centered',population_integration='qmc'))
    calls=[]; original=legacy.centered_duration_update
    def counted(*args):
        calls.append(1)
        return original(*args)
    legacy.centered_duration_update=counted
    legacy.sample()
    assert len(calls)==8
