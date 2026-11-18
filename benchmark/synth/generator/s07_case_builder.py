"""Deterministic in-memory mechanics for fictional S07 cases.

This module does not write a world, render documents, aggregate public rows,
or prepare model inputs.  Callers supply an explicit mechanics configuration,
a reviewed resolved structural source, and its effective structural design.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping

from .rng import chance, lognormal_params, sub_rng
from .s07_fresh_replica import (
    AS_OF,
    PHASE_CONTRACTS,
    S07ContractError,
    add_business_days as _calendar_add_business_days,
    is_business_day,
    parse_iso_date,
)
from .s07_structural_sources import validate_resolved_source


ROUTES = ("parallel_standard", "serial_standard", "no_preinstall_approval")
TECHNOLOGIES = ("pv_only", "pv_plus_storage")
SIZE_BANDS = ("0_10_kw", "10_38_4_kw")
PUBLIC_PHASES = tuple(PHASE_CONTRACTS)
CASES_PER_JURISDICTION = 1000
_ROUTE_SUFFIX = {
    "parallel_standard": "PARALLEL",
    "serial_standard": "SERIAL",
    "no_preinstall_approval": "NOPRE",
}


class S07CaseMechanicsError(S07ContractError):
    """Raised when explicit inputs cannot produce a valid S07 case."""


@dataclass(frozen=True)
class DurationSpec:
    median: float
    p90: float


@dataclass(frozen=True)
class DurationDraw:
    raw_business_days: float
    rounded_business_days: int


@dataclass(frozen=True)
class CaseMechanicsConfig:
    profile_id: str
    window_start: str
    window_end: str
    as_of: str
    speed_multiplier: float
    storage_share: float
    small_size_share: float
    automatic_permit_share: float
    automatic_same_day_probability: float
    preinstall_required_share: float
    parallel_submission_share: float
    denied_probability: float
    withdrawn_probability: float
    abandoned_probability: float
    max_repeats: int
    durations: Mapping[str, DurationSpec]
    repeat_probabilities: Mapping[str, float]


@dataclass(frozen=True)
class CaseDraws:
    arrival_date: str
    technology: str
    size_band: str
    automatic_permit: bool
    preinstall_required: bool
    parallel_submission: bool
    durations: Mapping[str, DurationDraw]
    repeat_counts: Mapping[str, int]
    denied: bool
    withdrawn: bool
    abandoned: bool


_DURATION_KEYS = frozenset((
    "design_sign_to_submit", "ahj_permit_manual",
    "ahj_permit_automatic_positive", "preinstall_ix", "installation",
    "ahj_inspection", "postinspection_handoff", "final_ix_to_pto",
))
_REPEAT_KEYS = frozenset((
    "ahj_permit_manual", "preinstall_ix", "ahj_inspection",
    "final_ix_to_pto",
))


def _probability(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise S07CaseMechanicsError(f"{label} must be numeric, not boolean")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise S07CaseMechanicsError(f"{label} must be finite and in [0,1]")
    return result


def validate_mechanics_config(config: CaseMechanicsConfig) -> None:
    if not isinstance(config.profile_id, str) or not config.profile_id:
        raise S07CaseMechanicsError("profile_id must be a nonempty string")
    start = parse_iso_date(config.window_start, field="window_start")
    end = parse_iso_date(config.window_end, field="window_end")
    cutoff = parse_iso_date(config.as_of, field="as_of")
    if end < start or cutoff <= end:
        raise S07CaseMechanicsError("window or cutoff ordering is invalid")
    if (config.window_start, config.window_end, config.as_of) != (
        "2024-09-02", "2026-08-31", AS_OF,
    ):
        raise S07CaseMechanicsError(
            "arrival window and cutoff must match the reviewed S07 R01 contract"
        )
    if isinstance(config.speed_multiplier, bool) or not isinstance(config.speed_multiplier, (int, float)):
        raise S07CaseMechanicsError("speed_multiplier must be numeric")
    if not math.isfinite(float(config.speed_multiplier)) or config.speed_multiplier <= 0:
        raise S07CaseMechanicsError("speed_multiplier must be finite and positive")
    for field in (
        "storage_share", "small_size_share", "automatic_permit_share",
        "automatic_same_day_probability", "preinstall_required_share",
        "parallel_submission_share", "denied_probability",
        "withdrawn_probability", "abandoned_probability",
    ):
        _probability(getattr(config, field), field)
    fixed_probabilities = {
        "small_size_share": 0.75,
        "automatic_same_day_probability": 0.55,
        "denied_probability": 0.04,
        "withdrawn_probability": 0.03,
        "abandoned_probability": 0.03,
    }
    for field, expected in fixed_probabilities.items():
        if getattr(config, field) != expected:
            raise S07CaseMechanicsError(
                f"{field} must equal the reviewed value {expected}"
            )
    if isinstance(config.max_repeats, bool) or not isinstance(config.max_repeats, int):
        raise S07CaseMechanicsError("max_repeats must be an integer, not boolean")
    if config.max_repeats != 2:
        raise S07CaseMechanicsError("the reviewed mechanics require max_repeats=2")
    if set(config.durations) != _DURATION_KEYS:
        raise S07CaseMechanicsError("durations must bind the exact reviewed keys")
    for key, spec in config.durations.items():
        if not isinstance(spec, DurationSpec):
            raise S07CaseMechanicsError(f"duration {key} must be a DurationSpec")
        for label, value in (("median", spec.median), ("p90", spec.p90)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise S07CaseMechanicsError(f"{key}.{label} must be numeric")
            if not math.isfinite(float(value)) or value <= 0:
                raise S07CaseMechanicsError(f"{key}.{label} must be finite and positive")
        if spec.p90 <= spec.median:
            raise S07CaseMechanicsError(f"{key}.p90 must exceed its median")
    if set(config.repeat_probabilities) != _REPEAT_KEYS:
        raise S07CaseMechanicsError("repeat_probabilities must bind exact reviewed keys")
    for key, value in config.repeat_probabilities.items():
        _probability(value, f"repeat_probabilities.{key}")


def _business_dates(start: str, end: str) -> tuple[str, ...]:
    first = parse_iso_date(start, field="window_start")
    last = parse_iso_date(end, field="window_end")
    if last < first:
        raise S07CaseMechanicsError("window_end precedes window_start")
    values = []
    current = first
    while current <= last:
        if current.weekday() < 5:
            values.append(current.isoformat())
        current += timedelta(days=1)
    if not values:
        raise S07CaseMechanicsError("arrival window contains no business dates")
    return tuple(values)


def subtract_business_days(start: str, days: int) -> str:
    """Subtract nonnegative weekdays without shifting a weekend start."""
    current = parse_iso_date(start, field="start")
    if current.weekday() >= 5:
        raise S07CaseMechanicsError("start must be a business day")
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise S07CaseMechanicsError("days must be a nonnegative integer, not boolean")
    weeks, remaining = divmod(days, 5)
    try:
        current -= timedelta(days=weeks * 7)
    except OverflowError as exc:
        raise S07CaseMechanicsError("business-day subtraction overflows the date range") from exc
    while remaining:
        try:
            current -= timedelta(days=1)
        except OverflowError as exc:
            raise S07CaseMechanicsError("business-day subtraction overflows the date range") from exc
        if current.weekday() < 5:
            remaining -= 1
    return current.isoformat()


def _add_business_days(start: str, days: int) -> str:
    """Use the reviewed calendar while failing promptly on date overflow."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise S07CaseMechanicsError("days must be a nonnegative integer, not boolean")
    first = parse_iso_date(start, field="start")
    if first.weekday() >= 5:
        raise S07CaseMechanicsError("start must be a business day")
    weeks, remainder = divmod(days, 5)
    try:
        base = first + timedelta(days=weeks * 7)
    except OverflowError as exc:
        raise S07CaseMechanicsError("business-day addition overflows the date range") from exc
    try:
        return _calendar_add_business_days(base.isoformat(), remainder)
    except OverflowError as exc:
        raise S07CaseMechanicsError("business-day addition overflows the date range") from exc


