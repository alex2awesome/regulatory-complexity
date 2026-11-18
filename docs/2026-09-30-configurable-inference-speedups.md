# Configurable inference and remaining speedups

2026-09-30; completed 2026-10-01. Requested by Alex after the W0
posterior-equivalence comparison.

**Completed verdict:** all four mechanisms and configuration are implemented.
Exact numerical checks pass. Town bucketing delivers a measured throughput
gain. The new HMC-SMC pair passes every declared posterior-agreement gate but
is slower at these settings. The new device RW pair matches the pooled CPU
reference but narrowly fails one between-run quantile gate. Neither new kernel
is promoted over the unchanged CPU default, and no general Solar/ADU portability
or 500-town posterior-mixing claim is made.

## Scope and definition of done

Implement exact multiplicity compression of exchangeable **whole** admin
records; JAX bucketing of compatible town computations; device-resident
Metropolis mutation; and Metropolis-corrected HMC mutation inside the existing
adaptive SMC driver. Expose validated scientific and execution configurations,
with unchanged legacy defaults and manifest-bound settings. Keep one SMC
tempering/resampling implementation. No particle reduction, float32, pruning,
independent milestone marginalization or changes to active remote jobs.

Configuration covers the supported serial process family, duration support,
repeat cap, reporting/selection conventions, contamination, priors, catalog,
and execution backend/kernel/batch size. It must reject unsupported observation
or graph semantics. Arbitrary concurrent graphs, uncertain actor assignments,
and learned source-specific selection are substantive model extensions, not
configuration flags that can safely be invented here. This task does not claim
a completed Solar/ADU full-process fit.

Budget: one implementation pass, focused regression/reference checks, a bounded
GPU benchmark and paired full W0 SMC comparisons with the existing reference.
Keep failed configurations; no repeated tuning or chain extensions to pass.
Maximum 90 minutes per launched remote experiment. New microbenchmarks use
public evidence or mechanical duplicates only, not hidden benchmark truth.
Completion means implemented features with explicit correctness/performance
results and limitations, not a guarantee each optimization wins on small W0.

The pre-edit source is retained at
`runs/toy_configurable_20260930/source_before/`. Current CPU reference draws
and old experimental JAX sources remain untouched.

Full-run settings declared before launch: two new seeds (20273001/20274001),
10,000 particles each; device random walk 30 moves per stage (60 final),
HMC six trajectories per stage (12 final), eight leapfrog steps, initial step
size 0.1, covariance from each stage's particle population, adaptation only
between stages toward 0.8 acceptance. Batch size 256. HMC uses no reference-fit
covariance. Compare both runs and the pooled reference with the preceding W0
gates: mean discrepancy <=0.1 posterior SD, SD discrepancy <=10%, 5/50/95%
quantile discrepancies <=0.2 SD; design probabilities <=0.025 absolute. Include
joint structure/parameter timing, execution-count and speed summaries. Smaller
HMC move count is a declared kernel comparison, not an automatic precision cut.
Do not re-tune on a failed result. GPUs 6/7 have idle compute and about 18 GiB
unallocated memory at launch; disable preallocation and use a 4% allocator budget.
The active VLLM acquisition workers on other GPUs are not changed.

## What changed

All four requested mechanisms are implemented, opt-in where they change the
execution kernel. The scientific CPU default remains unchanged.

- `compression.py` replaces repeated exchangeable **whole-case** administrative
  likelihoods by positive integer multiplicities. It retains source/cohort/other
  metadata and all jointly reported milestone offsets. Calendar dates can differ
  because this model currently conditions on elapsed intervals, not calendar time.
  This is not applicant deduplication or arbitrary interval-histogram ingestion.
- `jax_backend.py` is the optional production float64 implementation of the
  corrected likelihood. Compatible town topologies/array shapes are bucketed and
  vectorized; observations and local parameters remain town-specific. Bucketing
  is separately switchable for checks. It is not an assumption that towns share
  observations, parameters, or a latent design.
