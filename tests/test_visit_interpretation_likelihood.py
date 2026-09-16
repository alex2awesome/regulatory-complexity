import copy
import math

import numpy as np
import pytest
from scipy.special import logsumexp
from scipy.stats import t

from pipeline.procbench.bayes_trace_hierarchy import (
    Config, VisitHierarchy, unmodeled_duration_log_probability)
from pipeline.procbench.compile_visit_durations import compile_durations, hypothesis_options
from test_trace_hierarchy import data_fixture
from test_visit_hypotheses import hypothesis_inputs


def prior(weight=.25):
    return dict(residual_weight=weight, unmodeled_median_days=7., unmodeled_log_scale=3.,
                allocation='uniform_basis_then_reading')


def residual():
    return dict(basis='unmodeled_duration', median_days=7., log_scale=3.)


def mixed_data():
    data = data_fixture()
    o = data['programs'][0]['observations'][1]
    o['operators'].append(residual())
    o['operator_weights'] = [.75, .25]
    return data


def test_residual_is_a_normalized_absolute_log_report_distribution():
    op = residual()
    edges = np.r_[0., np.exp(np.linspace(-35., 35., 200)), np.inf]
    mass = sum(np.exp(unmodeled_duration_log_probability(a, b, op)) for a, b in zip(edges[:-1], edges[1:]))
    assert mass == pytest.approx(1., abs=1e-13)
    lo, hi = 3., 14.
    expected = t.cdf((math.log(hi)-math.log(7))/3, 4) - t.cdf((math.log(lo)-math.log(7))/3, 4)
    assert np.exp(unmodeled_duration_log_probability(lo, hi, op)) == pytest.approx(expected)


def test_residual_alone_does_not_inform_any_process_or_source_coordinate():
    data = data_fixture()
    o = data['programs'][0]['observations'][1]
    o.update(operators=[residual()], operator_weights=[1.])
    data['programs'][0]['observations'] = [o]
    model = VisitHierarchy(data, Config(population_size=16))
    rng = np.random.default_rng(523)
    values = [model.log_likelihood(z, [0]) for z in rng.normal(size=(30, model.layout.size))]
    np.testing.assert_allclose(values, values[0], rtol=0, atol=1e-14)


def test_absent_activity_retains_residual_prior_penalty_not_renormalization():
    data = mixed_data()
    o = data['programs'][0]['observations'][1]
    o['operators'][0]['activity_ids'] = ['absent_from_route']
    model = VisitHierarchy(data, Config(population_size=16))
    z = np.zeros(model.layout.size)
    actual = model.log_likelihood(z, [0], parts=True)['J__P:task']
    expected = math.log(.25) + unmodeled_duration_log_probability(o['lower'], o['upper'], residual())
    assert actual == pytest.approx(expected)
    assert model.log_likelihood_reference(z, [0], parts=True)['J__P:task'] == pytest.approx(expected)


def test_batched_reference_and_responsibilities_agree():
    data = mixed_data()
    model = VisitHierarchy(data, Config(population_size=16))
    rng = np.random.default_rng(938)
    states = rng.normal(scale=.3, size=(4, 8, model.layout.size))
    structures = np.zeros((4, 8, 1), dtype=int)
    ll, weights = [], []
    p = model.programs[0]
    for z in states.reshape(-1, model.layout.size):
        actual = model.log_likelihood(z, [0])
        assert actual == pytest.approx(model.log_likelihood_reference(z, [0]), abs=1e-10)
        par = model.parameters(z)
        terms = model._observation_parts(p, model.trace(p, z, par, 0), None, par, return_log_terms=True)
        _, start, end = p['compiled']['groups'][1]
        weights.append(np.exp(terms[start:end]-logsumexp(terms[start:end])))
        ll.append(actual)
    report = model.report(states, structures, np.asarray(ll).reshape(4, 8))
    interpretation = report['programs']['J__P']['interpretations']['task']
    np.testing.assert_allclose(interpretation['posterior_mean_weights'], np.mean(weights, axis=0))
    assert sum(interpretation['posterior_mean_weights']) == pytest.approx(1.)
    assert 'J__P:interpretation:task:1' in report['diagnostics']


@pytest.mark.parametrize('change', [dict(log_scale=0.), dict(median_days=-1.),
                                  dict(log_scale=float('nan')), dict(median_days=True),
                                  dict(activity_ids=['review'])])
def test_invalid_residual_reference_rejected(change):
    data = mixed_data()
    data['programs'][0]['observations'][1]['operators'][-1].update(change)
    with pytest.raises(ValueError, match='reference distribution'):
        VisitHierarchy(data)


def test_residual_cannot_mix_elapsed_with_hours_or_counts():
    for index in (2, 3):
        data = data_fixture()
        data['programs'][0]['observations'][index]['operators'].append(residual())
        data['programs'][0]['observations'][index]['operator_weights'] = [.75, .25]
        with pytest.raises(ValueError, match='measurement units|count probabilities'):
            VisitHierarchy(data)


def test_hypothesis_compilation_is_opt_in_and_preserves_original_evidence():
    e, v, s, d, p, audit = hypothesis_inputs()
    original = copy.deepcopy((e, v, s, audit))
    assert not compile_durations(e, v, s, d, p)['observations']
    assert not compile_durations(e, v, s, d, p, audit)['observations']
    p['hypothesis_prior'] = prior()
    result = compile_durations(e, v, s, d, p, audit)
    o = result['observations'][0]
    assert o['operator_weights'] == [.75, .25]
    assert o['operators'][-1] == residual()
    assert o['provenance']['interpretation_hypotheses'] == audit['measurements'][0]
    assert result['coverage']['compiled_with_interpretation_assumptions'] == 1
    assert (e, v, s, audit) == original
    p['interpretation_priors'] = {'m1': [1.]}
    with pytest.raises(ValueError, match='old-audit weights'):
        compile_durations(e, v, s, d, p, audit)


def test_partial_boundary_is_not_silently_promoted_to_full_cycle():
    e, v, s, d, p, audit = hypothesis_inputs()
    v['measurements'][0]['operators'][0]['end'] = 'other_milestone'
    audit['measurements'][0]['hypotheses'][0]['operator']['end'] = 'other_milestone'
    p['hypothesis_prior'] = prior()
    result = compile_durations(e, v, s, d, p, audit)
    assert not result['observations']
    assert 'partial_activity_boundary_is_not_a_complete_cycle' in result['dispositions'][0]['reasons']


def test_weight_allocation_does_not_favor_a_basis_with_more_readings():
    e, v, s, d, p, audit = hypothesis_inputs()
    row = audit['measurements'][0]
    first = copy.deepcopy(row['hypotheses'][0])
    first['operator'].update(basis='sum_visit_cycles', visits='all_in_completed_case')
    row['hypotheses'].append(first)
    second = copy.deepcopy(first)
    second['operator']['visits'] = 'reported_subset'
    row['hypotheses'].append(second)
    ops, weights = hypothesis_options(row, prior())
    assert weights == [.375, .1875, .1875, .25]
    assert ops[-1] == residual()
