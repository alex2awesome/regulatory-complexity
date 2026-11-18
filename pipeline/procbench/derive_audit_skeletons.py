"""Write the work order for the two per-measurement audits a ledger still needs.

WHY. A ledger reaches V6 only through `compile_visit_durations.py`, which
requires a visit-observation audit and a measurement-semantics audit, one row
per eligible measurement. Those rows decide what a figure MEANS: whether a
published duration is waiting or service, where its clock starts and stops,
whether the case was still open when it was reported. That is the semantic
judgement this project exists to make, and nothing here automates it.

What this module removes is the part that is not judgement. Today an author has
to enumerate the eligible measurements, copy each one's quotations, restate its
activity identities, and get two schemas right, before deciding anything. Across
the thirteen parsed ledgers that is 753 rows of clerical work wrapped around 753
decisions.

So this writes a SKELETON: every eligible measurement, already carrying its own
verified quotations, its activity identities, its stated unit, and the ledger
context needed to decide, with each judgement field left as an explicit
placeholder and listed in that row's `to_decide`.

IT IS DELIBERATELY NOT THE AUDIT SCHEMA. The output declares
`visit-audit-skeleton/1` and `semantic-audit-skeleton/1`, which no consumer
accepts. A placeholder can therefore never be mistaken for a decision, and the
skeleton cannot be fed to the compiler by accident. Turning it into a real audit
means replacing every placeholder and emptying every `to_decide`.

ONE FIELD IS DERIVED RATHER THAN PLACEHELD: `original_precision_unit`, which
restates the unit the ledger already recorded. Nothing else is filled, including
`reporting_sample`, whose enum has no abstention value and whose honest default
would otherwise be the substantive value `other`.

    python3 -m pipeline.procbench.derive_audit_skeletons \
        --evidence runs/.../evidence.json --documents runs/.../artifacts \
        --out-dir runs/.../compile/inputs
"""
from __future__ import annotations

import argparse
import json
import pathlib

from .audit_measurement_semantics import eligible
from .evidence_contract import normalized_quote, validate

PLACEHOLDER = '__DECIDE__'

UNIT_MAP = {
    'minutes': 'minutes', 'minute': 'minutes',
    'hours': 'hours', 'hour': 'hours',
    'calendar_days': 'calendar_days', 'days': 'calendar_days',
    'business_days': 'business_days', 'working_days': 'business_days',
    'weeks': 'weeks', 'week': 'weeks',
    'months': 'months', 'month': 'months',
}

VISIT_DECISIONS = {
    'identification': ('explicit / context_supported / unresolved',
                       'Does the document name this measurement\'s subject, or is it read from context?'),
    'activity_mapping': ('supported / unresolved / contradicted / not_applicable',
                         'Do the ledger activity identities this row carries actually match what the quote measures?'),
    'basis': ('whole_case_clock / single_visit_cycle / sum_visit_cycles / '
              'first_to_last_activity_span / wait_elapsed / service_elapsed / unknown',
              'A sum of visit cycles omits the time BETWEEN visits; a first-to-last span includes it. '
              'A task name followed by a duration settles neither.'),
    'start': ('process_start / first_submission / first_complete_submission / first_activity_start / '
              'single_visit_start / service_start / appointment_request / other_milestone / unknown',
              'First filing is the first submission event, not the completion of all corrections.'),
    'end': ('initial_decision / final_decision / latest_recorded_decision / legal_closeout / '
            'end_of_modeled_work / last_activity_end / single_visit_end / service_start / service_end / '
            'observation_time / other_milestone / unknown',
            'An unspecified "approved", "done" or "end to end" does NOT establish the decision\'s ordinal '
            'position. End of modelled work is not legal closeout.'),
    'visits': ('first / last / one_unspecified / all_completed_by_observation / all_in_completed_case / '
               'reported_subset / not_applicable / unknown',
               'Use not_applicable on a whole-case clock. For a sum, say whether all visits or only a '
               'reported subset are established.'),
    'censoring': ('none / right / left / unresolved',
                  'An open case can already hold a permit; an unfinished case does not mean the initial '
                  'decision is still pending.'),
}

SEMANTIC_DECISIONS = {
    'duration_basis': ('whole_case / stage_span / single_visit / wait_only / service_only / '
                       'elapsed_so_far / unresolved',
                       'Wait-only against service is the distinction that changes the answer most often.'),
    'start_event': ('preparation_start / first_submission / complete_submission / step_start / '
                    'after_milestone / unspecified', ''),
    'end_event': ('initial_decision / closeout / ongoing / step_end / unspecified', ''),
    'censoring': ('none / right / left / uncertain', ''),
    'population_scope': ('all_cases / selected_cohort / individual / unspecified',
                         'A first-visit summary, a summary of all visits and one case\'s cumulative time '
                         'have different populations.'),
    'reporting_sample': ('administrative / forum_selected / expert_estimate / other',
                         'This enum has NO abstention value, so it is left as a placeholder rather than '
                         'defaulted to "other", which is a substantive answer.'),
    'statistic_interpretation': ('individual_completion / individual_censored / population_mean / '
                                 'population_median / population_p90 / typical_range / '
                                 'informal_forecast / unresolved',
                                 'A typical official duration without a sample size is NOT a population median.'),
}


