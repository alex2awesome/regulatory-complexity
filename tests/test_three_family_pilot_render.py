"""Public-only, transport-stubbed tests for the three-family render adapter."""
from __future__ import annotations

import hashlib
import copy
import json
from pathlib import Path

import pytest

from benchmark.synth.render import three_family_pilot as adapter
from benchmark.synth.render.public_spec_revisions import SCHEMA, SCOPE, object_digest


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value)
    else:
        path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def public_world(tmp_path):
    world = tmp_path / adapter.WORLD_ID
    spec = {
        "schema_version": 1, "world_id": adapter.WORLD_ID, "artifact_id": "CCW__CCW_J01__program_overview",
        "family": "ccw", "jurisdiction_id": "CCW_J01", "kind": "program_overview",
        "construction_status": "structured_render_spec_not_rendered", "publisher": "Alderwick County",
        "url": "https://www.alderwick.aur.gov/ccw/program_overview",
        "content_blocks": [{"block_type": "claim_directives", "claims": [{
            "claim_id": "CCW__CCW_J01__program_overview:Q0001", "topic": "issuer",
            "value": "Alderwick County Sheriff", "unit": None, "fidelity": "exact", "qualifiers": [],
        }]}],
        "renderer_constraints": {"must_not_invent_claims": True,
                                 "must_not_reveal": ["private lineage"], "fictional_names_only": True},
    }
    shared = dict(spec, artifact_id="CCW__SHARED__fictional_state_framework",
                  jurisdiction_id=None, kind="fictional_state_framework",
                  publisher="Aurelia fictional state office",
                  url="https://www.aurelia.aur.gov/ccw/fictional_state_framework")
    _write(world / "BOUNDARY.md", "Public renderer inputs only. Never read private material.\n")
    _write(world / "public/render_specs/ccw.jsonl",
           "\n".join(json.dumps(x) for x in (spec, shared)) + "\n")
    _write(world / "public/render_specs/calfresh.jsonl", "")
    _write(world / "public/artifact_manifest.json", [
        {"artifact_id": x["artifact_id"], "family": x["family"],
         "jurisdiction_id": x["jurisdiction_id"], "kind": x["kind"],
         "status": "structured_render_spec_not_rendered"} for x in (spec, shared)
    ])
    _write(world / "public/render_context/ccw/CCW_J01.json", {
        "world_id": adapter.WORLD_ID, "family": "ccw", "jurisdiction_id": "CCW_J01",
        "jurisdiction_name": "Alderwick County", "fictional": True,
        "public_host": "www.alderwick.aur.gov", "public_organizations": {
            "issuer": "Alderwick County Sheriff"},
        "scope": "public", "prohibitions": ["do not consult private truth"],
    })
    # A tempting private marker: preparation must neither hash nor copy it.
    _write(world / "private/evaluation/split_manifest.json", {"secret": "DO_NOT_READ"})
    return world, spec, shared


def _allow(tmp_path: Path, *ids: str) -> Path:
    path = tmp_path / ("allow_" + hashlib.sha256("|".join(ids).encode()).hexdigest()[:8] + ".txt")
    path.write_text("\n".join(ids) + "\n")
    return path


def _markdown(spec: dict) -> str:
    jid = spec["jurisdiction_id"] if spec["jurisdiction_id"] is not None else "null"
    return ("---\n"
            f"artifact_id: {spec['artifact_id']}\n"
            f"url: {spec['url']}\n"
            f"kind: {spec['kind']}\n"
            f"family: {spec['family']}\n"
            f"jurisdiction_id: {jid}\n"
            f"publisher: {spec['publisher']}\n"
            "title: Fictional public information\n"
            "---\n"
            "The Alderwick County Sheriff is the issuer for this fictional program.\n")


def _prepare(tmp_path: Path, public_world, spec=None):
    world, default, _shared = public_world
    spec = spec or default
    run = tmp_path / ("run_" + spec["artifact_id"].replace("__", "_"))
    adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), run)
    return run, spec


