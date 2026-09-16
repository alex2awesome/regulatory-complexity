"""Complexity readouts over compiled rules and case panels.

Three axes, reported separately and never folded into one number:
  1. SIZE      — reading/structure cost: nodes, depth, inputs, actors, refs.
  2. DISCRETION — P(D): share of the case panel whose outcome the rule does
                  not determine (judgment/reference nodes pivotal). Judge-free:
                  certified by witness cases, not by any model's opinion.
  3. BURDEN    — expected effort vector over the panel (path-dependent),
                  plus wasted burden (effort spent by cases that end in deny).
"""

from collections import Counter

from executor import reachable_outcomes, burden_of_run


def static_metrics(tree):
    nodes = tree["nodes"]
    preds = [n["predicate"] for n in nodes if "predicate" in n]
    by_type = Counter(p["type"] for p in preds)
    deciders = {p["decider"] for p in preds}
    suppliers = {f["supplier"] for f in tree["input_schema"]["fields"]}
    flags = Counter(f["flag"] for n in nodes for f in n.get("flags", []))
    score_nodes = [n for n in nodes if "score" in n]
    return {
        "n_nodes": len(nodes),
        "n_predicates": len(preds),
        "n_score_nodes": len(score_nodes),
        "n_score_items": sum(len(n["score"]["items"]) for n in score_nodes),
        "predicates_by_type": dict(by_type),
        "judgment_mass": (by_type["judgment"] + by_type["reference"]) / max(len(preds), 1),
        "n_inputs": len(tree["input_schema"]["fields"]),
        "n_actors": len(deciders | suppliers),
        "n_deciders": len(deciders),
        "flags": dict(flags),
    }


def behavioral_metrics(tree, panel, priors):
    """Run every case; report discretion exposure and burden distribution."""
    runs = []
    for case in panel["cases"]:
        run = reachable_outcomes(tree, case["facts"])
        runs.append((case, run))

    n = len(runs)
    exposed = [(c, r) for c, r in runs if r.discretion_exposed]
    gaps = [(c, r) for c, r in runs if r.missing_inputs]
    pivotal = Counter(nid for _, r in runs for nid in r.pivotal_judgment)

    burdens = [burden_of_run(tree, r, priors) for _, r in runs]
    mean_burden = {
        k: sum(b[k] for b in burdens) / max(n, 1)
        for k in ("hours", "dollars", "wait_days", "trips", "n_sensitive")
    }
    # wasted burden: effort demanded of cases whose ONLY reachable outcome is deny
    denied = [b for (c, r), b in zip(runs, burdens) if r.outcomes == {"deny"}]
    wasted = {
        k: sum(b[k] for b in denied) / max(len(denied), 1)
        for k in ("hours", "dollars")
    } if denied else {"hours": 0, "dollars": 0}

    return {
        "n_cases": n,
        "p_discretion_exposed": len(exposed) / max(n, 1),
        "p_schema_gap": len(gaps) / max(n, 1),
        "pivotal_node_frequencies": dict(pivotal.most_common()),
        "mean_burden": mean_burden,
        "mean_burden_when_denied_outright": wasted,
        "n_denied_outright": len(denied),
        "witnesses": [
            {
                "case_id": c["case_id"],
                "outcomes": sorted(r.outcomes),
                "pivotal_nodes": sorted(r.pivotal_judgment),
                "narrative": (c.get("demographics") or {}).get("narrative", ""),
            }
            for c, r in exposed[:20]
        ],
    }


def check_monotonicity(tree, panel):
    """Metamorphic check: for each declared monotone input on each objective
    predicate, perturb the input in the declared direction and verify no
    outcome moves against it (approve must not flip to deny). Violations are
    compilation bugs — found without any oracle."""
    violations = []
    order = {"deny": 0, "refer": 1, "conditional_approve": 2, "approve": 3, "not_applicable": None}

    def best(outcomes):
        vals = [order[o] for o in outcomes if order.get(o) is not None]
        return max(vals) if vals else None

    for node in tree["nodes"]:
        pred = node.get("predicate") or {}
        for field_name, direction in (pred.get("monotonicity") or {}).items():
            if direction == "0":
                continue
            for case in panel["cases"]:
                facts = dict(case["facts"])
                if not isinstance(facts.get(field_name), (int, float)) or isinstance(facts.get(field_name), bool):
                    continue
                base = best(reachable_outcomes(tree, facts).outcomes)
                bumped = dict(facts)
                bumped[field_name] = facts[field_name] * 1.10 + 1
                after = best(reachable_outcomes(tree, bumped).outcomes)
                if base is None or after is None:
                    continue
                # '+': increasing the field pushes predicate toward true; which
                # outcome direction that implies depends on tree wiring, so we
                # only flag the universally suspect pattern: any strict flip
                # approve->deny or deny->approve from a small monotone bump.
                if abs(after - base) == 3:
                    violations.append({
                        "node": node["id"], "field": field_name,
                        "case_id": case["case_id"], "flip": [base, after],
                    })
    return violations
