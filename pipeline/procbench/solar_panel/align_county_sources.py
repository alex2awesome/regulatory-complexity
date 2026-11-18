#!/usr/bin/env python3
"""Align reviewed forum clocks to administrative phase endpoints without fitting."""
from __future__ import annotations

import argparse, hashlib, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
V1=ROOT/"runs/solar_forum_20260922/county_model/evidence_v1.json"
V2=ROOT/"runs/solar_forum_20260922/county_model/evidence_v2.json"
DEFAULT=V2 if V2.exists() else V1
OUT=ROOT/"runs/solar_forum_20260922/county_model/source_alignment_v1.json"

EXACT={"permit_submission_to_approval":("permit_review","exact_endpoint_match"),
       "city_inspection_receipt_to_pto":("final_ix_pto","utility_receipt_of_city_clearance_to_pto")}
FINAL={"final_documents_submission_to_pto":"submission_vs_admin_final_request_receipt_sensitivity",
       "installer_claimed_final_submission_to_pto":"claimed_submission_start_requires_source_sensitivity"}
PERMIT_BOUNDARY={"permit_application_to_permit_issuance":
                  "reported_application_or_permit_process_start_requires_receipt_boundary_sensitivity"}
INSPECTION={"installation_to_final_inspection","installation_to_first_inspection_attempt",
            "failed_inspection_to_pass","reported_reinspection_added_delay","reported_inspection_phase",
            "installation_complete_to_inspection_unscheduled"}
PERMIT_COMPONENT={"correction_resubmission_to_permit_issuance","county_review_component",
                  "permit_submission_to_city_correction_letter","permit_submission_to_city_document_request",
                  "reported_permitting_phase","design_acceptance_to_permit_issuance"}
PREINSTALL={"interconnection_submission_to_deemed_valid"}
PRIVATE={"contract_signature_to_site_survey","deposit_to_site_survey","first_meeting_to_design_ready",
         "installer_intro_call_to_owner_design_approval","site_assessment_to_design_acceptance",
         "site_assessment_to_reroof_requirement_notice","contractor_contact_attempts_to_response",
         "physical_installation_start_to_complete","powerwall_installation_start_to_complete",
         "powerwall_installation_to_backup_switch_installation","inverter_upgrade_start_to_complete",
         "maintenance_failure_confirmation_to_first_inverter_replacement","hoa_coordination",
         "existing_system_outage_during_upgrade","reported_nem_paperwork_preparation"}

