"""Elapsed report endpoints must observe one shared, possibly repeated graph."""
import numpy as np
import pytest

from pipeline.procbench.compact_visit_trace import (
    Block, CompactTrace, Operation, UnavailableTraceQuantity, validate_operator,
)
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy


def interval(start, end, *, start_event='end', end_event='end',
             start_occurrence='first', end_occurrence='last'):
    return dict(basis='activity_event_interval',
                start=dict(activity_id=start, event=start_event, occurrence=start_occurrence),
                end=dict(activity_id=end, event=end_event, occurrence=end_occurrence))


def test_repeat_and_wait_are_in_shared_clock_not_sum_of_endpoint_cycles():
    operations = [Operation(name, None, 'unknown', name) for name in ('file', 'review', 'approve')]
    blocks = [Block('file', ('file',)),
              Block('review', ('review',), repeat_key='revision', dwells=('review',)),
              Block('approve', ('approve',))]
    trace = CompactTrace(operations, blocks, np.array([[1., 3., 2.], [1., 3., 2.]]),
                         {'revision': np.array([0, 2])},
                         dwells=np.array([[np.nan, 4., np.nan], [np.nan, 4., np.nan]]))
    np.testing.assert_equal(trace.values(interval('file', 'approve')), [9., 23.])
    np.testing.assert_equal(trace.values(interval('review', 'review', start_event='start')),
                            [3., 17.])
    np.testing.assert_equal(trace.values(interval('review', 'review', start_event='start',
                                                  start_occurrence='last')), [3., 3.])


def test_parallel_branches_are_not_added_and_adjacent_events_can_share_time():
    operations = [Operation(name, None, 'unknown', name) for name in ('a', 'b', 'c')]
    trace = CompactTrace(operations, [Block('parallel', ('a', 'b', 'c'),
                                           edges=(('a', 'c'), ('b', 'c')))],
                         np.array([[2., 5., 1.]]))
    np.testing.assert_equal(trace.values(interval('a', 'c')), [4.])
    np.testing.assert_equal(trace.values(interval('b', 'c', end_event='start')), [0.])
    with pytest.raises(UnavailableTraceQuantity, match='precedes'):
        trace.values(interval('c', 'a'))
    with pytest.raises(UnavailableTraceQuantity, match='absent'):
        trace.values(interval('missing', 'a'))


def test_endpoint_selector_validation_and_native_v6_likelihood():
    operator = interval('a', 'b')
    validate_operator(operator)
    with pytest.raises(ValueError, match='endpoints'):
        validate_operator(dict(operator, start=dict(operator['start'], occurrence='guessed')))
    with pytest.raises(ValueError, match='exactly'):
        validate_operator(dict(operator, activity_ids=['a', 'b']))
    data = dict(programs=[dict(id='journey', routes=[dict(id='r', prior_weight=1.,
        operations=[dict(id=name, actor_id=None, actor_role='unknown', task_type=name)
                    for name in ('a', 'b')],
        blocks=[dict(id='serial', operations=['a', 'b'])])], observations=[dict(
            id='clock', case_id='case', source_family='forum', sampling='unselected',
            statistic='individual', lower=2., upper=4., operators=[operator], operator_weights=[1.])])])
    model = VisitHierarchy(data, Config(modeled_channels=('elapsed',), population_size=16))
    state = np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(state, [0]))
    assert model.log_likelihood(state, [0]) == pytest.approx(model.log_likelihood_reference(state, [0]))
