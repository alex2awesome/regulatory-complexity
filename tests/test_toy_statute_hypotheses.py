"""Bounded mechanics checks, not synthetic-world recovery results."""
import json

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pipeline.procbench.toy_statute import hypotheses as hs, readings
from toy_statute_reference import stage_c_reference


def h(name, V=((True, False), (False, True)), probs=(.5,)):
    return hs.Hypothesis(name, np.array(V, bool), tuple(f"q{i}" for i in range(len(probs))),
                         {f"q{i}": p for i, p in enumerate(probs)}, ("A", "B"))


def run(Hs, L=None, **kw):
    if L is None:
        L = np.log(np.array([[[.8, .2], [.3, .7]], [[.6, .4], [.4, .6]]]))
    return hs.run_hypotheses(L, None, Hs, [("uniform", {})], [.1], kw.pop("kappas", (None,)), **kw)


def test_identical_hypotheses_equal_single_and_uniform_weights():
    many = run([h("a"), h("b"), h("c")], kappas=(None, 10.), return_joint=True)
    one = hs.bma(run([h("single")], kappas=(None, 10.), return_joint=True))
    average = hs.bma(many)
    assert many["classes"] == [["a", "b", "c"]]
    assert_allclose(average["posterior_H"], [1/3]*3)
    for key in ("town_sets", "town_design", "particle_weights", "particle_town_design"):
        assert_allclose(average[key], one[key], atol=1e-12)


def test_question_labels_and_order_do_not_change_canonical_or_logz():
    a = h("a", [[1, 0], [1, 1], [0, 1], [0, 0]], (.2, .7))
    b = hs.Hypothesis("b", a.V[[0, 2, 1, 3]], ("renamed2", "renamed1"),
                      {"renamed2": .7, "renamed1": .2}, a.design_ids)
    assert hs.canonical(a)[0] == hs.canonical(b)[0]
    assert_allclose(hs.canonical(a)[1], hs.canonical(b)[1], atol=1e-12)
    res = run([a, b], kappas=(None, 10.))
    assert res["classes"] == [["a", "b"]]
    assert res["runs"]["a"] is res["runs"]["b"]


def test_analytic_bayes_factor_for_unlawful_observed_design():
    L = np.array([[[0., -np.inf]]])
    res = run([h("lawful", [[1, 0], [1, 0]]), h("unlawful", [[0, 1], [0, 1]])], L, rho=0)
    out = hs.bma(res)
    assert_allclose(out["posterior_H"], [.95, .05], atol=1e-12)
    assert_allclose(res["runs"]["lawful"][0]["log_marginal_ratio"] -
                    res["runs"]["unlawful"][0]["log_marginal_ratio"], np.log(19), atol=1e-12)


def test_canonical_collapse_equals_uncollapsed_reference():
    H = h("a", [[1, 0], [1, 0], [1, 1], [0, 1]], (.3, .6))
    L = np.log(np.random.default_rng(32).uniform(.1, 1, (7, 3, 2)))
    ref = stage_c_reference(L, hs._prior(H, .05), readings.choice_logprob(H.V, "risk", .15, beta=2))
    got = hs.run_hypotheses(L, None, [H], [("risk", {"beta": 2})], [.15], [None], chunk_size=2)["runs"]["a"][0]
    assert_allclose(got["log_marginal_ratio"], ref["log_marginal_ratio"], atol=1e-12)
    assert_allclose(got["town_design"], ref["town_design"], atol=1e-12)
    # Finite-kappa equality must couple Dirichlet draws by aggregation, not compare
    # independent draws with a fictitious 1e-12 Monte Carlo tolerance.
    raw = np.random.default_rng(2).dirichlet(np.maximum(10*hs._prior(H, .05), 1e-6), size=20)
    V, inverse = np.unique(H.V, axis=0, return_inverse=True)
    combined = np.column_stack([raw[:, :-1][:, inverse == j].sum(axis=1) for j in range(len(V))]+[raw[:, -1]])
    class Fixed:
        def __init__(self, draws): self.draws = draws
        def dirichlet(self, alpha, size):
            assert size == len(self.draws)
            return self.draws
    a = stage_c_reference(L, hs._prior(H, .05), readings.choice_logprob(H.V, "uniform", .15),
                          kappa=10., n_w=20, rng=Fixed(raw))
    # Use a per-particle law to exercise the sole kernel without another collapse.
    lc = np.broadcast_to(readings.choice_logprob(V, "uniform", .15), (len(L), len(V)+1, 2))
    b = readings.stage_c(L, hs._components(H, .05, 10)[1]/10, lc,
                         kappa=10., n_w=20, rng=Fixed(combined))
    for key in ("log_marginal_ratio", "town_design", "particle_weights"):
        assert_allclose(a[key], b[key], atol=1e-12)


