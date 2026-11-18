"""Solar phase 2b: how large a process-occupancy problem can this sampler hold?

The first five-fold run at all 440 authorities failed its convergence gate
badly: worst R-hat above four and effective sample sizes in the single digits.
Before concluding anything about the model, it is worth separating two very
different explanations.

  * The sampler is merely slow, in which case mixing improves in proportion to
    the number of draws and the only cost is compute.
  * The sampler is stuck, in which case more draws buy nothing, and the cause
    is structural: the presence logit is alpha[s] + u[j] with no constraint
    tying down the overall level, so adding a constant to every step effect and
    subtracting it from every jurisdiction effect leaves the likelihood
    unchanged. Two separate block updates cannot travel along that ridge.

The experiment runs the same held-out design at growing numbers of authorities
with the draw budget set by memory, and records mixing at each size. The
answer matters beyond solar: concealed carry has 30 authorities and CalFresh 58,
so if the sampler is sound at that scale their phases can proceed while solar's
440 cannot.
"""
from __future__ import annotations

import json

import numpy as np

from . import occupancy, solar_phase2 as P2

OUT = P2.OUT
# (authorities, chains, draws). Draws are set so that chains x draws x
# authorities x steps x 8 bytes stays near a gigabyte of retained samples.
CONDITIONS = [(30, 4, 6000), (60, 4, 5000), (120, 4, 3000), (240, 4, 1500), (440, 4, 800)]


def ridge_evidence(arrays, n_steps):
    """Correlation between the mean step effect and the mean jurisdiction effect.

    If the two are trading off against each other draw by draw, the additive
    non-identification is real and no amount of running will fix it.
    """
    white = arrays["hierarchy_white"]
    flat = white.reshape(-1, white.shape[-1])
    alpha_mean = flat[:, :n_steps].mean(axis=1)
    u_mean = flat[:, n_steps:-1].mean(axis=1) if flat.shape[1] > n_steps + 1 else None
    if u_mean is None or alpha_mean.std() == 0 or u_mean.std() == 0:
        return None
    return float(np.corrcoef(alpha_mean, u_mean)[0, 1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data_path = P2.PHASE1 / "occupancy_evidence.json"
    base = json.loads(data_path.read_text())
    rows = []
    for size, chains, draws in CONDITIONS:
        data, size = P2.subsample(base, size)
        config = occupancy.Config(chains=chains, warmup=max(300, draws // 2),
                                  draws=draws, seed=P2.SEED)
        import time
        started = time.time()
        result, arrays = occupancy.fit(data, config)
        elapsed = time.time() - started
        structural = {name: d for name, d in result["diagnostics"].items()
                      if not name.startswith("presence_probability")}
        rhats = [d["rhat"] for d in structural.values() if d["rhat"] is not None]
        ess = [d["ess_bulk"] for d in structural.values()]
        row = {
            "authorities": size, "chains": chains, "draws": draws,
            "total_draws": chains * draws, "seconds": round(elapsed, 1),
            "worst_rhat_structural": max(rhats) if rhats else None,
            "min_ess_bulk_structural": min(ess) if ess else None,
            "median_ess_bulk_structural": float(np.median(ess)) if ess else None,
            "ess_per_thousand_draws": (min(ess) / (chains * draws) * 1000) if ess else None,
            "numerically_usable": result["numerically_usable"],
            "level_ridge_correlation": ridge_evidence(arrays, len(data["steps"])),
        }
        rows.append(row)
        print(json.dumps(row))
        del arrays, result
    verdict = {
        "schema_version": "solar-occupancy-scaling/1",
        "packet": "solar_phase2_scaling",
        "conditions": rows,
        "reading": (
            "If effective sample size per thousand draws is roughly constant as authorities grow, "
            "the sampler is slow and the only barrier is compute and retained memory. If it falls "
            "towards zero, the problem is structural and more draws will not help. A level-ridge "
            "correlation near minus one is direct evidence that the step effects and the "
            "jurisdiction effects are trading off against each other, which is the additive "
            "non-identification the module's own docstring does not constrain away."),
        "consequence_for_other_families": (
            "Concealed carry has 30 authorities and CalFresh 58 counties. The 30 and 60 rows here "
            "are the sizes that matter for them, and they should be read before either family's "
            "occupancy phase is trusted."),
    }
    (OUT / "scaling_study.json").write_text(json.dumps(verdict, indent=2))
    print(json.dumps({"rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
