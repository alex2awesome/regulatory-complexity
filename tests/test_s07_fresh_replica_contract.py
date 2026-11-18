"""Source-free mechanical tests for the effective S07 R01 public contract."""
from __future__ import annotations

import copy

import pytest

from benchmark.synth.generator.s07_fresh_replica import (
    AS_OF,
    CALENDAR_ID,
    EFFECTIVE_CONTRACT_HASHES,
    JURISDICTIONS,
    OBSERVATION_SCHEMA_VERSION,
    PRIVATE_PROVENANCE_PATH,
    RELEASE_ID,
    S07ContractError,
    S07GenerationBlocked,
    WORLD_ID,
    add_business_days,
    business_days_between,
    canonical_owner_cell_id,
    canonical_population,
    canonical_public_cohort_cell_id,
    is_business_day,
    parse_iso_date,
    require_frozen_structural_source_contract,
    validate_declared_public_leak_policy,
    validate_public_observation,
    validate_public_observations,
)


def observation(**updates):
    row = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "release_id": RELEASE_ID,
        "observation_id": "obs-1",
        "owner_cell_id": "pending",
        "jurisdiction_id": "R01J06",
        "owner_type": "utility",
        "owner_id": "U01",
        "phase_id": "final_ix_to_pto",
        "start_event": "final_interconnection_request",
        "end_event": "permission_to_operate_granted",
        "duration_basis": "elapsed_owner_phase_including_internal_queue_and_rework_within_boundaries",
        "unit": "business_days",
        "calendar_id": CALENDAR_ID,
        "period_start": "2025-09-01",
        "period_end": "2026-08-31",
        "as_of": AS_OF,
        "technology": "pv_only",
        "size_band": "0_10_kw",
        "route": "parallel_standard",
        "population": "pending",
        "statistic": "median",
        "value_status": "reported",
        "value": 5,
        "sample_size_status": "known",
        "sample_size": 12,
        "rounding": "nearest_business_day",
        "completion_conditioning": "phase_completed_by_cutoff",
        "zero_semantics": "not_zero",
        "joined_install_count": 30,
        "public_cohort_cell_id": "pending",
    }
    row.update(updates)
    row["population"] = canonical_population(row)
    row["public_cohort_cell_id"] = canonical_public_cohort_cell_id(row)
    row["owner_cell_id"] = canonical_owner_cell_id(row)
    return row


def structural_freeze():
    names = (
        "authorities", "applicant_encounters", "required_documents",
        "checklist_items", "fee_schedule",
    )
    return {
        "schema_version": "s07-populated-structural-source-freeze/1",
        "world_id": WORLD_ID,
        "status": "frozen_populated_reviewed",
        "manifest_sha256": "a" * 64,
        "jurisdictions": {
            jid: {"sha256": "b" * 64, "collection_counts": {name: 1 for name in names}}
            for jid in JURISDICTIONS
        },
    }


def test_contract_provenance_and_private_path_are_fixed():
    assert EFFECTIVE_CONTRACT_HASHES == {
        "base_manifest": "2f0c6ffc529c8ee021f78554c7b2df51f8eeb06fc048ce5025c177382bd78a50",
        "reviewed_erratum01_manifest": "2316f6eaa54ce2eb5f286139b48aa0f1364c113d6c105fb73bfb71d0de527218",
        "reviewed_erratum02_manifest": "718a588f59f31e36ec7f7ae4c1c4a860c2334b86bbd86350c108eff7cd59c49c",
    }
    assert PRIVATE_PROVENANCE_PATH == "provenance/observation_membership.jsonl.gz"


def test_fictional_business_calendar_weekend_and_same_day_rules():
    assert is_business_day("2026-09-18")
    assert not is_business_day("2026-09-19")
    assert add_business_days("2026-09-18", 0) == "2026-09-18"
    assert add_business_days("2026-09-18", 1) == "2026-09-21"
    assert add_business_days("2026-09-18", 6) == "2026-09-28"
    assert business_days_between("2026-09-18", "2026-09-18") == 0
    assert business_days_between("2026-09-18", "2026-09-21") == 1
    assert business_days_between("2026-09-18", "2026-09-28") == 6


