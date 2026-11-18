# Source-bias control: separately declared numerical follow-up

Declared 2026-09-20 after the source-free development matrix was scored and
independently audited, **before this follow-up run**. This is outcome-informed
numerical development, not an extension permitted by the original protocol.

## Reason and immutable earlier result

The original 12-fit comparison remains failed: the shifted-73102 legacy control
failed its single allowed extension at R-hat 1.0107941951 for a derived
operation-location-plus-source-offset quantity. The original evaluation leaves
it unscored. All six new-hierarchy fits were numerically usable. Preserve the
original fits, evaluation and failed full-gate declaration unchanged.

This follow-up asks only whether substantially longer sampling of the **same
legacy target** resolves that numerical failure. It must not be represented as
an originally preregistered pass, a new independent seed, or a model improvement.

## Fixed run, declared before launch

- Input run:
  `runs/three_family_20260920/source_bias_mechanics_interwoven_v2/shifted_73102_legacy_extended`.
- Keep its data, likelihood, priors, configuration, four chain identities,
  existing 6,000 retained draws per chain and final states unchanged.
- Append exactly **18,000** retained draws per chain, no warmup, producing
  **24,000** retained draws per chain in total. No intermediate-result stopping.
- Continuation seed **2026692001**, two workers, BLAS/OMP threads one.
- Fresh output:
  `runs/three_family_20260920/source_bias_control_numerics_followup_v1/shifted_73102_legacy_24000`.
- Use the existing guarded `extend_visit_hierarchy` entry point. Its saved-input,
  draw-hash, fresh-seed and likelihood-replay checks must pass. Preserve its
  frozen source snapshot and complete manifest.
- Same numerical criteria: R-hat at most 1.01, bulk ESS at least 400, tail ESS
  at least 200, including existing derived quantities; unchanged integration
  precision criteria. Report every failure. No further extension in this round.

## Evaluation and stop rule

Replay saved-source likelihoods and numerical diagnostics before interpreting
the result. If it still fails, leave it unscored and stop this numerical branch.
If usable, report its scores and the corresponding already-frozen hierarchy
scores in a **separate supplemental table**, using the same population-median
estimand and shared interval scorer. The original matrix gate stays false.

Only source-free fixture labels may enter that supplemental evaluation. No real
corpus, rendered synthetic documents, generator/private truth, reserved labels,
LLM baseline, or transported source-trust claim is involved.

Earlier result: [mechanical results](../2026-09-20-source-bias-mechanical-results.md).
Independent scoring audit:
`runs/three_family_20260920/source_bias_mechanical_results_review_v1/`.
