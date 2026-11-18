"""Reviewed, append-only public-detail revisions for immutable pilot worlds.

This checks identities, byte bindings, exact excerpts and review declarations;
it cannot independently establish that an added claim follows from its quote.
That remains the named semantic reviewer's responsibility. No private world
file is read, and no original specification is changed.
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.procbench.infra.manifest import digest


SCHEMA = "three-family-public-spec-revisions/1"
SCOPE = "same_jurisdiction_public_detail_only"
GUIDE_KINDS = frozenset((
    "application_guide", "expedited_service_guide", "interview_guide",
    "issuance_guide", "program_overview", "verification_checklist",
    "initial_application_guide", "interview_and_pickup_guide", "renewal_guide",
    "training_provider_page", "typical_time_faq",
))


def object_digest(value) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False))


def _bound_file(root: Path, binding: dict, inputs: set[Path]) -> Path:
    if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
        raise ValueError("Revision binding needs a relative path")
    relative = Path(binding["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Revision file must stay inside its public bundle")
    path = root / relative
    # Reject symlink components, even a link whose target remains in the bundle.
    if any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError("Revision bundle files cannot use symlinks")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("Missing or escaping revision bundle file")
    if digest(path.read_bytes()) != binding.get("sha256"):
        raise ValueError("Revision bundle file hash mismatch: " + str(relative))
    inputs.add(path.resolve())
    return path


def _claims(blocks: list) -> dict[str, dict]:
    result = {}
    for block in blocks:
        if not isinstance(block, dict) or block.get("block_type") != "claim_directives":
            raise ValueError("Guide revisions support claim-directive blocks only")
        claims = block.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ValueError("Guide claim blocks must be nonempty")
        for claim in claims:
            if not isinstance(claim, dict):
                raise ValueError("Guide claim must be an object")
            cid = claim.get("claim_id")
            if not isinstance(cid, str) or not cid or cid in result:
                raise ValueError("Guide claim IDs must be nonempty and unique")
            result[cid] = claim
    return result


def apply_public_spec_revisions(path: Path, *, world_id: str, specs: dict,
                                selected_ids: list[str], frontmatter_parser):
    """Return replacement specs and bound inputs; never write any file.

    The caller supplies the existing public front-matter parser, avoiding a
    second interpretation of source identity. Review/approval records belong
    in the bundle but are never included in renderer prompts.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError("Revision envelope must be a regular file")
    path = path.resolve()
    root = path.parent
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if (envelope.get("schema_version") != SCHEMA or
            envelope.get("world_id") != world_id or envelope.get("scope") != SCOPE):
        raise ValueError("Revision envelope schema, world or scope mismatch")
    rows = envelope.get("revisions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Revision envelope must contain revisions")
    inputs = {path}
    approval_path = _bound_file(root, envelope.get("approval"), inputs)
    review_path = _bound_file(root, envelope.get("review"), inputs)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (approval.get("scope") != SCOPE or approval.get("world_id") != world_id or
            approval.get("user_response") != "Expand public-detail specifications; preserve the current pilot"):
        raise ValueError("Revision bundle lacks the scoped approval record")
    if (review.get("schema_version") != "three-family-public-spec-review/1" or
            review.get("scope") != SCOPE or review.get("world_id") != world_id or
            review.get("pass") is not True or review.get("independent") is not True or
            not isinstance(review.get("reviewer_id"), str) or not review["reviewer_id"].strip() or
            review.get("revisions_sha256") != object_digest(rows) or
            review.get("approval_sha256") != envelope["approval"]["sha256"]):
        raise ValueError("Revision bundle needs a passing hash-bound independent review")
    updated = dict(specs)
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Revision row must be an object")
        aid = row.get("artifact_id")
        if not isinstance(aid, str) or aid in seen or aid not in selected_ids:
            raise ValueError("Revision ID is duplicate or outside the frozen allowlist")
        seen.add(aid)
        original = specs[aid]
        if original.get("kind") not in GUIDE_KINDS or not original.get("jurisdiction_id"):
            raise ValueError("Revision is not an approved local guide/page/checklist")
        if object_digest(original) != row.get("original_spec_sha256"):
            raise ValueError("Revision predecessor specification hash mismatch")
        spec_path = _bound_file(root, row.get("replacement"), inputs)
        revised = json.loads(spec_path.read_text(encoding="utf-8"))
        if not isinstance(revised, dict) or set(revised) != set(original):
            raise ValueError("Revision cannot add or remove top-level specification fields")
        for key in original.keys() - {"content_blocks", "renderer_constraints"}:
            if revised[key] != original[key]:
                raise ValueError("Revision changed a preserved specification field: " + key)
        old_blocks, new_blocks = original["content_blocks"], revised["content_blocks"]
        if (not isinstance(new_blocks, list) or len(new_blocks) <= len(old_blocks) or
                new_blocks[:len(old_blocks)] != old_blocks):
            raise ValueError("Revision must append blocks without altering original claims")
        old_constraints, new_constraints = original["renderer_constraints"], revised["renderer_constraints"]
        if not isinstance(new_constraints, dict) or any(
            k not in new_constraints or new_constraints[k] != v for k, v in old_constraints.items()
        ):
            raise ValueError("Revision changed an existing renderer constraint")
        old_claims, all_claims = _claims(old_blocks), _claims(new_blocks)
        added = set(all_claims) - set(old_claims)
        covered = set()
        evidence = row.get("public_evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("Added claims require public evidence")
        for item in evidence:
            source_path = _bound_file(root, item, inputs)
            fields, body = frontmatter_parser(source_path.read_text(encoding="utf-8"))
            if (fields.get("artifact_id") != item.get("source_artifact_id") or
                    fields.get("jurisdiction_id") != original["jurisdiction_id"] or
                    fields.get("family") != original["family"]):
                raise ValueError("Revision evidence must come from the same jurisdiction and family")
            quote = item.get("quote")
            claim_ids = item.get("claim_ids")
            if not isinstance(quote, str) or not quote.strip() or quote not in body:
                raise ValueError("Revision public evidence quote does not match artifact bytes")
            if (not isinstance(claim_ids, list) or not claim_ids or
                    any(not isinstance(cid, str) or cid not in added for cid in claim_ids)):
                raise ValueError("Revision evidence must identify added claims")
            covered.update(claim_ids)
        if covered != added:
            raise ValueError("Every added claim needs public-source evidence")
        updated[aid] = revised
    return updated, inputs
