#!/usr/bin/env python3
"""Metrics for process-model reconstruction, computed from an alignment.

Every metric is reported as {"num", "den", "value"} so runs can be re-aggregated
(sum numerators, sum denominators) instead of averaging averages. Formulas are in
pipeline/procbench/README.md.
"""

import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))   # pipeline/
try:
    from procbench.align import (T_DISTRACTOR, VISIBLE, canon_actor, closure, f1, sim, toks)
except ImportError:                       # imported as pipeline.procbench.metrics
    from pipeline.procbench.align import (T_DISTRACTOR, VISIBLE, canon_actor, closure, f1,
                                          sim, toks)

def frac(num, den, **extra):
    return {"num": round(num, 4) if isinstance(num, float) else num, "den": den,
            "value": round(num / den, 4) if den else None, **extra}

def mean(xs):
    return round(sum(xs) / len(xs), 4) if xs else None

# ------------------------------------------------------------------- ceiling

def ceiling_refs(ceiling, gold):
    """Gold activity ids that the public artifacts provably reveal
    (recoverable_exact u recoverable_approx), resolved through element_ref too."""
    if not ceiling:
        return None
    raw = list(ceiling.get("recoverable_exact") or []) + list(ceiling.get("recoverable_approx") or [])
    refs = set()
    for r in raw:
        r = r.get("ref") or r.get("id") if isinstance(r, dict) else r
        if r:
            refs.add(re.split(r"[.#:]", str(r))[0])
    ids = {a["id"] for a in gold["activities"]}
    out = refs & ids
    for a in gold["activities"]:        # element-level ceiling entries (E2, L1, ...)
        if a["element_ref"] and str(a["element_ref"]) in refs:
            out.add(a["id"])
    return out

def pick_ceiling(obj, task=None):
    """ceiling.json may be one object, a list of them, or a dict keyed by task."""
    if obj is None:
        return None
    if isinstance(obj, list):
        cands = obj
    elif "recoverable_exact" in obj or "elements_total" in obj:
        cands = [obj]
    else:
        cands = [v for v in obj.values() if isinstance(v, dict)]
        if task and task in obj and isinstance(obj[task], dict):
            return obj[task]
    for c in cands:
        if not task or c.get("task_id") == task:
            return c
    return cands[0] if cands else None

# ------------------------------------------------------------------- metrics

def activity_metrics(pred, gold, pairs, ceil_ids):
    mg = {d["gold"] for d in pairs}
    mp = {d["pred"] for d in pairs}
    ng, npd = len(gold["activities"]), len(pred["activities"])
    rec = frac(len(mg), ng)
    prec = frac(len(mp), npd)
    pv, rv = prec["value"], rec["value"]
    f = round(2 * pv * rv / (pv + rv), 4) if pv and rv else 0.0
    vis = {a["id"] for a in gold["activities"] if a["visibility"] in VISIBLE}
    has_vis = any(a["visibility"] for a in gold["activities"])
    out = {"precision": prec, "recall_all": rec, "f1": f,
           "recall_visible": frac(len(mg & vis), len(vis)) if has_vis else
                             {"num": None, "den": None, "value": None,
                              "note": "gold has no visibility annotations"},
           "missed_gold": sorted({a["id"] for a in gold["activities"]} - mg),
           "missed_gold_staff_only": sorted(a["id"] for a in gold["activities"]
                                            if a["visibility"] == "staff_only"
                                            and a["id"] not in mg)}
    if ceil_ids is None:
        out["recall_ceiling"] = {"num": None, "den": None, "value": None,
                                 "note": "no ceiling supplied"}
    else:
        out["recall_ceiling"] = frac(len(mg & ceil_ids), len(ceil_ids),
                                     missed=sorted(ceil_ids - mg))
    return out

