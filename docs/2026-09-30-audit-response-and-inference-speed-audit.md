# Audit of the response, and equivalent-target inference speedups

2026-09-30. Requested follow-up to the [original audit](2026-09-29-toy-statute-full-chain-audit.md), reviewing the [response](2026-09-30-audit-response.md) and its [round-6 recovery plan](2026-09-30-toy-statute-round6-plan.md).

**Report only. No production code, tests, evidence, saved fits, or running jobs changed.** Optimization prototypes run only inside the audit process. No new posterior fits were launched. Diagnostic code, numerical receipts and profile are in [runs/toy_response_audit_20260930](../runs/toy_response_audit_20260930/).

## Verdict

The response makes substantial, correct repairs, and its withdrawal of earlier overclaims is appropriate. It does **not** close the audit. There are both unfinished repairs and package-integration defects that affect the recovery experiment.

The most urgent findings are:

1. **The kitchen fit's default answer path crashes after sampling:** it requests hen design `S1`, absent from the kitchen menu. The remote round-6 snapshot contains the same defect.
2. **The kitchen cost/fee pipeline is inconsistent:** Stage C omits kitchen-specific work; an actual generated case pays $53 while its scored truth is $73.
3. **The newer mapped-question scorer still has the unknown-mass bug.** The hen scorer was fixed, not both scoring paths.
4. **Completion selection and FFT aliasing were repaired, but “exact for the generator” remains too strong.** False timed events, exact milestone logs, and capped hours still have mismatches.
5. **There are useful equivalent-target speedups without changing priors or discarding evidence.** Audit-only prototypes reduce a full likelihood evaluation by roughly **threefold** locally, and simplify the reading layer exactly. This is not yet a demonstrated threefold end-to-end sampling improvement.

The survey approximation is a real qualification, but **not the leading numerical problem in the saved examples**: its checked error is below 0.0015 log-likelihood units per town. It should not become another open-ended verification workstream.

## Scope and checks

- Re-read the response, recovery plan, relevant production modules, generator, and tests.
- Ran the focused suite: **39 passed in 3.88 seconds**. No broad suite or source-verification campaign.
- Recomputed all **40** posterior-score rows in `W4/stage_c001/scores_corrected_F6F7.json`; maximum disagreement is **zero**.
- Reproduced the kitchen output crash, kitchen cost discrepancy, generated-fee mismatch, mapped-scoring error, and an hours-tail counterexample.
- Compared the survey approximation with the denied-binomial/nonapplicant-Poisson mixture at three old posterior points per world, three towns each: **18** comparisons. These are not draws from the corrected outcome model.
- Profiled the current W0/W4 likelihood and tested audit-only replacements at four historical posterior points plus two prior points per world. Historical particles supply parameter locations, not a claim that their old likelihood is valid.
- Checked remote `toy_statute_r6/{model,grid,smc,estimands,readings,outcomes}.py`: all six hashes match the audited local files. At that check W4's log had reached run 0, stage 1; this audit does not certify completion or results of round 6.

The [diagnostic script](../runs/toy_response_audit_20260930/audit_checks.py) records production hashes and confirms they stayed unchanged. [checks.json](../runs/toy_response_audit_20260930/checks.json) contains numerical results and benchmark details; [profile.txt](../runs/toy_response_audit_20260930/profile.txt) contains the call profile. Hidden truth is read only for scorer/generator checks, never supplied to optimization prototypes or an estimator.

## 1. Which response claims hold?

