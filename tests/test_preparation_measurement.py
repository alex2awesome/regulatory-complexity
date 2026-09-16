import copy
import math
from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from pipeline.procbench.bayes_preparation_measurement import Config,PreparationMeasurementModel,budget_fractions
from pipeline.procbench.bayes_outcome_measurement import Config as OutcomeConfig,OutcomeMeasurementModel
from test_bayes_hierarchy import measurement
from test_process_measurement import inputs as base_inputs,audit_row
from test_outcome_measurement import outcomes


def inputs(grouped=True):
    e,a=base_inputs()
    e['measurements'] += [measurement('file',value=12,ident='prep1'),measurement('file',value=8,ident='prep2')]
    a['measurements'] += [audit_row(mid,duration_basis='stage_span',start_event='step_start',end_event='step_end')
                          for mid in ['prep1','prep2']]
    rows=[dict(measurement_id=mid,phase='before_first_submission',start_event='unknown',
        end_event='unknown' if i==0 else 'first_submission',basis='stage_span',
        evidence=[dict(doc_id='document',quote='Evidence')],notes='') for i,mid in enumerate(['prep1','prep2'])]
    groups=[dict(case_id='c1',measurement_ids=['prep1','prep2'],coverage='reported_preparation_clock',
        evidence=[dict(doc_id='document',quote='Evidence')],notes='Earlier preparation is unknown.')] if grouped else []
    prep=dict(program_id=e['program_id'],measurements=rows,serial_groups=groups,unresolved=[])
    return e,a,outcomes(e),prep


def test_dirichlet_budgets_preserve_unreported_time_and_have_expected_prior_moments():
    rng=np.random.default_rng(432)
    samples=np.array([budget_fractions(z) for z in rng.normal(size=(6000,3))])
    assert np.all(samples>0) and np.all(samples.sum(axis=1)<1)
    np.testing.assert_allclose(samples.mean(axis=0),np.full(3,.25),atol=.008)
    assert np.mean(1-samples.sum(axis=1))==pytest.approx(.25,abs=.008)


def test_grouped_preparation_uses_a_shared_budget_not_a_fabricated_complete_clock():
    e,a,o,prep=inputs()
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    v=model.parameters(p,z)
    assert len(p['cases'])==1 and len(p['cases']['c1'])==3
    assert len(p['preparation_groups'])==1
    assert 0<v['preparation_spans'].sum()<1
    # Even 'reported_preparation_clock' does not establish all earlier preparation.
    assert p['preparation_groups'][0]['support']['coverage']=='reported_preparation_clock'


def test_ungrouped_spans_do_not_invent_nonoverlap_or_parallel_schedule():
    e,a,o,prep=inputs(False)
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    z[p['preparation_fractions']]=2.
    fractions=model.parameters(p,z)['preparation_spans']
    assert np.all(fractions<1) and fractions.sum()>1
    assert all(g['support'] is None for g in p['preparation_groups'])


def test_exact_full_preparation_clock_is_not_randomly_shortened():
    e,a,o,prep=inputs(False)
    prep['measurements'][0].update(start_event='process_start',end_event='first_submission')
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    assert len(p['preparation_fractions'])==1
    assert model.parameters(p,np.zeros(model.layout.size))['preparation_spans'][0]==1


def test_native_clock_likelihood_and_cache_match_independent_reference_and_gibbs_ridge():
    e,a,o,prep=inputs()
    cfg=Config(selection_sd=1.5)
    model=PreparationMeasurementModel([e],[a],[o],[prep],cfg)
    oracle=PreparationMeasurementModel([e],[a],[o],[prep],replace(cfg,accelerate=False))
    rng=np.random.default_rng(814)
    for z in rng.normal(size=(20,model.layout.size)):
        before=model.log_likelihood(z)
        assert before==pytest.approx(oracle.log_likelihood(z),abs=1e-9)
        moved=model.source_location_move(z,rng)
        assert model.log_likelihood(moved)==pytest.approx(before,abs=1e-9)
        z[model.programs[0]['preparation_fractions'][0]]+=1.
        assert model.log_likelihood(z)==pytest.approx(oracle.log_likelihood(z),abs=1e-9)


def test_same_case_total_and_partial_clocks_are_one_joint_integral():
    e,a,o,prep=inputs()
    cfg=Config(quadrature=1024,outcome_contrast_sd=0,source_sd=0,accelerate=False)
    model=PreparationMeasurementModel([e],[a],[o],[prep],cfg)
    z=np.zeros(model.layout.size)
    p=model.programs[0]
    z[p['clock'][0]]=2.
    par=model.parameters(p,z)
    def likelihood(node):
        return norm.pdf(node)*np.exp(sum(model.observation_probability(m,par['mu']+par['sigma']*node,par)
                                        for m in p['cases']['c1']))
    integral=quad(likelihood,-12,12,epsabs=1e-15)[0]
    assert model.log_likelihood(z)==pytest.approx(math.log(integral),abs=1e-7)


def test_partial_clocks_inform_preparation_fraction_and_inputs_are_not_mutated():
    e,a,o,prep=inputs()
    original=copy.deepcopy((e,a,o,prep))
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    z=np.zeros(model.layout.size)
    little=model.log_likelihood(z)
    z[p['clock'][0]]=2.
    assert model.log_likelihood(z)>little
    assert (e,a,o,prep)==original


def test_unknown_phase_and_short_service_stay_explicitly_excluded():
    e,a,o,prep=inputs(False)
    prep['measurements'][0]['phase']='unknown'
    prep['measurements'][1]['basis']='single_visit'
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    assert not p['anchors'] and len(p['excluded_preparation'])==2
    simpler=OutcomeMeasurementModel([e],[a],[o],OutcomeConfig())
    z=np.zeros(model.layout.size)
    assert model.layout.size==simpler.layout.size
    assert model.log_likelihood(z)==simpler.log_likelihood(z)


def test_preparation_only_cases_and_sources_are_included_without_duplication():
    e,a,o,prep=inputs(False)
    e['measurements'][1].update(case_id='c2',source_family='new source')
    other=copy.deepcopy(o['cases'][0])
    other['case_id']='c2'
    o['cases'].append(other)
    model=PreparationMeasurementModel([e],[a],[o],[prep])
    p=model.programs[0]
    assert len(p['cases'])==2 and 'new source' in p['sources']
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z))
    assert sorted(np.concatenate(model.blocks).tolist())==list(range(model.layout.size))


def test_wrong_audit_pairing_and_invalid_concentration_are_rejected():
    e,a,o,prep=inputs()
    changed=copy.deepcopy(prep)
    changed['program_id']='wrong'
    with pytest.raises(ValueError,match='match exactly'):
        PreparationMeasurementModel([e],[a],[o],[changed])
    with pytest.raises(ValueError,match='positive'):
        PreparationMeasurementModel([e],[a],[o],[prep],Config(preparation_span_alpha=0))
