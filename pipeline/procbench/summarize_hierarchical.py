"""Rebuild summaries from saved draws without refitting or overwriting a run.

Useful after a reporting-only defect or adding diagnostics. Checks the current
likelihood against saved values before producing a separately versioned summary.
Not a license to reuse draws after changing the statistical model.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import pathlib

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .run_hierarchical import evaluate, write


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--evaluate-world')
    args = ap.parse_args(argv)
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh reporting directory')
    manifest = json.loads((root / 'manifest.json').read_text())
    evidence = json.loads((root / 'evidence.json').read_text())
    cfg = Config(**manifest['config'])
    model = HierarchicalModel(evidence, cfg)
    draws = np.load(root / 'draws.npz')
    z, structures, ll = draws['z'], draws['structure'], draws['log_likelihood']
    # All parameters/latent variables are unchanged. This is an explicit
    # numerical check, in addition to retaining original sampling code snapshots.
    checks = np.unique(np.linspace(0, z.shape[1] - 1, min(100, z.shape[1])).astype(int))
    differences = [abs(model.log_likelihood(z[c, i], structures[c, i]) - ll[c, i])
                   for c in range(z.shape[0]) for i in checks]
    if max(differences) > 1e-7:
        raise ValueError('Current likelihood differs from saved run; refit instead')
    result = model.report(z, structures, ll)
    previous = root / 'posterior.json'
    if previous.exists():
        result['effort'] = json.loads(previous.read_text()).get('effort')
    else:
        result['effort'] = {'status': 'not refitted by this reporting-only command',
                            'note': 'Any saved effort arrays require their own summary; missing means unknown.'}
    write(out / 'posterior.json', result)
    write(out / 'manifest.json', {'config': asdict(cfg), 'draws_from': str(root / 'draws.npz'),
        'evidence_from': str(root / 'evidence.json'), 'sampling_manifest': str(root / 'manifest.json'),
        'report_source_sha256': hashlib.sha256(pathlib.Path(__file__).with_name('bayes_hierarchy.py').read_bytes()).hexdigest(),
        'saved_likelihood_check_max_error': max(differences), 'n_states_checked': len(differences),
        'posterior_sha256': hashlib.sha256((out / 'posterior.json').read_bytes()).hexdigest(),
        'created_utc': datetime.now(timezone.utc).isoformat(), 'hidden_truth_read_during_inference': False})
    for pid, p in result['programs'].items():
        write(out / f'{pid}.model.json', p['model'])
    if args.evaluate_world:
        write(out / 'evaluation.json', evaluate(result, pathlib.Path(args.evaluate_world)))
    print(json.dumps({'converged': result['posterior_converged'], 'flagged': result['diagnostics_flagged'],
        'timing': {pid: p['model']['process_timing'] for pid, p in result['programs'].items()}}), flush=True)


if __name__ == '__main__':
    main()
