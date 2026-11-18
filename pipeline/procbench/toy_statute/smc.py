"""Adaptive tempered sequential Monte Carlo for the toy statute model (fit002+).

  python -m pipeline.procbench.toy_statute.smc --evidence runs/.../W0/evidence --out runs/.../W0/bayes_fit002 \
      --runs 2 --particles 2000 --moves 12 --workers 4

Particles start from the prior and move to the posterior through tempered
targets prior * L^beta. Next beta is chosen so the incremental-weight ESS is
half the particle count; particles are resampled (systematic) and moved by
random-walk Metropolis with the particle covariance. Two independent runs are
compared (rank R-hat treating each run as a chain; standardized mean
difference). Predeclared in docs/2026-09-26-toy-statute-plan.md addendum.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from . import spec
from .model import Model, log_prior, sample_prior
from .config import ExecutionConfig

_MODEL = None


PREFLIGHT_DRAWS = 20  # prior draws tried before declaring evidence/model incompatible

def model_kwargs(center_towns=False, prior_json=None, blocks=None, design_space=None, package_path=None,
                 model_config=None):
    kw = {"center_towns": center_towns}
    if package_path:
        kw["package_path"] = str(package_path)
    elif design_space:
        kw["design_space"] = design_space
    if blocks:
        kw["blocks"] = [tuple(b.split("+")) for b in blocks.split(",")]
    if prior_json:
        pj = json.loads(Path(prior_json).read_text())
        kw["prior_overrides"] = pj.get("prior_overrides")
        kw["struct_prior"] = pj.get("struct_prior")
    if model_config is not None:
        kw["model_config"] = model_config
    return kw


def _init(ev_dir, kw=None):
    global _MODEL
    _MODEL = Model(ev_dir, **(kw or {}))


def _eval_chunk(X):
    out = np.empty((len(X), 2))
    for i, x in enumerate(X):
        lp = _MODEL.logprior(x)
        ll = _MODEL.loglik(x)
        out[i] = (lp, ll if np.isfinite(ll) else -np.inf)
    return out


def _town_loglik_chunk(X):
    from .readings import town_struct_logliks
    return town_struct_logliks(_MODEL, X)


def _move_chunk(args):
    X, LP, LL, beta, chol, scale, n_moves, seed = args
    rng = np.random.default_rng(seed)
    X, LP, LL = X.copy(), LP.copy(), LL.copy()
    acc = 0
    d = X.shape[1]
    for _ in range(n_moves):
        for i in range(len(X)):
            prop = X[i] + scale * (chol @ rng.standard_normal(d))
            lp = _MODEL.logprior(prop)
            if not np.isfinite(lp):
                continue
            ll = _MODEL.loglik(prop)
            if not np.isfinite(ll):
                continue
            if (lp + beta * ll) - (LP[i] + beta * LL[i]) >= math.log(rng.random()):
                X[i], LP[i], LL[i] = prop, lp, ll
                acc += 1
    return X, LP, LL, acc / (n_moves * len(X))


def systematic_resample(rng, w):
    n = len(w)
    u = (rng.random() + np.arange(n)) / n
    return np.minimum(np.searchsorted(np.cumsum(w), u), n - 1)


def _blocked_move_chunk(args):
    from .blocked import TownCache
    X, beta, geometry, scale, n_sweeps, seed = args
    rng = np.random.default_rng(seed)
    moved, priors, likelihoods = [], [], []
    accepted, proposals = 0, 0
    for x in X:
        cache = TownCache(_MODEL, x)
        for _ in range(n_sweeps):
            stats = cache.sweep(rng, beta, geometry, scale)
            accepted += stats["accepted"]
            proposals += stats["proposals"]
        moved.append(cache.x); priors.append(cache.lp); likelihoods.append(cache.ll)
    return np.array(moved).reshape(X.shape), np.array(priors), np.array(likelihoods), accepted/max(proposals, 1)


def run_smc(ev_dir, n, n_moves, workers, seed, log=print, kw=None, town_loglik_out=None, move_kernel="joint", pool_factory=None,
            execution=None):
    """The evaluator pool may be injected; tempering/resampling stay unchanged.

    The default is the existing CPU process pool. An experimental accelerator
    must implement the same ordered map contract and mutation kernel semantics.
    """
    config = ExecutionConfig.parse(execution or {"kernel": move_kernel})
    if execution is not None and move_kernel != "joint" and move_kernel != config.kernel:
        raise ValueError("move_kernel conflicts with execution configuration")
    move_kernel = config.kernel
    if min(n, n_moves, workers) < 1 or n < 2:
        raise ValueError("SMC requires >=2 particles, positive moves and workers")
    kw = kw or {}
    model = Model(ev_dir, **kw)
    rng = np.random.default_rng(seed)
    X = np.array([model.sample_prior_theta(rng) for _ in range(n)])
    chunks = lambda A: np.array_split(A, workers)
    accelerator = None
    if config.backend == "jax":
        if pool_factory is not None:
            raise ValueError("choose execution backend or pool_factory, not both")
        from .jax_pool import JaxPool
        accelerator = JaxPool(model, config)
        factory = accelerator.factory
    else:
        factory = ProcessPoolExecutor if pool_factory is None else pool_factory
    with factory(max_workers=workers, initializer=_init, initargs=(str(ev_dir), kw)) as ex:
        ev = np.vstack(list(ex.map(_eval_chunk, chunks(X))))
        LP, LL = ev[:, 0], ev[:, 1]
        if not np.isfinite(LL).any():
            raise ValueError("no prior particle has finite likelihood; cannot temper this particle population")
        beta, logZ, stages = 0.0, 0.0, []
        scale = 2.38 / math.sqrt(X.shape[1]) if move_kernel == "joint" else 1.
        if move_kernel == "hmc":
            scale = config.hmc_step_size
        while beta < 1.0:
            finite = np.isfinite(LL)
            LLc = np.where(finite, LL, -1e300)

            def ess_at(b):
                lw = (b - beta) * LLc
                w = np.exp(lw - logsumexp(lw))
                return 1.0 / np.sum(w ** 2)

            if ess_at(1.0) >= n / 2:
                nb = 1.0
            else:
                lo, hi = beta, 1.0
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if ess_at(mid) >= n / 2:
                        lo = mid
                    else:
                        hi = mid
                nb = lo if lo > beta else hi
            lw = (nb - beta) * LLc
            logZ += logsumexp(lw) - math.log(n)
            w = np.exp(lw - logsumexp(lw))
            idx = systematic_resample(rng, w)
            X, LP, LL = X[idx], LP[idx], LL[idx]
            beta = nb
            moves = n_moves if beta < 1.0 else 2 * n_moves
            if move_kernel in ("joint", "hmc"):
                cov = np.cov(X.T) + 1e-9 * np.eye(X.shape[1])
                chol = np.linalg.cholesky(cov)
                args = [(Xc, LPc, LLc_, beta, chol, scale, moves, int(rng.integers(1 << 31)))
                        for Xc, LPc, LLc_ in zip(chunks(X), chunks(LP), chunks(LL))]
                res = list(ex.map(_move_chunk, args))
            else:
                from .blocked import proposal_geometry
                geometry = proposal_geometry(model, X)
                args = [(Xc, beta, geometry, scale, moves, int(rng.integers(1 << 31))) for Xc in chunks(X)]
                res = list(ex.map(_blocked_move_chunk, args))
            X = np.vstack([r[0] for r in res])
            LP = np.concatenate([r[1] for r in res])
            LL = np.concatenate([r[2] for r in res])
            if config.refresh_prior_only:
                names = model.prior_only_names()
                ids = [model.idx[name] for name in names]
                if ids:
                    # Exact independent conditional draws. The likelihood is
                    # invariant, so no extra all-town evaluations are required.
                    X[:, ids] = np.array([sample_prior(rng, names, model.pspec) for _ in X])
                    LP = np.array([model.logprior(x) for x in X])
            acc = float(np.mean([r[3] for r in res]))
            scale *= math.exp(acc - (0.8 if move_kernel == "hmc" else 0.234))
            uniq = len(np.unique(idx))
            stages.append({"beta": beta, "acc": acc, "scale": scale, "unique_ancestors": int(uniq),
                           "logZ": logZ, "t": time.time()})
            if accelerator is not None:
                stages[-1]["accelerator"] = dict(accelerator.last_stats)
            log(f"  stage {len(stages)} beta={beta:.5f} acc={acc:.3f} uniq={uniq} logZ={logZ:.2f}")
        if town_loglik_out is not None:
            # One final evaluation per particle, amortized across every later
            # Stage-C condition. Does not draw RNG or change sampler transitions.
            from .readings import save_likelihood_cache
            L = np.concatenate(list(ex.map(_town_loglik_chunk, chunks(X))))
            save_likelihood_cache(town_loglik_out, model, X, L)
    return X, LP, LL, logZ, stages


def compare_runs(runs, names):
    import arviz as az
    if len(runs) < 2:
        out = {n: {"rhat": None, "smd": None, "mean": float(runs[0][:,j].mean()),
                   "sd": float(runs[0][:,j].std())} for j,n in enumerate(names)}
        return out, {"worst_rhat_between_runs": None, "worst_standardized_mean_diff": None,
                     "pass": None, "note": "single ensemble; independent agreement unassessed"}
    out = {}
    for j, nme in enumerate(names):
        x = np.stack([r[:, j] for r in runs])  # (runs, particles)
        pooled = x.reshape(-1)
        smd = abs(x[0].mean() - x[1].mean()) / (pooled.std() + 1e-12) if len(runs) > 1 else 0.0
        out[nme] = {"rhat": float(az.rhat(x, method="rank")), "smd": float(smd),
                    "mean": float(pooled.mean()), "sd": float(pooled.std())}
    worst_r = max(v["rhat"] for v in out.values())
    worst_smd = max(v["smd"] for v in out.values())
    return out, {"worst_rhat_between_runs": worst_r, "worst_standardized_mean_diff": worst_smd,
                 "pass": bool(worst_r < 1.01 and worst_smd < 0.1)}


def prior_sd(model, n=20000, seed=0):
    rng = np.random.default_rng(seed)
    P = np.array([model.sample_prior_theta(rng) for _ in range(n)])
    return P.std(axis=0)


def gate_v2(model, runs, per_param, answers_by_run):
    """Round-2 gate (predeclared in docs/2026-09-26-toy-statute-round2-plan.md)."""
    psd = prior_sd(model)
    pooled = np.vstack(runs)
    ratio = pooled.std(axis=0) / psd
    fails = []
    for j, n in enumerate(model.names):
        v = per_param[n]
        informed = ratio[j] < 0.8
        v["post_to_prior_sd"] = float(ratio[j])
        v["data_informed"] = bool(informed)
        if v["rhat"] >= 1.01 or (informed and v["smd"] >= 0.1):
            fails.append(n)
    est_fail = []
    a0, a1 = answers_by_run
    worst_est = 0.0
    for k in a0["estimands"]:
        l0, m0, u0 = a0["estimands"][k]
        l1, m1, u1 = a1["estimands"][k]
        sd = max((u0 - l0) / 3.29, (u1 - l1) / 3.29, 1e-9)
        d = abs(m0 - m1) / sd
        worst_est = max(worst_est, d)
        # 0.2 posterior-SD threshold: pure Monte Carlo noise between two medians of
        # 1000 draws is ~0.056 SD, so 0.2 is ~3.6 SE (0.1 would fail by chance across ~120 estimands).
        if d >= 0.2 and max(u0 - l0, u1 - l1) > 1e-9:
            est_fail.append((k, round(d, 3)))
    return {"param_fails": fails, "estimand_fails": est_fail, "worst_estimand_median_diff_sd": worst_est,
            "pass": not fails and not est_fail}


def main(argv=None):
    from .fit import answers_from_draws, sha
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--package", default=None, help="statute package json (round 5+); overrides --design-space")
    ap.add_argument("--design-space", default="menu6", choices=["menu6", "full"],
                    help="hypothesis space of process designs (round 4 uses 'full': 11 serial designs)")
    ap.add_argument("--particles", type=int, default=2000)
    ap.add_argument("--moves", type=int, default=12)
    ap.add_argument("--move-kernel", choices=["joint", "blocked"], default="joint",
                    help="blocked: --moves counts full shared/local/paired-speed sweeps, not joint proposals")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260927)
    ap.add_argument("--cache-town-loglik", action="store_true",
                    help="save final per-particle/town/design likelihoods for repeated Stage C; one extra final evaluation")
    ap.add_argument("--center-towns", action="store_true")
    ap.add_argument("--prior-json", default=None)
    ap.add_argument("--gate", choices=["v1", "v2"], default="v1")
    ap.add_argument("--blocks", default=None, help='e.g. "desk_review+decision_issue,neighbor_notice+comment_period"')
    ap.add_argument("--model-config", help="JSON ModelConfig; scientific target settings, defaults preserve v2")
    ap.add_argument("--execution-config", help="JSON ExecutionConfig; cpu/jax, joint/blocked/hmc, batching and step size")
    ap.add_argument("--answer-draws", type=int, default=1000,
                    help="postprocessing draws; does not change sampled target (v2 gate assumes 1000)")
    a = ap.parse_args(argv)
    if a.answer_draws < 1:
        raise ValueError("answer-draws must be positive")
    if a.package:
        spec.load_package(json.loads(Path(a.package).read_text()))
    else:
        spec.use_design_space(a.design_space)
    scientific = json.loads(Path(a.model_config).read_text()) if a.model_config else None
    execution = json.loads(Path(a.execution_config).read_text()) if a.execution_config else None
    execution = ExecutionConfig.parse(execution or {"kernel": a.move_kernel})
    kw = model_kwargs(a.center_towns, a.prior_json, a.blocks, a.design_space, a.package, scientific)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    # Provenance survives a sampling or output failure. Never replace a prior
    # run's particles/configuration merely because its closeout was incomplete.
    if any(out.glob("particles_run*.npz")) or (out / "manifest.json").exists():
        raise FileExistsError(f"fit output already contains results: {out}; use a new directory")
    ev = Path(a.evidence)
    model = Model(a.evidence, **kw)
    launch = {"evidence": {f.name: sha(f) for f in sorted(ev.glob("*.json"))},
              "code": {f.name: sha(f) for f in sorted(Path(__file__).parent.glob("*.py"))},
              "args": vars(a), "observation_model": model.observation_metadata}
    from dataclasses import asdict
    launch["execution_config"] = asdict(execution)
    launch["model_config"] = model.config.to_dict()
    for key in ("package", "prior_json", "model_config", "execution_config"):
        if getattr(a, key):
            launch[f"{key}_sha256"] = sha(getattr(a, key))
    with (out / "launch_manifest.json").open("x") as f:
        json.dump(launch, f, indent=1)
    source = out / "source_snapshot"
    source.mkdir()
    for f in sorted(Path(__file__).parent.glob("*.py")):
        shutil.copy2(f, source / f.name)
    # Exercise the real answer path BEFORE a multi-hour fit (one prior point,
    # not a posterior result or a convergence test).
    # Exact milestone/status likelihoods have no contamination floor, so a single prior draw with a
    # very tight step duration can be -inf for a possible design (2026-09-30 blind round). Several
    # prior draws are tried; only a package/evidence pair that is -inf at every draw fails preflight.
    smoke_theta, smoke_ll, smoke_tries = None, -np.inf, 0
    for smoke_tries in range(1, PREFLIGHT_DRAWS + 1):
        smoke_theta = model.sample_prior_theta(np.random.default_rng(a.seed + 990 + smoke_tries))
        smoke_ll = model.loglik(smoke_theta)
        if np.isfinite(smoke_ll):
            break
    if not np.isfinite(smoke_ll):
        raise ValueError(f"preflight: nonfinite likelihood at all {PREFLIGHT_DRAWS} prior draws; inspect evidence/model compatibility")
    smoke = answers_from_draws(model, smoke_theta[None, :], a.seed + 992, n_draws=1)
    if not all(np.isfinite(v).all() for v in smoke["estimands"].values()):
        raise ValueError("preflight answer path produced nonfinite estimands")
    (out / "preflight.json").write_text(json.dumps({"status": "passed", "loglik": smoke_ll,
                                                   "prior_draws_tried": smoke_tries,
                                                   "estimands": len(smoke["estimands"]),
                                                   "note": "one prior draw; not a fitted result"}, indent=1))
    t0 = time.time()
    runs, meta = [], []
    for r in range(a.runs):
        print(f"run {r}")
        cache_path = out / f"town_loglik_run{r}.npz" if a.cache_town_loglik else None
        X, LP, LL, logZ, stages = run_smc(a.evidence, a.particles, a.moves, a.workers, a.seed + 1000 * r,
                                        kw=kw, town_loglik_out=cache_path, move_kernel=a.move_kernel,
                                        execution=asdict(execution))
        np.savez_compressed(out / f"particles_run{r}.npz", X=X, LP=LP, LL=LL)
        if cache_path is not None:
            launch.setdefault("town_loglik_caches", {})[cache_path.name] = sha(cache_path)
        runs.append(X)
        meta.append({"run": r, "logZ": logZ, "stages": stages, "seconds": time.time() - t0})
        (out / "sampling_status.json").write_text(json.dumps(
            {"completed_runs": len(runs), "requested_runs": a.runs, "runs": meta}, indent=1))
        (out / "manifest.json").write_text(json.dumps(
            {**launch, "completion": "sampling_saved; postprocessing_pending"}, indent=1))
    model = Model(a.evidence, **kw)
    per, summ = compare_runs(runs, model.names)
    if a.gate == "v2":
        abr = [answers_from_draws(model, R, a.seed + 50 + i, random_fee_split=True, n_draws=a.answer_draws) for i, R in enumerate(runs)]
        for i, ab in enumerate(abr):
            (out / f"answers_run{i}.json").write_text(json.dumps(ab, indent=1))
        g2 = gate_v2(model, runs, per, abr)
        summ["gate_v1_pass"] = summ["pass"]
        summ["gate_v2"] = g2
        summ["pass"] = g2["pass"]
    summ.update({"runs": [{"run": m["run"], "logZ": m["logZ"], "n_stages": len(m["stages"]),
                           "final_acc": m["stages"][-1]["acc"]} for m in meta],
                 "particles": a.particles, "moves": a.moves, "seconds": time.time() - t0})
    (out / "diagnostics.json").write_text(json.dumps({"summary": summ, "params": per, "stages": meta}, indent=1))
    ans = answers_from_draws(model, np.vstack(runs), a.seed + 7, random_fee_split=True, n_draws=a.answer_draws)
    ans["method"] = "bayes_exact_structure_smc"
    ans["diagnostics_pass"] = summ["pass"]
    (out / "answers.json").write_text(json.dumps(ans, indent=1))
    (out / "manifest.json").write_text(json.dumps({**launch, "completion": "complete"}, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
