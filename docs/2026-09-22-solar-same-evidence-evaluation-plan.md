# Solar: how to test whether Bayesian aggregation beats an LLM

September 22, 2026. Proposed real-data evaluation protocol, not a completed
experiment or a retrospectively preregistered result.

**The necessary demonstration is better prediction of evidence neither method
has seen, using the same training information and the same requested output.**
Fitting the supplied numbers, obtaining narrow posterior intervals, or agreeing
with another LLM is not that demonstration. More forum downloads alone do not
establish it. This experiment can start on a bounded frozen subset while the
[bulk download and reading](2026-09-22-solar-download-and-reading-handoff.md) continues.

## 1. Claims we can and cannot test on real data

| Target | Independent evaluation target | What a win establishes |
|---|---|---|
| Permit/application or inspection/PTO elapsed time | Held-out dated case outcomes or administrative phase records, with matching endpoints | Better prediction of that observed clock in the stated sample |
| Jurisdiction phase summaries | Held-out administrative summaries with the same phase, year and population definition | Better prediction of the reported summary, not automatically of every resident's experience |
| Available actions/steps | Held-out explicit presence/absence answers or an independently reviewed complete instrument for that AHJ and era | Better calibrated process-availability probabilities |
| Number of steps | Complete action inventories, or complete applicant journeys, depending on the declared count | Recovery of that defined inventory or executed journey count |
| Intrinsic agency capability | No directly observed gold label currently established | Not validated just because timing prediction improves |

County is not the same as the permitting authority. City building departments,
county departments, utilities and installers must not share an invented agency
identity. Separate observed agency-associated speed from an intrinsic capability
claim requiring case-mix, workload, selection and other identification assumptions.

Step availability is not case participation or visit count. Sparse narratives
provide positive examples, not complete inventories. Do not score an unmentioned
step as absent, or a missing step duration as zero. An official published deadline
is not ground truth for experienced elapsed time.

## 2. Two comparisons, answering different questions

### A. Aggregation comparison — do first

Give both systems the **identical canonical evidence packet**, including quotes,
numeric claims, source types, units, clock alternatives, geography candidates,
case links, guide facts, and the same source-derived crosswalk/step vocabulary.
The Bayesian estimator compiles/fits it. The LLM directly estimates the requested
quantities from it. Neither gets test answers, model results, synthetic truth,
or extra live lookup. Any trained source-calibration data must be available to
both or declared as an intentionally separate experimental condition.

This isolates statistical aggregation from extraction differences. If a compiler
drops a useful whole-process sentence, record the loss; do not remove that
sentence from the LLM's shared evidence to make the comparison easier.

### B. End-to-end comparison — after A

Give both pipelines the same raw source set, cutoff and resource policy. One
extracts and fits; the other reads and estimates using a declared batching /
retrieval strategy. For inputs exceeding context, use the same source selection
or shared source-only summaries and report that compression. Do not compare
Bayesian use of the full corpus against an LLM handed one truncated page.

Report A and B separately: winning A would not prove our extraction pipeline
beats an end-to-end LLM. A competent LLM with tools can be an additional baseline,
but label its different compute policy rather than quietly changing conditions.

## 3. Freeze a small first experiment; reserve a genuinely new test

Codex owns the estimator and scorer; Claude can own source-only test labeling.
The already inspected Solar data supports an **exploratory** comparison now.
It cannot become an untouched confirmatory test merely by calling a reused
split “held out.” Reserve a new acquisition tranche before substantive model
development on it, or a genuinely future outcome window, for confirmation.

For the first exploratory run:

1. Inventory usable independent case groups and administrative cells, by clock,
   AHJ/utility, era, source type, censoring and geography. Choose targets by
   supported endpoint coverage, not which makes a model look good.
2. Freeze input hashes, inclusion rules, exact train/test IDs, estimands, priors,
   scorer, numerical gates, baseline prompt and model version before scoring.
   Save under a new `runs/solar_evaluation_20260922/experiment001/`; this directory
   is a planned deliverable, not an existing completed experiment.
