#!/usr/bin/env python3
"""The source-volume register: how much evidence each real channel actually yields.

Why this exists. The corpus-generation plan says to give each source family its
own availability mechanism and its own existence hurdle, which is right, but it
states no rates. Without measured rates the generator's visibility model is a
free parameter, and a free parameter tuned until the corpus "looks realistic" is
exactly the fitted-to-the-answer world the plan forbids.

So this module reduces every retrieval we actually hold to one number per
(county, source family, programme): how many independent documents or posts that
channel yields for that county, and whether the count is a lower bound. Those
numbers become the *anchors* for the hurdle model in `capacity.py`. Every anchor
carries its provenance tag, per the plan's section 3 rule:

    measured_anchor          counted from bytes on disk
    derived_with_assumptions counted, but a stated assumption converts it
    design_assumption        no measurement exists; the generator picks a value

Two defects motivated the rewrite of the reddit half. First, the existing
`county_coverage.analyse` comments that summing per-query rows would inflate the
count, then sums them anyway: it keeps a set of post *ids* but only stores the
first eight per row, so its headline "posts" figure double-counts every post
that several phrasings return. Second, a result list of exactly the API limit is
truncated, so it is a lower bound and must be labelled as one. Both are fixed
here by deduplicating full ids straight from the raw cache.

    python3 pipeline/recon/source_volume.py reddit
    python3 pipeline/recon/source_volume.py forums
    python3 pipeline/recon/source_volume.py register
    python3 pipeline/recon/source_volume.py anchors
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import re
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

OUT = ROOT / "corpus/counties"
RAW = OUT / "raw"
REDDIT_RAW = OUT / "reddit_raw"
REGISTER = OUT / "source_volume_register.csv"
ANCHORS = OUT / "source_volume_anchors.json"

API_LIMIT = 100          # a list this long was truncated by the search API
TIMING = re.compile(r"\b(weeks?|months?|days?|took|waiting|wait time|timeline|approved after|"
                    r"still waiting|backlog|business days)\b", re.I)


def _counties() -> list[str]:
    path = OUT / "ca_counties_covariates.csv"
    return [r["county"] for r in csv.DictReader(path.open())]


def _covariates() -> dict[str, dict]:
    path = OUT / "ca_counties_covariates.csv"
    return {r["county"]: r for r in csv.DictReader(path.open())}


def _slug(*parts) -> str:
    return re.sub(r"[^a-z0-9]+", "_", "__".join(str(p) for p in parts).lower()).strip("_")


# ---------------------------------------------------------------- reddit

def reddit_volume() -> dict[tuple[str, str], dict]:
    """Deduplicated post counts per (county, programme), straight from the cache.

    A post is counted once for a county no matter how many phrasings, subs or
    scopes returned it. `capped_queries` counts the queries that came back at the
    API limit, so a nonzero value means the true count is higher than reported.
    """
    import county_coverage as cc                                   # noqa: E402

    out: dict[tuple[str, str], dict] = {}
    for county, subs in cc.COUNTY_SUBS.items():
        for program, (phrasings, state_subs) in cc.PROGRAMS.items():
            ids: set[str] = set()
            timing_ids: set[str] = set()
            venues: set[str] = set()
            capped = 0
            queries = 0
            for sub in subs:
                # A sub shared by several counties, or one whose name is not
                # unique to California, is only ever queried with the county
                # name; crediting its bare-term hits to every listed county
                # would attribute one post to six counties at once.
                qs = ["%s County" % county] if sub in cc.REGIONAL_SUBS else phrasings
                for q in qs:
                    path = REDDIT_RAW / ("%s.json" % _slug(sub, q))
                    posts = cc._cache(path)
                    if posts is None:
                        continue
                    queries += 1
                    capped += len(posts) >= API_LIMIT
                    for p in posts:
                        pid = p.get("id")
                        if not pid:
                            continue
                        ids.add(pid)
                        venues.add(p.get("subreddit") or sub)
                        if cc.has_timing(p):
                            timing_ids.add(pid)
            for sub in state_subs:
                q = "%s County" % county
                path = REDDIT_RAW / ("%s.json" % _slug(sub, q))
                posts = cc._cache(path)
                if posts is None:
                    continue
                queries += 1
                capped += len(posts) >= API_LIMIT
                for p in posts:
                    pid = p.get("id")
                    if not pid:
                        continue
                    ids.add(pid)
                    venues.add(p.get("subreddit") or sub)
                    if cc.has_timing(p):
                        timing_ids.add(pid)
            out[(county, program)] = dict(
                posts=len(ids), timing=len(timing_ids), venues=len(venues),
                queries=queries, capped_queries=capped)
    return out



def reddit_county_totals() -> tuple[dict[str, set], dict[str, set]]:
    """Distinct post ids per county, deduplicated ACROSS programmes as well.

    A post matching two programmes' phrasings ("building permit" and "ADU
    permit") is one document, not two, so a county total is not the sum of its
    programme counts. Summing them inflates by about 1.3x on top of the 3.2x
    the per-query summation already introduced.
    """
    import county_coverage as cc                                   # noqa: E402

    ids: dict[str, set] = collections.defaultdict(set)
    timing: dict[str, set] = collections.defaultdict(set)
    for county, subs in cc.COUNTY_SUBS.items():
        ids[county], timing[county] = ids[county], timing[county]   # ensure the key exists
        for program, (phrasings, state_subs) in cc.PROGRAMS.items():
            pairs = [(s, ["%s County" % county] if s in cc.REGIONAL_SUBS else phrasings)
                     for s in subs]
            pairs += [(s, ["%s County" % county]) for s in state_subs]
            for sub, qs in pairs:
                for q in qs:
                    for post in (cc._cache(REDDIT_RAW / ("%s.json" % _slug(sub, q))) or []):
                        pid = post.get("id")
                        if not pid:
                            continue
                        ids[county].add(pid)
                        if cc.has_timing(post):
                            timing[county].add(pid)
    return ids, timing


def cmd_reddit(a):
    vol = reddit_volume()
    by_county: dict[str, dict] = collections.defaultdict(
        lambda: dict(ids=0, timing=0, capped=0, progs=0))
    # Per-county totals need their own dedup across programmes, because one post
    # can match two programmes' phrasings. Recomputed from the cache below.
    import county_coverage as cc
    for (county, program), v in vol.items():
        s = by_county[county]
        s["timing"] += v["timing"]
        s["capped"] += v["capped_queries"]
        s["progs"] += 1 if v["posts"] else 0
    county_ids, county_timing = reddit_county_totals()

    ranked = sorted(cc.COUNTY_SUBS, key=lambda c: -len(county_ids[c]))
    print("deduplicated reddit volume, window %s, %d counties" % (cc.AFTER, len(ranked)))
    print("%-16s %7s %7s %6s %6s" % ("county", "posts", "timing", "subs", "capped"))
    for c in ranked:
        print("%-16s %7d %7d %6d %6d"
              % (c, len(county_ids[c]), len(county_timing[c]),
                 by_county[c]["progs"], by_county[c]["capped"]))
    vals = [len(county_ids[c]) for c in ranked]
    tot = sum(vals)
    print("\ntotal distinct posts %d ; timing-bearing %d (%.0f%%)"
          % (tot, sum(len(county_timing[c]) for c in ranked),
             100 * sum(len(county_timing[c]) for c in ranked) / max(1, tot)))
    print("per county: mean %.0f  median %.0f  min %d  max %d"
          % (st.mean(vals), st.median(vals), min(vals), max(vals)))
    top5, bot30 = st.mean(vals[:5]), st.mean(vals[-30:])
    print("top-5 mean %.0f  bottom-30 mean %.1f  ratio %.0fx" % (top5, bot30, top5 / max(0.01, bot30)))
    print("counties with zero posts: %s" % ", ".join(c for c in ranked if not county_ids[c]))
    # Compare with the inflated figure the old summariser reported.
    old = OUT / "reddit_coverage_summary.json"
    if old.exists():
        prev = json.loads(old.read_text())
        pv = sum(v["posts"] for v in prev["per_county"].values())
        print("\nthe row-summing figure was %d, i.e. %.1fx the distinct count" % (pv, pv / max(1, tot)))
    return county_ids, county_timing


# ---------------------------------------------------------------- calguns

def calguns_volume() -> dict[str, dict]:
    """Per-county post and view counts from the cached county-information forum.

    This is the project's control case for separating the two halves of the
    hurdle. Every county got a thread in one administrative batch in October
    2010, so channel *existence* is 58/58 and carries no population signal at
    all; the *volume* inside those threads spans three orders of magnitude. A
    model with one availability slope cannot produce that pattern.
    """
    path = RAW / "forums/_calguns_county_threads.json"
    if not path.exists():
        return {}
    threads = json.loads(path.read_text())
    counties = _counties()
    # Longest name first, so "San Bernardino" is not captured by "San Benito"
    # style prefixes and multi-word names win over their first token.
    ordered = sorted(counties, key=len, reverse=True)
    out: dict[str, dict] = {c: dict(threads=0, posts=0, views=0, titles=[]) for c in counties}
    unmatched = []
    for title, meta in threads.items():
        tid, replies, views, last = (meta + ["", "", "", ""])[:4]
        hit = next((c for c in ordered if re.search(r"\b%s\b" % re.escape(c), title, re.I)), None)
        if hit is None:
            unmatched.append(title)
            continue
        s = out[hit]
        s["threads"] += 1
        s["posts"] += int(str(replies).replace(",", "") or 0)
        s["views"] += int(str(views).replace(",", "") or 0)
        s["titles"].append(title)
    return dict(out, __unmatched__=unmatched)


def cmd_forums(a):
    cg = calguns_volume()
    unmatched = cg.pop("__unmatched__", [])
    ranked = sorted(cg.items(), key=lambda kv: -kv[1]["posts"])
    print("calguns county-information forum: %d county threads matched, %d generic threads"
          % (sum(v["threads"] for v in cg.values()), len(unmatched)))
    print("%-16s %8s %8s %10s" % ("county", "threads", "posts", "views"))
    for c, v in ranked:
        print("%-16s %8d %8d %10d" % (c, v["threads"], v["posts"], v["views"]))
    posts = [v["posts"] for _, v in ranked]
    have = [p for p in posts if p]
    print("\nchannel existence: %d/%d counties have at least one thread"
          % (sum(1 for _, v in ranked if v["threads"]), len(ranked)))
    print("volume: total %d posts; mean %.0f; median %.0f; max %d; zero-post counties %d"
          % (sum(posts), st.mean(posts), st.median(posts), max(posts),
             sum(1 for p in posts if not p)))
    print("top-5 share %.0f%% of all posts" % (100 * sum(posts[:5]) / max(1, sum(posts))))
    views = [v["views"] for _, v in ranked if v["threads"]]
    print("views do not collapse the way posts do: min %d, median %d on threads that exist"
          % (min(views), st.median(views)))
    return cg


# ---------------------------------------------------------------- official docs

# Where each programme's cached county-facing documents live, and which evidence
# tier a file in that directory belongs to. A file here proves acquisition only.
DOC_DIRS = {
    ("adu", "declared"): ["adu_docs"],
    ("general_assistance", "declared"): ["ga", "general_assistance"],
    ("ccw", "declared"): ["ccw"],
    ("env_health", "declared"): [],          # inventory is a json, handled below
}


def official_docs() -> dict[tuple[str, str], int]:
    """Cached county-facing documents per (county, programme).

    Counted by county name appearing in the cached path, which is how the
    fetchers named them. This undercounts a document whose URL omits the county
    and overcounts a page that merely mentions a neighbour, so it is tagged
    `derived_with_assumptions`, never `measured_anchor`.
    """
    counties = _counties()
    slugs = {c: {c.lower().replace(" ", ""), c.lower().replace(" ", "_"),
                 c.lower().replace(" ", "-")} for c in counties}
    out: dict[tuple[str, str], int] = collections.Counter()
    for (prog, _tier), dirs in DOC_DIRS.items():
        for d in dirs:
            base = RAW / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.name.endswith(".meta.json"):
                    continue
                low = str(p).lower()
                for c, ss in slugs.items():
                    if any(s in low for s in ss):
                        out[(c, prog)] += 1
                        break
    return out


def env_health_docs() -> dict[str, dict]:
    """Per-county environmental-health evidence level from the P5 inventory.

    The inventory records, per county, how far retrieval actually got for each
    of septic (LAMP), wells and retail food. That per-stage record is what makes
    the funnel below measurable instead of assumed.
    """
    path = OUT / "p5_environmental_health_inventory.json"
    if not path.exists():
        return {}
    inv = json.loads(path.read_text())
    out: dict[str, dict] = {}
    for row in inv.get("rows", []):
        county = row.get("county")
        if not county:
            continue
        lamp, well, food = row.get("lamp", {}), row.get("well", {}), row.get("food", {})
        located = sum(bool(x) for x in (lamp.get("lamp_document_url"), well.get("permit_page_url"),
                                       food.get("plan_check_url")))
        read = sum([lamp.get("document_fetch_status", "").startswith("cached"),
                    bool(well.get("instructions_verified")),
                    bool(food.get("plancheck_instructions_verified"))])
        out[county] = dict(items=3, located=located, read=read,
                           lamp_status=lamp.get("status", ""),
                           lamp_operative=bool(lamp.get("current_operative_version_verified")),
                           well_level=well.get("program_evidence_level", ""),
                           food_level=food.get("plancheck_evidence_level", ""))
    return out


# The retrieval funnel, measured. The corpus plan asks for the chain
#
#   process exists -> topic covered -> claim reported -> document published
#   -> indexed/linked -> fetchable -> text recoverable -> claim extracted
#
# and says each source family needs its own rates. The P5 environmental-health
# packet recorded exactly that chain per county, so the rates below are counted,
# not chosen. They are steep, and they differ by family by a factor of ten at
# the deepest stage, which is the finding a single availability parameter cannot
# reproduce.
#
# READ THESE AS A JOINT RATE, NOT A PUBLICATION RATE. The packet spent 60
# searches and 170 fetches across 58 counties x 3 programmes, i.e. about one
# fetch per county-programme. So each rate is publication x indexing x our own
# bounded search depth. That makes them the right calibration for *what a
# bounded solver will find*, and a lower bound on what is published. The plan's
# own rule applies: access failure does not measure nonpublication.
FUNNEL = {
    "septic_lamp": {
        "tier": "designed",
        "stages": [("status source located", 57), ("programme authority evidenced", 48),
                   ("document link known", 38), ("document fetched", 3),
                   ("current operative version verified", 2)],
        "note": "the deepest stage is 3%: knowing a rule exists is common, holding the "
                "operative text of it is rare. A LAMP is optional Tier 2, so 'no document' "
                "can mean the lawful route is Tier 1, not that retrieval failed.",
    },
    "wells": {
        "tier": "declared",
        "stages": [("directory row", 58), ("permit page located", 22),
                   ("instructions read", 16), ("local standard above the state floor established", 0)],
        "note": "the last stage is zero of 58 and that is a real finding about "
                "identifiability, not a gap to paper over: 52 counties are 'not_verified' "
                "and 4 are 'not established, not a negative finding'.",
    },
    "retail_food": {
        "tier": "declared",
        "stages": [("directory row", 58), ("programme page read", 27),
                   ("plan-check instructions verified", 20), ("grading system verified", 7)],
        "note": "the shallowest funnel of the three, and the only one where a quarter of "
                "counties yield a scoreable local policy choice.",
    },
}


def cmd_funnel(a):
    print("the measured retrieval funnel, per source family (denominator 58 counties)\n")
    for fam, spec in FUNNEL.items():
        print("%s  [%s tier]" % (fam, spec["tier"]))
        prev = None
        for label, n in spec["stages"]:
            cond = "" if prev is None else "   conditional %3.0f%%" % (100 * n / max(1, prev))
            print("   %-52s %2d/58 = %3.0f%%%s" % (label, n, 100 * n / 58, cond))
            prev = n
        print("   %s\n" % spec["note"])
    print("Cross-family spread at the deepest stage: septic 3%, wells 0%, food 12%.")
    print("A single availability slope cannot produce that, which is why visibility.py")
    print("needs a per-family funnel rather than one parameter.")


# ---------------------------------------------------------------- the register

def build_register() -> list[dict]:
    """One row per (county, source family, programme) with a provenance tag."""
    rows: list[dict] = []
    cov = _covariates()
    rv = reddit_volume()
    cg = calguns_volume()
    cg.pop("__unmatched__", None)
    docs = official_docs()
    eh = env_health_docs()

    def add(county, family, programme, tier, n, unit, provenance, lower_bound=False, note=""):
        rows.append(dict(county=county, source_family=family, programme=programme,
                         evidence_tier=tier, n=n, unit=unit, provenance=provenance,
                         lower_bound=int(bool(lower_bound)), note=note,
                         population=cov.get(county, {}).get("pop_2023", "")))

    for (county, prog), v in sorted(rv.items()):
        add(county, "reddit", prog, "user", v["posts"], "distinct posts", "measured_anchor",
            lower_bound=bool(v["capped_queries"]),
            note="%d queries, %d at the API limit; %d timing-bearing; %d venues"
                 % (v["queries"], v["capped_queries"], v["timing"], v["venues"]))
    for county, v in sorted(cg.items()):
        add(county, "calguns_forum", "ccw", "user", v["posts"], "thread replies", "measured_anchor",
            note="%d county threads, %d views; channel created administratively in 2010"
                 % (v["threads"], v["views"]))
    for (county, prog), n in sorted(docs.items()):
        add(county, "official_page", prog, "declared", n, "cached documents",
            "derived_with_assumptions",
            note="county name matched in the cached path; acquisition only, not reading")
    for county, v in sorted(eh.items()):
        add(county, "official_page", "env_health", "declared", v["read"], "programmes read",
            "measured_anchor",
            note="of 3 programmes (septic/well/food): %d have a located document, %d were "
                 "actually read; lamp=%s well=%s food=%s"
                 % (v["located"], v["read"], v["lamp_status"] or "?",
                    v["well_level"] or "?", v["food_level"] or "?"))

    # Channels whose per-county volume we know the *shape* of but have not
    # counted. Recording them as design_assumption with the evidence we do have
    # keeps them in the register instead of silently absent, which is the
    # failure mode the closure ledger exists to prevent.
    grand_jury = {c: 1 for c in _counties()}
    for county in grand_jury:
        add(county, "grand_jury", "all", "designed", "", "reports per year",
            "design_assumption",
            note="mandated in all 58 counties; 9 of 9 sampled publish; rural counties "
                 "post 5-15 archived reports, large counties 10-25 per year. Inverted "
                 "against reddit: 8 of the 9 counties with no subreddit publish fetchable reports")
    return rows


def cmd_register(a):
    rows = build_register()
    cols = ["county", "source_family", "programme", "evidence_tier", "n", "unit",
            "provenance", "lower_bound", "note", "population"]
    with REGISTER.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    by_fam = collections.Counter(r["source_family"] for r in rows)
    by_prov = collections.Counter(r["provenance"] for r in rows)
    print("wrote %s: %d rows" % (REGISTER, len(rows)))
    print("\nby source family: %s" % dict(by_fam.most_common()))
    print("by provenance:    %s" % dict(by_prov.most_common()))
    print("\nThe register is the generator's only licensed source of volume rates.")
    print("A rate absent here is a design_assumption and must be declared as one.")


# ---------------------------------------------------------------- anchors

def cmd_anchors(a):
    """Reduce the register to the handful of numbers the generator consumes.

    Deliberately small. Each entry is a distribution shape plus the measurement
    that justifies it, so a reader can check any planted rate against its source
    without rerunning a retrieval.
    """
    rv = reddit_volume()
    cg = calguns_volume(); cg.pop("__unmatched__", None)
    cov = _covariates()

    def pop(c):
        try:
            return float(cov[c]["pop_2023"])
        except (KeyError, ValueError):
            return float("nan")

    counties = [c for c in _counties() if pop(c) == pop(c)]
    cid, ctim = reddit_county_totals()
    per_county = {c: len(cid[c]) for c in cid}

    # The existence hurdle and the volume slope, measured separately.
    import math
    pairs = [(math.log10(pop(c)), math.log10(per_county[c] + 1)) for c in counties]
    xs = [x for x, _ in pairs]; ys = [y for _, y in pairs]
    mx, my = st.mean(xs), st.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sxy / sxx
    r = sxy / math.sqrt(sxx * sum((y - my) ** 2 for y in ys))

    cg_pairs = [(math.log10(pop(c)), math.log10(cg[c]["posts"] + 1)) for c in counties if c in cg]
    cxs = [x for x, _ in cg_pairs]; cys = [y for _, y in cg_pairs]
    cmx, cmy = st.mean(cxs), st.mean(cys)
    csxy = sum((x - cmx) * (y - cmy) for x, y in cg_pairs)
    csxx = sum((x - cmx) ** 2 for x in cxs)
    cslope = csxy / csxx
    cr = csxy / math.sqrt(csxx * sum((y - cmy) ** 2 for y in cys))

    anchors = {
        "reddit": {
            "provenance": "measured_anchor",
            "unit": "distinct posts per county, 7 programmes, window 2022-09-01 onwards",
            "existence_rate": round(sum(1 for c in counties if per_county[c]) / len(counties), 4),
            "county_total_median": st.median([per_county[c] for c in counties]),
            "county_total_mean": round(st.mean([per_county[c] for c in counties]), 1),
            "county_total_max": max(per_county[c] for c in counties),
            "log10_slope_on_log10_population": round(slope, 3),
            "pearson_r_on_logs": round(r, 3),
            "county_total_p10": sorted(per_county[c] for c in counties)[5],
            "county_total_p90": sorted(per_county[c] for c in counties)[52],
            "timing_bearing_share": round(
                sum(len(ctim[c]) for c in counties) / max(1, sum(per_county[c] for c in counties)), 3),
            "capped_counties": sum(1 for c in counties
                                   if any(v["capped_queries"] for (cc_, _p), v in rv.items() if cc_ == c)),
            "note": "one county (Alpine, pop ~1,200) has zero posts; the existence hurdle "
                    "is nearly always passed, so the interesting variation is volume",
        },
        "calguns_forum": {
            "provenance": "measured_anchor",
            "unit": "thread replies per county, all-time",
            "existence_rate": round(sum(1 for c in counties if cg.get(c, {}).get("threads")) / len(counties), 4),
            "county_total_median": st.median([cg[c]["posts"] for c in counties if c in cg]),
            "county_total_max": max(cg[c]["posts"] for c in counties if c in cg),
            "log10_slope_on_log10_population": round(cslope, 3),
            "pearson_r_on_logs": round(cr, 3),
            "note": "the control case: threads were created for every county in one batch in "
                    "October 2010, so existence carries no population signal while volume "
                    "spans three orders of magnitude. Existence and volume need separate mechanisms.",
        },
        "grand_jury": {
            "provenance": "design_assumption",
            "unit": "reports per county-year",
            "existence_rate": 1.0,
            "note": "statutorily mandated in all 58 counties and inverted against reddit: 8 of "
                    "the 9 counties with no subreddit publish fetchable reports, and rural "
                    "reports are more on-topic per document. Volume not yet counted at title "
                    "level; do not plant a population slope here without measuring one.",
        },
    }
    ANCHORS.write_text(json.dumps(anchors, indent=1, default=str))
    print(json.dumps(anchors, indent=1, default=str))
    print("\nwrote %s" % ANCHORS)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("reddit", cmd_reddit), ("forums", cmd_forums),
                     ("funnel", cmd_funnel), ("register", cmd_register),
                     ("anchors", cmd_anchors)):
        p = sub.add_parser(name); p.set_defaults(fn=fn)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
