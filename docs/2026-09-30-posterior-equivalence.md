# End-to-end posterior equivalence: execution record

2026-09-30. Follow-up explicitly requested by Alex after the bounded
[GPU pilot](2026-09-30-jax-gpu-pilot.md). That pilot established numerical and
throughput agreement, **not equivalent converged posterior estimates**.

**Completed verdict:** on the unchanged W0/v2 target, GPU-backed production SMC
and four independent GPU HMC chains pass all declared posterior comparisons.
HMC also passes genuine time-series convergence diagnostics. The blocked CPU
chains fail and are not validated as a replacement. These results close the W0
posterior-equivalence gap, not the larger-town/other-statute validation gap.

Later implementation/results are tracked separately in
[configurable inference speedups](2026-09-30-configurable-inference-speedups.md).
Those device-resident mutation kernels use different RNG streams and their own
fixed-budget comparisons; this earlier pass must not be inherited by a new
configuration without its checks.

## Scope and frozen pass criteria

Public W0 evidence, unchanged v2 likelihood/priors, centered town speeds and both
existing block-coordinate transforms. No truth, author packages or score inputs.
The completed CPU `W0/fitE001` is the reference: two 10,000-particle, 30-move
adaptive-SMC runs passed existing gates (worst between-run particle R-hat
1.000734, mean difference 0.0468 posterior SD). These are independent-ensemble
agreement diagnostics, **not autocorrelation-based MCMC convergence proofs**.
W0m and W4 failed parts of their existing gates and are not treated as converged
references in this task. This task does not certify every statute/catalog.

1. Bind reference evidence/settings and check its saved likelihoods against the
   current CPU and JAX implementations at 64 preselected particle positions.
   Absolute likelihood error ≤1e−10, same impossible-event support.
2. Use the **existing production adaptive-SMC driver**, injecting only an
   evaluator pool. Retain ESS-based temperatures, systematic resampling,
   covariance proposals, scaling adaptation, priors, and 10,000 particles ×
   30 moves (60 at the last stage). Two independent GPU runs with new seeds.
   A small same-seed CPU/GPU mutation replay additionally checks RNG ordering
   and transition decisions; it is not substituted for posterior comparison.
3. Between independent SMC ensembles and between CPU/GPU posteriors: every
   sampled coordinate's mean difference ≤0.1 pooled posterior SD, SD relative
   discrepancy ≤10%, 5/50/95% quantile differences ≤0.2 pooled SD. Also compare
   town design probabilities (absolute difference ≤0.025), expected total days,
   expected step executions and relative town speed. Derived continuous
   quantities use the same mean/quantile thresholds. Differences are numerical
   Monte Carlo tolerances, not proof of identical mathematical distributions.
4. Run actual time-indexed chains for the alternative kernels: four chains,
   2,048 warmup + 8,192 retained HMC iterations; four chains, 2,048 warmup +
   16,384 retained blocked-CPU sweeps. Mass/proposal covariance is fixed from
   the separate CPU SMC reference (explicitly reference-informed tuning, **not**
   another likelihood factor). Initialize from dispersed prior draws, not
   tightly clustered posterior points. Adapt only scalar proposal scale during
   warmup, then freeze. Require every coordinate's rank R-hat <1.01, bulk and
   tail ESS ≥400, and the same distributional comparison tolerances. Report
   failures; do not extend or tune repeatedly until a gate passes.

Budget: one implementation/check pass; these two full GPU SMC runs and two
four-chain experiments; maximum 90 minutes per launched experiment. No existing
fit/acquisition job is changed. If an alternative kernel fails, it is not
promoted even if the GPU evaluator passes. No blanket "equivalent" verdict
without identifying the component and tested evidence.

Artifacts: `runs/toy_jax_pilot_20260930/equivalence/` locally and under the
dedicated sk3 task code root. Reference originals remain in
`/dfs/scratch0/alexspan/toy_statute/code/runs/toy_statute_20260926/W0/fitE001`.

## Adaptability

The intended boundaries are evidence compilation, statistical likelihood/prior,
numerical evaluation, transition kernels and posterior summaries. This task's
pool injection leaves the SMC algorithm in one place. Proposal/hardware changes
should preserve the target; source-bias, selection, prior and process-structure
changes deliberately change it and need fresh scientific validation.

The prototype is not yet fully plug-and-play: the catalog is module-global,
JAX specializes on fixed shapes, and its likelihood mirrors the CPU equations.
Use one catalog per worker/process, rebuild compiled evidence/JAX functions
after catalog or shape changes, and compare both numerical paths after changing
an observation law. Production town bucketing and a common immutable model
specification remain architectural follow-ups, not prerequisites for W0 testing.

