"""Independent source-free checks for the conditional step-burden reporter."""
from __future__ import annotations

import copy
import math

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.process_structure.step_burden import conditional_step_burden
from procbench_fixtures import data_fixture
from test_case_paths import cfg as path_cfg, path_data
from test_inter_operation_dwell import dwell_fixture
from test_multiple_step_repeat_blocks import configured_model_and_state, two_repeat_program


def _call(model, z, route_index=0):
    program = model.programs[0]
    return conditional_step_burden(
        model, program, z, model.parameters(z), route_index
    )


def test_two_repeat_blocks_reconcile_exact_counts_fees_labor_and_expected_burden():
    model, program, z, desired = configured_model_and_state()
    got = _call(model, z)
    aggregate = model.expected_burden(program, z, model.parameters(z), 0)

    alpha = 1.0 + desired["alpha_rework"][0] / (1.0 - desired["alpha_rework"][1])
    beta = 1.0 + desired["beta_rework"][0] / (1.0 - desired["beta_rework"][1])
    assert got["steps"]["alpha"]["expected_visits"] == pytest.approx(alpha)
    assert got["steps"]["beta"]["expected_visits"] == pytest.approx(beta)
    assert got["steps"]["decision"]["expected_visits"] == 1.0
    assert got["steps"]["alpha"]["fee_total"] == pytest.approx(10.0 * alpha)
    assert got["steps"]["beta"]["fee_total"] == pytest.approx(20.0 * beta)
    assert got["steps"]["decision"]["fee_total"] == 30.0

    assert got["totals"]["participation_probability"] == pytest.approx(
        aggregate["mean_operation_count"]
    )
    assert got["totals"]["expected_visits"] == pytest.approx(
        aggregate["mean_visit_count"]
    )
    assert got["totals"]["fee_total"] == pytest.approx(
        aggregate["mean_fee_total"]
    )
    assert got["totals"]["payer_hours"] == pytest.approx(
        aggregate["mean_payer_hours"]
    )
    assert got["totals"]["agency_hours"] == pytest.approx(
        aggregate["mean_agency_hours"]
    )


def test_path_participation_is_not_inventory_availability_and_reconciles_aggregate():
    model = VisitHierarchy(path_data(), path_cfg())
    z = np.zeros(model.layout.size)
    program = model.programs[0]
    got = _call(model, z)
    aggregate = model.expected_burden(program, z, model.parameters(z), 0)

    assert got["steps"]["file"]["inventory_available"] is True
    assert got["steps"]["review"]["inventory_available"] is True
    assert got["steps"]["approve"]["inventory_available"] is True
    assert got["steps"]["deny"]["inventory_available"] is True
    assert got["steps"]["file"]["participation_probability"] == pytest.approx(1.0)
    assert got["steps"]["review"]["participation_probability"] == pytest.approx(0.75)
    assert got["steps"]["approve"]["participation_probability"] == pytest.approx(0.75)
    assert got["steps"]["deny"]["participation_probability"] == pytest.approx(0.25)
    assert got["totals"]["participation_probability"] == pytest.approx(
        aggregate["mean_operation_count"]
    )
    assert got["totals"]["expected_visits"] == pytest.approx(
        aggregate["mean_visit_count"]
    )


def test_operation_outside_selected_inventory_is_available_false_not_unknown_burden():
    data = {
        "programs": [{
            "id": "two_inventories",
            "routes": [
                {
                    "id": "selected",
                    "prior_weight": 1.0,
                    "operations": [{
                        "id": "selected_step", "actor_id": "payer",
                        "actor_role": "payer", "task_type": "filing",
                        "payer_work": False, "agency_work": False, "fee": 0.0,
                    }],
                    "blocks": [{"id": "selected_block", "operations": ["selected_step"]}],
                },
                {
                    "id": "other",
                    "prior_weight": 1.0,
                    "operations": [{
                        "id": "other_step", "actor_id": "agency",
                        "actor_role": "agency", "task_type": "review",
                        "payer_work": None, "agency_work": None, "fee": None,
                    }],
                    "blocks": [{"id": "other_block", "operations": ["other_step"]}],
                },
            ],
            "observations": [],
            "rate_observations": [],
        }]
    }
    model = VisitHierarchy(data, Config(population_size=16, modeled_channels=("elapsed",)))
    got = _call(model, np.zeros(model.layout.size), route_index=0)
    absent = got["steps"]["other_step"]
    assert absent["inventory_available"] is False
    assert absent["participation_probability"] == 0.0
    assert absent["expected_visits"] == 0.0
    assert absent["fee_total"] == 0.0
    assert absent["payer_hours"] == 0.0
    assert absent["agency_hours"] == 0.0
    assert absent["expected_visits_given_participation"] is None


