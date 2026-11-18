"""Posterior prediction for one fresh reviewed episode with uncertain county.

The county prior is fixed before seeing the scored outcomes and one county is
shared by the whole checklist.  This module predicts source mentions, not
latent action truth, and does not update or infer the supplied county weights.
"""
from __future__ import annotations

import copy
import math

import numpy as np
from scipy.special import logsumexp as _scipy_logsumexp


SCHEMA = "process-structure-fresh-episode/1"
ATTESTATION_SCOPE = "reviewed_train_test_episode_and_source_lineage_nonoverlap"


def _logsumexp(values, axis=None):
    values = np.asarray(values, dtype=np.float64)
    result = _scipy_logsumexp(values, axis=axis)
    return result if axis is not None else float(result)


def _attestation(value, identity_scope_id):
    if not isinstance(value, dict):
        raise ValueError("Fresh-episode scoring requires an explicit train/test nonoverlap attestation")
    training = value.get("training_scope_ids")
    if (value.get("reviewed") is not True or value.get("scope") != ATTESTATION_SCOPE
            or value.get("test_scope_id") != identity_scope_id
            or not isinstance(training, list) or not training
            or any(not isinstance(item, str) or not item.strip() for item in training)
            or len(set(training)) != len(training) or identity_scope_id in training
            or not isinstance(value.get("review_note"), str) or not value["review_note"].strip()):
        raise ValueError("Invalid reviewed train/test nonoverlap attestation")
    return copy.deepcopy(value)


def _episode(value, jurisdictions, steps, source_types):
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("Need one normalized fresh-episode contract")
    episode_id, scope_id = value.get("episode_id"), value.get("identity_scope_id")
    if (not isinstance(episode_id, str) or not episode_id.strip()
            or not isinstance(scope_id, str) or not scope_id.strip()
            or value.get("identity_scope_reviewed") is not True
            or value.get("candidate_scope_complete") is not True
            or value.get("candidate_prior_outcome_independent") is not True
            or not isinstance(value.get("assignment_prior_basis"), str)
            or not value["assignment_prior_basis"].strip()
            or value.get("source_type") not in source_types):
        raise ValueError("Episode identity, source type and outcome-independent candidate context must be reviewed")
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Episode needs a normalized county candidate prior")
    seen, ids, weights = set(), [], []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid county candidate")
        county, weight = candidate.get("jurisdiction_id"), candidate.get("prior_weight")
        if (county not in jurisdictions or county in seen or isinstance(weight, bool)
                or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight <= 0):
            raise ValueError("County candidate weights must be distinct, finite and positive")
        seen.add(county)
        ids.append(county)
        weights.append(float(weight))
    weights = np.asarray(weights, dtype=np.float64)
    total_weight = float(weights.sum())
    if not math.isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("Fresh-episode county weights must already be normalized")
    weights /= total_weight
    if np.any(weights <= 0):
        raise ValueError("Numerical candidate-weight normalization removed positive county support")

    reviewed, rows = value.get("reviewed_step_ids"), value.get("readings")
    if (not isinstance(reviewed, list) or not reviewed
            or any(not isinstance(step, str) or step not in steps for step in reviewed)
            or len(set(reviewed)) != len(reviewed)
            or not isinstance(rows, list) or len(rows) != len(reviewed)):
        raise ValueError("Episode needs a nonempty distinct reviewed step checklist")
    scope_kind = value.get("reading_scope_kind")
    if scope_kind == "complete_fixed_universe":
        if set(reviewed) != set(steps):
            raise ValueError("Complete episode checklist must cover the fitted step universe")
    elif scope_kind == "reviewed_fixed_subset":
        if (value.get("step_scope_reviewed") is not True
                or not isinstance(value.get("step_scope_rationale"), str)
                or not value["step_scope_rationale"].strip()):
            raise ValueError("Partial episode checklist needs reviewed scope metadata")
    else:
        raise ValueError("Unknown episode reading scope")
    by_step = {}
    for row in rows:
        if (not isinstance(row, dict) or row.get("step_id") not in reviewed
                or row["step_id"] in by_step or type(row.get("detected")) is not bool
                or row.get("reviewed_scope") is not True):
            raise ValueError("Need exactly one reviewed boolean reading per episode step")
        by_step[row["step_id"]] = bool(row["detected"])
    if set(by_step) != set(reviewed):
        raise ValueError("Episode readings do not match reviewed step scope")
    return {
        "episode_id": episode_id,
        "identity_scope_id": scope_id,
        "source_type": value["source_type"],
        "candidate_ids": ids,
        "candidate_weights": weights,
        "assignment_prior_basis": value["assignment_prior_basis"],
        "reviewed_steps": list(reviewed),
        "outcomes": by_step,
        "scope_kind": scope_kind,
    }


