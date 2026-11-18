"""Documented task baselines change elapsed priors, never resource units."""
from dataclasses import asdict, replace
import hashlib
import json

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import main, preflight_report
from procbench_fixtures import data_fixture


def test_empty_task_baselines_preserve_historical_parameter_formula_and_layout():
    model = VisitHierarchy(data_fixture(), Config(population_size=16))
    assert model.cfg.elapsed_task_prior_medians == ()
    rng = np.random.default_rng(20)
    for _ in range(8):
        z = rng.normal(size=model.layout.size)
        par = model.parameters(z)
        c = model.cfg
        location = np.log([c.elapsed_prior_median, c.work_prior_median, c.work_prior_median]) + c.location_sd*z[model.location]
        expected = (location[:, None] + c.agency_sd*z[model.agency][:, model.agency_indices]
                    + c.task_sd*z[model.task][:, model.task_indices] + c.operation_sd*z[model.operation])
        np.testing.assert_array_equal(par['mu'], expected)
    assert not preflight_report(model)['duration_priors']['task_baselines_enabled']


def test_task_specific_baseline_moves_only_elapsed_location_and_keeps_fallback():
    cfg = Config(population_size=16, elapsed_task_prior_medians=[['filing', .125], ['review', 3.]])
    model = VisitHierarchy(data_fixture(), cfg)
    old = VisitHierarchy(data_fixture(), replace(cfg, elapsed_task_prior_medians=()))
    assert model.layout.size == old.layout.size
    z = np.zeros(model.layout.size)
    np.testing.assert_allclose(np.exp(model.parameters(z)['mu'][0]), [.125, 3., 7.])
    for seed in range(4):
        z = np.random.default_rng(seed).normal(size=model.layout.size)
        a, b = old.parameters(z), model.parameters(z)
        np.testing.assert_array_equal(a['mu'][1:], b['mu'][1:])
        np.testing.assert_allclose(b['mu'][0]-a['mu'][0], np.log([.125/7., 3./7., 1.]))
        assert model.log_likelihood_reference(z, [0]) == pytest.approx(model.log_likelihood(z, [0]), abs=1e-10)
    report = model.duration_prior_report()
    assert report['tasks']['decision']['origin'] == 'global_fallback'
    assert report['tasks']['filing']['origin'] == 'supplied_fixed_task_baseline'
    assert report['added_sampled_coordinates'] == 0
    assert not report['inferred_from_this_fit']


def test_task_prior_json_roundtrip_is_immutable_canonical_and_detached():
    raw = [['review', 3], ['filing', .125]]
    cfg = Config(elapsed_task_prior_medians=raw)
    raw[0][1] = 999
    assert cfg.elapsed_task_prior_medians == (('filing', .125), ('review', 3.))
    assert Config(**json.loads(json.dumps(asdict(cfg)))) == cfg


@pytest.mark.parametrize('value', [None, {'filing': 1.}, [('filing', 0)],
    [('filing', -1)], [('filing', True)], [('filing', float('nan'))],
    [('filing', float('inf'))], [('filing', '1')], [(' filing', 1)],
    [('', 1)], [('filing', 1), ('filing', 2)], [('filing', 1, 2)]])
def test_invalid_task_prior_declarations_fail(value):
    with pytest.raises(ValueError, match='Elapsed task priors'):
        Config(elapsed_task_prior_medians=value)


def test_task_typo_is_not_silently_ignored():
    with pytest.raises(ValueError, match='tasks absent.*filng'):
        VisitHierarchy(data_fixture(), Config(elapsed_task_prior_medians=(('filng', 1.),)))


@pytest.mark.parametrize('sampler', ['blocked', 'operation_centered'])
def test_sampler_moves_replay_exact_target_with_nonzero_task_offsets(sampler):
    cfg = Config(population_size=16, elapsed_task_prior_medians=(('filing', .125),),
                 hierarchy_sampler=sampler, chains=1, warmup=1, draws=8)
    model = VisitHierarchy(data_fixture(), cfg)
    states, routes, likelihood, _ = model.sample()
    for z, route, ll in zip(states[0], routes[0], likelihood[0]):
        assert model.log_likelihood_reference(z, route) == pytest.approx(ll, abs=1e-9)
    report = model.report(states, routes, likelihood)
    assert report['duration_priors']['tasks']['filing']['median_days'] == .125


def specification():
    return dict(schema_version='elapsed-task-priors/1',
        clock='single_visit_cycle_calendar_days_including_wait_and_service',
        medians_days={'filing': .125}, rationale='Artificial test prior; not empirical calibration.')


def test_cli_preflight_binds_and_copies_prior_provenance(tmp_path):
    data = tmp_path/'data.json'; data.write_text(json.dumps(data_fixture()))
    priors = tmp_path/'priors.json'; priors.write_text(json.dumps(specification()))
    out = tmp_path/'result'
    main(['--data', str(data), '--out', str(out), '--preflight', '--population-size', '16',
          '--elapsed-task-priors', str(priors)])
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['provenance']['input_sha256'][str(priors)] == hashlib.sha256(priors.read_bytes()).hexdigest()
    assert json.loads((out/'elapsed_task_priors.json').read_text()) == specification()
    assert json.loads((out/'preflight.json').read_text())['duration_priors']['tasks']['filing']['median_days'] == .125


@pytest.mark.parametrize('field,value', [('clock', 'payer_hours'), ('rationale', ''),
    ('medians_days', {}), ('schema_version', 'invented')])
def test_cli_rejects_undocumented_or_wrong_unit_priors_before_creating_run(tmp_path, field, value):
    data = tmp_path/'data.json'; data.write_text(json.dumps(data_fixture()))
    spec = specification(); spec[field] = value
    priors = tmp_path/'priors.json'; priors.write_text(json.dumps(spec))
    out = tmp_path/'result'
    with pytest.raises(ValueError, match='Elapsed task prior file'):
        main(['--data', str(data), '--out', str(out), '--preflight', '--elapsed-task-priors', str(priors)])
    assert not out.exists()


def test_diagnose_mode_cannot_change_saved_priors(tmp_path):
    with pytest.raises(SystemExit):
        main(['--diagnose-run', 'unused', '--out', str(tmp_path/'out'), '--elapsed-task-priors', 'unused'])
