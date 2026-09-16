import copy

import numpy as np
import pytest

from pipeline.procbench.audit_visit_observations import VERSION
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compile_visit_durations import compile_durations
from test_bayes_hierarchy import add_context, fixture, measurement
from test_process_measurement import audit_row


def inputs():
    e = fixture()
    e['measurements'] = [measurement()]
    operator = dict(basis='single_visit_cycle', activity_ids=['review'], start='single_visit_start',
                    end='single_visit_end', visits='first', censoring='none', notes='')
    visit = dict(schema_version=VERSION, program_id=e['program_id'], measurements=[dict(
        measurement_id='m1', identification='explicit', activity_mapping='supported',
        operators=[operator], evidence=[dict(doc_id='document', quote='Evidence')], notes='')], unresolved=[])
    semantic = dict(program_id=e['program_id'], measurements=[audit_row()], unresolved=[])
    docs = [dict(id='document', text='Evidence')]
    policy = dict(case_sampling={'c1': 'unselected'})
    return e, visit, semantic, docs, policy


def test_compiled_claim_runs_in_joint_model_without_altering_source():
    e, v, s, d, p = inputs()
    original = copy.deepcopy((e, v, s))
    compiled = compile_durations(e, v, s, d, p)
    assert (e, v, s) == original
    assert compiled['complete_elapsed_coverage']
    assert not compiled['ready_for_full_burden_fit']
    o = compiled['observations'][0]
    assert (o['lower'], o['upper']) == (11.5, 12.5)
    data = dict(programs=[dict(id=e['program_id'], observations=compiled['observations'], routes=[dict(
        id='r', prior_weight=1., operations=[dict(id='review', actor_id='A', actor_role='agency',
        task_type='technical_review', markers=['decision'])], blocks=[dict(id='b', operations=['review'])])])])
    model = VisitHierarchy(data, Config(population_size=16))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [0]))


def test_unknown_alternative_is_not_dropped_to_make_claim_fit():
    e, v, s, d, p = inputs()
    row = v['measurements'][0]
    row['identification'] = 'unresolved'
    unknown = copy.deepcopy(row['operators'][0])
    unknown.update(basis='unknown', visits='unknown')
    row['operators'].append(unknown)
    p['interpretation_priors'] = {'m1': [.9, .1]}
    result = compile_durations(e, v, s, d, p)
    assert not result['observations']
    assert 'unmodeled_duration_basis:unknown' in result['dispositions'][0]['reasons']
    assert len(result['dispositions'][0]['visit_audit']['operators']) == 2


def test_explicit_prior_required_for_all_supported_alternatives():
    e, v, s, d, p = inputs()
    row = v['measurements'][0]
    row['identification'] = 'unresolved'
    op = copy.deepcopy(row['operators'][0])
    op.update(basis='sum_visit_cycles', visits='all_in_completed_case')
    row['operators'].append(op)
    assert not compile_durations(e, v, s, d, p)['observations']
    p['interpretation_priors'] = {'m1': [.25, .75]}
    assert compile_durations(e, v, s, d, p)['observations'][0]['operator_weights'] == [.25, .75]
    p['interpretation_priors']['m1'] = [1., 0.]
    with pytest.raises(ValueError, match='every unchanged alternative'):
        compile_durations(e, v, s, d, p)


@pytest.mark.parametrize('basis,scope,reason', [
    ('wait_elapsed', 'first', 'unknown_or_partial_within_visit_phase_boundary'),
    ('service_elapsed', 'first', 'unknown_or_partial_within_visit_phase_boundary'),
    ('sum_visit_cycles', 'all_completed_by_observation', 'partial_or_unknown_visit_coverage')])
def test_unknown_phase_boundaries_and_partial_recording_are_preserved(basis, scope, reason):
    e, v, s, d, p = inputs()
    v['measurements'][0]['operators'][0].update(basis=basis, visits=scope)
    result = compile_durations(e, v, s, d, p)
    assert not result['observations']
    assert reason in result['dispositions'][0]['reasons']


@pytest.mark.parametrize('basis,start,end', [('wait_elapsed','appointment_request','service_start'),
                                           ('service_elapsed','service_start','service_end')])
