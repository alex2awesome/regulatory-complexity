# Independent cross-scoping verification — 2026-09-16

Owner: `codex`, packet `Q1-CROSS-SCOPING-AUDIT`. This is a separate audit of
Codex's P1/P3/P5 work and Claude/fable's APR, discretion, covariate and W2 claims.
The working reports remain owned by their authors. Findings are also posted to
the append-only [coordination log](FINDINGS.jsonl), so fixes can happen without
concurrent overwrites. No model fit or reserved-world access is part of this audit.

## Confirmed corrections

### The APR application date is not necessarily first submission

The official [Table A dictionary](https://data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/198bded5-7a17-4e1e-bea5-688dbb439c6d/download/annualprogressreport_tablea_datadictionary-1.docx)
defines `APP_SUBMIT_DT` as the application date **or the completeness date when
initial submission was incomplete**. Thus the joined clock excludes the earlier
incomplete-application period in those cases. Calling it full applicant elapsed
time, or using it as a direct target for end-to-end synthetic burden, is wrong.
Use **reported complete-application → permit** and model the omitted interval
separately. Nor does this interval measure staff work hours.

The same dictionary identifies APN as a **parcel**, whereas `JURS_TRACKING_ID` is
the jurisdiction's project identifier. Multiple applications can share a parcel.
An earliest-date parcel join needs sensitivity analysis, not a unique-project
interpretation. The [Table A2 dictionary](https://data.ca.gov/dataset/81b0841f-2802-403e-b48e-2ef4b751f77c/resource/354a375a-821d-4d4e-97ab-4d79c2925fce/download/annualprogressreport_tablea2_datadictionary-2.docx)
also describes a local identifier, but it can be a permit number; agreement
between identifiers across tables must be measured, not assumed.

Both dictionaries are cached as `corpus/counties/raw/qa_apr_table_*_dictionary.docx`;
the package metadata is `raw/qa_apr_package_2026-09-16.json`. The Table A dictionary
does **not** define the CSV's `PROJECT_TYPE` field. Its precise definition and
phase-in need separate APR instructions. Published missingness counts alone do
not establish a legal mandate or validate the reported labels as legal truth.

### Correlation does not establish reporting coverage or causal attribution

A correlation between county population and APR record volume is compatible
with both complete and selective reporting. Without an independent denominator
of eligible projects, it cannot establish that rural reporting is unbiased.
Similarly, a small marginal population/timing correlation is not a bound on
multivariable predictive performance, and unexplained variation is not identified
as local policy, discretion, or administrative capacity.

The draft W2 specification should not hard-code a low explained-variance regime
as an empirical conclusion of these exploratory correlations. Clock definition,
city-versus-county covariates, linkage, aggregation and case mix all change the
comparison. Predeclared low-/high-signal sensitivity worlds remain useful.

## Reproduced results and measured sensitivity

### APR linkage

[Independent replay](../../corpus/counties/audit_apr_linkage.py),
[saved summary](../../corpus/counties/apr_linkage_audit.json), and
[jurisdiction comparisons](../../corpus/counties/apr_linkage_audit_by_jurisdiction.csv)
reproduce **358,264 A rows, 922,104 A2 rows, 58,090 duplicate parcel-key hits and
376,564 matched A2 rows**. Those counts hold up.

However, among 300,171 application-side parcel keys:

- 20,377 have multiple application dates; 18,869 have multiple tracking IDs.
- 1,025 have conflicting nonempty process labels and 5,712 multiple statuses.
- 9,635 combine the earliest date with first-nonempty label/status values that
  never co-occur on one application row. This is a provenance failure, although
  it does not by itself prove every such merged record describes different cases.
- Among matched A2 rows with a permit date, 38,677 repeat a parcel + tracking ID
  + permit-date event. These are repeated records, not necessarily duplicate
  housing units; weighting them as distinct applicants is unsupported.

The P0 join's docstring says it takes the earliest A2 permit per key. Its loop
actually uses **every matching A2 row**. P9 does select the earliest permit per
parcel, but a parcel still is not an application, and label/outcome counts use
the original Table A rows while timing counts use collapsed parcel keys.

| ADU comparison | Observations | Pooled median days |
|---|---:|---:|
| Original earliest-parcel date, all valid matched A2 rows | 122,936 | 166 |
| Original earliest-parcel date, restricted to the paired cohort below | 90,845 | 150 |
| Exact tracking ID and same APN, same 90,845 valid A2 rows | 90,845 | 140 |
| Earliest permit per parcel | 90,553 parcel keys | 163 |
| Earliest permit per exact tracking ID, single application date and parcel | 69,665 tracking keys | 141 |

The **150 → 140** comparison isolates the date-linkage change on the same rows;
the other comparisons also change selection or weighting. In that paired cohort,
5,295 rows change duration. Exact IDs are a restricted sensitivity cohort, **not
validated entity resolution**. Many legitimate records may have differing
planning/building identifiers. A future join should preserve alternative matches,
label/date provenance and nonmatches rather than declare either method gold.

Aggregation matters independently: P9's Los Angeles city/county **140.5/383 days**
are medians of annual medians; pooled medians on its same parcel-key construction
are **141/315**. Neither statistic is intrinsically invalid, but they estimate
different quantities. The report should name the weighting and population.

### County correlations: values reproduce, inference changes

[Reproduction and rurality check](../../corpus/counties/audit_county_calibration.py)
writes [the saved audit](../../corpus/counties/county_calibration_audit.json).
It retains P9's exploratory 30-county, mixed city/county aggregation, including
its linkage limitations; it is not a replacement population estimate.

| Predictor | Correlation with raw median days | With log median days |
|---|---:|---:|
| log population | 0.335 | 0.342 |
| log local-government employment | 0.318 | 0.282 |
| RUCC | −0.398 | −0.389 |
| log density | 0.688 | 0.624 |
| bachelor's degree share | 0.583 | 0.605 |

The raw-day column reproduces P9. W2's calibration table labels its simulated
target **log** median days while citing the raw-day correlations. Those are not
interchangeable. Squaring 0.688 yields a single-predictor in-sample R², not a
measured five-predictor or transfer R².

For illustration, OLS with these five predictors plus an intercept gives
training R² **0.549 on raw days / 0.475 on log days**. Leaving one county out at
a time gives squared-error improvement over each fold's training-mean prediction
of **−0.067 / +0.131**, respectively. These are exploratory checks—predictors
were already selected after examining the data—not a clean confirmatory test or
a Bayesian-versus-LLM result. They show why training fit must not be substituted
for held-out prediction.

### Rurality covariate: four misclassified counties

The builder labels `RUCC >= 6` as `is_noncore`. USDA's
[RUCC definitions](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/documentation)
describe urban-population size and metro adjacency, not the metro/micro/noncore
partition. Actual noncore status excludes both metropolitan and micropolitan
areas; see [UIC definitions](https://www.ers.usda.gov/data-products/urban-influence-codes/documentation).

Joining the official [2024 UIC file](https://www.ers.usda.gov/media/6182/2024-urban-influence-codes.csv?v=91435)
to all 58 FIPS codes gives **11 noncore counties, not 15**. Alpine, Del Norte,
Inyo and Lassen are micropolitan in that file but marked noncore in the shared
table. [The correction join](../../corpus/counties/county_noncore_audit.csv)
is saved separately for its owner to incorporate. The original table is not
overwritten. QCEW's all-local-government employment also remains a proxy, not
county-department staffing; its README correctly states that limitation.

## Codex work rechecked

### CalFresh: all exported cells match their sources

[Read-only independent check](../../corpus/counties/audit_calfresh.py) compared
**every exported cell**, not just a sample, to the cached source workbooks:
source hashes, county/month, form cell, numeric value, suppression/error/missing
state, source coordinate and county code where published. It does not import
the extractor. [Saved audit](../../corpus/counties/calfresh_extraction_audit.json):

| Export | County + statewide cells checked | Workbooks | Result |
|---|---:|---:|---|
| CF 296 | 887,301 | 10 | All match |
| CF 18 selected timing cells | 7,080 | 1 | All match |

Total **894,381 cells**. This verifies transcription and provenance, not the
publisher's accuracy. The documented CWD-error qualifier, disposition-month
versus intake-cohort distinction, CF18 approval-versus-issuance clock, zero
denominators, source errors and statewide-mean anomaly remain material.

### General Assistance: a useful dataset, but not the requested broad clock

The [separate source audit](2026-09-16-general-assistance-source-audit-codex.md)
preserves the 12-row early inventory after handoff to Claude's `ga-agent`.
It checks two official GR237 workbooks: **32/30 wholly blank county-months**,
Humboldt July `#REF!` rows in both, and **11/9 missing county-months not disclosed
in release notes**. The narrow timing field concerns SSA-check disposition after
receipt, not ordinary GA application-to-decision time or agency labor.

The case descriptions also need care: Hunt concerns Sacramento medical-care
eligibility, not a current GA cash-grant schedule; the statutory safe-harbor
reference is to the 1991 poverty guideline, not today's guideline. See the
appendix's primary-source links and category/date caveats.

### Environmental health: freshness corrections, not universal coverage

The continuing P5 audit found San Mateo's March 28, 2022 approval in the lead
regional board's April 2022 report, despite another board's later-dated index
still saying in progress. It also corrected Santa Clara's approval date and
found a newer San Bernardino approval. The count becomes **48 listed/historical
approvals**, not 48 verified-current county LAMP PDFs. The explicit February 1
deadline is in the Tier 2 policy provision; statewide all-agency reporting and
regional guidance must not be conflated with that exact clause. Changes and
source links are recorded in the [P5 report](2026-09-16-county-environmental-health-58.md).

## W2 design items still requiring correction

These are **draft-design issues, not claims that an implemented W2 has already
leaked truth**. The late draft changed substantially while this audit ran.

1. **Clock/phase mechanism is not identified.** Different correlations on two
   differently selected and linked datasets do not prove all covariate effects
   occur before a decision and none afterward. The documented completeness
   date specifically contradicts treating the joined interval as all initial
   preparation/resubmission time. Queue-only effects can be a declared scenario,
   not a discovered causal law.
2. **Wrong outcome population in §9.1.** The 194,347 approved / 54,382 pending /
   1,219 withdrawn / 89 disapproved counts are P0's matched A2-row totals across
   **all unit categories**, not ADU applications. They also inherit repetition
   and first-nonempty-status assignment. Do not calibrate an ADU outcome mixture
   to these totals.
3. **Pending does not identify abandonment.** Nor do zero reported withdrawals
   prove suppression or nonreporting. Live cases, attrition, filing practice,
   follow-up windows and genuine low counts are confounded. Preserve these as
   sensitivity scenarios and require independent follow-up or account evidence
   to identify the mixture; merely planting labels makes it scoreable, not
   identifiable from the observations.
4. **Truth isolation needs an observation allowlist.** The proposed `world.json`
   contains county latent speed/strictness, source propensities and lineage,
   including reserved counties, outside `/reserved/`. A path-substring guard
   would not prevent leakage through that file. Separate public covariates and
   observations from evaluator-only latent metadata, and distinguish oracle
   structural tests from end-to-end text evaluation.
5. **Recovery sweeps are not automatically SBC.** Varying planted constants
   tests recovery; formal SBC additionally needs matched prior-predictive draws
   and inference likelihood, with ranks/coverage evaluated across simulations.
6. **Reconcile stale draft sections and save calibration artifacts.** The
   capacity acceptance test still specifies R² 0.02–0.15 while the revised body
   specifies 0.30–0.60; sample metadata still uses the earlier coefficients and
   marks several now-filled P8 covariates blocked. The claimed 60-seed tuning
   needs its runnable calculation and saved outputs before being treated as a
   verified experiment. This audit has not verified that claimed simulation.

Findings were posted to the shared log as they arose; active owners retain the
original files. Existing software checks completed before the user's retrieval
redirection: 409 repository tests and four audit counterexamples passed, with
one existing generator-test warning. **No further unit-test work is planned in
this retrieval tranche.** No production inference or reserved-world fits ran.

## Continuing collection

The user subsequently prioritized retrieving new material. IHSS timing and
assessment-appeals outcome/staffing sources are being collected as separate
bounded targets, alongside P5 and the P6 broad sweep. This audit is not a claim
that every source or every W2 formula has been checked.
