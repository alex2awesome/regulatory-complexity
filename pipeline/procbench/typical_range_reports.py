"""Explicit subjective-quantile interpretation of a typical-duration range.

The quoted bounds censor one noisy report of a population quantile Q(q).
The unknown q has a declared finite prior, integrated once per report. Bounds
are NOT two quantiles, a confidence interval, or a finite-sample statistic.
This is an opt-in reporting assumption requiring calibration/sensitivity, not
an assertion that every use of "usually" has these semantics.
"""
import math

import numpy as np
from scipy.special import logsumexp

from .compact_visit_trace import population_quantile


def validate_typical_range_model(model):
    required = {'kind', 'quantiles', 'weights', 'report_log_scale', 'description'}
    if not isinstance(model, dict) or set(model) != required:
        raise ValueError('Typical ranges require an explicit reporting model')
    if model['kind'] != 'interval_censored_subjective_quantile':
        raise ValueError('Unsupported typical-range reporting model')
    if not isinstance(model['description'], str) or not model['description'].strip():
        raise ValueError('Describe the typical-range interpretation assumption')
    quantiles, weights = model['quantiles'], model['weights']
    if (not isinstance(quantiles, list) or not quantiles or
            not isinstance(weights, list) or len(weights) != len(quantiles)):
        raise ValueError('Typical quantiles and weights must be nonempty matching lists')
    for values in (quantiles, weights):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
               not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError('Typical quantiles and weights must be finite and positive')
    if (any(q >= 1 for q in quantiles) or
            any(a >= b for a, b in zip(quantiles, quantiles[1:]))):
        raise ValueError('Typical quantiles must increase strictly within (0, 1)')
    if not math.isclose(sum(weights), 1., rel_tol=0., abs_tol=1e-12):
        raise ValueError('Typical quantile weights must sum to one')
    # Scale parameter of the df=4 Student-t report kernel.  It is not that
    # distribution's standard deviation (and contamination changes the complete
    # mixture's spread again), so the contract deliberately does not call it SD.
    scale = model['report_log_scale']
    if (isinstance(scale, bool) or not isinstance(scale, (int, float)) or
            not math.isfinite(scale) or scale <= 0):
        raise ValueError('Typical reporting uncertainty must be finite and positive')
    return model


def validate_typical_range_observation(observation):
    if observation['statistic'] != 'typical_range':
        if 'typical_range_model' in observation:
            raise ValueError('Typical-range metadata cannot modify another statistic')
        return
    validate_typical_range_model(observation.get('typical_range_model'))
    if observation['case_id'] is not None or observation.get('sample_size') is not None:
        raise ValueError('Typical ranges are subjective population reports, not individual or finite-cohort reports')
    lo, hi = observation['lower'], observation['upper']
    if (isinstance(lo, bool) or not isinstance(lo, (int, float)) or
            isinstance(hi, bool) or not isinstance(hi, (int, float)) or
            not math.isfinite(lo) or not math.isfinite(hi) or not 0 <= lo < hi):
        raise ValueError('Typical ranges need two finite ordered nonnegative bounds')
    if 'report_intervals' in observation:
        raise ValueError('Disjunctive typical ranges require a separate reporting contract')


def typical_range_log_probability(observation, population, values, offset,
                                  contamination, interval_kernel):
    """Integrate the declared subjective quantile, preserving path weights."""
    model = observation['typical_range_model']
    locations = np.asarray([population_quantile(population, values, q)
                            for q in model['quantiles']])
    terms = interval_kernel(observation, locations, offset,
                            model['report_log_scale'], contamination)
    return float(logsumexp(np.log(model['weights']) + terms))
