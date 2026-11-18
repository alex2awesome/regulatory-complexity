"""Non-duration burden claims: fees, counts and applicant/agency effort.

The semantic audit exists because a *duration* is ambiguous: a stated number of
days may be one visit, a sum of cycles or a first-to-last span, and choosing
between those readings is a judgment that must be quoted and reviewed. A stated
dollar amount is not ambiguous in that way, and neither is an applicant's count
of the trips they made. This module holds the declarative part of compiling
those claims: which document is which kind of source, which model basis a claim
can reach, and every unit or rounding convention the compiler applies, each one
returned as data so it lands in the compilation rather than in a comment here.

Nothing in this module reads benchmark truth, generator specifications, scores
or fitted outputs, and nothing here interprets a quotation. A claim that cannot
be modelled returns an explicit reason; it is never rounded into a convenient
one. All of these are declared modelling conventions, not measurements.
"""
from __future__ import annotations

import math
import re


# The money basis is a path functional (`compact_visit_trace.MONEY_BASES`): a
# published fee adds no sampled coordinate, so it is not a resource channel.
# Contract: individual (per-case) reports only, never mixed with duration or
# count operators in one observation, and amounts are USD.
MONEY_BASIS = 'payer_fee_total'
# `bayes_trace_hierarchy.COUNT_BASES` also contains `additional_rounds`, which
# needs a route repeat key that no source claim supplies, so the source compiler
# cannot reach it. `tests/test_burden_channels_compile.py` pins the agreement.
COUNT_BASES = ('visit_count', 'operation_count', 'agency_count')
EFFORT_BASES = {'payer_work': 'payer_hours', 'agency_work': 'agency_hours'}
BURDEN_CHANNELS = ('fee', 'count', 'effort')

# A count claim names what it counted; only these three kinds of countable thing
# exist in the trace. `total_attempts` mixes first attempts with repeats,
# `additional_correction_rounds` needs a repeat key, and `procedural_steps_unknown`
# is by construction not an identified countable thing.
COUNT_QUANTITY_BASES = {'encounters_or_visits': 'visit_count',
                        'distinct_operations': 'operation_count',
                        'distinct_public_organizations': 'agency_count'}
UNMAPPED_COUNT_QUANTITIES = {
    'additional_correction_rounds': 'additional_rounds_requires_a_route_repeat_key',
    'total_attempts': 'total_attempts_is_not_a_modeled_count_basis',
    'procedural_steps_unknown': 'unidentified_procedural_steps_are_not_a_countable_thing'}
# A count over the operations a case traversed needs to know which operations
# those are: either an explicit activity linkage or a whole-case scope.
WHOLE_CASE_COUNT_SCOPES = {'through_initial_decision', 'through_last_decision',
                           'through_explicit_closeout', 'whole_process_unspecified'}

# Effort units. A person does not work 168 hours in a week, so for an effort
# metric a 'week' is a work week and a 'business day' is a work day. The factor
# is declared here and recorded in every observation that uses it; it is a
# convention, not something measured from the corpus.
WORK_DAY_HOURS = 8.
WORK_WEEK_HOURS = 5 * WORK_DAY_HOURS
EFFORT_UNIT_HOURS = {'minutes': 1 / 60, 'hours': 1., 'business_days': WORK_DAY_HOURS,
                     'work_days': WORK_DAY_HOURS, 'weeks': WORK_WEEK_HOURS,
                     'work_weeks': WORK_WEEK_HOURS}
EFFORT_UNIT_ASSUMPTION = (
    'Effort units: a work day is %g hours and a work week is five work days (%g hours). '
    'On an effort claim "weeks"/"business days" are read as work weeks/work days, never as '
    '168 or 24 hours per unit. Declared convention, not a measured working pattern.'
    % (WORK_DAY_HOURS, WORK_WEEK_HOURS))
MONEY_REPORT_NOTE = (
    'A money observation is scored by a relative-error report model with no source offset, so a '
    'fee contributes nothing to the agency-versus-applicant source-family contrast; only duration '
    'reports do. Fee coverage is not source-bias coverage.')
ROUNDING_RULE = 'half_of_lowest_written_decimal_place'
ROUNDING_ASSUMPTION = (
    'Rounding (%s): a reported fee or effort amount with no stated bounds is read as a round '
    'number, so its interval is the amount plus or minus half of the lowest nonzero decimal '
    'place actually written. $190 becomes [185, 195]; $194 becomes [193.5, 194.5].' % ROUNDING_RULE)

