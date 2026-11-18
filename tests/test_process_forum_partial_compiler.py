"""Focused contract tests for opt-in partial forum checklists."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import types

import pytest

from pipeline.procbench.process_structure.forum import add_reviewed_episodes
from pipeline.procbench.process_structure.occupancy import Evidence, verify_source_bindings
from pipeline.procbench.process_structure.solar_forum_bridge import _mix_unresolved_identity


ARCHIVE = (Path(__file__).resolve().parents[1]
           / "runs/process_structure_20260921/calfresh_phase2/mixed_sources_corrected"
           / "reproducibility_snapshot")


def _source(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _quote(path, digest, literal):
    start = path.read_text().index(literal)
    return {"path": path.name, "sha256": digest, "char_start": start,
            "char_end": start + len(literal), "quote": literal}


def _ref(path, digest, locator):
    return {"path": path.name, "sha256": digest, "locator": locator}


def _base():
    return {
        "schema_version": "process-occupancy-evidence/1",
        "scope": "source-free partial forum fixture",
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Source-free fixture.",
        "jurisdictions": ["A", "B"],
        "steps": ["file_application", "interview_encounter", "request_verification"],
        "source_types": ["guide"],
        "source_models": {
            "guide": {"detection_beta": [2., 2.], "false_positive_probability": .02}
        },
        "observations": [], "known_presence": [],
    }


def _episode(source_path, source_hash, scope_path, scope_hash, *, jurisdiction="A"):
    filed = _quote(source_path, source_hash, "filed")
    result = {
        "episode_id": "partial-episode", "root_adopted": True,
        "complete_capture_read": True, "actor_and_lifecycle_reviewed": True,
        "identity_scope_id": "episode:partial", "identity_scope_reviewed": True,
        "identity_scope_refs": [_ref(source_path, source_hash, "captured episode root")],
        "dependence_group_id": "group:partial", "jurisdiction_id": jurisdiction,
        "county_quotes": [_quote(source_path, source_hash, "A")] if jurisdiction else [],
        "reading_scope_kind": "reviewed_fixed_subset",
        "reviewed_step_ids": ["file_application"],
        "step_scope_reviewed": True,
        "step_scope_rationale": "Only filing was reviewed in this bounded source-free pass.",
        "step_scope_refs": [_ref(scope_path, scope_hash, "reviewed subset declaration")],
        "readings": [{"step_id": "file_application", "detected": True,
                      "quotes": [filed]}],
    }
    if jurisdiction is None:
        result.update(
            candidates=[{"jurisdiction_id": "A", "prior_weight": 1.},
                        {"jurisdiction_id": "B", "prior_weight": 1.}],
            assignment_prior_kind="symmetric_bounded_context",
            assignment_prior_basis="Source-free exhaustive candidates.",
            identity_context_quotes=[filed],
        )
    return result


def _packet(episode):
    return {
        "schema_version": "reviewed-forum-occupancy-episodes/1",
        "packet_id": "partial-source-free", "root_adopted": True,
        "dependence_reviewed": True,
        "dependence_qualification": "One distinct source-free episode.",
        "selected_thread_count": 1, "jurisdictions": ["A", "B"],
        "episodes": [episode],
    }


def _inputs(tmp_path, *, jurisdiction="A"):
    source, source_hash = _source(tmp_path, "episode.txt", "A applicant filed.")
    scope, scope_hash = _source(tmp_path, "scope.txt", "Reviewed filing only.")
    return source, scope, _episode(source, source_hash, scope, scope_hash,
                                    jurisdiction=jurisdiction)


def _archived_forum():
    paths = {
        "_forum_archive": ARCHIVE / "pipeline",
        "_forum_archive.procbench": ARCHIVE / "pipeline/procbench",
        "_forum_archive.procbench.process_structure": ARCHIVE / "pipeline/procbench/process_structure",
    }
    for name, path in paths.items():
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package
    name = "_forum_archive.procbench.process_structure.forum"
    spec = importlib.util.spec_from_file_location(
        name, paths["_forum_archive.procbench.process_structure"] / "forum.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_default_whole_checklist_output_exactly_replays_frozen_compiler(tmp_path):
    source, source_hash = _source(tmp_path, "whole.txt", "A applicant filed.")
    ep = _episode(source, source_hash, source, source_hash)
    ep.pop("reading_scope_kind")
    ep.pop("step_scope_reviewed")
    ep.pop("step_scope_rationale")
    ep.pop("step_scope_refs")
    ep["reviewed_step_ids"] = list(_base()["steps"])
    ep["readings"] = [
        {"step_id": "file_application", "detected": True,
         "quotes": [_quote(source, source_hash, "filed")]},
        {"step_id": "interview_encounter", "detected": False, "quotes": []},
        {"step_id": "request_verification", "detected": False, "quotes": []},
    ]
    current = add_reviewed_episodes(_base(), _packet(ep), source_root=tmp_path)
    archived = _archived_forum().add_reviewed_episodes(
        _base(), _packet(ep), source_root=tmp_path)
    assert current == archived


def test_resolved_partial_episode_preserves_scope_and_leaves_unread_cells_empty(tmp_path):
    _, scope, episode = _inputs(tmp_path)
    data = add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)
    assert len(data["observations"]) == 1
    row = data["observations"][0]
    assert row["reading_scope_kind"] == "reviewed_fixed_subset"
    assert row["reviewed_step_ids"] == ["file_application"]
    assert row["step_scope_reviewed"] is True
    assert row["step_scope_rationale"] == episode["step_scope_rationale"]
    assert row["step_scope_refs"] == episode["step_scope_refs"]
    assert any(ref["path"] == scope.name for ref in row["evidence_refs"])
    evidence = Evidence(data)
    j, k = evidence.j["A"], evidence.k["forum_initial_episode"]
    assert evidence.positive[j, evidence.s["file_application"], k] == 1
    for step in ("interview_encounter", "request_verification"):
        s = evidence.s[step]
        assert evidence.positive[j, s, k] == 0
        assert evidence.negative[j, s, k] == 0
    assert verify_source_bindings(data, tmp_path) == 2


def test_uncertain_partial_episode_is_one_identity_unit_with_only_reviewed_rows(tmp_path):
    _, _, episode = _inputs(tmp_path, jurisdiction=None)
    data = add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)
    assert data["observations"] == []
    unit = data["uncertain_jurisdiction_units"][0]
    assert unit["reading_scope_kind"] == "reviewed_fixed_subset"
    assert unit["reviewed_step_ids"] == ["file_application"]
    assert len(unit["readings"]) == 1
    evidence = Evidence(data)
    h, k = 0, evidence.k["forum_initial_episode"]
    assert evidence.identity.positive[h, evidence.s["file_application"], k] == 1
    for step in ("interview_encounter", "request_verification"):
        s = evidence.s[step]
        assert evidence.identity.positive[h, s, k] == 0
        assert evidence.identity.negative[h, s, k] == 0
    assert verify_source_bindings(data, tmp_path) == 2


def test_unresolved_fallback_binding_reaches_identity_prior_and_byte_closure(tmp_path):
    _, _, episode = _inputs(tmp_path, jurisdiction=None)
    fallback, fallback_hash = _source(tmp_path, "fallback.json", '{"A":0,"B":1}')
    episode.update(
        occurrence_reviewed=True, statistic="individual",
        candidates=[{"jurisdiction_id": "A", "prior_weight": 1.}],
        candidate_unresolved_mass=.5,
        unresolved_identity_fallback={
            "schema_version": "unresolved-identity-fallback/1",
            "assumption_label": "external two-authority sensitivity frame",
            "independence_declaration": "source_independent_of_episode_action_and_timing",
            "source_refs": [_ref(fallback, fallback_hash, "$.declared_q")],
            "candidates": [{"jurisdiction_id": "B", "prior_weight": 1.}],
        },
    )
    mixed = _mix_unresolved_identity(episode, .5)
    data = add_reviewed_episodes(_base(), _packet(mixed), source_root=tmp_path)
    evidence = Evidence(data)
    assert evidence.identity.priors[0, evidence.j["A"]] == .5
    assert evidence.identity.priors[0, evidence.j["B"]] == .5
    unit = data["uncertain_jurisdiction_units"][0]
    assert unit["unresolved_identity_mixture"]["named_mass"] == .5
    assert any(ref["path"] == fallback.name for ref in unit["assignment_prior_refs"])
    assert verify_source_bindings(data, tmp_path) == 3


def test_missing_subset_opt_in_remains_a_failed_incomplete_whole_checklist(tmp_path):
    _, _, episode = _inputs(tmp_path)
    episode.pop("reading_scope_kind")
    with pytest.raises(ValueError, match="whole fixed action checklist"):
        add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)


@pytest.mark.parametrize("field", [
    "step_scope_reviewed", "step_scope_rationale", "step_scope_refs",
])
def test_partial_episode_requires_all_review_metadata(tmp_path, field):
    _, _, episode = _inputs(tmp_path)
    episode.pop(field)
    with pytest.raises(ValueError, match="reviewed scope metadata|source-bound"):
        add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)


def test_partial_scope_reference_bytes_are_verified_before_compilation(tmp_path):
    _, scope, episode = _inputs(tmp_path)
    scope.write_text("Changed after review.\n")
    with pytest.raises(ValueError, match="Changed forum step scope source"):
        add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)


@pytest.mark.parametrize("mutation", ["wrong_row", "extra_row", "duplicate_id", "unknown_id"])
def test_partial_rows_must_exactly_match_nonempty_distinct_reviewed_subset(tmp_path, mutation):
    _, _, episode = _inputs(tmp_path)
    if mutation == "wrong_row":
        episode["readings"][0]["step_id"] = "interview_encounter"
    elif mutation == "extra_row":
        episode["readings"].append({"step_id": "interview_encounter",
                                    "detected": False, "quotes": []})
    elif mutation == "duplicate_id":
        episode["reviewed_step_ids"] = ["file_application", "file_application"]
        episode["readings"].append(copy.deepcopy(episode["readings"][0]))
    else:
        episode["reviewed_step_ids"] = ["unreviewed_new_step"]
        episode["readings"][0]["step_id"] = "unreviewed_new_step"
    with pytest.raises(ValueError, match="exact distinct step rows"):
        add_reviewed_episodes(_base(), _packet(episode), source_root=tmp_path)
