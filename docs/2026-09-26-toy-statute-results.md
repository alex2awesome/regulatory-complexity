# Toy statute: results (2026-09-26)

Protocol: `docs/2026-09-26-toy-statute-plan.md`, including addenda A and B.
Goal served: `docs/CORE_GOAL.md`.
Code: `pipeline/procbench/toy_statute/`. Tests: `tests/test_toy_statute.py`
(15 pass). Runs: `runs/toy_statute_20260926/W0/`.

## What was built

1. **Public spec** (`spec.py`):
   - the statute (backyard hens, §§1–5);
   - the decision model read from it (D1 application, concrete; D2 nuisance
     determination, vague; D3 decision with a 30-day deadline, concrete);
   - a nine-p-step catalog, and a menu of six candidate process structures
     for the vague step. Structure S3 has one p-step serving two d-steps.
2. **World W0** (`truth_world.py`, generator and scorer only): Alder = S1 (desk
   review), Birch = S3 (desk review + inspection that also issues the
   decision), Cedar = S4 (neighbour notice, 14-day comments, desk review,
   hearing if objection).
3. **Generator** (`generate.py`): 80 admin records (Alder, Cedar), 45 applicant
   reports (13 pending), and 3 agency web pages. Birch's page omits the
   inspection by design. Cedar's page falsely lists an inspection by chance
   (a 3% draw). There are also 2,000 held-out cases per town. Truth, evidence
   and held-out cases live in separate directories. An AST test enforces that
   the fitter and baseline never import truth.
4. **Estimands** (`estimands.py`), one code path for truth and posterior:
   - burden per p-step (days, applicant hours, dollars), rolled up to d-steps,
     with shared p-steps attributed to every d-step they serve;
   - total-time distribution and the deadline miss probability;
   - process complexity (p-steps per case, applicant interactions, path
     entropy, coefficient of variation);
   - the drafting counterfactual (§3 rewritten as "review the site plan");
   - statute-level implementation variety.

   The exact values match Monte Carlo on the held-out cases.
5. **Bayesian model** (`model.py`): exact enumeration of 6 structures × case
   paths (loops 0–4 × hearing), exact FFT day-grid convolutions and no per-case
   latents; 36 continuous parameters; 7 ms per likelihood evaluation.
   Samplers: `fit.py` (preconditioned random-walk Metropolis) and `smc.py`
   (adaptive tempered SMC).
6. **LLM baseline** (`llm_baseline.py`): tool-less `claude -p --model opus`,
   run from an empty directory. It gets the same statute, decision model,
   catalog, structure menu, assumptions and evidence, plus precise estimand
   definitions and a JSON template. Three repeats, about $0.35 each, with
   5k–10k thinking tokens each.
7. **Text round trip** (`text_roundtrip.py`): Sonnet renders the reports as
   forum posts and the web pages as agency text. Sonnet then extracts them
   back. **Extraction was exact**: 45/45 records, 128/128 mentions, all
   hours, fees and web pages. So the Bayesian likelihood on the extracted
   evidence equals the structured one to 0.0. The LLM baseline was also run on
   the raw text.
8. **Scorer** (`score.py`, `report.py`): structure log score and Brier; 90%
   interval score, coverage and median error per estimand; pinball loss on
   held-out cases. Summaries are also computed on "non-trivial" estimands,
   excluding those that are exactly 0 in truth and answered [0, 0, 0].

## What the truth says (the drafting answer)

| town | mean total days | P(miss 30-day deadline) | Δ days if §3 were concrete |
|---|---|---|---|
| Alder (S1) | 23.1 | 0.03 | 0 |
| Birch (S3) | 41.8 | 0.48 | −11.0 |
| Cedar (S4) | 47.1 | 0.55 | −20.8 |

- **Statute level:** writing §3 concretely would cut mean time by 10.6 days per
  town.
- It would also shrink the between-town SD of mean total time by 7.2 days.
- D2 implementation variety is 1.58 bits: every town solidifies the vague
  step differently.
- Two of the three towns miss the statutory 30-day deadline about half the
  time. The deadline binds only where the vague step was solidified into
  extra procedure.

## Fitting history (all failures preserved)

