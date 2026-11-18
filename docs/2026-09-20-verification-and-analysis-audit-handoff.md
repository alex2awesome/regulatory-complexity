# Verification and analysis: audit handoff for Claude

Snapshot: **2026-09-20, 17:58 UTC / 10:58 a.m. PDT**. Prepared at Alex's request.
This is a map of checks, evidence, remaining work and limitations, not a new
verification pass or a claim that the three corpora are finished.

Update at **18:02 UTC / 11:02 a.m. PDT**: the first expanded CalFresh analysis
has arrived; its failed overall gate and passing bin-specific checks are
distinguished below. No extension has been launched.

## 1. What we are doing, and why verification has taken so long

The objective is to turn the captured real **solar, concealed-carry (CCW), and
CalFresh** material into source-faithful burden measurements and qualified V6
analyses. [Real corpora now come first](2026-09-20-real-corpora-first-work-order.md).
Synthetic generation, rendering and synthetic-only development are deferred.
The [full study plan](2026-09-20-three-statute-parse-verify-analysis-plan.md)
still defines the wider scope; older synthetic next steps do not override this
priority change.

We have been using “verification” for several different jobs. Copying a number
correctly is not the same as knowing what it measures, and neither establishes
that a fitted model is correct. The expensive part has been reconstructing
meaning: whose case, which application attempt, what event starts/stops a clock,
whether a scheduled event happened, and what a spreadsheet denominator means.
The [independent audit](2026-09-20-audit-of-codex-work.md) found misleading labels
in 12 of 60 sampled measurements despite no wrong numeric values. That motivates
semantic review, but is not a fresh error-rate estimate for the corrected data.

There has also been too much serial packet/seal/review bookkeeping. Some of it
caught real errors; some delayed the scientific loop. The current rule is:
**fit accepted batches while the remaining sources are being parsed**. A hash
repair should not trigger a fresh scientific review of unchanged values. An
unresolved source should remain visible without blocking unrelated accepted
evidence. Full-corpus completion and a bounded valid analysis are separate goals.

## 2. Exactly what each check does

These are distinct statuses, not one blanket “verified” flag. The scope of each
actual pass is in its packet; not every historical ledger has passed all stages.

| Stage | Actual check | What it establishes / does not establish |
|---|---|---|
| A. Coverage and identity | Enumerate frozen files, logical sources, physical aliases, missing attachments, duplicate captures, relevance decisions and unreadable/held sources. Account for every selected author/county/authority, including zero useful claims. | Establishes a denominator for the captured inventory. File presence or metadata screening does **not** establish a source was fully read or that the live web is exhaustively covered. |
| B. Source grounding | Hash source bytes; re-slice quoted spans using declared normalization; replay worksheet coordinates from native XLSX; check source/post IDs, arithmetic and units. For reviewed CCW packets, compare companion text, Markdown and HTML representations. | Establishes that a value/quote is actually in the bound source. Three representations of one post are not three independent witnesses, and a quote can still be misinterpreted. |
| C. Semantic review | Read the relevant surrounding history/definitions. Label population, authority, era, application/renewal, episode, origin, endpoint, statistic, day basis and precision. Separate observed events from scheduled events or “by this post” bounds; separate elapsed wait from labor/service time. | Establishes a defensible reading, with explicit ambiguity. Does not make an ambiguous date exact, convert an anecdote into a random sample, or resolve unobserved process steps. |
| D. Dependence and effective corrections | Reconcile repeated posts/aliases/cases; exclude duplicate totals and subclocks as independent evidence. Materialize itemized corrections with input hashes. Retain admitted, held, residual-only, duplicate and out-of-scope dispositions. | Establishes which version and rows enter an analysis. A sidecar sitting on disk is **not** proof that a compiler or fit consumed it. A corrected descriptive packet may still not be model input. |
| E. Source-to-likelihood mapping | Bind reviewed evidence to explicit operators/cohorts. Check units, histogram edges/counts, what n counts, clock boundaries, selection assumptions and factor multiplicity. Independently recompute simple likelihoods where possible. | Establishes that the code receives the intended quantities. A finite likelihood is only a construction check, not an adequate model, calibrated uncertainty or identified hierarchy. |
| F. Frozen run and numerical checks | Save exact inputs, imported source snapshot, effective config, seeds and sensitivity conditions. Run independent MCMC chains; check convergence/effective sample sizes, numerical approximation error, and diagnostics for the actual reported transformations. | Establishes whether the numerical approximation is usable under that model. Exit code 0 or an existing manifest is not a passing fit. Analytic integration eliminates a grid approximation, not modeling assumptions. |
| G. Adequacy and claims | Compare source counts/values with posterior predictions; show all prespecified sensitivities and failures; audit confounding and prior dependence. Then make same-information baseline and genuinely held-out comparisons where possible. | In-sample predictive agreement is not held-out validation, synthetic recovery, causal agency attribution or proof of superiority over an LLM. This stage is still incomplete for the expanded real study. |

