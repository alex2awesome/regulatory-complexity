# Toy statute round 2: predeclared protocol (2026-09-26, overnight)

Follows `docs/2026-09-26-toy-statute-results.md` and Alex's questions of
2026-09-26:
- Will the LLM scale?
- Is there a causal reading of the counterfactual?
- He is uncomfortable with LLM priors, since knowledge may not transfer across
  jurisdictions and cultures; "you can try it if you think it will help".

Written before any round-2 fit or LLM run is scored. Round-1 results are
frozen.

## Changes (code)

1. **Town-centering constraint** (`Model(center_towns=True)`). Town speed
   factors enter as deviations from their mean (sum-to-zero). This removes the
   dominant posterior ridge seen in fit003: step medians traded off against all
   town speed factors, with correlations up to −0.61. Scientific content is
   unchanged; step medians now mean "at the average town's speed".
2. **Robust informative priors** (`prior_elicit.py`, `Model(prior_overrides,
   struct_prior)`).
   - Opus, with no tools and no evidence, gives typical values and 90% ranges
     for step durations and applicant hours, plus structure probabilities.
     Three repeats, averaged.
   - These become log-normal priors, widened ×1.5 and mixed 80/20 with the
     original vague prior. The structure prior is mixed 80/20 with uniform.
   - Spreads, town speed, incompleteness and objection probabilities, and
     noise keep their vague priors.
   - Elicited once: `runs/toy_statute_20260926/llm_prior001/prior.json`. It is
     world-independent, because every world shares the statute.
3. **LLM baseline prompt leak removed.** S4's text no longer says
   "14-day-style comment period". Note: the no-evidence elicitation itself
   proposed a 14-day comment period, so this was general knowledge.
4. **Gate v2** (`smc.py --gate v2`). This refines, not relaxes, the gate:
   - **Data-informed parameters** (posterior SD < 0.8 × prior SD, from 20,000
     prior draws): between-run rank R-hat < 1.01 AND standardized mean
     difference < 0.1.
   - **Prior-dominated parameters:** R-hat < 1.01 only (SMD reported).
   - **Every scored estimand:** the two runs' medians differ by < 0.2
     posterior SD (from each run's 5–95% width / 3.29). Pure Monte Carlo noise
     between two medians of 1,000 draws is about 0.056 SD, so 0.2 is about
     3.6 SE.

## Worlds

- **W0:** unchanged (round 1).
- **W1, adversarial to common-sense priors:** same statute, different
  structures (Alder S2, Birch S6, Cedar S1), and step scales far from typical
  intuition: notice 18 d, comment 30 d, desk review 35 d, hearing 45 d,
  prepare 12 h. Admin records come from Birch and Cedar. Birch's web page omits
  the notice. Truth: mean totals 82 / 91 / 89 days; deadline missed 96–100%;
  statute counterfactual −18.7 days per town.
- **W0×5, W0×25:** W0's truth with 5× and 25× the evidence (400 and 2,000
  admin records; 225 and 1,125 reports), fresh draws. This is for the scaling
  question.

## Runs

| id | world | model | budget |
|---|---|---|---|
| W0/fit004 | W0 | centered, vague priors | B |
| W0/fit005 | W0 | centered, LLM priors | B |
| W1/fit001 | W1 | centered, vague priors | B |
| W1/fit002 | W1 | centered, LLM priors | B |
| W0x5/fit001 | W0×5 | centered, vague priors | B |
| W0x25/fit001 | W0×25 | centered, vague priors | B |
| W0/llm_baseline002 | W0 | Opus ×3, leak removed, structured evidence | — |
| W1/llm_baseline001 | W1 | Opus ×3 | — |
| W0x5/llm_baseline001 | W0×5 | Opus ×3 | — |
| W0x25/llm_baseline001 | W0×25 | Opus ×3 | — |

**Budget B,** a predeclared decision rule. A development check
(`W0/dev_center_check`, centered model, fit002's failed budget of 2,000
particles × 12 moves, diagnostics only, never scored) decides it:
- if the check passes gate v1, B = 2,000 particles × 20 moves;
- otherwise B = 3,000 particles × 30 moves.

In both cases: 2 runs, 8 workers, single-threaded BLAS, seed 20261001, and
gate v2. One execution per run id; failures are reported, with no retries.

