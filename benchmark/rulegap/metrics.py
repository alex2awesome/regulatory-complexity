"""Complexity measures per rule variant, computed from the spec before any run.

One flat row per (rung, arm) with the same columns in every domain. Measures
that need a modelled reading space are None on rungs marked not_modelled.
"""
from collections import Counter
from itertools import combinations
import json
import math

from . import dsl, trees
from .compile import Env, LEGAL, ILLEGAL, UNDEFINED, intended_verdict
from .readings import behavioral_classes, evaluate_panel
from .render import render
from .spec import key

RESTRICTION_WORDS = ['unless', 'except', 'only', 'provided', 'notwithstanding', 'subject to',
                     'not', 'no', 'other than']


def entropy_bits(ps):
    return -sum(p * math.log2(p) for p in ps if p > 0)


def surface(spec, rung, arm):
    out = render(spec, rung, arm)
    tokens = out.text.split()
    low = ' ' + ' '.join(t.strip('.,;:"()').lower() for t in tokens) + ' '
    counts = Counter(t.lower() for t in tokens)
    # Cross-reference hops: longest chain of printed definitions that use other defined terms.
    uses = {t: (spec.deps[t] & set(out.printed_definitions)) for t in out.printed_definitions}

    def hops(t, seen=()):
        return 1 + max((hops(u, seen + (t,)) for u in uses[t] if u not in seen), default=0)
    return dict(tokens=len(tokens), chars=len(out.text), n_sentences=len(out.lines),
        defined_terms=len(out.printed_definitions),
        crossref_hops=max((hops(t) for t in uses), default=0),
        restriction_words=sum(low.count(f' {w} ') for w in RESTRICTION_WORDS),
        token_entropy_bits=entropy_bits([c / len(tokens) for c in counts.values()]))


def pseudo_code(spec, rung):
    """Colliard-Georg style counts over the rule's logical form as printed:
    the skeleton plus the expressions of the definitions this rung prints."""
    exprs = [spec.skeleton(rung)['legal']]
    for term, d in spec.rungs[rung].get('definitions', {}).items():
        if spec.terms[term]['kind'] == 'cat':
            exprs += [spec.terms[term]['readings'][r]['expr'] for r in d['fixes_to']]
    operators, operands, conditions = 0, set(), 0
    for e in exprs:
        conditions += len(trees.atoms(e))
        for node in dsl.walk(e):
            if 'feature' in node:
                operands.add('feature:' + node['feature'])
                continue
            op, arg = next(iter(node.items()))
            if op in dsl.LEAVES:
                operands.add(f'{op}:{arg}')
            else:
                operators += 1
    return dict(operators=operators, operands=len(operands),
                nesting_depth=max(trees.nesting_depth(e) for e in exprs), cyclomatic_text=conditions + 1)


def _atom_values(spec, rung, record, assignment):
    env = Env(spec, rung, record['situation'], record['action'], assignment)

    def value(atom_key):
        v = dsl.eval3(json.loads(atom_key), env)
        return None if v is None else bool(v)
    return value


def _certificates(records, classes):
    """Per target pair: fewest OTHER CASES' pairs with a defined I* verdict that together
    eliminate every behavioural class disagreeing with I* on the target."""
    vecs = list(classes)
    sizes, uncovered = [], 0
    kills = []                      # per pair: bitmask of classes disagreeing with I* there
    for j, r in enumerate(records):
        m = 0
        if r['i_star'] != UNDEFINED:
            for c, vec in enumerate(vecs):
                if vec[j] != r['i_star']:
                    m |= 1 << c
        kills.append(m)
    for j, r in enumerate(records):
        need = kills[j]
        if r['i_star'] == UNDEFINED:
            continue
        if not need:
            sizes.append(0)
            continue
        covers = sorted({k & need for i, k in enumerate(kills)
                         if records[i].get('case_id', i) != r.get('case_id', j) and k & need},
                        key=lambda k: -bin(k).count('1'))
        covers = [k for k in covers if not any(k != o and k | o == o for o in covers)]
        left, greedy = need, 0
        while left and covers:
            best = max(covers, key=lambda k: bin(k & left).count('1'))
            if not best & left:
                break
            left &= ~best
            greedy += 1
        if left:
            uncovered += 1
            continue
        size = greedy
        for n in range(1, min(greedy, 5)):
            if any(_or(c) & need == need for c in combinations(covers, n)):
                size = n
                break
        sizes.append(size)
    return sizes, uncovered


def _or(masks):
    out = 0
    for m in masks:
        out |= m
    return out


