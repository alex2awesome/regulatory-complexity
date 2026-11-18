# Closing the response-audit gaps

2026-09-30. Implementation authorized by Alex after the [response/speed audit](2026-09-30-audit-response-and-inference-speed-audit.md).

## Scope and completion rule

Deliverable: bounded repairs to the toy-statute production modules, regression tests for R1–R6, and a numerical reference comparison for computation-only optimizations. Budget: one implementation pass and focused toy-model checks; no new evidence review or long posterior fits. Completion does **not** mean new posterior recovery has been demonstrated.

Production code means the modules imported by fitting jobs in `pipeline/procbench/toy_statute/`. The previous audit's prototypes were temporary in-memory substitutions in a diagnostic script; fitting jobs never used them. This task integrates supported changes into those modules.

## Assumptions and boundaries

- Preserve the already-landed R1 counterfactual guard and R3 mapped-score repair; those are another contributor's changes.
- Preserve historical evidence, scores, particles and running remote snapshots. Observation-model repairs define a new target and require new fits; output/scoring-only repairs do not by themselves require resampling.
- No kitchen-to-hen intervention equivalence is invented. An unspecified kitchen counterfactual stays unavailable.
- Fee amounts remain the declared plug-in/residual-allocation rule, not a newly learned fee observation model. This task fixes catalog consistency, not that missing statistical edge.
- Only public observation settings may enter the fitter. Any fallback for old evidence must be identified in output metadata.

The pre-edit Python modules are preserved in `runs/toy_response_repairs_20260930/source_before/` (including the R1/R3 changes already present at task start).

## Result

R1–R6 now have executable repairs in the local production modules. **This closes the enumerated implementation defects, not the recovery experiment.** No existing world, score, posterior file or remote running snapshot was modified; no long fit or paid-model call was launched. The new process target is `toy-process-v2-20260930`.

| Finding | Implemented repair | Consequence for old results |
|---|---|---|
| R1: kitchen closeout crashes on S1 | Preserve the package counterfactual guard; explicitly mark unavailable interventions in answer metadata. Run one prior draw through actual answer generation before SMC. Write launch provenance and a source snapshot before sampling. | The guard alone can repair old closeout using the corresponding old target. It does not make old particles valid under R4/R5. |
| R2: missing kitchen work/fees | Shared catalog execution counts and fee items now drive Stage-C burden, estimands, generated cases, web schedules and inferred fee tables. Kitchen course/lab/zoning work is included. | Old kitchen corpora retain their old fee-generation defect. Use a new versioned corpus before asserting fee recovery. Generation refuses to overwrite an existing world. |
| R3: unknown scored as No | Both scorers use one implementation. Conditional-known and unconditional joint scores are separate; residual mass is explicit. All-unknown rows have unavailable conditional scores, not fake No answers. Excluded questions are marginalized for joint MAP as well as joint log score. | Rescore into new outputs; no sampling needed solely for this change. Historical scores are untouched. |
| R4: impossible events and missing mask likelihood | Absent timed boundaries have zero probability. Include the generator's timing-mask selection conditional on mentions. Exact administrative milestones have no numerical contamination. | Changes design/path likelihoods; new fits required. |
| R5: capped hours/totals | Individual-step truncation is retained, but sums have full support. Hour reporting noise acts on the full sum. Administrative totals are not clipped. Completed/pending calculations use unnormalized prefixes only where sufficient. Predictive and extended elapsed summaries use full support. | New process fits and new summaries/scoring needed. |
| R6: Poisson approximation to denied quiet keepers | Integrate the conditional denied-binomial/nonapplicant-Poisson mixture, including uncertainty in overlapping-count allocation. Poisson truncation is checked against a relative likelihood-error bound of `1e-10`; otherwise use the full contributing support. | Outcome fits must be rerun. This is a corrected target, not an equivalent speedup. |

The fee regression now produces **$73, not $53**, for a case with a $53 application and $20 required course. This is a new test-generated case; it is **not** a claim that the inherited HK1b documents were rewritten.

Launch/closeout provenance is implemented in the active SMC entry point. Stage-C and outcome-cut entry points reject manifests from the old process target instead of silently reusing incompatible draws. The lower-level array API cannot establish the provenance of caller-supplied arrays. Historical driver scripts must use their source snapshots or be migrated explicitly.

## Mathematical changes versus computation-only changes

The process likelihood still enumerates candidate designs, correction counts and hearing occurrence, and integrates durations on their declared discrete grids. SMC still samples continuous parameters using the existing tempering/resampling/Metropolis scheme. Priors, particle budgets and proposal kernels were not weakened or reduced to obtain a speed gain.

**Changed target:** the timing-mask law is

\[
P(B\mid A)=\begin{cases}
p_0+(1-p_0)(1-p_t)^{|A|},&B=\varnothing,\\
(1-p_0)p_t^{|B|}(1-p_t)^{|A|-|B|},&\varnothing\ne B\subseteq A,\\
0,&B\not\subseteq A.
\end{cases}
\]

Here A is the set of truly occurring, mentioned, timeable events and B the observed timed subset. Numerical contamination can alter a reported gap value, not create an event. Completion selection remains inside the duration integral.

For the survey, condition on the observed overlapping counts, then integrate `Q | rest ~ Binomial(rest, phi)` and independent `R ~ Poisson(lambda_nonapplicant)`. The former implementation substituted `Poisson(E[Q] + lambda_nonapplicant)` for their sum; the new one retains the allocation and binomial variance.

**Same target, less computation:**

