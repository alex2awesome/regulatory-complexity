"""The decision layer: statute -> decision function -> jurisdiction readings -> process.

Motivation (Dan Ho, 2026-09-16 discussion, recorded in
docs/2026-09-16-bayesian-overnight-audit.md and docs/2026-09-16-decision-model-generator.md):
a statute fixes a *decision function* D over case facts only partly. Its
discretionary predicates are underdetermined by the text, and each implementing
jurisdiction resolves them with a *reading*. The process is the program that
evaluates D: it decides which activity checks which predicate and what happens
when a check fails. Cross-jurisdiction disagreement on readings is the empirical
discretion residual, and the process reconstruction pipeline is the instrument
that measures it. This module plants all of that as ground truth so that
recovery of readings, and of their dispersion across jurisdictions, can be
scored against a known answer.

Three kinds of predicate, per statute:

* ``crisp``      -- the statute fixes the test exactly ("built before January 1,
                    2020"). Every jurisdiction applies the same reading unless it
                    mis-implements it (``p_misimplement``), and a look-alike
                    statute in the neighbour state carries a different constant.
* ``standard``   -- the statute uses a standard word ("substandard condition",
                    "objective standard", "public safety") and says no number.
                    Each jurisdiction picks a reading from a small ordered
                    space, lenient to strict, with planted weights spread by the
                    ``discretion_spread`` knob.
* ``delegated``  -- the statute expressly leaves a threshold, cap or standard to
                    the local agency (an existing ``open_choices`` entry of kind
                    threshold/cap/standard/...). The reading follows the value the
                    local rule already chose, so the ordinance text and the
                    planted reading agree.
* ``local``      -- a jurisdiction's ``stricter_standards`` entry that is testable
                    against a case fact becomes an added predicate (ids ``Q*``).

A predicate is attached to the activity implementing the statute element that
evaluates it (application, inspection, decision, ...). A failing *fixable*
predicate sends the case round the activity's rework loop; a failing *fatal*
predicate is a denial at the decision step. Under ``decision_model_version`` 2 the
simulator's outcomes come from these evaluations over sampled case facts, so the
denial and correction rates are consequences of the readings rather than free
parameters; a stricter jurisdiction denies and corrects more.

Everything here is a pure function of the truth plus ``sub_rng`` draws, like the
rest of the generator. Legacy worlds (no ``decision_model_version`` knob) are
untouched: every hook returns early when the version is 1.
"""
from __future__ import annotations

import math

from .rng import chance, pick, sub_rng, weighted

VERSION_KEY = "decision_model_version"


def enabled(world: dict) -> bool:
    return int(world.get("knobs", {}).get(VERSION_KEY, 1)) >= 2


# ------------------------------------------------------------ predicates --
# Attribute distributions: ("normal", mu, sd) | ("lognormal", median, p90) |
# ("bernoulli", p) | ("choice", [(value, weight), ...]) | ("uniform", lo, hi).
# Readings: op in lt/le/gt/ge/eq/ne/in/not_in/always/bern; ``strictness`` orders
# the reading space (0 = most lenient); ``weight`` is the planted prior over
# jurisdictions for standard predicates; ``approx`` is the hedged phrasing.

def _r(label, op, value=None, strictness=1, weight=1.0, approx=None):
    return {"label": label, "op": op, "value": value, "strictness": strictness,
            "weight": weight, "approx": approx or label}


def _crisp(pid, name, attribute, element, dist, reading, alternates, question, unit="",
           fixable=False, statute_text=None, backoffice=()):
    return dict(pid=pid, name=name, attribute=attribute, kind="crisp", element=element, bound=None,
                dist=dist, readings=[reading], alternates=alternates, question=question,
                unit=unit, fixable=fixable, standard=None, choice=None,
                statute_text=statute_text or reading["label"], backoffice=tuple(backoffice))


def _standard(pid, name, attribute, element, dist, standard, readings, question, unit="",
              fixable=True, backoffice=()):
    return dict(pid=pid, name=name, attribute=attribute, kind="standard", element=element, bound=None,
                dist=dist, readings=readings, alternates=[], question=question, unit=unit,
                fixable=fixable, standard=standard, choice=None,
                statute_text="must satisfy the '%s' standard; the statute states no number" % standard,
                backoffice=tuple(backoffice))


def _delegated(pid, name, attribute, element, dist, choice, readings, question, unit="",
               fixable=True, backoffice=()):
    return dict(pid=pid, name=name, attribute=attribute, kind="delegated", element=element, bound=None,
                dist=dist, readings=readings, alternates=[], question=question, unit=unit,
                fixable=fixable, standard=None, choice=choice,
                statute_text="left to the local agency (open choice %s)" % choice,
                backoffice=tuple(backoffice))


def _capped(pid, name, attribute, element, dist, bound_label, bound_op, bound_value,
            under_values, question, unit="", fixable=True, bound_text=None):
    """A dimension the statute BOUNDS but does not fix.

    Welf. & Inst. Code 17001.5 is the real instance and the reason this kind
    exists (see docs/2026-09-16-county-scale-up-plan.md section 12). The statute
    says a residency requirement "shall not exceed 15 days", so a county may pick
    anything up to 15 and the observed rules pile onto the cap: five verified
    counties chose exactly 15 days, and nine of eleven employable time limits are
    exactly the permitted three months.

    That produces a variance signature no other kind has. A `standard` predicate
    disperses because the statute is silent; a `capped` predicate CONCENTRATES on
    the bound because the statute named it. Scoring the CONTRAST between the two
    is a sharper test than recovering dispersion, because it cannot be satisfied
    by predicting the modal reading everywhere.

    `under_values` are the lawful readings strictly inside the bound, weighted low
    so most jurisdictions sit on the cap.
    """
    readings = [_r(bound_label, bound_op, bound_value, strictness=2, weight=.70)]
    for label, value, weight in under_values:
        readings.append(_r(label, bound_op, value, strictness=1, weight=weight))
    return dict(pid=pid, name=name, attribute=attribute, kind="capped", element=element,
                dist=dist, readings=readings, alternates=[], question=question, unit=unit,
                fixable=fixable, standard=None, choice=None, bound=bound_value,
                statute_text=bound_text or ("the statute bounds this at %s and leaves any "
                                            "lesser requirement to the local agency" % bound_label),
                backoffice=())