- **fit001** (random-walk Metropolis, 4 × 30k): **FAILED** (R-hat 1.17, ESS 16).
- **fit002** (tempered SMC, 2 × 2,000 particles, 12 moves): **FAILED**
  (between-run R-hat 1.061, standardized mean difference 0.53). Log evidence
  agreed between the runs (−513.2 against −513.7).
- **fit003** (tempered SMC, 2 × 3,000 particles, 30 moves): **narrow gate
  FAILURE**.
  - Between-run R-hat: worst 1.0027, which passes.
  - Standardized mean difference: worst 0.119 against the 0.1 limit.
  - Only 2 of 36 parameters exceed 0.1: Alder's objection probability
    (essentially prior-only, since no supported Alder structure has a hearing)
    at 0.119, and Cedar's speed factor at 0.103.
  - Log evidence: −513.33 against −513.47.
  - Per protocol, no further attempts. fit003 is reported as the best
    available Bayesian fit, labelled as a narrow failure; it does not count as
    passed.
  The first execution was stopped for BLAS thread oversubscription (not
  results-driven) and re-executed identically.
- **Why the samplers struggle.** It is a finding, not only a bug.
  - Admin whole-process totals pin the *sum* of completeness check, desk
    review and decision issuance.
  - Individual step durations are identified only by the few reports that
    time an intermediate event.
  - The posterior is a broad ridge.
  - **Whole-process clocks do not identify per-step burden.** Per-step burden
    — our first core estimand — needs step-level timing evidence or
    informative priors.
- **Post-hoc check** (labelled as such). The decision-relevant estimands agree
  across fit001 and each fit002 run, well within their interval widths:
  - mean totals: about 24 / 44–45 / 46 days;
  - deadline miss: Birch about 0.4, Cedar about 0.55;
  - statute counterfactual: about −8 days [−17, −1].

  The sampler failures sit in nuisance parameters.

## Bayes vs LLM

Methods compared:

- `bayes_fit003`: tempered SMC, 6,000 particles, a narrow gate failure (see Fitting history above).
- `llm_avg3`: the average of 3 tool-less Opus runs on the structured evidence.
- `llmtext_avg3`: the same, on the raw forum-post and web-page text.

Each cell is median [5%, 95%].

**Alder** (true structure S1; P(true structure): bayes_fit003 1.00, llm_avg3 0.90, llmtext_avg3 0.90)

| estimand | truth | bayes_fit003 | llm_avg3 | llmtext_avg3 |
|---|---|---|---|---|
| mean total days | 23.09 | 23.91 [21.74, 26.79] | 22.90 [20.83, 25.17] | 22.93 [21.00, 25.33] |
| D1 application days | 7.23 | 6.80 [3.28, 13.17] | 6.33 [3.83, 10.67] | 7.67 [4.67, 11.67] |
| D2 nuisance-determination days (vague step) | 11.33 | 10.99 [2.78, 16.77] | 11.67 [7.67, 16.00] | 10.50 [6.33, 15.33] |
| D3 decision days | 4.53 | 5.60 [2.53, 11.83] | 4.80 [2.17, 8.00] | 5.00 [2.17, 8.67] |
| applicant hours | 3.65 | 3.67 [2.79, 4.92] | 3.13 [2.33, 4.23] | 3.13 [2.40, 4.17] |
| dollars | 25.00 | 25.00 [25.00, 25.00] | 25.00 [25.00, 25.00] | 25.00 [25.00, 26.00] |
| P(miss 30-day deadline) | 0.03 | 0.07 [0.00, 0.16] | 0.07 [0.02, 0.16] | 0.07 [0.02, 0.16] |
| p-steps executed per case | 4.22 | 4.12 [4.01, 4.56] | 4.38 [4.12, 4.80] | 4.57 [4.17, 5.13] |
| path entropy (bits) | 0.52 | 0.33 [0.04, 0.97] | 0.74 [0.28, 1.17] | 0.95 [0.43, 1.43] |
| Δ days if §3 made concrete | 0.00 | 0.00 [0.00, 0.00] | 0.00 [-1.50, 0.17] | 0.00 [-2.33, 0.00] |

**Birch** (true structure S3; P(true structure): bayes_fit003 1.00, llm_avg3 0.73, llmtext_avg3 0.63)

