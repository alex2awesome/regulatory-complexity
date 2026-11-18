"""Reading layer: text -> readings -> valid designs -> agency choice -> process posterior.

Protocol: docs/2026-09-29-toy-statute-round4-plan.md. Truth-blind.

A *reading* is one answer to each interpretive question in validity.QUESTIONS;
it fixes a decision model, and validity.check gives the designs valid under it.
The prior over readings is a pooled elicitation (log-linear pool over sources,
per question, with a residual reading). A *choice model* p(S | r, psi) says how
an agency picks a design given its reading. Stage C reweights saved process
particles exactly (they carry log p(data_t | S, theta) for every town and
design) to obtain posteriors over each town's reading, the population of
readings, and the designs, under each choice model.

Readings are identified only relative to the choice model (inverse planning):
report every result per choice model.
"""

from __future__ import annotations

import itertools
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from . import spec, validity

QUESTIONS = list(validity.QUESTIONS)
RESIDUAL = "residual"


# ---------------------------------------------------------------- readings and validity matrix

def all_readings():
    """All answer combinations, as dicts; index order is fixed."""
    return [dict(zip(QUESTIONS, vals)) for vals in itertools.product([True, False], repeat=len(QUESTIONS))]


def admissible(reading):
    """Mechanical admissibility of a reading of the toy statute. Every combination of
    Q1-Q5 answers preserves the concrete clauses and is internally consistent, so all
    are admissible here; the hook exists for statutes where they are not."""
    return True, "preserves concrete clauses; internally consistent"


def validity_matrix(design_ids=None):
    """bool array [n_readings, n_designs]: design valid under reading (fee items excluded:
    fee schedules are a town choice, not a structure)."""
    design_ids = design_ids or list(spec.STRUCTURE_IDS)
    R = all_readings()
    designs = {s: validity.menu_design(s) for s in design_ids}
    V = np.zeros((len(R), len(design_ids)), bool)
    for i, r in enumerate(R):
        for j, s in enumerate(design_ids):
            V[i, j] = all(ok for ok, _ in validity.check(designs[s], r).values())
    return V


# ---------------------------------------------------------------- prior over readings

def pooled_question_probs(sources, lambdas):
    """Log-linear pool per question. sources: {name: {q: P(yes)}}; lambdas: {name: weight}.
    Returns {q: P(yes)}. Sources missing a question are skipped for it."""
    out = {}
    for q in QUESTIONS:
        num = den = 0.0
        for name, probs in sources.items():
            if q not in probs or lambdas.get(name, 0) == 0:
                continue
            p = min(max(float(probs[q]), 1e-3), 1 - 1e-3)
            num += lambdas[name] * math.log(p)
            den += lambdas[name] * math.log(1 - p)
        if num == den == 0.0:
            out[q] = 0.5
        else:
            out[q] = 1.0 / (1.0 + math.exp(den - num))
    return out


def reading_prior(qprobs, rho=0.0):
    """Prior over readings (independent questions) plus a residual reading with mass rho.
    Returns array of length n_readings + 1 (last = residual). Inadmissible readings get 0."""
    R = all_readings()
    p = np.array([np.prod([qprobs[q] if r[q] else 1 - qprobs[q] for q in QUESTIONS]) for r in R])
    p *= np.array([admissible(r)[0] for r in R], float)
    p = p / p.sum() * (1 - rho)
    return np.append(p, rho)


# ---------------------------------------------------------------- choice models

CHOICE_MODELS = ("uniform", "cost", "risk")


