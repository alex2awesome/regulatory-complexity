"""Public-only render/verify adapter for supported three-family pilot worlds.

This module prepares hash-bound renderer packets, ingests drafts, accepts an
independent verifier's hash-bound verdict, and releases only current passing
artifacts.  It does not select artifacts, read ``private/``, implement semantic
verification, or call an LLM from its CLI.

Usage (all destinations must be fresh)::

  python -m benchmark.synth.render.three_family_pilot prepare \
    --world benchmark/synth/worlds/THREE_FAMILY_PILOT_001 \
    --allowlist public_ids.txt --out runs/three_family_pilot_render_001
  # An authorized caller may pass pipeline.procbench.infra.codex_runner.run_codex
  # to invoke_with_transport(); the CLI intentionally has no render command.
  python -m benchmark.synth.render.three_family_pilot ingest \
    --run runs/three_family_pilot_render_001 --artifact-id ID --response response.json
  python -m benchmark.synth.render.three_family_pilot verdict \
    --run runs/three_family_pilot_render_001 --verdict independent_verdict.json
  python -m benchmark.synth.render.three_family_pilot release \
    --run runs/three_family_pilot_render_001 --out runs/three_family_pilot_release_001
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Callable

from .public_spec_revisions import apply_public_spec_revisions
from pipeline.procbench.infra.manifest import RunManifest, digest


ROOT = pathlib.Path(__file__).resolve().parents[3]
ADAPTER_SOURCE = "benchmark/synth/render/three_family_pilot.py"
MANIFEST_SOURCE = "pipeline/procbench/infra/manifest.py"
WORLD_ID = "THREE_FAMILY_PILOT_001"
SUPPORTED_WORLD_IDS = {"THREE_FAMILY_PILOT_001", "THREE_FAMILY_PILOT_002",
                       "THREE_FAMILY_PILOT_003"}

STYLE_BY_KIND = {
    "program_overview": "municipal_pages.md",
    "initial_application_guide": "forms.md",
    "renewal_guide": "forms.md",
    "interview_and_pickup_guide": "municipal_pages.md",
    "training_provider_page": "municipal_pages.md",
    "fee_schedule": "legal_text.md",
    "monthly_performance_table": "municipal_pages.md",
    "typical_time_faq": "municipal_pages.md",
    "forum_thread": "reddit_style.md",
    "news_summary": "news_and_forums.md",
    "application_guide": "forms.md",
    "expedited_service_guide": "municipal_pages.md",
    "interview_guide": "municipal_pages.md",
    "verification_checklist": "forms.md",
    "issuance_guide": "municipal_pages.md",
    "receipt_cohort_workbook": "municipal_pages.md",
    "completion_cohort_dashboard": "municipal_pages.md",
    "schema_change_notice": "staff_reports.md",
    "applicant_forum": "reddit_style.md",
    "fictional_state_framework": "legal_text.md",
    "training_provider_standard": "legal_text.md",
    "statewide_annual_report": "staff_reports.md",
    "fictional_policy_manual": "legal_text.md",
    "cohort_data_dictionary": "staff_reports.md",
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "artifacts": {
            "type": "array", "minItems": 1, "maxItems": 1,
            "items": {
                "type": "object",
                "properties": {"artifact_id": {"type": "string"}, "markdown": {"type": "string"}},
                "required": ["artifact_id", "markdown"], "additionalProperties": False,
            },
        }
    },
    "required": ["artifacts"], "additionalProperties": False,
}

FRONTMATTER_FIELDS = ("artifact_id", "url", "kind", "family", "jurisdiction_id", "publisher", "title")
ARTIFACT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BINDING_FIELDS = ("packet_sha256", "prompt_sha256", "spec_sha256", "context_sha256",
                  "style_sha256", "artifact_sha256")


def _read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _exclusive_json(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError("Preserve existing file: " + str(path))
    serialized = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(serialized)


def _exclusive_text(path: pathlib.Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)


def _public_root(world: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    canonical_world = world.resolve()
    public = canonical_world / "public"
    if public.is_symlink():
        raise ValueError("World public root must not be a symlink")
    if not public.is_dir() or public.resolve() != public:
        raise ValueError("World public root is missing or non-canonical")
    return canonical_world, public


def _public_path(world: pathlib.Path, relative: str) -> pathlib.Path:
    canonical_world, public = _public_root(world)
    rel = pathlib.Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Adapter input path is unsafe: " + relative)
    lexical = canonical_world / rel
    path = lexical.resolve()
    boundary = canonical_world / "BOUNDARY.md"
    if rel == pathlib.Path("BOUNDARY.md"):
        if lexical.is_symlink() or path != boundary:
            raise ValueError("Construction boundary must be a regular world-root file")
        return path
    if not lexical.is_relative_to(public) or not path.is_relative_to(public):
        raise ValueError("Adapter input is not public: " + str(path))
    return path


def _safe_artifact_id(value, *, where: str) -> str:
    if not isinstance(value, str) or not ARTIFACT_ID.fullmatch(value) or pathlib.Path(value).name != value:
        raise ValueError(f"Unsafe artifact ID in {where}: {value!r}")
    return value


def read_allowlist(path: pathlib.Path) -> list[str]:
    ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not ids:
        raise ValueError("Public artifact-ID allowlist is empty")
    duplicates = sorted({aid for aid in ids if ids.count(aid) > 1})
    if duplicates:
        raise ValueError("Duplicate artifact IDs in allowlist: " + ", ".join(duplicates))
    for aid in ids:
        _safe_artifact_id(aid, where="allowlist")
    return ids


def _load_public_specs(world: pathlib.Path) -> tuple[dict[str, dict], dict[str, pathlib.Path]]:
    specs, sources = {}, {}
    for family in ("ccw", "calfresh"):
        path = _public_path(world, f"public/render_specs/{family}.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            spec = json.loads(line)
            aid = _safe_artifact_id(spec.get("artifact_id"), where=str(path))
            if aid in specs:
                raise ValueError("Duplicate artifact ID in public specs: " + aid)
            specs[aid], sources[aid] = spec, path
    return specs, sources


def _prompt(packet: dict) -> str:
    rules = """You are an isolated synthetic-document renderer. Use only INPUT. Do not use
