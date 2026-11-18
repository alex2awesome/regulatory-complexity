"""S07 fresh-replica public observation contract helpers.

This module implements the effective contract frozen in the S07 design packet
and its two reviewed errata.  It is deliberately *not* a world builder: no
structural rules or fees have been populated, and nothing here generates cases,
render specifications, prose, or private truth.

The public leakage guard enforces the contract's declared forbidden keys and
known string tokens.  It cannot prove the absence of arbitrary covert
information encoded in otherwise permitted values.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any


WORLD_ID = "S07_PILOT_20260920_R01"
OBSERVATION_SCHEMA_VERSION = "s07-public-observation/1"
RELEASE_ID = "S07_R01_SOLARTRACE_STYLE_V1"
CALENDAR_ID = "S07_R01_MON_FRI_NO_HOLIDAYS_V1"
AS_OF = "2026-09-01"
PRIVATE_PROVENANCE_PATH = "provenance/observation_membership.jsonl.gz"

# These hashes document the source of the in-module declarative constants.  The
# module never opens a runs/ path at import time or validation time.
EFFECTIVE_CONTRACT_HASHES = {
    "base_manifest": "2f0c6ffc529c8ee021f78554c7b2df51f8eeb06fc048ce5025c177382bd78a50",
    "reviewed_erratum01_manifest": "2316f6eaa54ce2eb5f286139b48aa0f1364c113d6c105fb73bfb71d0de527218",
    "reviewed_erratum02_manifest": "718a588f59f31e36ec7f7ae4c1c4a860c2334b86bbd86350c108eff7cd59c49c",
}

JURISDICTIONS = frozenset(f"R01J{i:02d}" for i in range(1, 13))
UTILITY_JURISDICTIONS = {
    "U01": frozenset(("R01J06", "R01J08")),
    "U02": frozenset(("R01J10", "R01J03")),
    "U03": frozenset(("R01J05", "R01J04")),
    "U04": frozenset(("R01J07", "R01J12")),
    "U05": frozenset(("R01J09", "R01J01")),
    "U06": frozenset(("R01J02", "R01J11")),
}

PHASE_CONTRACTS = {
    "ahj_permit": ("ahj", "first_permit_submission", "final_permit_approval"),
    "preinstall_ix": (
        "utility", "preinstall_interconnection_submission",
        "preinstall_interconnection_approval",
    ),
    "ahj_inspection": ("ahj", "inspection_request", "final_passed_inspection"),
    "final_ix_to_pto": (
        "utility", "final_interconnection_request",
        "permission_to_operate_granted",
    ),
}

POPULATION_COMPONENTS = (
    "owner_type", "owner_id", "period_start", "period_end", "technology",
    "size_band", "route", "phase_id", "completion_conditioning",
)
OWNER_CELL_COMPONENTS = POPULATION_COMPONENTS + ("statistic",)

REQUIRED_FIELDS = frozenset((
    "schema_version", "release_id", "observation_id", "owner_cell_id",
    "jurisdiction_id", "owner_type", "owner_id", "phase_id", "start_event",
    "end_event", "duration_basis", "unit", "calendar_id", "period_start",
    "period_end", "as_of", "technology", "size_band", "route", "population",
    "statistic", "value_status", "value", "sample_size_status", "sample_size",
    "rounding", "completion_conditioning", "zero_semantics",
    "joined_install_count", "public_cohort_cell_id",
))
OPTIONAL_FIELDS = frozenset((
    "numerator", "denominator", "source_document_id", "qualifiers",
))
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

FORBIDDEN_PUBLIC_KEYS = frozenset((
    "evaluation_split", "partition_role", "role_to_utility_mapping", "case_ids",
    "case_member_hash", "latent_eventual_outcome", "true_unrounded_value",
    "reporting_mechanism", "transformation", "intended_fidelity",
    "same_cohort_group", "information_ceiling",
))
FORBIDDEN_EXACT_STRING_VALUES = frozenset((
    "calibration", "development", "reserved",
))
FORBIDDEN_STRING_SUBSTRINGS = ("s07_cal_", "s07_dev_", "s07_res_")

_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class S07ContractError(ValueError):
    """Raised when an S07 public contract is violated."""


class S07GenerationBlocked(S07ContractError):
    """Raised when the separately frozen structural source gate is not met."""


def parse_iso_date(value: Any, *, field: str = "date") -> date:
    """Parse a strict YYYY-MM-DD real calendar date, rejecting booleans/objects."""
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise S07ContractError(f"{field} must be strict YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise S07ContractError(f"{field} is not a valid calendar date: {value}") from exc


def is_business_day(value: str) -> bool:
    """Return whether ``value`` is Monday--Friday in the fictional calendar."""
    return parse_iso_date(value).weekday() < 5


def add_business_days(start: str, days: int) -> str:
    """Add nonnegative fictional business days to a business-day start.

    The calendar intentionally has no holidays.  A zero-day completed phase
    returns the same date; Friday plus one business day is Monday.  This API
    requires an already-valid business-day event and never silently shifts a
    weekend filing clock.
    """
    current = parse_iso_date(start, field="start")
    if current.weekday() >= 5:
        raise S07ContractError("start must be a business day")
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise S07ContractError("days must be a nonnegative integer, not boolean")
    remaining = days
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current.isoformat()


def business_days_between(start: str, end: str) -> int:
    """Count business days in ``(start, end]`` under the fictional calendar."""
    first = parse_iso_date(start, field="start")
    last = parse_iso_date(end, field="end")
    if first.weekday() >= 5 or last.weekday() >= 5:
        raise S07ContractError("start and end must be business days")
    if last < first:
        raise S07ContractError("end must be on or after start")
    count = 0
    current = first
    while current < last:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


def _encoded_components(prefix: str, row: Mapping[str, Any], fields: Sequence[str]) -> str:
    parts = [prefix]
    for field in fields:
        if field not in row:
            raise S07ContractError(f"missing canonical-key component: {field}")
        value = str(row[field])
        parts.append(f"{field}:{len(value.encode('utf-8'))}:{value}")
    return "|".join(parts)


def canonical_public_cohort_cell_id(row: Mapping[str, Any]) -> str:
    """Return the unambiguous key for a phase cohort, excluding statistic."""
    return _encoded_components("s07-cohort-v1", row, POPULATION_COMPONENTS)


def canonical_owner_cell_id(row: Mapping[str, Any]) -> str:
    """Return the unambiguous owner/statistic cell key."""
    return _encoded_components("s07-owner-cell-v1", row, OWNER_CELL_COMPONENTS)


def canonical_population(row: Mapping[str, Any]) -> str:
    """Return the required explicit public population description."""
    missing = [field for field in POPULATION_COMPONENTS if field not in row]
    if missing:
        raise S07ContractError(f"missing population components: {missing}")
    return ";".join(f"{field}={row[field]}" for field in POPULATION_COMPONENTS)


def validate_declared_public_leak_policy(value: Any, *, path: str = "$") -> None:
    """Reject declared private keys and known split-bearing string tokens.

    This is a recursive known-policy guard, not proof against arbitrary covert
    information in allowed values.
    """
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise S07ContractError(f"{path}: public mapping key must be a string")
            folded_key = key.casefold()
            if (
                folded_key in FORBIDDEN_PUBLIC_KEYS or
                folded_key in FORBIDDEN_EXACT_STRING_VALUES or
                any(token in folded_key for token in FORBIDDEN_STRING_SUBSTRINGS)
            ):
                raise S07ContractError(f"{path}.{key}: forbidden public key")
            validate_declared_public_leak_policy(child, path=f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            validate_declared_public_leak_policy(child, path=f"{path}[{index}]")
        return
    if isinstance(value, str):
        folded = value.casefold()
        if folded in FORBIDDEN_EXACT_STRING_VALUES:
            raise S07ContractError(f"{path}: forbidden split-label value")
        if any(token in folded for token in FORBIDDEN_STRING_SUBSTRINGS):
            raise S07ContractError(f"{path}: forbidden split-bearing identifier")


def _require_nonempty_string(row: Mapping[str, Any], field: str) -> None:
    if not isinstance(row[field], str) or not row[field]:
        raise S07ContractError(f"{field} must be a nonempty string")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_float_representable(value: Any) -> bool:
    if not _is_number(value):
        return False
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        return False
    return math.isfinite(converted)


def _require_optional_nonnegative_int(row: Mapping[str, Any], field: str) -> None:
    value = row.get(field)
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 0
    ):
        raise S07ContractError(f"{field} must be null or a nonnegative integer")


def _validate_owner_and_phase(row: Mapping[str, Any]) -> None:
    phase = row["phase_id"]
    if phase not in PHASE_CONTRACTS:
        raise S07ContractError(f"unsupported phase_id: {phase}")
    expected_owner, expected_start, expected_end = PHASE_CONTRACTS[phase]
    if row["owner_type"] != expected_owner:
        raise S07ContractError(f"{phase} requires owner_type={expected_owner}")
    if row["start_event"] != expected_start or row["end_event"] != expected_end:
        raise S07ContractError(f"{phase} has mismatched start/end event")

    jid = row["jurisdiction_id"]
    owner_id = row["owner_id"]
    if jid not in JURISDICTIONS:
        raise S07ContractError(f"unknown jurisdiction_id: {jid}")
    if expected_owner == "ahj":
        if owner_id != jid:
            raise S07ContractError("AHJ owner_id must equal jurisdiction_id")
    elif owner_id not in UTILITY_JURISDICTIONS or jid not in UTILITY_JURISDICTIONS[owner_id]:
        raise S07ContractError("utility owner_id is inconsistent with jurisdiction_id")


def _validate_dates(row: Mapping[str, Any]) -> None:
    start = parse_iso_date(row["period_start"], field="period_start")
    end = parse_iso_date(row["period_end"], field="period_end")
    cutoff = parse_iso_date(row["as_of"], field="as_of")
    if row["as_of"] != AS_OF:
        raise S07ContractError(f"as_of must equal {AS_OF}")
    if end < start:
        raise S07ContractError("period_end must be on or after period_start")
    if end >= cutoff:
        raise S07ContractError("period_end must be strictly before as_of")


def _validate_status(row: Mapping[str, Any]) -> None:
    status = row["value_status"]
    sample_status = row["sample_size_status"]
    sample_size = row["sample_size"]
    value = row["value"]
    zero = row["zero_semantics"]
    conditioning = row["completion_conditioning"]

    if isinstance(sample_size, bool):
        raise S07ContractError("sample_size cannot be boolean")
    if sample_size is not None and (not isinstance(sample_size, int) or sample_size < 0):
        raise S07ContractError("sample_size must be null or a nonnegative integer")
    if sample_status in ("unknown", "not_applicable") and sample_size is not None:
        raise S07ContractError(f"{sample_status} sample_size must be null")

    if status == "reported":
        if not _is_finite_float_representable(value) or value < 0:
            raise S07ContractError(
                "reported value must be a finite-float-representable nonnegative number"
            )
        if sample_status not in ("known", "unknown"):
            raise S07ContractError("reported sample size must be known or unknown")
        if sample_status == "known" and (sample_size is None or sample_size < 1):
            raise S07ContractError("reported known sample_size must be >=1")
        if conditioning != "phase_completed_by_cutoff":
            raise S07ContractError("reported value requires phase_completed_by_cutoff")
        expected_zero = "same_day_completed" if value == 0 else "not_zero"
        if zero != expected_zero:
            raise S07ContractError(f"reported value requires zero_semantics={expected_zero}")
    elif status == "suppressed":
        if value is not None or zero != "suppressed_or_missing":
            raise S07ContractError("suppressed value must be null with suppressed_or_missing")
        if sample_status not in ("known", "unknown"):
            raise S07ContractError("suppressed sample size must be known or unknown")
        if sample_status == "known" and (sample_size is None or sample_size < 1):
            raise S07ContractError("suppressed known sample_size must be >=1")
        if conditioning != "phase_completed_by_cutoff":
            raise S07ContractError("suppressed value requires phase_completed_by_cutoff")
    elif status == "not_required":
        if value is not None or sample_status != "not_applicable" or sample_size is not None:
            raise S07ContractError("not_required requires null value and not_applicable null n")
        if conditioning != "not_applicable" or zero != "not_required":
            raise S07ContractError("not_required has inconsistent conditioning/zero semantics")
        if row["phase_id"] != "preinstall_ix" or row["route"] != "no_preinstall_approval":
            raise S07ContractError("not_required is limited to no-preinstall preinstall_ix")
    elif status == "no_observed_cases":
        if value is not None or sample_status != "known" or sample_size != 0:
            raise S07ContractError("no_observed_cases requires null value and known n=0")
        if conditioning != "phase_completed_by_cutoff" or zero != "no_observed_cases":
            raise S07ContractError("no_observed_cases has inconsistent conditioning/zero semantics")
    elif status == "missing_report":
        if value is not None or sample_status != "unknown" or sample_size is not None:
            raise S07ContractError("missing_report requires null value and unknown null n")
        if conditioning != "phase_completed_by_cutoff" or zero != "suppressed_or_missing":
            raise S07ContractError("missing_report has inconsistent conditioning/zero semantics")
    else:
        raise S07ContractError(f"unsupported value_status: {status}")

    if row["phase_id"] == "preinstall_ix" and row["route"] == "no_preinstall_approval":
        if status != "not_required":
            raise S07ContractError("no-preinstall route must encode preinstall_ix as not_required")


def _validate_rounding(row: Mapping[str, Any]) -> None:
    rounding = row["rounding"]
    status = row["value_status"]
    value = row["value"]
    if status != "reported":
        if rounding != "not_applicable":
            raise S07ContractError("nonreported values require rounding=not_applicable")
        return
    if rounding == "not_applicable":
        raise S07ContractError("reported values require an applicable rounding declaration")
    if rounding in ("exact_integer_business_day", "nearest_business_day"):
        on_grid = isinstance(value, int) or value.is_integer()
        if not on_grid:
            raise S07ContractError(f"{rounding} requires an integer-grid value")
    elif rounding == "nearest_half_business_day":
        on_grid = (
            isinstance(value, int) or value.is_integer() or
            value - math.floor(value) == 0.5
        )
        if not on_grid:
            raise S07ContractError("nearest_half_business_day requires a half-day-grid value")


def validate_public_observation(row: Mapping[str, Any]) -> None:
    """Validate one effective S07 public observation row or raise."""
    if not isinstance(row, Mapping):
        raise S07ContractError("observation must be a mapping")
    row_fields = set(row)
    if any(not isinstance(field, str) for field in row_fields):
        raise S07ContractError("observation field names must be strings")
    missing = REQUIRED_FIELDS - row_fields
    extras = row_fields - ALLOWED_FIELDS
    if missing:
        raise S07ContractError(f"missing required fields: {sorted(missing)}")
    if extras:
        raise S07ContractError(f"unknown fields: {sorted(extras)}")
    validate_declared_public_leak_policy(row)

    if row["schema_version"] != OBSERVATION_SCHEMA_VERSION:
        raise S07ContractError("unexpected schema_version")
    if row["release_id"] != RELEASE_ID:
        raise S07ContractError("unexpected release_id")
    for field in ("observation_id", "owner_cell_id", "owner_id", "population",
                  "public_cohort_cell_id"):
        _require_nonempty_string(row, field)

    _validate_owner_and_phase(row)
    if row["duration_basis"] != "elapsed_owner_phase_including_internal_queue_and_rework_within_boundaries":
        raise S07ContractError("unexpected duration_basis")
    if row["unit"] != "business_days" or row["calendar_id"] != CALENDAR_ID:
        raise S07ContractError("observation must use the frozen fictional business calendar")
    _validate_dates(row)

    if row["technology"] not in ("pv_only", "pv_plus_storage"):
        raise S07ContractError("unsupported technology")
    if row["size_band"] not in ("0_10_kw", "10_38_4_kw"):
        raise S07ContractError("unsupported size_band")
    if row["route"] not in (
        "parallel_standard", "serial_standard", "no_preinstall_approval", "all_routes",
    ):
        raise S07ContractError("unsupported route")
    if row["statistic"] not in ("median", "p90"):
        raise S07ContractError("statistic must be median or p90")
    if row["rounding"] not in (
        "exact_integer_business_day", "nearest_half_business_day",
        "nearest_business_day", "published_algorithm_unknown", "not_applicable",
    ):
        raise S07ContractError("unsupported rounding")

    _validate_status(row)
    _validate_rounding(row)
    _require_optional_nonnegative_int(row, "joined_install_count")
    _require_optional_nonnegative_int(row, "numerator")
    _require_optional_nonnegative_int(row, "denominator")
    source = row.get("source_document_id")
    if source is not None and not isinstance(source, str):
        raise S07ContractError("source_document_id must be a string or null")
    if "qualifiers" in row:
        qualifiers = row["qualifiers"]
        if not isinstance(qualifiers, list) or any(
            not isinstance(item, str) for item in qualifiers
        ):
            raise S07ContractError("qualifiers must be an array of strings when present")

    expected_population = canonical_population(row)
    if row["population"] != expected_population:
        raise S07ContractError("population must equal the canonical explicit population")
    if row["public_cohort_cell_id"] != canonical_public_cohort_cell_id(row):
        raise S07ContractError("public_cohort_cell_id is not canonical")
    if row["owner_cell_id"] != canonical_owner_cell_id(row):
        raise S07ContractError("owner_cell_id is not canonical")


_DUPLICATE_AGREEMENT_FIELDS = OWNER_CELL_COMPONENTS + (
    "start_event", "end_event", "duration_basis", "unit", "calendar_id", "as_of",
    "value_status", "value", "sample_size_status", "sample_size", "rounding",
    "zero_semantics", "public_cohort_cell_id", "population",
)


def validate_public_observations(rows: Sequence[Mapping[str, Any]]) -> None:
    """Validate rows, unique observation IDs, and repeated owner-cell agreement."""
    if isinstance(rows, (str, bytes, bytearray)) or not isinstance(rows, Sequence):
        raise S07ContractError("rows must be a sequence of mappings")
    observation_ids: set[str] = set()
    owner_cells: dict[str, tuple[Any, ...]] = {}
    for index, row in enumerate(rows):
        try:
            validate_public_observation(row)
        except S07ContractError as exc:
            raise S07ContractError(f"row {index}: {exc}") from exc
        observation_id = row["observation_id"]
        if observation_id in observation_ids:
            raise S07ContractError(f"duplicate observation_id: {observation_id}")
        observation_ids.add(observation_id)
        signature = tuple(row[field] for field in _DUPLICATE_AGREEMENT_FIELDS) + (
            tuple(row.get("qualifiers", ())),
        )
        prior = owner_cells.setdefault(row["owner_cell_id"], signature)
        if signature != prior:
            raise S07ContractError(
                f"conflicting restatement for owner_cell_id: {row['owner_cell_id']}"
            )


STRUCTURAL_COLLECTIONS = frozenset((
    "authorities", "applicant_encounters", "required_documents",
    "checklist_items", "fee_schedule",
))


def require_frozen_structural_source_contract(contract: Mapping[str, Any] | None) -> None:
    """Fail closed unless a separately reviewed populated source freeze is supplied.

    This validates only a caller-supplied freeze envelope.  It does not read the
    named content, recompute a hash, or attest human review.  A future builder
    must additionally resolve and verify the manifest and validate every
    structural source row against the reviewed field-level contract; this
    function is not authorization to generate a world.
    """
    if not isinstance(contract, Mapping):
        raise S07GenerationBlocked("a separately frozen populated structural source contract is required")
    if contract.get("schema_version") != "s07-populated-structural-source-freeze/1":
        raise S07GenerationBlocked("unexpected structural source freeze schema")
    if contract.get("world_id") != WORLD_ID:
        raise S07GenerationBlocked("structural source freeze has wrong world_id")
    if contract.get("status") != "frozen_populated_reviewed":
        raise S07GenerationBlocked("structural source contract is not frozen, populated and reviewed")
    manifest_hash = contract.get("manifest_sha256")
    if not isinstance(manifest_hash, str) or _SHA256_RE.fullmatch(manifest_hash) is None:
        raise S07GenerationBlocked("structural source freeze needs a lowercase SHA-256 manifest binding")
    jurisdictions = contract.get("jurisdictions")
    if not isinstance(jurisdictions, Mapping) or set(jurisdictions) != JURISDICTIONS:
        raise S07GenerationBlocked("structural source freeze must bind exactly all 12 jurisdictions")
    for jid, entry in jurisdictions.items():
        if not isinstance(entry, Mapping):
            raise S07GenerationBlocked(f"{jid}: structural source entry must be a mapping")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise S07GenerationBlocked(f"{jid}: missing lowercase SHA-256 source binding")
        counts = entry.get("collection_counts")
        if not isinstance(counts, Mapping) or set(counts) != STRUCTURAL_COLLECTIONS:
            raise S07GenerationBlocked(f"{jid}: all structural collection counts are required")
        for name, count in counts.items():
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise S07GenerationBlocked(f"{jid}: {name} must have at least one reviewed row")


__all__ = [
    "AS_OF", "CALENDAR_ID", "EFFECTIVE_CONTRACT_HASHES", "JURISDICTIONS",
    "OBSERVATION_SCHEMA_VERSION", "PHASE_CONTRACTS", "PRIVATE_PROVENANCE_PATH",
    "RELEASE_ID",
    "S07ContractError", "S07GenerationBlocked", "UTILITY_JURISDICTIONS", "WORLD_ID",
    "add_business_days", "business_days_between", "canonical_owner_cell_id",
    "canonical_population", "canonical_public_cohort_cell_id", "is_business_day",
    "parse_iso_date", "require_frozen_structural_source_contract",
    "validate_declared_public_leak_policy", "validate_public_observation",
    "validate_public_observations",
]