PREDICATES: dict[str, list[dict]] = {
    "unpermitted_unit_amnesty": [
        _crisp("P1", "Unit built before the cutoff date", "construction_year", "E1",
               ("choice", [((1960, 1999), 0.45), ((2000, 2015), 0.35), ((2016, 2019), 0.12), ((2020, 2024), 0.08)]),
               _r("the unit was created before January 1, 2020", "lt", 2020),
               [_r("the unit was created before January 1, 2018", "lt", 2018),
                _r("the unit was created before January 1, 2022", "lt", 2022)],
               "When was the unit built or converted?", "", fixable=False,
               statute_text="a dwelling unit created without a required building permit before January 1, 2020"),
        _standard("P2", "Ceiling height meets the substandard-conditions list", "ceiling_height_ft", "E2",
                  ("normal", 7.25, 0.45), "substandard condition",
                  [_r("a ceiling height of at least 6 feet 8 inches", "ge", 6.67, 0, 0.3, "roughly six and a half feet of headroom"),
                   _r("a ceiling height of at least 7 feet", "ge", 7.0, 1, 0.5, "about seven feet of ceiling height"),
                   _r("a ceiling height of at least 7 feet 6 inches", "ge", 7.5, 2, 0.2, "seven and a half feet or so of ceiling height")],
                  "What is the ceiling height of the unit?", "feet"),
        _delegated("P3", "Parcel is eligible by unit count", "parcel_units", "E1",
                   ("choice", [(1, 0.66), (2, 0.2), (3, 0.05), (4, 0.04), (6, 0.05)]), "C5",
                   [_r("units on parcels with up to four dwelling units are eligible", "le", 4, 1, approx="parcels with a handful of units qualify"),
                    _r("units on single-family and duplex parcels only", "le", 2, 2, approx="only houses and duplexes qualify"),
                    _r("all residentially zoned parcels are eligible", "always", None, 0, approx="any residential parcel qualifies")],
                   "How many dwelling units are on the parcel?", "units", fixable=False,
                   backoffice=("zoning_check", "gis_parcel")),
        _capped("P4", "Local residency before applying", "days_resident", "E1",
                ("lognormal", 400, 3000),
                "a residency requirement of 15 days", "ge", 15,
                [("a residency requirement of 10 days", 10, .18),
                 ("a residency requirement of 5 days", 5, .12)],
                "How long has the applicant lived in the jurisdiction?", "days",
                bound_text="a residence requirement, which shall not exceed 15 days"),
    ],
    "str_registration": [
        _crisp("P1", "A 24-hour local contact is named", "local_contact_named", "E1",
               ("bernoulli", 0.9), _r("the registration names a local contact reachable 24 hours a day", "eq", True),
               [_r("the registration names a local contact reachable during business hours", "eq", True)],
               "Is a 24-hour local contact named?", "", fixable=True),
        _standard("P2", "The unit is the host's primary residence", "owner_days_in_residence", "E4",
                  ("normal", 240, 70), "primary residence",
                  [_r("the host occupies the unit at least 183 days a year", "ge", 183, 0, 0.45, "the host lives there most of the year"),
                   _r("the host occupies the unit at least 275 days a year", "ge", 275, 1, 0.35, "the host lives there nearly year-round"),
                   _r("the host occupies the unit at least 330 days a year", "ge", 330, 2, 0.2, "the host must live there essentially full time")],
                  "How many days a year does the host live in the unit?", "days", fixable=False),
        _delegated("P3", "Planned rental nights are within the cap", "planned_nights", "E4",
                   ("lognormal", 90, 250), "C3",
                   [_r("unhosted rentals are limited to 120 nights per year", "le", 120, 1, approx="around four months of unhosted nights"),
                    _r("non-hosted registrations are capped citywide and allocated by lottery", "bern", 0.6, 2, approx="you have to win the annual lottery"),
                    _r("no cap on nights; one registration per host", "always", None, 0, approx="no limit on nights")],
                   "How many nights a year will the unit be rented?", "nights", backoffice=("tax_cert_check",)),
    ],
    "sidewalk_vending": [
        _crisp("P1", "A food vendor holds a county health permit", "health_permit_ok", "E4",
               ("bernoulli", 0.82), _r("a vendor selling food holds a current county health permit", "eq", True),
               [_r("a vendor selling food holds a current state food handler card", "eq", True)],
               "Does the food vendor hold a county health permit?", "", fixable=True),
        _standard("P2", "Vending location is clear of crosswalks and entrances", "distance_to_crosswalk_ft", "E5",
                  ("lognormal", 30, 120), "objective health, safety, or welfare concern",
                  [_r("no vending within 10 feet of a crosswalk or building entrance", "ge", 10, 0, 0.35, "keep about ten feet back from crossings"),
                   _r("no vending within 15 feet of a crosswalk or building entrance", "ge", 15, 1, 0.4, "roughly fifteen feet from crossings and doors"),
                   _r("no vending within 25 feet of a crosswalk or building entrance", "ge", 25, 2, 0.25, "keep well back, twenty-odd feet, from crossings")],
                  "How far is the vending location from the nearest crosswalk or building entrance?", "feet"),
        _delegated("P3", "Proposed vending hours are within the local limit", "proposed_end_hour", "E5",
                   ("choice", [(18, 0.3), (20, 0.35), (21, 0.2), (22, 0.15)]), "C3",
                   [_r("no vending in residential zones after 8:00 p.m.", "le", 20, 1, approx="wrap up by about eight in the evening"),
                    _r("vending permitted 7:00 a.m. to 9:00 p.m.", "le", 21, 0, approx="you can vend until about nine at night"),
                    _r("vending permitted 6:00 a.m. to 10:00 p.m. in commercial zones only", "le", 22, 0, approx="until about ten at night, commercial areas only")],
                   "Until what hour does the vendor propose to operate?", "hour"),
    ],
    "tree_removal": [
        _crisp("P1", "A site plan accompanies the application", "site_plan_included", "E1",
               ("bernoulli", 0.85), _r("the application includes a site plan showing the tree", "eq", True),
               [_r("the application includes a survey showing the tree", "eq", True)],
               "Does the application include a site plan?", "", fixable=True),
        _standard("P2", "The tree's condition justifies removal", "tree_condition_score", "E4",
                  ("normal", 0.5, 0.25), "condition",
                  [_r("removal is justified where the tree is in fair or worse condition", "le", 0.7, 0, 0.35, "a tree in fair shape or worse can come out"),
                   _r("removal is justified where the tree is in poor condition", "le", 0.5, 1, 0.4, "the tree has to be in poor condition"),
                   _r("removal is justified only where the tree is dead, dying, or hazardous", "le", 0.3, 2, 0.25, "only dead or hazardous trees can be removed")],
                  "What is the arborist's condition rating of the tree?", "", fixable=False),
        _delegated("P3", "Replacement planting meets the ratio", "replacement_capacity", "E7",
                   ("choice", [(0, 0.15), (1, 0.3), (2, 0.3), (3, 0.15), (5, 0.1)]), "C4",
                   [_r("two 24-inch box replacement trees per removed tree, or an in-lieu fee", "ge", 2, 1, approx="a couple of replacement trees or a fee"),
                    _r("one-for-one replacement with a 15-gallon tree, or an in-lieu payment", "ge", 1, 0, approx="one replacement tree or a payment"),
                    _r("three inches of new trunk diameter for every inch removed, or an appraised-value in-lieu fee", "ge", 3, 2, approx="several replacement trees or an appraised fee")],
                   "How many replacement trees can the site accommodate?", "trees"),
    ],
    "home_business": [
        _crisp("P1", "The activity is not a prohibited use", "prohibited_use", "E2",
               ("bernoulli", 0.06), _r("the activity is not vehicle repair, welding, or the storage of hazardous materials", "eq", False),
               [_r("the activity is not vehicle repair or the storage of hazardous materials", "eq", False)],
               "Is the activity on the prohibited-use list?", "", fixable=False),
        _standard("P2", "The business occupies a minor share of the dwelling", "floor_area_share", "E2",
                  ("normal", 0.2, 0.1), "objective standard",
                  [_r("the business occupies no more than 25 percent of the floor area", "le", 0.25, 0, 0.35, "about a quarter of the house at most"),
                   _r("the business occupies no more than 20 percent of the floor area", "le", 0.20, 1, 0.4, "roughly a fifth of the floor area"),
                   _r("the business occupies no more than 15 percent of the floor area", "le", 0.15, 2, 0.25, "only a small corner of the house")],
                  "What share of the dwelling's floor area does the business use?", "share"),
        _delegated("P3", "Nonresident employees are within the limit", "nonresident_employees", "E2",
                   ("choice", [(0, 0.6), (1, 0.25), (2, 0.1), (3, 0.05)]), "C3",
                   [_r("no more than one nonresident employee", "le", 1, 1, approx="one outside employee at most"),
                    _r("no nonresident employees", "le", 0, 2, approx="no outside employees at all"),
                    _r("no more than two nonresident employees", "le", 2, 0, approx="a couple of outside employees are fine")],
                   "How many nonresident employees work at the home?", "employees", backoffice=("zoning_check",)),
    ],
    "mobile_food": [
        _crisp("P1", "A commissary agreement is on file", "commissary_agreement", "E2",
               ("bernoulli", 0.88), _r("the application includes a signed commissary agreement", "eq", True),
               [_r("the application includes a signed commissary or commercial-kitchen agreement", "eq", True)],
               "Is a commissary agreement on file?", "", fixable=True),
        _standard("P2", "The unit passes the pre-operational sanitation inspection", "sanitation_score", "E4",
                  ("normal", 0.78, 0.12), "pre-operational inspection",
                  [_r("the unit scores at least 60 on the sanitation inspection", "ge", 0.6, 0, 0.3, "a passing sanitation score, low sixties"),
                   _r("the unit scores at least 70 on the sanitation inspection", "ge", 0.7, 1, 0.45, "a sanitation score around seventy"),
                   _r("the unit scores at least 80 on the sanitation inspection", "ge", 0.8, 2, 0.25, "a high sanitation score, eighty or so")],
                  "What is the unit's sanitation inspection score?", "points"),
        _delegated("P3", "The commissary's own permit is verified", "commissary_permit_current", "E4",
                   ("bernoulli", 0.85), "C3",
                   [_r("the commissary agreement is verified by a call to the operator", "always", None, 0, approx="they phone the commissary"),
                    _r("a copy of the commissary's current health permit is required", "eq", True, 2, approx="you need the commissary's own permit"),
                    _r("the commissary is verified by inspection during the pre-operational inspection", "eq", True, 1, approx="the inspector checks the commissary too")],
                   "Is the commissary's health permit current?", ""),
    ],
    "solar_auto_permit": [
        _crisp("P1", "System size is within the automated-permit limit", "system_kw", "E2",
               ("lognormal", 9, 30), _r("the system is 38.4 kilowatts or smaller", "le", 38.4),
               [_r("the system is 30 kilowatts or smaller", "le", 30.0), _r("the system is 50 kilowatts or smaller", "le", 50.0)],
               "What is the system's rated size in kilowatts?", "kW", fixable=False),
        _standard("P2", "The plan set is complete and compliant", "plan_conformance", "E3",
                  ("normal", 0.85, 0.12), "complete and compliant",
                  [_r("the plan set conforms to the standard plan in all material respects", "ge", 0.7, 0, 0.35, "the plans just need to broadly match the standard set"),
                   _r("the plan set conforms to the standard plan with no more than minor deviations", "ge", 0.8, 1, 0.4, "the plans have to match the standard set closely"),
                   _r("the plan set conforms to the standard plan exactly", "ge", 0.9, 2, 0.25, "the plans must match the standard set line for line")],
                  "How closely does the plan set conform to the standard plan?", "score"),
        _delegated("P3", "The roof passes the structural screen", "roof_year", "E3",
                   ("choice", [((1930, 1959), 0.18), ((1960, 1990), 0.42), ((1991, 2024), 0.4)]), "C5",
                   [_r("roofs framed before 1960 require a stamped structural letter", "ge", 1960, 1, approx="old roofs, pre-sixties, need an engineer's letter"),
                    _r("no structural review for light systems; installer certification accepted", "always", None, 0, approx="no structural review for normal systems"),
                    _r("structural review only where the platform flags a long-span truss roof", "ge", 1950, 0, approx="only unusual roofs get a structural check")],
                   "When was the roof framed?", "year"),
    ],
    "rental_inspection": [
        _crisp("P1", "The unit is registered in the rental registry", "unit_registered", "E1",
               ("bernoulli", 0.92), _r("the unit is registered in the agency's rental registry before inspection", "eq", True),
               [_r("the unit is registered with the county assessor as a rental", "eq", True)],
               "Is the unit registered?", "", fixable=True),
        _standard("P2", "Habitability violations are within tolerance", "habitability_violations", "E3",
                  ("choice", [(0, 0.45), (1, 0.25), (2, 0.15), (3, 0.1), (5, 0.05)]), "habitability",
                  [_r("a unit passes with up to two minor habitability violations", "le", 2, 0, 0.3, "a couple of minor items are tolerated"),
                   _r("a unit passes with no more than one minor habitability violation", "le", 1, 1, 0.45, "one minor item is tolerated"),
                   _r("a unit passes only with no habitability violations", "le", 0, 2, 0.25, "any violation fails the unit")],
                  "How many habitability violations were found?", "violations"),
        _standard("P3", "Corrections are completed within the compliance schedule", "days_to_correct", "E5",
                  ("lognormal", 20, 60), "compliance schedule",
                  [_r("cited violations are corrected within 45 days", "le", 45, 0, 0.3, "about six weeks to fix things"),
                   _r("cited violations are corrected within 30 days", "le", 30, 1, 0.5, "roughly a month to fix things"),
                   _r("cited violations are corrected within 14 days", "le", 14, 2, 0.2, "two weeks to fix things")],
                  "How many days did the owner take to correct the violations?", "days"),
        _capped("P4", "Correction period allowed before citation", "days_to_correct", "E5",
                ("lognormal", 20, 60),
                "30 days to correct cited violations", "le", 30,
                [("21 days to correct cited violations", 21, .16),
                 ("14 days to correct cited violations", 14, .14)],
                "How many days was the owner given to correct?", "days",
                bound_text="a correction period, which shall be not less than 30 days"),
    ],
    "backyard_hens": [
        _crisp("P1", "No roosters are kept", "has_rooster", "E1",
               ("bernoulli", 0.12), _r("no roosters are kept on the parcel", "eq", False),
               [_r("no more than one rooster is kept on the parcel", "eq", False)],
               "Are any roosters kept?", "", fixable=True),
        _standard("P2", "The coop meets the sanitation standard", "coop_condition_score", "E5",
                  ("normal", 0.75, 0.15), "sanitation",
                  [_r("the coop is kept reasonably clean and free of standing waste", "ge", 0.5, 0, 0.35, "the coop just has to be reasonably clean"),
                   _r("the coop is kept clean, dry, and free of odor beyond the property line", "ge", 0.65, 1, 0.4, "the coop has to be clean and not smell next door"),
                   _r("the coop is cleaned weekly with waste stored in a sealed container", "ge", 0.8, 2, 0.25, "weekly cleaning and sealed waste storage")],
                  "What is the inspector's condition rating of the coop?", ""),
        _delegated("P3", "The flock is within the cap", "birds_requested", "E1",
                   ("choice", [(2, 0.15), (4, 0.3), (6, 0.3), (8, 0.15), (12, 0.1)]), "C3",
                   [_r("up to six hens", "le", 6, 1, approx="about half a dozen hens"),
                    _r("up to four hens on a small lot", "le", 4, 2, approx="four hens on a normal lot"),
                    _r("up to twelve hens with a ministerial permit", "le", 12, 0, approx="a dozen hens is fine")],
                   "How many birds does the applicant propose to keep?", "birds", backoffice=("zoning_check", "gis_parcel")),
    ],
    "special_event": [
        _crisp("P1", "A certificate of insurance is on file", "insurance_on_file", "E7",
               ("bernoulli", 0.9), _r("a certificate of insurance naming the city is on file before the event", "eq", True),
               [_r("a certificate of insurance is on file before the event", "eq", True)],
               "Is the certificate of insurance on file?", "", fixable=True),
        _standard("P2", "Crowd size is within the safety-plan threshold", "attendance", "E2",
                  ("lognormal", 300, 3000), "public safety",
                  [_r("events over 1,000 attendees require a crowd-management plan", "le", 1000, 0, 0.35, "big events, a thousand-plus people, need a crowd plan"),
                   _r("events over 500 attendees require a crowd-management plan", "le", 500, 1, 0.4, "anything over about five hundred people needs a crowd plan"),
                   _r("events over 250 attendees require a crowd-management plan", "le", 250, 2, 0.25, "even a modest crowd, a few hundred, needs a crowd plan")],
                  "What is the expected attendance?", "attendees"),
        _delegated("P3", "The application was filed by the deadline", "days_before_event", "E1",
                   ("lognormal", 55, 120), "C4",
                   [_r("filed at least 60 days before the event", "ge", 60, 1, approx="about two months ahead"),
                    _r("filed at least 30 days before the event, with a surcharge inside 45", "ge", 30, 0, approx="a month ahead, with a late fee if under six weeks"),
                    _r("filed at least 60 days before the event, 10 for expressive activity", "ge", 60, 1, approx="two months ahead unless it is a demonstration")],
                   "How many days before the event was the application filed?", "days", fixable=False),
    ],
    "well_permit": [
        _crisp("P1", "The driller holds a C-57 licence", "contractor_licensed", "E1",
               ("bernoulli", 0.93), _r("the well is constructed by a C-57 licensed contractor", "eq", True),
               [_r("the well is constructed by a state-registered driller", "eq", True)],
               "Is the drilling contractor C-57 licensed?", "", fixable=True),
        _standard("P2", "The annular seal is adequate", "seal_depth_ft", "E4",
                  ("normal", 50, 12), "annular seal",
                  [_r("an annular seal of at least 20 feet", "ge", 20, 0, 0.3, "twenty-odd feet of seal"),
                   _r("an annular seal of at least 50 feet", "ge", 50, 1, 0.5, "around fifty feet of seal"),
                   _r("an annular seal of at least 60 feet", "ge", 60, 2, 0.2, "sixty feet of seal or more")],
                  "How deep is the annular seal?", "feet"),
        _delegated("P3", "Setback from the septic leach field is met", "distance_to_septic_ft", "E5",
                   ("lognormal", 120, 250), "C3",
                   [_r("at least 100 feet from a septic leach field", "ge", 100, 0, approx="a hundred feet from the leach field"),
                    _r("at least 150 feet from a septic leach field", "ge", 150, 2, approx="a hundred and fifty feet from the leach field"),
                    _r("the state standard setback of 100 feet, waivable on a hydrogeologic report", "ge", 100, 1, approx="the standard hundred feet, unless a report says otherwise")],
                   "How far is the well from the nearest septic leach field?", "feet", fixable=False),
    ],
    "contractor_registration": [
        _crisp("P1", "The state licence is active", "license_active", "E2",
               ("bernoulli", 0.9), _r("the state contractor licence is active and in good standing", "eq", True),
               [_r("the state contractor licence is active", "eq", True)],
               "Is the state licence active?", "", fixable=False, backoffice=("license_verify",)),
        _standard("P2", "Workers' compensation coverage is adequate", "wc_coverage_status", "E2",
                  ("choice", [("current", 0.8), ("lapsed", 0.12), ("exempt_sole_proprietor", 0.08)]), "workers' compensation coverage",
                  [_r("current coverage, or a sole-proprietor exemption on the state form", "in", ["current", "exempt_sole_proprietor"], 0, 0.5, "coverage or the sole-proprietor exemption"),
                   _r("current coverage, or a sole-proprietor exemption with a sworn affidavit", "in", ["current", "exempt_sole_proprietor"], 1, 0.3, "coverage, or an exemption sworn under penalty of perjury"),
                   _r("current coverage; no exemptions accepted", "in", ["current"], 2, 0.2, "you need actual coverage, no exemptions")],
                  "What is the workers' compensation coverage status?", ""),
        _delegated("P3", "Insurance is verified", "insurance_current", "E2",
                   ("bernoulli", 0.85), "C4",
                   [_r("insurance is verified at issuance and at each renewal", "eq", True, 1, approx="they check your insurance every time"),
                    _r("insurance is verified at issuance only", "eq", True, 0, approx="they check insurance once, at the start"),
                    _r("insurance is verified at issuance, at renewal, and on large permits", "eq", True, 2, approx="they check insurance at every step and on big jobs")],
                   "Is the liability insurance current?", "", backoffice=("insurance_check",)),
    ],
}

