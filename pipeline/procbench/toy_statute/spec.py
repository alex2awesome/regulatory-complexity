"""Public specification of the toy statute world (no ground truth here).

Everything in this module is knowledge that the Bayesian model, the LLM
baseline and the generator legitimately share: the statute text, the decision
model read from it, the process-step catalog, and the menu of candidate
process structures (the hypothesis space for the vague d-step).
"""

from __future__ import annotations

STATUTE_TEXT = """Backyard Hen Keeping Act (synthetic).
Sec. 1. A resident of a single-family dwelling may keep up to six hens after obtaining a permit from the local permitting authority.
Sec. 2. The applicant shall submit an application, together with a site plan showing the location of the coop and its distance to property lines.
Sec. 3. Before issuing a permit, the authority shall determine that the coop will not create a nuisance to adjoining properties.
Sec. 4. The authority shall issue or deny the permit within 30 days after receiving a complete application.
Sec. 5. The authority may charge a reasonable application fee."""

DEADLINE_DAYS = 30  # Sec. 4: complete application -> decision
COUNTERFACTUAL_DESIGN = "S1"  # Sec. 3 made concrete: "the authority shall review the site plan"

D_STEPS = [
    {"id": "D1", "name": "application", "clause": "Sec. 2 (+ Sec. 4 'complete')", "tag": "concrete",
     "note": "completeness check implied by Sec. 4; fee amount vague (Sec. 5)"},
    {"id": "D2", "name": "nuisance determination", "clause": "Sec. 3", "tag": "vague",
     "note": "procedure unspecified"},
    {"id": "D3", "name": "issue or deny", "clause": "Sec. 4", "tag": "concrete",
     "note": "30-day deadline from complete application"},
]

# Elapsed-time p-steps (order fixes parameter layout).
DAY_STEPS = [
    "completeness_check", "correction", "neighbor_notice", "comment_period",
    "desk_review", "hearing", "site_inspection", "decision_issue",
]
# Applicant-hour p-steps.
HOUR_STEPS = ["prepare", "correction", "site_inspection", "hearing"]
# Fee-bearing p-steps and the fee item they carry.
FEE_STEPS = {"prepare": "application", "neighbor_notice": "notice", "site_inspection": "inspection"}
# Agency steps whose duration scales with the town speed factor.
TOWN_SCALED = {"completeness_check", "neighbor_notice", "desk_review", "hearing",
               "site_inspection", "decision_issue"}
# Steps an agency web page may list.
LISTABLE = ["completeness_check", "neighbor_notice", "comment_period", "desk_review",
            "hearing", "site_inspection", "decision_issue"]
# Steps an applicant report may mention (applicant-visible, case-varying or structural).
MENTIONABLE = ["correction", "neighbor_notice", "site_inspection", "hearing"]
# Events an applicant can time.
TIMEABLE_EVENTS = ["submitted", "told_incomplete", "hearing", "inspection", "decision"]

P_STEPS = {
    "prepare":            {"d_steps": ["D1"], "actor": "applicant", "days": False, "hours": True,  "fee": "application", "applicant_facing": True, "events": []},
    "completeness_check": {"d_steps": ["D1"], "actor": "agency",    "days": True,  "hours": False, "fee": None, "applicant_facing": False, "events": []},  # emits told_incomplete / app_complete (D1 skeleton logic in chain)
    "correction":         {"d_steps": ["D1"], "actor": "applicant", "days": True,  "hours": True,  "fee": None, "applicant_facing": True, "events": []},
    "neighbor_notice":    {"d_steps": ["D2"], "actor": "agency",    "days": True,  "hours": False, "fee": "notice", "applicant_facing": False, "events": ["notice_mailed"]},
    "comment_period":     {"d_steps": ["D2"], "actor": "neighbors", "days": True,  "hours": False, "fee": None, "applicant_facing": False, "events": []},
    "desk_review":        {"d_steps": ["D2"], "actor": "agency",    "days": True,  "hours": False, "fee": None, "applicant_facing": False, "events": ["review_complete"]},
    "hearing":            {"d_steps": ["D2"], "actor": "board",     "days": True,  "hours": True,  "fee": None, "applicant_facing": True, "events": ["hearing"]},
    "site_inspection":    {"d_steps": ["D2"], "actor": "inspector", "days": True,  "hours": True,  "fee": "inspection", "applicant_facing": True, "events": ["inspection"]},
    "decision_issue":     {"d_steps": ["D3"], "actor": "agency",    "days": True,  "hours": False, "fee": None, "applicant_facing": False, "events": ["decision"]},
}
# Which decision step the vague middle refines (the design space varies this step's refinement),
# and which step issues the final decision when it is not shared.
VAGUE_DSTEP = "D2"
DECISION_STEP = "decision_issue"
# Applicant-report mention -> the event it lets the applicant time (None: not timeable).
MENTION_EVENT = {"correction": "told_incomplete", "hearing": "hearing", "site_inspection": "inspection", "neighbor_notice": None}
# Admin milestone field -> event name in the chain.
ADMIN_MILESTONES = {"deemed_complete": "app_complete", "inspection": "inspection", "hearing": "hearing"}
# Canonical order of events that can be timed (ties broken by this order).
EVENT_ORDER = ["submitted", "told_incomplete", "app_complete", "notice_mailed", "review_complete", "hearing", "inspection", "decision"]

