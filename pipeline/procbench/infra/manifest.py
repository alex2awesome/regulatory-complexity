"""JSON serialization, hashing and explicit, versioned run provenance.

Legacy manifest fields remain intact. The common `provenance` record distinguishes
direct dependencies (including parent draws) from a legacy input-evidence hash.
Truth access is a caller declaration, not something this writer can certify.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def write(path, data):
    path = Path(path)
    # Serialize before opening: a non-finite value must not truncate a good file.
    serialized = json.dumps(data, indent=2, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized)


def file_hashes(paths):
    return {str(p): digest(Path(p).read_bytes()) for p in paths}


def source_closure(root, entries):
    """Resolve static imports within one package, without executing any code.

    Paths stay relative to root so saved packages can be imported in isolation.
    Dynamic imports/assets must be declared as additional entries by the caller.
    """
    root = Path(root).resolve()
    pending, found = [Path(p) for p in entries], {}
    while pending:
        relative = pending.pop()
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source entry escapes package root')
        relative = path.relative_to(root)
        key = relative.as_posix()
        if key in found:
            continue
        raw = path.read_bytes()
        found[key] = raw
        if path.suffix != '.py':
            continue
        # Include package initializers, including those above nested modules.
        for parent in (relative.parent, *relative.parent.parents):
            init = parent / '__init__.py'
            if (root / init).is_file():
                pending.append(init)
        for node in ast.walk(ast.parse(raw, filename=key)):
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            base = relative.parent
            for _ in range(node.level - 1):
                base = base.parent if base != Path('.') else Path('..')
            if '..' in base.parts:
                # Outside this package; do not silently call this self-contained.
                raise ValueError(f'External relative import in {key}; declare its packaging explicitly')
            module = base.joinpath(*(node.module or '').split('.'))
            candidates = [module] if node.module else []
            candidates.extend(module / a.name for a in node.names if a.name != '*')
            for candidate in candidates:
                py, init = candidate.with_suffix('.py'), candidate / '__init__.py'
                if (root / py).is_file():
                    pending.append(py)
                elif (root / init).is_file():
                    pending.append(init)
    return dict(sorted(found.items()))


class RunManifest:
    """Lifecycle for a new run; refuses to overwrite an existing manifest."""

    def __init__(self, out, legacy, *, operation, inputs, config, seeds,
                 hidden_truth_read, source_root, sources):
        if type(hidden_truth_read) is not bool:
            raise ValueError('Declare whether this operation reads hidden truth')
        self.path = Path(out) / 'manifest.json'
        if self.path.exists():
            raise ValueError('Preserve existing manifest; choose a fresh run')
        self.started = time.monotonic()
        started_utc = datetime.now(timezone.utc).isoformat()
        source = source_closure(source_root, sources)
        hashes = {name: digest(raw) for name, raw in source.items()}
        self.data = dict(legacy)
        self.data.update(manifest_version='procbench-run/1', status='running',
                         started_utc=started_utc, seconds=None)
        # Some historical callers used a single script digest here. Preserve its
        # type/meaning; the complete dependency map always lives in provenance.
        self.data.setdefault('source_sha256', hashes)
        self.data['provenance'] = dict(operation=operation, started_utc=started_utc,
            completed_utc=None, seconds=None, config=config, seeds=seeds,
            input_sha256=file_hashes(inputs), source_sha256=hashes,
            hidden_truth_read=hidden_truth_read,
            truth_access_check='explicit caller declaration, not filesystem enforcement')
        for name, raw in source.items():
            target = self.path.parent / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise ValueError('Preserve existing source snapshot: ' + str(target))
            target.write_bytes(raw)
        write(self.path, self.data)

    def complete(self, **fields):
        if self.data['status'] != 'running':
            raise ValueError('Run is already complete')
        completed = datetime.now(timezone.utc).isoformat()
        seconds = time.monotonic() - self.started
        self.data.update(fields)
        self.data.update(status='completed', completed_utc=completed, seconds=seconds)
        self.data['provenance'].update(completed_utc=completed, seconds=seconds)
        write(self.path, self.data)
