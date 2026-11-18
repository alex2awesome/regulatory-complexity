# V6 evaluation and selection work, 2026-09-19

This implements Phase 0 of the [next-steps plan](2026-09-19-next-steps-plan.md).
It does not establish recovery, held-out performance, or superiority to an LLM.
The [burden audit](2026-09-19-bayesian-burden-audit.md) remains independent.

## Latest checkpoint: September 20, 04:33 UTC

The C44 routine-task-prior sensitivity has finished, passed numerical diagnostics,
and **failed development clock recovery**. Changing only the elapsed-time prior
medians for filing, payment and notification from seven days to one day gives
107.19 days (90% interval 45.12–238.03), versus the 41-day development target and
103.24-day control. Its ratio to target is 2.614 and its interval misses the
target. These are uncalibrated sensitivity values, not active-labor hours; no
decision-scope or block-order repair is included in this comparison.

All 27 archived files verify. Thirty-two saved likelihood evaluations replay
within 2.14e-13. Operation-sum R-hat is at most 1.00348 with bulk ESS at least
1,683; source-adjusted values are 1.00367 and 1,665. There are still 330 of 346
coordinates below 10% marginal prior-variance contraction, and 343 below 25%.
Convergence therefore does not imply identification or accurate recovery.

A paired-draw check holds each saved parameter state fixed while switching the
task baselines. On 64 draws per chain from the seven-day control, the median
paired clock ratio is 0.618 (about 38% shorter with one-day baselines). On draws
from the one-day refit it is 0.550. Every paired clock is non-increasing under
the shorter baseline, and 64 likelihood checks across the two fits replay within
1.99e-13. The refit compensates for the direct reduction through its other
posterior quantities; this diagnostic does not identify which parameters cause
that compensation. Subsampled cross-config predictions are not draws from the
other posterior and do not replace full-fit reports. We do not interpret the
small increase in the refitted median as a statistically established worsening.

Receipts: `runs/rw_parse_20260919/task_prior_sensitivity_results_v1/`, including
`C44__S12_one_day_task_prior_sensitivity_audit_v1.json`, the standard
`C44__S12_one_day_task_prior_sensitivity_score_v1/` evaluation and failed gate,
and `c44_paired_task_baseline_diagnostic_v1.json`. C29's task-prior and C44's
selection fits are still running at the last 04:13 UTC process check; no active
fit was modified.

### Block-order sensitivity, 03:50 UTC

The C44 block-order sensitivity has completed and passed independent audit:
all 26 archived file hashes, 32 likelihood replays (maximum error 1.99e-13),
operation-sum R-hat at most 1.00302 / bulk ESS at least 1,190, and
source-adjusted R-hat at most 1.00335 / ESS at least 1,185. Saved convergence and
numerical gates pass, but **development clock recovery still fails**.

| C44 initial-decision median | Original serial control | Explicit block-DAG sensitivity |
|---|---:|---:|
| Posterior, days | 103.24 | 98.06 |
| Posterior / development target (41 days) | 2.518 | 2.392 |
| 90% interval, days | 46.23–218.79 | 39.63–223.66 |
| Interval covers target | No | Yes |

This changes only scheduling between whole blocks, preserving the original
decision barrier and serial post-decision sequence. It is an optimistic
unknown-order sensitivity, **not evidence that actual parallelism was learned**.
The median decreases by about 5%; coverage improves through a broad interval,
not successful recovery. The separate decision-scope repair below is not included
in this fit, and the two improvements must not be added as if independent.
Both fits have 342 of 346 coordinates below 25% marginal prior-variance contraction;
this is not a measure of total information or causal identifiability.

A bounded paired-draw diagnostic explains why this is smaller than the direct
scheduling effect. On 64 retained draws per chain from the serial fit, changing
only the prediction schedule gives a median paired clock ratio of 0.758
(about 24% shorter). On the separately refitted DAG posterior it is 0.797.
The full refit therefore compensates for much of the direct shortening through
its other posterior parameters/structures; sparse timing evidence does not
pin those quantities separately. This is a sensitivity comparison, not a
decomposition identifying which parameter caused the compensation. Cross-schedule
predictions are not draws from the other posterior, and the subsampled medians
do not replace the full saved reports. Both archived likelihoods replay under
the frozen DAG implementation (64 checks total; maximum error 2.42e-13).

Receipts: `runs/rw_parse_20260919/block_order_ablation_results_v1/`, including
`C44__S12_block_order_control_audit_v1.json`, the standard
`C44__S12_block_order_control_score_v1/` evaluation and failed release gate, and
`c44_paired_schedule_diagnostic_v1.json`. At 03:48:55 UTC, C44's task-prior fit
has finished all chains and is reporting; C29's task-prior and C44's selection
fits are still sampling. No active fit was modified.

### Progress instrumentation, 03:25 UTC

Operational reporting now exposes progress without changing inference. Future
fits write `run_progress.jsonl` for sampling, combined-draw saving, posterior
prediction progress (first draw, every 250 draws and last draw), diagnostics,
integration checks and completion. Reporting previously had no visible progress
while revisiting all saved draws, which made a finished sampler appear stalled.
The optional callback leaves the scientific report and input arrays unchanged;
the logger refuses to overwrite an existing log. The full suite passes **978
tests** (one pre-existing generator warning). Current remote fits keep their
frozen sources and are not restarted to pick up this instrumentation.

At the earlier 03:24:58 UTC checkpoint the C44 block-order sensitivity had finished all four 8,000-step
chains but is still producing its posterior report. C44 selection-on and both
task-prior sensitivity jobs remain running. Completed chains alone are not a
convergence or recovery result. Poll receipt:
`runs/rw_parse_20260919/owned_visit_jobs_20260920_0326.json` (its embedded timestamp
is authoritative).

