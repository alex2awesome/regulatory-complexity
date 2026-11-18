import copy

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.joint_inventory_prior import (JointInventoryPrior, empirical_joint_inventory,
    replay_upstream_indices, empirical_bridge_report)


def fixture():
    programs = []
    for county in ["A", "B"]:
        routes = []
        for n in [1, 2]:
            operations = [dict(id=f"step{i}", actor_id=county, actor_role="agency", task_type="review",
                               payer_work=False, agency_work=True) for i in range(n)]
            routes.append(dict(id=f"count{n}", prior_weight=1., operations=operations,
                               blocks=[dict(id=f"block{i}", operations=[f"step{i}"]) for i in range(n)]))
        programs.append(dict(id=county, routes=routes, observations=[dict(
            id=f"observed_{county}", case_id=f"case_{county}", source_family="fixture",
            sampling="unselected", statistic="individual", lower=1, upper=1,
            operators=[dict(basis="operation_count")], operator_weights=[1.])]))
    return dict(programs=programs, joint_inventory_prior=dict(
        schema_version="v6-joint-inventory-prior/1", program_ids=["A", "B"],
        feedback_policy="downstream_evidence_updates_joint_inventory",
        evidence_partition_reviewed=True, evidence_partition_note="Source-free independent-count fixture, no reused occupancy claims.",
        route_semantics_reviewed=True, hypotheses=[
            dict(id="both_small", prior_weight=.3, route_ids=["count1", "count1"]),
            dict(id="both_large", prior_weight=.7, route_ids=["count2", "count2"])]))


def test_joint_inventory_conditional_matches_full_likelihood_enumeration():
    model = VisitHierarchy(fixture(), Config(modeled_channels=("elapsed",), population_size=16))
    z = np.zeros(model.layout.size)
    prior = model.joint_inventory_prior
    p, ll, calls = prior.conditional(model, z)
    full = np.array([model.log_likelihood(z, structure) for structure in prior.states])
    np.testing.assert_allclose(full, ll, atol=1e-13)
    expected = full+np.log([.3,.7])
    np.testing.assert_allclose(p, np.exp(expected-logsumexp(expected)), atol=1e-13)
    assert calls == 4
    assert p[0] > .3  # Count evidence updates the supplied structural prior.


def test_v6_sampler_keeps_joint_support_and_targets_analytic_count_posterior():
    cfg = Config(chains=2, warmup=8, draws=600, modeled_channels=("elapsed",), population_size=16, seed=813)
    model = VisitHierarchy(fixture(), cfg)
    probabilities, _, _ = model.joint_inventory_prior.conditional(model, np.zeros(model.layout.size))
    states, routes, likelihood, _ = model.sample()
    np.testing.assert_array_equal(routes[:,:,0], routes[:,:,1])
    assert (routes[:,:,0] == 0).mean() == pytest.approx(probabilities[0], abs=.06)
    # Count likelihood does not depend on continuous latent durations.
    for index in [0, 17, 599]:
        assert likelihood[0,index] == pytest.approx(model.log_likelihood(states[0,index], routes[0,index]), abs=1e-13)
    report = model.report(states[:,:8], routes[:,:8], likelihood[:,:8])
    assert report["joint_inventory_prior"]["feedback_policy"] == "downstream_evidence_updates_joint_inventory"
    assert "joint_inventory:both_small" in report["diagnostics"]


def test_joint_inventory_rejects_checkpoint_outside_support():
    model = VisitHierarchy(fixture(), Config(chains=2, draws=8, warmup=0, modeled_channels=("elapsed",), population_size=16))
    with pytest.raises(ValueError, match="outside.*joint inventory"):
        model.sample(initial=(np.zeros((2,model.layout.size)), np.array([[0,1],[0,0]])))


def test_joint_inventory_rejects_positive_support_lost_to_underflow():
    data = fixture()
    for h, weight in zip(data["joint_inventory_prior"]["hypotheses"],
                         [np.nextafter(0., 1.), 1e308]):
        h["prior_weight"] = float(weight)
    with pytest.raises(ValueError, match="lose positive support"):
        JointInventoryPrior(data["joint_inventory_prior"], data["programs"])


