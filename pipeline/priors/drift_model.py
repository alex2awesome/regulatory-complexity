#!/usr/bin/env python3
"""Non-stationary duration: a latent log-mean that walks in continuous time.

Alex's point: timing observations are draws from one distribution that MOVES, not from a fixed one.
That is a local-level state-space model, and it replaces two hacks in `latent_timing.py` — exponential
recency weighting and a two-window "refit on the recent half".

    state      mu_t  |  mu_s  ~  Normal(mu_s, tau^2 * (t - s))      continuous-time random walk
    observation  y_t  =  log(duration)  ~  Normal(mu_t, r_k^2)      r depends on the evidence tier

Evidence is dated and irregularly spaced (ours spans 1999-2026), so the state variance grows with the
gap rather than per observation. A Kalman filter gives the filtered mean at any date, including today;
a backward pass gives the smoothed path, which is what you want for "what was it in 2019".

Known changepoints (a fee resolution superseded, an ordinance amended, a department reorganised) are
injected as a variance shock at that date: the process is allowed to jump there rather than being
forced to explain the jump as noise. Where a version date is known this is far better identified than
a changepoint the model has to find for itself.

  python3 pipeline/priors/drift_model.py [--key "agency_class/task_type"] [--out dashboard/data/drift.json]
"""
import argparse, collections, glob, json, math, pathlib, statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
# observation variance in log space, by evidence tier: an audited figure is tighter than a forum post
R = {"verifiable_official": 0.10, "inferred": 0.15, "designed_document": 0.25,
     "statutory": 0.40, "community_reported": 0.55}
TAU2 = 0.05          # per-year variance of the latent walk
SHOCK = 0.60         # extra variance injected at a known changepoint


def _v(o, k):
    d = o.get("value") if isinstance(o.get("value"), dict) else o
    x = d.get(k) if isinstance(d, dict) else None
    return float(x) if isinstance(x, (int, float)) and x > 0 else None


def _t(o):
    s = str(o.get("date") or "")
    y = "".join(c for c in s[:4] if c.isdigit())
    if len(y) != 4:
        return None
    frac = 0.0
    if len(s) >= 7 and s[4] == "-" and s[5:7].isdigit():
        frac = (int(s[5:7]) - 1) / 12.0
    return int(y) + frac


def kalman(obs, changepoints=(), tau2=TAU2, shock=SHOCK):
    """obs: [(t, y, r2)] sorted by t -> filtered and smoothed latent log-mean."""
    if not obs:
        return [], None
    # diffuse prior: do not let the first observation act as its own prior, which double-counts it
    # and pulls the whole path toward the earliest evidence
    mu, P = obs[0][1], 1e6
    fwd = []
    prev_t = obs[0][0]
    for t, y, r2 in obs:
        dt = max(0.0, t - prev_t)
        P += tau2 * dt
        if any(prev_t < c <= t for c in changepoints):
            P += shock
        K = P / (P + r2)
        mu = mu + K * (y - mu)
        P = (1 - K) * P
        fwd.append({"t": round(t, 2), "mu": mu, "P": P, "y": y, "r2": r2})
        prev_t = t
    # RTS smoother
    sm = [dict(f) for f in fwd]
    for i in range(len(sm) - 2, -1, -1):
        dt = max(1e-6, sm[i + 1]["t"] - sm[i]["t"])
        Ppred = sm[i]["P"] + tau2 * dt
        G = sm[i]["P"] / Ppred
        sm[i]["mu_s"] = sm[i]["mu"] + G * (sm[i + 1].get("mu_s", sm[i + 1]["mu"]) - sm[i]["mu"])
        sm[i]["P_s"] = sm[i]["P"] + G * G * (sm[i + 1].get("P_s", sm[i + 1]["P"]) - Ppred)
    sm[-1]["mu_s"] = sm[-1]["mu"]; sm[-1]["P_s"] = sm[-1]["P"]
    return sm, {"mu_now": mu, "P_now": P}



# A single Gaussian random walk cannot do both jobs: a half-life long enough to use a 1999-2026 corpus
# makes the moves we measure 3-8 sigma events, and one short enough to represent them discards the corpus
# (the algebra is in docs/related-work-bayesian.md 9.1). So the state innovation gets two components —
# ordinary drift, plus rare jumps for the moments when a rule actually changed.
P_JUMP = 0.05          # prior probability that any given interval contains a rule change
JUMP_VAR = 0.55        # extra state variance when one does
SURPRISE_Z = 2.5       # a move this many sd beyond prediction is treated as a candidate jump


