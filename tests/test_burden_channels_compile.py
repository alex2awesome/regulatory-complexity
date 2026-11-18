"""Fees, counts and effort reach the likelihood, and nothing is dropped doing it.

One line kept most of the ledger away from the model: the compiler scoped itself
to `metric == 'elapsed'` and marked everything else outside its boundary. These
tests pin what replaces that. A fee attached to a case is an individual money
report; a published schedule amount is an input to the route and must not be
mistaken for an observation of it; a count that does not resolve to a countable
thing keeps its reason; and every claim still ends with exactly one disposition.

They also pin the two things most easily lost in a refactor: the conversion
factors are declared data in the output rather than a constant buried in code,
and the default compilation is unchanged, so every saved compilation still
reproduces. No network, no paid calls, no truth, no saved run is read.
"""
import copy

import numpy as np
import pytest

from pipeline.procbench.audit_burden_counts import VERSION as COUNT_VERSION, validate_counts
from pipeline.procbench.audit_visit_observations import VERSION as VISIT_VERSION
from pipeline.procbench.bayes_trace_hierarchy import COUNT_BASES as MODEL_COUNT_BASES
from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compact_visit_trace import MONEY_BASES
from pipeline.procbench import burden_channels as bc
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.evidence_contract import validate
from test_bayes_hierarchy import fixture, measurement
from test_process_measurement import audit_row


DOCUMENT = 'document'
QUOTE = 'Evidence'


def claim(ident, metric, unit, **kwargs):
    """A ledger measurement in any metric, not only the elapsed one."""
    row = measurement(ident=ident)
    row.update(metric=metric, unit=unit, scope='process', activity_ids=[],
               start='unspecified', end='unspecified', case_id=None, value=None)
    row.update(kwargs)
    return row


def ledger():
    """A synthetic ledger mixing every metric the evidence contract allows."""
    e = fixture()
    e['measurements'] = [
        measurement(),                                                      # elapsed, case c1
        claim('fee_case', 'fee', 'USD', value=190., case_id='c1', statistic='individual'),
        claim('fee_published', 'fee', 'USD', value=175., statistic='individual'),
        claim('payer', 'payer_work', 'hours', value=6., case_id='c1', statistic='individual'),
        claim('agency', 'agency_work', 'hours', value=1., statistic='estimate'),
        claim('staff', 'staffing_fte', 'fte', value=2., statistic='estimate'),
        claim('volume', 'annual_volume', 'cases_per_year', value=150., statistic='estimate'),
    ]
    operator = dict(basis='single_visit_cycle', activity_ids=['review'], start='single_visit_start',
                    end='single_visit_end', visits='first', censoring='none', notes='')
    visit = dict(schema_version=VISIT_VERSION, program_id=e['program_id'], measurements=[dict(
        measurement_id='m1', identification='explicit', activity_mapping='supported',
        operators=[operator], evidence=[dict(doc_id=DOCUMENT, quote=QUOTE)], notes='')], unresolved=[])
    semantic = dict(program_id=e['program_id'], measurements=[audit_row()], unresolved=[])
    documents = [dict(id=DOCUMENT, text=QUOTE)]
    policy = dict(case_sampling={'c1': 'unselected'})
    return e, visit, semantic, documents, policy


def count_audit(program_id, **kwargs):
    row = dict(id='bc1', case_id='c1', activity_ids=['review'], actor_ids=[], scope='activity_only',
               temporal_scope='current', population='One reported case.', source_family=DOCUMENT,
               duplicate_of=None, evidence=[dict(doc_id=DOCUMENT, quote=QUOTE)], notes='',
               quantity='encounters_or_visits', counting_unit='counter visits', basis='observed_case',
               statistic='individual', value=2, lower=None, upper=None, inventory_coverage='not_inventory')
    row.update(kwargs)
    return dict(schema_version=COUNT_VERSION, program_id=program_id,
                count_claims=[row], rate_claims=[], unresolved=[])


