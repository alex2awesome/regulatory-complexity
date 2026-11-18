"""Source-free tests for the bounded S07 in-memory case mechanics."""
from __future__ import annotations

import copy

import pytest

from benchmark.synth.generator.s07_case_builder import (
    CaseDraws,
    CaseMechanicsConfig,
    DurationDraw,
    DurationSpec,
    S07CaseMechanicsError,
    adjusted_duration,
    build_case_from_draws,
    choose_route,
    draw_case_inputs,
    generate_case,
    repeat_event_offsets,
    subtract_business_days,
    validate_mechanics_config,
)
from benchmark.synth.generator.s07_structural_sources import (
    EXPECTED_PHASE_EVENT_DEPENDENCIES,
    canonical_charge_key,
    validate_resolved_source,
)
from benchmark.synth.generator.s07_fresh_replica import business_days_between


ROUTES = ("parallel_standard", "serial_standard", "no_preinstall_approval")
ALL_EVENTS = sorted({
    value
    for _, event, _, required in EXPECTED_PHASE_EVENT_DEPENDENCIES
    for value in (event, *required)
})


def _design():
    dependencies = [
        {"route": route, "event": event, "mode": mode, "requires": list(required)}
        for route, event, mode, required in EXPECTED_PHASE_EVENT_DEPENDENCIES
    ]
    money = {
        "source_currency_label": "Fictional USD",
        "materialized_currency_code": "USD",
        "price_status": "fictional_design_price",
        "normalization_method": "label normalization only; no FX conversion",
        "amounts_unchanged": True,
        "fx_conversion_performed": False,
        "public_disclaimer": "Fictional dollar-denominated prices only.",
    }
    return {
        "schema_version": "s07_structural_additive_event_fee_design/2",
        "predecessor_sha256": "b8f468ea7d365f0dfbfc5c773e1c393f9f9c4c2d366369323c9c2750e3172004",
        "world_id": "S07_PILOT_20260920_R01",
        "known_routes": list(ROUTES),
        "known_events": ALL_EVENTS,
        "encounter_event_prerequisites": {
            "fixture": {"mode": "all_of", "events": ["design_complete"]},
        },
        "phase_event_dependencies": dependencies,
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
        "money_unit_normalization": money,
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
            "phase_event_dependencies": len(dependencies),
            "applicant_encounters": 20,
            "required_documents": 6,
            "checklist_items": 4,
            "fee_schedule": 6,
            "worked_fee_examples": 3,
        },
        "public_collection_whitelist": [],
        "public_forbidden_design_fields": [],
    }


