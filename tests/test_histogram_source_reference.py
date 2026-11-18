"""Invented exact-cohort/report integration; not empirical source calibration."""
import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.source_comparisons import comparison_digest
from procbench_fixtures import data_fixture, observation
from test_cohort_histograms import histogram_fixture
from test_source_offset_hierarchy import hierarchy_data


def anchored_fixture():
    data = data_fixture()
    program = data['programs'][0]
    program['observations'] = [dict(
        observation('forum_case', 'whole_case_clock', 40., 50.),
        source_family='forum_document')]
    cohort = histogram_fixture()
    cohort.update(operators=[dict(basis='whole_case_clock', start='process_start',
                                  end='initial_decision')], operator_weights=[1.],
                  bin_edges=[0, 15, 30, None], bin_counts=[3, 4, 3])
    program['histogram_cohorts'] = [cohort]
    data['source_offset_hierarchy'] = dict(
        schema_version='source-offset-hierarchy/2', source_family_grouping='document',
        elapsed_time_unit='calendar_days', reference_type='administrative',
        type_scale_prior=dict(median=.5, log_sd=.4),
        document_scale_prior=dict(median=.2, log_sd=.3),
        documents=[dict(document_id='forum_document', source_type='forum')],
        reference_histogram_cohorts=[dict(
            program_id=program['id'], cohort_id=cohort['cohort_id'],
            source_family=cohort['source_family'], cohort_sha256=comparison_digest(cohort))])
    return data


def config(**kwargs):
    return Config(modeled_channels=('elapsed',), population_size=256, **kwargs)


def test_reference_adds_no_fake_report_or_likelihood_factor():
    data = anchored_fixture()
    original = copy.deepcopy(data)
    model = VisitHierarchy(data, config())
    assert data == original
    hierarchy = model.source_offset_hierarchy
    assert model.sources == ['forum_document']
    assert hierarchy.documents_by_type['administrative'] == ()
    assert hierarchy.documents == ('forum_document',)
    assert len(hierarchy.coordinates) == 2  # Type spread and forum contrast only.
    assert model.programs[0]['cases'] == ['c']
    z = np.zeros(model.layout.size)
    parts = model.log_likelihood(z, [0], parts=True)
    assert len(parts) == 2
    histogram_key = 'J__P:histogram_cohort:published_histogram'
    assert histogram_key in parts
    z[hierarchy.type_coordinates['forum']] = 1.5
    changed = model.log_likelihood(z, [0], parts=True)
    assert changed[histogram_key] == parts[histogram_key]
    assert changed['J__P:forum_case'] != parts['J__P:forum_case']
    assert model.log_likelihood(z, [0]) == pytest.approx(
        model.log_likelihood_reference(z, [0]), abs=1e-12)
    report = model.source_support_report()
    assert report['source_families']['administrative_table']['exact_histogram_cohorts'] == 1
    assert not report['source_families']['administrative_table']['duration_offset_coordinates_allocated']
    family_reference = report['source_families']['administrative_table']['reference_histogram_support']
    assert family_reference['exact_histogram_reporting_offset'] == 'not_applicable'
    assert family_reference['exact_histogram_factors'] == 1
    assert family_reference['recorded_cases'] == 10
    assert not family_reference['noisy_report_offset_flags_apply_to_histogram']
    assert not family_reference['noisy_report_document_also_present']
    h = report['source_offset_hierarchy']
    assert h['source_types']['administrative']['informative_duration_rows'] == 0
    assert h['reference_histogram_support']['recorded_cases'] == 10
    assert h['reference_histogram_support']['exact_histogram_factors'] == 1
    assert h['reference_histogram_support']['additional_likelihood_factors'] == 0
    assert not h['reference_histogram_support']['matched_comparison_established']
    assert not h['reference_histogram_support']['substantive_review_verified']
    assert not h['bias_identification_established']


def test_v1_does_not_accept_histogram_only_reference_or_v2_fields():
    data = anchored_fixture()
    data['source_offset_hierarchy']['schema_version'] = 'source-offset-hierarchy/1'
    with pytest.raises(ValueError, match='unexpected or missing'):
        VisitHierarchy(data, config())
    del data['source_offset_hierarchy']['reference_histogram_cohorts']
    with pytest.raises(ValueError, match='no mapped duration document'):
        VisitHierarchy(data, config())


@pytest.mark.parametrize('field,value,match', [
    ('program_id', 'missing', 'missing or ambiguous'),
    ('cohort_id', 'missing', 'missing or ambiguous'),
    ('source_family', 'wrong', 'source family differs'),
    ('cohort_sha256', '0'*64, 'binding is stale'),
    ('cohort_sha256', 'not-a-digest', 'canonical SHA-256'),
    ('program_id', 'unknown', 'resolved nonempty'),
])
def test_reference_bindings_fail_closed(field, value, match):
    data = anchored_fixture()
    data['source_offset_hierarchy']['reference_histogram_cohorts'][0][field] = value
    with pytest.raises(ValueError, match=match):
        VisitHierarchy(data, config())