def compiled(channels=('fee', 'effort'), grouping='document', counts=None, **kwargs):
    e, v, s, d, p = ledger()
    for key, value in kwargs.items():
        e['measurements'] = [dict(m, **value) if m['id'] == key else m for m in e['measurements']]
    validate(e, d)
    audit = None if counts is None else count_audit(e['program_id'], **counts)
    if audit is not None:
        channels = tuple(channels) + ('count',)
    return compile_durations(e, v, s, d, p, count_audit=audit, burden_channels=channels,
                             source_family_grouping=grouping), e


def observations(report, channel):
    return [o for o in report['observations'] if o['provenance'].get('channel') == channel]


def disposition(report, mid):
    return next(r for r in report['dispositions'] if r['measurement_id'] == mid)


# --------------------------------------------------------------------- money
def test_fee_with_a_case_becomes_an_individual_money_observation():
    report, _ = compiled()
    fees = observations(report, 'fee')
    assert [o['id'] for o in fees] == ['fee_case']
    assert fees[0]['operators'] == [dict(basis=bc.MONEY_BASIS, activity_ids=[])]
    assert fees[0]['case_id'] == 'c1' and fees[0]['statistic'] == 'individual'
    # "$190" is a round report, so it arrives as its rounding interval: the model
    # rejects a zero-width continuous observation, money included.
    assert (fees[0]['lower'], fees[0]['upper']) == (185., 195.)
    assert fees[0]['provenance']['units'] == dict(unit='USD', hours_per_unit=None,
                                                  rounding=bc.ROUNDING_RULE)
    assert disposition(report, 'fee_case')['status'] == 'compiled'


def test_fee_with_no_case_is_a_route_input_and_never_an_observation():
    report, _ = compiled()
    assert 'fee_published' not in {o['id'] for o in report['observations']}
    row = disposition(report, 'fee_published')
    assert row['status'] == 'route_input_not_observation'
    assert row['reasons'] == ['published_fee_amount_without_case_is_a_route_input']
    # The amount is preserved for the structural bridge rather than discarded.
    assert row['route_input']['amount_usd'] == 175.
    assert row['route_input']['measurement_id'] == 'fee_published'
    assert report['coverage']['burden']['fee'] == dict(
        claims=2, observations=1, route_inputs=1, retained_with_disposition=0,
        reasons={'published_fee_amount_without_case_is_a_route_input': 1})


def test_a_step_scoped_fee_attaches_to_its_step_not_to_the_whole_path():
    """Supersedes an earlier expectation, and the real corpus is why.

    This once compiled every case-linked fee as a whole-path total, on the
    argument that naming operations refuses a path rather than discounting it.
    That argument is right for a PROCESS-scoped total and wrong for a
    step-scoped payment, and the food-facility ledger showed what the error
    costs: its ten case-linked amounts are commissary rents, an LLC franchise
    tax and a "$25,000 total overhead" figure, none of them a permit total, and
    all of them would have been fitted as this route's cost and would have
    driven a round-count posterior hard and wrongly.

    Paying for a step is evidence the case traversed it, so naming the step is
    the correct reading and a route omitting it is properly refused.
    """
    report, _ = compiled(fee_case=dict(scope='step', activity_ids=['review']))
    fee = observations(report, 'fee')[0]
    assert fee['operators'] == [dict(basis=bc.MONEY_BASIS, activity_ids=['review'])]
    scope = fee['provenance']['fee_scope']
    assert scope['operator'] == 'named_step_total'
    assert scope['ledger_activity_ids'] == ['review'] and scope['ledger_scope'] == 'step'
    assert bc.MONEY_REPORT_NOTE in report['coverage']['burden']['notes']


def test_money_observation_is_accepted_by_the_joint_model():
    report, e = compiled()
    fee = observations(report, 'fee')[0]
    program = dict(id=e['program_id'], observations=[fee], routes=[dict(
        id='r', prior_weight=1., operations=[dict(id='review', actor_id='A', actor_role='agency',
        task_type='technical_review', markers=['decision'], fee=190.)],
        blocks=[dict(id='b', operations=['review'])])])
    model = VisitHierarchy(dict(programs=[program]), Config(population_size=16))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [0]))