### Structural clock-support and decision-scope findings

A new structural clock-support diagnostic exposes an additional input limitation
without changing inference. In the saved C44 decision-scope fit, both
`first_submission` readings of m32 lack the required submission marker in **all
four inventories**. Their posterior weights of zero are therefore structural
exclusions, not evidence that the applicant meant process start. Moreover, all
48 inventory/path combinations contain only one nonrepeated decision marker:
initial and final decision are mechanically the same event. Appeal work exists,
but its decision is not marked by this handoff. The old bridge documents this
limitation; convergence cannot repair it.

`VisitHierarchy.clock_support_report()` is now included in bridge, preflight and
posterior reports. It checks event presence against case/population path scopes,
reports unsupported alternatives and guaranteed initial/final aliases, and does
not infer events from task names, renormalize interpretation priors, or change
likelihoods. Positive marker coverage is not proof of temporal or semantic
validity. The saved-input diagnostic is
`runs/rw_parse_20260919/decision_scope_ablation_results_v1/C44__S12_clock_support_v1.json`.
It finds eight unsupported inventory/operator combinations belonging to m32.
Repair requires quoted event bindings and correct handling under inventory
merges; guessing a submission marker or optimizing it against truth would not
be a valid repair. Restoring a supported clock need not lower the burden estimate.
All **976 tests pass** (one pre-existing generator return-value warning); the
seven new cases test missing markers, path conditioning, aliasing, bridge reporting and unchanged
likelihoods. Running remote fits retain their original source snapshots.

The C44 decision-scope comparison has finished, been collected with all 26
archive hashes checked, and passed independent replay of 32 saved likelihoods
(maximum absolute difference 1.43e-13). Operation-sum R-hat is at most 1.00381
with bulk ESS at least 1,264; source-adjusted sums reach R-hat 1.00408 / ESS 1,258.
The saved convergence and numerical gates pass. **Clock recovery still fails.**

| C44 initial-decision median | Original control | Decision-scope repair |
|---|---:|---:|
| Posterior, days | 103.24 | 83.56 |
| Posterior / development target (41 days) | 2.518 | 2.038 |
| 90% interval, days | 46.23–218.79 | 44.22–154.87 |
| Interval covers target | No | No |

Reconnecting three already-extracted decision-clock reports lowers the median
by about 19%, but does not explain the remaining twofold overestimate. This is
the prespecified endpoint comparison, not the selection-on fit and not the
fresh source-reconciliation model. It changes neither graph nor priors nor
the other 31 factors. The broader source-identity, lifecycle, ordering and
cutoff issues remain. Counts covering their targets here do not establish
count identification, and absent labor/fee outputs are still absent.

Archive and independent audit:
`runs/rw_parse_20260919/decision_scope_ablation_results_v1/`, including
`C44__S12_decision_scope_control_audit.json`. Standard scoring and the failed
development release gate are in `C44__S12_decision_scope_control_score_v1/`.
No synthetic posterior is being released as validated or as better than an LLM.

The fresh 22-artifact source-only reconciliation is complete at
`runs/rw_parse_20260919/w2_current_source_reconciliation_v1/`. Parent replay
checks 84 unique bound files, all 22 source hashes, preservation of the 81 prior
measurement rows, and 331 literal references in the new substantive outputs.
The worker's independent replay additionally checks references in the prior inputs
(633 total). Parent semantic acceptance is scoped, not a second blind extraction;
two copied C29 fee comments inside C44 have explicit non-applicability overrides.
Initial receipt: `w2_current_reconciliation_parent_review_v1.json` in the same
runs parent. A further full reread of all seven forum/Reddit documents found a
substantive case-outcome bug: five of the abandoned Oakland applicant's step
reports were marked `decided_outcome_unspecified`, because the worker used the
measurement ID to recognize abandonment instead of propagating case outcomes.
The preserved derivative `w2_current_reconciliation_parent_revision_v2/` corrects
those five, fills five missing known case outcomes, and explicitly preserves an
unspecified completion for the vague C44 forum recollection. It also incorporates
the two editorial fee corrections. Its authored twelve-case outcome registry and
effective views pass 400 literal-reference checks. The original packet is unchanged;
the incomplete first derivative attempt remains unselected. **Use the v2 effective
views and lineage, not the original timing annotations alone.**

This resolves some semantic mistakes but does not create a fit-ready graph:
C29's business licence and concurrent registration are distinct; C44's portal
setup is nested in electronic filing; unnamed C44 timing labels do not identify
operations, actors or lifecycle stages. Review inventories remain illustrative,
unweighted hypotheses. The workflow's renewal-before-issuance conflict and the
different visit-log versus whole-case cutoffs are retained. New compilation must
explicitly account for these facts rather than silently reuse old activity IDs.

At **01:55 UTC**, two separate task-prior sensitivity fits launched on SK3:
`task_prior_sensitivity_stage_v1/launch.json`, remote stage
`/lfs/skampere3/0/alexspan/regulatory-complexity-v6/task-priors-20260920.8xvgl9n6`.
They use the archived C29/C44 control input bytes and settings, changing only
elapsed visit-cycle baseline medians for filing, payment and notification from
seven to **one calendar day**. All scales, sampled coordinates, graphs,
observations and selection-off settings remain fixed. These are round
counterfactual sensitivity values, **not calibrated or elicited priors**, and
elapsed waiting is not converted from labor hours. Improved development scores
will not by themselves justify adopting them. Both jobs have live compute workers
and finite initial likelihoods. No running or historical job was changed.