def _case_rng(seed: int, jurisdiction_id: str, case_id: str, mechanism: str, *extra: Any):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise S07CaseMechanicsError("seed must be an integer, not boolean")
    return sub_rng(seed, "s07_r01", jurisdiction_id, case_id, mechanism, *extra)


def _round_half_up(value: float) -> int:
    if not math.isfinite(value) or value < 0:
        raise S07CaseMechanicsError("duration draw must be finite and nonnegative")
    return int(math.floor(value + 0.5))


def _duration_draw(
    config: CaseMechanicsConfig,
    seed: int,
    jurisdiction_id: str,
    case_id: str,
    key: str,
    *,
    positive: bool = False,
) -> DurationDraw:
    spec = config.durations[key]
    median = spec.median * config.speed_multiplier
    p90 = spec.p90 * config.speed_multiplier
    mu, sigma = lognormal_params(median, p90)
    try:
        raw = math.exp(
            _case_rng(seed, jurisdiction_id, case_id, "duration", key).gauss(mu, sigma)
        )
    except OverflowError as exc:
        raise S07CaseMechanicsError(f"duration draw overflow for {key}") from exc
    if not math.isfinite(raw):
        raise S07CaseMechanicsError(f"nonfinite duration draw for {key}")
    rounded = _round_half_up(raw)
    if positive:
        rounded = max(1, rounded)
    return DurationDraw(raw_business_days=raw, rounded_business_days=rounded)


def _repeat_count(
    config: CaseMechanicsConfig,
    seed: int,
    jurisdiction_id: str,
    case_id: str,
    key: str,
) -> int:
    probability = config.repeat_probabilities[key]
    count = 0
    while count < config.max_repeats:
        rng = _case_rng(seed, jurisdiction_id, case_id, "repeat", key, count + 1)
        if not chance(rng, probability):
            break
        count += 1
    return count


def choose_route(preinstall_required: bool, parallel_submission: bool) -> str:
    if not isinstance(preinstall_required, bool) or not isinstance(parallel_submission, bool):
        raise S07CaseMechanicsError("route flags must be boolean")
    if not preinstall_required and parallel_submission:
        raise S07CaseMechanicsError("parallel_submission requires preinstall_required")
    if not preinstall_required:
        return "no_preinstall_approval"
    return "parallel_standard" if parallel_submission else "serial_standard"