# --------------------------------------------------------------------- counts
def test_resolved_count_reaches_the_count_likelihood():
    report, _ = compiled(counts={})
    counts = observations(report, 'count')
    assert [o['id'] for o in counts] == ['bc1']
    assert counts[0]['operators'] == [dict(basis='visit_count', activity_ids=['review'])]
    assert (counts[0]['lower'], counts[0]['upper']) == (2, 2)
    assert report['coverage']['burden']['count']['observations'] == 1


def test_quote_declared_count_only_case_compiles_and_reaches_v6():
    e, v, s, d, p = ledger()
    e['measurements'] = []
    v['measurements'] = []
    s['measurements'] = []
    audit = count_audit(e['program_id'])
    audit.update(schema_version='burden-count-evidence/2', cases=[dict(
        case_id='c1', description='Explicitly declared count-only applicant', notes='',
        evidence=[dict(doc_id=DOCUMENT, quote=QUOTE)])])
    report = compile_durations(e, v, s, d, p, count_audit=audit, burden_channels=('count',))
    rows = observations(report, 'count')
    assert len(rows) == 1 and rows[0]['case_id'] == 'c1'
    assert e['measurements'] == []
    program = dict(id=e['program_id'], observations=rows, routes=[dict(
        id='r', prior_weight=1., operations=[dict(id='review', actor_id='A', actor_role='agency',
        task_type='technical_review', markers=['decision'])], blocks=[dict(id='b', operations=['review'])])])
    model = VisitHierarchy(dict(programs=[program]), Config(population_size=16))
    assert model.programs[0]['cases'] == ['c1']
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [0]))


@pytest.mark.parametrize('override,reason', [
    (dict(quantity='procedural_steps_unknown'),
     'unidentified_procedural_steps_are_not_a_countable_thing'),
    (dict(quantity='additional_correction_rounds'), 'additional_rounds_requires_a_route_repeat_key'),
    (dict(activity_ids=[]), 'unresolved_count_activity_linkage'),
    (dict(case_id=None), 'population_or_rule_count_is_not_an_individual_report'),
    (dict(basis='normative_rule'), 'count_basis_is_not_an_observed_case:normative_rule'),
    (dict(temporal_scope='hypothetical'), 'not_current_count_claim:hypothetical')])
def test_unresolved_count_keeps_a_disposition_with_its_reason(override, reason):
    report, _ = compiled(counts=override)
    assert not observations(report, 'count')
    row = report['count_dispositions'][0]
    assert row['count_claim_id'] == 'bc1' and row['status'] == 'retained_without_count_likelihood'
    assert reason in row['reasons']
    # The claim is retained whole, not reduced to its rejection.
    assert row['source']['evidence'] == [dict(doc_id=DOCUMENT, quote=QUOTE)]


def test_count_channel_requires_its_separate_audit():
    e, v, s, d, p = ledger()
    with pytest.raises(ValueError, match='burden-count audit'):
        compile_durations(e, v, s, d, p, burden_channels=('count',))


# --------------------------------------------------------------------- effort
def test_effort_hours_compile_with_the_declared_conversion_visible():
    report, _ = compiled()
    effort = observations(report, 'effort')
    assert [o['id'] for o in effort] == ['payer']
    assert effort[0]['operators'] == [dict(basis='payer_hours', activity_ids=[])]
    assert effort[0]['provenance']['units']['hours_per_unit'] == 1.
    assert bc.EFFORT_UNIT_ASSUMPTION in report['assumptions']
    # The agency-side estimate is a population claim, not an individual report.
    assert disposition(report, 'agency')['reasons'] == [
        'population_effort_statistic_not_implemented:estimate']


