"""Elicit informative priors from a tool-less LLM WITHOUT the evidence (round 2 hybrid).

  python -m pipeline.procbench.toy_statute.prior_elicit --out runs/toy_statute_20260926/llm_prior001 --repeats 3

The LLM sees only public knowledge: statute, decision model, p-step catalog,
structure menu and the modelling assumptions. No evidence, so the data are
not used twice. Output prior.json: {"prior_overrides": {...}, "struct_prior": {...}}
consumed by Model(prior_overrides=..., struct_prior=...).

Conversion (declared in docs/2026-09-26-toy-statute-round2-plan.md):
- step-duration medians and applicant-hour medians: log-scale normal centred
  at the geometric mean of the repeats' "typical" values; sd from the mean
  repeat 90% log-width / (2*1.645), widened x1.5; mixed 80/20 with the
  original vague prior (robustness: the data can override a wrong LLM guess).
- structure prior: mean of repeats' probabilities, mixed 80/20 with uniform,
  identical for every town (the LLM has no town-specific information).
- spreads, town speed, incompleteness/objection probabilities, noise: unchanged vague priors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import spec
from .llm_baseline import call_claude, extract_json
from .model import prior_spec

WIDEN = 1.5
W_LLM = 0.8


def build_prompt():
    dm = "\n".join(f"- {d['id']} {d['name']} ({d['clause']}): {d['tag']}. {d['note']}" for d in spec.D_STEPS)
    ps = "\n".join(f"- {k}: serves {','.join(v['d_steps'])}; actor {v['actor']}" for k, v in spec.P_STEPS.items())
    st = "\n".join(f"- {k}: {v}" for k, v in spec.STRUCTURE_TEXT.items())
    template = {
        "step_days": {s: {"typical": None, "low90": None, "high90": None} for s in spec.DAY_STEPS},
        "applicant_hours": {s: {"typical": None, "low90": None, "high90": None} for s in spec.HOUR_STEPS},
        "structure_probs": {S: None for S in spec.STRUCTURE_IDS},
    }
    return f"""You are helping set PRIOR beliefs for a statistical model of a local permitting process, BEFORE any data from the towns are seen.
There is no evidence here and no tools. Use general knowledge of how local permitting authorities typically operate.

STATUTE:
{spec.STATUTE_TEXT}

DECISION MODEL (read from the statute):
{dm}

PROCESS STEPS:
{ps}
An incomplete application loops through correction (by the applicant) and a new completeness check.

CANDIDATE PROCESS STRUCTURES a town might use to implement Sec. 3:
{st}

Give, for a typical town:
- step_days: for each step, the typical (median) elapsed days ONE occurrence of that step takes for the applicant (for site_inspection: the wait from the prior step until the visit; for correction: time for the applicant to resubmit; for comment_period: its length), with a 90% range (low90, high90) across towns and cases.
- applicant_hours: hours of the applicant's own time per occurrence (prepare = preparing the application and site plan; correction; attending a site inspection; attending a hearing), with 90% ranges.
- structure_probs: the probability that a town implements Sec. 3 with each structure S1..S6 (sum to 1).
All numbers must be positive; low90 < typical < high90.
Return ONLY this JSON with every null replaced by a number:
{json.dumps(template)}
"""


def convert(answers):
    towns_dummy = ["_"]
    vague = prior_spec(towns_dummy)
    overrides = {}
    for group, pfx, keys in (("step_days", "mu_", spec.DAY_STEPS), ("applicant_hours", "muh_", spec.HOUR_STEPS)):
        for s in keys:
            typ = [a[group][s]["typical"] for a in answers]
            lo = [a[group][s]["low90"] for a in answers]
            hi = [a[group][s]["high90"] for a in answers]
            m = float(np.mean(np.log(typ)))
            w = float(np.mean([math.log(h) - math.log(l) for l, h in zip(lo, hi)]))
            sd = max(w / (2 * 1.645), 0.05) * WIDEN
            _, vm, vs = vague[f"{pfx}{s}"]
            overrides[f"{pfx}{s}"] = ("mixnormal", [(W_LLM, m, sd), (1 - W_LLM, vm, vs)], None)
    sp = np.mean([[a["structure_probs"][S] for S in spec.STRUCTURE_IDS] for a in answers], axis=0)
    sp = sp / sp.sum()
    sp = W_LLM * sp + (1 - W_LLM) / len(sp)
    return overrides, {S: float(v) for S, v in zip(spec.STRUCTURE_IDS, sp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--towns", nargs="+", default=["Alder", "Birch", "Cedar"])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt()
    (out / "prompt.txt").write_text(prompt)

    def one(i):
        rc, so, se = call_claude(prompt, a.model)
        (out / f"raw_{i}.json").write_text(so)
        res = json.loads(so)
        ans = extract_json(res["result"])
        (out / f"answers_{i}.json").write_text(json.dumps(ans, indent=1))
        return ans, res.get("total_cost_usd")

    with ThreadPoolExecutor(max_workers=a.repeats) as ex:
        res = list(ex.map(one, range(a.repeats)))
    answers = [r[0] for r in res]
    overrides, sp = convert(answers)
    prior = {"prior_overrides": overrides, "struct_prior": {t: sp for t in a.towns},
             "meta": {"model": a.model, "repeats": a.repeats, "widen": WIDEN, "w_llm": W_LLM,
                      "cost_usd": [r[1] for r in res],
                      "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}}
    (out / "prior.json").write_text(json.dumps(prior, indent=1))
    print(json.dumps({k: (v[1][0] if v[0] == "mixnormal" else v) for k, v in overrides.items()}, indent=1))
    print(json.dumps(sp, indent=1))


if __name__ == "__main__":
    main()
