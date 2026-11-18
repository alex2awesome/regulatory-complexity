"""Source-free tests for deterministic S07 structural-source materialization."""
from __future__ import annotations

import copy
import json

import pytest

from benchmark.synth.generator.s07_structural_sources import (
    EXPECTED_PHASE_EVENT_DEPENDENCIES,
    EXPECTED_PROFILES,
    EXPECTED_UTILITIES,
    JURISDICTIONS,
    StructuralSourceError,
    canonical_charge_key,
    canonical_json_bytes,
    materialize_structural_sources,
    provisional_source_hashes,
    public_structural_projection,
    validate_resolved_source,
    write_provisional_sources,
)


def authority(jid, kind, issuer):
    suffix = "AHJ" if kind == "ahj" else "UTILITY"
    return {
        "authority_claim_id": f"{jid}.AUTH.{suffix}",
        "fictional_issuer_id": issuer,
        "jurisdiction_id": jid,
        "authority_kind": f"fictional {kind} rule",
        "effective_start": "2024-09-01",
        "effective_end": "2026-08-31",
        "scope": f"fictional {kind} scope for {jid}",
        "public_citation_label": f"{jid} {kind} rule (fictional)",
    }


def fixture_packets():
    shared = {
        "world_id": "S07_PILOT_20260920_R01",
        "applicant_encounters": [{
            "encounter_id": "${jid}.ENC.SUBMIT",
            "actor_id": "applicant_installer",
            "actor_type": "installer_applicant",
            "action": "submit fictional packet",
            "object": "solar packet",
            "recipient_or_counterparty": "${ahj_actor}",
            "trigger": "design_complete",
            "phase_id": "ahj_permit",
            "route_applicability": ["parallel_standard", "serial_standard", "no_preinstall_approval"],
            "required_status": "required",
            "submission_or_contact_channel": "fictional portal",
            "authority_claim_id": "${ahj_authority}",
            "prerequisite_encounter_ids": [],
        }],
        "required_documents": [{
            "document_requirement_id": "${jid}.DOC.PLAN",
            "public_name": "fictional plan",
            "supplied_by_actor_type": "installer_applicant",
            "received_by_actor_type": "ahj",
            "trigger": "initial submission",
            "phase_id": "ahj_permit",
            "route_applicability": ["parallel_standard", "serial_standard", "no_preinstall_approval"],
            "required_status": "required",
            "authority_claim_id": "${ahj_authority}",
            "accepted_variants": ["digital plan"],
            "copy_count": 1,
        }],
        "checklist_items": [{
            "checklist_item_id": "${jid}.CHK.MATCH",
            "responsible_actor_type": "ahj_inspector",
            "action": "compare installation",
            "evidence_or_object": "approved fictional plan",
            "trigger": "inspection",
            "phase_id": "ahj_inspection",
            "route_applicability": ["parallel_standard", "serial_standard", "no_preinstall_approval"],
            "pass_fail_effect": "mismatch requires correction",
            "authority_claim_id": "${ahj_authority}",
        }],
    }
    fee_template = {
        "fee_key": "base",
        "charge_id": "${jid}.FEE.BASE",
        "public_name": "fictional base charge",
        "amount": "${fee_amounts.base}",
        "currency": "Fictional USD",
        "payer_actor_type": "applicant_customer",
        "collector_actor_id": "${ahj_actor}",
        "authority_claim_id": "${ahj_authority}",
        "trigger": "initial permit submission",
        "phase_id": "ahj_permit",
        "route_applicability": ["parallel_standard", "serial_standard", "no_preinstall_approval"],
        "frequency": "once_per_case",
        "refundable_status": "nonrefundable",
        "waiver_or_exemption_rule": None,
        "effective_start": "2024-09-01",
        "effective_end": "2026-08-31",
    }
    jurisdictions = []
    for index, jid in enumerate(JURISDICTIONS, 1):
        utility = EXPECTED_UTILITIES[jid]
        ahj_actor = f"{jid} Fictional Office"
        utility_actor = f"{utility} Fictional Desk"
        jurisdictions.append({
            "jurisdiction_id": jid,
            "profile": EXPECTED_PROFILES[jid],
            "utility_id": utility,
            "bindings": {
                "jid": jid,
                "ahj_actor": ahj_actor,
                "utility_actor": utility_actor,
                "ahj_authority": f"{jid}.AUTH.AHJ",
                "utility_authority": f"{jid}.AUTH.UTILITY",
            },
            "authorities": [authority(jid, "ahj", ahj_actor), authority(jid, "utility", utility_actor)],
            "fee_amounts": {"base": index},
            "worked_totals": [
                {
                    "example_id": f"base_{route}",
                    "route": route,
                    "multiplicities": {"base": 1},
                    "total": index,
                }
                for route in ("parallel_standard", "serial_standard", "no_preinstall_approval")
            ],
        })
    part1 = {"world_id": "S07_PILOT_20260920_R01", "jurisdictions": []}
    part2 = {
        "world_id": "S07_PILOT_20260920_R01",
        "fee_row_templates": [fee_template],
        "jurisdictions": jurisdictions,
    }
    phase_dependencies = [
        {"route": route, "event": event, "mode": mode, "requires": list(requires)}
        for route, event, mode, requires in EXPECTED_PHASE_EVENT_DEPENDENCIES
    ]
    known_events = sorted({
        item
        for _, event, _, requires in EXPECTED_PHASE_EVENT_DEPENDENCIES
        for item in (event, *requires)
    })
    design = {
        "schema_version": "s07_structural_additive_event_fee_design/2",
        "predecessor_sha256": "b8f468ea7d365f0dfbfc5c773e1c393f9f9c4c2d366369323c9c2750e3172004",
        "world_id": "S07_PILOT_20260920_R01",
        "known_routes": ["parallel_standard", "serial_standard", "no_preinstall_approval"],
        "known_events": known_events,
        "encounter_event_prerequisites": {
            "${jid}.ENC.SUBMIT": {"mode": "all_of", "events": ["design_complete"]},
        },
        "phase_event_dependencies": phase_dependencies,
        "phase_rule_materialization": {
            "resolved_collection": "phase_event_dependencies",
            "publicly_projected": True,
            "rule_id_components": ["jurisdiction_id", "route", "event"],
            "source_lineage_fields": ["source_design_schema", "source_rule_index"],
            "source_rule_index_semantics": "zero-based index into this design's phase_event_dependencies array",
            "qualification": "The resolved rows restate this fictional design rule with jurisdiction-local identity; they do not assert real law.",
        },
        "fee_schedule_lock": {
            "applicability_date_basis": "case_schedule_version_locked_at_event",
            "applicability_date_event": "first_permit_submission",
            "eligible_initial_date_start": "2024-09-01",
            "eligible_initial_date_end": "2026-08-31",
            "locked_through_case_completion": True,
            "later_required_steps_and_repeats_use_locked_version": True,
            "after_cutoff_private_future_may_use_locked_version": True,
            "public_claims_must_remain_cutoff_safe": True,
            "no_new_schedule_after_effective_end_is_invented": True,
        },
        "money_unit_normalization": {
            "source_currency_label": "Fictional USD",
            "materialized_currency_code": "USD",
            "price_status": "fictional_design_price",
            "normalization_method": "label normalization only; no FX conversion",
            "amounts_unchanged": True,
            "fx_conversion_performed": False,
            "public_disclaimer": "Fictional dollar-denominated prices only.",
        },
        "actor_assumption": {
            "filer_actor_id": "applicant_installer",
            "filer_actor_type": "installer_applicant",
            "represented_party_actor_id": "applicant_customer",
            "represented_party_actor_type": "customer_owner",
            "fee_payer_actor_id": "applicant_customer",
            "fee_payer_actor_type": "applicant_customer",
            "relationship": "installer files for the customer owner; customer pays",
        },
        "expected_materialized_counts_per_jurisdiction": {
            "authorities": 2,
            "applicant_encounters": 1,
            "required_documents": 1,
            "checklist_items": 1,
            "fee_schedule": 1,
            "worked_fee_examples": 3,
            "phase_event_dependencies": len(phase_dependencies),
        },
        "public_collection_whitelist": [
            "schema_version", "world_id", "jurisdiction_id", "utility_id", "actors", "money_context",
            "authorities", "phase_event_dependencies", "applicant_encounters", "required_documents",
            "checklist_items", "fee_schedule",
        ],
        "public_forbidden_design_fields": [
            "profile", "bindings", "worked_fee_examples", "source_hashes",
            "materialization_receipt", "evaluation_split", "partition_role",
        ],
    }
    return shared, part1, part2, design


