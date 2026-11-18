"""Score a predicted decision model against the planted one (decision.py).

Two questions, in the order they matter for the research question:

1. **Reading recovery**, one jurisdiction.  For each planted predicate, did the
   prediction state a criterion for the same case fact, and how close is its
   reading?  ``criterion_recall`` / ``criterion_precision`` on matched
   predicates; ``reading_exact`` (same operator and value within tolerance, or
   same categorical), ``reading_direction`` (same sign of the inequality);
   ceiling-relative recall when a ``decision_ceiling`` is supplied.
2. **Discretion recovery**, many jurisdictions of one statute.  For each
   standard predicate, the planted dispersion of readings across jurisdictions
   (how many distinct readings, the entropy over the reading space) versus the
   dispersion of the recovered readings, and the per-jurisdiction agreement.
   This is the measurement Dan asked for: the decision model's uncertainty
   observed through implementation variance, with the truth known.

Prediction format (loose, like the process-model scorer):

    {"criteria": [{"name": "...", "attribute": "ceiling_height_ft" | null,
                   "op": "ge", "value": 7.0, "unit": "feet",
                   "evaluated_at": "<activity name or id>" | null,
                   "fixable": true | null, "evidence": [...]}, ...]}

Matching is by attribute when the prediction names one, else by token overlap
between the predicted criterion name and the gold predicate's name, question
and reading label, using the same tokenizer as the activity aligner.

CLI:
    python -m pipeline.procbench.decision_metrics --pred pred.json --gold truth/processes/J1__S01.json \
        [--ceiling ceiling.json --task W1__J1__S01] --out score.json
    python -m pipeline.procbench.decision_metrics cross --pairs pred1.json:gold1.json pred2.json:gold2.json ... --out cross.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from pipeline.procbench.align import f1, toks  # noqa: E402

VERSION = "decision-metrics/1"
NUMERIC_TOL = 0.05        # relative tolerance for a numeric reading to count as exact
OPPOSITE = {"lt": "ge", "le": "gt", "gt": "le", "ge": "lt"}
DIRECTION = {"lt": -1, "le": -1, "gt": 1, "ge": 1}


def _load(x):
    if isinstance(x, (str, pathlib.Path)):
        return json.loads(pathlib.Path(x).read_text())
    return x


def _gold_entries(gold: dict) -> list[dict]:
    dm = gold.get("decision_model") or {}
    return list(dm.get("predicates", []))


def _text(e: dict) -> str:
    return " ".join(x for x in (e.get("name"), e.get("question"), (e.get("reading") or {}).get("label"),
                                e.get("attribute", "").replace("_", " ")) if x)


def _pred_text(c: dict) -> str:
    return " ".join(str(x) for x in (c.get("name"), c.get("attribute", "") and c["attribute"].replace("_", " "),
                                     c.get("text")) if x)


def match(pred_criteria: list[dict], gold: list[dict], threshold: float = 0.25) -> list[dict]:
    """Greedy one-to-one matching: attribute equality first, then token F1."""
    pairs, used_p, used_g = [], set(), set()
    for gi, g in enumerate(gold):
        for pi, c in enumerate(pred_criteria):
            if pi in used_p or c.get("attribute") is None:
                continue
            if c["attribute"] == g["attribute"]:
                pairs.append(dict(pred=pi, gold=gi, how="attribute", sim=1.0))
                used_p.add(pi)
                used_g.add(gi)
                break
    cands = []
    for gi, g in enumerate(gold):
        if gi in used_g:
            continue
        gt = toks(_text(g))
        for pi, c in enumerate(pred_criteria):
            if pi in used_p:
                continue
            s = f1(toks(_pred_text(c)), gt)
            if s >= threshold:
                cands.append((s, pi, gi))
    for s, pi, gi in sorted(cands, reverse=True):
        if pi in used_p or gi in used_g:
            continue
        pairs.append(dict(pred=pi, gold=gi, how="text", sim=round(s, 3)))
        used_p.add(pi)
        used_g.add(gi)
    return pairs


def _num(v):
    try:
        if isinstance(v, bool):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def reading_agreement(c: dict, g: dict) -> dict:
    """exact / direction / value_error for one matched pair."""
    r = g.get("reading") or {}
    gop, gv = r.get("op"), r.get("value")
    pop, pv = c.get("op"), c.get("value")
    out = dict(gold_op=gop, gold_value=gv, pred_op=pop, pred_value=pv, exact=False, direction=None,
               log_value_error=None)
    if gop in ("always",):
        out["exact"] = pop in ("always", None) and pv in (None, "")
        return out
    gn, pn = _num(gv), _num(pv)
    if gn is not None and pn is not None:
        out["log_value_error"] = round(abs(math.log(max(pn, 1e-9) / max(gn, 1e-9))), 4) if gn > 0 and pn > 0 \
            else round(abs(pn - gn), 4)
        same_dir = (DIRECTION.get(pop) == DIRECTION.get(gop)) if pop and gop in DIRECTION else None
        out["direction"] = same_dir
        close = abs(pn - gn) <= NUMERIC_TOL * max(abs(gn), 1e-9) or abs(pn - gn) < 1e-9
        out["exact"] = bool(close and (same_dir in (True, None)))
        return out
    # categorical / boolean / membership readings
    if isinstance(gv, list):
        out["exact"] = isinstance(pv, list) and set(map(str, pv)) == set(map(str, gv))
    else:
        out["exact"] = str(pv).lower() == str(gv).lower() and (pop in (gop, None))
    return out


def score(pred, gold, ceiling=None, task_id=None) -> dict:
    pred, gold = _load(pred), _load(gold)
    criteria = list(pred.get("criteria") or pred.get("decision_model", {}).get("predicates") or [])
    entries = _gold_entries(gold)
    if not entries:
        return dict(version=VERSION, note="gold has no decision_model (legacy world)", scored=False)
    pairs = match(criteria, entries)
    by_gold = {p["gold"]: p for p in pairs}
    acts = {a["id"]: a for a in gold.get("activities", [])}
    rows = []
    for gi, g in enumerate(entries):
        p = by_gold.get(gi)
        row = dict(pred_id=g["pred_id"], kind=g["kind"], matched=bool(p), attribute=g["attribute"])
        if p:
            c = criteria[p["pred"]]
            row.update(match_how=p["how"], sim=p["sim"], **reading_agreement(c, g))
            host = acts.get(g["evaluated_at"], {})
            ea = str(c.get("evaluated_at") or "")
            row["step_correct"] = bool(ea) and (ea == g["evaluated_at"] or f1(toks(ea), toks(host.get("name", ""))) >= 0.5
                                                 or f1(toks(ea), toks(host.get("local_name") or "")) >= 0.5)
            row["fixable_correct"] = (c.get("fixable") is None) and None or (bool(c.get("fixable")) == bool(g["fixable"]))
        rows.append(row)
    n = len(entries)
    matched = [r for r in rows if r["matched"]]
    exact = [r for r in matched if r["exact"]]
    direction = [r for r in matched if r.get("direction") is True]
    out = dict(
        version=VERSION, task_id=task_id, model_id=gold.get("model_id"), scored=True,
        criterion_recall=dict(num=len(matched), den=n, value=round(len(matched) / n, 4)),
        criterion_precision=dict(num=len(matched), den=len(criteria), value=round(len(matched) / len(criteria), 4) if criteria else None),
        reading_exact=dict(num=len(exact), den=n, value=round(len(exact) / n, 4)),
        reading_exact_given_matched=dict(num=len(exact), den=len(matched), value=round(len(exact) / len(matched), 4) if matched else None),
        reading_direction=dict(num=len(direction), den=len(matched), value=round(len(direction) / len(matched), 4) if matched else None),
        step_correct=dict(num=sum(1 for r in matched if r.get("step_correct")), den=len(matched),
                          value=round(sum(1 for r in matched if r.get("step_correct")) / len(matched), 4) if matched else None),
        by_kind={k: dict(total=sum(1 for r in rows if r["kind"] == k),
                         matched=sum(1 for r in matched if r["kind"] == k),
                         exact=sum(1 for r in exact if r["kind"] == k)) for k in sorted({r["kind"] for r in rows})},
        hallucinated_criteria=len(criteria) - len(matched),
        per_predicate=rows,
    )
    if ceiling is not None:
        ceiling = _load(ceiling)
        entry = None
        if isinstance(ceiling, list):
            entry = next((c for c in ceiling if c.get("task_id") == task_id or c.get("model_id") == gold.get("model_id")), None)
        elif isinstance(ceiling, dict):
            entry = ceiling
        dc = (entry or {}).get("decision_ceiling")
        if dc:
            recoverable = set(dc["recoverable_exact"]) | set(dc["recoverable_approx"])
            exact_rec = set(dc["recoverable_exact"])
            got = {r["pred_id"] for r in matched}
            got_exact = {r["pred_id"] for r in exact}
            out["ceiling"] = dict(
                recall_ceiling=dict(num=len(got & recoverable), den=len(recoverable),
                                    value=round(len(got & recoverable) / len(recoverable), 4) if recoverable else None),
                reading_exact_ceiling=dict(num=len(got_exact & exact_rec), den=len(exact_rec),
                                           value=round(len(got_exact & exact_rec) / len(exact_rec), 4) if exact_rec else None),
                recovered_below_ceiling=sorted(got - recoverable),
                availability_gap=round(1 - len(recoverable) / n, 4) if n else None)
    return out


# ------------------------------------------------------------ discretion --

def _entropy(counts: dict) -> float:
    tot = sum(counts.values())
    return round(-sum(c / tot * math.log(c / tot) for c in counts.values() if c), 4) if tot else 0.0


def cross(pairs: list[tuple], statute_filter: str | None = None) -> dict:
    """pairs: [(pred, gold), ...] for several jurisdictions of one statute.
    Planted versus recovered dispersion of readings, per standard/delegated predicate."""
    loaded = [(_load(p), _load(g)) for p, g in pairs]
    stat_ids = {g.get("stat_id") for _, g in loaded}
    if statute_filter:
        loaded = [(p, g) for p, g in loaded if g.get("stat_id") == statute_filter]
        stat_ids = {statute_filter}
    if len(stat_ids) != 1:
        raise ValueError("cross() needs jurisdictions of one statute; got %s" % sorted(stat_ids))
    per = {}
    for p, g in loaded:
        s = score(p, g)
        if not s.get("scored"):
            continue
        for row in s["per_predicate"]:
            if row["kind"] not in ("standard", "delegated", "local", "capped"):
                continue
            slot = per.setdefault(row["pred_id"], dict(kind=row["kind"], planted={}, recovered={}, agree=0, n=0, missing=0))
            slot["n"] += 1
            gv = str(row.get("gold_value"))
            slot["planted"][gv] = slot["planted"].get(gv, 0) + 1
            if row["matched"]:
                pv = str(row.get("pred_value"))
                slot["recovered"][pv] = slot["recovered"].get(pv, 0) + 1
                slot["agree"] += bool(row["exact"])
            else:
                slot["missing"] += 1
    out = {}
    for pid, slot in per.items():
        planted_h, recovered_h = _entropy(slot["planted"]), _entropy(slot["recovered"])
        out[pid] = dict(
            kind=slot["kind"], jurisdictions=slot["n"],
            planted_distinct_readings=len(slot["planted"]), recovered_distinct_readings=len(slot["recovered"]),
            planted_entropy=planted_h, recovered_entropy=recovered_h,
            entropy_ratio=round(recovered_h / planted_h, 4) if planted_h else None,
            per_jurisdiction_agreement=round(slot["agree"] / slot["n"], 4),
            missing=slot["missing"],
            planted_histogram=slot["planted"], recovered_histogram=slot["recovered"],
        )
    # ---- the capped/uncapped contrast (plan section 12) ------------------
    # Entropy recovery alone is trivially satisfiable when most jurisdictions
    # share a reading: predict the mode everywhere and the ratio looks fine. The
    # sharper question is whether the model recovers that variance COLLAPSES on
    # dimensions the statute bounded and SPREADS on those it left open. A real
    # statute does both at once (Welf. & Inst. Code 17001.5: five counties at
    # exactly the permitted 15 days, nine of eleven at exactly three months,
    # against 3.2x-40x variance on the uncapped grant), so the contrast holds
    # every county-level confounder fixed.
    def _spread(hist: dict) -> float | None:
        """Normalised distinct-reading count: 0 when every jurisdiction agrees."""
        n = sum(hist.values())
        return round((len(hist) - 1) / (n - 1), 4) if n > 1 else None

    families = {"capped": ("capped",), "uncapped": ("standard", "delegated", "local")}
    contrast = {}
    for family, kinds in families.items():
        members = {pid: v for pid, v in out.items() if v["kind"] in kinds}
        if not members:
            continue
        planted = [x for x in (_spread(v["planted_histogram"]) for v in members.values()) if x is not None]
        recovered = [x for x in (_spread(v["recovered_histogram"]) for v in members.values()) if x is not None]
        agree = [v["per_jurisdiction_agreement"] for v in members.values()]
        contrast[family] = dict(
            predicates=len(members),
            planted_spread=round(sum(planted) / len(planted), 4) if planted else None,
            recovered_spread=round(sum(recovered) / len(recovered), 4) if recovered else None,
            mean_agreement=round(sum(agree) / len(agree), 4) if agree else None)
    verdict = None
    if "capped" in contrast and "uncapped" in contrast:
        pc, pu = contrast["capped"]["planted_spread"], contrast["uncapped"]["planted_spread"]
        rc, ru = contrast["capped"]["recovered_spread"], contrast["uncapped"]["recovered_spread"]
        if None not in (pc, pu, rc, ru):
            # The GAP, not the ratio, is the primary statistic. A ratio is
            # undefined exactly when the capped family behaves ideally and shows
            # zero spread, which is the case we most want to score. The gap is
            # always defined and is the quantity of interest: how much wider is
            # variation where the statute stayed silent.
            verdict = dict(
                planted_gap=round(pu - pc, 4), recovered_gap=round(ru - rc, 4),
                gap_error=round(abs((ru - rc) - (pu - pc)), 4),
                planted_ratio=round(pu / pc, 3) if pc else None,
                recovered_ratio=round(ru / rc, 3) if rc else None,
                direction_correct=bool((ru - rc) > 0) if (pu - pc) > 0
                                  else bool((ru - rc) <= 0),
                note=("planted_gap is uncapped spread minus capped spread. A model that predicts "
                      "one reading everywhere collapses BOTH families to zero spread, so its "
                      "recovered_gap is 0 against a positive planted_gap: it gets no credit. "
                      "The ratio is reported only when the capped family shows non-zero spread."))
    return dict(version=VERSION, stat_id=next(iter(stat_ids)), n_jurisdictions=len(loaded), predicates=out,
                discretion_recovered=round(sum(v["entropy_ratio"] for v in out.values() if v["entropy_ratio"] is not None)
                                           / max(1, sum(1 for v in out.values() if v["entropy_ratio"] is not None)), 4),
                by_family=contrast, capped_vs_uncapped=verdict,
                caveat=("entropy_ratio is reported for continuity but is weak when one reading holds "
                        "most of the mass; prefer capped_vs_uncapped and per-predicate tail recovery"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    one = sub.add_parser("score")
    one.add_argument("--pred", required=True)
    one.add_argument("--gold", required=True)
    one.add_argument("--ceiling")
    one.add_argument("--task")
    one.add_argument("--out", required=True)
    cr = sub.add_parser("cross")
    cr.add_argument("--pairs", nargs="+", required=True, help="pred.json:gold.json ...")
    cr.add_argument("--statute")
    cr.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "cross":
        pairs = [tuple(x.split(":", 1)) for x in args.pairs]
        result = cross(pairs, args.statute)
    else:
        result = score(args.pred, args.gold, args.ceiling, args.task)
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k not in ("per_predicate", "predicates")}, indent=1))


if __name__ == "__main__":
    main()