| Response item | Audit conclusion |
|---|---|
| F1: joint denial/unpermitted-complaint likelihood | **Confirmed for these counts.** The disjoint latent-cell sum correctly replaces the overlapping independent Poissons. The accompanying survey term remains approximate, differently from its description. |
| F2: completion selection inside the duration integral; uncontaminated pending survival | **Confirmed for that repair.** The formula and tested compatible-boundary cases are correct. Other observation-mechanism mismatches remain below. |
| F3: FFT wraparound | **Fixed.** Adequate padding plus an assertion removes the original aliasing example. Tail lumping is not universally equivalent to the generator. |
| F4: fix residual mass, vary slack | A reasonable restricted sensitivity analysis, **not learning both parameters**. The exact confounding statement needs its independent-town qualification. |
| F6/F7: corrected reading scorer and Q5 marginalization | **Confirmed in `score_readings` and the 40 saved corrected W4 rows. Not propagated to `score_mapped`.** |
| F8: normalized risk preference | **Confirmed.** Risk preference uses a fraction, not raw counts. Withdrawing the broad risk-aversion rejection is correct; the chosen beta values remain sensitivity settings. |
| Random fee split on ordinary SMC outputs | **Confirmed for `smc.py`**, including per-run answers. The legacy `fit.py` entry point still uses its old default. This is not a fee-observation likelihood and does not repair package-specific fees. |
| Stage-C prior guard | Present in `run_stage_c`. It is conservative: even a continuous-prior-only JSON is rejected. The lower-level matrix API/round-5 driver do not enforce the guard; current uniform-prior runs are not thereby invalid. |
| 39 tests | Reproduced. The new normalization/FFT/selection tests do not exercise the kitchen end-to-end answer path or mapped scorer. |

The quoted W4 Bayes score **−2.128** reproduces. The saved table also reports the LLM at **−2.673** under its product-of-question-marginals convention. These remain corrected scores of the **old defective, failed-gate fit**, as the response appropriately says—not a new validated advantage.

## 2. High-priority remaining defects

### R1. Kitchen output fails after the expensive part

In [estimands.py](../pipeline/procbench/toy_statute/estimands.py), `counterfactual` always evaluates `town_estimands(..., "S1", ...)`. The kitchen package contains `K1`–`K12`, not `S1`. `answers_from_draws` calls `all_estimands`, which calls that function. Round 6 uses gate v2, so answer generation occurs before the driver writes its final diagnostics and manifest.

Reproduction on HK1b: the current 75-dimensional model evaluates a finite likelihood, but `all_estimands` raises **`KeyError: 'S1'`**. This also occurs in the checked remote snapshot. It threatens HK1b/HK2 closeout; it does not invalidate every sampled particle. Per-run particle files are written before this failure, so a postprocessing repair need not automatically imply repeating sampling.

**Recommendation:** make the intervention an explicit package setting, or omit the unsupported counterfactual with a declared unavailable result. Do not silently assume that kitchen `K1` is the legal intervention equivalent of hen `S1`. Smoke-test one draw through the package's actual answer/scoring path before a costly fit. Separately, write immutable configuration/code provenance at launch, not only after all postprocessing succeeds.

### R2. Kitchen costs and generated fees disagree

`readings.burden_indices` is still a hard-coded hen formula. It ignores kitchen `product_lab_test` and `zoning_clearance` elapsed time, `food_safety_course` and lab effort, and additional fee items. The newer `town_estimands` roll-up uses the package catalog. This is not merely an arbitrary weight choice: two implementations of the same declared burden disagree.

At an ordinary prior-center parameter point, with the **same fee table** in both calculations:

| Kitchen design | Package-aware burden | Stage-C burden | Omitted burden |
|---|---:|---:|---:|
| K1 | 59.438 | 50.373 | 9.065 |
| K2 | 76.086 | 67.021 | 9.065 |
| K12 | 107.900 | 74.604 | 33.296 |

Units are the declared day-equivalent index, not observed days. The unequal omissions alter choice probabilities, not just a common offset. These are diagnostic parameter points, not posterior estimates.

There is also a generator/scorer discrepancy. HK1b's Amber/K6 has fees `application=53, course=20`. `simulate_case` reports **$53**, while `town_estimands` computes **$73**. `generate.make_webpage`, `simulate_case`, and `Model.fee_table` still special-case application/notice/inspection. The truth builder and package-aware estimands can carry additional items that these paths omit.

**Recommendation:** use one catalog-driven fee/cost definition across generation, observation, fitting and scoring; keep uncertain fee allocation separate. Reconcile the affected existing world's evidence and scoring policy explicitly—do not silently rewrite historical data. This is distinct from the already acknowledged missing fee-reading likelihood edge (HEN2 Q5 / kitchen fee question).

