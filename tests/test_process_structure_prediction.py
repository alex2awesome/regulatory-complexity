import copy

import numpy as np
import pytest

from pipeline.procbench.process_structure.prediction import (
    detection_baseline, leave_jurisdiction_readings_out, predict_readings, score_readings,
)


def fixture():
    data = dict(schema_version="process-occupancy-evidence/1", scope="fixture only",
                opportunity_frame="reviewed_units_not_selected_for_step_mentions",
                conditional_independence="assumed_given_presence_and_source_type_detection",
                assumption_note="Independent source-free fixture units.",
                jurisdictions=["A", "B"], steps=["interview"], source_types=["guide"],
                source_models={"guide": dict(detection_beta=[2, 2], false_positive_probability=.1)},
                observations=[], known_presence=[])
    for i, j in enumerate(data["jurisdictions"]):
        ref = dict(path=f"source_{j}", sha256=str(i)*64, locator="whole fixture")
        data["observations"].append(dict(unit_id=j, dependence_group_id=j, jurisdiction_id=j,
            step_id="interview", source_type="guide", detected=not bool(i), reviewed_scope=True,
            evidence_refs=[ref], lineage_reviewed=True, lineage_refs=[]))
    return data


def test_holdout_removes_all_county_readings_without_changing_input():
    data = fixture()
    training, held = leave_jurisdiction_readings_out(data, "B")
    assert len(training["observations"]) == len(held) == 1
    assert training["observations"][0]["jurisdiction_id"] == "A"
    assert len(data["observations"]) == 2
    assert training["jurisdictions"] == ["A", "B"]


def test_explicit_identity_policy_excludes_overlap_and_retains_disjoint_episode():
    data = fixture()
    data["schema_version"] = "process-occupancy-evidence/2"
    data["jurisdictions"].append("C")
    data["observations"].extend([
        dict(unit_id="C", dependence_group_id="C", jurisdiction_id="C",
             step_id="interview", source_type="guide", detected=True,
             reviewed_scope=True,
             evidence_refs=[dict(path="source_C", sha256="2" * 64, locator="whole fixture")],
             lineage_reviewed=True, lineage_refs=[]),
    ])
    data["uncertain_jurisdiction_units"] = [
        {
            "unit_id": "episode-overlap", "dependence_group_id": "episode-overlap",
            "source_type": "guide", "identity_reviewed": True,
            "identity_scope_id": "scope:episode-overlap", "identity_scope_reviewed": True,
            "identity_scope_refs": [dict(path="scope-overlap", sha256="3" * 64, locator="whole")],
            "candidate_scope_complete": True, "assignment_prior_basis": "reviewed fixture",
            "assignment_prior_kind": "reviewed_candidate_weights",
            "assignment_prior_refs": [dict(path="prior-overlap", sha256="4" * 64, locator="whole")],
            "lineage_reviewed": True, "lineage_refs": [],
            "candidates": [{"jurisdiction_id": "A", "prior_weight": 3.0},
                           {"jurisdiction_id": "B", "prior_weight": 2.0}],
            "reviewed_step_ids": ["interview"],
            "readings": [{"step_id": "interview", "detected": True,
                          "reviewed_scope": True,
                          "evidence_refs": [dict(path="reading-overlap", sha256="5" * 64, locator="whole")]}],
        },
        {
            "unit_id": "episode-disjoint", "dependence_group_id": "episode-disjoint",
            "source_type": "guide", "identity_reviewed": True,
            "identity_scope_id": "scope:episode-disjoint", "identity_scope_reviewed": True,
            "identity_scope_refs": [dict(path="scope-disjoint", sha256="6" * 64, locator="whole")],
            "candidate_scope_complete": True, "assignment_prior_basis": "reviewed fixture",
            "assignment_prior_kind": "reviewed_candidate_weights",
            "assignment_prior_refs": [dict(path="prior-disjoint", sha256="7" * 64, locator="whole")],
            "lineage_reviewed": True, "lineage_refs": [],
            "candidates": [{"jurisdiction_id": "A", "prior_weight": 3.0},
                           {"jurisdiction_id": "C", "prior_weight": 2.0}],
            "reviewed_step_ids": ["interview"],
            "readings": [{"step_id": "interview", "detected": False,
                          "reviewed_scope": True,
                          "evidence_refs": [dict(path="reading-disjoint", sha256="8" * 64, locator="whole")]}],
        },
    ]
    original = copy.deepcopy(data)

    training, held = leave_jurisdiction_readings_out(
        data, "B", uncertain_identity_policy="exclude_candidate_overlap")
    receipt = training["holdout_receipt"]

    assert {row["jurisdiction_id"] for row in held} == {"B"}
    assert [unit["unit_id"] for unit in training["uncertain_jurisdiction_units"]] == ["episode-disjoint"]
    assert training["uncertain_jurisdiction_units"][0]["candidates"] == [
        {"jurisdiction_id": "A", "prior_weight": 3.0},
        {"jurisdiction_id": "C", "prior_weight": 2.0},
    ]
    assert receipt["target"] == "known_county_source_mentions_not_latent_presence_truth"
    assert receipt["posterior_identity_used"] is False
    assert receipt["candidate_weights_renormalized"] is False
    assert receipt["excluded_identity_units"] == [{
        "unit_id": "episode-overlap", "dependence_group_id": "episode-overlap",
        "reason": "candidate_set_intersects_heldout_jurisdiction",
        "original_candidates": [
            {"jurisdiction_id": "A", "prior_weight": 3.0},
            {"jurisdiction_id": "B", "prior_weight": 2.0},
        ],
    }]
    assert data == original

    # A candidate-disjoint episode still cannot cross the held-out source
    # boundary when its reviewed evidence is a derivative of that source.
    boundary = copy.deepcopy(data)
    boundary["uncertain_jurisdiction_units"][1]["readings"][0]["evidence_refs"] = [
        dict(path="source_B", sha256="1" * 64, locator="a different reviewed span")
    ]
    boundary_train, _ = leave_jurisdiction_readings_out(
        boundary, "B", uncertain_identity_policy="exclude_candidate_overlap")
    boundary_receipt = boundary_train["holdout_receipt"]
    assert boundary_train["uncertain_jurisdiction_units"] == []
    assert any(item["unit_id"] == "episode-disjoint"
               and item["reason"] == "source_lineage_overlaps_heldout_target"
               for item in boundary_receipt["excluded_identity_units"])

    missing_lineage = copy.deepcopy(data)
    del missing_lineage["uncertain_jurisdiction_units"][1]["lineage_reviewed"]
    del missing_lineage["uncertain_jurisdiction_units"][1]["lineage_refs"]
    with pytest.raises(ValueError, match="reviewed source lineage"):
        leave_jurisdiction_readings_out(
            missing_lineage, "B", uncertain_identity_policy="exclude_candidate_overlap")


