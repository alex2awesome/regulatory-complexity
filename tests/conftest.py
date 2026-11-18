"""Offline shared fixtures. No paid backend is needed for infrastructure tests."""
from collections import deque
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from procbench_fixtures import data_fixture


@pytest.fixture
def visit_data():
    return data_fixture()


@pytest.fixture
def fake_codex(monkeypatch):
    from pipeline.procbench.infra import codex_runner

    class FakeCodex:
        def __init__(self):
            self.responses, self.calls = deque(), []

        def push(self, answer=None, *, raw=None, returncode=0, timeout=False, events=None):
            self.responses.append(dict(raw=json.dumps(answer) if raw is None and answer is not None else raw,
                returncode=returncode, timeout=timeout, events=events))

        def __call__(self, command, *, input, text, stdout, stderr, cwd, timeout):
            assert command[:2] == ['codex', 'exec']
            assert command[command.index('--sandbox') + 1] == 'read-only'
            assert all(flag in command for flag in ('--ephemeral', '--skip-git-repo-check', '--ignore-user-config'))
            assert Path(cwd) != Path.cwd()
            response = Path(command[command.index('-o') + 1])
            assert response.parent == Path(cwd) and not response.exists()
            schema = Path(command[command.index('--output-schema') + 1])
            assert {p.name for p in Path(cwd).iterdir()} == {'schema.json'}
            self.calls.append(dict(command=command, prompt=input, schema=json.loads(schema.read_text()),
                                   cwd=str(cwd), timeout=timeout))
            if not self.responses:
                raise AssertionError('Unexpected Codex call; no canned response remains')
            item = self.responses.popleft()
            if item['raw'] is not None:
                response.write_text(item['raw'])
            if '--json' in command:
                events = item['events'] if item['events'] is not None else [
                    dict(type='turn.started'),
                    dict(type='item.completed', item=dict(type='agent_message', text=item['raw'])),
                    dict(type='turn.completed')]
                stdout.write('\n'.join(json.dumps(e) for e in events))
            else:
                stdout.write('fake backend log\n')
            stderr.write('fake stderr\n')
            if item['timeout']:
                raise subprocess.TimeoutExpired(command, timeout)
            return SimpleNamespace(returncode=item['returncode'])

    fake = FakeCodex()
    monkeypatch.setattr(codex_runner.subprocess, 'run', fake)
    monkeypatch.setattr(codex_runner, 'cli_version', lambda: 'fake-codex/1')
    return fake
