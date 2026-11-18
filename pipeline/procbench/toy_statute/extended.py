"""Extended complexity/burden measures from docs/2026-09-26-complexity-measures-survey.md.

Computed post hoc from saved posterior particles (and from truth), so they do
not disturb the predeclared round-1/round-2 scored estimands. Descriptive:
Bayes vs truth only (the LLM baselines were not asked these).

  python -m pipeline.procbench.toy_statute.extended --world runs/.../W0 --fit runs/.../W0/bayes_fit003 [--center-towns] [--prior-json P]

Measures (survey ids):
  M9  deadline coverage: E[complete app -> decision] / E[submission -> decision];
      plus P(miss 30 d) if the clock started at first submission (lever).
  M8  serialisation excess: E[total] - E[total under statutory precedence only]
      (D1 before D2; D2 branches desk | notice->comment->[hearing] | inspection
      run concurrently; decision after all). Lever: concurrency clause.
  M1  consolidated deficiency notice: delta E[total days] if all applicant
      errors are cited at once (at most one correction round; P(round)=P(k>=1)).
  M10 error sensitivity: d E[total days] / d p_incomplete, and E[days per loop].
  M11 exposure: neighbours informed (0/1), premises entered (0/1),
      P(in-person discretionary encounter) (inspection or hearing).
  M4  statutory openness (log2 |menu| and entropy of a structure prior) vs
      realised structure variety across towns (entropy of full-structure labels).
  M6  guidance deficit: entropy (bits) of the structure posterior from the
      town's web page alone (Beta-integrated listing rates, uniform structure prior).
  M3  self-assessability is a text property (2/3 d-steps determinable in
      advance now; 3/3 with a safe harbour for Sec. 3) and is reported in the doc.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import betaln, expit

from . import estimands, grid, spec
from .config import config_for_params, ParameterDict

DEADLINE = spec.DEADLINE_DAYS


def _pmf_counts(steps, counts):
    return grid.sum_pmfs(steps, [counts])[0]


def _cnt(steps):
    c = [0] * len(spec.DAY_STEPS)
    for s in steps:
        c[spec.DAY_STEPS.index(s)] += 1
    return tuple(c)


def _conv(a, b):
    return np.convolve(a, b)


def _max_pmf(pmfs):
    if not pmfs:
        return np.array([1.0])
    length = max(len(p) for p in pmfs)
    cdf = np.ones(length)
    for p in pmfs:
        cdf = cdf * np.pad(np.cumsum(p), (0, length-len(p)), constant_values=p.sum())
    return np.diff(np.concatenate([[0.0], cdf]))


def parallel_total_pmf(p, town, s, steps):
    """Total days when only statutory precedence is enforced (see module doc)."""
    config = config_for_params(p)
    pk = grid.truncated_geometric(expit(p[f"lpinc_{town}"]), config.max_loops)
    hp = spec.hearing_possible(s)
    q = float(expit(p[f"lqobj_{town}"])) if hp else 0.0
    d2 = [x.rstrip("?") for x in spec.STRUCTURES[s]["d2"]]
    shared = spec.STRUCTURES[s]["shared_decision"]
    out = np.zeros(estimands.total_support_length(config))
    for k in range(config.max_loops + 1):
        d1 = _pmf_counts(steps, _cnt(["completeness_check"] * (k + 1) + ["correction"] * k))
        for h in ((0, 1) if hp else (0,)):
            w = pk[k] * ((q if h else 1 - q) if hp else 1.0)
            branches = [_pmf_counts(steps, _cnt(["desk_review"]))] if spec.has_step(s, "desk_review") else []
            if "neighbor_notice" in d2:
                nb = ["neighbor_notice", "comment_period"] + (["hearing"] if h else [])
                branches.append(_pmf_counts(steps, _cnt(nb)))
            if "site_inspection" in d2:
                branches.append(_pmf_counts(steps, _cnt(["site_inspection"])))
            d2p = _max_pmf(branches)
            tail = d2p if shared else _conv(d2p, _pmf_counts(steps, _cnt(["decision_issue"])))
            total = _conv(d1, tail)
            out[:len(total)] += w * total
    return out


def ext_town(p, town, s):
    config = config_for_params(p)
    if set(spec.DAY_STEPS) - set(spec._HEN_SNAPSHOT["DAY_STEPS"]):
        raise ValueError("extended concurrency intervention is defined only for the hen catalog")
    steps = estimands.day_step_pmfs(p, town)
    idays = np.arange(estimands.total_support_length(config))
    tot = estimands.total_days_pmf(p, town, s, steps)
    mean_tot = float(tot @ idays)
    hp = spec.hearing_possible(s)
    q = float(expit(p[f"lqobj_{town}"])) if hp else 0.0
    hs = (0, 1) if hp else (0,)
    cnt = [spec.segment_counts(spec.chain(s, 0, h), "app_complete", "decision") for h in hs]
    wv = np.array([q if h else 1 - q for h in hs]) if hp else np.array([1.0])
    dl = wv @ grid.sum_pmfs(steps, cnt, length=len(idays))
    out = {}
    out["ext.deadline_coverage"] = float(dl @ idays) / mean_tot if mean_tot > 0 else 1.0
    out["ext.p_miss_if_clock_from_submission"] = float(tot[spec.DEADLINE_DAYS + 1:].sum())
    par = parallel_total_pmf(p, town, s, steps)
    out["ext.serialisation_excess_days"] = mean_tot - float(par @ idays)
    # M1 consolidated notice: k in {0,1} with P(k=1) = P(k>=1)
    pinc = expit(p[f"lpinc_{town}"])
    pk = grid.truncated_geometric(pinc, config.max_loops)
    p1 = 1 - pk[0]
    alt = 0.0
    for k, wk in ((0, 1 - p1), (1, p1)):
        for h in hs:
            wh = (q if h else 1 - q) if hp else 1.0
            c = spec.segment_counts(spec.chain(s, k, h), "submitted", "decision")
            law = _pmf_counts(steps, c)
            alt += wk * wh * float(law @ np.arange(len(law)))
    out["ext.cf_consolidated_notice_delta_days"] = alt - mean_tot
    # M10 error sensitivity (numeric derivative in p_incomplete)
    eps = 1e-4
    p2 = ParameterDict(p, config)
    lp = p[f"lpinc_{town}"]
    p2[f"lpinc_{town}"] = math.log((pinc + eps) / (1 - pinc - eps))
    tot2 = estimands.total_days_pmf(p2, town, s, steps)
    out["ext.error_sensitivity_days_per_unit_p"] = (float(tot2 @ idays) - mean_tot) / eps
    mean_c = float(steps[spec.DAY_STEPS.index("completeness_check")] @ np.arange(config.day_grid_size))
    mean_corr = float(steps[spec.DAY_STEPS.index("correction")] @ np.arange(config.day_grid_size))
    out["ext.days_per_correction_loop"] = mean_c + mean_corr
    del lp
    # M11 exposure
    has_insp = spec.has_step(s, "site_inspection")
    out["ext.exposure_neighbours_informed"] = 1.0 if spec.has_step(s, "neighbor_notice") else 0.0
    out["ext.exposure_premises_entered"] = 1.0 if has_insp else 0.0
    out["ext.exposure_p_discretionary_encounter"] = 1 - (1 - (1.0 if has_insp else 0.0)) * (1 - q)
    return out


def cf_invariance_band(p, town, s, deltas=(-0.3, 0.1)):
    """Causal-frame assumption 1 sensitivity (docs/process-model-causal-frame.md):
    delta mean days of do(R=S1) when the remaining D2/D3 steps (desk review,
    decision issuance) change duration by (1+delta) after the edit."""
    steps = estimands.day_step_pmfs(p, town)
    if not estimands.counterfactual_available():
        return {}
    config = config_for_params(p)
    idays = np.arange(estimands.total_support_length(config))
    cur = float(estimands.total_days_pmf(p, town, s, steps) @ idays)
    out = {}
    for d in deltas:
        p2 = ParameterDict(p, config)
        for st in ("desk_review", "decision_issue"):
            p2[f"mu_{st}"] = p[f"mu_{st}"] + math.log1p(d)
        cf = float(estimands.total_days_pmf(p2, town, "S1") @ idays)
        out[f"ext.cf_concrete_delta_days_if_remaining_steps_{'faster30' if d < 0 else 'slower10'}"] = cf - cur
    return out


def ext_statute(structs, struct_prior=None):
    labels = list(structs.values())
    _, cnt = np.unique(labels, return_counts=True)
    w = cnt / cnt.sum()
    out = {"ext.statute_openness_bits_uniform": math.log2(len(spec.STRUCTURE_IDS)),
           "ext.statute_realised_structure_variety_bits": float(-(w * np.log2(w)).sum())}
    if struct_prior is not None:
        v = np.array([struct_prior[S] for S in spec.STRUCTURE_IDS])
        v = v / v.sum()
        out["ext.statute_openness_bits_prior"] = float(-(v * np.log2(v)).sum())
    return out


def guidance_deficit(webpage, a_l=2.0, b_l=1.0, a_e=1.0, b_e=20.0):
    listed = webpage["listed_steps"]
    lp = []
    for S in spec.STRUCTURE_IDS:
        n1 = n0 = m1 = m0 = 0
        for st in spec.LISTABLE:
            present = spec.has_step(S, st) or (st == "hearing" and spec.hearing_possible(S))
            if present:
                n1 += listed[st]
                n0 += 1 - listed[st]
            else:
                m1 += listed[st]
                m0 += 1 - listed[st]
        lp.append(betaln(a_l + n1, b_l + n0) - betaln(a_l, b_l) + betaln(a_e + m1, b_e + m0) - betaln(a_e, b_e))
    lp = np.array(lp)
    post = np.exp(lp - lp.max())
    post /= post.sum()
    nz = post[post > 0]
    return float(-(nz * np.log2(nz)).sum()), {S: float(v) for S, v in zip(spec.STRUCTURE_IDS, post)}


def all_ext(p, structs, struct_prior=None):
    flat = {}
    for t, s in structs.items():
        for k, v in {**ext_town(p, t, s), **cf_invariance_band(p, t, s)}.items():
            flat[f"{t}.{k}"] = v
    flat.update(ext_statute(structs, struct_prior))
    return flat


def main():
    from .model import Model
    from .smc import model_kwargs
    from .truth_eval import truth_params
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--fit", required=True)
    ap.add_argument("--center-towns", action="store_true")
    ap.add_argument("--prior-json", default=None)
    ap.add_argument("--draws", type=int, default=600)
    a = ap.parse_args()
    world = Path(a.world)
    wdict = json.loads((world / "truth" / "world.json").read_text())
    truth = all_ext(truth_params(wdict), dict(wdict["structure"]))
    webp = json.loads((world / "evidence" / "webpages.json").read_text())
    gd = {t: guidance_deficit(webp[t]) for t in wdict["towns"]}
    kw = model_kwargs(a.center_towns, a.prior_json)
    model = Model(world / "evidence", **kw)
    fit = Path(a.fit)
    model.require_fit_target(json.loads((fit / "manifest.json").read_text()))
    X = np.vstack([np.load(f)["X"] for f in sorted(fit.glob("particles_run*.npz"))])
    rng = np.random.default_rng(7)
    idx = np.linspace(0, len(X) - 1, a.draws).astype(int)
    rows = []
    for i in idx:
        th = X[i]
        pd = model.param_dict(th)
        structs = {}
        for t in model.towns:
            sp = model.struct_posterior(th, t)
            structs[t] = spec.STRUCTURE_IDS[rng.choice(len(sp), p=sp)]
        rows.append(all_ext(pd, structs, None))
    keys = rows[0].keys()
    post = {k: [float(np.quantile([r[k] for r in rows], q)) for q in (0.05, 0.5, 0.95)] for k in keys}
    out = {"truth": truth, "bayes": post, "guidance_deficit_bits": {t: v[0] for t, v in gd.items()},
           "guidance_page_only_structure_posterior": {t: v[1] for t, v in gd.items()}}
    (fit / "extended_measures.json").write_text(json.dumps(out, indent=1))
    print(f"{'measure':58s} {'truth':>8s}  bayes median [5,95]")
    for k in truth:
        b = post.get(k)
        print(f"{k:58s} {truth[k]:8.3f}  " + (f"{b[1]:.3f} [{b[0]:.3f}, {b[2]:.3f}]" if b else "–"))
    print("guidance deficit (bits):", {t: round(v[0], 3) for t, v in gd.items()})


if __name__ == "__main__":
    main()
