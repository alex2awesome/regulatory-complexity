# Rule-following under interpretive openness: update for Dan (2026-11-11)

Full plan: `docs/2026-11-10-rule-following-experiment-plan.md`. Code: `benchmark/rulegap/`.

**2026-11-11 measurement update:** E1 and the first E3 arms are complete (1,960 episodes), and corrected
scores are joined to complexity measurements in `docs/2026-11-11-rulegap-toy-results.md`. The interpretation
sets are authored candidates, not yet human-validated. E0 is now scoped to 17 complete readings, 51 human
judgments; review packets are ready. Confirmatory interpretation claims wait for those ratings.

## 1. Framing

The experiment separates a rule's text, candidate interpretations, a governing reference, and purpose.
Under a specified interpretation, the verdict is

    Legal(x) = I(c)(x)

| Symbol | Meaning |
|---|---|
| c | The rule text as printed: the sentence, plus any printed definitions. |
| x | A raw case plus a proposed action. Raw means orders with amounts, dates, vendors and descriptions, not labels such as "same need" or "emergency". |
| I | An interpretation: a function that takes the text to an executable decision procedure. I(c) is that procedure, and I(c)(x) is its verdict: legal, illegal, or undefined. |
| C(c; B) | A bounded candidate inventory: authored or sourced interpretations proposed for this text and stated background. Enumeration does not establish defensibility. |
| V(c; B) | The human-validated subset of C: complete interpretations judged defensible under a frozen review protocol. We do not claim it contains every defensible reading. |
| I* | The governing reference: authored in the toys, separately supported by practice evidence in a real case. Its membership in V must be checked, never forced. |
| P | The purpose function: which outcomes the drafter wanted, declared separately from the text. |

I* may be partial. Practice sometimes accepts several readings, and sometimes has not spoken on a case at all. On those cases the verdict is "undefined", and we never score an agent as breaching there.

Every judged action is scored against I*, purpose, and the selected reading set. A loophole requires an
unwanted action illegal under I* but supported by another validated reading. Until E0 is complete, the
corresponding exploratory category is **candidate gap**. Other cells are compliant, purpose-serving breach,
drafting failure, undefined, and breach unsupported by the selected bounded set. This is an outcome
classification, not a finding about the agent's motive. Numerical reports and verdicts must agree under
the same reading.

## 2. Where tacit knowledge lives

Tacit knowledge is everything needed to apply the rule that the text does not print. It sits in four places.

1. **Choosing among readings.** Picking I* out of the candidate set. We report -log2 of its prior mass as reference surprisal, not measured learning effort.
2. **Characterizing facts.** Deciding that two orders serve "the same need" is part of the reading, not a given fact. The benchmark never hands the agent that label.
3. **Articulated components.** Some parts of even a fully printed rule are stated in words and cannot be computed, such as "an imminent threat to health or safety". We model these as named judgment leaves. Their value on a case is a practice-holder label where one exists and open otherwise. This is the same seam between metric and judgment predicates as in the AB 2533 pilot.
4. **Background and purpose.** The background B that makes a reading defensible, and the purpose P, are both outside the text.

Printing a definition moves knowledge from place 1 into the text. It does not touch place 3. In the procurement toy the fully defined rule still leaves about 4% of cases undefined, all through the one judgment leaf.

## 3. How the interpretation set is determined

- **Candidate construction:** explicit term menus and bounded parameter families generate proposals.
  The procurement grid has 768 assignments but only 400 distinct expanded programs; percentile has 54.
  Incompatible combinations require explicit exclusions and reasons. Distinct programs are also compared
  on cases; agreement on a finite panel is not a proof of global equivalence.
- **Evidence:** a statutory definition, software convention or observed city practice can propose a
  reading. Its existence does not prove defensibility for this text. Authored and source-backed views are
  separate. A city's challenged provision is not automatically an admissible reading of the statute.
- **Validation (E0):** three independent humans judge each COMPLETE interpretation against the exact text
  and B, without I*, P, agent results or incentives. All three submit yes/no decisions and rationales;
  two of three accepts or rejects. Abstentions and missing ratings remain pending. LLMs can propose
  missing candidates but their votes do not substitute for human validation.
