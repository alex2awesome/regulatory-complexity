"""Continue legacy generated-data recovery runs using saved states and checked likelihoods."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
import hashlib
import json
import multiprocessing
import pathlib

import numpy as np

from .bayes_hierarchy import Config, HierarchicalModel
from .extend_hierarchy import check_fresh_seed, continue_chain
from .infra.manifest import write
from .validate_hierarchy import generated_evidence


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--extra-draws',type=int,default=8000)
    ap.add_argument('--seed',type=int,default=625933)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--cases',type=int,default=10)
    ap.add_argument('--no-totals',action='store_true')
    args=ap.parse_args(argv)
    root,out=pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh output directory')
    original=json.loads((root/'comparison.json').read_text())
    cfg=Config(**original['config'])
    base_manifest = json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else {'config':asdict(cfg)}
    check_fresh_seed(base_manifest,args.seed,cfg.chains)
    evidence,truth=generated_evidence(n_cases=args.cases,with_totals=not args.no_totals)
    evidence_digest=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
    if base_manifest.get('generated_evidence_sha256',evidence_digest)!=evidence_digest:
        raise ValueError('Generated evidence differs from the saved recovery run')
    model=HierarchicalModel([evidence],cfg)
    data=np.load(root/'draws.npz')
    z0,s0,ll0=data['z'],data['structure'],data['log_likelihood']
    indices=np.unique(np.linspace(0,z0.shape[1]-1,50).astype(int))
    differences=[abs(model.log_likelihood(z0[c,i],s0[c,i])-ll0[c,i])
                 for c in range(len(z0)) for i in indices]
    error=max(differences)
    if not np.all(np.isfinite(differences)) or error>1e-7:
        raise ValueError('Likelihood disagrees: cannot continue this generated-data run')
    continuation=replace(cfg,seed=args.seed,warmup=0,draws=args.extra_draws)
    combined=replace(cfg,draws=z0.shape[1]+args.extra_draws)
    source=pathlib.Path(__file__).parent
    names=('extend_validation.py','extend_hierarchy.py','validate_hierarchy.py',
           'bayes_hierarchy.py','latent_gaussian.py','evidence_contract.py','schedule_kernel.py')
    write(out/'manifest.json',dict(config=asdict(combined),continuation_config=asdict(continuation),
        base_manifest=base_manifest,generated_evidence_sha256=evidence_digest,
        n_cases=args.cases,with_totals=not args.no_totals,generator_seed=17,
        legacy_base_run=str(root),legacy_comparison=original,saved_likelihood_max_error=error,
        source_sha256={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names},
        caveat='Numerical target verified against saved likelihoods; base provenance is preserved without inventing a legacy source snapshot'))
    write(out/'evidence.json',[evidence])
    for name in names:
        path=out/'source'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((source/name).read_bytes())
    with ProcessPoolExecutor(max_workers=min(args.workers,cfg.chains),
            mp_context=multiprocessing.get_context('spawn')) as pool:
        jobs=[pool.submit(continue_chain,[evidence],continuation,i,(z0[i,-1],s0[i,-1]),str(out))
              for i in range(cfg.chains)]
        parts=[np.load(job.result()) for job in jobs]
    z=np.concatenate((z0,np.concatenate([p['z'] for p in parts])),axis=1)
    s=np.concatenate((s0,np.concatenate([p['structure'] for p in parts])),axis=1)
    ll=np.concatenate((ll0,np.concatenate([p['log_likelihood'] for p in parts])),axis=1)
    np.savez_compressed(out/'draws.npz',z=z,structure=s,log_likelihood=ll)
    model.cfg=combined
    report=model.report(z,s,ll)
    comparison={a['id']:dict(true_median=truth[a['id']],estimated_median=a['timing']['median_days'],
         ci90=a['timing']['median_ci90'],held_out='held_out' in a['id'])
         for a in report['programs'][evidence['program_id']]['model']['activities']}
    write(out/'report.json',report)
    write(out/'comparison.json',dict(config=asdict(combined),steps=comparison))
    print(json.dumps({'converged':report['posterior_converged'],'flagged':report['diagnostics_flagged'],
        'held_out':{k:v for k,v in comparison.items() if v['held_out']}}),flush=True)


if __name__=='__main__':
    main()
