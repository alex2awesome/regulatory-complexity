"""SOL003 authoritative-comment whole-thread review staging packet."""
from __future__ import annotations
import csv, hashlib, json
from .solar_forum_bridge import BLOCK, PANEL, ROOT, slug
from .solar_forum_review_sol001 import _quote

THREADS=json.loads((ROOT/"runs/solar_forum_20260922/model_bridge/parse/sol003_assignment.json").read_text())["thread_ids"]
RAW=ROOT/"runs/solar_forum_20260922/acquisition/forum/posts"; OUT=ROOT/"runs/solar_forum_20260922/model_bridge/parse"
# thread, author, context quote, occurred AHJ actions, semantic note
SPECS=[
 ("10noov9","dstachio","failed electrical inspection",{"solar_permit__ahj_final_inspection":"failed electrical inspection"},"Own initiated system; one failed inspection followed by an administrative appeal, not a reinspection."),
 ("114rjka","equalizeyou","Permit To Operate",{},"Own operating system; utility/billing problem only."),
 ("11u993g","pluckNstrum","My installer went out of business",{},"Own installed but unfinished system; AHJ occurrence not narrated."),
 ("12kasqs","theBotKilla","from SCE (Southern California Edison)",{"solar_permit__ahj_permit_issuance":"city permit"},"Own Southern California project; city permit supports issuance, not a separately observed plan review."),
 ("12kasqs","mtux96","re-inspection",{"solar_permit__ahj_final_inspection":"re-inspection","solar_permit__ahj_reinspection":"re-inspection"},"Own project undergoing repeat inspection."),
 ("15fd500","8CYLINDERS117","I'm in the South East",{"solar_permit__ahj_permit_issuance":"permit was approved"},"Own initiated Project Solar case in the southeastern US; approval supports issuance only and remains outside the California occupancy frame."),
 ("15fd500","LoofLoofington","1.5 years to install",{},"Own long installation account; no AHJ occurrence in quoted narrative."),
 ("169082p","Excellent-Archer228","passed final",{"solar_permit__ahj_final_inspection":"passed final","solar_permit__ahj_reinspection":"passed final","solar_permit__ahj_final_approval":"passed final"},"Own project passed after earlier failures; repeat path occurred."),
 ("16chldz","mn530","failed inspection yesterday",{"solar_permit__ahj_final_inspection":"failed inspection yesterday"},"Own system; failed inspection occurred. The reported reinspection was only scheduled, so it is not counted as an occurrence."),
 ("185dhq7","cm2460","county inspector had failed",{"solar_permit__ahj_final_inspection":"county inspector had failed"},"Own ground-mount project; county inspection failed."),
 ("1afkq0a","chrisgurn","they failed it",{"solar_permit__ahj_final_inspection":"they failed it"},"Own project; final city electrical inspection failed."),
 ("1g57774","meolclide","failed inspection",{"solar_permit__ahj_final_inspection":"failed inspection"},"One continuing journey also reported in 1ar72g0 and 1axo71u; encoded once. Repair work and county revision approval are not treated as applicant resubmittal or reinspection occurrences."),
 ("1d4eqdl","RustyTromboneSoloist","live in Wisconsin",{"solar_permit__ahj_final_inspection":"failed inspection","solar_permit__ahj_reinspection":"Another failed inspection"},"Own Wisconsin multi-year project with repeated failed inspections; retained as national out-of-frame evidence."),
 ("1d4eqdl","GoneSilent","our big system",{},"Own separate long utility-upgrade/PTO journey; no AHJ act narrated."),
 ("1fk73xn","Odd_Chain8811","Freedom Forever",{},"Own installed/PTO system with later permit and equipment problems; unclear AHJ occurrence is not promoted."),
 ("1g57774","Cowboycasey","took them 5 months",{"solar_permit__permit_revision":"took them 5 months"},"Own separate equipment-change/revision experience."),
]
TIMING=[
 ("10noov9","dstachio","installation","first_failed_inspection",7,None,None,"calendar_days","complete","A week later it failed electrical inspection"),
 ("12kasqs","theBotKilla","permit_submission","permit_approval",13,None,None,"calendar_days","complete","city permit (took it 13 days)"),
 ("12kasqs","theBotKilla","complete_utility_packet","utility_pto",1,None,None,"months","complete","PTO (1 month)"),
 ("15fd500","LoofLoofington","contract_or_design_start","installation",18,None,None,"months","complete_coarse","it took 1.5 years to install"),
 ("16chldz","mn530","failed_inspection","scheduled_reinspection",1,None,None,"calendar_days","scheduled_forecast","It failed inspection yesterday (grounding rod), but they are reinspecting it today"),
 ("1d4eqdl","RustyTromboneSoloist","contract","operational_completion",None,35,None,"months","right_censored","still waiting for solar power"),
 ("1d4eqdl","GoneSilent","utility_interconnection_start","utility_pto",None,24,None,"months","complete_lower_bound","Took 2+ years to get PTO"),
 ("1g57774","meolclide","failed_inspection","county_revision_approval",8,None,None,"months","complete_coarse","took 8 months to get county approval revisions"),
]

