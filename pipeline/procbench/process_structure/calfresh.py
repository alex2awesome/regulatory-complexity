"""Compile fully reviewed CalFresh county documents into occupancy evidence.

This bounded adapter does not manufacture reference truth, forum nondetections,
or county-by-county copies of statewide guidance. It is deliberately a pilot
of the declared 15-action initial-decision window, not all CalFresh burden.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .occupancy import Evidence, SCHEMA


COUNTY_SOURCES = {
    "S5": ("Los_Angeles", "la_staff_processing", "staff_policy"),
    "S19": ("Santa_Clara", "sc_staff_processing", "staff_policy"),
    "S7": ("San_Francisco", "sf_public_guides", "official_public_guide"),
    "S8": ("San_Francisco", "sf_public_guides", "official_public_guide"),
    "S9": ("Sacramento", "sac_public_guide", "official_public_guide"),
}


def compile_county_readings(scope, readings, *, source_root, detection_beta=(2., 2.), false_positive=.02):
    """Validate complete source-bound readings and union dependent SF pages.

    Semantic adoption is required on every reading before compilation. That
    flag records review; it cannot itself prove correct action interpretation.
    Non-detection references bind whole read documents, not a search hit.
    """
    root = Path(source_root)
    steps = [row["id"] for row in scope["steps"]]
    if not steps or len(set(steps)) != len(steps):
        raise ValueError("Canonical steps must be distinct and nonempty")
    if set(scope["source_scope"]) != set(COUNTY_SOURCES):
        raise ValueError("County pilot source frame changed; review the adapter explicitly")
    by_source = {}
    for reading in readings:
        sid = reading.get("source_id")
        if sid not in COUNTY_SOURCES or sid in by_source:
            raise ValueError("Unexpected or duplicate source reading")
        if reading.get("complete_reading") is not True or reading.get("root_adopted") is not True:
            raise ValueError("Need a complete, root-adopted semantic reading")
        expected_path = f"corpus/realworld/calfresh/raw/{sid}.txt"
        if reading.get("path") != expected_path:
            raise ValueError("Reading is not bound to its frozen county source path")
        raw = (root / expected_path).read_bytes()
        text = raw.decode("utf-8")
        if hashlib.sha256(raw).hexdigest() != reading.get("sha256"):
            raise ValueError("Changed source bytes")
        if reading.get("character_count") != len(text):
            raise ValueError("Incomplete whole-reading range")
        rows = reading.get("rows", [])
        if len(rows) != len(steps) or {r.get("step_id") for r in rows} != set(steps):
            raise ValueError("Each source needs exactly one review for every canonical step")
        for row in rows:
            if type(row.get("detected")) is not bool:
                raise ValueError("Detection must be a reviewed boolean")
            quotes = row.get("quotes")
            if not isinstance(quotes, list) or row["detected"] and not quotes:
                raise ValueError("Positive detections need exact quotations")
            for quote in quotes:
                start, end, value = quote.get("start"), quote.get("end"), quote.get("text")
                if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                        or not isinstance(value, str) or not value.strip() or text[start:end] != value):
                    raise ValueError("Quotation does not replay from captured source bytes")
        by_source[sid] = reading
    if set(by_source) != set(COUNTY_SOURCES):
        raise ValueError("Every selected source needs a complete review, not only positive sources")

    groups = {}
    for sid, (county, group, kind) in COUNTY_SOURCES.items():
        groups.setdefault((county, group, kind), []).append(by_source[sid])
    observations = []
    for (county, group, kind), members in groups.items():
        for step in steps:
            selected = [(member, next(row for row in member["rows"] if row["step_id"] == step))
                        for member in members]
            positive = any(row["detected"] for _, row in selected)
            refs, lineage = [], []
            for member, row in selected:
                whole = dict(path=member["path"], sha256=member["sha256"],
                             locator=f"whole captured source chars [0,{member['character_count']}); reviewed {step}")
                lineage.append(whole)
                # Both pages remain provenance even if only one contains a hit.
                refs.append(whole)
                if row["detected"]:
                    refs.extend(dict(path=member["path"], sha256=member["sha256"],
                                     locator=f"chars [{q['start']},{q['end']})", quote=q["text"])
                                for q in row["quotes"])
            observations.append(dict(unit_id=group, dependence_group_id=group,
                                     jurisdiction_id=county, step_id=step, source_type=kind,
                                     detected=positive, reviewed_scope=True, evidence_refs=refs,
                                     lineage_reviewed=True, lineage_refs=lineage,
                                     source_ids=[member["source_id"] for member in members]))
    data = dict(
        schema_version=SCHEMA,
        scope=scope["scope"],
        jurisdictions=list(dict.fromkeys(v[0] for v in COUNTY_SOURCES.values())),
        steps=steps, source_types=["staff_policy", "official_public_guide"],
        source_models={k: dict(detection_beta=list(detection_beta), false_positive_probability=false_positive)
                       for k in ["staff_policy", "official_public_guide"]},
        opportunity_frame="reviewed_units_not_selected_for_step_mentions",
        conditional_independence="assumed_given_presence_and_source_type_detection",
        assumption_note=("Fixed five-document captured-source frame, four county publisher groups. "
                         "SF pages are unioned once per action. Distinct action detections remain "
                         "conditionally independent by assumption; document completeness/verbosity "
                         "is not explicitly modeled. Source genre and county are confounded. "
                         "Captured-document scope only: effective policy eras are unresolved. "
                         "No independent truth anchors or completed heldout presence validation."),
        observations=observations, known_presence=[],
        fit_purpose="exploratory_identification_and_prior_sensitivity_not_scientific_release",
    )
    Evidence(data)
    return data