def test_hypothesis_shared_across_towns_not_flat_reading_pool():
    L = np.array([[[0., -np.inf], [-np.inf, 0.]]])
    res = run([h("a", [[1, 0], [1, 0]]), h("b", [[0, 1], [0, 1]])], L, rho=0)
    shared = hs.bma(res)
    flattened = readings.stage_c(L, np.array([.5, .5, 0.]), readings.choice_logprob(h("flat").V, "uniform", .1))
    assert_allclose(shared["log_marginal_ratio"], np.log(4*.95*.05), atol=1e-12)
    assert_allclose(flattened["log_marginal_ratio"], 0, atol=1e-12)


def test_risk_reading_measure_prevents_false_equivalence():
    a = h("a", [[1, 0], [1, 1]])
    p = 1-np.sqrt(.5)
    b = h("b", [[1, 0], [1, 0], [1, 0], [1, 1]], (p, p))
    assert_allclose(hs.canonical(a)[1], hs.canonical(b)[1], atol=1e-12)
    assert hs.equivalence_classes([a, b], include_risk=False) == [[0, 1]]
    assert hs.equivalence_classes([a, b]) == [[0], [1]]
    res = hs.run_hypotheses(np.log([[[.1, .9]]]), None, [a, b], [("risk", {"beta": 5})], [.1], [None])
    assert abs(res["runs"]["a"][0]["log_marginal_ratio"]-res["runs"]["b"][0]["log_marginal_ratio"]) > .01


def test_finite_kappa_floor_is_preserved():
    a = h("a", [[1, 0], [0, 1]], (0.,))
    b = h("b", [[1, 0], [1, 0], [1, 0], [0, 1]], (0., 0.))
    assert_allclose(hs.canonical(a)[1], hs.canonical(b)[1])
    assert hs.equivalence_classes([a, b], kappas=(None,), include_risk=False) == [[0, 1]]
    assert hs.equivalence_classes([a, b], include_risk=False) == [[0], [1]]


@pytest.mark.parametrize("kappa", [None, 10.])
@pytest.mark.parametrize("cm,kw", [("uniform", {}), ("risk", {"beta": 2}), ("cost", {"tau": 15})])
def test_chunking_equivalent_and_joint_marginals_match(kappa, cm, kw):
    rng = np.random.default_rng(21)
    L = np.log(rng.uniform(.1, 1, (11, 3, 2)))
    cost = rng.uniform(0, 80, L.shape)
    a = hs.run_hypotheses(L, cost, [h("a")], [(cm, kw)], [.15], [kappa], chunk_size=11, return_joint=True)
    b = hs.run_hypotheses(L, cost, [h("a")], [(cm, kw)], [.15], [kappa], chunk_size=3, return_joint=True)
    a, b = hs.bma(a), hs.bma(b)
    for key in ("log_marginal_ratio", "town_sets", "town_design", "particle_town_design"):
        assert_allclose(a[key], b[key], atol=1e-12)
    assert_allclose(a["particle_town_design"].sum(axis=0), a["town_design"], atol=1e-12)
    assert_allclose(a["particle_town_design"].sum(axis=2), np.tile(a["particle_weights"][:, None], (1, 3)), atol=1e-12)


def test_psi_posterior_is_not_uniform_and_residual_not_false():
    res = hs.run_hypotheses(np.array([[[0., -np.inf]]]), None, [h("a", [[1, 0], [1, 0]])],
                            [("uniform", {})], [.1, .9], [None], rho=.2)
    out = hs.bma(res)
    assert out["posterior_psi"][0] > out["posterior_psi"][1]
    assert_allclose(out["town_lawful_given_known"], [[1., 0.]])
    assert out["town_lawful_upper"][0, 1] > 0
    no_data = hs.prior_lawful_bma(res)
    assert_allclose(no_data["town_unknown"], .2)


