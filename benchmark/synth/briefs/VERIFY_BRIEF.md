# Wave-3 brief: verifying rendered artifacts against their specs

You are the leakage/faithfulness checker. For each artifact you get: the spec, the rendered text, and — unlike the renderer — the descriptions of the `must_not_reveal` elements (from `truth/`, supplied to you in `verify_context/<id>.json`).

Write `benchmark/synth/worlds/<W>/artifacts/<id>.verify.json` per DESIGN.md `verify`:
- `required_found`: for every `reveals` entry, was it stated at the right fidelity? Quote the sentence. An `exact` fee written as "about $430" is a fidelity error (record `found: true, fidelity_ok: false`).
- `leaks`: any sentence that discloses a hidden element (a staff-only step, its actor, its timing) — quote it. Also flag *invented* process facts (a fee, step, department, or timeline not licensed by the spec) under `extraneous_facts`; those are leaks of a different kind (fabrication) and must be fixed too.
  **Fee-administration rules are the fifth category, and the line is quantification.** That enumeration of four left the most common unlicensed construct in this corpus unclassified, so verifiers resolved it by instinct and the same sentence passed in 132 fee schedules and failed in 3. The rule (decided 2026-09-18): a statement of general fee POLICY carrying no quantity is boilerplate and passes -- "the fee is not refundable", "state surcharges are collected in addition", "this schedule supersedes the prior part", "where this schedule conflicts with the ordinance, the ordinance controls", "fees are set on a cost-recovery basis". A statement that attaches a QUANTITY to a fee is an extraneous fact and fails unless a `fee` reveal licenses that basis for that row: a denominator ("per application", "per unit", "per year", "annually"), a rate or percentage, a proration, or a blanket "unless otherwise noted" that supplies a basis the spec withheld. The reason the line sits there and not elsewhere: payer cost is a scored quantity in this project, so a denominator is something an extractor will turn into a burden number, while an unquantified policy rule is not. Realistic boilerplate therefore stays, and every claim that could move a scored quantity needs a licence. Two clarifications the first application of this rule earned, both of which existed only in dispatch text and are therefore now here: a **Basis column** falls under the rule only when it states a QUANTIFIED basis the spec withheld -- a denominator, a staff-hour count or an hourly rate -- because "Cost recovery" answers how the amount was set rather than "per what?", and the licensed sentence "fees are set on a cost-recovery basis" is itself a blanket basis statement that stays, so failing the same content in column form would make the standard turn on typography. And a **period word describing how often the schedule is reviewed or amended** is not a denominator: "amounts in this schedule are reviewed annually as part of the budget" states an amendment cadence, not any row's charging basis, and stays. "Annually" is a denominator only where it says what the payer is charged per.
- `contamination_ok`: each contamination fact present and plausibly attributed to the other process/jurisdiction.
- `style_ok`: brief judgment vs the style guide.
- `criteria`: for every `criterion` reveal, was the reading stated at the right fidelity (an `exact` reading must carry its number verbatim)? Any stated threshold, cap, or standard that no `criterion` reveal licenses is an `extraneous_facts` entry; any reading stated for a predicate in `must_not_reveal_criteria` is a leak.
- `pass`: true only if all required found at correct fidelity, zero leaks, zero extraneous process facts.

Explicitly check measurement semantics, not just matching numeric strings:

- Start and end events must match `measurement_clock`. First decision, last decision
  and closeout are different; first filing is not receipt of a complete application.
- A completed decision cannot be rendered as an ongoing wait because its poster is
  labeled "delayed". A sum of visit cycles is neither one visit nor a first-to-last
  span, and is not necessarily all pre-filing preparation. Elapsed time is not labor.
- A median, p90, informal forecast and legal target must retain their meanings.
  Cohort denominators must match the timing statistic; missing observations do not
  imply a zero-day processing time.
- Actor assignments require an explicit activity/actor reveal or the supplied
  public-law relationship. A named department's existence is not permission to
  assign other steps to it.
- Persona `true_timeline`/`true_days` values are verification-only. The document
  must preserve the specified noisy report, not replace it with the hidden number.

For failures, write a one-line fix instruction in `fix` (the renderer will be re-run with it). Append a summary line per artifact to `verify_log.jsonl`. Never git commit; never edit the artifacts yourself.
