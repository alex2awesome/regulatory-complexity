"""Source-free integration checks; none are evidence of real-data recovery."""
import copy
from dataclasses import replace

import numpy as np
import pytest
from scipy.special import logsumexp
from scipy.stats import multinomial

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.run_visit_hierarchy import preflight_report, precision_check
from procbench_fixtures import data_fixture
from test_cohort_histograms import histogram_fixture
from test_cohort_quantiles import cohort_fixture


def model_data():
    data = data_fixture()
    cohort = histogram_fixture()
    cohort.update(bin_edges=[0, 15, 30, None], bin_counts=[3, 4, 3],
                  operators=[cohort['operators'][0]], operator_weights=[1.])
    data['programs'][0].update(observations=[], histogram_cohorts=[cohort])
    return data


def configuration(**kwargs):
    return Config(population_size=256, modeled_channels=('elapsed',), **kwargs)


def manual_probabilities(trace, operator, edges):
    """Independent boundary comparison, not the production bin-assignment helper."""
    values = trace.values(operator)
    weights = getattr(trace, 'weights', np.full(len(values), 1 / len(values)))
    upper = edges[1:-1] + [np.inf]
    masses = []
    for i, (lo, hi) in enumerate(zip(edges[:-1], upper)):
        mask = (values >= lo if i == 0 else values > lo) & (values <= hi)
        masses.append(weights[mask].sum())
    return np.asarray(masses)


def test_integrated_histogram_matches_independent_multinomial_without_source_latent():
    data = model_data()
    model = VisitHierarchy(data, configuration())
    assert model.sources == []
    assert model.programs[0]['cases'] == []
    z = np.zeros(model.layout.size)
    p = model.programs[0]
    trace = model.trace(p, z, model.parameters(z), 0, True)
    c = p['histogram_cohorts'][0]
    probabilities = manual_probabilities(trace, c['operators'][0], c['bin_edges'])
    expected = multinomial.logpmf(c['bin_counts'], c['sample_size'], probabilities)
    assert np.isfinite(expected)
    assert model.log_likelihood(z, [0]) == pytest.approx(expected)
    assert model.log_likelihood_reference(z, [0]) == pytest.approx(expected)
    assert list(model.log_likelihood(z, [0], parts=True)) == ['J__P:histogram_cohort:published_histogram']
    changed = VisitHierarchy(data, replace(model.cfg, source_sd=3., report_sd=2., contamination=.4))
    assert changed.layout.size == model.layout.size
    assert changed.log_likelihood(z, [0]) == pytest.approx(expected)


@pytest.mark.parametrize('weights', [[.25, .75], [0., 1.]])
def test_histogram_interpretation_is_drawn_once_not_independently_per_bin(weights):
    data = model_data()
    c = data['programs'][0]['histogram_cohorts'][0]
    c.update(operators=histogram_fixture()['operators'], operator_weights=weights)
    model = VisitHierarchy(data, configuration())
    z = np.zeros(model.layout.size)
    components = []
    for op in c['operators']:
        single = copy.deepcopy(data)
        single['programs'][0]['histogram_cohorts'][0].update(operators=[op], operator_weights=[1.])
        components.append(VisitHierarchy(single, model.cfg).log_likelihood(z, [0]))
    with np.errstate(divide='ignore'):
        expected = logsumexp(np.log(weights) + components)
    assert model.log_likelihood(z, [0]) == pytest.approx(expected)


@pytest.mark.parametrize('scope', [None, ['full'], ['short']])
def test_histogram_integrates_path_population_before_multinomial(scope):
    data = model_data()
    route = data['programs'][0]['routes'][0]
    blocks = route.pop('blocks')
    route['paths'] = [dict(id='full', probability_weight=.7, blocks=blocks),
                      dict(id='short', probability_weight=.3,
                           blocks=[dict(id='last', operations=['decide'])])]
    if scope is not None:
        data['programs'][0]['histogram_cohorts'][0]['population_path_scope'] = scope
    model = VisitHierarchy(data, configuration())
    z = np.zeros(model.layout.size)
    p = model.programs[0]
    c = p['histogram_cohorts'][0]
    trace = model.trace(p, z, model.parameters(z), 0, True)
    if scope is not None:
        # One selected path is the conditional population, not weighted down by
        # its unconditioned prevalence in the full process.
        index = 0 if scope == ['full'] else 1
        trace = model.trace(p, z, model.parameters(z), 0, True, path_index=index)
    probs = manual_probabilities(trace, c['operators'][0], c['bin_edges'])
    expected = multinomial.logpmf(c['bin_counts'], c['sample_size'], probs)
    assert model.log_likelihood(z, [0]) == pytest.approx(expected)
    assert model.log_likelihood_reference(z, [0]) == pytest.approx(expected)