This is separate from the selection, decision-scope and scheduling comparisons.
The decision-scope result is reported above. Selection and block-order fits
continue. The sensitivity launch used the interface with 969 passing tests;
the later clock-support reporting change above does not alter those fits.

## Completed: standard post-fit scoring

`pipeline/procbench/evaluate_burden.py` now accepts V6 posteriors and the
`W2_DEV_001` world alias. Example, with a fresh output directory:

```sh
python -m pipeline.procbench.evaluate_burden \
  --run runs/w2_v6_fits_sk3_20260919/v2_combined_dedup_p8192 \
  --world W2_DEV_001 --out runs/my_new_v6_evaluation
```

Before reading any truth, it checks fit completion, the saved posterior hash,
and **all** program assignments against the world's calibration/development
partition metadata. Reserved and unassigned counties are rejected. Scoring
produces `evaluation.json`, `burden.json`, `release_gate.json`, and a completed
manifest binding the posterior, truth files, partition file and source snapshot.
Truth access is explicitly declared. Fitted inputs, draws and posteriors are not
modified. Legacy V3/V4 comparisons remain separate.

Every available fitted quantity gets a matching score or an explicit unsupported
disposition. Scores include median error, ratio, CI90 coverage and the shared
proper interval score, with log scores only for positive quantities. No labor
truth is invented from elapsed time. Missing fee reports are not zero. Conditional
route predictions are not flattened into unconditional predictions.

The development gate requires convergence, numerical precision, a completed
posterior-bound evaluation, and the plan's clock ratio of 0.7–1.4 with CI90
coverage. Passing this gate would still **not** establish validated synthetic
performance: source semantics, matched populations and untouched evaluation are
separate requirements. New fitter reports also explicitly state that inference
does not perform external truth validation.

## Clock bug in the scratch reference

### Later construction-side finding: news volume cohorts

The 2026-09-19 compact-source review found that the generator's backlog-news
branch in `benchmark/synth/generator/visibility.py` draws received applications
and issued permits independently (`60 + randrange(180)` and
`10 + randrange(60)`), while the attached timing sample size comes from the
simulated decided-case cohort. In the approved 438-document selection, **11 of
19 news documents** contain these unlinked volume claims; **nine** report a
timing sample larger than the stated applications received. None reports more
permits issued than applications received. Distinct reporting periods could
reconcile the numbers, but the specifications do not license those periods.
Inventing “historical” and “current” labels would hide the mismatch.

Read-only receipt:
`runs/rw_parse_20260919/compact_news_count_cohort_audit_v1.json`.
No specs, processes, cases, timing values or active fit snapshots were changed.
The exact C25 news document is held pending authority for a narrowly scoped
input correction; the broader count-cohort issue requires resolution before
these news totals support a count/rate recovery claim. This construction-side
report must not be handed to a source-only parser.

The running C29 ablation inputs carry its news timing statements as
`report_only` residuals, not cohort observations using the invented news
totals. That limits this defect's direct relevance to those frozen timing
comparisons; it does not repair the news corpus or validate count recovery.

### Original scratch-reference clock finding

`runs/w2_v6_fits_20260918/compare_to_truth.py` treats
`event_clocks.initial_decision` as a number. The generator stores an event object
with `elapsed_days`, `end_date` and `censored`. Consequently the scratch code
always substitutes legacy `elapsed_days`, the last-decision clock. The standard
evaluator reads named event objects and does not substitute another clock when a
requested one is missing or unobserved.

The reference's main numbers nevertheless reproduce on the five evaluated
programs: their relevant first- and last-decision quantiles coincide. The new
receipt covers **14 saved fits / 31 program-fit rows**, with **zero differences**
on the seven checked common quantities across the 29 rows having a saved
reference. The additional two rows are an existing repeat fit. This confirms the
audit's numerical comparison; it does not validate the reference's general clock
handling. The original scratch script and scores are preserved.

Receipt: `runs/rw_parse_20260919/v6_development_evaluations_v1/summary.json`.
Reproducer: `runs/rw_parse_20260919/evaluate_saved_v6.py`.
All 31 program-fit rows fail the development clock-recovery condition. For
example, the numerically usable SK3 combined/deduplicated fit has ratios 2.486
(C29) and 3.280 (C44); only C29's interval contains the comparison median.

The primary comparison population is explicitly **uncensored finally
approved/denied cases with an observed named event**, matching the audit's
closed-case population. Event-specific observed cohorts are additionally
reported. These cutoff-conditioned finite cohorts are not interchangeable with
an unconditional population. Counts use complete simulated paths, including
post-decision work, rather than the legacy evaluator's decision-truncated path.
Applicant-facing visibility and payer-work flags also need semantic alignment
before their comparison can be treated as a recovery test.

## Truth-access disclosure

While inspecting clock schema, the coordinator mistakenly included
`C02__S03` instead of `C32__S03` in an ad hoc log inspection. C02 is **unassigned**
in the render partition, not reserved. That inspection read its log and printed
its closed-case count and clock median. It did not enter an extractor, compiler,
fitter, prior, or calibration artifact. Do not describe the coordinator's whole
session as having read only designated calibration/development labels. No
reserved labels were read by this scoring work. The new pre-read partition guard
also rejects unassigned programs, specifically preventing this class of error
in the standard evaluator.

## Validation and remaining work

Eighteen new source-free regression cases cover named clocks, missing clocks,
cohort differences, full-path counts, money/labor absence, proper scoring,
conditional predictions, release gates, and checks before truth access.
The full suite passed **894 tests** with the existing generator return-value
warning. Subsequent changes must be rerun against that suite.

