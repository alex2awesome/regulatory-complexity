"""Prepare and fit adopted bulk-forum clocks with the existing marginal V6 model.

The unit of analysis is a contributor/clock/unit report, conditional on appearing
in the adopted forum packet.  Clock/unit frames are fit separately: their
likelihoods must not be multiplied to reconstruct a whole-process duration.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

from ..bayes_trace_hierarchy import Config, VisitHierarchy
from ..conditional_case_frames import canonical_sha256
from ..marginal_conditional_frames import MarginalConditionalFrame, run_marginal_frame


ROOT = Path(__file__).resolve().parents[3]
KINDS = {"completed_interval", "completed_lower_bound", "pending_right_censored"}
UNITS = {"calendar_days", "business_days"}
GEOGRAPHY_SCOPES = {
    "california_supported_by_parser",
    "county_candidates_provided",
    "outside_california_reported",
    "unresolved_or_other_scope",
}


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_source_key(row: dict) -> str:
    """Outcome-blind identity used only to thin dependent contributor reports."""
    identity = {
        "packet_id": row.get("packet_id"),
        "contributor_group": row.get("contributor_group"),
        "refs": row.get("refs"),
        "source_hashes": row.get("source_hashes"),
    }
    if not identity["packet_id"] or not identity["contributor_group"] or not identity["refs"]:
        raise ValueError("Selection requires packet_id, contributor_group, and refs")
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_bounds(row: dict) -> tuple[float, float | None]:
    lower, upper = row.get("lower"), row.get("upper")
    if isinstance(lower, bool) or not isinstance(lower, (int, float)) or not math.isfinite(lower) or lower < 0:
        raise ValueError("Every modeled observation needs a nonnegative numeric lower bound")
    if upper is not None and (isinstance(upper, bool) or not isinstance(upper, (int, float))
                              or not math.isfinite(upper) or upper <= lower):
        raise ValueError("A finite upper bound must exceed lower")
    kind = row.get("observation_kind")
    if kind == "completed_interval" and upper is None:
        raise ValueError("completed_interval requires an upper bound")
    if kind in {"completed_lower_bound", "pending_right_censored"} and upper is not None:
        raise ValueError(kind + " requires an open upper bound")
    return float(lower), None if upper is None else float(upper)


def _geography_mass_kind(value) -> str:
    """Classify imported geography metadata without coercing malformed values."""
    if (isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 1):
        return "positive" if value > 0 else "zero"
    return "unknown"


def _config(unit: str, *, chains: int, warmup: int, draws: int, seed: int) -> Config:
    # Scientific priors match the established exact-marginal forum frame.
    return Config(modeled_channels=("elapsed",), elapsed_time_unit=unit,
        agency_sd=0., task_sd=0., operation_sd=0., common_case_sd=0., source_sd=0.,
        selection_sd=0., population_size=32, elapsed_prior_median=7., location_sd=2.,
        case_log_sd_median=1., case_log_sd_prior=.5, chains=chains, warmup=warmup,
        draws=draws, seed=seed)


def prepare(observations_path: Path, out: Path, *, min_contributors: int,
            chains: int, warmup: int, draws: int, seed: int, scope: str = "all",
            clocks: tuple[str, ...] | None = None, domain: str = "solar") -> dict:
    if out.exists():
        raise FileExistsError(out)
    # ADU reuses the same conditional-frame model, not a copy of the sampler.
    # This only namespaces provenance; priors/likelihoods remain unchanged.
    if domain not in {"solar", "adu"}:
        raise ValueError("domain must be solar or adu")
    source_family = f"{domain}_bulk_forum"
    if clocks is not None and (not clocks or any(not isinstance(c, str) or not c.strip() for c in clocks)):
        raise ValueError("Declared fit clocks must be a nonempty collection of nonempty names")
    declared_clocks = None if clocks is None else set(clocks)
    packet = json.loads(observations_path.read_bytes())
    rows = packet if isinstance(packet, list) else packet.get("observations")
    if not isinstance(rows, list):
        raise ValueError("Input must be a list or an object with observations")
    adoption = None if isinstance(packet, list) else packet.get("adoption_state")
    if adoption not in {None, "adopted"}:
        raise ValueError("Bulk evidence must be root-adopted before model preparation")

    candidates: dict[tuple[str, str, str], list[tuple[str, dict]]] = {}
    dispositions, seen_claims = [], set()
    for row in rows:
        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id or claim_id in seen_claims:
            raise ValueError("claim_id values must be nonempty and unique")
        seen_claims.add(claim_id)
        route = None
        if scope == "california_supported" and row.get("geography_scope") not in {
                "california_supported_by_parser", "county_candidates_provided"}:
            route = "retained_outside_this_california_supported_sensitivity_frame"
        elif row.get("eligible_for_shared_clock_fit") is False:
            route = "retained_semantically_heterogeneous_or_non_target_clock"
        elif row.get("observation_kind") not in KINDS:
            route = "not_numeric_supported_censoring"
        elif row.get("time_unit") not in UNITS:
            route = "unsupported_or_missing_time_unit"
        elif not row.get("clock"):
            route = "missing_semantic_clock"
        elif declared_clocks is not None and row["clock"] not in declared_clocks:
            route = "retained_outside_declared_fit_estimands"
        elif not row.get("contributor_group"):
            route = "missing_contributor_group"
        if route:
            dispositions.append({"claim_id": claim_id, "route": route})
            continue
        _validate_bounds(row)
        source_key = _stable_source_key(row)
        key = (str(row["clock"]), str(row["time_unit"]), str(row["contributor_group"]))
        candidates.setdefault(key, []).append((source_key, row))

    selected, dependent = [], []
    for key, values in sorted(candidates.items()):
        values.sort(key=lambda pair: (pair[0], pair[1]["claim_id"]))
        selected.append(values[0][1])
        dependent.extend(row for _, row in values[1:])
    dispositions.extend({"claim_id": r["claim_id"],
                         "route": "same_contributor_clock_unit_not_independent",
                         "selected_by_outcome_blind_source_hash": next(
                             x["claim_id"] for x in selected if x["clock"] == r["clock"]
                             and x["time_unit"] == r["time_unit"]
                             and x["contributor_group"] == r["contributor_group"])}
                        for r in dependent)

    frames: dict[tuple[str, str], list[dict]] = {}
    for row in selected:
        frames.setdefault((row["clock"], row["time_unit"]), []).append(row)
    queue, frame_accounting, prepared_frames = [], [], []
    for index, ((clock, unit), group) in enumerate(sorted(frames.items())):
        slug = "frame_" + hashlib.sha256((clock + "\0" + unit).encode()).hexdigest()[:12]
        completed = sum(r["observation_kind"] == "completed_interval" for r in group)
        completed_lower_bounds = sum(
            r["observation_kind"] == "completed_lower_bound" for r in group)
        pending = sum(r["observation_kind"] == "pending_right_censored" for r in group)
        eligible = len(group) >= min_contributors and completed >= 5
        frame_accounting.append({"frame": slug, "clock": clock, "time_unit": unit,
            "contributors": len(group), "completed_intervals": completed,
            "completed_lower_bounds": completed_lower_bounds,
            "pending_right_censored": pending, "fit_eligible": eligible,
            "fit_disposition": "eligible" if eligible else (
                "below_minimum_contributors" if len(group) < min_contributors
                else "fewer_than_five_completed_intervals_no_location_claim")})
        for row in group:
            dispositions.append({"claim_id": row["claim_id"],
                "route": "modeled" if eligible else (
                    "retained_below_minimum_contributors" if len(group) < min_contributors
                    else "retained_fewer_than_five_completed_intervals_no_location_claim"),
                "frame": slug})
        if not eligible:
            continue
        observations = []
        for row in group:
            lower, upper = _validate_bounds(row)
            observations.append({"id": row["claim_id"], "case_id": row["contributor_group"],
                # This is the validator's literal admission token. The enclosing
                # frame defines the census as the hash-selected report frame,
                # not a census of applicants or installations.
                "source_family": source_family, "sampling": "census_within_declared_conditional_frame",
                "statistic": "individual", "lower": lower, "upper": upper,
                "time_unit": unit, "observation_kind": row["observation_kind"],
                "operators": [{"basis": "single_visit_cycle", "activity_ids": ["reported_phase"]}],
                "operator_weights": [1.], "provenance": {
                    "clock_id": row["claim_id"],
                    "evidence_cell_ids": [row["claim_id"]],
                    "date_resolution_rule": (
                        "Adopted normalized bounds; original source, clock, unit, and "
                        "rounding assumptions remain bound in the input packet.")}})
        frame_id = domain + "_bulk_" + slug
        ledger = {"schema_version": "conditional-case-frame-ledger/1", "rows": [
            {"registry_label_id": r["claim_id"], "status": "included",
             "case_id": r["contributor_group"], "reason": "Adopted bulk forum timing report"}
            for r in group]}
        canonical = canonical_sha256(ledger)
        target = f"Reported {clock} in {unit}"
        data = {"elapsed_time_unit": unit, "conditional_case_frames": [{
            "schema_version": "declared-conditional-case-frame/2", "id": frame_id,
            "target": target, "source_family": source_family,
            "eligibility": "One outcome-blind hash-selected report per contributor/clock/unit",
            "generalization_limit": "Selected-forum report frame; not applicant population, county policy, or agency capability",
            "registry_label_denominator": len(group),
            "included_case_ids": [r["contributor_group"] for r in group],
            "coarsening_assumption": {"kind": "assumed_ignorable_within_report_frame",
                "rationale": "Reported bounds and pending lower bounds are modeled as recorded; outcome-dependent posting and follow-up are not measured.",
                "sensitivity_plan": "Report completed and censored counts and retain geography/source strata for later declared sensitivity analyses; do not transport this frame to applicants.",
                "informative_posting_unmodeled": True}, "ledger": ledger,
            "ledger_sha256": canonical}], "programs": [{"id": frame_id,
            "conditional_frame_id": frame_id, "inventory_granularity": "aggregate_phases",
            "clock_estimand": target, "time_unit": unit, "observations": observations,
            "routes": [{"id": "single", "prior_weight": 1., "operations": [{
                "id": "reported_phase", "actor_id": None, "actor_role": "unknown",
                "task_type": "reported_phase", "markers": [], "payer_work": False,
                "agency_work": False}], "blocks": [{"id": "reported_phase",
                    "operations": ["reported_phase"]}]}]}]}
        cfg = _config(unit, chains=chains, warmup=warmup, draws=draws, seed=seed + index)
        # Both validators must accept every emitted frame before any fit is launched.
        VisitHierarchy(data, cfg)
        MarginalConditionalFrame(data, cfg, 128)
        prepared_frames.append((slug, data, asdict(cfg)))
        queue.append({"frame": slug, "clock": clock, "time_unit": unit,
            "contributors": len(group), "completed_intervals": completed,
            "completed_lower_bounds": completed_lower_bounds,
            "pending_right_censored": pending, "data": f"{slug}/data.json",
            "config": f"{slug}/config.json", "fit": f"{slug}/fit",
            "geography": {
                scope: sum(r.get("geography_scope") == scope for r in group)
                for scope in sorted(GEOGRAPHY_SCOPES)
            } | {
                "unknown_scope": sum(r.get("geography_scope") not in GEOGRAPHY_SCOPES
                                     for r in group),
                "unassigned_mass_positive": sum(
                    _geography_mass_kind(r.get("unassigned_geography_mass")) == "positive"
                    for r in group),
                "unassigned_mass_zero": sum(
                    _geography_mass_kind(r.get("unassigned_geography_mass")) == "zero"
                    for r in group),
                "unassigned_mass_unknown": sum(
                    _geography_mass_kind(r.get("unassigned_geography_mass")) == "unknown"
                    for r in group)}})
    receipt = {"schema_version": f"{domain}-bulk-forum-fit-plan/1",
        "domain": domain,
        "scope": scope,
        "declared_clocks": None if declared_clocks is None else sorted(declared_clocks),
        "clock_selection": "all admitted clock labels (legacy behavior)" if declared_clocks is None else (
            "Explicit estimand allowlist; other claims retained with routing dispositions, not erased or relabeled"),
        "input": str(observations_path), "input_sha256": _sha(observations_path),
        "selection": "minimum SHA256 of packet_id+contributor_group+refs+source_hashes within contributor/clock/unit; outcome and bounds excluded",
        "min_contributors": min_contributors, "input_claims": len(rows),
        "minimum_completed_intervals": 5,
        "eligibility": "At least min_contributors and at least five finite completed intervals; lower-bound-only frames are retained but not fit because report location is not identified by this bounded analysis.",
        "selected_claims": len(selected), "dependent_claims_retained_unmodeled": len(dependent),
        "candidate_frames": len(frame_accounting), "eligible_frames": len(queue),
        "frame_accounting": frame_accounting, "queue": queue,
        "qualification": "Frames are separate pooled selected-forum report distributions. They are not additive whole-process reconstructions or county/agency effects."}
    out.mkdir(parents=True)
    for slug, data, config in prepared_frames:
        _write(out / slug / "data.json", data)
        _write(out / slug / "config.json", config)
    _write(out / "route_accounting.json", {"rows": sorted(dispositions, key=lambda x: x["claim_id"])})
    _write(out / "fit_plan.json", receipt)
    return receipt


def fit(out: Path, workers: int, quadrature_size: int) -> None:
    plan = json.loads((out / "fit_plan.json").read_bytes())
    results = []
    for item in plan["queue"]:
        frame = out / item["frame"]
        fit_out = out / item["fit"]
        if fit_out.exists():
            raise FileExistsError(fit_out)
        data = json.loads((out / item["data"]).read_bytes())
        cfg_values = json.loads((out / item["config"]).read_bytes())
        cfg_values["modeled_channels"] = tuple(cfg_values["modeled_channels"])
        posterior = run_marginal_frame(data, Config(**cfg_values), fit_out,
            [out / item["data"], out / item["config"], out / "fit_plan.json",
             Path(__file__).resolve()], quadrature_size=quadrature_size, workers=workers)
        results.append({**item, "numerically_usable": posterior["numerically_usable"],
            "diagnostics_flagged": posterior["diagnostics_flagged"],
            "dimensions": posterior["dimensions"], "qualification": posterior["qualification"]})
        _write(out / "fit_results.json", results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-contributors", type=int, default=15)
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=1000)
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--quadrature-size", type=int, default=128)
    parser.add_argument("--scope", choices=["all", "california_supported"], default="all",
                        help="Optional California-supported sensitivity; never impute unknown county/state")
    parser.add_argument("--domain", choices=["solar", "adu"], default="solar",
                        help="Provenance namespace only; both domains use the identical marginal V6 model")
    parser.add_argument("--clock", action="append", dest="clocks",
                        help="Repeat to declare target clock labels; retain all other evidence outside this fit")
    parser.add_argument("--fit", action="store_true")
    args = parser.parse_args()
    if args.min_contributors < 1:
        parser.error("--min-contributors must be positive")
    if args.fit:
        fit(args.out.resolve(), args.workers, args.quadrature_size)
    else:
        result = prepare(args.observations.resolve(), args.out.resolve(),
            min_contributors=args.min_contributors, chains=args.chains,
            warmup=args.warmup, draws=args.draws, seed=args.seed, scope=args.scope,
            clocks=None if args.clocks is None else tuple(args.clocks), domain=args.domain)
        print(json.dumps({key: result[key] for key in (
            "schema_version", "input_sha256", "input_claims", "selected_claims",
            "dependent_claims_retained_unmodeled", "candidate_frames",
            "eligible_frames", "queue")}, indent=2))


if __name__ == "__main__":
    main()
