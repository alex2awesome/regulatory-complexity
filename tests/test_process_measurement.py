import copy
import math
from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from pipeline.procbench.audit_measurement_semantics import validate_audit, eligible
from pipeline.procbench.bayes_process_measurement import (
    Config, ProcessMeasurementModel, log_selection_weight, observed_log_probability,
    rounded_interval)
from test_bayes_hierarchy import fixture, measurement, add_context


def audit_row(mid='m1', **kwargs):
    row = dict(measurement_id=mid, duration_basis='whole_case', start_event='preparation_start',
        end_event='initial_decision', censoring='none', population_scope='individual',
        reporting_sample='administrative', statistic_interpretation='individual_completion',
        original_precision_unit='calendar_days', evidence=[{'doc_id':'document','quote':'Evidence'}], notes='')
    row.update(kwargs)
    return row


def inputs():
    e = fixture()
    e['measurements'] = [measurement(None, 'process', 30.)]
    a = dict(program_id=e['program_id'], measurements=[audit_row()], unresolved=[])
    return e, a


@pytest.mark.parametrize('strength', [0., .5, 2., 7.])
@pytest.mark.parametrize('width', [.1, .35, 1.])
def test_delay_ascertainment_is_normalized(strength, width):
    integral = quad(lambda z: norm.pdf(z)*np.exp(log_selection_weight(z,strength,width)), -12, 12,
                    epsabs=1e-10)[0]
    assert integral == pytest.approx(1., abs=1e-9)
    if strength == 0:
        np.testing.assert_allclose(log_selection_weight(np.arange(-10,10), strength,width), 0, atol=1e-14)


def test_right_censoring_is_not_completed_duration():
    bounds = (math.log(34), math.log(36))
    right = observed_log_probability(bounds, np.log([10,35,100]), .2, 0, 'right')
    assert np.all(np.diff(right)>0)
    completed = observed_log_probability(bounds,np.log([10,35,100]),.2,0)
    assert completed[1] > completed[2]
    with pytest.raises(ValueError,match='Unresolved censoring'):
        observed_log_probability(bounds,0,.2,0,'uncertain')


def test_original_minute_precision_survives_conversion_to_hours():
    m = measurement(value=1/3)
    m['unit'] = 'hours'
    a = audit_row(original_precision_unit='minutes')
    lo,hi = np.exp(rounded_interval(m,a))
    assert lo*1440 == pytest.approx(19.5)
    assert hi*1440 == pytest.approx(20.5)


def test_open_case_does_not_become_completed_or_censored_initial_decision():
    e,a = inputs()
    a['measurements'][0].update(duration_basis='elapsed_so_far',end_event='ongoing',censoring='right',
                                statistic_interpretation='individual_censored')
    model = ProcessMeasurementModel([e],[a])
    assert not model.programs[0]['observations']
    assert 'does not establish' in model.programs[0]['excluded'][0]['reason']
    assert model.log_likelihood(np.zeros(model.layout.size)) == 0


def test_ambiguous_whole_case_is_marginalized_only_when_explicitly_enabled():
    e,a=inputs()
    a['measurements'][0].update(end_event='unspecified',censoring='uncertain',statistic_interpretation='unresolved')
    excluded=ProcessMeasurementModel([e],[a])
    assert not excluded.programs[0]['observations']
    model=ProcessMeasurementModel([e],[a],Config(include_ambiguous=True))
    p=model.programs[0]
    assert len(p['observations'])==1 and len(p['cases'])==1
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z))
    par=model.parameters(p,z)
    assert par['progress'][0]==pytest.approx(.5)
    assert par['completion']==pytest.approx(math.sqrt(.5))


def test_source_eligible_audit_coverage_and_quotes():
    e,a = inputs()
    docs = [{'id':'document','text':'Evidence'}]
    validate_audit(a,e,docs)
    changed = copy.deepcopy(a)
    changed['measurements'].append(copy.deepcopy(changed['measurements'][0]))
    with pytest.raises(ValueError,match='exactly once'):
        validate_audit(changed,e,docs)
    changed = copy.deepcopy(a)
    changed['measurements'][0]['evidence'][0]['quote']='invented'
    with pytest.raises(ValueError,match='Nonverbatim'):
        validate_audit(changed,e,docs)
    add_context(e,'m1',temporal_scope='historical')
    assert eligible(e)==[]


def test_first_submission_does_not_remove_repeated_correction_span():
    e,a = inputs()
    model = ProcessMeasurementModel([e],[a])
    p = model.programs[0]
    z = np.zeros(model.layout.size)
    par = model.parameters(p,z)
    first = audit_row(start_event='first_submission')
    complete = audit_row(start_event='complete_submission')
    first_value = model.clock_options(first,par)[0][0]
    complete_value = model.clock_options(complete,par)[0][0]
    z[p['clock'][1]]=3.
    new = model.parameters(p,z)
    assert model.clock_options(first,new)[0][0] == first_value
    assert model.clock_options(complete,new)[0][0] < complete_value


def test_duplicate_claims_do_not_duplicate_cases_and_distinct_reports_share_latent_case():
    e,a = inputs()
    repeated=copy.deepcopy(e['measurements'][0])
    repeated['id']='repeat'
    e['measurements'].append(repeated)
    a['measurements'].append(audit_row('repeat'))
    model=ProcessMeasurementModel([e],[a])
    assert len(model.programs[0]['observations'])==1
    assert len(model.programs[0]['cases'])==1
    repeated['value']=31.
    model=ProcessMeasurementModel([e],[a])
    assert len(model.programs[0]['observations'])==2
    assert len(model.programs[0]['cases'])==1
    shared=model.log_likelihood(np.zeros(model.layout.size))
    repeated['case_id']='second case'
    independent=ProcessMeasurementModel([e],[a])
    separate=independent.log_likelihood(np.zeros(independent.layout.size))
    assert shared > separate


