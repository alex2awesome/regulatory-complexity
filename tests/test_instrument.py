"""Offline tests for the looseness instrument, screener, worlds, simplify.

Run:  python3 tests/test_instrument.py
"""

import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "pipeline"))

import looseness as L
import worlds as W
from screener import screen, calibrate
from simplify import (find_conjunctive_chain, reorder_conjunctive_chain,
                      prune_candidates, collapse_node, substitute, flip_report)
from executor import reachable_outcomes

ROOT = pathlib.Path(__file__).parent.parent
PRIORS = json.loads((ROOT / "pipeline" / "burden_priors.json").read_text())


# ------------------------------------------------------------- cutoff fitting

fit = L.fit_cutoff([0.1, 0.3, 0.5, 0.7, 0.9], [False, False, False, True, True])
assert fit["direction"] == "above" and 0.5 < fit["b"] < 0.7 and fit["err_rate"] == 0

fit_rev = L.fit_cutoff([0.1, 0.3, 0.7, 0.9], [True, True, False, False])
assert fit_rev["direction"] == "below" and fit_rev["err_rate"] == 0


# ------------------------------------------------- ensemble looseness recovery

def simulated_reader(b, slope=40, seed=0, n=41):
    """Logistic threshold reader over a dense sweep."""
    rng = random.Random(seed)
    resp = []
    for i in range(n):
        t = i / (n - 1)
        p = 1 / (1 + pow(2.718281828, -slope * (t - b)))
        resp.append((t, rng.random() < p))
    return resp

# Loose predicate: planted reader cutoffs spread over [0.35, 0.75].
# Stochastic readers mean exact endpoints aren't recoverable at n=41; what the
# instrument must recover is the ORDERING of readers and the DISPERSION.
planted = [0.35, 0.45, 0.55, 0.65, 0.75]
ens = L.ensemble_looseness({f"r{i}": simulated_reader(b, seed=i) for i, b in enumerate(planted)})
assert ens["n_threshold_readers"] == 5
recovered = [ens["per_reader"][f"r{i}"]["b"] for i in range(5)]
assert recovered == sorted(recovered), recovered              # order preserved
lo, hi = ens["band_full"]
assert 0.30 < lo < 0.55 and 0.60 < hi < 0.85, ens["band_full"]
assert 0.07 < ens["cutoff_sd"] < 0.20, ens["cutoff_sd"]

# Thin predicate: every reader cuts at the same place -> near-zero band
tight = L.ensemble_looseness({f"r{i}": simulated_reader(0.5, slope=60, seed=10 + i) for i in range(5)})
assert tight["cutoff_sd"] < 0.03, tight["cutoff_sd"]

# Non-threshold reader (random) is flagged, not averaged in
rng = random.Random(7)
noise_reader = [(i / 40, rng.random() < 0.5) for i in range(41)]
mixed = L.ensemble_looseness({"good": simulated_reader(0.5), "chaos": noise_reader})
assert mixed["n_nonthreshold_readers"] == 1

# Band mass under a population
pop = [i / 999 for i in range(1000)]
assert abs(L.band_mass((0.35, 0.75), pop) - 0.4) < 0.01


# --------------------------------------------------------- planted ladder

prof_t = L.codability_profile(L.threshold_world, noise=0.02)
assert prof_t["stump"] > 0.95, prof_t                       # code must win rung 1

prof_c = L.codability_profile(L.conjunction_world, noise=0.02)
assert prof_c["conj2"] > 0.93, prof_c                       # code wins at L2
assert prof_c["conj2"] > prof_t["constant"]

prof_g = L.codability_profile(L.gestalt_world, noise=0.02)
assert max(prof_g.values()) < 0.87, prof_g                  # plateau: 'needs a model'

curve = L.identifiability_curve(noise=0.1, ns=(10, 160), n_rep=15)
assert curve[160] < curve[10]                               # more decisions -> better recovery


# ------------------------------------------------------------------- worlds

world = json.loads((ROOT / "worlds" / "ab2533_sanitation.json").read_text())
sweep = W.sweep(world, n=11)
thetas = [c["theta"]["sanitation_severity"] for c in sweep]
assert thetas[0] == 0.0 and thetas[-1] == 1.0 and len(set(thetas)) == 11
assert "sewage" in W.template_render(world, sweep[-1]).lower()
pop = W.population_sample(world, n=500, seed=2)
assert all(0 <= t <= 1 for t in pop)
assert sum(pop) / len(pop) < 0.45                           # beta(2,5) skews low


# ----------------------------------------------------------------- screener

