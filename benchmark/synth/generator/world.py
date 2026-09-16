"""world.json: knobs, the two states, six jurisdictions, and who implements what.

Two fictional states so that "same domain, different state" look-alikes exist:
  * **State of Marisol** — the benchmark state (4 jurisdictions, all targets).
  * **State of Corvane** — the neighbour; its jurisdictions implement look-alike
    statutes with different cites and 1-2 different elements, and exist only to
    produce distractors (`neighbor_state` knob).

The four Marisol jurisdictions differ *structurally*, not just by name, because
that is the thing the benchmark asks an agent to recover: Halvern runs intake
through a Permit Services Center, Ellinsport is planning-led with bureaus,
Calder Springs is a 25k-population city that contracts building plan check and
inspection to the county, and Sennet County is the county itself.
"""
from __future__ import annotations

from .domains import DOMAINS, DOMAIN_ORDER, stat_id_for
from .rng import chance, sub_rng, weighted

GENERATOR_VERSION = "synthetic-process-generator/2"

# --------------------------------------------------------------------- knobs
# DESIGN.md table first, then documented generator extensions.
DEFAULT_KNOBS: dict = {
    # DESIGN.md hardness knobs
    "p_publish_program_page": 0.7,
    "p_publish_form": 0.8,
    "p_publish_faq": 0.4,
    "p_publish_fee_schedule": 0.9,
    "p_publish_staff_report": 0.35,
    "p_publish_sop": 0.1,
    "p_third_party_guide": 0.4,
    "p_bill_analysis": 0.8,
    "p_official_stats": 0.3,
    "p_reveal_backoffice_in_comments": 0.15,
    "p_stale": 0.25,
    "p_wrong_fact_user": 0.3,
    "complaint_selection": {"denied": 0.5, "delayed": 0.35, "normal": 0.08, "abandoned": 0.25},
    "distractor_ratio": 4.0,
    "naming_drift": 0.6,
    "neighbor_state": True,
    "n_applicants": 200,
    # ---- generator extensions (not in the DESIGN table; all overridable) ----
    "p_publish_checklist": 0.55,        # a checklist/handout exists (1.0 if the statute mandates publication)
    "p_publish_ordinance": 0.92,        # the adopting instrument is on the code host
    "p_publish_fee_resolution": 0.6,    # a separate fee resolution (exact fees + "supersedes Res. No. X")
    "p_publish_council_minutes": 0.35,
    "p_publish_news": 0.3,
    "p_publish_audit": 0.06,
    "p_publish_forum_thread": 0.25,
    "p_template_lineage": 0.4,          # a local rule is copied from another jurisdiction
    "p_prior_version": 0.4,             # the local rule has a superseded version
    "p_retrofit": 0.3,                  # the program pre-dated the statute and was retrofitted
    "p_backoffice": 0.55,               # per candidate back-office activity
    "p_abandon_total": 0.03,            # target overall abandonment share
    "p_appeal_if_denied": 0.25,
    "max_rework_rounds": 3,
    "visit_accounting_version": 2,      # actual visit indices; base fees once; loop caps count triggers
    "n_applicants_neighbor": 50,
    "max_threads_per_process": 3,
    "filler_cap": 1000,
    "filler_share": 0.6,     # pure filler may be at most this share of all distractors                  # cap on pure-filler distractors (keeps Wave 2 renderable)
    "as_of": "2026-09-15",
    "only_jurisdictions": None,         # e.g. ["J1", "J2"] -> build a tiny world (tests)
    "only_domains": None,               # e.g. ["tree_removal", ...] -> fewer statutes
    "sim_window_days": 760,             # applicants arrive over this window ending at as_of
}

# Canonical actor roles a process can reference; each jurisdiction names them.
DEPT_ROLES = [
    "lead_permits", "building", "planning", "code_enforcement", "fire", "finance",
    "clerk", "attorney", "hearing", "council", "publicworks", "health", "records",
    "assessor", "parks", "police", "housing", "animal", "arborist", "state_agency",
]

