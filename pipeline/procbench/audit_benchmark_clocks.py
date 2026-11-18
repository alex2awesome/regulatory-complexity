"""Read-only benchmark clock/cohort audit, deliberately separate from inference.

Does NOT replace legacy scores. First-decision times on the legacy final-decided
cohort are diagnostic alternative estimands, not a newly held-out evaluation.
"""
import argparse
from datetime import date,datetime,timezone
import json
import pathlib

import numpy as np

from .infra.manifest import digest, write


def decision_activity_ids(process):
    return {a['id'] for a in process['activities'] if a.get('element_ref')
        and a['element_ref'].startswith('E') and a['visibility']=='applicant_facing'
        and process['terminal_artifact'] in a['artifacts_out']}


def record_clocks(process,record):
    ids=decision_activity_ids(process)
    decisions=[step for step in record['path'] if step['a'] in ids]
    if not decisions:
        return None
    start=date.fromisoformat(record['arrived'])
    ends=[date.fromisoformat(step['e']) for step in decisions]
    return dict(first_decision_date=ends[0].isoformat(),last_decision_date=ends[-1].isoformat(),
                first_decision_days=(ends[0]-start).days,last_decision_days=(ends[-1]-start).days,
                decision_visits=len(decisions))


def summarize(values):
    values=np.asarray(values,dtype=float)
    return dict(n=len(values),median=float(np.median(values)) if len(values) else None,
                p90=float(np.quantile(values,.9)) if len(values) else None)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--world',required=True)
    ap.add_argument('--programs',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    world,out=pathlib.Path(args.world),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserving previous audit; choose a fresh directory')
    started=datetime.now(timezone.utc).isoformat()
    world_file=world/'world.json'
    as_of=json.loads(world_file.read_text())['knobs']['as_of']
    paths=[world_file]
    rows={}
    for pid in args.programs:
        pp=world/'truth/processes'/f'{pid}.json'
        lp=world/'truth/log'/f'{pid}.jsonl'
        sp=world/'truth/log'/f'{pid}.summary.json'
        paths.extend([pp,lp,sp])
        process=json.loads(pp.read_text())
        records=[json.loads(line) for line in lp.read_text().splitlines() if line.strip()]
        legacy=json.loads(sp.read_text())
        clocks=[(record,record_clocks(process,record)) for record in records]
        same=[(r,c) for r,c in clocks if not r['censored'] and r['outcome'] in {'approved','denied'}]
        if any(c is None for _,c in same):
            raise ValueError('Decided legacy case has no identifiable decision visit: '+pid)
        first_observed=[c for _,c in clocks if c is not None and c['first_decision_date']<=as_of]
        rows[pid]=dict(legacy_elapsed_days=legacy['elapsed_days'],
            n_uncensored_including_abandoned=legacy['n_completed'],
            repeated_decision_cases_all=sum(c is not None and c['decision_visits']>1 for _,c in clocks),
            same_legacy_cohort=dict(n=len(same),
                first_decision=summarize([c['first_decision_days'] for _,c in same]),
                last_decision=summarize([c['last_decision_days'] for _,c in same]),
                legacy_record_matches_last_decision=all(r['elapsed_days']==c['last_decision_days'] for r,c in same)),
            first_decision_observed_cohort=summarize([c['first_decision_days'] for c in first_observed]),
            first_outcome_labels_not_recoverable_from_final_outcome_alone=True)
        spec=world/'specs'/f'{pid}__official_stats.json'
        if spec.exists():
            paths.append(spec)
            rows[pid]['existing_dashboard_timing_spec']=[r for r in json.loads(spec.read_text())['reveals'] if r['field']=='timing']
    write(out/'audit.json',dict(programs=rows,
        scope='development benchmark diagnosis; does not overwrite source data, estimators or previous scores',
        caveat='First versus final decisions also define different censoring/outcome cohorts; same-cohort alternatives are diagnostic only.'))
    write(out/'manifest.json',dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
        inference_input=False,source_sha256=digest(pathlib.Path(__file__).read_bytes()),
        input_sha256={str(p):digest(p.read_bytes()) for p in paths}))
    print(json.dumps(rows),flush=True)


if __name__=='__main__':
    main()
