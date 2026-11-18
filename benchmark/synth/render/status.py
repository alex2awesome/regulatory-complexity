#!/usr/bin/env python3
"""Render status for another process to poll, recomputed from disk every time.

Why this is not just a flag file. A status label that nobody can check against
reality is what produced the false claim that retrieval was complete: a queue
said `done` because a budget was spent, and the label was read as coverage. So
the contract here is deliberately different.

    `state` is a CLAIM. Everything under `observed` is COUNTED FROM DISK.

A poller that trusts `state` alone is doing the thing that went wrong before.
`state` can be stale in the one way that matters — a session that dies mid-render
leaves `in_progress` behind forever — so every reader gets the counts needed to
decide for itself, plus `stale_risk`, which says exactly that.

States:

    in_progress   a render is running, or was when the writer last spoke
    finished      every selected spec has an artifact AND a verify verdict
    partial       the writer stopped on purpose short of complete
    failed        the writer stopped because something broke

Usage:

    python3 benchmark/synth/render/status.py --world W2_DEV_001            # read
    python3 benchmark/synth/render/status.py --world W2_DEV_001 --set in_progress \\
        --note "146 batches launched"
    python3 benchmark/synth/render/status.py --world W2_DEV_001 --json     # for a script
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
STATES = ("in_progress", "finished", "partial", "failed")
STATUS_NAME = "RENDER_STATUS.json"


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


# LIVENESS is harder than it looks, and three tests failed before this one.
#
#   mtime alone            false POSITIVE for ten minutes after a wave exits,
#                          because its final verdict appends leave the log warm.
#   growth vs a guard's    false POSITIVE: that watermark is written when repair/
#   watermark              verify_batches last ran, so accumulated growth from a
#                          wave that has since finished still looks like growth.
#   a running process      false NEGATIVE during a live wave: agents only run
#                          prepare_batch briefly and spend most of their time in
#                          an LLM call, with nothing local up.
#
# What works is an INTERVAL test against this module's own sidecar, refreshed on
# every read. Between two consecutive status reads (the cron runs ~every 19 min)
# growth means something is writing; no growth plus a warm log means the warmth
# was a finished wave's tail.
STATUS_WATERMARK = ".status_watermark.json"


def _sample(wd: pathlib.Path) -> tuple[int, bool]:
    """(current artifact+verdict count, did it grow since the last status read)."""
    vlog = wd / "verify_log.jsonl"
    lines = sum(1 for ln in vlog.read_text().splitlines() if ln.strip()) if vlog.exists() else 0
    arts = len(list((wd / "artifacts").glob("*.md"))) if (wd / "artifacts").exists() else 0
    now = lines + arts
    side = wd / STATUS_WATERMARK
    prev = None
    if side.exists():
        try:
            prev = int(json.loads(side.read_text()).get("count"))
        except (json.JSONDecodeError, TypeError, ValueError):
            prev = None
    side.write_text(json.dumps({"count": now, "at": _now()}))
    # No baseline yet: assume live, which is the safe direction -- it makes the
    # caller wait rather than launch a second wave on top of a live one.
    return now, True if prev is None else now > prev


def observe(wd: pathlib.Path) -> dict:
    """Count what is actually on disk. No claims, only files."""
    sel_file = wd / "render_selection.txt"
    selected = set()
    if sel_file.exists():
        selected = {ln.strip() for ln in sel_file.read_text().splitlines() if ln.strip()}

    # A killed agent could in principle leave a half-written artifact, which
    # would look rendered to `batches.py` and never be fixed. So "rendered"
    # means COMPLETE: closing front matter and a body. None have been found so
    # far, but the render has already been interrupted three times and the check
    # costs nothing; a silently truncated document is exactly the kind of defect
    # that only surfaces when an extractor scores badly for no visible reason.
    rendered, suspicious = set(), []
    if (wd / "artifacts").exists():
        for f in (wd / "artifacts").glob("*.md"):
            body = f.read_text()
            if body.startswith("---") and body.count("\n---") >= 1 and len(body.split()) >= 60:
                rendered.add(f.stem)
            else:
                suspicious.append(f.stem)

    verified: dict[str, bool] = {}
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
            aid = rec.get("artifact_id")
            if aid:
                verified[aid] = bool(rec.get("pass"))
    # A verdict on an artifact that does not exist is meaningless, and keeping it
    # is actively harmful: `verify_batches.py` only queues rendered artifacts
    # that LACK a verdict, so a stale "not rendered" failure would keep its
    # artifact out of every future verify wave and block its lane forever. 109 of
    # these appeared when a live render agent reached its verify stage holding a
    # batch id whose file had been rewritten underneath it, so the verifier was
    # asked about files nobody had written yet. Ignored on the read side, which
    # needs no lock; `verify_batches.py` purges them from the log under its own
    # warm-log guard.
    stale_verdicts = sorted(set(verified) - rendered)
    for aid in stale_verdicts:
        verified.pop(aid, None)

    batches = {p.stem for p in (wd / "batches").glob("*.json")
               if not p.name.endswith(".input.json")
               and not p.name.endswith(".verify_input.json")
               and p.stem != "index"}
    rendered_batches = set()
    rlog = wd / "render_log.jsonl"
    words = 0
    if rlog.exists():
        for line in rlog.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("batch"):
                rendered_batches.add(rec["batch"])
            words += int(rec.get("words") or 0)

    # LIVENESS, from file mtimes. The batch count below is a bad liveness
    # signal and was briefly mistaken for one: renderers append to
    # render_log.jsonl only at BATCH END, so it can read "24 of 143" while a
    # hundred fresh artifacts already sit on disk. A poller needs to know
    # whether anything is happening right now, which is a question about the
    # newest file, not about bookkeeping.
    newest = 0.0
    newest_what = None
    for label, path in (("artifact", wd / "artifacts"), ("verify_log", wd / "verify_log.jsonl"),
                        ("render_log", wd / "render_log.jsonl")):
        if not path.exists():
            continue
        if path.is_dir():
            files = list(path.glob("*.md"))
            mt = max((f.stat().st_mtime for f in files), default=0.0)
        else:
            mt = path.stat().st_mtime
        if mt > newest:
            newest, newest_what = mt, label
    idle_min = round((datetime.datetime.now().timestamp() - newest) / 60) if newest else None

    count, grew = _sample(wd)
    warm = idle_min is not None and idle_min <= 10

    missing = sorted(selected - rendered) if selected else []
    unverified = sorted(rendered - set(verified))
    failed = sorted(a for a, ok in verified.items() if not ok)
    selected_rendered = selected & rendered
    selected_verified = selected_rendered & set(verified)
    selected_unverified = sorted(selected_rendered - set(verified))
    selected_failed = sorted(a for a in selected_verified if not verified[a])
    return {
        "selected_specs": len(selected),
        "artifacts_rendered": len(rendered),
        "artifacts_missing": len(missing),
        "artifacts_verified": len(verified),
        "artifacts_unverified": len(unverified),
        "artifacts_failed_verification": len(failed),
        "words_rendered": words,
        "batches_total": len(batches),
        "batches_with_render_log": len(rendered_batches),
        "batches_outstanding": sorted(batches - rendered_batches)[:40],
        "sample_missing": missing[:20],
        "sample_failed": failed[:20],
        # The gate is about the immutable selected IDs, not every unrelated
        # artifact left on disk by earlier lanes. Keep the global backlog above
        # visible, and expose it separately rather than letting it block a lane.
        # A verdict may fail or be stale: count completion is NOT certification.
        "selected_counts": {
            "rendered": len(selected_rendered),
            "missing": len(missing),
            "verified": len(selected_verified),
            "unverified": len(selected_unverified),
            "failed_verification": len(selected_failed),
            "sample_unverified": selected_unverified[:20],
            "sample_failed": selected_failed[:20],
        },
        "complete_by_counts": bool(selected) and not missing and not selected_unverified,
        "all_rendered_have_verdicts": bool(rendered) and not unverified,
        # Use these two for liveness, NOT batches_with_render_log.
        "stale_verdicts_ignored": len(stale_verdicts),
        "artifacts_suspicious": len(suspicious),
        "sample_suspicious": sorted(suspicious)[:20],
        "idle_minutes": idle_min,
        "last_write_was": newest_what,
        # Mtime alone gives false positives: the final verdict appends of a wave
        # that has ALREADY exited leave the log warm for ten minutes, and this
        # reported "alive" for two cycles after every workflow had completed and
        # no process remained. So a warm log only counts as alive if a writer is
        # actually still running or the log is still growing -- the same test the
        # repair/verify guards use, kept in one place so the two cannot disagree.
        "looks_alive": bool(warm and grew),
        "warm_but_idle": bool(warm and not grew),
        "work_units_seen": count,
    }


def _scope(wd: pathlib.Path) -> dict:
    """What the current render_selection.txt actually covers.

    The selection is no longer always the whole corpus: it is now written one
    statute at a time, in the order set by
    docs/2026-09-17-single-statute-minimum-scope.md, so that statutes finish
    instead of everything finishing at once. That makes
    `complete_by_counts` mean "THIS LANE is complete", and a poller that reads
    it as "the corpus is complete" would stop twelve statutes early. So the
    scope is reported alongside it, and `corpus_complete` is the flag that
    means what the old one used to.
    """
    f = wd / "render_selection_scope.json"
    if not f.exists():
        return {"mode": "whole_selection", "statute": None}
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return {"mode": "unreadable", "statute": None}


def read(wd: pathlib.Path) -> dict:
    path = wd / STATUS_NAME
    claim = json.loads(path.read_text()) if path.exists() else {
        "state": "unknown", "note": "no status file has been written yet"}
    obs = observe(wd)
    age_min = None
    if claim.get("updated"):
        try:
            age_min = round(
                (datetime.datetime.now()
                 - datetime.datetime.fromisoformat(claim["updated"])).total_seconds() / 60)
        except ValueError:
            pass
    out = dict(claim)
    sc = _scope(wd)
    obs["scope_mode"] = sc.get("mode")
    obs["scope_statute"] = sc.get("statute")
    obs["scope_rank"] = sc.get("rank_in_scope_doc")
    # `complete_by_counts` is scoped to the current selection. Only say the
    # CORPUS is done when the selection is not a single-statute lane.
    obs["lane_complete"] = obs["complete_by_counts"]
    obs["corpus_complete"] = bool(obs["complete_by_counts"]
                                  and sc.get("mode") != "single_statute_completion")
    out["observed"] = obs
    out["claim_age_minutes"] = age_min
    # The one honest warning a poller needs.
    # A stale CLAIM is only a problem when the work has also stopped. Judge that
    # from the newest file on disk, not from how long ago someone last spoke:
    # a long render legitimately goes hours without anyone updating the note.
    out["stale_risk"] = (
        "state is 'in_progress' but nothing has been written for %s minutes; the writing "
        "session has probably died. Trust the observed counts, not the state."
        % obs["idle_minutes"]
        if claim.get("state") == "in_progress" and (obs["idle_minutes"] or 0) > 30
        else None)
    out["agrees_with_disk"] = (
        (claim.get("state") == "finished") == obs["complete_by_counts"]
        if claim.get("state") in STATES else None)
    return out


def write(wd: pathlib.Path, state: str, note: str, by: str) -> dict:
    if state not in STATES:
        raise SystemExit("state must be one of %s" % (STATES,))
    path = wd / STATUS_NAME
    prev = json.loads(path.read_text()) if path.exists() else {}
    history = prev.get("history", [])
    if prev.get("state"):
        history.append({"state": prev["state"], "note": prev.get("note", ""),
                        "at": prev.get("updated")})
    obs = observe(wd)
    rec = {
        "world": wd.name,
        "state": state,
        "note": note,
        "by": by,
        "updated": _now(),
        "started": prev.get("started") or _now(),
        "observed_at_write": obs,
        "history": history[-20:],
        "POLL_THESE": {
            "this lane done?": "observed.lane_complete",
            "WHOLE corpus done?": "observed.corpus_complete -- false while a "
                                  "single-statute lane is selected, however complete "
                                  "that lane is",
            "which lane": "observed.scope_statute / scope_rank",
            "alive?": "observed.looks_alive / observed.idle_minutes",
            "progress": "observed.artifacts_rendered and observed.artifacts_verified",
            "do_NOT_use_for_liveness": "observed.batches_with_render_log -- renderers "
                                       "append only at batch end, so it lags by a whole "
                                       "batch and reads like a stall when work is fine",
        },
        "HOW_TO_READ": (
            "`state` is a claim by the writer. Everything under `observed` is counted "
            "from disk by benchmark/synth/render/status.py and is the thing to trust. "
            "Poll with `status.py --world %s --json`: `observed.complete_by_counts` is "
            "true only when every selected spec has both an artifact and a verify "
            "verdict. A `state` of in_progress with a large `claim_age_minutes` means "
            "the writing session probably died -- but check observed.idle_minutes first, because a long render legitimately runs for hours between notes."
            % wd.name),
    }
    path.write_text(json.dumps(rec, indent=1))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--set", dest="state", choices=STATES)
    ap.add_argument("--note", default="")
    ap.add_argument("--by", default="fable")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    if not wd.exists():
        raise SystemExit("no world at %s" % wd)

    if a.state:
        write(wd, a.state, a.note, a.by)
    rec = read(wd)
    if a.json:
        print(json.dumps(rec, indent=1))
        return 0
    o = rec["observed"]
    print("%s render status: %s" % (rec.get("world", a.world), rec.get("state")))
    if rec.get("note"):
        print("  note: %s" % rec["note"])
    print("  claimed %s ago by %s" % (
        ("%d min" % rec["claim_age_minutes"]) if rec.get("claim_age_minutes") is not None else "?",
        rec.get("by", "?")))
    print("\ncounted from disk:")
    print("  selected specs          %s" % format(o["selected_specs"], ","))
    print("  artifacts rendered      %s" % format(o["artifacts_rendered"], ","))
    print("  still missing           %s" % format(o["artifacts_missing"], ","))
    print("  verified                %s  (failed %s)"
          % (format(o["artifacts_verified"], ","), format(o["artifacts_failed_verification"], ",")))
    print("  rendered but unverified %s" % format(o["artifacts_unverified"], ","))
    print("  words written           %s" % format(o["words_rendered"], ","))
    if o.get("stale_verdicts_ignored"):
        print("  stale verdicts ignored  %s  (verdicts on files that do not exist)"
              % format(o["stale_verdicts_ignored"], ","))
    if o["artifacts_suspicious"]:
        print("  TRUNCATED/INCOMPLETE    %s  <- treated as unrendered, will be re-batched"
              % format(o["artifacts_suspicious"], ","))
    print("  batches                 %d of %d have a render-log entry"
          % (o["batches_with_render_log"], o["batches_total"]))
    print("                          (lags: renderers log only at batch end -- not a liveness signal)")
    if o.get("warm_but_idle"):
        print("\n  log is warm but NO writer is running and it is not growing:")
        print("  those were a finished wave's last appends, so the world is IDLE.")
    print("\n  last write %s ago (%s) -> LOOKS ALIVE: %s"
          % (("%d min" % o["idle_minutes"]) if o["idle_minutes"] is not None else "never",
             o["last_write_was"] or "-", o["looks_alive"]))
    if o.get("scope_mode") == "single_statute_completion":
        print("\n  SCOPE: statute %s only (rank %s of 12 in the scope document)"
              % (o.get("scope_statute"), o.get("scope_rank")))
        print("  LANE COMPLETE: %s     CORPUS COMPLETE: %s  <- corpus needs all 12 lanes"
              % (o["lane_complete"], o["corpus_complete"]))
    else:
        print("\n  COMPLETE BY COUNTS: %s" % o["complete_by_counts"])
    if rec.get("agrees_with_disk") is False:
        print("  WARNING: the claimed state disagrees with the counts above.")
    if rec.get("stale_risk"):
        print("  WARNING: %s" % rec["stale_risk"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
