#!/usr/bin/env python3
"""Held-out scoring against the frozen baselines, and the forum reporting offset.

Two jobs, both specified before any fit in `estimands_frozen_v1/v2.json`:

1. Score the fitted authority model on the two frozen held-out splits against
   baseline B1, the raw cell median, and baseline B2, two-way fixed effects.
   The metric is the 90 percent interval score, lower better, with coverage.

2. Estimate E4, the reporting offset, from forum reports against the
   administrative panel. On the log scale a single case report is unbiased for
   the log median when case durations are symmetric in logs, so

       log(forum business days) = log(panel median) + delta + noise
       noise ~ N(0, omega^2)

   identifies delta without knowing the case spread omega, which is estimated
   alongside. delta is reported in percent. Its whole credibility rests on the
   calendar-to-business conversion recorded in the forum build, which is an
   assumption, so the offset is also reported with that conversion removed.

    python3 -m pipeline.procbench.solar_panel.score_and_offset
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.procbench.solar_panel.fit_hierarchy import (  # noqa: E402
    DENOM_FLOOR, build_design, load_cells, rhat_ess)

OUT = ROOT / 'runs/solar_panel_20260920'
CALENDAR_TO_BUSINESS = 5.0 / 7.0


def interval_score(lower, upper, actual, alpha=0.10):
    """Standard proper interval score for a central (1-alpha) interval."""
    width = upper - lower
    penalty = (2 / alpha) * (lower - actual) if actual < lower else 0.0
    penalty += (2 / alpha) * (actual - upper) if actual > upper else 0.0
    return width + penalty


def predict_model(draws, names, authorities, rows):
    """Posterior predictive log-median for each held-out cell."""
    index = {a: i for i, a in enumerate(authorities)}
    design, dnames, _, exposure, _ = build_design(rows)
    # Align the held-out design to the training coefficient names.
    cols = []
    for n in names:
        cols.append(dnames.index(n) if n in dnames else None)
    beta = draws['beta']
    out = np.zeros((beta.shape[0], len(rows)))
    for j, n in enumerate(names):
        if cols[j] is None:
            continue
        out += np.outer(beta[:, j], design[:, cols[j]])
    for i, r in enumerate(rows):
        k = index.get(r['authority'])
        if k is not None:
            out[:, i] += draws['a'][:, k]
    sigma = draws['sigma']
    phases = sorted({r['phase'] for r in rows})
    noise = np.zeros_like(out)
    for i, r in enumerate(rows):
        j = phases.index(r['phase']) if r['phase'] in phases else 0
        v = sigma[:, min(j, sigma.shape[1] - 1)] ** 2 + draws['kappa'] ** 2 / max(r['installs'], DENOM_FLOOR)
        noise[:, i] = np.sqrt(v)
    rng = np.random.default_rng(7)
    return out + noise * rng.normal(size=out.shape)


def baseline_raw(train, rows):
    """B1: the raw median of training cells sharing phase, size, technology, year."""
    pools = defaultdict(list)
    for r in train:
        if r['value'] > 0:
            pools[(r['phase'], r['size'], r['tech'], r['year'])].append(math.log(r['value']))
            pools[(r['phase'],)].append(math.log(r['value']))
    out = []
    for r in rows:
        pool = pools.get((r['phase'], r['size'], r['tech'], r['year'])) or pools.get((r['phase'],))
        arr = np.asarray(pool)
        out.append((float(np.median(arr)), float(np.quantile(arr, .05)), float(np.quantile(arr, .95))))
    return out


def baseline_fixed_effects(train, rows):
    """B2: least squares with authority and year fixed effects, no pooling."""
    design, names, levels, _, _ = build_design(train)
    auths = sorted({r['authority'] for r in train})
    aidx = {a: i for i, a in enumerate(auths)}
    extra = np.zeros((len(train), len(auths)))
    for i, r in enumerate(train):
        extra[i, aidx[r['authority']]] = 1.0
    X = np.hstack([design, extra])
    y = np.array([math.log(max(r['value'], 0.5)) for r in train])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    s = float(np.std(resid, ddof=1))
    d2, n2, _, _, _ = build_design(rows, levels)
    out = []
    for i, r in enumerate(rows):
        row = np.zeros(X.shape[1])
        for j, n in enumerate(names):
            if n in n2:
                row[j] = d2[i, n2.index(n)]
        k = aidx.get(r['authority'])
        if k is not None:
            row[len(names) + k] = 1.0
        mu = float(row @ coef)
        out.append((mu, mu - 1.645 * s, mu + 1.645 * s))
    return out


def score(rows, predictions, label):
    actual = np.array([math.log(max(r['value'], 0.5)) for r in rows])
    lo = np.array([p[1] for p in predictions])
    hi = np.array([p[2] for p in predictions])
    med = np.array([p[0] for p in predictions])
    scores = np.array([interval_score(lo[i], hi[i], actual[i]) for i in range(len(rows))])
    return dict(name=label, cells=len(rows), interval_score=float(np.mean(scores)),
                coverage=float(np.mean((actual >= lo) & (actual <= hi))),
                median_absolute_log_error=float(np.median(np.abs(med - actual))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--panel', default=str(OUT / 'panel_v1.csv'))
    ap.add_argument('--fit', default=str(OUT / 'fit_primary.json'))
    ap.add_argument('--draws', default=str(OUT / 'draws_primary.npz'))
    ap.add_argument('--forum', default=str(OUT / 'forum_v1.json'))
    ap.add_argument('--out', default=str(OUT / 'score_and_offset_v1.json'))
    args = ap.parse_args(argv)

    panel = pathlib.Path(args.panel)
    fitted = json.loads(pathlib.Path(args.fit).read_text())
    z = np.load(args.draws, allow_pickle=True)
    draws = dict(beta=z['beta'], a=z['a'], sigma=z['sigma'], kappa=z['kappa'])
    names = [str(x) for x in z['names']]
    authorities = [str(x) for x in z['authorities']]

    train = load_cells(panel)
    everything = load_cells(panel, holdout=True)
    split_a = [r for r in everything if r['holdout_authority'] and not r['holdout_year']]
    split_b = [r for r in everything if r['holdout_year'] and not r['holdout_authority']]

    report = dict(schema_version='solar-panel-score/1', stage='G-partial',
                  estimands='runs/solar_panel_20260920/estimands_frozen_v2.json',
                  training_cells=len(train), splits={})
    for label, rows in (('split_A_held_out_authorities', split_a),
                        ('split_B_forward_year_2022', split_b)):
        if not rows:
            continue
        pred = predict_model(draws, names, authorities, rows)
        model = score(rows, [(float(np.median(pred[:, i])), float(np.quantile(pred[:, i], .05)),
                              float(np.quantile(pred[:, i], .95))) for i in range(len(rows))],
                      'hierarchical_model')
        b1 = score(rows, baseline_raw(train, rows), 'B1_raw_cell_median')
        b2 = score(rows, baseline_fixed_effects(train, rows), 'B2_two_way_fixed_effects')
        beats = model['interval_score'] < b1['interval_score'] and model['interval_score'] < b2['interval_score']
        report['splits'][label] = dict(
            model=model, B1=b1, B2=b2,
            model_beats_both_baselines=bool(beats),
            coverage_in_band=bool(0.85 <= model['coverage'] <= 0.95),
            note=('Split A holds out whole authorities, so the model has no authority effect for '
                  'them and falls back to the population level; that is the intended test.'
                  if label.startswith('split_A') else
                  'Split B holds out 2022, the last year in the elasticity window.'))

    # ---- E4, the forum reporting offset --------------------------------
    forum = json.loads(pathlib.Path(args.forum).read_text())
    usable = [r for r in forum['rows'] if r['usable_for_offset'] and r['in_panel_years']
              and r['entity_level'] == 'utility']
    cells = defaultdict(list)
    with panel.open(encoding='utf-8') as handle:
        for r in csv.DictReader(handle):
            if r['present'] == 'true' and r['phase_level'] == 'utility':
                try:
                    v = float(r['median_business_days'])
                except (TypeError, ValueError):
                    continue
                if v > 0:
                    cells[(r['owner_name'], r['phase'], r['year'])].append(math.log(v))
                    cells[(r['owner_name'], r['phase'])].append(math.log(v))
                    cells[(r['phase'],)].append(math.log(v))
    paired, unmatched = [], 0
    for r in usable:
        key = (r['named_utility'], r['phase'], str(r['case_year']))
        pool = cells.get(key) or cells.get((r['named_utility'], r['phase'])) or cells.get((r['phase'],))
        if not pool or not r['business_days'] or r['business_days'] <= 0:
            unmatched += 1
            continue
        paired.append(dict(id=r['id'], phase=r['phase'], utility=r['named_utility'],
                           right_censored=bool(r.get('right_censored')),
                           year=r['case_year'], forum_business_days=r['business_days'],
                           panel_log_median=float(np.median(pool)), panel_cells=len(pool),
                           matched_on=('utility_phase_year' if cells.get(key) else
                                       'utility_phase' if cells.get((r['named_utility'], r['phase']))
                                       else 'phase_only'),
                           log_difference=math.log(r['business_days']) - float(np.median(pool))))
    if paired:
        d = np.array([p['log_difference'] for p in paired])
        cens = np.array([p['right_censored'] for p in paired])
        n = len(d)
        # Grid posterior over (delta, omega). Exact for this sample size and it
        # handles the right-censored rows properly: a case still in progress
        # contributes the probability that its true difference EXCEEDS the bound,
        # not the bound itself. Dropping them instead biases delta downward,
        # because a case still running is by definition one of the slow ones.
        from scipy.stats import norm as _norm
        grid_d = np.linspace(-1.5, 1.5, 601)
        grid_o = np.linspace(0.05, 2.5, 246)
        logpost = np.zeros((len(grid_d), len(grid_o)))
        for i, dd in enumerate(grid_d):
            for j, oo in enumerate(grid_o):
                ll = np.sum(_norm.logpdf(d[~cens], dd, oo))
                if cens.any():
                    ll += np.sum(_norm.logsf(d[cens], dd, oo))
                logpost[i, j] = ll - 0.5 * (dd / 1.0) ** 2 - math.log(oo)
        w = np.exp(logpost - logpost.max())
        w /= w.sum()
        margin_d = w.sum(axis=1)
        cdf = np.cumsum(margin_d)
        post_mean = float(grid_d[np.searchsorted(cdf, 0.5)])
        lo = float(grid_d[np.searchsorted(cdf, 0.05)])
        hi = float(grid_d[np.searchsorted(cdf, 0.95)])
        omega = float(grid_o[int(np.argmax(w.sum(axis=0)))])
        se = omega / math.sqrt(max(n - cens.sum(), 1))
        # The same estimator with the censored rows dropped, to size the effect
        # of the defect this fixes.
        dropped = d[~cens]
        lp2 = np.array([[np.sum(_norm.logpdf(dropped, dd, oo)) - 0.5 * dd ** 2 - math.log(oo)
                         for oo in grid_o] for dd in grid_d])
        w2 = np.exp(lp2 - lp2.max()); w2 /= w2.sum()
        c2 = np.cumsum(w2.sum(axis=1))
        naive = float(grid_d[np.searchsorted(c2, 0.5)])
        raw_units = post_mean - math.log(CALENDAR_TO_BUSINESS)
        report['E4_reporting_offset'] = dict(
            paired_reports=n, unmatched=unmatched,
            by_phase=dict((p, sum(1 for x in paired if x['phase'] == p)) for p in {x['phase'] for x in paired}),
            by_utility=dict((u, sum(1 for x in paired if x['utility'] == u)) for u in {x['utility'] for x in paired}),
            matched_on=dict((m, sum(1 for x in paired if x['matched_on'] == m)) for m in {x['matched_on'] for x in paired}),
            offset_log=post_mean, offset_percent=100 * (math.exp(post_mean) - 1),
            ci90_percent=[100 * (math.exp(lo) - 1), 100 * (math.exp(hi) - 1)],
            case_spread_omega_log=omega, standard_error_log=se,
            right_censored_reports=int(cens.sum()),
            offset_percent_if_censored_rows_were_dropped=100 * (math.exp(naive) - 1),
            censoring_note=('Reports still in progress enter as right-censored, contributing the '
                            'probability that the true duration exceeds the stated bound. Dropping '
                            'them removes the slow cases and biases the offset downward; the '
                            'figure that dropping would have produced is given above.'),
            offset_percent_without_the_calendar_conversion=100 * (math.exp(raw_units) - 1),
            conversion_warning=('The offset is computed on forum values converted from calendar to '
                                'business days at five sevenths. Without that conversion the same '
                                'data would show an offset inflated by about 40 percent, which is '
                                'the same order as the estimate itself. The conversion is an '
                                'assumption with no holiday calendar behind it.'),
            interpretation=('Positive means applicants report longer than the administrative panel '
                            'records for the same utility, phase and year. This is a reporting '
                            'offset under forum selection, not a measurement of bias in either '
                            'source alone.'),
            scale_caveat='Rests on %d paired reports, concentrated in one utility.' % n,
            pairs=paired)
    else:
        report['E4_reporting_offset'] = dict(paired_reports=0, unmatched=unmatched,
                                             status='no forum report could be paired')

    pathlib.Path(args.out).write_text(json.dumps(report, indent=1))
    for label, row in report['splits'].items():
        print('%s (%d cells)' % (label, row['model']['cells']))
        for key in ('model', 'B1', 'B2'):
            s = row[key]
            print('   %-28s interval score %7.3f  coverage %.2f  median |log err| %.3f'
                  % (s['name'], s['interval_score'], s['coverage'], s['median_absolute_log_error']))
        print('   beats both baselines: %s | coverage in band: %s'
              % (row['model_beats_both_baselines'], row['coverage_in_band']))
    e4 = report['E4_reporting_offset']
    if e4.get('paired_reports'):
        print('\nE4 reporting offset: %+.0f%% [%.0f, %.0f] on %d paired reports'
              % (e4['offset_percent'], e4['ci90_percent'][0], e4['ci90_percent'][1], e4['paired_reports']))
        print('   without the calendar-to-business conversion it would read %+.0f%%'
              % e4['offset_percent_without_the_calendar_conversion'])
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
