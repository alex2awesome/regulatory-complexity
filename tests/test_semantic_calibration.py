import copy

import numpy as np
import pytest

from pipeline.procbench.semantic_calibration import (
    LABEL_SCHEMA, calibrated_weights, fit_calibration, operator_weights)
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from test_compile_visit_durations import inputs
from test_trace_hierarchy import data_fixture


def labels():
    rows = []
    for split, truth in [('fit', ['cycle']*8+['sum']*2), ('validation', ['cycle', 'sum', 'sum'])]:
        for i, actual in enumerate(truth):
            rows.append(dict(id=f'{split}:{i}', world_id='W1', group_id=f'{split}:source:{i}',
                split=split, ambiguity_class='duration_basis', top_label='cycle', true_label=actual,
                link_status='verified', truth_provenance='Verified fixture generator reading'))
    return dict(schema_version=LABEL_SCHEMA, world_id='W1', purpose='development_calibration',
        extractor=dict(model='pinned', prompt_sha256='fixture-prompt'),
        label_spaces={'duration_basis': ['cycle', 'sum', 'unmodeled']}, rows=rows)


def retained_policy():
    return dict(default_case_sampling='unselected', retain_unsupported=True,
                residual_reference=dict(median_days=7., log_scale=3.), rounding_fallback='reported_unit')


def test_measures_true_given_reported_using_fit_labels_not_validation():
    data = labels()
    report = fit_calibration(data)
    cls = report['classes']['duration_basis']
    assert cls['decision'] == 'mixture_candidate'
    assert cls['top_accuracy'] == pytest.approx(1/3)
    weights = calibrated_weights(report, 'duration_basis', 'cycle', world_id='W1', extractor=data['extractor'])
    assert weights == pytest.approx(dict(cycle=8.5/11.5, sum=2.5/11.5, unmodeled=.5/11.5))
    assert cls['confusion_by_reported_label']['all']['cycle']['ci90']['sum'][0] > 0
    reading = dict(ambiguity_class='duration_basis', top_label='cycle', label_to_candidate={'cycle': 'audit:0'})
    mapped = operator_weights(report, reading, world_id='W1', extractor=data['extractor'])
    assert mapped == pytest.approx({'audit:0': 8.5/11.5, '__residual__': 3/11.5})


@pytest.mark.parametrize('change', ['reserved', 'overlap', 'duplicate', 'unverified', 'world'])
def test_calibration_rejects_leakage_and_fabricated_labels(change):
    data = labels()
    if change == 'reserved':
        data['rows'][-1]['split'] = 'reserved'
    elif change == 'overlap':
        data['rows'][-1]['group_id'] = data['rows'][0]['group_id']
    elif change == 'duplicate':
        data['rows'].append(data['rows'][0])
    elif change == 'unverified':
        data['rows'][-1]['link_status'] = 'candidate'
    else:
        data['rows'][-1]['world_id'] = 'W2'
    with pytest.raises(ValueError):
        fit_calibration(data)


def test_remeasure_on_new_world_or_extractor_and_no_prior_only_calibration():
    data = labels()
    report = fit_calibration(data)
    for world, extractor, label in [('W2', data['extractor'], 'cycle'),
            ('W1', dict(data['extractor'], prompt_sha256='changed'), 'cycle'),
            ('W1', data['extractor'], 'sum')]:
        with pytest.raises(ValueError):
            calibrated_weights(report, 'duration_basis', label, world_id=world, extractor=extractor)


def test_vote_strata_are_one_predictor_not_additional_independent_labels():
    data = labels()
    for row in data['rows']:
        row['stratum'] = '3_of_5_votes'
    report = fit_calibration(data)
    cell = report['classes']['duration_basis']['confusion_by_reported_label']['3_of_5_votes']['cycle']
    assert cell['n'] == 10  # not 50 LLM votes


