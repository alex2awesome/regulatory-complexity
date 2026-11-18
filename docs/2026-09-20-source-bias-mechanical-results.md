# Source-bias hierarchy: first mechanical recovery results

The optional V6 source hierarchy now passes its relative-bias recovery checks
on all six frozen mathematical fixtures. **The full comparison gate does not
pass:** one legacy control remains unconverged after its single allowed
extension and is unscored. This is a useful mechanical result, not empirical
source-trust calibration, rendered-corpus validation or an LLM comparison.

## What was tested

The [original protocol](scoping/2026-09-20-source-bias-mechanics-protocol.md)
fixed twelve artificial programs, three source types, three documents per type
and 36 noisy population-median reports per fixture. Three seeds were run under
clean source means and under relative multipliers of 0.8 for agency-official
reports and 2.0 for forum reports. The administrative reference shift is zero
by construction. These are deliberately matched reporting-kernel fixtures with
known clock, population and source identity—not text extracted by an LLM.

The first clean hierarchy run's original joint source ESS block failed even
after 6,000 retained draws per chain. The separately declared
[sampler-development round](scoping/2026-09-20-source-bias-sampler-development-02.md)
introduced optional split ESS and Jacobian-correct scale interweaving without
changing the statistical target. Clean seed 73101 therefore informed numerical
development and is not an unseen validation replication. Its original failure
and every later initial failure remain saved.

## Numerical and recovery results

All six hierarchy fits pass the unchanged numerical gate. The three clean
cases and shifted seed 73102 pass at 2,000 draws per chain; the other two shifted
cases pass after the predeclared extension to 6,000. Every legacy control needed
the extension. Five then passed; shifted seed 73102 still had one derived
operation-plus-source R-hat of **1.010794**, above the **1.01** gate. No further
extension or relaxed threshold was used.

On the first clean fixture, type-spread bulk ESS improved from about **89 to
1,485** at the same retained draw count. The new kernel uses additional
likelihood evaluations; local wall times also reflect different concurrent
workloads, so this is not a hardware-normalized speed benchmark.

The six shifted source contrasts all satisfy the original multiplicative
median-error gate (0.7–1.4 of the planted multiplier), and all six 90% intervals
cover the planted contrast. All six clean-condition intervals include zero on
the log scale. Three seeds are far too few to estimate interval coverage rates.

| Shifted seed | Agency-official multiplier, planted 0.8 | Forum multiplier, planted 2.0 |
|---|---|---|
| 73101 | 0.892 [0.763, 1.046] | 1.910 [1.630, 2.228] |
| 73102 | 0.775 [0.661, 0.911] | 2.059 [1.757, 2.395] |
| 73103 | 0.831 [0.704, 0.988] | 2.261 [1.912, 2.687] |

These are posterior medians and 90% intervals for relative source shifts, not
per-document error rates or probabilities of truthfulness. Type-effect marginal
variance contraction is approximately 97–98% in this designed overlap regime.
Type-spread and document-spread intervals remain much broader. No stochastic
hyper-scale was planted in this fixed-effect fixture, so their contraction is
not a hyper-scale recovery result.

## Clock comparison: improvement is not uniform

Scores concern the latent **population median** for each artificial program,
not a predictive interval for individual applicants. Smaller scores are better.
Each row averages the twelve program scores within one fixture; the programs
share fitted parameters and are not independent replications.

| Condition | Seed | Mean absolute log error, legacy → hierarchy | Mean 90% log interval score, legacy → hierarchy |
|---|---:|---|---|
| Clean | 73101 | 0.1013 → 0.0974 | 0.6991 → 0.7188 |
| Clean | 73102 | 0.0686 → 0.0765 | 0.5452 → 0.4884 |
| Clean | 73103 | 0.0996 → 0.1134 | 0.6692 → 0.5904 |
| Shifted | 73101 | 0.2053 → 0.0945 | 0.6502 → 0.6934 |
| Shifted | 73102 | **control failed; no paired score** | **control failed; no paired score** |
| Shifted | 73103 | 0.1917 → 0.1112 | 0.9847 → 0.6051 |

The hierarchy improves point estimates in both numerically available shifted
pairs, but one of their interval scores worsens. Clean-condition point errors
also sometimes worsen. Do not pool only the passing/favorable comparisons into
a headline claiming universal improvement. This control uses the historical
0.25 independent source prior; the new hierarchy changes anchoring and prior
structure as well as pooling. It is not an ablation isolating only hierarchical
pooling, and neither control is the LLM baseline.

## What this establishes—and what remains

Reference-anchored source effects can be recovered by integrated V6 when the
inputs genuinely measure the same quantities and the reporting mechanism is
matched. The previous source-block mixing problem did not require changing
evidence or priors to fix. It does not follow that more unaligned documents
would identify these effects on real data.

The fixture does not test a shared bias in the reference and other sources,
forum/institution selection, outliers, reporting-scale misspecification,
unknown semantic labels or transport across programs. Precision and
contamination remain separate unfinished calibration work. Real source-offset
hierarchy use is still off, and no three-family real or synthetic study release
follows from this result. The full numerical comparison gate remains failed
until a separately documented control-sampling check resolves its one failure.

Reproducible outputs:

- [All twelve selected fit results, original failures, per-program scores and source summaries](../runs/three_family_20260920/source_bias_mechanics_analysis_v2/results.json).
- [Evaluation script and manifest](../runs/three_family_20260920/source_bias_mechanics_analysis_v2).
- [Frozen-source numerical replay](../runs/three_family_20260920/source_bias_mechanics_validation_v2).
- [Original blocked fits and numerical audit](../runs/three_family_20260920/source_bias_mechanics_fits_v1).
- [Interwoven fits and preserved initial/extended controls](../runs/three_family_20260920/source_bias_mechanics_interwoven_v2).

The combined project/generator suite passed **1,344 tests** after the kernel
change, with one pre-existing generator-test return-value warning. Tests and
finite saved-state checks support mechanics; they are not semantic validation.