def draw_case_inputs(
    config: CaseMechanicsConfig,
    *,
    seed: int,
    jurisdiction_id: str,
    case_index: int,
) -> CaseDraws:
    """Draw one case using order-independent semantic RNG paths."""
    validate_mechanics_config(config)
    if not isinstance(jurisdiction_id, str) or not jurisdiction_id:
        raise S07CaseMechanicsError("jurisdiction_id must be a nonempty string")
    if (
        isinstance(case_index, bool)
        or not isinstance(case_index, int)
        or not 1 <= case_index <= CASES_PER_JURISDICTION
    ):
        raise S07CaseMechanicsError("case_index must be an integer in 1..1000, not boolean")
    case_id = f"{jurisdiction_id}.C{case_index:04d}"
    arrival_dates = _business_dates(config.window_start, config.window_end)
    arrival_rng = _case_rng(seed, jurisdiction_id, case_id, "arrival")
    arrival = arrival_dates[arrival_rng.randrange(len(arrival_dates))]
    storage = chance(
        _case_rng(seed, jurisdiction_id, case_id, "technology"),
        config.storage_share,
    )
    small = chance(
        _case_rng(seed, jurisdiction_id, case_id, "size_band"),
        config.small_size_share,
    )
    automatic = chance(
        _case_rng(seed, jurisdiction_id, case_id, "automatic_permit"),
        config.automatic_permit_share,
    )
    preinstall = chance(
        _case_rng(seed, jurisdiction_id, case_id, "preinstall_required"),
        config.preinstall_required_share,
    )
    parallel = preinstall and chance(
        _case_rng(seed, jurisdiction_id, case_id, "parallel_submission"),
        config.parallel_submission_share,
    )
    durations: dict[str, DurationDraw] = {
        "design_sign_to_submit": _duration_draw(
            config, seed, jurisdiction_id, case_id, "design_sign_to_submit"
        ),
        "preinstall_ix": _duration_draw(
            config, seed, jurisdiction_id, case_id, "preinstall_ix"
        ),
        "installation": _duration_draw(
            config, seed, jurisdiction_id, case_id, "installation"
        ),
        "ahj_inspection": _duration_draw(
            config, seed, jurisdiction_id, case_id, "ahj_inspection"
        ),
        "postinspection_handoff": _duration_draw(
            config, seed, jurisdiction_id, case_id, "postinspection_handoff"
        ),
        "final_ix_to_pto": _duration_draw(
            config, seed, jurisdiction_id, case_id, "final_ix_to_pto"
        ),
    }
    if automatic and chance(
        _case_rng(seed, jurisdiction_id, case_id, "automatic_same_day"),
        config.automatic_same_day_probability,
    ):
        durations["ahj_permit"] = DurationDraw(0.0, 0)
    elif automatic:
        durations["ahj_permit"] = _duration_draw(
            config, seed, jurisdiction_id, case_id,
            "ahj_permit_automatic_positive", positive=True,
        )
    else:
        durations["ahj_permit"] = _duration_draw(
            config, seed, jurisdiction_id, case_id, "ahj_permit_manual"
        )
    repeats = {
        "ahj_permit": 0 if automatic else _repeat_count(
            config, seed, jurisdiction_id, case_id, "ahj_permit_manual"
        ),
        "preinstall_ix": _repeat_count(
            config, seed, jurisdiction_id, case_id, "preinstall_ix"
        ) if preinstall else 0,
        "ahj_inspection": _repeat_count(
            config, seed, jurisdiction_id, case_id, "ahj_inspection"
        ),
        "final_ix_to_pto": _repeat_count(
            config, seed, jurisdiction_id, case_id, "final_ix_to_pto"
        ),
    }
    return CaseDraws(
        arrival_date=arrival,
        technology="pv_plus_storage" if storage else "pv_only",
        size_band="0_10_kw" if small else "10_38_4_kw",
        automatic_permit=automatic,
        preinstall_required=preinstall,
        parallel_submission=parallel,
        durations=durations,
        repeat_counts=repeats,
        denied=chance(
            _case_rng(seed, jurisdiction_id, case_id, "outcome", "denied"),
            config.denied_probability,
        ),
        withdrawn=chance(
            _case_rng(seed, jurisdiction_id, case_id, "outcome", "withdrawn"),
            config.withdrawn_probability,
        ),
        abandoned=chance(
            _case_rng(seed, jurisdiction_id, case_id, "outcome", "abandoned"),
            config.abandoned_probability,
        ),
    )


