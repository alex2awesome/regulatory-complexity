# Bayesian audit response and implementation status

2026-09-16. Implements the first tranche of the
[independent audit](2026-09-16-bayesian-overnight-audit.md), including its later
overspecification and refactor observations. This is not a new model generation,
new fit, or claim of Bayesian superiority. V6 remains the integration target.
No new LLM calls, posterior sampling, reserved-world reads, commits, or bulk moves
were performed in this tranche. W1 and historical experimental outputs are unchanged.

## Agreement and qualifications

The central diagnosis holds: the semantic interpreter was uncalibrated, the
compiler's zero coverage mixed configuration with model limitations, the evidence
does not identify most hierarchy components, and proliferating experiment drivers
did not converge on an end-to-end evaluation. Calibrate interpretation first,
consolidate one model, and validate transfer/count/labor/uncertainty on a genuinely
reserved, identifiable design.

Important qualifications:

- **Marginal contraction is not all information.** For N(0,1) coordinates,
  `1 - posterior variance` is fractional marginal variance contraction. Mean shifts,
  correlations and identified sums can still carry substantial information. It is
  parameterization-dependent, can be negative, and does not prove a derived agency
  cycle mean equals its prior. Do not automatically fix weak components at zero or
  at a calibrated point; marginalize them or propagate calibration uncertainty.
- **A local derivative is only a screen.** A prior-mean linearization can miss
  nonlinear information and thresholded repeat counts. V6's inverse-CDF repeat
  transform is discontinuous. A NUTS port needs a differentiable/marginalized target,
  not just a sampler swap, and must be benchmarked; seconds are not guaranteed.
  Joint case marginalization must preserve correlations among all reports/visits.
- **No calibration on reserved outcomes.** Re-measure on each world's designated
  calibration partition, freeze it, then open the separate evaluation partition.
  W1 is development data. The original frozen V4 reserved result was not tuned on
  its answer; it failed, and subsequent use of W1 is no longer held out.
- **The 90% rule is a measured routing heuristic**, not a guarantee of harmless
  errors. Error costs, uncertainty, candidate coverage and paired downstream timing/
  count results still matter. Repeated LLM votes are predictors, not independent
  truth labels. Estimate P(true interpretation | reported interpretation), not
  P(reported | true) used backwards. Keep an unknown/out-of-chart possibility.
- **100% retention is not 100% information.** Residual-only reports do not inform
  process parameters. Report this explicitly rather than calling retention success
  a full-source fit. No claim is silently deleted.
- V5 selection on these sources remains a largely prior-driven sensitivity; a
  favorable recovery experiment does not establish that the document data learn it.

## Completed repairs

### Extraction provenance

[audit_extraction_lineage.py](../pipeline/procbench/audit_extraction_lineage.py)
reconstructed all three programs. Downstream granularity manifests match the
imported first-response hashes, not the repaired second responses:

| Program | Used imported-first SHA-256 prefix | Unused repaired-final prefix |
|---|---|---|
| J1/S01 | `2ff34e39794c` | `bade86395b9f` |
| J1/S03 | `a9a06cf2f765` | `ad72bd1e60f8` |
| J2/S07 | `25da94d3420e` | `43480c42c784` |

The [retrospective lineage record](../runs/bayes_v6/audit_updates/extraction_lineage/lineage.json)
contains full hashes, original validation rejections and import notes. A prospectively
recorded attempt-selection rule and an identified original-validator snapshot are
missing; current revalidation cannot reconstruct them. Both attempts currently
validate. Methods commands and result disclosures now name the actual branch.

### Scoring, structural failures, and generator metadata

- Scorer **/4** rejects process-level statutory caps, targets and deadlines; reads
  explicit summary paths instead of dict-order-dependent arbitrary recursion; removes
  the dead median-sum helper. /2 repaired explicit timing, /3 added structural/count
  metrics, and /4 is this follow-up. Old score files retain their original versions.
- V6 validates operator syntax before sampling. An absent route event/repeat block
  uses a typed unavailable-quantity exception and contributes zero probability to
  that candidate, retaining the original residual mass. Other ValueErrors are not
  swallowed as if they were legitimate route alternatives.
