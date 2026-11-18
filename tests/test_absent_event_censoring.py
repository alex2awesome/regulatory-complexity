import copy
import math

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.absent_event_censoring import SCHEMA_VERSION, declaration_digest
from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy, duration_log_probability
from pipeline.procbench.compact_visit_trace import Block, CompactTrace, Operation, validate_operator
from pipeline.procbench.joint_duration_reports import (
    SCHEMA_VERSION as GROUP_SCHEMA, declaration_digest as group_digest)
from pipeline.procbench.run_visit_hierarchy import preflight_report
from procbench_fixtures import observation
from test_case_paths import cfg, path_data


def seal(p):
    for d in p['absent_event_censoring']:
        d['declaration_sha256']=declaration_digest(p['id'],d,p['observations'],p['routes'],p['case_path_scope'])
    for g in p.get('joint_duration_reports',[]):
        g['declaration_sha256']=group_digest(p['id'],g,p['observations'])


def fixture(grouped=False, selected=False):
    data=path_data();p=data['programs'][0];p['case_path_scope']={}
    pending=observation('pending_review','activity_event_clock',12.,None,case='a',activities=['review'])
    pending['operators'][0].update(start='process_start',event_occurrence='first')
    pending['observation_kind']='pending_right_censored'
    total=observation('total','whole_case_clock',8.,40.,case='a')
    p['observations']=[pending,total]
    if selected:
        for o in p['observations']:o['sampling']='delay_selected'
    p['absent_event_censoring']=[dict(schema_version=SCHEMA_VERSION,
        observation_id='pending_review',absent_paths_by_inventory={'inventory':['denied']},
        rationale='Fixture path explicitly ends without this event; pending does not imply eventual occurrence.')]
    if grouped:
        p['joint_duration_reports']=[dict(schema_version=GROUP_SCHEMA,id='timeline',case_id='a',
            observation_ids=['pending_review','total'],likelihood_kind='shared_log_scale_t4',
            assumption=dict(kind='perfectly_shared_log_error',relative_timings_exact_within_bounds=True,
                sensitivity_only=True,rationale='Declared fixture common-error sensitivity.'))]
    seal(p)
    return data


def test_activity_event_clock_is_not_the_duration_of_its_final_operation():
    trace=CompactTrace([Operation('first',None,'unknown','a'),Operation('second',None,'unknown','b')],
        [Block('serial',['first','second'])],np.array([[3.,7.],[2.,5.]]))
    op=dict(basis='activity_event_clock',start='process_start',activity_ids=['second'],event_occurrence='first')
    np.testing.assert_array_equal(trace.values(op),[10.,7.])
    np.testing.assert_array_equal(trace.values(dict(basis='single_visit_cycle',activity_ids=['second'])),[7.,5.])


@pytest.mark.parametrize('grouped',[False,True])
@pytest.mark.parametrize('selected',[False,True])
def test_pending_absent_path_keeps_case_weight_and_selection_normalization(grouped,selected):
    model=VisitHierarchy(fixture(grouped,selected),cfg(case_path_logit_sd=0.,selection_sd=float(selected)))
    p=model.programs[0];r=p['routes'][0]
    for z in np.random.default_rng(31).normal(size=(6,model.layout.size)):
        par=model.parameters(z)
        fast,detail=model._case_path_likelihood(p,z,par,0,details=True)
        slow=model.log_likelihood_reference(z,[0],parts=True)
        assert fast==pytest.approx(slow,abs=1e-12)
        direct=model.trace(p,z,par,0,path_index=1)
        total=p['observations'][1];value=direct.values(total['operators'][0])[0]
        expected=float(duration_log_probability(total['lower'],total['upper'],value,
            par['source'][0,model.sources.index(total['source_family'])],model.cfg.report_sd,model.cfg.contamination))
        assert detail['group_ll'][1].sum()==pytest.approx(expected,abs=1e-12)
        assert detail['case_weights']['a'][1]>0
        logprior=np.log(model.path_probabilities(r,z))
        likelihoods=detail['group_ll'].sum(axis=1)
        if selected:
            pop=model.trace(p,z,par,0,True)
            strength=abs(float(z[p['selection'][0]]))
            threshold,normalizers=model._selection_population_summary(p,pop,strength,0)
            from scipy.special import expit
            clocks=np.array([model.trace(p,z,par,0,path_index=i).event('initial_decision')[0]
                             for i in range(2)])
            h=expit((np.log(clocks)-threshold)/model.cfg.selection_width)
            weights=np.logaddexp(np.log1p(-h),strength+np.log(h))
            expected_case=logsumexp(logprior+likelihoods+weights)-logsumexp(logprior+normalizers)
        else:
            expected_case=logsumexp(logprior+likelihoods)
        assert fast['J__P:case:a']==pytest.approx(expected_case,abs=1e-12)


def test_completed_event_and_legacy_missing_operator_do_not_get_probability_one():
    data=fixture();p=data['programs'][0];del p['absent_event_censoring']
    legacy=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    z=np.zeros(legacy.layout.size)
    _,detail=legacy._case_path_likelihood(legacy.programs[0],z,legacy.parameters(z),0,details=True)
    assert detail['case_weights']['a'][1]==0.
    p['observations'][0].update(upper=20.,observation_kind='completed_interval')
    completed=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    z=np.zeros(completed.layout.size)
    _,detail=completed._case_path_likelihood(completed.programs[0],z,completed.parameters(z),0,details=True)
    assert detail['case_weights']['a'][1]==0.