def actor_accuracy(pairs):
    hit = sum(1 for d in pairs if d["actor_match"])
    return frac(hit, len(pairs),
                compatible=sum(1 for d in pairs if d["actor_compat"] >= 0.35),
                wrong=[[d["pred"], d["pred_actor"], d["gold"], d["gold_actor"]]
                       for d in pairs if not d["actor_match"]][:25])

def order_agreement(pred, gold, pairs):
    """Fraction of gold precedence pairs (i,j) — transitive closure of
    sequence/handoff-like edges, rework ignored — whose predicted
    representatives appear in the same order. Gold pairs that collapse onto a
    single predicted activity are reported as `conflated`, not as failures."""
    rep = {}
    for d in sorted(pairs, key=lambda d: -d["score"]):
        rep.setdefault(d["gold"], d["pred"])
    gc = closure(gold["activities"], gold["edges"])
    pc = closure(pred["activities"], pred["edges"])
    pidx = {a["id"]: a["idx"] for a in pred["activities"]}
    num = den = conflated = 0
    bad = []
    for u, v in sorted(gc):
        if u not in rep or v not in rep:
            continue
        p, q = rep[u], rep[v]
        if p == q:
            conflated += 1
            continue
        den += 1
        if (p, q) in pc:
            num += 1
        elif (q, p) in pc:
            bad.append([u, v, p, q, "reversed"])
        elif pidx.get(p, 0) < pidx.get(q, 0):   # no path either way: fall back to list order
            num += 1
        else:
            bad.append([u, v, p, q, "reversed_by_list_order"])
    return frac(num, den, conflated=conflated, violations=bad[:25])

def rework_metrics(pred, gold, pairs):
    a2g, a2p = {}, {}
    for d in pairs:
        a2g.setdefault(d["gold"], set()).add(d["pred"])
        a2p.setdefault(d["pred"], set()).add(d["gold"])
    gold_rw = {(e["from"], e["to"]) for e in gold["edges"] if e["kind"] == "rework"}
    pred_rw = {(e["from"], e["to"]) for e in pred["edges"] if e["kind"] == "rework"}
    hit_g = {(u, v) for u, v in gold_rw
             if any((p, q) in pred_rw for p in a2g.get(u, ()) for q in a2g.get(v, ()))}
    hit_p = {(p, q) for p, q in pred_rw
             if any((u, v) in gold_rw for u in a2p.get(p, ()) for v in a2p.get(q, ()))}
    return {"recall": frac(len(hit_g), len(gold_rw), missed=sorted(gold_rw - hit_g)),
            "precision": frac(len(hit_p), len(pred_rw), spurious=sorted(pred_rw - hit_p)),
            "n_gold_rework_edges": len(gold_rw), "n_pred_rework_edges": len(pred_rw)}

def fee_metrics(pred, gold, pairs):
    per, abs_e, rel_e = [], [], []
    for d in pairs:
        p, g = pred["by_id"][d["pred"]], gold["by_id"][d["gold"]]
        if p["fee"] is None or g["fee"] is None:
            continue
        ae = abs(p["fee"] - g["fee"])
        abs_e.append(ae)
        rel_e.append(ae / g["fee"] if g["fee"] else (0.0 if ae == 0 else 1.0))
        per.append({"pred": d["pred"], "gold": d["gold"], "pred_fee": p["fee"],
                    "gold_fee": g["fee"], "abs_err": round(ae, 2), "rel_err": round(rel_e[-1], 4)})
    gp = sum(a["fee"] for a in pred["activities"] if a["fee"])
    gg = sum(a["fee"] for a in gold["activities"] if a["fee"])
    return {"n_compared": len(abs_e), "mean_abs_err": mean(abs_e), "mean_rel_err": mean(rel_e),
            "exact_matches": frac(sum(1 for x in abs_e if x == 0), len(abs_e)),
            "total_fee_pred": gp, "total_fee_gold": gg,
            "total_fee_rel_err": round(abs(gp - gg) / gg, 4) if gg else None,
            "gold_fees_unmatched": [a["id"] for a in gold["activities"]
                                    if a["fee"] and a["id"] not in {d["gold"] for d in pairs}],
            "per_activity": per}

