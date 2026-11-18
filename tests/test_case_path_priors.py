"""Fixed case priors reuse V6's existing JOINT case likelihood; no real sources."""
import copy
import hashlib
import json

import numpy as np
import pytest
from scipy.special import logsumexp

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy
from pipeline.procbench.case_path_priors import SCHEMA_VERSION, declaration_digest
from pipeline.procbench.run_visit_hierarchy import preflight_report
from procbench_fixtures import observation
from test_case_paths import cfg, path_data


def seal(p, case, route, entry):
    entry['declaration_sha256']=declaration_digest(p['id'],case,route,entry)
    return entry


def declaration(weights, **kwargs):
    return dict(schema_version=SCHEMA_VERSION, interpretation='process_path',
        weights=weights, basis='declared_sensitivity', rationale='Source-free sensitivity fixture.',
        unknown_or_unlisted_path_id=None,
        exhaustive_scope_reason='The synthetic fixture defines these as its exhaustive paths.',
        actor_assignment=None, **kwargs)


def process_data():
    data=path_data(); p=data['programs'][0]
    p['case_path_scope']={}
    p['observations']=[observation('clock','whole_case_clock',6.,18.,case='a'),
                       observation('count','operation_count',3,3,case='a'),
                       observation('other','whole_case_clock',10.,30.,case='b')]
    entry=declaration({'approved':1.,'denied':9.})
    p['case_path_priors']={'a':{'inventory':seal(p,'a','inventory',entry)}}
    return data


def actor_data():
    data=process_data(); p=data['programs'][0]
    p['observations']=[observation('clock','whole_case_clock',6.,18.,case='a')]
    route=p['routes'][0]
    route['operations']=route['operations'][:1]+[
        dict(id='known_review',actor_id='J:Review',actor_role='agency',task_type='decision',
             markers=['decision'],payer_work=False,agency_work=True),
        dict(id='unknown_review',actor_id=None,actor_role='unknown',task_type='decision',
             markers=['decision'],payer_work=False,agency_work=True)]
    route['paths']=[dict(id='known',probability_weight=4.,blocks=[
        dict(id='known_block',operations=['file','known_review'])]),
        dict(id='unknown',probability_weight=1.,blocks=[
        dict(id='other_block_name',operations=['file','unknown_review'])])]
    entry=declaration({'known':1.,'unknown':3.})
    entry.update(interpretation='actor_assignment',unknown_or_unlisted_path_id='unknown',
        exhaustive_scope_reason=None,actor_assignment=dict(id='decision_actor',
            logical_phase_id='decision',candidate_operations=dict(known='known_review',unknown='unknown_review')))
    p['case_path_priors']={'a':{'inventory':seal(p,'a','inventory',entry)}}
    return data


def test_one_fixed_prior_over_joint_reports_not_a_prior_per_report():
    model=VisitHierarchy(process_data(),cfg(case_path_logit_sd=0.))
    p=model.programs[0]; z=np.random.default_rng(421).normal(size=model.layout.size)
    par=model.parameters(z)
    parts,detail=model._case_path_likelihood(p,z,par,0,details=True)
    columns=[i for i,o in enumerate(p['observations']) if o['case_id']=='a']
    prior=np.log([.1,.9]); terms=detail['group_ll'][:,columns]
    expected=logsumexp(prior+terms.sum(axis=1))
    assert parts['J__P:case:a']==pytest.approx(expected,abs=1e-12)
    wrong_independent=sum(logsumexp(prior+terms[:,i]) for i in range(len(columns)))
    wrong_repeated=logsumexp(len(columns)*prior+terms.sum(axis=1))
    assert expected!=pytest.approx(wrong_independent,abs=1e-6)
    assert expected!=pytest.approx(wrong_repeated,abs=1e-6)
    np.testing.assert_allclose(detail['case_weights']['a'],np.exp(prior+terms.sum(axis=1)-expected))
    # An undeclared case retains the population prior; the fixed case cannot
    # silently teach population prevalence.
    np.testing.assert_array_equal(model.path_probabilities(p['routes'][0],z),detail['probabilities'])
    assert detail['probabilities']==pytest.approx([.75,.25])


@pytest.mark.parametrize('selection',[0.,1.])
def test_fixed_case_priors_scalar_vectorized_and_observation_order(selection):
    data=process_data()
    if selection:
        for o in data['programs'][0]['observations']:o['sampling']='delay_selected'
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.,selection_sd=selection))
    reverse=copy.deepcopy(data);reverse['programs'][0]['observations'].reverse()
    other=VisitHierarchy(reverse,model.cfg)
    for z in np.random.default_rng(71).normal(size=(6,model.layout.size)):
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-11)
        assert model.log_likelihood(z,[0])==pytest.approx(other.log_likelihood(z,[0]),abs=1e-11)