# Testable stricter standards (local_rules.STRICTER strings) -> added predicate.
# Untested strings stay text-only, as before.
LOCAL_PREDICATES: dict[str, dict] = {
    "a 7-foot minimum ceiling height, exceeding the state standard":
        dict(attribute="ceiling_height_ft", dist=("normal", 7.25, 0.45), element="E2", fixable=True, unit="feet",
             reading=_r("a ceiling height of at least 7 feet under the local standard", "ge", 7.0, 2),
             question="Does the unit meet the local 7-foot ceiling standard?"),
    "smoke and carbon monoxide alarms required in every sleeping room, not only in the unit":
        dict(attribute="alarms_in_every_bedroom", dist=("bernoulli", 0.7), element="E2", fixable=True, unit="",
             reading=_r("smoke and carbon monoxide alarms in every sleeping room", "eq", True, 2),
             question="Are alarms installed in every sleeping room?"),
    "a 24-hour local contact must be within 25 miles":
        dict(attribute="contact_distance_miles", dist=("lognormal", 12, 60), element="E1", fixable=True, unit="miles",
             reading=_r("the local contact lives within 25 miles", "le", 25, 2),
             question="How far away is the local contact?"),
    "a certified food handler card is required for every worker on the cart":
        dict(attribute="all_workers_carded", dist=("bernoulli", 0.65), element="E5", fixable=True, unit="",
             reading=_r("every worker on the cart holds a food handler card", "eq", True, 2),
             question="Does every worker hold a food handler card?"),
    "an arborist report is required for every application, not only contested ones":
        dict(attribute="arborist_report_included", dist=("bernoulli", 0.55), element="E1", fixable=True, unit="",
             reading=_r("an arborist report accompanies every application", "eq", True, 2),
             question="Is an arborist report included?"),
    "no commercial vehicle over 10,000 pounds may be parked on the parcel":
        dict(attribute="heavy_vehicle_on_parcel", dist=("bernoulli", 0.08), element="E2", fixable=True, unit="",
             reading=_r("no commercial vehicle over 10,000 pounds on the parcel", "eq", False, 2),
             question="Is a heavy commercial vehicle parked on the parcel?"),
    "propane systems must carry a current third-party inspection tag":
        dict(attribute="propane_tag_current", dist=("bernoulli", 0.7), element="E4", fixable=True, unit="",
             reading=_r("a current third-party propane inspection tag", "eq", True, 2),
             question="Is the propane tag current?"),
    "pre-1960 roofs require a stamped structural letter":
        dict(attribute="roof_year", dist=("choice", [((1930, 1959), 0.18), ((1960, 1990), 0.42), ((1991, 2024), 0.4)]),
             element="E3", fixable=True, unit="year",
             reading=_r("roofs framed before 1960 carry a stamped structural letter", "ge", 1960, 2),
             question="When was the roof framed?"),
    "every unit must have a working GFCI in the kitchen and bath regardless of construction date":
        dict(attribute="gfci_installed", dist=("bernoulli", 0.6), element="E3", fixable=True, unit="",
             reading=_r("working GFCI protection in the kitchen and bath", "eq", True, 2),
             question="Is GFCI protection installed?"),
    "violations affecting habitability must be corrected in 14 days, not 30":
        dict(attribute="days_to_correct", dist=("lognormal", 20, 60), element="E5", fixable=True, unit="days",
             reading=_r("habitability violations corrected within 14 days", "le", 14, 2),
             question="How many days did corrections take?"),
    "no coop within 5 feet of a creek or drainage channel":
        dict(attribute="coop_distance_to_creek_ft", dist=("lognormal", 60, 300), element="E5", fixable=True, unit="feet",
             reading=_r("the coop is at least 5 feet from any creek or drainage channel", "ge", 5, 2),
             question="How far is the coop from a creek?"),
    "a traffic control plan stamped by a licensed engineer for any street closure":
        dict(attribute="stamped_traffic_plan", dist=("bernoulli", 0.5), element="E2", fixable=True, unit="",
             reading=_r("an engineer-stamped traffic control plan for any street closure", "eq", True, 2),
             question="Is a stamped traffic control plan included?"),
    "a 48-hour notice before the seal inspection":
        dict(attribute="seal_notice_hours", dist=("lognormal", 48, 120), element="E4", fixable=True, unit="hours",
             reading=_r("at least 48 hours' notice before the seal inspection", "ge", 48, 2),
             question="How much notice was given before the seal inspection?"),
    "proof of a local business address or registered agent":
        dict(attribute="local_address_proved", dist=("bernoulli", 0.75), element="E1", fixable=True, unit="",
             reading=_r("proof of a local business address or registered agent", "eq", True, 2),
             question="Is a local address or agent proved?"),
}


