#!/usr/bin/env python3
"""Stage 2: automated NY<->SD condition crosswalk, scored against Ho's
hand-made mapping (Figure 13 connector lines, recovered from the scan).

k independent LLM matchings (item lists shuffled per run so position can't
leak), then:
  - restricted precision/recall against the 43 high-confidence gold pairs
    (precision restricted to NY items that HAVE readable gold lines — a
    prediction for an unreadable-line item is not provably wrong);
  - cross-run stability (pairwise Jaccard) — crosswalk divergence is itself
    a measurement;
  - a >=2-votes ensemble, scored the same way.

Usage:  python3 crosswalk_eval.py -k 3
"""

import argparse
import json
import pathlib
import random
import sys
from itertools import combinations

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import llm
from llm import llm_json
from common import load

HC = HERE.parent / "corpus" / "health_codes"


def item_lines(items, name_key="name", pts_key=None):
    out = []
    for it in items:
        pts = it.get("possible_points") or it.get("points")
        out.append(f"{it['code']} — {it.get(name_key) or '(unnamed)'}"
                   + (f"  [points: {pts}]" if pts else ""))
    return out


def score(pairs, gold, gold_ny):
    pred = {(p["ny"], str(p["sd"])) for p in pairs}
    pred_on_gold = {p for p in pred if p[0] in gold_ny}
    tp = pred & gold
    return {"n_pred": len(pred), "n_pred_on_gold_ny": len(pred_on_gold),
            "tp": len(tp),
            "precision_restricted": round(len(tp) / len(pred_on_gold), 3) if pred_on_gold else None,
            "recall": round(len(tp) / len(gold), 3),
            "missed": sorted(map(list, gold - pred))[:15],
            "extra_on_gold_ny": sorted(map(list, pred_on_gold - gold))[:15]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--backend", default=None)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    llm.set_backend(args.backend, args.model)

    ny = load(HC / "ny_items.json")["items"]
    sd = load(HC / "sd_form_items.json")["items"]
    goldfile = load(HC / "gold_crosswalk.json")
    gold = {(a, b) for a, b in goldfile["high_confidence"]}
    gold_ny = {a for a, _ in gold}

    runs = []
    for i in range(args.k):
        rng = random.Random(100 + i)
        ny_l, sd_l = item_lines(ny), item_lines(sd)
        rng.shuffle(ny_l), rng.shuffle(sd_l)
        extra = ("NEW YORK CITY items:\n" + "\n".join(ny_l) +
                 "\n\nSAN DIEGO COUNTY items:\n" + "\n".join(sd_l))
        out = llm_json("13_crosswalk.md", "", None, extra=extra, max_tokens=16000)
        pairs = [{"ny": p["ny"], "sd": str(p["sd"])} for p in out.get("pairs", [])]
        runs.append({"pairs": pairs, "metrics": score(pairs, gold, gold_ny)})
        print(f"run {i}: {runs[-1]['metrics']['n_pred']} pairs, "
              f"P_r={runs[-1]['metrics']['precision_restricted']} R={runs[-1]['metrics']['recall']}")

    sets = [{(p["ny"], p["sd"]) for p in r["pairs"]} for r in runs]
    jacc = [round(len(a & b) / len(a | b), 3) for a, b in combinations(sets, 2)] if len(sets) > 1 else []
    from collections import Counter
    votes = Counter(pair for s in sets for pair in s)
    ensemble = [{"ny": a, "sd": b} for (a, b), v in votes.items() if v >= 2]

    report = {
        "gold": {"n_high": len(gold), "note": goldfile["source"][:160]},
        "runs": runs,
        "stability_jaccard": jacc,
        "ensemble_ge2": {"pairs": sorted((p["ny"], p["sd"]) for p in ensemble),
                         "metrics": score(ensemble, gold, gold_ny)},
    }
    out_path = HERE.parent / "examples" / "health_codes" / "crosswalk_eval.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    em = report["ensemble_ge2"]["metrics"]
    print(f"\nensemble(>=2 votes): P_r={em['precision_restricted']} R={em['recall']} "
          f"| stability Jaccard={jacc} -> {out_path}")


if __name__ == "__main__":
    main()
