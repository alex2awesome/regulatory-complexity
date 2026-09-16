# Joint visit hierarchy: development protocol

2026-09-16. This is a continuation toward the full Bayesian burden model, not a
change to the matched-LLM acceptance criterion in the v5 protocol. W1 remains
development data. No new reserved world has been generated or opened.

## Joint model

Agency and task-type effects generate positive per-visit calendar durations.
Payer and agency person-hours have independent hierarchies, never conversions
from days. Known absence of work is an explicit zero; unspecified work remains
unknown. A case shares its operation-level durations and resource amounts across
its repeat visits. Perfect within-case repeat correlation is an initial modeling
assumption to relax, not a fact inferred from public documents.

Route hypotheses are finite, explicit alternatives with declared prior weights.
One structural hypothesis is shared by every case in a program; this variable
does not pretend to be a population branch frequency. Each hypothesis consists
of sequential blocks containing an explicit operation DAG. Unspecified within-block
ordering defaults to serial; an empty edge list explicitly proposes parallelism.
Different hypotheses can include different operations or actor assignments.

Repeated blocks have unbounded hurdle-geometric additional rounds:
`P(R=0)=1-q`, `P(R=k)=q*(1-r)*r^(k-1)` for `k>=1`.
The any-correction prior is uniform; continuation has `Beta(2,3)` prior. Compact
trace operators preserve the full support without a maximum visit count. First
and final decisions, first filing, cycle sums and first-to-last spans differ.

All claims enter **one likelihood and one prior**. There is no multiplication of
previously fitted v4 and v5 posteriors. Same-case timing, counts and resource reports
observe the same latent visits. A separately counted rework cohort observes `q`;
an informal frequency is not assigned a sample size. Alternative duration operators
are mixed at the likelihood level using declared modeling priors, not LLM confidence.
Source offsets and robust interval-reporting errors reuse the earlier measurement
approach. An optional duration-dependent selection likelihood is normalized over
population traces, not independently over counts and timing.
The cohort contract explicitly requires completed cases for the repeat block;
an observed-by-date cohort containing open cases is not an eventual-risk binomial.

An actor/task design audit accompanies inference. Disconnected actor/task groups
mean that even perfectly known operation means cannot separate an agency contrast
from task-mix differences without prior assumptions. Passing this optimistic check
does not establish identification from actual claims. Agency inventory mean time
is not an intrinsic causal agency effect. The first integration experiment's review
and records agencies perform disjoint task types; it can test connected inventory
timing/count learning, but cannot validate separating those agencies' effects from
their task mix. This limitation is reported, not removed by changing the dataset.

Continuous parameters use blocked elliptical slice sampling. Program structural
alternatives use exact finite conditional updates. All priors, inputs and source
snapshots are saved; numerical improvements may change computation, not the target.

## First integration experiment, frozen before generation

This is a favorable **development integration test**, not a text-pipeline or LLM
comparison and not a calibration certificate. Use two programs sharing a review
agency and a records agency. The complete route contains applicant filing,
review, records checking and decision. Filing/review form a repeated block.
The alternative route omits the records check, with equal structural prior weight.
True first-visit medians are 2 / 8 / 3 / 1 days; case log SD is 0.45 with independent
visit channels but perfectly correlated repeats. Rework `(q,r)` is `(0.55,0.35)`
and `(0.25,0.20)` in the two programs. Agency hours per review/check/decision have
medians 1.5 / 0.6 / 0.2; payer filing hours have median 0.75. Within each channel,
a shared case log effect has SD 0.20. Known work-inapplicability is explicit.

Generate 10 cases for the first program and 3 for the second, fixed seed
2026092007. Compare the same whole-case timing reports alone with those reports
plus same-case first-visit review timings (up to 3 cases/program), actual complete
operation/agency counts (one case/program), total visit counts (up to 3), separate
agency/payer work-hour reports (up to 3), and independent 20-case correction
cohorts. Reports are intervals around amounts with multiplicative log-normal
noise SD 0.15; count reports use the actual integer. Source families are independent
case interviews, with same-person fields linked. No claim describes a first review
cycle as a sum across visits.

