"""Tests for the toy statute world (docs/2026-09-26-toy-statute-plan.md)."""

import ast
from pathlib import Path

import numpy as np
import pytest

from pipeline.procbench.toy_statute import grid, spec
from pipeline.procbench.toy_statute.estimands import all_estimands
from pipeline.procbench.toy_statute.generate import simulate_case
from pipeline.procbench.toy_statute.truth_eval import truth_params
from pipeline.procbench.toy_statute.truth_world import W0
from toy_statute_reference import poisson_survey_reference

PKG = Path(__file__).resolve().parents[1] / "pipeline" / "procbench" / "toy_statute"
TRUTH_BLIND = ["spec.py", "grid.py", "model.py", "estimands.py", "fit.py", "llm_baseline.py", "validity.py", "outcomes.py", "readings.py", "rsa_vagueness.py", "validity_rules.py"]


@pytest.mark.parametrize("fname", TRUTH_BLIND)
def test_fitter_and_baseline_never_import_truth(fname):
    tree = ast.parse((PKG / fname).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [a.name for a in node.names]
            assert "truth_world" not in mod and "truth_eval" not in mod, fname
            assert "truth_world" not in names and "truth_eval" not in names, fname
        if isinstance(node, ast.Import):
            for a in node.names:
                assert "truth" not in a.name, fname


def _all_day_reports():
    reps = [(r, "day") for r in range(0, 15)]
    reps += [(r, "week") for r in range(1, 12)]
    reps += [(r, "month") for r in range(1, 300)]
    return reps


@pytest.mark.parametrize("sigma", [0.1, 0.25, 0.6])
def test_day_report_likelihood_normalizes(sigma):
    total = sum(grid.report_lik_days(v, u, sigma) for v, u in _all_day_reports())
    assert np.allclose(total[:400], 1.0, atol=1e-6)


def test_hour_report_likelihood_normalizes():
    total = sum(grid.report_lik_hours(v * 0.5, 0.3) for v in range(0, 1200))
    assert np.allclose(total[:400], 1.0, atol=1e-6)


def test_day_report_generator_matches_likelihood():
    rng = np.random.default_rng(1)
    x, sigma = 23, 0.25
    counts = {}
    n = 40000
    for _ in range(n):
        k = grid.report_days(rng, x, sigma)
        counts[k] = counts.get(k, 0) + 1
    for (v, u), c in counts.items():
        if c > 400:
            assert abs(c / n - grid.report_lik_days(v, u, sigma)[x]) < 0.01


def test_discretized_lognormal_matches_sampler():
    rng = np.random.default_rng(2)
    pm = grid.discretized_lognormal([7.0], [0.6], grid.L_DAYS)[0]
    xs = np.array([grid.sample_rounded_lognormal(rng, 7.0, 0.6, grid.L_DAYS) for _ in range(40000)])
    emp = np.bincount(xs, minlength=grid.L_DAYS) / len(xs)
    assert np.abs(emp[:40] - pm[:40]).max() < 0.006


def test_full_support_convolution_is_exact():
    pm = grid.discretized_lognormal([5.0, 12.0], [0.5, 0.4], grid.L_DAYS)
    got = grid.sum_pmfs(pm, [[1, 2]])[0]
    ref = np.convolve(np.convolve(pm[0], pm[1]), pm[1])
    assert np.abs(got - ref).max() < 1e-10


def test_shared_decision_fires_at_inspection():
    seq = spec.chain("S3", 1, 0)
    pos = spec.event_positions(seq)
    assert pos["inspection"] == pos["decision"]
    assert spec.segment_counts(seq, "inspection", "decision") == tuple([0] * len(spec.DAY_STEPS))
    assert spec.segment_counts(spec.chain("S1", 0, 0), "submitted", "inspection") is None


def test_truth_estimands_match_monte_carlo():
    p = truth_params()
    flat, _ = all_estimands(p, dict(W0["structure"]), lambda t, s: W0["fees"][t])
    rng = np.random.default_rng(3)
    for t in W0["towns"]:
        cs = [simulate_case(rng, W0, t) for _ in range(3000)]
        tot = np.array([c["total_days"] for c in cs])
        hrs = np.array([c["hours"] for c in cs])
        assert abs(tot.mean() - flat[f"{t}.total.days_mean"]) < 4 * tot.std() / np.sqrt(len(tot)) + 0.05
        assert abs(hrs.mean() - flat[f"{t}.total.hours_mean"]) < 4 * hrs.std() / np.sqrt(len(hrs)) + 0.02
        assert flat[f"{t}.total.dollars_mean"] == cs[0]["dollars"]


BLOCKS = [("desk_review", "decision_issue"), ("neighbor_notice", "comment_period")]
W0_EV = Path(__file__).resolve().parents[1] / "runs" / "toy_statute_20260926" / "W0" / "evidence"


@pytest.mark.skipif(not W0_EV.exists(), reason="W0 evidence not generated")
def test_block_reparameterization_is_exact_and_volume_preserving():
    from pipeline.procbench.toy_statute.model import Model, sample_prior
    base = Model(W0_EV, center_towns=True)
    blk = Model(W0_EV, center_towns=True, blocks=BLOCKS)
    rng = np.random.default_rng(5)
    for _ in range(4):
        x = sample_prior(rng, base.base_names, base.pspec)
        y = blk.from_base(x)
        assert np.allclose(blk.to_base(y), x, atol=1e-10)
        assert abs(blk.logpost(y) - base.logpost(x)) < 1e-8
        # numeric Jacobian of to_base has |det| = 1
        h = 1e-6
        J = np.array([(blk.to_base(y + h * e) - blk.to_base(y - h * e)) / (2 * h) for e in np.eye(len(y))]).T
        assert abs(abs(np.linalg.det(J)) - 1.0) < 1e-5


# ---------------------------------------------------------------- validity (docs/process-validity.md)

def _valid(design, reading):
    from pipeline.procbench.toy_statute import validity
    return all(ok for ok, _ in validity.check(design, reading).values())


def test_validity_constraints_behave_as_declared():
    from pipeline.procbench.toy_statute import validity as V
    d = {x.id: x for x in V.all_designs()}
    for r in V.readings():
        # S1 (desk review only) is valid iff desk review suffices and no neighbour input is required.
        assert _valid(d["S1"], r) == (r["Q1_desk_sufficient"] and not r["Q2_neighbor_input_required"])
        # S4 (notice + comment + desk + hearing on objection) is valid under every reading.
        assert _valid(d["S4"], r)
        # A 30-day local comment period plus hearing notice breaks the clock iff the clock runs through D2.
        assert _valid(d["H3_30day_comment"], r) == (not r["Q4_clock_includes_d2"])
        # Issuing before the inspection, unauthorized burdens and grounds are always invalid.
        for h in ("H4_inspect_after_issue", "H2_neighbor_signatures", "H6_aesthetic_grounds"):
            assert not _valid(d[h], r)
        # Separate fees add exactly the Q5 condition.
        assert _valid(d["H8_S3_inspection_fee"], r) == (_valid(d["S3"], r) and r["Q5_separate_fees"])
    res = V.check(d["H4_inspect_after_issue"], next(V.readings()))
    assert not res["C3_precedence"][0]


def test_concurrency_never_changes_validity():
    from pipeline.procbench.toy_statute import validity as V
    d = {x.id: x for x in V.all_designs()}
    for s in ("S2", "S3", "S4", "S5", "S6"):
        for r in V.readings():
            assert _valid(d[s], r) == _valid(d[f"{s}c"], r), (s, r)


def test_edits_resolve_readings():
    from pipeline.procbench.toy_statute import validity as V
    d = {x.id: x for x in V.all_designs()}
    fixed, _ = V.EDITS["E1_safe_harbour"]
    assert V.evaluate(d["S1"], fixed=fixed)["p_valid"] == pytest.approx(1.0)
    fixed, _ = V.EDITS["E2_notice_required"]
    assert V.evaluate(d["S1"], fixed=fixed)["p_valid"] == pytest.approx(0.0)
    # P(valid) is a proper probability under the illustrative prior.
    for x in d.values():
        assert 0.0 <= V.evaluate(x)["p_valid"] <= 1.0


# ---------------------------------------------------------------- outcome layer (docs/2026-09-28-toy-statute-outcomes-plan.md)

def test_outcome_cells_partition_would_be_keepers():
    from pipeline.procbench.toy_statute import outcomes as O
    from pipeline.procbench.toy_statute.truth_world import W0o
    from pipeline.procbench.toy_statute.truth_eval import truth_outcome_params
    q = {k: np.array([v]) for k, v in truth_outcome_params(W0o).items()}
    for s in spec.STRUCTURE_IDS:
        r = O.rates(q, "Birch", s, 70.0)
        applied = r["deny"] + r["perm_n"] + r["perm_o"]
        assert np.allclose(applied, r["p_apply"])
        assert np.allclose(r["perm_n"] + r["perm_o"], r["Vp"] + r["Np"] + r["Rp"])
        assert np.allclose(r["un_n"] + r["un_o"], r["Vu"] + r["Nu"] + r["Ru"])
        assert np.allclose(r["un_n"] + r["un_o"], q["u"] * (1 - r["p_apply"] + r["deny"]))


@pytest.mark.parametrize("lamR", [3.0, 60.0, 400.0, 2500.0])
def test_conditional_survey_zero_denials_matches_exact_poisson_sum(lamR):
    from pipeline.procbench.toy_statute import outcomes as O
    for S in (10, 36, 60):
        exact = poisson_survey_reference(S, 400, 6000, 300, lamR)
        got = O.conditional_survey_loglik(S, 400, 6000, 300, [[1.0]], [0.0], [lamR])[0]
        assert abs(exact - got) < 1e-9, (S, lamR, exact, got)


def test_outcome_loglik_finite_and_prefers_truth_region():
    from pipeline.procbench.toy_statute import outcomes as O
    from pipeline.procbench.toy_statute.generate import generate_outcomes
    from pipeline.procbench.toy_statute.truth_world import W0o
    from pipeline.procbench.toy_statute.truth_eval import truth_burden
    obs, _ = generate_outcomes(W0o)
    towns = list(obs["towns"])
    names = O.param_names(towns, "shared")
    g = {"struct": dict(W0o["structure"]), "B": truth_burden(W0o)}
    o = W0o["outcomes"]
    x = {"lpi": np.log(0.15 / 0.85), "alpha": o["alpha"], "lbeta": np.log(o["beta"]),
         "lu": np.log(0.4 / 0.6), "lk1": np.log(4.0), "lk0": np.log(0.05 / 0.95)}
    for g_, sh in (("desk_review", "desk"), ("site_inspection", "insp"), ("comment_period", "nb")):
        x[f"ld_{sh}"] = np.log(o["d"][g_] / (1 - o["d"][g_]))
        x[f"lf_{sh}"] = np.log(o["f"][g_] / (1 - o["f"][g_]))
    for t in towns:
        x[f"lm_{t}"] = np.log(o["m"][t])
    X = np.array([[x[n] for n in names]])
    Xbad = X.copy()
    Xbad[0, names.index("ld_insp")] = -3.0
    ll = O.loglik(np.vstack([X, Xbad]), names, obs, g)
    assert np.all(np.isfinite(ll)) and ll[0] > ll[1]


# ---------------------------------------------------------------- reading layer (docs/2026-09-29-toy-statute-round4-plan.md)

def test_reading_prior_and_choice_models_normalize():
    from pipeline.procbench.toy_statute import readings as Rd
    spec.use_design_space("full")
    try:
        V = Rd.validity_matrix()
        assert V.shape == (32, 11) and V[:, spec.STRUCTURE_IDS.index("S4")].all()  # S4 valid under every reading
        pri = Rd.reading_prior({q: 0.5 for q in Rd.QUESTIONS}, rho=0.05)
        assert pri.shape == (33,) and abs(pri.sum() - 1) < 1e-12 and abs(pri[-1] - 0.05) < 1e-12
        cost = np.arange(11, dtype=float)
        for m in Rd.CHOICE_MODELS:
            lp = Rd.choice_logprob(V, m, eps=0.1, cost=cost)
            assert lp.shape == (33, 11)
            assert np.allclose(np.exp(lp).sum(axis=1), 1.0)
            assert np.all(np.exp(lp) >= 0.1 / 11 - 1e-12)  # slack mass everywhere
    finally:
        spec.use_design_space("menu6")


def test_stage_c_recovers_reading_from_decisive_evidence():
    from pipeline.procbench.toy_statute import readings as Rd
    spec.use_design_space("full")
    try:
        V = Rd.validity_matrix()
        D = len(spec.STRUCTURE_IDS)
        # two towns whose evidence overwhelmingly favours S1 (desk only) and S9 (notice only)
        L = np.full((50, 2, D), -50.0)
        L[:, 0, spec.STRUCTURE_IDS.index("S1")] = 0.0
        L[:, 1, spec.STRUCTURE_IDS.index("S9")] = 0.0
        prior = Rd.reading_prior({q: 0.5 for q in Rd.QUESTIONS}, rho=0.02)
        lc = Rd.choice_logprob(V, "uniform", eps=0.05)
        out = Rd.stage_c(L, prior, lc)
        R = Rd.all_readings()
        p_q1_yes_town0 = sum(out["town_reading"][0, i] for i, r in enumerate(R) if r["Q1_desk_sufficient"])
        p_q2_yes_town0 = sum(out["town_reading"][0, i] for i, r in enumerate(R) if r["Q2_neighbor_input_required"])
        assert p_q1_yes_town0 > 0.85 and p_q2_yes_town0 < 0.15   # S1 needs desk-sufficient, no neighbour input
        assert np.argmax(out["town_design"][1]) == spec.STRUCTURE_IDS.index("S9")
        assert abs(out["town_reading"].sum(axis=1) - 1).max() < 1e-9
        # hierarchical version runs and returns population weights that sum to one
        out2 = Rd.stage_c(L, prior, lc, kappa=5.0, n_w=50, rng=np.random.default_rng(1))
        assert abs(out2["population_weights"].sum() - 1) < 1e-9
    finally:
        spec.use_design_space("menu6")


def test_rsa_threshold_shifts_with_degree_prior():
    from pipeline.procbench.toy_statute import rsa_vagueness as V
    lo, hi = V.q1_prior_from_rsa("low"), V.q1_prior_from_rsa("high")
    assert hi["theta_mean"] > lo["theta_mean"]          # denser town: threshold sits higher on the scale
    assert 0.0 <= lo["P_Q1_desk_sufficient"] <= 1.0


def test_hen_package_round_trip():
    """Loading the hen statute from a package reproduces chains and the log posterior exactly."""
    import json
    from pipeline.procbench.toy_statute.model import Model
    pkg_path = Path(__file__).resolve().parents[1] / "runs" / "toy_statute2_20260929" / "hen_package_example.json"
    if not pkg_path.exists():
        pytest.skip("hen package example not present")
    spec.use_design_space("full")
    try:
        before = {s: spec.chain(s, 2, 1) for s in spec.STRUCTURE_IDS}
        ev = Path(__file__).resolve().parents[1] / "runs" / "toy_statute_20260926" / "W4" / "evidence"
        have_ev = ev.exists()
        if have_ev:
            m = Model(ev, center_towns=True)
            th = m.sample_prior_theta(np.random.default_rng(3))
            lp0 = m.logpost(th)
        spec.load_package(json.loads(pkg_path.read_text()))
        assert {s: spec.chain(s, 2, 1) for s in spec.STRUCTURE_IDS} == before
        assert spec.DESIGN_SPACE.startswith("package:")
        if have_ev:
            assert abs(Model(ev, center_towns=True).logpost(th) - lp0) < 1e-9
    finally:
        spec.use_design_space("menu6")


# ---------------------------------------------------------------- statute package 2 (round 5 prep)

PKG2 = Path(__file__).resolve().parents[1] / "runs" / "toy_statute2_20260929" / "statute_package.json"


@pytest.mark.skipif(not PKG2.exists(), reason="statute package 2 not present")
def test_author_validity_rules_match_author_counts():
    """The generic rule evaluator reproduces the author's independently computed validity counts."""
    import json
    from pipeline.procbench.toy_statute import validity_rules as VR
    pkg = json.loads(PKG2.read_text())
    spec.load_package(pkg)
    try:
        qids = [q["id"] for q in pkg["questions"]]
        V = VR.author_validity_matrix(pkg["validity_rules"], qids)
        for j, sid in enumerate(spec.STRUCTURE_IDS):
            assert int(V[:, j].sum()) == pkg["validity_rules"]["derived_validity"]["per_design"][sid]["n_valid_of_128"], sid
    finally:
        spec.use_design_space("menu6")


@pytest.mark.skipif(not PKG2.exists(), reason="statute package 2 not present")
def test_reader_validity_matrix_conjunction():
    from pipeline.procbench.toy_statute import validity_rules as VR
    pkg = __import__("json").loads(PKG2.read_text())
    spec.load_package(pkg)
    try:
        ids = spec.STRUCTURE_IDS
        reading = {"questions": [{"id": "A", "p_yes": 0.5, "major": True}, {"id": "B", "p_yes": 0.5, "major": True}],
                   "design_validity": {sid: {"A": {"valid_if_yes": True, "valid_if_no": sid != ids[0]},
                                             "B": {"valid_if_yes": sid != ids[1], "valid_if_no": True}} for sid in ids}}
        V, qids = VR.reader_validity_matrix(reading)
        assert qids == ["A", "B"] and V.shape == (4, len(ids))
        # reading (A=yes,B=yes): design ids[1] invalid; (A=no,B=no): ids[0] invalid; others valid
        assert not V[0, 1] and V[0, 0] and not V[3, 0] and V[3, 1]
    finally:
        spec.use_design_space("menu6")


# ---------------------------------------------------------------- audit 2026-09-29 counterexamples (F1, F2, F3)

def test_full_support_has_neither_aliasing_nor_tail_lumping():
    pm = np.zeros(grid.L_DAYS); pm[400] = 1.0
    cnt = [0] * 8; cnt[0] = 3
    out = grid.sum_pmfs(np.array([pm] * 8), [cnt])[0]
    assert int(np.argmax(out)) == 1200 and out[1200] == pytest.approx(1)
    assert grid.sum_pmfs(np.array([pm] * 8), [cnt], length=512).sum() == 0


def test_outcome_joint_normalizes_and_has_poisson_denial_marginal():
    from scipy.stats import poisson
    from pipeline.procbench.toy_statute import outcomes as O
    arr = {k: np.array([v]) for k, v in dict(l_dnv=1.5, l_dov=0.7, l_drest=4.0, l_nnv=2.0, l_nov=1.0).items()}
    tot, dm = 0.0, {}
    for D in range(0, 40):
        for Vu in range(0, 25):
            for Nu in range(0, 20):
                pv = float(np.exp(O._joint_denied_unpermitted(D, Vu, Nu, **arr)[0][0]))
                tot += pv; dm[D] = dm.get(D, 0.0) + pv
    assert abs(tot - 1.0) < 1e-6
    assert abs(dm[5] - poisson.pmf(5, 6.2)) < 1e-6


def test_completed_report_selection_matches_brute_force():
    import math
    from pipeline.procbench.toy_statute.model import Model, CONTAM
    ev = Path(__file__).resolve().parents[1] / "runs" / "toy_statute_20260926" / "W0" / "evidence"
    if not ev.exists():
        pytest.skip("W0 evidence not present")
    m = Model(ev, center_towns=True)
    p = m.param_dict(m.sample_prior_theta(np.random.default_rng(0))); sig = math.exp(p["lsig_r"])
    n = 0
    for town in m.towns:
        d = m.data[town]
        seg = grid.sum_pmfs(m.step_pmfs(p, town), d.seg_counts, length=grid.L_DAYS)
        gl = m._completed_gap_loglik(seg, d, sig, CONTAM); Lc, S = m.Lc, m.surv_post
        for ri in range(d.n_dec):
            gis = [g for g, r in enumerate(d.rep_of_gap) if r == ri]
            cis = [c for c in range(len(d.combos)) if all(d.gap_seg[c, g] >= 0 for g in gis)]
            if len(gis) not in (1, 2) or not cis:
                continue
            ci = cis[0]; qs = []
            for g in gis:
                v, u = d.gaps[g]; R = grid.report_lik_days(v, u, sig); ref = float(m.contam_days @ R)
                qs.append(seg[d.gap_seg[ci, g]] * ((1 - CONTAM) * R + CONTAM * ref))
            brute = (sum(qs[0][a] * S[a] for a in range(Lc)) if len(gis) == 1
                     else sum(qs[0][a] * qs[1][b] * S[a + b] for a in range(Lc) for b in range(Lc - a)))
            assert abs(math.log(brute) - gl[ci, ri]) < 1e-9
            n += 1
            if n >= 4:
                return
    assert n > 0


def test_score_mapped_residual_is_not_no():
    """Response audit R3: residual mass is reported separately, never scored as 'no'."""
    from pipeline.procbench.toy_statute import readings as Rd
    R = Rd.all_readings_for(["Q1"])
    p = np.zeros(len(R) + 1)
    p[next(j for j, r in enumerate(R) if r["Q1"])] = 0.5
    p[-1] = 0.5
    sc = Rd.score_mapped([p], ["Q1"], {"A": {"T1": True}}, {"Q1": "T1"}, ["A"])
    assert abs(sc["question_brier"]["Q1"]) < 1e-12 and abs(sc["mean_log_score"]) < 1e-12
    assert abs(sc["mean_residual_mass"] - 0.5) < 1e-12


def test_kitchen_package_answers_without_hen_counterfactual():
    """Response audit R1: a package without S1 must not request the hen intervention."""
    import json
    from pathlib import Path
    from pipeline.procbench.toy_statute import spec, estimands
    pkg = json.loads(Path("runs/toy_statute2_20260929/statute_package.json").read_text())
    try:
        spec.load_package(pkg)
        assert not estimands.counterfactual_available()
        keys = estimands.estimand_keys(["A"])
        assert not any("counterfactual" in k or ".cf_" in k for k in keys)
    finally:
        spec.use_design_space("menu6")
    assert estimands.counterfactual_available()