Phase 1 remains open. Source-type selection must be an explicit compiler
assumption, independent of case-ID naming and source-offset grouping, with
conflicting ascertainment mechanisms exposed. A real forum's existence is not
evidence for a known numerical inclusion probability. Selection, overlap and
task priors need controlled single-program development ablations and numerical
checks, followed by untouched evaluation—not successive claims of validation
on C29/C44.

## Source-type selection ablation launched

The compiler now accepts an explicit policy, for example
`source_type_sampling: {"forum": "delay_selected"}`, alongside an explicit
default for other sources. It consults source types, not case IDs, independently
of source-offset pooling. Mixed ascertainment mechanisms on one case require an
explicit reviewed override. The same case mechanism propagates to timing,
money, effort and count observations. Type decisions and unknown types remain
visible in the compilation receipt. This is a sensitivity assumption, not a
claim that forum inclusion probabilities have been measured.

`run_visit_hierarchy --selection-sd 2` enables the existing half-normal prior on
the log relative inclusion weight. Zero remains the default and disables the
correction. Preflight exposes declared selected cases with correction disabled.
Reports include the fitted log relative weight, distinguishing it from absolute
posting probabilities and the generator's discrete selection mechanism.

Preparation: `runs/rw_parse_20260919/selection_ablation_inputs_v2/`.
The preparation script reads only frozen artifact-side parse, audit, compilation
and bridge inputs. It verifies their hashes, exactly reproduces the original
control observation factors, and checks that the paired inputs differ only in
sampling declarations (including grouped-report provenance). There are five
selected cases / 11 changed observations in C29, and six / 24 in C44. Initial
preparation failures are preserved; v1 is partial, v2 is the completed input set.

At **19:40 UTC**, four jobs launched on SK3 in an isolated new compute directory:
`/lfs/skampere3/0/alexspan/regulatory-complexity-v6/selection-ablation-20260919.gNKZOO`.
Each program has its own control and selection-on fit, with four chains, 2,000
warmup, 6,000 retained draws, population size 8,192 and seed 2026092201. C44
retains its existing within-visit phase model; C29 does not acquire it. The
historical blocked sampler is unchanged. Two worker processes per fit, one BLAS
thread per worker. No pooled fit, new task prior, graph change, benchmark truth,
or score is included in this stage. All four were confirmed alive with finite
first-iteration likelihoods. Completion/precision/recovery are not yet known.

Local code/input inventory and launch receipt:
`runs/rw_parse_20260919/selection_ablation_stage_v1/`. The remote stage is owned
compute space, **not** a reviewed durable archive. Do not overwrite it with later
local source changes or restart jobs merely because sampling takes hours.

## Reporting improvements after the frozen remote stage

Local V6 code now reports applicant-participating visits and distinct operations
when actor/work applicability is resolved, and reports missing applicability
explicitly. This participation proxy is not automatically identical to the
generator's applicant-facing visibility.

For fully specified fee schedules, `expected_burden` and reports now include
`mean_fee_total` and `fee_total_case_sd` in USD. The latter is analytic between-
case spread over repeat multiplicities and case paths; it is not the posterior
uncertainty of the mean. Total variance, not an average of branch standard
deviations, combines path mixtures. Unstated fees suppress totals; a declared
zero is preserved. The existing per-visit fee contract charges repeated visits
again—this assumption must be source-reviewed, not silently applied to a
once-per-application charge. Missing fee totals in the older inputs are not
backfilled with benchmark amounts.

These reporting changes add no latent parameters or likelihood factors and are
**not present in the already frozen remote ablation code**. The fee-recovery
gate remains open. The suite now passes **900 tests**, with the same pre-existing
generator warning.

## Exact-computation speed improvement, after the running jobs were frozen

Profiling explains why the C44 selection fit is substantially slower: its first
inventory has 12 case paths, each integrated over 8,192 population cases. The
previous likelihood rebuilt full population traces when phase parameters changed,
although selection uses total elapsed clocks, which do not depend on the
waiting/service split. It also repeatedly sorted unchanged population clocks and
recomputed unchanged selection normalizers for case/source proposals.

Local code now keeps a separate clock-only population cache when no population
phase observation or finite cohort needs phases. Full individual phase traces
and any required population phase traces remain available. Selection summaries
are cached by complete trace identity, path probabilities and selection strength.
No prior, sampled coordinate, population size, report operator, or likelihood
factor is changed. The original remote jobs continue on their original snapshot;
the running jobs were not patched or relaunched.

Two isolated imports replayed **157 identical states across all four C44
inventories**, comparing **2,512 likelihood factors with exactly zero numeric
difference**. Local near-prior median speedups were 1.11× for duration changes,
7.58× for phase changes, 1.98× for case changes, 1.62× for selection changes and
2.58× for source changes. These are block-level computation measurements, not an
end-to-end sampler speedup or evidence of better posterior mixing/recovery.

Receipts: `runs/rw_parse_20260919/selection_cache_replay_historical_v1/replay.json`
and `selection_cache_replay_current_v1/replay.json`; reproducer
`runs/rw_parse_20260919/replay_selection_cache.py`. The earlier profile remains
in `selection_likelihood_profile_v1/`. Eight source-free cache tests cover
invalidation, full phase requirements and comparison against uncached formulas.
The full suite passes **908 tests** with the pre-existing generator warning.

## Source taxonomy correction

The real-source artifact indexes declare forum documents as `forum_post`, which
the burden-channel compiler previously did not recognize. The shared type reader
now accepts that alias and already-normalized source families. An explicitly
unrecognized type remains unresolved: neither a suggestive filename nor an
offset-family name can override it. Legacy filename inference remains available
only when no explicit document type was supplied. This prevents source selection
from depending on whether an opaque document ID happens to contain “reddit”.

