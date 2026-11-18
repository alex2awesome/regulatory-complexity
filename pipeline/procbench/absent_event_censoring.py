"""Explicit non-occurrence for a right-censored event time on a case path.

If a declared path never contains the endpoint event, its event time is infinity:
P(T > c | that path) = 1. This is not missing-data imputation or permission to
treat an unavailable duration/operator as a non-occurring event. Only reviewed
pending event-time observations with an available origin can opt in. Population
event-time summaries, withdrawal hazards and reporting/censoring selection are
not supplied by this contract.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math

import numpy as np

from .compact_visit_trace import CLOCK_EVENT_MARKERS, Block, Operation


SCHEMA_VERSION = 'absent-event-censoring/1'
FIELDS = {'schema_version', 'observation_id', 'absent_paths_by_inventory',
          'rationale', 'declaration_sha256'}


def _path_snapshot(routes):
    """Normalize raw and compiled paths to the same immutable model semantics."""
    return [dict(id=r['id'], prior_weight=r['prior_weight'],
        operations=[asdict(o if isinstance(o, Operation) else Operation(**o))
                    for o in r['operations']],
        paths=[dict(id=p['id'], probability_weight=p['probability_weight'],
                    blocks=[asdict(b if isinstance(b, Block) else Block(**b))
                            for b in p['blocks']]) for p in r['paths']]) for r in routes]


def declaration_digest(program_id, declaration, observations, routes, case_path_scope=None):
    by_id = {o['id']: o for o in observations}
    observation = by_id[declaration['observation_id']]
    payload = dict(program_id=program_id,
        declaration={k:v for k,v in declaration.items() if k != 'declaration_sha256'},
        observation=observation, paths=_path_snapshot(routes),
        case_path_scope=(case_path_scope or {}).get(observation['case_id']))
    try:
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError) as exc:
        raise ValueError('Absent-event declaration requires finite canonical JSON') from exc
    return hashlib.sha256(raw).hexdigest()


def _has_event(operations, event):
    if event in {'process_start', 'modeled_work_end', 'end_of_modeled_work'}:
        return True
    marker = CLOCK_EVENT_MARKERS[event][0]
    return any(marker in op.markers for op in operations)


def _has_endpoint(operations, operator):
    if operator['basis'] == 'activity_event_clock':
        return any(op.id == operator['activity_ids'][0] for op in operations)
    return _has_event(operations, operator['end'])


def validate_absent_event_censoring(raw, program):
    if not isinstance(raw, list):
        raise ValueError('absent_event_censoring must be a list')
    if not raw:
        return {}
    routes = program['routes']
    if any('paths' not in r for r in routes):
        raise ValueError('Absent-event censoring requires explicit paths in every inventory')
    by_id = {o['id']:o for o in program['observations']}
    result = {}
    for entry in raw:
        if (not isinstance(entry, dict) or set(entry) != FIELDS
                or entry['schema_version'] != SCHEMA_VERSION):
            raise ValueError('Absent-event censoring requires exact version-1 fields')
        name = entry['observation_id']
        if not isinstance(name, str) or name not in by_id or name in result:
            raise ValueError('Absent-event censoring requires distinct known observations')
        rationale = entry['rationale']
        if not isinstance(rationale, str) or not rationale.strip() or rationale != rationale.strip():
            raise ValueError('Absent-event censoring requires an explicit rationale')
        o = by_id[name]
        if (o['case_id'] is None or o['statistic'] != 'individual'
                or o.get('observation_kind') != 'pending_right_censored'
                or o['upper'] is not None or isinstance(o['lower'], bool)
                or not isinstance(o['lower'], (int, float)) or not math.isfinite(o['lower'])
                or o['lower'] < 0 or 'report_intervals' in o
                or len(o['operators']) != 1 or o['operator_weights'] != [1.]
                or any(isinstance(w, bool) or not isinstance(w, (int, float))
                       for w in o['operator_weights'])):
            raise ValueError('Absent-event censoring requires one explicitly pending individual event-time interval')
        operator = o['operators'][0]
        if (operator['basis'] not in {'whole_case_clock', 'activity_event_clock'}
                or (operator['basis'] == 'whole_case_clock'
                    and operator['end'] not in CLOCK_EVENT_MARKERS)):
            raise ValueError('Absent-event censoring requires an event endpoint, not a cycle duration or resource')
        absent = entry['absent_paths_by_inventory']
        if not isinstance(absent, dict) or set(absent) != {r['id'] for r in routes}:
            raise ValueError('Absent-event paths must cover every inventory explicitly')
        any_absent = False
        for route in routes:
            named = absent[route['id']]
            if (not isinstance(named, list) or any(not isinstance(x, str) for x in named)
                    or len(named) != len(set(named))):
                raise ValueError('Absent-event path IDs must be distinct strings')
            if not _has_endpoint(route['operations'], operator):
                raise ValueError('Endpoint absent from the entire inventory is unmodeled, not path non-occurrence')
            actual = []
            for path in route['paths']:
                if not _has_event(path['operations'], operator['start']):
                    raise ValueError('A censored event needs an available clock origin on every path')
                if not _has_endpoint(path['operations'], operator):
                    actual.append(path['id'])
            if set(named) != set(actual):
                raise ValueError('Declared absent paths do not match the structural endpoint presence')
            any_absent |= bool(actual)
        if not any_absent:
            raise ValueError('An absent-event declaration needs at least one explicitly absent path')
        if entry['declaration_sha256'] != declaration_digest(
                program['id'], entry, program['observations'], routes, program['case_path_scope']):
            raise ValueError('Absent-event digest does not match its observation and path structure')
        result[name] = deepcopy(entry)
    return result


def structural_survival_is_one(program, observation, trace):
    """No numeric infinities: structural absence is separate from invalid values."""
    if observation['id'] not in program.get('absent_event_censoring', {}):
        return False
    operator = observation['operators'][0]
    if _has_endpoint(trace.operations, operator):
        return False
    origin = trace.event(operator['start'])
    if not np.isfinite(origin).all():
        raise ValueError('Nonfinite event origin is not structural non-occurrence')
    return True
