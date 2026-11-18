"""Source-free checks of a transition kernel, not a new statistical model."""
import copy
from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from procbench_fixtures import data_fixture, observation


def population_data():
    data=data_fixture()
    data['programs'][0]['observations']=[
        observation('median','single_visit_cycle',4.,10.,case=None,activities=['review'])]
    other=copy.deepcopy(data['programs'][0])
    other['id']='K__P'
    data['programs'].append(other)
    return data


def test_sampler_configuration_is_explicit_and_rank_checked():
    with pytest.raises(ValueError,match='Unknown hierarchy sampler'):
        Config(hierarchy_sampler='magic')
    assert Config(hierarchy_sampler='operation_centered',operation_sd=0.).operation_sd==0.
    assert Config().hierarchy_sampler=='blocked'


def test_zero_operation_sd_uses_actual_full_rank_design_without_changing_target():
    data=data_fixture()
    cfg=Config(population_size=16,agency_sd=0.,task_sd=1.5,operation_sd=0.)
    blocked=VisitHierarchy(data,cfg)
    centered=VisitHierarchy(data,replace(cfg,hierarchy_sampler='operation_centered'))
    assert centered.layout.size==blocked.layout.size
    np.testing.assert_array_equal(centered.design,blocked.design)
    assert np.linalg.matrix_rank(centered.design)==len(centered.operations)
    rng=np.random.default_rng(3210)
    for _ in range(10):
        z=rng.normal(size=centered.layout.size)
        np.testing.assert_allclose(centered.parameters(z)['mu'],blocked.parameters(z)['mu'])
        assert centered.log_likelihood(z,[0])==blocked.log_likelihood(z,[0])
    np.testing.assert_allclose(centered.design@centered.duration_null_basis,0.,atol=1e-13)


def test_zero_operation_sd_rejects_genuinely_rank_deficient_design():
    data=data_fixture()
    for operation in data['programs'][0]['routes'][0]['operations']:
        operation['task_type']='same_task'
    cfg=Config(population_size=16,agency_sd=0.,task_sd=1.5,operation_sd=0.,
               hierarchy_sampler='operation_centered')
    with pytest.raises(ValueError,match='positive-definite actual operation-mean covariance'):
        VisitHierarchy(data,cfg)


@pytest.mark.parametrize('phases',[False,True])
def test_same_layout_prior_transform_and_full_likelihood(phases):
    data=population_data()
    cfg=Config(population_size=16,modeled_channels=('elapsed',),within_visit_phases=phases)
    original=VisitHierarchy(data,cfg)
    current=VisitHierarchy(data,replace(cfg,hierarchy_sampler='operation_centered'))
    assert current.layout.size==original.layout.size
    rng=np.random.default_rng(901)
    for _ in range(10):
        z=rng.normal(size=current.layout.size)
        np.testing.assert_allclose(current.parameters(z)['mu'],original.parameters(z)['mu'])
        assert current.log_likelihood(z,[0,0])==original.log_likelihood(z,[0,0])
        assert current.log_likelihood(z,[0,0])==pytest.approx(current.log_likelihood_reference(z,[0,0]))


def test_regression_moves_only_declared_program_operation_means():
    model=VisitHierarchy(population_data(),Config(population_size=16,hierarchy_sampler='operation_centered'))
    rng=np.random.default_rng(321)
    for pi,indices,rows,factor,scale,regression in model.duration_conditionals:
        wanted=np.zeros(len(model.operations))
        wanted[indices]=rng.normal(size=len(indices))
        np.testing.assert_allclose(model.design@regression@wanted[indices],wanted,atol=1e-13)
        np.testing.assert_allclose(factor.T@scale,np.eye(len(indices)),atol=1e-13)
    np.testing.assert_allclose(model.design@model.duration_null_basis,0.,atol=1e-13)
    np.testing.assert_allclose(model.duration_null_basis.T@model.duration_null_basis,
                               np.eye(model.duration_null_basis.shape[1]),atol=1e-13)


def test_gaussian_likelihood_matches_analytic_joint_posterior():
    # Two independent program likelihoods coupled through the full Gaussian
    # hierarchy. The exact posterior includes null variance and correlations.
    model=VisitHierarchy(population_data(),Config(population_size=16,modeled_channels=('elapsed',),
                         hierarchy_sampler='operation_centered'))
    indices=model.hierarchy_coordinates[0]
    design=model.design
    target=np.array([.1,1.,-.4,.8,-.5,1.2])
    noise=.5
    def likelihood(z,structures,*,_program_index=None):
        residual=(design@z[indices]-target)/noise
        if _program_index is not None:
            residual=residual[model.programs[_program_index]['global_indices']]
        return -.5*float(residual@residual)
    model.log_likelihood=likelihood
    posterior_cov=np.linalg.inv(np.eye(len(indices))+design.T@design/noise**2)
    posterior_mean=posterior_cov@design.T@target/noise**2
    rng=np.random.default_rng(612)
    z=rng.normal(size=model.layout.size)
    value=likelihood(z,[0,0])
    draws=[]
    for i in range(5000):
        old=z.copy()
        z,value,_=model.operation_centered_duration_update(z,[0,0],value,rng)
        assert value==pytest.approx(likelihood(z,[0,0]),abs=1e-12)
        if i>=500:
            draws.append(z[indices].copy())
    draws=np.asarray(draws)
    np.testing.assert_allclose(draws.mean(axis=0),posterior_mean,atol=.065)
    np.testing.assert_allclose(np.cov(draws,rowvar=False),posterior_cov,atol=.085)
    null=draws@model.duration_null_basis
    np.testing.assert_allclose(null.var(axis=0),1.,atol=.09)


@pytest.mark.parametrize('case_data',[False,True])
def test_new_transition_samples_actual_case_or_population_target(case_data):
    data=data_fixture() if case_data else population_data()
    model=VisitHierarchy(data,Config(chains=1,warmup=2,draws=8,population_size=16,
                                   hierarchy_sampler='operation_centered'))
    states,routes,ll,_=model.sample()
    assert np.isfinite(states).all()
    for z,r,value in zip(states[0],routes[0],ll[0]):
        assert model.log_likelihood(z,r)==pytest.approx(value,abs=1e-10)
    report=model.report(states,routes,ll)
    assert any(key.startswith('operation:') and key.endswith(':elapsed:log_location')
               for key in report['diagnostics'])
    assert any(key.startswith('agency:') and key.endswith(':inventory_mean_cycle_days')
               for key in report['diagnostics'])
    assert any(':report_offset:' in key for key in report['diagnostics'])
    assert report['external_validation']['synthetic_posterior_quotable_as_validated'] is False
