"""Data-driven validity of process designs, for any statute package.

Two rule formats produce the same object, a bool matrix [n_readings, n_designs]:

1. AUTHOR format (a package's `validity_rules`, hidden ground truth): evidence types per
   step; conditional sufficiency rules; deadline with start event and tolling; design
   floors; authorized burdens (always / conditional); design burdens; denial grounds.
   Conditions are dicts {question_id: bool} that must all hold ("when"/"all_of");
   "always" means unconditional.
2. READER format (a blind reader's `reading.json`): per major question and design,
   valid_if_yes / valid_if_no. A design is valid under a reading iff it is valid under
   every major question's answer in that reading (conjunction). This is the model-side
   matrix in round 5: the reader's questions, not the author's.

Readings are answer vectors over an ordered question list; `all_readings(qids)` fixes
the order (True first), matching readings.all_readings when qids == validity.QUESTIONS.
Truth-blind: no truth imports; the author rules are passed in by the generator/scorer.
"""

from __future__ import annotations

import itertools

import numpy as np

from . import spec


def all_readings(qids):
    return [dict(zip(qids, vals)) for vals in itertools.product([True, False], repeat=len(qids))]


def _holds(cond, reading):
    if cond in (None, "always"):
        return True
    return all(bool(reading.get(q)) == bool(v) for q, v in cond.items())


# ---------------------------------------------------------------- author format

def design_steps(sid):
    """Middle steps of a design (conditional marked), plus the decision step if separate."""
    st = spec.STRUCTURES[sid]
    steps = [(x.rstrip("?"), x.endswith("?")) for x in st["d2"]]
    return steps, st["shared_decision"]


def author_check(rules, sid, reading, burdens_of_design=None):
    """{constraint: (ok, reason)} for one design under one reading, author rules."""
    steps, shared = design_steps(sid)
    present = [s for s, _ in steps]
    res = {}
    # C2 sufficiency: evidence available before the decision
    ev = set()
    for s in present:
        ev |= set(rules.get("evidence_by_step", {}).get(s, []))
    missing = []
    for rule in rules.get("sufficiency_C2", []):
        if not _holds(rule.get("when"), reading):
            continue
        if "requires_all" in rule and not set(rule["requires_all"]) <= ev:
            missing.append(f"needs all {rule['requires_all']} ({rule.get('clause','')})")
        if "requires_any" in rule and not (set(rule["requires_any"]) & ev):
            missing.append(f"needs any {rule['requires_any']} ({rule.get('clause','')})")
    res["C2_sufficiency"] = (not missing, "; ".join(missing) or f"evidence {sorted(ev)}")
    # C3 precedence: serial menu, every evidence step precedes/coincides with the decision
    res["C3_precedence"] = (True, "serial design; determinations precede issuance")
    # C4 deadline: mandated floors between start event and decision, minus tolled steps
    dl = rules.get("deadline_C4")
    if dl:
        floors = rules.get("design_floors", {})
        tolled = set()
        t = dl.get("tolled_steps_if")
        if t and _holds(t.get("when"), reading):
            tolled = set(t.get("steps", []))
        total = sum(floors[s]["days"] for s, _ in steps if s in floors and s not in tolled)
        ok = total <= dl["days"]
        res["C4_deadline"] = (ok, f"mandated waits {total:g} d {'<=' if ok else '>'} {dl['days']} d"
                              + (f" (tolled: {sorted(tolled)})" if tolled else ""))
    # C5 authority: burdens implied by the design's steps (and any extra fee burdens passed in)
    always = set(rules.get("authorized_always", {}))
    cond = rules.get("authorized_if", {})
    burdens = set(burdens_of_design or [])
    implied = rules.get("step_burdens", {})  # optional explicit map step -> [burden ids]
    for s in present:
        for b in implied.get(s, []):
            burdens.add(b)
    if not implied:  # default convention shared with the hen: attendance / routine sample
        if "site_inspection" in present:
            burdens.add("attend:site_inspection")
        if "product_lab_test" in present:
            burdens.add("provide:sample_routine")
        if "hearing" in present:
            burdens.add("attend:hearing")
    bad = []
    for b in burdens:
        if b in always:
            continue
        c = cond.get(b)
        if c is not None and _holds(c.get("all_of"), reading):
            continue
        bad.append(b)
    res["C5_authority"] = (not bad, f"unauthorized {sorted(bad)}" if bad else "burdens authorized")
    return res


def author_validity_matrix(rules, qids, design_ids=None):
    design_ids = design_ids or list(spec.STRUCTURE_IDS)
    R = all_readings(qids)
    V = np.zeros((len(R), len(design_ids)), bool)
    for i, r in enumerate(R):
        for j, sid in enumerate(design_ids):
            V[i, j] = all(ok for ok, _ in author_check(rules, sid, r).values())
    return V


# ---------------------------------------------------------------- reader format

def reader_validity_matrix(reading_json, design_ids=None, major_only=True):
    """Conjunction over the reader's (major) questions of valid_if_yes / valid_if_no.
    Returns (V [n_readings, n_designs], qids in the order used)."""
    design_ids = design_ids or list(spec.STRUCTURE_IDS)
    qs = [q for q in reading_json["questions"] if (q.get("major") or not major_only)]
    qids = [q["id"] for q in qs]
    dv = reading_json["design_validity"]
    R = all_readings(qids)
    V = np.ones((len(R), len(design_ids)), bool)
    for j, sid in enumerate(design_ids):
        entry = dv.get(sid, {})
        for i, r in enumerate(R):
            ok = True
            for q in qids:
                e = entry.get("per_question", {}).get(q) or entry.get(q) or entry.get("questions", {}).get(q)
                if e is None:
                    continue  # reader gave no judgement: no constraint from this question
                ok = ok and bool(e["valid_if_yes"] if r[q] else e["valid_if_no"])
            V[i, j] = ok
    return V, qids


def reader_question_probs(reading_json, major_only=True):
    return {q["id"]: float(q["p_yes"]) for q in reading_json["questions"] if (q.get("major") or not major_only)}
