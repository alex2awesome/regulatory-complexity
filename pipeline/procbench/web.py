#!/usr/bin/env python3
"""Mock web over a synthetic world (benchmark/synth/DESIGN.md §"Mock web API").

Build:   python3 pipeline/procbench/web.py --world W1 build
Serve:   python3 pipeline/procbench/web.py --world W1 search "unit legalization Halvern"
         python3 pipeline/procbench/web.py --world W1 fetch <url> [--max-chars 8000]
         python3 pipeline/procbench/web.py --world W1 reddit search "..." [--sub r/Halvern]
         python3 pipeline/procbench/web.py --world W1 reddit thread <thread_id>

Every call is traced to runs/<run_id>/trace.jsonl when --run-id (or $PROCBENCH_RUN)
is set. --condition applies the information-condition filter (see HIDE below).
Stdlib only; BM25 is implemented here.
"""

import argparse
import datetime as dt
import json
import math
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
WORLDS_ROOT = REPO / "benchmark" / "synth" / "worlds"
RUNS_ROOT = REPO / "runs"

REDDIT_KINDS = {"reddit_thread", "forum_thread"}
DESIGNED_KINDS = {"staff_report", "sop", "audit_excerpt"}
# Information conditions -> artifact kinds hidden from search AND fetch.
# `search` is the full agentic condition: everything public is reachable; an
# employee SOP counts as public only if its spec marks it published.
# oracle_* conditions are executed by solve.py (docs handed over directly); the
# filters here are their web-side analogue so the CLI is usable in every mode.
HIDE = {
    "search": set(),
    "oracle_docs": set(),
    "oracle_no_distractors": set(),
    "declared_only": REDDIT_KINDS | DESIGNED_KINDS | {"news", "council_minutes"},
    "declared_plus_users": set(DESIGNED_KINDS),
}
CONDITIONS = list(HIDE)
STOP = set("a an the of for to in on at and or is are be as by with from this that it "
           "how do does i my you your what when where which who whom about if then than".split())


# ------------------------------------------------------------------ BM25 (~40 lines)

def tokenize(text):
    out = []
    for t in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if t in STOP or len(t) < 2:
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]                                      # crude singulariser
        out.append(t)
    return out


def bm25_build(docs):
    """docs: [{"id","title","text"}] -> index dict (JSON-serialisable)."""
    idx = {"df": {}, "docs": {}, "N": 0, "avgdl": 0.0}
    total = 0
    for d in docs:
        toks = tokenize(d.get("title", "")) * 3 + tokenize(d.get("text", ""))
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        idx["docs"][d["id"]] = {"tf": tf, "dl": len(toks)}
        for t in tf:
            idx["df"][t] = idx["df"].get(t, 0) + 1
        total += len(toks)
    idx["N"] = len(docs)
    idx["avgdl"] = (total / len(docs)) if docs else 0.0
    return idx



OPERATOR_RE = re.compile(r'(-?)(site|filetype|inurl|intitle):(\S+)', re.I)
PHRASE_RE = re.compile(r'"([^"]{2,})"')


def parse_query(q):
    """Split a real-search-shaped query into BM25 terms plus the operators a live engine honours.

    Real agents write `site:halvern.gov "Unit Legalization Program" -draft`. A bag-of-words index that
    ignores operators silently punishes that, so the mock honours them: `site:`/`inurl:` and `filetype:`
    filter, `intitle:` boosts, quoted spans must appear verbatim, a leading `-` excludes. Whatever is
    left becomes the scoring terms. Usage is recorded so operator reliance can be reported.
    """
    ops = {"site": [], "not_site": [], "filetype": [], "inurl": [], "intitle": [], "phrases": [], "not_terms": []}
    rest = q
    for sign, key, val in OPERATOR_RE.findall(q):
        key = key.lower(); val = val.strip('"').lower()
        if key in ("site", "inurl"):
            ops["not_site" if sign == "-" else ("site" if key == "site" else "inurl")].append(val)
        else:
            ops[key].append(val)
    rest = OPERATOR_RE.sub(" ", rest)
    for ph in PHRASE_RE.findall(rest):
        ops["phrases"].append(ph.lower())
    rest = PHRASE_RE.sub(" ", rest)
    terms = []
    for w in rest.split():
        if w.upper() == "OR":
            continue
        if w.startswith("-") and len(w) > 1:
            ops["not_terms"].append(w[1:].lower())
        else:
            terms.append(w)
    ops["used"] = sorted(k for k, v in ops.items() if k != "used" and v)
    return " ".join(terms) or q, ops


