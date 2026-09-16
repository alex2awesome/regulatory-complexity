from dataclasses import replace

import numpy as np
import pytest

from pipeline.procbench.bayes_repeat_timing import Config, fit_repeat_timing, refinement_check


def test_repeat_information_flows_back_to_shared_agency_task_duration():
    totals = np.linspace(20, 30, 12)
    cfg = Config(location_points=401, probability_points=201)
    low = fit_repeat_timing(totals, independent_rework_cohort=(2, 100), cfg=cfg)
    high = fit_repeat_timing(totals, independent_rework_cohort=(90, 100), cfg=cfg)
    assert high['agency_mean_cycle_days']['median'] < low['agency_mean_cycle_days']['median']
    assert high['expected_visit_count']['median'] > low['expected_visit_count']['median']
    assert high['posterior_location_rework_correlation'] < 0
    assert high['posterior_mass'].sum() == pytest.approx(1)


def test_direct_agency_task_data_inform_rework_without_treating_duration_as_counts():
    totals = np.linspace(20, 30, 12)
    cfg = Config(location_points=401, probability_points=201)
    quick = fit_repeat_timing(totals, task_cycle_days=np.full(20, 5.), cfg=cfg)
    slow = fit_repeat_timing(totals, task_cycle_days=np.full(20, 14.), cfg=cfg)
    assert quick['any_correction_probability']['median'] > slow['any_correction_probability']['median']
    assert quick['agency_mean_cycle_days']['median'] < slow['agency_mean_cycle_days']['median']


def test_probability_only_data_recover_count_posterior_and_grid_refinement():
    cfg = Config(location_points=401, probability_points=201)
    base = fit_repeat_timing([], independent_rework_cohort=(6, 10), cfg=cfg)
    finer = fit_repeat_timing([], independent_rework_cohort=(6, 10),
                             cfg=replace(cfg, location_points=801, probability_points=401))
    assert base['any_correction_probability']['mean'] == pytest.approx(7/12, abs=1e-5)
    assert refinement_check(base, finer)['acceptable']
    assert abs(base['posterior_location_rework_correlation']) < 1e-12


def test_invalid_cohorts_or_substantial_discarded_repeat_tails_are_rejected():
    with pytest.raises(ValueError, match='integer successes'):
        fit_repeat_timing([20.], independent_rework_cohort=(3.5, 10))
    with pytest.raises(ValueError, match='count tail too large'):
        fit_repeat_timing([20.], cfg=Config(probability_continue=.99))
