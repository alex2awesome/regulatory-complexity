"""Uncertain, globally shared interpretation spaces, using the sole Stage-C kernel.

No author packages, truth, or question-to-truth mapping are read here. Conditional
on equal-weight Stage-B posterior particles with a uniform design prior, integrate
each H first, then mix H outside the product over towns. Finite-kappa integration
is Monte Carlo; no diagnostic below makes it exact or establishes identification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from . import readings, validity_rules

UNKNOWN = "unknown"
DEFAULT_CHOICES = (("uniform", {}), ("cost", {"tau": 15.}), ("cost", {"tau": 40.}),
                   ("risk", {"beta": 2.}), ("risk", {"beta": 5.}))


@dataclass
class Hypothesis:
    id: str
    V: np.ndarray
    qids: tuple[str, ...]
    qprobs: dict[str, float]
    design_ids: tuple[str, ...]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.V = np.asarray(self.V)
        if self.V.dtype != bool or self.V.shape != (2 ** len(self.qids), len(self.design_ids)):
            raise ValueError("V must be Boolean, with one row per binary reading and one column per design")
        if not self.design_ids or len(set(self.design_ids)) != len(self.design_ids):
            raise ValueError("nonempty unique design ids required")
        if len(set(self.qids)) != len(self.qids) or set(self.qids) != set(self.qprobs):
            raise ValueError("question ids/probabilities do not agree")
        if any(not np.isfinite(p) or not 0 <= p <= 1 for p in self.qprobs.values()):
            raise ValueError("p_yes must be finite and in [0,1]")


def from_reader(obj, design_ids, reader_id, metadata=None):
    """Strict at this boundary: missing judgements must not silently mean lawful."""
    qs = obj["questions"]
    if not isinstance(qs, list) or any(type(q.get("major")) is not bool for q in qs):
        raise ValueError("questions must declare Boolean major")
    ids = [q["id"] for q in qs]
    if len(set(ids)) != len(ids) or any(not isinstance(q, str) or not q for q in ids):
        raise ValueError("duplicate or empty question id")
    major = [q["id"] for q in qs if q["major"]]
    if len(major) > 7:
        raise ValueError("at most seven major questions")
    for q in qs:
        if isinstance(q["p_yes"], bool) or not np.isfinite(q["p_yes"]) or not 0 <= q["p_yes"] <= 1:
            raise ValueError("invalid question probability")
    for sid in design_ids:
        entry = obj["design_validity"][sid]
        per = entry.get("per_question", entry.get("questions", entry))
        for q in major:
            if any(type(per[q][k]) is not bool for k in ("valid_if_yes", "valid_if_no")):
                raise ValueError(f"{sid}/{q}: explicit Boolean yes/no required")
    V, qids = validity_rules.reader_validity_matrix(obj, list(design_ids))
    meta = dict(metadata or {})
    meta["meta_rule"] = obj.get("meta_rule")
    meta["compiler_semantics"] = "conjunction of per-question flags; free-text joint rules not executed"
    return Hypothesis(reader_id, V, tuple(qids), validity_rules.reader_question_probs(obj), tuple(design_ids), meta)


def load_hypotheses(directory, design_ids, *, failures=None):
    """Load */reading.json once. Invalid readers are excluded and errors are explicit.

    If failures is omitted, raise on any invalid reader (never silently drop it).
    Caller can pass a list to retain failures and proceed with valid readers.
    """
    out, errors = [], []
    for path in sorted(Path(directory).glob("*/reading.json")):
        try:
            mp = path.with_name("metadata.json")
            meta = json.loads(mp.read_text()) if mp.exists() else {"provenance_missing": True}
            if meta.get("status") == "failed":
                raise ValueError("reader previously failed validation; excluded without manual repair")
            out.append(from_reader(json.loads(path.read_text()), design_ids, path.parent.name, meta))
        except (ValueError, KeyError, TypeError) as exc:
            errors.append({"reader": path.parent.name, "error": str(exc)})
    if failures is None and errors:
        raise ValueError(f"invalid readers: {errors}")
    if failures is not None:
        failures.extend(errors)
    return out


def _prior(h, rho):
    if not np.isfinite(rho) or not 0 <= rho <= 1:
        raise ValueError("rho must be in [0,1]")
    p = np.array([np.prod([h.qprobs[q] if r[q] else 1-h.qprobs[q] for q in h.qids])
                  for r in readings.all_readings_for(h.qids)])
    return np.r_[p / p.sum() * (1-rho), rho]


def _components(h, rho, kappa=None):
    V, inverse = np.unique(h.V, axis=0, return_inverse=True)
    original = _prior(h, rho)
    mass = original if kappa is None else np.maximum(kappa * original, 1e-6)
    grouped = np.r_[np.bincount(inverse, weights=mass[:-1], minlength=len(V)), mass[-1]]
    return V, grouped


def canonical(h, rho=0.05):
    """Sorted lawful-set patterns and nominal prior masses; unknown remains separate."""
    V, mass = _components(h, rho)
    return ["".join(str(int(b)) for b in row) for row in V] + [UNKNOWN], mass


def equivalence_classes(hypotheses, rho=0.05, kappas=(None, 10.), include_risk=True, atol=1e-12):
    """Conservative grid-wide classes: sets + risk profile + floored alpha masses.

    Equal masses alone are insufficient for the existing risk-choice model. These
    classes guarantee equivalence; additional observational equivalences may exist
    (e.g. no-lawful-design choice and residual both select uniformly).
    """
    signatures = []
    for h in hypotheses:
        patterns, _ = canonical(h, rho)
        values = np.concatenate([_components(h, rho, k)[1] for k in kappas] +
                                ([h.V.mean(axis=0)] if include_risk else []))
        signatures.append((h.design_ids, patterns, values))
    classes = []
    for i, (ids, patterns, values) in enumerate(signatures):
        for group in classes:
            ids0, patterns0, values0 = signatures[group[0]]
            if ids == ids0 and patterns == patterns0 and np.allclose(values, values0, atol=atol, rtol=0):
                group.append(i)
                break
        else:
            classes.append([i])
    return classes


def _choice(h, V, cm, kw, eps, cost):
    if cm == "risk":
        # Compute on ORIGINAL reading measure, then select canonical rows.
        _, indices = np.unique(h.V, axis=0, return_index=True)
        raw = readings.choice_logprob(h.V, cm, eps, **kw)
        return raw[np.r_[indices, len(h.V)]]
    if cm != "cost":
        return readings.choice_logprob(V, cm, eps, **kw)
    return np.stack([np.stack([readings.choice_logprob(V, cm, eps, cost=c, **kw) for c in row]) for row in cost])


def _integrate(L, cost, h, cm, kw, eps, kappa, rho, n_w, seed, chunk_size, return_joint):
    """Chunk particles, reusing the SAME population draws across every chunk."""
    V, mass = _components(h, rho, kappa)
    prior = mass if kappa is None else mass / kappa
    chunks, log_weights, sizes = [], [], []
    for start in range(0, len(L), chunk_size):
        stop = min(start+chunk_size, len(L))
        lc = _choice(h, V, cm, kw, eps, None if cost is None else cost[start:stop])
        res = readings.stage_c(L[start:stop], prior, lc, kappa=kappa, n_w=n_w,
                               rng=np.random.default_rng(seed), return_joint=return_joint)
        chunks.append(res)
        sizes.append(stop-start)
        log_weights.append(res["log_marginal_ratio"] + np.log(stop-start))
    z = logsumexp(log_weights)
    weights = np.exp(np.array(log_weights)-z)
    out = {"log_marginal_ratio": float(z-np.log(len(L))),
           "ess_joint": float(1 / sum(w*w / r["ess"] for w, r in zip(weights, chunks)))}
    for key in ("town_reading", "town_design", "population_weights"):
        out[key] = sum(w*r[key] for w, r in zip(weights, chunks))
    out["particle_weights"] = np.concatenate([w*r["particle_weights"] for w, r in zip(weights, chunks)])
    out["ess_particles"] = float(1 / np.square(out["particle_weights"]).sum())
    if return_joint:
        out["particle_town_design"] = np.concatenate([w*r["particle_town_design"] for w, r in zip(weights, chunks)])
    out["patterns"] = canonical(h, rho)[0]
    # Canonical reading rows ARE lawful-set states, including an unknown residual.
    out["town_sets"] = out.pop("town_reading")
    return out


def run_hypotheses(L, cost, Hs, choice_grid=DEFAULT_CHOICES, eps_grid=(.05, .15, .30),
                   kappas=(None, 10.), *, rho=.05, n_w=200, seed=20260930,
                   chunk_size=32, return_joint=False):
    L = np.asarray(L, float)
    if L.ndim != 3 or min(L.shape) == 0 or np.isnan(L).any() or np.isposinf(L).any() or not np.isfinite(logsumexp(L, axis=2)).all():
        raise ValueError("L must be [N,T,D] with positive finite support per particle/town")
    if not Hs or len({h.id for h in Hs}) != len(Hs):
        raise ValueError("nonempty unique hypothesis ids required")
    if any(h.design_ids != Hs[0].design_ids or h.V.shape[1] != L.shape[2] for h in Hs):
        raise ValueError("hypotheses must share the ordered design menu of L")
    if not choice_grid or not eps_grid or not kappas or any(not 0 < e <= 1 for e in eps_grid):
        raise ValueError("nonempty grid required, with 0 < epsilon <= 1")
    if any(k is not None and (not np.isfinite(k) or k <= 0) for k in kappas):
        raise ValueError("kappa must be None or positive finite")
    if chunk_size <= 0 or n_w <= 0:
        raise ValueError("positive chunk size and n_w required")
    for cm, kw in choice_grid:
        allowed = {"uniform": set(), "cost": {"tau"}, "risk": {"beta"}}
        if cm not in allowed or set(kw)-allowed[cm] or any(not np.isfinite(v) or v <= 0 for v in kw.values()):
            raise ValueError("invalid choice model or parameters")
    if any(cm == "cost" for cm, _ in choice_grid):
        cost = np.asarray(cost, float)
        if cost.shape != L.shape or not np.isfinite(cost).all():
            raise ValueError("cost choice requires finite cost array shaped like L")
    groups = equivalence_classes(Hs, rho, kappas, any(cm == "risk" for cm, _ in choice_grid))
    cells = []
    for cm, kw in choice_grid:
        for eps in eps_grid:
            for kappa in kappas:
                cells.append({"model": cm, **kw, "epsilon": eps, "kappa": kappa})
    # No per-H or per-psi subsampling. The same L is used throughout.
    runs = {}
    for group in groups:
        h = Hs[group[0]]
        result = [_integrate(L, cost, h, cell["model"],
                            {k: v for k, v in cell.items() if k in ("tau", "beta")},
                            cell["epsilon"], cell["kappa"], rho, n_w, seed, chunk_size, return_joint)
                  for cell in cells]
        for i in group:
            runs[Hs[i].id] = result  # shared calculation, no fake Monte Carlo Bayes factors
    return {"hypothesis_ids": [h.id for h in Hs], "design_ids": list(Hs[0].design_ids),
            "classes": [[Hs[i].id for i in g] for g in groups], "psi": cells, "runs": runs,
            "hypotheses": {h.id: {"qids": list(h.qids), "qprobs": h.qprobs, "metadata": h.metadata,
                                    "patterns": canonical(h, rho)[0], "prior_masses": canonical(h, rho)[1],
                                    "prior_masses_by_psi": [(_components(h, rho, c["kappa"])[1] /
                                                             _components(h, rho, c["kappa"])[1].sum()) for c in cells]} for h in Hs},
            "settings": {"rho": rho, "n_w": n_w, "seed": seed, "chunk_size": chunk_size, "n_particles": len(L),
                         "population_integration": "Monte Carlo for finite kappa; analytical independent towns",
                         "ess_warning": "importance ESS, not independent posterior sample size or convergence"}}


def class_prior(results):
    sizes = {h: len(c) for c in results["classes"] for h in c}
    return np.array([1 / (len(results["classes"])*sizes[h]) for h in results["hypothesis_ids"]])


def _lawful_summary(patterns, mass, D):
    values = np.array([[int(b) for b in p] if p != UNKNOWN else [0]*D for p in patterns])
    lower = mass @ values
    unknown = mass[:, patterns.index(UNKNOWN)]
    known = 1-unknown
    conditional = np.divide(lower, known[:, None], out=np.full_like(lower, np.nan), where=known[:, None] > 1e-15)
    return {"patterns": patterns, "town_sets": mass, "town_lawful_given_known": conditional,
            "town_lawful_lower": lower, "town_lawful_upper": lower+unknown[:, None], "town_unknown": unknown}


def bma(results, prior_over_H=None):
    """Weight H and psi by their JOINT evidence. psi has a uniform grid prior."""
    ids, cells = results["hypothesis_ids"], results["psi"]
    prior = np.full(len(ids), 1/len(ids)) if prior_over_H is None else np.asarray(prior_over_H, float)
    if prior.shape != (len(ids),) or not np.isfinite(prior).all() or np.any(prior < 0) or prior.sum() <= 0:
        raise ValueError("invalid hypothesis prior")
    prior = prior/prior.sum()
    with np.errstate(divide="ignore"):
        lp = np.log(prior)
    Z = np.array([[r["log_marginal_ratio"] for r in results["runs"][h]] for h in ids])
    if not np.isfinite(Z).all():
        raise ValueError("nonfinite hypothesis evidence")
    joint_log = Z+lp[:, None]-np.log(len(cells))
    log_z = logsumexp(joint_log)
    joint = np.exp(joint_log-log_z)
    cond = np.exp(Z+lp[:, None]-logsumexp(Z+lp[:, None], axis=0))
    patterns = sorted({p for h in ids for p in results["runs"][h][0]["patterns"] if p != UNKNOWN})+[UNKNOWN]
    index = {p: j for j, p in enumerate(patterns)}
    first = results["runs"][ids[0]][0]
    td = np.zeros_like(first["town_design"], dtype=float)
    sets = np.zeros((len(td), len(patterns)))
    pw = np.zeros_like(first["particle_weights"], dtype=float)
    pd = np.zeros_like(first["particle_town_design"], dtype=float) if "particle_town_design" in first else None
    for hi, h in enumerate(ids):
        for ci, res in enumerate(results["runs"][h]):
            w = joint[hi, ci]
            td += w*np.asarray(res["town_design"])
            sets[:, [index[p] for p in res["patterns"]]] += w*np.asarray(res["town_sets"])
            pw += w*np.asarray(res["particle_weights"])
            if pd is not None:
                pd += w*np.asarray(res["particle_town_design"])
    out = {"hypothesis_ids": ids, "prior_H": prior, "posterior_H": joint.sum(axis=1),
           "posterior_psi": joint.sum(axis=0), "posterior_H_given_psi": cond,
           "posterior_H_psi": joint, "log_marginal_ratio": float(log_z),
           "town_design": td, "particle_weights": pw, "ess_particles": float(1/np.square(pw).sum()),
           **_lawful_summary(patterns, sets, td.shape[1])}
    if pd is not None:
        out["particle_town_design"] = pd
    return out


def prior_lawful_bma(results, prior_over_H=None):
    """No-data lawful-set prior, not posterior-conditioned H weights with data erased."""
    ids = results["hypothesis_ids"]
    prior = np.ones(len(ids)) if prior_over_H is None else np.asarray(prior_over_H, float)
    if prior.shape != (len(ids),) or not np.isfinite(prior).all() or np.any(prior < 0) or prior.sum() <= 0:
        raise ValueError("invalid hypothesis prior")
    prior = prior/prior.sum()
    patterns = sorted({p for h in ids for p in results["hypotheses"][h]["patterns"] if p != UNKNOWN})+[UNKNOWN]
    vec = np.zeros(len(patterns))
    for w, h in zip(prior, ids):
        hs = results["hypotheses"][h]
        mass = np.mean(hs["prior_masses_by_psi"], axis=0) if "prior_masses_by_psi" in hs else np.asarray(hs["prior_masses"])
        vec[[patterns.index(p) for p in hs["patterns"]]] += w*mass
    T = len(results["runs"][ids[0]][0]["town_design"])
    return _lawful_summary(patterns, np.tile(vec, (T, 1)), len(results["design_ids"]))


def estimand_summary(joint, values, quantiles=(.05, .5, .95)):
    """Summarize a conditional estimand value for each (particle,town,design).

    This is uncertainty in conditional estimands, NOT a predictive case-duration
    interval. No product of marginal weights is used.
    """
    joint, values = np.asarray(joint, float), np.asarray(values, float)
    if values.shape != joint.shape or joint.ndim != 3 or not np.isfinite(values).all():
        raise ValueError("joint/values must be finite matching [N,T,D] arrays")
    if not np.isfinite(joint).all() or np.any(joint < 0) or not np.allclose(joint.sum(axis=(0, 2)), 1):
        raise ValueError("joint weights must sum to one for each town")
    means = (joint*values).sum(axis=(0, 2))
    qs = []
    for ti in range(joint.shape[1]):
        v, w = values[:, ti].ravel(), joint[:, ti].ravel()
        ix = np.argsort(v)
        cdf = np.cumsum(w[ix])
        qs.append([float(v[ix[min(np.searchsorted(cdf, q), len(ix)-1)]]) for q in quantiles])
    return {"mean": means, "quantiles": list(quantiles), "values": np.asarray(qs),
            "interval_kind": "conditional estimand uncertainty, not predictive case interval"}


def conditional_burdens(model, particles, seed=20260930):
    """Catalog mean burdens for BMA, without recomputing whole-process CDFs.

    Same execution counts, discretized step means, fee-table rule and shared-step
    roll-up as estimands.town_estimands. Fee splits are drawn ONCE per particle /
    town / design and reused across H and psi. Unidentified splits remain declared
    Dirichlet(1) assumptions; this is not a learned fee likelihood.
    """
    from scipy.special import expit
    from . import estimands, grid, spec
    from .config import config_for_params
    shape = (len(particles), len(model.towns), len(spec.STRUCTURE_IDS))
    values = {}
    rng = np.random.default_rng(seed)
    for ni, th in enumerate(particles):
        p = model.param_dict(th)
        config = config_for_params(p)
        mh = dict(zip(spec.HOUR_STEPS, estimands.hour_step_pmfs(p) @ (np.arange(config.hour_grid_size)*grid.HOUR_UNIT)))
        for ti, town in enumerate(model.towns):
            md = dict(zip(spec.DAY_STEPS, estimands.day_step_pmfs(p, town) @ np.arange(config.day_grid_size)))
            pk = grid.truncated_geometric(expit(p[f"lpinc_{town}"]), config.max_loops)
            ek = float(pk @ np.arange(config.max_loops+1))
            for di, sid in enumerate(spec.STRUCTURE_IDS):
                q = float(expit(p[f"lqobj_{town}"])) if spec.hearing_possible(sid) else 0.
                counts = spec.execution_counts(sid, ek, q)
                fees = model.fee_table(town, sid, rng)
                tables = {"days": {s: counts[s]*md[s] for s in spec.DAY_STEPS},
                          "hours": {s: counts[s]*mh[s] for s in spec.HOUR_STEPS},
                          "dollars": {s: float(fees.get(item, 0.)) if item in spec.fee_items(sid) else 0.
                                      for s, item in spec.FEE_STEPS.items()}}
                one = {}
                shared = spec.STRUCTURES[sid]["d2"][-1].rstrip("?") if spec.STRUCTURES[sid]["shared_decision"] else None
                for kind, table in tables.items():
                    one.update({f"pstep_{kind}.{s}": v for s, v in table.items()})
                    one[f"total.{kind}_mean"] = sum(table.values())
                    for d in spec.D_STEPS:
                        one[f"dstep_{kind}.{d['id']}"] = sum(v for s, v in table.items() if d["id"] in spec.P_STEPS[s]["d_steps"] or
                            (s == shared and d["id"] in spec.P_STEPS[spec.DECISION_STEP]["d_steps"]))
                one["complexity.expected_psteps"] = sum(counts.values())
                one["complexity.applicant_interactions"] = sum(counts[s] for s in counts if spec.P_STEPS[s]["applicant_facing"])
                if estimands.counterfactual_available():
                    cf = spec.COUNTERFACTUAL_DESIGN
                    cq = float(expit(p[f"lqobj_{town}"])) if spec.hearing_possible(cf) else 0.
                    cc = spec.execution_counts(cf, ek, cq)
                    one["counterfactual.delta_days_mean"] = sum(cc[s]*md[s] for s in md)-one["total.days_mean"]
                    one["counterfactual.delta_hours_mean"] = sum(cc[s]*mh[s] for s in mh)-one["total.hours_mean"]
                    one["counterfactual.delta_dollars_mean"] = fees.get("application", 0.)-one["total.dollars_mean"]
                for key, value in one.items():
                    if key not in values:
                        values[key] = np.zeros(shape)
                    values[key][ni, ti, di] = value
    cost = values["total.days_mean"]+4*values["total.hours_mean"]+values["total.dollars_mean"]/5
    return cost, values


def identification_report(results, L=None, cost=None, hypotheses=None):
    """Realized evidence separation is descriptive, not a formal identification proof."""
    pairs = []
    groups = results["classes"]
    for i, left in enumerate(groups):
        for right in groups[i+1:]:
            a, b = results["runs"][left[0]], results["runs"][right[0]]
            delta = np.array([x["log_marginal_ratio"]-y["log_marginal_ratio"] for x, y in zip(a, b)])
            pair = {"left": left, "right": right, "log_bayes_factors_by_psi": delta,
                          "max_absolute_log_bayes_factor": float(np.abs(delta).max()),
                          "numerical_caution": "finite-kappa Monte Carlo and Stage-B importance error not resolved by support separation"}
            if L is not None and hypotheses is not None:
                # A structural possibility check, NOT evidence of actual identification.
                hm = {h.id: h for h in hypotheses}
                support = np.exp(L-logsumexp(L, axis=2, keepdims=True)) > 1e-6
                maximum = 0.
                for cell in results["psi"]:
                    laws = []
                    for hid in (left[0], right[0]):
                        H = hm[hid]
                        V, mass = _components(H, results["settings"]["rho"], cell["kappa"])
                        lc = _choice(H, V, cell["model"], {k: v for k, v in cell.items() if k in ("tau", "beta")},
                                     cell["epsilon"], cost)
                        laws.append(np.einsum("...rd,r->...d", np.exp(lc), mass/mass.sum()))
                    difference = np.broadcast_to(np.abs(laws[0]-laws[1]), L.shape)
                    maximum = max(maximum, float(difference[support].max(initial=0)))
                pair["max_choice_law_difference_on_supported_designs"] = maximum
                pair["structurally_separable_on_support"] = maximum > 1e-12
                pair["support_cutoff"] = 1e-6
                pair["support_check_scope"] = "first-moment choice law; finite-kappa dependence may separate identical means"
            pairs.append(pair)
    return {"n_readers": len(results["hypothesis_ids"]), "n_grid_classes": len(groups), "pairs": pairs,
            "minimum_particle_ess": min(r["ess_particles"] for rs in results["runs"].values() for r in rs)}


def jsonable(value):
    """JSON-safe output: undefined conditional probabilities become null, not NaN."""
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value
