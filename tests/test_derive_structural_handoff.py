"""A derived handoff must be honest about being derived, and must not invent.

The danger is not that the derivation is wrong; it is that a derived handoff
looks exactly like an authored one to every downstream consumer. These tests pin
the markings that keep the two apart, and pin the sections the module must leave
empty rather than guess.
"""
import pytest

from pipeline.procbench.derive_structural_handoff import derive


def _act(ident, scope, stage='review', task_type='other', actor='agency__x', quote='a quoted span'):
    return {'id': ident, 'name': ident, 'actor_id': actor, 'scope': scope, 'stage': stage,
            'task_type': task_type, 'existence': 'explicit', 'condition': None, 'notes': '',
            'evidence': [{'doc_id': 'd1', 'quote': quote}]}


def _evidence(activities=None, relations=None, measurements=None):
    return {
        'schema_version': 'process-evidence/3', 'program_id': 'p__prog',
        'actors': [{'id': 'agency__x', 'name': 'X', 'role': 'agency', 'evidence': []},
                   {'id': 'payer__a', 'name': 'A', 'role': 'payer', 'evidence': []}],
        'activities': activities if activities is not None else [
            _act('p__core', 'core'), _act('p__cond', 'conditional'),
            _act('p__stand', 'standing'), _act('p__oos', 'out_of_scope')],
        'relations': relations or [], 'measurements': measurements or [],
        'observation_contexts': [], 'ambiguities': [], 'excluded': []}


DOCS = [{'id': 'd1', 'text': 'a quoted span and also another quoted span here'}]


def test_scope_decides_the_classification():
    h = derive(_evidence(), DOCS)
    got = {c['activity_id']: c['classification'] for c in h['activity_classifications']}
    assert got['p__core'] == 'performed_operation'
    assert got['p__cond'] == 'performed_operation'
    assert got['p__stand'] == 'standing_obligation'
    assert got['p__oos'].startswith('out_of_scope')


def test_the_output_is_marked_derived_and_unreviewed():
    h = derive(_evidence(), DOCS)
    assert h['variant'] == 'derived_default'
    assert h['reviewed'] is False
    assert h['diagnostic_only'] is True
    assert h['hidden_truth_read'] is False
    assert h['new_model_calls'] == 0
    assert h['changes_accepted_evidence'] is False
    assert 'DERIVED DEFAULT' in h['interpretation_status']


def test_every_per_activity_judgment_says_it_was_not_authored():
    h = derive(_evidence(), DOCS)
    assert all('DERIVED, NOT AUTHORED' in c['judgment'] for c in h['activity_classifications'])


def test_judgement_bearing_sections_are_left_empty_not_guessed():
    h = derive(_evidence(), DOCS)
    assert h['inventory_identity_hypotheses'] == []
    assert h['clock_boundary_markers'] == {}
    assert h['agency_identity_notes'] == []
    assert h['distinct_case_warnings'] == []
    assert len(h['derivation']['not_derived']) >= 5


def test_an_unknown_scope_is_flagged_rather_than_treated_as_an_operation():
    h = derive(_evidence([_act('p__weird', 'something_new')]), DOCS)
    cls = h['activity_classifications'][0]['classification']
    assert cls != 'performed_operation' and 'unclassified' in cls
    assert h['derivation']['unclassified_activities'] == ['p__weird']


def _rework(source, target):
    return {'kind': 'rework', 'source': source, 'target': target, 'existence': 'explicit',
            'evidence': [{'doc_id': 'd1', 'quote': 'a quoted span'}]}


def test_one_connected_group_of_rework_becomes_one_repeat_link():
    relations = [_rework('p__core', 'p__cond'),
                 {'kind': 'precedes', 'source': 'p__core', 'target': 'p__cond',
                  'existence': 'explicit', 'evidence': []}]
    h = derive(_evidence(relations=relations), DOCS)
    assert len(h['repeat_links']) == 1
    assert h['repeat_links'][0]['activity_ids'] == ['p__cond', 'p__core']
    assert h['other_rework_relations_not_submitted_as_repeat_links'] == []


