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

1. Review the initial snapshot file list with Alex and obtain explicit commit
   approval. No staging or committing has happened. Preserve this pre-refactor state.
2. Consolidate shared runner, manifest, quote/scoring utilities and tests; then
   reorganize model/evidence/infra/experiments/legacy/bench with compatibility shims.
   Keep saved import paths replayable. Separate discretion only after those tests.
3. Obtain source-only top readings, verify W1 claim labels, calibrate by ambiguity
   class and compare mixture/top-reading timing and counts. Enumerated step-merge
   inventories and org-chart categoricals are **not implemented yet**.
4. Reduce V6's inference dimension: omit unobserved resource channels from fitting,
   marginalize suitable case random effects without breaking shared-case evidence,
   and distinguish calibrated hierarchy priors from fixed nuisance point values.
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

The first full regression run after the initial repairs passed 364 tests in about
10 seconds (one pre-existing generator-test return-value warning). Subsequent
information-report additions have their own focused regression checks; the final
full-suite result is recorded in the handoff, rather than inferred from unit coverage.