### R3. The mapped scorer still turns unknown mass into “No”

`readings.score_mapped` still sums unnormalized known-reading probabilities and indexes the unnormalized true reading. It neither separates residual mass nor exposes the hen scorer's exclusion argument. `run_stage_c_round5.py` calls it for kitchen reader and oracle comparisons.

Minimal example: `[P(yes)=0.5, P(no)=0, P(unknown)=0.5]`, truth yes. The current mapped scorer returns **Brier 0.25 and log score −0.693**. Under the response's declared known-reading convention, both scores should be **zero**, with residual mass 0.5 reported separately.

**Recommendation:** share the corrected scoring implementation across question sets, retain an explicit residual-mass diagnostic, and explicitly marginalize excluded questions. A conditional-known score alone must not reward moving all uncertainty into the residual category. Also label hen `map_accuracy` correctly: it still evaluates the full known reading even when the joint log score excludes Q5.

This does not prove every recorded kitchen LLM number is wrong: an LLM vector with zero residual is unaffected by this particular defect. The risk is the Bayesian/LLM comparison using different residual semantics.

## 3. What remains of likelihood exactness

### R4. F2 fixes selection, not the entire report-generation mechanism

For compatible reported boundaries, the new kernel correctly implements

\[
\sum_{d_1,\ldots,d_G} \left\{\prod_g p(d_g\mid S,\theta)
[(1-c)p(y_g\mid d_g)+c\,p_{ref}(y_g)]\right\}
P(C\geq\textstyle\sum_g d_g).
\]

But `q[~ok, 0] = c0 * ref` in `_completed_gap_loglik` gives positive probability to a **timed event that does not exist on the candidate path**, treating its true duration as zero. In the generator, numeric contamination changes the reported gap value, not the event names; only genuinely occurring events can be timed. There are two W0 and 49 W4 completed reports with at least one such incompatible candidate path. These are not 51 bad documents—the issue is their likelihood under alternative paths. A W0 example receives log likelihood −16.324 where that event sequence is impossible under the generator.

The generator's choice of which mentioned events to time is also not explicitly represented. Conditioning it away needs justification because available events depend on the path. Similarly, W0m milestone records are generated as exact logs, whereas `town_struct_loglik` still applies contamination to each milestone gap and assigns a contamination likelihood to an impossible milestone set.

**Recommendation:** either implement the declared observation process, or explicitly declare a robust working model in which event labels/status logs can be wrong and evaluate it as such. Do not describe the remaining differences as numerical error or assume they cannot change design recovery. The published posting window itself is now supplied to the model and described to the baseline; that portion of the repair holds.

### R5. F3 removes aliasing but does not make capped totals generative truth

The revised convolution computes a sum capped at index 511. This is a valid distribution and is much better than circular wraparound. It is appropriate for a **declared top-coded observation**, or for probabilities below a cap when all tail mass is retained.

The generator, however, truncates/resamples **individual steps** and then sums them without capping the total. In particular, it adds hour indices and applies reporting noise to their full sum. The fitter instead applies report noise to a total capped at **127.75 hours**. Two legitimate 100-hour steps therefore produce a 200-hour true total but a 127.75-hour model total. A report of 200 hours at report sigma 0.3 has probability 0.003325 under the former versus 0.001089 under the latter: a **−1.116** log-likelihood difference.

For elapsed totals, the admin likelihood explicitly coarsens observed values at 511, which can be a deliberate information reduction. Completed forum totals cannot exceed the current 150-day posting window, so that particular tail issue does not affect their compatible-boundary kernel. Predictive elapsed means/quantiles are still capped, while generated/held-out totals are not. Expected per-step days can consequently fail to add to the reported capped total mean.

**Recommendation:** separate computational prefix truncation from an observational top code. Retain full support where the observation/estimand needs it, or report bounded approximation error. The hours example establishes a support defect; its posterior-wide impact is not measured here and should not be presumed large in every current world.

