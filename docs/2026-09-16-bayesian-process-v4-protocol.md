# v4 evaluation protocol, frozen before reserved-program evaluation

Written 2026-09-16 before fitting/scoring reserved J2/S07. Development programs
are J1/S03 (previous gold and failure already known) and J1/S01 (additional public
evidence). Reserved J2/S07 gold and old solver outputs are not provided to the
extractor, interpreter, Bayesian inference, or matched-evidence LLM baseline.

## Inputs and estimand

Use the quote-validated `process-evidence/2` first-pass ledgers in
`runs/bayes_v4/extraction/*_first_validated/`, followed by the same source-only
operational-granularity audit for all three programs. Audits cannot see scores,
benchmark counts, hidden timing parameters, or previous estimates. Keep both
interpretations and their complete mappings; do not choose granularity by F1.

Primary elapsed-time target: population median calendar days from beginning
preparation/filing to initial decision. Submission-to-decision and core-closeout
are separate estimates. Gold log summaries approximate this population target
with simulated case samples. Hours are a separate likelihood; do not convert
waiting to work. Count comparisons are conditional on semantic granularity and
are not a substitute for checking operation identity.

## Fitting and checks

- Defaults in `bayes_hierarchy.Config`: broad log-day location prior centered
  at seven days, inferred agency/task/residual scales, source offset SD 0.35,
  explicit contaminated interval likelihood, hidden-stage geometric mean 2
  truncated at 8, and finite schedule-completion uncertainty.
- Four chains, initially 2,500 warmup and 12,000 retained draws each. Extend runs
  for computational diagnostics, not to move an answer toward a gold outcome.
- Rank-normalized split/folded R-hat ≤ 1.01, bulk ESS ≥ 400, tail ESS ≥ 200.
  Report failures; do not erase unsuccessful runs.
- Cross-program fit of J1/S01 and J1/S03 tests shared-organization propagation.
  Fit J2/S07 separately. No cross-jurisdiction organization alias merging.
- Controlled generated data: known fast/slow agencies with held-out task durations;
  compare agency/task pooling with a global-only hierarchy. Computational SBC is
  a limited pilot, not a real-world calibration certificate.
- Sensitivity: global prior centers 3.5/7/14 days; hidden-stage means 0/1/2/4;
  source-offset SD 0.35/0.7; Sobol size/seed; new chain seed; removal of segment
  and total duration observations. Importance reweighting is acceptable only
  with reported effective sample size and a clear distinction from a refit.

## Comparisons and scores

Save draws, manifests, and posterior summaries before reading benchmark truth.
Report explicit process-median absolute log error and 90% interval coverage;
also log-median CRPS and interval score (wide intervals are not free). Show
legacy granularity-tolerant and one-to-one-backbone activity F1, raw count error,
and alignment caveats. Lexical matching is not semantic ground truth.

The matched LLM's elicited 90% interval can receive the same log-interval score,
including its width penalty, without inventing a full predictive distribution.
No CRPS is assigned to an LLM answer lacking that distribution. An elicited
interval is not presumed calibrated merely because it was labeled 90%.

Run three fresh, pinned-model LLM point estimations on the identical canonical
evidence, without Bayesian outputs or gold answers. Compare their variation
with fresh-chain variation, distinguishing interpretation uncertainty from
Monte Carlo uncertainty. The historical 55-day J1/S03 baseline remains a useful
reference, but changed extraction/model/information preclude a clean causal claim
that Bayes alone improved it.

Do not select priors or interpretations because they improve the reserved score.
If a reserved result reveals a defect, report it as a failure; a later correction
requires a newly reserved evaluation before claiming generalization.

## Pre-evaluation amendment: observation contexts

Recorded 2026-09-16, before opening J2/S07 truth or previous solver answers.
Source-only inspection found three semantic defects: an explicitly historical
claim entered the current-process likelihood; selected clean/upfront-certification
cohorts were treated as unconditional; an enforcement segment outside the initial
route was assigned zero duration. These were discovered in the public quotations,
not from reserved scores. Preserve the context-naive fits as diagnostic artifacts.