def choice_logprob(V, model, eps, cost=None, tau=15.0, beta=1.0):
    """log p(S | r) for every reading (rows) and design (cols), plus the residual reading
    (last row: uniform over all designs).

    V: bool [R, D] validity matrix. cost: [D] burden index per design (cost model).
    uniform: (1-eps)/|V_r| on valid designs, eps/D everywhere.
    cost:    (1-eps) softmax(-cost/tau) over valid designs, eps/D everywhere.
    risk:    (1-eps) softmax(beta * n_valid_readings(S)) over valid designs, eps/D everywhere:
             agencies prefer designs that are valid under many readings."""
    R, D = V.shape
    base = np.full((R + 1, D), eps / D)
    if model == "uniform":
        pref = np.ones(D)
    elif model == "cost":
        pref = np.exp(-(np.asarray(cost, float) - np.min(cost)) / tau)
    elif model == "risk":
        pref = np.exp(beta * V.mean(axis=0))   # normalized: share of readings under which the design is valid (audit F8)
    else:
        raise ValueError(model)
    for i in range(R):
        w = pref * V[i]
        if w.sum() > 0:
            base[i] += (1 - eps) * w / w.sum()
        else:  # a reading that permits nothing: all mass to slack
            base[i] = 1.0 / D
    base[R] = 1.0 / D
    return np.log(base)


# ---------------------------------------------------------------- Stage C: exact reweighting

def town_struct_logliks(model, particles):
    """[n_particles, T, D] log p(data_t | S, theta) from saved particles."""
    towns = model.towns
    out = np.zeros((len(particles), len(towns), len(spec.STRUCTURE_IDS)))
    for n, th in enumerate(particles):
        for ti, t in enumerate(towns):
            out[n, ti] = model.town_struct_loglik(th, t)
    return out


def _particle_digest(particles):
    x = np.ascontiguousarray(particles, dtype=np.float64)
    return hashlib.sha256(str(x.shape).encode() + x.tobytes()).hexdigest()


def _likelihood_cache_metadata(model):
    """Bind cached L to data, coordinates, centering, catalog and scientific target."""
    catalog = {k: getattr(spec, k) for k in (
        "STATUTE_ID", "STRUCTURES", "P_STEPS", "DAY_STEPS", "HOUR_STEPS", "MAX_LOOPS",
        "TOWN_SCALED", "LISTABLE", "MENTIONABLE", "MENTION_EVENT", "ADMIN_MILESTONES", "EVENT_ORDER",
        "VAGUE_DSTEP", "DECISION_STEP")}
    catalog["TOWN_SCALED"] = sorted(catalog["TOWN_SCALED"])
    inputs = {"evidence": model.ev, "catalog": catalog, "blocks": model.blocks,
              "center_towns": model.center_towns, "observation_model": model.observation_metadata}
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"format": "town-design-loglik-v1", "input_sha256": digest, "parameter_names": model.names,
            "towns": model.towns, "design_ids": list(spec.STRUCTURE_IDS),
            "target_version": model.observation_metadata["target_version"]}


def save_likelihood_cache(path, model, particles, L):
    """Optional computational artifact, not another model/likelihood backend."""
    L = np.asarray(L, dtype=np.float64)
    expected = (len(particles), len(model.towns), len(spec.STRUCTURE_IDS))
    if L.shape != expected or np.isnan(L).any() or np.isposinf(L).any():
        raise ValueError("invalid town-design likelihood cache")
    metadata = {**_likelihood_cache_metadata(model), "particle_sha256": _particle_digest(particles),
                "likelihood_sha256": _particle_digest(L)}
    with Path(path).open("xb") as f:
        np.savez_compressed(f, L=L, metadata=json.dumps(metadata, sort_keys=True))


def load_likelihood_cache(path, model, particles):
    """Fail closed on data, model, ordering or corruption mismatch; no silent refit."""
    with np.load(path, allow_pickle=False) as saved:
        L = saved["L"]
        meta = json.loads(str(saved["metadata"].item()))
    expected = {**_likelihood_cache_metadata(model), "particle_sha256": _particle_digest(particles),
                "likelihood_sha256": _particle_digest(L)}
    if meta != expected or L.shape != (len(particles), len(model.towns), len(spec.STRUCTURE_IDS)):
        raise ValueError("town-design cache provenance, contents or particle order mismatch")
    if np.isnan(L).any() or np.isposinf(L).any():
        raise ValueError("invalid cached likelihood values")
    return L