def _draws(posterior, arrays):
    if not isinstance(posterior, dict) or posterior.get("numerically_usable") is not True:
        raise ValueError("Cannot score a numerically failed posterior")
    for field in ("jurisdictions", "steps", "source_types"):
        values = posterior.get(field)
        if (not isinstance(values, list) or not values or len(set(values)) != len(values)
                or any(not isinstance(item, str) for item in values)):
            raise ValueError("Posterior is missing a distinct fitted universe")
    if not isinstance(arrays, dict) or "conditional_presence" not in arrays or "detection" not in arrays:
        raise ValueError("Need aligned conditional-presence and detection draws")
    raw_q, raw_p = np.asarray(arrays["conditional_presence"]), np.asarray(arrays["detection"])
    for raw in (raw_q, raw_p):
        if (raw.dtype.kind not in "iuf" or raw.dtype.kind == "b"):
            raise ValueError("Prediction draws must be real numeric arrays")
    q, p = raw_q.astype(np.float64), raw_p.astype(np.float64)
    expected_q = (len(posterior["jurisdictions"]), len(posterior["steps"]))
    expected_p = (len(posterior["steps"]), len(posterior["source_types"]))
    if (q.ndim != 4 or p.ndim != 4 or q.shape[:2] != p.shape[:2] or not q.shape[0] or not q.shape[1]
            or q.shape[2:] != expected_q or p.shape[2:] != expected_p
            or not np.isfinite(q).all() or not np.isfinite(p).all()
            or np.any((q < 0) | (q > 1)) or np.any((p < 0) | (p > 1))):
        raise ValueError("Invalid aligned conditional-presence/detection draws")
    return q, p


def predict_episode(posterior, arrays, episode, source_models, *, nonoverlap_attestation):
    """Score a fresh whole checklist while sharing one unknown county.

    Candidate weights are fixed prior/context weights.  They are mixed outside
    the within-county checklist product and are never updated with test outcomes.
    """
    q, p = _draws(posterior, arrays)
    parsed = _episode(episode, posterior["jurisdictions"], posterior["steps"], posterior["source_types"])
    attestation = _attestation(nonoverlap_attestation, parsed["identity_scope_id"])
    if not isinstance(source_models, dict) or parsed["source_type"] not in source_models:
        raise ValueError("Missing source model for fresh episode")
    f = source_models[parsed["source_type"]].get("false_positive_probability")
    if (isinstance(f, bool) or not isinstance(f, (int, float))
            or not math.isfinite(f) or not 0 <= f <= 1):
        raise ValueError("Invalid false-positive probability")
    f = float(f)
    ji = {value: index for index, value in enumerate(posterior["jurisdictions"])}
    si = {value: index for index, value in enumerate(posterior["steps"])}
    ki = posterior["source_types"].index(parsed["source_type"])
    candidate_indices = [ji[value] for value in parsed["candidate_ids"]]
    weights = parsed["candidate_weights"]

    # D x H x R: aligned draw, candidate county and reviewed step.
    probabilities = np.stack([
        f + q[:, :, candidate_indices, si[step]] *
        (p[:, :, si[step], ki][:, :, None] - f)
        for step in parsed["reviewed_steps"]
    ], axis=-1)
    if not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError("Nonfinite fresh-episode predictive probability")

    marginals = []
    for index, step in enumerate(parsed["reviewed_steps"]):
        value = float(np.mean(np.sum(probabilities[..., index] * weights[None, None, :], axis=2)))
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid marginal episode prediction")
        marginals.append({
            "step_id": step,
            "probability": value,
            "detected": parsed["outcomes"][step],
            "target": "fresh_episode_source_detection_not_latent_action_presence",
        })

    outcomes = np.asarray([parsed["outcomes"][step] for step in parsed["reviewed_steps"]], dtype=bool)
    joint_probabilities = probabilities
    joint_integration = "conditionally_independent_binary_presence_integrated_per_step"
    if posterior.get("logical_support") is not None:
        # Constraints couple steps even conditional on the continuous state.
        # Rao-Blackwellized marginals above remain valid, but their product is
        # NOT a whole-episode likelihood. Preserve aligned joint inventory draws.
        z = np.asarray(arrays.get("presence"))
        if (z.shape != q.shape or z.dtype.kind not in "biuf"
                or not np.isfinite(z).all() or not np.isin(z, [0, 1]).all()):
            raise ValueError("Constrained whole-episode prediction needs aligned joint presence draws")
        joint_probabilities = np.stack([
            np.where(z[:, :, candidate_indices, si[step]],
                     p[:, :, si[step], ki][:, :, None], f)
            for step in parsed["reviewed_steps"]
        ], axis=-1)
        joint_integration = "aligned_joint_inventory_monte_carlo_not_product_of_presence_marginals"
    with np.errstate(divide="ignore", invalid="ignore"):
        log_cells = np.where(outcomes[None, None, None, :],
                             np.log(joint_probabilities), np.log1p(-joint_probabilities))
    log_by_candidate = np.sum(log_cells, axis=-1)
    log_weights = np.log(weights)
    log_by_draw = _logsumexp(log_by_candidate + log_weights[None, None, :], axis=2)
    log_score = _logsumexp(log_by_draw.reshape(-1)) - math.log(log_by_draw.size)
    if math.isnan(log_score) or log_score == math.inf:
        raise ValueError("Whole-episode predictive density is numerically unresolved")
    zero_probability = log_score == -math.inf
    return {
        "schema_version": "process-structure-fresh-episode-prediction/1",
        "episode_id": parsed["episode_id"],
        "identity_scope_id": parsed["identity_scope_id"],
        "source_type": parsed["source_type"],
        "candidate_prior": [
            {"jurisdiction_id": county, "prior_weight": float(weight)}
            for county, weight in zip(parsed["candidate_ids"], weights)
        ],
        "assignment_prior_basis": parsed["assignment_prior_basis"],
        "candidate_prior_outcome_independent": True,
        "candidate_weights_updated_from_test_outcomes": False,
        "one_county_shared_across_whole_episode": True,
        "reading_scope_kind": parsed["scope_kind"],
        "marginal_predictions": marginals,
        "whole_episode_log_predictive_density": None if zero_probability else float(log_score),
        "zero_predictive_probability": zero_probability,
        "infinite_log_loss": zero_probability,
        "target": "fresh_episode_source_mentions_not_unseen_jurisdiction_or_latent_presence_truth",
        "conditional_independence": "step_mentions_conditionally_independent_given_saved_presence_detection_state_and_shared_county",
        "joint_presence_integration": joint_integration,
        "scientific_presence_validation": False,
        "nonoverlap_attestation": attestation,
        "qualification": "Reviewed candidate weights are normalized by their near-unit sum without deleting support or using test outcomes. The helper requires but cannot prove the caller's source/case nonoverlap review.",
    }


