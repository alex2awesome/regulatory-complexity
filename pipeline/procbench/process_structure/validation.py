"""Predeclared jurisdiction holdouts and proper binary-presence scores.

These helpers do not certify reference labels as truth, execute fits, or release
posteriors. They distinguish prediction with other test-jurisdiction evidence
from prediction for an entirely unseen jurisdiction. Reference-derived source
lineage must be reviewed upstream; hash checks alone cannot discover leakage.
"""
from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path

from .occupancy import Evidence


def jurisdiction_split(jurisdictions, *, fraction=.2, seed="20260921"):
    """Order-invariant split, chosen without looking at outcomes or mentions."""
    ids = list(jurisdictions)
    if (len(ids) < 2 or any(not isinstance(x, str) or not x.strip() for x in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError("Need at least two distinct jurisdiction IDs")
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not 0 < fraction < 1:
        raise ValueError("Holdout fraction must be strictly between zero and one")
    ordered = sorted(ids, key=lambda x: hashlib.sha256(f"{seed}\0{x}".encode()).hexdigest())
    n = min(len(ids) - 1, max(1, math.ceil(len(ids) * fraction)))
    return {"training_jurisdictions": sorted(ordered[n:]),
            "heldout_jurisdictions": sorted(ordered[:n]), "seed": str(seed),
            "requested_fraction": fraction, "actual_fraction": n / len(ids)}


def reference_holdout(data, heldout_jurisdictions, *, mode, source_root=None):
    """Remove held-out anchors and declared reference-derived observations.

Every observation must carry ``lineage_reviewed=True`` and an explicit list of
``lineage_refs`` (same path/hash/locator form as evidence_refs; [] when none).
    Resolved source paths and byte-identical SHA256 copies of withheld labels are
    conservatively withheld from observations in ALL jurisdictions, including
    declared derivatives. Use the same source_root as the fit runner. Training reference labels
may share a tabular source file with test labels: only their own rows remain as
anchors. Callers still must rule out undeclared copies and derived features.
"""
    Evidence(data)
    if data.get("uncertain_jurisdiction_units"):
        raise ValueError("Uncertain identity holdouts require an explicit candidate/lineage exclusion policy; not implemented")
    if mode not in {"reference_labels_only", "unseen_jurisdiction"}:
        raise ValueError("Choose reference_labels_only or unseen_jurisdiction")
    heldout = set(heldout_jurisdictions)
    if not heldout or not heldout < set(data["jurisdictions"]):
        raise ValueError("Hold out a nonempty proper subset of jurisdictions")
    labels = [copy.deepcopy(x) for x in data["known_presence"] if x["jurisdiction_id"] in heldout]
    if not labels:
        raise ValueError("No independent reference labels in held-out jurisdictions")
    root = Path(source_root if source_root is not None else Path.cwd()).resolve()
    def resolved_path(ref):
        return str((root / ref["path"]).resolve())
    reference_paths = {resolved_path(r) for row in labels for r in row["evidence_refs"]}
    reference_hashes = {r["sha256"] for row in labels for r in row["evidence_refs"]}
    retained, excluded = [], []
    for row in data["observations"]:
        lineage = row.get("lineage_refs")
        if row.get("lineage_reviewed") is not True or not isinstance(lineage, list):
            raise ValueError("Validation requires reviewed reference-source lineage for every observation")
        for ref in lineage:
            if (not isinstance(ref, dict)
                    or any(not isinstance(ref.get(k), str) or not ref[k] for k in ("path", "sha256", "locator"))
                    or len(ref["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in ref["sha256"])):
                raise ValueError("Invalid source-lineage reference")
        reference_derived = any(resolved_path(r) in reference_paths or r["sha256"] in reference_hashes
                                for r in row["evidence_refs"] + lineage)
        no_test_evidence = mode == "unseen_jurisdiction" and row["jurisdiction_id"] in heldout
        if reference_derived or no_test_evidence:
            excluded.append({"unit_id": row["unit_id"], "step_id": row["step_id"],
                             "reason": "reference_source_or_derivative" if reference_derived else "unseen_jurisdiction"})
        else:
            retained.append(copy.deepcopy(row))
    training = copy.deepcopy(data)
    training["observations"] = retained
    training["known_presence"] = [x for x in training["known_presence"] if x["jurisdiction_id"] not in heldout]
    Evidence(training)
    receipt = {"mode": mode, "heldout_jurisdictions": sorted(heldout),
               "heldout_reference_cells": len(labels), "reference_paths_excluded_from_observations": sorted(reference_paths),
               "reference_sha256_excluded_from_observations": sorted(reference_hashes),
               "source_root": str(root),
               "excluded_observations": excluded, "retained_observation_count": len(retained),
               "lineage_limit": "Declared reviewed lineage only; undeclared copies and feature leakage need independent review."}
    return training, labels, receipt


def _key(row):
    return row["jurisdiction_id"], row["step_id"]


def score_presence(predictions, labels, *, bins=10):
    """Exact coverage, micro/macro Brier and log loss, calibration bin counts.

No epsilon clipping: an impossible observed outcome has infinite log loss,
represented JSON-safely by null plus an explicit infinite-loss flag/count.
No unsupported full-process count is inferred from a partial reference panel.
"""
    if type(bins) is not int or bins < 1:
        raise ValueError("bins must be a positive integer")
    pred = {_key(x): x for x in predictions}
    truth = {_key(x): x for x in labels}
    if (not truth or len(pred) != len(predictions) or len(truth) != len(labels) or set(pred) != set(truth)):
        raise ValueError("Predictions must cover exactly the distinct held-out reference cells")
    scores, calibration = [], [[] for _ in range(bins)]
    for key in sorted(truth):
        p, y = pred[key].get("probability"), truth[key].get("present")
        if (isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p)
                or not 0 <= p <= 1 or type(y) is not bool):
            raise ValueError("Need finite probabilities and boolean reference labels")
        correct_probability = p if y else 1 - p
        loss = (-math.log(p) if y else -math.log1p(-p)) if correct_probability else math.inf
        scores.append((key[0], (p - int(y)) ** 2, loss))
        calibration[min(bins - 1, int(p * bins))].append((p, int(y)))

    def aggregate(rows):
        impossible = sum(math.isinf(x[2]) for x in rows)
        return {"cells": len(rows), "brier": sum(x[1] for x in rows) / len(rows),
                "mean_log_loss": None if impossible else sum(x[2] for x in rows) / len(rows),
                "infinite_log_loss": bool(impossible), "impossible_outcomes": impossible}

    per_jurisdiction = {j: aggregate([r for r in scores if r[0] == j]) for j in sorted({r[0] for r in scores})}
    groups = list(per_jurisdiction.values())
    return {"schema_version": "process-structure-presence-scores/1", "micro": aggregate(scores),
            "jurisdiction_macro": {
                "jurisdictions": len(groups), "brier": sum(g["brier"] for g in groups) / len(groups),
                "mean_log_loss": None if any(g["infinite_log_loss"] for g in groups) else sum(g["mean_log_loss"] for g in groups) / len(groups),
                "infinite_log_loss": any(g["infinite_log_loss"] for g in groups)},
            "per_jurisdiction": per_jurisdiction,
            "calibration_bins": [{"lower": i / bins, "upper": (i + 1) / bins, "upper_inclusive": i == bins - 1,
                                  "cells": len(values),
                                  "mean_probability": sum(v[0] for v in values) / len(values) if values else None,
                                  "observed_fraction": sum(v[1] for v in values) / len(values) if values else None}
                                 for i, values in enumerate(calibration)],
            "scientific_release_eligible": False,
            "qualification": "Scores apply only to reviewed reference fields and eras; bin counts alone do not establish calibration or transportability."}


def baseline_predictions(training_data, reference_cells):
    """Same-cell observed-only and Beta(1,1) smoothed training-label baselines.

Reference cells supply identity only; their outcomes are never read. A zero in
the observed-only comparator is a baseline prediction, not a known absence.
"""
    evidence = Evidence(training_data)
    if {_key(r) for r in training_data["known_presence"]} & {_key(r) for r in reference_cells}:
        raise ValueError("Baseline reference outcomes cannot remain in training anchors")
    positive = evidence.positive.sum(axis=2)
    pooled = {}
    for step in evidence.s:
        anchors = [r["present"] for r in training_data["known_presence"] if r["step_id"] == step]
        pooled[step] = (1 + sum(anchors)) / (2 + len(anchors))
    observed, prevalence = [], []
    for cell in reference_cells:
        j, s = _key(cell)
        if j not in evidence.j or s not in evidence.s:
            raise ValueError("Reference cell is outside the training universe")
        base = {"jurisdiction_id": j, "step_id": s}
        observed.append(dict(base, probability=float(positive[evidence.j[j], evidence.s[s]] > 0)))
        prevalence.append(dict(base, probability=pooled[s]))
    return {"observed_only": observed, "pooled_training_reference_prevalence": prevalence}
