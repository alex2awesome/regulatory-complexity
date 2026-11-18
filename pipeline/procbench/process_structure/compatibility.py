"""Mass-preserving diagnostic classification of empirical occupancy draws.

This module is not a route compiler, likelihood, timing model or burden model.
Callers supply source-reviewed, mutually exclusive mask rules.  Every original
county/draw cell is retained and classified exactly once; unknown executions do
not become zero burden or disappear through renormalization.
"""
from __future__ import annotations

import copy
import math

import numpy as np


SCHEMA = "process-inventory-compatibility/1"
ATTESTATION_SCOPE = "caller_supplied_inventory_mask_classification"
RULE_FIELDS = {
    "rule_id", "status", "unresolved", "required_present", "required_absent",
    "minimum_present_count", "maximum_present_count", "source_reviewed", "source_note",
}
ENDPOINT_KINDS = {"finite", "unbounded", "unknown"}


def _ids(values, label):
    if (not isinstance(values, list) or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or len(set(values)) != len(values)):
        raise ValueError(f"{label} must be a nonempty ordered list of distinct IDs")
    return list(values)


def _attestation(value):
    if not isinstance(value, dict):
        raise ValueError("Compatibility rules require an explicit source-review attestation")
    refs = value.get("source_refs")
    if (value.get("reviewed") is not True or value.get("scope") != ATTESTATION_SCOPE
            or not isinstance(value.get("review_note"), str) or not value["review_note"].strip()
            or not isinstance(refs, list) or not refs):
        raise ValueError("Invalid compatibility source-review attestation")
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {"path", "sha256", "locator"}
                or not isinstance(ref["path"], str) or not ref["path"]
                or not isinstance(ref["locator"], str) or not ref["locator"]
                or not isinstance(ref["sha256"], str) or len(ref["sha256"]) != 64
                or any(character not in "0123456789abcdef" for character in ref["sha256"])):
            raise ValueError("Compatibility source references need path, SHA256 and locator")
    result = copy.deepcopy(value)
    result["attestation_scope"] = (
        "Caller-reviewed declaration only; this helper validates its form but does not read sources "
        "or prove route meaning, completeness or independence."
    )
    return result


def _rules(rules, steps):
    if not isinstance(rules, list) or not rules:
        raise ValueError("Need nonempty caller-supplied compatibility rules")
    step_set, seen = set(steps), set()
    parsed = []
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != RULE_FIELDS:
            raise ValueError("Compatibility rules must use the explicit reviewed schema")
        name, status = rule["rule_id"], rule["status"]
        present, absent = rule["required_present"], rule["required_absent"]
        lower, upper = rule["minimum_present_count"], rule["maximum_present_count"]
        if (not isinstance(name, str) or not name.strip() or name in seen
                or not isinstance(status, str) or not status.strip()
                or type(rule["unresolved"]) is not bool
                or rule["source_reviewed"] is not True
                or not isinstance(rule["source_note"], str) or not rule["source_note"].strip()
                or not isinstance(present, list) or not isinstance(absent, list)
                or any(not isinstance(step, str) for step in present + absent)
                or len(set(present)) != len(present) or len(set(absent)) != len(absent)
                or not set(present + absent) <= step_set or set(present) & set(absent)
                or type(lower) is not int or type(upper) is not int
                or not 0 <= lower <= upper <= len(steps)):
            raise ValueError("Malformed source-reviewed compatibility rule")
        seen.add(name)
        parsed.append(copy.deepcopy(rule))
    return parsed


