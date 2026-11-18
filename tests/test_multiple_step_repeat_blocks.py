"""Source-free regression for two independent serial repeat blocks in V6."""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.special import betainc, ndtri, xlog1py, xlogy

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compact_visit_trace import Block, CompactTrace, Operation


def observation(ident, case, basis, lower, upper, *, repeat_key=None):
    operator = {"basis": basis}
    if repeat_key is not None:
        operator["repeat_key"] = repeat_key
    if basis == "whole_case_clock":
        operator.update(start="process_start", end="initial_decision")
    return {
        "id": ident,
        "case_id": case,
        "source_family": "source_free_fixture",
        "sampling": "unselected",
        "statistic": "individual",
        "lower": lower,
        "upper": upper,
        "operators": [operator],
        "operator_weights": [1.0],
    }


def two_repeat_program():
    observations = []
    for case, alpha, beta, visits, elapsed, fee in (
            ("c0", 2, 1, 6, 17, 100),
            ("c1", 0, 1, 4, 13, 80)):
        observations.extend([
            observation(f"{case}_alpha", case, "additional_rounds", alpha, alpha,
                        repeat_key="alpha_rework"),
            observation(f"{case}_beta", case, "additional_rounds", beta, beta,
                        repeat_key="beta_rework"),
            observation(f"{case}_visits", case, "visit_count", visits, visits),
            observation(f"{case}_elapsed", case, "whole_case_clock",
                        elapsed - 0.5, elapsed + 0.5),
            observation(f"{case}_fees", case, "payer_fee_total", fee - 0.5, fee + 0.5),
        ])
    return {
        "id": "two_repeat_steps",
        "routes": [{
            "id": "serial",
            "prior_weight": 1.0,
            "operations": [
                {"id": "alpha", "actor_id": "applicant", "actor_role": "payer",
                 "task_type": "submission", "markers": ["submission"],
                 "payer_work": True, "agency_work": False, "fee": 10.0},
                {"id": "beta", "actor_id": "agency", "actor_role": "agency",
                 "task_type": "review", "payer_work": False,
                 "agency_work": True, "fee": 20.0},
                {"id": "decision", "actor_id": "agency", "actor_role": "agency",
                 "task_type": "decision", "markers": ["decision"],
                 "payer_work": False, "agency_work": True, "fee": 30.0},
            ],
            "blocks": [
                {"id": "alpha_block", "operations": ["alpha"],
                 "repeat_key": "alpha_rework"},
                {"id": "beta_block", "operations": ["beta"],
                 "repeat_key": "beta_rework"},
                {"id": "decision_block", "operations": ["decision"]},
            ],
        }],
        "observations": observations,
        "rate_observations": [
            {"repeat_key": "alpha_rework", "event": "any_correction_per_case",
             "successes": 3, "trials": 10,
             "cohort_scope": "completed_cases_for_repeat_block",
             "independent_cohort": True},
            {"repeat_key": "beta_rework", "event": "any_correction_per_case",
             "successes": 7, "trials": 10,
             "cohort_scope": "completed_cases_for_repeat_block",
             "independent_cohort": True},
        ],
    }


def configured_model_and_state():
    cfg = Config(population_size=16, elapsed_prior_median=3.0,
                 location_sd=1.0, agency_sd=0.0,
                 task_sd=0.0, operation_sd=1.0, common_case_sd=0.0,
                 source_sd=0.0, selection_sd=0.0, contamination=0.0)
    model = VisitHierarchy({"elapsed_time_unit": "calendar_days",
                            "programs": [two_repeat_program()]}, cfg)
    p = model.programs[0]
    assert p["repeat_keys"] == ["alpha_rework", "beta_rework"]
    assert p["repeat"].shape == (2, 2)
    z = np.zeros(model.layout.size)
    # Exact per-visit durations 2, 3, and 5 days with zero case noises.
    for operation, duration in zip(range(3), (2.0, 3.0, 5.0)):
        z[model.operation[0, operation]] = math.log(duration / 3.0)
    desired = {
        "alpha_rework": (0.6, 0.2),
        "beta_rework": (0.4, 0.7),
    }
    for key, (probability_any, probability_continue) in desired.items():
        j = p["repeat_keys"].index(key)
        z[p["repeat"][0, j]] = ndtri(probability_any)
        z[p["repeat"][1, j]] = ndtri(betainc(2.0, 3.0, probability_continue))
    # Independent case uniforms yield alpha rounds [2,0], beta rounds [1,1].
    uniforms = {"c0": (0.90, 0.65), "c1": (0.20, 0.65)}
    for case, values in uniforms.items():
        row = p["case_coordinates"][p["case_index"][case]]
        for j, value in enumerate(values):
            z[row[p["noise_dimension"] + j]] = ndtri(value)
    return model, p, z, desired


