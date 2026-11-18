"""Auditable posterior reweighting and quadrature sensitivity, without gold.

Self-normalized importance weights are not a new MCMC fit. Poor overlap is flagged
and requires refitting. Raw-weight ESS ignores chain autocorrelation; both overlap
and a conservative autocorrelation-adjusted heuristic are reported explicitly.
"""
from dataclasses import replace
import argparse
import hashlib
import json
import math
import pathlib

import numpy as np
from scipy.special import logsumexp

from .bayes_hierarchy import Config, HierarchicalModel
from .infra.manifest import write


def weighted_quantiles(x, weights, probs=(.05, .5, .95)):
    if not len(weights) or np.sum(weights) <= 0:
        return [None for _ in probs]
    weights = np.asarray(weights) / np.sum(weights)
    order = np.argsort(x)
    x, weights = np.asarray(x)[order], np.asarray(weights)[order]
    cumulative = np.cumsum(weights) - weights / 2
    return np.interp(probs, cumulative, x, left=x[0], right=x[-1]).tolist()


def count_log_mass(h, mean, cap):
    if mean == 0:
        return np.where(h == 0, 0., -np.inf)
    log_r = math.log(mean / (1 + mean))
    return h * log_r - logsumexp(np.arange(cap + 1) * log_r)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--report', help='Optional reporting-only posterior path')
    ap.add_argument('--out', required=True)
    ap.add_argument('--stride', type=int, default=4)
    ap.add_argument('--quadrature', action='store_true')
    args = ap.parse_args(argv)
    if args.stride < 1:
        raise ValueError('Stride must be positive')
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving prior sensitivity; use a fresh directory')
    manifest = json.loads((root / 'manifest.json').read_text())
    report_path = pathlib.Path(args.report) if args.report else root / 'posterior.json'
    report = json.loads(report_path.read_text())
    cfg = Config(**manifest['config'])
    evidence = json.loads((root / 'evidence.json').read_text())
    model = HierarchicalModel(evidence, cfg)
    raw = np.load(root / 'draws.npz')
    original_shape = raw['z'].shape
    z = raw['z'][:, ::args.stride]
    st = raw['structure'][:, ::args.stride]
    ll = raw['log_likelihood'][:, ::args.stride].reshape(-1)
    flat = z.reshape((-1, z.shape[-1]))
    structures = st.reshape((-1, len(model.processes), 2))
    checked = np.unique(np.linspace(0,len(flat)-1,min(200,len(flat))).astype(int))
    error = max(abs(model.log_likelihood(flat[i],structures[i])-ll[i]) for i in checked)
    if not np.isfinite(error) or error > 1e-7:
        raise ValueError('Saved likelihood disagrees: cannot reweight a different posterior target')
    timing = {p.id: np.array(report['programs'][p.id]['process_median_draws']).reshape(original_shape[:2])[:, ::args.stride].reshape(-1)
              for p in model.processes}
    # An effective sample fraction is only a rough warning, not an IS-MCMC theorem.
    base_fraction = min(report['diagnostics'][f'process:{p.id}']['ess_bulk'] / (original_shape[0]*original_shape[1])
                        for p in model.processes)
    variants = [('default', {})]
    refits_required = {}
    variants += [(f'prior_median_{v}', {'global_median': v}) for v in (3.5, 14.)]
    if cfg.unseen_mean==0 and cfg.max_unseen>0:
        refits_required['unseen_mean_1.0/4.0'] = 'A zero-hidden-stage point prior cannot cover positive hidden counts by reweighting'
    else:
        variants += [(f'unseen_mean_{v}', {'unseen_mean': v}) for v in (0., 1., 4.)]
    if cfg.source_bias_sd>0:
        variants += [('source_bias_0.7', {'source_bias_sd': .7})]
    else:
        refits_required['source_bias_0.7'] = 'A zero-bias point prior cannot cover nonzero source offsets by reweighting'
    if cfg.outcome_logit_sd > 0 and any(len(p.zo) for p in model.processes):
        variants += [(f'outcome_logit_sd_{v}', {'outcome_logit_sd':v}) for v in (.75,3.)]
    elif any(len(p.zo) for p in model.processes):
        refits_required['outcome_logit_sd_0.75/3.0'] = 'Fixed outcome proportions require a refit for uncertain proportions'
    if args.quadrature:
        variants += [('quadrature_512', {'population_size': 512}),
                     ('quadrature_new_seed', {'population_seed': 1919})]
    results = {}
    for name, changes in variants:
        target = replace(cfg, **changes)
        logw = np.zeros(len(flat))
        values = timing
        if 'global_median' in changes:
            m = math.log(cfg.global_median) + cfg.global_log_sd * flat[:, model.hyper[0]]
            logw = -.5 * ((m - math.log(target.global_median)) / cfg.global_log_sd) ** 2 + .5 * flat[:, model.hyper[0]] ** 2
        if 'unseen_mean' in changes:
            for pi in range(len(model.processes)):
                h = structures[:, pi, 1]
                logw += count_log_mass(h, target.unseen_mean, cfg.max_unseen) - count_log_mass(h, cfg.unseen_mean, cfg.max_unseen)
        if 'source_bias_sd' in changes:
            actual = cfg.source_bias_sd * flat[:, model.zs]
            logw = (np.log(cfg.source_bias_sd / target.source_bias_sd)
                    - .5 * actual ** 2 * (1 / target.source_bias_sd ** 2 - 1 / cfg.source_bias_sd ** 2)).sum(axis=1)
        if 'outcome_logit_sd' in changes:
            coordinates = np.concatenate([p.zo for p in model.processes])
            actual = cfg.outcome_logit_sd*flat[:,coordinates]
            logw = (np.log(cfg.outcome_logit_sd/target.outcome_logit_sd)
                    -.5*actual**2*(1/target.outcome_logit_sd**2-1/cfg.outcome_logit_sd**2)).sum(axis=1)
        if 'population_size' in changes or 'population_seed' in changes:
            other = HierarchicalModel(evidence, target)
            logw = np.array([other.log_likelihood(x, ss) for x, ss in zip(flat, structures)]) - ll
            values = {p.id: [] for p in other.processes}
            for x, ss in zip(flat, structures):
                par = other.parameters(x)
                for pi, p in enumerate(other.processes):
                    _, mask, ends, hidden, _ = other.process_state(p, x, par, ss[pi], population=True)
                    values[p.id].append(float(np.median(p.decision_time(ends, mask) + hidden)))
        weights = np.exp(logw - logsumexp(logw))
        ess = float(1 / np.sum(weights ** 2))
        adjusted = ess * min(1., args.stride * base_fraction)
        results[name] = {'changes': changes, 'importance_ess_raw': ess,
            'importance_ess_autocorrelation_heuristic': adjusted,
            'max_normalized_weight': float(weights.max()),
            'overlap_adequate': bool(ess >= max(1000, .1 * len(weights)) and weights.max() < .01),
            'programs': {p.id: {'median_ci90': weighted_quantiles(values[p.id], weights),
                'hidden_count_ci90': weighted_quantiles(structures[:, pi, 1], weights),
                'per_chain_median': [weighted_quantiles(np.asarray(values[p.id]).reshape(z.shape[:2])[c],
                    weights.reshape(z.shape[:2])[c], [.5])[0] for c in range(z.shape[0])]}
                for pi, p in enumerate(model.processes)}}
        write(out / 'progress.json', results)
        print(json.dumps({'variant': name, **results[name]}), flush=True)
    write(out / 'sensitivity.json', {'run': str(root), 'report': str(report_path), 'stride': args.stride,
        'base_posterior_converged': report['posterior_converged'], 'results': results,
        'refits_required_for_prior_support':refits_required,
        'qualification': 'Self-normalized importance sensitivity, not refits. Weight ESS ignores autocorrelation; adjusted ESS is only a heuristic. Poor overlap requires refitting.'})
    write(out / 'manifest.json', {'base_run':str(root),'saved_likelihood_max_error':error,
        'evidence_sha256':hashlib.sha256((root/'evidence.json').read_bytes()).hexdigest(),
        'posterior_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
        'source_sha256':{name:hashlib.sha256((pathlib.Path(__file__).parent/name).read_bytes()).hexdigest()
                         for name in ('sensitivity_hierarchy.py','bayes_hierarchy.py','evidence_contract.py','schedule_kernel.py')}})


if __name__ == '__main__':
    main()
