"""Tests for Claude's solar process-structure leg.

These guard the distinctions the leg exists to protect: a missing survey answer
must never become a "No", a source cannot be both evidence and ground truth,
and a burden table must refuse to launder an unconverged posterior into a
finding. No network, no benchmark truth, no paid calls.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from pipeline.procbench.process_structure import occupancy, solar_sources as S
from pipeline.procbench.process_structure import solar_phase2 as P2

PHASE1 = S.ROOT / "runs/process_structure_20260921/solar_phase1"
needs_phase1 = pytest.mark.skipif(
    not (PHASE1 / "occupancy_evidence.json").exists(),
    reason="solar phase 1 has not been built in this checkout")


# ---------------------------------------------------------------- reading rules

@pytest.mark.parametrize("raw", ["", " ", "NA", "na", "N/A", "nan", "unknown", None, "maybe", "2019"])
def test_unanswered_survey_cells_are_not_a_no(raw):
    """The single most dangerous coercion in this leg: blank read as absence."""
    assert S.present_flag(raw) is not True
    assert S.present_flag(raw) is not False


@pytest.mark.parametrize("raw,expected", [
    ("Yes", True), ("yes (SolarAPP+)", True), ("1", True), ("Instant", True),
    ("No", False), ("0", False), ("false", False),
])
def test_answered_survey_cells_read_as_given(raw, expected):
    assert S.present_flag(raw) is expected


def test_counts_reject_missing_without_becoming_zero():
    assert S.count_value("NA") is None
    assert S.count_value("") is None
    assert S.count_value("not a number") is None
    assert S.count_value("0") == 0.0
    assert S.count_value("3") == 3.0


def test_slug_is_stable_and_collapses_punctuation():
    assert S.slug("San Buenaventura (Ventura)") == S.slug("san buenaventura  ventura")
    assert S.slug("Oakland city") == "oakland_city"


# ------------------------------------------------------------ evidence contract

@needs_phase1
def test_phase1_evidence_satisfies_the_occupancy_contract():
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    evidence = occupancy.Evidence(data)          # raises if any rule is broken
    report = evidence.support_report()
    assert report["reading_opportunities"] > 0
    assert report["reviewed_nondetections"] > 0, "a positive-only frame cannot identify detection"
    assert not report["positive_only_opportunity_frame"]


@needs_phase1
def test_no_cell_is_both_a_detection_and_an_anchor():
    """An anchor is an input to the fit. An input cannot also be the test."""
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    detection_support = {
        (row["jurisdiction_id"], row["step_id"], ref["path"], ref["sha256"], ref["locator"])
        for row in data["observations"] for ref in row["evidence_refs"]}
    for anchor in data["known_presence"]:
        for ref in anchor["evidence_refs"]:
            key = (anchor["jurisdiction_id"], anchor["step_id"],
                   ref["path"], ref["sha256"], ref["locator"])
            assert key not in detection_support


@needs_phase1
def test_every_reading_carries_a_resolvable_source_reference():
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    for row in data["observations"][:500] + data["known_presence"][:500]:
        for ref in row["evidence_refs"]:
            assert len(ref["sha256"]) == 64
            assert (S.ROOT / ref["path"]).exists()
            assert ref["locator"].strip()


@needs_phase1
def test_the_universe_contains_steps_no_ledger_activity_names():
    """If the universe came only from the parse, a county-added step could never appear."""
    rows = [json.loads(line) for line in (PHASE1 / "step_universe.jsonl").read_text().splitlines()]
    matrix_only = [r for r in rows if r["named_in"] == ["requirements_matrix"]]
    assert matrix_only, "no step entered the universe from a source outside the ledger"
    assert {r["layer_label"] for r in rows} <= {
        "statutory", "administrative-only", "other-party-or-applicant"}


# ------------------------------------------------------------------ subsampling

@needs_phase1
def test_subsample_keeps_the_evidence_internally_consistent():
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    reduced, size = P2.subsample(data, 25)
    assert size == 25 and len(reduced["jurisdictions"]) == 25
    keep = set(reduced["jurisdictions"])
    assert all(o["jurisdiction_id"] in keep for o in reduced["observations"])
    assert all(a["jurisdiction_id"] in keep for a in reduced["known_presence"])
    assert reduced["assumption_note"] != data["assumption_note"], "the restriction must be declared"
    occupancy.Evidence(reduced)                  # still a valid contract
    assert len(data["jurisdictions"]) > 25, "the original must not have been mutated"


@needs_phase1
def test_subsample_is_a_no_op_when_the_size_covers_everything():
    data = json.loads((PHASE1 / "occupancy_evidence.json").read_text())
    same, size = P2.subsample(data, 10 ** 6)
    assert same is data and size == len(data["jurisdictions"])


def test_withhold_removes_only_the_matrix_and_only_for_held_out():
    data = {"observations": [
        {"jurisdiction_id": "a", "source_type": "requirements_matrix"},
        {"jurisdiction_id": "a", "source_type": "agency_document"},
        {"jurisdiction_id": "b", "source_type": "requirements_matrix"},
    ], "assumption_note": "note"}
    fold, dropped = P2.withhold(data, {"a"})
    assert dropped == 1
    kept = {(o["jurisdiction_id"], o["source_type"]) for o in fold["observations"]}
    assert kept == {("a", "agency_document"), ("b", "requirements_matrix")}
    assert len(data["observations"]) == 3, "the original evidence must not be mutated"


# --------------------------------------------------------------- scoring pieces

def test_brier_and_log_score_reward_the_truth():
    good, _ = P2.brier_and_log([1, 0], [.9, .1])
    bad, _ = P2.brier_and_log([1, 0], [.1, .9])
    assert good < bad


def test_auc_is_undefined_without_both_classes():
    assert P2.auc([1, 1, 1], [.2, .5, .9]) is None
    assert P2.auc([0, 1], [.1, .9]) == 1.0
    assert P2.auc([0, 1], [.9, .1]) == 0.0


def test_calibration_bins_cover_every_scored_case():
    truth = [0, 1, 1, 0, 1]
    prob = [.05, .95, .55, .35, .75]
    bins = P2.calibration(truth, prob)
    assert sum(b["n"] for b in bins) == len(truth)
    assert all(0 <= b["observed_rate"] <= 1 for b in bins)


# ------------------------------------------------------------------ burden table

def test_burden_table_declares_where_its_presence_numbers_came_from():
    path = S.ROOT / "runs/process_structure_20260921/solar_phase5/burden_table.json"
    if not path.exists():
        pytest.skip("solar phase 5 has not been built in this checkout")
    table = json.loads(path.read_text())
    basis = table["presence_basis"]
    assert basis["source"] in {"occupancy_posterior", "direct_evidence_no_model"}
    if basis["source"] == "direct_evidence_no_model":
        assert "why" in basis and basis["why"].strip()
    shares = [p["share_of_measured_elapsed_time"] for p in table["burden_by_phase"].values()]
    assert math.isclose(sum(shares), 1.0, rel_tol=1e-9)


def test_burden_table_never_gives_a_step_a_time_without_a_phase_clock():
    path = S.ROOT / "runs/process_structure_20260921/solar_phase5/burden_table.json"
    if not path.exists():
        pytest.skip("solar phase 5 has not been built in this checkout")
    for row in json.loads(path.read_text())["steps"]:
        if row["phase_clock"] is None:
            assert row["phase_median_business_days"] is None
