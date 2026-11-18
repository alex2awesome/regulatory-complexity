"""Copied-claim detection and the deduplication sensitivity variant.

The corpus plants copied claims: one source restating another's figures as its
own case, in a different thread. The compiler cannot express the dependency,
because a report group may not span two `case_id`s -- correctly, since a report
group is one report restated, not two cases merged. So two copies of one
duration can enter a fit as two independent factors, which is a double count.

These tests pin the two judgements that make the detector usable rather than
noisy: agreement is counted per ACTIVITY (a ledger storing one claim in two
units must not look like two agreements), and only DISTINCTIVE values count (a
step two cases both call "same day" is what that step takes, not a fingerprint).
They also pin the variant builder's transitive handling, because a hub case that
is the copy in several pairs must be dropped once, not take its partners with it.

Offline, no network, no model call.
"""
from __future__ import annotations

import json

import pytest

from pipeline.procbench.audit_copied_claims import clusters, informative_ids, report


def measurement(mid, case, activity, value, unit='calendar_days'):
    row = dict(id=mid, metric='elapsed', unit=unit, case_id=case, value=value)
    if activity:
        row['activity_ids'] = [activity]
    return row


def ledger(measurements, program='P'):
    return dict(schema_version='process-evidence/3', program_id=program, measurements=measurements)


def compilation(informative=(), residual=(), program='P'):
    rows = [dict(id=i, case_id=None, operators=[dict(basis='sum_visit_cycles')]) for i in informative]
    rows += [dict(id=i, case_id=None, operators=[dict(basis='unmodeled_duration')]) for i in residual]
    return dict(program_id=program, observations=rows)


def test_one_shared_activity_is_weak_because_common_figures_recur():
    """Two cases agreeing on a single step prove nothing and must not be called a copy."""
    found = clusters(ledger([measurement('m1', 'a', 'file', 7),
                             measurement('m2', 'b', 'file', 7)]))
    assert len(found) == 1
    assert found[0]['strength'] == 'weak' and found[0]['agreements'] == 1


def test_several_distinctive_agreements_are_a_copy():
    found = clusters(ledger([measurement('m1', 'a', 'file', 369), measurement('m2', 'a', 'pay', 34),
                             measurement('m3', 'a', None, 676),
                             measurement('m4', 'b', 'file', 369), measurement('m5', 'b', 'pay', 34),
                             measurement('m6', 'b', None, 676)]))
    assert len(found) == 1
    assert found[0]['strength'] == 'strong'
    assert found[0]['agreements'] == 3 and found[0]['distinctive_agreements'] == 3


def test_one_claim_stored_in_two_units_counts_as_one_agreement():
    """A ledger records "same day or next business day" twice. That is one claim.

    Counting the calendar-day and business-day forms separately would turn a
    single shared trivially-short step into fake evidence of copying.
    """
    rows = []
    for case in ('a', 'b'):
        rows += [measurement('%s1' % case, case, 'portal', 1, 'business_days'),
                 measurement('%s2' % case, case, 'portal', [0, 1], 'calendar_days')]
    found = clusters(ledger(rows))
    assert len(found) == 1
    assert found[0]['agreements'] == 1, 'two unit forms of one claim are one agreement'
    assert found[0]['strength'] == 'weak'


def test_a_value_many_cases_share_is_a_common_figure_not_a_fingerprint():
    """Three cases reporting the same two steps: the values are no longer distinctive,
    so the pair is reported as common_values, never as a copy."""
    rows = []
    for case in ('a', 'b', 'c'):
        rows += [measurement('%s1' % case, case, 'portal', 1),
                 measurement('%s2' % case, case, 'screen', 1)]
    found = clusters(ledger(rows))
    assert found and all(c['strength'] == 'common_values' for c in found)
    assert all(c['distinctive_agreements'] == 0 for c in found)


def test_a_residual_only_copy_is_not_double_counted_and_the_audit_passes():
    """A residual row is a process-independent constant, so it cannot reinforce a twin."""
    evidence = ledger([measurement('m1', 'a', 'file', 369), measurement('m2', 'a', 'pay', 34),
                       measurement('m3', 'b', 'file', 369), measurement('m4', 'b', 'pay', 34)])
    out = report(evidence, compilation(informative=['m1', 'm2'], residual=['m3', 'm4']))
    assert out['strong_clusters'] == 1
    assert out['double_counted_clusters'] == 0
    assert not out['strong'][0]['both_sides_informative']


