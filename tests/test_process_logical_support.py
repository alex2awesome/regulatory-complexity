import copy
import itertools
import math

import numpy as np
import pytest
from scipy.special import expit, logsumexp

from pipeline.procbench.process_structure.logical_support import (
    BASIS, EVIDENCE_ROLE, LogicalSupport, MAX_COMPONENT_SIZE, SCHEMA,
)


def ref(locator="fixture:logical-support"):
    return {"path": "fixture.json", "sha256": "a" * 64, "locator": locator}


def implication(identifier, antecedent, consequent, *, with_refs=False):
    row = {
        "id": identifier,
        "antecedent_step_id": antecedent,
        "consequent_step_id": consequent,
        "basis": BASIS,
        "note": f"Fixture meaning rule {antecedent} implies {consequent}.",
    }
    if with_refs:
        row["source_refs"] = [ref(f"fixture:{identifier}")]
    return row


def declaration(*rows):
    return {
        "schema_version": SCHEMA,
        "reviewed": True,
        "scope": "source_free_fixture_scope",
        "evidence_role": EVIDENCE_ROLE,
        "basis": BASIS,
        "review_note": "Fixture semantics reviewed; not an observed truth anchor.",
        "source_refs": [ref()],
        "implications": list(rows),
    }


def factors(shape):
    return np.zeros(shape), np.zeros(shape)


def anchors(shape):
    return np.full(shape, -1, dtype=np.int8)


def brute(logits, present, absent, fixed, pairs):
    """Independent reference over the full state space, one jurisdiction."""
    states, log_prior, log_joint = [], [], []
    for raw in itertools.product((0, 1), repeat=len(logits)):
        state = np.asarray(raw, dtype=bool)
        if any(state[a] and not state[b] for a, b in pairs):
            continue
        one = -np.logaddexp(0, -logits)
        zero = -np.logaddexp(0, logits)
        prior = float(np.sum(np.where(state, one, zero)))
        states.append(state)
        log_prior.append(prior)
        if any(value >= 0 and state[index] != bool(value) for index, value in enumerate(fixed)):
            log_joint.append(-math.inf)
        else:
            log_joint.append(prior + float(np.sum(np.where(state, present, absent))))
    states = np.asarray(states)
    log_prior, log_joint = np.asarray(log_prior), np.asarray(log_joint)
    log_z = float(logsumexp(log_prior))
    log_numerator = float(logsumexp(log_joint))
    if log_numerator == -math.inf:
        return -math.inf, None
    weights = np.exp(log_joint - log_numerator)
    return log_numerator - log_z, weights @ states


def test_two_step_normalizer_matches_closed_form_and_forbidden_state_is_impossible():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    probabilities = np.array([.3, .4])
    logits = np.log(probabilities / (1 - probabilities))[None, :]
    z_value = 1 - probabilities[0] * (1 - probabilities[1])
    expected_00 = math.log((1 - probabilities[0]) * (1 - probabilities[1])) - math.log(z_value)
    assert support.prior_log_probability(logits, np.array([[0, 0]], dtype=int)) == pytest.approx(expected_00)
    assert support.prior_log_probability(logits, np.array([[1, 0]], dtype=int)) == -math.inf
    marginal = support.conditional_probabilities(logits, factors(logits.shape), anchors(logits.shape))[0]
    assert marginal == pytest.approx([
        probabilities[0] * probabilities[1] / z_value,
        probabilities[1] / z_value,
    ])


def test_no_data_marginal_is_zero_for_every_logit_not_fake_hierarchy_evidence():
    support = LogicalSupport(
        ["A", "B", "C", "D"],
        declaration(
            implication("a_to_b", "A", "B"),
            implication("b_to_c", "B", "C"),
        ),
    )
    logits = np.array([
        [-12.0, -3.0, .2, 8.0],
        [11.0, 2.5, -7.0, -4.0],
        [.1, .2, .3, .4],
    ])
    assert support.marginal_log_likelihood(
        logits, factors(logits.shape), anchors(logits.shape)) == pytest.approx(0, abs=1e-13)