def test_explicit_scope_alone_excludes_paths_and_adds_no_coordinates():
    data=process_data();p=data['programs'][0]
    p['case_path_scope']={'a':['approved']}
    entry=p['case_path_priors']['a']['inventory'];entry['weights']={'approved':12.}
    seal(p,'a','inventory',entry)
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    legacy=copy.deepcopy(data);del legacy['programs'][0]['case_path_priors']
    old=VisitHierarchy(legacy,model.cfg)
    assert model.layout.size==old.layout.size
    for z in np.random.default_rng(72).normal(size=(5,model.layout.size)):
        assert model.log_likelihood(z,[0])==old.log_likelihood(z,[0])


@pytest.mark.parametrize('bad',[
    'null','list','unknown_case','unknown_inventory','missing_inventory','plain_inventory',
    'missing_path','extra_path','bool_weight','zero_weight','negative_weight',
    'nan_weight','infinite_weight','string_weight','unsupported_basis','no_reason',
    'extra_field','wrong_schema','hash_mismatch','context_mismatch','learned_logits'])
def test_bad_fixed_declarations_fail_before_sampling(bad):
    data=process_data();p=data['programs'][0];entry=p['case_path_priors']['a']['inventory']
    config=cfg(case_path_logit_sd=0.)
    if bad=='null':p['case_path_priors']=None
    elif bad=='list':p['case_path_priors']=[]
    elif bad=='unknown_case':p['case_path_priors']['missing']=p['case_path_priors'].pop('a')
    elif bad=='unknown_inventory':p['case_path_priors']['a']['missing']=p['case_path_priors']['a'].pop('inventory')
    elif bad=='missing_inventory':p['case_path_priors']['a']={}
    elif bad=='plain_inventory':
        route=p['routes'][0];route['blocks']=route.pop('paths')[0]['blocks']
        route['operations']=route['operations'][:-1]
    elif bad=='missing_path':del entry['weights']['denied']
    elif bad=='extra_path':entry['weights']['extra']=1.
    elif bad.endswith('_weight'):
        entry['weights']['approved']={'bool_weight':True,'zero_weight':0.,'negative_weight':-1.,
            'nan_weight':float('nan'),'infinite_weight':float('inf'),'string_weight':'1'}[bad]
    elif bad=='unsupported_basis':entry['basis']='hash_reviewed_empirical_calibration'
    elif bad=='no_reason':entry['exhaustive_scope_reason']=''
    elif bad=='extra_field':entry['llm_confidence']=.99
    elif bad=='wrong_schema':entry['schema_version']='future'
    elif bad=='hash_mismatch':entry['declaration_sha256']='0'*64
    elif bad=='context_mismatch':entry['declaration_sha256']=declaration_digest(p['id'],'b','inventory',entry)
    elif bad=='learned_logits':config=cfg()
    if bad not in {'hash_mismatch','context_mismatch','nan_weight','infinite_weight'}:
        seal(p,'a','inventory',entry)
    with pytest.raises(ValueError):VisitHierarchy(data,config)


def test_digest_binds_weights_and_context_without_mutating_source_data():
    data=process_data();snapshot=copy.deepcopy(data)
    model=VisitHierarchy(data,cfg(case_path_logit_sd=0.))
    assert data==snapshot
    report=model.case_path_prior_report()
    report['J__P']['a']['inventory']['declaration']['weights']['approved']=999.
    assert model.programs[0]['case_path_priors']['a']['inventory']['declaration']['weights']['approved']==1.
    p=data['programs'][0];e=p['case_path_priors']['a']['inventory']
    assert declaration_digest(p['id'],'a','inventory',e)!=declaration_digest(p['id'],'b','inventory',e)
    e['weights']['approved']=2.
    with pytest.raises(ValueError,match='digest'):VisitHierarchy(data,cfg(case_path_logit_sd=0.))