def passes_ops(doc, ops):
    url = (doc.get("url") or "").lower()
    title = (doc.get("title") or "").lower()
    text = (doc.get("text") or "").lower()
    if ops["site"] or ops["inurl"]:
        want = ops["site"] + ops["inurl"]
        if not any(w in url for w in want):
            return False
    if any(w in url for w in ops["not_site"]):
        return False
    if ops["filetype"] and not any(url.endswith("." + f.lstrip(".")) for f in ops["filetype"]):
        return False
    for ph in ops["phrases"]:
        if ph not in text and ph not in title:
            return False
    for w in ops["not_terms"]:
        if w in text or w in title:
            return False
    return True


# A live engine ranks an official domain above a forum for a permit query; BM25 alone has no such prior.
AUTHORITY = {"program_page": 1.35, "generic_permits_page": 1.2, "faq": 1.2, "form": 1.15, "checklist": 1.15,
             "fee_schedule": 1.15, "fee_resolution": 1.1, "ordinance": 1.1, "official_stats": 1.1,
             "staff_report": 1.05, "council_minutes": 1.0, "bill_analysis": 1.0, "audit_excerpt": 1.0,
             "sop": 0.95, "third_party_guide": 0.9, "news": 0.9, "reddit_thread": 0.8, "forum_thread": 0.75}

def bm25_search(idx, query, allowed=None, k=10, k1=1.4, b=0.75):
    """-> [(doc_id, score)] best first. `allowed`: set of doc ids to consider."""
    q = tokenize(query)
    N, avgdl = max(idx["N"], 1), max(idx["avgdl"], 1.0)
    scored = []
    for doc_id, d in idx["docs"].items():
        if allowed is not None and doc_id not in allowed:
            continue
        s = 0.0
        for t in q:
            f = d["tf"].get(t)
            if not f:
                continue
            df = idx["df"].get(t, 0)
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d["dl"] / avgdl))
        if s > 0:
            scored.append((doc_id, round(s, 4)))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored[:k]


# ------------------------------------------------------------------ artifacts

def parse_artifact(path):
    """`---` front matter (key: value lines) then body -> (meta, body)."""
    raw = pathlib.Path(path).read_text()
    meta, body = {}, raw
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n?(.*)\Z", raw, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip().lstrip("- ")] = val.strip().strip('"')
        body = m.group(2)
    return meta, body.strip()


def _norm_url(u):
    return (u or "").strip().rstrip("/").lower()


