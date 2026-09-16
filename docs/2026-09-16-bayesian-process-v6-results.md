# Joint visit hierarchy: development status and results

2026-09-16. The [frozen protocol](2026-09-16-bayesian-process-v6-protocol.md) defines the
experiment. The full text-to-burden model and the matched-LLM goal remain incomplete.
No new reserved synthetic world has been opened and no new LLM win is claimed.

## Implemented connection

`bayes_trace_hierarchy.py` fits one posterior over agency/task/operation timing,
separate payer and agency work-hour hierarchies, normalized repeat probabilities,
same-case latent visits, source offsets and finite route hypotheses. A count claim
can affect timing and work through those shared visits. This is not a multiplication
of separately fitted v4 and v5 posteriors. Elapsed time never becomes staff hours.

`compact_visit_trace.py` computes initial/final decision clocks, first filing,
single cycles, sums of cycles, first-to-last spans, visits, operations and agencies.
Repeated blocks have unbounded support without enumerating every visit. Tests compare
compact operators with expanded `Trace` operators, including a million-repeat case.
Unspecified ordering defaults to serial rather than implausible free parallelism;
explicit empty within-block edges propose parallelism. Unknown actors and effort
are not assigned zero. Routes and interpretations still require an upstream compiler.

## Numerical status

The initial 25-warmup/100-draw, one-chain mixed-evidence smoke run completed but
**failed** convergence and prediction precision: 333 diagnostic quantities were
flagged, and the maximum checked clock-quantile change from 64 to 256 population
nodes was 27.1%. It is a smoke test, not an inferential result.
[Preserved pilot](../runs/bayes_v6/integration/pilot_mixed/posterior.json).

Before the four-chain fits, the sampler gained a Gaussian conditional update
which holds every realized case duration fixed while jointly resampling its
hierarchical decomposition and case noises. A likelihood correction covers
population/selection terms. Regression tests verify unchanged individual-claim
likelihoods and the known conditional Gaussian moments. A scale/source-offset
move likewise has a likelihood correction. Mean counts and work amounts now use
analytic expectations; these quantities do not require simulated population averages.

Both full conditions began with four independent chains, 1,000 warmup and 2,000
retained draws, and 1,024 population nodes. The slower mixed-evidence attempt was
subsequently stopped for a verified computational improvement; its progress, inputs
and source snapshot are preserved. The timing-only attempt was already further
along and was left running. No data, prior or model variant was selected by scores.

The batched likelihood matched the immutable original implementation **exactly**
at 200 checked states per condition (100 saved pilot states and 100 independent
prior states), including both structural routes. The recorded speedups were 5.4x
for mixed evidence and 2.3x for timing-only evidence. These are local timings, not
guaranteed end-to-end speedups. A previously stated 11.3x saved-state-only speedup
has no located supporting artifact and is withdrawn. The replacement mixed run
uses the identical configuration and data.

- [Mixed target/computation audit](../runs/bayes_v6/diagnostics/mixed_likelihood_batching/audit.json).
- [Timing-only target/computation audit](../runs/bayes_v6/diagnostics/timing_likelihood_batching/audit.json).
- Original outputs: `runs/bayes_v6/integration/mixed_joint_batched/` and
  `runs/bayes_v6/integration/timing_only_joint/`.

Both original four-chain fits completed and **failed** the declared numerical gates.
The timing-only fit flagged five diagnostic quantities; the mixed fit flagged 17.
Their maximum checked clock-quantile changes on increasing population prediction
nodes from 1,024 to 4,096 were 4.18% and 4.96%, respectively, above the 2% threshold.
Both had exactly zero likelihood change: these experiments have no population
integration in their case-only, no-selection likelihoods. These are computational
failures, not accuracy comparisons, and their original reports remain preserved.

The timing-only fit was extended by 4,000 draws per chain, yielding 6,000 retained
draws per chain. All convergence diagnostics passed. Its 4,096-to-16,384 prediction
check still narrowly failed at 2.034%. A separate prediction-only refinement then
recomputed outputs at 16,384 nodes **without changing or adding any posterior draws**.
The 16,384-to-65,536 check passed at 0.869%; all 200 checked saved likelihoods matched
exactly. This fit is now numerically usable, not a full-model validation.
[Completed timing-only fit](../runs/bayes_v6/integration/timing_only_joint_prediction16384/posterior.json).

