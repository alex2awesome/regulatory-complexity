"""Prepare existing forum evidence for admin comparisons without changing sources.

This is an explicit, inspectable event/clock adapter, not another extractor.
Unknown geography/year stays in the ledger. Candidate crosswalks are working
interpretations, never semantic gold or a claim that a source was re-read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import re

EVENTS = (
    "application_submitted", "application_complete", "permit_issued",
    "construction_start", "final_or_co", "interconnection_submitted", "pto",
    "design_start", "contract_signed", "preapp_meeting", "hoa_approval",
)
# None means that the agreed vocabulary has no faithful event, NOT no burden.
CLOCKS = {
    "contract_to_installation": ("contract_signed", None, False),
    "contract_to_pto": ("contract_signed", "pto", False),
    "deposit_to_installation": (None, None, False),
    "deposit_to_pto": (None, "pto", False),
    "final_inspection_to_interconnection_submission": ("final_or_co", "interconnection_submitted", False),
    "final_inspection_to_pto": ("final_or_co", "pto", False),
    "installation_to_final_inspection": (None, "final_or_co", False),
    "installation_to_interconnection_submission": (None, "interconnection_submitted", False),
    "installation_to_pto": (None, "pto", False),
    "interconnection_submission_to_pto": ("interconnection_submitted", "pto", True),
    "order_to_installation": (None, None, False),
    "order_to_pto": (None, "pto", False),
    "permit_approval_to_installation": ("permit_issued", None, False),
    "permit_submission_to_approval": ("application_submitted", "permit_issued", True),
    "physical_installation_duration": ("construction_start", None, False),
    "first_submission_to_issuance": ("application_submitted", "permit_issued", True),
    # 'Permitting' may include pre-submission work; never force an admin match.
    "reported_permitting_to_issuance": (None, "permit_issued", False),
    "construction_start_to_completion": ("construction_start", None, False),
    "project_process_start_to_completion": (None, None, False),
    "contract_to_permit_submission": ("contract_signed", "application_submitted", False),
    "order_to_permit_submission": (None, "application_submitted", False),
    "contract_to_permit_approval": ("contract_signed", "permit_issued", False),
    "order_to_permit_approval": (None, "permit_issued", False),
    "permit_approval_to_final_inspection": ("permit_issued", "final_or_co", True),
    "permit_issued_to_final_or_co": ("permit_issued", "final_or_co", True),
    "order_to_design": (None, None, False),
    "order_to_cancellation": (None, None, False),
    "provider_selection_duration": (None, None, False),
}
DATE_ALIASES = {
    **{x: x for x in EVENTS},
    "interconnection_application_submitted": "interconnection_submitted",
    "interconnection_application_submission": "interconnection_submitted",
    "utility_application_submitted": "interconnection_submitted",
    "application_submitted_to_utility": "interconnection_submitted",
    "authorization_to_operate": "pto", "permission_to_operate": "pto",
    "pto_received": "pto", "pto_granted": "pto", "pto_approval": "pto",
    "permit_submitted": "application_submitted", "permit_submission": "application_submitted",
    "permit_application_submitted": "application_submitted",
    "first_submission": "application_submitted", "application_submission": "application_submitted",
    "permit_issuance": "permit_issued", "permit_approved": "permit_issued",
    "final_inspection_passed": "final_or_co", "certificate_of_occupancy": "final_or_co",
    "signed_contract": "contract_signed", "contract_signing": "contract_signed",
}
UTILITIES = {
    "pg&e": "PGE", "pacific gas and electric": "PGE",
    "pacific gas & electric": "PGE", "sce": "SCE",
    "southern california edison": "SCE", "southern california edison (sce)": "SCE",
    "sdg&e": "SDGE", "sdge": "SDGE", "san diego gas & electric": "SDGE",
    "san diego gas and electric": "SDGE", "ladwp": "LADWP", "smud": "SMUD",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slug(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def rows_from(path):
    obj = json.loads(Path(path).read_bytes())
    return obj if isinstance(obj, list) else obj["observations"]


def event_dates(row, event):
    """Use explicitly labeled event dates, never the raw post creation time."""
    if event is None:
        return []
    original = row.get("original") or {}
    dates = original.get("supported_event_dates", [])
    if not isinstance(dates, list):
        return []
    result = []
    for item in dates:
        if not isinstance(item, dict):
            continue
        label = item.get("event") or item.get("label", "")
        if DATE_ALIASES.get(slug(label)) != event:
            continue
        raw = str(item.get("date", ""))
        if re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", raw):
            result.append(raw)
    return result


def start_year_candidates(row, start, end):
    starts = event_dates(row, start)
    if starts:
        return sorted({int(x[:4]) for x in starts}), "explicit_start_event_date"
    # A dated completed endpoint plus a bounded elapsed interval can locate the
    # start year. No business-day conversion or post-year imputation is used.
    if row.get("observation_kind") == "completed_interval" and row.get("time_unit") == "calendar_days":
        lo, hi = row.get("lower"), row.get("upper")
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and 0 <= lo <= hi:
            years = set()
            for raw in event_dates(row, end):
                if len(raw) != 10:
                    continue
                try:
                    d = date.fromisoformat(raw)
                    # Date arithmetic discards sub-day precision. Round outward
                    # so an interval crossing New Year does not lose a candidate.
                    a = d - timedelta(days=math.ceil(hi))
                    b = d - timedelta(days=math.floor(lo))
                except (ValueError, OverflowError):
                    continue
                years.update(range(a.year, b.year + 1))
            if years:
                return sorted(years), "derived_from_explicit_end_date_and_reported_bounds"
    return [], "project_start_year_unknown_no_post_year_imputation"


def utility_id(row):
    value = row.get("utility")
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    if key in UTILITIES:
        return UTILITIES[key]
    # Bare PGE can mean Portland General Electric. California support resolves
    # that particular abbreviation, without inventing a county or city.
    if key == "pge" and row.get("geography_scope") in {
        "california_supported_by_parser", "county_candidates_provided"
    }:
        return "PGE"
    return None


def adapt(row, crosswalk):
    effective = dict(row)
    review = crosswalk.get(row["claim_id"])
    role = "inherited_adopted_clock"
    if review:
        role = "working_crosswalk_candidate_not_semantic_gold"
        effective["clock_crosswalk"] = review
        category = review["category"]
        if category in {"declared", "other_process_interval"} and review.get("target_clock"):
            effective["clock"] = review["target_clock"]
            effective["eligible_for_shared_clock_fit"] = True
            effective["clock_pooling_status"] = role
        else:
            effective["eligible_for_shared_clock_fit"] = False
    clock = effective.get("clock")
    start, end, admin = CLOCKS.get(clock, (None, None, False))
    original = row.get("original") or {}
    for key in ("start_event", "end_event"):
        value = original.get(key)
        if value in EVENTS:
            if key == "start_event":
                start = value
            else:
                end = value
    effective.update(start_event=start, end_event=end)
    # An explicit boundary can override a clock label. Do not keep a misleading
    # admin equivalence when those boundaries disagree with the registry.
    if admin and (start, end) != CLOCKS[clock][:2]:
        admin = False
    effective["admin_clock_covered_in_principle"] = admin
    effective["interpretation_role"] = role
    effective["endpoint_note"] = "Null preserves unknown/out-of-vocabulary boundaries; physical installation completion is not final inspection."
    if admin:
        effective["model_role"] = "admin_comparison_candidate_not_forum_population_anchor"
    else:
        effective["model_role"] = "forum_burden_or_uncovered_clock"
    return effective


def comparison(row, domain):
    start, end = row.get("start_event"), row.get("end_event")
    years, year_basis = start_year_candidates(row, start, end)
    reading = row.get("cell_key_reading") or {}
    if not years and reading.get("start_year_candidates"):
        years = reading["start_year_candidates"]
        year_basis = "existing_context_reading_with_retained_assumptions_not_exact_event_dates"
    utility = utility_id(row)
    jurisdiction = row.get("jurisdiction_as_coded")
    if jurisdiction is None and isinstance(row.get("location"), dict):
        jurisdiction = row["location"].get("jurisdiction") or row["location"].get("city")
    jurisdictions = reading.get("jurisdiction_candidates") or ([jurisdiction] if jurisdiction else [])
    interconnection = start == "interconnection_submitted" and end == "pto"
    missing = []
    if not row.get("eligible_for_shared_clock_fit", True):
        missing.append("nonprocess_or_unresolved_interpretation")
    if not row["admin_clock_covered_in_principle"]:
        missing.append("not_an_admin_clock_equivalence")
    if not years:
        missing.append("start_year_unknown")
    elif not any(2017 <= y <= 2025 for y in years):
        missing.append("outside_2017_2025_window")
    if interconnection and not utility:
        missing.append("utility_unresolved")
    elif not interconnection and not jurisdictions:
        missing.append("jurisdiction_unresolved_county_not_substituted")
    return {
        "claim_id": row["claim_id"], "domain": domain,
        "clock": row.get("clock"), "start_event": start, "end_event": end,
        "utility_id": utility, "utility_as_coded": row.get("utility"),
        "jurisdiction_as_coded": jurisdiction, "location_as_coded": row.get("location"),
        "jurisdiction_candidates": jurisdictions,
        "county_weights": row.get("county_weights"),
        "unassigned_geography_mass": row.get("unassigned_geography_mass"),
        "start_year_candidates": years, "year_basis": year_basis,
        "end_year_candidates": reading.get("end_year_candidates", []),
        "cell_key_reading": reading or None,
        "cell_assignment_status": "working_candidates_not_bound_no_invented_weights",
        "observation_kind": row.get("observation_kind"),
        "lower": row.get("lower"), "upper": row.get("upper"), "time_unit": row.get("time_unit"),
        "contributor_group": row.get("contributor_group"),
        "cell_keys_ready": not missing, "missing_or_incompatible": missing,
        "admin_match_status": "awaiting_admin_cohorts",
        "retention": "retained_even_when_not_calibration_eligible",
        "interpretation_role": row["interpretation_role"],
    }


def prepare(observations, out, crosswalk=None, domain="solar", cell_readings=None):
    source = rows_from(observations)
    reviews = {} if crosswalk is None else {
        r["claim_id"]: r for r in map(json.loads, Path(crosswalk).read_text().splitlines())
    }
    if len({r["claim_id"] for r in source}) != len(source):
        raise ValueError("Duplicate source claim ids")
    if set(reviews) - {r["claim_id"] for r in source}:
        raise ValueError("Crosswalk refers to a claim outside the input snapshot")
    cell_rows = [] if cell_readings is None else json.loads(Path(cell_readings).read_text())
    readings = {r["claim_id"]: r for r in cell_rows}
    if len(readings) != len(cell_rows) or set(readings) - {r["claim_id"] for r in source}:
        raise ValueError("Duplicate or unknown cell-reading claim ids")
    effective = [adapt(r, reviews) for r in source]
    for row in effective:
        if row["claim_id"] in readings:
            row["cell_key_reading"] = readings[row["claim_id"]]
    comparisons = [comparison(r, domain) for r in effective]
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    (out / "observations.json").write_text(json.dumps(effective, ensure_ascii=False) + "\n")
    (out / "comparison_candidates.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in comparisons))
    summary = {
        "schema_version": "forum-admin-comparison-preparation/1", "domain": domain,
        "input": str(observations), "input_sha256": sha(observations),
        "crosswalk": None if crosswalk is None else str(crosswalk),
        "crosswalk_sha256": None if crosswalk is None else sha(crosswalk),
        "cell_readings": None if cell_readings is None else str(cell_readings),
        "cell_readings_sha256": None if cell_readings is None else sha(cell_readings),
        "code_sha256": sha(__file__), "input_claims": len(source), "retained_claims": len(effective),
        "clock_counts": dict(Counter(r.get("clock") for r in effective)),
        "admin_clock_candidates": sum(r["admin_clock_covered_in_principle"] and r.get("eligible_for_shared_clock_fit", True) for r in effective),
        "cell_keys_ready": sum(r["cell_keys_ready"] for r in comparisons),
        "missing_or_incompatible": dict(Counter(x for r in comparisons for x in r["missing_or_incompatible"])),
        "source_quotes_reverified": False, "new_fits": 0,
        "assumptions": [
            "Crosswalk labels are working Gemma/Luna interpretations, not calibrated semantic gold.",
            "Admin-covered clocks are reserved for admin anchoring and source comparisons; these are not new population timing estimates.",
            "Unknown geography/year stays in evidence; no county-to-city or post-year-to-project-year imputation.",
            "Contextual cell readings can carry existing explicit assumptions; ready means candidate keys exist, not a verified admin match.",
            "Forum/admin case overlap will be treated as negligible when cohorts arrive, not asserted absent.",
            "A source indicator alone cannot identify San Jose survivor selection without an anchor or selection assumptions.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "event_clock_registry.json").write_text(json.dumps({"events": EVENTS, "clocks": CLOCKS}, indent=2) + "\n")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observations", type=Path, required=True)
    p.add_argument("--crosswalk", type=Path)
    p.add_argument("--cell-readings", type=Path)
    p.add_argument("--domain", choices=["solar", "adu"], default="solar")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    s = prepare(a.observations, a.out, a.crosswalk, a.domain, a.cell_readings)
    print(json.dumps({k: s[k] for k in ("domain", "input_claims", "retained_claims", "admin_clock_candidates", "cell_keys_ready")}, indent=2))


if __name__ == "__main__":
    main()
