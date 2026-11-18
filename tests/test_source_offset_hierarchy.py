"""Source-free mechanical checks for the optional V6 source-bias hierarchy."""
import copy
from dataclasses import replace
import json
import math

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from procbench_fixtures import data_fixture
from test_source_comparisons import reviewed_fixture


def hierarchy_data():
    data = data_fixture()
    p = data['programs'][0]
    template = copy.deepcopy(p['observations'][0])
    rows=[]
    documents = [
        ('official_a','official'), ('official_b','official'),
        ('news_a','news'), ('news_b','news'), ('forum_a','forum')]
    for index,(document, _) in enumerate(documents):
        row=copy.deepcopy(template)
        row.update(id='elapsed_'+str(index),case_id='case_'+str(index),source_family=document)
        rows.append(row)
    count=copy.deepcopy(p['observations'][2])
    count.update(id='count_only',case_id='count_case',source_family='count_document')
    p['observations']=rows+[count]
    data['elapsed_time_unit']='calendar_days'
    data['source_offset_hierarchy']=dict(
        schema_version='source-offset-hierarchy/1',
        source_family_grouping='document', elapsed_time_unit='calendar_days',
        reference_type='official',
        type_scale_prior=dict(median=.4,log_sd=.3),
        document_scale_prior=dict(median=.2,log_sd=.25),
        documents=[dict(document_id=document,source_type=source_type)
                   for document,source_type in documents])
    return data


def cfg():
    return Config(population_size=16,modeled_channels=('elapsed',))


def test_reference_type_and_centered_document_geometry_are_exact():
    model=VisitHierarchy(hierarchy_data(),cfg())
    hierarchy=model.source_offset_hierarchy
    assert hierarchy is not None
    # type scale + two nonreference type effects + document scale + one
    # contrast for each two-document type.
    assert len(hierarchy.coordinates)==6
    assert np.all(model.source==-1)
    z=np.zeros(model.layout.size)
    z[hierarchy.type_coordinates['news']]=1.5
    z[hierarchy.type_coordinates['forum']]=-.5
    z[hierarchy.document_coordinates['official'][0]]=2.
    z[hierarchy.document_coordinates['news'][0]]=-1.
    transformed=hierarchy.transformed(z)
    assert transformed['type_effects']['official']==0.
    assert transformed['type_effects']['news']==pytest.approx(.6)
    assert transformed['type_effects']['forum']==pytest.approx(-.2)
    assert transformed['document_residuals']['forum_a']==0.
    for source_type in ('official','news'):
        residuals=[transformed['document_residuals'][name]
                   for name in hierarchy.documents_by_type[source_type]]
        assert sum(residuals)==pytest.approx(0.,abs=1e-15)
    offsets=model.parameters(z)['source'][0]
    for document in hierarchy.documents:
        assert offsets[model.sources.index(document)]==pytest.approx(
            transformed['document_offsets'][document])
    assert offsets[model.sources.index('count_document')]==0.


@pytest.mark.parametrize('change,match', [
    (lambda d: d['source_offset_hierarchy'].__setitem__('source_family_grouping','source_type'),
     'document-grouped'),
    (lambda d: d['source_offset_hierarchy'].__setitem__('elapsed_time_unit','business_days'),
     'calendar differs'),
    (lambda d: d['source_offset_hierarchy']['documents'][0].__setitem__('source_type','unknown'),
     'resolved nonempty'),
    (lambda d: d['source_offset_hierarchy']['documents'].pop(), 'exactly cover'),
    (lambda d: d['source_offset_hierarchy']['documents'].append(
        dict(document_id='extra',source_type='news')), 'exactly cover'),
    (lambda d: d['source_offset_hierarchy']['documents'][1].__setitem__(
        'document_id','official_a'), 'distinct'),
])
def test_hierarchy_declaration_fails_closed(change,match):
    data=hierarchy_data()
    change(data)
    with pytest.raises(ValueError,match=match):
        VisitHierarchy(data,cfg())