def build(world_dir):
    """artifacts/ + specs/ -> web/pages.jsonl, web/reddit.jsonl, web/links.jsonl, web/bm25.json."""
    world_dir = pathlib.Path(world_dir)
    specs = {}
    for p in sorted((world_dir / "specs").glob("*.json")):
        try:
            s = json.loads(p.read_text())
        except Exception:
            continue
        specs[s.get("artifact_id", p.stem)] = s
    docs = []
    for p in sorted((world_dir / "artifacts").glob("*.md")):
        if p.name.endswith(".verify.json"):
            continue
        aid = p.name[: -len(".md")]
        meta, body = parse_artifact(p)
        spec = specs.get(aid, {})
        kind = spec.get("kind") or meta.get("kind") or "page"
        doc = {
            "id": aid, "url": spec.get("url") or meta.get("url") or f"https://example.invalid/{aid}",
            "kind": kind, "title": meta.get("title") or aid.replace("__", " "),
            "date": spec.get("date") or meta.get("date") or "", "jur": spec.get("jur") or meta.get("jur") or "",
            "stat_id": spec.get("stat_id") or meta.get("stat_id") or "",
            "target": bool(spec.get("target", True)),
            "published": bool(spec.get("published", spec.get("audience") in ("public", "applicant", "council"))),
            "stale": bool(spec.get("stale", False)),
            "subreddit": meta.get("subreddit", ""), "thread_id": meta.get("thread_id") or aid,
            "links_to": list(spec.get("links_to") or []), "text": body,
        }
        docs.append(doc)
    by_url = {_norm_url(d["url"]): d["id"] for d in docs}
    by_id = {d["id"]: d for d in docs}
    # outgoing links: spec links_to (artifact ids) + any in-world url mentioned in the text
    links = []
    for d in docs:
        outs = []
        for tgt in d["links_to"]:
            if tgt in by_id:
                outs.append(by_id[tgt]["url"])
        for u in re.findall(r"https?://[^\s)\]\"'>,]+", d["text"]):
            tid = by_url.get(_norm_url(u))
            if tid and tid != d["id"] and by_id[tid]["url"] not in outs:
                outs.append(by_id[tid]["url"])
        d["links"] = outs
        links += [{"from_id": d["id"], "from_url": d["url"], "to_url": u, "to_id": by_url[_norm_url(u)]}
                  for u in outs]
    web = world_dir / "web"
    web.mkdir(parents=True, exist_ok=True)
    pages = [d for d in docs if d["kind"] not in REDDIT_KINDS]
    threads = [d for d in docs if d["kind"] in REDDIT_KINDS]
    for name, rows in (("pages", pages), ("reddit", threads), ("links", links)):
        (web / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (web / "bm25.json").write_text(json.dumps(bm25_build(docs)))
    return {"pages": len(pages), "reddit": len(threads), "links": len(links),
            "targets": sum(1 for d in docs if d["target"]), "world": world_dir.name}


# ------------------------------------------------------------------ the web

class World:
    """Query interface used by both the CLI and solve.py (import, don't shell out)."""

    def __init__(self, world, condition="search", run_id=None, worlds_root=None, runs_root=None):
        cand = pathlib.Path(worlds_root or WORLDS_ROOT) / world
        self.dir = cand if cand.is_dir() else pathlib.Path(world)     # id, or a path to a world dir
        if not self.dir.is_dir():
            raise SystemExit(f"no such world: {self.dir}")
        self.world = self.dir.name
        if condition not in HIDE:
            raise SystemExit(f"unknown condition {condition!r}; pick from {CONDITIONS}")
        self.condition = condition
        self.run_id = run_id or os.environ.get("PROCBENCH_RUN") or None
        self.runs_root = pathlib.Path(runs_root or os.environ.get("PROCBENCH_RUNS_ROOT") or RUNS_ROOT)
        if not (self.dir / "web" / "pages.jsonl").exists():
            build(self.dir)
        self.docs = {}
        for name in ("pages", "reddit"):
            p = self.dir / "web" / f"{name}.jsonl"
            for line in p.read_text().splitlines() if p.exists() else []:
                d = json.loads(line)
                self.docs[d["id"]] = d
        bm = self.dir / "web" / "bm25.json"
        self.idx = json.loads(bm.read_text()) if bm.exists() else bm25_build(list(self.docs.values()))

    # -- condition filter -------------------------------------------------
    def visible(self, doc):
        kind = doc.get("kind", "")
        if kind in HIDE[self.condition]:
            return False
        if kind == "sop" and not doc.get("published") and self.condition != "oracle_docs":
            return False                                    # unpublished SOP: staff-only
        if self.condition == "oracle_no_distractors" and not doc.get("target", True):
            return False
        return True

    def visible_ids(self, reddit_only=False, sub=None):
        out = set()
        for d in self.docs.values():
            if not self.visible(d):
                continue
            if reddit_only and d["kind"] not in REDDIT_KINDS:
                continue
            if sub and sub.strip("/ ").lower().removeprefix("r/") not in d.get("subreddit", "").lower():
                continue
            out.add(d["id"])
        return out

    # -- tracing ----------------------------------------------------------
    def trace(self, op, args, result_ids):
        if not self.run_id:
            return
        d = self.runs_root / self.run_id
        d.mkdir(parents=True, exist_ok=True)
        with (d / "trace.jsonl").open("a") as fh:
            fh.write(json.dumps({"ts": dt.datetime.now().isoformat(timespec="seconds"),
                                 "condition": self.condition, "op": op, "args": args,
                                 "result_ids": result_ids}) + "\n")

    # -- operations -------------------------------------------------------
    def search(self, query, k=10, reddit_only=False, sub=None):
        terms, ops = parse_query(query)
        allowed = self.visible_ids(reddit_only, sub)
        if any(ops[o] for o in ("site", "inurl", "not_site", "filetype", "phrases", "not_terms")):
            allowed = {i for i in allowed if passes_ops(self.docs[i], ops)}
        hits = bm25_search(self.idx, terms, allowed, k * 3)
        boost = lambda i: AUTHORITY.get(self.docs[i].get("kind"), 1.0) * (
            1.25 if ops["intitle"] and any(w in (self.docs[i].get("title") or "").lower() for w in ops["intitle"]) else 1.0)
        hits = sorted(((i, round(s * boost(i), 4)) for i, s in hits), key=lambda x: (-x[1], x[0]))[:k]
        res = [{"url": self.docs[i]["url"], "title": self.docs[i]["title"], "kind": self.docs[i]["kind"],
                "date": self.docs[i]["date"], "score": s, "artifact_id": i,
                "subreddit": self.docs[i].get("subreddit", ""), "thread_id": self.docs[i].get("thread_id", ""),
                "snippet": snippet(self.docs[i]["text"], query)} for i, s in hits]
        self.trace("reddit_search" if reddit_only else "search",
                   {"query": query, "k": k, "sub": sub, "operators": ops["used"]},
                   [r["artifact_id"] for r in res])
        return res

    def fetch(self, url, max_chars=12000):
        for d in self.docs.values():
            if _norm_url(d["url"]) == _norm_url(url) and self.visible(d):
                self.trace("fetch", {"url": url}, [d["id"]])
                text = d["text"]
                return {"url": d["url"], "title": d["title"], "kind": d["kind"], "date": d["date"],
                        "artifact_id": d["id"], "links": d.get("links", []),
                        "truncated": len(text) > max_chars, "text": text[:max_chars]}
        self.trace("fetch", {"url": url}, [])
        return {"url": url, "error": "404 Not Found — no such page on this web "
                                     "(check the url, or it is not reachable in this condition)"}

    def thread(self, thread_id, max_chars=12000):
        key = thread_id.strip().lstrip("/").removeprefix("t_").lower()
        for d in self.docs.values():
            if d["kind"] not in REDDIT_KINDS:
                continue
            if key in (d.get("thread_id", "").lower().removeprefix("t_"), d["id"].lower()) and self.visible(d):
                self.trace("reddit_thread", {"thread_id": thread_id}, [d["id"]])
                return {"thread_id": d.get("thread_id"), "url": d["url"], "title": d["title"], "kind": d["kind"],
                        "subreddit": d.get("subreddit", ""), "date": d["date"], "artifact_id": d["id"],
                        "truncated": len(d["text"]) > max_chars, "text": d["text"][:max_chars]}
        self.trace("reddit_thread", {"thread_id": thread_id}, [])
        return {"thread_id": thread_id, "error": "404 Not Found — no such thread in this condition"}

    # -- oracle ------------------------------------------------------------
    def oracle_docs(self, jur, stat_id, query="", budget_chars=120000, include_distractors=True):
        """Task docs (target & same jur/statute) first, then other visible docs by BM25
        as contamination, up to the char budget."""
        task = [d for d in self.docs.values()
                if d.get("target", True) and d.get("jur") == jur and d.get("stat_id") == stat_id]
        task.sort(key=lambda d: (d["kind"] != "program_page", d["id"]))
        out, used = [], 0
        for d in task:
            out.append(d)
            used += len(d["text"])
        if include_distractors:
            rest = {d["id"] for d in self.docs.values() if self.visible(d)} - {d["id"] for d in task}
            for did, _ in bm25_search(self.idx, query or f"{jur} {stat_id}", rest, k=50):
                d = self.docs[did]
                if used + len(d["text"]) > budget_chars:
                    continue
                out.append(d)
                used += len(d["text"])
        self.trace("oracle_docs", {"jur": jur, "stat_id": stat_id, "distractors": include_distractors},
                   [d["id"] for d in out])
        return out


def snippet(text, query, width=150):
    flat = re.sub(r"\s+", " ", text)
    terms = set(tokenize(query))
    low = flat.lower()
    pos = min((low.find(t) for t in terms if low.find(t) >= 0), default=-1)
    if pos < 0:
        return flat[: width * 2] + ("…" if len(flat) > width * 2 else "")
    a = max(0, pos - width // 2)
    return ("…" if a else "") + flat[a: a + width * 2] + ("…" if a + width * 2 < len(flat) else "")


# ------------------------------------------------------------------ CLI

def render(obj):
    if isinstance(obj, list):
        if not obj:
            return "no results"
        return "\n".join(
            f"[{i+1}] {r['title']}\n    url: {r['url']}   kind: {r['kind']}  date: {r['date']}"
            + (f"  {r['subreddit']} thread_id: {r['thread_id']}" if r.get("subreddit") else "")
            + f"\n    {r['snippet']}" for i, r in enumerate(obj))
    if obj.get("error"):
        return obj["error"]
    head = f"# {obj['title']}\nurl: {obj['url']}\nkind: {obj['kind']}  date: {obj['date']}"
    if obj.get("subreddit"):
        head += f"  {obj['subreddit']}  thread_id: {obj.get('thread_id')}"
    if obj.get("links") is not None:
        head += "\nlinks: " + (", ".join(obj["links"]) or "(none)")
    return head + "\n\n" + obj["text"] + ("\n\n[truncated]" if obj.get("truncated") else "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--worlds-root", default=None)
    ap.add_argument("--condition", default="search", choices=CONDITIONS)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of text")
    sub = ap.add_subparsers(dest="op", required=True)
    sub.add_parser("build")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--k", type=int, default=10)
    f = sub.add_parser("fetch"); f.add_argument("url"); f.add_argument("--max-chars", type=int, default=12000)
    r = sub.add_parser("reddit"); rs = r.add_subparsers(dest="rop", required=True)
    q = rs.add_parser("search"); q.add_argument("query"); q.add_argument("--k", type=int, default=10)
    q.add_argument("--sub", default=None)
    t = rs.add_parser("thread"); t.add_argument("thread_id"); t.add_argument("--max-chars", type=int, default=12000)
    for p in (s, f, q, t):                                  # --json is also accepted after the subcommand
        p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    if a.op == "build":
        wd = pathlib.Path(a.worlds_root or WORLDS_ROOT) / a.world
        out = build(wd if wd.is_dir() else pathlib.Path(a.world))
        print(json.dumps(out, indent=1))
        return
    w = World(a.world, a.condition, a.run_id, a.worlds_root, a.runs_root)
    if a.op == "search":
        out = w.search(a.query, a.k)
    elif a.op == "fetch":
        out = w.fetch(a.url, a.max_chars)
    elif a.rop == "search":
        out = w.search(a.query, a.k, reddit_only=True, sub=a.sub)
    else:
        out = w.thread(a.thread_id, a.max_chars)
    print(json.dumps(out, indent=1) if a.json else render(out))


if __name__ == "__main__":
    main()