def _find_median(obj):
    """Read an explicit process summary, never an arbitrary nested task or fee.

    Legacy event logs use elapsed_days.median. Unknown nested containers are
    deliberately not searched: JSON key ordering must not select the estimand.
    """
    if isinstance(obj, bool):
        return None
    if isinstance(obj, (int, float)):
        return float(obj) if math.isfinite(obj) and obj >= 0 else None
    if isinstance(obj, dict):
        if str(obj.get("kind", "")).strip().lower() in {"statutory_cap", "target", "deadline"}:
            return None
        for k in ("true_median_days", "median_days", "end_to_end_median_days", "median",
                  "p50_days", "best_estimate_from_posts"):
            if k in obj:
                v = _find_median(obj[k])
                if v is not None:
                    return v
        for key in ("elapsed_days", "process_timing", "end_to_end", "log_summary", "summary"):
            value = obj.get(key)
            got = _find_median(value) if isinstance(value, dict) else None
            if got is not None:
                return got
    return None

def timing_metrics(pred, gold, pairs, ceiling=None, log_summary=None):
    per, errs = [], []
    for d in pairs:
        p, g = pred["by_id"][d["pred"]], gold["by_id"][d["gold"]]
        if not p["median_days"] or not g["median_days"]:
            continue
        e = abs(math.log(p["median_days"] / g["median_days"]))
        errs.append(e)
        per.append({"pred": d["pred"], "gold": d["gold"], "pred_median_days": p["median_days"],
                    "gold_median_days": g["median_days"], "log_ratio_abs": round(e, 4)})
    obs = _find_median(log_summary) if log_summary else None
    pe = pred["end_to_end"]
    ge = gold["end_to_end"]
    if ge is None:
        ge = _find_median((ceiling or {}).get("timing_ceiling"))
    if ge is None:
        ge = obs
    out = {"n_compared": len(errs), "mean_abs_log_ratio": mean(errs),
           "within_2x": frac(sum(1 for e in errs if e <= math.log(2)), len(errs)),
           "end_to_end": {"pred_median_days": pe, "gold_median_days": ge,
                          "abs_log_ratio": round(abs(math.log(pe / ge)), 4) if pe and ge else None,
                          "note": "Explicit process estimates only; sums of step medians are not process medians."},
           "per_activity": per}
    if obs:
        out["vs_log_summary"] = {"observed_median_days": obs,
                                 "abs_log_ratio": round(abs(math.log(pe / obs)), 4) if pe else None,
                                 "gold_vs_observed_abs_log_ratio":
                                     round(abs(math.log(ge / obs)), 4) if ge else None}
    return out

def disentanglement(pred, gold, pairs, distractors, margin=0.05):
    """A predicted activity that aligns better to a distractor process than to
    gold = evidence from another process/jurisdiction leaked in (error source #4)."""
    if not distractors:
        return {"n_distractor_models": 0, "failures": frac(0, len(pred["activities"]),
                note="no distractors supplied"), "detail": []}
    matched = {d["pred"] for d in pairs}
    fails, detail = 0, []
    for p in pred["activities"]:
        bg = max((sim(p, g)[0] for g in gold["activities"]), default=0.0)
        bd, who = 0.0, None
        for dm in distractors:
            for g in dm["activities"]:
                s = sim(p, g)[0]
                if s > bd:
                    bd, who = s, f"{dm['model_id']}:{g['id']}"
        if bd >= T_DISTRACTOR and bd > bg + margin:
            fails += 1
            detail.append({"pred": p["id"], "pred_name": p["name"][:90],
                           "best_distractor": who, "distractor_score": bd,
                           "best_gold_score": bg, "was_matched_to_gold": p["id"] in matched})
    return {"n_distractor_models": len(distractors),
            "failures": frac(fails, len(pred["activities"])),
            "among_unmatched": sum(1 for d in detail if not d["was_matched_to_gold"]),
            "among_matched": sum(1 for d in detail if d["was_matched_to_gold"]),
            "detail": detail[:25]}