def _check_catalogue():
    from .domains import DOMAINS
    from .local_rules import CHOICE_VALUES
    for domain, preds in PREDICATES.items():
        ids = [p["pid"] for p in preds]
        assert len(ids) == len(set(ids)), domain
        elements = {e[0] for e in DOMAINS[domain]["elements"]}
        for p in preds:
            assert p["element"] in elements, (domain, p["pid"], p["element"])
            if p["kind"] == "delegated":
                key = "%s.%s" % (domain, p["choice"])
                assert key in CHOICE_VALUES and len(CHOICE_VALUES[key]) == len(p["readings"]), key


_check_catalogue()


# ------------------------------------------------------------ statute layer

def build_decision_function(domain: str, rng, marisol: bool) -> list[dict]:
    """statute_truth.decision_function: what the statute fixes, leaves to a
    standard, or delegates. A look-alike statute carries a different crisp
    constant so that retrieving the wrong state plants a wrong criterion."""
    out = []
    for p in PREDICATES[domain]:
        reading = p["readings"][0] if p["kind"] == "crisp" else None
        if p["kind"] == "crisp" and not marisol and p["alternates"]:
            reading = pick(rng, p["alternates"])
        out.append({
            "pred_id": p["pid"], "name": p["name"], "kind": p["kind"],
            "attribute": p["attribute"], "unit": p["unit"], "element_ref": p["element"],
            "fixable": p["fixable"], "question": p["question"],
            "statute_text": p["statute_text"] if marisol or p["kind"] != "crisp" else reading["label"],
            "standard": p["standard"], "choice_id": p["choice"], "bound": p.get("bound"),
            "statutory_reading": dict(reading) if reading else None,
            "backoffice": list(p["backoffice"]),
            "reading_space": [dict(label=r["label"], op=r["op"], value=r["value"],
                                   strictness=r["strictness"], weight=r["weight"])
                              for r in p["readings"]] if p["kind"] != "crisp" else [dict(reading)],
            "case_attribute_dist": list(p["dist"]),
        })
    return out