- A non-fixed route indicator with no observed transitions is flagged as unverified,
  not assigned a reassuring R-hat of one. Fixed one-route models remain valid.
- New world metadata records generator/accounting versions. Current seed-1 defaults
  do not regenerate legacy W1. The explicit legacy-accounting knob and the need for
  historical source/specs for exact replay are documented; W1 was not modified.
- The unsubstantiated 11.3x speedup claim is withdrawn. The four unconverged
  interpretation fits (4/9/8/7 flags) are recorded in the V6 results document.

### Hypotheses import and compiler policy

The S07 contract overloaded reported visit coverage and aggregation. A single-cycle
range can apply separately to every observed round without becoming their sum.
The validator now permits that combination; known parent fields still cannot change.
The saved S01/S03/S07 responses validate unchanged, producing 35/43/26 hypothesis
rows. Imports record the changed contract, complete validator hashes and snapshots.
[Revalidated responses](../runs/bayes_v6/audit_updates/hypotheses/).

[compile_visit_durations.py](../pipeline/procbench/compile_visit_durations.py) now
accepts corpus-level sampling/calendar/rounding/event conventions and calibrated
candidate weights. It recognizes the full audit event vocabulary while distinguishing
implemented clocks from explicit policy aliases and residual-only meanings. It
does not automatically equate latest-recorded with final decision.

The [minimal development policy](../pipeline/procbench/policies/w1_development_compiler.json)
declares unselected sampling, 7/5 calendar conversion without holidays, reported-unit
rounding when unspecified, and a process-independent log-t residual. These are
declared sensitivity assumptions, not learned facts. No guessed hypothesis mixture
or event alias is supplied in this first corpus pass.

| Program | Eligible elapsed | Retained likelihoods | Informative | Residual-only |
|---|---:|---:|---:|---:|
| S01 | 44 | 44 | 4 | 40 |
| S03 | 51 | 51 | 0 | 51 |
| S07 | 51 | 51 | 0 | 51 |
| Total | 146 | 146 | 4 | 142 |

[Saved compilation](../runs/bayes_v6/audit_updates/compilation/). Pure residual
observations are explicitly `report_only`, not fictitious population medians or
new latent cases. Tests verify their likelihood is independent of all process and
source parameters. An invalid/unconvertible numeric report remains accounted for
without a fabricated likelihood; that case is separately reported, not hidden.

### Measured semantic-calibration interface

[semantic_calibration.py](../pipeline/procbench/semantic_calibration.py) accepts
verified labeled judgments with a pinned extractor/prompt, world, case/source group,
and fit/validation split. It rejects reserved rows, duplicate judgments, group leakage,
unverified truth links and cross-world reuse. It estimates smoothed categorical
P(true | reported, vote stratum), reports cell uncertainty and grouped validation
accuracy, and applies the approximate 90% top-reading rule. Unsupported labels retain
residual mass without renormalizing surviving operators. Mixture promotion is still
conditional on a paired downstream validation; no mixture is certified by this tool.
The first interface uses posterior-mean calibration weights: uncertainty is reported
but not yet jointly propagated through the burden posterior.

The compiler consumes the resulting calibration artifact, not raw truth rows or LLM
confidence. Above-threshold classes can use the validated top candidate; other
classes retain calibrated alternatives. Original source/audit fields stay intact.

[prepare_semantic_labels.py](../pipeline/procbench/prepare_semantic_labels.py)
prepared all 146 W1 claims with their generator specifications and render-log entries,
plus separate **source-only** packets. [Review queue](../runs/bayes_v6/audit_updates/semantic_labels/review.json).
**Verified labels: zero so far.** Legacy render logs are document-level, not exact
claim-span crosswalks. No automatic number match is asserted as gold, especially
where the renderer contradicts the generator. New top-reading outputs and checked
claim-to-report links are the next calibration work. No accuracy or learned W1
confusion matrix is claimed yet.

### Information and numerical diagnostics

