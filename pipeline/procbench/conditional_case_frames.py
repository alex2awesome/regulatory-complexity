"""Strict admission contract for finite, artifact-defined reported-case frames.

This module does not inspect sources, certify semantic review, or change a
likelihood.  It only validates that a deliberately narrow V6 run is conditioned
on exactly the cases named by a complete, hash-bound registry ledger.
"""
from __future__ import annotations

import hashlib
import json
import math


SCHEMA_VERSION = "declared-conditional-case-frame/1"
CENSORED_SCHEMA_VERSION = "declared-conditional-case-frame/2"
TERMINAL_NEUTRAL_SCHEMA_VERSION = "declared-conditional-case-frame/3"
LEDGER_SCHEMA_VERSION = "conditional-case-frame-ledger/1"
SAMPLING_KIND = "census_within_declared_conditional_frame"


def _exact_fields(value: object, required: set[str], optional: set[str], kind: str) -> dict:
    """Reject schema drift before permissive downstream dataclass parsing.

    Conditional-frame mode is intentionally much narrower than the ordinary V6
    input language.  In particular, an otherwise valid V6 field must not be
    silently accepted when it would change the meaning of this one-phase case
    frame.
    """
    if not isinstance(value, dict):
        raise ValueError(f"Conditional-frame {kind} must be an object")
    fields = set(value)
    missing = required - fields
    extras = fields - required - optional
    if missing or extras:
        raise ValueError(
            f"Conditional-frame {kind} requires bounded fields; "
            f"missing={sorted(missing)!r}, extras={sorted(extras)!r}")
    return value


def canonical_sha256(value: object) -> str:
    """Digest one JSON value under an explicit, cross-run canonical encoding."""
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Conditional-frame ledger must be finite canonical JSON") from exc
    return hashlib.sha256(raw).hexdigest()


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"Conditional frame requires nonempty canonical {field}")
    return value


