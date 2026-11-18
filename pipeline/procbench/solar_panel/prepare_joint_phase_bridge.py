"""Compile the first narrow SolarTRACE/forum phase bridge; never run a sampler."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np

from pipeline.procbench.bayes_trace_hierarchy import Config, VisitHierarchy


ROOT = Path("runs/solar_forum_20260922/county_model")
ALIGNMENT = ROOT / "source_alignment_v3.json"
EVIDENCE = ROOT / "evidence_v3.json"
OUTPUT = ROOT / "joint_phase_bridge002"
PHASE_ROUTE = {
    "permit_review": {"matched_admin_phase"},
    "final_ix_pto": {"matched_admin_phase", "matched_with_boundary_sensitivity"},
}
REFERENCE_CELL = dict(year=2023, size_class="0-10kW", technology="PV Only")
BUSINESS_TO_CALENDAR = 1.4
UTILITY_ALIASES = {"PGE": "Pacific Gas & Electric Co. (PG&E)",
                   "SCE": "Southern California Edison Co (SCE)",
                   "SDGE": "San Diego Gas & Electric Co (SDGE)"}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def source_id(logical_threads: list[str]) -> str:
    return "forum_thread:" + "__".join(slug(value) for value in sorted(logical_threads))


def row_digest(row: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def operation(owner_id: str, phase: str) -> dict[str, Any]:
    return dict(id=phase, actor_id=owner_id, actor_role="agency", task_type=phase,
                markers=["decision"], payer_work=False, agency_work=False)


def program(program_id: str, owner_id: str, phase: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
    return dict(id=program_id, inventory_granularity="aggregate_phases",
        clock_estimand=("permit submission-to-approval administrative phase" if phase == "permit_review"
                        else "final interconnection request receipt-to-PTO administrative phase; forum submission boundary is a sensitivity assumption"),
        routes=[dict(id="declared_phase", prior_weight=1.0,
            operations=[operation(owner_id, phase)], blocks=[dict(id=phase, operations=[phase])])],
        observations=observations)


def forum_owner(claim: dict[str, Any], admin_names: set[str]) -> tuple[str, str, str | None]:
    phase=claim["admin_phase_candidate"]
    geography=claim["geography"]
    if phase == "permit_review":
        candidates=[x for x in geography["ahj_candidates"] if x in admin_names]
        if len(candidates) == 1:
            return "ahj:" + slug(candidates[0]), candidates[0], candidates[0]
        county_weights=geography["county_weights"]
        if (len(county_weights) == 1 and county_weights[0]["weight"] == 1.0
                and geography["county_unresolved_weight"] == 0):
            county=county_weights[0]["county"]
            return "unknown_ahj_within_county:"+slug(county), "Unknown AHJ within "+county, None
        return "unresolved:permit_review", "Unresolved California AHJ", None
    candidates=[x for x in geography["utility_candidates"] if x in UTILITY_ALIASES]
    if len(candidates) == 1:
        return "utility:" + slug(candidates[0]), UTILITY_ALIASES[candidates[0]], None
    return "unresolved:final_ix_pto", "Unresolved California utility", None


def forum_observation(claim: dict[str, Any], evidence_row: dict[str, Any]) -> dict[str, Any]:
    lower,upper=claim["bounds_calendar_days"]
    observation=dict(id=claim["row_id"], case_id=claim["canonical_case_id"],
        source_family=source_id(evidence_row["logical_threads"]), source_type="forum",
        sampling="unselected", statistic="individual", lower=float(lower),
        upper=None if upper is None else float(upper), time_unit="calendar_days",
        operators=[dict(basis="single_visit_cycle", activity_ids=[claim["admin_phase_candidate"]])],
        operator_weights=[1.0], provenance=dict(alignment_row_id=claim["row_id"],
            source_claim_id=claim["source_claim_id"], source_refs=claim["source_refs"],
            logical_threads=evidence_row["logical_threads"],
            geography=claim["geography"],
            alignment_route=claim["alignment_route"],
            boundary_assumption=("forum submission is treated as a sensitivity proxy for administrative receipt; not resolved or causal bias"
                if claim["alignment_route"] == "matched_with_boundary_sensitivity"
                else "reviewed named endpoints treated as compatible; no submission-to-receipt substitution")))
    return observation


def admin_observation(row: dict[str, Any]) -> dict[str, Any]:
    value=float(row["value"])
    if row["reported_zero"]:
        lower,upper=0.0,BUSINESS_TO_CALENDAR
    else:
        lower=max(0.0,(value-.5)*BUSINESS_TO_CALENDAR)
        upper=(value+.5)*BUSINESS_TO_CALENDAR
    return dict(id=row["row_id"], case_id=None, source_family=row["source_family"],
        source_type="official_administrative_panel", sampling="unselected", statistic="median",
        lower=lower, upper=upper, time_unit="calendar_days",
        operators=[dict(basis="single_visit_cycle", activity_ids=[row["phase"]])],
        operator_weights=[1.0], provenance=dict(admin_row_id=row["row_id"],
            original_units="business_days", conversion_multiplier=BUSINESS_TO_CALENDAR,
            observed_kind=row["observed_kind"], zero_semantics=row["zero_semantics"],
            installs=row["installs"], sample_size_status=row["sample_size_status"],
            denominator_uncertainty=row["denominator_uncertainty"]))


def compile_bridge(alignment: dict[str, Any], evidence: dict[str, Any]) -> tuple[dict, dict, dict]:
    evidence_forum={row["row_id"]:row for row in evidence["forum_observations"]}
    admin_reference=[row for row in evidence["administrative_observations"]
        if row["year"] == REFERENCE_CELL["year"] and row["size_class"] == REFERENCE_CELL["size_class"]
        and row["technology"] == REFERENCE_CELL["technology"]]
    admin_names={row["owner_name"] for row in admin_reference}
    admitted_claims=[c for c in alignment["claims"]
        if c["admin_phase_candidate"] in PHASE_ROUTE
        and c["alignment_route"] in PHASE_ROUTE[c["admin_phase_candidate"]]]
    case_counts={case:sum(c["canonical_case_id"] == case for c in admitted_claims)
                 for case in {c["canonical_case_id"] for c in admitted_claims}}
    duplicate_cases={case for case,count in case_counts.items() if count > 1}

    forum_routes=[]
    usable=[]
    for claim in alignment["claims"]:
        if claim not in admitted_claims:
            reason=("phase_outside_first_bridge" if claim["admin_phase_candidate"] not in PHASE_ROUTE
                    else "alignment_route_outside_first_bridge")
            forum_routes.append(dict(row_id=claim["row_id"], disposition="routed", reason=reason,
                                     phase=claim["admin_phase_candidate"], alignment_route=claim["alignment_route"]))
        elif claim["canonical_case_id"] in duplicate_cases:
            forum_routes.append(dict(row_id=claim["row_id"], disposition="routed",
                reason="shared_case_across_bridge_clocks_unsupported_no_duplicate_case_latent",
                canonical_case_id=claim["canonical_case_id"]))
        else:
            usable.append(claim)
            forum_routes.append(dict(row_id=claim["row_id"], disposition="admitted",
                phase=claim["admin_phase_candidate"], canonical_case_id=claim["canonical_case_id"]))

    owners={}
    for claim in usable:
        owner_id,owner_name,ahj_name=forum_owner(claim,admin_names)
        county_weights=claim["geography"]["county_weights"]
        county=(county_weights[0]["county"] if len(county_weights)==1
                and county_weights[0]["weight"]==1.0 and claim["geography"]["county_unresolved_weight"]==0 else None)
        owners[(claim["admin_phase_candidate"],owner_id)]=dict(
            owner_id=owner_id, owner_name=owner_name, ahj_name=ahj_name, county=county,
            geography_candidates=claim["geography"])

    # A county-only forum identity remains a distinct unknown AHJ.  When that
    # county has exactly one compatible panel owner in the reference cell, retain
    # its administrative median as a separate actor connected only by county.
    for (phase,owner_id),owner in list(owners.items()):
        if not owner_id.startswith("unknown_ahj_within_county:"):
            continue
        candidates=[row for row in admin_reference if row["phase"]==phase and row["county"]==owner["county"]]
        if len(candidates)==1:
            row=candidates[0]
            key=(phase,"panel_county_reference:"+slug(row["owner_name"]))
            owners[key]=dict(owner_id=key[1],owner_name=row["owner_name"],ahj_name=row["owner_name"],
                             county=row["county"],geography_candidates=None,reference_only=True)

    selected_admin={}
    admin_routes=[]
    for row in evidence["administrative_observations"]:
        key=None
        for (phase,owner_id),owner in owners.items():
            if owner_id.startswith("unresolved:") or row["phase"] != phase:
                continue
            if row["owner_name"] == owner["owner_name"]:
                key=(phase,owner_id)
                break
        reference=(row["year"] == REFERENCE_CELL["year"] and
                   row["size_class"] == REFERENCE_CELL["size_class"] and
                   row["technology"] == REFERENCE_CELL["technology"])
        if key is not None and reference:
            if key in selected_admin:
                raise ValueError("Reference cell is not unique for " + repr(key))
            selected_admin[key]=row
            admin_routes.append(dict(row_id=row["row_id"], disposition="admitted", reason="named_owner_reference_cell"))
        else:
            reason=("phase_outside_first_bridge" if row["phase"] not in PHASE_ROUTE
                    else "owner_not_named_by_admitted_forum_claim" if key is None
                    else "outside_predeclared_2023_0_10kw_pv_only_reference_cell")
            admin_routes.append(dict(row_id=row["row_id"], disposition="routed", reason=reason))

    missing=[key for key in owners if not key[1].startswith(("unresolved:","unknown_ahj_within_county:"))
             and key not in selected_admin]
    if missing:
        raise ValueError("Missing compatible administrative reference rows: " + repr(missing))

    observations_by_program={}
    metadata_by_program={}
    def ensure_program(phase, owner_id, era, owner):
        pid="bridge:"+phase+":"+slug(owner_id)+":"+era
        observations_by_program.setdefault(pid,[])
        metadata_by_program[pid]=dict(phase=phase,owner_id=owner_id,era=era,owner=owner)
        return pid
    for key,row in selected_admin.items():
        phase,owner_id=key; owner=owners[key]
        ensure_program(phase,owner_id,"admin_2023_reference",owner)
        observations_by_program["bridge:"+phase+":"+slug(owner_id)+":admin_2023_reference"].append(admin_observation(row))
    for claim in usable:
        phase=claim["admin_phase_candidate"]
        owner_id,_,_=forum_owner(claim,admin_names); owner=owners[(phase,owner_id)]
        era=("forum_2023_unknown_size_storage" if claim["event_era"]["years"] == [2023]
             else "forum_context_unknown_or_other")
        pid=ensure_program(phase,owner_id,era,owner)
        observations_by_program[pid].append(forum_observation(claim,evidence_forum[claim["forum_row_id"]]))

    terms=[]
    counties=sorted({o["county"] for o in owners.values() if o["county"]})
    for county in counties:
        terms.append(dict(id="county:"+slug(county),group="county",prior_sd=.4,
            rationale="Working fixed county context prior for known AHJs only; not county-government equivalence"))
    terms.extend([
        dict(id="era:context_unknown_or_other",group="year",prior_sd=.35,
             rationale="Unknown/non-2023 forum era sensitivity; not estimated temporal transport"),
        dict(id="forum:size_unknown",group="size",prior_sd=.35,
             rationale="Forum system size missing; fixed sensitivity rather than 0-10kW imputation"),
        dict(id="forum:storage_unknown",group="storage",prior_sd=.35,
             rationale="Forum storage status missing; fixed sensitivity rather than PV-only imputation")])
    rows=[]
    for pid,meta in metadata_by_program.items():
        loadings={}
        if meta["owner"]["county"]:
            loadings["county:"+slug(meta["owner"]["county"])]=1.0
        if meta["era"] == "forum_context_unknown_or_other":
            loadings["era:context_unknown_or_other"]=1.0
        if any(o["case_id"] is not None for o in observations_by_program[pid]):
            loadings["forum:size_unknown"]=1.0; loadings["forum:storage_unknown"]=1.0
        rows.append(dict(program_id=pid,operation_id=meta["phase"],loadings=loadings))

    programs=[program(pid,meta["owner_id"],meta["phase"],observations_by_program[pid])
              for pid,meta in metadata_by_program.items()]
    documents=sorted({o["source_family"] for p in programs for o in p["observations"]})
    admin_sources={r["source_family"] for r in selected_admin.values()}
    data=dict(schema_version="solar-joint-phase-bridge/1", elapsed_time_unit="calendar_days",
        programs=programs,
        operation_location_design=dict(schema_version="operation-location-design/1",
            interpretation="Additive fixed working priors for county/era and missing forum size/storage context; owner variation uses the base agency hierarchy once. No term is a calibrated capability or prevalence effect.",
            unlisted_operations="zero_additive_effect",terms=terms,rows=rows),
        source_offset_hierarchy=dict(schema_version="source-offset-hierarchy/1",
            source_family_grouping="document",elapsed_time_unit="calendar_days",
            reference_type="official_administrative_panel",
            type_scale_prior=dict(median=.4,log_sd=.3),
            document_scale_prior=dict(median=.25,log_sd=.3),
            documents=[dict(document_id=d,source_type=("official_administrative_panel" if d in admin_sources else "forum")) for d in documents]))
    accounting=dict(schema_version="solar-joint-phase-route-accounting/1",
        forum=dict(input=len(alignment["claims"]),admitted=sum(r["disposition"]=="admitted" for r in forum_routes),routes=forum_routes),
        administrative=dict(input=len(evidence["administrative_observations"]),admitted=len(selected_admin),routes=admin_routes),
        duplicate_canonical_cases=sorted(duplicate_cases), reference_cell=REFERENCE_CELL,
        qualifications=["Only permit_review and final_ix_pto are bridged.",
            "Utilities are county-free; unresolved owners remain explicit operations.",
            "Forum observations use contextual operations separate from the 2023 0-10kW PV-only administrative reference operation because forum size/storage are missing; they share actor and owner effects rather than inventing reference-cell membership.",
            "Exact logical thread IDs, not parser-batch filenames, define forum source documents.",
            "County-only permit identities use an unknown-AHJ-within-county actor; any panel county owner is a separate actor linked only through the county term.",
            "Forum sampling is provisionally treated as unselected/ignorable conditional on offsets; this is unproven.",
            "Selection is disabled; sensitivity to informative posting remains required.",
            "Final-document submission versus administrative receipt is an interpretation sensitivity, not a solved boundary or causal source bias.",
            "No installs field is used as sample size and no compound clock is admitted."])
    config=dict(modeled_channels=["elapsed"],elapsed_time_unit="calendar_days",population_size=32,
        agency_sd=.75,
        selection_sd=0.0,hierarchy_sampler="operation_centered",source_hierarchy_sampler="interwoven",
        unknown_n_report_sd_floor=.5,interpretation="Preflight configuration only; base agency effect is the sole owner prior and has fixed working sd .75, not a calibrated intrinsic capability.",
        posterior_association_warning="Forum source offsets and forum missing-size/storage terms are not separately identified by source composition; report association, not source trust or calibrated covariate effects.")
    return data,config,accounting


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--alignment",type=Path,default=ALIGNMENT)
    parser.add_argument("--evidence",type=Path,default=EVIDENCE)
    parser.add_argument("--out",type=Path,default=OUTPUT)
    args=parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Refusing to overwrite existing bridge output: "+str(args.out))
    alignment=json.loads(args.alignment.read_text()); evidence=json.loads(args.evidence.read_text())
    data,config_record,accounting=compile_bridge(alignment,evidence)
    provenance=dict(alignment_path=str(args.alignment),alignment_sha256=row_digest(alignment),
                    evidence_path=str(args.evidence),evidence_sha256=row_digest(evidence))
    data["provenance"]=provenance
    accounting["provenance"]=provenance
    cfg_args={k:v for k,v in config_record.items() if k not in ("interpretation","posterior_association_warning")}
    cfg_args["modeled_channels"]=tuple(cfg_args["modeled_channels"])
    model=VisitHierarchy(data,Config(**cfg_args))
    z=np.zeros(model.layout.size); structures=[0]*len(model.programs)
    likelihood=model.log_likelihood(z,structures)
    preflight=dict(schema_version="solar-joint-phase-preflight/1",valid=True,
        finite_zero_state_log_likelihood=bool(math.isfinite(likelihood)),zero_state_log_likelihood=float(likelihood),
        programs=len(model.programs),operations=len(model.operations),observations=sum(len(p["observations"]) for p in model.programs),
        coordinates=model.layout.size,sampler_run=False,input_sha256=dict(alignment=row_digest(alignment),evidence=row_digest(evidence)),
        scope="Two coarse administrative phases only; not all counties, not a full process, and not a capability estimate.")
    args.out.mkdir(parents=True,exist_ok=True)
    for name,value in (("data.json",data),("config.json",config_record),("route_accounting.json",accounting),("preflight.json",preflight)):
        (args.out/name).write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    print(json.dumps(preflight,indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
