"""GROUND TRUTH for toy world W0. Generator and scorer only.

The fitter (model.py, fit.py) and the LLM baseline must never import this
module; tests/test_toy_statute.py enforces that statically.
"""

W0 = {
    "world_id": "W0",
    "seed": 20260926,
    "towns": ["Alder", "Birch", "Cedar"],
    "structure": {"Alder": "S1", "Birch": "S3", "Cedar": "S4"},
    # elapsed-day steps: (median days at speed 1.0, lognormal sigma)
    "step_days": {
        "completeness_check": (5.0, 0.5),
        "correction": (7.0, 0.6),
        "neighbor_notice": (2.0, 0.3),
        "comment_period": (14.0, 0.01),   # fixed by local rule
        "desk_review": (10.0, 0.5),
        "hearing": (21.0, 0.3),
        "site_inspection": (12.0, 0.4),
        "decision_issue": (4.0, 0.5),
    },
    "town_speed": {"Alder": 1.0, "Birch": 1.3, "Cedar": 0.9},
    "p_incomplete": {"Alder": 0.10, "Birch": 0.15, "Cedar": 0.35},
    "q_objection": {"Alder": 0.20, "Birch": 0.20, "Cedar": 0.25},  # only used where a hearing is possible
    # applicant hours: median, shared sigma
    "hours_median": {"prepare": 3.0, "correction": 2.0, "site_inspection": 1.5, "hearing": 3.0},
    "hours_sigma": 0.5,
    "fees": {
        "Alder": {"application": 25},
        "Birch": {"application": 50, "inspection": 40},
        "Cedar": {"application": 40, "notice": 15},
    },
    "obs": {
        "sigma_report_days": 0.25,
        "sigma_report_hours": 0.30,
        "mention_detect": 0.70,
        "mention_false": 0.03,
        "web_list": 0.85,
        "web_false": 0.03,
        "contamination": 0.02,
    },
    "design": {
        "admin_towns": ["Alder", "Cedar"],
        "admin_n": 40,
        "reports_per_town": 15,
        "post_day_range": [10, 150],   # report posted this many days after submission (independent of outcome)
        "p_time_mentioned_event": 0.7,
        "p_total_only": 0.2,
        "p_report_hours": 0.6,
        "p_report_fees": 0.5,
        "forced_web_omissions": {"Birch": ["site_inspection"]},
        "heldout_n": 2000,
    },
}


# ---- Round 2 worlds (docs/2026-09-26-toy-statute-round2-plan.md) -------------
import copy as _copy

# W1: adversarial to "common sense" priors — same statute, different structures,
# step scales far from typical US-municipal intuition (local rules, backlog).
W1 = _copy.deepcopy(W0)
W1.update({
    "world_id": "W1",
    "seed": 20260929,
    "structure": {"Alder": "S2", "Birch": "S6", "Cedar": "S1"},
    "step_days": {
        "completeness_check": (1.5, 0.5),
        "correction": (20.0, 0.6),
        "neighbor_notice": (18.0, 0.3),     # certified mail + posting rule
        "comment_period": (30.0, 0.01),
        "desk_review": (35.0, 0.5),          # backlog
        "hearing": (45.0, 0.3),
        "site_inspection": (5.0, 0.4),
        "decision_issue": (12.0, 0.5),
    },
    "town_speed": {"Alder": 1.0, "Birch": 0.7, "Cedar": 1.5},
    "p_incomplete": {"Alder": 0.50, "Birch": 0.05, "Cedar": 0.20},
    "q_objection": {"Alder": 0.20, "Birch": 0.40, "Cedar": 0.20},
    "hours_median": {"prepare": 12.0, "correction": 6.0, "site_inspection": 4.0, "hearing": 5.0},
    "fees": {
        "Alder": {"application": 150, "inspection": 200},
        "Birch": {"application": 10, "notice": 60},
        "Cedar": {"application": 300},
    },
})
W1["design"] = dict(W0["design"], admin_towns=["Birch", "Cedar"],
                    forced_web_omissions={"Birch": ["neighbor_notice"]})


def scaled(world, factor, seed, wid):
    """Same truth, `factor` times the evidence (fresh draws)."""
    w = _copy.deepcopy(world)
    w["world_id"] = wid
    w["seed"] = seed
    w["design"] = dict(world["design"], admin_n=world["design"]["admin_n"] * factor,
                       reports_per_town=world["design"]["reports_per_town"] * factor)
    return w


W0x5 = scaled(W0, 5, 20260930, "W0x5")
W0x25 = scaled(W0, 25, 20260931, "W0x25")


def with_milestones(world, wid):
    """Same truth and same seed (same cases); admin records also log status-change milestones."""
    w = _copy.deepcopy(world)
    w["world_id"] = wid
    w["design"] = dict(world["design"], admin_milestones=True)
    return w


W0m = with_milestones(W0, "W0m")
W1m = with_milestones(W1, "W1m")

# ---- Outcome worlds (docs/2026-09-28-toy-statute-outcomes-plan.md) -----------
# Same process world and seed as W0 (byte-identical process evidence); the outcome
# layer is generated from a separate RNG stream.
OUTCOMES_COMMON = {
    "pi": {"Alder": 0.15, "Birch": 0.15, "Cedar": 0.15},       # nuisance incidence
    "d": {"desk_review": 0.35, "site_inspection": 0.75, "comment_period": 0.55},  # catch a nuisance
    "f": {"desk_review": 0.02, "site_inspection": 0.03, "comment_period": 0.06},  # flag a harmless coop
    "k1": 0.80, "k0": 0.05,          # P(>=1 complaint over the period | nuisance / harmless)
    "alpha": 0.8, "beta": 0.04,      # p_apply = expit(alpha - beta (B - B_REF))
    "u": 0.40,                       # non-applicants / denied who keep hens anyway
    "m": {"Alder": 600, "Birch": 700, "Cedar": 500},            # would-be keepers over the period
    "households": {"Alder": 5000, "Birch": 6000, "Cedar": 4500},
    "survey_n": 400, "period_years": 3, "seed_offset": 7919,
}
# Adversarial: nuisance incidence differs by town and is highest where towns inspect
# (confounding); inspections perfunctory, desk review strong; steep deterrence.
OUTCOMES_ADV = dict(OUTCOMES_COMMON,
    pi={"Alder": 0.05, "Birch": 0.30, "Cedar": 0.15},
    d={"desk_review": 0.60, "site_inspection": 0.25, "comment_period": 0.70},
    f={"desk_review": 0.05, "site_inspection": 0.01, "comment_period": 0.15},
    k1=0.50, k0=0.10, alpha=0.3, beta=0.08, u=0.70,
    m={"Alder": 400, "Birch": 900, "Cedar": 600})


def with_outcomes(world, outcomes, wid):
    w = _copy.deepcopy(world)
    w["world_id"] = wid
    w["outcomes"] = _copy.deepcopy(outcomes)
    return w


W0o = with_outcomes(W0, OUTCOMES_COMMON, "W0o")
W0o_adv = with_outcomes(W0, OUTCOMES_ADV, "W0o_adv")
WORLDS = {"W0": W0, "W1": W1, "W0x5": W0x5, "W0x25": W0x25, "W0m": W0m, "W1m": W1m,
          "W0o": W0o, "W0o_adv": W0o_adv}
