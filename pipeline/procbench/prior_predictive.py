"""Numerical prior-predictive checks conditional on the public semantic inventory."""
import argparse
from dataclasses import asdict
import hashlib
import json
import pathlib

import numpy as np
from scipy.special import logsumexp

from .bayes_hierarchy import Config, HierarchicalModel
from .infra.manifest import write


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--evidence',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--draws',type=int,default=5000)
    ap.add_argument('--seed',type=int,default=187921)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    files = [pathlib.Path(p) for p in args.evidence]
    evidence = [json.loads(p.read_text()) for p in files]
    cfg = Config()
    model = HierarchicalModel(evidence,cfg)
    rng = np.random.default_rng(args.seed)
    count_logp = np.array([model.hidden_log_prior(k) for k in range(cfg.max_unseen+1)])
    count_p = np.exp(count_logp-logsumexp(count_logp))
    result = {p.id:[] for p in model.processes}
    for _ in range(args.draws):
        z = rng.normal(size=model.layout.size)
        par = model.parameters(z)
        for p in model.processes:
            structure = int(rng.integers(len(p.graphs))),int(rng.choice(len(count_p),p=count_p))
            _, mask, ends, hidden, _ = model.process_state(p,z,par,structure,population=True)
            elapsed = p.decision_time(ends,mask)+hidden
            result[p.id].append([float(np.median(elapsed)),float(np.quantile(elapsed,.9)),
                                 float(np.mean(mask.sum(axis=1)+structure[1]))])
    def summarize(values):
        return {'median':float(np.median(values)), 'interval90':np.quantile(values,[.05,.95]).tolist(),
                'interval99':np.quantile(values,[.005,.995]).tolist()}
    summary = {pid:{key:summarize(np.array(v)[:,i]) for i,key in enumerate(
        ('process_median_days','process_p90_days','expected_distinct_initial_operations'))}
        for pid,v in result.items()}
    write(out/'prior_predictive.json',summary)
    write(out/'manifest.json',{'config':asdict(cfg),'draws':args.draws,'seed':args.seed,
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'source_sha256':{n:hashlib.sha256((pathlib.Path(__file__).parent/n).read_bytes()).hexdigest()
                         for n in ('prior_predictive.py','bayes_hierarchy.py','evidence_contract.py','schedule_kernel.py')},
        'scope':'numerical priors conditional on interpreted public inventory; no timing likelihood or benchmark truth'})
    np.savez_compressed(out/'draws.npz',**{pid:np.array(v) for pid,v in result.items()})
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
