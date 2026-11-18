"""GROUND TRUTH builder for any statute package with a `truth` block (round 5+).

Implements the author's declared rules: per-town covariate (density), readings per town
(independent questions; a covariate-dependent rule for the threshold question), expected
fees from the fee reading, cost-softmax design choice among designs valid under the
town's reading (author validity rules), realized fee schedule conditional on the reading,
and per-town process parameters. Generator and scorer only; the fitter never imports it.

The world dict it returns is consumed by generate.generate(); it also carries
"package_path" so generate/spec load the statute first.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import expit

from . import spec, validity_rules


def _range(v):
    return (int(v[0]), int(v[1]))


KITCHEN_ITEMS = {"inspection": {"step": "site_inspection"}, "lab": {"step": "product_lab_test"},
                 "zoning": {"step": "zoning_clearance", "requires": {"Q1_significant_traffic": True}},
                 "notice": {"step": "neighbor_notice", "requires": {"Q1_significant_traffic": True, "Q2_hosa_imports_procedure": True}}}


def expected_fees(reading, fees_rule, design_steps, rng=None, realize=False):
    """Fee schedule implied by a reading (midpoints) or realized (draws), per the package's fee rule:
    fees_rule["fee_question"] (default Q7_separate_fees) says whether separate items are authorized;
    fees_rule["items"] maps item -> {"step", "requires": {qid: bool}} (default: the kitchen convention)."""
    rg = fees_rule["ranges"]
    fq = fees_rule.get("fee_question", "Q7_separate_fees")
    items = fees_rule.get("items", KITCHEN_ITEMS)
    q7 = reading.get(fq, False)
    draw = (lambda lo, hi: int(rng.integers(lo, hi + 1))) if realize else (lambda lo, hi: (lo + hi) / 2)
    f = {}
    if q7:
        f["application"] = draw(*_range(rg["application_if_Q7_yes"]))
        for item, spec_ in items.items():
            if spec_["step"] not in design_steps or item not in rg:
                continue
            if any(bool(reading.get(q, False)) != bool(v) for q, v in spec_.get("requires", {}).items()):
                continue
            if realize and rng.random() >= fees_rule.get("p_charge_item", 0.8):
                continue
            f[item] = draw(*_range(rg[item]))
    else:
        f["application"] = draw(*_range(rg["application_if_Q7_no"]))
        if realize and rng.random() < fees_rule.get("fee_eps", 0.0):
            for item, spec_ in items.items():
                if spec_["step"] in design_steps and item in rg:
                    f[item] = draw(*_range(rg[item]))
                    f["_phantom_fee"] = item
                    break
    if "course" in rg:
        f["course"] = draw(*_range(rg["course"]))
    return f


def burden_index_truth(p, town, sid, fees):
    from . import estimands, outcomes
    return outcomes.burden_index(estimands.town_estimands(p, town, sid, fees)[0])


def make_world(package_path, seed=None, agencies_path=None, world_id=None):
    """agencies_path: shared-agency file (round 6): per town density, log speed, incompleteness,
    objection base, choice temperature tau and interpretive strictness s. When given, these replace
    the package's per-town draws, and each question's P(yes) is shifted by +/- s according to the
    question's "strict_answer" flag (yes strict -> +s; no strict -> -s; null -> no shift)."""
    pkg = json.loads(Path(package_path).read_text())
    spec.load_package(pkg)
    t = pkg["truth"]
    seed = seed if seed is not None else t["seed"]
    rng = np.random.default_rng(seed)
    ag = json.loads(Path(agencies_path).read_text())["agencies"] if agencies_path else None
    towns = list(ag) if ag else list(t["towns"])
    w = {"world_id": world_id or t["world_id"], "seed": seed, "package_path": str(package_path), "towns": towns,
         "step_days": {k: tuple(v) for k, v in t["step_days"].items()},
         "hours_median": dict(t["hours_median"]), "hours_sigma": float(t["hours_sigma"]),
         "obs": dict(t["obs"]), "agencies_path": str(agencies_path) if agencies_path else None}
    if ag:
        dens = {tn: float(ag[tn]["density"]) for tn in towns}
        w["town_speed"] = {tn: float(np.exp(ag[tn]["log_speed"])) for tn in towns}
        w["p_incomplete"] = {tn: float(ag[tn]["p_incomplete"]) for tn in towns}
        w["q_objection"] = {tn: float(ag[tn]["q_objection_base"] + 0.20 * dens[tn]) for tn in towns}
        w["agency_traits"] = {tn: dict(ag[tn]) for tn in towns}
    else:
        dens = t["density_or_local_covariate"]["by_town"]
        w["town_speed"] = {tn: float(np.exp(rng.normal(0.0, 0.25))) for tn in towns}
        w["p_incomplete"] = {tn: float(rng.uniform(0.12, 0.35)) for tn in towns}
        w["q_objection"] = {tn: float(0.08 + 0.20 * dens[tn]) for tn in towns}
    w["density"] = {k: float(v) for k, v in dens.items()}
    # readings
    rp = t["reading_probs"]
    qids = [q["id"] for q in pkg["questions"]]
    strict = {q["id"]: q.get("strict_answer") for q in pkg["questions"]}
    readings, reading_p = {}, {}
    for tn in towns:
        r, rpt = {}, {}
        for q in qids:
            v = rp[q]
            if isinstance(v, dict) and "rule_logit" in v:  # e.g. {"rule_logit": [a, b]}: P = expit(a + b*density)
                a, b = v["rule_logit"]
                p = float(expit(a + b * dens[tn]))
            else:
                p = float(v["by_town"][tn]) if isinstance(v, dict) else float(v)
            if ag and strict.get(q) is not None:
                sgn = 1.0 if strict[q] else -1.0
                p = float(expit(np.log(p / (1 - p)) + sgn * float(ag[tn]["strictness"])))
            rpt[q] = p
            r[q] = bool(rng.random() < p)
        readings[tn] = r
        reading_p[tn] = rpt
    w["readings"] = readings
    w["reading_p_by_town"] = reading_p
    w["readings"] = readings
    w["reading_probs"] = {q: float(np.mean([reading_p[tn][q] for tn in towns])) for q in qids}  # realized-town mean of P(yes)
    # validity under author rules, choice by cost-softmax with expected fees
    from .truth_eval import truth_params
    V = validity_rules.author_validity_matrix(pkg["validity_rules"], qids)
    R = validity_rules.all_readings(qids)
    idx = {tuple(r[q] for q in qids): i for i, r in enumerate(R)}
    cm = t["choice_model"]
    tau0, eps = float(cm["tau"]), float(cm["eps"])
    p_params = truth_params(w)
    struct, info, fees = {}, {}, {}
    for tn in towns:
        valid = V[idx[tuple(readings[tn][q] for q in qids)]]
        costs = []
        for sid in spec.STRUCTURE_IDS:
            steps = [x.rstrip("?") for x in spec.STRUCTURES[sid]["d2"]]
            ef = expected_fees(readings[tn], t["fees"], steps)
            ef = {k: v for k, v in ef.items() if not k.startswith("_")}
            costs.append(burden_index_truth(p_params, tn, sid, ef))
        costs = np.array(costs)
        tau = float(ag[tn]["tau"]) if ag else tau0
        pref = np.exp(-(costs - costs.min()) / tau) * valid
        probs = eps / len(costs) + (1 - eps) * (pref / pref.sum() if pref.sum() > 0 else valid / max(valid.sum(), 1))
        j = int(rng.choice(len(costs), p=probs))
        sid = spec.STRUCTURE_IDS[j]
        struct[tn] = sid
        steps = [x.rstrip("?") for x in spec.STRUCTURES[sid]["d2"]]
        fees[tn] = expected_fees(readings[tn], t["fees"], steps, rng=rng, realize=True)
        info[tn] = {"valid_designs": [spec.STRUCTURE_IDS[j] for j in np.where(valid)[0]],
                    "burden_index": {s_: float(c) for s_, c in zip(spec.STRUCTURE_IDS, costs)},
                    "chosen_valid": bool(valid[j]), "p_chosen": float(probs[j]),
                    "choice_probs": {s_: float(pp) for s_, pp in zip(spec.STRUCTURE_IDS, probs)},
                    "phantom_fee": fees[tn].get("_phantom_fee")}
    w["structure"] = struct
    w["fees"] = {tn: {k: v for k, v in f.items() if not k.startswith("_")} for tn, f in fees.items()}
    w["choice_model"] = {"model": cm["model"], "tau": tau0 if not ag else "per-agency", "eps": eps, "per_town": info}
    ed = t["evidence_design"]
    n_admin = int(str(ed["admin_towns"]).split()[0]) if isinstance(ed["admin_towns"], str) else len(ed["admin_towns"])
    admin = [str(x) for x in rng.choice(towns, size=n_admin, replace=False)]
    w["design"] = {"admin_towns": admin, "admin_n": ed["admin_n"], "reports_per_town": ed["reports_per_town"],
                   "post_day_range": ed["post_day_range"], "p_time_mentioned_event": ed["p_time_mentioned_event"],
                   "p_total_only": ed["p_total_only"], "p_report_hours": ed["p_report_hours"],
                   "p_report_fees": ed["p_report_fees"], "heldout_n": ed["heldout_n"],
                   "forced_web_omissions": ed.get("forced_web_omissions", {})}
    return w
