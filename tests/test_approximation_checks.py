import numpy as np
import pytest

from pipeline.procbench.approximation_checks import likelihood_weight_check


def test_large_constant_offset_does_not_change_posterior():
    result = likelihood_weight_check(np.full(100, 7.))
    assert result['acceptable']
    assert not result['legacy_absolute_threshold_passed']
    assert result['importance_ess_fraction'] == pytest.approx(1.)


def test_small_nonconstant_change_passes_but_large_reweighting_fails():
    result = likelihood_weight_check(np.linspace(-.03, .03, 100))
    assert result['acceptable']
    assert not result['legacy_absolute_threshold_passed']
    assert not likelihood_weight_check(np.linspace(-1., 1., 100))['acceptable']
    assert not likelihood_weight_check([0.]*99 + [4.])['acceptable']


@pytest.mark.parametrize('values', [[], [np.inf], [np.nan], [[0., 1.]]])
def test_invalid_approximation_check_is_not_a_pass(values):
    with pytest.raises(ValueError):
        likelihood_weight_check(values)
