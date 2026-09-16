"""The 12 statute domains (DESIGN.md `statute_truth.domain` enum) as data.

Everything domain-specific lives here so the logic modules stay generic and a
new domain is one dict (see generator/README.md "Adding a domain").

Per-domain fields
-----------------
shape        "prescriptive" (7-8 mandated elements, statute nearly writes the
             process, DROS-like) | "mid" (6-7, some choices) | "minimal"
             (5 listed, 3 mandated, AB 2533-like).
elements     tuples (element_id, kind, name, actor_role, optional,
             shot_clock_days, must_precede) -- kinds from the DESIGN enum.
             `shot_clock_days` on an applicant element is a filing deadline.
choices      tuples (choice_id, kind, what, constraint); `kind` tells
             local_rules.py how to invent a plausible value.
programs     local program-name variants -> naming drift between cities.
terminal     terminal-artifact variants.
lead_roles   department roles (see world.DEPT_ROLES) that plausibly administer.
backoffice   tags of back-office activities that plausibly attach (see
             processes.BACKOFFICE).
local_names  element_id -> alternative activity names cities actually use.
"""
from __future__ import annotations

# Order fixes the statute ids: S01..S12.
DOMAINS: dict[str, dict] = {
    # ------------------------------------------------------------------ S01
    "unpermitted_unit_amnesty": dict(
        title="Legalization of Unpermitted Dwelling Units",
        statute_title="Unpermitted Dwelling Unit Legalization Act of 2024",
        cite="Marisol Gov. Code § 41210",
        bill="AB 1188 (2024)",
        shape="minimal",
        pace=1.0,
        state_agency="Marisol Department of Housing and Community Development",
        applicability="Adoption of a local legalization program is permissive, but an "
        "agency that receives an application for a dwelling unit built before "
        "January 1, 2020 shall follow this chapter.",
        purpose_spec="Recite that an estimated 92,000 dwelling units in Marisol were built "
        "or converted without permits; that owners do not come forward because a permit "
        "application invites code enforcement and an investigation penalty; and that the "
        "state's interest is in bringing these units up to minimum health and safety "
        "standards rather than losing them from the housing stock.",
        defs=[
            ("unpermitted dwelling unit", "a dwelling unit or junior dwelling unit created without a required building permit before January 1, 2020"),
            ("substandard condition", "the conditions listed in Health and Safety Code Section 61120.3"),
            ("legalizing agency", "the city, county, or city and county with building permit jurisdiction over the unit"),
        ],
        elements=[
            ("E1", "application", "Application to legalize an unpermitted dwelling unit, with evidence of the date of construction", "applicant", False, None, ("E2",)),
            ("E2", "inspection", "Inspection of the unit against the substandard-conditions list", "agency", False, None, ("E4",)),
            ("E3", "third_party_option", "Confidential inspection by a licensed contractor, before or in lieu of the agency inspection", "third_party", True, None, ("E2",)),
            ("E4", "correction", "Permits to correct documented substandard conditions, without penalty or investigation fee", "applicant", False, None, ("E5",)),
            ("E5", "decision", "Issuance of a certificate recognizing the unit as legal", "agency", False, None, ()),
            ("E6", "timeline", "Delay of code enforcement for up to five years for conditions that are not an immediate life-safety hazard", "agency", True, None, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the application fee", "shall not exceed the reasonable cost of providing the service"),
            ("C2", "department", "which department administers the program", ""),
            ("C3", "standard", "what evidence proves the unit predates January 1, 2020", "the agency shall accept more than one form of evidence"),
            ("C4", "portal", "how an application is submitted", ""),
            ("C5", "threshold", "whether units on parcels zoned for two or more units are eligible", "an agency shall not exclude a unit solely because the parcel contains a duplex"),
        ],
        programs=["Unit Legalization Program", "Amnesty Permit Program", "Safe Housing Certificate Program", "Residential Legalization Pathway"],
        terminal=["Certificate of Compliance", "Housing Certificate of Compliance", "Legalization Permit", "Revocable Certificate of Occupancy"],
        lead_roles=["building", "lead_permits", "planning"],
        fee_range=(180, 780),
        fee_label="unit legalization permit",
        fee_basis="flat fee equal to three inspector-hours at the adopted hourly rate",
        app_form="Unpermitted Dwelling Unit Legalization Application",
        checklist="Substandard Housing Inspection Checklist (§ 61120.3)",
        inspection_name="housing inspection against the § 61120.3 substandard-conditions list",
        backoffice=["gis_parcel", "intake_screening", "ce_referral", "records_archive", "supervisor_denial", "assessor_referral", "status_update", "inspection_batch", "fee_recon"],
        extra_actors=["code_enforcement", "assessor", "third_party"],
        user_terms=["amnesty", "legalizing my in-law unit", "unpermitted garage conversion", "granny flat"],
        news_adopt="council adopts the amnesty ordinance; director says the city knows of roughly 900 unpermitted units",
        news_backlog="two inspectors for 140 applications; owners waiting months for a first inspection",
        local_names={
            "E1": ["Submit legalization application", "File amnesty application packet", "Apply for a Safe Housing Certificate"],
            "E2": ["Inspect the unit against the substandard-conditions list", "Conduct the housing inspection (city inspector)", "Perform the initial code inspection"],
            "E5": ["Issue the Certificate of Compliance", "Issue the Housing Certificate of Compliance", "Issue the legalization permit"],
        },
    ),
    # ------------------------------------------------------------------ S02
    "str_registration": dict(
        title="Short-Term Residential Rental Registration",
        statute_title="Short-Term Residential Rental Registration Act",
        cite="Marisol Gov. Code § 38560",
        bill="SB 744 (2023)",
        shape="prescriptive",
        pace=0.7,
        state_agency="Marisol Department of Consumer Affairs",
        applicability="A city or county that allows short-term residential rentals shall "
        "operate a registration program conforming to this article; a jurisdiction that "
        "prohibits short-term rentals is exempt.",
        purpose_spec="Recite the loss of long-term rental stock, uncollected transient "
        "occupancy tax, and the inability of neighbors to identify a responsible party; "
        "declare a statewide interest in a uniform registration record with a local "
        "contact available 24 hours a day.",
        defs=[
            ("short-term rental", "a residential dwelling unit rented for fewer than 30 consecutive days"),
            ("hosted rental", "a short-term rental in which the permanent resident remains on site"),
            ("hosting platform", "a person who provides a means through which an owner may offer a short-term rental"),
        ],
        elements=[
            ("E1", "application", "Registration application stating the unit, the owner, and a 24-hour local contact", "applicant", False, None, ("E4",)),
            ("E2", "fee", "Annual registration fee", "applicant", False, None, ("E4",)),
            ("E3", "inspection", "Life-safety self-certification, or an agency inspection where the agency requires one", "agency", True, None, ("E4",)),
            ("E4", "decision", "Issue or deny the registration certificate and assign a registration number", "agency", False, 45, ("E7",)),
            ("E5", "notice", "Written notice of the reasons for a denial and of the right to appeal", "agency", False, 10, ("E6",)),
            ("E6", "appeal", "Appeal to a hearing officer who did not participate in the decision", "applicant", False, 20, ()),
            ("E7", "record", "Public registry of registered units and registration numbers, updated at least quarterly", "agency", False, None, ()),
            ("E8", "timeline", "Annual renewal with a 30-day grace period before the registration lapses", "applicant", False, 30, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the annual registration fee", "shall not exceed the reasonable cost of administering the program"),
            ("C2", "department", "which department administers registration", ""),
            ("C3", "cap", "whether to cap the number of nights or of registrations", "a cap shall apply uniformly within a zoning district"),
            ("C4", "appeal_body", "who hears appeals", "the hearing officer shall not have participated in the decision"),
            ("C5", "standard", "whether an agency inspection is required or self-certification suffices", ""),
            ("C6", "portal", "the registration channel", ""),
        ],
        programs=["Short-Term Rental Registration", "Vacation Rental Permit Program", "Transient Lodging Registration", "Home Sharing Permit"],
        terminal=["Short-Term Rental Registration Certificate", "Vacation Rental Permit", "Home Sharing Permit"],
        lead_roles=["finance", "planning", "lead_permits"],
        fee_range=(120, 1050),
        fee_label="annual short-term rental registration",
        fee_basis="annual cost-recovery fee per registered unit",
        app_form="Short-Term Rental Registration Application",
        checklist="Short-Term Rental Life-Safety Self-Certification",
        inspection_name="life-safety inspection of the rental unit",
        backoffice=["intake_screening", "tax_cert_check", "status_update", "notice_mailing", "appeal_docket", "records_archive", "fee_recon", "complaint_crossref", "qa_audit"],
        extra_actors=["clerk", "hearing", "fire"],
        user_terms=["STR permit", "airbnb registration", "TOT certificate", "rental number"],
        news_adopt="council caps registrations at 250 after a two-year fight; hosts pack the chamber",
        news_backlog="renewal season swamps a one-person office; 300 applications pending",
        local_names={
            "E1": ["Submit STR registration application", "Apply for a Vacation Rental Permit", "Register a home-sharing unit"],
            "E4": ["Issue the registration certificate", "Approve the permit and assign an STR number", "Grant the home sharing permit"],
        },
    ),
    # ------------------------------------------------------------------ S03
    "sidewalk_vending": dict(
        title="Sidewalk Vending",
        statute_title="Safe Sidewalk Vending Act",
        cite="Marisol Gov. Code § 51038",
        bill="SB 402 (2022)",
        shape="prescriptive",
        pace=0.65,
        state_agency="Marisol Department of Consumer Affairs",
        applicability="A local authority shall not prohibit sidewalk vending outright; a "
        "local authority that requires a vending permit shall conform its program to this "
        "section.",
        purpose_spec="Recite that sidewalk vending is an entrepreneurship pathway for "
        "low-income and immigrant residents, that criminal penalties and unaffordable "
        "fines push vendors into the informal economy, and that local regulation must be "
        "limited to objective health, safety, and welfare concerns.",
        defs=[
            ("sidewalk vendor", "a person who sells food or merchandise from a pushcart, stand, or their person in a public right-of-way"),
            ("roaming sidewalk vendor", "a sidewalk vendor who moves from place to place and stops only to complete a transaction"),
            ("ability-to-pay determination", "a determination of a vendor's household income relative to the state median"),
        ],
        elements=[
            ("E1", "checklist_publication", "Publish the vending rules, the permit requirements, and the fine schedule in the two most commonly spoken languages in the jurisdiction", "agency", False, None, ("E2",)),
            ("E2", "application", "Sidewalk vending permit application", "applicant", False, None, ("E5",)),
            ("E3", "fee", "Permit fee limited to the cost of the permit program", "applicant", False, None, ("E5",)),
            ("E4", "referral", "Referral to the county health department for a food vending cart", "agency", False, None, ("E5",)),
            ("E5", "decision", "Grant or deny the vending permit", "agency", False, 30, ()),
            ("E6", "notice", "Notice of violation stating the administrative fine and the right to request an ability-to-pay determination", "agency", False, None, ("E7",)),
            ("E7", "fee_waiver", "Reduction of administrative fines by 75 percent for a vendor who shows inability to pay", "applicant", False, None, ()),
            ("E8", "appeal", "Administrative hearing on a fine or a permit denial", "applicant", False, 21, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the vending permit fee", "shall not exceed the cost of the permit program"),
            ("C2", "department", "which department issues vending permits", ""),
            ("C3", "hours", "time, place, and manner limits on vending", "limits shall be directly related to objective health, safety, or welfare concerns"),
            ("C4", "appeal_body", "who hears fine and denial appeals", ""),
            ("C5", "languages", "the two languages in which materials are published", "shall be the two most commonly spoken languages in the jurisdiction"),
        ],
        programs=["Sidewalk Vending Permit", "Mobile Vendor Permit Program", "Street Vending Program", "Public Right-of-Way Vending Permit"],
        terminal=["Sidewalk Vending Permit", "Street Vendor Permit and Badge", "Mobile Vendor Permit"],
        lead_roles=["finance", "lead_permits", "publicworks"],
        fee_range=(45, 320),
        fee_label="sidewalk vending permit",
        fee_basis="annual permit fee limited to program cost",
        app_form="Sidewalk Vending Permit Application",
        checklist="Sidewalk Vending Rules and Fine Schedule (bilingual handout)",
        inspection_name="cart and site compliance check",
        backoffice=["intake_screening", "translation", "health_referral", "status_update", "notice_mailing", "appeal_docket", "records_archive", "ce_referral", "fee_recon"],
        extra_actors=["health", "code_enforcement", "hearing"],
        user_terms=["vending permit", "street cart", "fruit cart", "tamale cart"],
        news_adopt="city rewrites its vending ban after the state act; fine drops from $1,000 to $100",
        news_backlog="vendors say permits take months and the health clearance is the bottleneck",
        local_names={
            "E2": ["Apply for a sidewalk vending permit", "Submit mobile vendor application", "File street vending application"],
            "E5": ["Issue the vending permit", "Approve the vendor permit and issue the badge", "Grant the mobile vendor permit"],
        },
    ),
    # ------------------------------------------------------------------ S04
    "tree_removal": dict(
        title="Protected Tree Removal",
        statute_title="Protected Tree Preservation and Permitting Act",
        cite="Marisol Pub. Res. Code § 4622",
        bill="AB 2015 (2021)",
        shape="mid",
        pace=0.8,
        state_agency="Marisol Department of Forestry and Fire Protection",
        applicability="A city or county that regulates the removal of protected trees on "
        "private property shall provide at least the procedure in this section.",
        purpose_spec="Recite urban canopy loss, heat-island effects, and inconsistent "
        "local tree ordinances; declare a minimum procedure of notice, an arborist "
        "record, a decision within a fixed period, and an appeal, while leaving the "
        "protected-species list to local choice.",
        defs=[
            ("protected tree", "a tree of a species or size designated for protection by local ordinance"),
            ("certified arborist", "a person holding a current certification from a recognized arboricultural credentialing body"),
            ("diameter at breast height", "the trunk diameter measured 54 inches above natural grade"),
        ],
        elements=[
            ("E1", "application", "Application for a permit to remove a protected tree, with a site plan", "applicant", False, None, ("E3",)),
            ("E2", "third_party_option", "Report by a certified arborist retained by the applicant", "third_party", True, None, ("E5",)),
            ("E3", "notice", "Notice posted on the site and mailed to owners within 100 feet at least 10 days before a decision", "agency", False, 10, ("E5",)),
            ("E4", "inspection", "Site inspection to verify species, size, and condition", "agency", False, None, ("E5",)),
            ("E5", "decision", "Grant, conditionally grant, or deny the removal permit", "agency", False, 30, ()),
            ("E6", "appeal", "Appeal of the decision to the body designated by the local authority", "applicant", False, 14, ()),
            ("E7", "correction", "Replacement planting, or payment of an in-lieu fee into a tree fund", "applicant", False, None, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the removal permit fee", "shall not exceed the reasonable cost of review and inspection"),
            ("C2", "department", "which department issues tree permits", ""),
            ("C3", "threshold", "the trunk diameter at which a tree becomes protected", "the threshold shall not exceed 24 inches diameter at breast height"),
            ("C4", "ratio", "the replacement-planting ratio or in-lieu fee", ""),
            ("C5", "appeal_body", "the appeal body", ""),
            ("C6", "radius", "the mailed-notice radius", "shall be not less than 100 feet"),
        ],
        programs=["Tree Removal Permit", "Protected Tree Permit Program", "Heritage Tree Permit", "Urban Forestry Permit"],
        terminal=["Tree Removal Permit", "Heritage Tree Removal Permit with replanting conditions"],
        lead_roles=["publicworks", "planning", "parks"],
        fee_range=(60, 540),
        fee_label="protected tree removal permit",
        fee_basis="per-application fee plus per-tree inspection charge",
        app_form="Protected Tree Removal Permit Application",
        checklist="Arborist Report Requirements and Replacement Planting Standards",
        inspection_name="site inspection of the tree by the city arborist",
        backoffice=["intake_screening", "gis_parcel", "notice_mailing", "posting", "appeal_docket", "records_archive", "second_review", "status_update", "inspection_batch"],
        extra_actors=["arborist", "planning", "hearing", "third_party"],
        user_terms=["oak removal permit", "heritage tree", "arborist report", "neighbor complained about my tree"],
        news_adopt="new ordinance protects oaks over 12 inches; developers object to the replanting ratio",
        news_backlog="one contract arborist covers the whole city; permits average nine weeks",
        local_names={
            "E1": ["Submit tree removal permit application", "Apply for a Heritage Tree Permit", "File protected tree application"],
            "E4": ["Inspect the tree on site (city arborist)", "Verify species and size in the field", "Visit the site (urban forester)"],
        },
    ),
    # ------------------------------------------------------------------ S05
    "home_business": dict(
        title="Home Occupation Permits",
        statute_title="Home-Based Business Fairness Act",
        cite="Marisol Gov. Code § 38701",
        bill="AB 993 (2023)",
        shape="minimal",
        pace=0.45,
        state_agency="Marisol Governor's Office of Business and Economic Development",
        applicability="A city or county shall process an application for a home occupation "
        "that meets the objective standards adopted under this section ministerially and "
        "without discretionary review or a public hearing.",
        purpose_spec="Recite the growth of home-based work, the cost of discretionary use "
        "permits for micro-businesses, and the requirement that local standards be "
        "objective, published, and applied ministerially.",
        defs=[
            ("home occupation", "a business conducted by a resident within a dwelling unit that is incidental to the residential use"),
            ("objective standard", "a standard that involves no personal or subjective judgment by a public official"),
        ],
        elements=[
            ("E1", "application", "Home occupation registration application describing the activity", "applicant", False, None, ("E2",)),
            ("E2", "decision", "Ministerial approval or denial without a hearing", "agency", False, 15, ()),
            ("E3", "record", "Record of registered home occupations available on request", "agency", False, None, ()),
            ("E4", "inspection", "Inspection where the activity involves on-site customers or hazardous materials", "agency", True, None, ("E2",)),
            ("E5", "notice", "Notice to the applicant of any objective standard not met, with one opportunity to amend", "agency", True, None, ("E2",)),
        ],
        choices=[
            ("C1", "fee_amount", "the registration fee", "shall not exceed the reasonable cost of processing"),
            ("C2", "department", "which department registers home occupations", ""),
            ("C3", "standard", "the objective standards (employees, customer trips, signage, storage)", "standards shall be objective and published"),
            ("C4", "portal", "the registration channel", ""),
            ("C5", "renewal", "the renewal period", ""),
        ],
        programs=["Home Occupation Permit", "Home-Based Business Registration", "Cottage Business Permit", "Home Business Clearance"],
        terminal=["Home Occupation Permit", "Home-Based Business Registration Certificate"],
        lead_roles=["planning", "finance", "lead_permits"],
        fee_range=(25, 210),
        fee_label="home occupation registration",
        fee_basis="flat processing fee, often bundled with the business license",
        app_form="Home Occupation Registration Application",
        checklist="Home Occupation Objective Standards Handout",
        inspection_name="home occupation compliance inspection",
        backoffice=["intake_screening", "zoning_check", "business_license_link", "status_update", "records_archive", "fee_recon", "notice_mailing"],
        extra_actors=["planning", "finance"],
        user_terms=["home business license", "home occupation permit", "working out of my garage"],
        news_adopt="city drops the use permit for home businesses; 400 registrations in year one",
        news_backlog="applicants report the clearance sits with zoning for weeks despite a 15-day clock",
        local_names={
            "E1": ["Submit home occupation application", "Register a home-based business", "Apply for cottage business permit"],
            "E2": ["Clear the application through zoning", "Issue the home occupation permit", "Approve the registration ministerially"],
        },
    ),
    # ------------------------------------------------------------------ S06
    "mobile_food": dict(
        title="Mobile Food Facility Permits",
        statute_title="Mobile Food Facility Uniform Permitting Act",
        cite="Marisol Health & Safety Code § 113790",
        bill="AB 1276 (2020)",
        shape="prescriptive",
        pace=0.95,
        state_agency="Marisol Department of Public Health",
        applicability="Each local enforcement agency shall administer this chapter for "
        "mobile food facilities operating within its jurisdiction.",
        purpose_spec="Recite foodborne-illness risk in mobile units, the burden on "
        "operators of inconsistent county requirements, and the mandate that each local "
        "enforcement agency publish a standard plan-review checklist and issue a decal.",
        defs=[
            ("mobile food facility", "any vehicle, cart, or trailer used to sell or dispense food"),
            ("commissary", "an approved food facility used by a mobile food facility for supplies, cleaning, or servicing"),
            ("local enforcement agency", "the county health department or a city department delegated enforcement authority"),
        ],
        elements=[
            ("E1", "checklist_publication", "Publish the standard plan-review checklist for mobile food facilities", "agency", False, None, ("E2",)),
            ("E2", "application", "Application for a mobile food facility health permit with plans and a commissary agreement", "applicant", False, None, ("E4",)),
            ("E3", "fee", "Plan review fee and annual health permit fee", "applicant", False, None, ("E4",)),
            ("E4", "inspection", "Pre-operational inspection of the unit and verification of the commissary", "agency", False, None, ("E6",)),
            ("E5", "referral", "Referral to the fire authority for units with cooking appliances or propane", "agency", False, None, ("E6",)),
            ("E6", "decision", "Issue the health permit and the permit decal", "agency", False, 30, ("E7",)),
            ("E7", "record", "Maintain inspection reports available to the public", "agency", False, None, ()),
            ("E8", "appeal", "Hearing before the local health officer on a permit suspension or denial", "applicant", False, 15, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the plan review and annual permit fees", "shall be set to recover the cost of the program"),
            ("C2", "department", "which agency administers mobile food permits", ""),
            ("C3", "standard", "how the commissary agreement is verified", ""),
            ("C4", "frequency", "the number of routine inspections per year", "not fewer than one"),
            ("C5", "appeal_body", "who hears suspension appeals", ""),
            ("C6", "portal", "the application channel", ""),
        ],
        programs=["Mobile Food Facility Permit", "Food Truck Health Permit", "Mobile Food Vendor Program", "Mobile Unit Plan Check"],
        terminal=["Mobile Food Facility Health Permit and decal", "Food Truck Operating Permit"],
        lead_roles=["health", "fire", "lead_permits"],
        fee_range=(240, 1450),
        fee_label="mobile food facility plan review and annual permit",
        fee_basis="plan review at an hourly rate plus a risk-tiered annual permit fee",
        app_form="Mobile Food Facility Plan Review Application",
        checklist="Mobile Food Facility Plan Review Checklist",
        inspection_name="pre-operational inspection of the unit and commissary",
        backoffice=["intake_screening", "plan_check_queue", "fire_referral", "second_review", "decal_issue", "records_archive", "status_update", "fee_recon", "inspection_batch"],
        extra_actors=["health", "fire", "third_party"],
        user_terms=["food truck permit", "plan check", "commissary letter", "health permit decal"],
        news_adopt="county publishes a single checklist after operators complain of moving targets",
        news_backlog="plan check for food trucks runs six weeks; operators pay rent on idle trucks",
        local_names={
            "E2": ["Submit mobile unit plan review application", "Apply for food truck health permit", "File mobile food facility application"],
            "E4": ["Inspect the unit before operation", "Verify the unit and the commissary", "Inspect the truck at the yard"],
        },
    ),
    # ------------------------------------------------------------------ S07
    "solar_auto_permit": dict(
        title="Automated Residential Solar Permitting",
        statute_title="Residential Solar Permit Automation Act",
        cite="Marisol Gov. Code § 62910",
        bill="SB 130 (2023)",
        shape="prescriptive",
        pace=0.22,
        state_agency="Marisol Energy Commission",
        applicability="A city or county with a population over 5,000 shall implement "
        "automated permitting for small residential rooftop solar energy systems.",
        purpose_spec="Recite soft costs in residential solar, the availability of an "
        "automated compliance-check tool, and the mandate of same-business-day issuance "
        "for a complete and compliant application, with a published standard plan set "
        "and a capped fee.",
        defs=[
            ("small residential rooftop solar energy system", "a system of no more than 38.4 kilowatts alternating current on a single-family or duplex roof"),
            ("automated permitting platform", "software that checks an application against the published standard plan set and issues the permit"),
        ],
        elements=[
            ("E1", "checklist_publication", "Publish the standard plan set, the checklist, and the permit fee on the agency's website", "agency", False, None, ("E2",)),
            ("E2", "application", "Online application through the automated review platform", "applicant", False, None, ("E3",)),
            ("E3", "decision", "Issue the permit on the same business day for a complete and compliant application", "agency", False, 1, ("E5",)),
            ("E4", "fee", "Permit fee capped at $450 for systems of 38.4 kilowatts or less", "applicant", False, None, ("E3",)),
            ("E5", "inspection", "A single inspection, scheduled for the next business day where practicable", "agency", False, 5, ()),
            ("E6", "record", "Annual report to the state of the number of automated permits issued", "agency", False, None, ()),
            ("E7", "third_party_option", "Acceptance of a licensed electrical contractor's certification in lieu of a second inspection", "third_party", True, None, ("E5",)),
        ],
        choices=[
            ("C1", "fee_amount", "the permit fee", "shall not exceed $450 for a qualifying system"),
            ("C2", "department", "which department runs solar permitting", ""),
            ("C3", "portal", "which automated platform is used", ""),
            ("C4", "frequency", "the inspection scheduling window", "next business day where practicable"),
            ("C5", "standard", "whether structural review is required for roofs framed before 1960", ""),
        ],
        programs=["Instant Solar Permit", "SolarFast Automated Permitting", "Residential Solar Express Permit", "One-Day Solar Permit"],
        terminal=["Residential Solar Photovoltaic Permit", "Instant Solar Permit and final inspection approval"],
        lead_roles=["building", "lead_permits"],
        fee_range=(95, 450),
        fee_label="residential rooftop solar permit",
        fee_basis="flat capped fee for qualifying systems",
        app_form="Automated Residential Solar Permit Application (online)",
        checklist="Standard Plan Set and Eligibility Checklist for Rooftop Solar",
        inspection_name="single final inspection of the installed system",
        backoffice=["portal_config", "intake_screening", "exception_queue", "inspection_batch", "records_archive", "state_report", "status_update", "fee_recon"],
        extra_actors=["third_party", "building"],
        user_terms=["solar permit", "instant permit", "PTO", "final inspection"],
        news_adopt="city goes live with instant solar permits; installer says a 3-week wait became minutes",
        news_backlog="platform rejects any roof framed before 1960, pushing a third of jobs to manual plan check",
        local_names={
            "E2": ["Submit online solar application", "Apply through SolarFast portal", "File instant solar permit application"],
            "E5": ["Inspect the installed PV system", "Perform the single combined inspection", "Complete the rooftop PV final"],
        },
    ),
    # ------------------------------------------------------------------ S08
    "rental_inspection": dict(
        title="Proactive Rental Housing Inspection",
        statute_title="Rental Housing Habitability Inspection Act",
        cite="Marisol Health & Safety Code § 61240",
        bill="AB 1571 (2022)",
        shape="prescriptive",
        pace=0.9,
        state_agency="Marisol Department of Housing and Community Development",
        applicability="A jurisdiction with more than 5,000 rental units shall operate a "
        "proactive rental inspection program; a smaller jurisdiction that operates one "
        "shall conform to this chapter.",
        purpose_spec="Recite that complaint-based enforcement fails tenants who fear "
        "retaliation, that habitability defects concentrate in older stock, and that a "
        "cyclical inspection program with tenant notice and a correction period is the "
        "minimum standard.",
        defs=[
            ("residential rental unit", "a dwelling unit offered for occupancy for 30 days or more in exchange for rent"),
            ("cyclical inspection", "an inspection conducted on a schedule rather than in response to a complaint"),
            ("compliance schedule", "a written schedule approved by the agency for correcting cited violations over more than 30 days"),
        ],
        elements=[
            ("E1", "record", "Owner registration of each residential rental unit in the agency's registry, renewed annually", "applicant", False, None, ("E3",)),
            ("E2", "fee", "Annual per-unit program fee", "applicant", False, None, ("E3",)),
            ("E3", "inspection", "Inspection of each registered unit at least once every four years", "agency", False, None, ("E5",)),
            ("E4", "notice", "Written notice to the tenant and the owner at least 48 hours before entry", "agency", False, 2, ("E3",)),
            ("E5", "correction", "Correction of cited violations within 30 days or under an approved compliance schedule", "applicant", False, 30, ("E6",)),
            ("E6", "decision", "Issue a certificate of compliance for the property", "agency", False, None, ()),
            ("E7", "appeal", "Appeal of a citation to a hearing officer", "applicant", False, 15, ()),
            ("E8", "referral", "Referral of repeat violations to the state housing agency and to counsel", "agency", False, None, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the annual per-unit fee", "shall not exceed the reasonable cost of the program"),
            ("C2", "department", "which department runs the inspection program", ""),
            ("C3", "frequency", "the inspection cycle", "shall be not longer than four years"),
            ("C4", "sampling", "whether a sample of units in a multi-unit building may stand for the building", "a sample shall be not less than 20 percent of units"),
            ("C5", "appeal_body", "who hears citation appeals", ""),
            ("C6", "threshold", "whether owner-occupied duplexes are exempt", ""),
        ],
        programs=["Rental Housing Safety Program", "Residential Rental Inspection Program", "Proactive Rental Inspection Program", "Healthy Housing Inspection Program"],
        terminal=["Certificate of Compliance for the rental property", "Rental Housing Safety Certificate"],
        lead_roles=["code_enforcement", "building", "housing"],
        fee_range=(28, 145),
        fee_label="annual per-unit rental registration and inspection",
        fee_basis="per-unit annual fee, tiered by building size",
        app_form="Residential Rental Unit Registration Form",
        checklist="Rental Housing Habitability Inspection Checklist",
        inspection_name="cyclical habitability inspection of the unit",
        backoffice=["intake_screening", "inspection_batch", "tenant_notice", "reinspection_sched", "ce_referral", "records_archive", "supervisor_denial", "status_update", "fee_recon", "qa_audit"],
        extra_actors=["code_enforcement", "tenant", "hearing", "attorney"],
        user_terms=["rental inspection", "RHSP", "inspector came by", "notice of violation"],
        news_adopt="council adopts proactive inspections over landlord objections; fee set at $58 a unit",
        news_backlog="eight inspectors for 23,000 units; the four-year cycle is really seven",
        local_names={
            "E1": ["Register the rental units", "Renew the annual rental registration", "File the rental unit roster"],
            "E3": ["Inspect the unit for habitability", "Conduct the cyclical unit inspection", "Carry out the rental housing safety inspection"],
        },
    ),
    # ------------------------------------------------------------------ S09
    "backyard_hens": dict(
        title="Keeping of Domestic Fowl",
        statute_title="Urban Agriculture Domestic Fowl Act",
        cite="Marisol Food & Agric. Code § 31280",
        bill="AB 640 (2021)",
        shape="minimal",
        pace=0.45,
        state_agency="Marisol Department of Food and Agriculture",
        applicability="A city or county that permits the keeping of domestic fowl on "
        "residential parcels shall use the procedure in this section; a jurisdiction may "
        "prohibit roosters.",
        purpose_spec="Recite food security and urban agriculture interests, the small "
        "administrative burden of fowl permits, and a short decision clock with a record "
        "by parcel.",
        defs=[
            ("domestic fowl", "chickens, ducks, and other poultry kept for eggs or companionship, excluding roosters"),
            ("coop", "an enclosed structure housing domestic fowl"),
        ],
        elements=[
            ("E1", "application", "Application to keep domestic fowl, stating the number of birds and the coop location", "applicant", False, None, ("E2",)),
            ("E2", "decision", "Approve or deny the application", "agency", False, 20, ()),
            ("E3", "record", "Record of permits issued, by parcel", "agency", False, None, ()),
            ("E4", "notice", "Notice to adjacent property owners", "agency", True, None, ("E2",)),
            ("E5", "inspection", "Inspection of the coop for setback and sanitation compliance", "agency", True, None, ("E2",)),
        ],
        choices=[
            ("C1", "fee_amount", "the permit fee", "shall not exceed the reasonable cost of processing"),
            ("C2", "department", "which department issues fowl permits", ""),
            ("C3", "cap", "the maximum number of birds", ""),
            ("C4", "threshold", "the coop setback from property lines and dwellings", ""),
            ("C5", "renewal", "whether the permit renews annually", ""),
        ],
        programs=["Backyard Hen Permit", "Domestic Fowl Permit", "Urban Chicken Keeping Permit", "Small Animal Keeping Clearance"],
        terminal=["Domestic Fowl Permit", "Backyard Hen Permit"],
        lead_roles=["planning", "code_enforcement", "animal"],
        fee_range=(15, 120),
        fee_label="domestic fowl permit",
        fee_basis="flat fee, renewed annually in some jurisdictions",
        app_form="Domestic Fowl Keeping Permit Application",
        checklist="Coop Standards and Setback Handout",
        inspection_name="coop setback and sanitation inspection",
        backoffice=["intake_screening", "zoning_check", "notice_mailing", "records_archive", "ce_referral", "status_update"],
        extra_actors=["code_enforcement", "animal"],
        user_terms=["chicken permit", "hens", "coop setback", "neighbor complained about my chickens"],
        news_adopt="six hens allowed, no roosters; the ordinance passes after a 40-minute debate",
        news_backlog="permits are quick, but code enforcement fields 60 chicken complaints a year",
        local_names={
            "E1": ["Apply for hen permit", "Submit domestic fowl application", "File small animal keeping clearance"],
            "E2": ["Issue the fowl permit", "Approve the hen keeping permit", "Approve the coop through zoning"],
        },
    ),
    # ------------------------------------------------------------------ S10
    "special_event": dict(
        title="Special Event Permits",
        statute_title="Public Assembly and Special Event Permit Act",
        cite="Marisol Gov. Code § 39701",
        bill="SB 211 (2022)",
        shape="mid",
        pace=0.8,
        state_agency="Marisol Office of Emergency Services",
        applicability="A city or county that requires a permit for an event on a public "
        "street, park, or plaza shall provide the procedure in this section and shall not "
        "vary charges based on the content of the event.",
        purpose_spec="Recite First Amendment limits on event permitting, the need for "
        "coordinated public-safety review, cost recovery for city services, and a fee "
        "waiver for expressive activity.",
        defs=[
            ("special event", "an organized activity on public property that requires city services or the closure of a street"),
            ("expressive activity", "conduct protected by the First Amendment, including a march, rally, or demonstration"),
        ],
        elements=[
            ("E1", "application", "Special event permit application filed at least 60 days before the event", "applicant", False, 60, ("E2",)),
            ("E2", "referral", "Coordinated review by police, fire, and public works", "agency", False, None, ("E4",)),
            ("E3", "fee", "Cost-recovery fees for city services, waivable for expressive activity", "applicant", False, None, ("E4",)),
            ("E4", "decision", "Grant or deny the permit, with conditions", "agency", False, 30, ()),
            ("E5", "public_hearing", "Council or board approval for a street closure longer than four hours", "agency", True, None, ("E4",)),
            ("E6", "appeal", "Appeal of a denial to the city manager or designee", "applicant", False, 10, ()),
            ("E7", "record", "Certificate of insurance and signed indemnification on file before the event", "applicant", False, None, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the application and service fees", "charges shall not vary with the content of the event"),
            ("C2", "department", "which office coordinates special events", ""),
            ("C3", "threshold", "the insurance minimum", ""),
            ("C4", "deadline", "the filing deadline", "shall not be more than 90 days before the event"),
            ("C5", "appeal_body", "who hears appeals", ""),
            ("C6", "standard", "the criteria for a fee waiver", ""),
        ],
        programs=["Special Event Permit", "Community Event Permit Program", "Street Closure and Event Permit", "Public Assembly Permit"],
        terminal=["Special Event Permit with conditions", "Community Event Permit and street closure authorization"],
        lead_roles=["clerk", "publicworks", "parks", "police"],
        fee_range=(85, 2200),
        fee_label="special event permit and city service charges",
        fee_basis="application fee plus actual cost of police, fire, and public works services",
        app_form="Special Event Permit Application",
        checklist="Special Event Site Plan and Insurance Requirements",
        inspection_name="pre-event site walk with public safety staff",
        confirm_meeting="special event review committee meeting",
        backoffice=["intake_screening", "event_committee", "police_referral", "fire_referral", "pw_referral", "insurance_check", "council_agenda", "records_archive", "status_update", "fee_recon"],
        extra_actors=["police", "fire", "publicworks", "clerk", "council"],
        user_terms=["event permit", "street closure", "block party", "insurance certificate"],
        news_adopt="new event ordinance sets a 60-day deadline and waives fees for protests",
        news_backlog="organizers say the review committee meets twice a month and misses its own clock",
        local_names={
            "E1": ["Submit special event application", "File community event permit application", "Apply for street closure permit"],
            "E2": ["Route the application to the event review committee", "Coordinate the public safety review", "Circulate the application for interdepartmental review"],
        },
    ),
    # ------------------------------------------------------------------ S11
    "well_permit": dict(
        title="Water Well Construction Permits",
        statute_title="Water Well Standards and Permitting Act",
        cite="Marisol Water Code § 13801",
        bill="AB 2201 (2020)",
        shape="mid",
        pace=0.8,
        state_agency="Marisol State Water Resources Board",
        applicability="Each county shall adopt a well construction ordinance meeting the "
        "state standards; a city may delegate well permitting to the county.",
        purpose_spec="Recite groundwater contamination pathways through improperly sealed "
        "wells, the state well standards bulletin, and the required construction "
        "inspection and completion report.",
        defs=[
            ("well", "an excavation used to extract groundwater, or to monitor or recharge an aquifer"),
            ("annular seal", "the grout seal between the well casing and the borehole wall"),
            ("C-57 contractor", "a contractor licensed in the water well drilling classification"),
        ],
        elements=[
            ("E1", "application", "Well construction, alteration, or destruction permit application with a site plan showing setbacks", "applicant", False, None, ("E5",)),
            ("E2", "fee", "Permit and inspection fee", "applicant", False, None, ("E5",)),
            ("E3", "third_party_option", "Certification of the annular seal by the licensed C-57 drilling contractor", "third_party", True, None, ("E4",)),
            ("E4", "inspection", "Inspection of the annular seal during construction", "agency", False, None, ("E6",)),
            ("E5", "decision", "Issue the well permit", "agency", False, 30, ("E4",)),
            ("E6", "record", "Well completion report filed with the state water board within 60 days", "applicant", False, 60, ()),
            ("E7", "referral", "Referral to the health department where the well will serve a public water system", "agency", False, None, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the permit and inspection fee", "shall not exceed the reasonable cost of the program"),
            ("C2", "department", "which division issues well permits", ""),
            ("C3", "threshold", "setback distances from septic systems and property lines", "shall be not less than the state standards"),
            ("C4", "frequency", "which construction stages are inspected", "the annular seal shall be inspected"),
            ("C5", "delegation", "whether a city delegates well permitting to the county", ""),
        ],
        programs=["Well Permit Program", "Water Well Construction Permit", "Groundwater Well Permitting", "Well and Septic Permit Program"],
        terminal=["Well Construction Permit and final seal approval", "Water Well Permit"],
        lead_roles=["health", "publicworks", "building"],
        fee_range=(320, 1900),
        fee_label="well construction permit and inspection",
        fee_basis="flat permit fee plus per-inspection charge",
        app_form="Well Construction Permit Application",
        checklist="Well Construction Standards and Setback Checklist",
        inspection_name="annular seal inspection during drilling",
        backoffice=["intake_screening", "gis_parcel", "second_review", "inspection_batch", "state_report", "health_referral", "records_archive", "status_update", "fee_recon"],
        extra_actors=["health", "third_party", "state_agency"],
        user_terms=["well permit", "C-57 driller", "seal inspection", "completion report"],
        news_adopt="county tightens well setbacks after nitrate findings; drillers warn of delays",
        news_backlog="drought applications triple; the single well inspector schedules two weeks out",
        local_names={
            "E1": ["Submit well permit application", "Apply for water well construction permit", "File well application with Environmental Health"],
            "E4": ["Inspect the seal during drilling", "Inspect the annular seal in the field", "Inspect the construction at grouting"],
        },
    ),
    # ------------------------------------------------------------------ S12
    "contractor_registration": dict(
        title="Local Contractor Registration",
        statute_title="Local Contractor Registration Uniformity Act",
        cite="Marisol Bus. & Prof. Code § 7302",
        bill="SB 588 (2021)",
        shape="mid",
        pace=0.4,
        state_agency="Marisol Contractors State License Board",
        applicability="A city or county that requires local registration of contractors "
        "shall conform to this section and shall not require a local examination.",
        purpose_spec="Recite duplicative local registration requirements, unlicensed "
        "activity, and workers' compensation verification; require verification against "
        "the state registry rather than a local examination.",
        defs=[
            ("contractor", "a person licensed under Division 3, Chapter 9 of this code"),
            ("state registry", "the online license and workers' compensation database maintained by the board"),
        ],
        elements=[
            ("E1", "application", "Local contractor registration application with the state license number and certificate of insurance", "applicant", False, None, ("E2",)),
            ("E2", "record", "Verification of the state license and workers' compensation coverage against the state registry", "agency", False, None, ("E4",)),
            ("E3", "fee", "Registration fee", "applicant", False, None, ("E4",)),
            ("E4", "decision", "Issue the registration certificate", "agency", False, 10, ()),
            ("E5", "notice", "Renewal notice mailed 30 days before expiration", "agency", False, 30, ()),
            ("E6", "appeal", "Appeal of a denial or revocation to a hearing officer", "applicant", False, 15, ()),
        ],
        choices=[
            ("C1", "fee_amount", "the registration fee", "shall not exceed the reasonable cost of verification and processing"),
            ("C2", "department", "which department registers contractors", ""),
            ("C3", "renewal", "the registration period", ""),
            ("C4", "standard", "whether insurance is verified at renewal as well as at issuance", ""),
            ("C5", "appeal_body", "who hears denials and revocations", ""),
        ],
        programs=["Contractor Business Registration", "Local Contractor Registration", "Contractor License Verification Program", "Building Contractor Registry"],
        terminal=["Local Contractor Registration Certificate", "Contractor Business Registration"],
        lead_roles=["finance", "building", "lead_permits"],
        fee_range=(55, 480),
        fee_label="local contractor registration",
        fee_basis="annual or biennial registration fee",
        app_form="Local Contractor Registration Application",
        checklist="Contractor Registration Document Checklist",
        inspection_name="records audit of insurance certificates",
        backoffice=["intake_screening", "license_verify", "insurance_check", "status_update", "notice_mailing", "records_archive", "fee_recon", "appeal_docket"],
        extra_actors=["finance", "state_agency", "hearing"],
        user_terms=["city business registration", "contractor license", "workers comp cert"],
        news_adopt="city drops its local contractor test after the state act; registration moves online",
        news_backlog="registrations pile up when the business tax office loses a clerk",
        local_names={
            "E1": ["Submit contractor registration application", "Register as a city contractor", "Apply for contractor business registration"],
            "E4": ["Issue the registration certificate", "Approve the contractor registration", "Issue the business registration"],
        },
    ),
}

DOMAIN_ORDER = list(DOMAINS)


def stat_id_for(domain: str) -> str:
    return "S%02d" % (DOMAIN_ORDER.index(domain) + 1)


def domain_for(stat_id: str) -> str:
    return DOMAIN_ORDER[int(stat_id[1:]) - 1]
