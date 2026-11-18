#!/usr/bin/env python3
"""The statute completion order, and the bundle that completes one statute.

This module exists so the render order is a DECLARED CONSTANT rather than a
heuristic. An earlier pass ordered the queue by "smallest outstanding lane",
which produced S12, S01, S03, S05, S02, S04, ... — close to, but not, the
ranking Alex set in `docs/2026-09-17-single-statute-minimum-scope.md`. A
heuristic that merely approximates the agreed order will drift every time the
outstanding counts change, and nobody will notice. So the order is copied here
verbatim from that document's ranking table and asserted against it.

The second thing this fixes is a real scope error. The render selection was
capped at a 20-county text tier, but the scope document's completion boundary
is explicit: "There is no 20-county limit or four-thread cap" for a full
bundle, and its per-statute county counts are the statute's OWN
implementations. S12 has 15 county implementations and only 8 of them were in
the 20-county tier, so the previous selection could never have completed any
statute no matter how long it ran. A bundle here therefore covers every county
that implements the statute.

Excluded from a bundle, following the document: legacy J/K jurisdictions,
unrelated filler, full recursive web expansion, and separate look-alike
process corpora. Included: the statute's target documents in its implementing
counties, the state-level documents for that statute, and the direct
shared-page dependencies its documents link to.

    python3 benchmark/synth/render/statute_order.py --world W2_DEV_001
    python3 benchmark/synth/render/statute_order.py --world W2_DEV_001 --statute S12 --write
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

SCOPE_DOC = "docs/2026-09-17-single-statute-minimum-scope.md"

# Verbatim from the scope document's "Full, unthinned completion ranking",
# ranks 1-12. Do NOT reorder this by a local cost recomputation: the ranking is
# an agreed plan, and `verify_against_doc()` checks this list still matches the
# table so an edit to either one is caught.
STATUTE_ORDER = ("S12", "S03", "S05", "S04", "S01", "S09",
                 "S02", "S10", "S11", "S06", "S08", "S07")

# The document's county-implementation counts, used as an independent check that
# a bundle covers the statute rather than a subset of it.
DOC_IMPL_COUNTS = {"S12": 15, "S03": 21, "S05": 30, "S04": 28, "S01": 30,
                   "S09": 24, "S02": 35, "S10": 38, "S11": 58, "S06": 58,
                   "S08": 58, "S07": 57}

USER_KINDS = {"reddit_thread", "forum_thread"}


def verify_against_doc() -> list[str]:
    """Re-read the scope document's ranking table and compare it to the constant."""
    path = ROOT / SCOPE_DOC
    if not path.exists():
        return ["scope document missing at %s" % SCOPE_DOC]
    ranked: list[tuple[int, str]] = []
    for line in path.read_text().splitlines():
        if not line.startswith("| ") or "—" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or not cells[0].isdigit():
            continue
        sid = cells[1].split("—")[0].strip()
        if sid.startswith("S"):
            ranked.append((int(cells[0]), sid))
    ranked.sort()
    from_doc = tuple(sid for _r, sid in ranked)
    problems = []
    if not from_doc:
        problems.append("could not parse a ranking table out of %s" % SCOPE_DOC)
    elif from_doc != STATUTE_ORDER:
        problems.append("STATUTE_ORDER disagrees with the document.\n"
                        "  document:  %s\n  constant:  %s" % (" ".join(from_doc),
                                                              " ".join(STATUTE_ORDER)))
    return problems


def _world(wd: pathlib.Path):
    return json.loads((wd / "world.json").read_text())


def implementing_counties(world: dict, sid: str) -> set[str]:
    """Counties that implement this statute. Legacy J/K are excluded per the doc."""
    return {i["jur"] for i in world["implementations"]
            if i.get("target") and i["stat_id"] == sid and str(i["jur"]).startswith("C")}


