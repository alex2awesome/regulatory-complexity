"""Bounded regression/reference checks for the 2026-09-30 response audit."""
import copy
import itertools
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.special import logsumexp
from scipy.stats import binom, poisson

from pipeline.procbench.toy_statute import estimands, grid, readings, spec
from pipeline.procbench.toy_statute.model import Model, CONTAM, prior_spec
from toy_statute_reference import ReferenceModel, sum_pmfs_direct, stage_c_reference


@pytest.fixture(autouse=True)
def restore_catalog():
    spec.use_design_space("menu6")
    yield
    spec.use_design_space("menu6")


def center_params(town="A"):
    p = {}
    for name, (kind, a, b) in prior_spec([town]).items():
        p[name] = a if kind == "normal" else math.log(a / b)
    return p


def kitchen_fixture():
    """Public-only small package; no gitignored package/world dependency."""
    pkg = {"statute_id": "test-kitchen", "text": "Test food permit", "deadline_days": 30}
    for field in ("d_steps", "p_steps", "day_steps", "hour_steps", "fee_steps", "town_scaled",
                  "listable", "mentionable", "timeable_events", "mention_event", "admin_milestones", "event_order"):
        value = copy.deepcopy(getattr(spec, field.upper()))
        pkg[field] = list(value) if isinstance(value, set) else value
    for step, days, hours, item, dsteps in [
        ("food_safety_course", False, True, "course", ["D1"]),
        ("product_lab_test", True, True, "lab", ["D2"]),
        ("zoning_clearance", True, False, "zoning", ["D2"]),
    ]:
        pkg["p_steps"][step] = {"days": days, "hours": hours, "fee": item, "d_steps": dsteps,
                                 "actor": "applicant", "applicant_facing": True, "events": []}
        if days:
            pkg["day_steps"].append(step)
        if hours:
            pkg["hour_steps"].append(step)
        pkg["fee_steps"][step] = item
    pkg["design_space"] = {
        "K1": {"d2": ["desk_review"], "shared_decision": False},
        "K2": {"d2": ["desk_review", "product_lab_test", "zoning_clearance"], "shared_decision": False},
    }
    return pkg


@pytest.mark.parametrize("length", [1, 8, 32, None, 200])
def test_cached_and_reference_convolutions_match_direct_without_tail_lumping(length):
    pmfs = grid.discretized_lognormal([5, 12], [.7, .9], 32)
    counts = np.array([[0, 0], [1, 0], [0, 1], [2, 3], [3, 2]])
    cached = grid.sum_pmfs(pmfs, counts, length=length)
    reference = sum_pmfs_direct(pmfs, counts, length=length)
    assert np.allclose(cached, reference, atol=2e-15)
    for i, row in enumerate(counts):
        direct = np.array([1.0])
        for j, n in enumerate(row):
            for _ in range(n):
                direct = np.convolve(direct, pmfs[j])
        want = np.zeros(cached.shape[1])
        end = min(len(direct), len(want))
        want[:end] = direct[:end]
        np.testing.assert_allclose(cached[i], want, atol=2e-15)


def test_hours_sum_is_not_capped_before_report_noise():
    step = np.zeros((1, 512))
    step[0, 400] = 1  # 100 hours each
    total = grid.sum_pmfs(step, [[2]])[0]
    report = grid.report_lik_hours(200, .3, length=len(total))
    assert np.argmax(total) == 800
    assert total @ report == pytest.approx(report[800], abs=1e-14)
    assert abs(math.log(report[800] / report[511])) > 1


def test_uncapped_elapsed_mean_adds_up_to_steps():
    p = center_params()
    for s in spec.DAY_STEPS:
        p[f"mu_{s}"] = math.log(180)
        p[f"lsig_{s}"] = math.log(.15)
    e, total = estimands.town_estimands(p, "A", "S5", {"application": 20})
    assert e["total.days_mean"] > 511
    assert total.sum() == pytest.approx(1, abs=1e-12)
    assert e["total.days_mean"] == pytest.approx(sum(e[f"pstep_days.{s}"] for s in spec.DAY_STEPS), abs=1e-8)


def test_extended_consumers_keep_full_support():
    from pipeline.procbench.toy_statute import extended
    p = center_params()
    result = extended.ext_town(p, "A", "S5")
    assert np.isfinite(list(result.values())).all()
    assert result["ext.serialisation_excess_days"] >= 0
    assert extended.cf_invariance_band(p, "A", "S5")


