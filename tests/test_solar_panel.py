"""Source-free tests for the solar panel leg.

No fixture here reads the real panel, the real ledger or any benchmark truth.
Each test pins a decision that a silent change would turn into a wrong number,
and several pin defects that were actually made and corrected during the work.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline.procbench.solar_panel import build_forum, fit_hierarchy, score_and_offset


# --------------------------------------------------------------------------
# unit conversion: the defect that would have faked a reporting offset
# --------------------------------------------------------------------------

def test_calendar_days_convert_to_fewer_business_days():
    factor, _ = build_forum.TO_BUSINESS_DAYS['calendar_days']
    assert factor == pytest.approx(5.0 / 7.0)
    assert 14 * factor == pytest.approx(10.0)


def test_business_days_are_not_converted():
    factor, note = build_forum.TO_BUSINESS_DAYS['business_days']
    assert factor == 1.0
    assert 'no conversion' in note


def test_every_convertible_unit_is_documented_as_an_assumption():
    for unit, (factor, note) in build_forum.TO_BUSINESS_DAYS.items():
        assert factor > 0
        assert note, 'unit %s has no recorded justification' % unit


def test_a_week_is_five_business_days_not_seven():
    factor, _ = build_forum.TO_BUSINESS_DAYS['weeks']
    assert factor == pytest.approx(5.0)


# --------------------------------------------------------------------------
# phase mapping and entity level
# --------------------------------------------------------------------------

def test_activity_phase_map_is_a_partition():
    seen = set()
    for phase, ids in build_forum.PHASE_ACTIVITIES.items():
        for a in ids:
            assert a not in seen, '%s is claimed by two phases' % a
            seen.add(a)
    assert build_forum.ACTIVITY_PHASE['utility_pto_grant'] == 'final_ix_pto'
    assert build_forum.ACTIVITY_PHASE['ahj_plan_review'] == 'permit_review'


def test_interconnection_phases_belong_to_a_utility_not_an_authority():
    """Assigning utility phases to candidate authorities was a real error."""
    utility_phases = {'pre_install_ix', 'final_ix_pto'}
    authority_phases = set(fit_hierarchy.AUTHORITY_PHASES)
    assert not (utility_phases & authority_phases)
    assert authority_phases == {'permit_review', 'inspection'}


# --------------------------------------------------------------------------
# censoring: the defect that biased the offset
# --------------------------------------------------------------------------

def _offset(differences, censored):
    """Reproduce the grid estimator on a small synthetic sample."""
    from scipy.stats import norm
    d = np.asarray(differences, dtype=float)
    c = np.asarray(censored, dtype=bool)
    grid_d = np.linspace(-1.5, 1.5, 601)
    grid_o = np.linspace(0.05, 2.5, 246)
    logpost = np.zeros((len(grid_d), len(grid_o)))
    for i, dd in enumerate(grid_d):
        for j, oo in enumerate(grid_o):
            ll = np.sum(norm.logpdf(d[~c], dd, oo))
            if c.any():
                ll += np.sum(norm.logsf(d[c], dd, oo))
            logpost[i, j] = ll - 0.5 * dd ** 2 - math.log(oo)
    w = np.exp(logpost - logpost.max())
    w /= w.sum()
    return float(grid_d[np.searchsorted(np.cumsum(w.sum(axis=1)), 0.5)])


def test_dropping_right_censored_reports_biases_the_offset_downward():
    """A still-running case is a slow case; discarding it makes the source look fast."""
    finished = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1]
    censored_at = [0.6, 0.7, 0.8]
    with_censoring = _offset(finished + censored_at, [False] * 6 + [True] * 3)
    dropping = _offset(finished, [False] * 6)
    assert with_censoring > dropping, 'censoring must pull the offset up, not down'


def test_a_censored_report_never_lowers_the_offset_below_its_bound_alone():
    high = _offset([1.0], [True])
    assert high > 0.0


# --------------------------------------------------------------------------
# the interval score, which is the frozen decision metric
# --------------------------------------------------------------------------

def test_interval_score_is_width_when_the_actual_is_inside():
    assert score_and_offset.interval_score(0.0, 2.0, 1.0) == pytest.approx(2.0)


def test_interval_score_penalises_a_miss_in_proportion_to_the_distance():
    inside = score_and_offset.interval_score(0.0, 2.0, 1.0)
    just_outside = score_and_offset.interval_score(0.0, 2.0, 2.5)
    far_outside = score_and_offset.interval_score(0.0, 2.0, 5.0)
    assert inside < just_outside < far_outside


def test_a_narrow_wrong_interval_scores_worse_than_a_wide_right_one():
    narrow_wrong = score_and_offset.interval_score(0.0, 0.1, 3.0)
    wide_right = score_and_offset.interval_score(0.0, 6.0, 3.0)
    assert wide_right < narrow_wrong


# --------------------------------------------------------------------------
# the design matrix and the exposure centring
# --------------------------------------------------------------------------

def _rows(n=40):
    out = []
    for i in range(n):
        out.append(dict(authority='a%d' % (i % 5), phase='permit_review' if i % 2 else 'inspection',
                        year=str(2017 + i % 6), size='0-10kW', tech='PV Only',
                        value=5.0 + i % 7, installs=10.0 * (1 + i % 9), censored=False,
                        holdout_authority=False, holdout_year=False, in_window=True))
    return out


def test_exposure_is_centred_so_the_intercept_is_a_typical_cell():
    _, _, _, exposure, centre = fit_hierarchy.build_design(_rows())
    assert abs(float(np.mean(exposure))) < 1e-9
    assert centre > 0


def test_exposure_is_log2_of_installs_over_the_source_floor():
    rows = _rows(2)
    rows[0]['installs'], rows[1]['installs'] = 10.0, 40.0
    _, _, _, exposure, _ = fit_hierarchy.build_design(rows)
    assert exposure[1] - exposure[0] == pytest.approx(2.0), 'four times ten is two doublings'


def test_installs_below_the_source_floor_are_clamped_not_extrapolated():
    rows = _rows(2)
    rows[0]['installs'], rows[1]['installs'] = 0.0, 10.0
    _, _, _, exposure, _ = fit_hierarchy.build_design(rows)
    assert exposure[0] == pytest.approx(exposure[1])


def test_the_design_names_are_reference_coded_with_one_intercept():
    _, names, _, _, _ = fit_hierarchy.build_design(_rows())
    assert names[0] == 'intercept'
    assert names[-1] == 'elasticity_log2_installs'
    assert sum(1 for n in names if n.startswith('phase:')) == 1, 'two phases, one contrast'


# --------------------------------------------------------------------------
# the sampler recovers a planted signal
# --------------------------------------------------------------------------

def test_sampler_recovers_a_planted_elasticity_and_authority_spread():
    rng = np.random.default_rng(11)
    true_elasticity, true_tau = -0.25, 0.40
    authorities = ['a%02d' % i for i in range(30)]
    effects = {a: rng.normal(0, true_tau) for a in authorities}
    rows = []
    for a in authorities:
        for year in range(2017, 2023):
            for phase in ('permit_review', 'inspection'):
                installs = float(10 * 2 ** rng.integers(0, 5))
                x = math.log2(installs / 10.0)
                mu = math.log(8.0) + effects[a] + true_elasticity * x + (0.3 if phase == 'inspection' else 0.0)
                rows.append(dict(authority=a, phase=phase, year=str(year), size='0-10kW',
                                 tech='PV Only', value=float(math.exp(mu + rng.normal(0, 0.25))),
                                 installs=installs, censored=False, holdout_authority=False,
                                 holdout_year=False, in_window=True))
    result = fit_hierarchy.fit(rows, draws=400, warmup=300, seed=5, random_slope=False)
    beta = result['draws']['beta']
    slope = beta[:, result['names'].index('elasticity_log2_installs')]
    lo, hi = np.quantile(slope, [.05, .95])
    assert lo <= true_elasticity <= hi, 'planted elasticity outside the 90 percent interval'
    tau = float(np.median(result['draws']['tau_a']))
    assert 0.5 * true_tau < tau < 2.0 * true_tau


def test_censored_cells_are_drawn_below_their_cap_not_dropped():
    rng = np.random.default_rng(3)
    rows = []
    for i in range(60):
        same_day = i % 4 == 0
        rows.append(dict(authority='a%d' % (i % 6), phase='permit_review', year=str(2017 + i % 5),
                         size='0-10kW', tech='PV Only',
                         value=0.0 if same_day else float(2 + rng.integers(1, 9)),
                         installs=40.0, censored=same_day, holdout_authority=False,
                         holdout_year=False, in_window=True))
    result = fit_hierarchy.fit(rows, draws=150, warmup=150, seed=9, random_slope=False)
    assert result['config']['censored'] == sum(r['censored'] for r in rows)
    assert result['config']['observations'] == len(rows), 'censored rows must not be dropped'


def test_same_day_convention_is_recorded_in_the_config():
    rows = _rows(20)
    rows[0]['value'], rows[0]['censored'] = 0.0, True
    full = fit_hierarchy.fit(rows, draws=40, warmup=40, seed=1, random_slope=False)
    half = fit_hierarchy.fit(rows, draws=40, warmup=40, seed=1, random_slope=False, same_day_cap=0.5)
    assert full['config']['same_day_cap'] == 1.0
    assert half['config']['same_day_cap'] == 0.5


# --------------------------------------------------------------------------
# convergence diagnostics
# --------------------------------------------------------------------------

def test_rhat_is_near_one_for_agreeing_chains_and_large_for_disagreeing_ones():
    rng = np.random.default_rng(0)
    agree = rng.normal(size=(4, 500))
    rhat_ok, ess_ok = fit_hierarchy.rhat_ess(agree)
    assert rhat_ok < 1.05 and ess_ok > 100
    disagree = agree + np.array([0.0, 5.0, 10.0, 15.0])[:, None]
    rhat_bad, _ = fit_hierarchy.rhat_ess(disagree)
    assert rhat_bad > 1.5


def test_rhat_accepts_a_single_chain_by_splitting_it():
    rng = np.random.default_rng(1)
    rhat, ess = fit_hierarchy.rhat_ess(rng.normal(size=800))
    assert rhat < 1.1 and ess > 50