def bundle(wd: pathlib.Path, sid: str, user_per_cell: int | None) -> dict:
    """Every artifact id needed to call this statute complete."""
    world = _world(wd)
    counties = implementing_counties(world, sid)
    specs = {p.stem: json.loads(p.read_text()) for p in (wd / "specs").glob("*.json")}

    core, user, deps, state = set(), collections.defaultdict(list), set(), set()
    for aid, s in specs.items():
        if s.get("stat_id") != sid:
            continue
        jur = s.get("jur")
        if not jur:
            state.add(aid)                      # statute text, bill analysis
            continue
        if jur not in counties:
            continue                            # J/K or a non-implementer
        if s.get("kind") in USER_KINDS:
            user[jur].append(aid)
        else:
            core.add(aid)
    # The compact design caps threads per county; None means every planted one.
    kept_user = set()
    for jur, ids in user.items():
        ids.sort()
        kept_user |= set(ids if user_per_cell is None else ids[:user_per_cell])
    # Direct shared-page dependencies only: no recursive web expansion.
    for aid in core | kept_user:
        for t in specs[aid].get("links_to") or []:
            if t in specs:
                deps.add(t)
    full = core | kept_user | deps | state
    rendered = {p.stem for p in (wd / "artifacts").glob("*.md")}
    verdict = {}
    vlog = wd / "verify_log.jsonl"
    if vlog.exists():
        for line in vlog.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("artifact_id"):
                verdict[rec["artifact_id"]] = bool(rec.get("pass"))
    return {
        "statute": sid,
        "domain": next((s["domain"] for s in world["statutes"] if s["stat_id"] == sid), "?"),
        "counties": len(counties),
        "doc_counties": DOC_IMPL_COUNTS.get(sid),
        "core": len(core), "user": len(kept_user), "deps": len(deps), "state": len(state),
        "total": len(full),
        "rendered": len(full & rendered),
        "passed": sum(1 for a in full if verdict.get(a) is True),
        "failed": sum(1 for a in full if verdict.get(a) is False),
        "to_render": sorted(full - rendered),
        "ids": sorted(full),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--statute", help="one statute; default reports all in order")
    ap.add_argument("--user-per-cell", type=int, default=4,
                    help="compact cap on planted threads per county; 0 means no cap")
    ap.add_argument("--write", action="store_true",
                    help="write render_selection.txt for --statute, so batches.py "
                         "batches only that statute's completion bundle")
    # Two agents cannot both drive lanes through render_selection.txt: it is a
    # single slot, and batches.py deletes and rebuilds the batch files under it.
    # `--write-to` puts a bundle in its own file so a second agent's lane leaves
    # the shared slot, and whatever is reading it, completely alone.
    ap.add_argument("--write-to", help="write the bundle to this file instead of "
                                       "render_selection.txt (for a concurrent lane)")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    cap = None if a.user_per_cell == 0 else a.user_per_cell

    problems = verify_against_doc()
    for p in problems:
        print("ORDER CHECK FAILED: %s" % p)
    if problems:
        return 2
    print("order check: STATUTE_ORDER matches %s\n" % SCOPE_DOC)

    targets = [a.statute] if a.statute else list(STATUTE_ORDER)
    print("%-4s %-5s %-26s %5s %6s %5s %5s %5s %6s %8s %7s %7s"
          % ("rank", "stat", "domain", "cnty", "doc", "core", "user", "deps", "total",
             "rendered", "passed", "to do"))
    first_unfinished = None
    for sid in targets:
        b = bundle(wd, sid, cap)
        rank = STATUTE_ORDER.index(sid) + 1
        flag = "" if b["counties"] == b["doc_counties"] else "  <- COUNTY COUNT DIFFERS FROM DOC"
        print("%-4d %-5s %-26s %5d %6s %5d %5d %5d %6d %8d %7d %7d%s"
              % (rank, sid, b["domain"], b["counties"], b["doc_counties"], b["core"],
                 b["user"], b["deps"], b["total"], b["rendered"], b["passed"],
                 len(b["to_render"]), flag))
        if first_unfinished is None and b["passed"] < b["total"]:
            first_unfinished = sid

    if a.statute and a.write_to:
        b = bundle(wd, a.statute, cap)
        out = wd / a.write_to
        out.write_text("\n".join(b["ids"]) + "\n")
        print("\nwrote %s for %s: %d ids, %d still to render" % (out.name, a.statute,
                                                                 b["total"], len(b["to_render"])))
        print("render_selection.txt was NOT touched, so a concurrent lane is undisturbed.")
        return 0
    if a.statute and a.write:
        b = bundle(wd, a.statute, cap)
        (wd / "render_selection.txt").write_text("\n".join(b["ids"]) + "\n")
        (wd / "render_selection_scope.json").write_text(json.dumps({
            "mode": "single_statute_completion",
            "statute": a.statute,
            "rank_in_scope_doc": STATUTE_ORDER.index(a.statute) + 1,
            "source": SCOPE_DOC,
            "user_per_cell": cap,
            "counties": b["counties"],
            "totals": {k: b[k] for k in ("core", "user", "deps", "state", "total",
                                         "rendered", "passed", "failed")},
            "NOTE": ("This selection is ONE statute's completion bundle, not the whole "
                     "corpus. It covers every county that implements the statute, which "
                     "the previous 20-county text tier did not: 8 of S12's 15 "
                     "implementations were inside that tier, so no statute could ever "
                     "have finished under it."),
        }, indent=1))
        print("\nwrote render_selection.txt for %s: %d ids, %d still to render"
              % (a.statute, b["total"], len(b["to_render"])))
        print("wrote render_selection_scope.json recording what this selection is")
    elif not a.statute:
        print("\nfirst unfinished statute in the agreed order: %s" % first_unfinished)
        print("write its bundle with:  --statute %s --write" % first_unfinished)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
