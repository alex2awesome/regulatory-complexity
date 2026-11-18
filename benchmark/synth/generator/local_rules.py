"""local_rule_truth: how each jurisdiction fills the statute's open choices.

Three mechanisms from docs/design.md §10 are modelled explicitly:

1. **Retrofit** (`retrofit: true`) -- the jurisdiction already ran a program
   before the statute; the current rule is version 2 and the *prior* version is
   the pre-statute program (different fee, different department, no statutory
   checklist). Hayward's amnesty program is the exemplar.
2. **Template lineage** (`lineage_from`) -- with `p_template_lineage` a
   jurisdiction copies another's rule: identical added elements, near-identical
   choices, and a *tell* (a stray cross-reference to the source's municipal
   code) that a careful reader can spot. Implementations are therefore not
   independent draws.
3. **Versioning** -- `prior_version` carries adoption dates and the changed
   choices, which is what makes stale artifacts checkable.
"""
from __future__ import annotations

from .domains import DOMAINS
from .rng import chance, dadd, pick, pick_n, sub_rng, weighted
from . import capacity
from .world import actor_name, jur_by_id

# Hourly rate used to derive flat fees ("N inspector-hours x rate"), per jurisdiction.
# The hand-written jurisdictions' adopted rates, kept literal so that
# world_model_version 1 stays byte-identical. A generated county's rate is
# derived from the measured wage gradient instead: see capacity.hourly_rate.
HOURLY = {"J1": 190, "J2": 235, "J3": 155, "J4": 176, "K1": 165, "K2": 148}

