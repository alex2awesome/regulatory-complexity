"""Simplification as tree surgery under harm bounds.

Three edit families, in ascending risk:
  1. reorder_conjunctive_chain — pure burden reduction, zero outcome flips by
     construction (cheapest-expected-disqualifier-first ordering).
  2. prune candidates — collapse predicates that never bind on the calibrated
     panel; zero flips ON THE PANEL, validity rests on panel coverage.
  3. substitute — replace a judgment predicate with an objective threshold
     (typically the reading-ensemble's median cutoff). This is the "objective
     standards" rewrite; flip_report prices it in people.

Harm semantics use identified sets: a substitution that DETERMINES a
previously indeterminate case is the intended effect (reported, with which
side of the band they landed on); a substitution that FLIPS a previously
determinate case is real harm.
"""

import copy

from executor import reachable_outcomes, burden_of_run


# ------------------------------------------------------------------ reorder

def find_conjunctive_chain(tree):
    """Longest run of predicate nodes n1 -> (if_true) -> n2 -> ... where every
    if_false lands on the same node (common disqualification). Reordering such
    a chain cannot change any case's outcome."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    best = []
    for start in nodes:
        chain, cur, fail = [], start, None
        while cur in nodes and "predicate" in nodes[cur]:
            node = nodes[cur]
            if fail is None:
                fail = node.get("if_false")
            if node.get("if_false") != fail:
                break
            chain.append(cur)
            cur = node.get("if_true")
        if len(chain) > len(best):
            best = chain
    return best if len(best) >= 2 else []


def reorder_conjunctive_chain(tree, panel, priors):
    """Sort the chain by expected-cost rule: ascending cost_i / P(fail_i)
    (cheapest, most-frequently-disqualifying checks first). Returns
    (new_tree, report). Outcome-invariant; only expected burden moves."""
    chain = find_conjunctive_chain(tree)
    if not chain:
        return tree, {"reordered": False, "reason": "no conjunctive chain of length >= 2"}
    nodes = {n["id"]: n for n in tree["nodes"]}
    fields = {f["name"]: f for f in tree["input_schema"]["fields"]}

    def node_cost(nid):
        total = 0.0
        for name in nodes[nid]["predicate"].get("inputs", []):
            f = fields.get(name, {})
            cls = priors["classes"].get(f.get("provenance_class", "a"), {})
            ov = f.get("burden_override", {})
            total += ov.get("hours", cls.get("hours", 0)) + ov.get("dollars", cls.get("dollars", 0)) / 60.0
        return max(total, 1e-6)

    def fail_rate(nid):
        pred = nodes[nid]["predicate"]
        if pred["type"] != "objective":
            return 0.5  # indeterminate: neutral prior
        from executor import eval_expr, Indeterminate
        fails = tries = 0
        for case in panel["cases"]:
            try:
                tries += 1
                if not bool(eval_expr(pred["expr"], case["facts"])):
                    fails += 1
            except Indeterminate:
                tries -= 1
        return fails / tries if tries else 0.5

    ranked = sorted(chain, key=lambda nid: node_cost(nid) / max(fail_rate(nid), 1e-6))
    if ranked == chain:
        return tree, {"reordered": False, "reason": "already optimal", "chain": chain}

    new_tree = copy.deepcopy(tree)
    new_nodes = {n["id"]: n for n in new_tree["nodes"]}
    tail = nodes[chain[-1]]["if_true"]
    fail = nodes[chain[0]]["if_false"]
    for i, nid in enumerate(ranked):
        new_nodes[nid]["if_true"] = ranked[i + 1] if i + 1 < len(ranked) else tail
        new_nodes[nid]["if_false"] = fail
    if new_tree["root"] == chain[0]:
        new_tree["root"] = ranked[0]
    else:  # repoint whatever led into the chain
        for n in new_tree["nodes"]:
            for k in ("if_true", "if_false"):
                if n.get(k) == chain[0] and n["id"] not in ranked:
                    n[k] = ranked[0]

    d_burden = _mean_burden_delta(tree, new_tree, panel, priors)
    flips = flip_report(tree, new_tree, panel)
    return new_tree, {"reordered": True, "old_order": chain, "new_order": ranked,
                      "mean_burden_delta": d_burden,
                      "n_true_flips": len(flips["true_flips"])}  # must be 0


# -------------------------------------------------------------------- prune

def prune_candidates(tree, panel):
    """Objective predicates on which every panel case takes the same branch.
    Collapsing them is flip-free on this panel; coverage is the caveat and is
    reported, not hidden."""
    from executor import eval_expr, Indeterminate
    out = []
    for node in tree["nodes"]:
        pred = node.get("predicate")
        if not pred or pred["type"] != "objective":
            continue
        vals = set()
        for case in panel["cases"]:
            try:
                vals.add(bool(eval_expr(pred["expr"], case["facts"])))
            except Indeterminate:
                vals.add(None)
        if len(vals) == 1 and None not in vals:
            out.append({"node": node["id"], "always": vals.pop(),
                        "caveat": f"constant on this panel of {len(panel['cases'])} cases; verify coverage"})
    return out


def collapse_node(tree, node_id, branch):
    """Remove a predicate node, wiring its parents straight to one branch."""
    new_tree = copy.deepcopy(tree)
    nodes = {n["id"]: n for n in new_tree["nodes"]}
    target = nodes[node_id]["if_true" if branch else "if_false"]
    for n in new_tree["nodes"]:
        for k in ("if_true", "if_false"):
            if n.get(k) == node_id:
                n[k] = target
    if new_tree["root"] == node_id:
        new_tree["root"] = target
    new_tree["nodes"] = [n for n in new_tree["nodes"] if n["id"] != node_id]
    return new_tree


# --------------------------------------------------------------- substitute

def substitute(tree, node_id, expr, inputs, note=""):
    """Replace a judgment predicate with an objective expr — the 'objective
    standards' rewrite. The cutoff should come from the looseness
    instrument's ensemble (e.g. median reader cutoff), not from intuition."""
    new_tree = copy.deepcopy(tree)
    for n in new_tree["nodes"]:
        if n["id"] == node_id:
            n["predicate"]["type"] = "objective"
            n["predicate"]["expr"] = expr
            n["predicate"]["inputs"] = inputs
            n["predicate"]["text"] += f"  [SUBSTITUTED: {note}]"
    return new_tree