## Results

The earlier unconverged pilot is retained and is not reclassified. All new
sampling runs, derived-output comparisons and diagnostics have completed.

### Same sampler, CPU versus GPU evaluator

Reference binding passed. At 64 preselected saved particle positions, current
CPU likelihoods match the saved CPU values exactly and GPU values differ by at
most 1.14e−13. A 16-particle × six-move same-seed mutation replay produced
**identical parameter states and accept/reject decisions**, with prior error
≤1.43e−14 and likelihood error ≤1.14e−13.

The production SMC driver now accepts an optional evaluator-pool factory; its
default CPU behavior is unchanged. The experimental GPU pool batches only
likelihood/prior evaluations, preserves logical-worker RNG streams, and retains
the original NumPy proposal arithmetic. If a nonfinite target would skip a
uniform draw in the CPU implementation, the adapter replays that chunk's step
from its saved RNG state on CPU. One such fallback occurred across the two
full runs; it is recorded, not ignored. Ten targeted existing tests pass after
adding the injection point. An additional fake-target regression forces both
nonfinite-prior and nonfinite-likelihood rejections and reproduces CPU states,
densities and acceptance exactly, without requiring a GPU in the test suite.
The consolidated targeted run passes **11/11 tests**.

Both GPU runs used 10,000 particles, 30 moves (60 at beta=1), 24 logical RNG
streams and new seeds 20271001/20272001. Both reached beta=1 in nine adaptive
stages. Initial stages retained 5,901/5,903 distinct parents, rather than the
three/four parents in the 16-particle pilot. Log normalizers were −528.315 and
−528.436 (CPU reference: −528.436, −528.470).

| Comparison, all 36 coordinates | Max mean difference / SD | Max SD discrepancy | Max 5/50/95% quantile difference / SD | Parameter gate |
|---|---:|---:|---:|---|
| CPU reference run 0 vs 1 | 0.0468 | 4.28% | 0.0917 | pass |
| GPU run 0 vs 1 | 0.0789 | 4.21% | 0.1408 | pass |
| Pooled CPU vs pooled GPU | 0.0513 | 5.66% | 0.1615 | pass |

GPU sampling took 161.65 + 167.44 = **329.09 s** (5.49 min). The saved CPU
runs took 1,909.41 + 1,939.86 = **3,849.27 s** (64.15 min), using 24 workers.
That historical ratio is 11.70×, not the pilot's 206× warm likelihood ratio.
The runs were on the same shared server at different times, using different
software environments and differently optimized equivalent CPU likelihood
sources. GPU timing excludes its initial compilation/preflight and neither
figure includes derived-output computation in this comparison. Consequently,
this establishes a useful measured runtime reduction, **not an isolated,
equal-resource hardware speedup attribution**. GPU compilation/preflight is
separately retained in the evaluation timing/provenance records.

### Blocked-chain result

Four independent prior-started chains completed 2,048 warmup and 16,384 retained
sweeps each, with frozen post-warmup proposal scales. They **fail** the declared
convergence gate: maximum rank R-hat 1.03479, minimum bulk ESS 105.5 and tail ESS
84.3. Against the CPU reference, maximum coordinate discrepancies are 0.1556 SD
for means, 11.02% for SDs and 0.3267 SD for 5/50/95% quantiles. Ten coordinates
fail the distributional comparison; 29 fail at least one chain diagnostic.

This does not invalidate the cache's numerical equality or invariant transition
kernel. It does mean this blocked configuration has **not demonstrated equivalent
posterior estimates at this budget**. The town-local cost reduction is not yet
an effective-sample-per-second improvement. Keep it opt-in; do not replace the
validated production SMC with these standalone chains.

### Derived quantities and HMC

HMC ran four dispersed prior-started chains, 2,048 warmup + 8,192 retained
iterations each, eight leapfrog steps per iteration, a fixed reference-informed
dense preconditioner, and Metropolis correction. The affine change of coordinates
has constant Jacobian, so it does not change the target. Step size was adapted
only during warmup and frozen at 0.288445; retained acceptance was 80.57%.
All 36 coordinates pass: maximum rank R-hat **1.001394**, minimum bulk ESS
**10,027.3**, minimum tail ESS **6,224.2**. Against the pooled CPU reference,
maximum mean discrepancy is **0.0406 SD**, SD discrepancy **3.42%**, and
5/50/95% quantile discrepancy **0.0962 SD**. This replaces the earlier pilot's
inconclusive HMC verdict with a positive result for this longer, preconditioned
configuration; it does not retroactively make the short chains converged.

