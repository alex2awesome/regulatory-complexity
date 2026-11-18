"""Exact-count histogram observations for one explicitly declared IID cohort.

The likelihood is a normalized multinomial over bin probabilities computed from
the hierarchy's supplied population-duration integration grid. It introduces no
individual-case latent variables. Each histogram is one likelihood factor with
one operator mixture; virtual rows returned for validation are not independent
reports. Exact counts receive no narrative-report scale, contamination, or
source-family time offset; ``source_family`` is provenance only.

``population_bin_probabilities`` is exact for the supplied discrete population
measure. Hard grid assignment is not smooth when a grid location crosses a bin
edge, however, and results remain subject to population-integration precision.
Grid refinement and downstream numerical checks are still required; this module
is not, by itself, a production fit-quality guarantee.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.special import gammaln


TIME_UNITS = {"calendar_days"}
REPORTING = "exact_event_duration_bin_counts"
BIN_CONVENTION = "right_closed"
SAMPLING = "iid_within_declared_population"
ELAPSED_BASES = {
    "whole_case_clock",
    "single_visit_cycle",
    "sum_visit_cycles",
    "first_to_last_activity_span",
    "wait_elapsed",
    "service_elapsed",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _numeric_array(values: Any, message: str) -> np.ndarray:
    objects = np.asarray(values, dtype=object)
    if any(isinstance(value, (bool, np.bool_)) for value in objects.flat):
        raise ValueError(message)
    array = np.asarray(values)
    if array.dtype.kind not in "iuf":
        raise ValueError(message)
    return array.astype(float, copy=False)


def _validate_counts(counts: Any) -> tuple[int, ...]:
    if not isinstance(counts, (list, tuple)) or not counts:
        raise ValueError("Histogram bin_counts must be a nonempty integer list")
    if any(isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0
           for value in counts):
        raise ValueError("Histogram counts must be observed nonnegative integers, not intervals")
    return tuple(int(value) for value in counts)


def _validate_edges(edges: Any) -> tuple[float | None, ...]:
    if not isinstance(edges, (list, tuple)) or len(edges) < 2:
        raise ValueError("Histogram bin_edges must contain [0, ..., null]")
    if isinstance(edges[0], bool) or not isinstance(edges[0], (int, float, np.number)):
        raise ValueError("Histogram bin_edges must start at numeric zero")
    if not math.isfinite(float(edges[0])) or float(edges[0]) != 0.0 or edges[-1] is not None:
        raise ValueError("Histogram bin_edges must be complete [0, ..., null]")
    interior: list[float] = []
    for edge in edges[1:-1]:
        if (isinstance(edge, bool) or not isinstance(edge, (int, float, np.number))
                or not math.isfinite(float(edge))):
            raise ValueError("Finite interior histogram edges must be numeric")
        interior.append(float(edge))
    if any(right <= left for left, right in zip([0.0] + interior, interior)):
        raise ValueError("Histogram bin_edges must be strictly increasing")
    return (0.0, *interior, None)


def _validate_operator_mixture(operators: Any, weights: Any) -> tuple[float, ...]:
    if (not isinstance(operators, list) or not operators
            or any(not isinstance(operator, dict) or not operator for operator in operators)):
        raise ValueError("A histogram requires one nonempty operator mixture")
    if any(not isinstance(operator.get("basis"), str)
           or operator["basis"] not in ELAPSED_BASES for operator in operators):
        raise ValueError("Histogram operators must use supported elapsed-duration bases")
    if not isinstance(weights, (list, tuple)) or len(weights) != len(operators):
        raise ValueError("Operator weights must align with the histogram operator mixture")
    if any(isinstance(value, bool) or not isinstance(value, (int, float, np.number))
           for value in weights):
        raise ValueError("Operator weights must be finite nonnegative numbers")
    numeric = np.asarray(weights, dtype=float)
    if (not np.isfinite(numeric).all() or np.any(numeric < 0)
            or not np.isclose(numeric.sum(), 1.0, atol=1e-12, rtol=0.0)):
        raise ValueError("Operator weights must be finite, nonnegative, and sum to one")
    return tuple(float(value) for value in numeric)


def cohort_histogram_observations(cohort: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate a histogram cohort and return one virtual operator-check row.

    The caller/model must enforce global uniqueness of ``cohort_id``. This local
    validator deliberately has no global state, so repeated cohort IDs can be
    detected across programs and evidence types at the model boundary.
    """
    required = {
        "id",
        "cohort_id",
        "sample_size",
        "bin_counts",
        "bin_edges",
        "reporting",
        "bin_convention",
        "sampling",
        "independent_of_other_evidence",
        "independent_of_other_cohorts",
        "same_cohort_mean_in_likelihood",
        "source_family",
        "population",
        "clock",
        "time_unit",
        "operators",
        "operator_weights",
    }
    optional = {"provenance", "population_path_scope", "population_condition"}
    if (not isinstance(cohort, dict) or not required <= cohort.keys()
            or set(cohort) - required - optional):
        raise ValueError("Histogram cohorts require an explicit clock/population/count contract")
    if any(not _nonempty_string(cohort[key])
           for key in ("id", "cohort_id", "source_family", "population")):
        raise ValueError("Histogram cohort, source, and population identities must be nonempty strings")

    clock = cohort["clock"]
    if (not isinstance(clock, dict) or set(clock) != {"start", "end"}
            or not _nonempty_string(clock["start"]) or not _nonempty_string(clock["end"])):
        raise ValueError("Histogram clock must declare nonempty start and end labels")
    if clock["start"] == clock["end"]:
        raise ValueError("Histogram clock start and end must differ")
    if not isinstance(cohort["time_unit"], str) or cohort["time_unit"] not in TIME_UNITS:
        raise ValueError("Histogram time_unit must currently be calendar_days")
    if cohort["reporting"] != REPORTING:
        raise ValueError("Histogram reporting must declare exact event-duration bin counts")
    if cohort["bin_convention"] != BIN_CONVENTION:
        raise ValueError("Histogram intervals must be right-closed")
    if (cohort["sampling"] != SAMPLING
            or cohort["independent_of_other_evidence"] is not True
            or cohort["independent_of_other_cohorts"] is not True):
        raise ValueError("Declare IID sampling and cohort/evidence independence explicitly")
    if cohort["same_cohort_mean_in_likelihood"] is not False:
        raise ValueError("A same-cohort mean cannot be a second likelihood term")

    sample_size = cohort["sample_size"]
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise ValueError("A histogram requires a positive integer observed sample size")
    counts = _validate_counts(cohort["bin_counts"])
    edges = _validate_edges(cohort["bin_edges"])
    if len(edges) != len(counts) + 1:
        raise ValueError("Histogram bin_counts must align one-for-one with complete bins")
    if sum(counts) != sample_size:
        raise ValueError("Histogram bin_counts must sum exactly to sample_size")
    operator_weights = _validate_operator_mixture(
        cohort["operators"], cohort["operator_weights"]
    )
    if "population_path_scope" in cohort:
        scope = cohort["population_path_scope"]
        if (not isinstance(scope, list) or not scope
                or any(not _nonempty_string(value) for value in scope)
                or len(set(scope)) != len(scope)):
            raise ValueError("A histogram path scope requires distinct nonempty path IDs")
    if "population_condition" in cohort:
        if (cohort["population_condition"] != "first_visit"
                or any(op["basis"] != "single_visit_cycle" or op.get("visits") != "first"
                       for op in cohort["operators"])):
            raise ValueError("First-visit histogram conditioning requires first-cycle operators")

    row = {
        "id": cohort["id"],
        "cohort_id": cohort["cohort_id"],
        "case_id": None,
        "reporting": REPORTING,
        "sample_size": sample_size,
        "bin_counts": list(counts),
        "bin_edges": list(edges),
        "bin_convention": BIN_CONVENTION,
        "sampling": SAMPLING,
        "source_family": cohort["source_family"],
        "population": cohort["population"],
        "clock": dict(clock),
        "time_unit": cohort["time_unit"],
        "operators": cohort["operators"],
        "operator_weights": list(operator_weights),
        "independent_of_other_evidence": True,
        "independent_of_other_cohorts": True,
        "same_cohort_mean_in_likelihood": False,
        "virtual_operator_check": True,
    }
    for key in optional:
        if key in cohort:
            row[key] = cohort[key]
    return [row]