Three regression tests cover these decisions. The full suite now passes **911
tests**, with the same pre-existing generator warning. This correction is local;
the four running ablations retain their frozen code and source decisions.

## First larger ablation result: C44 control, 22:12 UTC

The C44 selection-off control has completed and its 25 archived files pass
hash verification in `selection_ablation_results_v1/C44__S12_control/`.
Four chains × 6,000 retained draws pass the fitter's convergence and numerical
precision gates. An independent import of the archived source replays 32 saved
likelihoods with maximum discrepancy 2.0e-13. Additional operation-location
and source-adjusted-location checks have maximum R-hat 1.00481 and 1.00533,
respectively, with minimum bulk ESS above 1,460.

Nevertheless, the standard hash-bound development evaluation fails recovery:
initial-decision median **103.24 days** versus **41 days**, ratio **2.518**;
the 90% posterior interval **[46.23, 218.79]** does not cover the target.
This is a numerically usable posterior under this model, not a validated
burden estimate. The paired selection-on fit and both C29 fits are still
running; this result alone does not establish selection bias as the cause or
show that correcting it succeeds. The larger run does establish that simply
retaining more draws did not resolve this control's recovery failure.

The identification report also remains weak: 326/346 coordinates have under
10% marginal prior-variance contraction and 342/346 have under 25%. That is a
coordinate-level diagnostic, not a proof that every predictive combination is
uninformed. Intrinsic agency-effect headlines remain ineligible.

Scoring: `selection_ablation_results_v1/C44__S12_control_score_v1/`.
Independent replay: `C44__S12_control_independent_audit_v1.json` in the same
parent directory. These are all under `runs/rw_parse_20260919/`.
The original collector's unsupported macOS `rsync --protect-args` option was
replaced with strict safe-path validation; the failed empty collection directory
is preserved. No remote fit or source snapshot was changed.

One runtime detail: after chain completion, the frozen reporter computes
population predictions for all 24,000 retained states before its separate
precision check. This CPU work has no per-draw progress log; a quiet reporting
phase is not evidence that the process stalled.

### C29 control completed, 22:49 UTC

The other selection-off control is now collected with all **25 archived files**
hash-verified. Four chains × 6,000 draws pass convergence and precision gates;
runtime was 11,311 seconds (about 3.14 hours). Independent frozen-source replay
of 32 likelihoods differs by at most 1.42e-14. The maximum operation-location
R-hat is 1.00169 and source-adjusted-location R-hat 1.00179; their minimum bulk
ESS values are 3,124 and 3,064, respectively.

Recovery nevertheless fails: **81.13 days versus 46 days**, ratio **1.764**.
The 90% interval **[28.32, 354.47]** covers the target but is broad, and the
central estimate misses the plan's 0.7–1.4 ratio condition. Both selection-on
fits remain in progress. Neither completed control passes the development
recovery gate; these numerical checks cannot establish that selection
correction will fix the problem.

Results, standard scoring and independent audit are respectively
`selection_ablation_results_v1/C29__S12_control/`,
`C29__S12_control_score_v1/` and
`C29__S12_control_independent_audit_v1.json`, under `runs/rw_parse_20260919/`.

## Source-to-model gap identified after that result

The frozen compiler conservatively suppresses any timing report carrying an
explicit decision context. The downstream structural bridge already supplies
conditional paths for several of those same cases, but there is no handshake
allowing the compiler to recognize that the condition was represented.

For C44, three rows have **only** a decision-ID context constraint: a 5–7-week
denial, a 3–5-week approval, and a 209-day approval. All three become
process-independent residual reports, although each case already has an
appropriate bridge `case_path_scope`. Only two whole-case totals, about three
months and 218 days, remain connected to process clocks in this frozen input.
This drops both short and long reports; the net fitted effect remains unknown.
C29's five context-blocked rows additionally require activity/milestone handling
and cannot be released by a decision-only fix.

The source-only receipt is `runs/rw_parse_20260919/decision_context_gap_v1.json`.

### Opt-in decision binding implemented, 22:42 UTC

`compile_visit_durations --structural-context <preserved-data.json>` now accepts
an explicit compiler/bridge binding. The source ledger must state a single
decision outcome, and every inventory must already scope the case to all and
only paths containing that single, unrepeated decision operation. Conflicting
outcomes, missing paths, repeated decisions, activity inclusion/exclusion and
milestone constraints are not silently resolved. Existing report/operator holds
still apply. The fitter checks the binding against a hash of the exact process
routes and case scopes; dropping or changing the scope rejects the input.

Source-only replay in
`runs/rw_parse_20260919/decision_scope_projection_v4/` restores exactly C44
measurements m20, m32 and m36. Their intervals, source families, selection
declarations and pre-existing interpretation policy are retained; their original
case links and previously authored operator mixtures become informative again.
The other **31 C44 factors** are byte-for-byte-equivalent JSON values, as are
all **32 C29 factors**. Rebuilding from the original structural handoffs also
reproduces the exact graphs and case scopes. Both models have finite likelihoods
at the prior-mean coordinate vector, and removing C44's scope fails validation.

The replay follows each bridge's manifested compilation lineage: C44 uses a
later report-grouped compilation, not the older ungrouped diagnostic directory.
Early replay attempts failed guards before producing a C44 candidate; partial
v1–v3 receipts are preserved and are not the completed projection. This lineage
check prevents inadvertently replacing grouped intervals with their components.

Twenty-one new source-free regression cases cover the handshake and its rejection
paths, including aggregate/rule claims that happen to carry case IDs. The binding
requires a genuinely individual source claim. The full suite passes **932 tests**, with the same pre-existing generator
return-value warning; the frozen-reference test also archives the new dependency.
No running input or remote source has been modified. No new fit has been run
with these restored reports, and no recovery improvement is claimed. This is a
separate candidate change from the frozen selection ablation.

