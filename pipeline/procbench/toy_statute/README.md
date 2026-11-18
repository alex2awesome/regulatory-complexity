# Toy-statute inference: one active implementation

Use the corrected model and SMC driver:

```sh
python -m pipeline.procbench.toy_statute.smc \
  --evidence <world>/evidence --out <new-fit-directory> \
  --runs 2 --particles 2000 --moves 12 --workers 4 --gate v2
```

`python -m pipeline.procbench.toy_statute.fit` is an alias for the same driver,
with identical options/defaults. There is no alternate MAP/Laplace/MCMC fitter.
Historical `fit.run`, `--keep-mult`, FFT/capped-convolution helpers, backend
switches and the mean-matched Poisson survey shortcut are retired. To reproduce
historical algorithms, use their archived source snapshots, not current imports.

The active path is:

- `model.py`: one corrected process likelihood; discrete designs/paths summed out.
- `grid.py`: cached positive convolutions, full support or unnormalized prefixes.
- `smc.py`: process-posterior sampling, launch preflight and provenance.
- `fit.py` / `estimands.py`: shared answer generation and burden summaries.
- `readings.py`: one grouped reading integration kernel and shared scoring logic.
- `hypotheses.py`: global reader-hypothesis uncertainty and BMA using that same kernel.
- `outcomes.py`: conditional count-mixture likelihood and the separate outcome-cut
  inference stage. This is a different scientific layer, not an old process backend.

Choice models, prior sensitivities and independent/hierarchical reading models
remain explicit scientific options. There is no switch to a slower or defective
implementation of the same calculation. Independent numerical references live
only in `tests/toy_statute_reference.py`, never imported by production modules.

The process target is `toy-process-v3-20261002` (stable conditional duration PMFs,
full-support survival, and opt-in real-report observation settings). Old-target particles are not
compatible with current Stage C/outcome cuts. Refactoring preserves this target;
the preceding likelihood repairs did change it. Existing worlds and runs are not
overwritten. Remote jobs using frozen older snapshots are not updated by local edits.

## Configurable execution and scientific settings

The CPU path remains the default and has no JAX dependency. With a separately
installed float64 JAX environment, the same SMC command accepts an execution
configuration:

```sh
python -m pipeline.procbench.toy_statute.smc \
  --evidence <public-evidence-directory> --out <new-fit-directory> \
  --package <public-process-catalog.json> --center-towns \
  --model-config pipeline/procbench/toy_statute/configs/legacy_model.json \
  --execution-config pipeline/procbench/toy_statute/configs/jax_rw.json \
  --runs 2 --particles 10000 --moves 30 --gate v2
```

Use `configs/jax_hmc.json` for Metropolis-corrected HMC mutation inside SMC.
`--moves` then counts HMC trajectories; `hmc_steps` is the number of leapfrog
steps per trajectory, not extra independent samples. Both kernels keep particles
on the device for an entire mutation batch. The shared driver still chooses
temperatures, resamples and estimates particle covariance. Geometry and step
size are fixed within a stage; scale adapts only between stages. JAX and NumPy
use different RNG streams, so equal seeds do not promise identical trajectories.
No particle-count reduction is automatic. Accelerator acceptance, nonfinite/
divergent proposal counts, device and bucket count are saved with each stage.
On shared sk3, check current GPU utilization and free memory before selecting
`CUDA_VISIBLE_DEVICES`; set `XLA_PYTHON_CLIENT_PREALLOCATE=false`. A `jax` backend
does not itself promise a GPU: inspect the recorded device. The bounded tests
used a separately installed CUDA-13 JAX environment, not the local CPU Python.

`ExecutionConfig` controls `backend`, `kernel`, `batch_size`, `bucket_towns`,
`hmc_steps`, `hmc_step_size`. `bucket_towns=false` is a diagnostic ablation of
batching, not an alternative likelihood. Buckets require matching compiled
topology and array shapes; numerical observations and local parameters remain
town-specific. Heterogeneous towns are never forced into an incorrect template.

`ModelConfig` controls per-step day/hour support, maximum correction loops,
contamination probability/support and an optional declared posting window.
The included legacy file preserves existing settings. Custom settings change
the scientific target and propagate into likelihoods, predictions, burden and
Stage-C consumers. They are stored and checked separately from execution
settings. Priors and design priors still use `--prior-json`; public step/event/
design catalogs use `--package`; reporting-mask probabilities remain declared
in `public_spec.json`. Input file hashes and resolved settings enter manifests.

Only the current `serial_completeness_loop` process family and
`complete_partition_uniform_posting` observation family are implemented here.
Unknown configuration keys/families fail explicitly. **This is not yet a
general Solar/ADU graph or partial-report adapter.** Do not label its synthetic
posting rule, repeat cap or generic town effect as learned real-world facts.
Catalogs remain process-global; run different catalogs in separate processes.

Administrative rows are compressed by whole-record timing patterns and matching
source/cohort/other metadata. Dates may differ when all modeled elapsed intervals
agree. All milestones of one record are multiplied **before** path marginalization;
the resulting case likelihood is weighted by its positive integer `multiplicity`.
No source records are deleted, and repeated retellings of one applicant must
still be reconciled upstream. Counts are not independent marginal histograms.
`Model(..., compress_administrative=False)` is the equivalence/benchmark control.
Coarse time-bin cohorts, terminal outcomes and uncertain actor mixtures are not
silently converted to exact completed records.

Execution/results: [configurable speedups](../../../docs/2026-09-30-configurable-inference-speedups.md).
The example accelerator configurations are opt-in experiments, not a promise
of equal precision at a smaller budget. At the tested W0 budget the device RW
pair matches the pooled CPU reference, but narrowly misses one between-run
quantile threshold and is not faster than the previous GPU experiment. Read
the result/gate record before promoting either kernel for a scientific run.
The full W0 HMC-SMC pair passes all declared posterior comparisons, using
stage-wise particle covariance rather than reference-fit tuning, but takes
49.09 minutes versus device RW's 6.08 minutes. It is a validated W0 option,
not a demonstrated throughput improvement or an other-statute certificate.

For future fits reused by multiple Stage-C conditions, add `--cache-town-loglik`.
This saves final town-by-design likelihoods with input/parameter-order hashes,
costing one extra final likelihood pass and O(particles × towns × designs) storage.
The hypothesis-space runner consumes a complete matching cache automatically;
older fits without caches still use the same likelihood computation. This does
not alter proposals, random-number draws, particles, priors or the target.

The compiler now reuses identical **whole-report** timing calculations and path
spans, retaining each case's own mentions, hours and observation-mask likelihood.
It does not treat individual gaps as independent after case-path marginalization.
Exact-equivalence source fingerprints for the v2 optimization are recorded in
`likelihood_compatibility.json`; a different fingerprint is not silently certified.

Details: [repairs](../../../docs/2026-09-30-toy-statute-audit-repairs.md),
[single-path refactor](../../../docs/2026-09-30-toy-statute-single-path-refactor.md).
[Hypothesis spaces](../../../docs/2026-09-30-hypothesis-space-results.md) and
[scaling review](../../../docs/2026-09-30-scaling-inference-review.md).

Focused checks:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest \
  tests/test_toy_statute*.py -q
```

The optional JAX module skips when JAX is absent. In the separate accelerator
environment, run `python -m pytest tests/test_toy_statute_jax.py -q` explicitly.
