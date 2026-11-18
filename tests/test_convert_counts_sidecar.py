"""The counts-sidecar converter must move only genuine per-case burden counts.

The risk this guards is silent mis-conversion: a sidecar row is a number with a
prose unit, and several of the numbers in these corpora are statutory limits,
retention periods and fee percentages. Fitting a four-firearm statutory limit as
four correction rounds would inflate measured burden with no gate catching it,
which is the same failure mode the copied-claim audit found.
"""
import copy

import pytest

from pipeline.procbench.convert_counts_sidecar import convert


def _evidence():
    return {
        'schema_version': 'process-evidence/3',
        'program_id': 'p__prog',
        'actors': [{'id': 'agency__x', 'name': 'X', 'role': 'agency', 'evidence': []}],
        'activities': [
            {'id': 'p__submit', 'name': 'Submit', 'actor_id': 'agency__x', 'scope': 'core',
             'stage': 'submission', 'task_type': 'submission', 'existence': 'explicit',
             'condition': None, 'notes': '', 'evidence': []},
            {'id': 'p__other', 'name': 'Other', 'actor_id': 'agency__x', 'scope': 'core',
             'stage': 'review', 'task_type': 'review', 'existence': 'explicit',
             'condition': None, 'notes': '', 'evidence': []}],
        'relations': [],
        'measurements': [
            {'id': 'p__m1', 'case_id': 'p__case_a', 'doc_id': 'd1', 'metric': 'elapsed',
             'quote': 'it took 5 days', 'activity_ids': ['p__submit'], 'value': 5.0,
             'lower': None, 'upper': None, 'unit': 'calendar_days', 'statistic': 'individual',
             'scope': 'activity_only', 'start': None, 'end': None, 'n': None,
             'qualitative': False, 'cohort': None, 'interpretation': '',
             'source_family': 'd1'}],
        'observation_contexts': [
            {'measurement_id': 'p__m1', 'temporal_scope': 'current', 'segment_mode': None,
             'decision_activity_id': None, 'clock_start_after_activity_ids': [],
             'required_activity_ids': [], 'excluded_activity_ids': [], 'notes': '',
             'evidence': []}],
        'ambiguities': [], 'excluded': []}


def _sidecar(**over):
    row = {'id': 'c1', 'kind': 'trip_count', 'value': 3, 'lower': None, 'upper': None,
           'unit': 'store visits for one purchase', 'subject': 'trips in one case',
           'attaches_to_activity': 'p__submit', 'case_id': 'p__case_a', 'doc_id': 'd1',
           'quote': 'I had to drive back three times', 'note': ''}
    row.update(over)
    return {'schema_version': 'process-evidence-counts-sidecar/1', 'program_id': 'p__prog',
            'about': '', 'quotes_verified': True, 'entries': [row]}


DOCS = [{'id': 'd1', 'text': 'it took 5 days and I had to drive back three times, again and again'}]


def test_converts_a_per_case_visit_count():
    audit = convert(_sidecar(), _evidence(), DOCS)
    assert audit['schema_version'] == 'burden-count-evidence/1'
    assert len(audit['count_claims']) == 1 and not audit['unresolved']
    claim = audit['count_claims'][0]
    assert claim['quantity'] == 'encounters_or_visits'
    assert claim['basis'] == 'observed_case' and claim['statistic'] == 'individual'
    assert claim['value'] == 3 and claim['inventory_coverage'] == 'not_inventory'
    assert claim['actor_ids'] == ['agency__x']
    assert claim['temporal_scope'] == 'current'


@pytest.mark.parametrize('kind', ['rule_count', 'outcome_count', 'firearm_count', 'fee_rate',
                                  'retention_period', 'validity_period', 'prohibition_period',
                                  'record_count', 'dealer_count', 'workload_count', 'case_count',
                                  'rate_cap', 'fee_rate_basis'])
def test_kinds_that_are_never_burden_counts_are_refused_with_a_reason(kind):
    audit = convert(_sidecar(kind=kind), _evidence(), DOCS)
    assert not audit['count_claims']
    assert len(audit['unresolved']) == 1
    assert audit['unresolved'][0]['reason'].startswith('c1 [%s' % kind)
    assert audit['unresolved'][0]['evidence'][0]['quote'] == 'I had to drive back three times'


def test_a_statutory_limit_is_never_converted_as_repetition():
    """Four firearms allowed in thirty days is not four correction rounds."""
    audit = convert(_sidecar(kind='firearm_count', value=4,
                             unit='firearms allowed inside 30 days'), _evidence(), DOCS)
    assert not audit['count_claims']


