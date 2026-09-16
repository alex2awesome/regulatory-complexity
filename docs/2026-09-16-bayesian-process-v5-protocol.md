# Bayesian low-data continuation: v5 development protocol

2026-09-16, after the v4 reserved result was opened. W1, including J2/S07, is now
development data. The v4 negative comparison is immutable. This continuation has
not achieved the active goal merely by improving diagnostics or documenting failure.

## Ordered experiments

1. Fit a smaller Bayesian **measurement model for whole-process durations**.
   Whole-case reports need not be reconstructed by summing overlapping stage spans.
   Preserve the successful agency/task hierarchy as a separate component; do not
   substitute elapsed days for labor or silently claim that counts are solved.
2. Compare the same model with and without an explicit delay-dependent reporting
   mechanism. Forum cases are a selected sample; the selection mechanism's strength
   is uncertain, not chosen to make one benchmark answer correct. Include prior
   sensitivity and generated-data recovery for the selection likelihood.
3. Based on these development diagnostics, simplify further or add an event/visit
   representation where necessary. Only after the Bayesian candidates have been
   tested should a direct-LLM/probabilistic hybrid become the primary alternative.

The source-only measurement audit supplies machine-readable duration basis,
first-versus-repeated submission boundaries, endpoint/completion status, censoring,
and source/summary type. It cannot alter reported amounts or see scores, predictions,
gold, or generator specifications. Free-text recognition of an ongoing case is not
enough: the statistical likelihood must use that status.

## Scope and evaluation discipline

The primary timing target remains population median elapsed calendar time from
beginning applicant preparation/filing to initial decision. P90, agency timing,
distinct operations, repeat visits, agencies and separate payer/staff hours remain
in scope; a successful timing experiment is not a completed full-burden model.

Use the three previously studied W1 programs for development. Report every tested
variant rather than picking isolated favorable program results. The next evaluation
must use a **new generated world**, with a frozen candidate, public-input selection,
sample size, baseline prompt and scoring protocol before its outcome files are read.
The existing W1 corpus cannot become held out again. Rendering must preserve its
specification's actors, observation clocks and censoring; verification may reject a
rendering, but may not feed hidden facts to extraction or inference.

Compare fresh direct LLM estimates on the identical evidence representation and
program grouping. Primary timing acceptance requires no worse mean absolute log
error than the LLM control and no worse proper 90% log-interval score, with individual
program failures, repeat variation, Monte Carlo uncertainty and sampling uncertainty
visible. Also score operation/agency counts and report lack of labor evidence; do
not redefine the overall goal as one convenient timing score.

Continue to use four independent chains, R-hat <= 1.01, bulk ESS >= 400 and tail ESS
>= 200. Extend for computation only. Preserve data, prompts, source snapshots,
configuration, seeds and unsuccessful runs. No score-driven editing of a reserved
set's claims, clocks, prior or model is allowed.

