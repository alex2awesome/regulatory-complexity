"""The looseness instrument.

Reading-ensemble protocol: each reader (an LLM instantiation, a human, a city
checklist) applies one judgment predicate to cases sweeping a latent severity
axis. A reader who behaves like a threshold has a cutoff b_j; the predicate's
LOOSENESS is the dispersion of {b_j} across defensible readers — the width of
the borderline band — and its DISCRETION EXPOSURE is the population mass
living inside the band. Thin predicates have zero-width bands by construction.

Planted-reading protocol: WE fix the true reading, generate decisions from it,
and test recovery. The ladder of planted worlds (threshold -> conjunction ->
gestalt) validates the instrument and yields codability profiles kappa(L) —
"can code capture this?" answered where the answer is known.

Pure python, no LLM anywhere: models only produce the decisions consumed here.
"""

import random
import statistics
from itertools import combinations


# ---------------------------------------------------------------- cutoff fit

def fit_cutoff(thetas, decisions):
    """Best 1-D threshold reader explaining (theta, decision) pairs.

    Tries both directions (predicate true above cutoff / below cutoff);
    returns dict(b, direction, err_rate, n). err_rate near 0 means the reader
    IS a threshold on this axis; a high err_rate flags a non-threshold reader
    (multidimensional or unstable reading) — itself a finding, not noise to
    average away.
    """
    pairs = sorted(zip(thetas, decisions))
    n = len(pairs)
    xs = [p[0] for p in pairs]
    cuts = [xs[0] - 1e-9] + [(xs[i] + xs[i + 1]) / 2 for i in range(n - 1)] + [xs[-1] + 1e-9]
    best = None
    for direction in ("above", "below"):
        for b in cuts:
            err = sum(
                1 for t, d in pairs
                if d != ((t > b) if direction == "above" else (t < b))
            )
            if best is None or err < best["errors"]:
                best = {"b": b, "direction": direction, "errors": err}
    return {"b": round(best["b"], 4), "direction": best["direction"],
            "err_rate": best["errors"] / max(n, 1), "n": n}


def bootstrap_cutoff_ci(thetas, decisions, n_boot=500, seed=0, alpha=0.1):
    rng = random.Random(seed)
    pairs = list(zip(thetas, decisions))
    bs = []
    for _ in range(n_boot):
        sample = [rng.choice(pairs) for _ in pairs]
        bs.append(fit_cutoff([p[0] for p in sample], [p[1] for p in sample])["b"])
    bs.sort()
    lo = bs[int(alpha / 2 * n_boot)]
    hi = bs[int((1 - alpha / 2) * n_boot) - 1]
    return (round(lo, 4), round(hi, 4))


# ------------------------------------------------------- ensemble looseness

NONTHRESHOLD_TOL = 0.15  # err_rate above this -> reader not representable as a cutoff


