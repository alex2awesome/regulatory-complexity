#!/usr/bin/env python3
"""How many process steps has nobody disclosed? Stratified capture-recapture.

Treat each document as a capture occasion and each step as a species. Chao1 estimates the species you
have not yet seen from how many you saw exactly once versus exactly twice:

    S_est = S_obs + f1^2 / (2 * f2)          (bias-corrected form used when f2 = 0)

Plain Chao1 is invalid here, for a reason built into the subject: **catchability is not equal**. An
applicant-facing step is disclosed by almost every document kind; a staff-only step is disclosed by
almost none. Pooling them makes the estimate meaningless. So the estimate is computed **per visibility
stratum** and summed, which is the standard remedy for heterogeneous capture probability.

  python3 pipeline/priors/richness.py --gold                 # on the 16 real gold models (visibility known)
  python3 pipeline/priors/richness.py --fit runs/incremental/real_dros   # on an incremental fit
"""
import argparse, collections, glob, json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def chao1(counts):
    """counts: list of per-species capture counts (>=1). -> (S_obs, S_est, f1, f2)"""
    s = len(counts)
    f1 = sum(1 for c in counts if c == 1)
    f2 = sum(1 for c in counts if c == 2)
    if f2 > 0:
        est = s + (f1 * f1) / (2.0 * f2)
    elif f1 > 1:
        est = s + f1 * (f1 - 1) / 2.0          # bias-corrected, for f2 = 0
    else:
        est = float(s)
    return s, est, f1, f2


def var_chao1(s, f1, f2):
    if f2 <= 0:
        return None
    r = f1 / f2
    return f2 * (0.5 * r ** 2 + r ** 3 + 0.25 * r ** 4)


def from_gold():
    """Each gold activity's capture count = how many distinct source documents evidence it."""
    rows = []
    for f in sorted(glob.glob(str(ROOT / "benchmark/realworld/gold/*.json"))):
        g = json.load(open(f))
        strata = collections.defaultdict(list)
        for a in g["activities"]:
            docs = {e.get("doc") for e in (a.get("evidence") or []) if e.get("doc")}
            if not docs:
                continue
            strata[a.get("visibility") or "unknown"].append(len(docs))
        if not strata:
            continue
        tot_obs = tot_est = 0.0
        per = {}
        for v, counts in strata.items():
            s, est, f1, f2 = chao1(counts)
            per[v] = {"observed": s, "estimated": round(est, 1), "f1": f1, "f2": f2,
                      "unseen": round(est - s, 1)}
            tot_obs += s; tot_est += est
        # pooled, ignoring strata — shown only to demonstrate how much it misleads
        allc = [c for cs in strata.values() for c in cs]
        ps, pe, pf1, pf2 = chao1(allc)
        rows.append({"model": pathlib.Path(f).stem, "n_activities": len(g["activities"]),
                     "observed": int(tot_obs), "estimated_stratified": round(tot_est, 1),
                     "unseen_stratified": round(tot_est - tot_obs, 1),
                     "estimated_pooled": round(pe, 1), "unseen_pooled": round(pe - ps, 1),
                     "per_stratum": per})
    return rows


def from_fit(d):
    st = json.load(open(pathlib.Path(d) / "state.json"))
    counts = [n["support"] for n in st["nodes"]]
    s, est, f1, f2 = chao1(counts)
    v = var_chao1(s, f1, f2)
    return {"dir": str(d), "observed": s, "estimated": round(est, 1), "f1": f1, "f2": f2,
            "unseen": round(est - s, 1), "se": (round(math.sqrt(v), 1) if v else None),
            "caveat": "unstratified and therefore unreliable: an incremental fit carries no visibility "
                      "label per node, and its over-splitting turns duplicates into extra singletons, "
                      "which inflates f1 and so inflates the estimate"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", action="store_true")
    ap.add_argument("--fit")
    ap.add_argument("--out", default="dashboard/data/richness.json")
    a = ap.parse_args()
    out = {"built": "2026-09-15",
           "method": "Chao1 per visibility stratum, summed; capture occasion = a distinct source document"}
    if a.gold:
        rows = from_gold(); out["gold"] = rows
        print("%-46s %5s %6s %9s %9s %9s" % ("gold model", "acts", "obs", "strat.est", "unseen", "pooled"))
        for r in rows:
            print("%-46s %5d %6d %9.1f %9.1f %9.1f" % (r["model"][:46], r["n_activities"], r["observed"],
                  r["estimated_stratified"], r["unseen_stratified"], r["estimated_pooled"]))
        tot_o = sum(r["observed"] for r in rows); tot_s = sum(r["estimated_stratified"] for r in rows)
        tot_p = sum(r["estimated_pooled"] for r in rows)
        print("\npooled across models: %d observed, %.0f estimated stratified (%.0f unseen), "
              "%.0f if you ignore strata" % (tot_o, tot_s, tot_s - tot_o, tot_p))
        by = collections.defaultdict(lambda: [0, 0.0])
        for r in rows:
            for v, s in r["per_stratum"].items():
                by[v][0] += s["observed"]; by[v][1] += s["estimated"]
        print("\nby visibility stratum — the whole point of stratifying:")
        for v, (o, e) in sorted(by.items(), key=lambda x: -x[1][0]):
            print("   %-22s observed %4d  estimated %6.1f  implied unseen %5.1f  (%.0f%% more)"
                  % (v, o, e, e - o, 100 * (e - o) / max(o, 1)))
    if a.fit:
        r = from_fit(a.fit); out["fit"] = r
        print("\nfit %s: observed %d, Chao1 %.1f (unseen %.1f, se %s)\n  %s"
              % (r["dir"], r["observed"], r["estimated"], r["unseen"], r["se"], r["caveat"]))
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
