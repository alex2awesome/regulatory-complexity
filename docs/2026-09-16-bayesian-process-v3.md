# Bayesian process model v3: implementation and synthetic pilot

2026-09-16. This is an executable **first-stage, modular Bayesian model**, not a
claim that the full generative story has been fitted or calibrated. It supersedes
the proposed Beta–Binomial step-existence model in `2026-09-15-generative-model.md`.

**[Executed results and baseline comparison](2026-09-16-bayesian-process-v3-results.md):**
the pilot does not beat the saved one-pass LLM. It overestimates the step count
and underestimates decision time; the report includes sensitivity and limitations.

## Diagram and estimands

The alternate [TikZ package](figures/latex_plate_diagram_simplified/README.md)
contains an embeddable plate diagram, standalone PDF, and a write-up defining
every node and distinguishing target-model components from the implemented pilot.
The original diagram package is preserved.

The central latent object is a finite process graph: steps, identities, agency
assignments, precedence and rework. A case traverses a possible graph and realizes
elapsed times, payments, and work. Burden has **two sides**:

| Quantity | Interpretation | Pilot support |
|---|---|---|
| Elapsed days per step | A distribution of calendar waits, including queues | Fitted from typed claims |
| End-to-end days | Time to an identified decision; closeout separately | Simulated, with substantial scope/routing limitations |
| Applicant hands-on hours | Work performed by applicant/paid helpers | Separate likelihood/channel; no W1 cache observations |
| Agency hands-on hours | Staff labor, distinct from waiting | Separate likelihood/channel; no W1 cache observations |
| Fees | Paid transactions, not summed copies of fee mentions | Documented component only; unknown charges not invented |
| Agency task executions | Back-office and public-facing work events | Simulated separately from applicant activities |
| Agency count | Distinct sampled named organizations | Alias/catalog dependent; unresolved assignments separate |
| Encounters | Visits to counters, hearings, sites | Upper-count proxy unless shared encounter IDs are supplied |
| Disclosures, operating cost | Sensitive inputs, staffing dollars, standing overhead | Not yet estimated |

Neither agency elapsed time nor applicant elapsed time is a proxy for labor.
Standing obligations are distinct from per-case activity. Work-hour totals with
unmeasured work events are unknown. Money/hours/days are not aggregated into one
scalar without a specified valuation model.

## Implemented probability model

### Unknown step inventory and document detection

Let `N` be total steps, `K` represented steps, `z_r` a mention's step assignment,
and `z_r = 0` a spurious/out-of-scope claim. The default is a truncated
negative-binomial prior on `N` (mean 20, shape 2, maximum 100), **not** a CRP count
or a vote tally. These are assumptions, not values estimated using test truth.

Each step has a latent visibility stratum and a disclosure intensity
`lambda ~ Gamma(a, b)`. A read source family `d` has kind/visibility-dependent
exposure `q_d(v)`; mentions arise from a Poisson marked process with intensity
`lambda * q_d(v)`. Integrating the intensity gives, up to constants common to
all partitions:

```
L(cluster | v) = b^a Γ(a+n) / [Γ(a) (b + Σ_d q_d(v))^(a+n)]
                 × Π_mentions q_source(v)
q0 = Σ_v P(v) [b / (b + Σ_d q_d(v))]^a
P(N, partition | evidence) ∝ P(N) (N)_K q0^(N-K)
                            × Π_clusters L(cluster) × mark_likelihood
```

`(N)_K` is the falling factorial. `q0` is the prior-marginal probability that a
real step produces zero detected mentions in the acquired source families.
Visibility is integrated as a two-component mixture. Thus nonmentions have
different implications in staff procedures and public brochures.

Name marks use an integrated Dirichlet–multinomial bag-of-words model, with
an empirical corpus vocabulary/background. Agency marks use categorical
source-error likelihoods. A separate Poisson/background-language component
allows clutter. Explicitly ordered mentions in the same document cannot be
merged. Collapsed Gibbs samples partitions; `N | partition` is summed/sampled
explicitly, including undetected steps. This is genuinely probabilistic
assignment, not a lexical merge threshold, but the language model is still
simple and cannot resolve arbitrary semantic granularity.

**Important assumptions:** source accuracies/exposures are fixed, uncalibrated;
known source-family copies are deduplicated; unknown copying is not discovered.
The Poisson independence model within a source is an approximation for edited
prose. The acquired corpus is conditioned on; a retrieval-policy likelihood is
not implemented. Fully invisible steps remain prior-sensitive.

### Timing and fees conditional on a sampled partition

The timing grid carries log-median `mu` and case dispersion `sigma`. It uses
101 log-spaced median locations between 0.025 and 7,300 days, and six discrete
dispersion values. Boundary mass is reported. The common prior is deliberately
broad; **this pilot does not yet learn a cross-program duration hierarchy**.

- Individual waits use a log-normal observation model with case dispersion and
  additional reporting error.
- A reported sample median uses summary-statistic uncertainty. Where sample
  size is known, asymptotic log-median variance is `pi*sigma²/(2*n)` plus report
  error; an unknown sample size gets an explicit uncertainty floor.
- Ambiguous “typical/reported” estimates have a wider location likelihood.
- Literal ranges use interval probabilities, not a midpoint treated as exact.
- Zero-day reports are retained as rounded intervals `[0, 0.5]` days.
- Legal caps and service targets are retained but excluded from the duration fit.
- Business-day claims are excluded unless a calendar conversion is supplied;
  no automatic calendar/business-day equivalence is assumed.
