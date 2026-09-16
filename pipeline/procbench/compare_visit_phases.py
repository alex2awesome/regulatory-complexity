"""Score the frozen waiting/service integration, not a full-burden or LLM test."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
import math
import pathlib

from scipy.special import ndtri

from .compare_visit_integration import assert_nested_evidence,interval_score,verified_fit
from .reconcile_evidence import digest,write


def score(report,truth):
    metrics=report['programs']['J__appointment']['metrics']
    agency=report['agencies']['J:Appointments']
    return dict(
        cycle_median_days=interval_score(metrics['initial_decision_median_days'],truth['cycle_median_days'],True),
        cycle_p90_days=interval_score(metrics['initial_decision_p90_days'],
            truth['cycle_median_days']*math.exp(truth['cycle_log_sd']*ndtri(.9)),True),
        mean_cycle_days=interval_score(agency['inventory_mean_cycle_days'],truth['mean_cycle_days'],True),
        mean_wait_days=interval_score(agency['inventory_mean_wait_days'],truth['mean_wait_days'],True),
        mean_service_elapsed_days=interval_score(agency['inventory_mean_service_elapsed_days'],truth['mean_service_elapsed_days'],True))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('cycle-run','mixed-run','data','out'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args(argv)
    root,out=pathlib.Path(args.data),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Choose a fresh comparison directory')
    generator=json.loads((root/'manifest.json').read_text())
    inputs={}
    for name in ('cycle_only','mixed'):
        path=root/(name+'.json')
        if digest(path.read_bytes())!=generator['artifacts_sha256'][name]:
            raise ValueError('Frozen condition changed')
        inputs[name]=json.loads(path.read_text())
    assert_nested_evidence(inputs['cycle_only'],inputs['mixed'])
    manifests,reports={},{}
    for name,run in [('cycle_only',args.cycle_run),('mixed',args.mixed_run)]:
        manifests[name],reports[name]=verified_fit(run,inputs[name])
        if not reports[name]['phase_channel']['enabled']:
            raise ValueError('Both conditions must keep the same enabled phase prior')
    numerical={'seed','draws','warmup','population_size'}
    configs=[{k:v for k,v in m['config'].items() if k not in numerical} for m in manifests.values()]
    if configs[0]!=configs[1]:
        raise ValueError('Statistical assumptions changed between conditions')
    # Only after input and fit verification do we load/replay evaluation truth.
    source=root/'source/generate_visit_phases.py'
    if digest(source.read_bytes())!=generator['source_sha256']:
        raise ValueError('Frozen phase generator changed')
    spec=importlib.util.spec_from_file_location('pipeline.procbench._frozen_phase_generator',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cycle,mixed,truth=module.generate(generator['seed'])
    if cycle!=inputs['cycle_only'] or mixed!=inputs['mixed']:
        raise ValueError('Saved generator does not reproduce the exact evidence')
    path=root/'truth.json'
    if digest(path.read_bytes())!=generator['artifacts_sha256']['truth'] or json.loads(path.read_text())!=truth:
        raise ValueError('Truth does not match its saved generator')
    result=dict(conditions={name:dict(scores=score(report,truth),phase_channel=report['phase_channel'],
        agency_reports=report['agencies'],precision=report['precision'],
        agency_inventory_diagnostics=report['agency_inventory_diagnostics']) for name,report in reports.items()},
        scope=truth['scope'],matched_llm_comparison=False,full_burden_validation=False,
        caveats=['One ten-case development realization, not replicated calibration.',
            'Cycle-only phase estimates are prior-dependent, even if a prior interval looks wide.',
            'Waiting/service observations are added without changing original cycle reports or priors.',
            'Elapsed service is not person-hours; this dataset supplies no labor measurements.',
            'A single known operation/agency cannot identify intrinsic agency versus task-type effects.'])
    write(out/'comparison.json',result)
    write(out/'manifest.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        cycle_run=args.cycle_run,mixed_run=args.mixed_run,generator_manifest=generator,
        inference_manifests=manifests,frozen_generator_replayed=True,
        truth_sha256=digest(path.read_bytes()),source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        comparison_sha256=digest((out/'comparison.json').read_bytes())))
    print(json.dumps({name:row['scores'] for name,row in result['conditions'].items()}),flush=True)


if __name__=='__main__':
    main()