def test_upstream_threshold_and_insufficient_validation_are_explicit():
    data = labels()
    for row in data['rows']:
        row['true_label'] = row['top_label']
    assert fit_calibration(data)['classes']['duration_basis']['decision'] == 'top_reading'
    data['rows'] = [r for r in data['rows'] if r['split'] == 'fit']
    cls = fit_calibration(data)['classes']['duration_basis']
    assert cls['decision'] == 'insufficient_validation'
    assert cls['top_accuracy'] is None


def test_compiler_consumes_measured_priors_without_renormalizing_missing_labels():
    e, v, s, docs, _ = inputs()
    data = labels()
    report = fit_calibration(data)
    policy = retained_policy()
    policy.update(calibration_context=dict(world_id='W1', extractor=data['extractor']),
        calibrated_readings={'m1': dict(ambiguity_class='duration_basis', top_label='cycle',
                                      label_to_candidate={'cycle': 'audit:0'})})
    result = compile_durations(e, v, s, docs, policy, calibration=report)
    o = result['observations'][0]
    assert o['operator_weights'] == pytest.approx([8.5/11.5, 3/11.5])
    assert o['operators'][-1]['basis'] == 'unmodeled_duration'
    assert result['coverage']['informative_elapsed'] == 1
    assert 'measured_calibration' in o['provenance']['prior_origin']


def test_unsupported_claim_is_retained_as_noninformative_not_a_fake_median():
    e, v, s, docs, _ = inputs()
    e['measurements'][0].update(case_id=None, statistic='typical')
    s['measurements'][0].update(statistic_interpretation='typical_range', population_scope='all_cases')
    before = copy.deepcopy((e, v, s))
    compiled = compile_durations(e, v, s, docs, retained_policy())
    assert compiled['complete_elapsed_coverage']
    assert not compiled['complete_informative_coverage']
    assert compiled['coverage']['residual_only_elapsed'] == 1
    o = compiled['observations'][0]
    assert o['statistic'] == 'report_only'
    assert o['provenance']['original_statistic'] == 'typical_range'
    assert (e, v, s) == before
    data = data_fixture()
    data['programs'][0]['observations'] = [o]
    model = VisitHierarchy(data, Config(population_size=16))
    rng = np.random.default_rng(9)
    ll = [model.log_likelihood(z, [0]) for z in rng.normal(size=(10, model.layout.size))]
    np.testing.assert_allclose(ll, ll[0], rtol=0, atol=1e-14)


def test_policy_calendar_and_event_alias_are_explicit_and_preserve_sources():
    e, v, s, docs, _ = inputs()
    e['measurements'][0]['unit'] = 'business_days'
    s['measurements'][0]['original_precision_unit'] = 'business_days'
    v['measurements'][0]['operators'][0].update(basis='whole_case_clock', activity_ids=[],
        visits='not_applicable', start='process_start', end='latest_recorded_decision')
    policy = retained_policy()
    policy.update(calendar=dict(calendar_days_per_business_day=1.4, description='5/7 sensitivity'),
                  event_aliases={'latest_recorded_decision': 'final_decision'})
    compiled = compile_durations(e, v, s, docs, policy)
    o = compiled['observations'][0]
    assert o['lower'] == pytest.approx(11.5*1.4)
    assert o['operators'][0]['end'] == 'final_decision'
    assert o['provenance']['original_unit'] == 'business_days'
    assert v['measurements'][0]['operators'][0]['end'] == 'latest_recorded_decision'


def test_partial_unsupported_alternative_keeps_its_original_residual_mass():
    e, v, s, docs, _ = inputs()
    row = v['measurements'][0]
    row['identification'] = 'unresolved'
    unknown = copy.deepcopy(row['operators'][0])
    unknown.update(basis='unknown', visits='unknown')
    row['operators'].append(unknown)
    policy = retained_policy()
    policy['interpretation_priors'] = {'m1': [.8, .2]}
    o = compile_durations(e, v, s, docs, policy)['observations'][0]
    assert o['operator_weights'] == [.8, .2]
    assert o['operators'][1]['basis'] == 'unmodeled_duration'
