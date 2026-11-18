import copy
import json
import math

import pytest

from pipeline.procbench.process_structure.validation import (
    baseline_predictions, jurisdiction_split, reference_holdout, score_presence,
)


def fixture():
    data = dict(schema_version="process-occupancy-evidence/1", scope="fixture initial era",
                jurisdictions=["A", "B", "C"], steps=["interview"], source_types=["forum"],
                source_models={"forum": {"detection_beta": [2, 2], "false_positive_probability": .1}},
                opportunity_frame="reviewed_units_not_selected_for_step_mentions",
                conditional_independence="assumed_given_presence_and_source_type_detection",
                assumption_note="Source-free fixture.", observations=[], known_presence=[])
    for j, present in [("A", True), ("B", False), ("C", True)]:
        data["known_presence"].append(dict(jurisdiction_id=j, step_id="interview", unit_id=f"reference:{j}",
            present=present, basis="complete_inventory_review",
            evidence_refs=[dict(path="reference.csv", sha256="0" * 64, locator=j)]))
        data["observations"].append(dict(jurisdiction_id=j, step_id="interview", unit_id=f"case:{j}",
            dependence_group_id=f"case:{j}", source_type="forum", detected=True, reviewed_scope=True,
            evidence_refs=[dict(path=f"case_{j}.md", sha256="1" * 64, locator="post")],
            lineage_reviewed=True, lineage_refs=[]))
    return data


def test_split_order_invariant_and_nonempty_train_test():
    first = jurisdiction_split(["A", "B", "C", "D", "E"])
    assert first == jurisdiction_split(["E", "D", "C", "B", "A"])
    assert len(first["heldout_jurisdictions"]) == 1
    assert len(first["training_jurisdictions"]) == 4
    assert len(jurisdiction_split(["A", "B"], fraction=.99)["training_jurisdictions"]) == 1


@pytest.mark.parametrize("ids,fraction", [(["A"], .2), (["A", "A"], .2), (["A", "B"], 1),
                                          (["A", "B"], float("nan")), (["A", "B"], True)])
def test_bad_split_rejected(ids, fraction):
    with pytest.raises(ValueError):
        jurisdiction_split(ids, fraction=fraction)


def test_reference_only_retains_other_test_documents_but_not_labels():
    data = fixture()
    original = copy.deepcopy(data)
    train, labels, receipt = reference_holdout(data, ["C"], mode="reference_labels_only")
    assert len(train["observations"]) == 3
    assert [x["jurisdiction_id"] for x in train["known_presence"]] == ["A", "B"]
    assert len(labels) == 1 and labels[0]["jurisdiction_id"] == "C"
    assert receipt["excluded_observations"] == []
    assert original == data


def test_unseen_jurisdiction_removes_local_observations_too():
    train, _, receipt = reference_holdout(fixture(), ["C"], mode="unseen_jurisdiction")
    assert [x["jurisdiction_id"] for x in train["observations"]] == ["A", "B"]
    assert receipt["excluded_observations"][0]["reason"] == "unseen_jurisdiction"


def test_declared_reference_derivative_in_any_jurisdiction_is_removed():
    data = fixture()
    data["observations"][0]["lineage_refs"] = data["known_presence"][2]["evidence_refs"]
    train, _, receipt = reference_holdout(data, ["C"], mode="reference_labels_only")
    assert [x["jurisdiction_id"] for x in train["observations"]] == ["B", "C"]
    assert receipt["excluded_observations"][0]["reason"] == "reference_source_or_derivative"


def test_missing_lineage_review_is_not_silently_assumed_safe():
    data = fixture()
    del data["observations"][0]["lineage_reviewed"]
    with pytest.raises(ValueError, match="lineage"):
        reference_holdout(data, ["C"], mode="reference_labels_only")


@pytest.mark.parametrize("alias,sha", [("./reference.csv", "2" * 64),
                                      ("subdir/../reference.csv", "2" * 64),
                                      ("copied_reference.csv", "0" * 64)])
def test_reference_aliases_and_byte_identical_copies_are_excluded(alias, sha, tmp_path):
    data = fixture()
    data["observations"][0]["lineage_refs"] = [dict(path=alias, sha256=sha, locator="reference row")]
    train, _, receipt = reference_holdout(data, ["C"], mode="reference_labels_only", source_root=tmp_path)
    assert [x["jurisdiction_id"] for x in train["observations"]] == ["B", "C"]
    assert receipt["excluded_observations"][0]["reason"] == "reference_source_or_derivative"


def test_reference_symlink_alias_uses_same_source_root_as_runner(tmp_path):
    (tmp_path / "reference.csv").write_text("Reference fixture")
    (tmp_path / "alias.csv").symlink_to(tmp_path / "reference.csv")
    data = fixture()
    data["observations"][0]["lineage_refs"] = [dict(path="alias.csv", sha256="2" * 64, locator="field")]
    train, _, _ = reference_holdout(data, ["C"], mode="reference_labels_only", source_root=tmp_path)
    assert [x["jurisdiction_id"] for x in train["observations"]] == ["B", "C"]


def test_scores_macro_and_micro_differ_for_unequal_counties():
    cells = [("A", "one", True, .8), ("A", "two", False, .2), ("B", "one", True, .5)]
    labels = [dict(jurisdiction_id=j, step_id=s, present=y) for j, s, y, _ in cells]
    pred = [dict(jurisdiction_id=j, step_id=s, probability=p) for j, s, _, p in cells]
    result = score_presence(pred, labels, bins=5)
    assert result["micro"]["brier"] == pytest.approx(.11)
    assert result["jurisdiction_macro"]["brier"] == pytest.approx(.145)
    assert result["micro"]["mean_log_loss"] == pytest.approx((-2 * math.log(.8) - math.log(.5)) / 3)
    assert sum(x["cells"] for x in result["calibration_bins"]) == 3
    assert not result["scientific_release_eligible"]


def test_extreme_probabilities_are_not_clipped_and_are_json_safe():
    labels = [dict(jurisdiction_id="A", step_id="one", present=False)]
    pred = [dict(jurisdiction_id="A", step_id="one", probability=1.)]
    result = score_presence(pred, labels)
    assert result["micro"]["infinite_log_loss"]
    assert result["micro"]["mean_log_loss"] is None
    assert result["micro"]["impossible_outcomes"] == 1
    assert result["calibration_bins"][-1]["cells"] == 1
    json.dumps(result, allow_nan=False)


def test_score_requires_exact_distinct_coverage():
    labels = [dict(jurisdiction_id="A", step_id="one", present=True)]
    pred = [dict(jurisdiction_id="A", step_id="one", probability=.5)]
    for invalid in ([], pred + pred, [dict(pred[0], step_id="other")]):
        with pytest.raises(ValueError, match="exactly"):
            score_presence(invalid, labels)


def test_baselines_ignore_test_outcomes_and_only_use_training_labels():
    train, labels, _ = reference_holdout(fixture(), ["C"], mode="reference_labels_only")
    result = baseline_predictions(train, labels)
    assert result["observed_only"][0]["probability"] == 1.
    assert result["pooled_training_reference_prevalence"][0]["probability"] == .5
    labels[0]["present"] = False
    assert baseline_predictions(train, labels) == result
    with pytest.raises(ValueError, match="cannot remain"):
        baseline_predictions(fixture(), labels)
