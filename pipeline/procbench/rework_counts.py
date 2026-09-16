"""Normalized counts of additional rounds, distinct from per-visit retry rates.

A first-round correction probability and a continuation probability need not be
equal. These operators will be shared by route likelihoods and visit generation;
they do not infer actual behavior from normative inspection/step caps.
"""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class ReworkLaw:
    probability_any: float
    probability_continue: float

    def __post_init__(self):
        if (not math.isfinite(self.probability_any) or not 0 <= self.probability_any <= 1
                or not math.isfinite(self.probability_continue) or not 0 <= self.probability_continue < 1):
            raise ValueError('Rework probabilities require any in [0,1] and continuation in [0,1)')

    def probability(self, additional_rounds):
        if not isinstance(additional_rounds, (int, np.integer)) or additional_rounds < 0:
            raise ValueError('Additional rounds must be a nonnegative integer')
        q, r = self.probability_any, self.probability_continue
        return 1-q if additional_rounds == 0 else q*(1-r)*r**(additional_rounds-1)

    def at_least(self, additional_rounds):
        if not isinstance(additional_rounds, (int, np.integer)) or additional_rounds < 0:
            raise ValueError('Additional rounds must be a nonnegative integer')
        return 1. if additional_rounds == 0 else self.probability_any*self.probability_continue**(additional_rounds-1)

    def finite_bins(self, largest_exact_count):
        """Last bin is an explicit overflow category; no discarded/renormalized tail."""
        if not isinstance(largest_exact_count, int) or largest_exact_count < 0:
            raise ValueError('Largest exact count must be a nonnegative integer')
        return np.array([self.probability(k) for k in range(largest_exact_count+1)]
                        + [self.at_least(largest_exact_count+1)])

    def quantile(self, uniform):
        """Inverse CDF without a hidden maximum number of visits."""
        if not math.isfinite(uniform) or not 0 <= uniform < 1:
            raise ValueError('Uniform must be in [0,1)')
        q, r = self.probability_any, self.probability_continue
        if q == 0 or (q < 1 and uniform <= 1-q):
            return 0
        if r == 0:
            return 1
        return max(1, math.ceil((math.log1p(-uniform)-math.log(q))/math.log(r)))

    @property
    def mean_additional_rounds(self):
        return self.probability_any/(1-self.probability_continue)

    @property
    def variance_additional_rounds(self):
        q, r = self.probability_any, self.probability_continue
        return q*(1+r-q)/(1-r)**2

    @property
    def aggregate_correction_fraction_per_visit(self):
        """Population correction events / visits, not P(any correction per case)."""
        mean = self.mean_additional_rounds
        return mean/(1+mean)

    def selected_log_probability(self, additional_rounds, log_relative_posting_rate, threshold=1):
        """Bounded count-based selection, normalized over the entire count law.

        This is NOT automatically the normalization for a joint count-and-duration
        selection model when elapsed time depends on repeats. That joint model
        must compute its own joint normalizer, not multiply two marginal ones.
        """
        if not math.isfinite(log_relative_posting_rate) or log_relative_posting_rate < 0:
            raise ValueError('Posting tilt must be finite and nonnegative')
        if not isinstance(threshold, int) or threshold < 1:
            raise ValueError('Count-selection threshold must be a positive integer')
        mass = self.probability(additional_rounds)
        if mass == 0:
            return -math.inf
        tail = self.at_least(threshold)
        log_tail = math.log(tail) if tail > 0 else -math.inf
        log_rest = math.log1p(-tail) if tail < 1 else -math.inf
        normalizer = np.logaddexp(log_rest, log_relative_posting_rate+log_tail)
        return math.log(mass)+(log_relative_posting_rate if additional_rounds >= threshold else 0.)-normalizer
