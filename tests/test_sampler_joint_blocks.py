"""Focused checks for opt-in overlapping ESS transition blocks."""

import copy
from dataclasses import replace

import numpy as np

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy
from pipeline.procbench.latent_gaussian import elliptical_slice
from test_source_offset_hierarchy import cfg, hierarchy_data


def declared_data():
    data=hierarchy_data()
    p=data["programs"][0]
    data["operation_location_design"]=dict(
        schema_version="operation-location-design/1",
        interpretation="Synthetic context term for transition test only.",
        unlisted_operations="zero_additive_effect",
        terms=[dict(id="context",group="context",prior_sd=.4,rationale="fixed test scale")],
        rows=[dict(program_id=p["id"],operation_id="review",loadings={"context":1.0})])
    data["sampler_joint_blocks"]=dict(
        schema_version="sampler-joint-blocks/1",
        overlap_policy="sequential_invariant_kernels",
        blocks=[dict(id="forum_context",rationale="Jointly move a confounded test contrast.",selectors=[
            dict(kind="source_type_effect",source_type="forum"),
            dict(kind="operation_location_design_group",group="context"),
            dict(kind="operation_residuals",program_ids=[p["id"]])])])
    return data


def test_declaration_allocates_nothing_and_resolves_existing_whitened_coordinates():
    data=declared_data(); plain=copy.deepcopy(data); plain.pop("sampler_joint_blocks")
    configuration=replace(cfg(),hierarchy_sampler="operation_centered")
    model=VisitHierarchy(data,configuration); control=VisitHierarchy(plain,configuration)
    assert model.layout.size==control.layout.size
    assert model.layout.slices.keys()==control.layout.slices.keys()
    block=model.sampler_joint_blocks[0]["coordinates"]
    expected={model.source_offset_hierarchy.type_coordinates["forum"],
              int(model.operation_location_design_coordinates[0])}
    expected.update(map(int,model.operation[0,model.programs[0]["global_indices"]]))
    assert set(map(int,block))==expected
    rng=np.random.default_rng(72)
    for _ in range(5):
        z=rng.normal(size=model.layout.size)
        assert model.log_likelihood(z,[0])==control.log_likelihood(z,[0])
        assert -.5*z@z == -.5*z@z  # declaration adds no density or Jacobian term


def test_joint_ess_block_retains_standard_normal_prior_under_gaussian_likelihood():
    model=VisitHierarchy(declared_data(),replace(cfg(),hierarchy_sampler="operation_centered"))
    block=model.sampler_joint_blocks[0]["coordinates"]
    target=np.linspace(-.5,.75,len(block)); noise=.8
    def likelihood(z):
        residual=(z[block]-target)/noise
        return -.5*float(residual@residual)
    variance=noise**2/(1+noise**2)
    mean=target/(1+noise**2)
    rng=np.random.default_rng(991); z=rng.normal(size=model.layout.size); value=likelihood(z); draws=[]
    for i in range(3000):
        z,value,_=elliptical_slice(z,block,likelihood,value,rng)
        if i>=300: draws.append(z[block].copy())
    draws=np.asarray(draws)
    np.testing.assert_allclose(draws.mean(axis=0),mean,atol=.06)
    np.testing.assert_allclose(np.diag(np.cov(draws,rowvar=False)),variance,atol=.07)
