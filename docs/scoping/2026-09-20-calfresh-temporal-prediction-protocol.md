# CalFresh real-data temporal prediction, protocol v1

Frozen on 2026-09-20 before this coordinator reads the August2025–July2026
target category values. This is an **exploratory temporal evaluation**, not an
untouched blinded test: other parsers previously extracted the whole workbook,
and earlier July analyses have informed model development. No claim that no
agent ever saw these labels is made. Predictions use July alone, no later-month
counts, no synthetic data, and no retrieval.

## Fixed source, meaning and coverage

Use the captured `corpus/counties/raw/calfresh_cf296_july2025_ongoing.xlsx`
(SHA256 `23a57796e9936f8852c396eee6d098ef02c6daf0fbd8f7019bf525497c72972c`).
The source-only native extraction identifies13 months, July2025–July2026,
58 counties plus the dependent statewide row. The workbook's captured release
notes label these reporting months “All reporting”; this is not evidence that
each county reported all eligible cases or that a zero denotes zero events.
It is one retrospectively released snapshot (2026-08-24), not a replay of data
available to a July2025 forecaster. Revision-vintage leakage is not excluded.

Only cells30/33/36/39 (AK/AN/AQ/AT) enter: total recorded expedited-entitled
reports, issued within3 calendar days, days4–7, and after7days. Apply the
[already reviewed source meanings](../../runs/three_family_20260920/calfresh_all_county_admission_review_v1/report.md):
application to benefits issued, with reporting month assigned on disposition.
Do not use the new overdue-aging fields with unresolved clock definitions.

Replay every targeted native cell against the original XLSX; preserve blanks,
suppression, source errors and zero flags without imputation. Check every county
total equals its bins. Check statewide against county sums where all needed
values are numeric; retain it as a dependent check, never another likelihood
factor. Retain all58×13 rows whether eligible for evaluation or not.

## Train/test separation and zero semantics

Training is exactly July2025. The primary46 training counties are those in the
already frozen positive-bin V6 input. Hold that county set fixed; do not use
future outcomes to choose new training counties or tune priors/scales.

Target months are **all twelve** August2025–July2026. Primary scoring requires
all three target bins positive numeric integers and a consistent positive sum.
Other county-months are held, itemized, and counted in the evaluation denominator.
This is an explicitly **outcome-conditioned evaluation subset**: it cannot
estimate unconditional predictive calibration or represent all future counties.
Positive values themselves still do not establish complete reporting.

Report separately a literal-zero sensitivity on otherwise valid numeric
county-months. That strong assumption does not release reporting-zero holds.
The all58 model condition is sensitivity only and gets its own matched all58
baselines and denominator. Never compare methods on different target rows.
No suppression/blank/error is silently converted to zero, and unknown target
sample size or an inconsistent total makes a row unscorable.

## Fixed comparators and score

For every primary eligible county-month, compare:

1. **July county empirical proportions:** three recorded July counts divided
   by their sum; no fitted parameter or future data.
2. **July county Dirichlet(1/2,1/2,1/2):** predictive mean
   `(count + .5)/(n + 1.5)`, a simple nonhierarchical Bayesian comparator.
3. **July pooled proportions with .5 pseudocount per bin:** pool the exact same
   training county set. This uses the same cross-county information available
   to V6, but no county effects. Pseudocounts are fixed, not tuned.
4. **Every frozen V6 condition:** posterior mean of the three bin probabilities
   from July draws (not the median of each bin). Initial failures remain visible.
   Score only a numerically eligible initial fit or its sole preauthorized
   continuation; no condition chosen for good future performance. If unavailable
   or still failing, report it unscored and continue the other comparisons.

The primary score is conditional categorical log loss per recorded report:

`-sum_b target_count[b] * log(predicted_probability[b]) / target_n`.

Lower is better. This is a proper score for the predicted mean category
probabilities, not the joint predictive probability of a whole cohort. It avoids
claiming accurate extreme-tail Monte Carlo integration of a large multinomial
count vector. For an empirical zero prediction with positive observed count,
retain infinite loss explicitly, not an arbitrary epsilon. Use no target counts
to smooth a prediction.

Report raw per-county-month scores and paired differences, then unweighted
county-month and within-month averages **over the declared matched frame**.
These averages are not statewide burden or population-weighted estimates.
Do not give a standard error that treats twelve repeated observations of the
same county as twelve independent counties. Keep time-series dependence and
conditioning explicit; no significance claim is prespecified.

## Adequacy, uncertainty and next decisions

Also report source bin fractions and absolute prediction errors per bin. Bin
counts from V6's July in-sample PPC remain in-sample; they are not temporal
coverage. A future predictive-interval exercise must condition on the target n,
declare overdispersion/time drift and its independent-case assumption, and be
reported separately. This protocol does not add temporal dynamics, calibrate
source bias, or prove complete reporting.

Freeze this protocol before extracting target counts. Hash it, the extraction
code, source workbook, July input, native ledger and outputs in the additive
`runs/three_family_20260920/calfresh_temporal_prediction_v1/` packet. Store the
complete source row ledger and baseline predictions/scores even when V6 fails.
Any later model redesign or changed scoring rule is a new version with explicit
exposure to these evaluation outcomes; do not retroactively label it held-out.

This test asks whether the July conditional category distributions transport to
later recorded cohorts. It cannot establish source trust, intrinsic agency
delay, applicant labor hours, or LLM superiority. A same-document LLM comparator
is still separate outstanding work; these baselines test whether a complicated
timing model adds predictive value over the original administrative counts.
