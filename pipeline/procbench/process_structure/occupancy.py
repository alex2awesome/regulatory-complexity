"""Hierarchical process occupancy with imperfect detection.

logit Pr(z[j,s]=1) = alpha[s] + u[j]; independent Gaussian alpha priors,
u[j] ~ Normal(0,tau**2), and a lognormal prior on tau. A reviewed reading
opportunity detects a step with probability p[s,k] when present and an explicitly
declared false-positive probability f[k] otherwise. p has a Beta prior.

This is NOT a conjugate model as a whole: z and p use Gibbs updates and the
Gaussian-white hierarchy uses elliptical slice sampling. Source types are not
assigned a trust ranking. False-positive probabilities are sensitivity inputs,
not calibrated estimates. Missing opportunities contribute no likelihood.

The inferred object is presence in a fixed, reviewed jurisdiction/lifecycle/era
scope. It is not mandatory participation, case route frequency, legal authority,
ordering, or existence of unobserved steps outside the supplied universe.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import expit, xlogy, xlog1py

from ..latent_gaussian import diagnostics, elliptical_slice, summary
from .detection_hierarchy import DetectionHierarchy, validate_config as validate_detection_config
from .identity import JurisdictionAssignments, SCHEMA as IDENTITY_SCHEMA
from .logical_support import LogicalSupport


SCHEMA = "process-occupancy-evidence/1"


@dataclass(frozen=True)
class Config:
    chains: int = 4
    warmup: int = 500
    draws: int = 1500
    seed: int = 20260921
    step_logit_sd: float = 1.5
    jurisdiction_scale_median: float = .5
    jurisdiction_scale_log_sd: float = .75
    hierarchy_update: str = "augmented"
    hierarchy_block_size: int = 0
    detection_model: str = "independent_beta"
    detection_type_logit_sd: float = 1.5
    detection_step_logit_sd: float = .75

    def __post_init__(self):
        for key in ("chains", "warmup", "draws", "seed"):
            x = getattr(self, key)
            if type(x) is not int or x < 0:
                raise ValueError(f"{key} must be a nonnegative integer")
        if self.chains < 2 or self.draws < 8:
            raise ValueError("Need at least two chains and eight retained states")
        for key in ("step_logit_sd", "jurisdiction_scale_median", "jurisdiction_scale_log_sd"):
            x = getattr(self, key)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
                raise ValueError(f"{key} must be finite numeric")
        if self.step_logit_sd <= 0 or self.jurisdiction_scale_median <= 0 or self.jurisdiction_scale_log_sd < 0:
            raise ValueError("Invalid hierarchy scale prior")
        if self.hierarchy_update not in {"augmented", "collapsed"}:
            raise ValueError("hierarchy_update must be augmented or collapsed")
        if type(self.hierarchy_block_size) is not int or self.hierarchy_block_size < 0:
            raise ValueError("hierarchy_block_size must be a nonnegative integer (zero means whole family)")
        validate_detection_config(self.detection_model, self.detection_type_logit_sd,
                                  self.detection_step_logit_sd)


def _ids(values, name):
    if (not isinstance(values, list) or not values
            or any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in values)
            or len(set(values)) != len(values)):
        raise ValueError(f"{name} must be a nonempty list of distinct IDs")
    return {value: i for i, value in enumerate(values)}


def _refs(row):
    refs = row.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        raise ValueError("Every observation/anchor requires source-bound evidence_refs")
    for ref in refs:
        if (not isinstance(ref, dict) or not isinstance(ref.get("path"), str)
                or not ref["path"] or not isinstance(ref.get("locator"), str)
                or not ref["locator"] or not isinstance(ref.get("sha256"), str)
                or len(ref["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in ref["sha256"])):
            raise ValueError("Evidence references need path, SHA256 and reviewed locator")


class Evidence:
    def __init__(self, data):
        if data.get("schema_version") not in {SCHEMA, IDENTITY_SCHEMA}:
            raise ValueError("Unknown occupancy evidence contract")
        if (not isinstance(data.get("scope"), str) or not data["scope"].strip()
                or data.get("opportunity_frame") != "reviewed_units_not_selected_for_step_mentions"
                or data.get("conditional_independence") != "assumed_given_presence_and_source_type_detection"
                or not isinstance(data.get("assumption_note"), str) or not data["assumption_note"].strip()):
            raise ValueError("Declare scope, reading-opportunity frame and dependence assumption")
        self.data = data
        self.j = _ids(data.get("jurisdictions"), "jurisdictions")
        self.s = _ids(data.get("steps"), "steps")
        self.k = _ids(data.get("source_types"), "source_types")
        J, S, K = len(self.j), len(self.s), len(self.k)
        self.positive = np.zeros((J, S, K), dtype=int)
        self.negative = np.zeros_like(self.positive)
        self.anchors = np.full((J, S), -1, dtype=int)
        models = data.get("source_models")
        if not isinstance(models, dict) or set(models) != set(self.k):
            raise ValueError("Declare detection priors and false-positive assumption for every source type")
        self.a = np.zeros((S, K))
        self.b = np.zeros_like(self.a)
        self.false_positive = np.zeros(K)
        for kind, k in self.k.items():
            model = models[kind]
            ab = model.get("detection_beta")
            f = model.get("false_positive_probability")
            if (not isinstance(ab, list) or len(ab) != 2
                    or any(isinstance(x, bool) or not isinstance(x, (int, float))
                           or not math.isfinite(x) or x < 1 for x in ab)
                    or isinstance(f, bool) or not isinstance(f, (int, float))
                    or not math.isfinite(f) or not 0 <= f < 1):
                raise ValueError("Detection Beta shapes must be >=1 in this first-pass numeric implementation; invalid false-positive parameters")
            self.a[:, k], self.b[:, k] = ab
            self.false_positive[k] = f
        self.observation_units = set()
        seen = set()
        group_scope = {}
        unit_scope = {}
        detection_refs = set()
        seen_support = set()
        observations = data.get("observations")
        anchors = data.get("known_presence")
        if not isinstance(observations, list) or not isinstance(anchors, list):
            raise ValueError("Observations and independent truth anchors must be explicit lists")
        for row in observations:
            j, s, k = self._index(row)
            if type(row.get("detected")) is not bool or row.get("reviewed_scope") is not True:
                raise ValueError("Detection needs a boolean and an explicitly reviewed reading scope")
            unit, group = row.get("unit_id"), row.get("dependence_group_id")
            if any(not isinstance(x, str) or not x.strip() for x in (unit, group)):
                raise ValueError("Reading unit and dependence group IDs are required")
            key = (group, j, s)
            if key in seen:
                raise ValueError("Dependent claims/copies cannot become repeated detection opportunities")
            if group in group_scope and group_scope[group] != (j, k):
                raise ValueError("One source dependence group cannot be independently replicated across jurisdictions/types")
            if unit in unit_scope and unit_scope[unit] != (group, j, k):
                raise ValueError("A reading unit cannot change dependence group or jurisdiction/source type")
            seen.add(key)
            group_scope[group] = (j, k)
            unit_scope[unit] = (group, j, k)
            self.observation_units.add(unit)
            _refs(row)
            for ref in row["evidence_refs"]:
                signature = (ref["path"], ref["sha256"], ref["locator"])
                if (j, s, signature) in seen_support:
                    raise ValueError("The same source support cannot be counted under renamed reading units")
                seen_support.add((j, s, signature))
                detection_refs.add(signature)
            (self.positive if row["detected"] else self.negative)[j, s, k] += 1
        anchor_units = set()
        for row in anchors:
            try:
                j, s = self.j[row["jurisdiction_id"]], self.s[row["step_id"]]
            except (KeyError, TypeError) as exc:
                raise ValueError("Unknown anchor jurisdiction/step") from exc
            unit = row.get("unit_id")
            if (type(row.get("present")) is not bool or not isinstance(unit, str) or not unit.strip()
                    or row.get("basis") not in {"explicit_presence", "explicit_absence", "complete_inventory_review"}):
                raise ValueError("Known presence requires an explicit reviewed truth anchor, not silence")
            if row["basis"] == "explicit_presence" and not row["present"] or row["basis"] == "explicit_absence" and row["present"]:
                raise ValueError("Anchor value and evidential basis conflict")
            if self.anchors[j, s] != -1 or unit in self.observation_units:
                raise ValueError("Duplicate anchor or anchor source reused as detection evidence")
            _refs(row)
            if any((ref["path"], ref["sha256"], ref["locator"]) in detection_refs
                   for ref in row["evidence_refs"]):
                raise ValueError("Truth anchor cannot reuse detection source support under a different unit ID")
            self.anchors[j, s] = int(row["present"])
            anchor_units.add(unit)
        impossible = (self.anchors == 0) & np.any(
            (self.positive > 0) & (self.false_positive[None, None, :] == 0), axis=2)
        if np.any(impossible):
            raise ValueError("Known absence contradicts a declared zero-error positive detection")
        self.logical_support = (LogicalSupport(data["steps"], data["logical_support"])
                                if "logical_support" in data else None)
        if self.logical_support is not None:
            self.logical_support.validate_anchors(self.anchors)
            # Zero-error positive reports force states too. These are actual
            # likelihood restrictions, unlike the structural prior declaration.
            required = self.anchors.copy()
            required[np.any((self.positive > 0)
                            & (self.false_positive[None, None, :] == 0), axis=2)] = 1
            self.logical_support.validate_anchors(required)
        self.identity = JurisdictionAssignments(self, _refs)

    def _index(self, row):
        try:
            return self.j[row["jurisdiction_id"]], self.s[row["step_id"]], self.k[row["source_type"]]
        except (KeyError, TypeError) as exc:
            raise ValueError("Unknown/unresolved jurisdiction, step or source type is not a model cell") from exc

    def support_report(self):
        positive, negative = self.identity.base_positive, self.identity.base_negative
        total = positive + negative
        report = {
            "jurisdictions": len(self.j), "steps_in_observed_universe": len(self.s),
            "reading_opportunities": int(total.sum()),
            "positive_detections": int(positive.sum()),
            "reviewed_nondetections": int(negative.sum()),
            "cells_without_any_reading_opportunity": int(np.sum(total.sum(axis=2) == 0)),
            "cells_with_repeated_readings": int(np.sum(total.sum(axis=2) >= 2)),
            "known_present_cells": int(np.sum(self.anchors == 1)),
            "known_absent_cells": int(np.sum(self.anchors == 0)),
            "positive_only_opportunity_frame": bool(positive.sum() and not negative.sum()),
            "detection_calibration_opportunities_by_step_type": np.sum(
                total * (self.anchors == 1)[:, :, None], axis=0).tolist(),
            "qualification": "Support counts flag identification risks; they do not prove identifiable detection or transportability.",
        }
        if self.identity.units:
            ip, inn = int(self.identity.positive.sum()), int(self.identity.negative.sum())
            report.update(resolved_reading_opportunities=int(total.sum()),
                          uncertain_jurisdiction_units=len(self.identity.units),
                          uncertain_jurisdiction_readings=ip+inn,
                          reading_opportunities=int(total.sum())+ip+inn,
                          positive_detections=int(positive.sum())+ip,
                          reviewed_nondetections=int(negative.sum())+inn,
                          positive_only_opportunity_frame=bool((positive.sum()+ip) and negative.sum()+inn == 0),
                          cell_support_scope="Cell-specific repetition/anchor support above counts resolved readings only; categorical units are not replicated over candidates.")
        return report


def conditional_presence(logits, detection, evidence):
    """Exact binary conditional; missing observations supply zero log evidence."""
    logits = np.asarray(logits, dtype=float)
    p = np.asarray(detection, dtype=float)
    if (logits.shape != evidence.anchors.shape or p.shape != evidence.a.shape
            or not np.isfinite(logits).all() or not np.isfinite(p).all()
            or np.any(p <= 0) or np.any(p >= 1)):
        raise ValueError("Invalid occupancy/detection parameters")
    if evidence.logical_support is not None:
        return evidence.logical_support.conditional_probabilities(
            logits, detection_log_factors(p, evidence), evidence.anchors)
    n1, n0 = evidence.positive, evidence.negative
    present = -np.logaddexp(0, -logits) + np.sum(xlogy(n1, p) + xlog1py(n0, -p), axis=2)
    f = evidence.false_positive
    absent = -np.logaddexp(0, logits) + np.sum(xlogy(n1, f) + xlog1py(n0, -f), axis=2)
    result = expit(present - absent)
    if not np.isfinite(result).all():
        raise FloatingPointError("Observation has no finite occupancy explanation")
    result[evidence.anchors >= 0] = evidence.anchors[evidence.anchors >= 0]
    return result


def joint_count_summary(counts, universe_size):
    """Discrete empirical posterior; fractional expected counts remain valid."""
    values = np.asarray(counts)
    if values.ndim != 2 or not np.isin(values, np.arange(universe_size + 1)).all():
        raise ValueError("Joint counts must be chains x draws in the supplied universe")
    ordered = np.sort(values.reshape(-1))
    indices = np.maximum(0, np.ceil(np.array([.05, .5, .95]) * len(ordered)).astype(int) - 1)
    q = ordered[indices]
    masses = np.bincount(ordered.astype(int), minlength=universe_size + 1) / len(ordered)
    return {"mean": float(values.mean()), "median": int(q[1]),
            "ci90": [int(q[0]), int(q[2])],
            "empirical_posterior_count_mass": {str(n): float(p) for n, p in enumerate(masses)},
            "count_scope": "all_canonical_activity_types_in_supplied_scope_not_necessarily_applicant_actions",
            "qualification": "Integer equal-tail bounds from joint draws; zero sampled mass does not prove a count impossible."}


def detection_log_factors(detection, evidence):
    """Log likelihood of the reviewed detections for each possible cell state.

    No Bernoulli combinatorial factor is needed for labeled reading units.
    A missing reading contributes exactly zero to both states. These factors
    are cached during a hierarchy move because p and the data are fixed there.
    """
    p = np.asarray(detection, dtype=float)
    if (p.shape != evidence.a.shape or not np.isfinite(p).all()
            or np.any(p <= 0) or np.any(p >= 1)):
        raise ValueError("Invalid detection probabilities")
    positive, negative = evidence.positive, evidence.negative
    return (np.sum(xlogy(positive, p) + xlog1py(negative, -p), axis=2),
            np.sum(xlogy(positive, evidence.false_positive)
                   + xlog1py(negative, -evidence.false_positive), axis=2))


def marginal_occupancy_log_likelihood(logits, factors, evidence):
    """Integrate unanchored z exactly; retain independent anchor information.

    This is the hierarchy likelihood conditional on p, NOT a new statistical
    model. The latent indicators must be redrawn after this move and before
    updating p; retaining stale indicators would target the wrong posterior.
    """
    logits = np.asarray(logits, dtype=float)
    if logits.shape != evidence.anchors.shape or not np.isfinite(logits).all():
        raise ValueError("Invalid occupancy logits")
    if evidence.logical_support is not None:
        return evidence.logical_support.marginal_log_likelihood(logits, factors, evidence.anchors)
    present = -np.logaddexp(0, -logits) + factors[0]
    absent = -np.logaddexp(0, logits) + factors[1]
    mixed = np.logaddexp(present, absent)
    value = np.where(evidence.anchors == 1, present,
                     np.where(evidence.anchors == 0, absent, mixed))
    return float(np.sum(value))


def fit(data, config=Config()):
    evidence = Evidence(data)
    J, S, K = len(evidence.j), len(evidence.s), len(evidence.k)
    detector = (DetectionHierarchy(evidence.a, evidence.b,
                                   config.detection_type_logit_sd,
                                   config.detection_step_logit_sd)
                if config.detection_model == "logit_partial_pooling" else None)
    scale_coordinate = int(config.jurisdiction_scale_log_sd > 0)
    dimension = S + J + scale_coordinate
    shape = (config.chains, config.draws)
    saved_z = np.empty(shape + (J, S), dtype=np.uint8)
    saved_probability = np.empty(shape + (J, S))
    saved_detection = np.empty(shape + (S, K))
    saved_white = np.empty(shape + (dimension,))
    saved_tau = np.empty(shape)
    saved_log_likelihood = np.empty(shape)
    saved_detection_white = np.empty(shape + (S, K)) if detector else None
    saved_detection_type_effect = np.empty(shape + (K,)) if detector else None
    H = len(evidence.identity.units)
    saved_assignment = np.empty(shape + (H,), dtype=np.int32) if H else None
    saved_assignment_probability = np.empty(shape + (H, J)) if H else None

    def transform(white):
        tau = config.jurisdiction_scale_median * math.exp(
            config.jurisdiction_scale_log_sd * white[-1] if scale_coordinate else 0.)
        return config.step_logit_sd * white[:S][None, :] + tau * white[S:S+J, None], tau

    blocks = [np.arange(S), np.arange(S, S+J)]
    if config.hierarchy_block_size:
        blocks = [block[start:start + config.hierarchy_block_size]
                  for block in blocks for start in range(0, len(block), config.hierarchy_block_size)]
    if scale_coordinate:
        blocks.append(np.array([dimension-1]))
    for chain in range(config.chains):
        rng = np.random.default_rng(config.seed + chain * 104729)
        white = rng.normal(size=dimension)
        if detector:
            pwhite = rng.normal(size=(S, K))
            p = detector.probabilities(pwhite)
        else:
            p = rng.beta(evidence.a, evidence.b)
        if H:
            # Avoid impossible starts when a zero-error reading rules out some
            # anchored-absent candidates. No posterior tuning occurs here.
            initial = evidence.identity.priors.copy()
            for h, unit in enumerate(evidence.identity.units):
                if evidence.false_positive[evidence.k[unit["source_type"]]] == 0:
                    needed = evidence.identity.positive[h].sum(axis=-1) > 0
                    initial[h, ~np.all(evidence.anchors[:, needed] != 0, axis=1)] = 0
                    if evidence.logical_support is not None:
                        for ji in range(J):
                            if initial[h, ji] <= 0:
                                continue
                            candidate = evidence.anchors[ji:ji+1].copy()
                            candidate[0, needed] = 1
                            try:
                                evidence.logical_support.validate_anchors(candidate)
                            except ValueError:
                                initial[h, ji] = 0
                    if initial[h].sum() == 0:
                        raise ValueError("No candidate county supports a zero-error reading under the declared structure")
                    initial[h] /= initial[h].sum()
            assignment = evidence.identity.sample(initial, rng)
            evidence.identity.set_assignments(assignment)
        for iteration in range(config.warmup + config.draws):
            if config.hierarchy_update == "collapsed":
                # Partially collapsed Gibbs: white|p,y (z integrated), then
                # z|white,p,y, then p|z,y. Do not move the p update ahead of
                # the refreshed z draw. This also avoids conditioning the
                # hierarchy on thousands of unobserved auxiliary indicators.
                factors = detection_log_factors(p, evidence)

                def marginalized_likelihood(candidate):
                    candidate_logits, _ = transform(candidate)
                    return marginal_occupancy_log_likelihood(candidate_logits, factors, evidence)

                current = marginalized_likelihood(white)
                for block in blocks:
                    white, current, _ = elliptical_slice(white, block, marginalized_likelihood, current, rng)
            logits, _ = transform(white)
            if evidence.logical_support is None:
                probability = conditional_presence(logits, p, evidence)
                z = rng.random((J, S)) < probability
            else:
                # Logical prerequisites couple action indicators. Independent
                # Bernoulli draws from their marginals would violate support.
                z = evidence.logical_support.sample(
                    logits, detection_log_factors(p, evidence), evidence.anchors, rng)
            successes = np.sum(evidence.positive * z[:, :, None], axis=0)
            failures = np.sum(evidence.negative * z[:, :, None], axis=0)
            if detector:
                flat = pwhite.reshape(-1)
                for k in range(K):
                    indices = np.arange(k, S*K, K)

                    def detection_likelihood(candidate, source_index=k):
                        return detector.source_log_likelihood(
                            candidate.reshape(S, K), source_index,
                            successes[:, source_index], failures[:, source_index])

                    current = detection_likelihood(flat)
                    flat, current, _ = elliptical_slice(
                        flat, indices, detection_likelihood, current, rng)
                pwhite = flat.reshape(S, K)
                detection_logits = detector.logits(pwhite)
                p = detector.probabilities(pwhite)
            else:
                p = rng.beta(evidence.a + successes, evidence.b + failures)

            def occupancy_likelihood(candidate):
                candidate_logits, _ = transform(candidate)
                if evidence.logical_support is not None:
                    return evidence.logical_support.prior_log_probability(candidate_logits, z)
                return float(np.sum(np.where(z, -np.logaddexp(0, -candidate_logits),
                                             -np.logaddexp(0, candidate_logits))))

            if config.hierarchy_update == "augmented":
                current = occupancy_likelihood(white)
                for block in blocks:
                    white, current, _ = elliptical_slice(white, block, occupancy_likelihood, current, rng)
            if H:
                assignment_probability = evidence.identity.conditional_probabilities(z, p)
                assignment = evidence.identity.sample(assignment_probability, rng)
                evidence.identity.set_assignments(assignment)
            if iteration >= config.warmup:
                at = iteration - config.warmup
                logits, tau = transform(white)
                saved_z[chain, at] = z
                saved_probability[chain, at] = conditional_presence(logits, p, evidence)
                saved_detection[chain, at] = p
                saved_white[chain, at] = white
                saved_tau[chain, at] = tau
                if detector:
                    saved_detection_white[chain, at] = pwhite
                    saved_detection_type_effect[chain, at] = (
                        detector.conditional_type_effect(detection_logits)[0])
                if H:
                    saved_assignment[chain, at] = assignment
                    saved_assignment_probability[chain, at] = assignment_probability
                selected_p = np.where(z[:, :, None], p, evidence.false_positive)
                saved_log_likelihood[chain, at] = float(np.sum(
                    xlogy(evidence.positive, selected_p) + xlog1py(evidence.negative, -selected_p)))
    counts = saved_z.sum(axis=-1)
    check = {"log_detection_likelihood": diagnostics(saved_log_likelihood),
             "jurisdiction_logit_scale": diagnostics(saved_tau)}
    check.update({f"white:{i}": diagnostics(saved_white[:, :, i]) for i in range(dimension)})
    check.update({f"count:{j}": diagnostics(counts[:, :, index]) for j, index in evidence.j.items()})
    check.update({f"detection:{s}:{k}": diagnostics(saved_detection[:, :, si, ki])
                  for s, si in evidence.s.items() for k, ki in evidence.k.items()})
    if detector:
        check.update({f"detection_white:{s}:{k}":
                      diagnostics(saved_detection_white[:, :, si, ki])
                      for s, si in evidence.s.items() for k, ki in evidence.k.items()})
        check.update({f"detection_type_effect_conditional_mean:{k}":
                      diagnostics(saved_detection_type_effect[:, :, ki])
                      for k, ki in evidence.k.items()})
    check.update({f"presence_probability:{j}:{s}": diagnostics(saved_probability[:, :, ji, si])
                  for j, ji in evidence.j.items() for s, si in evidence.s.items()
                  if evidence.anchors[ji, si] < 0})
    if H:
        check.update({f"jurisdiction_assignment:{unit['unit_id']}:{j}":
                      diagnostics(saved_assignment_probability[:, :, h, ji])
                      for h, unit in enumerate(evidence.identity.units) for j, ji in evidence.j.items()
                      if evidence.identity.priors[h, ji] > 0})
        check.update({f"jurisdiction_assignment_indicator:{unit['unit_id']}:{j}":
                      diagnostics((saved_assignment[:, :, h] == ji).astype(float))
                      for h, unit in enumerate(evidence.identity.units) for j, ji in evidence.j.items()
                      if evidence.identity.priors[h, ji] > 0})
    failed = [name for name, d in check.items() if d["rhat"] is None or d["rhat"] > 1.01
              or d["ess_bulk"] < 400 or d["ess_tail"] < 200]
    reported_config = asdict(config)
    if detector is None:
        # Preserve the historical default result contract and seeded replay.
        for key in ("detection_model", "detection_type_logit_sd", "detection_step_logit_sd"):
            reported_config.pop(key)
    result = {
        "schema_version": "process-occupancy-posterior/1", "config": reported_config,
        "sampler": {"hierarchy_update": config.hierarchy_update,
                    "hierarchy_block_size": config.hierarchy_block_size,
                    "target": "same_joint_presence_detection_hierarchy_posterior",
                    "qualification": "Optional collapsing changes the transition, not the evidence or prior; convergence is still checked."},
        "scope": data["scope"], "support": evidence.support_report(),
        "numerically_usable": not failed, "diagnostics": check, "flagged": failed,
        "scientific_validation_complete": False,
        "scientific_release_eligible": False,
        "evidence_gate": {
            "has_reading_opportunities": bool((evidence.positive + evidence.negative).sum()),
            "has_reviewed_nondetections": bool(evidence.negative.sum()),
            "independent_heldout_validation": "not_performed_by_sampler",
            "prior_sensitivity": "not_performed_by_single_fit",
            "qualification": "Numerical convergence cannot release uncalibrated, unvalidated structure posteriors.",
        },
        "presence_probability": saved_probability.mean(axis=(0, 1)).tolist(),
        "jurisdictions": data["jurisdictions"], "steps": data["steps"],
        "source_types": data["source_types"],
        "joint_step_count": {j: joint_count_summary(counts[:, :, i], S) for j, i in evidence.j.items()},
        "jurisdiction_logit_scale": summary(saved_tau),
        "qualifications": [
            "Diagnostic summaries are not scientific results if the numerical gate fails.",
            "Counts are summed within JOINT presence draws, not from independent marginal Bernoulli approximations.",
            "Presence means implementation includes this action in the declared scope, not mandatory participation.",
            "Source detections are conditionally independent by assumption; copied or same-case claims require deduplication.",
            "False-positive probabilities are declared sensitivities; no source-reliability calibration is claimed.",
            "Detection and prevalence may remain prior-sensitive without replicated readings/independent truth anchors.",
            "The universe is observed and fixed: no count of never-mentioned steps is inferred.",
            "No ordering, repeat, time, cost, total-burden or V6 inventory handoff is inferred by this module.",
        ],
    }
    arrays = dict(presence=saved_z, conditional_presence=saved_probability,
                  detection=saved_detection, hierarchy_white=saved_white,
                  jurisdiction_scale=saved_tau, step_count=counts,
                  log_detection_likelihood=saved_log_likelihood)
    if evidence.logical_support is not None:
        result["logical_support"] = evidence.logical_support.as_report()
        result["sampler"]["target"] = "normalized_logically_constrained_presence_detection_hierarchy_posterior"
        result["qualifications"].append(
            "Logical implications restrict and normalize generative inventory support; they are declared modeling assumptions, not additional observations or presence anchors. Marginal presence probabilities cannot be multiplied to recover joint inventory or episode probabilities.")
    if detector:
        result["detection_hierarchy"] = {
            "model": "logit_partial_pooling",
            "logit_center_by_source_type": {
                k: float(detector.center[ki]) for k, ki in evidence.k.items()},
            "center_source": "log(a/b) from detection_beta; center only, not a Beta prior family",
            "type_logit_sd": detector.type_logit_sd,
            "step_logit_sd": detector.step_logit_sd,
            "logit_covariance": detector.covariance.tolist(),
            "type_effect_reporting": {
                k: {
                    "conditional_mean_summary": summary(saved_detection_type_effect[:, :, ki]),
                    "conditional_variance": detector.type_effect_conditional_variance,
                    "posterior_mean": float(saved_detection_type_effect[:, :, ki].mean()),
                    "posterior_variance": float(
                        saved_detection_type_effect[:, :, ki].var()
                        + detector.type_effect_conditional_variance),
                } for k, ki in evidence.k.items()},
            "type_effect_reporting_qualification": "Analytic conditional moments under the integrated Gaussian prior; no extra type-effect coordinate was sampled. Posterior variance uses total variance, while quantiles of the full mixture are not claimed.",
            "white_state": "one independent standard-normal S-vector per source type; separate from hierarchy_white",
            "qualification": "Partial pooling changes the declared detection prior; it does not identify omission versus action absence or calibrate source reliability.",
        }
        result["qualifications"].append(
            "The opt-in logit detection hierarchy uses Beta shapes only to center a distinct Gaussian-logit prior; it is not the independent-Beta model.")
        arrays.update(detection_white=saved_detection_white,
                      detection_type_effect_conditional_mean=saved_detection_type_effect)
    if H:
        result["jurisdiction_assignment"] = [dict(
            unit_id=unit["unit_id"], assignment_prior_basis=unit["assignment_prior_basis"],
            candidate_scope_complete=unit["candidate_scope_complete"],
            prior_probability={j: float(evidence.identity.priors[h, ji]) for j, ji in evidence.j.items()},
            posterior_probability={j: float(saved_assignment_probability[:, :, h, ji].mean())
                                   for j, ji in evidence.j.items()},
            interpretation="one_shared_uncertain_jurisdiction_for_the_entire_reading_unit_not_a_verified_identity")
            for h, unit in enumerate(evidence.identity.units)]
        result["qualifications"].append("Identity probabilities are conditional on declared candidate coverage and priors; no hard county/department assignment or calibrated text classifier is implied.")
        arrays.update(jurisdiction_assignment=saved_assignment,
                      jurisdiction_assignment_probability=saved_assignment_probability)
    return result, arrays


def verify_source_bindings(data, root):
    """Byte verification only; reviewed locators still require semantic review."""
    seen = {}
    rows = data["observations"] + data["known_presence"]
    rows = rows + [row for unit in data.get("uncertain_jurisdiction_units", []) for row in unit["readings"]]
    rows = rows + [{"evidence_refs": unit[key]} for unit in data.get("uncertain_jurisdiction_units", [])
                   for key in ("identity_scope_refs", "assignment_prior_refs") if unit.get(key)]
    rows = rows + [{"evidence_refs": unit['step_scope_refs']}
                   for unit in data.get('uncertain_jurisdiction_units', []) if unit.get('step_scope_refs')]
    rows = rows + [{"evidence_refs": row["identity_scope_refs"]}
                   for row in data["observations"] + data["known_presence"] if row.get("identity_scope_refs")]
    # Lineage references are part of the holdout boundary as well as the
    # source contract.  Verify both row- and unit-level lineage bytes before
    # any caller treats a retained unit as source-disjoint.
    rows = rows + [{"evidence_refs": row["lineage_refs"]}
                   for row in data["observations"] + data["known_presence"]
                   if row.get("lineage_refs")]
    rows = rows + [{"evidence_refs": unit["lineage_refs"]}
                   for unit in data.get("uncertain_jurisdiction_units", [])
                   if unit.get("lineage_refs")]
    if "logical_support" in data:
        declaration = data["logical_support"]
        # Validate the declaration too; malformed metadata must not be silently
        # ignored by a byte-only preflight or confused with presence evidence.
        LogicalSupport(data["steps"], declaration)
        rows.append({"evidence_refs": declaration["source_refs"]})
        rows.extend({"evidence_refs": rule["source_refs"]}
                    for rule in declaration["implications"] if rule.get("source_refs"))
    for row in rows:
        _refs(row)
        for ref in row["evidence_refs"]:
            path = (Path(root) / ref["path"]).resolve()
            if path not in seen:
                seen[path] = hashlib.sha256(path.read_bytes()).hexdigest()
            digest = seen[path]
            if digest != ref["sha256"]:
                raise ValueError(f"Changed source binding: {path}")
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("Choose a fresh output directory")
    implementation = Path(__file__)
    gaussian_sampler = implementation.parents[1] / "latent_gaussian.py"
    identity_implementation = Path(__file__).with_name("identity.py")
    detection_implementation = Path(__file__).with_name("detection_hierarchy.py")
    logical_implementation = Path(__file__).with_name("logical_support.py")
    bound_bytes = {path: path.read_bytes() for path in (
        args.input, args.config, implementation, gaussian_sampler,
        identity_implementation, detection_implementation, logical_implementation)}
    data = json.loads(bound_bytes[args.input])
    config = Config(**json.loads(bound_bytes[args.config]))
    Evidence(data)
    verified = verify_source_bindings(data, args.source_root)
    result, arrays = fit(data, config)
    # A shared workspace can change while a fit runs. Bind the bytes consumed,
    # and refuse to attribute saved draws to a later input/code/source revision.
    for path, payload in bound_bytes.items():
        if path.read_bytes() != payload:
            raise ValueError(f"Run binding changed during sampling: {path}")
    verify_source_bindings(data, args.source_root)
    args.out.mkdir(parents=True)
    np.savez_compressed(args.out / "draws.npz", **arrays)
    (args.out / "posterior.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    manifest = dict(schema_version="process-occupancy-run/1", status="completed",
                    completed_utc=datetime.now(timezone.utc).isoformat(),
                    numerically_usable=result["numerically_usable"], source_bindings_verified=verified,
                    input_sha256=hashlib.sha256(bound_bytes[args.input]).hexdigest(),
                    config_sha256=hashlib.sha256(bound_bytes[args.config]).hexdigest(),
                    implementation_sha256=hashlib.sha256(bound_bytes[implementation]).hexdigest(),
                    gaussian_sampler_sha256=hashlib.sha256(bound_bytes[gaussian_sampler]).hexdigest(),
                    identity_implementation_sha256=hashlib.sha256(bound_bytes[identity_implementation]).hexdigest(),
                    draws_sha256=hashlib.sha256((args.out / "draws.npz").read_bytes()).hexdigest(),
                    posterior_sha256=hashlib.sha256((args.out / "posterior.json").read_bytes()).hexdigest(),
                    scientific_validation_complete=False)
    manifest["detection_implementation_sha256"] = hashlib.sha256(
        bound_bytes[detection_implementation]).hexdigest()
    manifest["logical_support_implementation_sha256"] = hashlib.sha256(
        bound_bytes[logical_implementation]).hexdigest()
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
