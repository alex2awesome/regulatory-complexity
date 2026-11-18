"""Solar phase 3: presence posteriors for every authority and every step.

Phase 2 asked whether the model can be trusted on authorities whose answers are
hidden. This runs it on everything it has and writes the posterior it produces:
for each authority, the probability that each step is part of its process, and
the joint posterior over how many steps its process contains.

The count is a lower bound on steps that exist, because the universe is the
union of steps some source named and no model can find a step nobody mentioned.
It is not a lower bound on steps that burden anyone: a step no source has ever
named has imposed no burden anyone reported.
"""
from __future__ import annotations

import argparse
import collections
import json
import time

import numpy as np

from . import occupancy, solar_sources as S

PHASE1 = S.ROOT / "runs/process_structure_20260921/solar_phase1"
OUT = S.ROOT / "runs/process_structure_20260921/solar_phase3"
SEED = 20260921


def run(chains, warmup, draws):
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    universe = {row["step_id"]: row for row in
                (json.loads(line) for line in (PHASE1 / "step_universe.jsonl").read_text().splitlines())}
    config = occupancy.Config(chains=chains, warmup=warmup, draws=draws, seed=SEED)

    started = time.time()
    result, arrays = occupancy.fit(data, config)
    elapsed = time.time() - started

    jurisdictions, steps = data["jurisdictions"], data["steps"]
    probability = np.asarray(result["presence_probability"])
    draws_z = arrays["presence"]                       # chains x draws x J x S
    flat = draws_z.reshape(-1, len(jurisdictions), len(steps))
    lower = np.quantile(flat, .05, axis=0)
    upper = np.quantile(flat, .95, axis=0)

    # per-step prevalence across authorities, with the layer it was observed in
    by_step = []
    for si, step in enumerate(steps):
        row = universe.get(step, {})
        by_step.append({
            "step_id": step,
            "label": row.get("label"),
            "layer": row.get("layer_label"),
            "actor": row.get("actor"),
            "named_in": row.get("named_in"),
            "mean_presence_across_authorities": float(probability[:, si].mean()),
            "authorities_above_half": int((probability[:, si] > .5).sum()),
            "authorities_above_ninety": int((probability[:, si] > .9).sum()),
            "has_any_reading_opportunity": bool(
                any(o["step_id"] == step for o in data["observations"])),
        })

    with (OUT / "presence_by_authority.jsonl").open("w") as fh:
        for ji, j in enumerate(jurisdictions):
            fh.write(json.dumps({
                "jurisdiction_id": j,
                "expected_step_count": float(probability[ji].sum()),
                "joint_step_count": result["joint_step_count"][j],
                "steps": {s: {"presence": float(probability[ji, si]),
                              "ci90": [float(lower[ji, si]), float(upper[ji, si])]}
                          for si, s in enumerate(steps) if probability[ji, si] > .01},
            }, sort_keys=True) + "\n")

    layer_totals = collections.defaultdict(float)
    for si, step in enumerate(steps):
        layer_totals[universe.get(step, {}).get("layer_label", "unknown")] += float(probability[:, si].mean())

    detection = arrays["detection"].reshape(-1, len(steps), len(data["source_types"]))
    detection_summary = {}
    for ki, kind in enumerate(data["source_types"]):
        observed = {o["step_id"] for o in data["observations"] if o["source_type"] == kind}
        values = [float(detection[:, si, ki].mean()) for si, s in enumerate(steps) if s in observed]
        detection_summary[kind] = {
            "steps_with_a_reading": len(values),
            "mean_detection_probability": float(np.mean(values)) if values else None,
            "range": [float(np.min(values)), float(np.max(values))] if values else None,
        }

    report = {
        "schema_version": "solar-occupancy-posterior/1",
        "packet": "solar_phase3",
        "seconds": elapsed,
        "numerically_usable": result["numerically_usable"],
        "flagged_count": len(result["flagged"]),
        "flagged_examples": result["flagged"][:25],
        "worst_rhat": max((d["rhat"] for d in result["diagnostics"].values()
                           if d["rhat"] is not None), default=None),
        "min_ess_bulk": min((d["ess_bulk"] for d in result["diagnostics"].values()), default=None),
        "support": result["support"],
        "jurisdiction_logit_scale": result["jurisdiction_logit_scale"],
        "steps": by_step,
        "expected_steps_per_authority_by_layer": dict(layer_totals),
        "detection_by_source_type": detection_summary,
        "expected_step_count": {
            "mean": float(probability.sum(axis=1).mean()),
            "min": float(probability.sum(axis=1).min()),
            "max": float(probability.sum(axis=1).max()),
        },
        "qualifications": result["qualifications"] + [
            "The step count is a lower bound on steps that exist: the universe is the union of "
            "steps some source named, and no model finds a step nobody mentioned.",
            "A step with no reading opportunity anywhere keeps its prior and should be read as "
            "unmeasured, not as present at the prior rate.",
        ],
    }
    (OUT / "presence_report.json").write_text(json.dumps(report, indent=2))
    np.savez_compressed(OUT / "posterior_arrays.npz",
                        presence_probability=probability,
                        step_count=arrays["step_count"], detection=arrays["detection"])
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=400)
    parser.add_argument("--draws", type=int, default=600)
    args = parser.parse_args()
    report = run(args.chains, args.warmup, args.draws)
    print(json.dumps({k: report[k] for k in
                      ("numerically_usable", "worst_rhat", "min_ess_bulk",
                       "expected_step_count", "expected_steps_per_authority_by_layer",
                       "detection_by_source_type")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
