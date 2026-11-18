"""Opt-in Gaussian hierarchy for occupancy-source detection probabilities.

For each source type k and reviewed step s,

    logit(p[s,k]) = log(a[k] / b[k]) + mu[k] + delta[s,k]

with mu[k] ~ N(0, type_logit_sd**2) and independent
delta[s,k] ~ N(0, step_logit_sd**2).  The implementation integrates ``mu``
in the prior, so one S-dimensional standard-normal vector per source type is
mapped through the exact compound-symmetry covariance.  The Beta shapes from
the evidence contract supply the logit center only; this is not a Beta prior
reparameterization and has no Beta Jacobian.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import expit


MODES = {"independent_beta", "logit_partial_pooling"}


def validate_config(mode, type_logit_sd, step_logit_sd):
    if mode not in MODES:
        raise ValueError("detection_model must be independent_beta or logit_partial_pooling")
    for name, value in (("detection_type_logit_sd", type_logit_sd),
                        ("detection_step_logit_sd", step_logit_sd)):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0):
            raise ValueError(f"{name} must be finite and strictly positive")


class DetectionHierarchy:
    """Exact prior transform and conditional likelihood for one fixed scope."""

    def __init__(self, alpha, beta, type_logit_sd, step_logit_sd):
        a, b = np.asarray(alpha, dtype=float), np.asarray(beta, dtype=float)
        if (a.ndim != 2 or a.shape != b.shape or not a.size
                or not np.isfinite(a).all() or not np.isfinite(b).all()
                or np.any(a <= 0) or np.any(b <= 0)):
            raise ValueError("Detection centers require finite positive matching Beta-shape arrays")
        # Evidence currently declares one Beta pair per source type.  Refuse a
        # future step-varying declaration rather than silently choosing a row.
        if not (np.all(a == a[:1]) and np.all(b == b[:1])):
            raise ValueError("Partial pooling requires one declared center per source type")
        validate_config("logit_partial_pooling", type_logit_sd, step_logit_sd)
        self.steps, self.source_types = a.shape
        self.type_logit_sd = float(type_logit_sd)
        self.step_logit_sd = float(step_logit_sd)
        self.center = np.log(a[0] / b[0])
        covariance = (self.type_logit_sd ** 2 * np.ones((self.steps, self.steps))
                      + self.step_logit_sd ** 2 * np.eye(self.steps))
        self.covariance = covariance
        self.cholesky = np.linalg.cholesky(covariance)
        self.type_effect_conditional_variance = float(
            1 / (1 / self.type_logit_sd**2 + self.steps / self.step_logit_sd**2))

    @property
    def dimension(self):
        return self.steps * self.source_types

    def logits(self, white):
        w = np.asarray(white, dtype=float)
        if (w.shape != (self.steps, self.source_types)
                or not np.isfinite(w).all()):
            raise ValueError("Detection white state has the wrong shape or nonfinite values")
        return self.center[None, :] + self.cholesky @ w

    def probabilities(self, white):
        p = expit(self.logits(white))
        # expit may round an otherwise finite extreme logit to exactly 0/1;
        # downstream Bernoulli conditionals require an interior probability.
        if not np.isfinite(p).all() or np.any(p <= 0) or np.any(p >= 1):
            raise FloatingPointError("Detection logits exceed the finite interior-probability domain")
        return p

    def source_log_likelihood(self, white, source_index, successes, failures):
        if (type(source_index) is not int or not 0 <= source_index < self.source_types):
            raise ValueError("Unknown detection source index")
        n1, n0 = np.asarray(successes), np.asarray(failures)
        if (n1.shape != (self.steps,) or n0.shape != (self.steps,)
                or not np.issubdtype(n1.dtype, np.integer)
                or not np.issubdtype(n0.dtype, np.integer)
                or np.any(n1 < 0) or np.any(n0 < 0)):
            raise ValueError("Detection sufficient statistics must be nonnegative integer step counts")
        eta = self.logits(white)[:, source_index]
        # Stable Bernoulli log likelihood without forming probabilities.  A
        # step with no reviewed opportunity contributes exactly zero.
        return float(np.sum(-n1 * np.logaddexp(0., -eta)
                            - n0 * np.logaddexp(0., eta)))

    def conditional_type_effect(self, logits):
        """Analytic N(mu | the supplied full source logit vectors).

        This is a conditional decomposition of the integrated Gaussian prior,
        useful for reporting.  It is not an additional sampled coordinate.
        """
        eta = np.asarray(logits, dtype=float)
        if (eta.shape != (self.steps, self.source_types)
                or not np.isfinite(eta).all()):
            raise ValueError("Detection logits have the wrong shape or nonfinite values")
        centered = eta - self.center[None, :]
        mean = (self.type_logit_sd**2
                / (self.step_logit_sd**2 + self.steps*self.type_logit_sd**2)
                * centered.sum(axis=0))
        return mean, self.type_effect_conditional_variance