The shared [information report](../pipeline/procbench/latent_gaussian.py) is attached
to new V4/V6 reports. It gives coordinate means/variances, unclipped contraction,
block summaries, and joint covariance directions. Blocks below 25% mean marginal
contraction are prior-sensitive and ineligible for separate effect headlines;
derived sums are not automatically suppressed by a coordinate threshold. Channels
without direct observations anywhere in the hierarchy are explicitly ineligible
for measured-resource headlines. Numerical convergence remains a separate gate.

The existing V6 runner has a saved-draw diagnostics mode; no extra fitting script or
new sampling was needed. It checked eight saved likelihoods against current code
before producing new, separate information artifacts:

- [Mixed fit](../runs/bayes_v6/audit_updates/identification/mixed/identification.json):
  302 coordinates, 199 below 10%; mean agency/task/operation/source contraction
  13.0% / 9.3% / 9.4% / 8.2%.
- [Timing-only fit](../runs/bayes_v6/audit_updates/identification/timing_only/identification.json):
  302 coordinates, 259 below 10%. Unobserved labor components have approximately
  zero contraction, with small positive/negative Monte Carlo variation.

Prospective V6 integration checks now use signed likelihood perturbations and
posterior-weight sensitivity (importance ESS fraction >= .99 and normalized-weight
total variation <= .025), while retaining the old absolute-difference statistic.
Up to roughly 256 chain-spanning states plus prediction-check states are inspected.
A constant log-likelihood offset does not change posterior weights. This is finite
state overlap, not MCMC ESS, an error certificate, or an independent replication.
Prediction precision remains separately checked. Old fits are not reclassified.

## Remaining work, in order

1. **Done:** the approved 324-file snapshot is commit `e581748`; excluded data
   remain local. The subsequent infrastructure work is a separate uncommitted diff.
2. Shared runner, serialization, interval scoring and initial manifest/test
   consolidation are implemented below. Finish remaining provenance/quote consumers;
   then
   reorganize model/evidence/infra/experiments/legacy/bench with compatibility shims.
   Keep saved import paths replayable. Separate discretion only after those tests.
3. Obtain source-only top readings, verify W1 claim labels, calibrate by ambiguity
   class and compare mixture/top-reading timing and counts. Enumerated step-merge
   inventories and org-chart categoricals are **not implemented yet**.
4. Reduce V6's inference dimension: omit unobserved resource channels from fitting,
   marginalize suitable case random effects without breaking shared-case evidence,
   and distinguish calibrated hierarchy priors from fixed nuisance point values.
   The updated audit correctly distinguishes synthetic W2 recovery/reading calibration
   from learning real agency variation: W2 cannot supply the latter. Evaluate the
   existing real-data prior harvest with explicit population/source compatibility;
   do not silently use synthetic hierarchy scales as empirical real-world priors.
   Report identifiable agency/task cells where their separate effects are confounded.
   These changes are **not implemented by merely adding the information report**.
5. Fold outcome/censoring and learned/calibrated scale handling into that one model.
   Keep selection as sensitivity. A differentiable sampler port must preserve the
   target, enumerate/marginalize repeats as needed, and show measured speed/accuracy.
6. Repair remaining generator actor disclosures and build an audited crossed-design
   W2 with labor truth, separate calibration and reserved partitions, and predeclared
   transfer/uncertainty/count/labor criteria. No new reserved world has been opened.
7. Establish durable run storage and a tracked small-results registry. The
   [archive policy](../runs/README.md) and [project conventions](../CLAUDE.md) are
   written; actual off-machine archiving is not done.

The first tranche's final full regression run passed **368 tests**, with one
pre-existing generator-test return-value warning.

## Post-snapshot infrastructure refactor

After approval to continue, commit `e581748` captured exactly the reviewed source
list. The first refactor introduces [infra](../pipeline/procbench/infra/) without
moving the model or changing historical module/CLI paths. The subsequent diff is
not committed yet. W1, historical runs, priors, likelihoods and independent audit
text are unchanged. No live LLM calls or new research fits were run; tiny, deliberately
unconverged sampler fixtures are exercised only inside temporary test directories.

