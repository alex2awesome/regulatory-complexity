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


def test_source_type_sampling_is_independent_of_case_names_and_offset_grouping():
    e,v,s,d,p=inputs()
    p=dict(default_case_sampling='unselected',source_type_sampling={'forum':'delay_selected'})
    before=copy.deepcopy(e)
    for grouping in ('document','type'):
        result=compile_durations(e,v,s,d,p,source_family_grouping=grouping,
                                 source_family_kinds={'document':'forum_thread'})
        assert result['observations'][0]['sampling']=='delay_selected'
        assert result['source_type_sampling']['case_decisions']['c1']['basis']=='source_type_policy'
    assert before==e
    # Misleading case names are not a source-type declaration.
    e['measurements'][0]['case_id']='reddit_slow_case'
    result=compile_durations(e,v,s,d,p,source_family_kinds={'document':'official_stats'})
    assert result['observations'][0]['sampling']=='unselected'


def test_source_type_sampling_missing_kind_and_mixed_case_are_not_guessed():
    from pipeline.procbench.compile_visit_durations import source_type_case_sampling
    e,v,s,d,p=inputs()
    p=dict(source_type_sampling={'forum':'delay_selected'})
    report=compile_durations(e,v,s,d,p)
    assert not report['observations']
    assert 'case_sampling_assumption_not_declared' in report['dispositions'][0]['reasons']
    mixed=copy.deepcopy(e['measurements'][0])
    mixed.update(id='m2',doc_id='agency_document',source_family='agency_document')
    e['measurements'].append(mixed)
    p['default_case_sampling']='unselected'
    kinds={'document':'forum_thread','agency_document':'program_page'}
    with pytest.raises(ValueError,match='Conflicting source ascertainment'):
        source_type_case_sampling(e,None,p,kinds)
    p['case_sampling']={'c1':'delay_selected'}
    sampling,report=source_type_case_sampling(e,None,p,kinds)
    assert sampling=={'c1':'delay_selected'}
    assert report['case_decisions']['c1']['basis']=='explicit_case_override'


def test_source_type_sampling_applies_one_mechanism_to_timing_money_hours_and_counts():
    from test_burden_channels_compile import ledger,count_audit
    e,v,s,d,p=ledger()
    p=dict(source_type_sampling={'forum':'delay_selected'},default_case_sampling='unselected')
    count=count_audit(e['program_id'])
    result=compile_durations(e,v,s,d,p,count_audit=count,burden_channels=('fee','effort','count'),
                            source_family_kinds={'document':'forum_thread'})
    case_rows=[o for o in result['observations'] if o['case_id']=='c1']
    assert len(case_rows)==4
    assert {o['sampling'] for o in case_rows}=={'delay_selected'}
    assert set(result['source_type_sampling']['case_decisions'])=={'c1'}


def test_source_family_cannot_override_an_unresolved_document_kind():
    from pipeline.procbench.compile_visit_durations import source_type_case_sampling
    e,_,_,_,_=inputs()
    e['measurements'][0]['source_family']='reddit_offset_pool'
    policy={'source_type_sampling':{'forum':'delay_selected'}}
    sampling,report=source_type_case_sampling(e,None,policy,{'document':'unresolved_capture'})
    assert sampling=={}
    row=report['case_decisions']['c1']
    assert row['basis']=='unresolved_source_type_without_default'
    assert row['sources'][0]['source_type'] is None


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
    assert 'finite_cohort_requires_explicit_joint_sampling_contract' in result['dispositions'][0]['reasons']
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


def first_visit_binding(evidence):
    return dict(schema_version='joint-visit-source-bindings/1', program_id=evidence['program_id'],
        measurements=[dict(measurement_id='m1', population_condition='first_visit',
            operator_selections=[], evidence=[dict(doc_id='document', quote='Evidence')],
            assumptions=['No additional duration-dependent selection within the stated first visits.'])])


def test_first_visit_population_is_explicitly_conditioned_not_relabelled_all_cases():
    e,v,s,d,p=inputs()
    p={}
    e['measurements'][0].update(case_id=None,statistic='median')
    s['measurements'][0].update(population_scope='selected_cohort',statistic_interpretation='population_median')
    original=copy.deepcopy((e,v,s))
    assert not compile_durations(e,v,s,d,p)['observations']
    bindings=first_visit_binding(e)
    result=compile_durations(e,v,s,d,p,source_bindings=bindings)
    o=result['observations'][0]
    assert o['population_condition']=='first_visit'
    assert o['provenance']['source_binding']==bindings['measurements'][0]
    assert (e,v,s)==original
    assert result['coverage']['informative_elapsed']==1
    # A cohort size is not discarded by this population binding.
    e['measurements'][0]['n']=30
    finite=compile_durations(e,v,s,d,p,source_bindings=bindings)
    assert 'finite_cohort_requires_explicit_joint_sampling_contract' in finite['dispositions'][0]['reasons']


