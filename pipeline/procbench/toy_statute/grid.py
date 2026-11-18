"""Exact discretized-grid machinery shared by generator, model and estimands.

Durations are generated as lognormal values rounded to the grid (whole days,
or quarter hours), so the model's discretized pmfs are exact for the
generator, not approximations.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import ndtr, log_ndtr, logsumexp

L_DAYS = 512          # day grid 0..511
HOUR_UNIT = 0.25      # hours grid step
L_HOURS = 512         # 0..127.75 h
CONTAM_MAX_DAYS = 365
TINY = 1e-300


def discretized_lognormal(medians, sigmas, length, unit=1.0):
    """pmf over grid index i (value i*unit) of round(X/unit), X~LogNormal(log m, s).

    medians, sigmas: arrays (n,). Returns (n, length), renormalized after
    truncation at the grid end.
    """
    medians = np.atleast_1d(np.asarray(medians, float))
    sigmas = np.atleast_1d(np.asarray(sigmas, float))
    edges = (np.arange(length + 1) - 0.5) * unit
    edges[0] = 0.0
    with np.errstate(divide="ignore"):
        le = np.log(edges)  # -inf at 0
    z = (le[None, :] - np.log(medians)[:, None]) / sigmas[:, None]
    # Work in the lower tail or the reflected upper tail, whichever avoids
    # subtracting CDFs rounded to one. Normalize in log space: a far-above-grid
    # lognormal still has a valid CONDITIONAL distribution on this grid.
    lower, upper = z[:, :-1], z[:, 1:]
    reflected = lower > 0
    a = log_ndtr(np.where(reflected, -lower, upper))
    b = log_ndtr(np.where(reflected, -upper, lower))
    with np.errstate(divide="ignore", invalid="ignore"):
        logp = a + np.log(-np.expm1(np.minimum(b-a, 0.0)))
    normalizer = logsumexp(logp, axis=1, keepdims=True)
    if not np.isfinite(normalizer).all():
        raise ValueError("non-normalizable discretized lognormal; inspect proposed parameters")
    return np.exp(logp-normalizer)


def sample_rounded_lognormal(rng, median, sigma, length, unit=1.0):
    """Generator counterpart of discretized_lognormal (resample past grid end)."""
    while True:
        x = median * math.exp(sigma * rng.standard_normal())
        i = int(math.floor(x / unit + 0.5))
        if i < length:
            return i


def sum_pmfs(pmfs, counts, length=None):
    """Cached positive convolutions: full support or an UNNORMALIZED prefix.

    No overflow is put into a terminal bin. A prefix is sufficient below a
    posting horizon, but hours reports and predictions need full support.
    Positive arithmetic avoids FFT cancellation in tiny milestone probabilities.
    Independent reference implementations live only in tests.
    """
    pmfs = np.asarray(pmfs, float)
    raw = np.asarray(counts)
    if raw.ndim != 2 or raw.shape[1] != len(pmfs) or np.any(raw < 0) or np.any(raw != np.floor(raw)):
        raise ValueError("counts must be a nonnegative integer matrix over step types")
    counts = raw.astype(int)
    full_length = int(counts.sum(axis=1).max(initial=0)) * (pmfs.shape[1] - 1) + 1
    length = full_length if length is None else int(length)
    if length < 1:
        raise ValueError("convolution length must be positive")
    out = np.zeros((len(counts), length))
    cache = {tuple([0] * len(pmfs)): np.array([1.0])}

    def build(key):
        if key not in cache:
            j = next(j for j in reversed(range(len(key))) if key[j])
            parent = list(key)
            parent[j] -= 1
            a = build(tuple(parent))
            b = pmfs[j, :length]
            if len(a) == 1:
                value = a[0] * b
            else:
                value = np.convolve(a, b)[:length]
            cache[key] = value
        return cache[key]

    for i, c in enumerate(counts):
        value = build(tuple(c))
        out[i, :len(value)] = value
    return out


def contamination_pmf_days(length=L_DAYS, xmax=CONTAM_MAX_DAYS):
    """round(exp(U(0, log xmax))) on the day grid."""
    i = np.arange(length, dtype=float)
    lo = np.clip(i - 0.5, 1.0, xmax)
    hi = np.clip(i + 0.5, 1.0, xmax)
    p = (np.log(hi) - np.log(lo)) / math.log(xmax)
    return p / p.sum()


def sample_contamination_days(rng, xmax=CONTAM_MAX_DAYS):
    return int(math.floor(math.exp(rng.uniform(0.0, math.log(xmax))) + 0.5))


# ---- report rounding / noise -------------------------------------------------

UNITS = {"day": (1.0, 0.0, 14.0), "week": (7.0, 14.0, 70.0), "month": (30.4, 70.0, math.inf)}


def report_days(rng, x, sigma):
    """Generator: noisy, rounded report of a true gap x (whole days)."""
    if x <= 0:
        return 0, "day"
    v = x * math.exp(sigma * rng.standard_normal())
    for unit, (mult, lo, hi) in UNITS.items():
        if lo <= v < hi:
            return int(math.floor(v / mult + 0.5)), unit
    raise AssertionError


def report_lik_days(value, unit, sigma, length=L_DAYS):
    """P(report (value, unit) | true gap x) for x = 0..length-1."""
    x = np.arange(length, dtype=float)
    out = np.zeros(length)
    if unit == "day" and value == 0:
        out[0] = 1.0
    if unit == "interval":
        lo, hi = value
        out[0] = float(lo <= 0 <= hi)
    else:
        mult, ulo, uhi = UNITS[unit]
        lo = max((value - 0.5) * mult, ulo)
        hi = min((value + 0.5) * mult, uhi)
    if hi <= lo:
        return out
    xs = x[1:]
    with np.errstate(divide="ignore"):
        zhi = (math.log(hi) - np.log(xs)) / sigma if math.isfinite(hi) else np.full(xs.shape, np.inf)
        zlo = (math.log(lo) - np.log(xs)) / sigma if lo > 0 else np.full(xs.shape, -np.inf)
    out[1:] = np.clip(ndtr(zhi) - ndtr(zlo), 0.0, None)
    return out


def report_hours(rng, h_idx, sigma):
    """Generator: hours reported to the nearest half hour with multiplicative noise."""
    x = h_idx * HOUR_UNIT
    if x <= 0:
        return 0.0
    v = x * math.exp(sigma * rng.standard_normal())
    return math.floor(v / 0.5 + 0.5) * 0.5


def report_lik_hours(value, sigma, length=L_HOURS):
    x = np.arange(length, dtype=float) * HOUR_UNIT
    out = np.zeros(length)
    if value == 0:
        out[0] = 1.0
    lo = max(value - 0.25, 0.0)
    hi = value + 0.25
    xs = x[1:]
    zhi = (math.log(hi) - np.log(xs)) / sigma
    zlo = (math.log(lo) - np.log(xs)) / sigma if lo > 0 else np.full(xs.shape, -np.inf)
    out[1:] = np.clip(ndtr(zhi) - ndtr(zlo), 0.0, None)
    return out


def truncated_geometric(p, kmax):
    k = np.arange(kmax + 1)
    if not 0 <= p <= 1:
        raise ValueError("geometric tilt must lie in [0,1]")
    # The (1-p) factor cancels; retain the finite uniform limit at p=1.
    w = p ** k
    return w / w.sum()


def survival_from_full_pmf(pmf, ages):
    """P(T > age), using a full-support PMF without 1-CDF cancellation."""
    tail = np.concatenate([np.cumsum(pmf[:, ::-1], axis=1)[:, ::-1],
                           np.zeros((len(pmf), 1))], axis=1)
    return tail[:, np.minimum(np.asarray(ages)+1, pmf.shape[1])]


def quantile_from_pmf(pmf, q):
    c = np.cumsum(pmf)
    return int(np.searchsorted(c, q - 1e-12))