Implemented:

- **One Codex transport:** all 11 process-evidence callers (including reconciliation,
  audits and the matched baseline) use `infra/codex_runner.py`. Existing prompt,
  model/reasoning defaults, schemas, domain validators and retry limits stay in
  their callers. Every attempt has its own isolated temporary directory and saved
  prompt, exact raw response, backend log, CLI version, hashes, timing and status.
  JSONL event auditing remains mandatory on the hypotheses path; a transport log
  alone is not a proof of source-only behavior. A failed/missing response can no
  longer reuse a preceding retry's file. Invalid JSON and partial failure output
  are retained. Offline hypotheses revalidation no longer invokes the CLI.
- **One serialization/hashing implementation:** callers import `infra/manifest.py`.
  The old `reconcile_evidence`, `run_hierarchical` and `run_bayes_synth` helper names
  remain compatibility exports. JSON serialization is checked before opening an
  existing output, so a NaN cannot truncate it. Extraction cache reuse now checks
  the saved evidence hash as well as the input signature, and unfinished extraction
  directories cannot be silently overwritten.
- **Versioned manifests for current workflows:** reconciliation/import, the nine
  source audits, matched baseline and V6 fit/extend/refine/diagnose use
  `procbench-run/1`. The common `provenance` record stores operation, start/completion
  time, seconds, config, seeds, direct input hashes, transitive source hashes and
  an explicit `hidden_truth_read` declaration. Legacy fields remain available;
  parent draw dependencies do not replace original evidence hashes used for matched
  comparisons. The truth flag is a caller declaration, not filesystem enforcement.
  Static relative imports are snapshotted without executing code; dynamic imports
  and non-code assets must be explicitly declared. Historical manifests are not
  rewritten, and remaining legacy/evaluation drivers are not all migrated to this
  lifecycle schema yet.
- **One interval-score formula:** current and historical timing/count evaluators
  delegate to `infra/scoring.py`, with the Gneiting–Raftery tail penalty `2/alpha`.
  Existing output field names, log/raw scales and estimands stay unchanged. Tests
  compare against the prior formulas, reject malformed intervals, and do not invent
  a full predictive distribution for the LLM baseline.
- **Offline test scaffolding:** `tests/conftest.py` supplies a fake backend and a
  small V6 fixture; reusable visit data move out of a test module into
  `tests/procbench_fixtures.py`. New tests cover cache/repair behavior, immutable
  attempts, timeouts, missing output, provenance, transitive frozen-source likelihood
  replay, baseline execution and a V6 fit → extension → diagnostics round trip.

Validation: **401 tests pass in 10.86 seconds**, with the same pre-existing warning,
using `python -m pytest tests benchmark/synth/generator/test_generator.py -q`.
Compilation and `git diff --check` also pass. These are software compatibility
checks, not improved Bayesian benchmark measurements.

Still pending: bulk package moves/unified experiment CLI, quote-check consolidation,
legacy lifecycle migration, generator-test relocation, discretion separation,
dimension reduction, verified semantic labels/calibration, and durable run archives.
The next model work should change one target under a saved-state regression check;
this infrastructure step does not resolve the model's information limits.

## 2026-09-18: omit unobserved independent labor channels in V6

The dimension-reduction work now implements one bounded part of item 4 above.
`Config.modeled_channels` declares the retained channel layout; the current runner
adds `--observed-channels-only` to retain elapsed clocks and directly observed
labor channels. An observed resource channel cannot be omitted. Independent
unobserved labor location, agency, task, operation, spread, source and case
coordinates are integrated out rather than sampled or fixed at a guessed value.
Their resource arrays remain unavailable and their burden summaries are omitted,
not reported as zero. Active-channel case effects are **not** marginalized yet.

Historical defaults retain all three channels. Comparing the default sampler
against the pre-change Git source (SHA-256
`2eabc5270334a98bdf8c26cc4ffa2c5f78f59178cc455c8415be05a483013c49`)
on the saved-seed test fixture produced bitwise-identical state, route and
likelihood arrays. Projected-state tests also preserve the retained likelihood
with one/two channels and enabled/disabled within-visit phases. Population-grid
columns are explicitly aligned in that identity test: changing production
dimension changes the finite Sobol grid, so integration precision must still be
checked for an actual fit.

