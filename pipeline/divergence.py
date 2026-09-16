"""Cross-compilation divergence: the discretion measurement.

Given k independent compilations of the same rule and one case panel, a case
DIVERGES if two compilations' reachable-outcome sets are disjoint — i.e. there
exist faithful readings under which the case is approved and faithful readings
under which it is denied, with no overlap. (Overlapping sets mean the
compilations merely differ in how much they leave open, which is attributed
by the per-tree discretion metric instead.)

Each divergent case is a WITNESS: a concrete household whose outcome the
statute does not determine. Witnesses go to adjudication (prompt 05) to be
sorted into compilation_bug / schema_gap / genuine_underdetermination —
only the last counts as discretion.
"""

from itertools import combinations

from executor import reachable_outcomes


def divergence_report(trees, panel):
    per_case = []
    for case in panel["cases"]:
        sets = {}
        for t in trees:
            variant = (t.get("compiler") or {}).get("prompt_variant") or t["rule_id"]
            sets[variant] = sorted(reachable_outcomes(t, case["facts"]).outcomes)
        disjoint_pairs = [
            (a, b) for a, b in combinations(sets, 2)
            if not (set(sets[a]) & set(sets[b]))
        ]
        per_case.append({
            "case_id": case["case_id"],
            "outcome_sets": sets,
            "diverges": bool(disjoint_pairs),
            "disjoint_pairs": disjoint_pairs,
        })
    n = len(per_case)
    divergent = [c for c in per_case if c["diverges"]]
    return {
        "n_trees": len(trees),
        "n_cases": n,
        "p_divergent": len(divergent) / max(n, 1),
        "divergent_witnesses": divergent[:50],
        "per_case": per_case,
    }
