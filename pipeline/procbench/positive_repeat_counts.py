"""Count-only likelihood contract for completed positive repeat reports.

This module deliberately does not attach a reported count to a route block or
``CompactTrace``.  It validates a bounded, count-only input and evaluates the
normalized geometric law conditional on at least one additional round.  The
hurdle probability therefore does not appear here.

``validate_positive_repeat_counts`` returns a new self-describing dictionary::

    {
        "schema_version": "positive-repeat-count-observations/1",
        "rows": [... deep-copied input rows ...],
        "families": [... deterministic family summaries ...],
    }

Source bindings are structurally validated but not opened by this pure module;
an orchestrator remains responsible for verifying their bytes.
"""
from __future__ import annotations

import copy
import math
from numbers import Real


SCHEMA_VERSION = "positive-repeat-count-observations/1"
ASCERTAINMENT = "completed_positive_episode"
ATTACHMENT = "count_only"

ROW_FIELDS = {
    "id",
    "family_id",
    "family_definition",
    "attachment",
    "count",
    "case_id",
    "evidence_group_id",
    "source_family",
    "episode_complete",
    "exact_count_assumption",
    "ascertainment",
    "reporting_assumption",
    "source_bound",
    "severity_selection",
}
SOURCE_FIELDS = {"path", "sha256", "quote_segments"}
SEVERITY_FIELDS = {
    "id",
    "threshold",
    "log_tilt",
    "fixed_not_estimated",
}
FORBIDDEN_OPTIONS = {
    "sampling",
    "delay_selected",
    "duration_selected",
    "selection_sd",
    "report_error",
    "report_error_scale",
    "count_error_scale",
    "contamination",
    "lower",
    "upper",
    "operator",
    "operators",
    "operator_weights",
    "repeat_key",
}


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"Positive repeat count requires canonical nonempty {field}")
    return value


def _canonical_names(values: object, field: str) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field} must be an iterable of canonical names")
    try:
        names = list(values)
    except TypeError as exc:
        raise ValueError(f"{field} must be an iterable of canonical names") from exc
    output = {_canonical_text(value, field) for value in names}
    if len(output) != len(names):
        raise ValueError(f"{field} must not contain duplicate names")
    return output


