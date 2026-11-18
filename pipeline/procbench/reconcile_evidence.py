"""Quote-checked Codex interpretation with content-addressed, replayable artifacts.

No inference or scoring occurs here. Inputs are public Markdown documents ONLY.
The CLI runs in an empty temporary working directory, never inside this repo.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import pathlib
import time

from .evidence_contract import SCHEMA, validate
from .infra.codex_runner import cli_version, run_codex
# Backward-compatible exports for old callers; infrastructure owns these now.
from .infra.manifest import RunManifest, digest, write

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROMPT = pathlib.Path(__file__).parent / "prompts/reconcile_evidence_v2.md"


def public_documents(artifacts, program, index=None):
    """Do not open tasks/specs/verification/gold files, even to select inputs."""
    root = pathlib.Path(artifacts)
    expected = {}
    if index:
        selection = json.loads(pathlib.Path(index).read_text())
        if isinstance(selection, list):
            ids = [d['id'] for d in selection]
        elif selection.get('schema_version') == 'artifact-only-index/1':
            if program not in selection.get('programs', {}):
                raise ValueError('Source-only index has no explicit membership for ' + program)
            ids = selection['programs'][program]
            expected = {d['document_id']: d['sha256'] for d in selection['documents']}
            if len(expected) != len(selection['documents']) or not set(ids) <= expected.keys():
                raise ValueError('Invalid source-only index identities')
        else:
            raise ValueError('Unsupported public document index')
    else:
        statute = program.split("__")[-1]
        ids = sorted(p.stem for p in root.glob(f"{program}__*.md"))
        ids += [p.stem for p in sorted(root.glob(f"{statute}__*.md"))]
    if not ids:
        raise ValueError(f"No public documents for {program}")
    documents = []
    for ident in dict.fromkeys(ids):
        if not isinstance(ident, str) or pathlib.Path(ident).name != ident or ident in {'.', '..'}:
            raise ValueError('Document identities must be plain filenames')
        path = root / (ident + '.md')
        if root.resolve() not in path.resolve().parents:
            raise ValueError('Document escapes the source-only directory')
        raw = path.read_bytes()
        if expected and digest(raw) != expected[ident]:
            raise ValueError('Frozen source hash mismatch: ' + ident)
        documents.append(dict(id=ident, text=raw.decode()))
    return documents


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
        if manifest.get('evidence_sha256') != digest(target.read_bytes()):
            raise ValueError('Cached evidence changed since validation; choose a fresh --out')
        return validate(json.loads(target.read_text()), documents)
    if any(out.iterdir()):
        raise ValueError('Preserve unfinished extraction artifacts; choose a fresh --out')
    write(out / "inputs.json", inputs)
    write(out / "schema.json", SCHEMA)
    (out / "prompt.txt").write_text(prompt)
    version = cli_version()
    attempts = []
    start = time.monotonic()
    record = RunManifest(out, {}, operation='evidence.reconcile',
        inputs=[out/name for name in ('inputs.json', 'schema.json', 'prompt.txt')],
        config=dict(model=model, reasoning=reasoning, timeout=timeout), seeds={}, hidden_truth_read=False,
        source_root=pathlib.Path(__file__).parent,
        sources=['reconcile_evidence.py', 'prompts/reconcile_evidence_v2.md'])
    for attempt in range(3):
        raw = run_codex(prompt, SCHEMA, out, stem=f'attempt_{attempt}',
                        model=model, reasoning=reasoning, timeout=timeout)
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
    record.complete(**{"input_signature": signature, "model": model,
          "reasoning": reasoning, "cli_version": version,
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
        if out.exists():
            raise ValueError('Preserving existing evidence; choose a fresh output directory')
        inputs = json.loads((source / 'inputs.json').read_text())
        response = pathlib.Path(args.from_attempt)
        evidence = validate(json.loads(response.read_text()), inputs['documents'])
        record = RunManifest(out, {}, operation='evidence.revalidate_import',
            inputs=[response, *(source/name for name in ('inputs.json', 'schema.json', 'prompt.txt'))],
            config=dict(model_requested=args.model, reasoning_requested=args.reasoning), seeds={},
            hidden_truth_read=False, source_root=pathlib.Path(__file__).parent,
            sources=['reconcile_evidence.py', 'prompts/reconcile_evidence_v2.md'])
        write(out / 'evidence.json', evidence)
        for name in ('inputs.json', 'schema.json', 'prompt.txt'):
            (out / name).write_bytes((source / name).read_bytes())
        signature = digest(json.dumps({'inputs': inputs, 'prompt': (source / 'prompt.txt').read_text(),
            'schema': json.loads((source / 'schema.json').read_text()),
            'model': args.model, 'reasoning': args.reasoning}, sort_keys=True))
        record.complete(**{'model': args.model, 'reasoning': args.reasoning, 'input_signature': signature,
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
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}},
                  "required": ["ok"], "additionalProperties": False}
        raw = run_codex('Return {"ok":true}. Do not use tools or read files.', schema, out,
                        stem='probe', model=args.model, reasoning='low', timeout=120)
        (out / 'response.json').write_text(raw)
        print('probe exit', 0)
        return
    docs = public_documents(args.artifacts, args.program, args.index)
    print(f"Interpreting {len(docs)} public documents ({sum(len(d['text']) for d in docs)} chars)", flush=True)
    e = interpret(docs, args.program, args.out, args.model, args.reasoning)
    print(json.dumps({"activities": len(e["activities"]), "measurements": len(e["measurements"]),
                      "actors": len(e["actors"]), "out": args.out}))


if __name__ == "__main__":
    main()
