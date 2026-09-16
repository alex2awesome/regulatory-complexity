"""Refine v6 population predictions from unchanged posterior draws, without MCMC.

This is only valid when population integration is absent from the likelihood.
Original fits (including failed precision checks) remain immutable.
"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import pathlib
import shutil

import numpy as np

from .bayes_trace_hierarchy import Config, VisitHierarchy
from .reconcile_evidence import digest, write
from .run_visit_hierarchy import precision_check


def prepare_refinement(root, population_size):
    root = pathlib.Path(root)
    original = json.loads((root / 'manifest.json').read_text())
    if (not original.get('completed_utc') or
            original.get('posterior_sha256') != digest((root / 'posterior.json').read_bytes())):
        raise ValueError('Refinement requires a completed, unchanged fit')
    cfg = Config(**original['config'])
    if (population_size <= cfg.population_size or population_size & (population_size - 1)):
        raise ValueError('Use a larger, power-of-two population size')
    base = original
    while 'input_sha256' not in base:
        base = base['base_manifest']
    if len(base['input_sha256']) != 1:
        raise ValueError('Expected exactly one original joint-model input')
    for path, expected in base['input_sha256'].items():
        raw = pathlib.Path(path).read_bytes()
        if digest(raw) != expected:
            raise ValueError('An original inference input changed')
        input_data = json.loads(raw)
    data = json.loads((root / 'data.json').read_text())
    if data != input_data:
        raise ValueError('Saved data disagree with the original inference input')
    if cfg.selection_sd or any(o['case_id'] is None for p in data['programs']
                               for o in p.get('observations', [])):
        raise ValueError('Population integration occurs in the likelihood; refit instead')
    cfg = replace(cfg, population_size=population_size)
    model = VisitHierarchy(data, cfg)
    with np.load(root / 'draws.npz') as raw:
        z, structures, ll = raw['z'], raw['structures'], raw['log_likelihood']
    if (z.ndim != 3 or z.shape[:2] != ll.shape or structures.shape != (*ll.shape, len(model.programs))
            or z.shape[-1] != model.layout.size or z.shape[0] != cfg.chains
            or z.shape[1] != cfg.draws):
        raise ValueError('Saved state layout disagrees with the completed fit')
    positions = np.linspace(0, z.shape[1] - 1, min(50, z.shape[1]), dtype=int)
    errors = [abs(model.log_likelihood(z[c, i], structures[c, i]) - ll[c, i])
              for c in range(len(z)) for i in positions]
    if not np.isfinite(errors).all() or max(errors) > 1e-7:
        raise ValueError('Saved likelihood changed; prediction refinement is not a refit')
    checks = dict(saved_likelihood_checks=len(errors), saved_likelihood_max_difference=max(errors),
                  original_population_size=original['config']['population_size'])
    return original, model, z, structures, ll, checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--population-size', type=int, default=16384)
    args = parser.parse_args(argv)
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve prior results; choose a fresh output directory')
    original, model, z, structures, ll, checks = prepare_refinement(root, args.population_size)
    source = pathlib.Path(__file__).parent
    names = ['refine_visit_predictions.py', 'run_visit_hierarchy.py', 'bayes_trace_hierarchy.py',
             'compact_visit_trace.py', 'latent_gaussian.py', 'visit_clocks.py', 'bayes_hierarchy.py',
             'evidence_contract.py', 'schedule_kernel.py', 'approximation_checks.py']
    manifest = dict(config=asdict(model.cfg), base_run=str(root), base_manifest=original,
                    started_utc=datetime.now(timezone.utc).isoformat(),
                    prediction_resolution_only=True, mcmc_draws_added=0,
                    saved_draws_sha256=digest((root / 'draws.npz').read_bytes()),
                    hidden_truth_read_during_inference=False,
                    source_sha256={name: digest((source / name).read_bytes()) for name in names},
                    **checks)
    write(out / 'manifest.json', manifest)
    write(out / 'data.json', model.data)
    shutil.copy2(root / 'draws.npz', out / 'draws.npz')
    for name in names:
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
    print(json.dumps(dict(stage='recomputing_predictions', checks=checks,
                          population_size=args.population_size, mcmc_draws_added=0)), flush=True)
    report = model.report(z, structures, ll)
    finer = VisitHierarchy(model.data, replace(model.cfg, population_size=args.population_size * 4))
    report['precision'] = precision_check(model, finer, z, structures)
    report['numerically_usable'] = (report['posterior_converged'] and
                                    report['precision']['likelihood_acceptable'] and
                                    report['precision']['predictions_acceptable'])
    write(out / 'posterior.json', report)
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(),
                    posterior_sha256=digest((out / 'posterior.json').read_bytes()))
    write(out / 'manifest.json', manifest)
    print(json.dumps(dict(numerically_usable=report['numerically_usable'],
                          precision=report['precision'], flagged=report['diagnostics_flagged'])), flush=True)


if __name__ == '__main__':
    main()