# Declared source taxonomy. Type grouping is opt-in; document grouping retains
# the original source families. Recognizing a type is not a claim that its bias
# is identified: that requires reviewed, comparable evidence and replication.
SOURCE_FAMILY_TYPES = {
    'agency_official': ('ordinance', 'statute_text', 'statute', 'regulation', 'program_page',
                        'faq', 'form', 'checklist', 'fee_schedule', 'sop',
                        'generic_permits_page', 'departments_index', 'local_ordinance',
                        'program_overview', 'initial_application_guide', 'renewal_guide',
                        'interview_and_pickup_guide', 'application_guide',
                        'expedited_service_guide', 'interview_guide',
                        'verification_checklist', 'issuance_guide', 'typical_time_faq'),
    'agency_dashboard': ('official_stats', 'dataset', 'monthly_performance_table',
                         'receipt_cohort_workbook', 'completion_cohort_dashboard'),
    'news': ('news', 'council_minutes', 'staff_report'),
    'forum': ('reddit', 'reddit_thread', 'forum_thread', 'forum_post', 'applicant_forum'),
    'third_party': ('third_party_guide',),
    # Oversight bodies are neither the agency describing itself nor a reporter
    # nor a vendor, and their bias is different from all three: an audit or a
    # grand-jury report exists because someone suspected a problem.
    'oversight': ('audit', 'grand_jury', 'consultant_study', 'oversight'),
}
# Real document ids do not carry the synthetic corpus's `<program>__<kind>` shape;
# they look like `cslb_weeks_to_process_table`, `ccr827`, `reddit_1lwvryd`. Keying
# the taxonomy on that shape alone left every real source unclassified, so the
# grouping pooled nothing exactly where pooling was the point. A declared kind
# from the corpus's own document register is consulted first, and these prefixes
# catch the one family whose ids are systematically self-identifying.
SOURCE_FAMILY_PREFIXES = (('reddit_', 'forum'), ('forum_', 'forum'))
SOURCE_FAMILY_GROUPINGS = ('document', 'type')


def document_type(document_id, kinds=None):
    """Declared type of a document id, or None when the taxonomy does not cover it.

    `kinds` optionally maps document ids to a kind declared by the corpus itself
    (the real corpus records one per source: statute, program_page, official_stats,
    reddit and so on). A declared kind is authoritative and is consulted first,
    because reading a type off an id only works where ids were built to carry one.

    An uncovered document is not guessed into the nearest type: the caller keeps
    the document as its own family and reports the id, because inventing a
    source type would invent the pooled bias the grouping is meant to measure.
    """
    document_id = str(document_id)
    if kinds is not None and document_id in kinds:
        declared = kinds[document_id]
        if not isinstance(declared, str) or not declared.strip():
            return None
        declared = declared.strip().lower()
        for family, kind_names in SOURCE_FAMILY_TYPES.items():
            if declared == family or declared in kind_names:
                return family
        # A present but uncovered declaration is not permission to replace it
        # with a filename guess. Preserve that unresolved type for review.
        return None
    for prefix, family in SOURCE_FAMILY_PREFIXES:
        if document_id.startswith(prefix):
            return family
    suffix = document_id.rsplit('__', 1)[-1]
    stem = re.sub(r'_\d+$', '', suffix)
    for family, suffixes in SOURCE_FAMILY_TYPES.items():
        if suffix in suffixes or stem in suffixes:
            return family
    return None


def source_family(name, grouping='document', kinds=None):
    """Return (emitted family, declared type or None) under the chosen grouping."""
    if grouping not in SOURCE_FAMILY_GROUPINGS:
        raise ValueError('Unknown source-family grouping: ' + str(grouping))
    if grouping == 'document':
        return name, None
    kind = document_type(name, kinds)
    return (kind if kind is not None else name), kind