The reviewer should check the **claimed scope**, not assume “independent review”
means a new line-by-line reading of all documents. For example, the first96 CCW
review loaded all bound histories but semantically screened candidates and
endpoint-bearing contexts, not every unrelated forum sentence.

## 3. Concrete errors these checks caught

- **Solar denominator:** joined installation counts were not the sample size
  behind an AHJ timing median. All 401 current timing sample sizes remain unknown.
- **CalFresh zero:** the reporting instructions allow zero for nothing to report
  and for unavailable/untracked activity. The export lacks county comments that
  would resolve this. Twelve zero-affected counties remain outside the primary
  likelihood; a separate literal-zero sensitivity is not a semantic repair.
- **CCW endpoint:** a ready-for-pickup notice, a future appointment, an issuance
  date and physical possession are different endpoints. A post date can be only
  an upper bound on when an event occurred.
- **CCW burden label:** one “2.5 weeks” interval includes a week of applicant
  unavailability. It is elapsed waiting, not 2.5 weeks of agency service effort.
- **CCW denominator:** eight exact-day completed histories were supported, but
  nine additional completed same-estimand histories had coarse/conflicting
  clocks. A successor now exposes those holds instead of burying them in a
  generic exclusion bucket. No durations were invented to include them.
- **Solar artifact integrity:** a validator rewrote the very receipt whose hash
  its manifest checked. The additive closure fixes that self-dependency without
  changing data or erasing the failed original manifest.

## 4. Current accepted inputs, runs and audit entry points

All paths below are relative to the repository root; links resolve on the shared
disk. Most `runs/` files are gitignored. A source commit is **not** their backup;
see the [archive policy](../runs/README.md). Do not rebuild packets in place,
overwrite failed fits, restart an existing run, stage files or delete originals
as part of an audit.

### CalFresh: all-county source accounting; four-condition expanded fit

- Source packet: [calfresh_cf296_all_county_july2025_admission_v1](../runs/three_family_20260920/calfresh_cf296_all_county_july2025_admission_v1/README.md).
- Independent source/operator review: [report](../runs/three_family_20260920/calfresh_all_county_admission_review_v1/report.md),
  [native-cell replay](../runs/three_family_20260920/calfresh_all_county_admission_review_v1/cell_replay.csv),
  [manifest](../runs/three_family_20260920/calfresh_all_county_admission_review_v1/manifest.json).
  It independently reads original XLSX ZIP/XML: 236 cells, 58 counties plus the
  dependent statewide row; the latter is excluded from the likelihood.
- Frozen run protocol: [README](../runs/three_family_20260920/calfresh_all_county_fit_plan_v1/README.md),
  [plan.json](../runs/three_family_20260920/calfresh_all_county_fit_plan_v1/plan.json),
  [launcher](../runs/three_family_20260920/calfresh_all_county_fit_plan_v1/prepare_and_run.py).
  Its `conditions` entries contain exact argv, config, input hashes and outputs.
- Fit outputs: `runs/three_family_20260920/calfresh_all_county_fits_v1/<condition>/`.
  Inspect `manifest.json`, `data.json`, `source/`, `draws.npz`, `posterior.json`,
  `run_progress.jsonl` and `chain_*.progress.jsonl` together.
- Live sweep receipt: [fit_progress.json](../runs/three_family_20260920/calfresh_all_county_fit_plan_v1/fit_progress.json).
  **At this snapshot, `positive46_base` finished at 17:57:44 UTC but failed the
  runner's numerical gate (29 flagged diagnostics).** Its successful process
  exit is not a scientific pass. No continuation has been launched. Subsequent
  conditions are queued; tighter pooling is now running.
