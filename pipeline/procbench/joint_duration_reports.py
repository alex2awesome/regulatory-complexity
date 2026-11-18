"""Declared shared-log-error groups, not independent sentences from one case.

One log-scale reporting error multiplies every duration in a group. Intersect
its admissible intervals and integrate once. This is a strong sensitivity model:
relative timings have only the declared rounding/coarsening uncertainty, not
independent recall error. It is neither learned dependence nor semantic review.
"""
from copy import deepcopy
import hashlib
import json
import math

import numpy as np

from .bayes_hierarchy import log_interval
from .source_precision import precision_annotation


SCHEMA_VERSION = 'shared-log-error-report-group/1'
FIELDS = {'schema_version', 'id', 'case_id', 'observation_ids',
          'likelihood_kind', 'assumption', 'declaration_sha256'}
BASES = {'whole_case_clock', 'single_visit_cycle', 'sum_visit_cycles',
         'first_to_last_activity_span', 'wait_elapsed', 'service_elapsed',
         'activity_event_clock', 'activity_event_interval'}


def declaration_digest(program_id, declaration, observations):
    """Bind the complete member observations and program, not just their IDs."""
    names = declaration['observation_ids']
    by_id = {o['id']: o for o in observations}
    payload = dict(program_id=program_id,
        declaration={k: v for k, v in declaration.items() if k != 'declaration_sha256'},
        observations=[by_id[name] for name in names])
    try:
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError) as exc:
        raise ValueError('Joint-report declarations must be finite canonical JSON') from exc
    return hashlib.sha256(raw).hexdigest()


def _text(value, field):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError('Joint-report groups require canonical nonempty ' + field)


def validate_joint_duration_reports(raw, program):
    if not isinstance(raw, list):
        raise ValueError('joint_duration_reports must be a list')
    result, seen, used = [], set(), set()
    by_id = {o['id']: o for o in program['observations']}
    for group in raw:
        if not isinstance(group, dict) or set(group) != FIELDS:
            raise ValueError('Joint-report group requires exact version-1 fields')
        if (group['schema_version'] != SCHEMA_VERSION or
                group['likelihood_kind'] != 'shared_log_scale_t4'):
            raise ValueError('Unsupported joint-report schema or likelihood')
        _text(group['id'], 'id')
        _text(group['case_id'], 'case_id')
        if group['id'] in seen:
            raise ValueError('Joint-report group IDs must be distinct')
        seen.add(group['id'])
        assumption = group['assumption']
        if (not isinstance(assumption, dict) or set(assumption) !=
                {'kind', 'relative_timings_exact_within_bounds', 'sensitivity_only', 'rationale'}
                or assumption['kind'] != 'perfectly_shared_log_error'
                or assumption['relative_timings_exact_within_bounds'] is not True
                or assumption['sensitivity_only'] is not True):
            raise ValueError('Explicit shared-error sensitivity and relative-timing assumptions required')
        _text(assumption['rationale'], 'assumption rationale')
        names = group['observation_ids']
        if (not isinstance(names, list) or len(names) < 2 or
                any(not isinstance(name, str) or name not in by_id for name in names)
                or len(names) != len(set(names)) or used.intersection(names)):
            raise ValueError('Joint groups require distinct known members with no overlapping membership')
        members = [by_id[name] for name in names]
        if any(o['case_id'] != group['case_id'] or o['statistic'] != 'individual'
               for o in members):
            raise ValueError('Joint duration reports must belong to one individual case')
        if len({(o['source_family'], o['sampling']) for o in members}) != 1:
            raise ValueError('Joint duration reports must share source and ascertainment')
        for o in members:
            for name in ('lower', 'upper'):
                bound = o[name]
                if name == 'upper' and bound is None:
                    continue
                if (isinstance(bound, bool) or not isinstance(bound, (int, float))
                        or not math.isfinite(bound) or bound < 0):
                    raise ValueError('Joint report bounds must be nonboolean finite nonnegative numbers')
            weights = o['operator_weights']
            if (len(o['operators']) != 1 or o['operator_weights'] != [1.]
                    or any(isinstance(w, bool) or not isinstance(w, (int, float)) for w in weights)
                    or o['operators'][0]['basis'] not in BASES
                    or 'report_intervals' in o or precision_annotation(o) is not None):
                raise ValueError('Joint reports v1 require one elapsed operator and interval, with the common configured scale')
        if group['declaration_sha256'] != declaration_digest(program['id'], group, program['observations']):
            raise ValueError('Joint-report digest does not match member evidence and context')
        used.update(names)
        result.append(dict(declaration=deepcopy(group), members=deepcopy(members),
                           columns=[program['observations'].index(o) for o in members]))
    return result


def shared_log_error_probability(lower, upper, values, offset=0., scale=.25, contamination=.05):
    """One log probability for a vector of coarsened positive durations.

    Reported duration j = values[j] * exp(error), with ONE Student-t(4) error
    and ONE broad-component indicator per group. Empty intersections have
    exactly zero support, including when the contamination component is on.
    Zero latent durations remain zero; a multiplicative error cannot move them.
    """
    lo, hi, values = (np.asarray(x, dtype=float) for x in (lower, upper, values))
    if (lo.ndim != 1 or lo.size == 0 or lo.shape != hi.shape or lo.shape != values.shape
            or not np.isfinite(lo).all() or np.any(lo < 0)
            or np.isnan(hi).any() or np.any(hi <= lo)
            or not np.isfinite(values).all() or np.any(values < 0)
            or not math.isfinite(offset) or not math.isfinite(scale) or scale <= 0
            or not math.isfinite(contamination) or not 0 <= contamination < 1):
        raise ValueError('Invalid joint-duration values, intervals, or reporting parameters')
    zero = values == 0
    if np.any(zero & (lo > 0)):
        return -math.inf
    positive = ~zero
    if not positive.any():
        return 0.
    ll = np.full(lo.shape, -math.inf)
    np.log(lo, out=ll, where=lo > 0)
    log_values = np.log(values[positive])
    left = float(np.max(ll[positive] - log_values))
    right = float(np.min(np.log(hi[positive]) - log_values))
    if right <= left:
        return -math.inf
    regular = float(log_interval(left, right, offset, scale))
    if not contamination:
        return regular
    return float(np.logaddexp(math.log1p(-contamination) + regular,
        math.log(contamination) + log_interval(left, right, offset, 2.)))
