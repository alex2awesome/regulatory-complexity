"""Outcome layer: what each process produces, beyond its burden (externalities).

Protocol: docs/2026-09-28-toy-statute-outcomes-plan.md. Truth-blind: public
specification only (no truth_world / truth_eval imports).

Would-be hen keepers in town t arrive as M_t ~ Poisson(m_t) over the study
period. Each one:
  - keeps a coop that is a nuisance with probability pi_t;
  - applies for a permit with probability p_t = expit(alpha - beta (B_t - B_REF)),
    where B_t is the town's expected applicant burden index (day-equivalents,
    BURDEN_W) under its process: burden deters applications;
  - if it applies, is screened by every safeguard its process contains
    (desk review; site inspection; neighbour comment period). Safeguard g
    flags a nuisance coop with probability d_g and a harmless one with f_g.
    Any flag means denial;
  - if it did not apply or was denied, keeps hens without a permit with
    probability u;
  - every operating coop draws at least one complaint over the period with
    probability k1 (nuisance) or k0 (harmless). Code enforcement investigates
    complained coops and records whether the nuisance is verified.

Observed per town: applications, denials, complaints about permitted and
about unpermitted coops (verified or unfounded), and a household survey
(n_s households sampled with replacement from H_t; number keeping hens).

Poisson thinning makes disjoint cells independent. Overlapping observed counts
are marginalized jointly. The survey integrates the conditional binomial
denied-keeper count and independent Poisson nonapplicant count; numerical tail
truncation is bounded relative to each survey likelihood, not normalized away.

The process model's posterior enters through B_t, the current structure and
the counterfactual burden for every design. It is a CUT model: outcome data
do not feed back into the process posterior. Each of J saved process draws
gets its own outcome SMC run, and groups are pooled with equal weight.

  python -m pipeline.procbench.toy_statute.outcomes fit --world-dir runs/.../W0o \
      --process-fit runs/.../W0/fit004 --model shared|hier --out runs/.../W0o/outfit_shared001
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.special import expit, gammaln, logit, logsumexp, xlogy, xlog1py
from scipy.stats import poisson

from . import estimands, spec

BURDEN_W = {"days": 1.0, "hours": 4.0, "dollars": 0.2}   # day-equivalents
B_REF = 60.0
SAFEGUARDS = ["desk_review", "site_inspection", "comment_period"]
SG_SHORT = {"desk_review": "desk", "site_inspection": "insp", "comment_period": "nb"}


def safeguards(s: str):
    return [g for g in SAFEGUARDS if spec.has_step(s, g)]


def burden_index(e: dict) -> float:
    return (BURDEN_W["days"] * e["total.days_mean"] + BURDEN_W["hours"] * e["total.hours_mean"]
            + BURDEN_W["dollars"] * e["total.dollars_mean"])


def burden_table(p: dict, town: str, fees: dict) -> dict:
    """Burden index under every menu structure, with the town's own fee amounts
    (fee items apply only where the design contains the step; see plan)."""
    return {s: burden_index(estimands.town_estimands(p, town, s, fees)[0]) for s in spec.STRUCTURE_IDS}


# ---------------------------------------------------------------- parameters and priors

GLOBAL = ["ld_desk", "ld_insp", "ld_nb", "lf_desk", "lf_insp", "lf_nb", "lk1", "lk0", "alpha", "lbeta", "lu"]
PRIOR = {  # normal priors on the unconstrained scale: (mean, sd)
    "lpi": (-1.5, 1.0),
    "ld_desk": (0.0, 1.2), "ld_insp": (0.0, 1.2), "ld_nb": (0.0, 1.2),
    "lf_desk": (-3.0, 1.0), "lf_insp": (-3.0, 1.0), "lf_nb": (-3.0, 1.0),
    "lk1": (0.5, 1.2), "lk0": (-2.5, 1.0),
    "alpha": (0.0, 1.5), "lbeta": (math.log(0.03), 1.0), "lu": (0.0, 1.2),
    "lm": (math.log(600.0), 1.0),
    "mpi": (-1.5, 1.0), "ltau": (math.log(0.5), 0.7), "z": (0.0, 1.0),
}


def param_names(towns, model="shared"):
    if model == "shared":
        names = ["lpi"]
    else:
        names = ["mpi", "ltau"] + [f"z_{t}" for t in towns]
    return names + GLOBAL + [f"lm_{t}" for t in towns]


def _pkey(name):
    for k in ("lm_", "z_"):
        if name.startswith(k):
            return k[:-1]
    return name


def log_prior(X, names):
    lp = np.zeros(X.shape[0])
    for i, n in enumerate(names):
        m, s = PRIOR[_pkey(n)]
        lp += -0.5 * ((X[:, i] - m) / s) ** 2 - math.log(s)
    return lp


def sample_prior(rng, N, names):
    return np.column_stack([rng.normal(*PRIOR[_pkey(n)], size=N) for n in names])


def unpack(X, names, towns):
    """Vectorized natural-scale parameters."""
    ix = {n: i for i, n in enumerate(names)}
    q = {}
    for g in ("desk", "insp", "nb"):
        q[f"d_{g}"] = expit(X[:, ix[f"ld_{g}"]])
        q[f"f_{g}"] = expit(X[:, ix[f"lf_{g}"]])
    q["k1"], q["k0"] = expit(X[:, ix["lk1"]]), expit(X[:, ix["lk0"]])
    q["alpha"], q["beta"] = X[:, ix["alpha"]], np.exp(X[:, ix["lbeta"]])
    q["u"] = expit(X[:, ix["lu"]])
    for t in towns:
        q[f"m_{t}"] = np.exp(X[:, ix[f"lm_{t}"]])
        if "lpi" in ix:
            q[f"pi_{t}"] = expit(X[:, ix["lpi"]])
        else:
            q[f"pi_{t}"] = expit(X[:, ix["mpi"]] + np.exp(X[:, ix["ltau"]]) * X[:, ix[f"z_{t}"]])
    return q


# ---------------------------------------------------------------- cells and likelihood

def rates(q, t, s, B):
    """Per-would-be-keeper probabilities of each outcome cell for town t under design s,
    burden index B. Works on arrays (particles) or scalars."""
    sg = safeguards(s)
    miss_n = np.ones_like(q["u"], dtype=float)
    pass_o = np.ones_like(q["u"], dtype=float)
    for g in sg:
        miss_n = miss_n * (1 - q[f"d_{SG_SHORT[g]}"])
        pass_o = pass_o * (1 - q[f"f_{SG_SHORT[g]}"])
    c, fz = 1 - miss_n, 1 - pass_o
    p = expit(q["alpha"] - q["beta"] * (B - B_REF))
    pi = q[f"pi_{t}"]
    k1, k0, u = q["k1"], q["k0"], q["u"]
    un_n = u * ((1 - p) * pi + p * pi * c)
    un_o = u * ((1 - p) * (1 - pi) + p * (1 - pi) * fz)
    return {
        "p_apply": p, "c": c, "fz": fz, "pi": pi,
        "deny": p * (pi * c + (1 - pi) * fz),
        "perm_n": p * pi * (1 - c), "perm_o": p * (1 - pi) * (1 - fz),
        "un_n": un_n, "un_o": un_o,
        "Vp": p * pi * (1 - c) * k1, "Np": p * (1 - pi) * (1 - fz) * k0,
        "Rp": p * (pi * (1 - c) * (1 - k1) + (1 - pi) * (1 - fz) * (1 - k0)),
        "Vu": un_n * k1, "Nu": un_o * k0, "Ru": un_n * (1 - k1) + un_o * (1 - k0),
    }


def _pois(y, lam):
    lam = np.maximum(lam, 1e-300)
    return y * np.log(lam) - lam - gammaln(y + 1.0)


def _joint_denied_unpermitted(D, Vu, Nu, l_dnv, l_dov, l_drest, l_nnv, l_nov, return_rest=False):
    """log p(D, Vu, Nu) with the denied applicants' later fates marginalized (audit 2026-09-29, F1).

    Disjoint Poisson cells: denied-nuisance-keep-complained (a, part of both D and Vu),
    denied-harmless-keep-complained (b, part of both D and Nu), denied-other (D - a - b),
    non-applicant-nuisance-complained (Vu - a), non-applicant-harmless-complained (Nu - b).
    Returns (logp [N], E[a | data] [N], E[b | data] [N]) for use by the survey term."""
    N = len(l_dnv)
    a = np.arange(0, min(D, Vu) + 1)[None, :, None]           # [1, A, 1]
    b = np.arange(0, min(D, Nu) + 1)[None, None, :]           # [1, 1, B]
    rest = D - a - b                                           # [1, A, B]
    lp = (_pois(a, l_dnv[:, None, None]) + _pois(b, l_dov[:, None, None]) + _pois(np.maximum(rest, 0), l_drest[:, None, None])
          + _pois(Vu - a, l_nnv[:, None, None]) + _pois(Nu - b, l_nov[:, None, None]))
    lp = np.where(rest >= 0, lp, -np.inf)
    mx = lp.reshape(N, -1).max(axis=1)
    w = np.exp(lp - mx[:, None, None])
    Z = w.reshape(N, -1).sum(axis=1)
    Ea = (w * a).reshape(N, -1).sum(axis=1) / Z
    Eb = (w * b).reshape(N, -1).sum(axis=1) / Z
    result = (mx + np.log(Z), Ea, Eb)
    if not return_rest:
        return result
    rest_weights = np.zeros((N, D + 1))
    rr = np.broadcast_to(rest, (1, a.shape[1], b.shape[2])).reshape(-1)
    valid = rr >= 0
    np.add.at(rest_weights.T, rr[valid], (w.reshape(N, -1)[:, valid] / Z[:, None]).T)
    return (*result, rest_weights)


def conditional_survey_loglik(S, n, H, K_obs, rest_weights, phi, lamR, relative_tol=1e-10):
    """Survey law with Q|rest ~ Binomial(rest, phi), R ~ Poisson(lamR).

    Average over the FULL conditional distribution of rest = D-a-b. Positive
    linear convolution (not FFT) avoids manufacturing tiny tail probabilities.
    Start with a wide Poisson window; if its omitted mass exceeds relative_tol
    times the calculated survey probability, expand to all contributing R.
    R > H-K_obs cannot contribute. No truncated distribution is renormalized.
    """
    weights = np.atleast_2d(rest_weights)
    phi = np.broadcast_to(np.asarray(phi, float), (len(weights),))
    lamR = np.broadcast_to(np.asarray(lamR, float), (len(weights),))
    cap = int(H - K_obs)
    if cap < 0 or H <= 0 or not 0 <= S <= n or relative_tol <= 0:
        raise ValueError("invalid survey counts or tolerance")
    D = weights.shape[1] - 1
    rest = np.arange(D + 1)[:, None]
    count = np.arange(D + 1)[None, :]
    valid = count <= rest
    logchoose = gammaln(rest + 1) - gammaln(count + 1) - gammaln(np.maximum(rest - count, 0) + 1)
    theta = (K_obs + np.arange(cap + 1)) / H
    logsurvey = (gammaln(n + 1) - gammaln(S + 1) - gammaln(n - S + 1)
                 + xlogy(S, theta) + xlog1py(n - S, -theta))
    result = np.full(len(weights), -np.inf)
    for i, (w, probability, lam) in enumerate(zip(weights, phi, lamR)):
        logbin = np.where(valid, logchoose + xlogy(count, probability)
                          + xlog1py(np.maximum(rest - count, 0), -probability), -np.inf)
        pq = w @ np.exp(logbin)
        hi = min(cap, int(math.ceil(lam + 12 * math.sqrt(lam) + 30)))
        for _ in range(2):
            R = np.arange(hi + 1)
            lp = xlogy(R, lam) - lam - gammaln(R + 1)
            shift = float(lp.max())
            hidden = np.convolve(pq, np.exp(lp - shift))[:cap + 1]
            with np.errstate(divide="ignore"):
                value = float(logsumexp(np.log(hidden) + logsurvey[:len(hidden)]) + shift)
            # Bound the absolute omitted integrand by the omitted Poisson mass.
            if hi == cap or poisson.logsf(hi, lam) <= math.log(relative_tol) + value:
                result[i] = value
                break
            hi = cap
    return result


def loglik(X, names, obs, group):
    """obs: outcomes.json content; group: {'struct': {t: s}, 'B': {t: {s: B}}}.

    Cells that are disjoint person-level categories are independent Poissons; the denial count and
    the unpermitted-complaint counts overlap, so their joint is marginalized.
    The survey retains the conditional denied-binomial/nonapplicant-Poisson mixture;
    it does not replace the whole hidden count by a mean-matched Poisson."""
    towns = list(obs["towns"])
    q = unpack(X, names, towns)
    ll = np.zeros(X.shape[0])
    for t in towns:
        o = obs["towns"][t]
        s = group["struct"][t]
        r = rates(q, t, s, group["B"][t][s])
        m = q[f"m_{t}"]
        p, pi, c, fz, k1, k0, u = r["p_apply"], r["pi"], r["c"], r["fz"], q["k1"], q["k0"], q["u"]
        A, D = o["applications"], o["denials"]
        Vp, Np = o["complaints_permitted"]["verified"], o["complaints_permitted"]["unfounded"]
        Vu, Nu = o["complaints_unpermitted"]["verified"], o["complaints_unpermitted"]["unfounded"]
        Rp = A - D - Vp - Np
        # approved applicants: disjoint cells
        ll += _pois(Vp, m * r["Vp"]) + _pois(Np, m * r["Np"]) + _pois(Rp, m * r["Rp"])
        # denied applicants and non-applicants: overlapping observed totals
        l_dnv = m * p * pi * c * u * k1                 # denied, nuisance, keeps, complained
        l_dov = m * p * (1 - pi) * fz * u * k0          # denied, harmless, keeps, complained
        l_dq = m * p * (pi * c * u * (1 - k1) + (1 - pi) * fz * u * (1 - k0))   # denied, keeps, quiet
        l_dg = m * p * (pi * c + (1 - pi) * fz) * (1 - u)                       # denied, gives up
        l_nnv = m * (1 - p) * pi * u * k1
        l_nov = m * (1 - p) * (1 - pi) * u * k0
        l_nq = m * (1 - p) * u * (pi * (1 - k1) + (1 - pi) * (1 - k0))          # non-applicant keeps, quiet
        lj, _, _, rest_weights = _joint_denied_unpermitted(
            D, Vu, Nu, l_dnv, l_dov, l_dq + l_dg, l_nnv, l_nov, return_rest=True)
        ll += lj
        # survey: keepers = approved + complained keepers (observed) + quiet keepers (hidden)
        phi = l_dq / np.maximum(l_dq + l_dg, 1e-300)   # P(quiet keeper | denied, not complained)
        sv = o["survey"]
        ll += conditional_survey_loglik(sv["keepers"], sv["n"], sv["households"],
                                        A - D + Vu + Nu, rest_weights, phi, l_nq)
    return ll


# ---------------------------------------------------------------- estimands

def outcome_estimands(q, towns, struct, B):
    """Flat estimands from (possibly vectorized) natural-scale parameters.
    struct: {t: current s}; B: {t: {s: burden index}}."""
    out = {}
    for g in ("desk", "insp", "nb"):
        out[f"out.d_{g}"] = q[f"d_{g}"]
        out[f"out.f_{g}"] = q[f"f_{g}"]
    out["out.u"], out["out.beta"] = q["u"], q["beta"]
    for t in towns:
        for s in spec.STRUCTURE_IDS:
            r = rates(q, t, s, B[t][s])
            vals = {
                "p_apply": r["p_apply"],
                "operating_nuisance_per100": 100 * (r["perm_n"] + r["un_n"]),
                "wrongful_denials_per100": 100 * r["p_apply"] * (1 - r["pi"]) * r["fz"],
                "unpermitted_per100": 100 * (r["un_n"] + r["un_o"]),
                "burden_index": B[t][s] + 0 * r["p_apply"],
            }
            if s == struct[t]:
                out[f"{t}.out.pi"] = r["pi"]
                out[f"{t}.out.p_detect"] = r["c"]
                out[f"{t}.out.p_wrongful_denial"] = r["fz"]
                out[f"{t}.out.nuisance_share_permitted"] = r["perm_n"] / (r["perm_n"] + r["perm_o"])
                for k, v in vals.items():
                    out[f"{t}.out.{k}"] = v
            for k in ("p_apply", "operating_nuisance_per100", "wrongful_denials_per100", "burden_index"):
                out[f"{t}.cf.{s}.{k}"] = vals[k]
    return out


def estimand_keys(towns):
    keys = [f"out.d_{g}" for g in ("desk", "insp", "nb")] + [f"out.f_{g}" for g in ("desk", "insp", "nb")]
    keys += ["out.u", "out.beta"]
    for t in towns:
        keys += [f"{t}.out.{k}" for k in ("pi", "p_detect", "p_wrongful_denial", "nuisance_share_permitted",
                                           "p_apply", "operating_nuisance_per100", "wrongful_denials_per100",
                                           "unpermitted_per100", "burden_index")]
        for s in spec.STRUCTURE_IDS:
            keys += [f"{t}.cf.{s}.{k}" for k in ("p_apply", "operating_nuisance_per100",
                                                  "wrongful_denials_per100", "burden_index")]
    return keys


# ---------------------------------------------------------------- tempered SMC (vectorized)

def _logmeanexp(x):
    m = x.max()
    return float(m + np.log(np.mean(np.exp(x - m))))


def smc(names, llfn, rng, N=2000, moves=10, ess_frac=0.5):
    X = sample_prior(rng, N, names)
    LP, LL = log_prior(X, names), llfn(X)
    beta, logZ, steps, acc_hist = 0.0, 0.0, 0, []
    d = X.shape[1]
    scale = 2.38 / math.sqrt(d)
    while beta < 1.0:
        lo, hi = beta, 1.0
        def ess(b):
            w = (b - beta) * LL
            w = np.exp(w - w.max())
            return w.sum() ** 2 / (w ** 2).sum()
        if ess(1.0) >= ess_frac * N:
            nb = 1.0
        else:
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                (lo, hi) = (mid, hi) if ess(mid) >= ess_frac * N else (lo, mid)
            nb = max(lo, beta + 1e-6)
        inc = (nb - beta) * LL
        logZ += _logmeanexp(inc)
        w = np.exp(inc - inc.max())
        w /= w.sum()
        u0 = (rng.random() + np.arange(N)) / N
        idx = np.minimum(np.searchsorted(np.cumsum(w), u0), N - 1)
        X, LP, LL = X[idx], LP[idx], LL[idx]
        beta = nb
        cov = np.cov(X.T) + 1e-9 * np.eye(d)
        Lc = np.linalg.cholesky(cov)
        acc_tot = 0.0
        for _ in range(moves):
            Y = X + scale * rng.standard_normal((N, d)) @ Lc.T
            LPy, LLy = log_prior(Y, names), llfn(Y)
            a = np.log(rng.random(N)) < (LPy + beta * LLy) - (LP + beta * LL)
            X[a], LP[a], LL[a] = Y[a], LPy[a], LLy[a]
            acc = a.mean()
            acc_tot += acc
            scale *= math.exp(acc - 0.25)
        acc_hist.append(acc_tot / moves)
        steps += 1
    return X, LL, {"logZ": logZ, "steps": steps, "mean_acceptance": float(np.mean(acc_hist)),
                   "final_scale": scale}


# ---------------------------------------------------------------- process draws -> groups

def process_groups(process_fit, ev_dir, J, seed):
    """J groups from saved process particles: structure per town, burden index per design."""
    from .model import Model
    from .smc import model_kwargs
    man = json.loads((Path(process_fit) / "manifest.json").read_text())
    a = man["args"]
    model = Model(ev_dir, **model_kwargs(a.get("center_towns", False), a.get("prior_json"), a.get("blocks"), a.get("design_space"), a.get("package"), man.get("model_config")))
    model.require_fit_target(man)
    Xp = np.vstack([np.load(f)["X"] for f in sorted(Path(process_fit).glob("particles_run*.npz"))])
    rng = np.random.default_rng(seed)
    idx = np.linspace(0, len(Xp) - 1, J).astype(int)
    groups = []
    for i in idx:
        th = Xp[i]
        p = model.param_dict(th)
        g = {"particle": int(i), "struct": {}, "B": {}}
        for t in model.towns:
            sp = model.struct_posterior(th, t)
            s = spec.STRUCTURE_IDS[rng.choice(len(sp), p=sp)]
            g["struct"][t] = s
            g["B"][t] = burden_table(p, t, model.fee_table(t, s, rng))
        groups.append(g)
    return groups


def summarize_draws(draws: dict):
    return {k: [float(np.quantile(v, 0.05)), float(np.quantile(v, 0.5)), float(np.quantile(v, 0.95))]
            for k, v in draws.items()}


def fit(world_dir, process_fit, model_kind, out, J=24, N=2000, moves=10, runs=2, seed=20261101):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ev = Path(world_dir) / "evidence"
    obs = json.loads((ev / "outcomes.json").read_text())
    towns = list(obs["towns"])
    names = param_names(towns, model_kind)
    t0 = time.time()
    groups = process_groups(process_fit, ev, J, seed)
    (out / "process_groups.json").write_text(json.dumps(groups, indent=1))
    per_run = []
    for r in range(runs):
        rng = np.random.default_rng(seed + 1000 * (r + 1))
        draws, params, info = {}, [], []
        for g in groups:
            X, LL, inf = smc(names, lambda Z, g=g: loglik(Z, names, obs, g), rng, N=N, moves=moves)
            keep = X[rng.choice(len(X), size=N // 4, replace=False)]
            params.append(keep)
            q = unpack(keep, names, towns)
            e = outcome_estimands(q, towns, g["struct"], g["B"])
            for k, v in e.items():
                draws.setdefault(k, []).append(np.broadcast_to(v, (len(keep),)).copy())
            info.append(inf)
        draws = {k: np.concatenate(v) for k, v in draws.items()}
        P = np.vstack(params)
        np.savez_compressed(out / f"draws_run{r}.npz", params=P, **{k.replace(".", "__"): v for k, v in draws.items()})
        per_run.append({"draws": draws, "params": P, "info": info})
    # diagnostics: between-run standardized mean difference per parameter and estimand
    diag = {"params": {}, "estimands": {}}
    for i, n in enumerate(names):
        a, b = per_run[0]["params"][:, i], per_run[1]["params"][:, i]
        diag["params"][n] = _smd(a, b)
    for k in per_run[0]["draws"]:
        diag["estimands"][k] = _smd(per_run[0]["draws"][k], per_run[1]["draws"][k])
    worst_p = max(v["smd"] for v in diag["params"].values())
    worst_e = max(v["median_shift_sd"] for v in diag["estimands"].values())
    gate = {"worst_param_smd": worst_p, "worst_estimand_median_shift_sd": worst_e,
            "pass": bool(worst_p < 0.1 and worst_e < 0.2)}
    pooled = {k: np.concatenate([pr["draws"][k] for pr in per_run]) for k in per_run[0]["draws"]}
    Pall = np.vstack([pr["params"] for pr in per_run])
    prior_sd = {n: PRIOR[_pkey(n)][1] for n in names}
    contraction = {n: float(1 - Pall[:, i].std() / prior_sd[n]) for i, n in enumerate(names)}
    ans = {"method": f"bayes_outcomes_{model_kind}", "estimands": summarize_draws(pooled)}
    (out / "answers.json").write_text(json.dumps(ans, indent=1))
    (out / "diagnostics.json").write_text(json.dumps({
        "gate": gate, "param_contraction_sd": contraction, "between_run": diag,
        "smc_info": [pr["info"] for pr in per_run], "seconds": time.time() - t0}, indent=1))
    code = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(Path(__file__).parent.glob("*.py"))}
    (out / "manifest.json").write_text(json.dumps({
        "evidence": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(ev.glob("*.json"))},
        "process_fit": str(process_fit), "code": code,
        "outcome_target": "joint-counts-conditional-survey-v2-20260930",
        "survey_relative_tail_tolerance": 1e-10,
        "args": {"model": model_kind, "J": J, "N": N, "moves": moves, "runs": runs, "seed": seed}}, indent=1))
    return gate, contraction


def _smd(a, b):
    sd = math.sqrt(0.5 * (a.var() + b.var())) + 1e-12
    return {"smd": float(abs(a.mean() - b.mean()) / sd),
            "median_shift_sd": float(abs(np.median(a) - np.median(b)) / sd)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit")
    f.add_argument("--world-dir", required=True)
    f.add_argument("--process-fit", required=True)
    f.add_argument("--model", choices=["shared", "hier"], required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--J", type=int, default=24)
    f.add_argument("--N", type=int, default=2000)
    f.add_argument("--moves", type=int, default=10)
    f.add_argument("--seed", type=int, default=20261101)
    a = ap.parse_args(argv)
    gate, contraction = fit(a.world_dir, a.process_fit, a.model, a.out, a.J, a.N, a.moves, 2, a.seed)
    print(json.dumps({"gate": gate, "contraction": contraction}, indent=1))


if __name__ == "__main__":
    main()
