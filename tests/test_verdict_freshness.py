"""A verdict is a statement about a specific version of an artifact.

Nothing in `verify_log.jsonl` says which version, and two states look identical
if you only read `pass`: failing-and-still-broken needs an editor, while
failing-but-already-fixed needs a verifier. Dispatching the second as the first
sends an agent hunting for a sentence that was deleted an hour earlier.

These tests pin the precedence `stale_verdicts.py` uses, which was itself got
wrong on the first attempt: a recorded hash is PROOF and settles the question in
either direction, a timestamp is only evidence, and a date with no time of day is
neither -- an earlier fix pass wrote `verified_at: "2026-09-18"`, which compares
as midnight and made two verdicts look four hours stale while their hashes
matched the file exactly.

No network, no paid calls: every fixture is a temporary directory.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from benchmark.synth.render.stale_verdicts import audit


def _world(tmp_path: pathlib.Path) -> pathlib.Path:
    wd = tmp_path / "W_TEST"
    (wd / "artifacts").mkdir(parents=True)
    return wd


def _write(wd: pathlib.Path, aid: str, text: str, mtime: datetime.datetime | None = None) -> str:
    f = wd / "artifacts" / ("%s.md" % aid)
    f.write_text(text)
    if mtime is not None:
        ts = mtime.timestamp()
        os.utime(f, (ts, ts))
    return hashlib.sha256(f.read_bytes()).hexdigest()


def _log(wd: pathlib.Path, records: list[dict]) -> None:
    with (wd / "verify_log.jsonl").open("a") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def test_matching_hash_beats_a_stale_looking_timestamp(tmp_path):
    """The false positive that motivated the tool: a date-only stamp plus a good hash."""
    wd = _world(tmp_path)
    sha = _write(wd, "A", "body\n", datetime.datetime(2026, 9, 18, 4, 54, 16))
    _log(wd, [{"artifact_id": "A", "pass": True, "verified_at": "2026-09-18",
               "artifact_sha256": sha}])
    out = audit(wd, None)
    assert out["current"] == 1
    assert out["stale"] == [] and out["suspect"] == [] and out["unresolvable"] == []


def test_mismatched_hash_is_stale_even_with_a_fresh_timestamp(tmp_path):
    """A hash disagreement is proof, whatever the clock says."""
    wd = _world(tmp_path)
    _write(wd, "A", "edited body\n", datetime.datetime(2026, 9, 18, 5, 0, 0))
    _log(wd, [{"artifact_id": "A", "pass": False,
               "verified_at": "2026-09-18T05:00:30",
               "artifact_sha256": hashlib.sha256(b"old body\n").hexdigest()}])
    out = audit(wd, None)
    assert [s["artifact_id"] for s in out["stale"]] == ["A"]
    assert out["stale"][0]["by"] == "hash"


def test_verdict_written_before_the_edit_is_stale(tmp_path):
    """No hash: fall back to the clock. This is the real case from the S05 lane."""
    wd = _world(tmp_path)
    _write(wd, "A", "edited\n", datetime.datetime(2026, 9, 18, 5, 36, 44))
    _log(wd, [{"artifact_id": "A", "pass": False, "verified_at": "2026-09-18T05:20:47"}])
    out = audit(wd, None)
    assert [s["artifact_id"] for s in out["stale"]] == ["A"]
    assert out["stale"][0]["by"] == "timestamp"
    assert out["stale"][0]["minutes_stale"] == pytest.approx(16.0, abs=0.1)


def test_a_verdict_seconds_older_than_the_artifact_is_not_stale(tmp_path):
    """A verifier reads the file, then writes its line, so a small gap is normal."""
    wd = _world(tmp_path)
    _write(wd, "A", "body\n", datetime.datetime(2026, 9, 18, 5, 0, 30))
    _log(wd, [{"artifact_id": "A", "pass": True, "verified_at": "2026-09-18T05:00:00"}])
    assert audit(wd, None)["current"] == 1


def test_undatable_verdict_on_an_edited_artifact_is_suspect(tmp_path):
    """A preserved copy is evidence of an edit, and a PASS here is the quiet failure."""
    wd = _world(tmp_path)
    _write(wd, "A", "body\n")
    (wd / "artifacts" / "_rejected").mkdir()
    (wd / "artifacts" / "_rejected" / "A.1.md").write_text("previous\n")
    _log(wd, [{"artifact_id": "A", "pass": True}])
    out = audit(wd, None)
    assert [s["artifact_id"] for s in out["suspect"]] == ["A"]
    assert out["unresolvable"] == []


def test_undatable_verdict_on_a_never_edited_artifact_is_only_unresolvable(tmp_path):
    """Not evidence of a problem: the file is still its original render."""
    wd = _world(tmp_path)
    _write(wd, "A", "body\n")
    _log(wd, [{"artifact_id": "A", "pass": True}])
    out = audit(wd, None)
    assert [u["artifact_id"] for u in out["unresolvable"]] == ["A"]
    assert out["suspect"] == [] and out["stale"] == []


def test_last_verdict_wins_and_a_later_pass_clears_an_earlier_fail(tmp_path):
    wd = _world(tmp_path)
    sha = _write(wd, "A", "fixed\n", datetime.datetime(2026, 9, 18, 5, 36, 0))
    _log(wd, [{"artifact_id": "A", "pass": False, "verified_at": "2026-09-18T05:20:00"},
              {"artifact_id": "A", "pass": True, "verified_at": "2026-09-18T05:42:00",
               "artifact_sha256": sha}])
    out = audit(wd, None)
    assert out["current"] == 1 and out["stale"] == []


def test_a_verdict_on_a_deleted_artifact_is_ignored_not_reported(tmp_path):
    """verify_batches.py purges these; this tool must not double-count them."""
    wd = _world(tmp_path)
    _log(wd, [{"artifact_id": "GONE", "pass": False, "verified_at": "2026-09-18T05:00:00"}])
    out = audit(wd, None)
    assert out == {"stale": [], "suspect": [], "unresolvable": [], "current": 0}


def test_selection_restricts_the_audit_to_one_lane(tmp_path):
    wd = _world(tmp_path)
    _write(wd, "MINE", "edited\n", datetime.datetime(2026, 9, 18, 5, 36, 0))
    _write(wd, "THEIRS", "edited\n", datetime.datetime(2026, 9, 18, 5, 36, 0))
    _log(wd, [{"artifact_id": "MINE", "pass": False, "verified_at": "2026-09-18T05:00:00"},
              {"artifact_id": "THEIRS", "pass": False, "verified_at": "2026-09-18T05:00:00"}])
    out = audit(wd, {"MINE"})
    assert [s["artifact_id"] for s in out["stale"]] == ["MINE"]
