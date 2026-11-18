"""SOL002 whole-thread review staging packet and explicit timing records."""
from __future__ import annotations
import csv, hashlib, json
from .solar_forum_bridge import BLOCK, PANEL, ROOT, slug
from .solar_forum_review_sol001 import _quote

THREADS = "10gglh6 11ecjnu 12o535f 177vdj6 17hohne 1au08k0 1awl5ln 1chqqg5 1df4lx7 1dvj6x7 1e01h44 1f3oomm 1fpgzgz 1gcutaz 1hfgwsg 1hh9fk0 1k0axx1 1k1hnsh 1kfuowa 1kjgg12".split()
RAW = ROOT / "runs/solar_forum_20260922/acquisition/forum/posts"
OUT = ROOT / "runs/solar_forum_20260922/model_bridge/parse"

# Only initiated first-hand solar journeys. Planned projects, general policy,
# non-solar permits, professional aggregates and out-of-state cases stay coverage.
SPECS = [
 ("11ecjnu","TheCandyManisHere","San Diego, CA",{"solar_permit__ahj_permit_issuance":"what was approved on my permit","solar_permit__ahj_final_inspection":"It didn’t pass the first two times","solar_permit__ahj_reinspection":"It passed the third time","solar_permit__ahj_final_approval":"It passed the third time"},"Own San Diego project; later authoritative-root follow-up reports two failed virtual inspections and a third passing inspection."),
 ("11ecjnu","ocsolar","My installer went the next day",{"solar_permit__permit_revision":"updated the permit with changes"},"Own installation; permit revision occurred."),
 ("12o535f","pharmdjt","Central California",{"solar_permit__ahj_permit_application_submission":"installer applies for city permit","solar_permit__ahj_permit_issuance":"city approves permit"},"Own initiated project with dated city permit submission and approval."),
 ("17hohne","Accomplished_Tea7781","CA",{"solar_permit__ahj_final_inspection":"Solar Inspection that failed"},"Own failed final inspection; changes and any repeat inspection are future."),
 ("1chqqg5","mcfuzzum","California code",{"solar_permit__ahj_final_inspection":"Inspection failed"},"Own failed inspection; no repeat inspection yet."),
 ("1df4lx7","BlueRocker22","PG&E in California",{"solar_permit__ahj_final_inspection":"initial passing of inspections"},"Own operational system; reports inspections passed before utility provisioning dispute."),
 ("1df4lx7","Jenos00","CPUC contact",{},"Own utility dispute/PTO experience; retained for timing, no AHJ act."),
 ("1df4lx7","FredAkbar","PG&E application status",{},"First-hand homeowner with installed system and later PTO update; no AHJ act narrated."),
 ("1dvj6x7","mcfuzzum","PG&E",{},"Own system with recent utility PTO; no AHJ action narrated."),
 ("1fpgzgz","Longjumping-Night339","PGE",{"solar_permit__ahj_final_approval":"it was closed on their end"},"Own new-build project; city reports its approval/closeout completed."),
 ("12o535f","Chris4AMC_TO-DA-MOON","PGE application",{"solar_permit__ahj_final_inspection":"passed city inspection","solar_permit__ahj_final_approval":"passed city inspection"},"Own completed city inspection and subsequent PG&E PTO case."),
 ("1k1hnsh","buncle","Oakland CA",{"solar_permit__ahj_final_inspection":"partially failed inspection"},"Own Oakland solar inspection failed in part; no repeat yet."),
 ("1kfuowa","bchainsbuz","building permit (instantly approved)",{"solar_permit__ahj_permit_issuance":"building permit (instantly approved)"},"Own initiated project; building permit issued, fire approval pending."),
]

# thread, author, start, end, value/lower/upper/unit/status, quote
TIMING = [
 ("11ecjnu","ocsolar","installation_with_equipment_change","permit_revision_visit",1,None,None,"calendar_days","complete","went the next day and updated the permit"),
 ("11ecjnu","TheCandyManisHere","first_virtual_inspection","city_approval_after_third_virtual_inspection",2,None,None,"calendar_days","complete_approximate","only delayed city approval by two-ish days"),
 ("12o535f","pharmdjt","permit_submission","permit_approval",20,None,None,"calendar_days","complete","On 2/24, installer applies for city permit"),
 ("12o535f","amro340","complete_final_inspection_packet_submission","utility_pto",11,None,None,"calendar_days","complete_aggregate_customers","they took 11 days for PTO"),
 ("12o535f","Chris4AMC_TO-DA-MOON","utility_application_submission_after_city_inspection","utility_pto",18,None,None,"calendar_days","complete_approximate","after waiting for like 18 days"),
 ("1df4lx7","Jenos00","cpuc_contact","utility_pto",1,None,None,"calendar_days","complete","PTO the next day"),
 ("1df4lx7","FredAkbar","utility_ppi_test","utility_pto",18,None,None,"calendar_days","complete","PG&E emailed me today granting full PTO"),
 ("1fpgzgz","Longjumping-Night339","home_close","utility_pto",None,53,None,"calendar_days","right_censored","approaching day 60"),
 ("1kfuowa","bchainsbuz","contract_and_deposit","installation_start",None,40,None,"calendar_days","right_censored","It's now day 40"),
]