# ------------------------------------------------------------- jurisdictions
JURISDICTIONS: list[dict] = [
    dict(
        id="J1", name="City of Halvern", short="Halvern", kind="city", state="Marisol",
        pop=148300, style="permit_center",
        umbrella="Development Services Department",
        address="777 Mercer Street, 1st Floor, Halvern, MR 94088",
        phone="(510) 583-4000", hours="Monday-Thursday 8:00 a.m.-4:00 p.m., Friday 8:00 a.m.-noon",
        host="www.halvern.gov", email="permits@halvern.gov",
        permit_system="TrakIT (e-Permits portal)",
        subreddit="r/Halvern", legislative_host="halvern.legistream.com",
        code_host="library.municodex.com/mr/halvern",
        news=("The Halvern Beacon", "www.halvernbeacon.com"),
        council="City Council", council_cycle="first and third Tuesday",
        fee_instrument="Master Fee Schedule, adopted annually by resolution",
        depts={
            "lead_permits": "Permit Services Center",
            "building": "Building Division",
            "planning": "Planning Division",
            "code_enforcement": "Code Enforcement Division",
            "fire": "Halvern Fire Department, Fire Prevention Bureau",
            "finance": "Finance Department, Revenue Division",
            "clerk": "Office of the City Clerk",
            "attorney": "City Attorney's Office",
            "hearing": "Administrative Hearing Officer",
            "council": "City Council",
            "publicworks": "Public Works Department, Engineering Division",
            "records": "Development Services Records Unit",
            "parks": "Parks and Recreation Department",
            "police": "Halvern Police Department",
            "housing": "Housing Division",
            "animal": "Animal Services (contract with Sennet County)",
            "arborist": "Public Works Urban Forestry Section",
        },
        pref={"unpermitted_unit_amnesty": 2.2, "rental_inspection": 1.6, "solar_auto_permit": 1.3,
              "home_business": 1.1, "tree_removal": 1.0, "contractor_registration": 1.0},
    ),
    dict(
        id="J2", name="City of Ellinsport", short="Ellinsport", kind="city", state="Marisol",
        pop=312400, style="planning_led",
        umbrella="Department of Planning and Community Development",
        address="1 Harbor Plaza, Room 200, Ellinsport, MR 94510",
        phone="(415) 774-2100", hours="Monday-Friday 8:30 a.m.-4:30 p.m. (appointments after 3:00 p.m.)",
        host="www.ellinsport.gov", email="devreview@ellinsport.gov",
        permit_system="CityView Online Permit Center",
        subreddit="r/Ellinsport", legislative_host="ellinsport.legistream.com",
        code_host="library.municodex.com/mr/ellinsport",
        news=("Ellinsport Tribune", "www.ellinsporttribune.com"),
        council="City Council", council_cycle="every Tuesday",
        fee_instrument="Fee Ordinance, Chapter 3.44, amended by resolution",
        depts={
            "lead_permits": "Development Review Section",
            "building": "Building Safety Bureau",
            "planning": "Current Planning Section",
            "code_enforcement": "Neighborhood Compliance Bureau",
            "fire": "Ellinsport Fire Department, Bureau of Fire Prevention",
            "finance": "Department of Finance, Business Tax and License Section",
            "clerk": "Office of the City Clerk",
            "attorney": "Office of the City Attorney",
            "hearing": "Office of Administrative Hearings",
            "council": "City Council",
            "publicworks": "Department of Public Works, Street Use Section",
            "records": "Records and Imaging Unit",
            "parks": "Department of Parks, Recreation and Waterfront",
            "police": "Ellinsport Police Department, Special Events Unit",
            "housing": "Housing and Community Services Bureau",
            "animal": "Ellinsport Animal Care Services",
            "arborist": "Public Works Urban Forest Division",
        },
        pref={"sidewalk_vending": 2.4, "str_registration": 1.8, "rental_inspection": 2.0,
              "special_event": 1.8, "tree_removal": 1.4, "mobile_food": 1.0},
    ),
    dict(
        id="J3", name="City of Calder Springs", short="Calder Springs", kind="city", state="Marisol",
        pop=24800, style="contracts_to_county",
        umbrella="Community Development Department",
        address="12 Spring Street, Calder Springs, MR 95431",
        phone="(707) 431-9080", hours="Tuesday and Thursday 9:00 a.m.-3:00 p.m. (counter closed Monday)",
        host="www.caldersprings.gov", email="planning@caldersprings.gov",
        permit_system="paper applications; county TrakIT for building permits",
        subreddit="r/CalderSprings", legislative_host="caldersprings.gov/agendas",
        code_host="library.municodex.com/mr/caldersprings",
        news=("Calder Springs Courier", "www.calderspringscourier.com"),
        council="City Council", council_cycle="second Monday",
        fee_instrument="Master Fee Schedule, Resolution updated when Council directs",
        depts={
            "lead_permits": "Community Development front counter",
            "building": "Sennet County Building Inspection Division (by contract)",
            "planning": "Planning Technician",
            "code_enforcement": "Code Compliance Officer (0.5 FTE)",
            "fire": "Calder Springs Fire Protection District",
            "finance": "Finance and Administrative Services",
            "clerk": "City Clerk",
            "attorney": "City Attorney (contract, Boyle & Ruiz LLP)",
            "hearing": "Planning Commission sitting as the appeals body",
            "council": "City Council",
            "publicworks": "Public Works Maintenance Division",
            "records": "City Clerk's records vault",
            "parks": "Parks and Trails Division",
            "police": "Sennet County Sheriff's Office (by contract)",
            "housing": "Community Development Department",
            "animal": "Sennet County Animal Care",
            "arborist": "contract arborist (Maddow Tree Consulting)",
        },
        pref={"str_registration": 2.6, "backyard_hens": 2.0, "tree_removal": 1.8,
              "home_business": 1.5, "special_event": 1.4, "unpermitted_unit_amnesty": 1.2},
    ),
    dict(
        id="J4", name="County of Sennet", short="Sennet County", kind="county", state="Marisol",
        pop=511000, pop_unincorporated=96400, style="county",
        umbrella="Sennet County Planning and Building Department",
        address="Hall of Records, Room 110, 550 Court Street, Ardenne, MR 94502",
        phone="(510) 891-6500", hours="Monday-Friday 8:00 a.m.-4:00 p.m. (permit center closes at 3:30)",
        host="www.sennetcounty.gov", email="permitcenter@sennetcounty.gov",
        permit_system="TrakIT (county-wide, shared with contract cities)",
        subreddit="r/SennetCounty", legislative_host="sennetcounty.legistream.com",
        code_host="library.municodex.com/mr/sennetcounty",
        news=("Sennet County Ledger", "www.sennetledger.com"),
        council="Board of Supervisors", council_cycle="second and fourth Tuesday",
        fee_instrument="County Fee Ordinance, Title 3, amended by the Board",
        depts={
            "lead_permits": "Permit Center (Hall of Records, Room 110)",
            "building": "Building Inspection Division",
            "planning": "Current Planning Division",
            "code_enforcement": "Code Compliance Unit",
            "fire": "Office of the County Fire Marshal",
            "finance": "Auditor-Controller, Revenue Division",
            "clerk": "Clerk of the Board of Supervisors",
            "attorney": "Office of County Counsel",
            "hearing": "Zoning Administrator",
            "council": "Board of Supervisors",
            "publicworks": "Department of Public Works, Road Division",
            "health": "Environmental Health Division",
            "records": "Clerk-Recorder's Office",
            "assessor": "Sennet County Assessor's Office",
            "parks": "County Parks Department",
            "police": "Sennet County Sheriff's Office",
            "housing": "Housing and Community Development Agency",
            "animal": "Sennet County Animal Care",
            "arborist": "Public Works Vegetation Management",
        },
        pref={"well_permit": 3.0, "mobile_food": 2.6, "rental_inspection": 1.2,
              "unpermitted_unit_amnesty": 1.5, "backyard_hens": 1.0, "solar_auto_permit": 1.2},
    ),
    # ----- Corvane (neighbour state; look-alike distractors only) -----
    dict(
        id="K1", name="City of Tarnbrook", short="Tarnbrook", kind="city", state="Corvane",
        pop=88900, style="permit_center", target=False,
        umbrella="Department of Development and Inspectional Services",
        address="400 Pell Avenue, Tarnbrook, CV 71204",
        phone="(208) 447-3311", hours="Monday-Friday 9:00 a.m.-4:00 p.m.",
        host="www.tarnbrook-cv.gov", email="permits@tarnbrook-cv.gov",
        permit_system="OpenGov Permitting",
        subreddit="r/Tarnbrook", legislative_host="tarnbrook-cv.legistream.com",
        code_host="library.municodex.com/cv/tarnbrook",
        news=("Tarnbrook Sentinel", "www.tarnbrooksentinel.com"),
        council="City Council", council_cycle="first Wednesday",
        fee_instrument="Consolidated Fee Schedule",
        depts={
            "lead_permits": "Permit and Licensing Center",
            "building": "Inspectional Services Division",
            "planning": "Planning and Zoning Division",
            "code_enforcement": "Neighborhood Services Division",
            "fire": "Tarnbrook Fire Department, Prevention Division",
            "finance": "Office of the Treasurer, Licensing Section",
            "clerk": "City Clerk's Office",
            "attorney": "City Solicitor",
            "hearing": "Board of Appeals",
            "council": "City Council",
            "publicworks": "Department of Public Works",
            "records": "Central Records",
            "parks": "Parks Department",
            "police": "Tarnbrook Police Department",
            "housing": "Housing Division",
            "animal": "Wexley County Animal Control",
            "arborist": "City Forester",
        },
        pref={"unpermitted_unit_amnesty": 2.0, "str_registration": 1.8, "sidewalk_vending": 1.4,
              "rental_inspection": 1.6, "solar_auto_permit": 1.2},
    ),
    dict(
        id="K2", name="County of Wexley", short="Wexley County", kind="county", state="Corvane",
        pop=143000, pop_unincorporated=61000, style="county", target=False,
        umbrella="Wexley County Development Services Agency",
        address="9 Courthouse Square, Bell Falls, CV 71130",
        phone="(208) 512-7700", hours="Monday-Thursday 7:30 a.m.-5:30 p.m.",
        host="www.wexleycounty-cv.gov", email="devservices@wexleycounty-cv.gov",
        permit_system="Tyler EnerGov",
        subreddit="r/WexleyCounty", legislative_host="wexleycounty-cv.legistream.com",
        code_host="library.municodex.com/cv/wexley",
        news=("Bell Falls Register", "www.bellfallsregister.com"),
        council="Board of County Commissioners", council_cycle="every other Thursday",
        fee_instrument="Unified Fee Resolution",
        depts={
            "lead_permits": "One-Stop Permit Counter",
            "building": "Building Division",
            "planning": "Long Range and Current Planning Division",
            "code_enforcement": "Code Enforcement Section",
            "fire": "Wexley County Fire Marshal",
            "finance": "Office of the County Auditor",
            "clerk": "Clerk to the Board",
            "attorney": "County Attorney",
            "hearing": "Hearing Examiner",
            "council": "Board of County Commissioners",
            "publicworks": "Public Works Department",
            "health": "Wexley County Health District",
            "records": "Records Management",
            "assessor": "Wexley County Assessor",
            "parks": "Parks and Open Space",
            "police": "Wexley County Sheriff",
            "housing": "Housing Programs Office",
            "animal": "Wexley County Animal Control",
            "arborist": "Public Works Vegetation Crew",
        },
        pref={"well_permit": 2.8, "mobile_food": 2.2, "tree_removal": 1.4,
              "backyard_hens": 1.2, "special_event": 1.2},
    ),
]

