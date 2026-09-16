from dataclasses import replace

import pytest

from pipeline.procbench.visit_clocks import Trace,Visit


def trace():
    return Trace((
        Visit('f1','file',0,2,'applicant','payer',('submission',),payer_hours=1,agency_hours=0,fee_dollars=10),
        Visit('r1','review',2,6,'building','agency',service_start=5,payer_hours=0,agency_hours=2,fee_dollars=0),
        Visit('d1','decision',6,7,'building','agency',('decision',),payer_hours=0,agency_hours=.5,fee_dollars=0),
        Visit('f2','file',9,12,'applicant','payer',('submission','complete_submission'),payer_hours=2,agency_hours=0,fee_dollars=0),
        Visit('d2','decision',12,15,'building','agency',('decision',),payer_hours=0,agency_hours=.5,fee_dollars=0),
        Visit('background','records',4,18,None,'unknown'),
    ))


def test_first_last_decision_work_end_and_legal_closeout_are_different_events():
    case=trace()
    assert case.interval('process_start','initial_decision')==7
    assert case.interval('process_start','last_decision')==15
    assert case.event('modeled_work_end')==18
    assert case.event('legal_closeout') is None


def test_first_filing_never_subtracts_every_correction_visit():
    case=trace()
    assert case.interval('first_submission','initial_decision')==5
    assert case.interval('first_submission','last_decision')==13
    assert case.interval('first_complete_submission','last_decision')==3
    with pytest.raises(ValueError,match='precedes'):
        case.interval('first_complete_submission','initial_decision')


def test_cycle_sums_first_visit_and_stage_span_are_not_interchangeable():
    case=trace()
    assert case.activity_time('file','cycle')==5
    assert case.activity_time('file','cycle','first')==2
    assert case.activity_time('file','cycle','f2')==3
    assert case.activity_time('file','stage_span')==12
    assert case.activity_time('missing','cycle') is None


def test_wait_service_and_labor_are_different_units_with_no_silent_conversion():
    case=trace()
    assert case.activity_time('review','cycle')==4
    assert case.activity_time('review','waiting')==3
    assert case.activity_time('review','service')==1
    assert case.visits[1].agency_hours==2  # not 24 hours because elapsed service was one day
    assert case.activity_time('file','service') is None


def test_started_and_completed_backend_counts_have_explicit_boundary_policies():
    case=trace()
    completed=case.through('initial_decision','completed').burden()
    started=case.through('initial_decision','started').burden()
    assert completed['visits']==3 and started['visits']==4
    assert completed['agency_count']==1
    assert started['agency_count'] is None
    assert started['known_agency_count_lower_bound']==1
    assert started['unattributed_visit_ids']==['background']


def test_unknown_resource_values_remain_missing_with_known_lower_bounds():
    burden=trace().burden()
    assert burden['visits']==6 and burden['distinct_operations']==4
    assert burden['payer_hours']['total'] is None
    assert burden['payer_hours']['known_sum_lower_bound']==3
    assert burden['agency_hours']['known_sum_lower_bound']==3
    assert burden['fee_dollars']['known_sum_lower_bound']==10
    complete=trace().through('last_decision','completed').burden()
    assert complete['payer_hours']['total']==3 and complete['agency_hours']['total']==3


def test_operation_identity_hypothesis_changes_counts_not_calendar_or_labor():
    case=trace()
    ordinary=case.burden()
    coarse=case.burden(dict(file='filing',review='review-and-decision',decision='review-and-decision',records='records'))
    assert coarse['distinct_operations']==ordinary['distinct_operations']-1
    assert coarse['visits']==ordinary['visits']
    assert coarse['agency_hours']==ordinary['agency_hours']


def test_missing_events_duplicate_visits_and_impossible_service_times_are_not_zero_completions():
    assert Trace(()).event('initial_decision') is None
    assert Trace(()).event('modeled_work_end') is None
    assert Trace(()).through('initial_decision','completed') is None
    with pytest.raises(ValueError,match='distinct visit ID'):
        Trace((trace().visits[0],trace().visits[0]))
    with pytest.raises(ValueError,match='inside'):
        replace(trace().visits[1],service_start=9)
    with pytest.raises(ValueError,match='ordered'):
        replace(trace().visits[1],end=1)
    with pytest.raises(ValueError,match='Unsupported event'):
        trace().event('complete_application_guessed_from_last_filing')


def test_trace_copies_mutable_inputs_and_does_not_invent_missing_identity_mapping():
    visits=list(trace().visits)
    case=Trace(visits)
    visits.clear()
    assert len(case.visits)==6
    with pytest.raises(ValueError,match='cover every'):
        case.burden({})
    with pytest.raises(ValueError,match='empty identifier'):
        replace(case.visits[0],actor_id='')