def episode_detection_baseline(training, episode, *, nonoverlap_attestation):
    """Beta(1,1) pooled source-step mention baseline for a fresh episode.

    Resolved and uncertain-county training episodes both count.  Jurisdiction is
    irrelevant to this baseline; an independent dependence group contributes at
    most once to a source/step cell.
    """
    if not isinstance(training, dict):
        raise ValueError("Need normalized training evidence")
    parsed = _episode(episode, training.get("jurisdictions", []), training.get("steps", []),
                      training.get("source_types", []))
    attestation = _attestation(nonoverlap_attestation, parsed["identity_scope_id"])
    cells = {}

    def add(group, step, source_type, detected, origin):
        if (not isinstance(group, str) or not group.strip() or step not in training["steps"]
                or source_type not in training["source_types"] or type(detected) is not bool):
            raise ValueError("Invalid training reading for mention baseline")
        key = group, step, source_type
        if key in cells and cells[key][0] != detected:
            raise ValueError("Conflicting duplicate dependence-group reading")
        cells.setdefault(key, (detected, origin))

    for row in training.get("observations", []):
        add(row.get("dependence_group_id"), row.get("step_id"), row.get("source_type"),
            row.get("detected"), "resolved")
    for unit in training.get("uncertain_jurisdiction_units", []):
        for row in unit.get("readings", []):
            add(unit.get("dependence_group_id"), row.get("step_id"), unit.get("source_type"),
                row.get("detected"), "uncertain")

    predictions = []
    for step in parsed["reviewed_steps"]:
        matching = [value for (group, candidate_step, source_type), value in cells.items()
                    if candidate_step == step and source_type == parsed["source_type"]]
        detected = sum(value[0] for value in matching)
        predictions.append({
            "step_id": step,
            "probability": (1 + detected) / (2 + len(matching)),
            "independent_training_groups": len(matching),
            "detected_training_groups": detected,
            "uncertain_county_training_groups": sum(value[1] == "uncertain" for value in matching),
            "target": "pooled_source_step_mention_rate_not_latent_presence",
        })
    return {
        "schema_version": "process-structure-fresh-episode-mention-baseline/1",
        "episode_id": parsed["episode_id"],
        "source_type": parsed["source_type"],
        "prior": "Beta(1,1)",
        "marginal_predictions": predictions,
        "unknown_county_training_rows_retained": True,
        "dependence_groups_deduplicated": True,
        "nonoverlap_attestation": attestation,
        "qualification": "Pooled mention baseline; county identity and latent action presence are not modeled.",
    }
