#!/usr/bin/env python3
"""Build a verified-link semantic calibration label set from a decision-model world.

Stage 4 of docs/2026-09-16-county-scale-up-plan.md, and the audit's
highest-value missing piece: calibrating interpretation error instead of
assuming it.

`semantic_calibration.fit_calibration` refuses a row whose `link_status` is not
`verified`, and rightly so: a guessed crosswalk between a rendered sentence and
the fact that produced it would fabricate the confusion matrix it is supposed to
measure. That is exactly why the W1 attempt stalled at zero verified labels
(`prepare_semantic_labels.py`): a document-level render log cannot say which
sentence carries which claim.

A world built with `decision_model_version` 2 does not have that problem. Every
`criterion` reveal in an artifact spec names the predicate it discloses
(`ref`), the fidelity it must be written at, and the literal value the renderer
must state; the truth carries that predicate's actual reading. **The link is
verified by construction**, because the generator planted the sentence in order
to disclose that specific reading. So the label set can be emitted with no
crosswalk inference at all.

What this module does and does not give you:

* It emits `true_label` for every disclosed criterion, with the group, the
  ambiguity class, the label space and the fit/validation split. That is the
  ground truth half, and it is complete.
* It leaves `top_label` to be filled by an actual extractor run over the
  rendered text. Until that happens there is no measured accuracy, and this
  module will not invent one: `--extractor simulated` exists only to exercise
  the fitter against a *known* confusion matrix, and it stamps the output so
  the result can never be mistaken for a measurement.

Ambiguity classes, matching the plan's §4 table:

    reading_value      which threshold this jurisdiction applies (the discretion residual)
    criterion_kind     crisp / standard / delegated / local
    fixability         can a failure be corrected, or is it a denial
    evaluating_step    which activity performs the check

    python3 -m pipeline.procbench.build_semantic_labels \\
        --world benchmark/synth/worlds/W2 --out runs/calib/w2_labels.json
    python3 -m pipeline.procbench.build_semantic_labels \\
        --world <w> --out <o> --extractor simulated --sim-accuracy 0.82
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random

LABEL_SCHEMA = "semantic-calibration-labels/1"
FIDELITY_STRATA = ("exact", "approximate", "vague", "wrong")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_world(root: pathlib.Path):
    world = json.loads((root / "world.json").read_text())
    if int(world.get("decision_model_version", 1)) < 2:
        raise ValueError("This world has no decision layer, so no criterion reveal carries a "
                         "verified link. Rebuild with decision_model_version=2.")
    procs = {p.stem: json.loads(p.read_text()) for p in sorted((root / "truth/processes").glob("*.json"))}
    specs = [json.loads(p.read_text()) for p in sorted((root / "specs").glob("*.json"))]
    return world, procs, specs


def _predicates(proc: dict) -> dict[str, dict]:
    return {e["pred_id"]: e for e in (proc.get("decision_model") or {}).get("predicates", [])}


def build(root: pathlib.Path, split_fraction: float = 0.4, seed: int = 20260916):
    """One row per (artifact, disclosed criterion). Groups are artifacts, because
    every claim in one document shares its author, its register and its errors."""
    world, procs, specs = load_world(root)
    rng = random.Random(seed)

    # Split by PROGRAM, not by artifact: two artifacts about the same process
    # share its readings, so splitting artifacts would leak the answer across
    # the fit/validation boundary.
    programs = sorted(procs)
    rng.shuffle(programs)
    n_val = max(2, int(round(split_fraction * len(programs))))
    validation = set(programs[:n_val])

    spaces: dict[str, set] = {"criterion_kind": set(), "fixability": {"fixable", "fatal"},
                              "evaluating_step": set(), "reading_value": set()}
    rows = []
    for spec in specs:
        mid = None
        if spec.get("jur") and spec.get("stat_id"):
            mid = "%s__%s" % (spec["jur"], spec["stat_id"])
        for reveal in spec.get("reveals", []):
            if reveal.get("field") != "criterion":
                continue
            target = reveal.get("process") or mid
            proc = procs.get(target)
            if not proc:
                continue
            entry = _predicates(proc).get(reveal["ref"])
            if not entry or not entry.get("reading"):
                continue
            fidelity = reveal.get("fidelity", "exact")
            base = dict(world_id=world["world"], program_id=target, pred_id=entry["pred_id"],
                        group_id="%s::%s" % (target, spec["artifact_id"]),
                        artifact_id=spec["artifact_id"], artifact_kind=spec["kind"],
                        split="validation" if target in validation else "fit",
                        link_status="verified",
                        truth_provenance=("generator planted this reveal to disclose %s of %s; "
                                          "specs/%s.json reveals[] -> truth/processes/%s.json"
                                          "#decision_model.predicates[%s]"
                                          % (entry["pred_id"], target, spec["artifact_id"],
                                             target, entry["pred_id"])),
                        stratum=fidelity if fidelity in FIDELITY_STRATA else "all",
                        disclosed_value=str(reveal.get("value", ""))[:300],
                        disclosed_fidelity=fidelity)
            truths = {
                "reading_value": entry["reading"]["label"],
                "criterion_kind": entry["kind"],
                "fixability": "fixable" if entry["fixable"] else "fatal",
                "evaluating_step": entry["evaluated_at"],
            }
            for cls, true_label in truths.items():
                spaces.setdefault(cls, set()).add(true_label)
                rows.append(dict(base, id="%s::%s::%s" % (base["group_id"], entry["pred_id"], cls),
                                 ambiguity_class=cls, true_label=true_label, top_label=None))

    # A label space needs at least two members to be a classification problem.
    spaces = {k: sorted(v) for k, v in spaces.items() if len(v) >= 2}
    rows = [r for r in rows if r["ambiguity_class"] in spaces]
    return dict(schema_version=LABEL_SCHEMA, world_id=world["world"],
                purpose="development_calibration",
                extractor=dict(model=None, prompt_sha256=None,
                               note="top_label is UNFILLED; run an extractor over the rendered "
                                    "artifacts and fill it before fitting"),
                label_spaces=spaces, rows=rows,
                provenance=dict(world_root=str(root), decision_model_version=world.get("decision_model_version"),
                                split="by program, so artifacts about one process cannot straddle the split",
                                validation_programs=sorted(validation),
                                groups="one per (program, artifact): claims in a document share author and errors"),
                counts=dict(rows=len(rows), programs=len(programs),
                            validation_programs=len(validation),
                            by_class={k: sum(1 for r in rows if r["ambiguity_class"] == k) for k in spaces}))


def simulate_extractor(dataset: dict, accuracy: float, seed: int = 7) -> dict:
    """Fill `top_label` from a deliberately imperfect labeller with a KNOWN error
    rate, so the fitter can be checked against a matrix we already know.

    This is a test instrument, not a measurement. Fidelity carries the error:
    an `exact` disclosure is read correctly far more often than a `vague` or
    `wrong` one, which is the effect the real calibration is meant to quantify.
    """
    if not 0 < accuracy <= 1:
        raise ValueError("accuracy must be in (0, 1]")
    rng = random.Random(seed)
    per_stratum = {"exact": min(1.0, accuracy + .12), "approximate": accuracy,
                   "vague": max(.05, accuracy - .25), "wrong": max(.02, accuracy - .45),
                   "all": accuracy}
    out = json.loads(json.dumps(dataset))
    realised = {}
    for row in out["rows"]:
        labels = out["label_spaces"][row["ambiguity_class"]]
        p = per_stratum.get(row.get("stratum", "all"), accuracy)
        if rng.random() < p:
            row["top_label"] = row["true_label"]
        else:
            others = [x for x in labels if x != row["true_label"]] or labels
            row["top_label"] = rng.choice(others)
        slot = realised.setdefault(row["ambiguity_class"], [0, 0])
        slot[0] += row["top_label"] == row["true_label"]
        slot[1] += 1
    out["extractor"] = dict(model="SIMULATED-NOT-A-REAL-EXTRACTOR",
                            prompt_sha256=_sha("simulated:%.4f:%d" % (accuracy, seed)),
                            simulated=True, target_accuracy=accuracy,
                            per_stratum_target=per_stratum,
                            warning="Fitting this yields a KNOWN matrix, not a measured one. "
                                    "Never report it as a calibration of any real extractor.")
    out["simulated_realised_accuracy"] = {k: round(c / n, 4) for k, (c, n) in realised.items()}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--split-fraction", type=float, default=0.4)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--extractor", choices=["none", "simulated"], default="none")
    ap.add_argument("--sim-accuracy", type=float, default=0.85)
    a = ap.parse_args(argv)
    dataset = build(pathlib.Path(a.world), a.split_fraction, a.seed)
    if a.extractor == "simulated":
        dataset = simulate_extractor(dataset, a.sim_accuracy)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dataset, indent=1))
    print("wrote %s" % out)
    print("  rows %d over %d programs (%d held out for validation)"
          % (dataset["counts"]["rows"], dataset["counts"]["programs"],
             dataset["counts"]["validation_programs"]))
    for cls, n in sorted(dataset["counts"]["by_class"].items()):
        print("  %-16s %4d rows, %d labels" % (cls, n, len(dataset["label_spaces"][cls])))
    if dataset["extractor"].get("simulated"):
        print("  SIMULATED extractor, realised accuracy: %s" % dataset["simulated_realised_accuracy"])
    else:
        print("  top_label is UNFILLED: run a real extractor before fitting")


if __name__ == "__main__":
    main()
