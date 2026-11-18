"""Three-valued (Kleene) JsonLogic-style evaluator.

Pattern copied from pipeline/executor.py:eval_expr and extended with list
aggregates, leaves for terms/params/constants/action fields/facts/features, and
None as "undefined" instead of an exception. A feature returning None means the
fact characterization is unsettled; the value propagates.
"""

LEAVES = ('term', 'param', 'const', 'action', 'fact', 'feature', 'judgment')
COMPARE = ('==', '!=', '<', '<=', '>', '>=')
BOOL = ('and', 'or', 'not', 'iff')
ARITH = ('+', '-', '*', '/')
AGG = ('len', 'sum', 'max', 'min', 'any', 'all')
OPS = COMPARE + BOOL + ARITH + AGG + ('in', 'not_in', 'if')


def _op(expr):
    if 'feature' in expr:
        return 'feature', expr
    if len(expr) != 1:
        raise ValueError(f'malformed expr: {expr!r}')
    return next(iter(expr.items()))


def eval3(expr, env):
    if isinstance(expr, list):
        return [eval3(e, env) for e in expr]
    if not isinstance(expr, dict):
        return expr
    op, args = _op(expr)
    if op == 'term':
        return env.term(args)
    if op == 'param':
        return env.param(args)
    if op == 'const':
        return env.const(args)
    if op == 'action':
        return env.action_field(args)
    if op == 'fact':
        return env.fact(args)
    if op == 'judgment':
        # Articulated, not specified: a component stated in words whose value on a
        # case comes from a practice-holder label, or is open (None) without one.
        return env.judgment(args)
    if op == 'feature':
        kwargs = {k: eval3(v, env) for k, v in (expr.get('args') or {}).items()}
        return env.feature(expr['feature'], kwargs)
    vals = [eval3(a, env) for a in (args if isinstance(args, list) else [args])]
    if op == 'and':
        if any(v is False for v in vals):
            return False
        return None if any(v is None for v in vals) else True
    if op == 'or':
        if any(v is True for v in vals):
            return True
        return None if any(v is None for v in vals) else False
    if op == 'not':
        return None if vals[0] is None else not vals[0]
    if op == 'iff':
        return None if None in vals else bool(vals[0]) == bool(vals[1])
    if op == 'if':
        if vals[0] is None:
            return vals[1] if vals[1] == vals[2] else None
        return vals[1] if vals[0] else vals[2]
    if op in AGG:
        xs = vals[0]
        if xs is None:
            return None
        if op == 'len':
            return len(xs)
        if op in ('any', 'all'):
            return eval3({'or' if op == 'any' else 'and': list(xs)}, env) if xs else op == 'all'
        if any(x is None for x in xs):
            return None
        if op == 'sum':
            return sum(xs)
        return (max if op == 'max' else min)(xs) if xs else None
    if any(v is None for v in vals):
        return None
    a = vals[0]
    b = vals[1] if len(vals) > 1 else None
    if op == '==': return a == b
    if op == '!=': return a != b
    if op == '<':  return a < b
    if op == '<=': return a <= b
    if op == '>':  return a > b
    if op == '>=': return a >= b
    if op == 'in': return a in b
    if op == 'not_in': return a not in b
    if op == '+': return sum(vals)
    if op == '-': return a - b if len(vals) == 2 else -a
    if op == '*':
        out = 1
        for v in vals:
            out *= v
        return out
    if op == '/': return None if b == 0 else a / b
    raise ValueError(f'unsupported op: {op}')


def walk(expr):
    """Yield every dict node of an expression."""
    if isinstance(expr, list):
        for e in expr:
            yield from walk(e)
    elif isinstance(expr, dict):
        yield expr
        if 'feature' in expr:
            for v in (expr.get('args') or {}).values():
                yield from walk(v)
        else:
            for v in expr.values():
                yield from walk(v)


def refs(expr, kind):
    """Names referenced through {'term': X} or {'param': X} leaves."""
    return {n[kind] for n in walk(expr) if len(n) == 1 and kind in n}


def size(expr):
    return sum(1 for _ in walk(expr))


def check(expr):
    """Raise ValueError on any unknown operator (authoring errors)."""
    for node in walk(expr):
        if 'feature' in node:
            continue
        op, _ = _op(node)
        if op not in OPS + LEAVES:
            raise ValueError(f'unknown op {op!r} in {node!r}')
