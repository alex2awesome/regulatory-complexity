"""Build the source-only inventory for the solar, CCW and CalFresh study.

This command reads source freeze/index metadata and selected-ledger *manifests*.
It deliberately does not read evidence ledgers, benchmark truth/specification
files, scores, or fitted-model output.  Relevance inferred from a filename,
capture query, or subreddit is only a candidate disposition.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from .infra.manifest import digest, write


SCHEMA = "three-family-source-inventory/2"
FAMILIES = ("solar", "ccw", "calfresh")
STATE_RANK = {"needs_review": 0, "candidate": 1, "included": 2}
PRIVATE_PARTS = {"truth", "spec", "specs", "scores", "_gold", "gold"}
CACHE_PARTS = {"__pycache__", ".cache", ".pytest_cache", ".mypy_cache", ".git"}
SOURCE_LIKE_SUFFIXES = {
    ".csv", ".doc", ".docx", ".htm", ".html", ".json", ".md", ".pdf",
    ".rtf", ".txt", ".xls", ".xlsx", ".xml",
}

PRIMARY_FREEZES = {
    "solar_permit": "solar",
    "ccw_counties": "ccw",
    "calfresh": "calfresh",
    "calguns_a": "ccw",
    "calguns_g": "ccw",
    "calguns_q": "ccw",
}

KEYWORD_PATTERNS = {
    "solar": (r"solar", r"photovoltaic", r"interconnection", r"net[\s_-]*meter"),
    "ccw": (r"ccw", r"caguns", r"calguns", r"concealed", r"carry[\s_-]*licen[cs]e"),
    "calfresh": (r"calfresh", r"food[\s_-]*stamps?", r"snap"),
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
    return digest(payload)


def _repo_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _safe_source_path(value: str) -> bool:
    parts = {part.lower() for part in Path(value).parts}
    return not bool(parts & PRIVATE_PARTS)


def _thread_id(doc_id: str, row: dict[str, Any]) -> str | None:
    if not doc_id.lower().startswith("calguns_"):
        return None
    if row.get("thread_id"):
        return str(row["thread_id"])
    match = re.search(r"calguns_(\d+)_page", doc_id)
    return match.group(1) if match else None


def _reddit_id(doc_id: str, row: dict[str, Any]) -> str | None:
    for key in ("reddit_id", "thread_id"):
        if row.get(key):
            return str(row[key])
    patterns = (
        r"^reddit_thread_([a-z0-9]+)$",
        r"^reddit_root_context_([a-z0-9]+)_",
        r"^reddit_legacy_([a-z0-9]+)_",
        r"^reddit_comments_([a-z0-9]+)$",
        r"^reddit_([a-z0-9]+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, doc_id, flags=re.I)
        if match:
            return match.group(1).lower()
    return None


def candidate_families(*values: Any) -> list[str]:
    """Return metadata keyword matches; callers must retain candidate status."""
    text = " ".join(str(value) for value in values if value is not None).lower()
    return [family for family in FAMILIES
            if any(re.search(rf"(?<![a-z0-9])(?:{pattern})(?![a-z0-9])", text)
                   for pattern in KEYWORD_PATTERNS[family])]


def _source_key(process: str, row: dict[str, Any]) -> tuple[str, str]:
    doc_id = str(row.get("doc_id") or row.get("document_id"))
    thread = _thread_id(doc_id, row)
    if thread:
        return f"calguns-thread:{thread}", "forum_thread"
    reddit = _reddit_id(doc_id, row)
    if reddit:
        return f"reddit-thread:{reddit}", "forum_thread"
    source_path = str(row.get("source_path") or row.get("origin") or "")
    if source_path.lower().endswith((".xlsx", ".xls")):
        return f"workbook:{row.get('source_sha256') or row.get('origin_sha256') or doc_id}", "workbook"
    return f"freeze:{process}:{doc_id}", "document"


def _source_id(key: str) -> str:
    label = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")[:72]
    return f"src-{label}-{digest(key)[:12]}"


class Registry:
    def __init__(self, root: Path):
        self.root = root
        self.rows: dict[str, dict[str, Any]] = {}
        self._observed_paths: dict[str, dict[str, Any]] = {}

    def observe(self, value: str) -> dict[str, Any]:
        if value not in self._observed_paths:
            path = _repo_path(self.root, value)
            if not _safe_source_path(value) or not path.is_file():
                observed = {"exists": False, "actual_sha256": None,
                            "actual_bytes": None}
            else:
                raw = path.read_bytes()
                observed = {"exists": True,
                            "actual_sha256": hashlib.sha256(raw).hexdigest(),
                            "actual_bytes": len(raw)}
            self._observed_paths[value] = observed
        return self._observed_paths[value]

    def source(self, key: str, logical_kind: str) -> dict[str, Any]:
        if key not in self.rows:
            self.rows[key] = {
                "schema_version": SCHEMA,
                "source_id": _source_id(key),
                "logical_key": key,
                "logical_kind": logical_kind,
                "content_sha256": None,
                "physical_aliases": [],
                "freeze_origins": [],
                "family_assignments": [],
                "accepted_ledger_links": [],
                "parse_manifests": [],
                "expected_units": {},
                "jurisdiction": None,
                "era": None,
                "reviewer": "unassigned",
                "holds": [],
                "semantic_relevance_status": "not_adjudicated",
            }
        return self.rows[key]

    def add_alias(self, row: dict[str, Any], *, path: str, role: str,
                  sha256: str | None = None, byte_count: int | None = None,
                  origin_manifest: str | None = None) -> None:
        if not path or not _safe_source_path(path):
            return
        observed = self.observe(path)
        if not observed["exists"]:
            hash_status = "missing"
        elif sha256 is None:
            hash_status = "observed_no_declared_hash"
        elif sha256 == observed["actual_sha256"]:
            hash_status = "verified_match"
        else:
            hash_status = "declared_hash_mismatch"
        alias = {"path": path, "role": role,
                 "declared_sha256": sha256, "declared_bytes": byte_count,
                 **observed, "hash_status": hash_status,
                 "origin_manifest": origin_manifest}
        prior = next((item for item in row["physical_aliases"] if item["path"] == path), None)
        if prior is None:
            row["physical_aliases"].append(alias)
            if hash_status == "missing":
                self.add_hold(row, {"code": "physical_alias_missing", "path": path,
                                    "status": "open", "blocking_complete_coverage": True})
            elif hash_status == "declared_hash_mismatch":
                self.add_hold(row, {"code": "declared_hash_mismatch", "path": path,
                                    "declared_sha256": sha256,
                                    "actual_sha256": observed["actual_sha256"],
                                    "status": "open", "blocking_complete_coverage": True})
        elif prior.get("declared_sha256") is None and sha256 is not None:
            prior["declared_sha256"] = sha256
            prior["declared_bytes"] = byte_count
            prior["hash_status"] = ("verified_match" if sha256 == prior["actual_sha256"]
                                    else "declared_hash_mismatch")
            if prior["hash_status"] == "declared_hash_mismatch":
                self.add_hold(row, {"code": "declared_hash_mismatch", "path": path,
                                    "declared_sha256": sha256,
                                    "actual_sha256": prior["actual_sha256"],
                                    "status": "open", "blocking_complete_coverage": True})

    @staticmethod
    def assign(row: dict[str, Any], family: str, state: str, method: str,
               reason: str) -> None:
        assert family in FAMILIES and state in STATE_RANK
        existing = next((item for item in row["family_assignments"]
                         if item["family"] == family), None)
        value = {"family": family, "state": state, "method": method,
                 "reason": reason, "semantic_relevance_accepted": False}
        if existing is None:
            row["family_assignments"].append(value)
        elif STATE_RANK[state] > STATE_RANK[existing["state"]]:
            existing.update(value)

    @staticmethod
    def add_hold(row: dict[str, Any], hold: dict[str, Any]) -> None:
        marker = _canonical_hash(hold)
        if all(_canonical_hash(item) != marker for item in row["holds"]):
            row["holds"].append(hold)

    @staticmethod
    def resolve_hold(row: dict[str, Any], code: str, resolution: dict[str, Any]) -> None:
        for hold in row["holds"]:
            if hold.get("code") == code and hold.get("effective_status") != "resolved":
                hold["effective_status"] = "resolved"
                hold["resolution"] = resolution

    def finalize(self) -> list[dict[str, Any]]:
        result = []
        for row in self.rows.values():
            row["physical_aliases"].sort(key=lambda item: (item["path"], item["role"]))
            row["freeze_origins"].sort(key=lambda item: (item["index_path"], item["document_id"]))
            row["family_assignments"].sort(key=lambda item: FAMILIES.index(item["family"]))
            row["accepted_ledger_links"].sort(key=lambda item: item["path"])
            row["parse_manifests"] = sorted(set(row["parse_manifests"]))
            hashes = sorted({item["actual_sha256"] for item in row["physical_aliases"]
                             if item.get("actual_sha256")})
            # A logical hash binds all captured representations. It is not a claim
            # that an OCR/transcript is byte-identical to its physical original.
            row["content_sha256"] = _canonical_hash(hashes)
            row["hash_basis"] = "sorted replayed SHA-256 values of existing physical representations"
            if row["logical_key"].startswith("calguns-thread:"):
                pages = {item["document_id"] for item in row["freeze_origins"]
                         if "_page" in item["document_id"]}
                row["expected_units"].setdefault("captured_pages", len(pages))
            if row["logical_key"].startswith("reddit-thread:"):
                comments = row["expected_units"].get("comments")
                row["expected_units"].setdefault("captured_post_views",
                                                  comments + 1 if comments is not None else 1)
            row["parse_revision"] = {
                "selected_ledger_manifest_count": len(row["accepted_ledger_links"]),
                "manifests": row["parse_manifests"],
                "semantic_acceptance_inferred": False,
            }
            result.append(row)
        return sorted(result, key=lambda item: item["source_id"])


def _row_aliases(registry: Registry, source: dict[str, Any], process: str,
                 row: dict[str, Any], index_path: str) -> None:
    doc_id = str(row.get("doc_id") or row.get("document_id"))
    origin = row.get("origin") or row.get("source_path")
    if row.get("source_path") and origin == row.get("source_path"):
        origin_hash = row.get("source_sha256") or row.get("origin_sha256") or row.get("raw_sha256")
    else:
        origin_hash = row.get("origin_sha256") or row.get("raw_sha256")
    origin_bytes = row.get("origin_bytes") or row.get("raw_bytes")
    if origin:
        registry.add_alias(source, path=str(origin), role="physical_origin",
                           sha256=origin_hash, byte_count=origin_bytes,
                           origin_manifest=index_path)
    frozen = f"{Path(index_path).parent.as_posix()}/source/{doc_id}.txt"
    if _repo_path(registry.root, frozen).is_file():
        registry.add_alias(source, path=frozen, role="frozen_rendering",
                           sha256=row.get("sha256") or row.get("source_sha256"),
                           byte_count=row.get("bytes") or row.get("source_bytes"),
                           origin_manifest=index_path)
    artifact = row.get("artifact_path")
    explicit_artifact = bool(artifact)
    if not artifact:
        possible = f"{Path(index_path).parent.as_posix()}/artifacts/{doc_id}.md"
        artifact = possible if _repo_path(registry.root, possible).is_file() else None
    if artifact:
        registry.add_alias(source, path=str(artifact), role="artifact_rendering",
                           sha256=(row.get("artifact_sha256") or row.get("sha256"))
                           if explicit_artifact else None,
                           byte_count=row.get("artifact_bytes") or row.get("bytes"),
                           origin_manifest=index_path)
    for entry in row.get("origins", []):
        registry.add_alias(source, path=entry["path"], role="physical_origin",
                           sha256=entry.get("sha256"), byte_count=entry.get("bytes"),
                           origin_manifest=index_path)
    for entry in row.get("source_files", []):
        registry.add_alias(source, path=entry["path"], role="physical_origin",
                           sha256=entry.get("sha256"), byte_count=entry.get("bytes"),
                           origin_manifest=index_path)
    for entry in row.get("reused_root_context", []):
        registry.add_alias(source, path=entry["artifact_path"], role="root_context",
                           sha256=entry.get("sha256"), origin_manifest=index_path)


def add_index(registry: Registry, index_path: str, *, family: str | None,
              state: str, method: str, process_override: str | None = None,
              unresolved_if_no_match: bool = False) -> None:
    path = _repo_path(registry.root, index_path)
    if not path.is_file():
        return
    data = _json(path)
    process = process_override or str(data.get("process") or path.parent.name)
    index_sha256 = digest(path.read_bytes())
    for item in data.get("documents", []):
        key, kind = _source_key(process, item)
        source = registry.source(key, kind)
        doc_id = str(item.get("doc_id") or item.get("document_id"))
        freeze = {"index_path": index_path, "index_sha256": index_sha256,
                  "process": process, "document_id": doc_id,
                  "selection_state": state}
        if freeze not in source["freeze_origins"]:
            source["freeze_origins"].append(freeze)
        _row_aliases(registry, source, process, item, index_path)
        if family:
            registry.assign(source, family, state, method,
                            f"selected by {process} source metadata")
        else:
            values = [doc_id, item.get("subreddit"), item.get("subreddits"),
                      item.get("origin"), item.get("source_path"),
                      [entry.get("path") for entry in item.get("origins", [])],
                      [entry.get("path") for entry in item.get("source_files", [])]]
            matches = candidate_families(*values)
            for match in matches:
                registry.assign(source, match, "candidate", "metadata_keyword",
                                "filename, capture-query or subreddit metadata match; human review required")
            if not matches and unresolved_if_no_match:
                for unresolved_family in FAMILIES:
                    registry.assign(source, unresolved_family, "needs_review",
                                    "unassigned_mixed_capture",
                                    "no source-metadata family match; not a semantic exclusion")
        if kind == "workbook":
            source["expected_units"]["sheets"] = len(item.get("worksheets", []))
            source["expected_units"]["stored_cells"] = item.get("stored_cells")
            if item.get("semantic_read_complete") is False:
                registry.add_hold(source, {"code": "semantic_workbook_review_incomplete",
                                           "blocking_complete_coverage": True})
        if key.startswith("reddit-thread:"):
            comments = item.get("comments")
            if comments is not None:
                source["expected_units"]["comments"] = max(
                    comments, source["expected_units"].get("comments", 0))
            if item.get("root_context_missing"):
                registry.add_hold(source, {"code": "root_context_missing",
                                           "status": "historical_observation",
                                           "effective_status": "open",
                                           "blocking_complete_coverage": True})


def _attach_same_stem_aliases(registry: Registry, index_path: str) -> None:
    path = _repo_path(registry.root, index_path)
    if not path.is_file():
        return
    data = _json(path)
    process = str(data.get("process") or path.parent.name)
    by_stem: dict[str, dict[str, Any]] = {}
    for item in data.get("documents", []):
        origin = item.get("origin")
        if origin:
            key, kind = _source_key(process, item)
            by_stem[str(Path(origin).with_suffix(""))] = registry.source(key, kind)
    for withheld in data.get("withheld", []):
        alias = withheld.get("file") or withheld.get("path")
        reason = str(withheld.get("reason", "")).lower()
        if not alias or not any(token in reason for token in ("same-stem", "original", "copy")):
            continue
        source = by_stem.get(str(Path(alias).with_suffix("")))
        if source:
            registry.add_alias(source, path=alias, role="alternate_physical_representation",
                               origin_manifest=index_path)


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _strings(item)


def attach_accepted_ledgers(registry: Registry, selected_path: str) -> None:
    """Link sources using selected hashes plus sibling manifest declarations only."""
    path = _repo_path(registry.root, selected_path)
    selected = _json(path)
    ledgers = selected.get("ledgers", [])
    alias_map: dict[str, set[str]] = defaultdict(set)
    document_map: dict[str, set[str]] = defaultdict(set)
    thread_map: dict[str, str] = {}
    for key, source in registry.rows.items():
        for alias in source["physical_aliases"]:
            alias_map[alias["path"]].add(key)
        for item in source["freeze_origins"]:
            document_map[item["document_id"]].add(key)
        if key.startswith("calguns-thread:"):
            thread_map[key.split(":", 1)[1]] = key
    for ledger in ledgers:
        evidence_path = str(ledger["path"])
        manifest_path = str(Path(evidence_path).with_name("manifest.json"))
        manifest_file = _repo_path(registry.root, manifest_path)
        if not manifest_file.is_file():
            continue
        manifest = _json(manifest_file)
        declared = set(_strings(manifest))
        matched_keys: set[str] = set()
        for value in declared:
            matched_keys.update(alias_map.get(value, ()))
            matched_keys.update(document_map.get(value, ()))
            for thread in re.findall(r"calguns_(\d+)_page", value):
                if thread in thread_map:
                    matched_keys.add(thread_map[thread])
        for key in matched_keys:
            source = registry.rows[key]
            if source:
                link = {"path": evidence_path, "sha256": ledger["sha256"],
                        "program_id": ledger.get("program_id"),
                        "linkage": "selected ledger sibling manifest declares source/path"}
                if link not in source["accepted_ledger_links"]:
                    source["accepted_ledger_links"].append(link)
                source["parse_manifests"].append(manifest_path)


def _add_megathread_coverage(registry: Registry, audit: dict[str, Any]) -> None:
    for item in audit.get("forum", {}).get("megathreads", []):
        key = f"calguns-thread:{item['thread_id']}"
        if key not in registry.rows:
            continue
        source = registry.rows[key]
        source["expected_units"].update(
            captured_pages=item["artifact_count"],
            logical_pages=item["logical_page_count"],
            expected_through_page=item["max_page"],
            missing_pages=item["missing_page_count"],
        )
        if item["missing_page_count"]:
            Registry.add_hold(source, {"code": "missing_thread_pages",
                                       "ranges": item["missing_page_ranges"],
                                       "status": "historical_observation",
                                       "effective_status": "open",
                                       "observed_in": "runs/rw_parse_20260919/real_corpus_inventory_audit.json",
                                       "blocking_complete_coverage": True})


def add_current_forum_plan(registry: Registry, plan_path: str) -> None:
    """Attach later gap-fill captures while retaining the older gap finding."""
    path = _repo_path(registry.root, plan_path)
    if not path.is_file():
        return
    plan = _json(path)
    plan_sha256 = digest(path.read_bytes())
    terminal = {str(item["thread_id"]): item for item in plan.get("terminal_page_checks", [])}
    for item in plan.get("megathreads", []):
        thread = str(item["thread_id"])
        source = registry.source(f"calguns-thread:{thread}", "forum_thread")
        for document in item.get("documents", []):
            registry.add_alias(source, path=document["path"], role="artifact_rendering",
                               sha256=document.get("sha256"), byte_count=document.get("bytes"),
                               origin_manifest=plan_path)
            if document.get("slice") == "forum_gap_retrieval_v1":
                raw_path = str(Path(document["path"]).parent.parent / "raw" /
                               (Path(document["path"]).stem + ".html"))
                registry.add_alias(source, path=raw_path, role="physical_origin",
                                   origin_manifest=plan_path)
                freeze = {"index_path": plan_path, "index_sha256": plan_sha256,
                          "process": "forum_gap_retrieval_v1",
                          "document_id": document["document_id"],
                          "selection_state": "included"}
                if freeze not in source["freeze_origins"]:
                    source["freeze_origins"].append(freeze)
        unique_pages = item.get("unique_page_count")
        source["expected_units"].update(
            current_captured_pages=item.get("document_count"),
            current_unique_pages=unique_pages,
        )
        check = terminal.get(thread)
        if check and unique_pages == check.get("navigation_terminal"):
            Registry.resolve_hold(source, "missing_thread_pages", {
                "state": "resolved_in_later_freeze",
                "receipt_path": plan_path,
                "receipt_sha256": plan_sha256,
                "unique_pages": unique_pages,
                "navigation_terminal": check["navigation_terminal"],
                "terminal_source": check["source"],
            })


def resolve_reddit_root_holds(registry: Registry, recovery_path: str) -> None:
    path = _repo_path(registry.root, recovery_path)
    if not path.is_file():
        return
    receipt_hash = digest(path.read_bytes())
    data = _json(path)
    for item in data.get("documents", []):
        key = f"reddit-thread:{item['thread_id']}"
        if key in registry.rows:
            Registry.resolve_hold(registry.rows[key], "root_context_missing", {
                "state": "resolved_in_later_freeze",
                "receipt_path": recovery_path,
                "receipt_sha256": receipt_hash,
                "root_document_id": item["document_id"],
            })


def add_scoped_manifest_sources(registry: Registry, manifest_path: str,
                                family: str) -> None:
    """Add public corpus inputs declared by a family-scoped parse manifest."""
    path = _repo_path(registry.root, manifest_path)
    if not path.is_file():
        return
    data = _json(path)
    bindings = data.get("input_bindings") or data.get("inputs") or []
    manifest_sha256 = digest(path.read_bytes())
    for item in bindings:
        source_path = str(item.get("path", ""))
        if not source_path.startswith("corpus/") or not _safe_source_path(source_path):
            continue
        suffix = Path(source_path).suffix.lower()
        logical_kind = "workbook" if suffix in {".xls", ".xlsx"} else "document"
        source_hash = item.get("sha256")
        key = (f"workbook:{source_hash}" if logical_kind == "workbook"
               else f"source-file:{source_hash or source_path}")
        source = registry.source(key, logical_kind)
        registry.add_alias(source, path=source_path, role="physical_origin",
                           sha256=source_hash, byte_count=item.get("bytes"),
                           origin_manifest=manifest_path)
        origin = {"index_path": manifest_path,
                  "index_sha256": manifest_sha256,
                  "process": str(data.get("program_id") or Path(manifest_path).parent.name),
                  "document_id": Path(source_path).name,
                  "selection_state": "included"}
        if origin not in source["freeze_origins"]:
            source["freeze_origins"].append(origin)
        registry.assign(source, family, "included", "family_scoped_parse_manifest",
                        f"public corpus input declared by {manifest_path}")
        source["parse_manifests"].append(manifest_path)


def _source_groups(audit: dict[str, Any], workbook_manifest: dict[str, Any] | None,
                   forum_plan: dict[str, Any] | None,
                   root_recovery: dict[str, Any] | None) -> list[dict[str, Any]]:
    physical = audit["physical_corpus"]
    groups = [
        {"group_id": "audit:frozen-origins", "count": physical["supplied_frozen_origins"],
         "census_state": "source_rows_available_in_23_freezes",
         "study_state": "screened_partly_by_registry"},
        {"group_id": "audit:withheld-not-supplied", "count": physical["explicitly_withheld_not_supplied"],
         "census_state": "withheld_unassigned", "study_state": "needs_review",
         "limitation": "audit showed withheld was not a defensible semantic exclusion"},
        {"group_id": "audit:outside-every-freeze", "count": physical["outside_every_freeze"],
         "census_state": "outside_freezes", "study_state": "needs_review"},
        {"group_id": "excluded:hidden-gold", "count": physical["outside_every_freeze_by_collection"].get(
            "corpus/realworld/_gold (not opened)", 0), "census_state": "excluded_by_policy",
         "study_state": "excluded_hidden", "paths_read": False},
        {"group_id": "excluded:derived-analysis-model", "count": None,
         "census_state": "not_part_of_source_denominator", "study_state": "excluded_derived",
         "paths_read": False},
    ]
    for name, count in sorted(physical["outside_every_freeze_by_collection"].items()):
        if "_gold" in name:
            continue
        groups.append({"group_id": "outside:" + name, "count": count,
                       "census_state": "outside_freezes", "study_state": "needs_review",
                       "limitation": "collection-level audit count; source-level relevance unresolved"})
    if workbook_manifest:
        summary = workbook_manifest.get("summary", {})
        encrypted = summary.get("dispositions", {}).get(
            "encrypted_legacy_workbook_requires_authorized_readable_copy", 0)
        groups.append({"group_id": "program-workbooks:encrypted-unreadable", "count": encrypted,
                       "census_state": "known_unreadable", "study_state": "needs_review"})
        other_program = sum(not candidate_families(item.get("source_path"))
                            for item in workbook_manifest.get("documents", []))
        groups.append({"group_id": "program-workbooks:other-benefit-metadata", "count": other_program,
                       "census_state": "source_rows_available", "study_state": "needs_review",
                       "limitation": "not assigned to CalFresh merely because it shares a workbook freeze"})
    if forum_plan:
        groups.extend([
            {"group_id": "forum-gap-pages:historical", "count": 577,
             "census_state": "historical_missing_capture", "study_state": "historical_hold"},
            {"group_id": "forum-gap-pages:later-freeze", "count": 577,
             "census_state": "captured_and_hash_replayed", "study_state": "resolved_source_hold",
             "receipt": "runs/rw_parse_20260919/FORUM_WORK_PLAN_v3.json"},
        ])
    if root_recovery:
        summary = root_recovery.get("summary", {})
        groups.extend([
            {"group_id": "reddit-roots:historical-missing", "count": summary.get("missing_roots_before"),
             "census_state": "historical_missing_context", "study_state": "historical_hold"},
            {"group_id": "reddit-roots:later-recovered", "count": summary.get("recovered_threads"),
             "census_state": "captured_and_hash_replayed", "study_state": "resolved_source_hold",
             "receipt": "runs/rw_parse_20260919/exhaustive_reddit_comments_v1/root_context_v1/manifest.json"},
            {"group_id": "reddit-comment-parents:unresolved", "count": summary.get("unresolved_comment_parent_links"),
             "census_state": "known_missing_context", "study_state": "needs_review"},
        ])
    return groups


def _summary(rows: list[dict[str, Any]], audit: dict[str, Any], groups: list[dict[str, Any]]) -> dict[str, Any]:
    family = {name: Counter() for name in FAMILIES}
    for row in rows:
        for assignment in row["family_assignments"]:
            family[assignment["family"]][assignment["state"]] += 1
    hash_status = Counter(alias["hash_status"] for row in rows for alias in row["physical_aliases"])
    blocking = lambda hold: (hold.get("blocking_complete_coverage") and
                             hold.get("effective_status") != "resolved" and
                             hold.get("status") != "resolved")
    return {
        "schema_version": "three-family-source-coverage/2",
        "physical_census_denominator": {
            "snapshot": audit.get("created_utc"),
            "all_files": audit["physical_corpus"]["all_files"],
            "disjoint_strata": {
                "supplied_frozen_origins": audit["physical_corpus"]["supplied_frozen_origins"],
                "explicitly_withheld_not_supplied": audit["physical_corpus"]["explicitly_withheld_not_supplied"],
                "outside_every_freeze": audit["physical_corpus"]["outside_every_freeze"],
            },
            "unit": "physical files, not logical sources or semantic relevance",
        },
        "registry": {
            "logical_sources": len(rows),
            "physical_alias_rows": sum(len(row["physical_aliases"]) for row in rows),
            "physical_alias_hash_status": dict(sorted(hash_status.items())),
            "sources_with_accepted_ledger_link": sum(bool(row["accepted_ledger_links"]) for row in rows),
            "sources_with_effective_blocking_hold": sum(any(blocking(h) for h in row["holds"])
                                                        for row in rows),
            "historical_holds_resolved": sum(h.get("effective_status") == "resolved"
                                             for row in rows for h in row["holds"]),
            "by_family_and_state": {name: dict(sorted(counts.items()))
                                    for name, counts in family.items()},
        },
        "source_groups": {
            "count": len(groups),
            "baseline_unresolved_physical_files": (
                audit["physical_corpus"]["explicitly_withheld_not_supplied"]
                + audit["physical_corpus"]["outside_every_freeze"]
                - audit["physical_corpus"]["outside_every_freeze_by_collection"].get(
                    "corpus/realworld/_gold (not opened)", 0)
            ),
            "count_note": "collection subgroups overlap their outside-every-freeze parent and are not summed",
        },
        "excluded": ["benchmark truth/specification/score paths", "corpus/realworld/_gold contents",
                     "derived analyses and model fits"],
        "state_definitions": {
            "included": "selected by a directly family-scoped source freeze/manifest; semantic relevance is not inferred",
            "candidate": "metadata-only family match requiring human source review",
            "needs_review": "unassigned or other-program metadata; not a semantic exclusion",
        },
        "claims_not_made": [
            "The 14,915-file denominator is the preserved September 19 audit, not today's on-disk count.",
            "The registry is not an exhaustive live-web inventory.",
            "A metadata candidate is not a human relevance decision.",
            "Unassigned and collection-level groups are not semantic exclusions.",
            "Accepted-ledger linkage does not establish complete reading or fit readiness.",
            "A physical-file denominator is not a logical-source denominator.",
        ],
    }


def fresh_corpus_census(root: Path, rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Inventory current corpus paths and sizes without opening unrepresented files."""
    represented = {alias["path"] for row in rows for alias in row["physical_aliases"]
                   if alias["path"].startswith("corpus/")}
    categories = Counter()
    excluded_examples: dict[str, list[str]] = defaultdict(list)
    unresolved: list[dict[str, Any]] = []
    corpus = root / "corpus"
    for path in sorted(corpus.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        lowered = {part.lower() for part in parts}
        if any(part.startswith(".") for part in parts) or lowered & CACHE_PARTS or path.suffix.lower() == ".pyc":
            category = "excluded_hidden_or_cache"
        elif lowered & PRIVATE_PARTS:
            category = "excluded_private_or_gold"
        elif relative in represented:
            category = "represented_source_path"
        elif path.suffix.lower() in SOURCE_LIKE_SUFFIXES:
            category = "unrepresented_source_like_path"
            stat = path.stat()
            unresolved.append({
                "schema_version": "three-family-unrepresented-source-path/1",
                "path": relative,
                "bytes": stat.st_size,
                "suffix": path.suffix.lower(),
                "collection": "/".join(parts[:4]),
                "study_state": "needs_review",
                "contents_read": False,
                "semantic_exclusion": False,
            })
        else:
            category = "excluded_non_source_support"
        categories[category] += 1
        if category.startswith("excluded") and len(excluded_examples[category]) < 10:
            excluded_examples[category].append(relative)
    census = {
        "schema_version": "three-family-fresh-corpus-census/1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "current corpus/ filesystem path/stat census",
        "method": "directory entry, suffix and byte-size metadata only for unrepresented paths",
        "unrepresented_contents_read": False,
        "counts": dict(sorted(categories.items())),
        "current_on_disk_files": sum(categories.values()),
        "historical_denominator_replaced": False,
        "exclusion_rules": {
            "private_or_gold_components": sorted(PRIVATE_PARTS),
            "hidden_or_cache_components": sorted(CACHE_PARTS),
            "hidden_component_prefix": ".",
            "non_source_support": "non-source-like suffix after the above categories",
        },
        "excluded_examples": dict(sorted(excluded_examples.items())),
        "limitations": [
            "Suffix and path metadata do not establish semantic relevance.",
            "Unrepresented paths remain unresolved until source-level review.",
            "This current count is reported beside, not substituted for, the September 19 audit denominator.",
        ],
    }
    return census, unresolved


def build_inventory(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[str]]:
    root = root.resolve()
    audit_path = "runs/rw_parse_20260919/real_corpus_inventory_audit.json"
    selected_path = "runs/rw_parse_20260919/review_sweeps_73_ledgers/selected_ledgers.json"
    audit = _json(root / audit_path)
    registry = Registry(root)
    inputs = [audit_path, selected_path]

    for process, family in PRIMARY_FREEZES.items():
        index_path = f"runs/rw_parse_20260918/{process}/frozen_index.json"
        add_index(registry, index_path, family=family, state="included",
                  method="approved_program_freeze", process_override=process)
        _attach_same_stem_aliases(registry, index_path)
        inputs.append(index_path)

    optional = [
        ("runs/rw_parse_20260919/supplemental_sources/solar_permit/frozen_index.json", "solar", "included", False),
        ("runs/rw_parse_20260919/supplemental_sources/calguns_g/frozen_index.json", "ccw", "included", False),
        ("runs/rw_parse_20260919/reddit_comment_supplement_v1/solar_permit/artifact_only_index.json", "solar", "included", False),
        ("runs/rw_parse_20260918/county_user_evidence/frozen_index.json", None, "candidate", True),
        ("runs/rw_parse_20260919/exhaustive_reddit_comments_v1/manifest.json", None, "candidate", True),
        ("runs/rw_parse_20260919/legacy_reddit_posts_v1/manifest.json", None, "candidate", True),
        ("runs/rw_parse_20260919/exhaustive_reddit_comments_v1/root_context_v1/manifest.json", None, "candidate", True),
        ("runs/rw_parse_20260919/program_workbooks_v1/manifest.json", None, "candidate", True),
    ]
    for index_path, family, state, unresolved in optional:
        if (root / index_path).is_file():
            add_index(registry, index_path, family=family, state=state,
                      method="registered_source_metadata", unresolved_if_no_match=unresolved)
            inputs.append(index_path)

    for manifest_path in (
        "runs/rw_parse_20260919/calfresh_cf296_cohort_parse_v1/manifest.json",
        "runs/rw_parse_20260919/calfresh_cf18_cohort_parse_v1/manifest.json",
    ):
        if (root / manifest_path).is_file():
            add_scoped_manifest_sources(registry, manifest_path, "calfresh")
            inputs.append(manifest_path)

    _add_megathread_coverage(registry, audit)
    forum_plan_path = "runs/rw_parse_20260919/FORUM_WORK_PLAN_v3.json"
    add_current_forum_plan(registry, forum_plan_path)
    if (root / forum_plan_path).is_file():
        inputs.append(forum_plan_path)
    root_recovery_path = "runs/rw_parse_20260919/exhaustive_reddit_comments_v1/root_context_v1/manifest.json"
    resolve_reddit_root_holds(registry, root_recovery_path)
    attach_accepted_ledgers(registry, selected_path)
    rows = registry.finalize()
    workbook_path = root / "runs/rw_parse_20260919/program_workbooks_v1/manifest.json"
    workbook = _json(workbook_path) if workbook_path.is_file() else None
    forum_plan = _json(root / forum_plan_path) if (root / forum_plan_path).is_file() else None
    root_recovery = (_json(root / root_recovery_path)
                     if (root / root_recovery_path).is_file() else None)
    groups = _source_groups(audit, workbook, forum_plan, root_recovery)
    coverage = _summary(rows, audit, groups)
    return rows, groups, coverage, sorted(set(inputs))


def run(root: Path, out: Path) -> dict[str, Any]:
    rows, groups, coverage, inputs = build_inventory(root)
    if out.exists():
        raise ValueError(f"preserve existing inventory; choose a fresh output: {out}")
    out.mkdir(parents=True)
    sources_path = out / "sources.jsonl"
    sources_path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                                    for row in rows))
    census, unresolved = fresh_corpus_census(root.resolve(), rows)
    groups.append({
        "group_id": "fresh-census:unrepresented-source-like-paths",
        "count": len(unresolved),
        "census_state": "current_path_stat_only",
        "study_state": "needs_review",
        "contents_read": False,
        "list": "unrepresented_source_paths.jsonl",
    })
    coverage["source_groups"]["count"] = len(groups)
    coverage["fresh_metadata_only_census"] = {
        "path": "fresh_corpus_census.json",
        "current_on_disk_files": census["current_on_disk_files"],
        "unrepresented_source_like_paths": len(unresolved),
        "historical_denominator_replaced": False,
    }
    write(out / "source_groups.json", {"schema_version": "three-family-source-groups/2",
                                        "groups": groups})
    write(out / "coverage.json", coverage)
    write(out / "fresh_corpus_census.json", census)
    unresolved_path = out / "unrepresented_source_paths.jsonl"
    unresolved_path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                                       for row in unresolved))
    input_hashes = {path: digest((root / path).read_bytes()) for path in inputs}
    manifest = {
        "schema_version": "three-family-inventory-run/2",
        "status": "completed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "network_used": False,
        "hidden_truth_read": False,
        "benchmark_specs_read": False,
        "scores_read": False,
        "model_fits_read": False,
        "input_sha256": input_hashes,
        "source_sha256": digest(Path(__file__).read_bytes()),
        "outputs": {
            "sources.jsonl": digest(sources_path.read_bytes()),
            "source_groups.json": digest((out / "source_groups.json").read_bytes()),
            "coverage.json": digest((out / "coverage.json").read_bytes()),
            "fresh_corpus_census.json": digest((out / "fresh_corpus_census.json").read_bytes()),
            "unrepresented_source_paths.jsonl": digest(unresolved_path.read_bytes()),
        },
        "counts": {**coverage["registry"],
                   "fresh_corpus_census": census["counts"],
                   "fresh_unrepresented_source_paths": len(unresolved)},
    }
    write(out / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path,
                        default=Path("runs/three_family_20260920/inventory_v2"))
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else args.repo_root / args.out
    manifest = run(args.repo_root, out)
    print(json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