def test_hierarchy_refuses_active_labor_channels_in_bounded_v1():
    with pytest.raises(ValueError,match='elapsed-only'):
        VisitHierarchy(hierarchy_data(),Config(population_size=16))


def test_effective_offsets_drive_both_likelihood_paths_and_legacy_move_is_disabled():
    model=VisitHierarchy(hierarchy_data(),cfg())
    hierarchy=model.source_offset_hierarchy
    z=np.zeros(model.layout.size)
    baseline=model.log_likelihood(z,[0])
    z[hierarchy.type_coordinates['news']]=1.
    changed=model.log_likelihood(z,[0])
    assert changed != baseline
    assert changed==pytest.approx(model.log_likelihood_reference(z,[0]),abs=1e-12)
    moved,value=model.source_location_update(z,[0],changed,np.random.default_rng(4))
    np.testing.assert_array_equal(moved,z)
    assert value==changed


def test_transformed_support_report_separates_prior_summary_from_identification():
    model=VisitHierarchy(hierarchy_data(),cfg())
    states=np.random.default_rng(12).normal(size=(2,8,model.layout.size))
    report=model.source_support_report(states)
    hierarchy=report['source_offset_hierarchy']
    assert hierarchy['bias_identification_established'] is False
    assert hierarchy['reference_zero_is_coordinate_convention_not_unbiasedness'] is True
    assert hierarchy['source_types']['official']['type_log_offset'][
        'marginal_variance_contraction'] is None
    assert hierarchy['documents']['forum_a']['document_log_residual'][
        'marginal_variance_contraction'] is None
    assert hierarchy['documents']['news_a']['effective_log_offset']['prior'] is not None
    assert hierarchy['documents']['news_a']['effective_log_offset']['posterior'] is not None
    assert hierarchy['documents']['news_a']['effective_multiplier']['prior']['mean'] is None
    assert hierarchy['documents']['news_a']['effective_multiplier'][
        'marginal_variance_contraction'] is None
    assert report['source_families']['count_document']['duration_offset_coordinates_allocated'] is False
    assert report['source_families']['count_document']['offsets']=={}
    assert 'exactly centered' in report['offset_parameterization']


def test_prior_variances_are_analytic_and_multiplier_moments_are_not_invented():
    model=VisitHierarchy(hierarchy_data(),cfg())
    report=model.source_support_report()['source_offset_hierarchy']
    type_variance=.4**2*math.exp(2*.3**2)
    residual_variance=.2**2*math.exp(2*.25**2)*(1-1/2)
    assert report['source_types']['news']['type_log_offset'][
        'analytic_prior_variance']==pytest.approx(type_variance)
    assert report['documents']['news_a']['document_log_residual'][
        'analytic_prior_variance']==pytest.approx(residual_variance)
    assert report['documents']['news_a']['effective_log_offset'][
        'analytic_prior_variance']==pytest.approx(type_variance+residual_variance)
    scale_variance=.4**2*math.exp(.3**2)*math.expm1(.3**2)
    assert report['scale_summaries']['type']['analytic_prior_variance']==pytest.approx(scale_variance)
    multiplier=report['documents']['news_a']['effective_multiplier']
    assert multiplier['prior_mean'] is None and multiplier['prior_variance'] is None
    assert 'infinite' in multiplier['prior_moment_status']


def test_singleton_reference_is_fixed_zero_not_an_allocated_document_coordinate():
    data=hierarchy_data()
    keep={'official_a','news_a'}
    data['programs'][0]['observations']=[o for o in data['programs'][0]['observations']
        if o['source_family'] in keep]
    data['source_offset_hierarchy']['documents']=[d for d in
        data['source_offset_hierarchy']['documents'] if d['document_id'] in keep]
    model=VisitHierarchy(data,cfg())
    states=np.random.default_rng(92).normal(size=(2,8,model.layout.size))
    report=model.source_support_report(states)
    row=report['source_families']['official_a']
    assert row['duration_offset_hierarchy_member'] is True
    assert row['duration_offset_coordinates_allocated'] is False
    assert row['duration_offset_fixed_zero'] is True
    document=report['source_offset_hierarchy']['documents']['official_a']
    assert document['effective_log_offset']['analytic_prior_variance']==0.
    assert document['effective_log_offset']['marginal_variance_contraction'] is None
    assert document['effective_multiplier']['prior_mean']==1.
    assert document['effective_multiplier']['prior_variance']==0.


