"""Proper central-interval scores, shared by current and historical evaluators.

Callers choose the estimand and scale. In particular, a log-duration score is not
interchangeable with a score in days, and a median interval is not a case interval.
"""
import math


def interval_score(lower, upper, actual, *, alpha=.1):
    """Gneiting–Raftery central (1-alpha) interval score; smaller is better."""
    if not all(math.isfinite(v) for v in (lower, upper, actual, alpha)):
        raise ValueError('Interval score requires finite values')
    if lower > upper or not 0 < alpha < 1:
        raise ValueError('Ordered bounds and 0 < alpha < 1 are required')
    return float(upper - lower + (2 / alpha) *
                 (max(lower - actual, 0.) + max(actual - upper, 0.)))


def log_interval_score(lower, upper, actual, *, alpha=.1):
    """Score positive durations on their natural-log scale."""
    if not all(math.isfinite(v) and v > 0 for v in (lower, upper, actual)):
        raise ValueError('Log timing scores require finite positive durations')
    return interval_score(*map(math.log, (lower, upper, actual)), alpha=alpha)


def absolute_log_error(estimate, actual):
    if not all(math.isfinite(v) and v > 0 for v in (estimate, actual)):
        raise ValueError('Log timing scores require finite positive durations')
    return abs(math.log(estimate) - math.log(actual))