### R6. The survey approximation is different from its description, but small in the spot-check

The repaired overlapping-count sum is correct. Given denied-complaint allocations \(a,b\), however, the number of denied, quiet keepers is

\[
Q\mid a,b,D\sim\operatorname{Binomial}(D-a-b,\phi),
\quad R\sim\operatorname{Poisson}(\lambda_{nq}).
\]

The correct survey contribution averages the binomial survey likelihood over **both** this conditional distribution and the posterior weights on \(a,b\). The code calls `survey_loglik` with

\[
\lambda_{nq} + (D-E[a]-E[b])\phi.
\]

That is a **Poisson approximation to the whole hidden count**, not substitution of the denied count by a fixed conditional expectation. It changes variance, and the response's \(D/4\) bound concerns conditional binomial variance, not all allocation uncertainty.

Across 18 checks using old W0o/W0o_adv posterior locations, the largest absolute survey log-likelihood difference was **0.001492** per town; the adversarial-world maximum was **0.000239**. Thus this audit does not support treating the survey approximation as the immediate bottleneck in those examples. A higher-sampling-fraction counterexample shows differences of roughly 0.32–2.25 log units, so it is not universally harmless.

**Recommendation:** accurately name the approximation and its demonstrated regime. Retain the exact mixture as a small reference calculation; use it if the evidence regime changes. Existing survey quadrature tests compare two implementations of a Poisson hidden-count model, so they do not test this conditional-binomial approximation.

### Qualifications to the response's statistical claims

- **Residual/slack confounding is exact for independent town readings.** With finite Dirichlet concentration, equal \(\eta=\rho+(1-\rho)\epsilon\) need not imply equal cross-town dependence. For a two-design example, the design probability's variance contains \((1-\epsilon)^2\rho(1-\rho)/(4(\kappa+1))\), not eta alone. Holding rho fixed remains reasonable; the unrestricted “only eta observable” statement needs qualification.
- **Paired statutes do not automatically identify per-agency temperature.** Two design choices per agency, uncertain interpretation, and an arbitrary utility scale are weak information for a separate tau per agency. Hierarchical learning may help; it is not established by launching linked worlds.
- **The old design-recovery conclusions cannot yet be declared unaffected.** Completion selection changes path/design likelihoods. The response correctly suspends old interval claims, but the broader “unaffected in kind” language should remain a hypothesis until recovery finishes.
- **SMC diagnostics remain as previously implemented.** Acknowledging that particle-array R-hat is not an MCMC certificate has not removed it from the active gate. No amount of passing that gate proves identification or repairs a misspecified likelihood.

## 4. Equivalent-target speedups

“Equivalent” has three meanings that must not be mixed:

1. Same deterministic likelihood/posterior summaries, up to floating-point error.
2. Same posterior target, with a different Monte Carlo algorithm or estimator.
3. A smaller/approximate model that may predict similarly.

The first two are appropriate here. Shrinking priors, removing rare designs, replacing sums by MAP choices, and reducing particles without measuring Monte Carlo error belong to neither exact-equivalence claim.

### Measured: simplify completed-report integrations

Most completed reports have one gap: W0 has 30 one-gap, one two-gap, one three-gap; W4 has 93, 45 and four respectively. The current implementation nevertheless FFTs each report across all candidate paths.

- One gap needs only a dot product with the posting-survival vector.
- For two gaps, define \(F_2(j)=\sum_{b\leq j}q_2(b)\) and \(A_2(j)=\sum_{i\leq j}F_2(i)\), zero for negative indices. Uniform posting on \([a_0,b_0]\) gives

\[
P(y,complete)=\frac{1}{b_0-a_0+1}\sum_x q_1(x)
[A_2(b_0-x)-A_2(a_0-1-x)].
\]

- More gaps: convolve all but the last, then apply that prefix-sum identity. Truncate only coefficients that cannot finish by the posting horizon; do not renormalize them.

