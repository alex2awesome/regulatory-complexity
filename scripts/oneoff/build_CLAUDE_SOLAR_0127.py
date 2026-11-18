#!/usr/bin/env python3
"""Scratch build script for packet CLAUDE_SOLAR_0127. Unique name per brief
(scratchpad collision warning). Writes decisions.json, timing_staged.json,
coverage.json, manifest.json into the packet directory."""
import json, os, hashlib, datetime

ROOT = "/Users/spangher/Projects/stanford-research/regulatory-complexity"
PACKET_ID = "CLAUDE_SOLAR_0127"
PDIR = os.path.join(ROOT, "runs/solar_forum_20260922/parse/claude_bulk", PACKET_ID)
DEC_PATH = f"runs/solar_forum_20260922/parse/claude_bulk/{PACKET_ID}/decisions.json"

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

# ---------------------------------------------------------------------------
# EPISODES
# ---------------------------------------------------------------------------
episodes = []

def ep(**kw):
    kw.setdefault("same_installation_as", None)
    kw.setdefault("utility", None)
    kw.setdefault("timing", [])
    kw.setdefault("costs", [])
    kw.setdefault("effort", [])
    kw.setdefault("non_registry_actions", [])
    kw.setdefault("source_refs", ["post"])
    kw["decision_case_id"] = f"{kw['thread']}__{kw['author']}"
    episodes.append(kw)

# === THREAD 1ud0zfe ===================================================
ep(thread="1ud0zfe", author="Willing_Mongoose_840",
   lifecycle_stage="installed_awaiting_pto", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none; r/TeslaSolar, no state/utility named",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="No location clue anywhere in OP's posts in this thread.",
   source_refs=["post"],
   timing=[{
       "clock": "install_to_pto", "refs": ["post"], "unit": "weeks", "lower": 3,
       "censoring": "pending_lower_bound|approximate|self_reported",
       "quote": "8.4 kw system with one powerwall installed 3 weeks ago. Working great! Ive found all my powerwall answers here! No PTO so I’ve been geeking out, manipulating variables, checking Tesla app every time a cloud comes by, well you all know the drill.",
       "note": "Post dated 2026-06-22. No PTO yet as of posting; 3 weeks is a floor on install-to-PTO wait, open-ended."
   }])

ep(thread="1ud0zfe", author="Squeezitgirdle",
   lifecycle_stage="operating_with_unresolved_defect_repair_pending", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["otb4d14"],
   non_registry_actions=[{
       "actor": "Tesla", "action": "repair powerwall issue (previously attempted fix failed)",
       "status": "pending", "refs": ["otb4d14"],
       "quote": "Fix mine since tesla won't for several months after the last attempted 'fix'."
   }],
   effort=[], costs=[],
   )
# note: no timing entry -- "several months" has no number, per rule 5 (qualitative only).

# === THREAD 1ud3dnw (Sunnova bankruptcy) ==============================
ep(thread="1ud3dnw", author="fund2016",
   lifecycle_stage="entered_then_stalled_pending_contractor_bankruptcy",
   lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"county planning department\", \"county failing the inspection\" -- county named nowhere, state never given",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="Only a generic 'county' is referenced (planning dept, inspection); no state or county name anywhere in thread.",
   source_refs=["post", "otbb85x", "ot8vg4h", "otkpm52"],
   timing=[{
       "clock": "contract_to_final_permit_approval", "refs": ["otbb85x"],
       "unit": "months",
       "censoring": "pending_lower_bound|year_only|self_reported",
       "supported_event_dates": [
           {"date": "2022", "label": "contracted with Sunnova to install solar system"},
           {"date": "2024-05", "label": "last inspection / correction notice for incomplete electrical and no ladder"}
       ],
       "quote": "The last inspection was May 2024.  The posted correction notice listed incomplete electrical and no ladder as the deficiencies.",
       "note": "Post is dated 2026-06-23; still not resolved. Exact contract month in 2022 unknown, so no numeric duration is computed -- dates preserved instead per field rule 3/4."
   }],
   non_registry_actions=[
       {"actor": "county/AHJ", "action": "final permit review inspection", "status": "explicit_negative",
        "refs": ["otbb85x"],
        "quote": "The last inspection was May 2024.  The posted correction notice listed incomplete electrical and no ladder as the deficiencies."},
       {"actor": "contractor (Sunnova-affiliated)", "action": "respond to correction notice / resume work",
        "status": "explicit_negative", "refs": ["otbb85x"],
        "quote": "We have had no contact with any associated contractors since the notice nor have we been able to reach anyone."},
       {"actor": "applicant", "action": "make loan/lease payments", "status": "explicit_negative",
        "refs": ["ot8vg4h"],
        "quote": "No, not making payments. But have a fully installed system that can’t be permitted. I think there is also a lien on my property."},
       {"actor": "applicant", "action": "research lien on property", "status": "performed",
        "refs": ["otkpm52"], "quote": "Working on researching the lien.."}
   ])

# === THREAD 1ueqhjw (Enphase backup) ===================================
ep(thread="1ueqhjw", author="Delmorath",
   lifecycle_stage="installation_complete_awaiting_final_inspection_and_pto",
   lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"I live in a very rural area\" -- no state/county/utility named",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="Only 'very rural area' stated; no state, utility or city given anywhere in thread.",
   source_refs=["post", "otm5eiv", "otm7f3t", "otmmwn7"],
   timing=[{
       "clock": "research_and_installer_selection_phase", "refs": ["post"], "unit": "years", "value": 3,
       "censoring": "completed_observed|approximate|self_reported",
       "quote": "After 3 years of research, countless phone calls with Enphase, and working through 6-8 different solar companies, I finally found an installer willing to build exactly the system I wanted rather than pushing a standard package.",
       "note": "Self-reported summary duration for the pre-contract research/shopping phase, ending when this installer was selected."
   }, {
       "clock": "install_to_final_inspection_and_pto", "refs": ["post"],
       "censoring": "single_milestone_no_duration|exact_as_stated|self_reported",
       "supported_event_dates": [{"date": "2026-06-24", "label": "post date: installation complete and commissioned, awaiting final inspection and PTO"}],
       "quote": "System installation is complete and commissioned. Awaiting final inspection and PTO.",
       "note": "No PTO/inspection date observed yet as of post (2026-06-24); no duration derivable."
   }],
   effort=[
       {"lower": 6, "upper": 8, "unit": "contractors", "refs": ["post"],
        "censoring": "completed_observed|range_reported|self_reported",
        "quote": "working through 6-8 different solar companies",
        "note": "Number of solar companies evaluated before selecting installer."},
       {"lower": 5, "upper": 6, "unit": "contractors", "refs": ["otm5eiv"],
        "censoring": "completed_observed|range_reported|self_reported",
        "quote": "They gave me a list of five or six platinum installers and I went through all of them until I found the one I liked best.",
        "note": "Enphase-provided installer shortlist that applicant vetted; consistent with the 6-8 figure in the post, given by same author."}
   ],
   costs=[{
       "value": 36500, "unit": "USD", "refs": ["otmmwn7"],
       "note": "Total system price, financed over a 20-year loan; baseline monthly payment $300, incentive-adjusted estimate ~$244/month.",
       "quote": "Total price was 36,500 - I put a few thousand down with a 20 year payoff because I didn't like seeing an uneven number for my monthly payment... Baseline monthly payment 300... With my state incentive, the estimate monthly payment is around 244, which aggravates me because I wanted a round number 245"
   }],
   non_registry_actions=[
       {"actor": "installer", "action": "add critter guard to array (unrequested)", "status": "performed",
        "refs": ["otm7f3t"],
        "quote": "The critter guard was something I actually overlooked and the installer added them anyway."}
   ])

