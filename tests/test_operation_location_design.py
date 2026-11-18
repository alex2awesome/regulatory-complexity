"""Focused source-free checks for the optional operation-location design."""

from dataclasses import replace
import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy


def program(ident, operation):
    return dict(
        id=ident,
        inventory_granularity="aggregate_phases",
        clock_estimand="synthetic one-phase fixture",
        routes=[dict(id="only", prior_weight=1.0, operations=[dict(
            id=operation, actor_id=ident, actor_role="agency", task_type="review",
            markers=["decision"], payer_work=False, agency_work=False,
        )], blocks=[dict(id="phase", operations=[operation])])],
        observations=[],
    )


def declaration():
    return dict(
        schema_version="operation-location-design/1",
        interpretation="Synthetic county prior contrast; not learned prevalence.",
        unlisted_operations="zero_additive_effect",
        terms=[dict(id="county:santa_clara", group="county", prior_sd=.4,
                    rationale="Fixed working county log-location prior scale")],
        rows=[dict(program_id="ahj", operation_id="permit_review",
                   loadings={"county:santa_clara": 1.0})],
    )


def data(with_design=True):
    result=dict(programs=[program("ahj", "permit_review"),
                          program("utility", "final_ix_pto")])
    if with_design:
        result["operation_location_design"] = declaration()
    return result


def config(**kw):
    return Config(population_size=16, modeled_channels=("elapsed",), **kw)


def test_design_adds_declared_operation_mean_and_unlisted_utility_is_zero():
    model=VisitHierarchy(data(), config())
    z=np.zeros(model.layout.size)
    z[model.operation_location_design_coordinates]=2.0
    mu=model.parameters(z)["mu"][0]
    np.testing.assert_allclose(mu, [np.log(7.0)+.8, np.log(7.0)])
    assert model.operation_location_design["listed_rows"] == 1

    legacy=VisitHierarchy(data(False), config())
    assert "operation_location_design" not in legacy.layout.slices
    assert legacy.layout.size + 1 == model.layout.size
    zero=np.zeros(legacy.layout.size)
    np.testing.assert_array_equal(legacy.parameters(zero)["mu"][0],
                                  np.full(2, np.log(7.0)))

    invalid=data()
    invalid["operation_location_design"]["rows"].append(copy.deepcopy(
        invalid["operation_location_design"]["rows"][0]))
    with pytest.raises(ValueError, match="Duplicate operation"):
        VisitHierarchy(invalid, config())
    invalid=data()
    invalid["operation_location_design"]["rows"][0]["loadings"]={"unknown": 1.0}
    with pytest.raises(ValueError, match="unknown term"):
        VisitHierarchy(invalid, config())
    invalid=data()
    invalid["operation_location_design"]["terms"][0]["prior_sd"]=0
    with pytest.raises(ValueError, match="positive finite"):
        VisitHierarchy(invalid, config())


def test_operation_centered_gaussian_conditional_preserves_augmented_prior():
    model=VisitHierarchy(data(), config(hierarchy_sampler="operation_centered"))
    coordinates=model.hierarchy_coordinates[0]
    design=model.design
    target=np.array([.25, -.35])
    noise=.7

    def likelihood(z, structures, *, _program_index=None):
        residual=(design @ z[coordinates]-target)/noise
        if _program_index is not None:
            residual=residual[model.programs[_program_index]["global_indices"]]
        return -.5*float(residual @ residual)

    model.log_likelihood=likelihood
    covariance=np.linalg.inv(np.eye(len(coordinates))+design.T@design/noise**2)
    mean=covariance@design.T@target/noise**2
    rng=np.random.default_rng(8104)
    z=rng.normal(size=model.layout.size)
    value=likelihood(z,[0,0])
    draws=[]
    for iteration in range(2200):
        z,value,_=model.operation_centered_duration_update(z,[0,0],value,rng)
        if iteration>=200:
            draws.append(z[coordinates].copy())
    draws=np.asarray(draws)
    np.testing.assert_allclose(draws.mean(axis=0),mean,atol=.11)
    np.testing.assert_allclose(np.cov(draws,rowvar=False),covariance,atol=.14)
