# CalFresh: additional forum clocks actually consumed

2026-09-20. This is a continuation of the
[forum integration requirement](2026-09-20-calfresh-forum-model-integration.md),
not a new corpus or a restart of synthetic work. Captured-source review is
complete; fitting each supported clock is a distinct downstream task.

## Application to reported benefit availability

All four fixed conditions have now run through the existing V6 marginal-case
path and pass unchanged numerical and integration checks. Each is a cold fit
with four chains,1000 warmup and2000 retained draws per chain, two sampled
coordinates, and no continuation. No cases or priors changed after adoption.

| Selected report frame | Cases | Median calendar days,90% posterior interval |
|---|---:|---:|
| Completed intervals | 5 | 1.12 (0.17–3.52) |
| Completed plus pending | 6 | 2.14 (0.47–8.44) |
| Same six,wider report noise | 6 | 2.15 (0.43–8.46) |
| Same six,prior median7 rather than30days | 6 | 1.54 (0.29–6.68) |

These are **not estimates of typical CalFresh application time**. Four of the
five completed observations have zero lower bounds, including broad
completed-by reports. The finite six-record median is bounded only by0–13days
before distributional/reporting assumptions. The location-prior sensitivity
changes the posterior median by about28%; the spread's posterior variance
increases relative to its prior in every condition. That is a weak-constraint
warning, not evidence that the posterior literally equals the prior. Do not
headline a precise process time or an estimated county/agency effect.

Sources describe loaded, deposited, visible or reported received benefits;
these are applicant-facing availability endpoints, not a precisely observed
internal agency decision. Five captured authors are distinct and one is
uncaptured. Six case/thread representatives have no detected duplicate, but
independent people are an assumption. Cases can overlap other clock components;
neither counts nor durations should be added to obtain total burden.

The [root adoption](../runs/three_family_20260920/calfresh_benefit_availability_fullscope_v1/root_adoption_v4.md)
records the four earlier semantic repairs and the independent six-case review.
The [fit results](../runs/three_family_20260920/calfresh_next_clock_marginalization_v1/benefit_availability/analysis_v1/README.md)
and [actual factor-to-source consumption](../runs/three_family_20260920/calfresh_next_clock_marginalization_v1/benefit_availability/analysis_v1/actual_model_consumption.json)
are on disk. All eight saved likelihood states replay exactly per condition;
128-to256-node and independent Gaussian-case integration checks agree within
4e-9 on the checked states. Source semantics were independently reviewed;
these numerical summaries subsequently passed a separate
[twelve-fit numerical/provenance review](../runs/three_family_20260920/calfresh_next_clock_marginalization_v1/results_review_v1/report.md).
That reviewer authored the renewal inputs, so this is not an independent
renewal source-semantics audit. All227 bounded checks passed; no fits were rerun.

## Current SAR7 successor: ten records

The [ten-case successor](../runs/three_family_20260920/calfresh_sar7_fullscope10_marginal_v1/analysis_v1/README.md)
now replaces the nine-case SAR7 component below; it does not add another four
conditions to current totals. All four runs pass numerical gates. The original
nine observations/configurations are unchanged. One previously omitted source
describes June 1 submission followed by June 11 receipt of an individualized
missing-affidavit letter, yielding [9,11] calendar days under the existing
date-only rule. Root read the native chronology and the independent review;
the [adoption](../runs/three_family_20260920/calfresh_sar7_fullscope10_v1/root_adoption.md)
preserves later affidavit, discontinuation, scanning and contact as dependent
parallel uses, not independent responses.

| Declared condition | Cases (pending) | Model median days, 90% interval |
|---|---:|---:|
| Completed reports | 5 (0) | 9.53 (5.10–17.13) |
| Completed plus pending | 10 (5) | 19.15 (10.62–38.79) |
| Same ten, wider report noise | 10 (5) | 19.07 (10.38–39.14) |
| Same ten, seven-day location prior | 10 (5) | 18.14 (10.17–35.17) |

This remains first reported material response, not successful processing or
restoration. Finite-record median bounds are [9,13] days for completed reports
and [10,infinity) for the mixed frame, not posterior or confidence intervals.
Selection, small sample size and distributional assumptions remain limitations.
There were no continuations or best-condition selection.

## Historical nine-case SAR7 and current recertification

At the earlier checkpoint, all eight conditions were terminal numerical passes, with the same
four-chain budget and two-coordinate V6 inference path. Pre-fit corrections
preserve approximate dates, a June22 retrospective update rather than an
invented June13 update, and native metadata for relative-day bounds. No annual
recertification cadence is inferred. The [adoption record](../runs/three_family_20260920/calfresh_reporting_renewal_frames_effective_v3/root_adoption.md)
identifies the exact corrected inputs and unchanged configurations.