def test_explicit_identity_policy_rejects_unknown_policy():
    with pytest.raises(ValueError, match="Unknown uncertain identity holdout policy"):
        leave_jurisdiction_readings_out(fixture(), "B", uncertain_identity_policy="posterior")


@pytest.mark.parametrize("kind", ["copy", "alias", "lineage", "unreviewed"])
def test_rejects_reference_overlap_and_unreviewed_lineage(kind):
    data = fixture()
    a, b = data["observations"]
    if kind == "copy":
        b["evidence_refs"][0]["sha256"] = a["evidence_refs"][0]["sha256"]
    elif kind == "alias":
        b["evidence_refs"][0]["path"] = "./somewhere/../source_A"
    elif kind == "lineage":
        b["lineage_refs"] = copy.deepcopy(a["evidence_refs"])
    else:
        b["lineage_reviewed"] = False
    with pytest.raises(ValueError):
        leave_jurisdiction_readings_out(data, "B")


def test_prediction_preserves_presence_detection_covariance():
    data = fixture()
    posterior = dict(numerically_usable=True, jurisdictions=data["jurisdictions"],
                     steps=data["steps"], source_types=data["source_types"])
    q = np.array([[[[0.], [0.]], [[1.], [1.]]]])
    p = np.array([[[[.2]], [[.8]]]])
    predicted = predict_readings(posterior, dict(conditional_presence=q, detection=p),
                                data["observations"], data["source_models"])
    assert predicted[0]["probability"] == pytest.approx(.45)
    assert predicted[0]["probability"] != pytest.approx(.5*.5 + .5*.1)
    posterior["numerically_usable"] = False
    with pytest.raises(ValueError, match="failed"):
        predict_readings(posterior, dict(conditional_presence=q, detection=p),
                         data["observations"], data["source_models"])


def test_mention_baseline_uses_only_training_readings():
    data = fixture()
    training, held = leave_jurisdiction_readings_out(data, "B")
    pred = detection_baseline(training, held, stratify_source_type=True)
    assert pred[0]["probability"] == pytest.approx(2/3)
    held[0]["detected"] = True
    assert detection_baseline(training, held, stratify_source_type=True) == pred


def test_scores_are_detection_not_presence_and_infinite_loss_is_preserved():
    data = fixture()
    predictions = [dict(row, probability=float(row["detected"])) for row in data["observations"]]
    score = score_readings(predictions, data["observations"])
    assert score["micro"]["brier"] == 0
    assert not score["scientific_presence_validation"]
    predictions[0]["probability"] = 0
    score = score_readings(predictions, data["observations"])
    assert score["micro"]["infinite_log_loss"]
    assert score["micro"]["mean_log_loss"] is None
    with pytest.raises(ValueError, match="exactly matching"):
        score_readings(predictions[:1], data["observations"])
