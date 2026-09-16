# Bayesian v5: development results and clock-contract defects

**Post-audit qualification:** on the three source ledgers, selection strength
remained close to its prior. The selection-enabled estimates are sensitivity
results under that prior, not evidence that these documents identify the
selection mechanism. The correctly specified recovery fixtures show what can
happen under their assumptions; they do not establish that the source-ledger
data adjudicate between the variants. V5 is an archived control, not a parallel
candidate to keep tuning. [Audit response and next work](2026-09-16-bayesian-audit-implementation.md).

2026-09-16. Continuing the Bayesian route; **the accuracy/full-burden objective is
not achieved**. The smaller timing channel improves some comparisons and worsens
others. A newly discovered benchmark clock mismatch also prevents treating the
legacy scores as an equal-estimand accuracy test. No old observations, outcomes or
scores have been rewritten. [Model](2026-09-16-bayesian-process-v5.md),
[protocol and subsequent clock erratum](2026-09-16-bayesian-process-v5-protocol.md).

## Completed whole-process experiments

Both variants integrate same-case observations, source offsets, uncertain clocks,
and ambiguous completion. Only the second models delay-dependent forum selection.
These fit whole-process timing directly rather than adding overlapping stage spans.
All six final fits pass the specified chain diagnostics and doubled-resolution
integration check. Each has four chains and 3,000 retained draws per chain.

**Clock warning:** the estimators were prompted for initial decision; the legacy
comparand below uses last recorded decision. Retain these as development diagnostics,
not evidence of validated accuracy on the requested clock.

New invocations of `compare_process_measurement` require
`--allow-legacy-clock-mismatch` to produce these development diagnostics and
explicitly mark them `usable_for_accuracy_validation: false`. Numerical usability
is a separate field. Old comparison artifacts are preserved, not rewritten.

| Program | Legacy event-log median, days | No delay selection: median (90% interval) | With selection | Matched LLM, three repeats |
|---|---:|---|---|---|
| J1/S01 | 128 | 97.65 (65.24–146.00) | 84.85 (52.36–130.98) | 140 / 135 / 140 |
| J1/S03 | 74 | 78.79 (50.15–129.91) | 65.69 (34.49–111.03) | 75 / 75 / 75 |
| J2/S07 | 21 | 33.06 (18.88–58.95) | 26.81 (13.49–50.21) | 30 / 30 / 28 |

Across these three programs, mean absolute log error is **0.2624 / 0.2581 / 0.1415**
for no-selection Bayes / selection Bayes / matched LLM. Mean proper 90% log-interval
score is **0.9654 / 1.1334 / 1.3706**, respectively; lower is better. Bayesian
interval scores are better on average, but point errors are worse. This fails the
prespecified requirement to do at least as well on both. Do not pick the favorable
solar row and call the whole model better.
[Saved precision-checked comparison](../runs/bayes_v5/comparisons/whole_process_precision_checked/comparison.json).

The two initial solar fits passed MCMC diagnostics but failed quadrature checks:
256 versus 512 nodes changed checked log likelihoods by up to 0.0319 / 0.0491,
above the 0.01 threshold. Independent 512-node refits reduced the checked changes
to 0.00416 / 0.00169. Both initial attempts remain saved and marked unusable.
[Initial comparison including failures](../runs/bayes_v5/comparisons/whole_process_initial/comparison.json).

An earlier completed-only S03 pilot kept four explicitly completed cases and
excluded five ambiguous ones. Its no-selection / selection estimates were
68.85 / 56.59 days, with 90% intervals 38.65–123.18 / 27.10–103.78. Both passed
numerical checks, but excluding ambiguous stories is itself consequential
selection. The subsequent latent-completion variants above retain those reports.
[Preserved pilot comparison](../runs/bayes_v5/comparisons/completed_only_pilots/comparison.json).

The same-input LLM repeats are relatively stable here. These three repeats do not
establish general reproducibility, but neither do they support claiming the LLM
is intrinsically erratic on this fixed ledger. Bayesian simulation error is
measurable and reducible; extraction/model uncertainty remains separate.

## Outcome-stratified extension

