import copy
import json
import math

import numpy as np
import pytest

from pipeline.procbench.process_structure.episode_prediction import (
    ATTESTATION_SCOPE, SCHEMA, episode_detection_baseline, predict_episode,
)


def fixture():
    posterior = {
        "numerically_usable": True,
        "jurisdictions": ["A", "B"],
        "steps": ["file", "interview"],
        "source_types": ["forum"],
    }
    # chain x draw x county x step; intentionally correlated with p by draw.
    q = np.array([[
        [[.2, .8], [.9, .3]],
        [[.8, .1], [.4, .9]],
    ]])
    p = np.array([[
        [[.7], [.4]],
        [[.3], [.9]],
    ]])
    episode = {
        "schema_version": SCHEMA,
        "episode_id": "fresh",
        "identity_scope_id": "thread:fresh/episode:root",
        "identity_scope_reviewed": True,
        "source_type": "forum",
        "candidate_scope_complete": True,
        "candidate_prior_outcome_independent": True,
        "assignment_prior_basis": "Pre-outcome source context",
        "candidates": [
            {"jurisdiction_id": "A", "prior_weight": .25},
            {"jurisdiction_id": "B", "prior_weight": .75},
        ],
        "reading_scope_kind": "complete_fixed_universe",
        "reviewed_step_ids": ["file", "interview"],
        "readings": [
            {"step_id": "file", "detected": True, "reviewed_scope": True},
            {"step_id": "interview", "detected": False, "reviewed_scope": True},
        ],
    }
    attestation = {
        "reviewed": True,
        "scope": ATTESTATION_SCOPE,
        "training_scope_ids": ["thread:train/episode:one"],
        "test_scope_id": episode["identity_scope_id"],
        "review_note": "Fixture source/case scopes are disjoint; helper does not prove this.",
    }
    source_models = {"forum": {"false_positive_probability": .1}}
    return posterior, {"conditional_presence": q, "detection": p}, episode, source_models, attestation


def test_two_county_two_step_matches_direct_enumeration_and_not_product_of_marginals():
    posterior, arrays, episode, source_models, attestation = fixture()
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    q, p = arrays["conditional_presence"], arrays["detection"]
    weights, f = np.array([.25, .75]), .1
    theta = np.empty((2, 2, 2))
    for d in range(2):
        for j in range(2):
            for s in range(2):
                theta[d, j, s] = f + q[0, d, j, s] * (p[0, d, s, 0] - f)
    expected_marginals = [sum(weights[j] * theta[d, j, s] for d in range(2) for j in range(2)) / 2
                          for s in range(2)]
    expected_joint = sum(
        weights[j] * theta[d, j, 0] * (1 - theta[d, j, 1])
        for d in range(2) for j in range(2)
    ) / 2
    got = [row["probability"] for row in result["marginal_predictions"]]
    assert got == pytest.approx(expected_marginals)
    assert result["whole_episode_log_predictive_density"] == pytest.approx(math.log(expected_joint))
    assert expected_joint != pytest.approx(expected_marginals[0] * (1 - expected_marginals[1]))
    assert result["one_county_shared_across_whole_episode"] is True


def test_logical_support_keeps_joint_inventory_not_product_of_marginals():
    posterior, arrays, episode, source_models, attestation = fixture()
    posterior["logical_support"] = {"test_relation": "file implies interview"}
    arrays["conditional_presence"] = np.tile([1/3, 2/3], (1, 3, 2, 1))
    arrays["detection"] = np.ones((1, 3, 2, 1))
    arrays["presence"] = np.array([[[[0, 0], [0, 0]],
                                    [[0, 1], [0, 1]],
                                    [[1, 1], [1, 1]]]], dtype=np.uint8)
    source_models["forum"]["false_positive_probability"] = 0
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    assert [r["probability"] for r in result["marginal_predictions"]] == pytest.approx([1/3, 2/3])
    # Marginal multiplication assigns positive probability to a forbidden pair.
    assert result["whole_episode_log_predictive_density"] is None
    assert result["infinite_log_loss"]
    assert result["joint_presence_integration"].startswith("aligned_joint_inventory")
    episode["readings"][1]["detected"] = True
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    assert result["whole_episode_log_predictive_density"] == pytest.approx(math.log(1/3))