def test_three_step_chain_matches_independent_full_enumeration_with_anchors_and_factors():
    pairs = [(0, 1), (1, 2)]
    support = LogicalSupport(
        ["A", "B", "C"],
        declaration(implication("a_to_b", "A", "B"), implication("b_to_c", "B", "C")),
    )
    logits = np.array([[-.7, .2, 1.1], [1.2, -.4, .5]])
    present = np.array([[.1, -.3, .4], [-.2, .6, -.1]])
    absent = np.array([[-.5, .2, -.2], [.3, -.4, .2]])
    fixed = np.array([[-1, -1, 1], [0, -1, -1]], dtype=int)
    expected_log, expected_probability = 0.0, []
    for row in range(2):
        value, probability = brute(
            logits[row], present[row], absent[row], fixed[row], pairs)
        expected_log += value
        expected_probability.append(probability)
    assert support.marginal_log_likelihood(logits, (present, absent), fixed) == pytest.approx(expected_log)
    assert support.conditional_probabilities(logits, (present, absent), fixed) == pytest.approx(
        np.asarray(expected_probability))


def test_four_steps_with_disconnected_component_and_independent_cells_match_full_enumeration():
    support = LogicalSupport(
        ["A", "B", "C", "D"], declaration(implication("a_to_b", "A", "B")))
    logits = np.array([[.8, -.9, .3, -1.4]])
    present = np.array([[.2, -.1, -.4, .7]])
    absent = np.array([[-.3, .5, .1, -.2]])
    fixed = np.full((1, 4), -1, dtype=int)
    expected_log, expected_probability = brute(
        logits[0], present[0], absent[0], fixed[0], [(0, 1)])
    assert support.marginal_log_likelihood(logits, (present, absent), fixed) == pytest.approx(expected_log)
    assert support.conditional_probabilities(logits, (present, absent), fixed)[0] == pytest.approx(
        expected_probability)


def test_negative_infinity_detection_factors_select_a_valid_state_without_nan():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    logits = np.zeros((3, 2))
    present = np.zeros_like(logits)
    absent = np.zeros_like(logits)
    present[:, 0] = -math.inf  # A must be absent.
    absent[:, 1] = -math.inf   # B must be present.
    fixed = anchors(logits.shape)
    assert math.isfinite(support.marginal_log_likelihood(logits, (present, absent), fixed))
    assert support.conditional_probabilities(logits, (present, absent), fixed) == pytest.approx(
        np.tile([0.0, 1.0], (3, 1)))
    sample = support.sample(logits, (present, absent), fixed, np.random.default_rng(4))
    assert np.array_equal(sample, np.tile([False, True], (3, 1)))


def test_impossible_factor_combination_is_negative_infinity_and_cannot_be_sampled():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    logits = np.zeros((1, 2))
    # These factors demand forbidden A=1,B=0.
    present = np.array([[0.0, -math.inf]])
    absent = np.array([[-math.inf, 0.0]])
    fixed = anchors(logits.shape)
    assert support.marginal_log_likelihood(logits, (present, absent), fixed) == -math.inf
    with pytest.raises(FloatingPointError, match="no positive mass"):
        support.conditional_probabilities(logits, (present, absent), fixed)
    with pytest.raises(FloatingPointError, match="no positive mass"):
        support.sample(logits, (present, absent), fixed, np.random.default_rng(5))


def test_anchors_restrict_numerator_but_not_structural_prior_normalizer():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    logits = np.array([[.4, -.2]])
    fixed = np.array([[1, 1]], dtype=int)
    p = expit(logits[0])
    z_value = 1 - p[0] * (1 - p[1])
    expected = math.log(p[0] * p[1]) - math.log(z_value)
    assert support.marginal_log_likelihood(logits, factors(logits.shape), fixed) == pytest.approx(expected)
    with pytest.raises(ValueError, match="contradict"):
        support.validate_anchors(np.array([[1, 0]], dtype=int))


def test_joint_sampler_preserves_implication_and_nonfactorized_count_dependence():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    size = 20_000
    logits = np.zeros((size, 2))
    draws = support.sample(
        logits, factors(logits.shape), anchors(logits.shape), np.random.default_rng(20260921))
    assert not np.any(draws[:, 0] & ~draws[:, 1])
    assert draws.mean(axis=0) == pytest.approx([1 / 3, 2 / 3], abs=.015)
    joint = np.mean(draws[:, 0] & draws[:, 1])
    product_of_marginals = float(draws[:, 0].mean() * draws[:, 1].mean())
    assert joint == pytest.approx(1 / 3, abs=.015)
    assert abs(joint - product_of_marginals) > .08