def _public_revision(tmp_path, public_world):
    """A declared-review fixture, not an actual semantic-review certificate."""
    _world, spec, _ = public_world
    bundle = tmp_path / "revisions"
    successor = copy.deepcopy(spec)
    new_claim = dict(successor["content_blocks"][0]["claims"][0],
                     claim_id=spec["artifact_id"] + ":PUBLIC0001")
    successor["content_blocks"].append({"block_type": "claim_directives", "claims": [new_claim]})
    approval = {"scope": SCOPE, "world_id": adapter.WORLD_ID,
                "user_response": "Expand public-detail specifications; preserve the current pilot"}
    _write(bundle / "approval.json", approval)
    _write(bundle / "replacement.json", successor)
    _write(bundle / "source_only/source.md", _markdown(spec))

    def binding(name):
        return {"path": name, "sha256": hashlib.sha256((bundle / name).read_bytes()).hexdigest()}

    row = {"artifact_id": spec["artifact_id"], "original_spec_sha256": object_digest(spec),
           "replacement": binding("replacement.json"), "public_evidence": [{
               **binding("source_only/source.md"), "source_artifact_id": spec["artifact_id"],
               "quote": "The Alderwick County Sheriff is the issuer for this fictional program.",
               "claim_ids": [new_claim["claim_id"]],
           }]}
    envelope = {"schema_version": SCHEMA, "scope": SCOPE, "world_id": adapter.WORLD_ID,
                "approval": binding("approval.json"), "revisions": [row]}

    def seal():
        row["replacement"] = binding("replacement.json")
        row["public_evidence"][0].update(binding("source_only/source.md"))
        review = {"schema_version": "three-family-public-spec-review/1", "scope": SCOPE,
                  "world_id": adapter.WORLD_ID, "pass": True, "independent": True,
                  "reviewer_id": "declared-fixture-reviewer", "revisions_sha256": object_digest([row]),
                  "approval_sha256": envelope["approval"]["sha256"]}
        _write(bundle / "review.json", review)
        envelope["review"] = binding("review.json")
        _write(bundle / "envelope.json", envelope)
        return bundle / "envelope.json"

    return seal(), successor, row, seal


def test_public_revision_is_opt_in_append_only_and_preserves_original_world(tmp_path, public_world):
    world, spec, _ = public_world
    path, successor, _row, _seal = _public_revision(tmp_path, public_world)
    original = (world / "public/render_specs/ccw.jsonl").read_bytes()
    plain = tmp_path / "plain"
    revised = tmp_path / "revised"
    allow = _allow(tmp_path, spec["artifact_id"])
    adapter.prepare(world, allow, plain)
    adapter.prepare(world, allow, revised, public_spec_revisions=path)
    assert (world / "public/render_specs/ccw.jsonl").read_bytes() == original
    assert json.loads((plain / "packets" / f"{spec['artifact_id']}.json").read_text())["spec"] == spec
    packet = json.loads((revised / "packets" / f"{spec['artifact_id']}.json").read_text())
    assert packet["spec"] == successor
    assert "declared-fixture-reviewer" not in json.dumps(packet)
    manifest = json.loads((revised / "manifest.json").read_text())
    assert str(path.resolve()) in manifest["provenance"]["input_sha256"]
    assert "benchmark/synth/render/public_spec_revisions.py" in manifest["source_sha256"]


