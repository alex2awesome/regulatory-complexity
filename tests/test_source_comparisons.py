import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.source_comparisons import (VERSION, comparison_digest,
                                                  source_comparison_report)
from procbench_fixtures import data_fixture, observation


def reviewed_fixture(pairs=(('administrative', 'forum'),)):
    data = data_fixture()
    base = data['programs'][0]
    data['programs'] = []
    blocks = []
    for i, pair in enumerate(pairs):
        p = copy.deepcopy(base)
        p['id'] = f'jurisdiction_{i}'
        p['observations'] = [dict(observation(f'o{j}', 'whole_case_clock', 10., 20., case=None),
                                  source_family=f'document_{i}_{j}') for j in range(len(pair))]
        estimand = dict(program_id=p['id'], jurisdiction_id=f'J{i}', policy_era='era_1',
            window_start='2024-01-01', window_end='2024-12-31', population_id=f'population_{i}',
            outcome_condition='approved', route_scope='initial', clock_start='application',
            clock_end='first_decision', time_unit='calendar_days')
        members = [dict(observation_id=o['id'], observation_sha256=comparison_digest(o),
            source_type=typ, document_id=o['source_family'], lineage_id=o['source_family'],
            estimand=copy.deepcopy(estimand), ascertainment='same_defined_receipt_cohort')
            for o, typ in zip(p['observations'], pair)]
        blocks.append(dict(id=f'b{i}', program_id=p['id'], program_sha256=comparison_digest(p),
            reviewer='fixture_only', review_artifact_sha256='1'*64, members=members))
        data['programs'].append(p)
    data['source_comparisons'] = dict(schema_version=VERSION, reference_type='administrative', blocks=blocks)
    return data


def refresh(data):
    for p, b in zip(data['programs'], data['source_comparisons']['blocks']):
        b['program_sha256'] = comparison_digest(p)
        for o, m in zip(p['observations'], b['members']):
            m['observation_sha256'] = comparison_digest(o)


def test_absent_review_never_infers_overlap_from_clock_labels():
    r = source_comparison_report(data_fixture())
    assert r['status'] == 'not_declared'
    assert r['ordinary_observation_rows'] == r['unreviewed_observation_rows'] == 4
    assert r['contrast_candidate_blocks'] == 0
    assert not r['bias_identification_established']


def test_clean_crossed_design_is_only_a_rank_screen_and_preserves_likelihood():
    data = reviewed_fixture((('administrative', 'forum'),)*2)
    original = copy.deepcopy(data)
    r = source_comparison_report(data)
    assert r['contrast_candidate_blocks'] == 2
    assert r['design']['rank'] == r['design']['columns'] == 3
    assert r['design']['full_additive_contrast_rank']
    assert r['design']['connected_to_reference'] == ['forum']
    assert not r['bias_identification_established']
    cfg = Config(population_size=16, modeled_channels=('elapsed',))
    model = VisitHierarchy(data, cfg)
    no_review = copy.deepcopy(data)
    no_review.pop('source_comparisons')
    old = VisitHierarchy(no_review, cfg)
    assert model.layout.size == old.layout.size
    z = np.random.default_rng(42).normal(size=model.layout.size)
    assert model.log_likelihood(z, [0, 0]) == old.log_likelihood(z, [0, 0])
    assert model.source_support_report()['declared_source_comparisons'] == r
    assert data == original


def test_unknown_scope_does_not_become_identified_by_matching_unknown_strings():
    data = reviewed_fixture()
    for m in data['source_comparisons']['blocks'][0]['members']:
        m['estimand']['population_id'] = 'unknown'
    r = source_comparison_report(data)
    assert r['contrast_candidate_blocks'] == 0
    assert 'unresolved_review_scope_or_source_type' in r['blocks'][0]['holds']


def test_repeated_same_document_across_distinct_cohorts_does_not_invent_document_replication():
    data = reviewed_fixture((('administrative', 'forum'),)*2)
    for b in data['source_comparisons']['blocks']:
        for m in b['members']:
            m['document_id'] = m['source_type'] + '_single_report'
    r = source_comparison_report(data)
    assert r['design']['full_additive_contrast_rank']
    assert r['design']['types_with_less_than_two_documents'] == ['administrative', 'forum']
    assert r['design']['documents_spanning_blocks'] == {
        'administrative_single_report': ['b0', 'b1'], 'forum_single_report': ['b0', 'b1']}
    assert not r['design']['document_dependence_adjusted']
    assert not r['bias_identification_established']


@pytest.mark.parametrize('field,value', [
    ('jurisdiction_id', 'other_county'), ('policy_era', 'other_era'),
    ('window_start', '2024-02-01'), ('window_end', '2024-11-30'),
    ('population_id', 'different_population'), ('outcome_condition', 'all_decisions'),
    ('route_scope', 'renewal'), ('clock_start', 'complete_application'),
    ('clock_end', 'pickup')])
def test_matching_clock_words_do_not_overrule_other_estimand_differences(field, value):
    data = reviewed_fixture()
    data['source_comparisons']['blocks'][0]['members'][1]['estimand'][field] = value
    r = source_comparison_report(data)
    assert r['contrast_candidate_blocks'] == 0
    assert 'different_reviewed_estimands_or_ascertainment' in r['blocks'][0]['holds']


