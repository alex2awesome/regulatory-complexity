"""Regression tests for the 2026-10-01 real-data options in the toy-statute process engine:
unobserved web listings are masked, milestone contamination is opt-in, extreme logits stay finite."""
import math
from pathlib import Path

import numpy as np
import pytest

from pipeline.procbench.toy_statute import model

ROOT = Path(__file__).resolve().parents[1]
W0 = ROOT / "runs/toy_statute_20260926/W0/evidence"
pytestmark = pytest.mark.skipif(not W0.exists(), reason="W0 evidence not present")


def _model(**kw):
    return model.Model(W0, center_towns=True, design_space="menu6", **kw)


def test_masked_web_step_removes_exactly_its_term():
    m = _model()
    t = m.towns[0]
    p = m.param_dict(m.sample_prior_theta(np.random.default_rng(7)))
    full = m.town_struct_loglik_from_params(p, t)
    d = m.data[t]
    lam, ew = 1 / (1 + math.exp(-p["llam"])), 1 / (1 + math.exp(-p["lepsw"]))
    wl, pres = d.web_listed[0], d.web_present[:, 0]
    term = pres * (wl * math.log(lam) + (1 - wl) * math.log1p(-lam)) + (1 - pres) * (wl * math.log(ew) + (1 - wl) * math.log1p(-ew))
    d.web_observed = d.web_observed.copy()
    d.web_observed[0] = 0
    assert np.allclose(full - term, m.town_struct_loglik_from_params(p, t), atol=1e-10)


def test_milestone_contamination_is_opt_in():
    assert model.ModelConfig().milestone_contamination is False
    with pytest.raises(ValueError):
        model.ModelConfig(milestone_contamination="yes")


@pytest.mark.parametrize("x", [40.0, -40.0])
def test_extreme_town_logits_are_finite(x):
    m = _model()
    t = m.towns[0]
    p = m.param_dict(m.sample_prior_theta(np.random.default_rng(1)))
    p[f"lqobj_{t}"] = x
    p[f"lpinc_{t}"] = x
    assert np.all(np.isfinite(m.town_struct_loglik_from_params(p, t)))


def test_pending_contamination_is_opt_in_and_keeps_stale_open_cases_finite():
    assert model.ModelConfig().pending_contamination is False
    # contamination must span the open ages (real packages use 0-3650 days; the default is 365)
    m_off = _model(model_config={"contamination_max_days": 3650})
    m_on = _model(model_config={"contamination_max_days": 3650, "pending_contamination": True})
    t = next(t for t in m_off.towns if len(m_off.data[t].pend_N))
    th = m_off.sample_prior_theta(np.random.default_rng(5))
    for m in (m_off, m_on):   # every open case aged far beyond any modeled duration
        m.data[t].pend_N = np.full_like(m.data[t].pend_N, 3000)
    def short(m):   # steps of ~2 days: the model's own P(T > 3000) underflows
        p = m.param_dict(th)
        for k in list(p):
            if k.startswith("mu_"): p[k] = math.log(2.0)
            if k.startswith("lsig_") and k != "lsig_r": p[k] = math.log(0.1)
        return p
    on = m_on.town_struct_loglik_from_params(short(m_on), t)
    off = m_off.town_struct_loglik_from_params(short(m_off), t)
    assert np.all(np.isfinite(on)) and np.all(on > off) and (on - off).max() > 100


@pytest.mark.parametrize("x", [40.0, -40.0])
def test_extreme_shared_logits_are_finite(x):
    m = _model()
    t = next(t for t in m.towns if m.data[t].n_dec)
    p = m.param_dict(m.sample_prior_theta(np.random.default_rng(2)))
    for k in ("ldelta", "leps", "llam", "lepsw"):
        p[k] = x
    assert np.all(np.isfinite(m.town_struct_loglik_from_params(p, t)) | np.isneginf(m.town_struct_loglik_from_params(p, t)))
    assert not np.any(np.isnan(m.town_struct_loglik_from_params(p, t)))
