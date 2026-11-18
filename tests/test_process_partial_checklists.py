"""Bounded review of fixed-subset occupancy and holdout linkage contracts."""
from __future__ import annotations

import copy
import hashlib

import numpy as np
import pytest

from pipeline.procbench.process_structure.occupancy import Evidence, verify_source_bindings
from pipeline.procbench.process_structure.prediction import leave_jurisdiction_readings_out


def ref(name: str, digest: str | None = None):
    return {"path": f"sources/{name}.json", "sha256": digest or hashlib.sha256(name.encode()).hexdigest(), "locator": f"$.{name}"}


def row(jurisdiction, step, detected):
    return {
        "unit_id": f"fixed-{jurisdiction}", "dependence_group_id": f"fixed-{jurisdiction}",
        "jurisdiction_id": jurisdiction, "step_id": step, "source_type": "forum",
        "detected": detected, "reviewed_scope": True,
        "evidence_refs": [ref(f"{jurisdiction}-{step}")], "lineage_reviewed": True,
        "lineage_refs": [],
    }


def fixture():
    data = {
        "schema_version": "process-occupancy-evidence/2",
        "scope": "fixed-subset review fixture",
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": "Source-free bounded fixture.",
        "jurisdictions": ["A", "B"], "steps": ["s1", "s2"], "source_types": ["forum"],
        "source_models": {"forum": {"detection_beta": [2.0, 2.0], "false_positive_probability": .1}},
        "observations": [row("A", "s1", True), row("A", "s2", False),
                         row("B", "s1", False), row("B", "s2", True)],
        "known_presence": [],
        "uncertain_jurisdiction_units": [{
            "unit_id": "uncertain", "dependence_group_id": "uncertain", "source_type": "forum",
            "identity_reviewed": True, "identity_scope_id": "scope:uncertain",
            "identity_scope_reviewed": True, "identity_scope_refs": [ref("identity")],
            "candidate_scope_complete": True, "assignment_prior_basis": "bounded fixture",
            "assignment_prior_kind": "reviewed_candidate_weights", "assignment_prior_refs": [ref("prior")],
            "candidates": [{"jurisdiction_id": "A", "prior_weight": 1.0},
                           {"jurisdiction_id": "B", "prior_weight": 1.0}],
            "reviewed_step_ids": ["s1", "s2"],
            "readings": [{"step_id": "s1", "detected": True, "reviewed_scope": True,
                          "evidence_refs": [ref("uncertain-s1")]},
                         {"step_id": "s2", "detected": False, "reviewed_scope": True,
                          "evidence_refs": [ref("uncertain-s2")]}],
        }],
    }
    return data


def test_subset_leaves_unread_new_steps_out_of_both_counts_and_likelihood():
    data = fixture()
    unit = data["uncertain_jurisdiction_units"][0]
    unit.update(reading_scope_kind="reviewed_fixed_subset", step_scope_reviewed=True,
                step_scope_rationale="Frozen legacy checklist reviewed only s1.",
                step_scope_refs=[ref("fixed-checklist-scope")], reviewed_step_ids=["s1"])
    unit["readings"] = unit["readings"][:1]
    evidence = Evidence(data)
    assert evidence.identity.positive[0, 0, 0] == 1
    assert evidence.identity.negative[0, 1, 0] == 0
    assert evidence.identity.positive[0, 1, 0] == 0
    presence = np.array([[1, 0], [0, 1]])
    detection = np.array([[.6], [.4]])
    before = evidence.identity.conditional_probabilities(presence, detection)
    presence[:, 1] = 1 - presence[:, 1]
    detection[1] = .99
    np.testing.assert_allclose(evidence.identity.conditional_probabilities(presence, detection), before)


def test_omitted_scope_kind_remains_strict_complete_universe():
    data = fixture()
    unit = data["uncertain_jurisdiction_units"][0]
    unit["reviewed_step_ids"] = ["s1"]
    unit["readings"] = unit["readings"][:1]
    with pytest.raises(ValueError, match="complete reviewed fixed step checklist"):
        Evidence(data)


