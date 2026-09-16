"""Posterior-weight sensitivity to numerical likelihood approximations."""
import numpy as np
from scipy.special import logsumexp


def likelihood_weight_check(log_likelihood_changes, *, min_ess_fraction=.99, max_total_variation=.025):
    """Use signed refined-minus-base differences at base-posterior states.

    A constant likelihood offset changes no posterior weights. ESS here measures
    numerical reweighting overlap, NOT MCMC effective sample size or convergence.
    This is a finite-state diagnostic, not a uniform integration error bound.
    """
    delta = np.asarray(log_likelihood_changes, dtype=float)
    if delta.ndim != 1 or not len(delta) or not np.isfinite(delta).all():
        raise ValueError('Need a nonempty vector of finite signed likelihood differences')
    if not 0 < min_ess_fraction <= 1 or not 0 <= max_total_variation <= 1:
        raise ValueError('Invalid approximation tolerances')
    weights = np.exp(delta-logsumexp(delta))
    ess = min(float(len(delta)), float(1/np.sum(weights**2)))
    variation = float(.5*np.sum(np.abs(weights-1/len(weights))))
    return dict(criterion='posterior_weight_sensitivity/1', states_checked=len(delta),
        importance_ess=ess, importance_ess_fraction=ess/len(delta),
        normalized_weight_total_variation=variation, maximum_normalized_weight=float(weights.max()),
        max_absolute_log_likelihood_change=float(np.max(np.abs(delta))),
        log_likelihood_change_range=float(np.ptp(delta)),
        min_ess_fraction=min_ess_fraction, max_total_variation=max_total_variation,
        acceptable=bool(ess/len(delta) >= min_ess_fraction-1e-12 and variation <= max_total_variation),
        legacy_absolute_threshold_passed=bool(np.max(np.abs(delta)) < .01),
        qualification='Numerical overlap on checked posterior states, not chain ESS, independent replication or accuracy')