def materialized():
    return materialize_structural_sources(*fixture_packets())


def test_materializes_exactly_twelve_deterministically_with_typed_mechanics():
    first = materialized()
    second = materialized()
    assert first == second
    assert set(first) == set(JURISDICTIONS)
    assert provisional_source_hashes(first) == provisional_source_hashes(second)
    row = first["R01J01"]
    assert row["applicant_encounters"][0]["event_prerequisites"] == ["design_complete"]
    assert row["fee_schedule"][0]["applicability_date_event"] == "first_permit_submission"
    assert row["fee_schedule"][0]["locked_through_case_completion"] is True
    assert row["fee_schedule"][0]["currency"] == "USD"
    assert len(row["phase_event_dependencies"]) == len(EXPECTED_PHASE_EVENT_DEPENDENCIES)
    assert row["phase_event_dependencies"][2]["event"] == "final_permit_approval"
    assert row["phase_event_dependencies"][2]["requires"] == ["first_permit_submission"]
    assert row["phase_event_dependencies"][2]["source_rule_index"] == 2
    assert row["money_context"]["price_status"] == "fictional_design_price"
    assert row["money_context"]["fx_conversion_performed"] is False
    assert row["actors"]["filer_actor_id"] == "applicant_installer"
    assert row["actors"]["represented_party_actor_id"] == "applicant_customer"
    assert row["actors"]["fee_payer_actor_id"] == "applicant_customer"
    assert "profile" not in row and "bindings" not in row


