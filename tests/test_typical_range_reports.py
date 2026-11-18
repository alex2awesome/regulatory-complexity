import copy
import math

import numpy as np
import pytest
from scipy.special import logsumexp, stdtr

from pipeline.procbench.bayes_trace_hierarchy import (Config, VisitHierarchy,
    duration_report_log_probability)
from pipeline.procbench.compact_visit_trace import PopulationTraceMixture, population_quantile
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.typical_range_reports import (typical_range_log_probability,
                                                       validate_typical_range_model)
from procbench_fixtures import data_fixture, observation
from test_compile_visit_durations import inputs


def reporting_model():
    return dict(kind='interval_censored_subjective_quantile',
                quantiles=[.25, .5, .75], weights=[.25, .5, .25],
                report_log_scale=.6,
                description='Test-only subjective quantile prior; Student-t(4) scale, not calibrated.')


def range_inputs():
    e, v, s, d, _ = inputs()
    e['measurements'][0].update(case_id=None, statistic='typical', value=None,
                                lower=8., upper=10., unit='weeks')
    s['measurements'][0].update(statistic_interpretation='typical_range',
                                population_scope='all_cases', original_precision_unit='weeks')
    v['measurements'][0]['operators'][0].update(basis='whole_case_clock', activity_ids=[],
        start='process_start', end='initial_decision', visits='not_applicable')
    return e, v, s, d, dict(typical_range_model=reporting_model())


def range_data():
    data=data_fixture()
    o=observation('usual', 'whole_case_clock', 15., 25., case=None)
    o.update(statistic='typical_range', typical_range_model=reporting_model())
    data['programs'][0]['observations']=[o]
    return data


def test_explicit_range_compiles_without_relabeling_or_mutating_sources():
    e,v,s,d,p=range_inputs()
    original=copy.deepcopy((e,v,s,d,p))
    result=compile_durations(e,v,s,d,p)
    assert (e,v,s,d,p)==original
    o=result['observations'][0]
    assert o['statistic']=='typical_range'
    assert (o['lower'],o['upper'])==(56.,70.)
    assert o['typical_range_model']==reporting_model()
    assert 'sample_size' not in o
    assert result['coverage']['informative_elapsed']==1
    assert 'subjective_typical_range_reports' in result['required_model_features']
    # Existing runs must not acquire a reporting prior implicitly.
    assert not compile_durations(e,v,s,d,{})['observations']


@pytest.mark.parametrize('change,reason',[
    ({'n':20}, 'typical_range_is_not_a_finite_cohort_statistic'),
    ({'lower':None}, 'typical_range_requires_explicit_uncensored_bounds'),
    ({'case_id':'c1'}, 'population_statistic_with_individual_case_identity'),
])
def test_incompatible_source_semantics_remain_explicit_residuals(change,reason):
    e,v,s,d,p=range_inputs()
    e['measurements'][0].update(change)
    p.update(retain_unsupported=True,residual_reference=dict(median_days=7.,log_scale=3.))
    result=compile_durations(e,v,s,d,p)
    assert reason in result['dispositions'][0]['unresolved_reasons']
    if result['observations']:
        assert result['observations'][0]['statistic']=='report_only'
        assert 'typical_range_model' not in result['observations'][0]


@pytest.mark.parametrize('update',[
    {'weights':[.1,.1,.1]}, {'weights':[True,.5,.25]},
    {'quantiles':[.75,.5,.25]}, {'quantiles':[0.,.5,.75]},
    {'quantiles':[.25,.5,1.]}, {'quantiles':[.25,.5,.5]},
    {'report_log_scale':0.}, {'report_log_scale':float('nan')},
    {'kind':'median'}, {'description':''}, {'extra':1},
])
def test_invalid_reporting_contracts_fail(update):
    model=reporting_model()
    model.update(update)
    with pytest.raises(ValueError):
        validate_typical_range_model(model)


