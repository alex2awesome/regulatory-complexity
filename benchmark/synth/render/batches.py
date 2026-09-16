#!/usr/bin/env python3
"""Split a world's artifact specs into renderer batches.

Groups: T (target artifacts — high fidelity), D (structured distractors: modelled non-target processes and
look-alike statutes — same brief), F (filler: unmodelled programs / off-topic threads — short, cheap).
Batches are balanced by word budget so one agent finishes a batch in one run.
  python3 benchmark/synth/render/batches.py --world W1 [--words-per-batch 14000]
Writes worlds/<W>/batches/<batch_id>.json {batch_id, group, spec_ids, words, kinds, jurs} and batches/index.json.
Already-rendered specs (artifacts/<id>.md exists) are skipped, so re-running after a partial wave batches the rest.
"""
import argparse, json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[3]


def group_of(s):
    if s.get("target"):
        return "T"
    return "F" if "filler" in (s.get("why") or "").lower() else "D"


def words_of(s):
    lo, hi = (s.get("style") or {}).get("length_words", [250, 450])
    n = (lo + hi) / 2
    if s.get("kind") in ("reddit_thread", "forum_thread"):
        n += 60 * len(s.get("thread") or [])
    return int(n)


def _write(out, bid, g, cur, cw):
    rec = {"batch_id": bid, "group": g, "spec_ids": [s["artifact_id"] for s in cur], "words": cw,
           "kinds": dict(collections.Counter(s["kind"] for s in cur)), "jurs": sorted({s.get("jur") or "" for s in cur})}
    (out / f"{bid}.json").write_text(json.dumps(rec, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--world", default="W1"); ap.add_argument("--words-per-batch", type=int, default=14000)
    a = ap.parse_args()
    wd = ROOT / "benchmark/synth/worlds" / a.world
    specs = [json.load(open(f)) for f in sorted((wd / "specs").glob("*.json"))]
    done = {p.stem for p in (wd / "artifacts").glob("*.md")} if (wd / "artifacts").exists() else set()
    by = collections.defaultdict(list)
    for s in specs:
        if s["artifact_id"] not in done:
            by[group_of(s)].append(s)
    out = wd / "batches"; out.mkdir(exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    index = []
    for g, items in by.items():
        items.sort(key=lambda s: (s.get("jur") or "", s.get("stat_id") or "", s["kind"]))
        budget = a.words_per_batch if g != "F" else int(a.words_per_batch * 1.4)
        cur, cw, n = [], 0, 0
        for s in items:
            w = words_of(s)
            if cur and cw + w > budget:
                index.append(_write(out, f"{g}{n:02d}", g, cur, cw)); cur, cw, n = [], 0, n + 1
            cur.append(s); cw += w
        if cur:
            index.append(_write(out, f"{g}{n:02d}", g, cur, cw))
    (out / "index.json").write_text(json.dumps(index, indent=1))
    for g in "TDF":
        bs = [b for b in index if b["group"] == g]
        print(f"group {g}: {len(bs)} batches, {sum(b['words'] for b in bs)} words, {sum(len(b['spec_ids']) for b in bs)} specs")
    print(f"{len(index)} batches -> {out.relative_to(ROOT)} (skipped {len(done)} already rendered)")


if __name__ == "__main__":
    main()
