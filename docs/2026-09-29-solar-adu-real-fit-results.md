# Solar and ADU: September 29 real-data fit results

Work is ongoing. This is the first completed Solar timing tranche, not the
completed parsing handoff or a full statutory-process recovery result.
Protocol: [real-data fits](2026-09-29-solar-adu-real-fit-protocol.md).
Reading denominators: [execution record](2026-09-29-solar-adu-codex-execution.md).

**ADU input correction completed:** the initial pooled ADU results below omit
direct-format cross-slice additions because of an evidence-adapter bug. The
source bodies were preserved but their fields were not routed. Bundle004 now
recovers 261 fields (38 durations, 28 pre-submittal, 164 actions, 20 counts,
11 explicit absences), preserving every previously routed claim. Only the 66
recovered timing/pre-submittal fields received contextual admission; the other
1,066 readings are reused unchanged. Treat the three initial pooled ADU fits
as **incomplete-input attempts**, not the completed legacy-tranche result.
The selected two-case shared fit and Solar inputs do not use those additions.

The corrected successor, `legacy_pooled_prepared002`, fits **89 reports from
76 dependence labels**. All three frames pass: worst R-hat 1.00204, minimum
bulk ESS 2,937, minimum tail ESS 3,627. Same priors, support gates and sampling
budget; this is an input repair, not a selected winning configuration.

| Corrected legacy ADU reporting clock | Reports | Median days [90% interval] |
|---|---:|---:|
| Construction start → completion | 34 | 250.2 [201.6, 326.8] |
| Narrated project process → completion | 21 | 614.1 [432.6, 918.4] |
| Narrated permitting → issuance | 34 | 325.3 [241.4, 437.6] |

The three populations are different selected report groups, not additive phases
or agency-only times. `legacy_pooled_summary002.json` binds corrected input and
outputs; 001 remains incomplete-input history. The corrected compilation admits
327 elapsed readings and retains all 5,398 claim rows. Thinning leaves 289
reports, of which 200 remain below the unchanged support gates. The newly coded
A-series and Houzz are **not** in this corrected legacy fit.

## ADU legacy plus A1–A42 — completed, summarized 20:10 UTC

The first new-source tranche adds 42 completed reader slices to the corrected
legacy evidence. All **four supported frames pass** the unchanged numerical
gates: worst R-hat 1.00133, minimum bulk ESS 3,073, minimum tail ESS 3,989.
They fit 161 distinct claim IDs, 62 from the new source slices, representing
142 contributor/dependence labels across frames—not 142 verified projects.

| ADU reporting clock | Reports | Median days [90% interval] |
|---|---:|---:|
| Construction start → completion | 47 | 262.5 [213.8, 336.2] |
| First submission → issuance | 22 | 204.7 [145.8, 301.6] |
| Narrated project process → completion | 30 | 729.1 [538.2, 1,056.1] |
| Narrated permitting → issuance | 62 | 330.5 [254.5, 419.4] |

The first-submission frame now clears the predeclared support gate. Its start
is narrower than the narrated-permitting frame; do not collapse them or add
these four rows. These remain selected reporting distributions, not population
or intrinsic-agency times. There is no new source-selection, step-inventory or
counterfactual identification claim. Later reader slices are not in these fits.

The frozen `a1_a42_evidence_bundle001.json` retains 6,806 claim rows; the
compiled version routes 6,839 readings including 33 secondary clock readings.
It admits 456 elapsed readings, thins them to 410 dependent-report-adjusted
candidates, and fits the 161 in these four supported frames. Other evidence
remains recorded, not deleted. All 1,132 legacy annotations are reused; only
175 new timing/pre-submittal fields received contextual model readings, with
13 itemized root changes. This was model admission, not another raw-source
verification campaign.

Inputs, all four attempts, p90 intervals, prior comparisons, fitted IDs and
hashes: `runs/adu_model_20260929/a1_a42_pooled_summary001.json`, its Markdown
companion, and `a1_a42_pooled_prepared001/`. Each fit again uses four chains,
1,000 warmup and 2,000 retained draws, marginalizing case variation while
sampling two coordinates. Passing these checks establishes numerical usability,
not model truth or an advantage over the LLM baseline.

## Solar pooled reporting clocks — completed 16:53 UTC

All **14 frames passed** the unchanged numerical checks: worst R-hat 1.00120,
minimum bulk ESS 4,196, minimum tail ESS 4,259. Each fit uses four chains,
1,000 warmup and 2,000 retained draws per chain. The existing marginal V6
implementation integrates individual case variation and samples two parameters
per frame, location and spread. This is not 1,225 separately sampled case
durations or a 14-step process model.