The timing-only fixture reduces 48 coordinates to 18 (62.5%). This is a software
fixture measurement, not a W2 runtime or inference result. The full offline suite
passes **504 tests**, including fit/extend/diagnose and preflight with the new flag,
with the one existing generator-test return warning. W2 parsing is running; no
source-derived W2 V6 posterior has been fitted by this change. Remaining item-4
work includes active-case marginalization and identification-sensitive priors;
the full source-to-route/count/resource compiler remains unfinished.

## 2026-09-18: fresh-chain route support initialization

A two-route fixture exposed a seed-dependent startup failure: one structural
alternative could explain a measured review, while another omitted it. Seeds
selecting the omitted-step route stopped before sampling despite finite support
elsewhere. `bayes_trace_hierarchy.py` now enumerates each program's finite-support
alternatives conditional on the proposed continuous state, using the original
likelihood and declared route prior, only when a fresh chain's initial route has
nonfinite likelihood. Program-conditional likelihoods avoid a Cartesian product;
up to sixteen prior-state proposals are tried before a clear no-support failure.
This changes initialization, not the posterior target, observation inventory or
support of an incompatible route. Valid default initialization is unchanged.

Regression checks cover four formerly seed-sensitive starts, program IDs sharing
a prefix, a genuinely unsupported observation, and an invalid saved checkpoint
(which must fail rather than silently reset). The full offline suite passed
**511 tests** in 33.13 seconds with the existing generator-test return warning.
These are software checks, not convergence or W2 performance measurements.

## 2026-09-18: per-case paths within the integrated V6 hierarchy

Inventory hypotheses remain program-wide alternatives. Each inventory can now
contain explicit case paths with shared operation parameters and a separate
logistic-normal frequency prior. The likelihood sums over paths **after**
multiplying all reports from the same case. Known outcome/path labels condition
that case's mixture; selected anecdotes do not become prevalence counts.
Population summaries use the path weights, and explicitly conditional populations
can select paths. An absent clock on a positive-weight path is not silently
dropped. `--case-path-logit-sd` records the frequency-prior scale; input path weights
are declared assumptions, not calibrated LLM confidence.

The full offline suite passed **531 tests** (32.83 seconds, one existing warning).
The saved-seed default fixture reproduces the pre-change reference's states,
routes and likelihoods bit-for-bit; this is one fixture, not a universal target
proof. The [replay receipt](../runs/w2_v6_code_checks_20260918/default_case_path_replay.json)
records the source hashes. Tests cover same-case dependence, distinct outcomes,
conditional populations, weighted summaries, scalar/batched likelihood equality,
selection, sampling/reporting and unchanged legacy inventory semantics.

This does not implement withdrawal hazards, nested/interleaved repeats, finite-
cohort summary sampling, calibrated inventory/agency alternatives or the complete
source compiler. Active-case Gaussian effects remain sampled. The first accepted
W2 program, C29/S12, has 84 extracted measurements and 38 eligible elapsed claims;
its [initial compilation](../runs/w2_v6_diagnostic_compile_20260918/C29__S12_initial/compilation.json)
retains all 38 but has **zero informative** observations. The remaining boundaries
include first-visit population conditioning, alternative decision outcomes,
ambiguous operators, observation-window clocks and repeated-report dependence.
No prior-only fit is presented as W2 learning, and no W2 posterior has been fitted.

## 2026-09-18: first-visit populations and dependent report wording

Two compiler/model boundaries exposed by the accepted C29/S12 ledger are now
implemented in the same V6. A quoted `source_bindings` sidecar can explicitly
condition a population summary on a first visit and identify a first-present
alternative operation (for example, approval or denial). This is not a population
mean over every case, a sum of both outcomes, or implicit omission of missing
paths. Duration-dependent completion/recording selection remains unmodeled.

