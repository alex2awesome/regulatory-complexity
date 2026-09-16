"""statute_truth: the state-level mandated skeleton and the choices it leaves open.

Shape varies deliberately (DESIGN: "some prescribe nearly the whole process,
some only 3 elements"):

* ``prescriptive`` -- 7-8 mandated elements incl. shot clocks and an appeal; the
  local rule has little room (S02, S03, S06, S07, S08).
* ``mid`` -- 6-7 elements, one or two big open choices (S04, S10, S11, S12).
* ``minimal`` -- 5 listed elements of which 2 are "may"; 3 mandated, AB 2533-like
  (S01, S05, S09): the process is mostly *local* invention.

Corvane statutes are look-alikes: same domain, different cite, 1-2 elements
different, so an agent that retrieves the wrong state gets a nearly-right graph.
"""
from __future__ import annotations

from .domains import DOMAINS, DOMAIN_ORDER, stat_id_for
from .rng import chance, pick, sub_rng

LETTERS = "abcdefghijklmnopqrstuvwxyz"

# element kind -> section kind (DESIGN section kind enum)
SEC_KIND = {
    "fee": "fee", "fee_waiver": "fee", "appeal": "appeal", "record": "record",
    "timeline": "timeline", "public_hearing": "mandate",
}

CORVANE_CODES = {
    "unpermitted_unit_amnesty": ("Corvane Rev. Stat. § 12-408", "Nonconforming Dwelling Unit Certification Law"),
    "str_registration": ("Corvane Rev. Stat. § 40-215", "Transient Rental Licensing Law"),
    "sidewalk_vending": ("Corvane Rev. Stat. § 31-902", "Public Way Vending Law"),
    "tree_removal": ("Corvane Rev. Stat. § 55-110", "Landmark Tree Protection Law"),
    "home_business": ("Corvane Rev. Stat. § 31-455", "Residential Enterprise Registration Law"),
    "mobile_food": ("Corvane Rev. Stat. § 22-1140", "Itinerant Food Service Law"),
    "solar_auto_permit": ("Corvane Rev. Stat. § 19-660", "Expedited Solar Permitting Law"),
    "rental_inspection": ("Corvane Rev. Stat. § 27-330", "Rental Dwelling Certification Law"),
    "backyard_hens": ("Corvane Rev. Stat. § 6-712", "Residential Poultry Law"),
    "special_event": ("Corvane Rev. Stat. § 31-1201", "Public Gathering Permit Law"),
    "well_permit": ("Corvane Rev. Stat. § 47-205", "Private Water Well Law"),
    "contractor_registration": ("Corvane Rev. Stat. § 14-880", "Trade Contractor Registry Law"),
}


def _element(e: tuple, anchor: str) -> dict:
    eid, kind, name, role, optional, clock, must_precede = e
    return {
        "element_id": eid, "kind": kind, "name": name, "optional": optional,
        "shot_clock_days": clock, "actor_role": role,
        "must_precede": list(must_precede), "text_anchor": anchor,
    }


def _element_spec(dom: dict, el: dict) -> str:
    """content_spec detailed enough for a renderer to write statutory prose."""
    verb = "may" if el["optional"] else "shall"
    who = {"applicant": "the applicant", "agency": "the local agency",
           "third_party": "a qualified third party retained by the applicant",
           "public": "the public"}[el["actor_role"]]
    s = "Write the subdivision that %s: %s %s. " % (
        "authorizes" if el["optional"] else "mandates", who, el["name"].lower())
    if el["shot_clock_days"]:
        if el["actor_role"] == "applicant":
            s += ("State the deadline: %d days (a filing/compliance deadline on the applicant, "
                  "not on the agency). " % el["shot_clock_days"])
        else:
            s += ("State the shot clock: the agency shall act within %d days of a complete "
                  "submittal, and say what happens on inaction (deemed complete / deemed "
                  "approved / the applicant may proceed). " % el["shot_clock_days"])
    if el["must_precede"]:
        s += "State the ordering: this step precedes %s. " % ", ".join(el["must_precede"])
    if el["kind"] in ("fee", "fee_waiver"):
        s += "Use the cost-recovery limitation language; do not state a dollar amount (that is a local choice). "
    if el["kind"] == "checklist_publication":
        s += "Require publication on the agency's internet website and in writing at the public counter. "
    if el["kind"] == "third_party_option":
        s += "Use 'may' and preserve confidentiality where the domain calls for it. "
    if el["kind"] == "appeal":
        s += "Require an impartial decisionmaker and state the filing period. "
    s += "Vocabulary: %s." % ", ".join(t for t, _ in dom["defs"])
    return s


