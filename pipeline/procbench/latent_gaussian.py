"""Small, testable elliptical-slice sampler and rank-based chain diagnostics.

All coordinates have independent standard-normal priors; deterministic transforms
provide location/scale hierarchies. The callback is ONLY the log likelihood.
Algorithm: Murray, Adams & MacKay (2010), proceedings.mlr.press/v9/murray10a.html.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.special import ndtri
from scipy.stats import rankdata


def elliptical_slice(state, indices, likelihood, current, rng):
    """One exact-prior block transition, with no adaptation or step-size parameter."""
    indices = np.asarray(indices, dtype=int)
    if not len(indices):
        return state, current, 0
    old = state[indices].copy()
    direction = rng.normal(size=len(indices))
    height = current + math.log(max(rng.random(), np.finfo(float).tiny))
    angle = rng.uniform(0, 2 * math.pi)
    low, high = angle - 2 * math.pi, angle
    proposal = state.copy()
    for calls in range(1, 10001):
        proposal[indices] = old * math.cos(angle) + direction * math.sin(angle)
        value = likelihood(proposal)
        if np.isfinite(value) and value >= height:
            return proposal, value, calls
        if angle < 0:
            low = angle
        else:
            high = angle
        angle = rng.uniform(low, high)
    raise RuntimeError("Elliptical slice bracket did not close; inspect the likelihood")


def _split(chains):
    chains = np.asarray(chains, dtype=float)
    half = chains.shape[1] // 2
    if half < 4:
        raise ValueError("Need at least eight draws per chain for diagnostics")
    return np.concatenate((chains[:, :half], chains[:, -half:]), axis=0)


def _rhat(x):
    n = x.shape[1]
    within = np.var(x, axis=1, ddof=1).mean()
    between = n * np.var(x.mean(axis=1), ddof=1)
    if within == 0:
        return 1.0 if between == 0 else float("inf")
    return float(np.sqrt(((n - 1) / n * within + between / n) / within))


def _rank(x):
    return ndtri((rankdata(x, method="average").reshape(x.shape) - .375) / (x.size + .25))


def effective_size(x):
    """Multi-chain initial-positive, initial-monotone paired autocorrelation ESS."""
    m, n = x.shape
    centered = x - x.mean(axis=1, keepdims=True)
    fft = np.fft.rfft(centered, n=2 ** math.ceil(math.log2(2 * n)))
    acov = np.fft.irfft(fft * np.conjugate(fft), axis=1)[:, :n] / n
    within = np.var(x, axis=1, ddof=1).mean()
    var_plus = (n - 1) / n * within + np.var(x.mean(axis=1), ddof=1)
    if var_plus <= 0:
        return float(m * n)
    rho = 1 - (within - acov.mean(axis=0)) / var_plus
    rho[0] = 1
    pairs = []
    previous = float("inf")
    for i in range(0, n - 1, 2):
        pair = rho[i] + rho[i + 1]
        if pair < 0:
            break
        previous = min(previous, pair)
        pairs.append(previous)
    tau = max(1 / math.log10(max(m * n, 10)), -1 + 2 * sum(pairs))
    return float(min(m * n, m * n / tau))


def diagnostics(chains):
    x = _split(chains)
    ranked = _rank(x)
    folded = _rank(np.abs(x - np.median(x)))
    lo, hi = np.quantile(x, [.05, .95])
    rhat = max(_rhat(ranked), _rhat(folded))
    return {"rhat": rhat if np.isfinite(rhat) else None,
            "ess_bulk": effective_size(ranked),
            "ess_tail": min(effective_size((x <= lo).astype(float)),
                            effective_size((x >= hi).astype(float)))}


def summary(values):
    x = np.asarray(values, dtype=float)
    return {"median": float(np.median(x)), "mean": float(np.mean(x)),
            "ci90": np.quantile(x, [.05, .95]).tolist()}


def information_report(states, blocks, *, sampling_converged=None, threshold=.25):
    """Prior/posterior diagnostics for independent N(0,1) coordinates.

    1 - posterior variance is *marginal variance contraction*, not a fraction
    of all information learned. Keep mean shifts, variance expansion and joint
    directions visible. Never use this screen to silently fix uncertain effects.
    """
    states = np.asarray(states, dtype=float)
    if states.ndim != 3 or states.shape[0]*states.shape[1] < 2 or not np.isfinite(states).all():
        raise ValueError('Need finite chains-by-draws-by-whitened-coordinates')
    flat = states.reshape(-1, states.shape[-1])
    mean, variance = flat.mean(axis=0), flat.var(axis=0, ddof=1)
    contraction = 1-variance
    reports = {}
    for name, raw in blocks.items():
        indices = np.asarray(raw, dtype=int).ravel()
        if not len(indices):
            continue
        if len(set(indices)) != len(indices) or np.any(indices < 0) or np.any(indices >= flat.shape[1]):
            raise ValueError('Information blocks must contain valid distinct coordinate indices')
        average = float(contraction[indices].mean())
        low = average < threshold
        minimum_joint_variance = None
        if len(flat) > len(indices)+1:
            covariance = np.atleast_2d(np.cov(flat[:, indices], rowvar=False, ddof=1))
            minimum_joint_variance = max(0., float(np.linalg.eigvalsh(covariance)[0]))
        reports[name] = dict(coordinates=len(indices), mean_variance_contraction=average,
            median_variance_contraction=float(np.median(contraction[indices])),
            fraction_below_10_percent=float(np.mean(contraction[indices] < .1)),
            rms_posterior_mean_in_prior_sd=float(np.sqrt(np.mean(mean[indices]**2))),
            minimum_joint_direction_variance=minimum_joint_variance,
            status='low_marginal_contraction_prior_sensitive' if low else 'marginal_contraction_observed',
            headline_eligible=not low and sampling_converged is True,
            headline_rule='Screen for separate block-effect claims, not automatically for derived sums or process predictions')
    return dict(schema_version='whitened-prior-information/1', coordinates=flat.shape[1],
        draws=len(flat), sampling_converged=sampling_converged, threshold=threshold,
        coordinates_below_10_percent=int(np.sum(contraction < .1)),
        coordinates_below_25_percent=int(np.sum(contraction < .25)),
        posterior_mean=mean.tolist(), posterior_variance=variance.tolist(),
        marginal_variance_contraction=contraction.tolist(), blocks=reports,
        qualifications=['Conditional on independent standard-normal prior coordinates and the saved parameterization.',
            'Marginal contraction is not identifiability, mutual information, or proof that a posterior equals its prior.',
            'Mean shifts and correlations can contain information even if every component contracts little.',
            'Negative contraction is retained; posterior variance can exceed prior variance.',
            'Joint-direction covariance is descriptive and sample-dependent, not a pre-fit information bound.',
            'Weak components are flagged, not fixed to point values; derived burden needs its own prior-sensitivity assessment.',
            'Unconverged chains make these posterior summaries provisional.'])