- New analysis: [county results and gates](../runs/three_family_20260920/calfresh_all_county_analysis_v1/positive46_base/county_results.json),
  [independent likelihood replay](../runs/three_family_20260920/calfresh_all_county_analysis_v1/positive46_base/independent_likelihood_check.json),
  [predictive check](../runs/three_family_20260920/calfresh_all_county_analysis_v1/positive46_base/model_adequacy.json),
  [analysis manifest](../runs/three_family_20260920/calfresh_all_county_analysis_v1/positive46_base/analysis_manifest.json).
  All138 bin-probability diagnostics pass their frozen thresholds, while the
  shared-spread coordinate has R-hat1.027 and bulk ESS142. The six-state
  independent likelihood replay matches exactly at saved precision. Observed
  counts fall within135/138 marginal90% predictive intervals. These are
  diagnostics of an overall **unusable initial fit**, not released estimates
  or a validation win. Root checked these saved reports for this handoff; it
  has not independently rerun the new analysis program.

Primary data: 46 positive-bin counties, 59,036 recorded categorized reports.
All58 accounting totals 59,634. The population is recorded expedited-entitled
applications assigned to July2025 when disposed; the clock is application to
benefits issued, in calendar days. Disposition determines the reporting cohort,
not the clock endpoint. Counts define n; n does not establish complete reporting.

The four conditions are `positive46_base`, `positive46_tighter_pool`,
`positive46_fixed_spread`, and `rz_literal58_base`. The last is sensitivity only.
Report source counts/fractions, county bin probabilities and predictive counts;
not statewide rankings, precise within-bin times, agency efficiency or labor.
The positive-cell filter is outcome-visible and not representative.

### Solar: 401-authority permit-phase panel; five-condition expanded fit

- Source packet: [solar_full_panel_admission_v1](../runs/three_family_20260920/solar_full_panel_admission_v1/README.md).
- Independent review: [README](../runs/three_family_20260920/solar_full_panel_admission_review_v1/README.md),
  [checks](../runs/three_family_20260920/solar_full_panel_admission_review_v1/checks.json).
  It reconstructs 9,586 distinct timing cells from the original long CSV and
  checks the target stratum against that reconstruction, not just the builder.
- Required additive integrity repair: [closure v2](../runs/three_family_20260920/solar_full_panel_admission_closure_v2/README.md).
  Its 441 bindings replayed; the original failed manifest remains. The older
  reviews say “no fit authorization” because they were input checks; the later
  frozen fit plan records the subsequent adoption for bounded fitting.
- Frozen protocol: [README](../runs/three_family_20260920/solar_full_panel_fit_plan_v1/README.md),
  [plan.json](../runs/three_family_20260920/solar_full_panel_fit_plan_v1/plan.json),
  [manifest](../runs/three_family_20260920/solar_full_panel_fit_plan_v1/manifest.json).
- Fit outputs: `runs/three_family_20260920/solar_full_panel_fits_v1/<condition>/`.
  **Base is sampling** at this snapshot; runner PID80441 was checked live.
  Progress is in `base/run_progress.jsonl` and `base/chain_*.progress.jsonl`;
  launcher receipts/logs are in `solar_full_panel_fit_plan_v1/`.

Target: 2022, PV-only, 0–10kW, permit submission through final approval, business
days, including resubmission. Of 440 panel AHJs, 401 have identified target
cells, one name-only target is held, and 38 lack the target cell. This is not
401 whole solar-installation clocks, nor a complete statewide sample.

Five conditions: base; unknown-n reporting floors .25 and .75; narrower
agency/operation pooling scales; and changing the 29 same-day intervals from
[0,.5] to [0,1]. These intervals are declared assumptions, not source confidence
intervals or verified rounding rules. Report transformed AHJ phase medians and
finite-panel contrasts only. Agency, operation, task and source offsets cannot
be separately identified in this design; case spread is inactive for medians.
The 806 allocated coordinates are not 806 learned scientific effects.

### CCW: reviewed reported histories; continued fixed-order parsing

- Effective first96 descriptive packet: [v2 README](../runs/three_family_20260920/ccw_first96_whole_clock_descriptive_v2/README.md),
  [dispositions](../runs/three_family_20260920/ccw_first96_whole_clock_descriptive_v2/candidate_dispositions.json),
  [manifest](../runs/three_family_20260920/ccw_first96_whole_clock_descriptive_v2/manifest.json).
- Independent review that required that successor: [report](../runs/three_family_20260920/ccw_first96_whole_clock_review_v1/report.md),
  [candidate audit](../runs/three_family_20260920/ccw_first96_whole_clock_review_v1/candidate_audit.json).
