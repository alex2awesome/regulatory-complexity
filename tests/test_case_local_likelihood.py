import copy
from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.case_local_likelihood import (case_view, case_update_views,
    case_log_likelihood, refresh_full_likelihood)
from procbench_fixtures import observation
from test_case_paths import cfg, path_data
from test_absent_event_censoring import fixture, seal


def two_case_grouped(selected=False):
    data = fixture(grouped=True, selected=selected)
    p = data['programs'][0]
    # Retain one pending optional-event group; another case has two operators.
    second = observation('second', 'whole_case_clock', 3., 60., case='b')
    second['operators'].append(dict(basis='single_visit_cycle', activity_ids=['file']))
    second['operator_weights'] = [.7, .3]
    if selected:
        second['sampling'] = 'delay_selected'
    p['observations'].append(second)
    p['observations'].append(observation('population', 'whole_case_clock', 3., 70., case=None))
    seal(p)
    return data


@pytest.mark.parametrize('selected', [False, True])
@pytest.mark.parametrize('grouped', [False, True])
@pytest.mark.parametrize('phases', [False, True])
def test_local_factors_and_deltas_equal_complete_target(selected, grouped, phases):
    data = two_case_grouped(selected) if grouped else path_data()
    if selected and not grouped:
        for o in data['programs'][0]['observations']:
            o['sampling'] = 'delay_selected'
    model = VisitHierarchy(data, cfg(selection_sd=float(selected), within_visit_phases=phases))
    p = model.programs[0]
    views = case_update_views(model)
    rng = np.random.default_rng(312)
    for _ in range(5):
        z = rng.normal(scale=.35, size=model.layout.size)
        full_parts = model.log_likelihood(z, [0], parts=True)
        for block, (pi, view) in views.items():
            case = view['cases'][0]
            value = case_log_likelihood(model, view, z, 0)
            assert value == pytest.approx(full_parts[p['id'] + ':case:' + case], abs=1e-12)
            changed = z.copy()
            changed[list(block)] += rng.normal(scale=.1, size=len(block))
            updated = case_log_likelihood(model, view, changed, 0)
            assert updated - value == pytest.approx(
                model.log_likelihood(changed, [0]) - model.log_likelihood(z, [0]), abs=2e-11)
            assert pi == 0


def test_compiled_views_preserve_group_members_weights_and_original_arrays():
    model = VisitHierarchy(two_case_grouped(), cfg())
    p = model.programs[0]
    a, b = case_view(p, 'a'), case_view(p, 'b')
    assert len(a['observations']) == 2 and len(a['joint_duration_reports']) == 1
    assert a['joint_duration_reports'][0]['columns'] == [0, 1]
    assert len(b['observations']) == 1 and b['joint_duration_reports'] == []
    assert b['compiled']['groups'] == [('second', 0, 2)]
    np.testing.assert_allclose(np.exp(b['compiled']['logweights']), [.7, .3])
    assert a['cache'] is not p['cache'] and b['cache'] is not a['cache']
    original = p['compiled']['lower'].copy()
    a['compiled']['lower'][0] = 999
    np.testing.assert_array_equal(p['compiled']['lower'], original)
    assert a['case_coordinates'].shape[0] == 1 and a['case_index'] == {'a': 0}


def test_only_exact_case_blocks_accelerate_and_plain_routes_fall_back():
    data = path_data()
    plain = copy.deepcopy(data['programs'][0])
    plain['id'] = 'J__plain'
    route = plain['routes'][0]
    route['blocks'] = route['paths'][0]['blocks']
    route['operations'] = [op for op in route['operations'] if op['id'] != 'deny']
    del route['paths']
    plain.pop('case_path_scope')
    plain['observations'] = [observation('plain', 'whole_case_clock', 3., 60., case='a')]
    data['programs'].append(plain)
    model = VisitHierarchy(data, cfg())
    views = case_update_views(model)
    assert len(views) == 3
    assert sum(pi == 0 and view is not None for pi, view in views.values()) == 2
    assert sum(pi == 1 and view is None for pi, view in views.values()) == 1
    for block in views:
        assert any(tuple(row) == block for program in model.programs
                   for row in program['case_coordinates'])
    with pytest.raises(ValueError, match='explicit case paths'):
        case_view(model.programs[1], 'a')
    with pytest.raises(ValueError, match='Unknown case'):
        case_view(model.programs[0], 'missing')


