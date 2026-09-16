import copy
import math
from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import ndtr,ndtri
from scipy.stats import norm

from pipeline.procbench.audit_case_outcomes import validate_outcomes
from pipeline.procbench.bayes_outcome_measurement import Config,OutcomeMeasurementModel,mixture_quantile,shifted_selection_normalizer
from pipeline.procbench.bayes_process_measurement import ProcessMeasurementModel,Config as BaseConfig,log_selection_weight
from test_process_measurement import inputs


def outcomes(e,outcome='unknown'):
    return dict(program_id=e['program_id'],cases=[dict(case_id='c1',outcome=outcome,
        initial_decision_status='completed' if outcome in {'approved','denied'} else 'unknown',
        evidence=[dict(doc_id='document',quote='Evidence')],notes='')],population_counts=[],unresolved=[])


def count_row(**kwargs):
    row=dict(id='counts',approved=137,denied=37,abandoned=None,received=200,completed=None,still_open=None,
        denominator_interpretation='same_decision_cohort',population_scope='all_cases',
        temporal_scope='current',source_family='document',evidence=[dict(doc_id='document',quote='Evidence')],notes='')
    row.update(kwargs)
    return row


def test_mixture_quantile_uses_cdf_not_average_of_component_medians():
    means=np.log([10.,100.])
    median=mixture_quantile(.5,means,.2,.9)
    assert np.exp(median)<12
    cdf=.9*ndtr((median-means[0])/.2)+.1*ndtr((median-means[1])/.2)
    assert cdf==pytest.approx(.5,abs=1e-10)
    assert np.exp(median)!=pytest.approx(.9*10+.1*100)


@pytest.mark.parametrize('shift',[-3.,-.5,0.,2.])
def test_shifted_selection_is_normalized_for_each_outcome(shift):
    constant=shifted_selection_normalizer(shift,2.,.35)
    integral=quad(lambda z:norm.pdf(z)*np.exp(log_selection_weight(z+shift,2.,.35)-constant),-12,12)[0]
    assert integral==pytest.approx(1.,abs=1e-9)


def test_identical_outcome_components_reduce_to_single_population_model():
    e,a=inputs()
    a['measurements'][0]['reporting_sample']='forum_selected'
    cfg=Config(outcome_contrast_sd=0,selection_sd=1.5)
    model=OutcomeMeasurementModel([e],[a],[outcomes(e)],cfg)
    simple=ProcessMeasurementModel([e],[a],BaseConfig(selection_sd=1.5))
    rng=np.random.default_rng(843)
    for short in rng.normal(size=(10,simple.layout.size)):
        full=np.concatenate([short,rng.normal(size=model.layout.size-len(short))])
        assert model.log_likelihood(full)==pytest.approx(simple.log_likelihood(short),abs=1e-10)


def test_known_outcome_cases_do_not_become_binomial_prevalence_observations():
    e,a=inputs()
    model=OutcomeMeasurementModel([e],[a],[outcomes(e,'denied')])
    state=np.zeros(model.layout.size)
    p=model.programs[0]
    state[p['outcome_index'][1]]=ndtri(.1)
    first=model.log_likelihood(state)
    state[p['outcome_index'][1]]=ndtri(.9)
    assert model.log_likelihood(state)==pytest.approx(first,abs=1e-10)


def test_pending_denominators_cannot_become_approval_rate():
    e,a=inputs()
    audit=outcomes(e)
    audit['population_counts']=[count_row(approved=18,denied=None,received=81,
        denominator_interpretation='mixed_status_counts')]
    model=OutcomeMeasurementModel([e],[a],[audit])
    assert model.programs[0]['counts']==[]
    assert len(model.programs[0]['excluded_counts'])==1
    audit['population_counts'][0]['denominator_interpretation']='same_decision_cohort'
    with pytest.raises(ValueError,match='both explicit counts'):
        validate_outcomes(audit,e,[dict(id='document',text='Evidence')])


def test_decided_counts_favor_their_prevalence_with_cohort_bias_held_zero():
    e,a=inputs()
    audit=outcomes(e,'denied')
    audit['population_counts']=[count_row()]
    model=OutcomeMeasurementModel([e],[a],[audit])
    state=np.zeros(model.layout.size)
    state[model.programs[0]['outcome_index'][1]]=ndtri(137/174)
    near=model.log_likelihood(state)
    state[model.programs[0]['outcome_index'][1]]=ndtri(.5)
    assert near>model.log_likelihood(state)+20


def test_abandonment_is_not_a_completed_initial_decision():
    e,a=inputs()
    model=OutcomeMeasurementModel([e],[a],[outcomes(e,'abandoned')])
    assert not model.programs[0]['cases']
    assert not model.programs[0]['observations']
    assert model.log_likelihood(np.zeros(model.layout.size))==0


def test_independent_outcome_audit_can_resolve_initial_decision_censoring_without_rewriting_inputs():
    e,a=inputs()
    a['measurements'][0].update(end_event='ongoing',censoring='right',duration_basis='elapsed_so_far',
                                statistic_interpretation='individual_censored')
    o=outcomes(e)
    o['cases'][0]['initial_decision_status']='ongoing'
    model=OutcomeMeasurementModel([e],[a],[o])
    assert len(model.programs[0]['observations'])==1
    assert model.programs[0]['observations'][0]['audit']['end_event']=='initial_decision'
    assert a['measurements'][0]['end_event']=='ongoing'
    assert model.semantic_resolutions


def test_outcome_native_matches_scipy_and_cache_invalidates_only_relevant_programs():
    e,a=inputs()
    e2,a2=copy.deepcopy(e),copy.deepcopy(a)
    e2['program_id']=a2['program_id']='second__program'
    o,o2=outcomes(e),outcomes(e2,'denied')
    o['population_counts']=[count_row()]
    cfg=Config(selection_sd=1.5)
    native=OutcomeMeasurementModel([e,e2],[a,a2],[o,o2],cfg)
    reference=OutcomeMeasurementModel([e,e2],[a,a2],[o,o2],replace(cfg,accelerate=False))
    rng=np.random.default_rng(926)
    for z in rng.normal(size=(20,native.layout.size)):
        assert native.log_likelihood(z)==pytest.approx(reference.log_likelihood(z),abs=1e-9)
        before=native._program_cache[e2['program_id']]
        z[native.programs[0]['main'][0]]+=.1
        assert native.log_likelihood(z)==pytest.approx(reference.log_likelihood(z),abs=1e-9)
        assert native._program_cache[e2['program_id']]==before


def test_source_location_gibbs_move_preserves_outcome_likelihood():
    e,a=inputs()
    o=outcomes(e)
    o['population_counts']=[count_row()]
    m=OutcomeMeasurementModel([e],[a],[o],Config(selection_sd=1.5))
    rng=np.random.default_rng(2006)
    for z in rng.normal(size=(20,m.layout.size)):
        before=m.log_likelihood(z)
        moved=m.source_location_move(z,rng)
        assert m.log_likelihood(moved)==pytest.approx(before,abs=1e-9)
        assert not np.array_equal(z,moved)