def test_work_week_effort_uses_the_declared_forty_hour_factor():
    assert bc.WORK_DAY_HOURS == 8. and bc.WORK_WEEK_HOURS == 40.
    weeks = claim('weeks', 'payer_work', 'work_weeks', value=3., case_id='c1', statistic='individual')
    row = bc.effort_compilation(weeks)
    assert row['kind'] == 'observation'
    # Three weeks, rounded to the week, is 2.5 to 3.5 work weeks of 40 hours.
    assert row['interval'] == (100., 140.)
    assert row['units']['hours_per_unit'] == 40. and row['units']['unit'] == 'work_weeks'
    assert row['units']['reported_interval'] == [2.5, 3.5]
    assert '40 hours' in row['units']['assumption']
    assert bc.effort_compilation(
        claim('days', 'agency_work', 'work_days', value=2., case_id='c1',
              statistic='individual'))['units']['hours_per_unit'] == 8.


def test_work_week_effort_is_blocked_by_the_ledger_unit_enum_not_by_the_compiler():
    """The remaining half of 'a few weeks of my time' is the contract, not here.

    `evidence_contract` still admits only `hours` for an effort metric, so a
    work-week claim cannot be carried by a ledger even though the compiler now
    converts one. Recorded as a test so the gap is visible rather than assumed
    closed; widening the enum belongs to whoever owns that contract.
    """
    e, _, _, d, _ = ledger()
    original = list(e['measurements'])
    # A work-week unit is not in the schema enum at all ...
    e['measurements'] = original + [claim('w', 'payer_work', 'work_weeks', value=3., case_id='c1')]
    with pytest.raises(ValueError, match="'work_weeks' is not one of"):
        validate(e, d)
    # ... and the unit the enum does carry is refused for an effort metric.
    e['measurements'] = original + [claim('w', 'payer_work', 'weeks', value=3., case_id='c1')]
    with pytest.raises(ValueError, match='incompatible metric/unit'):
        validate(e, d)
    assert {'work_weeks', 'weeks'} <= set(bc.EFFORT_UNIT_HOURS)


def test_effort_without_a_magnitude_is_retained_with_its_reason():
    report, _ = compiled(payer=dict(value=None, qualitative=True))
    assert not observations(report, 'effort')
    assert disposition(report, 'payer')['reasons'] == ['claim_without_numeric_amount']


# ------------------------------------------------------------- source families
def test_source_family_grouping_changes_families_only_when_requested():
    default, _ = compiled()
    grouped, _ = compiled(grouping='type')
    assert {o['source_family'] for o in default['observations']} == {DOCUMENT}
    assert 'burden' not in default['coverage'] or default['coverage']['burden'][
        'source_family_grouping'] == 'document'
    assert grouped['coverage']['burden']['source_family_grouping'] == 'type'
    # 'document' is outside the declared taxonomy, so it keeps its own family
    # instead of being guessed into the nearest type.
    assert {o['source_family'] for o in grouped['observations']} == {DOCUMENT}
    assert grouped['coverage']['burden']['unclassified_document_ids'] == [DOCUMENT]


@pytest.mark.parametrize('document,expected', [
    ('C29__S12__ordinance', 'agency_official'), ('C29__fee_schedule', 'agency_official'),
    ('S12__statute_text', 'agency_official'), ('C38__S03__official_stats', 'agency_dashboard'),
    ('C29__S12__council_minutes', 'news'), ('C44__S03__staff_report', 'news'),
    ('C29__S12__reddit_2', 'forum'), ('C58__S03__reddit_101', 'forum'),
    ('C44__S12__forum_thread', 'forum'), ('C41__S12__third_party_guide', 'third_party'),
    ('S12__bill_analysis', None)])
def test_declared_taxonomy_maps_the_document_id_suffix(document, expected):
    assert bc.document_type(document) == expected
    assert bc.source_family(document, 'type') == (expected or document, expected)
    assert bc.source_family(document) == (document, None)


