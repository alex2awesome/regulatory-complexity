"""Source-free contracts for optional fixed source-type report scales."""

import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.source_precision import (attach_precision_annotation,
    resolved_precision_annotation, validate_source_type_report_scales)
from procbench_fixtures import data_fixture
from test_analytic_phase import config as analytic_config, phase_data
from test_cohort_quantiles import compiler_inputs, model_data
from test_compile_visit_durations import inputs
from test_histogram_hierarchy import model_data as histogram_data
from test_typical_range_reports import range_data


def declaration(scale=.35, source_type='forum'):
    return dict(schema_version='source-type-report-scales/1',
        elapsed={source_type:dict(report_log_scale=scale,
            calibration_id='source-free-test-calibration-reference')},
        fallback='config_report_sd')


def annotate(record, source_type='forum', scale=.35):
    return attach_precision_annotation(record,
        resolved_precision_annotation(source_type,declaration(scale,source_type)))


def test_no_declaration_keeps_compiler_and_legacy_diagnostics_free_of_new_fields():
    e,v,s,d,p=inputs()
    result=compile_durations(e,v,s,d,p)
    assert result['policy']==p
    assert 'source_precision' not in result
    assert all('source_type' not in o and 'report_log_scale' not in o
               and 'report_scale_basis' not in o['provenance']
               for o in result['observations'])
    model=VisitHierarchy(data_fixture(),Config(population_size=16))
    report=model.source_support_report()
    assert 'source_precision_policy' not in report
    assert all('source_precision' not in row for row in report['source_families'].values())


def test_compiler_resolves_fixed_scale_independently_of_offset_grouping():
    for grouping in ('document','type'):
        e,v,s,d,p=inputs()
        p['source_type_report_scales']=declaration(.37)
        result=compile_durations(e,v,s,d,p,source_family_grouping=grouping,
            source_family_kinds={'document':'forum_thread'})
        o=result['observations'][0]
        assert o['source_type']=='forum'
        assert o['report_log_scale']==.37
        assert o['provenance']['report_scale_basis']==dict(
            kind='fixed_source_type_declaration',
            calibration_id='source-free-test-calibration-reference',
            calibration_provenance='declared_reference_unverified')
        coverage=result['source_precision']
        assert coverage['learned_coordinates']==0
        assert coverage['fixed_declared_scales_by_type']['forum']['ordinary_factors']==1
        assert not coverage['unused_declared_source_types']
        assert 'did not hash-review' in coverage['calibration_qualification']


def test_compiler_surfaces_fallback_unused_type_and_unknown_n_floor_state():
    e,v,s,d,p=inputs()
    e['measurements'][0].update(case_id=None,statistic='median',n=None)
    s['measurements'][0].update(statistic_interpretation='population_median',
                               population_scope='all_cases')
    p={'source_type_report_scales':declaration(.3,'forum')}
    result=compile_durations(e,v,s,d,p,
        source_family_kinds={'document':'official_stats'})
    o=result['observations'][0]
    assert o['source_type']=='agency_dashboard'
    assert 'report_log_scale' not in o
    assert o['provenance']['report_scale_basis']['reason']=='source_type_not_declared'
    coverage=result['source_precision']
    assert coverage['unused_declared_source_types']==['forum']
    assert coverage['fallback_counts']==dict(source_type_not_declared_factors=1,
        source_type_unresolved_factors=0,unknown_n_floor_eligible_factors=1)
    model=VisitHierarchy(dict(programs=[dict(id=e['program_id'],routes=[dict(id='r',prior_weight=1.,
        operations=[dict(id='review',actor_id='A',actor_role='agency',task_type='review',
            markers=['decision'])],blocks=[dict(id='b',operations=['review'])])],
        observations=result['observations'])]),Config(population_size=16,modeled_channels=('elapsed',)))
    detail=model.source_support_report()['source_families']['document']['source_precision']
    assert detail['config_fallback_factors']==1
    assert detail['unknown_n_floor_factors']==1
    assert detail['unknown_n_floor_raised_factors']==1