def test_program_pairing_rejects_duplicate_audit_programs():
    e,a=inputs()
    other=copy.deepcopy(e)
    other['program_id']='another__program'
    with pytest.raises(ValueError,match='match exactly'):
        ProcessMeasurementModel([e,other],[a,a])


def test_known_summary_functionals_and_single_case_marginal_agree_with_independent_quadrature():
    e,a=inputs()
    cfg=Config(quadrature=512,source_sd=0)
    model=ProcessMeasurementModel([e],[a],cfg)
    state=np.zeros(model.layout.size)
    p=model.programs[0]
    par=model.parameters(p,state)
    m=p['observations'][0]
    oracle=quad(lambda z: norm.pdf(z)*np.exp(model.observation_probability(m,par['mu']+par['sigma']*z,par)),
                -12,12,epsabs=1e-12)[0]
    assert model.log_likelihood(state)==pytest.approx(math.log(oracle),abs=1e-8)
    selected=replace(cfg,selection_sd=1.5)
    a['measurements'][0]['reporting_sample']='forum_selected'
    model=ProcessMeasurementModel([e],[a],selected)
    state=np.zeros(model.layout.size)
    p=model.programs[0]
    state[p['selection']]=1.
    par=model.parameters(p,state)
    m=p['observations'][0]
    oracle=quad(lambda z: norm.pdf(z)*np.exp(log_selection_weight(z,1.5)+model.observation_probability(
        m,par['mu']+par['sigma']*z,par)), -12,12,epsabs=1e-12)[0]
    assert model.log_likelihood(state)==pytest.approx(math.log(oracle),abs=1e-8)


def test_median_mean_p90_are_not_interchangeable():
    e,a=inputs()
    e['measurements'][0].update(case_id=None,statistic='median',n=100)
    a['measurements'][0].update(statistic_interpretation='population_median',population_scope='all_cases')
    model=ProcessMeasurementModel([e],[a])
    z=np.zeros(model.layout.size)
    median=model.log_likelihood(z)
    a['measurements'][0]['statistic_interpretation']='population_mean'
    mean_model=ProcessMeasurementModel([e],[a])
    assert mean_model.log_likelihood(z)<median
    a['measurements'][0]['statistic_interpretation']='population_p90'
    p90_model=ProcessMeasurementModel([e],[a])
    assert p90_model.log_likelihood(z)<mean_model.log_likelihood(z)


def test_vectorized_likelihood_matches_independent_row_implementation():
    e,a=inputs()
    for i,stat in enumerate(['population_mean','population_p90','typical_range','informal_forecast',
                             'individual_completion','unresolved']):
        raw=measurement(None,'process',value=20+10*i,ident=f'm{i+2}',case=None if i<4 else 'c1')
        if i<4:
            raw['statistic']=['mean','p90','typical','estimate'][i]
        raw['cohort']='clean cases' if i==2 else None
        e['measurements'].append(raw)
        a['measurements'].append(audit_row(raw['id'],statistic_interpretation=stat,
            population_scope='selected_cohort' if i==2 else 'all_cases' if i<4 else 'individual',
            start_event=['first_submission','complete_submission','unspecified'][i%3],
            end_event='closeout' if i==3 else 'unspecified',censoring='uncertain' if i==5 else 'none',
            reporting_sample='forum_selected'))
    model=ProcessMeasurementModel([e],[a],Config(include_ambiguous=True,selection_sd=1.5))
    rng=np.random.default_rng(28)
    for z in rng.normal(size=(20,model.layout.size)):
        assert model.log_likelihood(z)==pytest.approx(model.log_likelihood_reference(z),abs=1e-10)


def test_selection_generator_and_grid_recover_known_component():
    from pipeline.procbench.validate_process_selection import selected_cases,grid_posterior,weighted_quantile
    rng=np.random.default_rng(293)
    mu=math.log(30.)
    values=selected_cases(rng,500,mu,.6,1.5)
    assert values.mean()>mu+.2
    mus=np.linspace(mu-1,mu+1,201)
    kappas=np.linspace(0,6,121)
    weights,kw=grid_posterior(values,.6,True,mus,kappas,mu)
    assert weights.sum()==pytest.approx(1.) and kw.sum()==pytest.approx(1.)
    estimate=weighted_quantile(mus,weights,[.5])[0]
    assert abs(estimate-mu)<.12
    unselected,_=grid_posterior(values,.6,False,mus,kappas,mu)
    biased=weighted_quantile(mus,unselected,[.5])[0]
    assert biased>estimate+.15


def test_native_student4_interval_matches_scipy_in_both_tails():
    from pipeline.procbench.measurement_kernel import student4_interval
    from pipeline.procbench.bayes_hierarchy import log_interval
    for lower,upper in [(-np.inf,np.inf),(-np.inf,0),(0,np.inf),(-3,-2),(-1,1),(1,2),
                        (1e3,1e3+.1),(-1e3-.1,-1e3),(1e8,1.1e8),(-1.1e8,-1e8)]:
        actual=math.log(student4_interval(lower,upper,0.,1.))
        assert actual==pytest.approx(float(log_interval(lower,upper,0.,1.)),abs=1e-8)
