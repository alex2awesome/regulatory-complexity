"""LLM baseline: a tool-less Claude call answers the same estimands from the same evidence.

  python -m pipeline.procbench.toy_statute.llm_baseline --evidence runs/.../W0/evidence \
      --out runs/.../W0/llm_baseline001 --repeats 3 --model opus

Runs `claude -p --tools ""` from an empty working directory, so the model can
read nothing but the prompt. Never imports truth_world.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import estimands, spec, validity

DEFINITIONS = """ESTIMAND DEFINITIONS (all "per case" quantities are expectations for a new application in that town).
Continuous estimands: give [q05, q50, q95] = the 5th, 50th and 95th percentiles of YOUR uncertainty about the true value.
- pstep_days.<step>: expected elapsed days per case spent in that p-step, summing repeats (completeness checks repeat after each correction). 0 if the step never occurs in that town. Hearing is occurrence-weighted (it only happens after an objection).
- pstep_hours.<step>: expected applicant hours per case: prepare; correction (summing repeats); site_inspection (attending); hearing (attending, occurrence-weighted).
- pstep_dollars.<step>: expected dollars per case: prepare = application fee; neighbor_notice = notice fee; site_inspection = inspection fee. 0 if the step does not exist in that town.
- dstep_{days,hours,dollars}.D1/D2/D3: roll-up of p-steps to decision steps. D1 = completeness_check + correction (hours: prepare + correction; dollars: application fee). D2 = neighbor_notice + comment_period + desk_review + hearing + site_inspection. D3 = decision_issue. If the decision is issued at the inspection (S3/S6), the inspection's days, hours and dollars count IN FULL toward BOTH D2 and D3.
- total.days_mean: mean days from submission to decision. total.days_q10/q50/q90: 10th/50th/90th percentile of the total-days distribution across cases. total.hours_mean, total.dollars_mean: per case.
- deadline.p_miss: probability that days from complete application (the final successful completeness check) to decision exceed 30.
- complexity.expected_psteps: expected number of p-step executions per case, counting prepare (1), every completeness check, every correction, each D2 step executed (hearing only when it happens), and decision_issue if it is a separate step.
- complexity.applicant_interactions: expected applicant-facing executions per case: prepare + corrections + site inspection (if it exists) + hearing (if it happens).
- complexity.path_entropy_bits: Shannon entropy in bits of the distribution over case paths, a path being (number of correction loops 0-4, hearing yes/no).
- complexity.cv_total_days: standard deviation / mean of total days.
- counterfactual.delta_{days,hours,dollars}_mean: (counterfactual minus current) mean total days / hours / dollars per case if Sec. 3 were rewritten as "the authority shall review the site plan", so every town uses S1 (desk review, separate decision issuance), each town keeping its own agency speed and incompleteness rate; dollars then = application fee only.
- statute.d2_implementation_entropy_bits: entropy in bits of the distribution of D2 refinements across the three towns; refinements are R1 (S1), R2 (S2 or S3), R3 (S4), R4 (S5 or S6).
- statute.d2_days_between_town_sd: population standard deviation across the three towns of mean D2 days.
- statute.cf_mean_delta_days: mean across towns of counterfactual.delta_days_mean.
- statute.cf_delta_between_town_sd_days: (population SD across towns of counterfactual mean total days) minus (population SD across towns of current mean total days).
- structure_probs.<town>.S1..S6: your probability that the town's process is each candidate structure (sum to 1).
- predictive_total_days.<town>: quantiles (0.05..0.95) of total days for ONE new case in that town, including your uncertainty.
"""


EXT_TOWN_KEYS = ["ext.deadline_coverage", "ext.p_miss_if_clock_from_submission", "ext.serialisation_excess_days",
                 "ext.cf_consolidated_notice_delta_days", "ext.days_per_correction_loop",
                 "ext.exposure_p_discretionary_encounter"]
EXT_STATUTE_KEYS = ["ext.statute_realised_structure_variety_bits"]
EXT_DEFINITIONS = """EXTENDED ESTIMAND DEFINITIONS (per town unless noted; give [q05, q50, q95] of your uncertainty):
- ext.deadline_coverage: E[days from complete application to decision] / E[days from first submission to decision].
- ext.p_miss_if_clock_from_submission: probability a new case takes more than 30 days from FIRST submission to decision.
- ext.serialisation_excess_days: mean total days now, minus mean total days if the town ran the D2 steps concurrently where the statute allows: after D1, the desk review, the neighbour notice->comment period->(hearing if objection) chain, and the site inspection proceed in parallel, and the decision follows the last of them (issued at the inspection if the town does that).
- ext.cf_consolidated_notice_delta_days: change in mean total days if the authority had to cite all deficiencies at once, so an incomplete application needs at most one correction round (probability of a round unchanged).
- ext.days_per_correction_loop: mean days one correction loop adds (applicant correction + a new completeness check).
- ext.exposure_p_discretionary_encounter: probability a case involves an in-person encounter with an official who has discretion (a site inspection or a hearing).
- ext.statute_realised_structure_variety_bits (statute level): entropy in bits of the distribution of the six structure labels (S1..S6) across the three towns.
"""


OUTCOME_DEFINITIONS = """OUTCOME ESTIMAND DEFINITIONS (give [q05, q50, q95] of your uncertainty about each true value).
"Would-be keeper": a household in the town that wants to keep hens during the study period (whether or not it applies).
Safeguards: desk review (desk), site inspection (insp), neighbour comment period (nb). Any flag by any safeguard present in a town's process means denial.
- out.d_desk / out.d_insp / out.d_nb: probability that the safeguard flags a coop that truly is a nuisance.
- out.f_desk / out.f_insp / out.f_nb: probability that the safeguard flags a coop that is NOT a nuisance.
- out.u: probability that a would-be keeper who does not apply, or is denied, keeps hens anyway.
- out.beta: deterrence slope: P(apply) = expit(alpha - beta * (burden_index - 60)) for some alpha.
- <town>.out.pi: share of that town's would-be keepers whose coop is a nuisance.
- <town>.out.p_detect: P(denied | nuisance, applied) under the town's current process.
- <town>.out.p_wrongful_denial: P(denied | not a nuisance, applied).
- <town>.out.nuisance_share_permitted: share of permitted coops that are nuisances.
- <town>.out.p_apply: probability that a would-be keeper applies.
- <town>.out.operating_nuisance_per100: nuisance coops operating (permitted or not) per 100 would-be keepers.
- <town>.out.wrongful_denials_per100: harmless coops denied per 100 would-be keepers.
- <town>.out.unpermitted_per100: households keeping hens without a permit per 100 would-be keepers.
- <town>.out.burden_index: expected applicant burden in day-equivalents = mean total days + 4 x mean applicant hours + (mean dollars)/5, per case.
- <town>.cf.<S>.{p_apply, operating_nuisance_per100, wrongful_denials_per100, burden_index}: the same quantities if the town used structure S instead (S1..S6), keeping its own agency speed, incompleteness and objection rates, its would-be keepers and nuisance share, and its current fee amounts for fee items whose step the structure contains (no fee for steps it does not currently charge for). Applicants respond to the new burden.
"""


READINGS_DEFINITIONS = """READING ESTIMANDS. A *reading* of the statute is one answer to each interpretive question below. Each town's agency acts on some reading when it designs its permit process. From the evidence, infer for EACH TOWN:
- reading_p_yes.<town>.<Q>: the probability that the town's agency acts on the YES answer to that question (a number in [0,1]).
- design_probs.<town>.<S>: the probability that the town uses each candidate design S1..S11 (sum to 1 per town).
Questions:
{qs}
Notes: a design is legally valid under a reading only if it collects evidence the reading accepts (desk review of the site plan counts only if the reading says a desk review suffices; a neighbour comment period or hearing supplies neighbour input; an inspection supplies site evidence), determines nuisance before issuing, and imposes only burdens the reading authorizes (attending an inspection needs the investigative-power answer; separate notice/inspection fees need the separate-fees answer). Agencies mostly, but not always, use designs valid under their own reading; they may also prefer cheaper or legally safer designs. Report what the evidence supports; where the evidence says nothing about a question, stay near your prior for that question.
"""


QUESTIONS_OVERRIDE = None  # {qid: text}; set from --questions-json (round 5: the blind reader's questions)


def _questions():
    return QUESTIONS_OVERRIDE or validity.QUESTIONS


def readings_template(towns):
    return {"reading_p_yes": {t: {q: None for q in _questions()} for t in towns},
            "design_probs": {t: {S: None for S in spec.STRUCTURE_IDS} for t in towns}}


def outcome_template(towns):
    from . import outcomes
    return {"estimands": {k: [None, None, None] for k in outcomes.estimand_keys(towns)}}


def ext_template(towns):
    e = {f"{t}.{k}": [None, None, None] for t in towns for k in EXT_TOWN_KEYS}
    e.update({k: [None, None, None] for k in EXT_STATUTE_KEYS})
    return {"estimands": e}


def template(towns):
    return {
        "structure_probs": {t: {S: None for S in spec.STRUCTURE_IDS} for t in towns},
        "estimands": {k: [None, None, None] for k in estimands.estimand_keys(towns)},
        "predictive_total_days": {t: {str(q): None for q in estimands.PRED_QUANTILES} for t in towns},
    }


def build_prompt(ev_dir, extended=False, outcomes=False, readings=False):
    """ev_dir is either structured evidence/ (reports.json, webpages.json) or
    text_evidence/ (posts.json, webpages_text.json): raw forum posts and page text."""
    ev_dir = Path(ev_dir)
    pub = json.loads((ev_dir / "public_spec.json").read_text())
    from .model import CONTAM, LEGACY_REPORTING
    observation_settings = {
        "posting_day_range": pub.get("posting", {}).get("post_day_range", [10, 150]),
        "timing_selection_given_mentions": {**LEGACY_REPORTING, **pub.get("reporting", {})},
        "legacy_reporting_assumptions": [k for k in LEGACY_REPORTING if k not in pub.get("reporting", {})],
        "numeric_contamination_probability": CONTAM,
        "admin_milestone_logs": "exact timestamps and event labels; no contamination",
        "step_support": "individual steps are truncated at 511 days or 127.75 hours; summed totals are NOT capped",
        "fee_policy": pub.get("fee_policy", "legacy generation policy not recorded"),
    }
    towns = pub["towns"]
    if (ev_dir / "posts.json").exists():
        evidence = {
            "admin_records": json.loads((ev_dir / "admin_records.json").read_text()),
            "applicant_forum_posts": json.loads((ev_dir / "posts.json").read_text()),
            "agency_webpage_text": json.loads((ev_dir / "webpages_text.json").read_text()),
        }
    else:
        evidence = {
            "admin_records": json.loads((ev_dir / "admin_records.json").read_text()),
            "applicant_reports": json.loads((ev_dir / "reports.json").read_text()),
            "agency_webpages": json.loads((ev_dir / "webpages.json").read_text()),
        }
    if outcomes:
        evidence["outcome_evidence"] = json.loads((ev_dir / "outcomes.json").read_text())
    dm = "\n".join(f"- {d['id']} {d['name']} ({d['clause']}): {d['tag']}. {d['note']}" for d in spec.D_STEPS)
    ps = "\n".join(f"- {k}: serves {','.join(v['d_steps'])}; actor {v['actor']}; "
                   f"elapsed days: {v['days']}; applicant hours: {v['hours']}; fee item: {v['fee']}"
                   for k, v in spec.P_STEPS.items())
    st = "\n".join(f"- {k}: {v}" for k, v in spec.STRUCTURE_TEXT.items())
    return f"""You are estimating the burden and complexity that a statute imposes, for statute drafters.