def test_activity_union_preserves_ids_and_compiles_a_first_visit_not_a_sum():
    e,v,s,d,p=inputs()
    e['measurements'][0].update(activity_ids=['review','file'],scope='segment')
    v['measurements'][0]['operators'][0]['activity_ids']=['review','file']
    bindings=first_visit_binding(e)
    bindings['measurements'][0].update(population_condition=None,
        operator_selections=[dict(operator_index=0,mode='first_present')])
    assert not compile_durations(e,v,s,d,p)['observations']
    result=compile_durations(e,v,s,d,p,source_bindings=bindings)
    operator=result['observations'][0]['operators'][0]
    assert operator['activity_ids']==['review','file']
    assert operator['basis']=='single_visit_cycle'
    assert operator['activity_selection']=='first_present'


@pytest.mark.parametrize('bad',['quote','case','unknown_visit','unknown_statistic','no_assumptions','repeated_id'])
def test_source_bindings_do_not_override_unresolved_source_contracts(bad):
    e,v,s,d,p=inputs()
    p={}
    e['measurements'][0].update(case_id=None,statistic='median')
    s['measurements'][0].update(population_scope='selected_cohort',statistic_interpretation='population_median')
    bindings=first_visit_binding(e)
    if bad=='quote': bindings['measurements'][0]['evidence'][0]['quote']='Not present'
    elif bad=='case': e['measurements'][0]['case_id']='c1'
    elif bad=='unknown_visit': v['measurements'][0]['operators'][0]['visits']='unknown'
    elif bad=='unknown_statistic': s['measurements'][0]['statistic_interpretation']='unresolved'
    elif bad=='no_assumptions': bindings['measurements'][0]['assumptions']=[]
    elif bad=='repeated_id': bindings['measurements']*=2
    with pytest.raises(ValueError):
        compile_durations(e,v,s,d,p,source_bindings=bindings)


def grouped_inputs():
    e,v,s,d,p=inputs()
    e['measurements'].append(copy.deepcopy(e['measurements'][0]))
    e['measurements'][1]['id']='m2'
    for audit in (v,s):
        audit['measurements'].append(copy.deepcopy(audit['measurements'][0]))
        audit['measurements'][1]['measurement_id']='m2'
    groups=dict(schema_version='joint-visit-report-groups/1',program_id=e['program_id'],groups=[
        dict(id='one_report',measurement_ids=['m1','m2'],relationship='repeated_wording',representative_id='m1',
             evidence=[dict(doc_id='document',quote='Evidence')],assumptions=['One quantity restated, not a new sample.'])])
    return e,v,s,d,p,groups


def test_repeated_wording_retains_two_claims_but_exactly_one_likelihood_factor():
    e,v,s,d,p,g=grouped_inputs()
    e['measurements'][1].update(lower=10.,upper=15.,value=None)
    original=copy.deepcopy((e,v,s))
    c=compile_durations(e,v,s,d,p,report_groups=g)
    assert (e,v,s)==original
    assert c['coverage']['compiled_elapsed']==2
    assert c['coverage']['likelihood_factors']==1
    assert c['coverage']['informative_report_factors']==1
    assert c['complete_elapsed_coverage']
    assert c['observations'][0]['measurement_ids']==['m1','m2']
    assert (c['observations'][0]['lower'],c['observations'][0]['upper'])==(11.5,12.5)
    assert len(c['observations'][0]['provenance']['source_reports'])==2
    assert {x['likelihood_id'] for x in c['dispositions']}=={'m1'}


@pytest.mark.parametrize('intervals,expected',[
    ([(0.,2.),(1.,3.)],[[0.,3.]]),
    ([(0.,1.),(2.,3.)],[[0.,1.],[2.,3.]]),
    ([(0.,2.),(1.,None)],[[0.,None]]),
])
def test_one_disjunctive_phrase_uses_interval_union_without_double_counting(intervals,expected):
    e,v,s,d,p,g=grouped_inputs()
    for m,(lo,hi) in zip(e['measurements'],intervals):
        m.update(lower=lo,upper=hi,value=None)
    g['groups'][0].update(relationship='disjunctive_report',representative_id=None)
    c=compile_durations(e,v,s,d,p,report_groups=g)
    assert len(c['observations'])==1
    assert c['observations'][0]['report_intervals']==expected


@pytest.mark.parametrize('bad',['different_cases','different_operators','conflicting_numbers','quote','overlap','same_case_components'])
def test_grouping_never_guesses_independence_or_which_conflicting_report_to_trust(bad):
    e,v,s,d,p,g=grouped_inputs()
    if bad=='different_cases':
        e['measurements'][1]['case_id']='c2'; p['case_sampling']['c2']='unselected'
    elif bad=='different_operators': v['measurements'][1]['operators'][0]['activity_ids']=['file']
    elif bad=='conflicting_numbers': e['measurements'][1].update(lower=30.,upper=35.,value=None)
    elif bad=='quote': g['groups'][0]['evidence'][0]['quote']='Invented'
    elif bad=='overlap': g['groups']*=2
    elif bad=='same_case_components': g['groups'][0]['relationship']='same_case'
    with pytest.raises(ValueError):
        compile_durations(e,v,s,d,p,report_groups=g)