@pytest.mark.parametrize('selected', [False, True])
def test_accelerated_sampler_preserves_target_and_reference_transitions(selected):
    config = cfg(chains=1, warmup=3, draws=8, seed=91, selection_sd=float(selected))
    data = two_case_grouped(selected)
    standard = VisitHierarchy(data, config)
    local = VisitHierarchy(data, config)
    initial = (np.zeros((1, standard.layout.size)), np.zeros((1, 1), dtype=int))
    a, routes_a, ll_a, _ = standard.sample(initial=initial)
    b, routes_b, ll_b, _ = local.sample(initial=initial, case_local_updates=True)
    # Equivalent ESS slices for these finite fixtures, to floating precision.
    np.testing.assert_allclose(a, b, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(routes_a, routes_b)
    np.testing.assert_allclose(ll_a, ll_b, rtol=0, atol=1e-11)
    for j in range(config.draws):
        assert ll_b[0, j] == pytest.approx(local.log_likelihood_reference(b[0, j], routes_b[0, j]), abs=2e-11)


def test_invalid_opt_in_rejected_before_sampling():
    model = VisitHierarchy(path_data(), cfg(chains=1, warmup=0, draws=8))
    with pytest.raises(ValueError, match='explicit boolean'):
        model.sample(case_local_updates=1)


def test_multiple_program_sampler_refreshes_before_later_selection_block(monkeypatch):
    data = two_case_grouped(selected=True)
    other = copy.deepcopy(data['programs'][0])
    other['id'] = 'J__other'
    seal(other)
    data['programs'].append(other)
    model = VisitHierarchy(data, cfg(chains=1, warmup=1, draws=8, seed=109, selection_sd=1.))
    import pipeline.procbench.bayes_trace_hierarchy as module
    real_refresh = module.refresh_full_likelihood
    refreshes = []
    def counted(*args):
        refreshes.append(1)
        return real_refresh(*args)
    monkeypatch.setattr(module, 'refresh_full_likelihood', counted)
    initial = (np.zeros((1, model.layout.size)), np.zeros((1, 2), dtype=int))
    states, routes, ll, _ = model.sample(initial=initial, case_local_updates=True)
    assert len(refreshes) == 2 * 9  # Before program2 selection, and sweep end.
    for j in range(8):
        assert ll[0, j] == pytest.approx(model.log_likelihood_reference(states[0, j], routes[0, j]), abs=2e-11)


def test_local_delta_inconsistency_fails_closed():
    model = VisitHierarchy(path_data(), cfg())
    z = np.zeros(model.layout.size)
    full = model.log_likelihood(z, [0])
    with pytest.raises(RuntimeError, match='complete target'):
        refresh_full_likelihood(model, z, [0], full + 1.)


def test_chunked_case_blocks_preserve_target_and_local_case_ownership():
    data = two_case_grouped(selected=False)
    base = cfg(chains=1, warmup=1, draws=8, seed=887)
    full = VisitHierarchy(data, base)
    chunked = VisitHierarchy(data, replace(base, case_update_block_size=1))
    assert full.layout.slices.keys() == chunked.layout.slices.keys()
    for key in full.layout.slices:
        np.testing.assert_array_equal(full.layout.slices[key], chunked.layout.slices[key])
    z = np.linspace(-.2, .2, full.layout.size)
    assert full.log_likelihood(z, [0]) == pytest.approx(chunked.log_likelihood(z, [0]), abs=1e-12)
    views = case_update_views(chunked)
    assert len(views) == sum(row.size for row in chunked.programs[0]['case_coordinates'])
    for block, (pi, view) in views.items():
        assert len(block) == 1 and pi == 0 and len(view['cases']) == 1
    initial = (np.zeros((1, chunked.layout.size)), np.zeros((1, 1), dtype=int))
    states, routes, likelihood, _ = chunked.sample(initial=initial, case_local_updates=True)
    for j in range(base.draws):
        assert likelihood[0, j] == pytest.approx(
            chunked.log_likelihood_reference(states[0, j], routes[0, j]), abs=2e-11)


def test_case_update_block_size_validation_and_legacy_default():
    assert Config().case_update_block_size == 0
    with pytest.raises(ValueError, match='nonnegative integer'):
        Config(case_update_block_size=-1)
    with pytest.raises(ValueError, match='nonnegative integer'):
        Config(case_update_block_size=True)