def stage_c(L, prior, logchoice, kappa=None, n_w=200, rng=None, particle_logprior_correction=None,
            return_joint=False):
    """Reading posterior by exact reweighting of Stage-B particles.

    L:         [N, T, D] town-structure log-likelihoods per particle (Stage B used a uniform
               structure prior, so particle n has weight prop. to prod_t mean_S exp(L[n,t,S])
               already; we divide that out).
    prior:     [R+1] prior over readings incl. residual (p0).
    logchoice: [R+1, D] or [N, R+1, D] log p(S | r) (per-particle when the choice depends on theta).
    kappa:     None = each town's reading drawn from p0 independently; a float = population
               weights w ~ Dirichlet(kappa * p0) shared by all towns, integrated by n_w draws.
    Returns dict with particle weights, per-town reading posteriors [T, R+1], design posteriors
    [T, D], population weights, and the log marginal likelihood ratio vs Stage B.
    return_joint additionally returns particle_town_design [N,T,D], summing to
    particle_weights per town. This preserves parameter/design dependence for BMA."""
    if particle_logprior_correction is not None:
        raise NotImplementedError("nonuniform Stage-B prior correction is not implemented; do not silently ignore it")
    prior = np.asarray(prior, float)
    if logchoice.ndim == 2:
        # Aggregate ONLY identical choice laws. In the finite-kappa model,
        # Dirichlet aggregation uses actual alpha values (including floors).
        classes, inverse = np.unique(logchoice, axis=0, return_inverse=True)
        if len(classes) < len(prior):
            mass = prior if kappa is None else np.maximum(kappa * prior, 1e-6)
            grouped = np.bincount(inverse, weights=mass)
            share = np.divide(mass, grouped[inverse], out=np.zeros_like(mass), where=grouped[inverse] > 0)
            result = _integrate_stage_c(L, grouped if kappa is None else grouped / kappa, classes,
                                        kappa=kappa, n_w=n_w, rng=rng, return_joint=return_joint)
            result["town_reading"] = result["town_reading"][:, inverse] * share[None, :]
            result["population_weights"] = result["population_weights"][inverse] * share
            result["reading_classes"] = len(classes)
            result["reading_entries"] = len(prior)
            return result
    return _integrate_stage_c(L, prior, logchoice, kappa=kappa, n_w=n_w, rng=rng, return_joint=return_joint)


def _integrate_stage_c(L, prior, logchoice, kappa, n_w, rng, return_joint=False):
    """One integration kernel for grouped shared rows or particle-dependent rows."""
    N, T, D = L.shape
    Rp1 = len(prior)
    if logchoice.ndim == 2:          # shared across particles and towns
        lc = np.broadcast_to(logchoice, (N, T, Rp1, D))
    elif logchoice.ndim == 3:        # per particle, shared across towns
        lc = np.broadcast_to(logchoice[:, None, :, :], (N, T, Rp1, D))
    else:                            # per particle and town (cost model)
        lc = logchoice
    # m[n, t, r] = log sum_S p(S|r) p(data_t | S, theta_n)
    m = logsumexp(L[:, :, None, :] + lc, axis=3)                         # [N, T, R+1]
    base = logsumexp(L, axis=2) - math.log(D)                            # [N, T] Stage-B town evidence
    rng = rng or np.random.default_rng(0)
    if kappa is None:
        W = np.log(prior + 1e-300)[None, :]                               # [1, R+1]
        n_w = 1
    else:
        alpha = np.maximum(kappa * prior, 1e-6)
        W = np.log(rng.dirichlet(alpha, size=n_w) + 1e-300)               # [n_w, R+1]
    # log p(data | w_k, theta_n) - log p_B(data | theta_n)
    lt = logsumexp(m[:, None, :, :] + W[None, :, None, :], axis=3)        # [N, n_w, T]
    ratio = (lt - base[:, None, :]).sum(axis=2)                           # [N, n_w]
    logZ = logsumexp(ratio) - math.log(N * n_w)
    wgt = np.exp(ratio - logsumexp(ratio))                                # joint weights over (particle, w-draw)
    # per-town reading posterior: E[ w_r m_{n,t}(r) / sum_r' ... ]
    post_r = np.exp(m[:, None, :, :] + W[None, :, None, :] - lt[..., None])   # [N, n_w, T, R+1]
    town_reading = np.einsum("nk,nktr->tr", wgt, post_r)
    # per-town design posterior under the reading prior
    # p(S | data_t, w, theta) = sum_r p(r | w, ...) p(S | r, data_t)
    pS_given_r = np.exp(L[:, :, None, :] + lc - m[..., None])              # [N, T, R+1, D]
    # Sum population-weight draws first: same finite weighted sum, much less work.
    particle_town_reading = np.einsum("nk,nktr->ntr", wgt, post_r)
    town_design = np.einsum("ntr,ntrd->td", particle_town_reading, pS_given_r)
    pop = np.einsum("nk,kr->r", wgt, np.exp(W)) if kappa is not None else prior
    ess = 1.0 / (wgt ** 2).sum()
    result = {"log_marginal_ratio": float(logZ), "ess": float(ess), "town_reading": town_reading,
            "town_design": town_design, "population_weights": pop,
            "particle_weights": wgt.sum(axis=1)}
    if return_joint:
        result["particle_town_design"] = np.einsum("ntr,ntrd->ntd", particle_town_reading, pS_given_r)
    return result