JUR_BY_ID = {j["id"]: j for j in JURISDICTIONS}

# How well a domain fits a kind of jurisdiction (before per-jurisdiction pref).
KIND_FIT = {
    "unpermitted_unit_amnesty": {"city": 1.4, "county": 1.0},
    "str_registration": {"city": 1.4, "county": 0.9},
    "sidewalk_vending": {"city": 1.6, "county": 0.5},
    "tree_removal": {"city": 1.4, "county": 0.9},
    "home_business": {"city": 1.3, "county": 1.0},
    "mobile_food": {"city": 0.6, "county": 2.0},
    "solar_auto_permit": {"city": 1.4, "county": 1.1},
    "rental_inspection": {"city": 1.5, "county": 0.8},
    "backyard_hens": {"city": 1.2, "county": 1.0},
    "special_event": {"city": 1.5, "county": 0.8},
    "well_permit": {"city": 0.4, "county": 2.4},
    "contractor_registration": {"city": 1.2, "county": 0.9},
}

# Statutes whose applicability text pushes most jurisdictions to implement.
BROAD = {"rental_inspection", "solar_auto_permit"}

# Per-jurisdiction load: 6-8 statutes each, summing to 26 target processes.
TARGET_LOAD = {"J1": 7, "J2": 7, "J3": 6, "J4": 6}
NEIGHBOR_LOAD = {"K1": 6, "K2": 6}