The frozen 968-packet corpus contains 25,833 staged episode records. Compilation
routes every one of 61,741 field entries and retains 10,605 numeric elapsed
candidates. **1,225 distinct claims actually entered these fits**, representing
899 contributor/dependence labels across frames, not 899 verified unique
installations. They comprise 1,007 completed intervals, 27 completed lower
bounds and 191 pending right-censored reports. Twenty otherwise admitted
reports remain below the declared support threshold; 9,041 candidates are
outside this initial clock list, 290 heterogeneous/non-target and 29 lack a
semantic clock. None of those routes deletes the original evidence.

Intervals below are **90% posterior intervals for each reporting distribution's
median**, in calendar days, not individual-case prediction intervals.

| Reported clock | Reports | Median days [90% interval] |
|---|---:|---:|
| Contract → installation | 68 | 104.6 [83.5, 131.1] |
| Contract → permission to operate (PTO) | 26 | 167.5 [124.8, 222.9] |
| Deposit → installation | 27 | 113.7 [79.8, 161.6] |
| Order → installation | 216 | 138.9 [124.9, 154.8] |
| Order → PTO | 43 | 128.7 [103.7, 158.9] |
| Permit submission → approval | 39 | 15.1 [9.9, 23.1] |
| Permit approval → installation | 17 | 19.4 [12.0, 31.6] |
| Physical installation duration | 137 | 2.15 [1.85, 2.52] |
| Installation → final inspection | 110 | 14.1 [11.4, 17.4] |
| Installation → interconnection submission | 17 | 73.9 [41.7, 138.6] |
| Installation → PTO | 403 | 74.4 [65.8, 84.0] |
| Final inspection → interconnection submission | 15 | 30.2 [20.1, 46.2] |
| Final inspection → PTO | 66 | 18.6 [13.1, 26.5] |
| Interconnection submission → PTO | 41 | 10.9 [6.9, 17.3] |

These are **different selected samples**, pooled across reported eras, utilities
and jurisdictions, including national and unknown-location accounts. They are
not California population estimates. Do not add or subtract rows. For example,
the order→PTO median is below order→installation, and inspection→submission is
above inspection→PTO: those are different reporting groups, not impossible
within-case timelines. They illustrate why independently fitted phase reports
cannot reconstruct one coherent process or measure source bias.

Unknown geography is retained; a named county/department is not an admission
condition. Posting/follow-up selection is not identified, the report-family
offset is fixed at zero as a convention, and the model assumes ignorable
coarsening within each declared report frame. These assumptions, the existing
Student-t reporting kernel and contamination prior govern inference.

Posterior/prior coordinate SD ratios are 0.032–0.185 for location and
0.114–0.546 for spread. Both shrink under this model, but marginal shrinkage
does not prove representative sampling, correct endpoints or separate causal
identification. There is no learned intrinsic agency capability, complete step
count, unobserved applicant labor or counterfactual statute-edit effect here.

Saved outputs:

- `runs/solar_model_20260929/combined_s1_frozen001.json`: exact packet versions.
- `combined_s1_adopted001/`: all claims, source links and compiler dispositions.
- `pooled_s1_prepared001/fit_plan.json`: estimands, support gates, input hash.
- `pooled_s1_prepared001/route_accounting.json`: every candidate's disposition.
- `pooled_s1_prepared001/fit_results.json`: all 14 attempts and numerical status.
- Each `pooled_s1_prepared001/frame_*/fit/`: input, config, draws, posterior,
  numerical diagnostics, implementation snapshot and hash-bound manifest.

## California-supported Solar reports — completed 17:02 UTC

This companion scope was declared after inspecting the all-location results,
so it is development rather than blind validation. It uses identical evidence
versions, priors, clock definitions and support gates, filtering only on the
preserved parser-supported California/context/county tags. Unknown-location
reports remain in the all-location analysis; they were not reclassified as
outside California.

Eight frames pass: worst R-hat 1.00202, minimum bulk ESS 1,404 and tail ESS 2,437.
There are **321 reports from 255 contributor labels across frames**: 269 completed
intervals, five completed lower bounds and 47 pending reports. Another 61
California-supported reports fall below the unchanged per-frame support gates.

| Reported clock | Reports | Median days [90% interval] |
|---|---:|---:|
| Contract → installation | 18 | 80.5 [53.1, 120.5] |
| Order → installation | 58 | 98.2 [80.7, 119.8] |
| Permit submission → approval | 16 | 17.1 [9.9, 27.7] |
| Physical installation duration | 34 | 2.27 [1.83, 2.91] |
| Installation → final inspection | 41 | 17.4 [12.7, 23.8] |
| Installation → PTO | 102 | 79.3 [62.7, 101.3] |
| Final inspection → PTO | 30 | 14.7 [8.8, 24.3] |
| Interconnection submission → PTO | 22 | 10.7 [6.2, 20.2] |

