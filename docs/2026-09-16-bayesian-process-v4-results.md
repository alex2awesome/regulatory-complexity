# Bayesian v4: experiments, diagnostics, and remaining limits

**Extraction-lineage correction:** these results and their matched controls use
the imported first-response branch, accepted after validator changes, not the
repaired second responses. The earlier methods commands named the wrong path.
See the [corrected methods](2026-09-16-bayesian-process-v4.md#running) and
[hash-checked retrospective audit](../runs/bayes_v6/audit_updates/extraction_lineage/lineage.json).
The original rejection messages and both branches are preserved. No posterior or
score has been regenerated or relabeled.

**Later clock erratum (v5 development):** the frozen numerical results below are
unchanged, but their "initial decision" description of the legacy gold clock was
incorrect for repeat-decision cases. The simulator's `elapsed_days` uses the last
recorded decision; the model and LLM prompts requested the first. A separate
[clock/cohort audit](../runs/bayes_v5/validation/benchmark_clocks/audit.json) finds
first/last same-cohort medians of 111/128 days for S01, 74/74 for S03, and 17/21
for S07. The S01 dashboard also introduced an unsupported acceptance-to-closeout
definition and a mismatched sample denominator. These findings qualify the
comparison, do not rewrite its scores, and do not establish Bayesian superiority.
See the [v5 benchmark-contract discussion](2026-09-16-bayesian-process-v5.md#benchmark-contract-defect-found-during-development).

2026-09-16. This records the continuing Bayesian implementation, not a switch to
a direct LLM estimator. The [model](2026-09-16-bayesian-process-v4.md),
[frozen evaluation protocol](2026-09-16-bayesian-process-v4-protocol.md), and
[TikZ diagram/glossary](figures/latex_plate_diagram_simplified/README.md) describe
the implementation and the broader target separately. Earlier failed and
unconverged runs remain under `runs/bayes_v4/`.

**Completed milestone, not a validated full-burden estimator.** All primary elapsed
fits, both reserved prior-sensitivity refits, and the stricter agency-transfer
controls pass their monitored numerical diagnostics. The reserved evaluation is
nevertheless a clear failure: **39 days versus 21 in the simulated log**, with the
90% interval missing. The matched LLM gives 28 days. No model, prior, or evidence
was changed after seeing the reserved answer. Step/agency counts also remain poor.

## Final-input comparison

The two J1 programs are fitted jointly; J2/S07 is fitted separately. Each grouping
uses exactly the ledgers supplied to its direct LLM controls. All monitored elapsed
diagnostics pass. The intervals below describe
uncertainty about a population median, not the range of individual case durations.

| Program | Simulated median, days | Bayesian median (90% interval) | Direct LLM, three repeats | Bayesian / LLM mean absolute log error |
|---|---:|---|---|---|
| J1/S01 | 128 | 116.15 (81.93–163.52) | 140 / 140 / 140 | 0.0972 / 0.0896 |
| J1/S03 | 74 | 80.91 (54.78–118.55) | 80 / 80 / 80 | 0.0892 / 0.0780 |
| J2/S07, reserved | 21 | 38.97 (26.23–59.25) | 28 / 28 / 28 | 0.6183 / 0.2877 |

The LLM is slightly closer on both development point estimates; those small margins
should not be treated as a meaningful estimator ranking. Bayesian 90% log-interval
scores are better here: 0.691 versus mean 0.831 for S01, and 0.772 versus 1.158
for S03 (lower is better; all intervals cover these two targets). Two development
programs cannot establish general superiority or calibration. Bayesian log-median
CRPS values are 0.0666 and 0.0684; the LLM has no elicited full distribution to
which that score could honestly be assigned.

On the **reserved** program the LLM is substantially better on both point and
interval scores: Bayesian log-interval score 5.264 versus LLM mean 1.990.
The Bayesian interval misses 21 days; all three LLM intervals include it.
Bayesian log-median CRPS is 0.4834. This result rejects a claim of a demonstrated
general accuracy advantage. The independently scored reserved result is preserved;
its now-known answer is development information for any future model iteration.
[Reserved comparison](../runs/bayes_v4/comparisons/reserved/comparison.json),
[first gold-read timestamp and frozen posterior hash](../runs/bayes_v4/comparisons/reserved/manifest.json).

The final joint p90 estimates are 160.38 days (109.00–244.11), versus the simulated
199 days, and 114.11 (76.01–180.25), versus 119 days. Neither direct LLM control
provides a p90. Synthetic log medians/p90s are finite-simulation estimates, not
noise-free population constants.
[Saved joint fit](../runs/bayes_v4/context_fits/joint_scoped_actors/posterior.json),
[matched comparison and provenance](../runs/bayes_v4/comparisons/joint/comparison.json).

On 3,000 subsampled joint draws, prior-center changes 3.5/14 give S01 medians
116.64/117.19 and S03 medians 80.55/81.21; the same subsample's defaults are
116.86/80.83. Larger/new-seed quadrature gives 117.50/116.04 and 80.57/80.65,
with good overlap. Source-SD 0.7 and the joint zero-undocumented-stage condition
fail overlap (ESS 134 and 406), so their reweighted points are not reliable
sensitivities. This check does not choose a revised model after development scoring.
[Joint numerical sensitivity](../runs/bayes_v4/context_checks/joint_sensitivity/sensitivity.json).

The joint claim audit also reveals a remaining **duration-boundary defect**:
S01's 20-minute appointment duration and its multiweek wait *to obtain* an
appointment were both mapped to one activity duration. The model consequently
assigns the 20-minute report a 0.994 contamination probability. That is not evidence
the report is false; its quoted clock is different. The ledger's free-text
interpretation recognizes the distinction, but the fitted activity has no separate
access-wait/service-duration variables. A robust likelihood cannot repair that
mapping. Keep this failure in the frozen comparison; a later component-aware
correction needs a new evaluation, not silently rewritten results.
[Joint claim checks](../runs/bayes_v4/context_checks/joint_claims/checks.json).

The same fit's count estimates remain poor. S01's expected distinct initial-case
operations are 15.38 (13.45–18.94) versus 9.21 in decided logs; agency operations
are 9.94 (9.05–10.86) versus 7. Its three represented agencies match, but a
degenerate 3–3 interval is **conditional on fixed actor identities**, not evidence
that unlisted organizations have been ruled out. S03 gives 10.03 distinct operations
(8.20–13.51) versus 7; agency operations 6.80 (5.70–7.60) versus 5; and agencies
1.66 (1.15–1.95) versus 4. These misses are retained in the same comparison artifact.

## The extraction failure was real

The old Bayesian pilot consumed only 14 usable duration claims from the original
ten-document cache. The new, quote-validated contract preserves process totals,
segments, case identities, native units, source families, and actor roles.

| Program | Public documents | Usable elapsed claims | Step / segment / process | Cases | Timing-source families |
|---|---:|---:|---|---:|---:|
| J1/S03, original development task | 10 | 51 | 41 / 1 / 9 | 9 | 5 |
| J1/S01, second development program | 13 | 44 | 32 / 2 / 10 | 9 | 5 |
| J2/S07, reserved program | 12 | 51 | 35 / 2 / 14 | 10 | 6 |

The pre-context ledgers had 46/53 claims in S01/S07. The source-only context audit
excludes an earlier-period anecdote, an unrealized personal expectation, a historical
three-day estimate, and a hypothetical omission scenario. These are retained in
the ledger; excluding them is not loss during parsing.

These are not independent cases. For J1/S03, most numerical reports
come from nine cases in three forum threads. The model shares case durations and
source offsets instead of treating every extracted number as an independent process.

Source-only operation-boundary audits reduce the inventories from 32→24, 35→30,
and 34→28 respectively. They remove automatic legal states as work, consolidate
one operation's output descriptions, and preserve distinct applicant and agency
actions. All original IDs and unassigned facts remain in the audit. The audit is
not shown benchmark counts; no attempt is made to force the inventory to the
generator's chosen granularity.

## Completed original-program development fit

The extended 80,000-draw operational fit estimates a process median of **78.7 days**,
with a 90% interval **52.2–120.3 days**. Synthetic log median: **74 days**. Historical
v3 estimate: **17.9 days**; historical direct-LLM estimate: **55 days**.

The initial 48,000-draw fit had an unmeasured decision-operation R-hat of 1.0152,
above the prespecified 1.01 threshold. An extension explored the decision/other-
unmeasured-stage allocation without changing the posterior target; **all monitored
diagnostics now pass**. A reporting-only array-index bug was fixed after sampling;
saved draws were retained and their likelihoods checked before rebuilding summaries.

Artifacts: [converged extension](../runs/bayes_v4/development/operational_extended/posterior.json),
[original sampling run](../runs/bayes_v4/development/operational_1/),
[rebuilt posterior](../runs/bayes_v4/development/operational_1_summary/posterior.json),
[evaluation](../runs/bayes_v4/development/operational_1_summary/evaluation.json),
[report provenance](../runs/bayes_v4/development/operational_1_summary/manifest.json).

The inventory has 24 represented operations; its undocumented-stage prior yields
25 total operations at the posterior median, interval 24–29. The benchmark has 13
activity types. Timing improvement therefore does **not** establish calibrated
step-count inference. The audit and generator use different operational granularity,
and the lexical evaluator also makes incorrect semantic matches. Version-3 scoring
reports both split/merge-tolerant F1 (0.7711) and one-to-one-backbone F1 (0.5946),
alongside explicit count error; neither is a substitute for an audited crosswalk.

### Counts and agency identity do not yet work comparably well

A supplementary evaluation aligns the **case clock**, rather than comparing a
whole-program inventory with one case's route. On the converged context-naive S03
fit, the posterior expected distinct initial-case operations are 9.91 (8.13–13.73)
versus a log-sample mean of 7; represented agency operations are 6.81 (5.72–7.59)
versus 5; distinct agencies are 1.68 (1.15–1.95) versus 4. All three intervals miss.
The log has 9.28 visits per decided case, but visits include repetitions and must
not be substituted for seven distinct operations. The model does not yet fit visits.
Its p90 estimate, 109.25 days (70.46–193.95), does cover the simulated 119-day p90.
[Matched-clock burden evaluation](../runs/bayes_v4/development/operational_extended_burden/burden.json).

This is not just an MCMC problem. The current count posterior cannot remove or
merge a fixed interpreted operation: adding undocumented stages to an over-split
inventory cannot repair overcounting. Actor aliases are also fixed upstream, so
agency-effect learning is not the same as calibrated agency-identity inference.

There are concrete benchmark/text discrepancies as well. S03's designed process
assigns completeness to Permit Services and technical review to Building Division.
The rendered staff report explicitly assigns both to Revenue. Its generation spec
supplies the workflow, but not those two actor assignments; the rendering brief
forbids inventing additional process facts. The statute also describes retention,
aggregate reporting, ability-to-pay adjudication, payment plans, community service,
and hearings beyond the generator's 13 activity types. Meanwhile, the interpretation
misses the generator's separate translation operation. These examples mean neither
"all extra operations are false positives" nor "all differences are harmless
granularity" is defensible. Keep the failures; do not tune extraction to 13 or force
four agencies after seeing these answers.

Evidence: [S03 public staff report](../benchmark/synth/worlds/W1/artifacts/J1__S03__staff_report.md),
[staff-report generation spec](../benchmark/synth/worlds/W1/specs/J1__S03__staff_report.json),
[development truth](../benchmark/synth/worlds/W1/truth/processes/J1__S03.json),
[rendering rules](../benchmark/synth/briefs/RENDER_BRIEF.md).

### Context-corrected standalone confirmation

The final-input S03 standalone fit also passes every monitored elapsed diagnostic:
**78.92 days** (52.20–119.38), p90 **109.36 days** (71.24–190.03). The context/clock
corrections preserve the timing improvement. They do not repair count identity:
expected distinct operations are 9.89 (8.12–13.59), agency operations 6.83
(5.72–7.59), and agencies 1.68 (1.15–1.95); all three intervals still miss the
development log means. This fit is separate from the two-program joint model.
[Standalone posterior](../runs/bayes_v4/context_fits/S03_single/posterior.json),
[matched-clock burden scores](../runs/bayes_v4/context_checks/S03_single_burden/burden.json).

A repeat sensitivity check on these final-input draws gives 78.23/79.57 days
under prior centers 3.5/14 days, and 78.62/78.54 with larger/new-seed quadrature.
Overlap is good for those checks. Source-SD 0.7 reweighting again has inadequate
overlap (raw ESS 357/6,000, maximum weight 3.4%); do not use its weighted answer
as a substitute for a refit. The full source-bias and fresh-chain refits below
refer to the context-naive operational ledger, not a secretly relabeled final fit.
[Final-input sensitivity](../runs/bayes_v4/context_checks/S03_single_sensitivity/sensitivity.json),
[claim checks](../runs/bayes_v4/context_checks/S03_single_claims/checks.json).

## Does the global timing prior still dominate?

A numerical prior-predictive check is deliberately sobering: conditional on the
interpreted inventory, the S03 process-median prior has median 182 days and 90%
interval roughly 4–10,417 days in the joint-program parameterization. It is very
broad, arguably too diffuse in its upper tail—not a prior that insists on a short
process. The data sharply narrow timing, while the operation-count posterior remains
close to its inventory/route prior. "Weaker" is not automatically "better"; realistic
regularization and semantic uncertainty need separate scrutiny.
[Prior-predictive draws](../runs/bayes_v4/validation/prior_predictive_joint/prior_predictive.json).

Importance sensitivity on the operational fit (6,000 retained subsampled draws):

| Assumption | Estimated process median, days |
|---|---:|
| Default 7-day global prior center | 78.9 |
| Prior center 3.5 days | 78.2 |
| Prior center 14 days | 79.5 |
| Undocumented-stage prior mean 0 | 77.7 |
| Undocumented-stage prior mean 1 | 78.3 |
| Undocumented-stage prior mean 4 | 79.5 |
| Population quadrature 128→512 | 78.7 |
| New quadrature seed | 78.6 |

These are reweighted sensitivity estimates, **not independent refits**. Raw weight
ESS is 5,927–5,928 for the location-prior changes and approximately 5,993–5,998 for
quadrature changes. Chain autocorrelation is reported separately. These weights
were computed on the initial operational draws, before its unchanged-target
extension cleared the remaining diagnostic.

Doubling source-bias SD to 0.7 has unacceptable importance overlap (raw weight
ESS ≈14; one draw carries 26% of weight). Its reweighted answer is **not reliable**.
A full refit followed by an unchanged-target numerical extension now **passes all
diagnostics**: 83.86 days, interval 45.46–153.68. The initial refit failed eleven
diagnostics; it remains preserved. Greater uncertainty about source reliability
widens timing uncertainty and modestly moves the point estimate. It is not equivalent
to changing the global timing prior.
[Converged source-bias refit](../runs/bayes_v4/sensitivity/source_bias_0_7_extended/posterior.json).

A fresh-seed operational fit, also extended until all monitored diagnostics pass,
gives 78.51 days (52.16–118.91), versus the original converged 78.70
(52.18–120.33). This checks numerical repeatability conditional on the same ledger;
it does not establish repeatability of fresh extraction.
[Fresh-seed fit](../runs/bayes_v4/sensitivity/fresh_seed_extended/posterior.json).

Artifacts: [sensitivity report](../runs/bayes_v4/sensitivity/operational_importance/sensitivity.json).
Claim diagnostics flag the incompatible 66-day cashier claim and the associated
ambiguous 40-day application claim, rather than forcing every other activity to
occur in parallel. A high contamination probability means a mismatch with the
model, not proof that a source is false. [Claim/source checks](../runs/bayes_v4/development/operational_checks/checks.json).

The **step-claims-only ablation has converged**: 24,000 retained draws, no flagged
diagnostics, process R-hat 1.0013 and bulk ESS 3,118. Its process median is 81.7
days, but the 90% interval widens to **36.9–323.8 days**. Compared with the full
ledger's 52.6–120.9-day interval, totals/segments chiefly constrain uncertainty and
the allocation of unmeasured time; they are not merely a way to move the point
estimate toward the benchmark. This ablation still includes the repaired 41 step
claims and agency/task hierarchy, so it is not equivalent to the old 14-claim pilot.
[Ablation posterior](../runs/bayes_v4/sensitivity/step_claims_only/posterior.json).

## Agency propagation works in an independent recovery test

An independently generated test provides three measured tasks at each of two
agencies and withholds one task duration at each. Tasks share a type, so an agency
effect can be distinguished from that type. Total and component reports share
their latent case, as in the real model.

The converged hierarchy recovers a withheld **22-day** task as **22.18 days**
(90% interval 16.12–27.47) and a withheld **2.5-day** task as **2.20 days**
(1.60–3.05). This demonstrates upward/downward information propagation, not
superiority to the LLM or real-world calibration.

[Recovery results](../runs/bayes_v4/validation/pooling_interwoven2/comparison.json),
[diagnostics](../runs/bayes_v4/validation/pooling_interwoven2/report.json).
The global-only control estimates both withheld tasks near 7.9 days. Its task
diagnostics passed initially, but its aggregate process had R-hat 1.0195 and bulk
ESS 247. An unchanged-target extension now clears all diagnostics (process R-hat
1.0079, bulk ESS 501): it estimates the slow withheld task as **8.01 days**
(0.77–23.97), and the fast task as **7.99 days** (0.76–24.01). The shared agency
structure, rather than just more sampling, is what separates these tasks.
[Converged global-only control](../runs/bayes_v4/validation/global_only_extended/comparison.json).
The withheld tasks still contribute to observed case totals: this test withholds
their **direct** duration reports, not every indirect constraint. Global-only is
also not an independent-per-task/no-pooling model.

A stricter recovery scenario removes **all process totals** as well as the two
withheld tasks' direct duration reports. Both fits pass every monitored diagnostic:

| Withheld task truth | Agency/task hierarchy, days (90% interval) | Global-only, days (90% interval) |
|---|---|---|
| Slow agency: 22 days | 23.00 (12.63–38.79) | 5.57 (0.46–67.69) |
| Fast agency: 2.5 days | 2.24 (1.30–3.91) | 5.52 (0.46–65.75) |

This isolates the agency-transfer benefit from indirect total-duration information.
The two models receive identical generated evidence; both retain global and
activity-level uncertainty. Removing totals changes the fixture's RNG consumption,
so this is a separate recovery scenario, not an identical-report ablation of the
preceding with-totals experiment. Each has 20,000 retained draws; 200 saved
likelihood checks match exactly, and recorded source/evidence hashes agree.
[Hierarchy without totals](../runs/bayes_v4/validation/pooling_without_totals/comparison.json),
[global-only without totals](../runs/bayes_v4/validation/global_only_without_totals/comparison.json),
[verification](../runs/bayes_v4/validation/pooling_without_totals/verification.json).

In the actual S03 ledger, agency uncertainty is much less decisive. Revenue's
equal-weight represented-task mean is 9.88 elapsed days (5.23–25.40), while its
task-adjusted time ratio is 1.00 (0.42–2.38). Fourteen direct step reports touch
seven of its eleven represented activities. County Health has one represented
task and a ratio of 1.09 (0.54–4.22). This is information propagation with honest
uncertainty, not evidence of a reliable agency ranking. The inventory-average
estimand includes waiting and is neither workload-weighted nor a staff-productivity
measure. [Agency posteriors](../runs/bayes_v4/context_fits/S03_single/posterior.json).

The public-ledger cross-program audit also found an identifier bug: separate
generic "City of Halvern" actors received one effect because their display names
collided, despite failing the distinctive-alias merge. Program-local registry
keys now prevent that accidental pooling. The corrected final joint fit passes
every monitored elapsed diagnostic. The earlier fit is retained as a
coarse-municipality pooling control, with its remaining graph R-hat of 1.0103
explicitly flagged. These two
ledgers have no supported shared **named department** after this correction, so
their joint comparison cannot demonstrate department-level cross-program transfer.
They still share global/task-type hyperparameters. The controlled generated-data
test above supplies the direct agency-transfer check.

The first 48-replicate computational-calibration pilot has 90%-interval coverage
of 42/48 for global location, 40/48 for agency effect, 41/48 for observed and
unmeasured task means, and 42/48 for case spread. Binomial uncertainty is wide.
More importantly, the global-location rank distribution is suspicious (exploratory
uniform KS p≈0.00074), and several fits fail strict chain thresholds. This is **not
a clean calibration pass**. The subsequent pilot and target/kernel checks below
investigate it; no failed pilot is discarded.
[First pilot](../runs/bayes_v4/validation/sbc_final_pilot/calibration.json).

A subsequent harness audit found that replicate zero reused the data/truth RNG
seed for the first MCMC chain: `SeedSequence([seed, 0])` equals `SeedSequence(seed)`.
Benchmark fitting is unaffected. Both pilots' zero replicates were refitted
on their unchanged generated data with domain-separated inference streams. The
original batches and corrected scores are both retained; this correction does
not remove the first batch's rank warning.

Both 48-replicate batches have now finished. Across all 96 generated datasets,
corrected 90%-interval coverage is 85/96 for global location, 86/96 for agency
effect, 84/96 for an observed task, 85/96 for an unmeasured task, and 86/96 for
case spread. Corresponding exact binomial 95% intervals are approximately
80–94%, 82–95%, 79–93%, 80–94%, and 82–95%. The second batch's global rank check
is unremarkable (p≈0.61), but the pooled check still warns (exploratory p≈0.010).
Strict diagnostic failures remain for 1, 0, 52, 69, and 70 fits respectively.
These are encouraging coverage numbers, **not a calibration certificate**.

The second batch uses longer chains and improved invariant updates, as well as
an independent seed; it is not a seed-only intervention. An audit checks 40 saved
states per replicate across all 96 datasets: all likelihoods match current code
exactly, and no report bins hit the numerical floor. This supports comparing
the same generative timing target while keeping computational failures visible.
[Combined calibration, with original and corrected rows](../runs/bayes_v4/validation/sbc_combined_summary/calibration_summary.json),
[saved-target audit](../runs/bayes_v4/validation/sbc_target_audit/audit.json).

Six individual transition kernels were checked on 20,000 independent prior states
and on 12,000 state/data draws under the generative likelihood. No systematic large
moment shift appeared (maximum standardized checked shift approximately 3.1 among
many coordinates). This is a necessary stationarity check, not proof of correctness.
An independent, direct importance-integration reference for a weak-data posterior
has weight ESS 48,544; five posterior quantities differ from MCMC by 1.2–2.3
approximate combined Monte Carlo standard errors. These checks have not identified
a sampler bug explaining the first SBC batch, but they do not erase its warning.
[Kernel checks](../runs/bayes_v4/validation/kernel_joint/checks.json),
[independent reference](../runs/bayes_v4/validation/independent_reference/reference.json).

## Repeatability and the matched-evidence baseline

The primary reserved fit is saved, with all monitored diagnostics passing:
**38.97 days** (26.23–59.25), p90 **70.68 days** (44.05–126.82), process R-hat
1.0006 and bulk ESS 5,942. The approval-route proportion remains weakly identified:
posterior median 0.43, interval 0.06–0.91. Known selected outcomes condition their
cases; their frequencies are not treated as a representative sample. This fit and
both full sensitivity refits were saved and passed their diagnostics before the
first reserved gold read at **13:34:09 UTC**.
[Frozen reserved posterior](../runs/bayes_v4/context_fits/reserved_uncertain_outcomes/posterior.json).

Reserved reweighting gives medians 38.58/39.11 days for global prior centers 3.5/14,
38.70/38.76 for larger/new-seed quadrature, and 38.87 for outcome-logit SD 0.75,
all with adequate importance overlap. Source SD 0.7 and outcome-logit SD 3 fail
overlap checks (ESS 82/1,309; largest weights 8.1%/1.54%), so they were refitted,
not reported as reliable reweighted sensitivities. The separately fitted fixed
equal-outcome control is 38.64 days (26.08–58.41); it does not represent uncertainty
about population outcome prevalence. [Reserved checks](../runs/bayes_v4/context_checks/reserved_sensitivity/sensitivity.json).

Both full four-chain refits pass all monitored diagnostics. Source SD 0.7 gives
**37.88 days (21.22–68.36)**; outcome-logit SD 3 gives **39.13 (26.33–59.33)**.
Neither repairs the primary miss, and neither replaces the primary model. The
source-SD fit's lower endpoint must not be rounded to 21 and described as covering
the 21-day log median. Widening source uncertainty is not a selection-bias model.
[Broader-source refit](../runs/bayes_v4/context_sensitivity/reserved_source_0_7/posterior.json),
[broader-outcome refit](../runs/bayes_v4/context_sensitivity/reserved_outcome_3/posterior.json).

Three fresh pinned-model direct LLM estimates on the context/clock-audited J1 ledger
all return **140 days for J1/S01 and 80 days for J1/S03**. Three estimates on the
reserved ledger alone all return **28 days for J2/S07**. Their uncertainty ranges
differ, and none claims a defensible population p90. Their final gold comparisons
are reported above; a stable point estimate is not proof of calibrated uncertainty.

The pre-context two-program controls returned 140/75 days in all repeats. An
exploratory baseline receiving all three programs returned 140/75/35 days in
all repeats; it has a different information set and is **not** the matched control
for the separately fitted reserved program. These results suggest that a shared
evidence representation can itself stabilize LLM point estimation. Three repeats
do not establish general determinism or calibrated LLM intervals.

[Final-input joint baseline](../runs/bayes_v4/context_baseline/joint/estimates.json),
[final-input reserved baseline](../runs/bayes_v4/context_baseline/reserved/estimates.json),
[pre-context joint baseline](../runs/bayes_v4/matched_baseline_joint/estimates.json).

### Why the reserved fit failed: post-evaluation diagnosis

This diagnoses the frozen failure; it is not a corrected held-out result or a
causal decomposition of the 18-day error. No new prior or fit is chosen using it.

- **Numerical mixing and the global prior are not the main explanation.** The
  primary and broader-prior fits converge; changing the timing-prior center,
  outcome-prior spread, source-prior spread, or quadrature does not move the
  answer close to 21 days.
- **Clock interpretation can absorb disagreement instead of resolving it.** The
  same posterior estimates 18.18 days (10.11–30.43) from its modeled submission
  boundary, versus 38.97 from preparation. For the two short one-to-three-week
  case totals M45/M57, posterior probabilities of the submission-start interpretation
  are 0.71/0.84 under the unchanged equal-prior clock mixture. These diagnostics
  expose an assumption; they do not authorize substituting 18.18 as the primary
  answer after seeing 21.
- **Repeated stages do not have one simple start/end boundary.** G05 combines
  initial filing and repeated correction submissions into one duration. The
  submission-start clock then subtracts that combined operation's completion,
  which need not be the first filing event. The generator separately records a
  stage's first-to-last-visit span; such spans can overlap other activities during
  rework and cannot simply become serial DAG task durations. This is a substantive
  representation limitation, not a reason to declare all missing edges parallel.
- **Censoring and selection remain unmodeled.** M11 explicitly describes a case
  still open five weeks after contracting. Its free-text context recognizes this,
  but the unspecified-endpoint likelihood treats it like a completed process
  observation. This is a definite likelihood mismatch, although correcting that
  one observation is not established as the cause of the upward error. The nine
  forum cases and one news case also are not a representative sample of arrivals.
- **Unknown ownership is not a known absence of agency work.** Six initial-route
  operations have an unresolved personnel/system actor. They are excluded from
  the known-attributed agency-operation count, producing a misleadingly narrow
  2–2 interval if read as total backend work. Actor identity needs its own uncertainty
  model rather than a fixed unknown label.

The reserved count intervals all miss: distinct operations 14.05 (11.75–18.18)
versus a decided-case mean 9.66; known-attributed agency operations 2 (2–2) versus
6.45; and agencies 1.57 (1.09–1.94) versus 3. The logs have 19.14 visits per
decided case, a different burden quantity not fitted by the distinct-operation
model. Its p90 estimate, 70.68 (44.05–126.82), does cover the simulated 54.6 days;
that does not rescue the median/count failures.

[Frozen-ledger clock diagnostics](../runs/bayes_v4/context_checks/reserved_clocks_posteval/checks.json),
[ledger and source contexts](../runs/bayes_v4/clocks/J2__S07/evidence.json),
[generator stage-span definition](../benchmark/synth/generator/simulate.py),
[reserved burden evaluation](../runs/bayes_v4/comparisons/reserved/comparison.json).

## Agency labor is fitted separately, but remains thinly evidenced

The joint agency-work fit passes its own hyperparameter, source, agency, activity,
route, and expected-hours diagnostics; 200 saved likelihood values match current
code exactly. A reporting-only check computes the conditional mean analytically
as the sum of route-weighted lognormal means, eliminating population-quadrature
error for this particular work functional. No inference draws or likelihoods change.

For S01, the posterior median of **mean agency work per initial case** is 2.78 hours,
with a 90% interval of 0.88–12.38 hours. There is only one direct numerical input:
a cost study's two-hour estimate, currently interpreted as typical/median hours.
It is not a sample of measured staff times. Agency-specific allocation remains
weakly identified, even though the arithmetic aggregation is exact.

S03 has **no direct labor observations**. Its 2.13-hour estimate (0.20–32.41) is
entirely borrowed from the work-channel hierarchy and its priors; it should not
be described as measured agency burden. These distributions have heavy upper
tails: the sample posterior means of the mean-work functional are 5.65 and 24.17
hours, respectively, not the 2.78/2.13-hour posterior medians. Do not use the latter
as precise budgeting forecasts. Agencies outside the initial route have zero
hours only within this restricted scope, not zero annual workload.

There are no numerical payer-work observations in these ledgers. S07 has no
numerical work-hour evidence in either channel. The synthetic event logs contain
elapsed durations, not hands-on hours, so they cannot validate these labor estimates.
[Separate work-hour audit, direct-evidence labels, and analytic summaries](../runs/bayes_v4/context_checks/joint_effort/checks.json).

## What more data would need to add

The repaired process median is not very sensitive to the global timing-prior
center. The more important limits are source bias/selection, ambiguous clocks,
semantic operation boundaries, unknown routes, and unevenly observed organizations.
More documents help when they contribute independent cases, new source families,
or multiple tasks/programs at a common agency—not merely more copies of one claim.

In particular, many reports of one task identify that task's mean but cannot fully
separate its agency effect from its task-specific residual. As a simple Normal
illustration (not an additional fitted experiment), with unit agency prior variance,
unit task-residual variance and unit observation variance, an agency observed on
`T` tasks with `n` reports each has conditional SD
`[1 + T / (1 + 1/n)]^(-1/2)`. A thousand reports of one task gives ≈0.707; ten tasks
with 100 reports each gives ≈0.303. Diversity of tasks is essential for agency learning.

Staff hours are a distinct channel. J1/S01 has a two-hour cost-study estimate;
neither elapsed days nor an FTE allocation is silently converted into labor.
Agency allocations, standing overhead, monetary operating costs, repeated visits,
entirely unlisted organizations, and selection bias remain only partly identified
or outside this implementation. A principled posterior is conditional on these
assumptions, not a certificate that they are correct.

## Next Bayesian iteration

The evidence does not justify abandoning Bayesian inference, or claiming that a
larger document count alone will solve the remaining problems. The next changes
should target the uncertainties that the current fit conditions away:

1. **Operation and actor identity.** Preserve a small set of quote-supported
   split/merge/ownership alternatives and integrate over them. Calibrate their
   likelihoods on audited extraction labels; do not treat an LLM's stated
   confidence or its repeat frequency as a calibrated probability. An extra-stage
   prior cannot remove a falsely represented operation.
2. **Within-operation clocks.** Separate access waiting, service elapsed time,
   and labor. Give component claims explicit machine-readable boundaries rather
   than relying on free-text interpretation; preserve the original reporting
   precision when converting units. The appointment example above is a concrete
   regression case for this extension.
3. **Observation selection.** Add representative administrative cases or a
   defensible observation-selection model. More selected anecdotes do not identify
   how reporting probability depends on delay or outcome. Until then, selection
   parameters need explicit sensitivity analysis, not claims of being learned.
4. **Agency transfer.** Collect several task types at each genuinely shared named
   organization, with overlap across programs. Distinguish elapsed service/queue
   duration from productivity. Generic municipal labels are insufficient evidence
   of a shared department.
5. **Full burden.** Collect actual payer/staff hours, repeated encounters,
   transaction rules, and overhead denominators. Keep cost-study estimates,
   normative staffing allocations, and observed labor samples as distinct evidence.
6. **A fresh audited benchmark.** Check rendered actor assignments, operation
   boundaries and reporting clocks against their generating specifications before
   reserving a new evaluation set. Preserve this evaluation; do not tune toward
   its revealed count or timing answers.

The shared evidence contract is useful whichever numerical estimator is used:
the direct LLM controls were stable on point estimates in three repeats too.
The demonstrated Bayesian advantage here is explicit uncertainty accounting and
agency-to-task propagation, not a proven universal accuracy or replicability win.

## Verification and artifacts

The final command `python -m pytest tests benchmark/synth/generator/test_generator.py -q`
passes **111 tests**. The generator smoke test has one existing warning about returning
a value from a pytest test; it does not fail. `compileall` passes for `pipeline/procbench`.
The simplified TikZ package compiles to a one-page figure and a seven-page glossary/
model article; its audit checks 20 nodes, 20 definitions and 38 edges. The layouts
were visually inspected, and the final LaTeX log has no overflow warnings.

Both final comparison posterior hashes remain unchanged after evaluation; matched
ledger hashes and evaluation timestamps are recorded. Raw runs and failed controls
remain in the local, gitignored `runs/bayes_v4/` tree, with saved source snapshots,
configuration, seeds and posterior draws. Keep that tree when archiving these
experiments: the documentation's artifact links refer to local run files.
Source snapshots are per run, not a claim that all experiments used the identical
revision. The primary reserved snapshot predates later pre-evaluation guards for
actor keys, route facts, excluded outcomes and parallel relations. Compatibility
with current postprocessors was checked against 200 saved likelihoods (maximum
error zero); retain the original snapshot for exact replay.
