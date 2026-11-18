"""Opt-in fixed case-specific priors for V6's existing joint path mixture.

These are declared sensitivity weights, not calibrated LLM confidence or
population path frequencies. Hashing binds the declaration to its case and
inventory; it cannot certify source interpretation. No observations or latent
coordinates are added here.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math

import numpy as np
from scipy.special import logsumexp


SCHEMA_VERSION = 'fixed-case-path-prior/1'
FIELDS = {'schema_version', 'interpretation', 'weights', 'basis', 'rationale',
          'unknown_or_unlisted_path_id', 'exhaustive_scope_reason',
          'actor_assignment', 'declaration_sha256'}


def declaration_digest(program_id, case_id, route_id, declaration):
    """Bind the complete non-digest payload, including its assignment context."""
    payload = dict(program_id=program_id, case_id=case_id, route_id=route_id,
                   declaration={k: v for k, v in declaration.items()
                                if k != 'declaration_sha256'})
    try:
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise ValueError('Case-path declarations must be finite canonical JSON') from exc
    return hashlib.sha256(raw).hexdigest()


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError('Case-path prior requires canonical nonempty ' + name)


def _actor_shape(path, candidate, logical_phase_id):
    """Erase only the nominated actor identity, never schedule or task facts."""
    names = {op.id: ('actor_phase:' + logical_phase_id if op.id == candidate
                     else 'shared_operation:' + op.id) for op in path['operations']}
    operations = []
    for op in path['operations']:
        row = asdict(op)
        row['id'] = names[op.id]
        if op.id == candidate:
            row['actor_id'], row['actor_role'] = '<assignment>', '<assignment>'
        operations.append(row)
    blocks = []
    block_names = {b.id: str(i) for i, b in enumerate(path['blocks'])}
    for b in path['blocks']:
        row = asdict(b)
        row['id'] = block_names[b.id]
        row['operations'] = [names[x] for x in b.operations]
        if b.edges is not None:
            row['edges'] = sorted([names[a], names[c]] for a, c in b.edges)
        if b.dwells is not None:
            row['dwells'] = sorted(names[x] for x in b.dwells)
        if b.predecessors is not None:
            row['predecessors'] = sorted(block_names[x] for x in b.predecessors)
        blocks.append(row)
    return dict(operations=sorted(operations, key=lambda row: row['id']), blocks=blocks)


def _validate_actor_assignment(entry, allowed_paths, cfg):
    assignment = entry['actor_assignment']
    if (not isinstance(assignment, dict) or set(assignment) !=
            {'id', 'logical_phase_id', 'candidate_operations'}):
        raise ValueError('Actor assignment requires one named logical phase and candidate-operation map')
    _text(assignment['id'], 'actor assignment id')
    _text(assignment['logical_phase_id'], 'logical phase id')
    mapping = assignment['candidate_operations']
    if not isinstance(mapping, dict) or set(mapping) != {p['id'] for p in allowed_paths}:
        raise ValueError('Actor candidate operations must exactly cover allowed paths')
    # Different operation effects or separate waiting/service decompositions
    # could distinguish alternatives for reasons other than actor identity.
    # The initial actor-only contract does not permit that confounding.
    if cfg.operation_sd != 0 or cfg.within_visit_phases or cfg.inter_operation_dwell:
        raise ValueError('Actor-only alternatives require zero operation_sd and no phase/dwell decomposition')
    unknown = entry['unknown_or_unlisted_path_id']
    if len(allowed_paths) > 1 and unknown is None:
        raise ValueError('Uncertain actor assignment requires an unknown/unlisted alternative')
    shapes, actors, candidate_ids = [], set(), set()
    for path in allowed_paths:
        ident = mapping[path['id']]
        _text(ident, 'candidate operation id')
        matches = [op for op in path['operations'] if op.id == ident]
        if len(matches) != 1 or ident in candidate_ids:
            raise ValueError('Actor alternatives need distinct path-present candidate operations')
        candidate_ids.add(ident)
        op = matches[0]
        actor = (op.actor_role, op.actor_id)
        if actor in actors:
            raise ValueError('Actor alternatives must represent distinct actor identities')
        actors.add(actor)
        if path['id'] == unknown:
            if op.actor_role != 'unknown' or op.actor_id is not None:
                raise ValueError('Unknown actor path must retain unknown role and null actor_id')
        elif op.actor_role == 'unknown' or op.actor_id is None:
            raise ValueError('An unlisted actor must be the declared unknown path')
        shapes.append(_actor_shape(path, ident, assignment['logical_phase_id']))
    if any(shape != shapes[0] for shape in shapes[1:]):
        raise ValueError('Actor-only paths differ in task, work, fee, markers or schedule')


def validate_case_path_priors(raw, program, cfg):
    """Validate an optional declaration without changing legacy construction.

