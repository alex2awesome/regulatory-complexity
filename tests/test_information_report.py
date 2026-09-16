import numpy as np
import pytest

from pipeline.procbench.latent_gaussian import information_report


def standardized(seed, dimensions):
    z = np.random.default_rng(seed).normal(size=(4, 1000, dimensions))
    flat = z.reshape(-1, dimensions)
    return (z-flat.mean(axis=0))/flat.std(axis=0, ddof=1)


def test_marginal_contraction_does_not_confuse_mean_shift_with_no_information():
    z = standardized(23, 2)
    z[:, :, 0] += 3
    z[:, :, 1] *= .5
    report = information_report(z, {'shifted': [0], 'narrowed': [1]}, sampling_converged=True)
    assert report['marginal_variance_contraction'] == pytest.approx([0., .75], abs=1e-12)
    assert report['blocks']['shifted']['rms_posterior_mean_in_prior_sd'] == pytest.approx(3.)
    assert not report['blocks']['shifted']['headline_eligible']
    assert report['blocks']['narrowed']['headline_eligible']


def test_identified_sum_can_coexist_with_weak_marginal_components():
    z = standardized(42, 8)
    direction = np.ones(8)/np.sqrt(8)
    # Tighten only the sum direction; each marginal retains ~7/8 of its variance.
    z -= .99*(z@direction)[:, :, None]*direction
    report = information_report(z, {'confounded_components': list(range(8))})
    block = report['blocks']['confounded_components']
    assert block['mean_variance_contraction'] < .25
    assert block['minimum_joint_direction_variance'] < .001


def test_variance_expansion_is_not_clipped_and_unconverged_fit_has_no_headline():
    z = standardized(7, 2)
    z[:, :, 0] *= 2
    z[:, :, 1] *= .1
    report = information_report(z, {'wide': [0], 'narrow': [1]}, sampling_converged=False)
    assert report['marginal_variance_contraction'][0] == pytest.approx(-3.)
    assert not report['blocks']['narrow']['headline_eligible']


def test_bad_input_blocks_fail_instead_of_fake_identification():
    with pytest.raises(ValueError):
        information_report(np.zeros((2, 4)), {'x': [0]})
    with pytest.raises(ValueError):
        information_report(standardized(1, 1), {'x': [1]})
