# Real per-jurisdiction permit timing from the HCD Annual Progress Reports

2026-09-16. Work packet **P0-APR-TIMING** of
[WORK_PACKETS.json](WORK_PACKETS.json), done. Dataset at
`corpus/counties/apr_permit_timing.csv`, quality report at
`corpus/counties/apr_permit_timing_quality.json`, builder at
`pipeline/recon/apr_permit_timing.py`.

## What this is

California's Department of Housing and Community Development requires every
city and county to file an Annual Progress Report. **Table A2** is the
unit-level record: one row per project, 922,104 records, for every jurisdiction
in the state, 2018 through 2025. Each row can carry three dates:

| field | meaning |
|---|---|
| `ENT_APPROVE_DT1` | entitlement approved, the discretionary land-use decision |
| `BP_ISSUE_DT1` | building permit issued |
| `CO_ISSUE_DT1` | certificate of occupancy issued |

So three elapsed clocks are computable per project, for every jurisdiction,
without reading a single document. **This is the external-validity benchmark
the project has been missing.** Everything the synthetic world simulates about
per-jurisdiction process timing can be checked against it.

The dataset produced here aggregates to one row per (jurisdiction, county, year,
unit category, city-or-unincorporated) with counts and the median, p25, p75 and
p90 of each span. 13,008 group rows.

## The headline numbers, for accessory dwelling units

- **281,322 ADU project records.** **35,677** have a usable
  entitlement-to-building-permit span, after discarding 3,615 with the dates out
  of order and 2,551 longer than ten years. **186 jurisdictions have 30 or more**
  such spans: 168 cities and 18 unincorporated county processes.
- **Median of the per-jurisdiction medians: 70 days.** Quartiles 2 and 118 days.
  Maximum 464 days (Woodland, Yolo County).
- **43 of the 186 jurisdictions have a median of exactly 0 days.**

**A note on what "median" means here, because two different statistics are easy
to confuse.** Every per-jurisdiction figure in this report is the **median of
that jurisdiction's yearly medians**, not the median of its pooled projects. The
two differ by a day or two in the large jurisdictions and the yearly version is
the right one for comparing jurisdictions, because it does not let a single
high-volume year dominate. Where a pooled figure is given it is labelled as
such. (An earlier draft of this file reported 35,729 spans, from an exploratory
pass with a different outlier cut; the reproducible figure from the published
builder is 35,677, and it is what an independent re-derivation confirms.)

| the fastest, by volume | days | the slowest with ≥30 spans | days |
|---|---:|---|---:|
| Anaheim (Orange) | 0 | Woodland (Yolo) | 464 |
| Fullerton (Orange) | 0 | Lomita (Los Angeles) | 358 |
| Fremont (Alameda) | 0 | Oxnard (Ventura) | 335 |
| Berkeley (Alameda) | 0 | Gilroy (Santa Clara) | 331 |
| Glendale (Los Angeles) | 14 | Hemet (Riverside) | 306 |

## Three findings

### 1. A zero entitlement-to-permit span tracks ministerial processing, but it is not a clean classifier

**Corrected 2026-09-16 after validating against Table A.** The first version of
this section claimed that a median of zero days means "no separate discretionary
step". Table A carries the jurisdiction's own `PROJECT_TYPE` label, so the claim
could be scored rather than asserted, and it is too strong as stated:

| the jurisdiction's own label | projects | median entitlement-to-permit span | share with a zero span |
|---|---:|---:|---:|
| Ministerial | 20,250 | **9 days** | 45% |
| Discretionary | 1,458 | **108 days** | 29% |

The label separates the two populations powerfully: a twelve-fold difference in
median. But **29% of projects the jurisdiction itself calls discretionary also
have a zero-day span**, and only 45% of ministerial ones do. So at the project
level a zero span is evidence for ministerial processing, not proof of it, and
"no zero span" is weak evidence either way.

Why both directions leak is itself informative. A discretionary project can
have a zero span when the entitlement and the permit are issued together at the
end of a long review, and a ministerial project can have a positive span when
the applicant takes time to return construction documents after approval. The
span measures *administrative simultaneity*, which correlates with the presence
of a discretionary step without being identical to it.

The honest statement is therefore: the entitlement-to-permit span is a **noisy
observable of the decision model's structure**, with a measured confusion
matrix, and `PROJECT_TYPE` is a **sparse ground-truth label** for it, present
on 153,159 of 376,564 joined rows. That pairing, a noisy signal with a partial
label, is exactly the setup the plan's §4 calibration calls for, and it now
exists in real data rather than only in the synthetic world.

The share is stable, not a post-2020 artefact of the ministerial-ADU statutes:

| year | jurisdiction-years with ≥10 spans | median 0 days | share |
|---|---:|---:|---:|
| 2018 | 35 | 7 | 20% |
| 2019 | 44 | 15 | 34% |
| 2020 | 58 | 17 | 29% |
| 2021 | 83 | 24 | 29% |
| 2022 | 96 | 30 | 31% |
| 2023 | 112 | 31 | 28% |
| 2024 | 107 | 31 | 29% |
| 2025 | 110 | 34 | 31% |

