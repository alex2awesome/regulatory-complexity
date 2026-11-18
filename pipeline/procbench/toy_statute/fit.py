"""Posterior answers and compatibility entry point for the sole process fitter.

  python -m pipeline.procbench.toy_statute.fit --evidence runs/.../W0/evidence --out runs/.../W0/bayes_fit001

Both ``python -m ...fit`` and ``python -m ...smc`` execute smc.main with the
same options and defaults. The historical MAP/Laplace/MCMC implementation is
retained only in archived source snapshots, not as a production fallback.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from . import estimands, spec
N_ESTIMAND_DRAWS = 1000


def answers_from_draws(model, draws_flat, seed, random_fee_split=True, n_draws=None):
    rng = np.random.default_rng(seed)
    if not len(draws_flat):
        raise ValueError("answer generation requires at least one posterior draw")
    idx = np.linspace(0, len(draws_flat) - 1, N_ESTIMAND_DRAWS if n_draws is None else n_draws).astype(int)
    rows = []
    sprobs = {t: np.zeros(len(spec.STRUCTURE_IDS)) for t in model.towns}
    pred_pmf = {t: 0.0 for t in model.towns}
    for i in idx:
        th = draws_flat[i]
        p = model.param_dict(th)
        structs = {}
        for t in model.towns:
            sp = model.struct_posterior(th, t)
            sprobs[t] += sp
            structs[t] = spec.STRUCTURE_IDS[rng.choice(len(sp), p=sp)]
            mix = 0.0
            for si, S in enumerate(spec.STRUCTURE_IDS):
                if sp[si] > 0:
                    mix = mix + sp[si] * estimands.total_days_pmf(p, t, S)
            pred_pmf[t] = pred_pmf[t] + mix
        fee_fn = (lambda t, s: model.fee_table(t, s, rng)) if random_fee_split else model.fee_table
        flat, _ = estimands.all_estimands(p, structs, fee_fn)
        rows.append(flat)
    keys = list(rows[0])
    arr = {k: np.array([r[k] for r in rows], float) for k in keys}
    ans = {"method": "bayes_exact_structure", "estimands": {}, "structure_probs": {}, "predictive_total_days": {}}
    ans["model_metadata"] = dict(model.observation_metadata)
    ans["model_metadata"]["counterfactual_design"] = spec.COUNTERFACTUAL_DESIGN
    ans["model_metadata"]["counterfactual_status"] = ("available" if estimands.counterfactual_available()
                                                       else "unavailable: no intervention design specified by this package")
    ans["model_metadata"]["fee_allocation"] = "Dirichlet residual split" if random_fee_split else "equal residual split"
    for k, v in arr.items():
        ans["estimands"][k] = [float(np.quantile(v, 0.05)), float(np.quantile(v, 0.5)), float(np.quantile(v, 0.95))]
    for t in model.towns:
        pr = sprobs[t] / len(idx)
        ans["structure_probs"][t] = {S: float(pr[i]) for i, S in enumerate(spec.STRUCTURE_IDS)}
        pm = pred_pmf[t] / len(idx)
        c = np.cumsum(pm)
        ans["predictive_total_days"][t] = {str(q): int(np.searchsorted(c, q - 1e-12)) for q in estimands.PRED_QUANTILES}
    return ans


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    from .smc import main as smc_main
    return smc_main(argv)


if __name__ == "__main__":
    main()
