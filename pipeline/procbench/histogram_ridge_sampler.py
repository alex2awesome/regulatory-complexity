"""An opt-in transition for the existing analytic V6 histogram target.

No prior, likelihood, coordinate, observation or report is replaced. A coupled
spread/location move follows the first-bin CDF ridge, with the full prior and
Jacobian in its Metropolis correction. The ordinary transitions remain in use.
"""
from __future__ import annotations

import math

import numpy as np

from .bayes_trace_hierarchy import VisitHierarchy


class HistogramRidgeHierarchy(VisitHierarchy):
    """Guarded transition-only subclass; all scientific methods are inherited."""

    def __init__(self, data, cfg, *, ridge_step=.05):
        if (isinstance(ridge_step, bool) or not math.isfinite(ridge_step)
                or ridge_step <= 0):
            raise ValueError('Histogram ridge step must be finite and positive')
        super().__init__(data, cfg)
        if (cfg.population_integration != 'analytic_single_phase'
                or cfg.hierarchy_sampler != 'operation_centered'
                or tuple(cfg.modeled_channels) != ('elapsed',)
                or cfg.case_log_sd_prior <= 0 or cfg.common_case_sd != 0
                or cfg.source_sd != 0 or cfg.selection_sd != 0
                or self.source_offset_hierarchy is not None
                or self.conditional_case_frames):
            raise ValueError('Histogram ridge moves require analytic elapsed-only '
                'operation-centered histograms, free spread, and no common-case/source/selection effects')
        anchors = np.empty(len(self.operations))
        used = []
        for program in self.programs:
            if (program['observations'] or len(program['histogram_cohorts']) != 1
                    or len(program['global_indices']) != 1):
                raise ValueError('Histogram ridge moves require exactly one histogram and operation per program')
            edges = program['histogram_cohorts'][0]['bin_edges']
            if len(edges) < 3 or edges[1] is None or edges[1] <= 0:
                raise ValueError('Histogram ridge moves require a positive finite interior edge')
            index = int(program['global_indices'][0])
            used.append(index)
            anchors[index] = math.log(edges[1])
        if sorted(used) != list(range(len(self.operations))):
            raise ValueError('Histogram ridge moves require a distinct operation for each program')
        self.ridge_step = float(ridge_step)
        self.ridge_anchors = anchors
        self.ridge_baseline = (math.log(cfg.elapsed_prior_median)
                               + self.elapsed_task_prior_offsets)
        self.ridge_coordinates = self.hierarchy_coordinates[0]
        self.ridge_sigma_coordinate = int(self.sigma[0])
        self.ridge_regression = np.linalg.solve(
            self.design @ self.design.T, self.design).T
        self.ridge_attempts = 0
        self.ridge_accepts = 0

    def ridge_proposal(self, z, delta):
        """Return the reversible map T_delta and log|dT_delta/dz|.

        For sigma'=exp(delta)*sigma, set mu'=a+exp(delta)*(mu-a).
        Thus (a-mu')/sigma'=(a-mu)/sigma. The full-row-rank Gaussian
        hierarchy changes only in its row space; independent null directions
        are untouched. Its determinant is exp(n_operations*delta). The spread
        coordinate translates, so its Jacobian is one. T_-delta is the inverse.
        """
        z = np.asarray(z, dtype=float)
        if z.shape != (self.layout.size,) or not np.isfinite(z).all():
            raise ValueError('Histogram ridge state must have the original finite layout')
        if not math.isfinite(delta):
            raise ValueError('Histogram ridge increment must be finite')
        multiplier = math.expm1(delta)
        centered = self.design @ z[self.ridge_coordinates]
        change = multiplier * (self.ridge_baseline + centered - self.ridge_anchors)
        trial = z.copy()
        trial[self.ridge_coordinates] += self.ridge_regression @ change
        trial[self.ridge_sigma_coordinate] += delta / self.cfg.case_log_sd_prior
        return trial, len(self.operations) * delta

    def ridge_update(self, z, structures, current, rng):
        self.ridge_attempts += 1
        delta = float(rng.normal(scale=self.ridge_step))
        try:
            trial, log_jacobian = self.ridge_proposal(z, delta)
            if not np.isfinite(trial).all():
                return z, current, 0
            value = self.log_likelihood(trial, structures)
        except (OverflowError, FloatingPointError):
            return z, current, 0
        # Proposal density in delta is symmetric. Include the standard-normal
        # prior on ALL whitened coordinates and the non-volume-preserving map.
        log_ratio = value-current-.5*float(trial@trial-z@z)+log_jacobian
        if math.isfinite(value) and math.log(max(rng.random(), np.finfo(float).tiny)) < log_ratio:
            self.ridge_accepts += 1
            return trial, value, 1
        return z, current, 1

    def operation_centered_duration_update(self, z, structures, current, rng):
        z, current, calls = super().operation_centered_duration_update(
            z, structures, current, rng)
        z, current, used = self.ridge_update(z, structures, current, rng)
        return z, current, calls+used

    def transition_report(self):
        return dict(kind='v6-analytic-histogram-cdf-ridge/1',
            log_spread_step=self.ridge_step, steps_per_sweep=1,
            anchor_log_edges=self.ridge_anchors.tolist(),
            statistical_target_changed=False, adaptive=False,
            qualification='Extra target-preserving transition, not a new hierarchy or evidence/adequacy validation')
