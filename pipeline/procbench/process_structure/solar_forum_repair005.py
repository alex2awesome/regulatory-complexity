"""Bounded semantic successor for Luna decisions003; preserves the original."""
from __future__ import annotations
import json
from .solar_sources import ROOT

OUT=ROOT/"runs/solar_forum_20260922/parse"
THREADS=["102ipmy","1098hkv"]
EPISODES=[
 {"thread":"102ipmy","author":"Bigtoddhere","utility":"PGE","location":"California utility stated by actor; exact AHJ unknown","context":["j2u1zxe","j2uep2h"],"actions":{},"timing":[],"qualitative_timing":[{"clock":"installation_weather_delay","wording":"being delayed on installation","status":"pending","refs":["j2u1zxe"]}],"note":"Own existing NEM2 system upgrade. PG&E is explicit in the actor's own comment, not inherited."},
 {"thread":"102ipmy","author":"ocsolar","inherited_context":True,"context":["j2vlel7"],"actions":{},"timing":[],"note":"Own operating solar-plus-battery case is established by first-person load shifting and battery capacity; no AHJ occurrence narrated."},
 {"thread":"102ipmy","author":"railroader44","inherited_context":True,"context":["j2wk005","j2xzfkl"],"actions":{},"timing":[],"note":"Own initiated 5.5kW project ('in the process now'); no completed AHJ occurrence narrated."},
 {"thread":"102ipmy","author":"jukaszor","utility":"PGE","inherited_context":True,"context":["j3rou42","j3ui9n5"],"actions":{},"timing":[],"qualitative_timing":[{"clock":"installation_month","month":"2020-12","status":"event_timestamp_not_elapsed_duration","refs":["j3rou42"]}],"note":"Own operating 4.1kW system inherited with the home plus active expansion decision. Existing installation is lifecycle context, not an AHJ action."},
 {"thread":"102ipmy","author":"mcdev16","utility":"PGE","inherited_context":True,"context":["j4502an","j456z5d"],"actions":{},"timing":[],"note":"Initiated DIY design/application journey with contractor-license access and concrete system questions; not required to be installed to count as initiated."},
 {"thread":"1098hkv","author":"Microfiber13","location":"Santa Cruz regional context","candidate_counties":["Santa Cruz"],"context":["j3wtfuc"],"actions":{},"timing":[],"note":"Own completed Alterra solar system; installation is lifecycle evidence, not one of the fixed AHJ actions."},
 {"thread":"1098hkv","author":"Dapper-Jellyfish7663","location":"Santa Cruz regional context","candidate_counties":["Santa Cruz"],"context":["j3x1tyf"],"actions":{},"timing":[],"qualitative_timing":[{"clock":"utility_permission_timestamp","wording":"got approval last week to turn on","status":"event_timestamp_not_elapsed_duration","refs":["j3x1tyf"]}],"note":"Clean Roofing being out of San Jose and GAF being made there do not identify the applicant AHJ. Approval to turn on is treated as likely utility PTO, not AHJ final approval."},
 {"thread":"1098hkv","author":"ArcticKitty","location":"Felton explicitly stated","candidate_counties":["Santa Cruz"],"context":["j3xs0qu"],"actions":{},"timing":[],"note":"Own initiated Alterra consultation and planning journey; installation need not have begun."},
 {"thread":"1098hkv","author":"foreverburning","location":"Santa Cruz regional context","candidate_counties":["Santa Cruz"],"context":["j3xtl26","j4lw942"],"actions":{},"timing":[],"qualitative_timing":[{"clock":"battery_outage_endurance_nonprocess","wording":"after one full day without power, were still at 64%","status":"capability_not_process_delay","refs":["j3xtuxe"]}],"note":"Own operating Sunrun/Costco system. Fire_Woman's reply is another author and is not part of this identity scope."},
 {"thread":"1098hkv","author":"buckaroob88","location":"Santa Cruz regional context","candidate_counties":["Santa Cruz"],"context":["j3wzxui","j3xv2ie"],"actions":{},"timing":[],"note":"Own operating solar+battery system, explicitly described as powering fridge/internet during outage; no AHJ occurrence narrated."},
 {"thread":"1098hkv","author":"slugstructor","utility":"PGE","location":"Santa Cruz explicitly stated","candidate_counties":["Santa Cruz"],"context":["j3xuq2b"],"actions":{"ahj_permit_issuance":["j3xuq2b"]},"timing":[],"qualitative_timing":[{"clock":"Sunrun_removal_to_pickup","wording":"left it in my yard for months","status":"lexical_coarsening_nonagency","refs":["j3xuq2b"]},{"clock":"Tesla_attempted_install_to_cancellation","wording":"heard nothing from them for months. I finally cancelled","status":"lexical_coarsening_cancelled","refs":["j3xuq2b"]},{"clock":"Allterra_contact_to_installation","wording":"installed within weeks of first contact","status":"lexical_coarsening_complete","refs":["j3xuq2b"]}],"note":"One property and one applicant episode with three linked vendor journeys. No numeric month/week count is imputed; Tesla cancellation is not zero time. Allterra literally obtained a permit, supporting issuance only."},
 {"thread":"1098hkv","author":"JHoolo","location":"Santa Cruz regional context","candidate_counties":["Santa Cruz"],"context":["j3z83ov"],"actions":{},"timing":[],"note":"Own operating Alterra solar system; proposed future battery does not create a completed battery journey or AHJ action."}
]