# ----------------------------------------------------------------- staleness

def _stale_values(gold):
    """Prior-version facts: dollar amounts, free text, and 'no <thing>' phrases."""
    pv = gold["prior_version"] or {}
    texts = []
    if isinstance(pv, dict):
        texts += [str(x) for x in (pv.get("changes") or [])]
        for k, v in (pv.get("choices") or {}).items():
            texts.append(f"{k}: {v}")
        for k in ("fee", "fees", "actor", "department", "note"):
            if pv.get(k) is not None:
                texts.append(f"{k}: {pv[k]}")
    elif isinstance(pv, list):
        texts += [str(x) for x in pv]
    fees = set()
    for t in texts:
        for m in re.finditer(r"\$\s?([\d,]+(?:\.\d+)?)", t):
            fees.add(float(m.group(1).replace(",", "")))
    removed = [re.sub(r"^no\s+", "", t.lower()) for t in texts if re.match(r"(?i)^no\s+\S", t)]
    return {"texts": texts, "fees": fees, "removed": removed}

def staleness(pred, gold, pairs):
    sv = _stale_values(gold)
    cur_fees = {a["fee"] for a in gold["activities"] if a["fee"]}
    matched_gold = {d["gold"] for d in pairs}
    fee_hits, actor_hits, elem_hits = [], [], []
    for p in pred["activities"]:
        if p["fee"] is not None and p["fee"] in sv["fees"] and p["fee"] not in cur_fees:
            fee_hits.append({"pred": p["id"], "fee": p["fee"],
                             "prior_version_fee": p["fee"], "current_fees": sorted(cur_fees)})
    for d in pairs:
        p, g = pred["by_id"][d["pred"]], gold["by_id"][d["gold"]]
        if p["actor"] == g["actor"] or p["actor"] == "unknown":
            continue
        # the predicted lane is wrong AND it is the lane the prior version named
        for t in sv["texts"]:
            if any(canon_actor(w) == p["actor"] for w in re.findall(r"[A-Za-z_]{3,}", t)):
                actor_hits.append({"pred": p["id"], "gold": g["id"], "pred_actor": p["actor"],
                                   "gold_actor": g["actor"], "prior_version_text": t})
                break
    for phrase in sv["removed"]:                # "no pre-application meeting" -> pred lacks it
        pt = toks(phrase)
        for g in gold["activities"]:
            if g["id"] in matched_gold:
                continue
            if max(f1(pt, g["toks"]), f1(pt, g["toks_local"])) >= 0.5:
                elem_hits.append({"gold": g["id"], "gold_name": g["name"][:80],
                                  "prior_version_text": f"no {phrase}"})
    n = len(pred["activities"])
    return {"prior_version_present": bool(sv["texts"]),
            "stale_fee": frac(len(fee_hits), n, detail=fee_hits[:10]),
            "stale_actor": frac(len(actor_hits), len(pairs) or 0, detail=actor_hits[:10]),
            "stale_missing_added_element": frac(len(elem_hits),
                                               len(sv["removed"]), detail=elem_hits[:10]),
            "total_stale_facts": len(fee_hits) + len(actor_hits) + len(elem_hits)}

# --------------------------------------------------- statute element coverage

