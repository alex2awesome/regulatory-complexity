# CalFresh: application to first observed decision

The current successor consumes **26 reported cases**, including 13 pending at
their historical observation date. All five declared fits are terminal; four
pass numerical checks and the main mixed fit **fails**. This expands actual
forum consumption but does not close the CalFresh study or its joint burden
model. These are selected reports, not a representative applicant cohort.

## Current 26-case successor

The [source-reviewed input](../runs/three_family_20260920/calfresh_application_decision_remaining_candidates_v1/README_effective_v2_26.md)
preserves the original 17 claims and all five configurations. Nine additional
histories add observed approvals/denials and historical pending observations;
13 completed histories comprise ten finite intervals and three completed lower
bounds. The 24-case intermediate draft was not fitted.

| Declared condition | Completed / pending | Numerical gate | Model median in days, 90% posterior interval |
|---|---:|---|---:|
| Completed reports only | 13 / 0 | PASS | 12.94 (4.54–32.72) |
| Completed plus pending | 13 / 13 | **FAIL** | Not released as a headline estimate |
| Same mixed cases, wider report noise | 13 / 13 | PASS | 48.96 (27.72–89.92) |
| Same mixed cases, 7-day location-prior median | 13 / 13 | PASS | 47.15 (24.73–87.56) |
| Same mixed cases, broader lexical interval | 13 / 13 | PASS | 45.32 (23.45–92.77) |

The main mixed spread coordinate has R-hat 1.010483865 against the fixed 1.01
gate (bulk ESS 520.43, tail ESS 1,097.95). Its raw summaries remain available
for diagnosis, not replaced by a passing sensitivity or the smaller old fit.
No automatic extension or relaxed gate is authorized by this experiment.
All five likelihood replays are exact; quadrature refinement and independent
case-integration checks pass. Root replayed 26 generic analysis bindings and
69 closeout bindings, including its builder.

A separate [deterministic same-target reference](../runs/three_family_20260920/calfresh_application_decision26_deterministic_reference_v1/README.md)
is also **unresolved**, not a replacement pass. Its frozen 129/257-point grids
used 66,049 likelihood evaluations in 14.53 seconds. Normalizer, median and
boundary-mass checks passed, but duration tail quantiles changed 1.47%/1.49%
against a prespecified 0.5% gate. The permitted domain expansion was not
triggered; execution stopped under the declared rule, below the maximum budget.
The original MCMC failure and all evidence/prior choices remain unchanged.

The [qualified numerical closeout](../runs/three_family_20260920/calfresh_application_decision_fullscope26_closeout_v1/README.md)
links the [main results](../runs/three_family_20260920/calfresh_application_decision_fullscope26_marginal_v1/analysis_v1/README.md),
[lexical result](../runs/three_family_20260920/calfresh_application_decision_fullscope26_lexical_marginal_v1/analysis_v1/README.md)
and [replacement consumption delta](../runs/three_family_20260920/calfresh_application_decision_fullscope26_closeout_v1/source_use_delta.json).
This replaces the old 17-case component; it does not add another five conditions.
At this checkpoint seven components consume 113 records across 28 conditions
(27 numerically usable), with 409 condition-by-factor executions, 95 exact case
IDs and 105 canonical registry references. These are not verified people counts.

Data-only bounds on the finite-record median are [10.5,34] days for completed
reports and [19,infinity) for the mixed frame; the lexical variant gives
[15.5,infinity). They are not posterior intervals. Selection, eventual decision
observation and reporting-error assumptions remain substantive limitations.

Two source-use details matter: 1onlkmu uses its actual interview timing plus a
later observed denial, not the worker's ten-day prediction; 1vffjyx reuses the
already-declared preceding-Sunday coarsening, not a newly verified exact date.
The nine additions close only this clock use, not dependent downstream uses.

## Historical 17-case experiment

The sections below preserve the original experiment, where all five conditions
passed. Its estimates and counts apply to those 17 inputs only and are not the
current 26-case base estimate.

## Inputs and the correction made before fitting

The target is reported application submission to the claimant's first observed
eligibility approval **or denial**. Submission is not certified administrative
completeness; later document requests do not reset the clock. Internal decisions,
interview, final successful approval, card possession and benefit availability
are distinct events.