ROUTES={
 "IntentionalFuturist":"professional_or_faq_summary","secret-squirrle":"prospective_diy_question","SF_Dubs":"prospective_addition","jayhp82":"potential_installer_question",
 "LamentRedHector":"prospective_not_initiated","inorbit222":"generic_advice","snatacruz":"generic_advice","Fire_Woman":"another_author_battery_interest",
}
def main():
 case={(e["thread"],e["author"].casefold()) for e in EPISODES}; dispositions=[]
 for t in THREADS:
  d=json.loads((ROOT/f"runs/solar_forum_20260922/acquisition/forum/posts/{t}.json").read_text()); authors=[]
  for a in [d["post"].get("author")]+[c.get("author") for c in d.get("comments",[])]:
   if a and a!="[deleted]" and a.casefold() not in {x.casefold() for x in authors}:authors.append(a)
  for a in authors:
   if (t,a.casefold()) in case: route="firsthand_episode"
   else: route=ROUTES.get(a,"reviewed_no_own_initiated_installation_or_procedural_secondhand")
   dispositions.append({"thread":t,"author":a,"route":route})
 packet={"schema_version":"solar-semantic-decisions/1","packet_id":"solar_decisions005","reviewer":"sol_bridge","adoption_state":"staged_unadopted","scope":"Two complete canonical trees 102ipmy and 1098hkv read once; corrected successor to preserved luna_decisions003.json.","threads":THREADS,"assumptions":["Applicant geography is actor-specific; contractor/manufacturer location is not an AHJ.","Utility PTO is not AHJ final approval.","Lexical months/weeks are retained without invented numeric counts.","Installation is lifecycle context, not one of the fixed eleven AHJ actions.","An active consultation, design, or application journey is initiated even before installation."],"episodes":EPISODES,"other_dispositions":dispositions}
 (OUT/"sol_decisions005.json").write_text(json.dumps(packet,indent=2)+"\n")
 receipt={"source_preserved":"runs/solar_forum_20260922/parse/luna_decisions003.json","successor":"runs/solar_forum_20260922/parse/sol_decisions005.json","threads":THREADS,"episodes":len(EPISODES),"author_dispositions":len(dispositions),"numeric_elapsed_timings":0,"repairs":["Removed San Jose as Dapper applicant AHJ; used Santa Cruz regional prior.","Reclassified approval last week as utility-PTO timestamp, not a one-week interval or AHJ final approval.","Removed invented 3-month/3-week values from slugstructor; retained lexical coarsening and three linked vendor journeys in one property episode.","Removed cross-author Fire_Woman reference from foreverburning identity and classified outage endurance as capability.","Made Bigtoddhere PG&E actor-explicit.","Removed installation pseudo-actions; added initiated ArcticKitty and own operating/initiated ocsolar, railroader44, jukaszor, mcdev16, buckaroob88, and JHoolo episodes."]}
 (OUT/"sol_decisions005_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 (OUT/"sol_decisions005_coverage.md").write_text("# SOL decisions 005 coverage\n\n- Full trees read once: `102ipmy`, `1098hkv`.\n- Firsthand episodes: "+str(len(EPISODES))+".\n- Numeric elapsed process durations: 0.\n- Lexical/coarse waits and capability statements remain under `qualitative_timing`.\n\n## All-author dispositions\n\n"+"\n".join(f"- `{x['thread']}` `{x['author']}` — {x['route']}" for x in dispositions)+"\n")
 print({"episodes":len(EPISODES),"authors":len(dispositions),"numeric_timings":0})
if __name__=="__main__":main()
