"""Apply explicit ADU overlays without reparsing text or inventing fit eligibility.

The output is a lossless, provenance-labeled record bundle, not a likelihood.
Original slices, including unmodeled fields and exclusions, remain embedded.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def quote_refs(value):
    if isinstance(value, dict):
        if isinstance(value.get("thread_id"), str) and isinstance(value.get("json_path"), str):
            yield value["thread_id"], value["json_path"]
        for child in value.values():
            yield from quote_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from quote_refs(child)


def provenance_for(speaker, claim, registry):
    declared = registry.get("speakers", {}).get(speaker, {})
    decision = declared.get("decision", "unreviewed")
    refs = set(quote_refs(claim))
    matched = [item for item in declared.get("claim_overrides", [])
               if (item["thread_id"], item["json_path"]) in refs]
    # Exclusions never relax an existing stricter speaker-level decision.
    if any(item.get("decision") == "exclude_primary" for item in matched):
        decision = "exclude_primary"
    return {"speaker_decision": declared.get("decision", "unreviewed"),
            "effective_decision": decision, "flag": declared.get("flag"),
            "source_type": declared.get("source_type", "unresolved"),
            "matched_claim_overrides": matched,
            "not_semantic_admission": True}


def identity_map(record_ids, merge_registry, review, records=()):
    """Use explicitly enumerated IDs, never a username-to-project heuristic."""
    parent = {ident: ident for ident in record_ids}
    assumptions, unresolved = [], []

    def find(ident):
        while parent[ident] != ident:
            parent[ident] = parent[parent[ident]]
            ident = parent[ident]
        return ident

    def connect(ids, origin, basis):
        present = [ident for ident in ids if ident in parent]
        missing = [ident for ident in ids if ident not in parent]
        if missing:
            unresolved.append({"origin": origin, "missing_ids": missing})
        for ident in present[1:]:
            left, right = find(present[0]), find(ident)
            parent[max(left, right)] = min(left, right)
        assumptions.append({"origin": origin, "member_ids": present, "basis": basis})

    for name, item in merge_registry.get("merge", {}).items():
        connect([member["episode_id"] for member in item.get("episodes", [])],
                "merge_registry:" + name, item.get("basis", merge_registry.get("rule")))
    for group in review.get("groups", []):
        if group["decision"] in {"merge_project", "attach_existing_addition"}:
            connect(group.get("episode_ids", []) + group.get("additional_evidence_ids", []),
                    "review:" + group["speaker"], group.get("basis"))
        elif group["decision"] == "contextual_alias":
            # Bind only records containing the specifically reviewed project evidence,
            # not every project either username has ever reported.
            refs = {(e["thread_id"], e["json_path"]) for e in group.get("evidence", [])}
            members = [r["record_id"] for r in records if r["record_id"] in parent
                       and refs.intersection(quote_refs(r["raw_record"]))]
            connect(members, "reviewed_project_alias:" + group["speaker"], group.get("basis"))
    protected = {ident for group in review.get("groups", [])
                 if group["decision"] == "retain_project_link_uncertainty"
                 for ident in group.get("episode_ids", []) + group.get("additional_evidence_ids", [])}
    pending = [r for r in records if r["record_type"] == "cross_slice_additions" and r["record_id"] not in protected]
    # A coder's explicit sibling-ID link is adopted only if its resolved targets
    # agree on one project. Conflicting targets stay candidates, not forced merges.
    while pending:
        changed, remaining = False, []
        for record in pending:
            if record["raw_record"].get("project_link_status") in {"candidate_only", "unresolved"}:
                # Explicit uncertainty defeats a candidate ID list. The evidence
                # still enters named-contributor report frames without a new case.
                remaining.append(record)
                continue
            siblings = record["raw_record"].get("sibling_records", [])
            # Two explicit-ID formats occur in reader outputs. Bare strings are
            # accepted only with the coder's confirmed-project declaration;
            # never resolve handles, prose or candidate lists as project IDs.
            declared_ids = [s.get("episode_id") if isinstance(s, dict) else
                            s if isinstance(s, str) and record["raw_record"].get(
                                "project_link_status") == "confirmed_same_project" else None
                            for s in siblings]
            target_ids = [ident for ident in declared_ids if ident in parent
                          and ident != record["record_id"]]
            groups = {find(ident) for ident in target_ids}
            if len(groups) == 1:
                before = find(record["record_id"])
                connect([record["record_id"]] + target_ids, "coder_sibling_ids:" + record["record_id"],
                        "Explicit sibling record IDs resolve to one existing project under the declared overlays; not inferred from handle.")
                changed |= before not in groups
            else:
                remaining.append(record)
        if not changed:
            break
        pending = remaining
    return {ident: find(ident) for ident in parent}, assumptions, unresolved


def stage_documents(documents, registry, merges, review):
    records, ids = [], set()
    for document in documents:
        data, source = document["data"], document["path"]
        for section in ("episodes", "cross_slice_additions", "general_practice_claims"):
            items = data.get(section, [])
            if not isinstance(items, list):
                raise ValueError((source, section, "expected array"))
            for index, item in enumerate(items):
                # Both layouts occur in the real corpus: earlier additions keep
                # measurements directly on the item, later ones nest them.
                # An absent wrapper must never turn retained evidence into {}.
                nested_addition = section == "cross_slice_additions" and isinstance(item.get("additional_evidence"), dict)
                record = item["additional_evidence"] if nested_addition else item
                if not isinstance(record, dict):
                    raise ValueError((source, section, index, "expected record object"))
                raw_id = record.get("episode_id") if section != "general_practice_claims" else record.get("claim_id")
                if section == "cross_slice_additions" and not nested_addition:
                    raw_id = raw_id or item.get("addition_id")
                ident = str(raw_id or f"{source}#/{section}/{index}")
                if ident in ids:
                    raise ValueError("Nonunique record ID requires explicit disambiguation: " + ident)
                ids.add(ident)
                # Older slices use `author`; preserve that explicit metadata
                # rather than converting a known handle into an anonymous case.
                # Do not extract handles from free-text notes here.
                speaker = (record.get("speaker") or record.get("author")
                           or item.get("speaker") or item.get("author"))
                claims = []
                if section == "general_practice_claims":
                    claims.append({"field": "general_practice_claim", "index": 0, "raw": record,
                                   "provenance": provenance_for(speaker, record, registry)})
                else:
                    for field in ("actions", "absent_actions", "durations", "round_counts",
                                  "pre_submittal_time", "costs", "effort", "note_quotes"):
                        entries = record.get(field) or []
                        if not isinstance(entries, list):
                            # Preserve uncommon field shapes without silently asserting no evidence.
                            entries = [entries]
                        for i, claim in enumerate(entries):
                            claims.append({"field": field, "index": i, "raw": claim,
                                           "provenance": provenance_for(speaker, claim, registry)})
                records.append({"record_id": ident, "source_document": source,
                                "source_pointer": f"/{section}/{index}", "record_type": section,
                                "speaker": speaker, "raw_record": item, "claims": claims,
                                "provenance": provenance_for(speaker, {}, registry)})
    project_ids = {r["record_id"] for r in records if r["record_type"] != "general_practice_claims"}
    mapping, assumptions, unresolved = identity_map(project_ids, merges, review, records)
    uncertainty = {g["speaker"]: g for g in review.get("groups", [])
                   if g["decision"] in {"retain_project_link_uncertainty", "contextual_alias"}}
    for record in records:
        record["explicit_project_group"] = mapping.get(record["record_id"])
        record["identity_qualification"] = uncertainty.get(record["speaker"])
        if record["record_type"] == "cross_slice_additions":
            record["link_status"] = ("explicitly_bound" if any(record["record_id"] in a["member_ids"] and len(a["member_ids"]) > 1
                                                                for a in assumptions) else "retained_unresolved_addition")
    return {"schema_version": "adu-forum-evidence-bundle/1", "documents": documents,
            "records": records, "speaker_registry": registry, "identity_registry": merges,
            "identity_review": review, "identity_assumptions": assumptions,
            "unresolved_identity_references": unresolved,
            "counts": {"documents": len(documents), "records_by_type": dict(Counter(r["record_type"] for r in records)),
                       "claim_rows": sum(len(r["claims"]) for r in records),
                       "claim_provenance_routes": dict(Counter(c["provenance"]["effective_decision"] for r in records for c in r["claims"]))},
            "fit_ready_observations": 0,
            "qualification": "Lossless staging with explicit overlay application, not new reading, semantic certification or model consumption. General practice, explicit absence and narrated actions are different measurement channels; array order is not chronology. Unknown county is retained. Unresolved additions are not independent new projects. Historical merge rules are declared assumptions, not identity truth."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parsed", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--merges", type=Path, required=True)
    parser.add_argument("--identity-review", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    paths = sorted(args.parsed.glob("*.json"))
    all_paths = paths + [args.registry, args.merges, args.identity_review]
    original = {str(path): path.read_bytes() for path in all_paths}
    documents = [{"path": str(path), "sha256": hashlib.sha256(original[str(path)]).hexdigest(),
                  "data": json.loads(original[str(path)])} for path in paths]
    bundle = stage_documents(documents, *(json.loads(original[str(p)]) for p in (args.registry, args.merges, args.identity_review)))
    bundle["input_sha256"] = {path: hashlib.sha256(raw).hexdigest() for path, raw in original.items()}
    bundle["compiler_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for path in all_paths:
        if path.read_bytes() != original[str(path)]:
            raise RuntimeError("Inputs changed during staging: " + str(path))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(bundle, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(bundle["counts"], indent=2))


if __name__ == "__main__":
    main()
