"""Independent integration checks for the bounded count-only V6 factor."""
import copy
import json
import math

import numpy as np
import pytest
from scipy.special import betainc, betaincinv, ndtr, ndtri

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.positive_repeat_counts import log_probability
from procbench_fixtures import data_fixture
from test_case_paths import path_data
from test_positive_repeat_counts import row


@pytest.mark.parametrize("fixture", [data_fixture, path_data])
@pytest.mark.parametrize("relative_rate", [1.0, 2.0, 10.0])
@pytest.mark.parametrize("r", [1e-6, 0.07, 0.4, 0.85, 0.999])
def test_v6_count_factor_matches_standalone_real_component_grid(
    fixture, relative_rate, r
):
    """The extra V6 part is exactly the real component's declared factor."""
    data = fixture()
    base = VisitHierarchy(copy.deepcopy(data), Config(population_size=16))
    declaration = row(severity_selection={
        "id": f"threshold3-rate-{relative_rate:g}",
        "threshold": 3,
        "log_tilt": math.log(relative_rate),
        "fixed_not_estimated": True,
    })
    data["programs"][0]["positive_repeat_count_observations"] = [declaration]
    model = VisitHierarchy(data, Config(population_size=16))
    family = model.programs[0]["count_only_repeat_families"][0]
    assert family["coordinate"] == base.layout.size
    z = np.zeros(model.layout.size)
    z[family["coordinate"]] = ndtri(betainc(2.0, 3.0, r))
    represented_r = float(betaincinv(2.0, 3.0, ndtr(z[family["coordinate"]])))
    assert represented_r == pytest.approx(r, abs=1e-9)
    parts = model.log_likelihood(z, [0], parts=True)
    base_parts = base.log_likelihood(z[:base.layout.size], [0], parts=True)
    key = model.programs[0]["id"] + ":positive_repeat_count:count-1"
    assert set(parts) == set(base_parts) | {key}
    assert parts[key] == pytest.approx(
        log_probability(3, represented_r, math.log(relative_rate), 3), abs=2e-12
    )
    assert model.log_likelihood(z, [0]) - base.log_likelihood(
        z[:base.layout.size], [0]
    ) == pytest.approx(parts[key], abs=2e-12)


def test_extreme_finite_target_states_produce_strict_json_conditional_report():
    data = path_data()
    data["programs"][0]["positive_repeat_count_observations"] = [row()]
    model = VisitHierarchy(data, Config(population_size=16))
    coordinate = model.programs[0]["count_only_repeat_families"][0]["coordinate"]
    states = np.random.default_rng(20260921).normal(
        scale=0.05, size=(2, 8, model.layout.size)
    )
    # These span essentially all finite ndtr/betaincinv behavior. At z>=8.3,
    # ndtr rounds to one and the K=3 target is correctly -inf, hence unsampled.
    values = np.array([-8.0, -6.0, -3.0, 0.0, 3.0, 6.0, 8.0, 8.2])
    states[0, :, coordinate] = values
    states[1, :, coordinate] = values[::-1]
    routes = np.zeros((2, 8, 1), dtype=int)
    likelihood = np.array([
        [model.log_likelihood(draw, [0]) for draw in chain] for chain in states
    ])
    assert np.isfinite(likelihood).all()
    report = model.report(states, routes, likelihood)
    count = report["positive_repeat_counts"]["J__P:paperwork_redo_or_resubmission"]
    json.dumps(count, allow_nan=False)
    for name in ("continuation_probability", "mean_additional_rounds_given_positive"):
        values = [value for value in count[name].values()
                  if isinstance(value, (int, float)) and not isinstance(value, bool)]
        assert values and np.isfinite(values).all()
    assert count["positive_event_probability"] is None
    assert count["unconditional_mean_additional_rounds"] is None
    assert count["burden_headline_eligible"] is False


def test_count_coordinate_does_not_enter_case_latents_or_burden_layout():
    data = path_data()
    base = VisitHierarchy(copy.deepcopy(data), Config(population_size=16))
    data["programs"][0]["positive_repeat_count_observations"] = [row()]
    model = VisitHierarchy(data, Config(population_size=16))
    before, after = base.programs[0], model.programs[0]
    assert after["case_dimension"] == before["case_dimension"]
    np.testing.assert_array_equal(after["case_coordinates"], before["case_coordinates"])
    assert after["noise_dimension"] == before["noise_dimension"]
    assert after["repeat_keys"] == before["repeat_keys"]
    z = np.zeros(model.layout.size)
    baseline = model.expected_burden(after, z, model.parameters(z), 0)
    z[-1] = 8.2
    assert model.expected_burden(after, z, model.parameters(z), 0) == baseline
