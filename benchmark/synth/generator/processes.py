"""process_truth: the full designed graph, including the steps nobody publishes.

Composition (in phase order, so the graph reads like a real designed process):

    0  standing agency obligations (publish a checklist)
    1  pre-application (third-party inspection, pre-app meeting, community meeting)
    2  submittal (portal account, application, fee, affidavit, deposit)
    3  intake back-office (completeness screening, GIS/zoning check, routing,
       license/insurance/tax verification, fee reconciliation, status update)
    4  referrals and notices (fire/health/police/public-works, neighbour notice)
    5  inspection (scheduling batch, tenant notice, the inspection itself)
    6  corrections by the applicant, then re-inspection
    7  decision (supervisor sign-off on denials, hearing/council action, mailing)
    8  post-decision (records archive, assessor/code-enforcement referral, state
       reporting, QA audit, appeal, renewal/delay paths)

Three fields carry the benchmark's signal:

* ``visibility`` -- ``applicant_facing`` / ``applicant_inferable`` / ``staff_only``.
  The visibility model (visibility.py) uses nothing else to decide what a public
  artifact can say.
* ``timing`` -- lognormal (median, p90) *cycle* time: from the moment the step
  becomes ready (including queue time), which is what an applicant experiences.
* ``rework`` -- p_trigger + back_to, the loops that make elapsed time
  heavy-tailed and that declared-tier pages almost never describe.
"""
from __future__ import annotations

from .domains import DOMAINS
from .rng import chance, pick, sub_rng, weighted
from . import capacity
from .world import actor_name, jur_by_id

# ------------------------------------------------------------- back office --
# tag -> (names, role, occasion, visibility, phase, median, p90, artifacts_out)
def _bo(names, role, occasion, visibility, phase, median, p90, out, notes=""):
    return dict(names=names, role=role, occasion=occasion, visibility=visibility,
                phase=phase, median=median, p90=p90, out=out, notes=notes)