Apply the same quote-validated, strongest-model context audit to all three programs.
The backward-compatible `process-evidence/3` extension records period, required
and excluded operations, explicit terminal outcome, and executed-segment versus
alternative-branch semantics. Historical/hypothetical reports remain in the ledger
but do not fit a static current process. Same-case constraints are shared and
contradictions fail validation. Executed-segment timing conditions on execution,
including post-initial work; selected-route claims do not estimate population
route frequencies. Unknown outcome proportions remain an explicit limitation.

Refit the amended likelihood from scratch; do not append to context-naive draws.
Keep all existing priors, targets, convergence rules, and reserved-evaluation
separation. Repeat the matched LLM control on these exact amended ledgers. Frozen
manifests retain source and evidence hashes. Source-only corrections are not a
license to tune after reading reserved truth.

The same pre-evaluation audit also found a segment boundary that included signoff
work in a clock explicitly starting *after* signoff. A second narrow, source-only
audit supplies optional `clock_start_after_activity_ids`; the schedule subtracts
the supported milestone, not a guessed duration. All three programs receive this
audit. Final amended input ledgers are in `runs/bayes_v4/clocks/<program>/`.

Supplementary burden evaluation (added before reserved truth is opened) compares
posterior expected distinct operations, represented agency operations, and agencies
against uncensored decided log cases through the decision endpoint. It also reports
population-p90 error/interval coverage. This is secondary to the frozen median
comparison and retains ontology/actor-identity caveats. Repeated visits are reported
as a separate truth quantity, not incorrectly treated as distinct operations.

Final pre-evaluation uncertainty correction: unknown terminal-outcome proportions
are themselves uncertain (exchangeable logistic-Normal, binary logit SD 1.5), not
a known 50/50 population mix. Known case/cohort outcomes still condition the
likelihood without treating selected anecdotes as representative frequencies.
Only J2/S07 has multiple retained terminal decisions among these three ledgers.
Preserve its fixed-mix fit as a sensitivity control and refit with the uncertain
mix, using the same evidence and all other priors. No reserved truth has been read.

A final public-metadata audit found an implementation collision in cross-program
actor keys: separate, unresolved "City of Halvern" actors acquired the same effect
through identical display names, despite not passing the distinctive-alias merge.
Keep those registry roots separate and refit the joint development model. Retain
the earlier joint fit as a coarse-municipality pooling control. Actual department
sharing still requires supported distinctive aliases. This changes the joint
development model, not either single-program statistical target or the reserved
evidence. It was diagnosed before reserved gold was opened, not from scores.

Before opening reserved truth, check importance sensitivity of its uncertain
outcome proportions to logit SD 0.75 and 3 (default 1.5), with the same overlap
diagnostics. The already fitted fixed-equal-mixture model is a separate sensitivity
control; it cannot be obtained by ordinary continuous-prior reweighting. These
checks do not select a prior according to the reserved score.

The completed primary reserved fit passes all monitored diagnostics. Its broader
source-SD 0.7 and outcome-logit-SD 3 importance checks fail the preset overlap
criteria (raw ESS 82 and 1,309; maximum weights 8.1% and 1.54%). Before opening
reserved gold, run those two controls as full four-chain refits, retaining the
original priors as the primary model. This is a numerical sensitivity follow-up,
not selection among answers according to benchmark performance.

## Reserved-evaluation gate

2026-09-16 13:33 UTC, before the first J2/S07 gold read: the primary uncertain-
outcome fit and both full sensitivity refits are complete, saved, hash-checked,
and pass every monitored elapsed diagnostic. No continuation is required. Primary
source SD 0.35 / outcome-logit SD 1.5 remains the designated model; broader source
SD 0.7 and outcome-logit SD 3 remain controls, not candidates selected by score.
Primary completion: 12:59:54 UTC; sensitivity completions: 13:33:07 and 13:33:10 UTC.
Evaluation will record its own start/completion timestamps and posterior hash.

The post-fit development claim audit also exposes the appointment-service versus
appointment-access clock mismatch in S01. It is documented as a remaining defect;
no ledger, model target or prior is changed to improve this frozen comparison.
A subsequent correction must be evaluated on a newly reserved set.
