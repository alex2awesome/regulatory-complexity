#!/usr/bin/env python3
"""Apply the approved dated-update correction to aggregate timing documents.

Construction-only utility: it reads the development chronology audit and specs,
never extractor inputs.  It preserves publication dates, measurement clocks,
figures, process graphs, and case draws.  Exact artifacts under another live/held
writer remain excluded and keep the release hold open.
"""
import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path

from benchmark.synth.render.complete_slice import (
    ROOT, append, current_manifest, lock, read, save, sha, stamp, state,
)

AUDIT = 'chronology_audit_20260918_0139.json'
HOLD_ID = 'aggregate_observation_chronology'
CONCURRENT_HOLD = 'concurrent_legacy_render'
LABEL_DATE = 'September 15, 2026'


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


def dated_value(value):
    prefix = f'Timing update as of {LABEL_DATE}: '
    if value.startswith(prefix):
        raise ValueError('Timing value already carries the approved update label')
    return prefix + value


def stage(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing correction stage; choose a new directory')
    audit = read(out / AUDIT)
    manifest = current_manifest(out)
    holds = read(out / 'release_holds.json')
    chronology = next(h for h in holds if h['id'] == HOLD_ID and h['status'] == 'open')
    targets = set(chronology.get('artifacts', []))
    concurrent = next(h for h in holds if h['id'] == CONCURRENT_HOLD)
    blocked = set(concurrent.get('artifacts', [])) if concurrent['status'] == 'open' else set()
    changes = []
    excluded = []
    for row in audit['aggregate_rows']:
        aid = row['artifact_id']
        if aid not in targets:
            continue
        if aid in blocked:
            excluded.append(aid)
            continue
        if aid not in manifest['artifacts']:
            raise ValueError('Chronology target is outside compact manifest: ' + aid)
        path = wd / 'specs' / (aid + '.json')
        if file_sha(path) != row['spec_sha256']:
            raise ValueError('Chronology-audited spec changed: ' + aid)
        before = read(path)
        after = deepcopy(before)
        if after['date'] != row['original_publication_date']:
            raise ValueError('Publication date drift: ' + aid)
        for index in row['reveals_indices']:
            reveal = after['reveals'][index]
            clock = reveal.get('measurement_clock', {})
            cutoff = clock.get('as_of')
            if not cutoff or date.fromisoformat(cutoff) <= date.fromisoformat(after['date']):
                raise ValueError('Expected post-publication measured cutoff: ' + aid)
            reveal['value'] = dated_value(reveal['value'])
        # Only the selected reveal strings may change.
        check = deepcopy(after)
        for index in row['reveals_indices']:
            check['reveals'][index]['value'] = before['reveals'][index]['value']
        if check != before:
            raise ValueError('Correction attempted a non-label mutation: ' + aid)
        before_bytes = path.read_bytes()
        after_bytes = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
        relative = 'specs/' + aid + '.json'
        write_new(dest / 'before' / relative, before_bytes)
        write_new(dest / 'after' / relative, after_bytes)
        write_new(dest / 'before' / 'artifacts' / (aid + '.md'),
                  (wd / 'artifacts' / (aid + '.md')).read_bytes())
        changes.append(dict(artifact_id=aid, path=relative,
            before_sha256=sha(before_bytes), after_sha256=sha(after_bytes),
            publication_date=before['date'], update_cutoffs=row['cutoffs'],
            reveal_indices=row['reveals_indices']))
    if set(r['artifact_id'] for r in changes) | set(excluded) != targets:
        raise ValueError('Chronology hold targets do not match audited rows')
    protected_paths = [wd / 'world.json'] + sorted(p for p in (wd / 'truth').rglob('*') if p.is_file())
    protected = {str(p.relative_to(wd)): file_sha(p) for p in protected_paths}
    plan = dict(schema_version='approved-aggregate-chronology-correction/1',
        staged_utc=stamp(), world=wd.name, audit=str(out / AUDIT), changes=changes,
        excluded_due_concurrent_hold=sorted(excluded), protected_sha256=protected,
        publication_dates_changed=False, describes_versions_changed=False,
        measurement_clocks_changed=False, figures_changed=False,
        process_or_case_files_changed=False,
        approval=('Alex approved explicit dated timing updates while preserving original '
                  'publication dates, policy versions, figures, and case draws.'),
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
                raise ValueError('Correction target changed after staging: ' + record['artifact_id'])
            if file_sha(dest / 'after' / record['path']) != record['after_sha256']:
                raise ValueError('Staged replacement changed: ' + record['artifact_id'])
        prior = state(wd, out, manifest)
        old_pending = {aid for aid, row in prior['artifacts'].items()
                       if row['status'] == 'rerender_pending'}
        revised = deepcopy(manifest)
        revision_number = len(list((out / 'manifest_revisions').glob('*.json'))) + 1
        revision = f'{revision_number:04d}'
        affected = {r['artifact_id'] for r in plan['changes']}
        revised.update(correction_revision=revision,
            correction_plan=str(dest / 'plan.json'),
            requires_rerender_ids=sorted(old_pending | affected),
            requires_fresh_review_ids=sorted(set(manifest.get('requires_fresh_review_ids', [])) | affected))
        for record in plan['changes']:
            path = target(wd, record['path'])
            path.write_bytes((dest / 'after' / record['path']).read_bytes())
            revised['artifacts'][record['artifact_id']]['spec_sha256'] = record['after_sha256']
        for relative, expected in plan['protected_sha256'].items():
            if file_sha(target(wd, relative)) != expected:
                raise ValueError('Protected file changed during apply: ' + relative)
        save(out / 'manifest_revisions' / (revision + '.json'), revised)
        holds_path = out / 'release_holds.json'
        before_holds = holds_path.read_bytes()
        write_new(dest / 'before' / 'release_holds.json', before_holds)
        holds = json.loads(before_holds)
        remaining = plan['excluded_due_concurrent_hold']
        for hold in holds:
            if hold['id'] == HOLD_ID:
                hold['artifacts'] = remaining
                hold['status'] = 'open' if remaining else 'resolved'
                hold['reason'] = (f'Approved dated timing labels applied to the final '
                    f'{len(affected)} compact artifacts; all 32 approved aggregate documents '
                    'now carry explicit dated updates. Publication dates, stale policy versions, '
                    'figures, measurement clocks, process graphs, and case draws unchanged.')
                hold['partial_correction_plan'] = str(dest / 'plan.json')
        holds_path.write_text(json.dumps(holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(applied_utc=stamp(), correction_revision=revision,
            changed_specs=len(affected), rerender_required=len(affected),
            prior_rerender_pending=len(old_pending), excluded=len(remaining),
            protected_files_unchanged=len(plan['protected_sha256']),
            publication_dates_changed=False, measurement_clocks_changed=False,
            process_or_case_files_changed=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='approved_aggregate_timing_update',
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
