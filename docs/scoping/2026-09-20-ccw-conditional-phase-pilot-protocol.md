# CCW reported-phase pilot: fixed small-sample sensitivity protocol

Frozen before any CCW conditional-phase fit on 2026-09-20. This is an
**outcome-informed development analysis**, not preregistration before seeing
the four durations, a held-out evaluation, or population recovery.

## Target and immutable evidence

Use only the four source-reviewed histories in the
[design packet](../../runs/three_family_20260920/ccw_reported_phase_pilot_design_v1/README.md):
15, 22, 57 and 62 calendar days from reported pre-training approval to
outside-provider training/class completion. Preserve all 48 original registry
labels: four included episodes and 44 reasoned exclusions. The
[root source review](../../runs/three_family_20260920/root_followup_review_1425/receipt.json)
confirms Jonty's separate January 11 approval post; the admitted successor must
include `ev_jonty_approval`, not rely on the ambiguous qualification-notice
label alone. The original proposed input remains unchanged.

The target is the conditional distribution of these eligible reported
histories under the declared artifact frame. It is not the applicant
population, all forum users, county performance, an intrinsic agency delay,
or a universal dependency. Training could precede approval in other histories.
This interval includes applicant scheduling and provider availability.

Each episode supplies one individual elapsed observation, not a population
median or an independent observation per quotation. Two date-only endpoints
give the primary continuous-duration interval `[d-1,d+1]`. No extra outcome,
denominator, source, or case may be added by fitting.

## One integrated model and fixed assumptions

Use V6's reviewed `census_within_declared_conditional_frame` mode: one
aggregate phase, unknown/mixed actor, no decision marker, one source family,
one route, elapsed channel only. Keep all episode IDs. Ordinary QMC mode
retains case latents; do not mislabel the observations as summaries to enable
the analytic-population mode.

Fix agency, task, operation, common-case, source and selection scales to zero.
The source zero is a report-frame reference convention, not learned honesty;
selection is conditioned on rather than corrected. Use the blocked hierarchy
sampler. No source hierarchy, comparison factor, cohort summary, rate, path,
repetition, dwell, cost or labor likelihood is admitted.

The base assumptions are elapsed prior median 7 days, location log-scale SD
2, case log-SD median 0.6 with log-prior SD 0.4, report Student-t scale 0.25,
and contamination 0.05. These are declared historical defaults, not calibrated
source precision. The tiny sample cannot separately identify process spread,
reporting noise and outlier frequency.

## All six configurations, no winner selection

| ID | Difference from base | Interpretation |
|---|---|---|
| `base` | None | Historical broad prior and report assumptions |
| `location_prior_30_sd1` | Location prior median 30 days, log-SD 1 | Joint alternative prior; not a one-factor attribution |
| `spread_prior_1` | Case log-SD prior median 1.0 | Greater a priori episode heterogeneity |
| `report_scale_0_5` | Report Student-t scale 0.5 | Less precise recollections, not learned forum unreliability |
| `contamination_0` | Contamination 0 | No broad-error component |
| `extra_day_uncertainty` | Observation interval `[d-2,d+2]` | Additional one-day endpoint/report ambiguity beyond date resolution; not an alternate source fact |

Preserve all six outputs, including failures. The raw four values remain the
primary descriptive result. Do not choose a configuration because its estimate
looks plausible or its interval is narrow. Broader report/date uncertainty
changes the measurement assumption, not the observed calendar differences.

Each configuration: four independent chains, 1,000 warmup and 2,000 retained
draws per chain, population size 4,096, cohort quadrature size 256 (unused),
native calendar days, case-path scale zero (unused), seeds 2026092061 through
2026092066 in table order. Worker threads are limited independently of this
scientific contract. Require exact saved Config/CLI equality and immutable
code/input/protocol bindings before launch.

## Gates, one bounded extension, and outputs

Require finite likelihoods, R-hat at most 1.01, bulk ESS at least 400 and
tail ESS at least 200 for sampled and reported quantities, plus the runner's
likelihood-weight and less-than-2% clock-quantile refinement checks. One
additional 4,000 draws per chain is allowed only for a failed numerical gate,
with identical target and fresh continuation RNG; retain the failed initial
report. No second extension or silent prior adjustment is permitted.

After code/semantic review and successful numerical gates, report the four
date differences, the sparse conditional distribution's location/spread
uncertainty, and side-by-side sensitivity changes. Inspect prior-to-posterior
contraction and posterior predictive compatibility without claiming that fit
checks validate selection, source honesty, or population representativeness.
If the sparse data leave those distribution parameters prior-determined, say
so; the descriptive histories remain valid without a fitted headline.

Never report primitive step counts, agency-only speed, all-applicant times,
an extrapolated county ranking, a source-trust ranking, or an LLM victory.
This fit is a bounded mechanics-and-evidence integration pilot inside the
three-family study, not its completion.
