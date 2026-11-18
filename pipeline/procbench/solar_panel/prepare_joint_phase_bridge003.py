"""Assemble the frozen-prior bridge003 expansion; never run a sampler here."""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.solar_panel.prepare_joint_phase_bridge import compile_bridge, row_digest


ROOT = Path("runs/solar_forum_20260922/county_model")
ALIGNMENT = ROOT / "source_alignment_v11.json"
EVIDENCE = ROOT / "evidence_v11.json"
OUTPUT = ROOT / "joint_phase_bridge003"

# Source semantics use both typographic and ASCII spellings. This normalization
# changes no geography or actor: it only maps an explicit utility name to the
# already-declared canonical utility token consumed by bridge002.
UTILITY_TOKEN_ALIASES = {"PG&E": "PGE"}


def normalize_alignment(alignment: dict) -> tuple[dict, list[dict]]:
    normalized = copy.deepcopy(alignment)
    receipts: list[dict] = []
    for claim in normalized["claims"]:
        values = claim["geography"]["utility_candidates"]
        mapped = [UTILITY_TOKEN_ALIASES.get(value, value) for value in values]
        if mapped != values:
            receipts.append({
                "row_id": claim["row_id"],
                "source_claim_id": claim["source_claim_id"],
                "before": values,
                "after": mapped,
                "reason": "explicit_utility_spelling_alias_only",
            })
            claim["geography"]["utility_candidates"] = mapped
    return normalized, receipts


def forum_program_ids(data: dict) -> list[str]:
    return sorted(
        program["id"]
        for program in data["programs"]
        if any(obs.get("source_type") == "forum" for obs in program["observations"])
    )


def add_joint_block(data: dict) -> None:
    data["sampler_joint_blocks"] = {
        "schema_version": "sampler-joint-blocks/1",
        "overlap_policy": "sequential_invariant_kernels",
        "blocks": [{
            "id": "forum_type_and_context_locations",
            "rationale": (
                "Same prior-preserving transition used by bridge002/fit004 over the forum "
                "type contrast, fixed forum context terms, and every forum-program residual."
            ),
            "selectors": [
                {"kind": "source_type_effect", "source_type": "forum"},
                {"kind": "operation_location_design_group", "group": "size"},
                {"kind": "operation_location_design_group", "group": "storage"},
                {"kind": "operation_location_design_group", "group": "year"},
                {"kind": "operation_residuals", "program_ids": forum_program_ids(data)},
            ],
        }],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alignment", type=Path, default=ALIGNMENT)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"Refusing to overwrite existing bridge output: {args.out}")

    raw_alignment = json.loads(args.alignment.read_text())
    evidence = json.loads(args.evidence.read_text())
    alignment, normalization_receipts = normalize_alignment(raw_alignment)
    data, config_record, accounting = compile_bridge(alignment, evidence)

    admitted = [row for row in accounting["forum"]["routes"] if row["disposition"] == "admitted"]
    case_ids = [row["canonical_case_id"] for row in admitted]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("bridge003 requires exactly one admitted observation per canonical case")
    if accounting["duplicate_canonical_cases"]:
        raise ValueError("bridge003 refuses ambiguous multiple eligible clocks per canonical case")

    provenance = {
        "alignment_path": str(args.alignment),
        "alignment_sha256": row_digest(raw_alignment),
        "normalized_alignment_sha256": row_digest(alignment),
        "evidence_path": str(args.evidence),
        "evidence_sha256": row_digest(evidence),
        "base_scientific_input": "runs/solar_forum_20260922/county_model/joint_phase_bridge002/data_joint_ess.json",
        "base_successful_fit": "runs/solar_forum_20260922/county_model/joint_phase_bridge002/fit004_collapsed_q256",
    }
    data["provenance"] = provenance
    accounting["provenance"] = provenance
    accounting["utility_token_normalization"] = normalization_receipts
    add_joint_block(data)

    production_config = {
        "chains": 4,
        "warmup": 1000,
        "draws": 2000,
        "workers": 2,
        "seed": 2026092001,
        "population_size": 1024,
        "cohort_quadrature_size": 256,
        "population_integration": "collapsed_single_phase_quadrature",
        "collapsed_case_quadrature_size": 256,
        "refinement_collapsed_case_quadrature_size": 512,
        "modeled_channels": ["elapsed"],
        "elapsed_time_unit": "calendar_days",
        "agency_sd": 0.75,
        "selection_sd": 0.0,
        "unknown_n_report_sd_floor": 0.5,
        "hierarchy_sampler": "operation_centered",
        "source_hierarchy_sampler": "interwoven",
        "case_scale_sampler": "blocked",
        "scientific_change_from_fit004": "evidence_only",
        "automatic_retry_or_extension": False,
    }
    cfg = Config(
        modeled_channels=("elapsed",), elapsed_time_unit="calendar_days",
        population_size=1024, population_integration="collapsed_single_phase_quadrature",
        collapsed_case_quadrature_size=256, agency_sd=.75, selection_sd=0.,
        unknown_n_report_sd_floor=.5, hierarchy_sampler="operation_centered",
        source_hierarchy_sampler="interwoven", case_scale_sampler="blocked",
    )
    model = VisitHierarchy(data, cfg)
    z = np.zeros(model.layout.size)
    structures = [0] * len(model.programs)
    likelihood = model.log_likelihood(z, structures)
    if not math.isfinite(likelihood):
        raise ValueError("Non-finite collapsed bridge003 zero-state likelihood")

    chosen = []
    for p in data["programs"]:
        for obs in p["observations"]:
            if obs["source_type"] == "forum":
                chosen.append({
                    "program_id": p["id"], "observation_id": obs["id"],
                    "case_id": obs["case_id"], "source_claim_id": obs["provenance"]["source_claim_id"],
                    "lower": obs["lower"], "upper": obs["upper"],
                    "logical_threads": obs["provenance"]["logical_threads"],
                })
    chosen.sort(key=lambda row: row["case_id"])
    preflight = {
        "schema_version": "solar-joint-phase-preflight/1",
        "valid": True,
        "finite_zero_state_log_likelihood": True,
        "zero_state_log_likelihood": float(likelihood),
        "programs": len(model.programs), "operations": len(model.operations),
        "observations": sum(len(p["observations"]) for p in data["programs"]),
        "forum_observations": len(chosen),
        "administrative_observations": sum(
            obs["source_type"] == "official_administrative_panel"
            for p in data["programs"] for obs in p["observations"]),
        "coordinates": model.layout.size,
        "one_report_per_canonical_case": len(chosen) == len({x["case_id"] for x in chosen}),
        "collapsed_guard_constructed": True,
        "sampler_run": False,
    }

    args.out.mkdir(parents=True)
    outputs = {
        "data.json": data,
        "data_joint_ess.json": data,
        "config.json": config_record,
        "production_run_config.json": production_config,
        "route_accounting.json": accounting,
        "chosen_forum_observations.json": {"count": len(chosen), "observations": chosen},
        "preflight.json": preflight,
    }
    for name, value in outputs.items():
        (args.out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps(preflight, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
