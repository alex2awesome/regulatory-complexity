"""python -m benchmark.rulegap.cli <validate|measure|readings|search|run|classify|table> ..."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys
import shutil

from . import dsl
from .arms import ARMS
from .cases import sample_panel
from .compile import classify
from .metrics import columns, measure_all
from .readings import evaluate_panel, live_readings
from .render import check_render
from .search import ExhaustiveSolver, get_solver
from .spec import load_spec

CELLS = ['compliant', 'candidate_gap', 'loophole', 'purpose_serving_breach', 'plain_breach', 'drafting_failure', 'undefined',
         'asked', 'no_action', 'error']


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = columns(rows)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def witness_situation(spec, w):
    return spec.domain['build_case'](**spec.raw['witness_cases'][w['case']]['build'])


def validate(spec):
    """Scripted check for a spec: expressions, witnesses, parse-back for every
    rung x arm, and solver agreement on witness cases where the domain has both."""
    problems = []
    for t in spec.terms.values():
        for r in t['readings'].values():
            dsl.check(r['expr'])
    for rung in spec.rungs:
        dsl.check(spec.skeleton(rung)['legal'])
        for arm in ARMS:
            if arm == 'safe_harbor' and 'arm_text' not in spec.raw:
                continue
            check_render(spec, rung, arm)
    for w in spec.raw.get('witnesses', []):
        c = classify(spec, w.get('rung', 'open'), witness_situation(spec, w), w['action'])
        for k, want in w['expect'].items():
            got = c.get(k)
            if k == 'consistent':
                got = {t: sorted({a[t] for a in c['consistent_readings']}) for t in want}
            if got != want:
                problems.append(f"witness {w['case']} {w['action']}: {k} = {got!r}, expected {want!r}")
    if 'text_source' in spec.raw:
        from .real import check_sources
        problems += check_sources(spec)
    if 'action_grid' in spec.domain and 'z3_model' in spec.domain:
        fast = get_solver('auto')
        if fast.name == 'z3':
            for name in spec.raw.get('witness_cases', {}):
                sit = spec.domain['build_case'](**spec.raw['witness_cases'][name]['build'])
                a, b = ExhaustiveSolver().loophole(spec, 'open', sit), fast.loophole(spec, 'open', sit)
                if (a is None) != (b is None) or (a and a['strain'] != b['strain']):
                    problems.append(f'solvers disagree on {name}: exhaustive {a}, z3 {b}')
    return problems


def cmd_validate(args):
    bad = 0
    for path in args.spec:
        problems = validate(load_spec(path))
        bad += bool(problems)
        print(f"{path}: {'OK' if not problems else 'FAILED'}")
        for p in problems:
            print('  ' + p)
    return 1 if bad else 0


def cmd_measure(args):
    spec = scoped_spec(args)
    panels = {w: sample_panel(spec, w) for w in ('declared', 'stress') if w in spec.raw['cases']}
    rows = measure_all(spec, args.arms.split(','), panels)
    for r in rows:      # check at creation: a fully settled rung has one reading
        if r['rung'] == 'fully_settled' and r['adm_size_with_grid'] != 1:
            raise ValueError('fully_settled rung has more than one admissible reading')
    out = Path(args.out) / f'{spec.rule_id}_measures.csv'
    write_csv(out, rows)
    print(out)
    return 0


def cmd_readings(args):
    spec = scoped_spec(args)
    records = evaluate_panel(spec, args.rung, sample_panel(spec, 'declared'))
    rows = live_readings(spec, args.rung, records, args.mass)
    out = Path(args.out) / f'{spec.rule_id}_{args.rung}_readings.csv'
    write_csv(out, rows)
    print(out, f"{sum(r['live'] for r in rows)} live classes of {len(rows)}")
    return 0


def cmd_search(args):
    spec = scoped_spec(args)
    sit = spec.domain['build_case'](**spec.raw['witness_cases'][args.case]['build'])
    solver = get_solver(args.solver)
    if args.conflict:
        if spec.reading_scope == 'validated':
            raise ValueError('validated multi-rule conflicts need separately reviewed catalogs for each rule')
        other = load_spec(args.conflict)
        result = solver.conflict([spec, other], [args.rung, 'open'], sit)
    else:
        result = solver.loophole(spec, args.rung, sit)
    print(json.dumps(dict(solver=solver.name, reading_scope=spec.reading_scope,
                          admissibility_validated=spec.reading_scope=='validated', result=result), indent=1))
    return 0


def cmd_e0_packet(args):
    from .real import rater_packet
    spec = load_spec(args.spec)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rater_packet(spec, args.rung))
    print(out)
    return 0


def scoped_spec(args):
    spec = load_spec(args.spec)
    scope = args.reading_scope or ('sourced' if 'text_source' in spec.raw else 'candidate')
    return load_spec(args.spec, reading_scope=scope, ratings_path=args.ratings,
                     rating_arm=getattr(args, 'arms', 'control'))


def cmd_e0_build(args):
    from .admissibility import write_packet, behavioral_audit
    spec=load_spec(args.spec)
    cat = write_packet(spec, args.rung, args.out, args.arm)
    if args.behavioral_panel:
        audit=behavioral_audit(spec,args.rung,sample_panel(spec,'declared')+sample_panel(spec,'stress'))
        (Path(args.out)/'behavioral_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(dict(canonical_candidates=len(cat['candidates']), catalog_digest=cat['catalog_digest'],
                          human_ratings=0, status='pending', out=args.out)))
    return 0


def cmd_e0_audit(args):
    from .admissibility import audit_ratings
    cat = json.loads(Path(args.catalog).read_text())
    rows = []
    for path in args.ratings:
        with Path(path).open(newline='') as f:
            rows.extend(csv.DictReader(f))
    result = audit_ratings(cat, rows)
    Path(args.out).write_text(json.dumps(result, indent=2)+'\n')
    write_csv(Path(args.out).with_suffix('.ratings.csv'),rows)
    print(json.dumps({k:v for k,v in result.items() if k not in ('accepted','rejected','pending')},indent=2))
    return 0


# --- runs ----------------------------------------------------------------

def _git_head():
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    except Exception:
        return None


def cmd_run(args):
    from pipeline.procbench.infra.manifest import digest, write
    from .harness.episode import run_episode
    from .harness.model import get_model
    from .harness.probes import judge_probe
    spec = scoped_spec(args)
    if spec.reading_scope != 'validated' and not args.exploratory:
        raise ValueError('E0 is not validated. Use --exploratory for an explicitly candidate-based pilot, '
                         'or --reading-scope validated --ratings <completed ratings.csv>.')
    if spec.reading_scope == 'validated':
        if ',' in args.rungs or ',' in args.arms:
            raise ValueError('validated runs require one exact rung and arm per ratings catalog')
        spec.admissible(args.rungs)
        if spec.validation_audit['status'] != 'complete':
            raise ValueError('confirmatory run requires a fully reviewed frozen candidate catalog')
    root = Path(args.out) / args.experiment
    # Case sampling is fixed across interpretation scopes, including control rejection.
    panel_spec=load_spec(args.spec)
    cases = sample_panel(panel_spec, args.panel, n=args.n_cases) + sample_panel(panel_spec, 'controls', n=args.n_controls)
    snapshots={}
    for label,path in [('spec',spec.path),('ratings',spec.ratings_path)]:
        if path is None:continue
        raw=Path(path).read_bytes()
        relative=Path('inputs')/digest(raw)/f'{label}{Path(path).suffix}'
        dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=raw:
            raise ValueError('input snapshot collision')
        dest.write_bytes(raw);snapshots[label+'_snapshot']=str(relative)
        if label=='spec' and 'text_source' in spec.raw:
            shutil.copytree(spec.path.parent/'sources',dest.parent/'sources',dirs_exist_ok=True)
    jobs = []
    for rung in args.rungs.split(','):
        for arm in args.arms.split(','):
            check_render(spec, rung, arm)
            for name in args.models.split(','):
                for inc in args.incentives.split(','):
                    for case in cases:
                        for seed in range(args.seeds):
                            jobs.append((rung, arm, name, inc, case, seed))
    manifest = dict(experiment=args.experiment, rule_id=spec.rule_id, spec_sha256=digest(spec.path.read_bytes()),
        git_head=_git_head(), argv=sys.argv[1:], started_utc=datetime.now(timezone.utc).isoformat(),
        n_jobs=len(jobs), panel=args.panel, n_cases=args.n_cases, n_controls=args.n_controls,
        reading_scope=spec.reading_scope, exploratory=args.exploratory,
        input_snapshots=snapshots,
        notes=['CLI transports; no sampling seed, seed is a replicate index',
               'codex keeps its own system prompt; claude runs with ours in place of its default'])
    mpath = root / f'{spec.rule_id}_manifest_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json'
    write(mpath, manifest)
    models = {}

    def one(job):
        rung, arm, name, inc, case, seed = job
        safe = name.replace(':', '_').replace('/', '_')
        path = root / spec.rule_id / rung / arm / safe / inc / f"{case['case_id']}_{seed}.json"
        if path.exists():
            existing=json.loads(path.read_text())
            if any(existing.get(k)!=v for k,v in snapshots.items()) or existing.get('reading_scope')!=spec.reading_scope:
                raise ValueError('existing episodes use different inputs/scope; select a new experiment directory')
            return 'kept'
        model = models.setdefault(name, get_model(name))
        tdir = root / 'transport' / spec.rule_id / rung / arm / safe / inc
        stem = f"{case['case_id']}_{seed}"
        trace = run_episode(spec, rung, arm, case, inc, model, seed, tdir, stem)
        trace.update(snapshots)
        if args.judge and not trace['error']:
            trace['judge'] = judge_probe(spec, trace, model, tdir, stem + '_judge')
        write(path, trace)
        return 'error' if trace['error'] else 'ok'
    with ThreadPoolExecutor(args.workers) as pool:
        counts = Counter(pool.map(one, jobs))
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(), outcomes=dict(counts))
    write(mpath, manifest)
    print(dict(counts), root)
    return 0


def cmd_classify(args):
    from .harness.episode import classify_trace
    root = Path(args.run)
    specs, rows = {}, []
    for path in sorted(root.glob('*/*/*/*/*/*.json')):
        if path.parts[-6] == 'transport':
            continue
        trace = json.loads(path.read_text())
        spec_path=(root/trace['spec_snapshot'] if 'spec_snapshot' in trace else
                   Path(__file__).parent / 'specs' / f"{trace['rule_id']}.yaml")
        scope=trace.get('reading_scope','candidate')
        spec_key=(str(spec_path),scope,trace.get('ratings_snapshot'),trace.get('arm'))
        if spec_key not in specs:
            specs[spec_key]=load_spec(spec_path,reading_scope=scope,
                ratings_path=root/trace['ratings_snapshot'] if trace.get('ratings_snapshot') else None,
                rating_arm=trace.get('rating_arm','control'))
        spec=specs[spec_key]
        row = {k: trace[k] for k in ('rule_id', 'rung', 'arm', 'model', 'incentive', 'seed', 'case_id', 'is_control')}
        row.update(classify_trace(spec, trace))
        row['mechanical_cell']=row['cell']
        row['cell']=row['reported_cell']
        row['judge_verdict'] = (trace.get('judge') or {}).get('verdict')
        row['cost_usd'] = trace['cost_usd'] + ((trace.get('judge') or {}).get('cost_usd') or 0)
        rows.append(row)
    write_csv(root / 'results.csv', rows)
    print(root / 'results.csv', len(rows), 'episodes')
    return 0


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def cmd_table(args):
    root = Path(args.run)
    rows = list(csv.DictReader((root / 'results.csv').open()))
    for r in rows:
        if r['cell']=='loophole' and r.get('reading_scope','candidate')!='validated':
            r['cell']='candidate_gap'
    groups = defaultdict(list)
    for r in rows:
        groups[(r['rule_id'], r['rung'], r['arm'], r['model'], r['incentive'])].append(r)
    out = []
    for (rule, rung, arm, model, inc), rs in sorted(groups.items()):
        test = [r for r in rs if r['is_control'] == 'False']
        ctrl = [r for r in rs if r['is_control'] == 'True']
        n = len(test)
        counts = Counter(r['cell'] for r in test)
        lo, hi = wilson(counts['loophole']+counts['candidate_gap'], n)
        row = dict(rule_id=rule, rung=rung, arm=arm, model=model, incentive=inc, n=n)
        row.update(reading_scope=rs[0].get('reading_scope','candidate'),
                   admissibility_validated=all(r.get('reading_scope')=='validated' for r in rs))
        row.update({c: round(counts[c] / n, 3) if n else None for c in CELLS})
        strains = [int(r['strain']) for r in test if r['cell'] in ('loophole','candidate_gap') and r['strain']]
        judged = [r for r in test if r['judge_verdict'] and r['cell'] in ('compliant', 'loophole','candidate_gap', 'plain_breach')]
        agree = sum((r['judge_verdict'] == 'permitted') == (r['cell'] == 'compliant') for r in judged)
        row.update(gap_wilson_lo_ignoring_case_clustering=round(lo, 3) if n else None,
            gap_wilson_hi_ignoring_case_clustering=round(hi, 3) if n else None,
            mean_strain=round(sum(strains) / len(strains), 2) if strains else None,
            flagged=round(sum(r['flagged'] == 'True' for r in test) / n, 3) if n else None,
            awareness=round(sum(r['awareness'] == 'True' for r in test) / n, 3) if n else None,
            completed=round(sum(r['completed'] == 'True' for r in test) / n, 3) if n else None,
            judge_says_permitted_given_gap=_share([r['judge_verdict'] == 'permitted' for r in judged if r['cell'] in ('loophole','candidate_gap')]),
            judge_agrees_with_classifier=round(agree / len(judged), 3) if judged else None,
            n_control=len(ctrl), control_compliant=_share([r['cell'] == 'compliant' for r in ctrl]),
            cost_usd=round(sum(float(r['cost_usd'] or 0) for r in rs), 2))
        out.append(row)
    write_csv(root / 'table.csv', out)
    cols = ['rule_id', 'rung', 'arm', 'model', 'incentive', 'n','reading_scope', 'compliant','candidate_gap', 'loophole', 'plain_breach',
            'drafting_failure', 'undefined', 'asked', 'no_action', 'error', 'control_compliant']
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    lines += ['| ' + ' | '.join(str(r[c]) for c in cols) + ' |' for r in out]
    (root / 'table.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0


def _share(xs):
    return round(sum(xs) / len(xs), 3) if xs else None


def main(argv=None):
    ap = argparse.ArgumentParser(prog='benchmark.rulegap.cli')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('validate'); p.add_argument('spec', nargs='+'); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser('measure'); p.add_argument('spec'); p.add_argument('--out', required=True)
    p.add_argument('--arms', default='control'); p.set_defaults(fn=cmd_measure)
    p.add_argument('--reading-scope', choices=['candidate','sourced','validated']); p.add_argument('--ratings')
    p = sub.add_parser('readings'); p.add_argument('spec'); p.add_argument('--rung', default='open')
    p.add_argument('--mass', type=float, default=0.95); p.add_argument('--out', required=True); p.set_defaults(fn=cmd_readings)
    p.add_argument('--reading-scope', choices=['candidate','sourced','validated']); p.add_argument('--ratings')
    p = sub.add_parser('search'); p.add_argument('spec'); p.add_argument('--rung', default='open')
    p.add_argument('--reading-scope', choices=['candidate','sourced','validated']); p.add_argument('--ratings')
    p.add_argument('--case', required=True); p.add_argument('--conflict'); p.add_argument('--solver', default='auto')
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser('run'); p.add_argument('spec'); p.add_argument('--experiment', required=True)
    p.add_argument('--models', required=True); p.add_argument('--rungs', default='open')
    p.add_argument('--arms', default='control'); p.add_argument('--incentives', default='none,conflicting')
    p.add_argument('--panel', default='stress'); p.add_argument('--n-cases', type=int, default=40)
    p.add_argument('--n-controls', type=int, default=5); p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--workers', type=int, default=6); p.add_argument('--judge', action='store_true')
    p.add_argument('--reading-scope', choices=['candidate','sourced','validated']); p.add_argument('--ratings')
    p.add_argument('--exploratory', action='store_true', help='Explicitly permit a pilot without completed E0 validation')
    p.add_argument('--out', required=True); p.set_defaults(fn=cmd_run)
    p = sub.add_parser('e0-packet'); p.add_argument('spec'); p.add_argument('--rung', default='open')
    p.add_argument('--out', required=True); p.set_defaults(fn=cmd_e0_packet)
    p = sub.add_parser('e0-build'); p.add_argument('spec'); p.add_argument('--rung', default='open')
    p.add_argument('--behavioral-panel', action='store_true')
    p.add_argument('--arm', default='control'); p.add_argument('--out', required=True); p.set_defaults(fn=cmd_e0_build)
    p = sub.add_parser('e0-audit'); p.add_argument('catalog'); p.add_argument('--ratings', nargs='+', required=True)
    p.add_argument('--out', required=True); p.set_defaults(fn=cmd_e0_audit)
    p = sub.add_parser('classify'); p.add_argument('run'); p.set_defaults(fn=cmd_classify)
    p = sub.add_parser('table'); p.add_argument('run'); p.set_defaults(fn=cmd_table)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    sys.exit(main())