# ---------------------------------------------------------------- scoring against truth (scorer only)

def score_readings(town_reading, truth_readings, truth_designs, town_design, towns, exclude=()):
    """truth_readings: {town: {q: bool}}; truth_designs: {town: S}.

    Audit 2026-09-29 (F6/F7): per-question P(yes) is CONDITIONAL on a known reading (residual mass
    is reported separately, never counted as 'no'); the joint log score is over the known-reading
    mass renormalized, and `exclude` drops questions from the joint (e.g. an unlearnable Q5) by
    marginalizing them out. MAP is over known readings."""
    return score_mapped(town_reading, QUESTIONS, truth_readings, {q: q for q in QUESTIONS},
                        towns, truth_designs, town_design, exclude)


# ---------------------------------------------------------------- fast burden index per design (for the cost model)

def burden_indices(p, town, fees):
    """Burden index (days + 4 hours + $/5) of every design in the current space for one town,
    from parameter dict p, without FFTs (expected counts x mean durations)."""
    from scipy.special import expit
    from . import estimands, grid
    from .config import config_for_params
    config = config_for_params(p)
    steps = estimands.day_step_pmfs(p, town)
    idays = np.arange(config.day_grid_size)
    mean_d = {st: float(steps[i] @ idays) for i, st in enumerate(spec.DAY_STEPS)}
    hsteps = estimands.hour_step_pmfs(p)
    ih = np.arange(config.hour_grid_size) * grid.HOUR_UNIT
    mean_h = {st: float(hsteps[i] @ ih) for i, st in enumerate(spec.HOUR_STEPS)}
    pk = grid.truncated_geometric(expit(p[f"lpinc_{town}"]), config.max_loops)
    Ek = float(pk @ np.arange(config.max_loops + 1))
    qo = float(expit(p[f"lqobj_{town}"]))
    out = np.zeros(len(spec.STRUCTURE_IDS))
    for j, s in enumerate(spec.STRUCTURE_IDS):
        q = qo if spec.hearing_possible(s) else 0.0
        executions = spec.execution_counts(s, Ek, q)
        days = sum(executions[st] * mean_d[st] for st in spec.DAY_STEPS)
        hours = sum(executions[st] * mean_h[st] for st in spec.HOUR_STEPS)
        dollars = sum(float(fees.get(item, 0.0)) for item in spec.fee_items(s))
        out[j] = days + 4.0 * hours + dollars / 5.0
    return out


# ---------------------------------------------------------------- CLI: Stage C on a saved fit