- `jax_pool.py` executes all mutations for a particle batch on the device. The
  same `smc.py` still performs tempering, resampling and covariance estimation.
  Device random-walk RNG streams differ from NumPy, so equivalence concerns the
  target and posterior, not bitwise particle trajectories.
- `jax_pool.py` also supplies Metropolis-corrected fixed-length HMC within that
  same SMC driver. Its geometry comes from current particles at each temperature,
  not a reference fit. Geometry and step size stay fixed during each stage.
- `config.py` separates scientific from execution settings, rejects unknown keys
  and unsupported families, and binds scientific settings to manifests and
  downstream target checks. Model-local grids/caps reach shared estimands,
  reading costs, hypothesis-averaged burdens and normal Stage-C/outcome loaders.
  Historical standalone drivers that reconstruct only the default model reject
  incompatible fits; they are not silently upgraded to new scientific settings.

### Mathematical preservation

For design `s`, case path `z`, and the vector of milestones `y_j` for one case,
compression computes

`log L_s = sum_j n_j * log(sum_z p(z | s, theta) p(y_j | z, s, theta))`.

The count multiplies the **marginal whole-case log likelihood**. Neither the
milestones nor latent paths become independent through compression. Town design
probabilities are then integrated in the same place as before. This preserves
the old posterior when multiplicities represent distinct exchangeable cases.

At temperature `beta`, both mutation kernels target
`pi_beta(theta) proportional to prior(theta) likelihood(theta)^beta`.
For HMC, with covariance factor `C = L L^T`, momentum `r ~ N(0,I)` and step
size `epsilon`, the updates use `theta += epsilon L r` and
`r += epsilon L^T gradient log pi_beta(theta)` (half momentum steps at the
ends). Acceptance includes the exact kinetic-energy difference. This is ordinary
preconditioned leapfrog in whitened coordinates. Numerical divergences are
recorded, not made into an additional selection criterion; nonfinite targets
are rejected. No approximate likelihood, float32, gradient subsampling or
unadjusted Langevin step was introduced. Discrete designs and paths remain
exactly enumerated/summed out.

As with the existing adaptive finite-particle SMC, kernel target preservation
does not make a finite run an exact independent posterior sample. Repeated-run
agreement and comparison to the reference remain necessary. Do not interpret
SMC particle order as a sequential MCMC chain for ESS/R-hat purposes.

## Bounded checks and measurements

Checked against the uncompressed corrected CPU likelihood on public W0 evidence:

- Maximum compression difference: `1.14e-13` (16 parameter points).
- Reference evidence hashes/target guard match; saved CPU likelihoods reproduce
  to `1.14e-13` at the same 16 preselected positions.
- Maximum float64 JAX/CPU difference: `1.14e-13`.
- Maximum difference after 100x administrative replication: `3.64e-12`.
- All 36 gradient coordinates checked by finite differences; maximum scaled
  discrepancy `1.11e-8`.
- 8,000 administrative rows compressed to 55 whole-case timing patterns. On that
  small synthetic duplicate fixture, CPU evaluation was only 1.24x faster
  (12.09 ms to 9.74 ms): the rest of this likelihood still costs time.
- Sixteen W0 likelihoods: CPU 162.1 ms, GPU 7.62 ms warm; initial GPU compilation
  and first call 15.57 s. This is not an end-to-end fit speedup.

Town scaling uses mechanically replicated **public observations** with varying
town parameters, not newly generated truth or a fit to a heterogeneous real
corpus. All likelihood errors are below the predeclared `1e-10` threshold.

| Towns | Compatible buckets | Cold compile + call (s) | Warm evaluation (ms) | Max absolute CPU/GPU difference |
|---|---:|---:|---:|---:|
| 12 | 3 | 5.11 | 2.44 | 9.09e-13 |
| 50 | 3 | 6.37 | 2.92 | 1.82e-12 |
| 200 | 3 | 5.82 | 3.41 | 2.18e-11 |
| 500 | 3 | 7.49 | 5.11 | 2.91e-11 |

