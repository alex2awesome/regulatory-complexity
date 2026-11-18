"""Solar phase 2: does the occupancy model read silence as absence?

The SolarTRACE requirements matrix is the only real ground truth this project
has about whether a process step exists in a jurisdiction. The test is the one
the work order specifies: hide it for a fifth of authorities, fit on what is
left, and score the recovered presence against the hidden answers.

Two things are being asked at once.

  * Calibration. Does the posterior probability of presence mean what it says
    on authorities the survey never answered for?
  * Silence. An authority whose survey answer is hidden has almost no evidence
    left. If the model responds by driving presence to zero, it is reading
    silence as absence, and every step count it produces for a thinly
    documented jurisdiction is wrong in the same direction. The gate is that
    the recovered step count must not fall with sparsity faster than the
    file's own count of Yes answers does.

A fold's held-out answers are removed from the fit entirely. They are never
anchors: an anchor is an input, and an input cannot be a test.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import numpy as np

from . import occupancy, solar_sources as S

PHASE1 = S.ROOT / "runs/process_structure_20260921/solar_phase1"
OUT = S.ROOT / "runs/process_structure_20260921/solar_phase2"
FOLDS = 5
SEED = 20260921

# The questions scored. Each is a static survey column whose answer the panel
# does not already anchor, so hiding it really does remove the evidence.
SCORED = {
    "solar_permit__ahj_structural_review": "Structural Review Required",
    "solar_permit__ahj_electrical_review": "Electrical Review Required",
    "solar_permit__ahj_third_party_plan_review": "Third-Party Permit Review",
    "solar_permit__ahj_rough_inspection": "Rough-In Inspection Required",
    "solar_permit__ahj_in_person_counter_permitting": "Same Day In-Person Permitting Available",
}


def subsample(data, size, seed=SEED):
    """Restrict the evidence to a random sample of authorities.

    The occupancy sampler retains one presence draw per authority and step, so
    its memory grows as chains x draws x authorities x steps and it cannot be
    run long enough to mix at 440 authorities. Restricting the problem is how
    the held-out test is still run honestly at the sizes the other two families
    will use: concealed carry has 30 authorities and CalFresh 58 counties.
    """
    if size is None or size >= len(data["jurisdictions"]):
        return data, len(data["jurisdictions"])
    rng = np.random.default_rng(seed)
    keep = set(rng.choice(data["jurisdictions"], size=size, replace=False).tolist())
    reduced = dict(data)
    reduced["jurisdictions"] = [j for j in data["jurisdictions"] if j in keep]
    reduced["observations"] = [o for o in data["observations"] if o["jurisdiction_id"] in keep]
    reduced["known_presence"] = [a for a in data["known_presence"] if a["jurisdiction_id"] in keep]
    reduced["assumption_note"] = (
        data["assumption_note"] +
        f" This run uses a random sample of {size} of {len(data['jurisdictions'])} authorities, "
        "because the sampler's retained draws grow with the number of authorities. The sample is "
        "drawn once from a fixed seed and is not chosen by any property of the authorities.")
    return reduced, size


def assign_folds(jurisdictions):
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(jurisdictions))
    return {jurisdictions[int(j)]: int(i % FOLDS) for i, j in enumerate(order)}


def withhold(data, held):
    """Drop every requirements-matrix reading for the held-out authorities."""
    kept, dropped = [], 0
    for row in data["observations"]:
        if row["source_type"] == "requirements_matrix" and row["jurisdiction_id"] in held:
            dropped += 1
            continue
        kept.append(row)
    fold = dict(data)
    fold["observations"] = kept
    fold["assumption_note"] = (
        data["assumption_note"] + " In this fold the requirements matrix is withheld for "
        f"{len(held)} authorities so that their answers can be scored rather than fitted.")
    return fold, dropped


def brier_and_log(truth, prob):
    truth = np.asarray(truth, dtype=float)
    prob = np.clip(np.asarray(prob, dtype=float), 1e-9, 1 - 1e-9)
    return (float(np.mean((prob - truth) ** 2)),
            float(-np.mean(truth * np.log(prob) + (1 - truth) * np.log1p(-prob))))


def auc(truth, prob):
    truth = np.asarray(truth)
    if truth.min() == truth.max():
        return None
    order = np.argsort(np.asarray(prob), kind="mergesort")
    ranks = np.empty(len(order), dtype=float)
    ranks[order] = np.arange(1, len(order) + 1)
    positives, negatives = truth.sum(), (1 - truth).sum()
    return float((ranks[truth == 1].sum() - positives * (positives + 1) / 2)
                 / (positives * negatives))


def calibration(truth, prob, bins=5):
    truth, prob = np.asarray(truth, dtype=float), np.asarray(prob, dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (prob >= lo) & (prob < hi if hi < 1 else prob <= 1)
        if not mask.any():
            continue
        out.append({"bin": [round(lo, 2), round(hi, 2)], "n": int(mask.sum()),
                    "mean_predicted": float(prob[mask].mean()),
                    "observed_rate": float(truth[mask].mean())})
    return out


def run(chains, warmup, draws, folds_to_run, size=None, tag=""):
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    data, size = subsample(data, size)
    reqs = S.read_requirements()
    jurisdictions = data["jurisdictions"]
    fold_of = assign_folds(jurisdictions)
    step_index = {s: i for i, s in enumerate(data["steps"])}
    config = occupancy.Config(chains=chains, warmup=warmup, draws=draws, seed=SEED)

    pooled = {step: {"truth": [], "prob": []} for step in SCORED}
    sparsity_rows, fold_reports = [], []

    for fold in range(FOLDS):
        if fold not in folds_to_run:
            continue
        held = {j for j in jurisdictions if fold_of[j] == fold}
        fold_data, dropped = withhold(data, held)
        started = time.time()
        result, arrays = occupancy.fit(fold_data, config)
        elapsed = time.time() - started
        probability = np.asarray(result["presence_probability"])

        per_step = {}
        for step, column in SCORED.items():
            si = step_index[step]
            truth, prob, names = [], [], []
            for j in sorted(held):
                answer = S.present_flag((reqs.get(j) or {}).get(column))
                if answer is None:
                    continue
                truth.append(int(answer))
                prob.append(float(probability[jurisdictions.index(j), si]))
                names.append(j)
            if not truth:
                continue
            pooled[step]["truth"].extend(truth)
            pooled[step]["prob"].extend(prob)
            brier, logscore = brier_and_log(truth, prob)
            base_rate = float(np.mean([
                S.present_flag((reqs.get(j) or {}).get(column))
                for j in jurisdictions
                if j not in held and S.present_flag((reqs.get(j) or {}).get(column)) is not None]))
            base_brier, base_log = brier_and_log(truth, np.full(len(truth), base_rate))
            per_step[step] = {
                "scored_authorities": len(truth), "observed_rate": float(np.mean(truth)),
                "mean_posterior_presence": float(np.mean(prob)),
                "brier": brier, "log_score": logscore, "auc": auc(truth, prob),
                "training_base_rate": base_rate,
                "baseline_brier_training_base_rate": base_brier,
                "baseline_log_score": base_log,
                "beats_base_rate_baseline": bool(brier < base_brier),
                "calibration": calibration(truth, prob),
            }

        # the silence test: recovered count against the file's own count
        for j in sorted(held):
            answered = {step: S.present_flag((reqs.get(j) or {}).get(column))
                        for step, column in SCORED.items()}
            answered = {k: v for k, v in answered.items() if v is not None}
            if not answered:
                continue
            sparsity_rows.append({
                "jurisdiction": j, "fold": fold,
                "questions_answered_in_file": len(answered),
                "file_yes_count": int(sum(answered.values())),
                "recovered_expected_count": float(sum(
                    probability[jurisdictions.index(j), step_index[s]] for s in answered)),
                "other_source_readings_retained": int(sum(
                    1 for o in fold_data["observations"] if o["jurisdiction_id"] == j)),
            })

        trimmed = {k: v for k, v in result.items()
                   if k not in {"diagnostics", "presence_probability", "joint_step_count", "flagged"}}
        structural = [name for name in result["flagged"]
                      if not name.startswith("presence_probability")]
        trimmed["flagged_structural_parameters"] = len(structural)
        trimmed["flagged_presence_cells"] = len(result["flagged"]) - len(structural)
        trimmed["flagged_examples"] = structural[:20]
        trimmed["worst_rhat"] = max(
            (d["rhat"] for d in result["diagnostics"].values() if d["rhat"] is not None), default=None)
        trimmed["min_ess_bulk"] = min(
            (d["ess_bulk"] for d in result["diagnostics"].values()), default=None)
        trimmed["seconds"] = elapsed
        trimmed["withheld_authorities"] = len(held)
        trimmed["withheld_readings"] = dropped
        trimmed["per_step_heldout_score"] = per_step
        (OUT / f"{tag}fold{fold}_report.json").write_text(json.dumps(trimmed, indent=2))
        np.savez_compressed(OUT / f"fold{fold}_detection.npz", detection=arrays["detection"])
        fold_reports.append({"fold": fold, "numerically_usable": result["numerically_usable"],
                             "worst_rhat": trimmed["worst_rhat"], "seconds": elapsed,
                             "withheld_authorities": len(held), "withheld_readings": dropped})
        del arrays, result
        print(f"fold {fold}: {elapsed:.1f}s usable={fold_reports[-1]['numerically_usable']} "
              f"worst_rhat={trimmed['worst_rhat']}")

    # ---- pooled scoring and the two gates
    pooled_scores = {}
    for step, blob in pooled.items():
        if not blob["truth"]:
            continue
        brier, logscore = brier_and_log(blob["truth"], blob["prob"])
        pooled_scores[step] = {
            "scored_authorities": len(blob["truth"]),
            "observed_rate": float(np.mean(blob["truth"])),
            "mean_posterior_presence": float(np.mean(blob["prob"])),
            "brier": brier, "log_score": logscore, "auc": auc(blob["truth"], blob["prob"]),
            "calibration": calibration(blob["truth"], blob["prob"]),
        }

    if sparsity_rows:
        file_total = sum(r["file_yes_count"] for r in sparsity_rows)
        recovered_total = sum(r["recovered_expected_count"] for r in sparsity_rows)
        thin = [r for r in sparsity_rows if r["other_source_readings_retained"] == 0]
        rich = [r for r in sparsity_rows if r["other_source_readings_retained"] > 0]
        silence = {
            "authorities_scored": len(sparsity_rows),
            "file_yes_total": file_total,
            "recovered_expected_total": recovered_total,
            "recovered_over_file": recovered_total / file_total if file_total else None,
            "thin_authorities_no_other_reading": len(thin),
            "thin_file_mean": float(np.mean([r["file_yes_count"] for r in thin])) if thin else None,
            "thin_recovered_mean": float(np.mean([r["recovered_expected_count"] for r in thin])) if thin else None,
            "other_authorities_file_mean": float(np.mean([r["file_yes_count"] for r in rich])) if rich else None,
            "other_authorities_recovered_mean": float(np.mean([r["recovered_expected_count"] for r in rich])) if rich else None,
        }
    else:
        silence = {"authorities_scored": 0}

    gate_calibration = all(
        s["brier"] < 0.25 for s in pooled_scores.values()) if pooled_scores else False
    ratio = silence.get("recovered_over_file")
    gate_silence = ratio is not None and 0.5 <= ratio <= 2.0

    report = {
        "schema_version": "solar-occupancy-heldout/1",
        "packet": "solar_phase2",
        "design": ("Five folds over 440 authorities. In each fold every requirements-matrix "
                   "reading for the held-out authorities is removed from the fit, and their "
                   "answers are then scored against the posterior. Held-out answers are never "
                   "anchors, because an anchor is an input to the fit."),
        "config": {"chains": chains, "warmup": warmup, "draws": draws,
                   "folds": sorted(folds_to_run), "seed": SEED, "authorities": size},
        "convergence": {
            "any_fold_numerically_usable": any(f["numerically_usable"] for f in fold_reports),
            "worst_rhat_across_folds": max((f["worst_rhat"] for f in fold_reports
                                            if f["worst_rhat"] is not None), default=None),
            "note": ("A fit that fails its convergence gate produces no scientific result. The "
                     "held-out scores below are reported for every run so that the relationship "
                     "between problem size, mixing and predictive quality is visible, but a "
                     "score from an unconverged fit is a diagnostic, not a finding."),
        },
        "folds": fold_reports,
        "pooled_heldout_scores": pooled_scores,
        "silence_is_not_absence_check": silence,
        "gates": {
            "calibration_gate_every_step_brier_below_quarter": gate_calibration,
            "silence_gate_recovered_count_within_half_to_double_the_file": gate_silence,
            "both_passed": bool(gate_calibration and gate_silence),
        },
        "qualifications": [
            "A held-out authority usually retains no other reading at all, so its posterior is "
            "the hierarchy's prediction rather than an inference from its own evidence. That is "
            "the quantity the project needs and it is what is scored here.",
            "Detection probability for the scored steps is transported from the steps where "
            "repeated readings and panel anchors identify it. That transport is an assumption.",
            "Passing these gates is a numerical and predictive result. It is not a release: no "
            "population claim, no causal claim, no transport beyond California solar.",
        ],
    }
    (OUT / f"{tag}heldout_report.json").write_text(json.dumps(report, indent=2))
    with (OUT / f"{tag}sparsity_rows.jsonl").open("w") as fh:
        for row in sparsity_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=300)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--folds", default="all")
    parser.add_argument("--authorities", type=int, default=None,
                        help="restrict to a random sample of this many authorities")
    parser.add_argument("--tag", default="", help="filename prefix for this condition")
    args = parser.parse_args()
    folds = set(range(FOLDS)) if args.folds == "all" else {int(x) for x in args.folds.split(",")}
    report = run(args.chains, args.warmup, args.draws, folds, args.authorities, args.tag)
    print(json.dumps({k: report[k] for k in
                      ("config", "convergence", "gates", "silence_is_not_absence_check")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
