"""Small joint Bayesian timing/rework component for controlled recovery tests.

T = fixed_other_days + (1+R)*X, log X ~ Normal(mu_agency_task, known_sigma).
R has separate any-correction and continuation probabilities. A case shares X
across its review visits: this is an explicit simplifying correlation assumption.
Independent first-visit task data share mu; actual independent cohort counts
inform the any-correction probability. No informal 'x in ten' becomes n=10 here.

This is not the full text/agency hierarchy. Known spread, continuation probability,
fixed other work, complete clocks and unselected independent samples make it a
deliberately favorable check of joint information propagation.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.special import logsumexp

from .phase_mixture import quantile_density


@dataclass(frozen=True)
class Config:
    fixed_other_days: float = 8.
    case_log_sd: float = .45
    probability_continue: float = .35
    prior_task_median: float = 5.
    prior_mu_sd: float = 1.5
    location_points: int = 801
    probability_points: int = 201
    max_additional_rounds: int = 64


def weighted_summary(values, weights):
    values, weights = np.ravel(values), np.ravel(weights)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    keep = weights > 0
    values, weights = values[keep], weights[keep]
    weights = weights/weights.sum()
    cdf = np.cumsum(weights)-.5*weights
    lo, med, hi = np.interp([.05, .5, .95], cdf, values)
    return dict(median=float(med), mean=float(values @ weights), ci90=[float(lo), float(hi)])


def fit_repeat_timing(total_days, task_cycle_days=(), independent_rework_cohort=None, cfg=Config()):
    if (cfg.fixed_other_days < 0 or not 0 <= cfg.probability_continue < 1
            or min(cfg.case_log_sd, cfg.prior_task_median, cfg.prior_mu_sd) <= 0
            or min(cfg.location_points, cfg.probability_points) < 16 or cfg.max_additional_rounds < 1):
        raise ValueError('Invalid controlled-model configuration')
    tail = cfg.probability_continue**cfg.max_additional_rounds
    if tail > 1e-12:
        raise ValueError('Repeat-count tail too large; increase numerical count resolution')
    total, task = np.asarray(total_days, dtype=float), np.asarray(task_cycle_days, dtype=float)
    if (not np.isfinite(total).all() or not np.isfinite(task).all()
            or np.any(total <= cfg.fixed_other_days) or np.any(task <= 0)):
        raise ValueError('Observed durations must exceed their fixed offset and be finite')
    if independent_rework_cohort is not None:
        k, n = independent_rework_cohort
        if not all(isinstance(x, (int, np.integer)) for x in (k, n)) or n < 1 or not 0 <= k <= n:
            raise ValueError('A genuinely counted independent cohort requires valid integer successes/trials')
    center = math.log(cfg.prior_task_median)
    # A fixed seven-prior-SD domain; probability grid uses cell midpoints.
    mu = np.linspace(center-7*cfg.prior_mu_sd, center+7*cfg.prior_mu_sd, cfg.location_points)
    q = (np.arange(cfg.probability_points)+.5)/cfg.probability_points
    logq, lognotq = np.log(q), np.log1p(-q)
    logpost = np.broadcast_to(-.5*((mu-center)/cfg.prior_mu_sd)**2,
                              (len(q), len(mu))).T.copy()
    rounds = np.arange(1, cfg.max_additional_rounds+1)
    if cfg.probability_continue == 0:
        positive_logmass = np.full(len(rounds), -np.inf)
        positive_logmass[0] = 0.
    else:
        positive_logmass = math.log1p(-cfg.probability_continue)+(rounds-1)*math.log(cfg.probability_continue)
    sigma = cfg.case_log_sd
    for observed in np.log(total-cfg.fixed_other_days):
        first = -.5*((observed-mu)/sigma)**2
        positive = logsumexp(positive_logmass[:, None]
            -.5*((observed-np.log1p(rounds)[:, None]-mu[None, :])/sigma)**2, axis=0)
        # The Jacobian and normal-density constants are independent of mu/q.
        # No truncated count tail is renormalized or assigned to a maximum count.
        logpost += np.logaddexp(first[:, None]+lognotq[None, :], positive[:, None]+logq[None, :])
    if len(task):
        logpost += np.sum(-.5*((np.log(task)[:, None]-mu[None, :])/sigma)**2, axis=0)[:, None]
    if independent_rework_cohort is not None:
        k, n = independent_rework_cohort
        logpost += k*logq[None, :]+(n-k)*lognotq[None, :]
    mass = np.exp(logpost-logsumexp(logpost))
    mu_mass, q_mass = mass.sum(axis=1), mass.sum(axis=0)
    agency_mean = np.exp(mu+.5*sigma*sigma)
    expected_visits = 4+q/(1-cfg.probability_continue)
    log_cycle_locations = np.log1p(np.arange(cfg.max_additional_rounds+1))
    log_process_component = []
    for probability in q:
        probabilities = np.r_[1-probability, probability*np.exp(positive_logmass)]
        # The omitted probability is <1e-12; retain it as a diagnostic rather
        # than silently rescale the likelihood into a bounded-repeat model.
        value, _ = quantile_density(.5, log_cycle_locations, probabilities, sigma)
        log_process_component.append(value)
    process = cfg.fixed_other_days+np.exp(mu[:, None]+np.asarray(log_process_component)[None, :])
    mean_mu, mean_q = mu @ mu_mass, q @ q_mass
    covariance = np.sum(mass*(mu-mean_mu)[:, None]*(q-mean_q)[None, :])
    denominator = math.sqrt(np.sum(mu_mass*(mu-mean_mu)**2)*np.sum(q_mass*(q-mean_q)**2))
    return dict(location_grid=mu, probability_grid=q, posterior_mass=mass,
        agency_mean_cycle_days=weighted_summary(agency_mean, mu_mass),
        any_correction_probability=weighted_summary(q, q_mass),
        expected_visit_count=weighted_summary(expected_visits, q_mass),
        population_process_median_days=weighted_summary(process, mass),
        posterior_location_rework_correlation=float(covariance/denominator),
        numerical=dict(conditional_repeat_tail_omitted=tail,
                       normal_prior_mass_outside_location_grid=2*float(.5*math.erfc(7/math.sqrt(2)))))


def refinement_check(base, finer):
    discrepancies = {}
    for label, axis in [('location', 0), ('probability', 1)]:
        grid = base[label+'_grid']
        finer_grid = finer[label+'_grid']
        mass = base['posterior_mass'].sum(axis=1-axis)
        finer_mass = finer['posterior_mass'].sum(axis=1-axis)
        cumulative = np.cumsum(mass)-.5*mass
        finer_cumulative = np.cumsum(finer_mass)-.5*finer_mass
        discrepancies[label+'_max_cdf_difference'] = float(np.max(np.abs(
            cumulative-np.interp(grid, finer_grid, finer_cumulative))))
    discrepancies['acceptable'] = max(discrepancies.values()) < .005
    return discrepancies