# Refinement menu: D2 procedure and whether the decision is issued at the inspection.
STRUCTURES = {
    "S1": {"d2": ["desk_review"], "shared_decision": False},
    "S2": {"d2": ["desk_review", "site_inspection"], "shared_decision": False},
    "S3": {"d2": ["desk_review", "site_inspection"], "shared_decision": True},
    "S4": {"d2": ["neighbor_notice", "comment_period", "desk_review", "hearing?"], "shared_decision": False},
    "S5": {"d2": ["neighbor_notice", "comment_period", "desk_review", "hearing?", "site_inspection"], "shared_decision": False},
    "S6": {"d2": ["neighbor_notice", "comment_period", "desk_review", "hearing?", "site_inspection"], "shared_decision": True},
}
STRUCTURE_IDS = list(STRUCTURES)
D2_REFINEMENT = {"S1": "R1_desk", "S2": "R2_desk_inspection", "S3": "R2_desk_inspection",
                 "S4": "R3_notice_desk", "S5": "R4_notice_desk_inspection", "S6": "R4_notice_desk_inspection"}
STRUCTURE_TEXT = {
    "S1": "D2 = desk review of the site plan; D3 = separate decision issuance.",
    "S2": "D2 = desk review, then site inspection; D3 = separate decision issuance after the inspection.",
    "S3": "D2 = desk review, then site inspection; D3 = decision issued at the inspection (the inspection serves D2 and D3).",
    "S4": "D2 = neighbour notice, a neighbour comment period, desk review, and a hearing only if a neighbour objects; D3 = separate decision issuance.",
    "S5": "D2 = as S4, then a site inspection; D3 = separate decision issuance.",
    "S6": "D2 = as S4, then a site inspection; D3 = decision issued at the inspection.",
}
_MENU6_TEXT = dict(STRUCTURE_TEXT)
MAX_LOOPS = 4  # correction loops per case, truncated

# ---- Compositional design space (round 4, docs/2026-09-29-toy-statute-round4-plan.md) ----
# Every non-empty subset of the three safeguards {desk review, site inspection,
# neighbour notice->comment->(hearing)} in canonical serial order, with the decision
# issued at the inspection as a variant wherever an inspection exists. S1-S6 keep their
# ids; S7-S11 are the designs the hand-written menu left out. Default stays the 6-menu
# so earlier rounds reproduce; call use_design_space("full") before building a Model.
_MENU6 = dict(STRUCTURES)
_FULL = dict(_MENU6)
_FULL.update({
    "S7": {"d2": ["site_inspection"], "shared_decision": False},
    "S8": {"d2": ["site_inspection"], "shared_decision": True},
    "S9": {"d2": ["neighbor_notice", "comment_period", "hearing?"], "shared_decision": False},
    "S10": {"d2": ["neighbor_notice", "comment_period", "hearing?", "site_inspection"], "shared_decision": False},
    "S11": {"d2": ["neighbor_notice", "comment_period", "hearing?", "site_inspection"], "shared_decision": True},
})
_FULL_TEXT = {
    "S7": "D2 = site inspection only (no desk review); D3 = separate decision issuance.",
    "S8": "D2 = site inspection only; D3 = decision issued at the inspection.",
    "S9": "D2 = neighbour notice, comment period, and a hearing only if a neighbour objects (no desk review, no inspection); D3 = separate decision issuance.",
    "S10": "D2 = neighbour notice, comment period, hearing only on objection, then site inspection (no desk review); D3 = separate decision issuance.",
    "S11": "D2 = as S10; D3 = decision issued at the inspection.",
}
_FULL_REF = {"S7": "R5_inspection", "S8": "R5_inspection", "S9": "R6_notice",
             "S10": "R7_notice_inspection", "S11": "R7_notice_inspection"}
