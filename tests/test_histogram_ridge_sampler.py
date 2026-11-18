"""Target-preservation checks, not real-data recovery claims."""
import copy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.special import ndtr

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy
from pipeline.procbench.histogram_ridge_sampler import HistogramRidgeHierarchy
from pipeline.procbench.run_visit_hierarchy import main, sampling_model, worker
from test_analytic_phase import config, phase_data


def fixture():
    data = phase_data(histogram=True)
    other = copy.deepcopy(data['programs'][0])
    other['id'] = 'second'
    other['histogram_cohorts'][0]['id'] += '_second'
    other['histogram_cohorts'][0]['cohort_id'] += '_second'
    data['programs'].append(other)
    cfg = config(hierarchy_sampler='operation_centered', common_case_sd=0.,
                 source_sd=0., chains=1, warmup=2, draws=8)
    return data, cfg


def test_same_layout_parameters_and_likelihood():
    data, cfg = fixture()
    old, new = VisitHierarchy(data, cfg), HistogramRidgeHierarchy(data, cfg)
    assert old.layout.size == new.layout.size
    for seed in range(8):
        z = np.random.default_rng(seed).normal(scale=.2, size=old.layout.size)
        np.testing.assert_array_equal(old.parameters(z)['mu'], new.parameters(z)['mu'])
        assert old.log_likelihood(z, [0, 0]) == new.log_likelihood(z, [0, 0])
        assert new.log_likelihood(z, [0, 0]) == pytest.approx(new.log_likelihood_reference(z, [0, 0]))


def test_inverse_null_preservation_and_anchored_cdf():
    model = HistogramRidgeHierarchy(*fixture())
    z = np.random.default_rng(418).normal(size=model.layout.size)
    moved, jac = model.ridge_proposal(z, .17)
    back, inverse_jac = model.ridge_proposal(moved, -.17)
    np.testing.assert_allclose(back, z, atol=1e-13)
    assert jac+inverse_jac == 0
    null = model.duration_null_basis
    np.testing.assert_allclose(null.T@moved[model.ridge_coordinates],
                               null.T@z[model.ridge_coordinates], atol=1e-13)
    def cdf(state):
        mu = model.ridge_baseline+model.design@state[model.ridge_coordinates]
        return ndtr((model.ridge_anchors-mu)/model.parameters(state)['sigma'][0])
    np.testing.assert_allclose(cdf(moved), cdf(z), atol=1e-14)


def test_full_state_finite_difference_jacobian():
    model = HistogramRidgeHierarchy(*fixture())
    z = np.random.default_rng(19).normal(scale=.1, size=model.layout.size)
    eps, delta = 1e-5, .23
    jacobian = np.column_stack([
        (model.ridge_proposal(z+eps*axis, delta)[0]
         -model.ridge_proposal(z-eps*axis, delta)[0])/(2*eps)
        for axis in np.eye(len(z))])
    sign, logdet = np.linalg.slogdet(jacobian)
    assert sign == 1
    assert logdet == pytest.approx(model.ridge_proposal(z, delta)[1], abs=1e-9)


@pytest.mark.parametrize('field,value', [
    ('common_case_sd', .2), ('source_sd', .2), ('selection_sd', .2),
    ('case_log_sd_prior', 0.), ('hierarchy_sampler', 'blocked'),
    ('population_integration', 'qmc')])
def test_guard_rejects_unsupported_frames(field, value):
    data, cfg = fixture()
    with pytest.raises(ValueError, match='Histogram ridge moves require'):
        HistogramRidgeHierarchy(data, replace(cfg, **{field:value}))


@pytest.mark.parametrize('step', [0., -.1, float('inf'), float('nan'), True])
def test_invalid_step(step):
    with pytest.raises(ValueError, match='finite and positive'):
        HistogramRidgeHierarchy(*fixture(), ridge_step=step)


def test_sample_saves_unchanged_target_values():
    model = HistogramRidgeHierarchy(*fixture())
    states, routes, ll, calls = model.sample()
    assert model.ridge_attempts == model.cfg.warmup+model.cfg.draws
    for z, route, value in zip(states[0], routes[0], ll[0]):
        assert model.log_likelihood(z, route) == pytest.approx(value, abs=1e-10)
    assert calls[0] > model.ridge_attempts


def test_disabled_factory_preserves_bitwise_rng_replay():
    data, cfg = fixture()
    original = VisitHierarchy(data, cfg).sample()
    ordinary = sampling_model(data, cfg).sample()
    for first, second in zip(original, ordinary):
        np.testing.assert_array_equal(first, second)


def test_one_step_preserves_known_correlated_gaussian_posterior():
    model = HistogramRidgeHierarchy(*fixture(), ridge_step=.35)
    # A linear-Gaussian likelihood has an exact posterior over the original
    # whitened coordinates, including their correlations with spread.
    n = model.layout.size
    vector = np.linspace(-.5, .8, n)
    noise, target = .7, .9
    covariance = np.linalg.inv(np.eye(n)+np.outer(vector, vector)/noise**2)
    mean = covariance@vector*target/noise**2
    def likelihood(z, structures):
        return -.5*((vector@z-target)/noise)**2
    model.log_likelihood = likelihood
    rng = np.random.default_rng(719)
    before = rng.multivariate_normal(mean, covariance, size=6000)
    after = np.array([model.ridge_update(z, [0, 0], likelihood(z, None), rng)[0]
                      for z in before])
    for change in (after-before, after*after-before*before):
        se = change.std(axis=0, ddof=1)/np.sqrt(len(change))
        assert np.all(abs(change.mean(axis=0)) < 6*se+.003)
    assert 0 < model.ridge_accepts < model.ridge_attempts


def test_worker_persists_transition_counters(tmp_path):
    data, cfg = fixture()
    path, calls = worker(data, cfg, 0, tmp_path, histogram_ridge=True)
    report = json.loads((tmp_path/'chain_0.transition.json').read_text())
    assert Path(path).exists()
    assert report['attempts'] == cfg.warmup+cfg.draws
    assert 0 <= report['accepts'] <= report['attempts']
    assert report['statistical_target_changed'] is False


def test_preflight_snapshot_contains_exact_sampler_module(tmp_path, capsys):
    data, _ = fixture()
    source = tmp_path/'data.json'
    source.write_text(json.dumps(data))
    out = tmp_path/'preflight'
    main(['--data', str(source), '--out', str(out), '--preflight',
          '--histogram-ridge-moves', '--population-integration', 'analytic_single_phase',
          '--hierarchy-sampler', 'operation_centered', '--observed-channels-only',
          '--source-sd', '0', '--common-case-sd', '0'])
    report = json.loads((out/'preflight.json').read_text())
    assert report['sampling_performed'] is False
    assert report['transition_kernel']['statistical_target_changed'] is False
    original = Path(__file__).parents[1]/'pipeline/procbench/histogram_ridge_sampler.py'
    assert (out/'source/histogram_ridge_sampler.py').read_bytes() == original.read_bytes()


@pytest.mark.parametrize('extra', [
    ['--histogram-ridge-step', '.1'],
    ['--histogram-ridge-moves', '--marginalize-conditional-cases']])
def test_cli_rejects_implicit_or_incompatible_transition_flags(tmp_path, extra):
    with pytest.raises(SystemExit):
        main(['--data', str(tmp_path/'nonexistent.json'), '--out', str(tmp_path/'out')]+extra)