def classify_inventory_draws(joint_presence, jurisdictions, step_ids, rules, *,
                             source_review_attestation):
    """Classify every aligned chain/draw/jurisdiction mask exactly once."""
    jurisdictions = _ids(jurisdictions, "Jurisdictions")
    steps = _ids(step_ids, "Steps")
    raw = np.asarray(joint_presence)
    if (raw.ndim != 4 or not raw.shape[0] or not raw.shape[1]
            or raw.shape[2:] != (len(jurisdictions), len(steps))
            or raw.dtype.kind not in "biu" or not np.isin(raw, [0, 1]).all()):
        raise ValueError("Need aligned chains-by-draws-by-jurisdictions-by-steps binary inventories")
    presence = raw.astype(np.uint8, copy=True)
    reviewed_rules = _rules(rules, steps)
    attestation = _attestation(source_review_attestation)
    index = {step: position for position, step in enumerate(steps)}
    present_count = presence.sum(axis=3)
    matches = []
    for rule in reviewed_rules:
        match = ((present_count >= rule["minimum_present_count"])
                 & (present_count <= rule["maximum_present_count"]))
        if rule["required_present"]:
            match &= presence[..., [index[step] for step in rule["required_present"]]].all(axis=3)
        if rule["required_absent"]:
            match &= ~presence[..., [index[step] for step in rule["required_absent"]]].any(axis=3)
        matches.append(match)
    match_count = np.sum(np.stack(matches, axis=-1), axis=-1)
    if np.any(match_count > 1):
        raise ValueError(f"Compatibility rules overlap on {int(np.sum(match_count > 1))} supplied cells")
    if np.any(match_count == 0):
        raise ValueError(f"Compatibility rules leave {int(np.sum(match_count == 0))} supplied cells uncovered")
    classification = np.argmax(np.stack(matches, axis=-1), axis=-1).astype(np.int64)
    total = classification.size

    rule_rows = []
    for rule_index, rule in enumerate(reviewed_rules):
        count = int(np.sum(classification == rule_index))
        rule_rows.append({
            "rule_index": rule_index,
            "rule_id": rule["rule_id"],
            "status": rule["status"],
            "unresolved": rule["unresolved"],
            "county_draw_cells": count,
            "mass": count / total,
            "source_note": rule["source_note"],
        })
    statuses = []
    for status in sorted({rule["status"] for rule in reviewed_rules}):
        selected = [i for i, rule in enumerate(reviewed_rules) if rule["status"] == status]
        count = int(np.sum(np.isin(classification, selected)))
        statuses.append({"status": status, "county_draw_cells": count, "mass": count / total})
    unresolved_indices = [i for i, rule in enumerate(reviewed_rules) if rule["unresolved"]]
    unresolved_count = int(np.sum(np.isin(classification, unresolved_indices)))
    by_jurisdiction = []
    denominator = classification.shape[0] * classification.shape[1]
    for ji, jurisdiction in enumerate(jurisdictions):
        county = classification[:, :, ji]
        by_jurisdiction.append({
            "jurisdiction_id": jurisdiction,
            "draws": denominator,
            "by_rule": {
                rule["rule_id"]: {
                    "count": int(np.sum(county == ri)),
                    "mass": float(np.mean(county == ri)),
                }
                for ri, rule in enumerate(reviewed_rules)
            },
            "unresolved_count": int(np.sum(np.isin(county, unresolved_indices))),
            "unresolved_mass": float(np.mean(np.isin(county, unresolved_indices))),
        })
    return {
        "schema_version": SCHEMA,
        "joint_presence": presence,
        "classification_index": classification,
        "draw_shape": list(presence.shape[:2]),
        "jurisdictions": jurisdictions,
        "steps": steps,
        "rules": reviewed_rules,
        "rule_summary": rule_rows,
        "status_summary": statuses,
        "county_draw_cells": total,
        "retained_county_draw_cells": total,
        "retained_mass": 1.0,
        "unresolved_count": unresolved_count,
        "unresolved_mass": unresolved_count / total,
        "by_jurisdiction": by_jurisdiction,
        "source_review_attestation": attestation,
        "route_vectors_created": False,
        "timings_created": False,
        "reweighted": False,
        "scientific_release_eligible": False,
        "qualification": (
            "Diagnostic classification of the supplied empirical draw multiset only; caller labels do not "
            "establish executable routes, participation, timing, burden or unseen posterior support."
        ),
    }


def _endpoint(value, side):
    if not isinstance(value, dict) or set(value) != {"kind", "value"} or value["kind"] not in ENDPOINT_KINDS:
        raise ValueError("Every identified-set endpoint needs explicit finite/unbounded/unknown status")
    kind, number = value["kind"], value["value"]
    if kind == "finite":
        if (isinstance(number, bool) or not isinstance(number, (int, float))
                or not math.isfinite(number)):
            raise ValueError("Finite identified-set endpoint needs a finite number")
        return kind, float(number)
    if number is not None:
        raise ValueError(f"{kind} identified-set endpoint must have null value")
    return kind, None


