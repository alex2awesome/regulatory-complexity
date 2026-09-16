import copy
import math
from dataclasses import asdict, replace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import expit
from scipy.stats import norm

from pipeline.procbench.bayes_preparation_measurement import Config as FixedConfig, PreparationMeasurementModel
from pipeline.procbench.bayes_variable_preparation import Config, VariablePreparationModel, partitioned_budget
from pipeline.procbench.phase_mixture import quantile_density
from pipeline.procbench.run_process_measurement import finer_config, make_model, saved_config
from test_bayes_hierarchy import measurement
from test_preparation_measurement import inputs
from test_process_measurement import audit_row


def test_total_coverage_prior_does_not_depend_on_segmentation_count():
    rng = np.random.default_rng(7138)
    z = rng.normal(size=(4000, 4))
    for k in (1, 2, 4):
        fractions = np.array([partitioned_budget(row[:k]) for row in z])
        assert np.all(fractions > 0) and np.all(fractions.sum(axis=1) < 1)
        np.testing.assert_allclose(fractions.sum(axis=1), norm.cdf(z[:, 0]), atol=1e-14)
        np.testing.assert_allclose(fractions.mean(axis=0), np.full(k, .5/k), atol=.013)


def test_case_fraction_is_shared_across_reports_but_not_across_cases():
    e, a, o, prep = inputs(False)
    e['measurements'][2]['case_id'] = 'c2'
    extra = copy.deepcopy(o['cases'][0])
    extra['case_id'] = 'c2'
    o['cases'].append(extra)
    model = VariablePreparationModel([e], [a], [o], [prep])
    p = model.programs[0]
    z = np.zeros(model.layout.size)
    before = model.parameters(p, z)
    z[p['case_fraction_indices'][0]] = 2.
    after = model.parameters(p, z)
    assert after['case_preparation']['c1'] > before['case_preparation']['c1']
    assert after['case_preparation']['c2'] == before['case_preparation']['c2']
    for case, rows in p['cases'].items():
        conditional = dict(after, prep=after['case_preparation'][case])
        for row in rows:
            expected = PreparationMeasurementModel.observation_probability(model, row, after['mu'], conditional)
            assert model.observation_probability(row, after['mu'], after) == pytest.approx(expected)


def test_zero_spread_old_budget_recovers_previous_individual_likelihood():
    e, a, o, prep = inputs()
    cfg = Config(case_preparation_logit_sd=0, preparation_budget_mode='dirichlet')
    model = VariablePreparationModel([e], [a], [o], [prep], cfg)
    old = PreparationMeasurementModel([e], [a], [o], [prep], FixedConfig())
    assert model.layout.size == old.layout.size
    rng = np.random.default_rng(12)
    for z in rng.normal(size=(10, model.layout.size)):
        assert model.log_likelihood(z) == pytest.approx(old.log_likelihood(z), abs=1e-9)


def test_population_clock_quantile_convolves_fraction_instead_of_scaling_median():
    e, a, o, prep = inputs()
    cfg = Config(case_preparation_logit_sd=1.4, fraction_quadrature=128, outcome_contrast_sd=0)
    model = VariablePreparationModel([e], [a], [o], [prep], cfg)
    z = np.zeros(model.layout.size)
    p = model.programs[0]
    par = model.parameters(p, z)
    median, _ = model.population_summary(par, 'first_submission', 'initial_decision', 'population_median')
    logit = math.log(cfg.prep_fraction/(1-cfg.prep_fraction))
    def integrand(node):
        factor = 1-expit(logit+cfg.case_preparation_logit_sd*node)
        return norm.pdf(node)*norm.cdf((median-math.log(factor)-par['mu'])/par['sigma'])
    assert quad(integrand, -10, 10, epsabs=1e-11)[0] == pytest.approx(.5, abs=1e-8)
    assert abs(median-(par['mu']+math.log1p(-par['prep']))) > .01
    mean, _ = model.population_summary(par, 'first_submission', 'initial_decision', 'population_mean')
    expected_fraction = quad(lambda n: norm.pdf(n)*(1-expit(logit+cfg.case_preparation_logit_sd*n)), -10, 10)[0]
    assert mean == pytest.approx(par['mu']+.5*par['sigma']**2+math.log(expected_fraction), abs=1e-9)


def test_native_quantile_density_matches_independent_cdf_and_scipy_path():
    rng = np.random.default_rng(51)
    for _ in range(20):
        loc = rng.normal(size=8)
        weights = rng.dirichlet(np.ones(8))
        sigma = .2+rng.random()
        for probability in (.05, .5, .9):
            value, density = quantile_density(probability, loc, weights, sigma)
            assert weights @ norm.cdf((value-loc)/sigma) == pytest.approx(probability, abs=1e-13)
            assert density == pytest.approx(weights @ norm.pdf((value-loc)/sigma)/sigma, abs=1e-13)
            np.testing.assert_allclose((value, density), quantile_density(probability, loc, weights, sigma, native=False), atol=1e-13)


def test_summary_sampling_errors_use_the_correct_statistic():
    e, a, o, prep = inputs()
    model = VariablePreparationModel([e], [a], [o], [prep], Config(outcome_contrast_sd=0))
    par = model.parameters(model.programs[0], np.zeros(model.layout.size))
    n, sigma = 100, par['sigma']
    _, mean_sd = model.population_summary(par, 'preparation_start', 'initial_decision', 'population_mean', n)
    _, median_sd = model.population_summary(par, 'preparation_start', 'initial_decision', 'population_median', n)
    assert mean_sd == pytest.approx(math.sqrt(math.log1p(math.expm1(sigma*sigma)/n)))
    assert median_sd == pytest.approx(sigma*math.sqrt(math.pi/(2*n)))
    assert mean_sd != pytest.approx(median_sd)


def test_summary_and_case_likelihood_preserve_native_reference_and_location_ridge():
    e, a, o, prep = inputs()
    e['measurements'].append(measurement(None, scope='process', value=28., case=None, statistic='median', ident='population'))
    a['measurements'].append(audit_row('population', start_event='first_submission',
        statistic_interpretation='population_median', population_scope='all_cases', reporting_sample='administrative'))
    cfg = Config(selection_sd=1.5)
    model = VariablePreparationModel([e], [a], [o], [prep], cfg)
    oracle = VariablePreparationModel([e], [a], [o], [prep], replace(cfg, accelerate=False))
    rng = np.random.default_rng(771)
    for z in rng.normal(size=(8, model.layout.size)):
        initial = model.log_likelihood(z)
        assert initial == pytest.approx(oracle.log_likelihood(z), abs=1e-9)
        moved = model.source_location_move(z, rng)
        assert model.log_likelihood(moved) == pytest.approx(initial, abs=1e-9)
        z[model.programs[0]['case_fraction_indices'][0]] += 1
        assert model.log_likelihood(z) == pytest.approx(oracle.log_likelihood(z), abs=1e-9)


def test_saved_configuration_and_precision_check_cover_both_integrals():
    e, a, o, prep = inputs()
    cfg = saved_config(asdict(Config()))
    assert isinstance(make_model([e], [a], cfg, [o], [prep]), VariablePreparationModel)
    assert finer_config(cfg).quadrature == 2*cfg.quadrature
    assert finer_config(cfg).fraction_quadrature == 2*cfg.fraction_quadrature
