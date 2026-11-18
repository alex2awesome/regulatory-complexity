#!/usr/bin/env python3
"""Measure per-county user-evidence coverage on reddit, by program.

Workstream A8 of docs/2026-09-16-county-scale-up-plan.md: the empirical version
of the availability model. Does the "rural counties have almost no data"
hypothesis hold, and does it hold for every program or only the urban ones?

Method. Arctic Shift keyword search needs a subreddit (reddit.com's own JSON is
403 to scripts), so for each county we query its own subreddit(s) if it has any,
and separately query statewide subreddits with the county name in the text. A
county with no subreddit and no statewide hits has, for our purposes, no user
evidence: that is the finding, not a gap in the method.

Every raw response is written under corpus/counties/reddit_raw/ so a rerun never
refetches. Rate limit is the client's (~1 req/1.2 s).

    python3 pipeline/recon/county_coverage.py subs        # which county subs exist
    python3 pipeline/recon/county_coverage.py coverage    # the full sweep
    python3 pipeline/recon/county_coverage.py analyse     # csv + summary from the raw cache
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import reddit_fetch as rf  # noqa: E402

OUT = ROOT / "corpus/counties"
RAW = OUT / "reddit_raw"

# The 58 counties with their candidate subreddits, most specific first. A county
# whose list is empty has no plausible sub of its own; it is still searched
# through the statewide subs. Names are verified by the `subs` subcommand, which
# records which of these actually return posts.
COUNTY_SUBS: dict[str, list[str]] = {
    "Alameda": ["oakland", "eastbay", "berkeley", "bayarea"],
    "Alpine": [],
    "Amador": [],
    "Butte": ["chico"],
    "Calaveras": [],
    "Colusa": [],
    "Contra Costa": ["eastbay", "bayarea"],
    "Del Norte": ["crescentcity"],
    "El Dorado": ["ElDoradoCounty", "southlaketahoe"],
    "Fresno": ["fresno"],
    "Glenn": [],
    "Humboldt": ["Humboldt", "eureka"],
    "Imperial": ["imperialvalley", "ElCentro"],
    "Inyo": ["bishopca"],
    "Kern": ["bakersfield"],
    "Kings": ["hanford"],
    "Lake": ["LakeCountyCA"],
    "Lassen": ["susanville"],
    "Los Angeles": ["LosAngeles", "AskLosAngeles", "longbeach", "SanFernandoValley"],
    "Madera": ["madera"],
    "Marin": ["marincounty", "bayarea"],
    "Mariposa": [],
    "Mendocino": ["Mendocino", "ukiah"],
    "Merced": ["merced"],
    "Modoc": [],
    "Mono": ["mammothlakes"],
    "Monterey": ["monterey", "salinas"],
    "Napa": ["Napa"],
    "Nevada": ["nevadacounty", "GrassValley", "truckee"],
    "Orange": ["orangecounty", "AskOC"],
    "Placer": ["Roseville", "rocklin", "placercounty"],
    "Plumas": ["quincyca"],
    "Riverside": ["riverside", "InlandEmpire", "PalmSprings", "temecula"],
    "Sacramento": ["Sacramento", "SacramentoRealEstate"],
    "San Benito": ["hollister"],
    "San Bernardino": ["sanbernardino", "InlandEmpire"],
    "San Diego": ["sandiego", "AskSanDiego"],
    "San Francisco": ["sanfrancisco", "AskSF", "bayarea"],
    "San Joaquin": ["Stockton", "tracyca"],
    "San Luis Obispo": ["SLO", "sanluisobispo"],
    "San Mateo": ["bayarea", "sanmateo"],
    "Santa Barbara": ["SantaBarbara", "sanluisobispo"],
    "Santa Clara": ["SanJose", "bayarea", "PaloAlto", "sunnyvale"],
    "Santa Cruz": ["santacruz"],
    "Shasta": ["Redding"],
    "Sierra": [],
    "Siskiyou": ["mtshasta", "yreka"],
    "Solano": ["Vallejo", "fairfieldca", "Benicia"],
    "Sonoma": ["Sonoma", "santarosa", "Petaluma"],
    "Stanislaus": ["Modesto", "turlock"],
    "Sutter": ["YubaCity", "yubasutter"],
    "Tehama": ["redbluff"],
    "Trinity": [],
    "Tulare": ["visalia", "Tulare"],
    "Tuolumne": ["sonoraca"],
    "Ventura": ["Ventura", "thousandoaks", "simivalley"],
    "Yolo": ["davisca", "UCDavis", "WestSacramento"],
    "Yuba": ["marysville", "yubasutter"],
}

# Statewide and program subs, searched with the county name as the query term.
STATEWIDE = ["California", "AskCalifornia", "bayarea", "CAguns", "CalFresh", "foodstamps",
             "Medicaid", "ADU", "homestead", "Septic", "realestateinvesting"]

# program -> (query phrasings, statewide subs worth querying for it)
PROGRAMS: dict[str, tuple[list[str], list[str]]] = {
    "calfresh": (["CalFresh", "food stamps", "EBT application"], ["CalFresh", "foodstamps", "California"]),
    "medical": (["Medi-Cal application", "Medi-Cal county"], ["Medicaid", "California"]),
    "general_assistance": (["general assistance", "general relief"], ["California"]),
    "ccw": (["CCW", "concealed carry permit"], ["CAguns", "California"]),
    "adu": (["ADU permit", "granny flat permit", "accessory dwelling unit"],
            ["ADU", "realestateinvesting", "California"]),
    "septic_well": (["septic permit", "perc test", "well permit"], ["homestead", "Septic", "California"]),
    "building_permit": (["building permit", "county permit"], ["California"]),
}

# Five candidate subreddits serve more than one county: r/bayarea (6), r/eastbay,
# r/InlandEmpire, r/sanluisobispo and r/yubasutter (2 each). Querying such a sub
# with a bare program term and crediting the result to every county that lists it
# double-counts: one r/bayarea post about CalFresh is not evidence about six
# counties, and it does not say which county it concerns. So a shared sub is
# scoped "regional" and is only ever queried WITH the county name; a post in it
# counts for a county only when that county is named. Exclusive subs (81 of 86)
# keep the bare program term, because there the county is implied by the venue.
def _shared_subs() -> set[str]:
    seen: dict[str, int] = {}
    for subs in COUNTY_SUBS.values():
        for sub in subs:
            seen[sub] = seen.get(sub, 0) + 1
    return {sub for sub, n in seen.items() if n > 1}


SHARED_SUBS = _shared_subs()

# Candidate names that are NOT unique to California: r/hanford is overwhelmingly
# the Washington nuclear site, r/Roseville is Michigan and Minnesota, and
# r/marysville is Washington and Ohio. A bare program term in these returns
# out-of-state content, so they are treated like a shared sub: only a query
# naming the county counts. (Found by the covariate agent, 2026-09-16.)
AMBIGUOUS_SUBS = {"hanford", "Roseville", "marysville"}
REGIONAL_SUBS = SHARED_SUBS | AMBIGUOUS_SUBS

AFTER = "2022-09-01"
TIMING = re.compile(r"\b(weeks?|months?|days?|took|waiting|wait time|timeline|approved after|"
                    r"still waiting|backlog|business days)\b", re.I)
POST_FIELDS = ("id", "subreddit", "title", "selftext", "created_utc", "num_comments", "score", "permalink")


def _cache(path: pathlib.Path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
    return None


def _slug(*parts) -> str:
    return re.sub(r"[^a-z0-9]+", "_", "__".join(str(p) for p in parts).lower()).strip("_")


def query(subreddit: str, q: str, limit: int = 100) -> list[dict]:
    """One cached search. Returns slim posts; [] on a sub that does not exist."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / ("%s.json" % _slug(subreddit, q))
    hit = _cache(path)
    if hit is not None:
        return hit
    try:
        posts = rf.search_posts(subreddit, query=q, after=AFTER, limit=limit)
        rows = [rf.slim(p, POST_FIELDS) for p in posts]
    except Exception as exc:                       # a missing sub 404s; record it as empty
        rows = []
        path.with_suffix(".error.txt").write_text("%s: %s" % (type(exc).__name__, exc))
    path.write_text(json.dumps(rows))
    return rows