def written_precision(value):
    """The lowest nonzero decimal place actually written in a reported amount."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('A reported amount must be finite')
    if value != int(value):
        decimals = len(repr(value).split('.')[1].rstrip('0')) or 1
        return 10. ** -decimals
    amount, step = abs(int(value)), 1
    while amount and amount % (step * 10) == 0:
        step *= 10
    return float(step)


def report_amount_interval(measurement):
    """Reported amount as an interval in its own unit; never a zero-width point.

    A point report is a rounded report, so it becomes its rounding interval. The
    model rejects a zero-width continuous observation for exactly this reason.
    """
    lower, upper, value = measurement['lower'], measurement['upper'], measurement['value']
    if lower is None and upper is None:
        if value is None:
            return None, ['claim_without_numeric_amount']
        half = .5 * written_precision(value)
        return (max(0., float(value) - half), float(value) + half), []
    low = 0. if lower is None else float(lower)
    high = None if upper is None else float(upper)
    if high is not None and high <= low:
        return None, ['zero_width_reported_interval']
    return (low, high), []


def _temporal_reasons(context):
    scope = (context or {}).get('temporal_scope')
    return ['not_current_empirical_claim:' + scope] if scope in {'historical', 'hypothetical'} else []


def fee_compilation(measurement, context=None):
    """Classify one `fee` claim into an individual money observation or not.

    A fee attached to a case is that applicant's reported total and is an
    observation. A published schedule amount with no case is an *input* to the
    route, not an observation of it, and is handed to the structural bridge.
    """
    interval, reasons = report_amount_interval(measurement)
    reasons = list(reasons) + _temporal_reasons(context)
    if interval is None:
        return dict(kind='unmodeled', reasons=reasons)
    if measurement['case_id'] is None:
        route_reason = 'published_fee_amount_without_case_is_a_route_input'
        if reasons:
            return dict(kind='unmodeled', reasons=reasons + [route_reason])
        return dict(kind='route_input', reasons=[route_reason], route_input=dict(
            measurement_id=measurement['id'], activity_ids=list(measurement['activity_ids']),
            scope=measurement['scope'], statistic=measurement['statistic'],
            amount_usd=measurement['value'], lower_usd=measurement['lower'],
            upper_usd=measurement['upper'], doc_id=measurement['doc_id'],
            quote=measurement['quote'], consumer='structural route bridge: published fee per operation'))
    if measurement['statistic'] != 'individual':
        reasons.append('fee_statistic_is_not_an_individual_paid_total:' + measurement['statistic'])

    # WHAT THE CLAIM IS ABOUT DECIDES ITS FORM, and getting this wrong is
    # dangerous rather than merely lossy. An earlier version compiled EVERY
    # case-linked fee as a whole-path total, which meant a "$25,000 total
    # overhead" figure and a monthly commissary rent would have been fitted as
    # this permit route's cost and would have driven a round-count posterior
    # hard and wrongly. The contract already records what a claim covers, so use
    # it rather than assuming every reported amount is a process total.
    scope = measurement['scope']
    if scope == 'standing':
        # A recurring obligation is not the cost of obtaining the permit. Rent,
        # an annual franchise tax and a periodic tag renewal are real burdens
        # and belong in the ledger, but they are not a path total and adding
        # them to one would inflate it without bound as a case ages.
        reasons.append('standing_recurring_amount_is_not_a_process_path_total')
    elif scope not in ('process', 'step', 'segment'):
        reasons.append('fee_scope_does_not_identify_what_the_amount_covers:' + str(scope))
    if reasons:
        return dict(kind='unmodeled', reasons=reasons)

    if scope == 'process':
        # Whole-route form, with no activity linkage. The sum is over the
        # operations the case actually traversed, which is what makes cost
        # path-dependent: a case that stops at the first gate never pays for the
        # inspection. Naming operations here would refuse (-inf), not discount,
        # every path omitting one of them, and path membership is a route
        # question a process-level total does not settle.
        return dict(kind='observation', reasons=[], interval=interval,
                    operator=dict(basis=MONEY_BASIS, activity_ids=[]),
                    units=dict(unit='USD', hours_per_unit=None, rounding=ROUNDING_RULE),
                    provenance=dict(fee_scope=dict(
                        operator='whole_case_path_total', ledger_scope=scope,
                        ledger_activity_ids=list(measurement['activity_ids']),
                        note=('A process-scoped reported total is compiled over the whole '
                              'traversed path; path membership is not settled by the source.'))))

    # Step- or segment-scoped: the applicant paid for THESE steps, which is also
    # evidence their case traversed them. Naming them is therefore right, and a
    # path omitting one being refused is the correct reading rather than a bug.
    activity_ids = [a for a in measurement['activity_ids'] if a]
    if not activity_ids:
        return dict(kind='unmodeled',
                    reasons=['step_scoped_fee_names_no_activity_to_attach_to'])
    return dict(kind='observation', reasons=[], interval=interval,
                operator=dict(basis=MONEY_BASIS, activity_ids=list(activity_ids)),
                units=dict(unit='USD', hours_per_unit=None, rounding=ROUNDING_RULE),
                provenance=dict(fee_scope=dict(
                    operator='named_step_total', ledger_scope=scope,
                    ledger_activity_ids=list(activity_ids),
                    note=('A step-scoped payment is attached to the steps it names. Paying for a '
                          'step is evidence the case traversed it, so a route omitting that step '
                          'is refused rather than credited with a smaller total.'))))


def effort_compilation(measurement, context=None):
    """Classify one `payer_work`/`agency_work` claim into an hours observation.

    The unit vocabulary is wider than `hours` on purpose: 'a few weeks of my
    time' is an effort claim, and dropping it for want of a work-week unit
    discards the second-priority burden quantity on a technicality.
    """
    basis = EFFORT_BASES[measurement['metric']]
    factor = EFFORT_UNIT_HOURS.get(measurement['unit'])
    interval, reasons = report_amount_interval(measurement)
    reasons = list(reasons) + _temporal_reasons(context)
    if factor is None:
        reasons.append('unmodeled_effort_unit:' + measurement['unit'])
    if measurement['case_id'] is None:
        reasons.append('population_effort_statistic_not_implemented:' + measurement['statistic'])
    elif measurement['statistic'] != 'individual':
        reasons.append('effort_statistic_is_not_an_individual_report:' + measurement['statistic'])
    if reasons or interval is None:
        return dict(kind='unmodeled', reasons=reasons)
    hours = (interval[0] * factor, None if interval[1] is None else interval[1] * factor)
    return dict(kind='observation', reasons=[], interval=hours,
                operator=dict(basis=basis, activity_ids=list(measurement['activity_ids'])),
                units=dict(unit=measurement['unit'], hours_per_unit=factor,
                           assumption=EFFORT_UNIT_ASSUMPTION, rounding=ROUNDING_RULE,
                           reported_interval=list(interval)))


def _countable(value):
    """Counts are discrete; an integral amount stays an integer in the output."""
    return int(value) if float(value) == int(value) else float(value)


def count_compilation(claim):
    """Classify one burden-count claim into an individual count observation.

    Only a count that resolves to a specific countable thing on the route can be
    one: a rule, a forecast, a population summary or an unidentified 'step' is
    retained with its reason instead.
    """
    reasons = []
    basis = COUNT_QUANTITY_BASES.get(claim['quantity'])
    if basis is None:
        reasons.append(UNMAPPED_COUNT_QUANTITIES.get(
            claim['quantity'], 'unmodeled_count_quantity:' + claim['quantity']))
    if claim['duplicate_of'] is not None:
        reasons.append('duplicate_of_another_count_claim')
    if claim['case_id'] is None:
        reasons.append('population_or_rule_count_is_not_an_individual_report')
    elif claim['statistic'] not in {'individual', 'exact'}:
        reasons.append('count_statistic_is_not_an_individual_total:' + claim['statistic'])
    if claim['basis'] != 'observed_case':
        reasons.append('count_basis_is_not_an_observed_case:' + claim['basis'])
    if claim['temporal_scope'] != 'current':
        reasons.append('not_current_count_claim:' + claim['temporal_scope'])
    if not claim['activity_ids'] and claim['scope'] not in WHOLE_CASE_COUNT_SCOPES:
        reasons.append('unresolved_count_activity_linkage')
    value, lower, upper = claim['value'], claim['lower'], claim['upper']
    if value is not None and lower is None and upper is None:
        interval = (_countable(value), _countable(value))
    else:
        interval = (0 if lower is None else _countable(lower),
                    None if upper is None else _countable(upper))
        if interval[1] is not None and interval[1] < interval[0]:
            reasons.append('reversed_reported_count_interval')
    if reasons:
        return dict(kind='unmodeled', reasons=sorted(set(reasons)))
    return dict(kind='observation', reasons=[], interval=interval,
                operator=dict(basis=basis, activity_ids=list(claim['activity_ids'])),
                units=dict(unit=claim['counting_unit'], discrete=True))


def ineligible_reasons(measurement, context, channels):
    """Why a ledger claim reached no likelihood, more specific than one bucket.

    Kept identical to the historical single reason when no burden channel is
    enabled, so existing compilations reproduce byte for byte.
    """
    if not channels:
        return ['non_elapsed_or_not_current_empirical_timing']
    reasons = []
    if measurement['metric'] != 'elapsed':
        reasons.append('metric_outside_compiled_channels:' + measurement['metric'])
    if measurement['scope'] == 'standing':
        reasons.append('standing_scope_is_not_a_case_measurement')
    if measurement['statistic'] in {'statutory_cap', 'target'}:
        reasons.append('normative_statistic_is_not_an_observation:' + measurement['statistic'])
    if all(measurement[k] is None for k in ('value', 'lower', 'upper')):
        reasons.append('claim_without_numeric_amount')
    reasons += _temporal_reasons(context)
    return sorted(set(reasons)) or ['non_elapsed_or_not_current_empirical_timing']
