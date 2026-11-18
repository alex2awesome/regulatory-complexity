#!/usr/bin/env python3
"""Archive current held bytes and retire the quiet legacy-render coordination hold."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

from benchmark.synth.render.complete_slice import ROOT, append, lock, read, save, stamp

HOLD_ID = 'concurrent_legacy_render'


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


def live_legacy_processes():
    output = subprocess.check_output(['ps', '-axo', 'pid,lstart,command'], text=True)
    rows = []
    for line in output.splitlines()[1:]:
        if str(os.getpid()) in line:
            continue
        lowered = line.lower()
        if ('t08' in lowered or 't09' in lowered or 't10' in lowered) and (
                'python' in lowered or 'codex' in lowered):
            rows.append(line.strip())
    return rows


def reconcile(wd, out, dest):
    if dest.exists():
        raise ValueError('Preserve the existing reconciliation archive')
    holds_path = out / 'release_holds.json'
    holds = read(holds_path)
    hold = next(h for h in holds if h['id'] == HOLD_ID and h['status'] == 'open')
    ids = sorted(hold['artifacts'])
    if len(ids) != 54:
        raise ValueError(f'Expected 54 held artifacts, found {len(ids)}')
    live = live_legacy_processes()
    if live:
        raise ValueError('Legacy writer still appears live: ' + repr(live))

    old_snapshot_path = out / hold['evidence']
    old_snapshot = read(old_snapshot_path)
    rows = {}
    newest = None
    for aid in ids:
        path = wd / 'artifacts' / (aid + '.md')
        content = path.read_bytes()
        write_new(dest / 'artifacts' / (aid + '.md'), content)
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        newest = max(newest, mtime) if newest else mtime
        old = old_snapshot['artifacts'][aid]
        current_sha = file_sha(path)
        rows[aid] = dict(current_sha256=current_sha, mtime_utc=mtime,
            equals_old_capture=current_sha == old['captured_sha256'],
            equals_old_receipt=current_sha == old['receipt_sha256'])

    active_handoff = out / 'ACTIVE_HANDOFF.json'
    write_new(dest / 'ACTIVE_HANDOFF.preserved.json', active_handoff.read_bytes())
    write_new(dest / 'prior_snapshot.preserved.json', old_snapshot_path.read_bytes())
    write_new(dest / 'before' / 'release_holds.json', holds_path.read_bytes())
    snapshot = dict(schema_version='quiet-legacy-reconciliation/1', created_utc=stamp(),
        world=wd.name, artifact_count=len(ids), artifacts=rows,
        live_legacy_processes=live, newest_held_artifact_mtime_utc=newest,
        old_snapshot=str(old_snapshot_path), active_handoff_preserved=True,
        note=('Freshness and ownership reconciliation only; this snapshot is not a '
              'fidelity verdict. Every changed document still requires fresh current-bound review.'))
    save(dest / 'snapshot.json', snapshot)

    with lock(out):
        # Recheck ownership and exact artifact bytes under the completion lock.
        if live_legacy_processes():
            raise ValueError('Legacy writer appeared during reconciliation')
        for aid, row in rows.items():
            if file_sha(wd / 'artifacts' / (aid + '.md')) != row['current_sha256']:
                raise ValueError('Held artifact changed during reconciliation: ' + aid)
        current_holds = read(holds_path)
        current = next(h for h in current_holds if h['id'] == HOLD_ID)
        if current['status'] != 'open' or sorted(current['artifacts']) != ids:
            raise ValueError('Coordination hold changed during reconciliation')
        current['status'] = 'resolved'
        current['reason'] = ('Fresh reconciliation found no T08/T09/T10 owner process. The '
            'recorded handoff is stale and all 54 current bytes were archived before further '
            'corrections. This retires coordination ownership only; it is not a fidelity verdict.')
        current['reconciliation_snapshot'] = str(dest / 'snapshot.json')
        holds_path.write_text(json.dumps(current_holds, indent=2, ensure_ascii=False) + '\n')
        receipt = dict(reconciled_utc=stamp(), held_artifacts=len(ids),
            live_legacy_processes=0, current_bytes_archived=len(ids),
            old_capture_unchanged=sum(row['equals_old_capture'] for row in rows.values()),
            changed_after_old_capture=sum(not row['equals_old_capture'] for row in rows.values()),
            coordination_hold_resolved=True, fidelity_verified=False)
        save(dest / 'applied.json', receipt)
        append(wd / 'provenance.jsonl', dict(kind='quiet_legacy_render_reconciliation',
            reconciliation_archive=str(dest), **receipt))
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', default='W2_DEV_001')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reconciliation', type=Path, required=True)
    args = parser.parse_args()
    wd = ROOT / 'benchmark/synth/worlds' / args.world
    print(json.dumps(reconcile(wd, args.out, args.reconciliation), indent=2))


if __name__ == '__main__':
    main()