| estimand | truth | bayes_fit003 | llm_avg3 | llmtext_avg3 |
|---|---|---|---|---|
| mean total days | 41.77 | 44.28 [35.48, 59.50] | 37.83 [30.33, 47.67] | 39.33 [31.00, 51.00] |
| D1 application days | 10.14 | 10.72 [4.40, 24.95] | 7.83 [4.33, 15.00] | 10.00 [5.33, 17.00] |
| D2 nuisance-determination days (vague step) | 31.63 | 32.83 [19.94, 50.25] | 30.00 [20.00, 40.67] | 28.00 [17.00, 40.33] |
| D3 decision days | 16.90 | 16.25 [3.69, 37.50] | 16.33 [4.00, 25.33] | 13.50 [3.00, 24.00] |
| applicant hours | 5.50 | 7.43 [5.64, 9.98] | 7.27 [5.33, 9.50] | 7.33 [5.60, 9.50] |
| dollars | 90.00 | 90.00 [90.00, 90.00] | 90.00 [86.67, 90.00] | 90.00 [88.00, 92.67] |
| P(miss 30-day deadline) | 0.48 | 0.46 [0.09, 0.75] | 0.37 [0.17, 0.60] | 0.41 [0.23, 0.62] |
| p-steps executed per case | 4.35 | 4.23 [4.01, 5.37] | 4.57 [4.23, 5.47] | 5.23 [4.70, 6.03] |
| path entropy (bits) | 0.72 | 0.54 [0.06, 1.63] | 0.86 [0.37, 1.40] | 1.03 [0.50, 1.60] |
| Δ days if §3 made concrete | -11.01 | -7.55 [-30.52, 8.17] | -12.33 [-21.33, -5.00] | -12.33 [-22.67, -5.00] |

**Cedar** (true structure S4; P(true structure): bayes_fit003 1.00, llm_avg3 0.80, llmtext_avg3 0.73)

| estimand | truth | bayes_fit003 | llm_avg3 | llmtext_avg3 |
|---|---|---|---|---|
| mean total days | 47.10 | 45.69 [42.56, 50.19] | 44.07 [40.67, 47.83] | 44.00 [40.17, 48.17] |
| D1 application days | 12.00 | 11.00 [5.74, 18.52] | 9.30 [5.67, 14.67] | 8.33 [5.17, 13.33] |
| D2 nuisance-determination days (vague step) | 31.02 | 28.38 [20.18, 36.14] | 30.17 [23.67, 37.33] | 31.67 [25.00, 38.67] |
| D3 decision days | 4.08 | 5.88 [2.79, 12.02] | 4.50 [2.00, 9.00] | 4.27 [1.67, 8.33] |
| applicant hours | 5.41 | 5.00 [3.78, 7.49] | 4.90 [3.70, 6.43] | 4.93 [3.80, 6.30] |
| dollars | 55.00 | 55.00 [55.00, 55.00] | 55.00 [55.00, 60.00] | 55.33 [55.00, 62.33] |
| P(miss 30-day deadline) | 0.55 | 0.57 [0.30, 0.76] | 0.51 [0.32, 0.71] | 0.65 [0.50, 0.79] |
| p-steps executed per case | 7.27 | 7.06 [6.47, 8.14] | 6.93 [6.47, 7.67] | 7.03 [6.47, 7.80] |
| path entropy (bits) | 2.20 | 1.96 [1.21, 2.70] | 1.82 [1.23, 2.33] | 1.83 [1.27, 2.33] |
| Δ days if §3 made concrete | -20.82 | -16.26 [-24.55, -8.63] | -20.50 [-27.00, -14.00] | -23.50 [-30.00, -17.00] |

**Statute level**

| estimand | truth | bayes_fit003 | llm_avg3 | llmtext_avg3 |
|---|---|---|---|---|
| D2 implementation variety (bits) | 1.58 | 1.58 [1.58, 1.58] | 1.58 [1.03, 1.58] | 1.58 [0.91, 1.58] |
| between-town SD of D2 days | 9.43 | 9.59 [6.75, 16.10] | 8.67 [5.00, 12.33] | 9.30 [5.50, 13.00] |
| Δ mean days per town if §3 made concrete | -10.61 | -7.95 [-16.67, -1.83] | -11.00 [-15.33, -6.67] | -11.75 [-16.00, -7.75] |
| Δ between-town SD of total days | -7.15 | -4.36 [-10.22, 2.82] | -7.50 [-11.33, -3.33] | -6.00 [-9.50, -2.50] |

