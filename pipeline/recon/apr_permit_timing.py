#!/usr/bin/env python3
"""Per-jurisdiction housing-permit timing from the HCD Annual Progress Reports.

Work packet P0-APR-TIMING of docs/scoping/WORK_PACKETS.json. The APR Table A2 is
a unit-level record of every housing permit in California from 2018 to 2023,
carrying three dates per project:

    ENT_APPROVE_DT1   entitlement approved (the discretionary decision)
    BP_ISSUE_DT1      building permit issued
    CO_ISSUE_DT1      certificate of occupancy issued

So three elapsed clocks are computable per project, for all 58 counties and
every city, without reading a single document. This is the project's
external-validity benchmark: real per-jurisdiction process timing at a scale
that makes a hierarchical model identifiable.

Two things to keep straight. A county row (JURIS_NAME equal to the county) is
the **unincorporated** process, which is a different process from any city in
that county; they are never pooled. And a median span of zero days is not
missing data: it means the building permit issued the same day as the
entitlement, so the jurisdiction has no separate discretionary step. That is the
decision model visible in the timing data.

    python3 pipeline/recon/apr_permit_timing.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "corpus/counties/raw/apr_table_a2.csv"
OUT = ROOT / "corpus/counties"

DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%Y/%m/%d", "%d-%b-%y", "%m-%d-%Y")
SPANS = (("ent_to_bp", "ENT_APPROVE_DT1", "BP_ISSUE_DT1"),
         ("bp_to_co", "BP_ISSUE_DT1", "CO_ISSUE_DT1"),
         ("ent_to_co", "ENT_APPROVE_DT1", "CO_ISSUE_DT1"))
MAX_SPAN_DAYS = 3650          # a decade; beyond that the pair is a data error
csv.field_size_limit(1 << 24)


def parse_date(s):
    s = (s or "").strip()
    if not s or s in ("NA", "N/A", "0"):
        return None
    for f in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(s[:10], f).date()
        except ValueError:
            continue
    return None


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return round(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo), 1)


def run(src: pathlib.Path = SRC, limit: int | None = None):
    groups: dict[tuple, dict] = {}
    quality = collections.Counter()
    unit_cats = collections.Counter()
    bad_order = collections.Counter()
    seen_apn: dict[str, int] = collections.Counter()
    n = 0
    with src.open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            n += 1
            if limit and n > limit:
                break
            juris = (row.get("JURIS_NAME") or "").strip()
            county = (row.get("CNTY_NAME") or "").strip()
            year = (row.get("YEAR") or "").strip()
            cat = (row.get("UNIT_CAT") or "").strip()
            if not juris or not county or not year:
                quality["row_missing_key_fields"] += 1
                continue
            unit_cats[cat] += 1
            apn = (row.get("APN") or "").strip()
            if apn:
                seen_apn[apn] += 1
            # The county's own row is the UNINCORPORATED process, and it is named
            # "<NAME> COUNTY" in this file. A row named just "<NAME>" is the CITY of
            # that name, which exists for Los Angeles, Orange, Sonoma and others, so
            # the test must key on the word "county" and not on matching the county
            # name alone. Getting this backwards swaps two different processes.
            j = juris.strip().lower()
            c = county.strip().lower().replace(" county", "")
            is_unincorporated = j.replace(" county", "").strip() == c and j.endswith("county")
            key = (juris, county, year, cat, "unincorporated" if is_unincorporated else "city")
            slot = groups.setdefault(key, dict(n_projects=0, spans={s: [] for s, _, _ in SPANS},
                                               have={c: 0 for c in ("ENT_APPROVE_DT1", "BP_ISSUE_DT1", "CO_ISSUE_DT1")},
                                               no_ent=0, no_bp=0))
            slot["n_projects"] += 1
            dates = {}
            for col in ("ENT_APPROVE_DT1", "BP_ISSUE_DT1", "CO_ISSUE_DT1"):
                d = parse_date(row.get(col))
                dates[col] = d
                if d:
                    slot["have"][col] += 1
                    quality["have_" + col] += 1
            if (row.get("NO_ENTITLEMENTS") or "").strip() not in ("", "0"):
                slot["no_ent"] += 1
            if (row.get("NO_BUILDING_PERMITS") or "").strip() not in ("", "0"):
                slot["no_bp"] += 1
            for name, a, b in SPANS:
                da, db = dates[a], dates[b]
                if not (da and db):
                    continue
                d = (db - da).days
                if d < 0:
                    bad_order[name] += 1
                    quality["negative_" + name] += 1
                elif d > MAX_SPAN_DAYS:
                    quality["oversize_" + name] += 1
                else:
                    slot["spans"][name].append(d)
    rows = []
    for (juris, county, year, cat, kind), s in sorted(groups.items()):
        rec = dict(jurisdiction=juris, county=county, year=year, unit_cat=cat, jurisdiction_kind=kind,
                   n_projects=s["n_projects"],
                   n_with_entitlement_date=s["have"]["ENT_APPROVE_DT1"],
                   n_with_bp_date=s["have"]["BP_ISSUE_DT1"],
                   n_with_co_date=s["have"]["CO_ISSUE_DT1"],
                   n_flagged_no_entitlement=s["no_ent"], n_flagged_no_building_permit=s["no_bp"])
        for name, _, _ in SPANS:
            vals = sorted(s["spans"][name])
            rec["n_" + name] = len(vals)
            rec["median_" + name] = quantile(vals, .5)
            rec["p25_" + name] = quantile(vals, .25)
            rec["p75_" + name] = quantile(vals, .75)
            rec["p90_" + name] = quantile(vals, .9)
        rows.append(rec)
    path = OUT / "apr_permit_timing.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    dup = sum(1 for v in seen_apn.values() if v > 1)
    summary = dict(source=str(src.relative_to(ROOT)), rows_read=n, groups=len(rows),
                   unit_categories=dict(unit_cats.most_common()),
                   quality=dict(quality), negative_spans=dict(bad_order),
                   duplicate_apns=dup, distinct_apns=len(seen_apn),
                   max_span_days_cut=MAX_SPAN_DAYS)
    (OUT / "apr_permit_timing_quality.json").write_text(json.dumps(summary, indent=1))
    print("wrote %s  (%d group rows from %d records)" % (path, len(rows), n))
    return rows, summary


def report(rows, summary):
    """The ADU cross-jurisdiction picture, which is what the packet is for."""
    adu = [r for r in rows if r["unit_cat"] == "ADU"]
    by_juris: dict[tuple, list] = collections.defaultdict(list)
    for r in adu:
        if r["n_ent_to_bp"]:
            by_juris[(r["jurisdiction"], r["county"], r["jurisdiction_kind"])].append(
                (r["n_ent_to_bp"], r["median_ent_to_bp"]))
    agg = []
    for (j, c, kind), vals in by_juris.items():
        n = sum(v[0] for v in vals)
        med = statistics.median([v[1] for v in vals])
        agg.append((j, c, kind, n, med))
    strong = sorted((a for a in agg if a[3] >= 30), key=lambda t: -t[3])
    zero = [a for a in strong if a[4] == 0]
    print("\n=== ADU entitlement-to-building-permit, jurisdictions with >=30 spans: %d" % len(strong))
    print("    of those, %d have a median of 0 days (no separate discretionary step)" % len(zero))
    meds = sorted(a[4] for a in strong)
    print("    median of medians %.0f days; p25 %.0f; p75 %.0f; max %.0f"
          % (statistics.median(meds), quantile(meds, .25), quantile(meds, .75), meds[-1]))
    print("\n    largest by volume:")
    for j, c, kind, n, med in strong[:10]:
        print("      %-28s %-14s %-16s n=%5d  median %4.0f d" % (j[:28], c[:14], kind, n, med))
    print("\n    slowest with >=30 spans:")
    for j, c, kind, n, med in sorted(strong, key=lambda t: -t[4])[:10]:
        print("      %-28s %-14s %-16s n=%5d  median %4.0f d" % (j[:28], c[:14], kind, n, med))
    unin = [a for a in strong if a[2] == "unincorporated"]
    print("\n    unincorporated-county processes with >=30 spans: %d" % len(unin))
    for j, c, kind, n, med in sorted(unin, key=lambda t: -t[3])[:8]:
        print("      %-28s n=%5d  median %4.0f d" % (j[:28], n, med))
    print("\n=== data quality")
    q = summary["quality"]
    tot = summary["rows_read"]
    for col in ("ENT_APPROVE_DT1", "BP_ISSUE_DT1", "CO_ISSUE_DT1"):
        print("    %-18s present on %7d of %d rows (%.1f%%)"
              % (col, q.get("have_" + col, 0), tot, 100 * q.get("have_" + col, 0) / tot))
    print("    negative spans (date out of order): %s" % summary["negative_spans"])
    print("    spans over %d days discarded: %s"
          % (summary["max_span_days_cut"],
             {k: v for k, v in q.items() if k.startswith("oversize_")}))
    print("    duplicate APNs: %d of %d distinct" % (summary["duplicate_apns"], summary["distinct_apns"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, help="stop after N records (smoke test)")
    a = ap.parse_args(argv)
    if not SRC.exists():
        sys.exit("missing %s; see WORK_PACKETS.json verified_assets hcd-apr-table-a2" % SRC)
    rows, summary = run(limit=a.limit)
    report(rows, summary)


if __name__ == "__main__":
    main()