Use the implementation's weak location, agency, task, operation, source and noise
priors; do not center them on the generating values. Begin with a short diagnostic
run, then four chains with 1,000 warmup and 2,000 retained draws, extending for
computation if needed. Require R-hat <=1.01, bulk ESS >=400 and tail ESS >=200 on
declared outputs and sampled parameters; a smoke run is not a successful fit.
Save both conditions, including failures. Check population prediction resolution
separately; case-only, no-selection likelihoods contain no population quadrature.
Require maximum checked log-likelihood change below 0.01 and clock median/p90
relative change below 2% when increasing prediction resolution fourfold. These
finite-state checks are not uniform error bounds. Counts and resource means use
analytic expectations under the declared independent count/duration model.

If only population-prediction precision fails and no population integration occurs
in the likelihood, increase prediction nodes using the identical saved draws rather
than rerunning MCMC. Verify saved likelihoods and input hashes, preserve the failed
run and record the prediction-only refinement separately. Do not apply this shortcut
to population-summary or selection-normalized likelihoods.

Report agency/task cycle timing, process median/p90, operation and agency counts,
visits and separate work hours. Explicitly distinguish prior-driven work estimates
in the timing-only condition. A favorable result is evidence of connected learning,
not evidence of full calibration or superiority over the LLM baseline.

## Outstanding before an end-to-end comparison

- Compile reconciled public-source route/identity hypotheses into this contract;
  do not repair W1 ambiguities with hidden generator facts.
- Support partial recording, unknown clock endpoints, outcome branches and
  competing-risk abandonment without interpreting open cases as unfinished first
  decisions by default.
- Relax repeat-duration correlation and evaluate nested/interleaved rework where
  documents support it. Finite hypotheses do not solve missing inventory coverage.
- Extend count/rate and population-summary likelihoods beyond supported contracts;
  reject unsupported denominators rather than silently assigning an effective n.
- Compare a frozen candidate on faithful fresh synthetic documents with matched
  LLM inputs and the original timing/count/labor scoring requirements.

## Within-visit waiting/service extension, specified before fitting

Extend the **same** joint hierarchy, rather than adding another fitted estimator.
Keep its cycle-duration prior unchanged. An explicitly enabled phase model partitions
each case-operation cycle `D` into `service = f*D` and `wait = (1-f)*D`.
The service fraction has a logistic-normal hierarchy: global logit location with
Normal(0,3) prior, agency/task/operation effects with Normal(0,1) priors, and a
case-operation logit deviation with fixed SD 0.75. These are weak sensitivity
assumptions, not measured proportions or settings selected using W1 scores.
Fraction and cycle noise are conditionally independent; repeated visits retain
the existing perfect within-case correlation. Elapsed service is **not** labor.

The old phase-disabled configuration and numerical target must remain available.
Source operators require supported activity linkage and explicit within-visit
boundaries: request/visit-start to service-start for waiting, service-start to
service-end/visit-end for service. Unknown endpoints and preparation ending at an
unspecified intermediate milestone are not automatically complete visit phases.
First, last and one-unspecified visit operators are equivalent only under this
model's declared repeat correlation; complete-case sums multiply by visit counts.

