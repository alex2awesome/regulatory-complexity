import copy
import math

import numpy as np
import pytest
from scipy.stats import multinomial

from pipeline.procbench.cohort_histograms import (
    cohort_histogram_observations,
    histogram_log_probability,
    population_bin_probabilities,
)


def histogram_fixture():
    return {
        "id": "published_histogram",
        "cohort_id": "county:2025-01:approved",
        "sample_size": 10,
        "bin_counts": [4, 3, 3],
        "bin_edges": [0, 3, 7, None],
        "reporting": "exact_event_duration_bin_counts",
        "bin_convention": "right_closed",
        "sampling": "iid_within_declared_population",
        "independent_of_other_evidence": True,
        "independent_of_other_cohorts": True,
        "same_cohort_mean_in_likelihood": False,
        "source_family": "administrative_table",
        "population": "approved initial applications in the declared county-month",
        "clock": {"start": "application", "end": "approval"},
        "time_unit": "calendar_days",
        "operators": [
            {"basis": "whole_case_clock", "start": "process_start", "end": "initial_decision"},
            {"basis": "single_visit_cycle", "activity_ids": ["review"]},
        ],
        "operator_weights": [0.25, 0.75],
        "provenance": {"document_id": "table", "cells": ["A1", "B1", "C1"]},
    }


def test_contract_returns_one_virtual_report_for_one_operator_mixture_without_mutation():
    cohort = histogram_fixture()
    original = copy.deepcopy(cohort)
    reports = cohort_histogram_observations(cohort)
    assert cohort == original
    assert len(reports) == 1
    report = reports[0]
    assert report["virtual_operator_check"] is True
    assert report["operators"] == cohort["operators"]
    assert report["operator_weights"] == [0.25, 0.75]
    assert report["bin_counts"] == [4, 3, 3]
    assert report["bin_edges"] == [0.0, 3.0, 7.0, None]
    assert report["reporting"] == "exact_event_duration_bin_counts"
    assert report["bin_convention"] == "right_closed"
    assert "statistic" not in report
    assert report["same_cohort_mean_in_likelihood"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_size", 0),
        ("sample_size", True),
        ("sample_size", 10.0),
        ("bin_counts", [4, 3, 2]),
        ("bin_counts", [4, 3, True]),
        ("bin_counts", [4, 3, -1]),
        ("bin_counts", [4, 3, None]),
        ("bin_counts", [4, 3, "*"]),
        ("bin_counts", [4, 3, {"lower": 0, "upper": 10}]),
        ("sampling", "completion_cohort"),
        ("independent_of_other_evidence", False),
        ("independent_of_other_cohorts", False),
        ("same_cohort_mean_in_likelihood", True),
        ("time_unit", "published_days"),
        ("time_unit", "business_days"),
        ("time_unit", ["calendar_days"]),
        ("reporting", "noisy_published_histogram"),
        ("bin_convention", "left_closed"),
    ],
)
def test_contract_rejects_invented_or_unsupported_count_semantics(field, value):
    cohort = histogram_fixture()
    cohort[field] = value
    with pytest.raises(ValueError):
        cohort_histogram_observations(cohort)


@pytest.mark.parametrize(
    "edges",
    [
        [1, 3, 7, None],
        [0, 3, 7, 10],
        [0, 3, 3, None],
        [0, 7, 3, None],
        [0, True, 7, None],
        [0, math.inf, None],
    ],
)
def test_contract_requires_complete_nonoverlapping_bins(edges):
    cohort = histogram_fixture()
    cohort["bin_edges"] = edges
    with pytest.raises(ValueError):
        cohort_histogram_observations(cohort)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda cohort: cohort.pop("clock"),
        lambda cohort: cohort.update(clock={"start": "application"}),
        lambda cohort: cohort.update(clock={"start": "approval", "end": "approval"}),
        lambda cohort: cohort.update(population=""),
        lambda cohort: cohort.update(operator_weights=[1.0]),
        lambda cohort: cohort.update(operator_weights=[True, 0.0]),
        lambda cohort: cohort.update(operator_weights=[0.2, 0.2]),
        lambda cohort: cohort.update(operators=[]),
        lambda cohort: cohort.update(operators=[{"basis": "annual_count"}]),
        lambda cohort: cohort.update(operators=[{"basis": "fee_total"}]),
        lambda cohort: cohort.update(operators=[{"basis": "agency_hours"}]),
        lambda cohort: cohort.update(operators=[{"basis": "unmodeled_duration"}]),
        lambda cohort: cohort.update(operators=[{"basis": ["whole_case_clock"]}]),
        lambda cohort: cohort.update(extra_assumption="hidden"),
    ],
)
def test_contract_requires_declared_clock_population_and_single_normalized_mixture(mutate):
    cohort = histogram_fixture()
    mutate(cohort)
    with pytest.raises(ValueError):
        cohort_histogram_observations(cohort)