def _integer(value: object, field: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _real(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite real number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite real number")
    return result


def _logaddexp(left: float, right: float) -> float:
    """Two-term log-sum-exp without overflowing at very large finite tilts."""
    if left == -math.inf:
        return right
    if right == -math.inf:
        return left
    high, low = (left, right) if left >= right else (right, left)
    return high + math.log1p(math.exp(low - high))


def _log_one_minus_exp(log_probability: float) -> float:
    """Stable log(1-exp(x)) for x<=0, including the probability-one edge."""
    if log_probability == 0.0:
        return -math.inf
    if log_probability < -math.log(2.0):
        return math.log1p(-math.exp(log_probability))
    return math.log(-math.expm1(log_probability))


def log_probability(
    k: int,
    r: float,
    log_severity_tilt: float = 0.0,
    severity_threshold: int = 3,
) -> float:
    """Log P(K=k | K>=1) under an optional fixed severity-report tilt.

    The unselected positive law is ``(1-r) r**(k-1)``.  A fixed reporting
    weight ``exp(lambda * 1[k>=t])`` has positive-frame normalizer
    ``1 + (exp(lambda)-1) r**(t-1)``.  The implementation works in log space
    and avoids ``exp(lambda)`` so large finite nonnegative tilts remain valid.

    ``r=0`` is a point mass at K=1.  At ``r=1`` every finite K has probability
    zero, so the result is ``-inf``.  No clipping changes either boundary.
    """
    k = _integer(k, "k", 1)
    threshold = _integer(severity_threshold, "severity_threshold", 1)
    r = _real(r, "r")
    tilt = _real(log_severity_tilt, "log_severity_tilt")
    if not 0.0 <= r <= 1.0:
        raise ValueError("r must be in [0,1]")
    if tilt < 0.0:
        raise ValueError("log_severity_tilt must be nonnegative")

    if r == 1.0:
        return -math.inf
    if r == 0.0:
        base = 0.0 if k == 1 else -math.inf
        log_tail = 0.0 if threshold == 1 else -math.inf
    else:
        base = math.log1p(-r) + (k - 1) * math.log(r)
        log_tail = (threshold - 1) * math.log(r)
    if base == -math.inf:
        return base

    # Tail is P(K>=threshold | K>=1).  For threshold one, every count is in
    # the severe category and the fixed tilt cancels exactly.
    log_rest = _log_one_minus_exp(log_tail)
    if k >= threshold:
        # lambda-logaddexp(log(rest),lambda+log(tail)), rewritten to avoid a
        # destructive lambda-lambda subtraction when lambda is very large.
        selection_correction = -_logaddexp(log_rest - tilt, log_tail)
    else:
        selection_correction = -_logaddexp(log_rest, tilt + log_tail)
    return base + selection_correction


def _validate_source_bound(raw: object) -> list[dict]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("Positive repeat count requires nonempty source_bound refs")
    output = []
    identities = set()
    for source in raw:
        if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
            raise ValueError("Each source_bound ref requires exact path/sha256/quote_segments fields")
        path = _canonical_text(source["path"], "source path")
        digest = source["sha256"]
        if (not isinstance(digest, str) or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)):
            raise ValueError("Source binding requires a lowercase SHA-256 digest")
        quotes = source["quote_segments"]
        if (not isinstance(quotes, list) or not quotes
                or any(not isinstance(quote, str) or not quote
                       for quote in quotes)):
            raise ValueError("Source binding requires nonempty literal quote segments")
        identity = (path, digest, tuple(quotes))
        if identity in identities:
            raise ValueError("Duplicate source_bound refs are not allowed")
        identities.add(identity)
        output.append(copy.deepcopy(source))
    return output


def _validate_severity(raw: object) -> dict:
    if not isinstance(raw, dict) or set(raw) != SEVERITY_FIELDS:
        raise ValueError("Fixed severity declaration requires exact id/threshold/log_tilt/fixed_not_estimated fields")
    result = copy.deepcopy(raw)
    result["id"] = _canonical_text(raw["id"], "severity declaration id")
    result["threshold"] = _integer(raw["threshold"], "severity threshold", 1)
    result["log_tilt"] = _real(raw["log_tilt"], "severity log tilt")
    if result["log_tilt"] < 0.0:
        raise ValueError("Severity log tilt must be nonnegative")
    if raw["fixed_not_estimated"] is not True:
        raise ValueError("Severity selection must be fixed and not estimated")
    return result


def validate_positive_repeat_counts(
    raw_rows: object,
    repeat_keys: object,
    other_cases: object,
    other_groups: object,
) -> dict:
    """Validate count-only rows and return deep-copied rows/family summaries.

    ``repeat_keys`` are executable CompactTrace repeat keys.  A count-only
    family is required to be disjoint from them.  ``other_cases`` and
    ``other_groups`` are the complete case and evidence-group identities used
    by every other likelihood factor in the containing program.  They prevent
    multiplication of dependent evidence under this deliberately narrow v1
    contract.

    Within a family this first implementation requires the same definition,
    source family, reporting assumption, and fixed severity declaration.  This
    is a bounded provenance/selection-frame rule, not evidence that sources are
    representative or independent.
    """
    executable = _canonical_names(repeat_keys, "repeat_keys")
    occupied_cases = _canonical_names(other_cases, "other_cases")
    occupied_groups = _canonical_names(other_groups, "other_groups")
    if not isinstance(raw_rows, list):
        raise ValueError("positive_repeat_count_observations must be a list")

    rows = []
    seen_ids: set[str] = set()
    seen_cases: set[str] = set()
    seen_groups: set[str] = set()
    family_contracts: dict[str, tuple] = {}
    family_rows: dict[str, list[dict]] = {}
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ValueError("Positive repeat count rows must be objects")
        extras = set(raw) - ROW_FIELDS
        forbidden = extras & FORBIDDEN_OPTIONS
        if forbidden:
            raise ValueError(f"Positive repeat count forbids selection/report-error options: {sorted(forbidden)!r}")
        missing = ROW_FIELDS - set(raw)
        if missing or extras:
            raise ValueError(
                "Positive repeat count row requires bounded fields; "
                f"missing={sorted(missing)!r}, extras={sorted(extras)!r}")

        row_id = _canonical_text(raw["id"], "row id")
        family_id = _canonical_text(raw["family_id"], "family id")
        family_definition = _canonical_text(raw["family_definition"], "family definition")
        case_id = _canonical_text(raw["case_id"], "case id")
        group_id = _canonical_text(raw["evidence_group_id"], "evidence group id")
        source_family = _canonical_text(raw["source_family"], "source family")
        reporting = _canonical_text(raw["reporting_assumption"], "reporting assumption")
        count = _integer(raw["count"], "count", 1)
        if raw["attachment"] != ATTACHMENT:
            raise ValueError("Positive repeat count attachment must be count_only")
        if family_id in executable:
            raise ValueError("Count-only family must not match an executable repeat key")
        if raw["episode_complete"] is not True or raw["exact_count_assumption"] is not True:
            raise ValueError("Positive repeat count requires completed and exact flags")
        if raw["ascertainment"] != ASCERTAINMENT:
            raise ValueError("Positive repeat count requires completed_positive_episode ascertainment")
        if row_id in seen_ids:
            raise ValueError("Positive repeat count row IDs must be distinct")
        if case_id in seen_cases or case_id in occupied_cases:
            raise ValueError("Positive repeat count case overlaps another likelihood factor")
        if group_id in seen_groups or group_id in occupied_groups:
            raise ValueError("Positive repeat count evidence group overlaps another likelihood factor")

        source_bound = _validate_source_bound(raw["source_bound"])
        severity = _validate_severity(raw["severity_selection"])
        contract = (
            family_definition,
            source_family,
            reporting,
            severity["id"],
            severity["threshold"],
            severity["log_tilt"],
        )
        if family_id in family_contracts and family_contracts[family_id] != contract:
            raise ValueError("Rows in one count-only family must share definition and provenance contract")
        family_contracts.setdefault(family_id, contract)

        row = copy.deepcopy(raw)
        row.update(
            id=row_id,
            family_id=family_id,
            family_definition=family_definition,
            count=count,
            case_id=case_id,
            evidence_group_id=group_id,
            source_family=source_family,
            reporting_assumption=reporting,
            source_bound=source_bound,
            severity_selection=severity,
        )
        rows.append(row)
        family_rows.setdefault(family_id, []).append(row)
        seen_ids.add(row_id)
        seen_cases.add(case_id)
        seen_groups.add(group_id)

    families = []
    for family_id in sorted(family_rows):
        members = family_rows[family_id]
        first = members[0]
        families.append({
            "id": family_id,
            "attachment": ATTACHMENT,
            "definition": first["family_definition"],
            "source_family": first["source_family"],
            "reporting_assumption": first["reporting_assumption"],
            "severity_selection": copy.deepcopy(first["severity_selection"]),
            "row_ids": [row["id"] for row in members],
            "case_ids": [row["case_id"] for row in members],
            "evidence_group_ids": [row["evidence_group_id"] for row in members],
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": rows,
        "families": families,
    }
