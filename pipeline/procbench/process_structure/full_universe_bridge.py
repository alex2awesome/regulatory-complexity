"""Embed a reviewed narrow occupancy input in the frozen full step registry.

The full administrative base remains authoritative for its source types.  Only
source types absent from that base (for example reviewed forum episodes) are
copied from the narrow input.  Missing expanded-step readings remain missing;
the bridge never manufactures checklist zeros.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from .occupancy import Evidence, verify_source_bindings


def _rows(rows):
    return {json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows}


def expand_to_full_registry(full_base: dict, narrow: dict, registry: list[dict], *,
                            admit_added_sources: bool = False) -> tuple[dict, dict]:
    registry_ids = [row.get("step_id") for row in registry]
    if (not registry_ids or len(set(registry_ids)) != len(registry_ids)
            or registry_ids != full_base.get("steps")):
        raise ValueError("Full base steps must exactly match the ordered frozen registry")
    if not set(narrow.get("steps", [])) <= set(registry_ids):
        raise ValueError("Narrow input contains actions outside the frozen registry")
    if narrow.get("jurisdictions") != full_base.get("jurisdictions"):
        raise ValueError("Expanded input cannot change the jurisdiction frame")
    if narrow.get("known_presence") != full_base.get("known_presence"):
        raise ValueError("Narrow input changed base truth anchors")

    base_types = set(full_base["source_types"])
    added_types = [kind for kind in narrow["source_types"] if kind not in base_types]
    # Every overlapping source is an exact projection of the full base onto
    # the narrow action set. This prevents renamed/copied rows entering twice.
    for kind in set(narrow["source_types"]) & base_types:
        expected = [row for row in full_base["observations"]
                    if row["source_type"] == kind and row["step_id"] in narrow["steps"]]
        actual = [row for row in narrow["observations"] if row["source_type"] == kind]
        if _rows(expected) != _rows(actual):
            raise ValueError(f"Narrow input changes overlapping source evidence: {kind}")

    data = copy.deepcopy(full_base)
    data["schema_version"] = narrow["schema_version"]
    admitted_types = added_types if admit_added_sources else []
    for kind in admitted_types:
        data["source_types"].append(kind)
        data["source_models"][kind] = copy.deepcopy(narrow["source_models"][kind])
        data["observations"].extend(copy.deepcopy([
            row for row in narrow["observations"] if row["source_type"] == kind]))
    if admit_added_sources and narrow.get("uncertain_jurisdiction_units"):
        if data.get("uncertain_jurisdiction_units"):
            raise ValueError("Full base already has unresolved units; explicit merge policy required")
        allowed = set(admitted_types)
        units = narrow["uncertain_jurisdiction_units"]
        if any(unit.get("source_type") not in allowed for unit in units):
            raise ValueError("Only newly added reviewed source types may supply unresolved units")
        data["uncertain_jurisdiction_units"] = copy.deepcopy(units)
    else:
        data["uncertain_jurisdiction_units"] = []

    data["scope"] = full_base["scope"]
    data["assumption_note"] = full_base["assumption_note"] + (
        " Reviewed narrow-universe sources are embedded only on their originally declared action scopes; "
        "expanded actions with no reading remain prior-determined, never synthetic nondetections. "
        + narrow.get("assumption_note", ""))
    if "forum_adoption" in narrow:
        data["forum_adoption"] = copy.deepcopy(narrow["forum_adoption"])
    data["full_universe_embedding"] = {
        "registry_count": len(registry_ids),
        "narrow_step_count": len(narrow["steps"]),
        "added_source_types": added_types,
        "admitted_added_source_types": admitted_types,
        "retained_descriptive_source_types": [k for k in added_types if k not in admitted_types],
        "missing_expanded_steps_emit_nondetections": False,
        "temporal_scope": full_base["scope"],
    }
    evidence = Evidence(data)
    support = evidence.support_report()
    direct_by_step = {step: 0 for step in registry_ids}
    for row in data["observations"]:
        direct_by_step[row["step_id"]] += 1
    for unit in data["uncertain_jurisdiction_units"]:
        for row in unit["readings"]:
            direct_by_step[row["step_id"]] += 1
    report = {
        "schema_version": "solar-full-universe-embedding/1",
        "status": "compiled_candidate_not_adopted_not_fitted",
        "registry_actions": len(registry_ids),
        "registry_actor_counts": {},
        "narrow_actions": len(narrow["steps"]),
        "added_source_types_found": added_types,
        "added_source_types_admitted": admitted_types,
        "added_sources_route": ("occupancy_likelihood" if admit_added_sources
                                 else "retained_descriptive_not_likelihood"),
        "added_resolved_readings": sum(
            row["source_type"] in admitted_types for row in data["observations"]),
        "added_uncertain_units": len(data["uncertain_jurisdiction_units"]),
        "added_uncertain_readings": sum(
            len(unit["readings"]) for unit in data["uncertain_jurisdiction_units"]),
        "synthetic_nondetections": 0,
        "retained_not_admitted": {
            "resolved_readings": sum(row["source_type"] in added_types
                                     for row in narrow["observations"]),
            "uncertain_units": len(narrow.get("uncertain_jurisdiction_units", [])),
            "uncertain_readings": sum(len(unit["readings"])
                                      for unit in narrow.get("uncertain_jurisdiction_units", [])),
            "reason": "Legacy 11-action completeness and response-selection assumptions are not re-adopted as full-universe reviewed opportunities."
        },
        "steps_without_any_direct_reading": sorted(
            step for step, count in direct_by_step.items() if count == 0),
        "direct_readings_by_step": direct_by_step,
        "support": support,
        "qualification": "No-reading cells are prior-determined under the hierarchy; this is not evidence that the action is absent.",
    }
    for row in registry:
        actor = row["actor"]
        report["registry_actor_counts"][actor] = report["registry_actor_counts"].get(actor, 0) + 1
    return data, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-base", type=Path, required=True)
    parser.add_argument("--narrow", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--admit-added-sources", action="store_true",
                        help="Opt in only for sources whose expanded action scopes were genuinely reviewed")
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("Choose a fresh output directory")
    registry = [json.loads(line) for line in args.registry.read_text().splitlines() if line.strip()]
    data, report = expand_to_full_registry(
        json.loads(args.full_base.read_text()), json.loads(args.narrow.read_text()), registry,
        admit_added_sources=args.admit_added_sources)
    verified = verify_source_bindings(data, args.source_root)
    args.out.mkdir(parents=True)
    (args.out / "occupancy_evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.out / "integration_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "step_registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "verified_source_files": verified,
                      "registry_actions": report["registry_actions"],
                      "synthetic_nondetections": 0}, indent=2))


if __name__ == "__main__":
    main()
