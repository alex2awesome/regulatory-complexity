"""Focused same-target tests for the optional production transition."""
import json
import math

import numpy as np
import pytest

from pipeline.procbench import case_scale_interweave as interweave
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import main as run_main
from procbench_fixtures import data_fixture, observation


def test_config_is_explicit_default_off_and_invalid_value_fails():
    assert Config().case_scale_sampler == 'blocked'
    assert Config(case_scale_sampler='interwoven').case_scale_sampler == 'interwoven'
    with pytest.raises(ValueError, match='Unknown case-scale sampler'):
        Config(case_scale_sampler='adaptive')


def test_transition_report_distinguishes_enabled_fixed_spread_noop():
    model = VisitHierarchy(data_fixture(), Config(population_size=16,
        case_log_sd_prior=0., case_scale_sampler='interwoven'))
    report = model.case_scale_transition_report()
    assert report['enabled']
    assert report['steps_per_sweep'] == 0
    assert report['no_op_reason'] == 'case_log_sd_prior_is_zero'


def test_multichannel_indexing_transforms_operation_residuals_not_common_coordinates():
    model = VisitHierarchy(data_fixture(), Config(population_size=16))
    state = np.random.default_rng(901).normal(size=model.layout.size)
    for channel in model.active_channels:
        layout = interweave.channel_case_coordinates(model, channel)
        before_common = state[layout.common_case_coordinates].copy()
        before_effect = (math.exp(model.cfg.case_log_sd_prior*state[layout.sigma_coordinate])
                         * state[layout.residual_coordinates])
        proposal = interweave.case_scale_proposal(model, state, channel,
                                                   state[layout.sigma_coordinate]+.37)
        after_effect = (math.exp(model.cfg.case_log_sd_prior
                                 * proposal['state'][layout.sigma_coordinate])
                        * proposal['state'][layout.residual_coordinates])
        np.testing.assert_allclose(after_effect, before_effect, rtol=3e-15, atol=3e-15)
        np.testing.assert_array_equal(proposal['state'][layout.common_case_coordinates],
                                      before_common)
    with pytest.raises(ValueError, match='active channel'):
        interweave.channel_case_coordinates(
            model, 99)


def test_augmented_jacobian_and_residual_prior_correction_are_independent_oracles():
    model = VisitHierarchy(data_fixture(), Config(population_size=16))
    state = np.random.default_rng(902).normal(scale=.2, size=model.layout.size)
    channel = int(model.active_channels[0])
    layout = interweave.channel_case_coordinates(model, channel)
    old_scale = float(state[layout.sigma_coordinate])
    new_scale = old_scale-.3
    proposal = interweave.case_scale_proposal(model, state, channel, new_scale)
    reverse = interweave.case_scale_proposal(
        model, proposal['state'], channel, old_scale)
    np.testing.assert_allclose(reverse['state'], state, rtol=0, atol=3e-16)

    # Finite-difference the augmented (s', z) -> (s', exp(a(s-s'))z)
    # map. K is counted from the model layout, not read from the proposal.
    residuals = state[layout.residual_coordinates]
    k = sum(len(p['cases'])*len(p['global_indices']) for p in model.programs)
    assert k == len(residuals)
    width = model.cfg.case_log_sd_prior
    point = np.r_[new_scale, residuals]
    epsilon = 1e-6

    def transform(value):
        scale = math.exp(width*(old_scale-value[0]))
        return np.r_[value[0], scale*value[1:]]

    jacobian = np.column_stack([(transform(point+epsilon*np.eye(k+1)[j])
        - transform(point-epsilon*np.eye(k+1)[j]))/(2*epsilon)
        for j in range(k+1)])
    sign, logabs = np.linalg.slogdet(jacobian)
    assert sign == 1
    assert logabs == pytest.approx(k*width*(old_scale-new_scale), abs=2e-9)

    structures = np.zeros(len(model.programs), dtype=int)
    current = model.log_likelihood(state, structures)
    expected = (model.log_likelihood(proposal['state'], structures)
        -.5*(proposal['state'][layout.residual_coordinates]
             @ proposal['state'][layout.residual_coordinates]
             - residuals@residuals)
        + k*width*(old_scale-new_scale))
    actual = interweave.anchored_log_target(
        model, state, structures, current, channel, new_scale)
    assert actual == pytest.approx(expected, abs=1e-12)
    # The scale-coordinate N(0,1) prior is supplied by ESS, not its callback.
    assert actual != pytest.approx(expected-.5*(new_scale**2-old_scale**2))