@pytest.mark.parametrize("failure", ["missing", "shape", "fractional"])
def test_logical_support_prediction_requires_joint_draws(failure):
    posterior, arrays, episode, source_models, attestation = fixture()
    posterior["logical_support"] = {"test_relation": "a implies b"}
    if failure == "shape":
        arrays["presence"] = np.ones((1, 2, 2))
    elif failure == "fractional":
        arrays["presence"] = arrays["conditional_presence"]
    with pytest.raises(ValueError, match="aligned joint presence"):
        predict_episode(posterior, arrays, episode, source_models,
                        nonoverlap_attestation=attestation)


def test_outcomes_change_joint_score_not_predictions_or_candidate_weights():
    posterior, arrays, episode, source_models, attestation = fixture()
    first = predict_episode(posterior, arrays, episode, source_models,
                            nonoverlap_attestation=attestation)
    changed = copy.deepcopy(episode)
    changed["readings"][0]["detected"] = False
    changed["readings"][1]["detected"] = True
    second = predict_episode(posterior, arrays, changed, source_models,
                             nonoverlap_attestation=attestation)
    assert [r["probability"] for r in first["marginal_predictions"]] == [
        r["probability"] for r in second["marginal_predictions"]]
    assert first["candidate_prior"] == second["candidate_prior"]
    assert first["whole_episode_log_predictive_density"] != second["whole_episode_log_predictive_density"]
    assert not first["candidate_weights_updated_from_test_outcomes"]


def test_partial_scope_and_known_county_point_mass_are_supported():
    posterior, arrays, episode, source_models, attestation = fixture()
    episode["candidates"] = [{"jurisdiction_id": "B", "prior_weight": 1.0}]
    episode["reading_scope_kind"] = "reviewed_fixed_subset"
    episode["reviewed_step_ids"] = ["interview"]
    episode["readings"] = [{"step_id": "interview", "detected": False, "reviewed_scope": True}]
    episode["step_scope_reviewed"] = True
    episode["step_scope_rationale"] = "Only the captured interview span was reviewed."
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    assert [row["step_id"] for row in result["marginal_predictions"]] == ["interview"]
    assert result["candidate_prior"] == [{"jurisdiction_id": "B", "prior_weight": 1.0}]


@pytest.mark.parametrize("failure", ["weights", "duplicate_step", "attestation", "failed"])
def test_fails_closed_on_invalid_contract_or_predictive_mass(failure):
    posterior, arrays, episode, source_models, attestation = fixture()
    if failure == "weights":
        episode["candidates"][0]["prior_weight"] = .5
    elif failure == "duplicate_step":
        episode["reviewed_step_ids"] = ["file", "file"]
    elif failure == "attestation":
        attestation["reviewed"] = False
    elif failure == "failed":
        posterior["numerically_usable"] = False
    with pytest.raises(ValueError):
        predict_episode(posterior, arrays, episode, source_models,
                        nonoverlap_attestation=attestation)


@pytest.mark.parametrize(("detection", "outcome"), [(0.0, True), (1.0, False)])
def test_exactly_impossible_episode_is_retained_as_infinite_log_loss(detection, outcome):
    posterior, arrays, episode, source_models, attestation = fixture()
    arrays["conditional_presence"][:] = 1
    arrays["detection"][:] = detection
    source_models["forum"]["false_positive_probability"] = detection
    episode["readings"] = [
        {"step_id": "file", "detected": outcome, "reviewed_scope": True},
        {"step_id": "interview", "detected": outcome, "reviewed_scope": True},
    ]
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    assert result["whole_episode_log_predictive_density"] is None
    assert result["zero_predictive_probability"] is True
    assert result["infinite_log_loss"] is True
    assert all(row["probability"] == detection for row in result["marginal_predictions"])
    json.dumps(result, allow_nan=False)


def test_log_domain_avoids_naive_positive_mass_underflow():
    posterior, arrays, episode, source_models, attestation = fixture()
    posterior["steps"] = [f"s{i}" for i in range(800)]
    arrays["conditional_presence"] = np.ones((1, 1, 2, 800))
    arrays["detection"] = np.full((1, 1, 800, 1), .1)
    episode["reviewed_step_ids"] = list(posterior["steps"])
    episode["readings"] = [
        {"step_id": step, "detected": True, "reviewed_scope": True}
        for step in posterior["steps"]
    ]
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    assert result["whole_episode_log_predictive_density"] == pytest.approx(800 * math.log(.1))
    assert result["zero_predictive_probability"] is False
    assert result["infinite_log_loss"] is False


