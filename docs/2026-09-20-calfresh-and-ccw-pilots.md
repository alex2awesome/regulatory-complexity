# CalFresh and concealed-carry: bounded real-data pilots

2026-09-20, 15:35 UTC checkpoint. These are integrated **V6** runs, not new
architectures, a completed three-family study, or an LLM comparison. Inputs,
assumptions and sensitivities were frozen before their fits, after the source
values had been reviewed. Independent CCW result review has passed with the
qualifications below. CalFresh's single allowed continuations and separate-agent
independent result review have also finished, with the same narrow release
boundary.

## Concealed carry: an observable phase, not agency speed

The primary result is four source-reviewed calendar differences:
**15, 22, 57 and 62 days** from reported pre-training approval to completion of
outside-provider training/classes. Their empirical sample median is **39.5
days**. They include applicant/provider scheduling; they are not agency-only
delays, and training need not universally follow approval.

All 48 labels from the fixed source registry are retained: four included
histories and 44 reasoned exclusions. Each history supplies one individual
observation, with date-resolution bounds `[d-1,d+1]`. The model conditions on
this reported-history frame, not on an unselected county-applicant sample.
Agency/task/operation/source offsets and selection corrections are fixed at
zero, with their lack of identification stated explicitly. Source zero is a
coordinate convention, not evidence of truthful or unbiased reporting.

The [frozen protocol](scoping/2026-09-20-ccw-conditional-phase-pilot-protocol.md)
has six configurations, each with four chains, 1,000 warmup and 2,000 retained
draws per chain. All six initial runs passed runner and transformed-quantity
numerical checks. Independent source/input review is
[sealed](../runs/three_family_20260920/ccw_reported_phase_pilot_independent_review_v1/report.md).

| Prespecified assumption | Model-distribution median, days | 90% posterior interval |
|---|---:|---:|
| Base | 31.3 | 16.4–56.9 |
| Alternative location prior | 32.4 | 18.1–58.4 |
| Wider between-history spread prior | 29.9 | 12.7–66.5 |
| Wider reporting error | 30.6 | 14.6–63.0 |
| No contamination component | 31.2 | 16.5–57.3 |
| Additional one-day reporting uncertainty | 31.3 | 16.4–57.8 |

These are posterior summaries of the working **lognormal distribution's
median parameter**, not the empirical median of the four dates, a mean time,
or a countywide estimate. Similar central values do not establish correct
tail shape or population coverage. Raw histories remain primary.

Under the base assumptions, marginal prior-variance contraction is about 96%
for log-location and 35% for log-case-SD. With wider reporting error, the latter
falls to 18%: the process spread and reporting uncertainty cannot be cleanly
separated by four histories. That condition is explicitly descriptive and
prior-determined under the prespecified screen. Contraction is not a complete
identification test. Reported-log-duration predictive checks include the
declared Student-t reporting error and contamination, not just latent times;
their compatibility with four observations does not validate reporting
selection or source honesty. The observed predictive-check statistics use the
four date-difference **midpoints**, whereas the likelihood uses date-resolution
intervals. This is a descriptive midpoint-conditional check, not an
interval-integrated validation.

Results and exact configurations:
[successor input](../runs/three_family_20260920/ccw_reported_phase_pilot_preflight_v1/README.md),
[six fits](../runs/three_family_20260920/ccw_reported_phase_fit_v1/launch_receipt.json),
[analysis](../runs/three_family_20260920/ccw_reported_phase_analysis_v2/analysis.json),
[independent results review](../runs/three_family_20260920/ccw_reported_phase_analysis_v2_independent_review_v1/report.md),
[qualified root consumption](../runs/three_family_20260920/ccw_reported_phase_root_consumption_v1/receipt.json).
The reviewer independently reproduced transformed arrays, diagnostics,
likelihoods and predictive simulations; root rehashed its 217 accessed paths
and all principal outputs (220 unique files, no mismatches).
The analysis's internal `scientific_release_guard` names concern its local
numerical/binding checks; they do **not** release the overall study or establish
synthetic recovery, empirical source calibration, or superiority to a baseline.

## CalFresh: numerical convergence and model adequacy differ

The input retains all twelve preselected counties and 6,784 recorded categorized
reports for July 2025. Each county supplies one three-bin histogram for calendar
time from application to expedited-benefit issuance: `[0,3]`, `(3,7]`, and
`(7,infinity)`. The report month is assigned on disposition; this is not an
application-receipt cohort, approval clock, or all-applicant distribution.

RZ-LITERAL deliberately assumes complete categorization and literal observed
zero counts. It does not resolve the San Benito, Sierra and Lake source holds:
their zeros may instead reflect unavailable/untracked activity. The published
total is sum-defined, not independent confirmation of population completeness.
Root replayed [48 original workbook cells and three clock/cohort quotations](../runs/three_family_20260920/root_calfresh_prefit_review_v1/receipt.json).