def test_rework_relations_sharing_an_activity_are_one_group():
    acts = [_act('a', 'core'), _act('b', 'core'), _act('c', 'core')]
    h = derive(_evidence(acts, [_rework('a', 'b'), _rework('b', 'c')]), DOCS)
    assert len(h['repeat_links']) == 1
    assert h['repeat_links'][0]['activity_ids'] == ['a', 'b', 'c']


def test_several_disconnected_loops_are_reported_and_none_is_chosen():
    """V6 carries one repeat block per programme; picking one is a judgement."""
    acts = [_act(x, 'core') for x in 'abcd']
    h = derive(_evidence(acts, [_rework('a', 'b'), _rework('c', 'd')]), DOCS)
    assert h['repeat_links'] == []
    unencoded = h['other_rework_relations_not_submitted_as_repeat_links']
    assert len(unencoded) == 2
    assert all('one repeat block per programme' in u['reason'] for u in unencoded)
    assert h['derivation']['counts']['rework_groups'] == 2
    assert h['derivation']['counts']['rework_groups_not_encoded'] == 2


def test_no_rework_means_no_repeat_link_and_nothing_reported():
    h = derive(_evidence(), DOCS)
    assert h['repeat_links'] == []
    assert h['other_rework_relations_not_submitted_as_repeat_links'] == []


def test_parallel_relations_are_reported_but_never_become_repeat_links():
    """A parallel edge halves the modelled clock, so it is surfaced, not applied."""
    relations = [{'kind': 'parallel', 'source': 'p__core', 'target': 'p__cond',
                  'existence': 'explicit', 'evidence': [{'doc_id': 'd1', 'quote': 'a quoted span'}]}]
    h = derive(_evidence(relations=relations), DOCS)
    assert h['repeat_links'] == []
    assert len(h['parallel_relations_in_ledger']) == 1


def test_decisions_are_grouped_only_from_core_and_conditional_activities():
    acts = [_act('p__d1', 'core', stage='decision', task_type='decision'),
            _act('p__d2', 'out_of_scope', stage='decision', task_type='decision'),
            _act('p__d3', 'standing', stage='decision', task_type='decision')]
    h = derive(_evidence(acts), DOCS)
    assert h['conditional_paths_and_outcomes'][0]['activity_ids'] == ['p__d1']
    assert h['conditional_paths_and_outcomes'][0]['decision_scope'] == 'per_decision_occasion'


def test_no_decision_group_is_emitted_when_the_ledger_has_no_decision():
    h = derive(_evidence(), DOCS)
    assert h['conditional_paths_and_outcomes'] == []


def test_measurements_sharing_a_source_family_are_grouped_as_one_report():
    ms = [{'id': 'm1', 'doc_id': 'd1', 'source_family': 'f', 'case_id': None},
          {'id': 'm2', 'doc_id': 'd1', 'source_family': 'f', 'case_id': None},
          {'id': 'm3', 'doc_id': 'd1', 'source_family': 'g', 'case_id': None}]
    h = derive(_evidence(measurements=ms), DOCS)
    groups = {g['id']: g['measurement_ids'] for g in h['same_report_measurement_groups']}
    assert groups == {'derived_family__f': ['m1', 'm2']}


def test_a_non_verbatim_ledger_quote_is_rejected_not_carried():
    acts = [_act('p__core', 'core', quote='a span that is not in the document')]
    with pytest.raises(ValueError, match='NON-VERBATIM'):
        derive(_evidence(acts), DOCS)


def test_quotes_are_not_reverified_when_no_documents_are_supplied_and_that_is_recorded():
    acts = [_act('p__core', 'core', quote='a span that is not in the document')]
    h = derive(_evidence(acts), None)
    assert h['provenance']['quotes_reverified'] is False


def test_the_ledger_is_not_modified():
    import copy
    evidence = _evidence()
    before = copy.deepcopy(evidence)
    derive(evidence, DOCS)
    assert evidence == before


def test_counts_match_the_classifications_emitted():
    h = derive(_evidence(), DOCS)
    counts = h['derivation']['counts']
    assert counts['activities'] == 4
    assert counts['performed_operations'] == 2
    assert counts['standing'] == 1
    assert counts['out_of_scope'] == 1
