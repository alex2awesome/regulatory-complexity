"""Same-target transition checks, independent of the real-data review."""
import copy
import itertools

import numpy as np
import pytest
from numpy.polynomial.hermite import hermgauss
from scipy.special import betaln, expit

from pipeline.procbench.process_structure.occupancy import (
    Config, Evidence, detection_log_factors, fit,
    marginal_occupancy_log_likelihood,
)


def data_fixture():
    data = dict(
        schema_version="process-occupancy-evidence/1", scope="source-free kernel test",
        opportunity_frame="reviewed_units_not_selected_for_step_mentions",
        conditional_independence="assumed_given_presence_and_source_type_detection",
        assumption_note="Labeled independent test readings only.",
        jurisdictions=["A", "B"], steps=["interview"], source_types=["forum"],
        source_models={"forum": {"detection_beta": [2., 3.], "false_positive_probability": .12}},
        observations=[], known_presence=[],
    )
    for j, outcomes in [("A", [True, False]), ("B", [False])]:
        for i, outcome in enumerate(outcomes):
            unit = f"{j}{i}"
            data["observations"].append(dict(
                unit_id=unit, dependence_group_id=unit, jurisdiction_id=j,
                step_id="interview", source_type="forum", detected=outcome,
                reviewed_scope=True,
                evidence_refs=[dict(path="fixture", sha256="0"*64, locator=unit)],
            ))
    return data


@pytest.mark.parametrize("anchor", [None, False, True])
def test_marginal_likelihood_matches_direct_binary_enumeration(anchor):
    data = data_fixture()
    if anchor is not None:
        data["known_presence"].append(dict(
            jurisdiction_id="B", step_id="interview", present=anchor,
            unit_id="truth", basis="explicit_presence" if anchor else "explicit_absence",
            evidence_refs=[dict(path="independent_truth", sha256="1"*64, locator="B")]))
    e = Evidence(data)
    logits, p = np.array([[1.1], [-.8]]), np.array([[.7]])
    terms = []
    for values in itertools.product([0, 1], repeat=2):
        if anchor is not None and values[1] != int(anchor):
            continue
        probability = 1.
        for j, z in enumerate(values):
            q = expit(logits[j, 0])
            probability *= q if z else 1-q
            report = p[0, 0] if z else .12
            probability *= report**e.positive[j, 0, 0] * (1-report)**e.negative[j, 0, 0]
        terms.append(probability)
    actual = marginal_occupancy_log_likelihood(logits, detection_log_factors(p, e), e)
    assert actual == pytest.approx(np.log(sum(terms)), abs=1e-13)


def test_missing_unanchored_cells_have_no_marginal_hierarchy_likelihood():
    data = data_fixture()
    data["observations"] = []
    e = Evidence(data)
    for logits in [np.array([[-300.], [300.]]), np.array([[.2], [-.3]])]:
        assert marginal_occupancy_log_likelihood(logits, detection_log_factors([[.8]], e), e) == pytest.approx(0., abs=1e-14)


def exact_joint_mass(data, quadrature_points=28):
    """Integrate Gaussian priors independently and shared p analytically."""
    e = Evidence(data)
    nodes, weights = hermgauss(quadrature_points)
    a, u, v = np.meshgrid(np.sqrt(2)*nodes, np.sqrt(2)*nodes,
                          np.sqrt(2)*nodes, indexing="ij")
    w1, w2, w3 = np.meshgrid(weights, weights, weights, indexing="ij")
    weights3 = w1*w2*w3 / np.pi**1.5
    prior_prob = [expit(1.5*a + .5*u), expit(1.5*a + .5*v)]
    joint = {}
    p_numerator = 0.
    for values in itertools.product([0, 1], repeat=2):
        prior = np.sum(weights3 * np.prod(
            [prior_prob[j] if z else 1-prior_prob[j] for j, z in enumerate(values)], axis=0))
        n1 = sum(e.positive[j, 0, 0] for j, z in enumerate(values) if z)
        n0 = sum(e.negative[j, 0, 0] for j, z in enumerate(values) if z)
        f1 = sum(e.positive[j, 0, 0] for j, z in enumerate(values) if not z)
        f0 = sum(e.negative[j, 0, 0] for j, z in enumerate(values) if not z)
        mass = prior * np.exp(betaln(2+n1, 3+n0)-betaln(2, 3)) * .12**f1 * .88**f0
        joint[values] = mass
        p_numerator += mass*(2+n1)/(5+n1+n0)
    normalizer = sum(joint.values())
    return {key: value/normalizer for key, value in joint.items()}, p_numerator/normalizer


@pytest.mark.parametrize("strategy", ["augmented", "collapsed"])
def test_joint_samples_match_quadrature_not_just_marginal_presence(strategy):
    data = data_fixture()
    expected, expected_p = exact_joint_mass(data)
    result, draws = fit(data, Config(chains=4, warmup=400, draws=2000,
                                    jurisdiction_scale_log_sd=0, seed=9271,
                                    hierarchy_update=strategy, hierarchy_block_size=1))
    z = draws["presence"].reshape(-1, 2)
    for state, probability in expected.items():
        assert np.all(z == state, axis=1).mean() == pytest.approx(probability, abs=.035)
    assert draws["detection"].mean() == pytest.approx(expected_p, abs=.025)
    assert result["sampler"]["hierarchy_update"] == strategy
    np.testing.assert_array_equal(draws["step_count"], draws["presence"].sum(axis=-1))


def test_collapsed_anchor_and_zero_false_positive_remain_exact():
    data = data_fixture()
    data["source_models"]["forum"]["false_positive_probability"] = 0.
    data["known_presence"] = [dict(
        jurisdiction_id="B", step_id="interview", present=False, unit_id="truth",
        basis="explicit_absence",
        evidence_refs=[dict(path="independent_truth", sha256="1"*64, locator="B")])]
    _, draws = fit(data, Config(chains=2, warmup=8, draws=16, hierarchy_update="collapsed"))
    assert np.all(draws["presence"][:, :, 0] == 1)
    assert np.all(draws["presence"][:, :, 1] == 0)


@pytest.mark.parametrize("kw", [dict(hierarchy_update="wrong"),
                              dict(hierarchy_block_size=-1), dict(hierarchy_block_size=True)])
def test_strategy_and_block_validation(kw):
    with pytest.raises(ValueError):
        Config(**kw)