| Prespecified initial run | Runtime | Numerical result |
|---|---:|---|
| Base, learned shared spread | 104.7 s | Failed convergence; 14 diagnostic flags |
| Tighter county pooling | 102.2 s | Failed convergence; 29 diagnostic flags |
| Spread fixed at 0.8 | 76.2 s | Passed, including all 36 bin-probability diagnostics |

All three passed exact-integration checks. The two failed initial runs remain
intact. Each received only the protocol's one allowed additional 4,000 draws per
chain, with unchanged likelihood, data, priors and fresh continuation RNG.
The base now passes runner and all 36 bin-probability gates at 24,000 retained
draws. Tighter pooling still fails: 16 runner flags and two bin-probability
flags. No second extension was run or is authorized under this protocol.
Fixed spread remains the original 8,000-draw fit. Both extensions preserve
their exact initial draw prefixes and replay 200 saved likelihoods with zero
difference. These results do not select a preferred assumption.

The converged fixed-spread condition nonetheless underpredicts the recorded
slow tail. For example, Sacramento reports **156 cases over seven days**,
where its model predicts a central 90% count interval of **26–47** (median 36).
For days four through seven, the source count is 140 versus a predicted 289–366.
Root replayed all 36 probability/predictive intervals from the saved 8,000
draws; 11 observed bin counts lie outside their individual central 90% predictive
intervals. This is a descriptive, in-sample model-check discrepancy, not a
calibrated multiple-testing result. It is not a reason to select an unconverged
alternative, but it prevents calling the fixed-spread model adequate merely
because its sampler converges.

The now-converged learned-spread base is compatible with more of the recorded
bins: Sacramento's over-seven-day predictive interval is **114–166** (median
139), compared with 156 recorded. This is an in-sample comparison under the
same strong reporting assumptions, not a baseline win or proof that the
lognormal tail is correct. Independent reproduction confirms one of 36
recorded counts outside its individual central 90% predictive interval:
Shasta over seven days has one recorded versus a predicted 2–12. This is not
a simultaneous-coverage or multiple-testing result.

The separate [mixing diagnostic](../runs/three_family_20260920/calfresh_initial_mixing_diagnostic_v1/report.md)
finds strong negative association between the shared spread and common county
log-location. The sampler updates them conditionally rather than jointly along
that slow direction. Tighter pooling worsens this coupling. That diagnostic
uses unconverged draws only to examine computation; it supplies no accepted
county posterior. Its raw-rate likelihood optimization is a separate
shape-compatibility diagnostic, not a Bayesian refit or a calibrated test.

A subsequent [source-free joint-sampler prototype](../runs/three_family_20260920/histogram_joint_sampler_design_v1/final_report.md)
passed its target-consistency checks but produced mixed performance: common
location ESS improved about 20%, while shared-spread ESS fell about 28% and
all four upper-tail-bin ESS values worsened. Its first reference-harness
rounding failure is preserved; a narrowly repaired, fixed-budget rerun supplies
these results. **It is not integrated into V6 and no real refit follows from it.**
This computational experiment changes neither the completed real protocols
nor the CalFresh interpretation above.
The [separate-agent sampler review](../runs/three_family_20260920/histogram_joint_sampler_independent_review_v1/report.md)
reproduces the result and corrects a cost-accounting detail: reported
"accounted calls" include no-op increments and omit initial evaluations. Its
reconstructed actual-call normalization leaves the mixed/negative conclusion
unchanged. Author-side validation is not counted as that independent review.

Receipts: [initial analysis](../runs/three_family_20260920/calfresh_rz_literal_analysis_v2/analysis.json),
[root predictive replay](../runs/three_family_20260920/root_calfresh_ppc_spotcheck_v1/receipt.json),
[bounded continuation protocol](../runs/three_family_20260920/calfresh_rz_literal_extension_launch_v1/protocol.json),
[side-by-side continuation analysis](../runs/three_family_20260920/calfresh_rz_literal_extension_analysis_v1/analysis.json),
[separate-agent independent review](../runs/three_family_20260920/calfresh_rz_literal_extension_independent_review_v1/report.md),
[qualified root consumption](../runs/three_family_20260920/calfresh_rz_literal_root_consumption_v1/receipt.json).
The independent reviewer reproduced all-draw likelihoods, probabilities,
predictive draws and diagnostic surfaces; root rehashed all 164 accessed paths
plus principal outputs (167 unique files, no mismatches). The earlier
`extension_review_v1` is runner-author validation despite its schema name,
not this separate-agent review. The analysis field
`eligible_for_scientific_reporting` is consumed only as **local numerical
eligibility**, not model adequacy or study release.
No statewide estimate, county ranking, precise within-bin/tail duration mean,
labor, fee, source-trust or intrinsic-agency claim is released here.

## What this adds to the source-trust work

Known administrative counts can strongly constrain recorded-category
probabilities without establishing source completeness or a correct duration
shape. A handful of forum histories can constrain a conditional timing
location while leaving the decomposition of process spread and reporting
error prior-sensitive. Those are different uncertainties, and the pipeline
now keeps them distinct. Neither pilot identifies a cross-source bias or
supports a credibility ranking. Matched synthetic recovery and same-information
baselines remain unfinished.
