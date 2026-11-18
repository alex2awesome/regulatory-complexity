"""One isolated CLI transport. Domain validation/retry policy stays with callers.

Every call gets a new temporary directory. Raw outputs (including malformed JSON),
prompts, logs and status are retained; a failed retry cannot reuse an old response.
No calls are made on import. Tests replace subprocess.run with a fake backend.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time

from .manifest import digest, write


def cli_version():
    return subprocess.check_output(['codex', '--version'], text=True, timeout=30).strip()


def audit_tool_free_events(path):
    """Fail closed if a direct-estimation baseline invoked any tool.

    A temporary cwd/read-only sandbox alone does not prevent reading test
    files elsewhere. Restrict tools at launch AND retain/audit the event trace.
    This checks transport behavior, not whether the supplied prompt has labels.
    """
    completed = False
    count = 0
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        kind = event.get('type')
        count += 1
        if kind in {'item.started', 'item.updated', 'item.completed'}:
            item_type = event.get('item', {}).get('type')
            if item_type not in {'reasoning', 'agent_message'}:
                raise ValueError(f'Tool-free baseline used an unexpected item: {item_type}')
        elif kind == 'turn.completed':
            completed = True
        elif kind not in {'thread.started', 'turn.started'}:
            raise ValueError(f'Unexpected baseline event: {kind}')
    if not completed:
        raise ValueError('Tool-free baseline has no completed-turn receipt')
    return dict(event_count=count, observed_tool_calls=0, completed_turn=True)


def run_codex(prompt, schema, out, *, stem, model, reasoning='xhigh', timeout=2400,
              events=False, tool_free=False):
    """Return the raw final message; do not silently repair or parse its contents."""
    if not stem or Path(stem).name != stem or stem in {'.', '..'}:
        raise ValueError('Attempt stem must be a plain filename')
    if timeout <= 0:
        raise ValueError('Timeout must be positive')
    events = events or tool_free
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paths = {kind: out / (stem + suffix) for kind, suffix in {
        'prompt': '.prompt.txt', 'response': '.raw.txt', 'status': '.transport.json',
        'log': '.stderr.log' if events else '.log', 'events': '.events.jsonl'}.items()}
    if any(path.exists() for path in paths.values()):
        raise ValueError('Preserve previous attempt artifacts; choose a fresh stem')
    with paths['prompt'].open('x') as stream:
        stream.write(prompt)
    started = time.monotonic()
    status = dict(schema_version='codex-transport/1', status='running',
        started_utc=datetime.now(timezone.utc).isoformat(), model=model, reasoning=reasoning,
        timeout_seconds=timeout, prompt_sha256=digest(prompt),
        source_sha256=digest(Path(__file__).read_bytes()),
        working_directory='isolated temporary directory', json_events=events,
        # The transport has not inspected prompt contents or proven absence of tools.
        hidden_truth_read=None, source_only_event_audit_performed=False,
        tool_free_requested=tool_free)
    write(paths['status'], status)
    try:
        status['cli_version'] = cli_version()
        with tempfile.TemporaryDirectory(prefix='rc-codex-') as isolated:
            schema_path, response = Path(isolated) / 'schema.json', Path(isolated) / 'response.json'
            write(schema_path, schema)
            status['schema_sha256'] = digest(schema_path.read_bytes())
            command = ['codex', 'exec', '--sandbox', 'read-only', '--ephemeral',
                '--skip-git-repo-check', '--ignore-user-config', '--color', 'never',
                '-C', isolated, '-m', model, '-c', f'model_reasoning_effort="{reasoning}"',
                '--output-schema', str(schema_path), '-o', str(response), '-']
            if events:
                command.insert(2, '--json')
            if tool_free:
                # Documented shell/web/app/agent controls plus installed CLI
                # feature flags. Never weaken the filesystem sandbox. Event
                # auditing below also catches an unexpected remaining tool.
                # https://learn.chatgpt.com/docs/config-file/config-reference
                overrides = [
                    'features.shell_tool=false', 'features.unified_exec=false',
                    'features.apps=false', 'agents.enabled=false',
                    'web_search="disabled"', 'features.browser_use=false',
                    'features.browser_use_external=false',
                    'features.in_app_browser=false', 'features.skill_search=false',
                    'features.skip_host_skill_discovery=true',
                    'suppress_unstable_features_warning=true',
                    'project_doc_max_bytes=0',
                ]
                command[-1:-1] = [part for value in overrides for part in ('-c', value)]
                status['tool_free_config_overrides'] = overrides
            try:
                with paths['log'].open('x') as log:
                    if events:
                        with paths['events'].open('x') as stream:
                            result = subprocess.run(command, input=prompt, text=True, stdout=stream,
                                stderr=log, cwd=isolated, timeout=timeout)
                    else:
                        result = subprocess.run(command, input=prompt, text=True, stdout=log,
                            stderr=log, cwd=isolated, timeout=timeout)
            finally:
                if response.exists():
                    paths['response'].write_bytes(response.read_bytes())
                    status['response_sha256'] = digest(response.read_bytes())
            status['returncode'] = result.returncode
            if result.returncode or not response.exists():
                raise RuntimeError(f'Codex failed or produced no response; inspect {paths["log"]}')
            if tool_free:
                status['tool_event_audit'] = audit_tool_free_events(paths['events'])
                status['source_only_event_audit_performed'] = True
            raw = response.read_text()
        status['status'] = 'completed'
        return raw
    except Exception as error:
        status.update(status='failed', error_type=type(error).__name__)
        raise
    finally:
        status.update(completed_utc=datetime.now(timezone.utc).isoformat(),
                      seconds=time.monotonic() - started)
        write(paths['status'], status)
