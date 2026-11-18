"""Are the rarely-detected steps what stops the S05 fit from mixing?

At 30 jurisdictions the fit misses its gate: R-hat 1.085 against 1.01, minimum
effective sample size 68 against 400, while the MEDIAN effective sample size is
above fifty thousand. Almost everything mixes; a handful of coordinates do not.

Sixteen of the 45 steps are detected three times or fewer across 266 documents.
A step seen once has almost nothing separating "rare but present" from "common
but rarely mentioned", so its prevalence and its detection probability trade off
against each other and the chain wanders along that trade-off.

This refits on the 29 steps detected more than three times, changing nothing
else. If the gate then passes, the diagnosis is precise and the remedy is a
modelling decision about rare steps rather than more compute. If it still
fails, the problem is the number of jurisdictions and the module's memory
profile, and that is a different conversation.

Dropping rare steps is a DIAGNOSTIC, not a proposal. Those steps are exactly
the county-added burden the project cares about; they must not be discarded
from a real analysis because they are inconvenient to sample.
"""
from __future__ import annotations

import argparse
import collections
import json

import numpy as np

from . import occupancy, solar_sources as S
from .synthetic_evidence import PACKETS

MIN_POSITIVES = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=8000)
    parser.add_argument("--draws", type=int, default=20000)
    args = parser.parse_args()

    directory = PACKETS["S05"]
    data = json.loads((directory / "occupancy_evidence.json").read_text())

    positives = collections.Counter(
        o["step_id"] for o in data["observations"] if o["detected"])
    keep = [s for s in data["steps"] if positives[s] >= MIN_POSITIVES]
    dropped = [s for s in data["steps"] if positives[s] < MIN_POSITIVES]

    reduced = dict(data)
    reduced["steps"] = keep
    reduced["observations"] = [o for o in data["observations"] if o["step_id"] in set(keep)]
    reduced["known_presence"] = [a for a in data["known_presence"] if a["step_id"] in set(keep)]
    reduced["assumption_note"] = (
        data["assumption_note"] + f" DIAGNOSTIC RUN: restricted to the {len(keep)} steps detected "
        f"at least {MIN_POSITIVES} times, dropping {len(dropped)}, purely to test whether rarely "
        "detected steps are what stops the sampler mixing. The dropped steps are county-added "
        "burden and must not be discarded from a real analysis.")

    config = occupancy.Config(chains=args.chains, warmup=args.warmup,
                              draws=args.draws, seed=20260921)
    result, arrays = occupancy.fit(reduced, config)
    structural = {k: v for k, v in result["diagnostics"].items()
                  if not k.startswith("presence_probability")}
    rhats = [d["rhat"] for d in structural.values() if d["rhat"] is not None]
    ess = [d["ess_bulk"] for d in structural.values()]

    report = {
        "schema_version": "s05-rare-step-diagnostic/1",
        "purpose": "Test whether rarely detected steps are what stops the S05 fit mixing.",
        "config": {"chains": args.chains, "warmup": args.warmup, "draws": args.draws},
        "steps_kept": len(keep), "steps_dropped": len(dropped),
        "dropped_steps": dropped,
        "minimum_positive_detections_to_keep": MIN_POSITIVES,
        "numerically_usable": result["numerically_usable"],
        "worst_rhat_structural": max(rhats) if rhats else None,
        "min_ess_bulk_structural": min(ess) if ess else None,
        "median_ess_bulk_structural": float(np.median(ess)) if ess else None,
        "flagged_structural": len([k for k in result["flagged"]
                                   if not k.startswith("presence_probability")]),
        "comparison_with_all_45_steps": {
            "worst_rhat": 1.0848, "min_ess_bulk": 68.5, "numerically_usable": False},
        "reading": (
            "If this run passes the gate and the 45-step run does not, rare steps are the cause "
            "and the remedy is a modelling decision about them, not more compute. If it still "
            "fails, the binding constraint is the number of jurisdictions together with the "
            "module retaining one draw per jurisdiction and step."),
        "warning": (
            "Dropping rare steps is a diagnostic only. They are the county-added burden the "
            "project exists to measure and must not be dropped from a real analysis."),
    }
    (directory / "rare_step_diagnostic.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in
                      ("steps_kept", "steps_dropped", "numerically_usable",
                       "worst_rhat_structural", "min_ess_bulk_structural",
                       "comparison_with_all_45_steps")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
