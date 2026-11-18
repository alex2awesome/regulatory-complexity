from pipeline.procbench.adu_panel.forum_evidence import provenance_for, stage_documents


def test_legacy_author_field_preserves_provenance_without_parsing_notes():
    data = {"episodes": [{"episode_id": "old", "author": "builder",
                           "durations": [{"quote": "reported duration"}]},
                          {"episode_id": "unknown", "notes": "Handle appears only in prose"}]}
    registry = {"speakers": {"builder": {"decision": "keep_flagged", "flag": "commercial"}}}
    records = stage_documents([{"path": "legacy.json", "data": data}], registry, {}, {})["records"]
    assert records[0]["speaker"] == "builder"
    assert records[0]["claims"][0]["provenance"]["effective_decision"] == "keep_flagged"
    assert records[1]["speaker"] is None


def test_claim_override_does_not_blacklist_entire_account():
    registry = {"speakers": {"builder": {"decision": "keep_flagged", "flag": "commercial",
                 "claim_overrides": [{"thread_id": "t", "json_path": "$.comments[2].body", "decision": "exclude_primary"}]}}}
    flagged = {"quote": {"thread_id": "t", "json_path": "$.comments[2].body"}}
    ordinary = {"quote": {"thread_id": "t", "json_path": "$.comments[3].body"}}
    assert provenance_for("builder", flagged, registry)["effective_decision"] == "exclude_primary"
    assert provenance_for("builder", ordinary, registry)["effective_decision"] == "keep_flagged"
    assert provenance_for("unknown", ordinary, registry)["effective_decision"] == "unreviewed"


def test_named_links_and_unresolved_additions_preserve_all_records():
    data = {"episodes": [{"episode_id": "a", "speaker": "owner", "actions": [{"action_id": "prepare_plans"}]},
                         {"episode_id": "b", "speaker": "owner", "absent_actions": []},
                         {"episode_id": "other_project", "speaker": "owner"}],
            "cross_slice_additions": [{"speaker": "owner", "additional_evidence": {"episode_id": "extra", "durations": [{"phase": "unknown"}]}}],
            "general_practice_claims": [{"claim_id": "practice", "speaker": "builder", "quote": "advice"}],
            "out_of_scope": [{"reason": "historical disposition"}]}
    merges = {"merge": {"reviewed": {"episodes": [{"episode_id": "a"}, {"episode_id": "b"}]}}}
    bundle = stage_documents([{"path": "slice.json", "data": data}], {}, merges, {})
    by_id = {r["record_id"]: r for r in bundle["records"]}
    assert by_id["a"]["explicit_project_group"] == by_id["b"]["explicit_project_group"]
    assert by_id["other_project"]["explicit_project_group"] != by_id["a"]["explicit_project_group"]
    assert by_id["extra"]["link_status"] == "retained_unresolved_addition"
    assert by_id["practice"]["explicit_project_group"] is None
    assert bundle["documents"][0]["data"] == data
    assert bundle["counts"]["claim_rows"] == 3
    assert bundle["fit_ready_observations"] == 0


def test_review_can_attach_an_addition_without_a_new_case():
    data = {"episodes": [{"episode_id": "a", "speaker": "owner"}],
            "cross_slice_additions": [{"speaker": "owner", "additional_evidence": {"episode_id": "extra"}}]}
    review = {"groups": [{"decision": "attach_existing_addition", "speaker": "owner", "episode_ids": ["a"], "additional_evidence_ids": ["extra"]}]}
    bundle = stage_documents([{"path": "slice.json", "data": data}], {}, {}, review)
    a, extra = bundle["records"]
    assert a["explicit_project_group"] == extra["explicit_project_group"]
    assert extra["link_status"] == "explicitly_bound"


def test_sibling_ids_must_agree_and_do_not_override_explicit_uncertainty():
    data = {"episodes": [{"episode_id": "a"}, {"episode_id": "b"}],
            "cross_slice_additions": [
                {"sibling_records": [{"episode_id": "a"}], "additional_evidence": {"episode_id": "linked"}},
                {"sibling_records": [{"episode_id": "a"}, {"episode_id": "b"}], "additional_evidence": {"episode_id": "conflict"}},
                {"sibling_records": [{"episode_id": "a"}], "additional_evidence": {"episode_id": "alternative"}}]}
    review = {"groups": [{"decision": "retain_project_link_uncertainty", "speaker": "owner", "additional_evidence_ids": ["alternative"]}]}
    bundle = stage_documents([{"path": "slice", "data": data}], {}, {}, review)
    rows = {r["record_id"]: r for r in bundle["records"]}
    assert rows["linked"]["explicit_project_group"] == rows["a"]["explicit_project_group"]
    assert rows["conflict"]["link_status"] == "retained_unresolved_addition"
    assert rows["alternative"]["link_status"] == "retained_unresolved_addition"


