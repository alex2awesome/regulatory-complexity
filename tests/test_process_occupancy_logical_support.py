"""Independent integration checks for normalized structural support."""
import copy
import itertools

import numpy as np
import pytest
from numpy.polynomial.hermite import hermgauss
from scipy.special import expit

from pipeline.procbench.process_structure.occupancy import (
    Config, Evidence, conditional_presence, detection_log_factors, fit,
    marginal_occupancy_log_likelihood, verify_source_bindings,
)


def fixture():
    refs = [dict(path="source-free-semantics", sha256="0"*64, locator="meanings")]
    data = dict(
        schema_version="process-occupancy-evidence/1", scope="test only",
        opportunity_frame="reviewed_units_not_selected_for_step_mentions",
        conditional_independence="assumed_given_presence_and_source_type_detection",
        assumption_note="Source-free distinct conditional reports.",
        jurisdictions=["A"], steps=["receipt", "filing"], source_types=["forum"],
        source_models={"forum": dict(detection_beta=[2., 2.], false_positive_probability=.1)},
        known_presence=[], observations=[],
        logical_support=dict(
            schema_version="process-logical-support/1", reviewed=True, scope="test only",
            evidence_role="structural_support_not_observation_or_anchor",
            basis="meaning_of_actions_not_observed_truth", review_note="No additional observation.",
            source_refs=refs,
            implications=[dict(id="receipt_requires_filing", antecedent_step_id="receipt",
                               consequent_step_id="filing", basis="meaning_of_actions_not_observed_truth",
                               note="Artificial semantic implication for kernel test.")]))
    for step, value in [("receipt", True), ("filing", False)]:
        data["observations"].append(dict(
            jurisdiction_id="A", step_id=step, source_type="forum", detected=value,
            unit_id="account", dependence_group_id="account", reviewed_scope=True,
            evidence_refs=[dict(path="source-free", sha256="1"*64, locator=step)]))
    return data


def test_occupancy_integration_uses_normalized_prior_and_joint_conditional():
    data = fixture()
    evidence = Evidence(data)
    logits, detection = np.array([[.8, -.6]]), np.array([[.7], [.4]])
    psi = expit(logits[0])
    normalizer = 1-psi[0]*(1-psi[1])
    masses, states = [], []
    for state in itertools.product([0, 1], repeat=2):
        if state == (1, 0):
            continue
        prior = np.prod([psi[s] if z else 1-psi[s] for s, z in enumerate(state)]) / normalizer
        likelihood = (detection[0, 0] if state[0] else .1)*(1-(detection[1, 0] if state[1] else .1))
        masses.append(prior*likelihood)
        states.append(state)
    expected = np.sum(np.asarray(masses)[:, None]*states, axis=0)/sum(masses)
    assert conditional_presence(logits, detection, evidence)[0] == pytest.approx(expected)
    actual = marginal_occupancy_log_likelihood(logits, detection_log_factors(detection, evidence), evidence)
    assert actual == pytest.approx(np.log(sum(masses)))
    data["observations"] = []
    empty = Evidence(data)
    assert empty.support_report()["known_present_cells"] == 0
    for value in [logits, np.array([[80., -90.]]), np.array([[-12., 14.]])]:
        assert marginal_occupancy_log_likelihood(value, detection_log_factors(detection, empty), empty) == pytest.approx(0., abs=1e-12)


def exact_quadrature():
    nodes, weights = hermgauss(24)
    a, b, u = np.meshgrid(np.sqrt(2)*nodes, np.sqrt(2)*nodes, np.sqrt(2)*nodes, indexing="ij")
    wa, wb, wu = np.meshgrid(weights, weights, weights, indexing="ij")
    measure = wa*wb*wu/np.pi**1.5
    p, q = expit(1.5*a+.5*u), expit(1.5*b+.5*u)
    normalizer = 1-p*(1-q)
    states = [(0, 0), (0, 1), (1, 1)]
    mass = []
    for i, j in states:
        prior = (p if i else 1-p)*(q if j else 1-q)/normalizer
        integrated_likelihood = (.5 if i else .1)*(.5 if j else .9)
        mass.append(np.sum(measure*prior)*integrated_likelihood)
    mass = np.asarray(mass)/sum(mass)
    means = np.sum(mass[:, None]*np.asarray(states), axis=0)
    detection_means = [.5+.1*means[0], .5-.1*means[1]]
    return states, mass, means, detection_means


@pytest.mark.parametrize("strategy", ["collapsed", "augmented"])
def test_both_sampler_targets_match_independent_quadrature(strategy):
    states, mass, means, pmeans = exact_quadrature()
    posterior, arrays = fit(fixture(), Config(chains=2, warmup=400, draws=1800, seed=9157,
        hierarchy_update=strategy, hierarchy_block_size=1, jurisdiction_scale_log_sd=0))
    z = arrays["presence"].reshape(-1, 2)
    assert not np.any((z[:, 0] == 1) & (z[:, 1] == 0))
    for state, probability in zip(states, mass):
        assert np.all(z == state, axis=1).mean() == pytest.approx(probability, abs=.045)
    assert arrays["conditional_presence"].mean(axis=(0, 1, 2)) == pytest.approx(means, abs=.035)
    assert arrays["detection"].mean(axis=(0, 1))[:, 0] == pytest.approx(pmeans, abs=.025)
    assert posterior["support"]["known_present_cells"] == 0
    assert posterior["sampler"]["target"].startswith("normalized_logically")
    np.testing.assert_array_equal(arrays["step_count"], arrays["presence"].sum(axis=-1))


def test_conflicting_anchor_and_zero_error_report_fail_before_sampling():
    data = fixture()
    data["known_presence"] = [dict(jurisdiction_id="A", step_id="filing", present=False,
        unit_id="truth", basis="explicit_absence",
        evidence_refs=[dict(path="truth", sha256="2"*64, locator="explicit")])]
    data["source_models"]["forum"]["false_positive_probability"] = 0.
    with pytest.raises(ValueError, match="contradict"):
        Evidence(data)


def test_logical_source_binding_is_consumed_not_an_ignored_sidecar(tmp_path):
    data = fixture()
    data["observations"] = []
    (tmp_path/"source-free-semantics").write_text("changed review")
    with pytest.raises(ValueError, match="Changed source binding"):
        verify_source_bindings(data, tmp_path)


def test_default_is_unchanged_when_no_structural_declaration_exists():
    data = fixture()
    del data["logical_support"]
    evidence = Evidence(data)
    assert evidence.logical_support is None
    logits, p = np.array([[.8, -.6]]), np.array([[.7], [.4]])
    factors = detection_log_factors(p, evidence)
    present, absent = -np.logaddexp(0., -logits)+factors[0], -np.logaddexp(0., logits)+factors[1]
    assert conditional_presence(logits, p, evidence) == pytest.approx(expit(present-absent))
    assert marginal_occupancy_log_likelihood(logits, factors, evidence) == pytest.approx(np.logaddexp(present, absent).sum())
