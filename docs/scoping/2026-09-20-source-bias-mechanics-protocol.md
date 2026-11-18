# Reference-anchored source bias: first mechanical recovery gate

Frozen before generating this fixture or running the new hierarchy. This is a
source-free development experiment, not a new corpus, blind benchmark result,
empirical calibration, or evidence of transportability. It tests integrated V6,
not another inference architecture. The corresponding source-comparison rank
screen is necessary geometry only.

## Fixed experiment

Use twelve artificial programs with one coarse elapsed phase per program and
calendar-day medians. Their true log medians are `log(20) + 0.07*(j-5.5)` for
zero-based program `j=0..11`. No individual cases, repeats, labor channels,
selection, censoring, fees, counts or finite-cohort labels are introduced.

Three source types measure every program: `agency_dashboard` (reference),
`agency_official`, and `forum`. Each type has three documents. Assign document
`(j + t*(j//3)) % 3`, with type index `t=0,1,2`. Each document's centered log
deviation is one of `[-0.10,0,0.10]` in document-index order. This is a declared
crossed source-free design, not a claim that actual documents have independent
errors. Reject a rank-deficient implementation rather than modifying assignments
after outcomes are observed.

Generate 36 independently noisy log population-median reports per fixture.
The report kernel is Student-t with four degrees of freedom and scale 0.20.
Round the generated log report to the nearest 0.01 on a fixed log-unit grid;
interval bounds are the rounded center exponentiated after adding `±0.005`.
Thus the likelihood integrates the actual reporting bin, rather than treating
a moving window around an exact observation as censoring. These
are interval reports, not confidence intervals or exact sample medians with a
fabricated denominator. Seeds are fixed at 73101, 73102 and 73103. Run two
conditions for every seed, retaining all results:

1. Clean type means: `[0,0,0]`.
2. Shifted type means: `[0,log(0.8),log(2)]`.

The initial fixture is intentionally matched to the reporting model and has no
outliers. A later selected/outlier/misspecified-world check must be separately
declared; success here cannot establish robustness to those mechanisms.

## Inference settings

Use exact single-phase population integration in V6 and elapsed-only channels.
Keep the case-spread parameter unlearned and out of headlines: medians do not
identify it. Use common program hierarchy settings across both controls:
elapsed prior median 20 days, location scale 1, agency scale 0.5, task scale 0,
operation scale 0.25, reporting scale and unknown-n floor both 0.20,
contamination 0, selection scale 0, and operation-centered sampling.

The opt-in source hierarchy uses reference type `agency_dashboard`, type-spread
prior `LogNormal(log(0.5),0.5)`, document-spread prior
`LogNormal(log(0.15),0.5)`, and exact within-type centered document contrasts.
These are fixture-development settings, not calibrated real-data priors.
Compare with legacy per-document source offsets at their historical 0.25 scale,
using identical reports and all other priors. Preserve their different model
assumptions; this is not a same-prior parameterization comparison.

Run four chains, 1,000 warmup and 2,000 retained draws initially. Any failed
convergence gate gets one predefined extension to 6,000 total retained draws
per chain, with originals retained. Do not change likelihoods, memberships,
priors, seeds or reporting conventions to rescue a result.

## Gates and honest interpretation

- Verify input hashes, known fixture labels, program/source design rank, exact
  zero reference mean, exact within-type centering, transformed offset use,
  scalar/vector likelihood agreement and all retained chains.
- Require the existing R-hat/ESS/numerical gates for the quantities reported.
  Failed numerical runs remain failures, not excluded replications.
- For shifted fixtures, report each type-contrast 90% interval, whether it
  contains the planted contrast, and multiplicative median error. A first
  mechanical pass requires all six nonreference contrast medians within a
  factor 0.7–1.4 of their planted multiplier and at least five of six intervals
  covering the planted contrast. Three seeds do not estimate coverage reliably.
- For clean fixtures, report all six intervals and false-exclusion count; at
  least five must include zero. Do not select the clean run that looks best.
- Report program-median error and interval scores for both models without
  claiming the Bayesian hierarchy necessarily beats the control. Source
  means, document deviations and hyper-scales are different estimands.
- Report each spread's prior/posterior interval and coordinate-level marginal
  contraction. Three types/three documents per type may not identify the scales;
  a passing type-mean gate must not be relabeled scale recovery or source trust.

This experiment does not test the realistic synthetic-document pipeline or the
LLM baseline. Both remain separate required study gates. No reserved corpus
labels may be consulted to build, fit or revise these fixtures.
