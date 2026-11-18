"""Score extended (survey) estimands: Bayes (extended_measures.json) and LLM (llm_ext answers) vs truth.

  python -m pipeline.procbench.toy_statute.score_ext --world runs/.../W0 \
      --bayes name=runs/.../W0/fitXXX/extended_measures.json --llm runs/.../W0/llm_ext001
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .extended import all_ext
from .llm_baseline import EXT_STATUTE_KEYS, EXT_TOWN_KEYS
from .score import interval_score
from .truth_eval import truth_params

FLOOR = {"ext.deadline_coverage": 0.05, "ext.p_miss_if_clock_from_submission": 0.05,
         "ext.serialisation_excess_days": 1.0, "ext.cf_consolidated_notice_delta_days": 1.0,
         "ext.days_per_correction_loop": 1.0, "ext.exposure_p_discretionary_encounter": 0.05,
         "ext.statute_realised_structure_variety_bits": 0.5}


def keys(towns):
    return [f"{t}.{k}" for t in towns for k in EXT_TOWN_KEYS] + list(EXT_STATUTE_KEYS)


def score(ans, truth, towns):
    rows = {}
    for k in keys(towns):
        v = ans.get(k)
        if v is None:
            continue
        l, m, u = sorted(float(x) for x in v)[0], float(v[1]), sorted(float(x) for x in v)[2]
        m = min(max(m, l), u)
        y = truth[k]
        base = k.split(".", 1)[1] if not k.startswith("ext.") else k
        sc = max(abs(y), FLOOR[base])
        rows[k] = {"truth": y, "q": [l, m, u], "scaled_is": interval_score(l, u, y) / sc,
                   "scaled_err": abs(m - y) / sc, "covered": bool(l <= y <= u)}
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--bayes", nargs="*", default=[])
    ap.add_argument("--llm", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    world = Path(a.world)
    wd = json.loads((world / "truth" / "world.json").read_text())
    towns = wd["towns"]
    truth = all_ext(truth_params(wd), dict(wd["structure"]))
    methods = {}
    for b in a.bayes:
        n, p = b.split("=", 1)
        methods[n] = json.loads(Path(p).read_text())["bayes"]
    for d in a.llm:
        A = [json.loads(f.read_text())["estimands"] for f in sorted(Path(d).glob("answers_[0-9].json"))]
        avg = {}
        for k in keys(towns):
            vals = [x[k] for x in A if x.get(k) and None not in x[k]]
            if vals:
                avg[k] = [float(np.mean([sorted(v)[i] for v in vals])) for i in range(3)]
        methods[f"llm_avg{len(A)}:{Path(d).name}"] = avg
        for i, x in enumerate(A):
            methods[f"llm{i}:{Path(d).name}"] = x
    res = {n: score(m, truth, towns) for n, m in methods.items()}
    summ = {n: {"n": len(r), "mean_scaled_is": float(np.mean([v["scaled_is"] for v in r.values()])),
                "mean_scaled_err": float(np.mean([v["scaled_err"] for v in r.values()])),
                "coverage90": float(np.mean([v["covered"] for v in r.values()]))} for n, r in res.items()}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ext_scores.json").write_text(json.dumps({"truth": truth, "scores": res, "summary": summ}, indent=1))
    for n, s in summ.items():
        print(f"{n:34s} n={s['n']:2d} scaledIS {s['mean_scaled_is']:.3f} err {s['mean_scaled_err']:.3f} cov {s['coverage90']:.2f}")


if __name__ == "__main__":
    main()