def _fit(jur: dict, domain: str) -> float:
    base = KIND_FIT[domain][jur["kind"]]
    return base * jur.get("pref", {}).get(domain, 0.8)


def _assign(seed: int, jur_ids: list[str], load: dict[str, int], counts: dict[str, int]) -> list[tuple[str, str]]:
    """Assign (jur, domain) pairs so each jurisdiction hits its load and each
    domain gets `counts[domain]` implementers. Greedy by fit x remaining slots."""
    rng = sub_rng(seed, "assign", ",".join(jur_ids))
    remaining = dict(load)
    pairs: list[tuple[str, str]] = []
    # Scarcest domains first (highest implementer count), so they can be satisfied.
    order = sorted(counts, key=lambda d: (-counts[d], d))
    for domain in order:
        chosen: list[str] = []
        for _ in range(counts[domain]):
            cands = [j for j in jur_ids if remaining[j] > 0 and j not in chosen]
            if not cands:
                break
            pick_id = weighted(rng, [(j, _fit(JUR_BY_ID[j], domain) * (remaining[j] + 0.4)) for j in cands])
            chosen.append(pick_id)
            remaining[pick_id] -= 1
        for j in chosen:
            pairs.append((j, domain))
    return pairs


def _implementer_counts(seed: int) -> dict[str, int]:
    """2-4 implementers per Marisol statute, 26 total across 12 statutes."""
    counts = {d: 2 for d in DOMAIN_ORDER}
    rng = sub_rng(seed, "impl_counts")
    extra = 2  # 24 + 2 = 26
    pool = sorted(BROAD) + [d for d in DOMAIN_ORDER if d not in BROAD]
    i = 0
    while extra > 0 and i < len(pool):
        d = pool[i]
        bump = 1 if (d in BROAD or chance(rng, 0.25)) else 0
        if bump:
            counts[d] += 1
            extra -= 1
        i += 1
    return counts