BACKOFFICE: dict[str, dict] = {
    "intake_screening": _bo(
        ["Screen the submittal for completeness", "Screen the application at the counter", "Review the submittal for completeness"],
        "lead_permits", "internal", "applicant_inferable", 3.0, 3, 10,
        ["completeness letter or correction request"],
        "the applicant sees only a request for missing items, never the screening checklist"),
    "gis_parcel": _bo(
        ["Verify the parcel and zoning in GIS", "Check the APN and zoning district", "Research the parcel record"],
        "planning", "internal", "staff_only", 3.1, 2, 7, ["parcel research note"]),
    "zoning_check": _bo(
        ["Check the proposal against the objective zoning standards", "Verify the zoning district and use"],
        "planning", "internal", "staff_only", 3.1, 4, 12, ["zoning clearance"]),
    "routing": _bo(
        ["Route the case to the assigned reviewer queue", "Assign the case to a plan reviewer (round robin)"],
        "lead_permits", "internal", "staff_only", 3.2, 2, 8, ["case assignment"]),
    "plan_check_queue": _bo(
        ["Review the submitted documents in the reviewer queue", "Plan-check the submitted documents", "Review the submittal technically"],
        "building", "internal", "applicant_inferable", 3.4, 18, 48, ["plan check comments"]),
    "second_review": _bo(
        ["Sign off as second reviewer", "Concur as senior reviewer", "Sign off as supervising inspector"],
        "building", "internal", "staff_only", 3.6, 5, 16, ["reviewer concurrence"]),
    "tax_cert_check": _bo(
        ["Verify the transient occupancy tax certificate", "Cross-check the business tax account"],
        "finance", "internal", "staff_only", 3.3, 4, 14, ["tax account verification"]),
    "license_verify": _bo(
        ["Verify the state license against the state registry", "Verify the state license and bond"],
        "finance", "internal", "staff_only", 3.3, 2, 8, ["license verification printout"]),
    "insurance_check": _bo(
        ["Verify the certificate of insurance and endorsements", "Review the insurance certificate (Risk Management)"],
        "attorney", "internal", "staff_only", 3.3, 6, 18, ["insurance verification"]),
    "business_license_link": _bo(
        ["Link the case to the business license account", "Open or update the business tax account"],
        "finance", "internal", "staff_only", 3.35, 3, 11, ["account link"]),
    "complaint_crossref": _bo(
        ["Cross-reference open complaints and code cases for the address",
         "Check the address against open enforcement cases"],
        "code_enforcement", "internal", "staff_only", 3.45, 3, 10, ["case history note"]),
    "fee_recon": _bo(
        ["Reconcile the fees with Finance in the daily cashiering batch", "Reconcile the deposit against the cost-recovery account"],
        "finance", "internal", "staff_only", 3.7, 4, 16, ["reconciliation entry"]),
    "status_update": _bo(
        ["Update the permit-tracking system status", "Post the status change to the portal"],
        "lead_permits", "internal", "applicant_inferable", 3.8, 1, 5, ["portal status change"],
        "the applicant infers progress from the portal status only"),
    "portal_config": _bo(
        ["Configure the automated review rules in the permit platform",
         "Maintain the automated eligibility rule set"],
        "building", "internal", "staff_only", 0.5, 12, 40, ["platform rule set"]),
    "exception_queue": _bo(
        ["Review manually the applications the automated check rejected", "Triage the exception queue"],
        "building", "internal", "applicant_inferable", 3.5, 9, 30, ["exception disposition"]),
    "fire_referral": _bo(
        ["Review the application for life safety (Fire Prevention)", "Clear the application (Fire Marshal)"],
        "fire", "internal", "applicant_inferable", 4.2, 12, 34, ["fire clearance or conditions"]),
    "health_referral": _bo(
        ["Review the application for health compliance (Environmental Health)", "Review the application (county health specialist)"],
        "health", "internal", "applicant_inferable", 4.2, 14, 40, ["health clearance"]),
    "police_referral": _bo(
        ["Review the event staffing plan (police special events unit)", "Review public safety staffing"],
        "police", "internal", "staff_only", 4.2, 10, 28, ["staffing plan and cost estimate"]),
    "pw_referral": _bo(
        ["Review the traffic control plan (Public Works)", "Review the encroachment and traffic control plan"],
        "publicworks", "internal", "staff_only", 4.25, 12, 32, ["traffic control approval"]),
    "event_committee": _bo(
        ["Review the application at the special event review committee", "Review the application at the interdepartmental event committee"],
        "lead_permits", "internal", "applicant_inferable", 4.3, 16, 38, ["committee conditions"]),
    "translation": _bo(
        ["Translate the program handout and rules into the required languages", "Send the program materials to translation services"],
        "clerk", "internal", "staff_only", 4.4, 8, 22, ["translated notice"]),
    "notice_mailing": _bo(
        ["Prepare and mail the decision notice", "Print, stuff and mail the notice batch"],
        "clerk", "mail", "applicant_inferable", 7.5, 4, 11, ["mailed notice", "proof of mailing"]),
    "posting": _bo(
        ["Post the notice on the site", "Post the public notice in the field"],
        "code_enforcement", "site_visit", "applicant_facing", 4.5, 5, 13, ["posting photograph and affidavit"]),
    "tenant_notice": _bo(
        ["Serve the 48-hour entry notice on the tenants", "Leave a door-hanger notice for the occupants"],
        "code_enforcement", "mail", "applicant_inferable", 4.9, 3, 9, ["entry notice"]),
    "inspection_batch": _bo(
        ["Batch-schedule the week's inspection route", "Add the case to the inspection route"],
        "building", "internal", "staff_only", 4.95, 6, 18, ["inspection route sheet"],
        "route batching is the real reason inspections cluster on certain days"),
    "reinspection_sched": _bo(
        ["Schedule the re-inspection after the correction period", "Calendar the 30-day re-inspection"],
        "code_enforcement", "internal", "staff_only", 6.2, 5, 15, ["re-inspection appointment"]),
    "supervisor_denial": _bo(
        ["Approve the denial recommendation (supervisor)", "Concur in the denial (division manager)"],
        "building", "internal", "staff_only", 7.2, 6, 20, ["approved denial memo"],
        "only denials take this path, which is why denial timelines are longer"),
    "council_agenda": _bo(
        ["Prepare the agenda item and route it to the clerk", "Prepare the agenda packet and obtain legal review"],
        "clerk", "internal", "staff_only", 6.8, 14, 34, ["agenda report"]),
    "decal_issue": _bo(
        ["Issue and log the permit decal", "Assign and log the decal number"],
        "lead_permits", "counter", "applicant_facing", 7.6, 2, 7, ["numbered decal"]),
    "ce_referral": _bo(
        ["Refer the case to Code Enforcement for follow-up", "Open a code enforcement watch on the address"],
        "code_enforcement", "internal", "staff_only", 8.3, 7, 24, ["code enforcement referral"]),
    "assessor_referral": _bo(
        ["Notify the County Assessor of the legalized unit", "Transmit the change to the Assessor"],
        "assessor", "internal", "staff_only", 8.4, 10, 30, ["assessor notification"],
        "applicants routinely do not learn of this until a reassessment notice arrives"),
    "records_archive": _bo(
        ["Scan and archive the case file to records management", "Index and archive the closed case"],
        "records", "internal", "staff_only", 8.6, 8, 26, ["archived case file"]),
    "state_report": _bo(
        ["Compile the annual report to the state agency", "Extract the quarterly data for the state"],
        "lead_permits", "internal", "staff_only", 8.8, 20, 60, ["state report submission"]),
    "appeal_docket": _bo(
        ["Docket the appeal and set the hearing date", "Calendar the appeal and notice the parties"],
        "clerk", "internal", "staff_only", 8.5, 7, 21, ["hearing notice"]),
    "qa_audit": _bo(
        ["Audit a monthly sample of issued permits", "Review a QA sample of closed cases"],
        "lead_permits", "internal", "staff_only", 8.9, 15, 45, ["audit sample memo"]),
}

# statute element kind -> (phase, timing class, occasion, visibility)
ELEMENT_PLAN = {
    "checklist_publication": (0.2, "publication", "internal", "applicant_facing"),
    "third_party_option": (1.0, "third_party", "site_visit", "applicant_facing"),
    "application": (2.0, "prepare", "counter", "applicant_facing"),
    "fee": (2.3, "payment", "online", "applicant_facing"),
    "record": (8.2, "record", "internal", "staff_only"),
    "referral": (4.1, "referral", "internal", "applicant_inferable"),
    "notice": (4.6, "notice", "mail", "applicant_facing"),
    "inspection": (5.0, "inspection", "site_visit", "applicant_facing"),
    "correction": (6.0, "correction", "site_visit", "applicant_facing"),
    "public_hearing": (6.9, "hearing", "hearing", "applicant_facing"),
    "decision": (7.0, "decision", "internal", "applicant_facing"),
    "fee_waiver": (8.15, "waiver", "counter", "applicant_facing"),
    "appeal": (8.55, "appeal", "hearing", "applicant_facing"),
    "timeline": (8.45, "renewal", "mail", "applicant_facing"),
}