@pytest.mark.parametrize("mutation,pattern", [
    ("predecessor", "predecessor"), ("old_claim", "original claims"),
    ("constraint", "renderer constraint"), ("identity", "preserved specification"),
    ("cross_jurisdiction", "same jurisdiction"), ("quote", "quote"),
    ("missing_support", "Every added claim"), ("duplicate_claim", "unique"),
])
def test_public_revision_counterexamples_fail_before_output(tmp_path, public_world, mutation, pattern):
    world, spec, _ = public_world
    path, successor, row, seal = _public_revision(tmp_path, public_world)
    if mutation == "predecessor":
        row["original_spec_sha256"] = "0" * 64
    elif mutation == "old_claim":
        successor["content_blocks"][0]["claims"][0]["value"] = "changed original"
    elif mutation == "constraint":
        successor["renderer_constraints"]["must_not_invent_claims"] = False
    elif mutation == "identity":
        successor["jurisdiction_id"] = "CCW_J02"
    elif mutation == "cross_jurisdiction":
        source = path.parent / "source_only/source.md"
        _write(source, source.read_text().replace("jurisdiction_id: CCW_J01", "jurisdiction_id: CCW_J02"))
    elif mutation == "quote":
        row["public_evidence"][0]["quote"] = "This sentence is not in the source."
    elif mutation == "missing_support":
        other = dict(successor["content_blocks"][-1]["claims"][0], claim_id="extra_without_support")
        successor["content_blocks"][-1]["claims"].append(other)
    elif mutation == "duplicate_claim":
        successor["content_blocks"][-1]["claims"][0]["claim_id"] = spec["content_blocks"][0]["claims"][0]["claim_id"]
    _write(path.parent / "replacement.json", successor)
    seal()
    out = tmp_path / "must_not_exist"
    with pytest.raises(ValueError, match=pattern):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), out, public_spec_revisions=path)
    assert not out.exists()


def test_public_revision_needs_current_independent_review_and_bound_inputs(tmp_path, public_world):
    world, spec, _ = public_world
    path, _successor, _row, seal = _public_revision(tmp_path, public_world)
    envelope = json.loads(path.read_text())
    envelope["revisions"][0]["public_evidence"][0]["quote"] = "different text"
    _write(path, envelope)
    with pytest.raises(ValueError, match="independent review"):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), tmp_path / "bad", public_spec_revisions=path)
    seal()
    run = tmp_path / "good"
    adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), run, public_spec_revisions=path)
    _write(path.parent / "source_only/source.md", "changed after preparation")
    with pytest.raises(ValueError, match="stale"):
        _ingest(run, spec)


@pytest.mark.parametrize("escape", ["parent", "absolute", "symlink"])
def test_public_revision_rejects_escaping_or_symlink_inputs(tmp_path, public_world, escape):
    world, spec, _ = public_world
    path, _successor, _row, _seal = _public_revision(tmp_path, public_world)
    envelope = json.loads(path.read_text())
    if escape == "parent":
        envelope["approval"]["path"] = "../revisions/approval.json"
    elif escape == "absolute":
        envelope["approval"]["path"] = str(path.parent / "approval.json")
    else:
        (path.parent / "approval_link.json").symlink_to(path.parent / "approval.json")
        envelope["approval"]["path"] = "approval_link.json"
    _write(path, envelope)
    out = tmp_path / "must_not_exist"
    with pytest.raises(ValueError, match="public bundle|symlinks"):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), out, public_spec_revisions=path)
    assert not out.exists()


def test_public_revision_rejects_self_review_declaration(tmp_path, public_world):
    world, spec, _ = public_world
    path, _successor, _row, _seal = _public_revision(tmp_path, public_world)
    review_path = path.parent / "review.json"
    review = json.loads(review_path.read_text())
    review["independent"] = False
    _write(review_path, review)
    envelope = json.loads(path.read_text())
    envelope["review"]["sha256"] = hashlib.sha256(review_path.read_bytes()).hexdigest()
    _write(path, envelope)
    with pytest.raises(ValueError, match="independent review"):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), tmp_path / "bad", public_spec_revisions=path)


def _ingest(run: Path, spec: dict):
    raw = json.dumps({"artifacts": [{"artifact_id": spec["artifact_id"],
                                     "markdown": _markdown(spec)}]})
    return adapter.ingest_response(run, spec["artifact_id"], raw)


def _verdict(tmp_path: Path, draft: dict, *, passed=True, independent=True, binding=None) -> Path:
    value = {
        "schema_version": "three-family-verdict/1", "artifact_id": draft["artifact_id"],
        "pass": passed, "independent": independent, "semantic_verification_performed": True,
        "verifier_id": "independent-fixture-verifier", "verified_utc": "2026-09-20T12:00:00Z",
        "binding": binding if binding is not None else draft["binding"], "findings": [],
    }
    path = tmp_path / ("verdict_" + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:8] + ".json")
    _write(path, value)
    return path


