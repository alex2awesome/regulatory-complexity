"""Deterministic rule text from a spec, and the parse-back check."""
from dataclasses import dataclass, field
from itertools import product
import re

from .arms import ARMS

DEF_RE = re.compile(r'^For purposes of this rule, "(.*)" means (.*)\.$')


@dataclass
class Rendered:
    text: str
    lines: list
    printed_definitions: dict = field(default_factory=dict)   # term -> reading id, or tuple of ids
    params_printed: dict = field(default_factory=dict)


def _fixed_params(spec, rung):
    out = {}
    for name, t in spec.terms.items():
        if t['kind'] == 'param':
            opts = spec.options(rung, name)
            if len(opts) == 1 and name in spec.rungs[rung].get('definitions', {}):
                out[name] = opts[0]
    return out


def expected_definitions(spec, rung):
    """What the rung's printed definitions fix: {term: id or tuple}, {param: value}."""
    defs, params = {}, _fixed_params(spec, rung)
    for term, d in spec.rungs[rung].get('definitions', {}).items():
        if spec.terms[term]['kind'] == 'cat':
            defs[term] = d['fixes_to'][0] if len(d['fixes_to']) == 1 and 'printed' not in d else tuple(d['fixes_to'])
    return defs, params


def render(spec, rung, arm='control'):
    r, t = spec.rungs[rung], spec.raw['templates']
    consts = spec.constants(rung)
    lines = [t[r['template']].format(**consts)]
    defs, params = expected_definitions(spec, rung)
    for term in spec.terms:
        if term not in defs:
            continue
        d = r['definitions'][term]
        if 'printed' in d:
            printed = d['printed']
        else:
            printed, fields = spec.printed(term, defs[term], params)
        lines.append(t['definition'].format(term_text=t['term_text'][term].format(**consts), printed=printed))
    lines += ARMS[arm](spec, rung)
    return Rendered('\n'.join(lines), lines, defs, params)


def parse_back(spec, rung, text):
    """Recover printed definitions from text alone by matching definition sentences."""
    consts, t = spec.constants(rung), spec.raw['templates']
    lookup = {}
    for term, info in spec.terms.items():
        if info['kind'] != 'cat':
            continue
        name = t['term_text'][term].format(**consts)
        for rid in info['values']:
            raw = info['readings'][rid]['printed']
            fields = sorted({f for f in re.findall(r'\{(\w+)\}', raw)})
            for combo in product(*(spec.terms[f]['values'] for f in fields)):
                ps = dict(zip(fields, combo))
                lookup[(name, raw.format(**ps))] = (term, rid, ps)
        for r in spec.rungs.values():
            d = r.get('definitions', {}).get(term, {})
            if 'printed' in d:
                lookup[(name, d['printed'])] = (term, tuple(d['fixes_to']), {})
    defs, params = {}, {}
    for line in text.split('\n'):
        m = DEF_RE.match(line)
        if not m:
            continue
        if m.groups() not in lookup:
            raise ValueError(f'unrecognised definition sentence: {line!r}')
        term, rid, ps = lookup[m.groups()]
        defs[term] = rid
        params.update(ps)
    return defs, params


def check_render(spec, rung, arm='control'):
    """Scripted check: text -> definitions equals exactly what the rung fixes."""
    out = render(spec, rung, arm)
    got = parse_back(spec, rung, out.text)
    want = expected_definitions(spec, rung)
    if got != want:
        raise ValueError(f'parse-back mismatch at {rung}/{arm}: got {got}, want {want}')
    if render(spec, rung, arm).text != out.text:
        raise ValueError('render is not deterministic')
    return out
