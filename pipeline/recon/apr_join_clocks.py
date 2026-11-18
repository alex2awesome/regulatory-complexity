#!/usr/bin/env python3
"""Join HCD APR Table A to Table A2: the full applicant-experienced permit clock.

Completes work packet P0-APR-TIMING. Table A is the application register and
carries `APP_SUBMIT_DT` on 100% of its 358,264 rows, plus two fields that matter
more than the dates:

    PROJECT_TYPE        "Ministerial" or "Discretionary", stated by the jurisdiction
    APPLICATION_STATUS  Approved / Pending / Withdrawn / Disapproved

Table A2 is the permit register and carries the entitlement, building-permit and
occupancy dates. Joining them on (jurisdiction, APN, unit category) yields the
clock an applicant actually experiences, **submission to building permit**,
which is the quantity the synthetic world simulates as end-to-end elapsed time
and the one the Bayesian model has been trying to recover from forum posts.

The join also makes a validation possible that nothing else in this project can
do: `PROJECT_TYPE` is the jurisdiction's own label for whether a discretionary
step exists, so the inference "a zero-day entitlement-to-permit span means a
ministerial process" can be **scored against a stated ground truth** rather than
asserted.

Duplicate APNs are common (multi-unit projects, re-reporting across years), so
per join key this takes the earliest submittal from A and the earliest
building-permit date from A2, and reports how often the key was ambiguous.

    python3 pipeline/recon/apr_join_clocks.py
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

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "corpus/counties/raw"
OUT = ROOT / "corpus/counties"
csv.field_size_limit(1 << 24)

DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%Y/%m/%d")
MAX_SPAN = 3650


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


def quantile(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    if len(v) == 1:
        return float(v[0])
    pos = q * (len(v) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (pos - lo), 1)


def is_unincorporated(juris: str, county: str) -> bool:
    j = juris.strip().lower()
    return j.replace(" county", "").strip() == county.strip().lower().replace(" county", "") \
        and j.endswith("county")


def key_of(row) -> tuple | None:
    apn = (row.get("APN") or "").strip()
    juris = (row.get("JURIS_NAME") or "").strip()
    if not apn or not juris:
        return None
    return (juris, apn, (row.get("UNIT_CAT") or "").strip())


def load_applications():
    """key -> earliest submittal, with the jurisdiction's own process label."""
    apps: dict[tuple, dict] = {}
    stats = collections.Counter()
    with (RAW / "apr_table_a.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            stats["rows"] += 1
            k = key_of(row)
            if not k:
                stats["no_join_key"] += 1
                continue
            d = parse_date(row.get("APP_SUBMIT_DT"))
            if not d:
                stats["no_submit_date"] += 1
                continue
            rec = apps.get(k)
            ptype = (row.get("PROJECT_TYPE") or "").strip()
            status = (row.get("APPLICATION_STATUS") or "").strip()
            if rec is None:
                apps[k] = dict(submit=d, county=(row.get("CNTY_NAME") or "").strip(),
                               ptype=ptype, status=status, n=1)
            else:
                rec["n"] += 1
                stats["duplicate_key"] += 1
                if d < rec["submit"]:
                    rec["submit"] = d
                rec["ptype"] = rec["ptype"] or ptype
                rec["status"] = rec["status"] or status
    return apps, stats


def run():
    apps, astats = load_applications()
    print("Table A: %d rows, %d join keys (%d duplicate-key hits, %d without a key)"
          % (astats["rows"], len(apps), astats["duplicate_key"], astats["no_join_key"]))

    groups: dict[tuple, dict] = {}
    label_check: dict[tuple, dict] = {}
    stats = collections.Counter()
    with (RAW / "apr_table_a2.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            stats["a2_rows"] += 1
            k = key_of(row)
            app = apps.get(k) if k else None
            if not app:
                stats["unmatched_a2_row"] += 1
                continue
            stats["matched"] += 1
            juris, _, cat = k
            county = app["county"] or (row.get("CNTY_NAME") or "").strip()
            year = (row.get("YEAR") or "").strip()
            kind = "unincorporated" if is_unincorporated(juris, county) else "city"
            gk = (juris, county, year, cat, kind)
            g = groups.setdefault(gk, dict(sub_to_bp=[], sub_to_ent=[], n=0,
                                           ministerial=0, discretionary=0, unlabelled=0,
                                           approved=0, pending=0, withdrawn=0, disapproved=0))
            g["n"] += 1
            pt = app["ptype"]
            g["ministerial" if pt == "Ministerial" else
              "discretionary" if pt == "Discretionary" else "unlabelled"] += 1
            st = app["status"].lower()
            if st in ("approved", "pending", "withdrawn", "disapproved"):
                g[st] += 1
            bp = parse_date(row.get("BP_ISSUE_DT1"))
            ent = parse_date(row.get("ENT_APPROVE_DT1"))
            for target, bucket in ((bp, "sub_to_bp"), (ent, "sub_to_ent")):
                if not target:
                    continue
                d = (target - app["submit"]).days
                if d < 0:
                    stats["negative_" + bucket] += 1
                elif d > MAX_SPAN:
                    stats["oversize_" + bucket] += 1
                else:
                    g[bucket].append(d)
            # validation pair: the jurisdiction's own label against the span
            if pt in ("Ministerial", "Discretionary") and ent and bp:
                span = (bp - ent).days
                if 0 <= span <= MAX_SPAN:
                    lk = (juris, county, cat)
                    lc = label_check.setdefault(lk, dict(min_spans=[], disc_spans=[]))
                    lc["min_spans" if pt == "Ministerial" else "disc_spans"].append(span)

    rows = []
    for (juris, county, year, cat, kind), g in sorted(groups.items()):
        rec = dict(jurisdiction=juris, county=county, year=year, unit_cat=cat, jurisdiction_kind=kind,
                   n_joined=g["n"], n_ministerial=g["ministerial"], n_discretionary=g["discretionary"],
                   n_unlabelled_project_type=g["unlabelled"], n_approved=g["approved"],
                   n_pending=g["pending"], n_withdrawn=g["withdrawn"], n_disapproved=g["disapproved"])
        for bucket, label in (("sub_to_bp", "submit_to_building_permit"),
                              ("sub_to_ent", "submit_to_entitlement")):
            v = g[bucket]
            rec["n_" + label] = len(v)
            rec["median_" + label] = quantile(v, .5)
            rec["p25_" + label] = quantile(v, .25)
            rec["p75_" + label] = quantile(v, .75)
            rec["p90_" + label] = quantile(v, .9)
        rows.append(rec)
    path = OUT / "apr_applicant_clock.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote %s  (%d group rows; %d of %d A2 rows matched an application)"
          % (path, len(rows), stats["matched"], stats["a2_rows"]))
    summary = dict(table_a=dict(astats), join=dict(stats), groups=len(rows))
    (OUT / "apr_applicant_clock_quality.json").write_text(json.dumps(summary, indent=1))
    return rows, summary, label_check


def report(rows, summary, label_check):
    adu = [r for r in rows if r["unit_cat"] == "ADU"]
    by: dict[tuple, list] = collections.defaultdict(list)
    for r in adu:
        if r["n_submit_to_building_permit"]:
            by[(r["jurisdiction"], r["county"], r["jurisdiction_kind"])].append(
                (r["n_submit_to_building_permit"], r["median_submit_to_building_permit"]))
    agg = [(j, c, k, sum(x[0] for x in v), statistics.median([x[1] for x in v]))
           for (j, c, k), v in by.items()]
    strong = sorted((a for a in agg if a[3] >= 30), key=lambda t: -t[3])
    print("\n=== ADU application-submission to building-permit, the applicant's clock")
    print("    jurisdictions with >=30 joined spans: %d" % len(strong))
    meds = sorted(a[4] for a in strong)
    if meds:
        print("    median of medians %.0f days; p25 %.0f; p75 %.0f; max %.0f"
              % (statistics.median(meds), quantile(meds, .25), quantile(meds, .75), meds[-1]))
        print("    jurisdictions with a median of 0 days on THIS clock: %d"
              % sum(1 for a in strong if a[4] == 0))
    for j, c, k, n, med in strong[:10]:
        print("      %-26s %-14s %-15s n=%5d  median %4.0f d" % (j[:26], c[:14], k, n, med))

    print("\n=== validation: does a zero entitlement-to-permit span mean 'ministerial'?")
    print("    (the jurisdiction's own PROJECT_TYPE label versus the observed span)")
    mins = [d for lc in label_check.values() for d in lc["min_spans"]]
    disc = [d for lc in label_check.values() for d in lc["disc_spans"]]
    if mins and disc:
        print("    labelled Ministerial:   n=%6d  median %5.0f d  share zero %.0f%%"
              % (len(mins), statistics.median(mins), 100 * sum(1 for d in mins if d == 0) / len(mins)))
        print("    labelled Discretionary: n=%6d  median %5.0f d  share zero %.0f%%"
              % (len(disc), statistics.median(disc), 100 * sum(1 for d in disc if d == 0) / len(disc)))
    print("\n=== outcomes, all unit categories")
    tot = {k: sum(r["n_" + k] for r in rows) for k in ("approved", "pending", "withdrawn", "disapproved")}
    print("    " + "  ".join("%s %d" % (k, v) for k, v in tot.items()))
    lab = {k: sum(r["n_" + k] for r in rows) for k in ("ministerial", "discretionary", "unlabelled_project_type")}
    print("    " + "  ".join("%s %d" % (k, v) for k, v in lab.items()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args(argv)
    rows, summary, label_check = run()
    report(rows, summary, label_check)


if __name__ == "__main__":
    main()
