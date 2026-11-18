"""The corpus-anchor audit classifies artifacts correctly.

The audit's own logic needs testing, because two defects in it produced false
alarms about a corpus that was fine: it compared a record-count slope against a
document count, and it counted distractor artifacts in the population slope.
Both made a faithful corpus look broken, which is the worse direction for an
audit to err in -- a false alarm gets chased, and chasing it re-tunes a
generator that was already right.

Built on a tiny world so the test needs no large build. No network, no paid
calls, no benchmark truth beyond the world manifest.
"""
from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

from benchmark.synth.generator.build import build
from pipeline.procbench.audit_corpus_anchors import ANCHORS, TIERS, audit


@pytest.fixture(scope="module")
def tiny_county_world():
    out = pathlib.Path(tempfile.mkdtemp()) / "W2_TEST"
    build("W2_TEST", 5, str(out), {
        "world_model_version": 2, "n_counties": 4, "n_applicants": 40,
        "distractor_ratio": 1.0, "only_domains": ["well_permit", "mobile_food",
                                                  "rental_inspection"],
    })
    return out


def test_every_artifact_kind_maps_to_exactly_one_tier():
    """A kind in two tiers would be double-counted; a kind in none is silently
    dropped from the denominator, which is how `news` went missing."""
    seen: dict[str, str] = {}
    for tier, kinds in TIERS.items():
        for kind in kinds:
            assert kind not in seen, "%s is in both %s and %s" % (kind, seen[kind], tier)
            seen[kind] = tier


def test_audit_leaves_no_kind_unclassified(tiny_county_world):
    rep = audit(tiny_county_world)
    assert "error" not in rep, rep.get("error")
    assert not rep.get("unclassified_kinds"), (
        "unclassified kinds are excluded from every slope: %s" % rep.get("unclassified_kinds"))


def test_distractors_are_excluded_from_the_slopes(tiny_county_world):
    """A look-alike is hosted on a county's site but is not a product of that
    county's caseload, so its count is flat in population."""
    rep = audit(tiny_county_world)
    assert rep["distractors_excluded"], "the world has distractors; they must be counted out"


def test_the_observed_anchor_is_about_records_not_documents():
    """0.989 is the slope of the case-record count. Comparing it to a document
    count is a category error that fails a correct corpus."""
    assert "RECORDS" in ANCHORS["observed_record_slope"]["unit"]
    assert "not artifacts" in ANCHORS["observed_record_slope"]["unit"]


def test_every_anchor_names_its_source():
    for name, spec in ANCHORS.items():
        assert spec.get("source"), "%s has no source" % name
        assert spec.get("unit"), "%s has no unit" % name


def test_audit_refuses_a_non_county_world():
    out = pathlib.Path(tempfile.mkdtemp()) / "W1_TEST"
    build("W1_TEST", 5, str(out), {"only_jurisdictions": ["J1"],
                                   "only_domains": ["well_permit"],
                                   "n_applicants": 20})
    rep = audit(out)
    assert "error" in rep, "a v1 world has no county panel to audit"


def test_user_tier_is_steeper_than_the_declared_tier(tiny_county_world):
    """The corpus-level version of the register's central finding: posts track
    population, official pages exist everywhere."""
    rep = audit(tiny_county_world)
    assert rep["tiers"]["user"]["slope"] > rep["tiers"]["declared"]["slope"]