def test_canonical_charge_key_and_totals_are_materialized_and_validated():
    sources = materialized()
    row = sources["R01J12"]
    fee = row["fee_schedule"][0]
    assert fee["canonical_charge_key"] == canonical_charge_key(fee)
    charge_id = fee["charge_id"]
    assert row["worked_fee_examples"][0]["multiplicities"] == {charge_id: 1}
    validate_resolved_source(row, fixture_packets()[3])


def test_public_projection_is_exact_whitelist_without_design_or_worked_metadata():
    shared, part1, part2, design = fixture_packets()
    source = materialize_structural_sources(shared, part1, part2, design)["R01J03"]
    public = public_structural_projection(source, design)
    assert set(public) == set(design["public_collection_whitelist"])
    assert public["schema_version"] == "s07-public-structural-source/2"
    assert public["phase_event_dependencies"] == source["phase_event_dependencies"]
    encoded = json.dumps(public)
    for forbidden in design["public_forbidden_design_fields"]:
        assert forbidden not in encoded


def test_write_is_canonical_twelve_files_and_refuses_existing_destination(tmp_path):
    sources = materialized()
    output = tmp_path / "resolved"
    hashes = write_provisional_sources(sources, output)
    assert len(list(output.glob("R01J*.json"))) == 12
    assert set(hashes) == set(JURISDICTIONS)
    assert (output / "R01J01.json").read_bytes() == canonical_json_bytes(sources["R01J01"])
    with pytest.raises(StructuralSourceError, match="already exists"):
        write_provisional_sources(sources, output)


@pytest.mark.parametrize("token", ["${unknown}", "${fee_amounts.missing}", "${unterminated"])
def test_unknown_missing_or_malformed_tokens_fail(token):
    shared, part1, part2, design = fixture_packets()
    shared["applicant_encounters"][0]["action"] = token
    with pytest.raises(StructuralSourceError, match="token"):
        materialize_structural_sources(shared, part1, part2, design)


def test_missing_binding_fails_without_default():
    shared, part1, part2, design = fixture_packets()
    del part2["jurisdictions"][0]["bindings"]["ahj_actor"]
    with pytest.raises(StructuralSourceError, match="binding"):
        materialize_structural_sources(shared, part1, part2, design)