def test_broad_scale_priors_serialize_without_nonfinite_json_numbers():
    data=hierarchy_data()
    data['source_offset_hierarchy']['type_scale_prior']['log_sd']=4.
    data['source_offset_hierarchy']['document_scale_prior']['log_sd']=4.
    report=VisitHierarchy(data,cfg()).source_support_report()['source_offset_hierarchy']
    json.dumps(report,allow_nan=False)
    assert report['documents']['news_a']['effective_multiplier']['prior']['mean'] is None


def test_conflicting_document_type_in_comparison_review_fails_closed():
    data=reviewed_fixture()
    documents=[]
    for observation,source_type in zip(data['programs'][0]['observations'],
                                       ('administrative','forum')):
        documents.append(dict(document_id=observation['source_family'],source_type=source_type))
    data['source_offset_hierarchy']=dict(schema_version='source-offset-hierarchy/1',
        source_family_grouping='document',elapsed_time_unit='calendar_days',
        reference_type='administrative',type_scale_prior=dict(median=.4,log_sd=.3),
        document_scale_prior=dict(median=.2,log_sd=.25),documents=documents)
    VisitHierarchy(data,cfg())
    data['source_comparisons']['blocks'][0]['members'][1]['source_type']='news'
    with pytest.raises(ValueError,match='conflicting types'):
        VisitHierarchy(data,cfg())


def test_absent_declaration_keeps_legacy_source_coordinates_and_likelihood():
    data=data_fixture()
    model=VisitHierarchy(data,Config(population_size=16))
    assert model.source_offset_hierarchy is None
    assert np.all(model.source[np.array(model.active_channels)]>=0)
    z=np.random.default_rng(31).normal(size=model.layout.size)
    source=model.parameters(z)['source']
    for channel in model.active_channels:
        np.testing.assert_array_equal(source[channel],model.cfg.source_sd*z[model.source[channel]])
    assert model.log_likelihood(z,[0])==model.log_likelihood_reference(z,[0])


def test_existing_sampler_accepts_whitened_hierarchy_coordinates():
    model=VisitHierarchy(hierarchy_data(),replace(cfg(),chains=1,warmup=0,draws=8,seed=81))
    states,routes,likelihood,_=model.sample()
    assert states.shape==(1,8,model.layout.size)
    assert routes.shape==(1,8,1)
    assert likelihood.shape==(1,8)
    assert np.isfinite(states).all() and np.isfinite(likelihood).all()


def test_analytic_single_phase_protocol_path_uses_transformed_offsets():
    data=hierarchy_data()
    p=data['programs'][0]
    p.update(inventory_granularity='aggregate_phases',
        clock_estimand='Artificial complete phase for source-free mechanics')
    p['routes']=[dict(id='phase',prior_weight=1.,operations=[dict(id='phase',
        actor_id='agency',actor_role='agency',task_type='phase',markers=['decision'],
        payer_work=False,agency_work=True)],blocks=[dict(id='phase',operations=['phase'])])]
    p['observations']=[o for o in p['observations'] if o['source_family']!='count_document']
    for o in p['observations']:
        o.update(case_id=None,statistic='median',operators=[dict(
            basis='single_visit_cycle',activity_ids=['phase'])])
    analytic=replace(cfg(),population_integration='analytic_single_phase',
                     hierarchy_sampler='operation_centered')
    model=VisitHierarchy(data,analytic)
    z=np.zeros(model.layout.size)
    assert np.isfinite(model.log_likelihood(z,[0]))
    z[model.source_offset_hierarchy.type_coordinates['news']]=1.
    assert model.log_likelihood(z,[0])==pytest.approx(
        model.log_likelihood_reference(z,[0]),abs=1e-12)