def _aggregate_endpoints(endpoints, side):
    kinds = [kind for kind, value in endpoints]
    if "unknown" in kinds:
        return {"kind": "unknown", "value": None}
    if "unbounded" in kinds:
        return {"kind": "unbounded", "value": None}
    return {"kind": "finite", "value": float(np.mean([value for kind, value in endpoints]))}


def summarize_burden_functional(compatibility, values, *, functional_id, unit,
                                identified_bounds=None):
    """Summarize an aligned functional without conditioning away missing cells.

    ``None`` is the only missing-value marker.  If any value is missing, the
    unconditional mean is null and its full missing mass is reported.  Optional
    per-cell identified bounds are aggregated only from explicit endpoint flags.
    """
    if (not isinstance(compatibility, dict) or compatibility.get("schema_version") != SCHEMA
            or compatibility.get("retained_mass") != 1.0
            or compatibility.get("reweighted") is not False):
        raise ValueError("Need a complete unreweighted compatibility result")
    classification = np.asarray(compatibility.get("classification_index"))
    rules = compatibility.get("rules")
    jurisdictions = compatibility.get("jurisdictions")
    if (classification.ndim != 3 or any(dimension == 0 for dimension in classification.shape)
            or classification.dtype.kind not in "iu"
            or not isinstance(rules, list) or not rules
            or not isinstance(jurisdictions, list) or not jurisdictions
            or len(jurisdictions) != classification.shape[2]
            or compatibility.get("draw_shape") != list(classification.shape[:2])
            or compatibility.get("county_draw_cells") != classification.size
            or compatibility.get("retained_county_draw_cells") != classification.size
            or np.any(classification < 0) or np.any(classification >= len(rules))):
        raise ValueError("Malformed or incomplete compatibility classification metadata")
    if not isinstance(functional_id, str) or not functional_id.strip() or not isinstance(unit, str) or not unit.strip():
        raise ValueError("Burden functional needs an explicit ID and unit")
    shape = classification.shape
    raw = np.asarray(values, dtype=object)
    if raw.shape != shape:
        raise ValueError("Functional values must align with every classified county draw")
    defined, numeric = np.zeros(shape, dtype=bool), np.zeros(shape, dtype=float)
    for location in np.ndindex(shape):
        value = raw[location]
        if value is None:
            continue
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
            raise ValueError("Defined burden values must be finite real numbers")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Defined burden values must be finite real numbers")
        defined[location], numeric[location] = True, value
    undefined_count = int(np.sum(~defined))
    result = {
        "schema_version": "process-inventory-partial-burden-summary/1",
        "functional_id": functional_id,
        "unit": unit,
        "aggregation_estimand": (
            "equal_weight_average_over_supplied_jurisdictions_not_applicant_population"
        ),
        "county_draw_cells": int(raw.size),
        "undefined_count": undefined_count,
        "undefined_mass": undefined_count / raw.size,
        "unconditional_mean": float(numeric.mean()) if defined.all() else None,
        "conditional_mean_reported": False,
        "reweighted": False,
        "identified_mean_bounds": None,
        "qualification": (
            "A null unconditional mean preserves missing draw mass; it is not a zero and no mean over "
            "the defined subset is reported. Bounds, when present, use caller-supplied endpoints only."
        ),
    }
    if identified_bounds is None:
        return result
    bounds = np.asarray(identified_bounds, dtype=object)
    if bounds.shape != shape:
        raise ValueError("Identified bounds must align with every classified county draw")
    lower, upper = [], []
    for location in np.ndindex(shape):
        item = bounds[location]
        if not isinstance(item, dict) or set(item) != {"lower", "upper"}:
            raise ValueError("Each identified set needs explicit lower and upper endpoints")
        lo, hi = _endpoint(item["lower"], "lower"), _endpoint(item["upper"], "upper")
        if lo[0] == hi[0] == "finite" and lo[1] > hi[1]:
            raise ValueError("Finite identified-set lower bound exceeds upper bound")
        if defined[location] and ((lo[0] == "finite" and numeric[location] < lo[1])
                                  or (hi[0] == "finite" and numeric[location] > hi[1])):
            raise ValueError("Defined burden value falls outside its finite identified bounds")
        lower.append(lo)
        upper.append(hi)
    result["identified_mean_bounds"] = {
        "lower": _aggregate_endpoints(lower, "lower"),
        "upper": _aggregate_endpoints(upper, "upper"),
        "within_set_probabilities_assigned": False,
    }
    return result