@pytest.mark.parametrize("target", ["fee", "copy", "multiplicity"])
def test_boolean_counts_and_amounts_are_rejected(target):
    shared, part1, part2, design = fixture_packets()
    if target == "fee":
        part2["jurisdictions"][0]["fee_amounts"]["base"] = True
    elif target == "copy":
        shared["required_documents"][0]["copy_count"] = True
    else:
        part2["jurisdictions"][0]["worked_totals"][0]["multiplicities"]["base"] = True
    with pytest.raises(StructuralSourceError, match="boolean"):
        materialize_structural_sources(shared, part1, part2, design)


def test_duplicate_ids_and_jurisdictions_fail():
    shared, part1, part2, design = fixture_packets()
    part2["jurisdictions"].append(copy.deepcopy(part2["jurisdictions"][0]))
    with pytest.raises(StructuralSourceError, match="duplicate jurisdiction"):
        materialize_structural_sources(shared, part1, part2, design)

    shared, part1, part2, design = fixture_packets()
    part2["jurisdictions"][0]["authorities"][1]["authority_claim_id"] = \
        part2["jurisdictions"][0]["authorities"][0]["authority_claim_id"]
    with pytest.raises(StructuralSourceError, match="duplicate authority"):
        materialize_structural_sources(shared, part1, part2, design)


def test_missing_or_cyclic_encounter_prerequisites_fail():
    shared, part1, part2, design = fixture_packets()
    shared["applicant_encounters"][0]["prerequisite_encounter_ids"] = ["${jid}.ENC.MISSING"]
    with pytest.raises(StructuralSourceError, match="unresolved prerequisite"):
        materialize_structural_sources(shared, part1, part2, design)

    shared, part1, part2, design = fixture_packets()
    shared["applicant_encounters"][0]["prerequisite_encounter_ids"] = ["${jid}.ENC.SUBMIT"]
    with pytest.raises(StructuralSourceError, match="cycle"):
        materialize_structural_sources(shared, part1, part2, design)


def test_typed_event_map_must_exactly_cover_templates_and_known_events():
    shared, part1, part2, design = fixture_packets()
    design["encounter_event_prerequisites"] = {}
    with pytest.raises(StructuralSourceError, match="encounter_event_prerequisites"):
        materialize_structural_sources(shared, part1, part2, design)


def test_additive_design_requires_typed_approval_dependencies_and_valid_fee_lock():
    shared, part1, part2, design = fixture_packets()
    design["phase_event_dependencies"][2]["requires"] = ["design_complete"]
    with pytest.raises(StructuralSourceError, match="exact effective design"):
        materialize_structural_sources(shared, part1, part2, design)


def test_currency_label_is_normalized_without_amount_or_fx_change():
    shared, part1, part2, design = fixture_packets()
    sources = materialize_structural_sources(shared, part1, part2, design)
    source = sources["R01J06"]
    assert source["fee_schedule"][0]["amount"] == 6
    assert source["fee_schedule"][0]["currency"] == "USD"
    assert source["money_context"]["amounts_unchanged"] is True
    assert source["money_context"]["fx_conversion_performed"] is False

    shared, part1, part2, design = fixture_packets()
    part2["fee_row_templates"][0]["currency"] = "EUR"
    with pytest.raises(StructuralSourceError, match="reviewed fictional label"):
        materialize_structural_sources(shared, part1, part2, design)

    shared, part1, part2, design = fixture_packets()
    design["fee_schedule_lock"]["eligible_initial_date_end"] = "2024-08-31"
    with pytest.raises(StructuralSourceError, match="eligible dates are reversed"):
        materialize_structural_sources(shared, part1, part2, design)


def test_unknown_resolved_fields_and_invalid_waiver_type_fail_closed():
    shared, part1, part2, design = fixture_packets()
    row = materialize_structural_sources(shared, part1, part2, design)["R01J01"]
    broken = copy.deepcopy(row)
    broken["profile"] = "B"
    with pytest.raises(StructuralSourceError, match="unknown fields"):
        validate_resolved_source(broken, design)
    broken = copy.deepcopy(row)
    broken["fee_schedule"][0]["waiver_or_exemption_rule"] = False
    with pytest.raises(StructuralSourceError, match="nonempty string"):
        validate_resolved_source(broken, design)

    shared, part1, part2, design = fixture_packets()
    design["encounter_event_prerequisites"]["${jid}.ENC.SUBMIT"]["events"] = ["invented"]
    with pytest.raises(StructuralSourceError, match="unknown event"):
        materialize_structural_sources(shared, part1, part2, design)