@pytest.mark.parametrize("value", [True, False, 1.5, -1, "1"])
def test_business_day_addition_rejects_non_integer_boolean_or_negative(value):
    with pytest.raises(S07ContractError, match="nonnegative integer"):
        add_business_days("2026-09-18", value)


@pytest.mark.parametrize("value", ["2026-2-03", "2026-02-30", "x", None, True])
def test_date_parser_is_strict(value):
    with pytest.raises(S07ContractError):
        parse_iso_date(value)


def test_calendar_helpers_reject_weekend_endpoints_and_reverse_order():
    with pytest.raises(S07ContractError, match="start must be a business day"):
        add_business_days("2026-09-19", 1)
    with pytest.raises(S07ContractError, match="must be business days"):
        business_days_between("2026-09-18", "2026-09-20")
    with pytest.raises(S07ContractError, match="on or after"):
        business_days_between("2026-09-21", "2026-09-18")


def test_canonical_keys_are_deterministic_and_statistic_scoped():
    median = observation()
    replay = dict(median)
    assert canonical_public_cohort_cell_id(replay) == median["public_cohort_cell_id"]
    assert canonical_owner_cell_id(replay) == median["owner_cell_id"]
    p90 = observation(statistic="p90", observation_id="obs-p90")
    assert p90["public_cohort_cell_id"] == median["public_cohort_cell_id"]
    assert p90["owner_cell_id"] != median["owner_cell_id"]
    assert "owner_type=utility" in median["population"]
    assert "completion_conditioning=phase_completed_by_cutoff" in median["population"]


@pytest.mark.parametrize("phase,owner_type,owner_id,start,end", [
    ("ahj_permit", "ahj", "R01J06", "first_permit_submission", "final_permit_approval"),
    ("preinstall_ix", "utility", "U01", "preinstall_interconnection_submission", "preinstall_interconnection_approval"),
    ("ahj_inspection", "ahj", "R01J06", "inspection_request", "final_passed_inspection"),
    ("final_ix_to_pto", "utility", "U01", "final_interconnection_request", "permission_to_operate_granted"),
])
def test_all_four_exact_phase_contracts_accept(phase, owner_type, owner_id, start, end):
    row = observation(
        phase_id=phase, owner_type=owner_type, owner_id=owner_id,
        start_event=start, end_event=end,
    )
    validate_public_observation(row)


def test_phase_owner_endpoint_and_utility_mapping_mismatches_fail():
    with pytest.raises(S07ContractError, match="mismatched start/end"):
        validate_public_observation(observation(start_event="inspection_request"))
    with pytest.raises(S07ContractError, match="requires owner_type"):
        validate_public_observation(observation(owner_type="ahj", owner_id="R01J06"))
    with pytest.raises(S07ContractError, match="inconsistent with jurisdiction"):
        validate_public_observation(observation(jurisdiction_id="R01J10"))
    with pytest.raises(S07ContractError, match="must equal jurisdiction"):
        validate_public_observation(observation(
            phase_id="ahj_permit", owner_type="ahj", owner_id="R01J08",
            start_event="first_permit_submission", end_event="final_permit_approval",
        ))


def test_reported_positive_and_same_day_zero_are_bidirectional():
    validate_public_observation(observation())
    validate_public_observation(observation(value=0, zero_semantics="same_day_completed"))
    with pytest.raises(S07ContractError, match="same_day_completed"):
        validate_public_observation(observation(value=0, zero_semantics="not_zero"))
    with pytest.raises(S07ContractError, match="not_zero"):
        validate_public_observation(observation(value=2, zero_semantics="same_day_completed"))


def test_known_n_zero_is_only_no_observed_cases():
    zero_cases = observation(
        value_status="no_observed_cases", value=None, sample_size_status="known",
        sample_size=0, zero_semantics="no_observed_cases", rounding="not_applicable",
    )
    validate_public_observation(zero_cases)
    with pytest.raises(S07ContractError, match="reported known sample_size"):
        validate_public_observation(observation(sample_size=0))
    with pytest.raises(S07ContractError, match="suppressed known sample_size"):
        validate_public_observation(observation(
            value_status="suppressed", value=None, sample_size=0,
            zero_semantics="suppressed_or_missing", rounding="not_applicable",
        ))
    with pytest.raises(S07ContractError, match="known n=0"):
        validate_public_observation(observation(
            value_status="no_observed_cases", value=None, sample_size=1,
            zero_semantics="no_observed_cases", rounding="not_applicable",
        ))