The timing-only posterior medians for initial-decision time are 18.14 days
(90% interval 13.08–25.16) for P and 25.60 (14.69–44.24) for Q. There is no direct
payer- or agency-hours evidence in this condition. For example, P's mean payer-work
interval is 0.037–118.37 hours: the estimate must not be presented as measured labor.
The posterior probabilities of the complete four-operation/two-agency route are
0.490 and 0.587. Total times alone have not established those inventories.

The mixed fit also completed its 4,000-draw extension, reaching 6,000 retained draws
per chain. All declared convergence diagnostics passed; the 16,384-to-65,536
prediction check passed at 0.723%. Its 200 checked saved likelihoods match exactly;
no evidence or prior changed. Both full conditions are now numerically usable.
`refine_visit_predictions.py` now supports immutable prediction-only refinements and
rejects them when population integration contributes to the likelihood.

## Completed controlled comparison: gains and failures

The paired evaluator verifies unchanged original timing claims, unchanged route
hypotheses and statistical settings, completed fit hashes and numerical gates. It
also replays the hashed frozen generator to reproduce both observed datasets and
the truth artifact. The fitter never reads that truth. Additional derived agency
inventory diagnostics (including presence and conditional chains) also pass: the
original fitter checked coordinates and program outputs but did not separately
check the nonlinear agency-inventory summaries.

These are two programs in one favorable development realization, not replications,
a calibration certificate, a text-pipeline comparison or an LLM benchmark.

| Quantity | Timing-only mean point error | Mixed-evidence mean point error |
|---|---:|---:|
| Expected visits, absolute log error | 0.169 | 0.043 |
| Mean payer hours, absolute log error | 0.561 | 0.242 |
| Mean agency hours, absolute log error | 0.486 | 0.052 |
| Any-correction probability, absolute probability error | 0.236 | 0.037 |
| Continuation probability, absolute probability error | 0.101 | **0.132** |

Corresponding 90% interval scores improve for all five listed quantities; for
example, expected-visit log interval score decreases from 0.817 to 0.329, and agency
hours from 7.659 to 1.126. The timing-only labor channels have no direct hours
evidence, so this comparison includes the expected benefit of actually observing
hours. Mixed-evidence operation/agency counts recover four/two, but the experiment
explicitly supplies complete counts and informative visit counts. This is not
evidence that the model can discover an unlisted agency from ambiguous prose.

**Agency cycle-time point estimates get worse.** The review agency's inventory mean
is 5.08 days in the generator. Timing-only estimates 5.25 (90% interval 1.03–11.04);
mixed evidence estimates 8.10 (5.49–11.94), missing truth. The records agency's truth
is 3.39; estimates move from 4.15 (0.37–19.18) to 1.52 (0.20–5.54). Their interval
scores improve through narrowing, but that does not erase the worse point accuracy
or the review agency's interval miss. These outputs pass their extra numerical
checks, so more MCMC is not an explanation for these errors.

A source-level diagnostic is that the six added review-time reports are centered
at approximately 15.7, 6.6, 16.4, 16.2, 20.5 and 11.8 days, while the generating
review-cycle median is eight. That small realized sample is high, and decomposition
of the remaining total among other operations remains uncertain. This is a plausible
contributor, not a demonstrated causal decomposition of the error. The realization
and priors are preserved, not replaced with a more favorable seed.

Mixed-evidence process median predictions are 21.05 days (15.35–29.23) for P and
23.58 (14.93–36.61) for Q. These process quantiles are **not accuracy-scored here**:
the frozen truth artifact contains counts, work means, repeat probabilities and
agency cycle means, but no population process quantiles. A separately verified
derivation of those targets remains necessary; reporting predictions is not a
substitute for validating timing accuracy.

[Paired results with agency checks](../runs/bayes_v6/integration/paired_comparison_with_agency_checks/comparison.json).
The earlier paired report without the supplemental agency checks is retained too.

## Connecting the public-source audits

`compile_visit_durations.py` now implements the elapsed-observation boundary between
quote-checked source ledgers and the joint model. It preserves case/source linkage,
reported units and rounding, first versus final clock endpoints, one-sided censoring,
and every operator alternative. Declared priors must cover the complete alternative
set; unsupported alternatives cannot be dropped and the rest renormalized. A test
fits a compiled claim through the actual joint likelihood. This is not yet a complete
route/identity/count/resource compiler.