# === THREAD 1ufr883 (Tesla 15% goodwill rebate) ========================
ep(thread="1ufr883", author="Estebe46",
   lifecycle_stage="pto_received_awaiting_vendor_goodwill_rebate", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue anywhere in OP's posts.",
   source_refs=["post", "otuy0ln"],
   timing=[{
       "clock": "pto_to_rebate_check_received", "refs": ["post"], "unit": "weeks", "lower": 8,
       "censoring": "pending_lower_bound|approximate|self_reported",
       "quote": "It's been almost two months since PTO and they're not responding to inquiries.",
       "note": "Tesla had promised the rebate check 4-6 weeks after PTO (per post: 'they said it would take 4 to 6 weeks after PTO'); that promise is a vendor estimate, not an observation, and is exceeded as of this report."
   }],
   non_registry_actions=[
       {"actor": "Tesla", "action": "pay promised 15% goodwill rebate check", "status": "pending",
        "refs": ["post"],
        "quote": "It's been almost two months since PTO and they're not responding to inquiries."}
   ])

ep(thread="1ufr883", author="PhilosopherOther3142",
   lifecycle_stage="pto_received_rebate_check_received", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["otzowva", "owvm7tz"],
   timing=[{
       "clock": "pto_to_rebate_check_received", "refs": ["otzowva", "owvm7tz"],
       "unit": "weeks", "value": 3,
       "censoring": "completed_observed|approximate|self_reported",
       "supported_event_dates": [
           {"date": "2026-06", "label": "PTO received ('last week' as of the 2026-06-26 comment)"},
           {"date": "2026-07-10", "label": "rebate check received ('yesterday' as of the 2026-07-11 comment)"}
       ],
       "quote": "I got PTO last week, emailed them today to submit the request for the 15% rebate. I have been told twice by them that a rebate check will be sent after PTO is received.",
       "note": "Approximate: 'last week' relative to 2026-06-26 is not an exact date; ~3 weeks elapsed to the 2026-07-10 receipt."
   }],
   non_registry_actions=[
       {"actor": "applicant", "action": "submit request for 15% rebate", "status": "performed",
        "refs": ["otzowva"],
        "quote": "I got PTO last week, emailed them today to submit the request for the 15% rebate. I have been told twice by them that a rebate check will be sent after PTO is received."},
       {"actor": "Tesla", "action": "send goodwill rebate check", "status": "performed",
        "refs": ["owvm7tz"], "quote": "FYI, i received my check yesterday."}
   ])

ep(thread="1ufr883", author="Ok_Appeal_4060",
   lifecycle_stage="completed_pto_and_rebate_after_repeated_filing", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["otv31h7"],
   timing=[{
       "clock": "pto_filing_process_start_to_approval", "refs": ["otv31h7"], "unit": "months", "lower": 3,
       "censoring": "completed_observed|approximate|self_reported",
       "quote": "After spending more than 3 months back and forth, spending more than 20 hours with them helping them to file PRO correctly with utility company 3 times until it was approved. they sent me $100 rebate check. ($5 an hour for my time doing their job)",
       "note": "'more than 3 months' is a stated floor on an already-completed process; source uses 'PRO' (likely typo for PTO)."
   }],
   effort=[
       {"lower": 20, "unit": "person_hours", "refs": ["otv31h7"],
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "spending more than 20 hours with them helping them to file PRO correctly with utility company 3 times until it was approved.",
        "note": "Applicant's own time spent helping the vendor file correctly with the utility."},
       {"value": 3, "unit": "rounds", "refs": ["otv31h7"],
        "censoring": "completed_observed|exact_as_stated|self_reported",
        "quote": "helping them to file PRO correctly with utility company 3 times until it was approved.",
        "note": "PTO/interconnection filing was submitted 3 times before acceptance."}
   ],
   costs=[{
       "value": 100, "unit": "USD", "refs": ["otv31h7"],
       "note": "Goodwill rebate check received (incurred/received, not merely quoted).",
       "quote": "they sent me $100 rebate check."
   }],
   non_registry_actions=[
       {"actor": "applicant", "action": "file PTO/interconnection paperwork with utility on vendor's behalf",
        "status": "performed", "refs": ["otv31h7"],
        "quote": "helping them to file PRO correctly with utility company 3 times until it was approved."},
       {"actor": "Tesla", "action": "send goodwill rebate check", "status": "performed",
        "refs": ["otv31h7"], "quote": "they sent me $100 rebate check."}
   ])

ep(thread="1ufr883", author="ryan9751",
   lifecycle_stage="escalated_to_arbitration_award_eventually_paid", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["otx3lqr"],
   timing=[
       {"clock": "arbitration_order_to_actual_payment", "refs": ["otx3lqr"], "unit": "months", "value": 6,
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "I took them to arbitration, and even after they lost and were demanded to pay within 30 days by the arbitrator it took 6 months.",
        "note": "Actual payment took 6 months versus the arbitrator's ordered 30-day deadline."},
       {"clock": "arbitrator_ordered_payment_deadline", "refs": ["otx3lqr"], "unit": "calendar_days", "value": 30,
        "censoring": "policy_deadline_not_observation|exact_as_stated|third_party",
        "quote": "I took them to arbitration, and even after they lost and were demanded to pay within 30 days by the arbitrator it took 6 months.",
        "note": "The 30-day figure is the arbitrator's ordered deadline, not an elapsed time anyone experienced; the observed elapsed time was 6 months (separate entry)."}
   ],
   non_registry_actions=[
       {"actor": "applicant", "action": "file arbitration claim against Tesla", "status": "performed",
        "refs": ["otx3lqr"], "quote": "I took them to arbitration, and even after they lost and were demanded to pay within 30 days by the arbitrator it took 6 months."},
       {"actor": "Tesla", "action": "pay arbitration award", "status": "performed",
        "refs": ["otx3lqr"],
        "quote": "I took them to arbitration, and even after they lost and were demanded to pay within 30 days by the arbitrator it took 6 months.",
        "note": "Paid, but ~6 months after the ordered 30-day deadline."}
   ])

# === THREAD 1ugnnj1 (Shed install) =====================================
ep(thread="1ugnnj1", author="Ninja_Terror",
   lifecycle_stage="pre_application_researching_permit_requirements_two_installers_unresponsive",
   lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given (no state named)", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No state/county/utility named anywhere in OP's comments.",
   source_refs=["post", "ou2k8s8", "ou51ump"],
   non_registry_actions=[
       {"actor": "applicant", "action": "obtain tree removal permit", "status": "planned_not_performed",
        "refs": ["ou2k8s8"], "quote": "I also likely need a permit to remove a tree first."},
       {"actor": "installer (\"EcoFlow enthusiast\", first contact)", "action": "commit to and perform panel install job",
        "status": "refused_by_actor", "refs": ["ou51ump"],
        "quote": "The first guy I found to do my panel install for the EcoFlow was an EcoFlow enthusiast and knew all of the inspectors, nudge, nudge, wink, wink, but he fell off the earth when he talked to his electrician.",
        "note": "Ambiguous: described as going silent ('fell off the earth') rather than an explicit refusal, but effectively ended the engagement."},
       {"actor": "installer (second EcoFlow dealer contact)", "action": "respond about panel install job",
        "status": "refused_by_actor", "refs": ["ou51ump"],
        "quote": "I spoke to another EcoFlow dealer, but I never heard from him again either.",
        "note": "Ambiguous: silence/non-response rather than an explicit refusal."},
       {"actor": "applicant", "action": "contact Electrical Safety Association about DP3 battery certification",
        "status": "performed", "refs": ["ou51ump"],
        "quote": "I contacted the Electrical Safety Association in the beginning asking about the certification for my DP3, as I had my doubts."}
   ])