The next variants distinguish approval and denial duration distributions, condition
known-outcome stories without treating their frequencies as a population survey,
and use valid administrative decided-cohort counts. The source audit identifies
137 issued / 37 denied in S01, while correctly declining to use S07's 18 issued /
81 received as a decided-case approval rate. It also resolves the news story's
unfinished initial decision, which becomes a censored observation, not a completed
35-day case.

The first four-chain, 3,000-draw fits passed the integration check but each narrowly
missed one chain-convergence threshold (R-hat 1.01086 and 1.01013). Extending each
to 7,000 retained draws per chain, with unchanged inputs and priors, fresh random
streams and an exact likelihood-invariant source/location Gibbs move, passes all
chain checks. The doubled-resolution integration changes are 0.00182 / 0.00079.
Their fresh joint
LLM controls, given all the same sidecars, return 140 / 75 / 35 days in all three
repeats. Those are different-input controls from the preceding table and must not
be interchanged.

| Program | No delay selection: median (90% interval), days | With selection | Matched LLM |
|---|---|---|---:|
| J1/S01 | 101.66 (57.40–174.98) | 84.44 (42.32–152.62) | 140 |
| J1/S03 | 81.06 (48.01–140.50) | 67.43 (33.14–123.20) | 75 |
| J2/S07 | 35.94 (19.70–65.65) | 30.24 (14.70–57.20) | 35 |

On the same legacy-clock comparison, mean absolute log errors are
0.2863 / 0.2912 versus the matched LLM's 0.2046. Mean 90% log-interval
scores are 1.1307 / 1.3180; the matched LLM's score is 1.2442. This extension
does not meet the accuracy objective either. Its better treatment of outcome
evidence is not, by itself, evidence of more accurate timing estimates.
[Saved outcome-aware comparison](../runs/bayes_v5/comparisons/outcome_precision_checked/comparison.json).

## Partial-preparation extension

This extension uses 29 additional source-audited pre-filing timing claims:
16 / 4 / 9 in S01 / S03 / S07. Four S01 groups contain at least two usable,
source-supported disjoint spans. Unresolved overlap is not forced into either a
sum or parallel execution. Every span shares its case duration, outcome and
source offset with that applicant's other reports. Partial coverage has an
explicit prior and an unobserved remainder; a short service appointment is not
silently treated as the entire preparation period.

The no-delay-selection fit passes four-chain diagnostics at 6,000 retained draws
per chain, and its 512-to-1,024-node integration check changes the log likelihood
by at most 0.000480. Its fresh matched LLM receives all twelve input files,
including preparation sidecars; earlier baselines are not interchangeable.

| Program | No delay selection: median (90% interval), days | Matched LLM, three repeats |
|---|---|---|
| J1/S01 | 115.65 (68.80–195.70) | 140 / 140 / 140 |
| J1/S03 | 82.15 (49.74–138.34) | 80 / 75 / 80 |
| J2/S07 | 31.48 (18.53–54.84) | 35 / 35 / 35 |

Mean absolute log error is **0.2036 versus 0.2190** for the matched LLM;
mean 90% log-interval score is **1.0512 versus 1.2071**. This is a small
average improvement on both measures, driven by S07: Bayesian point error is
still worse on S01 and S03. These are three repeatedly inspected development
programs, not a new holdout, and the legacy clock mismatch still applies.

The initial selection-aware preparation fit passes chain diagnostics but fails the
integration check: 512 versus 1,024 nodes changes the checked log likelihood by
0.03093, above the unchanged 0.01 threshold. Its estimates are preserved but
not usable for accuracy claims. A 1,024-node refit, with unchanged inputs and
priors, passes the four-chain checks and the 2,048-node comparison (maximum
checked change 0.001814). Its estimates are:

| Program | With delay selection: median (90% interval), days |
|---|---|
| J1/S01 | 99.04 (48.83–171.45) |
| J1/S03 | 66.65 (32.88–118.99) |
| J2/S07 | 26.92 (14.55–48.13) |

Its mean absolute log error is **0.2031**, slightly below the matched LLM's
0.2190, but mean interval score is **1.2460**, worse than 1.2071. It does not
beat the control on both measures. Reusing the same random streams happened to
retain identical parameter states across the two numerical resolutions; their
saved likelihoods differ. This is a precision refinement, not an independent
statistical replication. An independent adaptive-integral check finds a 0.0291
error at the old grid's worst prespecified check state, versus 0.00180 at the
refined grid. A targeted check of the largest old/new discrepancy among all
24,000 saved states finds refined-grid error 0.00200. Those extra checks support
the numerical refinement, not the model's assumptions or benchmark accuracy.
[Initial preparation comparison, including the flagged fit](../runs/bayes_v5/comparisons/preparation_initial/comparison.json).
[Precision-checked comparison](../runs/bayes_v5/comparisons/preparation_precision_checked/comparison.json).

