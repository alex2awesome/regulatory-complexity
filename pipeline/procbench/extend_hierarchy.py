"""Continue saved Bayesian chains with fresh independent RNG streams.

All prior draws and sources are preserved. New model likelihood must agree with
the saved likelihood before extending. This may change a valid transition kernel,
not the posterior target. Numerical extensions are not gold-driven model selection.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import pathlib
import time

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .run_hierarchical import evaluate, write
from .schedule_kernel import ACCELERATOR


def check_fresh_seed(manifest, seed, chains):
    """A second extension must not replay random numbers used by the first."""
    used = set()
    current = manifest
    while isinstance(current,dict):
        for key in ('config','continuation_config'):
            cfg = current.get(key,{})
            if 'seed' in cfg:
                used.update(cfg['seed']+104729*i for i in range(cfg.get('chains',chains)))
        current = current.get('base_manifest')
    proposed = {seed+104729*i for i in range(chains)}
    if used & proposed:
        raise ValueError('Continuation seed overlaps a previously used chain stream; choose a fresh --seed')


def continue_chain(evidence, cfg, index, start, out):
    model = HierarchicalModel(evidence, replace(cfg, chains=1, seed=cfg.seed + index * 104729))
    target = pathlib.Path(out)
    with (target / f'chain_{index}.progress.jsonl').open('w') as log:
        def progress(value):
            value['chain'] = index + 1
            log.write(json.dumps(value) + '\n')
            log.flush()
            if value['iteration'] == 1 or value['iteration'] % 1000 == 0:
                print(json.dumps(value), flush=True)
        z, s, ll, calls = model.sample(progress, initial=(start[0][None, :], start[1][None, :]))
    path = target / f'continuation_{index}.npz'
    np.savez_compressed(path, z=z, structure=s, log_likelihood=ll)
    return str(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--extra-draws', type=int, default=8000)
    ap.add_argument('--seed', type=int, default=918216)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--evaluate-world')
    args = ap.parse_args(argv)
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh continuation directory')
    original = json.loads((root / 'manifest.json').read_text())
    evidence = json.loads((root / 'evidence.json').read_text())
    cfg = Config(**original['config'])
    check_fresh_seed(original,args.seed,cfg.chains)
    model = HierarchicalModel(evidence, cfg)
    raw = np.load(root / 'draws.npz')
    z0, s0, ll0 = raw['z'], raw['structure'], raw['log_likelihood']
    checks = np.unique(np.linspace(0, z0.shape[1] - 1, 50).astype(int))
    differences = [abs(model.log_likelihood(z0[c,i], s0[c,i]) - ll0[c,i])
                   for c in range(z0.shape[0]) for i in checks]
    if not np.all(np.isfinite(differences)) or max(differences) > 1e-7:
        raise ValueError('Statistical target changed; cannot continue these chains')
    continuation = replace(cfg, seed=args.seed, warmup=0, draws=args.extra_draws)
    combined = replace(cfg, draws=cfg.draws + args.extra_draws)
    started = time.monotonic()
    source = pathlib.Path(__file__).parent
    names = ('extend_hierarchy.py', 'bayes_hierarchy.py', 'latent_gaussian.py', 'evidence_contract.py', 'schedule_kernel.py')
    manifest = {'config': asdict(combined), 'continuation_config': asdict(continuation),
        'base_run': str(root), 'base_manifest': original, 'targets_extended': ['elapsed'],
        'scheduling_backend': ACCELERATOR,
        'saved_likelihood_max_error': max(differences), 'started_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': {n: hashlib.sha256((source / n).read_bytes()).hexdigest() for n in names},
        'hidden_truth_read_during_inference': False}
    write(out / 'manifest.json', manifest)
    write(out / 'evidence.json', evidence)
    for name in names:
        path = out / 'source' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((source / name).read_bytes())
    with ProcessPoolExecutor(max_workers=min(args.workers, cfg.chains),
                             mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs = [pool.submit(continue_chain, evidence, continuation, i,
                           (z0[i,-1].copy(), s0[i,-1].copy()), str(out)) for i in range(cfg.chains)]
        pieces = [np.load(job.result()) for job in jobs]
    z = np.concatenate((z0, np.concatenate([p['z'] for p in pieces])), axis=1)
    s = np.concatenate((s0, np.concatenate([p['structure'] for p in pieces])), axis=1)
    ll = np.concatenate((ll0, np.concatenate([p['log_likelihood'] for p in pieces])), axis=1)
    np.savez_compressed(out / 'draws.npz', z=z, structure=s, log_likelihood=ll)
    model.cfg = combined
    report = model.report(z, s, ll)
    prior_report = root / 'posterior.json'
    if prior_report.exists():
        report['effort'] = json.loads(prior_report.read_text()).get('effort')
    else:
        report['effort'] = {'status': 'elapsed-only continuation; no new work-hour inference'}
    write(out / 'posterior.json', report)
    for pid, p in report['programs'].items():
        write(out / f'{pid}.model.json', p['model'])
    manifest.update(seconds=time.monotonic() - started, completed_utc=datetime.now(timezone.utc).isoformat(),
        posterior_sha256=hashlib.sha256((out / 'posterior.json').read_bytes()).hexdigest())
    write(out / 'manifest.json', manifest)
    if args.evaluate_world:
        write(out / 'evaluation.json', evaluate(report, pathlib.Path(args.evaluate_world)))
    print(json.dumps({'converged': report['posterior_converged'], 'flagged': report['diagnostics_flagged'],
        'timing': {pid: p['model']['process_timing'] for pid, p in report['programs'].items()}}), flush=True)


if __name__ == '__main__':
    main()
