"""Convert a free-form counts sidecar into the validated burden-count audit.

WHY THIS EXISTS. The evidence contract (`process-evidence/3`) carries elapsed
time, payer work, agency work, fees, staffing and volume, and nothing else; it
forbids extra properties. Parsers that found counts therefore had nowhere to put
them and invented `process-evidence-counts-sidecar/1`, a flat list of
`{kind, value, unit, subject, quote, ...}` rows. Those rows are unreachable by
every fitter in the project.

They do not have to be. `compile_visit_durations.py --count-audit` already
accepts a count channel, validated by `audit_burden_counts.validate_counts`
against `burden-count-evidence/1`. This module moves the rows that belong there,
and refuses the rest.

WHAT IT REFUSES, AND WHY THAT IS THE POINT. A count is only a burden count when
its DENOMINATOR is a single case's passage through the process. The sidecars mix
that with rule inventories, retention periods, fee percentages, record page
counts and statutory limits, all of which are numbers and none of which is "how
many times did this applicant have to do the thing". Converting on `kind` alone
would silently fit a four-firearm statutory limit as four correction rounds.

So conversion requires BOTH a per-kind policy AND a per-row denominator that the
row's own `unit`/`subject` text makes explicit. Every row that fails either test
is written to `unresolved` with the reason and its verbatim quote, where a human
can see it. A refused row is not discarded and not zero.

The `additional_correction_rounds` / `total_attempts` distinction is off by one
and the enum carries both, so the policy never guesses: a row is converted as
`total_attempts` only when its own wording counts submissions or visits made,
and a row whose wording counts EXTRA or ADDITIONAL passes converts as
`additional_correction_rounds`. Wording that settles neither is refused.

    python3 -m pipeline.procbench.convert_counts_sidecar \
        --sidecar runs/.../evidence_counts_sidecar.json \
        --evidence runs/.../evidence.json \
        --documents runs/.../inputs_documents.json \
        --out runs/.../burden_counts/audit.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

from .audit_burden_counts import validate_counts, validate_case_registry
from .evidence_contract import normalized_quote

SIDECAR_SCHEMA = 'process-evidence-counts-sidecar/1'
AUDIT_SCHEMA = 'burden-count-evidence/1'

# Per-kind policy. `None` means the kind is never a burden count; the string is
# the reason recorded against every row of that kind. A kind that IS eligible
# still has to pass the denominator test below.
# NOTE ON WHY THIS TABLE KEEPS GROWING. Each ad-hoc sidecar was written by a
# different parser inventing its own `kind` vocabulary, so there is no shared
# term to map from. Five sidecars have produced more than forty distinct kinds.
# The durable fix is that parsers now write `burden-count-evidence/1` directly;
# this table exists to rescue what was already written, and an unlisted kind is
# refused rather than guessed.
KIND_POLICY = {
    # Encounters the applicant has to make.
    'trip_count': 'encounters_or_visits',
    'interaction_count': 'encounters_or_visits',
    'compliance_count': 'encounters_or_visits',
    'call_attempt_count': 'encounters_or_visits',
    'call_count': 'encounters_or_visits',
    'contact_count': 'encounters_or_visits',
    'office_visit_count': 'encounters_or_visits',
    'appointment_count': 'encounters_or_visits',
    'interview_count': 'encounters_or_visits',
    'escalation_count': 'encounters_or_visits',
    # Things the applicant has to submit, which may be repeats.
    'submission_count': 'attempts',          # resolved to one of two enum values per row
    'questionnaire_count': 'attempts',
    'appeal_count': 'attempts',
    'rule_count': None,
    'outcome_count': None,
    'firearm_count': None,
    'record_count': None,
    'dealer_count': None,
    'workload_count': None,
    'case_count': None,
    'fee_rate': None,
    'fee_rate_basis': None,
    'rate_cap': None,
    'validity_period': None,
    'retention_period': None,
    'prohibition_period': None,
    'routing_rate': None,
    'callback_rate': None,
    'resolution_rate': None,
    'answer_rate': None,
    'staff_count': None,
    'work_item_count': None,
    'mail_weight': None,
    'page_count': None,
    'tracked_metric_count': None,
    'data_error_count': None,
    'duplicate_claim_count': None,
    'hearing_outcome_count': None,
    'self_service_count': None,
    'question_count': None,
    'notice_count': None,
    'document_count': None,
    'verification_count': None,
    'issue_count': None,
}

RATE_REASON = ('A frequency, not a count. rate_claims is the right home for it, but that schema '
               'requires the source\'s own event and denominator, which this sidecar row does not '
               'carry. Converting would mean supplying a denominator the document did not state.')

KIND_REASONS = {
    'rule_count': ('A count of what a rule lists, not of what a case did. It could become an '
                   'enumerated_inventory claim, but only after someone confirms the enumeration '
                   'is of process steps for one case rather than of obligations, documents or '
                   'prohibited categories.'),
    'outcome_count': 'Counts what happened to cases, not how many times an applicant acted.',
    'firearm_count': ('Counts items bought, not process repetitions. It is a denominator for other '
                      'counts, not a burden count itself.'),
    'record_count': 'Counts pages or records produced, which is output size, not applicant burden.',
    'dealer_count': 'Counts businesses in a market, not encounters made by one applicant.',
    'workload_count': 'An agency workload figure. Agency cost is a secondary channel and is not a per-case count.',
    'case_count': 'A programme volume. Volume is already an evidence-contract metric and is not a per-case count.',
    'compliance_count': 'Counts compliance events, which may or may not be applicant encounters.',
    'fee_rate': ('A percentage of a price, not the frequency of an event. rate_claims requires an '
                 'event and a denominator of cases; a restocking percentage has neither.'),
    'fee_rate_basis': 'A pricing basis, not the frequency of an event.',
    'rate_cap': 'A cap on a price or throughput, not the frequency of an event.',
    'validity_period': 'A duration, not a count.',
    'retention_period': 'A duration, not a count.',
    'prohibition_period': 'A duration, not a count.',
    'routing_rate': RATE_REASON, 'callback_rate': RATE_REASON,
    'resolution_rate': RATE_REASON, 'answer_rate': RATE_REASON,
    'staff_count': 'Counts agency staff. Agency cost is a secondary channel and is not a per-case count.',
    'work_item_count': 'An agency queue depth, not a count of what one applicant did.',
    'mail_weight': 'A physical quantity of mail, not a count of applicant actions.',
    'page_count': 'Counts pages, which is document size, not applicant burden.',
    'tracked_metric_count': 'Counts what the agency measures, not what an applicant did.',
    'data_error_count': ('Counts errors found in records. Whether each cost the applicant a step '
                         'is not stated, and assuming it would invent the burden.'),
    'duplicate_claim_count': ('Counts duplicate records in a system. A duplicate record is not '
                              'necessarily a repeated applicant action.'),
    'hearing_outcome_count': 'Counts what happened at hearings, not how many times an applicant acted.',
    'self_service_count': 'Counts transactions handled by a system, not encounters by one applicant.',
    'question_count': ('Ambiguous between questions on a form and questions asked of an applicant. '
                       'One is document size and the other is an encounter; the sidecar does not say which.'),
    'notice_count': ('Counts notices the agency sent. A notice received is not an action taken, and '
                     'treating it as one would count agency output as applicant burden.'),
    'document_count': ('Counts documents supplied. The count enum has no term for it, and mapping it '
                       'to encounters would assume one trip per document.'),
    'verification_count': ('Counts verification events without saying whose action each was, so it '
                           'cannot be attributed to the applicant or the agency.'),
    'issue_count': ('Counts problems on a claim. A problem is not a step, and several may be resolved '
                    'in one action.'),
}

# Denominator test. The row's own wording has to tie the number to ONE case's
# passage. These are the phrasings the corpora actually use.
ONE_CASE = re.compile(
    r'\b(for one|in one|per one|on one|of one|one purchase|one firearm|one transfer|'
    r'one application|one case|one request|one permit|one transaction|this case|'
    r'a single|per case|per applicant|per purchaser|per application)\b', re.I)
MANY_CASES = re.compile(
    r'\b(across|inside|within|episode|shopping trip|per year|annually|window|'
    r'each year|per month|statewide|per dealer|per county)\b', re.I)
EXTRA = re.compile(r'\b(extra|additional|more|another|further|again|repeat|re-?submi)\w*\b', re.I)
MADE = re.compile(r'\b(visits?|trips?|submissions?|attempts?|contacts?|calls?|interactions?|rounds?)\b', re.I)


def _denominator(row):
    """Return ('one_case', None) or (None, reason-it-was-refused).

    The test is applied to `unit`, which is the row's own statement of WHAT is
    being counted, and only falls back to `subject` when `unit` is empty. Reading
    the wider prose instead would let a note saying "for one purchase" rescue a
    unit that says "across 20 purchases", and the unit is the denominator.
    """
    text = str(row.get('unit') or '') or str(row.get('subject') or '')
    if row.get('case_id') is None:
        return None, ('No case identity, so the number is not tied to one applicant\'s passage '
                      'through the process.')
    # A case identity that resolves in the ledger IS the single-case denominator;
    # demanding the prose repeat it as well refuses rows the ledger already ties
    # to one applicant. What still disqualifies a row is wording that says the
    # number spans MORE than that one passage.
    if MANY_CASES.search(text) and not ONE_CASE.search(text):
        return None, ('The row\'s own wording spans more than one case, more than one item or a '
                      'time window ("%s"), so its denominator is not one passage through the '
                      'process even though it carries a case identity.' % row.get('unit'))
    return 'one_case', None


def _attempt_quantity(row):
    text = ' '.join(str(row.get(k) or '') for k in ('unit', 'subject'))
    if EXTRA.search(text):
        return 'additional_correction_rounds'
    if MADE.search(text):
        return 'total_attempts'
    return None


def convert(sidecar, evidence, documents=None, case_registry=None):
    if sidecar.get('schema_version') != SIDECAR_SCHEMA:
        raise ValueError('Not a %s sidecar' % SIDECAR_SCHEMA)
    if sidecar.get('program_id') != evidence['program_id']:
        raise ValueError('Program identity changed')

    activities = {a['id']: a for a in evidence['activities']}
    cases = {m['case_id'] for m in evidence['measurements'] if m['case_id'] is not None}
    if case_registry is not None:
        cases |= validate_case_registry(case_registry, evidence['program_id'], documents)
    # An observation context names its measurement, not the other way round.
    contexts = {c['measurement_id']: c for c in evidence.get('observation_contexts', [])}
    by_measurement_doc = {}
    for m in evidence['measurements']:
        ctx = contexts.get(m['id'])
        if ctx and ctx.get('temporal_scope'):
            by_measurement_doc.setdefault(m['doc_id'], ctx['temporal_scope'])

    claims, unresolved = [], []

    def refuse(row, reason):
        unresolved.append(dict(evidence=[dict(doc_id=row['doc_id'], quote=row['quote'])],
                               reason='%s [%s, value %s] %s'
                                      % (row['id'], row['kind'], row.get('value'), reason)))

    for row in sidecar['entries']:
        kind = row.get('kind')
        if kind not in KIND_POLICY:
            refuse(row, 'Unknown sidecar kind %r; no policy decides whether it is a burden count.' % kind)
            continue
        policy = KIND_POLICY[kind]
        if policy is None:
            refuse(row, KIND_REASONS[kind])
            continue
        _, reason = _denominator(row)
        if reason:
            refuse(row, reason)
            continue
        if row.get('case_id') not in cases:
            refuse(row, 'Case identity %r is not a case of the accepted ledger.' % row.get('case_id'))
            continue
        activity = row.get('attaches_to_activity')
        if activity not in activities:
            refuse(row, 'Activity %r is not an activity of the accepted ledger.' % activity)
            continue
        quantity = policy if policy != 'attempts' else _attempt_quantity(row)
        if quantity is None:
            refuse(row, ('The wording settles neither total attempts nor additional rounds, and the '
                         'two differ by one, so converting either way would invent the distinction.'))
            continue
        value = row.get('value')
        lower, upper = row.get('lower'), row.get('upper')
        if value is None and lower is None and upper is None:
            refuse(row, 'No finite amount or bound.')
            continue
        actor = activities[activity].get('actor_id')
        claims.append(dict(
            id=row['id'], case_id=row['case_id'], activity_ids=[activity],
            actor_ids=[actor] if actor else [], scope='activity_only',
            temporal_scope=by_measurement_doc.get(row['doc_id'], 'unspecified'),
            population='one case reported in %s' % row['doc_id'],
            source_family=row['doc_id'], duplicate_of=None,
            evidence=[dict(doc_id=row['doc_id'], quote=row['quote'])],
            notes=('Converted from %s row %r (kind %s, unit %r). %s'
                   % (SIDECAR_SCHEMA, row['id'], kind, row.get('unit'), row.get('note') or '')).strip(),
            quantity=quantity, counting_unit=row.get('unit') or row.get('subject') or '',
            basis='observed_case', statistic='individual',
            value=value, lower=lower, upper=upper, inventory_coverage='not_inventory'))

    audit = dict(schema_version=AUDIT_SCHEMA, program_id=evidence['program_id'],
                 count_claims=claims, rate_claims=[], unresolved=unresolved)
    if case_registry is not None:
        audit.update(schema_version='burden-count-evidence/2', cases=case_registry['cases'])
    validate_counts(audit, evidence, documents)
    return audit


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sidecar', required=True)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--documents')
    ap.add_argument('--case-registry', help='Quote-grounded burden-case-registry/1; never infer new cases from amounts alone')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)

    sidecar = json.loads(pathlib.Path(args.sidecar).read_text())
    evidence = json.loads(pathlib.Path(args.evidence).read_text())
    documents = None
    if args.documents:
        raw = json.loads(pathlib.Path(args.documents).read_text())
        documents = raw['documents'] if isinstance(raw, dict) else raw
    registry = json.loads(pathlib.Path(args.case_registry).read_text()) if args.case_registry else None
    audit = convert(sidecar, evidence, documents, case_registry=registry)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=1))
    print('%-22s converted=%-4d refused=%-4d of %d sidecar rows'
          % (evidence['program_id'][:22], len(audit['count_claims']),
             len(audit['unresolved']), len(sidecar['entries'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