def test_grouping_pools_the_forum_and_agency_sides_into_one_family_each():
    families = {bc.source_family(d, 'type')[0] for d in
                ('C29__S12__reddit_1', 'C29__S12__reddit_2', 'C29__S12__reddit_3')}
    assert families == {'forum'}
    assert bc.source_family('C29__S12__faq', 'type')[0] == bc.source_family(
        'C29__S12__program_page', 'type')[0] == 'agency_official'


# ------------------------------------------------------------------ accounting
def test_every_claim_of_every_metric_is_accounted_exactly_once():
    report, e = compiled(counts={})
    ledger_ids = {m['id'] for m in e['measurements']}
    assert len(report['dispositions']) == len(e['measurements'])
    assert {r['measurement_id'] for r in report['dispositions']} == ledger_ids
    observed = {mid for o in report['observations']
                for mid in o.get('measurement_ids', [o['id']])} & ledger_ids
    retained = {r['measurement_id'] for r in report['dispositions']
                if r['status'] not in {'compiled', 'residual_only'}}
    assert not observed & retained
    assert len(observed) + len(retained) == len(e['measurements'])
    assert report['coverage']['burden']['claim_accounting']['every_ledger_claim_accounted']
    # The count sidecar is accounted separately; it is not part of the ledger.
    assert len(report['count_dispositions']) == 1


def test_unmodelled_metrics_keep_a_specific_reason_instead_of_one_bucket():
    report, _ = compiled()
    assert disposition(report, 'staff')['reasons'] == ['metric_outside_compiled_channels:staffing_fte']
    assert disposition(report, 'volume')['reasons'] == ['metric_outside_compiled_channels:annual_volume']


def test_default_compilation_is_unchanged_by_the_new_channels():
    e, v, s, d, p = ledger()
    before = compile_durations(e, v, s, d, p)
    after = compile_durations(copy.deepcopy(e), v, s, d, p, burden_channels=(),
                              source_family_grouping='document')
    assert before == after
    assert before['schema_version'] == 'joint-visit-duration-compilation/1'
    assert 'burden' not in before['coverage']
    assert [r['reasons'] for r in before['dispositions'] if r['measurement_id'] != 'm1'] == [
        ['non_elapsed_or_not_current_empirical_timing']] * 6


# -------------------------------------------------------------------- contract
def test_compiled_bases_are_the_ones_the_model_implements():
    assert bc.MONEY_BASIS in MONEY_BASES
    assert set(bc.COUNT_BASES) <= MODEL_COUNT_BASES
    assert set(bc.COUNT_QUANTITY_BASES.values()) <= set(bc.COUNT_BASES)
    assert set(bc.EFFORT_BASES.values()) == {'payer_hours', 'agency_hours'}


def test_count_audit_is_validated_against_the_ledger_it_annotates():
    e, v, s, d, p = ledger()
    audit = count_audit(e['program_id'], case_id='unknown_case')
    with pytest.raises(ValueError, match='Unknown case identity'):
        validate_counts(audit, e, d)
    with pytest.raises(ValueError, match='Unknown case identity'):
        compile_durations(e, v, s, d, p, count_audit=audit, burden_channels=('count',))


def test_rounding_precision_follows_the_digits_actually_written():
    assert bc.written_precision(190) == 10. and bc.written_precision(194) == 1.
    assert bc.written_precision(400) == 100. and bc.written_precision(1.5) == .1


# --- source-family taxonomy on REAL document ids ------------------------------
# The first version read a type off the synthetic `<program>__<kind>` id shape.
# Real ids look like `cslb_weeks_to_process_table`, `ccr827`, `reddit_1lwvryd`,
# so every real source came back unclassified and the grouping pooled nothing --
# exactly where pooling the agency-versus-applicant contrast was the point.

