import math

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.joint_inventory_prior import (
    JointInventoryPrior,
    empirical_joint_inventory,
)
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import (
    load_source_initialization,
    preflight_report,
)


def _programs():
    return [
        dict(id="county_a", routes=[
            dict(id="a0", prior_weight=1.0),
            dict(id="a1", prior_weight=1.0),
        ]),
        dict(id="county_b", routes=[
            dict(id="b0", prior_weight=1.0),
            dict(id="b1", prior_weight=1.0),
        ]),
    ]


def _declaration(weights=(2.0, 3.0, 5.0)):
    return dict(
        schema_version="v6-joint-inventory-prior/1",
        program_ids=["county_a", "county_b"],
        feedback_policy="downstream_evidence_updates_joint_inventory",
        evidence_partition_reviewed=True,
        evidence_partition_note="Independent source-free review fixture.",
        route_semantics_reviewed=True,
        hypotheses=[
            dict(id="h00", prior_weight=weights[0], route_ids=["a0", "b0"]),
            dict(id="h01", prior_weight=weights[1], route_ids=["a0", "b1"]),
            dict(id="h10", prior_weight=weights[2], route_ids=["a1", "b0"]),
        ],
    )


def _visit_data_with_no_all_zero_support():
    programs = []
    for county in ["county_a", "county_b"]:
        routes = []
        for count in [1, 2]:
            operations = [
                dict(
                    id=f"step_{i}",
                    actor_id=county,
                    actor_role="agency",
                    task_type="review",
                    payer_work=False,
                    agency_work=True,
                )
                for i in range(count)
            ]
            routes.append(
                dict(
                    id=f"count_{count}",
                    prior_weight=1.0,
                    operations=operations,
                    blocks=[
                        dict(id=f"block_{i}", operations=[f"step_{i}"])
                        for i in range(count)
                    ],
                )
            )
        programs.append(
            dict(
                id=county,
                routes=routes,
                observations=[
                    dict(
                        id=f"observed_{county}",
                        case_id=f"case_{county}",
                        source_family="fixture",
                        sampling="unselected",
                        statistic="individual",
                        lower=1,
                        upper=2,
                        operators=[dict(basis="operation_count")],
                        operator_weights=[1.0],
                    )
                ],
            )
        )
    return dict(
        programs=programs,
        joint_inventory_prior=dict(
            schema_version="v6-joint-inventory-prior/1",
            program_ids=["county_a", "county_b"],
            feedback_policy="downstream_evidence_updates_joint_inventory",
            evidence_partition_reviewed=True,
            evidence_partition_note="Independent source-free runner fixture.",
            route_semantics_reviewed=True,
            hypotheses=[
                dict(id="small_large", prior_weight=1.0, route_ids=["count_1", "count_2"]),
                dict(id="large_small", prior_weight=1.0, route_ids=["count_2", "count_1"]),
            ],
        ),
    )


class _ProgramFactorModel:
    """A deliberately non-Cartesian exact-factorization oracle."""

    def __init__(self, factors):
        self.factors = np.asarray(factors, dtype=float)
        self.calls = []

    def log_likelihood(self, continuous_state, routes, *, _program_index=None):
        assert np.asarray(continuous_state).shape == (1,)
        if _program_index is None:
            return float(sum(self.factors[j, routes[j]] for j in range(len(routes))))
        self.calls.append((_program_index, int(routes[_program_index])))
        return float(self.factors[_program_index, routes[_program_index]])