Intervals again describe uncertainty about a reporting-distribution median,
not individual predictions. This subset is still historical, selectively
reported and mixed across utilities/places/eras—not a representative California
applicant population. Differences from the all-location table do not estimate
a California causal effect. These separate samples are not additive components.
All eight runs and their unchanged gates are in
`runs/solar_model_20260929/pooled_s1_california001/`.

## Shared Solar journeys

The 11-case shared-journey control finished at 17:08 UTC in 34.4 minutes and
passed its generic numerical gate. The subsequent actual-case summary passes
**216/216 quantities**: worst R-hat 1.00426, minimum bulk ESS 745, minimum tail
ESS 1,367. Its 68 observations share 70 within-journey interval components, so
totals and parts are constrained jointly. There are 40 declared action
occurrences and 30 residual/coordination components across the eleven journeys;
these are fixed input inventories, **not 70 steps per installation or learned
posterior counts**. Agency/source scales are fixed to zero; no intrinsic-agency
or source-trust learning is claimed.

| Source-linked journey | Modeled scope | Median days [90% interval] |
|---|---|---:|
| Sodachanhduong | Inspection → PTO | 64.6 [41.2, 92.3] |
| Legitimate_Bobcat450 | Contract → PTO | 70.0 [45.4, 100.3] |
| J673hdudg | Order → PTO, including reported resubmissions | 210.2 [154.5, 271.1] |
| joe-ender, Concord | Plans → PTO under the declared start interpretation | 36.1 [23.0, 84.8] |
| Prestigious_List_958 | Order → physical installation | 128.2 [96.1, 169.0] |
| Sonofakeech | Contract → PTO | 27.2 [20.4, 38.3] |
| Numerous-Judgment279 | Reported permit-review scope | 10.4 [6.1, 17.5] |
| RightWinger | Declared reported journey ending at PTO | 93.3 [56.1, 129.9] |
| mushrew | Reported permit-review scope | 34.6 [22.1, 51.8] |
| ZiaMan24 | Declared reported journey ending at PTO | 167.0 [100.8, 227.6] |
| michaellcherry5 | Declared reported journey ending at PTO | 76.2 [33.3, 118.4] |

These are posteriors for the particular reported journeys, not population
medians or a representative sample. Exact event boundaries and source links
are retained in `joint11_control_summary001.json`; the table does not make
unmentioned starts or actions known.

The Concord conflict remains: 70.4% of its modeled total lies above the
reported 31-day upper bound. Its reported same-day inspection approval has a
latent median 3.51 days, with only 20.5% inside [0,1] day; the broad-error
component's conditional responsibility is 57.5% for that observation. This is
**model/report disagreement**, not evidence the author lied. The whole-clock
report is present in the likelihood, not dropped by the compiler.

The scoped log-total posterior/prior SD ratios range 0.084–0.200. Four Concord
component-share directions remain prior-width-or-wider (ratios 0.831–0.975):
plans-to-submission handoff, ground-photo submission, inspection decision and
inspection-to-PTO residual. Narrow total uncertainty does not identify each
internal allocation. Fixed narrated paths still do not identify missing steps,
population repeat rates or statutory counterfactuals.

`joint11_control_fit001/` binds the fit, and `joint11_control_summary001.json`
with its companion manifest contains actual-case diagnostics, native Student-t
report checks and 2,048-draw prior comparisons.

### Declared Solar sensitivities

The no-contamination sensitivity finished at 17:49 UTC (37.9 minutes). Its
generic gate and all 216 actual-case quantities pass. Generic diagnostic
extrema are R-hat 1.00473, bulk ESS 1,254 and tail ESS 2,399. It changes only
the broad-error mixture probability from 0.05 to zero; Student-t reporting
noise remains, so quoted bounds are still not hard constraints.

| Concord quantity/check | Control | No broad-error component | Wider task prior* |
|---|---:|---:|---:|
| Plans → PTO median [90% interval], days | 36.1 [23.0, 84.8] | 32.6 [22.2, 54.6] | 35.6 [22.0, 107.1] |
| Probability total exceeds reported 31 days | 70.4% | 58.3% | 66.9% |
| Same-day approval span median [90% interval], days | 3.51 [0.59, 19.93] | 1.01 [0.43, 4.75] | 0.82 [0.21, 11.14] |
| Probability approval span is inside [0,1] day | 20.5% | 49.3% | 61.9% |