def test_joint_estimands_not_product_of_marginals():
    joint = np.array([[[.5, 0]], [[0, .5]]])
    values = np.array([[[0., 100.]], [[100., 0.]]])
    summary = hs.estimand_summary(joint, values)
    assert_allclose(summary["mean"], 0)
    assert (values*np.full_like(joint, .25)).sum() == 50


def test_loader_records_invalid_reader_instead_of_silent_permissive_default(tmp_path):
    obj = {"questions": [{"id": "q", "major": True, "p_yes": .5}],
           "design_validity": {"A": {"per_question": {}}, "B": {"per_question": {}}}}
    path = tmp_path / "bad"
    path.mkdir()
    (path / "reading.json").write_text(json.dumps(obj))
    failures = []
    assert hs.load_hypotheses(tmp_path, ["A", "B"], failures=failures) == []
    assert len(failures) == 1
    with pytest.raises(ValueError, match="invalid readers"):
        hs.load_hypotheses(tmp_path, ["A", "B"])


def test_invalid_inputs_and_json_unknown():
    with pytest.raises(ValueError, match="positive finite"):
        run([h("a")], kappas=(0,))
    with pytest.raises(ValueError, match="epsilon"):
        hs.run_hypotheses(np.zeros((1, 1, 2)), None, [h("a")], [("uniform", {})], [0], [None])
    out = hs.bma(run([h("a")], rho=1))
    # stage_c's historical 1e-300 numerical floor is not a meaningful known mass.
    assert hs.jsonable(out)["town_lawful_given_known"] == [[None, None], [None, None]]


@pytest.mark.parametrize("kitchen", [False, True])
def test_fast_burden_means_equal_existing_estimands(kitchen):
    from types import SimpleNamespace
    from pipeline.procbench.toy_statute import spec, estimands
    from test_toy_statute_response_repairs import center_params, kitchen_fixture
    spec.use_design_space("full")
    try:
        if kitchen:
            spec.load_package(kitchen_fixture())
        p = center_params("T")
        fees = {item: 10.+i for i, item in enumerate(spec.FEE_STEPS.values())}
        model = SimpleNamespace(towns=["T"], param_dict=lambda x: p, fee_table=lambda t, s, rng: fees)
        cost, values = hs.conditional_burdens(model, [None])
        for di, sid in enumerate(spec.STRUCTURE_IDS):
            reference, _ = estimands.town_estimands(p, "T", sid, fees)
            if estimands.counterfactual_available():
                cf, _ = estimands.counterfactual(p, "T", reference, fees)
                reference.update(cf)
            for key, value in values.items():
                assert_allclose(value[0, 0, di], reference[key], atol=1e-10)
            assert_allclose(cost[0, 0, di], readings.burden_indices(p, "T", fees)[di], atol=1e-10)
    finally:
        spec.use_design_space("menu6")


def load_script(name):
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "runs" / "toy_statute2_20260929" / f"{name}.py"
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_runner_rejects_old_target_before_reading_evidence(tmp_path):
    runner = load_script("run_hypotheses_hs001")
    (tmp_path / "manifest.json").write_text(json.dumps({"observation_model": None}))
    with pytest.raises(ValueError, match="v2-target"):
        runner.load_fit(tmp_path, tmp_path / "must-not-read", tmp_path / "must-not-read.json")


def test_evaluator_lawful_sets_and_tied_oracle():
    evaluator = load_script("evaluate_hypotheses_hs001")
    result = run([h("reader"), h("oracle")])
    avg = hs.bma(result)
    scores = evaluator.lawful_scores(avg, np.array([[1, 0], [0, 1]]), np.array([0, 1]))
    assert np.isfinite(scores["mean_true_set_log_score"])
    assert 0 <= scores["mean_brier_given_known"] <= 1
    ids = ["a", "b", "oracle"]
    rank = evaluator.ranking([1/3]*3, {f"single:{s}": {"mean_true_set_log_score": -1.} for s in ids}, ids)
    assert rank["positive_correlation"] == "unavailable"
    assert rank["oracle_top_two"] == "fails"