def _validate_frame(raw: object) -> dict:
    required = {"schema_version", "id", "target", "source_family", "eligibility",
                "generalization_limit", "registry_label_denominator",
                "included_case_ids", "ledger", "ledger_sha256"}
    if not isinstance(raw, dict):
        raise ValueError("Conditional frame declaration must be an object")
    version = raw.get("schema_version")
    lower_bound_versions = {CENSORED_SCHEMA_VERSION, TERMINAL_NEUTRAL_SCHEMA_VERSION}
    if (not isinstance(version, str)
            or version not in {SCHEMA_VERSION, *lower_bound_versions}):
        raise ValueError("Unknown conditional-case-frame schema")
    if version in lower_bound_versions:
        required.add("coarsening_assumption")
    if set(raw) != required:
        raise ValueError("Conditional frame requires the exact declared version's fields")
    if version in lower_bound_versions:
        assumption = _exact_fields(raw["coarsening_assumption"],
            {"kind", "rationale", "sensitivity_plan", "informative_posting_unmodeled"},
            set(), "coarsening assumption")
        if (assumption["kind"] != "assumed_ignorable_within_report_frame"
                or assumption["informative_posting_unmodeled"] is not True):
            raise ValueError("Censored report frames must explicitly assume ignorable coarsening and disclose unmodeled informative posting")
        for field in ("rationale", "sensitivity_plan"):
            _text(assumption[field], field)
    frame_id = _text(raw["id"], "id")
    for field in ("target", "source_family", "eligibility", "generalization_limit"):
        _text(raw[field], field)
    denominator = raw["registry_label_denominator"]
    if (isinstance(denominator, bool) or not isinstance(denominator, int)
            or denominator < 1):
        raise ValueError("Conditional frame requires a positive registry-label denominator")
    cases = raw["included_case_ids"]
    if (not isinstance(cases, list) or not cases
            or any(not isinstance(case, str) or not case.strip() or case != case.strip()
                   for case in cases)
            or len(cases) != len(set(cases))):
        raise ValueError("Conditional frame requires distinct nonempty included case IDs")
    ledger = raw["ledger"]
    if (not isinstance(ledger, dict)
            or set(ledger) != {"schema_version", "rows"}
            or ledger["schema_version"] != LEDGER_SCHEMA_VERSION
            or not isinstance(ledger["rows"], list)):
        raise ValueError("Conditional frame requires one embedded version-1 registry ledger")
    declared_digest = raw["ledger_sha256"]
    if (not isinstance(declared_digest, str) or len(declared_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in declared_digest)):
        raise ValueError("Conditional frame requires a lowercase SHA-256 ledger digest")
    actual_digest = canonical_sha256(ledger)
    if declared_digest != actual_digest:
        raise ValueError("Conditional-frame ledger digest does not match canonical embedded rows")
    rows = ledger["rows"]
    if len(rows) != denominator:
        raise ValueError("Conditional-frame ledger must contain every denominator registry label")
    labels, included, excluded = set(), [], 0
    row_fields = {"registry_label_id", "status", "case_id", "reason"}
    for row in rows:
        if not isinstance(row, dict) or set(row) != row_fields:
            raise ValueError("Conditional-frame ledger rows require exact label/status/case/reason fields")
        label = _text(row["registry_label_id"], "registry_label_id")
        reason = _text(row["reason"], "ledger reason")
        if label in labels:
            raise ValueError("Conditional-frame registry label IDs must be distinct")
        labels.add(label)
        if row["status"] == "included":
            case = row["case_id"]
            if not isinstance(case, str) or not case.strip() or case != case.strip():
                raise ValueError("Every included registry row requires one canonical case ID")
            included.append(case)
        elif row["status"] == "excluded":
            if row["case_id"] is not None:
                raise ValueError("Excluded conditional-frame rows cannot name a modeled case")
            excluded += 1
        else:
            raise ValueError("Conditional-frame registry status must be included or excluded")
    if len(included) != len(set(included)) or set(included) != set(cases):
        raise ValueError("Conditional-frame ledger cases must exactly equal included_case_ids")
    result = dict(schema_version=version, id=frame_id, target=raw["target"],
        source_family=raw["source_family"], eligibility=raw["eligibility"],
        generalization_limit=raw["generalization_limit"],
        registry_label_denominator=denominator, included_case_ids=list(cases),
        included_case_count=len(cases), excluded_registry_label_count=excluded,
        ledger_sha256=actual_digest,
        binding_qualification=("Canonical hashing proves binding to the embedded registry ledger; "
            "it does not prove source accuracy, complete retrieval, semantic review, or representativeness."),
        distribution_qualification=("Conditional report-frame distribution of the named completed histories only; "
            "not an unselected applicant population, agency-only delay, intrinsic agency speed, or a universal process dependency."),
        offset_qualification=("The single source-family offset is fixed at zero solely as a report-frame convention; "
            "this is not evidence of unbiased reporting or learned source reliability."))
    if version in lower_bound_versions:
        result.update(coarsening_assumption=dict(raw["coarsening_assumption"]),
            distribution_qualification=("Conditional report-frame time-to-event distribution of the named "
                "completed and/or pending histories under explicitly assumed ignorable report coarsening. "
                "A pending lower bound is not a completed duration. Informative posting/censoring may bias this "
                "distribution; it is not an unselected applicant population or intrinsic agency speed."))
    if version == TERMINAL_NEUTRAL_SCHEMA_VERSION:
        result["distribution_qualification"] = (
            "Conditional report-frame time-to-event distribution of the named completed, pending, and/or "
            "terminal-neutral elapsed histories under explicitly assumed ignorable report coarsening. "
            "A terminal-neutral lower bound asserts elapsed time only: it does not assert that the endpoint "
            "was observed or still pending. Informative posting/coarsening may bias this distribution; it is "
            "not an unselected applicant population or intrinsic agency speed.")
    return result


