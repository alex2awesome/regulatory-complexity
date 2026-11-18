"""Optional shared categorical jurisdiction assignment for a reading unit.

An uncertain source is assigned once for its entire reviewed step checklist, not
independently per quote or step. Candidate priors must be declared from reviewed
identity information, never manufactured by copying another commenter's county.
This module supplies Gibbs conditionals; it does not decide identities in text.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import logsumexp, xlog1py, xlogy


SCHEMA = "process-occupancy-evidence/2"


def _scope_overlap(left, right):
    """Conservative overlap of canonical logical locators in identical bytes.

    Distinct JSON roots in one bulk file are allowed. Canonical scope locators,
    not arbitrary quotation spans, must be supplied by the reviewed registry.
    Undeclared aliases still require semantic review; this is not entity NLP.
    """
    if left["sha256"] != right["sha256"]:
        return False
    a, b = left["locator"], right["locator"]
    return a == b or any(b.startswith(a + sep) or a.startswith(b + sep)
                         for sep in (".", "/", "["))


class JurisdictionAssignments:
    def __init__(self, evidence, ref_validator):
        self.evidence = evidence
        data = evidence.data
        self.units = data.get("uncertain_jurisdiction_units", [])
        if not isinstance(self.units, list):
            raise ValueError("Uncertain jurisdiction units must be an explicit list")
        if self.units and data.get("schema_version") != SCHEMA:
            raise ValueError("Uncertain jurisdiction evidence requires contract /2, not a silently ignored extension")
        J, S, K = len(evidence.j), len(evidence.s), len(evidence.k)
        self.base_positive = evidence.positive.copy()
        self.base_negative = evidence.negative.copy()
        self.positive = np.zeros((len(self.units), S, K), dtype=int)
        self.negative = np.zeros_like(self.positive)
        self.priors = np.zeros((len(self.units), J))
        existing_groups = {r["dependence_group_id"] for r in data["observations"]}
        existing_units = {r["unit_id"] for r in data["observations"] + data["known_presence"]}
        existing_support = {(ref["sha256"], ref["locator"], row["step_id"])
                            for row in data["observations"] + data["known_presence"] for ref in row["evidence_refs"]}
        existing_scopes = {}
        scope_owners = {}
        unscoped_hashes = set()
        if self.units or data.get("schema_version") == SCHEMA:
            for row in data["observations"] + data["known_presence"]:
                scope_id, refs = row.get("identity_scope_id"), row.get("identity_scope_refs")
                if scope_id is None and refs is None:
                    unscoped_hashes.update(r["sha256"] for r in row["evidence_refs"])
                elif not isinstance(scope_id, str) or not scope_id.strip() or row.get("identity_scope_reviewed") is not True:
                    raise ValueError("Resolved source identity scopes must be explicitly reviewed")
                else:
                    ref_validator({"evidence_refs": refs})
                    owner = row.get("dependence_group_id", row["unit_id"]), row["jurisdiction_id"]
                    if scope_id in existing_scopes:
                        if existing_scopes[scope_id] != refs or scope_owners[scope_id] != owner:
                            raise ValueError("Canonical resolved identity scope changes owner or references across steps")
                    elif any(_scope_overlap(ref, old) for ref in refs
                             for old_refs in existing_scopes.values() for old in old_refs):
                        raise ValueError("Resolved identity scopes overlap across distinct episodes")
                    existing_scopes[scope_id] = refs
                    scope_owners[scope_id] = owner
        self.refs = []
        for h, unit in enumerate(self.units):
            uid, group, kind = unit.get("unit_id"), unit.get("dependence_group_id"), unit.get("source_type")
            if (not isinstance(uid, str) or not uid.strip() or not isinstance(group, str) or not group.strip()
                    or kind not in evidence.k or uid in existing_units or group in existing_groups):
                raise ValueError("Uncertain reading must have a unique reviewed source unit/group/type")
            if (unit.get("identity_reviewed") is not True or unit.get("candidate_scope_complete") is not True
                    or not isinstance(unit.get("assignment_prior_basis"), str) or not unit["assignment_prior_basis"].strip()):
                raise ValueError("Declare reviewed candidate completeness and identity-prior basis")
            scope_id, scope_refs = unit.get("identity_scope_id"), unit.get("identity_scope_refs")
            if (not isinstance(scope_id, str) or not scope_id.strip()
                    or unit.get("identity_scope_reviewed") is not True):
                raise ValueError("Uncertain source needs reviewed canonical episode identity scope")
            ref_validator({"evidence_refs": scope_refs})
            ref_validator({"evidence_refs": unit.get("assignment_prior_refs")})
            if unit.get("assignment_prior_kind") not in {"symmetric_bounded_context", "reviewed_candidate_weights"}:
                raise ValueError("Declare whether candidate weights are symmetric context or reviewed weights")
            if (scope_id in existing_scopes
                    or any(ref["sha256"] in unscoped_hashes for ref in scope_refs)
                    or any(_scope_overlap(ref, old) for ref in scope_refs
                           for old_refs in existing_scopes.values() for old in old_refs)):
                raise ValueError("Canonical identity scope overlaps an already counted or unresolved source episode")
            existing_scopes[scope_id] = scope_refs
            self.refs.extend(scope_refs + unit["assignment_prior_refs"])
            existing_units.add(uid)
            existing_groups.add(group)
            candidates = unit.get("candidates")
            if not isinstance(candidates, list) or not candidates:
                raise ValueError("Uncertain identity needs supported jurisdiction candidates")
            seen_candidates = set()
            for candidate in candidates:
                jid, weight = candidate.get("jurisdiction_id"), candidate.get("prior_weight")
                if (jid not in evidence.j or jid in seen_candidates or isinstance(weight, bool)
                        or not isinstance(weight, (float, int)) or not math.isfinite(weight) or weight <= 0):
                    raise ValueError("Candidate jurisdiction priors must be distinct, supported, finite and positive")
                seen_candidates.add(jid)
                self.priors[h, evidence.j[jid]] = weight
            self.priors[h] /= self.priors[h].max()
            self.priors[h] /= self.priors[h].sum()
            if any(self.priors[h, evidence.j[jid]] <= 0 for jid in seen_candidates):
                raise ValueError('Candidate prior normalization underflow would remove positive identity support')
            if (unit["assignment_prior_kind"] == "symmetric_bounded_context"
                    and len({c["prior_weight"] for c in candidates}) != 1):
                raise ValueError("A declared symmetric identity prior must have equal candidate weights")
            rows = unit.get("readings")
            if not isinstance(rows, list) or not rows:
                raise ValueError("Uncertain source needs explicit reviewed readings")
            scope = unit.get("reviewed_step_ids")
            scope_kind = unit.get('reading_scope_kind', 'complete_fixed_universe')
            if scope_kind not in {'complete_fixed_universe', 'reviewed_fixed_subset'}:
                raise ValueError('Unknown uncertain-source reading scope kind')
            if scope_kind == 'reviewed_fixed_subset':
                if (unit.get('step_scope_reviewed') is not True
                        or not isinstance(unit.get('step_scope_rationale'), str)
                        or not unit['step_scope_rationale'].strip()):
                    raise ValueError('A partial checklist needs an explicit reviewed step-scope rationale')
                ref_validator({'evidence_refs': unit.get('step_scope_refs')})
                self.refs.extend(unit['step_scope_refs'])
            if (not isinstance(scope, list) or not scope
                    or any(not isinstance(step, str) for step in scope)
                    or len(set(scope)) != len(scope) or not set(scope) <= set(evidence.s)
                    or len(rows) != len(scope)
                    or (scope_kind == 'complete_fixed_universe' and set(scope) != set(evidence.s))):
                raise ValueError("Uncertain source requires exactly the complete reviewed fixed step checklist")
            seen_steps = set()
            for row in rows:
                step = row.get("step_id")
                if (step not in evidence.s or step in seen_steps or type(row.get("detected")) is not bool
                        or row.get("reviewed_scope") is not True):
                    raise ValueError("Uncertain source has duplicate, unresolved or unreviewed step readings")
                seen_steps.add(step)
                ref_validator(row)
                for ref in row["evidence_refs"]:
                    signature = ref["sha256"], ref["locator"], step
                    if signature in existing_support:
                        raise ValueError("Uncertain source duplicates already counted reading/anchor support")
                    existing_support.add(signature)
                    self.refs.append(ref)
                values = self.positive if row["detected"] else self.negative
                values[h, evidence.s[step], evidence.k[kind]] += 1
            if seen_steps != set(scope):
                raise ValueError("Uncertain readings do not cover the complete reviewed scope")
            if evidence.false_positive[evidence.k[kind]] == 0:
                needed = self.positive[h].sum(axis=-1) > 0
                possible = np.all(evidence.anchors[:, needed] != 0, axis=1)
                if not np.any(possible & (self.priors[h] > 0)):
                    raise ValueError("All candidate jurisdictions contradict a zero-error positive reading")

    def set_assignments(self, assignments):
        """Rebuild sufficient statistics for the current shared assignments."""
        a = np.asarray(assignments)
        if (a.shape != (len(self.units),) or not np.issubdtype(a.dtype, np.integer)
                or np.any(a < 0) or np.any(a >= self.priors.shape[1])
                or any(self.priors[h, j] <= 0 for h, j in enumerate(a))):
            raise ValueError("Invalid source-level jurisdiction assignment")
        self.evidence.positive = self.base_positive.copy()
        self.evidence.negative = self.base_negative.copy()
        np.add.at(self.evidence.positive, a, self.positive)
        np.add.at(self.evidence.negative, a, self.negative)

    def conditional_probabilities(self, presence, detection):
        """P(a_h=j | z,p,y_h, identity context), jointly across the unit's steps."""
        z, p = np.asarray(presence), np.asarray(detection)
        e = self.evidence
        if (z.shape != e.anchors.shape or p.shape != e.a.shape
                or not np.isin(z, [0, 1]).all() or not np.isfinite(p).all()
                or np.any(p <= 0) or np.any(p >= 1)):
            raise ValueError("Invalid presence/detection state for identity update")
        report = np.where(z[:, :, None], p, e.false_positive)
        result = np.empty_like(self.priors)
        for h in range(len(self.units)):
            likelihood = np.sum(xlogy(self.positive[h], report) + xlog1py(self.negative[h], -report), axis=(1, 2))
            with np.errstate(divide="ignore"):
                log_weights = np.log(self.priors[h]) + likelihood
            normalizer = logsumexp(log_weights)
            if not np.isfinite(normalizer):
                raise FloatingPointError("Uncertain source has no supported jurisdiction at this state")
            result[h] = np.exp(log_weights-normalizer)
        return result

    def sample(self, probabilities, rng):
        return np.array([rng.choice(len(row), p=row) for row in probabilities], dtype=np.int32)

    def restore_resolved_counts(self):
        self.evidence.positive = self.base_positive.copy()
        self.evidence.negative = self.base_negative.copy()
