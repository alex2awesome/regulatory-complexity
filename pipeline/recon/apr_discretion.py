#!/usr/bin/env python3
"""Measuring the discretion residual on real data: who calls an ADU ministerial?

Work packet P9-DISCRETION-REAL of docs/scoping/WORK_PACKETS.json.

The project's thesis is that a statute underdetermines a decision function, that
each jurisdiction resolves the underdetermination its own way, and that
cross-jurisdiction disagreement is therefore the empirical measure of the
statute's discretion. Everywhere else in this repo that quantity is synthetic.
Here it is real.

HCD APR **Table A** carries `PROJECT_TYPE`: the jurisdiction's own statement,
for each housing application it received, of whether its process routed that
application through a discretionary step ("Discretionary") or not
("Ministerial"). Two jurisdictions applying the same state ADU law and
disagreeing about that label are disagreeing about the decision function. One
jurisdiction that labels some of its own ADU applications one way and some the
other is running a *conditional* rule, which is a strictly stronger claim about
where the discretion lives: not in a fixed jurisdiction effect, but in a
predicate evaluated case by case.

So this builder computes, per (jurisdiction, county, application year, unit
category):

    ministerial_share   share of *labelled* applications the jurisdiction
                        itself calls Ministerial
    outcome shares      approved / pending / withdrawn / disapproved
    the applicant clock  median days from APP_SUBMIT_DT to BP_ISSUE_DT1, and
                        the same split by the label, so the label can be
                        scored against realised timing inside a single
                        jurisdiction-year

and answers five questions in report(): how bimodal the share is, whether it
moved over 2018-2025, whether the label predicts timing, whether county
covariates predict the label better than they predict timing (they barely
predict timing: r about 0.2, per the P0-APR-TIMING report), and whether
withdrawal tracks a long clock, which is the abandonment channel the synthetic
simulator models.

Three things this shares with pipeline/recon/apr_permit_timing.py and
pipeline/recon/apr_join_clocks.py, by import rather than by copy: the date
parser, the quantile helper, the (jurisdiction, APN, unit category) join key,
and the `is_unincorporated` test. That last one matters most. A row named
"LOS ANGELES" is the CITY; "LOS ANGELES COUNTY" is the unincorporated county
area. They are two different processes under the same statute and pooling them
destroys exactly the variation this packet measures.

Two deliberate differences from apr_join_clocks.py, both documented in the
report: this file counts **applications** (Table A rows) rather than permit
records, and it attaches at most **one** span per application by taking the
earliest building permit for that parcel, so a 6-unit project contributes one
observation instead of six. Span counts here are therefore lower than in
corpus/counties/apr_applicant_clock.csv and are not interchangeable with them.

    python3 pipeline/recon/apr_discretion.py
    python3 pipeline/recon/apr_discretion.py --min-labelled 30 --cats ADU,SFD,5+
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import json
import math
import pathlib
import random
import statistics
import sys

# Reuse, do not reimplement: the date parser, quantiles, the join key and the
# city-versus-unincorporated test all come from the existing APR builders.
from apr_join_clocks import is_unincorporated, key_of, parse_date, quantile

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "corpus/counties/raw"
OUT = ROOT / "corpus/counties"
COVARIATES = OUT / "ca_counties_covariates.csv"
csv.field_size_limit(1 << 24)

MAX_SPAN = 3650                  # a decade; beyond that the date pair is an error
FOLLOW_UP_DAYS = 365             # window for the censoring-robust permit rate
# Both date columns carry a few impossible values (a 2048 and a 2109 building
# permit, an 1899 and a 2819 application). They must not be allowed to set the
# end of the observation window, so the "as of" date is capped at the end of the
# last reporting year in the file and dates outside the window are counted, not
# silently used.
EARLIEST_PLAUSIBLE = datetime.date(2010, 1, 1)
MINISTERIAL, DISCRETIONARY = "Ministerial", "Discretionary"
STATUSES = ("approved", "pending", "withdrawn", "disapproved")
NEAR = 0.05                      # |share - 0| or |share - 1| under this is "near"


# --------------------------------------------------------------------------- #
# loading

def _int(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


def new_group():
    return dict(n_applications=0, apns=set(), ministerial=0, discretionary=0, unlabelled=0,
                status_stated=0, proposed=0, approved_units=0, disapproved_units=0,
                proposed_min=0, proposed_disc=0,
                spans=[], spans_min=[], spans_disc=[], spans_ent=[],
                eligible=0, within=0, within_min=0, within_disc=0,
                eligible_min=0, eligible_disc=0,
                matched_min=0, matched_disc=0, ent_min=0, ent_disc=0,
                **{s: 0 for s in STATUSES})


def load_applications():
    """Table A: the per-application register, grouped, plus a join index.

    Returns (groups, apps, stats). `groups` is keyed on
    (jurisdiction, county, year, unit_cat, kind) and counts every Table A row.
    `apps` is keyed on the (jurisdiction, APN, unit_cat) join key and keeps the
    earliest submittal for that key, which is how apr_join_clocks.py resolves
    the duplicate parcel numbers that are endemic to this file.
    """
    groups: dict[tuple, dict] = {}
    apps: dict[tuple, dict] = {}
    stats = collections.Counter()
    with (RAW / "apr_table_a.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            stats["rows"] += 1
            juris = (row.get("JURIS_NAME") or "").strip()
            county = (row.get("CNTY_NAME") or "").strip()
            year = (row.get("YEAR") or "").strip()
            cat = (row.get("UNIT_CAT") or "").strip()
            if not juris or not county or not year:
                stats["row_missing_key_fields"] += 1
                continue
            kind = "unincorporated" if is_unincorporated(juris, county) else "city"
            stats["row_" + kind] += 1
            gk = (juris, county, year, cat, kind)
            g = groups.setdefault(gk, new_group())
            g["n_applications"] += 1
            apn = (row.get("APN") or "").strip()
            if apn:
                if apn in g["apns"]:
                    stats["duplicate_apn_within_group"] += 1
                g["apns"].add(apn)
            ptype = (row.get("PROJECT_TYPE") or "").strip()
            units = _int(row.get("TOT_PROPOSED_UNITS"))
            if ptype == MINISTERIAL:
                g["ministerial"] += 1
                g["proposed_min"] += units
            elif ptype == DISCRETIONARY:
                g["discretionary"] += 1
                g["proposed_disc"] += units
            else:
                g["unlabelled"] += 1
                if ptype:
                    stats["project_type_unexpected_value"] += 1
            status = (row.get("APPLICATION_STATUS") or "").strip().lower()
            if status in STATUSES:
                g[status] += 1
                g["status_stated"] += 1
            elif status:
                stats["status_unexpected_value"] += 1
            g["proposed"] += _int(row.get("TOT_PROPOSED_UNITS"))
            g["approved_units"] += _int(row.get("TOT_APPROVED_UNITS"))
            g["disapproved_units"] += _int(row.get("TOT_DISAPPROVED_UNITS"))

            k = key_of(row)
            submit = parse_date(row.get("APP_SUBMIT_DT"))
            if not k:
                stats["no_join_key"] += 1
                continue
            if not submit:
                stats["no_submit_date"] += 1
                continue
            rec = apps.get(k)
            if rec is None:
                apps[k] = dict(submit=submit, group=gk, ptype=ptype,
                               units=_int(row.get("TOT_PROPOSED_UNITS")))
            else:
                stats["duplicate_join_key"] += 1
                if submit < rec["submit"]:
                    rec.update(submit=submit, group=gk, ptype=ptype,
                               units=_int(row.get("TOT_PROPOSED_UNITS")))
                rec["ptype"] = rec["ptype"] or ptype

    # The label's missingness is a filing decision, not a per-project one. If
    # that is true, no jurisdiction-year should be *partially* labelled.
    for (juris, county, year, cat, kind), g in groups.items():
        lab = g["ministerial"] + g["discretionary"]
        state = ("unlabelled" if lab == 0 else
                 "fully_labelled" if g["unlabelled"] == 0 else "partially_labelled")
        stats["%s_juris_years_%s" % (cat or "blank", state)] += 1
        if lab and year.isdigit() and int(year) < 2022:
            stats["pre2022_labelled_juris_year_groups"] += 1
    stats["jurisdictions_with_any_label"] = len(
        {(j, c) for (j, c, y, cat, k), g in groups.items() if g["ministerial"] + g["discretionary"]})
    stats["jurisdictions_total"] = len({(j, c) for (j, c, y, cat, k) in groups})
    return groups, apps, stats


def attach_timing(groups, apps):
    """Table A2: earliest building permit and entitlement per application key.

    One span per application, not one per permit record: a multi-unit project
    files many A2 rows against one parcel and counting each of them would
    weight the timing distribution by project size.
    """
    stats = collections.Counter()
    best: dict[tuple, dict] = {}
    max_year = 0
    with (RAW / "apr_table_a2.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            stats["a2_rows"] += 1
            y = (row.get("YEAR") or "").strip()
            if y.isdigit():
                max_year = max(max_year, int(y))
            k = key_of(row)
            if not k or k not in apps:
                stats["unmatched_a2_row"] += 1
                continue
            stats["matched_a2_row"] += 1
            slot = best.setdefault(k, dict(bp=None, ent=None))
            for col, name in (("BP_ISSUE_DT1", "bp"), ("ENT_APPROVE_DT1", "ent")):
                d = parse_date(row.get(col))
                if d and (slot[name] is None or d < slot[name]):
                    slot[name] = d
    stats["matched_application_keys"] = len(best)

    # The observation window ends at the later of the last credible permit and
    # the end of the last reporting year, never at an impossible 2048 date.
    end_of_window = datetime.date(max_year, 12, 31) if max_year else None
    plausible = [s["bp"] for s in best.values()
                 if s["bp"] and (not end_of_window or s["bp"] <= end_of_window)]
    as_of = max(plausible) if plausible else None
    stats["bp_dates_after_window"] = sum(1 for s in best.values()
                                         if s["bp"] and end_of_window and s["bp"] > end_of_window)
    cutoff = as_of - datetime.timedelta(days=FOLLOW_UP_DAYS) if as_of else None
    for k, app in apps.items():
        g = groups[app["group"]]
        arm = ("min" if app["ptype"] == MINISTERIAL else
               "disc" if app["ptype"] == DISCRETIONARY else None)
        eligible = False
        if not (EARLIEST_PLAUSIBLE <= app["submit"] <= (as_of or app["submit"])):
            stats["submit_date_outside_window"] += 1
        elif cutoff and app["submit"] <= cutoff:
            eligible = True
            g["eligible"] += 1
            if arm:
                g["eligible_" + arm] += 1
        slot = best.get(k)
        if not slot:
            continue
        if slot["bp"]:
            d = (slot["bp"] - app["submit"]).days
            if d < 0:
                stats["negative_submit_to_bp"] += 1
            elif d > MAX_SPAN:
                stats["oversize_submit_to_bp"] += 1
            else:
                g["spans"].append(d)
                if arm:
                    g["spans_" + arm].append(d)
                if eligible and d <= FOLLOW_UP_DAYS:
                    g["within"] += 1
                    if arm:
                        g["within_" + arm] += 1
        # The tempting substitute for the missing pre-2022 label is "a ministerial
        # project has no entitlement to date". Score it here so it can be rejected
        # with a number instead of an intuition.
        if arm:
            stats["%s_with_entitlement_date" % arm] += 1 if slot["ent"] else 0
            stats["%s_matched_keys" % arm] += 1
            g["matched_" + arm] += 1
            if slot["ent"]:
                g["ent_" + arm] += 1
        if slot["ent"]:
            d = (slot["ent"] - app["submit"]).days
            if 0 <= d <= MAX_SPAN:
                g["spans_ent"].append(d)
            else:
                stats["bad_submit_to_ent"] += 1
    stats["as_of_date"] = str(as_of)
    stats["follow_up_cutoff"] = str(cutoff)
    return stats


# --------------------------------------------------------------------------- #
# the output table

def share(num, den, digits=4):
    return round(num / den, digits) if den else None


def to_rows(groups):
    rows = []
    for (juris, county, year, cat, kind), g in sorted(groups.items()):
        labelled = g["ministerial"] + g["discretionary"]
        rec = dict(jurisdiction=juris, county=county, year=year, unit_cat=cat,
                   jurisdiction_kind=kind,
                   n_applications=g["n_applications"], n_distinct_apn=len(g["apns"]),
                   n_labelled=labelled, n_ministerial=g["ministerial"],
                   n_discretionary=g["discretionary"], n_unlabelled=g["unlabelled"],
                   ministerial_share=share(g["ministerial"], labelled),
                   n_status_stated=g["status_stated"])
        for s in STATUSES:
            rec["n_" + s] = g[s]
        for s in STATUSES:
            rec[s + "_share"] = share(g[s], g["status_stated"])
        rec.update(tot_proposed_units=g["proposed"], tot_approved_units=g["approved_units"],
                   tot_disapproved_units=g["disapproved_units"],
                   proposed_units_ministerial=g["proposed_min"],
                   proposed_units_discretionary=g["proposed_disc"],
                   mean_units_ministerial=share(g["proposed_min"], g["ministerial"], 3),
                   mean_units_discretionary=share(g["proposed_disc"], g["discretionary"], 3))
        for label, vals in (("submit_to_bp", g["spans"]),
                            ("submit_to_bp_ministerial", g["spans_min"]),
                            ("submit_to_bp_discretionary", g["spans_disc"]),
                            ("submit_to_entitlement", g["spans_ent"])):
            rec["n_" + label] = len(vals)
            rec["median_" + label] = quantile(vals, .5)
            if label == "submit_to_bp":
                rec["p25_" + label] = quantile(vals, .25)
                rec["p75_" + label] = quantile(vals, .75)
        rec.update(n_matched_ministerial=g["matched_min"], n_matched_discretionary=g["matched_disc"],
                   n_matched_ministerial_with_ent_date=g["ent_min"],
                   n_matched_discretionary_with_ent_date=g["ent_disc"],
                   n_eligible_365=g["eligible"], n_permit_within_365=g["within"],
                   permit_within_365_share=share(g["within"], g["eligible"]),
                   n_eligible_365_ministerial=g["eligible_min"],
                   n_permit_within_365_ministerial=g["within_min"],
                   n_eligible_365_discretionary=g["eligible_disc"],
                   n_permit_within_365_discretionary=g["within_disc"])
        rows.append(rec)
    return rows


def write_rows(rows, path):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


# --------------------------------------------------------------------------- #
# statistics helpers (stdlib only, in the style of the sibling builders)

def share_quantile(vals, q):
    """The imported `quantile` rounds to whole-day precision, which turns a
    withdrawal share of 0.0035 into 0.0. Shares need four digits."""
    if not vals:
        return None
    v = sorted(vals)
    if len(v) == 1:
        return round(float(v[0]), 4)
    pos = q * (len(v) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (pos - lo), 4)


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None, len(pairs)
    a, b = [p[0] for p in pairs], [p[1] for p in pairs]
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None, len(pairs)
    return round(statistics.correlation(a, b), 3), len(pairs)


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None, len(pairs)
    a, b = [p[0] for p in pairs], [p[1] for p in pairs]
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None, len(pairs)
    return round(statistics.correlation(a, b, method="ranked"), 3), len(pairs)


def boot_ci(vals, stat=statistics.median, n=2000, seed=11, lo=2.5, hi=97.5):
    """Percentile bootstrap. Returns (point, lo, hi) or None if too few values."""
    if len(vals) < 4:
        return None
    rng = random.Random(seed)
    draws = sorted(stat([rng.choice(vals) for _ in vals]) for _ in range(n))
    return (round(stat(vals), 1), round(quantile(draws, lo / 100), 1),
            round(quantile(draws, hi / 100), 1))


def sign_test_p(pos, neg):
    """Two-sided exact binomial p for pos successes out of pos+neg at p=1/2."""
    n = pos + neg
    if n == 0:
        return None
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, round(2 * tail, 5))


def norm_county(name):
    return (name or "").strip().upper().replace(" COUNTY", "").strip()


def load_covariates():
    cov = {}
    if not COVARIATES.exists():
        return cov
    with COVARIATES.open(newline="") as f:
        for row in csv.DictReader(f):
            cov[norm_county(row["county"])] = row
    return cov


def num(row, col):
    v = (row.get(col) or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# the five questions

def bucket(s):
    if s <= NEAR:
        return "near 0 (all discretionary)"
    if s < 0.35:
        return "0.05-0.35"
    if s <= 0.65:
        return "0.35-0.65 (genuinely mixed)"
    if s < 1 - NEAR:
        return "0.65-0.95"
    return "near 1 (all ministerial)"


BUCKETS = ["near 0 (all discretionary)", "0.05-0.35", "0.35-0.65 (genuinely mixed)",
           "0.65-0.95", "near 1 (all ministerial)"]


def q1_shares(rows, cats, min_labelled):
    print("\n=== Q1. per-(jurisdiction, year) ministerial share, >=%d labelled applications"
          % min_labelled)
    print("  first, every unit category, all jurisdiction-years pooled: the statewide")
    print("  ministerial share is a near-monotone gradient in project size")
    tot = collections.Counter()
    mini = collections.Counter()
    for r in rows:
        tot[r["unit_cat"]] += r["n_labelled"]
        mini[r["unit_cat"]] += r["n_ministerial"]
    gradient = {}
    for cat, n in sorted(tot.items(), key=lambda t: -(mini[t[0]] / t[1] if t[1] else 0)):
        if not n:
            continue
        gradient[cat] = dict(labelled=n, ministerial_share=round(mini[cat] / n, 4))
        print("    %-8s labelled %7d   ministerial share %.4f" % (cat, n, mini[cat] / n))
    out = {"_gradient_all_categories": gradient}
    for cat in cats:
        cells = [r for r in rows if r["unit_cat"] == cat and r["n_labelled"] >= min_labelled]
        if not cells:
            print("  %-6s not computable: no jurisdiction-year reaches %d labelled applications"
                  % (cat, min_labelled))
            continue
        shares = [r["ministerial_share"] for r in cells]
        hist = collections.Counter(bucket(s) for s in shares)
        jur = {(r["jurisdiction"], r["county"]) for r in cells}
        print("  %-6s %d jurisdiction-years, %d distinct jurisdictions, %d labelled applications"
              % (cat, len(cells), len(jur), sum(r["n_labelled"] for r in cells)))
        print("         mean share %.3f  median %.3f  pooled %.3f"
              % (statistics.fmean(shares), statistics.median(shares),
                 sum(r["n_ministerial"] for r in cells) / sum(r["n_labelled"] for r in cells)))
        for b in BUCKETS:
            n = hist.get(b, 0)
            print("           %-32s %5d  %5.1f%%" % (b, n, 100 * n / len(cells)))
        mixed = [r for r in cells if NEAR < r["ministerial_share"] < 1 - NEAR]
        print("         interior (%.2f < share < %.2f): %d of %d jurisdiction-years (%.1f%%)"
              % (NEAR, 1 - NEAR, len(mixed), len(cells), 100 * len(mixed) / len(cells)))
        print("         largest mixed jurisdiction-years:")
        for r in sorted(mixed, key=lambda r: -r["n_labelled"])[:8]:
            print("           %-26s %-12s %s  n=%4d  share %.2f"
                  % (r["jurisdiction"][:26], r["county"][:12], r["year"],
                     r["n_labelled"], r["ministerial_share"]))
        allnone = [r for r in cells if r["ministerial_share"] <= NEAR]
        if allnone:
            print("         largest all-discretionary jurisdiction-years:")
            for r in sorted(allnone, key=lambda r: -r["n_labelled"])[:8]:
                print("           %-26s %-12s %s  n=%4d  share %.2f"
                      % (r["jurisdiction"][:26], r["county"][:12], r["year"],
                         r["n_labelled"], r["ministerial_share"]))

        # Is the cross-jurisdiction spread real, or is it binomial noise? This is
        # the plan's §4.3 discretion residual, as a variance ratio. Under a single
        # statewide decision rule with probability p, each cell's share would vary
        # only by sampling, with variance p(1-p)/n.
        pooled_p = sum(r["n_ministerial"] for r in cells) / sum(r["n_labelled"] for r in cells)
        var_obs = statistics.pvariance(shares)
        var_exp = statistics.fmean([pooled_p * (1 - pooled_p) / r["n_labelled"] for r in cells])
        ratio = var_obs / var_exp if var_exp else None
        print("         cross-jurisdiction dispersion: observed variance of the share %.5f;"
              % var_obs)
        print("           binomial expectation under one statewide rule %.5f; ratio %s"
              % (var_exp, "%.0f x" % ratio if ratio else "not computable"))

        # How concentrated is the discretion? If a handful of jurisdictions carry
        # all of it, the county effect is a few outliers, not a gradient.
        disc_by_j = collections.Counter()
        for r in cells:
            disc_by_j[(r["jurisdiction"], r["county"])] += r["n_discretionary"]
        tot_disc = sum(disc_by_j.values())
        top10 = sum(v for _, v in disc_by_j.most_common(10))
        print("         %d discretionary-labelled applications in these cells; the top 10 "
              "jurisdictions hold %d (%.0f%%)"
              % (tot_disc, top10, 100 * top10 / tot_disc if tot_disc else 0))
        print("         jurisdictions with at least one discretionary application: %d of %d"
              % (sum(1 for v in disc_by_j.values() if v), len(disc_by_j)))

        # Same thing pooled over the years, which is the per-jurisdiction rule
        # rather than the per-jurisdiction-year one, and the level at which the
        # hierarchical model would place a county or jurisdiction effect.
        per_j = collections.defaultdict(lambda: [0, 0, []])
        for r in rows:
            if r["unit_cat"] != cat:
                continue
            p = per_j[(r["jurisdiction"], r["county"], r["jurisdiction_kind"])]
            p[0] += r["n_labelled"]
            p[1] += r["n_ministerial"]
            if r["median_submit_to_bp"] is not None and r["n_submit_to_bp"] >= 10:
                p[2].append(r["median_submit_to_bp"])
        pooled_j = {k: v for k, v in per_j.items() if v[0] >= min_labelled}
        js = {k: v[1] / v[0] for k, v in pooled_j.items()}
        n1 = sum(1 for s in js.values() if s >= 1 - NEAR)
        n0 = sum(1 for s in js.values() if s <= NEAR)
        print("         pooled over years, %d jurisdictions with >=%d labelled: near 1 %d (%.0f%%),"
              % (len(js), min_labelled, n1, 100 * n1 / len(js)))
        print("           near 0 %d (%.0f%%), interior %d (%.0f%%)"
              % (n0, 100 * n0 / len(js), len(js) - n1 - n0, 100 * (len(js) - n1 - n0) / len(js)))
        for title, sel in (("persistently discretionary (share <= %.2f)" % NEAR,
                            lambda s: s <= NEAR),
                           ("conditional rule (%.2f < share < %.2f)" % (NEAR, 1 - NEAR),
                            lambda s: NEAR < s < 1 - NEAR)):
            picked = sorted(((pooled_j[k][0], k, s) for k, s in js.items() if sel(s)), reverse=True)
            print("           %s: %d jurisdictions; largest by volume:" % (title, len(picked)))
            for n, k, s in picked[:8]:
                clk = pooled_j[k][2]
                print("             %-26s %-16s labelled %5d  share %.3f  median clock %s"
                      % (k[0][:26], k[1][:16], n, s,
                         "%.0f d" % statistics.median(clk) if clk else "not computable"))

        # The decisive cross-jurisdiction test: does a jurisdiction's stated rule
        # explain how long it actually takes, once we compare jurisdictions to
        # each other rather than projects inside one of them?
        sh_clk = [(s, statistics.median(pooled_j[k][2])) for k, s in js.items() if pooled_j[k][2]]
        if len(sh_clk) >= 10:
            r_b, n_b = pearson([a for a, _ in sh_clk], [b for _, b in sh_clk])
            s_b, _ = spearman([a for a, _ in sh_clk], [b for _, b in sh_clk])
            print("         BETWEEN jurisdictions, pooled share vs median applicant clock: "
                  "pearson %s, spearman %s (n=%d)" % (r_b, s_b, n_b))

        # The trap, turned into a measurement. Many California counties contain a
        # city of the same name, so "LOS ANGELES" and "LOS ANGELES COUNTY" are two
        # processes under one statute. Where both have enough volume they are a
        # matched pair: same county, same law, different administration.
        pairs = []
        for (j, c, kind), v in pooled_j.items():
            if kind != "city" or norm_county(j) != norm_county(c):
                continue
            unin = pooled_j.get((norm_county(c).title().upper() + " COUNTY", c, "unincorporated"))
            if unin is None:
                unin = next((w for (j2, c2, k2), w in pooled_j.items()
                             if k2 == "unincorporated" and c2 == c), None)
            if unin:
                pairs.append((j, c, v, unin))
        if pairs:
            print("         same-name city vs unincorporated county, both >=%d labelled:"
                  % min_labelled)
            for j, c, city, unin in sorted(pairs, key=lambda t: -t[2][0]):
                cc, uc = city[2], unin[2]
                print("             %-18s city share %.4f clock %-12s | county share %.4f clock %s"
                      % (c[:18], city[1] / city[0],
                         "%.0f d" % statistics.median(cc) if cc else "n/a",
                         unin[1] / unin[0],
                         "%.0f d" % statistics.median(uc) if uc else "n/a"))

        by_kind = {}
        for kind in ("city", "unincorporated"):
            ks = [r for r in cells if r["jurisdiction_kind"] == kind]
            if not ks:
                continue
            p = sum(r["n_ministerial"] for r in ks) / sum(r["n_labelled"] for r in ks)
            by_kind[kind] = dict(cells=len(ks), pooled=round(p, 4),
                                 mean=round(statistics.fmean(r["ministerial_share"] for r in ks), 4))
            print("         %-16s %4d jurisdiction-years, pooled ministerial share %.3f"
                  % (kind, len(ks), p))
        out[cat] = dict(cells=len(cells), jurisdictions=len(jur),
                        histogram={b: hist.get(b, 0) for b in BUCKETS},
                        mean=round(statistics.fmean(shares), 4),
                        median=round(statistics.median(shares), 4),
                        interior_cells=len(mixed),
                        pooled=round(pooled_p, 4),
                        variance_observed=round(var_obs, 6),
                        variance_binomial=round(var_exp, 6),
                        overdispersion_ratio=round(ratio, 1) if ratio else None,
                        discretionary_applications=tot_disc,
                        discretionary_top10_share=round(top10 / tot_disc, 4) if tot_disc else None,
                        pooled_jurisdictions=len(js), pooled_near_1=n1, pooled_near_0=n0,
                        pooled_interior=len(js) - n1 - n0,
                        between_share_vs_clock_pearson=r_b if len(sh_clk) >= 10 else None,
                        between_share_vs_clock_spearman=s_b if len(sh_clk) >= 10 else None,
                        city_county_pairs=len(pairs),
                        by_kind=by_kind)
    return out


def q2_years(rows, cats, min_labelled, astats=None, jstats=None):
    print("\n=== Q2. did the label move over 2018-2025?")
    if astats:
        print("  the label's missingness is a filing decision, not a per-project one:")
        for cat in ("ADU", "SFD", "5+"):
            full = astats.get("%s_juris_years_fully_labelled" % cat, 0)
            part = astats.get("%s_juris_years_partially_labelled" % cat, 0)
            none = astats.get("%s_juris_years_unlabelled" % cat, 0)
            print("    %-5s %5d jurisdiction-years: %4d fully labelled, %d PARTIALLY, %4d unlabelled"
                  % (cat, full + part + none, full, part, none))
        print("    jurisdiction-year groups with any label before 2022: %d"
              % astats.get("pre2022_labelled_juris_year_groups", 0))
        print("    jurisdictions filing at least one label: %d of %d in the file"
              % (astats.get("jurisdictions_with_any_label", 0),
                 astats.get("jurisdictions_total", 0)))
    if jstats:
        print("  the tempting proxy for the missing years, scored and rejected:")
        print("    share of matched applications carrying an entitlement date")
        for arm, name in (("min", "Ministerial"), ("disc", "Discretionary")):
            n = jstats.get("%s_matched_keys" % arm, 0)
            k = jstats.get("%s_with_entitlement_date" % arm, 0)
            print("      labelled %-14s %6d matched keys, %6d with a date (%.1f%%)"
                  % (name, n, k, 100 * k / n if n else 0))
        print("    -> a 42-point separation, so the proxy is informative in aggregate. Whether")
        print("       it can carry a *jurisdiction-level* series depends on whether the")
        print("       class-conditional rate is a constant or is itself jurisdiction practice:")
        per = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            if r["n_matched_ministerial"]:
                p = per[(r["jurisdiction"], r["county"])]
                p[0] += r["n_matched_ministerial"]
                p[1] += r["n_matched_ministerial_with_ent_date"]
        strong = [v[1] / v[0] for v in per.values() if v[0] >= 30]
        if len(strong) >= 10:
            print("       P(entitlement date | Ministerial) across %d jurisdictions with >=30 "
                  "matched\n       ministerial applications: p10 %.2f, median %.2f, p90 %.2f; "
                  "%d are at 0.00 and %d at 1.00"
                  % (len(strong), share_quantile(strong, .1), statistics.median(strong),
                     share_quantile(strong, .9), sum(1 for x in strong if x == 0),
                     sum(1 for x in strong if x == 1)))
            print("       -> the rate is not a constant, so the proxy cannot be inverted per")
            print("          jurisdiction; it is itself a reporting-practice variable.")
    print("  label coverage by reporting year, all unit categories:")
    cov = {}
    years = sorted({r["year"] for r in rows})
    for y in years:
        rs = [r for r in rows if r["year"] == y]
        apps = sum(r["n_applications"] for r in rs)
        lab = sum(r["n_labelled"] for r in rs)
        mini = sum(r["n_ministerial"] for r in rs)
        cov[y] = dict(applications=apps, labelled=lab,
                      label_coverage=share(lab, apps), ministerial_share=share(mini, lab))
        print("    %s  applications %6d  labelled %6d (%5.1f%%)  ministerial share of labelled %s"
              % (y, apps, lab, 100 * lab / apps if apps else 0,
                 "%.3f" % (mini / lab) if lab else "not computable (no labels)"))
    usable = [y for y in years if cov[y]["label_coverage"] and cov[y]["label_coverage"] >= .5]
    print("  years with >=50%% label coverage: %s" % (", ".join(usable) or "none"))
    print("  -> the 2018-2021 ministerial share is NOT COMPUTABLE from this field: HCD only")
    print("     required PROJECT_TYPE from the 2023 reporting year (2022 partial), so any")
    print("     pre-2022 series would be a self-selected handful of early filers.")

    switches = {}
    for cat in cats:
        print("\n  %-5s pooled ministerial share by reporting year (labelled applications only):"
              % cat)
        for y in years:
            rs = [r for r in rows if r["year"] == y and r["unit_cat"] == cat]
            lab = sum(r["n_labelled"] for r in rs)
            mini = sum(r["n_ministerial"] for r in rs)
            juris = len({(r["jurisdiction"], r["county"]) for r in rs if r["n_labelled"]})
            print("        %s  labelled %6d in %3d jurisdictions   share %s"
                  % (y, lab, juris,
                     "%.4f" % (mini / lab) if lab >= 100 else "not computable (<100 labelled)"))
        per = {}
        for r in rows:
            if r["unit_cat"] == cat and r["n_labelled"] >= min_labelled:
                per[(r["jurisdiction"], r["county"], r["year"])] = r
        pairs, crossed, strict = [], [], []
        for (j, c, y), r in per.items():
            nxt = per.get((j, c, str(int(y) + 1))) if y.isdigit() else None
            if not nxt:
                continue
            pairs.append((j, c, y, r["ministerial_share"], nxt["ministerial_share"], r, nxt))
            if (r["ministerial_share"] <= .5) != (nxt["ministerial_share"] <= .5):
                crossed.append(pairs[-1])
            if (r["ministerial_share"] <= .2 and nxt["ministerial_share"] >= .8) or \
               (r["ministerial_share"] >= .8 and nxt["ministerial_share"] <= .2):
                strict.append(pairs[-1])
        print("\n  %-5s consecutive jurisdiction-year pairs with >=%d labelled in both: %d"
              % (cat, min_labelled, len(pairs)))
        if not pairs:
            switches[cat] = dict(pairs=0)
            continue
        deltas = [p[4] - p[3] for p in pairs]
        print("        median year-over-year change in share %+.3f   mean %+.3f"
              % (statistics.median(deltas), statistics.fmean(deltas)))
        print("        crossed the 0.5 line: %d (%.1f%%);  0.2<->0.8 flips: %d"
              % (len(crossed), 100 * len(crossed) / len(pairs), len(strict)))
        for p in sorted(strict, key=lambda p: -(p[5]["n_labelled"] + p[6]["n_labelled"]))[:10]:
            j, c, y, a, b, r0, r1 = p
            print("          %-24s %-12s %s->%s  share %.2f -> %.2f  median clock %s -> %s d"
                  % (j[:24], c[:12], y, int(y) + 1, a, b,
                     r0["median_submit_to_bp"], r1["median_submit_to_bp"]))
        both = [p for p in strict if p[5]["median_submit_to_bp"] is not None
                and p[6]["median_submit_to_bp"] is not None
                and p[5]["n_submit_to_bp"] >= 5 and p[6]["n_submit_to_bp"] >= 5]
        print("        flips with >=5 measured spans on both sides: %d" % len(both))
        if both:
            signed = [(p[6]["median_submit_to_bp"] - p[5]["median_submit_to_bp"])
                      * (1 if p[4] > p[3] else -1) for p in both]
            ci = boot_ci(signed)
            print("        median change in the clock in the direction of more ministerial: %s"
                  % ("%+.1f d [%.1f, %.1f]" % ci if ci
                     else "not computable (%d flips, need >=4)" % len(both)))
        switches[cat] = dict(pairs=len(pairs), crossed=len(crossed), strict_flips=len(strict),
                             flips_with_timing=len(both),
                             median_delta=round(statistics.median(deltas), 4))
    return cov, switches


def q3_timing(rows, cats, min_arm):
    print("\n=== Q3. does the label predict the applicant clock, within jurisdiction-year?")
    print("  (>=%d measured submission-to-permit spans in each arm of the same cell)" % min_arm)
    out = {}
    for cat in cats:
        cells = [r for r in rows
                 if r["unit_cat"] == cat
                 and r["n_submit_to_bp_ministerial"] >= min_arm
                 and r["n_submit_to_bp_discretionary"] >= min_arm]
        pooled_m = sum(r["n_submit_to_bp_ministerial"] for r in rows if r["unit_cat"] == cat)
        pooled_d = sum(r["n_submit_to_bp_discretionary"] for r in rows if r["unit_cat"] == cat)
        print("\n  %-5s total measured spans: ministerial %d, discretionary %d" % (cat, pooled_m, pooled_d))
        if not cells:
            print("        within-cell comparison NOT COMPUTABLE: no (jurisdiction, year) cell has")
            print("        >=%d spans in both arms." % min_arm)
            out[cat] = dict(cells=0)
            continue
        diffs = [r["median_submit_to_bp_discretionary"] - r["median_submit_to_bp_ministerial"]
                 for r in cells]
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        ci = boot_ci(diffs)
        print("        cells: %d across %d jurisdictions"
              % (len(cells), len({(r["jurisdiction"], r["county"]) for r in cells})))
        print("        paired median(discretionary) - median(ministerial), days:")
        print("          median of differences %s"
              % ("%+.1f  95%% bootstrap [%+.1f, %+.1f]" % ci if ci else "not computable"))
        print("          discretionary slower in %d cells, faster in %d, tied in %d; sign-test p=%s"
              % (pos, neg, len(diffs) - pos - neg, sign_test_p(pos, neg)))
        # One jurisdiction (Los Angeles city) supplies several cells, so collapse
        # to one observation per jurisdiction before the sign test as well.
        per_j = collections.defaultdict(list)
        for r, d in zip(cells, diffs):
            per_j[(r["jurisdiction"], r["county"])].append(d)
        jd = [statistics.median(v) for v in per_j.values()]
        jpos = sum(1 for d in jd if d > 0)
        jneg = sum(1 for d in jd if d < 0)
        jci = boot_ci(jd)
        print("          collapsed to one observation per jurisdiction (%d): median %s;"
              % (len(jd), "%+.1f [%+.1f, %+.1f]" % jci if jci else "not computable"))
        print("            slower in %d, faster in %d; sign-test p=%s"
              % (jpos, jneg, sign_test_p(jpos, jneg)))
        for r in sorted(cells, key=lambda r: -(r["n_submit_to_bp_ministerial"]
                                               + r["n_submit_to_bp_discretionary"]))[:8]:
            print("          %-22s %-11s %s  min n=%4d med %5.0f | disc n=%4d med %5.0f"
                  % (r["jurisdiction"][:22], r["county"][:11], r["year"],
                     r["n_submit_to_bp_ministerial"], r["median_submit_to_bp_ministerial"],
                     r["n_submit_to_bp_discretionary"], r["median_submit_to_bp_discretionary"]))
        # censoring-robust: matched permit inside a year of submission, same cells
        rate_cells = [r for r in cells
                      if r["n_eligible_365_ministerial"] >= min_arm
                      and r["n_eligible_365_discretionary"] >= min_arm]
        if rate_cells:
            rd = [r["n_permit_within_365_discretionary"] / r["n_eligible_365_discretionary"]
                  - r["n_permit_within_365_ministerial"] / r["n_eligible_365_ministerial"]
                  for r in rate_cells]
            rci = boot_ci([round(100 * x, 2) for x in rd])
            print("        matched-permit-within-365-days rate, discretionary minus ministerial,")
            print("          over %d cells: %s percentage points"
                  % (len(rate_cells), "%+.1f [%+.1f, %+.1f]" % rci if rci else "not computable"))
        # The obvious confound, measured rather than asserted: are the
        # discretionary applications simply bigger projects? Proposed units is
        # the only complexity proxy Table A carries.
        um = sum(r["proposed_units_ministerial"] for r in cells)
        ud = sum(r["proposed_units_discretionary"] for r in cells)
        nm = sum(r["n_ministerial"] for r in cells)
        nd = sum(r["n_discretionary"] for r in cells)
        print("        complexity proxy in these cells: mean proposed units %.2f ministerial "
              "(n=%d) vs %.2f discretionary (n=%d)"
              % (um / nm if nm else float("nan"), nm, ud / nd if nd else float("nan"), nd))
        out[cat] = dict(cells=len(cells), pooled_ministerial_spans=pooled_m,
                        mean_units_ministerial=round(um / nm, 3) if nm else None,
                        mean_units_discretionary=round(ud / nd, 3) if nd else None,
                        pooled_discretionary_spans=pooled_d,
                        median_difference_days=ci[0] if ci else None,
                        ci=list(ci[1:]) if ci else None,
                        discretionary_slower_cells=pos, discretionary_faster_cells=neg,
                        sign_test_p=sign_test_p(pos, neg),
                        jurisdictions=len(jd),
                        jurisdiction_median_difference_days=jci[0] if jci else None,
                        jurisdiction_ci=list(jci[1:]) if jci else None,
                        jurisdiction_sign_test_p=sign_test_p(jpos, jneg))
    return out


PRIOR_TIMING = OUT / "apr_permit_timing.csv"


def prior_clock_check(cov, preds, cat="ADU", min_spans=30):
    """Reproduce the P0-APR-TIMING correlations, so the comparison is apples to apples.

    That report found county covariates barely predict timing (r about 0.2) using
    the *entitlement-to-building-permit* span, rolled up per jurisdiction with at
    least 30 spans and then to the county. This recomputes exactly that from
    corpus/counties/apr_permit_timing.csv. Any difference from the
    submission-to-permit correlations below is a difference in which clock is
    measured, not in the covariates.
    """
    if not PRIOR_TIMING.exists():
        print("  prior-clock cross-check NOT COMPUTABLE: %s is missing" % PRIOR_TIMING)
        return None
    per_j = collections.defaultdict(lambda: [0, []])
    with PRIOR_TIMING.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["unit_cat"] != cat or not (r["median_ent_to_bp"] or "").strip():
                continue
            slot = per_j[(r["jurisdiction"], r["county"])]
            slot[0] += int(r["n_ent_to_bp"] or 0)
            slot[1].append(float(r["median_ent_to_bp"]))
    by_county = collections.defaultdict(list)
    for (j, c), (n, meds) in per_j.items():
        if n >= min_spans:
            by_county[norm_county(c)].append(statistics.median(meds))
    names = sorted(k for k in by_county if k in cov)
    y = [statistics.median(by_county[k]) for k in names]
    print("\n  cross-check against the P0-APR-TIMING construction "
          "(%s entitlement-to-permit clock, jurisdictions with >=%d spans):" % (cat, min_spans))
    print("    %d counties; median of county medians %.0f days" % (len(names), statistics.median(y)))
    res = {}
    for label, col, tf in preds:
        xs = []
        for k in names:
            v = num(cov[k], col)
            xs.append(tf(v) if (tf and v and v > 0) else (None if tf else v))
        r_e, n_e = pearson(xs, y)
        s_e, _ = spearman(xs, y)
        res[label] = dict(pearson=r_e, spearman=s_e, n=n_e)
        print("    %-38s r %s  rho %s  (n=%d)"
              % (label, "n/a" if r_e is None else "%+.3f" % r_e,
                 "n/a" if s_e is None else "%+.3f" % s_e, n_e))
    return dict(counties=len(names), median_days=statistics.median(y), correlations=res)


def q4_covariates(rows, cov, cats, min_county_labelled):
    print("\n=== Q4. do county covariates predict the decision rule?")
    if not cov:
        print("  NOT COMPUTABLE: %s is missing." % COVARIATES)
        return {}
    preds = (("log population", "pop_2023", math.log),
             ("log local-govt employment", "local_govt_employment_2023", math.log),
             ("local-govt staff per 1k pop", "local_govt_empl_per_1k_pop", None),
             ("rurality code (higher = more rural)", "rucc_2023", None),
             ("median household income", "median_hh_income_2023", None),
             ("poverty rate", "poverty_rate_2023", None),
             ("pct bachelors", "pct_bachelors_2019_23", None),
             ("log population density", "pop_density_per_sqmi", math.log))
    out = {"_prior_entitlement_clock_check": prior_clock_check(cov, preds)}
    for cat in cats:
        by_county = collections.defaultdict(lambda: dict(lab=0, mini=0, spans=[]))
        for r in rows:
            if r["unit_cat"] != cat:
                continue
            c = by_county[norm_county(r["county"])]
            c["lab"] += r["n_labelled"]
            c["mini"] += r["n_ministerial"]
            if r["median_submit_to_bp"] is not None and r["n_submit_to_bp"] >= 10:
                c["spans"].append(r["median_submit_to_bp"])
        # Two different samples, on purpose. The label only exists where a county
        # filed it, so the share sample is thresholded on labelled volume. The
        # clock exists much more widely, and holding it to the same threshold
        # would make the comparison with the P0-APR-TIMING correlations unfair.
        share_names = sorted(k for k, v in by_county.items()
                             if v["lab"] >= min_county_labelled and k in cov)
        clock_names = sorted(k for k, v in by_county.items() if len(v["spans"]) >= 3 and k in cov)
        print("\n  %-5s counties with >=%d labelled applications and a covariate row: %d of 58"
              % (cat, min_county_labelled, len(share_names)))
        print("        counties with >=3 jurisdiction-year clock medians (the comparison "
              "sample): %d" % len(clock_names))
        if len(share_names) < 5:
            print("        NOT COMPUTABLE: fewer than 5 counties clear the label threshold.")
            out[cat] = dict(counties=len(share_names))
            continue
        y = [by_county[k]["mini"] / by_county[k]["lab"] for k in share_names]
        y_clock = [statistics.median(by_county[k]["spans"]) for k in clock_names]
        print("        county ministerial share: min %.3f  median %.3f  max %.3f"
              % (min(y), statistics.median(y), max(y)))
        if y_clock:
            print("        county median applicant clock: min %.0f  median %.0f  max %.0f d"
                  % (min(y_clock), statistics.median(y_clock), max(y_clock)))
        print("        %-38s %8s %9s | %8s %9s"
              % ("predictor", "r share", "rho share", "r clock", "rho clock"))
        res = {}

        def col_values(names, col, tf):
            xs = []
            for k in names:
                v = num(cov[k], col)
                xs.append(tf(v) if (tf and v and v > 0) else (None if tf else v))
            return xs

        for label, col, tf in preds:
            r_share, n = pearson(col_values(share_names, col, tf), y)
            s_share, _ = spearman(col_values(share_names, col, tf), y)
            r_clock, n_clock = pearson(col_values(clock_names, col, tf), y_clock)
            s_clock, _ = spearman(col_values(clock_names, col, tf), y_clock)
            fmt = lambda v: "n/a" if v is None else "%+.3f" % v
            print("        %-38s %8s %9s | %8s %9s"
                  % (label, fmt(r_share), fmt(s_share), fmt(r_clock), fmt(s_clock)))
            res[label] = dict(pearson_share=r_share, spearman_share=s_share, n_share=n,
                              pearson_clock=r_clock, spearman_clock=s_clock, n_clock=n_clock)
        best = max(((abs(v["pearson_share"]), k) for k, v in res.items()
                    if v["pearson_share"] is not None), default=None)
        best_clock = max(((abs(v["pearson_clock"]), k) for k, v in res.items()
                          if v["pearson_clock"] is not None), default=None)
        print("        strongest |r|: %s against the share; %s against the clock"
              % ("%s at %.2f" % (best[1], best[0]) if best else "not computable",
                 "%s at %.2f" % (best_clock[1], best_clock[0]) if best_clock
                 else "not computable (only %d counties have >=3 clock medians)"
                      % len(clock_names)))
        out[cat] = dict(counties_share=len(share_names), counties_clock=len(clock_names),
                        share_min=round(min(y), 4), share_median=round(statistics.median(y), 4),
                        share_max=round(max(y), 4), correlations=res,
                        strongest_share=[best[1], round(best[0], 3)] if best else None,
                        strongest_clock=([best_clock[1], round(best_clock[0], 3)]
                                         if best_clock else None))
    return out


def q5_outcomes(rows, cats, min_status):
    print("\n=== Q5. outcome structure, and does withdrawal track a long clock?")
    out = {}
    for cat in cats:
        rs = [r for r in rows if r["unit_cat"] == cat]
        tot = {s: sum(r["n_" + s] for r in rs) for s in STATUSES}
        stated = sum(r["n_status_stated"] for r in rs)
        apps = sum(r["n_applications"] for r in rs)
        print("\n  %-5s %d applications, status stated on %d (%.1f%%)"
              % (cat, apps, stated, 100 * stated / apps if apps else 0))
        print("        " + "  ".join("%s %d (%.2f%%)" % (s, tot[s], 100 * tot[s] / stated)
                                     for s in STATUSES))
        per = collections.defaultdict(lambda: dict(stated=0, spans=[], **{s: 0 for s in STATUSES}))
        for r in rs:
            p = per[(r["jurisdiction"], r["county"], r["jurisdiction_kind"])]
            p["stated"] += r["n_status_stated"]
            for s in STATUSES:
                p[s] += r["n_" + s]
            if r["median_submit_to_bp"] is not None and r["n_submit_to_bp"] >= 10:
                p["spans"].append((r["n_submit_to_bp"], r["median_submit_to_bp"]))
        keep = {k: v for k, v in per.items() if v["stated"] >= min_status}
        print("        jurisdictions with >=%d stated outcomes: %d" % (min_status, len(keep)))
        if not keep:
            out[cat] = dict(jurisdictions=0)
            continue
        wshare = [v["withdrawn"] / v["stated"] for v in keep.values()]
        pshare = [v["pending"] / v["stated"] for v in keep.values()]
        dshare = [v["disapproved"] / v["stated"] for v in keep.values()]
        print("        withdrawal share across jurisdictions: median %.4f  p90 %.4f  max %.4f"
              % (statistics.median(wshare), share_quantile(wshare, .9), max(wshare)))
        print("        pending share:     median %.3f  p90 %.3f" % (statistics.median(pshare),
                                                                    share_quantile(pshare, .9)))
        print("        disapproval share: median %.4f  max %.4f  jurisdictions with any: %d"
              % (statistics.median(dshare), max(dshare), sum(1 for d in dshare if d > 0)))
        clock = [statistics.median([m for _, m in v["spans"]]) if v["spans"] else None
                 for v in keep.values()]
        r_w, n_w = pearson(clock, wshare)
        s_w, _ = spearman(clock, wshare)
        r_p, n_p = pearson(clock, pshare)
        s_p, _ = spearman(clock, pshare)
        print("        withdrawal share vs median submission-to-permit clock: pearson %s, spearman %s (n=%d)"
              % (r_w, s_w, n_w))
        print("        pending share    vs median submission-to-permit clock: pearson %s, spearman %s (n=%d)"
              % (r_p, s_p, n_p))
        zero = sum(1 for v in keep.values() if v["withdrawn"] == 0)
        print("        jurisdictions reporting ZERO withdrawals: %d of %d (%.0f%%)"
              % (zero, len(keep), 100 * zero / len(keep)))
        top = sorted(((v["withdrawn"] / v["stated"], k, v) for k, v in keep.items()), reverse=True)[:8]
        for wsh, k, v in top:
            med = statistics.median([m for _, m in v["spans"]]) if v["spans"] else None
            print("          %-24s %-12s withdrawn %.3f of %5d   median clock %s"
                  % (k[0][:24], k[1][:12], wsh, v["stated"], med))
        out[cat] = dict(jurisdictions=len(keep), totals=tot, status_stated=stated,
                        withdrawal_median=round(statistics.median(wshare), 5),
                        withdrawal_vs_clock_pearson=r_w, withdrawal_vs_clock_spearman=s_w,
                        pending_vs_clock_pearson=r_p, pending_vs_clock_spearman=s_p,
                        jurisdictions_zero_withdrawals=zero, n_clock=n_w)
    return out


# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-labelled", type=int, default=20,
                    help="minimum labelled applications for a jurisdiction-year (default 20)")
    ap.add_argument("--min-arm", type=int, default=5,
                    help="minimum measured spans in each arm of a within-cell timing "
                         "comparison (default 5)")
    ap.add_argument("--min-county-labelled", type=int, default=100,
                    help="minimum labelled applications for a county in the covariate "
                         "correlations (default 100)")
    ap.add_argument("--min-status", type=int, default=100,
                    help="minimum stated outcomes for a jurisdiction in the outcome "
                         "section (default 100)")
    ap.add_argument("--cats", default="ADU,SFD,5+",
                    help="unit categories to report on (default ADU,SFD,5+: the near-fully "
                         "ministerial case, the mixed case and the contested case); "
                         "the output CSV always carries every category")
    ap.add_argument("--out", default=str(OUT / "apr_discretion_by_jurisdiction.csv"))
    a = ap.parse_args(argv)
    for p in (RAW / "apr_table_a.csv", RAW / "apr_table_a2.csv"):
        if not p.exists():
            sys.exit("missing %s; see WORK_PACKETS.json verified_assets" % p)
    cats = [c.strip() for c in a.cats.split(",") if c.strip()]

    groups, apps, astats = load_applications()
    print("Table A: %d rows -> %d (jurisdiction, county, year, category) groups, %d join keys"
          % (astats["rows"], len(groups), len(apps)))
    print("         %d duplicate join-key hits resolved to the earliest submittal; "
          "%d rows without a key; %d without a submittal date"
          % (astats["duplicate_join_key"], astats["no_join_key"], astats["no_submit_date"]))
    jstats = attach_timing(groups, apps)
    print("Table A2: %d rows, %d matched an application (%.1f%%), %d distinct application keys matched"
          % (jstats["a2_rows"], jstats["matched_a2_row"],
             100 * jstats["matched_a2_row"] / jstats["a2_rows"], jstats["matched_application_keys"]))
    print("         data as of %s; submissions on or before %s have a full %d-day follow-up"
          % (jstats["as_of_date"], jstats["follow_up_cutoff"], FOLLOW_UP_DAYS))
    print("         %d Table A rows are city jurisdictions, %d unincorporated county processes; "
          "%d rows repeat a parcel number already seen in their own group"
          % (astats["row_city"], astats["row_unincorporated"],
             astats["duplicate_apn_within_group"]))
    print("         %d matched keys carry a building-permit date after the reporting window "
          "(impossible dates, excluded from the window); %d applications have a submittal "
          "date outside it" % (jstats["bp_dates_after_window"], jstats["submit_date_outside_window"]))

    rows = to_rows(groups)
    path = write_rows(rows, pathlib.Path(a.out))
    print("wrote %s  (%d group rows)" % (path, len(rows)))

    summary = dict(source_table_a=str((RAW / "apr_table_a.csv").relative_to(ROOT)),
                   source_table_a2=str((RAW / "apr_table_a2.csv").relative_to(ROOT)),
                   table_a=dict(astats), join=dict(jstats), group_rows=len(rows),
                   thresholds=dict(min_labelled=a.min_labelled, min_arm=a.min_arm,
                                   min_county_labelled=a.min_county_labelled,
                                   min_status=a.min_status, follow_up_days=FOLLOW_UP_DAYS))
    cov = load_covariates()
    summary["q1_share_distribution"] = q1_shares(rows, cats, a.min_labelled)
    summary["q2_label_coverage"], summary["q2_switches"] = q2_years(
        rows, cats, a.min_labelled, astats, jstats)
    summary["q3_timing"] = q3_timing(rows, cats, a.min_arm)
    summary["q4_covariates"] = q4_covariates(rows, cov, cats, a.min_county_labelled)
    summary["q5_outcomes"] = q5_outcomes(rows, cats, a.min_status)
    # Derived from --out so an exploratory run with different thresholds cannot
    # silently overwrite the published quality report.
    qpath = path.with_name(path.stem.replace("_by_jurisdiction", "") + "_quality.json")
    qpath.write_text(json.dumps(summary, indent=1, default=str))
    print("\nwrote %s" % qpath)


if __name__ == "__main__":
    main()