# --- values for the substantive open choices (domain.choice_id -> variants) ---
CHOICE_VALUES: dict[str, list[str]] = {
    "unpermitted_unit_amnesty.C3": [
        "a signed and stamped letter from a licensed professional, an assessor record showing the unit, escrow documents, or prior code enforcement records",
        "an assessor record or utility bill predating January 1, 2020, plus an owner affidavit under penalty of perjury",
        "any two of: licensed professional letter, escrow documents, dated photographs, prior permit or code enforcement record",
    ],
    "unpermitted_unit_amnesty.C5": [
        "units on parcels with up to four dwelling units are eligible",
        "units on single-family and duplex parcels only; multifamily parcels use the standard permit process",
        "all residentially zoned parcels are eligible, including mixed-use parcels with residential above ground floor",
    ],
    "str_registration.C3": [
        "no cap on registrations; hosted rentals unlimited, unhosted rentals limited to 120 nights per year",
        "a citywide cap of 250 non-hosted registrations, allocated by lottery each January",
        "no cap; one registration per host, primary residence only",
    ],
    "str_registration.C5": [
        "self-certification on a signed life-safety checklist; no agency inspection",
        "an agency inspection before the first registration, then self-certification at renewal",
        "an agency inspection every third year and after any substantiated complaint",
    ],
    "sidewalk_vending.C3": [
        "no vending within 15 feet of a crosswalk, transit shelter, or building entrance; no vending in residential zones after 8:00 p.m.",
        "vending permitted 7:00 a.m. to 9:00 p.m. citywide; stationary vending prohibited in the two certified farmers-market blocks during market hours",
        "vending permitted in commercial zones only, 6:00 a.m. to 10:00 p.m., with a 4-foot pedestrian path maintained at all times",
    ],
    "sidewalk_vending.C5": [
        "English and Spanish",
        "English and Vietnamese",
        "English, Spanish, and Tagalog (three languages, exceeding the statutory minimum)",
    ],
    "tree_removal.C3": [
        "any tree 12 inches or more in diameter at breast height, and any native oak 6 inches or more",
        "any tree 18 inches or more in diameter at breast height",
        "any tree on the designated heritage species list regardless of size, plus any tree 14 inches or more",
    ],
    "tree_removal.C4": [
        "two 24-inch box replacement trees per removed tree, or an in-lieu fee of $450 per tree into the Tree Fund",
        "one-for-one replacement with a 15-gallon tree, or a $250 in-lieu payment",
        "replacement at three inches of new trunk diameter for every inch removed, or an appraised-value in-lieu fee",
    ],
    "home_business.C3": [
        "no more than one nonresident employee, no more than four customer trips per day, no exterior signage, no outdoor storage",
        "no nonresident employees, no customer visits, no signage, and no more than 25 percent of the floor area",
        "no more than two nonresident employees and eight customer trips per day; one 2-square-foot sign permitted",
    ],
    "home_business.C5": [
        "the permit runs with the business license and renews annually",
        "a one-time registration; no renewal unless the activity changes",
        "the permit renews every two years with a self-certification",
    ],
    "mobile_food.C3": [
        "a signed commissary agreement on the agency's form, verified by a call to the commissary operator",
        "a commissary agreement plus a copy of the commissary's current health permit; re-verified annually",
        "a commissary agreement; verification by inspection of the commissary during the pre-operational inspection",
    ],
    "mobile_food.C4": [
        "two routine inspections per year for units with cooking, one for prepackaged units",
        "three routine inspections per year for all mobile food facilities",
        "one routine inspection per year plus one unannounced inspection at a commissary",
    ],
    "solar_auto_permit.C4": [
        "inspections are scheduled for the next business day; installers may request a two-hour window",
        "inspections are batched Tuesdays and Thursdays and scheduled within five business days",
        "same-day inspection if the request is submitted before 7:00 a.m.; otherwise next business day",
    ],
    "solar_auto_permit.C5": [
        "structural review is required for roofs framed before 1960, which routes the application out of the automated path",
        "no structural review for systems under 5 pounds per square foot dead load; installer certification accepted",
        "structural review required only where the platform flags a truss-framed roof with spans over 30 feet",
    ],
    "rental_inspection.C3": [
        "a four-year cycle, with annual inspection of properties with two or more substantiated violations",
        "a three-year cycle for buildings built before 1978 and a four-year cycle for all others",
        "a four-year cycle, self-certification permitted in the intervening years",
    ],
    "rental_inspection.C4": [
        "20 percent of units in a building, minimum two units, plus all common areas",
        "every unit is inspected; no sampling",
        "30 percent of units, escalating to 100 percent if two or more units fail",
    ],
    "rental_inspection.C6": [
        "owner-occupied duplexes and single-family rentals are exempt",
        "no exemptions; every rental unit is registered",
        "properties with a current certificate from a state or federal inspection program are exempt for that cycle",
    ],
    "backyard_hens.C3": [
        "up to six hens; no roosters",
        "up to four hens on lots under 5,000 square feet and up to eight on larger lots; no roosters",
        "up to twelve hens with a ministerial permit; no roosters, no slaughtering on site",
    ],
    "backyard_hens.C4": [
        "the coop must be at least 15 feet from any dwelling on an adjacent parcel and 5 feet from any property line",
        "the coop must be at least 25 feet from any neighboring dwelling and located in the rear yard",
        "the coop must be at least 10 feet from a property line; no setback from the owner's own dwelling",
    ],
    "backyard_hens.C5": [
        "the permit is issued once and does not expire unless the parcel changes hands",
        "the permit renews annually with a $20 renewal fee",
        "the permit renews every three years with a self-certification",
    ],
    "special_event.C3": [
        "$1,000,000 per occurrence commercial general liability naming the city as additional insured; $2,000,000 for events with alcohol",
        "$500,000 per occurrence for events under 500 attendees; $2,000,000 above that",
        "$1,000,000 per occurrence, waivable for expressive activity with fewer than 100 participants",
    ],
    "special_event.C4": [
        "60 days before the event; 90 days if a street closure is requested",
        "45 days before the event, with a late-filing surcharge inside 30 days",
        "60 days before the event, reduced to 10 days for expressive activity",
    ],
    "special_event.C6": [
        "fees are waived for expressive activity on written request, with a sworn statement of purpose",
        "fees are waived for expressive activity and reduced 50 percent for registered nonprofits",
        "fees are waived for expressive activity; city service costs are still charged at cost for street closures",
    ],
    "well_permit.C3": [
        "100 feet from a septic leach field, 50 feet from a sewer line, and 10 feet from a property line",
        "150 feet from a septic leach field and 25 feet from a property line (exceeds the state minimum)",
        "the state standard setbacks, with an administrative waiver available on a hydrogeologic report",
    ],
    "well_permit.C4": [
        "the annular seal is inspected; destruction is also inspected",
        "the annular seal and the final well head are inspected, and a pump test report is required",
        "the annular seal is inspected; the contractor may self-certify the seal on monitoring wells",
    ],
    "well_permit.C5": [
        "cities in the county have delegated well permitting to Environmental Health",
        "the county permits wells in the unincorporated area only; cities retain authority",
        "the county permits all wells, and cities charge a separate zoning clearance",
    ],
    "contractor_registration.C3": [
        "registration is annual, expiring December 31 regardless of issue date",
        "registration is biennial and expires on the anniversary of issuance",
        "registration runs with the state license expiration date",
    ],
    "contractor_registration.C4": [
        "insurance and workers' compensation are verified at issuance and at each renewal",
        "insurance is verified at issuance only; the registrant certifies continuing coverage",
        "insurance is verified at issuance, at renewal, and on any permit application over $50,000 in valuation",
    ],
}

