# CalFresh administrative histogram: target-preserving sampler experiment

Declared before new sampling, 2026-09-20. This is a CalFresh-first development
experiment, not a replacement of the previous frozen experiment or its failures.

## Question and fixed comparison

Can a coupled spread/location proposal resolve the documented mixing problem
without changing the evidence, likelihood, prior, sampled coordinates or reported
quantities? The proposal preserves each county's first-bin CDF, not the complete
histogram likelihood. Its Metropolis correction evaluates the full likelihood,
the complete standard-normal prior, and the determinant term. The independent
review is `runs/three_family_20260920/histogram_ridge_sampler_review_v1/report.md`.

Repeat exactly the scientific configurations and inputs of `positive46_base`
and `positive46_tighter_pool` in the original all-county plan. Keep their original
seeds, four chains, 1,000 warmup and 2,000 retained draws per chain. Add exactly
one ridge proposal per ordinary sweep with fixed log-spread step 0.05. Use two
local workers; changing worker scheduling does not change the per-chain seeds.
Use fresh output directories and cold starts, not previous failed draws.

These two conditions are selected because their shared-spread targets failed
mixing and have the positive-count source interpretation. The fixed-spread
condition cannot test a spread proposal. The stronger-assumption RZ-LITERAL
58-county variant is not part of this experiment; its prior failures and twelve
source-semantics holds remain unchanged. No condition is selected after seeing
the new results, and neither new result may replace a historical failure.

## Gates and required outputs

- Preserve the existing runner's convergence, integration and derived-quantity
  checks. Report every condition, including failure. No automatic extension,
  proposal tuning, alternate seed, or best-run selection.
- Before sampling, independently replay target equality on saved old states
  and confirm exact input/configuration bindings. The off-by-default path must
  remain the ordinary sampler. Review and focused tests establish the transition
  mathematics; they do not establish that it will mix on these inputs.
- Report elapsed time, likelihood evaluations, per-chain proposal attempts and
  acceptance, rank R-hat, bulk/tail effective sample size, and old/new diagnostics.
  Compare original equal-budget fits separately from their longer continuations.
- Replay saved new likelihoods under the ordinary target. Run existing county
  bin-probability checks and predictive analysis only with the appropriate
  numerical qualification; do not present unconverged scientific posteriors.

## Scientific limits remain

There are 46 county histograms and 59,036 recorded categorized reports, not a
random sample of all applicants. Within-county exchangeability, source reporting
and the shared lognormal spread remain assumptions. Better mixing cannot repair
inadequate bin shapes, identify sub-bin duration distributions from coarse bins,
learn forum selection/source bias, or make an administrative outcome measure
equal applicant burden. The earlier temporal comparison and its simple/LLM
baselines remain visible. This experiment does not finish CalFresh or displace
the ongoing forum-integration work.
