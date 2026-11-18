#!/usr/bin/env python3
"""Compile county/AHJ solar administrative and reviewed forum evidence.

This is a loss-accounting compiler, not a model.  It preserves utility-scoped
rows without pretending utilities are counties and retains unresolved routes.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
from pipeline.recon.solar_review_packet import decision_case_id

ROOT = Path(__file__).resolve().parents[3]
PANEL = ROOT / "runs/solar_panel_20260920/panel_v1.csv"
COUNTIES = ROOT / "corpus/counties/ca_counties_covariates.csv"
TIMING = ROOT / "runs/solar_forum_20260922/timing_combined008"
OUT = ROOT / "runs/solar_forum_20260922/county_model/evidence_v1.json"

# Explicit corrections to missing panel geography, supported by municipal
# descriptions. The statewide HCD owner deliberately remains county-free.
COUNTY_CROSSWALK_SUPPLEMENTS = {
    "Cathedral City city": ("Riverside", "https://www.cathedralcity.gov/home/showpublisheddocument/2691/638416048925700000"),
    "Laguna Woods city": ("Orange", "https://cityoflagunawoods.org/wp-content/uploads/2015/06/LAGUNA-WOODS-OVERVIEW.pdf"),
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rid(prefix, payload):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return prefix+"_"+hashlib.sha256(raw.encode()).hexdigest()[:16]
def num(x):
    if x in (None, ""): return None
    try: return float(x)
    except (TypeError, ValueError): return None
def truth(x): return str(x).lower()=="true"

def timing_fit_status(timing):
    """Saved-result coverage only: a compiled input is not a fitted posterior."""
    queue = json.loads((timing / "fit_queue.json").read_text())
    summary_path = timing / "fit_summary.json"
    saved = json.loads(summary_path.read_text()) if summary_path.exists() else []
    queued = {row["clock"] for row in queue}
    reported = {row["clock"]: row for row in saved if row["clock"] in queued}
    return {
        "state": ("no_saved_fit_summaries" if not reported else
                  "all_clock_fit_summaries_saved" if len(reported) == len(queued)
                  else "partial_saved_fit_summaries"),
        "compiled_clocks": len(queued), "saved_clock_fit_summaries": len(reported),
        "numerically_usable_saved_clocks": sum(row.get("numerically_usable") is True for row in reported.values()),
        "qualification": "File-based result coverage, not a live-job status or evidence of population validity. Compiled claims alone are not posterior consumption.",
    }

def source_paths(timing=TIMING):
    paths={}
    for spec in sorted(timing.glob("*_spec.json")):
        data=json.loads(spec.read_text())
        for item in data.get("input_bindings", []):
            p=item.get("path")
            if p: paths[p]=item.get("sha256")
    return paths

def episode_index(paths):
    idx=defaultdict(list); loaded=[]
    for raw in sorted(paths):
        p=ROOT/raw
        if not p.exists() or "/parse/" not in raw: continue
        try: data=json.loads(p.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError): continue
        if not isinstance(data,dict) or not isinstance(data.get("episodes"),list): continue
        loaded.append(raw)
        for ep in data["episodes"]:
            ep = ep.get("review_metadata", {}).get("semantic_decision", ep)
            t=str(ep.get("thread") or ep.get("thread_id") or "")
            a=str(ep.get("author") or "")
            if t and a: idx[decision_case_id({**ep, "thread":t, "author":a})].append((raw,ep))
    return idx,loaded

def weights(ep, county_names, ahj_to_county):
    # Optional explicit soft geography, including unassigned probability mass.
    # These are upstream declared priors/sensitivities, not calibrated confidence.
    unknown=ep.get("unassigned_geography_mass")
    if unknown is not None and (isinstance(unknown,bool) or not isinstance(unknown,(int,float))
                                or not 0 <= unknown <= 1):
        raise ValueError("Unassigned geographic mass must be between zero and one")
    resolved_mass=1.0-(unknown or 0.0)
    if "county_assignment_probabilities" in ep:
        rows=ep["county_assignment_probabilities"]
        if not isinstance(rows,list):
            raise ValueError("County assignment probabilities must be an explicit list")
        seen=set(); result=[]
        for row in rows:
            county=row.get("county"); weight=row.get("weight")
            if (county not in county_names or county in seen or isinstance(weight,bool)
                    or not isinstance(weight,(int,float)) or not 0 < weight <= 1):
                raise ValueError("Invalid or repeated county assignment probability")
            seen.add(county)
            result.append({"county":county,"weight":weight,
                "basis":row.get("basis","declared_soft_geography_prior_not_calibrated")})
        if sum(r["weight"] for r in result)>1+1e-10:
            raise ValueError("County assignment probabilities exceed one")
        if unknown is not None and sum(r["weight"] for r in result)+unknown>1+1e-10:
            raise ValueError("County assignment and declared unknown mass exceed one")
        return result
    if resolved_mass == 0:
        return []  # Candidate names are not permission to erase declared uncertainty.
    ahjs=[str(x) for x in ep.get("ahj_names",[]) if x]
    if ahjs:
        counts=Counter(ahj_to_county.get(a.upper()) for a in ahjs)
        counts.pop(None,None)
        if counts:
            n=len(ahjs)
            return [{"county":c,"weight":resolved_mass*v/n,"basis":"uniform_candidate_AHJs_aggregated_to_county_with_declared_unknown_mass"} for c,v in sorted(counts.items())]
    candidates=[str(x).strip() for x in ep.get("candidate_counties",[]) if str(x).strip() in county_names]
    if candidates:
        u=sorted(set(candidates)); w=resolved_mass/len(u)
        return [{"county":c,"weight":w,"basis":"declared_county_candidate_uniform_prior"} for c in u]
    c=str(ep.get("county") or "").strip()
    if c in county_names: return [{"county":c,"weight":resolved_mass,"basis":"explicit_county_with_declared_unknown_mass"}]
    loc=str(ep.get("location") or "")
    hits=[c for c in county_names if re.search(rf"\b{re.escape(c)}(?: County)?\b",loc,re.I)]
    if len(hits)==1: return [{"county":hits[0],"weight":resolved_mass,"basis":"explicit_county_in_location_field_with_declared_unknown_mass"}]
    return []

def declared_era(original, ep):
    """Extract era only from declared date/year fields, never arbitrary text."""
    years=[]; full_dates=0
    def visit(obj):
        nonlocal full_dates
        if isinstance(obj,dict):
            for k,v in obj.items():
                key=str(k).lower()
                if key.endswith("_date") or key in {"date","start_date","end_date"}:
                    m=re.match(r"^(20\d{2})(?:-\d{2}-\d{2})?$",str(v))
                    if m: years.append(int(m.group(1))); full_dates += ("-" in str(v))
                elif key in {"year","event_year","installation_year"} and re.match(r"^20\d{2}$",str(v)):
                    years.append(int(v))
                elif key in {"event_years", "installation_years"} and isinstance(v, list):
                    for year in v:
                        visit({"event_year": year})
        elif isinstance(obj,list):
            for x in obj: visit(x)
    visit(original)
    # Episode-level declared dates are context, but free-text notes/location are not.
    for key in ("event_year","installation_year","event_years","installation_years","start_date","end_date"):
        if key in ep: visit({key:ep[key]})
    unique=sorted(set(years))
    return {"years":unique,"confidence":"high" if full_dates else "medium" if unique else "unknown",
            "basis":"declared_date_or_year_fields_only" if unique else "no_declared_event_date"}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default=str(OUT))
    ap.add_argument("--timing",type=Path,default=TIMING)
    ap.add_argument("--instruction-packet",type=Path,action="append",default=[],
                    help="County instruction captures retained as a separate, not-yet-fitted source layer")
    args=ap.parse_args(argv); timing=args.timing.resolve()
    county_rows=list(csv.DictReader(COUNTIES.open())); county_names={r["county"] for r in county_rows}
    panel=list(csv.DictReader(PANEL.open()))
    for row in panel:
        if not row["county"] and row["owner_name"] in COUNTY_CROSSWALK_SUPPLEMENTS:
            county, url = COUNTY_CROSSWALK_SUPPLEMENTS[row["owner_name"]]
            row["county"] = county
            row["county_original_missing"] = True
            row["county_crosswalk_source"] = url
    ahj_to_county={r["owner_name"].upper():r["county"] for r in panel if r["owner_kind"]=="ahj" and r["county"]}
    county_ahjs=defaultdict(set)
    for a,c in ahj_to_county.items(): county_ahjs[c].add(a)

    admin=[]; routes=[]; seen={}
    for i,r in enumerate(panel,2):
        key=(r["stable_owner_id"],r["phase"],r["year"],r["size_class"],r["technology"])
        base={"owner_id":r["stable_owner_id"],"owner_kind":r["owner_kind"],"county":r["county"] or None,
              "phase":r["phase"],"year":int(r["year"]),"size_class":r["size_class"],"technology":r["technology"]}
        if key in seen:
            routes.append({"row_id":rid("route",{"kind":"admin_duplicate", "line":i}),"source_family":"SolarTRACE_corrected_panel","source_type":"administrative_cell","route":"duplicate_stable_owner_phase_year_size_technology","original_line":i,"duplicate_of":seen[key]})
            continue
        value=num(r["median_business_days"])
        if r["present"]!="true" or value is None:
            route={"source_family":"SolarTRACE_corrected_panel","source_type":"administrative_cell",
                   "route":"administrative_cell_no_reported_reading","source_line":i,"owner_id":r["stable_owner_id"],
                   "owner_kind":r["owner_kind"],"county":r["county"] or None,"phase":r["phase"],
                   "year":int(r["year"]),"size_class":r["size_class"],"technology":r["technology"],"original":r}
            route["row_id"]=rid("route",{"kind":"admin_missing","key":key,"line":i}); seen[key]=route["row_id"]
            routes.append(route); continue
        obs={**base,"source_family":"SolarTRACE_corrected_panel","source_type":"administrative_cell",
             "owner_name":r["owner_name"],"owner_scope":r["owner_scope"],"ahj_identity":r["owner_name"] if r["owner_kind"]=="ahj" else None,
             "value":value,"units":r["unit"],"observed_kind":"reported_median_cell",
             "zero_semantics":r["zero_semantics"] or r["pre_install_zero_resolution"] or None,"reported_zero":truth(r["reported_zero"]),
             "installs":int(r["installs_same_cell"] or 0),"installs_role":r["installs_role"],"sample_size_status":r["sample_size_status"],
             "denominator_floor":int(r["denominator_floor"] or 10),"denominator_uncertainty":"unknown_n_at_least_floor; installs_is_exposure_and_upper_bound_not_sample_n",
             "holdout_authority":truth(r["holdout_authority"]),"holdout_forward_year":truth(r["holdout_forward_year"]),
             "source_row_count":int(r["source_row_count"] or 0),"source_line":i,"original":r}
        obs["row_id"]=rid("admin",{**base,"value":obs["value"],"source_line":i}); seen[key]=obs["row_id"]; admin.append(obs)

    bindings=source_paths(timing); idx,semantic_loaded=episode_index(bindings)
    consumption=json.loads((timing/"model_consumption.json").read_text()); aliases=consumption.get("explicit_same_installation_aliases",{})
    fit_status={}
    if (timing/"fit_summary.json").exists():
        fit_status={r["clock"]: ("fit_completed_numerically_usable" if r.get("numerically_usable")
                    else "fit_completed_numerically_failed")
                    for r in json.loads((timing/"fit_summary.json").read_text())}
    forum=[]
    for claim in consumption.get("claims",[]):
        cid=claim["case_id"]; canonical=aliases.get(cid,cid); candidates=idx.get(cid,[])
        if not candidates and canonical!=cid: candidates=idx.get(canonical,[])
        # The same case may occur in a clock-only adopted packet and its richer
        # semantic source. Prefer locating fields, never timing values, when
        # choosing the geography record.
        def geo_score(item):
            _, e=item
            return ("county_assignment_probabilities" in e,
                    6*bool(e.get("candidate_counties")) + 5*bool(e.get("county")) +
                    4*bool(e.get("ahj_names")) + 2*bool(e.get("location")) + bool(e.get("utility")))
        ep_path,ep=(max(candidates,key=geo_score) if candidates else (None,{}))
        ws=weights(ep,county_names,ahj_to_county)
        original=claim.get("original",{}); bounds=claim.get("bounds_calendar_days")
        original_unit=original.get("unit") or claim.get("elapsed_time_unit")
        unit="calendar_days" if bounds is not None else original_unit
        era=declared_era(original,ep)
        unresolved_weight=max(0.0,1.0-sum(w["weight"] for w in ws)) if ws else 1.0
        row={"source_family":"reviewed_solar_forum","source_type":"individual_elapsed_report","case_id":cid,"canonical_case_id":canonical,
             "timing_fit_state":fit_status.get(claim["clock"],"prepared_not_yet_fitted"),
             "clock_family":claim["clock"],"clock":claim["clock"],"units":unit,"original_units":original_unit,"bounds":bounds,
             "original_clock":claim.get("original_clock",claim["clock"]),
             "original_claim_id":claim.get("original_claim_id",claim.get("id")),
             "clock_alias_applied":claim.get("clock_alias_applied",False),
             "observed_kind":claim.get("observation_kind"),"route":claim.get("route"),"original":original,
             "utility":ep.get("utility") or claim.get("utility"),"ahj_candidates":ep.get("ahj_names",[]),"county_candidates":ep.get("candidate_counties",[]),
             "county_weights":ws,"geography_unresolved_weight":unresolved_weight,
             "geography_state":"resolved_or_weighted" if ws and unresolved_weight==0 else "partially_resolved" if ws else "missing_or_noncounty_context",
             "location_text":ep.get("location"),"time_era":era,"source_packet":ep_path,
             "source_refs":original.get("refs",[]),"logical_threads":sorted(set([cid.split("__",1)[0]]+claim.get("logical_threads",[]))),
             "source_claim_id":claim.get("id"),
             "selection_provenance":{"consumption_path":str((timing/"model_consumption.json").relative_to(ROOT)),
                "clock_spec_path":str((timing/f'{claim["clock"]}_spec.json').relative_to(ROOT)),
                "selection_route":claim.get("route"),"semantic_source_packet":ep_path,
                "source_claim_id":claim.get("id"),"source_refs":original.get("refs",[])}}
        row["row_id"]=rid("forum",{"claim":claim.get("id"),"case":cid,"clock":claim["clock"]}); forum.append(row)
        if not candidates: routes.append({"row_id":rid("route",{"claim":claim.get("id"),"reason":"semantic_source_unmatched"}),"source_family":"reviewed_solar_forum","source_type":"individual_elapsed_report","source_claim_id":claim.get("id"),"route":"semantic_episode_unmatched_geography_preserved","case_id":cid,"clock":claim["clock"]})
        elif not ws: routes.append({"row_id":rid("route",{"claim":claim.get("id"),"reason":"county_unresolved"}),"source_family":"reviewed_solar_forum","source_type":"individual_elapsed_report","source_claim_id":claim.get("id"),"route":"county_unresolved_observation_retained","case_id":cid,"clock":claim["clock"]})

    # Account for numeric semantic timing rows that were present in bound source
    # packets but were not selected into timing_combined008.  Repeated copies of
    # the same case/clock/refs across adopted and source packets count once.
    consumed={(x["case_id"],x["clock"]) for x in forum}
    consumed.update((x["case_id"],x["original_clock"]) for x in forum)
    unmatched_seen=set()
    for case_id, occurrences in idx.items():
        canonical=aliases.get(case_id,case_id)
        for path,ep in occurrences:
            for timing_row in ep.get("timing",[]):
                clock=timing_row.get("clock")
                if not clock or (case_id,clock) in consumed or (canonical,clock) in consumed: continue
                sig=(canonical,clock,tuple(timing_row.get("refs",[])))
                if sig in unmatched_seen: continue
                unmatched_seen.add(sig)
                routes.append({"row_id":rid("route",{"case":canonical,"clock":clock,"refs":sig[2]}),
                    "source_family":"reviewed_solar_forum","source_type":"semantic_numeric_clock",
                    "route":"numeric_clock_not_in_selected_timing_input","case_id":case_id,
                    "canonical_case_id":canonical,"clock":clock,"source_packet":path,
                    "source_refs":timing_row.get("refs",[]),"original":timing_row})

    by_county=Counter(x["county"] for x in admin if x["county"] and x["value"] is not None)
    forum_candidates=Counter(w["county"] for x in forum for w in x["county_weights"])
    forum_county=Counter()
    for observation in forum:
        for candidate in observation["county_weights"]:
            forum_county[candidate["county"]]+=candidate["weight"]
    frame=[]
    for r in county_rows:
        c=r["county"]; n=by_county[c]; nf=forum_county[c]
        frame.append({"county":c,"fips":r["fips"],"covariates":r,"panel_ahjs":sorted(county_ahjs[c]),
                      "administrative_readings":n,"forum_weighted_readings":nf,
                      "forum_candidate_readings":forum_candidates[c],
                      "reading_state":"administrative_and_forum" if n and nf else "administrative_only" if n else "forum_only" if nf else "zero_readings"})
    accounting={"county_count":len(frame),"administrative_input_rows":len(panel),"administrative_observations":len(admin),
                "forum_claims_input":len(consumption.get("claims",[])),"forum_observations":len(forum),
                "forum_with_county_weights":sum(bool(x["county_weights"]) for x in forum),"forum_missing_county_weights":sum(not x["county_weights"] for x in forum),
                "route_counts":dict(Counter(x["route"] for x in routes)),"counties_zero_readings":sum(x["reading_state"]=="zero_readings" for x in frame)}
    provenance={"panel":{"path":str(PANEL.relative_to(ROOT)),"sha256":sha(PANEL)},"counties":{"path":str(COUNTIES.relative_to(ROOT)),"sha256":sha(COUNTIES)},
                "timing_consumption":{"path":str((timing/"model_consumption.json").relative_to(ROOT)),"sha256":sha(timing/"model_consumption.json")},
                "timing_input_bindings":bindings,"semantic_packets_loaded":semantic_loaded}
    instructions=[]
    for packet in args.instruction_packet:
        packet=packet.resolve()
        binding={"path":str(packet.relative_to(ROOT)),"sha256":sha(packet)}
        for at,record in enumerate(json.loads(packet.read_text())["records"]):
            if record["county"] not in county_names:
                raise ValueError("Instruction county outside declared 58-county frame")
            status=record["status"]
            if "unresolved" in status or "blocked" in status:
                state="unresolved_source"
            elif "search_index" in status:
                state="search_index_excerpt_only_not_full_instructions"
            elif "historical" in status:
                state="held_historical_solar_instruction_source"
            elif "directory" in status:
                state="held_county_directory_link_not_full_instructions"
            elif "non_substantive" in status:
                state="captured_without_substantive_process_content"
            elif "general" in status:
                state="held_general_county_source_not_solar_specific"
            elif status == "captured_narrow_substantive_instruction":
                state="held_narrow_solar_instruction_not_full_guide"
            elif status in {"held_substantive","solar_specific_source","held_solar_specific",
                            "held_full_transformed_instruction_body","held_full_publisher_instruction_body"}:
                state="held_solar_instruction_source"
            else:
                state="source_status_requires_interpretation"
            instructions.append({"row_id":rid("instruction",{"path":binding["path"],"record":at}),
                "county":record["county"],"source_family":"county_public_instructions",
                "source_type":"agency_public_instruction","capture_state":state,
                "compiler_binding":{**binding,"locator":f"$.records[{at}]"},
                "model_route":"retained_instruction_layer_not_yet_a_structure_or_timing_likelihood",
                "parsed_action_records_not_step_count":len(record.get("actions",[])),
                "original":record})
    instruction_counties={r["county"] for r in instructions}
    accounting["instruction_sources"]=len(instructions)
    accounting["instruction_counties_attempted"]=len(instruction_counties)
    accounting["instruction_capture_states"]=dict(Counter(r["capture_state"] for r in instructions))
    for row in frame:
        row["instruction_capture_states"]=[r["capture_state"] for r in instructions if r["county"]==row["county"]]
        row["instruction_scope_qualification"]="County authority only, not a substitute for every municipal AHJ in this county"
    out={"schema_version":"solar-county-evidence/1", "instruction_evidence":instructions,
         "source_timing_fit_status": timing_fit_status(timing),
         "compiler_revision_note":[
             "Normalized forum bounds are always calendar_days; original_units is retained separately.",
             "Time era uses declared date/year fields only; free-text and identifiers are not regex-mined.",
             "County weights preserve geography_unresolved_weight when candidate AHJs do not map.",
             "Each forum row carries exact consumption, clock-spec, semantic-packet, claim-id and source-ref selection provenance.",
             "Explicit soft county-assignment priors override less-specific source-packet location fields; unassigned mass is preserved.",
             "forum_weighted_readings sums candidate weights; forum_candidate_readings counts distinct readings with this county as a candidate."
         ],
         "provenance":provenance,"county_frame":frame,"administrative_observations":admin,"forum_observations":forum,"routes":routes,"accounting":accounting}
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(accounting,indent=2))

if __name__=="__main__": main()
