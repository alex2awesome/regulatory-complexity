"""Step-level population expectations conditional on ONE linked V6 draw.

These are reporting functions, not a second likelihood or a fitted burden table.
Call them on aligned structure/continuous draws, then summarize those outputs;
products of marginal summaries would lose inventory/repeat/time dependence.
Inventory availability is distinct from participation in a case path. Elapsed
exposure is additive operation time, NOT a process clock on a parallel route.
"""
from __future__ import annotations

import math

import numpy as np


def _total_order(names, edges):
    """Whether a validated finite DAG orders every pair, including transitively."""
    reach = {name: set() for name in names}
    for before, after in edges:
        reach[before].add(after)
    for middle in names:
        for before in names:
            if middle in reach[before]:
                reach[before].update(reach[middle])
    return all(b in reach[a] or a in reach[b]
               for i, a in enumerate(names) for b in names[i + 1:])


def _serial(path):
    blocks = path['blocks']
    if not all(block.edges is None or _total_order(list(block.operations), block.edges)
               for block in blocks):
        return False
    return (all(block.predecessors is None for block in blocks)
            or _total_order([block.id for block in blocks],
                            [(parent, block.id) for block in blocks
                             for parent in (block.predecessors or ())]))


def _weighted(values, weights):
    # An unmeasured positive-mass branch is unknown, not zero or discarded.
    if any(value is None and weight > 0 for value, weight in zip(values, weights)):
        return None
    return float(sum(weight * value for value, weight in zip(values, weights)
                     if weight > 0))


def conditional_step_burden(model, program, z, parameters, route_index):
    """Exact means for counts/resources; analytic serial end-clock attribution.

    Time means integrate V6's lognormal case variation; repeats use its exact
    hurdle-geometric mean. A declared dwell is attributed to the gap BEFORE the
    named operation, explicitly, not relabeled as its labor. The clock, when
    additive, ends at modeled_work_end, not necessarily initial_decision.
    Fees are per visit under the existing V6 contract. Payee/stringency/legal
    provenance are not invented from actor IDs and must be joined separately.
    """
    route = program['routes'][route_index]
    paths = route.get('paths', [route])
    probabilities = (model.path_probabilities(route, z) if 'paths' in route
                     else np.ones(1))
    if (not np.isfinite(probabilities).all() or np.any(probabilities <= 0)
            or not np.isclose(sum(probabilities), 1.)):
        raise ValueError('Step burden needs a normalized positive case-path mixture')
    all_operations = {}
    for candidate in program['routes']:
        all_operations.update((op.id, op) for op in candidate['operations'])
    present = {op.id for op in route['operations']}
    q, r = model.repeat_parameters(program, z)
    phase = model.phase_means(parameters) if model.cfg.within_visit_phases else None
    serial = all(_serial(path) for path in paths)
    path_rows = []
    numeric = ('participation_probability', 'expected_visits', 'expected_extra_visits',
               'elapsed_exposure', 'waiting_elapsed', 'service_elapsed',
               'dwell_before', 'payer_hours', 'agency_hours', 'fee_total')
    for path in paths:
        rows = {aid: dict.fromkeys(numeric, 0.) for aid in all_operations}
        multiplier = dict.fromkeys((op.id for op in path['operations']), 1.)
        dwell_ids = set()
        for block in path['blocks']:
            dwell_ids.update(block.dwells or ())
            if block.repeat_key is not None:
                j = program['repeat_keys'].index(block.repeat_key)
                for aid in block.operations:
                    multiplier[aid] = 1. + q[j] / (1. - r[j])
        for index, op in zip(path['indices'], path['operations']):
            m = multiplier[op.id]
            row = rows[op.id]
            row.update(participation_probability=1., expected_visits=float(m),
                       expected_extra_visits=float(m - 1.))
            row['elapsed_exposure'] = m * math.exp(parameters['mu'][0, index]
                + .5 * (parameters['sigma'][0]**2 + model.cfg.common_case_sd**2))
            row['waiting_elapsed'] = None if phase is None else float(m * phase[0][index])
            row['service_elapsed'] = None if phase is None else float(m * phase[1][index])
            if op.id in dwell_ids:
                site = model.dwell_index[(program['id'], op.id)]
                row['dwell_before'] = m * math.exp(parameters['dwell_log'][site]
                                                   + .5 * model.cfg.dwell_case_sd**2)
            for channel, field in ((1, 'payer_work'), (2, 'agency_work')):
                applicable = getattr(op, field)
                key = 'payer_hours' if channel == 1 else 'agency_hours'
                row[key] = (0. if applicable is False else
                            m * math.exp(parameters['mu'][channel, index]
                                + .5 * (parameters['sigma'][channel]**2
                                        + model.cfg.common_case_sd**2))
                            if applicable is True and channel in model.active_channels
                            else None)
            row['fee_total'] = None if op.fee is None else m * op.fee
        path_rows.append(rows)
    result = {}
    for aid in all_operations:
        row = {key: _weighted([path[aid][key] for path in path_rows], probabilities)
               for key in numeric}
        row['inventory_available'] = aid in present
        participation = row['participation_probability']
        row['expected_visits_given_participation'] = (
            row['expected_visits'] / participation if participation > 0 else None)
        row['modeled_end_clock_contribution'] = (
            row['elapsed_exposure'] + row['dwell_before'] if serial else None)
        result[aid] = row
    totals = {}
    for key in (*numeric, 'modeled_end_clock_contribution'):
        vals = [row[key] for row in result.values()]
        totals[key] = None if any(value is None for value in vals) else float(sum(vals))
    share_channels = ('elapsed_exposure', 'dwell_before', 'payer_hours', 'agency_hours',
                      'fee_total', 'modeled_end_clock_contribution')
    for row in result.values():
        row['shares_of_population_mean'] = {
            key: row[key] / totals[key] if totals[key] is not None and totals[key] > 0
            else None for key in share_channels}
    return {
        'schema_version': 'conditional-step-burden/1',
        'program_id': program['id'], 'route_id': route['id'],
        'steps': result, 'totals': totals,
        'clock_attribution': 'serial_modeled_work_end' if serial else 'not_additive',
        'time_unit': model.data.get('elapsed_time_unit', 'calendar_days'),
        'estimand': 'population_expectation_conditional_on_one_joint_parameter_draw',
        'share_estimand': 'ratio_of_population_means_not_mean_of_casewise_ratios',
        'release_eligible': False,
        'cautions': [
            'Inventory availability does not mean mandatory participation.',
            'Elapsed exposure is not a clock for parallel paths.',
            'Dwell is elapsed waiting, never payer or agency labor.',
            'Unknown cost, work applicability, or inactive work channel stays unknown.',
            'Payee, stringency, and evidence-identification gates must be supplied separately.',
        ],
    }
