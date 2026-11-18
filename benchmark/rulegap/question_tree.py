"""Question-asking interpreter, v0 (pilot, 2026-11-17).

Reads a rule's text and writes, without any code:
  (a) a tree whose nodes keep the rule's own words (each node quotes a verbatim span),
  (b) the interpretive questions an official must answer before applying each node consistently,
      each with candidate answers labelled by how well the text supports them,
  (c) the words the reader treats as settled (candidates for the shared assumption set).
A separate matcher maps the generated questions onto the questions planted in two synthetic
administrative-law toys (hens permit act, procurement bidding rule), so recall is measured
against known truth. Generators never see the planted questions.

  python -m benchmark.rulegap.question_tree run --out runs/rulegap_20261117/question_tree
  python -m benchmark.rulegap.question_tree analyse --out runs/rulegap_20261117/question_tree
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re

from .redteam import call
from .render import render
from .spec import load_spec

GENERATORS = ['codex:gpt-5.6-luna', 'claude:claude-sonnet-5-5']
MATCHER = 'claude:claude-opus-5-5'  # first choice codex:gpt-5.6-sol got 403 on every call (kept in matched/)
MATCH_DIR = 'matched_opus'
SAMPLES = 3
SPEC = Path(__file__).with_name('specs') / 'procurement_v1.yaml'

HENS_TEXT = """Backyard Hen Keeping Act (synthetic).
Sec. 1. A resident of a single-family dwelling may keep up to six hens after obtaining a permit from the local permitting authority.
Sec. 2. The applicant shall submit an application, together with a site plan showing the location of the coop and its distance to property lines.
Sec. 3. Before issuing a permit, the authority shall determine that the coop will not create a nuisance to adjoining properties.
Sec. 4. The authority shall issue or deny the permit within 30 days after receiving a complete application.
Sec. 5. The authority may charge a reasonable application fee."""

# Planted interpretive questions. Hens: verbatim from the toy's statute package
# (runs/toy_statute2_20260929/hen_package.json, `questions`). Procurement: the open terms of
# specs/procurement_v1.yaml, one question per term, answers = the spec's printed readings.
PLANTED = {
    'hens': [
        dict(id='Q1_desk_sufficient', question='Sec. 3: can a desk review of the site plan alone support the nuisance determination?', answers=['yes', 'no']),
        dict(id='Q2_neighbor_input_required', question="Sec. 3 ('to adjoining properties'): must adjoining owners get notice and a chance to comment?", answers=['yes', 'no']),
        dict(id='Q3_investigative_power', question="Sec. 3: does the duty to determine imply power to require the applicant's attendance at an inspection or hearing?", answers=['yes', 'no']),
        dict(id='Q4_clock_includes_d2', question='Sec. 4: does the 30-day clock run through the nuisance determination (no tolling during notice)?', answers=['yes', 'no']),
        dict(id='Q5_separate_fees', question="Sec. 5: does 'a reasonable application fee' authorize separate notice or inspection fees?", answers=['yes', 'no']),
        dict(id='Q6_denial_grounds_limited', question='Sec. 1-4: does the statute limit the grounds for denial to ineligibility, incompleteness and the nuisance determination (no other ground)?', answers=['yes', 'no']),
    ],
    'procurement': [
        dict(id='PURCHASE', question="What counts as one 'purchase' when comparing against the threshold?",
             answers=['a single order', 'all orders that serve the same need, placed within some window, taken together',
                      'all orders carrying the same description of need, placed within some window, taken together',
                      'all orders placed with the same vendor in a twelve-month period, taken together']),
        dict(id='W', question='If orders are added together, over what time window?',
             answers=['a specific window length (any number of months or days)']),
        dict(id='EMERGENCY', question="What counts as 'an emergency'?",
             answers=['a situation declared an emergency in the procurement file (by anyone)',
                      'a situation the department head has declared an emergency',
                      'an imminent threat to health or safety',
                      "bidding cannot be completed before the request's deadline"]),
        dict(id='BID', question="What counts as a 'competitive bid' toward the three?",
             answers=['a written bid actually received from a vendor', 'a written request for a bid sent to a vendor']),
    ],
}
BACKGROUND = {
    'hens': 'You work for the local permitting authority that administers this act. You will apply it to permit applications.',
    'procurement': 'You work in the purchasing office of a state agency. You will apply this rule to purchase requests.',
}

SUPPORT = ['clearly supported by the text', 'plausible', 'stretch']
ROLES = ['eligibility', 'requirement', 'procedure step', 'condition', 'exception', 'deadline', 'fee', 'outcome', 'other']


def _strict(props):
    return {'type': 'object', 'additionalProperties': False, 'required': list(props), 'properties': props}


S = {'type': 'string'}
GEN_SCHEMA = _strict({
    'nodes': {'type': 'array', 'items': _strict({
        'id': S, 'quote': S, 'role': {'type': 'string', 'enum': ROLES},
        'depends_on': {'type': 'array', 'items': S}})},
    'questions': {'type': 'array', 'items': _strict({
        'id': S, 'node': S, 'open_words': S, 'question': S,
        'answers': {'type': 'array', 'items': _strict({'answer': S, 'support': {'type': 'string', 'enum': SUPPORT}})}})},
    'settled': {'type': 'array', 'items': _strict({'words': S, 'why': S})},
})
MATCH_SCHEMA = _strict({
    'generated': {'type': 'array', 'items': _strict({'qid': S, 'planted_id': {'type': ['string', 'null']}})},
    'planted': {'type': 'array', 'items': _strict({
        'id': S, 'matched_qids': {'type': 'array', 'items': S},
        'answers_covered': {'type': 'array', 'items': {'type': 'integer'}}})},
})


def law_text(law):
    return HENS_TEXT if law == 'hens' else render(load_spec(SPEC), 'open', 'control').text


def gen_prompt(law):
    return f"""{BACKGROUND[law]}