def test_catalog_fees_burden_and_generator_agree_for_kitchen():
    from pipeline.procbench.toy_statute.generate import simulate_case, make_webpage
    pkg = kitchen_fixture()
    spec.load_package(pkg)
    p = center_params()
    fees = {"application": 53, "course": 20, "lab": 40, "zoning": 15}
    indices = readings.burden_indices(p, "A", fees)
    for i, s in enumerate(spec.STRUCTURE_IDS):
        e, _ = estimands.town_estimands(p, "A", s, fees)
        assert indices[i] == pytest.approx(e["total.days_mean"] + 4*e["total.hours_mean"] + e["total.dollars_mean"]/5)
    world = {"structure": {"A": "K1"}, "p_incomplete": {"A": .1}, "q_objection": {"A": .1},
             "step_days": {s: [7, .4] for s in spec.DAY_STEPS}, "town_speed": {"A": 1},
             "hours_median": {s: 2 for s in spec.HOUR_STEPS}, "hours_sigma": .5, "fees": {"A": fees},
             "obs": {"web_list": 1, "web_false": 0}, "design": {"forced_web_omissions": {}}}
    case = simulate_case(np.random.default_rng(0), world, "A")
    assert case["dollars"] == 73
    webpage = make_webpage(np.random.default_rng(0), world, "A")
    assert webpage["fee_schedule"]["course"] == 20
    model = object.__new__(Model)
    model.data = {"A": SimpleNamespace(web_fees=webpage["fee_schedule"], fee_reports=[73])}
    assert sum(model.fee_table("A", "K1").values()) == 73
    flat, _ = estimands.all_estimands(p, {"A": "K1"}, model.fee_table)
    assert set(flat) == set(estimands.estimand_keys(["A"]))
    assert not any("counterfactual" in k for k in flat)


def make_evidence(tmp_path, *, milestones=False, package=None):
    from pipeline.procbench.toy_statute.generate import generate
    from pipeline.procbench.toy_statute.truth_world import W0
    world = copy.deepcopy(W0)
    for key in ("structure", "p_incomplete", "q_objection", "town_speed", "fees"):
        world[key]["Amber"] = copy.deepcopy(world[key][world["towns"][0]])
    world["towns"] = ["Amber"]
    world["design"].update(admin_towns=["Amber"], admin_n=3, reports_per_town=16, heldout_n=1,
                           admin_milestones=milestones)
    if package:
        path = tmp_path / "package.json"
        path.write_text(json.dumps(package))
        world["package_path"] = str(path)
        world["structure"]["Amber"] = "K1"
        for s in package["day_steps"]:
            world["step_days"].setdefault(s, [7, .4])
        for s in package["hour_steps"]:
            world["hours_median"].setdefault(s, 2)
        world["fees"]["Amber"]["course"] = 20
    generate(tmp_path / "world", world)
    return tmp_path / "world" / "evidence"


@pytest.mark.parametrize("milestones", [False, True])
def test_full_likelihood_optimized_equals_reference(tmp_path, milestones):
    ev = make_evidence(tmp_path, milestones=milestones)
    fast = Model(ev)
    ref = ReferenceModel(ev)
    for seed in (1, 4, 5):
        x = fast.sample_prior_theta(np.random.default_rng(seed))
        a, b = fast.loglik(x), ref.loglik(x)
        assert np.isfinite(a) and np.isfinite(b)
        assert a == pytest.approx(b, abs=1e-8)


def test_kitchen_real_answer_path_one_draw(tmp_path):
    from pipeline.procbench.toy_statute.fit import answers_from_draws
    package = kitchen_fixture()
    ev = make_evidence(tmp_path, package=package)
    model = Model(ev, package_path=tmp_path / "package.json")
    x = model.sample_prior_theta(np.random.default_rng(4))
    answer = answers_from_draws(model, x[None], 5, n_draws=1)
    assert set(answer["estimands"]) == set(estimands.estimand_keys(model.towns))
    assert answer["model_metadata"]["counterfactual_status"].startswith("unavailable")
    assert answer["model_metadata"]["assumed_legacy_reporting_keys"] == []