## Administrative-cohort readiness, 23:10 UTC

The Phase 3 proposal step needs source-level denominator review, not just an
integer `n`. `runs/rw_parse_20260919/solar_cohort_readiness_v1.json` inventories
all 74 median/p90 rows in the archived solar ledger and records these distinctions:

- **Eleven rows put a jurisdiction count in `n`**: 33/29 AHJs in the 2024
  report, 27/19 in 2023 and 13/7 in 2022. These are not numbers of permit cases.
  The source context explicitly distinguishes authorities from their projects.
- **Seventeen rows copy total year/technology project counts** onto different
  timing endpoints. The retrospective report says projects need only one date
  pair to enter the data; only about half have every milestone. Consequently a
  year total does not establish each endpoint's complete-case denominator.
- **Twenty-five rows quote a derived catalog/workbook summary**, not the
  original workbook cells. Primary-cell reconciliation must use the corrected
  SolarTRACE ownership/unit panel and preserve its denominator and overlap holds.
- Two adoption medians genuinely describe 97 agencies, but those agencies are
  undertaking software adoption, not applicant permit processing. Their backend
  burden is a separate estimand, not an erroneous count to discard.
- One restated study says **over** 200,000 cases, not exactly 200,000. Eighteen
  remaining rows have no explicit `n` and still require scope/statistic review.

The inspected compilation has **56** finite-cohort-contract holds. That predicate
is not the same as the earlier audit's “69 dropped medians”; neither should be
silently substituted for the other. The new receipt binds eleven supporting
source passages and preserves every original row. It does not alter a running
fit, rewrite the original audit, or claim complete semantic review of all rows.
The sidecar is a review requirement, not yet a new enforced compiler contract.

Thus “zero medians dropped for want of a binding” should mean zero **otherwise
eligible** rows held solely for missing clerical linkage. It must not force an
unjustified case denominator, quantile convention or independence assumption.
Unknown finite `n` does not make an aggregate uninformative: a population-summary
likelihood may still be appropriate after scope, dependence and reporting error
are resolved. The CalFresh CF18 parser's new native means/histograms are being
handled with the same distinction; they are not coerced into quantile factors.

## Separate decision-scope control launched, 23:21 UTC

`runs/rw_parse_20260919/decision_scope_ablation_stage_v1/` freezes a new C44
single-program comparison. It restores only m20/m32/m36; the other 31 factors,
graph, route/path priors, case scopes, reported intervals and interpretation
weights remain unchanged. Source-only preparation replays the compiler and
structural bridge with current validation code, checks all four inventories,
and reproduces the old control likelihood in 32 near-prior states. These finite
checks are not a general proof of numerical equivalence.

This is **not** another selection correction: `selection_sd=0`. The comparator
is the already collected `C44__S12_control`. Settings match that run: four chains,
2,000 warmup, 6,000 retained draws per chain, population size 8,192, two workers,
seed 2026092201, within-visit phases, observed channels only and the blocked
sampler. The current engine includes the previously tested exact population
cache and additional validation/diagnostic checks. It has 346 coordinates.

The source/input-only stage contains 58 manifested files. No truth, evaluation
scores, real-corpus files or previous draws were transferred. SK3 stage:
`/lfs/skampere3/0/alexspan/regulatory-complexity-v6/decision-scope-20260919.pnnsz0qj`.
The live launch handle is PID 2714082; `launch.json` records the exact command.
The original selection experiments were not modified or restarted.

The preregistered comparison is in `protocol.json`: independent archived
likelihood replay, chain/integration checks and standard clock/count/fee
scoring. Timing recovery still requires a ratio in 0.7–1.4 and 90% coverage,
not merely an improvement over the failed control. The coordinator has already
seen development results; this is not blinded or held-out evaluation.
No result or improvement is claimed at launch.

The collector now accepts explicit `--launch` and `--out` arguments for this
separate archive. Both historical controls are still hash-checked without
overwriting. At 23:21, C29 selection had finished sampling and was reporting;
C44 selection was still in its first chain pair. The original local solar
extension had saved all four extended chains and combined draws, with its
parent process still computing diagnostics.

## C29 selection result and completed solar extension, 23:33 UTC

The C29 selection-on fit is now collected and independently checked. Both it
and its unchanged control pass their saved convergence and numerical gates,
but **neither passes clock recovery**:

| C29 initial-decision median | Control | Selection on |
|---|---:|---:|
| Posterior, days | 81.13 | 81.31 |
| Posterior / development target (46 days) | 1.764 | 1.768 |
| 90% interval, days | 28.32–354.47 | 28.02–349.33 |

This is no demonstrated timing improvement, not evidence that selection is
generally irrelevant. The five selected cases supply eleven individual timing
rows, all task-cycle/residual mixtures; their overall-process durations remain
unmodeled residuals. The correction is enabled, but its log high-versus-low
inclusion weight remains weakly informed: median 1.293, interval 0.118–3.902,
close to the declared half-normal scale-2 prior. Its whitened coordinate has
3.3% marginal variance contraction; that statistic is not total information or
causal identification. Absolute posting probabilities are not estimated.

`runs/rw_parse_20260919/c29_selection_information_audit_v1.json` independently
verifies this information bottleneck: 13 modeled rows, 19 residual-only rows,
and zero modeled whole-case-clock rows. Setting selection strength to zero at
32 fixed saved states changes likelihood (maximum absolute difference 1.991),
so this is not an inert configuration switch. Those fixed-state contrasts are
not Bayes factors or another refit. The prior's strength median is 1.349 with
90% interval 0.125–3.920, close to the posterior above.

