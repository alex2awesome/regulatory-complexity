# Solar and ADU process refit — 2026-10-02

Status: **all four fits completed; both domains fail independent-run agreement**.
The numerical failures are repaired, but neither full posterior is accepted.

## Scope and stopping rule

User request: try fitting the Bayesian model to Solar and ADU following the
[real-data audit](2026-10-01-real-data-model-and-inference-audit.md).

Deliverable: fresh fits using the repaired process engine, independent-run and
analytic-prior diagnostics, and a result table distinguishing usable timing
summaries from unsupported structural/capability conclusions. No new acquisition,
synthetic work, raw-document reverification, or baseline-superiority claim.

Start with Los Angeles city, Los Angeles County, San Diego, San Francisco and
Sacramento: the five jurisdictions with direct permit-system records in the
inherited packages. The choice is based on source availability, not fitted results.
This is not the 467-jurisdiction ADU analysis. Other towns remain in the original
inputs; no raw source or historical result was changed.

| Domain | Completed administrative records | Administrative open cases | Forum reports | Sampled coordinates |
|---|---:|---:|---:|---:|
| Solar application → permit | 100,689 | 6,003 | 15 (12 completed, 3 pending) | 37 |
| ADU application → permit | 67,102 | 4,548 | 3 (all pending) | 37 |

The Solar subset contains all administrative completed records of the prior
19-town package; the other 14 towns were forum-only. The ADU subset contains
56.4% of the prior package's completed administrative records. It has very little
forum evidence and must not be described as the whole parsed forum corpus.

Four attempts, seeds 20261002 and 20262002 per domain, each with 512 particles,
8 blocked mutation sweeps per stage (16 at the final stage), 32 CPU workers,
and a **90-minute wall limit including closeout**. Failed or timed-out attempts
remain recorded; no automatic extension or best-likelihood seed selection.
GPUs were occupied at the resource check, so none was allocated by this task.

## Repairs used by these fits

- The rounded, truncated lognormal PMF is evaluated using log-CDF differences
  and log normalization. Extremely far-above-grid distributions no longer become
  all-zero PMFs.
- Pending survival uses a reverse cumulative sum over full support, not `1-CDF`.
- The conditioned geometric law has a finite uniform limit at tilt 1 in both
  likelihood and prediction code. Its interpretation remains a geometric tilt,
  not an observed per-review correction probability.
- Native forum interval endpoints reach the report kernel directly. No midpoint
  re-encoding into synthetic day/week/month bins.
- These runs turn off the synthetic timestamp-mask likelihood and synthetic
  uniform-posting selection. **Unselected reporting is a declared sensitivity
  assumption, not a learned account of forum selection.**
- Independent, unobserved labor and web-report parameters are refreshed from
  their exact priors after every SMC mutation stage. This preserves the target
  and does not claim those parameters have been learned.
- Continuous Beta prior draws are no longer clipped into artificial point masses.
- Sampling metadata and the launch manifest are saved before expensive answer
  generation. One-run summaries report agreement as unassessed, not an artificial
  passing diagnostic.

Fresh target epoch: `toy-process-v3-20261002`. The old source-fingerprint registry
is preserved, but old v2 particles are not certified compatible. CPU and JAX
numerical paths both contain the PMF/survival repair; the current fits use CPU.

The local focused suite exercised 130 tests: 129 passed in the last full pass;
the only failure was a mistyped source fingerprint, corrected and its test rerun
successfully. One optional JAX module was skipped locally. The added extreme-PMF
CPU/JAX and finite-gradient test passed separately on sk3 using CPU JAX (no GPU).
A second optional test passed for native intervals, disabled synthetic reporting
selection/masks, and contaminated full-support survival together, including gradients.
These are regression checks, not posterior certification.

Replay of the actual archived ADU failure: **256/256** formerly zero-mass
correction PMFs are finite and normalized, maximum mass error **8.11e-14**.
Their corrected conditional means are 508.8–510.1 days, near the stated grid
boundary, rather than nonexistent zero-mass distributions. This repairs the
numerical evaluation; it does not rehabilitate the old posterior or establish
that the support choice is appropriate. Receipt:
`runs/real_process_refit_20261002/saved_failure_replay.json`.

## Remaining scientific limitations

The inherited process menus and structural web readings are retained. The model
averages over those menus; it does not discover arbitrary processes. In particular,
the San Francisco ADU hearing reading inherits the earlier coarse HCD category
mapping; it is not newly adjudicated here.

