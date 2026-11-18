"""One-pass SOL004 review of ten unread complete local-California threads."""
from __future__ import annotations
import csv,hashlib,json
from .solar_sources import ROOT
from .solar_forum_bridge import BLOCK,PANEL,slug
from .solar_forum_review_sol001 import _quote

IDS="10gecn7 10kgiqh 10vkvxi 11vxrhs 12bn8vv 13pb2n3 14dmcqs 14ebxln 14laerr 14n2duz".split()
RAW=ROOT/"runs/solar_forum_20260922/acquisition/forum/posts"; OUT=ROOT/"runs/solar_forum_20260922/model_bridge/parse"
# thread, author, actor/lifecycle quote, observed AHJ actions, note
CASES=[
 ("10gecn7","D_D","I'm trying to get 4.8kW permitted",{"solar_permit__ahj_plan_review":"City just got back and asked for our roof plan"},"Submitted plans are under city review; requested roof plan is not treated as a completed resubmittal."),
 ("10gecn7","Impressive_Mess_7332","I've had solar panels for more than 10 years",{},"Own operating system; no AHJ occurrence narrated."),
 ("10gecn7","aw_7808","mine included",{},"Own operating system in SF; no AHJ occurrence narrated."),
 ("10kgiqh","SJPunx","we got it installed 1-1/2 years ago",{},"Own installed system; no AHJ occurrence narrated."),
 ("10kgiqh","uberlife","My prior 2019 experience with Tesla",{"solar_permit__ahj_final_approval":"permit sign off"},"Own prior installation; generic permit sign-off supports final approval, not plan review."),
 ("10kgiqh","AliveButterscotch319","I went with Solar Optimum a few months ago",{},"Own installed system; no AHJ occurrence narrated."),
 ("10kgiqh","richfei","I'm in San Jose and I'm another satisfied Solar Optimum customer",{},"Own installed San Jose system; no AHJ occurrence narrated."),
 ("10vkvxi","daquint","I recently got solar",{},"Own installed SF system; billing issue only."),
 ("11vxrhs","wjean","I am in the process of adding solar",{},"Own initiated SF system; no completed AHJ occurrence narrated."),
 ("11vxrhs","AlfaNovember","We have a battery",{},"Own operating system; no AHJ occurrence narrated."),
 ("12bn8vv","s0phr0syn3","ultimately purchased solar through Tesla",{},"Own initiated system; utility application approval is not promoted to an AHJ action."),
 ("12bn8vv","goldengig","We got our solar energy installation done",{},"Own installed regional system; no AHJ occurrence narrated."),
 ("14dmcqs","treeforface","June 2023 vs 2022",{},"Own operating Orange County system; no AHJ occurrence narrated."),
 ("14ebxln","luniz97","I went with Tesla",{},"Own installed system; no AHJ occurrence narrated."),
 ("14ebxln","sotzo3","The installation took a few hours",{},"Own installed system; no AHJ occurrence narrated."),
 ("14laerr","sugah560","5 months to get me up and running",{},"Own completed Bay Area installation; no specific AHJ occurrence narrated."),
 ("14laerr","Tropical-Gaijin","Using them for 6 months now",{},"Own operating system; no AHJ occurrence narrated."),
]
TIMINGS=[
 ("10gecn7","D_D","plan_submission","plan_review_still_open",None,3,None,"months","right_censored_coarse","Plans were submitted in October. City just got back"),
 ("10kgiqh","uberlife","nem_paperwork_process_unspecified_start","nem_application_paperwork_complete",9,None,None,"calendar_days","complete_reported","Nine days"),
 ("14ebxln","sotzo3","physical_installation_start","physical_installation_complete",None,None,1,"calendar_days","interval_upper_coarse","The installation took a few hours"),
 ("14laerr","sugah560","installer_engagement_unspecified_start","system_up_and_running",5,None,None,"months","complete_coarse","5 months to get me up and running"),
]