def test_irregular_joint_support_uses_each_program_route_factor_once():
    prior = JointInventoryPrior(_declaration(), _programs())
    model = _ProgramFactorModel([[-0.4, -1.2], [-0.7, -0.1]])

    probabilities, likelihood, calls = prior.conditional(model, np.zeros(1))
    expected_likelihood = np.array([-0.4 - 0.7, -0.4 - 0.1, -1.2 - 0.7])
    expected_log_mass = expected_likelihood + np.log([0.2, 0.3, 0.5])

    np.testing.assert_allclose(likelihood, expected_likelihood, atol=0, rtol=0)
    np.testing.assert_allclose(
        probabilities,
        np.exp(expected_log_mass - logsumexp(expected_log_mass)),
        atol=1e-15,
    )
    assert calls == 4
    assert sorted(model.calls) == [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_joint_update_returns_the_selected_full_likelihood_factor():
    prior = JointInventoryPrior(_declaration(), _programs())
    model = _ProgramFactorModel([[-0.4, -1.2], [-0.7, -0.1]])
    rng = np.random.default_rng(911)

    state, selected_likelihood, calls = prior.update(model, np.zeros(1), rng)

    assert tuple(state) in prior.lookup
    assert selected_likelihood == pytest.approx(
        model.log_likelihood(np.zeros(1), state), abs=1e-15
    )
    assert calls == 4


def test_joint_conditional_fails_when_every_supported_state_is_impossible():
    prior = JointInventoryPrior(_declaration(), _programs())
    model = _ProgramFactorModel([[-math.inf, -math.inf], [-0.7, -0.1]])

    with pytest.raises(ValueError, match="No supported joint inventory"):
        prior.conditional(model, np.zeros(1))


def test_empirical_compression_preserves_full_inventory_not_cell_marginals():
    # Each cell has marginal probability 1/2, but only the two perfectly
    # anticorrelated complete inventories are supported.
    state_a = [[1, 0], [0, 1]]
    state_b = [[0, 1], [1, 0]]
    inventories = np.array([[state_a, state_b], [state_a, state_b]])

    result = empirical_joint_inventory(
        inventories, ["county_a", "county_b"], ["step_1", "step_2"]
    )

    assert len(result["joint_inventories"]) == 2
    np.testing.assert_allclose(result["probabilities"], [0.5, 0.5], atol=0, rtol=0)
    reconstructed = result["joint_inventories"][result["upstream_draw_to_inventory"]]
    np.testing.assert_array_equal(reconstructed, inventories)
    # A factorized-marginal artifact such as all-zero is not introduced.
    assert not np.any(np.all(result["joint_inventories"] == 0, axis=(1, 2)))


@pytest.mark.parametrize(
    "bad",
    [
        np.array([[[[0.5]]]]),
        np.array([[[[np.nan]]]]),
        np.empty((1, 0, 1, 1), dtype=int),
    ],
)
def test_empirical_compression_rejects_nonbinary_or_empty_draw_frames(bad):
    with pytest.raises(ValueError, match="aligned chains"):
        empirical_joint_inventory(bad, ["county_a"], ["step_1"])


def test_runner_preflight_probes_a_supported_joint_vector_not_all_zero():
    model = VisitHierarchy(
        _visit_data_with_no_all_zero_support(),
        Config(modeled_channels=("elapsed",), population_size=16),
    )

    report = preflight_report(model)

    assert report["probed_route_indices"] == [0, 1]
    assert report["joint_inventory_prior"]["hypotheses"] == 2
    assert report["joint_inventory_prior"][
        "unique_program_route_likelihoods_per_update"
    ] == 4


def test_runner_source_initialization_rejects_marginally_valid_jointly_invalid_routes(
    tmp_path,
):
    cfg = Config(
        chains=2,
        draws=8,
        warmup=0,
        modeled_channels=("elapsed",),
        population_size=16,
    )
    model = VisitHierarchy(_visit_data_with_no_all_zero_support(), cfg)
    path = tmp_path / "unsupported_joint_state.npz"
    np.savez(
        path,
        z=np.zeros((cfg.chains, model.layout.size)),
        structures=np.zeros((cfg.chains, len(model.programs)), dtype=int),
    )

    with pytest.raises(ValueError, match="outside.*joint inventory"):
        load_source_initialization(path, model, cfg.chains)


def test_joint_report_marks_unvisited_nonfixed_hypotheses_as_unverified():
    cfg = Config(
        chains=2,
        draws=8,
        warmup=0,
        modeled_channels=("elapsed",),
        population_size=16,
    )
    model = VisitHierarchy(_visit_data_with_no_all_zero_support(), cfg)
    states = np.random.default_rng(288).normal(size=(2, 8, model.layout.size))
    route = model.joint_inventory_prior.states[0]
    routes = np.broadcast_to(route, (2, 8, len(model.programs))).copy()
    likelihood = np.array(
        [model.log_likelihood(z, route) for z in states.reshape(-1, model.layout.size)]
    ).reshape(2, 8)

    report = model.report(states, routes, likelihood)

    for hypothesis in model.joint_inventory_prior.names:
        diagnostic = report["diagnostics"][f"joint_inventory:{hypothesis}"]
        assert diagnostic["ess_bulk"] == 0
        assert diagnostic["ess_tail"] == 0
        assert "No transitions" in diagnostic["reason"]