ep(thread="1ugnnj1", author="LongjumpingGanache40",
   lifecycle_stage="in_process_exterior_conduit_approved_deck_run_uninspected", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given (no state named)", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No state/county/utility named anywhere in this commenter's posts.",
   source_refs=["ou1x6sr"],
   timing=[{
       "clock": "conduit_run_inspection_status", "refs": ["ou1x6sr"],
       "censoring": "single_milestone_no_duration|exact_as_stated|self_reported",
       "supported_event_dates": [{"date": "2026-06-27", "label": "comment date: exterior conduit run under deck not yet inspected"}],
       "quote": "Part of my run is under my deck. Not inspected yet. This part is AC wiring running from Apex 300 in garage to transfer switch in house.",
       "note": "No exact milestone date given beyond comment date; open pending inspection with no duration derivable."
   }],
   non_registry_actions=[
       {"actor": "AHJ inspector", "action": "approve exterior conduit installation", "status": "performed",
        "refs": ["ou1x6sr"],
        "quote": "All exterior conduit is schedule 40 PVC electrical conduit. Was approved by inspector."},
       {"actor": "AHJ inspector", "action": "inspect conduit run located under the deck", "status": "pending",
        "refs": ["ou1x6sr"],
        "quote": "Part of my run is under my deck. Not inspected yet."}
   ])