def test_prepare_requires_explicit_known_unique_public_ids(tmp_path, public_world):
    world, spec, _ = public_world
    duplicate = tmp_path / "duplicate.txt"
    duplicate.write_text(spec["artifact_id"] + "\n" + spec["artifact_id"] + "\n")
    with pytest.raises(ValueError, match="Duplicate artifact IDs"):
        adapter.prepare(world, duplicate, tmp_path / "dup_run")
    unknown = _allow(tmp_path, "NOT_A_PUBLIC_ARTIFACT")
    with pytest.raises(ValueError, match="Unknown artifact IDs"):
        adapter.prepare(world, unknown, tmp_path / "unknown_run")
    empty = tmp_path / "empty.txt"; empty.write_text("\n")
    with pytest.raises(ValueError, match="allowlist is empty"):
        adapter.prepare(world, empty, tmp_path / "empty_run")
    unsafe = _allow(tmp_path, "../escape")
    with pytest.raises(ValueError, match="Unsafe artifact ID"):
        adapter.prepare(world, unsafe, tmp_path / "unsafe_run")


def test_prepare_uses_only_public_inputs_and_records_no_truth_access(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["provenance"]["hidden_truth_read"] is False
    assert adapter.MANIFEST_SOURCE in manifest["provenance"]["source_sha256"]
    private_root = str((public_world[0] / "private").resolve())
    assert not any(path.startswith(private_root + "/")
                   for path in manifest["provenance"]["input_sha256"])
    packet = json.loads((run / "packets" / f"{spec['artifact_id']}.json").read_text())
    assert packet["private_inputs_provided"] is False
    assert packet["ceiling_provided_to_renderer"] is False
    assert "DO_NOT_READ" not in json.dumps(packet)
    assert packet["context"]["jurisdiction_id"] == spec["jurisdiction_id"]
    assert packet["style"]["path"].endswith("municipal_pages.md")
    assert not (public_world[0] / "artifacts").exists()


@pytest.mark.parametrize("successor_id", ["THREE_FAMILY_PILOT_002", "THREE_FAMILY_PILOT_003"])
def test_prepare_accepts_successor_identity_only_when_public_inputs_match(tmp_path, public_world,
                                                                          successor_id):
    world, spec, shared = public_world
    successor = world.parent / successor_id
    world.rename(successor)
    specs_path = successor / "public/render_specs/ccw.jsonl"
    specs = [dict(spec, world_id=successor.name), dict(shared, world_id=successor.name)]
    _write(specs_path, "\n".join(json.dumps(x) for x in specs) + "\n")
    context_path = successor / "public/render_context/ccw/CCW_J01.json"
    context = json.loads(context_path.read_text()); context["world_id"] = successor.name
    _write(context_path, context)
    run = tmp_path / "successor_run"
    adapter.prepare(successor, _allow(tmp_path, spec["artifact_id"]), run)
    assert json.loads((run / "manifest.json").read_text())["world"] == successor.name


def test_prepare_rejects_public_root_symlink_before_world_public_reads(tmp_path, public_world):
    world, spec, _shared = public_world
    public = world / "public"
    redirected = world / "private" / "redirected_public"
    public.rename(redirected)
    public.symlink_to(redirected, target_is_directory=True)
    with pytest.raises(ValueError, match="public root must not be a symlink"):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), tmp_path / "symlink_root_run")


def test_prepare_rejects_nested_public_symlink_resolving_into_private(tmp_path, public_world):
    world, spec, _shared = public_world
    context = world / "public/render_context/ccw/CCW_J01.json"
    private_context = world / "private/redirected_context.json"
    context.rename(private_context)
    context.symlink_to(private_context)
    with pytest.raises(ValueError, match="not public"):
        adapter.prepare(world, _allow(tmp_path, spec["artifact_id"]), tmp_path / "nested_escape_run")