def test_informative_on_both_sides_is_the_failure_the_exit_code_reports():
    evidence = ledger([measurement('m1', 'a', 'file', 369), measurement('m2', 'a', 'pay', 34),
                       measurement('m3', 'b', 'file', 369), measurement('m4', 'b', 'pay', 34)])
    out = report(evidence, compilation(informative=['m1', 'm2', 'm3', 'm4']))
    assert out['double_counted_clusters'] == 1
    assert 'twice' in out['verdict']


def test_informative_ids_reads_a_modelled_operator_not_a_residual_one():
    got = informative_ids(compilation(informative=['x'], residual=['y']))
    assert got == {'x'}


def test_a_hub_copy_is_dropped_once_and_does_not_take_its_partners_with_it():
    """One source may be the copy in several pairs. Dropping it resolves all of them.

    Without transitive handling the variant also drops that case's partners, discarding
    evidence the duplication never touched -- which would overstate the sensitivity.
    """
    from pipeline.procbench.dedup_copied_cases import plan
    audit = dict(programs=[dict(program_id='P', strong=[
        dict(cases=['hub', 'x'], both_sides_informative=True, distinctive_agreements=3,
             left_informative=['h1', 'h2'], right_informative=['x1']),
        dict(cases=['hub', 'y'], both_sides_informative=True, distinctive_agreements=2,
             left_informative=['h1', 'h2'], right_informative=['y1']),
    ])])
    data = dict(programs=[dict(id='P', observations=[
        dict(id='h1', case_id='hub', operators=[dict(basis='sum_visit_cycles')]),
        dict(id='x1', case_id='x', operators=[dict(basis='sum_visit_cycles')]),
        dict(id='y1', case_id='y', operators=[dict(basis='sum_visit_cycles')])])])
    _, dropped, decisions, _ = plan(data, audit, 'P')
    assert dropped == {'hub'}, 'the hub is dropped once; x and y are kept'
    # Both pairs are resolved by that single drop, so both name it.
    assert [d['action'] for d in decisions] == ['dropped hub', 'dropped hub']


def test_a_one_sided_cluster_drops_nothing():
    from pipeline.procbench.dedup_copied_cases import plan
    audit = dict(programs=[dict(program_id='P', strong=[
        dict(cases=['a', 'b'], both_sides_informative=False, distinctive_agreements=3,
             left_informative=['m1'], right_informative=[])])])
    data = dict(programs=[dict(id='P', observations=[
        dict(id='m1', case_id='a', operators=[dict(basis='sum_visit_cycles')])])])
    _, dropped, decisions, _ = plan(data, audit, 'P')
    assert dropped == set()
    assert decisions[0]['action'] == 'kept both'


def test_a_single_pair_drops_the_side_carrying_less_evidence():
    from pipeline.procbench.dedup_copied_cases import choose_dropped
    cluster = dict(cases=['keep', 'drop'], left_informative=['a', 'b'], right_informative=['c'])
    assert choose_dropped(cluster, set()) == 'drop'
    tie = dict(cases=['aaa', 'zzz'], left_informative=['a'], right_informative=['b'])
    assert choose_dropped(tie, set()) == 'zzz', 'ties break on case id, so the choice is reproducible'


def test_the_cover_prefers_dropping_less_evidence_on_a_tie_of_degree():
    from pipeline.procbench.dedup_copied_cases import cover
    # One pair, both cases in one pair each: degree ties, so evidence decides.
    assert cover([['rich', 'poor']], dict(rich=5, poor=1)) == ['poor']


def test_a_case_pinned_by_keep_survives_and_its_partner_is_dropped():
    from pipeline.procbench.dedup_copied_cases import cover
    assert cover([['hub', 'x']], dict(hub=9, x=1), keep={'hub'}) == ['x']


def test_non_elapsed_and_valueless_rows_are_ignored():
    rows = [dict(id='f1', metric='fee', unit='USD', case_id='a', value=190, activity_ids=['pay']),
            dict(id='f2', metric='fee', unit='USD', case_id='b', value=190, activity_ids=['pay']),
            dict(id='q1', metric='elapsed', unit='calendar_days', case_id='a', value=None,
                 lower=None, upper=None, activity_ids=['file'])]
    assert clusters(ledger(rows)) == []