This mechanism still assumes the same preparation fraction of total duration
for every case within a program. Its coverage prior also depends on the number
of separately reported spans. Neither assumption is established by the text.
For the solar 313-day story, the posterior mean probability of the broad
report-error component increases from 0.308 to 0.645 after adding preparation
claims (comparing no-selection models). This is a **model-conditional conflict
diagnostic, not proof that the source is wrong**: real variation in preparation
versus review time could create the same conflict. Further work must check that
the apparent accuracy improvement is not bought by an overly restrictive phase
model dismissing inconvenient reports.
[Before](../runs/bayes_v5/diagnostics/outcome_unselected_reports/attributions.json),
[after](../runs/bayes_v5/diagnostics/preparation_unselected_reports/attributions.json).

## Why more data is not automatically the cure

A separate, deliberately favorable selection-component recovery test uses known
case variability and exact clocks. With true median 30 days, ignoring selection
gives average estimates 43.31, 42.06 and 41.51 days at 10, 100 and 1,000 independent
cases. Modeling selection gives 33.43, 31.23 and 29.95 days. Ignoring selection
covers the target in 14/32, 0/32 and 0/32 nominal 90% intervals; the selected model
covers in 30/32 at each size. This is **not full-pipeline calibration**, but it
demonstrates systematic error that more observations can make more confident.
[Saved recovery experiment](../runs/bayes_v5/validation/selection_grid/summary.json).

The real development inputs have about nine case stories per program, mostly in
three forum threads. Ten documents are not ten independent population samples,
and hundreds of documents copying the same cases would not become hundreds of
independent observations. Low data and selection/measurement misspecification
are different problems.

A second recovery experiment also learns case variability (the preceding grid
test fixed it). Sixteen paired datasets per condition share nested selected
samples and, where present, 20 independent unselected administrative cases. All
64 four-chain fits pass the numerical diagnostics. The true median is 30 days.

| Selected cases | Unselected admin cases | Mean absolute log error | Mean 90% log-interval score | Coverage |
|---:|---:|---:|---:|---:|
| 10 | 0 | 0.1720 | 0.9710 | 16/16 |
| 100 | 0 | 0.0790 | 0.5946 | 15/16 |
| 1,000 | 0 | 0.0266 | 0.1147 | 14/16 |
| 100 | 20 | 0.0571 | 0.3096 | 13/16 |

This supports both more independent cases and a differently sampled source.
Adding 20 administrative cases improves average error and proper interval score
relative to the paired 100-selected-case condition, but its empirical coverage
is only 13/16. Sixteen replicates, one fixed parameter setting, exact observation
clocks and a correctly specified selection family are **not a calibration
certificate**. Neither experiment measures how many text documents are sufficient,
nor compares against an LLM. The timing prior is centered at the fixed recovery
truth; no claim of broad prior-robust recovery follows.
[Unknown-spread mixed-source experiment](../runs/bayes_v5/validation/mixed_sources_unknown_spread/summary.json).

## Benchmark defects now verified

The legacy simulator overwrites the decision timestamp when a later decision is
visited. Among the same finally-decided, uncensored cases:

| Program | First-decision median | Last-decision median used by old scores | Cases with repeated decisions, out of all 200 |
|---|---:|---:|---:|
| J1/S01 | 111 | 128 | 74 |
| J1/S03 | 74 | 74 | 0 |
| J2/S07 | 17 | 21 | 45 |

These are alternative diagnostic quantities, **not replacement scores or a new
held-out success**. Their proper observation/censoring cohorts differ too: S01 has
181 observed initial decisions but only 174 observed last decisions. Simply
changing one number in a scoring file would not fix the evaluation design.
[Read-only clock audit](../runs/bayes_v5/validation/benchmark_clocks/audit.json).