@pytest.mark.parametrize('mutation',[
    lambda d: d.update(schema_version='wrong'),
    lambda d: d.update(fallback='other'),
    lambda d: d.update(elapsed={}),
    lambda d: d['elapsed']['forum'].update(report_log_scale=True),
    lambda d: d['elapsed']['forum'].update(report_log_scale=0.),
    lambda d: d['elapsed']['forum'].update(report_log_scale=-.1),
    lambda d: d['elapsed']['forum'].update(report_log_scale=float('nan')),
    lambda d: d['elapsed']['forum'].update(report_log_scale=float('inf')),
    lambda d: d['elapsed']['forum'].update(calibration_id=''),
    lambda d: d.update(elapsed={'invented_type':d['elapsed']['forum']}),
    lambda d: d.update(extra=True),
])
def test_invalid_declarations_fail_strictly(mutation):
    value=declaration()
    mutation(value)
    with pytest.raises(ValueError):
        validate_source_type_report_scales(value,{
            'agency_official':(), 'agency_dashboard':(), 'news':(),
            'forum':(), 'third_party':(), 'oversight':()})


def test_joint_cohort_carries_one_scale_and_unverified_reference():
    e,v,s,d,p,b=compiler_inputs()
    p['source_type_report_scales']=declaration(.41,'agency_dashboard')
    compiled=compile_durations(e,v,s,d,p,cohort_bindings=b,
        source_family_kinds={'document':'official_stats'})
    assert compiled['observations']==[]
    c=compiled['quantile_cohorts'][0]
    assert (c['source_type'],c['report_log_scale'])==('agency_dashboard',.41)
    assert c['provenance']['report_scale_basis']['calibration_provenance']=='declared_reference_unverified'
    assert all('report_scale_basis' not in r['provenance'] for r in c['reports'])
    row=compiled['source_precision']['fixed_declared_scales_by_type']['agency_dashboard']
    assert row['finite_quantile_cohorts']==1 and row['finite_quantile_report_rows']==2
    data=model_data()
    data['programs'][0]['quantile_cohorts']=compiled['quantile_cohorts']
    model=VisitHierarchy(data,Config(population_size=16,cohort_quadrature_size=16,
                                    modeled_channels=('elapsed',)))
    assert model.log_likelihood(np.zeros(model.layout.size),[0])==pytest.approx(
        model.log_likelihood_reference(np.zeros(model.layout.size),[0]))
    detail=model.source_support_report()['source_families']['document']['source_precision']
    assert detail['fixed_declared_factors']==1
    assert detail['calibration_references'][0]['calibration_verified'] is False


def test_mixed_source_types_cannot_be_hidden_inside_one_cohort():
    e,v,s,d,p,b=compiler_inputs()
    e['measurements'][1]['doc_id']='second_document'
    d.append(dict(id='second_document',text='Evidence'))
    p['source_type_report_scales']=dict(schema_version='source-type-report-scales/1',
        elapsed={
            'agency_dashboard':dict(report_log_scale=.3,calibration_id='dashboard-ref'),
            'forum':dict(report_log_scale=.3,calibration_id='forum-ref')},
        fallback='config_report_sd')
    with pytest.raises(ValueError,match='one resolved source type'):
        compile_durations(e,v,s,d,p,cohort_bindings=b,source_family_kinds={
            'document':'official_stats','second_document':'forum_thread'})


def test_declaration_does_not_admit_a_bare_denominator():
    e,v,s,d,p=inputs()
    e['measurements'][0].update(case_id=None,statistic='median',n=25)
    s['measurements'][0].update(statistic_interpretation='population_median',
                               population_scope='all_cases')
    p={'source_type_report_scales':declaration()}
    result=compile_durations(e,v,s,d,p,source_family_kinds={'document':'forum_thread'})
    assert not result['observations'] and not result['quantile_cohorts']
    assert 'finite_cohort_requires_explicit_joint_sampling_contract' in result['dispositions'][0]['reasons']


