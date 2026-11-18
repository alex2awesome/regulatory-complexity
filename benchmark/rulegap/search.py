"""Search over actions and readings: loopholes, minimal strain, rule conflicts.

ExhaustiveSolver is the reference (domain action grid x admissible readings).
Z3Solver is an optional accelerator for domains that supply `z3_model`; results
of either are existence claims on the modelled grid only. Z3 path assumption:
judgment leaves occur positively (no negation above them), so 'definitely
legal' and 'definitely illegal' are obtained by setting open judgments to
False and True respectively.
"""
from . import dsl
from .compile import classify, intended_verdict, legal_set, strain, LEGAL, ILLEGAL
from .spec import key


def _sit(situation, action):
    return action.get('_situation', situation)


def _public(action):
    return {k: v for k, v in action.items() if k != '_situation'}


class ExhaustiveSolver:
    name = 'exhaustive'

    def loophole(self, spec, rung, situation):
        best = None
        for action in spec.domain['action_grid'](spec, situation):
            c = classify(spec, rung, _sit(situation, action), action)
            if c['cell'] == 'loophole' and (best is None or c['strain'] < best['strain']):
                best = dict(action=_public(action), strain=c['strain'], assignment=c['strain_assignment'], p=c['p'])
        return best

    def min_strain(self, spec, rung, situation, action):
        return classify(spec, rung, _sit(situation, action), action)['strain']

    def conflict(self, specs, rungs, situation):
        """Is any action legal under every rule's intended reading? If not, the
        cheapest total departure from the intended readings that makes one legal."""
        best = None
        completes = specs[0].domain.get('completes', lambda s, a: True)
        for action in specs[0].domain['action_grid'](specs[0], situation):
            if not completes(situation, action):
                continue
            total, picks = 0, []
            for spec, rung in zip(specs, rungs):
                sit = _sit(situation, action)
                if intended_verdict(spec, rung, sit, action) == LEGAL:
                    picks.append(None)
                    continue
                by_key = {key(a): a for a in spec.admissible(rung)}
                legal = [by_key[k] for k, v in legal_set(spec, rung, sit, action).items() if v == LEGAL]
                if not legal:
                    total = None
                    break
                (n, _), a = strain(spec, rung, legal)
                total += n
                picks.append(key(a))
            if total is not None and (best is None or total < best['strain']):
                best = dict(action=_public(action), strain=total, assignments=picks)
        return dict(conflict_under_intended=best is None or best['strain'] > 0,
                    dissolving=best if best and best['strain'] > 0 else None)