# ------------------------------------------------------- locally added steps
# kind -> how to instantiate it as a process activity later.
ADDED_ELEMENTS: dict[str, dict] = {
    "pre_application_meeting": dict(
        names=["Attend a pre-application meeting with staff", "Attend the mandatory pre-submittal consultation",
               "Attend a pre-application counter appointment"],
        role="lead_permits", occasion="counter", visibility="applicant_facing",
        median=9, p90=25, fee=None, out=["pre-application notes"], mand_p=0.6),
    "neighbor_notification": dict(
        names=["Mail notice to neighbours within 300 feet", "Send a courtesy notice to adjacent property owners",
               "Post notice on the property for 10 days"],
        role="planning", occasion="mail", visibility="applicant_inferable",
        median=7, p90=16, fee=(35, 140), out=["notice affidavit"], mand_p=0.8),
    "extra_inspection": dict(
        names=["Re-inspect after the corrections", "Inspect for final compliance",
               "Re-inspect with the supervising inspector"],
        role="building", occasion="site_visit", visibility="applicant_facing",
        median=11, p90=27, fee=(85, 320), out=["re-inspection report"], mand_p=0.9),
    "deposit": dict(
        names=["Post a refundable performance deposit", "Post a cost-recovery deposit against staff time"],
        names_for={"special_event": ["Post a cleanup and damage deposit", "Post a refundable street-closure deposit"],
                   "tree_removal": ["Post a tree protection bond", "Post a replacement planting deposit"],
                   "well_permit": ["Post a well destruction security deposit"]},
        role="finance", occasion="online", visibility="applicant_facing",
        median=1, p90=4, fee=(250, 1500), out=["deposit receipt"], mand_p=1.0),
    "online_portal": dict(
        names=["Create a portal account and upload the documents", "Submit electronically (mandatory)",
               "Register in the online permit center"],
        role="applicant", occasion="online", visibility="applicant_facing",
        median=1, p90=3, fee=None, out=["portal case number"], mand_p=1.0),
    "appeal_to_hearing_officer": dict(
        names=["File an appeal to the Administrative Hearing Officer", "File an appeal to the Board of Appeals",
               "Request a hearing before the hearing officer"],
        role="hearing", occasion="hearing", visibility="applicant_facing",
        median=34, p90=72, fee=(150, 600), out=["hearing officer decision"], mand_p=0.5),
    "community_meeting": dict(
        names=["Convene a neighbourhood meeting", "Hold a community information meeting"],
        role="applicant", occasion="hearing", visibility="applicant_facing",
        median=21, p90=45, fee=None, out=["meeting summary"], mand_p=0.7),
    "affidavit": dict(
        names=["Sign and notarise the owner affidavit", "Sign the declaration under penalty of perjury",
               "Sign and notarise the indemnification and hold-harmless agreement"],
        role="applicant", occasion="counter", visibility="applicant_facing",
        median=4, p90=12, fee=None, out=["notarized affidavit"], mand_p=1.0),
    "fire_clearance": dict(
        names=["Obtain the Fire Prevention clearance", "Obtain the Fire Marshal sign-off", "Obtain the life-safety clearance from Fire"],
        role="fire", occasion="internal", visibility="applicant_inferable",
        median=12, p90=30, fee=(60, 275), out=["fire clearance"], mand_p=0.85),
    "business_license_prereq": dict(
        names=["Obtain the business licence first", "Obtain the business tax certificate first",
               "Register the business concurrently"],
        role="finance", occasion="online", visibility="applicant_facing",
        median=6, p90=15, fee=(40, 180), out=["business tax certificate"], mand_p=1.0),
}