# timing class -> (median_days, p90_days) before the jurisdiction speed factor
TIMING = {
    "publication": (30, 90), "third_party": (16, 45), "prepare": (8, 30), "payment": (2, 8),
    "record": (6, 22), "referral": (12, 32), "notice": (6, 15), "inspection": (12, 30),
    "correction": (18, 55), "hearing": (28, 62), "decision": (5, 15), "waiver": (10, 28),
    "appeal": (34, 75), "renewal": (9, 26),
}

# Locally added element kinds -> phase
ADDED_PHASE = {
    "pre_application_meeting": 1.2, "community_meeting": 1.4, "business_license_prereq": 1.6,
    "online_portal": 1.9, "affidavit": 2.4, "deposit": 2.5, "neighbor_notification": 4.55,
    "fire_clearance": 4.4, "extra_inspection": 6.5, "appeal_to_hearing_officer": 8.56,
}

# The hand-written jurisdictions' pace multipliers, literal so that
# world_model_version 1 stays byte-identical. A generated county derives one
# from capacity.speed_factor, which plants the measured population gradient and
# the much larger unexplained residual that goes with it.
SPEED = {"J1": 1.0, "J2": 1.25, "J3": 1.4, "J4": 1.15, "K1": 1.0, "K2": 1.1}

# Back-office steps the *case* does not wait for: they run in parallel with the
# visible path (a GIS check inside the review window, a nightly cashiering batch,
# archiving after closure). Everything else is blocking, i.e. on the applicant's
# critical path. This is the difference between a 15-step process that takes four
# months and one that takes two years.
NON_BLOCKING = {
    "gis_parcel", "zoning_check", "routing", "tax_cert_check", "license_verify",
    "insurance_check", "business_license_link", "complaint_crossref", "fee_recon",
    "status_update", "records_archive", "assessor_referral", "ce_referral", "qa_audit",
    "state_report", "portal_config", "translation", "posting",
}

# Back-office work that is a standing obligation rather than a step a case walks
# through: configuring the platform, translating the program handout, the annual
# report to the state, the monthly QA sample.
STANDING_TAGS = {"portal_config", "state_report", "qa_audit", "translation"}

DENIAL_BASE = {
    "unpermitted_unit_amnesty": 0.10, "str_registration": 0.07, "sidewalk_vending": 0.05,
    "tree_removal": 0.18, "home_business": 0.04, "mobile_food": 0.08, "solar_auto_permit": 0.03,
    "rental_inspection": 0.05, "backyard_hens": 0.03, "special_event": 0.06,
    "well_permit": 0.05, "contractor_registration": 0.04,
}


def _artifacts(kind: str, dom: dict, terminal: str) -> tuple[list[str], list[str]]:
    return {
        "checklist_publication": ([], [dom["checklist"]]),
        "third_party_option": (["access to the site"], ["third-party inspection report", dom["checklist"] + " (contractor-signed)"]),
        "application": ([dom["app_form"], "supporting documents"], ["submitted application", "case number"]),
        "fee": (["fee invoice"], ["paid receipt"]),
        "record": (["case record"], ["registry entry"]),
        "referral": (["case file"], ["referral memo"]),
        "notice": (["mailing list"], ["written notice"]),
        "inspection": ([dom["checklist"], "access to the site"], ["completed inspection checklist", "list of violations"]),
        "correction": (["list of violations"], ["corrections completed", "corrective-work permit where required"]),
        "public_hearing": (["staff report"], ["legislative action"]),
        "decision": (["complete case file"], [terminal]),
        "fee_waiver": (["income declaration"], ["ability-to-pay determination"]),
        "appeal": (["appeal form", "appeal fee"], ["hearing officer decision"]),
        "timeline": (["renewal or delay request"], ["renewal notice or delay authorization"]),
    }.get(kind, ([], []))


def _timing(world: dict, cls: str, jur_id: str, shot_clock: int | None, rng, pace: float = 1.0) -> dict:
    med, p90 = TIMING[cls]
    f = _speed_for(world, jur_id) * pace * (0.85 + 0.3 * rng.random())
    med, p90 = med * f, p90 * f
    if shot_clock and cls in ("decision", "notice", "appeal", "inspection"):
        # a shot clock anchors the distribution: most cases inside it, a tail outside
        med = max(1.0, shot_clock * (0.45 + 0.25 * rng.random()))
        p90 = shot_clock * (0.95 + 0.45 * rng.random())
    return {"dist": "lognormal", "median_days": round(med, 1), "p90_days": round(max(p90, med * 1.3), 1)}


# --------------------------------------------------------- action phrasing --
# Activity `name` is always **verb first** ("Submit...", "Pay...", "Review...",
# "Issue...", "Request...") so that a solver's natural phrasing aligns with gold
# without penalty; the statute's own clause wording is preserved verbatim in
# `element_text` and in `span.quote` (with the section anchor as `span.cite`).

def _receiver_role(el_name: str, domain: str, jur: dict) -> str:
    n = el_name.lower()
    for key, role in (("health", "health"), ("fire", "fire"), ("police", "police"),
                      ("public works", "publicworks"), ("counsel", "attorney"),
                      ("attorney", "attorney"), ("state", "state_agency"),
                      ("assessor", "assessor")):
        if key in n:
            return role
    return {"mobile_food": "fire", "sidewalk_vending": "health", "special_event": "police"}.get(domain, "fire")


