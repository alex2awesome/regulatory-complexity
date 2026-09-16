from dataclasses import asdict

import pytest

from pipeline.procbench.visit_clocks import Trace, Visit
from pipeline.procbench.visit_observation_operators import evaluate_alternatives, evaluate_operator


def trace():
    return Trace((Visit('r1', 'review', 0, 2, service_start=1),
                  Visit('d1', 'decision', 2, 3, markers=('decision',)),
                  Visit('r2', 'review', 5, 8, service_start=7),
                  Visit('d2', 'decision', 8, 9, markers=('decision',))))


def operator(**kwargs):
    return dict(basis='sum_visit_cycles', activity_ids=['review'], start='single_visit_start',
                end='single_visit_end', visits='all_in_completed_case', censoring='none', notes='', **kwargs)


def test_sum_and_first_to_last_span_are_not_interchangeable():
    op = operator()
    assert evaluate_operator(trace(), op, complete_case=True).days == 5
    op['basis'] = 'first_to_last_activity_span'
    assert evaluate_operator(trace(), op, complete_case=True).days == 8
    op.update(basis='single_visit_cycle', visits='first')
    assert evaluate_operator(trace(), op).days == 2


def test_initial_final_and_latest_recorded_decisions_are_different_operators():
    op = dict(basis='whole_case_clock', activity_ids=[], start='process_start',
              end='initial_decision', visits='not_applicable', censoring='none', notes='')
    assert evaluate_operator(trace(), op).days == 3
    op['end'] = 'final_decision'
    assert evaluate_operator(trace(), op).days is None
    assert evaluate_operator(trace(), op, complete_case=True).days == 9
    op['end'] = 'latest_recorded_decision'
    assert evaluate_operator(trace(), op, complete_case=True).days is None
    assert evaluate_operator(trace(), op, complete_case=True, recorded_visit_ids=['d1']).days == 3


def test_unlinked_single_visit_or_reported_subset_is_not_guessed():
    op = operator()
    op.update(basis='single_visit_cycle', visits='one_unspecified')
    assert evaluate_operator(trace(), op).days is None
    assert evaluate_operator(trace(), op, reported_visit_ids=['r2']).days == 3
    op.update(basis='sum_visit_cycles', visits='reported_subset')
    assert evaluate_operator(trace(), op).days is None
    assert evaluate_operator(trace(), op, reported_visit_ids=['r1', 'r2']).days == 5


def test_observation_boundary_excludes_future_completions_and_needs_a_date():
    op = operator()
    op['visits'] = 'all_completed_by_observation'
    assert evaluate_operator(trace(), op).days is None
    assert evaluate_operator(trace(), op, observation_time=6).days == 2
    with pytest.raises(ValueError, match='Observation time'):
        evaluate_operator(trace(), op, observation_time=-1)
    with pytest.raises(ValueError, match='belong to the latent trace'):
        evaluate_operator(trace(), op, reported_visit_ids=['invented'])


def test_waiting_and_service_are_calendar_intervals_not_person_hours():
    op = operator()
    op['basis'] = 'wait_elapsed'
    assert evaluate_operator(trace(), op, complete_case=True).days == 3
    op['basis'] = 'service_elapsed'
    assert evaluate_operator(trace(), op, complete_case=True).days == 2
    t = Trace((Visit('r1', 'review', 0, 5),))
    assert evaluate_operator(t, op, complete_case=True).days is None


def test_semantic_alternatives_stay_separate_and_bad_identity_is_not_fitted():
    cycle = operator()
    span = dict(cycle, basis='first_to_last_activity_span')
    row = dict(activity_mapping='supported', operators=[cycle, span])
    assert [r.days for r in evaluate_alternatives(trace(), row, complete_case=True)] == [5, 8]
    row['activity_mapping'] = 'contradicted'
    results = evaluate_alternatives(trace(), row, complete_case=True)
    assert len(results) == 1 and results[0].days is None
    assert asdict(results[0])['unresolved']
