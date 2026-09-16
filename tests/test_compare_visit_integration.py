import copy
import pathlib

import pytest
import numpy as np

from pipeline.procbench.compare_visit_integration import agency_diagnostics, assert_nested_evidence, interval_score, verified_fit, verified_truth
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench import generate_visit_integration
from pipeline.procbench.generate_visit_integration import generate
from pipeline.procbench.reconcile_evidence import digest, write


def test_interval_score_penalizes_misses_without_rewarding_unbounded_intervals():
    estimate = dict(median=2., ci90=[1., 3.])
    assert interval_score(estimate, 2., False)['interval_score_90'] == 2.
    assert interval_score(estimate, 4., False)['interval_score_90'] == 22.
    assert interval_score(estimate, 4., True)['covered_90'] is False
    with pytest.raises(ValueError, match='Invalid'):
        interval_score(dict(median=1., ci90=[0., 2.]), 1., True)


def test_conditions_must_add_evidence_without_changing_base_reports_or_routes():
    data, _ = generate()
    assert_nested_evidence(data['timing_only'], data['mixed_evidence'])
    changed = copy.deepcopy(data['mixed_evidence'])
    changed['programs'][0]['observations'][0]['lower'] += 1.
    with pytest.raises(ValueError, match='changed or removed'):
        assert_nested_evidence(data['timing_only'], changed)
    changed = copy.deepcopy(data['mixed_evidence'])
    changed['programs'][0]['routes'][0]['prior_weight'] = .9
    with pytest.raises(ValueError, match='Route hypotheses'):
        assert_nested_evidence(data['timing_only'], changed)


@pytest.mark.parametrize('usable,precision', [(False, True), (True, False)])
def test_failed_numerics_are_not_accuracy_results(tmp_path, usable, precision):
    report = dict(numerically_usable=usable, posterior_converged=True, diagnostics_flagged={},
                  precision=dict(likelihood_acceptable=True, predictions_acceptable=precision))
    write(tmp_path / 'posterior.json', report)
    write(tmp_path / 'manifest.json', dict(completed_utc='test',
        posterior_sha256=digest((tmp_path / 'posterior.json').read_bytes())))
    with pytest.raises(ValueError, match='Numerical gates failed'):
        verified_fit(tmp_path, {})


def test_changed_completed_report_is_rejected(tmp_path):
    write(tmp_path / 'posterior.json', dict(numerically_usable=True))
    write(tmp_path / 'manifest.json', dict(completed_utc='test', posterior_sha256='wrong'))
    with pytest.raises(ValueError, match='completed, unchanged'):
        verified_fit(tmp_path, {})


def test_truth_must_match_hashed_frozen_generator_and_all_observed_data(tmp_path):
    raw = pathlib.Path(generate_visit_integration.__file__).read_bytes()
    (tmp_path / 'generator_source.py').write_bytes(raw)
    manifest = dict(seed=2026092007, source_sha256=digest(raw))
    data, truth = generate()
    write(tmp_path / 'truth.json', truth)
    assert verified_truth(tmp_path, data, manifest) == truth
    bad = copy.deepcopy(truth)
    bad['J__P']['mean_agency_hours'] += 1.
    write(tmp_path / 'truth.json', bad)
    with pytest.raises(ValueError, match='truth disagrees'):
        verified_truth(tmp_path, data, manifest)
    changed = copy.deepcopy(data)
    changed['timing_only']['programs'][0]['observations'][0]['lower'] += 1.
    with pytest.raises(ValueError, match='reproduces the frozen observations'):
        verified_truth(tmp_path, changed, manifest)


def test_agency_diagnostics_check_presence_and_conditional_draws():
    data, _ = generate()
    model = VisitHierarchy(data['timing_only'], Config(chains=2, population_size=16))
    z = np.random.default_rng(7).normal(scale=.1, size=(2, 20, model.layout.size))
    routes = np.ones((2, 20, 2), dtype=int)
    routes[0, :2, :] = 0
    result = agency_diagnostics(model, z, routes)
    assert result['J:Review:inventory_mean_conditional']['conditional_draws_per_chain_checked'] == 20
    assert result['J:Records:inventory_mean_conditional']['conditional_draws_per_chain_checked'] == 18
    assert set(result) == {'J:Review:inventory_mean_conditional', 'J:Review:presence',
                           'J:Records:inventory_mean_conditional', 'J:Records:presence'}