def test_actor_only_guard_and_zero_effect_symmetry_at_equal_latent_durations():
    model=VisitHierarchy(actor_data(),cfg(case_path_logit_sd=0.,operation_sd=0.,agency_sd=0.))
    p=model.programs[0];z=np.zeros(model.layout.size)
    _,detail=model._case_path_likelihood(p,z,model.parameters(z),0,details=True)
    assert detail['case_weights']['a']==pytest.approx([.25,.75])
    assert model.path_probabilities(p['routes'][0],z)==pytest.approx([.8,.2])
    # This is a conditional symmetry check at equal latent durations, not a
    # false assertion that independently sampled counterfactual noises match.
    assert len(model.case_path_prior_report()['J__P'])==1


@pytest.mark.parametrize('bad',['unknown_omitted','unknown_named','no_map','wrong_map',
    'changed_task','changed_schedule','changed_fee','second_assignment','operation_effect','phases','dwells'])
def test_actor_assignment_cannot_hide_structure_or_unknown_identity(bad):
    data=actor_data();p=data['programs'][0];e=p['case_path_priors']['a']['inventory'];r=p['routes'][0]
    config=cfg(case_path_logit_sd=0.,operation_sd=0.)
    if bad=='unknown_omitted':e.update(unknown_or_unlisted_path_id=None,exhaustive_scope_reason='Unsupported claim of certainty.')
    elif bad=='unknown_named':r['operations'][-1].update(actor_role='agency',actor_id='MadeUp')
    elif bad=='no_map':e['actor_assignment']=None
    elif bad=='wrong_map':e['actor_assignment']['candidate_operations']['unknown']='file'
    elif bad=='changed_task':r['operations'][-1]['task_type']='other'
    elif bad=='changed_schedule':r['paths'][-1]['blocks'][0]['edges']=[]
    elif bad=='changed_fee':r['operations'][-1]['fee']=10.
    elif bad=='second_assignment':e['actor_assignment']['second_assignment']={}
    elif bad=='operation_effect':config=cfg(case_path_logit_sd=0.)
    elif bad=='phases':config=cfg(case_path_logit_sd=0.,operation_sd=0.,within_visit_phases=True)
    elif bad=='dwells':config=cfg(case_path_logit_sd=0.,operation_sd=0.,inter_operation_dwell=True)
    seal(p,'a','inventory',e)
    with pytest.raises(ValueError):VisitHierarchy(data,config)


def test_preflight_and_posterior_expose_conditional_assignment_not_calibration():
    model=VisitHierarchy(actor_data(),cfg(case_path_logit_sd=0.,operation_sd=0.,chains=2,warmup=1,draws=12))
    preflight=preflight_report(model)
    assert preflight['fixed_case_path_priors']['J__P']['a']['inventory']['calibration_verified'] is False
    states,routes,ll,_=model.sample();report=model.report(states,routes,ll)
    row=report['programs']['J__P']['fixed_case_path_assignments']['a']['inventory']
    assert sum(row['posterior_mean_weights_given_inventory'].values())==pytest.approx(1.)
    assert row['normalized_prior_weights']==pytest.approx({'known':.25,'unknown':.75})
    assert row['draws_given_inventory']==24
    assert row['calibration_verified'] is False
    assert any(':case_assignment:a:' in k for k in report['diagnostics'])


def test_default_target_sampler_and_full_report_replay_prechange_digest():
    model=VisitHierarchy(path_data(),cfg(chains=2,warmup=2,draws=12,seed=2026092401))
    states,routes,ll,_=model.sample();report=model.report(states,routes,ll)
    digest=lambda a:hashlib.sha256(a.tobytes()).hexdigest()
    assert digest(states)=='9567e27961012410887d9c03aab662ae75f863241173f3b62a6af25cd5622e35'
    assert digest(routes)=='5d89f056865052bcb89c910d2d62872e029fb273c3db03f8968a52a41593c1b5'
    assert digest(ll)=='9d4810a5ac0328b678fc9d148f2308dc00c070ffb2cd1ec107885ae702dcc32f'
    # The default-off transition flag is new metadata, not a target or RNG
    # change. Require its default explicitly, then replay the entire legacy
    # report rather than replacing the digest with a newly observed value.
    assert report['config'].pop('case_scale_sampler') == 'blocked'
    assert hashlib.sha256(json.dumps(report,sort_keys=True,allow_nan=False).encode()).hexdigest()==(
        '70b3e3f5d96238ecfdcd3a57350b901623d823abca8aa74a70371280dab7689a')


def test_single_clock_conditional_frame_guard_is_not_relaxed():
    from test_conditional_case_frames import frame_data,frame_config
    data=frame_data();data['programs'][0]['case_path_priors']={}
    with pytest.raises(ValueError,match='bounded fields'):
        VisitHierarchy(data,frame_config())