class Z3Solver:
    name = 'z3'

    def __init__(self):
        import z3
        self.z3 = z3

    # --- translation -----------------------------------------------------
    def _tz(self, expr, c):
        z3 = self.z3
        if isinstance(expr, bool):
            return z3.BoolVal(expr)
        if not isinstance(expr, dict):
            return expr
        if 'feature' in expr:
            return c['model']['features'][expr['feature']](**{k: self._tz(v, c) for k, v in (expr.get('args') or {}).items()})
        op, args = next(iter(expr.items()))
        if op in ('term', 'param'):
            return self._term(args, c)
        if op == 'const':
            return c['spec'].constants(c['rung'])[args]
        if op == 'action':
            return c['model']['action'][args]
        if op == 'fact':
            if args in c['model']['facts']:
                return c['model']['facts'][args]
            cur = c['situation']
            for part in args.split('.'):
                cur = cur.get(part)
            if cur is None:
                raise LookupError(args)
            return z3.BoolVal(cur) if isinstance(cur, bool) else cur
        if op == 'judgment':
            label = (c['situation'].get('_judgments') or {}).get(args)
            return z3.BoolVal(c['open_as'] if label is None else label)
        vals = [self._tz(a, c) for a in (args if isinstance(args, list) else [args])]
        if op == 'and': return z3.And(*vals)
        if op == 'or': return z3.Or(*vals)
        if op == 'not': return z3.Not(vals[0])
        if op == 'iff': return vals[0] == vals[1]
        if op == '+': return z3.Sum(vals) if any(z3.is_expr(v) for v in vals) else sum(vals)
        a, b = vals[0], vals[1]
        return {'==': lambda: a == b, '!=': lambda: a != b, '<': lambda: a < b, '<=': lambda: a <= b,
                '>': lambda: a > b, '>=': lambda: a >= b, '-': lambda: a - b, '*': lambda: a * b}[op]()

    def _term(self, name, c):
        z3 = self.z3
        choice = c['assign'][name]
        t = c['spec'].terms[name]
        if t['kind'] == 'param' or not z3.is_expr(choice):
            return choice if t['kind'] == 'param' else self._tz(t['readings'][choice]['expr'], c)
        opts = c['spec'].options(c['rung'], name)
        out = self._lift(self._tz(t['readings'][opts[-1]]['expr'], c))
        for i in range(len(opts) - 2, -1, -1):
            out = z3.If(choice == i, self._lift(self._tz(t['readings'][opts[i]]['expr'], c)), out)
        return out

    def _lift(self, v):
        z3 = self.z3
        return v if z3.is_expr(v) else z3.BoolVal(v) if isinstance(v, bool) else z3.IntVal(v)

    def _setup(self, spec, rung, situation, model, prefix=''):
        z3 = self.z3
        sel, cons = {}, []
        for t in spec.active_terms(rung):
            opts = spec.options(rung, t)
            v = z3.Int(prefix + 'sel_' + t)
            sel[t] = v
            if spec.terms[t]['kind'] == 'param':
                cons.append(z3.Or(*[v == o for o in opts]))
            else:
                cons += [v >= 0, v < len(opts)]
        if spec.reading_scope != 'candidate' or spec.raw.get('incompatible_combinations'):
            cons.append(z3.Or(*[z3.And(*[
                sel[t] == (a[t] if spec.terms[t]['kind'] == 'param' else spec.options(rung,t).index(a[t]))
                for t in sel]) for a in spec.admissible(rung)]))
        base = dict(spec=spec, rung=rung, situation=situation, model=model)
        legal = spec.skeleton(rung)['legal']
        free_true = self._tz(legal, {**base, 'assign': sel, 'open_as': False})
        intended_false, intended_true, dist = [], [], []
        for a in spec.intended(rung):
            intended_false.append(z3.Not(self._tz(legal, {**base, 'assign': a, 'open_as': True})))
            intended_true.append(self._tz(legal, {**base, 'assign': a, 'open_as': False}))
            terms = []
            for t, v in sel.items():
                target = a[t] if spec.terms[t]['kind'] == 'param' else spec.options(rung, t).index(a[t])
                terms.append(z3.If(v != target, 1, 0))
            dist.append(z3.Sum(terms))
        try:
            unwanted = z3.Not(self._tz(spec.purpose['wanted'], {**base, 'assign': {}, 'open_as': False}))
        except LookupError:      # purpose not defined for this case: classify from I* only
            unwanted = z3.BoolVal(True)
        return dict(sel=sel, cons=cons, free_true=free_true, intended_false=z3.And(*intended_false),
                    intended_true=z3.And(*intended_true), dist=dist, unwanted=unwanted)

    def _assignment(self, spec, rung, sel, m):
        out = {}
        for t, v in sel.items():
            i = m.eval(v, model_completion=True).as_long()
            out[t] = i if spec.terms[t]['kind'] == 'param' else spec.options(rung, t)[i]
        return out

    # --- queries ---------------------------------------------------------
    def loophole(self, spec, rung, situation):
        z3 = self.z3
        model = spec.domain['z3_model'](z3, situation)
        q = self._setup(spec, rung, situation, model)
        for k in range(1, len(q['sel']) + 1):
            s = z3.Solver()
            s.add(*model['constraints'], *q['cons'], q['free_true'], q['intended_false'], q['unwanted'],
                  z3.Or(*[d <= k for d in q['dist']]))
            if s.check() == z3.sat:
                m = s.model()
                return dict(action=_public(model['decode'](m)), strain=k,
                            assignment=key(self._assignment(spec, rung, q['sel'], m)), p='unwanted')
        return None

    def conflict(self, specs, rungs, situation):
        z3 = self.z3
        model = specs[0].domain['z3_model'](z3, situation)
        qs = [self._setup(spec, rung, situation, model, f'r{i}_') for i, (spec, rung) in enumerate(zip(specs, rungs))]
        done = [model['complete']] if 'complete' in model else []
        s = z3.Solver()
        s.add(*model['constraints'], *done, *[q['intended_true'] for q in qs])
        if s.check() == z3.sat:
            return dict(conflict_under_intended=False, dissolving=None)
        total = z3.Sum([q['dist'][0] for q in qs])     # distance to the first intended assignment of each rule
        for k in range(1, sum(len(q['sel']) for q in qs) + 1):
            s = z3.Solver()
            s.add(*model['constraints'], *[c for q in qs for c in q['cons']], *[q['free_true'] for q in qs], *done, total <= k)
            if s.check() == z3.sat:
                m = s.model()
                return dict(conflict_under_intended=True, dissolving=dict(action=_public(model['decode'](m)), strain=k,
                    assignments=[key(self._assignment(spec, rung, q['sel'], m)) for spec, rung, q in zip(specs, rungs, qs)]))
        return dict(conflict_under_intended=True, dissolving=None)


def get_solver(name='auto'):
    if name == 'exhaustive':
        return ExhaustiveSolver()
    try:
        return Z3Solver()
    except ImportError:
        if name == 'z3':
            raise
        return ExhaustiveSolver()
