"""Real-world cases: provenance checks and the E0 rater packet.

Fetched files are parsed as text only. A spec's rule text and every sourced
reading must quote a retained file: the file's hash must match the manifest and
the quote must be a substring of the file's visible text.
"""
import hashlib
import html
import json
from pathlib import Path
import re

KINDS = ('statute_definition', 'software_default', 'practice_verdict', 'audit_definition',
         'author_catalog', 'benchmark_gold', 'text_literal', 'authored')


def visible_text(path):
    s = Path(path).read_text(errors='ignore')
    s = re.sub(r'<(script|style).*?</\1>', ' ', s, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s)))


def check_sources(spec):
    """Scripted check for a real spec. Returns a list of problems."""
    root = spec.path.parent / 'sources'
    manifest = {}
    for line in (root / 'manifest.jsonl').read_text().splitlines():
        row = json.loads(line)
        manifest[row['file']] = row
    problems, texts = [], {}

    def quote_ok(src, label):
        if src.get('kind') not in KINDS:
            problems.append(f'{label}: unknown source kind {src.get("kind")!r}')
        if src.get('kind') == 'authored':
            return
        f = src.get('file')
        if f not in manifest or not manifest[f]['bytes']:
            problems.append(f'{label}: source file {f!r} missing from manifest or empty')
            return
        raw = (root / 'raw' / f).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest[f]['sha256']:
            problems.append(f'{label}: {f} does not match its manifest hash')
        if f not in texts:
            texts[f] = visible_text(root / 'raw' / f)
        if src['quote'] not in texts[f]:
            problems.append(f'{label}: quote not found in {f}: {src["quote"][:60]!r}')
    quote_ok(spec.raw['text_source'], 'text_source')
    if spec.raw['text_source']['quote'] not in spec.raw['templates']['open']:
        problems.append('rule text is not the quoted source sentence')
    for term, t in spec.terms.items():
        for rid, r in t['readings'].items():
            for i, src in enumerate(r.get('sources') or [dict(kind=None)]):
                quote_ok(src, f'{term}.{rid}[{i}]')
    return problems


def rater_packet(spec, rung='open'):
    """E0 step 1 packet: text and background only. No intended reading, no sources."""
    from .render import render
    lines = [f'# Rater packet: {spec.rule_id}', '', '## Instructions', '', spec.raw['background'].strip(), '',
             'This is term-level screening only; it does not validate complete interpretations. '
             'Use cli e0-build for the whole-interpretation review and ratings that can enter analysis. '
             'For each candidate meaning below, mark whether a careful reader could defend it from the rule text alone. '
             'Do not consult any other material. Then note any meaning you think is missing.', '',
             '## Rule text', '', '> ' + render(spec, rung).text.replace('\n', '\n> '), '']
    for term in spec.active_terms(rung):
        t = spec.terms[term]
        if t['kind'] != 'cat':
            continue
        name = spec.raw['templates']['term_text'][term].format(**spec.constants(rung))
        lines += [f'## "{name}"', '', '| # | Candidate meaning | Defensible (Y/N) | Comment |', '|---|---|---|---|']
        # Fixed alphabetical order so the list does not reveal the spec's ordering.
        for i, rid in enumerate(sorted(t['values'], key=lambda r: t['readings'][r]['printed']), 1):
            lines.append(f"| {i} | {t['readings'][rid]['printed']} |  |  |")
        lines += ['', 'Missing meanings:', '']
    return '\n'.join(lines) + '\n'
