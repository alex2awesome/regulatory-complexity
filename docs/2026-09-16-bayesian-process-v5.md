# Bayesian v5 development: measurement clocks before process reconstruction

Status: continuing development, **not a validated replacement for the full burden
model**. The [protocol](2026-09-16-bayesian-process-v5-protocol.md) preserves the negative v4
holdout result. W1 is now development data; no new reserved result has been opened.

The purpose of this iteration is to find whether a coherent, smaller Bayesian
measurement channel can estimate whole-process timing without summing overlapping
stage spans. The v4 agency/task hierarchy and its controlled transfer results are
preserved. These timing experiments do **not** solve uncertain operation identity,
agency counts, repeat visits or labor, and do not yet connect their process-level
posterior back into the task hierarchy. They are not a switch to an LLM estimator.

## What changes

`audit_measurement_semantics.py` produces an immutable, quote-validated sidecar:
whole case versus stage span versus visit/wait/service; first versus complete
submission; endpoint and censoring; population versus selected cohort; the actual
statistic; and original rounding precision. It receives public text and existing
claims only, not hidden outcomes or Bayesian estimates. In particular, 20 minutes
of appointment service no longer has to mean a multiweek appointment-access wait.
The process channel leaves both for the separate task-duration channel.

The first model integrates a latent case duration once per case. Repeated claims
about that case share its duration; repeated source families share an offset.
Whole-case reports constrain a population lognormal median directly. Measured
means and p90s observe different distributional functionals. A typical range or
informal forecast receives substantially more observation error than a measured
median. Statutory caps, historical observations and work hours are not elapsed
completion-time measurements.

Start-clock fractions are explicit uncertainties: first filing removes an
uncertain preparation fraction, **not all repeat correction submissions**.
Unspecified starts marginalize preparation/first-filing clocks. Closeout is an
additional uncertain duration, not automatically initial decision. Unknown
endpoints marginalize initial/closeout interpretations. These fractions are
modeling assumptions needing sensitivity, not facts extracted from text.

A conservatively audited unknown completion status is not silently discarded in
the richer variant. It is a mixture of completed and partial-duration reports:
completion probability has Beta(2,1) prior and a partial report observes a
Beta(2,2) fraction of eventual duration. Both alternatives have interval-probability
likelihoods. Adding an interval probability to a survival probability would compare
different observation measures; the implementation does not do that. Explicitly
right-censored initial decisions use the survival likelihood. An open case whose
initial decision is unknown is retained but is not automatically initial-decision
censoring.

## Ascertainment: which cases make it into documents?

Write `z` for a standardized latent log duration, `Phi` for the standard-normal
CDF, `w=0.35`, and `c=Phi^{-1}(0.75)*sqrt(1+w^2)`. Define

```
h(z) = Phi((z-c)/w)
weight(z,kappa) = [1 + (exp(kappa)-1)*h(z)] / [.75 + .25*exp(kappa)]
```

`E[h(Z)]=.25` for `Z~Normal(0,1)`, so this density ratio integrates to one.
The model with `kappa=0` has no duration-dependent selection. The selection variant
uses `kappa~HalfNormal(1.5)`; it does not plug in a benchmark-specific bias correction.
Its normalizer is essential: omitting it would reward arbitrary selection strength.
Tests check normalization and an independent numerical integral. Selection
strength is weakly identified from a few stories and confounded with source bias.

## Outcome-stratified Bayesian extension

`audit_case_outcomes.py` adds typed, quoted case outcomes and population count
denominators. For example, 137 issued and 37 denied in the same public cohort can
constrain approval prevalence among decided cases. Eighteen issued out of 81
received cannot: the remainder includes unresolved statuses. Historical, selected
or undefined denominators do not become population approval rates.

The extension has two normal components for log duration: approval and denial,
with a shared within-outcome spread and an uncertain difference in locations.
The population median and p90 are roots of the mixture CDF, **not** averages of
component medians. Initial-decision abandonment is retained separately rather than
treated as a completed approval/denial.

Known-outcome anecdotes condition on that outcome; the number of explicitly
reported denials is not a binomial population survey. Unlabeled cases marginalize
the selected outcome mixture. An uncertain denial-related posting multiplier is
shared across jointly fitted programs. Delay-selection normalization is recalculated
for each outcome component and for their mixture. Administrative outcome counts
have an explicit uncertain cohort log-odds offset.

Selective disclosure of outcomes remains a limitation: someone may mention a
denial more explicitly than an approval. The selected unlabeled-case mixture is
an assumption, not identification of that disclosure mechanism. Broader route
mixtures, visit-based clocks, and uncertain agency identity remain open work.

## Independent checks and data volume

The selection recovery experiment uses 32 generated datasets at each of 10, 100
and 1,000 **independent cases**, with true median 30 days. It intentionally knows
case variability, has exact clocks, and contains no reporting errors; it tests
the selection component, **not calibration of the full text pipeline**.

| Independent cases | Mean estimated median, ignoring selection | With selection | 90% coverage, ignoring / modeling selection |
|---:|---:|---:|---:|
| 10 | 43.31 | 33.43 | 14/32 / 30/32 |
| 100 | 42.06 | 31.23 | 0/32 / 30/32 |
| 1,000 | 41.51 | 29.95 | 0/32 / 30/32 |

These fixed-parameter recovery results are not simulation-based calibration over
the full prior. They demonstrate that more biased observations can make a wrong
model more confidently wrong. More documents also need not mean more independent
cases or source families. [Saved component experiment](../runs/bayes_v5/validation/selection_grid/summary.json).

## Numerical and comparison discipline

