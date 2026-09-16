import random

from benchmark.synth.generator.visibility import reveals_for


def test_dashboard_declares_actual_clock_and_uses_decided_median_denominator():
    process=dict(stat_id='S01',activities=[],prior_version=None,terminal_artifact='letter')
    summary=dict(elapsed_days=dict(median=128,n=174),n_completed=182,n_applicants=200,
                 outcomes=dict(approved=137,denied=37,abandoned=8,in_progress=18),share_with_rework=.65)
    reveals,hidden,notes=reveals_for('official_stats',{'knobs':{}},process,{},
                                    {'S01':{}},summary,random.Random(4),False,False)
    row=next(r for r in reveals if r['field']=='timing')
    assert row['measurement_clock']==dict(start='beginning_preparation_or_filing',end='last_recorded_decision',
        population='uncensored_approved_or_denied',statistic='median',sample_size=174)
    assert '174 decided cases' in row['value']
    assert '182' not in row['value']
    assert 'beginning preparation/filing' in row['value']
    assert 'last recorded approval or denial' in row['value']
    assert 'not a clock through later closeout' in row['value']


def test_clock_audit_separates_repeat_decisions_and_never_relabels_legacy_elapsed():
    from pipeline.procbench.audit_benchmark_clocks import record_clocks
    process=dict(terminal_artifact='permit',activities=[dict(id='decision',element_ref='E1',
        visibility='applicant_facing',artifacts_out=['permit'])])
    record=dict(arrived='2026-01-01',elapsed_days=20,path=[
        dict(a='decision',s='2026-01-05',e='2026-01-10'),
        dict(a='decision',s='2026-01-15',e='2026-01-21')])
    clocks=record_clocks(process,record)
    assert clocks['first_decision_days']==9
    assert clocks['last_decision_days']==20
    assert clocks['decision_visits']==2
    assert record['elapsed_days']==20


def test_new_generator_event_clocks_keep_censoring_and_cohorts_separate():
    from benchmark.synth.generator.simulate import event_clock,event_timing_summary
    first=event_clock('2026-01-01','2026-01-10','approved','2026-01-15')
    last=event_clock('2026-01-01','2026-01-21','denied','2026-01-15')
    absent=event_clock('2026-01-01',None,None,'2026-01-15')
    assert first['elapsed_days']==9 and first['outcome']=='approved' and not first['censored']
    assert last['elapsed_days']==20 and last['outcome']=='in_progress' and last['censored']
    assert last['provisional_outcome']=='denied'
    assert absent['elapsed_days'] is None and absent['censored'] is None
    rows=[dict(outcome='in_progress',event_clocks=dict(initial_decision=first,last_decision=last)),
          dict(outcome='abandoned',event_clocks=dict(initial_decision=absent,last_decision=absent))]
    initial=event_timing_summary(rows,'initial_decision')
    final=event_timing_summary(rows,'last_decision')
    assert initial['n']==1 and initial['median']==9 and initial['observed_outcomes']=={'approved':1}
    assert final['n']==0 and final['median'] is None and final['n_censored']==1 and final['n_no_event']==1


def test_empty_dashboard_cohort_does_not_report_a_zero_day_median():
    process=dict(stat_id='S01',activities=[],prior_version=None,terminal_artifact='letter')
    summary=dict(elapsed_days=dict(median=0,n=0),n_completed=1,n_applicants=2,
                 outcomes=dict(abandoned=1,in_progress=1),share_with_rework=0)
    reveals,_,_=reveals_for('official_stats',{'knobs':{}},process,{},
                           {'S01':{}},summary,random.Random(4),False,False)
    assert not any(row['field']=='timing' for row in reveals)
    assert any('no duration is reported' in row['value'] for row in reveals)


