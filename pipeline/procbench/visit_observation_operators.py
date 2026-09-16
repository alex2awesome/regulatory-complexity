"""Evaluate a typed observation on one latent trace, without guessing omissions.

Missing/ambiguous operators return an explicit reason, never a zero burden. A
caller fitting alternatives must marginalize them with a declared probability
model; this module does not average LLM interpretations or invent weights.
"""
from dataclasses import dataclass
import math

from .visit_clocks import Trace


@dataclass(frozen=True)
class OperatorValue:
    days: float | None
    unresolved: str | None = None


EVENTS = {'process_start': 'process_start', 'first_submission': 'first_submission',
          'first_complete_submission': 'first_complete_submission',
          'initial_decision': 'initial_decision', 'final_decision': 'last_decision',
          'legal_closeout': 'legal_closeout', 'end_of_modeled_work': 'modeled_work_end'}


def evaluate_operator(trace, operator, *, complete_case=False, observation_time=None,
                      reported_visit_ids=None, recorded_visit_ids=None):
    """The trace is assumed complete from process start, not necessarily at its end.

    `recorded_visit_ids` is an explicit observation-process realization, not the
    set of all latent visits. Thus latest-recorded and final decisions can differ
    even when both timestamps have passed. Labor is never inferred by this clock.
    """
    if not isinstance(trace, Trace):
        raise TypeError('A typed latent trace is required')
    if observation_time is not None and (
            not math.isfinite(observation_time) or observation_time < trace.process_start):
        raise ValueError('Observation time must be finite and no earlier than process start')
    available = {v.visit_id: v for v in trace.visits}
    for ids in (reported_visit_ids, recorded_visit_ids):
        if ids is not None and (len(ids) != len(set(ids)) or not set(ids) <= set(available)):
            raise ValueError('Observation visit IDs must be distinct and belong to the latent trace')
    basis = operator['basis']
    if basis == 'whole_case_clock':
        def event(name):
            if name == 'latest_recorded_decision':
                if recorded_visit_ids is None:
                    return None
                recorded = [available[v] for v in recorded_visit_ids]
                if observation_time is not None:
                    recorded = [v for v in recorded if v.end <= observation_time]
                return Trace(tuple(recorded), trace.process_start).event('last_decision')
            if name in {'final_decision', 'legal_closeout', 'end_of_modeled_work'} and not complete_case:
                return None
            return trace.event(EVENTS[name]) if name in EVENTS else None
        start, end = event(operator['start']), event(operator['end'])
        if start is None or end is None:
            return OperatorValue(None, 'Unknown/missing event, incomplete final clock, or unspecified recording process')
        if end < start:
            return OperatorValue(None, 'This latent route does not support the stated event order')
        return OperatorValue(end-start)
    activities = set(operator['activity_ids'])
    if not activities:
        return OperatorValue(None, 'Activity identity is unresolved')
    rows = [v for v in trace.visits if v.activity_id in activities]
    scope = operator['visits']
    if scope == 'all_completed_by_observation':
        if observation_time is None:
            return OperatorValue(None, 'Completed-by-observation scope needs an observation time')
        rows = [v for v in rows if v.end <= observation_time]
    elif scope == 'all_in_completed_case':
        if not complete_case:
            return OperatorValue(None, 'All visits in a completed case requires a complete latent case')
    elif scope == 'reported_subset':
        if reported_visit_ids is None:
            return OperatorValue(None, 'A reported subset requires explicit visit linkage')
        rows = [v for v in rows if v.visit_id in reported_visit_ids]
    elif scope in {'first', 'last'}:
        if len(activities) != 1 or (scope == 'last' and not complete_case):
            return OperatorValue(None, 'First/last visit requires one activity and last requires case completion')
        rows.sort(key=lambda v: (v.start, v.end, v.visit_id))
        rows = rows[:1] if scope == 'first' else rows[-1:]
    elif scope == 'one_unspecified':
        if reported_visit_ids is None or len(reported_visit_ids) != 1:
            return OperatorValue(None, 'An unspecified single visit cannot silently become the first visit')
        rows = [v for v in rows if v.visit_id in reported_visit_ids]
    else:
        return OperatorValue(None, 'Visit scope is unresolved')
    if not rows:
        return OperatorValue(None, 'No linked visit on this latent route; absence is not a zero duration')
    if basis == 'single_visit_cycle':
        if len(rows) != 1:
            return OperatorValue(None, 'Single-visit operator selected multiple visits')
        return OperatorValue(rows[0].end-rows[0].start)
    if basis == 'sum_visit_cycles':
        return OperatorValue(sum(v.end-v.start for v in rows))
    if basis == 'first_to_last_activity_span':
        return OperatorValue(max(v.end for v in rows)-min(v.start for v in rows))
    if basis in {'wait_elapsed', 'service_elapsed'}:
        if any(v.service_start is None for v in rows):
            return OperatorValue(None, 'Waiting and service require explicit within-visit boundaries')
        return OperatorValue(sum((v.service_start-v.start if basis == 'wait_elapsed' else v.end-v.service_start)
                                 for v in rows))
    return OperatorValue(None, 'Duration basis is unresolved')


def evaluate_alternatives(trace, row, **context):
    if row['activity_mapping'] in {'unresolved', 'contradicted'} and any(
            op['basis'] != 'whole_case_clock' for op in row['operators']):
        return [OperatorValue(None, 'Resolve activity identity before linking this report to latent visits')]
    return [evaluate_operator(trace, operator, **context) for operator in row['operators']]