def _why_implements(rng, jur: dict, domain: str, retrofit: bool) -> str:
    dom = DOMAINS[domain]
    bits = []
    if retrofit:
        bits.append(
            "the %s already ran a local %s program before %s was enacted; the statute was "
            "absorbed into the existing machinery (fee re-set, statute cite added, new checklist)"
            % (jur.get("umbrella", "department"), dom["title"].lower(), dom["bill"])
        )
    if domain in BROAD:
        bits.append("the statute's applicability threshold reaches a jurisdiction of %s" % f"{jur['pop']:,}")
    if jur.get("pref", {}).get(domain, 0) >= 1.8:
        bits.append("local salience: %s" % {
            "sidewalk_vending": "a large street-vending economy on two commercial corridors",
            "str_registration": "a visitor economy and a decade of short-term-rental complaints",
            "rental_inspection": "an older rental stock and an active tenant coalition",
            "well_permit": "unincorporated parcels on private groundwater",
            "mobile_food": "the county is the local enforcement agency for food facilities",
            "unpermitted_unit_amnesty": "an estimated 900 unpermitted units identified in the housing element",
            "backyard_hens": "an urban-agriculture council priority",
            "special_event": "a downtown events calendar and repeated street closures",
            "tree_removal": "a heritage-oak canopy and contested removals",
            "home_business": "small-business outreach after the statute's ministerial mandate",
        }.get(domain, "a council priority"))
    if not bits:
        bits.append("routine adoption: the %s brought the existing practice into conformance with %s"
                    % (jur.get("umbrella", "department"), dom["cite"]))
    return "; ".join(bits)


def _why_not(rng, jur: dict, domain: str) -> str:
    dom = DOMAINS[domain]
    if domain == "well_permit" and jur["kind"] == "city":
        return "wells are permitted by the county under %s; the city has delegated" % dom["cite"]
    if domain == "mobile_food":
        return "mobile food facilities are permitted by the county health department as the local enforcement agency"
    if domain == "sidewalk_vending" and jur["pop"] < 40000:
        return "no vending permit program; the statute forbids a prohibition but does not require a permit"
    if domain == "str_registration" and jur["pop"] > 200000:
        return "short-term rentals are prohibited outside two overlay districts, so the registration article does not apply"
    if domain == "rental_inspection":
        return "fewer than 5,000 rental units, so the proactive program is optional and the jurisdiction relies on complaints"
    return "optional under %s; not adopted (no council sponsor, no dedicated staff)" % dom["cite"]