@pytest.mark.parametrize("field", ["step_scope_reviewed", "step_scope_rationale", "step_scope_refs"])
def test_subset_requires_bound_scope_metadata(field):
    data = fixture()
    unit = data["uncertain_jurisdiction_units"][0]
    unit.update(reading_scope_kind="reviewed_fixed_subset", step_scope_reviewed=True,
                step_scope_rationale="Fixed s1 scope.", step_scope_refs=[ref("scope")],
                reviewed_step_ids=["s1"])
    unit["readings"] = unit["readings"][:1]
    del unit[field]
    with pytest.raises(ValueError):
        Evidence(data)


def test_subset_rejects_unhashable_step_name_closed():
    data = fixture()
    unit = data["uncertain_jurisdiction_units"][0]
    unit.update(reading_scope_kind="reviewed_fixed_subset", step_scope_reviewed=True,
                step_scope_rationale="Fixed scope.", step_scope_refs=[ref("scope")],
                reviewed_step_ids=["s1", ["s2"]])
    with pytest.raises((ValueError, TypeError)):
        Evidence(data)


def test_step_scope_reference_is_byte_verified(tmp_path):
    source = tmp_path / "scope.json"
    source.write_text('{"steps":["s1"]}\n')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    data = {"observations": [], "known_presence": [],
            "uncertain_jurisdiction_units": [{"readings": [], "identity_scope_refs": [],
                "assignment_prior_refs": [], "step_scope_refs": [{
                "path": source.name, "sha256": digest, "locator": "$.steps"}]}]}
    assert verify_source_bindings(data, tmp_path) == 1
    source.write_text('{"steps":["s2"]}\n')
    with pytest.raises(ValueError, match="Changed source binding"):
        verify_source_bindings(data, tmp_path)


@pytest.mark.parametrize("owner", ["row", "unit"])
def test_lineage_references_are_byte_verified_at_row_and_unit_level(tmp_path, owner):
    source = tmp_path / f"{owner}-lineage.json"
    source.write_text('{"lineage":1}\n')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    lineage = [{"path": source.name, "sha256": digest, "locator": "$.lineage"}]
    if owner == "row":
        data = {"observations": [{"evidence_refs": lineage, "lineage_refs": lineage}],
                "known_presence": [], "uncertain_jurisdiction_units": []}
    else:
        data = {"observations": [], "known_presence": [],
                "uncertain_jurisdiction_units": [{"readings": [], "identity_scope_refs": [],
                    "assignment_prior_refs": [], "step_scope_refs": [], "lineage_refs": lineage}]}
    assert verify_source_bindings(data, tmp_path) == 1
    source.write_text('{"lineage":2}\n')
    with pytest.raises(ValueError, match="Changed source binding"):
        verify_source_bindings(data, tmp_path)


def test_malformed_lineage_reference_is_rejected_before_path_use(tmp_path):
    data = {"observations": [], "known_presence": [],
            "uncertain_jurisdiction_units": [{"readings": [], "identity_scope_refs": [],
                "assignment_prior_refs": [], "step_scope_refs": [],
                "lineage_refs": [{"path": "bad", "sha256": "not-a-digest", "locator": "$.x"}]}]}
    with pytest.raises(ValueError, match="Evidence references need path"):
        verify_source_bindings(data, tmp_path)


def test_holdout_excludes_candidate_disjoint_unit_when_step_scope_reuses_held_source():
    data = fixture()
    data["jurisdictions"].append("C")
    for observation in data["observations"]:
        observation["lineage_reviewed"] = True
    data["observations"].append(row("C", "s1", True))
    unit = data["uncertain_jurisdiction_units"][0]
    unit["candidates"] = [{"jurisdiction_id": "A", "prior_weight": 1.0},
                           {"jurisdiction_id": "C", "prior_weight": 1.0}]
    unit["lineage_reviewed"] = True
    unit["lineage_refs"] = []
    held_ref = data["observations"][2]["evidence_refs"][0]
    unit.update(reading_scope_kind="reviewed_fixed_subset", step_scope_reviewed=True,
                step_scope_rationale="Fixed legacy s1 scope.", step_scope_refs=[copy.deepcopy(held_ref)],
                reviewed_step_ids=["s1"])
    unit["readings"] = unit["readings"][:1]
    training, held = leave_jurisdiction_readings_out(
        data, "B", uncertain_identity_policy="exclude_candidate_overlap")
    assert len(held) == 2
    assert training["uncertain_jurisdiction_units"] == []
    assert training["holdout_receipt"]["excluded_identity_units"][0]["reason"] == "source_lineage_overlaps_heldout_target"
