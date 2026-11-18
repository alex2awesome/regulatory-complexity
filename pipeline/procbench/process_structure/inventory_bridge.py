"""Bind empirical full inventories to reviewed downstream route hypotheses.

This module performs no route interpretation.  A caller must supply one
reviewed route vector for every raw empirical inventory.  The bridge merely
checks that coverage, aggregates duplicate vectors, and remaps upstream draw
memberships into the exact downstream hypothesis order.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np

from ..joint_inventory_prior import (
    JointInventoryPrior,
    empirical_bridge_report,
    replay_upstream_indices,
)


SCHEMA = "process-inventory-bridge/1"
JOINT_SCHEMA = "v6-joint-inventory-prior/1"
FEEDBACK_POLICY = "downstream_evidence_updates_joint_inventory"
MASS_SCOPE = "supplied_empirical_draw_multiset_not_continuous_posterior"


def _names(values, label):
    if (not isinstance(values, list) or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or len(set(values)) != len(values)):
        raise ValueError(f"{label} must be a nonempty ordered list of distinct names")
    return list(values)


def _empirical(empirical):
    if not isinstance(empirical, dict):
        raise ValueError("Empirical joint inventory must be an explicit object")
    jurisdictions = _names(empirical.get("jurisdictions"), "Jurisdictions")
    steps = _names(empirical.get("steps"), "Steps")
    inventories = np.asarray(empirical.get("joint_inventories"))
    membership = np.asarray(empirical.get("upstream_draw_to_inventory"))
    probabilities = np.asarray(empirical.get("probabilities"), dtype=float)
    if (inventories.ndim != 3
            or inventories.shape[1:] != (len(jurisdictions), len(steps))
            or not len(inventories) or not np.isin(inventories, [0, 1]).all()):
        raise ValueError("Empirical inventories must be nonempty binary inventory-by-jurisdiction-by-step values")
    if (membership.ndim != 2 or not membership.size
            or not np.issubdtype(membership.dtype, np.integer)
            or np.any(membership < 0) or np.any(membership >= len(inventories))):
        raise ValueError("Upstream memberships must be nonempty chains-by-draws inventory indices")
    counts = np.bincount(membership.ravel(), minlength=len(inventories))
    if np.any(counts == 0):
        raise ValueError("Every empirical inventory must retain at least one supplied upstream draw")
    expected = counts / membership.size
    if (probabilities.shape != (len(inventories),)
            or not np.isfinite(probabilities).all() or np.any(probabilities <= 0)
            or not np.allclose(probabilities, expected, rtol=0, atol=2e-16)):
        raise ValueError("Empirical probabilities must equal supplied draw frequencies")
    shape = empirical.get("chain_draw_shape")
    if (not isinstance(shape, (list, tuple)) or list(shape) != list(membership.shape)
            or empirical.get("retained_mass") != 1
            or empirical.get("retained_mass_scope") != MASS_SCOPE
            or empirical.get("route_semantics_reviewed") is not False):
        raise ValueError("Empirical metadata must preserve the complete unreviewed supplied draw multiset")
    return jurisdictions, steps, inventories.astype(np.uint8), membership.astype(np.int64), counts


def _fingerprint(jurisdictions, steps, inventory):
    payload = json.dumps(
        {
            "jurisdictions": jurisdictions,
            "steps": steps,
            "joint_inventory": inventory.astype(int).tolist(),
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def inventory_fingerprints(empirical):
    """Return stable identities for mapping records; never infer route meaning."""
    jurisdictions, steps, inventories, _, _ = _empirical(empirical)
    return [
        {
            "raw_inventory_index": index,
            "raw_inventory_sha256": _fingerprint(jurisdictions, steps, inventory),
        }
        for index, inventory in enumerate(inventories)
    ]


def _reviewed_vectors(records, fingerprints, program_ids):
    if not isinstance(records, list) or len(records) != len(fingerprints):
        raise ValueError("Supply exactly one reviewed route vector for every raw inventory")
    by_index = {}
    reviewed_records = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Reviewed route mappings must be explicit objects")
        index = row.get("raw_inventory_index")
        routes = row.get("route_ids")
        if (isinstance(index, bool) or not isinstance(index, int)
                or index < 0 or index >= len(fingerprints) or index in by_index
                or row.get("raw_inventory_sha256") != fingerprints[index]["raw_inventory_sha256"]
                or row.get("route_vector_reviewed") is not True
                or not isinstance(row.get("review_note"), str) or not row["review_note"].strip()
                or not isinstance(routes, list) or len(routes) != len(program_ids)
                or any(not isinstance(route, str) or not route.strip() for route in routes)):
            raise ValueError("Each raw inventory needs one fingerprint-bound reviewed complete route vector")
        try:
            reviewed = json.loads(json.dumps(row, allow_nan=False))
        except (TypeError, ValueError) as error:
            raise ValueError("Reviewed route mapping provenance must be finite strict JSON") from error
        by_index[index] = tuple(routes)
        reviewed_records[index] = reviewed
    if set(by_index) != set(range(len(fingerprints))):
        raise ValueError("Reviewed route mapping has missing or extra raw inventory indices")
    return ([by_index[index] for index in range(len(fingerprints))],
            [reviewed_records[index] for index in range(len(fingerprints))])


def _attestations(evidence_partition_reviewed, evidence_partition_note,
                  route_semantics_reviewed, route_semantics_note):
    if (evidence_partition_reviewed is not True
            or route_semantics_reviewed is not True
            or not isinstance(evidence_partition_note, str) or not evidence_partition_note.strip()
            or not isinstance(route_semantics_note, str) or not route_semantics_note.strip()):
        raise ValueError("Bridge needs explicit reviewed partition and route-semantics attestations")
    return {
        "evidence_partition_reviewed": True,
        "evidence_partition_note": evidence_partition_note,
        "route_semantics_reviewed": True,
        "route_semantics_note": route_semantics_note,
        "attestation_scope": (
            "Caller-reviewed declarations only; this helper does not inspect sources, "
            "prove nonoverlap, or infer inventory-to-route semantics."
        ),
    }


def _declaration(program_ids, vectors, counts, attestations, supplied):
    unique_vectors = sorted(set(vectors))
    grouped_counts = {vector: 0 for vector in unique_vectors}
    for vector, count in zip(vectors, counts):
        grouped_counts[vector] += int(count)
    expected_mass = np.array([grouped_counts[vector] for vector in unique_vectors], dtype=float)
    expected_mass /= expected_mass.sum()

    if supplied is None:
        hypotheses = [
            {
                "id": f"joint_inventory_{index:04d}",
                "prior_weight": grouped_counts[vector],
                "route_ids": list(vector),
            }
            for index, vector in enumerate(unique_vectors)
        ]
        declaration = {
            "schema_version": JOINT_SCHEMA,
            "program_ids": list(program_ids),
            "feedback_policy": FEEDBACK_POLICY,
            "evidence_partition_reviewed": True,
            "evidence_partition_note": attestations["evidence_partition_note"],
            "route_semantics_reviewed": True,
            "hypotheses": hypotheses,
        }
        return declaration, unique_vectors, expected_mass

    if not isinstance(supplied, dict):
        raise ValueError("Downstream declaration must be an explicit object")
    if (supplied.get("schema_version") != JOINT_SCHEMA
            or supplied.get("program_ids") != program_ids
            or supplied.get("feedback_policy") != FEEDBACK_POLICY
            or supplied.get("evidence_partition_reviewed") is not True
            or supplied.get("evidence_partition_note") != attestations["evidence_partition_note"]
            or supplied.get("route_semantics_reviewed") is not True):
        raise ValueError("Downstream declaration has mismatched program order or review contract")
    rows = supplied.get("hypotheses")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Downstream declaration needs finite hypotheses")
    ids, supplied_vectors, weights = [], [], []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Downstream hypotheses must be explicit objects")
        name, routes, weight = row.get("id"), row.get("route_ids"), row.get("prior_weight")
        if (not isinstance(name, str) or not name.strip() or name in ids
                or not isinstance(routes, list) or len(routes) != len(program_ids)
                or any(not isinstance(route, str) or not route.strip() for route in routes)
                or isinstance(weight, bool) or not isinstance(weight, (int, float))
                or not math.isfinite(weight) or weight <= 0):
            raise ValueError("Downstream hypotheses need unique IDs, complete routes and positive finite weights")
        vector = tuple(routes)
        if vector in supplied_vectors:
            raise ValueError("Downstream declaration must aggregate duplicate route vectors")
        ids.append(name)
        supplied_vectors.append(vector)
        weights.append(float(weight))
    if set(supplied_vectors) != set(unique_vectors):
        raise ValueError("Downstream declaration has missing or extra route-vector support")
    weights = np.asarray(weights)
    scaled = weights / weights.max()
    if np.any(scaled == 0):
        raise ValueError("Downstream hypothesis weights lose positive support in normalization")
    normalized = scaled / scaled.sum()
    expected_by_vector = dict(zip(unique_vectors, expected_mass))
    expected_in_supplied_order = np.array([expected_by_vector[vector] for vector in supplied_vectors])
    if not np.allclose(normalized, expected_in_supplied_order, rtol=0, atol=2e-16):
        raise ValueError("Downstream hypothesis weights must equal aggregated supplied empirical mass")
    # Round-trip to a detached JSON-compatible object and reject non-JSON extras.
    try:
        declaration = json.loads(json.dumps(supplied, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ValueError("Downstream declaration must be finite strict JSON") from error
    return declaration, supplied_vectors, expected_in_supplied_order


def build_inventory_bridge(empirical, reviewed_route_vectors, program_ids, *,
                           downstream_declaration=None,
                           evidence_partition_reviewed,
                           evidence_partition_note,
                           route_semantics_reviewed,
                           route_semantics_note):
    """Aggregate reviewed route vectors and bind upstream draws to hypotheses."""
    program_ids = _names(program_ids, "Program IDs")
    jurisdictions, steps, inventories, membership, counts = _empirical(empirical)
    fingerprints = inventory_fingerprints(empirical)
    vectors, review_records = _reviewed_vectors(
        reviewed_route_vectors, fingerprints, program_ids
    )
    attestations = _attestations(
        evidence_partition_reviewed,
        evidence_partition_note,
        route_semantics_reviewed,
        route_semantics_note,
    )
    declaration, downstream_vectors, normalized_mass = _declaration(
        program_ids, vectors, counts, attestations, downstream_declaration
    )
    vector_to_index = {vector: index for index, vector in enumerate(downstream_vectors)}
    original_to_downstream = np.array([vector_to_index[vector] for vector in vectors], dtype=np.int64)
    remapped = original_to_downstream[membership]
    downstream_counts = np.bincount(remapped.ravel(), minlength=len(downstream_vectors))
    if (downstream_counts.sum() != membership.size
            or not np.allclose(downstream_counts / membership.size, normalized_mass,
                               rtol=0, atol=2e-16)):
        raise AssertionError("Internal bridge aggregation lost supplied draw mass")
    hypothesis_ids = [row["id"] for row in declaration["hypotheses"]]
    raw_rows = []
    for index, (vector, count, fingerprint, review_record) in enumerate(
        zip(vectors, counts, fingerprints, review_records)
    ):
        hi = int(original_to_downstream[index])
        raw_rows.append({
            **fingerprint,
            "supplied_draw_count": int(count),
            "route_ids": list(vector),
            "review_note": review_record["review_note"],
            "reviewed_route_mapping": review_record,
            "downstream_hypothesis_index": hi,
            "downstream_hypothesis_id": hypothesis_ids[hi],
        })
    hypotheses = []
    for hi, (name, vector, count) in enumerate(zip(hypothesis_ids, downstream_vectors, downstream_counts)):
        hypotheses.append({
            "downstream_hypothesis_index": hi,
            "downstream_hypothesis_id": name,
            "route_ids": list(vector),
            "supplied_draw_count": int(count),
            "empirical_probability": float(count / membership.size),
            "raw_inventory_indices": np.flatnonzero(original_to_downstream == hi).tolist(),
        })
    return {
        "schema_version": SCHEMA,
        "program_ids": program_ids,
        "jurisdictions": jurisdictions,
        "steps": steps,
        "supplied_chain_draw_shape": list(membership.shape),
        "supplied_draw_count": int(membership.size),
        "raw_inventory_count": len(inventories),
        "downstream_hypothesis_count": len(downstream_vectors),
        "hypothesis_ids": hypothesis_ids,
        "joint_inventory_prior": declaration,
        "remapped_upstream_draw_to_hypothesis": remapped.tolist(),
        "original_inventory_to_downstream": original_to_downstream.tolist(),
        "raw_inventories": raw_rows,
        "hypotheses": hypotheses,
        "retained_mass": 1.0,
        "retained_mass_scope": MASS_SCOPE,
        "attestations": attestations,
        "scientific_validation_complete": False,
        "qualification": (
            "Mechanical finite-draw aggregation only. Route decisions, source partition, "
            "upstream Monte Carlo support and scientific transportability remain external."
        ),
    }


def replay_inventory_bridge(bridge, prior, structural_draws, rng):
    """Replay upstream particles using only compiler-remapped memberships.

    Structural draws are ordinary saved V6 route-index vectors.  They are
    mapped through the actual ``JointInventoryPrior`` so declaration order,
    rather than a caller's guessed integer convention, determines membership.
    """
    if not isinstance(bridge, dict) or bridge.get("schema_version") != SCHEMA:
        raise ValueError("Need a reviewed process inventory bridge")
    if not isinstance(prior, JointInventoryPrior):
        raise ValueError("Replay requires the actual compiled JointInventoryPrior")
    if (bridge.get("joint_inventory_prior") != prior.declaration
            or bridge.get("hypothesis_ids") != prior.names):
        raise ValueError("Bridge declaration and ordered hypothesis IDs must match the compiled prior")
    membership = np.asarray(bridge.get("remapped_upstream_draw_to_hypothesis"))
    shape = bridge.get("supplied_chain_draw_shape")
    hypotheses = bridge.get("hypotheses")
    if (membership.ndim != 2 or not membership.size
            or not np.issubdtype(membership.dtype, np.integer)
            or np.any(membership < 0) or np.any(membership >= len(prior.names))
            or not isinstance(shape, list) or shape != list(membership.shape)
            or bridge.get("supplied_draw_count") != membership.size
            or bridge.get("downstream_hypothesis_count") != len(prior.names)
            or bridge.get("retained_mass") != 1.0
            or bridge.get("retained_mass_scope") != MASS_SCOPE
            or not isinstance(hypotheses, list) or len(hypotheses) != len(prior.names)):
        raise ValueError("Bridge remapped memberships or finite-mass metadata are inconsistent")
    counts = np.bincount(membership.ravel(), minlength=len(prior.names))
    if np.any(counts == 0):
        raise ValueError("Bridge membership must retain supplied draws for every hypothesis")
    for index, (row, name, count, probability, declaration) in enumerate(zip(
        hypotheses, prior.names, counts, prior.probabilities,
        prior.declaration["hypotheses"]
    )):
        if (not isinstance(row, dict)
                or row.get("downstream_hypothesis_index") != index
                or row.get("downstream_hypothesis_id") != name
                or row.get("route_ids") != declaration["route_ids"]
                or row.get("supplied_draw_count") != int(count)
                or not isinstance(row.get("empirical_probability"), (int, float))
                or isinstance(row.get("empirical_probability"), bool)
                or not math.isclose(row["empirical_probability"], count / membership.size,
                                    rel_tol=0, abs_tol=2e-16)
                or not math.isclose(float(probability), count / membership.size,
                                    rel_tol=0, abs_tol=2e-16)):
            raise ValueError("Bridge hypothesis masses/order do not match remapped draws and prior")
    structures = np.asarray(structural_draws)
    if (structures.ndim != 3 or structures.shape[2] != prior.states.shape[1]
            or not structures.size or not np.issubdtype(structures.dtype, np.integer)):
        raise ValueError("Structural draws must be nonempty chains-by-draws-by-program integer routes")
    selected = np.empty(structures.shape[:2], dtype=np.int64)
    for chain in range(structures.shape[0]):
        for draw in range(structures.shape[1]):
            selected[chain, draw] = prior.index(structures[chain, draw])
    indices = replay_upstream_indices(membership, selected, rng)
    return {
        "upstream_flat_indices": indices,
        "downstream_hypothesis_indices": selected,
        "empirical_bridge_report": empirical_bridge_report(membership, selected),
        "qualification": (
            "One shared empirical upstream particle index per downstream draw; "
            "finite supplied support only, not continuous-posterior reconstruction."
        ),
    }