## Predeclared questions and how they are read

- **Q1 (convergence).** Does centering make the fits pass gate v2? Report per
  fit.
- **Q2 (hybrid helps where priors are right).** On W0, does fit005 have a lower
  non-trivial scaled interval score than fit004, overall and on the roll-up
  families (dstep_days, total, deadline, complexity, counterfactual, statute)?
- **Q3 (hybrid harm where priors are wrong).** On W1, harm = fit002 − fit001
  (non-trivial scaled interval score, overall and by family). Also report the
  structure log score and each lever estimand. Prior–data conflict diagnostic:
  for each step, the posterior median's percentile under the LLM prior's LLM
  component. Anything beyond the 2.5–97.5 percentiles is flagged as a
  conflict.
- **Q4 (scaling).** For W0, W0×5 and W0×25: Bayes (vague, centered) and the LLM
  average, non-trivial scaled interval score and median error, overall and by
  family. Report whether per-step families improve with n, not only roll-ups.
  The predicted limit is that whole-process clocks leave the per-step ridge in
  place.
- **Q5 (LLM, leak-free).** W0 llm_baseline002 against round 1's llm_baseline001:
  how much did the leak matter?

One world per condition means no significance claims. Descriptive only.

## Also tonight (no fits)

- Causal framing of the model and the drafting counterfactual:
  `docs/process-model-causal-frame.md`.
- Complexity-measures literature survey (agent):
  `docs/2026-09-26-complexity-measures-survey.md`. Promising measures may be
  added to `estimands.py` as additional descriptive estimands. They are not
  scored in round 2 unless they are ready before the LLM runs, in which case
  they are added to both methods.

## Addendum R2-A (2026-09-26 10:10, before any further round-2 scoring)

**Infrastructure.** The local queue was stopped during W0/fit005. Mac load
average was about 500: 16 CPU-minutes in 7 hours. fit004 had completed. It
passed gate v1 and gate v2, and it is not re-run. All remaining round-2 fits
move to sk3 (288 cores; miniconda Python 3.11, numpy 2.2.6, scipy 1.17.1,
arviz 0.23.4), with identical code, budget (3,000 × 30), seeds and gate v2.
fit005's partial local attempt is preserved as `fit005_attempt1_mac_overloaded`
and is not inspected. Fits run in parallel on sk3, 8 workers each.

**New question Q6: step linking through milestones.** Alex asked what fixes
per-step identification, and emphasized the machinery of linking steps.

- **Worlds W0m and W1m.** They have the same truth and the same seed as W0
  and W1 (the same underlying cases). The only change is that admin records
  also log status-change milestones: "deemed complete", plus inspection and
  hearing dates where they occurred. Milestone records are exact; the
  generator applies no contamination to them.
- **Model support.** Each milestone record contributes the exact likelihood of
  each segment between consecutive recorded events. The combo's chain must
  contain exactly the recorded milestone event set. Otherwise only the fixed
  2% contamination term explains the record. That is the step-linking
  constraint.
- **Runs.** W0m/fit001 and W1m/fit001 (vague priors); W0m/fit002 and
  W1m/fit002 (LLM priors); W0m and W1m llm_baseline001 (Opus ×3). The same
  budget and gate v2 apply.
- **Predicted:**
  1. per-step families (pstep_days, dstep_days) improve sharply against the
     no-milestone fit on the same cases;
  2. prior sensitivity (hybrid minus vague) shrinks;
  3. the W1 failure mode of prior-driven step splits largely disappears for
     both Bayes and the LLM.

## Addendum R2-B (2026-09-26 15:50): fee-split bug fix, post hoc, reported both ways

The deterministic fee rule split an unlisted fee residual *equally*, with zero
uncertainty, whenever more than one unlisted fee-bearing step was present. The
example is W1 Birch: notice plus inspection. When those items always
co-occur, the split is unidentified, the same joint-step problem as for
durations. The equal split produced overconfident point answers ($30
[30, 30] against a truth of $60 / $0), with huge interval scores. Fix: the
split is drawn Dirichlet(1) per posterior draw
(`Model.fee_table(rng)`, `answers_from_draws(random_fee_split=True)`).
Answers are recomputed from the same saved particles (`answers_feefix.json`);
no refit. The original answers are kept and both are reported. Fees remain
outside the likelihood, as declared.
