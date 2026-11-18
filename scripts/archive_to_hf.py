"""Archive the project's data (not in git) to the private Hugging Face dataset, and restore it.

Each top-level folder becomes one .tar.gz at the same path:
  corpus/<child>.tar.gz, benchmark/synth/worlds/<world>.tar.gz, runs/<run>.tar.gz,
  plus <top>/_files.tar.gz for loose files, and scratch/<dir>.tar.gz for the project's folders on
  sk3 shared scratch (/dfs/scratch0/alexspan, streamed over ssh; nothing is written on sk3).
Before packing, each folder is scanned for credential patterns; a folder with a hit is skipped and
logged, never uploaded. Archives are batched into commits of about 3 GB (Hub commit rate limit).
State is kept in runs/hf_archive_<date>/state.jsonl so a rerun resumes.

  python scripts/archive_to_hf.py push            # create the private dataset if needed, upload all
  python scripts/archive_to_hf.py restore DIR     # untar every downloaded archive under DIR in place
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

REPO = 'alex2awesome/regulatory-complexity-data'
ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / 'runs' / 'hf_archive_20261117'
STAGE = STATE_DIR / 'stage'
BATCH_BYTES = 3e9
LOCAL_TOPS = ['corpus', 'benchmark/synth/worlds', 'runs']
SK3_ROOT = '/dfs/scratch0/alexspan'
SK3_DIRS = [  # this project's folders only; other projects, envs, caches and model weights are left out
    'admin_data_20260929', 'admin_model_inputs_20260930', 'adu_bayarea_20260924', 'adu_census_interim',
    'adu_comment_census', 'adu_counties_20260926', 'adu_fn_sample', 'adu_forum_fetch', 'adu_statewide_20260926',
    'gemma_jobs', 'multi_census', 'open_model_smoketest', 'procurement_20261021', 'real_process_20261001',
    'real_process_refit_20261002', 'rulegap_gemma_20261111', 'solar_admin_integration_20260930',
    'solar_ix_calibration_20260930', 'solar_screen_20260923', 'toy_configurable_20260930',
    'toy_jax_pilot_20260930', 'toy_statute']
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=25', '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
       '-o', 'ProxyCommand=ssh -4 -o BatchMode=yes -o ControlMaster=no -o ControlPath=none -W %h:%p whale', 'sk3']
# AWS access key IDs (AKIA...) are left out on purpose: they are public identifiers, and forum posts
# carry other people's expired presigned S3 links that contain them. Secret keys are caught by assignment.
SECRET = (r'(sk-(ant|proj)-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}'
          r'|xox[abpr]-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|aws_secret_access_key *[=:] *[A-Za-z0-9/+]{40})')


def log(msg):
    line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {msg}'
    print(line, flush=True)
    with open(STATE_DIR / 'archive.log', 'a') as f:
        f.write(line + '\n')


def units():
    out = []
    for top in LOCAL_TOPS:
        base = ROOT / top
        if not base.exists():
            continue
        children = sorted(base.iterdir(), key=lambda p: p.name)
        loose = [p for p in children if p.is_file()]
        if loose:
            out.append(dict(kind='files', top=top, files=[p.name for p in loose], archive=f'{top}/_files.tar.gz'))
        for p in children:
            if p.is_dir() and p.resolve() != STATE_DIR.resolve() and p.name not in ('__pycache__',):
                out.append(dict(kind='dir', top=top, name=p.name, archive=f'{top}/{p.name}.tar.gz'))
    out += [dict(kind='sk3', name=d, archive=f'scratch/{d}.tar.gz') for d in SK3_DIRS]
    return out


def ssh(cmd, out=None, timeout=7200):
    for attempt in range(3):
        r = subprocess.run(SSH + [cmd], stdin=subprocess.DEVNULL, stdout=out or subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=timeout)
        if r.returncode in (0, 1):  # grep exits 1 when nothing matches
            return r
        time.sleep(60 * (attempt + 1))
    raise RuntimeError(f'ssh failed: {cmd[:80]} :: {r.stderr[-300:]!r}')


def scan_and_count(u):
    if u['kind'] == 'sk3':
        path = f'{SK3_ROOT}/{u["name"]}'
        hits = ssh(f"grep -rIlE '{SECRET}' {path} 2>/dev/null | head -5").stdout.decode().split()
        n = int(ssh(f'find {path} -type f | wc -l').stdout.decode().strip() or 0)
        return hits, n
    paths = [str(ROOT / u['top'] / f) for f in u['files']] if u['kind'] == 'files' else [str(ROOT / u['top'] / u['name'])]
    r = subprocess.run(['grep', '-rIlE', SECRET] + paths, capture_output=True, text=True)
    hits = r.stdout.split('\n')[:5] if r.stdout.strip() else []
    n = len(u['files']) if u['kind'] == 'files' else sum(len(fs) for _, _, fs in os.walk(paths[0]))
    return [h for h in hits if h], n


def pack(u, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if u['kind'] == 'sk3':
        with open(dest, 'wb') as f:
            ssh(f'tar czf - -C {SK3_ROOT} {u["name"]}', out=f, timeout=6 * 3600)
        if subprocess.run(['tar', 'tzf', str(dest)], stdout=subprocess.DEVNULL).returncode:
            raise RuntimeError('streamed archive does not list cleanly')
        return
    with tarfile.open(dest, 'w:gz') as t:
        if u['kind'] == 'files':
            for f in u['files']:
                t.add(ROOT / u['top'] / f, arcname=f'{u["top"]}/{f}')
        else:
            t.add(ROOT / u['top'] / u['name'], arcname=f'{u["top"]}/{u["name"]}')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def flush(api, batch):
    if not batch:
        return
    total = sum(r['bytes'] for r in batch)
    log(f'uploading {len(batch)} archives, {total / 1e9:.2f} GB')
    try:
        api.upload_folder(repo_id=REPO, repo_type='dataset', folder_path=str(STAGE),
                          commit_message=f'Add {len(batch)} archives ({total / 1e9:.1f} GB)')
    except Exception as e:
        log(f'UPLOAD FAILED, stopping (rerun resumes): {type(e).__name__}: {e}')
        raise
    with open(STATE_DIR / 'state.jsonl', 'a') as f:
        for r in batch:
            f.write(json.dumps(r) + '\n')
    shutil.rmtree(STAGE)
    log(f'committed {len(batch)} archives, {total / 1e9:.2f} GB: {[r["archive"] for r in batch]}')


def push():
    from huggingface_hub import HfApi
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    api = HfApi()
    api.create_repo(REPO, repo_type='dataset', private=True, exist_ok=True)
    state = STATE_DIR / 'state.jsonl'
    done = {json.loads(l)['archive'] for l in state.read_text().splitlines()} if state.exists() else set()
    if STAGE.exists():
        shutil.rmtree(STAGE)
    todo = [u for u in units() if u['archive'] not in done]
    log(f'{len(todo)} archives to build ({len(done)} already uploaded)')
    batch, staged = [], 0
    for u in todo:
        try:
            hits, n = scan_and_count(u)
            if hits:
                log(f'SKIPPED {u["archive"]}: credential pattern in {hits}')
                with open(STATE_DIR / 'skipped.jsonl', 'a') as f:
                    f.write(json.dumps(dict(archive=u['archive'], hits=hits)) + '\n')
                continue
            dest = STAGE / u['archive']
            pack(u, dest)
            row = dict(archive=u['archive'], source=('sk3:' + SK3_ROOT + '/' + u['name']) if u['kind'] == 'sk3'
                       else u['top'] + ('/' + u['name'] if u['kind'] == 'dir' else ' (loose files)'),
                       n_files=n, bytes=dest.stat().st_size, sha256=sha256(dest))
            batch.append(row)
            staged += row['bytes']
            log(f'packed {u["archive"]}: {n} files, {row["bytes"] / 1e6:.0f} MB')
            if staged >= BATCH_BYTES:
                flush(api, batch)
                batch, staged = [], 0
        except Exception as e:
            log(f'FAILED {u["archive"]}: {type(e).__name__}: {e}')
            with open(STATE_DIR / 'failed.jsonl', 'a') as f:
                f.write(json.dumps(dict(archive=u['archive'], error=f'{type(e).__name__}: {e}'[:500])) + '\n')
            p = STAGE / u['archive']
            if p.exists():
                p.unlink()
    flush(api, batch)
    rows = [json.loads(l) for l in state.read_text().splitlines()]
    (STATE_DIR / 'MANIFEST.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    api.upload_file(path_or_fileobj=str(STATE_DIR / 'MANIFEST.jsonl'), path_in_repo='MANIFEST.jsonl',
                    repo_id=REPO, repo_type='dataset', commit_message='Manifest of archives')
    api.upload_file(path_or_fileobj=str(ROOT / 'scripts' / 'hf_dataset_card.md'), path_in_repo='README.md',
                    repo_id=REPO, repo_type='dataset', commit_message='Dataset card')
    log(f'done: {len(rows)} archives, {sum(r["bytes"] for r in rows) / 1e9:.1f} GB')


def restore(where):
    where = Path(where)
    for p in sorted(where.rglob('*.tar.gz')):
        rel = p.relative_to(where)
        target = where / 'scratch' if rel.parts[0] == 'scratch' else where  # local archives carry their top folder
        with tarfile.open(p) as t:
            t.extractall(target, filter='data')
        print('restored', p.relative_to(where))


if __name__ == '__main__':
    if sys.argv[1:2] == ['push']:
        push()
    elif sys.argv[1:2] == ['restore'] and len(sys.argv) == 3:
        restore(sys.argv[2])
    else:
        print(__doc__)