def test_nonreported_status_contracts_are_distinct():
    validate_public_observation(observation(
        value_status="suppressed", value=None, sample_size_status="unknown",
        sample_size=None, zero_semantics="suppressed_or_missing", rounding="not_applicable",
    ))
    validate_public_observation(observation(
        value_status="missing_report", value=None, sample_size_status="unknown",
        sample_size=None, zero_semantics="suppressed_or_missing", rounding="not_applicable",
    ))
    validate_public_observation(observation(
        phase_id="preinstall_ix", start_event="preinstall_interconnection_submission",
        end_event="preinstall_interconnection_approval", route="no_preinstall_approval",
        value_status="not_required", value=None, sample_size_status="not_applicable",
        sample_size=None, completion_conditioning="not_applicable",
        zero_semantics="not_required", rounding="not_applicable",
    ))
    with pytest.raises(S07ContractError, match="must encode preinstall_ix"):
        validate_public_observation(observation(
            phase_id="preinstall_ix", start_event="preinstall_interconnection_submission",
            end_event="preinstall_interconnection_approval", route="no_preinstall_approval",
        ))


@pytest.mark.parametrize("field,value", [
    ("value", True), ("sample_size", True), ("joined_install_count", True),
    ("numerator", True), ("denominator", False),
])
def test_python_booleans_never_pass_as_public_numbers(field, value):
    with pytest.raises(S07ContractError):
        validate_public_observation(observation(**{field: value}))


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan"), -0.1])
def test_reported_values_must_be_finite_and_nonnegative(value):
    with pytest.raises(S07ContractError, match="finite-float-representable"):
        validate_public_observation(observation(value=value))


@pytest.mark.parametrize("rounding,value", [
    ("exact_integer_business_day", 1.3),
    ("nearest_business_day", 1.5),
    ("nearest_half_business_day", 1.3),
    ("nearest_half_business_day", 0.5000000000001),
])
def test_rounding_labels_enforce_their_numeric_grid(rounding, value):
    with pytest.raises(S07ContractError, match="grid value"):
        validate_public_observation(observation(rounding=rounding, value=value))
    validate_public_observation(observation(
        rounding="published_algorithm_unknown", value=value,
    ))


def test_numeric_policy_rejects_overflowing_int_as_contract_error():
    with pytest.raises(S07ContractError, match="finite-float-representable"):
        validate_public_observation(observation(value=10 ** 10000))


@pytest.mark.parametrize("value", [10 ** 308, float.fromhex("0x1.fffffffffffffp+1023")])
def test_numeric_policy_accepts_large_finite_float_representable_grid_values(value):
    validate_public_observation(observation(
        value=value, rounding="exact_integer_business_day",
    ))


def test_rounding_status_and_qualifier_nullability_are_semantic():
    with pytest.raises(S07ContractError, match="applicable rounding"):
        validate_public_observation(observation(rounding="not_applicable"))
    with pytest.raises(S07ContractError, match="nonreported values"):
        validate_public_observation(observation(
            value_status="missing_report", value=None, sample_size_status="unknown",
            sample_size=None, zero_semantics="suppressed_or_missing",
        ))
    with pytest.raises(S07ContractError, match="array of strings"):
        validate_public_observation(observation(qualifiers=None))


def test_required_dimensions_statistics_dates_and_canonical_values_fail_closed():
    missing = observation()
    del missing["technology"]
    with pytest.raises(S07ContractError, match="missing required fields"):
        validate_public_observation(missing)
    with pytest.raises(S07ContractError, match="unknown fields"):
        validate_public_observation({**observation(), "extra": 1})
    with pytest.raises(S07ContractError, match="median or p90"):
        validate_public_observation(observation(statistic="count"))
    with pytest.raises(S07ContractError, match="strict YYYY-MM-DD"):
        validate_public_observation(observation(period_start="2025-9-01"))
    with pytest.raises(S07ContractError, match="on or after"):
        validate_public_observation(observation(period_start="2026-08-31", period_end="2025-09-01"))
    with pytest.raises(S07ContractError, match="strictly before"):
        validate_public_observation(observation(period_end=AS_OF))
    row = observation()
    row["population"] = "all applications"
    with pytest.raises(S07ContractError, match="canonical explicit population"):
        validate_public_observation(row)
    row = observation()
    row["owner_cell_id"] = "made-up"
    with pytest.raises(S07ContractError, match="owner_cell_id is not canonical"):
        validate_public_observation(row)


