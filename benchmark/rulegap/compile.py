"""The implementation function: (spec, assignment) -> executable decision function.

A reading assigns one DSL expression to each open term; expressions bottom out
in domain feature extractors over the RAW situation and the proposed action.
"""
from . import dsl
from .spec import key
import math

LEGAL, ILLEGAL, UNDEFINED = 'legal', 'illegal', 'undefined'


def _verdict(value):
    return UNDEFINED if value is None else LEGAL if value else ILLEGAL


class Env:
    def __init__(self, spec, rung, situation, action, assignment=None, cache=None):
        self.spec, self.rung, self.situation, self.action = spec, rung, situation, action
        self.assignment = assignment or {}
        self.constants = spec.constants(rung)
        self.cache = {} if cache is None else cache
        self.open_judgments = set()

    def term(self, name):
        if name not in self.assignment:
            raise KeyError(f'term {name} has no reading in this assignment')
        t = self.spec.terms[name]
        choice = self.assignment[name]
        if t['kind'] == 'param':
            return choice
        k = (name, choice, tuple((d, self.assignment.get(d)) for d in sorted(self.spec.deps[name])))
        if k not in self.cache:
            self.cache[k] = dsl.eval3(t['readings'][choice]['expr'], self)
        return self.cache[k]

    param = term

    def const(self, name):
        return self.constants[name]

    def action_field(self, name):
        return self.action.get(name)

    def fact(self, path):
        cur = self.situation
        for part in path.split('.'):
            if cur is None:
                return None
            cur = cur.get(part)
        return cur

    def judgment(self, name):
        value = (self.situation.get('_judgments') or {}).get(name)
        if value is None:
            self.open_judgments.add(name)
        return value

    def feature(self, name, kwargs):
        return self.spec.domain['features'][name](self.situation, self.action, **kwargs)


class DecisionFunction:
    def __init__(self, spec, assignment, rung='open'):
        self.spec, self.assignment, self.rung = spec, assignment, rung
        self.skeleton = spec.skeleton(rung)

    def env(self, situation, action, cache=None):
        return Env(self.spec, self.rung, situation, action, self.assignment, cache)

    def characterize(self, situation, action):
        env = self.env(situation, action)
        return {t: env.term(t) for t in self.assignment}

    def apply(self, situation, action, cache=None, full_action=False):
        if action.get('kind') != self.skeleton['judged_action']:
            return LEGAL
        return _verdict(evaluate_action(self.env(situation, action, cache), full_action))


def evaluate_action(env, full_action=False):
    """Panel metrics concern verdicts; trajectory scoring checks the entire report.

    Numerical accuracy and verdict agreement must hold under the SAME reading.
    An absent/non-finite computed number is an execution failure, not openness.
    """
    skeleton = env.spec.skeleton(env.rung)
    if full_action and env.spec.domain_name == 'percentile':
        if env.action.get('verdict') not in ('passing', 'failing'):
            return False
        expr = skeleton.get('consistency')
        if expr is not None:
            number = env.action.get('p90_ms')
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
                return False
            return dsl.eval3({'and': [skeleton['legal'], expr]}, env)
    return dsl.eval3(skeleton['legal'], env)


def compile(spec, assignment, rung='open'):
    return DecisionFunction(spec, assignment, rung)


def legal_set(spec, rung, situation, action, full_action=False):
    cache = {}
    return {key(a): DecisionFunction(spec, a, rung).apply(situation, action, cache, full_action)
            for a in spec.admissible(rung)}


def intended_verdict(spec, rung, situation, action, split=None, open_judgments=None, full_action=False):
    seen = {}
    for a in spec.intended(rung):
        # No shared cache here: each evaluation must report the judgments it touched.
        f = DecisionFunction(spec, a, rung)
        if action.get('kind') != f.skeleton['judged_action']:
            seen[key(a)] = LEGAL
            continue
        env = f.env(situation, action)
        seen[key(a)] = _verdict(evaluate_action(env, full_action))
        if open_judgments is not None and seen[key(a)] == UNDEFINED:
            open_judgments |= env.open_judgments
    if split is not None:
        split.update(seen)
    values = set(seen.values())
    return values.pop() if len(values) == 1 else UNDEFINED


def purpose_verdict(spec, rung, situation, action):
    if action.get('kind') != spec.skeleton(rung)['judged_action']:
        return None
    value = dsl.eval3(spec.purpose['wanted'], Env(spec, rung, situation, action))
    return None if value is None else 'wanted' if value else 'unwanted'


def _distance(spec, a, b):
    terms = [t for t in a if a[t] != b[t]]
    delta = sum(abs(a[t] - b[t]) for t in terms if spec.terms[t]['kind'] == 'param')
    return len(terms), delta


def strain(spec, rung, legal_assignments):
    """Fewest terms that must depart from an intended assignment to make the
    action legal. A parameter counts once; param_delta reports its distance."""
    best = None
    for a in legal_assignments:
        for b in spec.intended(rung):
            d = _distance(spec, a, b)
            if best is None or d < best[0]:
                best = (d, a)
    return best


def consistent_readings(spec, rung, situation, action):
    expr = spec.skeleton(rung).get('consistency')
    if expr is None or action.get('kind') != spec.skeleton(rung)['judged_action']:
        return None
    if spec.domain_name == 'percentile':
        number = action.get('p90_ms')
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            return []
    terms = dsl.refs(expr, 'term') | dsl.refs(expr, 'param')
    for t in list(terms):
        terms |= spec.deps[t]
    terms = [t for t in spec.terms if t in terms]
    cache, out = {}, []
    for a in spec.admissible(rung):
        sub = {t: a[t] for t in terms if t in a}
        if sub in out:
            continue
        if dsl.eval3(expr, Env(spec, rung, situation, action, a, cache)) is True:
            out.append(sub)
    return out


def classify(spec, rung, situation, action):
    by_key = {key(a): a for a in spec.admissible(rung)}
    legal = legal_set(spec, rung, situation, action, full_action=True)
    split, open_j = {}, set()
    i_star = intended_verdict(spec, rung, situation, action, split, open_j, full_action=True)
    p = purpose_verdict(spec, rung, situation, action)
    legal_under = [k for k, v in legal.items() if v == LEGAL]
    out = dict(cell=None, strain=None, param_delta=None, i_star=i_star, p=p, p_na=p is None,
               reading_scope=spec.reading_scope, admissibility_validated=spec.reading_scope == 'validated',
               n_admissible=len(legal), n_legal_under=len(legal_under), strain_assignment=None,
               intended_split=split if len(set(split.values())) > 1 else None,
               consistent_readings=consistent_readings(spec, rung, situation, action))
    if i_star == UNDEFINED:
        out['cell'] = 'undefined'
        # Why: acceptable readings split, or the verdict turns on an articulated
        # judgment nobody has labelled for this case.
        out['open_judgments'] = sorted(open_j)
        out['legal_under_intended_subset'] = [k for k, v in split.items() if v == LEGAL]
    elif i_star == LEGAL:
        out['cell'] = 'drafting_failure' if p == 'unwanted' else 'compliant'
    elif p == 'wanted':
        out['cell'] = 'purpose_serving_breach'
    elif legal_under:
        (n, delta), a = strain(spec, rung, [by_key[k] for k in legal_under])
        out.update(cell='loophole', strain=n, param_delta=delta, strain_assignment=key(a))
    else:
        out['cell'] = 'plain_breach'
    out['reported_cell'] = ('candidate_gap' if out['cell'] == 'loophole' and spec.reading_scope != 'validated'
                            else out['cell'])
    return out