def test_candidate_sibling_ids_do_not_assert_same_project():
    data = {"episodes": [{"episode_id": "a", "speaker": "owner"}],
            "cross_slice_additions": [
                {"project_link_status": "candidate_only",
                 "sibling_records": [{"episode_id": "a"}],
                 "additional_evidence": {"episode_id": "candidate", "speaker": "owner"}},
                {"project_link_status": "candidate_only",
                 "candidate_sibling_records": [{"episode_id": "a"}],
                 "additional_evidence": {"episode_id": "candidate2", "speaker": "owner"}},
                {"project_link_status": "confirmed_same_project",
                 "sibling_records": [{"episode_id": "a"}],
                 "additional_evidence": {"episode_id": "confirmed", "speaker": "owner"}}]}
    bundle = stage_documents([{"path": "slice", "data": data}], {}, {}, {})
    rows = {row["record_id"]: row for row in bundle["records"]}
    assert rows["candidate"]["link_status"] == "retained_unresolved_addition"
    assert rows["candidate2"]["link_status"] == "retained_unresolved_addition"
    assert rows["confirmed"]["link_status"] == "explicitly_bound"
    assert rows["confirmed"]["explicit_project_group"] == rows["a"]["explicit_project_group"]
    assert rows["candidate"]["explicit_project_group"] != rows["a"]["explicit_project_group"]


def test_direct_and_nested_additions_both_keep_measurements():
    duration = {"phrase": "one month", "quote": {"thread_id": "t", "json_path": "$.post.selftext"}}
    direct = {"addition_id": "direct", "speaker": "owner", "durations": [duration],
              "actions": [{"action_id": "issue_corrections"}], "round_counts": [{"lower_bound": 2}]}
    nested = {"speaker": "other", "additional_evidence": {
        "episode_id": "nested", "durations": [duration]}}
    bundle = stage_documents([{"path": "slice", "data": {"cross_slice_additions": [direct, nested]}}], {}, {}, {})
    rows = {row["record_id"]: row for row in bundle["records"]}
    assert [claim["field"] for claim in rows["direct"]["claims"]] == ["actions", "durations", "round_counts"]
    assert rows["direct"]["claims"][1]["raw"] == duration
    assert rows["nested"]["claims"][0]["raw"] == duration
    assert rows["direct"]["raw_record"] == direct
    assert rows["direct"]["link_status"] == "retained_unresolved_addition"
    assert rows["nested"]["speaker"] == "other"


def test_confirmed_string_sibling_ids_are_supported_without_guessing_identity():
    data = {"episodes": [{"episode_id": "a", "speaker": "owner"},
                         {"episode_id": "b", "speaker": "owner"}],
            "cross_slice_additions": [
                {"addition_id": "confirmed", "project_link_status": "confirmed_same_project",
                 "sibling_records": ["a"], "durations": [{"phrase": "one month"}]},
                {"addition_id": "candidate", "project_link_status": "candidate_only",
                 "sibling_records": ["a"]},
                {"addition_id": "unspecified", "sibling_records": ["a"]},
                {"addition_id": "handle_not_id", "project_link_status": "confirmed_same_project",
                 "sibling_records": ["owner"]},
                {"addition_id": "conflicting", "project_link_status": "confirmed_same_project",
                 "sibling_records": ["a", {"episode_id": "b"}]},
                {"addition_id": "protected", "project_link_status": "confirmed_same_project",
                 "sibling_records": ["a"]}]}
    review = {"groups": [{"speaker": "owner", "decision": "retain_project_link_uncertainty",
                           "additional_evidence_ids": ["protected"]}]}
    bundle = stage_documents([{"path": "slice", "data": data}], {}, {}, review)
    rows = {row["record_id"]: row for row in bundle["records"]}
    assert rows["confirmed"]["explicit_project_group"] == rows["a"]["explicit_project_group"]
    assert rows["confirmed"]["link_status"] == "explicitly_bound"
    for ident in ("candidate", "unspecified", "handle_not_id", "conflicting", "protected"):
        assert rows[ident]["link_status"] == "retained_unresolved_addition"
    assert rows["b"]["explicit_project_group"] != rows["a"]["explicit_project_group"]
    assert bundle["documents"][0]["data"] == data
    assert bundle["counts"]["claim_rows"] == 1
