"""Same-target checks for independent-case integration, not fit validation."""
import copy
import hashlib
import json
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import ndtri

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy
from pipeline.procbench.marginal_conditional_frames import MarginalConditionalFrame
from pipeline.procbench.marginal_conditional_frames import run_marginal_frame
from pipeline.procbench.run_visit_hierarchy import main
from pipeline.procbench.summarize_conditional_frames import summarize
from test_conditional_case_frames import (frame_config, frame_data, censored_frame_data,
                                          terminal_neutral_frame_data)


@pytest.mark.parametrize('contamination', [0., .05, .8])
@pytest.mark.parametrize('scale', [.25, .5, 2.])
@pytest.mark.parametrize('state', [[0., 0.], [2., -2.], [-2., 2.]])
def test_marginal_matches_independent_original_case_kernel(contamination, scale, state):
    model = MarginalConditionalFrame(censored_frame_data(),
        frame_config(report_sd=scale, contamination=contamination), 256)
    assert model.log_likelihood(state, [0]) == pytest.approx(
        model.reference_log_likelihood(state), abs=2e-8)


def test_terminal_neutral_status_does_not_change_lower_null_marginal_likelihood():
    neutral = MarginalConditionalFrame(terminal_neutral_frame_data(), frame_config(), 256)
    pending = MarginalConditionalFrame(censored_frame_data(), frame_config(), 256)
    completed_data = terminal_neutral_frame_data()
    completed_data['programs'][0]['observations'][1]['observation_kind'] = 'completed_lower_bound'
    completed = MarginalConditionalFrame(completed_data, frame_config(), 256)
    for state in ([0.,0.],[1.,-.5],[-1.,.5]):
        assert neutral.log_likelihood(state) == pending.log_likelihood(state)
        assert neutral.log_likelihood(state) == completed.log_likelihood(state)


@pytest.mark.parametrize('lower,upper', [(0., .01), (.999, 1.001),
                                      (math.exp(8), None), (math.exp(-8), math.exp(-7.9))])
def test_narrow_and_tail_reports_preserve_student_t_not_gaussian(lower, upper):
    data = censored_frame_data()
    data['programs'][0]['observations'][0].update(lower=lower, upper=upper,
        observation_kind='completed_interval' if upper is not None else 'completed_lower_bound')
    model = MarginalConditionalFrame(data,
        frame_config(elapsed_prior_median=1., case_log_sd_median=.03,
                     contamination=0.), 256)
    assert model.log_likelihood([0., 0.]) == pytest.approx(
        model.reference_log_likelihood([0., 0.]), abs=2e-7)


def test_factor_integrals_equal_integrated_full_v6_likelihood():
    data, cfg = censored_frame_data(), frame_config()
    full = VisitHierarchy(data, cfg)
    model = MarginalConditionalFrame(data, cfg, 256)
    z = np.random.default_rng(5).normal(size=full.layout.size)
    z[full.location[0]], z[full.sigma[0]] = .4, -.2
    expected = {}
    for i, obs in enumerate(full.programs[0]['observations']):
        key = full.programs[0]['id']+':'+obs['id']
        index = full.programs[0]['case_coordinates'][i, 0]

        def integrand(case_z):
            trial = z.copy(); trial[index] = case_z
            return math.exp(full.log_likelihood(trial, [0], parts=True)[key]
                            - case_z*case_z/2)/math.sqrt(2*math.pi)

        value, _ = quad(integrand, -12, 12, epsabs=1e-12, limit=100)
        expected[key] = math.log(value)
    assert model.log_likelihood([.4, -.2], [0], parts=True) == pytest.approx(expected, abs=2e-8)


def test_fixed_spread_is_integrated_not_a_fake_extra_coordinate():
    model = MarginalConditionalFrame(frame_data(), frame_config(case_log_sd_prior=0.))
    assert model.layout.size == 1
    assert model.parameters([.3])[1] == pytest.approx(.6)
    assert model.log_likelihood([.3]) == pytest.approx(model.reference_log_likelihood([.3]), abs=1e-6)
    states = np.random.default_rng(17).normal(size=(2, 8, 1))
    ll = np.array([[model.log_likelihood(z) for z in chain] for chain in states])
    report = model.report(states, ll)
    assert 'elapsed:case_log_sd' not in report['diagnostics']
    assert report['fixed_quantities']['elapsed:case_log_sd']['value'] == .6


@pytest.mark.parametrize('change', ['no_frame', 'two_reports', 'common_effect', 'source_effect'])
def test_rejects_inputs_where_independent_case_reduction_would_be_wrong(change):
    data, cfg = frame_data(), frame_config()
    if change == 'no_frame':
        data.pop('conditional_case_frames')
        data['programs'][0].pop('conditional_frame_id')
        for row in data['programs'][0]['observations']:
            row['sampling'] = 'unselected'
    elif change == 'two_reports':
        extra = copy.deepcopy(data['programs'][0]['observations'][0])
        extra['id'] = 'another-report-of-same-case'
        data['programs'][0]['observations'].append(extra)
    elif change == 'common_effect':
        cfg = frame_config(common_case_sd=.2)
    else:
        cfg = frame_config(source_sd=.2)
    with pytest.raises(ValueError):
        MarginalConditionalFrame(data, cfg)


@pytest.mark.parametrize('nodes', [True, 1, 0, 128.5])
def test_invalid_quadrature_is_not_silently_rounded(nodes):
    with pytest.raises(ValueError):
        MarginalConditionalFrame(frame_data(), frame_config(), nodes)


def test_invalid_state_and_route_are_not_silently_accepted():
    model = MarginalConditionalFrame(frame_data(), frame_config())
    with pytest.raises(ValueError):
        model.log_likelihood([0.])
    with pytest.raises(ValueError):
        model.log_likelihood([0., 0.], [1])


