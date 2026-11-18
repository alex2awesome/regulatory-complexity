"""Score outcome-layer answers (Bayes and LLM, same schema) against truth.

Protocol: docs/2026-09-28-toy-statute-outcomes-plan.md.

  python -m pipeline.procbench.toy_statute.score_outcomes --world runs/.../W0o \
      --answers shared=runs/.../W0o/outfit_shared001/answers.json llm=runs/.../W0o/llm_outcomes001/answers_avg3.json \
      --out runs/.../W0o/scores_outcomes001
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import outcomes, spec
from .score import head_to_head, interval_score
from .truth_eval import truth_outcome_estimands


def floor(key):
    if key.endswith("_per100"):
        return 1.0
    if key.endswith("burden_index"):
        return 1.0
    if key.endswith("out.beta"):
        return 0.01
    return 0.05  # probabilities


def group(key):
    if ".cf." in key:
        return "counterfactual_" + key.rsplit(".", 1)[1]
    if key.startswith("out."):
        return "global_" + key.split(".")[1].split("_")[0]
    return "town_" + key.split(".", 2)[2]


def score(ans, truth, keys):
    out = {"estimands": {}, "missing": []}
    for k in keys:
        y = float(truth[k])
        v = ans.get("estimands", {}).get(k)
        try:
            l, m, u = (float(x) for x in v)
        except Exception:
            out["missing"].append(k)
            continue
        l, u = min(l, u), max(l, u)
        m = min(max(m, l), u)
        sc = max(abs(y), floor(k))
        IS = interval_score(l, u, y)
        out["estimands"][k] = {"truth": y, "q05": l, "q50": m, "q95": u, "interval_score": IS,
                               "scaled_is": IS / sc, "covered": bool(l <= y <= u),
                               "scaled_abs_err": abs(m - y) / sc, "group": group(k)}
    return out


def summarize(sc):
    rows = list(sc["estimands"].values())
    by = {}
    for r in rows:
        g = by.setdefault(r["group"], {"scaled_is": [], "covered": []})
        g["scaled_is"].append(r["scaled_is"])
        g["covered"].append(r["covered"])
    cur = [r for k, r in sc["estimands"].items() if ".cf." not in k]
    return {
        "n": len(rows), "missing": len(sc["missing"]),
        "mean_scaled_is": float(np.mean([r["scaled_is"] for r in rows])),
        "coverage90": float(np.mean([r["covered"] for r in rows])),
        "current_mean_scaled_is": float(np.mean([r["scaled_is"] for r in cur])),
        "current_coverage90": float(np.mean([r["covered"] for r in cur])),
        "groups": {g: {"n": len(v["scaled_is"]), "mean_scaled_is": float(np.mean(v["scaled_is"])),
                       "coverage": float(np.mean(v["covered"]))} for g, v in sorted(by.items())},
    }


def design_ranking(ans, truth, towns):
    """Per town: design minimizing operating nuisance, by answer median and by truth."""
    res = {}
    for t in towns:
        row = {}
        for src, get in (("answer", lambda k: ans["estimands"][k][1]), ("truth", lambda k: truth[k])):
            vals = {s: get(f"{t}.cf.{s}.operating_nuisance_per100") for s in spec.STRUCTURE_IDS}
            bur = {s: get(f"{t}.cf.{s}.burden_index") for s in spec.STRUCTURE_IDS}
            row[src] = {"min_nuisance": min(vals, key=vals.get), "min_burden": min(bur, key=bur.get),
                        "nuisance_per100": vals, "burden_index": bur}
        res[t] = row
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--answers", nargs="+", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    world = json.loads((Path(a.world) / "truth" / "world.json").read_text())
    truth = truth_outcome_estimands(world)
    towns = world["towns"]
    keys = outcomes.estimand_keys(towns)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scores, summ, ranks = {}, {}, {}
    for s_ in a.answers:
        name, path = s_.split("=", 1)
        ans = json.loads(Path(path).read_text())
        scores[name] = score(ans, truth, keys)
        summ[name] = summarize(scores[name])
        try:
            ranks[name] = design_ranking(ans, truth, towns)
        except Exception as e:  # incomplete answers
            ranks[name] = {"error": repr(e)}
    names = list(scores)
    h2h = {f"{x}_vs_{y}": head_to_head(scores[x], scores[y]) for i, x in enumerate(names) for y in names[i + 1:]}
    (out / "scores_detail.json").write_text(json.dumps({"truth": truth, "scores": scores}, indent=1))
    (out / "summary.json").write_text(json.dumps({"summary": summ, "head_to_head_interval_score": h2h,
                                                  "design_ranking": ranks}, indent=1))
    print(json.dumps({"summary": {n: {k: v for k, v in s.items() if k != "groups"} for n, s in summ.items()},
                      "h2h": h2h}, indent=1))


if __name__ == "__main__":
    main()
