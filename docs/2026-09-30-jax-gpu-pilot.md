# JAX/GPU pilot: execution record

Requested 2026-09-30 after the scaling review. This is an actual port/benchmark,
not another recommendations document. Production inference is not replaced until
the measured outcome supports doing so. Existing fits are left running unchanged.

Alex's revised order is now in effect: **scaling benchmark → town-local cache and
blocked moves → JAX likelihood/batching → gradient mutation within SMC**. The CPU
measurements below finished before starting the GPU benchmark. No full 500-town
fit was launched. This document is the consolidated execution/results record.

## Fixed scope before execution

- Port the toy process's complete v2 likelihood and prior to float64 JAX, using
  public evidence and the existing compiler. Preserve design/path marginalization,
  joint selected-report timing, exact administrative milestones, pending survival,
  hours, webpage observations, centering and the block-coordinate prior.
- Positive direct convolutions; no FFT replacement, dropped designs, changed grid,
  float32 shortcut, hidden-truth input or likelihood approximation.
- Validate finite/support behavior and scalar likelihood agreement on held evidence,
  and derivatives against finite differences. Gate: likelihood error ≤1e-10 at the
  prespecified interior points; relative gradient error ≤1e-4 away from numerical
  boundaries. Report failures, not adjusted thresholds.
- Measure synchronized cold compile and warm CPU/GPU likelihood/gradient batches
  of 16, 128 and 512 particles where memory/runtime permit. Do not assume GPU wins.
- Run a bounded Metropolis-corrected gradient sampling pilot and a random-walk
  comparator on the same posterior. Maximum 4 chains × (128 warmup + 256 retained
  iterations) per kernel in the first pilot. This is not automatically convergence.
  Report acceptance, numerical diagnostics, effective sampling and intervals.
- After correctness, exercise the same HMC move inside a separately labeled
  tiny SMC pilot: 16 particles, two independent runs per kernel, four fixed
  temperatures (0.1, 0.3, 0.6, 1.0), two moves per stage. This tests wiring and
  actual tempered mutation; report weight/ancestor collapse rather than treating
  a 16-particle run as reliable scientific inference. No budget escalation.
- One debugging/implementation pass and one measured pilot, not repeated tuning
  until a favorable result. Long computation stays in dedicated sk3 scratch.

Hardware check: eight B200 GPUs, all with existing allocations. GPU 0 had low
observed utilization and over 100 GiB free; use a modest bounded allocation there
without stopping or modifying other users' processes. Shared-machine contention
will be disclosed. Install in a new isolated environment, not a shared one.

Artifacts: `runs/toy_jax_pilot_20260930/`; remote execution under
`/dfs/scratch0/alexspan/toy_jax_pilot_20260930/`. Results appended here when measured.

## 1. Scaling benchmark and blocked CPU moves: completed

Fixture: deterministic replication of **public W4 observations**, not a new
scientific world or recovery experiment. Per administrative/report stream, 40%
of towns have zero records, 30% one, 15% two, 10% five and 5% twenty (small panels
use quantile allocation). Every town has its observed webpage, including negative
listings. At 500 towns this is 1,050 administrative records + 1,050 forum records
+ 500 webpages. Repeated payloads measure computation, not independent evidence.
The first fixture attempt hit an empty administrative pool in one source town;
the corrected fixture falls back to the public pooled records. No fitted output
was involved. Both the failed attempt and corrected fixture remain on sk3.

Single-threaded NumPy/SciPy on shared sk3 (AMD EPYC 9565, 288 logical CPUs),
with BLAS/OpenMP limited to one thread:

| Towns | Full evaluation, 6 designs (s) | Full evaluation, 11 designs (s) | Naive local sweep, 11 designs (s) | Cached blocked sweep, 11 designs (s) |
|---:|---:|---:|---:|---:|
| 12 | 0.0178 | 0.0218 | 0.264 | 0.092 |
| 50 | 0.0749 | 0.0948 | 4.73* | 0.415 |
| 200 | 0.302 | 0.383 | 77.7* | 1.66 |
| 500 | 0.813 | 1.031 | 511* | 4.20 |