Answer from the material below only. There are no tools; reason it through and output the final JSON.

STATUTE:
{spec.STATUTE_TEXT}

DECISION MODEL (read from the statute):
{dm}

PROCESS-STEP CATALOG (p-steps; which decision step each serves):
{ps}
D1 always consists of prepare -> completeness_check, and an incomplete application loops through correction -> completeness_check.

CANDIDATE PROCESS STRUCTURES for each town (exactly one is true per town):
{st}

ASSUMPTIONS:
{spec.PUBLIC_MODEL_NOTES}
PUBLIC OBSERVATION SETTINGS / DECLARED LEGACY ASSUMPTIONS (same as the Bayesian fitter):
{json.dumps(observation_settings)}
Towns: {", ".join(towns)}.

EVIDENCE (JSON):
{json.dumps(evidence)}

{READINGS_DEFINITIONS.format(qs=chr(10).join(f"- {k}: {v}" for k, v in _questions().items())) if readings else OUTCOME_DEFINITIONS if outcomes else EXT_DEFINITIONS if extended else DEFINITIONS}
OUTPUT: return ONLY a JSON object with exactly this structure, every null replaced by a number (no nulls, no extra keys, no prose):
{json.dumps(readings_template(towns) if readings else outcome_template(towns) if outcomes else ext_template(towns) if extended else template(towns))}
"""


def extract_json(text):
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    else:
        i, j = t.find("{"), t.rfind("}")
        t = t[i:j + 1]
    return json.loads(t)


def call_claude(prompt, model, timeout=3600):
    with tempfile.TemporaryDirectory() as empty:
        r = subprocess.run(["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence",
                            "--output-format", "json"], input=prompt, capture_output=True, text=True,
                           cwd=empty, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def run_one(args):
    prompt, model, out, i = args
    rc, so, se = call_claude(prompt, model)
    (out / f"raw_{i}.json").write_text(so)
    (out / f"stderr_{i}.txt").write_text(se)
    rec = {"repeat": i, "returncode": rc, "parse_ok": False, "retried": False}
    try:
        res = json.loads(so)
        rec["cost_usd"] = res.get("total_cost_usd")
        ans = extract_json(res["result"])
        rec["parse_ok"] = True
    except Exception as e:  # one retry for invalid JSON only, recorded
        rec["parse_error"] = repr(e)[:500]
        rec["retried"] = True
        rc, so, se = call_claude(prompt, model)
        (out / f"raw_{i}_retry.json").write_text(so)
        try:
            res = json.loads(so)
            ans = extract_json(res["result"])
            rec["parse_ok"] = True
        except Exception as e2:
            rec["retry_parse_error"] = repr(e2)[:500]
            return rec
    ans["method"] = f"llm_{model}_repeat{i}"
    (out / f"answers_{i}.json").write_text(json.dumps(ans, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--extended", action="store_true", help="ask the extended (survey) estimands instead")
    ap.add_argument("--outcomes", action="store_true", help="ask the outcome-layer estimands (evidence must include outcomes.json)")
    ap.add_argument("--readings", action="store_true", help="ask each town's reading (Q1-Q5) and design probabilities")
    ap.add_argument("--design-space", default="menu6", choices=["menu6", "full"])
    ap.add_argument("--package", default=None, help="statute package json; overrides --design-space")
    ap.add_argument("--questions-json", default=None, help="blind reader reading.json: use its major questions")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    global QUESTIONS_OVERRIDE
    if a.package:
        spec.load_package(json.loads(Path(a.package).read_text()))
    else:
        spec.use_design_space(a.design_space)
    if a.questions_json:
        rj = json.loads(Path(a.questions_json).read_text())
        QUESTIONS_OVERRIDE = {q["id"]: q["question"] for q in rj["questions"] if q.get("major")}
    prompt = build_prompt(a.evidence, extended=a.extended, outcomes=a.outcomes, readings=a.readings)
    (out / "prompt.txt").write_text(prompt)
    with ThreadPoolExecutor(max_workers=a.repeats) as ex:
        recs = list(ex.map(run_one, [(prompt, a.model, out, i) for i in range(a.repeats)]))
    manifest = {"model": a.model, "repeats": recs,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "evidence": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                             for f in sorted(Path(a.evidence).glob("*.json"))}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()


def average_dir(d):
    """Average repeats' answers (quantile-wise; probabilities averaged) into answers_avg{n}.json."""
    import numpy as np
    d = Path(d)
    A = [json.loads(f.read_text()) for f in sorted(d.glob("answers_[0-9].json"))]
    out = {"method": f"avg{len(A)}", "estimands": {}}
    if "structure_probs" in A[0]:
        out["structure_probs"] = {t: {S: float(np.mean([a["structure_probs"][t][S] for a in A]))
                                      for S in A[0]["structure_probs"][t]} for t in A[0]["structure_probs"]}
        out["predictive_total_days"] = {t: {q: float(np.mean([a["predictive_total_days"][t][q] for a in A
                                                             if a["predictive_total_days"][t].get(q) is not None]))
                                            for q in A[0]["predictive_total_days"][t]} for t in A[0]["predictive_total_days"]}
    for k in set().union(*[a["estimands"] for a in A]):
        vals = [a["estimands"].get(k) for a in A if a["estimands"].get(k) and None not in a["estimands"].get(k)]
        if vals:
            out["estimands"][k] = [float(np.mean([sorted(v)[i] for v in vals])) for i in range(3)]
    p = d / f"answers_avg{len(A)}.json"
    p.write_text(json.dumps(out, indent=1))
    return p
