#!/usr/bin/env python3
"""Infer a latent duration distribution per step key from heterogeneous, biased, dated evidence.

Evidence about how long a step takes does not arrive as samples from one distribution. It arrives as
five different things, and treating them alike is how you get the 1.5x timing error the benchmark shows:

  official p50 / p90     summary statistics of the true distribution        -> moment constraints
  observed point values  a real case, or an agency's own measured figure    -> samples
  community reports      samples through a selection filter: a delayed
                         applicant posts, a normal one does not             -> tilted samples
  ranges ("3-6 weeks")   an interval covering most of the mass              -> quantile anchors
  statutory caps         a policy, not an observation of practice           -> NOT fitted; the
                         model instead reports P(exceed) as a derived number

Model: D ~ LogNormal(mu, sigma). In log space the selection tilt P(report | d) proportional to d**gamma
shifts the mean by gamma*sigma**2 and leaves the shape, so community evidence enters with that shift
removed. Gamma is estimated by pooling the step keys that carry both community and official evidence,
then bounded, because the per-key ratios are unstable (0.14x to 7.7x measured).

Dates matter: processes change. Observations are weighted by recency with a half-life, and the fit is
reported both weighted and unweighted so drift is visible rather than averaged away.

  python3 pipeline/priors/latent_timing.py [--half-life-years 3] [--min-n 2] [--out dashboard/data/latent_timing.json]
"""
import argparse, collections, glob, json, math, pathlib, statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
OFFICIAL = {"verifiable_official", "inferred"}
DESIGNED = {"designed_document"}
COMMUNITY = {"community_reported"}
Z90 = 1.2815515655446004


def _v(o, k):
    d = o.get("value") if isinstance(o.get("value"), dict) else o
    x = d.get(k) if isinstance(d, dict) else None
    return float(x) if isinstance(x, (int, float)) and x > 0 else None


def _year(o):
    s = str(o.get("date") or "")
    m = "".join(ch for ch in s[:4] if ch.isdigit())
    return int(m) if len(m) == 4 else None


def _key(o):
    sk = o.get("step_key") if isinstance(o.get("step_key"), dict) else {}
    return tuple((sk.get(f) or "unspecified") for f in
                 ("agency_class", "task_type", "channel", "blocking_party", "cadence", "jurisdiction_class"))


def load():
    obs = []
    for f in sorted(glob.glob(str(ROOT / "pipeline/priors/observations/*.json"))):
        d = json.load(open(f))
        obs += [o for o in (d.get("observations") or []) if isinstance(o, dict)]
    return obs


def estimate_gamma(groups):
    """Selection tilt, pooled over step keys holding both community and official evidence.

    ratio = community_median / official_median = exp(gamma * sigma^2). With sigma unknown per key we
    use the pooled log-ratio and a nominal sigma, and bound the result: the per-key ratios span two
    orders of magnitude, much of which is small-n noise and segment mismatch rather than selection.
    """
    lrs = []
    for k, g in groups.items():
        com = [x for x, _, _ in g["community"]]
        off = [x for x, _, _ in g["official"]]
        if len(com) >= 2 and len(off) >= 1:
            lrs.append(math.log(statistics.median(com) / statistics.median(off)))
    if not lrs:
        return 0.0, 0, None, "no step key carries both community and official evidence"
    med = statistics.median(lrs)
    sigma_nominal = 0.7
    raw = med / (sigma_nominal ** 2)
    # A selection story predicts a POSITIVE tilt: delayed applicants post, ordinary ones do not.
    # If the pooled estimate comes out negative, the data are not telling a selection story and the
    # honest move is to apply no correction and say why, rather than clamp to zero and imply one.
    if raw <= 0:
        return 0.0, len(lrs), round(med, 3), "not identified: pooled community evidence is FASTER than official, " \
            "the wrong sign for selection. Most likely the two measure different segments of the process. " \
            "No tilt applied."
    return min(2.0, raw), len(lrs), round(med, 3), None


