"""Verify new clock fields without regenerating or mutating an existing world."""
import argparse
from datetime import datetime,timezone
import json
import pathlib

from benchmark.synth.generator.simulate import simulate_process
from .reconcile_evidence import digest,write


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--world',required=True)
    ap.add_argument('--programs',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    root,out=pathlib.Path(args.world),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve existing verification: choose a fresh directory')
    paths=[root/'world.json']
    world=json.loads(paths[0].read_text())
    result={}
    for pid in args.programs:
        pp=root/'truth/processes'/f'{pid}.json'
        rp=root/'truth/local_rules'/f'{pid}.json'
        lp=root/'truth/log'/f'{pid}.jsonl'
        sp=root/'truth/log'/f'{pid}.summary.json'
        paths.extend([pp,rp,lp,sp])
        records=[json.loads(line) for line in lp.read_text().splitlines() if line.strip()]
        new,summary=simulate_process(world,json.loads(pp.read_text()),json.loads(rp.read_text()),len(records))
        old_keys=[{k:v for k,v in record.items() if k not in {'event_clocks','rework_events'}} for record in new]
        prior_summary={k:v for k,v in summary.items() if k not in {
            'event_clock_summaries','clock_definitions','observed_first_visit_clocks','observed_rework'}}
        same_records=old_keys==records
        same_summary=prior_summary==json.loads(sp.read_text())
        invariant=all(c['initial_decision']['elapsed_days'] is None or (
            c['initial_decision']['elapsed_days']<=c['last_decision']['elapsed_days']<=c['modeled_work_end']['elapsed_days'])
            for c in (r['event_clocks'] for r in new))
        result[pid]=dict(n=len(records),all_legacy_record_fields_unchanged=same_records,
            all_legacy_summary_fields_unchanged=same_summary,clock_ordering_valid=invariant,
            new_clock_summaries=summary['event_clock_summaries'],
            observed_first_visit_clocks=summary['observed_first_visit_clocks'],
            observed_rework=summary['observed_rework'])
    write(out/'verification.json',result)
    source=pathlib.Path(__file__).resolve().parents[2]/'benchmark/synth/generator/simulate.py'
    write(out/'manifest.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        existing_world_modified=False,inference_input=False,
        input_sha256={str(p):digest(p.read_bytes()) for p in paths},
        generator_source_sha256=digest(source.read_bytes()),source_sha256=digest(pathlib.Path(__file__).read_bytes())))
    print(json.dumps(result),flush=True)
    if not all(r['all_legacy_record_fields_unchanged'] and r['all_legacy_summary_fields_unchanged']
               and r['clock_ordering_valid'] for r in result.values()):
        raise ValueError('Clock extension failed a legacy-value or ordering check; see preserved report')


if __name__=='__main__':
    main()