def validate_conditional_case_frames(data: object, cfg: object) -> dict[str, dict]:
    """Validate and summarize the optional bounded conditional-frame mode.

    With no declaration this returns an empty mapping and deliberately performs
    no policy checks, preserving the historical data contract and parameterization.
    """
    if not isinstance(data, dict):
        raise ValueError("V6 data must be an object")
    declarations = data.get("conditional_case_frames")
    if declarations is None:
        if any("conditional_frame_id" in program for program in data.get("programs", [])):
            raise ValueError("A program conditional_frame_id requires a top-level declaration")
        return {}
    if not isinstance(declarations, list) or not declarations:
        raise ValueError("conditional_case_frames must be a nonempty list")
    frames = [_validate_frame(raw) for raw in declarations]
    if len({frame["id"] for frame in frames}) != len(frames):
        raise ValueError("Conditional-frame IDs must be distinct")
    programs = data.get("programs")
    if not isinstance(programs, list) or len(programs) != 1 or len(frames) != 1:
        raise ValueError("Conditional-case-frame mode is bounded to exactly one program and one frame")
    raw_program = programs[0]
    frame = frames[0]
    _exact_fields(raw_program,
        {"id", "conditional_frame_id", "inventory_granularity", "clock_estimand",
         "routes", "observations"},
        {"time_unit", "rate_observations", "quantile_cohorts", "histogram_cohorts",
         "case_path_scope"}, "program")
    _text(raw_program["id"], "program id")
    if raw_program.get("conditional_frame_id") != frame["id"]:
        raise ValueError("Program conditional_frame_id must exactly bind the declared frame")
    if raw_program.get("inventory_granularity") != "aggregate_phases":
        raise ValueError("Conditional-case-frame mode requires one declared aggregate phase")
    if not isinstance(raw_program.get("clock_estimand"), str) or not raw_program["clock_estimand"].strip():
        raise ValueError("Conditional-case-frame mode requires an explicit clock estimand")
    if raw_program["clock_estimand"] != frame["target"]:
        raise ValueError("Conditional-frame target must exactly equal the program clock_estimand")
    if raw_program.get("rate_observations", []) or raw_program.get("quantile_cohorts", []) or raw_program.get("histogram_cohorts", []):
        raise ValueError("Conditional-case-frame mode forbids rates and cohort summaries")
    if raw_program.get("case_path_scope"):
        raise ValueError("Conditional-case-frame mode forbids case paths")
    routes = raw_program.get("routes")
    if not isinstance(routes, list) or len(routes) != 1:
        raise ValueError("Conditional-case-frame mode requires exactly one route")
    route = routes[0]
    _exact_fields(route, {"id", "prior_weight", "operations", "blocks"}, set(), "route")
    _text(route["id"], "route id")
    weight = route["prior_weight"]
    if (isinstance(weight, bool) or not isinstance(weight, (int, float))
            or not math.isfinite(weight) or weight != 1.0):
        raise ValueError("Conditional-case-frame single route requires prior_weight=1.0")
    operations, blocks = route.get("operations"), route.get("blocks")
    if not isinstance(operations, list) or len(operations) != 1 or not isinstance(blocks, list) or len(blocks) != 1:
        raise ValueError("Conditional-case-frame mode requires one operation in one block")
    operation, block = operations[0], blocks[0]
    _exact_fields(operation,
        {"id", "actor_id", "actor_role", "task_type", "markers", "payer_work",
         "agency_work"}, set(), "operation")
    _exact_fields(block, {"id", "operations"}, set(), "block")
    _text(operation["id"], "operation id")
    _text(operation["task_type"], "operation task_type")
    _text(block["id"], "block id")
    if (operation.get("actor_id") is not None or operation.get("actor_role") != "unknown"
            or operation.get("markers") != []
            or operation.get("payer_work") is not False or operation.get("agency_work") is not False):
        raise ValueError("Conditional phase must be mixed-actor/unknown with no decision markers or implied labor")
    if block.get("operations") != [operation.get("id")]:
        raise ValueError("Conditional phase block cannot repeat, branch, or declare dwell")
    observations = raw_program.get("observations")
    if not isinstance(observations, list) or len(observations) != len(frame["included_case_ids"]):
        raise ValueError("Conditional frame requires exactly one observation per included case")
    seen_cases = []
    sources = set()
    lower_bound_version = frame["schema_version"] in {
        CENSORED_SCHEMA_VERSION, TERMINAL_NEUTRAL_SCHEMA_VERSION}
    terminal_neutral_version = frame["schema_version"] == TERMINAL_NEUTRAL_SCHEMA_VERSION
    kind_counts = dict(completed_interval=0, completed_lower_bound=0, pending_right_censored=0)
    if terminal_neutral_version:
        kind_counts["terminal_neutral_lower_bound"] = 0
    for observation in observations:
        observation_fields = {"id", "case_id", "source_family", "sampling", "statistic", "lower",
                              "upper", "operators", "operator_weights", "provenance"}
        if lower_bound_version:
            observation_fields.add("observation_kind")
        _exact_fields(observation,
            observation_fields,
            {"time_unit"}, "observation")
        _text(observation["id"], "observation id")
        case = observation.get("case_id")
        if (observation.get("sampling") != SAMPLING_KIND
                or observation.get("statistic") != "individual"
                or not isinstance(case, str) or not case.strip() or case != case.strip()):
            raise ValueError("Conditional-frame rows must be case-linked individual clocks with the explicit sampling kind")
        _text(observation["source_family"], "observation source_family")
        seen_cases.append(case)
        sources.add(observation.get("source_family"))
        lower, upper = observation["lower"], observation["upper"]
        finite_lower = (not isinstance(lower, bool) and isinstance(lower, (int, float))
                        and math.isfinite(lower) and lower >= 0)
        finite_interval = (finite_lower and not isinstance(upper, bool)
                           and isinstance(upper, (int, float)) and math.isfinite(upper)
                           and upper > lower)
        if not lower_bound_version and not finite_interval:
            raise ValueError("Conditional completed histories require one finite nonempty elapsed interval")
        if lower_bound_version:
            kind = observation["observation_kind"]
            if not isinstance(kind, str) or kind not in kind_counts:
                raise ValueError("Conditional observation_kind is not admitted by the declared frame schema")
            if kind == "completed_interval":
                if not finite_interval:
                    raise ValueError("Completed intervals require finite nonempty elapsed bounds")
            elif not finite_lower or lower <= 0 or upper is not None:
                raise ValueError("Lower-bound observation kinds require positive finite lower and null upper")
            kind_counts[kind] += 1
        operators, weights = observation.get("operators"), observation.get("operator_weights")
        if (not isinstance(operators, list) or len(operators) != 1
                or not isinstance(weights, list) or len(weights) != 1
                or isinstance(weights[0], bool) or not isinstance(weights[0], (int, float))
                or not math.isfinite(weights[0]) or weights[0] != 1.0
                or not isinstance(operators[0], dict)):
            raise ValueError("Conditional-frame rows must observe the one coarse phase directly")
        _exact_fields(operators[0], {"basis", "activity_ids"}, set(), "operator")
        if (operators[0].get("basis") != "single_visit_cycle"
                or operators[0].get("activity_ids") != [operation.get("id")]):
            raise ValueError("Conditional-frame rows must observe the one coarse phase directly")
        provenance = observation["provenance"]
        _exact_fields(provenance,
            {"clock_id", "evidence_cell_ids", "date_resolution_rule"}, set(),
            "observation provenance")
        evidence = provenance["evidence_cell_ids"]
        if (provenance["clock_id"] != observation["id"]
                or not isinstance(evidence, list) or not evidence
                or any(not isinstance(item, str) or not item.strip() or item != item.strip()
                       for item in evidence)
                or len(evidence) != len(set(evidence))):
            raise ValueError("Conditional observation provenance must bind its clock and distinct evidence cells")
        _text(provenance["date_resolution_rule"], "date_resolution_rule")
    if len(seen_cases) != len(set(seen_cases)) or set(seen_cases) != set(frame["included_case_ids"]):
        raise ValueError("Program cases must exactly equal the conditional-frame case registry")
    if sources != {frame["source_family"]}:
        raise ValueError("Conditional-case-frame mode requires exactly its declared source family")
    if lower_bound_version:
        frame.update(observation_kind_counts=kind_counts,
            all_observations_lower_bounds=(kind_counts["completed_interval"] == 0),
            censoring_qualification=("Lower bounds use the existing report survival probability, not a point "
                "duration. Report noise/contamination remain explicit assumptions. With only lower bounds, "
                "the upper tail and finite location estimates depend on the prior; no typical-duration headline is supported."))
    if terminal_neutral_version:
        frame["censoring_qualification"] = (
            "Every null-upper row uses the existing report survival probability, not a point duration. "
            "terminal_neutral_lower_bound makes no completed-versus-pending assertion. Report noise and "
            "contamination remain explicit assumptions. With only lower bounds, the upper tail and finite "
            "location estimates depend on the prior; no typical-duration headline is supported.")
    forbidden_top_level = ("source_offset_hierarchy", "source_comparisons")
    if any(data.get(field) is not None for field in forbidden_top_level):
        raise ValueError("Conditional-case-frame mode forbids source hierarchy/comparison declarations")
    required_config = dict(population_integration="qmc", modeled_channels=("elapsed",),
        agency_sd=0.0, task_sd=0.0, operation_sd=0.0, common_case_sd=0.0,
        source_sd=0.0, selection_sd=0.0, within_visit_phases=False,
        inter_operation_dwell=False, hierarchy_sampler="blocked")
    for field, expected in required_config.items():
        actual = getattr(cfg, field)
        if actual != expected:
            raise ValueError(f"Conditional-case-frame mode requires {field}={expected!r}")
    if getattr(cfg, "elapsed_task_prior_medians"):
        raise ValueError("Conditional-case-frame mode forbids task-specific timing priors")
    # The ordinary report kernel remains unchanged; these checks only guarantee
    # the offsets/selection and unsupported hierarchy components are inert.
    if not math.isfinite(getattr(cfg, "report_sd")) or getattr(cfg, "report_sd") <= 0:
        raise ValueError("Conditional-case-frame mode requires finite positive report noise")
    return {raw_program["id"]: frame}
