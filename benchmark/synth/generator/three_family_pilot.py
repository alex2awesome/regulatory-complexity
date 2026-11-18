"""Build the fictional CCW and CalFresh counterparts for the three-family pilot.

This is a *construction* generator, not an extractor or an inference driver.  It
uses the existing semantic-path RNG and typed lineage records, generates cases
before summaries, and writes renderer inputs rather than rendered prose.  All
rates are declared design assumptions; none is presented as empirical
calibration.

The boundary is intentionally visible in the directory layout::

    public/                 renderer-visible specifications and contexts
    private/truth/          process, case, and summary truth
    private/provenance/     source links and planted reporting mechanisms
    private/evaluation/     split assignments and information ceilings

Extractors and fitters may receive rendered artifacts later.  They must never
receive this generator, ``public/render_specs`` (which are renderer directives),
or anything under ``private``.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import pathlib
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, Iterable

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "benchmark.synth.generator"

from .lineage import COPIED_TEXT, SAME_CASE, SAME_COHORT, independence_report, link
from .rng import chance, quantile, sample_days, sub_rng, weighted


WORLD_ID = "THREE_FAMILY_PILOT_003"
GENERATOR_VERSION = "three-family-pilot/3"
SEED = 20260920
N_JURISDICTIONS = 12
N_EPISODES = 1000
MONTHS = tuple(
    f"{year:04d}-{month:02d}"
    for year, month in ((2024 + (8 + i) // 12, (8 + i) % 12 + 1) for i in range(24))
)
WINDOW_START = "2024-09-01"
WINDOW_END = "2026-08-31"
AS_OF = "2026-09-01"
SPLITS = ("calibration",) * 4 + ("development",) * 4 + ("reserved",) * 4

CCW_NAMES = (
    "Alderwick", "Bellweather", "Cairn Harbor", "Dunlin", "Eastmere", "Fox Hollow",
    "Gannet Ridge", "Hearthstone", "Ivory Wash", "Juniper Vale", "Kestrel", "Larkspur Bend",
)
CALFRESH_NAMES = (
    "Morrowfield", "Northglass", "Orchard Run", "Peregrine", "Quarry Lake", "Redfern",
    "Stillwater", "Thistle Bay", "Umber Plains", "Verdant", "Westbarrow", "Yarrow",
)

CCW_STAGES = (
    "application_received", "interview", "background_check", "training_review",
    "decision", "credential_pickup",
)
CALFRESH_STAGES = (
    "application_received", "eligibility_discovery", "interview", "verification",
    "decision", "benefit_issuance",
)

# Frozen before any episode draw.  Variation by jurisdiction is a deterministic
# part of the design, not a fitted or empirically calibrated parameter.
CCW_PROFILES = (
    (0.72, 0.82), (0.66, 1.08), (0.78, 1.34), (0.61, 0.94),
    (0.74, 1.55), (0.69, 0.73), (0.76, 1.18), (0.64, 1.43),
    (0.81, 0.88), (0.70, 1.27), (0.67, 1.67), (0.79, 1.01),
)  # (initial share, speed multiplier)
CALFRESH_PROFILES = (
    (0.18, 0.78), (0.24, 1.12), (0.29, 1.38), (0.20, 0.91),
    (0.26, 1.52), (0.16, 0.70), (0.31, 1.20), (0.22, 1.43),
    (0.19, 0.86), (0.27, 1.29), (0.23, 1.61), (0.17, 1.00),
)  # (expedited share, speed multiplier)

CCW_ARTIFACT_KINDS = (
    "program_overview", "initial_application_guide", "renewal_guide",
    "interview_and_pickup_guide", "training_provider_page", "fee_schedule",
    "monthly_performance_table", "typical_time_faq", "forum_thread", "news_summary",
)
CALFRESH_ARTIFACT_KINDS = (
    "program_overview", "application_guide", "expedited_service_guide",
    "interview_guide", "verification_checklist", "issuance_guide",
    "receipt_cohort_workbook", "completion_cohort_dashboard",
    "schema_change_notice", "applicant_forum",
)
SHARED_KINDS = {
    "ccw": ("fictional_state_framework", "training_provider_standard", "statewide_annual_report"),
    "calfresh": ("fictional_policy_manual", "cohort_data_dictionary", "statewide_annual_report"),
}

FORBIDDEN_PUBLIC_KEYS = {
    "case_id", "cohort_id", "source_id", "truth", "split", "planned_outcome",
    "delay_attribution", "private_provenance", "lineage",
}

BOUNDARY_TEXT = """# THREE_FAMILY_PILOT_003 construction boundary

This bundle is a generator-stage product. `public/render_specs/` contains
structured directives for a later renderer, not prose artifacts and not an
extractor packet. `public/render_context/` contains only fictional public names
and renderer constraints. Even though these inputs describe what a public
artifact may eventually say, extractors and fitters must not receive them.

Everything under `private/` is generator/evaluator material. It contains case
and process truth, cohort summaries, planted reporting mechanisms, dependence
lineage, split assignments, and ceilings. Reserved truth remains locked until
the evaluation protocol and all inputs are frozen.