def test_equal_scale_annotation_preserves_layout_target_and_rng_sequence():
    plain_data=data_fixture()
    declared_data=copy.deepcopy(plain_data)
    annotate(declared_data['programs'][0]['observations'][0],scale=.25)
    cfg=Config(chains=1,warmup=0,draws=8,population_size=16)
    plain=VisitHierarchy(plain_data,cfg)
    declared=VisitHierarchy(declared_data,cfg)
    assert plain.layout.slices.keys()==declared.layout.slices.keys()
    for name in plain.layout.slices:
        np.testing.assert_array_equal(plain.layout.slices[name],declared.layout.slices[name])
    assert plain.layout.size==declared.layout.size
    z=np.zeros(plain.layout.size)
    assert plain.log_likelihood(z,[0])==declared.log_likelihood(z,[0])
    left=plain.sample()
    right=declared.sample()
    for a,b in zip(left[:3],right[:3]):
        np.testing.assert_array_equal(a,b)
    assert left[3]==right[3]


@pytest.mark.parametrize('field,value',[
    ('report_log_scale',True),('report_log_scale',0.),('report_log_scale',-.1),
    ('report_log_scale',float('nan')),('report_log_scale',float('inf')),
])
def test_invalid_resolved_scales_are_rejected_at_construction(field,value):
    data=data_fixture()
    o=data['programs'][0]['observations'][0]
    annotate(o)
    o[field]=value
    with pytest.raises(ValueError,match='Fixed source precision'):
        VisitHierarchy(data,Config(population_size=16))


def test_resolved_annotation_requires_strict_provenance_and_known_type():
    for mutation in ('null_basis','verified','unknown_type','mismatched_fallback'):
        data=data_fixture(); o=data['programs'][0]['observations'][0]
        annotate(o)
        if mutation=='null_basis': o['provenance']['report_scale_basis']=None
        elif mutation=='verified':
            o['provenance']['report_scale_basis']['calibration_provenance']='verified'
        elif mutation=='unknown_type': o['source_type']='invented_type'
        else:
            o.pop('report_log_scale')
            o['provenance']['report_scale_basis']=dict(kind='config_report_sd_fallback',
                reason='source_type_unresolved',calibration_provenance='not_applicable')
        with pytest.raises(ValueError):
            VisitHierarchy(data,Config(population_size=16))


def test_source_type_only_metadata_is_legacy_inert_for_rows_and_cohorts():
    row_data=data_fixture()
    row_data['programs'][0]['observations'][0]['source_type']='forum'
    plain=VisitHierarchy(data_fixture(),Config(population_size=16))
    typed=VisitHierarchy(row_data,Config(population_size=16))
    z=np.zeros(plain.layout.size)
    assert not typed.source_precision_active
    assert typed.layout.slices.keys()==plain.layout.slices.keys()
    assert typed.log_likelihood(z,[0])==plain.log_likelihood(z,[0])
    cohort_data=model_data()
    cohort_data['programs'][0]['quantile_cohorts'][0]['source_type']='agency_dashboard'
    cohort=VisitHierarchy(cohort_data,Config(population_size=16,cohort_quadrature_size=16))
    assert not cohort.source_precision_active
    typical_data=range_data()
    typical_data['programs'][0]['observations'][0]['source_type']='forum'
    typical=VisitHierarchy(typical_data,Config(population_size=16))
    assert not typical.source_precision_active


@pytest.mark.parametrize('kind',['typical','residual','count','money','effort'])
def test_generic_scale_cannot_override_special_report_contracts(kind):
    if kind=='typical':
        data=range_data(); o=data['programs'][0]['observations'][0]
    else:
        data=data_fixture(); o=data['programs'][0]['observations'][0]
        if kind=='residual':
            o.update(case_id=None,statistic='report_only',operators=[dict(
                basis='unmodeled_duration',median_days=7.,log_scale=3.)])
        elif kind=='count':
            o['operators']=[dict(basis='visit_count')]
        elif kind=='money':
            o['operators']=[dict(basis='payer_fee_total')]
        else:
            o['operators']=[dict(basis='payer_hours')]
    annotate(o)
    with pytest.raises(ValueError,match='only an elapsed report kernel'):
        VisitHierarchy(data,Config(population_size=16))


