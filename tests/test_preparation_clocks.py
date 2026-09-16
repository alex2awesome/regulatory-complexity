import copy
import pytest

from pipeline.procbench.audit_preparation_clocks import candidates,validate_preparation
from test_bayes_hierarchy import fixture,measurement


def inputs():
    e=fixture()
    e['measurements']=[measurement('file',ident='m1'),measurement('file',ident='m2')]
    rows=[dict(measurement_id=m['id'],phase='before_first_submission',start_event='unknown',
        end_event='first_submission',basis='stage_span',evidence=[dict(doc_id='document',quote='Evidence')],notes='')
        for m in e['measurements']]
    rows[0]['end_event']='unknown'
    group=dict(case_id='c1',measurement_ids=['m1','m2'],coverage='partial_disjoint_spans',
               evidence=[dict(doc_id='document',quote='Evidence')],notes='')
    return e,dict(program_id=e['program_id'],measurements=rows,serial_groups=[group],unresolved=[])


def test_candidates_and_group_identity_are_quote_checked():
    e,a=inputs()
    assert len(candidates(e))==2
    validate_preparation(a,e,[dict(id='document',text='Evidence')])
    e['measurements'][1]['case_id']='different case'
    with pytest.raises(ValueError,match='share one case'):
        validate_preparation(a,e,[dict(id='document',text='Evidence')])


def test_serial_groups_cannot_reuse_duration_or_reverse_pre_filing_boundary():
    e,a=inputs()
    second=copy.deepcopy(a['serial_groups'][0])
    a['measurements'][1]['end_event']='unknown'
    second['measurement_ids'].reverse()
    a['serial_groups'].append(second)
    with pytest.raises(ValueError,match='reuse the same duration'):
        validate_preparation(a,e,[dict(id='document',text='Evidence')])
    a['serial_groups'].pop()
    a['measurements'][0]['start_event']='complete_submission'
    with pytest.raises(ValueError,match='pre-filing span'):
        validate_preparation(a,e,[dict(id='document',text='Evidence')])


def test_first_filing_cannot_be_an_internal_boundary_of_pre_filing_serial_group():
    e,a=inputs()
    a['measurements'][0]['end_event']='first_submission'
    with pytest.raises(ValueError,match='final serial span'):
        validate_preparation(a,e)