Separate same-GPU bucketing ablation: 12 towns improve from 6.46 to 2.43 ms
(2.66x), and 50 towns from 25.47 to 2.93 ms (8.69x), with identical values.
Cold compile/call improves from 12.12 to 4.68 s and 30.08 to 7.37 s respectively.
This isolates the batching benefit. It does **not** prove an equivalent gain
in posterior precision per second at 500 towns. Highly heterogeneous evidence
may create many buckets and reduce that benefit.

### Full W0 device random-walk SMC

Two 10,000-particle, 30-move runs completed in 185.01 and 179.71 s: **6.08 min
combined**. They use different seeds from both earlier CPU and GPU runs. Both
have nine temperature stages and no nonfinite proposals among six million total
proposals. Values are sampling times including initialization/JIT, excluding
post-fit answer construction and comparison.

Pooled versus the CPU reference: all 36 parameter gates pass (maximum mean
discrepancy 0.0422 SD, SD discrepancy 2.76%, quantile discrepancy 0.109 SD).
Design probabilities, joint design/parameter timing and execution counts, and
relative town speeds all pass too. Maximum design-probability difference is
`7.06e-5`.

**The full validation verdict is nevertheless FAIL at this fixed budget:**
the two new ensembles differ by 0.2167 SD on a duration-spread quantile
(`lsig_desk_review`), above the predeclared 0.2 threshold. Other primitive
checks and all derived between-run checks pass. This isolated miss is not
evidence of a different likelihood, but it prevents an unqualified
posterior-equivalence/mixing claim. No seed, gate or budget was changed to
remove the miss.

Runtime does not improve on the previous host-proposal GPU experiment (5.49 min
combined). The 6.08 min result is about 11% slower, with different batching,
kernel compilation and shared-GPU load. Both are much faster than the historical
64.15 min CPU reference, but that is not an equal-resource speed benchmark.
Device residency is available; it is not advertised as a demonstrated W0 gain.

### Full W0 HMC within SMC

**PASS at the predeclared budget**, both against the CPU reference and between
the two new independent ensembles. All 36 parameters, town design probabilities,
joint design/parameter timing and execution-count distributions, and relative
town-speed distributions pass. No gate, seed, trajectory length or move count
was changed after seeing a result.

| Comparison | Maximum parameter mean discrepancy (SD) | Maximum parameter SD discrepancy | Maximum parameter quantile discrepancy (SD) | Maximum design-probability discrepancy |
|---|---:|---:|---:|---:|
| New HMC runs against each other | 0.0385 | 3.19% | 0.0974 | 0.000198 |
| Pooled HMC against pooled CPU reference | 0.0380 | 3.42% | 0.1144 | 0.000264 |

Joint timing/count quantile discrepancies against the CPU reference are at most
0.0820 SD; relative-speed quantile discrepancies at most 0.0948 SD. These
summaries integrate over both designs and parameters. They are uncertainty
intervals for conditional population summaries, not individual-case predictive
intervals. SMC particles are not ordered chains; no new MCMC ESS/R-hat claim is
made. The prior fixed-HMC experiment's time-series diagnostics remain a separate
result.

Runs took 1,475.53 and 1,469.90 s: **49.09 min combined**, versus device RW's
6.08 min. Both had nine stages and 600,000 HMC proposals, with final acceptance
0.811/0.814 and log normalizers -528.41/-528.37. Combined nonfinite/large-energy-
error diagnostics numbered 229/289 (518 of 1.2 million proposals, 0.0432%).
The test proves neither that these diagnostics are harmless on other targets
nor that high acceptance alone establishes mixing; the declared posterior
comparisons supply the measured W0 evidence.

Unlike the earlier fixed-HMC chain experiment, these fits learned their proposal
covariance from the current tempering population, **not** the CPU reference.
HMC at this trajectory/batch setting is about 8.1x slower than the new device
RW pair. That RW pair failed one gate, so this is not an equal-precision speed
comparison either. No posterior precision/resource-hour advantage is claimed
for HMC, no lower-particle HMC budget was tried, and there is no automatic switch
to it. It remains a validated **W0 configuration option**, not a blanket
replacement recommendation.

