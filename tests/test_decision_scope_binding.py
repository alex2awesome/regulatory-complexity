import copy

import numpy as np
import pytest

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy
from pipeline.procbench.compile_visit_durations import compile_durations
from pipeline.procbench.decision_scope_binding import bind_decision_contexts
from test_bayes_hierarchy import add_context, measurement
from test_compile_visit_durations import inputs


def scoped_inputs():
    e, v, s, d, p = inputs()
    e['measurements'] = [measurement(None, 'process', 12.)]
    add_context(e, 'm1', decision_activity_id='decide')
    v['measurements'][0]['operators'] = [dict(basis='whole_case_clock', activity_ids=[],
        start='process_start', end='initial_decision', visits='not_applicable', censoring='none', notes='')]
    p.update(retain_unsupported=True, residual_reference=dict(median_days=7., log_scale=3.))
    operations = [dict(id=a, actor_id='agency', actor_role='agency', task_type='decision',
        markers=['decision'] if a != 'file' else []) for a in ('file', 'decide', 'deny')]
    paths = [dict(id=a, probability_weight=.5, blocks=[dict(id='b', operations=['file', a])])
             for a in ('decide', 'deny')]
    program = dict(id=e['program_id'], routes=[dict(id='inventory', prior_weight=1.,
        operations=operations, paths=paths)], case_path_scope={'c1': ['decide']})
    return e, v, s, d, p, program


def test_only_explicit_validated_structure_restores_a_decision_clock():
    e, v, s, d, p, program = scoped_inputs()
    before = copy.deepcopy((e, v, s, p, program))
    old = compile_durations(e, v, s, d, p)
    assert old['observations'][0]['statistic'] == 'report_only'
    compiled = compile_durations(e, v, s, d, p, structural_context={'programs': [program]})
    row = compiled['observations'][0]
    assert row['case_id'] == 'c1' and row['statistic'] == 'individual'
    assert row['operators'] == v['measurements'][0]['operators']
    assert row['operator_weights'] == [1.]
    assert (row['lower'], row['upper']) == (11.5, 12.5)
    assert row['decision_context_binding']['allowed_paths'] == ['decide']
    assert (e, v, s, p, program) == before
    payload = dict(programs=[dict(program, observations=compiled['observations'])])
    model = VisitHierarchy(payload, Config(population_size=16, modeled_channels=('elapsed',)))
    assert np.isfinite(model.log_likelihood(np.zeros(model.layout.size), [0]))
    assert model.programs[0]['case_path_scope'] == {'c1': ['decide']}


@pytest.mark.parametrize('extra', [dict(required_activity_ids=['review']),
    dict(excluded_activity_ids=['review']), dict(clock_start_after_activity_ids=['file']),
    dict(segment_mode='performed_operations')])
def test_other_constraints_are_not_discharged(extra):
    e, v, s, d, p, program = scoped_inputs()
    e['observation_contexts'][0].update(extra)
    result = compile_durations(e, v, s, d, p, structural_context=program)
    assert result['decision_context_bindings'] == {}
    assert result['observations'][0]['statistic'] == 'report_only'


def test_hypothetical_case_is_not_promoted_to_an_observation():
    e, v, s, d, p, program = scoped_inputs()
    e['observation_contexts'][0]['temporal_scope'] = 'hypothetical'
    # The existing eligibility contract excludes hypothetical elapsed claims.
    v['measurements'] = []; s['measurements'] = []
    result = compile_durations(e, v, s, d, p, structural_context=program)
    assert result['decision_context_bindings'] == {}
    assert result['observations'] == []


@pytest.mark.parametrize('statistic', ['median', 'mean', 'typical', 'estimate', 'target', 'statutory_cap'])
def test_nonindividual_source_claim_is_not_bound_by_a_case_id(statistic):
    e, _, _, _, _, program = scoped_inputs()
    e['measurements'][0]['statistic'] = statistic
    assert bind_decision_contexts(e, program) == {}


@pytest.mark.parametrize('mutation', ['remove_scope', 'wrong_path', 'remove_marker', 'repeat_decision',
                                     'missing_inventory_outcome', 'extra_valid_path'])
def test_unproved_or_narrowed_structural_scopes_are_rejected(mutation):
    e, v, s, d, p, program = scoped_inputs()
    route = program['routes'][0]
    if mutation == 'remove_scope':
        program['case_path_scope'] = {}
    elif mutation == 'wrong_path':
        program['case_path_scope']['c1'] = ['deny']
    elif mutation == 'remove_marker':
        route['operations'][1]['markers'] = []
    elif mutation == 'repeat_decision':
        route['paths'][0]['blocks'][0]['repeat_key'] = 'correction'
    elif mutation == 'missing_inventory_outcome':
        other = copy.deepcopy(route); other['id'] = 'other'
        other['paths'] = [other['paths'][1]]
        program['routes'].append(other)
    elif mutation == 'extra_valid_path':
        other = copy.deepcopy(route['paths'][0]); other['id'] = 'decide_with_optional_step'
        route['paths'].append(other)
    with pytest.raises(ValueError):
        compile_durations(e, v, s, d, p, structural_context=program)


def test_fit_rejects_restored_observation_when_scope_or_structure_changes():
    e, v, s, d, p, program = scoped_inputs()
    result = compile_durations(e, v, s, d, p, structural_context=program)
    program['observations'] = result['observations']
    for field in ('case_path_scope', 'routes'):
        changed = copy.deepcopy(program)
        if field == 'case_path_scope':
            changed[field] = {}
        else:
            changed[field][0]['paths'][0]['probability_weight'] = .8
        with pytest.raises(ValueError, match='exact reviewed structural context'):
            VisitHierarchy(dict(programs=[changed]), Config(population_size=16))


def test_conflicting_quoted_outcomes_are_not_resolved_by_structure():
    e, v, s, d, p, program = scoped_inputs()
    e['measurements'].append(measurement(None, 'process', 15., ident='m2'))
    add_context(e, 'm2', decision_activity_id='deny')
    with pytest.raises(ValueError, match='Conflicting source decision'):
        bind_decision_contexts(e, program)


def test_context_does_not_remove_other_operator_or_reporting_holds():
    e, v, s, d, p, program = scoped_inputs()
    v['measurements'][0]['operators'][0]['start'] = 'unknown'
    result = compile_durations(e, v, s, d, p, structural_context=program)
    assert result['decision_context_bindings']
    assert result['observations'][0]['statistic'] == 'report_only'
    assert 'decision_context_binding' not in result['observations'][0]
