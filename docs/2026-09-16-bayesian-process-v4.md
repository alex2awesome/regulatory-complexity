# Joint agency, task, case, and evidence model (v4)

This is the next Bayesian implementation, not a switch to an LLM point estimator.
The LLM interprets the documents; a versioned evidence contract, joint statistical
model, saved posterior draws, and diagnostics make the numerical inference auditable.
Historical v3 runs and their negative comparison are preserved.
The completed v4 reserved test also misses its median target despite numerical
convergence. This is a working research implementation, not a calibrated full-
burden estimator; [the results](2026-09-16-bayesian-process-v4-results.md) retain that failure.

## What changed

- `process-evidence/2` preserves step, segment, and total durations; native units;
  actual versus normative timing; stable case/source identities; actor roles;
  supporting verbatim quotes; and unresolved semantic interpretations.
- The backward-compatible `/3` extension adds quote-supported observation
  contexts: historical/hypothetical/current period, selected route, known outcome,
  executed segment versus alternative branches, and explicit clock-start milestones.
- Reconciliation reads only public documents in an isolated Codex working
  directory. It uses an explicit model and reasoning setting, schema-constrained
  output, quote/reference validation, and content-addressed caches. It does not
  get benchmark truth, prior solver answers, or agency speed parameters.
- Agency, task-type, program, and individual-activity effects are jointly learned.
  Sources share reporting offsets. Case reports share latent case durations.
- A total and a step breakdown from the same person are observations of the same
  latent case, **not independent realizations of the process**.
- Missing order creates multiple valid schedule completions. Initial decision
  always follows all applicable prerequisite operations. Skipping a conditional
  step preserves the transitive dependency through it. Supported parallelism is
  not overridden by an inferred ordering; contradictory mandatory relations fail
  validation rather than being silently ignored.
- Step-count uncertainty includes undocumented stages, with an explicitly
  sensitivity-tested geometric prior; it is not disguised as precisely learned
  coverage. Inventory/alias uncertainty from interpretation remains a limitation.

## Timing hierarchy

For represented activity `i`, agency/actor `a(i)`, task type `t(i)`, and program `p(i)`:

```
mu_i = m + alpha_a(i) + beta_t(i) + gamma_p(i) + delta_i
log D_ni = mu_i + common_case_effect_n + sigma * z_ni
```

`m` has a broad Normal prior on log days. Agency, task, and residual standard
deviations have half-Normal priors and are inferred, rather than plugged in from
the same observations. Program effects use a documented weak fixed scale when
multiple programs are fitted. Source offsets have a separate prior. Case-level
spread and shared case heterogeneity are not uncertainty about the population
median. Defaults are in `bayes_hierarchy.Config`, not selected using a gold score.

Individual reports observe their actual latent case. A process report observes
that case's scheduled path. Typical/median/p90/mean claims without case identity
observe the corresponding population summary, with sample-size uncertainty when
available and reporting uncertainty even when it is not. Fixed Sobol quadrature
approximates population summaries; increasing its size/changing its seed is a
required numerical sensitivity check, not additional observations.

Rounded/interval claims use a Student-t interval likelihood with an explicit
contamination component. Contradictory reports can be noisy, rather than forcing
impossible concurrency. Statutory caps and targets are retained but never fitted
as realized durations. Business-day intervals are conservatively converted using
an unknown start weekday and a five-day week; holidays remain unspecified.

Claims are conditioned on their actual scope. A clean-submittal cohort does not
observe the unconditional mixture of clean and problematic applications. A known
case's route/outcome constraints apply to all its same-case measurements, and
contradictory constraints raise an error. A timed enforcement segment is measured
when performed, even though it is not a prerequisite of the initial permit.
"One week after signoff" excludes the completed signoff operation. These boundaries
come from quoted evidence, not inferred benchmark outcomes. Explicitly historical
and hypothetical claims remain in the ledger but do not fit the static current
process. This is not a model of historical process change.

Within-operation clocks are not yet fully separated. The final joint audit
found a 20-minute appointment duration mapped to the same activity as the wait
to obtain that appointment. Its free-text interpretation preserves the distinction,
but the likelihood does not; the robust model flags it as incompatible. This is
a remaining representation/model defect, not evidence that the short report is
false. Component-aware elapsed/service clocks are required in the next iteration.