def has_timing(post: dict) -> bool:
    return bool(TIMING.search((post.get("title") or "") + " " + (post.get("selftext") or "")))


def cmd_subs(args):
    """Which candidate subreddits actually exist and carry any traffic."""
    rows = []
    for county, subs in COUNTY_SUBS.items():
        for sub in subs:
            posts = query(sub, "permit")
            rows.append(dict(county=county, subreddit=sub, permit_posts=len(posts)))
            print("%-16s r/%-22s %3d" % (county, sub, len(posts)), flush=True)
    (OUT / "reddit_subs_probe.json").write_text(json.dumps(rows, indent=1))
    live = sorted({r["subreddit"] for r in rows if r["permit_posts"]})
    dead = sorted({r["subreddit"] for r in rows if not r["permit_posts"]})
    print("\nlive: %d  %s" % (len(live), ", ".join(live)))
    print("no hits: %d  %s" % (len(dead), ", ".join(dead)))


def cmd_coverage(args):
    rows = []
    counties = [args.county] if args.county else list(COUNTY_SUBS)
    for county in counties:
        subs = COUNTY_SUBS[county]
        for program, (phrasings, state_subs) in PROGRAMS.items():
            if args.program and program != args.program:
                continue
            # 1. the county's OWN subreddits, queried by program term. A sub shared
            # with another county cannot attribute a bare-term hit, so it is
            # queried with the county name instead and scoped "regional".
            exclusive = [x for x in subs if x not in REGIONAL_SUBS][:args.max_subs]
            regional = [x for x in subs if x in REGIONAL_SUBS][:args.max_subs]
            for sub in exclusive:
                for q in phrasings[:args.phrasings]:
                    posts = query(sub, q)
                    rows.append(dict(county=county, program=program, scope="county_sub", subreddit=sub,
                                     query=q, n_posts=len(posts),
                                     n_timing=sum(1 for p in posts if has_timing(p)),
                                     cap_hit=len(posts) >= 100,
                                     ids=",".join(p.get("id", "") for p in posts[:8])))
            for sub in regional:
                q = "%s County" % county
                posts = query(sub, q)
                rows.append(dict(county=county, program=program, scope="regional_sub", subreddit=sub,
                                 query=q, n_posts=len(posts),
                                 n_timing=sum(1 for p in posts if has_timing(p)),
                                 cap_hit=len(posts) >= 100,
                                 ids=",".join(p.get("id", "") for p in posts[:8])))
            # 2. statewide subs, queried with the county name
            for sub in state_subs[:args.statewide]:
                q = "%s County" % county
                posts = query(sub, q)
                rows.append(dict(county=county, program=program, scope="statewide", subreddit=sub,
                                 query=q, n_posts=len(posts),
                                 n_timing=sum(1 for p in posts if has_timing(p)),
                                 cap_hit=len(posts) >= 100,
                                 ids=",".join(p.get("id", "") for p in posts[:8])))
            done = sum(r["n_posts"] for r in rows if r["county"] == county and r["program"] == program)
            print("%-16s %-18s %4d posts" % (county, program, done), flush=True)
    _write(rows)


