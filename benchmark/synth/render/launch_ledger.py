#!/usr/bin/env python3
"""A ledger of render launches, so the same batch is never given to two agents.

WHY THIS EXISTS. A render wave was launched on batches T00-T10, appeared to go
idle for 119 minutes, and was relaunched on the same ids. It had not died: its
agents were **sleeping through usage-limit resets**, which produces no file
activity at all. Two waves then rendered batch T00 concurrently and wrote the
same 25 artifact paths against each other between 19:08 and 19:25. One
renderer's report put it plainly: *"they were overwritten one-by-one... I stopped
rewriting instead of starting a write war. Do not assign one batch to two
agents."*

The lesson is narrow and important:

    "no files have changed for N minutes" DOES NOT MEAN "the wave is dead".

A wave blocked on a usage-limit reset is idle and alive, possibly for hours, and
no filesystem signal distinguishes it from a dead one. Every liveness test in
this directory samples the filesystem, so none of them can tell the difference.
What *can* tell the difference is bookkeeping: a launch is outstanding until its
completion has been observed and recorded.

So this ledger is append-only, and `check` refuses a launch whose batch ids
overlap any launch not yet marked done. It is deliberately conservative: an
un-reconciled launch blocks, because the cost of blocking is a delayed cycle
while the cost of colliding is two agents destroying each other's output.

`done` IS THE WEAK POINT, and it has been got wrong once. A fix wave went quiet
for four hours and one minute. The verify log had not been appended to in 14,788
seconds, both waves looked plainly dead, and `done` was recorded for two runs on
that basis. The wave was not dead: it was sleeping through a usage-limit reset,
and when it woke it finished all 22 of its agents, 15,736 seconds after launch,
having lost none of them. Three artifacts were then verified twice, once by the
original wave's verifier and once by the replacement -- harmless here, because
verification only appends, but the same inference on a RENDER wave is the T00
write war exactly.

The mistake is not hard to name: quiet was read as death, which is the one
inference this file's whole first half says cannot be made. So `done` now
requires `--evidence`, a sentence saying how the completion was OBSERVED -- a
task notification, a workflow result, an agent's own report. "The log has been
quiet for N hours" is not evidence and the tool rejects it, because that is the
exact reasoning that fails. If a wave really is unreachable, say so plainly in
the evidence string and own it; what must not happen is the elapsed-silence
argument dressed up as a completion.

    python3 benchmark/synth/render/launch_ledger.py check --world W2_DEV_001 --ids AT00,AT01
    python3 benchmark/synth/render/launch_ledger.py record --world W2_DEV_001 \
        --run wf_xxx --ids AT00,AT01
    python3 benchmark/synth/render/launch_ledger.py done --world W2_DEV_001 --run wf_xxx \
        --evidence "task notification for wkbpwl9ub reported 22/22 agents done"
    python3 benchmark/synth/render/launch_ledger.py list --world W2_DEV_001
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = "launch_ledger.jsonl"


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _read(wd: pathlib.Path) -> list[dict]:
    f = wd / LEDGER
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _append(wd: pathlib.Path, rec: dict) -> None:
    with (wd / LEDGER).open("a") as f:
        f.write(json.dumps(rec) + "\n")


def outstanding(wd: pathlib.Path) -> dict[str, dict]:
    """run_id -> launch record, for launches with no recorded completion."""
    launches: dict[str, dict] = {}
    done: set[str] = set()
    for rec in _read(wd):
        if rec.get("event") == "launch":
            launches[rec["run"]] = rec
        elif rec.get("event") == "done":
            done.add(rec.get("run"))
    return {r: v for r, v in launches.items() if r not in done}


def conflicts(wd: pathlib.Path, ids: list[str]) -> list[tuple[str, list[str]]]:
    want = set(ids)
    out = []
    for run, rec in sorted(outstanding(wd).items()):
        overlap = sorted(want & set(rec.get("ids") or []))
        if overlap:
            out.append((run, overlap))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "record", "done", "list"])
    ap.add_argument("--world", required=True)
    ap.add_argument("--run")
    ap.add_argument("--ids", default="")
    ap.add_argument("--evidence", default="",
                    help="required by `done`: how the completion was OBSERVED. Elapsed "
                         "silence is not an observation and is rejected.")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    ids = [i.strip() for i in a.ids.split(",") if i.strip()]

    if a.cmd == "list":
        out = outstanding(wd)
        if not out:
            print("no outstanding launches: every recorded launch has a recorded completion")
            return 0
        print("OUTSTANDING launches (no completion recorded):")
        for run, rec in sorted(out.items()):
            print("  %-26s %s  %d batches: %s"
                  % (run, rec.get("at"), len(rec.get("ids") or []),
                     ",".join((rec.get("ids") or [])[:8])))
        print("\nA wave sleeping through a usage-limit reset looks IDLE on disk but is")
        print("alive. Do not relaunch these ids until a completion is OBSERVED. This has")
        print("already been got wrong once by reading four hours of silence as death; see")
        print("the header of launch_ledger.py.")
        return 0

    if a.cmd == "check":
        if not ids:
            raise SystemExit("--ids required for check")
        bad = conflicts(wd, ids)
        if not bad:
            print("clear to launch: none of these %d batch ids belong to an outstanding "
                  "launch" % len(ids))
            return 0
        print("REFUSING: these batch ids are already assigned to a launch with no recorded")
        print("completion. Relaunching them risks two agents writing the same artifacts.")
        for run, overlap in bad:
            print("  %s  overlaps on %d: %s" % (run, len(overlap), ",".join(overlap[:10])))
        print("\nIf that run really is finished, record it:")
        print("  launch_ledger.py done --world %s --run <run_id>" % a.world)
        return 1

    if a.cmd == "record":
        if not (a.run and ids):
            raise SystemExit("--run and --ids required for record")
        _append(wd, {"event": "launch", "run": a.run, "ids": ids, "at": _now()})
        print("recorded launch %s over %d batches" % (a.run, len(ids)))
        return 0

    if a.cmd == "done":
        if not a.run:
            raise SystemExit("--run required for done")
        ev = (a.evidence or "").strip()
        if len(ev) < 12:
            print("REFUSING: `done` needs --evidence saying how the completion was OBSERVED.")
            print("A completion is observed, never inferred: a task notification, a workflow")
            print("result, an agent's own report. See this file's header for the four-hour")
            print("silence that was not a death.")
            return 1
        # The precise reasoning that has already failed here, blocked by name.
        low = ev.lower()
        quiet_words = ("quiet", "silent", "silence", "no activity", "idle", "untouched",
                       "stalled", "not appended", "nothing written", "no files", "looks dead",
                       "seems dead", "hours with no", "mtime")
        hit = next((w for w in quiet_words if w in low), None)
        if hit and not any(g in low for g in ("notification", "workflow result", "reported",
                                              "agent said", "unreachable", "confirmed")):
            print("REFUSING: the evidence rests on %r, i.e. on elapsed silence." % hit)
            print("A wave sleeping through a usage-limit reset is silent for hours and then")
            print("finishes everything. That has happened in this world: a run went quiet for")
            print("4h01m and then completed all 22 of its agents. Wait for the notification,")
            print("or state plainly that the run is unreachable and why you are sure.")
            return 1
        _append(wd, {"event": "done", "run": a.run, "at": _now(), "evidence": ev})
        print("recorded completion of %s; its batch ids are free again" % a.run)
        print("evidence: %s" % ev)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
