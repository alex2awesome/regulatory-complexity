"""A skeleton is a work order, and must never be mistakable for a decision.

The failure this guards against is a placeholder reaching the compiler as if it
were an audited judgement. Two defences are pinned here: the declared schema is
one no consumer accepts, and every placeholder field is also named in the row's
`to_decide` list.
"""
import copy

import pytest

from pipeline.procbench.derive_audit_skeletons import PLACEHOLDER, derive


def _measurement(ident='p__m1', metric='elapsed', statistic='individual', scope='activity_only',
                 unit='calendar_days', value=5.0, quote='it took 5 days'):
    return {'id': ident, 'case_id': 'p__case', 'doc_id': 'd1', 'metric': metric, 'quote': quote,
            'activity_ids': ['p__submit'], 'value': value, 'lower': None, 'upper': None,
            'unit': unit, 'statistic': statistic, 'scope': scope, 'start': None, 'end': None,
            'n': None, 'qualitative': False, 'cohort': None, 'interpretation': '',
            'source_family': 'd1'}


def _evidence(measurements=None, contexts=None):
    return {'schema_version': 'process-evidence/3', 'program_id': 'p__prog',
            'actors': [], 'activities': [], 'relations': [],
            'measurements': measurements if measurements is not None else [_measurement()],
            'observation_contexts': contexts or [], 'ambiguities': [], 'excluded': []}


DOCS = [{'id': 'd1', 'text': 'it took 5 days and then it took 9 weeks'}]


def test_both_skeletons_declare_a_schema_no_consumer_accepts():
    visit, semantic = derive(_evidence(), DOCS)
    assert visit['schema_version'] == 'visit-audit-skeleton/1'
    assert semantic['schema_version'] == 'semantic-audit-skeleton/1'
    assert visit['target_schema'] == 'visit-observation-evidence/1'


def test_every_judgement_field_is_a_placeholder_and_is_listed_in_to_decide():
    visit, semantic = derive(_evidence(), DOCS)
    v, s = visit['measurements'][0], semantic['measurements'][0]
    for field in v['to_decide']:
        assert v.get(field) == PLACEHOLDER or v['operators'][0].get(field) == PLACEHOLDER
    for field in s['to_decide']:
        assert s[field] == PLACEHOLDER


def test_reporting_sample_is_not_defaulted_because_its_enum_has_no_abstention():
    _, semantic = derive(_evidence(), DOCS)
    assert semantic['measurements'][0]['reporting_sample'] == PLACEHOLDER
    assert 'reporting_sample' in semantic['measurements'][0]['to_decide']


def test_the_stated_unit_is_the_only_field_filled_without_judgement():
    _, semantic = derive(_evidence([_measurement(unit='weeks', quote='it took 9 weeks')]), DOCS)
    row = semantic['measurements'][0]
    assert row['original_precision_unit'] == 'weeks'
    assert 'original_precision_unit' not in row['to_decide']


def test_an_unrecognised_unit_becomes_unspecified_rather_than_guessed():
    _, semantic = derive(_evidence([_measurement(unit='fortnights')]), DOCS)
    assert semantic['measurements'][0]['original_precision_unit'] == 'unspecified'


def test_only_eligible_measurements_get_rows():
    measurements = [
        _measurement('p__ok'),
        _measurement('p__cap', statistic='statutory_cap'),
        _measurement('p__target', statistic='target'),
        _measurement('p__standing', scope='standing'),
        _measurement('p__fee', metric='fee'),
        dict(_measurement('p__noamount'), value=None, lower=None, upper=None)]
    visit, semantic = derive(_evidence(measurements), DOCS)
    assert [r['measurement_id'] for r in visit['measurements']] == ['p__ok']
    assert [r['measurement_id'] for r in semantic['measurements']] == ['p__ok']
    assert visit['eligible'] == 1 and visit['elapsed_in_ledger'] == 5


def test_a_historical_context_makes_a_measurement_ineligible():
    contexts = [{'measurement_id': 'p__m1', 'temporal_scope': 'historical'}]
    visit, _ = derive(_evidence(contexts=contexts), DOCS)
    assert visit['measurements'] == [] and visit['eligible'] == 0


def test_the_row_carries_the_ledger_facts_needed_to_decide():
    contexts = [{'measurement_id': 'p__m1', 'temporal_scope': 'current',
                 'segment_mode': 'span', 'decision_activity_id': 'p__decide', 'notes': 'ctx note'}]
    visit, _ = derive(_evidence(contexts=contexts), DOCS)
    row = visit['measurements'][0]
    assert row['ledger_statistic'] == 'individual'
    assert row['ledger_activity_ids'] == ['p__submit']
    assert row['context_temporal_scope'] == 'current'
    assert row['context_decision_activity_id'] == 'p__decide'
    assert row['evidence'] == [{'doc_id': 'd1', 'quote': 'it took 5 days'}]


def test_a_non_verbatim_quote_is_rejected_rather_than_carried():
    with pytest.raises(ValueError, match='NON-VERBATIM'):
        derive(_evidence([_measurement(quote='a span not in the document')]), DOCS)


def test_without_documents_quotes_are_not_reverified_and_that_is_recorded():
    visit, _ = derive(_evidence([_measurement(quote='a span not in the document')]), None)
    assert visit['quotes_reverified'] is False


def test_the_field_guide_names_every_decision():
    visit, semantic = derive(_evidence(), DOCS)
    assert set(visit['field_guide']) == set(visit['measurements'][0]['to_decide'])
    assert set(semantic['field_guide']) == set(semantic['measurements'][0]['to_decide'])


def test_the_ledger_is_not_modified():
    evidence = _evidence()
    before = copy.deepcopy(evidence)
    derive(evidence, DOCS)
    assert evidence == before