@pytest.mark.parametrize("change", ["marginal_weights", "missing_program", "duplicate_state", "unknown_route", "no_partition", "no_feedback"])
def test_joint_prior_contract_fails_closed(change):
    data = fixture()
    d = data["joint_inventory_prior"]
    if change == "marginal_weights": data["programs"][0]["routes"][0]["prior_weight"] = .7
    if change == "missing_program": d["program_ids"] = ["A"]
    if change == "duplicate_state": d["hypotheses"].append(dict(id="duplicate", prior_weight=1, route_ids=["count1","count1"]))
    if change == "unknown_route": d["hypotheses"][0]["route_ids"][0] = "absent"
    if change == "no_partition": d["evidence_partition_reviewed"] = False
    if change == "no_feedback": d["feedback_policy"] = "silent_cut"
    with pytest.raises(ValueError):
        JointInventoryPrior(d, data["programs"])


def test_empirical_joint_compression_retains_correlations_and_draw_membership():
    z = np.array([[[[0,1],[0,1]], [[1,1],[1,1]], [[0,1],[0,1]]],
                  [[[1,1],[1,1]], [[1,1],[1,1]], [[1,1],[1,1]]]])
    result = empirical_joint_inventory(z, ["A","B"], ["review","decide"])
    assert result["retained_mass"] == 1
    np.testing.assert_allclose(result["probabilities"], [1/3,2/3])
    recovered = result["joint_inventories"][result["upstream_draw_to_inventory"]]
    np.testing.assert_array_equal(recovered,z)
    assert result["route_semantics_reviewed"] is False


def test_no_declaration_keeps_legacy_independent_routes():
    data = fixture()
    del data["joint_inventory_prior"]
    model = VisitHierarchy(data, Config(chains=2, draws=40, warmup=0, modeled_channels=("elapsed",), population_size=16))
    assert model.joint_inventory_prior is None
    _, routes, _, _ = model.sample()
    assert np.any(routes[:,:,0] != routes[:,:,1])


def test_upstream_replay_preserves_joint_draw_and_conditional_distribution():
    membership = np.array([[0,1,1], [0,1,1]])
    downstream = np.tile(np.array([[0,1]]), (2,4000))
    idx = replay_upstream_indices(membership, downstream, np.random.default_rng(8))
    np.testing.assert_array_equal(membership.ravel()[idx], downstream)
    frequencies = np.bincount(idx.ravel(), minlength=membership.size)/idx.size
    np.testing.assert_allclose(frequencies, [.25,.125,.125,.25,.125,.125], atol=.015)
    # Shared indices, not a separate independent draw for each upstream variable.
    a = np.arange(membership.size)
    b = 3*a+1
    np.testing.assert_array_equal(b[idx], 3*a[idx]+1)
    report = empirical_bridge_report(membership, downstream)
    assert report['upstream_particle_weight_ess'] == pytest.approx(16/3)
    assert report['maximum_reweighting_ratio'] == pytest.approx(1.5)
    assert report['upstream_mass_on_unvisited_inventories'] == 0


def test_empirical_reweighting_reports_support_collapse():
    membership = np.array([[0,1,2,3],[4,5,6,7]])
    report = empirical_bridge_report(membership, np.zeros((2,40),dtype=int))
    assert report['upstream_particle_weight_ess'] == 1
    assert report['upstream_mass_on_unvisited_inventories'] == 7/8


@pytest.mark.parametrize('membership,selected', [([[0,2]],[[0]]), ([[0,1]],[[2]]),
    ([[0.,1.]],[[0]]), ([[0,1]],[[-1]]), ([],[[0]]), ([[0,1]],[0,1])])
def test_replay_rejects_invalid_memberships(membership,selected):
    with pytest.raises(ValueError):
        replay_upstream_indices(membership,selected,np.random.default_rng(0))


def test_joint_contract_snapshot_is_not_caller_mutable():
    data=fixture()
    prior=JointInventoryPrior(data['joint_inventory_prior'],data['programs'])
    data['joint_inventory_prior']['feedback_policy']='silent_cut'
    assert prior.declaration['feedback_policy']=='downstream_evidence_updates_joint_inventory'
    with pytest.raises(ValueError, match='integer index'):
        prior.index([0.,0.])