def test_a_declared_kind_beats_the_id_shape():
    """The corpus records a kind per source; that is authoritative over id parsing."""
    from pipeline.procbench.burden_channels import document_type
    register = {'cslb_app_guide': 'program_page', 'ccr827': 'regulation',
                'cslb_weeks_to_process_table': 'official_stats',
                'sunset_review_2019': 'audit'}
    assert document_type('cslb_app_guide', register) == 'agency_official'
    assert document_type('ccr827', register) == 'agency_official'
    assert document_type('cslb_weeks_to_process_table', register) == 'agency_dashboard'


def test_frozen_forum_post_kind_is_recognized_without_filename_inference():
    assert bc.document_type('opaque_capture', {'opaque_capture':'forum_post'}) == 'forum'
    assert bc.document_type('opaque_capture', {'opaque_capture':'forum'}) == 'forum'


def test_uncovered_explicit_kind_is_not_overridden_by_a_filename_guess():
    assert bc.document_type('reddit_123', {'reddit_123':'unresolved_capture'}) is None
    assert bc.document_type('P__faq', {'P__faq':'unresolved_capture'}) is None


def test_a_self_identifying_prefix_is_recognised_without_a_register():
    """Forum ids carry their family in the id, and often arrive with no register."""
    from pipeline.procbench.burden_channels import document_type
    assert document_type('reddit_1lwvryd') == 'forum'
    assert document_type('forum_thread_9912') == 'forum'


def test_an_oversight_body_is_not_filed_as_news_or_as_the_agency():
    """An audit or grand-jury report exists because someone suspected a problem,
    so its bias is unlike the agency describing itself or a reporter covering it."""
    from pipeline.procbench.burden_channels import document_type
    for kind in ('audit', 'grand_jury', 'consultant_study'):
        assert document_type('doc_x', {'doc_x': kind}) == 'oversight'


@pytest.mark.parametrize('kind,expected', [
    ('applicant_forum', 'forum'),
    ('monthly_performance_table', 'agency_dashboard'),
    ('receipt_cohort_workbook', 'agency_dashboard'),
    ('completion_cohort_dashboard', 'agency_dashboard'),
    ('program_overview', 'agency_official'),
    ('initial_application_guide', 'agency_official'),
    ('renewal_guide', 'agency_official'),
    ('interview_and_pickup_guide', 'agency_official'),
    ('application_guide', 'agency_official'),
    ('expedited_service_guide', 'agency_official'),
    ('interview_guide', 'agency_official'),
    ('verification_checklist', 'agency_official'),
    ('issuance_guide', 'agency_official'),
    ('typical_time_faq', 'agency_official'),
])
def test_three_family_public_kind_aliases_work_without_guessing_unknown_sources(kind, expected):
    from pipeline.procbench.burden_channels import document_type, source_family
    assert document_type('opaque', {'opaque': kind}) == expected
    assert document_type('P__' + kind) == expected
    assert source_family('P__' + kind, 'document') == ('P__' + kind, None)
    assert document_type('P__' + kind, {'P__' + kind: 'unreviewed_source'}) is None


def test_the_synthetic_id_shape_still_resolves():
    """The synthetic corpus must keep working: this was a widening, not a swap."""
    from pipeline.procbench.burden_channels import document_type
    assert document_type('C29__S12__faq') == 'agency_official'
    assert document_type('C38__S03__official_stats') == 'agency_dashboard'
    assert document_type('C29__S12__reddit_2') == 'forum'


def test_an_unknown_document_is_still_not_guessed_into_a_family():
    """Inventing a source type would invent the pooled bias we are measuring."""
    from pipeline.procbench.burden_channels import document_type, source_family
    assert document_type('mystery_doc') is None
    assert source_family('mystery_doc', 'type') == ('mystery_doc', None)


# --- what a fee claim covers decides its form ---------------------------------
# An earlier version compiled EVERY case-linked fee as a whole-path total. On the
# real food-facility ledger that would have fitted a "$25,000 total overhead"
# figure and a monthly commissary rent as this permit route's cost, and driven a
# round-count posterior hard and wrongly. The contract records scope; use it.

