# CalFresh joint47: same-target computational repair

Status: computational protocol, not launch authorization. Written after the
equal-path and 90%-standard-path conditions failed convergence, while the third
original condition is running. No original joint47 draws have been used to
choose a new prior, observation, or scientific sensitivity.

## Question and invariant

Can better transitions explore the **same** joint posterior at the same draw
budget? This is a numerical experiment, not evidence that the model fits the
sources well, corrects forum selection, identifies an agency effect, or beats
an LLM. Numerical improvement cannot substitute for those subsequent checks.

Keep the source-selected 47 histories, 61 facets, shared-report dependence,
optional interview paths, observation bounds, prior scales, contamination,
population integration and source-derived initial states unchanged. Preserve
all original failures and all three fixed path-prior sensitivities in order:

1. Standard/direct weights 50/50; seed 2026092601.
2. Standard/direct weights 90/10; seed 2026092602.
3. Standard/direct weights 10/90; seed 2026092603.

For each, retain four chains, 1,000 warmup and 2,000 retained draws per chain,
two workers, and the original 4,096-point prediction grid with its 16,384-point
refinement. No posterior state is recycled as a prior or source-derived initial
condition. The same initial states do not guarantee cross-mode exploration;
that limitation remains in both computations.

## Only proposed changes

- Set `hierarchy_sampler=operation_centered` under a guard on the **actual**
  operation-mean covariance. The three distinct positive-scale task effects
  make this particular covariance full rank even when `operation_sd=0`.
  Do not add an operation prior, numerical jitter, or a pseudoinverse to pass it.
- Set the new default-off `case_scale_sampler=interwoven`. Hold realized
  operation effects fixed while jointly updating case spread and its residuals.
  The one-dimensional elliptical-slice callback includes the residual Gaussian
  prior ratio and transformation Jacobian; the spread's standard-normal prior
  is supplied by the slice sampler. Recompute the complete ordinary likelihood
  on acceptance, including any population or selection terms.
- Keep exact case-local likelihood evaluation enabled, with full-likelihood
  refreshes before nonlocal moves. This is computational reuse, not a likelihood
  approximation or independent treatment of dependent facets.

The parameter layout, scientific likelihood and priors must agree with the
original at matched states. An independent fixed-effect conditional test of
the scale move is in
[root_conditional_stationarity_check.py](../../runs/three_family_20260920/calfresh_case_scale_interweave_prototype_v1/root_conditional_stationarity_check.py).
Its 4,000 one-step probes passed against a numerical reference with a
spread-dependent likelihood. This checks a transition; it does not establish
better mixing on the real cases.

## Execution and comparison

Complete the original three conditions and their frozen base/mixture analyses
before adopting any live patch. Then review the integrated sampler and run the
regressions. Use the existing general V6 runner with explicit source-derived
initialization and local-update options, not another copied experimental sampler.
A fresh plan must bind all input, initial-state, configuration and source hashes;
root must inspect and authorize that exact plan before any new fit starts.

Use fresh outputs and report every condition, not whichever sensitivity mixes
best. Retain the original gates: all nonfixed reported diagnostics finite,
R-hat at most 1.01, bulk ESS at least 400, tail ESS at least 200, and both
integration-precision checks passing. Do not remove an unmeasured coordinate
from this computational comparison merely to make its gate pass.

Compare wall time, likelihood-call counts, log-likelihood and spread diagnostics,
operation-location diagnostics and case-path diagnostics. Failed posterior
summaries are diagnostic only; they are not reliable numerical reference truth.
Report all case-level mixture intervals using posterior path weights, not a
single selected path or averaged path quantiles. No automatic continuation,
extra draws, relaxed gate, or preferred scientific condition is authorized here.

These computations do not close other supported uses from the same source
histories. Forum evidence use remains a CalFresh completion requirement under
the [current integration work order](../2026-09-20-calfresh-forum-model-integration.md).
