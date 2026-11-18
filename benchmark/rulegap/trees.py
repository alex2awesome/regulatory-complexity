"""Decision trees read off a legality expression.

Atoms are the maximal non-boolean subexpressions. The page tree keeps each open
term as one predicate; the operative tree first substitutes a reading's
expressions for the terms. Trees are Shannon expansions in a given atom order.
"""
from itertools import permutations
import json

from . import dsl

CONNECTIVES = ('and', 'or', 'not', 'iff')


def _is_conn(expr):
    return isinstance(expr, dict) and len(expr) == 1 and next(iter(expr)) in CONNECTIVES


def atoms(expr):
    """Distinct atoms in text order."""
    out = []

    def visit(e):
        if _is_conn(e):
            args = next(iter(e.values()))
            for a in (args if isinstance(args, list) else [args]):
                visit(a)
        elif e not in out and not isinstance(e, bool):
            out.append(e)
    visit(expr)
    return out


def nesting_depth(expr):
    if not _is_conn(expr):
        return 0
    args = next(iter(expr.values()))
    return 1 + max(nesting_depth(a) for a in (args if isinstance(args, list) else [args]))


def _eval(expr, values):
    """Kleene evaluation of the boolean structure given some atom values."""
    if not _is_conn(expr):
        return expr if isinstance(expr, bool) else values.get(json.dumps(expr, sort_keys=True))
    op, args = next(iter(expr.items()))
    vals = [_eval(a, values) for a in (args if isinstance(args, list) else [args])]
    if op == 'and':
        return False if False in vals else None if None in vals else True
    if op == 'or':
        return True if True in vals else None if None in vals else False
    if op == 'not':
        return None if vals[0] is None else not vals[0]
    return None if None in vals else vals[0] == vals[1]


def shannon(expr, order, values=None):
    """Tree as nested tuples: ('leaf', bool) or ('node', atom_key, low, high)."""
    values = values or {}
    v = _eval(expr, values)
    if v is not None:
        return ('leaf', v)
    for a in order:
        k = json.dumps(a, sort_keys=True)
        if k in values:
            continue
        low, high = shannon(expr, order, {**values, k: False}), shannon(expr, order, {**values, k: True})
        # If the atom does not matter on this path, both branches are the same subtree.
        return low if low == high else ('node', k, low, high)
    raise ValueError('expression undetermined after all atoms were set')


def n_nodes(t):
    return 0 if t[0] == 'leaf' else 1 + n_nodes(t[2]) + n_nodes(t[3])


def n_leaves(t):
    return 1 if t[0] == 'leaf' else n_leaves(t[2]) + n_leaves(t[3])


def depth(t):
    return 0 if t[0] == 'leaf' else 1 + max(depth(t[2]), depth(t[3]))


def rank(t):
    """Ehrenfeucht-Haussler rank."""
    if t[0] == 'leaf':
        return 0
    a, b = rank(t[2]), rank(t[3])
    return a + 1 if a == b else max(a, b)


def predicates(t):
    return set() if t[0] == 'leaf' else {t[1]} | predicates(t[2]) | predicates(t[3])


def minimize(expr, max_atoms=7):
    """Smallest Shannon tree over all atom orders (exact up to max_atoms)."""
    order = atoms(expr)
    if len(order) > max_atoms:
        return shannon(expr, order), False
    best = min((shannon(expr, list(p)) for p in permutations(order)), key=n_nodes)
    return best, True


def queries(t, atom_value):
    """Atoms evaluated walking the tree for one case; stops at an undefined atom."""
    n = 0
    while t[0] == 'node':
        n += 1
        v = atom_value(t[1])
        if v is None:
            break
        t = t[3] if v else t[2]
    return n


def expand(spec, assignment, expr):
    """Substitute readings for term leaves, recursively (operative expression)."""
    if isinstance(expr, list):
        return [expand(spec, assignment, e) for e in expr]
    if not isinstance(expr, dict):
        return expr
    if len(expr) == 1 and ('term' in expr or 'param' in expr):
        name = expr.get('term', expr.get('param'))
        t = spec.terms[name]
        if t['kind'] == 'param':
            return assignment[name]
        return expand(spec, assignment, t['readings'][assignment[name]]['expr'])
    return {k: expand(spec, assignment, v) for k, v in expr.items()}


def expand_printed(spec, rung, expr):
    """Expand only definitions actually printed and fixed to one reading."""
    if isinstance(expr, list):
        return [expand_printed(spec, rung, e) for e in expr]
    if not isinstance(expr, dict):
        return expr
    if len(expr) == 1 and ('term' in expr or 'param' in expr):
        name = expr.get('term', expr.get('param'))
        definition = spec.rungs[rung].get('definitions', {}).get(name, {})
        options = definition.get('fixes_to', [])
        if len(options) != 1:
            return expr
        info = spec.terms[name]
        return (options[0] if info['kind'] == 'param' else
                expand_printed(spec, rung, info['readings'][options[0]]['expr']))
    return {k: expand_printed(spec, rung, v) for k,v in expr.items()}


def tree_measures(expr, prefix):
    order = atoms(expr)
    text_tree = shannon(expr, order)
    small, exact = minimize(expr)
    return {f'{prefix}_leaves': n_leaves(text_tree), f'{prefix}_depth': depth(text_tree),
            f'{prefix}_distinct_predicates': len(predicates(text_tree)),
            f'{prefix}_cyclomatic': n_nodes(text_tree) + 1, f'{prefix}_minimized_nodes': n_nodes(small),
            f'{prefix}_minimized_exact': exact, f'{prefix}_rank': rank(small)}, text_tree


def export_decision_tree(t):
    """Nested dict form for inspection."""
    if t[0] == 'leaf':
        return {'outcome': 'legal' if t[1] else 'illegal'}
    return {'predicate': json.loads(t[1]), 'false': export_decision_tree(t[2]), 'true': export_decision_tree(t[3])}