def test_two_repeat_blocks_have_independent_hurdle_geometric_parameters():
    model, p, z, desired = configured_model_and_state()
    q, r = model.repeat_parameters(p, z)
    for key, expected in desired.items():
        j = p["repeat_keys"].index(key)
        assert q[j] == pytest.approx(expected[0])
        assert r[j] == pytest.approx(expected[1])
    parts = model.log_likelihood(z, [0], parts=True)
    assert parts["two_repeat_steps:cohort:0"] == pytest.approx(
        xlogy(3, 0.6) + xlog1py(7, -0.6))
    assert parts["two_repeat_steps:cohort:1"] == pytest.approx(
        xlogy(7, 0.4) + xlog1py(3, -0.4))
    changed = z.copy()
    alpha = p["repeat_keys"].index("alpha_rework")
    changed[p["repeat"][0, alpha]] = ndtri(0.8)
    changed[p["repeat"][1, alpha]] = ndtri(betainc(2.0, 3.0, 0.5))
    moved = model.log_likelihood(changed, [0], parts=True)
    assert moved["two_repeat_steps:cohort:0"] != parts["two_repeat_steps:cohort:0"]
    assert moved["two_repeat_steps:cohort:1"] == parts["two_repeat_steps:cohort:1"]
    assert moved["two_repeat_steps:c0_beta"] == parts["two_repeat_steps:c0_beta"]
    assert moved["two_repeat_steps:c1_beta"] == parts["two_repeat_steps:c1_beta"]


def test_two_serial_repeat_blocks_propagate_counts_durations_and_fees():
    model, p, z, _ = configured_model_and_state()
    trace = model.trace(p, z, model.parameters(z), 0)
    np.testing.assert_array_equal(trace.rounds["alpha_rework"], [2, 0])
    np.testing.assert_array_equal(trace.rounds["beta_rework"], [1, 1])
    np.testing.assert_array_equal(trace.values({"basis": "additional_rounds",
                                                "repeat_key": "alpha_rework"}), [2, 0])
    np.testing.assert_array_equal(trace.values({"basis": "additional_rounds",
                                                "repeat_key": "beta_rework"}), [1, 1])
    np.testing.assert_array_equal(trace.values({"basis": "visit_count"}), [6, 4])
    np.testing.assert_array_equal(trace.values({"basis": "operation_count"}), [3, 3])
    np.testing.assert_allclose(trace.event("initial_decision"), [17, 13], atol=1e-12)
    np.testing.assert_allclose(trace.values({"basis": "payer_fee_total"}), [100, 80], atol=1e-12)
    assert [visit.activity_id for visit in trace.materialize(0).visits] == [
        "alpha", "alpha", "alpha", "beta", "beta", "decision"]


def test_expected_burden_adds_each_blocks_multiplicity_and_fee_variance():
    model, p, z, desired = configured_model_and_state()
    result = model.expected_burden(p, z, model.parameters(z), 0)
    q_alpha, r_alpha = desired["alpha_rework"]
    q_beta, r_beta = desired["beta_rework"]
    mean_alpha = q_alpha / (1 - r_alpha)
    mean_beta = q_beta / (1 - r_beta)
    assert result["mean_visit_count"] == pytest.approx(3 + mean_alpha + mean_beta)
    assert result["mean_operation_count"] == 3
    assert result["mean_fee_total"] == pytest.approx(
        60 + 10 * mean_alpha + 20 * mean_beta)
    variance_alpha = q_alpha * (1 + r_alpha - q_alpha) / (1 - r_alpha)**2
    variance_beta = q_beta * (1 + r_beta - q_beta) / (1 - r_beta)**2
    assert result["fee_total_case_sd"] == pytest.approx(
        math.sqrt(10**2 * variance_alpha + 20**2 * variance_beta))


def test_duplicate_key_is_not_two_independent_blocks_and_nested_schema_is_rejected():
    operations = [Operation("a", "agency", "agency", "a", fee=1),
                  Operation("b", "agency", "agency", "b", fee=1)]
    with pytest.raises(ValueError, match="Repeat keys must be distinct"):
        CompactTrace(operations,
                     [Block("a", ("a",), repeat_key="same"),
                      Block("b", ("b",), repeat_key="same")],
                     np.ones((1, 2)), {"same": np.array([1])})
    with pytest.raises(TypeError):
        Block(id="outer", operations=("a",), repeat_key="r",
              nested_blocks=(Block("inner", ("a",)),))