def _priors(elicit, rsa, variants):
    """Build {variant: {q: P(yes)}} from the elicitation aggregate and the RSA output."""
    direct = elicit["question_p_yes_direct_mean"]
    freq = elicit["question_p_yes_parse_frequency"]
    out = {}
    if "P-flat" in variants:
        out["P-flat"] = {q: 0.5 for q in QUESTIONS}
    if "P-llm" in variants:
        out["P-llm"] = pooled_question_probs({"direct": direct}, {"direct": 1.0})
    if "P-pool" in variants:
        srcs = {"direct": direct, "freq": freq}
        lam = {"direct": 1.0, "freq": 0.5}
        if rsa is not None:
            srcs["rsa"] = {"Q1_desk_sufficient": rsa["medium"]["P_Q1_desk_sufficient"]}
            lam["rsa"] = 0.5
        out["P-pool"] = pooled_question_probs(srcs, lam)
    if "P-pool2" in variants:  # addendum 4-A: direct + RSA only (parse frequency was degenerate 0/1)
        srcs = {"direct": direct}
        lam = {"direct": 1.0}
        if rsa is not None:
            srcs["rsa"] = {"Q1_desk_sufficient": rsa["medium"]["P_Q1_desk_sufficient"]}
            lam["rsa"] = 0.5
        out["P-pool2"] = pooled_question_probs(srcs, lam)
    return out


