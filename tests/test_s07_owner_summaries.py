"""Source-free tests for the pure S07 owner/cohort summary module."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from benchmark.synth.generator.s07_fresh_replica import (
    AS_OF,
    JURISDICTIONS,
    PHASE_CONTRACTS,
    RELEASE_ID,
    UTILITY_JURISDICTIONS,
    WORLD_ID,
    add_business_days,
)
from benchmark.synth.generator.s07_owner_summaries import (
    S07OwnerSummaryError,
    build_owner_summaries,
    canonical_observation_id,
    membership_hash,
)


def _profiles(**overrides):
    profiles = {jid: "A" for jid in JURISDICTIONS}
    profiles.update(overrides)
    return profiles


def _utility(jid):
    return next(uid for uid, members in UTILITY_JURISDICTIONS.items() if jid in members)


def _phase(status, phase_id, start=None, end=None, duration=None):
    if status == "completed":
        if phase_id == "installation":
            start_event, end_event = "installation_start", "installation_complete"
        else:
            _, start_event, end_event = PHASE_CONTRACTS[phase_id]
        return {
            "phase_id": phase_id,
            "status": status,
            "start_event": start_event,
            "start_date": start,
            "end_event": end_event,
            "end_date": end,
            "duration": {
                "raw_sampled_business_days": float(duration),
                "rounded_business_days": duration,
                "realized_business_days": duration,
                "repeat_chronology_floor": 0,
                "repeat_floor_applied": False,
            },
            "repeat_count": 0,
        }
    return {
        "phase_id": phase_id,
        "status": status,
        "start_event": None,
        "start_date": None,
        "end_event": None,
        "end_date": None,
        "duration": None,
        "repeat_count": 0,
    }


def _case(
    jid,
    index,
    profile,
    *,
    route="parallel_standard",
    technology="pv_only",
    size_band="0_10_kw",
    completed=None,
    arrival="2025-01-06",
):
    completed = completed or {}
    case_id = f"{jid}.C{index:04d}"
    utility = _utility(jid)
    base_starts = {
        "ahj_permit": arrival,
        "preinstall_ix": "2025-01-07",
        "installation": "2025-01-20",
        "ahj_inspection": "2025-02-03",
        "final_ix_to_pto": "2025-03-03",
    }
    phases = {}
    events = [{"event": "first_permit_submission", "date": arrival, "ordinal": 1}]
    ordinal = 1
    for phase_id in (*PHASE_CONTRACTS, "installation"):
        if phase_id == "preinstall_ix" and route == "no_preinstall_approval":
            phases[phase_id] = _phase("not_required", phase_id)
            continue
        if phase_id not in completed:
            phases[phase_id] = _phase("not_started_due_to_outcome", phase_id)
            continue
        duration = completed[phase_id]
        start = base_starts[phase_id]
        if phase_id == "ahj_permit":
            start = arrival
        end = add_business_days(start, duration)
        phases[phase_id] = _phase("completed", phase_id, start, end, duration)
        if phase_id == "installation":
            start_event, end_event = "installation_start", "installation_complete"
        else:
            _, start_event, end_event = PHASE_CONTRACTS[phase_id]
        if not (start_event == "first_permit_submission" and start == arrival):
            ordinal += 1
            events.append({"event": start_event, "date": start, "ordinal": ordinal})
        ordinal += 1
        events.append({"event": end_event, "date": end, "ordinal": ordinal})
    events.sort(key=lambda row: (row["date"], row["ordinal"]))
    for new_ordinal, event in enumerate(events, 1):
        event["ordinal"] = new_ordinal
    candidates = []
    for phase_id, (owner_type, _, _) in PHASE_CONTRACTS.items():
        phase = phases[phase_id]
        candidates.append({
            "membership_candidate_id": f"{case_id}.MEMBER.{phase_id}",
            "case_id": case_id,
            "phase_id": phase_id,
            "owner_type": owner_type,
            "owner_id": jid if owner_type == "ahj" else utility,
            "technology": technology,
            "size_band": size_band,
            "route": route,
            "phase_status": phase["status"],
            "completed_by_cutoff": (
                phase["status"] == "completed" and phase["end_date"] < AS_OF
            ),
        })
    return {
        "schema_version": "s07-private-case-mechanics/1",
        "case_id": case_id,
        "same_case_group": f"s07-case:{case_id}",
        "jurisdiction_id": jid,
        "utility_id": utility,
        "profile_id": profile,
        "arrival_date": arrival,
        "technology": technology,
        "size_band": size_band,
        "route": route,
        "fee_schedule_lock": {
            "event": "first_permit_submission",
            "date": arrival,
        },
        "events": events,
        "phases": phases,
        "observed_cutoff": {
            "as_of": AS_OF,
            "state": "pending_at_cutoff",
            "events": [event for event in events if event["date"] < AS_OF],
        },
        "private_membership_provenance": {
            "basis": "full_base_case_phase_membership_before_any_reporting_transform",
            "base_membership_candidates": candidates,
            "derived_reporting_memberships": [],
            "derived_memberships_constructed_here": False,
            "private_audit_only": True,
            "permitted_blind_input": False,
        },
    }


def _rows(result, **criteria):
    return [
        row for row in result.public_observations
        if all(row[key] == value for key, value in criteria.items())
    ]


def _companions(result, **criteria):
    return [
        row for row in result.private_observation_companions
        if all(row[key] == value for key, value in criteria.items())
    ]


def test_empty_input_emits_complete_matrix_with_status_precedence():
    profiles = _profiles(R01J03="D", R01J08="B")
    result = build_owner_summaries([], profiles)
    assert len(result.public_observations) == 1152
    assert len({row["owner_cell_id"] for row in result.public_observations}) == 864
    assert len({row["public_cohort_cell_id"] for row in result.public_observations}) == 432
    assert len(result.private_cohort_memberships) == 432
    assert len(result.private_observation_companions) == 1152
    assert all(
        row["value_status"] == "not_required"
        for row in _rows(
            result, phase_id="preinstall_ix", route="no_preinstall_approval",
        )
    )
    empty_d = _rows(
        result, jurisdiction_id="R01J03", owner_type="ahj",
        phase_id="ahj_inspection", statistic="p90",
        technology="pv_only", size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert empty_d["value_status"] == "no_observed_cases"
    assert empty_d["sample_size_status"] == "known"
    assert empty_d["sample_size"] == 0
    empty_b = _rows(
        result, jurisdiction_id="R01J08", owner_type="ahj",
        phase_id="ahj_permit", statistic="median",
        technology="pv_only", size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert empty_b["sample_size_status"] == "known" and empty_b["sample_size"] == 0


def test_phase_completion_is_admitted_without_whole_project_completion_and_zero_is_reported():
    profiles = _profiles(R01J06="A")
    case = _case("R01J06", 1, "A", completed={"ahj_permit": 0})
    result = build_owner_summaries([case], profiles)
    row = _rows(
        result, jurisdiction_id="R01J06", owner_type="ahj",
        phase_id="ahj_permit", statistic="median", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert row["value_status"] == "reported"
    assert row["value"] == 0
    assert row["zero_semantics"] == "same_day_completed"
    assert row["sample_size"] == 1
    assert case["phases"]["final_ix_to_pto"]["status"] != "completed"


def test_utility_pooling_is_single_cohort_with_local_joined_counts():
    profiles = _profiles(R01J09="B", R01J01="D")
    cases = [
        _case(
            "R01J09", 1, "B",
            completed={"installation": 1, "final_ix_to_pto": 1},
        ),
        _case("R01J01", 2, "D", completed={"final_ix_to_pto": 3}),
    ]
    result = build_owner_summaries(cases, profiles)
    rows = _rows(
        result, owner_type="utility", owner_id="U05",
        phase_id="final_ix_to_pto", statistic="median", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )
    assert len(rows) == 2
    assert {row["jurisdiction_id"] for row in rows} == {"R01J09", "R01J01"}
    assert {row["value"] for row in rows} == {2.0}
    assert {row["owner_cell_id"] for row in rows}.__len__() == 1
    assert len({row["observation_id"] for row in rows}) == 2
    assert {row["sample_size"] for row in rows} == {2}
    assert {row["jurisdiction_id"]: row["joined_install_count"] for row in rows} == {
        "R01J09": 1, "R01J01": 0,
    }
    companions = [
        next(item for item in result.private_observation_companions
             if item["observation_id"] == row["observation_id"])
        for row in rows
    ]
    assert len({item["base_membership_hash"] for item in companions}) == 1
    assert len({item["selected_membership_hash"] for item in companions}) == 1


def test_profile_c_freezes_common_tail_selection_and_descending_case_id_tie():
    profiles = _profiles(R01J02="A", R01J11="D")
    cases = []
    for index, duration in enumerate((1, 2, 3, 4, 5, 6, 7, 8, 9, 9), 1):
        jid = "R01J02" if index <= 5 else "R01J11"
        cases.append(_case(
            jid, index, profiles[jid],
            completed={"final_ix_to_pto": duration},
        ))
    result = build_owner_summaries(cases, profiles)
    rows = _rows(
        result, owner_type="utility", owner_id="U06",
        phase_id="final_ix_to_pto", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )
    assert len(rows) == 4
    assert {row["sample_size"] for row in rows} == {9}
    cohort_id = rows[0]["public_cohort_cell_id"]
    cohort = next(
        row for row in result.private_cohort_memberships
        if row["public_cohort_cell_id"] == cohort_id
    )
    assert cohort["base_n"] == 10 and cohort["selected_n"] == 9
    assert cohort["excluded_case_ids"] == ["R01J11.C0010"]
    assert "R01J11.C0010" in cohort["base_case_ids"]
    assert "R01J11.C0010" not in cohort["selected_case_ids"]
    assert cohort["base_membership_hash"] != cohort["selected_membership_hash"]
    p90_rows = [row for row in rows if row["statistic"] == "p90"]
    assert {row["value"] for row in p90_rows} == {8.0}
    statistic_companions = _companions(
        result, public_cohort_cell_id=cohort_id,
    )
    assert len({row["selected_membership_hash"] for row in statistic_companions}) == 1
    assert {
        row["selected_unrounded_statistic"]
        for row in statistic_companions if row["statistic"] == "p90"
    } == {8.2}


def test_profile_d_positive_inspection_p90_is_missing_but_private_statistic_remains():
    profiles = _profiles(R01J03="D")
    case = _case("R01J03", 1, "D", completed={"ahj_inspection": 2})
    result = build_owner_summaries([case], profiles)
    p90 = _rows(
        result, jurisdiction_id="R01J03", owner_type="ahj",
        phase_id="ahj_inspection", statistic="p90", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )[0]
    median = _rows(
        result, jurisdiction_id="R01J03", owner_type="ahj",
        phase_id="ahj_inspection", statistic="median", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert p90["value_status"] == "missing_report" and p90["value"] is None
    assert median["value_status"] == "reported" and median["value"] == 2
    companion = next(
        row for row in result.private_observation_companions
        if row["observation_id"] == p90["observation_id"]
    )
    assert companion["base_unrounded_statistic"] == 2.0
    assert companion["selected_unrounded_statistic"] == 2.0


def test_completion_at_cutoff_is_not_admitted():
    profiles = _profiles(R01J06="A")
    case = _case(
        "R01J06", 1, "A", arrival="2026-08-31",
        completed={"ahj_permit": 1},
    )
    result = build_owner_summaries([case], profiles)
    row = _rows(
        result, jurisdiction_id="R01J06", owner_type="ahj",
        phase_id="ahj_permit", statistic="median", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert case["phases"]["ahj_permit"]["end_date"] == AS_OF
    assert row["value_status"] == "no_observed_cases"


def test_denied_permit_is_not_misread_as_completed_duration():
    profiles = _profiles(R01J06="A")
    case = _case("R01J06", 1, "A")
    denial_date = add_business_days(case["arrival_date"], 2)
    case["phases"]["ahj_permit"] = {
        "phase_id": "ahj_permit",
        "status": "denied",
        "start_event": "first_permit_submission",
        "start_date": case["arrival_date"],
        "end_event": "permit_denied",
        "end_date": denial_date,
        "duration": {
            "raw_sampled_business_days": 2.0,
            "rounded_business_days": 2,
            "realized_business_days": 2,
            "repeat_chronology_floor": 0,
            "repeat_floor_applied": False,
        },
        "repeat_count": 0,
    }
    case["events"].append({"event": "permit_denied", "date": denial_date, "ordinal": 2})
    case["observed_cutoff"]["events"] = copy.deepcopy(case["events"])
    candidate = next(
        row for row in case["private_membership_provenance"]["base_membership_candidates"]
        if row["phase_id"] == "ahj_permit"
    )
    candidate["phase_status"] = "denied"
    candidate["completed_by_cutoff"] = False
    result = build_owner_summaries([case], profiles)
    row = _rows(
        result, jurisdiction_id="R01J06", owner_type="ahj",
        phase_id="ahj_permit", statistic="median", technology="pv_only",
        size_band="0_10_kw", route="parallel_standard",
    )[0]
    assert row["value_status"] == "no_observed_cases"


def test_frozen_observation_and_membership_identity_encodings():
    owner = "é-owner"
    expected_observation = (
        "s07-observation-v1"
        f"|release_id:{len(RELEASE_ID.encode('utf-8'))}:{RELEASE_ID}"
        "|jurisdiction_id:6:R01J01"
        f"|owner_cell_id:{len(owner.encode('utf-8'))}:{owner}"
    )
    assert canonical_observation_id("R01J01", owner) == expected_observation
    ids = ["case-β", "case-a"]
    payload = {
        "schema_version": "s07-private-membership-hash/1",
        "world_id": WORLD_ID,
        "public_cohort_cell_id": "cohort-1",
        "membership_kind": "base",
        "case_ids": sorted(ids),
    }
    expected_hash = hashlib.sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    assert membership_hash("cohort-1", "base", ids) == expected_hash
    assert membership_hash("cohort-1", "base", ids) != \
        membership_hash("cohort-1", "selected", ids)
    with pytest.raises(S07OwnerSummaryError, match="unique"):
        membership_hash("cohort-1", "base", ["x", "x"])


def test_duplicate_profile_candidate_and_duration_mismatches_fail_closed():
    profiles = _profiles(R01J06="A")
    valid = _case("R01J06", 1, "A", completed={"ahj_permit": 2})
    with pytest.raises(S07OwnerSummaryError, match="duplicate case_id"):
        build_owner_summaries([valid, copy.deepcopy(valid)], profiles)
    wrong_profile = copy.deepcopy(valid)
    wrong_profile["profile_id"] = "B"
    with pytest.raises(S07OwnerSummaryError, match="profile differs"):
        build_owner_summaries([wrong_profile], profiles)
    duplicate_candidate = copy.deepcopy(valid)
    duplicate_candidate["private_membership_provenance"]["base_membership_candidates"][1] = \
        copy.deepcopy(duplicate_candidate["private_membership_provenance"]["base_membership_candidates"][0])
    with pytest.raises(S07OwnerSummaryError, match="membership_candidate_id"):
        build_owner_summaries([duplicate_candidate], profiles)
    bad_duration = copy.deepcopy(valid)
    bad_duration["phases"]["ahj_permit"]["duration"]["realized_business_days"] = 1
    with pytest.raises(S07OwnerSummaryError, match="does not replay"):
        build_owner_summaries([bad_duration], profiles)


def test_profile_map_is_complete_and_case_consistent():
    incomplete = _profiles()
    del incomplete["R01J12"]
    with pytest.raises(S07OwnerSummaryError, match="exactly all 12"):
        build_owner_summaries([], incomplete)
    invalid = _profiles(R01J01="reserved")
    with pytest.raises(S07OwnerSummaryError, match="unsupported reporting profile"):
        build_owner_summaries([], invalid)


def test_public_rows_exclude_private_membership_and_profiles_and_no_io(tmp_path, monkeypatch):
    profiles = _profiles(R01J06="C")
    case = _case("R01J06", 1, "C", completed={"ahj_permit": 2})
    monkeypatch.chdir(tmp_path)
    result = build_owner_summaries([case], profiles)
    assert list(tmp_path.iterdir()) == []
    encoded = json.dumps(result.public_observations, sort_keys=True)
    for forbidden in (
        "case_ids", "case_member_hash", "membership_hash", "profile",
        "reporting_transform", "same_cohort_group", "private_audit_only",
    ):
        assert forbidden not in encoded
    assert any(row["base_case_ids"] for row in result.private_cohort_memberships)
