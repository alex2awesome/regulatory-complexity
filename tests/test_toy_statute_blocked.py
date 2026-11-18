"""Bounded same-target cache/transition checks, not a convergence claim."""
import copy
import json
import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from pipeline.procbench.toy_statute import spec
from pipeline.procbench.toy_statute.model import Model
from pipeline.procbench.toy_statute.blocked import TownCache, proposal_geometry
from test_toy_statute_response_repairs import make_evidence


@pytest.fixture
def pair(tmp_path):
    spec.use_design_space("menu6")
    ev = make_evidence(tmp_path)
    for file in ("admin_records", "reports"):
        p = ev / f"{file}.json"
        rows = json.loads(p.read_text())
        other = copy.deepcopy(rows)
        for r in other: r["town"] = "Birch"
        p.write_text(json.dumps(rows+other))
    p = ev / "public_spec.json"
    public = json.loads(p.read_text()); public["towns"].append("Birch")
    p.write_text(json.dumps(public))
    p = ev / "webpages.json"
    pages = json.loads(p.read_text()); pages["Birch"] = copy.deepcopy(pages["Amber"])
    pages["Birch"]["town"] = "Birch"; p.write_text(json.dumps(pages))
    return ev


@pytest.mark.parametrize("centered", [False, True])
def test_sparse_and_shared_cache_matches_full_target(pair, centered):
    m = Model(pair, center_towns=centered, blocks=[("desk_review", "decision_issue")])
    x = m.sample_prior_theta(np.random.default_rng(2))
    cache = TownCache(m, x)
    assert_allclose(cache.ll, m.loglik(x), atol=1e-10, rtol=0)
    rng = np.random.default_rng(71)
    geometry = proposal_geometry(m, np.stack([x+rng.normal(0,.015,len(x)) for _ in range(16)]))
    for _ in range(3):
        stat = cache.sweep(rng, .63, geometry)
        assert stat["town_evaluations"] == (4*len(m.towns)-2 if centered else 3*len(m.towns))
        assert_allclose(cache.ll, m.loglik(cache.x), atol=1e-10, rtol=0)
        assert_allclose(cache.lp, m.logprior(cache.x), atol=1e-10, rtol=0)
        assert_allclose(list(cache.p.values()), list(m.param_dict(cache.x).values()), atol=1e-12, rtol=0)


def test_local_acceptance_matches_full_recomputation_and_rejection_restores(pair):
    m = Model(pair, center_towns=True)
    x = m.sample_prior_theta(np.random.default_rng(2))
    cache = TownCache(m, x)
    for ids, change, towns in ((cache.local[0], [.05, -.02], [0]), (cache.speed, [.03, -.03], [0,1])):
        prop = cache.x.copy(); prop[ids] += change
        lr = m.logprior(prop)-m.logprior(cache.x)+.7*(m.loglik(prop)-m.loglik(cache.x))
        before = cache.x.copy()
        yes = cache.local_move(ids, change, towns, .7, -1.)
        assert yes == (lr >= -1.)
        assert_allclose(cache.x, prop if yes else before, atol=0, rtol=0)
        before = cache.x.copy(); p = cache.p.copy(); ll = cache.ll
        assert not cache.local_move(ids, change, towns, .7, float("inf"))
        assert_allclose(cache.x, before, atol=0, rtol=0)
        assert cache.p == p and cache.ll == ll
    with pytest.raises(ValueError, match="zero sum"):
        cache.local_move(cache.speed[:1], [.1], [0], 1., -1.)
    with pytest.raises(ValueError, match="affected towns"):
        cache.local_move(cache.local[0], [.1,.1], [1], 1., -1.)


def test_grand_mean_draw_is_prior_conditional_and_does_not_change_effective_speeds(pair):
    m = Model(pair, center_towns=True, prior_overrides={"la_Birch": ("normal", .2, .5)})
    cache = TownCache(m, m.sample_prior_theta(np.random.default_rng(2)))
    old_p, old_ll = cache.p.copy(), cache.ll
    raw = cache.x[cache.speed]; contrasts = raw-raw.mean()
    prec = np.array([1/.3**2, 1/.5**2])
    expected_mean = np.sum((np.array([0.,.2])-contrasts)*prec)/prec.sum()
    expected_sd = math.sqrt(1/prec.sum())
    rng = np.random.default_rng(14)
    draws = []
    for _ in range(1500):
        cache.refresh_grand_mean(rng); draws.append(cache.x[cache.speed].mean())
    assert abs(np.mean(draws)-expected_mean) < .08*expected_sd
    assert abs(np.std(draws)/expected_sd-1) < .08
    assert cache.p == old_p and cache.ll == old_ll
    assert_allclose(cache.ll, m.loglik(cache.x), atol=1e-10, rtol=0)


def test_blocked_worker_uses_real_target(pair, monkeypatch):
    from pipeline.procbench.toy_statute import smc
    m = Model(pair, center_towns=True)
    x = m.sample_prior_theta(np.random.default_rng(2))
    rng = np.random.default_rng(17)
    X = np.stack([x+rng.normal(0,.02,len(x)) for _ in range(4)])
    geometry = proposal_geometry(m, X)
    monkeypatch.setattr(smc, "_MODEL", m)
    Y, LP, LL, acc = smc._blocked_move_chunk((X, .45, geometry, 1., 1, 183))
    assert 0 <= acc <= 1
    for y, lp, ll in zip(Y, LP, LL):
        assert_allclose(lp, m.logprior(y), atol=1e-10, rtol=0)
        assert_allclose(ll, m.loglik(y), atol=1e-10, rtol=0)
