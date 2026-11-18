import copy

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import expit

from pipeline.procbench.process_structure.detection_hierarchy import (
    DetectionHierarchy, validate_config,
)
from pipeline.procbench.process_structure.occupancy import Config, Evidence, fit


def _ref(locator, digit="1"):
    return {"path": "source-free.md", "sha256": digit * 64, "locator": locator}


def _data(*, identity=False):
    data = {
        "schema_version": "process-occupancy-evidence/2" if identity else "process-occupancy-evidence/1",
        "scope": "source-free partial detection pooling fixture",
        "jurisdictions": ["A", "B"],
        "steps": ["apply", "interview"],
        "source_types": ["staff", "forum"],
        "source_models": {
            "staff": {"detection_beta": [2.0, 3.0], "false_positive_probability": .05},
            "forum": {"detection_beta": [3.0, 2.0], "false_positive_probability": .1},
        },
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Source-free fixture only.",
        "observations": [
            {"unit_id": "staff-A", "dependence_group_id": "staff-A", "jurisdiction_id": "A",
             "step_id": "apply", "source_type": "staff", "detected": True,
             "reviewed_scope": True, "evidence_refs": [_ref("staff-A/apply")]},
            {"unit_id": "staff-A", "dependence_group_id": "staff-A", "jurisdiction_id": "A",
             "step_id": "interview", "source_type": "staff", "detected": False,
             "reviewed_scope": True, "evidence_refs": [_ref("staff-A/interview")]},
        ],
        "known_presence": [],
    }
    if identity:
        # Contract /2 requires reviewed scopes on resolved readings as well.
        for row in data["observations"]:
            row.update(identity_scope_id="episode:A", identity_scope_reviewed=True,
                       identity_scope_refs=[_ref("episode:A", "2")])
        data["uncertain_jurisdiction_units"] = [{
            "unit_id": "forum-unknown", "dependence_group_id": "forum-unknown",
            "source_type": "forum", "identity_reviewed": True,
            "candidate_scope_complete": True,
            "assignment_prior_basis": "bounded source-free candidates",
            "assignment_prior_kind": "symmetric_bounded_context",
            "assignment_prior_refs": [_ref("identity-context", "3")],
            "identity_scope_id": "episode:unknown", "identity_scope_reviewed": True,
            "identity_scope_refs": [_ref("episode:unknown", "4")],
            "candidates": [{"jurisdiction_id": "A", "prior_weight": 1.0},
                           {"jurisdiction_id": "B", "prior_weight": 1.0}],
            "reviewed_step_ids": ["apply", "interview"],
            "readings": [
                {"step_id": "apply", "detected": True, "reviewed_scope": True,
                 "evidence_refs": [_ref("unknown/apply", "5")]},
                {"step_id": "interview", "detected": False, "reviewed_scope": True,
                 "evidence_refs": [_ref("unknown/interview", "6")]},
            ],
        }]
    return data


def _hierarchy(steps=3, sources=2, type_sd=1.2, step_sd=.45):
    a = np.tile(np.linspace(2., 3., sources), (steps, 1))
    b = np.tile(np.linspace(4., 2., sources), (steps, 1))
    return DetectionHierarchy(a, b, type_sd, step_sd)


def test_compound_normal_prior_covariance_and_centers_are_exact():
    hierarchy = _hierarchy(steps=4, sources=2, type_sd=1.3, step_sd=.6)
    expected = 1.3**2 * np.ones((4, 4)) + .6**2 * np.eye(4)
    np.testing.assert_allclose(hierarchy.covariance, expected, atol=0, rtol=0)
    np.testing.assert_allclose(hierarchy.cholesky @ hierarchy.cholesky.T,
                               expected, atol=2e-15, rtol=2e-15)
    np.testing.assert_allclose(hierarchy.logits(np.zeros((4, 2))),
                               np.tile(np.log(np.array([2/4, 3/2])), (4, 1)))


def test_integrated_type_effect_conditional_matches_gaussian_formula():
    hierarchy = _hierarchy(steps=3, sources=2, type_sd=1.1, step_sd=.7)
    white = np.array([[.3, -.2], [1.1, .4], [-.7, .9]])
    logits = hierarchy.logits(white)
    actual_mean, actual_variance = hierarchy.conditional_type_effect(logits)
    covariance = hierarchy.covariance
    cross = hierarchy.type_logit_sd**2 * np.ones(3)
    inverse = np.linalg.inv(covariance)
    centered = logits - hierarchy.center
    expected_mean = cross @ inverse @ centered
    expected_variance = hierarchy.type_logit_sd**2 - cross @ inverse @ cross
    np.testing.assert_allclose(actual_mean, expected_mean, atol=2e-15)
    assert actual_variance == pytest.approx(expected_variance, abs=2e-15)


def test_logistic_likelihood_is_stable_and_missing_opportunities_are_zero():
    hierarchy = _hierarchy(steps=2, sources=1)
    extreme = np.array([[900.], [-900.]])
    value = hierarchy.source_log_likelihood(
        extreme, 0, np.array([1, 0]), np.array([0, 1]))
    assert np.isfinite(value)
    assert value <= 0
    assert hierarchy.source_log_likelihood(
        extreme, 0, np.zeros(2, dtype=int), np.zeros(2, dtype=int)) == 0
    assert hierarchy.source_log_likelihood(
        -extreme, 0, np.zeros(2, dtype=int), np.zeros(2, dtype=int)) == 0


