"""GROUND TRUTH builder for round-4 world W4 (docs/2026-09-29-toy-statute-round4-plan.md).

Twelve towns. Each town draws a true READING of the statute (answers to Q1-Q5) from a
known population distribution, then picks a process design by a known choice model:
cost-softmax among the designs valid under its reading (truth burden index, temperature
TAU), with slack EPS for invalid practice. Process step laws are W0's; town speed,
incompleteness, objection rates and fee schedules are drawn per town.

Generator and scorer only. The fitter never imports this module.
"""

from __future__ import annotations

import copy

import numpy as np

from . import estimands, outcomes, readings, spec, validity
from .truth_world import W0

TOWNS = ["Alder", "Birch", "Cedar", "Dogwood", "Elm", "Fir", "Ginkgo", "Hazel", "Ironwood", "Juniper", "Kapok", "Larch"]
READING_PROBS = {"Q1_desk_sufficient": 0.6, "Q2_neighbor_input_required": 0.35, "Q3_investigative_power": 0.9,
                 "Q4_clock_includes_d2": 0.8, "Q5_separate_fees": 0.5}
TAU, EPS = 15.0, 0.05
SEED = 20261004


def _truth_params_for(world):
    from .truth_eval import truth_params
    return truth_params(world)


def make_w4(seed=SEED):
    spec.use_design_space("full")
    rng = np.random.default_rng(seed)
    w = copy.deepcopy(W0)
    w.update({"world_id": "W4", "seed": seed, "design_space": "full", "towns": list(TOWNS)})
    w["town_speed"] = {t: float(np.exp(rng.normal(0.0, 0.25))) for t in TOWNS}
    w["p_incomplete"] = {t: float(rng.uniform(0.08, 0.35)) for t in TOWNS}
    w["q_objection"] = {t: float(rng.uniform(0.15, 0.30)) for t in TOWNS}
    fees = {}
    for t in TOWNS:
        f = {"application": int(rng.integers(25, 61))}
        if rng.random() < 0.5:
            f["notice"] = int(rng.integers(10, 21))
        if rng.random() < 0.5:
            f["inspection"] = int(rng.integers(30, 61))
        fees[t] = f
    w["fees"] = fees
    # readings
    rd = {t: {q: bool(rng.random() < p) for q, p in READING_PROBS.items()} for t in TOWNS}
    w["readings"] = rd
    w["reading_probs"] = dict(READING_PROBS)
    # choice: cost-softmax within the valid set, slack EPS
    R = readings.all_readings()
    V = readings.validity_matrix()
    p = _truth_params_for(w)
    struct, choice_info = {}, {}
    for t in TOWNS:
        cost = np.array([outcomes.burden_index(estimands.town_estimands(p, t, s, fees[t])[0]) for s in spec.STRUCTURE_IDS])
        ri = next(i for i, r in enumerate(R) if all(r[q] == rd[t][q] for q in readings.QUESTIONS))
        valid = V[ri]
        pref = np.exp(-(cost - cost.min()) / TAU) * valid
        probs = EPS / len(cost) + (1 - EPS) * pref / pref.sum()
        s = spec.STRUCTURE_IDS[rng.choice(len(cost), p=probs)]
        struct[t] = s
        choice_info[t] = {"valid_designs": [spec.STRUCTURE_IDS[j] for j in np.where(valid)[0]],
                          "burden_index": {sid: float(c) for sid, c in zip(spec.STRUCTURE_IDS, cost)},
                          "chosen_valid": bool(valid[spec.STRUCTURE_IDS.index(s)])}
    w["structure"] = struct
    w["choice_model"] = {"model": "cost", "tau": TAU, "eps": EPS, "per_town": choice_info}
    admin = list(rng.choice(TOWNS, size=6, replace=False))
    w["design"] = dict(W0["design"], admin_towns=[str(x) for x in admin], admin_n=40, reports_per_town=15,
                       heldout_n=500, forced_web_omissions={})
    w.pop("outcomes", None)
    return w
