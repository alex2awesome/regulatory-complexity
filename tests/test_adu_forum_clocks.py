from copy import deepcopy

import pytest

from pipeline.procbench.adu_panel.forum_evidence import stage_documents
from pipeline.procbench.adu_panel.prepare_forum_clocks import bind_dependence_groups, compile_clocks, content_sha


def fixture():
    claim = {"thread_id": "t", "json_path": "$.post.selftext", "char_start": 0,
             "char_end": 20, "quote": "Example quoted clock"}
    data = {"episodes": [{"episode_id": "e", "speaker": "owner", "jurisdiction": None,
                           "durations": [claim], "actions": [{"action_id": "submit_application"}]}]}
    bundle = stage_documents([{"path": "slice.json", "data": data}], {}, {}, {})
    bundle["input_sha256"] = {"slice.json": "fake-fixture-hash"}
    review = {"schema_version": "adu-clock-review/1", "adoption_state": "adopted",
              "reviewed_by": "fixture", "clocks": {"filing_to_permit": {
                  "start": "first permit filing", "end": "permit issuance",
                  "qualification": "First filing is not deemed completeness."}},
              "claims": {"e:durations:0": {"claim_content_sha256": content_sha(claim),
                  "route": "duration", "clock": "filing_to_permit",
                  "quantity": "elapsed_calendar_time", "observation_status": "completed",
                  "measurement": {"unit": "months", "lower": 6}, "rationale": "Fixture annotation"}}}
    return bundle, review


def test_completed_and_pending_bounds_are_distinct_and_unknown_place_is_retained():
    bundle, review = fixture()
    completed = compile_clocks(bundle, review)
    observed = completed["observations"][0]
    assert observed["observation_kind"] == "completed_lower_bound"
    assert observed["lower"] == pytest.approx(182.625)
    assert observed["upper"] is None
    assert observed["jurisdiction_as_coded"] is None
    assert len(completed["claim_routes"]) == 2
    review["claims"]["e:durations:0"]["observation_status"] = "pending"
    pending = compile_clocks(bundle, review)["observations"][0]
    assert pending["observation_kind"] == "pending_right_censored"
    assert pending["lower"] == observed["lower"]


@pytest.mark.parametrize("status", ["forecast", "policy_deadline", "unresolved"])
def test_nonobservations_remain_routed_not_modeled(status):
    bundle, review = fixture()
    review["claims"]["e:durations:0"]["observation_status"] = status
    result = compile_clocks(bundle, review)
    assert result["observations"] == []
    assert any(r["route"] == "retained_" + status for r in result["claim_routes"])


def test_stale_claim_fails_and_missing_review_preserves_evidence():
    bundle, review = fixture()
    review["claims"]["e:durations:0"]["claim_content_sha256"] = "stale"
    with pytest.raises(ValueError, match="Stale reviewed claim"):
        compile_clocks(bundle, review)
    review["claims"] = {}
    result = compile_clocks(bundle, review)
    assert result["observations"] == []
    assert result["counts"]["all_claims"] == 2
    assert result["counts"]["routes"]["retained_without_structured_clock_reading"] == 1


def test_provenance_and_unresolved_additions_do_not_become_independent_cases():
    bundle, review = fixture()
    for disposition in ("exclude_primary", "out_of_scope", "sensitivity_only"):
        changed = deepcopy(bundle)
        changed["records"][0]["claims"][1]["provenance"]["effective_decision"] = disposition
        assert compile_clocks(changed, review)["observations"] == []
    bundle["records"][0]["record_type"] = "cross_slice_additions"
    bundle["records"][0]["link_status"] = "retained_unresolved_addition"
    # A named author can supply a report without asserting which earlier
    # project it belongs to; the shared fitter thins by contributor.
    result = compile_clocks(bundle, review)
    assert len(result["observations"]) == 1
    assert result["observations"][0]["project_link_status"] == "retained_unresolved_addition"
    assert "not a new independent installation" in result["observations"][0]["project_identity_qualification"]
    bundle["records"][0]["speaker"] = None
    result = compile_clocks(bundle, review)
    assert result["observations"] == []
    assert any(r["route"] == "retained_unresolved_anonymous_addition_dependence_unknown"
               for r in result["claim_routes"])