def test_many_equal_candidates_and_near_unit_weights_preserve_all_support():
    posterior, arrays, episode, source_models, attestation = fixture()
    count = 58
    posterior["jurisdictions"] = [f"J{i}" for i in range(count)]
    arrays["conditional_presence"] = np.ones((1, 1, count, 2))
    arrays["detection"] = np.ones((1, 1, 2, 1))
    source_models["forum"]["false_positive_probability"] = 0
    # Accepted decimal input is within the declared unit-sum tolerance, then
    # numerically normalized. Every positive county remains in support.
    episode["candidates"] = [
        {"jurisdiction_id": county, "prior_weight": 1 / count}
        for county in posterior["jurisdictions"]
    ]
    episode["candidates"][0]["prior_weight"] += 5e-13
    episode["readings"] = [
        {"step_id": "file", "detected": True, "reviewed_scope": True},
        {"step_id": "interview", "detected": True, "reviewed_scope": True},
    ]
    result = predict_episode(posterior, arrays, episode, source_models,
                             nonoverlap_attestation=attestation)
    weights = [candidate["prior_weight"] for candidate in result["candidate_prior"]]
    assert len(weights) == count
    assert all(weight > 0 for weight in weights)
    assert sum(weights) == pytest.approx(1, abs=1e-15)
    assert result["whole_episode_log_predictive_density"] == pytest.approx(0)
    assert not result["infinite_log_loss"]

    near_unit = copy.deepcopy(episode)
    near_unit["candidates"] = [
        {"jurisdiction_id": "J0", "prior_weight": 1 - 1e-15},
        {"jurisdiction_id": "J1", "prior_weight": 1e-15},
    ]
    preserved = predict_episode(posterior, arrays, near_unit, source_models,
                                nonoverlap_attestation=attestation)
    assert len(preserved["candidate_prior"]) == 2
    assert all(candidate["prior_weight"] > 0 for candidate in preserved["candidate_prior"])


def test_beta11_baseline_retains_unknown_county_rows_and_deduplicates_groups():
    posterior, arrays, episode, source_models, attestation = fixture()
    training = {
        "jurisdictions": posterior["jurisdictions"],
        "steps": posterior["steps"],
        "source_types": posterior["source_types"],
        "observations": [
            {"dependence_group_id": "known", "step_id": "file", "source_type": "forum", "detected": True},
        ],
        "uncertain_jurisdiction_units": [
            {"dependence_group_id": "unknown1", "source_type": "forum", "readings": [
                {"step_id": "file", "detected": False}, {"step_id": "interview", "detected": True}]},
            {"dependence_group_id": "unknown2", "source_type": "forum", "readings": [
                {"step_id": "file", "detected": True}, {"step_id": "interview", "detected": False}]},
            # Exact same group/cell is one reading opportunity, not a second count.
            {"dependence_group_id": "unknown2", "source_type": "forum", "readings": [
                {"step_id": "file", "detected": True}, {"step_id": "interview", "detected": False}]},
        ],
    }
    result = episode_detection_baseline(training, episode, nonoverlap_attestation=attestation)
    by_step = {row["step_id"]: row for row in result["marginal_predictions"]}
    assert by_step["file"]["probability"] == pytest.approx(3 / 5)  # 2/3 groups detected plus Beta(1,1)
    assert by_step["file"]["independent_training_groups"] == 3
    assert by_step["file"]["uncertain_county_training_groups"] == 2
    assert by_step["interview"]["probability"] == pytest.approx(1 / 2)  # 1/2 groups detected
    assert by_step["interview"]["independent_training_groups"] == 2
    assert by_step["interview"]["uncertain_county_training_groups"] == 2
    assert result["unknown_county_training_rows_retained"]
    assert result["dependence_groups_deduplicated"]


def test_baseline_rejects_conflicting_duplicate_group_cell():
    posterior, arrays, episode, source_models, attestation = fixture()
    training = {
        "jurisdictions": posterior["jurisdictions"], "steps": posterior["steps"],
        "source_types": posterior["source_types"],
        "observations": [
            {"dependence_group_id": "g", "step_id": "file", "source_type": "forum", "detected": True},
            {"dependence_group_id": "g", "step_id": "file", "source_type": "forum", "detected": False},
        ],
        "uncertain_jurisdiction_units": [],
    }
    with pytest.raises(ValueError, match="Conflicting"):
        episode_detection_baseline(training, episode, nonoverlap_attestation=attestation)
