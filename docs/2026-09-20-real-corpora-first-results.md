# Real-corpus results: first source-to-prediction checkpoint

2026-09-20. Real data only; synthetic work remains deferred. These are bounded,
qualified findings, not completion of the three-family study or a Bayesian win.

## CalFresh: an actual temporal comparison

The [new temporal packet](../runs/three_family_20260920/calfresh_temporal_prediction_v1/README.md)
trains on July2025 category counts and predicts August2025–July2026 in the same
captured administrative workbook. It replays3,068 native timing/total cells,
retains all754 county-month records, and removes the dependent statewide rows
from inference. The [protocol](scoping/2026-09-20-calfresh-temporal-prediction-protocol.md)
was fixed before this coordinator inspected later counts; this remains
exploratory, not blinded, and does not recover an as-of-July data vintage.

On481 comparable future positive-bin county-months, lower log loss is better:

| July-trained prediction | Mean category log loss |
|---|---:|
| County counts with simple Dirichlet smoothing | 0.252282 |
| LLM attempt1, July counts only | 0.252880 |
| LLM attempt2, July counts only | 0.253034 |
| LLM attempt3, July counts only | 0.253007 |
| County empirical proportions | 0.253356 |
| Pooled counts across the training counties | 0.266509 |
| Prespecified fixed-spread V6 condition | 0.276854 |

There is real predictive signal in county-specific recorded distributions. The
fixed-spread V6 condition loses to even these simple baselines despite passing
numerical checks; its poor in-sample predictive compatibility already warned
against it. Learned-spread V6 conditions are not yet eligible for comparison:
the base, tighter and all58 literal-zero conditions remain numerical failures
after their sole continuations. No further continuation is scheduled. This is
not evidence that Bayesian methods in general fail—the
simple Dirichlet comparator is itself Bayesian.

The [three-attempt LLM comparison](../runs/three_family_20260920/calfresh_llm_bin_baseline_v1/scored_v1/summary.json)
uses exactly the July counts, with no future observations, forum facts, tools or
V6 outputs in its payload. All three attempts were frozen before scoring; none
was selected as the winner. Their equal-weight probability average, reported
secondarily, scores0.252953. The largest across-run probability range is2.413
percentage points; the mean range across138 county/bin probabilities is0.0983
points. This is prediction variability, not a posterior uncertainty interval.
Each attempt chose its own Dirichlet-style smoothing rule, emphasizing that
“LLM versus Bayesian” is not a clean methodological dichotomy here. No
significance or full-burden superiority claim follows. Scoring arithmetic was
replayed by root, not yet independently reviewed by another agent.

The primary county set was selected on positive July bins; later primary
scoring also requires positive bins. Reporting zeros may mean missing/untracked
activity, and positive reports do not establish completeness. The71 excluded
future county-months stay visible; a literal-zero sensitivity is separate.
These results do not support statewide transport, county performance rankings,
intrinsic agency delays, or precise within-bin elapsed-time estimates.

## CalFresh forums: coverage is not model consumption

**Latest numerical result:** [case marginalization within the same V6 target](2026-09-20-calfresh-case-marginalization-results.md)
now passes all seven prespecified conditions on the same31 phone and28 interview
cases. It samples two coordinates rather than68/62, with unchanged evidence and
priors. Mixed-report medians are146.93minutes (90% interval113.75–191.14) for queue
exit and9.12calendar days (5.58–14.65) for interview. Fits took12.7–21.7seconds.
This resolves the numerical failures in these components, not source selection,
model adequacy or the joint burden model. Original full-latent failures below
remain historical failures; no passing sensitivity was promoted to base.

At20:50UTC, all945 captured logical threads have source-review receipts and
explicit dispositions. The exact777-thread new-batch union and1,810 manifest
bindings replay; the later-capture check found no added native comments in the
checked original143 captures. The [current source-use index](../runs/three_family_20260920/calfresh_forum_source_use_v2/README.md)
tracks actual expanded phone/interview factors and descriptive uses separately.
This is not complete model integration. The administrative
V6 input still has46 histograms and **zero forum observations**; forum cases are
in separate V6 components, not yet a joint administrative/forum posterior.

Current full-scope [interview fits](../runs/three_family_20260920/calfresh_forum_interview_fullscope_v3/compiled_preflight_v2/analysis_v1/README.md)
consume28 histories (18 completed,10 pending). Completed-only and base mixed fail
numerical gates. The prespecified wider-noise sensitivity passes, with conditional
median9.14calendar days (90% posterior interval5.65–14.88). Current
[phone fits](../runs/three_family_20260920/calfresh_phone_queue_exit_fullscope_v3/compiled_preflight_v3/analysis_v1/README.md)
consume31 queue spells (25 completed,6 pending). Completed-only passes with
128.54minutes (96.58–172.10); wider-noise mixed passes with147.72 (111.34–196.50).
Base mixed and prior15 fail. All eight-state likelihood replays are exact; this
does not override any numerical failure or establish model adequacy. No passing
sensitivity is chosen as a replacement base. These counts include the older17
cases per component, and one case is shared across clocks. They cannot be summed
into a number of independent applicants or a total burden.