Issued-only source and observation-window selection, terminal outcomes, source
bias, era changes and case mix remain incomplete. Open-case contamination is not
an abandonment model. No fee schedules or hour measurements are present. Generic
answer files may carry conditional/prior-derived hour and zero-fee computations;
these are excluded from measured-burden headlines. Relative town multipliers are
not intrinsic agency capability.

With no completed ADU forum reports, the ordinary report-noise and mention
parameters are also prior-only controls. The current refresh option targets
labor/web parameters; the independent diagnostics will additionally check those
unrefreshed report parameters rather than assume they mixed.

## Acceptance and analysis

1. Require successful beta=1 completion and finite normalized step distributions.
2. Compare every analytically prior-only marginal against its actual prior.
   Flag mean shifts over 0.25 prior SD or SD ratios outside [0.75,1.25] as a
   deliberately loose analytic-control screen for these 512-particle attempts;
   this does not replace the unchanged independent-ensemble gate.
3. Compare independent ensembles with the existing parameter gate; retain its
   limitations for resampled SMC particles. Do not interpret agreement as proof
   of global mode coverage.
4. Report each seed's design probabilities, expected executed-step count,
   correction-count distribution and actual discrete timing distributions.
   Never average two trapped modes 50/50 and call that inferred uncertainty.
5. Compare posterior predictions with observed administrative totals as an
   in-sample check, not as held-out validation or an LLM comparison.

Each run uses 128 answer draws for bounded closeout. We are **not** applying the
1,000-answer-draw estimand Monte Carlo gate to that smaller sample. The paired
parameter diagnostic uses all retained particles. Unvalidated results stay
labelled diagnostic, even if a timing median looks plausible.

Before any run completed, the summary was also set to report the existing v2
**parameter-only** rule (R-hat <1.01; standardized mean difference <0.1 when
posterior/prior SD <0.8), using analytic prior SDs. This distinguishes random
mean differences in refreshed prior-only coordinates from disagreement in
informed coordinates. The original v1 verdict remains reported; neither rule
alone is a global posterior-coverage certificate.

## Locations

- Input preparation, settings, counts and assumptions:
  `runs/real_process_refit_20261002/{solar_permit,adu_permit}/`.
- Preparation and launch scripts: `runs/real_process_refit_20261002/`.
- Isolated remote snapshot, logs and fits:
  `/dfs/scratch0/alexspan/real_process_refit_20261002/` on sk3.
- Run names: `solar_permit_20261002`, `solar_permit_20262002`,
  `adu_permit_20261002`, `adu_permit_20262002`.
- Production engine: `pipeline/procbench/toy_statute/`.

## Results

All four attempts reached beta=1, generated answers and wrote final manifests.
They finished in about 22–23 minutes each on sk3 CPUs; none reached its timeout.
There was no automatic extension or replacement fit. Original attempts and source
snapshots remain intact.

| Domain / seed | Tempering stages | Sampling seconds | Mean saved log likelihood | PMF / saved-likelihood checks |
|---|---:|---:|---:|---|
| Solar / 20261002 | 35 | 1,297.5 | −446,416.15 | Pass |
| Solar / 20262002 | 37 | 1,361.2 | −446,991.94 | Pass |
| ADU / 20261002 | 38 | 1,331.4 | −443,404.04 | Pass |
| ADU / 20262002 | 37 | 1,309.5 | −443,419.92 | Pass |

Sampling seconds exclude most closeout; complete driver times were 1,316–1,363
seconds. These are not controlled speedup comparisons with earlier runs: scope,
target, particle budget, workers and observation handling differ.

Across every retained draw, town and day-step, the maximum normalization error
was **7.98e-13**. Recomputing the first and last saved likelihood of each run
agreed with the cached sampler likelihood to **5.83e-11** or better. The earlier
zero-mass/immortal-survival failure is absent in these saved states.

### Independent-run agreement: fails for both

| Diagnostic | Solar | ADU |
|---|---:|---:|
| Largest between-ensemble rank R-hat | 2.169 | 1.852 |
| Largest standardized mean difference | 1.991 | 1.801 |
| Parameters failing original v1 rule | 29 / 37 | 26 / 37 |
| Parameters failing existing v2 parameter-only rule | 28 / 37 | 26 / 37 |

These are substantial failures, not just the tighter gate reacting to Monte Carlo
noise in unobserved quantities. No pair is pooled into a released posterior.
Mean likelihoods are recorded for diagnosis, not used to choose the "winning"
seed or estimate posterior mode probabilities.