Before any full-source fit, check compact versus independently expanded traces,
conservation of cycle time, preservation of hours/counts/clocks when only phase
parameters change, batched/reference likelihood agreement, prior-conditional
sampler updates, and disabled-model saved-likelihood compatibility. Then fit a
fixed ten-case generated appointment example with a 14-day cycle median and a
median service fraction of 20 minutes / 14 days, using independent log-cycle SD 0.35 and
logit-fraction SD 0.60. Use seed 2026092011, reporting log-noise SD 0.10, linked
wait/service/cycle reports for each case, and a separate truth artifact. This is
a targeted measurement integration test, not an LLM comparison, calibration over
all settings, or a substitute for full timing/count/labor evaluation. Use unchanged
default hierarchy priors; do not center them on the generating values. Start with
four chains, 1,000 warmup and 2,000 retained draws; extend/refine only for declared
numerical diagnostics. Report phase-enabled versus phase-omitted likelihood
behavior without relabeling service reports as whole cycles in a scored candidate.
Preserve a matched cycle-only condition with the same enabled phase priors and
the same ten cycle reports; its unmeasured phase split must remain prior-dependent.

## Ambiguous observation operators, specified before source audits or fitting

Retain the strict quote-checked visit audit as a record of what the source actually
identifies. Add a separate, source-only **hypothesis** sidecar: candidate readings
must name the original operator they refine, preserve every already-known field,
use only the existing supported activity linkage, quote their motivation, and list
the additional assumptions. The sidecar cannot alter numbers, statistic, units,
case identity, actor identity or known clock boundaries. Unsupported partial spans
and recording mechanisms remain unresolved. A task label plus duration may motivate
single-cycle, cumulative-cycle, span, waiting or elapsed-service alternatives; it
does not establish any of them as fact. Preserve identified alternatives verbatim.

Run the same pinned `gpt-6-astra`, `xhigh`, schema-constrained, isolated read-only
interpreter on the three existing public-document/evidence/visit-audit bundles.
No truth, posterior, score or benchmark-generator descriptions go in its prompt.
Capture JSONL events and reject an audit that uses a tool; the no-tools prompt
alone is not evidence that the run stayed source-only. Check exact quotes and
contract invariants. Preserve attempts and source/input/schema/prompt hashes.

Candidate sets are not assumed exhaustive. A declared prior assigns probability
0.25 to an unmodeled-report alternative; the remaining mass is uniform across
distinct operator bases and then across distinct readings within each base.
This is a modeling prior, not LLM confidence. Predeclare residual-weight sensitivity
0.10 and 0.50; do not select a weight from downstream accuracy. The residual uses
a normalized Student-t(4) distribution for log elapsed days, centered at log(7)
with scale 3, independent of route, case duration and source offset. The broad
reference is not an extra duration observation or a learned missing operation.
Retain the original residual mass when an activity is absent from a route; never
renormalize surviving interpretations. Report posterior interpretation weights so
compiled claims assigned to the residual are not counted as identified timings.
The existing relative reporting-contamination component is a different mechanism.

Keep the no-sidecar compiler and the likelihood for old inputs unchanged. Both
batched and scalar likelihoods must agree; test normalization, non-informative
residual behavior, preserved alternatives, source independence and disabled-input
compatibility. Check coverage on all three source corpora, with explicit case
sampling policies, retaining unresolved populations, finite-cohort summaries,
calendars and route constraints in the ledger rather than silently dropping them.
Do not call improved compiler coverage a completed full-source fit or an LLM win.

For a bounded sampler check use a ten-case, two-operation serial repeat block,
with independent generated case log cycles (medians 2 and 8 days; SD 0.35),
any-repeat probability 0.4, continuation probability 0.2, seed 2026092023.
Both conditions receive the same process-start-to-final-decision timing and
visit-count reports (review completion marks each decision in the repeat block);
the added-evidence condition also receives an ambiguously labeled review duration
that in generation uses one cycle, all review cycles, or the review span (chosen
uniformly per case), with report log noise 0.10. The estimator receives the
three alternatives plus the fixed residual, never the generating interpretation.
Compare equal priors with versus without these extra reports; save all results,
including failures and worsened metrics. Use four chains, 1,000 warmup and 2,000
retained draws, extending only for the existing numerical gates. This checks
integration of ambiguous evidence in the joint hierarchy; it does not replace a
fresh full-burden, matched-input text/LLM benchmark.