THE RULE
{law_text(law)}

Read the rule closely. Do not write code. Return JSON with three parts.

1. nodes: break the rule into nodes. Each node quotes the exact words of the rule it comes from (a verbatim, contiguous span), gives its role, and lists the ids of the nodes it depends on.

2. questions: list every interpretive question you would need answered before you could apply this rule consistently to the cases you will see. A question belongs here only if reasonable officials, reading the same words in good faith, could answer it differently. For each question give the node id, the exact words of the rule that leave it open, the question, and two to five candidate answers, each labelled "clearly supported by the text", "plausible" or "stretch".

3. settled: the words or phrases you would treat as clear enough to apply without a question, each with one line on why."""


ALIASES = {  # the claude CLI does not enforce the schema; map the key names it chose
    'node': ('node', 'node_id'), 'open_words': ('open_words', 'rule_words', 'words'),
    'answers': ('answers', 'candidates', 'candidate_answers'), 'support': ('support', 'label'),
    'words': ('words', 'phrase', 'term'), 'quote': ('quote', 'text', 'rule_words'),
}


def _get(d, key, default=''):
    for k in ALIASES.get(key, (key,)):
        if k in d:
            return d[k]
    return default


def normalize(reply):
    qs = []
    for i, q in enumerate(reply.get('questions', [])):
        qs.append(dict(id=q.get('id') or f'q{i + 1}', node=_get(q, 'node'), open_words=_get(q, 'open_words'),
                       question=q.get('question', ''),
                       answers=[dict(answer=a.get('answer', ''), support=_get(a, 'support')) for a in _get(q, 'answers', [])]))
    return dict(nodes=[dict(id=n.get('id', ''), quote=_get(n, 'quote'), role=n.get('role', ''),
                            depends_on=n.get('depends_on', [])) for n in reply.get('nodes', [])],
                questions=qs,
                settled=[dict(words=_get(s, 'words'), why=s.get('why', '')) for s in reply.get('settled', [])])


def match_prompt(law, gen):
    planted = '\n'.join(f"- {p['id']}: {p['question']}\n" + '\n'.join(f'    answer {i}: {a}' for i, a in enumerate(p['answers']))
                        for p in PLANTED[law])
    qs = '\n'.join(f"- {q['id']}: {q['question']}\n" + '\n'.join(f"    - {a['answer']} [{a['support']}]" for a in q['answers'])
                   for q in gen['questions'])
    return f"""You are checking whether a reader of a rule raised the interpretive questions that the rule's authors planted.

THE RULE
{law_text(law)}

PLANTED QUESTIONS (with numbered answers)
{planted}

