"""Optional exact case-spread/residual interweave for the existing V6 target.

The one-dimensional ESS prior is the existing N(0,1) spread coordinate prior.
Its callback includes the transformed residual prior, full Jacobian, and full
likelihood.  No coordinate, prior, observation, or likelihood is added.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np

from .latent_gaussian import elliptical_slice


CHANNEL_NAMES = ('elapsed', 'payer_hours', 'agency_hours')


def channel_case_coordinates(model, channel):
    if isinstance(channel, bool) or not isinstance(channel, (int, np.integer)):
        raise ValueError('Case-scale channel must be an integer channel index')
    channel = int(channel)
    active = tuple(int(ch) for ch in model.active_channels)
    if channel not in active:
        raise ValueError('Case-scale interweave requires an active channel')
    sigma_coordinate = int(model.sigma[channel])
    if sigma_coordinate < 0:
        raise ValueError('Active channel has no spread coordinate')
    position = active.index(channel)
    residuals, common = [], []
    for program in model.programs:
        n = len(program['global_indices'])
        coordinates = np.asarray(program['case_coordinates'])
        if coordinates.ndim != 2:
            raise ValueError('Case-coordinate layout must be a matrix')
        start, stop = position*(n+1), position*(n+1)+n
        if coordinates.shape[1] < stop+1:
            raise ValueError('Case-coordinate layout is shorter than its channel block')
        residuals.extend(int(i) for i in coordinates[:, start:stop].reshape(-1))
        common.extend(int(i) for i in coordinates[:, stop].reshape(-1))
    residuals, common = np.asarray(residuals, dtype=int), np.asarray(common, dtype=int)
    if (len(set(map(int, residuals))) != len(residuals)
            or set(map(int, residuals)) & set(map(int, common))
            or sigma_coordinate in set(map(int, residuals)) | set(map(int, common))):
        raise ValueError('Case-scale coordinate blocks must be disjoint')
    return SimpleNamespace(channel=channel, sigma_coordinate=sigma_coordinate,
        residual_coordinates=residuals, common_case_coordinates=common,
        dimension=len(residuals))


def case_scale_proposal(model, state, channel, proposed_scale_coordinate):
    state = np.asarray(state, dtype=float)
    if state.shape != (model.layout.size,) or not np.isfinite(state).all():
        raise ValueError('Case-scale proposal requires the original finite state layout')
    if (isinstance(proposed_scale_coordinate, bool)
            or not isinstance(proposed_scale_coordinate, (int, float, np.integer, np.floating))
            or not math.isfinite(proposed_scale_coordinate)):
        raise ValueError('Proposed case-scale coordinate must be finite')
    prior_width = model.cfg.case_log_sd_prior
    if isinstance(prior_width, bool) or not isinstance(prior_width, (int, float)):
        raise ValueError('case_log_sd_prior must be numeric')
    if prior_width == 0:
        return None
    if not math.isfinite(prior_width) or prior_width < 0:
        raise ValueError('case_log_sd_prior must be finite and nonnegative')
    layout = channel_case_coordinates(model, channel)
    old_scale_coordinate = float(state[layout.sigma_coordinate])
    log_scale = prior_width*(old_scale_coordinate-float(proposed_scale_coordinate))
    try:
        scale = math.exp(log_scale)
    except OverflowError:
        return None
    if not math.isfinite(scale) or scale == 0:
        return None
    proposal = state.copy()
    proposal[layout.sigma_coordinate] = float(proposed_scale_coordinate)
    with np.errstate(over='ignore', invalid='ignore'):
        proposal[layout.residual_coordinates] *= scale
    if not np.isfinite(proposal).all():
        return None
    return dict(state=proposal, channel=layout.channel,
        sigma_coordinate=layout.sigma_coordinate,
        residual_coordinates=layout.residual_coordinates.copy(),
        common_case_coordinates=layout.common_case_coordinates.copy(),
        dimension=layout.dimension, log_scale=log_scale, scale=scale,
        log_jacobian=layout.dimension*log_scale)


def anchored_log_target(model, original, structures, current, channel,
                        proposed_scale_coordinate):
    proposal = case_scale_proposal(model, original, channel, proposed_scale_coordinate)
    if proposal is None:
        return -math.inf
    if proposed_scale_coordinate == original[proposal['sigma_coordinate']]:
        return float(current)
    try:
        likelihood = model.log_likelihood(proposal['state'], structures)
    except (FloatingPointError, OverflowError):
        return -math.inf
    if not math.isfinite(likelihood):
        return -math.inf
    indices = proposal['residual_coordinates']
    with np.errstate(over='ignore', invalid='ignore'):
        old_square = float(np.dot(original[indices], original[indices]))
        new_square = float(np.dot(proposal['state'][indices], proposal['state'][indices]))
        value = likelihood-.5*(new_square-old_square)+proposal['log_jacobian']
    return float(value) if math.isfinite(value) else -math.inf


def case_scale_interweave_update(model, state, structures, current, rng):
    state = np.asarray(state, dtype=float)
    if state.shape != (model.layout.size,) or not np.isfinite(state).all():
        raise ValueError('Case-scale update requires the original finite state layout')
    if not math.isfinite(current):
        raise ValueError('Case-scale update requires a finite current full likelihood')
    if model.cfg.case_log_sd_prior == 0:
        return state, current, 0
    calls = 0
    for channel in model.active_channels:
        layout = channel_case_coordinates(model, channel)
        original = state
        anchor = np.array([original[layout.sigma_coordinate]], dtype=float)

        def callback(one_coordinate):
            return anchored_log_target(model, original, structures, current,
                channel, float(one_coordinate[0]))

        draw, _, used = elliptical_slice(anchor, np.array([0]), callback, current, rng)
        proposal = case_scale_proposal(model, original, channel, float(draw[0]))
        if proposal is None:
            raise RuntimeError('ESS accepted a numerically invalid case-scale proposal')
        refreshed = model.log_likelihood(proposal['state'], structures)
        if not math.isfinite(refreshed):
            raise RuntimeError('ESS accepted a nonfinite ordinary likelihood')
        state, current = proposal['state'], float(refreshed)
        calls += used+1
    return state, current, calls


def transition_report(model):
    enabled = model.cfg.case_scale_sampler == 'interwoven'
    fixed_spread = model.cfg.case_log_sd_prior == 0
    return dict(schema_version='v6-case-scale-residual-interweave/1',
        enabled=enabled,
        active_channels=[CHANNEL_NAMES[ch] for ch in model.active_channels],
        steps_per_sweep=(len(model.active_channels) if enabled and not fixed_spread else 0),
        no_op_reason=('case_log_sd_prior_is_zero' if enabled and fixed_spread else None),
        transformed_coordinates='all per-case operation residuals for each active channel',
        excluded_coordinates=['common_case','hierarchy','phase','dwell','repeat','path','selection','source'],
        target_changed=False, adaptive=False,
        qualification=('Exact ESS scale/residual reparameterization with complete likelihood, residual-prior '
            'and Jacobian correction; not a new prior, observation, model, or convergence claim.'))
