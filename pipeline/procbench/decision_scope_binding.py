"""Narrow source-to-structure handshake for already represented case outcomes.

This is not outcome inference. A source-checked ledger supplies the decision ID;
an independently supplied structural program must already condition that case
on all and only paths carrying that single, unrepeated decision operation.
Other activity, exclusion and milestone constraints remain unsupported here.
"""
import hashlib
import json

VERSION = 'decision-only-case-scope/1'


def structure_digest(program):
    value = {k: program[k] for k in ('id', 'routes')}
    value['case_path_scope'] = program.get('case_path_scope', {})
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def decision_paths(program, case, decision):
    scope = program.get('case_path_scope', {}).get(case)
    if (not isinstance(scope, list) or not scope or
            any(not isinstance(p, str) or not p for p in scope) or len(set(scope)) != len(scope)):
        raise ValueError('Decision binding requires an existing explicit case-path scope: ' + case)
    if not program.get('routes'):
        raise ValueError('Decision binding requires structural inventories')
    all_matching, all_paths = set(), set()
    for route in program['routes']:
        operations = {o['id']: o for o in route['operations']}
        if len(operations) != len(route['operations']) or not route.get('paths'):
            raise ValueError('Decision binding requires distinct operations and explicit paths in every inventory')
        matching, route_ids = set(), set()
        for path in route['paths']:
            if path['id'] in route_ids:
                raise ValueError('Repeated structural path ID')
            route_ids.add(path['id']); all_paths.add(path['id'])
            members = [a for block in path['blocks'] for a in block['operations']]
            if not set(members) <= operations.keys():
                raise ValueError('Decision path refers to an unknown operation')
            decisions = [a for a in members if 'decision' in operations[a].get('markers', [])]
            if decision not in decisions:
                continue
            if decisions != [decision] or any(block.get('repeat_key') is not None
                    and decision in block['operations'] for block in path['blocks']):
                raise ValueError('Decision-only binding cannot resolve multiple or repeated decision occasions')
            matching.add(path['id'])
        if not matching or set(scope) & route_ids != matching:
            raise ValueError('Case scope must include all and only matching decision paths in each inventory')
        all_matching.update(matching)
    if set(scope) != all_matching or not set(scope) <= all_paths:
        raise ValueError('Case scope contains unrepresented decision paths')
    return sorted(scope)


def bind_decision_contexts(evidence, structural_context):
    """Return bindings only for decision-only, individual process contexts."""
    if structural_context is None:
        return {}
    if 'programs' in structural_context:
        matches = [p for p in structural_context['programs'] if p['id'] == evidence['program_id']]
        if len(matches) != 1:
            raise ValueError('Structural context must contain exactly one matching program')
        program = matches[0]
    else:
        program = structural_context
    if program.get('id') != evidence['program_id']:
        raise ValueError('Decision scope program does not match evidence')
    measurements = {m['id']: m for m in evidence['measurements']}
    contexts = evidence.get('observation_contexts', [])
    by_case = {}
    for context in contexts:
        case = measurements[context['measurement_id']]['case_id']
        if case is not None and context.get('decision_activity_id') is not None:
            by_case.setdefault(case, set()).add(context['decision_activity_id'])
    if any(len(decisions) != 1 for decisions in by_case.values()):
        raise ValueError('Conflicting source decision IDs cannot be discharged by a decision-only binding')
    fingerprint = structure_digest(program)
    bindings = {}
    for context in contexts:
        mid = context['measurement_id']; measurement = measurements[mid]
        decision = context.get('decision_activity_id')
        if (decision is None or measurement['case_id'] is None or measurement['metric'] != 'elapsed'
                or measurement['statistic'] != 'individual'
                or measurement['scope'] != 'process' or context['segment_mode'] != 'not_segment'
                or context['temporal_scope'] == 'hypothetical'
                or any(context.get(key) for key in ('required_activity_ids', 'excluded_activity_ids',
                                                   'clock_start_after_activity_ids'))):
            continue
        paths = decision_paths(program, measurement['case_id'], decision)
        bindings[mid] = dict(schema_version=VERSION, case_id=measurement['case_id'],
            decision_activity_id=decision, allowed_paths=paths, structure_sha256=fingerprint)
    return bindings


def validate_bound_observations(program):
    """Fail closed if a restored observation loses its required path condition."""
    fingerprint = None
    for observation in program.get('observations', []):
        binding = observation.get('decision_context_binding')
        if binding is None:
            continue
        if (set(binding) != {'schema_version', 'case_id', 'decision_activity_id', 'allowed_paths',
                             'structure_sha256'} or binding['schema_version'] != VERSION
                or observation['case_id'] is None or observation['statistic'] != 'individual'
                or binding['case_id'] != observation['case_id']):
            raise ValueError('Invalid decision-context observation binding')
        if fingerprint is None:
            fingerprint = structure_digest(program)
        if binding['structure_sha256'] != fingerprint:
            raise ValueError('Decision-bound observation requires its exact reviewed structural context')
        if binding['allowed_paths'] != decision_paths(program, binding['case_id'], binding['decision_activity_id']):
            raise ValueError('Decision-bound observation path condition changed')
