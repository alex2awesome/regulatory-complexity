from pipeline.procbench.process_structure.full_universe_bridge import expand_to_full_registry


def test_narrow_readings_embed_without_expanded_zeros():
    model = {"detection_beta": [2, 2], "false_positive_probability": .02}
    base = {
        "schema_version": "process-occupancy-evidence/1", "scope": "2017-2024 fixture",
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "base", "jurisdictions": ["j"], "steps": ["a", "b"],
        "source_types": ["base"], "source_models": {"base": model},
        "observations": [], "known_presence": []}
    narrow = dict(base, schema_version="process-occupancy-evidence/2", steps=["a"],
                  source_types=["base", "forum"],
                  source_models={"base": model, "forum": model},
                  observations=[{"jurisdiction_id": "j", "step_id": "a", "source_type": "forum",
                                 "detected": True, "reviewed_scope": True, "unit_id": "u",
                                 "dependence_group_id": "g", "evidence_refs": [{"path": "p", "sha256": "a"*64, "locator": "x"}],
                                 "identity_scope_id": "scope", "identity_scope_reviewed": True,
                                 "identity_scope_refs": [{"path": "p", "sha256": "a"*64, "locator": "scope"}]}],
                  uncertain_jurisdiction_units=[])
    registry = [{"step_id": "a", "actor": "applicant"},
                {"step_id": "b", "actor": "utility"}]
    data, report = expand_to_full_registry(base, narrow, registry, admit_added_sources=True)
    assert data["steps"] == ["a", "b"]
    assert len(data["observations"]) == 1
    assert report["direct_readings_by_step"] == {"a": 1, "b": 0}
    assert report["steps_without_any_direct_reading"] == ["b"]
    assert report["synthetic_nondetections"] == 0


def test_default_retains_unreviewed_added_source_outside_likelihood():
    model = {"detection_beta": [2, 2], "false_positive_probability": .02}
    base = {"schema_version": "process-occupancy-evidence/1", "scope": "fixture",
            "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
            "conditional_independence": "assumed_given_presence_and_source_type_detection",
            "assumption_note": "base", "jurisdictions": ["j"], "steps": ["a", "b"],
            "source_types": ["base"], "source_models": {"base": model},
            "observations": [], "known_presence": []}
    narrow = dict(base, schema_version="process-occupancy-evidence/2", steps=["a"],
                  source_types=["base", "forum"], source_models={"base": model, "forum": model},
                  observations=[{"source_type": "forum"}], uncertain_jurisdiction_units=[])
    registry = [{"step_id": "a", "actor": "applicant"}, {"step_id": "b", "actor": "utility"}]
    data, report = expand_to_full_registry(base, narrow, registry)
    assert data["observations"] == []
    assert "forum" not in data["source_types"]
    assert report["retained_not_admitted"]["resolved_readings"] == 1
    assert report["added_sources_route"] == "retained_descriptive_not_likelihood"