def test_unknown_fee_differs_from_zero_and_disabled_labor_is_not_zeroed():
    data = data_fixture()
    program = data["programs"][0]
    program["observations"] = []
    for operation, fee in zip(program["routes"][0]["operations"], (0.0, None, 5.0)):
        operation["fee"] = fee
    model = VisitHierarchy(data, Config(population_size=16, modeled_channels=("elapsed",)))
    z = np.zeros(model.layout.size)
    got = _call(model, z)

    assert got["steps"]["file"]["fee_total"] == 0.0
    assert got["steps"]["review"]["fee_total"] is None
    assert got["steps"]["decide"]["fee_total"] == 5.0
    assert got["totals"]["fee_total"] is None
    # Explicit false applicability is zero. True applicability on an inactive
    # channel is unmeasured/unknown, not zero.
    assert got["steps"]["file"]["agency_hours"] == 0.0
    assert got["steps"]["file"]["payer_hours"] is None
    assert got["steps"]["review"]["payer_hours"] == 0.0
    assert got["steps"]["review"]["agency_hours"] is None

    known = copy.deepcopy(data)
    known["programs"][0]["routes"][0]["operations"][1]["fee"] = 0.0
    known_model = VisitHierarchy(
        known, Config(population_size=16, modeled_channels=("elapsed",))
    )
    known_z = np.zeros(known_model.layout.size)
    known_got = _call(known_model, known_z)
    known_aggregate = known_model.expected_burden(
        known_model.programs[0], known_z, known_model.parameters(known_z), 0
    )
    assert known_got["totals"]["fee_total"] == pytest.approx(
        known_aggregate["mean_fee_total"]
    )


def test_phase_wait_and_service_partition_elapsed_but_never_become_labor():
    config = Config(
        population_size=16,
        elapsed_prior_median=3.0,
        location_sd=1.0,
        agency_sd=0.0,
        task_sd=0.0,
        operation_sd=1.0,
        common_case_sd=0.0,
        source_sd=0.0,
        selection_sd=0.0,
        contamination=0.0,
        within_visit_phases=True,
        phase_case_sd=0.7,
    )
    model = VisitHierarchy(
        {"elapsed_time_unit": "calendar_days", "programs": [two_repeat_program()]},
        config,
    )
    z = np.zeros(model.layout.size)
    # Make the phase allocation non-symmetric and the work channels visibly
    # distinct from elapsed waiting/service.
    z[model.phase_coordinates] = np.linspace(-1.0, 1.0, len(model.phase_coordinates))
    got = _call(model, z)
    for row in got["steps"].values():
        assert row["waiting_elapsed"] + row["service_elapsed"] == pytest.approx(
            row["elapsed_exposure"]
        )
    assert got["totals"]["waiting_elapsed"] + got["totals"]["service_elapsed"] \
        == pytest.approx(got["totals"]["elapsed_exposure"])
    assert got["steps"]["beta"]["waiting_elapsed"] != pytest.approx(
        got["steps"]["beta"]["agency_hours"]
    )
    assert got["steps"]["alpha"]["service_elapsed"] != pytest.approx(
        got["steps"]["alpha"]["payer_hours"]
    )


def test_declared_dwell_repeats_with_its_operation_and_reconciles_additive_clock():
    model = VisitHierarchy(
        dwell_fixture(),
        Config(population_size=16, inter_operation_dwell=True),
    )
    z = np.zeros(model.layout.size)
    program = model.programs[0]
    parameters = model.parameters(z)
    got = _call(model, z)
    aggregate = model.expected_burden(program, z, parameters, 0)
    q, r = model.repeat_parameters(program, z)
    repeated = 1.0 + q[0] / (1.0 - r[0])
    review_site = model.dwell_index[(program["id"], "review")]
    decide_site = model.dwell_index[(program["id"], "decide")]
    review_wait = math.exp(
        parameters["dwell_log"][review_site] + 0.5 * model.cfg.dwell_case_sd**2
    )
    decide_wait = math.exp(
        parameters["dwell_log"][decide_site] + 0.5 * model.cfg.dwell_case_sd**2
    )
    assert got["steps"]["review"]["dwell_before"] == pytest.approx(
        repeated * review_wait
    )
    assert got["steps"]["decide"]["dwell_before"] == pytest.approx(decide_wait)
    assert got["steps"]["file"]["dwell_before"] == 0.0
    assert got["totals"]["modeled_end_clock_contribution"] == pytest.approx(
        got["totals"]["elapsed_exposure"] + got["totals"]["dwell_before"]
    )
    assert got["totals"]["expected_visits"] == pytest.approx(
        aggregate["mean_visit_count"]
    )
    assert got["totals"]["payer_hours"] == pytest.approx(
        aggregate["mean_payer_hours"]
    )
    assert got["totals"]["agency_hours"] == pytest.approx(
        aggregate["mean_agency_hours"]
    )


