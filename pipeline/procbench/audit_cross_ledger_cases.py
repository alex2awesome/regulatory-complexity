"""Find shared individual-case quotations across evidence ledgers for review.

This is a candidate generator. Matching wording may be a quotation, copying,
boilerplate or one application cross-posted into another thread. It does not
merge cases, discard claims, or prove distinctness when no match is found.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from .evidence_contract import normalized_quote


def audit(paths, minimum_characters=80):
    groups, inputs = defaultdict(list), []
    for path in paths:
        raw = path.read_bytes()
        ledger = json.loads(raw)
        inputs.append(dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                           program_id=ledger['program_id']))
        for row in ledger['measurements']:
            quote = normalized_quote(row['quote'])
            if row.get('case_id') is None or row['statistic'] != 'individual' or len(quote) < minimum_characters:
                continue
            groups[quote].append(dict(ledger=str(path), program_id=ledger['program_id'],
                measurement_id=row['id'], case_id=row['case_id'], doc_id=row['doc_id'],
                metric=row['metric'], value=row['value'], lower=row['lower'], upper=row['upper'],
                unit=row['unit'], interpretation=row['interpretation']))
    candidates = []
    for quote, rows in groups.items():
        if len({r['ledger'] for r in rows}) < 2 or len({r['case_id'] for r in rows}) < 2:
            continue
        candidates.append(dict(quote_sha256=hashlib.sha256(quote.encode()).hexdigest(),
            quote=quote, claims=rows, review_status='unreviewed',
            automatic_merge=False, automatic_exclusion=False))
    candidates.sort(key=lambda row: row['quote_sha256'])
    return dict(schema_version='cross-ledger-case-candidates/1', inputs=inputs,
        minimum_quote_characters=minimum_characters, candidate_groups=len(candidates),
        candidates=candidates,
        limitations=['Exact normalized quotation matching does not measure recall.',
            'Different cases can quote the same rule or earlier post.',
            'One case can have distinct repeated observations or application episodes.',
            'Semantic source review is required before any case or likelihood changes.'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--evidence', nargs='+', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError('Preserve earlier audit: ' + str(args.out))
    report = audit(args.evidence)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(ledgers=len(report['inputs']), candidate_groups=report['candidate_groups'])))


if __name__ == '__main__':
    main()
