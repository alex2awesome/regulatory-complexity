import numpy as np
import pytest

from pipeline.procbench.compact_visit_trace import Block,CompactTrace,Operation


def example(edges=None, rounds=2):
    ops=[Operation('file','payer','payer','filing',('submission',)),
         Operation('review','A','agency','review'),
         Operation('decide','A','agency','decision',('decision',))]
    blocks=[Block('cycle',('file','review'),edges,'retry'),Block('end',('decide',))]
    return CompactTrace(ops,blocks,np.array([[2.,3.,1.]]),{'retry':np.array([rounds])},
                        {'agency_hours':np.array([[0.,.5,.1]])})


def test_missing_edges_are_serial_but_explicit_empty_edges_allow_parallelism():
    assert example().event('initial_decision')[0]==16
    assert example(edges=()).event('initial_decision')[0]==10


def test_cycle_sum_span_first_filing_and_labor_are_distinct():
    trace=example()
    assert trace.values(dict(basis='sum_visit_cycles',activity_ids=['file']))[0]==6
    assert trace.values(dict(basis='first_to_last_activity_span',activity_ids=['file']))[0]==12
    assert trace.values(dict(basis='single_visit_cycle',activity_ids=['file']))[0]==2
    assert trace.event('initial_decision')[0]-trace.event('first_submission')[0]==14
    assert trace.values(dict(basis='agency_hours'))[0]==1.6
    assert trace.values(dict(basis='visit_count'))[0]==7
    assert trace.values(dict(basis='operation_count'))[0]==3
    assert trace.values(dict(basis='agency_count'))[0]==1


def test_compact_trace_matches_independent_expanded_operators():
    for edges in (None,()):
        for rounds in (0,1,8):
            trace=example(edges,rounds)
            expanded=trace.materialize()
            for event in ('initial_decision','first_submission','modeled_work_end'):
                assert trace.event(event)[0]==expanded.event(event)
            for aid in ('file','review','decide'):
                for basis, old in [('sum_visit_cycles','cycle'),('first_to_last_activity_span','stage_span')]:
                    assert trace.values(dict(basis=basis,activity_ids=[aid]))[0]==expanded.activity_time(aid,old)
            assert trace.values(dict(basis='agency_hours'))[0]==pytest.approx(expanded.burden()['agency_hours']['total'])


def test_first_final_decisions_separate_when_a_decision_repeats():
    ops=[Operation('d','A','agency','decision',('decision',))]
    trace=CompactTrace(ops,[Block('b',('d',),repeat_key='retry')],np.array([[3.]]),{'retry':np.array([4])})
    assert trace.event('initial_decision')[0]==3
    assert trace.event('final_decision')[0]==15


def test_no_hidden_numerical_maximum_on_repeats():
    trace=example(rounds=1_000_000)
    assert trace.event('initial_decision')[0]==5_000_006
    assert trace.values(dict(basis='visit_count'))[0]==2_000_003
    with pytest.raises(ValueError,match='expansion'):
        trace.materialize()


def test_unknown_agencies_resources_and_events_are_not_zero():
    op=Operation('u',None,'unknown','review')
    trace=CompactTrace([op],[Block('b',('u',))],np.array([[2.]]))
    for operator in (dict(basis='agency_count'),dict(basis='agency_hours')):
        with pytest.raises(ValueError):
            trace.values(operator)
    with pytest.raises(ValueError,match='absent'):
        trace.event('initial_decision')


def test_invalid_routes_and_counts_fail_instead_of_ignoring_evidence():
    ops=[Operation('a','A','agency','review'),Operation('b','A','agency','review')]
    durations=np.ones((1,2))
    with pytest.raises(ValueError,match='cycle'):
        CompactTrace(ops,[Block('x',('a','b'),(('a','b'),('b','a')))],durations)
    with pytest.raises(ValueError,match='integer'):
        CompactTrace(ops,[Block('x',('a','b'),repeat_key='r')],durations,{'r':np.array([1.5])})
    with pytest.raises(ValueError,match='cover'):
        CompactTrace(ops,[Block('x',('a',))],durations)


def test_wait_and_service_conserve_cycle_and_match_expanded_trace_across_repeats():
    for edges in (None, ()):
        for rounds in (0, 3, 9):
            base=example(edges,rounds)
            trace=CompactTrace(base.operations,base.blocks,base.durations,base.rounds,base.resources,
                               service_fractions=np.array([[.05,.25,1.]]))
            expanded=trace.materialize()
            np.testing.assert_array_equal(trace.event('initial_decision'),base.event('initial_decision'))
            np.testing.assert_array_equal(trace.values(dict(basis='agency_hours')),base.values(dict(basis='agency_hours')))
            for aid in ('file','review','decide'):
                for scope,visit in [('first','first'),('last','last'),('all_in_completed_case','all')]:
                    wait=trace.values(dict(basis='wait_elapsed',activity_ids=[aid],visits=scope))[0]
                    service=trace.values(dict(basis='service_elapsed',activity_ids=[aid],visits=scope))[0]
                    assert wait==pytest.approx(expanded.activity_time(aid,'waiting',visit))
                    assert service==pytest.approx(expanded.activity_time(aid,'service',visit))
                    assert wait+service==pytest.approx(expanded.activity_time(aid,'cycle',visit))
            op=dict(basis='service_elapsed',activity_ids=['file','review'],visits='all_in_completed_case')
            assert trace.values(op)[0]==pytest.approx(sum(expanded.activity_time(aid,'service') for aid in op['activity_ids']))


def test_phases_require_real_boundaries_and_resolved_visit_coverage():
    base=example()
    op=dict(basis='service_elapsed',activity_ids=['review'],visits='first')
    with pytest.raises(ValueError,match='unmodeled'):
        base.values(op)
    for fractions in (np.array([[.5]]), np.array([[.1,np.nan,.5]]),np.array([[.1,-.1,.5]])):
        with pytest.raises(ValueError,match='Service fractions'):
            CompactTrace(base.operations,base.blocks,base.durations,base.rounds,service_fractions=fractions)
    trace=CompactTrace(base.operations,base.blocks,base.durations,base.rounds,service_fractions=np.full((1,3),.1))
    for scope in ('reported_subset','unknown','all_completed_by_observation'):
        with pytest.raises(ValueError,match='coverage'):
            trace.values(dict(op,visits=scope))
    with pytest.raises(ValueError,match='one operation'):
        trace.values(dict(op,activity_ids=['file','review']))