def _perturbation_measures(spec, rung, records, max_depth=2):
    perturb = spec.domain.get('perturb')
    if perturb is None:
        return dict(sensitivity_mean=None, manip_cost_mean=None, manip_share_reachable=None)
    flips, costs, reachable, n_illegal = [], [], 0, 0
    for r in records:
        if r['i_star'] == UNDEFINED:
            continue
        singles = perturb(spec, r['situation'], r['action'])
        flips.append(sum(intended_verdict(spec, rung, s, a) not in (r['i_star'], UNDEFINED) for _, _, s, a in singles))
        if r['i_star'] != ILLEGAL:
            continue
        n_illegal += 1
        best, frontier = None, [(0, r['situation'], r['action'])]
        for _ in range(max_depth):
            nxt = []
            for cost, s, a in frontier:
                for _, c, s2, a2 in perturb(spec, s, a):
                    if best is not None and cost + c >= best:
                        continue
                    if intended_verdict(spec, rung, s2, a2) == LEGAL:
                        best = cost + c
                    else:
                        nxt.append((cost + c, s2, a2))
            frontier = sorted(nxt, key=lambda x: x[0])[:20]
        if best is not None:
            reachable += 1
            costs.append(best)
    return dict(sensitivity_mean=_mean(flips), manip_cost_mean=_mean(costs),
                manip_share_reachable=reachable / n_illegal if n_illegal else None)


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def panel_measures(spec, rung, records, tag):
    """Measures that depend on a case panel."""
    n = len(records)
    settled = sum(len(set(r['verdicts'])) == 1 and UNDEFINED not in r['verdicts'] for r in records)
    defined = [r for r in records if r['i_star'] != UNDEFINED and r['p'] is not None]
    over = sum(r['i_star'] == ILLEGAL and r['p'] == 'wanted' for r in defined)
    under = sum(r['i_star'] == LEGAL and r['p'] == 'unwanted' for r in defined)
    out = {f's_{tag}': settled / n,
           f'undefined_share_istar_{tag}': sum(r['i_star'] == UNDEFINED for r in records) / n,
           f'articulated_share_{tag}': sum(bool(r['open_judgments']) for r in records) / n,
           f'purpose_mismatch_{tag}': (over + under) / len(defined) if defined else None,
           f'overinclusion_{tag}': over / len(defined) if defined else None,
           f'underinclusion_{tag}': under / len(defined) if defined else None,
           f'permissiveness_{tag}': _mean([r['i_star'] == LEGAL for r in records if r['i_star'] != UNDEFINED])}
    return out


def measure(spec, rung, arm='control', panels=None):
    row = dict(rule_id=spec.rule_id, rung=rung, arm=arm, reading_scope=spec.reading_scope,
               admissibility_validated=spec.reading_scope == 'validated',
               semantic_arm_modelled=arm == 'control', decision_scope='verdict_only',
               certificate_method='cross-case, exact through size 4; greedy upper bound thereafter',
               tree_scope='Boolean atoms; feature-internal work omitted',
               manip_method='depth-2 beam search over declared perturbations; feasible-cost upper bound')
    row.update(surface(spec, rung, arm))
    modelled = spec.rungs[rung].get('reading_space') != 'not_modelled'
    row['reading_space_modelled'] = modelled
    if not modelled:
        return row
    row.update(pseudo_code(spec, rung))
    legal = spec.skeleton(rung)['legal']
    page_expr = trees.expand_printed(spec, rung, legal)
    page, page_tree = trees.tree_measures(page_expr, 'page')
    row.update(page)
    row['page_expr_size'] = dsl.size(page_expr)
    intended = spec.intended(rung)
    op_expr = trees.expand(spec, intended[0], legal)
    operative, op_tree = trees.tree_measures(op_expr, 'operative')
    row.update(operative)
    row['operative_expr_size'] = dsl.size(op_expr)
    row['operative_measures_partial'] = any('feature' in n for a in trees.atoms(op_expr) for n in dsl.walk(a))
    adm = spec.admissible(rung)
    row['n_distinct_operative_exprs'] = len({json.dumps(trees.expand(spec, a, legal), sort_keys=True) for a in adm})
    active = spec.active_terms(rung)
    prior = spec.prior(rung)
    cats = [t for t in active if spec.terms[t]['kind'] == 'cat']
    values={t:{a[t] for a in adm} for t in active}
    reference_mass=sum(prior.get(key(a),0) for a in intended)
    reference_covered=all(key(a) in prior for a in intended)
    row.update(n_open_terms=sum(len(v)>1 for v in values.values()),
        readings_per_term=json.dumps({t:len(v) for t,v in values.items()}),
        adm_size=len({tuple(a[t] for t in cats) for a in adm}), adm_size_with_grid=len(adm),
        n_intended=len(intended), reading_entropy_bits=entropy_bits(prior.values()),
        reading_entropy_bits_uniform=math.log2(len(adm)),
        reference_covered=reference_covered,
        bits_to_istar=-math.log2(reference_mass) if reference_covered else None,
        bits_to_istar_uniform=-math.log2(len(intended) / len(adm)) if reference_covered else None)
    row['n_canonical_candidates'] = len({json.dumps(trees.expand(spec, a, legal), sort_keys=True) for a in adm})
    for tag, panel in (panels or {}).items():
        records = evaluate_panel(spec, rung, panel)
        row.update(panel_measures(spec, rung, records, tag))
        if tag != 'declared':
            continue
        classes = behavioral_classes(spec, rung, records)
        row['n_behavioral_classes'] = len(classes)
        sizes, uncovered = _certificates(records, classes) if reference_covered else ([],None)
        row.update(certificate_max=max(sizes, default=None), certificate_mean=_mean(sizes),
                   certificate_uncovered_share=(uncovered / sum(r['i_star'] != UNDEFINED for r in records)
                                                if reference_covered and any(r['i_star'] != UNDEFINED for r in records) else None))
        q_page, q_op = [], []
        for r in records:
            q_page.append(trees.queries(page_tree, _atom_values(spec, rung, r, intended[0])))
            q_op.append(trees.queries(op_tree, _atom_values(spec, rung, r, intended[0])))
        row.update(page_expected_queries=_mean(q_page), operative_expected_queries=_mean(q_op))
        row.update(_perturbation_measures(spec, rung, records))
    return row


def measure_all(spec, arms=('control',), panels=None):
    return [measure(spec, rung, arm, panels) for rung in spec.rungs for arm in arms]


def columns(rows):
    cols = []
    for r in rows:
        cols += [c for c in r if c not in cols]
    return cols
