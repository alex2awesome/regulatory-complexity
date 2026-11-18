"""Markdown tables for the toy statute results doc (scorer-side; reads truth).

  python -m pipeline.procbench.toy_statute.report --world runs/.../W0 --scores runs/.../W0/scores_final \
      --answers bayes=... llm0=... ...
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .truth_eval import truth_estimands

LEVER_KEYS = [
    ("{t}.total.days_mean", "mean total days"),
    ("{t}.dstep_days.D1", "D1 application days"),
    ("{t}.dstep_days.D2", "D2 nuisance-determination days (vague step)"),
    ("{t}.dstep_days.D3", "D3 decision days"),
    ("{t}.total.hours_mean", "applicant hours"),
    ("{t}.total.dollars_mean", "dollars"),
    ("{t}.deadline.p_miss", "P(miss 30-day deadline)"),
    ("{t}.complexity.expected_psteps", "p-steps executed per case"),
    ("{t}.complexity.path_entropy_bits", "path entropy (bits)"),
    ("{t}.counterfactual.delta_days_mean", "Δ days if §3 made concrete"),
]
STATUTE_KEYS = [
    ("statute.d2_implementation_entropy_bits", "D2 implementation variety (bits)"),
    ("statute.d2_days_between_town_sd", "between-town SD of D2 days"),
    ("statute.cf_mean_delta_days", "Δ mean days per town if §3 made concrete"),
    ("statute.cf_delta_between_town_sd_days", "Δ between-town SD of total days"),
]


def fmt(v):
    return "–" if v is None else f"{v[1]:.2f} [{v[0]:.2f}, {v[2]:.2f}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--answers", nargs="+", required=True)
    a = ap.parse_args()
    truth, _ = truth_estimands(json.loads((Path(a.world) / "truth" / "world.json").read_text()))
    towns = json.loads((Path(a.world) / "evidence" / "public_spec.json").read_text())["towns"]
    ans = {}
    for s in a.answers:
        n, p = s.split("=", 1)
        ans[n] = json.loads(Path(p).read_text())
    names = list(ans)
    lines = []
    for t in towns:
        lines.append(f"\n**{t}** (true structure {[S for S in 'S1 S2 S3 S4 S5 S6'.split() if truth[f'{t}.structure_probs.{S}'] == 1][0]}; "
                     + "P(true structure): " + ", ".join(
                         f"{n} {ans[n]['structure_probs'][t][[S for S in 'S1 S2 S3 S4 S5 S6'.split() if truth[f'{t}.structure_probs.{S}'] == 1][0]]:.2f}"
                         for n in names) + ")\n")
        lines.append("| estimand | truth | " + " | ".join(names) + " |")
        lines.append("|---|---|" + "---|" * len(names))
        for key, label in LEVER_KEYS:
            k = key.format(t=t)
            lines.append(f"| {label} | {truth[k]:.2f} | " + " | ".join(fmt(ans[n]["estimands"].get(k)) for n in names) + " |")
    lines.append("\n**Statute level**\n")
    lines.append("| estimand | truth | " + " | ".join(names) + " |")
    lines.append("|---|---|" + "---|" * len(names))
    for k, label in STATUTE_KEYS:
        lines.append(f"| {label} | {truth[k]:.2f} | " + " | ".join(fmt(ans[n]["estimands"].get(k)) for n in names) + " |")
    summ = json.loads((Path(a.scores) / "summary.json").read_text())
    lines.append("\n**Scores** (lower is better except log score; non-trivial = excluding estimands that are exactly 0 in truth and answered [0,0,0])\n")
    lines.append("| method | structure log score | non-trivial scaled interval score | non-trivial 90% coverage | non-trivial scaled median error | predictive pinball |")
    lines.append("|---|---|---|---|---|---|")
    for n, s in summ["summary"].items():
        lines.append(f"| {n} | {s['structure_mean_log_score']:.3f} | {s['nontrivial_mean_scaled_is']:.3f} | "
                     f"{s['nontrivial_coverage90']:.2f} | {s['nontrivial_mean_scaled_abs_err']:.3f} | {s['predictive_mean_pinball']:.3f} |")
    fams = sorted(next(iter(summ["summary"].values()))["families"])
    lines.append("\n**Scaled interval score by estimand family**\n")
    lines.append("| family | " + " | ".join(summ["summary"]) + " |")
    lines.append("|---|" + "---|" * len(summ["summary"]))
    for f in fams:
        lines.append(f"| {f} | " + " | ".join(
            (f"{s['families'][f]['mean_scaled_is']:.3f}" if f in s["families"] else "–") for s in summ["summary"].values()) + " |")
    lines.append("\n**Head-to-head (non-trivial estimands, lower interval score wins)**\n")
    for k, v in summ["head_to_head_interval_score"].items():
        lines.append(f"- {k}: {v}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