| Selected report frame | Cases (pending) | Median calendar days,90% posterior interval |
|---|---:|---:|
| SAR7,completed | 4 (0) | 9.34 (4.46–19.38) |
| SAR7,mixed | 9 (5) | 22.20 (11.35–48.34) |
| SAR7,mixed,wider noise | 9 (5) | 22.16 (11.38–49.70) |
| SAR7,mixed,7day prior | 9 (5) | 20.61 (10.44–43.61) |
| Recertification,completed | 2 (0) | 26.31 (11.60–60.63) |
| Recertification,mixed | 3 (1) | 31.27 (15.72–68.01) |
| Recertification,mixed,wider noise | 3 (1) | 32.70 (14.00–83.59) |
| Recertification,mixed,7day prior | 3 (1) | 29.36 (14.58–63.14) |

SAR7 ends at the first source-observed material processing response/state;
recertification ends at observed decision/status, not necessarily successful
renewal. The two completed recertifications are denial/status histories, not
two successful approvals. Unknown departments are allowed throughout.

More than half the SAR7 records are pending. Their finite-record median has
lower bound11days and **no finite upper bound**; its finite posterior interval
depends on the assumed distribution and spread prior. Recertification has only
three records. Mixed-frame spread variance contractions are23% and10%
respectively, triggering the existing weak-constraint screen. These are not
claims of a precise typical SAR7 or recertification time, population service
quality, calibrated selection or learned agency effects.

[SAR7 results and consumption](../runs/three_family_20260920/calfresh_next_clock_marginalization_v1/sar7/analysis_v1/README.md)
and [recertification results and consumption](../runs/three_family_20260920/calfresh_next_clock_marginalization_v1/recertification/analysis_v1/README.md)
retain all conditions and every source-bound factor. Eight saved likelihood
states replay exactly per condition; the prescribed integration checks pass.

## Approval to physical card possession

An additive [business-date admission sensitivity](../runs/three_family_20260920/calfresh_card_business_bound_marginal_v1/analysis_v1/README.md)
has also finished and passes: nine cases, six pending, model median22.07days
(90% interval11.42–48.45). The four eight-case conditions below stay unchanged.
The added Stanislaus report explicitly says four business days since approval
without card receipt. Under a declared four-distinct-inclusive-business-dates
reading, unknown within-day times permit only a conservative lower bound of
two calendar days. This is not an exact conversion or an assumption-free reading
of colloquial counting. Root rejected an earlier three-day lower bound: Monday
23:59 to Thursday00:01 spans four business dates but just over two elapsed days.
The [adoption](../runs/three_family_20260920/calfresh_card_business_bound_sensitivity_v1/root_adoption.md)
preserves the native fact, unchanged report-error kernel, original eight inputs
and the separate unknown-origin hold. No additional bound was tried after fitting.

The [card-access fits](../runs/three_family_20260920/calfresh_card_access_marginal_fit_v1/analysis_v1/README.md)
now consume eight additional component records under four fixed conditions.
All four pass the unchanged numerical gates. These use the existing V6
independent-case marginal likelihood, not a new architecture.

| Selected report frame | Cases (pending) | Median calendar days,90% posterior interval |
|---|---:|---:|
| Completed physical possession | 3 (0) | 5.20 (0.85–21.12) |
| Completed plus pending | 8 (5) | 21.80 (11.24–49.34) |
| Same eight,wider report noise | 8 (5) | 22.90 (10.50–57.25) |
| Same eight,7day location prior | 8 (5) | 20.34 (10.65–45.52) |

The clock starts at source-reported approval/notification and ends at physical
possession, including in-person issuance. It is not mailing time, benefit
availability or intrinsic agency delay. The [pre-fit root adoption](../runs/three_family_20260920/calfresh_card_access_compiler_v1/root_adoption.md)
records the eight histories, context-dependent origin interpretation and excluded
business-day record. The majority are pending: their finite-record median is
bounded below by10days and has **no finite upper bound**. A proper lognormal
duration model assumes eventual possession, which these reports do not establish.
Existing-card reactivation, nonissuance, delivery route and posting selection are
not modeled. Do not headline a typical card wait or promise eventual arrival.

Root replayed all19 analysis bindings and inspected every condition's numerical
and integration diagnostics. Minimum bulk ESS2646, minimum tail ESS3319 and
maximum R-hat1.00123; saved likelihood replays agree exactly and checked
quadrature differences are below5.3e-9. The spread's posterior variance exceeds
its prior in all four conditions, retaining the weak-constraint warning. These
checks are not a source-selection or model-adequacy validation.

## Other supported uses and limits

The [remaining descriptive analysis](../runs/three_family_20260920/calfresh_contact_rework_remaining_analysis_v1/report.md)
accounts for all60 rows in its assigned queue:26 supply42 standalone numeric
facts,28 retain nonnumeric context, and6 have explicit holds. These include
contacts, documents, reported financial consequences, access problems and
workforce context; their units and meanings are not summed into a burden score.
The [sixteen-claim semantic resolution](../runs/three_family_20260920/calfresh_semantic_resolution_16_v1/root_adoption.md)
preserves explicit actor/identity ambiguity and adds three timing candidates,
not yet three likelihood factors. Named departments are not an admission gate.

No evidence is globally excluded merely for failing to match the administrative
July2025 cohort. None of these separate components yet calibrates source bias
or establishes a joint administrative/applicant burden posterior.