def test_business_days_never_silently_become_calendar_days():
    bundle, review = fixture()
    annotation = review["claims"]["e:durations:0"]
    annotation["measurement"] = {"unit": "business_days", "lower": 5, "upper": 7}
    with pytest.raises(ValueError, match="quantity and unit disagree"):
        compile_clocks(bundle, review)
    annotation["quantity"] = "elapsed_business_time"
    result = compile_clocks(bundle, review)["observations"][0]
    assert result["time_unit"] == "business_days"
    assert (result["lower"], result["upper"]) == (5, 7)


def test_equal_handles_on_different_platforms_are_not_one_contributor():
    bundle, review = fixture()
    review["platform"] = "reddit"
    reddit = compile_clocks(bundle, review)["observations"][0]
    review["platform"] = "houzz"
    houzz = compile_clocks(bundle, review)["observations"][0]
    assert reddit["contributor_group"] != houzz["contributor_group"]


def test_secondary_clocks_preserve_parent_claim_and_forecasts_do_not_enter_likelihood():
    bundle, review = fixture()
    annotation = review["claims"]["e:durations:0"]
    review["clocks"]["build"] = {"start": "construction start", "end": "construction complete", "qualification": "Elapsed construction, not labor."}
    child = {"clock": "build", "quantity": "elapsed_calendar_time", "observation_status": "completed",
             "measurement": {"value": 2, "unit": "weeks"}, "rationale": "Second quoted clock in the same claim."}
    annotation["additional_readings"] = [child, {**child, "observation_status": "forecast"}]
    result = compile_clocks(bundle, review)
    assert result["counts"]["all_claims"] == 2
    assert result["counts"]["additional_clock_readings"] == 2
    assert result["counts"]["routing_rows"] == 4
    assert len(result["observations"]) == 2
    secondary = result["observations"][1]
    assert secondary["source_claim_id"] == "e:durations:0"
    assert secondary["claim_id"] == "e:durations:0:reading:1"
    assert secondary["clock"] == "build"
    assert any(row["route"] == "retained_forecast" for row in result["claim_routes"])


def test_month_resolution_is_preserved_when_explicitly_declared():
    bundle, review = fixture()
    annotation = review["claims"]["e:durations:0"]
    annotation["measurement"] = {"value": 6, "unit": "months"}
    annotation["precision"] = "month_only"
    observed = compile_clocks(bundle, review)["observations"][0]
    assert observed["lower"] == pytest.approx(5.5 * 365.25 / 12)
    assert observed["upper"] == pytest.approx(6.5 * 365.25 / 12)


def test_explicit_project_aliases_and_anonymous_linked_records_are_not_independent():
    rows = [
        {"platform": "reddit", "contributor_group": "reddit:owner", "case_id": "p"},
        {"platform": "reddit", "contributor_group": "reddit:alias", "case_id": "p"},
        {"platform": "reddit", "contributor_group": "project:p", "case_id": "p"},
        {"platform": "reddit", "contributor_group": "reddit:owner", "case_id": "second_project"},
        {"platform": "reddit", "contributor_group": "project:unrelated", "case_id": "unrelated"},
        {"platform": "houzz", "contributor_group": "houzz:owner", "case_id": "p"},
    ]
    bind_dependence_groups(rows)
    assert len({r["contributor_group"] for r in rows[:4]}) == 1
    assert len({rows[0]["contributor_group"], rows[4]["contributor_group"], rows[5]["contributor_group"]}) == 3
    assert rows[3]["case_id"] == "second_project"  # no identity merge
    assert rows[1]["reported_contributor_group"] == "reddit:alias"
