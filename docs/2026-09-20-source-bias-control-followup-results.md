# Source-bias control: supplemental numerical result

The separately declared longer legacy-control run **converged**. It completes
the missing numerical comparison for the source-free shifted-73102 fixture,
but **does not change the original protocol's failed full gate**.

## Numerical check

The [follow-up protocol](scoping/2026-09-20-source-bias-control-numerics-followup.md)
fixed one continuation from 6,000 to 24,000 retained draws per chain, four chains,
with no change to likelihood, data or priors and no intermediate stopping.
The earlier 6,000-draw prefixes are preserved bit-for-bit. The continuation took
700 seconds locally, including posterior reporting; this is not sampler-only
runtime or a hardware-normalized comparison.

The previously failing operation-location-plus-forum-offset diagnostic improved
from R-hat 1.010794 to **1.001490**, with bulk ESS **6,197** and tail ESS **12,797**.
All declared numerical gates passed. The extension checked 200 saved-state
likelihoods; the subsequent frozen-source audit reproduced twelve checked
likelihoods and scalar/vector calculations with maximum difference zero.

## Supplemental paired scores

Same artificial program population-median estimand, same twelve programs,
same shared scorers; smaller is better. The hierarchy result is the already
frozen, usable 2,000-draw-per-chain fit, not a newly selected fit.

| Mean score across the twelve programs | Legacy, supplemental 24,000 draws/chain | Frozen hierarchy |
|---|---:|---:|
| Absolute log error | 0.1418 | 0.0734 |
| 90% interval score, calendar days | 13.3780 | 9.9730 |
| 90% interval score, log days | 0.5657 | 0.4916 |

Including this explicitly supplemental pair, hierarchy point errors are lower
in all three shifted fixtures and log interval scores in two of three. The
[original table](2026-09-20-source-bias-mechanical-results.md) also shows that
clean-condition point errors sometimes worsen. No universal improvement or
calibrated coverage rate follows from three seeds. Programs within a fixture
share parameters; they are not twelve independent model replications.

This is outcome-informed numerical development on deliberately aligned
mathematical reports. Anchoring and priors differ between the models; it is not
a pooling-only ablation, realistic prose extraction, empirical source-trust
calibration, a transported prior, or an LLM comparison. No further control
extension is needed for this branch.

## Reproduction

- [Supplemental evaluation](../runs/three_family_20260920/source_bias_control_numerics_followup_v1/evaluation/results.json)
- [Frozen-source numerical audit](../runs/three_family_20260920/source_bias_control_numerics_followup_v1/evaluation/numerical_audit.json)
- [Evaluation code](../runs/three_family_20260920/source_bias_control_numerics_followup_v1/evaluation/evaluate.py)
- [Fit manifest](../runs/three_family_20260920/source_bias_control_numerics_followup_v1/shifted_73102_legacy_24000/manifest.json)

The original frozen evaluation still leaves its failed control unscored and
`full_mechanical_gate_passed: false`. This supplemental result is stored
separately; the earlier independent scoring audit does not certify this new
evaluation.