QUESTIONS THE READER RAISED (with the reader's candidate answers)
{qs}

Return JSON.
- generated: for every question the reader raised, the id of the planted question it asks about, or null if it asks about something else. A reader question matches a planted one if answering it would settle the same issue, even if worded differently or broader.
- planted: for every planted question, the reader question ids that match it, and the numbers of the planted answers that appear among the reader's candidate answers for those questions (same meaning, any wording). For yes/no planted questions, count an answer as present if some reader answer takes that side.

Reply with JSON only, in exactly this shape:
{{"generated": [{{"qid": "<reader question id>", "planted_id": "<planted id or null>"}}],
  "planted": [{{"id": "<planted id>", "matched_qids": ["<reader question id>"], "answers_covered": [<answer numbers>]}}]}}"""


def run(out, workers=8):
    out = Path(out)
    raw, gen_dir, match_dir = out / 'raw', out / 'generated', out / MATCH_DIR
    for d in (raw, gen_dir, match_dir):
        d.mkdir(parents=True, exist_ok=True)
    jobs = [(law, m, k) for law in PLANTED for m in GENERATORS for k in range(SAMPLES)]

    def one(job):
        law, m, k = job
        stem = f"{law}__{m.replace(':', '_')}__s{k}"
        g = gen_dir / f'{stem}.json'
        call(m, gen_prompt(law), GEN_SCHEMA, stem, raw, g)
        if not g.exists():
            return
        reply = normalize(json.loads(g.read_text())['reply'])
        call(MATCHER, match_prompt(law, reply), MATCH_SCHEMA, f'match__{stem}', raw, match_dir / f'{stem}.json')

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, jobs))


def _norm(s):
    return re.sub(r'\s+', ' ', s.replace('’', "'").replace('“', '"').replace('”', '"')).strip().lower()


def anchor_failures(law, reply):
    """Scripted check: node quotes and open words must be verbatim spans of the rule."""
    text = _norm(law_text(law))
    bad = [n['quote'] for n in reply['nodes'] if _norm(n['quote']).strip('."') not in text]
    bad += [q['open_words'] for q in reply['questions'] if _norm(q['open_words']).strip('."') not in text]
    return bad


def analyse(out):
    out = Path(out)
    rows, settled, new_qs, errors = [], {}, {}, []
    for g in sorted((out / 'generated').glob('*.json')):
        if g.name.endswith('.error.json'):
            errors.append(json.loads(g.read_text()))
            continue
        law, model, sample = g.stem.split('__')
        reply = normalize(json.loads(g.read_text())['reply'])
        mpath = out / MATCH_DIR / g.name
        if not mpath.exists():
            errors.append(dict(stem=g.stem, error='matcher failed', detail=json.loads(mpath.with_suffix('.error.json').read_text()) if mpath.with_suffix('.error.json').exists() else None))
            continue
        match = json.loads(mpath.read_text())['reply']
        planted = {p['id']: p for p in PLANTED[law]}
        hit = {p['id']: p for p in match['planted'] if p['id'] in planted}
        n_hit = sum(bool(hit.get(i, {}).get('matched_qids')) for i in planted)
        ans_tot = sum(len(planted[i]['answers']) for i in planted)
        ans_cov = sum(len({a for a in hit.get(i, {}).get('answers_covered', []) if 0 <= a < len(planted[i]['answers'])})
                      for i in planted if hit.get(i, {}).get('matched_qids'))
        unmatched = [q for q in reply['questions']
                     if not any(x['qid'] == q['id'] and x['planted_id'] in planted for x in match['generated'])]
        rows.append(dict(law=law, model=model, sample=sample, n_nodes=len(reply['nodes']),
                         n_questions=len(reply['questions']), planted_found=n_hit, planted_total=len(planted),
                         answers_covered=ans_cov, answers_total=ans_tot, new_questions=len(unmatched),
                         anchor_failures=len(anchor_failures(law, reply)),
                         found=sorted(i for i in planted if hit.get(i, {}).get('matched_qids'))))
        settled.setdefault(law, []).extend(f"{s['words']} -- {s['why']}" for s in reply['settled'])
        new_qs.setdefault(law, []).extend(f"[{model} {sample}] {q['question']}" for q in unmatched)
    summary = {}
    for law in PLANTED:
        for model in sorted({r['model'] for r in rows if r['law'] == law}):
            rs = [r for r in rows if r['law'] == law and r['model'] == model]
            summary[f'{law}|{model}'] = dict(
                samples=len(rs),
                planted_found_per_sample=[r['planted_found'] for r in rs],
                planted_found_union=len(set().union(*[r['found'] for r in rs])) if rs else 0,
                planted_total=len(PLANTED[law]),
                answers_covered_per_sample=[r['answers_covered'] for r in rs],
                answers_total=rs[0]['answers_total'] if rs else None,
                questions_per_sample=[r['n_questions'] for r in rs],
                new_questions_per_sample=[r['new_questions'] for r in rs],
                anchor_failures=sum(r['anchor_failures'] for r in rs),
                never_found=sorted(set(p['id'] for p in PLANTED[law]) - set().union(*[r['found'] for r in rs])) if rs else None)
    (out / 'rows.json').write_text(json.dumps(rows, indent=1))
    (out / 'summary.json').write_text(json.dumps(dict(summary=summary, errors=errors), indent=1))
    (out / 'settled.json').write_text(json.dumps(settled, indent=1))
    (out / 'new_questions.json').write_text(json.dumps(new_qs, indent=1))
    print(json.dumps(dict(summary=summary, n_errors=len(errors)), indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['run', 'analyse', 'prompts'])
    ap.add_argument('--out', default='runs/rulegap_20261117/question_tree')
    a = ap.parse_args(argv)
    if a.cmd == 'prompts':
        for law in PLANTED:
            print(f'===== {law}\n{gen_prompt(law)}\n')
    elif a.cmd == 'run':
        run(a.out)
        analyse(a.out)
    else:
        analyse(a.out)


if __name__ == '__main__':
    main()