def test_audit_keeps_first_visit_and_process_quantile_clocks_separate():
    activity=dict(id='a',name='review',visibility='applicant_facing',element_ref='E1',
        artifacts_out=['letter'],timing=dict(median_days=5),fee=None)
    process=dict(stat_id='S01',activities=[activity],prior_version=None,terminal_artifact='letter')
    summary=dict(elapsed_days=dict(median=128,p90=199,n=174),per_activity_median_days={'a':5},
        observed_first_visit_clocks=dict(as_of='2026-01-31',activities={'a':dict(n=12,median=7,p90=11)}))
    reveals,_,_=reveals_for('audit_excerpt',{'knobs':{}},process,{},
                            {'S01':{}},summary,random.Random(4),False,False)
    process_row=next(r for r in reveals if r['ref']=='process')
    assert '90th percentile 199 days' in process_row['value']
    assert '20 percent' not in process_row['value'] and 'intake' not in process_row['value']
    assert process_row['measurement_clock']['end']=='last_recorded_decision'
    step_row=next(r for r in reveals if r['ref']=='a')
    assert 'median 7 days' in step_row['value']
    assert step_row['measurement_clock']['basis']=='single_visit_cycle'
    assert step_row['measurement_clock']['sample_size']==12


def test_first_visit_observation_never_reads_future_completion_or_relabels_repeat():
    from benchmark.synth.generator.simulate import observed_first_visit_summaries
    from benchmark.synth.generator.visibility import first_visit_timing
    records=[dict(path=[dict(a='a',s='2026-01-01',e='2026-01-04'),
                        dict(a='a',s='2026-01-10',e='2026-01-12'),
                        dict(a='b',s='2026-01-10',e='2026-02-10')])]
    observed=observed_first_visit_summaries(records,'2026-01-31')
    assert observed=={'a':dict(n=1,median=3,p90=3)}
    activity=dict(id='b',timing=dict(median_days=10))
    summary=dict(observed_first_visit_clocks=dict(as_of='2026-01-31',activities=observed))
    value,clock=first_visit_timing(summary,activity)
    assert value==10 and clock['statistic']=='forecast'


def test_delayed_persona_is_completed_and_visit_sums_do_not_become_stage_spans():
    from benchmark.synth.generator.visibility import persona_from
    activities=[dict(id=aid,name=aid,visibility='applicant_facing',element_ref='E1',
                     artifacts_out=['permit'] if aid=='decide' else []) for aid in ['file','decide','later']]
    process=dict(activities=activities,terminal_artifact='permit')
    record=dict(arrived='2026-01-01',elapsed_days=19,total_rework_rounds=1,fees_paid=5,
        outcome='approved',provisional_outcome=None,path=[
            dict(a='file',s='2026-01-01',e='2026-01-04'),
            dict(a='file',s='2026-01-10',e='2026-01-12'),
            dict(a='decide',s='2026-01-19',e='2026-01-20'),
            dict(a='later',s='2026-01-21',e='2026-02-10')],applicant_id='case1')
    world=dict(knobs=dict(as_of='2026-01-31',p_wrong_fact_user=0))
    persona=persona_from(world,process,'delayed',record,random.Random(81))
    assert 'decision eventually arrived' in persona['why_posting']
    assert '19' not in persona['why_posting']  # no hidden exact duration leaks into noisy narrative
    assert persona['case_outcome']=='approved'
    reported=persona['reported_timeline']
    assert reported['measurement_clock']['end']=='last_recorded_decision'
    first=next(s for s in reported['steps'] if s['ref']=='file')
    assert first['true_days']==5  # sum 3+2, not the first-to-last 11-day span
    assert first['measurement_clock']['basis']=='sum_visit_cycles'
    assert not any(s['ref']=='later' for s in reported['steps'])


def test_renderer_receives_only_public_reported_persona_numbers_without_mutation():
    import copy
    from benchmark.synth.render.prepare_batch import renderer_spec
    spec=dict(persona=dict(true_timeline=dict(total_days=70),reported_timeline=dict(total='112 days',
        total_days_reported=91,steps=[dict(ref='a',reported='28 days',true_days=10)])))
    original=copy.deepcopy(spec)
    rendered=renderer_spec(spec)
    assert 'true_timeline' not in rendered['persona']
    report=rendered['persona']['reported_timeline']
    assert report==dict(total='112 days',steps=[dict(ref='a',reported='28 days')])
    assert spec==original