@pytest.mark.parametrize("problem", [
    "unknown", "self", "duplicate_pair", "duplicate_id", "bad_basis", "bad_refs", "unhashable",
])
def test_malformed_implications_fail_closed(problem):
    rows = [implication("a_to_b", "A", "B")]
    if problem == "unknown":
        rows[0]["consequent_step_id"] = "missing"
    elif problem == "self":
        rows[0]["consequent_step_id"] = "A"
    elif problem == "duplicate_pair":
        rows.append(implication("again", "A", "B"))
    elif problem == "duplicate_id":
        rows.append(implication("a_to_b", "B", "C"))
    elif problem == "bad_basis":
        rows[0]["basis"] = "observed_truth"
    elif problem == "bad_refs":
        rows[0]["source_refs"] = [{"path": "x", "sha256": "bad", "locator": "x"}]
    else:
        rows[0]["antecedent_step_id"] = []
    with pytest.raises(ValueError):
        LogicalSupport(["A", "B", "C"], declaration(*rows))


def test_large_connected_component_fails_before_exponential_enumeration():
    steps = [f"s{index}" for index in range(MAX_COMPONENT_SIZE + 1)]
    rows = [implication(f"edge{index}", steps[index], steps[index + 1])
            for index in range(MAX_COMPONENT_SIZE)]
    with pytest.raises(ValueError, match="maximum"):
        LogicalSupport(steps, declaration(*rows))


def test_report_is_explicitly_structural_and_not_an_evidence_or_route_claim():
    supplied = declaration(implication("a_to_b", "A", "B", with_refs=True))
    support = LogicalSupport(["A", "B", "C"], supplied)
    report = support.as_report()
    assert report["declaration"] == supplied
    assert report["method"].startswith("exact_connected_component_enumeration")
    assert report["anchors_restrict_likelihood_not_prior_normalizer"] is True
    assert report["components"] == [{
        "step_ids": ["A", "B"],
        "implication_ids": ["a_to_b"],
        "allowed_state_count": 3,
        "unconstrained_binary_state_count": 4,
    }]
    assert report["unconstrained_step_ids"] == ["C"]
    assert "does not infer participation" in report["qualification"]


def test_input_shape_dtype_and_factor_contracts_fail_closed():
    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    logits = np.zeros((1, 2))
    with pytest.raises(ValueError, match="factors"):
        support.marginal_log_likelihood(logits, list(factors(logits.shape)), anchors(logits.shape))
    with pytest.raises(ValueError, match="anchors"):
        support.validate_anchors(np.array([[-1.0, -1.0]]))
    with pytest.raises(ValueError, match="binary"):
        support.prior_log_probability(logits, np.array([[0.0, 1.0]]))
    with pytest.raises(ValueError, match="Generator"):
        support.sample(logits, factors(logits.shape), anchors(logits.shape), None)


def test_declaration_is_deep_copied():
    supplied = declaration(implication("a_to_b", "A", "B"))
    support = LogicalSupport(["A", "B"], supplied)
    supplied["implications"][0]["note"] = "mutated"
    assert support.as_report()["declaration"]["implications"][0]["note"] != "mutated"


@pytest.mark.parametrize("uniform", [0., np.nextafter(1., 0.)])
def test_inverse_cdf_never_selects_zero_mass_anchor_excluded_state(uniform):
    class BoundaryGenerator(np.random.Generator):
        def random(self, size=None, **kwargs):
            return np.full(size, uniform)

    support = LogicalSupport(["A", "B"], declaration(implication("a_to_b", "A", "B")))
    logits = np.array([[.7, -1.3], [100., -120.]])
    # Only 01 is compatible; both leading 00 and trailing 11 have zero mass.
    fixed = np.tile([0, 1], (2, 1))
    sample = support.sample(logits, factors(logits.shape), fixed,
                            BoundaryGenerator(np.random.PCG64(3)))
    assert np.array_equal(sample, fixed.astype(bool))
    marginal = support.conditional_probabilities(logits, factors(logits.shape), fixed)
    assert np.array_equal(marginal, fixed)