### 2. The unincorporated county process is a different process, and the data prove it

`LOS ANGELES` and `LOS ANGELES COUNTY` are separate rows: the city and the
unincorporated area. Over eight years, the city's ADU span has a
median-of-yearly-medians of **58 days across 1,659 projects** (pooled median
57); the county's unincorporated process is **129 days across 1,603** (pooled
median 128). Same statute, same years, adjacent territory, more than double the
elapsed time on either definition.

Across the 18 unincorporated processes with enough data, the spread is as wide
as it gets: Placer, El Dorado and Santa Clara counties are at 0 days, Shasta 62,
Del Norte 68, Alameda County **188**.

A first-pass classifier that keys on the county name alone gets this backwards,
because a row named just `LOS ANGELES` is the city. The builder keys on the word
"county" instead, and the fix changed the unincorporated count from 10 to 18.
Any future analysis of this file has to make the same distinction or it will
pool two different processes.

### 3. County covariates barely predict timing, which strengthens the decision-model framing

Rolling the 186 strong jurisdictions up to their 35 counties and correlating
against the covariate table:

| predictor | correlation with median ADU entitlement-to-permit days |
|---|---:|
| log population | 0.21 |
| log local-government staff | 0.18 |
| rurality code (higher = more rural) | −0.27 |

All weak, and the rural sign is *negative*: more rural counties are slightly
faster, not slower. So the eight-fold variation in permit timing is **not**
explained by county size, staffing or rurality.

**Revised the same day, after the unincorporated-share covariate arrived.** The
correlations above pool city processes with county processes while matching both
to *county* covariates, which is the wrong pairing: a city's process has nothing
to do with its county's staffing. Restricting to the **18 unincorporated county
processes**, where the county's own process is matched to the county's own
covariates, the relationships are two to three times stronger:

| predictor, unincorporated processes only | r | 95% CI | variance explained |
|---|---:|---|---:|
| log unincorporated population | **0.50** | [0.05, 0.79] | 25% |
| ADU uptake per 10,000 unincorporated residents | 0.47 | [0.01, 0.77] | 22% |
| 2024 Democratic vote share | 0.44 | [−0.03, 0.75] | 20% |
| rurality code | −0.34 | [−0.69, 0.15] | 11% |
| *(the earlier mixed estimate, for comparison)* | *0.21* | *[−0.13, 0.51]* | *4%* |

So the first pass understated the covariate relationship by mixing jurisdiction
types. **But do not over-read the revision**: n = 18, the intervals are wide, and
the mixed estimate of 0.21 sits inside the clean interval, so the two are not
statistically distinguishable. The honest summary is that **log population
plausibly explains something between nothing and two thirds of the
between-county timing variance, most likely around a quarter**, and that a
larger sample is needed to say more. The population the county actually governs,
not its total population, is the right regressor.

**For the model**: fit the covariate regression, and expect it to carry a modest
share of the variance rather than most of it. Use the unincorporated population
as the scale variable for county-administered programmes. Most of the variation
remains jurisdiction-specific and must be estimated per jurisdiction or from
process structure.

**And fit it against the right clock.** Packet P9 found that covariates predict
the **applicant** clock roughly twice as strongly as the entitlement clock
(ADU best |r| 0.69 against the clock versus 0.43 against the decision rule;
SFD 0.76 versus 0.57). Since the applicant clock is also the quantity that
matters to the person subject to the process, it is the right regressand for
§4.1's coefficients.

**For the research question**: if timing differences were mostly capacity, the
interesting story would be budgetary. They are not. They look like **policy
choices** about whether to require a discretionary entitlement at all, which is
precisely the decision-model variation the project set out to measure. The
zero-versus-nonzero split predicts far more than any covariate.

## Data quality, honestly

| field | present on | share of 922,104 rows |
|---|---:|---:|
| `BP_ISSUE_DT1` | 626,837 | 68.0% |
| `CO_ISSUE_DT1` | 421,851 | 45.7% |
| `ENT_APPROVE_DT1` | 171,787 | **18.6%** |

The entitlement date is the scarce one. An earlier draft of this section read
that as informative missingness on the ground that a ministerial project has no
entitlement to date. **Packet P9 measured it and that reading is wrong as
stated.** Across 267 jurisdictions, the probability that a project labelled
Ministerial nonetheless carries an entitlement date has p10 of 0.00, a median of
0.50 and p90 of 1.00. A near-uniform spread from never to always is the
signature of a **filing habit of the jurisdiction**, not a property of the
project. Some jurisdictions record a date for every ministerial approval and
some for none.

So the missingness is informative about **who is reporting**, not about whether
a discretionary step exists, and it must be modelled as a jurisdiction-level
reporting propensity rather than as evidence about the process. That is a
different and more awkward object, because it means the observable is filtered
through a per-jurisdiction recording convention before we ever see it.

Other defects, all recorded in the quality file:

- **Dates out of order**: 3,615 entitlement-after-permit, 1,829
  permit-after-occupancy, 598 entitlement-after-occupancy. Discarded from the
  spans, counted in the report.
- **Spans over ten years** discarded: 2,551 entitlement-to-permit, 2,069
  entitlement-to-occupancy, 158 permit-to-occupancy.
- **Duplicate parcel numbers**: 202,999 of 537,504 distinct APNs appear more
  than once. Legitimate for multi-unit projects and re-reported across years,
  but it means the file is not a clean one-row-per-project register and a naive
  count of projects will be inflated.

## The applicant's clock, from the Table A join

**Added 2026-09-16.** Table A, the application register, carries
`APP_SUBMIT_DT` on **100% of its 358,264 rows**. Joining it to Table A2 on
(jurisdiction, parcel number, unit category) gives a much longer clock than the
permit records alone. Builder: `pipeline/recon/apr_join_clocks.py`; output
`corpus/counties/apr_applicant_clock.csv`, 8,457 group rows.

**Naming correction, from the cross-scoping audit.** An earlier draft called this
"the applicant's clock" and "the clock an applicant actually experiences". That
overstates it. HCD defines `APP_SUBMIT_DT` as the application date **or the date
the local government determined the application complete, when the initial
submission was incomplete**. So the measured span is
**complete-application to building permit**, and in every case that arrived
incomplete it *excludes* the earlier completeness back-and-forth.

Two consequences. The 156-day figure is a **lower bound** on what applicants
live through, not an estimate of it, and the excluded period is exactly the
intake-and-resubmission phase that documents describe worst — so the true
applicant experience is longer than measured here by an unknown amount that
itself varies by jurisdiction. And it must **not** be used as a direct target
for end-to-end synthetic burden without modelling the completeness gap
separately.

**The complete-application clock is two to three times the permit-record
clock**, and is itself a lower bound on the applicant's full experience.

| clock | median of per-jurisdiction medians | jurisdictions with ≥30 spans |
|---|---:|---:|
| entitlement → building permit | 70 days | 186 |
| **complete application → building permit** | **156 days** | **275** |

| jurisdiction | spans | median complete-application to permit |
|---|---:|---:|
| Los Angeles (city) | 51,293 | 152 days |
| San Diego (city) | 4,854 | 270 days |
| **Los Angeles County (unincorporated)** | 4,590 | **331 days** |
| Long Beach | 2,570 | 170 days |
| Garden Grove | 1,730 | 120 days |
| Anaheim | 1,651 | 0 days |

Two things follow. First, **only 11 of 275 jurisdictions have a zero median on
this clock**, against 43 of 186 on the entitlement clock: almost nowhere is
genuinely instant once the applicant's own waiting is counted. Second, this is
direct evidence for the audit's finding that the model underestimates
end-to-end duration. Anyone reconstructing a process from permit records alone
sees 70 days where the applicant lived through 156. The missing time is
pre-entitlement: intake, completeness review and the applicant's own
resubmissions, which is precisely the part that published documents describe
worst and forum posts describe best.

The join also yields **per-jurisdiction outcomes**: 194,347 approved, 54,382
pending, 1,219 withdrawn, 89 disapproved. Disapproval is vanishingly rare for
ADUs, which is what a ministerial statute should produce, so denial rate is the
wrong outcome to model for this programme.

**Corrected by packet P9**: an earlier draft added "withdrawal and the pending
backlog are the informative ones". Withdrawal is not. It is 0.66% of ADU
outcomes and **82 of 193 jurisdictions report exactly zero**, with a correlation
against the clock of only 0.125. That is a reporting variable, not an
abandonment signal. **The pending backlog is the usable one**: 38.2% for ADUs
and 56.7% for multifamily, and it is what an abandonment channel should be
calibrated against.

**Join quality.** 376,564 of 922,104 Table A2 rows matched an application, a
41% match rate. The unmatched rows are mostly permits whose application predates
the reporting window or whose parcel number differs between the two tables.
58,090 duplicate-key hits were resolved by taking the earliest submittal.
`PROJECT_TYPE` is present on 153,159 of the joined rows, so the ministerial
label covers 41% of the joined set, not all of it.

## What remains in this packet
- The **data dictionaries** (DOCX resources on the same open-data package)
  should be read to confirm each date field's official definition and known
  quality caveats before any of this is published.
- The same treatment for the other unit categories. Single-family detached is
  250,293 rows and would give a second, independent process to compare against,
  with the advantage that it is discretionary nearly everywhere.

## Why this changes the plan's sequencing

The plan ranked ADU third among candidate programs behind CalFresh. On this
evidence it should be **first**: it is the only candidate where per-jurisdiction,
per-project elapsed timing already exists in a single downloadable file, for all
58 counties and every city, over eight years, with a structural signal in it
that maps directly onto the decision model. CalFresh's CF 296 may yet prove
comparable, but it is Excel, per fiscal year, and its per-county breakdown is
still unconfirmed.
