import json
from pathlib import Path

from pipeline.procbench.inventory_three_family_sources import (
    Registry,
    _row_aliases,
    _source_key,
    add_index,
    candidate_families,
    fresh_corpus_census,
)


def test_metadata_match_is_candidate_not_an_exclusion():
    assert candidate_families("corpus/counties/reddit_raw/askoc_calfresh.json") == ["calfresh"]
    assert candidate_families("CAguns") == ["ccw"]
    assert candidate_families("snapshot_of_county_files.json") == []
    assert candidate_families("local county subreddit") == []


def test_reddit_thread_id_is_not_misclassified_as_calguns_thread():
    assert _source_key("root_context", {
        "document_id": "reddit_root_context_abc_123", "thread_id": "abc"
    }) == ("reddit-thread:abc", "forum_thread")


def test_logical_source_hash_is_deterministic_across_alias_order(tmp_path):
    first = Registry(tmp_path)
    row = first.source("calguns-thread:123", "forum_thread")
    first.add_alias(row, path="raw/page2.html", role="physical_origin", sha256="b" * 64)
    first.add_alias(row, path="raw/page1.html", role="physical_origin", sha256="a" * 64)
    first.assign(row, "ccw", "included", "approved_program_freeze", "fixture")

    second = Registry(tmp_path)
    other = second.source("calguns-thread:123", "forum_thread")
    second.add_alias(other, path="raw/page1.html", role="physical_origin", sha256="a" * 64)
    second.add_alias(other, path="raw/page2.html", role="physical_origin", sha256="b" * 64)
    second.assign(other, "ccw", "included", "approved_program_freeze", "fixture")

    left, right = first.finalize()[0], second.finalize()[0]
    assert left["source_id"] == right["source_id"]
    assert left["content_sha256"] == right["content_sha256"]
    assert [item["path"] for item in left["physical_aliases"]] == [
        "raw/page1.html", "raw/page2.html"]


def test_direct_freeze_assignment_takes_precedence_over_heuristic(tmp_path):
    registry = Registry(tmp_path)
    row = registry.source("reddit-thread:abc", "forum_thread")
    registry.assign(row, "solar", "candidate", "metadata_keyword", "filename")
    registry.assign(row, "solar", "included", "approved_program_freeze", "freeze")
    registry.assign(row, "solar", "needs_review", "unassigned", "later generic pass")
    assignment = registry.finalize()[0]["family_assignments"][0]
    assert assignment == {
        "family": "solar",
        "state": "included",
        "method": "approved_program_freeze",
        "reason": "freeze",
        "semantic_relevance_accepted": False,
    }


def test_private_paths_are_not_added_as_aliases(tmp_path):
    registry = Registry(tmp_path)
    row = registry.source("fixture", "document")
    registry.add_alias(row, path="benchmark/world/truth/private.json",
                       role="physical_origin", sha256="a" * 64)
    registry.add_alias(row, path="corpus/realworld/_gold/labels.json",
                       role="physical_origin", sha256="b" * 64)
    assert registry.finalize()[0]["physical_aliases"] == []


def test_output_row_keeps_unresolved_review_state(tmp_path):
    registry = Registry(tmp_path)
    row = registry.source("reddit-thread:xyz", "forum_thread")
    for family in ("solar", "ccw", "calfresh"):
        registry.assign(row, family, "needs_review", "unassigned_mixed_capture",
                        "not a semantic exclusion")
    result = registry.finalize()[0]
    assert {item["state"] for item in result["family_assignments"]} == {"needs_review"}
    assert result["accepted_ledger_links"] == []


def test_declared_hash_is_separate_from_replayed_hash_and_mismatch_blocks(tmp_path):
    physical = tmp_path / "source.txt"
    physical.write_text("actual bytes")
    registry = Registry(tmp_path)
    row = registry.source("fixture", "document")
    registry.add_alias(row, path="source.txt", role="physical_origin",
                       sha256="0" * 64, byte_count=99)
    result = registry.finalize()[0]
    alias = result["physical_aliases"][0]
    assert alias["declared_sha256"] == "0" * 64
    assert alias["actual_sha256"] != alias["declared_sha256"]
    assert alias["actual_bytes"] == len("actual bytes")
    assert alias["hash_status"] == "declared_hash_mismatch"
    assert result["holds"][0]["code"] == "declared_hash_mismatch"