Four independent chains, rank-based diagnostics, saved source/input hashes and
immutable experiment directories remain required. Latent case durations are
integrated by Gaussian quadrature; doubled-resolution checks are separate from
MCMC convergence. A maximum checked log-likelihood change >=0.01 marks a fit
numerically unusable even when its chains pass. Both checks are diagnostics, not
proof of calibration or a uniform quadrature error bound.

The optional native likelihood uses the closed-form Student-t(4) CDF and is checked
against an independent SciPy implementation, including both tails. It changes
computation, not the observation model. Incomplete slow attempts and failed
precision checks are preserved, not presented as completed comparisons.

Fresh three-repeat LLM controls receive the same ledgers, semantic sidecars and
program grouping as each experiment. Outcome-aware fits get newly matched controls
with the outcome sidecars too. Scoring uses log-median absolute error and proper
90% log-interval score; no LLM CRPS is invented. All tested variants, numerical
failures and individual-program failures must be shown. A favorable timing result
alone cannot complete the full-burden objective.

The [existing TikZ diagram and glossary](figures/latex_plate_diagram_simplified/README.md)
continue to distinguish the fuller target graph from implemented components.
This experimental timing channel is not a claim that the entire target graph is fitted.

## Benchmark contract defect found during development

The existing W1 S01 dashboard specification supplies a rounded median and "182
cases", without a clock definition. The renderer added acceptance-to-closeout
wording. The generator actually computes this median from arrival/preparation
through the **last recorded decision**, excluding abandoned cases; its denominator is 174,
not the 182 uncensored cases including eight abandonments. Thus a model faithfully
reading this dashboard is adjusting between clocks that the original scalar
benchmark did not distinguish. This is an evaluation/input mismatch, not grounds
to secretly relabel the input so an estimator scores better.

The generator now emits the actual clock and `elapsed_days.n` for **future**
dashboard specs, and the rendering brief forbids invented boundaries. A regression
test distinguishes 174 decided from 182 completed cases. W1 documents, specs,
truth and existing scores have **not** been regenerated or changed. This defect
does not erase the independent v4 solar failure or establish Bayesian superiority.

A deeper audit found that `simulate.py` overwrites `decision_end` on every repeat
decision. The legacy `elapsed_days` target is therefore not necessarily the first
initial decision requested in the model/baseline prompts. Among the same finally
decided, uncensored evaluation cohorts, first-decision medians are 111 / 74 / 17
days for S01 / S03 / S07, versus the legacy last-decision medians 128 / 74 / 21.
Those are **diagnostic alternative estimands, not replacement scores or a new
held-out victory**. A fresh benchmark must declare first decision, last decision,
and closeout separately; legacy comparisons stay intact. New dashboard wording now
says last recorded approval/denial to match the existing generated statistic.

Different generator quantities must also remain distinct: `persona_from` sums
per-visit cycle durations across an activity's visits; log summaries separately
contain first-visit durations and first-to-last stage spans. Those three quantities
are not interchangeable. Inconsistent reported numbers can additionally arise
from intentional synthetic reporting noise; they are not automatically evidence
of overlapping spans.

## Learning preparation from partial clocks

`bayes_preparation_measurement.py` extends the outcome model with quoted pre-filing
span constraints. With latent case duration `D` and preparation fraction `f`, a
partial span observes `u*f*D`. A singleton's `u` is initially uniform. Explicitly
disjoint spans share a Dirichlet budget with a separate unreported remainder. Their
sum cannot exceed preparation, but their reports need not measure all preparation.
Other spans have separate partial-coverage variables and are not added. A fully
anchored process-start-to-first-submission report observes `f*D` directly.

The preparation reports and total for the same person observe the same integrated
case duration, source offset and outcome component. Thus preparation evidence can
inform the total and the preparation fraction together. It is not a two-stage
subtraction of noisy point estimates. Unknown initial-versus-rework application
spans stay explicitly excluded; a meeting's minutes are not given the same generic
coverage prior as an appointment-access wait measured in weeks.

This deliberately limited extension assumes a common preparation fraction across
cases and a specified prior on coverage. It does **not** learn agency-level task
times, operation counts or work hours. Those remain the next connection to the
fuller hierarchical graph, not benefits claimed for a partial-clock model alone.
[Frozen development settings](2026-09-16-bayesian-process-v5-protocol.md#partial-preparation-experiment-specified-before-fitting).

The [visit-clock contract](2026-09-16-bayesian-visit-clocks.md) defines the implemented
deterministic observation operators and the remaining requirements for connecting
these timing channels back to agency/task parameters, repeats, counts and labor.

## Case variation and segmentation-invariant coverage

`bayes_variable_preparation.py` adds a sensitivity model in which each case has
its own logistic-normal preparation fraction. Reports from one case share that
fraction. Population clock summaries integrate the fraction distribution with
the approval/denial lognormal mixture; a median after subtracting preparation is
not estimated by subtracting medians. Quantile sampling error uses the density
at the quantile, and arithmetic-mean sampling error uses the mixture's moments.
These are asymptotic summary approximations, not individual administrative data.

The alternate coverage prior separates total observed coverage, `C~Beta(1,1)`,
from the Dirichlet allocation of that coverage among disjoint reported spans.
This removes the earlier prior's dependence of total coverage on how many pieces
were reported. Unsupported overlapping spans are still not summed. Case fraction
spread is fixed for sensitivity analysis, not claimed to be measured, and the
model still assumes fraction and total duration are conditionally independent.
The paired SD-0/SD-1 experiment is specified in the
[protocol](2026-09-16-bayesian-process-v5-protocol.md#case-varying-preparation-sensitivity-specified-before-fitting).