def _validate_draws(config: CaseMechanicsConfig, draws: CaseDraws) -> None:
    if not is_business_day(draws.arrival_date):
        raise S07CaseMechanicsError("arrival_date must be a business date")
    if not config.window_start <= draws.arrival_date <= config.window_end:
        raise S07CaseMechanicsError("arrival_date lies outside the configured window")
    if draws.technology not in TECHNOLOGIES or draws.size_band not in SIZE_BANDS:
        raise S07CaseMechanicsError("draws contain an unknown technology or size band")
    for field in (
        "automatic_permit", "preinstall_required", "parallel_submission",
        "denied", "withdrawn", "abandoned",
    ):
        if not isinstance(getattr(draws, field), bool):
            raise S07CaseMechanicsError(f"draws.{field} must be boolean")
    if not draws.preinstall_required and draws.parallel_submission:
        raise S07CaseMechanicsError("parallel_submission requires preinstall_required")
    expected_durations = {
        "design_sign_to_submit", "ahj_permit", "preinstall_ix", "installation",
        "ahj_inspection", "postinspection_handoff", "final_ix_to_pto",
    }
    if set(draws.durations) != expected_durations:
        raise S07CaseMechanicsError("draws.durations has the wrong keys")
    for key, draw in draws.durations.items():
        if not isinstance(draw, DurationDraw):
            raise S07CaseMechanicsError(f"draws.durations.{key} is invalid")
        if (
            isinstance(draw.raw_business_days, bool)
            or not isinstance(draw.raw_business_days, (int, float))
            or not math.isfinite(draw.raw_business_days)
            or draw.raw_business_days < 0
        ):
            raise S07CaseMechanicsError(f"draws.durations.{key}.raw is invalid")
        if (
            isinstance(draw.rounded_business_days, bool)
            or not isinstance(draw.rounded_business_days, int)
            or draw.rounded_business_days < 0
        ):
            raise S07CaseMechanicsError(f"draws.durations.{key}.rounded is invalid")
        expected = _round_half_up(draw.raw_business_days)
        if key == "ahj_permit" and draws.automatic_permit and draw.raw_business_days > 0:
            expected = max(1, expected)
        if draw.rounded_business_days != expected:
            raise S07CaseMechanicsError(
                f"draws.durations.{key}.rounded does not replay from its raw value"
            )
    if draws.automatic_permit and draws.repeat_counts.get("ahj_permit") != 0:
        raise S07CaseMechanicsError("automatic permit cases cannot carry permit repeats")
    if set(draws.repeat_counts) != {
        "ahj_permit", "preinstall_ix", "ahj_inspection", "final_ix_to_pto",
    }:
        raise S07CaseMechanicsError("draws.repeat_counts has the wrong keys")
    for key, count in draws.repeat_counts.items():
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 2:
            raise S07CaseMechanicsError(f"draws.repeat_counts.{key} must be 0..2")
    if not draws.preinstall_required and draws.repeat_counts["preinstall_ix"] != 0:
        raise S07CaseMechanicsError("a structurally absent preinstall phase cannot repeat")


def adjusted_duration(draw: DurationDraw, *, phase_id: str, repeats: int) -> dict[str, Any]:
    """Apply reviewed repeat chronology floors only when repeats are positive."""
    if not isinstance(draw, DurationDraw):
        raise S07CaseMechanicsError("draw must be a DurationDraw")
    if (
        isinstance(draw.raw_business_days, bool)
        or not isinstance(draw.raw_business_days, (int, float))
        or not math.isfinite(draw.raw_business_days)
        or draw.raw_business_days < 0
    ):
        raise S07CaseMechanicsError("draw.raw_business_days must be finite and nonnegative")
    if (
        isinstance(draw.rounded_business_days, bool)
        or not isinstance(draw.rounded_business_days, int)
        or draw.rounded_business_days < 0
    ):
        raise S07CaseMechanicsError("draw.rounded_business_days must be a nonnegative integer")
    if phase_id not in {
        "design_sign_to_submit", "ahj_permit", "preinstall_ix", "installation",
        "ahj_inspection", "postinspection_handoff", "final_ix_to_pto",
    }:
        raise S07CaseMechanicsError("phase_id is outside the reviewed mechanics")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or not 0 <= repeats <= 2:
        raise S07CaseMechanicsError("repeats must be an integer in 0..2, not boolean")
    realized = draw.rounded_business_days
    minimum = 0
    if repeats > 0 and phase_id == "ahj_permit":
        minimum = 2 * repeats + 1
    elif repeats > 0 and phase_id == "ahj_inspection":
        minimum = 3 * repeats + 1
    if minimum:
        realized = max(realized, minimum)
    return {
        "raw_sampled_business_days": draw.raw_business_days,
        "rounded_business_days": draw.rounded_business_days,
        "realized_business_days": realized,
        "repeat_chronology_floor": minimum,
        "repeat_floor_applied": realized != draw.rounded_business_days,
    }


def repeat_event_offsets(total_duration: int, *, repeats: int, events_per_repeat: int) -> tuple[int, ...]:
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (
        total_duration, repeats, events_per_repeat,
    )):
        raise S07CaseMechanicsError("repeat offset inputs must be integers, not booleans")
    if total_duration < 0 or repeats < 0 or events_per_repeat < 1:
        raise S07CaseMechanicsError("repeat offset inputs are out of range")
    count = repeats * events_per_repeat
    if count == 0:
        return ()
    if total_duration < count + 1:
        raise S07CaseMechanicsError("total duration cannot place strict repeat chronology")
    return tuple(math.ceil(k * total_duration / (count + 1)) for k in range(1, count + 1))


def _index_by_suffix(rows: list[dict], field: str, suffix: str) -> dict:
    matches = [row for row in rows if row[field].endswith(suffix)]
    if len(matches) != 1:
        raise S07CaseMechanicsError(f"expected exactly one structural row ending {suffix}")
    return matches[0]


def _eventual_phase(
    phase_id: str,
    *,
    status: str,
    start_event: str | None,
    start_date: str | None,
    end_event: str | None,
    end_date: str | None,
    duration: dict[str, Any] | None,
    repeats: int,
) -> dict[str, Any]:
    return {
        "phase_id": phase_id,
        "status": status,
        "start_event": start_event,
        "start_date": start_date,
        "end_event": end_event,
        "end_date": end_date,
        "duration": duration,
        "repeat_count": repeats,
    }


