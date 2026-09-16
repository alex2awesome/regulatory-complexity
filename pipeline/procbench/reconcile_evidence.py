"""Quote-checked Codex interpretation with content-addressed, replayable artifacts.

No inference or scoring occurs here. Inputs are public Markdown documents ONLY.
The CLI runs in an empty temporary working directory, never inside this repo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import pathlib
import subprocess
import tempfile
import time

from .evidence_contract import SCHEMA, validate

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROMPT = pathlib.Path(__file__).parent / "prompts/reconcile_evidence_v2.md"


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def public_documents(artifacts, program, index=None):
    """Do not open tasks/specs/verification/gold files, even to select inputs."""
    root = pathlib.Path(artifacts)
    if index:
        ids = [d["id"] for d in json.loads(pathlib.Path(index).read_text())]
    else:
        statute = program.split("__")[-1]
        ids = sorted(p.stem for p in root.glob(f"{program}__*.md"))
        ids += [p.stem for p in sorted(root.glob(f"{statute}__*.md"))]
    if not ids:
        raise ValueError(f"No public documents for {program}")
    return [{"id": i, "text": (root / f"{i}.md").read_text()} for i in dict.fromkeys(ids)]


def interpret(documents, program, out, model="gpt-6-astra", reasoning="xhigh", timeout=2400):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    prompt = (PROMPT.read_text() + "\nProgram ID: " + program + "\n\n" +
              "\n\n".join(f"DOCUMENT doc_id={d['id']}\n{d['text']}" for d in documents))
    inputs = {"documents": documents, "program_id": program}
    signature = digest(json.dumps({"inputs": inputs, "prompt": prompt, "schema": SCHEMA,
                                   "model": model, "reasoning": reasoning}, sort_keys=True))
    target = out / "evidence.json"
    if target.exists():
        manifest = json.loads((out / "manifest.json").read_text())
        if manifest.get("input_signature") != signature:
            raise ValueError("Cache differs from requested inputs/config; choose a fresh --out")
        return validate(json.loads(target.read_text()), documents)
    write(out / "inputs.json", inputs)
    write(out / "schema.json", SCHEMA)
    (out / "prompt.txt").write_text(prompt)
    cli_version = subprocess.check_output(["codex", "--version"], text=True).strip()
    attempts = []
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="rc-evidence-") as isolated:
        # Schema and final output are the only files the CLI needs. No truth paths.
        schema_path = pathlib.Path(isolated) / "schema.json"
        write(schema_path, SCHEMA)
        for attempt in range(3):
            response_path = pathlib.Path(isolated) / "response.json"
            command = ["codex", "exec", "--sandbox", "read-only", "--ephemeral",
                       "--skip-git-repo-check", "--ignore-user-config", "--color", "never",
                       "-C", isolated, "-m", model,
                       "-c", f'model_reasoning_effort="{reasoning}"',
                       "--output-schema", str(schema_path), "-o", str(response_path), "-"]
            log_path = out / f"attempt_{attempt}.log"
            with log_path.open('w') as log:
                with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=log, text=True, cwd=isolated) as process:
                    try:
                        process.communicate(prompt, timeout=timeout)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                        raise
            if process.returncode or not response_path.exists():
                raise RuntimeError(f"Codex failed ({process.returncode}): {log_path.read_text()[-1500:]}")
            raw = response_path.read_text()
            (out / f"attempt_{attempt}.json").write_text(raw)
            try:
                evidence = validate(json.loads(raw), documents)
                if evidence["program_id"] != program:
                    raise ValueError("program ID changed")
                break
            except (ValueError, json.JSONDecodeError) as error:
                attempts.append(str(error))
                prompt += ("\n\nYour previous output failed validation. Return the complete corrected "
                           "object. Errors:\n" + str(error) + "\nPrevious output:\n" + raw)
        else:
            raise ValueError("Evidence validation failed after repairs: " + attempts[-1])
    write(target, evidence)
    write(out / "manifest.json", {"input_signature": signature, "model": model,
          "reasoning": reasoning, "cli_version": cli_version,
          "created_utc": datetime.now(timezone.utc).isoformat(),
          "seconds": time.monotonic() - start, "validation_repairs": attempts,
          "evidence_sha256": digest(target.read_bytes()),
          "hidden_truth_read": False, "working_directory": "isolated temporary directory",
          "prompt_sha256": digest(PROMPT.read_bytes())})
    return evidence


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--program", default="J1__S03")
    ap.add_argument("--artifacts", default="benchmark/synth/worlds/W1/artifacts")
    ap.add_argument("--index")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt-6-astra")
    ap.add_argument("--reasoning", default="xhigh")
    ap.add_argument("--probe", action="store_true", help="Small, logged backend connectivity check; no documents")
    ap.add_argument("--from-attempt", help="Validate/import a saved LLM response; requires --source-cache")
    ap.add_argument("--source-cache", help="Original run with inputs, prompt and schema for --from-attempt")
    args = ap.parse_args(argv)
    if args.from_attempt:
        if not args.source_cache:
            ap.error('--from-attempt requires --source-cache')
        source, out = pathlib.Path(args.source_cache), pathlib.Path(args.out)
        if (out / 'evidence.json').exists():
            raise ValueError('Preserving existing evidence; choose a fresh output directory')
        inputs = json.loads((source / 'inputs.json').read_text())
        response = pathlib.Path(args.from_attempt)
        evidence = validate(json.loads(response.read_text()), inputs['documents'])
        write(out / 'evidence.json', evidence)
        for name in ('inputs.json', 'schema.json', 'prompt.txt'):
            (out / name).write_bytes((source / name).read_bytes())
        signature = digest(json.dumps({'inputs': inputs, 'prompt': (source / 'prompt.txt').read_text(),
            'schema': json.loads((source / 'schema.json').read_text()),
            'model': args.model, 'reasoning': args.reasoning}, sort_keys=True))
        write(out / 'manifest.json', {'model': args.model, 'reasoning': args.reasoning, 'input_signature': signature,
            'imported_from': str(response), 'response_sha256': digest(response.read_bytes()),
            'prompt_sha256': digest((source / 'prompt.txt').read_bytes()),
            'evidence_sha256': digest((out / 'evidence.json').read_bytes()),
            'hidden_truth_read': False, 'validation': 'schema, references and every quote checked',
            'note': 'Original LLM response accepted after fixing overstrict self-rework and decision-phase validation; no semantic field edited'})
        print(f'Validated/imported {len(evidence["measurements"])} measurements -> {out}')
        return
    if args.probe:
        out = pathlib.Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='rc-backend-probe-') as isolated:
            schema = pathlib.Path(isolated) / 'schema.json'
            write(schema, {"type": "object", "properties": {"ok": {"type": "boolean"}},
                           "required": ["ok"], "additionalProperties": False})
            cmd = ['codex', 'exec', '--sandbox', 'read-only', '--ephemeral', '--skip-git-repo-check',
                   '--ignore-user-config', '--color', 'never', '-C', isolated, '-m', args.model,
                   '-c', 'model_reasoning_effort="low"', '--output-schema', str(schema),
                   '-o', str(out.resolve() / 'response.json'), '-']
            with (out / 'probe.log').open('w') as log:
                result = subprocess.run(cmd, input='Return {"ok":true}. Do not use tools or read files.',
                                        text=True, stdout=log, stderr=log, cwd=isolated, timeout=120)
            print('probe exit', result.returncode)
        return
    docs = public_documents(args.artifacts, args.program, args.index)
    print(f"Interpreting {len(docs)} public documents ({sum(len(d['text']) for d in docs)} chars)", flush=True)
    e = interpret(docs, args.program, args.out, args.model, args.reasoning)
    print(json.dumps({"activities": len(e["activities"]), "measurements": len(e["measurements"]),
                      "actors": len(e["actors"]), "out": args.out}))


if __name__ == "__main__":
    main()