def _source(design):
    jid = "R01J01"
    ahj = f"{jid}.AUTH.AHJ"
    utility = f"{jid}.AUTH.UTILITY"
    actors = {
        **design["actor_assumption"],
        "ahj_actor": f"{jid} Fictional Office",
        "utility_actor": "U05 Fictional Desk",
    }
    authorities = []
    for suffix, issuer in (("AHJ", actors["ahj_actor"]), ("UTILITY", actors["utility_actor"])):
        authorities.append({
            "authority_claim_id": f"{jid}.AUTH.{suffix}",
            "fictional_issuer_id": issuer,
            "jurisdiction_id": jid,
            "authority_kind": "fictional source-free rule",
            "effective_start": "2024-09-01",
            "effective_end": "2026-08-31",
            "scope": "tiny source-free mechanics fixture",
            "public_citation_label": f"{jid} fixture rule (fictional)",
        })
    phase_rules = [{
        "phase_rule_id": f"{jid}.PHASE_RULE.{row['route']}.{row['event']}",
        "jurisdiction_id": jid,
        **row,
        "source_design_schema": design["schema_version"],
        "source_rule_index": index,
    } for index, row in enumerate(design["phase_event_dependencies"])]

    encounters = []
    base_tokens = {
        "parallel_standard": ("PERMIT", "PREIX", "INSTALL", "INSPECT", "FINALIX"),
        "serial_standard": ("PERMIT", "PREIX", "INSTALL", "INSPECT", "FINALIX"),
        "no_preinstall_approval": ("PERMIT", "INSTALL", "INSPECT", "FINALIX"),
    }
    suffixes = {
        "parallel_standard": "PARALLEL",
        "serial_standard": "SERIAL",
        "no_preinstall_approval": "NOPRE",
    }
    phase_by_token = {
        "PERMIT": "ahj_permit", "PERMIT_CORRECTION": "ahj_permit",
        "PREIX": "preinstall_ix", "INSTALL": "installation",
        "INSPECT": "ahj_inspection", "REINSPECTION": "ahj_inspection",
        "FINALIX": "final_ix_to_pto",
    }
    for route in ROUTES:
        for token in (*base_tokens[route], "PERMIT_CORRECTION", "REINSPECTION"):
            authority = utility if token in ("PREIX", "FINALIX") else ahj
            encounters.append({
                "encounter_id": f"{jid}.ENC.{token}.{suffixes[route]}",
                "actor_id": "applicant_installer",
                "actor_type": "installer_applicant",
                "action": f"perform fictional {token.lower()} action",
                "object": "fictional solar case",
                "recipient_or_counterparty": actors["utility_actor"] if authority == utility else actors["ahj_actor"],
                "trigger": "fixture event",
                "phase_id": phase_by_token[token],
                "route_applicability": [route],
                "required_status": "conditional" if token in ("PERMIT_CORRECTION", "REINSPECTION") else "required",
                "submission_or_contact_channel": "fictional portal",
                "authority_claim_id": authority,
                "prerequisite_encounter_ids": [],
                "event_prerequisite_mode": "all_of",
                "event_prerequisites": ["design_complete"],
            })

    documents = []
    for token, phase, routes, status, condition in (
        ("SITE_PLAN", "ahj_permit", ROUTES, "required", None),
        ("ELECTRICAL", "ahj_permit", ROUTES, "required", None),
        ("EQUIPMENT", "ahj_permit", ROUTES, "required", None),
        ("STORAGE", "ahj_permit", ROUTES, "conditional", "pv_plus_storage only"),
        ("PREIX", "preinstall_ix", ROUTES[:2], "required", None),
        ("PASS", "postinspection_handoff", ROUTES, "required", None),
    ):
        row = {
            "document_requirement_id": f"{jid}.DOC.{token}",
            "public_name": f"fictional {token.lower()} record",
            "supplied_by_actor_type": "installer_applicant",
            "received_by_actor_type": "fictional authority",
            "trigger": "fixture trigger",
            "phase_id": phase,
            "route_applicability": list(routes),
            "required_status": status,
            "authority_claim_id": utility if token == "PREIX" else ahj,
            "accepted_variants": ["fictional digital record"],
            "copy_count": 1,
        }
        if condition:
            row["condition"] = condition
        documents.append(row)

    checklist = [{
        "checklist_item_id": f"{jid}.CHK.{token}",
        "responsible_actor_type": "ahj_inspector",
        "action": "perform fictional check",
        "evidence_or_object": "fictional installation",
        "trigger": "inspection visit",
        "phase_id": "ahj_inspection",
        "route_applicability": list(ROUTES),
        "pass_fail_effect": "fixture pass/fail effect",
        "authority_claim_id": ahj,
    } for token in ("CONFIGURATION", "LABELS", "STORAGE", "PASS_RECORD")]

    fees = []
    fee_specs = (
        ("PERMIT_BASE", 10, ahj, ROUTES, "once_per_case"),
        ("PERMIT_REPEAT", 2, ahj, ROUTES, "once_per_repeat"),
        ("PREIX", 3, utility, ROUTES[:2], "once_per_submission"),
        ("INSPECTION_INITIAL", 4, ahj, ROUTES, "conditional_once"),
        ("REINSPECTION", 5, ahj, ROUTES, "once_per_repeat"),
        ("FINAL_PTO", 6, utility, ROUTES, "conditional_once"),
    )
    for token, amount, authority, routes, frequency in fee_specs:
        row = {
            "charge_id": f"{jid}.FEE.{token}",
            "canonical_charge_key": "pending",
            "public_name": f"fictional {token.lower()} charge",
            "amount": amount,
            "currency": "USD",
            "payer_actor_type": "applicant_customer",
            "collector_actor_id": actors["utility_actor"] if authority == utility else actors["ahj_actor"],
            "authority_claim_id": authority,
            "trigger": "fixture trigger",
            "phase_id": "preinstall_ix" if token == "PREIX" else "ahj_permit",
            "route_applicability": list(routes),
            "frequency": frequency,
            "refundable_status": "nonrefundable",
            "waiver_or_exemption_rule": None,
            "effective_start": "2024-09-01",
            "effective_end": "2026-08-31",
            "applicability_date_basis": "case_schedule_version_locked_at_event",
            "applicability_date_event": "first_permit_submission",
            "locked_through_case_completion": True,
        }
        row["canonical_charge_key"] = canonical_charge_key(row)
        fees.append(row)

    worked = []
    for route in ROUTES:
        multiplicities = {}
        for row in fees:
            applies = route in row["route_applicability"]
            multiplicities[row["charge_id"]] = (
                1 if applies and row["frequency"] != "once_per_repeat" else 0
            )
        worked.append({
            "example_id": f"fixture_{route}",
            "route": route,
            "multiplicities": multiplicities,
            "total": sum(row["amount"] * multiplicities[row["charge_id"]] for row in fees),
        })
    return {
        "schema_version": "s07-resolved-structural-source/2",
        "world_id": "S07_PILOT_20260920_R01",
        "jurisdiction_id": jid,
        "utility_id": "U05",
        "actors": actors,
        "money_context": copy.deepcopy(design["money_unit_normalization"]),
        "authorities": authorities,
        "phase_event_dependencies": phase_rules,
        "applicant_encounters": encounters,
        "required_documents": documents,
        "checklist_items": checklist,
        "fee_schedule": fees,
        "worked_fee_examples": worked,
    }


