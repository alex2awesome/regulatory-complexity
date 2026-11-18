"""Slow, independent numerical oracles. Never imported by production code.

These are test calculations, not user-selectable inference backends. Historical
implementations live in immutable run snapshots, not this helper.
"""
import math
from unittest.mock import patch

import numpy as np
from scipy.special import logsumexp
from scipy.stats import binom, poisson

from pipeline.procbench.toy_statute import grid
from pipeline.procbench.toy_statute.model import Model


def sum_pmfs_direct(pmfs, counts, length=None):
    counts = np.asarray(counts, int)
    length = (int(counts.sum(axis=1).max(initial=0)) * (pmfs.shape[1]-1) + 1
              if length is None else length)
    out = np.zeros((len(counts), length))
    for i, row in enumerate(counts):
        value = np.array([1.0])
        for j, repetitions in enumerate(row):
            for _ in range(repetitions):
                value = np.convolve(value, pmfs[j])
        end = min(length, len(value))
        out[i, :end] = value[:end]
    return out


class ReferenceModel(Model):
    """Keep the same scientific likelihood; independently evaluate its integrals."""
    def town_struct_loglik(self, theta, town):
        with patch.object(grid, "sum_pmfs", sum_pmfs_direct):
            return super().town_struct_loglik(theta, town)

    def _completed_gap_loglik(self, seg, d, sig_r, c0):
        out = np.zeros((len(d.combos), d.n_dec))
        for ri, gis in enumerate(d.gaps_of_rep):
            if not gis:
                continue
            product = np.zeros((len(d.combos), self.Lc))
            product[:, 0] = 1
            possible = np.ones(len(d.combos), bool)
            for gi in gis:
                value, unit = d.gaps[gi]
                report = grid.report_lik_days(value, unit, sig_r,
                                             length=max(self.Lc, len(self.contam_days)))
                ref = self.contam_days @ report[:len(self.contam_days)]
                kernel = (1-c0) * report[:self.Lc] + c0 * ref
                indices = d.gap_seg[:, gi]
                possible &= indices >= 0
                factor = np.zeros_like(product)
                ok = indices >= 0
                factor[ok] = seg[indices[ok], :self.Lc] * kernel
                product = np.stack([np.convolve(a, b)[:self.Lc] for a, b in zip(product, factor)])
            value = product @ self.surv_post[:self.Lc]
            with np.errstate(divide="ignore"):
                out[:, ri] = np.where(possible, np.log(value), -np.inf)
        return out


def poisson_survey_reference(S, n, H, K_obs, lam):
    """Full finite sum for the zero-denied-count special case."""
    r = np.arange(H-K_obs+1)
    return float(logsumexp(poisson.logpmf(r, lam) + binom.logpmf(S, n, (K_obs+r)/H)))


def stage_c_reference(L, prior, logchoice, kappa=None, n_w=200, rng=None):
    """Uncollapsed sum with the original contraction order; test oracle only."""
    N, T, D = L.shape
    R = len(prior)
    if logchoice.ndim == 2:
        lc = np.broadcast_to(logchoice, (N, T, R, D))
    elif logchoice.ndim == 3:
        lc = np.broadcast_to(logchoice[:, None], (N, T, R, D))
    else:
        lc = logchoice
    m = logsumexp(L[:, :, None] + lc, axis=3)
    base = logsumexp(L, axis=2) - math.log(D)
    rng = rng or np.random.default_rng(0)
    if kappa is None:
        W = np.log(prior + 1e-300)[None]
        n_w = 1
    else:
        W = np.log(rng.dirichlet(np.maximum(kappa*prior, 1e-6), size=n_w) + 1e-300)
    lt = logsumexp(m[:, None] + W[None, :, None], axis=3)
    ratio = (lt - base[:, None]).sum(axis=2)
    logZ = logsumexp(ratio) - math.log(N*n_w)
    weight = np.exp(ratio-logsumexp(ratio))
    post_r = np.exp(m[:, None] + W[None, :, None] - lt[..., None])
    post_s = np.exp(L[:, :, None] + lc - m[..., None])
    return {"log_marginal_ratio": float(logZ), "ess": float(1/(weight**2).sum()),
            "town_reading": np.einsum("nk,nktr->tr", weight, post_r),
            "town_design": np.einsum("nk,nktr,ntrd->td", weight, post_r, post_s),
            "population_weights": np.einsum("nk,kr->r", weight, np.exp(W)) if kappa is not None else prior,
            "particle_weights": weight.sum(axis=1)}
