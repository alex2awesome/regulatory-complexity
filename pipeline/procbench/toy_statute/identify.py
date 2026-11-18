"""Step-linking identifiability diagnostic.

For a given evidence design (which intervals between which events are
observed, per town) and given process structures, report which estimands are
identified at the level of MEANS, and which rest on priors.

Mean durations add along a chain, so the mean of every observed interval is a
known function of the step parameters. Locally, an estimand is identified from
interval means iff its gradient w.r.t. the parameters lies in the row space of
the Jacobian of the observed interval means. The residual
||g - P_rowspace(J) g|| / ||g|| is ~0 when identified and ~1 when the data are
silent. This is conservative: interval *shapes* (variances, mixture
structure) carry extra information that a means-only analysis ignores.

  python -m pipeline.procbench.toy_statute.identify --evidence runs/.../W0/evidence --structures Alder=S1 Birch=S3 Cedar=S4

Evaluated at the prior centre (no truth needed). Structures are an input:
use the posterior mode (for W0/W1 the fits put probability ~1 on one
structure per town).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import expit

from . import estimands, grid, spec
from .model import Model, load_evidence

PARAM_PREFIX = ("mu_", "lsig_", "la_", "lpinc_", "lqobj_")


def observed_interval_types(ev, town):
    """Distinct (from_event, to_event) interval types observed in a town's evidence."""
    types = set()
    for r in ev["admin"]:
        if r["town"] != town:
            continue
        if "milestones" not in r:
            types.add(("submitted", "decision"))
        else:
            name = {"deemed_complete": "app_complete", "inspection": "inspection", "hearing": "hearing"}
            evs = [("submitted", 0)] + [(name[k], v) for k, v in r["milestones"].items()] + [("decision", r["decided"])]
            evs = sorted(evs, key=lambda e: (e[1] if isinstance(e[1], str) else "0000", ["submitted", "app_complete", "hearing", "inspection", "decision"].index(e[0])))
            for a, b in zip(evs[:-1], evs[1:]):
                types.add((a[0], b[0]))
    for r in ev["reports"]:
        if r["town"] != town:
            continue
        if r["status"] == "pending":
            types.add(("submitted", "decision"))
        else:
            for g in r["gaps"]:
                types.add((g["from"], g["to"]))
    return sorted(types)


def interval_mean(p, town, s, e1, e2):
    """E[interval e1->e2 | it exists] under structure s (mixture over case paths)."""
    steps = estimands.day_step_pmfs(p, town)
    from .config import config_for_params
    config = config_for_params(p)
    means = steps @ np.arange(config.day_grid_size)
    pk = grid.truncated_geometric(expit(p[f"lpinc_{town}"]), config.max_loops)
    hp = spec.hearing_possible(s)
    q = float(expit(p[f"lqobj_{town}"])) if hp else 0.0
    num = den = 0.0
    for k, h in ((k, h) for k in range(config.max_loops + 1) for h in ((0, 1) if hp else (0,))):
        c = spec.segment_counts(spec.chain(s, k, h), e1, e2)
        if c is None:
            continue
        w = pk[k] * ((q if h else 1 - q) if hp else 1.0)
        num += w * float(np.dot(c, means))
        den += w
    return num / den if den > 0 else float("nan")


def analyse(ev_dir, structs, keys=None, h=1e-4, hypothetical=()):
    ev = load_evidence(ev_dir)
    model = Model(ev_dir)
    names = [n for n in model.names if n.startswith(PARAM_PREFIX)]
    # prior centre
    p0 = {}
    for n in model.names:
        kind, a, b = model.pspec[n]
        p0[n] = a if kind == "normal" else math.log((a / (a + b)) / (1 - a / (a + b)))
    rows = []
    obs_list = []
    for t, s in structs.items():
        for e1, e2 in observed_interval_types(ev, t):
            if math.isnan(interval_mean(p0, t, s, e1, e2)):
                continue  # interval impossible under the given structure
            obs_list.append((t, e1, e2))
    for hyp in hypothetical:  # "town:e1:e2" or "*:e1:e2" (what-if evidence design)
        ht, e1, e2 = hyp.split(":")
        for t, s in structs.items():
            if (ht in ("*", t)) and (t, e1, e2) not in obs_list and not math.isnan(interval_mean(p0, t, s, e1, e2)):
                obs_list.append((t, e1, e2))
    def obs_vec(p):
        return np.array([interval_mean(p, t, structs[t], e1, e2) for t, e1, e2 in obs_list])

    def est_vec(p):
        flat, _ = estimands.all_estimands(p, structs, lambda t, s: {"application": 0})
        return flat

    J = np.zeros((len(obs_list), len(names)))
    base_est = est_vec(p0)
    keys = keys or [k for k in base_est if any(f in k for f in ("pstep_days", "dstep_days", "total.days_mean",
                                                                   "counterfactual.delta_days", "deadline.p_miss",
                                                                   "statute.cf_mean_delta_days"))]
    G = np.zeros((len(keys), len(names)))
    for j, n in enumerate(names):
        pp, pm = dict(p0), dict(p0)
        pp[n] += h
        pm[n] -= h
        J[:, j] = (obs_vec(pp) - obs_vec(pm)) / (2 * h)
        ep, em = est_vec(pp), est_vec(pm)
        G[:, j] = [(ep[k] - em[k]) / (2 * h) for k in keys]
    # row space projector of J
    U, S, Vt = np.linalg.svd(J, full_matrices=False)
    rank = int((S > S.max() * 1e-8).sum()) if S.size else 0
    V = Vt[:rank].T
    res = {}
    for i, k in enumerate(keys):
        g = G[i]
        ng = np.linalg.norm(g)
        if ng < 1e-10:
            res[k] = {"residual": 0.0, "identified": True, "trivial": True}
            continue
        r = np.linalg.norm(g - V @ (V.T @ g)) / ng
        res[k] = {"residual": float(r), "identified": bool(r < 1e-3)}
    return {"observed_interval_types": [list(o) for o in obs_list], "n_params": len(names), "jacobian_rank": rank,
            "estimands": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--structures", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--hypothetical", nargs="*", default=[], help='what-if intervals, e.g. "*:app_complete:review_complete"')
    a = ap.parse_args()
    structs = dict(x.split("=") for x in a.structures)
    out = analyse(a.evidence, structs, hypothetical=a.hypothetical)
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))
    print("observed interval types:", len(out["observed_interval_types"]), "Jacobian rank", out["jacobian_rank"], "of", out["n_params"])
    for t, e1, e2 in out["observed_interval_types"]:
        print("  ", t, e1, "->", e2)
    ide = [k for k, v in out["estimands"].items() if v["identified"] and not v.get("trivial")]
    non = [(k, round(v["residual"], 3)) for k, v in out["estimands"].items() if not v["identified"]]
    print(f"identified ({len(ide)}):", ide)
    print(f"NOT identified from interval means ({len(non)}):", non)


if __name__ == "__main__":
    main()