def test_supported_phase_compiles_to_the_same_joint_likelihood(basis,start,end):
    e,v,s,d,p=inputs()
    v['measurements'][0]['operators'][0].update(basis=basis,start=start,end=end)
    result=compile_durations(e,v,s,d,p)
    assert result['required_model_features']==['within_visit_phases']
    data=dict(programs=[dict(id=e['program_id'],observations=result['observations'],routes=[dict(
        id='r',prior_weight=1.,operations=[dict(id='review',actor_id='A',actor_role='agency',
        task_type='technical_review',markers=['decision'])],blocks=[dict(id='b',operations=['review'])])])])
    with pytest.raises(ValueError,match='within_visit_phases'):
        VisitHierarchy(data,Config(population_size=16))
    model=VisitHierarchy(data,Config(population_size=16,within_visit_phases=True))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size),[0]))


def test_typical_is_not_median_and_finite_n_is_not_ignored():
    e, v, s, d, p = inputs()
    m, semantic = e['measurements'][0], s['measurements'][0]
    m.update(case_id=None, statistic='typical')
    semantic.update(statistic_interpretation='typical_range', population_scope='all_cases')
    p = {}
    assert not compile_durations(e, v, s, d, p)['observations']
    m.update(statistic='median', n=20)
    semantic['statistic_interpretation'] = 'population_median'
    result = compile_durations(e, v, s, d, p)
    assert 'finite_cohort_summary_likelihood_not_implemented' in result['dispositions'][0]['reasons']
    m['n'] = None
    assert compile_durations(e, v, s, d, p)['observations'][0]['statistic'] == 'median'


def test_censoring_and_original_minute_precision_survive_compilation():
    e, v, s, d, p = inputs()
    e['measurements'][0].update(value=1 / 3, unit='hours')
    s['measurements'][0]['original_precision_unit'] = 'minutes'
    o = compile_durations(e, v, s, d, p)['observations'][0]
    assert o['lower'] * 1440 == pytest.approx(19.5)
    assert o['upper'] * 1440 == pytest.approx(20.5)
    v['measurements'][0]['operators'][0]['censoring'] = 'right'
    o = compile_durations(e, v, s, d, p)['observations'][0]
    assert o['upper'] is None
    assert o['lower'] * 1440 == pytest.approx(19.5)


def test_unknown_sampling_clocks_and_calendar_are_not_invented():
    e, v, s, d, p = inputs()
    assert not compile_durations(e, v, s, d)['observations']
    e['measurements'][0]['unit'] = 'business_days'
    assert 'unmodeled_calendar:business_days' in compile_durations(e, v, s, d, p)['dispositions'][0]['reasons']
    op = v['measurements'][0]['operators'][0]
    op.update(basis='whole_case_clock', activity_ids=[], start='process_start',
              end='latest_recorded_decision', visits='not_applicable')
    assert 'unmodeled_or_unknown_clock_boundary' in compile_durations(e, v, s, d, p)['dispositions'][0]['reasons']


def test_whole_source_ledger_is_accounted_for_and_quotes_checked():
    e, v, s, d, p = inputs()
    fee = measurement(ident='fee')
    fee.update(metric='fee', unit='USD')
    e['measurements'].append(fee)
    result = compile_durations(e, v, s, d, p)
    assert len(result['dispositions']) == 2
    assert result['dispositions'][1]['source']['id'] == 'fee'
    assert result['coverage']['eligible_elapsed'] == 1
    e['measurements'][0]['quote'] = 'Invented source'
    with pytest.raises(ValueError, match='not verbatim'):
        compile_durations(e, v, s, d, p)


def test_observed_case_branch_constraints_cannot_be_lost_at_compilation():
    e, v, s, d, p = inputs()
    add_context(e, 'm1', required_activity_ids=['review'], excluded_activity_ids=['file'])
    result = compile_durations(e, v, s, d, p)
    assert not result['observations']
    row = result['dispositions'][0]
    assert row['route_context']['excluded_activity_ids'] == ['file']
    assert 'case_route_or_milestone_constraints_need_compilation' in row['reasons']