def test_repeated_cohort_ids_are_intentionally_left_for_model_wide_validation():
    first = histogram_fixture()
    second = histogram_fixture()
    second["id"] = "another_local_factor"
    assert cohort_histogram_observations(first)[0]["cohort_id"] == first["cohort_id"]
    assert cohort_histogram_observations(second)[0]["cohort_id"] == first["cohort_id"]


def test_population_bin_probabilities_are_right_closed_and_include_zero():
    above_one = np.nextafter(1.0, math.inf)
    above_two = np.nextafter(2.0, math.inf)
    population = np.array([0.0, 1.0, above_one, 2.0, above_two, 100.0])
    weights = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.25])
    probabilities = population_bin_probabilities(population, [0, 1, 2, None], weights)
    np.testing.assert_allclose(probabilities, [0.15, 0.35, 0.50], atol=1e-15)
    assert probabilities.sum() == pytest.approx(1.0, abs=1e-15)


def test_population_bin_probabilities_use_uniform_grid_weights_by_default():
    probabilities = population_bin_probabilities([0, 1, 2, 3], [0, 1, 2, None])
    np.testing.assert_array_equal(probabilities, [0.5, 0.25, 0.25])


@pytest.mark.parametrize(
    "population,weights",
    [
        ([], None),
        ([0, -1], None),
        ([0, math.inf], None),
        ([False, True], None),
        ([False, 1], None),
        (["0", "1"], None),
        ([0, 1], [1.0]),
        ([0, 1], [True, False]),
        ([0, 1], [True, 0]),
        ([0, 1], ["0.5", "0.5"]),
        ([0, 1], [0.2, 0.2]),
        ([0, 1], [-0.1, 1.1]),
    ],
)
def test_population_grid_and_weights_are_explicit_and_valid(population, weights):
    with pytest.raises(ValueError):
        population_bin_probabilities(population, [0, 1, None], weights)


@pytest.mark.parametrize(
    "counts,probabilities",
    [
        ([4, 3, 3], [0.2, 0.3, 0.5]),
        ([10, 0, 0], [1.0, 0.0, 0.0]),
        ([0, 5, 5], [0.0, 0.4, 0.6]),
        ([0, 0, 0], [0.2, 0.3, 0.5]),
    ],
)
def test_exact_kernel_matches_scipy_normalized_multinomial(counts, probabilities):
    expected = multinomial.logpmf(counts, n=sum(counts), p=probabilities)
    assert histogram_log_probability(counts, probabilities) == pytest.approx(expected, abs=1e-12)


def test_positive_count_on_zero_mass_is_impossible_without_pseudocounts():
    assert histogram_log_probability([1, 0], [0.0, 1.0]) == -math.inf
    assert math.isfinite(histogram_log_probability([0, 1], [0.0, 1.0]))


@pytest.mark.parametrize(
    "counts,probabilities",
    [
        ([1, True], [0.5, 0.5]),
        ([1, None], [0.5, 0.5]),
        ([1, "*"], [0.5, 0.5]),
        ([1, 1], [0.5]),
        ([1, 1], [True, False]),
        ([1, 1], [True, 0]),
        ([1, 1], ["0.5", "0.5"]),
        ([1, 1], [0.2, 0.2]),
        ([1, 1], [-0.1, 1.1]),
        ([1, 1], [math.nan, math.nan]),
    ],
)
def test_exact_kernel_rejects_nonexact_counts_and_invalid_probability_vectors(counts, probabilities):
    with pytest.raises(ValueError):
        histogram_log_probability(counts, probabilities)