def _write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "reddit_coverage.csv"
    cols = ["county", "program", "scope", "subreddit", "query", "n_posts", "n_timing", "cap_hit", "ids"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote", path, len(rows), "rows")


def cmd_analyse(args):
    """Rebuild the csv from the raw cache and summarise, without any network."""
    rows = []
    for county, subs in COUNTY_SUBS.items():
        for program, (phrasings, state_subs) in PROGRAMS.items():
            for sub in subs:
                if sub in REGIONAL_SUBS:
                    q = "%s County" % county
                    posts = _cache(RAW / ("%s.json" % _slug(sub, q)))
                    if posts is not None:
                        rows.append(dict(county=county, program=program, scope="regional_sub", subreddit=sub,
                                         query=q, n_posts=len(posts),
                                         n_timing=sum(1 for p in posts if has_timing(p)),
                                         cap_hit=len(posts) >= 100,
                                         ids=",".join(p.get("id", "") for p in posts[:8])))
                    continue
                for q in phrasings:
                    posts = _cache(RAW / ("%s.json" % _slug(sub, q)))
                    if posts is None:
                        continue
                    rows.append(dict(county=county, program=program, scope="county_sub", subreddit=sub,
                                     query=q, n_posts=len(posts),
                                     n_timing=sum(1 for p in posts if has_timing(p)),
                                     cap_hit=len(posts) >= 100,
                                     ids=",".join(p.get("id", "") for p in posts[:8])))
            for sub in state_subs:
                q = "%s County" % county
                posts = _cache(RAW / ("%s.json" % _slug(sub, q)))
                if posts is None:
                    continue
                rows.append(dict(county=county, program=program, scope="statewide", subreddit=sub,
                                 query=q, n_posts=len(posts),
                                 n_timing=sum(1 for p in posts if has_timing(p)),
                                 cap_hit=len(posts) >= 100,
                                 ids=",".join(p.get("id", "") for p in posts[:8])))
    if not rows:
        print("no raw cache yet; run `coverage` first")
        return
    _write(rows)
    # per-county totals, deduplicating the same post found by several queries
    # Deduplicate by post id within a county: several phrasings, and the county
    # and regional scopes, can return the same post. Summing rows would inflate.
    per_county: dict[str, dict] = {}
    for r in rows:
        slot = per_county.setdefault(r["county"], dict(posts=0, timing=0, subs=set(), ids=set()))
        slot["posts"] += r["n_posts"]
        slot["timing"] += r["n_timing"]
        slot["ids"].update(x for x in r["ids"].split(",") if x)
        if r["n_posts"]:
            slot["subs"].add(r["subreddit"])
    per_program: dict[str, dict] = {}
    for r in rows:
        slot = per_program.setdefault(r["program"], dict(posts=0, timing=0, counties_with_any=set()))
        slot["posts"] += r["n_posts"]
        slot["timing"] += r["n_timing"]
        if r["n_posts"]:
            slot["counties_with_any"].add(r["county"])
    print("\n== per program")
    for p, s in sorted(per_program.items(), key=lambda kv: -kv[1]["posts"]):
        print("%-18s %6d posts  %5d with timing  %2d/58 counties with any"
              % (p, s["posts"], s["timing"], len(s["counties_with_any"])))
    print("\n== counties, most to least")
    ranked = sorted(per_county.items(), key=lambda kv: -kv[1]["posts"])
    for c, s in ranked:
        print("%-16s %6d posts  %5d timing  %d live subs  (%d distinct ids sampled)"
              % (c, s["posts"], s["timing"], len(s["subs"]), len(s["ids"])))
    top5 = sum(s["posts"] for _, s in ranked[:5])
    bottom30 = sum(s["posts"] for _, s in ranked[-30:])
    print("\ntop-5 counties: %d posts; bottom-30: %d; ratio %.1fx"
          % (top5, bottom30, (top5 / bottom30) if bottom30 else float("inf")))
    zero = [c for c, s in per_county.items() if not s["posts"]]
    print("counties with zero posts across all programs: %d  %s" % (len(zero), ", ".join(sorted(zero))))
    (OUT / "reddit_coverage_summary.json").write_text(json.dumps(dict(
        per_program={p: dict(posts=s["posts"], timing=s["timing"],
                             counties_with_any=len(s["counties_with_any"])) for p, s in per_program.items()},
        per_county={c: dict(posts=s["posts"], timing=s["timing"], live_subs=sorted(s["subs"]),
                            distinct_ids_sampled=len(s["ids"]))
                    for c, s in per_county.items()},
        top5_posts=top5, bottom30_posts=bottom30, zero_counties=sorted(zero),
        window_after=AFTER, n_queries=len(rows)), indent=1))
    print("wrote", OUT / "reddit_coverage_summary.json")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("subs"); s.set_defaults(fn=cmd_subs)
    c = sub.add_parser("coverage"); c.add_argument("--county"); c.add_argument("--program")
    c.add_argument("--max-subs", type=int, default=2, dest="max_subs")
    c.add_argument("--phrasings", type=int, default=1)
    c.add_argument("--statewide", type=int, default=2)
    c.set_defaults(fn=cmd_coverage)
    a = sub.add_parser("analyse"); a.set_defaults(fn=cmd_analyse)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