def build_statute(domain: str, seed: int, state: str = "Marisol") -> dict:
    dom = DOMAINS[domain]
    rng = sub_rng(seed, "statute", state, domain)
    marisol = state == "Marisol"
    elements = [list(e) for e in dom["elements"]]
    differences: list[str] = []

    if not marisol:
        # 1-2 element differences from the Marisol statute.
        drop_opt = [i for i, e in enumerate(elements) if e[4]]
        if drop_opt and len(elements) > 5 and chance(rng, 0.7):
            i = pick(rng, drop_opt)
            differences.append("no %s element (Marisol has one)" % elements[i][1])
            elements.pop(i)
        clocked = [i for i, e in enumerate(elements) if e[5]]
        if clocked:
            i = pick(rng, clocked)
            old = elements[i][5]
            new = max(5, int(old * pick(rng, [0.5, 0.67, 1.5, 2.0])))
            elements[i][5] = new
            differences.append("%s clock is %d days, not %d" % (elements[i][0], new, old))
        if chance(rng, 0.45):
            add = pick(rng, [
                ("X1", "public_hearing", "Public hearing before the local legislative body on a denial", "public", False, None, ()),
                ("X1", "notice", "Published notice of the application in a newspaper of general circulation", "agency", False, 14, ()),
                ("X1", "record", "Quarterly report of permits issued to the state agency", "agency", False, None, ()),
            ])
            elements.append(list(add))
            differences.append("adds a %s element (%s)" % (add[1], add[2]))

    year = int(dom["bill"].split("(")[1][:4])
    if not marisol:
        year += pick(rng, [-1, 0, 1])
    enacted = "%d-09-%02d" % (year, 8 + rng.randrange(20))
    operative = "%d-01-01" % (year + 1)

    if marisol:
        cite, title = dom["cite"], dom["statute_title"]
        bill = dom["bill"]
        agency = dom["state_agency"]
        committee = "Assembly Committee on Local Government"
    else:
        cite, title = CORVANE_CODES[domain]
        bill = "H.B. %d (%d)" % (1100 + rng.randrange(800), year)
        agency = pick(rng, ["Corvane Department of Community Affairs", "Corvane Health Division",
                            "Corvane Water Resources Department"])
        committee = "Senate Committee on Government Operations"

    # ---- sections -------------------------------------------------------
    sections = [
        {"sec": "(a)", "kind": "purpose", "mandated_element": None,
         "content_spec": "Findings and declarations. " + dom["purpose_spec"] +
                         " Close with a declaration that this is a matter of statewide concern."},
        {"sec": "(b)", "kind": "definition", "mandated_element": None,
         "content_spec": "Definitions, one per defined term: " +
                         "; ".join("'%s' means %s" % (t, d) for t, d in dom["defs"]) + "."},
    ]
    skeleton = []
    li = 2
    for e in elements:
        letter = LETTERS[li]
        li += 1
        el = _element(tuple(e), "(%s)%s" % (letter, "(2)" if e[5] else ""))
        skeleton.append(el)
        sections.append({
            "sec": "(%s)" % letter, "kind": SEC_KIND.get(el["kind"], "option" if el["optional"] else "mandate"),
            "mandated_element": el["element_id"], "content_spec": _element_spec(dom, el),
        })
    sections.append({
        "sec": "(%s)" % LETTERS[li], "kind": "preemption", "mandated_element": None,
        "content_spec": ("Applicability and preemption: %s A local agency may impose additional "
                         "requirements only to the extent they do not conflict with this section, and "
                         "shall not impose a requirement that defeats its purpose. Note that the section "
                         "is silent on which department administers the program and on the amount of any "
                         "fee." % dom["applicability"]),
    })
    li += 1
    sections.append({
        "sec": "(%s)" % LETTERS[li], "kind": "record", "mandated_element": None,
        "content_spec": ("Reporting and records: the local agency shall retain records of applications "
                         "and decisions for at least three years and shall report aggregate counts to %s "
                         "on request." % agency),
    })

    choices = [{"choice_id": c[0], "kind": c[1], "what": c[2], "constraint": c[3]} for c in dom["choices"]]
    if not marisol and chance(rng, 0.5) and len(choices) > 3:
        removed = choices.pop(rng.randrange(len(choices)))
        differences.append("does not leave open: %s" % removed["what"])

    stat_id = stat_id_for(domain) if marisol else "C%s" % stat_id_for(domain)[1:]
    out = {
        "stat_id": stat_id,
        "state": state,
        "cite": cite,
        "title": title,
        "domain": domain,
        "shape": dom["shape"],
        "bill": bill,
        "enacted": enacted,
        "operative": operative,
        "legislative_history": "(Added by Stats. %d, Ch. %d, Sec. %d. Operative %s.)"
                               % (year, 100 + rng.randrange(700), 1 + rng.randrange(40), operative),
        "committee": committee,
        "state_agency": agency,
        "applicability": dom["applicability"],
        "text": "<rendered in Wave 2 from `sections`; the generator emits the section outline only>",
        "sections": sections,
        "skeleton": skeleton,
        "open_choices": choices,
        "version": 1,
    }
    if not marisol:
        out["lookalike_of"] = stat_id_for(domain)
        out["differences_from_lookalike"] = differences
    return out


def build_statutes(world: dict) -> dict[str, dict]:
    seed = world["seed"]
    out: dict[str, dict] = {}
    for domain in world.get("domains", DOMAIN_ORDER):
        s = build_statute(domain, seed, "Marisol")
        out[s["stat_id"]] = s
    if world["knobs"]["neighbor_state"]:
        needed = sorted({i["domain"] for i in world["implementations"] if not i["target"]})
        for domain in needed:
            s = build_statute(domain, seed, "Corvane")
            out[s["stat_id"]] = s
    return out
