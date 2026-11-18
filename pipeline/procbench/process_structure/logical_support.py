"""Exact opt-in logical support for binary process occupancy.

Caller-reviewed implications have the form ``antecedent present => consequent
present``.  They restrict and renormalize the latent occupancy prior; they are
not observations, truth anchors, route declarations, or participation facts.
Small connected components are enumerated exactly.  Steps outside those
components retain the independent Bernoulli occupancy model.
"""
from __future__ import annotations

import copy
import math

import numpy as np
from scipy.special import logsumexp


SCHEMA = "process-logical-support/1"
EVIDENCE_ROLE = "structural_support_not_observation_or_anchor"
BASIS = "meaning_of_actions_not_observed_truth"
MAX_COMPONENT_SIZE = 10
DECLARATION_FIELDS = {
    "schema_version", "reviewed", "scope", "evidence_role", "basis",
    "review_note", "source_refs", "implications",
}
IMPLICATION_REQUIRED_FIELDS = {
    "id", "antecedent_step_id", "consequent_step_id", "basis", "note",
}
IMPLICATION_ALLOWED_FIELDS = IMPLICATION_REQUIRED_FIELDS | {"source_refs"}


def _ordered_ids(values):
    if (not isinstance(values, list) or not values
            or any(not isinstance(value, str) or not value.strip() or value != value.strip()
                   for value in values)
            or len(set(values)) != len(values)):
        raise ValueError("step_ids must be a nonempty ordered list of distinct IDs")
    return list(values)


def _refs(refs):
    if not isinstance(refs, list) or not refs:
        raise ValueError("Every logical implication needs source-bound review references")
    for ref in refs:
        if (not isinstance(ref, dict)
                or not {"path", "sha256", "locator"} <= set(ref)
                or not isinstance(ref["path"], str) or not ref["path"]
                or not isinstance(ref["locator"], str) or not ref["locator"]
                or not isinstance(ref["sha256"], str) or len(ref["sha256"]) != 64
                or any(character not in "0123456789abcdef" for character in ref["sha256"])):
            raise ValueError("Logical-support references need path, SHA256 and reviewed locator")


def _log_binary_prior(logits):
    return -np.logaddexp(0.0, -logits), -np.logaddexp(0.0, logits)