**Scores** (lower is better except log score; non-trivial = excluding estimands that are exactly 0 in truth and answered [0,0,0])

| method | structure log score | non-trivial scaled interval score | non-trivial 90% coverage | non-trivial scaled median error | predictive pinball |
|---|---|---|---|---|---|
| bayes_fit003 | -0.001 | 1.150 | 0.99 | 0.201 | 2.910 |
| llm_avg3 | -0.214 | 1.052 | 1.00 | 0.133 | 2.949 |
| llm0 | -0.219 | 1.117 | 0.98 | 0.155 | 2.944 |
| llm1 | -0.228 | 1.333 | 0.99 | 0.145 | 2.956 |
| llm2 | -0.197 | 1.018 | 0.98 | 0.144 | 2.952 |
| llmtext_avg3 | -0.291 | 1.381 | 0.97 | 0.172 | 2.951 |
| fit002_FAILED | -0.001 | 1.177 | 0.98 | 0.204 | 2.916 |
| fit001_FAILED | -0.002 | 1.121 | 0.99 | 0.203 | 2.928 |

**Scaled interval score by estimand family**

| family | bayes_fit003 | llm_avg3 | llm0 | llm1 | llm2 | llmtext_avg3 | fit002_FAILED | fit001_FAILED |
|---|---|---|---|---|---|---|---|---|
| complexity | 0.766 | 0.583 | 0.574 | 0.644 | 0.533 | 0.780 | 0.751 | 0.806 |
| counterfactual | 0.969 | 0.875 | 0.895 | 0.816 | 0.914 | 1.176 | 0.973 | 0.963 |
| deadline | 1.769 | 1.429 | 1.425 | 1.304 | 2.604 | 1.335 | 1.769 | 1.761 |
| dstep_days | 1.498 | 0.982 | 0.978 | 1.015 | 0.955 | 1.009 | 1.484 | 1.483 |
| dstep_dollars | 0.000 | 0.170 | 0.111 | 0.259 | 0.139 | 1.051 | 0.000 | 0.000 |
| dstep_hours | 1.053 | 1.332 | 1.404 | 1.226 | 1.365 | 1.407 | 1.082 | 0.971 |
| pstep_days | 1.312 | 1.548 | 1.542 | 1.612 | 1.544 | 2.141 | 1.354 | 1.256 |
| pstep_dollars | 0.000 | 0.750 | 0.000 | 2.222 | 0.028 | 2.421 | 0.000 | 0.000 |
| pstep_hours | 1.434 | 1.829 | 2.024 | 1.713 | 1.749 | 2.088 | 1.566 | 1.332 |
| statute | 1.054 | 0.766 | 0.759 | 0.844 | 0.695 | 0.745 | 1.074 | 1.121 |
| total | 0.372 | 0.291 | 0.258 | 0.362 | 0.296 | 0.368 | 0.361 | 0.376 |

**Head-to-head** (non-trivial estimands; wins on the 90% interval score):

- bayes_fit003 vs llm_avg3: 42–60 (8 ties);
- bayes_fit003 vs llmtext_avg3: 57–54 (7 ties);
- llm_avg3 vs llmtext_avg3: 70–30 (18 ties).

The full list is in `W0/scores_final/summary.json`.


### Reading the comparison

1. **Structure: Bayes wins decisively.** Log score is about −0.001 against
   about −0.21 for the LLM. Exact enumeration of the menu extracts the
   structural signal from mentions, gap patterns and web pages. That signal
   includes "inspection → decision the same day" (Birch), and it discounts
   Cedar's false web listing correctly. The LLM gets the right answer most of
   the time but hedges (0.72–0.9).
