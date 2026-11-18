"""Solar phase 1: the step universe and the detection matrix.

Builds, for the solar permitting statute as implemented by California
authorities, a jurisdiction-by-step-by-source-type table in which every cell is
a reviewed reading opportunity that either detected the step or did not, with
its own source provenance. The output is the evidence contract the occupancy
model consumes in phase 2.

Three commitments, from the work order:

  * The universe is the union of every step named in ANY source, never the
    statute alone, and every step carries the layer it was observed in.
  * A missing survey answer is no reading opportunity. It is not a "No".
  * A source that says "no" is a reviewed non-detection, and whether that means
    absence is for the model to decide through its detection probability.

Reads no benchmark truth, no generator specs, no scores.
"""
from __future__ import annotations

import collections
import json
import pathlib

from . import solar_sources as S

OUT = S.ROOT / "runs/process_structure_20260921/solar_phase1"

# Requirements-matrix columns that name a process step, and the step they name.
# A column is listed here only when answering it is a statement about whether
# the authority performs that step.
# Requirements-matrix questions that name a process step. Each entry is the
# survey wave it belongs to, the column, and the step it asks about. A wave is a
# separate reading of the authority, so two waves asking the same question are
# the repeat visits that let detection be told apart from presence.
#
# The 2019 and 2022 online-permitting waves are NOT used as repeats: Government
# Code 65850.52 required authorities to stand up automated permitting on a
# staggered deadline through 2024, so a change between those waves is a real
# change in the process rather than a detection difference. Only the 2024 and
# 2025 waves sit after the mandate and can be read as two looks at one step.
MATRIX_QUESTIONS = [
    ("static", "Structural Review Required", "solar_permit__ahj_structural_review"),
    ("static", "Electrical Review Required", "solar_permit__ahj_electrical_review"),
    ("static", "Third-Party Permit Review", "solar_permit__ahj_third_party_plan_review"),
    ("static", "Rough-In Inspection Required", "solar_permit__ahj_rough_inspection"),
    ("static", "Same Day In-Person Permitting Available",
     "solar_permit__ahj_in_person_counter_permitting"),
    ("2024", "Online Permitting - 2024", "solar_permit__ahj_online_permit_submission"),
    ("2025", "Online Permitting - 2025", "solar_permit__ahj_online_permit_submission"),
    ("2024", "Online Instant Permitting - 2024",
     "solar_permit__solarapp_automated_compliance_review"),
    ("2025", "PV Online Instant Permitting - 2025",
     "solar_permit__solarapp_automated_compliance_review"),
]

# Counted and priced questions that also state whether a step happens at all.
# The inspection count is the one question the matrix and the timeline panel
# both bear on, so it is where detection for this source is actually estimated
# rather than assumed.
MATRIX_COUNT_QUESTIONS = [
    ("static", "Number of Inspections Required", "solar_permit__ahj_final_inspection"),
    ("static", "Median Permit Cost", "solar_permit__ahj_permit_fee_payment"),
]

# Historical waves kept out of the fit and reported instead, for the same reason.
MATRIX_HISTORICAL = ["Online Permitting in 2019", "Online Permitting - 2022",
                     "Online Instant Permitting - 2022"]

# Steps the matrix names that the ledger's activity list does not contain. They
# enter the universe because a source named them; that is the whole design.
MATRIX_ONLY_STEPS = {
    "solar_permit__ahj_structural_review": (
        "AHJ structural plan review of the solar permit application",
        "ahj__unknown_ca_building_department"),
    "solar_permit__ahj_electrical_review": (
        "AHJ electrical plan review of the solar permit application",
        "ahj__unknown_ca_building_department"),
    "solar_permit__ahj_third_party_plan_review": (
        "Plan review outsourced by the AHJ to a third-party reviewer",
        "inspector__third_party"),
    "solar_permit__ahj_in_person_counter_permitting": (
        "Over-the-counter same-day permitting at the building department counter",
        "ahj__unknown_ca_building_department"),
    "solar_permit__ahj_online_permit_submission": (
        "Online submission of the solar permit application through the AHJ portal",
        "installer__solar_contractor"),
}

# Panel phase -> the step whose occurrence a reported timeline demonstrates.
# These become explicit-presence anchors, never detections, so that a cell is
# never both evidence and ground truth.
PHASE_ANCHOR = {
    "permit_review": "solar_permit__ahj_permit_issuance",
    "inspection": "solar_permit__ahj_final_inspection",
    "pre_install_ix": "solar_permit__utility_preinstall_approval_to_build",
    "final_ix_pto": "solar_permit__utility_pto_grant",
}

