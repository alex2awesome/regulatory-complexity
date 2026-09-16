"""Summarize all retained SBC batches, including diagnostic failures and rank warnings."""
import argparse
import hashlib
import json
import pathlib

import numpy as np
from scipy.stats import binomtest,kstest

from .run_hierarchical import write


def summarize(rows):
    result={}
    for key in rows[0]:
        r=[v[key] for v in rows]
        k=sum(v['covered90'] for v in r)
        interval=binomtest(k,len(r)).proportion_ci()
        ranks=[v['rank_fraction'] for v in r]
        ks=kstest(ranks,'uniform')
        bad=sum(v['diagnostics']['rhat'] is None or v['diagnostics']['rhat']>1.01
                or v['diagnostics']['ess_bulk']<400 or v['diagnostics']['ess_tail']<200 for v in r)
        result[key]=dict(covered=k,replicates=len(r),coverage90=k/len(r),
            coverage_binomial_ci95=[float(interval.low),float(interval.high)],
            mean_rank_fraction=float(np.mean(ranks)),rank_ks_statistic=float(ks.statistic),
            exploratory_rank_ks_p=float(ks.pvalue),strict_diagnostic_failures=bad)
    return result


def apply_rng_repairs(batches, paths, repairs):
    """Keep every generated replicate, replacing only separately audited fits."""
    rows = [[r for r in batch['runs']] for batch in batches]
    locations = {pathlib.Path(p).resolve():i for i,p in enumerate(paths)}
    used, provenance = set(), []
    for directory in repairs:
        root = pathlib.Path(directory)
        manifest = json.loads((root/'manifest.json').read_text())
        source = pathlib.Path(manifest['base_run']).resolve()
        if source not in locations:
            raise ValueError('Repair refers to a batch not included in this summary')
        index, rep = locations[source], manifest['replicate']
        if (index,rep) in used or not 0 <= rep < len(rows[index]):
            raise ValueError('Duplicate or invalid repaired replicate')
        if manifest['batch_seed'] != batches[index]['seed']:
            raise ValueError('Repair seed does not match its calibration batch')
        if manifest['original_result'] != rows[index][rep]:
            raise ValueError('Original calibration row differs from repair provenance')
        evidence = source/f'replicate_{rep:03d}'/'evidence.json'
        if manifest['evidence_sha256'] != hashlib.sha256(evidence.read_bytes()).hexdigest():
            raise ValueError('Repair does not preserve generated evidence')
        result = root/'result.json'
        if manifest.get('result_sha256') != hashlib.sha256(result.read_bytes()).hexdigest():
            raise ValueError('RNG correction is incomplete or its result changed')
        replacement = json.loads(result.read_text())
        if set(replacement) != set(rows[index][rep]):
            raise ValueError('Calibration functionals changed in correction')
        used.add((index,rep))
        provenance.append(dict(directory=str(root),base_run=str(source),replicate=rep,
            original_result=rows[index][rep],corrected_result=replacement))
        rows[index][rep] = replacement
    return rows, provenance


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--rng-repairs',nargs='*',default=[],
                    help='Audited independent-RNG corrections; original scores are also retained')
    args=ap.parse_args(argv)
    out=pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh summary directory')
    batches=[json.loads((pathlib.Path(p)/'calibration.json').read_text()) for p in args.runs]
    if len({b['seed'] for b in batches}) != len(batches):
        raise ValueError('Do not pool repeated seeds as independent calibration data')
    keys=set(batches[0]['runs'][0])
    if any(set(b['runs'][0])!=keys for b in batches):
        raise ValueError('Calibration functionals differ')
    corrected,repairs=apply_rng_repairs(batches,args.runs,args.rng_repairs)
    pooled=summarize([r for b in corrected for r in b])
    report={'batches':{p:summarize(b) for p,b in zip(args.runs,corrected)},
        'pooled':pooled,'all_replicates_retained':True,
        'interpretation':['Coverage confidence intervals describe finite-replicate uncertainty, not real-world performance',
            'KS diagnostics are exploratory; within-chain autocorrelation and finite posterior simulation affect ranks',
            'Any failed chain diagnostics remain visible; do not declare calibration certified',
            'Pilot tests its generative timing hierarchy, not extraction, count/alias uncertainty, selection bias or heterogeneous real processes']}
    if repairs:
        report.update(rng_corrections=repairs,
            legacy_pooled=summarize([r for b in batches for r in b['runs']]),
            legacy_batches={p:summarize(b['runs']) for p,b in zip(args.runs,batches)})
        report['interpretation'].append('RNG corrections refit the same generated replicate; they are not additional independent datasets')
    write(out/'calibration_summary.json',report)
    write(out/'manifest.json',{'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'inputs':{p:hashlib.sha256((pathlib.Path(p)/'calibration.json').read_bytes()).hexdigest() for p in args.runs},
        'rng_repairs':{p:hashlib.sha256((pathlib.Path(p)/'manifest.json').read_bytes()).hexdigest() for p in args.rng_repairs}})
    print(json.dumps(pooled,indent=2))


if __name__=='__main__':
    main()