def decision_section_spec(df: list[dict]) -> str:
    """Appended to the statute's definition section content_spec so the renderer
    writes the tests the statute actually fixes, the standards it leaves open, and
    the delegations, without inventing numbers for the standards."""
    parts = []
    for p in df:
        if p["kind"] == "crisp":
            parts.append("state the exact test: %s" % p["statutory_reading"]["label"])
        elif p["kind"] == "standard":
            parts.append("use the standard '%s' for %s and state NO numeric threshold"
                         % (p["standard"], p["name"].lower()))
        elif p["kind"] == "capped":
            parts.append("state the OUTER BOUND on %s (%s) and make clear the local agency "
                         "may adopt any lesser requirement" % (p["name"].lower(), p["statute_text"]))
        else:
            parts.append("delegate %s to the local agency (open choice %s)" % (p["name"].lower(), p["choice_id"]))
    return " Decision criteria: " + "; ".join(parts) + "."


# ------------------------------------------------------------- local rules

def resolve_readings(stat: dict, rule: dict, rng, knobs: dict) -> dict[str, dict]:
    """local_rule_truth.readings: this jurisdiction's resolution of every predicate."""
    from .local_rules import CHOICE_VALUES
    spread = float(knobs.get("discretion_spread", 1.0))
    p_mis = float(knobs.get("p_misimplement", 0.05))
    domain = rule["domain"]
    catalogue = {p["pid"]: p for p in PREDICATES[domain]}
    readings: dict[str, dict] = {}
    for p in stat.get("decision_function", []):
        spec = catalogue[p["pred_id"]]
        why = ""
        if p["kind"] == "crisp":
            reading = dict(p["statutory_reading"])
            mis = bool(spec["alternates"]) and chance(rng, p_mis)
            if mis:
                reading = dict(pick(rng, spec["alternates"]))
                why = "mis-implemented: the local checklist restates the statutory test with a different constant"
            else:
                why = "the statute fixes this test; applied as written"
            reading["misimplemented"] = mis
        elif p["kind"] == "capped":
            space = p["reading_space"]
            cap = max(space, key=lambda r: r["weight"])
            if spread <= 0 or not chance(rng, min(1.0, spread)):
                reading = dict(cap)
                why = "sits on the statutory bound, the commonest choice (discretion_spread=%.2f)" % spread
            else:
                reading = dict(weighted(rng, [(r, r["weight"]) for r in space]))
                why = ("drawn from the bounded space: the statute caps this dimension, so the "
                       "jurisdiction chose the cap or a lesser requirement")
            reading["misimplemented"] = False
        elif p["kind"] == "standard":
            space = p["reading_space"]
            modal = max(space, key=lambda r: r["weight"])
            if spread <= 0 or not chance(rng, min(1.0, spread)):
                reading = dict(modal)
                why = "the modal reading of the standard (discretion_spread=%.2f)" % spread
            else:
                reading = dict(weighted(rng, [(r, r["weight"]) for r in space]))
                why = "drawn from the reading space of the standard '%s' with the planted weights" % p["standard"]
            reading["misimplemented"] = False
        else:
            key = "%s.%s" % (domain, p["choice_id"])
            values = CHOICE_VALUES[key]
            chosen = rule["choices"].get(p["choice_id"])
            idx = values.index(chosen) if chosen in values else 0
            reading = dict(p["reading_space"][idx])
            reading["misimplemented"] = False
            why = "follows the local rule's choice %s (option %d of %d)" % (p["choice_id"], idx + 1, len(values))
        reading.pop("weight", None)
        reading["why"] = why
        readings[p["pred_id"]] = reading
    # locally added, testable stricter standards
    qn = 0
    for s in rule.get("stricter_standards", []):
        spec = LOCAL_PREDICATES.get(s)
        if not spec:
            continue
        qn += 1
        r = dict(spec["reading"])
        r.pop("weight", None)
        r.update(misimplemented=False, why="added by the local rule as a stricter standard",
                 local_source=s)
        readings["Q%d" % qn] = r
    return readings


