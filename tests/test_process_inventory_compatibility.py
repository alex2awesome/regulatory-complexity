import copy

import numpy as np
import pytest

from pipeline.procbench.process_structure.compatibility import (
    ATTESTATION_SCOPE, classify_inventory_draws, summarize_burden_functional,
)


def attestation():
    return {
        "reviewed": True,
        "scope": ATTESTATION_SCOPE,
        "review_note": "Source-free fixture rule semantics reviewed; helper does not prove them.",
        "source_refs": [{"path": "fixture", "sha256": "0" * 64, "locator": "fixture:rules"}],
    }


def rules():
    return [
        {
            "rule_id": "empty", "status": "all_zero", "unresolved": True,
            "required_present": [], "required_absent": [],
            "minimum_present_count": 0, "maximum_present_count": 0,
            "source_reviewed": True, "source_note": "Empty fixture mask.",
        },
        {
            "rule_id": "nonempty_without_entry", "status": "nonzero_no_entry", "unresolved": True,
            "required_present": [], "required_absent": ["entry"],
            "minimum_present_count": 1, "maximum_present_count": 3,
            "source_reviewed": True, "source_note": "Nonempty fixture mask without entry.",
        },
        {
            "rule_id": "entry_present", "status": "entry_present_execution_unresolved", "unresolved": True,
            "required_present": ["entry"], "required_absent": [],
            "minimum_present_count": 1, "maximum_present_count": 3,
            "source_reviewed": True, "source_note": "Entry is present; execution remains unresolved.",
        },
    ]


def fixture():
    # chain x draw x jurisdiction x step
    presence = np.array([
        [
            [[0, 0, 0], [0, 1, 0]],
            [[1, 0, 0], [1, 1, 1]],
        ],
        [
            [[0, 0, 1], [0, 0, 0]],
            [[1, 1, 0], [0, 1, 1]],
        ],
    ], dtype=np.uint8)
    return presence, ["A", "B"], ["entry", "middle", "outcome"]


def classified():
    presence, jurisdictions, steps = fixture()
    return classify_inventory_draws(
        presence, jurisdictions, steps, rules(), source_review_attestation=attestation()
    )


def test_every_draw_is_retained_aligned_and_classified_once():
    presence, jurisdictions, steps = fixture()
    result = classified()
    assert np.array_equal(result["joint_presence"], presence)
    assert result["classification_index"].shape == presence.shape[:3]
    assert result["draw_shape"] == [2, 2]
    assert result["jurisdictions"] == jurisdictions
    assert result["steps"] == steps
    assert result["county_draw_cells"] == result["retained_county_draw_cells"] == 8
    assert result["retained_mass"] == 1
    assert sum(row["county_draw_cells"] for row in result["rule_summary"]) == 8
    assert sum(row["mass"] for row in result["status_summary"]) == pytest.approx(1)
    assert result["unresolved_count"] == 8
    assert result["unresolved_mass"] == 1
    assert not result["route_vectors_created"] and not result["timings_created"]
    assert not result["reweighted"]
    expected = np.array([[[0, 1], [2, 2]], [[1, 0], [2, 1]]])
    assert np.array_equal(result["classification_index"], expected)


@pytest.mark.parametrize("bad", ["fraction", "shape", "float_dtype"])
def test_malformed_binary_draws_fail_closed(bad):
    presence, jurisdictions, steps = fixture()
    if bad == "fraction":
        presence = presence.astype(float)
        presence[0, 0, 0, 0] = .5
    elif bad == "shape":
        presence = presence[..., :2]
    else:
        presence = presence.astype(float)
    with pytest.raises(ValueError, match="binary inventories"):
        classify_inventory_draws(
            presence, jurisdictions, steps, rules(), source_review_attestation=attestation()
        )


def test_rule_overlap_and_uncovered_support_fail_closed():
    presence, jurisdictions, steps = fixture()
    overlapping = rules()
    overlapping.append({
        **copy.deepcopy(overlapping[0]), "rule_id": "also_empty", "status": "duplicate_empty",
    })
    with pytest.raises(ValueError, match="overlap"):
        classify_inventory_draws(
            presence, jurisdictions, steps, overlapping, source_review_attestation=attestation()
        )
    uncovered = rules()[1:]
    with pytest.raises(ValueError, match="uncovered"):
        classify_inventory_draws(
            presence, jurisdictions, steps, uncovered, source_review_attestation=attestation()
        )


@pytest.mark.parametrize("mutation", ["attestation", "rule_source", "unknown_step", "schema_extra"])
def test_source_attestation_and_rule_schema_fail_closed(mutation):
    presence, jurisdictions, steps = fixture()
    review, supplied = attestation(), rules()
    if mutation == "attestation":
        review["reviewed"] = False
    elif mutation == "rule_source":
        supplied[0]["source_reviewed"] = False
    elif mutation == "unknown_step":
        supplied[0]["required_present"] = ["invented"]
    else:
        supplied[0]["route_id"] = "fabricated"
    with pytest.raises(ValueError):
        classify_inventory_draws(
            presence, jurisdictions, steps, supplied, source_review_attestation=review
        )