@pytest.mark.parametrize('sign', [-1., 1.])
def test_overflowed_location_fails_closed_for_censored_data(sign):
    model = MarginalConditionalFrame(censored_frame_data(), frame_config())
    state = [sign*np.finfo(float).max, 0.]
    assert model.log_likelihood(state) == -math.inf
    with pytest.raises(FloatingPointError):
        model.log_likelihood(state, parts=True)


def test_sampler_is_reproducible_and_saved_likelihoods_replay():
    model = MarginalConditionalFrame(censored_frame_data(),
        frame_config(chains=1, warmup=3, draws=8))
    first = model.sample_chain(0)
    second = model.sample_chain(0)
    np.testing.assert_array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])
    np.testing.assert_allclose(first[1], [model.log_likelihood(z) for z in first[0]], atol=1e-12)
    assert first[2] == second[2]


def test_flat_likelihood_recovers_whitened_prior_without_spurious_case_density():
    model = MarginalConditionalFrame(frame_data(),
        frame_config(chains=1, warmup=0, draws=2000))
    model.log_likelihood = lambda z: 0.
    states, ll, _ = model.sample_chain(0)
    np.testing.assert_allclose(states.mean(axis=0), 0., atol=.1)
    np.testing.assert_allclose(states.var(axis=0), 1., atol=.15)
    np.testing.assert_array_equal(ll, 0.)


def test_report_quantiles_are_exact_functionals_and_smoke_fit_is_not_certified():
    model = MarginalConditionalFrame(frame_data(), frame_config(chains=2, draws=8))
    states = np.random.default_rng(2).normal(size=(2, 8, 2))
    ll = np.array([[model.log_likelihood(z) for z in chain] for chain in states])
    report = model.report(states, ll)
    mu = math.log(7)+2*states[:, :, 0]
    sigma = .6*np.exp(.4*states[:, :, 1])
    metrics = report['programs']['reported-program']['metrics']
    assert metrics['modeled_work_end_median_days']['median'] == pytest.approx(np.median(np.exp(mu)))
    assert metrics['modeled_work_end_p90_days']['median'] == pytest.approx(np.median(np.exp(mu+ndtri(.9)*sigma)))
    assert report['posterior_converged'] is False
    assert report['identification']['coordinates'] == 2


def test_existing_runner_exposes_guarded_preflight_and_preserves_config(tmp_path):
    data = tmp_path/'input.json'; data.write_text(json.dumps(frame_data()))
    out = tmp_path/'fit'
    main(['--data', str(data), '--out', str(out), '--preflight',
          '--marginalize-conditional-cases', '--observed-channels-only',
          '--agency-sd', '0', '--task-sd', '0', '--operation-sd', '0',
          '--common-case-sd', '0', '--source-sd', '0'])
    preflight = json.loads((out/'preflight.json').read_text())
    assert preflight['dimensions'] == 2
    assert preflight['sampling_performed'] is False
    manifest = json.loads((out/'manifest.json').read_text())
    assert manifest['report_sha256'] == hashlib.sha256((out/'preflight.json').read_bytes()).hexdigest()
    assert (out/'source'/'marginal_conditional_frames.py').exists()
    assert not (out/'draws.npz').exists()
    with pytest.raises(ValueError):
        main(['--data', str(data), '--out', str(out), '--preflight'])


def test_runner_does_not_ignore_quadrature_option_without_opt_in(tmp_path):
    with pytest.raises(SystemExit):
        main(['--data', 'not-read.json', '--out', str(tmp_path/'fit'),
              '--case-quadrature-size', '256'])


def test_marginal_fit_summary_replay_and_tamper_guards(tmp_path, monkeypatch):
    from test_prepare_conditional_frames import fixture, invoke
    from pipeline.procbench.bayes_trace_hierarchy import Config
    spec = fixture(tmp_path, monkeypatch)
    spec['conditions'] = spec['conditions'][:1]
    invoke(spec, tmp_path)
    packet = tmp_path/'prepared'
    plan = json.loads((packet/'plan.json').read_text())
    data = json.loads((packet/'mixed_data.json').read_text())
    cfg = Config(**plan['conditions'][0]['config'])
    plan['conditions'][0]['inference'] = MarginalConditionalFrame(data, cfg).inference
    (packet/'plan.json').write_text(json.dumps(plan))
    prepared_manifest = json.loads((packet/'manifest.json').read_text())
    for row in prepared_manifest['outputs']:
        row['sha256'] = hashlib.sha256((tmp_path/row['path']).read_bytes()).hexdigest()
    (packet/'manifest.json').write_text(json.dumps(prepared_manifest))
    fit = packet/'fit_mixed'
    run_marginal_frame(data, cfg, fit, [packet/'mixed_data.json'], workers=1)
    result = summarize(packet, packet/'analysis', tmp_path)
    assert result['unique_forum_cases_consumed'] == 2
    assert result['conditions'][0]['likelihood_replay_max_difference'] == 0.
    assert not result['conditions'][0]['numerically_usable']  # eight draws are not validation
    for name in ['draws.npz', 'posterior.json', 'source/marginal_conditional_frames.py']:
        path = fit/name; original = path.read_bytes()
        path.write_bytes(original+b'\n')
        with pytest.raises(ValueError, match='hash mismatch|dependency differs'):
            summarize(packet, packet/'rejected', tmp_path)
        assert not (packet/'rejected').exists()
        path.write_bytes(original)
    manifest_path = fit/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['status'] = 'running'
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='lifecycle'):
        summarize(packet, packet/'rejected', tmp_path)
