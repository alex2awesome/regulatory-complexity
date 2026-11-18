"""Score answers (Bayes and LLM, same schema) against W0 truth.

  python -m pipeline.procbench.toy_statute.score --world runs/.../W0 \
      --answers bayes=runs/.../W0/bayes_fit001/answers.json llm0=... --out runs/.../W0/scores001
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from . import estimands, spec
from .truth_eval import truth_estimands

ALPHA = 0.10  # 90% intervals

# floor scales for scale-free aggregation (value units of each family)
FAMILY_FLOOR = {
    "pstep_days": 1.0, "pstep_hours": 0.25, "pstep_dollars": 1.0,
    "dstep_days": 1.0, "dstep_hours": 0.25, "dstep_dollars": 1.0,
    "total": 1.0, "deadline": 0.05, "complexity": 0.25, "counterfactual": 1.0, "statute": 0.5,
}


def family(key):
    parts = key.split(".")
    return parts[0] if parts[0] == "statute" else parts[1]


def interval_score(l, u, y):
    return (u - l) + (2 / ALPHA) * max(l - y, 0.0) + (2 / ALPHA) * max(y - u, 0.0)


def score_answers(ans, truth, towns, heldout):
    out = {"structure": {}, "estimands": {}, "predictive": {}, "missing": []}
    for t in towns:
        sp = ans.get("structure_probs", {}).get(t, {})
        vals = np.array([float(sp.get(S) or 0.0) for S in spec.STRUCTURE_IDS])
        if vals.sum() > 0:
            vals = vals / vals.sum()
        true_s = [S for S in spec.STRUCTURE_IDS if truth[f"{t}.structure_probs.{S}"] == 1.0][0]
        pt = vals[spec.STRUCTURE_IDS.index(true_s)]
        onehot = np.array([1.0 if S == true_s else 0.0 for S in spec.STRUCTURE_IDS])
        out["structure"][t] = {"p_true": float(pt), "log_score": float(math.log(max(pt, 1e-6))),
                               "brier": float(((vals - onehot) ** 2).sum()), "true": true_s}
    for k in estimands.estimand_keys(towns):
        y = float(truth[k])
        v = ans.get("estimands", {}).get(k)
        try:
            l, m, u = (float(x) for x in v)
        except Exception:
            out["missing"].append(k)
            continue
        l, u = min(l, u), max(l, u)
        m = min(max(m, l), u)
        fam = family(k)
        scale = max(abs(y), FAMILY_FLOOR[fam])
        IS = interval_score(l, u, y)
        out["estimands"][k] = {"truth": y, "q05": l, "q50": m, "q95": u, "interval_score": IS,
                               "scaled_is": IS / scale, "covered": bool(l <= y <= u),
                               "abs_err_median": abs(m - y), "scaled_abs_err": abs(m - y) / scale, "family": fam}
    for t in towns:
        pq = ans.get("predictive_total_days", {}).get(t, {})
        ys = np.array(heldout[t]["total_days"], float)
        losses = []
        for q in estimands.PRED_QUANTILES:
            v = pq.get(str(q))
            if v is None:
                continue
            e = ys - float(v)
            losses.append(np.mean(np.maximum(q * e, (q - 1) * e)))
        out["predictive"][t] = {"pinball_mean": float(np.mean(losses)) if losses else None,
                                "n_quantiles": len(losses)}
    return out


def summarize(sc):
    fam = {}
    for k, r in sc["estimands"].items():
        f = fam.setdefault(r["family"], {"n": 0, "scaled_is": [], "covered": [], "scaled_abs_err": []})
        f["n"] += 1
        f["scaled_is"].append(r["scaled_is"])
        f["covered"].append(r["covered"])
        f["scaled_abs_err"].append(r["scaled_abs_err"])
    fam_s = {f: {"n": v["n"], "mean_scaled_is": float(np.mean(v["scaled_is"])),
                 "coverage": float(np.mean(v["covered"])), "mean_scaled_abs_err": float(np.mean(v["scaled_abs_err"]))}
             for f, v in fam.items()}
    all_is = [r["scaled_is"] for r in sc["estimands"].values()]
    nt = [r for r in sc["estimands"].values()
          if not (r["truth"] == 0 and r["q05"] == 0 and r["q95"] == 0)]
    return {
        "nontrivial_n": len(nt),
        "nontrivial_mean_scaled_is": float(np.mean([r["scaled_is"] for r in nt])) if nt else None,
        "nontrivial_coverage90": float(np.mean([r["covered"] for r in nt])) if nt else None,
        "nontrivial_mean_scaled_abs_err": float(np.mean([r["scaled_abs_err"] for r in nt])) if nt else None,
        "structure_mean_log_score": float(np.mean([v["log_score"] for v in sc["structure"].values()])),
        "structure_mean_brier": float(np.mean([v["brier"] for v in sc["structure"].values()])),
        "estimands_scored": len(sc["estimands"]), "missing": len(sc["missing"]),
        "overall_mean_scaled_is": float(np.mean(all_is)) if all_is else None,
        "overall_coverage90": float(np.mean([r["covered"] for r in sc["estimands"].values()])) if all_is else None,
        "overall_mean_scaled_abs_err": float(np.mean([r["scaled_abs_err"] for r in sc["estimands"].values()])) if all_is else None,
        "predictive_mean_pinball": float(np.mean([v["pinball_mean"] for v in sc["predictive"].values()
                                                  if v["pinball_mean"] is not None])),
        "families": fam_s,
    }


def head_to_head(a, b):
    """Per-estimand wins on interval score (lower is better), non-trivial estimands only."""
    wins = {"a": 0, "b": 0, "tie": 0}
    for k in a["estimands"]:
        if k not in b["estimands"]:
            continue
        ra, rb = a["estimands"][k], b["estimands"][k]
        if ra["truth"] == 0 and ra["q95"] == 0 and rb["q95"] == 0 and ra["q05"] == 0 and rb["q05"] == 0:
            continue
        x, y = a["estimands"][k]["interval_score"], b["estimands"][k]["interval_score"]
        if abs(x - y) < 1e-9:
            wins["tie"] += 1
        elif x < y:
            wins["a"] += 1
        else:
            wins["b"] += 1
    return wins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--answers", nargs="+", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    world = Path(a.world)
    wdict = json.loads((world / "truth" / "world.json").read_text())
    truth, _ = truth_estimands(wdict)
    towns = json.loads((world / "evidence" / "public_spec.json").read_text())["towns"]
    heldout = json.loads((world / "heldout" / "heldout_cases.json").read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scores, summ = {}, {}
    for spec_ in a.answers:
        name, path = spec_.split("=", 1)
        ans = json.loads(Path(path).read_text())
        scores[name] = score_answers(ans, truth, towns, heldout)
        summ[name] = summarize(scores[name])
    names = list(scores)
    h2h = {f"{x}_vs_{y}": head_to_head(scores[x], scores[y]) for i, x in enumerate(names) for y in names[i + 1:]}
    (out / "scores_detail.json").write_text(json.dumps({"truth": truth, "scores": scores}, indent=1))
    (out / "summary.json").write_text(json.dumps({"summary": summ, "head_to_head_interval_score": h2h}, indent=1))
    print(json.dumps({"summary": summ, "head_to_head_interval_score": h2h}, indent=1))


if __name__ == "__main__":
    main()
