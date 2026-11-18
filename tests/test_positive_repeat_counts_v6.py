"""The optional positive-count component must not leak into executable visits."""
import copy

import numpy as np
import pytest
from scipy.special import betaincinv, ndtr

from pipeline.procbench.bayes_trace_hierarchy import VisitHierarchy
from pipeline.procbench.case_local_likelihood import case_view, case_log_likelihood
from pipeline.procbench.positive_repeat_counts import log_probability
from procbench_fixtures import data_fixture, observation
from test_case_paths import cfg, path_data
from test_positive_repeat_counts import row


@pytest.mark.parametrize('fixture', [data_fixture, path_data])
def test_count_added_once_in_both_route_modes_without_old_coordinate_changes(fixture):
    data = fixture()
    # The fixture's labor observation requires the default three channels.
    from pipeline.procbench.bayes_trace_hierarchy import Config
    config = Config(population_size=16)
    base = VisitHierarchy(copy.deepcopy(data), config)
    data['programs'][0]['positive_repeat_count_observations'] = [row()]
    model = VisitHierarchy(data, config)
    assert model.layout.size == base.layout.size + 1
    for name, indices in base.layout.slices.items():
        np.testing.assert_array_equal(model.layout.slices[name], indices)
    p = model.programs[0]
    assert p['cases'] == base.programs[0]['cases']
    assert p['repeat_keys'] == base.programs[0]['repeat_keys']
    np.testing.assert_array_equal(p['population_normals'], base.programs[0]['population_normals'])
    assert model.sources == base.sources
    z = np.random.default_rng(91).normal(scale=.25, size=model.layout.size)
    base_parts = base.log_likelihood(z[:-1], [0], parts=True)
    parts = model.log_likelihood(z, [0], parts=True)
    key = p['id'] + ':positive_repeat_count:count-1'
    assert set(parts) == set(base_parts) | {key}
    assert {k:v for k,v in parts.items() if k != key} == base_parts
    expected = log_probability(3, float(betaincinv(2, 3, ndtr(z[-1]))))
    assert parts[key] == pytest.approx(expected)
    assert model.log_likelihood(z, [0]) == pytest.approx(sum(base_parts.values()) + expected)
    assert model.log_likelihood_reference(z, [0]) == pytest.approx(model.log_likelihood(z, [0]))
    # Changing count severity cannot change time, fees, visits or labor.
    old_burden = model.expected_burden(p, z, model.parameters(z), 0)
    z[-1] += 1.
    assert model.expected_burden(p, z, model.parameters(z), 0) == old_burden
    if fixture is path_data:
        view = case_view(p, 'a')
        assert case_log_likelihood(model, view, z, 0) == pytest.approx(
            model.log_likelihood(z, [0], parts=True)[p['id']+':case:a'])


def test_empty_extension_keeps_saved_seed_sampler_replay():
    data = path_data()
    config = cfg(chains=1, warmup=2, draws=8)
    base = VisitHierarchy(copy.deepcopy(data), config)
    data['programs'][0]['positive_repeat_count_observations'] = []
    empty = VisitHierarchy(data, config)
    assert base.layout.size == empty.layout.size
    assert list(base.layout.slices) == list(empty.layout.slices)
    for expected, actual in zip(base.sample(), empty.sample()):
        np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize('where', ['earlier_program', 'later_program', 'count_program', 'group'])
def test_cross_program_case_and_group_overlap_fails_closed(where):
    data = path_data()
    other = copy.deepcopy(data['programs'][0])
    other['id'] = 'OTHER'
    other['case_path_scope'] = {}
    other['observations'] = [observation('other', 'whole_case_clock', 1, 9, case='case-1')]
    p = data['programs'][0]
    p['positive_repeat_count_observations'] = [row()]
    if where == 'earlier_program':
        data['programs'].insert(0, other)
    elif where == 'later_program':
        data['programs'].append(other)
    elif where == 'count_program':
        other['observations'] = []
        other['positive_repeat_count_observations'] = [row(id='new', evidence_group_id='new-group')]
        data['programs'].append(other)
    else:
        p['observations'][0]['evidence_group_id'] = 'episode-1'
    with pytest.raises(ValueError, match='overlaps'):
        VisitHierarchy(data, cfg())


def test_count_factor_collision_does_not_overwrite_a_population_observation():
    data = path_data()
    p = data['programs'][0]
    p['positive_repeat_count_observations'] = [row()]
    p['observations'].append(observation('positive_repeat_count:count-1',
                                        'whole_case_clock', 1, 5, case=None))
    with pytest.raises(ValueError, match='factor key collision'):
        VisitHierarchy(data, cfg())


def test_old_coordinates_preserved_across_multiple_programs_and_conditional_target():
    data = path_data()
    second = copy.deepcopy(data['programs'][0])
    second['id'] = 'SECOND'
    data['programs'].append(second)
    base = VisitHierarchy(copy.deepcopy(data), cfg())
    data['programs'][0]['positive_repeat_count_observations'] = [row()]
    model = VisitHierarchy(data, cfg())
    for name, indices in base.layout.slices.items():
        np.testing.assert_array_equal(model.layout.slices[name], indices)
    z = np.zeros(model.layout.size)
    assert model.log_likelihood(z, [0,0], _program_index=1) == pytest.approx(
        base.log_likelihood(z[:-1], [0,0], _program_index=1))


def test_runner_checks_source_bytes_and_literal_quotes(tmp_path):
    import hashlib
    from pipeline.procbench.run_visit_hierarchy import positive_repeat_source_paths, preflight_report
    source = tmp_path/'source.md'
    source.write_text('Reported paperwork THREE times before approval.')
    ref = dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               quote_segments=['paperwork THREE times'])
    data = path_data()
    data['programs'][0]['positive_repeat_count_observations'] = [row(source_bound=[ref])]
    model = VisitHierarchy(data, cfg())
    assert positive_repeat_source_paths(model) == [source]
    assert preflight_report(model)['positive_repeat_counts']['rows'] == 1
    source.write_text('Changed source')
    with pytest.raises(ValueError, match='Changed positive-repeat source'):
        positive_repeat_source_paths(model)
    ref['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    model = VisitHierarchy(data, cfg())
    with pytest.raises(ValueError, match='quote absent'):
        preflight_report(model)


def test_marginal_reduction_cannot_silently_drop_positive_counts():
    from pipeline.procbench.marginal_conditional_frames import MarginalConditionalFrame
    from test_conditional_case_frames import frame_config, frame_data
    data = frame_data()
    data['programs'][0]['positive_repeat_count_observations'] = [row()]
    with pytest.raises(ValueError, match='bounded fields'):
        MarginalConditionalFrame(data, frame_config())


def test_posterior_report_keeps_conditional_counts_out_of_burden():
    data = path_data()
    data['programs'][0]['positive_repeat_count_observations'] = [row()]
    model = VisitHierarchy(data, cfg())
    states = np.random.default_rng(91).normal(scale=.1, size=(2,8,model.layout.size))
    routes = np.zeros((2,8,1), dtype=int)
    likelihood = np.array([[model.log_likelihood(z, [0]) for z in chain] for chain in states])
    report = model.report(states, routes, likelihood)
    count = report['positive_repeat_counts']['J__P:paperwork_redo_or_resubmission']
    assert count['positive_event_probability'] is None
    assert count['unconditional_mean_additional_rounds'] is None
    assert count['executable_block_attached'] is False
    assert count['burden_headline_eligible'] is False
    assert 'positive_repeat:J__P:paperwork_redo_or_resubmission:continuation' in report['diagnostics']