def _dag_model(edges):
    data = data_fixture()
    program = data["programs"][0]
    program["observations"] = []
    program["routes"][0]["blocks"] = [{
        "id": "dag",
        "operations": ["file", "review", "decide"],
        "edges": edges,
    }]
    return VisitHierarchy(data, Config(population_size=16))


def test_serial_dag_allows_additive_clock_but_parallel_dag_refuses_attribution():
    serial = _dag_model([["file", "review"], ["review", "decide"]])
    serial_got = _call(serial, np.zeros(serial.layout.size))
    assert serial_got["clock_attribution"] == "serial_modeled_work_end"
    assert serial_got["totals"]["modeled_end_clock_contribution"] == pytest.approx(
        serial_got["totals"]["elapsed_exposure"]
    )

    parallel = _dag_model([["file", "decide"], ["review", "decide"]])
    parallel_got = _call(parallel, np.zeros(parallel.layout.size))
    assert parallel_got["clock_attribution"] == "not_additive"
    assert parallel_got["totals"]["modeled_end_clock_contribution"] is None
    assert all(
        row["modeled_end_clock_contribution"] is None
        for row in parallel_got["steps"].values()
    )
    assert parallel_got["totals"]["elapsed_exposure"] > 0.0


def test_explicit_block_predecessor_dag_controls_clock_attribution():
    serial_data = data_fixture()
    serial_program = serial_data["programs"][0]
    serial_program["observations"] = []
    serial_program["routes"][0]["blocks"][0]["predecessors"] = []
    serial_program["routes"][0]["blocks"][1]["predecessors"] = ["loop"]
    serial = VisitHierarchy(serial_data, Config(population_size=16))
    serial_got = _call(serial, np.zeros(serial.layout.size))
    assert serial_got["clock_attribution"] == "serial_modeled_work_end"

    parallel_data = data_fixture()
    parallel_program = parallel_data["programs"][0]
    parallel_program["observations"] = []
    parallel_program["routes"][0]["blocks"][0]["predecessors"] = []
    parallel_program["routes"][0]["blocks"][1]["predecessors"] = []
    parallel = VisitHierarchy(parallel_data, Config(population_size=16))
    parallel_got = _call(parallel, np.zeros(parallel.layout.size))
    assert parallel_got["clock_attribution"] == "not_additive"
    assert parallel_got["totals"]["modeled_end_clock_contribution"] is None


def test_shares_are_linked_draw_ratios_not_combinations_of_marginal_summaries():
    model = VisitHierarchy(path_data(), path_cfg(case_path_logit_sd=1.0))
    route = model.programs[0]["routes"][0]
    states = []
    for path_shift, approve_shift, deny_shift in ((2.0, 1.5, -1.0), (-2.0, -1.0, 1.5)):
        z = np.zeros(model.layout.size)
        z[route["path_coordinates"]] = path_shift
        approve_index = next(
            index for index, operation in enumerate(model.operations)
            if operation["op"].id == "approve"
        )
        deny_index = next(
            index for index, operation in enumerate(model.operations)
            if operation["op"].id == "deny"
        )
        z[model.operation[0, approve_index]] = approve_shift
        z[model.operation[0, deny_index]] = deny_shift
        states.append(_call(model, z))

    for got in states:
        shares = [
            row["shares_of_population_mean"]["elapsed_exposure"]
            for row in got["steps"].values()
        ]
        assert sum(shares) == pytest.approx(1.0)
        assert got["steps"]["approve"]["shares_of_population_mean"]["elapsed_exposure"] \
            == pytest.approx(
                got["steps"]["approve"]["elapsed_exposure"]
                / got["totals"]["elapsed_exposure"]
            )

    linked_mean_share = np.mean([
        got["steps"]["approve"]["shares_of_population_mean"]["elapsed_exposure"]
        for got in states
    ])
    ratio_of_separately_averaged_outputs = (
        np.mean([got["steps"]["approve"]["elapsed_exposure"] for got in states])
        / np.mean([got["totals"]["elapsed_exposure"] for got in states])
    )
    assert abs(linked_mean_share - ratio_of_separately_averaged_outputs) > 1e-3
    assert all(
        got["share_estimand"] == "ratio_of_population_means_not_mean_of_casewise_ratios"
        for got in states
    )