def run_stage_c(world_dir, fit_dir, elicit_path, rsa_path, out_dir, n_sub=2000, n_w=50, seed=20261005):
    from .model import Model
    from .smc import model_kwargs
    world_dir, fit_dir, out_dir = Path(world_dir), Path(fit_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fit_manifest = json.loads((fit_dir / "manifest.json").read_text())
    man = fit_manifest["args"]
    if man.get("prior_json"):
        raise ValueError("Stage C assumes the Stage-B fit used a UNIFORM design prior; this fit used prior_json "
                         f"{man['prior_json']} (its struct_prior would need to be divided out)")
    model = Model(world_dir / "evidence", **model_kwargs(man.get("center_towns", False), man.get("prior_json"),
                                                          man.get("blocks"), man.get("design_space"), man.get("package"),
                                                          fit_manifest.get("model_config")))
    model.require_fit_target(fit_manifest)
    X = np.vstack([np.load(f)["X"] for f in sorted(fit_dir.glob("particles_run*.npz"))])
    rng = np.random.default_rng(seed)
    towns, D = model.towns, len(spec.STRUCTURE_IDS)
    L = town_struct_logliks(model, X)                                      # [N, T, D]
    cost = np.zeros((len(X), len(towns), D))
    for n, th in enumerate(X):
        p = model.param_dict(th)
        for ti, t in enumerate(towns):
            fees = model.fee_table(t, spec.STRUCTURE_IDS[int(np.argmax(L[n, ti]))], rng)
            cost[n, ti] = burden_indices(p, t, fees)
    np.savez_compressed(out_dir / "stage_c_inputs.npz", L=L, cost=cost)
    V = validity_matrix()
    elicit = json.loads(Path(elicit_path).read_text())
    rsa = json.loads(Path(rsa_path).read_text()) if rsa_path else None
    priors = _priors(elicit, rsa, ["P-flat", "P-llm", "P-pool", "P-pool2"])
    choice_grid = [("uniform", {}), ("cost", {"tau": 15.0}), ("cost", {"tau": 40.0}), ("risk", {"beta": 2.0}), ("risk", {"beta": 5.0})]
    results = {"priors": priors, "runs": {},
               "note": "For independent town readings, rho and eps enter choice only through eta = rho + (1-rho) eps. "
                       "With finite Dirichlet kappa, cross-town dependence can distinguish them. "
                       "This sensitivity grid holds rho at 0.05 and varies eps; it does not learn both."}
    sub = rng.choice(len(X), size=min(n_sub, len(X)), replace=False)
    for pname, qp in priors.items():
        for rho in [0.05]:
            prior = reading_prior(qp, rho)
            for cm, kw in choice_grid:
                for eps in (0.05, 0.15, 0.30):
                    if cm == "cost":
                        lc = np.stack([np.stack([choice_logprob(V, cm, eps, cost=cost[n, ti], **kw) for ti in range(len(towns))], axis=0)
                                       for n in range(len(X))])   # [N, T, R+1, D]
                    else:
                        lc = choice_logprob(V, cm, eps, **kw)
                    for kappa in (None, 3.0, 10.0, 30.0):
                        key = f"{pname}|rho={rho}|{cm}{'' if not kw else ':' + ','.join(f'{k}={v}' for k, v in kw.items())}|eps={eps}|kappa={kappa or 'inf'}"
                        if kappa is None:
                            res = stage_c(L, prior, lc, kappa=None)
                        else:
                            res = stage_c(L[sub], prior, lc if lc.ndim == 2 else lc[sub], kappa=kappa, n_w=n_w,
                                          rng=np.random.default_rng(seed + 1))
                        results["runs"][key] = {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                                                for k, v in res.items() if k != "particle_weights"}
                        results["runs"][key]["ess"] = res["ess"]
    (out_dir / "stage_c.json").write_text(json.dumps(results, indent=1))
    return results



def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Stage C: reading layer on a saved process fit")
    ap.add_argument("--world-dir", required=True)
    ap.add_argument("--fit", required=True)
    ap.add_argument("--elicit", required=True, help="parse_elicit aggregate.json")
    ap.add_argument("--rsa", default=None, help="rsa_vagueness output json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = run_stage_c(a.world_dir, a.fit, a.elicit, a.rsa, a.out)
    print(len(res["runs"]), "stage-C runs written to", a.out)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- round 5: Stage C with a reader's (or the author's) questions

def stage_c_from_matrix(L, cost, V, qprobs, qids, choice_grid, eps_grid=(0.05, 0.15), kappas=(None, 10.0),
                        rho=0.05, n_sub=2000, n_w=50, seed=20261005):
    """Run the Stage-C grid for an arbitrary question set and validity matrix.
    L: [N, T, D] town-design log-likelihoods; cost: [N, T, D] burden indices; V: [R, D] bool.
    qprobs: {qid: P(yes)} prior; returns {key: result} with reading posteriors over R+1 (residual last)."""
    R = all_readings_for(qids)
    prior = np.array([np.prod([qprobs[q] if r[q] else 1 - qprobs[q] for q in qids]) for r in R])
    prior = np.append(prior / prior.sum() * (1 - rho), rho)
    N, T, D = L.shape
    rng = np.random.default_rng(seed)
    sub = rng.choice(N, size=min(n_sub, N), replace=False)
    out = {}
    for cm, kw in choice_grid:
        for eps in eps_grid:
            if cm == "cost":
                lc = np.stack([np.stack([choice_logprob(V, cm, eps, cost=cost[n, ti], **kw) for ti in range(T)]) for n in range(N)])
            else:
                lc = choice_logprob(V, cm, eps, **kw)
            for kappa in kappas:
                key = f"{cm}{'' if not kw else ':' + ','.join(f'{k}={v}' for k, v in kw.items())}|eps={eps}|kappa={kappa or 'inf'}"
                if kappa is None:
                    res = stage_c(L, prior, lc, kappa=None)
                else:
                    res = stage_c(L[sub], prior, lc if lc.ndim == 2 else lc[sub], kappa=kappa, n_w=n_w,
                                  rng=np.random.default_rng(seed + 1))
                out[key] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in res.items() if k != "particle_weights"}
    return out, prior.tolist()


def all_readings_for(qids):
    return [dict(zip(qids, vals)) for vals in itertools.product([True, False], repeat=len(qids))]