def kalman_jump(obs, changepoints=(), tau2=TAU2, shock=SHOCK, jump_var=JUMP_VAR, z=SURPRISE_Z):
    """Local level with TWO heavy tails, kept separate — the first version of this conflated them and
    produced a 1,955-day estimate for a step whose median is about 150 days.

    A large surprise has two possible causes and they need opposite responses:

      observation outlier  one strange case report, or a figure covering a different segment. The state
                           did not move. Response: DOWN-WEIGHT the observation (inflate r), which is
                           standard robust filtering and is sound on a single point.
      state jump           the rule changed. The state really did move. Response: inflate P so the filter
                           follows. But a single observation cannot distinguish this from an outlier —
                           only persistence can — so a jump is admitted ONLY at a date we know about.

    Inflating P on surprise, as the first version did, turns the filter into a follower: the gain goes to
    one and the estimate chases the last extreme value. That is why jumps must be anchored on known dates,
    which is also what the partial-order literature does (docs/related-work-bayesian.md 9.1).
    """
    if not obs:
        return [], None, []
    mu, P = obs[0][1], 1e6
    out, events = [], []
    prev_t = obs[0][0]
    for i, (t, y, r2) in enumerate(obs):
        dt = max(0.0, t - prev_t)
        P += tau2 * dt
        if any(prev_t < c <= t for c in changepoints):
            P += shock
            events.append({"t": round(t, 2), "kind": "known changepoint"})
        resid = y - mu
        S = P + r2
        if i > 0 and abs(resid) > z * math.sqrt(S):
            # treat as an observation outlier: widen r rather than moving the state
            scale = (abs(resid) / (z * math.sqrt(S))) ** 2
            r2 = r2 * scale
            S = P + r2
            events.append({"t": round(t, 2), "kind": "downweighted outlier",
                           "resid": round(resid, 3), "factor": round(scale, 1)})
        K = P / S
        mu = mu + K * resid
        P = (1 - K) * P
        out.append({"t": round(t, 2), "mu": mu, "P": P, "y": y, "r2": r2})
        prev_t = t
    sm = [dict(f) for f in out]
    for i in range(len(sm) - 2, -1, -1):
        dt = max(1e-6, sm[i + 1]["t"] - sm[i]["t"])
        Ppred = sm[i]["P"] + tau2 * dt
        G = sm[i]["P"] / Ppred
        sm[i]["mu_s"] = sm[i]["mu"] + G * (sm[i + 1].get("mu_s", sm[i + 1]["mu"]) - sm[i]["mu"])
    sm[-1]["mu_s"] = sm[-1]["mu"]
    return sm, {"mu_now": mu, "P_now": P}, events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dashboard/data/drift.json")
    ap.add_argument("--min-obs", type=int, default=4)
    a = ap.parse_args()
    obs = []
    for f in sorted(glob.glob(str(ROOT / "pipeline/priors/observations/*.json"))):
        obs += [o for o in (json.load(open(f)).get("observations") or []) if isinstance(o, dict)]
    g = collections.defaultdict(list)
    for o in obs:
        e = _v(o, "elapsed_days") or _v(o, "p50")
        t = _t(o)
        if not e or not t:
            continue
        sk = o.get("step_key") if isinstance(o.get("step_key"), dict) else {}
        key = (sk.get("agency_class") or "?", sk.get("task_type") or "?")
        g[key].append((t, math.log(e), R.get(str(o.get("evidence_tier")), 0.4), o.get("slug")))
    rows = []
    for key, pts in g.items():
        pts.sort()
        if len(pts) < a.min_obs:
            continue
        sm, now, jumps = kalman_jump([(t, y, r) for t, y, r, _ in pts])
        first, last = sm[0], sm[-1]
        rows.append({
            "agency_class": key[0], "task_type": key[1], "n_obs": len(pts),
            "span": [round(pts[0][0], 1), round(pts[-1][0], 1)],
            "median_days_start": round(math.exp(first.get("mu_s", first["mu"])), 1),
            "median_days_now": round(math.exp(now["mu_now"]), 1),
            "sd_now_log": round(math.sqrt(now["P_now"]), 3),
            "ci68_now": [round(math.exp(now["mu_now"] - math.sqrt(now["P_now"])), 1),
                         round(math.exp(now["mu_now"] + math.sqrt(now["P_now"])), 1)],
            "drift_factor": round(math.exp(now["mu_now"] - first.get("mu_s", first["mu"])), 2),
            "path": [{"t": s["t"], "median_days": round(math.exp(s.get("mu_s", s["mu"])), 1)} for s in sm],
            "slugs": sorted({s for _, _, _, s in pts if s}),
            "events": jumps, "n_events": len(jumps),
        })
    rows.sort(key=lambda r: -r["n_obs"])
    out = {"built": "2026-09-15", "model": "continuous-time local-level (Kalman) on log duration; "
           "state variance tau^2 per year; observation variance by evidence tier",
           "tau2_per_year": TAU2, "obs_variance_by_tier": R,
           "robustness": {"jump_var_at_known_changepoints": JUMP_VAR, "surprise_z": SURPRISE_Z,
                          "policy": "surprise down-weights the OBSERVATION; only a known date moves the STATE",
                              "why": "a single Gaussian walk cannot hold both a 27-year corpus and the "
                                     "measured 4-8 sigma moves; see docs/related-work-bayesian.md 9.1"},
           "n_keys": len(rows), "rows": rows}
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(f"{len(rows)} step keys with >= {a.min_obs} dated observations -> {a.out}\n")
    hdr = "{:40}{:>4}{:>14}{:>9}{:>9}{:>16}{:>8}".format("step key", "n", "span", "then", "now", "68% now", "drift")
    print(hdr)
    for r in rows[:14]:
        key = (r["agency_class"] + "/" + r["task_type"])[:40]
        span = "{:.0f}-{:.0f}".format(r["span"][0], r["span"][1])
        ci = "{:.0f}-{:.0f} d".format(r["ci68_now"][0], r["ci68_now"][1])
        print("{:40}{:>4}{:>14}{:>9.1f}{:>9.1f}{:>16}{:>8.2f}".format(
            key, r["n_obs"], span, r["median_days_start"], r["median_days_now"], ci, r["drift_factor"]))


if __name__ == "__main__":
    main()
