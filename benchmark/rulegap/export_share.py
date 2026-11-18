"""Copy the rulegap package and the two synthetic admin-law toys into a standalone folder to share.

  python -m benchmark.rulegap.export_share DEST

DEST must not exist. Nothing is pushed anywhere; the folder is ready for `git init` and a push once
Alex picks the destination. Excluded on purpose:
- run outputs (runs/ is gitignored and holds model transcripts);
- the experiment plan and other docs that quote internal notes;
- fetched web pages under real/percentile/sources/raw (third-party documentation; the manifest keeps
  each URL and sha256 so they can be re-fetched). The Model Spec (CC0) and the tau2 airline policy
  (MIT, sierra-research/tau2-bench) are kept because tests check them.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPY = [
    'benchmark/rulegap',
    'pipeline/procbench/__init__.py',
    'pipeline/procbench/infra/__init__.py',
    'pipeline/procbench/infra/manifest.py',
    'pipeline/procbench/infra/codex_runner.py',
    'tests/test_rulegap.py',
    'tests/test_rulegap_admissibility.py',
    'tests/test_rulegap_airline.py',
    'tests/test_rulegap_constitution.py',
    'requirements-rulegap.txt',
    'docs/2026-11-11-rulegap-toy-results.md',
    'docs/2026-11-11-rulegap-redteam-trial.md',
    'docs/2026-11-11-rulegap-agent-readings.md',
    'docs/2026-11-17-question-tree-pilot.md',
]
EXTRA = {  # source -> destination inside DEST
    'runs/toy_statute2_20260929/hen_package.json': 'toys/hens/hen_package.json',
}
SKIP_DIRS = {'__pycache__', '.pytest_cache'}
SKIP_PREFIX = 'benchmark/rulegap/real/percentile/sources/raw'


def _ignore(src, names):
    rel = Path(src).resolve().relative_to(ROOT).as_posix()
    if rel.startswith(SKIP_PREFIX):
        return names
    return [n for n in names if n in SKIP_DIRS or (rel + '/' + n).startswith(SKIP_PREFIX)]


def export(dest):
    dest = Path(dest)
    if dest.exists():
        raise SystemExit(f'{dest} exists; pick a new folder')
    for rel in COPY:
        src, dst = ROOT / rel, dest / rel
        if not src.exists():
            print(f'missing, skipped: {rel}')
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=_ignore)
        else:
            shutil.copy2(src, dst)
    for rel, out in EXTRA.items():
        (dest / out).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest / out)
    shutil.copy2(ROOT / 'benchmark/rulegap/README.md', dest / 'README.md')
    (dest / '.gitignore').write_text('__pycache__/\n.pytest_cache/\nruns/\n')
    n = sum(1 for p in dest.rglob('*') if p.is_file())
    print(f'wrote {n} files to {dest}')


if __name__ == '__main__':
    export(sys.argv[1])