DESIGN_SPACE = "menu6"
STATUTE_ID = "hens_v1"
# Snapshot of the hen catalog so use_design_space() fully restores it after load_package().
import copy as _copy2
_HEN_SNAPSHOT = {k: _copy2.deepcopy(globals()[k]) for k in
                 ("STATUTE_TEXT", "DEADLINE_DAYS", "D_STEPS", "P_STEPS", "DAY_STEPS", "HOUR_STEPS", "FEE_STEPS",
                  "TOWN_SCALED", "LISTABLE", "MENTIONABLE", "TIMEABLE_EVENTS", "VAGUE_DSTEP", "DECISION_STEP",
                  "MENTION_EVENT", "ADMIN_MILESTONES", "EVENT_ORDER")}


def _restore_hen_catalog():
    global STATUTE_TEXT, DEADLINE_DAYS, VAGUE_DSTEP, DECISION_STEP, STATUTE_ID, COUNTERFACTUAL_DESIGN
    COUNTERFACTUAL_DESIGN = "S1"
    h = _HEN_SNAPSHOT
    STATUTE_TEXT, DEADLINE_DAYS = h["STATUTE_TEXT"], h["DEADLINE_DAYS"]
    VAGUE_DSTEP, DECISION_STEP, STATUTE_ID = h["VAGUE_DSTEP"], h["DECISION_STEP"], "hens_v1"
    D_STEPS[:] = _copy2.deepcopy(h["D_STEPS"])
    P_STEPS.clear(); P_STEPS.update(_copy2.deepcopy(h["P_STEPS"]))
    DAY_STEPS[:] = list(h["DAY_STEPS"]); HOUR_STEPS[:] = list(h["HOUR_STEPS"])
    FEE_STEPS.clear(); FEE_STEPS.update(h["FEE_STEPS"])
    TOWN_SCALED.clear(); TOWN_SCALED.update(h["TOWN_SCALED"])
    LISTABLE[:] = list(h["LISTABLE"]); MENTIONABLE[:] = list(h["MENTIONABLE"])
    TIMEABLE_EVENTS[:] = list(h["TIMEABLE_EVENTS"])
    MENTION_EVENT.clear(); MENTION_EVENT.update(h["MENTION_EVENT"])
    ADMIN_MILESTONES.clear(); ADMIN_MILESTONES.update(h["ADMIN_MILESTONES"])
    EVENT_ORDER[:] = list(h["EVENT_ORDER"])