### Tests and failure record

Local focused suite: 118 passed, one optional JAX module skipped (JAX not installed
locally). Remote JAX suite: three tests passed, including Gaussian target moments,
seed reproducibility for RW/HMC, and custom-support CPU/GPU agreement. The town
test was then strengthened to use different actual webpage observations and
rerun once: passed. A configuration propagation check additionally compares the
hypothesis-averaged burden path to shared estimands on reduced grids/repeat caps.

Initial GPU check `checks001` failed on a traced NumPy contamination lookup;
the lookup was changed to JAX indexing and the bounded check rerun as
`checks002`. The failed launch remains on sk3. CUDA autotuning emitted delay-timer
warnings; wall-clock measurements above explicitly synchronize returned arrays.
Shared hardware and load still limit comparisons across different experiments.

## Configuration and use

See [the package README](../pipeline/procbench/toy_statute/README.md) for commands.
Examples are `configs/legacy_model.json`, `configs/jax_rw.json` and
`configs/jax_hmc.json` in that package.

- Scientific JSON: `day_grid_size`, `hour_grid_size`, `max_loops`,
  `contamination_probability`, `contamination_max_days`, `post_day_range`,
  `process_family`, `observation_family`.
- Execution JSON: `backend`, `kernel`, `batch_size`, `bucket_towns`, `hmc_steps`,
  `hmc_step_size`. `--moves` counts trajectories for HMC, not leapfrog steps.
- Existing options remain: `--package` for the public catalog, `--prior-json`
  for declared priors, `--center-towns`, particle/move/run budgets, and saved
  per-town likelihood caches. Compression can be disabled through the Model API
  for reference checks. Catalogs remain process-global; use separate processes
  for distinct catalogs.

Changing grid limits, loop caps or contamination changes the scientific model;
it is not a guaranteed-equivalent speed optimization. These are assumptions,
not newly learned parameters. The likelihood-equivalence certificate covers
legacy scientific defaults; manifest checks separately reject mismatched custom
settings. Kernel/batching changes should leave the scientific target unchanged,
but their finite-run posterior quality still needs checking.

The accelerated engine is useful for eventual Solar/ADU fits; these changes do
not supply a general concurrent graph, partial-report likelihood, calibrated
source-selection model, or uncertain agency/geography assignments. Do not force
real records into the toy model merely because its engine is now configurable.

## Receipts and preservation

Local receipts: `runs/toy_configurable_20260930/`:

- `source_before/`: pre-edit package snapshot;
- `check_acceleration.py`: checks and frozen full-fit settings;
- `checks002/checks.json`, `scaling.json`, `ablation001/ablation.json`;
- `reference_binding_check.json`: reference evidence/target/saved-likelihood check;
- `joint001/`: both particles, stage diagnostics, launch/completion records;
- `summarize_acceleration.py`, `observables/`, `comparison.json`: fixed-gate
  comparison, including failures and mixtures over designs and parameters;
- `hmc001/`: both completed particles, stage diagnostics and launch/completion
  records; all compared outputs have been copied locally.

Frozen remote source/run root:
`/dfs/scratch0/alexspan/toy_configurable_20260930/code/` on sk3. Full scaling
fixture inputs remain there; their small launch/scaling/completion receipts and
the failed `checks001` launch are copied locally. The only later Python-file
difference from the fit snapshot is `hypotheses.py`'s custom-support burden-summary
fix, covered by the local regression suite; it is not imported by these SMC fits.
Benchmarks read public evidence and the existing
CPU reference particles, not hidden truth. Raw corpora, previous fitted outputs,
acquisition jobs, other users' GPU memory reservations and Git staging/commits
were not changed. JAX jobs used only GPUs 6/7, idle compute with approximately
18 GiB free at launch, with preallocation disabled and a 4% allocator budget.
The task reused the isolated CUDA-13 environment and installed pytest there for
the optional tests; no system CUDA installation was changed.
