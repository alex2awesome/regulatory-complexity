"""Layer-2 static looseness screener.

Scores a discourse span (typically a TEST or EXCEPTION) for predicted
looseness using the linguistic typology: relative gradable adjectives
(Kennedy 2007 — context-supplied threshold), multidimensional/evaluative
heads (Sassoon), explicit delegation markers (assigned discretion, a distinct
mechanism), open-ended enumerations, and hedged quantifiers; offset by
thinness markers (numbers, dates, dimensions, cross-references).

EPISTEMIC STATUS: every score this module emits is a HYPOTHESIS. Per the
retraction lesson, a static rating — lexicon-based or LLM-based — is never a
measurement of looseness; the synthetic instrument (looseness.py) is. The
screener exists to be calibrated against the instrument on a subsample
(calibrate()) and then applied at scale with that calibration's uncertainty.
"""

import re
import statistics

RELATIVE_GRADABLE = {
    "adequate", "inadequate", "reasonable", "unreasonable", "substantial",
    "sufficient", "insufficient", "proper", "improper", "appropriate",
    "suitable", "excessive", "unsanitary", "sanitary", "hazardous",
    "dangerous", "safe", "unsafe", "good", "sound", "effective",
    "ineffective", "faulty", "defective", "deteriorated", "dilapidated",
    "necessary", "serious", "significant", "timely", "prompt", "promptly",
}

# Absolute gradable / endpoint-standard words: gradable but with a fixed
# endpoint, hence far tighter than relative ones (Kennedy & McNally).
ABSOLUTE_GRADABLE = {"complete", "closed", "open", "empty", "full", "flat", "straight", "dry"}

DELEGATION_MARKERS = [
    "in the opinion of", "to the satisfaction of", "as determined by",
    "as deemed", "deemed by", "at the discretion of", "acceptable to",
    "as approved by", "as required by the",
]

OPEN_ENUMERATION = [
    "including, but not limited to", "including but not limited to",
    "shall include, but not be limited to", "or otherwise", "any other",
    "such as",
]

THIN_MARKERS = [
    r"\b\d+(?:,\d{3})*(?:\.\d+)?\b",          # numbers
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d",
    r"\b\d+\s*(?:feet|foot|inches|square|percent|days|years|months)\b",
    r"\bsection\s+\d", r"\b\d+\.\d+\b",        # cross-references
]


def screen(text):
    """Feature dict + heuristic looseness score in [0, 1]. HYPOTHESIS ONLY."""
    t = text.lower()
    words = re.findall(r"[a-z]+", t)
    feats = {
        "relative_gradable": sorted({w for w in words if w in RELATIVE_GRADABLE}),
        "absolute_gradable": sorted({w for w in words if w in ABSOLUTE_GRADABLE}),
        "delegation": [m for m in DELEGATION_MARKERS if m in t],
        "open_enumeration": [m for m in OPEN_ENUMERATION if m in t],
        "thin_markers": sum(1 for pat in THIN_MARKERS if re.search(pat, t)),
        "n_words": len(words),
    }
    score = 0.0
    score += 0.35 * min(len(feats["relative_gradable"]), 2) / 2
    score += 0.30 * (1 if feats["delegation"] else 0)
    score += 0.20 * (1 if feats["open_enumeration"] else 0)
    score -= 0.25 * min(feats["thin_markers"], 2) / 2
    score = max(0.0, min(1.0, score + 0.15))  # base rate: legal text is rarely fully thin
    mechanism = ("delegation" if feats["delegation"]
                 else "gradable" if feats["relative_gradable"]
                 else "enumeration" if feats["open_enumeration"]
                 else "none_detected")
    return {"text": text, "features": feats,
            "looseness_hypothesis": round(score, 3), "mechanism": mechanism,
            "status": "HYPOTHESIS — calibrate against the synthetic instrument"}


def calibrate(pairs):
    """pairs: [(screener_score, measured_band_width_or_mass), ...] from the
    subsample where the instrument was run. Simple OLS + Pearson r; the
    regression is itself a finding (does linguistics predict behavior?)."""
    n = len(pairs)
    if n < 3:
        raise ValueError("need >= 3 calibration points")
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    sy = statistics.pstdev(ys)
    sx = statistics.pstdev(xs)
    r = (sxy / n) / (sx * sy) if sx and sy else 0.0
    resid = [y - (intercept + slope * x) for x, y in pairs]
    return {"n": n, "slope": round(slope, 4), "intercept": round(intercept, 4),
            "pearson_r": round(r, 4),
            "resid_sd": round(statistics.pstdev(resid), 4)}
