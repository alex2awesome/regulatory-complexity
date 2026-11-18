"""Truth-side helpers (scorer and tests only): truth parameters -> estimands."""

from __future__ import annotations

import math

from . import estimands
from .model import param_names
from .truth_world import W0


def _logit(p):
    return math.log(p / (1 - p))


def truth_params(world=W0):
    th = {}
    for s, (med, sig) in world["step_days"].items():
        th[f"mu_{s}"] = math.log(med)
        th[f"lsig_{s}"] = math.log(sig)
    for t in world["towns"]:
        th[f"la_{t}"] = math.log(world["town_speed"][t])
        th[f"lpinc_{t}"] = _logit(world["p_incomplete"][t])
        th[f"lqobj_{t}"] = _logit(world["q_objection"][t])
    for s, v in world["hours_median"].items():
        th[f"muh_{s}"] = math.log(v)
    o = world["obs"]
    th.update(lsigh=math.log(world["hours_sigma"]), lsig_r=math.log(o["sigma_report_days"]),
              lsig_rh=math.log(o["sigma_report_hours"]), ldelta=_logit(o["mention_detect"]),
              leps=_logit(o["mention_false"]), llam=_logit(o["web_list"]), lepsw=_logit(o["web_false"]))
    assert set(th) == set(param_names(world["towns"]))
    return th


def truth_estimands(world=W0):
    p = truth_params(world)
    flat, pmfs = estimands.all_estimands(p, dict(world["structure"]), lambda t, s: world["fees"][t])
    for t in world["towns"]:
        for S in ("S1", "S2", "S3", "S4", "S5", "S6"):
            flat[f"{t}.structure_probs.{S}"] = 1.0 if world["structure"][t] == S else 0.0
    return flat, pmfs


def truth_outcome_params(world):
    """Natural-scale outcome parameters in the form outcomes.unpack returns (scalars)."""
    o = world["outcomes"]
    q = {"k1": o["k1"], "k0": o["k0"], "alpha": o["alpha"], "beta": o["beta"], "u": o["u"]}
    for g, short in (("desk_review", "desk"), ("site_inspection", "insp"), ("comment_period", "nb")):
        q[f"d_{short}"], q[f"f_{short}"] = o["d"][g], o["f"][g]
    for t in world["towns"]:
        q[f"pi_{t}"], q[f"m_{t}"] = o["pi"][t], o["m"][t]
    return {k: float(v) for k, v in q.items()}


def truth_burden(world):
    """Truth burden index per town and design (truth process parameters, the town's fee schedule)."""
    from . import outcomes
    p = truth_params(world)
    return {t: outcomes.burden_table(p, t, world["fees"][t]) for t in world["towns"]}


def truth_outcome_estimands(world):
    from . import outcomes
    q = truth_outcome_params(world)
    e = outcomes.outcome_estimands(q, world["towns"], dict(world["structure"]), truth_burden(world))
    return {k: float(v) for k, v in e.items()}