The audit prototype also reuses repeated report-value/unit kernels within a town. On the tested W0/W4 points the maximum complete-log-likelihood difference was below **1e-12**; local full-likelihood time improved about **1.2–1.3×** with this change alone. This preserves even the current incompatible-boundary convention; it is an optimization, not a hidden scientific repair.

### Measured: reuse short, capped convolutions

The profile places roughly half the W0/W4 evaluation time in `conv_from_counts`, in addition to substantial completed-report FFT work. Every proposal recomputes many related segment distributions using 8,192-point FFTs and complex log/exponentiation.

For the **current capped-sum target**, nonnegative addition satisfies

\[
\min(\min(X,c)+Y,c)=\min(X+Y,c).
\]

Therefore related segment-count vectors can share cached prefixes, building each additional step using a sufficiently padded **1,024-point pairwise convolution** and retaining overflow in the cap. This does **not** mean shortening the existing many-factor FFT to 1,024: that would reintroduce aliasing. The safe construction uses pairwise addition and the identity above. Correct zero-padding for linear convolution is also described in the [SciPy FFT documentation](https://docs.scipy.org/doc/scipy/tutorial/fft.html).

Combined with the completed-report change, the local benchmark is approximately:

| Full likelihood | Current | Audit-only prototype | Speedup |
|---|---:|---:|---:|
| W0, 3 towns / 36 coordinates | 40.1 ms | 14.3 ms | 2.80× |
| W4, 12 towns / 63 coordinates | 315.7 ms | 99.4 ms | 3.18× |

Exact timing samples live in `checks.json`; wall times fluctuate. Across the 12 checked parameter points the largest absolute log-likelihood difference was **2.96e-12**. This is a useful prototype, not a production-certified replacement: extreme tails and packages beyond the checked worlds still need a bounded numerical comparison. If R5 is repaired by retaining uncapped hours, use the appropriate uncapped support for that channel; the capped identity must not silently define the scientific model.

These are CPU microbenchmarks with BLAS threads set to one, not a remote fit ETA. At the measured W4 cost, 10,000 particles × 30 moves means **300,000 likelihood evaluations per ordinary tempering stage**. That is about 26 CPU-hours per stage before parallelization, and there are multiple stages and two runs. Much of the runtime is repeated arithmetic, not an unavoidable requirement of Bayesian inference.

### Measured: contract Stage-C arrays in a better order

Current code computes

```python
einsum("nk,nktr,ntrd->td", weight, reading_given_nk, design_given_nr)
```

First summing out `k` removes a large repeated dimension:

```python
nr = einsum("nk,nktr->ntr", weight, reading_given_nk)
town_design = einsum("ntr,ntrd->td", nr, design_given_nr)
```

This is the same finite weighted sum. For 200 saved W4 particles, 12 towns, 33 readings and 50 population-weight draws, paired local measurements show about **1.5×** faster Stage-C evaluation. All outputs except roundoff in `town_design` are identical; its maximum difference is **6.53e-14**. Chunking particles/population draws also bounds memory without changing the target. Do not multiply this speedup by the likelihood speedup: they concern different stages.

### Exact reduction: combine observationally equivalent readings

If two reading rows give the same choice distribution for every relevant particle/town, all downstream likelihoods see only their combined probability. Sum their prior masses, infer the class, and reconstruct reading probabilities within it. In the tested W4 uniform-choice setting, **33 entries including residual reduce to five distinct choice rows**. Reconstructed reading/design posteriors agree within **2e-14**.

For finite kappa, Dirichlet aggregation gives class parameters
\(\alpha_g=\sum_{r\in g}\alpha_r\). Conditional allocations within a class remain unlearned and can be integrated analytically. Use the actual effective alpha values, including any implementation floors. This preserves the posterior target, though replacing full-vector random Dirichlet draws with grouped draws changes finite Monte Carlo realizations.

Group **choice rows**, not arbitrary textual readings. Keep the risk preference's original reading measure fixed when grouping; recomputing an unweighted risk fraction over the collapsed classes would change the model. A new fee-reading likelihood can distinguish previously identical classes, so the grouping must be rebuilt when that edge is added.

For few classes/towns, there is a further exact alternative to the 50 weight draws: expand
\(\prod_t\sum_g w_g\ell_{tg}\) by dynamic programming and integrate each monomial with the Dirichlet moment formula. For five classes and 12 towns there are only \({16\choose4}=1820\) degree-12 count states. Whether this beats grouped Monte Carlo in time needs benchmarking; it would remove that integration noise, not the outer particle error.

### Other same-target improvements, not benchmarked here

1. **Cache by parameter dependency.** Hour laws do not depend on town speed. Reuse hour convolutions and reporting kernels across towns at a fixed theta; compile report groupings, structural masks and segment plans once. Cache final per-particle town/design likelihoods for Stage C and answer generation, rather than reevaluating every town repeatedly. Cache keys must include data/model hashes.
2. **Use block-local Metropolis moves.** Loop/hearing probabilities change mixture weights, not convolutions; mention/listing parameters change detection factors, not durations. Their proposals should not recompute every FFT. Town-specific moves need only affected towns, except that the centered-speed parameterization couples raw town coordinates; use contrasts or paired speed moves. This is a different kernel with the same target, requiring an efficiency comparison, not identical random draws.
3. **Integrate out the unused common town-speed direction.** Under the default independent equal-variance Normal priors, the centered likelihood ignores the common mean; orthonormal contrasts preserve the induced prior exactly. This saves one coordinate, not an order of magnitude. Do not simply fix a coordinate while changing the remaining prior covariance.
4. **Rao–Blackwellize output calculations.** Average/enumerate design probabilities instead of drawing a design unnecessarily. For credible intervals of a design-dependent estimand, use its weighted mixture distribution—not a quantile of conditional means. Nonlinear cross-town entropy still needs a suitable joint calculation. Reusing distributions also makes the current 1,000-draw answer gate less noisy.
5. **Consider better SMC moves after arithmetic improvements.** Blocked proposals, gradient-informed moves, or waste-free SMC can improve effective information per CPU-hour while keeping the posterior target. They do not make a fixed particle count universally equivalent. See the [SMC review](https://arxiv.org/abs/2007.11936), [HMC-within-SMC paper](https://arxiv.org/abs/1808.07730), and the authors' [waste-free SMC implementation tutorial](https://particles-sequential-monte-carlo-in-python.readthedocs.io/en/latest/notebooks/SMC_samplers_tutorial.html). No such sampler change was tested here.

The round-6 launcher already limits BLAS threads. Turning that setting on again is not a new speedup. More workers or a GPU rewrite should follow measurements of the new kernel; neither fixes unnecessary work or incorrect targets.

## 5. Recommended next actions

In order, as a bounded follow-up rather than another broad redesign:

1. **Fix closeout and scoring first:** package-specific counterfactual handling, mapped scoring, and one-draw package smoke tests. Preserve completed particles and historical artifacts. Do not label every active run unusable merely because postprocessing is broken.
2. **Resolve the kitchen burden/fee inconsistency and declare the remaining observation model.** Separate corrections that change the target from code changes that only compute it faster. Those two categories have different refitting requirements.
3. **Implement the measured arithmetic optimizations behind one reference comparison:** completed-gap sums, cached pairwise convolutions with correct support, and Stage-C contraction. Keep priors, likelihood semantics, evidence, support and sampling budget fixed during the equivalence check.
4. **Collapse equivalent readings and reuse likelihood caches.** This addresses Stage-C memory/integration cost without pretending to learn distinctions the evidence cannot see.
5. **Only then compare sampler efficiency:** predeclare a small fixed suite, report output Monte Carlo error per CPU-hour plus log-normalizer stability, and compare intervals/design probabilities—not just particle-array R-hat or a matching MAP design. No need for a broad new verification campaign.

Changing a correct evaluation order does not require changing priors, calibrating new hyperparameters, or simplifying the scientific model. Changing an incorrect observation likelihood does require an explicitly new target. Keeping those two tracks separate is the quickest route to results that are both faster and defensible.