The first strict pass over the existing three source sets accounts for every one
of their 236 measurements and all 146 eligible elapsed claims. It compiles **zero**
claims under the current model and default no-added-assumptions policy. This is not
evidence that the text has no information or a license to omit it in a benchmark.
Overlapping reasons include 92 claims with an unknown duration basis, 35 with
unknown or unsupported clock boundaries, nine with waiting-only operators, two
with service-only operators, 24 with business-day calendars, and 22 carrying case
route/milestone constraints that still need integration. In addition, 123 individual
claims need a declared sampling assumption; typical/forecast statements and finite
cohort summaries require their own observation likelihoods.
Even after removing missing sampling/interpretation-prior declarations from the
reason lists, 145 of the 146 claims still need a model or semantic-contract extension.

[S01 coverage](../runs/bayes_v6/source_compilation/J1__S01/compilation.json),
[S03 coverage](../runs/bayes_v6/source_compilation/J1__S03/compilation.json),
[S07 coverage](../runs/bayes_v6/source_compilation/J2__S07/compilation.json).

The next source-model extension must represent plausible ambiguous meanings with
explicit, sensitivity-checked observation hypotheses, not require certainty from
every document or coerce all durations into one clock. Waiting/service decomposition,
case-specific routes, actual calendar conventions and finite-cohort uncertainty are
also concrete requirements exposed by these audits. Longer MCMC alone cannot supply
these mechanisms. No new source interpretations were obtained using fitted scores.

## Within-visit waiting/service: implemented in the same joint model

The optional phase hierarchy now partitions each visit's cycle into waiting and
elapsed service, with shared agency/task/operation effects on its service fraction.
It does not fit another posterior and multiply it into the timing posterior.
Both phase reports and cycle reports observe the same case and source family;
person-hours remain an independent measured resource channel. Conditional
cycle/fraction independence, fixed case-fraction spread and perfect correlation
between a case's repeated visits are explicit limitations.

Tests check conservation, compact/expanded trace agreement, shared-case and
cross-program propagation, independent labor/count/clock behavior, likelihood
batching, phase-moment integration and conditional sampler moves. The earlier
phase-disabled model matches its independently loaded frozen source package
**exactly** at 200 checked saved/prior states, including both route hypotheses.
[Compatibility audit](../runs/bayes_v6/diagnostics/phase_disabled_compatibility/audit.json).

The pre-specified ten-case appointment experiment has a 14-day cycle median,
independent case variation in the cycle and service fraction, and independent
noisy cycle/wait/service reports linked by case. The cycle-only and mixed fits
use identical hierarchy/phase priors and unchanged original cycle reports.
No labor measurements are supplied. The generator and truth are replayed and
hashed separately from inference; this is not a text pipeline or LLM benchmark.

The cycle-only fit passes its four-chain and prediction checks with 2,000 retained
draws per chain. The initial mixed fit fails 11 convergence quantities and is
preserved. A same-target extension to 6,000 draws per chain passes convergence,
but fails the 1,024-to-4,096 population-prediction check at 2.51%. Recomputing
predictions at 4,096 nodes using **identical saved draws** passes the 16,384-node
check at 0.526%. All 200 checked saved likelihoods match exactly; phase-mean
integration differences are below 6e-16. Both final conditions are numerically
usable, which is not itself a calibration certificate.

| Population quantity | Generating value | Cycle-only posterior median | Mixed posterior median (90% interval) |
|---|---:|---:|---:|
| Cycle median, days | 14.00 | 12.28 | 11.91 (8.71–16.30) |
| Cycle p90, days | 21.92 | 22.89 | 22.29 (16.01–35.13) |
| Mean cycle, days | 14.88 | 13.92 | 13.50 (9.98–19.25) |
| Mean waiting, days | 14.87 | 6.97 | 13.48 (9.96–19.22) |
| Mean elapsed service, minutes | 25.44 | 9,484.44 | 36.80 (21.71–63.61) |

The cycle-only waiting/service split has **no direct phase evidence**. Its service
interval is extremely wide yet still misses the small generating mean: a vague
prior is not automatically safe for every scale. Adding the correctly typed
phase observations changes service from an unlearned days-long split to a
minutes-long estimate without shrinking the visit's whole cycle or inventing
labor. Waiting and service absolute log errors improve from 0.758 / 5.921 to
0.098 / 0.369. Their proper 90% log-interval scores improve from 5.649 / 30.050
to 0.657 / 1.075.