def test_active_elapsed_precision_does_not_relabel_labor_rows_or_cohorts():
    data=model_data()
    elapsed=copy.deepcopy(data_fixture()['programs'][0]['observations'][0])
    annotate(elapsed,scale=.6)
    data['programs'][0]['observations']=[elapsed]
    cohort=data['programs'][0]['quantile_cohorts'][0]
    cohort['source_family']='labor_dashboard'
    cohort['operators']=[dict(basis='agency_hours')]
    model=VisitHierarchy(data,Config(population_size=16,cohort_quadrature_size=16))
    report=model.source_support_report()['source_families']
    assert report['source']['report_log_scales']==[.6]
    assert report['labor_dashboard']['report_log_scales']==[.25]
    assert report['labor_dashboard']['source_precision']==dict(
        fixed_declared_factors=0,config_fallback_factors=0,implicit_fallback_factors=0,
        unknown_n_floor_factors=0,unknown_n_floor_raised_factors=0,
        source_types=[],calibration_references=[])
    states=np.zeros((2,8,model.layout.size))
    routes=np.zeros((2,8,len(model.programs)),dtype=int)
    likelihood=np.zeros((2,8))
    cohort_report=model.report(states,routes,likelihood)['programs']['J__P']['quantile_cohorts']['dashboard']
    assert 'source_precision' not in cohort_report


def test_exact_histogram_rejects_narrative_source_precision_annotation():
    data=histogram_data()
    annotate(data['programs'][0]['histogram_cohorts'][0])
    with pytest.raises(ValueError,match='explicit clock/population/count contract'):
        VisitHierarchy(data,Config(population_size=256,modeled_channels=('elapsed',)))


def test_fixed_scale_matches_vector_scalar_and_analytic_paths_and_floor_composition():
    data=phase_data(); annotate(data['programs'][0]['observations'][0],scale=.7)
    model=VisitHierarchy(data,analytic_config(unknown_n_report_sd_floor=.5))
    z=np.zeros(model.layout.size)
    assert model.log_likelihood(z,[0])==model.log_likelihood_reference(z,[0])
    row=model.source_support_report()['source_families']['source']
    assert row['report_log_scales']==[.7]
    detail=row['source_precision']
    assert detail['unknown_n_floor_factors']==1
    assert detail['unknown_n_floor_raised_factors']==0
    lower=phase_data(); annotate(lower['programs'][0]['observations'][0],scale=.2)
    lower_model=VisitHierarchy(lower,analytic_config(unknown_n_report_sd_floor=.5))
    lower_row=lower_model.source_support_report()['source_families']['source']
    assert lower_row['report_log_scales']==[.5]
    assert lower_row['source_precision']['unknown_n_floor_raised_factors']==1


def test_type_names_have_no_hard_ranking_and_behavior_follows_supplied_scale():
    def likelihood(source_type,scale):
        data=data_fixture()
        data['programs'][0]['observations']=data['programs'][0]['observations'][:1]
        annotate(data['programs'][0]['observations'][0],source_type=source_type,scale=scale)
        model=VisitHierarchy(data,Config(population_size=16,modeled_channels=('elapsed',)))
        return model.log_likelihood(np.zeros(model.layout.size),[0])
    forum_narrow=likelihood('forum',.18)
    oversight_narrow=likelihood('oversight',.18)
    forum_wide=likelihood('forum',.82)
    oversight_wide=likelihood('oversight',.82)
    assert forum_narrow==oversight_narrow
    assert forum_wide==oversight_wide
    assert forum_narrow!=forum_wide
    assert forum_narrow-oversight_narrow==forum_wide-oversight_wide==0.


def test_finite_cohort_nondefault_scale_matches_legacy_scale_oracle_and_ignores_floor():
    fixed_data=model_data(37)
    annotate(fixed_data['programs'][0]['quantile_cohorts'][0],
             source_type='agency_dashboard',scale=.63)
    plain_data=model_data(37)
    fixed=VisitHierarchy(fixed_data,Config(population_size=16,cohort_quadrature_size=64,
        report_sd=.25,unknown_n_report_sd_floor=5.,modeled_channels=('elapsed',)))
    oracle=VisitHierarchy(plain_data,Config(population_size=16,cohort_quadrature_size=64,
        report_sd=.63,unknown_n_report_sd_floor=.1,modeled_channels=('elapsed',)))
    assert fixed.layout.size==oracle.layout.size
    for z in np.random.default_rng(8801).normal(scale=.3,size=(6,fixed.layout.size)):
        assert fixed.log_likelihood(z,[0])==oracle.log_likelihood(z,[0])
        assert fixed.log_likelihood_reference(z,[0])==oracle.log_likelihood_reference(z,[0])
        assert fixed.log_likelihood(z,[0])==fixed.log_likelihood_reference(z,[0])
    assert fixed.source_support_report()['source_families']['dashboard']['report_log_scales']==[.63]


