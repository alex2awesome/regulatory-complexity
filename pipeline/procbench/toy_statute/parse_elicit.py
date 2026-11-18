"""Layer 1 elicitation: K independent tool-less LLM parses of the statute, no evidence.

Each parse returns (a) the decision-model skeleton as elements with confidences,
(b) free-form ambiguities classified with the Massey et al. (2014) taxonomy, and
(c) P(yes) for the pre-registered questions Q1-Q5. Aggregation:
  - element reliability = share of parses that include the element (correlated votes,
    reported as such, not as independent evidence);
  - question prior from direct probabilities (mean across parses) and from parse
    frequency (share of parses answering yes), kept as two separate sources;
  - free-form ambiguities that map to no pre-registered question feed the residual.

  python -m pipeline.procbench.toy_statute.parse_elicit --out runs/.../W4/parse_elicit001 --k 6 --model opus
"""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import spec, validity
from .llm_baseline import call_claude, extract_json

TAXONOMY = ["lexical", "syntactic", "semantic", "vagueness", "incompleteness", "referential"]

SKELETON_ELEMENTS = {
    "E1_application_with_site_plan_required": "An application with a site plan (coop location, distance to property lines) must be submitted.",
    "E2_completeness_check_implied": "The authority assesses whether an application is complete (implied by 'complete application').",
    "E3_nuisance_determination_required_before_issuance": "Before issuing, the authority must determine the coop will not create a nuisance to adjoining properties.",
    "E4_decision_within_30_days_of_complete_application": "Issue or deny within 30 days after receiving a complete application.",
    "E5_fee_authorized": "The authority may charge a reasonable application fee.",
    "E6_scope_single_family_six_hens": "Only residents of single-family dwellings, up to six hens, are eligible.",
    "E7_denial_grounds_limited": "Denial may rest only on ineligibility, incompleteness or the nuisance determination.",
}


def build_prompt():
    qs = "\n".join(f"- {k}: {v}" for k, v in validity.QUESTIONS.items())
    els = "\n".join(f"- {k}: {v}" for k, v in SKELETON_ELEMENTS.items())
    tmpl = {
        "elements": {k: {"present": None, "confidence": None} for k in SKELETON_ELEMENTS},
        "additional_elements": [{"text": "...", "clause": "...", "confidence": 0.0}],
        "ambiguities": [{"clause": "Sec. N", "phrase": "...", "type": "one of " + "/".join(TAXONOMY),
                         "question": "...", "answers": [{"answer": "...", "probability": 0.0}],
                         "maps_to_question": "Q id or 'none'"}],
        "question_p_yes": {k: None for k in validity.QUESTIONS},
    }
    return f"""You are a careful legal reader. Read the statute below and produce a structured parse. Do not assume any facts beyond the text. Output JSON only.

STATUTE:
{spec.STATUTE_TEXT}

TASK 1. For each candidate element of the decision model below, say whether the text requires it (present: true/false) and your confidence (0-1) in that judgement. List any additional required elements you find that are not in the list.
{els}

TASK 2. List every ambiguity or vagueness in the text. For each, give the clause, the phrase, its type using this taxonomy: lexical (a word with multiple meanings), syntactic (grammatical structure), semantic (meaning of the sentence as a whole), vagueness (a gradable or threshold term without a cutoff), incompleteness (a needed detail is missing), referential (unclear what a term refers to). State the interpretive question it raises, the plausible answers with probabilities that a court or agency would adopt each (sum to 1), and which of the pre-registered questions below it maps to, or 'none'.

TASK 3. For each pre-registered question, give the probability that the answer is YES, as a probability that a competent agency reading this text would act on the YES answer:
{qs}

OUTPUT: only this JSON, filled in (arrays may have any length):
{json.dumps(tmpl)}
"""


def run(out, k, model):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt()
    (out / "prompt.txt").write_text(prompt)

    def one(i):
        rc, so, se = call_claude(prompt, model)
        (out / f"raw_{i}.json").write_text(so)
        try:
            res = json.loads(so)
            ans = extract_json(res["result"])
            (out / f"parse_{i}.json").write_text(json.dumps(ans, indent=1))
            return {"i": i, "ok": True, "cost_usd": res.get("total_cost_usd")}
        except Exception as e:
            return {"i": i, "ok": False, "error": repr(e)[:300]}

    with ThreadPoolExecutor(max_workers=k) as ex:
        recs = list(ex.map(one, range(k)))
    parses = [json.loads((out / f"parse_{r['i']}.json").read_text()) for r in recs if r["ok"]]
    agg = aggregate(parses)
    agg["runs"] = recs
    agg["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
    (out / "aggregate.json").write_text(json.dumps(agg, indent=1))
    return agg


def aggregate(parses):
    K = len(parses)
    el = {}
    for e in SKELETON_ELEMENTS:
        pres = [bool(p.get("elements", {}).get(e, {}).get("present")) for p in parses]
        conf = [p.get("elements", {}).get(e, {}).get("confidence") for p in parses]
        conf = [float(c) for c in conf if c is not None]
        el[e] = {"share_present": float(np.mean(pres)) if pres else None,
                 "mean_confidence": float(np.mean(conf)) if conf else None, "k": K}
    direct = {q: [] for q in validity.QUESTIONS}
    for p in parses:
        for q, v in (p.get("question_p_yes") or {}).items():
            if q in direct and v is not None:
                direct[q].append(float(v))
    direct_mean = {q: float(np.mean(v)) if v else None for q, v in direct.items()}
    freq_yes = {q: float(np.mean([x > 0.5 for x in v])) if v else None for q, v in direct.items()}
    amb, unmapped = [], []
    for i, p in enumerate(parses):
        for a in p.get("ambiguities", []) or []:
            a = dict(a, parse=i)
            amb.append(a)
            if str(a.get("maps_to_question", "none")).lower() in ("none", "", "null"):
                unmapped.append(a)
    types = {}
    for a in amb:
        types[str(a.get("type"))] = types.get(str(a.get("type")), 0) + 1
    extra = [dict(e, parse=i) for i, p in enumerate(parses) for e in (p.get("additional_elements") or [])]
    return {"k": K, "elements": el, "question_p_yes_direct_mean": direct_mean,
            "question_p_yes_parse_frequency": freq_yes,
            "ambiguities_total": len(amb), "ambiguities_per_parse": len(amb) / max(K, 1),
            "ambiguity_types": types, "unmapped_ambiguities": unmapped,
            "unmapped_share": len(unmapped) / max(len(amb), 1), "additional_elements": extra}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--model", default="opus")
    a = ap.parse_args()
    agg = run(a.out, a.k, a.model)
    print(json.dumps({k: v for k, v in agg.items() if k not in ("unmapped_ambiguities", "additional_elements")}, indent=1))


if __name__ == "__main__":
    main()