def build_case_from_draws(
    config: CaseMechanicsConfig,
    structural_source: Mapping[str, Any],
    structural_design: Mapping[str, Any],
    *,
    case_index: int,
    draws: CaseDraws,
) -> dict[str, Any]:
    """Build one private in-memory case from explicit, reviewable draws."""
    validate_mechanics_config(config)
    validate_resolved_source(structural_source, structural_design)
    _validate_draws(config, draws)
    if (
        isinstance(case_index, bool)
        or not isinstance(case_index, int)
        or not 1 <= case_index <= CASES_PER_JURISDICTION
    ):
        raise S07CaseMechanicsError("case_index must be an integer in 1..1000, not boolean")
    jid = structural_source["jurisdiction_id"]
    case_id = f"{jid}.C{case_index:04d}"
    route = choose_route(draws.preinstall_required, draws.parallel_submission)
    suffix = _ROUTE_SUFFIX[route]
    as_of = config.as_of

    events: list[dict[str, Any]] = []
    phases: dict[str, dict[str, Any]] = {}
    encounters: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    checklist: list[dict[str, Any]] = []
    fees: list[dict[str, Any]] = []
    sequence = 0

    def add_event(event: str, event_date: str, **details: Any) -> None:
        nonlocal sequence
        if not is_business_day(event_date):
            raise S07CaseMechanicsError(f"event {event} is not on a business day")
        sequence += 1
        events.append({"event": event, "date": event_date, "_sequence": sequence, **details})

    def add_encounter(row: Mapping[str, Any], event: str, event_date: str, repeat_index: int | None = None) -> None:
        occurrence = len(encounters) + 1
        encounters.append({
            "occurrence_id": f"{case_id}.ENCOUNTER.{occurrence:02d}",
            "encounter_id": row["encounter_id"],
            "event": event,
            "date": event_date,
            "repeat_index": repeat_index,
        })

    def add_document(row: Mapping[str, Any], event: str, event_date: str) -> None:
        for copy_index in range(1, row["copy_count"] + 1):
            occurrence = len(documents) + 1
            documents.append({
                "occurrence_id": f"{case_id}.DOCUMENT.{occurrence:02d}",
                "document_requirement_id": row["document_requirement_id"],
                "copy_index": copy_index,
                "event": event,
                "date": event_date,
            })

    def add_check(row: Mapping[str, Any], visit_index: int, event: str, event_date: str) -> None:
        occurrence = len(checklist) + 1
        checklist.append({
            "occurrence_id": f"{case_id}.CHECK.{occurrence:02d}",
            "checklist_item_id": row["checklist_item_id"],
            "visit_index": visit_index,
            "event": event,
            "date": event_date,
        })

    def add_fee(row: Mapping[str, Any], event: str, event_date: str, repeat_index: int | None = None) -> None:
        occurrence = len(fees) + 1
        fees.append({
            "occurrence_id": f"{case_id}.FEE.{occurrence:02d}",
            "charge_id": row["charge_id"],
            "canonical_charge_key": row["canonical_charge_key"],
            "amount": row["amount"],
            "currency": row["currency"],
            "event": event,
            "date": event_date,
            "repeat_index": repeat_index,
            "schedule_locked_at_event": "first_permit_submission",
            "schedule_locked_at_date": draws.arrival_date,
        })

    encounter_rows = list(structural_source["applicant_encounters"])
    document_rows = list(structural_source["required_documents"])
    checklist_rows = list(structural_source["checklist_items"])
    fee_rows = list(structural_source["fee_schedule"])
    encounter = lambda token: _index_by_suffix(encounter_rows, "encounter_id", f".ENC.{token}.{suffix}")
    document = lambda token: _index_by_suffix(document_rows, "document_requirement_id", f".DOC.{token}")
    check = lambda token: _index_by_suffix(checklist_rows, "checklist_item_id", f".CHK.{token}")
    fee = lambda token: _index_by_suffix(fee_rows, "charge_id", f".FEE.{token}")

    permit_base_fee = fee("PERMIT_BASE")
    if not permit_base_fee["effective_start"] <= draws.arrival_date <= permit_base_fee["effective_end"]:
        raise S07CaseMechanicsError("first permit submission is outside the reviewed fee schedule")

    design_duration = adjusted_duration(
        draws.durations["design_sign_to_submit"], phase_id="design_sign_to_submit", repeats=0,
    )
    contract_date = subtract_business_days(
        draws.arrival_date, design_duration["realized_business_days"]
    )
    add_event("customer_contract_signed", contract_date)
    add_event("design_complete", draws.arrival_date)
    add_event("first_permit_submission", draws.arrival_date)
    phases["design_sign_to_submit"] = _eventual_phase(
        "design_sign_to_submit", status="completed",
        start_event="customer_contract_signed", start_date=contract_date,
        end_event="first_permit_submission", end_date=draws.arrival_date,
        duration=design_duration, repeats=0,
    )
    add_encounter(encounter("PERMIT"), "first_permit_submission", draws.arrival_date)
    for token in ("SITE_PLAN", "ELECTRICAL", "EQUIPMENT"):
        add_document(document(token), "first_permit_submission", draws.arrival_date)
    if draws.technology == "pv_plus_storage":
        add_document(document("STORAGE"), "first_permit_submission", draws.arrival_date)
    add_fee(permit_base_fee, "first_permit_submission", draws.arrival_date)

    pre_duration = adjusted_duration(
        draws.durations["preinstall_ix"], phase_id="preinstall_ix",
        repeats=draws.repeat_counts["preinstall_ix"],
    )
    pre_start: str | None = None
    pre_end: str | None = None
    if route == "no_preinstall_approval":
        phases["preinstall_ix"] = _eventual_phase(
            "preinstall_ix", status="not_required", start_event=None,
            start_date=None, end_event=None, end_date=None, duration=None,
            repeats=0,
        )
    if route == "parallel_standard":
        pre_start = draws.arrival_date
        pre_end = _add_business_days(pre_start, pre_duration["realized_business_days"])
        add_event("preinstall_interconnection_submission", pre_start)
        add_encounter(encounter("PREIX"), "preinstall_interconnection_submission", pre_start)
        add_document(document("PREIX"), "preinstall_interconnection_submission", pre_start)
        add_fee(fee("PREIX"), "preinstall_interconnection_submission", pre_start)

    permit_repeats = draws.repeat_counts["ahj_permit"]
    permit_duration = adjusted_duration(
        draws.durations["ahj_permit"], phase_id="ahj_permit", repeats=permit_repeats,
    )
    permit_end = _add_business_days(
        draws.arrival_date, permit_duration["realized_business_days"]
    )
    permit_offsets = repeat_event_offsets(
        permit_duration["realized_business_days"], repeats=permit_repeats,
        events_per_repeat=2,
    )
    for repeat_index in range(1, permit_repeats + 1):
        request_date = _add_business_days(draws.arrival_date, permit_offsets[2 * repeat_index - 2])
        submit_date = _add_business_days(draws.arrival_date, permit_offsets[2 * repeat_index - 1])
        add_event("permit_correction_requested", request_date, repeat_index=repeat_index)
        add_event("corrected_permit_submission", submit_date, repeat_index=repeat_index)
        add_encounter(
            encounter("PERMIT_CORRECTION"), "corrected_permit_submission",
            submit_date, repeat_index,
        )
        add_fee(fee("PERMIT_REPEAT"), "corrected_permit_submission", submit_date, repeat_index)

    if route == "parallel_standard" and pre_end is not None and pre_end <= permit_end:
        add_event("preinstall_interconnection_approval", pre_end)
        phases["preinstall_ix"] = _eventual_phase(
            "preinstall_ix", status="completed", start_event="preinstall_interconnection_submission",
            start_date=pre_start, end_event="preinstall_interconnection_approval",
            end_date=pre_end, duration=pre_duration,
            repeats=draws.repeat_counts["preinstall_ix"],
        )

    if draws.denied:
        add_event("permit_denied", permit_end)
        phases["ahj_permit"] = _eventual_phase(
            "ahj_permit", status="denied", start_event="first_permit_submission",
            start_date=draws.arrival_date, end_event="permit_denied", end_date=permit_end,
            duration=permit_duration, repeats=permit_repeats,
        )
        if route == "parallel_standard" and "preinstall_ix" not in phases:
            phases["preinstall_ix"] = _eventual_phase(
                "preinstall_ix", status="canceled_due_to_permit_denial",
                start_event="preinstall_interconnection_submission", start_date=pre_start,
                end_event=None, end_date=None, duration=None,
                repeats=draws.repeat_counts["preinstall_ix"],
            )
        terminal_event = "permit_denied"
        terminal_date = permit_end
        outcome = "denied_or_ineligible"
    else:
        add_event("final_permit_approval", permit_end)
        phases["ahj_permit"] = _eventual_phase(
            "ahj_permit", status="completed", start_event="first_permit_submission",
            start_date=draws.arrival_date, end_event="final_permit_approval", end_date=permit_end,
            duration=permit_duration, repeats=permit_repeats,
        )
        if route == "parallel_standard" and "preinstall_ix" not in phases:
            assert pre_end is not None
            add_event("preinstall_interconnection_approval", pre_end)
            phases["preinstall_ix"] = _eventual_phase(
                "preinstall_ix", status="completed", start_event="preinstall_interconnection_submission",
                start_date=pre_start, end_event="preinstall_interconnection_approval",
                end_date=pre_end, duration=pre_duration,
                repeats=draws.repeat_counts["preinstall_ix"],
            )
        elif route == "serial_standard":
            pre_start = _add_business_days(permit_end, 1)
            pre_end = _add_business_days(pre_start, pre_duration["realized_business_days"])
            add_event("preinstall_interconnection_submission", pre_start)
            add_event("preinstall_interconnection_approval", pre_end)
            add_encounter(encounter("PREIX"), "preinstall_interconnection_submission", pre_start)
            add_document(document("PREIX"), "preinstall_interconnection_submission", pre_start)
            add_fee(fee("PREIX"), "preinstall_interconnection_submission", pre_start)
            phases["preinstall_ix"] = _eventual_phase(
                "preinstall_ix", status="completed", start_event="preinstall_interconnection_submission",
                start_date=pre_start, end_event="preinstall_interconnection_approval",
                end_date=pre_end, duration=pre_duration,
                repeats=draws.repeat_counts["preinstall_ix"],
            )
        approvals_end = max(permit_end, pre_end) if pre_end is not None else permit_end
        if draws.withdrawn:
            terminal_date = _add_business_days(approvals_end, 1)
            terminal_event = "application_withdrawn"
            add_event(terminal_event, terminal_date)
            outcome = "withdrawn"
        else:
            installation_start = _add_business_days(approvals_end, 1)
            add_event("installation_start", installation_start)
            add_encounter(encounter("INSTALL"), "installation_start", installation_start)
            installation_duration = adjusted_duration(
                draws.durations["installation"], phase_id="installation", repeats=0,
            )
            installation_end = _add_business_days(
                installation_start, installation_duration["realized_business_days"]
            )
            add_event("installation_complete", installation_end)
            phases["installation"] = _eventual_phase(
                "installation", status="completed", start_event="installation_start",
                start_date=installation_start, end_event="installation_complete",
                end_date=installation_end, duration=installation_duration, repeats=0,
            )
            if draws.abandoned:
                terminal_date = _add_business_days(installation_end, 1)
                terminal_event = "project_abandoned"
                add_event(terminal_event, terminal_date)
                outcome = "abandoned"
            else:
                inspection_start = _add_business_days(installation_end, 1)
                add_event("inspection_request", inspection_start)
                add_encounter(encounter("INSPECT"), "inspection_request", inspection_start)
                add_fee(fee("INSPECTION_INITIAL"), "inspection_request", inspection_start)
                inspection_repeats = draws.repeat_counts["ahj_inspection"]
                inspection_duration = adjusted_duration(
                    draws.durations["ahj_inspection"], phase_id="ahj_inspection",
                    repeats=inspection_repeats,
                )
                inspection_end = _add_business_days(
                    inspection_start, inspection_duration["realized_business_days"]
                )
                inspection_offsets = repeat_event_offsets(
                    inspection_duration["realized_business_days"], repeats=inspection_repeats,
                    events_per_repeat=3,
                )
                failed_visit_dates = []
                for repeat_index in range(1, inspection_repeats + 1):
                    base = 3 * repeat_index - 3
                    failed = _add_business_days(inspection_start, inspection_offsets[base])
                    corrected = _add_business_days(inspection_start, inspection_offsets[base + 1])
                    request = _add_business_days(inspection_start, inspection_offsets[base + 2])
                    failed_visit_dates.append(failed)
                    add_event("inspection_failed", failed, repeat_index=repeat_index)
                    add_event("inspection_correction_completed", corrected, repeat_index=repeat_index)
                    add_event("reinspection_request", request, repeat_index=repeat_index)
                    add_encounter(encounter("REINSPECTION"), "reinspection_request", request, repeat_index)
                    add_fee(fee("REINSPECTION"), "reinspection_request", request, repeat_index)
                add_event("final_passed_inspection", inspection_end)
                visit_dates = failed_visit_dates + [inspection_end]
                for visit_index, visit_date in enumerate(visit_dates, 1):
                    visit_event = "inspection_failed" if visit_index <= inspection_repeats else "final_passed_inspection"
                    add_check(check("CONFIGURATION"), visit_index, visit_event, visit_date)
                    add_check(check("LABELS"), visit_index, visit_event, visit_date)
                    if draws.technology == "pv_plus_storage":
                        add_check(check("STORAGE"), visit_index, visit_event, visit_date)
                add_check(check("PASS_RECORD"), len(visit_dates), "final_passed_inspection", inspection_end)
                phases["ahj_inspection"] = _eventual_phase(
                    "ahj_inspection", status="completed", start_event="inspection_request",
                    start_date=inspection_start, end_event="final_passed_inspection",
                    end_date=inspection_end, duration=inspection_duration,
                    repeats=inspection_repeats,
                )
                handoff_duration = adjusted_duration(
                    draws.durations["postinspection_handoff"],
                    phase_id="postinspection_handoff", repeats=0,
                )
                final_request = _add_business_days(
                    inspection_end, handoff_duration["realized_business_days"]
                )
                add_event("final_interconnection_request", final_request)
                add_encounter(encounter("FINALIX"), "final_interconnection_request", final_request)
                add_document(document("PASS"), "final_interconnection_request", final_request)
                add_fee(fee("FINAL_PTO"), "final_interconnection_request", final_request)
                phases["postinspection_handoff"] = _eventual_phase(
                    "postinspection_handoff", status="completed",
                    start_event="final_passed_inspection", start_date=inspection_end,
                    end_event="final_interconnection_request", end_date=final_request,
                    duration=handoff_duration, repeats=0,
                )
                final_repeats = draws.repeat_counts["final_ix_to_pto"]
                final_duration = adjusted_duration(
                    draws.durations["final_ix_to_pto"], phase_id="final_ix_to_pto",
                    repeats=final_repeats,
                )
                pto_date = _add_business_days(
                    final_request, final_duration["realized_business_days"]
                )
                add_event("permission_to_operate_granted", pto_date)
                phases["final_ix_to_pto"] = _eventual_phase(
                    "final_ix_to_pto", status="completed",
                    start_event="final_interconnection_request", start_date=final_request,
                    end_event="permission_to_operate_granted", end_date=pto_date,
                    duration=final_duration, repeats=final_repeats,
                )
                terminal_event = "permission_to_operate_granted"
                terminal_date = pto_date
                outcome = "pto_completed"

    for phase_id in (
        "installation", "ahj_inspection", "postinspection_handoff", "final_ix_to_pto",
    ):
        if phase_id not in phases:
            phases[phase_id] = _eventual_phase(
                phase_id, status="not_started_due_to_outcome", start_event=None,
                start_date=None, end_event=None, end_date=None, duration=None, repeats=0,
            )
    if "preinstall_ix" not in phases:
        phases["preinstall_ix"] = _eventual_phase(
            "preinstall_ix", status="not_started_due_to_outcome", start_event=None,
            start_date=None, end_event=None, end_date=None, duration=None,
            repeats=0,
        )

    events.sort(key=lambda item: (item["date"], item["_sequence"]))
    for ordinal, event in enumerate(events, 1):
        event["ordinal"] = ordinal
        del event["_sequence"]
    observed_events = [event for event in events if event["date"] < as_of]
    observed_state = "pending_at_cutoff"
    if terminal_date < as_of:
        observed_state = {
            "pto_completed": "completed",
            "denied_or_ineligible": "denied",
            "withdrawn": "withdrawn",
            "abandoned": "abandoned",
        }[outcome]

    def observed_occurrences(rows: list[dict]) -> list[dict]:
        return [row for row in rows if row["date"] < as_of]

    membership_candidates = []
    for phase_id in PUBLIC_PHASES:
        phase = phases[phase_id]
        owner_type = PHASE_CONTRACTS[phase_id][0]
        membership_candidates.append({
            "membership_candidate_id": f"{case_id}.MEMBER.{phase_id}",
            "case_id": case_id,
            "phase_id": phase_id,
            "owner_type": owner_type,
            "owner_id": jid if owner_type == "ahj" else structural_source["utility_id"],
            "technology": draws.technology,
            "size_band": draws.size_band,
            "route": route,
            "phase_status": phase["status"],
            "completed_by_cutoff": (
                phase["status"] == "completed"
                and phase["end_date"] is not None
                and phase["end_date"] < as_of
            ),
        })

    total_fee = sum(row["amount"] for row in fees)
    observed_fees = observed_occurrences(fees)
    return {
        "schema_version": "s07-private-case-mechanics/1",
        "case_id": case_id,
        "same_case_group": f"s07-case:{case_id}",
        "jurisdiction_id": jid,
        "utility_id": structural_source["utility_id"],
        "profile_id": config.profile_id,
        "arrival_date": draws.arrival_date,
        "technology": draws.technology,
        "size_band": draws.size_band,
        "route": route,
        "automatic_permit": draws.automatic_permit,
        "private_draw_provenance": {
            "duration_draws": {
                key: {
                    "raw_business_days": draw.raw_business_days,
                    "rounded_business_days": draw.rounded_business_days,
                }
                for key, draw in sorted(draws.durations.items())
            },
            "repeat_count_draws": dict(sorted(draws.repeat_counts.items())),
            "stage_outcome_draws": {
                "denied_at_permit_review_end": draws.denied,
                "withdrawn_after_required_approvals": draws.withdrawn,
                "abandoned_after_installation": draws.abandoned,
            },
            "qualification": "downstream draws remain private even when an earlier stopping outcome prevents their realization",
        },
        "fee_schedule_lock": {
            "event": "first_permit_submission",
            "date": draws.arrival_date,
        },
        "events": events,
        "phases": phases,
        "latent_eventual_outcome": outcome,
        "terminal_event": terminal_event,
        "terminal_date": terminal_date,
        "observed_cutoff": {
            "as_of": as_of,
            "state": observed_state,
            "events": observed_events,
            "encounters": observed_occurrences(encounters),
            "documents": observed_occurrences(documents),
            "checklist_actions": observed_occurrences(checklist),
            "fees": observed_fees,
            "fee_total": sum(row["amount"] for row in observed_fees),
        },
        "realized_burden": {
            "encounters": encounters,
            "documents": documents,
            "checklist_actions": checklist,
            "fees": fees,
            "counts": {
                "encounters": len(encounters),
                "document_copies": len(documents),
                "checklist_actions": len(checklist),
                "fee_occurrences": len(fees),
            },
            "fee_total": total_fee,
            "fee_currency": "USD",
            "channels_must_not_be_summed": True,
        },
        "private_membership_provenance": {
            "basis": "full_base_case_phase_membership_before_any_reporting_transform",
            "base_membership_candidates": membership_candidates,
            "derived_reporting_memberships": [],
            "derived_memberships_constructed_here": False,
            "private_audit_only": True,
            "permitted_blind_input": False,
        },
        "dependence_qualification": {
            "independent_of_other_evidence": None,
            "rule": "exact overlap or unknown membership cannot assert independence; no joint case-plus-cohort factor is constructed here",
            "public_membership_leakage_permitted": False,
            "private_membership_may_drive_blind_admission_or_weights": False,
        },
    }


def generate_case(
    config: CaseMechanicsConfig,
    structural_source: Mapping[str, Any],
    structural_design: Mapping[str, Any],
    *,
    seed: int,
    case_index: int,
) -> dict[str, Any]:
    """Draw and build one in-memory case; performs no filesystem writes."""
    jid = structural_source.get("jurisdiction_id")
    if not isinstance(jid, str) or not jid:
        raise S07CaseMechanicsError("structural source lacks jurisdiction_id")
    draws = draw_case_inputs(
        config, seed=seed, jurisdiction_id=jid, case_index=case_index,
    )
    return build_case_from_draws(
        config, structural_source, structural_design,
        case_index=case_index, draws=draws,
    )


__all__ = [
    "CaseDraws", "CaseMechanicsConfig", "DurationDraw", "DurationSpec",
    "S07CaseMechanicsError", "adjusted_duration", "build_case_from_draws",
    "choose_route", "draw_case_inputs", "generate_case",
    "repeat_event_offsets", "subtract_business_days", "validate_mechanics_config",
]
