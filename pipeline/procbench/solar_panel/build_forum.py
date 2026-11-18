#!/usr/bin/env python3
"""Stage C preparation: build and verify the solar forum dataset. READ-ONLY.

Moved ahead of the model fit at Alex's steer, and that ordering caught a defect
that would have produced a fake result. The administrative panel is entirely in
BUSINESS days. Forum reports are overwhelmingly in CALENDAR days, months and
weeks. Comparing the two without conversion inflates the forum side by roughly
seven fifths, which is the same magnitude as the reporting offset the study is
trying to estimate.

What this builds, per forum elapsed measurement:

  * the quote, re-sliced from the frozen artifact and verified byte for byte
    after whitespace normalisation;
  * the value in its own stated unit, and separately a business-day equivalent
    with the conversion factor recorded as an explicit assumption;
  * the phase, only where the measurement's activities map to exactly one panel
    phase, otherwise an explicit reason;
  * the case period, from dates in the quote where present and otherwise bounded
    above by the post's creation time;
  * a candidate authority set with prior weights, built from LOCATING EVIDENCE
    ONLY: the utility named, any place named, and install-volume weighting.
    Never from the reported duration.

Nothing here fits a model or resolves a semantic ambiguity. Rows that cannot be
placed are retained with a reason.

    python3 -m pipeline.procbench.solar_panel.build_forum
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.procbench.burden_channels import source_family  # noqa: E402
from pipeline.procbench.compile_visit_durations import declared_kinds  # noqa: E402
from pipeline.procbench.evidence_contract import normalized_quote  # noqa: E402

LEDGER = ROOT / 'runs/rw_parse_20260918/solar_permit'
PANEL = ROOT / 'runs/solar_panel_20260920/panel_v1.csv'
OUT = ROOT / 'runs/solar_panel_20260920'

# Business days per unit. The calendar-to-business factor of five sevenths is an
# ASSUMPTION about weekends with no holiday calendar, recorded on every row it
# touches. It is the single largest correction applied here and it is the reason
# this file exists before the fit.
CALENDAR_TO_BUSINESS = 5.0 / 7.0
TO_BUSINESS_DAYS = {
    'business_days': (1.0, 'stated in the panel\'s own unit; no conversion'),
    'calendar_days': (CALENDAR_TO_BUSINESS, 'calendar to business at five sevenths, weekends only'),
    'weeks': (7.0 * CALENDAR_TO_BUSINESS, 'calendar weeks to business days at five per week'),
    'months': (365.25 / 12 * CALENDAR_TO_BUSINESS, 'calendar months to business days at five sevenths'),
    'hours': (1.0 / 24 * CALENDAR_TO_BUSINESS, 'sub-day report; converted but flagged as coarse'),
}

PHASE_ACTIVITIES = {
    'permit_review': ('ahj_permit_application_submission', 'ahj_completeness_determination',
                      'ahj_plan_review', 'ahj_permit_issuance', 'ahj_correction_resubmittal',
                      'solarapp_automated_compliance_review', 'ahj_permit_fee_payment',
                      # The source counts resubmission inside the permit metric:
                      # "Permits that require changes and resubmission are counted
                      # from the original submittal date." So a revision is part of
                      # permit review, by the panel's own definition.
                      'permit_revision'),
    'inspection': ('ahj_rough_inspection', 'ahj_final_inspection', 'ahj_reinspection',
                   'ahj_final_approval', 'inspection_scheduling_request'),
    'pre_install_ix': ('ix_application_submission', 'utility_application_validation',
                       'utility_initial_review', 'utility_preinstall_approval_to_build',
                       'utility_supplemental_review'),
    'final_ix_pto': ('final_inspection_clearance_submission', 'utility_pto_review',
                     'utility_pto_grant', 'utility_meter_exchange',
                     'utility_post_installation_inspection'),
}
ACTIVITY_PHASE = {a: p for p, ids in PHASE_ACTIVITIES.items() for a in ids}

# A row measures a panel phase only if it TRAVERSES that phase. Membership in the
# activity set is not enough: a spot check of twelve mapped rows found about a
# third were gaps between phases, or the post-inspection phase (inspect to final
# interconnection submission) recorded as if it were submission to permission to
# operate. The panel's own quartile sheet lists post-inspection as a separate
# phase, which is exactly the one being conflated. So each phase declares the
# activity that ENDS it, and the row must both contain that activity and carry a
# completion endpoint.
PHASE_TERMINAL = {
    'permit_review': ('ahj_permit_issuance', 'solarapp_automated_compliance_review'),
    'inspection': ('ahj_final_approval', 'ahj_final_inspection'),
    'pre_install_ix': ('utility_preinstall_approval_to_build',),
    'final_ix_pto': ('utility_pto_grant',),
}
COMPLETING_END = ('decision', 'activity_end')
STARTING_START = ('submission', 'complete_application', 'activity_start', 'preparation_start')

UTILITY_PATTERNS = [
    (r'\b(pg\s?&\s?e|pge|pacific gas)\b', 'Pacific Gas & Electric Co. (PG&E)'),
    (r'\b(sce|southern california edison)\b', 'Southern California Edison Co (SCE)'),
    (r'\b(sdg\s?&\s?e|sdge|san diego gas)\b', 'San Diego Gas & Electric Co (SDGE)'),
    (r'\b(smud|sacramento municipal)\b', 'Sacramento Municipal Util Dist (SMUD)'),
    (r'\b(ladwp|los angeles department of water)\b', 'Los Angeles Department of Water & Power (LADWP)'),
    (r'\b(iid|imperial irrigation)\b', 'Imperial Irrigation District (IID)'),
]
DATE_IN_QUOTE = re.compile(r'\b(20(?:1[7-9]|2[0-6]))\b')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_panel_geography():
    """Authority names, their serving utilities and install volumes, for priors."""
    by_utility = defaultdict(Counter)
    names = {}
    with PANEL.open(encoding='utf-8') as handle:
        for r in csv.DictReader(handle):
            if r['owner_kind'] != 'ahj':
                continue
            names[r['stable_owner_id']] = r['owner_name']
            volume = int(r['installs_same_cell'] or 0)
            for u in (r['serving_utilities'] or '').split(';'):
                if u:
                    by_utility[u][r['stable_owner_id']] += volume
    return names, by_utility


def post_created(doc_id):
    path = LEDGER / 'artifacts' / (doc_id + '.md')
    if not path.exists():
        return None, None
    head = path.read_text(errors='ignore')[:800]
    m = re.search(r'created_utc:\s*([0-9.]+)', head)
    if not m:
        return None, path
    return dt.datetime.fromtimestamp(float(m.group(1)), dt.timezone.utc), path


def candidate_authorities(blob, names, by_utility, top=60):
    """Prior over authorities from locating evidence only, never from duration."""
    named = [aid for aid, nm in names.items()
             if re.search(r'\b' + re.escape(re.sub(r'\s+(city|town|County)$', '', nm)) + r'\b', blob, re.I)]
    if named:
        return {a: 1.0 / len(named) for a in named}, 'explicit_place_name'
    for pattern, utility in UTILITY_PATTERNS:
        if re.search(pattern, blob, re.I):
            weights = by_utility.get(utility)
            if weights:
                total = sum(weights.values())
                if total > 0:
                    top_items = weights.most_common(top)
                    s = sum(v for _, v in top_items)
                    return {a: v / s for a, v in top_items if v > 0}, 'utility_volume_weighted:' + utility
    return {}, 'no_locating_evidence'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT / 'forum_v1.json'))
    args = ap.parse_args(argv)

    evidence = json.loads((LEDGER / 'evidence.json').read_text())
    kinds = declared_kinds(json.loads((LEDGER / 'source/document_register.json').read_text()))
    names, by_utility = load_panel_geography()

    rows, reasons, quote_fail = [], Counter(), []
    for m in evidence['measurements']:
        if m['metric'] != 'elapsed':
            continue
        family, _ = source_family(m['source_family'], 'type', kinds)
        if family != 'forum':
            continue
        record = dict(id=m['id'], doc_id=m.get('doc_id'), statistic=m.get('statistic'),
                      case_id=m.get('case_id'), unit=m.get('unit'), raw_value=m.get('value'),
                      lower=m.get('lower'), upper=m.get('upper'))

        # quote verification against the frozen artifact
        created, path = post_created(m.get('doc_id') or '')
        quote = m.get('quote') or ''
        if path and path.exists() and quote:
            body = normalized_quote(path.read_text(errors='ignore'))
            ok = normalized_quote(quote) in body
            record['quote_verified'] = bool(ok)
            if not ok:
                quote_fail.append(m['id'])
        else:
            record['quote_verified'] = None
        record['post_created_utc'] = created.isoformat() if created else None

        # value and unit conversion
        # A row with a lower bound and no upper is a case STILL IN PROGRESS
        # ("it has been three months and counting"). Dropping those removes
        # precisely the slow cases and biases any comparison toward the forum
        # looking fast. They are retained as right-censored, not discarded.
        value = m.get('value')
        right_censored = False
        if value is None and m.get('lower') is not None and m.get('upper') is not None:
            value = (m['lower'] + m['upper']) / 2.0
        elif value is None and m.get('lower') is not None and m.get('upper') is None:
            value, right_censored = m['lower'], True
        record['right_censored'] = right_censored
        # An hours-denominated report of a multi-day administrative process is
        # ambiguous: one row says "48 business hours", which is six working days,
        # not the two the calendar conversion would give. Excluded rather than
        # converted under a guess.
        if m.get('unit') == 'hours':
            factor, note = None, 'hours excluded: business hours and clock hours are not distinguishable here'
        else:
            factor, note = TO_BUSINESS_DAYS.get(m.get('unit'), (None, 'unit not convertible'))
        record['business_days'] = (value * factor) if (value is not None and factor) else None
        record['conversion_factor'] = factor
        record['conversion_note'] = note
        record['conversion_is_an_assumption'] = m.get('unit') != 'business_days'

        # phase mapping
        activities = [a.split('__')[-1] for a in (m.get('activity_ids') or [])]
        phases = {ACTIVITY_PHASE[a] for a in activities if a in ACTIVITY_PHASE}
        record['activities'] = activities
        start_marker, end_marker = m.get('start'), m.get('end')
        record['start_marker'], record['end_marker'] = start_marker, end_marker
        phase = list(phases)[0] if len(phases) == 1 else None
        if len(phases) == 0:
            record['phase'], record['phase_reason'] = None, 'no activity maps to a panel phase'
        elif len(phases) > 1:
            record['phase'] = None
            record['phase_reason'] = 'spans %d panel phases: %s' % (len(phases), sorted(phases))
        elif not (set(activities) & set(PHASE_TERMINAL[phase])):
            record['phase'] = None
            record['phase_reason'] = ('does not reach the activity that ends %s, so it measures a '
                                      'part or a gap, not the phase' % phase)
        elif end_marker not in COMPLETING_END:
            record['phase'] = None
            record['phase_reason'] = 'end marker %r is not a completion' % end_marker
        elif start_marker not in STARTING_START:
            record['phase'] = None
            record['phase_reason'] = 'start marker %r does not open the phase' % start_marker
        else:
            record['phase'], record['phase_reason'] = phase, 'complete traversal of a single phase'

        # case period, from the quote where possible, else bounded by the post
        blob = ' '.join(str(m.get(k) or '') for k in ('quote', 'interpretation', 'cohort'))
        years = sorted({int(y) for y in DATE_IN_QUOTE.findall(blob)})
        record['years_in_quote'] = years
        record['case_year'] = years[-1] if years else None
        record['case_year_source'] = 'quote' if years else ('post_upper_bound' if created else 'unknown')
        if not years and created:
            record['case_year'] = created.year
        record['in_panel_years'] = bool(record['case_year'] and 2017 <= record['case_year'] <= 2024)

        # The latent entity depends on the phase. Permit review and inspection
        # belong to an authority, which a post rarely names, so those need a
        # candidate distribution. Interconnection belongs to a UTILITY, which a
        # post usually names outright, so there is nothing latent to marginalise.
        named_utility = ''
        for pattern, utility in UTILITY_PATTERNS:
            if re.search(pattern, blob, re.I):
                named_utility = utility
                break
        record['named_utility'] = named_utility
        if record['phase'] in ('pre_install_ix', 'final_ix_pto'):
            record['entity_level'] = 'utility'
            if named_utility:
                candidates, basis = {named_utility: 1.0}, 'utility_named_exactly'
            else:
                candidates, basis = {}, 'no_utility_named_for_a_utility_phase'
        else:
            record['entity_level'] = 'authority'
            candidates, basis = candidate_authorities(blob, names, by_utility)
        record['candidate_count'] = len(candidates)
        record['candidate_basis'] = basis
        record['effective_candidates'] = (round(1.0 / sum(w * w for w in candidates.values()), 1)
                                          if candidates else None)
        record['candidates'] = dict(sorted(candidates.items(), key=lambda kv: -kv[1])[:60])

        record['censoring_note'] = ('lower bound only; the case had not finished when the post was '
                                    'written' if right_censored else '')
        usable = (record['phase'] is not None and record['business_days'] is not None
                  and record['statistic'] == 'individual' and bool(candidates)
                  and record['quote_verified'] is not False)
        record['usable_for_offset'] = bool(usable)
        if not usable:
            why = []
            if record['phase'] is None:
                why.append('phase_unmapped')
            if record['business_days'] is None:
                why.append('no_convertible_value')
            if record['statistic'] != 'individual':
                why.append('statistic:' + str(record['statistic']))
            if not candidates:
                why.append('no_locating_evidence')
            if record['quote_verified'] is False:
                why.append('quote_mismatch')
            record['unusable_reasons'] = why
            reasons[','.join(why)] += 1
        rows.append(record)

    usable = [r for r in rows if r['usable_for_offset']]
    report = dict(
        schema_version='solar-forum-prep/1', stage='C-preparation',
        plan='docs/2026-09-20-solar-leg-plan-for-claude.md',
        estimands='runs/solar_panel_20260920/estimands_frozen_v2.json',
        ledger=dict(path=str((LEDGER / 'evidence.json').relative_to(ROOT)),
                    sha256=sha(LEDGER / 'evidence.json')),
        unit_defect=dict(
            found='The panel is in business days; forum reports are overwhelmingly calendar days, '
                  'months and weeks.',
            forum_units=dict(Counter(r['unit'] for r in rows)),
            correction='five sevenths, weekends only, no holiday calendar',
            magnitude='about 1.4x, the same order as the reporting offset being estimated',
            status='an explicit assumption recorded on every converted row, not a fact'),
        totals=dict(forum_elapsed_rows=len(rows),
                    quote_verified=sum(1 for r in rows if r['quote_verified']),
                    quote_mismatch=len(quote_fail),
                    phase_mapped=sum(1 for r in rows if r['phase']),
                    individual=sum(1 for r in rows if r['statistic'] == 'individual'),
                    with_locating_evidence=sum(1 for r in rows if r['candidate_count']),
                    usable_for_offset=len(usable)),
        usable_by_phase=dict(Counter(r['phase'] for r in usable)),
        right_censored_usable=sum(1 for r in usable if r.get('right_censored')),
        usable_by_entity_level=dict(Counter(r.get('entity_level') for r in usable)),
        exact_utility_matches=sum(1 for r in usable if r['candidate_basis'] == 'utility_named_exactly'),
        latent_authority_rows=sum(1 for r in usable if r.get('entity_level') == 'authority'),
        in_panel_years_usable=sum(1 for r in usable if r['in_panel_years']),
        usable_by_candidate_basis=dict(Counter(r['candidate_basis'].split(':')[0] for r in usable)),
        usable_by_case_year=dict(sorted(Counter(r['case_year'] for r in usable).items(),
                                        key=lambda kv: (kv[0] is None, kv[0]))),
        case_year_source=dict(Counter(r['case_year_source'] for r in usable)),
        effective_candidate_counts=dict(
            median=(sorted(r['effective_candidates'] for r in usable)[len(usable) // 2]
                    if usable else None),
            note='Effective number of candidate authorities under the volume-weighted prior. A '
                 'small number means a case informs a specific authority; a large one means it '
                 'informs the statewide and utility levels instead.'),
        unusable_reason_counts=dict(reasons),
        declarations=dict(reads_benchmark_truth=False, network_used=False, model_calls=0,
                          prior_uses_duration=False),
        rows=rows)
    pathlib.Path(args.out).write_text(json.dumps(report, indent=1))
    t = report['totals']
    print('forum elapsed rows %d | quotes verified %d, mismatched %d' %
          (t['forum_elapsed_rows'], t['quote_verified'], t['quote_mismatch']))
    print('phase-mapped %d | individual %d | with locating evidence %d | USABLE %d'
          % (t['phase_mapped'], t['individual'], t['with_locating_evidence'], t['usable_for_offset']))
    print('usable by phase:', report['usable_by_phase'])
    print('usable by case year:', report['usable_by_case_year'])
    print('candidate basis:', report['usable_by_candidate_basis'],
          '| median effective candidates', report['effective_candidate_counts']['median'])
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