def test_wording_spanning_several_cases_is_refused_even_with_a_case_id():
    audit = convert(_sidecar(unit='dealer visits across 20 purchases'), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'more than one case' in audit['unresolved'][0]['reason']


def test_a_case_identity_absent_from_the_ledger_is_refused_not_invented():
    audit = convert(_sidecar(case_id='p__case_missing'), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'not a case of the accepted ledger' in audit['unresolved'][0]['reason']


def test_a_quote_declared_count_only_case_does_not_need_a_fake_duration():
    registry = dict(schema_version='burden-case-registry/1', program_id='p__prog', cases=[dict(
        case_id='p__case_missing', description='One purchaser reporting return visits', notes='',
        evidence=[dict(doc_id='d1', quote='I had to drive back three times')])])
    e = _evidence()
    original = copy.deepcopy(e)
    audit = convert(_sidecar(case_id='p__case_missing'), e, DOCS, case_registry=registry)
    assert e == original
    assert audit['schema_version'] == 'burden-count-evidence/2'
    assert audit['count_claims'][0]['case_id'] == 'p__case_missing'
    assert not audit['unresolved']


def test_a_row_with_no_case_identity_is_refused():
    audit = convert(_sidecar(case_id=None), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'No case identity' in audit['unresolved'][0]['reason']


def test_an_activity_absent_from_the_ledger_is_refused():
    audit = convert(_sidecar(attaches_to_activity='p__nope'), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'not an activity of the accepted ledger' in audit['unresolved'][0]['reason']


def test_additional_rounds_and_total_attempts_are_distinguished_not_guessed():
    extra = convert(_sidecar(kind='submission_count', value=2,
                             unit='additional submissions after the first was rejected',
                             subject='extra rounds'), _evidence(), DOCS)
    assert extra['count_claims'][0]['quantity'] == 'additional_correction_rounds'

    made = convert(_sidecar(kind='submission_count', value=2,
                            unit='submissions for one firearm',
                            subject='submissions in one purchase'), _evidence(), DOCS)
    assert made['count_claims'][0]['quantity'] == 'total_attempts'

    neither = convert(_sidecar(kind='submission_count', value=2, unit='paperwork',
                               subject='forms'), _evidence(), DOCS)
    assert not neither['count_claims']
    assert 'differ by one' in neither['unresolved'][0]['reason']


def test_no_finite_amount_is_refused():
    audit = convert(_sidecar(value=None, lower=None, upper=None), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'No finite amount' in audit['unresolved'][0]['reason']


def test_an_unknown_kind_is_refused_rather_than_defaulted():
    audit = convert(_sidecar(kind='novel_count'), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'no policy decides' in audit['unresolved'][0]['reason']


def test_a_program_identity_change_is_rejected():
    sidecar = _sidecar()
    sidecar['program_id'] = 'p__different'
    with pytest.raises(ValueError, match='Program identity changed'):
        convert(sidecar, _evidence(), DOCS)


def test_a_foreign_schema_is_rejected():
    sidecar = _sidecar()
    sidecar['schema_version'] = 'something-else/1'
    with pytest.raises(ValueError, match='Not a process-evidence-counts-sidecar'):
        convert(sidecar, _evidence(), DOCS)


def test_every_sidecar_row_is_either_converted_or_refused():
    """No row may be dropped silently; a refused count is not a zero count."""
    sidecar = _sidecar()
    sidecar['entries'] = [dict(sidecar['entries'][0], id='c%d' % i, kind=kind)
                          for i, kind in enumerate(
                              ['trip_count', 'rule_count', 'submission_count', 'fee_rate',
                               'outcome_count', 'interaction_count'])]
    audit = convert(sidecar, _evidence(), DOCS)
    assert len(audit['count_claims']) + len(audit['unresolved']) == len(sidecar['entries'])


def test_the_evidence_ledger_is_not_modified():
    evidence = _evidence()
    before = copy.deepcopy(evidence)
    convert(_sidecar(), evidence, DOCS)
    assert evidence == before


def test_a_quote_absent_from_its_document_is_rejected_by_validation():
    with pytest.raises(Exception):
        convert(_sidecar(quote='a sentence that is not in the document'), _evidence(), DOCS)


@pytest.mark.parametrize('kind', ['call_attempt_count', 'contact_count', 'call_count',
                                  'office_visit_count', 'appointment_count', 'interview_count',
                                  'escalation_count'])
def test_contact_kinds_convert_as_encounters(kind):
    audit = convert(_sidecar(kind=kind), _evidence(), DOCS)
    assert audit['count_claims'][0]['quantity'] == 'encounters_or_visits'


@pytest.mark.parametrize('kind', ['routing_rate', 'callback_rate', 'resolution_rate', 'answer_rate'])
def test_frequencies_are_refused_rather_than_given_an_invented_denominator(kind):
    audit = convert(_sidecar(kind=kind), _evidence(), DOCS)
    assert not audit['count_claims']
    assert 'denominator the document did not state' in audit['unresolved'][0]['reason']


@pytest.mark.parametrize('kind', ['notice_count', 'staff_count', 'work_item_count',
                                  'self_service_count', 'page_count', 'document_count'])
def test_agency_output_is_never_counted_as_applicant_burden(kind):
    audit = convert(_sidecar(kind=kind), _evidence(), DOCS)
    assert not audit['count_claims']