2. **Per-p-step burden: Bayes has the better interval scores.** Scaled
   interval score by family, Bayes against the LLM average: p-step days
   1.31 vs 1.55, p-step hours 1.43 vs 1.83, dollars 0 vs 0.17–0.75. The LLM's
   narrower intervals miss more often at the step level. The LLM's *medians*
   are often closer, though, where the evidence cannot separate steps and
   common sense sets a better prior than the Bayesian model's generic one
   (every step median ~7 days, σ ~0.4):
   - notice mailing: truth 1.9 d, LLM 3.7, Bayes 6.3;
   - inspection attendance: truth 1.7 h, LLM 2.7, Bayes 3.4;
   - comment period: truth 14, LLM 14.0, Bayes 6.6. **Caveat:** the LLM
     prompt's structure text said "14-day-style comment period". That is
     information the Bayesian prior did not get. It is disclosed here and not
     re-run, because of the usage limit.
3. **Roll-ups and the drafting lever: the LLM is better here.** d-step days
   0.98 vs 1.50; totals 0.29 vs 0.37; deadline 1.43 vs 1.77; complexity 0.58
   vs 0.77; counterfactual 0.88 vs 0.97; statute 0.77 vs 1.05.
   - Statute-level counterfactual (truth −10.6 days per town): LLM −11.0
     [−15.3, −6.7], Bayes −8.0 [−16.7, −1.8].
   - Birch counterfactual (truth −11.0): LLM −12.3 [−21.3, −5.0], Bayes −7.6
     [−30.5, 8.2].
   - The Bayesian roll-up intervals are honest but too wide, because weakly
     identified per-step posteriors propagate upward. They are widest for
     Birch, which has no admin records.
   - The Bayesian model never puts meaningful mass on the wrong structure. The
     LLM hedges, but that costs little on roll-ups.
4. **Calibration.** The Bayesian 90% intervals cover 98–99% of non-trivial
   truths, too wide on this world. The prior mass on long step durations
   inflates the per-step intervals.
5. **Text vs structured evidence.** The LLM loses accuracy reading raw posts
   (non-trivial interval score 1.38 against 1.05 for the structured-evidence
   average). The Bayesian pipeline does not, because extraction was exact.
   Rendering was deliberately faithful, so this is an upper bound on text
   quality, not realism.
6. **Held-out prediction** (pinball on total days): all methods are within 1%
   (2.91–2.96), with Bayes lowest (2.910). Total-time prediction is easy given the admin records.

## What this means for the method (the point of the toy)

- The frame works end to end: statute → decision model (concrete/vague) →
  bounded refinement menu → exact structure posterior → burden and complexity
  estimands → a drafting counterfactual with uncertainty.
- **Bayes is good at the discrete, structural part** (which refinement did each
  jurisdiction choose) **and at calibrated per-step intervals. It is too
  conservative on roll-ups.** **LLMs are good at scale common sense and at
  sharp roll-ups.** On this world the LLM is closer on the drafting
  counterfactual. The natural next model is the hybrid already named in
  CORE_GOAL: an LLM-elicited prior over the menu *and over step-duration
  scales*, updated by the exact likelihood. The toy is the right testbed.
- Per-step burden needs step-level evidence. For real data this argues for
  targeting sources that time intermediate events (inspection dates,
  correction requests), not only more whole-process clocks.
- Samplers: the exact-marginal likelihood makes tempered SMC workable. Real
  problems will be larger, so gradient information or reparameterizing the
  weakly identified ridge (sums and shares instead of separate medians) is
  the next engineering step.

## Limitations (declared)

- One world, three towns. No significance claims.
- The Bayesian model is well specified, which is an advantage.
- Reporting is unselected.
- Text rendering was faithful.
- There is one prompt-information asymmetry (see above).
- V6 was not fitted. A read-only assessment estimates a 250–400-line adapter.
  Web-page listings and mention flags have no V6 likelihood.

## Next (proposed, not started)

1. **Hybrid:** LLM-elicited priors (menu and step scales), then refit. Remove
   the "14-day" asymmetry from the LLM prompt.
2. **Replicate over about 5 random worlds.** Add selection-biased reporting
   and messy text rendering (vague and relative phrasing) as declared
   variants.
3. **Ridge reparameterization** or gradient-based sampling.
4. **V6 adapter** on the same W0 evidence, to diagnose V6.