- **First scope:** nine percentile methods with samples and comparison fixed in the text; eight procurement
  emergency/bid combinations with purchase fixed. Seventeen readings × three raters = 51 judgments.
  The broader inventories are exploratory until separately reviewed. Grammar generation is not yet built
  and would not by itself solve the admissibility problem.

## 4. Experiments and estimated timing

Estimates, not commitments. Human-rater steps depend on recruiting raters.

| Experiment | What it does | Status and estimate |
|---|---|---|
| Machinery | Readings as code, classifier, complexity metrics, two solvers, agent harness | Built and tested 2026-11-11 |
| E1 baseline | Candidate-based gaps and reference violations on toy rules, with and without a conflicting incentive. Two models. | 1,680 episodes complete; corrected scores and complexity table available |
| E2 ladders | Same rule at several levels of printed definition; outcomes against complexity measures | 1 week |
| E3 drafting arms | Purpose, anti-avoidance and examples against a control; same tools in every arm | First 280 episodes complete; other arms pending |
| E4 conflicts | Two rules that cannot both be met under I*; does the agent flag or reinterpret? | Solver side built; runs 2 weeks |
| Real: percentile | Published definitions and software defaults as readings | 2 to 3 days |
| Real: airline policy (tau2-bench) | Published benchmark policy with known loopholes | about 1 week |
| Real: procurement thresholds | FAR and California text; splitting and bunching in 197,000 state purchase orders | about 2 weeks |
| Real: ADU statute (E7) | Cities' provisions as readings, HCD's 2,420 findings as I*; per-jurisdiction page versus operative complexity against permit timing | 3 to 4 weeks |
| E0, E6 human raters and anchors | E0 whole-reading defensibility ratings; E6 human baseline | E0 packets ready, 51 ratings needed; E6 unscheduled |

## 5. What we are trying to show

1. Test whether incentives increase reference violations supported by defensible alternative readings. An incentive effect alone does not identify knowing defection.
2. Drafting is a treatment: how a rule is written changes the loophole rate, and some fixes work better than others.
3. Separate text size, structural complexity and interpretation-dependent determinacy. Settled share depends on the chosen reading set and case/action distribution; it is a proxy to investigate, not the definition of rules versus standards.
4. Test whether operative complexity predicts held-out burden better than page complexity. Timing used to infer a tree cannot also be its independent evaluation target.

**Measurement.** Results are joined to text size, Boolean tree size/rank, distinct candidate programs,
reading entropy, reference surprisal, settled share, purpose mismatch, cross-case certificate summaries,
and bounded perturbation costs. Certificates exclude every action of the target case. Feature-internal
computations are not counted by the Boolean tree; extra-clause semantic complexity is unmodeled. Report
reference violations, purpose outcomes, completion and clarification alongside candidate gaps. A
model-as-judge remains a probe.

**Learning mechanism.** Partly.

- For the applier: yes in principle. Precedents eliminate readings; certificate size says how many are needed. The examples arm tests whether agents actually use them.
- For the drafter: a solver finds the cheapest loophole, a printed definition closes it, and the solver re-runs. This loop exists for the toy rules. It is manual, not a learner.
- For us as observers: not yet. Nothing updates a posterior over which reading an agent or a jurisdiction is using from its behaviour. That is the bridge to the main project's calibrated posterior over decision models, and it is the main open design question.

## Candidate-space measurements (toy rules, declared case distribution)

| Rule variant | Candidate assignments | Settled share | Reference surprisal, bits |
|---|---|---|---|
| Percentile, open | 54 | 0.60 | 2.5 |
| Percentile, all terms defined | 1 | 1.00 | 0 |
| Procurement, open | 768 | 0.62 | 8.4 |
| Procurement, "purchase" defined | 8 | 0.72 | 2.1 |
| Procurement, all terms defined | 1 | 0.96 | 0 |
| Procurement, exception removed | 192 | 0.78 | 7.1 |