def build_world(world_id: str, seed: int, knob_overrides: dict | None = None) -> dict:
    knobs = dict(DEFAULT_KNOBS)
    knobs.update(knob_overrides or {})
    only_j, only_d = knobs.get("only_jurisdictions"), knobs.get("only_domains")
    jurisdictions = [j for j in JURISDICTIONS if not only_j or j["id"] in only_j]
    domain_order = [d for d in DOMAIN_ORDER if not only_d or d in only_d]
    marisol_ids = [j["id"] for j in jurisdictions if j["state"] == "Marisol"]
    if only_j or only_d:
        # generic sizing for a subset world: 2 implementers per statute (or 1 if
        # only one Marisol jurisdiction), spread as evenly as the loads allow.
        per = min(2, len(marisol_ids))
        counts = {d: per for d in domain_order}
        total = sum(counts.values())
        load = {j: total // len(marisol_ids) for j in marisol_ids}
        for j in marisol_ids[: total % len(marisol_ids)]:
            load[j] += 1
    else:
        counts = _implementer_counts(seed)
        load = TARGET_LOAD
    pairs = _assign(seed, marisol_ids, load, counts)

    neighbour_pairs: list[tuple[str, str]] = []
    if knobs["neighbor_state"] and any(j["state"] != "Marisol" for j in jurisdictions):
        # Corvane look-alikes: prefer domains Marisol jurisdictions also implement.
        implemented = sorted({d for _, d in pairs})
        neigh_load = {j["id"]: NEIGHBOR_LOAD[j["id"]] for j in jurisdictions
                      if j["state"] != "Marisol" and j["id"] in NEIGHBOR_LOAD}
        ncounts = {}
        rng = sub_rng(seed, "corvane_domains")
        pool = implemented[:]
        rng.shuffle(pool)
        for d in pool[: max(1, min(len(pool), sum(neigh_load.values())))]:
            ncounts[d] = 1
        # pad to the exact load
        total = sum(neigh_load.values())
        for d in pool:
            if sum(ncounts.values()) >= total:
                break
            if ncounts.get(d, 0) < 2:
                ncounts[d] = ncounts.get(d, 0) + 1
        neighbour_pairs = _assign(seed, list(neigh_load), neigh_load, ncounts) if neigh_load else []

    impls, non_impls = [], []
    for jid, domain in sorted(pairs + neighbour_pairs):
        jur = JUR_BY_ID[jid]
        rng = sub_rng(seed, "impl", jid, domain)
        retrofit = chance(rng, knobs["p_retrofit"])
        sid = stat_id_for(domain)
        if jur["state"] != "Marisol":          # Corvane statutes are C01..C12
            sid = "C" + sid[1:]
        impls.append({
            "jur": jid, "stat_id": sid, "domain": domain,
            "target": jur["state"] == "Marisol",
            "retrofit": retrofit,
            "why": _why_implements(rng, jur, domain, retrofit),
        })
    for jid in marisol_ids:
        have = {i["domain"] for i in impls if i["jur"] == jid}
        for domain in domain_order:
            if domain not in have:
                non_impls.append({"jur": jid, "stat_id": stat_id_for(domain), "domain": domain,
                                  "why": _why_not(sub_rng(seed, "noimpl", jid, domain), JUR_BY_ID[jid], domain)})

    statutes = [{
        "stat_id": stat_id_for(d), "domain": d, "state": "Marisol",
        "cite": DOMAINS[d]["cite"], "title": DOMAINS[d]["statute_title"],
        "shape": DOMAINS[d]["shape"], "bill": DOMAINS[d]["bill"],
        "applicability": DOMAINS[d]["applicability"],
        "n_implementers": sum(1 for i in impls if i["domain"] == d and i["target"]),
        "implementers": [i["jur"] for i in impls if i["domain"] == d and i["target"]],
        "lookalike_implementers": [i["jur"] for i in impls if i["domain"] == d and not i["target"]],
    } for d in domain_order]

    return {
        "world": world_id,
        "seed": seed,
        "as_of": knobs["as_of"],
        "generator": "benchmark/synth/generator (no LLM calls; stdlib only)",
        "generator_version": GENERATOR_VERSION,
        "visit_accounting_version": knobs["visit_accounting_version"],
        "design_doc": "benchmark/synth/DESIGN.md",
        "knobs": knobs,
        "states": [
            {"id": "MR", "name": "State of Marisol", "role": "primary", "pop": 8420000,
             "legislature": "Marisol Legislature", "reporter": "Marisol Statutes",
             "committee": "Assembly Committee on Local Government",
             "agencies": sorted({DOMAINS[d]["state_agency"] for d in domain_order})},
            {"id": "CV", "name": "State of Corvane", "role": "neighbor_lookalike", "pop": 2110000,
             "legislature": "Corvane General Assembly", "reporter": "Corvane Revised Statutes",
             "committee": "Senate Committee on Government Operations",
             "agencies": ["Corvane Department of Community Affairs", "Corvane Health Division",
                          "Corvane Water Resources Department"]},
        ],
        "domains": domain_order,
        "jurisdictions": jurisdictions,
        "statutes": statutes,
        "implementations": impls,
        "non_implementations": non_impls,
        "counts": {
            "jurisdictions": len(jurisdictions),
            "target_processes": sum(1 for i in impls if i["target"]),
            "lookalike_processes": sum(1 for i in impls if not i["target"]),
            "statutes": len(statutes),
        },
    }


# ------------------------------------------------------------------ helpers


def actor_name(jur: dict, role: str, domain: str | None = None) -> str:
    """Jurisdiction-specific name for a canonical actor role."""
    if role == "applicant":
        return {"rental_inspection": "Property owner", "contractor_registration": "Contractor",
                "sidewalk_vending": "Vendor", "mobile_food": "Operator",
                "special_event": "Event organizer"}.get(domain or "", "Applicant")
    if role == "third_party":
        return {"unpermitted_unit_amnesty": "Licensed contractor (third-party inspector)",
                "tree_removal": "Certified arborist retained by the applicant",
                "well_permit": "Licensed C-57 well drilling contractor",
                "solar_auto_permit": "Licensed electrical contractor / solar installer",
                "mobile_food": "Commissary operator"}.get(domain or "", "Third-party professional")
    if role == "tenant":
        return "Tenant"
    if role == "state_agency":
        return DOMAINS[domain]["state_agency"] if domain else "State agency"
    depts = jur["depts"]
    if role in depts:
        return depts[role]
    if role == "health":  # cities without their own health department
        return "Sennet County Environmental Health Division (by agreement)" if jur["state"] == "Marisol" \
            else "Wexley County Health District (by agreement)"
    if role == "assessor":
        return "Sennet County Assessor's Office" if jur["state"] == "Marisol" else "Wexley County Assessor"
    return depts.get("lead_permits", "Staff")


def render_context(world: dict, jur: dict, statutes: dict, local_rules: dict, processes: dict) -> dict:
    """Public-facing facts a Wave-2 renderer may use (briefs/RENDER_BRIEF.md)."""
    progs = []
    for mid, proc in sorted(processes.items()):
        if proc["jur_id"] != jur["id"]:
            continue
        lr = local_rules[mid]
        progs.append({
            "model_id": mid, "stat_id": proc["stat_id"], "program_name": proc["program_name"],
            "statute_cite": statutes[proc["stat_id"]]["cite"], "bill": statutes[proc["stat_id"]]["bill"],
            "local_instrument": lr["cite"], "adopted": lr["adopted"],
            "terminal_artifact": proc["terminal_artifact"],
            "lead_department": proc["lead_department"],
            "form_name": proc["form_name"], "checklist_name": proc["checklist_name"],
        })
    return {
        "world": world["world"], "jur": jur["id"], "name": jur["name"], "state": "State of " + jur["state"],
        "kind": jur["kind"], "population": jur["pop"], "umbrella_department": jur["umbrella"],
        "departments": jur["depts"], "address": jur["address"], "phone": jur["phone"],
        "counter_hours": jur["hours"], "website": "https://%s/" % jur["host"], "email": jur["email"],
        "permit_system": jur["permit_system"], "subreddit": jur["subreddit"],
        "legislative_host": jur["legislative_host"], "code_host": jur["code_host"],
        "news_outlet": {"name": jur["news"][0], "host": jur["news"][1]},
        "legislative_body": jur["council"], "meeting_cycle": jur["council_cycle"],
        "fee_instrument": jur["fee_instrument"], "programs": progs,
    }