Saved result: `selection_ablation_results_v1/C29__S12_selection/`; standard
evaluation: sibling `C29__S12_selection_score_v1/`. The independent audit checks
25 transferred file hashes and replays 32 frozen likelihoods with maximum error
2.85e-14. Worst operation-location R-hat is 1.00231 and source-adjusted R-hat
1.00240; their minimum bulk ESS values are 2,565 and 2,517. These are numerical
checks, not recovery or source-semantic certification. C44 selection and the
separate three-report decision-scope correction remain running.

The original local solar extension also completed at 23:24:57 UTC after about
12.6 hours. Its combined four-by-6,000 draws still fail both convergence and
prediction precision (maximum checked clock-quantile change 2.53%, above 2%).
Independent replay of 32 states is exact, and 27 file hashes/bindings check.
Additional operation-sum diagnostics are worse than its coordinate-only maximum:
R-hat 1.04118, minimum bulk ESS 125; source-adjusted sums R-hat 1.04086, ESS 110.
Receipt: `runs/rw_parse_20260919/solar_extension_independent_audit_v1.json`.
Stable central estimates across extensions do not establish convergence, repair
the documented input omissions, or authorize real-corpus burden headlines. This
run is completed, not stuck; it is not being restarted.

## Current-source extraction queued, 23:49 UTC

A separate source-only snapshot is now frozen at
`runs/rw_parse_20260919/w2_current_c29_c44_sources_v1/sources/`: 22 unique
documents, 12 assigned to C29 and 11 to C44 including one shared statute.
These are the current compact documents and county dependencies, not the older
diagnostic source bytes. Every included artifact, spec and complete verifier
context matches a passing review; all copied artifact hashes replay independently.
The one held C29 news document is explicitly excluded in the private coordinator
receipt. This is a scoped diagnostic subset, not completion of all 438 documents.

The existing source-only worker is queued to read the packet after Reddit011,
following `w2_current_c29_c44_parse_brief.md`. It receives only the public-source
subdirectory and contracts, never the coordinator receipt, verifier findings,
specifications, old synthetic parses, graphs, draws or scores. Fresh C29 then
C44 ledgers will receive independent semantic review before compilation. No new
fit is launched from this packet yet. This changes the source edition and is
therefore distinct from both frozen comparisons still running on SK3.

## Compact repair boundary and live fits, 00:05 UTC September 20

The authorized non-held compact repair queue is exhausted. A parent read-only
recomputation at 00:03:53 UTC confirms **428 current-hash passes, five failures
and five unverified documents out of 438**. The ten nonpassing documents are
held; this is not a released corpus. Five input-consistency decisions remain:
registration ordering at C57, the C25 timing/volume cohort conflict, independently
sampled news volume claims, C41 fee timing, and the newly recorded C22
portal-registration-versus-paper-filing description conflict. Neither the world
nor these held inputs was changed to clear the gate. Exact IDs and proposed
repairs are in
`runs/w2_s12_s03_completion_20260917/compact438_handoff_20260919T235343Z.json`
and its linked queues. The older saved count snapshot precedes the fifth hold;
`release_holds.json` is the current hold list. Construction-side audit files
remain prohibited extractor inputs.

Both C44 jobs have live compute workers, not merely a sleeping parent process.
The selection-on job's first two chains are around iterations 6,900 and 6,800
of 8,000, after about 4.4 hours; its second pair has not started. The separate
decision-scope control's first pair is around 5,600 after 44 minutes. These
checkpoints establish progress, not convergence or a reliable completion ETA.
Their observation sets and population-computation needs differ, so the timing
difference is not a controlled performance benchmark. No active fit is restarted.

Real-source parsing continues independently: the selected snapshot now has
57 ledgers / 8,222 measurement rows, with source-bound Solano lifecycle holds.
The next whole thread and ten CF296 workbooks are being read; the fresh C29/C44
source packet remains queued behind Reddit011. This is progress toward the
existing integrated V6 plan, not a new competing architecture.

## Current-source extraction and independent review, 00:37 UTC September 20

The fresh 22-document C29/C44 extraction is complete. The coordinator has now
read all assigned source documents as a semantic reviewer; this is declared
mixed-context development review, not blind extraction or untouched evaluation.
The source-only worker received no truth, old graphs or scores. Original parses
are preserved beside reviewed derivatives.

The parent found two omitted short-duration C29 reports, a C44 named-step fee
incorrectly treated as a whole-case total, and source-family identifiers that
conflated a program with its unrelated publications and forum threads. Preserved
revisions retain the omitted reports, correct the fee scope and default source
families to exact document identities. Explicit legal dependencies are being
restored; unknown ordering is still unknown, and renewal-before-issuance prose
conflicts are exposed rather than made into initial-case prerequisites.

Three unnamed C44 FAQ timing entries remain unaligned to named operations.
Opaque source-frontmatter activity references are not a license to consult the
hidden process graph. C29's review-like labels also do not establish five
independent operations. These are substantive reconciliation/compilation issues,
not failures of quotation integrity. No fit from the fresh packet is launched yet.

At 00:28 UTC the decision-scope fit had completed its first two chains and
started the second pair; the selection-on fit's first pair was at approximately
7,500/7,400 iterations of 8,000. Both had live CPU workers. Completion of two
chains is not four-chain convergence. The real-source snapshot separately reaches
58 ledgers / 8,291 measurement rows, and all 25 frozen administrative XLSX files
now have native extraction packets with independent parent raw-cell replay.

## Explicit block scheduling and frozen-target replay, 00:58 UTC September 20

