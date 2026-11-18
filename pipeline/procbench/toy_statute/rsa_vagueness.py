"""A Lassiter-Goodman (2017) threshold model of a vague predicate, applied to "nuisance".

Rational Speech Acts with a free threshold variable:
  literal listener  L0(x | u, theta) ∝ P(x) · [[u]](x; theta)
  speaker           S1(u | x, theta) ∝ exp(alpha · (log L0(x | u, theta) − cost(u)))
  pragmatic listener L1(x, theta | u) ∝ S1(u | x, theta) · P(x) · P(theta)
with P(theta) uniform. Utterances: "nuisance" (true iff degree x > theta) and the null
utterance (always true). The pragmatic listener's marginal over theta is the model's
distribution over *readings* of the vague word: it concentrates where saying "nuisance"
is informative relative to the prior over degrees, so it shifts with that prior.

Use in round 4 (docs/2026-09-29-toy-statute-round4-plan.md): one member of the prior pool
for Q1 ("does a desk review of the site plan suffice?") via the declared mapping
    P(Q1 = yes) = P(theta > x_plan),
where x_plan is the degree level that plan features (setback, coop size) can resolve.
If the threshold sits above what a plan can show, only clearly egregious coops are
nuisances and a plan check decides them; if it sits below, borderline cases need site
or neighbour evidence. This mapping is a modelling assumption, not part of the RSA model.

  python -m pipeline.procbench.toy_statute.rsa_vagueness [--out rsa.json]
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy.special import logsumexp
from scipy.stats import lognorm


def degree_prior(grid, density="medium"):
    """Prior over nuisance degree x (0..10) for a town; denser towns have more mass at
    high degrees (closer neighbours, more noise and odour exposure)."""
    med = {"low": 2.0, "medium": 3.0, "high": 4.5}[density]
    p = lognorm.pdf(grid, s=0.6, scale=med)
    return p / p.sum()


def rsa(grid, prior_x, alpha=4.0, cost_nuisance=1.0):
    """Return marginal posterior over theta (same grid) after hearing "nuisance"."""
    G = len(grid)
    theta = grid
    # literal meanings: [utterance, x, theta]
    lit_nuis = (grid[:, None] > theta[None, :]).astype(float)              # x > theta
    lit_null = np.ones((G, G))
    # L0(x | u, theta) ∝ P(x) * lit
    def L0(lit):
        m = lit * prior_x[:, None]
        z = m.sum(axis=0, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(z > 0, m / z, 0.0)
    L0n, L0null = L0(lit_nuis), L0(lit_null)
    with np.errstate(divide="ignore"):
        u_n = alpha * (np.log(L0n) - cost_nuisance)
        u_null = alpha * (np.log(L0null) - 0.0)
    # S1(u | x, theta) softmax over utterances
    Z = logsumexp(np.stack([u_n, u_null]), axis=0)
    S1_n = np.exp(u_n - Z)
    # L1(x, theta | "nuisance") ∝ S1 * P(x) * P(theta)
    joint = S1_n * prior_x[:, None] / G
    joint /= joint.sum()
    return joint.sum(axis=0), joint


def q1_prior_from_rsa(density="medium", x_plan_quantile=0.7, alpha=4.0):
    grid = np.linspace(0.05, 10, 200)
    px = degree_prior(grid, density)
    post_theta, _ = rsa(grid, px, alpha=alpha)
    cdf = np.cumsum(px)
    x_plan = grid[np.searchsorted(cdf, x_plan_quantile)]
    p_q1 = float(post_theta[grid > x_plan].sum())
    return {"density": density, "x_plan": float(x_plan), "theta_mean": float((grid * post_theta).sum()),
            "theta_q10": float(grid[np.searchsorted(np.cumsum(post_theta), 0.1)]),
            "theta_q90": float(grid[np.searchsorted(np.cumsum(post_theta), 0.9)]),
            "P_Q1_desk_sufficient": p_q1}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = {d: q1_prior_from_rsa(d) for d in ("low", "medium", "high")}
    for d, r in res.items():
        print(f"{d:7s} theta mean {r['theta_mean']:.2f} [{r['theta_q10']:.2f},{r['theta_q90']:.2f}]  "
              f"x_plan {r['x_plan']:.2f}  P(Q1 desk sufficient) {r['P_Q1_desk_sufficient']:.3f}")
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)
    return res


if __name__ == "__main__":
    main()