def main():
 base=json.loads((OUT/"reviewed_sol001.json").read_text()); bay=next(e["candidates"] for e in base["episodes"] if len(e.get("candidates",[]))==95)
 with PANEL.open(newline="",encoding="utf-8") as h: orange=sorted({slug(r["owner_name"]) for r in csv.DictReader(h) if r["owner_scope"]=="ahj" and r["county"]=="Orange"})
 cache={}; episodes=[]; case_auth={(t,a.casefold()) for t,a,*_ in CASES}
 for t,a,ctx,pos,note in CASES:
  if t not in cache:
   p=RAW/f"{t}.json"; cache[t]=(p,json.loads(p.read_text()),hashlib.sha256(p.read_bytes()).hexdigest())
  p,d,sha=cache[t]; scope=_quote(d,a,ctx,p,sha); qs={s:_quote(d,a,q,p,sha) for s,q in pos.items()}; eid=f"reddit_{t}__{a}__installation_1"
  cs=[{"jurisdiction_id":j,"prior_weight":1.0} for j in orange] if (t,a)==("14dmcqs","treeforface") else bay
  basis="Explicit South Orange County; county-bounded AHJ mixture." if (t,a)==("14dmcqs","treeforface") else "Local California subreddit context; uniform reviewed nine-county Bay Area mixture."
  episodes.append({"episode_id":eid,"thread_id":t,"author":a,"dependence_group_id":eid,"identity_scope_id":eid,"identity_scope_refs":[{"path":str(p.relative_to(ROOT)),"sha256":sha,"locator":f"$case[{json.dumps(eid)}]"}],"root_adopted":False,"complete_capture_read":True,"actor_and_lifecycle_reviewed":True,"occurrence_reviewed":True,"statistic":"individual","reading_scope_kind":"complete_fixed_universe","reviewed_step_ids":BLOCK,"jurisdiction_id":None,"assignment_prior_kind":"reviewed_candidate_weights","assignment_prior_basis":basis,"identity_context_quotes":[scope],"candidates":cs,"readings":[{"step_id":s,"detected":s in qs,"quotes":[qs[s]] if s in qs else []} for s in BLOCK],"review_metadata":{"semantic_note":note,"no_mention_means":"reviewed_nondetection_not_absence"}})
 dispositions=[]
 for t in IDS:
  p=RAW/f"{t}.json"; d=json.loads(p.read_text()); authors=[]
  for a in [d["post"].get("author")]+[c.get("author") for c in d.get("comments",[])]:
   if a and a!="[deleted]" and a.casefold() not in {x.casefold() for x in authors}:authors.append(a)
  for a in authors:
   route="firsthand_episode" if (t,a.casefold()) in case_auth else "reviewed_no_own_initiated_installation_or_procedural_only"
   dispositions.append({"thread_id":t,"author":a,"disposition":route})
 timings=[]
 for t,a,start,end,val,lo,up,unit,status,text in TIMINGS:
  if t not in cache:
   p=RAW/f"{t}.json"; cache[t]=(p,json.loads(p.read_text()),hashlib.sha256(p.read_bytes()).hexdigest())
  p,d,sha=cache[t]; timings.append({"thread_id":t,"author":a,"case_id":f"reddit_{t}__{a}__installation_1","clock_start":start,"clock_end":end,"value":val,"lower":lo,"upper":up,"unit":unit,"status":status,"source_refs":[_quote(d,a,text,p,sha)]})
 packet={"schema_version":"reviewed-forum-occupancy-episodes/1","packet_id":"reviewed_sol004","root_adopted":False,"dependence_reviewed":True,"dependence_qualification":"Ten full local-subreddit trees read once; one unit per own initiated installation.","selected_thread_count":10,"jurisdictions":base["jurisdictions"],"episodes":episodes,"timing_records":timings,"review_status":"staged_unadopted","author_dispositions":dispositions}
 (OUT/"reviewed_sol004.json").write_text(json.dumps(packet,indent=2)+"\n")
 thread_lines="\n".join(f"- `{t}` — full post and authoritative root comments read once" for t in IDS)
 timing_lines="\n".join(f"- `{x['thread_id']}` `{x['author']}`: {x['clock_start']} → {x['clock_end']}; {x['status']}" for x in timings)
 author_lines="\n".join(f"- `{x['thread_id']}` `{x['author']}` — {x['disposition']}" for x in dispositions)
 (OUT/"reviewed_sol004_coverage.md").write_text("# SOL004 coverage\n\n## Ten-thread read boundary\n\n"+thread_lines+"\n\n## Retained timing records (4)\n\n"+timing_lines+"\n\n## All-author dispositions\n\n"+author_lines+"\n")
 print({"threads":10,"episodes":len(episodes),"authors":len(dispositions),"timings":len(timings),"positives":sum(r["detected"] for e in episodes for r in e["readings"])})
if __name__=="__main__":main()