def test_missing_functional_values_never_become_a_conditional_mean():
    result = classified()
    values = np.arange(8, dtype=object).reshape(2, 2, 2)
    values[0, 0, 0] = None
    summary = summarize_burden_functional(
        result, values, functional_id="elapsed", unit="days"
    )
    assert summary["unconditional_mean"] is None
    assert summary["undefined_count"] == 1
    assert summary["undefined_mass"] == pytest.approx(1 / 8)
    assert summary["conditional_mean_reported"] is False
    assert "conditional_mean" not in summary


def test_complete_functional_returns_only_the_unconditional_mean():
    result = classified()
    values = np.arange(8, dtype=float).reshape(2, 2, 2)
    summary = summarize_burden_functional(
        result, values, functional_id="count", unit="actions"
    )
    assert summary["unconditional_mean"] == pytest.approx(3.5)
    assert summary["undefined_mass"] == 0
    assert summary["conditional_mean_reported"] is False
    assert summary["aggregation_estimand"] == (
        "equal_weight_average_over_supplied_jurisdictions_not_applicant_population"
    )


@pytest.mark.parametrize("mutation", ["empty", "bad_index", "wrong_draw_shape", "wrong_retained_count"])
def test_forged_or_inconsistent_compatibility_metadata_fails_closed(mutation):
    result = classified()
    if mutation == "empty":
        result["classification_index"] = np.empty((0, 2, 2), dtype=np.int64)
        result["draw_shape"] = [0, 2]
        result["county_draw_cells"] = result["retained_county_draw_cells"] = 0
    elif mutation == "bad_index":
        result["classification_index"][0, 0, 0] = len(result["rules"])
    elif mutation == "wrong_draw_shape":
        result["draw_shape"] = [4, 1]
    else:
        result["retained_county_draw_cells"] -= 1
    values = np.zeros(np.asarray(result["classification_index"]).shape, dtype=float)
    with pytest.raises(ValueError, match="classification metadata"):
        summarize_burden_functional(
            result, values, functional_id="count", unit="actions"
        )


def endpoint(kind, value=None):
    return {"kind": kind, "value": value}


def test_explicit_bounds_preserve_unbounded_and_unknown_endpoints():
    result = classified()
    values = np.full((2, 2, 2), None, dtype=object)
    bounds = np.empty(values.shape, dtype=object)
    for location in np.ndindex(bounds.shape):
        bounds[location] = {"lower": endpoint("finite", 0), "upper": endpoint("finite", 10)}
    bounds[0, 0, 0]["upper"] = endpoint("unbounded")
    summary = summarize_burden_functional(
        result, values, functional_id="time", unit="days", identified_bounds=bounds
    )
    assert summary["unconditional_mean"] is None
    assert summary["undefined_mass"] == 1
    assert summary["identified_mean_bounds"] == {
        "lower": {"kind": "finite", "value": 0.0},
        "upper": {"kind": "unbounded", "value": None},
        "within_set_probabilities_assigned": False,
    }
    bounds[1, 1, 1]["upper"] = endpoint("unknown")
    unknown = summarize_burden_functional(
        result, values, functional_id="time", unit="days", identified_bounds=bounds
    )
    assert unknown["identified_mean_bounds"]["upper"] == {"kind": "unknown", "value": None}


def test_defined_functional_value_must_respect_explicit_finite_bounds():
    result = classified()
    values = np.zeros((2, 2, 2), dtype=object)
    values[0, 0, 0] = 10
    bounds = np.empty(values.shape, dtype=object)
    for location in np.ndindex(bounds.shape):
        bounds[location] = {"lower": endpoint("finite", 0), "upper": endpoint("finite", 1)}
    with pytest.raises(ValueError, match="outside its finite identified bounds"):
        summarize_burden_functional(
            result, values, functional_id="burden", unit="units", identified_bounds=bounds
        )


@pytest.mark.parametrize("bad", ["shape", "finite_null", "backwards", "nonfinite_value"])
def test_malformed_functionals_and_bounds_fail_closed(bad):
    result = classified()
    values = np.zeros((2, 2, 2), dtype=object)
    bounds = np.empty(values.shape, dtype=object)
    for location in np.ndindex(bounds.shape):
        bounds[location] = {"lower": endpoint("finite", 0), "upper": endpoint("finite", 1)}
    if bad == "shape":
        values = values[:, :, :1]
    elif bad == "finite_null":
        bounds[0, 0, 0]["lower"] = endpoint("finite")
    elif bad == "backwards":
        bounds[0, 0, 0] = {"lower": endpoint("finite", 2), "upper": endpoint("finite", 1)}
    else:
        values[0, 0, 0] = np.inf
    with pytest.raises(ValueError):
        summarize_burden_functional(
            result, values, functional_id="burden", unit="units", identified_bounds=bounds
        )
