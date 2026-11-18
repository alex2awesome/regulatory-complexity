import hashlib

from pipeline.procbench.process_structure.official_instruction_bridge import add_official_instruction_anchors


def test_positive_claims_collapse_to_anchor_and_silence_is_not_absence(tmp_path):
    source = tmp_path / "held.txt"
    source.write_text("reviewed requirement")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    base = {
        "schema_version": "process-occupancy-evidence/1",
        "scope": "fixture", "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "fixture", "jurisdictions": ["x_county"], "steps": ["step"],
        "source_types": ["doc"], "source_models": {"doc": {"detection_beta": [2, 2], "false_positive_probability": .02}},
        "observations": [], "known_presence": []
    }
    claim = {"county": "X", "mapped_action_id": "step", "status": "required",
             "source": {"text_path": "held.txt", "lines": "1", "quote": "reviewed requirement"}}
    additions = {"schema_version": "additions/fixture",
                 "mapped_ahj_action_claims": [dict(claim, claim_id="a"), dict(claim, claim_id="b")],
                 "conditional_absences": [{"claim_id": "outside", "mapped_action_id": None}],
                 "silence_not_absence": [{"county": "X", "route_variant": "ordinary"}]}
    data, report = add_official_instruction_anchors(
        base, additions, {"X": {"jurisdiction_id": "x_county", "basis": "explicit county authority"}},
        source_root=tmp_path)
    assert len(data["known_presence"]) == 1
    assert data["known_presence"][0]["official_claim_ids"] == ["a", "b"]
    assert data["known_presence"][0]["evidence_refs"][0]["sha256"] == digest
    assert report["added_presence_anchors"] == 1
    assert report["added_likelihood_detection_trials"] == 0
    assert not any(row.get("basis") == "explicit_absence" for row in data["known_presence"])
    assert {row["disposition"] for row in report["routes"] if "disposition" in row} >= {
        "consumed_in_presence_anchor", "retained_outside_registry", "silence_retained_no_likelihood"}
