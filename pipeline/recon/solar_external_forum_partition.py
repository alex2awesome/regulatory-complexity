"""Partition captured SolarPanelTalk pages into readable posts.

Mechanical only: preserves quoted blocks as marked text and records source
hash/page/post identifiers. It does not assign location, actor, or timing
semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


def text_with_quote_markers(content):
    soup = BeautifulSoup(str(content), "html.parser")
    quotes = []
    for q in soup.select(".bbcode_quote"):
        qt = " ".join(q.get_text(" ", strip=True).split())
        quotes.append(qt)
        q.replace_with("\n[BEGIN QUOTED MATERIAL]\n" + qt + "\n[END QUOTED MATERIAL]\n")
    body = "\n".join(x.strip() for x in soup.get_text("\n").splitlines() if x.strip())
    return body, quotes


def parse_page(path: Path, url: str):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    soup = BeautifulSoup(raw, "html.parser")
    out = []
    for li in soup.select("li.b-post[data-node-id]"):
        pid = li.get("data-node-id")
        content = li.select_one(".js-post__content-text")
        if not pid or content is None:
            continue
        body, quotes = text_with_quote_markers(content)
        author = li.select_one('[itemprop="author"] [itemprop="name"]')
        date = li.select_one('[itemprop="publishDate"]')
        created = date.get("content") if date else None
        if not created and li.get("data-node-publishdate"):
            created = datetime.fromtimestamp(float(li["data-node-publishdate"]), timezone.utc).isoformat()
        out.append({
            "source_path": str(path), "source_sha256": digest, "source_url": url,
            "forum": "SolarPanelTalk", "post_id": pid,
            "post_number": li.select_one(".b-post__number" ).get_text(" ", strip=True) if li.select_one(".b-post__number") else None,
            "author": author.get_text(" ", strip=True) if author else None,
            "created_at": created, "body": body, "quote_blocks": quotes,
            "body_chars": len(body), "body_words": len(body.split()),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--text-dir", type=Path, required=True)
    args = ap.parse_args()
    args.text_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(args.raw_dir.glob("spt_*.bin")):
        key = path.stem
        # URL is carried in the sibling manifest when available; reconstruct
        # page URLs from the original lead manifest for stable provenance.
        url = None
        if "_p" not in key:
            m = json.loads(Path("runs/solar_forum_20260922/acquisition/external_leads002.json").read_text())
            url = next((x["url"] for x in m["records"] if x["id"] == key), None)
        else:
            base, page = key.rsplit("_p", 1)
            m = json.loads(Path("runs/solar_forum_20260922/acquisition/external_leads002.json").read_text())
            root = next(x["url"] for x in m["records"] if x["id"] == base)
            url = root.rstrip("/") + "/page" + page
        rows.extend(parse_page(path, url))
    # Stable page-readable text, with post boundaries and author/date labels.
    by_page = {}
    for row in rows:
        by_page.setdefault(row["source_path"], []).append(row)
    for src, posts in by_page.items():
        tp = args.text_dir / (Path(src).stem + ".txt")
        pos = 0
        chunks = []
        for row in posts:
            block = f"POST {row['post_id']}\nAUTHOR: {row['author']}\nDATE: {row['created_at']}\n\n{row['body']}\n\n"
            row["text_path"] = str(tp)
            row["text_char_start"] = pos
            pos += len(block)
            row["text_char_end"] = pos
            chunks.append(block)
        tp.write_text("".join(chunks), encoding="utf-8")
    args.out.write_text(json.dumps({
        "schema_version": 1, "interpretation": "Mechanical author/date/body partition; quoted material is marked and not reattributed; no semantic adoption.",
        "generated_at": datetime.now(timezone.utc).isoformat(), "posts": rows,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(by_page), "posts": len(rows), "out": str(args.out)}))


if __name__ == "__main__":
    main()