This isolates a material role for the broad-error mechanism, but does not
eliminate the conflict or establish a preferred error model. The same frozen
eleven cases and all reports remain present. All-case posteriors, checks and
prior-width comparisons live in `joint11_no_contamination_summary001.json`,
bound to `joint11_no_contamination_fit001/`; none are hidden by the focused
Concord display. For example, michaellcherry5 moves from 76.2 [33.3,118.4] to
86.2 [48.0,120.9] days, illustrating that this is a scientific assumption
change, not a universally beneficial numerical fix.

*The wider task prior (`task_sd=2`) has completed, but **fails the strict
actual-case numerical gate**: 214/216 quantities pass. The two failed names
refer to the same michaellcherry5 county-plan-review span, with R-hat 1.01177,
bulk ESS 481 and tail ESS 3,037. Its generic coordinate gate passes (worst
R-hat 1.00989), illustrating why that generic check alone is insufficient.
Concord's displayed quantities individually pass, but this configuration
is not a fully passing fit. No chain extension or deletion is scheduled.

The wider prior leaves the original 0.05 contamination probability, evidence,
and sampling budget unchanged. It moves the same-day span markedly while
leaving the whole-clock conflict and a long upper tail. Broad-error
responsibility for that span falls from 57.5% to 22.3%; for the whole clock it
is 18.5%, versus 17.4% in the control. These are model allocations, not source
dishonesty probabilities. The uncertainty is sensitive to scientific assumptions
even when a particular reported quantity mixes well.

`joint11_declared_comparison001.json` records **all eleven cases in all three
attempts**, exact inputs/configuration differences and both numerical gates.
`joint11_wider_task_summary001.json` retains every failed quantity and all
report checks. Neither sensitivity deletes conflicting reports. Better
in-sample agreement is not held-out superiority; no winning model, new LLM
comparison or further prior/error grid is claimed.

## ADU pooled reporting clocks — initial incomplete-input attempt

All **three supported frames pass**: worst R-hat 1.00198, minimum bulk ESS
2,961 and tail ESS 3,801. The same two-coordinate marginal V6 implementation
used for Solar integrates individual case variation and samples location/spread;
four chains, 1,000 warmup and 2,000 retained draws per chain. Quadrature precision
checks also pass. No sampler extensions or extra source verification were needed.

This fit uses the initially compiled subset of the **old 22-slice tranche**,
not the ongoing A-series reading. It finished by 18:29 UTC; the direct-addition
omission identified later is described above and is being corrected without
deleting the original fit.
Its 1,066 timing/pre-submittal claims received contextual readings; 28 secondary
clocks are preserved separately. The compiler admits 300 elapsed observations,
keeps 688 qualitative/descriptive readings, 71 forecasts and 27 unresolved
readings, plus eight claim-level provenance holds. The other 4,071 field entries
remain in their own measurement channels, not fabricated into durations.

Dependence thinning leaves 271 reports across 160 clock/unit frames; 29 related
reports stay out of independent likelihood use. Three frames pass the fixed
15-contributor/five-finite-completed rule: **81 reports from 70 dependence
labels across frames**, not 70 verified independent projects. The other 190
thinned reports remain below support. First submission→issuance has 12 reports
and plan-check start→approval has five; neither was silently relabeled to swell
the broader permitting group.

| Selected report clock | Reports (finite completed / completed lower / pending) | Median days [90% interval] |
|---|---:|---:|
| Physical construction → reported completion | 30 (19 / 2 / 9) | 250.6 [198.9, 326.6] |
| Narrated project-process start → completion | 19 (8 / 2 / 9) | 662.0 [436.2, 1,095.0] |
| Narrated permitting-process start → permission issued | 32 (23 / 3 / 6) | 318.8 [233.9, 435.1] |

These intervals describe uncertainty about each selected reporting distribution's
median, not individual prediction intervals. The latter two clocks explicitly
have heterogeneous starts; construction completion can use final inspection
where that is the narrator's stated build endpoint. Seventy-six reports carry
California support and five have unresolved scope. Posting dates do not prove
event eras, and exchangeability across jurisdictions, project types and eras
is an assumption. These are **different report groups**, not additive phases,
statutory-clock violations or measured intrinsic agency delay.

Location-coordinate posterior/prior SD ratios are 0.077–0.141; spread-coordinate
ratios are 0.453–0.635. This demonstrates conditional posterior contraction,
not corrected forum selection, source trust or unseen-process identification.
The long whole-project upper interval reflects substantial remaining uncertainty.