# ------------------------------------------------------------ process layer

def _local_predicate_entries(rule: dict) -> list[dict]:
    out, qn = [], 0
    for s in rule.get("stricter_standards", []):
        spec = LOCAL_PREDICATES.get(s)
        if not spec:
            continue
        qn += 1
        out.append(dict(pred_id="Q%d" % qn, name=s[0].upper() + s[1:], kind="local", attribute=spec["attribute"],
                        unit=spec["unit"], element_ref=spec["element"], fixable=spec["fixable"],
                        question=spec["question"], statute_text=None, standard=None, choice_id=None,
                        case_attribute_dist=list(spec["dist"]), backoffice=[], bound=None))
    return out


def attach(proc: dict, stat: dict, rule: dict, knobs: dict, seed: int = 0) -> None:
    """Attach every predicate to the activity that evaluates it and write
    process_truth.decision_model. Idempotent; no-op for version-1 worlds."""
    if int(knobs.get(VERSION_KEY, 1)) < 2:
        return
    acts = proc["activities"]
    by_el = {a["element_ref"]: a for a in acts if a["element_ref"]}
    decision = next((a for a in acts if proc["terminal_artifact"] in (a["artifacts_out"] or [])), None)
    if decision is None:
        decision = acts[-1]
    order = {a["id"]: i for i, a in enumerate(acts)}
    app = next((a for a in acts if a["element_ref"] and a["element_ref"].startswith("E")
                and a["actor"] == "applicant" and a["occasion"] in ("counter", "online")), acts[0])
    corr = next((a for a in acts if a["element_ref"] and any(
        e["element_id"] == a["element_ref"] and e["kind"] == "correction" for e in stat["skeleton"])), None)
    for a in acts:
        a["evaluates"] = []
        a["inputs_required"] = []
    entries = []
    readings = rule.get("readings", {})
    by_tag = {a.get("backoffice_tag"): a for a in acts if a.get("backoffice_tag")}
    for p in list(stat.get("decision_function", [])) + _local_predicate_entries(rule):
        host = by_el.get(p["element_ref"])
        # a back-office step that really performs the check takes the predicate
        # (a staff-only evaluation: its reading is disclosed only by staff documents)
        for tag in p.get("backoffice", ()) or ():
            if tag in by_tag:
                host = by_tag[tag]
                break
        fallback = host is None
        if fallback:
            host = decision
        # the correction that a failed fixable predicate triggers must point backwards
        back_to = None
        if p["fixable"]:
            if host.get("rework"):
                back_to = host["rework"]["back_to"]
            elif corr and order[corr["id"]] < order[host["id"]]:
                back_to = corr["id"]
            elif order[app["id"]] < order[host["id"]]:
                back_to = app["id"]
        host["evaluates"].append(p["pred_id"])
        if p["attribute"] not in host["inputs_required"]:
            host["inputs_required"].append(p["attribute"])
        r = readings.get(p["pred_id"])
        entries.append({
            "pred_id": p["pred_id"], "name": p["name"], "kind": p["kind"], "attribute": p["attribute"],
            "unit": p["unit"], "element_ref": p["element_ref"], "evaluated_at": host["id"],
            "evaluated_by": host["actor"], "evaluation_visibility": host["visibility"],
            "fallback_to_decision": fallback,
            "fixable": bool(p["fixable"] and back_to), "correction_back_to": back_to,
            "question": p["question"], "statute_text": p["statute_text"], "standard": p["standard"],
            "choice_id": p["choice_id"], "bound": p.get("bound"), "reading": r,
            "case_attribute_dist": p["case_attribute_dist"],
        })
    # expected pass rates under this jurisdiction's readings (analytic Monte Carlo,
    # its own stream; the simulated log is the observed counterpart)
    rng = sub_rng(int(seed), "decision_expect", proc["model_id"])
    n = 4000
    fails = {e["pred_id"]: 0 for e in entries}
    fatal = 0
    # The analytic expectation must describe the SAME applicant pool the
    # simulation will draw from, or `denial_rate` stops being the rate anyone
    # observes. Passed through rather than read from a global so this function
    # stays pure.
    p_ss = float(knobs.get("p_self_select", 0.0)) if knobs else 0.0
    for _ in range(n):
        attrs = sample_attributes(entries, rng, p_self_select=p_ss)
        any_fatal = False
        for e in entries:
            ok = evaluate(e, e["reading"], attrs)
            if not ok:
                fails[e["pred_id"]] += 1
                if not e["fixable"]:
                    any_fatal = True
        fatal += any_fatal
    for e in entries:
        e["expected_fail_rate"] = round(fails[e["pred_id"]] / n, 3)
    proc["decision_model"] = {
        "version": 2,
        "outcome_rule": "denied if any fatal predicate fails or a fixable failure survives the retry cap; "
                        "otherwise approved",
        "predicates": entries,
        "expected_fatal_fail_rate": round(fatal / n, 3),
        "strictness_index": round(sum(float((e["reading"] or {}).get("strictness", 1)) for e in entries
                                      if e["kind"] in ("standard", "delegated", "capped")) /
                                  max(1, sum(1 for e in entries if e["kind"] in ("standard", "delegated", "capped"))), 2),
        "why": ("%d predicates: %d crisp, %d standard, %d delegated, %d local; evaluated at %s"
                % (len(entries), sum(e["kind"] == "crisp" for e in entries), sum(e["kind"] == "standard" for e in entries),
                   sum(e["kind"] == "delegated" for e in entries),
                   sum(e["kind"] in ("local", "capped") for e in entries),
                   ", ".join(sorted({e["evaluated_at"] for e in entries})))),
    }
    # the legacy free parameter becomes a derived quantity under version 2
    proc["denial_rate"] = round(max(0.005, proc["decision_model"]["expected_fatal_fail_rate"]), 3)