def fit_key(g, gamma, half_life, now=2026):
    """Weighted fit in log space. Returns the latent distribution and what it rests on."""
    anchors = []          # (log_value, weight, what)
    def w_recency(y):
        if not y or not half_life:
            return 1.0
        return 0.5 ** (max(0, now - y) / half_life)

    for x, y, tier in g["official"]:
        anchors.append((math.log(x), 3.0 * w_recency(y), "official"))
    for x, y, tier in g["designed"]:
        anchors.append((math.log(x), 1.5 * w_recency(y), "designed"))
    for x, y, tier in g["community"]:
        anchors.append((math.log(x), 1.0 * w_recency(y), "community"))
    for p50, p90, y in g["quantiles"]:
        if p50:
            anchors.append((math.log(p50), 3.0 * w_recency(y), "p50"))
    if not anchors:
        return None

    W = sum(w for _, w, _ in anchors)
    mu_naive = sum(l * w for l, w, _ in anchors) / W
    if len(anchors) > 1:
        var = sum(w * (l - mu_naive) ** 2 for l, w, _ in anchors) / W
        sigma = max(0.15, math.sqrt(var))
    else:
        sigma = 0.7
    # sigma from a p50/p90 pair is better than spread across heterogeneous sources
    for p50, p90, _y in g["quantiles"]:
        if p50 and p90 and p90 > p50:
            sigma = max(0.15, math.log(p90 / p50) / Z90)
            break
    for lo, hi, _y in g["ranges"]:
        if lo and hi and hi > lo and not g["quantiles"]:
            sigma = max(0.15, math.log(hi / lo) / (2 * Z90))

    # remove the selection tilt from community evidence only
    shift = gamma * sigma ** 2
    corrected = []
    for l, w, what in anchors:
        corrected.append((l - shift if what == "community" else l, w, what))
    mu = sum(l * w for l, w, _ in corrected) / W

    med = math.exp(mu)
    p90 = math.exp(mu + Z90 * sigma)
    caps = [c for c, _y in g["caps"]]
    cap = statistics.median(caps) if caps else None
    p_exceed = None
    if cap:
        z = (math.log(cap) - mu) / sigma
        p_exceed = round(1 - 0.5 * (1 + math.erf(z / math.sqrt(2))), 3)

    # drift: refit on the most recent half of the dated evidence
    dated = []
    for x, y, _t in g["official"]:
        if y: dated.append((y, math.log(x) , 3.0))
    for x, y, _t in g["designed"]:
        if y: dated.append((y, math.log(x), 1.5))
    for x, y, _t in g["community"]:
        if y: dated.append((y, math.log(x) - shift, 1.0))
    for p50_, _p90, y in g["quantiles"]:
        if y and p50_: dated.append((y, math.log(p50_), 3.0))
    dated.sort(key=lambda r: r[0])
    drift = None
    if len(dated) >= 4:
        half = dated[len(dated) // 2:]
        Wl = sum(r[2] for r in half) or 1
        mu_recent = sum(l * w for _, l, w in half) / Wl
        drift = {"recent_median_days": round(math.exp(mu_recent), 1),
                 "since_year": half[0][0], "n_recent": len(half),
                 "ratio_recent_to_all": round(math.exp(mu_recent - mu), 2)}

    com = [x for x, _, _ in g["community"]]
    off = [x for x, _, _ in g["official"]]
    flags = []
    if com and off:
        r = statistics.median(com) / statistics.median(off)
        if r > 3 or r < 0.34:
            flags.append(f"community and official disagree by {r:.1f}x — likely different segments measured, "
                         f"not only selection bias")
    if cap and p_exceed is not None and p_exceed > 0.5:
        flags.append(f"the fitted distribution exceeds the {cap:.0f}-day statutory cap {100*p_exceed:.0f}% of the time")
    if len(anchors) < 3:
        flags.append("thin evidence: treat as indicative, not a distribution")

    return {"mu": round(mu, 4), "sigma": round(sigma, 4),
            "median_days": round(med, 1), "p90_days": round(p90, 1),
            "n_anchors": len(anchors), "weight_total": round(W, 2),
            "n_official": len(off), "n_designed": len(g["designed"]), "n_community": len(com),
            "statutory_cap_days": cap, "p_exceed_cap": p_exceed,
            "selection_shift_applied": round(shift, 3), "drift": drift, "flags": flags,
            "touch_median_days": (round(statistics.median(g["touch"]), 2) if g["touch"] else None),
            "queue_median_days": (round(statistics.median(g["queue"]), 1) if g["queue"] else None),
            "slugs": sorted(g["slugs"]), "example_quote": g["quote"]}



def pool(rows, min_keep=1):
    """Partial pooling over step keys — the Gaussian layer of the model.

    Each key's log-scale location is treated as a draw from its family's distribution:
        mu_key ~ Normal(mu_family, tau^2),   family = (agency_class, task_type)
        mu_hat_key | mu_key ~ Normal(mu_key, sigma^2 / n_key)
    Empirical Bayes gives the posterior mean as a precision-weighted blend, so a key resting on two
    anchors is pulled toward its family while a key resting on fourteen barely moves. Without this, a
    thin key reports whatever its one or two sources happened to say, which is how a prior built from
    620 observations still produces nonsense for the 40 keys that carry two.
    """
    fam = collections.defaultdict(list)
    for r in rows:
        fam[(r["agency_class"], r["task_type"])].append(r)
    grand = statistics.mean([r["mu"] for r in rows]) if rows else 0.0
    for key, group in fam.items():
        mus = [r["mu"] for r in group]
        fam_mean = statistics.mean(mus) if mus else grand
        # Between-key variance, with the within-key noise removed. The spread of observed key means is
        # Var(y) = tau^2 + mean(s^2_k), so using the raw spread over-states tau^2 and under-shrinks.
        if len(mus) > 1:
            s2_bar = statistics.mean([max(0.05, r["sigma"] ** 2) / max(1.0, r["weight_total"]) for r in group])
            tau2 = max(0.05, statistics.pvariance(mus) - s2_bar)
        else:
            tau2 = 0.35
        for r in group:
            # NOTE: n is the summed evidence WEIGHT (official 3.0, designed 1.5, community 1.0), used as an
            # effective sample size. One audited figure therefore counts like three community reports, which
            # is the intent, but it also narrows the interval accordingly — intervals are optimistic.
            n = max(1.0, r["weight_total"])
            s2 = max(0.05, r["sigma"] ** 2)
            w = tau2 / (tau2 + s2 / n)          # weight on the key's own estimate
            mu_post = w * r["mu"] + (1 - w) * fam_mean
            se = math.sqrt(1.0 / (n / s2 + 1.0 / tau2))
            r["pooled"] = {
                "family": f"{key[0]}/{key[1]}", "family_n_keys": len(group),
                "shrinkage_toward_family": round(1 - w, 3),
                "mu_pooled": round(mu_post, 4),
                "median_days_pooled": round(math.exp(mu_post), 1),
                "ci68_days": [round(math.exp(mu_post - se), 1), round(math.exp(mu_post + se), 1)],
                "ci95_days": [round(math.exp(mu_post - 1.96 * se), 1), round(math.exp(mu_post + 1.96 * se), 1)],
                "moved_by_factor": round(math.exp(mu_post - r["mu"]), 2),
            }
            if r.get("statutory_cap_days"):
                z = (math.log(r["statutory_cap_days"]) - mu_post) / max(0.15, r["sigma"])
                r["pooled"]["p_exceed_cap_pooled"] = round(1 - 0.5 * (1 + math.erf(z / math.sqrt(2))), 3)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--half-life-years", type=float, default=3.0)
    ap.add_argument("--min-n", type=int, default=2)
    ap.add_argument("--out", default="dashboard/data/latent_timing.json")
    a = ap.parse_args()

    groups = collections.defaultdict(lambda: {"official": [], "designed": [], "community": [], "quantiles": [],
                                              "ranges": [], "caps": [], "touch": [], "queue": [],
                                              "slugs": set(), "quote": None})
    for o in load():
        k = _key(o); g = groups[k]; y = _year(o); tier = o.get("evidence_tier")
        g["slugs"].add(o.get("slug") or "?")
        if not g["quote"] and o.get("quote"):
            g["quote"] = str(o["quote"])[:200]
        e = _v(o, "elapsed_days")
        if e:
            (g["official"] if tier in OFFICIAL else g["designed"] if tier in DESIGNED
             else g["community"] if tier in COMMUNITY else g["designed"]).append((e, y, tier))
        p50, p90 = _v(o, "p50"), _v(o, "p90")
        if p50 or p90:
            g["quantiles"].append((p50, p90, y))
        d = o.get("value") if isinstance(o.get("value"), dict) else {}
        rng = d.get("range_days") if isinstance(d, dict) else None
        if isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, (int, float)) and x > 0 for x in rng):
            g["ranges"].append((float(rng[0]), float(rng[1]), y))
        c = _v(o, "statutory_cap_days")
        if c:
            g["caps"].append((c, y))
        t, q = _v(o, "touch_days"), _v(o, "queue_days")
        if t: g["touch"].append(t)
        if q: g["queue"].append(q)

    gamma, ngk, medlr, gamma_note = estimate_gamma(groups)
    rows = []
    for k, g in groups.items():
        n = len(g["official"]) + len(g["designed"]) + len(g["community"]) + len(g["quantiles"])
        if n < a.min_n:
            continue
        fit = fit_key(g, gamma, a.half_life_years)
        if not fit:
            continue
        rows.append({**dict(zip(("agency_class", "task_type", "channel", "blocking_party",
                                 "cadence", "jurisdiction_class"), k)), **fit})
    rows = pool(rows)
    rows.sort(key=lambda r: -r["n_anchors"])
    out = {"built": "2026-09-15",
           "model": "Duration is continuous and right-skewed, so the family is LogNormal: log D ~ Normal(mu, sigma^2). "
                    "Key-level means are partially pooled toward their (agency_class, task_type) family by empirical "
                    "Bayes, which is the Gaussian layer that lets thin keys borrow strength. Statutory caps are policy, "
                    "not observations: they are excluded from the fit and re-enter as a derived P(exceed).",
           "selection_gamma": round(gamma, 3), "gamma_from_n_keys": ngk,
           "median_log_ratio_community_over_official": medlr, "selection_gamma_note": gamma_note,
           "half_life_years": a.half_life_years, "n_step_keys": len(rows), "rows": rows}
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"selection gamma = {gamma:.3f} (from {ngk} step keys with both community and official evidence; "
          f"median log-ratio {medlr})")
    if gamma_note:
        print(f"  NOTE: {gamma_note}")
    print(f"{len(rows)} step keys fitted -> {a.out}\n")
    print(f"{'step key':40}{'raw':>7}{'pooled':>8}{'68% interval':>18}{'shrink':>8}{'n':>4}")
    for r in rows[:16]:
        p_ = r.get("pooled") or {}
        ci = p_.get("ci68_days") or [0, 0]
        print(f"{(r['agency_class']+'/'+r['task_type'])[:40]:40}{r['median_days']:>7.1f}"
              f"{p_.get('median_days_pooled', 0):>8.1f}{f'{ci[0]:.0f}-{ci[1]:.0f} d':>18}"
              f"{p_.get('shrinkage_toward_family', 0):>8.2f}{r['n_anchors']:>4}")
    thin = [r for r in rows if r["n_anchors"] <= 2]
    print(f"\n{len(thin)} of {len(rows)} keys rest on <=2 anchors; median shrinkage toward family "
          f"{statistics.median([r['pooled']['shrinkage_toward_family'] for r in thin]):.2f}" if thin else "")


if __name__ == "__main__":
    main()
