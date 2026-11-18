import copy
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import logsumexp
from scipy.stats import t

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy, duration_log_probability
from pipeline.procbench.joint_duration_reports import (
    SCHEMA_VERSION, declaration_digest, shared_log_error_probability)
from pipeline.procbench.run_visit_hierarchy import preflight_report
from procbench_fixtures import observation
from test_case_paths import cfg, path_data


def seal(p, group):
    group['declaration_sha256']=declaration_digest(p['id'],group,p['observations'])
    return group


def data_fixture(paths=False, fixed=False):
    data=path_data();p=data['programs'][0]
    p['case_path_scope']={}
    if not paths:
        r=p['routes'][0]
        r['blocks']=r.pop('paths')[0]['blocks']
        r['operations']=[op for op in r['operations'] if op['id']!='deny']
    p['observations']=[observation('total','whole_case_clock',10.,30.,case='a'),
        observation('filing','single_visit_cycle',1.,6.,case='a',activities=['file']),
        observation('other','whole_case_clock',12.,40.,case='b')]
    group=dict(schema_version=SCHEMA_VERSION,id='timeline',case_id='a',
        observation_ids=['total','filing'],likelihood_kind='shared_log_scale_t4',
        assumption=dict(kind='perfectly_shared_log_error',
            relative_timings_exact_within_bounds=True,sensitivity_only=True,
            rationale='Source-free common-clock-distortion sensitivity.'))
    p['joint_duration_reports']=[seal(p,group)]
    if fixed:
        from test_case_path_priors import declaration, seal as seal_prior
        entry=declaration({'approved':1.,'denied':4.})
        p['case_path_priors']={'a':{'inventory':seal_prior(p,'a','inventory',entry)}}
    return data


def test_shared_kernel_integrates_one_error_and_one_contamination_event():
    lo,hi,val=np.array([4.,10.]),np.array([8.,30.]),np.array([6.,18.])
    left=max(np.log(lo/val));right=min(np.log(hi/val))
    offset,scale,contamination=.17,.4,.13
    expected=quad(lambda e:(1-contamination)*t.pdf((e-offset)/scale,4)/scale
                  +contamination*t.pdf((e-offset)/2,4)/2,left,right,epsabs=1e-12)[0]
    actual=shared_log_error_probability(lo,hi,val,offset,scale,contamination)
    assert math.exp(actual)==pytest.approx(expected,abs=1e-12)
    wrong=sum(duration_log_probability(lo,hi,val,offset,scale,contamination))
    assert actual!=pytest.approx(wrong)


@pytest.mark.parametrize('contamination',[0.,.05,.4])
def test_singleton_equals_existing_duration_kernel_and_duplicates_do_not_square(contamination):
    ll=shared_log_error_probability([4.],[8.],[6.],.1,.25,contamination)
    assert ll==pytest.approx(float(duration_log_probability(4.,8.,6.,.1,.25,contamination)),abs=1e-14)
    assert shared_log_error_probability([4.,4.],[8.,8.],[6.,6.],.1,.25,contamination)==ll


def test_censoring_zero_and_impossible_relative_timing():
    assert shared_log_error_probability([0.,0.],[math.inf,math.inf],[3.,8.])==pytest.approx(0.)
    assert shared_log_error_probability([0.,0.],[1.,2.],[0.,0.])==0.
    assert shared_log_error_probability([1.],[2.],[0.])==-math.inf
    assert shared_log_error_probability([1.,10.],[2.,11.],[1.,1.],contamination=.99)==-math.inf
    # Touching intervals also have zero continuous error mass.
    assert shared_log_error_probability([1.,2.],[2.,3.],[1.,1.])==-math.inf
    expected=duration_log_probability(7.,None,5.)
    assert shared_log_error_probability([0.,7.],[math.inf,math.inf],[2.,5.])==pytest.approx(expected)


@pytest.mark.parametrize('paths,fixed,selection',[(False,False,0.),(True,False,0.),
                                              (True,True,0.),(True,True,1.)])
def test_group_replaces_members_and_path_prior_occurs_once(paths,fixed,selection):
    data=data_fixture(paths,fixed)
    if selection:
        p=data['programs'][0]
        for o in p['observations']:o['sampling']='delay_selected'
        seal(p,p['joint_duration_reports'][0])
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.,selection_sd=selection))
    p=model.programs[0]
    for z in np.random.default_rng(31).normal(size=(8,model.layout.size)):
        par=model.parameters(z)
        actual=model.log_likelihood(z,[0],parts=True)
        reference=model.log_likelihood_reference(z,[0],parts=True)
        assert actual.keys()==reference.keys()
        for k in actual: assert actual[k]==pytest.approx(reference[k],abs=1e-12)
        if not paths:
            assert set(actual)=={'J__P:report_group:timeline','J__P:other'}
            trace=model.trace(p,z,par,0)
            val=[trace.values(o['operators'][0])[p['case_index']['a']] for o in p['observations'][:2]]
            source=model.sources.index('source')
            expected=shared_log_error_probability([10.,1.],[30.,6.],val,
                                                 par['source'][0,source],model.cfg.report_sd,model.cfg.contamination)
            assert actual['J__P:report_group:timeline']==expected
        elif not selection:
            prior=np.array([.2,.8]) if fixed else np.array([.75,.25])
            terms=[]
            for j in range(2):
                trace=model.trace(p,z,par,0,path_index=j)
                terms.append(model._joint_duration_group_parts(p,trace,par)['J__P:report_group:timeline'])
            assert actual['J__P:case:a']==pytest.approx(logsumexp(np.log(prior)+terms),abs=1e-12)