def test_group_with_only_nonoccurring_pending_members_is_neutral_once():
    data=fixture(grouped=True);p=data['programs'][0]
    p['observations'][1]=copy.deepcopy(p['observations'][0]);p['observations'][1]['id']='total'
    d=copy.deepcopy(p['absent_event_censoring'][0]);d['observation_id']='total'
    p['absent_event_censoring'].append(d);seal(p)
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.));p=model.programs[0]
    z=np.zeros(model.layout.size)
    parts=model._joint_duration_group_parts(p,model.trace(p,z,model.parameters(z),0,path_index=1),model.parameters(z))
    assert parts=={'J__P:report_group:timeline':0.}


def test_marker_clock_support_and_available_nonzero_origin():
    data=fixture();p=data['programs'][0]
    p['routes'][0]['operations'][1]['markers']=['complete_submission']
    p['observations'][0]['operators']=[dict(basis='whole_case_clock',start='first_submission',end='first_complete_submission')]
    seal(p);model=VisitHierarchy(data,cfg(case_path_logit_sd=0.));z=np.zeros(model.layout.size)
    _,detail=model._case_path_likelihood(model.programs[0],z,model.parameters(z),0,details=True)
    assert detail['group_ll'][1,0]==0.
    assert np.isfinite(detail['group_ll'][0,0])


@pytest.mark.parametrize('bad',['null','extra','schema','duplicate','unknown_obs','completed','lower_only_completed',
    'finite_upper','population','bool_bound','bool_weight','cycle','missing_inventory','wrong_absence',
    'unknown_path','absent_everywhere','missing_origin','bad_digest','changed_structure','changed_evidence'])
def test_invalid_or_undeclared_absence_fails_closed(bad):
    data=fixture();p=data['programs'][0];d=p['absent_event_censoring'][0];o=p['observations'][0]
    if bad=='null':p['absent_event_censoring']=None
    elif bad=='extra':d['assumed_calibrated']=True
    elif bad=='schema':d['schema_version']='future'
    elif bad=='duplicate':p['absent_event_censoring'].append(copy.deepcopy(d))
    elif bad=='unknown_obs':d['observation_id']='unknown'
    elif bad=='completed':o['observation_kind']='completed_interval'
    elif bad=='lower_only_completed':o['observation_kind']='completed_lower_bound'
    elif bad=='finite_upper':o['upper']=30.
    elif bad=='population':o.update(case_id=None,statistic='median')
    elif bad=='bool_bound':o['lower']=True
    elif bad=='bool_weight':o['operator_weights']=[True]
    elif bad=='cycle':o['operators']=[dict(basis='single_visit_cycle',activity_ids=['review'])]
    elif bad=='missing_inventory':d['absent_paths_by_inventory']={}
    elif bad=='wrong_absence':d['absent_paths_by_inventory']['inventory']=['approved']
    elif bad=='unknown_path':d['absent_paths_by_inventory']['inventory']=['missing']
    elif bad=='absent_everywhere':o['operators'][0]['activity_ids']=['never_modeled']
    elif bad=='missing_origin':o['operators'][0]['start']='first_complete_submission'
    elif bad=='bad_digest':d['declaration_sha256']='0'*64
    elif bad=='changed_structure':p['routes'][0]['operations'][0]['task_type']='changed'
    elif bad=='changed_evidence':o['lower']=13.
    if bad not in {'null','unknown_obs','bad_digest','changed_structure','changed_evidence'}:seal(p)
    with pytest.raises(ValueError):VisitHierarchy(data,cfg(case_path_logit_sd=0.))


def test_compiled_contract_is_immutable_and_metadata_copied():
    data=fixture();data['programs'][0]['case_path_scope']={'a':['approved']}
    seal(data['programs'][0]);model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    z=np.zeros(model.layout.size);before=model.log_likelihood(z,[0])
    data['programs'][0]['observations'][0]['upper']=13.
    data['programs'][0]['absent_event_censoring'][0]['absent_paths_by_inventory']['inventory'].clear()
    data['programs'][0]['case_path_scope']['a'][:]=['denied']
    data['programs'][0]['routes'][0]['operations'][0]['markers'].clear()
    data['programs'][0]['routes'][0]['paths'][0]['blocks'][0]['operations'].clear()
    assert model.log_likelihood(z,[0])==before
    report=preflight_report(model)['absent_event_censoring']['J__P']
    report['declarations'][0]['rationale']='modified'
    assert model.absent_event_censoring_metadata()['J__P']['declarations'][0]['rationale']!='modified'


def test_preconstruction_scope_change_requires_new_digest():
    data=fixture();data['programs'][0]['case_path_scope']={'a':['approved']}
    with pytest.raises(ValueError,match='digest'):VisitHierarchy(data,cfg(case_path_logit_sd=0.))


def test_preconstruction_path_weight_change_requires_new_digest():
    data=fixture();data['programs'][0]['routes'][0]['paths'][0]['probability_weight']=17.
    with pytest.raises(ValueError,match='digest'):VisitHierarchy(data,cfg(case_path_logit_sd=0.))


def test_empty_opt_in_preserves_default_layout_and_likelihood():
    data=path_data();other=copy.deepcopy(data);other['programs'][0]['absent_event_censoring']=[]
    a=VisitHierarchy(data,cfg());b=VisitHierarchy(other,cfg())
    assert a.layout.size==b.layout.size
    for z in np.random.default_rng(23).normal(size=(8,a.layout.size)):
        assert a.log_likelihood(z,[0])==b.log_likelihood(z,[0])


@pytest.mark.parametrize('mutation',[{'start':'unknown'},{'activity_ids':['review','other']},
    {'event_occurrence':'whenever'},{'activity_selection':'first_present'},{'calibrated':True}])
def test_event_operator_rejects_unsupported_semantics(mutation):
    op=dict(basis='activity_event_clock',start='process_start',activity_ids=['review'],event_occurrence='first')
    op.update(mutation)
    with pytest.raises(ValueError):validate_operator(op)
