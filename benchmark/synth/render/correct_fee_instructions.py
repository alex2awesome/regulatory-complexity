#!/usr/bin/env python3
"""Correct nine fee drafting instructions while preserving fee provenance.

The structured fee amount, derivation, due event, and adopted_by fields remain
unchanged.  Only contradictory public drafting prose is corrected: an amount
recorded as administratively set/not found in an adopted instrument must not be
instructed as adopted by that instrument.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, lock, read, save, sha, stamp, state,
)

HOLD_ID = 'fee_adoption_instruction_conflict'
LAW_RESTATING = {'ordinance', 'fee_resolution', 'staff_report', 'council_minutes'}


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


def corrected_instruction(rule):
    amount = rule['choices']['C1']
    derivation = rule['fee']['derivation']
    text = rule['text_spec']
    old_set = f'set the fee at {amount} ({derivation})'
    new_set = (f'state the current administratively set fee as {amount} ({derivation}) '
               'for public information, but do not adopt it in this instrument')
    old_choice = f'adopt the choices C1 = {amount}; C2 ='
    new_choice = (f'preserve C1 = {amount} only as the current administratively set amount, '
                  'not as an adopted choice; adopt the choices C2 =')
    if text.count(old_set) != 1 or text.count(old_choice) != 1:
        raise ValueError('Unexpected fee drafting instruction: ' + rule['model_id'])
    return text.replace(old_set, new_set).replace(old_choice, new_choice)


def affected_artifacts(wd, manifest, programs):
    result = []
    for aid in manifest['artifacts']:
        if not any(aid.startswith(mid + '__') for mid in programs):
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
    programs = sorted(hold['programs'])
    changes = []
    target_relatives = set()
    for mid in programs:
        path = wd / 'truth/local_rules' / (mid + '.json')
        before = read(path)
        if 'NOT FOUND in any adopted instrument' not in before['fee']['adopted_by']:
            raise ValueError('Structured fee provenance no longer matches hold: ' + mid)
        after = deepcopy(before)
        after['text_spec'] = corrected_instruction(before)
        check = deepcopy(after)
        check['text_spec'] = before['text_spec']
        if check != before:
            raise ValueError('Correction attempted a structured fee mutation: ' + mid)
        before_bytes = path.read_bytes()
        after_bytes = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
        relative = 'truth/local_rules/' + mid + '.json'
        target_relatives.add(relative)
        write_new(dest / 'before' / relative, before_bytes)
        write_new(dest / 'after' / relative, after_bytes)
        changes.append(dict(model_id=mid, path=relative, before_sha256=sha(before_bytes),
            after_sha256=sha(after_bytes), fee=before['fee']))
    affected = affected_artifacts(wd, manifest, programs)
    for aid in affected:
        write_new(dest / 'before' / 'artifacts' / (aid + '.md'),
                  (wd / 'artifacts' / (aid + '.md')).read_bytes())
    protected_paths = [wd / 'world.json'] + sorted(p for p in (wd / 'truth').rglob('*')
                                                   if p.is_file() and str(p.relative_to(wd)) not in target_relatives)
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths}
    plan = dict(schema_version='approved-fee-instruction-correction/1', staged_utc=stamp(),
        world=wd.name, changes=changes, affected_artifacts=affected,
        protected_sha256=protected, structured_fee_fields_changed=False,
        process_timing_or_case_files_changed=False,
        approval=('Alex approved correcting nine fee drafting instructions while preserving '
                  'structured fee provenance, operational graphs, timings, and case draws.'),
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
        revision_number = len(list((out / 'manifest_revisions').glob('*.json'))) + 1
        revision = f'{revision_number:04d}'
        affected = set(plan['affected_artifacts'])
        revised.update(correction_revision=revision,
            correction_plan=str(dest / 'plan.json'),
            requires_rerender_ids=sorted(old_pending | affected),
            requires_fresh_review_ids=sorted(set(manifest.get('requires_fresh_review_ids', [])) | affected))
        for record in plan['changes']:
            target(wd, record['path']).write_bytes((dest / 'after' / record['path']).read_bytes())
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
                hold['status'] = 'resolved'
                hold['reason'] = ('Nine drafting instructions now describe the recorded fee as '
                    'administratively set and not adopted by the instrument. Structured amount, '
                    'derivation, due event, and adopted_by provenance are unchanged.')
                hold['correction_plan'] = str(dest / 'plan.json')
        holds_path.write_text(json.dumps(holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            changed_local_rules=len(plan['changes']), rerender_required=len(affected),
            prior_rerender_pending=len(old_pending), protected_files_unchanged=len(plan['protected_sha256']),
            structured_fee_fields_changed=False, process_timing_or_case_files_changed=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_fee_instruction_correction',
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
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {'changes', 'protected_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