@pytest.mark.parametrize("payload", [
    {"evaluation_split": "x"},
    {"nested": [{"safe": "reserved"}]},
    {"nested": "prefix-S07_CAL_UTILITY_01-suffix"},
    {"nested": {"S07_DEV_secret": "x"}},
    {"reserved": "x"},
    {"case_ids": []},
])
def test_recursive_declared_key_and_value_leak_policy(payload):
    with pytest.raises(S07ContractError, match="forbidden"):
        validate_declared_public_leak_policy(payload)
    validate_declared_public_leak_policy({"nested": [{"safe": "public utility U01"}]})


def test_duplicate_owner_cell_restatement_must_agree_but_join_count_may_differ():
    first = observation()
    repeated = observation(
        observation_id="obs-2", jurisdiction_id="R01J08", joined_install_count=55,
        source_document_id="another-document",
    )
    assert repeated["owner_cell_id"] == first["owner_cell_id"]
    validate_public_observations([first, repeated])
    conflicting = dict(repeated, observation_id="obs-3", value=6)
    with pytest.raises(S07ContractError, match="conflicting restatement"):
        validate_public_observations([first, conflicting])
    qualified = dict(repeated, observation_id="obs-4", qualifiers=["different cutoff population"])
    with pytest.raises(S07ContractError, match="conflicting restatement"):
        validate_public_observations([first, qualified])
    with pytest.raises(S07ContractError, match="duplicate observation_id"):
        validate_public_observations([first, dict(repeated, observation_id="obs-1")])


def test_unknown_or_not_applicable_sample_size_must_be_null():
    with pytest.raises(S07ContractError, match="unknown sample_size must be null"):
        validate_public_observation(observation(sample_size_status="unknown", sample_size=4))
    with pytest.raises(S07ContractError, match="not_applicable sample_size must be null"):
        validate_public_observation(observation(
            phase_id="preinstall_ix", start_event="preinstall_interconnection_submission",
            end_event="preinstall_interconnection_approval", route="no_preinstall_approval",
            value_status="not_required", value=None, sample_size_status="not_applicable",
            sample_size=0, completion_conditioning="not_applicable",
            zero_semantics="not_required", rounding="not_applicable",
        ))


def test_structural_source_gate_fails_closed_without_filesystem_side_effect(tmp_path):
    before = list(tmp_path.iterdir())
    with pytest.raises(S07GenerationBlocked, match="separately frozen"):
        require_frozen_structural_source_contract(None)
    assert list(tmp_path.iterdir()) == before

    candidate = structural_freeze()
    candidate["status"] = "draft"
    with pytest.raises(S07GenerationBlocked, match="not frozen"):
        require_frozen_structural_source_contract(candidate)
    assert list(tmp_path.iterdir()) == before


def test_structural_source_gate_requires_exact_hash_bound_complete_envelope():
    require_frozen_structural_source_contract(structural_freeze())
    missing = structural_freeze()
    missing["jurisdictions"].pop("R01J12")
    with pytest.raises(S07GenerationBlocked, match="exactly all 12"):
        require_frozen_structural_source_contract(missing)
    bad_hash = structural_freeze()
    bad_hash["manifest_sha256"] = "A" * 64
    with pytest.raises(S07GenerationBlocked, match="lowercase SHA-256"):
        require_frozen_structural_source_contract(bad_hash)
    boolean_count = structural_freeze()
    boolean_count["jurisdictions"]["R01J01"]["collection_counts"]["fee_schedule"] = True
    with pytest.raises(S07GenerationBlocked, match="at least one reviewed row"):
        require_frozen_structural_source_contract(boolean_count)
    missing_collection = copy.deepcopy(structural_freeze())
    missing_collection["jurisdictions"]["R01J01"]["collection_counts"].pop("fee_schedule")
    with pytest.raises(S07GenerationBlocked, match="all structural collection counts"):
        require_frozen_structural_source_contract(missing_collection)