- Original source slices and unchanged exact-day table: [v1 packet](../runs/three_family_20260920/ccw_first96_whole_clock_descriptive_v1/README.md).
- Subsequent ranks97–108: [batch09](../runs/three_family_20260920/ccw_324060_clock_binding_pilot_batch09/README.md),
  [two-label additive correction](../runs/three_family_20260920/ccw_324060_clock_binding_pilot_batch09_erratum_v1/README.md).
  That correction is written; its existence alone is not root adoption or fit
  consumption.
- Arrival during handoff preparation: [batch10, ranks109–120](../runs/three_family_20260920/ccw_324060_clock_binding_pilot_batch10/README.md)
  is now author-sealed, reporting58 candidates and zero fit-ready rows. Root has
  not reviewed it; do not treat this arrival as semantic adoption. Its reported
  next cursor is rank121 (`jdl`). The author also completed the
  [ARFrog neutral-approval label erratum](../runs/three_family_20260920/ccw_324060_clock_binding_pilot_batch06_approval_label_erratum_v1/README.md),
  likewise not independently consumed in this documentation-only handoff.

The first96 packet accounts for 300 candidates. Eight exact-day initial
submission-to-physical-receipt episodes are supported: seven start in2022,
158–367 calendar days, finite-report median297; one starts in2023, 498days,
kept separate. Nine additional completed same-estimand episodes remain held
for unresolved clocks. These are forum histories selected by reporting and
clarity, not estimates of the county applicant population. The first96
successor is **descriptive, not a new model input or whole-process fit**.
Earlier four-case training-phase fits are a different estimand and remain
documented in the [bounded pilot results](2026-09-20-calfresh-and-ccw-pilots.md).

## 5. Computation and post-fit verification plan

Both expanded studies use the existing integrated V6, elapsed-only,
`analytic_single_phase` likelihood and `operation_centered` transition.
There is **MCMC sampling**: four independent chains, 1,000 warmup iterations
and 2,000 retained draws per chain initially. Analytic single-phase integration
integrates the stipulated lognormal phase distribution; it does not eliminate
posterior sampling. CalFresh uses four CPU workers, Solar three, locally.

For each finished condition, in order:

1. Reconcile the actual input/config/source hashes to its frozen plan and saved
   run; verify completed outputs rather than relying on a running-state claim.
2. Inspect chain convergence and diagnostics for the reported quantities, not
   just raw latent coordinates. CalFresh's frozen bin-probability gates are
   R-hat ≤1.01, bulk ESS ≥400 and tail ESS ≥200, **and** the runner's numerical
   gate must pass. Solar also needs derived phase/contrast diagnostics; do not
   imply a numeric threshold is frozen in its plan when it is not listed there.
3. For CalFresh, independently replay six chain-spanning states with normal-CDF
   bin probabilities and normalized multinomial likelihood, tolerance1e-8.
   A grid-size equality in analytic mode is not this independent formula check.
4. Produce direct-source tables, posterior summaries and in-sample predictive
   checks. CalFresh prespecifies seed2026092097 and marginal90% predictive bin
   count intervals, not simultaneous coverage. Distinguish a converged but
   inadequate model from an unconverged numerical approximation.
5. Show every prespecified sensitivity, including failures. Both plans permit
   at most one separately recorded +4,000-draw-per-chain continuation for a
   numerical failure, using the same target and fresh RNG. Review initial
   diagnostics before authorizing it; no automatic repeated extension or
   post-fit winner selection. No such expanded-run extension is launched yet.

These current expansions are exploratory: small pilots and source values had
already been examined. Source-type reporting bias, precision, contamination and
selection are distinct mechanisms. The machinery is not empirical calibration:
bounded real solar/CalFresh overlap reviews found **zero eligible matched
comparisons**. No real-source trust ranking or calibrated bias claim follows.
See the [source/cohort handoff](2026-09-20-source-precision-and-cohort-handoff.md).

## 6. Remaining work and completion criteria

1. **Now:** finish/diagnose the already-running expanded conditions, release
   qualified direct-source results without waiting for complete corpus review,
   and continue CCW fixed-order episode reconciliation concurrently.
2. **Real evidence:** finish relevant unread text, captured threads, workbook
   definitions and era/identity holds. Expand other phases/months only when their
   semantics support it. Complete requirement/actor/route/fee inventories;
   timing-only fits do not complete the burden study. Do not infer missing labor
   hours, treat checklist headings as realized steps, or silently zero missing
   fees. Preserve all unresolved sources and their reasons.