def ensemble_looseness(responses_by_reader):
    """responses_by_reader: {reader_id: [(theta, decision), ...]}.

    Returns per-reader fits plus the looseness summary over threshold-like
    readers. Non-threshold readers are excluded from the band but REPORTED —
    a predicate many readers can't reduce to a cutoff is loose in a deeper
    way (multidimensional), and averaging would hide that.
    """
    fits = {}
    for reader, resp in responses_by_reader.items():
        thetas = [r[0] for r in resp]
        decisions = [r[1] for r in resp]
        fits[reader] = fit_cutoff(thetas, decisions)

    threshold_readers = {r: f for r, f in fits.items() if f["err_rate"] <= NONTHRESHOLD_TOL}
    cutoffs = sorted(f["b"] for f in threshold_readers.values())
    summary = {"per_reader": fits,
               "n_readers": len(fits),
               "n_threshold_readers": len(threshold_readers),
               "n_nonthreshold_readers": len(fits) - len(threshold_readers)}
    if len(cutoffs) >= 2:
        k = len(cutoffs)
        summary.update({
            "band_full": (cutoffs[0], cutoffs[-1]),
            "band_iqr": (cutoffs[k // 4], cutoffs[(3 * k) // 4] if k > 3 else cutoffs[-1]),
            "cutoff_sd": round(statistics.pstdev(cutoffs), 4),
            "cutoff_median": round(statistics.median(cutoffs), 4),
        })
    return summary


def band_mass(band, population_thetas):
    """Discretion exposure: fraction of the population inside the band —
    the people for whom the word does not decide."""
    lo, hi = band
    inside = sum(1 for t in population_thetas if lo <= t <= hi)
    return inside / max(len(population_thetas), 1)


# ------------------------------------------------- planted worlds (the ladder)

def threshold_world(n=200, b=0.6, noise=0.0, seed=0):
    """Rung 1: decisions from a planted 1-D cutoff. Code must win."""
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        t = rng.random()
        d = t > b
        if rng.random() < noise:
            d = not d
        X.append({"f1": t})
        y.append(d)
    return X, y


def conjunction_world(n=200, b1=0.5, b2=0.7, noise=0.0, seed=0):
    """Rung 2: violation iff BOTH axes exceed cutoffs. Code wins at larger L."""
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        t1, t2 = rng.random(), rng.random()
        d = (t1 > b1) and (t2 > b2)
        if rng.random() < noise:
            d = not d
        X.append({"f1": t1, "f2": t2})
        y.append(d)
    return X, y


def gestalt_world(n=200, noise=0.0, seed=0):
    """Rung 3: XOR structure no stump/conjunction/disjunction captures —
    'needs a model' by construction. The instrument must report the plateau."""
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        t1, t2 = rng.random(), rng.random()
        d = (t1 > 0.5) != (t2 > 0.5)
        if rng.random() < noise:
            d = not d
        X.append({"f1": t1, "f2": t2})
        y.append(d)
    return X, y


# ------------------------------------------------- program fitting: kappa(L)

def _grid(lo=0.0, hi=1.0, steps=21):
    return [lo + (hi - lo) * i / (steps - 1) for i in range(steps)]


def _acc(pred, X, y):
    return sum(1 for x, d in zip(X, y) if pred(x) == d) / max(len(y), 1)


def fit_program(X, y, cls):
    """Best program in a class, by grid search. Returns (predict_fn, train_acc).
    Classes, in ascending complexity L:
      constant  — L0, majority class
      stump     — L1, one threshold on one feature, either direction
      conj2     — L2, conjunction of two stumps
      disj2     — L2, disjunction of two stumps
    """
    feats = sorted(X[0].keys())

    def stumps():
        for f in feats:
            for b in _grid():
                for direction in (True, False):
                    yield (lambda x, f=f, b=b, d=direction: (x[f] > b) == d)

    if cls == "constant":
        maj = sum(y) * 2 >= len(y)
        pred = lambda x, m=maj: m
        return pred, _acc(pred, X, y)
    if cls == "stump":
        best = max(stumps(), key=lambda p: _acc(p, X, y))
        return best, _acc(best, X, y)
    if cls in ("conj2", "disj2"):
        cands = list(stumps())
        op = all if cls == "conj2" else any
        best, best_acc = None, -1
        for p1, p2 in combinations(cands, 2):
            pred = lambda x, a=p1, b=p2, op=op: op([a(x), b(x)])
            a = _acc(pred, X, y)
            if a > best_acc:
                best, best_acc = pred, a
        return best, best_acc
    raise ValueError(cls)


def codability_profile(world_fn, classes=("constant", "stump", "conj2", "disj2"),
                       n_train=200, n_test=400, seed=0, **world_kwargs):
    """kappa(L): held-out accuracy of the best program per class against the
    planted world. A profile that saturates at some L says 'code captures
    this at complexity L'; a plateau below 1 says 'not with these program
    classes' — with the planted ladder telling you whether the instrument
    itself can be trusted to detect each case."""
    Xtr, ytr = world_fn(n=n_train, seed=seed, **world_kwargs)
    Xte, yte = world_fn(n=n_test, seed=seed + 1, **world_kwargs)
    profile = {}
    for cls in classes:
        pred, _ = fit_program(Xtr, ytr, cls)
        profile[cls] = round(_acc(pred, Xte, yte), 4)
    return profile


def identifiability_curve(b_true=0.6, ns=(10, 20, 40, 80, 160), noise=0.1, n_rep=20, seed=0):
    """How much decision data does it take to recover a planted reading?
    Bounds what revealed-reading estimation can extract from permit records."""
    rng = random.Random(seed)
    curve = {}
    for n in ns:
        errs = []
        for rep in range(n_rep):
            X, y = threshold_world(n=n, b=b_true, noise=noise, seed=rng.randrange(10 ** 9))
            fit = fit_cutoff([x["f1"] for x in X], y)
            errs.append(abs(fit["b"] - b_true))
        curve[n] = round(statistics.mean(errs), 4)
    return curve