tools, browse, read files, or infer omitted facts. Render every claim in
spec.content_blocks and no additional process fact. Preserve values, units,
qualifiers, cohort definitions, suppression tokens, report gaps, endpoints, and
the stated fidelity; do not correct approximate or biased claims. Enforce every
renderer constraint. Never print claim IDs, construction instructions, fidelity
labels, internal jurisdiction IDs, or the world ID in the document body.

Return one complete Markdown document. Front matter must contain exactly these
semantic fields: artifact_id, url, kind, family, jurisdiction_id, publisher,
and title. Use null for a shared artifact's jurisdiction_id. Do not invent a
date. The body may use presentation boilerplate but no new process fact.
Return only schema-conforming JSON."""
    return rules + "\nINPUT:\n" + json.dumps(packet, ensure_ascii=False, sort_keys=True)


def prepare(world_dir: str | pathlib.Path, allowlist_path: str | pathlib.Path,
            out_dir: str | pathlib.Path, *, public_spec_revisions: str | pathlib.Path | None = None) -> dict:
    world, allowlist, out = pathlib.Path(world_dir), pathlib.Path(allowlist_path), pathlib.Path(out_dir)
    world_id = world.name
    if not world.is_dir() or world_id not in SUPPORTED_WORLD_IDS:
        raise ValueError("Expected a supported immutable world: " + ", ".join(sorted(SUPPORTED_WORLD_IDS)))
    if out.exists():
        raise ValueError("Fresh run destination required")
    _public_root(world)  # Reject a redirected public root before any world-public read.
    ids = read_allowlist(allowlist)
    specs, spec_sources = _load_public_specs(world)
    mismatched = sorted(aid for aid, spec in specs.items() if spec.get("world_id") != world_id)
    if mismatched:
        raise ValueError("Public spec world identity mismatch: " + ", ".join(mismatched))
    public_manifest = _read_json(_public_path(world, "public/artifact_manifest.json"))
    manifest_ids = [row.get("artifact_id") for row in public_manifest]
    if len(manifest_ids) != len(set(manifest_ids)):
        raise ValueError("Duplicate artifact ID in public artifact manifest")
    unknown = sorted(set(ids) - set(specs))
    if unknown:
        raise ValueError("Unknown artifact IDs: " + ", ".join(unknown))
    if not set(ids) <= set(manifest_ids):
        raise ValueError("Allowlist/spec IDs disagree with public artifact manifest")

    revision_inputs = set()
    if public_spec_revisions is not None:
        specs, revision_inputs = apply_public_spec_revisions(
            pathlib.Path(public_spec_revisions), world_id=world_id, specs=specs,
            selected_ids=ids, frontmatter_parser=_frontmatter,
        )

    boundary = _public_path(world, "BOUNDARY.md")
    input_paths = {allowlist.resolve(), boundary, _public_path(world, "public/artifact_manifest.json")}
    input_paths.update(revision_inputs)
    packets = {}
    for aid in ids:
        spec = specs[aid]
        style_name = STYLE_BY_KIND.get(spec.get("kind"))
        if not style_name:
            raise ValueError("No approved style mapping for kind: " + str(spec.get("kind")))
        style_path = (ROOT / "benchmark/synth/style" / style_name).resolve()
        if not style_path.is_file():
            raise ValueError("Missing style guide: " + str(style_path))
        context_path = None
        context = None
        jid = spec.get("jurisdiction_id")
        if jid:
            context_path = _public_path(world, f"public/render_context/{spec['family']}/{jid}.json")
            context = _read_json(context_path)
            if (context.get("jurisdiction_id") != jid or context.get("family") != spec.get("family") or
                    context.get("world_id") != world_id):
                raise ValueError("Context identity mismatch: " + aid)
        packet = {
            "schema_version": "three-family-render-packet/1",
            "boundary": boundary.read_text(encoding="utf-8"),
            "spec": spec, "context": context,
            "style": {"path": style_path.relative_to(ROOT).as_posix(),
                      "text": style_path.read_text(encoding="utf-8")},
            "private_inputs_provided": False,
            "ceiling_provided_to_renderer": False,
        }
        packets[aid] = packet
        input_paths.update({spec_sources[aid].resolve(), style_path})
        if context_path:
            input_paths.add(context_path.resolve())

    record = RunManifest(
        out, {"schema_version": "three-family-render-run/1", "world": world_id,
              "artifact_ids": ids, "artifact_count": len(ids),
              "semantic_verifier_implemented": False},
        operation="three_family_pilot.prepare_public_render_packets",
        inputs=sorted(input_paths), config={"artifact_ids": ids, "style_by_kind": STYLE_BY_KIND},
        seeds={}, hidden_truth_read=False, source_root=ROOT,
        sources=[ADAPTER_SOURCE, MANIFEST_SOURCE],
    )
    packet_records = {}
    for aid in ids:
        packet_path, prompt_path = out / "packets" / f"{aid}.json", out / "prompts" / f"{aid}.txt"
        _exclusive_json(packet_path, packets[aid])
        prompt = _prompt(packets[aid])
        _exclusive_text(prompt_path, prompt)
        spec, context = packets[aid]["spec"], packets[aid]["context"]
        packet_records[aid] = {
            "packet": str(packet_path), "packet_sha256": digest(packet_path.read_bytes()),
            "prompt": str(prompt_path), "prompt_sha256": digest(prompt),
            "spec_sha256": digest(json.dumps(spec, sort_keys=True, ensure_ascii=False)),
            "context_sha256": (digest(json.dumps(context, sort_keys=True, ensure_ascii=False))
                               if context is not None else None),
            "style_sha256": digest(packets[aid]["style"]["text"]), "state": "prepared",
        }
    _exclusive_json(out / "artifact_state.json", packet_records)
    record.complete(packet_sha256={aid: row["packet_sha256"] for aid, row in packet_records.items()},
                    artifact_state="prepared; no render or verification performed")
    return packet_records


def _frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---\n") or "\n---\n" not in markdown[4:]:
        raise ValueError("Draft needs complete Markdown front matter")
    head, body = markdown[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if not sep or not key.strip() or key.strip() in fields:
            raise ValueError("Malformed or duplicate front matter field")
        fields[key.strip()] = value.strip().strip("\"'")
    missing = set(FRONTMATTER_FIELDS) - set(fields)
    if missing:
        raise ValueError("Missing front matter fields: " + ", ".join(sorted(missing)))
    extra = set(fields) - set(FRONTMATTER_FIELDS)
    if extra:
        raise ValueError("Unexpected front matter fields: " + ", ".join(sorted(extra)))
    return fields, body


def _validate_draft(aid: str, markdown: str, spec: dict) -> None:
    fields, body = _frontmatter(markdown)
    expected = {
        "artifact_id": aid, "url": str(spec["url"]), "kind": str(spec["kind"]),
        "family": str(spec["family"]),
        "jurisdiction_id": str(spec.get("jurisdiction_id") if spec.get("jurisdiction_id") is not None else "null"),
        "publisher": str(spec["publisher"]),
    }
    for field, wanted in expected.items():
        if fields[field] != wanted:
            raise ValueError(f"Front matter {field} mismatch for {aid}")
    if not fields["title"]:
        raise ValueError("Draft title is empty")
    if any(world_id in body for world_id in SUPPORTED_WORLD_IDS):
        raise ValueError("Private construction world ID appears in body")
    if not body.strip():
        raise ValueError("Draft body is empty")


def _assert_public_inputs_current(manifest: dict) -> None:
    for name, expected in manifest["provenance"]["input_sha256"].items():
        path = pathlib.Path(name)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError("Prepared public input is missing or stale: " + name)


def _frozen_membership(manifest: dict, state: dict) -> list[str]:
    if manifest.get("world") not in SUPPORTED_WORLD_IDS:
        raise ValueError("Frozen world identity is unsupported or tampered")
    ids = manifest.get("artifact_ids")
    if not isinstance(ids, list) or not ids:
        raise ValueError("Frozen artifact-ID list is missing or empty")
    for aid in ids:
        _safe_artifact_id(aid, where="run manifest")
    if len(ids) != len(set(ids)):
        raise ValueError("Frozen artifact-ID list contains duplicates")
    configured = manifest.get("provenance", {}).get("config", {}).get("artifact_ids")
    if configured != ids or set(state) != set(ids):
        raise ValueError("Frozen artifact-ID membership is inconsistent or tampered")
    return ids


def _prepared(run: pathlib.Path, artifact_id: str) -> tuple[dict, dict, dict]:
    aid = _safe_artifact_id(artifact_id, where="prepared run request")
    manifest, state = _read_json(run / "manifest.json"), _read_json(run / "artifact_state.json")
    ids = _frozen_membership(manifest, state)
    if aid not in ids:
        raise ValueError("Artifact ID was not in the frozen public allowlist")
    _assert_public_inputs_current(manifest)
    packet_path, prompt_path = pathlib.Path(state[aid]["packet"]), pathlib.Path(state[aid]["prompt"])
    if digest(packet_path.read_bytes()) != state[aid]["packet_sha256"]:
        raise ValueError("Prepared packet is stale")
    if digest(prompt_path.read_bytes()) != state[aid]["prompt_sha256"]:
        raise ValueError("Prepared prompt is stale")
    packet = _read_json(packet_path)
    if packet.get("spec", {}).get("world_id") != manifest["world"]:
        raise ValueError("Prepared packet world identity is stale or tampered")
    if packet.get("context") is not None and packet["context"].get("world_id") != manifest["world"]:
        raise ValueError("Prepared context world identity is stale or tampered")
    return manifest, state, packet


def ingest_response(run_dir: str | pathlib.Path, artifact_id: str, raw_response: str | bytes) -> dict:
    run = pathlib.Path(run_dir)
    _manifest, state, packet = _prepared(run, artifact_id)
    response = json.loads(raw_response)
    if set(response) != {"artifacts"} or not isinstance(response["artifacts"], list) or len(response["artifacts"]) != 1:
        raise ValueError("Response must contain exactly one artifact")
    item = response["artifacts"][0]
    if set(item) != {"artifact_id", "markdown"} or item["artifact_id"] != artifact_id:
        raise ValueError("Response artifact identity mismatch")
    _validate_draft(artifact_id, item["markdown"], packet["spec"])
    draft_path = run / "drafts" / f"{artifact_id}.md"
    _exclusive_text(draft_path, item["markdown"])
    binding = {k: state[artifact_id][k] for k in
               ("packet_sha256", "prompt_sha256", "spec_sha256", "context_sha256", "style_sha256")}
    binding["artifact_sha256"] = digest(item["markdown"])
    record = {
        "schema_version": "three-family-draft/1", "artifact_id": artifact_id,
        "state": "unverified", "draft": str(draft_path), "binding": binding,
        "response_sha256": digest(raw_response if isinstance(raw_response, bytes) else raw_response.encode()),
        "ingested_utc": datetime.now(timezone.utc).isoformat(),
        "semantic_verification_performed": False,
    }
    _exclusive_json(run / "drafts" / f"{artifact_id}.json", record)
    return record


def invoke_with_transport(run_dir: str | pathlib.Path, artifact_id: str, *,
                          transport: Callable, model: str, reasoning: str = "xhigh") -> dict:
    """Call an explicitly supplied transport, then ingest its response.

    There is deliberately no default transport and no CLI command for this.
    Tests pass a stub; a later authorized renderer may explicitly pass the
    shared ``run_codex`` transport.
    """
    run = pathlib.Path(run_dir)
    _manifest, state, _packet = _prepared(run, artifact_id)
    prompt = pathlib.Path(state[artifact_id]["prompt"]).read_text(encoding="utf-8")
    raw = transport(prompt, OUTPUT_SCHEMA, run / "jobs", stem=f"render_{artifact_id}",
                    model=model, reasoning=reasoning, events=True)
    return ingest_response(run, artifact_id, raw)


def _strict_verdict(verdict: dict, *, draft: dict | None = None, saved: bool = False) -> dict:
    required = {"schema_version", "artifact_id", "pass", "independent", "semantic_verification_performed",
                "verifier_id", "verified_utc", "binding", "findings"}
    allowed = required | ({"verdict_source_sha256", "state"} if saved else set())
    if set(verdict) != allowed or verdict.get("schema_version") != "three-family-verdict/1":
        raise ValueError("Verdict does not satisfy three-family-verdict/1")
    _safe_artifact_id(verdict.get("artifact_id"), where="verdict")
    if verdict["independent"] is not True or verdict["semantic_verification_performed"] is not True:
        raise ValueError("Release requires an independent semantic verdict")
    if type(verdict["pass"]) is not bool or not isinstance(verdict["findings"], list):
        raise ValueError("Malformed verdict result")
    if not isinstance(verdict["verifier_id"], str) or not verdict["verifier_id"].strip():
        raise ValueError("Verdict requires a nonempty verifier identity")
    if not isinstance(verdict["verified_utc"], str):
        raise ValueError("Verdict timestamp must be timezone-aware ISO 8601")
    try:
        stamp = datetime.fromisoformat(verdict["verified_utc"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Verdict timestamp must be timezone-aware ISO 8601") from error
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Verdict timestamp must be timezone-aware ISO 8601")
    binding = verdict.get("binding")
    if not isinstance(binding, dict) or set(binding) != set(BINDING_FIELDS):
        raise ValueError("Verdict binding has the wrong fields")
    for field in BINDING_FIELDS:
        value = binding[field]
        if field == "context_sha256" and value is None:
            continue
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            raise ValueError("Verdict binding contains an invalid digest: " + field)
    if draft is not None and binding != draft.get("binding"):
        raise ValueError("Verdict is stale or bound to different inputs/output")
    if saved:
        if not isinstance(verdict["verdict_source_sha256"], str) or not SHA256.fullmatch(verdict["verdict_source_sha256"]):
            raise ValueError("Saved verdict lacks its source digest")
        expected_state = "verified_pass" if verdict["pass"] else "verified_fail"
        if verdict["state"] != expected_state:
            raise ValueError("Saved verdict state disagrees with result")
    return verdict


def ingest_verdict(run_dir: str | pathlib.Path, verdict_path: str | pathlib.Path) -> dict:
    """Ingest an external semantic verdict; semantic verification is not implemented here."""
    run, path = pathlib.Path(run_dir), pathlib.Path(verdict_path)
    verdict = _read_json(path)
    aid = _safe_artifact_id(verdict.get("artifact_id"), where="verdict")
    draft_path = run / "drafts" / f"{aid}.json"
    if not draft_path.is_file():
        raise ValueError("No ingested draft for verdict artifact")
    draft = _read_json(draft_path)
    _strict_verdict(verdict, draft=draft)
    saved = dict(verdict, verdict_source_sha256=digest(path.read_bytes()),
                 state="verified_pass" if verdict["pass"] else "verified_fail")
    _exclusive_json(run / "reviews" / f"{aid}.json", saved)
    return saved


def _current_binding(run: pathlib.Path, aid: str, state: dict, draft: dict) -> dict:
    packet_path, prompt_path = pathlib.Path(state[aid]["packet"]), pathlib.Path(state[aid]["prompt"])
    artifact_path = pathlib.Path(draft["draft"])
    current = {k: state[aid][k] for k in
               ("packet_sha256", "prompt_sha256", "spec_sha256", "context_sha256", "style_sha256")}
    current["packet_sha256"] = digest(packet_path.read_bytes())
    current["prompt_sha256"] = digest(prompt_path.read_bytes())
    current["artifact_sha256"] = digest(artifact_path.read_bytes())
    return current


def release(run_dir: str | pathlib.Path, out_dir: str | pathlib.Path) -> dict:
    run, out = pathlib.Path(run_dir), pathlib.Path(out_dir)
    if out.exists():
        raise ValueError("Fresh release destination required")
    manifest, state = _read_json(run / "manifest.json"), _read_json(run / "artifact_state.json")
    _assert_public_inputs_current(manifest)
    ids = _frozen_membership(manifest, state)
    inputs, accepted = [run / "manifest.json", run / "artifact_state.json"], []
    for aid in ids:
        draft_file, verdict_file = run / "drafts" / f"{aid}.json", run / "reviews" / f"{aid}.json"
        if not draft_file.is_file() or not verdict_file.is_file():
            raise ValueError("Release blocked by missing draft or verdict: " + aid)
        draft, verdict = _read_json(draft_file), _read_json(verdict_file)
        packet = _read_json(pathlib.Path(state[aid]["packet"]))
        if (packet.get("spec", {}).get("world_id") != manifest["world"] or
                (packet.get("context") is not None and
                 packet["context"].get("world_id") != manifest["world"])):
            raise ValueError("Release blocked by stale or tampered world identity: " + aid)
        try:
            _strict_verdict(verdict, draft=draft, saved=True)
        except ValueError as error:
            raise ValueError("Release blocked by invalid or stale verdict: " + aid) from error
        if verdict.get("pass") is not True or verdict.get("state") != "verified_pass":
            raise ValueError("Release blocked by failing verdict: " + aid)
        if verdict.get("binding") != draft.get("binding"):
            raise ValueError("Release blocked by stale verdict record: " + aid)
        if _current_binding(run, aid, state, draft) != draft["binding"]:
            raise ValueError("Release blocked by changed packet, prompt, or artifact: " + aid)
        inputs.extend([pathlib.Path(state[aid]["packet"]), pathlib.Path(state[aid]["prompt"]),
                       pathlib.Path(draft["draft"]), draft_file, verdict_file])
        accepted.append((aid, draft, verdict))
    record = RunManifest(
        out, {"schema_version": "three-family-source-release/1", "world": manifest["world"],
              "artifact_ids": ids, "artifact_count": len(ids)},
        operation="three_family_pilot.release_verified_sources", inputs=inputs,
        config={"artifact_ids": ids, "requires_current_independent_pass": True}, seeds={},
        hidden_truth_read=False, source_root=ROOT,
        sources=[ADAPTER_SOURCE, MANIFEST_SOURCE],
    )
    documents = []
    for aid, draft, verdict in accepted:
        content = pathlib.Path(draft["draft"]).read_bytes()
        target = out / "source_only" / f"{aid}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)
        documents.append({"document_id": aid, "file": target.name,
                          "sha256": digest(content), "verdict_sha256": verdict["verdict_source_sha256"]})
    _exclusive_json(out / "source_only/index.json", {
        "schema_version": "artifact-only-index/1", "documents": documents,
        "release_gate": "every document has a current independent passing semantic verdict",
    })
    record.complete(released_documents=len(documents), all_current_independent_passes=True)
    return {"released_documents": len(documents), "artifact_ids": ids}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--world", required=True); p.add_argument("--allowlist", required=True); p.add_argument("--out", required=True)
    p.add_argument("--public-spec-revisions", help="Reviewed append-only public-detail revision envelope; original world stays unchanged")
    p = sub.add_parser("ingest"); p.add_argument("--run", required=True); p.add_argument("--artifact-id", required=True); p.add_argument("--response", required=True)
    p = sub.add_parser("verdict"); p.add_argument("--run", required=True); p.add_argument("--verdict", required=True)
    p = sub.add_parser("release"); p.add_argument("--run", required=True); p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.action == "prepare":
        result = prepare(args.world, args.allowlist, args.out, public_spec_revisions=args.public_spec_revisions)
    elif args.action == "ingest":
        result = ingest_response(args.run, args.artifact_id, pathlib.Path(args.response).read_bytes())
    elif args.action == "verdict":
        result = ingest_verdict(args.run, args.verdict)
    else:
        result = release(args.run, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
