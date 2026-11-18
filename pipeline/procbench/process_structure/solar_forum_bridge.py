"""Compile reviewed SOLAR forum positives into the existing occupancy contract.

This is deliberately a positive-mention-selected likelihood.  The held forum
parse extracted elapsed measurements, not whole-case action checklists, so it
cannot support inferred nondetections.  Episodes without usable AHJ identity
remain in the coverage ledger and timing evidence; utility context is never
converted into an AHJ identity.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .forum import add_reviewed_episodes
from .identity import SCHEMA
from .occupancy import Evidence, verify_source_bindings
from .solar_sources import ROOT, slug

BASE = ROOT / "runs/process_structure_20260921/solar_phase1/occupancy_evidence.json"
REGISTRY = ROOT / "runs/process_structure_20260921/solar_phase1/step_universe.jsonl"
FORUM = ROOT / "runs/solar_panel_20260920/forum_v1.json"
PANEL = ROOT / "runs/solar_panel_20260920/panel_v1.csv"
ARTIFACTS = ROOT / "runs/rw_parse_20260918/solar_permit/artifacts"
DEFAULT_OUT = ROOT / "runs/solar_forum_20260922/model_bridge/exploratory_held_input"

BLOCK = [
    "solar_permit__ahj_permit_application_submission",
    "solar_permit__ahj_completeness_determination",
    "solar_permit__ahj_plan_review",
    "solar_permit__ahj_structural_review",
    "solar_permit__ahj_electrical_review",
    "solar_permit__ahj_correction_resubmittal",
    "solar_permit__ahj_permit_issuance",
    "solar_permit__inspection_scheduling_request",
    "solar_permit__ahj_final_inspection",
    "solar_permit__ahj_reinspection",
    "solar_permit__ahj_final_approval",
]
SHORT = {x.removeprefix("solar_permit__"): x for x in BLOCK}


def _ref(path: Path, locator: str) -> dict:
    return {"path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "locator": locator}


def _crosswalk() -> dict[str, str]:
    out = {}
    with PANEL.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["owner_scope"] != "ahj":
                continue
            value = slug(row["owner_name"])
            old = out.setdefault(row["stable_owner_id"], value)
            if old != value:
                raise ValueError("stable owner maps to more than one phase-1 jurisdiction")
    return out


def _block_base() -> dict:
    base = json.loads(BASE.read_text())
    data = copy.deepcopy(base)
    data["schema_version"] = SCHEMA
    data["steps"] = list(BLOCK)
    data["observations"] = [r for r in data["observations"] if r["step_id"] in BLOCK]
    data["known_presence"] = [r for r in data["known_presence"] if r["step_id"] in BLOCK]
    data["source_types"] = [k for k in data["source_types"] if any(
        r["source_type"] == k for r in data["observations"])]
    data["source_models"] = {k: data["source_models"][k] for k in data["source_types"]}
    return data


def compile_bridge() -> tuple[dict, dict]:
    """Exploratory held-timing bridge; not a valid primary occupancy input.

    Selection into the elapsed-measurement ledger depends on a positive mention,
    while the occupancy likelihood does not model that selection.  Its output is
    useful only to exercise identity marginalization and source plumbing.
    """
    data = _block_base()
    forum = json.loads(FORUM.read_text())
    crosswalk = _crosswalk()
    kind = "forum_elapsed_positive_mentions"
    data["source_types"].append(kind)
    # Selected mentions estimate neither full-narrative detection nor absence.
    data["source_models"][kind] = {"detection_beta": [2.0, 2.0],
                                   "false_positive_probability": 0.02}
    data["uncertain_jurisdiction_units"] = []

    grouped = defaultdict(list)
    coverage = Counter()
    coverage_rows = []
    for row in forum["rows"]:
        hits = sorted({SHORT[a] for a in row.get("activities", []) if a in SHORT})
        reason = None
        if row.get("entity_level") == "utility":
            reason = "utility_scoped_timing_only"
        elif not hits:
            reason = "no_coherent_ahj_block_positive"
        elif row.get("candidate_basis") != "explicit_place_name":
            reason = ("ahj_positive_weak_or_unlocalized_retained_in_duration_evidence"
                      if row.get("entity_level") == "authority" else "non_ahj_scope")
        elif not row.get("candidates"):
            reason = "no_supported_ahj_candidate"
        elif not row.get("quote_verified"):
            reason = "quote_not_verified"
        else:
            key = row.get("case_id") or row["id"]
            grouped[(row["doc_id"], key)].append((row, hits))
            reason = "admitted_positive_mention_episode"
        coverage[reason] += 1
        coverage_rows.append({"measurement_id": row["id"], "doc_id": row["doc_id"],
                              "case_id": row.get("case_id"), "route": reason,
                              "candidate_basis": row.get("candidate_basis"),
                              "activities_in_block": hits,
                              "duration_row_retained": True})

    for (doc_id, case_id), members in sorted(grouped.items()):
        artifact = ARTIFACTS / f"{doc_id}.md"
        if not artifact.exists():
            raise ValueError(f"missing reviewed forum artifact: {artifact}")
        candidates = {}
        for row, _ in members:
            for stable, weight in row["candidates"].items():
                if stable not in crosswalk:
                    raise ValueError(f"forum candidate absent from exact panel crosswalk: {stable}")
                jid = crosswalk[stable]
                candidates[jid] = max(candidates.get(jid, 0.0), float(weight))
        total = sum(candidates.values())
        candidates = [{"jurisdiction_id": j, "prior_weight": w / total}
                      for j, w in sorted(candidates.items())]
        detected = sorted({step for _, hits in members for step in hits})
        scope = _ref(artifact, f"$case[{json.dumps(case_id)}]")
        readings = []
        for step in detected:
            ids = [r["id"] for r, hits in members if step in hits]
            readings.append({"step_id": step, "detected": True, "reviewed_scope": True,
                             "evidence_refs": [_ref(artifact, f"$measurements[{json.dumps(i)}]")
                                               for i in ids]})
        uid = f"solar-forum-positive::{case_id}"
        data["uncertain_jurisdiction_units"].append({
            "unit_id": uid, "dependence_group_id": uid, "source_type": kind,
            "identity_scope_id": uid, "identity_scope_reviewed": True,
            "identity_scope_refs": [scope], "identity_reviewed": True,
            "candidate_scope_complete": True,
            "assignment_prior_kind": "reviewed_candidate_weights",
            "assignment_prior_basis": "Held forum review found explicit place-name context; weights are the frozen contextual candidate weights and do not use duration or outcome.",
            "assignment_prior_refs": [scope], "candidates": candidates,
            "reading_scope_kind": "reviewed_fixed_subset",
            "reviewed_step_ids": detected, "step_scope_reviewed": True,
            "step_scope_rationale": "Elapsed-measurement extraction selected positive action mentions only; no nondetections are asserted.",
            "step_scope_refs": [scope], "readings": readings,
        })

    data["scope"] += " Forum contribution is restricted to selected positive AHJ-action mentions."
    data["assumption_note"] += (
        " Forum elapsed extraction is positive-mention selected: it contributes no nondetections. "
        "Only explicit place-name candidate sets enter AHJ occupancy; weak localization and utility "
        "context remain in duration coverage without AHJ assignment.")
    data["forum_adoption"] = {
        "status": "exploratory_invalid_for_primary_inference",
        "invalid_primary_reason": "positive-mention selection is not represented in the occupancy likelihood",
        "ascertainment": "positive_mentions_from_prevalidated_elapsed_measurements",
        "nondetections_emitted": 0,
        "episodes_admitted": len(data["uncertain_jurisdiction_units"]),
        "rows_by_route": dict(sorted(coverage.items())),
        "all_duration_rows_retained_in_coverage": len(coverage_rows) == len(forum["rows"]),
    }
    Evidence(data)
    report = {
        "schema_version": "solar-forum-bridge-coverage/1",
        "status": "exploratory_invalid_for_primary_inference",
        "forum_rows": len(forum["rows"]), "rows_by_route": dict(sorted(coverage.items())),
        "episodes_admitted": len(data["uncertain_jurisdiction_units"]),
        "positive_readings": sum(len(u["readings"]) for u in data["uncertain_jurisdiction_units"]),
        "nondetections_emitted": 0, "rows": coverage_rows,
        "qualifications": [
            "Coverage retention is not occupancy admission.",
            "Utility-only evidence remains utility timing evidence.",
            "Survey No is used only for the exact question asked; missing answers emit no row.",
            "The 50-step registry is metadata; the fit contains only the coherent 11-step block."
        ]
    }
    return data, report


def _explicit_unresolved_mass(episode: dict):
    """Return explicitly declared identity mass outside named candidates, if any."""
    values = [episode.get(key) for key in (
        "unresolved_jurisdiction_mass", "candidate_unresolved_mass",
        "jurisdiction_unresolved_mass") if episode.get(key) is not None]
    prior = episode.get("jurisdiction_prior")
    if isinstance(prior, dict) and prior.get("unresolved_mass") is not None:
        values.append(prior["unresolved_mass"])
    if not values:
        return None
    if len(values) != 1 or isinstance(values[0], bool) or not isinstance(values[0], (int, float)):
        raise ValueError("Declare unresolved jurisdiction mass once as a finite probability")
    value = float(values[0])
    if not 0 <= value <= 1:
        raise ValueError("Unresolved jurisdiction mass must be in [0,1]")
    return value


def _mix_unresolved_identity(episode: dict, unresolved_mass: float) -> dict | None:
    """Apply an explicitly declared fallback q without inventing geography.

    Named weights are treated as w conditional on the named component and keep
    total mass ``1-u``.  Fallback weights are q conditional on the unresolved
    component and keep total mass ``u``.  Overlapping jurisdictions are summed;
    neither component is separately renormalized after mixing.
    """
    fallback = episode.get("unresolved_identity_fallback")
    if fallback is None:
        return None
    if (not isinstance(fallback, dict)
            or fallback.get("schema_version") != "unresolved-identity-fallback/1"
            or fallback.get("independence_declaration") != "source_independent_of_episode_action_and_timing"
            or not isinstance(fallback.get("assumption_label"), str)
            or not fallback["assumption_label"].strip()):
        raise ValueError("Fallback q needs schema, source-independence declaration and assumption label")
    refs = fallback.get("source_refs")
    if (not isinstance(refs, list) or not refs
            or any(not isinstance(ref, dict) or not isinstance(ref.get("path"), str)
                   or not ref["path"] or not isinstance(ref.get("sha256"), str)
                   or len(ref["sha256"]) != 64 or not isinstance(ref.get("locator"), str)
                   or not ref["locator"] for ref in refs)):
        raise ValueError("Fallback q requires explicit source-bound references")

    def component(rows, label, allow_empty=False):
        if not isinstance(rows, list) or (not rows and not allow_empty):
            raise ValueError(f"{label} candidates must be an explicit nonempty list")
        result, seen = [], set()
        for row in rows:
            jid, weight = row.get("jurisdiction_id"), row.get("prior_weight")
            if (not isinstance(jid, str) or not jid or jid in seen or isinstance(weight, bool)
                    or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight <= 0):
                raise ValueError(f"{label} candidates need distinct IDs and finite positive weights")
            seen.add(jid)
            result.append((jid, float(weight)))
        total = sum(weight for _, weight in result)
        return [(jid, weight / total) for jid, weight in result]

    named = component(episode.get("candidates", []), "Named", allow_empty=unresolved_mass == 1)
    fallback_q = component(fallback.get("candidates"), "Fallback")
    combined = defaultdict(float)
    for jid, weight in named:
        combined[jid] += (1 - unresolved_mass) * weight
    for jid, weight in fallback_q:
        combined[jid] += unresolved_mass * weight
    combined = {jid: weight for jid, weight in combined.items() if weight > 0}
    if not combined or not math.isclose(sum(combined.values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Unresolved identity mixture must preserve total probability one")

    result = copy.deepcopy(episode)
    result["candidates"] = [
        {"jurisdiction_id": jid, "prior_weight": weight}
        for jid, weight in sorted(combined.items())]
    result["assignment_prior_kind"] = "reviewed_candidate_weights"
    result["assignment_prior_basis"] = (
        result.get("assignment_prior_basis", "Reviewed named identity weights")
        + f" Mixed with unresolved mass {unresolved_mass:g} under declared fallback: "
        + fallback["assumption_label"])
    result["unresolved_identity_mixture"] = {
        "unresolved_mass": unresolved_mass,
        "named_mass": 1 - unresolved_mass,
        "named_candidates_conditional": [
            {"jurisdiction_id": jid, "prior_weight": weight} for jid, weight in named],
        "fallback_candidates_conditional": [
            {"jurisdiction_id": jid, "prior_weight": weight} for jid, weight in fallback_q],
        "combined_candidates": copy.deepcopy(result["candidates"]),
        "assumption_label": fallback["assumption_label"],
        "independence_declaration": fallback["independence_declaration"],
        "source_refs": copy.deepcopy(refs),
    }
    return result


def _route_reviewed_packet(packet: dict) -> tuple[dict, list[dict]]:
    """Separate honest opportunity scopes from descriptive-only episodes.

    The occupancy adapter has no latent category for geography outside the
    declared jurisdiction candidates. Explicit unresolved mass therefore stays
    visible in routing instead of being silently normalized away.
    """
    filtered = copy.deepcopy(packet)
    admitted, routes = [], []
    for episode in packet.get("episodes", []):
        episode_id = episode.get("episode_id")
        scope_kind = episode.get("reading_scope_kind", "complete_fixed_universe")
        descriptive = (scope_kind == "positive_only_descriptive"
            or episode.get("inference_scope") == "descriptive_only"
            or episode.get("likelihood_eligible") is False)
        readings = episode.get("readings")
        if descriptive:
            if (not isinstance(readings, list)
                    or any(type(row.get("detected")) is not bool for row in readings)
                    or any(not row["detected"] for row in readings)):
                raise ValueError("Positive-only descriptive episodes may contain explicit positives only")
            routes.append(dict(episode_id=episode_id, disposition="descriptive_only",
                reason="positive_only_or_nonopportunity_scope_no_occupancy_likelihood",
                reviewed_step_ids=copy.deepcopy(episode.get("reviewed_step_ids", [])),
                explicit_unresolved_jurisdiction_mass=_explicit_unresolved_mass(episode)))
            continue
        if episode.get("occurrence_reviewed") is not True:
            raise ValueError("Every production episode must review performed/experienced occurrence")
        if episode.get("statistic") != "individual":
            raise ValueError("Targets, typical claims and aggregate statistics are not individual episodes")
        reviewed = episode.get("reviewed_step_ids")
        if scope_kind == "complete_fixed_universe":
            if reviewed != BLOCK:
                raise ValueError("Production full checklist must equal the ordered frozen 11-step block")
        elif scope_kind == "reviewed_fixed_subset":
            if (not isinstance(reviewed, list) or not reviewed
                    or len(set(reviewed)) != len(reviewed)
                    or not set(reviewed) <= set(BLOCK)
                    or not isinstance(readings, list)
                    or len(readings) != len(reviewed)
                    or {row.get("step_id") for row in readings} != set(reviewed)
                    or episode.get("step_scope_reviewed") is not True
                    or not isinstance(episode.get("step_scope_rationale"), str)
                    or not episode["step_scope_rationale"].strip()
                    or not any(row.get("detected") is True for row in readings)):
                raise ValueError("Production subset needs exact declared support, reviewed scope metadata and an AHJ positive")
        else:
            raise ValueError("Unknown production SOLAR reading scope kind")
        unresolved_mass = _explicit_unresolved_mass(episode)
        if unresolved_mass:
            mixed = _mix_unresolved_identity(episode, unresolved_mass)
            if mixed is None:
                routes.append(dict(episode_id=episode_id, disposition="descriptive_only",
                    reason="explicit_unresolved_geography_mass_not_representable_without_silent_normalization",
                    reviewed_step_ids=copy.deepcopy(reviewed),
                    explicit_unresolved_jurisdiction_mass=unresolved_mass))
                continue
            episode = mixed
        if episode.get("assignment_prior_kind") == "reviewed_candidate_weights":
            episode = copy.deepcopy(episode)
            episode.setdefault("assignment_prior_basis", "Reviewed contextual weights; broad CA support may be prior-driven and is not a hard AHJ assignment.")
        admitted.append(episode)
        routes.append(dict(episode_id=episode_id, disposition="occupancy_opportunity",
            reason=("explicit_unresolved_identity_mixture" if unresolved_mass
                    else ("legacy_complete_fixed_universe" if scope_kind == "complete_fixed_universe"
                          else "explicit_reviewed_fixed_subset")),
            reviewed_step_ids=copy.deepcopy(reviewed),
            explicit_unresolved_jurisdiction_mass=unresolved_mass,
            combined_candidates=copy.deepcopy(episode.get("candidates")) if unresolved_mass else None))
    filtered["episodes"] = admitted
    return filtered, routes


def compile_reviewed_packet(packet: dict) -> tuple[dict, dict]:
    """Compile full or explicitly bounded reviews through the existing adapter."""
    filtered, routes = _route_reviewed_packet(packet)
    data = add_reviewed_episodes(_block_base(), filtered, source_root=ROOT)
    admitted_ids = {row["episode_id"] for row in routes
                    if row["disposition"] == "occupancy_opportunity"}
    admitted = [episode for episode in packet.get("episodes", [])
                if episode.get("episode_id") in admitted_ids]
    report = {
        "schema_version": "solar-forum-reviewed-bridge/1", "status": "production_candidate",
        "episodes": len(admitted),
        "input_episodes": len(packet.get("episodes", [])),
        "descriptive_episodes": len(packet.get("descriptive_episodes", [])) + sum(
            row["disposition"] == "descriptive_only" for row in routes),
        "full_opportunity_episodes": sum(row["reason"] == "legacy_complete_fixed_universe" for row in routes),
        "subset_opportunity_episodes": sum(row["reason"] == "explicit_reviewed_fixed_subset" for row in routes),
        "reading_opportunities": sum(len(e["readings"]) for e in admitted),
        "positive_readings": sum(r["detected"] for e in admitted for r in e["readings"]),
        "reviewed_nondetections": sum(not r["detected"] for e in admitted for r in e["readings"]),
        "nondetections_emitted_outside_declared_support": 0,
        "routes": routes,
        "ascertainment": "whole captured episode selected before action coding; performed/experienced occurrence reviewed",
        "qualification": "Positive-only/descriptive episodes contribute no occupancy likelihood; subset nondetections exist only inside explicitly reviewed_step_ids.",
    }
    return data, report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--reviewed-packet", type=Path)
    parser.add_argument("--held-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError("choose a fresh output directory")
    if bool(args.reviewed_packet) == bool(args.held_diagnostic):
        raise ValueError("choose exactly one of --reviewed-packet or --held-diagnostic")
    if args.reviewed_packet:
        data, report = compile_reviewed_packet(json.loads(args.reviewed_packet.read_text()))
    else:
        data, report = compile_bridge()
    args.out.mkdir(parents=True)
    (args.out / "occupancy_evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    (args.out / "coverage.json").write_text(json.dumps(report, indent=2) + "\n")
    registry = [json.loads(line) for line in REGISTRY.read_text().splitlines()]
    (args.out / "action_registry_metadata.json").write_text(json.dumps({
        "source": str(REGISTRY.relative_to(ROOT)), "registry_count": len(registry),
        "fit_step_ids": BLOCK, "excluded_from_fit_count": len(registry) - len(BLOCK),
        "registry": registry}, indent=2) + "\n")
    (args.out / "smoke_config.json").write_text(json.dumps({
        "chains": 2, "warmup": 20, "draws": 40, "seed": 20260922,
        "hierarchy_update": "collapsed", "hierarchy_block_size": 4}, indent=2) + "\n")
    config_name = "production_config.json" if args.reviewed_packet else "exploratory_config.json"
    (args.out / config_name).write_text(json.dumps({
        "chains": 4, "warmup": 1000, "draws": 2000, "seed": 20260922,
        "hierarchy_update": "collapsed", "hierarchy_block_size": 4}, indent=2) + "\n")
    verified = verify_source_bindings(data, ROOT)
    console = {"out": str(args.out), "verified_source_files": verified,
               "status": report.get("status")}
    for key in ("forum_rows", "episodes", "episodes_admitted", "reading_opportunities",
                "positive_readings", "reviewed_nondetections", "nondetections_emitted"):
        if key in report:
            console[key] = report[key]
    print(json.dumps(console, indent=2))


if __name__ == "__main__":
    main()
