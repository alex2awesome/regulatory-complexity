#!/usr/bin/env python3
"""Proper posterior for the duration hierarchy: a conjugate Gibbs sampler.

This replaces three acknowledged weaknesses in `latent_timing.py` at once:

  (1) effective sample size — the old code used the SUM of evidence weights as n, so one audited figure
      (weight 3.0) counted as three independent draws and every interval came out optimistic. Here n is
      Kish's effective sample size, n_eff = (sum w)^2 / sum w^2, which equals the count when weights are
      equal and shrinks toward 1 when one source dominates.

  (2) sigma estimated three different ways — the old code took sigma from a p50/p90 pair if present, else
      a range, else the weighted spread across heterogeneous sources, which on two anchors was close to
      arbitrary. Here sigma_k is a parameter with its own hierarchical prior, so a thin key inherits the
      family's shape instead of inventing one.

  (3) not a posterior — the old code was empirical Bayes with tau^2 estimated from the same data it
      shrank, and normal-approximation intervals. Here tau^2, the family mean, and the shape hierarchy
      are sampled jointly, so the reported intervals include uncertainty about the hierarchy itself.

Model, fully conjugate:

    y_{k,j}   ~ Normal(mu_k, sigma_k^2)          log durations, j = 1..n_k
    mu_k      ~ Normal(m, tau^2)                 partial pooling across keys in a family
    sigma_k^2 ~ InvGamma(nu/2, nu*s2/2)          shape hierarchy: thin keys borrow the family's spread
    m         ~ Normal(0, 100)
    tau^2     ~ InvGamma(a0, b0)
    s2        ~ Gamma(c0, d0)

  python3 pipeline/priors/hier_fit.py [--family agency_task|step_key] [--draws 4000] [--burn 1000]
"""
import argparse, collections, glob, json, math, pathlib, random, statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
OFFICIAL = {"verifiable_official", "inferred"}
DESIGNED = {"designed_document"}
COMMUNITY = {"community_reported"}
W = {"verifiable_official": 3.0, "inferred": 3.0, "designed_document": 1.5,
     "community_reported": 1.0, "statutory": 0.0}          # caps are policy: weight 0, never fitted
KEYF = ("agency_class", "task_type", "channel", "blocking_party", "cadence", "jurisdiction_class")


def _v(o, k):
    d = o.get("value") if isinstance(o.get("value"), dict) else o
    x = d.get(k) if isinstance(d, dict) else None
    return float(x) if isinstance(x, (int, float)) and x > 0 else None


def anchors():
    """-> {key: [(log_value, weight)]}, plus the cap per key, from every observation file."""
    g = collections.defaultdict(list)
    caps = collections.defaultdict(list)
    for f in sorted(glob.glob(str(ROOT / "pipeline/priors/observations/*.json"))):
        for o in (json.load(open(f)).get("observations") or []):
            if not isinstance(o, dict):
                continue
            sk = o.get("step_key") if isinstance(o.get("step_key"), dict) else {}
            key = tuple((sk.get(x) or "unspecified") for x in KEYF)
            w = W.get(str(o.get("evidence_tier")), 1.0)
            c = _v(o, "statutory_cap_days")
            if c:
                caps[key].append(c)
            for field in ("elapsed_days", "p50"):
                x = _v(o, field)
                if x and w > 0:
                    g[key].append((math.log(x), w))
                    break
    return g, caps


def invgamma(a, b, rnd):
    return b / rnd.gammavariate(a, 1.0) if a > 0 and b > 0 else 1.0


def gibbs(groups, families, draws=4000, burn=1000, thin=2, nu=4.0, seed=11):
    """Returns posterior draws of mu_k and sigma_k, plus the family-level parameters."""
    rnd = random.Random(seed)
    keys = list(groups)
    # weighted sufficient statistics with Kish effective sample size
    stats = {}
    for k in keys:
        ys = groups[k]
        sw = sum(w for _, w in ys); sw2 = sum(w * w for _, w in ys)
        n_eff = (sw * sw / sw2) if sw2 > 0 else 1.0
        ybar = sum(y * w for y, w in ys) / sw if sw else 0.0
        stats[k] = {"n_eff": n_eff, "ybar": ybar, "ys": ys, "sw": sw}
    fam_of = {k: families(k) for k in keys}
    fams = sorted(set(fam_of.values()))
    mu = {k: stats[k]["ybar"] for k in keys}
    sig2 = {k: 0.5 for k in keys}
    m = {f: statistics.mean([stats[k]["ybar"] for k in keys if fam_of[k] == f]) for f in fams}
    tau2, s2 = 0.4, 0.5
    out = {k: {"mu": [], "sig": []} for k in keys}
    hyper = {"tau2": [], "s2": [], "m": collections.defaultdict(list)}
    for it in range(draws):
        # mu_k | rest
        for k in keys:
            st = stats[k]; prec = st["n_eff"] / sig2[k] + 1.0 / tau2
            mean = (st["n_eff"] * st["ybar"] / sig2[k] + m[fam_of[k]] / tau2) / prec
            mu[k] = rnd.gauss(mean, math.sqrt(1.0 / prec))
        # sigma_k^2 | rest   (weighted SSE, effective n)
        for k in keys:
            st = stats[k]
            sse = sum(w * (y - mu[k]) ** 2 for y, w in st["ys"]) * (st["n_eff"] / max(st["sw"], 1e-9))
            sig2[k] = max(1e-3, invgamma((nu + st["n_eff"]) / 2.0, (nu * s2 + sse) / 2.0, rnd))
        # family means | rest
        for f in fams:
            ks = [k for k in keys if fam_of[k] == f]
            prec = len(ks) / tau2 + 1.0 / 100.0
            mean = (sum(mu[k] for k in ks) / tau2) / prec
            m[f] = rnd.gauss(mean, math.sqrt(1.0 / prec))
        # tau^2 | rest
        ss = sum((mu[k] - m[fam_of[k]]) ** 2 for k in keys)
        tau2 = max(1e-3, invgamma(2.0 + len(keys) / 2.0, 0.5 + ss / 2.0, rnd))
        # s2 | rest  (scale of the shape hierarchy)
        s2 = max(1e-3, rnd.gammavariate(2.0 + len(keys) * nu / 2.0,
                                        1.0 / (1.0 + (nu / 2.0) * sum(1.0 / sig2[k] for k in keys))))
        if it >= burn and (it - burn) % thin == 0:
            for k in keys:
                out[k]["mu"].append(mu[k]); out[k]["sig"].append(math.sqrt(sig2[k]))
            hyper["tau2"].append(tau2); hyper["s2"].append(s2)
            for f in fams:
                hyper["m"][f].append(m[f])
    return out, hyper, stats, fam_of