# === THREAD 1ujym90 (Already Thinking Upgrade) =========================
ep(thread="1ujym90", author="Cultural-Ad4953",
   lifecycle_stage="completed_operating_considering_addon", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   utility="municipal_electric_unspecified",
   location={"raw_clue": "'local utilities (municipal electric in my case)' -- municipality/state never named",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="OP states their own utility is a municipal electric utility but never names which one, city, or state.",
   source_refs=["post", "ousorcd", "ousoxgc"],
   timing=[{
       "clock": "install_to_pto", "refs": ["post"], "unit": "days", "value": 9,
       "censoring": "completed_observed|exact_as_stated|self_reported",
       "supported_event_dates": [
           {"date": "2026-06-01", "label": "solar installed"},
           {"date": "2026-06-10", "label": "PTO given"}
       ],
       "quote": "My solar was installed June 1st, and PTO given June 10th."
   }])

ep(thread="1ujym90", author="Head_Mycologist3917",
   lifecycle_stage="completed_operating_paid_transformer_upgrade_for_addon", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given; this is a different commenter from the OP, own case only.",
   source_refs=["ourt0cd"],
   costs=[{
       "value": 5000, "unit": "USD", "refs": ["ourt0cd"],
       "note": "Utility-required transformer upgrade cost paid by this commenter for their own system expansion (not the OP's case).",
       "quote": "The utility will have sized their side for your system's output. Adding more may mean a transformer upgrade. Which you may or may not have to pay for. Mine was $5k."
   }])

ep(thread="1ujym90", author="Reddit_Bot_Beep_Boop",
   lifecycle_stage="completed_operating_addon_installed_utility_notification_unclear", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["ous1ok1"],
   non_registry_actions=[],
   )
episodes[-1]["note"] = ("Commenter describes adding 12 panels to their own Enphase system and asks "
    "'Why tell the utility at all?' -- phrased as a rhetorical question, not an explicit statement "
    "that the utility was not notified, so no explicit_negative action is recorded per the "
    "explicit-statement-only rule. Quote: 'Adding panels is easy. I did it with my Enphase system by "
    "adding 12 new panels. I maxed out my combiner and landed the other 8 on my main electric panel. "
    "Why tell the utility at all?' [ous1ok1]")

ep(thread="1ujym90", author="OmgNoodles",
   lifecycle_stage="completed_operating_addon_from_second_company", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["ouu6l8y"],
   timing=[{
       "clock": "original_install_milestone", "refs": ["ouu6l8y"],
       "censoring": "single_milestone_no_duration|year_only|self_reported",
       "supported_event_dates": [{"date": "2019", "label": "original Tesla solar install"}],
       "quote": "I was in the same boat and had Tesla do my original install back in 2019.   I was able to get new panels installed by another company for a tad bit cheaper, but overall I hadn't had any real issues and I figured it'd be better for me to let just 1 company do all my solar."
   }])

# === THREAD 1ukjic9 (Maryland electrician needed) ======================
ep(thread="1ukjic9", author="PlentyEfficiency1424",
   lifecycle_stage="pre_application_seeking_electrician_for_diy_ground_mount", lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"northern Maryland (Baltimore County)\" explicit", "resolved_state": "Maryland",
             "resolved_county": "Baltimore County", "candidate_counties": ["Baltimore County"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_maryland"},
   location_evidence="Post explicitly: 'Looking for an electrician in northern Maryland (Baltimore County)'.",
   source_refs=["post"],
   non_registry_actions=[
       {"actor": "applicant", "action": "find electrician willing to pull permit and do final terminations for DIY ground mount",
        "status": "pending", "refs": ["post"],
        "quote": "Need an electrician that will pull the permit and make final wiring terminations at all junctions and wire inverter to main panel."}
   ])

ep(thread="1ukjic9", author="JuniorExperience1767",
   lifecycle_stage="pre_application_seeking_diy_electrician", lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"looking for one here in FL too\" explicit", "resolved_state": "Florida",
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 0.0,
             "scope_label": "out_of_state_florida"},
   location_evidence="Explicit: 'looking for one here in FL too'.",
   source_refs=["ouw85hl"],
   non_registry_actions=[
       {"actor": "applicant", "action": "find electrician for DIY solar", "status": "pending",
        "refs": ["ouw85hl"],
        "quote": "Seem hard to come by... looking for one here in FL too cause I've not been impressed with any of the Pro Installers here so far...I think part of the reason is that just about all of them are roofers turned solar installers"}
   ])

ep(thread="1ukjic9", author="TooGoodToBeeTrue",
   lifecycle_stage="completed_or_operating_prior_diy_ev_charger_permit_via_same_electrician",
   lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"I'm in MoCo\" (Montgomery County, MD)", "resolved_state": "Maryland",
             "resolved_county": "Montgomery County", "candidate_counties": ["Montgomery County"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_maryland"},
   location_evidence="Explicit: 'I'm in MoCo' -- commonly used abbreviation for Montgomery County, MD, consistent with thread being about Maryland.",
   source_refs=["oux2642"],
   non_registry_actions=[
       {"actor": "applicant", "action": "get DIY EV charger outlet reviewed and permitted by a licensed electrician",
        "status": "performed", "refs": ["oux2642"],
        "quote": "We worked out a deal for him to review my DIY EV charger outlet and get it permitted before I had solar done. He's a one man shop."}
   ])

ep(thread="1ukjic9", author="ckoval7",
   lifecycle_stage="pre_application_undecided_electrician_vs_off_grid", lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"in AACO soon\" (Anne Arundel County, MD)", "resolved_state": "Maryland",
             "resolved_county": "Anne Arundel County", "candidate_counties": ["Anne Arundel County"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_maryland"},
   location_evidence="Explicit: 'I'm gonna be in the same boat in AACO soon' -- AACO = Anne Arundel County.",
   source_refs=["ovd1ueh"],
   non_registry_actions=[
       {"actor": "applicant", "action": "decide between hiring an electrician vs. going off-grid",
        "status": "planned_not_performed", "refs": ["ovd1ueh"],
        "quote": "I'm actually on the fence about whether to hope I find an electrician willing to work with me, or just go the off-grid route, but that would be leaving quite a few kWh on the table even with a battery."}
   ])

ep(thread="1ukjic9", author="miketunes",
   lifecycle_stage="pre_application_seeking_electrician", lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"Baltimore City\" explicit", "resolved_state": "Maryland",
             "resolved_county": "Baltimore City", "candidate_counties": ["Baltimore City"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_maryland"},
   location_evidence="Explicit: 'Also looking in Baltimore City for the same.'",
   source_refs=["oux92th"],
   non_registry_actions=[
       {"actor": "applicant", "action": "find electrician for DIY solar", "status": "pending",
        "refs": ["oux92th"], "quote": "Also looking in Baltimore City for the same."}
   ])

# === THREAD 1uli8ne (PSA re Portable Solar) ============================
ep(thread="1uli8ne", author="TooGoodToBeeTrue",
   lifecycle_stage="electrician_secured_for_inspection_signoff_via_barter", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "OP post states 'This pertains to Maryland, your AHJ may have something similar'",
             "resolved_state": "Maryland", "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_maryland"},
   location_evidence="OP explicitly frames the post around Maryland state law; no county given.",
   source_refs=["post", "ovus3m9"],
   non_registry_actions=[
       {"actor": "applicant", "action": "secure licensed electrician for required inspection/sign-off",
        "status": "performed", "refs": ["ovus3m9"],
        "quote": "Numerous people have posted requests to recommend electricians for this exact \"inspection\" however most electricians won't bother with with the effort. I was lucky in that I found one who's services I trade for dog sitting while he is on vacation.",
        "note": "Payment was in-kind (dog-sitting barter), not cash; no USD cost entry recorded."}
   ])

# === THREAD 1ulwhtz -- no episodes (post removed, only AutoModerator) ===

# === THREAD 1uqj35m (Ion Solar experience) ==============================
ep(thread="1uqj35m", author="MessAccomplished4530",
   lifecycle_stage="completed_operating_after_miswired_correction_and_billing_dispute",
   lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   utility="unknown (New Mexico local utility, unnamed)",
   location={"raw_clue": "\"I am in New Mexico.\" explicit", "resolved_state": "New Mexico",
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 0.0,
             "scope_label": "out_of_state_new_mexico"},
   location_evidence="Explicit: 'I am in New Mexico.'",
   source_refs=["post", "owffyg4"],
   timing=[
       {"clock": "quoted_vs_actual_completion_duration", "refs": ["post"], "unit": "months", "value": 10,
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "120 day process(their quote not mine) took 10 months.",
        "note": "Vendor's own quote was 120 days (~4 months); actual observed time to completion was ~10 months."},
       {"clock": "quoted_vs_actual_completion_duration_days", "refs": ["owffyg4"], "unit": "days", "value": 300,
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "I would not have gone with them and shopped around if I knew there 120 day completion estimate was going to turn into 10 months of roughly 300 days."},
       {"clock": "post_pto_defect_repair", "refs": ["post"], "unit": "weeks", "value": 1,
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "It did take a week or so to get fixed."}
   ],
   costs=[
       {"value": 56000, "unit": "USD", "refs": ["owffyg4"],
        "note": "Total system cost: Tesla Powerwall 3, gateway, panel upgrade, and 6.1kW solar.",
        "quote": "For the tesla powerwall 3, gateway, panel upgrade, and 6.1kw of solar on a flat roof with weighted banister or whatever they are called it was around $56,000."},
       {"value": 5000, "unit": "USD", "refs": ["post"],
        "note": "Panel-upgrade cost that was initially quoted but omitted from the permit submission, then charged as an extra after correction.",
        "quote": "I was then told that the panel upgrade was an extra $5k."}
   ],
   non_registry_actions=[
       {"actor": "installer (Ion Solar)", "action": "install solar/battery circuit breakers at the correct (sub) panel",
        "status": "explicit_negative", "refs": ["post"],
        "quote": "After looking at the site plans with the permit and following wires, I realized that the solar and battery circuit breakers should have been installed at the sub panel."},
       {"actor": "county inspector", "action": "inspect and pass the installation", "status": "performed",
        "refs": ["post"],
        "quote": "The scary thing about this whole install was that the County inspection \"Passed\" and the power company gave me permission to operate."},
       {"actor": "utility", "action": "grant permission to operate (PTO)", "status": "performed",
        "refs": ["post"],
        "quote": "The scary thing about this whole install was that the County inspection \"Passed\" and the power company gave me permission to operate."},
       {"actor": "installer (Ion Solar)", "action": "correct miswired main/sub panel breaker placement",
        "status": "performed", "refs": ["post"], "quote": "It did take a week or so to get fixed."},
       {"actor": "installer (Ion Solar)", "action": "include panel upgrade in permit request submission",
        "status": "explicit_negative", "refs": ["post"],
        "quote": "When they sent in the permit request the panel upgrade was not included so had them correct it and resubmit it."},
       {"actor": "applicant", "action": "claim New Mexico 10% state solar tax credit", "status": "planned_not_performed",
        "refs": ["owffyg4"],
        "quote": "The New Mexico 10% tax credit can only be applied after PTO so I will claim the New Mexico one in 2026."}
   ])

ep(thread="1uqj35m", author="Lanky_Savings_5815",
   lifecycle_stage="completed_operating_dissatisfied_with_economics", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location given; separate, later (2026-09-04), unrelated case in the same thread.",
   source_refs=["p7v86um"],
   costs=[
       {"value": 285, "unit": "USD", "refs": ["p7v86um"],
        "note": "Stated monthly solar payment (recurring), 36-panel system, 1800 sq ft house.",
        "quote": "36 panels installed on solar $285 a month."},
       {"value": 49000, "unit": "USD", "refs": ["p7v86um"],
        "note": "Total system cost described by commenter as wasted spending.",
        "quote": "$49000 out the window."}
   ])

# === THREAD 1urvc4c (NEC Code power station) ============================
ep(thread="1urvc4c", author="ToughGuy69420",
   lifecycle_stage="pre_application_researching_electrical_permit_requirement_for_small_ground_mount",
   lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"My local code (MN)\" explicit", "resolved_state": "Minnesota",
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 0.0,
             "scope_label": "out_of_state_minnesota"},
   location_evidence="Explicit: 'My local code (MN) is clear on the panel part...'",
   source_refs=["post"],
   non_registry_actions=[
       {"actor": "applicant", "action": "obtain permit for main breaker panel and meter pan DIY work (prior, separate job)",
        "status": "performed", "refs": ["post"],
        "quote": "I was able to get a permit to do my main breaker panel and meter pan myself so that seems wild."},
       {"actor": "applicant", "action": "determine whether electrical permit is required for small ground-mount PV run",
        "status": "pending", "refs": ["post"],
        "quote": "My local code (MN) is clear on the panel part but then says electrical permit is needed and MN DOLI seems to only specify for contractors."}
   ])

# === THREAD 1uswo1v (Is solar throttled until PTO?) =====================
ep(thread="1uswo1v", author="Kiddcutie",
   lifecycle_stage="in_process_awaiting_pto_export_throttled", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["owrpc9h"],
   non_registry_actions=[
       {"actor": "field technician", "action": "explain export throttling policy prior to PTO", "status": "performed",
        "refs": ["owrpc9h"],
        "quote": "I spoke with the field technician, who explained that my system was throttled prior to receiving Permission to Operate (PTO). According to him, this is standard practice because some customers intentionally delay their PTO process to avoid paying the full cost of their system"}
   ])

ep(thread="1uswo1v", author="ggfb20",
   lifecycle_stage="in_process_awaiting_pto_export_throttled", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["owxnov3"],
   non_registry_actions=[
       {"actor": "service technicians", "action": "explain non-export throttling as normal pending PTO",
        "status": "performed", "refs": ["owxnov3"],
        "quote": "I'm told by the service techs that this is perfectly normal until PTO is received."}
   ])

# === THREAD 1uvxxhx (PTO but app not working) ===========================
ep(thread="1uvxxhx", author="brownshug5",
   lifecycle_stage="pto_received_activation_troubleshooting_after_contractor_bankruptcy",
   lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["post", "oxeusds"],
   timing=[{
       "clock": "pto_received_milestone", "refs": ["post"],
       "censoring": "single_milestone_no_duration|exact_as_stated|self_reported",
       "supported_event_dates": [{"date": "2026-07-14", "label": "PTO received from utility company"}],
       "quote": "a horrible company who went bankrupt recently (Freedom Forever…not) was my contractor and they went under but I finally got PTO today from my utility company at 9AM."
   }],
   non_registry_actions=[
       {"actor": "applicant", "action": "contact Tesla about system not producing after PTO",
        "status": "planned_not_performed", "refs": ["oxeusds"],
        "quote": "Welp Theres my problem. I will get in touch with Tesla tomorrow"}
   ])

# === THREAD 1uxjpj8 (Lawsuit with Solar Company) ========================
ep(thread="1uxjpj8", author="CurrentCar2331",
   lifecycle_stage="long_operating_ppa_contract_cancelled_disputed_no_lawsuit_filed",
   lifecycle_coarse="entered_then_terminated",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"local city electric system\" -- city/state never named", "resolved_state": None,
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="Only a generic 'local city electric system' is mentioned; no city or state named anywhere in the thread.",
   utility="municipal_electric_unspecified",
   source_refs=["post", "oxsbhoh", "oxse5v0", "oxsmco6", "oyrvh0t", "oyvx83h"],
   timing=[
       {"clock": "install_milestone", "refs": ["oxse5v0"],
        "censoring": "single_milestone_no_duration|month_only|self_reported",
        "supported_event_dates": [{"date": "2017-10", "label": "solar system installed, passed inspection"}],
        "quote": "it has passed inspection, it was installed october of 2017"},
       {"clock": "inspection_letters_to_present_unresolved", "refs": ["oxsbhoh"], "unit": "months", "lower": 5,
        "censoring": "pending_lower_bound|approximate|self_reported",
        "quote": "they were sending me a letter stating they need to inspect the system. So I would always call and try to scedule an insepection time and they would never set it up over the phone, just always tell me they will call back. This happened in Jan and Feb.",
        "note": "Jan/Feb (year assumed same as post year, 2026) to post date 2026-07-15 is roughly 5+ months, approximate."}
   ],
   non_registry_actions=[
       {"actor": "PPA company", "action": "cancel PPA contract", "status": "performed", "refs": ["post"],
        "quote": "today I found out my company has cancelled my contract and with not tell me why and will only say that I have to contact an attorney."},
       {"actor": "PPA company", "action": "disclose reason for contract cancellation", "status": "explicit_negative",
        "refs": ["post"],
        "quote": "today I found out my company has cancelled my contract and with not tell me why and will only say that I have to contact an attorney."},
       {"actor": "PPA company", "action": "request property access to inspect system", "status": "performed",
        "refs": ["oxsbhoh"],
        "quote": "they were sending me a letter stating they need to inspect the system. So I would always call and try to scedule an insepection time and they would never set it up over the phone, just always tell me they will call back."},
       {"actor": "PPA company", "action": "schedule the promised inspection appointment", "status": "explicit_negative",
        "refs": ["oxsbhoh"],
        "quote": "So I would always call and try to scedule an insepection time and they would never set it up over the phone, just always tell me they will call back."},
       {"actor": "applicant", "action": "retain lawyer to contact PPA company", "status": "performed",
        "refs": ["oxsmco6"], "quote": "my lawyer is calling them tomorrow."}
   ])
episodes[-1]["note"] = ("Per thread clarification at [oyve0oi]/[oyvx83h], no lawsuit was actually filed "
    "('so they have Not filed a lawsuit against you' -- 'no' [system not operating as it should]); OP's "
    "initial fear of being sued is not treated as an escalation event per the intent-vs-escalation rule.")

# === THREAD 1v1thqu (First-time DIY ground mount, MA) ====================
ep(thread="1v1thqu", author="twistypencil",
   lifecycle_stage="pre_application_planning_diy_ground_mount_massachusetts", lifecycle_coarse="pre_application",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"Building a new ~2,000 sq ft all-electric house north of Boston\" explicit",
             "resolved_state": "Massachusetts", "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_massachusetts"},
   location_evidence="Explicit: 'Building a new ~2,000 sq ft all-electric house north of Boston.' No specific town/county named.",
   source_refs=["post", "oys3gob"],
   non_registry_actions=[
       {"actor": "applicant", "action": "pull building permit for structural/ground-mount foundation side",
        "status": "planned_not_performed", "refs": ["oys3gob"],
        "quote": "It seems like I can pull the building permit for the structural side, can do the ground-mount foundation and racking."}
   ])
episodes[-1]["note"] = ("Massachusetts state law (MGL c.141, per commenter ReplicaRascal/oys3gob) requires all "
    "PV electrical work, including DC wiring, inverter connections, AC output circuits and interconnection, "
    "to be performed and permitted by a MA-licensed electrician; applicant can only self-perform the "
    "structural/mechanical side. Recorded as context, not forced into a non_registry_actions status.")

ep(thread="1v1thqu", author="Toad32",
   lifecycle_stage="completed_operating_ground_mount_with_battery", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location given by this commenter (do not infer from OP's Massachusetts location).",
   source_refs=["oyq01ho"],
   costs=[
       {"value": 30000, "unit": "USD", "refs": ["oyq01ho"],
        "note": "Total system cost: 19kW ground mount, 32kWh battery backup, 20kW Growatt hybrid inverters in parallel.",
        "quote": "I paid roughly 30k to get 19kw panels in a ground mount with 32KWH battery backup and 20KW growatt hybrid inverters in parrallel. The biggest expese was the electrician at 9k for the AC side hookup."},
       {"value": 9000, "unit": "USD", "refs": ["oyq01ho"],
        "note": "Electrician cost for the AC-side hookup, the single largest line item.",
        "quote": "The biggest expese was the electrician at 9k for the AC side hookup."},
       {"value": 5800, "unit": "USD", "refs": ["oyq01ho"],
        "note": "Cost of the 32 panels (580W each, 19kW total), shipped.",
        "quote": "The panels are the cheapest part - got 19kw of 580W panels (32 of them) for $5800 shipped."}
   ])

ep(thread="1v1thqu", author="Fit-Avocado-1646",
   lifecycle_stage="completed_operating_diy_ground_mount_with_engineer_signoff", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location given by this commenter.",
   source_refs=["oyq6nbl"],
   costs=[{
       "value": 18000, "unit": "USD", "refs": ["oyq6nbl"],
       "note": "DIY system cost including a friend discount on engineering services; 13kWh of panels, no batteries.",
       "quote": "DiY i think I was around $18k with everything 13 kWh of panels no batteries but I did get a friend discount from a family friend who is an engineer who did my roof load calculation and the engineer sign off saying my ground mount (skyrack 2.0) met local wind and snow loads."
   }],
   non_registry_actions=[
       {"actor": "engineer (discounted, personal connection)",
        "action": "perform roof/ground-mount load calculation and provide signed engineering approval",
        "status": "performed", "refs": ["oyq6nbl"],
        "quote": "I did get a friend discount from a family friend who is an engineer who did my roof load calculation and the engineer sign off saying my ground mount (skyrack 2.0) met local wind and snow loads."}
   ])

ep(thread="1v1thqu", author="CricktyDickty",
   lifecycle_stage="completed_operating_diy_ground_mount_dual_axis_trackers", lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"I'm on the other side of border (in upstate New York)\" is a REPLY commenter's location, not this author's; this author gives none",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="No location given by CricktyDickty themself; do not infer from a different reply author's location.",
   source_refs=["oyr9q4r"],
   costs=[{
       "value": 1.55, "unit": "per_watt", "refs": ["oyr9q4r"],
       "note": "Installed cost per watt for a 16.5kW DC ground mount with 3 dual-axis trackers.",
       "quote": "As a reference, I installed a DC 16.5kw system with 3 dual axis trackers and the total cost was $1.55/watt."
   }],
   non_registry_actions=[
       {"actor": "applicant", "action": "self-perform DIY ground-mount install including grid tap, per own AHJ rules",
        "status": "performed", "refs": ["oyr9q4r"],
        "quote": "In some rural jurisdictions (like mine) you can do all the work yourself, including tapping to the grid, provided you pass inspection."}
   ])

# === THREAD 1v26ks7 (Starting officially) ================================
ep(thread="1v26ks7", author="Careful_Okra8589",
   lifecycle_stage="in_process_utility_and_county_coordination_for_ground_mount_permit",
   lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "generic 'county'/'utility', never named", "resolved_state": None,
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="Post refers only to 'my utility' and 'county'; no state, county, or utility name given.",
   source_refs=["post", "p2xfeed"],
   timing=[{
       "clock": "permit_process_progress_milestones", "refs": ["post"],
       "censoring": "single_milestone_no_duration|approximate|self_reported",
       "supported_event_dates": [
           {"date": "2026-07-21", "label": "post date: utility said only a line diagram + county permission needed; planned to pull electrical permit that Friday and start work the following week"},
           {"date": "2026-08-10", "label": "utility approved wire diagram, per follow-up comment"}
       ],
       "quote": "Talked to my utility. They just need a line diagram and permission from county."
   }],
   non_registry_actions=[
       {"actor": "utility", "action": "approve wire/line diagram", "status": "performed", "refs": ["p2xfeed"],
        "quote": "I got my wire diagram approved from the Utility."},
       {"actor": "applicant", "action": "obtain county permission for ground mount", "status": "pending",
        "refs": ["post"],
        "quote": "County only requires an electrical permit for a ground mount system."},
       {"actor": "applicant", "action": "pull electrical permit", "status": "planned_not_performed",
        "refs": ["post"],
        "quote": "Will be pulling my electrical permit Friday and starting work the following week."}
   ])

# === THREAD 1v4i7jw (Solar not generating) ================================
ep(thread="1v4i7jw", author="Redactedacted",
   lifecycle_stage="pto_received_activation_troubleshooting_after_contractor_departure",
   lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "none given", "resolved_state": None, "resolved_county": None,
             "candidate_counties": [], "unassigned_geography_mass": 1.0,
             "scope_label": "unresolved_unknown"},
   location_evidence="No location clue given.",
   source_refs=["post", "ozb6smn"],
   timing=[{
       "clock": "pto_received_milestone", "refs": ["post"],
       "censoring": "single_milestone_no_duration|approximate|self_reported",
       "supported_event_dates": [{"date": "2026-07-23", "label": "post date; PTO described as 'recently' received"}],
       "quote": "I recently got the PTO from the utility company, but having trouble configuring the solark app/portal/directly on the inverter so it generates.",
       "note": "'recently' relative to post date 2026-07-23; no exact PTO date given."
   }],
   non_registry_actions=[
       {"actor": "original solar company", "action": "complete post-install support / confirm CT install",
        "status": "explicit_negative", "refs": ["ozb6smn"],
        "quote": "I'm dealing with a situation where the solar company bailed on us (long story) so not sure if these are installed or where."}
   ])

# === THREAD 1v4pv33 (NY/NJ generation thread) ============================
ep(thread="1v4pv33", author="kickflipper1087",
   lifecycle_stage="installer_submitted_pto_awaiting_utility_psegli", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   utility="PSEG Long Island",
   location={"raw_clue": "\"PSEG Long Island\" utility named explicitly", "resolved_state": "New York",
             "resolved_county": None, "candidate_counties": ["Suffolk County", "Nassau County"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_new_york"},
   location_evidence="Explicit utility 'PSEG Long Island' pins Long Island, NY, but not a specific county (Nassau or Suffolk).",
   source_refs=["post"],
   timing=[{
       "clock": "pto_request_submission_milestone", "refs": ["post"],
       "censoring": "single_milestone_no_duration|exact_as_stated|self_reported",
       "supported_event_dates": [{"date": "2026-07-21", "label": "installer submitted PTO request to PSEG Long Island, after inspection-certificate delay"}],
       "quote": "I'm impatiently waiting for PSEG Long Island to give us PTO (installer submitted on Tuesday the 21st after some delay with our inspection certificate)."
   }],
   non_registry_actions=[
       {"actor": "installer", "action": "submit PTO request to utility", "status": "performed", "refs": ["post"],
        "quote": "I'm impatiently waiting for PSEG Long Island to give us PTO (installer submitted on Tuesday the 21st after some delay with our inspection certificate)."}
   ])

ep(thread="1v4pv33", author="arcsnsparks98",
   lifecycle_stage="inspection_completed_after_inspector_communication_failure",
   lifecycle_coarse="completed_or_operating",
   inference_scope="installer_reported_on_behalf_of_client",
   location={"raw_clue": "none given by this commenter; thread is about NY/NJ generation but do not infer",
             "resolved_state": None, "resolved_county": None, "candidate_counties": ["New York", "New Jersey"],
             "unassigned_geography_mass": 1.0, "scope_label": "unresolved_unknown"},
   location_evidence="Commenter is an installer describing a client's inspection; no city/state stated directly, only weak thread-level context (NY/NJ generation thread) which is not treated as a pin.",
   source_refs=["ozd0oqq"],
   non_registry_actions=[
       {"actor": "AHJ inspector", "action": "conduct site inspection and communicate correction status",
        "status": "explicit_negative", "refs": ["ozd0oqq"],
        "quote": "I had been accusing the inspector of not being there but it turns out he went there, said I needed to make a correction but never uploaded that information to the portal. Never emailed me. Never responded to my emails when I reached out to him."},
       {"actor": "AHJ inspector", "action": "confirm inspection passed with no correction needed", "status": "performed",
        "refs": ["ozd0oqq"],
        "quote": "Turns out he was mistaken and I did not need to make a correction, everything was fine."}
   ])

ep(thread="1v4pv33", author="Calliesdad20",
   lifecycle_stage="completed_operating_fast_utility_approval_and_meter_change",
   lifecycle_coarse="completed_or_operating",
   inference_scope="self_reported_applicant",
   utility="Eversource",
   location={"raw_clue": "\"Cape cod\" explicit", "resolved_state": "Massachusetts",
             "resolved_county": "Barnstable County", "candidate_counties": ["Barnstable County"],
             "unassigned_geography_mass": 0.0, "scope_label": "out_of_state_massachusetts"},
   location_evidence="Explicit: 'Cape cod'; Eversource named as the utility that approved the application.",
   source_refs=["ozdq8d0", "ozds4wc"],
   timing=[
       {"clock": "pto_milestone", "refs": ["ozdq8d0"],
        "censoring": "single_milestone_no_duration|exact_as_stated|self_reported",
        "supported_event_dates": [{"date": "2026-05-12", "label": "PTO day"}],
        "quote": "Since my may 12th pto day im 820kwh net exported"},
       {"clock": "install_submission_to_utility_approval", "refs": ["ozds4wc"], "unit": "days", "value": 1,
        "censoring": "completed_observed|exact_as_stated|self_reported",
        "quote": "my application was approved by Eversource the day after my solar company submitted it."},
       {"clock": "approval_to_meter_change", "refs": ["ozds4wc"], "unit": "hours", "value": 24,
        "censoring": "completed_observed|exact_as_stated|self_reported",
        "quote": "Then within 24 hours they changed my meter"},
       {"clock": "meter_change_to_pto", "refs": ["ozds4wc"], "unit": "days", "lower": 2, "upper": 5,
        "censoring": "range_reported|approximate|self_reported",
        "quote": "the pto came a few days later",
        "note": "Vendor had estimated 'a couple of weeks' for the meter change, which the actual 24-hour turnaround beat; that estimate is not itself an observation."}
   ],
   non_registry_actions=[
       {"actor": "Eversource", "action": "approve interconnection application", "status": "performed",
        "refs": ["ozds4wc"], "quote": "my application was approved by Eversource the day after my solar company submitted it."},
       {"actor": "Eversource", "action": "change meter", "status": "performed", "refs": ["ozds4wc"],
        "quote": "Then within 24 hours they changed my meter"}
   ])

ep(thread="1v4pv33", author="jrkkrj1",
   lifecycle_stage="in_process_awaiting_pto_massachusetts_grid_delay", lifecycle_coarse="in_process_incomplete",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"Waiting on PTO in MA still\" explicit", "resolved_state": "Massachusetts",
             "resolved_county": None, "candidate_counties": [], "unassigned_geography_mass": 0.0,
             "scope_label": "out_of_state_massachusetts"},
   location_evidence="Explicit: 'Waiting on PTO in MA still.'",
   source_refs=["ozdrjqo", "ozdsm8c"],
   non_registry_actions=[
       {"actor": "grid operator / utility (unnamed)", "action": "process PTO request without unnecessary delay",
        "status": "explicit_negative", "refs": ["ozdsm8c"],
        "quote": "I'm dealing with grid. They are delaying as much as possible."}
   ])

# non-episode: suspected LLM-generated content in this thread
llm_suspect_1v4pv33 = {
    "thread": "1v4pv33", "reason": "suspected_llm_generated_advice_not_firsthand",
    "refs": ["ozifzza"], "scope": "comment",
    "quote": "15.64kW on IQ8X is a solid match — those micros clip at 384W continuous, and your REC 460s will hit that for a few hours midday on a clear July day. Expect maybe 2-3% annual clipping loss, which is optimal.",
    "note": ("Confident, generically-hedged, multi-topic recitation (module clipping specs + utility PTO "
             "turnaround statistics + seasonal production forecast) unlike surrounding conversational replies; "
             "not confirmed AI-generated, so content and quote are preserved and NOT used as a basis for any "
             "timing entry (the '10-14 business days for PTO... probably early August' claim is a third-party "
             "prediction, not an observation, and is excluded from kickflipper1087's timing[] for that reason too).")
}

# === THREAD 1v7dlmf (When it burns) =======================================
ep(thread="1v7dlmf", author="NetAtraX",
   lifecycle_stage="entered_then_terminated_catastrophic_fire_litigation_ongoing",
   lifecycle_coarse="entered_then_terminated",
   inference_scope="self_reported_applicant",
   location={"raw_clue": "\"It's Italy, btw.\" / \"I'm a stranger here in Italy\" explicit",
             "resolved_state": None, "resolved_county": None, "candidate_counties": [],
             "unassigned_geography_mass": 0.0, "scope_label": "international_non_us_italy"},
   location_evidence="Explicit: 'It's Italy, btw.' [ozxc6cu] and 'I'm a stranger here in Italy' [ozxcxni]. Not a US/California case; recorded with explicit international scope label, never to be pooled into any US/California estimate.",
   source_refs=["post", "ozxes0o", "p01q6qv"],
   timing=[
       {"clock": "initial_energize_to_first_shutdown", "refs": ["post"], "unit": "hours", "value": 1,
        "censoring": "completed_observed|approximate|self_reported",
        "quote": "It ran for maybe an hour, then shut down."},
       {"clock": "fire_start_to_inverter_data_stop", "refs": ["post"], "unit": "minutes", "value": 50,
        "censoring": "completed_observed|exact_as_stated|third_party",
        "quote": "The fact that the fire broke out and the inverter continued to record data for another 50 minutes afterward: It doesn’t matter. It was the inverter.",
        "note": "Attributed to the court-appointed expert's finding, reported by the applicant."}
   ],
   non_registry_actions=[
       {"actor": "electrician", "action": "install solar tiles, inverter, battery, and grid connection",
        "status": "performed", "refs": ["post"],
        "quote": "So a handyman cobbled together a wooden box, the electrician installed everything inside it, connected the solar tiles to the solar system, and the solar system to the power grid."},
       {"actor": "electrician", "action": "test the system before/after energizing", "status": "explicit_negative",
        "refs": ["post"], "quote": "The electrician forgot to install series diodes, he used defective tiles, and, worst of all: he never tested the system."},
       {"actor": "electrician", "action": "install required series diodes", "status": "explicit_negative",
        "refs": ["post"], "quote": "The electrician forgot to install series diodes, he used defective tiles, and, worst of all: he never tested the system."},
       {"actor": "electrician", "action": "provide string-measurement test results", "status": "explicit_negative",
        "refs": ["post"], "quote": "The electrician comes by and claims he performed a string measurement. But he doesn’t provide me with the results. He sends me photos of the “string measurements.” They show voltage and power figures that are never recorded on Huawei’s portal."},
       {"actor": "electrician", "action": "connect grounding connectors of inverter and battery to ground",
        "status": "explicit_negative", "refs": ["ozxes0o"],
        "quote": "He didn't connect the grounding connectors of inverter and battery to the ground. When confronted with this (before the fire) he told me: Well, I grounded the switch board, that's for everything."},
       {"actor": "court", "action": "assign liability share for fire damage", "status": "performed",
        "refs": ["post"],
        "quote": "BUT: I, as a layperson, am supposed to bear 50% of the damage. After all, as the client, I supposedly stood by and watched as the electrician put the system into operation without handing me the legally required permit."},
       {"actor": "electrician", "action": "provide legally required permit/documentation to homeowner",
        "status": "explicit_negative", "refs": ["post"],
        "quote": "At fault: The electrician. Because he didn’t have the required documentation."},
       {"actor": "applicant", "action": "inform building department of separate installation code violations (unconduited buried cabling)",
        "status": "performed", "refs": ["p01q6qv"],
        "quote": "Btw: I informed the authorities. Just an example: Power lines are just in the earth, no protective conduits, cables are literally just put into the earth and covered with an inch of dirt."},
       {"actor": "building department official", "action": "take enforcement action on reported violations",
        "status": "explicit_negative", "refs": ["p01q6qv"],
        "quote": "Response from the person in charge at the building department: “There’s nothing we can do about it; otherwise, the electrician will go bankrupt....”"}
   ])
episodes[-1]["note"] = ("Several commenters (AriochQ, shikkonin, BigWhiteDog, Previous-Sentence684) suspected this "
    "post was AI-generated; OP explicitly and repeatedly denied it, offered specific unverifiable-by-us but "
    "concrete corroborating detail (photos/video, named tile brand Dyaqua, named inverter model, timeline of "
    "travel), and stated 'It was written by me. Sorry that English isn't my first language.' Per the brief's "
    "guidance for cases of suspicion without certainty, the content is retained as a firsthand report with this "
    "note flagging the community's suspicion, rather than being silently dropped or silently trusted.")

# ---------------------------------------------------------------------------
# COVERAGE
# ---------------------------------------------------------------------------
held = {
    "1ud0zfe": 33, "1ud3dnw": 19, "1ueqhjw": 40, "1ufr883": 9, "1ugnnj1": 23,
    "1ujym90": 18, "1ukjic9": 9, "1uli8ne": 19, "1ulwhtz": 1, "1uqj35m": 5,
    "1urvc4c": 10, "1uswo1v": 15, "1uvxxhx": 8, "1uxjpj8": 38, "1v1thqu": 22,
    "1v26ks7": 8, "1v4i7jw": 12, "1v4pv33": 22, "1v7dlmf": 36
}
sources = {s["thread_id"]: s for s in json.load(open(os.path.join(PDIR, "reservation.json")))["sources"]}

episodes_per_thread = {}
for e in episodes:
    episodes_per_thread[e["thread"]] = episodes_per_thread.get(e["thread"], 0) + 1

removed_deleted_threads = {"1ud3dnw", "1ueqhjw", "1uxjpj8", "1v4i7jw", "1v7dlmf"}

coverage_rows = []
for tid, hc in held.items():
    n_eps = episodes_per_thread.get(tid, 0)
    disposition = "process_evidence_extracted" if n_eps > 0 else "read_no_process_evidence"
    gap_flags = ["removed_or_deleted_body"] if tid in removed_deleted_threads else []
    coverage_rows.append({
        "thread_id": tid,
        "source_path": sources[tid]["source_path"],
        "source_sha256": sources[tid]["sha256"],
        "held_comments": hc,
        "read_comments": hc,
        "gap_flags": gap_flags,
        "state": "completed",
        "disposition": disposition,
        "episodes_extracted": n_eps,
        "packet_path": f"runs/solar_forum_20260922/parse/claude_bulk/{PACKET_ID}/decisions.json"
    })

coverage = {
    "schema_version": "solar-packet-coverage/1",
    "packet_id": PACKET_ID,
    "rows": coverage_rows
}

# ---------------------------------------------------------------------------
# DECISIONS
# ---------------------------------------------------------------------------
non_episode_dispositions = [llm_suspect_1v4pv33]

decisions = {
    "schema_version": "solar-semantic-decisions/1",
    "packet_id": PACKET_ID,
    "adoption_state": "staged_pending_root_review",
    "reviewer": "Claude_bulk_reading",
    "review_method": "full manual read of all 19 reserved threads, every held comment, single pass, per READER_BRIEF.md",
    "threads": list(held.keys()),
    "episodes": episodes,
    "non_episode_dispositions": non_episode_dispositions
}

# ---------------------------------------------------------------------------
# TIMING_STAGED
# ---------------------------------------------------------------------------
timing_episodes = []
for e in episodes:
    timing_episodes.append({
        "thread": e["thread"], "author": e["author"],
        "same_installation_as": e.get("same_installation_as"),
        "utility": e.get("utility"),
        "location": e.get("location"),
        "county_weights": {},
        "unassigned_geography_mass": (e.get("location") or {}).get("unassigned_geography_mass", 1.0),
        "context": e.get("lifecycle_stage"),
        "timing": e.get("timing", []),
        "source_packets": [DEC_PATH]
    })

timing_staged = {
    "schema_version": "solar-reviewed-timing/1",
    "packet_id": PACKET_ID,
    "source_packets": [DEC_PATH],
    "episodes": timing_episodes
}

# ---------------------------------------------------------------------------
# WRITE decisions/timing/coverage first (manifest depends on their hashes)
# ---------------------------------------------------------------------------
def write_json(name, obj):
    path = os.path.join(PDIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path

p_dec = write_json("decisions.json", decisions)
p_tim = write_json("timing_staged.json", timing_staged)
p_cov = write_json("coverage.json", coverage)

# ---------------------------------------------------------------------------
# MANIFEST
# ---------------------------------------------------------------------------
nclaims = {"timing": 0, "costs": 0, "effort": 0, "non_registry_actions": 0}
for e in episodes:
    for k in nclaims:
        nclaims[k] += len(e.get(k) or [])

res = json.load(open(os.path.join(PDIR, "reservation.json")))
inputs = [{"path": "runs/solar_forum_20260922/parse/claude_bulk/CLAUDE_SOLAR_0127/reservation.json",
           "sha256": sha256(os.path.join(PDIR, "reservation.json"))}]
for s in res["sources"]:
    inputs.append({"path": s["source_path"], "sha256": s["sha256"]})

now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

manifest = {
    "packet_id": PACKET_ID,
    "inputs": inputs,
    "outputs": [
        {"path": DEC_PATH, "sha256": sha256(p_dec)},
        {"path": f"runs/solar_forum_20260922/parse/claude_bulk/{PACKET_ID}/timing_staged.json", "sha256": sha256(p_tim)},
        {"path": f"runs/solar_forum_20260922/parse/claude_bulk/{PACKET_ID}/coverage.json", "sha256": sha256(p_cov)}
    ],
    "reader": "Claude_bulk_reading",
    "model": "claude-sonnet-5",
    "started_at": "2026-09-22T18:16:24Z",
    "finished_at": now,
    "counts": {
        "threads": len(held),
        "held_comments": sum(held.values()),
        "read_comments": sum(held.values()),
        "episodes": len(episodes),
        "claims_by_type": nclaims
    },
    "assumptions": [
        "Where a year was omitted but implied by thread context (e.g. 'May of 2024' or a Jan/Feb reference "
        "in a 2026-dated thread), the year is stated explicitly in each entry's note/label, never silently assumed.",
        "'Several months', 'a while', and other purely qualitative durations with no number were NOT converted "
        "into timing entries per field rule 5; they are preserved only in non_registry_actions/notes.",
        "No candidate weighting or county assignment was performed for out-of-state/international cases; "
        "unassigned_geography_mass is set to 1.0 (or near it) for every episode in this packet, since none "
        "resolve to a California county.",
        "This packet contains zero explicit California location evidence across all 19 threads; every located "
        "episode is out-of-state (MD, FL, MN, NM, NY, MA) or international (Italy), and the remainder are unresolved/unknown."
    ],
    "no_synthetic_truth_access": True,
    "staged_not_model_consumed": True
}

p_man = os.path.join(PDIR, "manifest.json")
with open(p_man, "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print("Wrote:", p_dec, p_tim, p_cov, p_man)
print("Episodes:", len(episodes))
print("Claims:", nclaims)
