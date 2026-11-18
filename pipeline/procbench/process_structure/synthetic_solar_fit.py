"""Fit occupancy on the synthetic solar test-bed and report mixing honestly.

Four counties and 34 steps is the smallest real configuration this project
will ever ask the sampler for, and it is the richest in repeat readings: 7.75
looks at each county-step pair against roughly one in the real corpus. If the
sampler cannot mix here it cannot mix anywhere, and if it can, this bounds the
size at which the occupancy approach is usable at all.

No truth is read here. Scoring against the world's truth is a separate step
that records the fact that it read it.
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from . import occupancy, solar_sources as S

DIR = S.ROOT / "runs/process_structure_20260921/synthetic_solar"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=4000)
    parser.add_argument("--draws", type=int, default=12000)
    args = parser.parse_args()

    data = json.loads((DIR / "occupancy_evidence.json").read_text())
    config = occupancy.Config(chains=args.chains, warmup=args.warmup,
                              draws=args.draws, seed=20260921)
    result, arrays = occupancy.fit(data, config)

    structural = {k: v for k, v in result["diagnostics"].items()
                  if not k.startswith("presence_probability")}
    rhats = [d["rhat"] for d in structural.values() if d["rhat"] is not None]
    ess = [d["ess_bulk"] for d in structural.values()]
    white = arrays["hierarchy_white"]
    move = float(np.abs(np.diff(white, axis=1)).mean())

    probability = np.asarray(result["presence_probability"])
    counties, steps = data["jurisdictions"], data["steps"]
    detection = arrays["detection"].reshape(-1, len(steps), len(data["source_types"]))
    by_source = {}
    for ki, kind in enumerate(data["source_types"]):
        seen = {o["step_id"] for o in data["observations"] if o["source_type"] == kind}
        values = [float(detection[:, si, ki].mean()) for si, s in enumerate(steps) if s in seen]
        by_source[kind] = {"steps_with_a_reading": len(values),
                           "mean_detection_probability": float(np.mean(values)) if values else None}

    report = {
        "schema_version": "synthetic-solar-occupancy/1",
        "packet": "synthetic_solar_fit",
        "config": {"chains": args.chains, "warmup": args.warmup, "draws": args.draws},
        "size": {"counties": len(counties), "steps": len(steps),
                 "latent_dimension": int(white.shape[-1]),
                 "reading_opportunities": int((data and len(data["observations"])) or 0)},
        "numerically_usable": result["numerically_usable"],
        "worst_rhat_structural": max(rhats) if rhats else None,
        "min_ess_bulk_structural": min(ess) if ess else None,
        "median_ess_bulk_structural": float(np.median(ess)) if ess else None,
        "mean_absolute_move_per_draw": move,
        "flagged_structural": len([k for k in result["flagged"]
                                   if not k.startswith("presence_probability")]),
        "detection_by_source_type": by_source,
        "expected_steps_per_county": {c: float(probability[i].sum())
                                      for i, c in enumerate(counties)},
        "presence": {c: {s: round(float(probability[i, j]), 4) for j, s in enumerate(steps)}
                     for i, c in enumerate(counties)},
        "reads_world_truth": False,
        "qualification": ("Mixing is reported before any presence number is used. If the gate "
                          "fails the presence table is a diagnostic, not a result."),
    }
    (DIR / "occupancy_fit.json").write_text(json.dumps(report, indent=2))
    np.savez_compressed(DIR / "occupancy_draws.npz",
                        presence_probability=probability,
                        step_count=arrays["step_count"], detection=arrays["detection"])
    print(json.dumps({k: report[k] for k in
                      ("size", "numerically_usable", "worst_rhat_structural",
                       "min_ess_bulk_structural", "median_ess_bulk_structural",
                       "mean_absolute_move_per_draw", "detection_by_source_type",
                       "expected_steps_per_county")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
