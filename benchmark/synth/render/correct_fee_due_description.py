#!/usr/bin/env python3
"""Align C35's public fee-step label with its structured due event.

The sampled process contains one fee node whose structured ``when`` field says
``at issuance``.  This correction changes only the contradictory public label
``before review`` in that process node and the compact saved specifications.
It does not alter the fee object, process topology, timing, or sampled cases.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, lock, read, save, sha, stamp, state,
)

MODEL_ID = 'C35__S03'
ACTIVITY_ID = 'A03'
OLD = 'Pay the sidewalk vending permit fee before review'
NEW = 'Pay the sidewalk vending permit fee at issuance'
HOLD_ID = 'fee_due_description_conflict'


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


def replace_strings(value):
    if isinstance(value, str):
        return value.replace(OLD, NEW)
    if isinstance(value, list):
        return [replace_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item) for key, item in value.items()}
    return value


def stage(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing correction stage; choose a new directory')
    manifest = current_manifest(out)
    process_path = wd / 'truth/processes' / (MODEL_ID + '.json')
    process_before = read(process_path)
    matching = [a for a in process_before['activities'] if a['id'] == ACTIVITY_ID]
    if len(matching) != 1:
        raise ValueError('Expected exactly one C35 A03 process activity')
    activity = matching[0]
    if activity['local_name'] != OLD:
        raise ValueError('C35 A03 public label no longer matches the approved correction')
    if activity.get('fee') != {'amount': 194, 'when': 'at issuance',
                               'label': 'sidewalk vending permit'}:
        raise ValueError('C35 A03 structured fee is not the approved single-fee source')

    process_after = deepcopy(process_before)
    after_activity = next(a for a in process_after['activities'] if a['id'] == ACTIVITY_ID)
    after_activity['local_name'] = NEW
    process_check = deepcopy(process_after)
    next(a for a in process_check['activities'] if a['id'] == ACTIVITY_ID)['local_name'] = OLD
    if process_check != process_before:
        raise ValueError('Correction attempted a process mutation beyond the public label')

    changes = []
    process_relative = 'truth/processes/' + MODEL_ID + '.json'
    process_before_bytes = process_path.read_bytes()
    process_after_bytes = (json.dumps(process_after, indent=2, ensure_ascii=False) + '\n').encode()
    write_new(dest / 'before' / process_relative, process_before_bytes)
    write_new(dest / 'after' / process_relative, process_after_bytes)
    changes.append(dict(kind='process', id=MODEL_ID, path=process_relative,
        before_sha256=sha(process_before_bytes), after_sha256=sha(process_after_bytes),
        replacements=1))

    affected = []
    for aid in sorted(manifest['artifacts']):
        if not (aid.startswith(MODEL_ID + '__') or aid == 'C35__generic_permits_page'):
            continue
        spec_path = wd / 'specs' / (aid + '.json')
        before_bytes = spec_path.read_bytes()
        before = json.loads(before_bytes)
        serialized = json.dumps(before, ensure_ascii=False)
        if OLD not in serialized:
            continue
        after = replace_strings(before)
        after_bytes = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
        relative = 'specs/' + aid + '.json'
        write_new(dest / 'before' / relative, before_bytes)
        write_new(dest / 'after' / relative, after_bytes)
        write_new(dest / 'before' / 'artifacts' / (aid + '.md'),
                  (wd / 'artifacts' / (aid + '.md')).read_bytes())
        replacements = serialized.count(OLD)
        changes.append(dict(kind='spec', id=aid, path=relative,
            before_sha256=sha(before_bytes), after_sha256=sha(after_bytes),
            replacements=replacements))
        affected.append(aid)
    if len(affected) != 7:
        raise ValueError(f'Expected seven compact affected specs, found {len(affected)}: {affected}')

    protected_paths = [wd / 'world.json'] + sorted(
        p for p in (wd / 'truth').rglob('*')
        if p.is_file() and p != process_path)
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths}
    plan = dict(schema_version='approved-fee-due-description-correction/1',
        staged_utc=stamp(), world=wd.name, changes=changes,
        affected_artifacts=affected, protected_sha256=protected,
        structured_fee_changed=False, process_graph_structure_changed=False,
        process_timing_or_case_files_changed=False,
        approval=('Alex approved correcting the single contradictory C35 A03 public fee-step '
                  'label to match the unambiguous structured due event at issuance, while '
                  'preserving the fee object, operational graph, timings, and case draws.'),
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
                raise ValueError('Correction target changed after staging: ' + record['id'])
            if file_sha(dest / 'after' / record['path']) != record['after_sha256']:
                raise ValueError('Staged replacement changed: ' + record['id'])

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
            if record['kind'] == 'spec':
                revised['artifacts'][record['id']]['spec_sha256'] = record['after_sha256']
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected file changed during apply: ' + relative)
        save(out / 'manifest_revisions' / (revision + '.json'), revised)

        holds_path = out / 'release_holds.json'
        before_holds = holds_path.read_bytes()
        write_new(dest / 'before' / 'release_holds.json', before_holds)
        holds = json.loads(before_holds)
        if any(hold['id'] == HOLD_ID for hold in holds):
            raise ValueError('Fee due-description hold already exists')
        holds.append(dict(id=HOLD_ID, status='resolved', programs=[MODEL_ID],
            artifacts=sorted(affected), correction_plan=str(dest / 'plan.json'),
            reason=('The single contradictory C35 A03 public label now says at issuance, '
                    'matching its structured fee due event. Fee object, graph structure, '
                    'timing, and sampled cases are unchanged.')))
        holds_path.write_text(json.dumps(holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            changed_process_labels=1, changed_specs=len(affected),
            rerender_required=len(affected), prior_rerender_pending=len(old_pending),
            protected_files_unchanged=len(plan['protected_sha256']),
            structured_fee_changed=False, process_graph_structure_changed=False,
            process_timing_or_case_files_changed=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_fee_due_description_correction',
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