Every declared case covers every inventory hypothesis explicitly. Scope alone
excludes a path; a missing weight may not silently exclude it. V1 deliberately
requires fixed population path logits, so case sensitivity weights cannot be
misreported as learned population frequencies.
"""
    if not isinstance(raw, dict):
        raise ValueError('case_path_priors must be an object')
    if not raw:
        return {}
    if cfg.case_path_logit_sd != 0:
        raise ValueError('Fixed case-path priors v1 require case_path_logit_sd=0')
    if set(raw) - set(program['cases']):
        raise ValueError('Fixed path priors require known observed case IDs')
    routes = {r['id']: r for r in program['routes']}
    if any('paths' not in r for r in routes.values()):
        raise ValueError('Fixed case-path priors require paths in every inventory')
    result = {}
    for case, declarations in raw.items():
        if not isinstance(declarations, dict) or set(declarations) != set(routes):
            raise ValueError('Each fixed-prior case must explicitly cover every inventory')
        scope = program['case_path_scope'].get(case)
        result[case] = {}
        for route_id, entry in declarations.items():
            if not isinstance(entry, dict) or set(entry) != FIELDS:
                raise ValueError('Fixed case-path prior requires exact version-1 fields')
            if entry['schema_version'] != SCHEMA_VERSION:
                raise ValueError('Unknown fixed case-path prior schema')
            if entry['basis'] != 'declared_sensitivity':
                raise ValueError('Fixed case-path prior v1 supports declared sensitivity, not claimed calibration')
            if entry['interpretation'] not in ('process_path', 'actor_assignment'):
                raise ValueError('Unknown case-path prior interpretation')
            _text(entry['rationale'], 'rationale')
            paths = routes[route_id]['paths']
            allowed = [p for p in paths if scope is None or p['id'] in scope]
            weights = entry['weights']
            if (not allowed or not isinstance(weights, dict) or
                    set(weights) != {p['id'] for p in allowed}):
                raise ValueError('Fixed weights must exactly cover nonempty allowed case paths')
            for weight in weights.values():
                if (isinstance(weight, bool) or not isinstance(weight, (int, float))
                        or not math.isfinite(weight) or weight <= 0):
                    raise ValueError('Fixed path weights must be positive finite numbers')
            unknown = entry['unknown_or_unlisted_path_id']
            if unknown is not None and (not isinstance(unknown, str) or unknown not in weights):
                raise ValueError('Unknown/unlisted path must be an allowed path')
            if unknown is None:
                _text(entry['exhaustive_scope_reason'], 'exhaustive scope reason')
            elif entry['exhaustive_scope_reason'] is not None:
                raise ValueError('Do not declare an exhaustive scope while retaining an unknown path')
            if entry['interpretation'] == 'actor_assignment':
                _validate_actor_assignment(entry, allowed, cfg)
            elif entry['actor_assignment'] is not None:
                raise ValueError('Process-path declaration may not masquerade as actor attribution')
            expected = declaration_digest(program['id'], case, route_id, entry)
            if entry['declaration_sha256'] != expected:
                raise ValueError('Case-path declaration digest does not match its payload and context')
            log_prior = np.array([math.log(weights[p['id']]) if p['id'] in weights
                                  else -math.inf for p in paths])
            log_prior -= logsumexp(log_prior)
            result[case][route_id] = dict(declaration=deepcopy(entry), log_prior=log_prior)
    return result