def test_observation_order_and_member_order_do_not_change_target():
    data=data_fixture(True,True)
    other=copy.deepcopy(data);p=other['programs'][0]
    p['observations'].reverse();p['joint_duration_reports'][0]['observation_ids'].reverse()
    # Both declarations bind ordering; reseal the explicitly changed declaration.
    seal(p,p['joint_duration_reports'][0])
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.));reverse=VisitHierarchy(other,model.cfg)
    for z in np.random.default_rng(42).normal(size=(6,model.layout.size)):
        assert model.log_likelihood(z,[0])==pytest.approx(reverse.log_likelihood(z,[0]),abs=1e-12)


@pytest.mark.parametrize('bad',['null','dict','extra','schema','kind','assumption','unknown_case',
    'unknown_member','one_member','repeated_member','overlap','other_case','other_source',
    'population','count','operator_mixture','interval_union','bool_weight','bool_bound',
    'hash','context','changed_data'])
def test_bad_group_contracts_fail_closed(bad):
    data=data_fixture();p=data['programs'][0];g=p['joint_duration_reports'][0]
    if bad=='null':p['joint_duration_reports']=None
    elif bad=='dict':p['joint_duration_reports']={}
    elif bad=='extra':g['calibrated']=True
    elif bad=='schema':g['schema_version']='future'
    elif bad=='kind':g['likelihood_kind']='independent'
    elif bad=='assumption':g['assumption']['sensitivity_only']=False
    elif bad=='unknown_case':g['case_id']='missing'
    elif bad=='unknown_member':g['observation_ids'][0]='missing'
    elif bad=='one_member':g['observation_ids']=['total']
    elif bad=='repeated_member':g['observation_ids']=['total','total']
    elif bad=='overlap':
        duplicate=copy.deepcopy(g);duplicate['id']='second';seal(p,duplicate)
        p['joint_duration_reports'].append(duplicate)
    elif bad=='other_case':g['observation_ids']=['total','other']
    elif bad=='other_source':p['observations'][1]['source_family']='other_source'
    elif bad=='population':p['observations'][1].update(case_id=None,statistic='median')
    elif bad=='count':p['observations'][1]['operators']=[dict(basis='operation_count')]
    elif bad=='operator_mixture':
        o=p['observations'][1];o['operators']*=2;o['operator_weights']=[.5,.5]
    elif bad=='interval_union':p['observations'][1]['report_intervals']=[[1.,2.],[3.,6.]]
    elif bad=='bool_weight':p['observations'][1]['operator_weights']=[True]
    elif bad=='bool_bound':p['observations'][1]['lower']=True
    elif bad=='hash':g['declaration_sha256']='0'*64
    elif bad=='context':p['id']='different'
    elif bad=='changed_data':p['observations'][1]['lower']=2.
    if bad not in {'hash','context','changed_data','unknown_member'}:seal(p,g)
    with pytest.raises(ValueError):VisitHierarchy(data,cfg(case_path_logit_sd=0.))


def test_group_factor_key_collision_fails_before_sampling():
    data=data_fixture();p=data['programs'][0]
    p['observations'][2]['id']='report_group:timeline'
    with pytest.raises(ValueError,match='factor key collision'):VisitHierarchy(data,cfg())


def test_empty_groups_are_default_noop_and_metadata_is_deepcopied():
    data=data_fixture();plain=copy.deepcopy(data);del plain['programs'][0]['joint_duration_reports']
    empty=copy.deepcopy(plain);empty['programs'][0]['joint_duration_reports']=[]
    a=VisitHierarchy(plain,cfg());b=VisitHierarchy(empty,cfg())
    for z in np.random.default_rng(2).normal(size=(4,a.layout.size)):
        assert a.log_likelihood(z,[0])==b.log_likelihood(z,[0])
    model=VisitHierarchy(data,cfg());pre=preflight_report(model)
    assert pre['joint_duration_reports']['J__P']['integrated_error_coordinates']==0
    assert pre['joint_duration_reports']['J__P']['calibration_verified'] is False
    pre['joint_duration_reports']['J__P']['groups'][0]['observation_ids'].append('fake')
    assert len(model.programs[0]['joint_duration_reports'][0]['members'])==2


def test_digest_bound_group_is_not_mutated_through_callers_input():
    data=data_fixture(True,True);model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    z=np.zeros(model.layout.size);before=model.log_likelihood(z,[0])
    metadata=model.joint_duration_report_metadata()
    data['programs'][0]['observations'][0].update(lower=900.,case_id='changed')
    data['programs'][0]['joint_duration_reports'][0]['observation_ids'].reverse()
    assert model.log_likelihood(z,[0])==before
    assert model.joint_duration_report_metadata()==metadata


def test_existing_strict_conditional_frame_does_not_accept_new_group_field():
    from test_conditional_case_frames import frame_data
    data=frame_data()
    data['programs'][0]['joint_duration_reports']=[]
    with pytest.raises(ValueError):VisitHierarchy(data,cfg())
