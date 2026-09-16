#!/usr/bin/env python3
"""Aggregate per-slug duration observations into (agency_class, task_type, channel, blocking_party,
cadence, jurisdiction_class) priors.

  python3 pipeline/priors/rollup.py [--out dashboard/data/priors.json] [--min-n 1]

Reads pipeline/priors/observations/*.json (schema: pipeline/priors/taxonomy.json). For each step key it
reports n, the median and range of elapsed days, the statutory cap where one exists, the best evidence tier
backing it, and the spread between what officials claim and what applicants report — the quantity the
timing results say a model cannot read off a page.
"""
import argparse, collections, glob, json, pathlib, statistics
ROOT = pathlib.Path(__file__).resolve().parents[2]
TIER_RANK = ["verifiable_official", "inferred", "designed_document", "statutory", "community_reported"]
KEYS = ["agency_class", "task_type", "channel", "blocking_party", "cadence", "jurisdiction_class"]


def obs_list(d):
    for k in ("observations", "rows", "obs"):
        if isinstance(d.get(k), list):
            return d[k]
    return d if isinstance(d, list) else []


def key_of(o):
    sk = o.get("step_key") if isinstance(o.get("step_key"), dict) else o
    return tuple((sk.get(k) or "unspecified") for k in KEYS)


def nums(o, *fields):
    v = o.get("value") if isinstance(o.get("value"), dict) else o
    for f in fields:
        x = v.get(f)
        if isinstance(x, (int, float)):
            return float(x)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dashboard/data/priors.json")
    ap.add_argument("--min-n", type=int, default=1)
    a = ap.parse_args()
    files = sorted(glob.glob(str(ROOT / "pipeline/priors/observations/*.json")))
    groups, total, by_tier, by_slug = collections.defaultdict(list), 0, collections.Counter(), collections.Counter()
    for f in files:
        d = json.load(open(f))
        slug = pathlib.Path(f).stem
        for o in obs_list(d):
            if not isinstance(o, dict):
                continue
            total += 1
            by_tier[o.get("evidence_tier") or "unknown"] += 1
            by_slug[slug] += 1
            groups[key_of(o)].append(dict(o, _slug=o.get("slug") or slug))
    rows = []
    for k, os_ in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        el = [x for x in (nums(o, "elapsed_days", "p50") for o in os_) if x is not None]
        touch = [x for x in (nums(o, "touch_days") for o in os_) if x is not None]
        queue = [x for x in (nums(o, "queue_days") for o in os_) if x is not None]
        caps = [x for x in (nums(o, "statutory_cap_days") for o in os_) if x is not None]
        off = [x for x in (nums(o, "elapsed_days", "p50") for o in os_
                           if o.get("evidence_tier") in ("verifiable_official", "inferred", "designed_document")) if x is not None]
        com = [x for x in (nums(o, "elapsed_days", "p50") for o in os_
                           if o.get("evidence_tier") == "community_reported") if x is not None]
        tiers = {o.get("evidence_tier") for o in os_}
        best = next((t for t in TIER_RANK if t in tiers), None)
        if len(os_) < a.min_n:
            continue
        rows.append({**dict(zip(KEYS, k)),
                     "n": len(os_), "n_elapsed": len(el),
                     "median": round(statistics.median(el), 1) if el else None,
                     "lo": round(min(el), 1) if el else None, "hi": round(max(el), 1) if el else None,
                     "touch_median": round(statistics.median(touch), 2) if touch else None,
                     "queue_median": round(statistics.median(queue), 1) if queue else None,
                     "statutory_cap": round(statistics.median(caps), 1) if caps else None,
                     "official_median": round(statistics.median(off), 1) if off else None,
                     "community_median": round(statistics.median(com), 1) if com else None,
                     "official_vs_community": (round(statistics.median(com) / statistics.median(off), 2)
                                               if off and com and statistics.median(off) else None),
                     "best_tier": best, "tiers": sorted(t for t in tiers if t),
                     "slugs": sorted({o["_slug"] for o in os_}),
                     "example_quote": next((str(o.get("quote"))[:220] for o in os_ if o.get("quote")), None),
                     "example_label": next((str(o.get("step_label"))[:90] for o in os_ if o.get("step_label")), None)})
    # cap-vs-reality: where a statutory clock and a measured duration coexist
    breaches = [r for r in rows if r["statutory_cap"] and r["median"] and r["median"] > r["statutory_cap"]]
    out = {"built": "2026-09-15", "total": total, "n_step_keys": len(rows), "files": len(files),
           "by_tier": dict(by_tier), "by_slug": dict(by_slug),
           "cap_breaches": sorted(breaches, key=lambda r: -(r["median"] / r["statutory_cap"]))[:12],
           "rows": rows}
    p = ROOT / a.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"{total} observations from {len(files)} files -> {len(rows)} step keys -> {a.out}")
    print("  by tier:", dict(by_tier))
    print("  by slug:", dict(by_slug))
    if breaches:
        print(f"  {len(breaches)} step keys where the measured median exceeds the statutory cap; worst:")
        for r in out["cap_breaches"][:5]:
            print(f"    {r['agency_class']}/{r['task_type']}: median {r['median']}d vs cap {r['statutory_cap']}d"
                  f" ({r['median']/r['statutory_cap']:.1f}x, n={r['n']})")
    for r in rows[:10]:
        print(f"  n={r['n']:3} {r['agency_class']:18}{r['task_type']:18} median={r['median']} range={r['lo']}-{r['hi']} best={r['best_tier']}")


if __name__ == "__main__":
    main()