def build():
    jurisdictions=[]; county={}
    with PANEL.open(newline="",encoding="utf-8") as h:
        for r in csv.DictReader(h):
            if r["owner_scope"]=="ahj":
                j=slug(r["owner_name"]); jurisdictions.append(j); county[j]=r["county"]
    jurisdictions=sorted(set(jurisdictions)); episodes=[]; timing=[]
    blobs={}
    def source(thread):
        if thread not in blobs:
            p=RAW/f"{thread}.json"; blobs[thread]=(p,json.loads(p.read_text()),hashlib.sha256(p.read_bytes()).hexdigest())
        return blobs[thread]
    for thread,author,context,positives,note in SPECS:
        p,b,d=source(thread); cref=_quote(b,author,context,p,d)
        q={s:_quote(b,author,t,p,d) for s,t in positives.items()}; eid=f"reddit_{thread}__{author}__installation_1"
        resolved={("11ecjnu","TheCandyManisHere"):"san_diego_city",("1k1hnsh","buncle"):"oakland_city"}.get((thread,author))
        if resolved: candidates=[]
        elif "central california" in context.lower():
            candidates=[{"jurisdiction_id":j,"prior_weight":1.0} for j in jurisdictions if county[j] in {"Fresno","Kern","Kings","Madera","Merced","San Joaquin","Stanislaus","Tulare"}]
        else: candidates=[{"jurisdiction_id":j,"prior_weight":1.0} for j in jurisdictions]
        episodes.append({"episode_id":eid,"thread_id":thread,"author":author,"dependence_group_id":eid,
          "identity_scope_id":eid,"identity_scope_refs":[{"path":str(p.relative_to(ROOT)),"sha256":d,"locator":f"$case[{json.dumps(eid)}]"}],
          "root_adopted":False,"complete_capture_read":True,"actor_and_lifecycle_reviewed":True,"occurrence_reviewed":True,"statistic":"individual",
          "reading_scope_kind":"complete_fixed_universe","reviewed_step_ids":BLOCK,"jurisdiction_id":resolved,"county_quotes":[cref] if resolved else [],
          "assignment_prior_kind":"reviewed_candidate_weights","assignment_prior_basis":"Explicit city resolved where stated; otherwise uniform over reviewed Central California context or broad California, never utility-install volume.",
          "identity_context_quotes":[cref],"candidates":candidates,
          "readings":[{"step_id":s,"detected":s in q,"quotes":[q[s]] if s in q else []} for s in BLOCK],
          "review_metadata":{"semantic_note":note,"no_mention_means":"reviewed_nondetection_not_absence"}})
    for thread,author,start,end,value,lower,upper,unit,status,text in TIMING:
        p,b,d=source(thread); qr=_quote(b,author,text,p,d)
        timing.append({"thread_id":thread,"author":author,"case_id":f"reddit_{thread}__{author}__installation_1",
          "clock_start":start,"clock_end":end,"value":value,"lower":lower,"upper":upper,"unit":unit,"status":status,
          "source_refs":[qr],"qualification":"Timing retained separately from AHJ occupancy; professional/aggregate rows are explicitly labelled."})
    adopted_threads={e["thread_id"] for e in episodes}
    routes={"1awl5ln":"out_of_scope_municipal_street_lighting","1hfgwsg":"out_of_state_north_carolina",
            "1f3oomm":"out_of_scope_hvac","1gcutaz":"out_of_scope_shed_permit","1kjgg12":"not_initiated_water_heater",
            "10gglh6":"procedural_policy_faq","177vdj6":"not_initiated","1au08k0":"not_initiated",
            "1e01h44":"roof_sales_question_no_ahj_episode","1hh9fk0":"tax_question_not_initiated","1k0axx1":"ev_permit_issue_not_solar_ahj"}
    coverage=[{"thread_id":t,"route":routes.get(t,"reviewed_with_episode" if t in adopted_threads else "reviewed_no_individual_episode")} for t in THREADS]
    packet={"schema_version":"reviewed-forum-occupancy-episodes/1","packet_id":"reviewed_sol002","root_adopted":False,
      "dependence_reviewed":True,"dependence_qualification":"One unit per author-installation; updates merged; professional aggregates and procedural claims excluded from occupancy.",
      "selected_thread_count":20,"jurisdictions":jurisdictions,"episodes":episodes,"timing_records":timing,
      "review_status":"unadopted_interim_awaiting_root_spot_check"}
    return packet,coverage

def main():
    OUT.mkdir(parents=True,exist_ok=True); p,c=build()
    (OUT/"reviewed_sol002.json").write_text(json.dumps(p,indent=2)+"\n")
    (OUT/"reviewed_sol002_coverage.md").write_text("# SOL002 coverage\n\n"+"\n".join(f"- `{x['thread_id']}` — {x['route']}" for x in c)+"\n")
    print(json.dumps({"threads":len(c),"episodes":len(p["episodes"]),"timing_records":len(p["timing_records"]),"positives":sum(r["detected"] for e in p["episodes"] for r in e["readings"])},indent=2))
if __name__=="__main__": main()
