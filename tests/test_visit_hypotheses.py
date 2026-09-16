import copy
import json

import pytest

from pipeline.procbench.audit_visit_hypotheses import (
    MANAGED_APPROVAL_NOTICE, VERSION, check_source_only_events, validate_hypotheses)
from test_compile_visit_durations import inputs


def hypothesis_inputs():
    e, visit, semantic, docs, policy = inputs()
    row = visit['measurements'][0]
    complete = copy.deepcopy(row['operators'][0])
    complete['visits'] = 'one_unspecified'
    row['identification'] = 'unresolved'
    row['operators'][0].update(basis='unknown', start='unknown', end='unknown', visits='unknown')
    h = dict(id='cycle', parent_operator=0, operator=complete,
             assumptions=['Assume the quoted duration covers one complete cycle.'],
             evidence=copy.deepcopy(row['evidence']))
    audit = dict(schema_version=VERSION, program_id=e['program_id'], measurements=[dict(
        measurement_id='m1', disposition='hypotheses', hypotheses=[h],
        residual_explanation='It may instead describe a partial interval.', notes='')], unresolved=[])
    return e, visit, semantic, docs, policy, audit


def test_hypotheses_are_valid_but_do_not_modify_source_facts():
    e, v, s, d, p, a = hypothesis_inputs()
    original = copy.deepcopy((e, v))
    assert validate_hypotheses(a, e, v, d) == a
    assert (e, v) == original
    assert v['measurements'][0]['operators'][0]['basis'] == 'unknown'


@pytest.mark.parametrize('field,value', [('activity_ids', ['file']), ('censoring', 'right')])
def test_cannot_override_known_mapping_or_censoring(field, value):
    e, v, s, d, p, a = hypothesis_inputs()
    a['measurements'][0]['hypotheses'][0]['operator'][field] = value
    with pytest.raises(ValueError, match='known parent field'):
        validate_hypotheses(a, e, v, d)


def test_known_partial_boundary_stays_partial():
    e, v, s, d, p, a = hypothesis_inputs()
    v['measurements'][0]['operators'][0]['end'] = 'other_milestone'
    with pytest.raises(ValueError, match='known parent field: end'):
        validate_hypotheses(a, e, v, d)


def test_no_supported_mapping_and_no_assumption_are_rejected():
    e, v, s, d, p, a = hypothesis_inputs()
    v['measurements'][0]['activity_mapping'] = 'unresolved'
    with pytest.raises(ValueError, match='activity mappings'):
        validate_hypotheses(a, e, v, d)
    v['measurements'][0]['activity_mapping'] = 'supported'
    a['measurements'][0]['hypotheses'][0]['assumptions'] = []
    with pytest.raises(ValueError, match='assumptions'):
        validate_hypotheses(a, e, v, d)


def test_fully_specified_original_alternative_cannot_disappear():
    e, v, s, d, p, a = hypothesis_inputs()
    op = copy.deepcopy(a['measurements'][0]['hypotheses'][0]['operator'])
    op.update(basis='sum_visit_cycles', visits='all_in_completed_case',
              start='first_activity_start', end='last_activity_end')
    v['measurements'][0]['operators'].append(op)
    with pytest.raises(ValueError, match='discarded an identified'):
        validate_hypotheses(a, e, v, d)


def test_nonverbatim_support_and_duplicate_candidates_fail():
    e, v, s, d, p, a = hypothesis_inputs()
    row = a['measurements'][0]
    row['hypotheses'][0]['evidence'][0]['quote'] = 'Made up quotation'
    with pytest.raises(ValueError, match='Nonverbatim'):
        validate_hypotheses(a, e, v, d)
    row['hypotheses'][0]['evidence'][0]['quote'] = 'Evidence'
    duplicate = copy.deepcopy(row['hypotheses'][0])
    duplicate['id'] = 'another_name'
    row['hypotheses'].append(duplicate)
    with pytest.raises(ValueError, match='Duplicate semantic'):
        validate_hypotheses(a, e, v, d)


def test_incomplete_coverage_and_empty_residual_fail():
    e, v, s, d, p, a = hypothesis_inputs()
    a['measurements'][0]['residual_explanation'] = ''
    with pytest.raises(ValueError, match='Unmodeled'):
        validate_hypotheses(a, e, v, d)
    a['measurements'] = []
    with pytest.raises(ValueError, match='every eligible'):
        validate_hypotheses(a, e, v, d)


def test_event_audit_accepts_output_only_and_rejects_tools_or_failed_turn(tmp_path):
    path = tmp_path / 'events.jsonl'
    events = [dict(type='thread.started', thread_id='t'), dict(type='turn.started'),
              dict(type='item.completed', item=dict(type='agent_message', text='{"ok":true}')),
              dict(type='turn.completed')]
    path.write_text('\n'.join(json.dumps(e) for e in events))
    assert check_source_only_events(path)['tool_events'] == 0
    for kind in ('command_execution', 'web_search', 'mcp_tool_call', 'file_change', 'unknown_tool'):
        changed = events + [dict(type='item.started', item=dict(type=kind))]
        path.write_text('\n'.join(json.dumps(e) for e in changed))
        with pytest.raises(ValueError, match='used a tool'):
            check_source_only_events(path)
    path.write_text('\n'.join(json.dumps(e) for e in events[:-1]))
    with pytest.raises(ValueError, match='did not complete'):
        check_source_only_events(path)
    path.write_text(json.dumps(dict(type='turn.failed')))
    with pytest.raises(ValueError, match='Unexpected/failed'):
        check_source_only_events(path)


def test_only_exact_pre_turn_managed_approval_notice_is_allowed(tmp_path):
    path = tmp_path/'events.jsonl'
    notice = dict(type='item.completed', item=dict(type='error', message=MANAGED_APPROVAL_NOTICE))
    start = dict(type='turn.started')
    rest = [dict(type='item.completed', item=dict(type='agent_message', text='{}')),
            dict(type='turn.completed')]
    path.write_text('\n'.join(json.dumps(e) for e in [notice, start, *rest]))
    result = check_source_only_events(path)
    assert result['managed_policy_notices'] == [MANAGED_APPROVAL_NOTICE]
    assert result['tool_events'] == 0
    path.write_text('\n'.join(json.dumps(e) for e in [start, notice, *rest]))
    with pytest.raises(ValueError, match='used a tool'):
        check_source_only_events(path)
    notice['item']['message'] = 'A different error must not be suppressed'
    path.write_text('\n'.join(json.dumps(e) for e in [notice, start, *rest]))
    with pytest.raises(ValueError, match='used a tool'):
        check_source_only_events(path)
