# SolarTRACE: a source-faithful, numerically usable V6 phase pilot

2026-09-20. **Provisional descriptive analysis, not a released benchmark result.**
This closes a small source-to-fit loop while the approved three-family study
continues. It does not establish Bayesian superiority, source-type trust, or
complete parsing of the solar corpus.

## Input and estimand

The [source packet](../runs/three_family_20260920/solar_coarse_pilot_v1/README.md)
contains twelve deduplicated AHJ medians for **first permit submission through
final permit approval**, including resubmissions. Units are **business days**,
not calendar days. Inspection, utility interconnection and whole-project clocks
are not included.

Selection used metadata, not favorable timing values: the widest common
year/size/technology stratum was 2022 / 0–10 kW / PV-only, with 401 identifiable
AHJs. Stable owner IDs were SHA256 ordered and the first twelve selected.
Coverage of all 440 owners is retained in the packet. Each modeled operation
is explicitly an aggregate phase, not a primitive applicant step.

The adjacent AHJ–utility installation count is **not** the phase-median sample
size. We leave n unknown. Each published median y supplies the interval
`[max(0, y − 0.5), y + 0.5]` business days. This is a declared likelihood floor,
not a source confidence interval or a verified rounding algorithm. The one
published zero is retained as `[0, 0.5]`; the source defines zero as same-day
approval. Its interval interpretation still needs sensitivity analysis.

## Same V6 hierarchy, exact population calculation

The model retains the existing elapsed hierarchy. For jurisdiction j, its
phase log-location is

`μ_j = log(7) + 2 z_location + z_agency[j] + 0.75 z_task + 0.5 z_operation[j]`,

with independent standard-normal z coordinates. The single dataset offset is
`δ = 0.25 z_source`. These are inherited development priors, not newly estimated
empirical scales. With one phase per authority, agency and operation effects
cannot be separately interpreted as intrinsic task productivity.

Case log-duration variance is `σ² + 0.25²`, where
`σ = 0.6 exp(0.4 z_case_scale)`. The phase median is therefore exactly `exp(μ_j)`.
A reported median uses a Student-t error on the log scale centered at `μ_j + δ`:
95% with scale 0.5 (the existing unknown-n summary floor), 5% with scale 2.
These are scale parameters, not standard deviations. There is no source-type
ranking, learned per-type precision, selection correction, or known-n cohort
likelihood in this particular fit.

V6 now has an opt-in `analytic_single_phase` population calculation. It
integrates the same lognormal case variation analytically; it adds no latent
parameters. It requires one aggregate phase, one route, elapsed only, no
repeats/dwells/branches, and matching complete-phase operators. Unsupported
structures fail rather than silently using a lognormal approximation to a sum.
The normal multi-operation path retains its historical QMC calculation.

The same exact subcase supports normalized multinomial histogram likelihoods
through lognormal bin masses. That mathematical support does **not** establish
the meaning of administrative zeros, sample sizes, clocks or reporting coverage.

Posterior sampling is still Monte Carlo: four chains, 1,000 warmup and 2,000
retained draws per chain, using the existing operation-centered transition
kernel. The 28 coordinates retain the hierarchy; individual case latents and
unobserved labor channels are absent. Population summaries conditional on each
draw are analytical, not Monte Carlo estimates of case quantiles.

## Results and checks

The [initial QMC fit](../runs/three_family_20260920/solar_coarse_fit_v1/posterior.json)
converged but failed prediction precision: increasing its grid from 256 to 1,024
moved some quantiles by 6.36%. It is preserved as numerically unusable.

The [exact-phase fit](../runs/three_family_20260920/solar_coarse_fit_analytic_v1/posterior.json)
completed locally in **58.65 seconds**, with no convergence flags. Its population
likelihood and quantiles are grid-independent. Zero grid-refinement differences
are a consequence of using an exact formula, **not an independent validation of
that formula or the source-to-operator mapping**. Separate source-free tests
compare quantiles and multinomial probabilities against SciPy reference
calculations, including a tiny positive tail that naive CDF subtraction loses.
A post-fit audit replayed 32 saved likelihood evaluations exactly.

The [descriptive table and analysis](../runs/three_family_20260920/solar_coarse_analysis_v1/README.md)
show all twelve authorities, including the zero-median source. For illustration,
Lemoore's published 14-business-day median produces a model median of 11.64
(90% interval 3.85–29.48); Lake Forest's published 1 produces 1.49 (0.50–6.08).
Intervals remain broad under the inherited reporting assumptions.