Full-evaluation entries are medians of three calls; blocked sweeps are means of
two fully executed sweeps. `*` Naive full-sweep costs project from **four measured
consecutive proposals**, each changing one town and recomputing all towns. The
12-town naive sweep was executed in full. These projections are not measured
8.5-minute runs. At 500 towns, the 6-design cached sweep is 3.245 s versus a
407.7 s naive-sweep projection.

Important comparison boundary: the naive sweep has T single-town proposals;
the cached sweep has **one shared proposal + T joint correction/objection
proposals + T−1 paired-speed proposals**. They are not identical kernels or equal
mixing budgets. The original production sampler proposes all coordinates jointly;
we have **not** established how many of those joint proposals equal a blocked
sweep in effective samples. Do not advertise a 120× end-to-end fit speedup.

The measured computational lesson is nevertheless clear. Evaluation cost is
roughly linear over this range, while naive local sweeps multiply it by T.
6 → 11 designs adds about 25–35% here, much less than the repeated all-town
work. This is not evidence that truly combinatorial design menus are cheap.
No ESS/hour, convergence, or real-world posterior claim follows from this table.

### Implementation and target preservation

- `pipeline/procbench/toy_statute/blocked.py`: per-particle town likelihoods,
  sparse coordinate/prior updates, full shared moves, paired speed moves and a
  separate update of the nuisance raw speed mean. Local proposals do not rebuild
  the full parameter dictionary/prior/vector, avoiding hidden O(T²) overhead.
- `Model.town_struct_loglik_from_params`: the same unchanged likelihood body,
  exposed after parameter mapping/centering. The ordinary entry point delegates.
- `smc.py --move-kernel blocked`: available for new opt-in experiments. `--moves`
  means **sweeps** with this option; the default remains the existing joint kernel.
  Geometry is computed from shared and small local covariance blocks, avoiding
  a dense O((3T+G)³) Cholesky. Mutation geometry is frozen within each SMC stage.
- A sweep evaluates **4T−2 town factors** when centered, including the shared
  move, versus T² town factors for the naive T-proposal sweep. It retains all
  designs, paths, observations and priors; no constant-town shortcut is assumed.

For a local symmetric proposal at inverse temperature beta, acceptance uses
`delta log prior + beta * sum_changed_towns(delta log likelihood)`. The centered
speed transform is `a_eff[t] = a_raw[t] − mean(a_raw)`. Changing one raw speed
would change every town, so speed proposals change two raw values by `(+d,−d)`.
A random spanning path supplies all T−1 contrast directions. These moves alone
would freeze the raw mean; its additional update is necessary for the **same
joint prior**, even though the likelihood does not see that direction.

For independent normal raw-speed priors N(m_t,s_t²), with fixed contrasts c_t,
the exact conditional raw mean has precision `sum_t 1/s_t²` and mean
`sum_t (m_t−c_t)/s_t² / sum_t 1/s_t²`. This includes heterogeneous normal prior
overrides. Other prior families use a symmetric prior-only MH common shift.
No prior is replaced with a contrast-only approximation.

**99 focused tests pass.** Checks cover changed blocks, centered/uncentered
coordinates, accept/reject replay against full recomputation, cache restoration,
invalid one-town centered changes, the conditional grand-mean draw, and the SMC
worker path. The scaling runs' maximum final full-vs-cache log-likelihood
difference is **5.46e−12**, under the declared 1e−10 gate. High acceptance in the
timing fixture reflects deliberately small proposals; it is not good-mixing
evidence. Sampler source/defaults of existing remote fits were not modified.

Receipts: `runs/toy_jax_pilot_20260930/scaling_baseline_results.json`,
`scaling_blocked_results.json`, and the reproducible `scaling_benchmark.py`.
Large fixture JSON remains in the dedicated sk3 experiment directory.

## 2. JAX/GPU pilot: measured results

