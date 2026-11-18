"""Deterministic materializer for provisional S07 structural source rows.

The caller supplies the reviewed normalized draft and additive event/fee design
explicitly.  This module has no dependency on gitignored runs paths and does not
generate cases, a world, render specifications, prose, fits, or scores.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from .s07_fresh_replica import validate_declared_public_leak_policy


WORLD_ID = "S07_PILOT_20260920_R01"
RESOLVED_SCHEMA_VERSION = "s07-resolved-structural-source/2"
PUBLIC_SCHEMA_VERSION = "s07-public-structural-source/2"
ROUTES = frozenset(("parallel_standard", "serial_standard", "no_preinstall_approval"))
JURISDICTIONS = tuple(f"R01J{i:02d}" for i in range(1, 13))
EXPECTED_PROFILES = {
    "R01J06": "A", "R01J08": "B", "R01J10": "C", "R01J03": "D",
    "R01J05": "A", "R01J04": "B", "R01J07": "C", "R01J12": "D",
    "R01J09": "A", "R01J01": "B", "R01J02": "C", "R01J11": "D",
}
EXPECTED_UTILITIES = {
    "R01J06": "U01", "R01J08": "U01", "R01J10": "U02", "R01J03": "U02",
    "R01J05": "U03", "R01J04": "U03", "R01J07": "U04", "R01J12": "U04",
    "R01J09": "U05", "R01J01": "U05", "R01J02": "U06", "R01J11": "U06",
}
EXPECTED_PHASE_EVENT_DEPENDENCIES = (
    ("all", "first_permit_submission", "all_of", ("design_complete",)),
    ("all", "corrected_permit_submission", "all_of", ("first_permit_submission", "permit_correction_requested")),
    ("all", "final_permit_approval", "all_of", ("first_permit_submission",)),
    ("parallel_standard", "preinstall_interconnection_submission", "all_of", ("design_complete",)),
    ("parallel_standard", "preinstall_interconnection_approval", "all_of", ("preinstall_interconnection_submission",)),
    ("parallel_standard", "installation_start", "all_of", ("final_permit_approval", "preinstall_interconnection_approval")),
    ("serial_standard", "preinstall_interconnection_submission", "all_of", ("final_permit_approval",)),
    ("serial_standard", "preinstall_interconnection_approval", "all_of", ("preinstall_interconnection_submission",)),
    ("serial_standard", "installation_start", "all_of", ("final_permit_approval", "preinstall_interconnection_approval")),
    ("no_preinstall_approval", "installation_start", "all_of", ("final_permit_approval",)),
    ("all", "installation_complete", "all_of", ("installation_start",)),
    ("all", "inspection_request", "all_of", ("installation_complete",)),
    ("all", "reinspection_request", "all_of", ("inspection_failed", "inspection_correction_completed")),
    ("all", "final_passed_inspection", "any_of", ("inspection_request", "reinspection_request")),
    ("all", "final_interconnection_request", "all_of", ("final_passed_inspection",)),
    ("all", "permission_to_operate_granted", "all_of", ("final_interconnection_request",)),
)

AUTHORITY_FIELDS = frozenset((
    "authority_claim_id", "fictional_issuer_id", "jurisdiction_id",
    "authority_kind", "effective_start", "effective_end", "scope",
    "public_citation_label",
))
ENCOUNTER_FIELDS = frozenset((
    "encounter_id", "actor_id", "actor_type", "action", "object",
    "recipient_or_counterparty", "trigger", "phase_id", "route_applicability",
    "required_status", "submission_or_contact_channel", "authority_claim_id",
    "prerequisite_encounter_ids", "event_prerequisite_mode",
    "event_prerequisites",
))
DOCUMENT_FIELDS = frozenset((
    "document_requirement_id", "public_name", "supplied_by_actor_type",
    "received_by_actor_type", "trigger", "phase_id", "route_applicability",
    "required_status", "authority_claim_id", "accepted_variants", "copy_count",
))
CHECKLIST_FIELDS = frozenset((
    "checklist_item_id", "responsible_actor_type", "action",
    "evidence_or_object", "trigger", "phase_id", "route_applicability",
    "pass_fail_effect", "authority_claim_id",
))
FEE_FIELDS = frozenset((
    "charge_id", "canonical_charge_key", "public_name", "amount", "currency",
    "payer_actor_type", "collector_actor_id", "authority_claim_id", "trigger",
    "phase_id", "route_applicability", "frequency", "refundable_status",
    "waiver_or_exemption_rule", "effective_start", "effective_end",
    "applicability_date_basis", "applicability_date_event",
    "locked_through_case_completion",
))
WORKED_TOTAL_FIELDS = frozenset(("example_id", "route", "multiplicities", "total"))
SOURCE_FIELDS = frozenset((
    "schema_version", "world_id", "jurisdiction_id", "utility_id", "actors", "money_context",
    "authorities", "phase_event_dependencies", "applicant_encounters", "required_documents",
    "checklist_items", "fee_schedule", "worked_fee_examples",
))
ACTOR_FIELDS = frozenset((
    "filer_actor_id", "filer_actor_type", "represented_party_actor_id",
    "represented_party_actor_type", "fee_payer_actor_id",
    "fee_payer_actor_type", "relationship", "ahj_actor", "utility_actor",
))
MONEY_CONTEXT_FIELDS = frozenset((
    "source_currency_label", "materialized_currency_code", "price_status",
    "normalization_method", "amounts_unchanged", "fx_conversion_performed",
    "public_disclaimer",
))
PHASE_RULE_FIELDS = frozenset((
    "phase_rule_id", "jurisdiction_id", "route", "event", "mode", "requires",
    "source_design_schema", "source_rule_index",
))

_TOKEN_RE = re.compile(r"\$\{([^{}]+)\}")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class StructuralSourceError(ValueError):
    """Raised when normalized or resolved structural source data is invalid."""


def _strict_date(value: Any, field: str) -> date:
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise StructuralSourceError(f"{field} must be strict YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise StructuralSourceError(f"{field} is not a valid date: {value}") from exc


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise StructuralSourceError(f"{field} must be a nonempty string")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StructuralSourceError(f"{field} must be a nonnegative integer, not boolean")
    return value


def _lookup_token(token: str, bindings: Mapping[str, Any]) -> Any:
    if token.startswith("fee_amounts."):
        key = token.removeprefix("fee_amounts.")
        amounts = bindings.get("fee_amounts")
        if not isinstance(amounts, Mapping) or key not in amounts:
            raise StructuralSourceError(f"missing token binding: {token}")
        return amounts[key]
    if token not in bindings:
        raise StructuralSourceError(f"unknown or missing token binding: {token}")
    return bindings[token]


def _resolve_tokens(value: Any, bindings: Mapping[str, Any]) -> Any:
    if isinstance(value, Mapping):
        return {key: _resolve_tokens(child, bindings) for key, child in value.items()}
    if isinstance(value, list):
        return [_resolve_tokens(child, bindings) for child in value]
    if not isinstance(value, str):
        return copy.deepcopy(value)
    matches = list(_TOKEN_RE.finditer(value))
    if not matches:
        if "${" in value:
            raise StructuralSourceError(f"malformed unresolved token: {value}")
        return value
    if len(matches) == 1 and matches[0].span() == (0, len(value)):
        return copy.deepcopy(_lookup_token(matches[0].group(1), bindings))
    result = value
    for match in matches:
        replacement = _lookup_token(match.group(1), bindings)
        if not isinstance(replacement, str):
            raise StructuralSourceError(
                f"non-string token {match.group(1)} cannot be embedded in text"
            )
        result = result.replace(match.group(0), replacement)
    if "${" in result:
        raise StructuralSourceError(f"unresolved token after substitution: {result}")
    return result


def _contains_token(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_token(key) or _contains_token(child) for key, child in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_token(child) for child in value)
    return isinstance(value, str) and "${" in value


def canonical_charge_key(row: Mapping[str, Any]) -> str:
    fields = ("charge_id", "collector_actor_id", "authority_claim_id", "trigger", "effective_start")
    return "|".join(_nonempty_string(row.get(field), field) for field in fields)


def _require_fields(
    row: Mapping[str, Any],
    required: frozenset[str],
    label: str,
    *,
    allowed: frozenset[str] | None = None,
) -> None:
    if not isinstance(row, Mapping):
        raise StructuralSourceError(f"{label} must be a mapping")
    missing = required - set(row)
    if missing:
        raise StructuralSourceError(f"{label} missing fields: {sorted(missing)}")
    extras = set(row) - (required if allowed is None else allowed)
    if extras:
        raise StructuralSourceError(f"{label} has unknown fields: {sorted(extras)}")


def _validate_design(design: Mapping[str, Any]) -> None:
    if design.get("schema_version") != "s07_structural_additive_event_fee_design/2":
        raise StructuralSourceError("unknown additive design schema_version")
    if design.get("predecessor_sha256") != "b8f468ea7d365f0dfbfc5c773e1c393f9f9c4c2d366369323c9c2750e3172004":
        raise StructuralSourceError("additive design predecessor binding mismatch")
    if design.get("world_id") != WORLD_ID:
        raise StructuralSourceError("additive design world_id mismatch")
    if set(design.get("known_routes", [])) != set(ROUTES):
        raise StructuralSourceError("additive design known_routes mismatch")
    known_events_raw = design.get("known_events")
    if (
        not isinstance(known_events_raw, list)
        or not known_events_raw
        or any(not isinstance(item, str) or not item for item in known_events_raw)
        or len(known_events_raw) != len(set(known_events_raw))
    ):
        raise StructuralSourceError("additive design known_events must be unique strings")
    known_events = set(known_events_raw)

    encounter_rules = design.get("encounter_event_prerequisites")
    if not isinstance(encounter_rules, Mapping) or not encounter_rules:
        raise StructuralSourceError("additive design lacks encounter_event_prerequisites")
    for template_id, rule in encounter_rules.items():
        _nonempty_string(template_id, "encounter event template ID")
        _require_fields(rule, frozenset(("mode", "events")), f"encounter rule {template_id}")
        if rule["mode"] != "all_of":
            raise StructuralSourceError(f"encounter rule {template_id} must use all_of")
        events = rule["events"]
        if (
            not isinstance(events, list)
            or not events
            or any(event not in known_events for event in events)
            or len(events) != len(set(events))
        ):
            raise StructuralSourceError(
                f"encounter rule {template_id} has missing, duplicate, or unknown events"
            )

    dependencies = design.get("phase_event_dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise StructuralSourceError("additive design lacks phase_event_dependencies")
    signatures: set[tuple[str, str]] = set()
    graph: dict[str, set[str]] = {event: set() for event in known_events}
    for index, dependency in enumerate(dependencies):
        label = f"phase_event_dependencies[{index}]"
        _require_fields(
            dependency,
            frozenset(("route", "event", "mode", "requires")),
            label,
        )
        route = dependency["route"]
        event = dependency["event"]
        mode = dependency["mode"]
        required = dependency["requires"]
        if route not in ROUTES and route != "all":
            raise StructuralSourceError(f"{label}.route is unknown")
        if event not in known_events:
            raise StructuralSourceError(f"{label}.event is unknown")
        if mode not in ("all_of", "any_of"):
            raise StructuralSourceError(f"{label}.mode is unknown")
        if (
            not isinstance(required, list)
            or not required
            or any(item not in known_events for item in required)
            or len(required) != len(set(required))
        ):
            raise StructuralSourceError(f"{label}.requires has missing, duplicate, or unknown events")
        if event in required:
            raise StructuralSourceError(f"{label} is self-referential")
        signature = (route, event)
        if signature in signatures:
            raise StructuralSourceError(f"duplicate phase-event dependency: {signature}")
        signatures.add(signature)
        graph[event].update(required)

    normalized_dependencies = tuple(
        (row["route"], row["event"], row["mode"], tuple(row["requires"]))
        for row in dependencies
    )
    if normalized_dependencies != EXPECTED_PHASE_EVENT_DEPENDENCIES:
        raise StructuralSourceError("phase-event dependencies differ from the exact effective design")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(event: str) -> None:
        if event in visiting:
            raise StructuralSourceError(f"phase-event dependency cycle at {event}")
        if event in visited:
            return
        visiting.add(event)
        for predecessor in graph[event]:
            visit(predecessor)
        visiting.remove(event)
        visited.add(event)

    for event in graph:
        visit(event)

    fee_lock = design.get("fee_schedule_lock")
    if not isinstance(fee_lock, Mapping):
        raise StructuralSourceError("additive design lacks fee_schedule_lock")
    if fee_lock.get("applicability_date_basis") != "case_schedule_version_locked_at_event":
        raise StructuralSourceError("fee schedule has the wrong applicability_date_basis")
    if fee_lock.get("applicability_date_event") != "first_permit_submission":
        raise StructuralSourceError("fee schedule has the wrong applicability_date_event")
    start = _strict_date(fee_lock.get("eligible_initial_date_start"), "fee lock start")
    end = _strict_date(fee_lock.get("eligible_initial_date_end"), "fee lock end")
    if end < start:
        raise StructuralSourceError("fee schedule eligible dates are reversed")
    for field in (
        "locked_through_case_completion",
        "later_required_steps_and_repeats_use_locked_version",
        "after_cutoff_private_future_may_use_locked_version",
        "public_claims_must_remain_cutoff_safe",
        "no_new_schedule_after_effective_end_is_invented",
    ):
        if fee_lock.get(field) is not True:
            raise StructuralSourceError(f"fee schedule lock requires {field}=true")

    money = design.get("money_unit_normalization")
    if not isinstance(money, Mapping):
        raise StructuralSourceError("additive design lacks money_unit_normalization")
    _require_fields(money, MONEY_CONTEXT_FIELDS, "money_unit_normalization")
    if money["source_currency_label"] != "Fictional USD":
        raise StructuralSourceError("money normalization source label mismatch")
    if money["materialized_currency_code"] != "USD":
        raise StructuralSourceError("materialized money unit must use USD")
    if money["price_status"] != "fictional_design_price":
        raise StructuralSourceError("money normalization lacks fictional price status")
    for field in ("normalization_method", "public_disclaimer"):
        _nonempty_string(money[field], f"money_unit_normalization.{field}")
    if money["amounts_unchanged"] is not True or money["fx_conversion_performed"] is not False:
        raise StructuralSourceError("money normalization must preserve amounts without FX conversion")

    expected_counts = design.get("expected_materialized_counts_per_jurisdiction")
    count_fields = frozenset((
        "authorities", "applicant_encounters", "required_documents",
        "checklist_items", "fee_schedule", "worked_fee_examples",
        "phase_event_dependencies",
    ))
    if not isinstance(expected_counts, Mapping):
        raise StructuralSourceError("additive design lacks expected materialized counts")
    _require_fields(expected_counts, count_fields, "expected materialized counts")
    for field in count_fields:
        _nonnegative_int(expected_counts[field], f"expected count {field}")
    if expected_counts["phase_event_dependencies"] != len(EXPECTED_PHASE_EVENT_DEPENDENCIES):
        raise StructuralSourceError("phase-event dependency count differs from the effective design")

    phase_materialization = design.get("phase_rule_materialization")
    expected_phase_materialization = {
        "resolved_collection": "phase_event_dependencies",
        "publicly_projected": True,
        "rule_id_components": ["jurisdiction_id", "route", "event"],
        "source_lineage_fields": ["source_design_schema", "source_rule_index"],
        "source_rule_index_semantics": "zero-based index into this design's phase_event_dependencies array",
        "qualification": "The resolved rows restate this fictional design rule with jurisdiction-local identity; they do not assert real law.",
    }
    if phase_materialization != expected_phase_materialization:
        raise StructuralSourceError("phase-rule materialization contract mismatch")


def _validate_routes(row: Mapping[str, Any], label: str) -> None:
    routes = row.get("route_applicability")
    if not isinstance(routes, list) or not routes or any(route not in ROUTES for route in routes):
        raise StructuralSourceError(f"{label}.route_applicability must contain known routes")
    if len(routes) != len(set(routes)):
        raise StructuralSourceError(f"{label}.route_applicability contains duplicates")


def _validate_preinstall_route_absence(
    row: Mapping[str, Any], label: str, identity: str,
) -> None:
    is_preinstall = row.get("phase_id") == "preinstall_ix" or ".PREIX" in identity
    if not is_preinstall:
        return
    if row.get("phase_id") != "preinstall_ix":
        raise StructuralSourceError(f"{label} PREIX identity must use phase_id=preinstall_ix")
    if "no_preinstall_approval" in row.get("route_applicability", []):
        raise StructuralSourceError(f"{label} PREIX declaration is forbidden on no_preinstall_approval")


def _validate_authorities(rows: list[dict], jid: str) -> set[str]:
    ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"authorities[{index}]"
        _require_fields(row, AUTHORITY_FIELDS, label)
        authority_id = _nonempty_string(row["authority_claim_id"], f"{label}.authority_claim_id")
        if authority_id in ids:
            raise StructuralSourceError(f"duplicate authority_claim_id: {authority_id}")
        ids.add(authority_id)
        if row["jurisdiction_id"] != jid:
            raise StructuralSourceError(f"{label}.jurisdiction_id mismatch")
        for field in AUTHORITY_FIELDS - {"effective_start", "effective_end"}:
            _nonempty_string(row[field], f"{label}.{field}")
        start = _strict_date(row["effective_start"], f"{label}.effective_start")
        end = _strict_date(row["effective_end"], f"{label}.effective_end")
        if end < start:
            raise StructuralSourceError(f"{label} effective dates are reversed")
        if "fictional" not in row["public_citation_label"].casefold():
            raise StructuralSourceError(f"{label} public citation lacks fictional qualification")
    return ids


def _validate_encounters(rows: list[dict], authority_ids: set[str], known_events: set[str]) -> set[str]:
    ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"applicant_encounters[{index}]"
        _require_fields(row, ENCOUNTER_FIELDS, label)
        encounter_id = _nonempty_string(row["encounter_id"], f"{label}.encounter_id")
        if encounter_id in ids:
            raise StructuralSourceError(f"duplicate encounter_id: {encounter_id}")
        ids.add(encounter_id)
        for field in (
            "actor_id", "actor_type", "action", "object", "recipient_or_counterparty",
            "trigger", "phase_id", "required_status", "submission_or_contact_channel",
            "authority_claim_id",
        ):
            _nonempty_string(row[field], f"{label}.{field}")
        if row["actor_id"] != "applicant_installer" or row["actor_type"] != "installer_applicant":
            raise StructuralSourceError(f"{label} must make the installer filer explicit")
        if row["authority_claim_id"] not in authority_ids:
            raise StructuralSourceError(f"{label} has unresolved authority_claim_id")
        if row["required_status"] not in ("required", "conditional", "optional", "not_applicable"):
            raise StructuralSourceError(f"{label} has unknown required_status")
        _validate_routes(row, label)
        _validate_preinstall_route_absence(row, label, encounter_id)
        prereqs = row["prerequisite_encounter_ids"]
        if not isinstance(prereqs, list) or any(not isinstance(item, str) for item in prereqs):
            raise StructuralSourceError(f"{label}.prerequisite_encounter_ids must be strings")
        if len(prereqs) != len(set(prereqs)):
            raise StructuralSourceError(f"{label} has duplicate encounter prerequisites")
        if row["event_prerequisite_mode"] != "all_of":
            raise StructuralSourceError(f"{label} requires typed all_of event prerequisites")
        events = row["event_prerequisites"]
        if not isinstance(events, list) or not events or any(event not in known_events for event in events):
            raise StructuralSourceError(f"{label} has missing or unknown event prerequisites")
        if len(events) != len(set(events)):
            raise StructuralSourceError(f"{label} has duplicate event prerequisites")

    graph: dict[str, list[str]] = {}
    by_id = {row["encounter_id"]: row for row in rows}
    for row in rows:
        encounter_id = row["encounter_id"]
        prereqs = row["prerequisite_encounter_ids"]
        for prereq in prereqs:
            if prereq not in by_id:
                raise StructuralSourceError(f"{encounter_id} has unresolved prerequisite: {prereq}")
            if not set(row["route_applicability"]).issubset(by_id[prereq]["route_applicability"]):
                raise StructuralSourceError(f"{encounter_id} prerequisite has incompatible route")
        graph[encounter_id] = list(prereqs)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise StructuralSourceError(f"encounter prerequisite cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for prior in graph[node]:
            visit(prior)
        visiting.remove(node)
        visited.add(node)

    for encounter_id in graph:
        visit(encounter_id)
    return ids


def _validate_documents(rows: list[dict], authority_ids: set[str]) -> set[str]:
    ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"required_documents[{index}]"
        allowed = DOCUMENT_FIELDS | frozenset(("condition",))
        _require_fields(row, DOCUMENT_FIELDS, label, allowed=allowed)
        row_id = _nonempty_string(row["document_requirement_id"], f"{label}.document_requirement_id")
        if row_id in ids:
            raise StructuralSourceError(f"duplicate document_requirement_id: {row_id}")
        ids.add(row_id)
        for field in (
            "public_name", "supplied_by_actor_type", "received_by_actor_type",
            "trigger", "phase_id", "required_status", "authority_claim_id",
        ):
            _nonempty_string(row[field], f"{label}.{field}")
        if row["authority_claim_id"] not in authority_ids:
            raise StructuralSourceError(f"{label} has unresolved authority_claim_id")
        _validate_routes(row, label)
        _validate_preinstall_route_absence(row, label, row_id)
        _nonnegative_int(row["copy_count"], f"{label}.copy_count")
        if row["required_status"] not in ("required", "conditional", "optional", "not_applicable"):
            raise StructuralSourceError(f"{label} has unknown required_status")
        variants = row["accepted_variants"]
        if not isinstance(variants, list) or not variants or any(not isinstance(x, str) or not x for x in variants):
            raise StructuralSourceError(f"{label}.accepted_variants must be nonempty strings")
        if row["required_status"] == "conditional":
            _nonempty_string(row.get("condition"), f"{label}.condition")
        elif "condition" in row:
            raise StructuralSourceError(f"{label}.condition is only valid for conditional rows")
    return ids


def _validate_checklist(rows: list[dict], authority_ids: set[str]) -> set[str]:
    ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"checklist_items[{index}]"
        _require_fields(row, CHECKLIST_FIELDS, label)
        row_id = _nonempty_string(row["checklist_item_id"], f"{label}.checklist_item_id")
        if row_id in ids:
            raise StructuralSourceError(f"duplicate checklist_item_id: {row_id}")
        ids.add(row_id)
        for field in CHECKLIST_FIELDS - {"route_applicability"}:
            _nonempty_string(row[field], f"{label}.{field}")
        if row["authority_claim_id"] not in authority_ids:
            raise StructuralSourceError(f"{label} has unresolved authority_claim_id")
        _validate_routes(row, label)
    return ids


def _validate_fees(
    rows: list[dict],
    authority_ids: set[str],
    actors: Mapping[str, str],
    fee_lock: Mapping[str, Any],
) -> set[str]:
    ids: set[str] = set()
    keys: set[str] = set()
    for index, row in enumerate(rows):
        label = f"fee_schedule[{index}]"
        _require_fields(row, FEE_FIELDS, label)
        charge_id = _nonempty_string(row["charge_id"], f"{label}.charge_id")
        if charge_id in ids:
            raise StructuralSourceError(f"duplicate charge_id: {charge_id}")
        ids.add(charge_id)
        for field in (
            "canonical_charge_key", "public_name", "currency", "payer_actor_type",
            "collector_actor_id", "authority_claim_id", "trigger", "phase_id",
            "frequency", "refundable_status", "effective_start", "effective_end",
            "applicability_date_basis", "applicability_date_event",
        ):
            _nonempty_string(row[field], f"{label}.{field}")
        _nonnegative_int(row["amount"], f"{label}.amount")
        if row["currency"] != "USD":
            raise StructuralSourceError(f"{label}.currency must be canonical USD")
        waiver = row["waiver_or_exemption_rule"]
        if waiver is not None:
            _nonempty_string(waiver, f"{label}.waiver_or_exemption_rule")
        if row["payer_actor_type"] != "applicant_customer":
            raise StructuralSourceError(f"{label} must declare the customer fee payer")
        if row["collector_actor_id"] not in (actors["ahj_actor"], actors["utility_actor"]):
            raise StructuralSourceError(f"{label} has unknown collector_actor_id")
        if row["authority_claim_id"] not in authority_ids:
            raise StructuralSourceError(f"{label} has unresolved authority_claim_id")
        _validate_routes(row, label)
        _validate_preinstall_route_absence(row, label, charge_id)
        if row["frequency"] not in (
            "once_per_case", "once_per_submission", "once_per_repeat", "conditional_once",
        ):
            raise StructuralSourceError(f"{label} has invalid frequency")
        if row["refundable_status"] not in (
            "refundable", "nonrefundable", "conditional", "not_applicable",
        ):
            raise StructuralSourceError(f"{label} has invalid refundable_status")
        start = _strict_date(row["effective_start"], f"{label}.effective_start")
        end = _strict_date(row["effective_end"], f"{label}.effective_end")
        if end < start:
            raise StructuralSourceError(f"{label} effective dates are reversed")
        if (
            row["effective_start"] != fee_lock["eligible_initial_date_start"]
            or row["effective_end"] != fee_lock["eligible_initial_date_end"]
        ):
            raise StructuralSourceError(f"{label} effective period differs from the schedule lock")
        if row["applicability_date_basis"] != "case_schedule_version_locked_at_event":
            raise StructuralSourceError(f"{label} lacks the case schedule lock")
        if row["applicability_date_event"] != "first_permit_submission":
            raise StructuralSourceError(f"{label} has the wrong applicability event")
        if row["locked_through_case_completion"] is not True:
            raise StructuralSourceError(f"{label} must remain locked through case completion")
        expected_key = canonical_charge_key(row)
        if row["canonical_charge_key"] != expected_key:
            raise StructuralSourceError(f"{label} has a noncanonical charge key")
        if expected_key in keys:
            raise StructuralSourceError(f"canonical charge-key collision: {expected_key}")
        keys.add(expected_key)
    return ids


def _validate_worked_totals(rows: list[dict], fee_rows: list[dict]) -> None:
    amounts = {row["charge_id"]: row["amount"] for row in fee_rows}
    fee_by_id = {row["charge_id"]: row for row in fee_rows}
    example_ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"worked_fee_examples[{index}]"
        _require_fields(row, WORKED_TOTAL_FIELDS, label)
        example_id = _nonempty_string(row.get("example_id"), f"{label}.example_id")
        if example_id in example_ids:
            raise StructuralSourceError(f"duplicate worked example: {example_id}")
        example_ids.add(example_id)
        if row.get("route") not in ROUTES:
            raise StructuralSourceError(f"{label} has unknown route")
        multiplicities = row.get("multiplicities")
        if not isinstance(multiplicities, Mapping) or set(multiplicities) != set(amounts):
            raise StructuralSourceError(f"{label} must bind exactly all charge IDs")
        total = 0
        for charge_id, count in multiplicities.items():
            count = _nonnegative_int(count, f"{label}.{charge_id}")
            fee = fee_by_id[charge_id]
            route_applies = row["route"] in fee["route_applicability"]
            if not route_applies and count != 0:
                raise StructuralSourceError(f"{label}.{charge_id} must be zero off its route")
            if route_applies and fee["frequency"] in ("once_per_case", "conditional_once") and count != 1:
                raise StructuralSourceError(
                    f"{label}.{charge_id} must have multiplicity one for {fee['frequency']}"
                )
            if route_applies and fee["frequency"] == "once_per_submission" and count < 1:
                raise StructuralSourceError(
                    f"{label}.{charge_id} must include at least one applicable submission"
                )
            total += amounts[charge_id] * count
        _nonnegative_int(row.get("total"), f"{label}.total")
        if row["total"] != total:
            raise StructuralSourceError(f"{label} total mismatch: {row['total']} != {total}")
    if {row["route"] for row in rows} != set(ROUTES):
        raise StructuralSourceError("worked fee examples must cover each route exactly once")


def _validate_phase_rules(
    rows: list[dict], jid: str, design: Mapping[str, Any],
) -> set[str]:
    dependencies = design["phase_event_dependencies"]
    if len(rows) != len(dependencies):
        raise StructuralSourceError("phase_event_dependencies count mismatch")
    ids: set[str] = set()
    for index, (row, dependency) in enumerate(zip(rows, dependencies, strict=True)):
        label = f"phase_event_dependencies[{index}]"
        _require_fields(row, PHASE_RULE_FIELDS, label)
        expected_id = f"{jid}.PHASE_RULE.{dependency['route']}.{dependency['event']}"
        if row["phase_rule_id"] != expected_id:
            raise StructuralSourceError(f"{label}.phase_rule_id is noncanonical")
        if expected_id in ids:
            raise StructuralSourceError(f"duplicate phase_rule_id: {expected_id}")
        ids.add(expected_id)
        _nonnegative_int(row["source_rule_index"], f"{label}.source_rule_index")
        expected = {
            "phase_rule_id": expected_id,
            "jurisdiction_id": jid,
            "route": dependency["route"],
            "event": dependency["event"],
            "mode": dependency["mode"],
            "requires": dependency["requires"],
            "source_design_schema": design["schema_version"],
            "source_rule_index": index,
        }
        if row != expected:
            raise StructuralSourceError(f"{label} differs from its exact source design rule")
    return ids


def validate_resolved_source(source: Mapping[str, Any], design: Mapping[str, Any]) -> None:
    """Validate one fully resolved provisional jurisdiction source."""
    if not isinstance(source, Mapping):
        raise StructuralSourceError("resolved source must be a mapping")
    _validate_design(design)
    _require_fields(source, SOURCE_FIELDS, "resolved source")
    if source.get("schema_version") != RESOLVED_SCHEMA_VERSION or source.get("world_id") != WORLD_ID:
        raise StructuralSourceError("resolved source identity mismatch")
    jid = source.get("jurisdiction_id")
    if jid not in JURISDICTIONS:
        raise StructuralSourceError("unknown jurisdiction_id")
    if source.get("utility_id") != EXPECTED_UTILITIES[jid]:
        raise StructuralSourceError("utility_id mismatch")
    if _contains_token(source):
        raise StructuralSourceError("resolved source contains an unresolved token")

    expected_counts = design.get("expected_materialized_counts_per_jurisdiction")
    if not isinstance(expected_counts, Mapping):
        raise StructuralSourceError("design lacks expected materialized counts")
    for field in (
        "authorities", "phase_event_dependencies", "applicant_encounters", "required_documents",
        "checklist_items", "fee_schedule", "worked_fee_examples",
    ):
        rows = source.get(field)
        if not isinstance(rows, list):
            raise StructuralSourceError(f"{field} must be a list")
        count = _nonnegative_int(expected_counts.get(field), f"expected count {field}")
        if len(rows) != count:
            raise StructuralSourceError(f"{field} count mismatch: {len(rows)} != {count}")

    actor_assumption = design.get("actor_assumption")
    if not isinstance(actor_assumption, Mapping):
        raise StructuralSourceError("design lacks actor_assumption")
    actors = source.get("actors")
    if not isinstance(actors, Mapping):
        raise StructuralSourceError("actors must be a mapping")
    _require_fields(actors, ACTOR_FIELDS, "actors")
    for field in ACTOR_FIELDS:
        _nonempty_string(actors.get(field), f"actors.{field}")
    for field in actor_assumption:
        if actors.get(field) != actor_assumption[field]:
            raise StructuralSourceError(f"actors.{field} differs from the additive design")
    money_context = source.get("money_context")
    if not isinstance(money_context, Mapping):
        raise StructuralSourceError("money_context must be a mapping")
    _require_fields(money_context, MONEY_CONTEXT_FIELDS, "money_context")
    if dict(money_context) != dict(design["money_unit_normalization"]):
        raise StructuralSourceError("money_context differs from the additive design")

    authorities = _validate_authorities(source["authorities"], jid)
    known_events = set(design.get("known_events", []))
    if not known_events:
        raise StructuralSourceError("design has no known_events")
    identifier_sets = [
        authorities,
        _validate_phase_rules(source["phase_event_dependencies"], jid, design),
        _validate_encounters(source["applicant_encounters"], authorities, known_events),
        _validate_documents(source["required_documents"], authorities),
        _validate_checklist(source["checklist_items"], authorities),
        _validate_fees(source["fee_schedule"], authorities, actors, design["fee_schedule_lock"]),
    ]
    all_ids: set[str] = set()
    for ids in identifier_sets:
        collision = all_ids & ids
        if collision:
            raise StructuralSourceError(f"cross-collection ID collision: {sorted(collision)}")
        all_ids.update(ids)
    _validate_worked_totals(source["worked_fee_examples"], source["fee_schedule"])


def _combine_jurisdictions(part1: Mapping[str, Any], part2: Mapping[str, Any]) -> dict[str, dict]:
    combined: dict[str, dict] = {}
    for packet in (part1, part2):
        if packet.get("world_id") != WORLD_ID or not isinstance(packet.get("jurisdictions"), list):
            raise StructuralSourceError("jurisdiction source packet identity mismatch")
        for row in packet["jurisdictions"]:
            if not isinstance(row, Mapping):
                raise StructuralSourceError("jurisdiction source row must be a mapping")
            jid = row.get("jurisdiction_id")
            if jid in combined:
                raise StructuralSourceError(f"duplicate jurisdiction source: {jid}")
            combined[jid] = copy.deepcopy(dict(row))
    if set(combined) != set(JURISDICTIONS):
        raise StructuralSourceError("jurisdiction sources must cover exactly all 12 R01 IDs")
    return combined


def materialize_structural_sources(
    shared: Mapping[str, Any],
    part1: Mapping[str, Any],
    part2: Mapping[str, Any],
    design: Mapping[str, Any],
) -> dict[str, dict]:
    """Resolve and validate all twelve provisional jurisdiction source objects."""
    for label, packet in (("shared", shared), ("design", design)):
        if not isinstance(packet, Mapping) or packet.get("world_id") != WORLD_ID:
            raise StructuralSourceError(f"{label} packet identity mismatch")
    _validate_design(design)
    jurisdictions = _combine_jurisdictions(part1, part2)
    fee_templates = part2.get("fee_row_templates")
    if not isinstance(fee_templates, list) or not fee_templates:
        raise StructuralSourceError("part2 must declare fee_row_templates")
    event_templates = design.get("encounter_event_prerequisites")
    if not isinstance(event_templates, Mapping):
        raise StructuralSourceError("design lacks encounter_event_prerequisites")
    encounter_templates = shared.get("applicant_encounters")
    if not isinstance(encounter_templates, list):
        raise StructuralSourceError("shared packet lacks applicant_encounters")
    if set(event_templates) != {row.get("encounter_id") for row in encounter_templates}:
        raise StructuralSourceError("typed event-prerequisite map must exactly cover encounter templates")
    fee_lock = design.get("fee_schedule_lock")
    if not isinstance(fee_lock, Mapping):
        raise StructuralSourceError("design lacks fee_schedule_lock")

    resolved: dict[str, dict] = {}
    for jid in JURISDICTIONS:
        config = jurisdictions[jid]
        if config.get("profile") != EXPECTED_PROFILES[jid]:
            raise StructuralSourceError(f"{jid}: profile mismatch")
        if config.get("utility_id") != EXPECTED_UTILITIES[jid]:
            raise StructuralSourceError(f"{jid}: utility mismatch")
        bindings = config.get("bindings")
        if not isinstance(bindings, Mapping) or bindings.get("jid") != jid:
            raise StructuralSourceError(f"{jid}: missing or inconsistent bindings")
        full_bindings = dict(bindings)
        if "fee_amounts" in config:
            amounts = config["fee_amounts"]
            if not isinstance(amounts, Mapping):
                raise StructuralSourceError(f"{jid}: fee_amounts must be a mapping")
            for key, value in amounts.items():
                _nonnegative_int(value, f"{jid}.fee_amounts.{key}")
            full_bindings["fee_amounts"] = dict(amounts)

        encounters = _resolve_tokens(encounter_templates, full_bindings)
        event_map = {
            _resolve_tokens(template_id, full_bindings): copy.deepcopy(spec)
            for template_id, spec in event_templates.items()
        }
        for encounter in encounters:
            spec = event_map.get(encounter["encounter_id"])
            if spec is None:
                raise StructuralSourceError(f"{jid}: encounter lacks typed event prerequisites")
            encounter["event_prerequisite_mode"] = spec.get("mode")
            encounter["event_prerequisites"] = copy.deepcopy(spec.get("events"))

        if "fee_schedule" in config:
            fees = copy.deepcopy(config["fee_schedule"])
        else:
            fees = []
            for template in fee_templates:
                row = _resolve_tokens(template, full_bindings)
                row.pop("fee_key", None)
                fees.append(row)
        for fee in fees:
            money = design["money_unit_normalization"]
            if fee.get("currency") != money["source_currency_label"]:
                raise StructuralSourceError(
                    f"{jid}: source fee currency is not the reviewed fictional label"
                )
            fee["currency"] = money["materialized_currency_code"]
            supplied = fee.get("canonical_charge_key")
            computed = canonical_charge_key(fee)
            if supplied is not None and supplied != computed:
                raise StructuralSourceError(f"{jid}: supplied canonical charge key mismatch")
            fee["canonical_charge_key"] = computed
            fee["applicability_date_basis"] = fee_lock.get("applicability_date_basis")
            fee["applicability_date_event"] = fee_lock.get("applicability_date_event")
            fee["locked_through_case_completion"] = fee_lock.get("locked_through_case_completion")

        worked = copy.deepcopy(config.get("worked_totals"))
        if not isinstance(worked, list):
            raise StructuralSourceError(f"{jid}: worked_totals must be a list")
        fee_key_to_id = {
            template["fee_key"]: _resolve_tokens(template["charge_id"], full_bindings)
            for template in fee_templates
        }
        for example in worked:
            multiplicities = example.get("multiplicities")
            if not isinstance(multiplicities, Mapping):
                raise StructuralSourceError(f"{jid}: worked total lacks multiplicities")
            if set(multiplicities) == set(fee_key_to_id):
                example["multiplicities"] = {
                    fee_key_to_id[key]: value for key, value in multiplicities.items()
                }
            example.pop("arithmetic", None)

        actors = copy.deepcopy(design.get("actor_assumption"))
        if not isinstance(actors, dict):
            raise StructuralSourceError("design actor_assumption must be a mapping")
        actors["ahj_actor"] = full_bindings.get("ahj_actor")
        actors["utility_actor"] = full_bindings.get("utility_actor")
        phase_rules = []
        for index, dependency in enumerate(design["phase_event_dependencies"]):
            phase_rules.append({
                "phase_rule_id": f"{jid}.PHASE_RULE.{dependency['route']}.{dependency['event']}",
                "jurisdiction_id": jid,
                "route": dependency["route"],
                "event": dependency["event"],
                "mode": dependency["mode"],
                "requires": copy.deepcopy(dependency["requires"]),
                "source_design_schema": design["schema_version"],
                "source_rule_index": index,
            })
        source = {
            "schema_version": RESOLVED_SCHEMA_VERSION,
            "world_id": WORLD_ID,
            "jurisdiction_id": jid,
            "utility_id": config["utility_id"],
            "actors": actors,
            "money_context": copy.deepcopy(design["money_unit_normalization"]),
            "authorities": copy.deepcopy(config.get("authorities")),
            "phase_event_dependencies": phase_rules,
            "applicant_encounters": encounters,
            "required_documents": _resolve_tokens(shared.get("required_documents"), full_bindings),
            "checklist_items": _resolve_tokens(shared.get("checklist_items"), full_bindings),
            "fee_schedule": fees,
            "worked_fee_examples": worked,
        }
        validate_resolved_source(source, design)
        resolved[jid] = source
    return resolved


def public_structural_projection(source: Mapping[str, Any], design: Mapping[str, Any]) -> dict:
    """Return only explicitly whitelisted public structural identities/collections."""
    validate_resolved_source(source, design)
    whitelist = design.get("public_collection_whitelist")
    if not isinstance(whitelist, list) or any(not isinstance(item, str) for item in whitelist):
        raise StructuralSourceError("design public_collection_whitelist is invalid")
    required = {
        "schema_version", "world_id", "jurisdiction_id", "utility_id", "actors", "money_context",
        "authorities", "phase_event_dependencies", "applicant_encounters", "required_documents",
        "checklist_items", "fee_schedule",
    }
    if set(whitelist) != required:
        raise StructuralSourceError("public whitelist differs from the reviewed structural-only set")
    public = {key: copy.deepcopy(source[key]) for key in whitelist}
    public["schema_version"] = PUBLIC_SCHEMA_VERSION
    forbidden = design.get("public_forbidden_design_fields")
    if not isinstance(forbidden, list) or set(public) & set(forbidden):
        raise StructuralSourceError("public projection contains forbidden design metadata")
    validate_declared_public_leak_policy(public)
    return public


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def provisional_source_hashes(sources: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    if set(sources) != set(JURISDICTIONS):
        raise StructuralSourceError("hash input must contain exactly all 12 jurisdictions")
    return {jid: hashlib.sha256(canonical_json_bytes(sources[jid])).hexdigest() for jid in sorted(sources)}


def write_provisional_sources(sources: Mapping[str, Mapping[str, Any]], output: pathlib.Path) -> dict[str, str]:
    """Write canonical provisional per-jurisdiction JSON into a new directory."""
    if output.exists():
        raise StructuralSourceError(f"output destination already exists: {output}")
    hashes = provisional_source_hashes(sources)
    output.mkdir(parents=True, exist_ok=False)
    for jid in sorted(sources):
        (output / f"{jid}.json").write_bytes(canonical_json_bytes(sources[jid]))
    return hashes


def _load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared", type=pathlib.Path, required=True)
    parser.add_argument("--part1", type=pathlib.Path, required=True)
    parser.add_argument("--part2", type=pathlib.Path, required=True)
    parser.add_argument("--design", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    design = _load(args.design)
    sources = materialize_structural_sources(
        _load(args.shared), _load(args.part1), _load(args.part2), design,
    )
    hashes = write_provisional_sources(sources, args.out)
    print(json.dumps({"status": "provisional", "count": len(sources), "hashes": hashes}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "JURISDICTIONS", "PUBLIC_SCHEMA_VERSION", "RESOLVED_SCHEMA_VERSION", "ROUTES",
    "StructuralSourceError", "WORLD_ID", "canonical_charge_key",
    "canonical_json_bytes", "materialize_structural_sources",
    "provisional_source_hashes", "public_structural_projection",
    "validate_resolved_source", "write_provisional_sources",
]
