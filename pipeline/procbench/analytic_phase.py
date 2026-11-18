"""Exact population functionals for V6's explicitly restricted one-phase case.

This is the same lognormal operation model, integrating its independent case
and common-case normal effects analytically. It is not a new hierarchy and does
not convert clocks, infer source reliability, or manufacture a sample size.
"""
import math

import numpy as np
from scipy.special import gammaln, log_ndtr, ndtri

from .cohort_histograms import _validate_counts, _validate_edges


def phase_quantile(log_location, log_scale, quantile):
    if not math.isfinite(log_location) or not math.isfinite(log_scale) or log_scale<=0:
        raise ValueError('Lognormal phase requires a finite location and positive scale')
    if not 0 <= quantile <= 1:
        raise ValueError('Invalid population quantile')
    if quantile == 0:
        return 0.
    if quantile == 1:
        return math.inf
    return float(np.exp(log_location + log_scale*ndtri(quantile)))


def phase_histogram_log_probability(counts, edges, log_location, log_scale):
    """Normalized multinomial using stable normal tail differences, not grid bins."""
    counts=np.asarray(_validate_counts(counts))
    edges=_validate_edges(edges)
    if len(edges)!=len(counts)+1:
        raise ValueError('Histogram edges and counts must align')
    if not math.isfinite(log_location) or not math.isfinite(log_scale) or log_scale<=0:
        raise ValueError('Lognormal phase requires a finite location and positive scale')
    z=[-math.inf]+[(math.log(x)-log_location)/log_scale for x in edges[1:-1]]+[math.inf]
    masses=[]
    for lo,hi in zip(z[:-1],z[1:]):
        # Use survival probabilities in the right tail, CDFs otherwise. This
        # retains tiny positive bin mass instead of rounding it to zero at 1.
        a,b=(log_ndtr(-lo),log_ndtr(-hi)) if lo>=0 else (log_ndtr(hi),log_ndtr(lo))
        masses.append(float(a+np.log(-np.expm1(b-a))) if b<a else -math.inf)
    positive=counts>0
    return float(gammaln(counts.sum()+1)-gammaln(counts+1).sum()
                 + counts[positive]@np.asarray(masses)[positive])


def validate_single_phase_program(program):
    """Fail closed outside the exact subcase; never silently approximate a sum."""
    if (program['inventory_granularity']!='aggregate_phases' or len(program['routes'])!=1
            or program['cases'] or program['rates'] or program['quantile_cohorts']):
        raise ValueError('Analytic single-phase integration requires one coarse inventory, population reports only, and no quantile/rate cohorts')
    route=program['routes'][0]
    if ('paths' in route or len(route['operations'])!=1 or len(route['blocks'])!=1
            or route['blocks'][0].repeat_key or route['blocks'][0].dwells):
        raise ValueError('Analytic single-phase integration forbids paths, multiple operations, repeats and dwells')
    operation=route['operations'][0]
    allowed_ends={'modeled_work_end','end_of_modeled_work'}
    if 'decision' in operation.markers:
        allowed_ends.update(('initial_decision','final_decision','last_decision'))
    for observation in program['observations']+program['histogram_cohorts']:
        for operator in observation['operators']:
            basis=operator['basis']
            if basis=='unmodeled_duration':
                continue
            if (basis=='single_visit_cycle' and operator.get('activity_ids')==[operation.id]):
                continue
            if (basis=='whole_case_clock' and operator['start']=='process_start'
                    and operator['end'] in allowed_ends):
                continue
            raise ValueError('Analytic single-phase integration requires a complete phase-duration operator')


def validate_collapsed_single_phase_program(program):
    """Fail closed around the sole case structure eligible for 1-D integration."""
    validate_single_phase_program(dict(program,cases=[]))
    if (program['rates'] or program['quantile_cohorts'] or program['histogram_cohorts']
            or program.get('positive_repeat_counts') or program.get('joint_duration_reports')
            or program.get('absent_event_censoring') or program.get('case_path_priors')):
        raise ValueError('Collapsed single-phase quadrature forbids rates, cohorts, repeats, structural and joint factors')
    operation=program['routes'][0]['operations'][0]
    eligible=[]
    for observation in program['observations']:
        if observation['case_id'] is None:
            continue
        weights=observation['operator_weights']
        if (observation['statistic']!='individual' or observation['sampling']!='unselected'
                or len(observation['operators'])!=1 or len(weights)!=1 or weights[0]!=1.):
            raise ValueError('Collapsed cases require one unselected individual report with one certain interpretation')
        operator=observation['operators'][0]
        allowed=(operator['basis']=='single_visit_cycle' and
                 operator.get('activity_ids')==[operation.id])
        allowed=allowed or (operator['basis']=='whole_case_clock' and
            operator['start']=='process_start' and operator['end'] in
            {'modeled_work_end','end_of_modeled_work','initial_decision','final_decision','last_decision'})
        if not allowed:
            raise ValueError('Collapsed cases require a complete one-phase elapsed clock')
        if observation.get('population_condition') or observation.get('first_visit'):
            raise ValueError('Collapsed cases forbid conditional or first-visit reports')
        eligible.append(observation['id'])
    if not eligible:
        raise ValueError('Collapsed single-phase quadrature requires an individual report')
    return eligible


def phase_spread_sensitive_factors(program):
    """Syntactic dependence on spread, not a claim of identification or calibration."""
    factors=[c['id'] for c in program['histogram_cohorts'] if len(c['bin_counts'])>1]
    for observation in program['observations']:
        if not any(op['basis']!='unmodeled_duration' for op in observation['operators']):
            continue
        statistic=observation['statistic']
        if (statistic in ('mean','p90') or (statistic=='typical_range' and
                any(q!=.5 for q in observation['typical_range_model']['quantiles']))):
            factors.append(observation['id'])
    return factors
