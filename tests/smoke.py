"""Smoke test: hand-built 5-node fragment of AB 2533 through the offline stack.

Run:  python3 tests/smoke.py
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "pipeline"))

from executor import reachable_outcomes, burden_of_run
from metrics import static_metrics, behavioral_metrics, check_monotonicity
from divergence import divergence_report

PRIORS = json.loads((pathlib.Path(__file__).parent.parent / "pipeline" / "burden_priors.json").read_text())


def mini_tree(variant, sanitation_objective):
    """Fragment: pre-2020 construction gate, then a sanitation standard.
    Variant A leaves 'inadequate sanitation' as judgment (faithful to HSC
    17920.3(a)); variant B resolves it into an objective proxy (has_toilet
    and has_hot_water) — the kind of silent threshold-invention a real
    compiler might commit, and exactly what divergence should surface."""
    sanitation_pred = (
        {"text": "unit has a toilet and hot water", "type": "objective",
         "expr": {"and": [{"var": "has_toilet"}, {"var": "has_hot_water"}]},
         "inputs": ["has_toilet", "has_hot_water"], "decider": "inspector",
         "monotonicity": {"has_toilet": "+", "has_hot_water": "+"}}
        if sanitation_objective else
        {"text": "sanitation is not inadequate per HSC 17920.3(a)", "type": "judgment",
         "inputs": ["has_toilet", "has_hot_water"], "decider": "inspector"}
    )
    return {
        "rule_id": "ab2533-mini",
        "citation": "Cal. Gov. Code § 66311.7; Cal. HSC § 17920.3 (fragment)",
        "compiler": {"prompt_variant": variant},
        "input_schema": {"fields": [
            {"name": "construction_year", "type": "number", "range": [1950, 2026],
             "question": "What year was the unit constructed?", "supplier": "applicant",
             "provenance_class": "c", "sensitive": True},
            {"name": "has_toilet", "type": "boolean", "question": "Does the unit have a working toilet?",
             "supplier": "inspector", "provenance_class": "f"},
            {"name": "has_hot_water", "type": "boolean", "question": "Does the unit have hot running water?",
             "supplier": "inspector", "provenance_class": "f"},
        ]},
        "nodes": [
            {"id": "n_date",
             "span": {"quote": "constructed before January 1, 2020", "cite": "GOV 66311.7(a)"},
             "predicate": {"text": "constructed before 2020", "type": "objective",
                           "expr": {"<": [{"var": "construction_year"}, 2020]},
                           "inputs": ["construction_year"], "decider": "clerk",
                           "monotonicity": {"construction_year": "-"}},
             "if_true": "n_sanitation", "if_false": "o_na"},
            {"id": "n_sanitation",
             "span": {"quote": "Inadequate sanitation", "cite": "HSC 17920.3(a)"},
             "predicate": sanitation_pred,
             "if_true": "o_approve", "if_false": "o_deny"},
            {"id": "o_approve", "outcome": {"label": "approve"}},
            {"id": "o_deny", "outcome": {"label": "deny"}},
            {"id": "o_na", "outcome": {"label": "not_applicable"}},
        ],
        "root": "n_date",
    }


tree_a = mini_tree("vA", sanitation_objective=False)
tree_b = mini_tree("vB", sanitation_objective=True)

panel = {"panel_id": "smoke", "generation": {"mode": "fuzz"}, "cases": [
    {"case_id": "c1", "facts": {"construction_year": 2014, "has_toilet": True, "has_hot_water": True},
     "demographics": {"narrative": "2014 garage conversion, full plumbing"}},
    {"case_id": "c2", "facts": {"construction_year": 2014, "has_toilet": True, "has_hot_water": False},
     "demographics": {"narrative": "2014 unit, no hot water heater"}},
    {"case_id": "c3", "facts": {"construction_year": 2023, "has_toilet": False, "has_hot_water": False}},
    {"case_id": "c4", "facts": {"construction_year": 2010}},  # missing inspection facts -> schema gap
]}

# --- executor ---
r1a = reachable_outcomes(tree_a, panel["cases"][0]["facts"])
assert r1a.outcomes == {"approve", "deny"}, r1a.outcomes            # judgment node -> identified set
assert r1a.discretion_exposed and r1a.pivotal_judgment == {"n_sanitation"}
r1b = reachable_outcomes(tree_b, panel["cases"][0]["facts"])
assert r1b.outcomes == {"approve"} and r1b.determinate              # objective variant determines it
r3 = reachable_outcomes(tree_b, panel["cases"][2]["facts"])
assert r3.outcomes == {"not_applicable"}                            # post-2020 short-circuits
r4 = reachable_outcomes(tree_b, panel["cases"][3]["facts"])
assert r4.missing_inputs == {"has_toilet"} or r4.missing_inputs <= {"has_toilet", "has_hot_water"}
assert not r4.discretion_exposed                                    # gap, not discretion

# --- burden: path-dependence ---
b3 = burden_of_run(tree_b, r3, PRIORS)
b1 = burden_of_run(tree_b, r1b, PRIORS)
assert b3["dollars"] < b1["dollars"]        # short-circuited case never pays for the inspection
assert b1["n_sensitive"] == 1

# --- metrics ---
s_a, s_b = static_metrics(tree_a), static_metrics(tree_b)
assert s_a["judgment_mass"] == 0.5 and s_b["judgment_mass"] == 0.0
beh_a = behavioral_metrics(tree_a, panel, PRIORS)
beh_b = behavioral_metrics(tree_b, panel, PRIORS)
assert beh_a["p_discretion_exposed"] > beh_b["p_discretion_exposed"]
assert beh_a["witnesses"][0]["narrative"]
assert check_monotonicity(tree_b, panel) == []

# --- divergence: c2 splits the readings (judgment set overlaps, so only a
#     genuinely disjoint pair counts). vA on c2 -> {approve,deny}; vB -> {deny}.
#     Overlap -> not divergent. Verify via a third, stricter tree instead.
tree_c = mini_tree("vC", sanitation_objective=True)
tree_c["nodes"][1]["predicate"]["expr"] = {"var": "has_toilet"}  # laxer reading: toilet alone suffices
tree_c["nodes"][1]["predicate"]["inputs"] = ["has_toilet"]
tree_c["nodes"][1]["predicate"]["monotonicity"] = {"has_toilet": "+"}
rep = divergence_report([tree_b, tree_c], panel)
div_ids = {c["case_id"] for c in rep["divergent_witnesses"]}
assert div_ids == {"c2"}, div_ids            # toilet yes / hot water no: approve vs deny, disjoint

print("smoke OK")
print(f"  tree A: judgment_mass={s_a['judgment_mass']:.2f}, P(discretion)={beh_a['p_discretion_exposed']:.2f}")
print(f"  tree B: judgment_mass={s_b['judgment_mass']:.2f}, P(discretion)={beh_b['p_discretion_exposed']:.2f}")
print(f"  burden(full path)={b1['hours']:.1f}h ${b1['dollars']:.0f}  vs  burden(short-circuit)={b3['hours']:.1f}h ${b3['dollars']:.0f}")
print(f"  divergence witnesses (vB vs vC): {sorted(div_ids)}")