3. Group all posts/updates about one installation together. Group crossposts,
   copied documents, repeated utility cells and overlapping cohort summaries.
   No case appears in both sides through a different username/thread/summary.
4. Use a reproducible approximately 20% grouped case holdout for the first clock
   task. If it yields fewer than about 30 independent evaluable cases, call it
   a pilot and report the low precision; do not manufacture extra cases from
   multiple intervals. Thirty is a planning floor, not a power calculation.
5. Add authority-held-out and genuinely forward-in-time evaluations as distinct
   tests of pooling and updating. Training on later years makes a missing-year
   test interpolation, not forecasting. These tests need not all be completed
   before the first exploratory result.

Two case tasks are legitimate but must not be conflated:

- **New-case prediction:** no narrative/outcome from the held-out installation
  enters training; both receive the same allowed contextual covariates.
- **Pending-case forecast:** both see an explicitly frozen earlier snapshot;
  later updates, quotations, thread titles/edits and descendants revealing the
  outcome are removed. Score the actual later result. Record that follow-up
  may be selected; this is not a random California cohort.

Hide test outcomes in an evaluator-owned file. Baseline execution should receive
only an allowlisted packet in an isolated work directory, no repository browsing
or network tools. Merely writing “do not read truth” in a prompt is not a technical
barrier when the runner has full filesystem access. Source readers may extract
labels, but their outcome notes and test-dependent schemas must not enter fitting.

Refit the Bayesian model on training data only; current all-data fits are not
eligible test predictions. Remove anchors and any logically redundant evidence
that reveal held-out answers. Do not use a predictive distribution conditional
on the same held-out case latent that was fitted to its outcome.

## 4. Baselines and matching outputs

Use three levels, all trained/given information from the same split:

1. A simple pooled/stratified empirical baseline with predictive uncertainty,
   appropriate to the clock and censoring. Include the direct whole-process
   sentence estimator where such a training-source statement exists. Do not
   extract that sentence from the held-out answer itself.
2. The repeated same-evidence LLM baseline: five independent runs with frozen
   prompt/model/settings, all saved and all reported. Do not pick the best
   answer. Run order variation is a separately reported sensitivity, not a way
   to tune on test outcomes.
3. The Bayesian model, with frozen scientific assumptions and ordinary numerical
   diagnostics. A failed fit is reported as failed, not silently replaced by a
   successful seed or a relaxed threshold.

For individual elapsed outcomes, require both methods to produce median and
central 50%/90% **posterior predictive** intervals, in the same time unit and with
the same start/end events. Those include case variability. A credible interval
for the population median is a different object and cannot be scored as a
case interval. For a reported administrative cell median, predict that reported
statistic instead, including its measurement uncertainty. Do not invent its
sample size from an installation count or number of jurisdictions.

For structure, require probabilities for the same frozen actor/action registry
and a count distribution for the same defined inventory. Report novel actions
separately rather than marking everything outside the vocabulary nonexistent.
No available gold labels means “not evaluated,” not a win by assertion.

Existing code to reuse rather than create another framework:

- `pipeline/procbench/evidence_baseline.py`: repeated identical-evidence baseline
  and receipts. **Its current prompt targets initial permit decision and its
  intervals describe the population median. It cannot be used unchanged for
  Solar PTO or case-predictive scoring.** Its input contract also needs an
  explicit adapter to these Solar packets.
- `pipeline/procbench/infra/scoring.py`: common proper interval scores.
- `pipeline/procbench/solar_panel/score_county_timing.py`: administrative clock
  holdout machinery and distinction between interpolation and forward tests.
- `pipeline/procbench/solar_panel/score_and_offset.py`: earlier panel baselines;
  not proof that the new forum/journey model beat an LLM.

Do not rebrand old panel or structure results as this new matched experiment.
Preserve earlier scores, losses and failed fits alongside the successor.

## 5. Scoring and the decision rule