def test_derived_artifact_does_not_reuse_frozen_source_hash(tmp_path):
    base = tmp_path / "freeze"
    (base / "source").mkdir(parents=True)
    (base / "artifacts").mkdir()
    (base / "source" / "doc.txt").write_text("frozen")
    (base / "artifacts" / "doc.md").write_text("rendered differently")
    frozen_hash = __import__("hashlib").sha256(b"frozen").hexdigest()
    registry = Registry(tmp_path)
    source = registry.source("fixture", "document")
    _row_aliases(registry, source, "fixture",
                 {"doc_id": "doc", "sha256": frozen_hash},
                 "freeze/frozen_index.json")
    aliases = {item["role"]: item for item in registry.finalize()[0]["physical_aliases"]}
    assert aliases["frozen_rendering"]["declared_sha256"] == frozen_hash
    assert aliases["frozen_rendering"]["hash_status"] == "verified_match"
    assert aliases["artifact_rendering"]["declared_sha256"] is None
    assert aliases["artifact_rendering"]["hash_status"] == "observed_no_declared_hash"


def test_mixed_workbook_freeze_does_not_assign_other_benefit_to_calfresh(tmp_path):
    manifest = tmp_path / "workbooks" / "manifest.json"
    manifest.parent.mkdir()
    calfresh = tmp_path / "calfresh_cf18.xlsx"
    calworks = tmp_path / "calworks_ca237.xlsx"
    calfresh.write_bytes(b"cf")
    calworks.write_bytes(b"cw")
    manifest.write_text(json.dumps({
        "process": "program_workbooks_v1",
        "documents": [
            {"document_id": "cf", "source_path": "calfresh_cf18.xlsx",
             "source_sha256": __import__("hashlib").sha256(b"cf").hexdigest()},
            {"document_id": "cw", "source_path": "calworks_ca237.xlsx",
             "source_sha256": __import__("hashlib").sha256(b"cw").hexdigest()},
        ],
    }))
    registry = Registry(tmp_path)
    add_index(registry, "workbooks/manifest.json", family=None, state="candidate",
              method="registered_source_metadata", unresolved_if_no_match=True)
    rows = registry.finalize()
    cf = next(row for row in rows if row["physical_aliases"][0]["path"] == "calfresh_cf18.xlsx")
    cw = next(row for row in rows if row["physical_aliases"][0]["path"] == "calworks_ca237.xlsx")
    assert cf["family_assignments"] == [{
        "family": "calfresh", "state": "candidate", "method": "metadata_keyword",
        "reason": "filename, capture-query or subreddit metadata match; human review required",
        "semantic_relevance_accepted": False,
    }]
    assert {item["state"] for item in cw["family_assignments"]} == {"needs_review"}


def test_historical_hold_is_retained_when_later_receipt_resolves_it(tmp_path):
    registry = Registry(tmp_path)
    row = registry.source("calguns-thread:1", "forum_thread")
    registry.add_hold(row, {"code": "missing_thread_pages", "ranges": ["2-4"],
                            "status": "historical_observation", "effective_status": "open",
                            "blocking_complete_coverage": True})
    registry.resolve_hold(row, "missing_thread_pages",
                          {"state": "resolved_in_later_freeze", "receipt_path": "plan.json"})
    hold = registry.finalize()[0]["holds"][0]
    assert hold["ranges"] == ["2-4"]
    assert hold["effective_status"] == "resolved"
    assert hold["resolution"]["receipt_path"] == "plan.json"


def test_fresh_census_lists_unrepresented_without_private_or_cache_paths(tmp_path):
    (tmp_path / "corpus/raw").mkdir(parents=True)
    (tmp_path / "corpus/realworld/_gold").mkdir(parents=True)
    (tmp_path / "corpus/__pycache__").mkdir(parents=True)
    (tmp_path / "corpus/raw/represented.pdf").write_bytes(b"represented")
    (tmp_path / "corpus/raw/unrepresented.pdf").write_bytes(b"unrepresented")
    (tmp_path / "corpus/realworld/_gold/labels.json").write_text("private")
    (tmp_path / "corpus/__pycache__/cached.pyc").write_bytes(b"cache")
    (tmp_path / "corpus/helper.py").write_text("support")
    registry = Registry(tmp_path)
    row = registry.source("represented", "document")
    registry.add_alias(row, path="corpus/raw/represented.pdf", role="physical_origin")
    census, unresolved = fresh_corpus_census(tmp_path, registry.finalize())
    assert census["current_on_disk_files"] == 5
    assert census["counts"] == {
        "excluded_hidden_or_cache": 1,
        "excluded_non_source_support": 1,
        "excluded_private_or_gold": 1,
        "represented_source_path": 1,
        "unrepresented_source_like_path": 1,
    }
    assert [item["path"] for item in unresolved] == ["corpus/raw/unrepresented.pdf"]
    assert unresolved[0]["contents_read"] is False