A quoted `report_groups` sidecar can combine repeated wording of one report or
disjunctive numerical wording. A disjunction contributes the probability of its
interval union, not a product of duplicate observations or a convex envelope
that fills gaps. A more precise repeated report may be the representative only
when its interval is contained in the other reports. All original measurements,
quotes, intervals and dispositions remain available. Different source/operator/
case contracts and conflicting reports are rejected rather than silently merged.

The compiler accepts `--source-bindings` and `--report-groups` and distinguishes
represented claim counts from likelihood-factor counts. For C29/S12, explicit
first-visit bindings make two of 38 elapsed claims informative. Six quoted report
pairs reduce 38 claims to 32 factors. Including the independently accepted
visit-hypotheses audit gives **16 informative claims in 13 informative factors**,
with 22 claims retained as 19 residual-only factors. The
[diagnostic compilation](../runs/w2_v6_diagnostic_compile_20260918/C29__S12_hypothesis_diagnostic/compilation.json)
uses an explicitly **uncalibrated** policy: 0.2 out-of-set mass, with remaining
mass equal by basis then reading. It is a coverage/mechanics diagnostic, not
measured semantic accuracy or a promoted inference policy. No gold values set
these weights. Calibrated weights and sensitivity checks remain required.

At this boundary **561 offline tests passed** in 36.30 seconds with the existing
generator-test warning. The saved-seed default fixture again reproduced the
pre-change reference's state, route and likelihood arrays bit-for-bit; the
[replay receipt](../runs/w2_v6_code_checks_20260918/default_report_binding_replay.json)
records exact hashes and settings. This does not establish convergence or
calibration. Conditional correction-only work, complete source-derived inventory/
agency alternatives, recording/withdrawal clocks and finite-cohort summaries
remain unfinished. No W2 posterior fit or matched LLM comparison has run.

## 2026-09-18: joint finite-cohort quantile likelihood in V6

V6 previously rejected any population summary with a supplied n. It now accepts
explicit `quantile_cohorts` for sample medians and p90s. These feed the same
agency/task/operation hierarchy and likelihood as individual reports; this is
not another architecture or a separately fitted posterior.

