# One active toy-statute implementation

2026-09-30. Alex requested that the verified corrected/optimized code become the only active implementation.

Scope: remove obsolete algorithms and production reference switches from `pipeline/procbench/toy_statute/`; keep independent reference calculations in tests. Preserve historical sources, evidence, results and remote jobs. Budget: one bounded refactor, focused regression tests, and a before/after numerical/runtime check. Done means unchanged corrected-target behavior and one production path—not new posterior recovery or a repo-wide architecture rewrite.

The preceding [repair report](2026-09-30-toy-statute-audit-repairs.md) distinguishes two comparisons: optimized versus corrected reference (equivalent to floating-point accuracy), and corrected versus buggy pre-edit implementation (intentionally different targets). This refactor changes neither target nor priors.

Pre-refactor corrected source: `runs/toy_single_path_refactor_20260930/source_before/`. Historical snapshots are reproduction records, not selectable production backends. Independent test references remain necessary to catch future regressions.

## Completed

The corrected optimized implementation is now the sole production path in this package:

- `grid.sum_pmfs` always uses cached positive convolution. Removed capped FFT convolution, complex-log FFT helpers, FFT constants, and direct/FFT backend switches.
- `Model` has one completed-gap integration and no convolution/completion backend options. The direct reference moved to `tests/toy_statute_reference.py`.
- `readings.stage_c` automatically groups equivalent shared choice rows and calls one integration kernel. Removed the public `collapse_readings=False` bypass. Particle-dependent choice laws use the same kernel without invalid grouping.
- `outcomes` retains only the conditional denied-binomial/nonapplicant-Poisson survey likelihood. Removed the unused mean-matched Poisson/quadrature routines; the necessary numerical oracle is test-only.
- Removed the old MAP/Laplace/random-walk-MCMC implementation from `fit.py`. It retains shared answer generation and delegates its command line to `smc.main`. There is one process-sampling implementation, not two divergent fitters.

No files, historical evidence, saved particles, or remote jobs were deleted. Removed code is recoverable from the pre-refactor source snapshot. The outcome-cut sampler remains because it samples a **different scientific layer**, not because there is an alternative process implementation. Choice models, priors, gates and independent/hierarchical reading options remain scientific settings.

## Supported commands and compatibility

Canonical process fit:

```sh
python -m pipeline.procbench.toy_statute.smc \
  --evidence <world>/evidence --out <new-fit-directory> \
  --runs 2 --particles 2000 --moves 12 --workers 4 --gate v2
```

`python -m pipeline.procbench.toy_statute.fit` accepts the **same SMC arguments and defaults** and calls the same implementation. It no longer launches the historical four-chain fitter. `fit.run`, the old `--keep-mult` argument, and the retired backend APIs are deliberately unsupported; old algorithms/driver scripts must be replayed with their recorded source snapshot. There is no automatic conversion from an MCMC budget to an SMC budget.

Entry-point documentation: [toy_statute/README.md](../pipeline/procbench/toy_statute/README.md).

## Verification of this refactor

Focused suite: **68 passed in 4.47 seconds**. The tests check numerical references, the audit counterexamples, launch provenance, the `fit` → `smc` delegation, and the absence of retired production methods/options or production imports of test references.

Same-target before/after comparison against the frozen **corrected** pre-refactor source:

- 24 parameter points across W0, W0m, W4, HK1b, HEN2 and HK2: maximum likelihood difference **0**; maximum structure-posterior difference **0**; priors and observation metadata identical.
- Actual answer generation at one parameter point per world, with the same random seed: maximum output difference **0**, including estimands, predictive quantiles, design probabilities and metadata.
- Six actual Metropolis proposals (two particles × three moves): resulting states, prior values, likelihoods and acceptance summary **bitwise identical**. This is a transition regression, not a new posterior fit or convergence certificate.
- Stage C under uniform, risk and particle-dependent cost choice, each with independent readings and finite kappa: maximum before/after output difference **0**, using identical seeds.
- Conditional survey calculation: maximum before/after difference **0**.

The initial comparison harness stopped because it tried to cast metadata strings to floats. Its log is preserved as `checks_initial_harness_error.log`; the comparator was corrected to compare strings as strings. This was a harness error, not a model discrepancy.

## Performance

Paired local timings, seven repeats per implementation, one BLAS thread:

| World | Corrected before refactor (ms) | Sole implementation (ms) | Speedup versus buggy pre-repair code |
|---|---:|---:|---:|
| W0 | 15.29 | 15.86 | 2.61× |
| W0m | 16.91 | 16.72 | 2.75× |
| W4 | 92.77 | 93.12 | 3.41× |
| HK1b | 139.29 | 143.29 | 2.56× |
| HEN2 | 102.90 | 101.13 | 3.43× |
| HK2 | 131.30 | 134.27 | 2.50× |

The cleanup preserves performance: paired medians are within 4% of the already optimized implementation. It retains the earlier approximately 2.5–3.4× gain; it does not add another multiplicative speedup. The buggy-code comparison is runtime-only because its target differs. There is still no measured full-fit wall-clock or Monte Carlo-efficiency claim.

Receipts and reproduction: [check_refactor.py](../runs/toy_single_path_refactor_20260930/check_refactor.py), [checks.json](../runs/toy_single_path_refactor_20260930/checks.json), [tests.log](../runs/toy_single_path_refactor_20260930/tests.log).

## Boundary

The target remains `toy-process-v2-20260930`; this refactor itself needs no new scientific fit. The **preceding repairs** do require new fits relative to round 6. Remote jobs continue using their frozen historical snapshot and were not stopped or patched. Historical audit scripts that call retired APIs require their matching source snapshot. Scientific limitations in the repair report, including the missing fee-reading likelihood and unrepaired historical kitchen fee evidence, remain explicit.
