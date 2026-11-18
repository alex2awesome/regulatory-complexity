"""Independent adaptive-integral checks of saved whole-case timing likelihoods.

This is a numerical diagnostic, not another fit or accuracy score. It compares
prior-centered Gauss-Hermite integrals with adaptive integration at saved states,
including the worst doubled-resolution states. No benchmark outcomes are read.
"""
import argparse
from datetime import datetime, timezone
import json
import math
import pathlib

import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp
from scipy.stats import norm

from .bayes_outcome_measurement import shifted_selection_normalizer
from .bayes_process_measurement import log_selection_weight
from .infra.manifest import digest, write
from .run_process_measurement import finer_config, make_model, saved_config


def case_integral(model, p, case, par, adaptive=False):
    rows = p['cases'][case]
    has_outcome = 'locations' in par
    locations = par['locations'] if has_outcome else np.array([par['mu']])
    outcome = p.get('outcomes', {}).get(case)
    branches = [0] if outcome == 'approved' or not has_outcome else [1] if outcome == 'denied' else [0, 1]
    selected = any(m['audit']['reporting_sample'] == 'forum_selected' for m in rows)
    pi = par.get('approval_probability', 1.)
    logmix = np.log([pi, 1-pi]) if has_outcome else np.array([0.])
    posting = np.array([0., par['denial_posting']]) if has_outcome else np.array([0.])
    shifts = (locations-par['mu'])/par['sigma']
    normalizers = np.array([shifted_selection_normalizer(s, par['strength'], model.cfg.selection_width)
                            for s in shifts])
    global_normalizer = logsumexp(logmix+posting+normalizers)
    terms, errors = [], []
    for branch in branches:
        def log_joint(nodes):
            base = locations[branch]+par['sigma']*np.asarray(nodes)
            logp = sum(model.observation_probability(m, base, par) for m in rows)
            if selected:
                logp = logp+log_selection_weight(np.asarray(nodes)+shifts[branch], par['strength'], model.cfg.selection_width)
            return logp
        if adaptive:
            # Scale near the mode so absolute integration tolerances do not
            # overwhelm a tiny product of multiple report interval probabilities.
            extent = 20.
            grid = np.linspace(-extent, extent, 201)
            density = log_joint(grid)+norm.logpdf(grid)
            peak = float(density.max())
            points = []
            for i in np.argsort(density)[-4:]:
                lo, hi = grid[max(0, i-1)], grid[min(len(grid)-1, i+1)]
                mode = minimize_scalar(lambda x: -float(log_joint(x)+norm.logpdf(x)),
                                       bounds=(lo, hi), method='bounded', options={'xatol': 1e-10})
                peak = max(peak, -mode.fun)
                points.append(float(mode.x))
            integral, error = quad(lambda x: math.exp(float(log_joint(x)+norm.logpdf(x))-peak),
                -extent, extent, points=sorted(set(points)), epsabs=1e-10, epsrel=1e-8, limit=1000)
            if integral <= 0 or not math.isfinite(integral):
                raise ValueError('Adaptive reference integral failed')
            term = peak+math.log(integral)
            # Every report probability <=1 and the reference selection weight
            # is bounded by 4. This conservative omitted-tail bound is explicit.
            tail_relative = math.exp(math.log(8.)+norm.logsf(extent)-term)
            relative_error = error/integral+tail_relative
            if not math.isfinite(relative_error) or relative_error > 1e-6:
                raise ValueError('Adaptive reference error bound is not sufficiently small')
            errors.append(float(relative_error))
        else:
            term = float(logsumexp(model.log_weights+log_joint(model.nodes)))
        if len(branches) == 1:
            if selected:
                term -= normalizers[branch]
        else:
            term += logmix[branch]+(posting[branch]-global_normalizer if selected else 0.)
        terms.append(term)
    return float(logsumexp(terms)), max(errors, default=0.)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--scan-states', type=int, default=200)
    ap.add_argument('--adaptive-states', type=int, default=4)
    ap.add_argument('--state-indices', type=int, nargs='+',
                    help='Optional explicit flattened saved-state indices for targeted numerical checks')
    args = ap.parse_args(argv)
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists() or args.adaptive_states < 1 or args.scan_states < args.adaptive_states:
        raise ValueError('Choose a fresh output directory and valid state counts')
    manifest = json.loads((root/'manifest.json').read_text())
    if not manifest.get('completed_utc') or manifest.get('posterior_sha256') != digest((root/'posterior.json').read_bytes()):
        raise ValueError('A completed saved posterior and matching hash are required')
    cfg = saved_config(manifest['config'])
    inputs = {name: json.loads((root/f'{name}.json').read_text()) if (root/f'{name}.json').exists() else None
              for name in ('evidence', 'audits', 'outcomes', 'preparations')}
    def create(config):
        return make_model(inputs['evidence'], inputs['audits'], config, inputs['outcomes'], inputs['preparations'])
    model, finer = create(cfg), create(finer_config(cfg))
    arrays = np.load(root/'draws.npz')
    states = arrays['z'].reshape(-1, model.layout.size)
    stored = arrays['log_likelihood'].ravel()
    ids = (np.asarray(args.state_indices, dtype=int) if args.state_indices is not None
           else np.linspace(0, len(states)-1, min(args.scan_states, len(states))).astype(int))
    if np.any(ids < 0) or np.any(ids >= len(states)) or len(ids) != len(set(ids.tolist())):
        raise ValueError('Targeted state indices must be distinct valid saved-state indices')
    scanned = []
    for i in ids:
        value = model.log_likelihood(states[i])
        if not math.isfinite(value) or abs(value-stored[i]) > 1e-7:
            raise ValueError('Current likelihood does not reproduce the saved fit')
        scanned.append(dict(state=int(i), doubled_minus_base=float(finer.log_likelihood(states[i])-value)))
    selected = sorted(scanned, key=lambda r: -abs(r['doubled_minus_base']))[:args.adaptive_states]
    results = []
    for scanned_row in selected:
        index = scanned_row['state']
        z = states[index]
        rows = []
        for p, fp in zip(model.programs, finer.programs):
            par, fpar = model.parameters(p, z), finer.parameters(fp, z)
            for case in p['cases']:
                base, _ = case_integral(model, p, case, par)
                doubled, _ = case_integral(finer, fp, case, fpar)
                adaptive, relative_error = case_integral(model, p, case, par, adaptive=True)
                rows.append(dict(program=p['id'], case_id=case, base=base, doubled=doubled,
                    adaptive=adaptive, adaptive_minus_base=adaptive-base,
                    adaptive_minus_doubled=adaptive-doubled,
                    estimated_relative_integration_error_plus_tail_bound=relative_error))
        result = dict(**scanned_row, cases=rows,
            summed_adaptive_minus_base=sum(r['adaptive_minus_base'] for r in rows),
            summed_adaptive_minus_doubled=sum(r['adaptive_minus_doubled'] for r in rows))
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != 'cases'}), flush=True)
    write(out/'checks.json', dict(scanned_states=scanned, adaptive_checks=results,
        adaptive_integrator_error_is_estimated_not_a_mathematical_bound=True,
        scope='Conditional case-duration integrals only; not summary/fraction quadrature or full posterior validation'))
    write(out/'manifest.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        base_run=str(root), posterior_sha256=manifest['posterior_sha256'], hidden_truth_read=False,
        source_sha256=digest(pathlib.Path(__file__).read_bytes())))


if __name__ == '__main__':
    main()
