import copy
from dataclasses import replace

import numpy as np
import pytest
from scipy.special import roots_hermitenorm

from pipeline.procbench.bayes_trace_hierarchy import Config,VisitHierarchy,duration_log_probability
from test_trace_hierarchy import data_fixture,observation


def phase_fixture():
    data=data_fixture()
    for basis,lo,hi in [('wait_elapsed',4.,9.),('service_elapsed',.01,.02)]:
        row=observation(basis,basis,lo,hi,activities=['review'])
        row['operators'][0]['visits']='first'
        data['programs'][0]['observations'].append(row)
    return data


def test_phase_changes_wait_and_service_but_not_cycle_work_counts_or_schedule():
    model=VisitHierarchy(phase_fixture(),Config(population_size=16,within_visit_phases=True))
    z=np.zeros(model.layout.size)
    initial=model.log_likelihood(z,[0],parts=True)
    p=model.programs[0]
    first=model.trace(p,z,model.parameters(z),0)
    z[model.phase_coordinates[0]]=-2.
    second=model.trace(p,z,model.parameters(z),0)
    changed=model.log_likelihood(z,[0],parts=True)
    assert first is not second  # phase parameters must participate in cache key
    for key in ('total','task','visits','labor'):
        assert initial['J__P:'+key]==changed['J__P:'+key]
    for key in ('wait_elapsed','service_elapsed'):
        assert initial['J__P:'+key]!=changed['J__P:'+key]
    np.testing.assert_array_equal(first.durations,second.durations)
    np.testing.assert_array_equal(first.resources['agency_hours'],second.resources['agency_hours'])
    np.testing.assert_array_equal(first.event('initial_decision'),second.event('initial_decision'))


def test_phase_centering_preserves_realized_fractions_and_reference_likelihood():
    data=phase_fixture()
    model=VisitHierarchy(data,Config(population_size=16,within_visit_phases=True))
    rng=np.random.default_rng(911)
    for _ in range(15):
        z=rng.normal(size=model.layout.size)
        current=model.log_likelihood(z,[0])
        assert current==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-10)
        first=model.trace(model.programs[0],z,model.parameters(z),0)
        updated,value=model.centered_duration_update(z,[0],current,rng)
        second=model.trace(model.programs[0],updated,model.parameters(updated),0)
        np.testing.assert_allclose(first.durations,second.durations,rtol=1e-12)
        np.testing.assert_allclose(first.service_fractions,second.service_fractions,rtol=1e-12)
        assert value==pytest.approx(current,abs=1e-8)


def test_phase_effect_propagates_to_same_agency_in_another_program():
    data=phase_fixture()
    second=copy.deepcopy(data['programs'][0])
    second['id']='J__Q'
    data['programs'].append(second)
    model=VisitHierarchy(data,Config(population_size=16,within_visit_phases=True))
    z=np.zeros(model.layout.size)
    before=model.log_likelihood(z,[0,0],parts=True)
    index=1+model.agencies.index('J:Review')
    z[model.phase_coordinates[index]]=2.
    after=model.log_likelihood(z,[0,0],parts=True)
    for pid in ('J__P','J__Q'):
        assert before[pid+':service_elapsed']!=after[pid+':service_elapsed']
        assert before[pid+':task']==after[pid+':task']
        assert before[pid+':labor']==after[pid+':labor']


def test_phase_mean_integration_conserves_cycles_and_refines_independently():
    model=VisitHierarchy(phase_fixture(),Config(population_size=16,within_visit_phases=True))
    nodes,weights=roots_hermitenorm(64)
    weights/=np.sqrt(2*np.pi)
    rng=np.random.default_rng(998)
    for _ in range(40):
        z=rng.normal(size=model.layout.size)
        par=model.parameters(z)
        phases=model.phase_means(par)
        refined=model.phase_means(par,nodes,weights)
        for first,second in zip(phases,refined):
            np.testing.assert_allclose(first,second,rtol=1e-10,atol=1e-12)
        cycle=np.exp(par['mu'][0]+.5*(par['sigma'][0]**2+model.cfg.common_case_sd**2))
        np.testing.assert_allclose(sum(phases),cycle,rtol=1e-14)


def test_same_case_short_service_and_long_wait_are_compatible_in_one_model():
    model=VisitHierarchy(phase_fixture(),Config(population_size=16,within_visit_phases=True))
    z=np.zeros(model.layout.size)
    base=model.log_likelihood(z,[0],parts=True)
    # This changes the phase partition only: seven-day cycles need not become
    # 20-minute cycles, nor do they imply 168 staff-hours.
    z[model.phase_coordinates[0]]=np.log((1/72)/(7-1/72))/model.cfg.phase_location_sd
    after=model.log_likelihood(z,[0],parts=True)
    expected=duration_log_probability(.01,.02,1/72,scale=model.cfg.report_sd,
                                      contamination=model.cfg.contamination)
    assert after['J__P:service_elapsed']==pytest.approx(float(expected))
    assert after['J__P:service_elapsed']>base['J__P:service_elapsed']
    assert after['J__P:wait_elapsed']>base['J__P:wait_elapsed']
    assert after['J__P:total']==base['J__P:total']


def test_phase_disabled_remains_same_layout_and_target_under_irrelevant_phase_scales():
    cfg=Config(population_size=16)
    base=VisitHierarchy(data_fixture(),cfg)
    changed=VisitHierarchy(data_fixture(),replace(cfg,phase_location_sd=5.,phase_case_sd=2.))
    z=np.random.default_rng(55).normal(size=base.layout.size)
    assert base.layout.size==changed.layout.size
    assert base.log_likelihood(z,[0])==changed.log_likelihood(z,[0])


def test_phase_sampler_report_is_joint_but_smoke_run_does_not_claim_convergence():
    cfg=Config(chains=1,warmup=1,draws=8,population_size=16,within_visit_phases=True)
    model=VisitHierarchy(phase_fixture(),cfg)
    arrays=model.sample()
    report=model.report(*arrays[:3])
    assert not report['posterior_converged']
    assert report['phase_channel']['direct_claims']==2
    agency=report['agencies']['J:Review']
    assert agency['inventory_mean_wait_days']['median']>0
    assert agency['inventory_mean_service_elapsed_days']['median']>0
    assert any('inventory_mean_wait_days' in key for key in report['diagnostics'])