Integrated V6 now accepts an opt-in predecessor DAG between whole blocks.
Every block must explicitly declare its predecessors, including empty lists for
roots; otherwise the historical serial default is preserved. Partial graphs,
unknown references and cycles fail validation. Internal operation order,
repeat counts, elapsed dwells and labor resources retain their existing semantics.
A repeated block remains atomic; this does not implement staff-capacity scheduling
or interleaving of repeated blocks. Supplied overlap is reported as an assumption,
never as something the model learned from missing dependencies.

The project suite passes **945 tests** (13 new scheduling checks), with one existing
generator-test return-value warning. An earlier unscoped `pytest` invocation also
collected the vendored PolicyEngine source tree and failed for its absent optional
dependency; the scoped project suite excludes that unrelated source checkout.
Neither running SK3 fit uses these new local files or was changed/restarted.

Two frozen-input diagnostics precede any timing claim:

- `runs/rw_parse_20260919/declared_order_structural_sensitivity_v1.json`
  measures the order added by the old bridge. Under equal one-unit durations and
  no extra repeats, an optimistic relaxation preserving the initial-decision
  barrier shortens C29 paths by 20–30% and C44 paths by 20–45%. An independent
  120-trace engine replay agrees. These are graph diagnostics, **not day estimates**.
- `runs/rw_parse_20260919/block_order_sensitivity_v1/` freezes an implementable,
  more conservative block-level sensitivity. It keeps all old inventories,
  observations, within-block edges, repeat structures and priors, retaining the
  initial-decision barrier and serial post-decision blocks. Only relative order
  between pre-decision blocks is relaxed, explicitly as an optimistic hypothesis.

At 32 frozen states per program the unchanged default replays saved likelihoods
within 2e-13. Both schedules have identical latent layouts (C29: 155; C44: 346).
C29's operator dependencies establish an exactly invariant likelihood: its
informative timing operators observe single-visit durations, selection is off,
and no cohort or rate factors add schedule dependence. All 32 changed-schedule
likelihood differences are exactly zero. Its draws can therefore support a
conditional scheduling sensitivity without rerunning MCMC; the evidence cannot
choose between these schedules. C44 has whole-case clocks and its likelihood
changes (up to 4.76 at these fixed states). Its old draws **cannot** be presented
as a posterior for the relaxed schedule; that requires a matched refit.

This isolates a structural-assumption problem rather than claiming that more
sampling or favorable comparison to truth repaired it. Fresh-source reconciliation
is still separate, and optimistic parallelism is not a replacement default.

### C29 conditional prediction check and C44 matched refit, 01:11 UTC

`runs/rw_parse_20260919/c29_order_posterior_sensitivity_v1.json` evaluates the
same 128 retained draws per chain under both schedules. For this 512-draw subset,
the posterior median of the population's median decision time is 78.7 days
under the serial control and 62.7 under the optimistic block schedule. The median
**paired ratio is 0.811**, with a 90% interval of 0.585–0.962. This subset's
serial summary is not a replacement for the archived full-fit report. The relaxed
clock's 90% posterior interval remains wide, 25.7–247.9 days. Functional R-hat
is below 1.002 and bulk ESS above 485 on the retained subset; 32-state repeated
and doubled prediction-grid checks change its median clock by at most 1.12%.
These are conditional sensitivity diagnostics, not a new full approximation audit.
The likelihood is identical: **these data cannot decide which schedule is right**.

The corresponding C44 target is different, so a matched four-chain fit was
launched at 01:07 UTC in its own source-evidence-only SK3 stage:
`/lfs/skampere3/0/alexspan/regulatory-complexity-v6/block-order-20260920.202fl4en`.
Local protocol, hashes and launch receipt are in
`runs/rw_parse_20260919/block_order_ablation_stage_v1/`.
It uses the same 2,000 warmup / 6,000 retained draws, population 8,192, seed,
priors, observations, inventory/path weights and within-visit phases as the
archived control; only the explicitly supplied block dependencies change.
Source selection remains off and the three-observation decision-scope repair is
not included. No truth, scores or posterior states were uploaded. Both workers
are live, and neither of the other running fits was altered. Compare all numerical
gates and standard burden metrics when complete; do not combine the three
distinct interventions or select a graph merely for approaching development truth.

### Task-specific prior interface and regression checks, 01:30 UTC

Phase 1c now has an opt-in implementation in integrated V6:
`Config.elapsed_task_prior_medians`, exposed by the runner as
`--elapsed-task-priors <file.json>`. It changes only fixed elapsed log-location
baselines per task. The hierarchy scales, case variation, scheduling, labor
channels and parameter count stay unchanged. A supplied file must declare the
complete-visit calendar-day clock, positive medians and a rationale. Its bytes
are hash-bound as an input and its contents are copied into the immutable run.
Unknown task names fail; omitted tasks visibly retain the global fallback.
Preflight and posterior reports disclose the baselines and their supplied status.

This is **mechanics, not prior calibration or a recovery result**. Complete-visit
elapsed time includes waiting. A payment taking minutes of active work does not
establish a minutes-long elapsed payment visit. No new task median has been
selected from development truth or applied to the three running experiments.
An independently justified elicitation or explicitly labeled sensitivity protocol
is still needed before this option earns an empirical claim.

The scoped project suite passes **969 tests**, with the same pre-existing
generator return-value warning. The 24 added tests include input/clock/provenance
validation, unchanged historical parameter formulas, labor-channel separation,
JSON round trips and both sampler kernels with nonzero offsets. A separate
current-code replay checks 32 archived control states per program: maximum
likelihood errors are 1.42e-14 for C29 and 1.99e-13 for C44, with unchanged
dimensions. Receipt:
`runs/rw_parse_20260919/task_prior_default_target_replay_v1.json`.
