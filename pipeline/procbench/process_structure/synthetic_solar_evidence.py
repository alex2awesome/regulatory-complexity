"""Build the occupancy evidence contract from the synthetic solar test-bed.

The real solar data could not identify detection probability: the requirements
survey is one instrument answered once, so there is almost nothing to compare
it against. The synthetic world fixes exactly that. Statute S07 is implemented
by four counties, each with six to nine independent documents of different
kinds, so the same step is looked for many times in the same county through
different eyes. That is what occupancy needs and what the real corpus lacks.

Non-detections are generated here rather than asked of the extraction agents.
An agent reports the steps it found and the documents it read in full; every
step in the universe that it did not find in a document it read is a reviewed
non-detection. Asking an agent to emit a row per step per document invites
both fatigue and invention, and the negative space is derivable exactly.

Reads only rendered artifacts and the agents' own extraction files. Reads no
truth, specs, ceilings or scores; scoring against truth happens in a separate,
explicitly recorded evaluation step.
"""
from __future__ import annotations

import collections
import json

from . import solar_sources as S

WORLD = "W2_DEV_001"
STATUTE = "S07"
ARTIFACTS = S.ROOT / f"benchmark/synth/worlds/{WORLD}/artifacts"
DIR = S.ROOT / "runs/process_structure_20260921/synthetic_solar"

# How a document kind is treated as an instrument. Kinds differ in how reliably
# they mention a step that exists, which is the quantity occupancy estimates.
SOURCE_TYPE = {
    "ordinance": "local_law",
    "council_minutes": "local_law",
    "fee_resolution": "local_law",
    "checklist": "agency_instruction",
    "form": "agency_instruction",
    "program_page": "agency_instruction",
    "faq": "agency_instruction",
    "staff_report": "agency_internal",
    "news": "press",
    "reddit": "applicant_account",
    "forum_thread": "applicant_account",
}

DETECTION_PRIOR = {
    "local_law": [2.5, 1.5],
    "agency_instruction": [2.5, 1.5],
    "agency_internal": [2.0, 2.0],
    "press": [1.2, 3.0],
    "applicant_account": [1.2, 3.0],
}
FALSE_POSITIVE = {"local_law": .01, "agency_instruction": .01,
                  "agency_internal": .02, "press": .05, "applicant_account": .05}


# Counties named the same step differently. Merging plain synonyms is necessary
# or the universe double-counts; merging anything looser would manufacture
# cross-county agreement, which is precisely the quantity being estimated. So
# only unambiguous synonyms are merged, and the near-misses are deliberately
# left apart with the reason recorded.
ALIASES = {
    # the fire authority's sign-off, named three ways
    "obtain_fire_prevention_clearance": "obtain_fire_clearance",
    "obtain_fire_marshal_signoff": "obtain_fire_clearance",
    # publishing the register of issued permits, named three ways
    "publish_register_of_issued_permits": "publish_public_permit_register",
    "maintain_public_permit_registry": "publish_public_permit_register",
    "update_public_permit_register": "publish_public_permit_register",
    # correcting and resubmitting after a rejection
    "resubmit_after_correction_notice": "resubmit_after_correction",
    "submit_corrections_after_review_rejection": "resubmit_after_correction",
}

NOT_MERGED = {
    "screen_submittal_for_completeness vs screen_application_at_counter": (
        "One is a back-office completeness screen and the other happens at a public "
        "counter. The channel is the burden: attending in person is not the same demand "
        "as waiting. Kept separate."),
    "manual_review_when_automated_check_fails vs documents_review_in_reviewer_queue": (
        "One is a fallback triggered when the automated check does not clear, the other a "
        "standing queue every submittal waits in. Merging them would assert that two "
        "counties do the same thing when one does it only on failure. Kept separate."),
}


def canonical(step_id: str) -> str:
    return ALIASES.get(step_id, step_id)


def document_kind(filename: str) -> str:
    stem = filename.rsplit("__", 1)[-1].removesuffix(".md")
    for kind in SOURCE_TYPE:
        if stem.startswith(kind):
            return kind
    return stem