Separately, S01's dashboard renderer added an acceptance-to-closeout definition to
a spec that did not provide that clock. Its quoted sample size, 182, includes eight
abandoned cases that the generated median excludes. Future dashboard specs now
name the actual last-decision clock and use the median's decided denominator;
empty cohorts do not report a fictitious zero-day median.

New generator records explicitly preserve first decision, last decision and end
of modeled work, with independent censoring and cohort summaries. End of modeled
work is not automatically legal closeout. A deterministic verification reproduced
all **600 existing cases and every legacy summary field unchanged** while adding
the new clock fields in memory. W1 itself was not regenerated.
[Compatibility verification](../runs/bayes_v5/validation/generator_clock_extension/verification.json).

Further generator checks found additional contract defects, now corrected for
future worlds:

- A completed but slow persona was described as still waiting for an update.
  Its unnoised total also appeared in the motivation alongside noisy timing claims.
  Future wording retains completion and uses only reported numbers.
- Audit excerpts claimed 20% exceeded the supplied p90. They now name the 90th
  percentile directly and retain its clock and decided denominator.
- First-visit medians and persona cycle sums could include future completions.
  New observed summaries and reports respect the observation date. First visits,
  sums of visit cycles and first-to-last stage spans carry different metadata.
- Renderer batches exposed exact persona timelines alongside intended noisy
  reports. The renderer now gets only reported amounts; verifiers retain originals.
- `r` counted a step's loop triggers, not its visits. Revisiting a filing step
  without its own loop could charge its base fee twice and miss its repeat speedup.
  A deterministic regression reproduces a $200 legacy charge versus the intended
  $100, and 38 versus 35 days. New worlds use version-2 visit accounting; old worlds
  without the version knob preserve legacy behavior.

These are benchmark changes, not improvements secretly applied to estimator input.
The new version requires a freshly rendered and audited corpus before evaluation.
Another read-only replay confirms all 600 original records and legacy summaries
remain reproducible, including their old defects.
[Version-compatibility verification](../runs/bayes_v5/validation/generator_accounting_legacy_compatibility/verification.json).

## Remaining Bayesian work

### Additional controlled joint timing/rework check

The frozen eight-replicate experiment in the v5 protocol completed all 32 grid
fits; every marginal-CDF refinement check passed. With ten whole-case times alone,
agency mean-cycle absolute log error averaged 0.240 and its proper 90% log-interval
score 0.956. Adding an independent 20-case correction cohort changed these to
0.218 and 0.730; adding five first-visit task times instead gave 0.130 and 0.578.
One hundred whole-case times gave 0.053 and 0.475. Count information can therefore
update timing through the shared joint model, rather than through an arbitrary
correction to a point estimate.

Not every metric improved: the correction cohort slightly worsened the process
interval score (0.483 to 0.503), and direct task times worsened the expected-visit
point error (0.031 to 0.042). Known noise, known continuation rate, fixed other
work and perfect within-case repeat correlation are favorable assumptions. This
is one agency/task component, not the full hierarchy or an LLM comparison.
[Saved results](../runs/bayes_v5/validation/joint_repeat_timing/summary.json).

### Rework observation defect and prospective repair

The FAQ generator labeled one checkpoint's per-eligible-visit retry probability
as the fraction of applications needing any correction. It also rounded zero or
small probabilities up to one in ten. This helps explain, but does not retrospectively
repair, the conflicting rendered FAQ/dashboard claims. New FAQ specifications
preserve per-visit units and identify a planning probability, without fabricating
a counted cohort. New dashboard specifications use timestamped observed corrections
and actual received-case numerators/denominators, including unfinished cases and
post-decision corrections explicitly. Future rework is not observable rework.
Version-2 nonblocking checkpoints also cannot start corrections before the result
triggering them. Legacy schedules remain unchanged.

The new regression suite passed, and another replay preserved every legacy field
of the 600 development cases and their summaries.
[Rework-event compatibility check](../runs/bayes_v5/diagnostics/rework_event_extension/verification.json).

### Integration, not yet a fitted full pipeline

The [v6 development protocol](2026-09-16-bayesian-process-v6-protocol.md) specifies a joint
visit/agency/task model and its next controlled test. Its trace operators distinguish
cycle sums from stage spans and first from final decisions; timing, counts and
separately supplied work amounts share the same latent repeated visits. This is
new implementation work, not a completed fresh comparison or a replacement for
the preserved results above.