def score_mapped(town_reading, qids, truth_readings, mapping, towns, truth_designs=None, town_design=None, exclude=()):
    """Per-question Brier and log score of the true reading, where model question q maps to truth
    question mapping[q] (None -> truth constant True).

    Same convention as score_readings (audit F6/F7; response audit R3, 2026-09-30): per-question
    P(yes) and the joint log score are CONDITIONAL on a known reading (the last entry of each
    town's vector is residual mass, reported separately as mean_residual_mass, never scored as
    'no'); `exclude` marginalizes questions out of the joint log score."""
    R = all_readings_for(qids)
    tr = np.array(town_reading, float)
    if (tr.shape != (len(towns), len(R) + 1) or not np.isfinite(tr).all()
            or np.any(tr < 0) or not np.allclose(tr.sum(axis=1), 1.0)):
        raise ValueError("reading probabilities must be normalized, finite, nonnegative, with residual last")
    keep = [q for q in qids if q not in exclude]
    out = {"question_brier": {}, "town_p_yes": {}, "mean_log_score": None, "map_accuracy": None,
           "design_map_accuracy": None, "joint_questions": keep,
           "mean_residual_mass": float(tr[:, -1].mean()), "town_residual_mass": {}, "towns": {},
           "unscorable_known_towns": [], "score_probability_floor": 1e-12}
    ls, acc, full_acc, unconditional_ls = [], [], [], []
    per_q = {q: [] for q in qids}
    for ti, t in enumerate(towns):
        known_mass = float(tr[ti, :-1].sum())
        truth = {q: (bool(truth_readings[t][mapping[q]]) if mapping[q] else True) for q in qids}
        out["town_residual_mass"][t] = float(tr[ti, -1])
        if known_mass == 0:
            out["unscorable_known_towns"].append(t)
            out["town_p_yes"][t] = {q: None for q in qids}
            out["towns"][t] = {"p_true_reading_known": None, "p_residual": float(tr[ti, -1]),
                               "question_p_yes_given_known": out["town_p_yes"][t]}
            unconditional_ls.append(math.log(1e-12))
            continue
        known = tr[ti, :-1] / known_mass
        p_true = float(sum(known[j] for j, r in enumerate(R) if all(bool(r[q]) == truth[q] for q in keep)))
        ls.append(math.log(max(p_true, 1e-12)))
        unconditional_ls.append(math.log(max(p_true * known_mass, 1e-12)))
        i = next(j for j, r in enumerate(R) if all(bool(r[q]) == truth[q] for q in qids))
        full_acc.append(int(np.argmax(known) == i))
        marginal = {}
        for j, r in enumerate(R):
            key = tuple(bool(r[q]) for q in keep)
            marginal[key] = marginal.get(key, 0.0) + known[j]
        acc.append(int(max(marginal, key=marginal.get) == tuple(truth[q] for q in keep)))
        out["town_p_yes"][t] = {}
        for q in qids:
            pq = float(sum(known[j] for j, r in enumerate(R) if r[q]))
            out["town_p_yes"][t][q] = pq
            per_q[q].append((pq - float(truth[q])) ** 2)
        out["towns"][t] = {"p_true_reading_known": p_true, "p_residual": float(tr[ti, -1]),
                           "question_p_yes_given_known": out["town_p_yes"][t]}
    out["mean_log_score"] = float(np.mean(ls)) if ls else None
    out["mean_unconditional_log_score"] = float(np.mean(unconditional_ls))
    out["map_accuracy"] = float(np.mean(acc)) if acc else None
    out["full_known_map_accuracy"] = float(np.mean(full_acc)) if full_acc else None
    out["known_scored_towns"] = len(ls)
    out["question_brier"] = {q: float(np.mean(v)) if v else None for q, v in per_q.items()}
    out["design_log_score"] = None
    if truth_designs is not None and town_design is not None:
        td = np.array(town_design)
        out["design_map_accuracy"] = float(np.mean([int(np.argmax(td[ti]) == spec.STRUCTURE_IDS.index(truth_designs[t])) for ti, t in enumerate(towns)]))
        probs = [float(td[ti, spec.STRUCTURE_IDS.index(truth_designs[t])]) for ti, t in enumerate(towns)]
        out["design_log_score"] = float(np.mean(np.log(np.maximum(probs, 1e-12))))
        for t, probability in zip(towns, probs):
            out["towns"][t]["p_true_design"] = probability
    return out
