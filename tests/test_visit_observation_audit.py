import copy

import pytest

from pipeline.procbench.audit_visit_observations import VERSION, validate_visit_audit
from test_bayes_hierarchy import fixture, measurement


def inputs():
    e = fixture()
    e['measurements'] = [measurement(ident='one')]
    operator = dict(basis='sum_visit_cycles', activity_ids=['review'],
                    start='single_visit_start', end='single_visit_end',
                    visits='all_completed_by_observation', censoring='none', notes='')
    row = dict(measurement_id='one', identification='explicit', activity_mapping='supported',
               operators=[operator], evidence=[dict(doc_id='document', quote='Evidence')], notes='')
    audit = dict(schema_version=VERSION, program_id=e['program_id'], measurements=[row], unresolved=[])
    return e, audit, [dict(id='document', text='Evidence')]


def test_per_cycle_reported_coverage_is_distinct_from_an_aggregate():
    e, audit, docs = inputs()
    validate_visit_audit(audit, e, docs)
    audit['measurements'][0]['operators'][0]['basis'] = 'single_visit_cycle'
    # Revised contract: "quick each reported round" is per-cycle, although
    # its reporting coverage spans multiple observed rounds. It is not a sum.
    validate_visit_audit(audit, e, docs)
    audit['measurements'][0]['operators'][0]['visits'] = 'all_in_completed_case'
    with pytest.raises(ValueError, match='one visit or reported per-visit coverage'):
        validate_visit_audit(audit, e, docs)


def test_first_final_and_latest_recorded_decisions_are_distinct_values():
    e, audit, docs = inputs()
    row = audit['measurements'][0]
    row['identification'] = 'unresolved'
    row['operators'] = [dict(basis='whole_case_clock', activity_ids=[], start='process_start',
        end=endpoint, visits='not_applicable', censoring='none', notes='')
        for endpoint in ('initial_decision', 'final_decision', 'latest_recorded_decision')]
    validate_visit_audit(audit, e, docs)
    row['identification'] = 'explicit'
    with pytest.raises(ValueError, match='alternative operators are unresolved'):
        validate_visit_audit(audit, e, docs)


def test_unfinished_observation_time_is_not_a_completed_decision():
    e, audit, docs = inputs()
    row = audit['measurements'][0]
    row['operators'][0]['end'] = 'observation_time'
    with pytest.raises(ValueError, match='does not establish completion'):
        validate_visit_audit(audit, e, docs)
    row['identification'] = 'unresolved'
    row['operators'][0]['censoring'] = 'unresolved'
    validate_visit_audit(audit, e, docs)


def test_claim_coverage_identity_duplicates_and_quotes_are_checked():
    e, audit, docs = inputs()
    row = audit['measurements'][0]
    row['identification'] = 'unresolved'
    row['operators'].append(copy.deepcopy(row['operators'][0]))
    with pytest.raises(ValueError, match='Duplicate operator'):
        validate_visit_audit(audit, e, docs)
    row['operators'].pop()
    row['operators'][0]['activity_ids'] = ['invented']
    with pytest.raises(ValueError, match='activity identity'):
        validate_visit_audit(audit, e, docs)
    row['operators'][0]['activity_ids'] = ['review']
    row['evidence'][0]['quote'] = 'Not in the document'
    with pytest.raises(ValueError, match='Nonverbatim'):
        validate_visit_audit(audit, e, docs)
