"""Pure in-memory S07 owner/cohort summary construction.

The public observations, private canonical cohort memberships, and private
observation companions are returned as three separate collections.  This
module performs no filesystem I/O and never loads a run-local profile map.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .rng import quantile
from .s07_fresh_replica import (
    AS_OF,
    CALENDAR_ID,
    JURISDICTIONS,
    OBSERVATION_SCHEMA_VERSION,
    PHASE_CONTRACTS,
    RELEASE_ID,
    UTILITY_JURISDICTIONS,
    WORLD_ID,
    S07ContractError,
    business_days_between,
    canonical_owner_cell_id,
    canonical_population,
    canonical_public_cohort_cell_id,
    is_business_day,
    parse_iso_date,
    validate_declared_public_leak_policy,
    validate_public_observation,
    validate_public_observations,
)


PERIOD_START = "2024-09-01"
PERIOD_END = "2026-08-31"
ARRIVAL_START = "2024-09-02"
TECHNOLOGIES = ("pv_only", "pv_plus_storage")
SIZE_BANDS = ("0_10_kw", "10_38_4_kw")
ROUTES = ("parallel_standard", "serial_standard", "no_preinstall_approval")
STATISTICS = ("median", "p90")
PROFILES = frozenset(("A", "B", "C", "D"))
UTILITY_REPORTING_PROFILES = {
    "U01": "A", "U02": "C", "U03": "A",
    "U04": "C", "U05": "A", "U06": "C",
}

EXPECTED_PUBLIC_ROWS = 1152
EXPECTED_OWNER_CELLS = 864
EXPECTED_COHORT_CELLS = 432


class S07OwnerSummaryError(S07ContractError):
    """Raised when cases cannot produce the frozen owner-summary matrix."""


@dataclass(frozen=True)
class OwnerSummaryCollections:
    """Separate public and private collections; not a renderer payload."""

    public_observations: tuple[dict[str, Any], ...]
    private_cohort_memberships: tuple[dict[str, Any], ...]
    private_observation_companions: tuple[dict[str, Any], ...]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")


def membership_hash(
    public_cohort_cell_id: str,
    membership_kind: str,
    case_ids: Sequence[str],
) -> str:
    """Return the frozen, domain-separated private membership hash."""
    if not isinstance(public_cohort_cell_id, str) or not public_cohort_cell_id:
        raise S07OwnerSummaryError("public_cohort_cell_id must be a nonempty string")
    if membership_kind not in ("base", "selected"):
        raise S07OwnerSummaryError("membership_kind must be base or selected")
    if isinstance(case_ids, (str, bytes, bytearray)) or not isinstance(case_ids, Sequence):
        raise S07OwnerSummaryError("case_ids must be a sequence of unique strings")
    ids = list(case_ids)
    if any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise S07OwnerSummaryError("case_ids must contain nonempty strings")
    if len(ids) != len(set(ids)):
        raise S07OwnerSummaryError("case_ids must be unique before hashing")
    payload = {
        "schema_version": "s07-private-membership-hash/1",
        "world_id": WORLD_ID,
        "public_cohort_cell_id": public_cohort_cell_id,
        "membership_kind": membership_kind,
        "case_ids": sorted(ids),
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def canonical_observation_id(jurisdiction_id: str, owner_cell_id: str) -> str:
    """Return the frozen restatement-addressable public observation ID."""
    values = {
        "release_id": RELEASE_ID,
        "jurisdiction_id": jurisdiction_id,
        "owner_cell_id": owner_cell_id,
    }
    parts = ["s07-observation-v1"]
    for field in ("release_id", "jurisdiction_id", "owner_cell_id"):
        value = values[field]
        if not isinstance(value, str) or not value:
            raise S07OwnerSummaryError(f"{field} must be a nonempty string")
        parts.append(f"{field}:{len(value.encode('utf-8'))}:{value}")
    return "|".join(parts)


def _validate_profile_map(jurisdiction_profiles: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(jurisdiction_profiles, Mapping):
        raise S07OwnerSummaryError("jurisdiction_profiles must be a mapping")
    if set(jurisdiction_profiles) != set(JURISDICTIONS):
        raise S07OwnerSummaryError("jurisdiction_profiles must bind exactly all 12 jurisdictions")
    result = dict(jurisdiction_profiles)
    for jid, profile in result.items():
        if profile not in PROFILES:
            raise S07OwnerSummaryError(f"{jid}: unsupported reporting profile")
    return result


def _utility_for_jurisdiction(jurisdiction_id: str) -> str:
    matches = [
        utility_id
        for utility_id, jurisdictions in UTILITY_JURISDICTIONS.items()
        if jurisdiction_id in jurisdictions
    ]
    if len(matches) != 1:
        raise S07OwnerSummaryError(
            f"{jurisdiction_id}: expected exactly one frozen utility assignment"
        )
    return matches[0]


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise S07OwnerSummaryError(f"{label} must be a mapping")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise S07OwnerSummaryError(f"{label} must be a nonempty string")
    return value


def _find_event(case: Mapping[str, Any], event_name: str, date_value: str) -> None:
    events = case.get("events")
    if not isinstance(events, list):
        raise S07OwnerSummaryError(f"{case.get('case_id')}: events must be a list")
    matches = [
        event for event in events
        if isinstance(event, Mapping)
        and event.get("event") == event_name
        and event.get("date") == date_value
    ]
    if len(matches) != 1:
        raise S07OwnerSummaryError(
            f"{case.get('case_id')}: expected one {event_name} event at {date_value}"
        )


def _replay_completed_phase(
    case_id: str,
    phase_id: str,
    phase: Mapping[str, Any],
    *,
    expected_start_event: str,
    expected_end_event: str,
    case: Mapping[str, Any],
) -> int:
    if phase.get("status") != "completed":
        raise S07OwnerSummaryError(f"{case_id}/{phase_id}: phase is not completed")
    if phase.get("start_event") != expected_start_event or phase.get("end_event") != expected_end_event:
        raise S07OwnerSummaryError(f"{case_id}/{phase_id}: completed endpoints mismatch")
    start = _require_nonempty_string(phase.get("start_date"), f"{case_id}/{phase_id}.start_date")
    end = _require_nonempty_string(phase.get("end_date"), f"{case_id}/{phase_id}.end_date")
    duration = _require_mapping(phase.get("duration"), f"{case_id}/{phase_id}.duration")
    realized = duration.get("realized_business_days")
    if isinstance(realized, bool) or not isinstance(realized, int) or realized < 0:
        raise S07OwnerSummaryError(
            f"{case_id}/{phase_id}: realized duration must be a nonnegative integer"
        )
    replayed = business_days_between(start, end)
    if replayed != realized:
        raise S07OwnerSummaryError(
            f"{case_id}/{phase_id}: realized duration does not replay from dates"
        )
    _find_event(case, expected_start_event, start)
    _find_event(case, expected_end_event, end)
    return realized


def _validate_case(
    case: Mapping[str, Any],
    profiles: Mapping[str, str],
    seen_case_ids: set[str],
    seen_membership_candidate_ids: set[str],
    seen_membership_candidates: set[tuple[str, str]],
) -> dict[str, Any]:
    if not isinstance(case, Mapping):
        raise S07OwnerSummaryError("each case must be a mapping")
    if case.get("schema_version") != "s07-private-case-mechanics/1":
        raise S07OwnerSummaryError("case has an unexpected schema_version")
    case_id = _require_nonempty_string(case.get("case_id"), "case_id")
    if case_id in seen_case_ids:
        raise S07OwnerSummaryError(f"duplicate case_id: {case_id}")
    seen_case_ids.add(case_id)
    jid = case.get("jurisdiction_id")
    if jid not in JURISDICTIONS:
        raise S07OwnerSummaryError(f"{case_id}: unknown jurisdiction_id")
    expected_utility = _utility_for_jurisdiction(jid)
    if case.get("utility_id") != expected_utility:
        raise S07OwnerSummaryError(f"{case_id}: utility assignment mismatch")
    if case.get("profile_id") != profiles[jid]:
        raise S07OwnerSummaryError(f"{case_id}: profile differs from supplied profile map")
    technology = case.get("technology")
    size_band = case.get("size_band")
    route = case.get("route")
    if technology not in TECHNOLOGIES or size_band not in SIZE_BANDS or route not in ROUTES:
        raise S07OwnerSummaryError(f"{case_id}: invalid technology, size band, or route")

    arrival = _require_nonempty_string(case.get("arrival_date"), f"{case_id}.arrival_date")
    parse_iso_date(arrival, field=f"{case_id}.arrival_date")
    if not is_business_day(arrival) or not ARRIVAL_START <= arrival <= PERIOD_END:
        raise S07OwnerSummaryError(f"{case_id}: arrival is outside the frozen business-date cohort")
    fee_lock = _require_mapping(case.get("fee_schedule_lock"), f"{case_id}.fee_schedule_lock")
    if fee_lock.get("event") != "first_permit_submission" or fee_lock.get("date") != arrival:
        raise S07OwnerSummaryError(f"{case_id}: fee/arrival event binding mismatch")
    _find_event(case, "first_permit_submission", arrival)

    observed = _require_mapping(case.get("observed_cutoff"), f"{case_id}.observed_cutoff")
    if observed.get("as_of") != AS_OF:
        raise S07OwnerSummaryError(f"{case_id}: observed cutoff mismatch")
    events = case.get("events")
    if not isinstance(events, list):
        raise S07OwnerSummaryError(f"{case_id}: events must be a list")
    for event in events:
        if not isinstance(event, Mapping) or not isinstance(event.get("date"), str):
            raise S07OwnerSummaryError(f"{case_id}: malformed event")
        parse_iso_date(event["date"], field=f"{case_id}.event.date")
        if not is_business_day(event["date"]):
            raise S07OwnerSummaryError(f"{case_id}: event date is not a business day")
    observed_events = observed.get("events")
    if not isinstance(observed_events, list):
        raise S07OwnerSummaryError(f"{case_id}: observed events must be a list")
    for event in observed_events:
        if not isinstance(event, Mapping) or not isinstance(event.get("date"), str):
            raise S07OwnerSummaryError(f"{case_id}: malformed observed event")
        parse_iso_date(event["date"], field=f"{case_id}.observed_event.date")
        if event["date"] >= AS_OF:
            raise S07OwnerSummaryError(f"{case_id}: observed projection contains cutoff/future event")
    expected_observed_events = [event for event in events if event["date"] < AS_OF]
    if observed_events != expected_observed_events:
        raise S07OwnerSummaryError(f"{case_id}: observed events do not replay the cutoff projection")

    phases = _require_mapping(case.get("phases"), f"{case_id}.phases")
    missing_phases = (set(PHASE_CONTRACTS) | {"installation"}) - set(phases)
    if missing_phases:
        raise S07OwnerSummaryError(f"{case_id}: missing required phases {sorted(missing_phases)}")
    provenance = _require_mapping(
        case.get("private_membership_provenance"),
        f"{case_id}.private_membership_provenance",
    )
    if (
        provenance.get("basis") != "full_base_case_phase_membership_before_any_reporting_transform"
        or provenance.get("derived_memberships_constructed_here") is not False
        or provenance.get("private_audit_only") is not True
        or provenance.get("permitted_blind_input") is not False
    ):
        raise S07OwnerSummaryError(f"{case_id}: private membership boundary mismatch")
    if provenance.get("derived_reporting_memberships") != []:
        raise S07OwnerSummaryError(f"{case_id}: derived membership must not preexist aggregation")
    candidates = provenance.get("base_membership_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(PHASE_CONTRACTS):
        raise S07OwnerSummaryError(f"{case_id}: requires exactly four base phase candidates")
    by_phase: dict[str, Mapping[str, Any]] = {}
    candidate_ids: set[str] = set()
    for candidate in candidates:
        candidate = _require_mapping(candidate, f"{case_id}.membership_candidate")
        candidate_id = _require_nonempty_string(
            candidate.get("membership_candidate_id"),
            f"{case_id}.membership_candidate_id",
        )
        if candidate_id in candidate_ids:
            raise S07OwnerSummaryError(f"{case_id}: duplicate membership_candidate_id")
        candidate_ids.add(candidate_id)
        if candidate_id in seen_membership_candidate_ids:
            raise S07OwnerSummaryError(
                f"duplicate global membership_candidate_id: {candidate_id}"
            )
        seen_membership_candidate_ids.add(candidate_id)
        phase_id = candidate.get("phase_id")
        if phase_id not in PHASE_CONTRACTS or phase_id in by_phase:
            raise S07OwnerSummaryError(f"{case_id}: duplicate or unknown phase candidate")
        signature = (case_id, phase_id)
        if signature in seen_membership_candidates:
            raise S07OwnerSummaryError(f"duplicate case/phase membership candidate: {signature}")
        seen_membership_candidates.add(signature)
        if candidate_id != f"{case_id}.MEMBER.{phase_id}":
            raise S07OwnerSummaryError(
                f"{case_id}/{phase_id}: membership_candidate_id is noncanonical"
            )
        by_phase[phase_id] = candidate
        if not isinstance(candidate.get("completed_by_cutoff"), bool):
            raise S07OwnerSummaryError(
                f"{case_id}/{phase_id}: completed_by_cutoff must be boolean"
            )

    realized_public_phases: dict[str, int | None] = {}
    for phase_id, (owner_type, start_event, end_event) in PHASE_CONTRACTS.items():
        phase = _require_mapping(phases[phase_id], f"{case_id}.phases.{phase_id}")
        candidate = by_phase[phase_id]
        expected_owner = jid if owner_type == "ahj" else expected_utility
        expected_completed = (
            phase.get("status") == "completed"
            and isinstance(phase.get("end_date"), str)
            and phase["end_date"] < AS_OF
        )
        expected_candidate = {
            "case_id": case_id,
            "phase_id": phase_id,
            "owner_type": owner_type,
            "owner_id": expected_owner,
            "technology": technology,
            "size_band": size_band,
            "route": route,
            "phase_status": phase.get("status"),
            "completed_by_cutoff": expected_completed,
        }
        for field, expected in expected_candidate.items():
            if candidate.get(field) != expected:
                raise S07OwnerSummaryError(
                    f"{case_id}/{phase_id}: candidate field {field} mismatch"
                )
        if phase_id == "preinstall_ix" and route == "no_preinstall_approval":
            if phase.get("status") != "not_required":
                raise S07OwnerSummaryError(
                    f"{case_id}: no-preinstall phase must be structurally not_required"
                )
            realized_public_phases[phase_id] = None
        elif phase.get("status") == "completed":
            realized_public_phases[phase_id] = _replay_completed_phase(
                case_id, phase_id, phase,
                expected_start_event=start_event,
                expected_end_event=end_event,
                case=case,
            )
        else:
            if phase.get("status") == "not_required":
                raise S07OwnerSummaryError(
                    f"{case_id}/{phase_id}: not_required is invalid on this route"
                )
            realized_public_phases[phase_id] = None

    installation = _require_mapping(phases["installation"], f"{case_id}.phases.installation")
    installation_duration: int | None = None
    if installation.get("status") == "completed":
        installation_duration = _replay_completed_phase(
            case_id, "installation", installation,
            expected_start_event="installation_start",
            expected_end_event="installation_complete",
            case=case,
        )

    return {
        "case": case,
        "case_id": case_id,
        "jurisdiction_id": jid,
        "utility_id": expected_utility,
        "profile": profiles[jid],
        "technology": technology,
        "size_band": size_band,
        "route": route,
        "arrival_date": arrival,
        "public_phase_durations": realized_public_phases,
        "installation_duration": installation_duration,
        "installation_completed_by_cutoff": (
            installation.get("status") == "completed"
            and isinstance(installation.get("end_date"), str)
            and installation["end_date"] < AS_OF
        ),
    }


def _round_half_day(value: float) -> float:
    return math.floor(2.0 * value + 0.5) / 2.0


def _round_whole_day(value: float) -> int:
    return math.floor(value + 0.5)


def _transform_name(profile: str) -> str:
    return {
        "A": "all_base_linear_quantile_nearest_half_day_known_n",
        "B": "all_base_linear_quantile_nearest_whole_day_unknown_n",
        "C": "exclude_longest_floor_base_n_over_10_linear_quantile_nearest_half_day_known_selected_n",
        "D": "all_base_linear_quantile_nearest_whole_day_unknown_n_with_inspection_p90_gap",
    }[profile]


def _selected_members(
    base_members: list[tuple[str, int]], profile: str,
) -> tuple[list[tuple[str, int]], list[str]]:
    if profile != "C" or len(base_members) < 10:
        return list(base_members), []
    exclude_n = len(base_members) // 10
    ranked = sorted(base_members, key=lambda item: (item[1], item[0]), reverse=True)
    excluded = {case_id for case_id, _ in ranked[:exclude_n]}
    return (
        [item for item in base_members if item[0] not in excluded],
        sorted(excluded),
    )


def _raw_statistic(members: Sequence[tuple[str, int]], statistic: str) -> float | None:
    if not members:
        return None
    q = 0.5 if statistic == "median" else 0.9
    return quantile([duration for _, duration in members], q)


def _joined_install_count(
    cases: Sequence[Mapping[str, Any]],
    jurisdiction_id: str,
    technology: str,
    size_band: str,
    route: str,
) -> int:
    return sum(
        1 for case in cases
        if case["jurisdiction_id"] == jurisdiction_id
        and case["technology"] == technology
        and case["size_band"] == size_band
        and case["route"] == route
        and case["installation_completed_by_cutoff"]
    )


def _build_public_row(
    *,
    jurisdiction_id: str,
    owner_type: str,
    owner_id: str,
    phase_id: str,
    technology: str,
    size_band: str,
    route: str,
    statistic: str,
    profile: str,
    public_cohort_cell_id: str,
    base_n: int,
    selected_n: int,
    selected_raw: float | None,
    joined_install_count: int,
) -> dict[str, Any]:
    _, start_event, end_event = PHASE_CONTRACTS[phase_id]
    row: dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "release_id": RELEASE_ID,
        "observation_id": "pending",
        "owner_cell_id": "pending",
        "jurisdiction_id": jurisdiction_id,
        "owner_type": owner_type,
        "owner_id": owner_id,
        "phase_id": phase_id,
        "start_event": start_event,
        "end_event": end_event,
        "duration_basis": "elapsed_owner_phase_including_internal_queue_and_rework_within_boundaries",
        "unit": "business_days",
        "calendar_id": CALENDAR_ID,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "as_of": AS_OF,
        "technology": technology,
        "size_band": size_band,
        "route": route,
        "population": "pending",
        "statistic": statistic,
        "value_status": "pending",
        "value": None,
        "sample_size_status": "pending",
        "sample_size": None,
        "rounding": "not_applicable",
        "completion_conditioning": "phase_completed_by_cutoff",
        "zero_semantics": "pending",
        "joined_install_count": joined_install_count,
        "public_cohort_cell_id": public_cohort_cell_id,
    }
    structurally_absent = phase_id == "preinstall_ix" and route == "no_preinstall_approval"
    if structurally_absent:
        row.update({
            "value_status": "not_required",
            "sample_size_status": "not_applicable",
            "completion_conditioning": "not_applicable",
            "zero_semantics": "not_required",
        })
    elif base_n == 0:
        row.update({
            "value_status": "no_observed_cases",
            "sample_size_status": "known",
            "sample_size": 0,
            "zero_semantics": "no_observed_cases",
        })
    elif profile == "D" and phase_id == "ahj_inspection" and statistic == "p90":
        row.update({
            "value_status": "missing_report",
            "sample_size_status": "unknown",
            "zero_semantics": "suppressed_or_missing",
        })
    else:
        assert selected_raw is not None
        if profile in ("A", "C"):
            value: int | float = _round_half_day(selected_raw)
            rounding = "nearest_half_business_day"
            sample_status = "known"
            sample_size: int | None = selected_n
        else:
            value = _round_whole_day(selected_raw)
            rounding = "nearest_business_day"
            sample_status = "unknown"
            sample_size = None
        row.update({
            "value_status": "reported",
            "value": value,
            "sample_size_status": sample_status,
            "sample_size": sample_size,
            "rounding": rounding,
            "zero_semantics": "same_day_completed" if value == 0 else "not_zero",
        })
    row["population"] = canonical_population(row)
    row["owner_cell_id"] = canonical_owner_cell_id(row)
    row["observation_id"] = canonical_observation_id(jurisdiction_id, row["owner_cell_id"])
    validate_public_observation(row)
    return row


def _validate_output_matrix(result: OwnerSummaryCollections) -> None:
    rows = result.public_observations
    validate_public_observations(rows)
    validate_declared_public_leak_policy(rows)
    if len(rows) != EXPECTED_PUBLIC_ROWS:
        raise S07OwnerSummaryError(f"expected {EXPECTED_PUBLIC_ROWS} public rows")
    if len({row["observation_id"] for row in rows}) != EXPECTED_PUBLIC_ROWS:
        raise S07OwnerSummaryError("public observation IDs are not unique")
    owner_counts = Counter(row["owner_cell_id"] for row in rows)
    if len(owner_counts) != EXPECTED_OWNER_CELLS:
        raise S07OwnerSummaryError(f"expected {EXPECTED_OWNER_CELLS} unique owner cells")
    cohort_ids = {row["public_cohort_cell_id"] for row in rows}
    if len(cohort_ids) != EXPECTED_COHORT_CELLS:
        raise S07OwnerSummaryError(f"expected {EXPECTED_COHORT_CELLS} unique cohorts")
    ahj_counts = [
        count for owner_id, count in owner_counts.items()
        if next(row for row in rows if row["owner_cell_id"] == owner_id)["owner_type"] == "ahj"
    ]
    utility_counts = [
        count for owner_id, count in owner_counts.items()
        if next(row for row in rows if row["owner_cell_id"] == owner_id)["owner_type"] == "utility"
    ]
    if len(ahj_counts) != 576 or set(ahj_counts) != {1}:
        raise S07OwnerSummaryError("AHJ owner-cell cardinality mismatch")
    if len(utility_counts) != 288 or set(utility_counts) != {2}:
        raise S07OwnerSummaryError("utility owner-cell cardinality mismatch")
    for owner_cell_id, count in owner_counts.items():
        if count != 2:
            continue
        paired = [row for row in rows if row["owner_cell_id"] == owner_cell_id]
        expected = set(UTILITY_JURISDICTIONS[paired[0]["owner_id"]])
        if {row["jurisdiction_id"] for row in paired} != expected:
            raise S07OwnerSummaryError("utility owner cell has wrong restatement jurisdictions")
    rows_by_cohort: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_cohort[row["public_cohort_cell_id"]].append(row)
    for cohort_rows in rows_by_cohort.values():
        expected_count = 2 if cohort_rows[0]["owner_type"] == "ahj" else 4
        if len(cohort_rows) != expected_count:
            raise S07OwnerSummaryError("public cohort has wrong statistic/restatement cardinality")
        if {row["statistic"] for row in cohort_rows} != set(STATISTICS):
            raise S07OwnerSummaryError("public cohort does not contain median and p90")
    if len(result.private_cohort_memberships) != EXPECTED_COHORT_CELLS:
        raise S07OwnerSummaryError("private cohort membership cardinality mismatch")
    private_by_cohort: dict[str, Mapping[str, Any]] = {}
    for record in result.private_cohort_memberships:
        cohort_id = record["public_cohort_cell_id"]
        if cohort_id in private_by_cohort:
            raise S07OwnerSummaryError("duplicate private cohort membership record")
        private_by_cohort[cohort_id] = record
        base_ids = record["base_case_ids"]
        selected_ids = record["selected_case_ids"]
        excluded_ids = record["excluded_case_ids"]
        if (
            base_ids != sorted(set(base_ids))
            or selected_ids != sorted(set(selected_ids))
            or excluded_ids != sorted(set(excluded_ids))
        ):
            raise S07OwnerSummaryError("private membership IDs must be sorted and unique")
        if not set(selected_ids).issubset(base_ids):
            raise S07OwnerSummaryError("selected membership is not a subset of base membership")
        if excluded_ids != sorted(set(base_ids) - set(selected_ids)):
            raise S07OwnerSummaryError("excluded membership does not replay base minus selected")
        if record["base_n"] != len(base_ids) or record["selected_n"] != len(selected_ids):
            raise S07OwnerSummaryError("private membership count mismatch")
        if record["base_membership_hash"] != membership_hash(cohort_id, "base", base_ids):
            raise S07OwnerSummaryError("base membership hash mismatch")
        if record["selected_membership_hash"] != membership_hash(
            cohort_id, "selected", selected_ids,
        ):
            raise S07OwnerSummaryError("selected membership hash mismatch")
        if (
            record["identity_control_membership_kind"] != "base"
            or record["identity_control_membership_hash"] != record["base_membership_hash"]
        ):
            raise S07OwnerSummaryError("identity control does not use full base membership")
    private_cohort_ids = set(private_by_cohort)
    if private_cohort_ids != cohort_ids:
        raise S07OwnerSummaryError("private cohort records do not resolve every public cohort")
    if len(result.private_observation_companions) != EXPECTED_PUBLIC_ROWS:
        raise S07OwnerSummaryError("private observation companion cardinality mismatch")
    companion_by_id: dict[str, Mapping[str, Any]] = {}
    public_by_id = {row["observation_id"]: row for row in rows}
    for companion in result.private_observation_companions:
        observation_id = companion["observation_id"]
        if observation_id in companion_by_id:
            raise S07OwnerSummaryError("duplicate private observation companion")
        companion_by_id[observation_id] = companion
        if observation_id not in public_by_id:
            raise S07OwnerSummaryError("private companion does not resolve a public observation")
        public = public_by_id[observation_id]
        cohort = private_by_cohort[companion["public_cohort_cell_id"]]
        if companion["cohort_record_id"] != cohort["cohort_record_id"]:
            raise S07OwnerSummaryError("private companion cohort reference mismatch")
        for prefix in ("base", "selected"):
            if companion[f"{prefix}_n"] != cohort[f"{prefix}_n"]:
                raise S07OwnerSummaryError("private companion membership count mismatch")
            if companion[f"{prefix}_membership_hash"] != cohort[f"{prefix}_membership_hash"]:
                raise S07OwnerSummaryError("private companion membership hash mismatch")
        if (
            companion["owner_cell_id"] != public["owner_cell_id"]
            or companion["public_value_status"] != public["value_status"]
            or companion["public_value"] != public["value"]
            or companion["statistic"] != public["statistic"]
            or companion["restatement_jurisdiction_id"] != public["jurisdiction_id"]
        ):
            raise S07OwnerSummaryError("private companion does not replay its public row")
        if (
            companion["identity_control_untransformed_value"]
            != companion["base_unrounded_statistic"]
        ):
            raise S07OwnerSummaryError("companion identity control is not the base statistic")
    companion_ids = set(companion_by_id)
    if companion_ids != {row["observation_id"] for row in rows}:
        raise S07OwnerSummaryError("private companions do not resolve every observation")


def build_owner_summaries(
    cases: Sequence[Mapping[str, Any]],
    jurisdiction_profiles: Mapping[str, str],
) -> OwnerSummaryCollections:
    """Build the frozen S07 matrix without reading or writing external state."""
    if isinstance(cases, (str, bytes, bytearray)) or not isinstance(cases, Sequence):
        raise S07OwnerSummaryError("cases must be a sequence of private case mappings")
    profiles = _validate_profile_map(jurisdiction_profiles)
    seen_case_ids: set[str] = set()
    seen_membership_candidate_ids: set[str] = set()
    seen_membership_candidates: set[tuple[str, str]] = set()
    validated_cases = [
        _validate_case(
            case, profiles, seen_case_ids,
            seen_membership_candidate_ids, seen_membership_candidates,
        )
        for case in cases
    ]

    case_index: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for case in validated_cases:
        for phase_id, duration in case["public_phase_durations"].items():
            phase = case["case"]["phases"][phase_id]
            if (
                duration is not None
                and phase["status"] == "completed"
                and phase["end_date"] < AS_OF
            ):
                owner_type = PHASE_CONTRACTS[phase_id][0]
                owner_id = (
                    case["jurisdiction_id"] if owner_type == "ahj" else case["utility_id"]
                )
                key = (
                    phase_id, owner_id, case["technology"], case["size_band"], case["route"],
                )
                case_index[key].append(case)

    public_rows: list[dict[str, Any]] = []
    private_cohorts: list[dict[str, Any]] = []
    private_companions: list[dict[str, Any]] = []
    for phase_id, (owner_type, _, _) in PHASE_CONTRACTS.items():
        owners: list[tuple[str, tuple[str, ...], str]]
        if owner_type == "ahj":
            owners = [
                (jid, (jid,), profiles[jid]) for jid in sorted(JURISDICTIONS)
            ]
        else:
            owners = [
                (utility_id, tuple(sorted(jurisdictions)), UTILITY_REPORTING_PROFILES[utility_id])
                for utility_id, jurisdictions in sorted(UTILITY_JURISDICTIONS.items())
            ]
        for owner_id, restatement_jurisdictions, profile in owners:
            for technology in TECHNOLOGIES:
                for size_band in SIZE_BANDS:
                    for route in ROUTES:
                        cell_basis = {
                            "owner_type": owner_type,
                            "owner_id": owner_id,
                            "period_start": PERIOD_START,
                            "period_end": PERIOD_END,
                            "technology": technology,
                            "size_band": size_band,
                            "route": route,
                            "phase_id": phase_id,
                            "completion_conditioning": (
                                "not_applicable"
                                if phase_id == "preinstall_ix" and route == "no_preinstall_approval"
                                else "phase_completed_by_cutoff"
                            ),
                        }
                        cohort_id = canonical_public_cohort_cell_id(cell_basis)
                        members = case_index.get(
                            (phase_id, owner_id, technology, size_band, route), [],
                        )
                        base_members = sorted(
                            (
                                case["case_id"],
                                case["public_phase_durations"][phase_id],
                            )
                            for case in members
                        )
                        if phase_id == "preinstall_ix" and route == "no_preinstall_approval":
                            if base_members:
                                raise S07OwnerSummaryError(
                                    "structurally absent preinstall cohort has members"
                                )
                        selected_members, excluded_ids = _selected_members(base_members, profile)
                        base_ids = sorted(case_id for case_id, _ in base_members)
                        selected_ids = sorted(case_id for case_id, _ in selected_members)
                        base_hash = membership_hash(cohort_id, "base", base_ids)
                        selected_hash = membership_hash(cohort_id, "selected", selected_ids)
                        same_cohort_group = f"s07-same-cohort:{cohort_id}"
                        transform = (
                            "not_applicable_structural_absence"
                            if phase_id == "preinstall_ix" and route == "no_preinstall_approval"
                            else _transform_name(profile)
                        )
                        private_cohorts.append({
                            "schema_version": "s07-private-cohort-membership/1",
                            "world_id": WORLD_ID,
                            "release_id": RELEASE_ID,
                            "cohort_record_id": cohort_id,
                            "public_cohort_cell_id": cohort_id,
                            "owner_type": owner_type,
                            "owner_id": owner_id,
                            "phase_id": phase_id,
                            "technology": technology,
                            "size_band": size_band,
                            "route": route,
                            "period_start": PERIOD_START,
                            "period_end": PERIOD_END,
                            "as_of": AS_OF,
                            "profile": profile,
                            "reporting_transform": transform,
                            "base_case_ids": base_ids,
                            "base_n": len(base_ids),
                            "base_membership_hash": base_hash,
                            "selected_case_ids": selected_ids,
                            "selected_n": len(selected_ids),
                            "selected_membership_hash": selected_hash,
                            "excluded_case_ids": excluded_ids,
                            "identity_control_membership_kind": "base",
                            "identity_control_membership_hash": base_hash,
                            "same_cohort_group": same_cohort_group,
                            "private_audit_only": True,
                            "permitted_blind_input": False,
                        })
                        for statistic in STATISTICS:
                            base_raw = _raw_statistic(base_members, statistic)
                            selected_raw = _raw_statistic(selected_members, statistic)
                            for jid in restatement_jurisdictions:
                                joined_count = _joined_install_count(
                                    validated_cases, jid, technology, size_band, route,
                                )
                                row = _build_public_row(
                                    jurisdiction_id=jid,
                                    owner_type=owner_type,
                                    owner_id=owner_id,
                                    phase_id=phase_id,
                                    technology=technology,
                                    size_band=size_band,
                                    route=route,
                                    statistic=statistic,
                                    profile=profile,
                                    public_cohort_cell_id=cohort_id,
                                    base_n=len(base_ids),
                                    selected_n=len(selected_ids),
                                    selected_raw=selected_raw,
                                    joined_install_count=joined_count,
                                )
                                public_rows.append(row)
                                private_companions.append({
                                    "schema_version": "s07-private-observation-companion/1",
                                    "world_id": WORLD_ID,
                                    "release_id": RELEASE_ID,
                                    "observation_id": row["observation_id"],
                                    "owner_cell_id": row["owner_cell_id"],
                                    "public_cohort_cell_id": cohort_id,
                                    "cohort_record_id": cohort_id,
                                    "restatement_jurisdiction_id": jid,
                                    "statistic": statistic,
                                    "profile": profile,
                                    "reporting_transform": transform,
                                    "base_n": len(base_ids),
                                    "base_membership_hash": base_hash,
                                    "base_unrounded_statistic": base_raw,
                                    "identity_control_untransformed_value": base_raw,
                                    "selected_n": len(selected_ids),
                                    "selected_membership_hash": selected_hash,
                                    "selected_unrounded_statistic": selected_raw,
                                    "public_value_status": row["value_status"],
                                    "public_value": row["value"],
                                    "same_cohort_group": same_cohort_group,
                                    "lineage_relation": "same_cohort",
                                    "private_audit_only": True,
                                    "permitted_blind_input": False,
                                })

    result = OwnerSummaryCollections(
        public_observations=tuple(sorted(public_rows, key=lambda row: row["observation_id"])),
        private_cohort_memberships=tuple(
            sorted(private_cohorts, key=lambda row: row["public_cohort_cell_id"])
        ),
        private_observation_companions=tuple(
            sorted(private_companions, key=lambda row: row["observation_id"])
        ),
    )
    _validate_output_matrix(result)
    return result


__all__ = [
    "OwnerSummaryCollections", "S07OwnerSummaryError",
    "UTILITY_REPORTING_PROFILES", "build_owner_summaries",
    "canonical_observation_id", "membership_hash",
]
