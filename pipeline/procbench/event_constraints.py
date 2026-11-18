"""Propagate source-reviewed event bounds without creating new observations.

Each input constrains ``lower <= t[end] - t[start] <= upper``. None means
unbounded. Ordering must be supplied explicitly; disconnected events stay
unrelated. This deterministic compiler neither fits a distribution nor assigns
actors, verifies source interpretations, or makes report errors independent.
"""
from __future__ import annotations

import math
from fractions import Fraction
from numbers import Real


class InconsistentEventConstraints(ValueError):
    """A negative cycle witnesses mutually incompatible supplied bounds."""

    def __init__(self, event, support, gap):
        self.event = event
        self.support = list(dict.fromkeys(support))
        self.exact_gap = str(gap)
        try:
            self.gap = float(gap)
        except OverflowError:
            self.gap = None
        if self.gap is not None and not math.isfinite(self.gap):
            self.gap = None
        super().__init__(f'Inconsistent event bounds at {event}: '
                         f'cycle upper bound {gap}; support={self.support}')


def _name(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'Event constraints require a canonical nonempty {label}')
    return value


def _bound(value, label):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{label} must be a finite real number or null')
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f'{label} must fit a finite floating-point number') from exc
    if not finite:
        raise ValueError(f'{label} must be a finite real number or null')
    # Source JSON decimals, not binary machine-rounding residuals, define the
    # constraints. Keep exact arithmetic until emitting the JSON-facing bounds.
    return Fraction(str(value))


def _output_bound(value):
    if value is None:
        return None
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError('Derived event bound exceeds finite output range') from exc
    if not math.isfinite(result):
        raise ValueError('Derived event bound exceeds finite output range')
    return result


def propagate_event_bounds(events, constraints, *, tolerance=0.):
    """Return tight difference bounds and explicit input-edge witnesses.

    This is all-pairs shortest-path closure of a difference-bound matrix, not
    probabilistic inference. With continuous event times, no additional priors
    or ordering, its bounds are the extrema allowed by the supplied constraints.
    They inherit all source/rounding assumptions. Derived bounds may be useful
    summaries or consistency checks, NEVER additional likelihood factors beside
    their parent constraints. Open bounds are represented by infima/suprema.

    Closure uses exact rational arithmetic on the decimal representations of
    supplied numbers. Nonzero tolerances are rejected: accepting a negative
    cycle cannot certify feasible bounds. No event is pinned to time zero.
    """
    if tolerance is None or _bound(tolerance, 'Event-bound tolerance') != 0:
        raise ValueError('Event-bound tolerance must be zero; closure is exact')
    if not isinstance(events, (list, tuple)) or not events:
        raise ValueError('Declare a nonempty list of event IDs')
    events = [_name(event, 'event ID') for event in events]
    if len(events) != len(set(events)):
        raise ValueError('Event IDs must be distinct')
    if not isinstance(constraints, (list, tuple)):
        raise ValueError('Event constraints must be a list')
    index = {event: i for i, event in enumerate(events)}
    n = len(events)
    distance = [[Fraction(0) if i == j else None for j in range(n)] for i in range(n)]
    paths = [[[] for _ in range(n)] for _ in range(n)]
    identifiers, groups = [], set()

    def edge(i, j, upper, support):
        if distance[i][j] is None or upper < distance[i][j]:
            distance[i][j] = upper
            paths[i][j] = [support]

    for row in constraints:
        if not isinstance(row, dict) or not {'id', 'start', 'end', 'lower', 'upper'} <= row.keys():
            raise ValueError('Each constraint needs id, start, end, lower and upper')
        ident = _name(row['id'], 'constraint ID')
        if ident in identifiers:
            raise ValueError('Constraint IDs must be distinct')
        identifiers.append(ident)
        start, end = _name(row['start'], 'start'), _name(row['end'], 'end')
        if start not in index or end not in index:
            raise ValueError('Every bound endpoint must be a declared event')
        lo, hi = _bound(row['lower'], 'Lower bound'), _bound(row['upper'], 'Upper bound')
        if lo is None and hi is None:
            raise ValueError('A constraint must supply at least one finite bound')
        if lo is not None and hi is not None and lo > hi:
            raise ValueError('Lower event bound exceeds upper bound')
        if row.get('report_group_id') is not None:
            groups.add(_name(row['report_group_id'], 'report-group ID'))
        i, j = index[start], index[end]
        if hi is not None:
            edge(i, j, hi, ident + ':upper')
        if lo is not None:
            edge(j, i, -lo, ident + ':lower')

    def check_cycles():
        for i, event in enumerate(events):
            if distance[i][i] < 0:
                raise InconsistentEventConstraints(event, paths[i][i], distance[i][i])

    check_cycles()
    for k in range(n):
        for i in range(n):
            if distance[i][k] is None:
                continue
            for j in range(n):
                if distance[k][j] is None:
                    continue
                candidate = distance[i][k] + distance[k][j]
                if distance[i][j] is None or candidate < distance[i][j]:
                    distance[i][j] = candidate
                    paths[i][j] = paths[i][k] + paths[k][j]
        check_cycles()

    bounds = []
    for i, start in enumerate(events):
        for j, end in enumerate(events):
            if i == j:
                continue
            lo = _output_bound(-distance[j][i]) if distance[j][i] is not None else None
            hi = _output_bound(distance[i][j])
            bounds.append(dict(start=start, end=end, lower=lo, upper=hi,
                lower_support=list(dict.fromkeys(paths[j][i])),
                upper_support=list(dict.fromkeys(paths[i][j])),
                independent_observation=False))
    return dict(schema_version='source-event-difference-closure/1', feasible=True,
        events=events, input_constraint_ids=identifiers,
        report_group_ids=sorted(groups), tolerance=0., bounds=bounds,
        arithmetic='exact_rational_from_input_decimal_representation',
        automatic_ordering=False, latent_time_origin_fixed=False,
        qualification='Derived constraint bounds, not new observations, probabilities, '
            'posterior intervals, verified source facts or independent report errors.')