def test_prepare_rejects_supported_directory_with_mismatched_spec_identity(tmp_path, public_world):
    world, spec, _shared = public_world
    successor = world.parent / "THREE_FAMILY_PILOT_002"
    world.rename(successor)
    with pytest.raises(ValueError, match="world identity mismatch"):
        adapter.prepare(successor, _allow(tmp_path, spec["artifact_id"]), tmp_path / "bad_world_run")


def test_prepare_rejects_unknown_world_version(tmp_path, public_world):
    world, spec, _shared = public_world
    unknown = world.parent / "THREE_FAMILY_PILOT_999"
    world.rename(unknown)
    with pytest.raises(ValueError, match="supported immutable world"):
        adapter.prepare(unknown, _allow(tmp_path, spec["artifact_id"]), tmp_path / "unknown_world_run")


def test_shared_artifact_packet_has_null_context(tmp_path, public_world):
    run, shared = _prepare(tmp_path, public_world, public_world[2])
    packet = json.loads((run / "packets" / f"{shared['artifact_id']}.json").read_text())
    assert packet["context"] is None
    assert packet["style"]["path"].endswith("legal_text.md")


def test_stub_transport_ingests_hash_bound_unverified_draft(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    calls = []

    def stub(prompt, schema, out, **kwargs):
        calls.append((prompt, schema, out, kwargs))
        return json.dumps({"artifacts": [{"artifact_id": spec["artifact_id"],
                                          "markdown": _markdown(spec)}]})

    draft = adapter.invoke_with_transport(run, spec["artifact_id"], transport=stub,
                                          model="fixture-model", reasoning="low")
    assert len(calls) == 1 and calls[0][1] == adapter.OUTPUT_SCHEMA
    assert draft["state"] == "unverified"
    assert draft["semantic_verification_performed"] is False
    assert draft["binding"]["artifact_sha256"] == adapter.digest(_markdown(spec))
    assert not (run / "reviews" / f"{spec['artifact_id']}.json").exists()


@pytest.mark.parametrize("stale", ["prompt", "public_input"])
def test_transport_is_not_called_when_any_frozen_input_is_stale(tmp_path, public_world, stale):
    run, spec = _prepare(tmp_path, public_world)
    if stale == "prompt":
        (run / "prompts" / f"{spec['artifact_id']}.txt").write_text("tampered")
    else:
        context = public_world[0] / "public/render_context/ccw/CCW_J01.json"
        context.write_text(context.read_text() + "\n")
    called = []

    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError("stale public inputs must be rejected before transport")

    with pytest.raises(ValueError, match="stale"):
        adapter.invoke_with_transport(run, spec["artifact_id"], transport=forbidden,
                                      model="must-not-run")
    assert not called


def test_ingest_rejects_wrong_response_identity_and_frontmatter(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    wrong = json.dumps({"artifacts": [{"artifact_id": "WRONG", "markdown": _markdown(spec)}]})
    with pytest.raises(ValueError, match="identity mismatch"):
        adapter.ingest_response(run, spec["artifact_id"], wrong)
    bad_text = _markdown(spec).replace(f"kind: {spec['kind']}", "kind: wrong")
    bad = json.dumps({"artifacts": [{"artifact_id": spec["artifact_id"], "markdown": bad_text}]})
    with pytest.raises(ValueError, match="kind mismatch"):
        adapter.ingest_response(run, spec["artifact_id"], bad)


def test_verdict_must_be_independent_semantic_and_exactly_bound(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    with pytest.raises(ValueError, match="independent semantic verdict"):
        adapter.ingest_verdict(run, _verdict(tmp_path, draft, independent=False))
    stale = dict(draft["binding"], artifact_sha256="0" * 64)
    with pytest.raises(ValueError, match="stale or bound"):
        adapter.ingest_verdict(run, _verdict(tmp_path, draft, binding=stale))
    unsafe = json.loads(_verdict(tmp_path, draft).read_text())
    unsafe["artifact_id"] = "../escape"
    unsafe_path = tmp_path / "unsafe_verdict.json"; _write(unsafe_path, unsafe)
    with pytest.raises(ValueError, match="Unsafe artifact ID"):
        adapter.ingest_verdict(run, unsafe_path)


@pytest.mark.parametrize("field,value,match", [
    ("independent", False, "invalid or stale verdict"),
    ("semantic_verification_performed", False, "invalid or stale verdict"),
    ("schema_version", "other", "invalid or stale verdict"),
    ("verifier_id", "", "invalid or stale verdict"),
    ("verified_utc", "2026-09-20T12:00:00", "invalid or stale verdict"),
])
def test_release_revalidates_entire_saved_verdict_contract(tmp_path, public_world,
                                                            field, value, match):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=True))
    review = run / "reviews" / f"{spec['artifact_id']}.json"
    record = json.loads(review.read_text()); record[field] = value; _write(review, record)
    with pytest.raises(ValueError, match=match):
        adapter.release(run, tmp_path / ("release_bad_" + field))


def test_release_refuses_count_completion_missing_or_failing_verdict(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    with pytest.raises(ValueError, match="missing draft or verdict"):
        adapter.release(run, tmp_path / "release_missing")
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=False))
    with pytest.raises(ValueError, match="failing verdict"):
        adapter.release(run, tmp_path / "release_failed")