# ------------------------------------------------------------------ pricing

def flip_report(orig_tree, new_tree, panel):
    """Price an edit in people, with identified-set semantics."""
    determined, true_flips, widened = [], [], []
    for case in panel["cases"]:
        old = reachable_outcomes(orig_tree, case["facts"]).outcomes
        new = reachable_outcomes(new_tree, case["facts"]).outcomes
        if old == new:
            continue
        entry = {"case_id": case["case_id"], "old": sorted(old), "new": sorted(new),
                 "narrative": (case.get("demographics") or {}).get("narrative", "")}
        if len(old) > 1 and len(new) == 1 and new <= old:
            determined.append(entry)      # band case resolved: intended effect, count who and which way
        elif new - old:
            true_flips.append(entry)      # reaches an outcome the original never allowed: harm
        else:
            widened.append(entry)
    return {"n_cases": len(panel["cases"]),
            "determined": determined, "true_flips": true_flips, "widened": widened,
            "summary": {"n_determined": len(determined), "n_true_flips": len(true_flips)}}


def _mean_burden_delta(orig_tree, new_tree, panel, priors):
    def mean_hours(tree):
        tot = 0.0
        for case in panel["cases"]:
            run = reachable_outcomes(tree, case["facts"])
            tot += burden_of_run(tree, run, priors)["hours"]
        return tot / max(len(panel["cases"]), 1)
    return {"hours_before": round(mean_hours(orig_tree), 3),
            "hours_after": round(mean_hours(new_tree), 3)}
