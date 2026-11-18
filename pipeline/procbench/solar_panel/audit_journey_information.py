"""Necessary event-boundary design screen for reviewed serial case journeys.

This is not a sampler, Fisher information estimate or recovery/calibration gate.
It examines which *case duration combinations* the supplied interval endpoints
can distinguish even with perfect reports. Unknown actions inside a declared
composite are not coordinates here and do not become identified by this screen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _serial_operations(program):
    routes = program['routes']
    if len(routes) != 1:
        raise ValueError('Screen requires one fixed realized route, not a route mixture')
    route = routes[0]
    if route.get('paths') or route.get('repeats') or route.get('dwells'):
        raise ValueError('Screen does not linearize path mixtures, repeat families or dwells')
    order, previous = [], []
    for block in route['blocks']:
        if len(block['operations']) != 1 or block.get('predecessors') != previous or block.get('repeat_key'):
            raise ValueError('Screen requires explicit serial singleton blocks in topological order')
        order.append(block['operations'][0])
        previous = [block['id']]
    if len(set(order)) != len(order) or set(order) != {o['id'] for o in route['operations']}:
        raise ValueError('Each declared operation must occur exactly once in the serial path')
    return order


def _row(observation, order):
    operators = observation['operators']
    if len(operators) != 1 or observation['operator_weights'] != [1.0]:
        raise ValueError('Screen does not flatten uncertain endpoint operators')
    operator = operators[0]
    row = np.zeros(len(order))
    if operator['basis'] == 'single_visit_cycle':
        activities = operator['activity_ids']
        if len(activities) != 1:
            raise ValueError('Expected one reviewed activity for single_visit_cycle')
        row[order.index(activities[0])] = 1.
    elif operator['basis'] == 'activity_event_interval':
        def prefix(event):
            if event.get('event') not in {'start', 'end'} or event.get('occurrence') not in {'first', 'last'}:
                raise ValueError('Unsupported event selector')
            stop = order.index(event['activity_id']) + int(event['event'] == 'end')
            value = np.zeros(len(order))
            value[:stop] = 1.
            return value
        row = prefix(operator['end']) - prefix(operator['start'])
        if np.any(row < 0) or not np.any(row):
            raise ValueError('Interval is not a forward nonempty serial duration')
    else:
        raise ValueError('Unsupported observation basis: '+operator['basis'])
    return row


def _screen(matrix, order):
    if not len(matrix):
        basis = np.zeros((0, len(order)))
        singular = np.array([])
    else:
        _, singular, right = np.linalg.svd(matrix, full_matrices=False)
        tolerance = max(matrix.shape)*np.finfo(float).eps*singular[0]
        basis = right[singular > tolerance]

    def residual(vector):
        return float(np.linalg.norm(vector-basis.T@(basis@vector)))

    individual = [residual(np.eye(len(order))[i]) < 1e-8 for i in range(len(order))]
    return dict(rows=len(matrix), rank=len(basis), duration_coordinates=len(order),
        nullity=len(order)-len(basis), singular_values=singular.tolist(),
        individually_separable=[o for o, yes in zip(order, individual) if yes],
        not_individually_separable=[o for o, yes in zip(order, individual) if not yes],
        scoped_total_in_row_space=residual(np.ones(len(order))) < 1e-8)


def audit(data):
    rows = []
    for program in data['programs']:
        context = program.get('journey_context', {})
        case = context.get('canonical_case_id', program['id'])
        try:
            order = _serial_operations(program)
            observations = program['observations']
            matrix = np.asarray([_row(o, order) for o in observations]).reshape(-1, len(order))
            completed = [i for i, o in enumerate(observations)
                if o.get('observation_kind') == 'completed_interval'
                and isinstance(o.get('lower'), (int, float))
                and isinstance(o.get('upper'), (int, float))
                and np.isfinite([o['lower'], o['upper']]).all()]
            by_id = {o['operation_id']: o for o in context['reviewed_operation_declarations']}
            rows.append(dict(case_id=case, status='screened', operation_order=order,
                observation_ids=[o['id'] for o in observations], incidence_matrix=matrix.tolist(),
                all_report_directions=_screen(matrix, order),
                finite_completed_intervals=_screen(matrix[completed], order),
                one_sided_or_other_rows=[o['id'] for i, o in enumerate(observations) if i not in completed],
                composites_or_coordination=[k for k in order if by_id[k]['component_kind'] != 'action_cycle']))
        except (KeyError, ValueError) as error:
            # Preserve unsupported cases explicitly instead of silently removing
            # graph branches and certifying the remaining matrix.
            rows.append(dict(case_id=case, status='unsupported', reason=str(error)))
    screened = [r for r in rows if r['status'] == 'screened']
    return dict(schema_version='solar-journey-boundary-design/1', cases=rows,
        screened_cases=len(screened), unsupported_cases=len(rows)-len(screened),
        duration_coordinates=sum(r['all_report_directions']['duration_coordinates'] for r in screened),
        optimistic_rank_all_report_directions=sum(r['all_report_directions']['rank'] for r in screened),
        finite_completed_interval_rank=sum(r['finite_completed_intervals']['rank'] for r in screened),
        qualifications=[
            'Necessary optimistic linear design screen, not posterior learning or a fit gate.',
            'Finite intervals have uncertainty and one-sided reports do not pin exact values; rank is not Fisher information.',
            'A composite coordinate can be separable even when every internal action duration is unknown.',
            'Conditional on reviewed fixed serial routes; missing actions, selection, report error and route uncertainty are not solved here.',
            'Case-duration separability is not population task-mean, source-bias or intrinsic-agency identification.',
            'No extra likelihood factors or prior assumptions are introduced by this diagnostic.'
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    raw = args.data.read_bytes()
    report = audit(json.loads(raw))
    report['input'] = {'path': str(args.data), 'sha256': hashlib.sha256(raw).hexdigest()}
    report['implementation_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.out.open('x') as stream:
        stream.write(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('screened_cases', 'unsupported_cases',
        'duration_coordinates', 'optimistic_rank_all_report_directions', 'finite_completed_interval_rank')}))


if __name__ == '__main__':
    main()