def test_histogram_rejects_scope_absent_from_declared_routes_and_invalid_conditioning():
    data = model_data()
    c = data['programs'][0]['histogram_cohorts'][0]
    c['population_path_scope'] = ['not_a_path']
    with pytest.raises(ValueError, match='known case-path'):
        VisitHierarchy(data, configuration())
    c.pop('population_path_scope')
    c['population_condition'] = 'first_visit'
    with pytest.raises(ValueError, match='first-cycle'):
        VisitHierarchy(data, configuration())


def test_larger_configured_grid_that_rounds_to_same_effective_grid_cannot_pass_precision():
    data = model_data()
    cfg = replace(configuration(), population_size=257)
    model = VisitHierarchy(data, cfg)
    fine = VisitHierarchy(data, replace(cfg, population_size=258))
    states = np.zeros((1, 8, model.layout.size))
    routes = np.zeros((1, 8, 1), dtype=int)
    result = precision_check(model, fine, states, routes)
    assert result['base_effective_population_sizes'] == {'J__P': 512}
    assert result['refined_effective_population_sizes'] == {'J__P': 512}
    assert not result['histogram_integration_refined_or_unused']
    assert not result['likelihood_acceptable']


@pytest.mark.parametrize('overlap', ['program', 'individual', 'rate', 'quantile', 'factor_id'])
def test_histogram_rejects_overlapping_cohorts(overlap):
    data = model_data()
    p = data['programs'][0]
    c = p['histogram_cohorts'][0]
    if overlap == 'program':
        data['programs'].append(dict(copy.deepcopy(p), id='J__Q'))
    elif overlap in {'individual', 'factor_id'}:
        p['observations'] = [data_fixture()['programs'][0]['observations'][0]]
        if overlap == 'individual':
            p['observations'][0]['cohort_id'] = c['cohort_id']
        else:
            c['id'] = p['observations'][0]['id']
    elif overlap == 'rate':
        p['rate_observations'] = [dict(repeat_key='corrections', successes=1, trials=10,
                                       event='any_correction_per_case', independent_cohort=True,
                                       cohort_scope='completed_cases_for_repeat_block',
                                       cohort_id=c['cohort_id'])]
    else:
        p['quantile_cohorts'] = [dict(cohort_fixture(), cohort_id=c['cohort_id'])]
    with pytest.raises(ValueError, match='overlap'):
        VisitHierarchy(data, configuration())


def test_phase_histogram_requires_phase_model():
    data = model_data()
    c = data['programs'][0]['histogram_cohorts'][0]
    c['operators'] = [dict(basis='wait_elapsed', activity_ids=['review'], visits='first')]
    with pytest.raises(ValueError, match='within_visit_phases'):
        VisitHierarchy(data, configuration())
    model = VisitHierarchy(data, configuration(within_visit_phases=True))
    z = np.zeros(model.layout.size)
    assert model.log_likelihood(z, [0]) == pytest.approx(model.log_likelihood_reference(z, [0]))


def test_histogram_zero_grid_support_is_not_replaced_with_pseudocounts():
    data = model_data()
    data['programs'][0]['histogram_cohorts'][0]['bin_edges'] = [0, 1e-12, 2e-12, None]
    model = VisitHierarchy(data, configuration())
    assert model.log_likelihood(np.zeros(model.layout.size), [0]) == -np.inf


def test_counts_do_not_allocate_cases_and_reports_require_grid_refinement():
    cfg = configuration(chains=1, warmup=0, draws=8)
    data = model_data()
    model = VisitHierarchy(data, cfg)
    larger = copy.deepcopy(data)
    larger['programs'][0]['histogram_cohorts'][0].update(sample_size=10000, bin_counts=[3000, 4000, 3000])
    assert model.layout.size == VisitHierarchy(larger, cfg).layout.size
    assert model.programs[0]['case_coordinates'].size == 0
    states, routes, ll, _ = model.sample()
    assert np.isfinite(ll).all()
    report = model.report(states, routes, ll)
    c = report['programs']['J__P']['histogram_cohorts']['published_histogram']
    assert c['sample_size'] == 10
    assert c['posterior_mean_weights'] == [1.]
    preflight = preflight_report(model)
    assert preflight['sources'] == 0
    assert preflight['cases'] == 0
    assert preflight['independent_histogram_cohorts'] == 1
    assert preflight['histogram_observed_cases'] == 10
    assert preflight['direct_resource_observations']['elapsed'] == 1
    assert preflight['observation_rows'] == 1  # One factor, not three bins or ten cases.
    precision = precision_check(model, model, states, routes)
    assert not precision['histogram_integration_refined_or_unused']
    assert not precision['likelihood_acceptable']
    fine = VisitHierarchy(data, replace(cfg, population_size=1024))
    assert precision_check(model, fine, states, routes)['histogram_integration_refined_or_unused']