For a cohort of n IID draws from a declared modeled population, the required
uniform order statistics are integrated **jointly**. Given a previous rank j
and value u, the next rank k has the representation
`U_(k) = u + (1-u) * Beta(k-j, n-k+1)`. Transform these through the weighted
population inverse CDF, and apply the explicitly declared sample-quantile
interpolation to durations. Source offsets and reporting error act on those
sample summaries afterward. The implementation uses deterministic scrambled
Sobol integration and SciPy's inverse incomplete-beta function. The underlying
order-statistic construction is described in these
[CMU probability notes](https://www.cs.cmu.edu/afs/cs/academic/class/15750-s16/Handouts/orderstats.pdf);
the numerical APIs are documented by
[SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.betaincinv.html).

Each cohort contributes `sum_h prior(h) E[product_j P(report_j | sample_quantile_j, h)]`.
Thus a median and p90 from the same people are not independent cohort draws,
and a shared clock interpretation is weighted once, not once per statistic.
The explicit out-of-set interpretation remains a process-independent product
reference over the reported intervals. There are no n new sampled case effects.
The prior/source/report scales are not divided by sqrt(n).

The compiler's `--cohort-bindings` contract preserves source n, exact quoted
membership, quantile convention and explicit assumptions. Source evidence and
earlier audits remain unchanged. Conflicting clocks/interpretation priors must
be reconciled before grouping. Known overlap with an individual/rate cohort or
another separately supplied quantile cohort is rejected. Ordinary population
rows with n still fail instead of silently becoming plug-in statistics.

Limits are consequential: IID sampling within the specified population,
non-overlap with other evidence conditional on shared model parameters, and
conditional reporting-error independence are **assumptions**, not facts learned
from a denominator. The implementation does not handle finite-sample means,
overlapping stage cohorts with different clocks, duration-dependent completion
selection, or unknown quantile conventions. No such assumption has yet been
approved as a calibrated W2 inference policy. Observation-window conditioning
still cannot be replaced by simply labeling a cohort complete.

Tests compare the joint likelihood with exhaustive enumeration of small weighted
populations; check the uniform order-statistic covariance, even-n median,
linear versus inverse-CDF conventions, shared interpretation weights and source
bias; and exercise compiler-to-V6 sampling, conditional paths, preservation of n,
overlap rejection and precision/continuation guards. Both the population grid and
cohort grid must be refined for the numerical likelihood check. Prediction-only
refinement cannot change a cohort likelihood without refitting. A default-layout
saved-seed fixture still reproduces its historical reference's states, routes and
likelihoods bit-for-bit (one fixture with current imported helpers, not a universal
target proof or convergence result).

Separately, the accepted C44/S12 source-only hypotheses now compile under the
unchanged **uncalibrated diagnostic** policy to 44 retained elapsed claims,
32 with informative alternatives and 12 residual-only. This initial hypothesis
compilation does not yet group its repeated/disjunctive wording and must not be
fit as 44 independent reports. It contains no finite-cohort observations. No W2
posterior or matched LLM comparison is claimed by this implementation.

## 2026-09-19: count-only cases reach the existing V6 likelihood

The real-corpus audit found that `validate_counts` accepted a case only when its
ID appeared in a timing, labor or money measurement. This excluded applicants
whose only reported burden was returning, calling or submitting repeatedly.

`burden-count-evidence/2` adds explicit quote-supported case declarations. The
existing V1 schema and behavior are unchanged. `validate_case_registry` checks
program identity, unique nonempty IDs, descriptions and verbatim support;
undeclared count references still fail. `convert_counts_sidecar --case-registry`
can use a `burden-case-registry/1` artifact. The compiler's sampling-policy case
set includes these validated declarations. Count-only observations already fit
the V6 case representation, so the likelihood itself did not need changing.

A fixture with zero timing/money measurements compiles a count-only applicant
and obtains a finite V6 likelihood. This proves the connection works, not that
the real count interpretation or selection is identified. Source-reviewed DROS
case declarations restore eight claims (13 to 21), retaining all 82 source
claims or unresolved entries; unsupported transaction mergers remain unresolved.
See the [real-corpus continuation](2026-09-19-codex-parse-continuation.md).

All **863 offline tests pass**, with the existing generator return warning.
Multiple repeat blocks, partial-count likelihoods, temporal transport and the
remaining source-to-route reviews are separate unfinished work. There is no new
real-data posterior or Bayesian-versus-LLM performance result from this change.

## 2026-09-20: case effects integrated for guarded real report frames

The optional V6 runner path `--marginalize-conditional-cases` now integrates
independent case-duration effects instead of sampling them. It is restricted
to the existing single-operation conditional-frame contract: one observation
per case, no shared hierarchy/source effects, repeated reports or branching.
The ordinary V6 path remains unchanged and the guard rejects richer inputs.

The calculation retains the existing Student-t(4) reporting/contamination
likelihood and location/spread priors. A normal/Gamma representation integrates
the Gaussian case effect analytically and the report precision by deterministic
quadrature, leaving two sampled coordinates. Log-scale quadrature refinement
and independent adaptive integration check the likelihood numerically; exact
latent lognormal quantiles replace the earlier finite-QMC reporting quantiles.
This is the same marginal target, not a second scientific model or an assertion
that individual-case timings have been learned.

The seven prespecified real phone/interview successors use unchanged31/28 cases,
priors and seeds. All seven pass unchanged numerical gates, compared with three
of seven full-latent predecessors. Original failures remain preserved. Root ran
50 focused and249 adjacent tests, not a new full suite. Both the code review and
the later [independent seven-fit result review](../runs/three_family_20260920/calfresh_case_marginalization_v1/independent_results_adoption.md)
passed. See the [results and limits](2026-09-20-calfresh-case-marginalization-results.md).

This closes a sampler bottleneck, not source selection, ambiguous actor
inference, model adequacy or the administrative/forum joint posterior. Every
captured CalFresh thread has been reviewed, but supported evidence consumption
remains an explicit [separate completion requirement](2026-09-20-calfresh-forum-model-integration.md).