def test_release_requires_current_pass_and_emits_source_only_index(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=True))
    release = tmp_path / "release"
    result = adapter.release(run, release)
    assert result == {"released_documents": 1, "artifact_ids": [spec["artifact_id"]]}
    index = json.loads((release / "source_only/index.json").read_text())
    assert index["release_gate"].startswith("every document has a current independent")
    assert (release / "source_only" / f"{spec['artifact_id']}.md").read_text() == _markdown(spec)
    manifest = json.loads((release / "manifest.json").read_text())
    assert manifest["all_current_independent_passes"] is True
    assert manifest["provenance"]["hidden_truth_read"] is False
    assert adapter.MANIFEST_SOURCE in manifest["provenance"]["source_sha256"]


def test_release_rejects_artifact_changed_after_passing_verdict(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=True))
    Path(draft["draft"]).write_text(_markdown(spec) + "changed after review\n")
    with pytest.raises(ValueError, match="changed packet, prompt, or artifact"):
        adapter.release(run, tmp_path / "stale_release")


def test_release_rejects_changed_public_source_after_verdict(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=True))
    context = public_world[0] / "public/render_context/ccw/CCW_J01.json"
    context.write_text(context.read_text() + "\n")
    with pytest.raises(ValueError, match="public input is missing or stale"):
        adapter.release(run, tmp_path / "source_stale_release")


def test_release_rejects_tampered_supported_world_identity(tmp_path, public_world):
    run, spec = _prepare(tmp_path, public_world)
    draft = _ingest(run, spec)
    adapter.ingest_verdict(run, _verdict(tmp_path, draft, passed=True))
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["world"] = "THREE_FAMILY_PILOT_002"
    _write(manifest_path, manifest)
    with pytest.raises(ValueError, match="world identity"):
        adapter.release(run, tmp_path / "world_tamper_release")


@pytest.mark.parametrize("mutation,match", [
    ("empty", "missing or empty"),
    ("duplicate", "duplicates"),
    ("membership", "inconsistent or tampered"),
])
def test_release_rejects_empty_or_tampered_frozen_membership(tmp_path, public_world,
                                                              mutation, match):
    run, spec = _prepare(tmp_path, public_world)
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if mutation == "empty":
        manifest["artifact_ids"] = []
    elif mutation == "duplicate":
        manifest["artifact_ids"] = [spec["artifact_id"], spec["artifact_id"]]
    else:
        manifest["artifact_ids"] = ["SAFE_BUT_NOT_IN_STATE"]
        manifest["provenance"]["config"]["artifact_ids"] = ["SAFE_BUT_NOT_IN_STATE"]
    _write(manifest_path, manifest)
    with pytest.raises(ValueError, match=match):
        adapter.release(run, tmp_path / ("release_" + mutation))