def test_default_blocked_sampling_is_bitwise_equal_to_explicit_blocked():
    values = dict(chains=1, warmup=1, draws=8, population_size=16, seed=1881)
    implicit = VisitHierarchy(data_fixture(), Config(**values))
    explicit = VisitHierarchy(data_fixture(), Config(**values,
        case_scale_sampler='blocked'))
    first = implicit.sample()
    second = explicit.sample()
    for a, b in zip(first[:3], second[:3]):
        np.testing.assert_array_equal(a, b)
    assert first[3] == second[3]


def test_integrated_interwoven_sample_stores_ordinary_full_likelihood():
    data = data_fixture()
    data['programs'][0]['observations'] = [row for row in data['programs'][0]['observations']
        if all(op['basis'] not in {'visit_count', 'payer_hours', 'agency_hours'}
               for op in row['operators'])]
    model = VisitHierarchy(data, Config(chains=1, warmup=1, draws=8,
        population_size=16, modeled_channels=('elapsed',), seed=1882,
        case_scale_sampler='interwoven'))
    states, routes, likelihood, _ = model.sample(case_local_updates=True)
    for state, structure, stored in zip(states[0], routes[0], likelihood[0]):
        assert stored == pytest.approx(model.log_likelihood(state, structure), abs=1e-10)


@pytest.mark.parametrize('selected', [False, True])
def test_full_likelihood_population_and_selection_terms_are_evaluated_and_returned(
        monkeypatch, selected):
    data = data_fixture()
    data['programs'][0]['observations'] = [row for row in data['programs'][0]['observations']
        if all(op['basis'] not in {'visit_count', 'payer_hours', 'agency_hours'}
               for op in row['operators'])]
    if selected:
        for row in data['programs'][0]['observations']:
            row['sampling'] = 'delay_selected'
    data['programs'][0]['observations'].append(observation(
        'population-review', 'single_visit_cycle', 4., 10., case=None,
        activities=['review']))
    model = VisitHierarchy(data, Config(population_size=16,
        modeled_channels=('elapsed',), selection_sd=2. if selected else 0.,
        case_scale_sampler='interwoven'))
    state = np.zeros(model.layout.size)
    structures = np.zeros(len(model.programs), dtype=int)
    current = model.log_likelihood(state, structures)
    proposal = interweave.case_scale_proposal(model, state, 0, .4)
    changed = model.log_likelihood(proposal['state'], structures)
    assert changed != current  # population factor depends on spread

    def deterministic_ess(anchor, indices, callback, old, rng):
        draw = np.array([anchor[0]+.4])
        adjusted = callback(draw)
        assert math.isfinite(adjusted)
        return draw, adjusted, 1

    monkeypatch.setattr(interweave, 'elliptical_slice', deterministic_ess)
    moved, returned, calls = model.case_scale_interweave_update(
        state, structures, current, np.random.default_rng(41))
    assert calls == 2
    assert returned == model.log_likelihood(moved, structures)
    assert returned != current


def test_zero_width_is_noop_and_nonfinite_transform_does_not_mask_contract_errors():
    model = VisitHierarchy(data_fixture(), Config(population_size=16,
        case_log_sd_prior=0.,
        case_scale_sampler='interwoven'))
    state = np.zeros(model.layout.size)
    structures = np.zeros(len(model.programs), dtype=int)
    current = model.log_likelihood(state, structures)
    moved, returned, calls = model.case_scale_interweave_update(
        state, structures, current, np.random.default_rng(4))
    np.testing.assert_array_equal(moved, state)
    assert returned == current and calls == 0
    free = VisitHierarchy(data_fixture(), Config(population_size=16))
    assert interweave.case_scale_proposal(free,
        np.zeros(free.layout.size), 0, -1e308) is None
    with pytest.raises(ValueError, match='finite state layout'):
        interweave.case_scale_proposal(free,
            np.full(free.layout.size, np.nan), 0, 0.)


def test_runner_cli_and_preflight_bind_opt_in_without_sampling(tmp_path, capsys):
    path = tmp_path/'data.json'
    path.write_text(json.dumps(data_fixture()))
    out = tmp_path/'preflight'
    run_main(['--data', str(path), '--out', str(out), '--preflight',
        '--population-size', '16', '--case-scale-sampler', 'interwoven'])
    manifest = json.loads((out/'manifest.json').read_text())
    report = json.loads((out/'preflight.json').read_text())
    assert manifest['provenance']['config']['case_scale_sampler'] == 'interwoven'
    assert report['case_scale_sampler'] == 'interwoven'
    assert report['case_scale_transition']['enabled']
    assert not report['sampling_performed']
    capsys.readouterr()
