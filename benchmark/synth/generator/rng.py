"""Deterministic randomness + small date/stat helpers (stdlib only).

Every random draw in the generator comes from ``sub_rng(seed, *path)``: a RNG
keyed by a stable hash of the world seed plus a semantic path (e.g.
``("local_rule", "J2", "S03")``).  Consequences that matter:

* generation order does not affect any object's content (adding a jurisdiction
  does not reshuffle the others);
* any object can be regenerated in isolation for debugging;
* the same seed gives byte-identical worlds on any machine/Python 3.12 build
  (we never rely on ``hash()``, set iteration order, or float formatting).
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import date, timedelta

# ---------------------------------------------------------------- randomness


def sub_rng(seed: int, *path) -> random.Random:
    """A Random keyed by (seed, path). Stable across runs and machines."""
    key = "|".join([str(seed)] + [str(p) for p in path]).encode("utf-8")
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return random.Random(int.from_bytes(digest, "big"))


def pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def pick_n(rng: random.Random, seq, n: int) -> list:
    """n distinct items, order stable given rng."""
    items = list(seq)
    rng.shuffle(items)
    return items[: min(n, len(items))]


def chance(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def weighted(rng: random.Random, pairs):
    """pairs = [(item, weight), ...]"""
    total = sum(w for _, w in pairs)
    x = rng.random() * total
    for item, w in pairs:
        x -= w
        if x <= 0:
            return item
    return pairs[-1][0]


# ---------------------------------------------------------------- lognormal

Z90 = 1.2815515655446004  # Phi^-1(0.90)


def lognormal_params(median_days: float, p90_days: float):
    """(mu, sigma) of the underlying normal from a median and a p90."""
    med = max(float(median_days), 0.25)
    p90 = max(float(p90_days), med * 1.05)
    return math.log(med), math.log(p90 / med) / Z90


def sample_days(rng: random.Random, median_days: float, p90_days: float) -> int:
    """Draw a duration in whole days (>=0) from lognormal(median, p90)."""
    mu, sigma = lognormal_params(median_days, p90_days)
    val = math.exp(rng.gauss(mu, sigma))
    if median_days < 1:  # counter/online steps: same day or next day
        return 0 if val < 0.7 else int(round(min(val, 3)))
    return int(round(min(val, median_days * 12)))


# ---------------------------------------------------------------- statistics


def quantile(values, q: float) -> float:
    """Linear-interpolation quantile of a list of numbers (stdlib only)."""
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    return float(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo))


def median(values) -> float:
    return quantile(values, 0.5)


def r2(x: float) -> float:
    return round(float(x), 2)


# ---------------------------------------------------------------- dates


def dparse(s: str) -> date:
    y, m, d = (int(p) for p in s.split("-"))
    return date(y, m, d)


def dfmt(d: date) -> str:
    return d.isoformat()


def dadd(s: str, days: int) -> str:
    return dfmt(dparse(s) + timedelta(days=days))


def ddiff(a: str, b: str) -> int:
    return (dparse(a) - dparse(b)).days


def next_workday(s: str) -> str:
    """Push a date off Sat/Sun (counters and hearings are weekday events)."""
    d = dparse(s)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return dfmt(d)


def random_date_between(rng: random.Random, start: str, end: str) -> str:
    span = max(ddiff(end, start), 1)
    return dadd(start, rng.randrange(span))