def test_incompatible_timed_events_are_structural_zeros(tmp_path):
    model = Model(make_evidence(tmp_path))
    d = model.data["Amber"]
    x = model.sample_prior_theta(np.random.default_rng(2))
    p = model.param_dict(x)
    seg = grid.sum_pmfs(model.step_pmfs(p, "Amber"), d.seg_counts, length=model.Lc)
    # A timed boundary that is absent from candidate 0 cannot be rescued by
    # numeric contamination, even if the other observed gaps are feasible.
    d.gap_seg[0, 0] = -1
    result = model._completed_gap_loglik(seg, d, math.exp(p["lsig_r"]), CONTAM)
    assert np.isneginf(result[0, d.rep_of_gap[0]])


def test_timing_mask_normalizes_over_all_subsets():
    model = object.__new__(Model)
    model.reporting = {"p_total_only": .2, "p_time_mentioned_event": .7}
    for available in range(5):
        count = np.array([sum(s) for s in itertools.product([0, 1], repeat=available)])
        d = SimpleNamespace(timing_available=np.full((1, len(count)), available), timing_observed=count,
                            timing_compatible=np.ones((1, len(count)), bool))
        mass = np.exp(model.timing_mask_loglik(d))
        assert mass.sum() == pytest.approx(1)
        assert mass[0, 0] == pytest.approx(.2 + .8 * .3**available)


def test_exact_milestone_labels_cannot_be_contaminated(tmp_path):
    model = Model(make_evidence(tmp_path, milestones=True))
    d = model.data["Amber"]
    mask = d.combo_struct == 0
    d.agap_seg[mask, 0] = -1
    x = model.sample_prior_theta(np.random.default_rng(4))
    assert np.isneginf(model.town_struct_loglik(x, "Amber")[0])


def test_mapped_and_hen_scorers_share_unknown_and_exclusion_semantics():
    qids = list(readings.QUESTIONS)
    truth = {"A": {q: True for q in qids}}
    p = np.zeros(2**len(qids) + 1)
    p[0], p[1], p[-1] = .1, .4, .5  # same kept reading, opposite last question
    design = np.ones((1, len(spec.STRUCTURE_IDS))) / len(spec.STRUCTURE_IDS)
    a = readings.score_readings([p], truth, {"A": "S1"}, design, ["A"], exclude=[qids[-1]])
    b = readings.score_mapped([p], qids, truth, {q: q for q in qids}, ["A"], {"A": "S1"}, design, exclude=[qids[-1]])
    assert a == b
    assert a["mean_log_score"] == pytest.approx(0)
    assert a["map_accuracy"] == 1 and a["full_known_map_accuracy"] == 0
    assert a["mean_unconditional_log_score"] == pytest.approx(math.log(.5))
    empty = readings.score_mapped([[0, 0, 1]], ["Q"], {"A": {"Q": True}}, {"Q": "Q"}, ["A"])
    assert empty["mean_log_score"] is None and empty["question_brier"]["Q"] is None
    assert empty["unscorable_known_towns"] == ["A"]


def test_reading_class_collapse_reconstructs_same_independent_target():
    rng = np.random.default_rng(8)
    L = rng.normal(size=(4, 3, 6))
    lc = np.log(np.array([[.1, .2, .3, .1, .1, .2], [.2, .1, .2, .1, .2, .2]]))
    lc = lc[[0, 0, 1, 0, 1]]
    prior = np.array([.1, .1, .2, .3, .3])
    a = stage_c_reference(L, prior, lc)
    b = readings.stage_c(L, prior, lc)
    for k in a:
        np.testing.assert_allclose(a[k], b[k], atol=1e-13)
    assert b["reading_classes"] == 2
    # With shared Dirichlet weights, data cannot learn allocations WITHIN a class.
    c = readings.stage_c(L, prior, lc, kappa=10, n_w=500, rng=np.random.default_rng(9))
    np.testing.assert_allclose(c["town_reading"][:, 3], 3*c["town_reading"][:, 0])
    assert c["population_weights"].sum() == pytest.approx(1)


@pytest.mark.parametrize("lam", [0., 3., 20.])
def test_conditional_survey_matches_brute_force(lam):
    from pipeline.procbench.toy_statute import outcomes as O
    w = np.array([.1, .2, .3, .4])
    phi = .7
    for S, n, H, K in [(5, 40, 80, 4), (25, 40, 80, 4), (0, 8, 80, 0)]:
        terms = []
        for rest, weight in enumerate(w):
            for q in range(rest + 1):
                for r in range(H-K-q+1):
                    terms.append(math.log(weight) + binom.logpmf(q, rest, phi) + poisson.logpmf(r, lam)
                                 + binom.logpmf(S, n, (K+q+r)/H))
        want = logsumexp(terms)
        got = O.conditional_survey_loglik(S, n, H, K, w[None], [phi], [lam])[0]
        assert got == pytest.approx(want, abs=1e-9)