def _element_actor(el: dict, jur: dict, rule: dict, dom: dict, lead: str, phase: float,
                   standing: bool) -> tuple[str, str | None]:
    """(actor role, counterparty role) for a statute element, sanity-checked by kind."""
    kind, domain = el["kind"], rule["domain"]
    if el["actor_role"] == "applicant":
        counter = {
            "fee": "finance" if "finance" in jur["depts"] else lead,
            "application": lead,
            "correction": "building" if "building" in jur["depts"] else lead,
            "appeal": "hearing",
            "fee_waiver": "hearing" if "hearing" in jur["depts"] else "code_enforcement",
            "record": "state_agency" if "state" in el["name"].lower() else lead,
            "timeline": "code_enforcement" if "code enforcement" in el["name"].lower() else lead,
        }.get(kind, lead)
        return "applicant", counter
    if el["actor_role"] == "third_party":
        return "third_party", lead
    if el["actor_role"] == "public":
        return "council", lead
    # ---- agency elements
    if kind == "inspection":
        if domain in ("rental_inspection", "sidewalk_vending"):
            return "code_enforcement", None
        if domain in ("mobile_food", "well_permit"):
            return ("health" if ("health" in jur["depts"] or jur["kind"] == "county") else lead), None
        return ("building" if "building" in jur["depts"] else lead), None
    if kind == "notice":
        # an enforcement notice comes from Code Enforcement; a decision/hearing
        # notice from the clerk
        return ("code_enforcement" if (phase >= 8.0 or "violation" in el["name"].lower())
                else "clerk"), None
    if kind == "record":
        return ("records" if standing else lead), None
    if kind == "referral":
        return lead, _receiver_role(el["name"], domain, jur)       # the lead department routes
    if kind == "public_hearing":
        return "council", lead
    if kind == "appeal":
        return "hearing", lead
    if kind == "checklist_publication":
        return ("clerk" if "language" in el["name"].lower() and "clerk" in jur["depts"] else lead), None
    if kind == "fee":
        return ("finance" if "finance" in jur["depts"] else lead), "applicant"
    return lead, None


def _element_action(el: dict, dom: dict, rule: dict, jur: dict, lead: str, phase: float,
                    standing: bool, receiver: str | None) -> tuple[str, list[str]]:
    """(verb-first canonical name, jurisdiction-flavoured variants)."""
    N = {
        "program": rule["program_name"], "form": dom["app_form"], "checklist": dom["checklist"],
        "terminal": rule["terminal_artifact"], "fee_label": dom["fee_label"],
        "inspection": dom["inspection_name"], "council": jur["council"],
        "dept": actor_name(jur, lead, rule["domain"]),
        "receiver": actor_name(jur, receiver, rule["domain"]) if receiver else "the reviewing department",
        "body": rule["choices"].get(next((c for c, v in rule["choices"].items()
                                          if "hearing" in str(v).lower() or "commission" in str(v).lower()), ""),
                                    actor_name(jur, "hearing", rule["domain"])),
        "portal": jur["permit_system"],
    }
    if not N["body"].lower().startswith("the "):
        N["body"] = "the " + N["body"]
    k, low = el["kind"], el["name"].lower()
    if k == "application":
        return ("Submit the %(program)s application" % N,
                ["Apply for the %(program)s" % N, "File the %(form)s" % N,
                 "Submit the %(form)s through %(portal)s" % N])
    if k == "fee":
        return ("Pay the %(fee_label)s fee" % N,
                ["Pay the %(program)s fee" % N, "Pay the permit fee at the cashier",
                 "Pay the %(fee_label)s fee before review" % N])
    if k == "inspection":
        return ("Conduct the %(inspection)s" % N,
                ["Inspect the site for compliance", "Carry out the %(inspection)s" % N])
    if k == "third_party_option":
        return ("Obtain a third-party inspection from a licensed professional",
                ["Obtain a confidential third-party code inspection",
                 "Hire a licensed professional to inspect before applying"])
    if k == "correction":
        return ("Correct the cited violations and obtain any corrective permits",
                ["Complete the required corrections", "Correct the violations and call for re-inspection",
                 "Complete the replacement planting or pay the in-lieu fee"
                 if rule["domain"] == "tree_removal" else "Finish the corrective work"])
    if k == "decision":
        return ("Issue the %(terminal)s" % N,
                ["Approve or deny the application", "Grant the permit and issue the %(terminal)s" % N])
    if k == "notice":
        if phase >= 8.0 or "violation" in low:
            return ("Issue the notice of violation with the fine schedule",
                    ["Serve the notice of violation", "Issue the administrative citation"])
        if "tenant" in low or "entry" in low:
            return ("Serve the entry notice on the tenant",
                    ["Notify the tenant and owner before entry", "Give the 48-hour entry notice"])
        if "renewal" in low:
            return ("Mail the renewal notice", ["Send the renewal reminder"])
        return ("Mail and post the required public notice",
                ["Notice the neighbours and post the site", "Send the notice of the application"])
    if k == "record":
        if el["actor_role"] == "applicant":
            return (("Register the units in the %(dept)s registry" % N) if phase < 5
                    else "File the required report with the state agency",
                    ["File the registration with %(dept)s" % N, "Submit the completion report"])
        if standing:
            return (("Maintain the public %(program)s registry" % N),
                    ["Publish the register of issued permits", "Update the public permit register"])
        return ("Verify the applicant's record against the state registry",
                ["Check the state licence and insurance record",
                 "Confirm the registration against the state database"])
    if k == "referral":
        return ("Route the application to %(receiver)s for review" % N,
                ["Refer the file to %(receiver)s" % N,
                 "Send the application to %(receiver)s for clearance" % N])
    if k == "appeal":
        return ("Hear the appeal and decide it",
                ["Hold the administrative hearing", "Decide the appeal after a hearing"]) \
            if el["actor_role"] == "agency" else \
            ("File an appeal of the decision",
             ["Appeal the decision to %(body)s" % N, "Request a hearing on the decision"])
    if k == "fee_waiver":
        return ("Request a fine reduction for inability to pay",
                ["Apply for the ability-to-pay reduction", "Request a hardship reduction of the fine"])
    if k == "timeline":
        if "delay" in low:
            return ("Request the five-year delay of code enforcement",
                    ["File the code-enforcement delay request", "Ask for the enforcement delay"])
        if "renew" in low:
            return ("Renew the %(program)s registration" % N,
                    ["File the annual renewal", "Renew before the grace period ends"])
        return ("Meet the statutory deadline", ["Act within the statutory period"])
    if k == "public_hearing":
        return ("Hold the %(council)s hearing on the application" % N,
                ["Take the item to the %(council)s" % N, "Obtain %(council)s approval" % N])
    if k == "checklist_publication":
        return ("Publish the %(checklist)s" % N,
                ["Post the %(checklist)s on the department website" % N,
                 "Publish the program rules and the fine schedule"])
    return (el["name"], [])


