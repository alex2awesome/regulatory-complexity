# Source precision and the finite-cohort handoff

2026-09-20. Implementation follow-up to the
[source-trust note](2026-09-20-source-trust-note-for-codex.md), within the
approved solar / concealed-carry / CalFresh study. This is not empirical
calibration or evidence of superiority to an LLM.

## What now works

V6 accepts an optional, fixed elapsed reporting-error scale by source type.
The [compiler](../pipeline/procbench/compile_visit_durations.py) resolves an
explicit declaration; [one validator/resolver](../pipeline/procbench/source_precision.py)
supplies the scale to the vectorized, reference, ordinary-population and
finite-quantile-cohort likelihoods and their diagnostics. No new latent
coordinate, source ranking or production prior default is introduced.

| Mechanism | Current treatment | What this change does not claim |
|---|---|---|
| Relative reporting bias | Optional reference-anchored type/document hierarchy | No real-data source contrasts have been identified in the fixed solar pilot. |
| Reporting precision | Explicit fixed log-scale by type, with default fallback | A named calibration reference is not proof it has been empirically calibrated. |
| Finite-sample variation | Joint order-statistic integration using a reviewed denominator | An adjacent installation count or bare ledger `n` is not automatically an eligible cohort. |
| Contamination | Existing global broad-error mixture | Type-specific contamination is not yet learned. |
| Selection | Existing explicitly declared case selection, separate from reporting | Neither source labels nor larger `n` correct population/institution selection. |

The optional compiler policy key is `source_type_report_scales`, schema
`source-type-report-scales/1`, with `elapsed` entries containing positive
`report_log_scale` and a declared `calibration_id`; fallback is
`config_report_sd`. Diagnostics label references **unverified** and distinguish
fixed scales, fallback, unknown-`n` floor eligibility and actual floor increases.
The interface and hash-bound source receipts are in the
[implementation packet](../runs/three_family_20260920/source_precision_implementation_v1/implementation_report.md).

`Config.report_sd` is a four-degree-of-freedom Student-t **scale**, not its
standard deviation. Increasing a reviewed cohort's `n` shrinks sampling
variation, not this reporting scale. Unknown-`n` summaries retain the explicit
floor. Subjective typical ranges retain their own contract. Residual-only
reports, labor, counts, money and exact histograms are not silently given the
new precision policy. Exact histograms have no narrative-report error kernel.

Without a precision declaration, the root's
[independent replay](../runs/three_family_20260920/source_precision_root_review_v1/receipt.json)
found exactly equal likelihoods, layouts, source-support reports and short
seeded chains against preserved code on six source-free fixtures. Both
document- and type-grouped compiler outputs were unchanged. These short chains
are regression checks, not convergence evidence.

## Controlled influence check

A [protocol-fixed numerical experiment](../runs/three_family_20260920/source_precision_influence_gate_v1/report.md)
compares one individual report with a reviewed finite-sample median. Both
inform the same log population median, use the same reported interval,
location prior and known population spread, and integrate the individual
case's latent duration. It does not treat the individual's reported number as
a known population statistic.

With equal reporting scale `0.35`, the posterior log-location SD falls from
`0.544` for the individual to `0.382` for the `n=101` median, approximately a
30% reduction. Movement from the prior toward the common report rises from
`0.539` to `0.778` of the prior-to-report distance. The infinite-`n` SD remains
`0.378`: reporting uncertainty does not disappear. Independent order-statistic
quadrature checks the V6 cohort-grid calculation; the declared numerical and
directional gates pass.

In a prespecified counterexample, giving the cohort a reporting scale of
`0.70` and the individual `0.20` reverses the advantage even at `n=101`.
Consequently this is evidence that the mechanics distinguish sampling from
reporting uncertainty, **not** a theorem that aggregates or official sources
always deserve more weight. No actual corpus or synthetic-world labels were
used in this experiment.

## Concrete integration bug repaired

The structural bridge previously copied ordinary observations but always
emitted `quantile_cohorts=[]`. The compiler could therefore admit a reviewed
cohort and then lose it before V6. The
[bridge](../pipeline/procbench/bridge_structural_routes.py) now carries the
compiled joint cohort verbatim, including its denominator, operators,
population contract and resolved precision. It does not manufacture these
fields from a source label or a number in prose.

The cohort contributes once to route-reference accounting, rather than once
per reported quantile or once per applicant. Its operators participate in
channel/phase and unsupported-route checks. Claim identities, cohort identities
and native time units are checked to prevent duplication or reinterpretation.
An end-to-end source-free test follows two compiled cohort summaries through
the bridge into **one** V6 likelihood factor.

Independent review of the first patch found three additional problems:
an ordinary row could collide with a generated cohort likelihood key and be
overwritten; a business-day cohort could reinterpret legacy unitless calendar
rows; and combining programs could admit a duplicate cohort identity. The
[failed review is preserved](../runs/three_family_20260920/bridge_quantile_cohorts_review_v1/report.md).
All three have bridge guards and regression tests. A fourth issue found during
review—unitless nonelapsed factors incorrectly imposing calendar units—was
also repaired. The [second independent bridge review](../runs/three_family_20260920/bridge_quantile_cohorts_review_v2/report.md)
passes all four counterexamples and 111 adjacent tests. The
[independent direct-model review](../runs/three_family_20260920/conditional_case_frames_independent_review_v1/report.md)
also passes: exact generated keys are reserved globally across programs and
checked separately for plain/path route alternatives. This catches delimiter
aliases such as program `a` / row `b:c` versus program `a:b` / row `c`, without
rejecting keys used only in mutually exclusive route modes. The final frozen
code passes [1,472 regression tests](../runs/three_family_20260920/root_integration_checkpoint_1443/receipt.json).
Do not read a passing ordinary test suite as proof that these errors were absent
before the independent counterexamples were tried.

