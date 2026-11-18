"""Spec loading, validation helpers and the admissible reading space."""
from itertools import product
from pathlib import Path
import string

import yaml

from . import dsl
from .domains import REGISTRY


def key(assignment):
    return '|'.join(f'{k}={assignment[k]}' for k in assignment)


class Spec:
    def __init__(self, raw, path=None, reading_scope='candidate', ratings_path=None, rating_arm='control'):
        if reading_scope not in ('candidate', 'sourced', 'validated'):
            raise ValueError('reading_scope must be candidate, sourced or validated')
        self.reading_scope, self.ratings_path, self.rating_arm = reading_scope, ratings_path, rating_arm
        self._spaces = {}
        self.raw, self.path = raw, path
        self.rule_id, self.domain_name = raw['rule_id'], raw['domain']
        self.domain = REGISTRY[self.domain_name]
        self.purpose = raw['purpose']
        self.terms = {}
        for name, t in raw['open_terms'].items():
            if 'family' in t:
                lo, hi = t['family']['range']
                values = list(range(lo, hi + 1, t['family'].get('step', 1)))
                prior = {v: 1 / len(values) for v in values}
                self.terms[name] = dict(kind='param', values=values, readings={},
                                        intended=list(t['intended']), prior=prior)
                continue
            rs = t.get('readings') or self.domain['reading_sets'][t['readings_from']]()
            total = sum(r.get('prior', 1.0) for r in rs)
            self.terms[name] = dict(kind='cat', values=[r['id'] for r in rs],
                readings={r['id']: r for r in rs}, intended=list(t['intended']),
                prior={r['id']: r.get('prior', 1.0) / total for r in rs})
        self.rungs = {r['rung']: r for r in raw['ladder']}
        self.deps = {name: self._deps(name) for name in self.terms}

    # --- structure -------------------------------------------------------
    def _direct(self, name):
        out = set()
        for r in self.terms[name]['readings'].values():
            out |= dsl.refs(r['expr'], 'term') | dsl.refs(r['expr'], 'param')
        return out

    def _deps(self, name, seen=()):
        if name in seen:
            raise ValueError(f'cyclic term reference through {name}')
        out = set()
        for d in self._direct(name):
            if d not in self.terms:
                raise ValueError(f'{name} references unknown term {d}')
            out |= {d} | self._deps(d, seen + (name,))
        return out

    def skeleton(self, rung):
        return {**self.raw['skeleton'], **self.rungs[rung].get('skeleton_override', {})}

    def constants(self, rung):
        return {**self.raw.get('constants', {}), **self.rungs[rung].get('extra_constants', {})}

    def active_terms(self, rung):
        """Terms the rung's legality expression can reach, in spec order."""
        legal = self.skeleton(rung)['legal']
        top = dsl.refs(legal, 'term') | dsl.refs(legal, 'param')
        reach = set(top)
        for t in top:
            reach |= self.deps[t]
        return [t for t in self.terms if t in reach]

    def options(self, rung, term):
        fixed = self.rungs[rung].get('definitions', {}).get(term, {}).get('fixes_to')
        return list(fixed) if fixed else list(self.terms[term]['values'])

    def intended_options(self, rung, term):
        """Printed text governs: if a rung's definition excludes the intended
        reading, the rung's own options are the intended ones."""
        opts = self.options(rung, term)
        keep = [v for v in self.terms[term]['intended'] if v in opts]
        return keep or opts

    # --- reading space ---------------------------------------------------
    def candidates(self, rung):
        terms = self.active_terms(rung)
        assignments = [dict(zip(terms, combo)) for combo in product(*(self.options(rung, t) for t in terms))]
        constraints = self.raw.get('incompatible_combinations', [])
        for c in constraints:
            if not c.get('reason') or not c.get('forbid'):
                raise ValueError('incompatible combinations need a nonempty forbid pattern and reason')
            for t,v in c['forbid'].items():
                if t not in self.terms or v not in self.terms[t]['values']:
                    raise ValueError(f'unknown interpretation constraint {t}={v}')
        return [a for a in assignments if not any(all(a.get(t)==v for t,v in c['forbid'].items())
                                                   for c in constraints)]

    def admissible(self, rung):
        """Legacy API name. Candidate scope is explicitly NOT human-validated."""
        if rung not in self._spaces:
            assignments = self.candidates(rung)
            if self.reading_scope == 'sourced':
                from .admissibility import sourced
                if 'text_source' in self.raw:
                    from .real import check_sources
                    problems=check_sources(self)
                    if problems:
                        raise ValueError('source provenance failed: '+ '; '.join(problems))
                assignments = [a for a in assignments if sourced(self, a, rung)]
            elif self.reading_scope == 'validated':
                if self.ratings_path is None:
                    raise ValueError('validated scope requires independent human ratings')
                from .admissibility import validated_assignments
                assignments, self.validation_audit = validated_assignments(self, rung, self.ratings_path, self.rating_arm)
            if not assignments:
                raise ValueError(f'no interpretations in {self.reading_scope} scope for {rung}')
            self._spaces[rung] = assignments
        return self._spaces[rung]

    def intended(self, rung):
        terms = self.active_terms(rung)
        return [dict(zip(terms, combo)) for combo in product(*(self.intended_options(rung, t) for t in terms))]

    def prior(self, rung):
        out = {}
        for a in self.admissible(rung):
            p = 1.0
            for t, v in a.items():
                p *= self.terms[t]['prior'][v]
            out[key(a)] = p
        total = sum(out.values())
        return {k: v / total for k, v in out.items()}

    def printed(self, term, reading, params):
        """Printed definition text of one reading, with parameters substituted."""
        text = self.terms[term]['readings'][reading]['printed']
        fields = [f for _, f, _, _ in string.Formatter().parse(text) if f]
        return text.format(**{f: params[f] for f in fields}), fields


def load_spec(path, **kwargs):
    path = Path(path)
    return Spec(yaml.safe_load(path.read_text()), path, **kwargs)
