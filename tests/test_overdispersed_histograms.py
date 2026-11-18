"""Source-free probability-law tests; not evidence that CF18 is model-ready."""
import itertools
import math

import numpy as np
import pytest
from scipy.special import gammaln, logsumexp
from scipy.stats import betabinom, dirichlet_multinomial

from pipeline.procbench.cohort_histograms import histogram_log_probability
from pipeline.procbench.overdispersed_histograms import (
    dirichlet_multinomial_log_probability as logpmf,
)


@pytest.mark.parametrize("kappa", [1e-8, 0.3, 3., 100., 1e6])
def test_matches_independent_scipy_law(kappa):
    n = [3, 7, 2]
    p = np.array([.2, .5, .3])
    expected = dirichlet_multinomial.logpmf(n, kappa * p, sum(n))
    assert logpmf(n, np.log(p), kappa) == pytest.approx(expected, abs=5e-8)


@pytest.mark.parametrize("kappa", [.15, 3., 200.])
def test_enumeration_normalizes_and_reproduces_variance(kappa):
    n, p = 7, np.array([.2, .3, .5])
    counts = np.array([[i, j, n-i-j] for i in range(n+1) for j in range(n-i+1)])
    masses = np.exp([logpmf(row.tolist(), np.log(p), kappa) for row in counts])
    assert masses.sum() == pytest.approx(1., abs=1e-13)
    mean = masses @ counts
    cov = np.einsum('i,ij,ik->jk', masses, counts-mean, counts-mean)
    np.testing.assert_allclose(mean, n*p, atol=1e-12, rtol=0)
    expected = n*(n+kappa)/(1+kappa)*(np.diag(p)-np.outer(p,p))
    np.testing.assert_allclose(cov, expected, atol=1e-11, rtol=0)


def test_two_bins_match_beta_binomial_without_defining_the_whole_model_that_way():
    for k in range(11):
        expected = betabinom.logpmf(k, 10, 2., 3.)
        assert logpmf([k, 10-k], np.log([.4, .6]), 5.) == pytest.approx(expected, abs=1e-12)


def test_multinomial_limit_without_switching_likelihood():
    n, p = [3, 7, 2], np.array([.2, .5, .3])
    expected = histogram_log_probability(n, p)
    assert logpmf(n, np.log(p), 1e12) == pytest.approx(expected, abs=1e-10)


def test_permutation_invariance():
    n, p = np.array([2, 0, 4]), np.array([.1, .4, .5])
    expected = logpmf(n.tolist(), np.log(p), 2.)
    for order in itertools.permutations(range(3)):
        at = list(order)
        assert logpmf(n[at].tolist(), np.log(p[at]), 2.) == pytest.approx(expected, abs=1e-13)


def test_single_trial_has_no_concentration_information():
    for kappa in [1e-20, .1, 1., 100., 1e100]:
        assert logpmf([0, 1, 0], np.log([.2, .3, .5]), kappa) == pytest.approx(math.log(.3), abs=5e-14)


def test_structural_zero_and_empty_cohort():
    assert logpmf([3, 0], [0., -np.inf], .4) == 0
    assert logpmf([3, 1], [0., -np.inf], .4) == -math.inf
    assert logpmf([0, 0], np.log([.2, .8]), .4) == 0


def test_underflowing_positive_support_is_not_a_structural_zero():
    assert logpmf([1, 0], [-1000., 0.], 2.) == pytest.approx(-1000., abs=1e-12)
    # Analytic small-alpha limit for all three observations in the tiny bin.
    expected = -1000. + math.log(2.) + gammaln(3) + gammaln(2.) - gammaln(5.)
    assert logpmf([3, 0], [-1000., 0.], 2.) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("counts", [[True, 1], [-1, 1], [1.2, 3], [2**53, 1]])
def test_invalid_counts_rejected(counts):
    with pytest.raises(ValueError):
        logpmf(counts, np.log([.5, .5]), 2.)


@pytest.mark.parametrize("kappa", [True, 0., -2., math.nan, math.inf, '2'])
def test_invalid_concentration_rejected(kappa):
    with pytest.raises(ValueError):
        logpmf([2, 1], np.log([.5, .5]), kappa)


@pytest.mark.parametrize("logs", [[0., 0.], [-np.inf, -np.inf], [np.nan, 0.],
                                  [np.inf, 0.], [True, False], ['0', '-1']])
def test_invalid_log_masses_rejected(logs):
    with pytest.raises(ValueError):
        logpmf([2, 1], logs, 2.)
