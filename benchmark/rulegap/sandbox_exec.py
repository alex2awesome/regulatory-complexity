"""Run model-written readings on a panel, in a separate `python -I` process.

Usage: python -I sandbox_exec.py IN.json OUT.json
IN = {"readings": [{"rid", "code"}], "pairs": [{"pid", "situation", "action"}]}
OUT = {"verdicts": {rid: {pid: legal|illegal|undefined|error}}, "errors": {rid: msg}}
The code is checked statically and runs with a reduced builtins table. This is
hygiene for research code we requested, not a security boundary.
"""
import ast
import json
import signal
import sys

ALLOWED_MODULES = {'math', 're', 'datetime', 'statistics', 'collections', 'itertools', 'functools'}
FORBIDDEN = {'open', 'exec', 'eval', 'compile', 'globals', 'locals', 'vars', 'getattr', 'setattr',
             'delattr', 'input', 'breakpoint', 'help', 'exit', 'quit', 'memoryview', '__import__',
             'os', 'sys', 'subprocess', 'socket', 'shutil', 'pathlib', 'builtins'}
SAFE = ['abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter', 'float', 'int', 'isinstance', 'len',
        'list', 'map', 'max', 'min', 'range', 'reversed', 'round', 'set', 'sorted', 'str', 'sum', 'tuple',
        'zip', 'frozenset', 'Exception', 'ValueError', 'KeyError', 'TypeError', 'IndexError',
        'AttributeError', 'ZeroDivisionError', 'StopIteration', 'next', 'iter', 'hasattr', 'divmod', 'pow']


def check(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or '').split('.')[0]]
            bad = [n for n in names if n not in ALLOWED_MODULES]
            if bad:
                raise ValueError(f'import not allowed: {bad}')
        if isinstance(node, ast.Name) and node.id in FORBIDDEN:
            raise ValueError(f'name not allowed: {node.id}')
        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            raise ValueError(f'attribute not allowed: {node.attr}')
    if not any(isinstance(n, ast.FunctionDef) and n.name == 'legal' for n in tree.body):
        raise ValueError('no top-level function named legal')


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split('.')[0] not in ALLOWED_MODULES:
        raise ImportError(name)
    return __import__(name, globals, locals, fromlist, level)


def timeout(signum, frame):
    raise TimeoutError('reading exceeded its time limit')


def main(src, dst):
    import builtins
    data = json.load(open(src))
    out = {'verdicts': {}, 'errors': {}}
    signal.signal(signal.SIGALRM, timeout)
    for r in data['readings']:
        rid, verdicts = r['rid'], {}
        try:
            check(r['code'])
            env = {'__builtins__': {**{k: getattr(builtins, k) for k in SAFE}, '__import__': guarded_import,
                                    'print': lambda *a, **k: None, 'True': True, 'False': False, 'None': None}}
            signal.alarm(20)
            exec(compile(r['code'], f'<{rid}>', 'exec'), env)
            fn = env['legal']
            for p in data['pairs']:
                try:
                    v = fn(json.loads(json.dumps(p['situation'])), dict(p['action']))
                    verdicts[p['pid']] = 'undefined' if v is None else 'legal' if v is True else 'illegal' if v is False else 'error'
                except TimeoutError:
                    raise
                except Exception as e:
                    verdicts[p['pid']] = 'error'
                    out['errors'].setdefault(rid, f'{type(e).__name__}: {e}'[:300])
            signal.alarm(0)
        except Exception as e:
            signal.alarm(0)
            out['errors'][rid] = f'{type(e).__name__}: {e}'[:300]
            verdicts = {p['pid']: 'error' for p in data['pairs']}
        out['verdicts'][rid] = verdicts
    json.dump(out, open(dst, 'w'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