**Cycle median and mean point accuracy get slightly worse**, although both still
cover truth and their interval scores improve. Every listed score and failure is
retained. This is one favorable ten-case realization, not replicated calibration,
identification of intrinsic agency effects, proof of sufficient information for
unseen steps/agencies, or parity with the LLM.
[Verified paired comparison](../runs/bayes_v6/phases/comparison/comparison.json).

The compiler now recognizes four formerly unsupported W1/S01 phase claims: one
appointment-access wait, two inspection-access waits, and the 20-minute appointment.
They still need a declared case-sampling assumption. Seven other phase claims
have unknown or partial within-visit endpoints and remain explicit unresolved
measurements, not full-phase assertions. Overall default strict coverage remains
0/146; after ignoring only missing sampling/interpretation-prior declarations,
five claims are now model-compatible rather than one. The other 141 still need
semantic/operator extensions. This fixes a real representation defect but does
not solve the much larger source-integration gap.
[Updated S01 coverage](../runs/bayes_v6/source_compilation_with_phases/J1__S01/compilation.json),
[S03](../runs/bayes_v6/source_compilation_with_phases/J1__S03/compilation.json),
[S07](../runs/bayes_v6/source_compilation_with_phases/J2__S07/compilation.json).

## Information limits that this experiment cannot resolve

The two programs share agencies, but review and records staff perform disjoint
task types. An SVD-based actor/task design audit flags their agency contrast as
inseparable from task mix without prior assumptions—even if every operation mean
were known. This experiment can test joint inventory timing/count/resource learning,
not identify intrinsic causal agency slowness. The diagnostic uses the union of
route hypotheses and is optimistic: passing it would not prove identification
from the actual claims. Work-hour outputs in the timing-only condition must be
labeled as lacking direct resource evidence.

Outstanding limitations include source-to-route compilation, genuine per-case
branching versus shared structural uncertainty, partial recording, competing-risk
abandonment, nested/interleaved rework and unknown inventory coverage. The complete
Bayesian objective and fresh matched-input comparison remain active requirements.

## Audit follow-up: interpretation experiments and implementation repairs

The four already-started interpretation fits all completed under their original
protocol. In order `timing_count_only`, `mixed_residual10`, `mixed_residual25`,
`mixed_residual50`, they flag **4 / 9 / 8 / 7** convergence quantities. Their
prediction-resolution checks pass, but all four remain numerically unusable.
No timing/count accuracy comparison or new sampling extension has been run.
[Preserved fits](../runs/bayes_v6/interpretations/fits/).

The source-only responses now validate for all three programs, including S07.
This is explicitly **revalidation under a changed contract**, not a claim the old
validator passed them: a per-cycle report can cover each observed round without
becoming a sum. All original fields and raw responses are unchanged, and imports
save every validator hash and source snapshot.
[Validated imports](../runs/bayes_v6/audit_updates/hypotheses/).

An explicit development policy plus residual retention now accounts for and
attaches likelihoods to all **146/146** eligible elapsed reports. **Only four**
have informative process likelihoods; **142** are independent residual-only
reports. This is not 100% informative coverage, a fit, or a Bayesian win. The
minimal policy declares unselected sampling and a 7/5 business-day sensitivity
convention; it does not invent clock aliases or learned hypothesis weights.
[Compilation artifacts](../runs/bayes_v6/audit_updates/compilation/).

Saved-draw information reports reproduce **199/302** mixed-evidence and
**259/302** timing-only coordinates with under 10% marginal variance contraction.
They also retain posterior mean shifts and block covariance directions: marginal
contraction is not all information learned or proof that a derived sum is
unidentified. No old posterior was modified.
[Mixed report](../runs/bayes_v6/audit_updates/identification/mixed/identification.json),
[timing-only report](../runs/bayes_v6/audit_updates/identification/timing_only/identification.json).

The [audit implementation record](2026-09-16-bayesian-audit-implementation.md)
lists the compiler/calibration path, prospective numerical-gate changes,
identification warnings, and remaining refactor/model work. Old failures are not
retroactively promoted under the new gates.
