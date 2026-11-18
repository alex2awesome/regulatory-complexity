"""Held-out reading prediction, explicitly distinct from latent-presence truth.

This evaluates whether the model predicts what an unseen source will mention.
It cannot validate that an unmentioned action is absent from an implementation.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path

import numpy as np

from .occupancy import Evidence


def leave_jurisdiction_readings_out(data, jurisdiction, *, source_root=None,
                                    uncertain_identity_policy=None):
    """Withhold all readings/anchors for a county; require reviewed lineage.

    This compact helper rejects shared source files/hashes across the split,
    rather than silently guessing which reference derivative can be retained.
    Taxonomy and priors are supplied/fixed outside this helper.

    By default, an unresolved identity unit fails closed.  With the explicit
    ``exclude_candidate_overlap`` policy, an entire unresolved episode is
    excluded from training when any of its reviewed jurisdiction candidates is
    held out.  Candidate weights are copied unchanged for disjoint units; no
    posterior identity is consulted.  The explicit policy places a receipt
    describing the excluded identity units in ``training["holdout_receipt"]``;
    the historical two-value return is retained for both policies.
    """
    Evidence(data)
    uncertain = data.get("uncertain_jurisdiction_units", [])
    if uncertain_identity_policy not in {None, "exclude_candidate_overlap"}:
        raise ValueError("Unknown uncertain identity holdout policy")
    if uncertain and uncertain_identity_policy is None:
        raise ValueError("Uncertain identity holdouts require an explicit candidate/lineage exclusion policy")
    if jurisdiction not in data["jurisdictions"] or len(data["jurisdictions"]) < 2:
        raise ValueError("Need a held-out jurisdiction and at least one training jurisdiction")
    held = [copy.deepcopy(r) for r in data["observations"] if r["jurisdiction_id"] == jurisdiction]
    if not held:
        raise ValueError("No held-out readings to score")
    root = Path(source_root if source_root is not None else Path.cwd()).resolve()

    def validate_refs(refs):
        for ref in refs:
            if (not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not ref["path"]
                    or not isinstance(ref.get("locator"), str) or not ref["locator"]
                    or not isinstance(ref.get("sha256"), str) or len(ref["sha256"]) != 64
                    or any(c not in "0123456789abcdef" for c in ref["sha256"])):
                raise ValueError("Invalid reviewed source-lineage binding")

    def support_sets(refs):
        validate_refs(refs)
        return ({str((root / ref["path"]).resolve()) for ref in refs},
                {ref["sha256"] for ref in refs})

    def supports(rows):
        refs = [ref for row in rows for ref in row["evidence_refs"] + row.get("lineage_refs", [])]
        return support_sets(refs)

    held_anchors = [r for r in data["known_presence"] if r["jurisdiction_id"] == jurisdiction]
    held_paths, held_hashes = supports(held + held_anchors)
    train = copy.deepcopy(data)
    train["observations"] = [r for r in train["observations"] if r["jurisdiction_id"] != jurisdiction]
    train["known_presence"] = [r for r in train["known_presence"] if r["jurisdiction_id"] != jurisdiction]
    excluded_identity_units = []
    retained_identity_units = []
    if uncertain_identity_policy == "exclude_candidate_overlap":
        retained_units = []
        for unit in train.get("uncertain_jurisdiction_units", []):
            candidates = copy.deepcopy(unit.get("candidates", []))
            candidate_ids = [candidate.get("jurisdiction_id") for candidate in candidates]
            unit_refs = list(unit.get("identity_scope_refs", []))
            unit_refs.extend(unit.get("assignment_prior_refs", []))
            unit_refs.extend(unit.get('step_scope_refs', []))
            unit_refs.extend(unit.get("lineage_refs", []))
            for reading in unit.get("readings", []):
                unit_refs.extend(reading.get("evidence_refs", []))
                unit_refs.extend(reading.get("lineage_refs", []))
            unit_paths, unit_hashes = support_sets(unit_refs)
            if jurisdiction in candidate_ids:
                excluded_identity_units.append({
                    "unit_id": unit.get("unit_id"),
                    "dependence_group_id": unit.get("dependence_group_id"),
                    "reason": "candidate_set_intersects_heldout_jurisdiction",
                    "original_candidates": candidates,
                })
            elif unit_paths & held_paths or unit_hashes & held_hashes:
                excluded_identity_units.append({
                    "unit_id": unit.get("unit_id"),
                    "dependence_group_id": unit.get("dependence_group_id"),
                    "reason": "source_lineage_overlaps_heldout_target",
                    "original_candidates": candidates,
                })
            else:
                if (unit.get("lineage_reviewed") is not True
                        or not isinstance(unit.get("lineage_refs"), list)):
                    raise ValueError("Retained disjoint uncertain identity unit requires reviewed source lineage")
                retained_units.append(unit)
                retained_identity_units.append({
                    "unit_id": unit.get("unit_id"),
                    "dependence_group_id": unit.get("dependence_group_id"),
                    "reason": "candidate_set_disjoint_from_heldout_jurisdiction",
                    "original_candidates": candidates,
                })
        train["uncertain_jurisdiction_units"] = retained_units
    for row in data["observations"]:
        if row.get("lineage_reviewed") is not True or not isinstance(row.get("lineage_refs"), list):
            raise ValueError("Held-out reading evaluation requires reviewed source lineage")

    train_paths, train_hashes = supports(train["observations"] + train["known_presence"])
    if held_paths & train_paths or held_hashes & train_hashes:
        raise ValueError("Held-out sources or declared derivatives overlap the training evidence")
    Evidence(train)
    if uncertain_identity_policy == "exclude_candidate_overlap":
        receipt = {
            "schema_version": "process-structure-prediction-holdout-receipt/1",
            "heldout_jurisdictions": [jurisdiction],
            "target": "known_county_source_mentions_not_latent_presence_truth",
            "uncertain_identity_policy": uncertain_identity_policy,
            "excluded_identity_units": excluded_identity_units,
            "retained_disjoint_identity_units": retained_identity_units,
            "candidate_weights_renormalized": False,
            "posterior_identity_used": False,
            "identity_scope": "whole_episode_candidate_set",
            "lineage_overlap_checked": True,
        }
        train["holdout_receipt"] = receipt
    return train, held


def prediction_key(row):
    return row["dependence_group_id"], row["jurisdiction_id"], row["step_id"], row["source_type"]


def predict_readings(posterior, arrays, observations, source_models):
    """Integrate z and p jointly, not E[z] * E[p].

    The conditional_presence array is evaluated at each saved hierarchy and p.
    It is therefore valid for Rao–Blackwell prediction of a fresh reading.
    Callers must actually withhold the scored observations and their lineage.
    """
    if not posterior.get("numerically_usable"):
        raise ValueError("Cannot score a numerically failed posterior as a valid prediction")
    js = {x: i for i, x in enumerate(posterior["jurisdictions"])}
    ss = {x: i for i, x in enumerate(posterior["steps"])}
    ks = {x: i for i, x in enumerate(posterior["source_types"])}
    q, p = np.asarray(arrays["conditional_presence"]), np.asarray(arrays["detection"])
    if (q.ndim != 4 or p.ndim != 4 or q.shape[:2] != p.shape[:2]
            or q.shape[2:] != (len(js), len(ss)) or p.shape[2:] != (len(ss), len(ks))
            or not np.isfinite(q).all() or not np.isfinite(p).all()
            or np.any((q < 0) | (q > 1)) or np.any((p < 0) | (p > 1))):
        raise ValueError("Invalid aligned joint presence/detection draws")
    predictions = []
    for row in observations:
        j, s, k = js[row["jurisdiction_id"]], ss[row["step_id"]], ks[row["source_type"]]
        f = source_models[row["source_type"]]["false_positive_probability"]
        values = f + q[:, :, j, s]*(p[:, :, s, k]-f)
        predictions.append(dict(dependence_group_id=row["dependence_group_id"],
            jurisdiction_id=row["jurisdiction_id"], step_id=row["step_id"], source_type=row["source_type"],
            probability=float(values.mean()), target="fresh_source_detection_not_latent_action_presence"))
    return predictions


def detection_baseline(training, observations, *, stratify_source_type):
    """Beta(1,1) source-mention prevalence, without an occupancy decomposition."""
    result = []
    for row in observations:
        matching = [r for r in training["observations"] if r["step_id"] == row["step_id"]
                    and (not stratify_source_type or r["source_type"] == row["source_type"])]
        result.append(dict(dependence_group_id=row["dependence_group_id"],
            jurisdiction_id=row["jurisdiction_id"], step_id=row["step_id"], source_type=row["source_type"],
            probability=(1 + sum(r["detected"] for r in matching))/(2 + len(matching))))
    return result


def score_readings(predictions, observations):
    pred = {prediction_key(r): r for r in predictions}
    obs = {prediction_key(r): r for r in observations}
    if not obs or len(pred) != len(predictions) or len(obs) != len(observations) or set(pred) != set(obs):
        raise ValueError("Require exactly matching independent held-out reading cells")
    scored = []
    for key in sorted(obs):
        p, y = pred[key]["probability"], obs[key]["detected"]
        if (type(y) is not bool or isinstance(p, bool) or not isinstance(p, (int, float))
                or not math.isfinite(p) or not 0 <= p <= 1):
            raise ValueError("Need valid detection probabilities and boolean observations")
        hit = p if y else 1-p
        scored.append(dict(dependence_group_id=key[0], jurisdiction_id=key[1], step_id=key[2],
                           source_type=key[3], probability=p, detected=y,
                           brier=(p-int(y))**2, log_loss=-math.log(hit) if hit else None))

    def aggregate(rows):
        return dict(reading_cells=len(rows), brier=sum(r["brier"] for r in rows)/len(rows),
                    mean_log_loss=(sum(r["log_loss"] for r in rows)/len(rows)
                                   if all(r["log_loss"] is not None for r in rows) else None),
                    infinite_log_loss=any(r["log_loss"] is None for r in rows))

    groups = {group: aggregate([r for r in scored if r["dependence_group_id"] == group])
              for group in sorted({r["dependence_group_id"] for r in scored})}
    return dict(schema_version="process-structure-detection-scores/1",
                target="heldout_source_detection_not_latent_action_presence",
                micro=aggregate(scored), per_independent_group=groups, cells=scored,
                scientific_presence_validation=False,
                qualification="Cells within one source are not independent validation jurisdictions; inspect source-group scores.")
