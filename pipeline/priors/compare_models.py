#!/usr/bin/env python3
"""Does the hierarchical Bayesian fit actually predict better than the simpler things it replaced?

Leave-one-key-out. For each step key in turn: hide every observation belonging to it, fit on what
remains, predict its duration, and score the prediction against that key's own held-out evidence. This
is the only comparison that is not circular — a fit evaluated on the observations it was fitted to will
always look good.

Four predictors, in increasing order of what they are allowed to use:

  global      the median of every duration in the corpus. Knows nothing about the step.
  family      the median of the key's (agency_class, task_type) family. The naive pooling in rollup.py.
  EB          empirical-Bayes shrinkage toward the family, the previous implementation.
  Bayes       the posterior predictive from the Gibbs hierarchy, which also carries an interval.

Scored by median absolute log error (how many multiplicative factors off), and — only the Bayesian
predictor can offer this — by whether the held-out truth falls inside its 90% interval.

  python3 pipeline/priors/compare_models.py [--min-anchors 2] [--draws 2500]
"""
import argparse, collections, json, math, pathlib, statistics, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import hier_fit as H


def loo(groups, families, draws, burn, min_anchors):
    keys = [k for k, v in groups.items() if len(v) >= min_anchors]
    rows = []
    for held in keys:
        truth = statistics.median([y for y, _ in groups[held]])
        rest = {k: v for k, v in groups.items() if k != held}
        training_logs = [y for v in rest.values() for y, _ in v]
        if not training_logs:
            continue
        global_med = statistics.median(training_logs)
        fam = families(held)
        fam_logs = [y for k, v in rest.items() if families(k) == fam for y, _ in v]
        if not fam_logs:
            continue
        fam_med = statistics.median(fam_logs)
        # empirical Bayes: shrink the family estimate by how much evidence the family carries
        n_fam = len(fam_logs)
        var_fam = statistics.pvariance(fam_logs) if n_fam > 1 else 1.0
        w = n_fam / (n_fam + var_fam) if (n_fam + var_fam) else 0.5
        eb = w * fam_med + (1 - w) * global_med
        # Bayesian: sample the hierarchy without the held-out key, then draw the predictive for a NEW
        # key in that family, which is exactly the situation of an unmeasured jurisdiction
        d, hyper, stats, fam_of = H.gibbs(rest, families, draws=draws, burn=burn, seed=17)
        ms = hyper["m"].get(fam) or []
        if not ms:
            continue
        taus = hyper["tau2"]
        pred = [m_ + (t_ ** 0.5) * 0.0 for m_, t_ in zip(ms, taus)]      # predictive mean per draw
        import random as _r
        rnd = _r.Random(23)
        pred_draws = [rnd.gauss(m_, math.sqrt(t_)) for m_, t_ in zip(ms, taus)]
        bayes = statistics.median(pred_draws)
        lo, hi = H.q(pred_draws, .05), H.q(pred_draws, .95)
        rows.append({"key": "/".join(held[:2]), "n": len(groups[held]),
                     "truth_days": round(math.exp(truth), 1),
                     "global": abs(global_med - truth), "family": abs(fam_med - truth),
                     "eb": abs(eb - truth), "bayes": abs(bayes - truth),
                     "covered": bool(lo <= truth <= hi),
                     "bayes_days": round(math.exp(bayes), 1),
                     "ci90_days": [round(math.exp(lo), 1), round(math.exp(hi), 1)]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-anchors", type=int, default=2)
    ap.add_argument("--draws", type=int, default=2500)
    ap.add_argument("--burn", type=int, default=600)
    ap.add_argument("--family", choices=["agency_task", "task", "agency"], default="agency_task")
    ap.add_argument("--out", default="dashboard/data/model_comparison.json")
    a = ap.parse_args()
    groups, caps = H.anchors()
    fam = {"agency_task": lambda k: f"{k[0]}/{k[1]}", "task": lambda k: k[1], "agency": lambda k: k[0]}[a.family]
    rows = loo(groups, fam, a.draws, a.burn, a.min_anchors)
    if not rows:
        print("no keys with enough anchors"); return
    out = {"built": "2026-09-15", "n_keys_tested": len(rows), "family_definition": a.family,
           "protocol": "leave-one-key-out; each predictor sees every observation EXCEPT the held-out key's",
           "rows": rows}
    for name in ("global", "family", "eb", "bayes"):
        errs = [r[name] for r in rows]
        out[name] = {"median_abs_log_error": round(statistics.median(errs), 4),
                     "mean_abs_log_error": round(statistics.mean(errs), 4),
                     "median_factor_off": round(math.exp(statistics.median(errs)), 2),
                     "within_2x": round(sum(1 for e in errs if e < math.log(2)) / len(errs), 3)}
    out["bayes"]["ci90_coverage"] = round(sum(1 for r in rows if r["covered"]) / len(rows), 3)
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"Leave-one-key-out over {len(rows)} step keys ({a.family} families)\n")
    print("%-10s %22s %18s %12s" % ("predictor", "median |log error|", "median factor off", "within 2x"))
    for name, label in [("global", "global median"), ("family", "family median (naive pooling)"),
                        ("eb", "empirical Bayes"), ("bayes", "hierarchical posterior")]:
        m = out[name]
        print("%-10s %22.4f %18.2fx %12.0f%%" % (label[:10], m["median_abs_log_error"],
                                                 m["median_factor_off"], 100 * m["within_2x"]))
    print(f"\n90% interval coverage, Bayesian predictor: {100*out['bayes']['ci90_coverage']:.0f}%  (nominal 90%)")
    base, bay = out["family"]["median_abs_log_error"], out["bayes"]["median_abs_log_error"]
    print(f"improvement over naive pooling: {100*(base-bay)/base:+.1f}% in median log error")
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