def test_survey_retains_denied_binomial_not_poisson_variance():
    from pipeline.procbench.toy_statute import outcomes as O
    w = np.zeros((1, 101)); w[0, 100] = 1
    for S in (60, 90, 120):
        want = logsumexp(binom.logpmf(np.arange(101), 100, .9)
                         + binom.logpmf(S, 1000, np.arange(101)/1000))
        got = O.conditional_survey_loglik(S, 1000, 1000, 0, w, [.9], [0])[0]
        assert got == pytest.approx(want, abs=1e-10)


def test_joint_denial_rest_distribution_preserves_moments():
    from pipeline.procbench.toy_statute import outcomes as O
    args = [np.array([v]) for v in [1.5, .7, 4., 2., 1.]]
    lp, ea, eb, w = O._joint_denied_unpermitted(6, 3, 2, *args, return_rest=True)
    assert w.sum() == pytest.approx(1)
    assert (w @ np.arange(7)).item() == pytest.approx((6-ea-eb).item())


def test_old_target_particles_cannot_silently_enter_new_stage_c(tmp_path):
    model = Model(make_evidence(tmp_path))
    with pytest.raises(ValueError, match="refit"):
        model.require_fit_target({"args": {}})
    model.require_fit_target({"observation_model": model.observation_metadata})


def test_new_generator_will_not_replace_old_world_and_baseline_sees_settings(tmp_path):
    from pipeline.procbench.toy_statute.generate import generate
    from pipeline.procbench.toy_statute.llm_baseline import build_prompt
    ev = make_evidence(tmp_path)
    with pytest.raises(FileExistsError, match="new versioned"):
        generate(ev.parent)
    prompt = build_prompt(ev)
    assert '"p_total_only": 0.2' in prompt and '"p_time_mentioned_event": 0.7' in prompt
    assert "summed totals are NOT capped" in prompt


def test_smc_writes_provenance_and_smoke_check_before_sampling(tmp_path, monkeypatch):
    from pipeline.procbench.toy_statute import smc
    ev = make_evidence(tmp_path)
    out = tmp_path / "fit"
    monkeypatch.setattr("sys.argv", ["smc", "--evidence", str(ev), "--out", str(out)])

    class StopBeforeSampling(Exception):
        pass

    def stop(*args, **kwargs):
        launch = json.loads((out / "launch_manifest.json").read_text())
        preflight = json.loads((out / "preflight.json").read_text())
        from pipeline.procbench.toy_statute.model import TARGET_VERSION
        assert launch["observation_model"]["target_version"] == TARGET_VERSION
        assert (out / "source_snapshot" / "model.py").exists()
        assert preflight["status"] == "passed"
        raise StopBeforeSampling

    monkeypatch.setattr(smc, "run_smc", stop)
    with pytest.raises(StopBeforeSampling):
        smc.main()


def test_fit_command_delegates_to_the_only_process_sampler(monkeypatch):
    from pipeline.procbench.toy_statute import fit, smc
    seen = []
    monkeypatch.setattr(smc, "main", lambda argv: seen.append(argv) or "delegated")
    args = ["--evidence", "example", "--out", "example-fit", "--particles", "100"]
    assert fit.main(args) == "delegated"
    assert seen == [args]
    assert not hasattr(fit, "find_map") and not hasattr(fit, "_chain_worker")


def test_production_has_no_reference_or_legacy_switches():
    import ast
    import inspect
    from pathlib import Path
    from pipeline.procbench.toy_statute import outcomes
    assert "backend" not in inspect.signature(grid.sum_pmfs).parameters
    assert "convolution_backend" not in inspect.signature(Model).parameters
    assert "completed_backend" not in inspect.signature(Model).parameters
    assert "collapse_readings" not in inspect.signature(readings.stage_c).parameters
    assert not hasattr(grid, "conv_from_counts") and not hasattr(grid, "log_fft")
    assert not hasattr(outcomes, "survey_loglik") and not hasattr(outcomes, "survey_loglik_exact")
    for path in Path(grid.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert "toy_statute_reference" not in (node.module or "")
            elif isinstance(node, ast.Import):
                assert all("toy_statute_reference" not in a.name for a in node.names)
