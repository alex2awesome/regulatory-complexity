"""Two agents driving different statutes must not share a single slot.

`V` was one such slot: `verify_batches.py` deletes and rebuilds every `V*.json`
when it runs, so an agent closing out S05 would have wiped the batch files a
second agent was verifying S12 against. The same shape already destroyed render
work once. `--prefix` gives a lane its own namespace and `--selection` keeps its
work inside its own bundle.

The second thing pinned here is the liveness guard. It refuses a rebuild while a
verify wave is appending, because rewriting a batch file changes what a running
agent is asked to check. A prefix whose files do not exist yet is a different
case, not an exception to be forced: no agent can be reading a file that is not
there. These tests check the guard both ways round, so `--force` never becomes
the habitual answer.

And `launch_ledger.py done` is checked for the inference that has already failed:
elapsed silence is not an observed completion.

No network, no paid calls.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from benchmark.synth.render import launch_ledger, verify_batches


def _world(tmp_path, monkeypatch, ids, verdicts=(), rendered=None):
    root = tmp_path
    wd = root / "benchmark/synth/worlds/W_TEST"
    (wd / "artifacts").mkdir(parents=True)
    (wd / "specs").mkdir()
    (wd / "batches").mkdir()
    for aid in (rendered if rendered is not None else ids):
        (wd / "artifacts" / ("%s.md" % aid)).write_text("body\n")
        (wd / "specs" / ("%s.json" % aid)).write_text(json.dumps(
            {"artifact_id": aid, "kind": "program_page", "style": {"length_words": [300, 400]},
             "jur": aid.split("__")[0]}))
    with (wd / "verify_log.jsonl").open("w") as f:
        for v in verdicts:
            f.write(json.dumps(v) + "\n")
    monkeypatch.setattr(verify_batches, "ROOT", root)
    # Writing the log just now leaves it warm, so the real guard would sit through
    # its 20-second growth sample in every test. Default to "not live" and let the
    # two tests that are actually ABOUT the guard override it.
    monkeypatch.setattr(verify_batches, "wave_is_live",
                        lambda *a, **k: (False, "test fixture: no wave"))
    return wd


def _batches(wd, glob):
    return sorted(p.name for p in (wd / "batches").glob(glob))


def test_prefix_leaves_another_lanes_batches_alone(tmp_path, monkeypatch):
    wd = _world(tmp_path, monkeypatch, ["C01__a", "C02__b"])
    (wd / "batches" / "V00.json").write_text(json.dumps({"batch_id": "V00", "spec_ids": ["x"]}))
    rc = verify_batches.main(["--world", "W_TEST", "--prefix", "A"])
    assert rc == 0
    assert _batches(wd, "AV*.json") == ["AV00.json"]
    # the other lane's slot is untouched, contents included
    assert json.loads((wd / "batches" / "V00.json").read_text())["spec_ids"] == ["x"]


def test_no_prefix_still_rebuilds_the_shared_slot(tmp_path, monkeypatch):
    """The default behaviour must not change: this is what the other agent drives."""
    wd = _world(tmp_path, monkeypatch, ["C01__a"])
    (wd / "batches" / "V00.json").write_text(json.dumps({"batch_id": "V00", "spec_ids": ["x"]}))
    assert verify_batches.main(["--world", "W_TEST"]) == 0
    assert json.loads((wd / "batches" / "V00.json").read_text())["spec_ids"] == ["C01__a"]


def test_selection_keeps_a_lane_out_of_another_lanes_artifacts(tmp_path, monkeypatch):
    wd = _world(tmp_path, monkeypatch, ["C01__mine", "C02__theirs"])
    (wd / "mine.txt").write_text("C01__mine\n")
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A",
                                "--selection", "mine.txt"]) == 0
    rec = json.loads((wd / "batches" / "AV00.json").read_text())
    assert rec["spec_ids"] == ["C01__mine"]


def test_also_force_includes_an_id_that_already_has_a_verdict(tmp_path, monkeypatch):
    """For a verdict whose freshness cannot be established, see stale_verdicts.py."""
    wd = _world(tmp_path, monkeypatch, ["C01__a", "C01__b"],
                verdicts=[{"artifact_id": "C01__a", "pass": True}])
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A"]) == 0
    assert json.loads((wd / "batches" / "AV00.json").read_text())["spec_ids"] == ["C01__b"]
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A",
                                "--also", "C01__a"]) == 0
    assert json.loads((wd / "batches" / "AV00.json").read_text())["spec_ids"] == ["C01__a", "C01__b"]


def test_a_fresh_namespace_is_built_even_while_a_wave_is_live(tmp_path, monkeypatch):
    """Safe by construction: no agent can be reading files that do not exist."""
    wd = _world(tmp_path, monkeypatch, ["C01__a"])
    called = {"n": 0}

    def _live(*_a, **_k):
        called["n"] += 1
        return True, "log is growing"

    monkeypatch.setattr(verify_batches, "wave_is_live", _live)
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A"]) == 0
    assert _batches(wd, "AV*.json") == ["AV00.json"]
    assert called["n"] == 0, "the guard should not even be consulted for an unused namespace"


def test_an_existing_namespace_is_still_protected_while_a_wave_is_live(tmp_path, monkeypatch):
    """The guard is right; a prefix is not a way around it."""
    wd = _world(tmp_path, monkeypatch, ["C01__a"])
    (wd / "batches" / "AV00.json").write_text(json.dumps({"batch_id": "AV00", "spec_ids": ["old"]}))
    monkeypatch.setattr(verify_batches, "wave_is_live", lambda *a, **k: (True, "log is growing"))
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A"]) == 1
    assert json.loads((wd / "batches" / "AV00.json").read_text())["spec_ids"] == ["old"]


def test_a_lane_build_never_rewrites_the_shared_verify_log(tmp_path, monkeypatch):
    """The purge is a whole-world repair; a lane build must not touch a shared file."""
    wd = _world(tmp_path, monkeypatch, ["C01__a"],
                verdicts=[{"artifact_id": "C01__a", "pass": True},
                          {"artifact_id": "DELETED__x", "pass": False}])
    before = (wd / "verify_log.jsonl").read_text()
    assert verify_batches.main(["--world", "W_TEST", "--prefix", "A",
                                "--also", "C01__a"]) == 0
    assert (wd / "verify_log.jsonl").read_text() == before


def test_ledger_done_refuses_an_elapsed_silence_argument(tmp_path, monkeypatch, capsys):
    root = tmp_path
    wd = root / "benchmark/synth/worlds/W_TEST"
    wd.mkdir(parents=True)
    monkeypatch.setattr(launch_ledger, "ROOT", root)
    assert launch_ledger.main(["record", "--world", "W_TEST", "--run", "wf_x",
                               "--ids", "AT00"]) == 0
    # the exact reasoning that failed: four hours of quiet read as a death
    assert launch_ledger.main(["done", "--world", "W_TEST", "--run", "wf_x",
                               "--evidence", "verify log untouched for 14788 s"]) == 1
    assert "wf_x" in launch_ledger.outstanding(wd)
    # and with no evidence at all
    assert launch_ledger.main(["done", "--world", "W_TEST", "--run", "wf_x"]) == 1
    assert "wf_x" in launch_ledger.outstanding(wd)


def test_ledger_done_accepts_an_observed_completion(tmp_path, monkeypatch):
    root = tmp_path
    wd = root / "benchmark/synth/worlds/W_TEST"
    wd.mkdir(parents=True)
    monkeypatch.setattr(launch_ledger, "ROOT", root)
    launch_ledger.main(["record", "--world", "W_TEST", "--run", "wf_x", "--ids", "AT00"])
    assert launch_ledger.main(["done", "--world", "W_TEST", "--run", "wf_x", "--evidence",
                               "task notification reported 22/22 agents done"]) == 0
    assert launch_ledger.outstanding(wd) == {}
    assert launch_ledger.conflicts(wd, ["AT00"]) == []


def test_ledger_still_refuses_a_launch_overlapping_an_outstanding_one(tmp_path, monkeypatch):
    root = tmp_path
    wd = root / "benchmark/synth/worlds/W_TEST"
    wd.mkdir(parents=True)
    monkeypatch.setattr(launch_ledger, "ROOT", root)
    launch_ledger.main(["record", "--world", "W_TEST", "--run", "wf_x", "--ids", "AT00,AT01"])
    assert launch_ledger.main(["check", "--world", "W_TEST", "--ids", "AT01"]) == 1
    assert launch_ledger.main(["check", "--world", "W_TEST", "--ids", "AT09"]) == 0