Artifacts under `runs/adu_model_20260929/`:

- `legacy_clock_review_adopted001.json`: exact reviewed source hashes and 71
  itemized root adoption differences; originals are preserved.
- `legacy_clock_compiled001.json`: every claim's route and 300 admitted readings.
- `legacy_pooled_prepared001/`: frozen fit plan, all frame support counts,
  observation routes, all three fits, implementation snapshots and numerical gates.
- `legacy_pooled_summary001.json`: hash-bound consolidated metrics and diagnostics.

## ADU shared-phase model — completed 17:38 UTC

The first ADU attempt took 4.75 minutes, using four chains with 1,000 warmup
and 4,000 retained draws each. Generic and actual-case gates pass: **29/29
quantities**, worst R-hat 1.00309, minimum bulk ESS 1,403 and tail ESS 2,522.
The same V6 compiler/model serves both domains; only the evidence namespace
differs. This is not a new ADU-only architecture.

Two already-coded California-context accounts supply seven elapsed observations.
The ten modeled components are two design actions, four mixed approval/build
composites and four unmeasured handoff intervals. They are **not ten identified
steps, a county process menu or a learned distribution of correction rounds**.
Both accounts have unresolved city identity and were retained. Agency/source
scales remain zero; active labor, intrinsic capability and source selection
are not identified.

The substantive result is a warning, not good process recovery:

- `schatzistef` reports about two months design, four months submissions and
  approvals, five months construction, and an almost-one-year total. The model
  places that total at **419.9 [295.4, 759.5] days**, with **73.6% above one year**.
  The whole statement is admitted; broad-error responsibility is 13.4%.
  The two unmeasured gaps each receive a median about 39 days. Those are
  model-dependent allocations, not new observations of two month-long waits.
- `Special111k` reports four months drawing plans, six months of iterations and
  approval, and about ten construction months so far. Its **eventual** scoped
  total is **842.2 [507.6, 1,828.8] days**. That is conditional extrapolation,
  **not an observed completion time**. The construction posterior is 342.9
  [135.3, 974.6] days; 26.7% lies below the conservatively rounded pending bound.
  The native reporting kernel treats that bound as noisy, not a hard minimum.

The total SD ratios are 0.144 and 0.186 relative to prior, yet the short-total
conflict persists. For the pending case, both gap-share directions remain
prior-width-or-wider (0.857 and 0.844). Even narrower marginal gap durations
can be inherited through the hierarchy rather than directly measured. These
results point to a residual-gap/prior/report-error problem worth addressing,
not a reason to drop the whole-process statements or keep extending chains.
No further ADU sensitivity run is declared in this attempt.

The unchanged shared event-boundary design calculation gives a sharper
qualification (`shared2_boundary_design001.json`): ten component durations
have only seven distinct report directions, six from finite completed
intervals. Neither case separately distinguishes its two handoff gaps.
Schatzistef's reported total constrains their combined residual, not its split.
Special111k's total is **not in the observed endpoint row space at all**;
its narrower posterior inherits information through the hierarchy/prior and
is not a data-identified whole-project duration. This is an optimistic design
screen, not a new fit, an information estimate, or raw-source verification.

One post-fit **metadata correction** is explicit. The original common task
label said first submission through approval, but Special111k only establishes
plan iterations through approval. `reviewed_shared_journeys002.json` corrects
that start and labels the shared family as a broad narrated post-design
approval composite. Partial pooling of these differently described starts is
an assumption, not evidence of matched clocks. Observations, numbers, graph,
grouping and priors are unchanged. A bijective label-renaming comparison and
three saved-likelihood checks give exactly zero differences; **no resampling
or new fit** was performed. The original input, fit and summary remain intact.

Under `runs/adu_model_20260929/`:

- `shared2_fit001/`: the one actual sampling execution and immutable draws.
- `reviewed_shared_journeys002.json`, `shared2_prepared002/`: corrected semantic
  declarations; original 001 versions are preserved.
- `shared2_metadata_view002/METADATA_VIEW.json`: exact equivalence receipt and
  links to the original posterior/draws, explicitly not a second fit.
- `shared2_summary002.json`: current actual-case report on those same draws,
  with correct phase labels, all gates, prior comparisons and report checks.

The 22-packet pooled ADU tranche is now fitted separately above; new-source
reading is still ongoing. These two selected cases do not mean the whole ADU
corpus was fitted. Clock annotation read existing coded context, not the raw
source threads again.

No new same-evidence LLM comparison has been run. Numerical convergence here
does not establish a Bayesian accuracy advantage.