3. **Real evaluation:** freeze feasible predictive splits before using their
   labels; compare source-only and LLM baselines using the same documents,
   clock, population and information budget. Measure repeated-run variation
   under fixed inputs. Do not score an in-sample histogram fit as a win over its
   own source counts. No held-out comparison or LLM superiority is complete yet.
4. **Synthesis:** one results/coverage table per family, each linked from source
   to effective evidence to run and limitations; identify learned quantities
   versus prior/confounded quantities. A full-source claim requires every
   relevant readable frozen source accounted for, not every claim fit-ready.
5. **Later:** reconsider synthetic known-truth recovery after real deliverables;
   preserve interrupted synthetic work without presenting it as accepted.

The earlier [schedule](2026-09-20-real-corpora-first-work-order.md) estimated
24–48 hours for first consolidated real results and 3–6 days for complete
relevant readable-source coverage. Those remain estimates, not promises. The
CalFresh base took about9.6minutes through report writing but failed numerics;
the Solar worker currently estimates roughly2–2.5hours for its initial base
under concurrent load, with four conditions following. The five-condition Solar
sweep and any bounded continuation can therefore outlast the earlier6–12hour
initial-fit window. Re-estimate from recorded progress, not a generic assertion
that all models fit in minutes. There is no measured wall-time breakdown proving
how much of last night was parsing versus review versus sampling.

## 7. Suggested audit order and code map

Please prioritize **semantic validity and useful conclusions over redoing every
hash check**. Read the packets above, spot-check original sources, and then:

- Challenge the CCW exact-origin requirement: does it discard useful uncertain
  whole-process reports that could enter a declared interval/mixture model?
  Conversely, check we have not turned contextually inferred dates into facts.
- Challenge the CalFresh positive-only cohort and literal-zero sensitivity:
  neither fixes incomplete reporting or establishes statewide representativeness.
- Challenge Solar's confounded hierarchy and unknown-n priors. Is the expanded
  model adding anything beyond transparent source medians plus uncertainty?
- Trace corrections into the **actual** effective object or fit data. Historical
  sidecars, descriptive successors and current model inputs are different things.
- Check current numerical failures and every sensitivity before trusting a
  point estimate; identify unused checks/packets that can be retired from the
  critical path. Do not erase their historical records.

Implementation entry points (the saved run's `source/` is authoritative for
reproducing that run if working-tree code changes):

- [Inventory](../pipeline/procbench/inventory_three_family_sources.py),
  [coverage closeout](2026-09-20-three-family-source-census-closeout.md).
- [Effective corrections](../pipeline/procbench/effective_evidence.py),
  [duration/cohort compiler](../pipeline/procbench/compile_visit_durations.py).
- [V6 model](../pipeline/procbench/bayes_trace_hierarchy.py),
  [runner](../pipeline/procbench/run_visit_hierarchy.py),
  [histograms](../pipeline/procbench/cohort_histograms.py),
  [conditional case frames](../pipeline/procbench/conditional_case_frames.py).
- [Source comparisons](../pipeline/procbench/source_comparisons.py),
  [precision](../pipeline/procbench/source_precision.py),
  [offset hierarchy](../pipeline/procbench/source_offset_hierarchy.py).
- [Progress narrative](2026-09-20-three-family-execution-progress.md),
  [machine status](../runs/three_family_20260920/EXECUTION_STATUS.json).
  These contain historical checkpoints; actual run files outrank stale prose.

Read-only examples, from the repository root, using the Conda `python`:

```sh
python runs/three_family_20260920/solar_full_panel_admission_closure_v2/replay_closure.py --check-receipt
jq '{numerically_usable, posterior_converged, flagged: (.diagnostics_flagged | length)}' runs/three_family_20260920/calfresh_all_county_fits_v1/positive46_base/posterior.json
jq . runs/three_family_20260920/calfresh_all_county_fit_plan_v1/fit_progress.json
tail -n 5 runs/three_family_20260920/solar_full_panel_fits_v1/base/run_progress.jsonl
```

Do not rerun a packet's builder/validator before checking whether it overwrites
its own outputs (the Solar v1 example did). Write independent audit results to
a new location. A regression test is a code check, not semantic verification;
if needed, the scoped command is `python -m pytest tests
benchmark/synth/generator/test_generator.py -q`. No fresh full suite was run
for this documentation handoff. New audit findings should be additive, itemized
and source-bound; they should not rewrite the earlier independent audit.
