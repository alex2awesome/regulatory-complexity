#!/usr/bin/env python3
"""Batch the artifacts that are rendered but not yet verified.

Why this is separate from `batches.py`. That script batches specs that still
need RENDERING, and it deletes and rebuilds every batch file when it runs. So an
interrupted wave leaves a real gap: artifacts written before the interruption
exist on disk, their batch files are gone, and nothing can verify them. That is
exactly what a credit exhaustion produced here — 652 rendered artifacts with no
verify verdict and no batch to verify them against.

The fix is a tool that derives its work from disk state rather than from a
previous run's bookkeeping, so it is idempotent: run it any number of times, and
it always produces batches covering precisely the artifacts that lack a verdict.
`batches.py` may wipe these files on its next run; re-running this restores
them.

Batch ids are prefixed `V` so they never collide with the render groups T/D/F.

CONCURRENT LANES. `V` is a single shared slot, and two agents driving different
statutes through it will delete each other's batch files. `--prefix` gives a lane
its own namespace (`--prefix AV` writes `AV00.json`, ...), and `--selection`
restricts the work to one lane's completion bundle instead of every artifact in
the world, so one agent's rebuild cannot reach another's artifacts.

A prefix also settles the liveness guard honestly rather than by force. The guard
exists because rewriting a batch file changes what a RUNNING agent is asked to
check. An agent can only be reading files that exist, so writing batch ids that
do not exist yet cannot disturb anybody: when `--prefix` names a namespace with
no batch files on disk, the rebuild is safe by construction and the guard does
not apply. It still applies in full to a prefix whose files are already there.
That is the reason not to reach for `--force`: the guard is right, and the case
is genuinely different.

    python3 benchmark/synth/render/verify_batches.py --world W2_DEV_001
    python3 benchmark/synth/render/verify_batches.py --world W2_DEV_001 \
        --prefix AV --selection render_selection_S05.txt
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]


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

def _verdict_ids(wd: pathlib.Path) -> set[str]:
    out = set()
    vlog = wd / "verify_log.jsonl"
    if not vlog.exists():
        return out
    for line in vlog.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("artifact_id"):
            out.add(rec["artifact_id"])
    return out


def unverified(wd: pathlib.Path, only: set[str] | None = None,
               also: set[str] | None = None) -> list[str]:
    """Rendered artifacts with no verdict, optionally restricted to one lane.

    `also` force-includes ids that DO have a verdict. That is for a verdict whose
    freshness cannot be established -- no recorded hash, no time of day, and an
    artifact that has since been edited -- where the honest state is unverified
    even though a line exists. See `stale_verdicts.py`.
    """
    rendered = {p.stem for p in (wd / "artifacts").glob("*.md")}
    verdicts = set()
    vlog = wd / "verify_log.jsonl"
    if vlog.exists():
        for line in vlog.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue          # a half-written line from a concurrent append
            if rec.get("artifact_id"):
                verdicts.add(rec["artifact_id"])
    out = (rendered - verdicts) | ((also or set()) & rendered)
    if only is not None:
        out &= only
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--force", action="store_true",
                    help="rebuild even if a verify wave looks live")
    ap.add_argument("--per-batch", type=int, default=30,
                    help="artifacts per verify batch; verification reads the full spec "
                         "plus the rendered text, so batches are smaller than render ones")
    ap.add_argument("--prefix", default="",
                    help="namespace for this lane's verify batches, e.g. AV -> AV00.json. "
                         "Without it the shared V slot is rebuilt, which another agent may "
                         "be driving.")
    ap.add_argument("--selection", help="restrict to the ids in this file (one lane's bundle)")
    ap.add_argument("--also", default="",
                    help="comma-separated ids to include even though they carry a verdict, "
                         "for verdicts whose freshness cannot be established")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    if not wd.exists():
        raise SystemExit("no world at %s" % wd)

    group = (a.prefix or "") + "V"
    only = None
    if a.selection:
        only = {ln.strip() for ln in (wd / a.selection).read_text().splitlines() if ln.strip()}
    also = {i.strip() for i in a.also.split(",") if i.strip()}
    ids = unverified(wd, only, also)
    out = wd / "batches"
    out.mkdir(exist_ok=True)

    # DO NOT rebuild while a verify wave is live. Each verifier agent runs
    # `prepare_batch --verify` at its own start time, so rewriting V*.json
    # underneath a running wave changes what its agents are asked to check:
    # some artifacts get two verdicts and others none. Nothing is lost, because
    # this tool is idempotent and a later pass picks up whatever was missed, but
    # it wastes a wave. Learned by doing it, once.
    vlog = wd / "verify_log.jsonl"
    existing = sorted(out.glob("%s*.json" % group))
    if not a.force and existing:
        live, why = wave_is_live(wd)
        if live:
            print("a verify wave looks live: %s" % why)
            print("Rebuilding %s* now would change what its agents check. Wait for it to "
                  "finish." % group)
            print("Do NOT reach for --force: use --prefix with an unused namespace instead, "
                  "which is safe by construction.")
            return 1
    elif not existing and group != "V":
        print("namespace %s* has no batch files yet, so no running agent can be reading them: "
              "building it cannot disturb a live wave." % group)

    # Purge verdicts for artifacts that do not exist. See status.py: such a
    # verdict silently excludes its artifact from every future verify wave.
    # Safe here because the warm-log guard above has already established that no
    # verify wave is appending.
    stale = sorted(set(_verdict_ids(wd)) - {p.stem for p in (wd / "artifacts").glob("*.md")})
    if stale and (a.prefix or a.selection):
        # A lane build must not rewrite the shared log. The purge is a whole-world
        # repair and it rewrites verify_log.jsonl, which a concurrent wave is
        # appending to; a fresh prefixed namespace skipped the liveness check
        # precisely because it was not going to touch anything shared.
        print("%d verdicts name artifacts that do not exist; NOT purging them from a lane "
              "build (run without --prefix/--selection on an idle world to repair)" % len(stale))
        stale = []
    if stale:
        keep_lines = []
        for line in vlog.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("artifact_id") in set(stale):
                continue
            keep_lines.append(line)
        vlog.write_text("\n".join(keep_lines) + ("\n" if keep_lines else ""))
        print("purged %d verdicts on artifacts that do not exist" % len(stale))

    for old_file in out.glob("%s*.json" % group):
        old_file.unlink()                  # idempotent: rebuild from scratch
    if not ids:
        print("nothing to verify: every rendered artifact already has a verdict")
        return 0

    made = []
    for i in range(0, len(ids), a.per_batch):
        chunk = ids[i:i + a.per_batch]
        specs = []
        for aid in chunk:
            f = wd / "specs" / ("%s.json" % aid)
            if f.exists():
                specs.append(json.loads(f.read_text()))
        bid = "%s%02d" % (group, i // a.per_batch)
        rec = {
            "batch_id": bid,
            "group": group,
            "spec_ids": chunk,
            "words": sum(int(((s.get("style") or {}).get("length_words") or [300, 400])[1])
                         for s in specs),
            "kinds": dict(collections.Counter(s["kind"] for s in specs)),
            "jurs": sorted({s.get("jur") or "" for s in specs}),
        }
        (out / ("%s.json" % bid)).write_text(json.dumps(rec, indent=1))
        made.append(bid)

    print("%d artifacts need a verdict%s" % (len(ids),
          " in this lane" if a.selection else ""))
    print("%d verify batches: %s" % (len(made), " ".join(made)))
    print(json.dumps(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