An agency report includes its posterior **equal-weight represented-task mean
elapsed duration** and its task-adjusted timing ratio. These are not interchangeable
with agency productivity, service time excluding queues, an actual workload-weighted
mean, or staff labor hours. Waiting days never become work hours.

## Inference and checks

All continuous coordinates have independent standard-Normal priors before
deterministic transformations. Blocked [elliptical slice sampling](https://proceedings.mlr.press/v9/murray10a.html)
updates their joint likelihood. Finite graph/count states use exact conditional
categorical updates. Centered/noncentered interweaving adds:

1. a Gaussian conditional step-mean proposal holding actual case durations fixed,
   with an MH correction for population-summary observations;
2. exact Gaussian attribution of fixed step means to agency/task/program effects;
3. centered half-Normal scale updates that keep realized effects fixed;
4. reversible whole-case swaps of unmeasured step durations to explore ambiguous
   decompositions, plus unit-Jacobian moves that redistribute a fixed sum between
   two operations;
5. a Gaussian-prior projection refresh along a common log-time/source-bias ridge,
   with a likelihood MH correction. This improves source/location mixing without
   tightening their priors. Tests check reversibility, Jacobians, and stationarity.

The attribution and scale updates must preserve all predictions. Tests verify
this and verify the joint prior is preserved without observations. The base
sampler is also checked against an analytically known conjugate posterior.
Rank-normalized split/folded R-hat and bulk/tail ESS are reported for step means,
agency effects, hyperparameters, source effects, process duration, and structure.
An unconverged fit is explicitly flagged, never presented as a validated posterior.
Cached likelihood calculations are regression-tested against an uncached reference.
Numerical scheduling drops transitive parents but retains the original edges;
nonnegative durations and zero-duration pass-through make the result identical.
An optional native scheduling kernel uses installed Numba, with exact comparison
against the NumPy path, no fast-math, and no extra parallel reductions. The statistical
runner remains usable without it; new manifests record the backend and kernel source.

The initial-case clock selects one terminal decision when the interpretation retains
multiple approval/denial operations. Unknown population outcome proportions have an
exchangeable logistic-Normal prior (binary logit SD 1.5), not a fixed 50/50 split or
a measured approval rate. An explicitly observed outcome conditions its case or
selected cohort, without counting biased anecdotes as a representative outcome
sample. Unknown process-start wording is an equal mixture of preparation-start
and submission-start interpretations. Core closeout is reported separately; conditional
withdrawal/correction paths are not automatically added to every completed case.

Agency-work totals sum agency work, not applicant work. A directly reported agency-work
amount attached to an applicant-owned operation is retained but marked unattributed
to a resolved agency. Neither an hourly rate nor FTE alone supplies actual work-hours.
Elapsed-chain convergence does not imply work-hour convergence. `check_effort`
audits the saved work-hour draws separately, including hyperparameters, agency and
step effects, and expected per-case hours. A cost-study's typical-hours estimate
does not precisely identify arithmetic mean workload or per-agency allocations.

## Experiment protocol

J1/S03 is **development data**: its earlier mistakes and gold outcome are already
known. Independent generated-data tests check agency propagation, removing agency/task pooling,
case/total dependence, and computational calibration. J1/S01 adds another program
for joint pooling. J2/S07 is reserved for evaluation after development decisions
and inference inputs are frozen. No inference code imports benchmark truth.

Save posterior artifacts before evaluation. Compare prior/hidden-stage sensitivity,
process-claim ablation, quadrature sensitivity, and fresh-chain stability. Do not
select a prior because it moves J1/S03 closer to its known 74-day answer. A stronger
extractor and different documents are information changes, not evidence that a
Bayesian estimator intrinsically beats the previous LLM baseline.

The `--no-hierarchy` control retains a global location and activity residuals; it is
**global-only pooling**, not fully independent per-task estimation. The reserved
evaluation choices are recorded in [the frozen protocol](2026-09-16-bayesian-process-v4-protocol.md).
Three fresh direct LLM estimations receive the identical canonical ledgers for each
fit grouping, without Bayesian outputs or gold answers. Fresh interpretation variance,
point-estimation variance, and Monte Carlo error are different quantities.

## Running

**Retrospective lineage correction (2026-09-16 audit):** the published fits and
matched LLM controls descend from `extraction/*_first_validated/evidence.json`.
Those files import the initially rejected `attempt_0.json` after validator
changes; `extraction/*/evidence.json` instead contains the repaired second
response and has a different hash. The earlier command examples named the wrong
branch. The original rejection messages, both response hashes, import notes and
downstream hash checks are now in the [lineage audit](../runs/bayes_v6/audit_updates/extraction_lineage/lineage.json).
There was no prospectively recorded attempt-selection rule or identified frozen
original validator. Current validation does not repair that historical omission.
No existing ledgers, posterior files or comparison scores were replaced.

```sh
python -m pip install -r requirements-bayes.txt
python -m pipeline.procbench.reconcile_evidence \
  --index runs/incremental/extract_synth/index.json \
  --out runs/bayes_v4/extraction/J1__S03
python -m pipeline.procbench.validate_hierarchy --out runs/bayes_v4/validation/pooling
python -m pipeline.procbench.calibrate_hierarchy --out runs/bayes_v4/validation/sbc
```

The final experiments use source-only operation, context, and clock audits before
fitting. Each command preserves old output directories; choose fresh names when rerunning:

```sh
python -m pipeline.procbench.audit_granularity \
  --evidence runs/bayes_v4/extraction/J1__S03_first_validated/evidence.json \
  --inputs runs/bayes_v4/extraction/J1__S03_first_validated/inputs.json \
  --out runs/bayes_v4/granularity/J1__S03
python -m pipeline.procbench.audit_context \
  --evidence runs/bayes_v4/granularity/J1__S03/evidence.json \
  --inputs runs/bayes_v4/extraction/J1__S03_first_validated/inputs.json \
  --out runs/bayes_v4/context/J1__S03
python -m pipeline.procbench.audit_clocks \
  --evidence runs/bayes_v4/context/J1__S03/evidence.json \
  --inputs runs/bayes_v4/extraction/J1__S03_first_validated/inputs.json \
  --out runs/bayes_v4/clocks/J1__S03
python -m pipeline.procbench.run_hierarchical \
  --evidence runs/bayes_v4/clocks/J1__S03/evidence.json \
  --out runs/bayes_v4/main --warmup 2500 --draws 12000 --thin 1 --workers 4
python -m pipeline.procbench.sensitivity_hierarchy --run runs/bayes_v4/main \
  --out runs/bayes_v4/main_sensitivity --quadrature
python -m pipeline.procbench.check_hierarchy --run runs/bayes_v4/main \
  --out runs/bayes_v4/main_checks
```

Sensitivity reweighting is explicitly labeled, reports overlap/weight ESS and
autocorrelation limitations, and is not a replacement for refitting when overlap
is poor. Summaries can be rebuilt from saved draws into a new directory with
`summarize_hierarchical`; it verifies saved likelihood values before proceeding.

Extraction requires the authenticated Codex subscription. Cached statistical runs
are offline. Inputs, schema, prompt, model/settings, version information, seeds,
code snapshots, hashes, diagnostics, and draws are retained. A cached run is
reproducible; fresh LLM interpretations are not claimed to be bit-identical.
New runs also save `elapsed_posterior.json` before the separate work-hour stage,
with `work_progress.jsonl` for that stage; `posterior.json` remains the completed
composite artifact. Work-hour convergence is audited separately with
`python -m pipeline.procbench.check_effort --run <fit> --out <fresh-check-directory>`.
Completed measurements and failed diagnostics are recorded in
[the experiment report](2026-09-16-bayesian-process-v4-results.md).

## Boundaries still requiring evidence

Agency and task effects need **multiple tasks**, not simply many reports of one
task. Number and duration of undisclosed stages remain partly confounded. Forum
case selection, unknown copying, extractor error, and condition prevalence are
not identified from a small convenience corpus. Separate payer-work and agency-work
hierarchies run when numerical work-hour claims exist; otherwise labor is explicitly
unknown. Fees and staffing claims remain in the ledger, not a fitted workload model.
Abandonment, historical process transitions, and detailed rework routes are not yet
fitted. Counts describe distinct modeled operations, not identified repeat visits;
reported operation durations may already include rework. Sensitivity and transparent
uncertainty are necessary even when the sampler converges.

Sharing a latent case prevents a total and its components from becoming different
process realizations. It does not fully model every dependency in reporting:
an explicitly arithmetic-derived total should not be counted as another independent
noisy measurement of those same component reports. The current contract deduplicates
known repeated observations, but has no general provenance graph for derived numbers.
