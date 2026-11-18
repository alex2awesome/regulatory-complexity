#!/usr/bin/env python3
"""Render captured Reddit solar threads as readable, lossless Markdown.

Input records are the root collector's ``post`` + ``comments`` schema.  The
renderer deliberately reads only ``record['comments']`` (never a legacy
``post.comments`` field), retains every body verbatim, and emits a compact
manifest for downstream batching.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _words(value: str) -> int:
    return len(value.split())


def _timestamp(value: object) -> str:
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return "unknown"


def render(record: dict, source_path: Path, output_path: Path) -> dict:
    post = record.get("post") or {}
    comments = record.get("comments") or []
    post_body = _text(post.get("selftext"))
    raw = source_path.read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()

    lines = [
        "# " + (_text(post.get("title")) or "(untitled post)"),
        "",
        "- source file: `" + str(source_path) + "`",
        "- source sha256: `" + source_sha256 + "`",
        "- subreddit: `" + _text(post.get("subreddit")) + "`",
        "- post id: `" + _text(post.get("id")) + "`",
        "- post author: `" + _text(post.get("author")) + "`",
        "- post author flair (context only): `" + _text(post.get("author_flair_text")) + "`",
        "- post topic flair (not author location): `" + _text(post.get("link_flair_text")) + "`",
        "- post created UTC: `" + _timestamp(post.get("created_utc")) + "`",
        "- permalink: " + _text(post.get("permalink")),
        "",
        "## Original post",
        "",
        post_body,
        "",
        "## Comments",
        "",
    ]
    comment_chars = 0
    comment_words = 0
    for index, comment in enumerate(comments, 1):
        body = _text(comment.get("body"))
        comment_chars += len(body)
        comment_words += _words(body)
        lines.extend([
            f"### Comment {index}: `{_text(comment.get('id'))}`",
            "",
            "- author: `" + _text(comment.get("author")) + "`",
            "- author flair (context only): `" + _text(comment.get("author_flair_text")) + "`",
            "- parent_id: `" + _text(comment.get("parent_id")) + "`",
            "- link_id: `" + _text(comment.get("link_id")) + "`",
            "- subreddit: `" + _text(comment.get("subreddit")) + "`",
            "- created UTC: `" + _timestamp(comment.get("created_utc")) + "`",
            "- score: `" + _text(comment.get("score")) + "`",
            "",
            body,
            "",
        ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    total_chars = len(post_body) + comment_chars
    total_words = _words(post_body) + comment_words
    return {
        "id": _text(post.get("id")) or source_path.stem,
        "source_path": str(source_path),
        "rendered_path": str(output_path),
        "source_sha256": source_sha256,
        "title": _text(post.get("title")),
        "subreddit": _text(post.get("subreddit")),
        "post_author": _text(post.get("author")),
        "post_author_flair": _text(post.get("author_flair_text")),
        "post_topic_flair": _text(post.get("link_flair_text")),
        "post_chars": len(post_body),
        "post_words": _words(post_body),
        "comment_count": len(comments),
        "comment_chars": comment_chars,
        "comment_words": comment_words,
        "total_chars": total_chars,
        "total_words": total_words,
        "declared_num_comments": record.get("declared_num_comments", post.get("num_comments")),
        "returned_comment_count": record.get("returned_comment_count", len(comments)),
        "comment_status": record.get("comment_status"),
        "limit_reached": record.get("limit_reached"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for source_path in sorted(args.input.glob("*.json")):
        record = json.loads(source_path.read_bytes().decode("utf-8"))
        post_id = _text((record.get("post") or {}).get("id")) or source_path.stem
        rows.append(render(record, source_path, args.output / f"{post_id}.md"))
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({"schema_version": 1, "threads": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"rendered {len(rows)} threads")


if __name__ == "__main__":
    main()
