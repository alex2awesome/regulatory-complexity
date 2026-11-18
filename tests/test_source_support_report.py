import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import preflight_report
from procbench_fixtures import data_fixture
from test_cohort_histograms import histogram_fixture
from test_cohort_quantiles import cohort_fixture


def test_residual_only_source_is_visible_but_never_declared_informative():
    data=data_fixture()
    obs=copy.deepcopy(data['programs'][0]['observations'][0])
    obs.update(id='residual',source_family='only_residual',statistic='report_only',case_id=None,
               operators=[dict(basis='unmodeled_duration',median_days=30.,log_scale=2.)])
    data['programs'][0]['observations'].append(obs)
    model=VisitHierarchy(data,Config(population_size=16))
    report=model.source_support_report()
    row=report['source_families']['only_residual']
    assert row['observation_rows']==1
    assert row['residual_only_rows']==1
    assert row['observation_rows_with_duration_candidates']==0
    assert row['offsets']['elapsed']['no_direct_duration_support']
    assert row['offsets']['elapsed']['posterior_log_offset'] is None
    assert row['duration_offset_coordinates_allocated']
    ordinary=report['source_families']['source']
    assert ordinary['duration_candidate_rows_by_channel']==dict(elapsed=2,payer_hours=0,agency_hours=1)
    assert ordinary['count_rows']==1
    assert len(ordinary['duration_candidate_unselected_case_ids'])==1  # Three duration claims, one case.
    assert report['count_source_policy']['per_type_reliability'] is False
    assert preflight_report(model)['source_support']==report


def test_histogram_provenance_never_masquerades_as_an_estimated_source_offset():
    data=data_fixture()
    p=data['programs'][0]
    p.update(observations=[],histogram_cohorts=[histogram_fixture()])
    model=VisitHierarchy(data,Config(modeled_channels=('elapsed',),population_size=16))
    row=model.source_support_report()['source_families']['administrative_table']
    assert row['exact_histogram_cases']==10
    assert row['exact_histogram_cohorts']==1
    assert row['offsets']=={}
    assert not row['duration_offset_coordinates_allocated']
    assert row['duration_contamination_probability'] is None
    assert row['report_log_scales']==[]


def test_joint_quantiles_report_cohorts_separately_from_report_rows():
    data=data_fixture()
    data['programs'][0].update(observations=[],quantile_cohorts=[cohort_fixture()])
    model=VisitHierarchy(data,Config(population_size=16,cohort_quadrature_size=16))
    row=model.source_support_report()['source_families']['dashboard']
    assert row['finite_quantile_cohorts']==1
    assert row['observation_rows']==0
    assert row['observation_rows_with_duration_candidates']==0
    assert row['duration_candidate_rows_by_channel']['elapsed']==2
    assert row['report_log_scales']==[.25]


def test_source_posterior_diagnostics_do_not_mutate_likelihood_or_assert_identification():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    states=np.random.default_rng(3).normal(size=(2,8,model.layout.size))
    before=model.log_likelihood(states[0,0],[0])
    report=model.source_support_report(states)
    z=states[:,:,model.source[0,0]].ravel()
    info=report['source_families']['source']['offsets']['elapsed']
    assert info['marginal_variance_contraction']==pytest.approx(1.-np.var(z,ddof=1))
    assert info['posterior_log_offset']['median']==pytest.approx(np.median(.25*z))
    assert info['posterior_multiplier']['median']==pytest.approx(np.median(np.exp(.25*z)))
    assert model.log_likelihood(states[0,0],[0])==before
    assert 'Not established' in report['reviewed_same_estimand_overlap']


@pytest.mark.parametrize('kind',['flat','one_draw','wrong_coordinates','nan','infinity'])
def test_source_diagnostics_reject_invalid_or_insufficient_state_arrays(kind):
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    states=np.zeros((1,2,model.layout.size))
    if kind=='flat': states=states.ravel()
    elif kind=='one_draw': states=states[:,:1]
    elif kind=='wrong_coordinates': states=states[:,:,:-1]
    else: states[0,0,0]=np.nan if kind=='nan' else np.inf
    with pytest.raises(ValueError,match='finite chains-by-draws'):
        model.source_support_report(states)


def test_source_contraction_matches_canonical_sample_variance_not_population_variance():
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    states=np.zeros((1,2,model.layout.size))
    states[0,1,model.source[0,0]]=2.
    info=model.source_support_report(states)['source_families']['source']['offsets']['elapsed']
    assert info['marginal_variance_contraction']==-1.


def test_count_and_money_only_cases_are_not_mislabeled_duration_cases():
    data=data_fixture()
    p=data['programs'][0]
    p['observations'][2]['case_id']='count_only'
    money=dict(copy.deepcopy(p['observations'][0]),id='money',case_id='money_only',
               source_family='fee_source',operators=[dict(basis='payer_fee_total')])
    p['observations'].append(money)
    report=VisitHierarchy(data,Config(population_size=16)).source_support_report()
    ordinary=report['source_families']['source']
    assert ordinary['count_rows']==1
    assert ordinary['duration_candidate_unselected_case_ids']==[dict(program_id='J__P',case_id='c')]
    fees=report['source_families']['fee_source']
    assert fees['money_rows']==1
    assert fees['observation_rows_with_duration_candidates']==0
    assert fees['duration_candidate_unselected_case_ids']==[]
    assert fees['duration_contamination_probability'] is None
