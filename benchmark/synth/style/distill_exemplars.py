#!/usr/bin/env python3
"""Distill style exemplars from the real reconnaissance corpus into benchmark/synth/style/.
Reads corpus/realworld/*/reddit/posts/*.json and picks posts/comments that carry process or timing
content (heuristics: numbers + day/week/month words, step verbs), writes reddit_exemplars.md
(verbatim, with source ids), and reddit_stats.json (length distributions, comment counts, share of
posts with timing) so the generator's persona/thread parameters can be calibrated.
Run after Wave 1: python3 benchmark/synth/style/distill_exemplars.py
"""
import glob, json, pathlib, re, statistics, random
ROOT = pathlib.Path(__file__).resolve().parents[3]
TIMING = re.compile(r"\b(\d+|a couple|a few|two|three|four|five|six|ten)\s*(business\s*)?(day|week|month|hour|min)s?\b", re.I)
STEPS = re.compile(r"\b(submit|applied|application|inspect|approved|denied|permit|interview|appeal|fee|paid|scheduled|received|called|counter|plan check|review)\w*", re.I)


def score(text):
    t = text or ""
    return len(TIMING.findall(t)) * 2 + min(len(STEPS.findall(t)), 8)


def main(seed=0, per_slug=6, max_chars=1800):
    random.seed(seed)
    out_md, stats = ["# Reddit exemplars (verbatim, from corpus/realworld)\n"], {}
    for slug_dir in sorted(glob.glob(str(ROOT / "corpus/realworld/*/reddit/posts"))):
        slug = pathlib.Path(slug_dir).parents[1].name
        posts = [json.load(open(f)) for f in glob.glob(slug_dir + "/*.json")]
        if not posts:
            continue
        rows = []
        for p in posts:
            body = (p.get("selftext") or "")
            cs = p.get("comments") or []
            rows.append((score(p.get("title", "") + " " + body), p, cs))
        rows.sort(key=lambda r: -r[0])
        lens = [len((p.get("selftext") or "").split()) for _, p, _ in rows]
        clens = [len((c.get("body") or "").split()) for _, _, cs in rows for c in cs]
        stats[slug] = {"n_posts": len(rows), "post_words_median": statistics.median(lens) if lens else 0,
                       "comment_words_median": statistics.median(clens) if clens else 0,
                       "comments_per_post_median": statistics.median([len(cs) for _, _, cs in rows]),
                       "share_posts_with_timing": sum(1 for _, p, _ in rows if TIMING.search((p.get("title") or "") + (p.get("selftext") or ""))) / len(rows),
                       "share_comments_with_timing": (sum(1 for _, _, cs in rows for c in cs if TIMING.search(c.get("body") or "")) / len(clens)) if clens else 0}
        out_md.append(f"\n## {slug}\n")
        for sc, p, cs in rows[:per_slug]:
            out_md.append(f"\n### r/{p.get('subreddit')} · {p.get('created_iso','')} · id {p.get('id')} · score {sc}\n**{p.get('title','')}**\n\n{(p.get('selftext') or '')[:max_chars]}\n")
            best = sorted(cs, key=lambda c: -score(c.get("body")))[:4]
            for c in best:
                out_md.append(f"\n> **comment** ({c.get('score')}): {(c.get('body') or '')[:900]}\n")
    (ROOT / "benchmark/synth/style/reddit_exemplars.md").write_text("\n".join(out_md))
    (ROOT / "benchmark/synth/style/reddit_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