### Known prior-only controls: partial repair, remaining failure exposed

The refreshed labor/web controls behave as expected: across the four runs the
largest mean displacement among refreshed coordinates is about **0.085 prior
SD**, with SD ratios approximately **0.94–1.08**. Solar passes the declared
analytic-control screen on every tested coordinate.

ADU also has three unrefreshed prior-only report coordinates because this subset
has no completed forum reports. The broader check catches the remaining problem:
`leps` shifts **−1.32** and **−0.62 prior SD** in the two runs; `ldelta` also fails
the control screen in the first. These shifts cannot represent data learning.
The refresh implementation used here covered labor/web
absence; it needs extending to all mechanically absent likelihood coordinates.
That extension alone would not repair the major disagreement in informed timing
parameters. No post-hoc redraw was used to make these diagnostics look better.

### Whole-clock predictions can agree while the decomposition fails

The following are each run's **posterior-predictive median total days**. The
observed column is the median among completed administrative records only. The
model also sees open cases, so equality with that completed-only median is not a
calibration requirement. Source/window selection remains unmodeled.

| Jurisdiction | Solar observed | Solar seed 1 / 2 | ADU observed | ADU seed 1 / 2 |
|---|---:|---:|---:|---:|
| Los Angeles city | 117 | 112 / 103 | 133 | 133 / 133 |
| Los Angeles County | 7 | 6 / 6 | 226 | 298 / 300 |
| San Diego | 12 | 11 / 11 | 304 | 379 / 382 |
| San Francisco | 71.5 | 82 / 108 | 443 | 615 / 607 |
| Sacramento | 6 | 6 / 7 | 95 | 99 / 101 |

ADU whole-clock predictions are similar between the two runs. That does **not**
validate its step-level posteriors. For San Diego:

| Quantity | Seed 20261002 | Seed 20262002 |
|---|---|---|
| Posterior mean total days, median [90%] | 448.6 [442.6,455.6] | 450.8 [443.4,458.3] |
| Expected executed p-steps, median [90%] | 9.51 [9.03,9.92] | 7.88 [7.41,8.39] |

Those step-count intervals do not overlap despite closely matching total-time
estimates. Counts include repeated executions under the authored catalog; they
are not the number of distinct actions discovered in text. The quoted intervals
are diagnostic, conditional on the sampled configuration, and **not validated
credible intervals**.

Solar is more visibly multimodal. Seed 1 selects A2 for Los Angeles city, San
Francisco and Sacramento; seed 2 selects A1 for all five cities. San Francisco's
expected step count is 9.96 [9.29,10.15] versus 5.39 [4.80,6.19]. No 50/50 average
of these designs is reported as inferred structural uncertainty.

ADU selects the same broad menu entries across seeds (A1 for LA city, LA County
and Sacramento; A2 for San Diego and San Francisco), but disagrees within those
entries on the split into review, correction, notice/comment and hearing delays.
Agreement on a menu label therefore does not certify agency capability or the
number/cost of executed steps. Several A1 expected counts sit close to 8, the
maximum expected count allowed by this conditioned-geometric parameterization;
that boundary behavior is another reason not to call them observed procedure.

### Interpretation and next bounded step

This task successfully ran the repaired, existing Bayesian process engine on
real Solar and ADU evidence. It did **not** establish a validated full real-data
posterior, structural recovery, intrinsic agency capability, or superiority to
an LLM baseline.

The next bottleneck is mixing/identification of shared process components, not
the former probability-normalization defect. Before scaling back to all 467 ADU
jurisdictions, extend exact treatment of absent likelihood coordinates, improve
shared-parameter/multimodal exploration on this fixed input, and connect actual
intermediate milestones or repeat observations to the process decomposition.
Retain unsupported decomposition uncertainty; do not interpret more independent
seeds followed by best-likelihood selection as a Bayesian solution.

Machine-readable comparison and independent outputs:

- [Comparison](../runs/real_process_refit_20261002/comparison.json)
- [Four saved fits, including particles, answers, manifests and source snapshots](../runs/real_process_refit_20261002/remote_fits/)
- [Logs](../runs/real_process_refit_20261002/logs/)
- [Launch commands and budgets](../runs/real_process_refit_20261002/launches.json)

No additional runs were launched after these failures. No raw evidence, historical
posterior, remote acquisition job, or unrelated working-tree edit was changed.
