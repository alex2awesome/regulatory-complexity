import copy

import pytest

from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.effective_evidence import evidence_digest
from test_compile_visit_durations import inputs
from test_effective_evidence import review_for, row


def gated_inputs(disposition='admitted'):
    e,v,s,d,p=inputs()
    review=review_for(e,d,[row('m1',disposition,quotes=[dict(doc_id='document',quote='Evidence')])])
    bindings=dict(schema_version='effective-evidence-sidecar-bindings/1',
                  evidence_sha256=evidence_digest(e),sidecar_sha256=dict(
                      visit_audit=evidence_digest(v),semantic_audit=evidence_digest(s)))
    return e,v,s,d,p,review,bindings


def test_admitted_review_reaches_existing_compiler_with_provenance():
    e,v,s,d,p,r,b=gated_inputs()
    original=copy.deepcopy(e)
    result=compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b)
    assert e==original
    assert result['coverage']['informative_elapsed']==1
    assert result['effective_review']['counts']['admitted']==1
    assert result['effective_evidence']==e
    observation=copy.deepcopy(result['observations'][0])
    assert observation['provenance'].pop('gate_ids')==['["three-family.v1","m1"]']
    assert observation==compile_durations(e,v,s,d,p)['observations'][0]


@pytest.mark.parametrize('disposition',['held','out_of_scope','residual_only'])
def test_gate_prevents_informative_consumption_despite_valid_old_sidecars(disposition):
    e,v,s,d,p,r,b=gated_inputs(disposition)
    p.update(retain_unsupported=True,residual_reference=dict(median_days=7.,log_scale=3.))
    result=compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b)
    assert result['coverage']['informative_elapsed']==0
    assert result['coverage']['accounted_elapsed']==1
    if disposition=='residual_only':
        assert result['observations'][0]['statistic']=='report_only'
        assert all(op['basis']=='unmodeled_duration' for op in result['observations'][0]['operators'])
    else:
        assert not result['observations']
        assert result['dispositions'][0]['status']=='review_'+disposition


def test_missing_or_changed_downstream_sidecars_fail_closed():
    e,v,s,d,p,r,b=gated_inputs()
    with pytest.raises(ValueError,match='Reviewed sidecars'):
        compile_durations(e,v,s,d,p,effective_review=r)
    s['measurements'][0]['notes']='Changed judgment after review'
    with pytest.raises(ValueError,match='Reviewed sidecars'):
        compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b)
    with pytest.raises(ValueError,match='require an effective review'):
        compile_durations(e,v,s,d,p,review_sidecar_bindings=b)


def test_numeric_correction_changes_actual_compiled_interval_not_only_sidecar():
    e,v,s,d,p=inputs()
    d[0]['text']='Evidence: review took 30 days.'
    m=e['measurements'][0]
    m['quote']=d[0]['text']
    quote=dict(doc_id='document',quote=d[0]['text'])
    change=dict(field='value',old=m['value'],new=30.,reason='Wrong transcribed number',
                source_quotes=[quote],source_value_text='30')
    r=review_for(e,d,[row('m1',quotes=[quote],changes=[change])])
    corrected=copy.deepcopy(e)
    corrected['measurements'][0]['value']=30.
    b=dict(schema_version='effective-evidence-sidecar-bindings/1',
           evidence_sha256=evidence_digest(corrected),sidecar_sha256=dict(
               visit_audit=evidence_digest(v),semantic_audit=evidence_digest(s)))
    result=compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b)
    assert result['observations'][0]['lower']==29.5
    assert result['observations'][0]['upper']==30.5
    assert e['measurements'][0]['value']==12.
    assert result['effective_review']['requires_downstream_review_measurement_ids']==['m1']


def test_count_sidecars_cannot_bypass_measurement_only_gate():
    e,v,s,d,p,r,b=gated_inputs()
    with pytest.raises(ValueError,match='Count sidecars need their own'):
        compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b,
                          count_audit={'count_claims':[]},burden_channels=('count',))


def test_excluded_source_cannot_change_admitted_case_sampling():
    from test_burden_channels_compile import ledger
    e,v,s,d,_=ledger()
    d.append(dict(id='agency_document',text='Evidence'))
    e['measurements'][1].update(doc_id='agency_document',source_family='agency_document')
    p=dict(source_type_sampling={'forum':'delay_selected'},default_case_sampling='unselected')
    r=review_for(e,d,[row(m['id'],'admitted' if m['id']=='m1' else 'held',
        quotes=[dict(doc_id=m['doc_id'],quote=m['quote'])]) for m in e['measurements']])
    b=dict(schema_version='effective-evidence-sidecar-bindings/1',
           evidence_sha256=evidence_digest(e),sidecar_sha256=dict(
               visit_audit=evidence_digest(v),semantic_audit=evidence_digest(s)))
    result=compile_durations(e,v,s,d,p,effective_review=r,review_sidecar_bindings=b,
        burden_channels=('fee','effort'),source_family_kinds={
            'document':'forum_thread','agency_document':'program_page'})
    assert result['observations'][0]['sampling']=='delay_selected'
    assert len(result['source_type_sampling']['case_decisions']['c1']['sources'])==1
    for channel in ('fee','effort'):
        counts=result['coverage']['burden'][channel]
        assert counts['claims']==counts['retained_with_disposition']==2
        assert counts['observations']==counts['route_inputs']==0
