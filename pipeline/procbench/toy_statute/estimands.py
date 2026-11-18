"""Estimands tied to docs/CORE_GOAL.md: burden per p-step rolled up to d-steps,
process/decision complexity, and counterfactual statute edits.

All functions take a plain parameter dict p (names as in model.param_names)
so the same code computes truth (from truth parameters) and posterior draws.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import expit

from . import grid, spec
from .config import ModelConfig, config_for_params

PRED_QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]


def day_step_pmfs(p, town):
    a = p[f"la_{town}"]
    med = np.array([math.exp(p[f"mu_{s}"] + (a if s in spec.TOWN_SCALED else 0.0)) for s in spec.DAY_STEPS])
    sig = np.array([math.exp(p[f"lsig_{s}"]) for s in spec.DAY_STEPS])
    return grid.discretized_lognormal(med, sig, config_for_params(p).day_grid_size)


def hour_step_pmfs(p):
    med = np.array([math.exp(p[f"muh_{s}"]) for s in spec.HOUR_STEPS])
    sig = np.full(len(spec.HOUR_STEPS), math.exp(p["lsigh"]))
    return grid.discretized_lognormal(med, sig, config_for_params(p).hour_grid_size, grid.HOUR_UNIT)


def _entropy_bits(w):
    w = np.asarray(w, float)
    w = w[w > 0]
    return float(-(w * np.log2(w)).sum())


def total_support_length(config=None):
    """Common full support across designs, so predictive mixtures can be added."""
    config = ModelConfig.parse(config)
    return max(len(spec.chain(s, config.max_loops, int(spec.hearing_possible(s))))
               for s in spec.STRUCTURE_IDS) * (config.day_grid_size - 1) + 1


def total_days_pmf(p, town, s, steps=None):
    if steps is None:
        steps = day_step_pmfs(p, town)
    config = config_for_params(p)
    pk = grid.truncated_geometric(expit(p[f"lpinc_{town}"]), config.max_loops)
    q = expit(p[f"lqobj_{town}"]) if spec.hearing_possible(s) else 0.0
    combos = [(k, h) for k in range(config.max_loops + 1)
              for h in ((0, 1) if spec.hearing_possible(s) else (0,))]
    counts = [spec.segment_counts(spec.chain(s, k, h), "submitted", "decision") for k, h in combos]
    w = np.array([pk[k] * (q if h else (1 - q) if spec.hearing_possible(s) else 1.0) for k, h in combos])
    pm = grid.sum_pmfs(steps, counts, length=total_support_length(config))
    return w @ pm


def town_estimands(p, town, s, fees):
    """Burden/complexity estimands for one town under structure s.

    fees: {"application": a, "notice": n, "inspection": i} (amounts in dollars).
    Returns (flat dict, total-days pmf).
    """
    steps = day_step_pmfs(p, town)
    config = config_for_params(p)
    idays = np.arange(config.day_grid_size)
    mean_d = {st: float(steps[i] @ idays) for i, st in enumerate(spec.DAY_STEPS)}
    hsteps = hour_step_pmfs(p)
    ih = np.arange(config.hour_grid_size) * grid.HOUR_UNIT
    mean_h = {st: float(hsteps[i] @ ih) for i, st in enumerate(spec.HOUR_STEPS)}

    pinc = expit(p[f"lpinc_{town}"])
    pk = grid.truncated_geometric(pinc, config.max_loops)
    Ek = float(pk @ np.arange(config.max_loops + 1))
    hp = spec.hearing_possible(s)
    q = float(expit(p[f"lqobj_{town}"])) if hp else 0.0
    shared = spec.STRUCTURES[s]["shared_decision"]

    out = {}
    d1_steps = spec.D1_STEPS()
    executions = spec.execution_counts(s, Ek, q)
    pd = {st: executions[st] * mean_d[st] for st in spec.DAY_STEPS}
    ph = {st: executions[st] * mean_h[st] for st in spec.HOUR_STEPS}
    active_fees = spec.fee_items(s)
    pdol = {st: (float(fees.get(item, 0.0)) if item in active_fees else 0.0) for st, item in spec.FEE_STEPS.items()}
    for k, v in pd.items():
        out[f"pstep_days.{k}"] = v
    for k, v in ph.items():
        out[f"pstep_hours.{k}"] = v
    for k, v in pdol.items():
        out[f"pstep_dollars.{k}"] = v

    # roll-ups to decision steps from the catalog; a shared decision step (the last middle
    # step also issues the decision) counts in full toward the decision d-step as well
    dec_d = spec.P_STEPS[spec.DECISION_STEP]["d_steps"]
    last_mid = spec.STRUCTURES[s]["d2"][-1].rstrip("?") if shared else None
    for d in spec.D_STEPS:
        did = d["id"]
        for kind, table in (("days", pd), ("hours", ph), ("dollars", pdol)):
            tot_k = 0.0
            for st, v in table.items():
                serves = list(spec.P_STEPS[st]["d_steps"])
                if st == last_mid and did in dec_d:
                    serves = serves + dec_d
                if did in serves:
                    tot_k += v
            out[f"dstep_{kind}.{did}"] = tot_k
    d2_days = out[f"dstep_days.{spec.VAGUE_DSTEP if isinstance(spec.VAGUE_DSTEP, str) else spec.VAGUE_DSTEP[0]}"]
    out["total.hours_mean"] = sum(ph.values())
    out["total.dollars_mean"] = sum(pdol.values())

    tot = total_days_pmf(p, town, s, steps)
    total_days = np.arange(len(tot))
    mean = float(tot @ total_days)
    sd = math.sqrt(max(float(tot @ total_days ** 2) - mean ** 2, 0.0))
    out["total.days_mean"] = mean
    out["total.days_q10"] = grid.quantile_from_pmf(tot, 0.10)
    out["total.days_q50"] = grid.quantile_from_pmf(tot, 0.50)
    out["total.days_q90"] = grid.quantile_from_pmf(tot, 0.90)

    # deadline: complete application -> decision
    hs = (0, 1) if hp else (0,)
    cnt = [spec.segment_counts(spec.chain(s, 0, h), "app_complete", "decision") for h in hs]
    wv = np.array([q if h else 1 - q for h in hs]) if hp else np.array([1.0])
    dl = wv @ grid.sum_pmfs(steps, cnt, length=spec_deadline_index() + 1)
    out["deadline.p_miss"] = float(np.clip(1.0 - dl.sum(), 0, 1))

    n_d2_fixed = sum(1 for x in spec.STRUCTURES[s]["d2"] if not x.endswith("?"))
    n_d1_extra = len([x for x in d1_steps if x not in ("prepare", "completeness_check", "correction")])
    out["complexity.expected_psteps"] = 1 + n_d1_extra + (Ek + 1) + Ek + n_d2_fixed + q + (0 if shared else 1)
    mid_facing = sum(1 for x in spec.STRUCTURES[s]["d2"] if not x.endswith("?")
                     and spec.P_STEPS[x]["applicant_facing"] and x != "hearing")
    out["complexity.applicant_interactions"] = 1 + n_d1_extra + Ek + mid_facing + q
    out["complexity.path_entropy_bits"] = _entropy_bits(pk) + (_entropy_bits([q, 1 - q]) if hp else 0.0)
    out["complexity.cv_total_days"] = sd / mean if mean > 0 else 0.0
    return out, tot


def spec_deadline_index():
    return spec.DEADLINE_DAYS


def counterfactual_available():
    return spec.COUNTERFACTUAL_DESIGN in spec.STRUCTURES


def counterfactual(p, town, cur, fees):
    """The vague step written concretely (hens: 'the authority shall review the site plan', S1).
    The intervention design is statute-specific (spec.COUNTERFACTUAL_DESIGN, set by a package's
    `counterfactual_design`); callers skip it when counterfactual_available() is False."""
    cf, _ = town_estimands(p, town, spec.COUNTERFACTUAL_DESIGN, {"application": fees.get("application", 0.0)})
    return {
        "counterfactual.delta_days_mean": cf["total.days_mean"] - cur["total.days_mean"],
        "counterfactual.delta_hours_mean": cf["total.hours_mean"] - cur["total.hours_mean"],
        "counterfactual.delta_dollars_mean": cf["total.dollars_mean"] - cur["total.dollars_mean"],
    }, cf


def statute_estimands(structs, cur_by_town, cf_by_town):
    labels = [spec.D2_REFINEMENT[s] for s in structs.values()]
    _, counts = np.unique(labels, return_counts=True)
    towns = list(cur_by_town)
    d2 = np.array([cur_by_town[t]["dstep_days.D2"] for t in towns])
    tot = np.array([cur_by_town[t]["total.days_mean"] for t in towns])
    out = {
        "statute.d2_implementation_entropy_bits": _entropy_bits(counts / counts.sum()),
        "statute.d2_days_between_town_sd": float(d2.std()),
    }
    if cf_by_town:
        tot_cf = np.array([cf_by_town[t]["total.days_mean"] for t in towns])
        out["statute.cf_mean_delta_days"] = float((tot_cf - tot).mean())
        out["statute.cf_delta_between_town_sd_days"] = float(tot_cf.std() - tot.std())
    return out


def all_estimands(p, structs, fee_fn):
    """structs: {town: s}; fee_fn(town, s) -> fee dict. Returns (flat dict, pmfs)."""
    flat, pmfs, cur, cfs = {}, {}, {}, {}
    for t, s in structs.items():
        fees = fee_fn(t, s)
        e, tot = town_estimands(p, t, s, fees)
        c = {}
        if counterfactual_available():
            c, cfs[t] = counterfactual(p, t, e, fees)
        cur[t], pmfs[t] = e, tot
        for k, v in {**e, **c}.items():
            flat[f"{t}.{k}"] = v
    flat.update(statute_estimands(structs, cur, cfs))
    return flat, pmfs


def estimand_keys(towns):
    """Canonical flat keys of all scored continuous estimands."""
    dummy_keys = []
    for t in towns:
        for st in spec.DAY_STEPS:
            dummy_keys.append(f"{t}.pstep_days.{st}")
        for st in spec.HOUR_STEPS:
            dummy_keys.append(f"{t}.pstep_hours.{st}")
        for st in spec.FEE_STEPS:
            dummy_keys.append(f"{t}.pstep_dollars.{st}")
        for kind in ("days", "hours", "dollars"):
            for d in spec.D_STEPS:
                dummy_keys.append(f"{t}.dstep_{kind}.{d['id']}")
        for k in ("days_mean", "days_q10", "days_q50", "days_q90", "hours_mean", "dollars_mean"):
            dummy_keys.append(f"{t}.total.{k}")
        dummy_keys.append(f"{t}.deadline.p_miss")
        for k in ("expected_psteps", "applicant_interactions", "path_entropy_bits", "cv_total_days"):
            dummy_keys.append(f"{t}.complexity.{k}")
        if counterfactual_available():
            for k in ("delta_days_mean", "delta_hours_mean", "delta_dollars_mean"):
                dummy_keys.append(f"{t}.counterfactual.{k}")
    dummy_keys += ["statute.d2_implementation_entropy_bits", "statute.d2_days_between_town_sd"]
    if counterfactual_available():
        dummy_keys += ["statute.cf_mean_delta_days", "statute.cf_delta_between_town_sd_days"]
    return dummy_keys