The [contact/rework analysis](../runs/three_family_20260920/calfresh_contact_rework_analysis_v1/README.md)
adds40 reported count facts across34 recorded cases and20 nonnumeric structural
facts. These support finite-corpus descriptions, not population rates, active
hours or a Bayesian total-step estimate. The current index has776 effective
review items;718 are outside the two current likelihoods, including53 with
descriptive use already. This is a routing inventory, not718 known fit-ready
measurements or718 uniformly unfinished analyses. Other supported clocks and
burden uses remain on the integration path.

### Historical17-case components

The separate [claimant interview-encounter successor](../runs/three_family_20260920/calfresh_forum_interview_pending_v2/analysis_v1/README.md)
consumed17 unique forum cases:12 completed encounters and5
historical pending cases. All three prespecified conditions pass numerical
gates, with exact saved-likelihood replay. The completed-only report-frame
median is6.60calendar days (90% posterior interval4.11–10.45); including pending
histories gives11.41 (7.10–18.72), and wider report noise on those same17 cases
gives11.52 (7.19–18.92). Adding pending histories changes the selected frame;
this is not an estimated correction for forum selection. The predecessor's10
cases overlap these17, not27 in total.
Unknown actor identity is allowed. These are reported application-to-interview
encounters, including interrupted and joint-benefit intake, **not approval or
benefit availability**. Some intervals are explicit analyst coarsening
assumptions. This does not establish model adequacy, selection-corrected
population burden or a joint administrative/forum source-bias model. Most
reviewed evidence still has not entered a fit. Both continued coverage and
broader forum consumption remain completion requirements, tracked in the
[integration record](2026-09-20-calfresh-forum-model-integration.md).

The separate [phone-queue-exit component](../runs/three_family_20260920/calfresh_phone_queue_exit_compiler_v2/compiled_preflight_v1/analysis_v1/README.md)
fitted17 reported queue spells: six answered, four abandoned, one disconnected,
and six ongoing. All four prespecified conditions pass numerical gates and exact
likelihood replay. The11 completed exits give a median138.20minutes (90% interval
94.75–204.70); adding ongoing spells gives170.43 (123.53–252.19). Wider report
noise gives177.00 (120.10–272.96); moving the prior median from60 to15minutes
gives168.61 (122.78–247.05). These are elapsed single-queue spells, not active
labor, a successful-contact clock, or population-wide phone burden. Abandonment
is a completed exit, not censoring of an eventual answer. The17 phone and17
interview case IDs are disjoint, but no person-level independence or additive
total burden is asserted. Source-selection calibration remains unresolved.

## Solar: separate source requirements from fitted timing eras

The401-authority 2022 permit-phase V6 sweep was launched under its
[frozen plan](../runs/three_family_20260920/solar_full_panel_fit_plan_v1/README.md).
At18:21UTC the base and launcher were reversibly suspended to implement
[CalFresh first](2026-09-20-calfresh-first-closeout-work-order.md). No full-panel
result has passed analysis yet; no further Solar condition is launching.

New structural/fee extraction exposed a provenance problem: some locally saved
`.txt` files are WebFetch summaries, not original page text. The file named
`sandiego_infobulletin301_solarpv.pdf` is actually the original captured HTML.
The [additive correction](../runs/three_family_20260920/solar_structural_fee_fullread_001_provenance_erratum_v1/report.md)
checks ten San Diego claims against that HTML and identifies its **May2026**
bulletin date. Twelve claims from three other summarized pages are downgraded
to derivative evidence; their exhaustive-source-read claims are retracted.

The confirmed San Diego source distinguishes alternative permit routes,
plan-check and inspection fees, conditional structural review, and the separate
SDG&E energization approval. Those are useful process/fee observations, but
cannot silently explain the2022 timing panel or imply observed encounter counts.

## CCW: whole-process histories, not independent subclock totals

The [reviewed first96-label descriptive view](../runs/three_family_20260920/ccw_first96_whole_clock_descriptive_v2/README.md)
contains eight exact-day initial-submission-to-physical-receipt episodes: seven
start in2022 and span158–367days (finite-report median297); one starts in2023
and spans498days. Nine additional completed same-estimand histories have
unresolved/coarse clocks and remain visible rather than converted to exact days.

Source parsing has progressed through fixed rank132, with later tranches still
awaiting coordinator consumption. The first whole-process V6 candidate remains
two unexecuted drafts, deferred under CalFresh-first; it is not a prepared input
or fit. Selected forum reporters cannot be treated as an unselected county
applicant sample.

## What remains

Finish CalFresh first: forum coverage and direct model integration, and a
consolidated qualified result. The administrative continuations are terminal;
their numerical failures are preserved, not grounds for another open-ended run.
The temporal scorer has an independent qualified review; all three LLM
comparisons are now scored. Solar, CCW and synthetic work remain deferred.
Full source completion, source-bias calibration and paper-ready
generalization remain unproven. The [audit handoff](2026-09-20-verification-and-analysis-audit-handoff.md)
explains the verification stages and historical state; this document records
the new empirical result rather than another blanket “verified” label.
