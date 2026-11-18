#!/usr/bin/env python3
"""Find verdicts that describe text which no longer exists on disk.

WHY THIS EXISTS. A fix wave ran 22 agents as 11 edit-then-verify chains and was
killed after 17 of them. The five it lost were all verifiers, so three artifacts
ended up EDITED at 12:36-12:37Z carrying failing verdicts written at 12:20-12:31Z.
Read naively, the lane had seven failures; in fact three of the seven had already
been repaired and merely never re-checked. Their `fix` strings named sentences
that had been deleted an hour earlier, so dispatching another edit round against
them would have had an agent hunt for absent text and, at worst, damage prose
that was already correct.

The general shape: **a verdict is a statement about a specific version of an
artifact**, and nothing in the log's own structure says which version. Two
distinct states look identical if you only look at `pass`:

    failing, and the text still has the defect      -> needs an edit
    failing, but the text was fixed afterwards      -> needs a verifier

Two signals can answer it, and their precedence matters. `artifact_sha256`, where
a verifier recorded one, is PROOF: a matching hash means the verdict describes
exactly these bytes, whatever the clocks say. A timestamp compared against the
artifact's mtime is only evidence, and it misreads in both directions -- an
earlier fix pass wrote `verified_at: "2026-09-18"`, a date with no time, which
compares as midnight and made two verdicts look four hours stale when their
hashes matched the file exactly. So: hash first, timestamps only when there is no
hash, and an honest third bucket for records that carry neither. Most of the
older `V*`/`D*` records in this world have no timestamp at all, and calling those
stale would be just as wrong as trusting them.

Exit status is 1 when any stale verdict is found, so a cycle can gate on it.

    python3 benchmark/synth/render/stale_verdicts.py --world W2_DEV_001
    python3 benchmark/synth/render/stale_verdicts.py --world W2_DEV_001 \
        --selection render_selection_S05.txt
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

# An edit and the verdict that follows it are written by different processes, and
# the verifier reads the file before it writes its line. A verdict a few seconds
# "older" than the artifact is therefore normal. Only a clear gap means the
# verdict really predates the edit.
SKEW_SECONDS = 120


def _parse(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts)
    except ValueError:
        return None


def last_verdicts(wd: pathlib.Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
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
            out[rec["artifact_id"]] = rec       # last line wins, as everywhere else
    return out


def audit(wd: pathlib.Path, ids: set[str] | None) -> dict:
    stale, unresolvable, suspect, fine = [], [], [], 0
    for aid, rec in sorted(last_verdicts(wd).items()):
        if ids is not None and aid not in ids:
            continue
        art = wd / "artifacts" / ("%s.md" % aid)
        if not art.exists():
            continue                            # verify_batches.py purges these
        edited = datetime.datetime.fromtimestamp(art.stat().st_mtime)
        passed = bool(rec.get("pass"))

        # 1. A recorded hash settles it outright, in either direction.
        want = rec.get("artifact_sha256")
        if want:
            if hashlib.sha256(art.read_bytes()).hexdigest() == want:
                fine += 1
            else:
                stale.append({"artifact_id": aid, "pass": passed, "by": "hash",
                              "recorded_sha": str(want)[:12],
                              "edited_at": edited.isoformat(timespec="seconds"),
                              "fix": rec.get("fix")})
            continue

        # 2. No hash: fall back to the clock, but only if it carries a time. A
        #    date-only stamp cannot be compared to an mtime within that day.
        raw = rec.get("verified_at")
        written = _parse(raw)
        if written is None or (isinstance(raw, str) and len(raw.strip()) <= 10):
            # One thing is still knowable without either signal: whether the
            # artifact was ever edited at all. Every edit pass preserves the text
            # it replaced under artifacts/_rejected/<id>.N.md, so a preserved copy
            # is evidence of an edit and no preserved copy means the file is the
            # original render. An undatable verdict on a never-edited artifact is
            # almost certainly about the text on disk; the same verdict on an
            # edited artifact is a coin flip, and a PASS there is the quiet
            # failure -- it counts toward a finished lane while nothing has
            # actually checked the current text.
            was_edited = bool(list((wd / "artifacts" / "_rejected").glob("%s.*.md" % aid))) \
                if (wd / "artifacts" / "_rejected").exists() else False
            rec_out = {"artifact_id": aid, "pass": passed, "verified_at": raw,
                       "edited": edited.isoformat(timespec="seconds")}
            (suspect if was_edited else unresolvable).append(rec_out)
            continue
        if written.tzinfo is not None:           # verdict stamps carry a UTC offset
            written = written.astimezone().replace(tzinfo=None)
        gap = (edited - written).total_seconds()
        if gap > SKEW_SECONDS:
            stale.append({"artifact_id": aid, "pass": passed, "by": "timestamp",
                          "verdict_at": written.isoformat(timespec="seconds"),
                          "edited_at": edited.isoformat(timespec="seconds"),
                          "minutes_stale": round(gap / 60.0, 1),
                          "fix": rec.get("fix")})
            continue
        fine += 1
    return {"stale": stale, "suspect": suspect, "unresolvable": unresolvable,
            "current": fine}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--selection", help="restrict to the ids in this file, e.g. one lane's bundle")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    wd = ROOT / "benchmark/synth/worlds" / a.world
    ids = None
    if a.selection:
        f = wd / a.selection
        ids = {ln.strip() for ln in f.read_text().splitlines() if ln.strip()}

    out = audit(wd, ids)
    if a.json:
        print(json.dumps(out, indent=1))
        return 1 if (out["stale"] or out["suspect"]) else 0

    print("%d verdicts provably describe the artifact as it stands" % out["current"])
    if out["stale"]:
        print("\n%d STALE verdicts: the artifact changed after the verdict was written, so the"
              % len(out["stale"]))
        print("verdict describes text that no longer exists. These need a VERIFIER, not an editor:")
        for s in out["stale"]:
            how = ("sha %s no longer matches, file written %s"
                   % (s["recorded_sha"], s["edited_at"][11:])) if s["by"] == "hash" else (
                  "verdict %s, edited %s (%.1f min later)"
                  % (s["verdict_at"][11:], s["edited_at"][11:], s["minutes_stale"]))
            print("  %-34s %-5s %s" % (s["artifact_id"], "PASS" if s["pass"] else "FAIL", how))
        print("\nA failing stale verdict is the dangerous one: dispatching its `fix` again sends an")
        print("agent looking for a sentence that was already removed. A passing stale verdict is")
        print("quieter and still wrong: nothing has checked the text that is actually there.")
    if out["suspect"]:
        print("\n%d SUSPECT verdicts: no hash, no time of day, AND the artifact has a preserved"
              % len(out["suspect"]))
        print("copy in artifacts/_rejected/, so it was edited at some point and nothing here can")
        print("say whether the verdict came before or after that edit. Re-verify these:")
        for s in out["suspect"]:
            print("  %-34s %-5s file written %s" % (s["artifact_id"],
                  "PASS" if s["pass"] else "FAIL", s["edited"][11:]))
    if out["unresolvable"]:
        print("\n%d verdicts carry neither a hash nor a timestamp with a time of day, so their"
              % len(out["unresolvable"]))
        print("freshness cannot be established from the record. None of these has ever been edited,")
        print("though, so the artifact is still its original render and the verdict is about it:")
        for u in out["unresolvable"][:15]:
            print("  %-34s %-5s verified_at=%r" % (u["artifact_id"],
                  "PASS" if u["pass"] else "FAIL", u["verified_at"]))
        if len(out["unresolvable"]) > 15:
            print("  ... and %d more" % (len(out["unresolvable"]) - 15))
    return 1 if (out["stale"] or out["suspect"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
