#!/usr/bin/env python3
"""Apply the mechanical repairs verifiers asked for, and re-verify independently.

Why not just re-render. The render README's recovery path is to delete a failed
artifact and re-render it, which is right when the prose is wrong. But most
failures in the first verified wave were not prose failures:

    18  one renderer used "Permit Center" throughout county C27, whose licensed
        unit is "Development Services Counter" -- another jurisdiction's name,
        correctly caught as a fabricated cross-jurisdiction fact
    10  a markdown link pointed somewhere other than the spec's `links_to` url,
        with the verifier explicitly noting "the body text is verified, do not
        re-render it"
     5  genuine prose problems: a swapped agency/applicant clock attribution, an
        invented tolling clause, an unlicensed cross-programme routing fact

For the first 28, an LLM re-render is the wrong instrument: it costs a full
generation, it can introduce new errors in text that was already verified, and
it discards a verifier's exact instruction in favour of hoping the next attempt
guesses right. A substitution is cheaper, deterministic and reviewable.

Three rules this tool follows, because a repair tool is the obvious place to
accidentally manufacture a pass:

1.  **Every original is preserved** under `artifacts/_rejected/<id>.<n>.md`. The
    plan requires it: "preserve every attempt and rejection. Do not silently
    remove difficult artifacts or loosen the spec to pass them."
2.  **A repair never edits the verify log.** It clears the failing verdict so the
    artifact is unverified again, and an independent verifier has to pass it on
    its own merits. This tool cannot mark anything as passing.
3.  **Only substitutions derivable from the spec and the render context** are
    applied. Anything needing judgement is left for re-rendering and reported.

    python3 benchmark/synth/render/repair.py --world W2_DEV_001 --dry-run
    python3 benchmark/synth/render/repair.py --world W2_DEV_001 --apply
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]

# Unit names that belong to a specific jurisdiction style. A renderer that
# reaches for one of these in the wrong county has fabricated a cross-
# jurisdiction fact, which is the single most common mechanical failure.
KNOWN_UNIT_NAMES = (
    "Permit Center", "Permit Services Center", "Development Services Counter",
    "Development Review Section", "Resource Management Agency, Permit Desk",
    "Community Development front counter",
)


# Distinguishing a LIVE WAVE from a SIBLING TOOL'S WRITE.
#
# Both guards keyed on the verify log's mtime, which cannot tell "verifier agents
# are appending verdicts" from "verify_batches.py just rewrote the file to purge
# stale verdicts". That false positive blocked a repair pass whose whole purpose
# was to run while the corpus was idle, and it cost a cycle.
#
# Agents only ever APPEND, so a live wave makes the log grow. A tool rewrite
# holds or shrinks the line count. So the guard watches the count, recorded in a
# sidecar next to the log.
def wave_is_live(wd, quiet_seconds=600, sample_seconds=20):
    """(bool, reason). True only if the verify log grows during a live sample.

    Three earlier versions of this got it wrong and each cost a cycle:

      mtime alone          false POSITIVE for ten minutes after a wave exits, since
                           its last verdict appends leave the log warm.
      growth vs a stored   false POSITIVE: the watermark is only refreshed when a
      watermark            guard runs, which is rare, so it accumulates growth from
                           waves that finished hours ago. This reported "grew from
                           2361 to 3155 lines" about two completed waves.
      a running process    false NEGATIVE during a live wave: agents run
                           prepare_batch briefly and then sit in an LLM call.

    So the test samples the log twice, `sample_seconds` apart, and asks whether it
    is growing NOW. Only reached when the log is warm at all, so an idle world
    pays nothing.
    """
    import datetime
    import time
    vlog = wd / "verify_log.jsonl"
    if not vlog.exists():
        return False, "no verify log"
    age = datetime.datetime.now().timestamp() - vlog.stat().st_mtime
    if age >= quiet_seconds:
        return False, "log untouched for %d s" % age

    def count():
        return sum(1 for ln in vlog.read_text().splitlines() if ln.strip())

    first = count()
    time.sleep(sample_seconds)
    second = count()
    if second > first:
        return True, ("log grew from %d to %d lines during a %d s sample, so verifier "
                      "agents are appending now" % (first, second, sample_seconds))
    return False, ("log is warm (%d s) but did not grow during a %d s sample, so the "
                   "warmth was a finished wave's last appends" % (age, sample_seconds))

def _load_fails(wd: pathlib.Path) -> list[dict]:
    out, seen = [], {}
    vlog = wd / "verify_log.jsonl"
    if not vlog.exists():
        return []
    for line in vlog.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("artifact_id"):
            seen[rec["artifact_id"]] = rec       # last verdict wins
    return [r for r in seen.values() if not r.get("pass")]


def _licensed_unit(wd: pathlib.Path, jur: str) -> str | None:
    f = wd / "render_context" / ("%s.json" % jur)
    if not f.exists():
        return None
    ctx = json.loads(f.read_text())
    depts = ctx.get("departments") or {}
    return depts.get("lead_permits")


def plan_repairs(wd: pathlib.Path) -> tuple[list[dict], list[dict]]:
    """(mechanical, needs_rerender). Nothing is written."""
    mechanical, manual = [], []
    for rec in sorted(_load_fails(wd), key=lambda r: r["artifact_id"]):
        aid = rec["artifact_id"]
        art = wd / "artifacts" / ("%s.md" % aid)
        spec_f = wd / "specs" / ("%s.json" % aid)
        if not art.exists() or not spec_f.exists():
            manual.append(dict(rec, why="artifact or spec missing"))
            continue
        spec = json.loads(spec_f.read_text())
        text = art.read_text()
        edits: list[tuple[str, str, str]] = []      # (kind, find, replace)

        # 1. wrong unit name -> the county's licensed lead_permits name
        jur = spec.get("jur")
        licensed = _licensed_unit(wd, jur) if jur else None
        if licensed:
            for wrong in KNOWN_UNIT_NAMES:
                if wrong != licensed and wrong in text:
                    edits.append(("unit_name", wrong, licensed))

        # 2. link target -> the url of the spec's own links_to targets
        for target in spec.get("links_to") or []:
            tf = wd / "specs" / ("%s.json" % target)
            if not tf.exists():
                continue
            url = (json.loads(tf.read_text()) or {}).get("url")
            if not url or url in text:
                continue
            # Replace only markdown link targets, never prose.
            for m in re.finditer(r"\]\((https?://[^)\s]+)\)", text):
                bad = m.group(1)
                if bad != url and bad.rstrip("/") != url.rstrip("/"):
                    edits.append(("link_target", "](%s)" % bad, "](%s)" % url))
                    break

        if edits:
            mechanical.append(dict(rec, edits=edits))
        else:
            manual.append(dict(rec, why="needs judgement: no derivable substitution"))
    return mechanical, manual


def apply_repairs(wd: pathlib.Path, mechanical: list[dict]) -> int:
    rejected = wd / "artifacts" / "_rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    repaired: set[str] = set()
    for item in mechanical:
        aid = item["artifact_id"]
        art = wd / "artifacts" / ("%s.md" % aid)
        text = art.read_text()
        # preserve the rejected attempt before touching anything
        n = len(list(rejected.glob("%s.*.md" % aid))) + 1
        (rejected / ("%s.%d.md" % (aid, n))).write_text(text)
        seen: set[tuple] = set()
        for _kind, find, repl in item["edits"]:
            if (find, repl) in seen:
                continue
            seen.add((find, repl))
            text = text.replace(find, repl)
        art.write_text(text)
        repaired.add(aid)

    # Drop the failing verdicts so the artifacts are UNVERIFIED again. This tool
    # must never be able to turn a failure into a pass; only a verifier can.
    vlog = wd / "verify_log.jsonl"
    kept = []
    for line in vlog.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("artifact_id") in repaired and not rec.get("pass"):
            continue                       # verdict withdrawn, awaiting re-verification
        kept.append(line)
    vlog.write_text("\n".join(kept) + ("\n" if kept else ""))
    return len(repaired)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="apply even if a verify wave looks live")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    mech, manual = plan_repairs(wd)

    kinds = collections.Counter(k for m in mech for k, _f, _r in m["edits"])
    print("%d failing artifacts: %d mechanically repairable, %d need re-rendering"
          % (len(mech) + len(manual), len(mech), len(manual)))
    print("edit kinds: %s" % dict(kinds.most_common()))
    print("\nmechanical:")
    for m in mech[:40]:
        print("  %-46s %s" % (m["artifact_id"],
                              ", ".join("%s: %r -> %r" % (k, f[:34], r[:34])
                                        for k, f, r in m["edits"][:2])))
    print("\nneeds re-rendering (judgement required):")
    for m in manual:
        print("  %-46s %s" % (m["artifact_id"], str(m.get("fix") or m.get("why"))[:96]))

    if a.apply and not a.dry_run:
        # RACE GUARD. apply_repairs rewrites verify_log.jsonl to withdraw the
        # failing verdicts. A live verify wave is APPENDING to that same file,
        # so a rewrite while it runs can drop verdicts that landed between the
        # read and the write. Same hazard as rebuilding V batches mid-wave, and
        # the same rule: refuse while the log is warm, unless forced.
        if not a.force:
            live, why = wave_is_live(wd)
            if live:
                print("\na verify wave looks live: %s" % why)
                print("Rewriting the log now could drop its verdicts. Wait for it to go "
                      "quiet, or pass --force if you are sure it is dead.")
                return 1
        n = apply_repairs(wd, mech)
        print("\nrepaired %d artifacts; originals kept in artifacts/_rejected/" % n)
        print("their failing verdicts were WITHDRAWN, not passed: re-run")
        print("  python3 benchmark/synth/render/verify_batches.py --world %s" % a.world)
        print("and the verify-only workflow, so an independent verifier decides.")
    else:
        print("\ndry run: nothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