def test_matching_endpoints_do_not_equate_selected_and_receipt_cohorts():
    data = reviewed_fixture()
    data['source_comparisons']['blocks'][0]['members'][1]['ascertainment'] = 'delay_selected_forum'
    assert source_comparison_report(data)['contrast_candidate_blocks'] == 0


@pytest.mark.parametrize('mutation', ['calendar', 'missing_scope', 'date', 'reversed_date',
                                    'review_hash', 'program_hash', 'observation_hash', 'repeated_row'])
def test_invalid_or_stale_bindings_fail_before_sampling(mutation):
    data = reviewed_fixture()
    b = data['source_comparisons']['blocks'][0]
    m = b['members'][0]
    if mutation == 'calendar': m['estimand']['time_unit'] = 'business_days'
    elif mutation == 'missing_scope': m['estimand'].pop('population_id')
    elif mutation == 'date': m['estimand']['window_start'] = '2024'
    elif mutation == 'reversed_date': m['estimand']['window_start'] = '2025-01-01'
    elif mutation == 'review_hash': b['review_artifact_sha256'] = 'not_a_hash'
    elif mutation == 'program_hash': data['programs'][0]['routes'][0]['id'] = 'changed'
    elif mutation == 'observation_hash': m['observation_sha256'] = '0'*64
    else: b['members'].append(copy.deepcopy(m))
    with pytest.raises(ValueError):
        VisitHierarchy(data, Config(population_size=16))


@pytest.mark.parametrize('mutation', ['individual', 'typical_range', 'different_statistic',
                                    'residual', 'different_operator', 'selected', 'finite_cohort'])
def test_narrow_design_refuses_richer_or_mismatched_observation_contracts(mutation):
    data = reviewed_fixture()
    o = data['programs'][0]['observations'][1]
    if mutation == 'individual': o.update(case_id='c', statistic='individual')
    elif mutation == 'typical_range': o['statistic'] = 'typical_range'
    elif mutation == 'different_statistic': o['statistic'] = 'mean'
    elif mutation == 'residual': o['operators'] = [dict(basis='unmodeled_duration')]
    elif mutation == 'different_operator': o['operators'][0]['end'] = 'final_decision'
    elif mutation == 'finite_cohort': o['sample_size'] = 100
    else: o['sampling'] = 'delay_selected'
    refresh(data)
    assert source_comparison_report(data)['contrast_candidate_blocks'] == 0


@pytest.mark.parametrize('value', ['20240101', '2024-W01-1', '2024-02-30'])
def test_window_dates_require_exact_valid_calendar_dates(value):
    data = reviewed_fixture()
    data['source_comparisons']['blocks'][0]['members'][0]['estimand']['window_start'] = value
    with pytest.raises(ValueError, match='ISO dates'):
        source_comparison_report(data)


@pytest.mark.parametrize('duplicate', ['program', 'observation'])
def test_standalone_screen_refuses_ambiguous_input_identities(duplicate):
    data = reviewed_fixture()
    if duplicate == 'program':
        data['programs'].append(copy.deepcopy(data['programs'][0]))
    else:
        p = data['programs'][0]
        p['observations'].append(copy.deepcopy(p['observations'][0]))
        data['source_comparisons']['blocks'][0]['program_sha256'] = comparison_digest(p)
    with pytest.raises(ValueError, match='Repeated .* identity'):
        source_comparison_report(data)


@pytest.mark.parametrize('across_blocks', [False, True])
def test_copies_do_not_increase_contrast_rank_or_replication(across_blocks):
    data = reviewed_fixture((('administrative', 'forum'),)* (2 if across_blocks else 1))
    blocks = data['source_comparisons']['blocks']
    first = blocks[0]['members'][0]['lineage_id']
    blocks[-1]['members'][1]['lineage_id'] = first
    r = source_comparison_report(data)
    assert r['contrast_candidate_blocks'] == 0
    assert not r['design']['full_additive_contrast_rank']


def test_single_type_documents_are_not_a_cross_type_comparison():
    r = source_comparison_report(reviewed_fixture((('forum', 'forum'),)))
    assert r['contrast_candidate_blocks'] == 0
    assert 'only_one_source_type' in r['blocks'][0]['holds']


def test_disconnected_types_cannot_be_contrasted_to_an_absent_reference():
    r = source_comparison_report(reviewed_fixture((('oversight', 'forum'),)))
    assert r['contrast_candidate_blocks'] == 1
    assert r['design']['disconnected_types'] == ['forum', 'oversight']
    assert r['design']['nullity'] == 1
    assert not r['design']['full_additive_contrast_rank']


def test_transitive_overlap_is_visible_without_inventing_direct_overlap():
    r = source_comparison_report(reviewed_fixture((('administrative', 'oversight'), ('oversight', 'forum'))))
    assert r['design']['connected_to_reference'] == ['forum', 'oversight']
    assert r['design']['full_additive_contrast_rank']
    assert r['design']['source_type_blocks'] == dict(administrative=1, forum=1, oversight=2)


def test_source_types_cannot_change_between_reports_of_the_same_document():
    data = reviewed_fixture()
    members = data['source_comparisons']['blocks'][0]['members']
    members[1]['document_id'] = members[0]['document_id']
    with pytest.raises(ValueError, match='Conflicting source-type'):
        source_comparison_report(data)