@pytest.mark.parametrize('references', [None, [], {}, [None]])
def test_v2_requires_actual_anchor_members(references):
    data = anchored_fixture()
    data['source_offset_hierarchy']['reference_histogram_cohorts'] = references
    with pytest.raises(ValueError):
        VisitHierarchy(data, config())


def test_duplicate_reference_and_changed_counts_are_not_silently_consumed():
    data = anchored_fixture()
    refs = data['source_offset_hierarchy']['reference_histogram_cohorts']
    refs.append(copy.deepcopy(refs[0]))
    with pytest.raises(ValueError, match='Repeated histogram reference'):
        VisitHierarchy(data, config())
    refs.pop()
    data['programs'][0]['histogram_cohorts'][0]['bin_counts'] = [4, 3, 3]
    with pytest.raises(ValueError, match='binding is stale'):
        VisitHierarchy(data, config())


@pytest.mark.parametrize('mutation', ['nonexact', 'dependent', 'trivial', 'missing', 'duplicate'])
def test_anchor_cannot_bypass_existing_cohort_contract(mutation):
    data = anchored_fixture()
    program = data['programs'][0]
    c = program['histogram_cohorts'][0]
    if mutation == 'nonexact':
        c['reporting'] = 'noisy_published_histogram'
    elif mutation == 'dependent':
        c['independent_of_other_evidence'] = False
    elif mutation == 'trivial':
        c.update(bin_counts=[10], bin_edges=[0, None])
    elif mutation == 'missing':
        program['histogram_cohorts'] = []
    else:
        program['histogram_cohorts'].append(copy.deepcopy(c))
    data['source_offset_hierarchy']['reference_histogram_cohorts'][0]['cohort_sha256'] = comparison_digest(c)
    with pytest.raises(ValueError):
        VisitHierarchy(data, config())


def test_same_family_reference_and_report_types_must_agree():
    data = anchored_fixture()
    data['programs'][0]['observations'][0]['source_family'] = 'administrative_table'
    data['source_offset_hierarchy']['documents'][0]['document_id'] = 'administrative_table'
    with pytest.raises(ValueError, match='conflicting report source type'):
        VisitHierarchy(data, config())


def test_shared_histogram_and_noisy_reference_family_keeps_separate_offset_semantics():
    data = anchored_fixture()
    for index, document in enumerate(['administrative_table', 'second_admin_report']):
        data['programs'][0]['observations'].append(dict(
            observation('admin_case_'+str(index), 'whole_case_clock', 15., 25., case='a'+str(index)),
            source_family=document))
        data['source_offset_hierarchy']['documents'].append(
            dict(document_id=document, source_type='administrative'))
    model = VisitHierarchy(data, config())
    row = model.source_support_report()['source_families']['administrative_table']
    assert row['duration_offset_coordinates_allocated']
    assert row['duration_offset_hierarchy_member']
    assert not row['duration_offset_fixed_zero']
    assert row['reference_histogram_support']['noisy_report_document_also_present']
    assert not row['reference_histogram_support']['noisy_report_offset_flags_apply_to_histogram']
    assert row['reference_histogram_support']['exact_histogram_reporting_offset'] == 'not_applicable'
    z = np.zeros(model.layout.size)
    before = model.log_likelihood(z, [0], parts=True)
    z[model.source_offset_hierarchy.document_coordinates['administrative'][0]] = 1.
    after = model.log_likelihood(z, [0], parts=True)
    assert before['J__P:histogram_cohort:published_histogram'] == after['J__P:histogram_cohort:published_histogram']
    assert before['J__P:admin_case_0'] != after['J__P:admin_case_0']


def test_v2_with_existing_reference_documents_matches_v1_target_and_layout():
    data = hierarchy_data()
    c = anchored_fixture()['programs'][0]['histogram_cohorts'][0]
    data['programs'][0]['histogram_cohorts'] = [c]
    legacy = VisitHierarchy(data, config())
    v2 = copy.deepcopy(data)
    decl = v2['source_offset_hierarchy']
    decl['schema_version'] = 'source-offset-hierarchy/2'
    decl['reference_histogram_cohorts'] = [dict(program_id='J__P',
        cohort_id=c['cohort_id'], source_family=c['source_family'],
        cohort_sha256=comparison_digest(c))]
    model = VisitHierarchy(v2, config())
    assert model.layout.size == legacy.layout.size
    for z in np.random.default_rng(720).normal(scale=.2, size=(12, model.layout.size)):
        assert model.log_likelihood(z, [0]) == legacy.log_likelihood(z, [0])
    assert 'reference_histogram_support' not in legacy.source_support_report()['source_offset_hierarchy']


def test_seeded_sampler_runs_and_keeps_scalar_reference_agreement():
    model = VisitHierarchy(anchored_fixture(), config(chains=1, warmup=0, draws=8, seed=913))
    states, routes, likelihood, _ = model.sample()
    assert states.shape == (1, 8, model.layout.size)
    assert np.isfinite(likelihood).all()
    for z, route, ll in zip(states[0], routes[0], likelihood[0]):
        assert ll == pytest.approx(model.log_likelihood_reference(z, route), abs=1e-12)
