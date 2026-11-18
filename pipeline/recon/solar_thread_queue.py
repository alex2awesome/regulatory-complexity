#!/usr/bin/env python3
"""Build deterministic review accounting for captured solar Reddit trees/posts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

try:
    from .solar_forum_collect import clues, BURDEN_PRIORITY
except ImportError:
    from solar_forum_collect import clues, BURDEN_PRIORITY


def post_view(record: dict) -> dict:
    # Full-tree capture schema wraps a compact post; discovery files are raw post objects.
    return record.get("post") if isinstance(record.get("post"), dict) else record


def comments_view(record: dict) -> list[dict]:
    comments = record.get("comments")
    return comments if isinstance(comments, list) else []


def text_size(post: dict, comments: list[dict]) -> tuple[int, int]:
    text = "\n".join([str(post.get("title") or ""), str(post.get("selftext") or "")] + [str(c.get("body") or "") for c in comments])
    return len(text), len(text.split())


def read_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    if path.suffix == ".json":
        data = json.loads(path.read_bytes().decode("utf-8"))
        return set(data.get("threads", [])) if isinstance(data, dict) else set(data)
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.search(r"`([a-z0-9]+)`", line)
        if m:
            ids.add(m.group(1))
    return ids


def read_reviewed_coverage(paths: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in paths:
        data = json.loads(Path(raw).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # Thread-level adoption declarations take precedence over episode
            # rows, which may repeat one thread many times.
            entries = data.get("threads") if data.get("threads") is not None else data.get("episodes", [])
        else:
            entries = data
        for item in entries:
            if isinstance(item, str):
                # A list of thread IDs proves neither scientific adoption nor
                # model consumption; inherit the explicit packet state instead.
                tid, state = item, (data.get("adoption_state", "reviewed_adoption_unspecified")
                                    if isinstance(data,dict) else "reviewed_adoption_unspecified")
            else:
                tid = item.get("thread_id") or item.get("thread") or item.get("review_metadata", {}).get("thread_id")
                state = item.get("adoption_state") or item.get("status")
                if not state:
                    raise ValueError(f"reviewed coverage entry lacks explicit adoption_state/status: {raw}: {item}")
                label = str(item.get("coverage_label", ""))
                if state.lower().startswith("adopted") and label and not re.search(r"reviewed_with(?:_one_or_more)?_episode", label):
                    state = "reviewed_out_of_frame_" + state
            if tid:
                out[str(tid)] = str(state)
    return out


def run(args: argparse.Namespace) -> dict:
    root = Path(args.root)
    sources: dict[str, dict] = {}
    duplicates = []
    # Full-tree capture wins across all held roots; discovery is fallback only.
    directories = [
        ("discovered_post", root / "discovered_posts", 3),
        ("full_tree", root / "posts", 4),
        ("legacy_post", Path(__file__).resolve().parents[2] / "corpus/realworld/solar_permit/reddit/posts", 1),
        ("discovery_post", Path(__file__).resolve().parents[2] / "runs/solar_forum_20260922/reddit_discovery/posts", 2),
        ("national_post", root / "national_posts", 1),
    ]
    for kind, directory, rank in directories:
        for path in sorted(directory.glob("*.json")):
            record = json.loads(path.read_bytes().decode("utf-8"))
            post = post_view(record)
            tid = str(post.get("id") or path.stem)
            comments = comments_view(record)
            # Only the acquisition root/posts contract declares a full tree;
            # embedded comments in legacy partial captures do not upgrade them.
            effective_kind = kind
            candidate = {"id": tid, "kind": effective_kind, "rank": rank, "path": str(path), "record": record, "post": post, "comments": comments}
            if tid in sources:
                if rank > sources[tid]["rank"]:
                    duplicates.append({"id": tid, "discarded": sources[tid]["path"], "preferred": str(path)})
                    sources[tid] = candidate
                else:
                    duplicates.append({"id": tid, "discarded": str(path), "preferred": sources[tid]["path"]})
            else:
                sources[tid] = candidate

    root_decisions = read_ids(Path(args.root_decisions))
    sol001 = read_ids(Path(args.sol001))
    sol002 = read_ids(Path(args.sol002))
    reviewed = read_reviewed_coverage(args.reviewed_coverage)
    rows = []
    for tid in sorted(sources):
        item = sources[tid]; post = item["post"]; comments = item["comments"]
        if tid in reviewed:
            state = reviewed[tid].lower().replace(" ", "_")
            status = state if state.startswith(("adopted", "staged", "reviewed_")) else f"reviewed_{state}"
        elif tid in root_decisions:
            status = "adopted_root"
        elif tid in sol001:
            status = "adopted_SOL001"
        elif tid in sol002:
            status = "staged_SOL002"
        elif item["kind"] == "full_tree":
            status = "unread"
        else:
            status = "comment_fetch_pending"
        chars, words = text_size(post, comments)
        process_text="\n".join([str(post.get("title") or ""),str(post.get("selftext") or "")]
                               +[str(c.get("body") or "") for c in comments])
        rows.append({
            "thread_id": tid, "status": status, "source_kind": item["kind"], "source_path": item["path"],
            "subreddit": post.get("subreddit"), "title": post.get("title"), "author": post.get("author"),
            "permalink": post.get("permalink"), "declared_comments": item["record"].get("declared_num_comments", post.get("num_comments")),
            "returned_comments": len(comments), "comments_missing": item["kind"] != "full_tree",
            "capture_completeness": "full_tree" if item["kind"] == "full_tree" else "post_only_or_comments_missing",
            "california_screening_clues": clues(post, comments), "body_chars": chars, "body_words": words,
            "process_priority_clue": bool(BURDEN_PRIORITY.search(process_text)),
        })

    # Only unread full trees are runnable. Discovery/post-only records are a
    # separate acquisition queue and adopted/staged records are not reread.
    ordered = sorted([r for r in rows if r["status"] == "unread" and not r["comments_missing"]], key=lambda r: (-r["process_priority_clue"], -bool(r["california_screening_clues"]), r["thread_id"]))
    batch_dir = Path(args.output) / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    batches = []
    current, current_chars = [], 0
    for row in ordered:
        if current and current_chars + row["body_chars"] > args.batch_chars:
            number = len(batches) + 1
            path = batch_dir / f"batch_{number:03d}.json"
            path.write_text(json.dumps({"batch": number, "target_chars": args.batch_chars, "estimated_chars": current_chars, "threads": current}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            batches.append({"batch": number, "path": str(path), "threads": len(current), "estimated_chars": current_chars})
            current, current_chars = [], 0
        current.append(row); current_chars += row["body_chars"]
    if current:
        number = len(batches) + 1; path = batch_dir / f"batch_{number:03d}.json"
        path.write_text(json.dumps({"batch": number, "target_chars": args.batch_chars, "estimated_chars": current_chars, "threads": current}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        batches.append({"batch": number, "path": str(path), "threads": len(current), "estimated_chars": current_chars})

    counts = Counter(row["status"] for row in rows)
    clue_counts = Counter()
    for row in rows:
        if row["comments_missing"]:
            clue_counts["comments_missing_with_clues" if row["california_screening_clues"] else "comments_missing_without_clues"] += 1
        else:
            clue_counts["comments_present_with_clues" if row["california_screening_clues"] else "comments_present_without_clues"] += 1
    discovery_pending = [r for r in rows if r["status"] == "comment_fetch_pending"]
    staged_or_adopted = [r for r in rows if r["status"].startswith(("adopted", "staged"))]
    Path(args.output, "discovery_only_awaiting_comments.json").write_text(json.dumps({"threads": discovery_pending}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output, "adopted_or_staged.json").write_text(json.dumps({"threads": staged_or_adopted}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    selected = {r["thread_id"] for r in staged_or_adopted}
    leads = []
    for tid in sorted(selected):
        item = sources[tid]; post = item["post"]
        source_path = Path(item["path"]); source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        post_hits = clues(post, [])
        leads.append({"thread_id": tid, "source_path": str(source_path), "sha256": source_hash, "comment_id": None, "author": post.get("author"), "lexicon_hits": post_hits, "subreddit_context": post.get("subreddit"), "context_is_not_location": True})
        for comment in item["comments"]:
            leads.append({"thread_id": tid, "source_path": str(source_path), "sha256": source_hash, "comment_id": comment.get("id"), "author": comment.get("author"), "lexicon_hits": clues(post, [comment]), "subreddit_context": post.get("subreddit"), "context_is_not_location": True})
    Path(args.output, "clue_leads.json").write_text(json.dumps({"schema_version": 1, "scope": "captured reviewed/staged threads only; lexicon clues do not establish author location", "leads": leads}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output = {"schema_version": 2, "canonical_thread_count": len(rows), "duplicate_count": len(duplicates), "status_counts": dict(sorted(counts.items())), "screening_accounting": dict(clue_counts), "adopted_expected": {"root": len(root_decisions), "SOL001": len(sol001), "SOL002": len(sol002), "reviewed_coverage": len(reviewed)}, "duplicates": duplicates, "batches": batches, "discovery_only_awaiting_comments": len(discovery_pending), "adopted_or_staged": len(staged_or_adopted), "threads": rows}
    Path(args.output).mkdir(parents=True, exist_ok=True)
    Path(args.output, "thread_queue.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--root", required=True); p.add_argument("--output", required=True); p.add_argument("--root-decisions", required=True); p.add_argument("--sol001", required=True); p.add_argument("--sol002", required=True); p.add_argument("--reviewed-coverage", action="append", default=[], help="JSON file(s) with explicit threads/episodes and adoption state"); p.add_argument("--batch-chars", type=int, default=40000)
    out = run(p.parse_args()); print(json.dumps({"threads": out["canonical_thread_count"], "duplicates": out["duplicate_count"], "status_counts": out["status_counts"], "batches": len(out["batches"])}, indent=2))


if __name__ == "__main__": main()