Isolated remote environment installed successfully (JAX/JAXlib 0.11.2, CUDA 12
plugin, NumPy 2.5.3, SciPy 1.18.1); no shared environment changed. GPU load was
checked again immediately before launch. GPU 0 showed 0% utilization, 62,616 MiB
allocated out of 183,359 MiB. Pilot uses device 0, float64, disabled preallocation and a 4%
allocator fraction. It neither calls acquisition APIs nor stops/changes jobs.
All timing is shared-machine timing, not an exclusive-hardware benchmark.

First GPU attempt: all three W0 scalar/design likelihood checks agreed within
1.14e−13, but result serialization rejected a NumPy boolean (fixed with explicit
`bool`). More importantly, JAX warned that installed cuBLAS 12.9 has a known
concurrent-kernel corruption risk on this hardware. No sampling was performed
with that stack. Its partial result directory is retained as `gpu_w0`. Installing
a **separate** CUDA 13 environment (`env13`), leaving the first one unchanged;
driver 580.82.07 meets JAX's CUDA 13 requirement. See
[official JAX installation guidance](https://docs.jax.dev/en/latest/installation.html).
The first CUDA 13 install failed when uv's **default local-disk cache** ran out
of space. The retry places its cache explicitly inside the dedicated DFS task
directory; no shared cache cleanup or deletion was performed.
The isolated CUDA 13 installation then succeeded: cuBLAS 13.8.1.7, CUDA runtime
13.4.92, cuDNN 9.27.0.42, JAX/JAXlib 0.11.2. The actual pilot was launched with
a 20-minute wall-clock cap, eight affinity CPUs for compilation, and the same
GPU-0 memory limits after another utilization check. Local sk3 storage was still
nearly full independently of this DFS retry; future installs must specify the
DFS cache rather than assume uv's default cache is safe.

### CPU control (completed, not a speedup)

JAX CPU on W0m passes three per-design/full-likelihood comparisons (max error
2.27e−13) and all 36 finite-difference gradient checks (max scaled error
5.99e−9). W0's CPU batch of 16 also agrees within 1.14e−13. But positive direct
convolution under this `vmap` lowering is **much slower on CPU**: warmed batch
likelihood median 10.350 s, gradient median 45.800 s, versus 0.183 s for 16
ordinary NumPy/SciPy evaluations. Cold calls are 13.941 s and 53.010 s respectively
(compilation plus first execution, not pure compilation). JAX CPU was limited to
four affinity CPUs; BLAS/OpenMP remained one-threaded. This is not a claim that
every possible JAX CPU implementation is slow; it rejects this lowering as a
replacement for our optimized CPU oracle.

Receipts: `cpu_w0m_check/results.json`, `cpu_w0_batch16/results.json` under the
pilot run directory. Further large CPU batching is not warranted by this result.

### Gradient sampler mathematics and limits

The gradient kernel targets `log p(theta) + beta * log L(theta)`, after the same
exact sums over designs and paths. In fixed affine coordinates
`theta = origin + scales * z`, the Jacobian is a constant and cancels in MH.
Momentum is standard normal. Four leapfrog steps propose `(z', r')`, accepted
with probability `min(1, exp(log_target(z')−log_target(z) + (||r||²−||r'||²)/2))`.
Thus finite-step integration error is Metropolis-corrected; it is not a change
to the discretized statistical model. All computations remain float64.

The stand-alone chain pilot adapts only step size during 128 warmup iterations,
then freezes it for 256 retained iterations; four chains per kernel share the
same slightly jittered prior-center initialization (not overdispersed draws).
The comparator is a symmetric random walk with
the same fixed affine scaling, **not the production particle-covariance SMC
sampler**. No NUTS, state-dependent stopping, likelihood surrogate, lower
precision or changed prior is used. The SMC pilot fixes both step size and move
count at every predeclared temperature, with ordinary importance weighting and
systematic resampling. Proposal scales/trajectory lengths affect mixing, not
the target; small particle counts and short chains still threaten estimation.

Even if GPU throughput is favorable, neither this W0 prototype nor its tiny
SMC run establishes end-to-end performance at 500 towns, a good posterior,
independent effective samples, or superiority to the new blocked CPU kernel.
The current JAX graph unrolls towns; production-scale town bucketing and
combining local caching with gradient moves remain distinct follow-up work.

### GPU batching: strong likelihood-throughput result

The CUDA 13 W0 run completed, including sampling and SMC. All three fixed-point
likelihood/structure/prior comparisons passed (largest likelihood error
1.14e−13), as did all 36 gradient coordinates (max scaled error 6.60e−9).
All 656 batch points also passed the 1e−10 gate, with maximum error 2.27e−13.
Every compared batch gradient was finite.

The wider W4 GPU check also passed: 12 towns, 11 designs, 63 continuous
coordinates; three fixed points, maximum full-likelihood error 2.27e−13,
maximum per-design error 2.71e−13, and all-coordinate finite-difference scaled
gradient error 1.94e−8. Its cold gradient call took 38.70 s. This checks a larger
catalog/panel, not a W4 posterior fit. Together with the W0m CPU milestone
check, it covers more than the throughput fixture without launching new fits.

| Particle batch | NumPy/SciPy CPU, serial (ms) | GPU likelihood, warm median (ms) | CPU/GPU ratio | GPU value + gradient, warm median (ms) |
|---:|---:|---:|---:|---:|
| 16 | 157.9 | 3.454 | 45.7× | 11.872 |
| 128 | 1,294.1 | 7.753 | 166.9× | 37.690 |
| 512 | 5,150.3 | 24.995 | 206.1× | 125.967 |

These are synchronized wall-clock timings, three warm measurements per entry.
They compare **one serial CPU evaluation stream against one GPU batch**, not a
288-CPU server against a GPU, nor equal-cost hardware, nor full fits. Cold
likelihood calls (compile + first execution) took 6.7–7.7 s per batch shape;
gradient cold calls took 8.7–10.9 s. Host→device transfer was 0.384 s on the
first batch and under 0.5 ms subsequently. Input compilation/import/setup is
not part of the warm ratio. Shared-device autotuning emitted three delay-timer
warnings at batch 512; the table uses explicit external readiness barriers,
not the internal autotuner's timing. Sampled process GPU allocation was 6,376 MiB
(an observation, not a measured peak). The process exited and released it.

### Actual sampling: not converged, not promoted

Each kernel ran 4 × (128 warmup + 256 retained) iterations at beta=1. The
retained arrays and intervals are saved, but **are not reliable posterior
estimates**. Standard rank-normalized diagnostics were computed once from those
arrays with `summarize_sampling.py`:

| Kernel | Retained seconds | Compile + warmup + retained seconds | Acceptance | Worst rank R-hat | Minimum / median bulk ESS |
|---|---:|---:|---:|---:|---:|
| GPU random walk | 1.587 | 12.172 | 27.4% | 2.913 | 4.75 / 5.78 |
| GPU HMC, 4 leapfrog steps | 10.671 | 32.699 | 77.6% | 1.624 | 6.91 / 44.02 |

All 36 coordinates miss R-hat <1.01 for **both** kernels. HMC improves mixing
per iteration, especially the median ESS, but costs more: the diagnostic
minimum ESS/retained-second is **0.65 for HMC versus 2.99 for random walk**.
With these unconverged chains those rates are not reliable efficiency estimates;
they certainly do not establish HMC as the winner per resource-hour. The
intervals have not stabilized across kernels. No tuning/repeated extensions
were used to chase a passing result.

### Gradient moves inside SMC: executed, too small for inference

Both kernels completed **two independent 16-particle SMC runs**, four fixed
temperatures and two mutations per stage. Final particle likelihoods were
checked against the CPU oracle: max difference 1.14e−13 across both kernels and
seeds. First runs cost 9.99 s (RW) and 16.83 s (HMC), including compilation;
second runs reused compiled functions and cost 0.258 s and 0.665 s.

The first tempering jump had ESS **1.82 and 1.23 out of 16**, retaining only
four and three distinct parents. Later within-stage ESS does not undo that
ancestry collapse. Independent log-normalizer estimates differ by about 23
nats: RW −572.975 vs −549.559; HMC −572.240 vs −549.138. HMC's 100% acceptance
here reflects tiny fixed steps, not successful exploration. These runs verify
the tempered-gradient/resampling machinery, **not posterior accuracy** and
not a reason to reduce production particles or use four fixed temperatures.

Artifacts: `runs/toy_jax_pilot_20260930/gpu13_w0/` contains `results.json`,
environment/source/evidence hashes, both four-chain draw arrays, four SMC
particle arrays and `standard_diagnostics.json`. The implementation and runner
are `jax_model.py` and `gpu_benchmark.py` in the pilot directory. Results/data
are gitignored, not archived merely because the report exists.
`gpu13_w4_check/results.json` records the wider GPU check; `source_final/`
retains the production Python source used in this task. The isolated remote
code directory retains the exact GPU experiment scripts and public inputs.

### Reproduction / scope boundaries

From the repo root, on sk3, with a **new** output directory for each invocation:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 runs/toy_jax_pilot_20260930/scaling_benchmark.py --mode baseline --out NEW_BASELINE_DIR
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 runs/toy_jax_pilot_20260930/scaling_benchmark.py --mode blocked --out NEW_BLOCKED_DIR
```

For the GPU runner use the task's `env13/bin/python`, recheck device availability
first, and set `CUDA_VISIBLE_DEVICES`, `JAX_ENABLE_X64=1`,
`XLA_PYTHON_CLIENT_PREALLOCATE=false`, `XLA_PYTHON_CLIENT_MEM_FRACTION=.04`,
`OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`. Run
`gpu_benchmark.py --mode all --world W0 --out NEW_GPU_DIR` from the experiment's
repo-shaped code root. Its defaults are the fixed budgets described above;
`--mode check --world W4` performs only the wider likelihood/gradient check.
No automatic rerun is scheduled. The new production `--move-kernel blocked`
flag is separate from this experimental GPU runner.

## Decision and remaining work

1. **Keep the structural optimization.** Cached, centered-safe blocked moves
   are available as an opt-in in the sole toy SMC driver, with the original
   likelihood/prior and no dense all-coordinate covariance factorization.
2. **Keep pursuing GPU likelihood batching.** Its benefit is now measured, not
   speculative. Do not use this port as a CPU replacement.
3. **Do not switch production sampling defaults yet.** The short HMC/RW chains
   fail convergence and the tiny SMC runs fail particle diversity. Next bounded
   comparison should retain adaptive tempering, use adequate particles and
   frozen/preconditioned moves, and compare independent-run interval stability
   and effective error per resource-hour against cached blocked CPU moves.
4. **Combine the two gains deliberately.** The current GPU prototype batches
   particles but unrolls towns. A production backend needs town-shape buckets,
   local cache invalidation and gradient moves on appropriate shared/local
   blocks, with memory/compilation measured at larger T. No 500-town GPU fit,
   real-corpus posterior improvement, or uncertainty-calibration improvement
   has been demonstrated in this task.

No acquisition calls, shared-job modifications, commits or deletions were made.
The existing long scientific fits continue on their original source snapshots.

## Completed follow-up: full posterior comparison

The bounded pilot results above are unchanged. The later
[full W0 equivalence experiment](2026-09-30-posterior-equivalence.md) closes the
posterior-comparison gap: two 10,000-particle GPU-backed production SMC runs
match the CPU reference, and longer preconditioned HMC chains converge and
match parameter and derived intervals (max rank R-hat 1.0014). Blocked CPU
chains still fail. GPU SMC sampling took 5.49 min versus 64.15 min for the
historical CPU reference, with the hardware/environment/timing caveats in that
report. No blanket other-world/large-town equivalence or default promotion is
claimed.