# Steps stated by California law rather than by any one authority's practice.
# This labels a layer; it is not a per-jurisdiction detection, because one
# statewide sentence is not independent evidence about 440 authorities.
STATUTORY_STEPS = {
    "solar_permit__ahj_permit_application_submission",
    "solar_permit__ahj_completeness_determination",
    "solar_permit__ahj_plan_review",
    "solar_permit__ahj_permit_issuance",
    "solar_permit__ahj_final_inspection",
    "solar_permit__ahj_permit_fee_payment",
    "solar_permit__ahj_appeal",
    "solar_permit__ahj_expedited_ordinance_adoption",
    "solar_permit__ahj_solarapp_adoption",
    "solar_permit__utility_pto_grant",
    "solar_permit__rule21_dispute_resolution",
}

# Documents in the ledger are bound to an authority by their own identifier
# prefix, which is how the parse recorded provenance. Utility and statewide
# documents are deliberately absent: they are not evidence about an authority.
DOC_PREFIX_AUTHORITY = {
    "oakland": "oakland_city",
    "sandiego": "san_diego_city",
}

NAMED_AHJ_ACTORS = {
    "ahj__oakland_bureau_of_building": "oakland_city",
    "ahj__san_diego_development_services": "san_diego_city",
    "ahj__sacramento_county_building": "sacramento_county",
    "ahj__pleasant_hill": "pleasant_hill_city",
    "ahj__menifee": "menifee_city",
    "ahj__stockton": "stockton_city",
}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(S.LEDGER.read_text())
    panel = S.read_panel()
    reqs = S.read_requirements()

    ahj_rows = [r for r in panel if r["owner_scope"] == "ahj"]
    authorities = {}
    for row in ahj_rows:
        authorities.setdefault(S.slug(row["owner_name"]), row["owner_name"])
    jurisdictions = sorted(authorities)

    # ---- step universe: ledger activities, then steps only a matrix column names
    steps = {}
    for act in ledger["activities"]:
        steps[act["id"]] = {
            "step_id": act["id"],
            "label": act["name"],
            "actor": act.get("actor_id"),
            "stage": act.get("stage"),
            "existence_in_ledger": act.get("existence"),
            "named_in": ["solar_permit_ledger"],
        }
    for step_id, (label, actor) in MATRIX_ONLY_STEPS.items():
        if step_id in steps:
            steps[step_id]["named_in"].append("requirements_matrix")
        else:
            steps[step_id] = {"step_id": step_id, "label": label, "actor": actor,
                              "stage": "review", "existence_in_ledger": None,
                              "named_in": ["requirements_matrix"]}
    for _, _, step_id in MATRIX_QUESTIONS + MATRIX_COUNT_QUESTIONS:
        if "requirements_matrix" not in steps[step_id]["named_in"]:
            steps[step_id]["named_in"].append("requirements_matrix")

    # ---- layer labels
    for step_id, step in steps.items():
        if step_id in STATUTORY_STEPS:
            layer = "statutory"
        elif "requirements_matrix" in step["named_in"] or str(step["actor"]).startswith("ahj__"):
            layer = "administrative-only"
        else:
            layer = "other-party-or-applicant"
        step["layer_label"] = layer

    observations, anchors = [], []
    req_ref_cache = {}

    def matrix_ref(key, column):
        row = reqs[key]
        if key not in req_ref_cache:
            req_ref_cache[key] = S.ref(S.AHJ_REQS, f"line {row['__line__']}")
        base = req_ref_cache[key]
        return {**base, "locator": f"{base['locator']} column {column!r}"}

    # ---- source type 1: the SolarTRACE requirements matrix, by survey wave
    matrix_unanswered = collections.Counter()
    historical = collections.Counter()
    for key in jurisdictions:
        row = reqs.get(key)
        if row is None:
            continue
        for column in MATRIX_HISTORICAL:
            if S.present_flag(row.get(column)) is not None:
                historical[column] += 1
        for wave, column, step_id in MATRIX_QUESTIONS:
            flag = S.present_flag(row.get(column))
            if flag is None:
                matrix_unanswered[column] += 1
                continue          # missing answer is NO reading opportunity
            observations.append({
                "jurisdiction_id": key, "step_id": step_id,
                "source_type": "requirements_matrix", "detected": bool(flag),
                "reviewed_scope": True,
                "unit_id": f"requirements_matrix::{wave}::{key}",
                "dependence_group_id": f"requirements_matrix::{wave}::{key}",
                "evidence_refs": [matrix_ref(key, column)],
            })
        for wave, column, step_id in MATRIX_COUNT_QUESTIONS:
            value = S.count_value(row.get(column))
            if value is None:
                matrix_unanswered[column] += 1
                continue
            observations.append({
                "jurisdiction_id": key, "step_id": step_id,
                "source_type": "requirements_matrix", "detected": bool(value > 0),
                "reviewed_scope": True,
                "unit_id": f"requirements_matrix::{wave}::{key}",
                "dependence_group_id": f"requirements_matrix::{wave}::{key}",
                "evidence_refs": [matrix_ref(key, column)],
            })

    # ---- source type 2: an authority's own documents, reviewed completely
    doc_positive = collections.defaultdict(set)
    for act in ledger["activities"]:
        for evidence_item in act.get("evidence") or []:
            key = DOC_PREFIX_AUTHORITY.get(str(evidence_item.get("doc_id", "")).split("_")[0])
            if key:
                doc_positive[key].add(act["id"])
    ledger_ref = S.ref(S.LEDGER, "activities[]")
    for key, seen in sorted(doc_positive.items()):
        if key not in authorities:
            continue
        for step_id in sorted(steps):
            observations.append({
                "jurisdiction_id": key, "step_id": step_id,
                "source_type": "agency_document", "detected": step_id in seen,
                "reviewed_scope": True,
                "unit_id": f"agency_document::{key}",
                "dependence_group_id": f"agency_document::{key}",
                "evidence_refs": [{**ledger_ref,
                                   "locator": f"activities[] reviewed against {key} documents, step {step_id}"}],
            })

    # ---- source type 3: applicant accounts, and why solar has none
    # The verified solar forum dataset locates a report against authorities as a
    # probability distribution over candidates, not as an identification: its
    # rows carry a candidate weight per authority because the poster names a
    # utility or a region rather than a building department. Turning a weighted
    # candidate set into a detection for one authority would invent evidence, so
    # solar contributes no applicant-account detections and the count is
    # reported rather than quietly omitted.
    forum = json.loads(S.FORUM.read_text())
    forum_rows = forum.get("rows") or []
    forum_note = {
        "rows": len(forum_rows),
        "usable_for_offset": sum(1 for r in forum_rows if r.get("usable_for_offset")),
        "authority_level_rows": sum(1 for r in forum_rows if r.get("entity_level") == "authority"),
        "rows_with_a_single_candidate_authority": sum(
            1 for r in forum_rows if isinstance(r.get("candidates"), dict) and len(r["candidates"]) == 1),
        "used_as_detections": 0,
        "reason": ("Authority attribution in the solar forum data is a candidate weight "
                   "distribution, not an identification. A weighted candidate set is not a "
                   "reading of one authority and is not used as one."),
    }

    # ---- anchors: the panel's own reported timelines, and declared absent ATB
    panel_ref = S.ref(S.PANEL, "panel_v1.csv")
    anchor_seen = set()
    for row in ahj_rows:
        key = S.slug(row["owner_name"])
        step_id = PHASE_ANCHOR.get(row["phase"])
        if step_id is None or (key, step_id) in anchor_seen:
            continue
        if row.get("present") != "true" or row.get("disposition") != "retained_panel_cell":
            continue
        resolution = row.get("pre_install_zero_resolution") or ""
        if resolution == "no_atb_requirement_step_absent":
            present, basis = False, "explicit_absence"
        elif resolution.startswith("unresolved"):
            continue          # the source is ambiguous; do not resolve it here
        else:
            present, basis = True, "explicit_presence"
        anchor_seen.add((key, step_id))
        anchors.append({
            "jurisdiction_id": key, "step_id": step_id,
            "present": present, "basis": basis,
            "unit_id": f"timeline_panel::{key}::{row['phase']}",
            "evidence_refs": [{**panel_ref,
                               "locator": f"owner {row['stable_owner_id']} phase {row['phase']} reported timeline"}],
        })

    # ---- stringency, reported directly as burden and available as a covariate
    stringency = []
    for key in jurisdictions:
        row = reqs.get(key)
        if row is None:
            continue
        stringency.append({
            "jurisdiction_id": key,
            "inspections_required": S.count_value(row.get("Number of Inspections Required")),
            "median_permit_cost_usd": S.count_value(row.get("Median Permit Cost")),
            "structural_review": S.present_flag(row.get("Structural Review Required")),
            "electrical_review": S.present_flag(row.get("Electrical Review Required")),
            "third_party_review": S.present_flag(row.get("Third-Party Permit Review")),
            "rough_in_inspection": S.present_flag(row.get("Rough-In Inspection Required")),
            "same_day_in_person": S.present_flag(row.get("Same Day In-Person Permitting Available")),
            "online_instant_permitting": S.present_flag(row.get("Online Instant Permitting - 2022")),
            "evidence_ref": matrix_ref(key, "stringency block"),
        })

    evidence = {
        "schema_version": "process-occupancy-evidence/1",
        "scope": ("Solar photovoltaic permitting by California authorities having jurisdiction, "
                  "current practice as recorded 2017-2024. Presence of a step in an authority's "
                  "process, not mandatory participation, ordering or case frequency."),
        "opportunity_frame": "reviewed_units_not_selected_for_step_mentions",
        "conditional_independence": "assumed_given_presence_and_source_type_detection",
        "assumption_note": (
            "A missing requirements-matrix answer is no reading opportunity, never a No. "
            "Statewide statutory text is a layer label, not a per-authority detection, because "
            "one sentence of state law is not independent evidence about 440 authorities. "
            "Agency-document non-detections assume the parse reviewed that authority's documents "
            "completely for the activity list; applicant-account non-detections assume only that "
            "the account was read in full, which is weak and is what its detection probability "
            "should absorb. Detection probabilities transported to steps the matrix never asks "
            "about are an assumption, not an estimate."),
        "jurisdictions": jurisdictions,
        "steps": sorted(steps),
        "source_types": ["requirements_matrix", "agency_document", "applicant_account"],
        "source_models": {
            "requirements_matrix": {"detection_beta": [4, 1.5], "false_positive_probability": 0.02},
            "agency_document": {"detection_beta": [2, 2], "false_positive_probability": 0.01},
            "applicant_account": {"detection_beta": [1.2, 4], "false_positive_probability": 0.02},
        },
        "observations": observations,
        "known_presence": anchors,
    }

    (OUT / "occupancy_evidence.json").write_text(json.dumps(evidence))
    with (OUT / "step_universe.jsonl").open("w") as fh:
        for step in sorted(steps.values(), key=lambda s: s["step_id"]):
            fh.write(json.dumps(step, sort_keys=True) + "\n")
    with (OUT / "detections.jsonl").open("w") as fh:
        for row in observations:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with (OUT / "known_presence.jsonl").open("w") as fh:
        for row in anchors:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with (OUT / "stringency_features.jsonl").open("w") as fh:
        for row in stringency:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    per_juris = collections.Counter(o["jurisdiction_id"] for o in observations)
    by_source = collections.Counter(o["source_type"] for o in observations)
    layers = collections.Counter(s["layer_label"] for s in steps.values())
    summary = {
        "jurisdictions": len(jurisdictions),
        "steps_in_universe": len(steps),
        "steps_by_layer": dict(layers),
        "reading_opportunities": len(observations),
        "opportunities_by_source_type": dict(by_source),
        "positive_detections": sum(1 for o in observations if o["detected"]),
        "reviewed_nondetections": sum(1 for o in observations if not o["detected"]),
        "anchors_present": sum(1 for a in anchors if a["present"]),
        "anchors_absent": sum(1 for a in anchors if not a["present"]),
        "authorities_with_no_reading_opportunity": sum(
            1 for j in jurisdictions if per_juris[j] == 0),
        "authorities_with_only_one_source_type": sum(
            1 for j in jurisdictions
            if len({o["source_type"] for o in observations if o["jurisdiction_id"] == j}) == 1),
        "matrix_questions_unanswered": dict(matrix_unanswered),
        "matrix_historical_waves_reported_not_fitted": dict(historical),
        "applicant_accounts": forum_note,
        "authorities_with_their_own_documents": sorted(
            k for k in doc_positive if k in authorities),
        "qualification": (
            "Sparsity is reported before anything is fitted. Most authorities are seen through "
            "the survey alone, so their step posteriors will be driven by pooling rather than by "
            "their own evidence, and the phase 2 held-out test is the check on whether that "
            "pooling is honest."),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    (OUT / "manifest.json").write_text(json.dumps({
        "packet": "solar_phase1",
        "work_order": "docs/2026-09-21-process-structure-posterior-plan.md",
        "inputs": {name: {"path": str(path.relative_to(S.ROOT)), "sha256": S.sha256(path)}
                   for name, path in [("panel", S.PANEL), ("requirements_matrix", S.AHJ_REQS),
                                      ("ledger", S.LEDGER), ("forum", S.FORUM)]},
        "reads_benchmark_truth": False, "reads_generator_specs": False, "network_used": False,
    }, indent=2))
    return summary


def main():
    summary = build()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