def optional_consultation_label(name: str) -> str:
    """Describe the sampled optional step without making it mandatory in prose."""
    return name.replace('the mandatory pre-submittal consultation',
                        'an optional pre-submittal consultation')

# Which added elements plausibly attach to which domain.
ADDED_BY_DOMAIN = {
    "unpermitted_unit_amnesty": ["pre_application_meeting", "extra_inspection", "affidavit", "online_portal", "deposit"],
    "str_registration": ["online_portal", "business_license_prereq", "extra_inspection", "neighbor_notification", "appeal_to_hearing_officer"],
    "sidewalk_vending": ["business_license_prereq", "pre_application_meeting", "extra_inspection", "online_portal"],
    "tree_removal": ["neighbor_notification", "community_meeting", "deposit", "extra_inspection", "pre_application_meeting"],
    "home_business": ["business_license_prereq", "neighbor_notification", "affidavit", "online_portal"],
    "mobile_food": ["fire_clearance", "extra_inspection", "business_license_prereq", "online_portal"],
    "solar_auto_permit": ["online_portal", "extra_inspection", "fire_clearance"],
    "rental_inspection": ["extra_inspection", "online_portal", "appeal_to_hearing_officer", "deposit"],
    "backyard_hens": ["neighbor_notification", "extra_inspection", "affidavit"],
    "special_event": ["deposit", "pre_application_meeting", "fire_clearance", "community_meeting", "online_portal"],
    "well_permit": ["extra_inspection", "deposit", "affidavit", "online_portal"],
    "contractor_registration": ["business_license_prereq", "online_portal", "appeal_to_hearing_officer", "affidavit"],
}

STRICTER = {
    "unpermitted_unit_amnesty": ["smoke and carbon monoxide alarms required in every sleeping room, not only in the unit",
                                 "a 7-foot minimum ceiling height, exceeding the state standard",
                                 "the deed restriction must be recorded before the certificate issues"],
    "str_registration": ["a 24-hour local contact must be within 25 miles",
                         "one off-street parking space per bedroom offered",
                         "quiet hours 9:00 p.m. to 8:00 a.m. written into the registration conditions"],
    "sidewalk_vending": ["a city-issued badge must be worn and visible at all times",
                         "carts must be removed from the right-of-way nightly",
                         "a certified food handler card is required for every worker on the cart"],
    "tree_removal": ["a bond equal to the appraised tree value for construction near a protected tree",
                     "an arborist report is required for every application, not only contested ones",
                     "removal is prohibited during nesting season, February 1 to August 31"],
    "home_business": ["no commercial vehicle over 10,000 pounds may be parked on the parcel",
                      "deliveries limited to standard parcel carriers"],
    "mobile_food": ["a grease interceptor at the commissary is verified annually",
                    "propane systems must carry a current third-party inspection tag",
                    "a hand-wash sink with 5 gallons of warm water, exceeding the state minimum"],
    "solar_auto_permit": ["a roof-mounted rapid shutdown label placard in a city-specified format",
                          "pre-1960 roofs require a stamped structural letter"],
    "rental_inspection": ["a written tenant complaint log must be produced at inspection",
                          "every unit must have a working GFCI in the kitchen and bath regardless of construction date",
                          "violations affecting habitability must be corrected in 14 days, not 30"],
    "backyard_hens": ["coops must be cleaned weekly and waste stored in a sealed container",
                      "no coop within 5 feet of a creek or drainage channel"],
    "special_event": ["a traffic control plan stamped by a licensed engineer for any street closure",
                      "two certified crowd managers per 250 attendees",
                      "a waste diversion plan for events over 1,000 attendees"],
    "well_permit": ["a hydrogeologic report for any well within 500 feet of a known plume",
                    "destruction permits require a licensed geologist's log",
                    "a 48-hour notice before the seal inspection"],
    "contractor_registration": ["a $5,000 surety bond in addition to the state bond",
                                "proof of a local business address or registered agent"],
}


