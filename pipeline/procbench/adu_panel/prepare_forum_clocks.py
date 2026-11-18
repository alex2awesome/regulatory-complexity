"""Compile explicit ADU clock readings into the shared marginal-V6 input format.

No inference from prose, no regex duration extraction, and no source re-audit.
The human/LLM contextual reader supplies an adopted, hash-bound measurement.
Unreviewed and non-duration claims remain in a lossless routing ledger.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .forum_evidence import quote_refs
from ..solar_panel.adopt_bulk_forum import duration_bounds


def content_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def claim_id(record, claim):
    return f"{record['record_id']}:{claim['field']}:{claim['index']}"


def bind_dependence_groups(observations):
    """Conservatively thin both repeated handles and explicitly linked projects.

    This is a dependence group, not a new person/project identity adjudication.
    In particular two reviewed aliases for one project must not become two
    independent observations simply because their handles differ.
    """
    parent = {}

    def find(key):
        parent.setdefault(key, key)
        if parent[key] != key:
            parent[key] = find(parent[key])
        return parent[key]

    for row in observations:
        contributor = (row["platform"], "contributor", row["contributor_group"])
        project = (row["platform"], "project", row["case_id"])
        left, right = find(contributor), find(project)
        parent[max(left, right)] = min(left, right)
    groups = {}
    for key in parent:
        groups.setdefault(find(key), []).append(key)
    for row in observations:
        original = row["contributor_group"]
        key = find((row["platform"], "contributor", original))
        members = sorted(groups[key])
        row["reported_contributor_group"] = original
        row["contributor_group"] = "adu_dependence:" + content_sha(members)
        row["dependence_group_members"] = members


def compile_clocks(bundle, review):
    if review.get("schema_version") != "adu-clock-review/1" or review.get("adoption_state") != "adopted":
        raise ValueError("Requires an adopted adu-clock-review/1 packet")
    if not review.get("reviewed_by"):
        raise ValueError("Clock review needs a reviewer")
    definitions = review.get("clocks", {})
    for name, definition in definitions.items():
        if not name or not isinstance(definition, dict) or not all(definition.get(k) for k in ("start", "end", "qualification")):
            raise ValueError("Every clock needs explicit start, end and qualification")
    entries = {}
    for record in bundle["records"]:
        for claim in record["claims"]:
            key = claim_id(record, claim)
            if key in entries:
                raise ValueError("Duplicate claim ID: " + key)
            entries[key] = (record, claim)
    annotations = dict(review.get("claims", {}))
    source_claims = {key: key for key in entries}
    reading_indices = {key: 0 for key in entries}
    original_claim_count = len(entries)
    for key, annotation in list(annotations.items()):
        if key not in entries:
            raise ValueError("Reviewed claim missing from input: " + key)
        additional = annotation.get("additional_readings", [])
        if not isinstance(additional, list):
            raise ValueError("Additional clock readings must be an array: " + key)
        for index, child in enumerate(additional, 1):
            if not isinstance(child, dict):
                raise ValueError("Additional clock reading must be an object: " + key)
            child_key = f"{key}:reading:{index}"
            if child_key in entries or child_key in annotations:
                raise ValueError("Duplicate additional clock reading: " + child_key)
            entries[child_key] = entries[key]
            annotations[child_key] = {
                "claim_content_sha256": annotation.get("claim_content_sha256"),
                "route": "duration",
                **{name: annotation[name] for name in ("platform", "geography_scope") if name in annotation},
                **child,
            }
            source_claims[child_key], reading_indices[child_key] = key, index
    for key, annotation in annotations.items():
        if annotation.get("claim_content_sha256") != content_sha(entries[key][1]["raw"]):
            raise ValueError("Stale reviewed claim: " + key)
        if not annotation.get("rationale"):
            raise ValueError("Reviewed claim requires a rationale: " + key)
        if annotation.get("route") not in {"duration", "descriptive", "unresolved"}:
            raise ValueError("Unsupported clock-review route: " + key)
    routes, observations = [], []
    for key, (record, claim) in entries.items():
        annotation = annotations.get(key)
        speaker = str(record.get("speaker") or "").strip().casefold()
        named_contributor = speaker not in {"", "[deleted]", "[removed]", "none"}
        row = {"claim_id": key, "source_claim_id": source_claims[key],
               "reading_index": reading_indices[key], "record_id": record["record_id"],
               "record_type": record["record_type"], "field": claim["field"],
               "original": claim["raw"], "source_document": record["source_document"],
               "source_pointer": record["source_pointer"],
               "project_group": record.get("explicit_project_group"),
               "provenance": claim["provenance"], "clock_review": annotation}
        if claim["field"] not in {"durations", "pre_submittal_time"}:
            row["route"] = "retained_other_measurement_channel"
        elif claim["provenance"]["effective_decision"] in {"exclude_primary", "out_of_scope", "sensitivity_only"}:
            row["route"] = "retained_provenance_" + claim["provenance"]["effective_decision"]
        elif (record["record_type"] == "cross_slice_additions"
              and record.get("link_status") != "explicitly_bound" and not named_contributor):
            row["route"] = "retained_unresolved_anonymous_addition_dependence_unknown"
        elif annotation is None:
            row["route"] = "retained_without_structured_clock_reading"
        elif annotation["route"] != "duration":
            row["route"] = "retained_reviewed_" + annotation["route"]
        else:
            clock = annotation.get("clock")
            if clock not in definitions:
                raise ValueError("Reviewed duration requires a defined clock: " + key)
            quantity = annotation.get("quantity")
            status = annotation.get("observation_status")
            if quantity not in {"elapsed_calendar_time", "elapsed_business_time"}:
                row["route"] = "retained_non_elapsed_quantity"
            elif status not in {"completed", "pending"}:
                if status not in {"forecast", "policy_deadline", "unresolved"}:
                    raise ValueError("Explicit observation status required: " + key)
                row["route"] = "retained_" + status
            else:
                measurement = annotation.get("measurement", {})
                precision = annotation.get("precision", "approximate" if measurement.get("approximate") else "unspecified")
                if precision not in {"unspecified", "approximate", "month_only", "year_only"}:
                    raise ValueError("Unsupported declared duration precision: " + key)
                if (quantity == "elapsed_business_time") != (measurement.get("unit") == "business_days"):
                    raise ValueError("Elapsed quantity and unit disagree: " + key)
                bounds, error = duration_bounds(measurement,
                    "pending_lower_bound" if status == "pending" else "completed_observed",
                    precision)
                if error:
                    raise ValueError(f"Invalid adopted bounds for {key}: {error}")
                refs = sorted(set(quote_refs(claim["raw"])))
                if not refs:
                    raise ValueError("Adopted duration has no retained source references: " + key)
                platform = annotation.get("platform", review.get("platform", "unspecified_forum"))
                if platform not in {"reddit", "houzz", "biggerpockets", "contractortalk", "archinect", "unspecified_forum"}:
                    raise ValueError("Unsupported or missing forum platform: " + key)
                contributor = (platform + ":" + speaker if named_contributor
                               else "project:" + record["explicit_project_group"])
                source_document = record["source_document"]
                source_sha = bundle["input_sha256"][source_document]
                observation = {"claim_id": key, "source_claim_id": source_claims[key],
                    "reading_index": reading_indices[key], "packet_id": source_document,
                    "case_id": record["explicit_project_group"], "contributor_group": contributor,
                    "platform": platform,
                    "project_link_status": record.get("link_status"),
                    "project_identity_qualification": (
                        "Unresolved addition admitted only to the contributor-thinned conditional report frame; not a new independent installation or a linked multi-step journey."
                        if record["record_type"] == "cross_slice_additions" and record.get("link_status") != "explicitly_bound"
                        else "Original explicit project grouping retained; no new project identity inferred."),
                    "clock": clock, "clock_definition": definitions[clock],
                    "eligible_for_shared_clock_fit": True, **bounds,
                    "refs": [f"{thread}:{path}" for thread, path in refs],
                    "source_hashes": {source_document: source_sha},
                    "geography_scope": annotation.get("geography_scope", "unresolved_or_other_scope"),
                    "jurisdiction_as_coded": (record["raw_record"].get("additional_evidence", record["raw_record"])).get("jurisdiction"),
                    "unassigned_geography_mass": None,
                    "original": claim["raw"], "adopted_reading": annotation,
                    "source_reference_qualification": "References were retained in the already coded slice; compilation does not repeat quote verification. Source-document hash binds that coding. Raw-capture hashes remain in the slice's own receipts.",
                    "dependence_qualification": "Shared fitter selects at most one outcome-blind report per dependence-group/clock/unit. Groups connect same-platform handles and explicitly linked projects; they are conservative dependence groups, not inferred project/person identities."}
                observations.append(observation)
                row["route"] = "adopted_elapsed_observation_not_fitted"
        routes.append(row)
    bind_dependence_groups(observations)
    return {"schema_version": "adu-clock-compilation/1", "adoption_state": "adopted",
            "observations": observations, "claim_routes": routes,
            "clocks": definitions, "reviewed_by": review["reviewed_by"],
            "counts": {"all_claims": original_claim_count,
                       "additional_clock_readings": len(entries) - original_claim_count,
                       "routing_rows": len(routes), "reviewed_claims": len(review.get("claims", {})),
                       "reviewed_readings": len(annotations),
                       "adopted_elapsed_observations": len(observations),
                       "routes": dict(Counter(r["route"] for r in routes))},
            "qualification": "Structured clock admission only, not fitting. Unknown jurisdiction is retained. Named unresolved additions can enter the contributor-thinned report frame, never independent project/journey inference; anonymous unresolved additions remain held. Completed lower bounds differ from pending censoring; distinct clocks are not additive; forum selection and intrinsic agency capability are not identified."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    inputs = {str(path): path.read_bytes() for path in (args.bundle, args.review)}
    result = compile_clocks(*(json.loads(inputs[str(path)]) for path in (args.bundle, args.review)))
    result["input_sha256"] = {name: hashlib.sha256(raw).hexdigest() for name, raw in inputs.items()}
    result["compiler_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(result["counts"], indent=2))


if __name__ == "__main__":
    main()
