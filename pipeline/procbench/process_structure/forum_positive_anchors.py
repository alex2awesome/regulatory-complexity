"""Compile selected forum positives as existential presence anchors.

Selection on a positive response invalidates detection/prevalence estimation,
but a verified, actor-correct occurrence with resolved identity can still prove
that the action existed in that jurisdiction and era.  This adapter consumes
no negative rows and adds no detection source type.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict
from pathlib import Path

from .occupancy import Evidence, verify_source_bindings


def add_positive_anchors(base: dict, selected: dict, decisions: dict,
                         registry: list[dict]) -> tuple[dict, dict]:
    if decisions.get("schema_version") != "solar-forum-positive-anchor-decisions/1":
        raise ValueError("Need explicit positive-anchor decisions")
    era = decisions.get("target_era")
    if (not isinstance(era, dict) or type(era.get("start_year")) is not int
            or type(era.get("end_year")) is not int or era["start_year"] > era["end_year"]):
        raise ValueError("Decisions must declare a finite target era")
    actor_by_step = {row["step_id"]: row["actor"] for row in registry}
    if set(actor_by_step) != set(base["steps"]):
        raise ValueError("Registry and base action universe differ")
    positives = {(row["unit_id"], row["step_id"]): row
                 for row in selected["observations"]
                 if row.get("source_type") == "forum_initial_episode" and row.get("detected") is True}
    rows = decisions.get("decisions")
    if not isinstance(rows, list) or len({(r.get("unit_id"), r.get("step_id")) for r in rows}) != len(rows):
        raise ValueError("Decision keys must be unique")
    keyed = {(row["unit_id"], row["step_id"]): row for row in rows}
    if set(keyed) != set(positives):
        raise ValueError("Every selected resolved positive needs exactly one decision")

    data = copy.deepcopy(base)
    existing = {(row["jurisdiction_id"], row["step_id"]): row
                for row in data["known_presence"]}
    grouped = defaultdict(list)
    routes = []
    for key, source in positives.items():
        decision = keyed[key]
        disposition = decision.get("disposition")
        if disposition == "retain_descriptive":
            routes.append({"unit_id": key[0], "step_id": key[1], "disposition": disposition,
                           "reason": decision.get("reason")})
            continue
        if disposition != "anchor_presence":
            raise ValueError("Decision must anchor or retain descriptively")
        year, actor = decision.get("event_year"), decision.get("actor")
        if (type(year) is not int or not era["start_year"] <= year <= era["end_year"]
                or actor != actor_by_step[source["step_id"]]):
            raise ValueError("Anchor needs an in-era event and exact registry actor")
        if source.get("jurisdiction_id") not in data["jurisdictions"]:
            raise ValueError("Positive anchor requires resolved modeled jurisdiction")
        grouped[(source["jurisdiction_id"], source["step_id"])].append((source, decision))

    added = []
    for cell, members in sorted(grouped.items()):
        jurisdiction, step = cell
        if cell in existing:
            if existing[cell].get("present") is not True:
                raise ValueError("Forum positive conflicts with explicit absence")
            routes.extend({"unit_id": source["unit_id"], "step_id": step,
                           "disposition": "already_anchored_true", "jurisdiction_id": jurisdiction}
                          for source, _ in members)
            continue
        refs = list({(ref["path"], ref["sha256"], ref["locator"]): copy.deepcopy(ref)
                     for source, _ in members for ref in source["evidence_refs"]}.values())
        row = {
            "unit_id": f"forum-positive-anchor::{jurisdiction}::{step}",
            "jurisdiction_id": jurisdiction, "step_id": step, "present": True,
            "basis": "explicit_presence", "evidence_refs": refs,
            "actor": actor_by_step[step],
            "event_years": sorted({decision["event_year"] for _, decision in members}),
            "source_episode_ids": sorted({source["unit_id"] for source, _ in members}),
            "selection_qualification": (
                "Positive-selected source proves existential occurrence only; it supplies no detection, "
                "nondetection, encounter-frequency, or mandatory-participation likelihood."),
        }
        data["known_presence"].append(row)
        existing[cell] = row
        added.append(row)
        routes.extend({"unit_id": source["unit_id"], "step_id": step,
                       "disposition": "consumed_in_presence_anchor", "jurisdiction_id": jurisdiction,
                       "anchor_unit_id": row["unit_id"]} for source, _ in members)

    data["forum_positive_anchor_integration"] = {
        "target_era": copy.deepcopy(era), "positive_rows_reviewed": len(positives),
        "added_anchor_cells": len(added), "detection_trials_added": 0,
        "nondetections_added": 0,
        "estimand": "existential typed action presence in resolved jurisdiction and target era",
    }
    Evidence(data)
    return data, {
        "schema_version": "solar-forum-positive-anchor-integration/1",
        "status": "compiled_candidate_not_fitted",
        "positive_rows_reviewed": len(positives),
        "added_anchor_cells": len(added),
        "duplicate_true_anchor_rows": sum(r["disposition"] == "already_anchored_true" for r in routes),
        "retained_descriptive_rows": sum(r["disposition"] == "retain_descriptive" for r in routes),
        "detection_trials_added": 0, "nondetections_added": 0,
        "added_anchors": added, "routes": routes,
        "qualification": "No claim about encounter frequency, mandatory participation, detection probability, utility identity, or actions outside the exact positive occurrence.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("Choose a fresh output directory")
    registry = [json.loads(line) for line in args.registry.read_text().splitlines() if line.strip()]
    data, receipt = add_positive_anchors(
        json.loads(args.base.read_text()), json.loads(args.selected.read_text()),
        json.loads(args.decisions.read_text()), registry)
    verified = verify_source_bindings(data, args.source_root)
    args.out.mkdir(parents=True)
    (args.out / "occupancy_evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.out / "integration_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "verified_source_files": verified,
                      "added_anchor_cells": receipt["added_anchor_cells"],
                      "detection_trials_added": 0}, indent=2))


if __name__ == "__main__":
    main()