loose = screen("Inadequate sanitation shall include, but not be limited to, the following: lack of adequate ventilation")
tight_s = screen("The unit was constructed before January 1, 2020, as shown in Section 17920.3")
deleg = screen("is determined to be a fire hazard in the opinion of the chief of the fire department")
assert loose["looseness_hypothesis"] > tight_s["looseness_hypothesis"]
assert "adequate" in loose["features"]["relative_gradable"]
assert loose["features"]["open_enumeration"]
assert deleg["mechanism"] == "delegation"
assert "HYPOTHESIS" in loose["status"]

cal = calibrate([(0.1, 0.05), (0.3, 0.12), (0.5, 0.22), (0.7, 0.30), (0.9, 0.41)])
assert cal["pearson_r"] > 0.98 and 0.4 < cal["slope"] < 0.5


# ----------------------------------------------------------------- simplify

def chain_tree():
    return {
        "rule_id": "chain-demo", "citation": "demo",
        "input_schema": {"fields": [
            {"name": "score_e", "type": "number", "range": [0, 1], "question": "engineer score",
             "supplier": "third_party", "provenance_class": "e"},
            {"name": "flag_a", "type": "boolean", "question": "self-attested flag",
             "supplier": "applicant", "provenance_class": "a"},
        ]},
        "nodes": [
            {"id": "n_exp", "span": {"quote": "q1", "cite": "c1"},
             "predicate": {"text": "expensive check, rarely fails", "type": "objective",
                           "expr": {">": [{"var": "score_e"}, 0.2]}, "inputs": ["score_e"], "decider": "official"},
             "if_true": "n_cheap", "if_false": "o_deny"},
            {"id": "n_cheap", "span": {"quote": "q2", "cite": "c2"},
             "predicate": {"text": "cheap check, often fails", "type": "objective",
                           "expr": {"var": "flag_a"}, "inputs": ["flag_a"], "decider": "clerk"},
             "if_true": "o_approve", "if_false": "o_deny"},
            {"id": "o_approve", "outcome": {"label": "approve"}},
            {"id": "o_deny", "outcome": {"label": "deny"}},
        ],
        "root": "n_exp",
    }

tree = chain_tree()
rng = random.Random(3)
panel = {"panel_id": "p", "generation": {"mode": "fuzz"}, "cases": [
    {"case_id": f"c{i}", "facts": {"score_e": rng.random(), "flag_a": rng.random() < 0.3}}
    for i in range(60)
]}

assert find_conjunctive_chain(tree) == ["n_exp", "n_cheap"]
new_tree, rep = reorder_conjunctive_chain(tree, panel, PRIORS)
assert rep["reordered"] and rep["new_order"] == ["n_cheap", "n_exp"]
assert rep["n_true_flips"] == 0                                        # outcome-invariant
assert rep["mean_burden_delta"]["hours_after"] < rep["mean_burden_delta"]["hours_before"]
for case in panel["cases"]:                                            # belt and suspenders
    assert reachable_outcomes(tree, case["facts"]).outcomes == \
           reachable_outcomes(new_tree, case["facts"]).outcomes

# prune: a predicate constant on the panel
tree2 = chain_tree()
tree2["nodes"][0]["predicate"]["expr"] = {">": [{"var": "score_e"}, -1]}   # always true here
cands = prune_candidates(tree2, panel)
assert any(c["node"] == "n_exp" and c["always"] is True for c in cands)
collapsed = collapse_node(tree2, "n_exp", True)
assert collapsed["root"] == "n_cheap"
frep = flip_report(tree2, collapsed, panel)
assert not frep["true_flips"] and not frep["determined"]

# substitute: judgment -> objective threshold determines band cases, flips none
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from smoke import mini_tree  # reuse the AB 2533 mini fragment
judg = mini_tree("vA", sanitation_objective=False)
panel2 = {"panel_id": "p2", "generation": {"mode": "fuzz"}, "cases": [
    {"case_id": f"s{i}", "facts": {"construction_year": 2010, "has_toilet": i % 2 == 0, "has_hot_water": i % 3 == 0}}
    for i in range(12)
]}
subbed = substitute(judg, "n_sanitation",
                    {"and": [{"var": "has_toilet"}, {"var": "has_hot_water"}]},
                    ["has_toilet", "has_hot_water"], note="ensemble median cutoff proxy")
frep2 = flip_report(judg, subbed, panel2)
assert frep2["summary"]["n_true_flips"] == 0
assert frep2["summary"]["n_determined"] == 12                          # every band case resolved

print("test_instrument OK")
print(f"  ensemble band recovered: {ens['band_full']} (planted 0.35–0.75), thin sd={tight['cutoff_sd']}")
print(f"  kappa(L) threshold={prof_t}  conjunction={prof_c}  gestalt={prof_g}")
print(f"  reorder: {rep['mean_burden_delta']['hours_before']}h -> {rep['mean_burden_delta']['hours_after']}h, 0 flips")
print(f"  substitution: {frep2['summary']['n_determined']} band cases determined, 0 true flips")
