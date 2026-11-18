#!/usr/bin/env python3
"""Finish approved appeal-authority corrections after quiet-hold reconciliation."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, lock, read, save, sha, stamp, state,
)
from benchmark.synth.render.correct_appeal_authorities import (
    HOLD_ID, LAW_RESTATING, NEW_AUTHORITY, appeal_choice_id, file_sha,
    sampled_appeal_activity, target, write_new,
)

PROGRAMS = ('C50__S03', 'C51__S03', 'C52__S03', 'C57__S03', 'C58__S03')


def affected_artifacts(wd, manifest):
    return sorted(aid for aid in manifest['artifacts']
        if any(aid.startswith(model_id + '__') for model_id in PROGRAMS)
        and read(wd / 'specs' / (aid + '.json'))['kind'] in LAW_RESTATING)


def stage(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing correction stage; choose a new directory')
    manifest = current_manifest(out)
    holds = read(out / 'release_holds.json')
    coordination = next(h for h in holds if h['id'] == 'concurrent_legacy_render')
    if coordination['status'] != 'resolved' or not coordination.get('reconciliation_snapshot'):
        raise ValueError('Concurrent legacy hold has not been freshly reconciled')
    hold = next(h for h in holds if h['id'] == HOLD_ID and h['status'] == 'open')
    if set(hold['programs']) != set(PROGRAMS):
        raise ValueError('Appeal hold no longer matches the five deferred programs')

    changes = []
    target_relatives = set()
    for model_id in PROGRAMS:
        appeal = sampled_appeal_activity(read(wd / 'truth/processes' / (model_id + '.json')))
        choice_id = appeal_choice_id(model_id)
        path = wd / 'truth/local_rules' / (model_id + '.json')
        before = read(path)
        old_authority = before['choices'][choice_id]
        clause = f'{choice_id} = {old_authority};'
        if old_authority == NEW_AUTHORITY or before['text_spec'].count(clause) != 1:
            raise ValueError('Unexpected deferred appeal rule: ' + model_id)
        after = deepcopy(before)
        after['choices'][choice_id] = NEW_AUTHORITY
        after['text_spec'] = before['text_spec'].replace(
            clause, f'{choice_id} = {NEW_AUTHORITY};')
        check = deepcopy(after)
        check['choices'][choice_id] = old_authority
        check['text_spec'] = before['text_spec']
        if check != before or after.get('prior_version') != before.get('prior_version'):
            raise ValueError('Correction attempted a change beyond current appeal prose')
        before_bytes = path.read_bytes()
        after_bytes = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
        relative = 'truth/local_rules/' + model_id + '.json'
        target_relatives.add(relative)
        write_new(dest / 'before' / relative, before_bytes)
        write_new(dest / 'after' / relative, after_bytes)
        changes.append(dict(model_id=model_id, path=relative, choice_id=choice_id,
            old_authority=old_authority, new_authority=NEW_AUTHORITY,
            appeal_activity_id=appeal['id'], appeal_activity_notes=appeal['notes'],
            before_sha256=sha(before_bytes), after_sha256=sha(after_bytes)))

    affected = affected_artifacts(wd, manifest)
    if len(affected) != 9:
        raise ValueError(f'Expected nine deferred law/restating artifacts, found {len(affected)}')
    for aid in affected:
        write_new(dest / 'before' / 'artifacts' / (aid + '.md'),
                  (wd / 'artifacts' / (aid + '.md')).read_bytes())
    protected_paths = [wd / 'world.json'] + sorted(
        p for p in (wd / 'truth').rglob('*')
        if p.is_file() and str(p.relative_to(wd)) not in target_relatives)
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths}
    plan = dict(schema_version='approved-deferred-appeal-authority-correction/1',
        staged_utc=stamp(), world=wd.name, changes=changes,
        affected_artifacts=affected, protected_sha256=protected,
        prior_versions_changed=False, process_graphs_changed=False,
        fees_changed=False, process_timing_or_case_files_changed=False,
        reconciliation_snapshot=coordination['reconciliation_snapshot'],
        approval=('Alex approved completing the five deferred appeal-body corrections after '
                  'fresh quiet-owner reconciliation, preserving graphs, history, fees, timings, '
                  'and sampled cases.'),
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
            if file_sha(target(wd, record['path'])) != record['before_sha256']:
                raise ValueError('Correction target changed: ' + record['model_id'])
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
                hold['status'] = 'resolved'
                hold['programs'] = []
                hold['reason'] = ('All 28 approved appeal-body descriptions now match the '
                    'sampled Zoning Administrator authority. Graphs, prior-version history, '
                    'fees, timings, and sampled cases are unchanged.')
                hold['final_correction_plan'] = str(dest / 'plan.json')
        holds_path.write_text(json.dumps(holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            changed_local_rules=len(plan['changes']), corrected_programs=len(PROGRAMS),
            rerender_required=len(affected), prior_rerender_pending=len(old_pending),
            protected_files_unchanged=len(plan['protected_sha256']),
            prior_versions_changed=False, process_graphs_changed=False,
            fees_changed=False, process_timing_or_case_files_changed=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_deferred_appeal_authority_correction',
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