def _fee_amount(rng, jur_id: str, domain: str, jur: dict | None = None) -> tuple[int, str]:
    """A plausible fee plus how it was derived (cost-recovery arithmetic)."""
    lo, hi = DOMAINS[domain]["fee_range"]
    rate = HOURLY.get(jur_id) or capacity.hourly_rate(jur or {"pop": 200_000})
    if "hour" in DOMAINS[domain]["fee_basis"] or chance(rng, 0.45):
        hours = max(1, round((lo + (hi - lo) * rng.random()) / rate))
        amt = int(hours * rate)
        if amt < lo:
            amt, hours = int(2 * rate), 2
        return min(amt, hi), "%d staff hours x $%d adopted hourly rate" % (hours, rate)
    span = hi - lo
    amt = int(round((lo + span * (0.25 + 0.6 * rng.random())) / 5.0) * 5)
    return amt, "cost-allocation study, rounded to the nearest $5"


def _fee_value(rng, domain: str, amount: int) -> str:
    if domain == "rental_inspection":
        return "$%d per unit per year (minimum $%d per property)" % (max(18, amount // 3), amount)
    if domain == "mobile_food":
        return "$%d plan review plus $%d annual health permit" % (amount, max(120, int(amount * 0.7)))
    if domain == "special_event":
        return "$%d application fee plus actual cost of police, fire, and public works services" % amount
    return "$%d" % amount


def _choice_value(rng, jur: dict, domain: str, ch: dict, fee_amt: int, lead_role: str) -> str:
    kind, cid = ch["kind"], ch["choice_id"]
    key = "%s.%s" % (domain, cid)
    if kind == "fee_amount":
        return _fee_value(rng, domain, fee_amt)
    if kind == "department":
        return actor_name(jur, lead_role, domain)
    if kind == "portal":
        if "paper" in jur["permit_system"].lower():      # small cities without a portal
            return pick(rng, [
                "by paper application at the %s, or by mail" % jur["depts"].get("lead_permits", "counter"),
                "in person at the %s; forms are emailed on request to %s"
                % (jur["depts"].get("lead_permits", "counter"), jur["email"]),
                "by paper application; %s is used only for building permits" % jur["permit_system"],
            ])
        return pick(rng, [
            "online through %s" % jur["permit_system"],
            "in person at %s, or by email to %s" % (jur["depts"].get("lead_permits", "the counter"), jur["email"]),
            "online through %s; paper applications accepted at the counter" % jur["permit_system"],
        ])
    if kind == "appeal_body":
        return actor_name(jur, pick(rng, ["hearing", "council", "planning"]), domain)
    if kind == "radius":
        return pick(rng, ["100 feet", "150 feet", "300 feet (exceeding the statutory minimum)"])
    if key in CHOICE_VALUES:
        return pick(rng, CHOICE_VALUES[key])
    return pick(rng, ["as provided in the adopting instrument", "per the department's published standards"])


def _instrument(rng, retrofit: bool) -> str:
    return weighted(rng, [("ordinance", 0.58), ("resolution", 0.24), ("admin_policy", 0.18)])


def _cite(rng, jur: dict, instrument: str, year: int) -> str:
    n = 1 + rng.randrange(180)
    if jur["kind"] == "county":
        if instrument == "ordinance":
            return "Ordinance No. %d-%02d" % (year, n % 40 + 1)
        if instrument == "resolution":
            return "Board Resolution No. %d-%03d" % (year, n)
        return "Administrative Directive %s-%02d" % (jur["id"], n % 30 + 1)
    if instrument == "ordinance":
        return "Ordinance No. %02d-%03d" % (year % 100, n)
    if instrument == "resolution":
        return "Resolution No. %02d-%03d" % (year % 100, n)
    return "Administrative Policy %s-%02d" % (jur["umbrella"].split()[0][:2].upper(), n % 30 + 1)


def build_local_rules(world: dict, statutes: dict) -> dict[str, dict]:
    """model_id (`<jur>__<stat>`) -> local_rule_truth."""
    seed = world["seed"]
    knobs = world["knobs"]
    # This world's jurisdictions, which at world_model_version 2 include the
    # generated county panel. The module-level JUR_BY_ID holds only the
    # hand-written four.
    by_id = jur_by_id(world)
    rules: dict[str, dict] = {}
    dated: list[tuple[str, str]] = []   # (adopted, model_id) for lineage ordering

    # ---- pass 1: dates, instrument, program name, choices ----
    for impl in world["implementations"]:
        jur = by_id[impl["jur"]]
        stat = statutes[impl["stat_id"]]
        domain = impl["domain"]
        dom = DOMAINS[domain]
        mid = "%s__%s" % (impl["jur"], impl["stat_id"])
        rng = sub_rng(seed, "local_rule", mid)
        retrofit = impl["retrofit"]

        op = stat["operative"]
        if retrofit:
            first_adopted = dadd(op, -(360 + rng.randrange(900)))
            adopted = dadd(op, rng.randrange(-40, 300))     # the retrofit amendment
        else:
            first_adopted = None
            adopted = dadd(op, 30 + rng.randrange(430))
        instrument = _instrument(rng, retrofit)
        year = int(adopted[:4])
        cite = _cite(rng, jur, instrument, year)

        # the domain's canonical department usually administers, but not always:
        # weights 0.6 / 0.25 / 0.15 over the domain's candidate roles that this
        # jurisdiction actually has (this is open choice C2 in most statutes)
        # "health" resolves to the county health department by agreement even in a
        # city that has none (the real contract-city arrangement)
        cands = [r for r in dom["lead_roles"]
                 if r in jur["depts"] or r == "health"] or ["lead_permits"]
        lead_role = weighted(rng, list(zip(cands, [0.6, 0.25, 0.15][:len(cands)])))
        fee_amt, fee_deriv = _fee_amount(rng, jur["id"], domain, jur)
        program_name = pick(rng, dom["programs"])
        terminal = pick(rng, dom["terminal"])

        choices = {}
        for ch in stat["open_choices"]:
            choices[ch["choice_id"]] = _choice_value(rng, jur, domain, ch, fee_amt, lead_role)

        # locally added elements (0-3)
        n_added = weighted(rng, [(0, 0.18), (1, 0.32), (2, 0.31), (3, 0.19)])
        cand = [k for k in ADDED_BY_DOMAIN[domain]
                if not (k == "appeal_to_hearing_officer"
                        and any(e["kind"] == "appeal" for e in stat["skeleton"]))]
        # coherence: a jurisdiction that chose self-certification does not also
        # add an extra agency inspection
        if any("self-certification" in v or "no agency inspection" in v for v in choices.values()):
            cand = [k for k in cand if k != "extra_inspection"]
        added = []
        for i, kind in enumerate(pick_n(rng, cand, n_added)):
            spec = ADDED_ELEMENTS[kind]
            fee = None
            if spec["fee"] and (kind == "deposit" or chance(rng, 0.6)):
                flo, fhi = spec["fee"]
                fee = int(round((flo + (fhi - flo) * rng.random()) / 5.0) * 5)
            names = spec.get("names_for", {}).get(domain, spec["names"])
            added.append({
                "element_id": "L%d" % (i + 1), "kind": kind, "name": pick(rng, names),
                "mandatory": chance(rng, spec["mand_p"]), "fee": fee,
            })
            # Names and optionality used to be independent: an optional activity
            # could literally be named "mandatory". Normalize only that label,
            # after the existing draws, so all sampled parameters remain stable.
            if kind == "pre_application_meeting" and not added[-1]["mandatory"]:
                added[-1]["name"] = optional_consultation_label(added[-1]["name"])
        stricter = pick_n(rng, STRICTER.get(domain, []), weighted(rng, [(0, 0.3), (1, 0.4), (2, 0.22), (3, 0.08)]))

        rules[mid] = {
            "jur": impl["jur"], "stat_id": impl["stat_id"], "model_id": mid, "domain": domain,
            "instrument": instrument, "cite": cite, "adopted": adopted,
            "effective": dadd(adopted, 30 if instrument == "ordinance" else 0),
            "choices": choices,
            "added_elements": added,
            "stricter_standards": stricter,
            "version": 2 if retrofit else 1,
            "prior_version": None,
            "lineage_from": None,
            "retrofit": retrofit,
            "first_adopted": first_adopted,
            "program_name": program_name,
            "terminal_artifact": terminal,
            "lead_role": lead_role,
            "fee": {"amount": fee_amt, "label": dom["fee_label"], "derivation": fee_deriv,
                    "when": pick(rng, ["at submittal", "prior to project review", "at issuance"]),
                    "adopted_by": ("the %s" % jur["fee_instrument"]) if chance(rng, 0.75)
                                  else "NOT FOUND in any adopted instrument (administratively set)"},
            "text_spec": "",   # filled below, once lineage is known
        }
        dated.append((adopted, mid))

    # ---- pass 2: template lineage (copy from an earlier adopter) ----
    dated.sort()
    for adopted, mid in dated:
        rule = rules[mid]
        rng = sub_rng(seed, "lineage", mid)
        if not chance(rng, knobs["p_template_lineage"]):
            continue
        same_state = by_id[rule["jur"]]["state"]
        srcs = [m for a, m in dated
                if a < adopted and rules[m]["domain"] == rule["domain"] and m != mid]
        if not srcs:
            continue
        prefer = [m for m in srcs if by_id[rules[m]["jur"]]["state"] == same_state]
        pool = prefer if (prefer and not chance(rng, 0.25)) else srcs
        src = pick(rng, pool)
        s = rules[src]
        src_jur = by_id[s["jur"]]
        jur = by_id[rule["jur"]]
        # copy choices, then re-localize the two that cannot travel
        new_choices = dict(rule["choices"])           # start from its own (ids may differ)
        for cid, val in s["choices"].items():
            if cid not in new_choices:
                continue                              # the look-alike statute lacks this choice
            if val == actor_name(src_jur, s["lead_role"], s["domain"]):
                new_choices[cid] = actor_name(jur, rule["lead_role"], rule["domain"])
            elif val.startswith("$") or val.startswith("online through") or "at the counter" in val:
                pass                                  # fees and portals cannot travel
            else:
                new_choices[cid] = val
        rule["choices"] = new_choices
        rule["added_elements"] = [dict(e) for e in s["added_elements"]]
        rule["stricter_standards"] = list(s["stricter_standards"])
        rule["lineage_from"] = s["jur"]
        rule["lineage_note"] = (
            "adapted from %s (%s); the %s carries a tell: %s"
            % (src_jur["name"], s["cite"], rule["instrument"],
               pick(rng, [
                   "one subdivision still cross-references %s Municipal Code" % src_jur["short"],
                   "the handout still says \"%s\" in the signature block" % src_jur["short"],
                   "the findings recite %s's population and unit count" % src_jur["short"],
                   "the fee table footnote refers to %s's cost study" % src_jur["short"],
               ])))

    # ---- pass 3: prior versions ----
    for mid, rule in rules.items():
        rng = sub_rng(seed, "prior", mid)
        jur = by_id[rule["jur"]]
        stat = statutes[rule["stat_id"]]
        if not (rule["retrofit"] or chance(rng, knobs["p_prior_version"])):
            continue
        changes, pchoices = [], dict(rule["choices"])
        # fee changed
        fee_cid = next((c["choice_id"] for c in stat["open_choices"] if c["kind"] == "fee_amount"), None)
        old_fee = int(rule["fee"]["amount"] * pick(rng, [0.72, 0.8, 0.88, 1.08]))
        old_fee = int(round(old_fee / 5.0) * 5)
        if fee_cid:
            pchoices[fee_cid] = _fee_value(rng, rule["domain"], old_fee)
        changes.append("fee was %s (now %s)" % (_fee_value(rng, rule["domain"], old_fee),
                                                _fee_value(rng, rule["domain"], rule["fee"]["amount"])))
        # department changed
        dep_cid = next((c["choice_id"] for c in stat["open_choices"] if c["kind"] == "department"), None)
        if dep_cid and chance(rng, 0.5):
            others = [r for r in DOMAINS[rule["domain"]]["lead_roles"] if r in jur["depts"] and r != rule["lead_role"]]
            if others:
                old_role = pick(rng, others)
                pchoices[dep_cid] = actor_name(jur, old_role, rule["domain"])
                changes.append("%s administered the program; it moved to %s"
                               % (actor_name(jur, old_role, rule["domain"]),
                                  actor_name(jur, rule["lead_role"], rule["domain"])))
                rule["prior_lead_role"] = old_role
        # a step was added at the amendment
        if rule["added_elements"] and chance(rng, 0.7):
            dropped = pick(rng, rule["added_elements"])
            changes.append("no %s step (\"%s\" was added by %s)"
                           % (dropped["kind"].replace("_", " "), dropped["name"], rule["cite"]))
            rule["prior_dropped_element"] = dropped["element_id"]
        if rule["retrofit"]:
            changes.append("the program predated %s: no statutory checklist, no %s cite, and the "
                           "third-party option was not offered"
                           % (stat["bill"], stat["cite"]))
        prior_adopted = rule["first_adopted"] or dadd(rule["adopted"], -(300 + rng.randrange(700)))
        rule["prior_version"] = {
            "adopted": prior_adopted,
            "instrument": "admin_policy" if rule["retrofit"] and chance(rng, 0.5) else rule["instrument"],
            "cite": _cite(rng, jur, rule["instrument"], int(prior_adopted[:4])),
            "choices": pchoices,
            "fee_amount": old_fee,
            "changes": changes,
        }
        rule["version"] = 2

    # ---- pass 4: text_spec for the renderer ----
    for mid, rule in rules.items():
        jur = by_id[rule["jur"]]
        stat = statutes[rule["stat_id"]]
        rule["text_spec"] = (
            "Draft the %s (%s) adopted %s by the %s of %s implementing %s (%s). Recitals: the statute, "
            "the local need, and %s. Operative provisions: name the program \"%s\"; designate %s to "
            "administer; set the fee at %s (%s); adopt the choices %s; add the local steps %s; add the "
            "stricter standards %s; state the terminal document as the %s.%s"
            % (rule["instrument"], rule["cite"], rule["adopted"], jur["council"], jur["name"],
               stat["cite"], stat["bill"],
               "the prior program" if rule["prior_version"] else "the cost study",
               rule["program_name"], actor_name(jur, rule["lead_role"], rule["domain"]),
               rule["choices"].get(next((c["choice_id"] for c in stat["open_choices"]
                                         if c["kind"] == "fee_amount"), "C1"), "$0"),
               rule["fee"]["derivation"],
               "; ".join("%s = %s" % (k, v) for k, v in sorted(rule["choices"].items())),
               "; ".join(e["name"] for e in rule["added_elements"]) or "none",
               "; ".join(rule["stricter_standards"]) or "none",
               rule["terminal_artifact"],
               (" Note the lineage: %s." % rule["lineage_note"]) if rule.get("lineage_note") else ""))

    # ---- pass 5: readings of the statute's decision predicates (decision.py) ----
    from .decision import enabled as _decision_enabled, resolve_readings
    if _decision_enabled(world):
        for mid, rule in rules.items():
            rule["readings"] = resolve_readings(statutes[rule["stat_id"]], rule,
                                                sub_rng(seed, "readings", mid), knobs)
    return rules
