import numpy as np
from pipeline.procbench.latent_gaussian import elliptical_slice, diagnostics


def test_gaussian_conjugate_posterior():
    # Prior N(0,1), y=2 with sd=.5 -> posterior mean=1.6, variance=.2.
    rng = np.random.default_rng(711)
    f = lambda z: -.5 * ((z[0] - 2) / .5) ** 2
    state = np.zeros(1)
    current = f(state)
    draws = []
    for i in range(10000):
        state, current, _ = elliptical_slice(state, [0], f, current, rng)
        if i >= 1000:
            draws.append(state[0])
    assert abs(np.mean(draws) - 1.6) < .035
    assert abs(np.var(draws) - .2) < .02


def test_flat_likelihood_preserves_prior_and_other_coordinates():
    rng = np.random.default_rng(2026)
    state = np.array([0., 37.])
    draws = []
    for _ in range(6000):
        state, _, _ = elliptical_slice(state, [0], lambda _: 0., 0., rng)
        assert state[1] == 37
        draws.append(state[0])
    assert abs(np.mean(draws)) < .05
    assert abs(np.var(draws) - 1) < .07


def test_rank_diagnostics_detect_bad_chains_and_scale_disagreement():
    rng = np.random.default_rng(3)
    good = rng.normal(size=(4, 2000))
    d = diagnostics(good)
    assert d['rhat'] < 1.01
    assert d['ess_bulk'] > 5000
    bad = good + np.arange(4)[:, None]
    assert diagnostics(bad)['rhat'] > 1.25
    bad = good * np.array([1, 1, 8, 8])[:, None]
    assert diagnostics(bad)['rhat'] > 1.15