def classify(clock):
    if clock in EXACT:
        p,r=EXACT[clock]; return p,"matched_admin_phase",r
    if clock in FINAL:
        return "final_ix_pto","matched_with_boundary_sensitivity",FINAL[clock]
    if clock in PERMIT_BOUNDARY:
        return "permit_review","matched_with_boundary_sensitivity",PERMIT_BOUNDARY[clock]
    if clock in INSPECTION:
        return "inspection","boundary_mixture_required","administrative_inspection_endpoint_is_source_contradictory"
    if clock in PERMIT_COMPONENT:
        return "permit_review","component_or_boundary_mismatch","not_the_full_first_submission_to_final_approval_endpoint"
    if clock in PREINSTALL:
        return "pre_install_ix","matched_with_boundary_sensitivity","deemed_valid_may_not_equal_approval_to_build"
    if clock in PRIVATE:
        return None,"private_or_nonadministrative_process","no_compatible_administrative_phase_endpoint"
    if clock in {"pto_wait_unspecified_start","project_work_elapsed_unspecified_boundaries"}:
        return None,"unknown_boundary","start_boundary_missing_not_forced_into_phase"
    if "pto" in clock or "operational_completion" in clock:
        return None,"compound_or_broader_pto_clock","contains_private_AHJ_or_utility_time_beyond_one_admin_phase"
    if "installation" in clock or "permit" in clock or "interconnection" in clock:
        return None,"compound_or_cross_phase_clock","not_equal_to_one_administrative_phase_endpoint"
    return None,"unmatched_typed_clock","no_declared_compatible_endpoint"

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence",type=Path,default=DEFAULT); ap.add_argument("--out",type=Path,default=OUT); args=ap.parse_args(argv)
    raw=args.evidence.read_bytes(); evidence=json.loads(raw); rows=[]
    for claim in evidence["forum_observations"]:
        phase,route,reason=classify(claim["clock"])
        utility_phase=phase in {"pre_install_ix","final_ix_pto"}
        geography={"county_weights":claim.get("county_weights",[]),"county_unresolved_weight":claim.get("geography_unresolved_weight",1.0),
                   "county_candidates":claim.get("county_candidates",[]),"ahj_candidates":claim.get("ahj_candidates",[]),"utility_candidates":[claim["utility"]] if claim.get("utility") else [],
                   "geography_state":claim.get("geography_state"),
                   "identity_strategy":("utility_scope_county_not_required" if utility_phase else
                     "known_AHJ_or_county_candidates_with_unresolved_population_mixture" if claim.get("county_weights") or claim.get("ahj_candidates") else
                     "unknown_geography_population_mixture_no_flat_assignment")}
        row={"row_id":"align_"+hashlib.sha256((claim["row_id"]+"|"+str(phase)+"|"+route).encode()).hexdigest()[:16],
             "forum_row_id":claim["row_id"],"case_id":claim["case_id"],"canonical_case_id":claim["canonical_case_id"],
             "source_family":claim["source_family"],"source_type":claim["source_type"],"clock":claim["clock"],"clock_family":claim["clock_family"],
             "alignment_route":route,"alignment_reason":reason,"admin_phase_candidate":phase,
             "observed_kind":claim["observed_kind"],"bounds_calendar_days":claim["bounds"],"units":"calendar_days",
             "original_units":claim.get("original_units"),"business_calendar_sensitivity":{"admin_business_to_calendar_multiplier":7/5,"forum_calendar_to_business_multiplier":5/7,"status":"declared_unit_conversion_sensitivity_not_an_observed_duration"},
             "event_era":claim.get("time_era",{"years":[],"confidence":"unknown"}),"size_class":"unknown_not_imputed","technology":"unknown_not_imputed",
             "geography":geography,"source_packet":claim.get("source_packet"),"source_claim_id":claim.get("source_claim_id"),
             "source_refs":claim.get("source_refs",[]),"selection_provenance":claim.get("selection_provenance"),"original":claim.get("original")}
        rows.append(row)
    route_counts=Counter(x["alignment_route"] for x in rows); phase_counts=Counter(str(x["admin_phase_candidate"] or "none") for x in rows)
    taxonomy={
      "matched_admin_phase":"Forum endpoints match the named administrative phase.",
      "matched_with_boundary_sensitivity":"Candidate phase retained, but submission/receipt, claimed-status, or approval-to-build boundary needs sensitivity.",
      "boundary_mixture_required":"Potential inspection evidence retained as a mixture because the administrative source contradicts itself about inspection start/end endpoints.",
      "component_or_boundary_mismatch":"A component of an administrative phase, not silently treated as the full phase.",
      "private_or_nonadministrative_process":"Installer/applicant/private work not represented by an administrative owner phase.",
      "compound_or_broader_pto_clock":"Clock crosses or contains more than one administrative/private segment through PTO.",
      "compound_or_cross_phase_clock":"Clock crosses phase boundaries and is not decomposed without evidence.",
      "unknown_boundary":"Elapsed report retained with an unknown start or end rather than assigned to a phase.",
      "unmatched_typed_clock":"Typed claim preserved; no current administrative analogue."
    }
    out={"schema_version":"solar-county-source-alignment/1","scope":"Endpoint/source alignment for eventual joint likelihood; not a source-bias estimate, posterior, fitted output, or whole-process sum.",
         "input":{"path":str(args.evidence),"sha256":hashlib.sha256(raw).hexdigest(),"forum_claims":len(evidence["forum_observations"])},
         "principles":["Unknown AHJ/county never excludes a forum claim.","Utilities are not counties; PTO alignment can be utility-scoped with county unresolved.","Unknown geography uses a declared future population mixture, never an implicit flat assignment.","Forum event era remains observed/unknown as compiled; size and technology remain unknown.","Administrative business days convert to calendar days by 7/5 only as a declared sensitivity.","Contradictory administrative inspection endpoints require a boundary mixture."],
         "taxonomy":taxonomy,"accounting":{"input_claims":len(rows),"output_claims":len(rows),"route_counts":dict(sorted(route_counts.items())),"phase_candidate_counts":dict(sorted(phase_counts.items())),"claims_with_unresolved_county_mass":sum(x["geography"]["county_unresolved_weight"]>0 for x in rows),"claims_with_unknown_era":sum(not x["event_era"].get("years") for x in rows)},"claims":rows}
    if len(rows)!=len(evidence["forum_observations"]):
        raise ValueError("Every input forum observation must retain an alignment route")
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out["accounting"],indent=2))

if __name__=="__main__": main()
