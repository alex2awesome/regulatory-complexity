"""Optional count likelihood for a future V6 repeated-cohort adapter.

The existing exact-cohort multinomial remains unchanged. This module is not
imported by V6 yet: using it requires an explicit panel/population contract.

For one cohort, q ~ Dirichlet(concentration * p), then n | q ~ Multinomial(N,q).
Integrating q gives a Dirichlet-multinomial. It represents extra variation in
recorded bin composition, NOT source bias, missing counts, cohort overlap, or
cross-month dependence. Those require separate declarations/latent effects.

Log-probability inputs preserve very small but positive bin support. There is
no probability floor or automatic multinomial substitution at large precision.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import betaln, digamma, logsumexp, polygamma

from .cohort_histograms import _validate_counts


def _log_beta_integer_second(log_alpha: float, count: int) -> float:
    """log B(alpha,n), allowing positive alpha below floating-point support.

    B(alpha,n) = 1/alpha * product_{k=1}^{n-1} k/(k+alpha).
    When alpha<=1e-6, a second-order log1p expansion has absolute remainder
    below alpha^3*zeta(3)/3 < 4.01e-19. This avoids underflow, not truncation
    of the model's probability support. For n=1 the expression is exact.
    """
    if count == 1:
        return -log_alpha
    if log_alpha <= math.log(1e-6):
        alpha = math.exp(log_alpha)  # Underflow to zero only in negligible terms.
        harmonic = float(digamma(count)) + float(np.euler_gamma)
        harmonic2 = math.pi**2 / 6 - float(polygamma(1, count))
        return -log_alpha - alpha * harmonic + 0.5 * alpha**2 * harmonic2
    return float(betaln(math.exp(log_alpha), count))


def dirichlet_multinomial_log_probability(
    bin_counts, log_probabilities, concentration: float,
) -> float:
    """Normalized integrated cohort probability, conditional on its total.

    ``log_probabilities`` are normalized log masses (negative infinity denotes
    structural zero support). ``concentration`` is positive and finite; larger
    values approach the existing multinomial. Zero observed counts in a bin do
    NOT imply zero probability. An all-zero cohort contributes zero log mass,
    hence no information, conditional on its observed zero total.

    The collapsed expression log(N)-sum(log(n_j))+log B(kappa,N)
    -sum(log B(kappa*p_j,n_j)) is over positive counts only. It avoids the
    severe gamma-function cancellation at large concentration.
    """
    counts = _validate_counts(bin_counts)
    raw = np.asarray(log_probabilities)
    if (raw.ndim != 1 or raw.shape != (len(counts),)
            or raw.dtype.kind not in "fiu"):
        raise ValueError("Log masses must be a real numeric vector aligned with counts")
    logs = np.asarray(raw, dtype=float)
    if np.any(np.isnan(logs)) or np.any(np.isposinf(logs)) or np.all(np.isneginf(logs)):
        raise ValueError("Log masses must have finite normalized support")
    norm = float(logsumexp(logs))
    if not math.isfinite(norm) or abs(norm) > 1e-12:
        raise ValueError("Log masses must sum to one without a probability floor")
    logs = logs - norm  # Numerical normalization only; structural zeros remain.
    if (isinstance(concentration, (bool, np.bool_))
            or not isinstance(concentration, (int, float, np.integer, np.floating))
            or not math.isfinite(concentration) or concentration <= 0):
        raise ValueError("Concentration must be positive, finite and nonboolean")
    total = sum(counts)
    if total > 2**53:
        raise ValueError("Count total exceeds exact float64 integer representation")
    if not total:
        return 0.0
    positive = [(n, float(lp)) for n, lp in zip(counts, logs) if n > 0]
    if any(lp == -math.inf for _, lp in positive):
        return -math.inf
    if len(positive) == 1 and positive[0][1] == 0.0:
        return 0.0
    log_kappa = math.log(concentration)
    value = math.fsum([
        math.log(total),
        -math.fsum(math.log(n) for n, _ in positive),
        _log_beta_integer_second(log_kappa, total),
        -math.fsum(_log_beta_integer_second(log_kappa + lp, n)
                   for n, lp in positive),
    ])
    if not math.isfinite(value):
        raise FloatingPointError("Nonfinite integrated histogram probability")
    # A materially positive log mass signals numerical trouble, not a value to
    # clip into support. Small rounding errors also remain visible to callers.
    if value > 1e-9:
        raise FloatingPointError("Integrated histogram probability exceeds one")
    return float(value)
