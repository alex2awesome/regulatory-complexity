"""Build the occupancy evidence contract from a synthetic test-bed.

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
import re

from . import solar_sources as S

WORLD = "W2_DEV_001"
ARTIFACTS = S.ROOT / f"benchmark/synth/worlds/{WORLD}/artifacts"
PACKETS = {
    "S07": S.ROOT / "runs/process_structure_20260921/synthetic_solar",
    "S05": S.ROOT / "runs/process_structure_20260921/synthetic_s05",
}

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
    "sop": "agency_internal",
    "official_stats": "agency_internal",
    "audit_excerpt": "agency_internal",
    "third_party_guide": "third_party_guide",
    "news": "press",
    "reddit": "applicant_account",
    "forum_thread": "applicant_account",
}

DETECTION_PRIOR = {
    "local_law": [2.5, 1.5],
    "agency_instruction": [2.5, 1.5],
    "agency_internal": [2.0, 2.0],
    "third_party_guide": [1.5, 2.5],
    "press": [1.2, 3.0],
    "applicant_account": [1.2, 3.0],
}
FALSE_POSITIVE = {"local_law": .01, "agency_instruction": .01,
                  "agency_internal": .02, "third_party_guide": .03,
                  "press": .05, "applicant_account": .05}


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


# ---------------------------------------------------------------- S05 aliases
# Twenty-four extractions produced 78 distinct labels for a nine-step statute.
# Most of that is wording, not process: eleven counties call the fee step
# pay_registration_fee and four call it pay_application_fee. Left alone the
# universe fragments and every county looks unique, which is the opposite of
# what occupancy is meant to measure.
#
# The rule is the one used for S07. Merge plain synonyms. Where two labels name
# genuinely different acts, keep them apart and record why in S05_NOT_MERGED,
# because over-merging manufactures the cross-jurisdiction agreement being
# estimated while under-merging only costs a rare step.
S05_ALIASES = {
    # paying, collecting and reconciling the fee
    "pay_application_fee": "pay_registration_fee",
    "pay_application_fees": "pay_registration_fee",
    "pay_program_fee": "pay_registration_fee",
    "collect_registration_fee": "pay_registration_fee",
    "reconcile_deposit_against_cost_recovery_account": "reconcile_fees_with_finance",
    "reconcile_fee": "reconcile_fees_with_finance",
    "reconcile_fees": "reconcile_fees_with_finance",
    # the public notice, mailed and posted together
    "mail_and_post_required_public_notice": "mail_and_post_public_notice",
    "notice_neighbours_and_post_site": "mail_and_post_public_notice",
    "notice_neighbors_and_post_site": "mail_and_post_public_notice",
    "post_notice_on_property_for_10_days": "post_notice_on_property",
    "send_courtesy_notice_to_adjacent_property_owners": "send_courtesy_notice_to_adjacent_owners",
    "mail_neighbour_notice": "mail_notice_to_neighbours",
    "mail_notice_to_neighbours_300_feet": "mail_notice_to_neighbours",
    "print_stuff_and_mail_notice_batch": "print_and_mail_notice_batch",
    # filing through the portal
    "create_portal_account_and_upload_documents": "register_in_online_permit_center",
    "create_portal_account_and_submit_electronically": "register_in_online_permit_center",
    "submit_application_electronically": "register_in_online_permit_center",
    "submit_electronically": "register_in_online_permit_center",
    # the portal status line
    "update_permit_tracking_system_status": "post_status_change_to_portal",
    # the unnamed internal review, and routing the file to whoever performs it
    "internal_review_of_file": "conduct_internal_review_of_file",
    "conduct_internal_review": "conduct_internal_review_of_file",
    "conduct_internal_staff_review": "conduct_internal_review_of_file",
    "route_case_to_reviewer_queue": "assign_case_to_plan_reviewer",
    "route_case_to_assigned_reviewer": "assign_case_to_plan_reviewer",
    "assign_file_to_plan_reviewer": "assign_case_to_plan_reviewer",
    "route_file_for_internal_processing": "assign_case_to_plan_reviewer",
    # checking the proposal against the zoning standards
    "verify_zoning_district_and_use": "clear_application_through_zoning",
    "check_zoning_standards": "clear_application_through_zoning",
    "plan_check_against_objective_zoning_standards": "clear_application_through_zoning",
    # closing the file
    "scan_and_archive_case_file_to_records_management": "scan_and_archive_case_file",
    # the standards handout, published by the agency and completed by the applicant
    "publish_objective_standards_handout": "publish_objective_standards",
    "complete_standards_handout_before_inspection": "complete_objective_standards_handout",
    "prepare_inspection_handout": "complete_objective_standards_handout",
    # the public performance dashboard
    "publish_program_counts_dashboard": "publish_program_performance_statistics",
    "publish_aggregate_performance_statistics": "publish_program_performance_statistics",
    # the business tax record, agency side and applicant side
    "link_business_license_record": "open_or_update_business_tax_account",
    "link_case_to_business_license_account": "open_or_update_business_tax_account",
    "obtain_business_tax_certificate": "register_business_concurrently",
    # the owner's authorisation, however it is papered
    "obtain_property_owner_authorization": "sign_and_notarise_owner_affidavit",
    "obtain_owner_consent_letter": "sign_and_notarise_owner_affidavit",
    # two-yearly renewal by self-certification
    "renew_registration_with_self_certification": "self_certify_biennial_renewal",
    "self_certify_for_biennial_renewal": "self_certify_biennial_renewal",
    "submit_biennial_renewal_self_certification": "self_certify_biennial_renewal",
    "renew_permit_with_self_certification": "self_certify_biennial_renewal",
    "file_biennial_renewal_self_certification": "self_certify_biennial_renewal",
    # labels that arrived with the last five counties
    "mail_courtesy_notice_to_adjacent_property_owners": "send_courtesy_notice_to_adjacent_owners",
    "check_proposal_against_objective_standards": "clear_application_through_zoning",
    "index_and_archive_closed_case": "scan_and_archive_case_file",
    "route_file_internally": "assign_case_to_plan_reviewer",
    "conduct_internal_file_review": "conduct_internal_review_of_file",
}

S05_NOT_MERGED = {
    "screen_application_at_counter vs determine_completeness_of_submittal": (
        "Kept apart. Counter screening is an in-person stage applicants time separately; the "
        "statutory completeness determination is what starts the 15-day clock. No document ties "
        "the two. KNOWN INCONSISTENCY: the split was noticed part way through, so the earlier "
        "extractions for C09, C25, C26, C47 and C48 folded counter screening into "
        "determine_completeness_of_submittal, while the later ones label it separately. Those "
        "five are not re-labelled here because doing so would overwrite what the extractor "
        "actually read, so the completeness step is over-detected in exactly those five and any "
        "result that turns on it must say so."),
    "post_notice_on_property vs mail_and_post_public_notice": (
        "One is the physical sign on the applicant's own house, which several counties time as "
        "its own multi-day stage; the other is the combined mail-and-post act. Counties that "
        "describe them together keep the combined step; counties describing only the sign keep "
        "the narrower one."),
    "send_notice_of_application vs mail_notice_to_neighbours vs send_courtesy_notice_to_adjacent_owners": (
        "Three notices with different recipients: the world at large, neighbours within a stated "
        "radius, and adjacent owners as a courtesy. Counties run different combinations, so "
        "collapsing them would erase the variation the model exists to find."),
    "deposit_fee_to_programme_account vs reconcile_fees_with_finance": (
        "Depositing money and reconciling an account are two acts by different offices, and one "
        "county names both."),
    "issue_registration_certificate vs issue_ministerial_decision": (
        "Several extractors flagged that their county times the certificate separately from the "
        "decision. Where a county named it separately it stays separate; no county's single "
        "decision is silently split into two."),
    "renew_registration_annually vs self_certify_biennial_renewal": (
        "Not merged, and the difference is the point. One county renews the registration every "
        "year with the business licence; the others self-certify every two years. Collapsing "
        "them would hide a doubling of a recurring applicant burden behind a shared label."),
    "retain_applicant_copy_of_application vs retain_application_and_decision_records": (
        "The applicant keeping their own copy is not the agency's three-year retention duty. "
        "Different actor, different burden, and only one of them is statutory."),
    "review_standards_handout_with_applicant vs screen_application_at_counter": (
        "Counter staff walking an applicant through the standards handout happens before "
        "anything is filed. Screening happens to a submitted application. The extractor was "
        "explicit that these are separate interactions in its county."),
    "register_business_concurrently vs open_or_update_business_tax_account": (
        "The applicant registering a business and the agency opening a tax account are different "
        "actors doing different work, even though they concern one record."),
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


def document_kind(filename: str) -> str:
    """Map a rendered artifact's filename to its document kind.

    Exact match first, then a numbered variant such as reddit_3, and only then a
    prefix. Prefix matching alone is wrong and was: "forum_thread" begins with
    "form", so every forum thread was being typed as an agency form, which
    quietly moved applicant evidence into the agency-instruction source type and
    biased both detection probabilities. Found while extending this to S05.
    """
    stem = filename.rsplit("__", 1)[-1].removesuffix(".md")
    if stem in SOURCE_TYPE:
        return stem
    base = re.sub(r"_\d+$", "", stem)
    if base in SOURCE_TYPE:
        return base
    for kind in SOURCE_TYPE:
        if stem.startswith(kind):
            return kind
    return stem


def build(statute="S07", aliases=None):
    directory = PACKETS[statute]
    # Alias maps are strictly per statute. Merging them let an S07 entry rename an
    # S05 step that four counties had named independently, which is exactly the
    # silent cross-contamination the extraction prompts spend a paragraph guarding
    # against. Different statutes, different vocabularies.
    by_statute = {"S07": ALIASES, "S05": S05_ALIASES}
    alias_map = aliases if aliases is not None else by_statute[statute]

    def canon(step_id):
        return alias_map.get(step_id, step_id)

    vocabulary = json.loads((directory / "statute_vocabulary.json").read_text())
    counties = sorted(directory.glob("county_*.json"))
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
        statutory = source.endswith(f"{statute}__statute_text.md")
        steps[step["step_id"]] = {
            **step,
            "layer_label": "statutory" if statutory else "described_in_analysis_not_enacted",
            "named_in": ["statute" if statutory else "bill_analysis"]}

    county_data = {}
    for path in counties:
        blob = json.loads(path.read_text())
        county_data[blob["county"]] = blob
        for step in blob.get("new_steps", []):
            step_id = canon(step["step_id"])
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
            positives_by_kind[canon(hit["step_id"])].add(kind)
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
        listed = {(canon(h["step_id"]), h["file"]) for h in blob.get("detections", [])}
        for step in blob.get("new_steps", []):
            source = step.get("source_file")
            key = (canon(step["step_id"]), source)
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
            step_id = canon(hit["step_id"])
            found[hit["file"]].add(step_id)
            quotes[(hit["file"], step_id)] = hit.get("quote", "")
        # A document that says a step does NOT happen is a non-detection, which is
        # what it already is by omission. It must never become a detection.
        for miss in blob.get("explicit_absences", []):
            found.get(miss["file"], set()).discard(canon(miss["step_id"]))
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
        "scope": (f"Synthetic statute {statute} in world {WORLD} as implemented by "
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
    (directory / "occupancy_evidence.json").write_text(json.dumps(evidence))
    with (directory / "step_universe.jsonl").open("w") as fh:
        for step in sorted(steps.values(), key=lambda s: s["step_id"]):
            fh.write(json.dumps(step, sort_keys=True) + "\n")

    per_county = collections.Counter(o["jurisdiction_id"] for o in observations)
    summary = {
        "world": WORLD, "statute": statute,
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
        "aliases_merged": alias_map,
        "deliberately_not_merged": {"S07": NOT_MERGED, "S05": S05_NOT_MERGED}[statute],
        "why_this_beats_the_real_corpus": (
            "Every county is read by six to nine documents of four or five different kinds, so "
            "the same step is looked for many times in the same place. Real solar had one survey "
            "answer per authority and no way to tell a missing step from a missing mention."),
    }
    (directory / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--statute", default="S07", choices=sorted(PACKETS))
    args = parser.parse_args()
    print(json.dumps(build(args.statute), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
