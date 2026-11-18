"""Candidate interpretations are not validated interpretations.

E0 freezes whole executable interpretations, not independently approved term
menus. Three distinct human raters judge each whole reading against the exact
text and background. Source provenance and panel equivalence are separate.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from . import dsl, trees
from .spec import key

POLICY = 'whole-reading-three-humans-majority-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def used_terms(spec, assignment, rung):
    """Follow only the chosen definitions; W is irrelevant to an order reading."""
    exprs = [spec.skeleton(rung)['legal'], spec.skeleton(rung).get('consistency')]
    used = set()
    while exprs:
        expr = exprs.pop()
        for term in dsl.refs(expr, 'term') | dsl.refs(expr, 'param'):
            if term in used:
                continue
            used.add(term)
            if spec.terms[term]['kind'] == 'cat':
                exprs.append(spec.terms[term]['readings'][assignment[term]]['expr'])
    return [t for t in spec.terms if t in used]


def sourced(spec, assignment, rung):
    """A source establishes provenance only, never contextual defensibility."""
    for term in used_terms(spec, assignment, rung):
        info = spec.terms[term]
        record = (spec.raw['open_terms'][term] if info['kind'] == 'param'
                  else info['readings'][assignment[term]])
        if not any(s.get('kind') in ('statute_definition','software_default','practice_verdict',
                                    'audit_definition','author_catalog','benchmark_gold','text_literal')
                   for s in record.get('sources', [])):
            return False
    return True


def catalog(spec, rung, arm='control'):
    """Canonicalize identical expanded code, retaining every generating assignment.

    This is syntactic equivalence, not a proof of semantic equivalence. Explicit
    incompatible-combination constraints are applied by Spec.candidates.
    """
    from .render import render
    grouped = {}
    for assignment in spec.candidates(rung):
        semantics = {k: trees.expand(spec, assignment, spec.skeleton(rung).get(k))
                     for k in ('legal', 'consistency')}
        cid = digest(semantics)[:20]
        if cid not in grouped:
            definitions, evidence = {}, {}
            for term in used_terms(spec, assignment, rung):
                info, value = spec.terms[term], assignment[term]
                if info['kind'] == 'param':
                    definitions[term] = value
                    record = spec.raw['open_terms'][term]
                else:
                    record = info['readings'][value]
                    definitions[term] = record['printed'].format(**assignment)
                evidence[term] = record.get('sources') or [{'kind': 'authored'}]
            grouped[cid] = dict(candidate_id=cid, definitions=definitions,
                evidence=evidence, assignments=[], sourced=sourced(spec, assignment, rung))
        grouped[cid]['assignments'].append(assignment)
    source_root = Path(__file__).parent
    evaluator = {str(p.relative_to(source_root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [source_root/'dsl.py', source_root/'compile.py', source_root/'trees.py',
                           source_root/'domains'/f'{spec.domain_name}.py']}
    result = dict(policy=POLICY, rule_id=spec.rule_id, rung=rung, arm=arm,
        text=render(spec, rung, arm).text, background=spec.raw['background'],
        spec_digest=digest(spec.raw), evaluator=evaluator,
        candidates=sorted(grouped.values(), key=lambda r: r['candidate_id']),
        completeness='bounded candidate inventory; no claim of exhaustive admissibility')
    result['catalog_digest'] = digest(result)
    return result


def audit_ratings(cat, rows):
    """Fail closed on stale, duplicate, non-human, partial or malformed ratings.

    Unknown/abstain is permitted, but three yes/no decisions are required before
    majority acceptance/rejection. Neither sources nor model votes substitute.
    """
    if digest({k:v for k,v in cat.items() if k!='catalog_digest'}) != cat['catalog_digest']:
        raise ValueError('catalog contents no longer match their frozen digest')
    ids = {c['candidate_id'] for c in cat['candidates']}
    votes = defaultdict(dict)
    for row in rows:
        cid = row.get('candidate_id')
        if cid not in ids or row.get('catalog_digest') != cat['catalog_digest']:
            raise ValueError('rating references an unknown candidate or stale catalog')
        if not row.get('decision'):
            continue                       # untouched template, not a rating
        rater = (row.get('rater_id') or '').strip()
        if not rater or row.get('rater_kind') != 'human':
            raise ValueError('validation requires a named human rater')
        if rater in votes[cid]:
            raise ValueError(f'duplicate rating: {cid}/{rater}')
        if row['decision'] not in ('defensible', 'indefensible', 'abstain'):
            raise ValueError('decision must be defensible, indefensible or abstain')
        if not (row.get('rationale') or '').strip():
            raise ValueError('each submitted rating needs a text-grounded rationale')
        votes[cid][rater] = row['decision']
    accepted, rejected, pending = [], [], []
    for cid in sorted(ids):
        decisions = list(votes[cid].values())
        if len(decisions) > 3:
            raise ValueError('predeclared policy permits exactly three raters per candidate')
        if len(decisions) != 3 or 'abstain' in decisions:
            pending.append(cid)
        elif decisions.count('defensible') >= 2:
            accepted.append(cid)
        else:
            rejected.append(cid)
    return dict(policy=POLICY, catalog_digest=cat['catalog_digest'],
        accepted=accepted, rejected=rejected, pending=pending,
        coverage=(len(accepted)+len(rejected))/len(ids) if ids else 0,
        n_raters=len({r for v in votes.values() for r in v}),
        status='complete' if ids and not pending else 'pending')


def validated_assignments(spec, rung, ratings_path, arm='control'):
    cat = catalog(spec, rung, arm)
    with Path(ratings_path).open(newline='') as f:
        audit = audit_ratings(cat, list(csv.DictReader(f)))
    accepted = set(audit['accepted'])
    assignments = [a for c in cat['candidates'] if c['candidate_id'] in accepted for a in c['assignments']]
    if not assignments:
        raise ValueError('no human-validated interpretations; use candidate scope for exploratory results')
    # The target is independent evidence, not a definition chosen by the raters.
    if not {key(a) for a in spec.intended(rung)} <= {key(a) for a in assignments}:
        raise ValueError('governing reference not covered by validated set; investigate, do not replace I*')
    return assignments, audit


def write_packet(spec, rung, out, arm='control'):
    cat = catalog(spec, rung, arm)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out/'catalog.json').write_text(json.dumps(cat, indent=2)+'\n')
    lines = ['# Whole-interpretation review', '', 'Rule:', '', cat['text'], '',
        'Allowed background:', '', cat['background'], '',
        'Judge each COMPLETE reading against this text and background. A plausible term does not make '
        'its combination with other terms defensible. Do not consult agent outputs, rewards, purpose labels, '
        'or the designated governing reading. Work independently before discussing disagreements.', '',
        'Mark defensible, indefensible, or abstain; give a text-grounded rationale. Record missing readings '
        'separately for a new catalog version. Do not infer that this list is exhaustive.', '']
    for c in cat['candidates']:
        lines += [f"## {c['candidate_id']}", '', *[f'- {t}: {v}' for t,v in c['definitions'].items()], '']
    (out/'rater_packet.md').write_text('\n'.join(lines))
    fields = ['catalog_digest','candidate_id','rater_id','rater_kind','decision','rationale']
    for n in range(1,4):
        with (out/f'ratings_{n}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            w.writerows(dict(catalog_digest=cat['catalog_digest'],candidate_id=c['candidate_id'])
                        for c in cat['candidates'])
    (out/'audit.json').write_text(json.dumps(audit_ratings(cat, []),indent=2)+'\n')
    return cat


def behavioral_audit(spec, rung, panel):
    """Pairwise witnesses on a declared finite panel; no claim of global equivalence."""
    from .readings import evaluate_panel
    from .cases import visible
    cat=catalog(spec,rung); records=evaluate_panel(spec,rung,panel)
    indices={key(a):i for i,a in enumerate(spec.admissible(rung))}
    grouped=defaultdict(list)
    for c in cat['candidates']:
        i=indices[key(c['assignments'][0])]
        grouped[tuple(r['verdicts'][i] for r in records)].append(c['candidate_id'])
    vectors=list(grouped)
    witnesses=[]
    for a in range(len(vectors)):
        for b in range(a+1,len(vectors)):
            j=next(j for j,(va,vb) in enumerate(zip(vectors[a],vectors[b])) if va!=vb)
            witnesses.append(dict(class_a=a,class_b=b,record=j,
                                  verdict_a=vectors[a][j],verdict_b=vectors[b][j]))
    return dict(scope='equivalence on this finite verdict panel only',catalog_digest=cat['catalog_digest'],
        classes=[dict(class_id=i,candidate_ids=grouped[v]) for i,v in enumerate(vectors)],
        records=[dict(case_id=r['case_id'],situation=visible(r['situation']),action=visible(r['action']))
                 for r in records],witnesses=witnesses)