Codex source interpretation stays pinned to `gpt-6-astra` with explicit reasoning,
strict output schemas, isolated read-only working directories and saved outputs.
This follows the [official non-interactive interface](https://learn.chatgpt.com/docs/non-interactive-mode)
and [model guidance](https://developers.openai.com/api/docs/guides/latest-model);
no model upgrade or estimated benchmark answer is part of the semantic audit.

## Subsequent development discovery: legacy clock mismatch

The read-only benchmark audit found that repeated decisions overwrite the simulator's
`decision_end`, so the legacy log-summary median is time to the last recorded
decision, while the inference/baseline prompts requested the first. The S01
dashboard's rendered clock and denominator also disagree with its generated
statistic. Preserve all existing data, comparisons and negative findings. Do not
relabel the original scores as a new success on a retrospectively changed target.

Before a fresh reserved evaluation, explicitly distinguish first decision, last
decision and closeout, their censoring rules, and their population denominators.
Freeze which quantity is primary and report the other supported burden quantities.
The legacy W1 scores remain development diagnostics, not a valid certificate of
equal-estimand accuracy or a reason to abandon the Bayesian hierarchy.

## Partial-preparation experiment, specified before fitting

2026-09-16, following the outcome-aware development comparison. The new source-only
preparation audits are fixed and quote-checked. The model uses 16 / 4 / 9 individual
pre-filing spans in S01 / S03 / S07. Four S01 groups retain at least two explicitly
disjoint spans. It neither reinterprets unknown application/rework clocks as
preparation nor sums unsupported overlaps.

For a case duration `D` and program preparation fraction `f`, preparation is `P=fD`.
An isolated partial report observes `uP`, `u~Beta(1,1)`. An explicitly disjoint group
of `k` spans has a `Dirichlet(1,...,1)` budget over those `k` spans **and an unobserved
remainder**. A narrated starting-action-to-filing clock does not establish absence
of earlier preparation. An explicitly observed process-start-to-first-filing span
instead observes `P` itself. Non-grouped partial spans can overlap; this is not a
new schedule or an assertion of parallel work. Service/visit microdurations are
left to their separate task channel rather than assigned an exchangeable generic
fraction of weeks of preparation.

The population model, outcome model, original preparation-fraction prior, selection
prior, contamination and source offsets stay unchanged. The new partial-span
reporting scale is 0.35 log days, with the same robust Student-t observation family.
Coverage concentration parameters are both 1. Primary development variants have
delay-selection scale 0 and 1.5, respectively. Four chains start at 1,500 warmup and
6,000 retained draws, quadrature 512; numerical extensions/refinements may change
computation only. Native/reference likelihood, shared-case integration, budget
normalization and source/location Gibbs invariance have dedicated tests.

Fresh three-repeat LLM controls get the identical twelve input files (three ledgers
and three of each audit type). Existing controls cannot be substituted. This remains
a **development** experiment with a known legacy-clock mismatch. It is not full
calibration or an agency/task hierarchy replacement. The shared preparation fraction
and coverage prior are consequential simplifications to examine, not empirical facts.

## Case-varying preparation sensitivity, specified before fitting

2026-09-16, after inspecting the no-selection partial-preparation result and its
robust-component conflict diagnostics. These are development sensitivity tests,
not candidates selected using a reserved set. Public inputs and the matched
twelve-file LLM control stay fixed. The new count audit is **not** supplied to
these timing fits or secretly used as extra evidence.

Run two no-delay-selection variants with case preparation logit SD 0 and 1.
For case `c`, `logit(f_c)=eta_p+s*z_c`, with independent standard-normal `z_c`;
the program location `eta_p` retains its original prior. A person's total and
partial clocks share the same `f_c`. Conditional independence of fraction and
total duration is still an assumption, but proportional preparation time is no
longer forced in the SD-1 variant.

Both variants use a segmentation-invariant coverage prior: total reported
coverage `C~Beta(1,1)` and, conditional on `C`, a `Dirichlet(1,...,1)` partition
among the explicitly disjoint spans. A singleton is unchanged; adding a finer
description does not itself push total coverage toward 1. Source-supported full
preparation clocks still observe the full preparation duration.

Population first-filing/complete-filing summaries use the convolution of the
fraction distribution with the outcome-specific duration distributions. They
do not multiply population medians. Approximate sampling errors now use the
appropriate mean or quantile functional rather than using the median formula
for every summary. The SD-0 comparator shares these changes, isolating the
case-variation assumption within this new pair.

Use four independent chains, 1,500 warmup and 6,000 retained draws each, 1,024
case-duration quadrature nodes and 64 fraction nodes. Check against doubled
resolution in **both** integrals. Existing convergence/precision thresholds and
priors otherwise stay fixed. Save both results, including failures; extend/refine
computation as necessary without selecting settings by their legacy score.

## Joint repeat/timing propagation check, specified before generation

This controlled component experiment tests the proposed connection between
rework claims and agency/task timing, not end-to-end extraction or a new W1 win.
Use eight paired replicates with true agency/task first-visit median 7 days,
known log SD 0.45, any-correction probability 0.6 and known continuation
probability 0.35. Additional rounds have hurdle-geometric probabilities
`P(R=0)=1-q`, `P(R=k)=q*(1-r)*r^(k-1)` for `k>=1`. All visits to this task in one
case share a duration `X`, an explicit simplifying correlation assumption.
Whole-case timing is `T=8+(1+R)*X`; three other fixed-duration operations make
the realized visit count `4+R`. These fixed/known components are favorable
assumptions, not facts inferred from text.

Compare 10 whole-case times alone, those same times plus a separately sampled
20-case actual rework cohort, those same times plus 5 independent first-visit
agency/task times, and a nested 100-whole-case-time sample alone. An informal
frequency is not an actual counted cohort; no existing FAQ is assigned an n.
The shared log task-median prior is `N(log(5),1.5^2)` and `q` is uniform. No LLM
baseline is involved and no new reserved world is generated or read.

Fit their joint posterior by numerical grids, beginning with 801 location and
201 probability nodes, checking against doubled cell resolution and twice as
many repeat-count terms. Preserve the unnormalized omitted repeat tail, which
must be below 1e-12; never silently impose a maximum retry count. Maximum marginal
CDF discrepancy must be below 0.005; refine for computation only when needed.
Report agency mean cycle time, expected visit count and population timing, with
point error, proper log-interval score and empirical coverage. Eight replicates,
one truth setting and known noise/route parameters do not establish calibration.
