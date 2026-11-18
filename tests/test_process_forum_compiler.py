"""Source-free contract checks for reviewed forum occupancy episodes."""
from __future__ import annotations

import copy
import hashlib

import pytest

from pipeline.procbench.process_structure.forum import add_reviewed_episodes
from pipeline.procbench.process_structure.occupancy import Evidence


def source(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def quote(path, digest, literal):
    text = path.read_text()
    start = text.index(literal)
    return {"path": path.name, "sha256": digest, "char_start": start,
            "char_end": start+len(literal), "quote": literal}


def base():
    return {
        "schema_version": "process-occupancy-evidence/1",
        "scope": "source-free initial application fixture",
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Source-free fixture.",
        "jurisdictions": ["A", "B"],
        "steps": ["file_application", "interview_encounter"],
        "source_types": ["guide"],
        "source_models": {
            "guide": {"detection_beta": [2.0, 2.0], "false_positive_probability": 0.02}
        },
        "observations": [],
        "known_presence": [],
    }


def episode(path, digest, name, *, jurisdiction, scope_id=None):
    filed = quote(path, digest, "filed")
    county = quote(path, digest, jurisdiction) if jurisdiction else []
    rows = [
        {"step_id": "file_application", "detected": True, "quotes": [filed]},
        {"step_id": "interview_encounter", "detected": False, "quotes": []},
    ]
    result = {
        "episode_id": name,
        "root_adopted": True,
        "complete_capture_read": True,
        "actor_and_lifecycle_reviewed": True,
        "identity_scope_id": scope_id or f"scope:{name}",
        "identity_scope_reviewed": True,
        "identity_scope_refs": [{"path": path.name, "sha256": digest, "locator": "$"}],
        "dependence_group_id": f"group:{name}",
        "jurisdiction_id": jurisdiction,
        "county_quotes": [county] if county else [],
        "reviewed_step_ids": ["file_application", "interview_encounter"],
        "readings": rows,
    }
    if jurisdiction is None:
        result.update(
            candidates=[{"jurisdiction_id": "A", "prior_weight": 1.0},
                        {"jurisdiction_id": "B", "prior_weight": 1.0}],
            assignment_prior_kind="symmetric_bounded_context",
            assignment_prior_basis="Source-free exhaustive two-county context.",
            identity_context_quotes=[filed],
        )
    return result


def packet(episodes):
    return {
        "schema_version": "reviewed-forum-occupancy-episodes/1",
        "packet_id": "source-free-forum-fixture",
        "root_adopted": True,
        "dependence_reviewed": True,
        "dependence_qualification": "Fixture logical episodes are distinct.",
        "selected_thread_count": len(episodes),
        "jurisdictions": ["A", "B"],
        "episodes": episodes,
    }


def test_compiles_known_and_uncertain_whole_checklists_without_mutating_base(tmp_path):
    known_path, known_hash = source(tmp_path, "known.txt", "A applicant filed.")
    unknown_path, unknown_hash = source(tmp_path, "unknown.txt", "Applicant filed.")
    known = episode(known_path, known_hash, "known", jurisdiction="A")
    unknown = episode(unknown_path, unknown_hash, "unknown", jurisdiction=None)
    original = base()
    data = add_reviewed_episodes(original, packet([known, unknown]), source_root=tmp_path)
    assert original == base()
    assert data["schema_version"] == "process-occupancy-evidence/2"
    assert len(data["observations"]) == 2
    assert len(data["uncertain_jurisdiction_units"]) == 1
    assert len(data["uncertain_jurisdiction_units"][0]["readings"]) == 2
    evidence = Evidence(data)
    assert evidence.support_report()["reading_opportunities"] == 4
    assert evidence.support_report()["positive_detections"] == 2
    assert data["forum_adoption"]["unresolved_identity_not_discarded"]


@pytest.mark.parametrize("mutation,match", [
    ("missing_step", "whole fixed action checklist"),
    ("hidden_positive", "positives need quotes"),
    ("hard_county_without_quote", "Resolved county"),
    ("changed_bytes", "Changed complete forum reading source"),
])
def test_incomplete_or_unbound_episode_fails_closed(tmp_path, mutation, match):
    path, digest = source(tmp_path, "episode.txt", "A applicant filed.")
    ep = episode(path, digest, "episode", jurisdiction="A")
    if mutation == "missing_step":
        ep["readings"].pop()
    elif mutation == "hidden_positive":
        ep["readings"][0]["detected"] = False
    elif mutation == "hard_county_without_quote":
        ep["county_quotes"] = []
    else:
        path.write_text("A changed applicant filed.\n")
    with pytest.raises(ValueError, match=match):
        add_reviewed_episodes(base(), packet([ep]), source_root=tmp_path)


def test_compiler_refuses_incremental_second_forum_packet(tmp_path):
    path, digest = source(tmp_path, "episode.txt", "A applicant filed.")
    first = add_reviewed_episodes(
        base(), packet([episode(path, digest, "episode", jurisdiction="A")]),
        source_root=tmp_path)
    with pytest.raises(ValueError, match="once"):
        add_reviewed_episodes(
            first, packet([episode(path, digest, "another", jurisdiction="A")]),
            source_root=tmp_path)


def test_same_canonical_episode_cannot_be_counted_in_two_resolved_counties(tmp_path):
    path, digest = source(tmp_path, "shared.txt", "A B applicant filed.")
    left = episode(path, digest, "left", jurisdiction="A", scope_id="same-episode")
    right = episode(path, digest, "right", jurisdiction="B", scope_id="same-episode")
    with pytest.raises(ValueError, match="[Cc]anonical|overlap|episode"):
        add_reviewed_episodes(base(), packet([left, right]), source_root=tmp_path)