def _fee(scope, activity_ids=(), value=450.0, case='c1', statistic='individual'):
    return dict(id='m_fee', metric='fee', unit='USD', scope=scope, statistic=statistic,
                case_id=case, value=value, lower=None, upper=None, qualitative=False,
                activity_ids=list(activity_ids), doc_id='d1', quote='q', interpretation='i')


def test_a_process_scoped_total_is_a_whole_path_sum():
    from pipeline.procbench.burden_channels import fee_compilation
    out = fee_compilation(_fee('process'))
    assert out['kind'] == 'observation'
    assert out['operator']['activity_ids'] == [], 'a process total sums the traversed path'
    assert out['provenance']['fee_scope']['operator'] == 'whole_case_path_total'


def test_a_step_scoped_payment_attaches_to_the_step_it_names():
    """Paying for a step is evidence the case traversed it, so naming it is right
    and a route omitting that step being refused is the correct reading."""
    from pipeline.procbench.burden_channels import fee_compilation
    out = fee_compilation(_fee('step', ['a_pay']))
    assert out['kind'] == 'observation'
    assert out['operator']['activity_ids'] == ['a_pay']
    assert out['provenance']['fee_scope']['operator'] == 'named_step_total'


def test_a_recurring_standing_amount_is_never_a_process_total():
    """Rent, an annual franchise tax and a periodic tag are real burdens that
    belong in the ledger, but adding them to a path total inflates it without
    bound as a case ages."""
    from pipeline.procbench.burden_channels import fee_compilation
    out = fee_compilation(_fee('standing', ['a_rent']))
    assert out['kind'] == 'unmodeled'
    assert 'standing_recurring_amount_is_not_a_process_path_total' in out['reasons']


def test_a_step_scoped_fee_naming_no_activity_cannot_be_attached():
    from pipeline.procbench.burden_channels import fee_compilation
    out = fee_compilation(_fee('step', []))
    assert out['kind'] == 'unmodeled'
    assert 'step_scoped_fee_names_no_activity_to_attach_to' in out['reasons']


def test_a_published_amount_with_no_case_is_still_a_route_input():
    from pipeline.procbench.burden_channels import fee_compilation
    out = fee_compilation(_fee('step', ['a_pay'], case=None))
    assert out['kind'] == 'route_input'


# --- declared kinds must actually reach the taxonomy --------------------------

def test_a_document_register_supplies_kinds_the_ids_do_not_carry():
    """The taxonomy fix was unreachable from the compiler until this was wired:
    the first real compile reported 19 of 20 families unclassified."""
    from pipeline.procbench.compile_visit_durations import declared_kinds
    register = dict(sources=[
        dict(source_id='S1', kind='statute', saved_as='raw/S1_gov_7922_535.txt'),
        dict(source_id='S2', kind='official_stats', saved_as='raw/weeks_table.txt'),
        dict(source_id='S3', saved_as='raw/no_kind.txt')])
    kinds = declared_kinds(register)
    assert kinds['S1_gov_7922_535'] == 'statute' and kinds['S1'] == 'statute'
    assert kinds['weeks_table'] == 'official_stats'
    assert 'no_kind' not in kinds, 'a source with no declared kind is not invented'


def test_declared_kinds_accepts_a_plain_map_and_nothing_at_all():
    from pipeline.procbench.compile_visit_durations import declared_kinds
    assert declared_kinds({'doc_a': 'faq'}) == {'doc_a': 'faq'}
    assert declared_kinds(None) is None, 'absent kinds must fall back to reading the id'
@pytest.mark.parametrize('declared', ['', None, 0, False, [], {}, '  ', 'unreviewed_source'])
def test_present_unresolved_source_declaration_never_guesses_from_alias(declared):
    from pipeline.procbench.burden_channels import document_type, source_family
    name = 'P__program_overview'
    assert document_type(name, {name: declared}) is None
    assert source_family(name, 'type', {name: declared}) == (name, None)
    assert source_family(name, 'document', {name: declared}) == (name, None)
