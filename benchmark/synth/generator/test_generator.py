"""Smoke test: build a tiny world and check the invariants that matter.

    python3 benchmark/synth/generator/test_generator.py     # or: pytest <this file>

Tiny world: 2 jurisdictions (Halvern, Calder Springs) x 3 statutes, 20 applicants,
no neighbour state. Checks:

1. every object validates against benchmark/synth/schemas (via schemas/validate.py);
2. ceiling ⊆ truth -- the recoverability buckets partition the real activity ids,
   nothing in `hidden` is revealed by any artifact about the process, and every
   `reveals.ref` resolves to a real activity/element/process-level fact;
3. no spec reveals an id it also lists in `must_not_reveal` (no leakage in the spec);
4. determinism: the same seed twice gives byte-identical output;
5. the simulated log is consistent with the graph (paths visit real activities,
   rework rounds respect the cap, elapsed >= 0).
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmark.synth.generator.build import build   # noqa: E402

TINY_KNOBS = {
    "only_jurisdictions": ["J1", "J3"],
    "only_domains": ["unpermitted_unit_amnesty", "sidewalk_vending", "solar_auto_permit"],
    "neighbor_state": False,
    "n_applicants": 20,
    "distractor_ratio": 1.5,
    "filler_cap": 60,
}


def _build(tmp: pathlib.Path, seed: int = 3) -> dict:
    return build("WTEST", seed, str(tmp), dict(TINY_KNOBS))


def _load_dir(root: pathlib.Path, sub: str) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in sorted((root / sub).glob("*.json"))}


def test_tiny_world():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="synthworld_"))
    try:
        counts = _build(tmp)
        assert counts["statutes"] == 3, counts
        assert counts["target_processes"] == 6 == counts["tasks"], counts
        assert counts["specs_target"] > 20, counts

        # 1. schema + structural validation ---------------------------------
        rc = subprocess.run([sys.executable, str(ROOT / "benchmark/synth/schemas/validate.py"),
                             "--world", str(tmp), "--quiet"], capture_output=True, text=True)
        assert rc.returncode == 0, rc.stdout + rc.stderr

        procs = _load_dir(tmp, "truth/processes")
        specs = _load_dir(tmp, "specs")
        ceiling = json.loads((tmp / "ceiling.json").read_text())
        rules = _load_dir(tmp, "truth/local_rules")
        statutes = _load_dir(tmp, "truth/statutes")

        # 2. ceiling is a subset of truth ------------------------------------
        for c in ceiling:
            proc = procs[c["model_id"]]
            ids = {a["id"] for a in proc["activities"]}
            buckets = (c["recoverable_exact"] + c["recoverable_approx"]
                       + c["only_wrong"] + c["hidden"])
            assert sorted(buckets) == sorted(ids), c["model_id"]
            about = [specs[a] for a in c["artifacts_about_process"]]
            revealed = {r["ref"] for s in about for r in s["reveals"]
                        if not r.get("process") or r["process"] == c["model_id"]}
            assert not (set(c["hidden"]) & revealed), (c["model_id"], c["hidden"])
            # everything claimed recoverable really is revealed somewhere
            for aid in c["recoverable_exact"]:
                assert aid in revealed, (c["model_id"], aid)

        # 3. specs do not leak what they hide --------------------------------
        for s in specs.values():
            refs = {r["ref"] for r in s["reveals"]}
            plain = {x for x in s["must_not_reveal"] if ":" not in x}
            assert not (refs & plain), s["artifact_id"]
            for q in (x for x in s["must_not_reveal"] if ":" in x):
                qm, qa = q.split(":", 1)
                shown = {r["ref"] for r in s["reveals"] if r.get("process") == qm}
                assert qa not in shown, (s["artifact_id"], q)
            mid = "%s__%s" % (s["jur"], s["stat_id"]) if s.get("jur") and s.get("stat_id") else None
            if mid in procs:
                staff = {a["id"] for a in procs[mid]["activities"] if a["visibility"] == "staff_only"}
                assert plain <= staff, s["artifact_id"]

        # element refs resolve; every process is within the DESIGN bounds
        for mid, proc in procs.items():
            skel = {e["element_id"] for e in statutes[proc["stat_id"]]["skeleton"]}
            local = {e["element_id"] for e in rules[mid]["added_elements"]}
            assert 8 <= len(proc["activities"]) <= 20, mid
            assert 4 <= len(proc["actors"]) <= 11, mid
            for a in proc["activities"]:
                assert a["element_ref"] in (skel | local | {None}), (mid, a["id"])

        # 5. logs are consistent with the graphs ----------------------------
        for mid, proc in procs.items():
            ids = {a["id"] for a in proc["activities"]}
            recs = [json.loads(l) for l in
                    (tmp / ("truth/log/%s.jsonl" % mid)).read_text().splitlines() if l.strip()]
            assert len(recs) == 20, mid
            for rec in recs:
                assert rec["elapsed_days"] >= 0
                assert all(step["a"] in ids for step in rec["path"])
                assert all(v <= 3 for v in rec["rework_rounds"].values())

        # 4. determinism -----------------------------------------------------
        tmp2 = pathlib.Path(tempfile.mkdtemp(prefix="synthworld_"))
        try:
            _build(tmp2)
            for rel in ("world.json", "ceiling.json", "tasks.json",
                        "truth/processes/J1__S01.json", "provenance.jsonl"):
                assert (tmp / rel).read_text() == (tmp2 / rel).read_text(), rel
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)
        return counts
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    c = test_tiny_world()
    print("smoke test OK:", json.dumps({k: c[k] for k in
                                        ("statutes", "processes", "activities", "specs_total",
                                         "specs_target", "tasks")}))
