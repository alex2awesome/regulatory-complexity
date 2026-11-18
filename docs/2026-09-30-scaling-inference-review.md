# Scaling recommendations: bounded exact-optimization pass

2026-09-30. Review of [Claude's recommendations](2026-09-30-scaling-inference-recommendations.md).

**Follow-up executed:** Alex reordered the work to benchmark first, then blocked
town-local moves, then JAX. See the consolidated
[scaling and GPU execution record](2026-09-30-jax-gpu-pilot.md). The deferred/not
launched statements below describe the earlier bounded pass, not current status.

## Frozen scope before edits

Implement exact reuse of complete timing-report kernels and identical path-span
signatures, with repeated hour values reused as well (C9 / a conservative D12).
Do not merge independent gaps: completion selection applies to their **sum**, and
all gaps/mentions/hours within a case share its path. Preserve original case columns
and summation order. Add a provenance-bound optional Stage-B likelihood cache for
Stage C (E14). No new sampler, particle reduction, pruning, FFT approximation,
new prior, real-data fit, or changes to running jobs.

One bounded check: focused toy tests; fixed-point before/after likelihood and
structure comparisons on six held evidence worlds; paired warm runtime timings;
a duplicated-report fixture; saved-cache round trip and tamper/ordering checks.
Exact-change gate: absolute log-likelihood difference at most 1e-10, including
matching impossible-event support. Timing is per evaluation, not effective draws
per CPU-hour. No long 12/50/200/500-town fit campaign in this pass. Historical
source retained at `runs/toy_scaling_exact_20260930/source_before/`.

## Decisions

The recommendations are directionally good, but not all their "exact" or
"same target" qualifications hold without additional conditions.

| Items | Decision | Important condition / correction |
|---|---|---|
| A1–A2: local cache / blocked moves | High-priority next sampler experiment; not activated | Cache only genuinely unchanged factors. A dense orthonormal contrast is **not** a local town coordinate. Changing one raw centered speed changes every effective speed. Pairwise zero-sum speed moves can affect two towns; correction/objection coordinates are already local. Preserve the original joint prior, not just the likelihood. |
| A3: omit towns without records | Do not implement as written | A town webpage—including negative listing observations—is data. The current schema requires webpages. With hierarchy or centering, an unobserved town can still share posterior dependence; its posterior is not generally its original marginal prior. Skip a proven-constant likelihood factor, not the town's role in the joint model. |
| A4: nested town parallelism | Defer pending batching benchmark | Particle workers already run in parallel. Another process pool risks oversubscription, serialization and memory duplication; choose parallel axes deliberately. |
| B5 / F15: JAX, gradients, GPU batching | Strong next scalability candidate | A likelihood port and a sampler change are two different experiments. Float64, support masking and stable gradients need explicit checks. No current JAX/GPU speedup is claimed. |
| B6: 2,000 particles, adaptive moves, waste-free SMC | Do not change defaults now | Fewer particles changes Monte Carlo precision, not the intended target. Uncontrolled state-dependent stopping of moves need not preserve an invariant kernel. Waste-free SMC requires correct correlated-particle variance treatment. Compare independent-run errors and effective samples per resource-hour first. |
| B7: conjugate hyperparameter updates | Conditional recommendation | Our current speed prior has fixed scales, not a conjugate learned population block. Adding a hierarchy is a model change. Gibbs is useful only for an actually derived full conditional. |
| C8: reuse shared convolutions | Partly already implemented; more reuse possible | Count-vector spans are already deduplicated. Sharing across towns requires identical PMFs; "nearby" speeds do not qualify unless a declared approximation is introduced. Unscaled step laws offer exact reuse. |
| C9 / D12: repeated records/spans | Implemented conservatively | Reuse the whole timing-report kernel and identical joint span signatures, then restore original case columns. Do not multiply separately marginalized gap likelihoods. All per-case mentions, hours and timing masks remain distinct. |
| C10: design-feature dynamic programming | Defer; factorization not established | A factorized **prior** does not make the **likelihood** factorize. Endpoint sums, completion selection and shared decisions couple features. Dynamic programming needs a derived state representation/treewidth argument, not merely a feature encoding. |
| C11: 30-nat pruning | Reject for this pass | A per-design threshold is not a bound on total omitted mass across many designs/towns. Bounds must include prior/choice weights and accumulate across factors. Pruning Stage B can also remove designs later favored by H. No pruning added. |
| D13: admin histograms | Exact only for truly exchangeable, matching complete observations | Marginal milestone histograms lose within-case dependence. Keep clock, cohort, censoring, strata and sampling scheme fixed; changing an observation into a histogram is not automatically exact. |
| E14: Stage-C reuse | Implemented for future opt-in fits | Cache all town/design log likelihoods, bound to data, particle order and model settings. Does not solve finite-kappa population-weight importance collapse; ESS is not an error estimate. |
| F16: scaling benchmark | Accept, as the next separate deliverable | This pass has microbenchmarks only, not a 500-town scalability demonstration. Full fits are neither necessary nor appropriate for the first hardware-throughput test. |

No priors were narrowed, observations removed, designs pruned, sums replaced by
MAP choices, or particle/move defaults reduced. SMC proposals/resampling are unchanged.

## What changed, and the mathematical reason it is equivalent

For a completed report with several gaps, the kernel is

\[
K=\sum_{d_1,\ldots,d_G}\prod_g
 p(d_g\mid c,\theta)\,p(y_g\mid d_g,\theta)\;
 P(C\geq\textstyle\sum_g d_g).
\]

The posting selection factor couples the gaps. A cache keyed only by one gap
does not replace this joint sum. The new compiler instead groups reports by the
**entire sequence** of reported values/units and per-combination segment selectors.
Within each group it groups case-path combinations by their complete vector of
segment selectors. Equal keys give equal K for every theta. Compute K once and
expand it back into the original report/combination columns. Mention likelihoods,
time-mask likelihoods, hours, path weights and case marginalization follow exactly
as before. Rounded hour values similarly reuse their emission calculation, then
return to their original case columns. Compiled evidence is treated as fixed.

This is computational reuse, **not removal of repeated applicants** or a claim
that repeated retellings are independent evidence. Duplicate-case reconciliation
remains an upstream evidence responsibility.

Changes live in `pipeline/procbench/toy_statute/model.py`, `readings.py`, `smc.py`
and the hypothesis-space runner. Existing active fits/snapshots are untouched.
The sole production likelihood remains the optimized implementation. A narrow
`likelihood_compatibility.json` records checked before/after source fingerprints
for this same v2 target; unrelated source mismatches still fail the runner's gate.

## Measured outcome

**94 focused tests pass** after this pass. The bounded before/after check compared
18 fixed parameter points across six held evidence worlds plus four on a duplicated
report fixture. Maximum absolute differences in both full and per-design log
likelihoods were **0** at these points; impossible-event support agreed. A six-move
seeded sampler replay also matched exactly. The cache toggle has an additional
uninformative-target sampler test: identical particles, prior/likelihood values and
normalizer, with and without writing the cache.

Seven alternating warm timing pairs per fixture gave:

| Evidence | Before, median ms | After, median ms | Ratio before/after |
|---|---:|---:|---:|
| W0 | 15.28 | 14.90 | 1.03× |
| W0m | 16.23 | 15.43 | 1.05× |
| W4 | 85.26 | 79.89 | 1.07× |
| HEN2 | 94.15 | 89.24 | 1.06× |
| HK1b_v2 | 123.70 | 118.91 | 1.04× |
| HK2_v2 | 115.03 | 113.76 | 1.01× |
| W4 with 5× repeated report payloads | 193.17 | 83.02 | 2.33× |

The ordinary-corpus gain is **modest**, and the smallest ratios should be treated
as timing noise rather than a strong improvement claim. Early pairs overlapped
the focused test process; there are no confidence intervals. The repeated-report
fixture demonstrates the scaling benefit of reuse, not performance on a new
independent real corpus. No end-to-end ESS/hour gain has been measured.
Receipt and reproducible script: `runs/toy_scaling_exact_20260930/checks.json`
and `check_scaling.py`. No reruns to chase a preferred speedup.

### Saved-likelihood cache

For a **new** fit, add `--cache-town-loglik` to the ordinary SMC command. It costs
one final evaluation per particle, uses the existing workers, consumes no sampler
randomness, and writes `town_loglik_run<N>.npz`. Storage before compression is
approximately `8 × particles × towns × designs` bytes. This is opt-in to avoid
surprise disk use: 10,000 particles × 500 towns × 12 designs is about 480 MB/run
before compression. It does not remove that computation from the first fit;
it amortizes it across later Stage-C conditions.

The cache contains ordered L and checksums for particle values/order, evidence,
catalog, parameter layout, centering, block transform and target. Completed fit
manifests also hash the cache file. The hypothesis runner uses a complete matching
set automatically; a corrupted/mismatched cache fails, while a genuinely absent
cache uses the ordinary likelihood path. There is no alternate statistical backend.

## JAX sampling and other GPU acceleration

**Yes: prioritize a bounded JAX/GPU pilot next, not indefinite CPU polishing.**
A read-only hardware check found eight B200 GPUs on sk3. That establishes installed
hardware, not currently free capacity. The inspected local Python environment has
no JAX/JAXlib, NumPyro, BlackJAX or CuPy installed. No installations or GPU jobs were
started, and existing acquisition/model jobs were not disturbed.

Two opportunities must be evaluated separately:

1. **Faster evaluations, same sampler:** compile the same likelihood, batch
   particles and similarly shaped towns, and keep repeated arrays resident on the
   device. JAX's `vmap` supplies a batching transformation. This is a throughput
   change, not permission to approximate the model. [JAX vmap](https://docs.jax.dev/en/latest/_autosummary/jax.vmap.html).
2. **Better movement, same target:** use derivatives of the marginalized likelihood
   in Metropolis-corrected HMC or MALA at each SMC temperature,
   `log prior + beta * log likelihood`. Discrete designs remain summed out.
   Correctly implemented, this need not change the posterior target. It does
   change Monte Carlo behavior and must beat the random-walk kernel on error and
   effective sampling per resource-hour, not just proposals/second.

For the first batching pilot, use float64 and the existing positive convolutions.
JAX defaults to 32-bit; the current `1e-300` floor and very small milestone
probabilities cannot simply be moved to that dtype unchanged. We have already
encountered cancellation problems with FFT-based alternatives; no float32, mixed
precision, FFT-tail clipping or learned-surrogate replacement is presumed safe.
[JAX precision documentation](https://docs.jax.dev/en/latest/101/default_dtypes.html).

The port also needs static/padded or bucketed observation shapes, precompiled span
indices, and finite gradients through masked impossible paths. `log(0)`, all-impossible
masked rows and tiny CDF differences need care; a finite scalar likelihood alone
does not certify its automatic derivatives. Centering/reparameterization must
preserve the prior and Jacobian. Gradient checks are a bounded implementation
requirement, not a new corpus verification campaign.

Measure compilation, transfer, steady-state synchronized runtime and memory
separately. JAX dispatch is asynchronous, so timing without a readiness barrier
can time only submission. GPU execution is not guaranteed faster for tiny batches.
[JAX benchmarking guidance](https://docs.jax.dev/en/latest/benchmarking.html).

Other paths: a compiled CPU kernel can reduce Python overhead; GPU array libraries
can accelerate large batches without changing the sampler, but a mechanical
array-library replacement leaves Python loops and repeated device transfers.
Multiple GPUs should initially shard independent particle batches or independent
runs; do not introduce nested worker/GPU contention. NUTS is possible, but
fixed-length batched HMC is a reasonable first GPU kernel because different
trajectory depths complicate batching. No hardware speed factor is promised.

### Bounded next experiment (not launched)

- Port one town likelihood and its gradient, then a batched complete likelihood.
  Use the current exact implementation as the test oracle, not a competing
  permanent production backend.
- Test 16/128/512-particle batches on CPU and one available sk3 GPU. Use varied
  supported and incompatible observations; check log-likelihood difference ≤1e-10
  on the fixed regression set and finite-difference gradients at interior points.
- If throughput is worthwhile, compare a fixed-budget Metropolis-corrected
  HMC/MALA-SMC pilot against current SMC, with independent runs and matched
  posterior intervals. Record compilation amortization and GPU versus CPU-hours.
- Stop after the pilot and report success/failure. Promote a sole production
  path only after equivalence and useful effective-sampling performance are shown.

Rejected shortcuts for this pilot: uncorrected stochastic-gradient sampling,
variational/Laplace output presented as the same posterior, unvalidated surrogate
likelihoods, lower precision with changed tails, arbitrary design pruning, and
reducing particles until an appealing wall time appears. Metropolis-corrected
delayed acceptance could use a surrogate **without** changing the target, but its
exact second stage and benefit would need their own bounded test; none is added here.