For the first exact completed-clock task, preregister mean **90% interval score
in calendar days** as primary, lower better. It penalizes both unnecessarily wide
intervals and missed outcomes. Report 50%/90% coverage, widths and absolute error
alongside it. Use log-day scores as a labeled secondary sensitivity only on
positive durations; do not choose the winning scale after seeing results. Define
same-day resolution before scoring; no arbitrary zero-to-positive replacement.

For interval-reported or censored test outcomes, use a common outcome-event
probability scoring contract (interval mass or survival probability), or keep
them as a separately labeled task until both predictors support it. Never
replace “still waiting at day 60” with a completed duration of 60. An exact-only
primary score is conditional on having an exact completion report and cannot
support an all-applicant claim. Do not discard pending cases from training just
because the initial scoring contract is narrower.

For independently labeled step presence, report Brier score, calibration and
performance relative to a step-specific pooled prior; counts use an appropriate
predictive score only where a complete count is known. Do not average days and
step probabilities into a post-hoc omnibus “win.” Predeclare one primary timing
endpoint and report other clocks/structure as separate secondary targets.

Pair scores by held-out unit. For a county/generalization claim, estimate
uncertainty with AHJ/county-cluster resampling, not a bootstrap that treats
hundreds of clocks from a handful of people as independent. Include between-LLM-
run variability. With too few independent clusters, report that the comparison
is underpowered rather than a falsely precise confidence interval.

Proposed confirmatory win rule, to be frozen before outcomes:

- Bayesian primary-score loss is at least 5% lower than the repeated-LLM mean;
- a paired 95% uncertainty interval for the improvement excludes zero;
- it also beats the simple baseline on the primary score;
- nominal interval coverage is compatible with its stated level at the available
  sample size, with no hidden abstention or outcome-specific missingness advantage.

The 5% threshold is an explicit practical design choice, not a discovered law.
Record all requested predictions and abstentions. Use one predeclared fallback
for missing predictions for both methods, and also report common-subset scores
plus prediction coverage. Invalid JSON or failed fitting must not simply remove
difficult cases from one method's denominator. No threshold changes after results.

A result whose improvement interval overlaps zero is **inconclusive**, not proof
of equivalence. Evidence of equivalence would require a separate prespecified
equivalence margin and sufficient independent test data. Lower run-to-run
variance alone is reproducibility, not predictive superiority.

## 6. Test the actual heterogeneous-evidence hypothesis

After the first comparison, run a small fixed ablation on the same splits:

| Evidence/assumption condition | Purpose |
|---|---|
| Administrative only | Establish what the best measured phase data already explains |
| Forum only | Measure what selected applicant reports predict on their own |
| Both, common source model | Measure gain from adding evidence without learned source corrections |
| Both, source hierarchy and declared selection sensitivity | Test whether the extra machinery helps held-out prediction |

Give the LLM the corresponding evidence in each comparison. Add training-only
learning curves at fixed evidence budgets to test whether pooling helps more
when evidence is sparse or heterogeneous. Do not search many variants on the
final test; select variants on training/development data and evaluate once.

Predicting held-out forums well could mean predicting forum selection well.
Improved independent administrative prediction after adding forums is stronger
evidence that combining sources helps. Neither identifies intrinsic agency
delay unless endpoint alignment, case mix and source/selection confounding are
addressed. Real held-out results test practical prediction; a later small known-
truth synthetic stress test can diagnose latent recovery, but is not a dependency
for this real-data-first evaluation.

## 7. Deliverable and stopping point

Codex delivers one frozen experiment manifest, train/test packet hashes, all raw
LLM answers, Bayesian diagnostics, per-unit predictions and scores, paired score
differences, coverage/calibration and a short limitations table. Claude's source-
only label receipts remain separate. The first result must say one of: **win,
loss, inconclusive, or test not estimable with this evidence**.

If Bayesian and LLM predictions are similar, the Bayesian system may still offer
useful persistent uncertainty, auditable updates, coherent pooling and explicit
assumptions. Those are distinct contributions; we should not claim superior
accuracy without this comparison. Conversely, a failed simple baseline comparison
is a reason to fix the evidence/compiler/estimand mismatch before adding another
layer of latent parameters.