def build():
    vocabulary = json.loads((DIR / "statute_vocabulary.json").read_text())
    counties = sorted(DIR.glob("county_*.json"))
    if not counties:
        raise SystemExit("no county extraction files yet")

    # Not every step in the statute vocabulary is established BY the statute. Four
    # of the nineteen appear only in the bill analysis, which describes expected
    # local practice or points at other law. Labelling those statutory would put
    # county-added burden on the statute's side of the ledger, which is the exact
    # error the layer split exists to prevent.
    steps = {}
    for step in vocabulary["steps"]:
        source = str(step.get("source_file", ""))
        statutory = source.endswith("S07__statute_text.md")
        steps[step["step_id"]] = {
            **step,
            "layer_label": "statutory" if statutory else "described_in_analysis_not_enacted",
            "named_in": ["statute" if statutory else "bill_analysis"]}

    county_data = {}
    for path in counties:
        blob = json.loads(path.read_text())
        county_data[blob["county"]] = blob
        for step in blob.get("new_steps", []):
            step_id = canonical(step["step_id"])
            existing = steps.get(step_id)
            if existing is None:
                steps[step_id] = {**step, "step_id": step_id,
                                  "layer_label": "administrative-or-applicant-only",
                                  "named_in": [blob["county"]],
                                  "aliases": sorted({step["step_id"]})}
            else:
                if blob["county"] not in existing["named_in"]:
                    existing["named_in"].append(blob["county"])
                existing["aliases"] = sorted(set(existing.get("aliases", [])) | {step["step_id"]})

    # An applicant-only step is one no law and no agency document ever names.
    positives_by_kind = collections.defaultdict(set)
    for county, blob in county_data.items():
        for hit in blob.get("detections", []):
            kind = SOURCE_TYPE.get(document_kind(hit["file"]), "applicant_account")
            positives_by_kind[canonical(hit["step_id"])].add(kind)
    for step_id, step in steps.items():
        if step["layer_label"] == "statutory":
            continue
        if step["layer_label"] == "described_in_analysis_not_enacted" and step_id not in positives_by_kind:
            continue
        kinds = positives_by_kind.get(step_id, set())
        if kinds and kinds <= {"applicant_account", "press"}:
            step["layer_label"] = "applicant-only"
        elif kinds:
            step["layer_label"] = "administrative-only"

    # A step reported under new_steps carries its own quote and source file. That
    # IS a positive reading and must enter the detection table, or the step exists
    # in the universe with no evidence anywhere and the posterior drives it to
    # zero in the very county that reported it. Three of the four extractions
    # listed their local steps only under new_steps, which produced exactly that
    # failure on the first pass and was caught by scoring against truth.
    promoted = 0
    for county, blob in county_data.items():
        listed = {(canonical(h["step_id"]), h["file"]) for h in blob.get("detections", [])}
        for step in blob.get("new_steps", []):
            source = step.get("source_file")
            key = (canonical(step["step_id"]), source)
            if source and key not in listed:
                blob.setdefault("detections", []).append({
                    "step_id": step["step_id"], "file": source,
                    "quote": step.get("quote", ""),
                    "promoted_from": "new_steps"})
                listed.add(key)
                promoted += 1

    observations = []
    for county, blob in county_data.items():
        found = collections.defaultdict(set)
        quotes = {}
        for hit in blob.get("detections", []):
            step_id = canonical(hit["step_id"])
            found[hit["file"]].add(step_id)
            quotes[(hit["file"], step_id)] = hit.get("quote", "")
        # A document that says a step does NOT happen is a non-detection, which is
        # what it already is by omission. It must never become a detection.
        for miss in blob.get("explicit_absences", []):
            found.get(miss["file"], set()).discard(canonical(miss["step_id"]))
        for document in blob["documents_reviewed"]:
            filename = document["file"]
            path = ARTIFACTS / filename
            if not path.exists():
                continue
            kind = SOURCE_TYPE.get(document_kind(filename))
            if kind is None:
                continue
            base = S.ref(path, "whole document reviewed against the step universe")
            for step_id in steps:
                detected = step_id in found.get(filename, set())
                locator = (f"quote: {quotes[(filename, step_id)][:120]}" if detected
                           else f"reviewed in full, no mention of {step_id}")
                observations.append({
                    "jurisdiction_id": county, "step_id": step_id,
                    "source_type": kind, "detected": detected, "reviewed_scope": True,
                    "unit_id": f"{county}::{filename}",
                    "dependence_group_id": f"{county}::{filename}",
                    "evidence_refs": [{**base, "locator": locator}],
                })

    used_kinds = sorted({o["source_type"] for o in observations})
    evidence = {
        "schema_version": "process-occupancy-evidence/1",
        "scope": (f"Synthetic statute {STATUTE} in world {WORLD} as implemented by "
                  f"{len(county_data)} counties. Presence of a step in a county's process, read "
                  "from its rendered documents only."),
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": (
            "Each rendered document is one reading opportunity, reviewed in full against the "
            "whole step universe, so a step absent from a document it was looked for in is a "
            "reviewed non-detection rather than missing evidence. Documents of the same kind in "
            "the same county are treated as conditionally independent given presence, which is "
            "generous: a county's checklist and its form are written by the same office and may "
            "repeat each other's omissions. No truth, spec or ceiling was read in building this."),
        "jurisdictions": sorted(county_data),
        "steps": sorted(steps),
        "source_types": used_kinds,
        "source_models": {kind: {"detection_beta": DETECTION_PRIOR[kind],
                                 "false_positive_probability": FALSE_POSITIVE[kind]}
                          for kind in used_kinds},
        "observations": observations,
        "known_presence": [],
    }
    (DIR / "occupancy_evidence.json").write_text(json.dumps(evidence))
    with (DIR / "step_universe.jsonl").open("w") as fh:
        for step in sorted(steps.values(), key=lambda s: s["step_id"]):
            fh.write(json.dumps(step, sort_keys=True) + "\n")

    per_county = collections.Counter(o["jurisdiction_id"] for o in observations)
    summary = {
        "world": WORLD, "statute": STATUTE,
        "counties": sorted(county_data), "steps_in_universe": len(steps),
        "steps_by_layer": dict(collections.Counter(s["layer_label"] for s in steps.values())),
        "documents_read": sum(len(b["documents_reviewed"]) for b in county_data.values()),
        "source_types": used_kinds,
        "reading_opportunities": len(observations),
        "positive_detections": sum(1 for o in observations if o["detected"]),
        "readings_per_county": dict(per_county),
        "repeat_readings_per_step_and_county": (
            len(observations) / max(1, len(steps) * len(county_data))),
        "county_specific_steps_promoted_to_detections": promoted,
        "aliases_merged": ALIASES,
        "deliberately_not_merged": NOT_MERGED,
        "why_this_beats_the_real_corpus": (
            "Every county is read by six to nine documents of four or five different kinds, so "
            "the same step is looked for many times in the same place. Real solar had one survey "
            "answer per authority and no way to tell a missing step from a missing mention."),
    }
    (DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
