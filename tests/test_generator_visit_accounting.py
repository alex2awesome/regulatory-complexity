import copy

import pytest

from benchmark.synth.generator import simulate


def inputs(version=None):
    knobs=dict(as_of='2026-09-15',p_abandon_total=0,max_rework_rounds=1,sim_window_days=760)
    if version is not None:
        knobs['visit_accounting_version']=version
    world=dict(seed=43,knobs=knobs)
    base=dict(optional=False,p_occurs=None,actor='agency',per_case=True,flow_gate='always',
        blocking=True,occasion='online',fee=None,element_ref=None,visibility='applicant_facing',
        artifacts_out=[],rework=None,timing=dict(median_days=10,p90_days=20))
    acts=[dict(copy.deepcopy(base),id=aid) for aid in ['file','review','decide']]
    acts[0].update(actor='applicant',fee=dict(amount=100,label='Application fee',refundable=False))
    acts[1]['rework']=dict(p_trigger=1,back_to='file')
    acts[2].update(element_ref='E1',artifacts_out=['permit'],timing=dict(median_days=1,p90_days=2))
    process=dict(model_id='test__permit',activities=acts,terminal_artifact='permit',denial_rate=0,p_appeal_if_denied=0)
    return world,process,dict(effective='2026-01-01')


def test_repeat_visit_is_not_the_number_of_times_that_operation_triggered_a_loop(monkeypatch):
    monkeypatch.setattr(simulate,'sample_days',lambda rng,median,p90:int(median))
    legacy,_=simulate.simulate_process(*inputs(),1)
    corrected,_=simulate.simulate_process(*inputs(2),1)
    old,new=legacy[0],corrected[0]
    assert [s['a'] for s in old['path']]==[s['a'] for s in new['path']]==['file','review','file','review','decide']
    assert [s['r'] for s in old['path']]==[0,0,0,1,0]
    assert [s['visit_index'] for s in new['path']]==[0,0,1,1,0]
    assert [s['loop_triggers_before'] for s in new['path']]==[0,0,0,1,0]
    assert old['elapsed_days']==38 and new['elapsed_days']==35
    assert old['fees_paid']==200  # reproduce, do not rewrite, the legacy defect
    assert new['fees_paid']==100
    assert [s['fee_charged_dollars'] for s in new['path']]==[100,0,0,0,0]
    assert new['total_rework_rounds']==1


def test_inspection_fees_can_be_per_visit_without_recharging_base_fees(monkeypatch):
    monkeypatch.setattr(simulate,'sample_days',lambda rng,median,p90:int(median))
    world,process,rule=inputs(2)
    process['activities'][0]['fee']['label']='Site inspection fee'
    records,_=simulate.simulate_process(world,process,rule,1)
    assert records[0]['fees_paid']==200
    assert [s['fee_charged_dollars'] for s in records[0]['path']]==[100,0,100,0,0]


def test_nonblocking_correction_cannot_start_before_its_trigger_finishes(monkeypatch):
    monkeypatch.setattr(simulate,'sample_days',lambda rng,median,p90:int(median))
    for version in (1,2):
        world,process,rule=inputs(version)
        process['activities'][1]['blocking']=False
        records,_=simulate.simulate_process(world,process,rule,1)
        record=records[0]
        trigger,repeat=record['path'][1:3]
        assert record['rework_events']==[dict(activity_id='review',back_to='file',
            triggered_at=trigger['e'],round_at_checkpoint=1)]
        if version==2:
            assert repeat['s']>=trigger['e']
        else:
            assert repeat['s']<trigger['e']  # legacy behavior deliberately preserved


def test_reported_fees_never_include_a_charge_after_the_observation_date(monkeypatch):
    monkeypatch.setattr(simulate,'sample_days',lambda rng,median,p90:int(median))
    world,process,rule=inputs(2)
    world['knobs']['as_of']='2026-01-25'
    records,_=simulate.simulate_process(world,process,rule,5)
    for record in records:
        known=sum(s['fee_charged_dollars'] for s in record['path'] if s['e']<=world['knobs']['as_of'])
        assert record['fees_paid_by_observation']==known
        assert known<=record['fees_paid']


def test_legacy_is_default_only_for_old_worlds_and_unknown_versions_fail():
    from benchmark.synth.generator.world import DEFAULT_KNOBS
    assert DEFAULT_KNOBS['visit_accounting_version']==2
    assert 'visit_accounting_version' not in inputs()[0]['knobs']
    with pytest.raises(ValueError,match='version'):
        simulate.simulate_process(*inputs(900),1)


def test_build_refuses_to_delete_or_rewrite_an_existing_world(tmp_path):
    from benchmark.synth.generator.build import build
    sentinel=tmp_path/'world.json'
    sentinel.write_text('{"important": "existing evaluation"}')
    before=sentinel.read_bytes()
    with pytest.raises(ValueError,match='Preserving existing'):
        build('WNEW',100,str(tmp_path),{})
    assert sentinel.read_bytes()==before
