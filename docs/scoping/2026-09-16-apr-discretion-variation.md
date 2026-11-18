# The discretion residual, measured on real data: who calls an ADU ministerial?

2026-09-16. Work packet **P9-DISCRETION-REAL** of
[WORK_PACKETS.json](WORK_PACKETS.json), done. Builder at
`pipeline/recon/apr_discretion.py`, dataset at
`corpus/counties/apr_discretion_by_jurisdiction.csv` (10,268 rows, one per
jurisdiction × county × reporting year × unit category), quality report at
`corpus/counties/apr_discretion_quality.json`. Companion to
[the APR permit-timing report](2026-09-16-apr-permit-timing.md), whose finding 3
(county covariates barely predict timing) this builder reproduces exactly as a
cross-check before extending it.

## What this measures and why it is the instrument

The project's thesis is that a statute underdetermines a decision function, that
each jurisdiction resolves the underdetermination its own way, and that
cross-jurisdiction disagreement is therefore the empirical measure of the
statute's discretion — the plan's §4.3 `omega_p`. Everywhere else in this repo
that quantity is synthetic.

HCD APR **Table A** carries `PROJECT_TYPE`, the jurisdiction's own statement,
per application, of whether its process routed that application through a
discretionary step ("Discretionary") or not ("Ministerial"). It is not a proxy
and not an inference: it is **516 of the 529 jurisdictions in the file**, each
declaring in a mandatory state filing how it reads the same statute. 164,222 of
358,264 applications carry it.

Two jurisdictions disagreeing on that label are disagreeing about the decision
function. One jurisdiction that labels *some* of its own ADU applications each
way is running a **conditional** rule, which is a stronger claim about where the
discretion sits: in a predicate evaluated case by case, not in a fixed
jurisdiction effect.

## The five headline numbers

1. **For ADUs the distribution is not bimodal; it is a spike.** 89.1% of the 596
   jurisdiction-years with ≥20 labelled ADU applications are within 0.05 of
   all-ministerial; the pooled share is 0.974. Only 1.5% are all-discretionary.
2. **The residual disagreement is nonetheless real: 45× binomial noise.** The
   observed cross-jurisdiction variance of the ADU ministerial share is 0.02121
   against a 0.00047 expectation under one statewide rule. It is concentrated —
   the top 10 jurisdictions hold 71% of all discretionary ADU applications, and
   156 of 236 jurisdictions never file a single one.
3. **The label predicts timing *within* a jurisdiction and almost nothing
   *between* jurisdictions.** Within a jurisdiction-year, a discretionary ADU is
   a median **+104 days** slower (95% bootstrap [+3, +185], 13 of 17
   jurisdictions, sign-test p = 0.021). Across jurisdictions the pooled share
   correlates with the median clock at only **−0.163** (n = 250).
4. **The matched city/county pairs prove it, in both directions.** Los Angeles
   city and Los Angeles County's unincorporated area **agree** on the rule
   (0.9898 vs 0.9996 ministerial) and differ by **243 days** on the median
   applicant clock (140 vs 383). Santa Cruz city and Santa Cruz County
   **disagree completely** (0.9623 vs 0.0000) and differ by only 38 days (190 vs
   228). San Mateo reverses the sign outright: its fully *discretionary* city is
   **140 days faster** than its fully *ministerial* county (138 vs 278).
5. **Covariates predict the ADU decision rule worse than they predict its
   timing.** Best |r| against the county ministerial share is 0.43; against the
   applicant clock, 0.69. For single-family detached, covariates predict both
   moderately (income −0.57 on the share, education +0.76 on the clock).

Together: for ADUs the statute has **closed the stated rule and not the realised
process**. That is a different finding from the one the packet was set up to
expect, and it relocates the discretion residual from the decision label to the
queue behind it.

## 1. The ministerial share, per jurisdiction-year

### The statute is doing the work, and it does it by project size

Pooling every labelled application, all years, all jurisdictions:

| unit category | labelled applications | ministerial share |
|---|---:|---:|
| ADU | 92,696 | **0.9743** |
| Mobile home | 2,944 | 0.9412 |
| Single-family detached | 54,228 | 0.8779 |
| 2 to 4 units | 6,404 | 0.8234 |
| Single-family attached | 2,159 | 0.6860 |
| **5+ units** | 5,791 | **0.4835** |

A near-monotone gradient in project size. This is what a statute that mandates
by-right ADU approval looks like from the administrative side, and multifamily
is the genuinely contested category.

