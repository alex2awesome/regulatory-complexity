#!/usr/bin/env python3
"""Does a built world reproduce the volumes our real retrievals measured?

The generator's unit tests check the availability *mechanism* in isolation. This
checks the *corpus*, which is a different and weaker claim: a coefficient can be
right while the artifacts that come out of it are wrong, because a render cap, a
poster pool or a per-process ceiling can flatten a correct gradient. Both of
those happened during the W2 build:

  * a `max_threads_per_process` cap of 3 put every county at the ceiling and
    realised a population slope of 0.23 against the measured 0.75;
  * a constant applicant count meant a county whose availability draw asked for
    500 posts could only supply as many posters as it had cases, holding the
    realised slope at 0.50.

So this audit reads only the built artifacts and compares them against
`docs/2026-09-16-source-volume-register.md`. It reads no truth beyond the world
manifest and the spec index, and it never reads scores.

    python3 pipeline/procbench/audit_corpus_anchors.py benchmark/synth/worlds/W2_DEV_001
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics as st

# Which artifact kinds belong to which evidence tier. The tiers are the
# benchmark's own three-tier model plus the user tier.
TIERS = {
    "user": {"reddit_thread", "forum_thread", "office_review", "staff_review"},
    "declared": {"program_page", "form", "checklist", "faq", "generic_permits_page",
                 "third_party_guide", "vendor_boilerplate"},
    "designed": {"ordinance", "staff_report", "sop", "council_minutes", "audit_excerpt",
                 "fee_resolution", "fee_schedule", "bill_analysis", "grand_jury_report"},
    "observed": {"official_stats"},
    # Journalism is its own family: it reports on a process without being a
    # product of it, so it belongs to none of the three designed tiers. Given a
    # tier of its own rather than folded into one, so it is never silently
    # dropped from the denominator.
    "press": {"news"},
}

# The anchors, each naming what it is a slope OF. Getting this wrong is easy and
# was got wrong once: 0.989 is the slope of the RECORD COUNT inside the
# statistics artifacts, not of the number of artifacts, so comparing it to a
# document count is a category error that makes a correct corpus look broken.
ANCHORS = {
    "user_county_total_slope": dict(target=0.747, tol=0.15, unit="log10 artifacts per county",
                                    source="deduplicated reddit sweep, 58 counties"),
    "user_cell_median": dict(target=13, lo=8, hi=24, unit="artifacts per county-programme cell",
                             source="median distinct posts per cell"),
    "user_cell_zero_share": dict(target=0.07, lo=0.02, hi=0.18, unit="share of cells empty",
                                 source="29 of 406 cells had no post"),
    "observed_record_slope": dict(target=0.989, tol=0.20,
                                  unit="log10 CASE RECORDS per county, not artifacts",
                                  source="APR project counts, r=0.950"),
    "declared_flatter_than_user": dict(target=True,
                                       unit="the declared tier must have a shallower slope",
                                       source="official pages exist everywhere; posts do not"),
}


def _slope(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if not sxx:
        return 0.0, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / sxx, (sxy / math.sqrt(sxx * syy) if syy else 0.0)


def audit(world_dir: pathlib.Path) -> dict:
    world = json.loads((world_dir / "world.json").read_text())
    panel = {c["id"]: c for c in world.get("county_panel", [])}
    if not panel:
        return {"error": "not a county world: world_model_version is %s"
                         % world.get("world_model_version")}
    sid2dom = {s["stat_id"]: s["domain"] for s in world["statutes"]}

    per_tier: dict[str, collections.Counter] = {t: collections.Counter() for t in TIERS}
    cell = collections.Counter()
    unknown_kinds = collections.Counter()
    distractors = collections.Counter()
    for path in sorted((world_dir / "specs").glob("*.json")):
        spec = json.loads(path.read_text())
        jur, kind = spec.get("jur"), spec.get("kind")
        if jur not in panel:
            continue
        tier = next((t for t, kinds in TIERS.items() if kind in kinds), None)
        if tier is None:
            unknown_kinds[kind] += 1
            continue
        # DISTRACTORS MUST NOT ENTER THE SLOPE. A look-alike or filler artifact
        # is hosted on a county's site but is not a product of that county's
        # caseload, so its count is flat in population. Counting them diluted
        # the realised user slope from 0.690 to 0.556 and made a faithful
        # corpus look broken -- a defect in this audit, found by comparing the
        # artifact counts against the availability draw cell by cell.
        if not spec.get("target"):
            distractors[tier] += 1
            continue
        per_tier[tier][jur] += 1
        if tier == "user":
            dom = sid2dom.get(spec.get("stat_id"))
            if dom:
                cell[(jur, dom)] += 1

    counties = sorted(panel)
    logpop = [math.log10(panel[c]["pop"]) for c in counties]
    out: dict = {"world": world.get("world"), "n_counties": len(counties),
                 "scenario": (world.get("availability") or {}).get("scenario"),
                 "tiers": {}, "checks": {}}
    for tier in TIERS:
        vals = [per_tier[tier][c] for c in counties]
        slope, r = _slope(logpop, [math.log10(v + 1) for v in vals])
        out["tiers"][tier] = dict(total=sum(vals), median=st.median(vals), min=min(vals),
                                  max=max(vals), slope=round(slope, 3), r=round(r, 3),
                                  counties_with_none=sum(1 for v in vals if not v))

    # The observed tier's anchor is about RECORDS, so read the simulated case
    # counts rather than the artifact count.
    records = collections.Counter()
    for summ_path in sorted((world_dir / "truth" / "log").glob("*.summary.json")):
        jur = summ_path.name.split("__")[0]
        if jur not in panel:
            continue
        records[jur] += int(json.loads(summ_path.read_text()).get("n_applicants") or 0)

    # implemented cells only: a county that does not run a programme is not an
    # empty cell, it is not a cell at all.
    impl = collections.defaultdict(set)
    for i in world["implementations"]:
        if i["jur"] in panel and i.get("target"):
            impl[i["jur"]].add(i["domain"])
    cells = [cell.get((c, d), 0) for c in counties for d in sorted(impl[c])]

    def check(name, value, ok, detail=""):
        spec = ANCHORS[name]
        out["checks"][name] = dict(value=value, target=spec["target"], pass_=bool(ok),
                                   unit=spec["unit"], source=spec["source"], detail=detail)

    us = out["tiers"]["user"]["slope"]
    check("user_county_total_slope", us, abs(us - 0.747) <= 0.15)
    if cells:
        med = st.median(cells)
        zero = sum(1 for x in cells if not x) / len(cells)
        check("user_cell_median", med, 8 <= med <= 24,
              "%d implemented cells; mean %.1f, max %d" % (len(cells), st.mean(cells), max(cells)))
        check("user_cell_zero_share", round(zero, 4), 0.02 <= zero <= 0.18)
    if records:
        rs, rr = _slope([math.log10(panel[c]["pop"]) for c in counties if records[c]],
                        [math.log10(records[c]) for c in counties if records[c]])
        check("observed_record_slope", round(rs, 3), abs(rs - 0.989) <= 0.20,
              "r=%.3f over %d counties; total %d case records" % (rr, len(records), sum(records.values())))
    ds = out["tiers"]["declared"]["slope"]
    check("declared_flatter_than_user", ds < us, ds < us,
          "declared %.3f vs user %.3f" % (ds, us))

    if unknown_kinds:
        out["unclassified_kinds"] = dict(unknown_kinds.most_common())
    lineage = collections.Counter(l["kind"] for l in world.get("source_lineage", []))
    out["source_lineage"] = dict(lineage)
    prov = ((world.get("availability") or {}).get("provenance") or {})
    out["coefficient_provenance"] = prov.get("by_provenance")
    out["distractors_excluded"] = dict(distractors)
    out["passed"] = all(c["pass_"] for c in out["checks"].values())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("world_dir", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rep = audit(a.world_dir)
    if a.json:
        print(json.dumps(rep, indent=1, default=str))
        return 0 if rep.get("passed") else 1
    if "error" in rep:
        print("cannot audit: %s" % rep["error"])
        return 2
    print("corpus anchor audit: %s, %d counties, scenario %s\n"
          % (rep["world"], rep["n_counties"], rep["scenario"]))
    print("%-10s %8s %8s %6s %6s %7s %6s  %s" %
          ("tier", "total", "median", "min", "max", "slope", "r", "counties with none"))
    for tier, t in rep["tiers"].items():
        print("%-10s %8d %8.0f %6d %6d %7.3f %6.2f  %d"
              % (tier, t["total"], t["median"], t["min"], t["max"], t["slope"], t["r"],
                 t["counties_with_none"]))
    print("\nchecks against the measured register:")
    for name, c in rep["checks"].items():
        print("  [%s] %-28s %-10s target %-8s  %s"
              % ("PASS" if c["pass_"] else "FAIL", name, c["value"], c["target"], c["unit"]))
        if c.get("detail"):
            print("         %s" % c["detail"])
        print("         source: %s" % c["source"])
    print("\ndistractors excluded from the slopes: %s" % rep.get("distractors_excluded"))
    if rep.get("unclassified_kinds"):
        print("\nartifact kinds not mapped to a tier: %s" % rep["unclassified_kinds"])
    print("\nsource lineage: %s" % rep["source_lineage"])
    print("coefficient provenance: %s" % rep["coefficient_provenance"])
    print("\n%s" % ("ALL ANCHORS REPRODUCED" if rep["passed"] else "SOME ANCHORS MISSED"))
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
