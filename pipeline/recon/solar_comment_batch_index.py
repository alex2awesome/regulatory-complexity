#!/usr/bin/env python3
"""Index saved national Reddit comment pages without treating them as threads.

This is a local, mechanical bridge from ``list_comments`` receipts to priority
thread leads. It performs no retrieval and never writes under the full-tree
capture directory.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
from collections import defaultdict
from typing import Any

from pipeline.recon.solar_forum_collect import PROCESS_CLUES, clues

ROOT = pathlib.Path(__file__).resolve().parents[2]
ACQ = ROOT / "runs/solar_forum_20260922/acquisition"
PAGES = ACQ / "forum/national_comment_pages"
POSTS = ACQ / "forum/posts"
INDEX_OUT = ACQ / "comment_batch_index001.json"
LEADS_OUT = ACQ / "comment_batch_leads001.json"

def normalized(value: Any, prefix: str) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[len(prefix):] if text.lower().startswith(prefix) else text


def walk_comments(value: Any):
    if isinstance(value, dict):
        if value.get("id") and isinstance(value.get("body"), str):
            yield value
        for child in value.values():
            yield from walk_comments(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_comments(child)


def load_full_tree_ids(posts_dir: pathlib.Path) -> tuple[set[str], set[str]]:
    comment_ids: set[str] = set()
    post_ids: set[str] = set()
    for path in posts_dir.glob("*.json"):
        post_ids.add(normalized(path.stem, "t3_") or path.stem)
        value = json.loads(path.read_text(encoding="utf-8"))
        # Canonical refreshed captures keep the authoritative tree here.
        for comment in walk_comments(value.get("comments", [])):
            comment_ids.add(normalized(comment["id"], "t1_") or str(comment["id"]))
    return comment_ids, post_ids


def dump(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=pathlib.Path, default=PAGES)
    parser.add_argument("--posts", type=pathlib.Path, default=POSTS)
    parser.add_argument("--index-out", type=pathlib.Path, default=INDEX_OUT)
    parser.add_argument("--leads-out", type=pathlib.Path, default=LEADS_OUT)
    args = parser.parse_args()

    full_comment_ids, held_post_ids = load_full_tree_ids(args.posts.resolve())
    by_comment: dict[str, dict] = {}
    raw_rows = 0

    page_paths = sorted(args.pages.resolve().glob("**/*.json"))
    for page in page_paths:
        payload = page.read_bytes()
        value = json.loads(payload)
        page_hash = hashlib.sha256(payload).hexdigest()
        for index, row in enumerate(value.get("comments", [])):
            raw_rows += 1
            raw_id = str(row.get("id") or "")
            key = normalized(raw_id, "t1_")
            if not key:
                continue
            body = row.get("body") or ""
            # ``clues`` accepts a post plus comment rows; route the saved row as
            # a comment so its body/flair, rather than nonexistent title fields,
            # drives recall hints.
            clue_hits = clues({"subreddit": row.get("subreddit", "")}, [row])
            occurrence = {
                "path": str(page.relative_to(ROOT)),
                "json_path": f"$.comments[{index}]",
                "sha256": page_hash,
                "page_schema_version": value.get("schema_version"),
            }
            if key not in by_comment:
                by_comment[key] = {
                    "comment_id": key,
                    "raw_id": raw_id,
                    "link_id": normalized(row.get("link_id"), "t3_"),
                    "raw_link_id": row.get("link_id"),
                    "parent_id": normalized(row.get("parent_id"), "t1_")
                        if str(row.get("parent_id") or "").lower().startswith("t1_")
                        else normalized(row.get("parent_id"), "t3_"),
                    "raw_parent_id": row.get("parent_id"),
                    "parent_kind": ("unknown" if not row.get("parent_id") else
                        "post" if (str(row["parent_id"]).lower().startswith("t3_") or
                                   normalized(row["parent_id"], "t3_") == normalized(row.get("link_id"), "t3_"))
                        else "comment"),
                    "subreddit": row.get("subreddit"),
                    "author": row.get("author"),
                    "author_flair_text": row.get("author_flair_text"),
                    "body": body,
                    "created_utc": row.get("created_utc"),
                    "retrieved_on": row.get("retrieved_on"),
                    "score": row.get("score"),
                    "process_clue": bool(PROCESS_CLUES.search(body)),
                    "recall_clues": clue_hits,
                    "occurrences": [occurrence],
                }
            else:
                by_comment[key]["occurrences"].append(occurrence)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in by_comment.values():
        grouped[row.get("link_id") or "unknown"].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda r: (r.get("created_utc") or 0, r["comment_id"]))

    missing_parent_ids = sorted({
        row["parent_id"] for row in by_comment.values()
        if row["parent_kind"] == "comment" and row.get("parent_id") not in by_comment
    })
    overlap_ids = sorted(set(by_comment) & full_comment_ids)
    linked_posts = sorted(k for k in grouped if k != "unknown")
    index = {
        "schema_version": "solar-comment-batch-index/1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "completeness": "Partial dated comment windows only; not full threads, not fully read captures, and not occupancy/geography assignments.",
        "source_glob": str(args.pages.resolve().relative_to(ROOT)) + "/**/*.json",
        "normalization": "t1_ is removed only from comment keys; t3_ is removed only from grouped post keys. Raw IDs are retained.",
        "stats": {
            "source_pages": len(page_paths),
            "raw_rows": raw_rows,
            "unique_comments": len(by_comment),
            "duplicate_rows": raw_rows - len(by_comment),
            "linked_posts": len(linked_posts),
            "comments_overlapping_full_tree": len(overlap_ids),
            "linked_posts_with_full_tree_capture": len(set(linked_posts) & held_post_ids),
            "missing_parent_count": len(missing_parent_ids),
        },
        "overlap_with_full_tree_comment_ids": overlap_ids,
        "missing_parent_ids": missing_parent_ids,
        "posts": [
            {"post_id": post_id, "raw_link_ids": sorted({r["raw_link_id"] for r in grouped[post_id] if r.get("raw_link_id")}),
             "comment_count": len(grouped[post_id]), "comments": grouped[post_id]}
            for post_id in sorted(grouped)
        ],
    }

    lead_rows = []
    for post_id in linked_posts:
        if post_id in held_post_ids:
            continue
        matches = [r for r in grouped[post_id] if r["recall_clues"]]
        process_rows = [r for r in grouped[post_id] if r["process_clue"]]
        if matches and process_rows:
            lead_rows.append({
                "post_id": post_id,
                "url": f"https://www.reddit.com/comments/{post_id}/",
                "priority_comment_ids": [r["comment_id"] for r in matches],
                "process_comment_ids": [r["comment_id"] for r in process_rows],
                "recall_clues": sorted(set().union(*(set(r["recall_clues"]) for r in matches))),
                "basis": "Saved thread fragments jointly contain process and broad California clues, including weak abbreviations/place names. They need not occur in the same comment or author. This prioritizes retrieval only and does not assign any actor's location.",
            })
    leads = {
        "schema_version": "solar-comment-batch-leads/1",
        "completeness": "Priority URLs derived from partial comment windows; not full-thread captures and not labels.",
        "full_tree_captures_excluded": True,
        "enumerated_post_metadata_may_already_be_held": True,
        "lead_count": len(lead_rows),
        "leads": lead_rows,
    }
    dump(args.index_out.resolve(), index)
    dump(args.leads_out.resolve(), leads)
    print(json.dumps({"index": str(args.index_out), "leads": str(args.leads_out), **index["stats"], "priority_leads": len(lead_rows)}))


if __name__ == "__main__":
    main()
