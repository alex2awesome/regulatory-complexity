"""Actor-level California-frame correction for the staged SOL001/SOL002 packets."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from .solar_sources import ROOT

BASE=ROOT/"runs/solar_forum_20260922/model_bridge/parse"
UNKNOWN={
 ("reviewed_sol001","10ez6hd","treo650"),
 ("reviewed_sol002","11ecjnu","ocsolar"),
}
INFERRED={
 ("reviewed_sol001","10bdub6","SisyphusRuns"):"SGIP program context",
 ("reviewed_sol001","10h78kd","Puzzleheaded_Look959"):"NEM2 parent context",
 ("reviewed_sol001","11102ka","YoungGrassahsh"):"PG&E service context",
 ("reviewed_sol001","1240ozt","Chris4AMC_TO-DA-MOON"):"PG&E service context",
 ("reviewed_sol001","15gur8l","TransportationNo8071"):"NEM2 deadline context",
 ("reviewed_sol001","15hitou","Logical-Specific2573"):"Los Angeles parent context",
 ("reviewed_sol001","1aezusd","Original1620"):"California CSLB complaint",
 ("reviewed_sol002","1df4lx7","Jenos00"):"PG&E CPUC context",
 ("reviewed_sol002","1df4lx7","FredAkbar"):"PG&E application context",
 ("reviewed_sol002","1dvj6x7","mcfuzzum"):"PG&E tariff context",
 ("reviewed_sol002","1fpgzgz","Longjumping-Night339"):"PG&E service context",
 ("reviewed_sol002","12o535f","Chris4AMC_TO-DA-MOON"):"PG&E application context",
 ("reviewed_sol001","11azrsl","holdyourthrow"):"r/bayarea parent context",
 ("reviewed_sol002","1kfuowa","bchainsbuz"):"r/bayarea parent context",
}

def main():
 for stem in ("reviewed_sol001","reviewed_sol002"):
  src=BASE/f"{stem}.json"; p=json.loads(src.read_text()); kept=[]; desc=list(p.get("descriptive_episodes",[])); review=[]
  source_for_bay=p if stem=="reviewed_sol001" else json.loads((BASE/"reviewed_sol001.json").read_text())
  bay_candidates=next(e["candidates"] for e in source_for_bay["episodes"] if len(e.get("candidates",[]))==95)
  for e in p["episodes"]:
   key=(stem,e["thread_id"],e["author"]); quote=(e.get("identity_context_quotes") or [None])[0]
   if key in UNKNOWN:
    cls,basis="unknown_national","no actor location"
    e["occupancy_eligible"]=False; e["candidates"]=[]; desc.append(e)
   else:
    cls="inferred_california" if key in INFERRED else "explicit_california"
    basis=INFERRED.get(key,"direct California location")
    if basis=="r/bayarea parent context":
     raw=ROOT/f"runs/solar_forum_20260922/acquisition/forum/posts/{e['thread_id']}.json"; sha=hashlib.sha256(raw.read_bytes()).hexdigest()
     quote={"path":str(raw.relative_to(ROOT)),"sha256":sha,"json_path":"$.post.subreddit","char_start":0,"char_end":7,"quote":"bayarea"}
     e["identity_context_quotes"]=[quote]; e["candidates"]=json.loads(json.dumps(bay_candidates))
    kept.append(e)
   review.append({"thread_id":e["thread_id"],"author":e["author"],"geography_class":cls,"basis":basis,"source_quote":quote})
  p["episodes"]=kept; p["descriptive_episodes"]=desc; p["geography_review"]=review
  p["packet_id"]=stem+"_geo_corrected"; p["root_adopted"]=True; p["review_status"]="root_adopted_geography_corrected"
  for e in kept:e["root_adopted"]=True
  out=BASE/f"{stem}_geo_corrected.json"; out.write_text(json.dumps(p,indent=2)+"\n")
  print(stem,{"eligible":len(kept),"descriptive":len(desc)})

if __name__=="__main__":main()
