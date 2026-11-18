# Toy statute: plan and predeclared protocol (2026-09-26)

Serves `docs/CORE_GOAL.md`. Approved by Alex 2026-09-26 ("implement it in
full, synthesize the whole thing, then fit the Bayesian model and the LLM").
Purpose: get the statute → decision model → process model → observation
machinery right end to end on a world small enough to reason about exactly,
and find out whether a Bayesian model can beat (or usefully complement) an LLM
on the estimands we actually care about. This is a machinery test, not a
realism claim.

Code: `pipeline/procbench/toy_statute/`. Runs: `runs/toy_statute_20260926/`.
Tests: `tests/test_toy_statute.py`.

## 1. Statute (synthetic)

> **Backyard Hen Keeping Act.**
> §1. A resident of a single-family dwelling may keep up to six hens after
> obtaining a permit from the local permitting authority.
> §2. The applicant shall submit an application, together with a site plan
> showing the location of the coop and its distance to property lines.
> §3. Before issuing a permit, the authority shall determine that the coop will
> not create a nuisance to adjoining properties.
> §4. The authority shall issue or deny the permit within 30 days after
> receiving a complete application.
> §5. The authority may charge a reasonable application fee.

## 2. Decision model (read from the text)

| d-step | clause | tag | notes |
|---|---|---|---|
| D1 application | §2 (+§4 "complete") | concrete | completeness check implied by §4; fee amount vague (§5) |
| D2 nuisance determination | §3 | **vague** | procedure unspecified |
| D3 issue or deny | §4 | concrete | 30-day deadline from complete application |

Decision-model complexity (from text, not estimated): 3 d-steps, 1 vague
procedural clause, 1 vague fee clause, 1 deadline.

## 3. Process-step catalog and refinement menu

p-steps (actor; burden components):

| p-step | d-step | actor | days | hours | $ |
|---|---|---|---|---|---|
| prepare | D1 | applicant | – | yes | app fee |
| completeness_check | D1 | agency | yes | – | – |
| correction (loop) | D1 | applicant | yes | yes | – |
| neighbor_notice | D2 | agency | yes | – | notice fee |
| comment_period | D2 | neighbours | yes | – | – |
| desk_review | D2 | agency | yes | – | – |
| hearing (if objection) | D2 | board | yes | yes | – |
| site_inspection | D2 (and D3 if shared) | inspector | yes | yes | inspection fee |
| decision_issue | D3 | agency | yes | – | – |

D1 always refines to prepare → completeness_check, with a correction loop
(incomplete with town-specific probability; truncated at 4 loops). The
hypothesis space ("menu") for the vague D2 and the D3 refinement is six
structures:

| id | D2 refinement | D3 |
|---|---|---|
| S1 | desk_review | decision_issue |
| S2 | desk_review → site_inspection | decision_issue |
| S3 | desk_review → site_inspection | decided at the inspection (shared p-step) |
| S4 | neighbor_notice → comment_period → desk_review → [hearing if objection] | decision_issue |
| S5 | S4 steps → site_inspection | decision_issue |
| S6 | S4 steps → site_inspection | decided at the inspection (shared) |

Prior over structures: uniform (1/6). An LLM-elicited prior is a later variant.

## 4. World W0 (truth; readable only by generator and scorer)

Three towns. Truth structures: **Alder = S1, Birch = S3, Cedar = S4**. Agency
step durations are shared by step type and multiplied by a town speed factor
(Alder 1.0, Birch 1.3, Cedar 0.9); comment_period is a fixed 14 days;
correction is applicant-driven (no town factor). Step durations are
lognormal, rounded to whole days. Applicant hours lognormal, rounded to
quarter hours. Fees are fixed per town. Exact values live in
`toy_statute/truth_world.py`, which the fitter and baseline never import.

## 5. Evidence (structured records; Phase 1)

- **Admin records** (Alder, Cedar only): 40 cases each, submission and decision
  day, exact.
- **Applicant reports**: 15 per town, from cases *not* in the admin records
  (declared assumption: no overlap, so no double counting). About 20% pending
  ("submitted N days ago, still waiting"). Decided reports mention steps they
  noticed (correction, neighbour notice, inspection, hearing; detection < 1,
  small false-mention rate), give gaps between noticed events rounded to
  days/weeks/months with multiplicative noise, sometimes total applicant hours
  (noisy, half-hour rounding) and total fees paid (exact).
- **Agency web page** per town: listed steps (each true step listed with
  probability < 1, false listings rare) and a fee schedule. Designed feature:
  Birch's page omits the inspection and its fee.
- Reporting is random with respect to outcomes in Phase 1 (no selection
  bias). Selection-biased reporting is a declared later variant.

## 6. Estimands (both Bayes and LLM answer all of them)

Per town:

1. **Structure**: probability over S1–S6.
2. **Burden per p-step**, expected per case: elapsed days (for time-bearing
   steps), applicant hours (applicant-facing steps), dollars (fee-bearing
   steps). A step absent from the process contributes 0; a possibly-present
   step contributes its occurrence-weighted mean.
3. **Burden per d-step** (D1, D2, D3): mean days, hours, dollars. A shared
   p-step is attributed in full to each d-step it serves; totals count it once.
4. **Total**: mean days, q10/q50/q90 of total days for a new case, mean hours,
   mean dollars.
5. **Deadline**: P(complete application → decision > 30 days).
6. **Process complexity**: expected p-steps executed per case; expected
   applicant-facing interactions; path entropy (bits) over case paths
   (correction loops × hearing); coefficient of variation of total days.
7. **Counterfactual (lever)**: change in mean total days, hours and dollars if
   §3 were written concretely as "the authority shall review the site plan"
   (every town uses S1), each town keeping its own speed and incompleteness.

Statute level:

8. **Implementation variety of D2**: entropy (bits) of the distribution of D2
   refinements across the three towns; between-town SD of mean D2 days.
9. **Counterfactual, statute level**: mean over towns of the change in mean
   total days; change in the between-town SD of mean total days.

Each continuous estimand is answered as 5/50/95 quantiles.

## 7. Bayesian model

The same process family as the generator (well specified in Phase 1, a
declared advantage):

- Exact enumeration over the six structures per town, and over correction
  loops (0–4) and hearing (0/1) per case. There is no sampling over discrete
  structure.
- Step-duration distributions are discretized to the day. Every observed
  interval uses an exact convolution of the p-steps between the two observed
  events (FFT), so there are no per-case latent durations.
- Continuous parameters (about 36): step medians and spreads, town speed
  factors, per-town incompleteness and objection probabilities, applicant-hour
  medians and spread, report noise, mention detection and false-mention rates,
  web-page listing rates. Weakly informative priors are declared in code.
- Contamination: each reported gap or admin total has a fixed 2% probability
  of coming from a broad log-uniform distribution, so one odd report cannot
  zero out a structure.
- Fees enter the dollar estimands deterministically. The listed web-page items
  are used first. Any residual between reported totals and the listed items is
  attributed to unlisted fee-bearing steps present in the structure. They do
  not enter the structure likelihood.
- **Fit**: find the most likely parameters (L-BFGS), then a finite-difference
  Hessian, then 4 random-walk Metropolis chains preconditioned by the Laplace
  covariance. Chain covariance adaptation happens during warm-up only.
- **Fixed budget**: 4 chains × (10,000 warm-up + 20,000 kept, thinned by 10).
  **Gates**: rank-normalized R-hat < 1.01 and bulk ESS > 400 for every
  parameter. A failure is reported as a failure. At most one predeclared
  doubling of the kept iterations is allowed; no other extension.
- Structure posterior: Rao-Blackwellized p(s | θ, data) per draw. The
  estimands draw a structure per draw from it.

## 8. LLM baseline

- `claude -p --model opus` with **no tools**, run from an empty working
  directory. Three independent repeats.
- The prompt contains the statute, the decision model table, the p-step catalog
  and the S1–S6 menu (the same hypothesis space the Bayesian model gets), the
  full evidence JSON, and the estimand definitions.
- Output: JSON in the same answer schema as the Bayesian fit. Parsing failures
  are recorded as failures, not retried silently. One retry is allowed for
  invalid JSON only, and is recorded.

## 9. Scoring (against W0 truth)

- **Structure**: log score of the true structure; Brier score.
- **Continuous estimands**: 90% interval score
  `(u−l) + 20·(l−y)⁺ + 20·(y−u)⁺`, whether the interval covers the truth, and
  absolute error of the median. Scores are summarized per estimand family,
  per method, and per LLM repeat.
- **Predictive**: for 2,000 fresh held-out cases per town, the pinball loss of
  the predictive quantiles (5, 10, 25, 50, 75, 90, 95) of total days. The
  Bayesian model's quantiles come from its posterior predictive. The LLM is
  asked for the same quantiles.
- One world gives no significance claim. Replication over several random
  worlds is the declared next step if machinery works.

## 10. Phases

1. Generator, structured evidence, Bayesian fit, LLM baseline, scoring
   (this document).
2. Render the evidence as forum-style posts and web pages (LLM rendering). Then
   extract it back with an LLM, refit the Bayesian model on the extracted
   evidence, and give the LLM baseline the raw text. Extraction error is
   measured against the structured evidence.
3. Try the existing V6 model on the same W0 evidence, to diagnose whether V6
   recovers the truth.

Declared later variants: selection-biased reporting; misspecified truth
(non-lognormal durations, heavier-tailed report noise); an LLM-elicited
structure prior; more towns and random worlds.

## Addendum A (2026-09-26, before any scoring): fit001 failed; fit002 predeclared

**fit001 (random-walk Metropolis) FAILED its gates.** Budget: 4 chains ×
(10,000 warm-up + 20,000 kept). Worst rank R-hat was 1.172 and minimum bulk
ESS 16.2 (gates: < 1.01 and > 400). The worst parameters are the medians of
p-steps that appear only inside sums in the evidence: desk_review,
completeness_check and decision_issue. The chains are not in separate modes.
They drift slowly along a broad ridge: admin whole-process totals identify the
*sum* of these steps well, but individual steps only weakly, through the few
reports that time an intermediate event. This is itself a substantive finding
for the core goal: **whole-process clocks do not identify per-step burden
without step-level timing evidence.**

fit001 is preserved (`W0/bayes_fit001/`). Its answers are scored only as a
labelled failed-gate diagnostic, never as the Bayesian result. The one
predeclared doubling was not spent: at ESS 16, doubling cannot reach 400.

**fit002 (predeclared now):** the same model, priors and evidence, sampled by
adaptive tempered SMC (`toy_statute/smc.py`):

- 2 independent runs;
- 2,000 particles, starting from the prior;
- each next temperature chosen so the incremental ESS is N/2;
- systematic resampling, then 12 random-walk Metropolis moves per stage with
  the particle covariance (24 at the final temperature).

**Gates:** rank R-hat across the two runs < 1.01 and standardized mean
difference < 0.1 for every parameter. No retries, and no extension beyond this
budget. If fit002 fails, it is reported as failed.

## Addendum B (2026-09-26): fit002 failed; fit003 predeclared

**fit002 (tempered SMC, 2 runs × 2,000 particles, 12 moves per stage) FAILED
its gates.** Worst between-run rank R-hat was 1.061 and worst standardized mean
difference 0.53 (gates: < 1.01 and < 0.1). The two runs' log evidence agreed
(−513.2 against −513.7). The runs disagreed on the spreads (σ) and medians of
weakly identified p-steps: completeness_check σ, neighbor_notice σ,
correction median. fit002 is preserved and is not called the result.

**fit003 (predeclared now):** the same model, priors, evidence and SMC code,
with a larger fixed budget:

- 2 independent runs of 3,000 particles each;
- 30 random-walk Metropolis moves per stage, 60 at the final temperature;
- 8 workers;
- the same gates;
- no further attempts after this one.

**Post-hoc, descriptive only (labelled as such):** for fit001 and for each
fit002 run separately, compare the scored estimands (burden, complexity,
counterfactual). This shows whether conclusions depend on the unmixed nuisance
parameters. It does not replace the gates.

**fit003 infrastructure re-execution (2026-09-26 23:40 PT).** The first
execution ran with numpy/BLAS thread oversubscription: 8 workers each spawned
their own math threads, and machine load reached 100–157 on 10 cores. Run 0
took 1.5 h. Run 1 was still running after 3.5 h and its output was never
inspected. That execution was stopped and preserved as
`W0/bayes_fit003_attempt1_oversubscribed/`, including its completed run 0
particles. fit003 is re-executed with identical code, budget and seeds, with
`OMP_NUM_THREADS=VECLIB_MAXIMUM_THREADS=OPENBLAS_NUM_THREADS=1` and unbuffered
logging. This is not a results-driven retry. The gates are unchanged.
