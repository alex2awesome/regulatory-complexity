"""Validity of process designs under the toy statute's decision model.

Design: docs/process-validity.md. Truth-blind (public spec only).

A process design is VALID under a reading of the statute if it satisfies
every constraint that reading places on it:

  C1 coverage     every d-step is carried out by some p-step;
  C2 sufficiency  the D2 steps collect evidence that the reading accepts
                  for a Sec. 3 nuisance determination;
  C3 precedence   every step that makes the determination finishes
                  before the permit is issued (Sec. 3 "before issuing");
  C4 deadline     the design's own mandated waiting periods fit within
                  the Sec. 4 clock (a design can be infeasible by construction);
  C5 authority    every burden on the applicant (hours, fees, documents)
                  traces to a clause that authorizes it;
  C6 grounds      a denial may rest only on authorized grounds.

Validity is a property of the design. Compliance (e.g. how often a town
actually meets the 30-day deadline) is a property of behaviour, estimated
from evidence (estimands `deadline.p_miss`). A design can be valid and
chronically non-compliant.

The statute's vague clauses make validity uncertain. Each open interpretive
question is a binary reading; a full reading is one answer to each. We
report validity per reading, and P(valid) under a declared reading prior.
The default prior is ILLUSTRATIVE, not an estimate: real reading
probabilities would come from case law, agency guidance, or calibrated
legal readers. Statute edits are modelled as resolving questions (fixing
their answers) or changing constraints.

  python -m pipeline.procbench.toy_statute.validity [--out validity.json]
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import spec

# ---------------------------------------------------------------- readings

QUESTIONS = {
    "Q1_desk_sufficient": "Sec. 3: can a desk review of the site plan alone support the nuisance determination?",
    "Q2_neighbor_input_required": "Sec. 3 ('to adjoining properties'): must adjoining owners get notice and a chance to comment?",
    "Q3_investigative_power": "Sec. 3: does the duty to determine imply power to require the applicant's attendance at an inspection or hearing?",
    "Q4_clock_includes_d2": "Sec. 4: does the 30-day clock run through the nuisance determination (no tolling during notice)?",
    "Q5_separate_fees": "Sec. 5: does 'a reasonable application fee' authorize separate notice or inspection fees?",
}

# ILLUSTRATIVE prior, P(answer = True). Not an estimate; see module docstring.
ILLUSTRATIVE_PRIOR = {
    "Q1_desk_sufficient": 0.7,
    "Q2_neighbor_input_required": 0.3,
    "Q3_investigative_power": 0.9,
    "Q4_clock_includes_d2": 0.8,
    "Q5_separate_fees": 0.5,
}

# Evidence each p-step contributes to the Sec. 3 determination.
EVIDENCE = {
    "desk_review": {"plan"},
    "site_inspection": {"site"},
    "comment_period": {"neighbor_input"},
    "hearing": {"neighbor_input", "hearing"},
}

# Burdens that trace to text with certainty, and those that depend on a reading.
AUTHORIZED_ALWAYS = {
    "prepare_application": "Sec. 2",
    "site_plan": "Sec. 2",
    "correction": "Sec. 2 + Sec. 4 ('complete application')",
    "fee:application": "Sec. 5",
    # Attending a hearing is the applicant's right, not a compelled burden
    # (it still costs hours; burden is measured separately from validity).
    "attend:hearing": "Sec. 3 (participation, voluntary)",
}
AUTHORIZED_IF = {
    "attend:site_inspection": ("Q3_investigative_power", "Sec. 3 (implied)"),
    "fee:notice": ("Q5_separate_fees", "Sec. 5 (broad reading)"),
    "fee:inspection": ("Q5_separate_fees", "Sec. 5 (broad reading)"),
}
AUTHORIZED_GROUNDS = {"ineligible": "Sec. 1", "incomplete": "Sec. 4", "nuisance": "Sec. 3"}


# ---------------------------------------------------------------- designs

@dataclass
class Step:
    id: str                 # p-step catalog id (spec.P_STEPS) or a new step
    serves: list            # d-steps it serves
    after: list = field(default_factory=list)   # precedence: ids that must finish first
    floor_days: float = 0.0  # waiting period the design itself mandates
    conditional: bool = False  # e.g. hearing only on objection
    determines: bool = False   # makes (part of) the Sec. 3 determination


@dataclass
class Design:
    id: str
    text: str
    steps: list
    decision_at: str        # step id at which the permit decision issues
    burdens: list           # applicant burden ids (see AUTHORIZED_*)
    grounds: list = field(default_factory=lambda: ["ineligible", "incomplete", "nuisance"])
    in_menu: bool = True    # part of the fitted refinement menu S1-S6


def _d1():
    return [Step("prepare", ["D1"]), Step("completeness_check", ["D1"], ["prepare"])]


def menu_design(s: str) -> Design:
    """Translate a spec.STRUCTURES entry into a Design (serial chain)."""
    st = spec.STRUCTURES[s]
    steps = _d1()
    prev = "completeness_check"
    for raw in st["d2"]:
        sid = raw.rstrip("?")
        # Design floors: a 14-day comment period and a 10-day hearing notice
        # (assumed design parameters of the menu, declared in docs/process-validity.md).
        floor = {"comment_period": 14.0, "hearing": 10.0}.get(sid, 0.0)
        steps.append(Step(sid, ["D2"], [prev], floor_days=floor, conditional=raw.endswith("?"),
                          determines=sid in EVIDENCE))
        prev = sid
    if st["shared_decision"]:
        steps[-1].serves = ["D2", "D3"]
        decision_at = steps[-1].id
    else:
        steps.append(Step("decision_issue", ["D3"], [prev]))
        decision_at = "decision_issue"
    # Fee schedules are a town choice separate from the structure; add them with with_fees().
    burdens = ["prepare_application", "site_plan", "correction", "fee:application"]
    ids = [x.id for x in steps]
    if "site_inspection" in ids:
        burdens += ["attend:site_inspection"]
    if "hearing" in ids:
        burdens += ["attend:hearing"]
    return Design(s, spec.STRUCTURE_TEXT[s], steps, decision_at, burdens)


def with_fees(design: Design, items, new_id=None) -> Design:
    """Copy of a design whose town also charges the given separate fee items."""
    import copy
    d = copy.deepcopy(design)
    d.burdens = d.burdens + [f"fee:{i}" for i in items]
    d.id = new_id or f"{design.id}+fees({','.join(items)})"
    d.in_menu = False
    d.text = design.text + f" Separate fee(s): {', '.join(items)}."
    return d


def concurrent_design(s: str) -> Design:
    """Menu structure s with its D2 branches run in parallel after completeness:
    desk review | notice -> comment -> [hearing] | site inspection."""
    d = menu_design(s)
    by = {x.id: x for x in d.steps}
    ends = []
    for sid in ("desk_review", "neighbor_notice", "site_inspection"):
        if sid in by:
            by[sid].after = ["completeness_check"]
            ends.append(sid)
    if "neighbor_notice" in by:
        ends.remove("neighbor_notice")
        ends.append("comment_period")
        if "hearing" in by:  # hearing (on objection) follows the comment period
            by["hearing"].after = ["comment_period"]
            ends.append("hearing")
    if spec.STRUCTURES[s]["shared_decision"]:
        by["site_inspection"].serves = ["D2"]
        d.steps.append(Step("issue_at_inspection", ["D3"], list(ends)))
        d.decision_at = "issue_at_inspection"
    else:
        by["decision_issue"].after = list(ends)
    d.id, d.in_menu = f"{s}c", False
    d.text = spec.STRUCTURE_TEXT[s] + " D2 branches run concurrently."
    return d


def hypothetical_designs() -> list:
    """Designs outside the fitted menu, chosen to exercise each constraint."""
    out = []
    # Concurrent variants of S2-S6 (the M8 lever): all D2 branches start once the
    # application is complete; the decision issues when every branch has finished.
    for m in ("S2", "S3", "S4", "S5", "S6"):
        out.append(concurrent_design(m))
    # H2: S1 plus a requirement to collect signed consent from neighbours.
    d = menu_design("S1")
    d.id, d.in_menu = "H2_neighbor_signatures", False
    d.text = "As S1, but the applicant must collect signed consent from all adjoining neighbours."
    d.burdens = d.burdens + ["neighbor_signatures"]
    out.append(d)
    # H3: S4 with a locally mandated 30-day comment period.
    d = menu_design("S4")
    for x in d.steps:
        if x.id == "comment_period":
            x.floor_days = 30.0
    d.id, d.in_menu = "H3_30day_comment", False
    d.text = "As S4, but local rules mandate a 30-day comment period."
    out.append(d)
    # H4: permit issued after desk review; inspection afterwards (conditional permit).
    steps = _d1() + [Step("desk_review", ["D2"], ["completeness_check"], determines=True),
                     Step("decision_issue", ["D3"], ["desk_review"]),
                     Step("site_inspection", ["D2"], ["decision_issue"], determines=True)]
    out.append(Design("H4_inspect_after_issue",
                      "Desk review, permit issued, then a site inspection whose findings also count toward the nuisance determination.",
                      steps, "decision_issue",
                      ["prepare_application", "site_plan", "correction", "fee:application",
                       "attend:site_inspection"], in_menu=False))
    # H5: inspection only, decision issued at it.
    steps = _d1() + [Step("site_inspection", ["D2", "D3"], ["completeness_check"], determines=True)]
    out.append(Design("H5_inspection_only", "Site inspection only; the inspector decides on the spot.",
                      steps, "site_inspection",
                      ["prepare_application", "site_plan", "correction", "fee:application",
                       "attend:site_inspection"], in_menu=False))
    # H6: S1 but denial may also rest on coop appearance.
    d = menu_design("S1")
    d.id, d.in_menu = "H6_aesthetic_grounds", False
    d.text = "As S1, but the reviewer may deny a coop that is unsightly."
    d.grounds = d.grounds + ["aesthetics"]
    out.append(d)
    # H7: notice + comment + desk + hearing, all concurrent with D1 completeness checking.
    d = menu_design("S4")
    by = {x.id: x for x in d.steps}
    by["neighbor_notice"].after = ["prepare"]
    d.id, d.in_menu = "H7_notice_at_submission", False
    d.text = "As S4, but neighbours are notified at submission, while the application is still being checked for completeness."
    out.append(d)
    # H8: S3 with a separate inspection fee (a fee-schedule choice, not a structure).
    out.append(with_fees(menu_design("S3"), ["inspection"], "H8_S3_inspection_fee"))
    return out


def all_designs() -> list:
    return [menu_design(s) for s in spec.STRUCTURE_IDS] + hypothetical_designs()


# ---------------------------------------------------------------- checks

def _ancestors(design: Design, sid: str) -> set:
    by = {x.id: x for x in design.steps}
    seen, stack = set(), list(by[sid].after)
    while stack:
        a = stack.pop()
        if a not in seen:
            seen.add(a)
            stack.extend(by[a].after)
    return seen


def _earliest_finish(design: Design) -> dict:
    """Earliest finish time of every step if every step took only its mandated floor
    (agency work instantaneous). Conditional steps are included: the design must
    allow for them when they occur."""
    by = {x.id: x for x in design.steps}
    ef = {}

    def f(sid):
        if sid not in ef:
            ef[sid] = max((f(p) for p in by[sid].after), default=0.0) + by[sid].floor_days
        return ef[sid]

    for x in design.steps:
        f(x.id)
    return ef


def check(design: Design, reading: dict) -> dict:
    """Constraint results for one design under one reading: {constraint: (ok, reason)}."""
    ids = [x.id for x in design.steps]
    by = {x.id: x for x in design.steps}
    res = {}

    served = {d for x in design.steps for d in x.serves}
    missing = [d["id"] for d in spec.D_STEPS if d["id"] not in served]
    res["C1_coverage"] = (not missing, f"no step serves {missing}" if missing else "all d-steps served")

    # Evidence available BEFORE (or at) the decision.
    dec = design.decision_at
    before = _ancestors(design, dec) | {dec}
    ev = set()
    for sid in before:
        if by[sid].determines:
            ev |= EVIDENCE.get(sid, set())
    # A conditional hearing only happens on objection; the comment period supplies input either way.
    need = []
    if not ev:
        need.append("some evidence")
    if not reading["Q1_desk_sufficient"] and not ev & {"site", "neighbor_input"}:
        need.append("site or neighbour evidence (desk review alone insufficient)")
    if reading["Q2_neighbor_input_required"] and "neighbor_input" not in ev:
        need.append("neighbour notice and comment")
    res["C2_sufficiency"] = (not need, "missing " + "; ".join(need) if need else f"evidence {sorted(ev)}")

    late = [x.id for x in design.steps if x.determines and x.id not in before]
    res["C3_precedence"] = (not late, f"determining step(s) {late} finish after the permit issues" if late
                            else "determination precedes issuance")

    if reading["Q4_clock_includes_d2"]:
        ef = _earliest_finish(design)
        floor = ef[dec] - ef["completeness_check"]
        ok = floor <= spec.DEADLINE_DAYS
        res["C4_deadline"] = (ok, f"mandated waiting {floor:g} d {'<=' if ok else '>'} {spec.DEADLINE_DAYS} d")
    else:
        res["C4_deadline"] = (True, "clock tolled during the determination (reading)")

    bad = []
    for b in design.burdens:
        if b in AUTHORIZED_ALWAYS:
            continue
        if b in AUTHORIZED_IF and reading[AUTHORIZED_IF[b][0]]:
            continue
        bad.append(b)
    res["C5_authority"] = (not bad, f"unauthorized burden(s) {bad}" if bad else "all burdens authorized")

    badg = [g for g in design.grounds if g not in AUTHORIZED_GROUNDS]
    res["C6_grounds"] = (not badg, f"unauthorized ground(s) {badg}" if badg else "grounds authorized")
    return res


def readings():
    qs = list(QUESTIONS)
    for vals in itertools.product([True, False], repeat=len(qs)):
        yield dict(zip(qs, vals))


def reading_weight(r: dict, prior: dict) -> float:
    w = 1.0
    for q, v in r.items():
        w *= prior[q] if v else 1.0 - prior[q]
    return w


def evaluate(design: Design, prior: dict = ILLUSTRATIVE_PRIOR, fixed: dict | None = None) -> dict:
    """Validity summary over readings. `fixed` pins question answers (a statute edit)."""
    fixed = fixed or {}
    pv, tot = 0.0, 0.0
    per_constraint = {}
    depends = set()
    for r in readings():
        if any(r[q] != v for q, v in fixed.items()):
            continue
        w = reading_weight({q: v for q, v in r.items() if q not in fixed}, prior)
        res = check(design, r)
        valid = all(ok for ok, _ in res.values())
        tot += w
        pv += w * valid
        for c, (ok, why) in res.items():
            pc = per_constraint.setdefault(c, {"p_pass": 0.0, "reasons": set()})
            pc["p_pass"] += w * ok
            if not ok:
                pc["reasons"].add(why)
    for q in QUESTIONS:
        if q in fixed:
            continue
        for r in readings():
            if any(r[k] != v for k, v in fixed.items()):
                continue
            r2 = dict(r, **{q: not r[q]})
            if all(ok for ok, _ in check(design, r).values()) != all(ok for ok, _ in check(design, r2).values()):
                depends.add(q)
                break
    p = pv / tot
    status = "valid under every reading" if p > 1 - 1e-12 else (
        "invalid under every reading" if p < 1e-12 else "reading-dependent")
    return {
        "design": design.id, "in_menu": design.in_menu, "text": design.text,
        "p_valid": p, "status": status, "depends_on": sorted(depends),
        "constraints": {c: {"p_pass": v["p_pass"] / tot, "fail_reasons": sorted(v["reasons"])}
                        for c, v in per_constraint.items()},
    }


# ---------------------------------------------------------------- statute edits

EDITS = {
    "E1_safe_harbour": ({"Q1_desk_sufficient": True, "Q2_neighbor_input_required": False},
                        "A coop at least 10 ft from every property line is deemed not a nuisance "
                        "(for compliant plans the determination is a plan check)."),
    "E2_notice_required": ({"Q2_neighbor_input_required": True},
                           "The authority shall notify adjoining owners and allow 14 days for comment."),
    "E3_clock_tolled": ({"Q4_clock_includes_d2": False},
                        "The 30-day period excludes any period for neighbour comment."),
    "E4_single_fee": ({"Q5_separate_fees": False},
                      "The application fee is the only fee that may be charged."),
    "E5_investigation": ({"Q3_investigative_power": True},
                         "The authority may inspect the site; the applicant shall allow access."),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    designs = all_designs()
    rows = [evaluate(d) for d in designs]
    edits = {e: {"text": t, "fixes": f, "p_valid": {d.id: evaluate(d, fixed=f)["p_valid"] for d in designs}}
             for e, (f, t) in EDITS.items()}
    out = {"questions": QUESTIONS, "illustrative_prior": ILLUSTRATIVE_PRIOR,
           "designs": rows, "edits": edits}
    for r in rows:
        fails = {c: v["p_pass"] for c, v in r["constraints"].items() if v["p_pass"] < 1}
        print(f"{r['design']:24s} P(valid)={r['p_valid']:.3f}  {r['status']:28s} depends={r['depends_on']} fails={fails}")
    print("\nP(valid) after each statute edit:")
    print(" " * 24 + "".join(f"{e[:14]:>16s}" for e in edits))
    for d in designs:
        print(f"{d.id:24s}" + "".join(f"{edits[e]['p_valid'][d.id]:16.3f}" for e in edits))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=sorted))
    return out


if __name__ == "__main__":
    main()
