#!/usr/bin/env python3
"""The retrieval-closure ledger: one row per county x programme x evidence type.

Why this exists. The work-packet queue marks a packet `done` when its bounded
pass finishes and its budget is spent. That is **not** the same as its sources
being exhausted, and conflating the two produced a false claim that retrieval
was essentially complete. A packet that honestly reports "42 counties without a
verified well instruction" is `done` in the queue and *incomplete* in the world.

So closure is tracked separately, per target, with a status vocabulary that
cannot be satisfied by spending a budget:

    acquired_read       the document is cached AND a human or agent read it
    acquired_unread     cached but never read: a real and common state
    located_unfetched   the URL is known and recorded, the bytes are not here
    blocked             a named wall (403, Cloudflare, login, image-only PDF)
    not_located         searched to a stated depth and not found
    out_of_scope        the county genuinely does not run this programme
    unexamined          nobody has looked at this cell yet

`unexamined` is the default, so the ledger's honest starting position is that
almost everything is unknown. A cell only leaves `unexamined` when some
artifact on disk or some report says so. **A blank is never read as absence.**

The ledger is machine-built from what is actually on disk, then annotated from
the scoping reports' own tables, so it cannot drift from reality the way a
hand-maintained checklist does.

    python3 pipeline/recon/retrieval_closure.py build
    python3 pipeline/recon/retrieval_closure.py report
    python3 pipeline/recon/retrieval_closure.py next --limit 25
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "corpus/counties"
RAW = OUT / "raw"
LEDGER = OUT / "retrieval_closure.csv"

STATUSES = ("acquired_read", "acquired_unread", "located_unfetched", "blocked",
            "not_located", "out_of_scope", "unexamined")
CLOSED = ("acquired_read", "out_of_scope")          # the only statuses that need no more work

# The four programmes chosen in plan section 11, plus the three already swept.
PROGRAMMES = {
    "adu": "ADU permitting in the unincorporated area",
    "medical": "Medi-Cal eligibility determination",
    "elections": "Registrar of voters, mail-ballot processing",
    "ag_permits": "Agricultural commissioner restricted-materials permits",
    "ccw": "Concealed-carry licensing",
    "general_assistance": "General Assistance / General Relief",
    "env_health": "Environmental health: septic, wells, retail food",
}

# The evidence tiers the benchmark distinguishes (DESIGN.md three-tier model).
EVIDENCE = {
    "declared": "applicant-facing public page or checklist",
    "designed": "policy, handbook, SOP, ordinance or oversight report",
    "observed": "official statistics: counts, timing, outcomes",
    "user": "first-person accounts: forum, review, news",
}

# Which (programme, evidence) cells are in scope at all. A county registrar does
# not publish an applicant handbook; Medi-Cal timing is a state dataset, not a
# per-county page. Marking these out of scope up front stops the ledger from
# manufacturing thousands of impossible targets.
OUT_OF_SCOPE = {
    ("elections", "declared"),      # voter-facing material is state-standardised
    ("ag_permits", "user"),         # permit holders are businesses; no consumer forum
}


# Statewide datasets that carry a verified row for EVERY county. These close the
# `observed` tier for all 58 at once, and pretending otherwise would send agents
# to re-fetch per-county pages for data we already hold in one file. Each entry
# names the file, the verification, and what it does NOT cover.
STATEWIDE_OBSERVED = {
    "adu": dict(path="corpus/counties/raw/apr_table_a2.csv",
                verified="922,104 permit records, every jurisdiction, 2018-2025; joined to Table A",
                covers="per-project entitlement, permit and occupancy dates, plus ministerial label",
                not_covered="the clock starts at completeness, not initial submission"),
    "medical": dict(path="corpus/counties/raw/p6/p6_medical_renewals_by_county.csv",
                    verified="58 of 58 counties, 98 months 2018-01 to 2026-02, SAWS label per county-month",
                    covers="renewal completion by due date, ex parte split, consortium migration",
                    not_covered="APPLICATION timing: the performance workbook returned a challenge page"),
    "elections": dict(path="corpus/counties/raw/p6/p6_eavs_2024_public_release_csv.zip",
                      verified="6,461 rows of which California is exactly 58; 61 rejection items; cured/uncured",
                      covers="which predicate failed and whether it was cured, per county",
                      not_covered="only the 2024 wave is cached; 11 biennial waves exist"),
    "ag_permits": dict(path="corpus/counties/raw/p6/p6_dpr_restricted_material_permits.xlsx",
                       verified="per-county monthly permits, inspections and enforcement 2020-2025",
                       covers="permit and inspection volumes per county",
                       not_covered="no per-county processing time"),
}


def counties() -> list[str]:
    path = OUT / "ca_counties_covariates.csv"
    if not path.exists():
        raise SystemExit("need %s first (run build_county_covariates.py)" % path)
    return [r["county"] for r in csv.DictReader(path.open())]


def _cached_files() -> dict[str, list[str]]:
    """Every cached artifact, bucketed by the lowercased text of its path.

    Crude on purpose: it answers "did we fetch anything that mentions this
    county for this programme", which is the `acquired_unread` test. Reading is
    a separate, stronger claim that only a report can make.
    """
    out: dict[str, list[str]] = collections.defaultdict(list)
    if not RAW.exists():
        return out
    for p in RAW.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(RAW)).lower()].append(str(p.relative_to(ROOT)))
    return out


PROGRAMME_HINTS = {
    "adu": ("adu", "accessory", "granny"),
    "medical": ("medical", "medi-cal", "medical_", "dhcs"),
    "elections": ("eavs", "election", "registrar"),
    "ag_permits": ("dpr", "pesticide", "restricted_material", "rmp"),
    "ccw": ("ccw", "permitium", "sheriff"),
    "general_assistance": ("ga/", "general_assistance", "general-relief", "generalrelief"),
    "env_health": ("lamp", "owts", "septic", "well", "food", "env_health", "environmental"),
}


def build() -> list[dict]:
    rows = []
    cache = _cached_files()
    cache_paths = list(cache)
    for county in counties():
        slug = county.lower().replace(" ", "")
        slug2 = county.lower().replace(" ", "_")
        slug3 = county.lower().replace(" ", "-")
        for prog, prog_label in PROGRAMMES.items():
            hints = PROGRAMME_HINTS[prog]
            hit = None
            for path in cache_paths:
                if any(s in path for s in (slug, slug2, slug3)) and any(h in path for h in hints):
                    hit = cache[path][0]
                    break
            for tier, tier_label in EVIDENCE.items():
                status = "unexamined"
                note = ""
                evidence = ""
                sw = STATEWIDE_OBSERVED.get(prog)
                if (prog, tier) in OUT_OF_SCOPE:
                    status, note = "out_of_scope", "not a per-county artifact for this programme"
                elif tier == "observed" and sw and (ROOT / sw["path"]).exists():
                    # A verified statewide file with a row per county closes this
                    # tier for every county at once.
                    status = "acquired_read"
                    evidence = sw["path"]
                    note = "statewide dataset, %s. NOT covered: %s" % (sw["verified"], sw["not_covered"])
                elif hit:
                    # A cached file proves acquisition, never reading, and never
                    # which tier it belongs to. Record the weaker claim.
                    status = "acquired_unread"
                    evidence = hit
                    note = "a cached artifact mentions this county and programme; tier unconfirmed"
                rows.append(dict(county=county, programme=prog, programme_label=prog_label,
                                 evidence_tier=tier, evidence_label=tier_label,
                                 status=status, evidence_path=evidence, note=note,
                                 searched_depth="", source_report=""))
    return rows


def load() -> list[dict]:
    if not LEDGER.exists():
        return []
    return list(csv.DictReader(LEDGER.open()))


def save(rows: list[dict]):
    cols = ["county", "programme", "programme_label", "evidence_tier", "evidence_label",
            "status", "evidence_path", "note", "searched_depth", "source_report"]
    with LEDGER.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def cmd_build(a):
    existing = {(r["county"], r["programme"], r["evidence_tier"]): r for r in load()}
    rows = build()
    kept = 0
    for r in rows:
        key = (r["county"], r["programme"], r["evidence_tier"])
        old = existing.get(key)
        # Never downgrade a human/agent annotation to a machine guess.
        if old and old["status"] not in ("unexamined", "acquired_unread"):
            r.update(old)
            kept += 1
        elif old and old["status"] == "acquired_unread" and r["status"] == "unexamined":
            r.update(old)
            kept += 1
    save(rows)
    print("wrote %s: %d cells (%d counties x %d programmes x %d tiers), %d annotations preserved"
          % (LEDGER, len(rows), len(counties()), len(PROGRAMMES), len(EVIDENCE), kept))


def cmd_report(a):
    rows = load() or build()
    by_status = collections.Counter(r["status"] for r in rows)
    total = len(rows)
    inscope = sum(1 for r in rows if r["status"] != "out_of_scope")
    closed = sum(1 for r in rows if r["status"] in CLOSED)
    print("retrieval closure: %d cells, %d in scope" % (total, inscope))
    print("  CLOSED (read or out of scope): %d of %d = %.0f%%" % (closed, total, 100 * closed / total))
    print("\nby status:")
    for s in STATUSES:
        n = by_status.get(s, 0)
        if n:
            print("  %-18s %5d  %4.1f%%" % (s, n, 100 * n / total))
    print("\nby programme (share of in-scope cells that are read):")
    for prog in PROGRAMMES:
        cells = [r for r in rows if r["programme"] == prog and r["status"] != "out_of_scope"]
        read = sum(1 for r in cells if r["status"] == "acquired_read")
        have = sum(1 for r in cells if r["status"].startswith("acquired"))
        print("  %-20s read %3d/%3d (%3.0f%%)   any artifact %3d (%3.0f%%)"
              % (prog, read, len(cells), 100 * read / max(1, len(cells)),
                 have, 100 * have / max(1, len(cells))))
    print("\nby evidence tier:")
    for tier in EVIDENCE:
        cells = [r for r in rows if r["evidence_tier"] == tier and r["status"] != "out_of_scope"]
        have = sum(1 for r in cells if r["status"].startswith("acquired"))
        print("  %-10s any artifact %3d/%3d (%3.0f%%)" % (tier, have, len(cells),
                                                          100 * have / max(1, len(cells))))
    print("\nThe stopping condition: every in-scope cell reaches acquired_read, blocked,")
    print("or not_located with a stated search depth. A spent budget is not closure.")


def cmd_next(a):
    """The work queue, worst-covered programme first, so effort goes where the
    ledger is emptiest rather than where it is easiest."""
    rows = load() or build()
    open_cells = [r for r in rows if r["status"] in ("unexamined", "located_unfetched", "acquired_unread")]
    by_prog = collections.Counter(r["programme"] for r in open_cells)
    order = [p for p, _ in sorted(by_prog.items(), key=lambda kv: -kv[1])]
    open_cells.sort(key=lambda r: (order.index(r["programme"]), r["county"], r["evidence_tier"]))
    print("%d open cells; showing %d" % (len(open_cells), min(a.limit, len(open_cells))))
    for r in open_cells[:a.limit]:
        print("  %-14s %-20s %-9s %-17s %s" % (r["county"], r["programme"], r["evidence_tier"],
                                               r["status"], r["note"][:44]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.set_defaults(fn=cmd_build)
    r = sub.add_parser("report"); r.set_defaults(fn=cmd_report)
    n = sub.add_parser("next"); n.add_argument("--limit", type=int, default=25); n.set_defaults(fn=cmd_next)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
