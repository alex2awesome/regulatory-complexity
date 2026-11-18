"""Add reviewed official-policy presence anchors to occupancy evidence.

Official instructions are not independent detection trials.  A supported
requirement/available route can establish that an action exists in the modeled
jurisdiction scope, including when it is conditional on a declared route.  It
does not establish universal applicant participation.  Absence is admissible
only when the claim maps to a registry action and explicitly covers the whole
modeled scope; source silence is never converted to absence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .occupancy import Evidence, verify_source_bindings


def _source_ref(claim: dict, source_root: Path) -> dict:
    source = claim.get("source")
    if not isinstance(source, dict):
        raise ValueError("Every consumed official claim needs source metadata")
    rel = source.get("text_path") or source.get("raw_path")
    if not isinstance(rel, str) or not rel:
        raise ValueError("Every consumed official claim needs a captured source path")
    path = source_root / rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    locator = source.get("lines")
    quote = source.get("quote")
    if not isinstance(locator, str) or not locator or not isinstance(quote, str) or not quote.strip():
        raise ValueError("Every consumed official claim needs reviewed lines and quotation")
    return {"path": rel, "sha256": digest,
            "locator": f"lines {locator}; reviewed quote: {quote}"}


def add_official_instruction_anchors(
        base: dict, additions: dict, authority_resolution: dict, *, source_root: Path
        ) -> tuple[dict, dict]:
    """Return a successor input plus complete claim routing.

    ``authority_resolution`` is an explicit source-scope resolution, not a
    generic county-to-city crosswalk.  Each value needs ``jurisdiction_id`` and
    a nonempty evidential ``basis``.
    """
    data = copy.deepcopy(base)
    steps, jurisdictions = set(data["steps"]), set(data["jurisdictions"])
    existing = {(row["jurisdiction_id"], row["step_id"]): row
                for row in data["known_presence"]}
    grouped: dict[tuple[str, str], list[tuple[dict, dict]]] = defaultdict(list)
    routes = []

    for claim in additions.get("mapped_ahj_action_claims", []):
        cid, county, step = claim.get("claim_id"), claim.get("county"), claim.get("mapped_action_id")
        resolution = authority_resolution.get(county)
        if (not isinstance(resolution, dict)
                or not isinstance(resolution.get("jurisdiction_id"), str)
                or not isinstance(resolution.get("basis"), str)
                or not resolution["basis"].strip()):
            raise ValueError(f"Missing explicit authority resolution for {county}")
        jurisdiction = resolution["jurisdiction_id"]
        if jurisdiction not in jurisdictions or step not in steps:
            raise ValueError(f"Unknown resolved jurisdiction/action for {cid}")
        ref = _source_ref(claim, source_root)
        grouped[(jurisdiction, step)].append((claim, ref))

    added = []
    for (jurisdiction, step), members in sorted(grouped.items()):
        claim_ids = [claim["claim_id"] for claim, _ in members]
        if (jurisdiction, step) in existing:
            if existing[(jurisdiction, step)].get("present") is not True:
                raise ValueError("Official positive conflicts with an existing absence anchor")
            routes.extend({"claim_id": cid, "disposition": "already_anchored_true",
                           "jurisdiction_id": jurisdiction, "step_id": step}
                          for cid in claim_ids)
            continue
        refs = list({(ref["path"], ref["sha256"], ref["locator"]): ref
                     for _, ref in members}.values())
        row = {
            "unit_id": "official-v13::" + jurisdiction + "::" + step,
            "jurisdiction_id": jurisdiction,
            "step_id": step,
            "present": True,
            "basis": "explicit_presence",
            "evidence_refs": refs,
            "official_claim_ids": claim_ids,
            "policy_interpretation": (
                "Existential action availability/presence in the declared authority and temporal scope; "
                "conditional route claims do not imply universal applicant participation."),
        }
        data["known_presence"].append(row)
        existing[(jurisdiction, step)] = row
        added.append(row)
        routes.extend({"claim_id": cid, "disposition": "consumed_in_presence_anchor",
                       "jurisdiction_id": jurisdiction, "step_id": step,
                       "anchor_unit_id": row["unit_id"]} for cid in claim_ids)

    # Conditional absences in this packet are retained, but only a registry-
    # mapped, whole-scope declaration could become an explicit_absence anchor.
    for claim in additions.get("conditional_absences", []):
        disposition = "retained_outside_registry" if claim.get("mapped_action_id") is None \
            else "retained_route_conditional_not_whole_scope_absence"
        routes.append({"claim_id": claim.get("claim_id"), "disposition": disposition,
                       "mapped_action_id": claim.get("mapped_action_id"),
                       "condition": claim.get("condition")})
    for row in additions.get("silence_not_absence", []):
        routes.append({"county": row.get("county"), "route_variant": row.get("route_variant"),
                       "disposition": "silence_retained_no_likelihood"})

    data.setdefault("official_instruction_integration", {})["v13_additions"] = {
        "source_schema": additions.get("schema_version"),
        "observation_model": "explicit_presence_truth_anchor_not_detection_trial",
        "added_presence_anchors": len(added),
        "added_detection_trials": 0,
        "conditional_absence_anchors": 0,
        "qualification": "Conditional route positives establish availability, not mandatory participation; silence is not absence.",
    }
    Evidence(data)
    report = {
        "schema_version": "solar-official-instruction-integration/1",
        "status": "compiled_candidate_not_fitted",
        "observation_model_mapping": {
            "positive_requirement_or_available_route": "known_presence explicit_presence anchor",
            "duplicate_positive_same_cell": "one anchor with all source claim IDs/references",
            "conditional_absence_outside_registry": "route accounting only",
            "generic_silence": "no likelihood",
        },
        "added_likelihood_detection_trials": 0,
        "added_presence_anchors": len(added),
        "added_anchor_cells": [{"jurisdiction_id": row["jurisdiction_id"],
                                "step_id": row["step_id"],
                                "claim_ids": row["official_claim_ids"]} for row in added],
        "counties_with_added_anchors": sorted({j.removesuffix("_county").replace("_", " ")
                                                for j, _ in [(r["jurisdiction_id"], r["step_id"])
                                                             for r in added]}),
        "routes": routes,
    }
    return data, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--additions", type=Path, required=True)
    parser.add_argument("--authority-resolution", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("Choose a fresh output directory")
    data, report = add_official_instruction_anchors(
        json.loads(args.base.read_text()), json.loads(args.additions.read_text()),
        json.loads(args.authority_resolution.read_text()), source_root=args.source_root)
    verified = verify_source_bindings(data, args.source_root)
    args.out.mkdir(parents=True)
    (args.out / "occupancy_evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.out / "integration_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "verified_source_files": verified,
                      "added_presence_anchors": report["added_presence_anchors"],
                      "added_likelihood_detection_trials": 0}, indent=2))


if __name__ == "__main__":
    main()