def test_joint_v6_likelihood_matches_explicit_quantile_mixture():
    data=range_data()
    model=VisitHierarchy(data,Config(population_size=64,modeled_channels=('elapsed',)))
    z=np.zeros(model.layout.size)
    par=model.parameters(z)
    p=model.programs[0]
    population=model._likelihood_population(p,z,par,0)
    o=p['observations'][0]
    values=population.values(o['operators'][0])
    rm=o['typical_range_model']
    expected=logsumexp([math.log(w)+float(duration_report_log_probability(o,
        population_quantile(population,values,q),0.,rm['report_log_scale'],model.cfg.contamination))
        for q,w in zip(rm['quantiles'],rm['weights'])])
    assert model.log_likelihood(z,[0])==pytest.approx(expected)
    assert model.log_likelihood_reference(z,[0])==pytest.approx(expected)
    rng=np.random.default_rng(621)
    for _ in range(12):
        z=rng.normal(0,.4,model.layout.size)
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)
    # A report actually changes the hierarchy likelihood, rather than residual retention only.
    moved=np.zeros_like(z)
    moved[model.location[0]]=2.
    assert abs(model.log_likelihood(moved,[0])-expected)>.1


def test_weighted_cdf_and_student_t_kernel_match_independent_analytic_calculation():
    class Trace:
        def __init__(self, size):
            self.durations=np.zeros((size,1))

    # Path probabilities .8/.2 and two integration rows per path imply weights
    # [.4,.4,.1,.1]. Thus inverse-CDF quantiles .25 and .75 are exactly 1 and 2,
    # unlike an unweighted interpolation. The expectation below intentionally
    # does not call either production helper used to obtain those quantities.
    population=PopulationTraceMixture([Trace(2),Trace(2)],[.8,.2],['common','rare'])
    values=np.array([1.,2.,10.,20.])
    observation=dict(lower=1.5,upper=3.,typical_range_model=dict(
        kind='interval_censored_subjective_quantile',quantiles=[.25,.75],weights=[.3,.7],
        report_log_scale=.4,description='Analytic test contract.'))
    offset=.1
    locations=np.array([1.,2.])
    lo=(math.log(observation['lower'])-(np.log(locations)+offset))/.4
    hi=(math.log(observation['upper'])-(np.log(locations)+offset))/.4
    expected=logsumexp(np.log([.3,.7])+np.log(stdtr(4.,hi)-stdtr(4.,lo)))
    actual=typical_range_log_probability(observation,population,values,offset,0.,
                                         duration_report_log_probability)
    assert actual==pytest.approx(expected,abs=1e-14)


def test_typical_with_residual_keeps_declared_operator_mass():
    data=range_data()
    o=data['programs'][0]['observations'][0]
    o['operators'].append(dict(basis='unmodeled_duration',median_days=7.,log_scale=3.))
    o['operator_weights']=[.8,.2]
    model=VisitHierarchy(data,Config(population_size=32,modeled_channels=('elapsed',)))
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]))


def test_case_path_population_uses_weights_and_reference_agrees():
    data=range_data()
    route=data['programs'][0]['routes'][0]
    blocks=route.pop('blocks')
    route['paths']=[dict(id='long',probability_weight=.8,blocks=blocks),
                    dict(id='short',probability_weight=.2,blocks=[blocks[-1]])]
    model=VisitHierarchy(data,Config(population_size=32,modeled_channels=('elapsed',)))
    rng=np.random.default_rng(9)
    for _ in range(8):
        z=rng.normal(0,.2,model.layout.size)
        assert model.log_likelihood(z,[0])==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)


@pytest.mark.parametrize('update',[
    {'case_id':'case'}, {'sample_size':10}, {'upper':None},
    {'upper':15.}, {'report_intervals':[[15.,25.]]},
    {'statistic':'median'}, {'typical_range_model':None},
])
def test_model_rejects_unsupported_typical_report_forms(update):
    data=range_data()
    data['programs'][0]['observations'][0].update(update)
    with pytest.raises(ValueError):
        VisitHierarchy(data,Config(population_size=16))
