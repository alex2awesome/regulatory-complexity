import copy

import pytest

from pipeline.procbench.audit_burden_counts import VERSION, validate_counts
from test_bayes_hierarchy import fixture, measurement


def inputs():
    evidence = fixture()
    evidence['measurements'] = [measurement()]
    common = dict(case_id=None, activity_ids=['review'], actor_ids=['agency'],
                  scope='through_initial_decision', temporal_scope='current', population='Applicants',
                  source_family='document', duplicate_of=None,
                  evidence=[dict(doc_id='document', quote='Six in ten need corrections.')], notes='')
    rate = dict(**common, id='rate1', event='at_least_one_correction_per_case',
                denominator_unit='cases', conditioning='all applicants', basis='informal_frequency',
                value=.6, lower=None, upper=None, reported_numerator=6, reported_denominator=10,
                cohort_successes=None, cohort_trials=None)
    count = dict(**common, id='count1', quantity='additional_correction_rounds',
                 counting_unit='additional rounds', basis='observed_case', statistic='individual',
                 value=2, lower=None, upper=None, inventory_coverage='not_inventory')
    count.update(case_id='c1', evidence=[dict(doc_id='document', quote='I needed two extra rounds.')])
    audit = dict(schema_version=VERSION, program_id=evidence['program_id'],
                 count_claims=[count], rate_claims=[rate], unresolved=[])
    docs = [dict(id='document', text='Six in ten need corrections. I needed two extra rounds.')]
    return evidence, audit, docs


def test_frequency_wording_does_not_supply_an_empirical_sample_size():
    evidence, audit, docs = inputs()
    validate_counts(audit, evidence, docs)
    rate = audit['rate_claims'][0]
    rate.update(cohort_successes=6, cohort_trials=10)
    with pytest.raises(ValueError, match='actual empirical cohort'):
        validate_counts(audit, evidence, docs)
    rate['basis'] = 'empirical_cohort'
    # The structural validator cannot certify that the text actually implies
    # this basis. That semantic assertion still requires source review.
    validate_counts(audit, evidence, docs)
    rate['cohort_successes'] = 11
    with pytest.raises(ValueError, match='valid trial count'):
        validate_counts(audit, evidence, docs)


def test_counts_require_known_identity_and_verbatim_support():
    evidence, audit, docs = inputs()
    audit['count_claims'][0]['case_id'] = 'invented person'
    with pytest.raises(ValueError, match='Unknown case'):
        validate_counts(audit, evidence, docs)
    audit['count_claims'][0]['case_id'] = 'c1'
    audit['count_claims'][0]['evidence'][0]['quote'] = 'I needed three extra rounds.'
    with pytest.raises(ValueError, match='Nonverbatim'):
        validate_counts(audit, evidence, docs)


def test_private_actors_cannot_enter_public_organization_counts():
    evidence, audit, docs = inputs()
    count = audit['count_claims'][0]
    count.update(quantity='distinct_public_organizations', actor_ids=['payer'])
    with pytest.raises(ValueError, match='known private actors'):
        validate_counts(audit, evidence, docs)


def test_duplicate_references_are_typed_and_acyclic():
    evidence, audit, docs = inputs()
    count = audit['count_claims'][0]
    count['duplicate_of'] = 'rate1'
    with pytest.raises(ValueError, match='same kind'):
        validate_counts(audit, evidence, docs)
    second = copy.deepcopy(count)
    second.update(id='count2', duplicate_of='count1')
    count['duplicate_of'] = 'count2'
    audit['count_claims'].append(second)
    with pytest.raises(ValueError, match='cycle'):
        validate_counts(audit, evidence, docs)
    count['duplicate_of'] = None
    validate_counts(audit, evidence, docs)


def test_partial_counts_remain_bounds_and_empty_audits_are_allowed():
    evidence, audit, docs = inputs()
    count = audit['count_claims'][0]
    count.update(statistic='lower_bound', value=None, lower=2)
    validate_counts(audit, evidence, docs)
    count['upper'] = 1
    with pytest.raises(ValueError, match='Reversed interval'):
        validate_counts(audit, evidence, docs)
    audit.update(count_claims=[], rate_claims=[])
    validate_counts(audit, evidence, docs)


def test_cohort_denominator_alone_does_not_require_invented_success_count():
    evidence, audit, docs = inputs()
    rate = audit['rate_claims'][0]
    rate.update(basis='empirical_cohort', cohort_trials=100, cohort_successes=None)
    validate_counts(audit, evidence, docs)
    rate['case_id'] = 'c1'
    with pytest.raises(ValueError, match='population frequency'):
        validate_counts(audit, evidence, docs)


def test_exact_count_is_not_a_fraction_or_inventory_disguised_as_a_case():
    evidence, audit, docs = inputs()
    count = audit['count_claims'][0]
    count['value'] = 2.5
    with pytest.raises(ValueError, match='integral'):
        validate_counts(audit, evidence, docs)
    count.update(value=2, inventory_coverage='complete_for_stated_scope')
    with pytest.raises(ValueError, match='only to an inventory'):
        validate_counts(audit, evidence, docs)
