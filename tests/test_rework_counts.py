import math

import numpy as np
import pytest

from pipeline.procbench.rework_counts import ReworkLaw


def test_hurdle_count_law_preserves_mass_and_correct_moments():
    law = ReworkLaw(.6, .35)
    n = np.arange(100)
    mass = np.array([law.probability(int(k)) for k in n])
    assert mass.sum() == pytest.approx(1)
    mean = n @ mass
    assert mean == pytest.approx(law.mean_additional_rounds)
    assert (n-mean)**2 @ mass == pytest.approx(law.variance_additional_rounds)
    assert law.at_least(1) == .6
    assert law.aggregate_correction_fraction_per_visit == pytest.approx(.6/(.65+.6))
    assert law.aggregate_correction_fraction_per_visit != law.probability_any


def test_finite_bins_keep_overflow_instead_of_forcing_a_maximum_number_of_steps():
    law = ReworkLaw(.8, .95)
    bins = law.finite_bins(3)
    assert len(bins) == 5
    assert bins.sum() == pytest.approx(1)
    assert bins[-1] == pytest.approx(.8*.95**3)
    assert bins[-1] > .5
    assert law.quantile(.999) > 3


def test_inverse_cdf_recovers_counts_and_handles_no_repeat_boundary():
    law = ReworkLaw(.4, .5)
    for u in np.linspace(.001, .999, 1000):
        k = law.quantile(float(u))
        assert 1-law.at_least(k+1) >= u-1e-12
        assert k == 0 or 1-law.at_least(k) < u+1e-12
    assert ReworkLaw(0, .9).quantile(.999) == 0
    assert ReworkLaw(1, 0).quantile(.5) == 1
    assert ReworkLaw(1, .3).quantile(0) == 1
    assert ReworkLaw(.4, 0).quantile(.7) == 1


def test_bounded_forum_selection_is_normalized_even_for_a_large_posting_tilt():
    law = ReworkLaw(.4, .35)
    for strength in (0., 2., 1000.):
        mass = np.exp([law.selected_log_probability(k, strength, threshold=2) for k in range(100)])
        assert mass.sum() == pytest.approx(1, abs=1e-12)
    assert math.isinf(ReworkLaw(0, .5).selected_log_probability(1, 2.))


def test_invalid_count_law_and_nonintegral_visits_are_rejected():
    with pytest.raises(ValueError):
        ReworkLaw(.5, 1)
    with pytest.raises(ValueError):
        ReworkLaw(.5, .3).probability(1.5)
    with pytest.raises(ValueError):
        ReworkLaw(.5, .3).quantile(1)