@pytest.fixture
def fixture_source():
    design = _design()
    source = _source(design)
    validate_resolved_source(source, design)
    return source, design


@pytest.fixture
def config():
    durations = {
        key: DurationSpec(2, 6)
        for key in (
            "design_sign_to_submit", "ahj_permit_manual",
            "preinstall_ix", "installation", "ahj_inspection",
            "postinspection_handoff", "final_ix_to_pto",
        )
    }
    durations["ahj_permit_automatic_positive"] = DurationSpec(1, 3)
    return CaseMechanicsConfig(
        profile_id="SOURCE_FREE_B",
        window_start="2024-09-02",
        window_end="2026-08-31",
        as_of="2026-09-01",
        speed_multiplier=1.0,
        storage_share=0.5,
        small_size_share=0.75,
        automatic_permit_share=0.25,
        automatic_same_day_probability=0.55,
        preinstall_required_share=0.6,
        parallel_submission_share=0.4,
        denied_probability=0.04,
        withdrawn_probability=0.03,
        abandoned_probability=0.03,
        max_repeats=2,
        durations=durations,
        repeat_probabilities={key: 0.2 for key in (
            "ahj_permit_manual", "preinstall_ix", "ahj_inspection", "final_ix_to_pto",
        )},
    )


def _draws(
    *, route="serial_standard", outcome="completed", arrival="2025-01-06",
    technology="pv_plus_storage", permit_repeats=0, inspection_repeats=0,
    permit_days=2, pre_days=2,
):
    return CaseDraws(
        arrival_date=arrival,
        technology=technology,
        size_band="0_10_kw",
        automatic_permit=False,
        preinstall_required=route != "no_preinstall_approval",
        parallel_submission=route == "parallel_standard",
        durations={
            "design_sign_to_submit": DurationDraw(2.0, 2),
            "ahj_permit": DurationDraw(float(permit_days), permit_days),
            "preinstall_ix": DurationDraw(float(pre_days), pre_days),
            "installation": DurationDraw(3.0, 3),
            "ahj_inspection": DurationDraw(2.0, 2),
            "postinspection_handoff": DurationDraw(1.0, 1),
            "final_ix_to_pto": DurationDraw(2.0, 2),
        },
        repeat_counts={
            "ahj_permit": permit_repeats,
            "preinstall_ix": 0,
            "ahj_inspection": inspection_repeats,
            "final_ix_to_pto": 0,
        },
        denied=outcome == "denied",
        withdrawn=outcome == "withdrawn",
        abandoned=outcome == "abandoned",
    )


def _build(config, fixture_source, draws, case_index=1):
    source, design = fixture_source
    return build_case_from_draws(
        config, source, design, case_index=case_index, draws=draws,
    )