def _context(evidence):
    return {c['measurement_id']: c for c in evidence.get('observation_contexts', [])}


def _quotes(measurement, texts):
    refs = []
    quote = measurement.get('quote')
    if quote:
        if texts is not None and normalized_quote(quote) not in texts.get(measurement['doc_id'], ''):
            raise ValueError('NON-VERBATIM quote on measurement %s' % measurement['id'])
        refs.append(dict(doc_id=measurement['doc_id'], quote=quote))
    return refs


def _shared(measurement, context, texts):
    """The facts the decider needs, all already in the ledger."""
    return dict(
        measurement_id=measurement['id'],
        ledger_metric=measurement['metric'],
        ledger_statistic=measurement['statistic'],
        ledger_scope=measurement['scope'],
        ledger_unit=measurement['unit'],
        ledger_value=measurement['value'],
        ledger_lower=measurement['lower'],
        ledger_upper=measurement['upper'],
        ledger_n=measurement.get('n'),
        ledger_case_id=measurement.get('case_id'),
        ledger_source_family=measurement.get('source_family'),
        ledger_activity_ids=measurement.get('activity_ids') or [],
        ledger_start=measurement.get('start'),
        ledger_end=measurement.get('end'),
        ledger_interpretation=measurement.get('interpretation') or '',
        context_temporal_scope=(context or {}).get('temporal_scope'),
        context_segment_mode=(context or {}).get('segment_mode'),
        context_decision_activity_id=(context or {}).get('decision_activity_id'),
        context_notes=(context or {}).get('notes') or '',
        evidence=_quotes(measurement, texts))


def derive(evidence, documents=None):
    texts = ({d['id']: normalized_quote(d['text']) for d in documents}
             if documents is not None else None)
    contexts = _context(evidence)
    rows = eligible(evidence)

    visit, semantic = [], []
    for m in rows:
        shared = _shared(m, contexts.get(m['id']), texts)
        visit.append(dict(
            shared,
            identification=PLACEHOLDER, activity_mapping=PLACEHOLDER,
            operators=[dict(basis=PLACEHOLDER, activity_ids=shared['ledger_activity_ids'],
                            start=PLACEHOLDER, end=PLACEHOLDER, visits=PLACEHOLDER,
                            censoring=PLACEHOLDER, notes='')],
            notes='', to_decide=sorted(VISIT_DECISIONS)))
        semantic.append(dict(
            shared,
            duration_basis=PLACEHOLDER, start_event=PLACEHOLDER, end_event=PLACEHOLDER,
            censoring=PLACEHOLDER, population_scope=PLACEHOLDER, reporting_sample=PLACEHOLDER,
            statistic_interpretation=PLACEHOLDER,
            original_precision_unit=UNIT_MAP.get(m['unit'], 'unspecified'),
            notes='', to_decide=sorted(SEMANTIC_DECISIONS)))

    header = dict(
        program_id=evidence['program_id'],
        WHAT_THIS_IS=('A WORK ORDER, not an audit. Every %s is a placeholder that must be replaced '
                      'by a decision read from the documents. This file declares a skeleton schema '
                      'that no consumer accepts, so it cannot reach the compiler by accident.'
                      % PLACEHOLDER),
        eligibility_rule=('audit_measurement_semantics.eligible: elapsed metric, scope not standing, '
                          'statistic not statutory_cap or target, some amount stated, context not '
                          'historical or hypothetical.'),
        measurements_in_ledger=len(evidence['measurements']),
        elapsed_in_ledger=sum(1 for m in evidence['measurements'] if m['metric'] == 'elapsed'),
        eligible=len(rows),
        quotes_reverified=documents is not None)

    return (dict(header, schema_version='visit-audit-skeleton/1',
                 target_schema='visit-observation-evidence/1',
                 field_guide={k: dict(values=v[0], caution=v[1]) for k, v in VISIT_DECISIONS.items()},
                 measurements=visit, unresolved=[]),
            dict(header, schema_version='semantic-audit-skeleton/1',
                 target_schema='the ROW schema in audit_measurement_semantics.py',
                 derived_without_judgement=['original_precision_unit, restated from the ledger unit'],
                 field_guide={k: dict(values=v[0], caution=v[1]) for k, v in SEMANTIC_DECISIONS.items()},
                 measurements=semantic, unresolved=[]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--evidence', required=True)
    ap.add_argument('--documents', help='Directory of <doc_id>.md artifacts, for quote re-verification')
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args(argv)

    evidence = json.loads(pathlib.Path(args.evidence).read_text())
    documents = None
    if args.documents:
        documents = [dict(id=p.stem, text=p.read_text(errors='replace'))
                     for p in sorted(pathlib.Path(args.documents).glob('*.md'))]
        evidence = validate(evidence, documents)
    visit, semantic = derive(evidence, documents)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'visit_audit.skeleton.json').write_text(json.dumps(visit, indent=1))
    (out / 'semantic_audit.skeleton.json').write_text(json.dumps(semantic, indent=1))
    print('%-22s measurements=%-5d elapsed=%-5d ELIGIBLE=%-4d rows written=%d'
          % (evidence['program_id'][:22], visit['measurements_in_ledger'],
             visit['elapsed_in_ledger'], visit['eligible'], len(visit['measurements'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