The [protocol](scoping/2026-09-20-calfresh-application-decision-protocol.md),
[additive input correction](../runs/three_family_20260920/calfresh_application_decision_input_erratum_v1/README.md)
and [root adoption](../runs/three_family_20260920/calfresh_application_decision_input_erratum_v1/root_adoption.md)
were fixed before sampling. Root caught one material endpoint error: the
San Diego history `1922mjh` had an earlier denial, so its later December approval
could not be the first-decision endpoint. The effective interval is conservatively
completed-by [0,52] days, not the erroneous [61,69]. No case was discarded. The
earlier sealed input is preserved but was never fitted.

One "almost three months" report uses the declared lexical interval [56,93]
days in the original four conditions. A fifth pre-fit sensitivity broadens it to
[0,93]. This acknowledges uncertain wording without inventing a calibrated
mixture probability. All other observations and priors stay unchanged between
that sensitivity and the mixed base.

## Results

Each fit uses four chains, 1,000 warmup and 2,000 retained draws per chain.
The existing V6 marginal-case path integrates independent case effects, leaving
location and spread coordinates; no new process model is introduced. No retries,
extensions, gate changes or best-condition selection were used.

| Declared condition | Completed / pending | Model median in days, 90% posterior interval |
|---|---:|---:|
| Completed reports only | 7 / 0 | 11.95 (3.80–34.10) |
| Completed plus pending | 7 / 10 | 54.15 (30.29–96.94) |
| Same mixed cases, wider report noise | 7 / 10 | 54.52 (29.62–100.02) |
| Same mixed cases, 7-day rather than 30-day location-prior median | 7 / 10 | 52.18 (27.93–92.84) |
| Same mixed cases, broader lexical interval | 7 / 10 | 49.90 (25.53–95.14) |

The [four primary results](../runs/three_family_20260920/calfresh_application_decision_marginal_v1/analysis_v1/README.md)
and [lexical sensitivity](../runs/three_family_20260920/calfresh_application_decision_lexical_marginal_v1/analysis_v1/README.md)
retain exact fitted-factor/source links. Root replayed their 26 analysis bindings.
Saved likelihood replay differences are zero. Across five fits, maximum R-hat
is 1.00694, minimum bulk ESS 887 and minimum tail ESS 1,260. Checked quadrature
refinement and independent integration differences are below 1.1e-8. Fit-manifest
times are 6.1–11.6 seconds; these are measured runtimes, not general forecasts.

## What the data support

Completed-only analysis omits most histories in this selected frame. Including
those still waiting materially changes the inferred distribution. This is a
frame/censoring sensitivity, **not an estimated correction for forum selection**.
The report-noise and location-prior sensitivities leave similar central values;
the lexical sensitivity moves the median by about four days. None tests all
possible reporting, censoring or selection models.

Assuming the compiled intervals literally contain the reported durations, the
finite-record median lies in [1,34] days for the seven completed histories and
[25,infinity) for all 17. The lexical sensitivity gives [24,infinity). These
are descriptive bounds, not posterior or confidence intervals. The finite upper
posterior bounds above come from distributional/reporting assumptions, not a
finite data-only upper bound. A proper finite-duration model also assumes that
pending claimants eventually observe a decision; the sources do not establish it.

Location uncertainty contracts substantially, but spread is weakly constrained:
its whitened posterior variance exceeds its prior variance in all four mixed
conditions. Do not turn numerical convergence into a claim that the whole
distribution, source trust, agency delay or posting mechanism is identified.
The reports can share thread context and overlap other components. Adding clock
medians or counting condition executions as people would be incorrect.

## Source-use accounting and next integration

The [effective delta over source-use v5](../runs/three_family_20260920/calfresh_application_decision_closeout_v1/source_use_delta.json)
links all 17 newly fitted clock uses to canonical claims. Seven separate clock
families now consume **104 component records** in **28 conditions**, corresponding
to 367 condition-by-factor executions, 92 exact case IDs and 101 claim references.
None of these is an independently verified count of people. Only this clock use
closes; other uses of the same claims remain explicitly open.

Remaining work is shared-case/event inference, defensible actor uncertainty,
supported additional clocks and counts, heterogeneous-source treatment, adequacy
and comparisons. Administrative and forum components are not yet one joint
burden posterior. Other real families and synthetic construction remain deferred
under the user's CalFresh-first priority, not removed from the overall goal.