**One expectation in the packet brief is wrong and the data say so plainly.**
Single-family detached was expected to be "discretionary nearly everywhere". It
is not: 87.8% of labelled SFD applications are Ministerial, and 59.9% of SFD
jurisdiction-years are within 0.05 of all-ministerial. This is legally
unsurprising on reflection — a house in an R-1 zone needing no variance is a
building-permit matter — but it means SFD is a *weaker* contrast than assumed.
The real contrast is **5+ units**, so the builder reports it by default
(`--cats ADU,SFD,5+`).

### Shape of the distribution, jurisdiction-years with ≥20 labelled applications

| bucket for the ministerial share | ADU (596 cells) | SFD (314) | 5+ (43) |
|---|---:|---:|---:|
| near 0, ≤ 0.05 — all discretionary | 9 (1.5%) | 26 (8.3%) | 8 (18.6%) |
| 0.05 – 0.35 | 1 (0.2%) | 18 (5.7%) | 6 (14.0%) |
| 0.35 – 0.65 — genuinely mixed | 12 (2.0%) | 24 (7.6%) | 12 (27.9%) |
| 0.65 – 0.95 | 43 (7.2%) | 58 (18.5%) | 8 (18.6%) |
| near 1, ≥ 0.95 — all ministerial | **531 (89.1%)** | 188 (59.9%) | 9 (20.9%) |
| **interior (0.05 < share < 0.95)** | **56 (9.4%)** | **100 (31.8%)** | **26 (60.5%)** |
| pooled share | 0.977 | 0.911 | 0.622 |

ADU is unimodal at 1, with a 9.4% interior tail. SFD is bimodal-with-a-lean.
5+ is the only category that is genuinely spread out, and its modal bucket is
the middle one. **Bimodality is a property of the project type, not of
California's jurisdictions.**

### Is the spread real, or is it small-sample noise?

