# CalFresh: uncertain actor identity without discarding the report

This is an opt-in extension of the existing V6 case-path mixture, not a new
architecture. It is implemented and computationally reviewed, but **has not
yet been applied in a real CalFresh fit**. Unknown departments already do not
block the separate timing components. This extension is for retaining several
plausible assignments when actor attribution is itself the target.

## What the likelihood does

For a case with candidate assignment `a`, declaration weight `w[a]`, and reports
`y[1], ..., y[n]`, the existing mixture now allows a case-specific prior:

`L(case) = sum_a w[a] * product_j p(y[j] | a, case, parameters)`.

The assignment is shared across all reports from that case. The prior is applied
once, outside the product; each sentence does not independently choose its own
department. When ascertainment correction is enabled, the selection normalizer
uses the same case prior. This does not by itself specify the correlation of
reporting errors from several sentences in one post.

Program input `case_path_priors[case_id][inventory_id]` accepts schema
`fixed-case-path-prior/1`. It requires positive weights for every allowed path,
a rationale, a context-bound declaration digest, and either an unknown/unlisted
alternative or an explicit exhaustive-scope explanation. V1 supports only
`basis: declared_sensitivity`: weights are not calibrated LLM confidence scores.
It requires `case_path_logit_sd=0`, adds no sampled coordinates, and does not
turn a case assignment into a population path-frequency observation.

The `actor_assignment` subtype is deliberately narrower than `process_path`.
Candidate paths must have equivalent tasks, work, fees and schedules after
erasing only the nominated actor identity. Uncertain assignments must include
an unknown actor. Operation effects must be zero and phase/dwell decompositions
disabled, so these alternatives cannot differ because of an unrelated operation
effect or changed process. Candidate construction still needs source review.

## What a posterior assignment means

Preflight reports normalized declared weights and `calibration_verified=false`.
Posterior reports include assignment means conditional on each inventory,
inventory draw counts and inventory probabilities. An inventory never visited
has no assignment estimate. Route-conditional assignment diagnostics are not
provided when the route is present in only part of the chain; those means must
not be advertised as separately convergence-checked.

Counterfactual operation durations still have independent case noises. Thus
assignment weights can move within a draw even when actor effects are zero;
that is not evidence of actor learning. Only the posterior marginal assignment
has an attribution interpretation, subject to identification and sensitivity
checks. With no distinguishing information it should not manufacture certainty.

## Checks and remaining work

The [independent review](../runs/three_family_20260920/calfresh_fixed_case_path_priors_review_v1/report.md)
found no computational blocker, with the above qualifications. Root ran
`python -m pytest tests/test_case_path_priors.py tests/test_case_paths.py tests/test_conditional_case_frames.py tests/test_marginal_conditional_frames.py -q`:
**197 tests passed**. The fixed-prior tests preserve the exact prechange default
sampler states, likelihoods, route draws and full-report hashes. The strict
single-clock conditional-frame schema still rejects this new field.

Next is a source-bound candidate/weight declaration and a joint reporting-error
contract, not another broad reread of the 945 threads. The existing nine-case
event constraints are derived bounds, not independent extra observations or a
joint fit. Neither this code nor those bounds close the
[forum-use completion requirement](2026-09-20-calfresh-forum-model-integration.md#required-closeout--do-not-lose-this-work).