# ------------------------------------------------------------- evaluation

def sample_attr(dist, rng):
    kind = dist[0]
    if kind == "normal":
        return round(rng.gauss(dist[1], dist[2]), 3)
    if kind == "lognormal":
        median, p90 = dist[1], dist[2]
        sigma = math.log(p90 / median) / 1.2816 if p90 > median else 0.1
        return round(median * math.exp(sigma * rng.gauss(0, 1)), 2)
    if kind == "bernoulli":
        return rng.random() < dist[1]
    if kind == "uniform":
        return round(dist[1] + (dist[2] - dist[1]) * rng.random(), 3)
    if kind == "choice":
        v = weighted(rng, [(val, w) for val, w in dist[1]])
        if isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(x, int) for x in v):
            return v[0] + rng.randrange(v[1] - v[0] + 1)
        return v
    raise ValueError("unknown attribute distribution %r" % (kind,))


# APPLICANT SELF-SELECTION.
#
# Sampling every case attribute independently of the rules manufactures
# applications that were hopeless before they were filed, and with several
# non-curable predicates per process the union of their failure probabilities
# runs away: the first development world reached a mean planted denial rate of
# 0.265 with a maximum of 0.933, against a real APR disapproval share of about
# 0.09% of 247,326 status-stated applications.
#
# The missing mechanism is not a smaller constant, it is selection at intake.
# People apply when they believe they qualify; counters and portals screen the
# obviously ineligible before an application is ever docketed; professionals file
# on behalf of applicants precisely to avoid a refusal. So a real applicant pool
# is heavily pre-filtered against the hard eligibility tests, which is why real
# denial rates are low even where the rules are strict.
#
# Modelled as rejection sampling against the FATAL predicates only: a
# self-selecting applicant redraws until no non-curable test fails. Fixable
# predicates are deliberately left alone — failing those is the everyday
# correction cycle, and it is a large part of what the benchmark measures.
SELF_SELECT_TRIES = 12


def sample_attributes(entries: list[dict], rng, *, p_self_select: float = 0.0) -> dict:
    """Case attributes. `p_self_select` is P(the applicant is pre-filtered).

    Defaults to 0.0 so that `outcome_model_version` 1 is byte-identical: the
    legacy path must consume exactly the draws it always did.
    """
    def draw():
        attrs: dict = {}
        for e in entries:
            if e["attribute"] not in attrs:
                attrs[e["attribute"]] = sample_attr(e["case_attribute_dist"], rng)
        # lottery-style readings draw on a uniform of their own
        attrs["_u"] = rng.random()
        return attrs

    attrs = draw()
    if not p_self_select or rng.random() >= p_self_select:
        return attrs
    fatal = [e for e in entries if not e.get("fixable")]
    if not fatal:
        return attrs
    for _ in range(SELF_SELECT_TRIES):
        if all(evaluate(e, e["reading"], attrs) for e in fatal):
            return attrs
        attrs = draw()
    # Twelve tries and still ineligible: this applicant really does not qualify,
    # and letting it through is the small residual of genuinely hopeless filings
    # that any real register contains.
    return attrs


def evaluate(entry: dict, reading: dict | None, attrs: dict) -> bool:
    if not reading:
        return True
    op, v = reading["op"], reading["value"]
    x = attrs.get(entry["attribute"])
    if op == "always":
        return True
    if op == "bern":
        return attrs.get("_u", 0.0) < float(v)
    if x is None:
        return True
    if op == "lt":
        return x < v
    if op == "le":
        return x <= v
    if op == "gt":
        return x > v
    if op == "ge":
        return x >= v
    if op == "eq":
        return x == v
    if op == "ne":
        return x != v
    if op == "in":
        return x in v
    if op == "not_in":
        return x not in v
    raise ValueError("unknown op %r" % op)


def cure(entry: dict, reading: dict, attrs: dict) -> None:
    """A correction makes the case satisfy the reading (used with p_cure)."""
    op, v = reading["op"], reading["value"]
    a = entry["attribute"]
    if op in ("lt",):
        attrs[a] = v - 1 if isinstance(v, int) else v - 0.01
    elif op in ("le", "ge", "eq", "gt"):
        attrs[a] = v if op != "gt" else (v + 1 if isinstance(v, int) else v + 0.01)
    elif op == "ne":
        attrs[a] = None if v is not None else 0
    elif op == "in":
        attrs[a] = v[0]
    elif op == "not_in":
        attrs[a] = "other"
    elif op == "bern":
        attrs["_u"] = 0.0


# ---------------------------------------------------------------- phrasing

def reading_phrase(entry: dict, reading: dict, fidelity: str, rng=None) -> str:
    if fidelity == "exact":
        return reading["label"]
    if fidelity == "approximate":
        return reading.get("approx") or reading["label"]
    if fidelity == "vague":
        if entry.get("standard"):
            return "the %s must meet the %s standard" % (entry["name"].lower(), entry["standard"])
        return entry["question"].rstrip("?").replace("?", "") + " is checked"
    # wrong: another reading from the space, or a perturbed constant
    space = [r for r in (entry.get("reading_space") or []) if r["label"] != reading["label"]]
    if space and rng is not None:
        return pick(rng, space)["label"]
    v = reading.get("value")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        factor = 1.5 if (rng is None or rng.random() < 0.5) else 0.6
        return reading["label"].replace(str(v), str(round(v * factor, 1) if isinstance(v, float) else int(v * factor)))
    return "no such requirement applies"


def _pred_entry(proc: dict, pid: str) -> dict | None:
    dm = proc.get("decision_model") or {}
    for e in dm.get("predicates", []):
        if e["pred_id"] == pid:
            return e
    return None


def _rev(ref, fidelity, value, **extra):
    d = {"ref": ref, "field": "criterion", "fidelity": fidelity, "value": value, "must_quote": False}
    d.update(extra)
    return d


