#!/usr/bin/env python3
"""Align approved public appeal-body choices with sampled process authority.

This correction covers only the 23 compact programs that do not overlap the
concurrent legacy-render hold.  It changes the current C4/C5 choice and the
matching drafting clause to ``Zoning Administrator``.  Prior-version history,
process graphs, timings, fees, and sampled cases remain unchanged.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, lock, read, save, sha, stamp, state,
)

HOLD_ID = 'appeal_rule_process_authority'
NEW_AUTHORITY = 'Zoning Administrator'
LAW_RESTATING = {'ordinance', 'fee_resolution', 'staff_report', 'council_minutes'}
PROGRAMS = (
    'C03__S12', 'C07__S12', 'C16__S12', 'C19__S12', 'C22__S12',
    'C41__S12', 'C45__S12', 'C55__S12', 'C56__S12', 'C57__S12',
    'C02__S03', 'C08__S03', 'C11__S03', 'C23__S03', 'C25__S03',
    'C32__S03', 'C33__S03', 'C36__S03', 'C37__S03', 'C38__S03',
    'C42__S03', 'C44__S03', 'C45__S03',
)
DEFERRED_PROGRAMS = ('C50__S03', 'C51__S03', 'C52__S03', 'C57__S03', 'C58__S03')


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)


def target(wd, relative):
    result = wd / relative
    if wd.resolve() not in result.resolve().parents:
        raise ValueError('Correction target escapes world directory: ' + relative)
    return result


def appeal_choice_id(model_id):
    return 'C5' if model_id.endswith('__S12') else 'C4'


def sampled_appeal_activity(process):
    matches = [a for a in process['activities']
               if a.get('counterparty') == 'hearing'
               and a.get('actor') == 'applicant'
               and a.get('flow_gate') == 'if_appealed'
               and 'counterparty: Zoning Administrator' in (a.get('notes') or '')]
    if len(matches) != 1:
        raise ValueError('Expected one sampled Zoning Administrator appeal activity')
    return matches[0]


def affected_artifacts(wd, manifest):
    result = []
    for aid in manifest['artifacts']:
        if not any(aid.startswith(model_id + '__') for model_id in PROGRAMS):
            continue
        if read(wd / 'specs' / (aid + '.json'))['kind'] in LAW_RESTATING:
            result.append(aid)
    return sorted(result)


def stage(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing correction stage; choose a new directory')
    manifest = current_manifest(out)
    holds = read(out / 'release_holds.json')
    hold = next(h for h in holds if h['id'] == HOLD_ID and h['status'] == 'open')
    if set(hold['programs']) != set(PROGRAMS) | set(DEFERRED_PROGRAMS):
        raise ValueError('Appeal hold no longer matches the approved 28-program set')

    changes = []
    target_relatives = set()
    for model_id in PROGRAMS:
        process = read(wd / 'truth/processes' / (model_id + '.json'))
        appeal = sampled_appeal_activity(process)
        choice_id = appeal_choice_id(model_id)
        path = wd / 'truth/local_rules' / (model_id + '.json')
        before = read(path)
        old_authority = before['choices'][choice_id]
        if old_authority == NEW_AUTHORITY:
            raise ValueError('Appeal choice already corrected: ' + model_id)
        clause = f'{choice_id} = {old_authority};'
        if before['text_spec'].count(clause) != 1:
            raise ValueError('Unexpected appeal drafting clause: ' + model_id)

        after = deepcopy(before)
        after['choices'][choice_id] = NEW_AUTHORITY
        after['text_spec'] = before['text_spec'].replace(
            clause, f'{choice_id} = {NEW_AUTHORITY};')
        check = deepcopy(after)
        check['choices'][choice_id] = old_authority
        check['text_spec'] = before['text_spec']
        if check != before:
            raise ValueError('Correction attempted a local-rule mutation beyond appeal prose')
        if after.get('prior_version') != before.get('prior_version'):
            raise ValueError('Correction attempted to revise prior-version history')

        before_bytes = path.read_bytes()
        after_bytes = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
        relative = 'truth/local_rules/' + model_id + '.json'
        target_relatives.add(relative)
        write_new(dest / 'before' / relative, before_bytes)
        write_new(dest / 'after' / relative, after_bytes)
        changes.append(dict(model_id=model_id, path=relative,
            choice_id=choice_id, old_authority=old_authority,
            new_authority=NEW_AUTHORITY, appeal_activity_id=appeal['id'],
            appeal_activity_notes=appeal['notes'],
            before_sha256=sha(before_bytes), after_sha256=sha(after_bytes),
            prior_version_changed=False))

    affected = affected_artifacts(wd, manifest)
    if len(affected) != 43:
        raise ValueError(f'Expected 43 compact law/restating artifacts, found {len(affected)}')
    concurrent = next(h for h in holds if h['id'] == 'concurrent_legacy_render')
    overlap = set(affected) & set(concurrent.get('artifacts', []))
    if overlap:
        raise ValueError('Safe appeal subset overlaps concurrent hold: ' + repr(sorted(overlap)))
    for aid in affected:
        write_new(dest / 'before' / 'artifacts' / (aid + '.md'),
                  (wd / 'artifacts' / (aid + '.md')).read_bytes())

    protected_paths = [wd / 'world.json'] + sorted(
        p for p in (wd / 'truth').rglob('*')
        if p.is_file() and str(p.relative_to(wd)) not in target_relatives)
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths}
    plan = dict(schema_version='approved-appeal-authority-correction/1',
        staged_utc=stamp(), world=wd.name, changes=changes,
        affected_artifacts=affected, deferred_programs=list(DEFERRED_PROGRAMS),
        protected_sha256=protected, prior_versions_changed=False,
        process_graphs_changed=False, fees_changed=False,
        process_timing_or_case_files_changed=False,
        approval=('Alex approved correcting conflicting public appeal-body descriptions '
                  'to match sampled operational graphs. This stage excludes five programs '
                  'whose exact artifacts remain under the concurrent legacy-render hold.'),
        parent_manifest_sha256=sha(json.dumps(manifest, sort_keys=True)))
    save(dest / 'plan.json', plan)
    return plan


def apply(wd, out, dest):
    plan = read(dest / 'plan.json')
    if (dest / 'applied.json').exists():
        raise ValueError('Correction already applied; preserve its receipt')
    with lock(out):
        manifest = current_manifest(out)
        if sha(json.dumps(manifest, sort_keys=True)) != plan['parent_manifest_sha256']:
            raise ValueError('Manifest changed after staging')
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected world/truth file changed: ' + relative)
        for record in plan['changes']:
            path = target(wd, record['path'])
            if file_sha(path) != record['before_sha256']:
                raise ValueError('Correction target changed after staging: ' + record['model_id'])
            if file_sha(dest / 'after' / record['path']) != record['after_sha256']:
                raise ValueError('Staged replacement changed: ' + record['model_id'])

        prior = state(wd, out, manifest)
        old_pending = {aid for aid, row in prior['artifacts'].items()
                       if row['status'] == 'rerender_pending'}
        revised = deepcopy(manifest)
        revision = f"{len(list((out / 'manifest_revisions').glob('*.json'))) + 1:04d}"
        affected = set(plan['affected_artifacts'])
        revised.update(correction_revision=revision,
            correction_plan=str(dest / 'plan.json'),
            requires_rerender_ids=sorted(old_pending | affected),
            requires_fresh_review_ids=sorted(
                set(manifest.get('requires_fresh_review_ids', [])) | affected))
        for record in plan['changes']:
            target(wd, record['path']).write_bytes(
                (dest / 'after' / record['path']).read_bytes())
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected file changed during apply: ' + relative)
        save(out / 'manifest_revisions' / (revision + '.json'), revised)

        holds_path = out / 'release_holds.json'
        before_holds = holds_path.read_bytes()
        write_new(dest / 'before' / 'release_holds.json', before_holds)
        holds = json.loads(before_holds)
        for hold in holds:
            if hold['id'] == HOLD_ID:
                hold['programs'] = list(DEFERRED_PROGRAMS)
                hold['reason'] = ('Approved appeal-body descriptions corrected for 23 of 28 '
                    'programs; five S03 programs remain deferred because their exact compact '
                    'artifacts are under concurrent_legacy_render. Process graphs, prior-version '
                    'history, fees, timings, and sampled cases are unchanged.')
                hold['partial_correction_plan'] = str(dest / 'plan.json')
        holds_path.write_text(json.dumps(holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            changed_local_rules=len(plan['changes']), corrected_programs=len(PROGRAMS),
            deferred_programs=len(DEFERRED_PROGRAMS), rerender_required=len(affected),
            prior_rerender_pending=len(old_pending),
            protected_files_unchanged=len(plan['protected_sha256']),
            prior_versions_changed=False, process_graphs_changed=False,
            fees_changed=False, process_timing_or_case_files_changed=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_appeal_authority_correction',
            correction_archive=str(dest), no_cases_resimulated=True, **receipt))
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['stage', 'apply'])
    parser.add_argument('--world', default='W2_DEV_001')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--correction', type=Path, required=True)
    args = parser.parse_args()
    wd = ROOT / 'benchmark/synth/worlds' / args.world
    result = (stage if args.action == 'stage' else apply)(wd, args.out, args.correction)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {'changes', 'protected_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