def test_semantic_rng_is_deterministic_and_order_independent(config, fixture_source):
    source, design = fixture_source
    first = generate_case(config, source, design, seed=1107, case_index=8)
    generate_case(config, source, design, seed=1107, case_index=2)
    second = generate_case(config, source, design, seed=1107, case_index=8)
    assert first == second
    assert draw_case_inputs(config, seed=1107, jurisdiction_id="R01J01", case_index=8) == \
        draw_case_inputs(config, seed=1107, jurisdiction_id="R01J01", case_index=8)
    assert draw_case_inputs(config, seed=1108, jurisdiction_id="R01J01", case_index=8) != \
        draw_case_inputs(config, seed=1107, jurisdiction_id="R01J01", case_index=8)


def test_routes_schedule_exact_dependencies_and_no_pre_is_absence(config, fixture_source):
    parallel = _build(config, fixture_source, _draws(route="parallel_standard"), 1)
    serial = _build(config, fixture_source, _draws(route="serial_standard"), 2)
    no_pre = _build(config, fixture_source, _draws(route="no_preinstall_approval"), 3)
    pdates = {row["event"]: row["date"] for row in parallel["events"]}
    sdates = {row["event"]: row["date"] for row in serial["events"]}
    assert pdates["preinstall_interconnection_submission"] == pdates["first_permit_submission"]
    assert sdates["preinstall_interconnection_submission"] > sdates["final_permit_approval"]
    assert no_pre["phases"]["preinstall_ix"]["status"] == "not_required"
    assert not any("PREIX" in row["encounter_id"] for row in no_pre["realized_burden"]["encounters"])
    for case in (parallel, serial, no_pre):
        for phase in case["phases"].values():
            if phase["status"] == "completed":
                assert business_days_between(phase["start_date"], phase["end_date"]) == \
                    phase["duration"]["realized_business_days"]


def test_repeat_floors_apply_only_for_positive_repeats_and_place_events(config, fixture_source):
    same_day = adjusted_duration(DurationDraw(0.2, 0), phase_id="ahj_permit", repeats=0)
    permit = adjusted_duration(DurationDraw(0.2, 0), phase_id="ahj_permit", repeats=2)
    inspection = adjusted_duration(DurationDraw(1.1, 1), phase_id="ahj_inspection", repeats=2)
    assert same_day["realized_business_days"] == 0
    assert same_day["repeat_chronology_floor"] == 0
    assert permit["realized_business_days"] == 5
    assert inspection["realized_business_days"] == 7
    assert repeat_event_offsets(5, repeats=2, events_per_repeat=2) == (1, 2, 3, 4)
    case = _build(
        config, fixture_source,
        _draws(permit_repeats=1, inspection_repeats=2, permit_days=0),
    )
    assert case["phases"]["ahj_permit"]["duration"]["realized_business_days"] == 3
    assert case["phases"]["ahj_inspection"]["duration"]["realized_business_days"] == 7
    assert case["realized_burden"]["counts"] == {
        "encounters": 8,
        "document_copies": 6,
        "checklist_actions": 10,
        "fee_occurrences": 7,
    }
    assert case["private_draw_provenance"]["duration_draws"]["ahj_permit"] == {
        "raw_business_days": 0.0,
        "rounded_business_days": 0,
    }


@pytest.mark.parametrize(
    ("route", "outcome", "expected", "terminal"),
    [
        ("parallel_standard", "denied", "denied_or_ineligible", "permit_denied"),
        ("serial_standard", "withdrawn", "withdrawn", "application_withdrawn"),
        ("serial_standard", "abandoned", "abandoned", "project_abandoned"),
    ],
)
def test_outcomes_stop_downstream_events(config, fixture_source, route, outcome, expected, terminal):
    case = _build(config, fixture_source, _draws(route=route, outcome=outcome))
    assert case["latent_eventual_outcome"] == expected
    assert case["terminal_event"] == terminal
    terminal_ordinal = next(row["ordinal"] for row in case["events"] if row["event"] == terminal)
    assert terminal_ordinal == len(case["events"])
    if outcome == "denied":
        assert "installation_start" not in {row["event"] for row in case["events"]}
    if outcome == "withdrawn":
        assert "installation_start" not in {row["event"] for row in case["events"]}
    if outcome == "abandoned":
        assert "inspection_request" not in {row["event"] for row in case["events"]}


