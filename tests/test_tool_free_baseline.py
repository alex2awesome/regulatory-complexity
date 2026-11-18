import json

import pytest

from pipeline.procbench.infra.codex_runner import audit_tool_free_events


def test_direct_baseline_event_trace_is_accepted(tmp_path):
    p = tmp_path / 'events.jsonl'
    events = [dict(type='thread.started'), dict(type='turn.started'),
              dict(type='item.completed', item=dict(type='reasoning')),
              dict(type='item.completed', item=dict(type='agent_message')),
              dict(type='turn.completed')]
    p.write_text(''.join(json.dumps(x) + '\n' for x in events))
    assert audit_tool_free_events(p)['observed_tool_calls'] == 0


@pytest.mark.parametrize('kind', ['command_execution', 'mcp_tool_call', 'web_search',
                                  'file_change', 'future_unknown_tool'])
def test_any_tool_or_unknown_item_fails_closed(tmp_path, kind):
    p = tmp_path / 'events.jsonl'
    p.write_text(json.dumps(dict(type='item.completed', item=dict(type=kind))) + '\n')
    with pytest.raises(ValueError, match='unexpected item'):
        audit_tool_free_events(p)


def test_incomplete_baseline_trace_is_not_a_receipt(tmp_path):
    p = tmp_path / 'events.jsonl'
    p.write_text(json.dumps(dict(type='turn.started')) + '\n')
    with pytest.raises(ValueError, match='completed-turn'):
        audit_tool_free_events(p)