HMC wall time was 781.18 s (13.02 min), including its compilation and warmup;
retained sampling took 614.14 s. It used covariance from the already-completed
reference, whose cost is **not** included. This is not an independently tuned
from-scratch speed comparison. Blocked chains took 606.6–609.3 s each in parallel.

Derived timing/count intervals mix over both designs and parameter draws.
Quantiles of a conditional mean over designs are **not** a replacement for the
full joint uncertainty; the comparison retains per-design values and their
conditional weights. These are posterior intervals over **population mean
elapsed days and expected step executions**, not predictive intervals for one
applicant. Repetitions enter expected executions; structure probabilities retain
inventory uncertainty. Relative speed is a centered town duration multiplier
(larger means slower), not identified causal/intrinsic agency capability.

| Candidate vs pooled CPU reference | Largest absolute design-probability difference | Timing/count/speed interval gates | Overall |
|---|---:|---|---|
| GPU SMC, two 10,000-particle runs | 0.000201 | all pass | pass |
| GPU HMC, four chains | 0.000172 | all pass | pass |
| Blocked CPU, four chains | 0.010697 | fail: Alder timing SD and relative-speed distribution | fail |

Independent CPU reference ensembles and independent GPU SMC ensembles also pass
the derived-output gates. The maximum GPU-vs-CPU timing/count mean discrepancy
is 0.0132 posterior SD; maximum timing/count quantile discrepancy is 0.0402 SD.
For a concrete example, Birch's mean elapsed time has median [90% interval]
43.34 [35.21, 58.38] days under CPU SMC, 43.36 [35.42, 58.25] under GPU SMC,
and 43.20 [35.16, 58.48] under HMC. Its expected step executions are
4.255 [4.018, 5.476], 4.260 [4.018, 5.481], and 4.255 [4.017, 5.435], respectively.

Derived summaries use all SMC particles; chain summaries use every eighth draw
only to bound postprocessing cost. R-hat/ESS and coordinate comparisons use
**all retained draws**, not thinned ones. Four preselected reference positions,
all three towns and all six designs were additionally checked against production
CPU `struct_posterior` / `town_estimands`: maximum probability difference
1.20e−14, mean-days difference 4.27e−14, execution-count difference 8.89e−16,
and relative-speed difference zero.

## Receipts, reproduction and disposition

- Main experiment: `runs/toy_jax_pilot_20260930/equivalence.py`.
- Original sampling source preserved at
  `runs/toy_jax_pilot_20260930/equivalence_source_sampling/equivalence.py`;
  its SHA-256 matches the GPU SMC/blocked launch records. Subsequent helper
  changes add derived-output computation, not new sampling settings.
- Comparator: `runs/toy_jax_pilot_20260930/compare_equivalence.py`.
- Full coordinate diagnostics, intervals and verdicts:
  `runs/toy_jax_pilot_20260930/equivalence/comparison.json`.
- `gpu_smc/`, `hmc/`, `blocked/`, and `observables/` beneath that root contain
  draws, launch hashes/settings, runtime/progress records and completion markers.
  A completion marker means execution finished; `comparison.json` determines
  whether its statistical gates passed.
- Reference copy: `runs/toy_jax_pilot_20260930/cpu_reference/fitE001/`.
  Experiment outputs and source are also retained under the dedicated DFS task
  root on sk3. These gitignored artifacts are **not a committed data archive**.

Recompute comparisons locally (scientific environment's `python`):

```sh
python runs/toy_jax_pilot_20260930/compare_equivalence.py \
  --root runs/toy_jax_pilot_20260930/equivalence \
  --reference runs/toy_jax_pilot_20260930/cpu_reference/fitE001
python -m pytest tests/test_toy_statute_scaling.py \
  tests/test_toy_statute_blocked.py tests/test_toy_statute_gpu_pool_contract.py -q
```

No defaults were changed, and no existing scientific/acquisition jobs were
modified. The GPU pool and HMC runner remain experimental execution adapters;
the optional pool injection is in production SMC. GPU batching is now supported
by a full posterior comparison, not just likelihood microbenchmarks. HMC is a
validated alternative for this target, not yet a production CLI/backend or a
tested gradient mutation kernel within full-sized SMC. Blocked global/local
mixing, town bucketing and larger-catalog GPU runs remain separate engineering
work; this experiment does not authorize claims of 500-town posterior recovery.