@pytest.mark.parametrize("target", ["encounter", "document", "fee"])
def test_preinstall_declarations_forbid_no_preinstall_route(target):
    shared, part1, part2, design = fixture_packets()
    if target == "encounter":
        shared["applicant_encounters"][0]["phase_id"] = "preinstall_ix"
    elif target == "document":
        shared["required_documents"][0]["phase_id"] = "preinstall_ix"
    else:
        part2["fee_row_templates"][0]["phase_id"] = "preinstall_ix"
    with pytest.raises(StructuralSourceError, match="forbidden on no_preinstall_approval"):
        materialize_structural_sources(shared, part1, part2, design)


def test_worked_totals_enforce_fee_frequency_even_when_arithmetic_matches():
    shared, part1, part2, design = fixture_packets()
    row = materialize_structural_sources(shared, part1, part2, design)["R01J01"]
    broken = copy.deepcopy(row)
    charge_id = broken["fee_schedule"][0]["charge_id"]
    amount = broken["fee_schedule"][0]["amount"]
    broken["worked_fee_examples"][0]["multiplicities"][charge_id] = 2
    broken["worked_fee_examples"][0]["total"] = 2 * amount
    with pytest.raises(StructuralSourceError, match="multiplicity one"):
        validate_resolved_source(broken, design)


def test_phase_rule_lineage_tampering_fails_resolved_validation():
    shared, part1, part2, design = fixture_packets()
    row = materialize_structural_sources(shared, part1, part2, design)["R01J01"]
    broken = copy.deepcopy(row)
    broken["phase_event_dependencies"][2]["requires"] = ["design_complete"]
    with pytest.raises(StructuralSourceError, match="exact source design rule"):
        validate_resolved_source(broken, design)


def test_authority_route_and_date_contracts_fail_closed():
    shared, part1, part2, design = fixture_packets()
    shared["required_documents"][0]["authority_claim_id"] = "${jid}.AUTH.MISSING"
    with pytest.raises(StructuralSourceError, match="unresolved authority"):
        materialize_structural_sources(shared, part1, part2, design)

    shared, part1, part2, design = fixture_packets()
    shared["checklist_items"][0]["route_applicability"] = ["invented"]
    with pytest.raises(StructuralSourceError, match="known routes"):
        materialize_structural_sources(shared, part1, part2, design)

    shared, part1, part2, design = fixture_packets()
    part2["jurisdictions"][0]["authorities"][0]["effective_end"] = "2024-08-31"
    with pytest.raises(StructuralSourceError, match="reversed"):
        materialize_structural_sources(shared, part1, part2, design)


def test_canonical_key_fee_lock_and_total_tampering_fail_validation():
    shared, part1, part2, design = fixture_packets()
    row = materialize_structural_sources(shared, part1, part2, design)["R01J01"]
    broken = copy.deepcopy(row)
    broken["fee_schedule"][0]["canonical_charge_key"] = "wrong"
    with pytest.raises(StructuralSourceError, match="noncanonical"):
        validate_resolved_source(broken, design)
    broken = copy.deepcopy(row)
    broken["fee_schedule"][0]["applicability_date_event"] = "later_fee_trigger"
    with pytest.raises(StructuralSourceError, match="wrong applicability"):
        validate_resolved_source(broken, design)
    broken = copy.deepcopy(row)
    broken["worked_fee_examples"][0]["total"] += 1
    with pytest.raises(StructuralSourceError, match="total mismatch"):
        validate_resolved_source(broken, design)


def test_public_whitelist_cannot_add_profile_or_design_metadata():
    shared, part1, part2, design = fixture_packets()
    row = materialize_structural_sources(shared, part1, part2, design)["R01J01"]
    design["public_collection_whitelist"].append("profile")
    with pytest.raises(StructuralSourceError, match="whitelist differs"):
        public_structural_projection(row, design)