def element_coverage(pred, gold, statute, pairs):
    """Mandated-element coverage vs the statute skeleton. Works with a
    `statute_truth` (has `skeleton`) or a statute-sourced process model (reuses
    pipeline.process_model.coverage)."""
    matched_gold = {d["gold"] for d in pairs}
    sk = statute.get("skeleton")
    if sk:
        mand = [{"element_id": e.get("element_id"), "name": e.get("name"),
                 "optional": bool(e.get("optional"))} for e in sk]
        req = [e for e in mand if not e["optional"]]
        covered = []
        for e in req:
            gs = [a for a in gold["activities"] if str(a["element_ref"]) == str(e["element_id"])]
            if gs and any(a["id"] in matched_gold for a in gs):
                covered.append(e["element_id"])
            elif not gs:                 # not in the truth graph: fall back to name match
                pt = toks(e["name"])
                if any(max(f1(pt, p["toks"]), f1(pt, p["toks_local"])) >= 0.5
                       for p in pred["activities"]):
                    covered.append(e["element_id"])
        return {"mode": "statute_truth.skeleton", "mandated": [e["element_id"] for e in req],
                "covered": covered, "missing": [e["element_id"] for e in req
                                                if e["element_id"] not in covered],
                "coverage": frac(len(covered), len(req))}
    import process_model                                     # statute-sourced process model
    cov = process_model.coverage(pred["raw"], statute)
    return {"mode": "process_model.coverage", **cov,
            "coverage_frac": frac(len(cov["present"]), len(cov["mandated"]))}

def confidence_evidence(pred, pairs):
    matched = {d["pred"] for d in pairs}
    cm = [a["confidence"] for a in pred["activities"]
          if a["confidence"] is not None and a["id"] in matched]
    cu = [a["confidence"] for a in pred["activities"]
          if a["confidence"] is not None and a["id"] not in matched]
    return {"mean_confidence_matched": mean(cm), "mean_confidence_unmatched": mean(cu),
            "confidence_gap": round(mean(cm) - mean(cu), 4) if cm and cu else None,
            "with_evidence": frac(sum(1 for a in pred["activities"] if a["evidence"]),
                                  len(pred["activities"]))}

def actor_selection(pred, gold, pairs, universe=None):
    """Actor attribution scored as selection from a known universe of institutions.

    Without a universe the model draws a department from an unbounded space, so plain accuracy has no
    baseline. Given the jurisdiction's actual list of departments (its published directory), three
    separable quantities become reportable:
      in_universe  — does the predicted actor name an institution that exists here at all?
                     (a miss is an invented institution, a different error from misattribution)
      correct      — of matched pairs, is it the right one?
      lift         — (correct - chance) / (1 - chance), chance = 1/K over the universe
    """
    from_gold = sorted({a["actor"] for a in gold["activities"] if a.get("actor")})
    uni = sorted({str(u).strip().lower().replace(" ", "_") for u in (universe or from_gold) if u})
    k = len(uni)
    canon = lambda s: str(s or "").strip().lower().replace(" ", "_")
    pa = [a for a in pred["activities"] if a.get("actor")]
    in_uni = [a for a in pa if canon(a["actor"]) in uni]
    seen, correct, total = set(), 0, 0
    for d in pairs:
        key = (d["pred"], d["gold"])
        if key in seen:
            continue
        seen.add(key)
        p, g = pred["by_id"].get(d["pred"]), gold["by_id"].get(d["gold"])
        if not p or not g or not p.get("actor") or not g.get("actor"):
            continue
        total += 1
        if canon(p["actor"]) == canon(g["actor"]) or p.get("actor") == g.get("actor"):
            correct += 1
    chance = (1.0 / k) if k else None
    acc = (correct / total) if total else None
    lift = None
    if acc is not None and chance is not None and chance < 1:
        lift = round((acc - chance) / (1 - chance), 4)
    return {"universe_size": k, "universe_source": "supplied" if universe else "gold actors",
            "in_universe": frac(len(in_uni), len(pa),
                                invented=[a.get("actor") for a in pa if canon(a["actor"]) not in uni][:12]),
            "correct": frac(correct, total), "chance": (round(chance, 4) if chance else None),
            "lift_over_chance": lift}
