"""Re-score saved episodes and join complexity; never overwrite inherited runs.

python -m benchmark.rulegap.reanalyse --runs <E1> <E3> --out <new-directory>
No network calls. Candidate-based endpoints are labelled explicitly.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .admissibility import catalog, digest
from .cases import sample_panel
from .cli import write_csv
from .harness.episode import classify_trace
from .metrics import measure
from .spec import load_spec


def sign_flip(deltas):
    """Two-sided case-blocked sign-flip sensitivity, not randomized assignment inference."""
    weights=Counter({0:1})
    for value in deltas:
        if not value:
            continue
        new=Counter()
        for subtotal,count in weights.items():
            new[subtotal+value]+=count
            new[subtotal-value]+=count
        weights=new
    observed=abs(sum(deltas))
    return sum(n for v,n in weights.items() if abs(v)>=observed)/sum(weights.values())


def summarize(rows):
    groups=defaultdict(list)
    keys=('experiment','rule_id','rung','arm','model','incentive')
    for r in rows:
        if not r['is_control']:
            groups[tuple(r[k] for k in keys)].append(r)
    out=[]
    for group,rs in sorted(groups.items()):
        row=dict(zip(keys,group)); n=len(rs)
        cells=Counter(r['reported_cell'] for r in rs)
        row.update(n_episodes=n,n_cases=len({r['case_id'] for r in rs}),
                   reading_scope='candidate',admissibility_validated=False,
                   validated_loopholes=None,validation_status='pending E0; bounded authored candidates')
        for cell in ['compliant','candidate_gap','plain_breach','purpose_serving_breach','drafting_failure',
                     'undefined','asked','no_action','error']:
            row[cell+'_n']=cells[cell]
            row[cell+'_rate']=cells[cell]/n
        for field in ['any_reference_violation','any_purpose_unwanted','completed','asked']:
            row[field+'_n']=sum(r.get(field) is True for r in rs)
            row[field+'_rate']=row[field+'_n']/n if any(r.get(field) is not None for r in rs) else None
        row['unsupported_number_episodes']=sum(r['n_unsupported_numbers']>0 for r in rs)
        out.append(row)
    return out


def contrasts(rows):
    groups=defaultdict(lambda:defaultdict(dict))
    for r in rows:
        if not r['is_control']:
            group=tuple(r[k] for k in ('experiment','rule_id','rung','arm','model'))
            groups[group][(r['case_id'],r['seed'])][r['incentive']]=r
    out=[]
    for group,pairs in sorted(groups.items()):
        for endpoint in ['any_candidate_gap','any_reference_violation','asked','any_purpose_unwanted']:
            deltas=defaultdict(int); n=excluded=0
            for (case,rep),p in pairs.items():
                if set(p)!={'none','conflicting'} or any(r['error'] for r in p.values()):
                    excluded+=1;continue
                deltas[case]+=int(bool(p['conflicting'][endpoint]))-int(bool(p['none'][endpoint]));n+=1
            out.append(dict(zip(('experiment','rule_id','rung','arm','model'),group)) |
                       dict(endpoint=endpoint,matched_pairs=n,excluded_pairs=excluded,n_cases=len(deltas),
                            incentive_difference=sum(deltas.values())/n if n else None,
                            case_blocked_sign_flip_p=sign_flip(deltas.values()) if n else None,
                            method='case-blocked sign-flip sensitivity; complete transport pairs; exploratory'))
    return out


def run(roots,out,refresh=False):
    out=Path(out)
    if out.resolve() in {Path(r).resolve() for r in roots}:
        raise ValueError('analysis output must be separate from input runs')
    if refresh and not (out/'manifest.json').exists():
        raise ValueError('refresh requires an existing generated analysis manifest')
    out.mkdir(parents=True,exist_ok=refresh)
    specs={}; rows=[]; inputs=[]; panels=defaultdict(dict); changes=[]
    for root in map(Path,roots):
        old={}
        if (root/'results.csv').exists():
            with (root/'results.csv').open(newline='') as f:
                old={tuple(r[k] for k in ('rule_id','rung','arm','model','incentive','case_id','seed')):r for r in csv.DictReader(f)}
        for path in sorted(root.glob('*/*/*/*/*/*.json')):
            if path.parts[-6]=='transport':continue
            raw=path.read_bytes();trace=json.loads(raw)
            rid=trace['rule_id']
            if rid not in specs:specs[rid]=load_spec(Path(__file__).parent/'specs'/f'{rid}.yaml')
            spec=specs[rid]
            if not trace['is_control']:
                case=dict(case_id=trace['case_id'],is_control=False,situation=trace['situation0'])
                if trace['case_id'] in panels[rid] and panels[rid][trace['case_id']]!=case:
                    raise ValueError('same case_id has different facts; cannot pool complexity panels')
                panels[rid][trace['case_id']]=case
            row={k:trace[k] for k in ('rule_id','rung','arm','model','incentive','case_id','seed','is_control')}
            row.update(experiment=root.name,**classify_trace(spec,trace))
            row['judge_verdict']=(trace.get('judge') or {}).get('verdict')
            rows.append(row)
            ident=tuple(str(row[k]) for k in ('rule_id','rung','arm','model','incentive','case_id','seed'))
            before=old.get(ident,{})
            if before.get('cell')!=row['cell']:
                changes.append({k:row[k] for k in ('experiment','rule_id','rung','arm','model','incentive','case_id','seed')} |
                               dict(old_cell=before.get('cell'),new_cell=row['reported_cell']))
            inputs.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        print(f'{root.name}: scored {sum(r["experiment"]==root.name for r in rows)} episodes',flush=True)
    write_csv(out/'episodes.csv',rows);write_csv(out/'classification_changes.csv',changes)
    summaries=summarize(rows); metric_rows=[]; by_metric={}
    for rid,rung,arm in sorted({(r['rule_id'],r['rung'],r['arm']) for r in rows}):
        spec=specs[rid]
        measurements=measure(spec,rung,arm,dict(declared=sample_panel(spec,'declared'),
                                               observed=list(panels[rid].values())))
        measurements['n_observed_cases']=len(panels[rid])
        metric_rows.append(measurements);by_metric[(rid,rung,arm)]=measurements
        print(f'measured {rid}/{rung}/{arm}',flush=True)
    joined=[r|by_metric[(r['rule_id'],r['rung'],r['arm'])] for r in summaries]
    write_csv(out/'complexity.csv',metric_rows)
    write_csv(out/'complexity_results.csv',joined)
    write_csv(out/'incentive_contrasts.csv',contrasts(rows))
    source_root=Path(__file__).parent
    snapshots=[]
    for path in sorted(source_root.rglob('*.py'))+sorted(source_root.rglob('*.yaml')):
        raw=path.read_bytes();target=out/'source'/path.relative_to(source_root)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        snapshots.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest()))
    meta=dict(created_utc=datetime.now(timezone.utc).isoformat(),n_episodes=len(rows),
        n_changed_cells=len(changes),inputs=inputs,source=snapshots,
        assumptions=['No human ratings exist: candidate gaps are not validated loopholes.',
                     'Numerical report and verdict must jointly match one interpretation.',
                     'Complexity measures use verdict-only candidate actions, not reported numerical errors.',
                     'Declared and observed stress-case distributions are reported separately.',
                     'Semantic complexity of extra drafting clauses is not modeled.',
                     'Rate denominators include all assigned test episodes; transport failures are reported separately.',
                     'No new model calls; original raw runs and summaries remain unchanged.'])
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(dict(n_episodes=len(rows),n_changed_cells=len(changes),out=str(out))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',nargs='+',required=True);p.add_argument('--out',required=True)
    p.add_argument('--refresh',action='store_true',help='Refresh this working analysis, never its input runs')
    a=p.parse_args();run(a.runs,a.out,a.refresh)