def test_disjunctive_intervals_use_nondefault_declared_scale_in_both_paths():
    fixed_data=data_fixture()
    fixed_data['programs'][0]['observations']=fixed_data['programs'][0]['observations'][:1]
    observation=fixed_data['programs'][0]['observations'][0]
    observation['report_intervals']=[[15.,18.],[22.,25.]]
    annotate(observation,scale=.61)
    plain_data=copy.deepcopy(fixed_data)
    plain=plain_data['programs'][0]['observations'][0]
    plain.pop('source_type'); plain.pop('report_log_scale')
    plain['provenance'].pop('report_scale_basis')
    fixed=VisitHierarchy(fixed_data,Config(population_size=16,report_sd=.25,
        modeled_channels=('elapsed',)))
    oracle=VisitHierarchy(plain_data,Config(population_size=16,report_sd=.61,
        modeled_channels=('elapsed',)))
    for z in np.random.default_rng(1902).normal(scale=.4,size=(6,fixed.layout.size)):
        assert fixed.log_likelihood(z,[0])==oracle.log_likelihood(z,[0])
        assert fixed.log_likelihood_reference(z,[0])==oracle.log_likelihood_reference(z,[0])
        assert fixed.log_likelihood(z,[0])==fixed.log_likelihood_reference(z,[0])


def test_known_n_sampling_variation_shrinks_but_report_error_does_not_vanish():
    models=[]
    sampling_variances=[]
    report_variances=[]
    for n in (11,101,1001):
        data=model_data(n)
        cohort=data['programs'][0]['quantile_cohorts'][0]
        # Use one statistic so the deterministic Sobol grid measures exactly the
        # same pinned population median at each stated n.
        cohort['reports']=cohort['reports'][:1]
        annotate(cohort,source_type='agency_dashboard',scale=.35)
        model=VisitHierarchy(data,Config(population_size=64,cohort_quadrature_size=4096,
            modeled_channels=('elapsed',)))
        values=np.exp(np.linspace(-1.5,1.5,257))
        medians=model.programs[0]['quantile_cohorts'][0]['grid'].values(values)[:,0]
        sampling_variances.append(float(np.var(np.log(medians))))
        # df=4 Student-t has variance df/(df-2)*scale^2 = 2*scale^2.
        report_variances.append(2*.35**2)
        models.append(model)
    assert sampling_variances[2] < sampling_variances[1] < sampling_variances[0]
    assert report_variances==pytest.approx([.245,.245,.245])
    assert all(sampling+report >= .245 for sampling,report in
               zip(sampling_variances,report_variances))
    assert all(m.source_support_report()['source_families']['dashboard']
               ['report_log_scales']==[.35] for m in models)


def test_declared_scale_adds_no_coordinate_even_with_no_matching_observation():
    plain=VisitHierarchy(data_fixture(),Config(population_size=16))
    data=data_fixture()
    annotate(data['programs'][0]['observations'][0],scale=.6)
    declared=VisitHierarchy(data,Config(population_size=16))
    assert declared.layout.slices.keys()==plain.layout.slices.keys()
    for name in plain.layout.slices:
        np.testing.assert_array_equal(plain.layout.slices[name],declared.layout.slices[name])
    assert declared.layout.size==plain.layout.size
    e,v,s,d,p=inputs()
    p['source_type_report_scales']=declaration(.4,'oversight')
    compiled=compile_durations(e,v,s,d,p,source_family_kinds={'document':'forum_thread'})
    assert compiled['source_precision']['unused_declared_source_types']==['oversight']
    assert compiled['source_precision']['learned_coordinates']==0