No prose corpus, verification verdict, extraction ledger, fit input, posterior,
or score is included. All stochastic parameters are fictional design
assumptions and have no claimed empirical calibration.
"""


def _iso_day(s: str) -> date:
    return date.fromisoformat(s)


def _day(s: str, n: int) -> str:
    return (_iso_day(s) + timedelta(days=n)).isoformat()


def _month(s: str) -> str:
    return s[:7]


def _json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_json(path: pathlib.Path, obj: Any, *, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                               indent=2 if pretty else None) + "\n", encoding="utf-8")


def _write_jsonl(path: pathlib.Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_json_bytes(row) for row in rows))


def _write_jsonl_gz(path: pathlib.Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(_json_bytes(row) for row in rows)
    path.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))


def _sha256(obj: Any) -> str:
    return hashlib.sha256(_json_bytes(obj)).hexdigest()


def _jurisdictions() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"ccw": [], "calfresh": []}
    for family, names, prefix, profiles in (
        ("ccw", CCW_NAMES, "CCW", CCW_PROFILES),
        ("calfresh", CALFRESH_NAMES, "CF", CALFRESH_PROFILES),
    ):
        for i, (name, profile) in enumerate(zip(names, profiles), 1):
            jid = f"{prefix}_J{i:02d}"
            common = {
                "id": jid, "name": f"{name} County", "state": "Aurelia (fictional)",
                "family": family, "profile_index": i - 1,
                "public_host": f"www.{name.lower().replace(' ', '').replace("'", '')}.aur.gov",
            }
            if family == "ccw":
                common.update({
                    "initial_share": profile[0], "speed_multiplier": profile[1],
                    "issuer": (f"{name} County Sheriff, Licensing Division" if i % 3
                               else f"{name} Department of Public Safety, Permit Bureau"),
                    "operator": (f"CivicPermit {chr(64 + (i % 3 or 3))}" if i % 2 else
                                 f"{name} County Licensing Counter"),
                    "training_provider": f"Aurelia Certified Safety Network Region {(i - 1) % 4 + 1}",
                    "fingerprint_provider": (f"{name} Records Unit" if i % 2 else
                                             "Aurelia Identity Services Cooperative"),
                    "vendor_template": f"CCW_VENDOR_{(i - 1) % 3 + 1}",
                })
            else:
                common.update({
                    "expedited_share": profile[0], "speed_multiplier": profile[1],
                    "agency": f"{name} County Human Support Agency",
                    "operator": f"Aurelia Benefits Consortium {(i - 1) % 3 + 1}",
                    "issuance_provider": ("Aurelia EBT Services" if i % 4 else
                                          "CommonGood Benefit Payments"),
                    "consortium_template": f"BENEFITS_CONSORTIUM_{(i - 1) % 3 + 1}",
                    "report_gap_months": [MONTHS[(i * 5) % 24]] + ([MONTHS[(i * 5 + 11) % 24]] if i % 4 == 0 else []),
                })
            out[family].append(common)
    return out


def frozen_design(seed: int = SEED) -> tuple[dict, dict]:
    """Return configuration and split assignment without consuming an RNG draw."""
    jurisdictions = _jurisdictions()
    config = {
        "world_id": WORLD_ID, "generator_version": GENERATOR_VERSION, "seed": seed,
        "families": ["ccw", "calfresh"], "jurisdictions_per_family": N_JURISDICTIONS,
        "episodes_per_jurisdiction": N_EPISODES, "months": list(MONTHS),
        "window": {"start": WINDOW_START, "end": WINDOW_END, "as_of": AS_OF},
        "split_counts_per_family": {"calibration": 4, "development": 4, "reserved": 4},
        "artifact_quota": {"per_jurisdiction_max": 12, "shared_per_family_max": 3},
        "generation_order": ["freeze_config", "freeze_split", "episodes", "summaries", "render_specs", "ceilings"],
        "parameter_basis": "design_assumption",
        "empirical_calibration": None,
        "assumption_notice": (
            "All route, outcome, duration, selection, suppression, and reporting parameters are "
            "fictional design assumptions. They are not estimates of any real jurisdiction or program."
        ),
        "route_and_outcome_shares_frozen": True,
        "successor_repairs": [
            "Only events completed by the cutoff are observed; an active stage is represented separately as right-censored.",
            "Withdrawal checkpoint is drawn once and cannot be the decision stage.",
            "Decision and fulfillment statuses and clocks are distinct.",
            "The CCW renewal route omits interview, matching its complete public stage inventory.",
            "CalFresh approval clocks name application or service-clock origins; issuance is application-origin.",
            "CalFresh published timing rows are stratified by route and clock origin.",
            "Latent and observed CalFresh service-clock origins are derived from retained and completed paths.",
            "Latent and observed repeat counts are derived from their corresponding paths.",
            "Completed denials have an observed application-to-denial endpoint in forum directives.",
        ],
        "routes": {
            "ccw": {"initial_share_by_jurisdiction": [p[0] for p in CCW_PROFILES],
                    "planned_outcome_weights": {"initial": {"approved": .76, "denied": .08, "withdrawn": .07, "pending": .09},
                                                "renewal": {"approved": .86, "denied": .04, "withdrawn": .05, "pending": .05}}},
            "calfresh": {"expedited_share_by_jurisdiction": [p[0] for p in CALFRESH_PROFILES],
                         "expedited_origin_weights": {"application": .45, "eligibility_discovery": .55},
                         "planned_outcome_weights": {"approved": .78, "denied": .12, "withdrawn": .05, "pending": .05}},
        },
        "construction_scope": {
            "structured_render_specs": True, "rendered_prose_artifacts": False,
            "independent_verification": False, "extraction_ledgers": False,
            "fit_inputs": False, "scores": False,
        },
    }
    split = {
        "world_id": WORLD_ID, "frozen_before_draws": True,
        "assignment_rule": "ordered fictional IDs: first 4 calibration, next 4 development, last 4 reserved",
        "families": {
            family: {j["id"]: SPLITS[i] for i, j in enumerate(jurisdictions[family])}
            for family in ("ccw", "calfresh")
        },
        "access_rule": (
            "Reserved truth is evaluator-only and remains locked until public inputs, code, priors, "
            "prompts, and evaluation protocol are frozen."
        ),
    }
    _validate_freeze(config, split, jurisdictions)
    return config, split


def _validate_freeze(config: dict, split: dict, jurisdictions: dict[str, list[dict]]) -> None:
    assert config["jurisdictions_per_family"] == 12
    assert config["episodes_per_jurisdiction"] == 1000
    assert len(config["months"]) == 24 and len(set(config["months"])) == 24
    for family in ("ccw", "calfresh"):
        assert len(jurisdictions[family]) == 12
        assert Counter(split["families"][family].values()) == {"calibration": 4, "development": 4, "reserved": 4}
    assert config["artifact_quota"] == {"per_jurisdiction_max": 12, "shared_per_family_max": 3}
    assert config["empirical_calibration"] is None


def _event(stage: str, start: int, duration: int, origin: str, *, visit: int = 1) -> dict:
    return {"stage": stage, "visit_index": visit, "start_day": start,
            "end_day": start + duration, "duration_days": duration, "clock_origin": origin}


def _choice(rng, weights: dict[str, float]) -> str:
    return weighted(rng, list(weights.items()))


def _observed_path(latent_path: list[dict], cutoff: int) -> tuple[list[dict], dict | None]:
    """Project latent mechanics onto information available at the fixed cutoff."""
    observed = [dict(event) for event in latent_path if event["end_day"] <= cutoff]
    active = next((event for event in latent_path
                   if event["start_day"] <= cutoff < event["end_day"]), None)
    if active is None:
        return observed, None
    return observed, {
        "stage": active["stage"], "visit_index": active["visit_index"],
        "start_day": active["start_day"], "observed_through_day": cutoff,
        "elapsed_lower_bound_days": cutoff - active["start_day"],
        "status": "right_censored",
    }


def _force_pending_at_cutoff(rng, latent_path: list[dict], cutoff: int) -> None:
    """Plant a still-open stage without inventing its eventual outcome."""
    candidates = [i for i, event in enumerate(latent_path)
                  if event["stage"] not in {"application_received", "decision",
                                             "credential_pickup", "benefit_issuance"}]
    if not candidates:
        return
    chosen = candidates[rng.randrange(len(candidates))]
    event = latent_path[chosen]
    if event["start_day"] <= cutoff:
        event["end_day"] = max(event["end_day"], cutoff + 1 + rng.randrange(30))
        event["duration_days"] = event["end_day"] - event["start_day"]
    # A planted pending case has no latent decision or fulfillment endpoint.
    del latent_path[chosen + 1:]


def _repeat_counts(latent_path: list[dict], observed_path: list[dict]) -> tuple[int, int]:
    return (sum(e["visit_index"] > 1 for e in latent_path),
            sum(e["visit_index"] > 1 for e in observed_path))


def _calfresh_service_clock_state(latent_path: list[dict], observed_path: list[dict],
                                   app_day: int) -> dict:
    latent_discovery = next((e for e in latent_path
                             if e["stage"] == "eligibility_discovery"), None)
    observed_discovery = next((e for e in observed_path
                               if e["stage"] == "eligibility_discovery"), None)
    return {
        "latent_service_clock_origin": ("eligibility_discovery" if latent_discovery
                                         else "application"),
        "latent_service_clock_origin_day": (latent_discovery["end_day"]
                                             if latent_discovery else app_day),
        "observed_service_clock_origin": ("eligibility_discovery" if observed_discovery else
                                          "application" if latent_discovery is None else None),
        "observed_service_clock_origin_day": (observed_discovery["end_day"] if observed_discovery else
                                              app_day if latent_discovery is None else None),
    }


def _generate_ccw_cases(seed: int, jur: dict) -> tuple[list[dict], dict]:
    cases: list[dict] = []
    start = _iso_day(WINDOW_START)
    cutoff = (_iso_day(WINDOW_END) - start).days
    for n in range(N_EPISODES):
        rng = sub_rng(seed, "three_family_pilot", "ccw", jur["id"], "episode", n)
        app_day = rng.randrange(cutoff + 1)
        app_date = (start + timedelta(days=app_day)).isoformat()
        route = "initial" if chance(rng, jur["initial_share"]) else "renewal"
        outcome_weights = ({"approved": .76, "denied": .08, "withdrawn": .07, "pending": .09}
                           if route == "initial" else
                           {"approved": .86, "denied": .04, "withdrawn": .05, "pending": .05})
        planned = _choice(rng, outcome_weights)
        speed = jur["speed_multiplier"] * (1.0 if route == "initial" else .72)
        durations = {
            "interview": sample_days(rng, 9 * speed, 31 * speed),
            "background_check": sample_days(rng, 18 * speed, 61 * speed),
            "training_review": sample_days(rng, 5 * speed, 19 * speed),
            "decision": sample_days(rng, 12 * speed, 48 * speed),
            "credential_pickup": sample_days(rng, 4 * speed, 16 * speed),
        }
        latent_path = [_event("application_received", app_day, 0, "application")]
        cursor = app_day
        stages = (["interview", "background_check", "training_review", "decision"]
                  if route == "initial" else ["background_check", "training_review", "decision"])
        withdrawal_after_stage = None
        if planned == "withdrawn":
            eligible = [stage for stage in stages if stage != "decision"]
            withdrawal_after_stage = weighted(
                rng, [(stage, {"interview": 3, "background_check": 2,
                                "training_review": 1}[stage]) for stage in eligible])
        for stage in stages:
            dur = durations[stage]
            latent_path.append(_event(stage, cursor, dur, "application"))
            cursor += dur
            p_repeat = {"interview": .07, "background_check": .04, "training_review": .13, "decision": 0}[stage]
            if chance(rng, p_repeat):
                redur = sample_days(rng, max(1, dur * .35), max(2, dur * .75))
                latent_path.append(_event(stage, cursor, redur, "application", visit=2))
                cursor += redur
            if stage == withdrawal_after_stage:
                break
        if planned == "approved" and latent_path[-1]["stage"] == "decision":
            dur = durations["credential_pickup"]
            latent_path.append(_event("credential_pickup", cursor, dur, "application"))
        if planned == "pending":
            _force_pending_at_cutoff(rng, latent_path, cutoff)
        observed_path, in_progress = _observed_path(latent_path, cutoff)
        latent_repeat_count, observed_repeat_count = _repeat_counts(latent_path, observed_path)
        decision = next((e for e in observed_path if e["stage"] == "decision"), None)
        pickup = next((e for e in observed_path if e["stage"] == "credential_pickup"), None)
        withdrawal_observed = (withdrawal_after_stage is not None and
                               any(e["stage"] == withdrawal_after_stage for e in observed_path) and
                               in_progress is None)
        if decision is not None:
            decision_status, decision_outcome = "completed", planned
        elif withdrawal_observed:
            decision_status, decision_outcome = "withdrawn", "withdrawn"
        else:
            decision_status, decision_outcome = "pending", None
        if decision_outcome == "approved":
            fulfillment_status = "completed" if pickup is not None else "pending"
        elif decision_outcome in {"denied", "withdrawn"}:
            fulfillment_status = "not_applicable"
        else:
            fulfillment_status = "not_reached"
        cases.append({
            "case_id": f"{jur['id']}-C{n + 1:04d}", "family": "ccw", "jurisdiction_id": jur["id"],
            "application_date": app_date, "receipt_cohort": _month(app_date), "route": route,
            "planned_outcome": planned, "withdrawal_after_stage": withdrawal_after_stage,
            "decision_status": decision_status, "decision_outcome": decision_outcome,
            "decision_right_censored": decision_status == "pending",
            "fulfillment_status": fulfillment_status,
            "fulfillment_right_censored": fulfillment_status == "pending",
            "issuer": jur["issuer"], "application_operator": jur["operator"],
            "training_provider": jur["training_provider"], "fingerprint_provider": jur["fingerprint_provider"],
            "latent_repeat_count": latent_repeat_count,
            "observed_repeat_count": observed_repeat_count,
            "latent_eventual_path": latent_path,
            "observed_path": observed_path, "in_progress_event": in_progress,
            "decision_days_from_application": decision["end_day"] - app_day if decision else None,
            "pickup_days_from_application": pickup["end_day"] - app_day if pickup else None,
        })
    process = {
        "family": "ccw", "jurisdiction_id": jur["id"], "routes": ["initial", "renewal"],
        "route_stage_inventory": {
            "initial": list(CCW_STAGES),
            "renewal": ["application_received", "background_check", "training_review",
                        "decision", "credential_pickup"],
        }, "organizations": {
            "issuer": jur["issuer"], "application_operator": jur["operator"],
            "training_provider": jur["training_provider"], "fingerprint_provider": jur["fingerprint_provider"],
        },
        "organization_distinctions": ["issuer != training_provider", "issuer may differ from application_operator",
                                      "fingerprint_provider may differ from issuer"],
        "duration_basis": "fictional design assumption",
        "successor_design_repair": "renewal interview removed to match the complete public renewal inventory",
        "hidden_fields": ["staff_hours", "internal_queue_priority"],
    }
    _validate_cases(cases, "ccw", jur["id"])
    return cases, process


def _generate_calfresh_cases(seed: int, jur: dict) -> tuple[list[dict], dict]:
    cases: list[dict] = []
    start = _iso_day(WINDOW_START)
    cutoff = (_iso_day(WINDOW_END) - start).days
    for n in range(N_EPISODES):
        rng = sub_rng(seed, "three_family_pilot", "calfresh", jur["id"], "episode", n)
        app_day = rng.randrange(cutoff + 1)
        app_date = (start + timedelta(days=app_day)).isoformat()
        route = "expedited" if chance(rng, jur["expedited_share"]) else "normal"
        origin = (_choice(rng, {"application": .45, "eligibility_discovery": .55})
                  if route == "expedited" else "application")
        planned = _choice(rng, {"approved": .78, "denied": .12, "withdrawn": .05, "pending": .05})
        speed = jur["speed_multiplier"] * (.45 if route == "expedited" else 1.0)
        latent_path = [_event("application_received", app_day, 0, "application")]
        cursor = app_day
        if origin == "eligibility_discovery":
            discovery_delay = rng.randrange(0, 3)
            latent_path.append(_event("eligibility_discovery", cursor, discovery_delay,
                                      "eligibility_discovery"))
            cursor += discovery_delay
        withdrawal_after_stage = (weighted(rng, [("interview", 3), ("verification", 2)])
                                  if planned == "withdrawn" else None)
        for stage, med, p90, repeat_p in (
            ("interview", 4, 12, .10), ("verification", 5, 18, .16), ("decision", 6, 24, 0),
        ):
            dur = sample_days(rng, max(.3, med * speed), max(.8, p90 * speed))
            latent_path.append(_event(stage, cursor, dur, origin))
            cursor += dur
            if chance(rng, repeat_p):
                redur = sample_days(rng, max(.3, dur * .4), max(.8, dur * .9))
                latent_path.append(_event(stage, cursor, redur, origin, visit=2))
                cursor += redur
            if stage == withdrawal_after_stage:
                break
        if planned == "approved" and latent_path[-1]["stage"] == "decision":
            dur = sample_days(rng, max(.2, 1.5 * speed), max(.7, 5 * speed))
            latent_path.append(_event("benefit_issuance", cursor, dur, origin))
        if planned == "pending":
            _force_pending_at_cutoff(rng, latent_path, cutoff)
        observed_path, in_progress = _observed_path(latent_path, cutoff)
        latent_repeat_count, observed_repeat_count = _repeat_counts(latent_path, observed_path)
        clock_state = _calfresh_service_clock_state(latent_path, observed_path, app_day)
        decision = next((e for e in observed_path if e["stage"] == "decision"), None)
        issuance = next((e for e in observed_path if e["stage"] == "benefit_issuance"), None)
        withdrawal_observed = (withdrawal_after_stage is not None and
                               any(e["stage"] == withdrawal_after_stage for e in observed_path) and
                               in_progress is None)
        if decision is not None:
            decision_status, decision_outcome = "completed", planned
        elif withdrawal_observed:
            decision_status, decision_outcome = "withdrawn", "withdrawn"
        else:
            decision_status, decision_outcome = "pending", None
        if decision_outcome == "approved":
            fulfillment_status = "completed" if issuance is not None else "pending"
        elif decision_outcome in {"denied", "withdrawn"}:
            fulfillment_status = "not_applicable"
        else:
            fulfillment_status = "not_reached"
        decision_end = decision["end_day"] if decision else None
        issue_end = issuance["end_day"] if issuance else None
        approval_from_application = decision_end - app_day if decision_outcome == "approved" else None
        service_clock_day = (clock_state["observed_service_clock_origin_day"]
                             if decision_outcome == "approved" else None)
        approval_from_service_clock = (decision_end - service_clock_day
                                       if decision_outcome == "approved" else None)
        delay_attr = None
        if approval_from_application is not None and approval_from_application > 30:
            delay_attr = _choice(rng, {"county": .45, "applicant": .35, "third_party": .20})
        cases.append({
            "case_id": f"{jur['id']}-C{n + 1:04d}", "family": "calfresh", "jurisdiction_id": jur["id"],
            "application_date": app_date, "receipt_cohort": _month(app_date), "route": route,
            **clock_state,
            "planned_outcome": planned, "withdrawal_after_stage": withdrawal_after_stage,
            "decision_status": decision_status, "decision_outcome": decision_outcome,
            "decision_right_censored": decision_status == "pending",
            "fulfillment_status": fulfillment_status,
            "fulfillment_right_censored": fulfillment_status == "pending", "agency": jur["agency"],
            "application_operator": jur["operator"], "issuance_provider": jur["issuance_provider"],
            "latent_repeat_count": latent_repeat_count,
            "observed_repeat_count": observed_repeat_count,
            "latent_eventual_path": latent_path,
            "observed_path": observed_path, "in_progress_event": in_progress,
            "decision_days_from_application": decision_end - app_day if decision_end is not None else None,
            "approval_days_from_application": approval_from_application,
            "approval_days_from_service_clock": approval_from_service_clock,
            "approval_service_clock_origin": (clock_state["observed_service_clock_origin"]
                                               if decision_outcome == "approved" else None),
            "issuance_days_from_application": issue_end - app_day if issue_end is not None else None,
            "decision_to_issuance_days": issue_end - decision_end if issue_end is not None else None,
            "completion_cohort": _month(_day(WINDOW_START, decision_end)) if decision_end is not None else None,
            "delay_attribution": delay_attr,
        })
    process = {
        "family": "calfresh", "jurisdiction_id": jur["id"], "routes": ["normal", "expedited"],
        "approval_clock_origins": ["application", "eligibility_discovery"],
        "issuance_clock_origin": "application", "stages": list(CALFRESH_STAGES),
        "organizations": {"agency": jur["agency"], "application_operator": jur["operator"],
                          "issuance_provider": jur["issuance_provider"]},
        "organization_distinctions": ["agency may differ from application_operator",
                                      "agency != issuance_provider"],
        "duration_basis": "fictional design assumption", "hidden_fields": ["staff_hours", "internal_queue_priority"],
    }
    _validate_cases(cases, "calfresh", jur["id"])
    return cases, process


def _validate_cases(cases: list[dict], family: str, jid: str) -> None:
    assert len(cases) == N_EPISODES and len({c["case_id"] for c in cases}) == N_EPISODES
    assert {c["family"] for c in cases} == {family} and {c["jurisdiction_id"] for c in cases} == {jid}
    assert {c["decision_outcome"] for c in cases} >= {"approved", "denied", "withdrawn", None}
    assert any(c["latent_repeat_count"] for c in cases)
    for case in cases:
        assert WINDOW_START <= case["application_date"] <= WINDOW_END
        ends = [e["end_day"] for e in case["latent_eventual_path"]]
        starts = [e["start_day"] for e in case["latent_eventual_path"]]
        assert all(e >= s >= 0 for s, e in zip(starts, ends))
        assert all(starts[i] >= ends[i - 1] for i in range(1, len(starts)))
        assert case["latent_repeat_count"] == sum(
            e["visit_index"] > 1 for e in case["latent_eventual_path"])
        assert case["observed_repeat_count"] == sum(
            e["visit_index"] > 1 for e in case["observed_path"])
        assert case["observed_repeat_count"] <= case["latent_repeat_count"]
        assert all(e["end_day"] <= (_iso_day(WINDOW_END) - _iso_day(WINDOW_START)).days
                   for e in case["observed_path"])
        if case["in_progress_event"]:
            assert set(case["in_progress_event"]) == {
                "stage", "visit_index", "start_day", "observed_through_day",
                "elapsed_lower_bound_days", "status",
            }
            assert case["in_progress_event"]["status"] == "right_censored"
        if case["planned_outcome"] == "withdrawn":
            assert case["withdrawal_after_stage"] != "decision"
            assert not any(e["stage"] == "decision" for e in case["latent_eventual_path"])
        if family == "ccw":
            if case["route"] == "renewal":
                assert not any(e["stage"] == "interview" for e in case["latent_eventual_path"])
            assert (case["decision_days_from_application"] is not None) == (case["decision_status"] == "completed")
            assert (case["pickup_days_from_application"] is not None) == (case["fulfillment_status"] == "completed")
        else:
            app_day = (_iso_day(case["application_date"]) - _iso_day(WINDOW_START)).days
            latent_discovery = next((e for e in case["latent_eventual_path"]
                                     if e["stage"] == "eligibility_discovery"), None)
            observed_discovery = next((e for e in case["observed_path"]
                                       if e["stage"] == "eligibility_discovery"), None)
            assert case["latent_service_clock_origin"] == (
                "eligibility_discovery" if latent_discovery else "application")
            assert case["latent_service_clock_origin_day"] == (
                latent_discovery["end_day"] if latent_discovery else app_day)
            assert case["observed_service_clock_origin"] == (
                "eligibility_discovery" if observed_discovery else
                "application" if latent_discovery is None else None)
            assert case["observed_service_clock_origin_day"] == (
                observed_discovery["end_day"] if observed_discovery else
                app_day if latent_discovery is None else None)
            assert (case["decision_days_from_application"] is not None) == (case["decision_status"] == "completed")
            assert (case["approval_days_from_application"] is not None) == (case["decision_outcome"] == "approved")
            assert (case["issuance_days_from_application"] is not None) == (case["fulfillment_status"] == "completed")
            if case["approval_days_from_application"] is not None:
                assert case["approval_service_clock_origin"] == case["observed_service_clock_origin"]
                delta = case["observed_service_clock_origin_day"] - app_day
                assert case["approval_days_from_application"] == case["approval_days_from_service_clock"] + delta


def _cell(value: Any, *, suppress: bool = False) -> dict:
    if suppress and isinstance(value, int) and 0 < value < 10:
        return {"raw_value": value, "published_value": "<10", "status": "suppressed", "suppression_rule": "1-9"}
    return {"raw_value": value, "published_value": value, "status": "reported"}


def _summarize_ccw(cases: list[dict], jur: dict) -> dict:
    months = []
    for m in MONTHS:
        cohort = [c for c in cases if c["receipt_cohort"] == m]
        decision = [c["decision_days_from_application"] for c in cohort
                    if c["decision_days_from_application"] is not None]
        pickup = [c["pickup_days_from_application"] for c in cohort
                  if c["pickup_days_from_application"] is not None]
        months.append({
            "cohort_id": f"{jur['id']}:receipt:{m}", "month": m, "cohort_definition": "application receipt month",
            "received": len(cohort),
            "approved_decisions": sum(c["decision_outcome"] == "approved" for c in cohort),
            "denied_decisions": sum(c["decision_outcome"] == "denied" for c in cohort),
            "withdrawn_before_decision": sum(c["decision_outcome"] == "withdrawn" for c in cohort),
            "decision_pending_at_cutoff": sum(c["decision_status"] == "pending" for c in cohort),
            "pickup_completed": sum(c["fulfillment_status"] == "completed" for c in cohort),
            "pickup_pending_given_approval": sum(c["fulfillment_status"] == "pending" for c in cohort),
            "decision_median_days": round(quantile(decision, .5), 1) if decision else None,
            "pickup_median_days": round(quantile(pickup, .5), 1) if pickup else None,
            "decision_n": len(decision), "pickup_n": len(pickup),
        })
    approved = [c["pickup_days_from_application"] for c in cases
                if c["pickup_days_from_application"] is not None]
    return {"family": "ccw", "jurisdiction_id": jur["id"], "monthly_receipt_cohorts": months,
            "overall": {"n": len(cases), "approved_pickup_median_days": round(quantile(approved, .5), 1),
                        "approved_pickup_p75_days": round(quantile(approved, .75), 1),
                        "approved_pickup_p90_days": round(quantile(approved, .9), 1)}}


def _calfresh_stratum(case: dict) -> str:
    return f"{case['route']}_{case['approval_service_clock_origin']}"


def _calfresh_timing_strata(cases: list[dict], schema: str) -> list[dict]:
    out = []
    for stratum_id, route, origin in (
        ("normal_application", "normal", "application"),
        ("expedited_application", "expedited", "application"),
        ("expedited_eligibility_discovery", "expedited", "eligibility_discovery"),
    ):
        approved = [c for c in cases if c["decision_outcome"] == "approved" and
                    c["route"] == route and c["approval_service_clock_origin"] == origin]
        vals = [c["approval_days_from_service_clock"] for c in approved]
        bins = {"0_3": sum(v <= 3 for v in vals), "4_7": sum(4 <= v <= 7 for v in vals),
                "8_30": sum(8 <= v <= 30 for v in vals), "31_plus": sum(v > 30 for v in vals)}
        if schema == "CF18_A":
            over_30 = {"field_id": "A_OVER30", "definition": "approved cases over 30 service-clock days",
                       "value": _cell(sum(v > 30 for v in vals), suppress=True)}
        else:
            delayed = [c for c in approved if c["approval_days_from_service_clock"] > 30 and
                       c["delay_attribution"] == "county"]
            over_30 = {"field_id": "B_CTY_OVER30",
                       "definition": "approved cases over 30 service-clock days attributed to county delay",
                       "value": _cell(len(delayed), suppress=True)}
        out.append({
            "stratum_id": stratum_id, "route": route, "clock_origin": origin,
            "duration_definition": f"{origin}-to-approval",
            "approved_n": _cell(len(approved)),
            "approval_mean_days": _cell(round(sum(vals) / len(vals), 1) if vals else None),
            "approval_bins": {k: _cell(v, suppress=True) for k, v in bins.items()},
            "over_30_field": over_30,
        })
    return out


def _summarize_calfresh(cases: list[dict], jur: dict) -> dict:
    receipt, completion = [], []
    gaps = set(jur["report_gap_months"])
    for idx, m in enumerate(MONTHS):
        schema = "CF18_A" if idx < 12 else "CF18_B"
        cohort = [c for c in cases if c["receipt_cohort"] == m]
        row = {
            "cohort_id": f"{jur['id']}:receipt:{m}", "month": m, "schema_era": schema,
            "cohort_definition": "application receipt month", "report_status": "gap" if m in gaps else "reported",
            "workload": {
                "received": _cell(len(cohort)),
                "approved_decisions": _cell(sum(c["decision_outcome"] == "approved" for c in cohort)),
                "denied_decisions": _cell(sum(c["decision_outcome"] == "denied" for c in cohort), suppress=True),
                "withdrawn_before_decision": _cell(sum(c["decision_outcome"] == "withdrawn" for c in cohort), suppress=True),
                "decision_pending_at_cutoff": _cell(sum(c["decision_status"] == "pending" for c in cohort), suppress=True),
                "issuance_completed": _cell(sum(c["fulfillment_status"] == "completed" for c in cohort)),
                "issuance_pending_given_approval": _cell(sum(c["fulfillment_status"] == "pending" for c in cohort), suppress=True),
            },
            "timing_strata": _calfresh_timing_strata(cohort, schema),
        }
        receipt.append(row)
        completed = [c for c in cases if c["completion_cohort"] == m and c["decision_outcome"] == "approved"]
        completion.append({
            "cohort_id": f"{jur['id']}:completion:{m}", "month": m,
            "cohort_definition": "decision completion month; approvals only",
            "approved_completions": _cell(len(completed)),
            "timing_strata": _calfresh_timing_strata(completed, schema),
            "report_status": "reported",
        })
    return {"family": "calfresh", "jurisdiction_id": jur["id"], "receipt_cohorts": receipt,
            "completion_cohorts": completion,
            "schema_eras": [{"id": "CF18_A", "months": [MONTHS[0], MONTHS[11]]},
                             {"id": "CF18_B", "months": [MONTHS[12], MONTHS[-1]],
                              "breaking_change": "over-30 field adds county-caused-delay qualifier"}],
            "report_gaps": list(jur["report_gap_months"])}


def _claim(artifact_id: str, seq: int, topic: str, value: Any, *, unit: str | None = None,
           fidelity: str = "exact", qualifiers: list[str] | None = None) -> dict:
    return {"claim_id": f"{artifact_id}:Q{seq:04d}", "topic": topic, "value": value,
            "unit": unit, "fidelity": fidelity, "qualifiers": qualifiers or []}


def _spec_base(family: str, artifact_id: str, kind: str, jur: dict | None) -> dict:
    return {
        "schema_version": 1, "world_id": WORLD_ID, "artifact_id": artifact_id, "family": family,
        "jurisdiction_id": jur["id"] if jur else None, "kind": kind,
        "construction_status": "structured_render_spec_not_rendered",
        "publisher": (jur["name"] if jur else "Aurelia fictional state office"),
        "url": (f"https://{jur['public_host']}/{family}/{kind}" if jur else
                f"https://www.aurelia.aur.gov/{family}/{kind}"),
        "content_blocks": [],
        "renderer_constraints": {
            "must_not_invent_claims": True,
            "must_not_reveal": ["unpublished case records", "private lineage", "unpublished stage durations",
                                "staff labor hours", "evaluation split", "information ceiling"],
            "fictional_names_only": True,
        },
    }


def _add_claim(spec: dict, provenance: list[dict], topic: str, value: Any, *, source_kind: str,
               source_id: str, mechanism: str = "faithful", fidelity: str = "exact",
               unit: str | None = None, qualifiers: list[str] | None = None,
               transform: str = "identity") -> dict:
    seq = sum(len(b.get("claims", [])) for b in spec["content_blocks"]) + 1
    c = _claim(spec["artifact_id"], seq, topic, value, unit=unit, fidelity=fidelity, qualifiers=qualifiers)
    if not spec["content_blocks"]:
        spec["content_blocks"].append({"block_type": "claim_directives", "claims": []})
    spec["content_blocks"][0]["claims"].append(c)
    provenance.append({
        "claim_id": c["claim_id"], "artifact_id": spec["artifact_id"], "family": spec["family"],
        "source_kind": source_kind, "source_id": source_id, "reporting_mechanism": mechanism,
        "transformation": transform, "intended_fidelity": fidelity,
        "basis": "fictional design assumption" if source_kind == "design" else "generated episode/cohort truth",
    })
    return c


def _forum_observation(case: dict, family: str) -> dict:
    """Return the observed endpoint or right-censored age used by a forum claim."""
    app_day = (_iso_day(case["application_date"]) - _iso_day(WINDOW_START)).days
    cutoff = (_iso_day(WINDOW_END) - _iso_day(WINDOW_START)).days
    if family == "ccw" and case["pickup_days_from_application"] is not None:
        endpoint, status, value = ("application_to_pickup", "completed",
                                   case["pickup_days_from_application"])
    elif family == "calfresh" and case["issuance_days_from_application"] is not None:
        endpoint, status, value = ("application_to_issuance", "completed",
                                   case["issuance_days_from_application"])
    elif case["decision_status"] == "completed":
        endpoint = ("application_to_denial" if case["decision_outcome"] == "denied"
                    else "application_to_approval")
        status, value = "completed", case["decision_days_from_application"]
    elif case["decision_outcome"] == "withdrawn":
        endpoint, status = "application_to_withdrawal", "completed"
        value = max(e["end_day"] for e in case["observed_path"]) - app_day
    else:
        endpoint, status, value = "application_to_cutoff", "right_censored", cutoff - app_day
    assert value is not None and value >= 0
    return {"endpoint": endpoint, "censor_status": status, "duration_days": value}


def _ccw_specs(seed: int, jur: dict, cases: list[dict], summary: dict,
               provenance: list[dict], lineage: list[dict]) -> list[dict]:
    specs = []
    overall = summary["overall"]
    for kind in CCW_ARTIFACT_KINDS:
        aid = f"CCW__{jur['id']}__{kind}"
        spec = _spec_base("ccw", aid, kind, jur)
        if kind == "program_overview":
            _add_claim(spec, provenance, "issuer", jur["issuer"], source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "application_operator", jur["operator"], source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "routes", ["initial", "renewal"], source_kind="design", source_id=jur["id"])
        elif kind == "initial_application_guide":
            _add_claim(spec, provenance, "initial_stages", list(CCW_STAGES[:-1]), source_kind="design",
                       source_id=jur["id"], qualifiers=[
                           "scope=application receipt through decision; credential pickup is separate"])
        elif kind == "renewal_guide":
            _add_claim(spec, provenance, "renewal_stages",
                       ["application_received", "background_check", "training_review", "decision"],
                       source_kind="design", source_id=jur["id"], qualifiers=[
                           "scope=application receipt through decision; credential pickup is separate"])
        elif kind == "interview_and_pickup_guide":
            _add_claim(spec, provenance, "appointments", ["interview", "credential_pickup"], source_kind="design", source_id=jur["id"])
        elif kind == "training_provider_page":
            _add_claim(spec, provenance, "training_provider", jur["training_provider"], source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "issuer_is_not_training_provider", True, source_kind="design", source_id=jur["id"])
        elif kind == "fee_schedule":
            fee = 90 + 7 * jur["profile_index"]
            _add_claim(spec, provenance, "initial_agency_fee", fee, unit="USD", source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "provider_charge_separate", True, source_kind="design", source_id=jur["id"])
        elif kind == "monthly_performance_table":
            rows = [{k: row[k] for k in (
                "month", "received", "approved_decisions", "denied_decisions",
                "withdrawn_before_decision", "decision_pending_at_cutoff",
                "pickup_completed", "pickup_pending_given_approval",
                "decision_median_days", "decision_n")}
                    for row in summary["monthly_receipt_cohorts"]]
            _add_claim(spec, provenance, "receipt_cohort_table", rows, source_kind="cohort",
                       source_id=f"{jur['id']}:receipt:all",
                       qualifiers=["decision timing includes every observed completed decision",
                                   "pickup counts are a distinct fulfillment endpoint"])
        elif kind == "typical_time_faq":
            lo = max(1, round(overall["approved_pickup_median_days"] * .58))
            hi = max(lo + 1, round(overall["approved_pickup_p75_days"] * .82))
            _add_claim(spec, provenance, "typical_application_to_pickup_range", [lo, hi], unit="days",
                       source_kind="cohort", source_id=f"{jur['id']}:all:approved", mechanism="optimistic_summary",
                       fidelity="approximate", transform="0.58*median to 0.82*p75, rounded")
        elif kind == "news_summary":
            fast = [c["pickup_days_from_application"] for c in cases
                    if c["pickup_days_from_application"] is not None and
                    c["pickup_days_from_application"] <= 90]
            value = round(quantile(fast, .5), 1) if fast else None
            _add_claim(spec, provenance, "recent_processing_median", value, unit="days", source_kind="cohort",
                       source_id=f"{jur['id']}:approved_under90", mechanism="optimistic_truncation",
                       fidelity="approximate", transform="exclude approvals over 90 days and all unresolved cases")
        elif kind == "forum_thread":
            candidates = []
            for case in cases:
                observation = _forum_observation(case, "ccw")
                candidates.append((observation["duration_days"], case["case_id"], observation, case))
            candidates.sort(reverse=True)
            selected = candidates[:3]
            for pos, (raw, _case_id, observation, case) in enumerate(selected):
                endpoint, status = observation["endpoint"], observation["censor_status"]
                reported = int(math.ceil(raw / 14.0) * 2)
                c1 = _add_claim(spec, provenance, f"poster_{pos + 1}_timeline", reported, unit="weeks",
                                source_kind="case", source_id=case["case_id"], mechanism="delay_selected_forum",
                                fidelity="approximate",
                                qualifiers=[f"endpoint={endpoint}", f"censor_status={status}"],
                                transform="selected among longest observed endpoints/lower bounds; round up to two-week units")
                if pos == 0:
                    c2 = _add_claim(spec, provenance, "original_poster_update", reported, unit="weeks",
                                    source_kind="case", source_id=case["case_id"], mechanism="linked_update",
                                    fidelity="approximate",
                                    qualifiers=[f"endpoint={endpoint}", f"censor_status={status}"],
                                    transform="same observed endpoint/lower bound restated in an update")
                    lineage.append(link(SAME_CASE, c1["claim_id"], c2["claim_id"], facts_agree=True,
                                        note="original post and update describe the same CCW episode"))
                    c3 = _add_claim(spec, provenance, "quoted_timeline_reply", reported, unit="weeks",
                                    source_kind="case", source_id=case["case_id"], mechanism="copied_claim",
                                    fidelity="approximate",
                                    qualifiers=[f"endpoint={endpoint}", f"censor_status={status}"],
                                    transform="reply copies the original rounded timeline")
                    lineage.append(link(COPIED_TEXT, c1["claim_id"], c3["claim_id"],
                                        mechanism="restated_publication", facts_agree=True,
                                        note="a forum reply quotes the earlier rounded claim; it is not another case"))
        specs.append(spec)
    # Vendor boilerplate is private lineage: shared prose does not mean shared practice.
    source = f"TEMPLATE:{jur['vendor_template']}"
    lineage.append(link(COPIED_TEXT, source, f"CCW__{jur['id']}__program_overview",
                        mechanism="vendor_boilerplate", facts_agree=False))
    return specs


def _published(value: Any) -> Any:
    return value.get("published_value") if isinstance(value, dict) and "published_value" in value else value


def _calfresh_specs(seed: int, jur: dict, cases: list[dict], summary: dict,
                    provenance: list[dict], lineage: list[dict]) -> list[dict]:
    specs = []
    for kind in CALFRESH_ARTIFACT_KINDS:
        aid = f"CALFRESH__{jur['id']}__{kind}"
        spec = _spec_base("calfresh", aid, kind, jur)
        if kind == "program_overview":
            _add_claim(spec, provenance, "administering_agency", jur["agency"], source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "application_operator", jur["operator"], source_kind="design", source_id=jur["id"])
        elif kind == "application_guide":
            _add_claim(spec, provenance, "normal_route_stages",
                       ["application_received", "interview", "verification", "decision"],
                       source_kind="design", source_id=jur["id"], qualifiers=[
                           "scope=application receipt through decision; benefit issuance is separate"])
        elif kind == "expedited_service_guide":
            _add_claim(spec, provenance, "expedited_clock_origins", ["application", "eligibility_discovery"], source_kind="design", source_id=jur["id"],
                       qualifiers=["origin depends on when potential expedited eligibility is discovered"])
        elif kind == "interview_guide":
            _add_claim(spec, provenance, "interview_can_repeat", True, source_kind="design", source_id=jur["id"])
        elif kind == "verification_checklist":
            _add_claim(spec, provenance, "verification_can_repeat", True, source_kind="design", source_id=jur["id"])
        elif kind == "issuance_guide":
            _add_claim(spec, provenance, "issuance_provider", jur["issuance_provider"], source_kind="design", source_id=jur["id"])
            _add_claim(spec, provenance, "approval_and_issuance_are_distinct_endpoints", True, source_kind="design", source_id=jur["id"])
        elif kind == "receipt_cohort_workbook":
            for row in summary["receipt_cohorts"]:
                if row["report_status"] == "gap":
                    continue
                vals = {
                    "month": row["month"], "schema_era": row["schema_era"],
                    "workload": {k: _published(v) for k, v in row["workload"].items()},
                    "timing_strata": [{
                        "stratum_id": s["stratum_id"], "route": s["route"],
                        "clock_origin": s["clock_origin"],
                        "duration_definition": s["duration_definition"],
                        "approved_n": _published(s["approved_n"]),
                        "approval_mean_days": _published(s["approval_mean_days"]),
                        "approval_bins": {k: _published(v) for k, v in s["approval_bins"].items()},
                        "over_30_field": {"field_id": s["over_30_field"]["field_id"],
                                          "definition": s["over_30_field"]["definition"],
                                          "value": _published(s["over_30_field"]["value"])},
                    } for s in row["timing_strata"]],
                }
                c = _add_claim(spec, provenance, "receipt_cohort_row", vals, source_kind="cohort",
                               source_id=row["cohort_id"], mechanism="suppressed_monthly_release",
                               qualifiers=["workload totals are not timing denominators",
                                           "timing is route-and-clock-origin stratified",
                                           "approval mean and bins condition on approvals",
                                           "cells 1-9 are suppressed"])
                # Every component in the row is dependent on the same receipt cohort.
                lineage.append(link(SAME_COHORT, row["cohort_id"], c["claim_id"], facts_agree=True,
                                    note="counts, mean, and bins are dependent summaries of one receipt cohort"))
        elif kind == "completion_cohort_dashboard":
            for row in summary["completion_cohorts"]:
                vals = {"month": row["month"],
                        "approved_completions": _published(row["approved_completions"]),
                        "timing_strata": [{
                            "stratum_id": s["stratum_id"], "route": s["route"],
                            "clock_origin": s["clock_origin"],
                            "duration_definition": s["duration_definition"],
                            "approved_n": _published(s["approved_n"]),
                            "approval_mean_days": _published(s["approval_mean_days"]),
                        } for s in row["timing_strata"]]}
                c = _add_claim(spec, provenance, "completion_cohort_row", vals, source_kind="cohort",
                               source_id=row["cohort_id"], qualifiers=["completion month; approvals only"])
                lineage.append(link(SAME_COHORT, row["cohort_id"], c["claim_id"], facts_agree=True,
                                    note="completion count and mean summarize the same approved completions"))
        elif kind == "schema_change_notice":
            _add_claim(spec, provenance, "schema_revision", summary["schema_eras"], source_kind="design",
                       source_id=f"{jur['id']}:schema", qualifiers=["the two over-30 fields are not interchangeable"])
            _add_claim(spec, provenance, "known_report_gaps", summary["report_gaps"], source_kind="cohort",
                       source_id=f"{jur['id']}:gaps", qualifiers=["a gap is not a reported zero"])
        elif kind == "applicant_forum":
            candidates = []
            for case in cases:
                observation = _forum_observation(case, "calfresh")
                candidates.append((observation["duration_days"], case["case_id"], observation, case))
            candidates.sort(reverse=True)
            for pos, (raw, _case_id, observation, case) in enumerate(candidates[:3]):
                endpoint, status = observation["endpoint"], observation["censor_status"]
                reported = int(math.ceil(raw / 7.0))
                c1 = _add_claim(spec, provenance, f"poster_{pos + 1}_timeline", reported, unit="weeks",
                                source_kind="case", source_id=case["case_id"], mechanism="delay_selected_forum",
                                fidelity="approximate",
                                qualifiers=[f"endpoint={endpoint}", f"censor_status={status}"],
                                transform="select long observed endpoints/lower bounds and round upward to weeks")
                if pos == 0:
                    c2 = _add_claim(spec, provenance, f"poster_update_same_{endpoint}", reported, unit="weeks",
                                    source_kind="case", source_id=case["case_id"], mechanism="linked_update",
                                    fidelity="approximate", qualifiers=[f"endpoint={endpoint}", f"censor_status={status}"],
                                    transform="same case and same observed endpoint/lower bound, later restatement")
                    lineage.append(link(SAME_CASE, c1["claim_id"], c2["claim_id"], facts_agree=True,
                                        note="original post and linked update describe one benefit case"))
        specs.append(spec)
    lineage.append(link(COPIED_TEXT, f"TEMPLATE:{jur['consortium_template']}",
                        f"CALFRESH__{jur['id']}__program_overview", mechanism="consortium_template",
                        facts_agree=False))
    return specs


def _shared_specs(family: str, all_summaries: list[dict], provenance: list[dict],
                  lineage: list[dict]) -> list[dict]:
    specs = []
    for kind in SHARED_KINDS[family]:
        aid = f"{family.upper()}__SHARED__{kind}"
        spec = _spec_base(family, aid, kind, None)
        if "framework" in kind or "manual" in kind:
            stages = list(CCW_STAGES if family == "ccw" else CALFRESH_STAGES)
            _add_claim(spec, provenance, "state_process_framework", stages, source_kind="design", source_id=f"{family}:state")
        elif "provider_standard" in kind:
            _add_claim(spec, provenance, "provider_and_issuer_are_distinct_roles", True, source_kind="design", source_id="ccw:state")
        elif "data_dictionary" in kind:
            _add_claim(spec, provenance, "cohort_definitions", {
                "receipt": "month application was received", "completion": "month an approval decision completed",
                "approval_mean": "approval-conditioned within route and named clock origin",
                "approval_application_clock": "application received to approval decision",
                "approval_service_clock": "application or eligibility-discovery origin to approval decision",
                "issuance_application_clock": "application received to benefit issuance",
                "workload_counts": "all cases in cohort; never a timing denominator",
            }, source_kind="design", source_id="calfresh:state")
        else:
            if family == "ccw":
                vals = [s["overall"]["approved_pickup_median_days"] for s in all_summaries]
                value = round(sum(vals) / len(vals), 1)
                c1 = _add_claim(spec, provenance, "statewide_average_of_jurisdiction_medians", value, unit="days",
                                source_kind="cohort", source_id="ccw:all_jurisdictions", mechanism="optimistic_summary",
                                fidelity="approximate", transform="unweighted mean of approval-conditioned medians")
            else:
                values: dict[str, list[float]] = defaultdict(list)
                for s in all_summaries:
                    for row in s["receipt_cohorts"]:
                        if row["report_status"] == "gap":
                            continue
                        for stratum in row["timing_strata"]:
                            raw = stratum["approval_mean_days"]["raw_value"]
                            if raw is not None:
                                values[stratum["stratum_id"]].append(raw)
                value = {key: round(sum(vals) / len(vals), 1)
                         for key, vals in sorted(values.items())}
                c1 = _add_claim(spec, provenance,
                                "statewide_unweighted_monthly_approval_mean_by_timing_stratum",
                                value, unit="days",
                                source_kind="cohort", source_id="calfresh:all_reported_months", mechanism="optimistic_summary",
                                fidelity="approximate",
                                qualifiers=["separate values by route and clock origin"],
                                transform="within each timing stratum, unweighted mean of approval-conditioned reported county-month means")
            lineage.append(link(SAME_COHORT, c1["claim_id"], f"{c1['claim_id']}:source_aggregate",
                                mechanism="restated_publication", facts_agree=True,
                                note="state report restates an aggregate derived from the county summaries; not independent"))
        specs.append(spec)
    return specs


def _context(jur: dict) -> dict:
    if jur["family"] == "ccw":
        orgs = {k: jur[k] for k in ("issuer", "operator", "training_provider", "fingerprint_provider")}
    else:
        orgs = {k: jur[k] for k in ("agency", "operator", "issuance_provider")}
    return {
        "world_id": WORLD_ID, "family": jur["family"], "jurisdiction_id": jur["id"],
        "jurisdiction_name": jur["name"], "fictional": True, "public_host": jur["public_host"],
        "public_organizations": orgs,
        "scope": "Renderer may use only this context and the matching artifact specification.",
        "prohibitions": ["do not infer omitted facts", "do not consult private truth", "do not invent citations",
                         "do not imply empirical calibration", "do not claim independent verification"],
    }


def _ceiling(family: str, jur: dict, specs: list[dict]) -> dict:
    topics = [c["topic"] for s in specs for b in s["content_blocks"] for c in b.get("claims", [])]
    exact = sorted({c["topic"] for s in specs for b in s["content_blocks"] for c in b.get("claims", [])
                    if c["fidelity"] == "exact"})
    approx = sorted(set(topics) - set(exact))
    universe = ({"issuer", "application_operator", "routes", "initial_stages", "renewal_stages", "appointments",
                 "training_provider", "issuer_is_not_training_provider", "initial_agency_fee", "provider_charge_separate",
                 "receipt_cohort_table", "typical_application_to_pickup_range", "recent_processing_median",
                 "staff_hours", "internal_queue_priority"} if family == "ccw" else
                {"administering_agency", "application_operator", "normal_route_stages", "expedited_clock_origins",
                 "interview_can_repeat", "verification_can_repeat", "issuance_provider",
                 "approval_and_issuance_are_distinct_endpoints", "receipt_cohort_row", "completion_cohort_row",
                 "schema_revision", "known_report_gaps", "staff_hours", "internal_queue_priority"})
    hidden = sorted(universe - set(exact) - set(approx))
    return {"family": family, "jurisdiction_id": jur["id"], "artifact_ids": [s["artifact_id"] for s in specs],
            "recoverable_exact": exact, "recoverable_approximate_or_biased": approx,
            "recoverable_only_wrong": [], "hidden": hidden,
            "note": "Ceiling describes renderer-directed information, not a claim that prose has been rendered or verified."}


def _assert_public_boundary(specs: list[dict], contexts: list[dict]) -> None:
    for obj in [*specs, *contexts]:
        def walk(x: Any) -> None:
            if isinstance(x, dict):
                assert not (set(x) & FORBIDDEN_PUBLIC_KEYS), (obj.get("artifact_id"), set(x) & FORBIDDEN_PUBLIC_KEYS)
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(obj)


def _validate_outputs(config: dict, all_specs: dict[str, list[dict]], cases_count: int,
                      summaries: dict[str, list[dict]], provenance: list[dict], lineage: list[dict],
                      ceilings: list[dict]) -> None:
    assert cases_count == 2 * N_JURISDICTIONS * N_EPISODES == 24000
    claim_ids = []
    for family in ("ccw", "calfresh"):
        specs = all_specs[family]
        local = [s for s in specs if s["jurisdiction_id"]]
        shared = [s for s in specs if not s["jurisdiction_id"]]
        assert len(shared) <= config["artifact_quota"]["shared_per_family_max"] == 3
        assert Counter(s["jurisdiction_id"] for s in local) == {
            ("CCW" if family == "ccw" else "CF") + f"_J{i:02d}": len(CCW_ARTIFACT_KINDS if family == "ccw" else CALFRESH_ARTIFACT_KINDS)
            for i in range(1, 13)
        }
        assert max(Counter(s["jurisdiction_id"] for s in local).values()) <= 12
        assert len({s["artifact_id"] for s in specs}) == len(specs)
        claim_ids.extend(c["claim_id"] for s in specs for b in s["content_blocks"] for c in b.get("claims", []))
    assert len(claim_ids) == len(set(claim_ids))
    assert {p["claim_id"] for p in provenance} == set(claim_ids)
    assert {l["kind"] for l in lineage} == {SAME_CASE, SAME_COHORT, COPIED_TEXT}
    assert len(ceilings) == 24
    for s in summaries["calfresh"]:
        assert len(s["receipt_cohorts"]) == len(s["completion_cohorts"]) == 24
        assert s["report_gaps"]
        assert {r["schema_era"] for r in s["receipt_cohorts"]} == {"CF18_A", "CF18_B"}


def build(out_dir: str | pathlib.Path, *, seed: int = SEED) -> dict:
    """Build the fixed pilot in a new directory and return non-sensitive counts.

    Existing files are never overwritten.  The frozen config and private split
    manifest are written before the first episode RNG is constructed.
    """
    out = pathlib.Path(out_dir)
    if out.exists():
        raise ValueError("Preserving existing world/files: destination must not exist")
    out.mkdir(parents=True)
    config, split = frozen_design(seed)
    jurisdictions = _jurisdictions()
    freeze_digest = _sha256({"config": config, "split": split})
    _write_json(out / "world.json", config)
    (out / "BOUNDARY.md").write_text(BOUNDARY_TEXT, encoding="utf-8")
    _write_json(out / "private/evaluation/split_manifest.json", split)
    _write_json(out / "construction_receipt.json", {
        "world_id": WORLD_ID, "freeze_digest": freeze_digest, "frozen_before_draws": True,
        "completed_stages": ["freeze_config", "freeze_split"],
    })

    all_specs: dict[str, list[dict]] = {"ccw": [], "calfresh": []}
    summaries: dict[str, list[dict]] = {"ccw": [], "calfresh": []}
    provenance: list[dict] = []
    lineage: list[dict] = []
    ceilings: list[dict] = []
    contexts: list[dict] = []
    cases_count = 0
    generated_cases: dict[tuple[str, str], list[dict]] = {}

    # Every episode table is generated, checked, and persisted before any
    # derived summary is constructed.
    for family in ("ccw", "calfresh"):
        for jur in jurisdictions[family]:
            if family == "ccw":
                cases, process = _generate_ccw_cases(seed, jur)
            else:
                cases, process = _generate_calfresh_cases(seed, jur)
            generated_cases[(family, jur["id"])] = cases
            cases_count += len(cases)
            _write_jsonl_gz(out / f"private/truth/cases/{family}/{jur['id']}.jsonl.gz", cases)
            _write_json(out / f"private/truth/processes/{family}/{jur['id']}.json", process)

    for family in ("ccw", "calfresh"):
        for jur in jurisdictions[family]:
            cases = generated_cases[(family, jur["id"])]
            summary = _summarize_ccw(cases, jur) if family == "ccw" else _summarize_calfresh(cases, jur)
            summaries[family].append(summary)
            _write_json(out / f"private/truth/summaries/{family}/{jur['id']}.json", summary)
            specs = (_ccw_specs(seed, jur, cases, summary, provenance, lineage) if family == "ccw" else
                     _calfresh_specs(seed, jur, cases, summary, provenance, lineage))
            all_specs[family].extend(specs)
            ceilings.append(_ceiling(family, jur, specs))
            context = _context(jur)
            contexts.append(context)
            _write_json(out / f"public/render_context/{family}/{jur['id']}.json", context)

    for family in ("ccw", "calfresh"):
        all_specs[family].extend(_shared_specs(family, summaries[family], provenance, lineage))
        _write_jsonl(out / f"public/render_specs/{family}.jsonl", all_specs[family])

    _assert_public_boundary(all_specs["ccw"] + all_specs["calfresh"], contexts)
    _validate_outputs(config, all_specs, cases_count, summaries, provenance, lineage, ceilings)
    _write_jsonl_gz(out / "private/provenance/claim_provenance.jsonl.gz", provenance)
    _write_json(out / "private/provenance/lineage.json", {
        "links": lineage, "independence_report": independence_report(lineage),
    })
    _write_json(out / "private/evaluation/ceilings.json", ceilings)

    artifact_manifest = [{"artifact_id": s["artifact_id"], "family": s["family"],
                          "jurisdiction_id": s["jurisdiction_id"], "kind": s["kind"],
                          "status": s["construction_status"]}
                         for f in ("ccw", "calfresh") for s in all_specs[f]]
    _write_json(out / "public/artifact_manifest.json", artifact_manifest)
    counts = {
        "world_id": WORLD_ID, "families": 2, "jurisdictions": 24,
        "jurisdictions_per_family": 12, "episodes": cases_count,
        "episodes_per_jurisdiction": N_EPISODES, "months": 24,
        "artifacts": len(artifact_manifest),
        "artifacts_by_family": {f: len(all_specs[f]) for f in ("ccw", "calfresh")},
        "artifacts_per_jurisdiction": len(CCW_ARTIFACT_KINDS), "shared_artifacts_per_family": 3,
        "claims": len(provenance), "lineage_links": len(lineage), "ceilings": len(ceilings),
        "split_counts_per_family": config["split_counts_per_family"],
        "rendered_artifacts": 0, "independently_verified_artifacts": 0,
    }
    _write_json(out / "counts.json", counts)
    _write_json(out / "construction_receipt.json", {
        "world_id": WORLD_ID, "freeze_digest": freeze_digest, "frozen_before_draws": True,
        "successor_of": "THREE_FAMILY_PILOT_002",
        "successor_repairs": config["successor_repairs"],
        "completed_stages": config["generation_order"], "validation": "passed_in_memory_before_release",
        "limitations": [
            "Structured render specifications and contexts only; no prose corpus has been rendered.",
            "No artifact has received an independent verification verdict.",
            "No extraction ledger, fit input, posterior, or score is included.",
            "All stochastic parameters are fictional design assumptions, not empirical calibration.",
            "CalFresh recertification episodes are not yet modeled in this bounded initial build.",
            "CCW policy-era transitions are not yet modeled; CalFresh has two schema eras only.",
            "This build plants heterogeneous reporting distortions but does not provide a paired mechanics-versus-misspecification world.",
            "Stage inventories are fixed within each route; jurisdiction-specific step-inventory variation is not modeled.",
            "Planned-pending cases stop at an extended cutoff-crossing stage and have no latent eventual decision outcome or completion time; they cannot support an unconditional eventual-all-cases completion estimand without a separately reviewed future mechanism.",
        ],
    })
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the fixed fictional CCW and CalFresh pilot.")
    ap.add_argument("--out", default=f"benchmark/synth/worlds/{WORLD_ID}")
    args = ap.parse_args(argv)
    counts = build(args.out)
    # Counts and construction status are safe to print; private generated truth is not.
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