def q(xs, p):
    xs = sorted(xs); i = max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))
    return xs[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=["agency_task", "task", "agency"], default="agency_task")
    ap.add_argument("--draws", type=int, default=4000)
    ap.add_argument("--burn", type=int, default=1000)
    ap.add_argument("--min-anchors", type=int, default=1)
    ap.add_argument("--out", default="dashboard/data/hier_posterior.json")
    a = ap.parse_args()
    g, caps = anchors()
    g = {k: v for k, v in g.items() if len(v) >= a.min_anchors}
    fam = {"agency_task": lambda k: f"{k[0]}/{k[1]}", "task": lambda k: k[1], "agency": lambda k: k[0]}[a.family]
    draws, hyper, stats, fam_of = gibbs(g, fam, a.draws, a.burn)
    Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
    rows = []
    for k, d in draws.items():
        mus, sigs = d["mu"], d["sig"]
        med = [math.exp(x) for x in mus]
        cap = statistics.median(caps[k]) if caps.get(k) else None
        pex = None
        if cap:
            ps = [1 - Phi((math.log(cap) - mu_) / sg) for mu_, sg in zip(mus, sigs)]
            pex = {"mean": round(statistics.mean(ps), 3), "q05": round(q(ps, .05), 3), "q95": round(q(ps, .95), 3)}
        rows.append({**dict(zip(KEYF, k)), "family": fam_of[k],
                     "n_anchors": len(stats[k]["ys"]), "n_eff": round(stats[k]["n_eff"], 2),
                     "median_days": round(statistics.median(med), 1),
                     "ci50": [round(q(med, .25), 1), round(q(med, .75), 1)],
                     "ci90": [round(q(med, .05), 1), round(q(med, .95), 1)],
                     "sigma_mean": round(statistics.mean(sigs), 3),
                     "sigma_ci90": [round(q(sigs, .05), 3), round(q(sigs, .95), 3)],
                     "statutory_cap_days": cap, "p_exceed_cap": pex})
    rows.sort(key=lambda r: -r["n_eff"])
    out = {"built": "2026-09-15", "sampler": "conjugate Gibbs, two-level normal with a hierarchical shape",
           "draws": a.draws, "burn": a.burn, "family": a.family,
           "n_eff_note": "Kish effective sample size (sum w)^2/sum w^2, not the weight sum",
           "hyper": {"tau2_mean": round(statistics.mean(hyper["tau2"]), 4),
                     "tau2_ci90": [round(q(hyper["tau2"], .05), 4), round(q(hyper["tau2"], .95), 4)],
                     "s2_mean": round(statistics.mean(hyper["s2"]), 4)},
           "n_keys": len(rows), "rows": rows}
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print("tau^2 posterior mean %.3f  90%% CI [%.3f, %.3f]   (EB point estimate was a single number)"
          % (out["hyper"]["tau2_mean"], *out["hyper"]["tau2_ci90"]))
    print("%d keys -> %s\n" % (len(rows), a.out))
    print("%-40s %5s %6s %8s %18s %14s" % ("step key", "n", "n_eff", "median", "90% CI (days)", "sigma"))
    for r in rows[:14]:
        print("%-40s %5d %6.2f %8.1f %18s %14s" % (
            (r["agency_class"] + "/" + r["task_type"])[:40], r["n_anchors"], r["n_eff"], r["median_days"],
            "%.1f - %.1f" % (r["ci90"][0], r["ci90"][1]),
            "%.2f [%.2f,%.2f]" % (r["sigma_mean"], *r["sigma_ci90"])))


if __name__ == "__main__":
    main()
