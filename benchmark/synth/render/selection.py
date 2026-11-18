#!/usr/bin/env python3
"""Freeze partitions and choose what gets rendered, recording what does not.

Two jobs the plan requires before a mass render, both of which must happen
BEFORE any document exists so they cannot be chosen to flatter a result.

**Partitions** (plan §9). Counties are split calibration / development /
reserved, stratified on public design covariates, frozen here. "Do not choose
them after viewing posterior performance."

**Render selection.** This is the decision that needs stating plainly, because
it is a departure the plan's budget section anticipates but does not size. The
corpus PLANTS 17,558 user-forum threads, because that is what the measured
reddit volume implies — a median of 13 distinct posts per county-programme cell
across 452 cells. Those threads are 70.6% of all specs. Rendering all of them
would spend 70% of the budget on the channel that carries a usable duration in
only 32% of its posts, and would leave the declared and designed tiers — where
the calibration labels actually come from — as a rounding error in the spend.

So the user tier is **sampled**, and the sample is recorded per cell. The
critical consequence, which any downstream scorer must respect:

    a cell with planted > rendered is NOT a cell with no evidence.

The planted count is the truth and feeds the information ceiling. The rendered
count is what a text-condition solver can reach. Conflating them would turn a
budget decision into a false finding about rural information poverty — the exact
error the availability calibration exists to avoid. `render_manifest.json`
carries both numbers for every cell so the difference is always recoverable.

NAMED `selection.py`, NOT `select.py`: this directory ends up on sys.path for
every tool in it, and a module called `select` shadows the stdlib `select`, which
breaks any transitive `import subprocess` / `asyncio`. That bit status.py once.

    python3 benchmark/synth/render/selection.py --world W2_DEV_001 \
        --user-per-cell 4 --text-counties 20
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

USER_KINDS = {"reddit_thread", "forum_thread"}
# Reserved counties are released for inference only under the frozen evaluation
# protocol; their truth is read only by the scorer.
SPLITS = ("calibration", "development", "reserved")


def stratify(counties: list[dict], n_text: int) -> dict:
    """Pick the text-rendered counties and split them, stratified by size.

    Stratified on population decile rather than sampled at random, because the
    availability gradient IS the population gradient: a random 20 of 58 could
    easily contain no county from the sparse tail, and the sparse tail is where
    the interesting claim lives.
    """
    ranked = sorted(counties, key=lambda c: -c["pop"])
    if n_text >= len(ranked):
        chosen = ranked
    else:
        # take every k-th county down the size ranking, so all deciles appear
        step = len(ranked) / n_text
        chosen = [ranked[min(len(ranked) - 1, int(i * step))] for i in range(n_text)]
    # 8 / 7 / 5 of 20 in the plan's proportions, applied to whatever n_text is
    n_cal = max(1, round(len(chosen) * 8 / 20))
    n_dev = max(1, round(len(chosen) * 7 / 20))
    out: dict[str, list[str]] = {s: [] for s in SPLITS}
    # deal round-robin down the size ranking so each split spans the range
    quota = {"calibration": n_cal, "development": n_dev,
             "reserved": len(chosen) - n_cal - n_dev}
    order = [s for s in SPLITS for _ in range(max(0, quota[s]))]
    for i, c in enumerate(chosen):
        out[order[i % len(order)] if i < len(order) else SPLITS[i % 3]].append(c["id"])
    spec_only = [c["id"] for c in ranked if c["id"] not in {x for v in out.values() for x in v}]
    return dict(splits=out, spec_only=spec_only,
                text_counties=[c["id"] for c in chosen])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--user-per-cell", type=int, default=4,
                    help="user-forum threads to render per county-programme cell")
    ap.add_argument("--text-counties", type=int, default=20,
                    help="counties that get rendered documents; the rest stay spec-only")
    ap.add_argument("--all", action="store_true",
                    help="render every county and every spec; ignores the two caps above")
    a = ap.parse_args(argv)

    wd = ROOT / "benchmark/synth/worlds" / a.world
    world = json.loads((wd / "world.json").read_text())
    panel = world.get("county_panel") or []
    if not panel:
        raise SystemExit("%s has no county panel" % a.world)

    part = stratify(panel, len(panel) if a.all else a.text_counties)
    text_set = set(part["text_counties"])
    sid2dom = {s["stat_id"]: s["domain"] for s in world["statutes"]}

    planted = collections.Counter()
    selected: list[str] = []
    skipped = collections.Counter()
    per_cell_taken = collections.Counter()
    for f in sorted((wd / "specs").glob("*.json")):
        s = json.loads(f.read_text())
        aid, jur, kind = s["artifact_id"], s.get("jur"), s.get("kind")
        # State-level documents (statutes, bill analyses) are always rendered:
        # every task needs the public law.
        if not jur:
            selected.append(aid)
            continue
        if jur in {c["id"] for c in panel} and jur not in text_set:
            skipped["county not in the text tier"] += 1
            continue
        if kind in USER_KINDS:
            cell = (jur, sid2dom.get(s.get("stat_id"), "?"))
            planted[cell] += 1
            if not a.all and per_cell_taken[cell] >= a.user_per_cell:
                skipped["user tier over the per-cell sample"] += 1
                continue
            per_cell_taken[cell] += 1
        selected.append(aid)

    manifest = {
        "world": a.world,
        "partitions": part["splits"],
        "spec_only_counties": part["spec_only"],
        "render_selection": {
            "user_per_cell": None if a.all else a.user_per_cell,
            "text_counties": len(text_set),
            "selected_specs": len(selected),
            "skipped": dict(skipped),
        },
        "user_cells": [
            {"county": c, "programme": d, "planted": planted[(c, d)],
             "rendered": per_cell_taken[(c, d)]}
            for (c, d) in sorted(planted)
        ],
        "READ_THIS": (
            "planted > rendered means the corpus contains evidence a text-condition "
            "solver cannot reach; it does NOT mean the cell is empty. The planted "
            "count is truth and feeds the information ceiling. Any score computed "
            "over rendered documents must use the rendered count as its denominator "
            "and must not report an unrendered cell as an absence of evidence."),
    }
    (wd / "render_manifest.json").write_text(json.dumps(manifest, indent=1))
    (wd / "render_selection.txt").write_text("\n".join(sorted(selected)) + "\n")

    tp = sum(planted.values())
    tr = sum(per_cell_taken.values())
    print("world %s" % a.world)
    for s in SPLITS:
        print("  %-12s %2d counties" % (s, len(part["splits"][s])))
    print("  %-12s %2d counties (oracle/spec-only, no documents)"
          % ("spec_only", len(part["spec_only"])))
    print("\nrender selection: %s of %s specs"
          % (format(len(selected), ","), format(len(selected) + sum(skipped.values()), ",")))
    for why, n in skipped.most_common():
        print("  skipped %-36s %s" % (why, format(n, ",")))
    print("\nuser tier: %s planted threads, %s rendered (%.1f%%) across %d cells"
          % (format(tp, ","), format(tr, ","), 100 * tr / max(1, tp), len(planted)))
    print("  a cell with planted > rendered still HAS evidence; see render_manifest.json")
    print("\nwrote %s and render_selection.txt" % (wd / "render_manifest.json").name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