- Cache shared step-count convolution prefixes. For nonnegative durations, discarded coefficients above a required observation horizon cannot return below it. Do not renormalize prefixes or move their missing mass into a final bin.
- One completed gap is a dot product. For multiple gaps, integrate the last gap using two cumulative sums and the uniform posting window; retain a separate positive-convolution reference.
- Contract Stage-C arrays over population-weight draws first.
- Combine identical shared choice rows, then reconstruct individual reading probabilities. For finite kappa use summed **effective Dirichlet alpha**, including existing floors. Within-class allocation remains at its prior. This changes finite Monte Carlo realizations but not the target. Particle-dependent cost rows are not automatically grouped.

An initial FFT/reference check failed on an exact-milestone fixture by about 0.001 log-likelihood units: tiny Fourier coefficients were contaminated by cancellation. Production therefore uses cached **positive pairwise convolution**, not the audit's FFT prototype verbatim. A direct positive reference independently checks the result. The legacy capped convolution remains available for historical diagnostics, but the active model/estimands no longer call it.

## Bounded verification and timings

Command:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest tests/test_toy_statute.py tests/test_toy_statute_response_repairs.py -q
```

**66 tests pass.** The new regressions cover full-support convolution, the 200-hour counterexample, additive elapsed means, catalog fees/burden, the actual kitchen answer path, impossible timed events, normalized timing-mask probabilities, exact milestones, shared scoring semantics, grouped readings, conditional survey sums, target-version rejection, launch preflight, and no-overwrite generation. No repo-wide verification campaign was run.

Independent arithmetic comparison: **24 parameter points across W0, W0m, W4, HK1b, HEN2 and HK2**, including historical parameter locations and prior draws. Maximum optimized-minus-reference log-likelihood difference: **4.55e-13**. All six one-draw answer paths complete with finite estimands. Historical parameter locations are numerical test inputs, not valid draws from the new posterior.

Paired local single-thread timings versus the preserved pre-edit implementation:

| World | Pre-edit likelihood (ms) | Corrected optimized likelihood (ms) | Runtime ratio |
|---|---:|---:|---:|
| W0 | 53.34 | 20.32 | 2.63× |
| W0m | 45.93 | 18.00 | 2.55× |
| W4 | 338.41 | 99.05 | 3.42× |
| HK1b | 366.55 | 138.66 | 2.64× |
| HEN2 | 378.30 | 123.28 | 3.07× |
| HK2 | 329.81 | 126.30 | 2.61× |

These old/new timings compare **different targets** because defects were repaired. Equivalence is established separately against the corrected direct reference; that reference is deliberately simple and is not the historical performance baseline. There is no measured end-to-end fit speedup or convergence claim yet.

On the independent-town Stage-C numerical fixture, 33 reading entries reduce to 5 choice classes, with maximum output difference below `4e-15` and about **4.3×** faster evaluation. Do not multiply this by the likelihood speedup: they concern different stages.

Receipts: [tests.log](../runs/toy_response_repairs_20260930/tests.log), [checks.json](../runs/toy_response_repairs_20260930/checks.json), [runtime_vs_pre_edit.json](../runs/toy_response_repairs_20260930/runtime_vs_pre_edit.json). Reproduction scripts and pre-edit source are in the same directory. The post-hoc `extended.py` compatibility repair and baseline/public-settings safeguards followed the main arithmetic benchmark and are covered by the final tests.

## Fixed settings and remaining scientific gaps

The observation design's timing-selection probabilities are now published with newly generated evidence. Old evidence without those fields uses an **explicit assumption** `p_total_only=0.2`, `p_time_mentioned_event=0.7`, disclosed in answers and manifests. The fitter does not consult generator truth to obtain them. Future LLM prompts receive the same observation settings/legacy assumptions. These are appropriate fixed experimental settings for the current synthetic design, not learned or transportable descriptions of real forum behavior.

The following are still limitations, not repaired by faster arithmetic:

- Fee amounts/allocation remain a plug-in/residual rule; no generative fee-reading likelihood has been added. Old kitchen evidence must be regenerated under a new version before a fee-recovery claim.
- Residual mass, choice slack, choice temperature, contamination and utility weights remain declared settings/sensitivity choices. This task does not establish that the data identify them. Rho/slack equivalence is exact for independent town readings, not generally for finite-kappa dependence.
- The existing SMC gate's particle-array R-hat is not an MCMC convergence certificate. No gate was relaxed, and no new gate-pass result is claimed.
- Grouping readings preserves unknown distinctions; it does not learn distinctions that share a choice law. The missing fee edge could split these classes later.
- The older extended concurrency intervention is explicitly hen-specific; unsupported kitchen concurrency now raises a clear error rather than omitting extra work silently.

## Handoff / next run

1. Coordinate with the owner of the active `toy_statute_r6` jobs before any stop/relaunch. This task did not modify or stop that snapshot. Old particles can still support historical-target analysis, but cannot be relabeled as v2.
2. For W0/W0m/W4 timing recovery, use a fresh fit directory and the v2 source snapshot. Record the public observation settings or the disclosed legacy assumptions. Preserve old baselines; rerun the baseline if its information/prompt changes.
3. For kitchen fee/cost recovery, create new versioned HK evidence using the corrected generator, then fit and score that version. Do not mutate the inherited evidence to make it agree after the fact.
4. Run Stage C and outcome cuts only on target-compatible process particles. Compare held-out predictions, interval recovery and Monte Carlo stability under the predeclared budget. The implementation checks here are not a substitute for those results.
