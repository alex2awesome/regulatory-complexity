#!/usr/bin/env python3
"""Reddit retrieval for process reconnaissance, via the Arctic Shift archive API
(reddit.com's own JSON endpoints return 403 to scripts; pullpush.io is rate-limited).

Verified 2026-09-15:
  posts:    /api/posts/search?subreddit=X&query=Y&after=YYYY-MM-DD&limit=100   (keyword search needs subreddit or author)
  comments: /api/comments/tree?link_id=t3_<id>&limit=9999                       (full thread)
  comments: /api/comments/search?subreddit=X&body=Y&limit=100
Rate limit: ~1 req/s; a 422 "Timeout. Maybe slow down a bit" means back off.

CLI:
  python3 reddit_fetch.py search --sub bayarea --q "ADU amnesty" [--after 2024-01-01] [--limit 50] --out dir/
  python3 reddit_fetch.py thread --id 1abc23 --out dir/
  python3 reddit_fetch.py comments --sub Unemployment --q "identity verification" --out dir/
Each call writes JSON to --out (posts/<id>.json with the post + full comment tree when --with-comments).
"""
import argparse, json, pathlib, sys, time, urllib.parse, urllib.request

BASE = "https://arctic-shift.photon-reddit.com/api"
UA = {"User-Agent": "Mozilla/5.0 (research; regulatory-complexity process recon)"}
_last = [0.0]


def _get(path, params, retries=4):
    url = f"{BASE}{path}?{urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, '')})}"
    for i in range(retries):
        wait = 1.2 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.loads(f.read()).get("data") or []
        except urllib.error.HTTPError as e:
            body = e.read()[:200]
            if e.code in (422, 429, 503):
                time.sleep(3 * (i + 1))
                continue
            raise RuntimeError(f"{e.code} {url} {body}")
    return []


POST_FIELDS = ["id", "subreddit", "title", "selftext", "author", "created_utc", "score",
               "num_comments", "permalink", "url", "link_flair_text"]
COMMENT_FIELDS = ["id", "link_id", "parent_id", "subreddit", "author", "body", "created_utc", "score"]


def slim(d, fields):
    return {k: d.get(k) for k in fields if k in d}


def search_posts(subreddit, query=None, title=None, after=None, before=None, limit=100):
    return [slim(p, POST_FIELDS) for p in _get("/posts/search", {
        "subreddit": subreddit, "query": query, "title": title,
        "after": after, "before": before, "limit": min(limit, 100), "sort": "desc"})]


def search_comments(subreddit, body, after=None, limit=100):
    return [slim(c, COMMENT_FIELDS) for c in _get("/comments/search", {
        "subreddit": subreddit, "body": body, "after": after, "limit": min(limit, 100)})]


def _flatten(tree, out):
    for node in tree:
        d = node.get("data", node)
        if node.get("kind") == "more":
            continue
        out.append(slim(d, COMMENT_FIELDS))
        kids = d.get("replies") or node.get("children") or []
        if isinstance(kids, dict):
            kids = kids.get("data", {}).get("children", [])
        _flatten(kids, out)


def thread(post_id, limit=9999):
    lid = post_id if post_id.startswith("t3_") else f"t3_{post_id}"
    raw = _get("/comments/tree", {"link_id": lid, "limit": limit})
    out = []
    _flatten(raw, out)
    return out


def save_posts(posts, outdir, with_comments=True, max_comments_posts=40):
    outdir = pathlib.Path(outdir); (outdir / "posts").mkdir(parents=True, exist_ok=True)
    n = 0
    for p in posts:
        f = outdir / "posts" / f"{p['id']}.json"
        if f.exists():
            continue
        rec = dict(p)
        rec["created_iso"] = time.strftime("%Y-%m-%d", time.gmtime(p.get("created_utc") or 0))
        if with_comments and n < max_comments_posts and (p.get("num_comments") or 0) > 0:
            try:
                rec["comments"] = thread(p["id"])
            except Exception as e:  # keep going; note the failure
                rec["comments_error"] = str(e)[:200]
            n += 1
        f.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    idx = outdir / "index.jsonl"
    with idx.open("a") as fh:
        for p in posts:
            fh.write(json.dumps({k: p.get(k) for k in ["id", "subreddit", "title", "created_utc", "num_comments", "score"]}) + "\n")
    return len(posts)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("--sub", required=True); s.add_argument("--q"); s.add_argument("--title")
    s.add_argument("--after"); s.add_argument("--before"); s.add_argument("--limit", type=int, default=50)
    s.add_argument("--out", required=True); s.add_argument("--no-comments", action="store_true")
    t = sub.add_parser("thread"); t.add_argument("--id", required=True); t.add_argument("--out", required=True)
    c = sub.add_parser("comments"); c.add_argument("--sub", required=True); c.add_argument("--q", required=True)
    c.add_argument("--after"); c.add_argument("--limit", type=int, default=100); c.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "search":
        posts = search_posts(a.sub, query=a.q, title=a.title, after=a.after, before=a.before, limit=a.limit)
        n = save_posts(posts, a.out, with_comments=not a.no_comments)
        print(f"{n} posts from r/{a.sub} q={a.q!r} -> {a.out}/posts/")
        for p in posts[:15]:
            print(f"  {p['id']} {time.strftime('%Y-%m-%d', time.gmtime(p.get('created_utc') or 0))} c={p.get('num_comments')} {p.get('title','')[:90]}")
    elif a.cmd == "thread":
        cs = thread(a.id)
        out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / f"thread_{a.id}.json").write_text(json.dumps(cs, indent=1, ensure_ascii=False))
        print(f"{len(cs)} comments -> {out}/thread_{a.id}.json")
    elif a.cmd == "comments":
        cs = search_comments(a.sub, a.q, after=a.after, limit=a.limit)
        out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
        fn = out / f"comments_{a.sub}_{urllib.parse.quote_plus(a.q)[:40]}.json"
        fn.write_text(json.dumps(cs, indent=1, ensure_ascii=False))
        print(f"{len(cs)} comments -> {fn}")
        for c in cs[:10]:
            print("  -", (c.get("body") or "")[:120].replace("\n", " "))


if __name__ == "__main__":
    main()
