"""Model clients. One call = one reply holding a JSON object with tool calls.

The CLI clients have no native tool calling; the tool list is identical on every
backend and in every arm. Known limits, recorded per run: the codex CLI keeps its
own system prompt (ours is prepended to the user turn); the claude CLI runs with
our system prompt in place of its default. Neither accepts a sampling seed.
"""
import json
from pathlib import Path
import re
import subprocess
import tempfile


def reply_schema(tools):
    """Flat strict schema: every tool's argument is a nullable field of a call."""
    types = {}
    for t in tools.values():
        types.update(t['args'])
    props = {'tool': {'type': 'string', 'enum': list(tools)}}
    for name, kind in types.items():
        props[name] = ({'type': ['array', 'null'], 'items': {'type': 'string'}} if kind == 'array'
                       else {'type': [kind, 'null']})
    call = {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}
    return {'type': 'object', 'additionalProperties': False, 'required': ['reasoning', 'calls'],
            'properties': {'reasoning': {'type': 'string'}, 'calls': {'type': 'array', 'items': call}}}


def extract_json(text):
    text = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.S)
    if m:
        text = m.group(1)
    start = text.find('{')
    if start < 0:
        raise ValueError('no JSON object in reply')
    return json.JSONDecoder().raw_decode(text[start:])[0]


class ScriptedModel:
    """Replays canned replies (tests). Each reply is a dict or a raw string."""
    name = 'scripted'

    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def call(self, system, messages, schema, stem, out):
        self.calls.append(dict(system=system, messages=messages))
        r = self.replies.pop(0)
        return dict(text=r if isinstance(r, str) else json.dumps(r), cost_usd=None)


def flatten(system, messages):
    parts = [system] if system else []
    for m in messages:
        parts.append(('' if m['role'] == 'user' else 'YOUR EARLIER REPLY:\n') + m['content'])
    return '\n\n'.join(parts)


class CodexCLI:
    def __init__(self, model, reasoning='medium', timeout=600):
        self.model, self.reasoning, self.timeout = model, reasoning, timeout
        self.name = f'codex:{model}'

    def call(self, system, messages, schema, stem, out):
        from pipeline.procbench.infra.codex_runner import run_codex
        raw = run_codex(flatten(system, messages), schema, Path(out), stem=stem, model=self.model,
                        reasoning=self.reasoning, timeout=self.timeout, tool_free=True)
        return dict(text=raw, cost_usd=None)


class ClaudeCLI:
    def __init__(self, model, timeout=600):
        self.model, self.timeout = model, timeout
        self.name = f'claude:{model}'

    def call(self, system, messages, schema, stem, out):
        prompt = flatten('', messages)
        with tempfile.TemporaryDirectory(prefix='rulegap-claude-') as empty:
            r = subprocess.run(['claude', '-p', '--model', self.model, '--tools', '', '--no-session-persistence',
                '--disable-slash-commands', '--system-prompt', system, '--output-format', 'json'],
                input=prompt, capture_output=True, text=True, cwd=empty, timeout=self.timeout)
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{stem}.raw.json').write_text(r.stdout)
        if r.returncode:
            (out / f'{stem}.stderr.log').write_text(r.stderr)
            raise RuntimeError(f'claude CLI failed ({r.returncode}); see {out / (stem + ".stderr.log")}')
        res = json.loads(r.stdout)
        return dict(text=res['result'], cost_usd=res.get('total_cost_usd'))


def get_model(name):
    backend, _, model = name.partition(':')
    if backend == 'codex':
        return CodexCLI(model)
    if backend == 'claude':
        return ClaudeCLI(model)
    raise ValueError(f'unknown backend {backend!r}; use codex:<model> or claude:<model>')
