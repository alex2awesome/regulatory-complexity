"""Check retained SBC likelihoods against current code without regenerating data.

The batches used different invariant kernels and chain lengths. This audit checks
the statistical target on saved states; it is not a claim that either batch mixed
adequately. No regulatory benchmark truth is read.
"""
import argparse
import hashlib
import json
import pathlib

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel, timing_interval
from .run_hierarchical import write


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving prior audit: choose a fresh directory')
    results = {}
    for directory in args.runs:
        root = pathlib.Path(directory)
        batch = json.loads((root/'calibration.json').read_text())
        cfg = Config(**batch['config'])
        rows = []
        for rep in range(batch['replicates']):
            path = root/f'replicate_{rep:03d}'
            evidence = json.loads((path/'evidence.json').read_text())
            model = HierarchicalModel([evidence],cfg)
            raw = np.load(path/'draws.npz')
            z,s,ll = raw['z'],raw['structure'],raw['log_likelihood']
            indices = np.unique(np.linspace(0,z.shape[1]-1,20).astype(int))
            error = max(abs(model.log_likelihood(z[c,i],s[c,i])-ll[c,i])
                        for c in range(len(z)) for i in indices)
            clipped = [m['id'] for m in evidence['measurements']
                if not np.allclose(timing_interval(m),np.log([m['lower'],m['upper']]),rtol=0,atol=1e-12)]
            rows.append(dict(replicate=rep,saved_likelihood_max_error=error,
                             altered_reporting_bins=clipped,states_checked=len(indices)*len(z)))
        results[directory] = dict(replicates=rows,
            max_likelihood_error=max(r['saved_likelihood_max_error'] for r in rows),
            all_checked_targets_match=all(np.isfinite(r['saved_likelihood_max_error']) and
                r['saved_likelihood_max_error']<=1e-7 and not r['altered_reporting_bins'] for r in rows))
        print(json.dumps(dict(run=directory,match=results[directory]['all_checked_targets_match'],
                              max_error=results[directory]['max_likelihood_error'])),flush=True)
    write(out/'audit.json',dict(batches=results,
        qualification='Finite numerical checks of saved likelihoods, not a proof of kernel correctness or convergence'))
    source = pathlib.Path(__file__).parent
    write(out/'manifest.json',dict(source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest()
        for n in ('audit_calibration_target.py','bayes_hierarchy.py','evidence_contract.py','schedule_kernel.py')},
        inputs={p:hashlib.sha256((pathlib.Path(p)/'calibration.json').read_bytes()).hexdigest() for p in args.runs}))


if __name__ == '__main__':
    main()