def load_package(pkg: dict):
    """Replace the module-level statute with a statute package (see
    runs/toy_statute2_20260929/hen_package_example.json for the format). Mutates the
    same module-level names use_design_space() does, so all consumers see the new statute.
    The D1 skeleton (prepare -> completeness_check with correction loops) is fixed."""
    global STATUTE_TEXT, DEADLINE_DAYS, VAGUE_DSTEP, DECISION_STEP, DESIGN_SPACE, STATUTE_ID, COUNTERFACTUAL_DESIGN
    STATUTE_ID = pkg.get("statute_id", "package")
    # the "make the vague step concrete" intervention is statute-specific; absent -> not computed
    COUNTERFACTUAL_DESIGN = pkg.get("counterfactual_design", "S1" if "S1" in pkg["design_space"] else None)
    STATUTE_TEXT = pkg["text"]
    DEADLINE_DAYS = pkg.get("deadline_days", DEADLINE_DAYS)
    D_STEPS[:] = list(pkg["d_steps"])
    P_STEPS.clear(); P_STEPS.update(pkg["p_steps"])
    DAY_STEPS[:] = list(pkg["day_steps"]); HOUR_STEPS[:] = list(pkg["hour_steps"])
    FEE_STEPS.clear(); FEE_STEPS.update(pkg["fee_steps"])
    TOWN_SCALED.clear(); TOWN_SCALED.update(pkg["town_scaled"])
    LISTABLE[:] = list(pkg["listable"]); MENTIONABLE[:] = list(pkg["mentionable"])
    TIMEABLE_EVENTS[:] = list(pkg["timeable_events"])
    VAGUE_DSTEP = pkg.get("vague_dstep", VAGUE_DSTEP)
    DECISION_STEP = pkg.get("decision_step", DECISION_STEP)
    MENTION_EVENT.clear(); MENTION_EVENT.update(pkg.get("mention_event", MENTION_EVENT))
    ADMIN_MILESTONES.clear(); ADMIN_MILESTONES.update(pkg.get("admin_milestones", ADMIN_MILESTONES))
    EVENT_ORDER[:] = list(pkg.get("event_order", EVENT_ORDER))
    STRUCTURES.clear(); STRUCTURES.update({k: dict(v) for k, v in pkg["design_space"].items()})
    STRUCTURE_IDS[:] = list(STRUCTURES)
    STRUCTURE_TEXT.clear(); STRUCTURE_TEXT.update(pkg.get("design_text", {}))
    D2_REFINEMENT.clear()
    for k, v in STRUCTURES.items():  # refinement label = the set of vague-middle steps, ignoring the shared flag
        D2_REFINEMENT[k] = "R_" + "+".join(x.rstrip("?") for x in v["d2"])
    DESIGN_SPACE = f"package:{STATUTE_ID}"


def use_design_space(name: str):
    """Switch the module-level design space in place ("menu6" or "full")."""
    global DESIGN_SPACE
    assert name in ("menu6", "full"), name
    _restore_hen_catalog()   # a package may have replaced the catalog; the hen design spaces need the hen catalog
    STRUCTURES.clear()
    STRUCTURES.update(_FULL if name == "full" else _MENU6)
    STRUCTURE_IDS[:] = list(STRUCTURES)
    D2_REFINEMENT.clear()
    D2_REFINEMENT.update({"S1": "R1_desk", "S2": "R2_desk_inspection", "S3": "R2_desk_inspection",
                          "S4": "R3_notice_desk", "S5": "R4_notice_desk_inspection", "S6": "R4_notice_desk_inspection"})
    STRUCTURE_TEXT.clear()
    STRUCTURE_TEXT.update(_MENU6_TEXT)
    if name == "full":
        D2_REFINEMENT.update(_FULL_REF)
        STRUCTURE_TEXT.update(_FULL_TEXT)
    DESIGN_SPACE = name


def hearing_possible(s: str) -> bool:
    return "hearing?" in STRUCTURES[s]["d2"]


def has_step(s: str, step: str) -> bool:
    d2 = [x.rstrip("?") for x in STRUCTURES[s]["d2"]]
    if step in d2:
        return True
    if step == DECISION_STEP:
        return not STRUCTURES[s]["shared_decision"]
    # steps outside the vague middle and the decision step belong to the fixed D1 skeleton
    # (prepare, completeness_check, correction, plus any catalog step that serves only D1)
    return step in D1_STEPS()


def D1_STEPS():
    """Catalog steps that every case performs before the vague middle (the fixed skeleton):
    prepare, completeness_check, correction and any other step serving only D1."""
    out = ["prepare", "completeness_check", "correction"]
    for k, v in P_STEPS.items():
        if k not in out and v.get("d_steps") == ["D1"] and k not in DAY_STEPS:
            out.append(k)   # e.g. a one-time course: hours/fee only, no elapsed-time slot
    return out


def execution_counts(s, k, h):
    """Executions by catalog step; k/h may be actual counts or expectations."""
    return {st: (k + 1 if st == "completeness_check" else
                 k if st == "correction" else
                 h if st == "hearing" and hearing_possible(s) else
                 0 if st == "hearing" else float(has_step(s, st)))
            for st in P_STEPS}


def fee_items(s):
    """One-time schedule items attached to steps in this design (not per loop).

    Current catalogs have no conditional hearing/correction fee; reject one
    until its charging rule is specified instead of silently charging all cases.
    """
    if any(st in ("hearing", "correction") for st in FEE_STEPS):
        raise ValueError("conditional/repeated-step fees need an explicit charging rule")
    return tuple(dict.fromkeys(item for st, item in FEE_STEPS.items() if has_step(s, st)))