Under a single statewide decision rule with probability *p*, each cell's share
would vary only by sampling, with variance *p*(1−*p*)/*n*. The plan's §4.3
discretion residual is the excess:

| category | observed variance | binomial expectation | ratio |
|---|---:|---:|---:|
| ADU | 0.02121 | 0.00047 | **45×** |
| SFD | 0.10674 | 0.00167 | **64×** |
| 5+ | 0.12951 | 0.00610 | **21×** |

So the disagreement is not sampling noise for any category. For ADU it is large
in *relative* terms and small in absolute terms: real, and concentrated in few
places. 2,059 discretionary ADU applications in these cells, 71% of them in ten
jurisdictions, and only 80 of 236 jurisdictions file even one.

### Pooled over years: who actually dissents, and who runs a conditional rule

291 jurisdictions have ≥20 labelled ADU applications across all years.
248 (85%) are near-1, **5 (2%) are near-0**, and **38 (13%) are interior**.

| persistently discretionary on ADUs | county | labelled | share | median clock |
|---|---|---:|---:|---:|
| Simi Valley | Ventura | 167 | 0.000 | 184 d |
| Monterey County (unincorporated) | Monterey | 105 | 0.010 | 208 d |
| Half Moon Bay | San Mateo | 39 | 0.000 | 328 d |
| Santa Cruz County (unincorporated) | Santa Cruz | 25 | 0.000 | 228 d |
| San Mateo | San Mateo | 25 | 0.000 | 138 d |

Five jurisdictions out of 291 with enough ADU volume to measure. That is the
entire population of ADU processes that self-report a discretionary route as
their standing rule.

The interior group is more interesting, because a share strictly between 0 and 1
means the same office routed some ADU applications one way and some the other:

| conditional ADU rule | county | labelled | share | median clock |
|---|---|---:|---:|---:|
| Oakland | Alameda | 827 | 0.915 | 176 d |
| **San Francisco** | San Francisco | 555 | **0.335** | 423 d |
| Bakersfield | Kern | 517 | 0.938 | 0 d |
| Santa Barbara | Santa Barbara | 510 | 0.890 | 271 d |
| Monterey | Monterey | 410 | 0.941 | 0 d |
| San Luis Obispo County | San Luis Obispo | 348 | 0.899 | 168 d |
| Arcadia | Los Angeles | 343 | 0.694 | 200 d |
| Laguna Beach | Orange | 322 | 0.929 | 180 d |

San Francisco is the substantively important case: two thirds of its ADU
applications go through a discretionary step, on 555 labelled applications, and
its median applicant clock is 423 days — the slowest of any high-volume ADU
process in the state. **A conditional rule is exactly the structure the plan's
§4.3 ordered-logit is written for**: the jurisdiction has a predicate, the
predicate fires on a subset, and the subset share is the estimand.

### The trap, turned into an instrument

`LOS ANGELES` is the city; `LOS ANGELES COUNTY` is the unincorporated area. Many
California counties contain a same-named city, so these are **matched pairs**:
one statute, one county, one housing market, two administrations. The builder
reports every pair with ≥20 labelled applications on both sides.

| county | city share | city clock | unincorporated share | unincorporated clock |
|---|---:|---:|---:|---:|
| Los Angeles | 0.9898 | 140 d | 0.9996 | **383 d** |
| San Diego | 0.9865 | 216 d | 0.9982 | 134 d |
| Sacramento | 0.9847 | 189 d | 0.9730 | 136 d |
| **Santa Barbara** | 0.8902 | 271 d | **0.4062** | 237 d |
| Fresno | 0.9980 | 259 d | 1.0000 | 77 d |
| **Monterey** | 0.9415 | 0 d | **0.0095** | 208 d |
| **Santa Cruz** | 0.9623 | 190 d | **0.0000** | 228 d |
| Santa Clara | 1.0000 | 218 d | 0.9749 | 247 d |
| San Bernardino | 1.0000 | 176 d | 1.0000 | 236 d |
| **San Mateo** | **0.0000** | 138 d | 1.0000 | 278 d |
| Napa | 0.6364 | 233 d | 1.0000 | 140 d |
| Tulare | 1.0000 | 64 d | 1.0000 | not computable |

Read the bolded rows in both directions. **Four pairs disagree about the rule
almost completely** under the identical statute in the identical county —
Monterey 0.94 vs 0.01, Santa Cruz 0.96 vs 0.00, San Mateo 0.00 vs 1.00, Santa
Barbara 0.89 vs 0.41. So the statute is genuinely read differently in adjacent
territory.

**And the rule does not determine the clock.** Scoring each pair on whether the
more-ministerial side is the faster side: **6 of the 12 order as the label
predicts, 4 order the opposite way** (Los Angeles, Sacramento, Santa Barbara, San
Mateo), one has no share difference to test (San Bernardino) and one has no
county clock (Tulare). The four reversals are not marginal. Los Angeles *agrees*
on the rule to within 0.01 and differs by 243 days. Santa Barbara's
more-discretionary unincorporated process is the *faster* one, 237 against 271
days. San Mateo reverses outright: the all-discretionary city is 140 days faster
than the all-ministerial county. And where the rule disagreement is total, the
time gap can be small — Santa Cruz, 0.96 against 0.00, is 190 against 228 days.

This single table contains both halves of the finding, and they are in tension
with each other by design: cross-jurisdiction disagreement about the decision
rule is real, and it is not what makes one jurisdiction slower than another.

Aggregated: cities are at a pooled ADU ministerial share of 0.979 over 532
jurisdiction-years, unincorporated processes 0.962 over 64. Nearly identical on
the stated rule. The unincorporated processes are the slow ones on the clock
(per the prior report), so the kind-of-jurisdiction effect is a timing effect,
not a decision-rule effect.

## 2. Over time: the question as posed is not computable, and the reason matters

**`PROJECT_TYPE` did not exist as a populated field before 2022.** HCD phased it
in; it is 100% populated for the 2023–2025 reporting years, 21.4% for 2022, and
under 1.3% before that.

| reporting year | applications | labelled | coverage | ministerial share of labelled |
|---|---:|---:|---:|---:|
| 2018 | 30,143 | 238 | 0.8% | 0.618 |
| 2019 | 44,381 | 245 | 0.6% | 0.661 |
| 2020 | 37,132 | 235 | 0.6% | 0.647 |
| 2021 | 44,004 | 583 | 1.3% | 0.767 |
| 2022 | 50,512 | 10,829 | 21.4% | 0.923 |
| 2023 | 49,045 | 49,045 | **100%** | 0.909 |
| 2024 | 47,141 | 47,141 | **100%** | 0.905 |
| 2025 | 55,906 | 55,906 | **100%** | 0.932 |

The 2018–2021 rows are not a sample of California; they are 82
jurisdiction-year-category groups of voluntary early filers (Adelanto, Oroville,
Tehama County, Culver City, Soledad and a dozen others). So:

> **Not computable: the 2018–2025 statewide trend in the ministerial share, and
> the before/after natural experiment around the 2020–2021 ADU statutes.** The
> label does not exist for the "before" period. Any pre-2022 series would be a
> self-selected handful of filers, and the ascending 0.618 → 0.923 sequence above
> is a composition effect of who chose to fill the field, not a policy trend.

**The obvious substitute was tested and rejected, and the reason it fails is a
finding in its own right.** "A ministerial project has no entitlement to date"
suggests using entitlement-date missingness as a proxy with full historical
coverage. Scored per application against the label:

| the jurisdiction's own label | matched applications | carry an entitlement date |
|---|---:|---:|
| Ministerial | 88,909 | **35.4%** |
| Discretionary | 6,254 | **77.6%** |

A 42-point separation, so the proxy *is* informative in aggregate — enough that a
method-of-moments inversion of a statewide rate looks tempting. It still cannot
be used, because the class-conditional rate is not a constant. Across the 267
jurisdictions with ≥30 matched ministerial applications, P(entitlement date |
Ministerial) has **p10 = 0.00, median = 0.50, p90 = 1.00, with 36 jurisdictions
at exactly 0.00 and 58 at exactly 1.00**.

That is not a project attribute with noise; it is a filing habit. Whether a
jurisdiction writes an entitlement date on a ministerial ADU is a
jurisdiction-level convention that swings the whole way from never to always. So
the proxy cannot be inverted per jurisdiction, and it cannot be validated for the
pre-2022 period at all, because the label needed to calibrate it does not exist
there.

**This qualifies the prior report's reading of the same field.** That report
called the 81.4% missingness of `ENT_APPROVE_DT1` "informative missingness, not
noise", on the grounds that a ministerial project has no entitlement to date. The
first half is right — missingness is informative — but the information is
substantially about *the jurisdiction's reporting convention*, not only about the
project's route. Both signals are in there and this file cannot separate them
without a jurisdiction-level reporting-propensity term, which is the same
`pi(kind, c)` structure the plan's §4.2 specifies for documents.

### What *is* computable: 2022–2025, and the label is sticky

| pooled ministerial share | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| ADU | 0.9896 | 0.9716 | 0.9650 | 0.9808 |
| SFD | 0.7403 | 0.8587 | 0.8710 | **0.9183** |
| 5+ | 0.5403 | 0.4714 | 0.4397 | 0.5196 |

The 2022 column rests on 22 jurisdictions for SFD and 20 for ADU and should be
read as indicative only; 2023–2025 each rest on 360–390 jurisdictions.

ADU is flat and saturated. **SFD is the category that moved**: +6 points from
2023 to 2025 on 15,000–21,000 labelled applications a year across ~380
jurisdictions, which is the direction the by-right single-family statutes (SB 9
and successors) predict. This file cannot attribute it: the same three years also
saw the reporting template settle, and a jurisdiction that changed how it fills
the field would look identical.

At the jurisdiction level the label is very sticky:

| category | consecutive jurisdiction-year pairs (≥20 labelled both years) | median change in share | crossed 0.5 | 0.2↔0.8 flips |
|---|---:|---:|---:|---:|
| ADU | 344 | +0.000 | 8 (2.3%) | 4 |
| SFD | 163 | +0.000 | 18 (11.0%) | 7 |
| 5+ | 17 | +0.008 | 4 (23.5%) | 1 |

Stickiness is itself a modelling result: a jurisdiction effect on the decision
rule is a nearly-constant quantity year over year, so the hierarchical model can
treat it as a jurisdiction-level parameter rather than a jurisdiction-year one,
and the effective sample size for the discretion residual is **jurisdictions,
not jurisdiction-years**.

> **Not computable: the before/after timing effect at switching jurisdictions.**
> Only 4 ADU flips and 7 SFD flips exist, and of those only 2 and 1 respectively
> have ≥5 measured spans on both sides — below the 4 needed for the bootstrap.
> The flips that do exist are listed in the builder output (Arcadia 2023→2024,
> Marin County 2024→2025 with the clock falling 213 → 130 days; Jurupa Valley
> flipping twice in three years, which looks like a reporting change rather than
> a policy change). This is the single clearest candidate for a follow-up: it
> needs either the 2026 filing or the per-ordinance record, not more of this file.

## 3. Does the label predict the applicant's clock?

Within a (jurisdiction, year, category) cell with ≥5 measured
submission-to-building-permit spans in **each** arm:

| | ADU | SFD | 5+ |
|---|---:|---:|---:|
| measured spans, ministerial | 45,852 | 24,229 | 319 |
| measured spans, discretionary | 801 | 1,788 | 216 |
| cells with both arms | 21 | 15 | 4 |
| jurisdictions | 17 | 13 | **1** |
| median of paired differences, disc − min | **+122.5 d** | **+132.5 d** | −169.2 d |
| 95% bootstrap | [+14, +190] | [+22, +322] | [−380, +173] |
| collapsed to one per jurisdiction | **+104 d** | +91 d | not computable |
| 95% bootstrap | [+3, +185] | [+22, +229] | — |
| slower / faster cells | 16 / 4 | 12 / 3 | 1 / 3 |
| sign-test p, per jurisdiction | **0.021** | 0.092 | — |
| permit-within-365-days rate, disc − min | **−29.6 pp** [−39.9, −6.1] | −18.6 pp [−43.9, −8.9] | −2.4 pp |

**The ADU result is solid and the SFD result is suggestive.** A discretionary ADU
takes about three and a half months longer than a ministerial one in the same
office in the same year, and is about 30 percentage points less likely to reach a
building permit within a year of submission. The 5+ column is reported and
should not be used: every cell is Los Angeles city.

The largest ADU cells, which drive the point:

| jurisdiction | year | ministerial n / median | discretionary n / median |
|---|---|---:|---:|
| Los Angeles (city) | 2022 | 5,422 / 159 d | 28 / **525 d** |
| Los Angeles (city) | 2023 | 4,481 / 153 d | 18 / 427 d |
| Los Angeles (city) | 2024 | 4,412 / 128 d | 17 / 434 d |
| Los Angeles (city) | 2021 | 510 / 360 d | 20 / 736 d |
| Sacramento | 2023 | 197 / 144 d | 9 / 334 d |
| Santa Barbara | 2023 | 76 / 270 d | 23 / 454 d |
| San Diego | 2024 | 98 / 236 d | 10 / 275 d |
| Santa Cruz | 2023 | 65 / 204 d | 5 / 308 d |

### What is confounded here, stated exactly

- **This is observational.** Nothing assigns the label; the jurisdiction does,
  and it may assign it *because* a project is hard. The effect is an upper bound
  on any causal reading.
- **The complexity confound is measured, and for ADUs it is small.** Mean
  proposed units in these cells: **1.35 ministerial vs 1.30 discretionary**. For
  SFD it is 1.58 vs 2.08, mild. For 5+ it is 47.6 vs 106.8 — the discretionary
  multifamily projects are more than twice the size, which alone disqualifies
  the 5+ comparison. So for ADUs the difference is not explained by project size
  on the only complexity proxy Table A carries. It could still be explained by
  unobserved difficulty: a non-conforming lot, a historic district, a coastal
  zone. `HISTORIC_SITES` is in Table A and is the obvious next control.
- **Right-censoring attenuates the estimate.** Only projects that reached a
  permit by 2025-12-31 contribute a span, and the slower arm loses more of its
  mass to censoring. Both arms sit in the same cohort year, so the direction of
  the bias is toward zero. The permit-within-365-days rate is the
  censoring-robust version and it agrees, which is the main reason to believe the
  sign.
- **The rate is a lower bound, not a rate.** Only 40.8% of Table A2 rows match an
  application, so "no permit observed" pools "no permit yet" with "permit exists
  under a different parcel number". Comparable between arms of the same cell;
  not interpretable as an absolute probability.
- **Los Angeles city supplies 4 of 21 ADU cells.** Collapsing to one observation
  per jurisdiction is the guard; it moves the estimate from +122.5 to +104 days
  and the interval to [+3, +185], still excluding zero.
- **The estimate survives a stricter threshold.** At
  `--min-labelled 50 --min-arm 8` the ADU per-jurisdiction estimate is
  **+122.5 days [+3.2, +190.0]** on 11 jurisdictions. Tightening the cell
  requirement moves the point estimate up and keeps the interval clear of zero,
  which is the opposite of what a small-sample artefact does.

### The between-jurisdiction result, which is the important one

| comparison | ADU | SFD |
|---|---:|---:|
| **within** jurisdiction-year, days per discretionary label | +104 [+3, +185] | +91 [+22, +229] |
| **between** jurisdictions, pooled share vs median clock, pearson | **−0.163** | −0.333 |
| same, spearman | −0.110 | −0.328 |
| n jurisdictions | 250 | 147 |

The label separates projects inside an office and barely orders offices against
each other. Los Angeles city and its county's unincorporated area are the
extreme case: agreement to 0.01 on the rule, 243 days apart on the clock.

**This is the substantive result of the packet.** For ADUs the statute has
successfully standardised the *stated* decision rule across 516 filing
jurisdictions while leaving a 25-to-423-day spread in *realised* county median
duration. A model that
represents per-jurisdiction variation only as a decision-rule variable will
therefore fit this program badly. The variation that survives standardisation
lives in the queue, the intake, the completeness review and the resubmission
loop — precisely the part the prior report showed is invisible in permit records
(70 days) and visible on the applicant clock (156 days).

## 4. Do county covariates predict the decision rule?

Rolled up to counties with ≥100 labelled applications, against the 26 populated
columns of `corpus/counties/ca_counties_covariates.csv`. Pearson first, Spearman
in brackets.

### ADU, 30 counties; share range 0.335 to 1.000, clock range 25 to 423 days

| predictor | vs ministerial share | vs applicant clock |
|---|---:|---:|
| log population | +0.098 [+0.295] | +0.335 [+0.506] |
| log local-government employment | +0.058 [+0.276] | +0.318 [+0.477] |
| local-government staff per 1k pop | −0.213 [−0.244] | −0.251 [−0.409] |
| rurality code (higher = more rural) | +0.105 [−0.166] | −0.398 [−0.543] |
| median household income | −0.282 [−0.218] | +0.468 [+0.534] |
| poverty rate | +0.008 [+0.002] | −0.265 [−0.282] |
| pct bachelor's degree | **−0.427** [−0.329] | +0.583 [+0.532] |
| log population density | −0.374 [+0.040] | **+0.688** [+0.642] |

### SFD, 42 counties; share range 0.090 to 1.000, clock range 0 to 431 days

| predictor | vs ministerial share | vs applicant clock |
|---|---:|---:|
| log population | −0.314 [−0.556] | +0.346 [+0.323] |
| log local-government employment | −0.298 [−0.547] | +0.321 [+0.296] |
| local-government staff per 1k pop | +0.285 [+0.522] | −0.316 [−0.455] |
| rurality code | +0.395 [+0.575] | −0.306 [−0.345] |
| median household income | **−0.572** [−0.713] | +0.636 [+0.604] |
| poverty rate | +0.350 [+0.480] | −0.522 [−0.508] |
| pct bachelor's degree | −0.564 [−0.651] | **+0.755** [+0.756] |
| log population density | −0.414 [−0.640] | +0.482 [+0.441] |

**The answer to the packet's question is: no for ADU, moderately yes for SFD, and
in both cases covariates predict the clock better than the rule.** ADU best
|r| is 0.43 against the share and 0.69 against the clock. SFD best |r| is 0.57
against the share and 0.76 against the clock. For 5+, on 11 counties, rurality
correlates with the share at +0.65 — the rural counties are the ones still
requiring discretionary review of multifamily — but 11 counties is too few to
lean on and the 5+ clock correlation is **not computable** (only 2 counties have
≥3 clock medians).

The SFD signs are coherent and worth stating plainly: **poorer, more rural,
less-educated counties are more likely to call single-family housing
ministerial**, and richer, denser, better-educated counties take longer. That is
a real, interpretable gradient and the first covariate finding in this project
with an |r| above 0.5.

### A reconciliation the prior report requires

The prior report concluded that "county covariates barely predict timing
(r ≈ 0.2)". The clock columns above go to 0.69. That is not a contradiction and
not a revision: **it is a different clock.** The builder recomputes the prior
report's construction exactly — the ADU *entitlement*-to-permit median, per
jurisdiction with ≥30 spans, rolled to the county, 35 counties — and reproduces
it to three decimals:

| predictor | entitlement→permit clock (prior construction, 35 counties) | submission→permit clock (this report, 30 counties) |
|---|---:|---:|
| log population | **+0.212** | +0.335 |
| log local-government employment | **+0.180** | +0.318 |
| rurality code | **−0.269** | −0.398 |
| log population density | +0.334 | +0.688 |
| pct bachelor's degree | +0.308 | +0.583 |

So the prior finding stands for the clock it measured, and a **new** finding
follows: the strongest covariates roughly double in magnitude when the target is
the applicant-experienced clock instead of the permit-record clock — density
+0.33 → +0.69, education +0.31 → +0.58 — while the weak ones stay weak
(population +0.21 → +0.34). The two columns are not a perfectly controlled
comparison: the county sets differ (35 versus 30) because they have different
inclusion rules, with 27 counties common to both. The mechanism is the obvious one
and it is the same one the prior report identified — the missing time is
pre-entitlement intake and resubmission, and *that* is where capacity and
caseload bite. The permit-record clock starts after the queue and so is nearly
capacity-free by construction.

**For the plan's §4.1**: the covariate regression is worth more than the prior
report implied, but only if the modelled quantity is the applicant's end-to-end
duration rather than the permit-record span. Fitted against the wrong clock it
recovers `gamma` near zero and looks useless.

## 5. Outcome structure and the abandonment channel

| | ADU | SFD | 5+ |
|---|---:|---:|---:|
| applications | 167,720 | 146,621 | 13,701 |
| status stated | 130,538 (77.8%) | 90,468 (61.7%) | 8,748 (63.8%) |
| approved | 61.04% | 72.87% | 42.34% |
| **pending** | **38.20%** | 26.62% | **56.70%** |
| withdrawn | 0.66% | 0.44% | 0.73% |
| disapproved | 0.09% | 0.07% | 0.23% |

Per-jurisdiction, among those with ≥100 stated outcomes:

| | ADU (193 jurisdictions) | SFD (116) |
|---|---:|---:|
| median withdrawal share | 0.0035 | 0.0000 |
| p90 / max withdrawal share | 0.0273 / 0.1148 | 0.0182 / 0.5820 |
| jurisdictions reporting **zero** withdrawals | **82 (42%)** | 66 (57%) |
| jurisdictions with any disapproval | 24 | 10 |
| median / p90 pending share | 0.293 / 0.678 | 0.256 / 0.663 |
| withdrawal share vs median clock (pearson / spearman) | 0.125 / 0.236 | 0.093 / 0.299 |
| pending share vs median clock (pearson / spearman) | 0.079 / 0.121 | **0.615 / 0.601** |

**The abandonment hypothesis is not confirmed by this file, and the reason is a
reporting problem rather than a behavioural one.** The correlation between a
jurisdiction's withdrawal share and its median applicant clock is +0.125 Pearson
and +0.236 Spearman on 188 ADU jurisdictions: the right sign, too weak to build
on. The blocker is that **42% of ADU jurisdictions report exactly zero
withdrawals**, which is not credible as behaviour across hundreds of
applications and is much more likely to mean the jurisdiction does not track
withdrawn applications in its APR. Tracy reports 58.2% of its 122 SFD
applications withdrawn; San Anselmo 11.5% of 122 ADUs. Ranges like that across
otherwise similar jurisdictions are a reporting-practice variable.

The highest-withdrawal ADU jurisdictions are nonetheless slow ones, which is
what the mechanism predicts:

| jurisdiction | county | withdrawal share | stated outcomes | median clock |
|---|---|---:|---:|---:|
| San Anselmo | Marin | 0.115 | 122 | 218 d |
| Santa Maria | Santa Barbara | 0.113 | 1,276 | 199 d |
| Hawthorne | Los Angeles | 0.074 | 351 | 131 d |
| Arcadia | Los Angeles | 0.054 | 480 | 200 d |
| Downey | Los Angeles | 0.051 | 1,063 | 172 d |
| Bell | Los Angeles | 0.043 | 164 | 365 d |

**What to model instead.** Disapproval is 0.09% of ADU outcomes and absent from
169 of 193 jurisdictions; the prior report's conclusion that denial rate is the
wrong outcome for this program is confirmed on the application register. The
informative outcome is the **pending backlog**: 38.2% of ADU and 56.7% of 5+
applications sit unresolved. For SFD the pending share correlates with the clock
at 0.615, which is partly mechanical — a slow process has more work in progress
at any snapshot — and is therefore better treated as a *second observable of
duration* than as an independent outcome. For ADU the same correlation is only
0.079, which is a puzzle worth one follow-up: it suggests ADU pending shares are
dominated by how a jurisdiction closes out its records rather than by its speed.

So W2's abandonment channel should be specified, per the plan's §9.5, but it
should be calibrated against **the pending backlog and the censored permit rate**,
not against reported withdrawals. A disclosure/reporting-propensity term on the
withdrawal field is required if that field is used at all — this is the same
`pi(kind, c)` structure as §4.2, applied to a data field instead of a document.

## Data quality, honestly

Everything below is in `corpus/counties/apr_discretion_quality.json`.

- **`PROJECT_TYPE` coverage is all-or-nothing per jurisdiction-year.** Of 2,582
  ADU jurisdiction-years, 1,138 are fully labelled, 1,444 carry no label at all,
  and **zero are partially labelled**. The missingness is a filing decision, not
  a per-project one. Any model of the label must treat it as
  missing-at-jurisdiction-year, which also means a jurisdiction-year with a label
  is a jurisdiction-year that filed on the current HCD template — a possible
  correlate of administrative capacity that is not controlled for here.
- **Join and dedup.** 358,264 Table A rows → 300,171 (jurisdiction, APN, unit
  category) keys; 58,090 duplicate-key hits resolved to the earliest submittal,
  3 rows without a key, 0 without a submittal date. 376,564 of 922,104 Table A2
  rows matched (40.8%), covering 219,601 distinct application keys.
- **One span per application, not one per permit record.** A multi-unit project
  files many A2 rows against one parcel; this builder takes the earliest building
  permit per application key. Span counts here are therefore *lower* than in
  `corpus/counties/apr_applicant_clock.csv`, which counts per A2 row, and the two
  files are not interchangeable. Every per-jurisdiction clock figure in this
  report is a median of that jurisdiction's yearly medians, matching the
  convention set in the prior report.
- **Impossible dates.** 69 matched keys carry a building-permit date after the
  end of the last reporting year (there is a 2048 and a 2109). Left to itself
  this set the observation window 22 years into the future and silently broke the
  365-day follow-up rate; the builder now caps the window at the end of the last
  reporting year, 2025-12-31. 254 applications have a submittal date outside
  [2010-01-01, 2025-12-31] (there is an 1899 and a 2819) and are excluded from the
  follow-up eligibility count. Spans are additionally cut at 10 years and at
  negative values, as in the sibling builders.
- **Duplicate and placeholder parcel numbers.** 35,858 Table A rows repeat a
  parcel number already seen inside their own (jurisdiction, county, year,
  category) group, and 58,090 hits collide on the (jurisdiction, APN, category)
  join key and were resolved to the earliest submittal. Worse, some
  jurisdictions file a placeholder: Adelanto's 195 SFA applications for 2021
  carry **one** distinct APN between them. `n_distinct_apn` is in the output CSV
  so this is detectable per row; it makes any per-parcel join unreliable for
  those jurisdictions and it is why the timing analysis is restricted to cells
  with enough matched spans rather than run on everything.
- **City versus unincorporated.** The `is_unincorporated` test is imported from
  `apr_join_clocks.py` and keys on the word "county", not on matching the county
  name: 273,152 city rows, 85,112 unincorporated. `LOS ANGELES` and
  `LOS ANGELES COUNTY` are never pooled here, and §1's matched-pair table is only
  meaningful because they are not.

## What this changes for the plan

1. **§4.3's discretion residual is measurable and it is small for ADU.** The
   estimand exists in real data, with a variance ratio (45×) that shows it is not
   noise, and a location (five standing dissenters plus 38 conditional
   jurisdictions out of 291). A synthetic world calibrated to a *wide* dispersion
   of readings on a strongly-ministerial statute would be miscalibrated: the real
   dispersion is a spike with a thin, concentrated tail. §3.3's "discretion
   dispersion at 58 draws" should be re-specified to reproduce a mass point plus a
   tail, not a broad distribution.
2. **Route structure, not the decision label, carries the cross-jurisdiction
   variation for this program.** The between-jurisdiction correlation of the
   stated rule with realised duration is −0.163. Per the plan's §5, the route
   stays unshared and per-jurisdiction — this is the empirical justification for
   that choice, and it is stronger than the plan assumed.
3. **Fit the covariate regression against the applicant's clock.** Reproducing
   the prior report's construction shows the r ≈ 0.2 result is a property of the
   entitlement clock; the same covariates reach 0.69 against the submission clock.
   §4.1's `gamma` is identifiable, on the right target.
4. **Two natural experiments are almost available and worth the wait.** Four ADU
   and seven SFD jurisdictions flip the rule between adjacent years, and SFD's
   statewide share moved 6 points from 2023 to 2025. Neither has enough measured
   spans yet. The 2026 filing adds a fourth year to a three-year panel and, more
   usefully, a second year of permit follow-up for the 2024 and 2025 cohorts,
   which is what the flip analysis is actually short of.
5. **W2 needs a withdrawal-reporting propensity, not just an abandonment
   channel.** 42% of jurisdictions reporting zero withdrawals is a disclosure
   model, identical in form to §4.2's `pi(kind, c)`, and it must be fitted before
   the withdrawal field can calibrate anything.

## What remains in this packet

- **`HISTORIC_SITES`, `APPROVE_SB35` and `DENSITY_BONUS_RECEIVED`** are in Table
  A and are the natural controls for the unobserved-difficulty confound in §3.
  They were not used here and would sharpen the +104 days into something closer
  to a conditional effect.
- **The data dictionaries** (DOCX on the same HCD open-data package) should be
  read to confirm HCD's official definition of `PROJECT_TYPE` and the reporting
  year it became mandatory. This report infers the phase-in from the coverage
  pattern; it should be confirmed from the template history before publication.
- **The 38 conditional ADU jurisdictions are the qualitative sample.** If the
  project wants to know *what predicate* a jurisdiction is conditioning on, San
  Francisco (0.335 on 555 applications), Arcadia (0.694 on 343) and Santa Barbara
  city (0.890 on 510) are where reading the ordinance will actually pay, because
  those are the places where the statute demonstrably underdetermines the route.
  Santa Barbara *County* is the most extreme reading in the state at 0.406, but on
  only 32 labelled applications, so it is a case study and not an estimate.