def population_bin_probabilities(
    population: Any,
    bin_edges: Any,
    weights: Any = None,
) -> np.ndarray:
    """Aggregate a discrete population measure into complete right-closed bins.

    Edges ``[0, a, b, None]`` mean ``[0, a]``, ``(a, b]``, and
    ``(b, infinity)``. Thus zero and every finite boundary value are assigned
    deterministically to the lower bin.
    """
    edges = _validate_edges(bin_edges)
    raw_values = np.asarray(population)
    if raw_values.ndim != 1 or not len(raw_values):
        raise ValueError("Histogram population must be a nonempty one-dimensional duration grid")
    values = _numeric_array(population, "Histogram population durations must be numeric")
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("Histogram population durations must be finite and nonnegative")

    if weights is None:
        probabilities = np.full(len(values), 1.0 / len(values), dtype=float)
    else:
        raw_weights = np.asarray(weights)
        if raw_weights.ndim != 1 or raw_weights.shape != values.shape:
            raise ValueError("Population weights must match the duration grid")
        probabilities = _numeric_array(weights, "Population weights must be numeric")
        if (not np.isfinite(probabilities).all() or np.any(probabilities < 0)
                or not np.isclose(probabilities.sum(), 1.0, atol=1e-12, rtol=0.0)):
            raise ValueError("Population weights must be finite, nonnegative, and sum to one")
        probabilities = probabilities / probabilities.sum()  # Numerical normalization only.

    finite_upper_edges = np.asarray(edges[1:-1], dtype=float)
    assignments = np.searchsorted(finite_upper_edges, values, side="left")
    result = np.bincount(assignments, weights=probabilities, minlength=len(edges) - 1)
    result = np.asarray(result, dtype=float)
    result /= result.sum()  # Numerical normalization; never adds support to an empty bin.
    return result


def histogram_log_probability(bin_counts: Any, probabilities: Any) -> float:
    """Return the normalized multinomial log probability for exact bin counts."""
    counts = _validate_counts(bin_counts)
    raw_probs = np.asarray(probabilities)
    if raw_probs.ndim != 1 or raw_probs.shape != (len(counts),):
        raise ValueError("Histogram probabilities must align with bin_counts")
    probs = _numeric_array(probabilities, "Histogram probabilities must be numeric")
    if (not np.isfinite(probs).all() or np.any(probs < 0)
            or not np.isclose(probs.sum(), 1.0, atol=1e-12, rtol=0.0)):
        raise ValueError("Histogram probabilities must be finite, nonnegative, and sum to one")
    probs = probs / probs.sum()  # Numerical normalization only; zero support stays zero.
    count_array = np.asarray(counts, dtype=float)
    if np.any((count_array > 0) & (probs == 0)):
        return -math.inf
    positive = count_array > 0
    return float(
        gammaln(count_array.sum() + 1)
        - gammaln(count_array + 1).sum()
        + np.dot(count_array[positive], np.log(probs[positive]))
    )