class LogicalSupport:
    """Normalized implication support over a fixed ordered step universe."""

    def __init__(self, step_ids, declaration):
        self.step_ids = _ordered_ids(step_ids)
        self.index = {step: position for position, step in enumerate(self.step_ids)}
        if not isinstance(declaration, dict) or set(declaration) != DECLARATION_FIELDS:
            raise ValueError("Logical-support declaration must use the explicit schema")
        if (declaration["schema_version"] != SCHEMA or declaration["reviewed"] is not True
                or declaration["evidence_role"] != EVIDENCE_ROLE
                or declaration["basis"] != BASIS
                or not isinstance(declaration["scope"], str) or not declaration["scope"].strip()
                or not isinstance(declaration["review_note"], str)
                or not declaration["review_note"].strip()
                or not isinstance(declaration["implications"], list)
                or not declaration["implications"]):
            raise ValueError("Invalid reviewed logical-support declaration")
        _refs(declaration["source_refs"])

        seen_ids, seen_pairs, implications = set(), set(), []
        adjacency = {position: set() for position in range(len(self.step_ids))}
        for raw in declaration["implications"]:
            if (not isinstance(raw, dict)
                    or not IMPLICATION_REQUIRED_FIELDS <= set(raw) <= IMPLICATION_ALLOWED_FIELDS):
                raise ValueError("Logical implications must use the explicit schema")
            identifier = raw["id"]
            antecedent, consequent = raw["antecedent_step_id"], raw["consequent_step_id"]
            if (not isinstance(identifier, str) or not identifier.strip() or identifier in seen_ids
                    or not isinstance(antecedent, str) or not isinstance(consequent, str)
                    or antecedent not in self.index or consequent not in self.index
                    or antecedent == consequent
                    or (antecedent, consequent) in seen_pairs
                    or raw["basis"] != BASIS
                    or not isinstance(raw["note"], str) or not raw["note"].strip()):
                raise ValueError("Malformed, unknown, self, or duplicate logical implication")
            if "source_refs" in raw:
                _refs(raw["source_refs"])
            ai, ci = self.index[antecedent], self.index[consequent]
            seen_ids.add(identifier)
            seen_pairs.add((antecedent, consequent))
            implications.append((identifier, ai, ci))
            adjacency[ai].add(ci)
            adjacency[ci].add(ai)

        involved = {index for _, ai, ci in implications for index in (ai, ci)}
        components, visited = [], set()
        for start in sorted(involved):
            if start in visited:
                continue
            pending, members = [start], []
            while pending:
                current = pending.pop()
                if current in visited:
                    continue
                visited.add(current)
                members.append(current)
                pending.extend(sorted(adjacency[current] - visited, reverse=True))
            members = sorted(members)
            if len(members) > MAX_COMPONENT_SIZE:
                raise ValueError(
                    f"Logical-support component has {len(members)} steps; maximum is {MAX_COMPONENT_SIZE}")
            local = {global_index: local_index for local_index, global_index in enumerate(members)}
            component_implications = [item for item in implications
                                      if item[1] in local and item[2] in local]
            state_count = 1 << len(members)
            integers = np.arange(state_count, dtype=np.uint64)[:, None]
            bit_positions = np.arange(len(members), dtype=np.uint64)[None, :]
            states = ((integers >> bit_positions) & 1).astype(bool)
            allowed = np.ones(state_count, dtype=bool)
            for _, ai, ci in component_implications:
                allowed &= ~(states[:, local[ai]] & ~states[:, local[ci]])
            states = states[allowed]
            states.setflags(write=False)
            components.append({
                "indices": np.asarray(members, dtype=np.int64),
                "states": states,
                "implications": component_implications,
            })
        self.components = components
        self.unconstrained = np.asarray(
            [index for index in range(len(self.step_ids)) if index not in involved], dtype=np.int64)
        self.declaration = copy.deepcopy(declaration)

    def _inputs(self, logits, factors, anchors):
        logits = np.asarray(logits, dtype=float)
        if (logits.ndim != 2 or logits.shape[0] == 0
                or logits.shape[1] != len(self.step_ids) or not np.isfinite(logits).all()):
            raise ValueError("logits must be a finite jurisdictions-by-steps array")
        if not isinstance(factors, tuple) or len(factors) != 2:
            raise ValueError("factors must be a (present, absent) tuple")
        parsed = []
        for factor in factors:
            value = np.asarray(factor, dtype=float)
            if (value.shape != logits.shape or np.isnan(value).any()
                    or np.isposinf(value).any()):
                raise ValueError("Detection factors must match logits and be finite or negative infinity")
            parsed.append(value)
        checked_anchors = self.validate_anchors(anchors)
        if checked_anchors.shape != logits.shape:
            raise ValueError("anchors must match logits")
        return logits, (parsed[0], parsed[1]), checked_anchors

    def validate_anchors(self, anchors):
        """Validate anchor form and compatibility without changing prior normalization."""
        anchors = np.asarray(anchors)
        if (anchors.ndim != 2 or anchors.shape[0] == 0
                or anchors.shape[1] != len(self.step_ids)
                or anchors.dtype.kind not in "iu" or not np.isin(anchors, [-1, 0, 1]).all()):
            raise ValueError("anchors must be a nonempty jurisdictions-by-steps integer array in {-1,0,1}")
        checked = anchors.astype(np.int8, copy=True)
        for component in self.components:
            indices, states = component["indices"], component["states"]
            fixed = checked[:, indices]
            compatible = np.all(
                (fixed[:, None, :] < 0) | (states[None, :, :] == fixed[:, None, :]), axis=2)
            if not np.all(np.any(compatible, axis=1)):
                raise ValueError("Anchors contradict declared logical support")
        return checked

    @staticmethod
    def _component_terms(logits, present, absent, anchors, component):
        indices, states = component["indices"], component["states"]
        log_one, log_zero = _log_binary_prior(logits[:, indices])
        prior = np.sum(
            np.where(states[None, :, :], log_one[:, None, :], log_zero[:, None, :]), axis=2)
        log_normalizer = logsumexp(prior, axis=1)
        evidence = np.sum(
            np.where(states[None, :, :], present[:, None, indices], absent[:, None, indices]), axis=2)
        fixed = anchors[:, indices]
        allowed = np.all(
            (fixed[:, None, :] < 0) | (states[None, :, :] == fixed[:, None, :]), axis=2)
        posterior = np.where(allowed, prior + evidence, -math.inf)
        return states, prior, log_normalizer, posterior

    def marginal_log_likelihood(self, logits, factors, anchors):
        """Integrate latent indicators under the normalized constrained prior."""
        logits, factors, anchors = self._inputs(logits, factors, anchors)
        present, absent = factors
        log_one, log_zero = _log_binary_prior(logits)
        total = 0.0
        for component in self.components:
            _, _, normalizer, posterior = self._component_terms(
                logits, present, absent, anchors, component)
            numerator = logsumexp(posterior, axis=1)
            if np.isneginf(numerator).any():
                return -math.inf
            total += float(np.sum(numerator - normalizer))
        if len(self.unconstrained):
            indices = self.unconstrained
            one = log_one[:, indices] + present[:, indices]
            zero = log_zero[:, indices] + absent[:, indices]
            fixed = anchors[:, indices]
            contribution = np.where(
                fixed == 1, one, np.where(fixed == 0, zero, np.logaddexp(one, zero)))
            if np.isneginf(contribution).any():
                return -math.inf
            total += float(np.sum(contribution))
        return float(total)

    def conditional_probabilities(self, logits, factors, anchors):
        """Return exact marginal Pr(z=1 | factors, anchors, logical support)."""
        logits, factors, anchors = self._inputs(logits, factors, anchors)
        present, absent = factors
        log_one, log_zero = _log_binary_prior(logits)
        result = np.empty_like(logits)
        for component in self.components:
            states, _, _, posterior = self._component_terms(
                logits, present, absent, anchors, component)
            normalizer = logsumexp(posterior, axis=1)
            if np.isneginf(normalizer).any():
                raise FloatingPointError("Logical-support posterior has no positive mass")
            weights = np.exp(posterior - normalizer[:, None])
            weights /= weights.sum(axis=1, keepdims=True)
            # A sum of normalized floating-point weights can exceed one by an
            # ulp. This only clips numerical roundoff of valid binary marginals.
            result[:, component["indices"]] = np.clip(weights @ states, 0., 1.)
        if len(self.unconstrained):
            indices = self.unconstrained
            one = log_one[:, indices] + present[:, indices]
            zero = log_zero[:, indices] + absent[:, indices]
            fixed = anchors[:, indices]
            normalizer = np.where(
                fixed == 1, one, np.where(fixed == 0, zero, np.logaddexp(one, zero)))
            if np.isneginf(normalizer).any():
                raise FloatingPointError("Independent occupancy cell has no positive posterior mass")
            probabilities = np.empty(one.shape)
            probabilities[fixed == 1] = 1.0
            probabilities[fixed == 0] = 0.0
            free = fixed < 0
            probabilities[free] = np.exp(one[free] - normalizer[free])
            result[:, indices] = probabilities
        return result

    def sample(self, logits, factors, anchors, rng):
        """Draw one joint jurisdictions-by-steps occupancy state."""
        if not isinstance(rng, np.random.Generator):
            raise ValueError("rng must be a numpy.random.Generator")
        logits, factors, anchors = self._inputs(logits, factors, anchors)
        present, absent = factors
        log_one, log_zero = _log_binary_prior(logits)
        result = np.empty(logits.shape, dtype=bool)
        for component in self.components:
            states, _, _, posterior = self._component_terms(
                logits, present, absent, anchors, component)
            normalizer = logsumexp(posterior, axis=1)
            if np.isneginf(normalizer).any():
                raise FloatingPointError("Logical-support posterior has no positive mass")
            weights = np.exp(posterior - normalizer[:, None])
            weights /= weights.sum(axis=1, keepdims=True)
            cumulative = np.cumsum(weights, axis=1)
            last_positive = len(states) - 1 - np.argmax(weights[:, ::-1] > 0, axis=1)
            # Never put rounding-residual mass on an anchor-excluded tail state.
            cumulative = np.where(np.arange(len(states))[None, :] >= last_positive[:, None],
                                  1., np.minimum(cumulative, 1.))
            # Right-sided inverse CDF also skips leading zero mass at u=0.
            chosen = np.sum(cumulative <= rng.random(logits.shape[0])[:, None], axis=1)
            result[:, component["indices"]] = states[chosen]
        if len(self.unconstrained):
            indices = self.unconstrained
            one = log_one[:, indices] + present[:, indices]
            zero = log_zero[:, indices] + absent[:, indices]
            fixed = anchors[:, indices]
            normalizer = np.where(
                fixed == 1, one, np.where(fixed == 0, zero, np.logaddexp(one, zero)))
            if np.isneginf(normalizer).any():
                raise FloatingPointError("Independent occupancy cell has no positive posterior mass")
            probabilities = np.empty(one.shape)
            probabilities[fixed == 1] = 1.0
            probabilities[fixed == 0] = 0.0
            free = fixed < 0
            probabilities[free] = np.exp(one[free] - normalizer[free])
            result[:, indices] = rng.random(probabilities.shape) < probabilities
        return result

    def prior_log_probability(self, logits, z):
        """Log normalized constrained prior for an augmented hierarchy state."""
        logits = np.asarray(logits, dtype=float)
        raw_z = np.asarray(z)
        if (logits.ndim != 2 or logits.shape[0] == 0
                or logits.shape[1] != len(self.step_ids) or not np.isfinite(logits).all()
                or raw_z.shape != logits.shape or raw_z.dtype.kind not in "biu"
                or not np.isin(raw_z, [0, 1]).all()):
            raise ValueError("Need finite logits and aligned binary augmented occupancy state")
        z = raw_z.astype(bool, copy=False)
        for component in self.components:
            for _, antecedent, consequent in component["implications"]:
                if np.any(z[:, antecedent] & ~z[:, consequent]):
                    return -math.inf
        log_one, log_zero = _log_binary_prior(logits)
        total = float(np.sum(np.where(z, log_one, log_zero)))
        for component in self.components:
            indices, states = component["indices"], component["states"]
            one, zero = log_one[:, indices], log_zero[:, indices]
            prior = np.sum(
                np.where(states[None, :, :], one[:, None, :], zero[:, None, :]), axis=2)
            total -= float(np.sum(logsumexp(prior, axis=1)))
        return total

    def as_report(self):
        """Return a JSON-ready declaration and exact-enumeration qualification."""
        return {
            "schema_version": SCHEMA,
            "active": True,
            "step_ids": list(self.step_ids),
            "declaration": copy.deepcopy(self.declaration),
            "components": [{
                "step_ids": [self.step_ids[index] for index in component["indices"]],
                "implication_ids": [item[0] for item in component["implications"]],
                "allowed_state_count": int(len(component["states"])),
                "unconstrained_binary_state_count": int(1 << len(component["indices"])),
            } for component in self.components],
            "unconstrained_step_ids": [self.step_ids[index] for index in self.unconstrained],
            "method": "exact_connected_component_enumeration_with_parameter_dependent_prior_normalization",
            "maximum_component_size": MAX_COMPONENT_SIZE,
            "anchors_restrict_likelihood_not_prior_normalizer": True,
            "qualification": (
                "Caller-reviewed meaning constraint only. This helper does not verify source bytes or semantics, "
                "and it does not infer participation, paths, ordering, timing, burden, or observed truth."
            ),
        }
