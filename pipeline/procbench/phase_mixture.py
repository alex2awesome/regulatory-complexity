"""Population functionals for clock fractions times lognormal-mixture durations.

A population median after a random clock subtraction is not the original median
times the median remaining fraction. This small kernel evaluates the convolution.
"""
import math

import numpy as np

from .measurement_kernel import njit


def quantile_density_loop(probability, locations, weights, sigma):
    lower = np.min(locations) - 12 * sigma
    upper = np.max(locations) + 12 * sigma
    for _ in range(55):
        middle = (lower + upper) / 2
        cumulative = 0.
        for i in range(len(locations)):
            cumulative += weights[i] * .5 * math.erfc((locations[i] - middle) / (sigma * math.sqrt(2)))
        if cumulative < probability:
            lower = middle
        else:
            upper = middle
    quantile = (lower + upper) / 2
    density = 0.
    for i in range(len(locations)):
        distance = (quantile - locations[i]) / sigma
        density += weights[i] * math.exp(-distance * distance / 2) / (sigma * math.sqrt(2 * math.pi))
    return quantile, density


quantile_density_native = njit(cache=True)(quantile_density_loop) if njit is not None else None


def quantile_density(probability, locations, weights, sigma, native=True):
    locations, weights = np.asarray(locations, dtype=float), np.asarray(weights, dtype=float)
    if (not 0 < probability < 1 or not math.isfinite(sigma) or sigma <= 0
            or locations.ndim != 1 or locations.shape != weights.shape or not len(locations)
            or not np.isfinite(locations).all() or not np.isfinite(weights).all()
            or np.any(weights < 0) or not np.isclose(weights.sum(), 1., atol=1e-12, rtol=0)):
        raise ValueError('A quantile needs a normalized finite normal mixture and positive spread')
    kernel = quantile_density_native if native and quantile_density_native is not None else quantile_density_loop
    return kernel(probability, locations, weights, sigma)