Across the twelve represented authorities, the posterior SD of log phase
medians is 1.14, with a 90% interval 0.83–1.45. This is a **derived finite-panel
statistic**, not a learned statewide variance-component hyperparameter.
Centered jurisdiction log-locations show about 65% average marginal variance
contraction relative to their corresponding prior contrasts. This supports
learning of relative reported-phase timing under this model; it does not
separate agency from task/operation effects or imply causal identification.

The source-offset coordinate has only about 0.3% marginal contraction—consistent
with essentially no source-bias learning here. The case-scale coordinate also
stays near its prior. In this median-only exact subcase, the likelihood contains
**no information about case spread**. P90 and population mean extrapolations
therefore cannot be headline findings. Program and global information reports
also exclude intrinsic-agency and primitive task/operation claims from aggregate
phases; global location is explicitly labelled a represented-phase location.

## Assumption sensitivity and report-component allocation

The [frozen four-variant sweep](../runs/three_family_20260920/solar_phase_sensitivity_v1/plan.json)
keeps all twelve authorities and the same source values. It was specified after
seeing the baseline, before sampling these variants. No preferred variant was
selected by fit or agreement with the published inputs. The exposed
`unknown_n_report_sd_floor` replaces a hidden constant; its default remains 0.5.
Known-n cohorts and explicitly modeled subjective ranges are unaffected.

| Assumption | SD of log phase medians across this panel, posterior median (90% interval) |
|---|---:|
| Baseline | 1.14 (0.83–1.45) |
| Unknown-n report floor 0.25 | 1.23 (0.92–1.49) |
| Unknown-n report floor 0.75 | 1.07 (0.75–1.42) |
| Agency/operation prior scales halved | 0.61 (0.41–0.81) |
| Same-day interval [0,1] instead of [0,0.5] | 1.10 (0.83–1.40) |

The initial narrower-floor fit missed the ESS ≥400 criterion on the same-day
authority's location (bulk ESS approximately 374–394, R-hat approximately 1.005).
It remains preserved as unusable. A fixed extension of 4,000 draws per chain,
using fresh RNG streams and the identical target, passed all convergence and
precision checks. The table uses that
[extended analysis](../runs/three_family_20260920/solar_phase_sensitivity_v1/narrower_extended_analysis/analysis.json);
the [original sweep summary](../runs/three_family_20260920/solar_phase_sensitivity_v1/summary/results.json)
retains the initial failure rather than being overwritten. All five conditions
now have a usable fit, but none is independent validation.

Stronger pooling is consequential, not innocuous: Montebello's inferred median
changes from 0.87 to 5.37 business days even though its published median remains
zero. A [report-component audit](../runs/three_family_20260920/solar_report_component_audit_v1/results.json)
finds the posterior probability assigned to the broad reporting-error component
increases from 22.1% to 60.2%. This probability is conditional on the chosen
model; it is **not the probability that the source is wrong**. Genuine
between-authority differences can be discounted as reporting errors when
pooling is too strong. The shared 5% mixture weight was fixed, not learned.

Thus even this deliberately small analysis cannot justify a precise headline
heterogeneity estimate without calibrating reporting and pooling assumptions.
Computational convergence and marginal variance contraction do not establish
robustness or superior estimation. Direct published medians remain a necessary
same-information baseline, not ground truth for scoring these fits.

## What remains

- Calibration of reporting/pooling assumptions and real held-out checks; the
  first sensitivity sweep above is complete but is not such calibration.
- The complete eligible panel, its missingness, eras and deduplication audit.
- Source-bound overlapping forum/administrative/oversight measurements before
  estimating source heterogeneity or transporting source corrections.
- Corresponding synthetic recovery and same-information direct-source/LLM
  comparisons. The published medians used for fitting are not validation truth.
- Full solar source coverage, separate structural inventories and scoped fees.

Code: [analytic_phase.py](../pipeline/procbench/analytic_phase.py),
[V6](../pipeline/procbench/bayes_trace_hierarchy.py), and
[runner](../pipeline/procbench/run_visit_hierarchy.py).
The [independent source review](../runs/three_family_20260920/solar_coarse_pilot_review_v1/README.md)
and [analytic-mode review](../runs/three_family_20260920/analytic_single_phase_review_v1/review.json)
remain preserved, including their findings. Later reporting guard changes do
not rewrite the frozen posterior or its original source snapshot.