def combos(s: str):
    """Case paths (k correction loops, h hearing) possible under structure s."""
    hs = (0, 1) if hearing_possible(s) else (0,)
    return [(k, h) for k in range(MAX_LOOPS + 1) for h in hs]


def chain(s: str, k: int, h: int):
    """Ordered elapsed-time steps for one case, with events that fire at step ends.

    Returns list of (day_step, [events]). 'submitted' fires at time 0 (before
    the first step).
    """
    seq = [("completeness_check", ["told_incomplete"] if k >= 1 else ["app_complete"])]
    for j in range(k):
        seq.append(("correction", []))
        seq.append(("completeness_check", ["app_complete"] if j == k - 1 else []))
    for raw in STRUCTURES[s]["d2"]:
        step = raw.rstrip("?")
        if raw.endswith("?") and not h:
            continue
        seq.append((step, [e for e in P_STEPS[step].get("events", []) if e != "decision"]))
    if STRUCTURES[s]["shared_decision"]:
        seq[-1][1].append("decision")  # the last vague-middle step also issues the decision
    else:
        seq.append((DECISION_STEP, list(P_STEPS[DECISION_STEP].get("events", ["decision"]))))
    return seq


def event_positions(seq):
    """Map event -> number of steps completed when it fires."""
    pos = {"submitted": 0}
    for i, (_, evs) in enumerate(seq):
        for e in evs:
            pos[e] = i + 1
    return pos


def segment_counts(seq, e1: str, e2: str):
    """Day-step count vector for the steps between events e1 and e2, or None."""
    pos = event_positions(seq)
    if e1 not in pos or e2 not in pos or pos[e2] < pos[e1]:
        return None
    counts = [0] * len(DAY_STEPS)
    for step, _ in seq[pos[e1]:pos[e2]]:
        counts[DAY_STEPS.index(step)] += 1
    return tuple(counts)


def hour_counts(s: str, k: int, h: int):
    """Applicant-hour step executions for one case path, from the catalog: prepare once,
    correction k times, any hour-bearing middle step once if present (the hearing only when it
    happens), any hour-bearing D1-only step once."""
    c = [0] * len(HOUR_STEPS)
    for j, step in enumerate(HOUR_STEPS):
        if step == "prepare":
            c[j] = 1
        elif step == "correction":
            c[j] = k
        elif step == "hearing":
            c[j] = int(bool(h) and hearing_possible(s))
        elif step in D1_STEPS():
            c[j] = 1
        elif has_step(s, step):
            c[j] = 1
    return tuple(c)


def occurrence(s: str, k: int, h: int):
    """Which MENTIONABLE steps occurred in a case path (catalog-driven)."""
    out = {}
    for m in MENTIONABLE:
        if m == "correction":
            out[m] = k >= 1
        elif m == "hearing":
            out[m] = bool(h) and hearing_possible(s)
        else:
            out[m] = has_step(s, m)
    return out


def report_unit_bins():
    """Report rounding convention: the noisy value v (days) is reported in days
    if v < 14, weeks if 14 <= v < 70, months (30.4 d) otherwise."""
    return {"day": (1.0, 0.0, 14.0), "week": (7.0, 14.0, 70.0), "month": (30.4, 70.0, float("inf"))}


PUBLIC_MODEL_NOTES = """Assumptions shared by the Bayesian model and stated to the LLM baseline:
- Case paths: an incomplete application triggers a correction by the applicant and a new completeness check (loops truncated at 4).
- Under S4-S6, a hearing happens only if a neighbour objects.
- Agency step durations may differ by town by a common speed factor; comment_period and correction are not agency-paced.
- Admin records and applicant reports come from different cases.
- Applicant reports: gaps between events the applicant noticed, rounded to days (<14), weeks (<70) or months, with some reporting error; pending reports give days since submission with no decision yet.
- Reports are posted a uniformly random 10-150 days after submission, independent of the case; a report is pending if the decision had not arrived by the posting day, so completed reports over-represent quick cases.
- Web pages may omit steps or list steps that do not exist.
"""
