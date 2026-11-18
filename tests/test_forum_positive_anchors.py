from pipeline.procbench.process_structure.forum_positive_anchors import add_positive_anchors


def test_selected_positive_becomes_anchor_not_detection_trial():
    model = {"detection_beta": [2, 2], "false_positive_probability": .02}
    base = {"schema_version": "process-occupancy-evidence/1", "scope": "2017-2024",
            "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
            "conditional_independence": "assumed_given_presence_and_source_type_detection",
            "assumption_note": "fixture", "jurisdictions": ["j"], "steps": ["s"],
            "source_types": ["base"], "source_models": {"base": model},
            "observations": [], "known_presence": []}
    ref = {"path": "held.json", "sha256": "a"*64, "locator": "$.quote"}
    selected = {"observations": [{"unit_id": "case", "jurisdiction_id": "j", "step_id": "s",
                                  "source_type": "forum_initial_episode", "detected": True,
                                  "evidence_refs": [ref]}]}
    decisions = {"schema_version": "solar-forum-positive-anchor-decisions/1",
                 "target_era": {"start_year": 2017, "end_year": 2024},
                 "decisions": [{"unit_id": "case", "step_id": "s", "disposition": "anchor_presence",
                                "event_year": 2023, "actor": "applicant"}]}
    data, receipt = add_positive_anchors(base, selected, decisions,
                                         [{"step_id": "s", "actor": "applicant"}])
    assert len(data["known_presence"]) == 1
    assert data["observations"] == []
    assert receipt["added_anchor_cells"] == 1
    assert receipt["detection_trials_added"] == receipt["nondetections_added"] == 0
