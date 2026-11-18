# Audit of Codex's inference speedups, and what real data exposed (2026-10-01)

Requested by Alex ("audit what codex has done, and run the fast sped-up version"). Scope: the
configurable-speedup work in `pipeline/procbench/toy_statute/` (`docs/2026-09-30-configurable-inference-speedups.md`)
and a spot check of the 2026-09-30 Solar/ADU execution doc. One pass; the real-data fits are in
`docs/2026-10-01-real-data-process-fits.md`.

> **Follow-up (2026-10-01):** Codex's audit (`docs/2026-10-01-real-data-model-and-inference-audit.md`)
> found what this one missed: a zero-mass PMF defect in the shared discretizer at extreme states (ADU run
> invalid) and a failed exact prior-only check for the blocked sampler. Claude reproduced both. Item 0
> below ("pending contamination") does not repair deficient PMFs, and item 6's reading of mean
> log-likelihood gaps as mode mass is withdrawn.

## Verdict
The speedup work is sound and honestly reported. Every number I checked reproduces, failures are
kept and not promoted, and the equivalence certificate caught my own later edit. Running it on
real records exposed **three modeling gaps, two code bugs and one scaling limit**, none visible on synthetic worlds.
I fixed the gaps and bugs (defaults bit-identical; 123 tests); the scaling limit remains for Codex.

## What reproduces
- Focused suite: `pytest tests/test_toy_statute*.py`: 118 passed, 1 skipped (JAX module absent
  locally), as claimed. After my changes: 123 passed, 1 skipped.
- `runs/toy_configurable_20260930/comparison.json` matches the doc exactly: device random-walk
  pair passes vs the CPU reference (max mean diff 0.0422 SD, SD diff 2.76%, quantile diff 0.109 SD)
  but fails between-run agreement on one quantile (0.2167 SD > 0.2); HMC pair passes everything
  (vs reference 0.0380 / 3.42% / 0.1144). Neither kernel was promoted; that is the right call.
- Codex's Solar/ADU execution doc (2026-09-30): the three burden-frame report counts (21: 14/0/7,
  28: 25/3/0, 76: 49/3/24) match `runs/solar_admin_integration_20260930/burden_frames/fit_results.json`,
  and contract -> permit submission posterior median 40.66 d matches the doc's 40.7.

## What real data exposed
0. **Open (pending) cases underflow and are uncontaminated (target gap, opt-in fix; affects both
   backends).** P(T > age) is computed as 1 - cdf with no contamination. For an "open" record aged
   years (ADU: 10,046 of 37,669 open cases are over 4 years old; most are applications that died or
   changed parcel number without being closed), the model survival underflows to rounding noise, so
   each case adds about log(1e-300) = -690. This is why CPU and JAX disagreed by up to 144,475 log
   units on real Solar data (they round the tail differently), and it would have distorted the fits.
   Added opt-in `ModelConfig.pending_contamination` (same mixture as totals; needs
   `contamination_max_days` above the oldest open age). With it on, CPU and JAX agree to 9e-10 on all
   19 Solar towns (`runs/real_process_20261001/diag_jax_cpu.py`). The ADU and Solar permit fit001 runs
   (started before this was found) were stopped and rerun as fit002. The real fix is a terminal
   (abandonment) outcome, listed in the Codex handoff.
1. **Crash in the CPU likelihood at extreme town logits (bug, fixed).** `Model.combo_logw` computed
   `math.log1p(-q)` with `q = expit(lqobj)`; when a town's objection probability is unidentified its
   logit drifts past ~37, `expit` rounds to 1.0 and the sweep dies with `math domain error` (Solar
   permit probe, SMC stage 15). `grid.truncated_geometric` likewise returns NaN at `pinc = 1.0`.
   The JAX backend already used the stable log-sigmoid form. Fix: the CPU path switches to the
   same stable form only when `expit` has rounded to exactly 0 or 1, so every ordinary value is
   bit-identical. Regression test: `tests/test_toy_statute_real_data_options.py`.
2. **Exact milestone scoring cannot hold real admin dates (target gap, opt-in fix).** Milestone
   gaps are scored with no contamination and each step's support stops at `day_grid_size - 1`
   (511 days). One DG Stats record with a 512+ day completeness -> PTO gap (1,637 of 1.3M) makes the
   whole likelihood -inf at every prior draw. Added `ModelConfig.milestone_contamination`
   (default False): the gap value gets the same contamination mixture totals already have; an
   event-set mismatch stays impossible.
3. **Web pages required for every town and step (target gap, fix).** Real towns mostly have no
   published process page. The model read a missing entry as a KeyError; now an absent town or
   step is unobserved and masked, not "not listed". Synthetic worlds list every step, so their
   likelihood is unchanged (difference 0.0 on W0 and HEN3 at 8 prior points each:
   `runs/real_process_20261001/checks/web_mask_equivalence.json`).
4. **GPU path does not scale to heterogeneous towns (open).** Towns share a compiled JAX bucket
   only when every per-town evidence array has the same shape. Real towns differ (distinct
   duration counts, pending ages, reports), so 467 ADU towns are 467 buckets compiled one by one.
   Measured (`runs/real_process_20261001/bench_jax.py`): ADU (467 towns) model build + first
   likelihood had not finished after 43.5 minutes (19 GB RSS); Solar permit (19 towns, 10 buckets)
   built in 4.8 s, first call 16 s, then 12 ms per likelihood and 25 ms per gradient. The CPU blocked kernel (`blocked.py`, also
   Codex's) is what ran the real fits. Recommendation: pad arrays to a few shape classes with
   zero-weight cases (exact) before promoting the GPU path for real data.

5. **The documented GPU command could not run (bug, fixed).** `JaxPool.map` recognized driver
   operations by identity (`fn in (smc._eval_chunk, ...)`). Under the README's
   `python -m pipeline.procbench.toy_statute.smc`, the driver's functions belong to `__main__`, a
   different module object, so every JAX run stopped at once with "unsupported accelerator
   operation: _eval_chunk". Codex's validated GPU runs used its own driver (`check_acceleration.py`)
   that imports `run_smc`, so they never hit it. Fix: match by function name (JAX path only).

6. **Mode trapping on real data (open; inference, not code).** Six Solar permit fits: three CPU
   blocked runs ended in two configurations, three GPU HMC runs (three seeds) all ended in one identical
   configuration -- ~660 log-likelihood units below the best configuration a CPU run found. Each
   reproduces the totals. W0's "HMC passes between-run agreement" does not transfer: on real data the
   HMC runs agree with each other on a worse mode. See the results doc.

Also noted, not changed: synthetic-world defaults that are wrong for real data and had to be set
per package (posting window 10-150 days; Beta(1,3) correction prior; town-speed SD .3; 2%
contamination over 365 days). These are scientific settings, now declared in each package's
`prior.json` / `model_config.json`, not engine defaults.

## Certificate handling
`likelihood_compatibility.json` correctly rejected the edited `model.py` until re-certified. I
appended the new fingerprints with the equivalence record; the older entries are untouched.