- Process/segment summaries cannot update a single step's duration likelihood.
  They need a separate schedule-level likelihood, not a scope relabeling.
- A shared source offset is integrated by quadrature within a step. Identical
  timing claims from the same source are not counted repeatedly.

Agency/payer work-hours use **separate** likelihoods with explicit measurements.
Fee amounts have categorical posteriors over reported values. Step median
credible intervals and future-case prediction intervals are separate outputs.

This is a **cut posterior**: timing does not feed back into entity resolution.
Source reporting error and extractor error are not separately learned. Shared
source bias across different steps and joint case-selection correction are
extensions. The grid's intervals are conditional on these choices, not a
demonstration of calibration.

### Routing and burden

Claimed precedence is resolved against sampled step identities. A categorical
edge model, sampled with DAG-constrained Gibbs updates, allows contradictory
sources without introducing cycles into base precedence. Rework is separate;
its existence has an evidence likelihood but its trigger frequency is a prior
unless explicitly measured. Rework repeats the supported path, with a safety cap.

The scheduler handles parallel prerequisites with maximum completion time,
not summed medians. It charges flat fees once per transaction, permits per-visit
fees, and deduplicates encounters when IDs exist. Unknown encounter identity is
flagged as a proxy. Legacy extractions lack reliable applicability/outcome
fields, so standing/conditional classifications and inclusion probabilities
are transparent heuristic priors. A full mutually exclusive branch/denial/
abandonment model is **not** implemented.

Unobserved step count is inferred, but their placement and cost are unidentified.
The main burden forecast is therefore conditional on represented steps. It must
not be presented as a fully identified forecast of all real burden. Missing
precedence also makes the current timing forecast sensitive to implicit
parallelism; this is a limitation, not evidence of process efficiency.

## Commands and provenance

No new LLM calls, network access or additional dependencies are required:

```sh
python3 -m pipeline.procbench.run_bayes_synth \
  --out runs/bayes_v3_final --sweeps 800 --burn 300 --chains 4 --cases 60 --sensitivity
```

Inference reads `runs/incremental/extract_synth/index.json` and its ten cached
document extractions (89 candidate mentions). Rendered document front matter
supplies public provenance metadata only. **No hidden truth, generator specs,
ceilings, or saved solver answers enter inference.** The posterior is written
before the runner opens truth for evaluation. Ground truth is not used to tune
the default priors or choose among sensitivity variants (count means 10/20/40).

Outputs in the new run directory:

- `evidence.json`, with extraction/source hashes.
- `posterior.json`, `model.json`, `draws.json`, `case_draws.json`.
- `evaluation.json`, including count CRPS and interval diagnostics.
- `baseline_rescoring.json` and `rescored/`, preserving all historical runs.
- `sensitivity_count_10.json`, `sensitivity_count_40.json`, and `manifest.json`.

The eight saved oracle and three search runs are rescored, but **only W1/J1/S03
has cached document-level extraction suitable for this initial inference run**.
The LLM baseline and pilot see different representations: the legacy cache
omits process-level duration claims and case identities. This is a diagnostic
pilot, not an equal-information benchmark or a claim that Bayes beats an LLM.

## Scoring corrections

Scorer version 2 reads `process_timing.median_days` as well as legacy explicit
end-to-end fields, accepts typed `timing.value_days` where appropriate, excludes
caps/targets, and no longer substitutes a sum of step medians for process time.
It also fixes held-out-key leakage in the separate real-corpus global-median
baseline. Original saved score files are retained for provenance.

Across the existing saved synthetic predictions, corrected multiplicative
end-to-end error is **1.075×** for eight oracle runs and **1.321×** for three search
runs (formerly 1.545× and 2.387×). This says nothing by itself about calibration.
The two conditions have different task sets; their aggregate difference is not
a paired estimate of retrieval loss. The synthetic dashboard's end-to-end
metrics and explanation are refreshed, while its historical structural
alignments are retained. Rebuild those timing fields with:

```sh
python3 -m pipeline.procbench.refresh_synth_scores
```

## Validation and next gates

Unit tests cover timing schemas, target exclusion, zero waits, medians versus
individual cases, duplicate sources, count normalization, evidence order,
parallel schedules, rework, transaction/encounter deduplication, and distinct
agency/applicant labor channels. Incomplete work-hour totals remain null rather
than being summarized over a misleading zero-work subset. Conditional timing
means retain partially defined posterior draws. Basic multi-chain count diagnostics are not a
guarantee of graph-posterior convergence or statistical identification.

Before expanding the pilot, improve the extractor's process/segment scope,
operation-versus-condition granularity, case identities and agency aliases;
obtain independently audited error/disclosure estimates; compare identical
evidence streams and multiple worlds; then fit hierarchical timing and a proper
conditional route/outcome model. Do not tune against this single test program
and call the resulting accuracy a held-out result.

Background: [finite mixtures with an explicit count prior](https://arxiv.org/abs/1502.06241),
[imperfect detection](https://www.usgs.gov/publications/estimating-site-occupancy-rates-when-detection-probabilities-are-less-one),
and [posterior versus predictive uncertainty](https://mc-stan.org/docs/2_28/stan-users-guide/sampling-from-the-posterior-predictive-distribution.html).
These motivate pieces of the design; they do not supply calibration guarantees
for this composed model.
