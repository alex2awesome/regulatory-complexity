"""Flag fee measurements whose own quotation contradicts the scope they carry.

WHY. `burden_channels.fee_compilation()` reads the contract `scope` field to
decide what an amount is: `process` becomes a whole-case path total, `step` and
`segment` become named totals over the listed activities, and `standing` is
refused because a recurring amount is not a process path total. That fix stopped
a class of error where every case-linked amount compiled as the cost of the
permit.

It cannot stop a second class, because it trusts `scope`. A parser can record an
amount as `process` scope in good faith when the applicant was describing
something else: a yearly overhead figure, or a setup estimate that bundles
insurance and bonding with the agency's fees. Compiled as a path total, an
annual overhead becomes the price of the permit.

This reads each fee measurement's own verbatim quotation and reports where the
words disagree with the field:

* RECURRENCE. The quote says per year, a month, annually, each year. A recurring
  amount has no single value on a path that is traversed once. `standing` scope
  is already refused downstream; the same words under `process` scope are not.
* BUNDLING. The quote says the figure includes, or is inclusive of, components
  the process does not charge -- insurance, bonding, a contractor's own price,
  equipment, materials, wages. A total that contains a market price is not a
  price the process sets.
* CONSEQUENTIAL. The quote frames the money as lost, forgone or spent WHILE
  waiting. That is a real burden, and the user ranks external delay costs third
  among priorities, but it is not a fee and must not be summed with fees.

This reports; it changes nothing. Every hit needs a human, because the words
that trigger it also appear in legitimate quotations, and a false positive is
cheap while a silent contamination is not.

    python3 -m pipeline.procbench.audit_fee_scope --evidence runs/.../evidence.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

# Scopes whose amounts are summed onto a path that is traversed once.
PATH_SCOPES = {'process', 'segment', 'step'}

# NOTE: "renewal fee" is deliberately NOT a recurrence marker. A renewal is a
# separate instance of the process with its own single payment, not an amount
# that repeats within one path. Including it produced 24 false positives out of
# 44 flags on the first run, which would have made this tool noise.
RECURRENCE = re.compile(
    r'(\bper\s+(?:year|month|week|annum)\b|/\s*(?:yr|year|mo|month)\b|\bannual(?:ly)?\b|'
    r'\ba\s+(?:year|month)\b|\beach\s+(?:year|month)\b|\bmonthly\b|\byearly\b)', re.I)
BUNDLING = re.compile(
    r'\b(includ(?:es|ing|ed)|inclusive of|that includes|plus)\b[^.]{0,80}?'
    r'\b(insurance|bonding|bond|materials?|equipment|labou?r|wages?|contractor|installer|'
    r'system|panels?|rent|salary|tuition|classes|school)\b', re.I)
CONSEQUENTIAL = re.compile(
    r'\b(over\s?head|overhead|lost (?:income|revenue|wages|rent)|out of pocket while|'
    r'while (?:i|we|they) waited|during the (?:wait|delay)|forgone|foregone|'
    r'carrying costs?|holding costs?|lost business)\b', re.I)


AMOUNT = re.compile(r'\$\s?\d')
# A charge that names its own period is recurring however long the extract is,
# and however much whitespace padding a PDF table left around it.
NAMED_RECURRING = re.compile(
    r'\b(annual|monthly|yearly|quarterly|per[- ]annum)\s+(fee|charge|dues|assessment|rent|tax|'
    r'premium|subscription|renewal)\b', re.I)


def _collapse(text):
    """Length as a reader sees it: PDF table extracts carry runs of padding."""
    return re.sub(r'\s+', ' ', text).strip()
SHORT_QUOTE = 120
NEAR = 40


def _recurs(quote):
    """A recurrence marker counts only where it plausibly qualifies an amount.

    Fee schedules are extracted as whole table blocks, and those blocks carry
    column headers like "Estimated Annual Volume". A bare search for "annual"
    then flags one-time per-site fees, which is how this check first produced
    nineteen false positives on a fee-study corpus. So in a long quote the
    marker has to sit within %d characters of a currency amount, the way a
    price states its period ("$605/year"). A short quote is taken as a caption
    or a sentence about one amount, where no such window exists.
    """ % NEAR
    if NAMED_RECURRING.search(quote):
        return True                      # the charge names its own period
    hits = list(RECURRENCE.finditer(quote))
    if not hits:
        return False
    if len(_collapse(quote)) <= SHORT_QUOTE:
        return True
    spans = [a.start() for a in AMOUNT.finditer(quote)]
    return any(abs(h.start() - s) <= NEAR for h in hits for s in spans)


def audit(evidence):
    hits = []
    for m in evidence['measurements']:
        if m['metric'] != 'fee' or m.get('scope') not in PATH_SCOPES:
            continue
        quote = m.get('quote') or ''
        flags = []
        if _recurs(quote):
            flags.append('recurrence: the quote states a repeating amount, which has no single '
                         'value on a path traversed once')
        if BUNDLING.search(quote):
            flags.append('bundling: the quote says the figure includes components the process does '
                         'not charge, so it is not a price the process sets')
        if CONSEQUENTIAL.search(quote):
            flags.append('consequential: the quote frames the money as lost or spent while waiting, '
                         'which is a real burden but is not a fee and must not be summed with fees')
        if flags:
            hits.append(dict(measurement_id=m['id'], scope=m['scope'], statistic=m['statistic'],
                             value=m['value'], lower=m['lower'], upper=m['upper'],
                             case_id=m.get('case_id'), doc_id=m['doc_id'],
                             quote=quote, flags=flags))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', nargs='+', required=True)
    ap.add_argument('--json-out')
    args = ap.parse_args(argv)

    report, total_fees, total_hits = [], 0, 0
    for path in args.evidence:
        evidence = json.loads(pathlib.Path(path).read_text())
        fees = sum(1 for m in evidence['measurements'] if m['metric'] == 'fee')
        hits = audit(evidence)
        total_fees += fees
        total_hits += len(hits)
        report.append(dict(program_id=evidence['program_id'], path=path,
                           fee_measurements=fees, flagged=hits))
        print('%-46s fees=%-4d flagged=%d' % (evidence['program_id'][:46], fees, len(hits)))
        for h in hits:
            print('    %-44s %10s  %s' % (h['measurement_id'][:44], h['value'],
                                          h['quote'].replace('\n', ' ')[:82]))
            for f in h['flags']:
                print('        - %s' % f)
    print('\n%d fee measurements, %d flagged for review' % (total_fees, total_hits))
    if args.json_out:
        out = pathlib.Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(schema_version='fee-scope-audit/1',
                                       WHAT_THIS_IS=('Reported contradictions between a fee '
                                                     'measurement\'s scope field and its own quotation. '
                                                     'Nothing is changed; every hit needs a human.'),
                                       fee_measurements=total_fees, flagged=total_hits,
                                       programs=report), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