# Geography is author/case specific.  A location supplied by some other commenter
# in the same national thread is never inherited by an episode.
GEO={
 ("12kasqs","theBotKilla"):("explicit_california","SCE (Southern California Edison)"),
 ("11u993g","pluckNstrum"):("explicit_out_of_frame","Houston, TX"),
 ("15fd500","8CYLINDERS117"):("explicit_out_of_frame","I'm in the South East"),
 ("1g57774","meolclide"):("explicit_out_of_frame","Virginia"),
 ("1d4eqdl","RustyTromboneSoloist"):("explicit_out_of_frame","live in Wisconsin"),
 ("1fk73xn","Odd_Chain8811"):("explicit_out_of_frame","I am in TX"),
}

def build():
 js=[]
 with PANEL.open(newline="",encoding="utf-8") as h:
  for r in csv.DictReader(h):
   if r["owner_scope"]=="ahj": js.append(slug(r["owner_name"]))
 js=sorted(set(js)); cache={}
 def src(t):
  if t not in cache:
   p=RAW/f"{t}.json"; cache[t]=(p,json.loads(p.read_text()),hashlib.sha256(p.read_bytes()).hexdigest())
  return cache[t]
 eps=[]; descriptive=[]; geo_rows=[]
 for t,a,ctx,pos,note in SPECS:
  p,b,d=src(t); q={s:_quote(b,a,x,p,d) for s,x in pos.items()}; eid=f"reddit_{t}__{a}__installation_1"
  gclass,gtext=GEO.get((t,a),("unknown_national",None)); gquote=_quote(b,a,gtext,p,d) if gtext else None
  cr=gquote or _quote(b,a,ctx,p,d)
  resolved="" 
  episode={"episode_id":eid,"thread_id":t,"author":a,"dependence_group_id":eid,"identity_scope_id":eid,
   "identity_scope_refs":[{"path":str(p.relative_to(ROOT)),"sha256":d,"locator":f"$case[{json.dumps(eid)}]"}],"root_adopted":False,
   "complete_capture_read":True,"actor_and_lifecycle_reviewed":True,"occurrence_reviewed":True,"statistic":"individual","reading_scope_kind":"complete_fixed_universe","reviewed_step_ids":BLOCK,
   "jurisdiction_id":None,"assignment_prior_kind":"reviewed_candidate_weights","assignment_prior_basis":"Permissive broad California/context prior; no exact-department gate and no utility-volume weighting.","identity_context_quotes":[cr],
   "candidates":[{"jurisdiction_id":j,"prior_weight":1.0} for j in js],"readings":[{"step_id":s,"detected":s in q,"quotes":[q[s]] if s in q else []} for s in BLOCK],
   "review_metadata":{"semantic_note":note,"geography_class":gclass,"authoritative_comment_tree":"$.comments","no_mention_means":"reviewed_nondetection_not_absence"}}
  geo_rows.append({"thread_id":t,"author":a,"geography_class":gclass,"geography_quote":gquote})
  if gclass=="explicit_california": eps.append(episode)
  else:
   episode["occupancy_eligible"]=False; episode["candidates"]=[]; descriptive.append(episode)
 timings=[]
 for t,a,st,en,v,lo,up,u,status,text in TIMING:
  p,b,d=src(t); qr=_quote(b,a,text,p,d); gclass=GEO.get((t,a),("unknown_national",None))[0]; timings.append({"thread_id":t,"author":a,"case_id":f"reddit_{t}__{a}__installation_1","clock_start":st,"clock_end":en,"value":v,"lower":lo,"upper":up,"unit":u,"status":status,"geography_class":gclass,"source_refs":[qr]})
 used={e["thread_id"] for e in eps}; routes={"138x5lh":"context_not_safely_california","15ri9u2":"out_of_scope_ev_permit","15sslvs":"out_of_state_florida","179b7sr":"not_initiated","1axo71u":"linked_same_meolclide_journey_as_1g57774","1ar72g0":"linked_same_meolclide_journey_as_1g57774","1dif5y1":"out_of_scope_roof_quote","1ehfuhl":"secondhand_failed_project_not_primary"}
 cov=[{"thread_id":t,"route":routes.get(t,"reviewed_with_episode" if t in used else "reviewed_no_primary_episode")} for t in THREADS]
 return {"schema_version":"reviewed-forum-occupancy-episodes/1","packet_id":"reviewed_sol003","root_adopted":False,"dependence_reviewed":True,"dependence_qualification":"Full refreshed comments read; one unit per author-installation; linked updates merged by retaining one journey.","selected_thread_count":20,"jurisdictions":js,"episodes":eps,"descriptive_episodes":descriptive,"geography_review":geo_rows,"timing_records":timings,"review_status":"unadopted_interim"},cov

def main():
 p,c=build(); OUT.mkdir(parents=True,exist_ok=True); (OUT/"reviewed_sol003.json").write_text(json.dumps(p,indent=2)+"\n"); (OUT/"reviewed_sol003_coverage.md").write_text("# SOL003 coverage\n\n"+"\n".join(f"- `{x['thread_id']}` — {x['route']}" for x in c)+"\n"); print({"episodes":len(p["episodes"]),"descriptive":len(p["descriptive_episodes"]),"timing":len(p["timing_records"]),"positive":sum(r["detected"] for e in p["episodes"] for r in e["readings"])})
if __name__=="__main__": main()
