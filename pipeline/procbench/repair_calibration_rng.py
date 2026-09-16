"""Refit a legacy SBC replicate with inference RNG independent of its truth.

Preserves its generated data, parameters, and original diagnostic failures. Does
not use benchmark data or change the posterior target. The original calibration
batch remains intact; this output is a separately recorded technical correction.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
import pathlib
import time

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .calibrate_hierarchy import inference_seed, score_replicate
from .run_hierarchical import write


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--replicate', type=int, default=0)
    ap.add_argument('--draws', type=int, default=4000)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    root, out = pathlib.Path(args.run), pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh repair directory; originals are preserved')
    original = json.loads((root/'manifest.json').read_text())
    rep = root/f'replicate_{args.replicate:03d}'
    evidence = json.loads((rep/'evidence.json').read_text())
    raw = np.load(rep/'draws.npz')
    previous = json.loads((rep/'result.json').read_text())
    cfg = replace(Config(**original['config']), draws=args.draws,
                  seed=inference_seed(original['seed'], args.replicate))
    model = HierarchicalModel([evidence], cfg)
    positions = np.unique(np.linspace(0,raw['z'].shape[1]-1,50).astype(int))
    error = max(abs(model.log_likelihood(raw['z'][c,i],raw['structure'][c,i])-
                    raw['log_likelihood'][c,i]) for c in range(len(raw['z'])) for i in positions)
    if error > 1e-7:
        raise ValueError('Likelihood changed: do not call this an RNG-only correction')
    source = pathlib.Path(__file__).parent
    names = ('repair_calibration_rng.py','calibrate_hierarchy.py','bayes_hierarchy.py',
             'latent_gaussian.py','evidence_contract.py','schedule_kernel.py')
    manifest = dict(base_run=str(root), replicate=args.replicate, batch_seed=original['seed'],
        config=asdict(cfg), saved_likelihood_max_error=error,
        evidence_sha256=hashlib.sha256((rep/'evidence.json').read_bytes()).hexdigest(),
        original_result=previous,
        purpose='Independent inference RNG, same generated evidence and true parameters; no result-based replicate selection',
        source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names})
    write(out/'manifest.json',manifest)
    write(out/'evidence.json',evidence)
    for name in names:
        path = out/'source'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((source/name).read_bytes())
    start = time.monotonic()
    with (out/'progress.jsonl').open('w') as log:
        def progress(value):
            log.write(json.dumps(value)+'\n')
            log.flush()
            if value['iteration']==1 or value['iteration']%1000==0:
                print(json.dumps(value),flush=True)
        z,s,ll,_ = model.sample(progress)
    rows = score_replicate(model,z,raw['true_z'])
    np.savez_compressed(out/'draws.npz',z=z,structure=s,log_likelihood=ll,true_z=raw['true_z'])
    write(out/'result.json',rows)
    manifest['seconds'] = time.monotonic()-start
    manifest['result_sha256'] = hashlib.sha256((out/'result.json').read_bytes()).hexdigest()
    write(out/'manifest.json',manifest)
    print(json.dumps(rows),flush=True)


if __name__ == '__main__':
    main()