@pytest.mark.parametrize("mode,type_sd,step_sd", [
    ("unknown", 1., 1.), ("logit_partial_pooling", 0., 1.),
    ("logit_partial_pooling", 1., -1.), ("independent_beta", True, 1.),
])
def test_detection_configuration_fails_closed(mode, type_sd, step_sd):
    with pytest.raises(ValueError):
        validate_config(mode, type_sd, step_sd)


def test_step_varying_beta_shapes_cannot_silently_define_one_center():
    a = np.array([[2., 2.], [3., 2.]])
    b = np.full_like(a, 3.)
    with pytest.raises(ValueError, match="one declared center"):
        DetectionHierarchy(a, b, 1.5, .75)


def test_opt_in_fit_preserves_public_detection_shape_and_separate_white_state():
    config = Config(chains=2, warmup=10, draws=16, seed=1927,
                    jurisdiction_scale_log_sd=0,
                    detection_model="logit_partial_pooling")
    result, arrays = fit(_data(), config)
    assert arrays["detection"].shape == (2, 16, 2, 2)
    assert arrays["detection_white"].shape == (2, 16, 2, 2)
    assert arrays["hierarchy_white"].shape == (2, 16, 4)
    assert arrays["detection_type_effect_conditional_mean"].shape == (2, 16, 2)
    assert np.all((arrays["detection"] > 0) & (arrays["detection"] < 1))
    assert result["config"]["detection_model"] == "logit_partial_pooling"
    assert result["detection_hierarchy"]["center_source"].endswith("not a Beta prior family")
    report = result["detection_hierarchy"]["type_effect_reporting"]["staff"]
    actual = arrays["detection_type_effect_conditional_mean"][:, :, 0]
    assert report["posterior_mean"] == pytest.approx(actual.mean())
    assert report["posterior_variance"] == pytest.approx(
        actual.var() + report["conditional_variance"])
    assert any(key.startswith("detection_white:") for key in result["diagnostics"])
    assert any(key.startswith("detection_type_effect_conditional_mean:")
               for key in result["diagnostics"])


def test_one_cell_detection_posterior_matches_independent_quadrature():
    data = {
        "schema_version": "process-occupancy-evidence/1",
        "scope": "one anchored cell Gaussian-logit target check",
        "jurisdictions": ["A"], "steps": ["apply"], "source_types": ["staff"],
        "source_models": {"staff": {"detection_beta": [2., 3.],
                                      "false_positive_probability": .05}},
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Two independent source-free readings.",
        "observations": [
            {"unit_id": "positive", "dependence_group_id": "positive",
             "jurisdiction_id": "A", "step_id": "apply", "source_type": "staff",
             "detected": True, "reviewed_scope": True,
             "evidence_refs": [_ref("positive")]},
            {"unit_id": "negative", "dependence_group_id": "negative",
             "jurisdiction_id": "A", "step_id": "apply", "source_type": "staff",
             "detected": False, "reviewed_scope": True,
             "evidence_refs": [_ref("negative")]},
        ],
        "known_presence": [{"unit_id": "truth", "jurisdiction_id": "A",
                            "step_id": "apply", "present": True,
                            "basis": "explicit_presence",
                            "evidence_refs": [_ref("independent truth", "2")]}],
    }
    type_sd, step_sd = 1.5, .75
    center, sd = np.log(2/3), np.sqrt(type_sd**2 + step_sd**2)

    def unnormalized(eta):
        p = expit(eta)
        return np.exp(-.5*((eta-center)/sd)**2) * p * (1-p)

    denominator = quad(unnormalized, -np.inf, np.inf, epsabs=1e-12)[0]
    expected = quad(lambda eta: expit(eta)*unnormalized(eta),
                    -np.inf, np.inf, epsabs=1e-12)[0] / denominator
    _, arrays = fit(data, Config(chains=4, warmup=300, draws=1200, seed=91,
                                 jurisdiction_scale_log_sd=0,
                                 detection_model="logit_partial_pooling",
                                 detection_type_logit_sd=type_sd,
                                 detection_step_logit_sd=step_sd))
    assert arrays["detection"].mean() == pytest.approx(expected, abs=.02)


def test_partial_pooling_runs_with_one_shared_unknown_jurisdiction_assignment():
    data = _data(identity=True)
    config = Config(chains=2, warmup=12, draws=16, seed=187,
                    jurisdiction_scale_log_sd=0,
                    hierarchy_update="collapsed",
                    detection_model="logit_partial_pooling")
    first, arrays = fit(data, config)
    second, repeated = fit(copy.deepcopy(data), config)
    for key in arrays:
        np.testing.assert_array_equal(arrays[key], repeated[key])
    assert first == second
    assert arrays["jurisdiction_assignment"].shape == (2, 16, 1)
    np.testing.assert_allclose(
        arrays["jurisdiction_assignment_probability"].sum(axis=-1), 1., atol=2e-15)
    assert np.isfinite(arrays["conditional_presence"]).all()


def test_independent_beta_mode_does_not_expose_inactive_hierarchy_state():
    result, arrays = fit(_data(), Config(chains=2, warmup=3, draws=8,
                                         jurisdiction_scale_log_sd=0))
    assert "detection_model" not in result["config"]
    assert "detection_hierarchy" not in result
    assert "detection_white" not in arrays
    assert "detection_type_effect_conditional_mean" not in arrays