# per-kind disclosure of readings: which predicates, at what fidelity
CRITERION_RULES = {
    # kind: (which predicates, fidelity, p_include)
    "program_page": ("eligibility", "approximate", 0.6),
    "checklist": ("inspection", "exact", 0.8),
    "form": ("eligibility", "exact", 0.4),
    "faq": ("any_public", "approximate", 0.5),
    "ordinance": ("delegated_local", "exact", 0.9),
    "staff_report": ("any", "exact", 0.5),
    "sop": ("any", "exact", 0.9),
    "third_party_guide": ("any_public", "approximate", 0.7),
    "council_minutes": ("any_public", "vague", 0.3),
    "news": ("any_public", "vague", 0.25),
    "audit_excerpt": ("any", "exact", 0.4),
    "generic_permits_page": ("eligibility", "vague", 0.2),
}


def _select(entries: list[dict], which: str) -> list[dict]:
    if which == "eligibility":
        return [e for e in entries if e["evaluated_by"] == "applicant" or e["kind"] == "crisp"
                or e["evaluated_at"] and e["element_ref"] in ("E1",)]
    if which == "inspection":
        return [e for e in entries if e["evaluation_visibility"] != "staff_only"
                and e["evaluated_by"] != "applicant"]
    if which == "delegated_local":
        return [e for e in entries if e["kind"] in ("delegated", "local", "crisp", "capped")]
    if which == "any_public":
        return [e for e in entries if e["evaluation_visibility"] != "staff_only"]
    return list(entries)


def criterion_reveals(kind: str, proc: dict, rule: dict, rng, knobs: dict, stale: bool = False) -> list[dict]:
    """Criterion (reading) reveals for one artifact kind. Returns [] for
    version-1 worlds or kinds that never state criteria."""
    dm = proc.get("decision_model")
    if not dm or kind not in CRITERION_RULES:
        return []
    which, fidelity, p_inc = CRITERION_RULES[kind]
    out = []
    p_wrong = float(knobs.get("p_wrong_fact_third_party", 0.15))
    for e in _select(dm["predicates"], which):
        if not e["reading"] or not chance(rng, p_inc):
            continue
        fid = fidelity
        if kind == "third_party_guide" and chance(rng, p_wrong):
            fid = "wrong"
        if kind == "ordinance" and e["kind"] == "standard":
            fid = "vague"          # an ordinance restates the standard, rarely the number
        value = reading_phrase(e, e["reading"], fid, rng)
        out.append(_rev(e["pred_id"], fid, value, criterion_kind=e["kind"],
                        evaluated_at=e["evaluated_at"], must_quote=(fid == "exact" and kind in ("checklist", "sop"))))
    return out


def statute_criterion_reveals(stat: dict) -> list[dict]:
    """State-level reveals for the statute text / bill analysis: the crisp test
    exact, the standard's phrase only, the delegation as such."""
    out = []
    for p in stat.get("decision_function", []):
        if p["kind"] == "crisp":
            out.append(_rev(p["pred_id"], "exact", p["statutory_reading"]["label"], level="statute",
                            criterion_kind="crisp", must_quote=True))
        elif p["kind"] == "standard":
            out.append(_rev(p["pred_id"], "vague", "the statute requires that %s meet the '%s' standard "
                            "and states no number" % (p["name"].lower(), p["standard"]),
                            level="statute", criterion_kind="standard"))
        elif p["kind"] == "capped":
            # The BOUND is in the statute and therefore always public; which value
            # the jurisdiction chose under it is not, so this is approximate, not
            # exact, about the local rule.
            out.append(_rev(p["pred_id"], "approximate",
                            "the statute bounds %s: %s. The local agency may adopt any lesser "
                            "requirement, and this section does not say which it chose"
                            % (p["name"].lower(), p["statute_text"]),
                            level="statute", criterion_kind="capped", must_quote=True))
        else:
            out.append(_rev(p["pred_id"], "vague", "the statute leaves %s to the local agency"
                            % p["name"].lower(), level="statute", criterion_kind="delegated"))
    return out


def persona_failed_criteria(proc: dict, rec: dict) -> list[dict]:
    """The predicates this applicant failed, for the OP's story."""
    out = []
    for pid, res in (rec.get("predicate_results") or {}).items():
        if res.get("passed_ever") is False or res.get("failed_first"):
            e = _pred_entry(proc, pid)
            if e and e["reading"] and e["evaluation_visibility"] != "staff_only":
                out.append({"pred_id": pid, "name": e["name"], "reading": e["reading"], "entry": e,
                            "resolved": bool(res.get("passed_ever"))})
    return out


def hidden_criteria(proc: dict, revealed: set[str], law_restating: bool) -> list[str]:
    """Predicate ids an artifact of this kind must not state: readings of
    standards applied at staff-only steps, unless the kind restates public law
    and the reading is in the ordinance (delegated/local)."""
    dm = proc.get("decision_model")
    if not dm:
        return []
    out = []
    for e in dm["predicates"]:
        if e["pred_id"] in revealed:
            continue
        if e["evaluation_visibility"] == "staff_only" and e["kind"] == "standard":
            out.append(e["pred_id"])
        elif e["evaluation_visibility"] == "staff_only" and not law_restating and e["kind"] in ("delegated", "local", "capped"):
            out.append(e["pred_id"])
    return out


# ------------------------------------------------------------------ ceiling

RANK = {"exact": 3, "approximate": 2, "vague": 1, "wrong": 0}
NAME = {3: "exact", 2: "approximate", 1: "vague", 0: "wrong"}


def decision_ceiling(proc: dict, specs_about: list[dict]) -> dict | None:
    dm = proc.get("decision_model")
    if not dm:
        return None
    mid = proc["model_id"]
    best: dict[str, tuple[int, str, str]] = {}
    for s in specs_about:
        for r in s.get("reveals", []):
            if r.get("field") != "criterion":
                continue
            if r.get("process") and r["process"] != mid:
                continue
            fid = RANK[r["fidelity"]]
            cur = best.get(r["ref"])
            if cur is None or fid > cur[0]:
                best[r["ref"]] = (fid, s["artifact_id"], str(r["value"])[:160])
    buckets = {"recoverable_exact": [], "recoverable_approx": [], "only_wrong": [], "hidden": []}
    per = {}
    for e in dm["predicates"]:
        b = best.get(e["pred_id"])
        if b is None:
            key = "hidden"
        elif b[0] == 3:
            key = "recoverable_exact"
        elif b[0] >= 1:
            key = "recoverable_approx"
        else:
            key = "only_wrong"
        buckets[key].append(e["pred_id"])
        per[e["pred_id"]] = {"kind": e["kind"], "fidelity": NAME[b[0]] if b else "hidden",
                             "artifact": b[1] if b else None, "reading": (e["reading"] or {}).get("label")}
    n = len(dm["predicates"])
    by_kind = {}
    for e in dm["predicates"]:
        k = by_kind.setdefault(e["kind"], {"total": 0, "exact": 0, "any": 0})
        k["total"] += 1
        f = per[e["pred_id"]]["fidelity"]
        k["exact"] += f == "exact"
        k["any"] += f in ("exact", "approximate", "vague")
    return {
        "predicates_total": n,
        **buckets,
        "per_predicate": per,
        "by_kind": by_kind,
        "strictness_index": dm["strictness_index"],
        "coverage": {"exact": round(len(buckets["recoverable_exact"]) / n, 3) if n else None,
                     "any": round((n - len(buckets["hidden"]) - len(buckets["only_wrong"])) / n, 3) if n else None},
    }