# Keyed by (world, seed, scenario, jur_id), NOT by county id alone. Codex's
# review reproduced the contamination the short key caused: build the reference
# scenario and then the inverse one inside a single process and C01/C02 kept
# 0.723 / 1.620 instead of the expected 1.452 / 0.816, because the second build
# read the first build's cache. Separate CLI processes were unaffected, which is
# exactly why it survived: every corpus so far was built by its own process, and
# the defect would only have surfaced in a multi-seed or scenario sweep, where it
# would have made two different worlds look identical.
_SPEED_CACHE: dict[tuple, float] = {}


def _speed_key(world: dict, jur_id: str) -> tuple:
    return (world.get("world"), world.get("seed"),
            world["knobs"].get("speed_scenario", "reference"), jur_id)


def _speed_for(world: dict, jur_id: str) -> float:
    """Pace multiplier for a jurisdiction: literal for the hand-written six,
    derived and cached per (world, seed, scenario) for a generated county."""
    if jur_id in SPEED:
        return SPEED[jur_id]
    return _SPEED_CACHE.get(_speed_key(world, jur_id), 1.15)


def build_process(world: dict, statutes: dict, rule: dict) -> dict:
    jur = jur_by_id(world)[rule["jur"]]
    key = _speed_key(world, jur["id"])
    if jur["id"] not in SPEED and key not in _SPEED_CACHE:
        _SPEED_CACHE[key] = capacity.speed_factor(
            jur, world["seed"],
            scenario=world["knobs"].get("speed_scenario", "reference"))
    stat = statutes[rule["stat_id"]]
    dom = DOMAINS[rule["domain"]]
    knobs = world["knobs"]
    mid = rule["model_id"]
    rng = sub_rng(world["seed"], "process", mid)
    terminal = rule["terminal_artifact"]
    lead = rule["lead_role"]

    rows: list[dict] = []   # (phase, spec) pre-id assignment
    unimplemented, deviations = [], []

    # ---- 1. statute skeleton ------------------------------------------------
    for el in stat["skeleton"]:
        phase, cls, occ, vis = ELEMENT_PLAN[el["kind"]]
        if el["kind"] == "record" and el["must_precede"]:
            # a registration/verification that gates later steps happens early
            phase, cls, occ = (2.1, "prepare", "online") if el["actor_role"] == "applicant" \
                else (3.35, "record", "internal")
        if el["kind"] == "correction" and not el["must_precede"]:
            phase = 8.1           # a post-decision condition (replanting, completion report)
        if el["kind"] == "notice" and any(
                e["kind"] in ("fee_waiver", "appeal") for e in stat["skeleton"]
                if e["element_id"] in el["must_precede"]):
            phase = 8.05          # an enforcement notice, not an application notice
        if el["optional"] and chance(rng, 0.25):
            unimplemented.append({"element_id": el["element_id"], "name": el["name"],
                                  "why": "the local rule is silent; staff do not offer it"})
            continue
        # standing obligations: publishing the checklist/rules, and maintaining a
        # registry or filing periodic reports. They are real agency activities but
        # no individual applicant walks through them.
        standing = (el["kind"] == "checklist_publication"
                    or (el["kind"] == "record" and el["actor_role"] == "agency"
                        and not el["must_precede"]))
        role, counterparty = _element_actor(el, jur, rule, dom, lead, phase, standing)
        if standing and el["kind"] == "record":
            vis = "applicant_facing" if "public" in el["name"].lower() else "staff_only"
        ain, aout = _artifacts(el["kind"], dom, terminal)
        name, variants = _element_action(el, dom, rule, jur, lead, phase, standing, counterparty)
        other_programs = [x.lower() for x in dom["programs"] if x != rule["program_name"]]
        pool = list(variants) + [
            n for n in dom.get("local_names", {}).get(el["element_id"], [])
            if not any(w in n.lower() for p_ in other_programs for w in [p_.replace(" program", "")])]
        local = pick(rng, pool) if (pool and chance(rng, knobs["naming_drift"])) else None
        if local == name:
            local = None
        fee = None
        if el["kind"] == "fee":
            fee = {"amount": rule["fee"]["amount"], "when": rule["fee"]["when"],
                   "label": rule["fee"]["label"]}
        if el["kind"] == "third_party_option" and chance(rng, 0.45):
            deviations.append({"element_id": el["element_id"],
                               "deviation": "the third-party report is filed with the agency and signed by the "
                                            "contractor, so the statute's confidentiality is not preserved in practice"})
        notes = []
        if el["shot_clock_days"]:
            notes.append("shot clock: %d days" % el["shot_clock_days"])
        if standing:
            notes.append("standing obligation of the agency, not a per-case step")
        if counterparty and el["actor_role"] in ("applicant", "third_party"):
            notes.append("counterparty: %s" % actor_name(jur, counterparty, rule["domain"]))
        rows.append(dict(phase=phase, name=name, local_name=local, role=role, visibility=vis,
                         element_ref=el["element_id"], occasion=occ, ain=ain, aout=aout,
                         timing=_timing(world, cls, jur["id"], el["shot_clock_days"], rng, dom["pace"]), fee=fee,
                         optional=el["optional"], p_occurs=None, standing=standing,
                         counterparty=counterparty,
                         element_text=el["name"],
                         span={"quote": el["name"],
                               "cite": "%s %s" % (stat["cite"], el["text_anchor"])},
                         flow_gate={"appeal": "if_appealed", "fee_waiver": "if_denied"}.get(el["kind"], "always"),
                         notes="; ".join(notes)))

    # ---- 2. locally added elements -----------------------------------------
    from .local_rules import ADDED_ELEMENTS, optional_consultation_label
    for ae in rule["added_elements"]:
        spec = ADDED_ELEMENTS[ae["kind"]]
        role = spec["role"] if spec["role"] in jur["depts"] or spec["role"] == "applicant" else lead
        fee = None
        if ae["fee"]:
            cap = max(120, int(DOMAINS[rule["domain"]]["fee_range"][1] * 1.6))
            fee = {"amount": min(ae["fee"], cap), "when": "at submittal", "label": ae["name"],
                   "refundable": ae["kind"] == "deposit"}
        names = spec.get("names_for", {}).get(rule["domain"], spec["names"])
        if ae['kind'] == 'pre_application_meeting' and not ae['mandatory']:
            # Normalize the pool as well as its chosen canonical name, preserving
            # its size/order and the RNG sequence when excluding that name.
            names = [optional_consultation_label(n) for n in names]
        variants = [n for n in names if n != ae["name"]]
        local = pick(rng, variants) if (variants and chance(rng, knobs["naming_drift"])) else None
        rows.append(dict(phase=ADDED_PHASE[ae["kind"]], name=ae["name"], local_name=local, role=role,
                         visibility=spec["visibility"], element_ref=ae["element_id"],
                         occasion=spec["occasion"], ain=[], aout=list(spec["out"]),
                         timing=_timing_added(world, spec, jur["id"], rng, dom["pace"]), fee=fee,
                         optional=not ae["mandatory"], p_occurs=None, standing=False,
                         counterparty=None, element_text=ae["name"],
                         span={"quote": ae["name"], "cite": rule["cite"]},
                         flow_gate="if_appealed" if ae["kind"] == "appeal_to_hearing_officer" else "always",
                         notes="added by %s (%s)" % (rule["cite"], rule["instrument"])))

    # ---- 3. back office ----------------------------------------------------
    cands = [t for t in dom["backoffice"] if t in BACKOFFICE]
    # a review queue exists wherever there is a technical review
    if rule["domain"] not in ("home_business", "backyard_hens", "contractor_registration") \
            and "plan_check_queue" not in cands:
        cands.append("plan_check_queue")
    if "routing" not in cands:
        cands.append("routing")
    chosen = [t for t in cands if chance(rng, knobs["p_backoffice"])]
    for t in ("intake_screening", "records_archive"):      # always present in practice
        if t in cands and t not in chosen:
            chosen.append(t)
    # size the process into [8, 20] activities
    pool = [t for t in cands if t not in chosen]
    while len(rows) + len(chosen) < 9 and pool:
        chosen.append(pool.pop(0))
    while len(rows) + len(chosen) > 20 and chosen:
        drop = next((t for t in reversed(chosen) if BACKOFFICE[t]["visibility"] == "staff_only"), chosen[-1])
        chosen.remove(drop)
    for t in chosen:
        spec = BACKOFFICE[t]
        role = spec["role"]
        if role not in jur["depts"] and role not in ("applicant", "third_party", "health",
                                                     "assessor", "state_agency", "tenant"):
            role = lead
        f = _speed_for(world, jur["id"]) * dom["pace"] * (0.85 + 0.3 * rng.random())
        rows.append(dict(phase=spec["phase"], name=spec["names"][0],
                         local_name=(pick(rng, spec["names"][1:]) if len(spec["names"]) > 1
                                     and chance(rng, knobs["naming_drift"]) else None),
                         role=role, visibility=spec["visibility"], element_ref=None,
                         occasion=spec["occasion"], ain=[], aout=list(spec["out"]),
                         timing={"dist": "lognormal", "median_days": round(spec["median"] * f, 1),
                                 "p90_days": round(spec["p90"] * f, 1)},
                         fee=None, optional=False, p_occurs=None,
                         standing=t in STANDING_TAGS, counterparty=None,
                         element_text=None, span=None,
                         flow_gate={"supervisor_denial": "if_denied", "appeal_docket": "if_appealed",
                                    "reinspection_sched": "if_rework"}.get(t, "always"),
                         notes=spec["notes"], bo_tag=t))

    # ---- 4. order, ids, optional occurrence probabilities -------------------
    # enforce the statute's `must_precede` constraints on the phase ordering
    el_phase = {r["element_ref"]: r for r in rows if r["element_ref"]}
    for _ in range(3):
        for el in stat["skeleton"]:
            me = el_phase.get(el["element_id"])
            if not me:
                continue
            for tgt in el["must_precede"]:
                other = el_phase.get(tgt)
                if other and me["phase"] >= other["phase"]:
                    me["phase"] = round(other["phase"] - 0.05, 3)
    rows.sort(key=lambda r: (r["phase"], r["visibility"] != "applicant_facing"))
    activities = []
    for i, r in enumerate(rows, start=1):
        p_occ = None
        if r["optional"]:
            p_occ = round(weighted(rng, [(0.2, 0.3), (0.35, 0.4), (0.6, 0.3)]), 2)
        act = {
            "id": "A%02d" % i, "name": r["name"], "local_name": r["local_name"], "actor": r["role"],
            "counterparty": r.get("counterparty"),
            "visibility": r["visibility"], "element_ref": r["element_ref"],
            "element_text": r.get("element_text"), "span": r.get("span"),
            "occasion": r["occasion"],
            "artifacts_in": r["ain"], "artifacts_out": r["aout"], "timing": r["timing"],
            "fee": r["fee"], "rework": None, "optional": r["optional"], "p_occurs": p_occ,
            "flow_gate": r["flow_gate"], "notes": r["notes"],
        }
        if "bo_tag" in r:
            act["backoffice_tag"] = r["bo_tag"]
        # standing obligations (publish a checklist, maintain the platform, report
        # to the state, audit a sample) are not walked by an individual applicant
        act["per_case"] = not (r.get("standing") or r["phase"] < 1.0
                               or r.get("bo_tag") in STANDING_TAGS)
        # blocking = the case waits for it (on the applicant's critical path)
        act["blocking"] = not (r.get("bo_tag") in NON_BLOCKING or r["phase"] >= 8.0)
        activities.append(act)

    # a statute with no `fee` element still has a locally adopted fee: it is
    # collected with the application (the commonest real arrangement)
    if not any(a["element_ref"] and _is_kind(stat, a["element_ref"], "fee") for a in activities):
        host = next((a for a in activities if a["actor"] == "applicant"
                     and a["element_ref"] and a["element_ref"].startswith("E")), None)
        if host:
            host["fee"] = {"amount": rule["fee"]["amount"], "when": rule["fee"]["when"],
                           "label": rule["fee"]["label"]}
            host["notes"] = (host["notes"] + "; fee set by %s" % rule["cite"]).strip("; ")

    # A staff-only step that implements a *public* mandate (a statute element, or a
    # locally added element carried in an ordinance/resolution) is invisible to the
    # applicant but inferable from public law: any document restating the mandate
    # discloses it. DESIGN.md "Wave-2/3 finding: statutory mandates cannot be
    # hidden". This is a second axis, not a relabel -- `visibility` is unchanged.
    _skel_ids = {e["element_id"] for e in stat["skeleton"]}
    _local_ids = {e["element_id"] for e in rule["added_elements"]}
    _public_local = rule["instrument"] in ("ordinance", "resolution")
    for a in activities:
        ref = a["element_ref"]
        a["statutorily_disclosed"] = bool(
            a["visibility"] == "staff_only" and ref
            and (ref in _skel_ids or (ref in _local_ids and _public_local)))

    by_id = {a["id"]: a for a in activities}
    idx = {a["id"]: i for i, a in enumerate(activities)}

    def find(pred):
        return next((a for a in activities if pred(a)), None)

    # ---- 5. rework loops ---------------------------------------------------
    app_act = find(lambda a: a["element_ref"] and a["element_ref"].startswith("E")
                   and a["actor"] == "applicant" and a["occasion"] in ("counter", "online"))
    screen = find(lambda a: a.get("backoffice_tag") == "intake_screening")
    review = find(lambda a: a.get("backoffice_tag") in ("plan_check_queue", "exception_queue", "second_review"))
    insp = find(lambda a: a["element_ref"] and _is_kind(stat, a["element_ref"], "inspection"))
    corr = find(lambda a: a["element_ref"] and _is_kind(stat, a["element_ref"], "correction"))
    reinsp = find(lambda a: a["element_ref"] and a["element_ref"].startswith("L")
                  and "inspection" in (a["name"] or "").lower())
    n_loops = 0
    if screen and app_act:
        screen["rework"] = {"p_trigger": round(0.22 + 0.24 * rng.random(), 2), "back_to": app_act["id"],
                            "reason": "incomplete application: missing documents or unpaid fee"}
        n_loops += 1
    if review and app_act and chance(rng, 0.85):
        review["rework"] = {"p_trigger": round(0.2 + 0.25 * rng.random(), 2), "back_to": app_act["id"],
                            "reason": "plan check comments: applicant resubmits corrected documents"}
        n_loops += 1
    dec = find(lambda a: a["element_ref"] and _is_kind(stat, a["element_ref"], "decision"))
    if corr:
        # violations -> corrections -> re-check; the loop closes on whatever
        # verifies the corrections (a re-inspection if the city added one, else
        # the decision step), and always points backwards.
        src = next((a for a in (reinsp, dec, insp) if a and idx[a["id"]] > idx[corr["id"]]), None)
        if src:
            src["rework"] = {"p_trigger": round(0.22 + 0.26 * rng.random(), 2), "back_to": corr["id"],
                             "reason": "corrections incomplete at re-inspection: back to the correction list"}
            n_loops += 1
    elif insp and app_act and idx[insp["id"]] > idx[app_act["id"]]:
        insp["rework"] = {"p_trigger": round(0.24 + 0.26 * rng.random(), 2), "back_to": app_act["id"],
                          "reason": "violations found at inspection must be corrected and re-submitted"}
        n_loops += 1
    if n_loops == 0 and activities and app_act:
        if dec and idx[dec["id"]] > idx[app_act["id"]]:
            dec["rework"] = {"p_trigger": 0.18, "back_to": app_act["id"],
                             "reason": "application returned for correction before a decision issues"}

    # ---- 6. edges ----------------------------------------------------------
    edges = []
    for a, b in zip(activities, activities[1:]):
        etype = "sequence"
        if b["optional"]:
            etype = "optional"
        elif a["actor"] != b["actor"]:
            etype = "handoff"
        cond = ""
        if b["flow_gate"] == "if_denied":
            etype, cond = "optional", "only on a denial"
        elif b["flow_gate"] == "if_appealed":
            etype, cond = "optional", "only if the applicant appeals"
        elif b["flow_gate"] == "if_rework":
            etype, cond = "optional", "only where corrections were required"
        elif b["optional"]:
            cond = "applicant elects this step" if b["actor"] == "applicant" else "where staff determine it is needed"
        edges.append({"from": a["id"], "to": b["id"], "type": etype, "condition": cond})
    for a in activities:
        if a["rework"]:
            edges.append({"from": a["id"], "to": a["rework"]["back_to"], "type": "rework",
                          "condition": a["rework"]["reason"]})
    tp = find(lambda a: a["element_ref"] and _is_kind(stat, a["element_ref"], "third_party_option"))
    if tp and insp:
        edges.append({"from": tp["id"], "to": insp["id"], "type": "optional",
                      "condition": "the third-party report may substitute for the agency inspection"})

    # ---- 7. actors ---------------------------------------------------------
    roles = []
    for a in activities:
        if a["actor"] not in roles:
            roles.append(a["actor"])
    for must in ("applicant", lead):
        if must not in roles:
            roles.insert(0, must)
    while len(roles) < 4:
        for extra in ("records", "finance", "clerk", "code_enforcement"):
            if extra not in roles and extra in jur["depts"]:
                roles.append(extra)
                break
        else:
            break
    actors = [{"id": r, "name": actor_name(jur, r, rule["domain"]),
               "dept": None if r in ("applicant", "third_party", "tenant")
                       else jur["depts"].get(r, jur["umbrella"]),
               "type": "external" if r in ("applicant", "third_party", "tenant") else
                       ("external_government" if r in ("assessor", "state_agency", "health")
                        and jur["kind"] != "county" else "agency")}
              for r in roles]

    # ---- 8. prior-version diff --------------------------------------------
    prior = None
    if rule["prior_version"]:
        changes = list(rule["prior_version"]["changes"])
        if rule.get("prior_dropped_element"):
            dropped = next((a for a in activities if a["element_ref"] == rule["prior_dropped_element"]), None)
            if dropped:
                changes.append("the step \"%s\" (%s) did not exist" % (dropped["name"], dropped["id"]))
        prior = {"version": 1, "version_date": rule["prior_version"]["adopted"],
                 "cite": rule["prior_version"]["cite"],
                 "fee_amount": rule["prior_version"]["fee_amount"], "changes": changes}

    denial = DENIAL_BASE[rule["domain"]] * (0.7 + 0.6 * rng.random())
    proc = {
        "model_id": mid,
        "source": "designed",
        "jurisdiction": jur["name"],
        "jur_id": jur["id"],
        "state": jur["state"],
        "stat_id": rule["stat_id"],
        "statute_cite": stat["cite"],
        "domain": rule["domain"],
        "program_name": rule["program_name"],
        "local_rule_cite": rule["cite"],
        "local_rule_instrument": rule["instrument"],
        "lead_department": actor_name(jur, lead, rule["domain"]),
        "form_name": dom["app_form"],
        "checklist_name": dom["checklist"],
        "permit_system": jur["permit_system"],
        "version": rule["version"],
        "version_date": rule["adopted"],
        "actors": actors,
        "activities": activities,
        "edges": edges,
        "terminal_artifact": terminal,
        "denial_rate": round(denial, 3),
        "p_appeal_if_denied": knobs["p_appeal_if_denied"],
        "unimplemented_elements": unimplemented,
        "deviations": deviations,
        "prior_version": prior,
        "notes": ("Designed process as operated by %s under %s. %d activities, %d actors; "
                  "%d applicant-facing, %d applicant-inferable, %d staff-only."
                  % (jur["name"], rule["cite"], len(activities), len(actors),
                     sum(1 for a in activities if a["visibility"] == "applicant_facing"),
                     sum(1 for a in activities if a["visibility"] == "applicant_inferable"),
                     sum(1 for a in activities if a["visibility"] == "staff_only"))),
    }
    from .decision import attach as _attach_decision
    _attach_decision(proc, stat, rule, knobs, world["seed"])
    return proc


def _timing_added(world: dict, spec: dict, jur_id: str, rng, pace: float = 1.0) -> dict:
    f = _speed_for(world, jur_id) * pace * (0.85 + 0.3 * rng.random())
    return {"dist": "lognormal", "median_days": round(spec["median"] * f, 1),
            "p90_days": round(spec["p90"] * f, 1)}


def _is_kind(stat: dict, element_ref: str, kind: str) -> bool:
    return any(e["element_id"] == element_ref and e["kind"] == kind for e in stat["skeleton"])


def build_processes(world: dict, statutes: dict, rules: dict) -> dict[str, dict]:
    return {mid: build_process(world, statutes, rule) for mid, rule in sorted(rules.items())}