def test_parallel_denial_preserves_only_approval_completed_before_denial(config, fixture_source):
    early = _build(
        config, fixture_source,
        _draws(route="parallel_standard", outcome="denied", permit_days=3, pre_days=1), 1,
    )
    late = _build(
        config, fixture_source,
        _draws(route="parallel_standard", outcome="denied", permit_days=1, pre_days=3), 2,
    )
    assert early["phases"]["preinstall_ix"]["status"] == "completed"
    assert late["phases"]["preinstall_ix"]["status"] == "canceled_due_to_permit_denial"
    assert "preinstall_interconnection_approval" not in {row["event"] for row in late["events"]}


def test_no_pre_denial_keeps_structural_absence_distinct(config, fixture_source):
    case = _build(
        config, fixture_source,
        _draws(route="no_preinstall_approval", outcome="denied"),
    )
    phase = case["phases"]["preinstall_ix"]
    assert phase["status"] == "not_required"
    assert phase["duration"] is None
    assert phase["repeat_count"] == 0


def test_cutoff_projection_is_pending_and_excludes_cutoff_or_future(config, fixture_source):
    case = _build(
        config, fixture_source,
        _draws(route="serial_standard", arrival="2026-08-31"),
    )
    projection = case["observed_cutoff"]
    assert projection["state"] == "pending_at_cutoff"
    assert all(row["date"] < "2026-09-01" for row in projection["events"])
    assert case["latent_eventual_outcome"] == "pto_completed"
    assert case["terminal_date"] >= "2026-09-01"


def test_private_membership_is_full_base_audit_only_and_not_an_independence_claim(config, fixture_source):
    case = _build(config, fixture_source, _draws())
    provenance = case["private_membership_provenance"]
    assert len(provenance["base_membership_candidates"]) == 4
    assert {row["case_id"] for row in provenance["base_membership_candidates"]} == {case["case_id"]}
    assert provenance["derived_reporting_memberships"] == []
    assert provenance["derived_memberships_constructed_here"] is False
    assert provenance["private_audit_only"] is True
    assert provenance["permitted_blind_input"] is False
    assert case["dependence_qualification"]["independent_of_other_evidence"] is None
    assert case["dependence_qualification"]["private_membership_may_drive_blind_admission_or_weights"] is False
    assert case["arrival_date"] == "2025-01-06"


def test_builder_performs_no_filesystem_write(config, fixture_source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _build(config, fixture_source, _draws())
    assert list(tmp_path.iterdir()) == []


def test_config_and_draws_fail_closed(config, fixture_source):
    bad = copy.copy(config)
    object.__setattr__(bad, "as_of", "2026-09-02")
    with pytest.raises(S07CaseMechanicsError, match="reviewed S07 R01"):
        validate_mechanics_config(bad)
    bad = copy.copy(config)
    object.__setattr__(bad, "denied_probability", 0.05)
    with pytest.raises(S07CaseMechanicsError, match="reviewed value"):
        validate_mechanics_config(bad)
    draws = _draws()
    bad_draws = copy.copy(draws)
    object.__setattr__(bad_draws, "arrival_date", "2025-01-05")
    with pytest.raises(S07CaseMechanicsError, match="business date"):
        _build(config, fixture_source, bad_draws)
    with pytest.raises(S07CaseMechanicsError, match="integer, not boolean"):
        generate_case(config, fixture_source[0], fixture_source[1], seed=True, case_index=1)
    with pytest.raises(S07CaseMechanicsError, match="route flags must be boolean"):
        choose_route(1, False)
    bad_draws = _draws()
    bad_draws.durations["installation"] = DurationDraw(1.2, 2)
    with pytest.raises(S07CaseMechanicsError, match="does not replay"):
        _build(config, fixture_source, bad_draws)
    huge = _draws()
    huge.durations["installation"] = DurationDraw(1e308, int(1e308))
    with pytest.raises(S07CaseMechanicsError, match="overflows the date range"):
        _build(config, fixture_source, huge)
    boolean_raw = _draws()
    boolean_raw.durations["installation"] = DurationDraw(True, 1)
    with pytest.raises(S07CaseMechanicsError, match="raw is invalid"):
        _build(config, fixture_source, boolean_raw)


def test_business_day_subtraction_rejects_weekend_and_bool():
    assert subtract_business_days("2025-01-06", 1) == "2025-01-03"
    with pytest.raises(S07CaseMechanicsError, match="business day"):
        subtract_business_days("2025-01-05", 1)
    with pytest.raises(S07CaseMechanicsError, match="not boolean"):
        subtract_business_days("2025-01-06", True)