The new fitted preparation channel uses partial pre-filing spans, but its common
case fraction and coverage priors still need sensitivity checks. Explicit
first/final decision clocks must replace the old ambiguous decision endpoint;
the old sum of all activity spans must not return.

The segmentation-invariant coverage-prior sensitivity fits have now both completed
their initial four chains (6,000 retained draws each). Common preparation fractions
yield process medians 116.53 / 81.44 / 31.12 days; variable preparation fractions
yield 113.67 / 82.88 / 32.95. Both pass duration/fraction quadrature refinement
(maximum checked log-likelihood changes 0.00000230 and 0.00272) but flag three and
four convergence quantities, respectively. Same-target 4,000-draw extensions were
started; the preliminary numbers were not used to select a variant or score
a new LLM comparison. These remain legacy-clock-mismatched development sensitivities.

Both 4,000-draw extensions have now completed (10,000 retained draws per chain).
The common-fraction fit passes all declared numerical gates, with process medians
117.03 / 81.41 / 31.28 days and maximum checked log-likelihood refinement change
0.00000157. The variable-fraction fit passes quadrature (0.00429) but still fails
one convergence gate: coordinate 58 has R-hat 1.01337, bulk ESS 795 and tail ESS
1,808. Its medians are 114.30 / 83.10 / 33.01 days, retained as preliminary results,
not usable accuracy evidence. No prior was selected from those scores and no
additional LLM superiority claim is made.
[Common extension](../runs/bayes_v5/timing/preparation_partition_common_extended/posterior.json),
[variable extension](../runs/bayes_v5/timing/preparation_partition_variable_extended/posterior.json).

A new source-only count/rework contract distinguishes distinct operations,
visits, extra correction rounds, total attempts and public-organization counts.
It preserves normative limits separately from observed counts, and informal
frequencies separately from real sample sizes. The quote-checked audits found
2 / 1 / 14 numerical count claims and 3 / 0 / 1 rate claims in S01 / S03 / S07,
including duplicate and normative claims that are not independent observations.
S01's FAQ says roughly 30% of applications need corrections while its dashboard
says 65%; the latter does not establish the correction cohort's size. S07's FAQ
says roughly 40%. These are case-level any-correction rates, not per-visit retry
probabilities or samples of ten. Only a few anecdotes explicitly count actual
revisions or visits, and even those can refer to applicant-side redesign rather
than an agency-requested correction. This contract is not yet a fitted route/count
likelihood; the timing experiments above do not consume these new claims.

The new visit-operator audit leaves 133/146 claims partially unresolved and flags
12 uncertain activity mappings. That does not mean the claims contain no useful
information: their durations and named activities can be informative while visit
aggregation or exact starting/ending events remain uncertain. In particular, old
rendered task durations generally do not explicitly state whether they sum
multiple visits. No visit-cycle sum is asserted by this source-only audit merely
because the hidden generator used that operator. The older outcome audit also
interprets the solar news subject as awaiting an initial decision, whereas the
new clock audit retains an unspecified unfinished event; "case still open" and
wanting a letter do not by themselves prove a particular decision timestamp.
The saved fits remain conditional on the older audit; no evidence was silently
changed after observing scores.

Agency/task pooling, separate work-hour channels and their controlled recovery
remain available in v4. This iteration does not validate operation counts,
uncertain agency identity, repeated-visit counts or labor, and has not yet joined
the new timing channel back to that hierarchy. No alternative non-Bayesian
estimator has been substituted for the requested Bayesian effort.

The [visit-clock contract](2026-09-16-bayesian-visit-clocks.md) now provides tested deterministic operators for a realized trace:
first/last decision, explicit first filing, cycle sums, stage spans, wait/service
intervals, distinct operations versus visits, and separately supplied labor/fees.
Unknown agencies and missing labor do not become tight zero estimates. This is
infrastructure for a visit-based Bayesian hierarchy, **not** a newly fitted full
burden posterior; integration with that hierarchy remains unfinished.

All source interpretation uses pinned Codex calls with strict schemas and verbatim
quote validation; no scores or hidden log facts are supplied. The model/skill
guidance kept those calls pinned and reproducible rather than changing models
between variants. Runs and raw outputs are under `runs/bayes_v5/` and are locally
gitignored; they must be archived with any published results.