The no-cohort bridge replay uses a
[hash-verified reconstruction](../runs/three_family_20260920/source_precision_root_review_v1/bridge_receipt.json)
of the pre-edit source: the initial assumed snapshot did not contain this
module. Default program output is identical on its fixtures, with only an
intentional correction to the empty-cohort explanation in the report.

## Remaining empirical boundary

The [fixed-12 solar overlap review](../runs/three_family_20260920/solar_fixed12_cross_source_overlap_v1/README.md)
found zero eligible forum/oversight comparisons after checking 41 candidate
pairs. All twelve jurisdictions remain unmatched. Its captured-record token
screen is not an exhaustive semantic read of every document or live source.
It supports **no identified comparison in this pilot**, not a claim that such
comparisons cannot exist elsewhere. The mathematical bias/precision checks do
not remove this empirical limitation.

A second [bounded overlap review, for CalFresh](../runs/three_family_20260920/calfresh_cf296_narrative_match_review_v1/report.md),
accounts for 25 already-reviewed forum threads (17 extracted timing records in
nine threads, 16 without such records), 29 oversight records and all twelve
July 2025 CF296 target histograms. It finds **zero matched narrative cases**.
Wrong clocks, counties, periods and populations—not the sources' reputations—
exclude the apparently similar three-day statements. Cases were not converted
to medians and no ratio or source-bias estimate was calculated. Root rehashed
all 51 packet/input/source bindings with no mismatches. This is a closed-inventory
absence result, not an exhaustive web finding; the reviewer reused the earlier
source-checked oversight quotations rather than rereading all six PDFs.

The [bounded CCW and CalFresh real-data pilots](2026-09-20-calfresh-and-ccw-pilots.md)
now have independently reproduced results under explicit conditional targets.
They constrain a reported-history timing location or recorded-bin probabilities,
not cross-source trust. Matched synthetic counterparts and same-information
baselines remain unfinished. Source-type
precision calibration, learned contamination and transport between programs
remain separate unfinished work. Counts still have a global error scale and
no source offset; labor and external costs remain non-headline where evidence
does not identify them.

## Exact administrative counts as the hierarchy's reference

A further integration gap was reproduced on an invented fixture: v1 of the
optional source hierarchy requires a noisy-report document of its reference
type. An exact administrative histogram correctly has no such reporting-offset
document, so histogram-plus-forum evidence could run in legacy V6 but could not
use that histogram as the hierarchy reference. No factor was silently lost.

The [narrow v2 extension](scoping/2026-09-20-histogram-source-reference-extension.md)
adds hash-bound references to existing exact histogram cohorts. It introduces
neither a dummy administrative median nor a duplicate likelihood term; the
histogram keeps its original exact-count treatment while report types retain
their bias terms. It does not certify matching clocks/populations or truthful,
complete administrative reporting. All prior real fits remain unchanged on
their frozen V3 code.

The [initial implementation and replay](../runs/three_family_20260920/histogram_source_reference_implementation_v1/replay_receipt.json)
passed 54 focused tests and 1,543 scoped regression tests (one pre-existing
generator warning). Six v1/disabled fixtures reproduced frozen coordinates,
likelihoods, complete source-support reports and short seeded trajectories
exactly. Those short runs test compatibility, not convergence. The
[independent initial review](../runs/three_family_20260920/histogram_source_reference_extension_review_v1/report.md)
passed target mechanics but found an ambiguous family-level diagnostic: an exact
histogram has **no applicable reporting-offset parameter**, which must be kept
separate from any noisy-report offsets in the same source family. A narrow
reporting repair has now [passed successor independent review](../runs/three_family_20260920/histogram_source_reference_extension_review_v2/report.md),
including mixed-family and two-anchor cases. The initial failed review is
preserved. The [sealed successor and legacy replay](../runs/three_family_20260920/histogram_source_reference_implementation_v2/replay_receipt.json)
pass 55 focused and 1,544 scoped regression tests, with the same pre-existing
warning; all six v1/disabled replay results remain exactly equal. No real fit or
calibration has been run with v2.

## Shared populations versus shared cases

A [source-free dependence review](../runs/three_family_20260920/s07_cohort_case_dependence_review_v1/report.md)
confirms another boundary: V6 does not currently model the joint likelihood of
a forum case and an administrative aggregate that contains that exact case.
It rejects an explicitly shared `cohort_id`, but missing membership metadata
does not magically establish independence; unlinked inputs contribute separate
factors. Independently sampled cases from a common population are different and
may legitimately share parameters without being duplicates.

The synthetic builder must preserve exact membership privately for evaluation.
The review's [mandatory boundary qualification](../runs/three_family_20260920/s07_cohort_case_dependence_review_qualification_erratum01/qualification.md)
restricts its private-membership instructions to generator/evaluator audits.
That does **not** authorize a blind extractor or fitter to use those hidden IDs
to choose evidence or weights. The [root implementation decision](../runs/three_family_20260920/s07_case_contract_root_review_v1/decision.md)
requires public support for an independence claim, a predeclared single-view
experiment, or a genuinely disjoint published cohort; otherwise the combination
stays held. Published statistics cannot be silently recomputed from private
truth to manufacture independence. The new histogram-reference mechanism does
not remove this requirement. S07's frozen business-day median/p90 reports also
remain distinct from V6's calendar-day exact-histogram contract.
