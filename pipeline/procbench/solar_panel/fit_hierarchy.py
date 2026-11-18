#!/usr/bin/env python3
"""Stage B: the crossed hierarchical model for solar permitting phase times.

Deliberately NOT the V6 trace model. There are no cases, no repeat blocks and no
route uncertainty in this panel, so the trace machinery would add nothing; see
`docs/2026-09-20-solar-leg-plan-for-claude.md` stage B.

Model, on the natural log of a cell's median business days:

    y[c] = m + a[i] + phase[j] + size + tech + year[t] + (b + e[i]) * x[c] + noise
    x[c] = log2(installs[c] / 10), the exposure, zero at the source's own
           minimum of ten projects
    a[i] ~ N(0, tau_a^2)    authority level
    e[i] ~ N(0, tau_e^2)    authority deviation from the mean load elasticity b
    noise ~ N(0, sigma[j]^2 + kappa^2 / n[c])

The noise splits deliberately. `sigma[j]` is genuine cell-to-cell heterogeneity
the design does not explain. `kappa^2 / n[c]` is the sampling error of a median
over n projects, and n is unknown but the source guarantees at least ten, so
n[c] = max(10, installs[c]) makes the sampling term an optimistic lower bound on
variance. The `--floor-n` sensitivity sets n[c] = 10 everywhere instead.

Same-day cells are recorded by the source as zero, meaning approval on the day of
submission. They enter as LEFT-CENSORED at log(1) business day, not as a dropped
row and not as a small positive number. `--same-day-half` censors at log(0.5).

Sampling is a blocked Gibbs sampler with data augmentation for the censored
cells. Conditional on the variances the location parameters are jointly Gaussian;
authorities are conditionally independent given the globals, so each authority's
intercept and slope are drawn from a two-by-two conditional. Variance parameters
are slice-sampled on the log scale under half-normal priors.

    python3 -m pipeline.procbench.solar_panel.fit_hierarchy --draws 2000
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
from collections import defaultdict

import numpy as np
from scipy.special import log_ndtr, ndtri
from scipy.stats import truncnorm

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'runs/solar_panel_20260920'
AUTHORITY_PHASES = ('permit_review', 'inspection')
DENOM_FLOOR = 10.0


def load_cells(panel_path, window_only=True, holdout=False):
    """Authority-level present cells with a usable value or a censored zero."""
    rows = []
    with panel_path.open(encoding='utf-8') as handle:
        for r in csv.DictReader(handle):
            if r['present'] != 'true' or r['phase'] not in AUTHORITY_PHASES:
                continue
            if r['owner_kind'] != 'ahj':
                continue
            if window_only and r['in_elasticity_window'] != 'True':
                continue
            if not holdout and (r['holdout_authority'] == 'True' or r['holdout_forward_year'] == 'True'):
                continue
            try:
                value = float(r['median_business_days'])
            except (TypeError, ValueError):
                continue
            if value < 0:
                continue
            rows.append(dict(
                authority=r['stable_owner_id'], phase=r['phase'], year=r['year'],
                size=r['size_class'], tech=r['technology'], value=value,
                installs=float(r['installs_same_cell'] or 0.0),
                censored=(value == 0.0),
                holdout_authority=(r['holdout_authority'] == 'True'),
                holdout_year=(r['holdout_forward_year'] == 'True'),
                in_window=(r['in_elasticity_window'] == 'True')))
    return rows


def build_design(rows, levels=None):
    """Fixed block: intercept, phase, size, technology, year, mean elasticity."""
    if levels is None:
        levels = dict(phase=sorted({r['phase'] for r in rows})[1:],
                      size=sorted({r['size'] for r in rows})[1:],
                      tech=sorted({r['tech'] for r in rows})[1:],
                      year=sorted({r['year'] for r in rows})[1:])
    names = ['intercept']
    names += ['phase:' + v for v in levels['phase']]
    names += ['size:' + v for v in levels['size']]
    names += ['tech:' + v for v in levels['tech']]
    names += ['year:' + v for v in levels['year']]
    names += ['elasticity_log2_installs']
    index = {n: i for i, n in enumerate(names)}
    design = np.zeros((len(rows), len(names)))
    design[:, 0] = 1.0
    # Centred so the intercept is the typical-load cell rather than the
    # ten-project floor, which decorrelates the intercept from the slope.
    raw = np.array([math.log2(max(r['installs'], DENOM_FLOOR) / DENOM_FLOOR) for r in rows])
    exposure = raw - raw.mean()
    for i, r in enumerate(rows):
        for key, value in (('phase', r['phase']), ('size', r['size']),
                           ('tech', r['tech']), ('year', r['year'])):
            column = index.get(key + ':' + value)
            if column is not None:
                design[i, column] = 1.0
        design[i, index['elasticity_log2_installs']] = exposure[i]
    return design, names, levels, exposure, float(raw.mean())


def slice_log_scale(current, logpost, rng, width=0.6, steps=12):
    """Univariate slice sampler on log of a positive scale parameter."""
    x0 = math.log(current)
    y = logpost(current) + math.log(max(rng.random(), 1e-300))
    left, right = x0 - width * rng.random(), 0.0
    right = left + width
    for _ in range(steps):
        if logpost(math.exp(left)) <= y:
            break
        left -= width
    for _ in range(steps):
        if logpost(math.exp(right)) <= y:
            break
        right += width
    for _ in range(40):
        xp = left + (right - left) * rng.random()
        if logpost(math.exp(xp)) > y:
            return math.exp(xp)
        if xp < x0:
            left = xp
        else:
            right = xp
    return current


def fit(rows, draws=2000, warmup=1000, seed=20260920, same_day_cap=1.0, floor_n=False,
        random_slope=True, progress=None):
    rng = np.random.default_rng(seed)
    design, names, levels, exposure, exposure_centre = build_design(rows)
    n_obs, n_fixed = design.shape
    authorities = sorted({r['authority'] for r in rows})
    auth_index = {a: i for i, a in enumerate(authorities)}
    a_of = np.array([auth_index[r['authority']] for r in rows])
    phase_list = sorted({r['phase'] for r in rows})
    p_of = np.array([phase_list.index(r['phase']) for r in rows])

    y = np.array([math.log(r['value']) if not r['censored'] else math.log(same_day_cap) - 0.5
                  for r in rows])
    censored = np.array([r['censored'] for r in rows])
    cap = math.log(same_day_cap)
    n_eff = np.array([DENOM_FLOOR if floor_n else max(r['installs'], DENOM_FLOOR) for r in rows])

    beta = np.zeros(n_fixed)
    beta[0] = math.log(10.0)
    a = np.zeros(len(authorities))
    e = np.zeros(len(authorities))
    tau_a, tau_e, kappa = 0.5, 0.2, 2.0
    sigma = np.full(len(phase_list), 0.5)

    # Per-authority row blocks, so each authority's 2x2 conditional is cheap.
    blocks = defaultdict(list)
    for i, r in enumerate(rows):
        blocks[auth_index[r['authority']]].append(i)
    blocks = {k: np.array(v) for k, v in blocks.items()}

    intercept_at = names.index('intercept')
    slope_at = names.index('elasticity_log2_installs')

    def ridge_move(beta, effects, column, tau, prior_sd, rng, scale=0.15):
        """Shift mass between a global coefficient and its random effects.

        The likelihood is invariant: adding d to the global term and subtracting
        d from every effect leaves every fitted value unchanged. Only the priors
        change, so the Metropolis ratio is available in closed form. This is the
        same device V6 uses for its location/source ridge, and without it the
        chain wanders along that direction instead of mixing across it.
        """
        d = scale * rng.normal()
        cur = -0.5 * np.sum(effects ** 2) / tau ** 2 - 0.5 * (beta[column] / prior_sd) ** 2
        new_effects = effects - d
        new = -0.5 * np.sum(new_effects ** 2) / tau ** 2 - 0.5 * ((beta[column] + d) / prior_sd) ** 2
        if math.log(max(rng.random(), 1e-300)) < new - cur:
            beta[column] += d
            return new_effects, True
        return effects, False

    keep = dict(beta=[], tau_a=[], tau_e=[], kappa=[], sigma=[], a=[], e=[])
    ridge_accept = [0, 0]
    for it in range(warmup + draws):
        var = sigma[p_of] ** 2 + kappa ** 2 / n_eff
        mu = design @ beta + a[a_of] + e[a_of] * exposure

        # 1. latent values for the left-censored same-day cells
        if censored.any():
            sd = np.sqrt(var[censored])
            upper = (cap - mu[censored]) / sd
            y[censored] = mu[censored] + sd * truncnorm.rvs(
                -np.inf, upper, random_state=rng, size=int(censored.sum()))

        # 2. fixed block, conditional Gaussian
        resid = y - a[a_of] - e[a_of] * exposure
        weight = 1.0 / var
        precision = (design * weight[:, None]).T @ design + np.eye(n_fixed) / 4.0
        rhs = (design * weight[:, None]).T @ resid
        chol = np.linalg.cholesky(precision)
        mean = np.linalg.solve(chol.T, np.linalg.solve(chol, rhs))
        beta = mean + np.linalg.solve(chol.T, rng.normal(size=n_fixed))

        # 3. authority intercept and slope, one 2x2 solve each
        base = y - design @ beta
        for k, idx in blocks.items():
            w = 1.0 / var[idx]
            z = np.column_stack((np.ones(len(idx)), exposure[idx]))
            if random_slope:
                prec = (z * w[:, None]).T @ z + np.diag([1.0 / tau_a ** 2, 1.0 / tau_e ** 2])
                r_ = (z * w[:, None]).T @ base[idx]
                c_ = np.linalg.cholesky(prec)
                m_ = np.linalg.solve(c_.T, np.linalg.solve(c_, r_))
                a[k], e[k] = m_ + np.linalg.solve(c_.T, rng.normal(size=2))
            else:
                prec_ = float(np.sum(w)) + 1.0 / tau_a ** 2
                mean_ = float(np.sum(w * base[idx])) / prec_
                a[k] = mean_ + rng.normal() / math.sqrt(prec_)

        # 3b. break the global/random-effect ridge, twice per sweep
        for _ in range(2):
            a, ok = ridge_move(beta, a, intercept_at, tau_a, 2.0, rng)
            ridge_accept[0] += ok
            if random_slope:
                e, ok = ridge_move(beta, e, slope_at, tau_e, 0.5, rng, scale=0.05)
                ridge_accept[1] += ok

        # 4. hierarchy scales, half-normal priors, slice sampled
        def tau_post(values, prior_sd):
            def f(t):
                if t <= 0:
                    return -np.inf
                return (-0.5 * np.sum(values ** 2) / t ** 2 - len(values) * math.log(t)
                        - 0.5 * (t / prior_sd) ** 2)
            return f
        tau_a = slice_log_scale(tau_a, tau_post(a, 1.0), rng)
        if random_slope:
            tau_e = slice_log_scale(tau_e, tau_post(e, 0.5), rng)

        # 5. residual scales: per-phase heterogeneity and the shared sampling term
        mu = design @ beta + a[a_of] + e[a_of] * exposure
        r2 = (y - mu) ** 2

        def make_sigma_post(j):
            mask = p_of == j
            def f(s):
                if s <= 0:
                    return -np.inf
                v = s ** 2 + kappa ** 2 / n_eff[mask]
                return -0.5 * np.sum(r2[mask] / v + np.log(v)) - 0.5 * (s / 1.0) ** 2
            return f
        for j in range(len(phase_list)):
            sigma[j] = slice_log_scale(sigma[j], make_sigma_post(j), rng)

        def kappa_post(k_):
            if k_ <= 0:
                return -np.inf
            v = sigma[p_of] ** 2 + k_ ** 2 / n_eff
            return -0.5 * np.sum(r2 / v + np.log(v)) - 0.5 * (k_ / 3.0) ** 2
        kappa = slice_log_scale(kappa, kappa_post, rng)

        if it >= warmup:
            keep['beta'].append(beta.copy())
            keep['a'].append(a.copy())
            keep['e'].append(e.copy())
            keep['tau_a'].append(tau_a)
            keep['tau_e'].append(tau_e)
            keep['kappa'].append(kappa)
            keep['sigma'].append(sigma.copy())
        if progress and (it + 1) % 200 == 0:
            progress(it + 1, warmup + draws)
    return dict(names=names, levels=levels, authorities=authorities, phases=phase_list,
                ridge_acceptance=[r / (2 * (warmup + draws)) for r in ridge_accept],
                draws={k: np.asarray(v) for k, v in keep.items()},
                config=dict(draws=draws, warmup=warmup, seed=seed, same_day_cap=same_day_cap,
                            floor_n=floor_n, observations=n_obs,
                            exposure_centred_at_log2_installs_over_10=exposure_centre,
                            random_slope=random_slope,
                            censored=int(censored.sum()), authorities=len(authorities)))


def rhat_ess(chain):
    """Rank-free R-hat and bulk ESS for one scalar.

    Accepts either a single chain, split in two, or a chains-by-draws array, in
    which case the split is across the real chains.
    """
    chain = np.asarray(chain, dtype=float)
    if chain.ndim == 2:
        halves = chain
        n = chain.size
    else:
        n = len(chain) // 2 * 2
        halves = chain[:n].reshape(2, -1)
    m, s = halves.mean(axis=1), halves.var(axis=1, ddof=1)
    w = s.mean()
    b = halves.shape[1] * m.var(ddof=1)
    var = ((halves.shape[1] - 1) * w + b) / halves.shape[1]
    rhat = math.sqrt(var / w) if w > 0 else float('nan')
    flat = halves.reshape(-1)
    centred = flat - flat.mean()
    denom = np.sum(centred ** 2)
    if denom <= 0:
        return rhat, 0.0
    acf = np.correlate(centred, centred, 'full')[len(centred) - 1:] / denom
    total, k = 0.0, 1
    while k + 1 < len(acf) and acf[k] + acf[k + 1] > 0:
        total += acf[k] + acf[k + 1]
        k += 2
    return rhat, float(n / (1 + 2 * total))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--panel', default=str(OUT / 'panel_v1.csv'))
    ap.add_argument('--draws', type=int, default=1500)
    ap.add_argument('--warmup', type=int, default=750)
    ap.add_argument('--seed', type=int, default=20260920)
    ap.add_argument('--chains', type=int, default=4)
    ap.add_argument('--no-random-slope', action='store_true',
                    help='common load elasticity only; use when tau_e collapses to the boundary')
    ap.add_argument('--same-day-half', action='store_true', help='censor at log(0.5) instead of log(1)')
    ap.add_argument('--floor-n', action='store_true', help='set every denominator to the source floor of 10')
    ap.add_argument('--label', default='primary')
    ap.add_argument('--out', default=str(OUT))
    args = ap.parse_args(argv)

    panel = pathlib.Path(args.panel)
    rows = load_cells(panel)
    print('training cells %d, authorities %d, censored %d'
          % (len(rows), len({r['authority'] for r in rows}), sum(r['censored'] for r in rows)))
    runs = []
    for c in range(args.chains):
        print('chain %d of %d' % (c + 1, args.chains), flush=True)
        runs.append(fit(rows, draws=args.draws, warmup=args.warmup, seed=args.seed + 104729 * c,
                        same_day_cap=0.5 if args.same_day_half else 1.0, floor_n=args.floor_n,
                        random_slope=not args.no_random_slope,
                        progress=lambda i, n: print('  %d/%d' % (i, n), flush=True)))
    result = runs[0]
    # chains-by-draws for diagnostics, pooled draws for summaries
    chains = {k: np.stack([r['draws'][k] for r in runs]) for k in runs[0]['draws']}
    draws = {k: np.concatenate([r['draws'][k] for r in runs]) for k in runs[0]['draws']}
    result['config']['chains'] = args.chains
    summary = {}
    for j, name in enumerate(result['names']):
        col = draws['beta'][:, j]
        r, ess = rhat_ess(chains['beta'][:, :, j])
        summary[name] = dict(median=float(np.median(col)),
                             ci90=[float(np.quantile(col, .05)), float(np.quantile(col, .95))],
                             rhat=round(r, 4), ess_bulk=round(ess, 1))
    scale_keys = [('tau_a', 'half-normal(1.0)'), ('kappa', 'half-normal(3.0)')]
    if not args.no_random_slope:
        scale_keys.insert(1, ('tau_e', 'half-normal(0.5)'))
    for key, prior in scale_keys:
        col = draws[key]
        r, ess = rhat_ess(chains[key])
        summary[key] = dict(median=float(np.median(col)),
                            ci90=[float(np.quantile(col, .05)), float(np.quantile(col, .95))],
                            rhat=round(r, 4), ess_bulk=round(ess, 1), prior=prior)
    for j, phase in enumerate(result['phases']):
        col = draws['sigma'][:, j]
        r, ess = rhat_ess(chains['sigma'][:, :, j])
        summary['sigma:' + phase] = dict(median=float(np.median(col)),
                                         ci90=[float(np.quantile(col, .05)), float(np.quantile(col, .95))],
                                         rhat=round(r, 4), ess_bulk=round(ess, 1))

    elasticity = draws['beta'][:, result['names'].index('elasticity_log2_installs')]
    per_authority = elasticity[:, None] + draws['e']
    report = dict(
        schema_version='solar-panel-fit/1', stage='B', label=args.label,
        plan='docs/2026-09-20-solar-leg-plan-for-claude.md',
        estimands='runs/solar_panel_20260920/estimands_frozen_v2.json',
        model=('crossed hierarchical lognormal on log median business days; authority intercept '
               'and authority-specific load slope; per-phase heterogeneity plus a shared '
               'median-sampling term scaled by the denominator; same-day cells left-censored'),
        is_v6_trace_model=False,
        panel=dict(path=str(panel.relative_to(ROOT)), sha256=hashlib.sha256(panel.read_bytes()).hexdigest()),
        config=result['config'], parameters=summary,
        elasticity=dict(
            mean_per_doubling_log=float(np.median(elasticity)),
            mean_per_doubling_percent=float(100 * (math.exp(np.median(elasticity)) - 1)),
            ci90_percent=[float(100 * (math.exp(np.quantile(elasticity, .05)) - 1)),
                          float(100 * (math.exp(np.quantile(elasticity, .95)) - 1))],
            spread_tau_e=(None if args.no_random_slope else float(np.median(draws['tau_e']))),
            authority_specific_slopes=not args.no_random_slope,
            authority_slope_p10_p90_percent=(None if args.no_random_slope else [
                float(100 * (math.exp(np.quantile(np.median(per_authority, axis=0), .1)) - 1)),
                float(100 * (math.exp(np.quantile(np.median(per_authority, axis=0), .9)) - 1))]),
            interpretation=('Change in an authority\'s median phase time per doubling of annual '
                            'installations in the same cell. Exposure is treated as exogenous: it '
                            'is driven by statewide tariff and credit policy, not by one '
                            'authority\'s speed. That is an assumption, stated here.')),
        authority_spread=dict(
            tau_a_log=float(np.median(draws['tau_a'])),
            ratio_p90_over_p10=float(math.exp(2 * 1.2816 * np.median(draws['tau_a']))),
            interpretation='Between-authority spread in phase time after year, phase and stratum.'),
        convergence=dict(
            max_rhat=max(v['rhat'] for v in summary.values() if v.get('rhat') == v.get('rhat')),
            min_ess=min(v['ess_bulk'] for v in summary.values()),
            gate='rhat <= 1.01 and ess_bulk >= 400 on every reported parameter',
            passes=bool(max(v['rhat'] for v in summary.values()) <= 1.01
                        and min(v['ess_bulk'] for v in summary.values()) >= 400)),
        declarations=dict(reads_benchmark_truth=False, network_used=False, model_calls=0,
                          held_out_cells_excluded_from_training=True))
    target = pathlib.Path(args.out) / ('fit_%s.json' % args.label)
    target.write_text(json.dumps(report, indent=1))
    np.savez_compressed(pathlib.Path(args.out) / ('draws_%s.npz' % args.label),
                        beta=draws['beta'], a=draws['a'], e=draws['e'], tau_a=draws['tau_a'],
                        tau_e=draws['tau_e'], kappa=draws['kappa'], sigma=draws['sigma'],
                        authorities=np.array(result['authorities']), names=np.array(result['names']))
    print('\nelasticity per doubling: %+.1f%% [%.1f, %.1f]'
          % (report['elasticity']['mean_per_doubling_percent'], *report['elasticity']['ci90_percent']))
    print('between-authority spread: tau_a %.3f, p90/p10 ratio %.2fx'
          % (report['authority_spread']['tau_a_log'], report['authority_spread']['ratio_p90_over_p10']))
    print('convergence: max rhat %.4f, min ESS %.0f -> passes=%s'
          % (report['convergence']['max_rhat'], report['convergence']['min_ess'],
             report['convergence']['passes']))
    print('wrote', target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
