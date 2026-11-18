"""Assemble adopted forum packets with approved same-installation linkages; never fits."""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from .solar_sources import ROOT

B=ROOT/"runs/solar_forum_20260922/model_bridge/parse"
INPUTS=[ROOT/"runs/solar_forum_20260922/parse/reviewed_root001.json",ROOT/"runs/solar_forum_20260922/parse/reviewed_root002.json",B/"reviewed_sol001_geo_corrected.json",B/"reviewed_sol002_geo_corrected.json",B/"reviewed_sol003.json"]
LINK={
 "chris4amc_to-da-moon":"chris4amc_2023", "mcfuzzum":"mcfuzzum_2023", "andy2na":"andy2na_2023",
 "random_fotographer":"random_fotographer_2023", "acefr":"acefr_2023",
}
def author(e):
 if e.get("author"): return e["author"]
 m=re.match(r"reddit_[^_]+__(.+?)__installation",e["episode_id"],re.I); return m.group(1) if m else e["episode_id"]
def merge(a,b):
 a["identity_scope_refs"]+=b.get("identity_scope_refs",[]); a.setdefault("linked_report_episode_ids",[]).append(b["episode_id"])
 a.setdefault("linked_thread_ids",[]).append(b.get("thread_id") or b["episode_id"].split("__")[0].removeprefix("reddit_"))
 by={r["step_id"]:r for r in a["readings"]}
 for r in b["readings"]:
  z=by[r["step_id"]]; z["detected"]=z["detected"] or r["detected"]; z["quotes"]+=r.get("quotes",[])
 seen={x["jurisdiction_id"] for x in a.get("candidates",[])}
 a.setdefault("candidates",[]).extend(x for x in b.get("candidates",[]) if x["jurisdiction_id"] not in seen)
 return a
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--external",action="store_true"); args=ap.parse_args()
 inputs=list(INPUTS)
 if args.external: inputs.append(ROOT/"runs/solar_forum_20260922/parse/reviewed_external001.json")
 ps=[json.loads(x.read_text()) for x in inputs]; eps=[]; desc=[]; groups={}
 for p in ps:
  desc+=p.get("descriptive_episodes",[])
  for e0 in p["episodes"]:
   e=copy.deepcopy(e0); au=author(e); key=LINK.get(au.casefold(),e["episode_id"])
   if key in groups: groups[key]=merge(groups[key],e)
   else: groups[key]=e; eps.append(e)
 # One ROOT002 author explicitly reported two distinct installations.  Give the
 # already-reviewed systems distinct canonical scope locators while preserving
 # the same immutable source file and author provenance.
 for e in eps:
  if e["episode_id"].startswith("reddit_12tnelt__dogeborks__installation_"):
   for ref in e["identity_scope_refs"]: ref["locator"] += ":" + e["episode_id"].rsplit("__",1)[-1]
 for e in eps:e["root_adopted"]=True
 version="003" if args.external else "002"
 out={"schema_version":"reviewed-forum-occupancy-episodes/1","packet_id":"reviewed_combined"+version,"root_adopted":True,"dependence_reviewed":True,"dependence_qualification":"Actor-installation units reviewed across packets; five approved cross-thread same-installation linkages merge readings and provenance into one likelihood unit. External001 cases are independently reviewed units.","jurisdictions":ps[0]["jurisdictions"],"episodes":eps,"descriptive_episodes":desc,"selected_thread_count":sum(p.get("selected_thread_count",0) for p in ps),"scope_status":"interim_reviewed_forum_expansion","linkage_receipt":"runs/solar_forum_20260922/model_bridge/parse/combined002_linkage_receipt.json","interpretation_guards":["Eleven indicators are not additive applicant encounters.","Survey Required=No is not global process absence.","Unknown-national and out-of-frame narratives do not enter California occupancy."]}
 path=B/f"reviewed_combined{version}.json"; path.write_text(json.dumps(out,indent=2)+"\n")
 rec={"inputs":[{"path":str(x.relative_to(ROOT)),"sha256":hashlib.sha256(x.read_bytes()).hexdigest()} for x in inputs],"raw_eligible_reports":sum(len(p["episodes"]) for p in ps),"linked_installations":len(eps),"descriptive_reports":len(desc),"checklist_rows":sum(len(e["readings"]) for e in eps),"fit_launched":False}
 (B/f"reviewed_combined{version}_receipt.json").write_text(json.dumps(rec,indent=2)+"\n"); print(rec)
if __name__=="__main__":main()
