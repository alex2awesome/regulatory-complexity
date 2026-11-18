# How much data each real channel actually yields

2026-09-16. The numeric half of the
[corpus-generation plan](2026-09-16-synthetic-corpus-generation-plan.md)'s
section 3 register, and the answer to a direct question: do our retrievals tell
us how much evidence to expect from reddit and elsewhere?

**They do, and the plan states none of it.** The plan's evidence-design table is
a list of what the corpus should reproduce and what it must not infer, which is
the right epistemic frame, but it contains no rates. Its section 7 asks for
per-source-family availability mechanisms and separate existence hurdles without
saying what any of them are. An unstated rate is a free parameter, and a free
parameter tuned until the corpus looks realistic is exactly the fitted-to-the-
answer world the plan forbids in section 6. So this document supplies the
measurements, with provenance, and flags two places where the
[W2 spec](2026-09-16-w2-generator-spec.md) currently plants a number our data
contradicts.

Built by `pipeline/recon/source_volume.py`; outputs
`corpus/counties/source_volume_register.csv` (687 rows) and
`source_volume_anchors.json`.

## 0. First, a correction to our own reddit numbers

The previously reported sweep total was **16,037 posts**. The true count of
distinct posts is **4,998** — the reported figure was inflated 3.2×.

`county_coverage.analyse` carries the comment *"deduplicating the same post found
by several queries … Summing rows would inflate"* and then sums `n_posts` across
rows anyway. It does keep a set of post ids, but only the first eight per row, so
the set was never usable as the count. Every post returned by more than one
phrasing, or by both a county-scoped and a statewide query, was counted once per
query. Seven programmes × up to three phrasings × several subreddits gives
roughly the 3.2× observed.

Two further corrections in the same place:

- A county total is **not** the sum of its programme counts. One post matching
  both `building permit` and `ADU permit` is one document. Summing programmes
  inflates a further ~1.3× on top of the above.
- A result list of exactly 100 is **truncated at the API limit**, so it is a
  lower bound. 10 counties have at least one capped query; Alameda has 15.

`source_volume.py` deduplicates full ids straight from the raw cache and labels
the capped counties. All figures below are the corrected ones.

## 1. What reddit actually yields

| | value |
|---|---|
| distinct posts, 58 counties × 7 programmes, since 2022-09-01 | **4,998** |
| timing-bearing (a duration word in title or body) | **1,597 = 32%** |
| counties with at least one post | **57 of 58** (only Alpine, pop. ~1,200, has none) |
| posts per county | median **37**, mean 86, p10 **4**, p90 297, max 426 |
| log–log slope on population | **0.747** (r = 0.865) |

The per-county spread is 32× between the top-5 mean (366) and the bottom-30 mean
(11.5). But the number that matters for corpus design is the **cell**, not the
county:

| per county × programme cell (406 cells) | posts | timing-bearing |
|---|---:|---:|
| median | 13 | **1** |
| mean | 39.6 | 8.9 |
| cells with zero | 29 (7%) | **155 (38%)** |
| cells with ≥ 5 | — | 122 (30%) |
| cells with ≥ 20 | — | 73 (18%) |

**The median county-programme cell yields one timing-bearing reddit post, and
38% of cells yield none.** Ranked by programme, CCW is richest (median 3) and
septic/well, ADU, Medi-Cal and building permits tie at the floor (median 1, with
24 of 58 counties at zero).

### The consequence for the calibration bridge

[The calibration bridge](scoping/2026-09-16-calibration-bridge.md) derived a
requirement of roughly **1,056 labelled rows per ambiguity class** to reach a
0.80 confusion diagonal in a 12-label class. The entire user tier — all 58
counties, all 7 programmes, three years — holds **1,597** timing-bearing posts.
That is 1.5× what *one* class needs, before any of it is turned into a verified
label.

So the corpus cannot source its calibration volume from the user tier. Label
volume has to come from criterion reveals in the declared and designed document
tiers, and the user tier's job in the design is to be what it measurably is: a
sparse, heavy-tailed, population-skewed nuisance channel that is empty for a
third of the cells. This is a real design constraint, and it argues for the
plan's decision to render only ~20 counties rather than thinly rendering 58.

## 2. Existence and volume are different mechanisms, and we can prove it

The CalGuns county-information forum is the cleanest natural experiment we have.
Every one of the 58 county threads was created in a single administrative batch
on 14–15 October 2010, so channel *existence* was assigned by an administrator
and carries **no population signal at all**. Volume inside those threads was
left to the population.

| | reddit | CalGuns forum | APR permit records |
|---|---|---|---|
| tier | user | user | observed |
| channel exists | 57/58 (98%) | **58/58 (100%)** | 58/58 |
| median per county | 37 posts | 156 replies | **5,461 projects** |
| max | 426 | 19,262 | 195,483 |
| log–log slope on population | **0.747** | **1.157** | **0.989** |
| r on logs | 0.865 | 0.842 | 0.950 |

Three findings the generator needs:

1. **The slopes differ by family**, from 0.75 to 1.16. Reddit is sub-linear —
   small counties get *more* than their population share. The gun forum is
   super-linear — volume concentrates harder than population. Administrative
   records are almost exactly linear, i.e. per-capita constant. One availability
   slope cannot produce this, which is the measured version of the plan's
   section 7 instruction.
2. **Existence is nearly always passed for institutional channels.** Three of
   the four families above are 58/58. The interesting variation is volume, and a
   model that spends its structure on an existence hurdle is modelling the wrong
   stage — except where existence really is the binding constraint (see §4).
3. **Audience does not collapse with authorship.** Modoc has 0 replies on its
   thread and **4,123 views**; Trinity has 3 replies and 7,605 views; the median
   view count on threads that exist is 85,101. A county with no posts is not a
   county with no readers. Three counties have a thread with zero replies, so
   even within one family, existence and volume disagree per county.

## 3. The retrieval funnel, measured per family

The plan asks for the chain `published → indexed → fetchable → text recoverable`
with per-family rates. The P5 environmental-health packet recorded exactly that
chain per county, so these are counted:

| stage | septic (LAMP) | wells | retail food |
|---|---:|---:|---:|
| directory row / status source located | 57 (98%) | 58 (100%) | 58 (100%) |
| authority or programme page reached | 48 (83%) | 22 (38%) | 27 (47%) |
| instructions or document read | 3 (5%) | 16 (28%) | 20 (34%) |
| operative local policy established | **2 (3%)** | **0 (0%)** | 7 (12%) |

**Read these as joint rates, not publication rates.** The packet spent 60
searches and 170 fetches across 58 counties × 3 programmes — about one fetch per
county-programme. Each rate is therefore publication × indexing × *our own
bounded search depth*. That makes them the right calibration for what a bounded
solver will find, and a lower bound on what is published. The plan's own rule
holds: access failure does not measure nonpublication.

Two of these cells are findings rather than gaps. Wells at 0 of 58 means no
county's local construction standard was conclusively established as stricter
than the state floor — 52 are `not_verified` and 4 are explicitly "not
established, not a negative finding." And septic's 3% is partly structural: a
LAMP is an **optional Tier 2** instrument, so a missing document can mean the
county lawfully uses Tier 1.

The cross-family spread at the deepest stage is 0% / 3% / 12%. That is the
strongest single argument in this document for a per-family funnel.

## 4. The tiers are 150× apart, and the rich tier is mostly uninformative

| tier | median per county | what it is |
|---|---:|---|
| observed | **5,461** | APR project records |
| observed, with a measurable span | **454** | entitlement → permit dated pairs |
| user (CalGuns) | 156 | thread replies |
| user (reddit) | 37 | distinct posts |
| declared (env health) | **0 of 3** | programmes whose instructions we read |

Volume and information run in opposite directions. Only **97,983 of 922,104**
APR projects (10.6%) carry a measurable entitlement-to-permit span; only 32% of
reddit posts carry a duration word; the declared tier has a **median of zero**
programmes read per county, with 33 of 58 counties at zero.

So the corpus should not equate document count with information. The plan says
this in prose — "more rendered pages are not necessarily more independent
information" — and the ratios above are the sizes to plant it at.

## 5. Two W2 spec parameters our data contradicts

The spec's §7.3 is the best-calibrated part of either document, and its
two-stage hurdle-then-volume shape is right. Two of its constants now have
direct measurements they did not have when written.

### 5.1 `V_POP = 0.85` understates the population gradient by ~35%

`post_volume` uses `V_POP` against a z-scored log population. With
sd(ln pop) = 1.576 across the 50 counties in the test set, `V_POP = 0.85`
implies a ln–ln slope of **0.539**. Measured slope: **0.83** for all programmes
(0.68 for ADU alone, 0.72 for ADU plus building permits). To reproduce 0.83,
`V_POP` should be about **1.31** on that z-score, or 1.53 against the full
58-county sd of 1.838.

Direction of the error matters: the spec currently makes rural counties look
*better* supplied with user evidence than they are.

### 5.2 `V_DELAY = 0.55` is not supported — the measured value is ~0

The spec sets `V_DELAY = 0.55` and comments "delay generates posts — this is the
selection mechanism the plan's κ is meant to estimate," calling κ "the single
most important measurement parameter in the plan." We can now test it: APR gives
a per-county median entitlement→permit delay, and the sweep gives per-county
post volume.

Regressing ln(1+posts) on ln(population) and ln(1+delay), n = 50 counties with
at least 30 measured spans:

| specification | population slope | delay slope | ΔR² from delay |
|---|---:|---:|---:|
| all 7 programmes | +0.772 | **+0.076** | **+0.004** |
| ADU + building permit | +0.718 | +0.073 | +0.004 |
| ADU only | +0.676 | +0.023 | +0.000 |
| all 7, timing-bearing posts only | +0.973 | **−0.034** | — |

The raw delay–volume correlation is +0.36 to +0.44, but it is **almost entirely
population confounding**: delay itself correlates with population at r = +0.50.
Once population is in the model, delay adds at most four thousandths of R², and
for timing-bearing posts specifically **the sign flips negative**.

**Robustness.** The null is not an artifact of one clock. Repeating it on all
four timing measures the APR panel supports:

| clock | n | delay coef. (posts) | ΔR² | delay coef. (timing posts) | ΔR² |
|---|---:|---:|---:|---:|---:|
| entitlement → permit | 50 | +0.030 | 0.0007 | **−0.045** | 0.0015 |
| permit → occupancy | 54 | +0.350 | 0.0088 | +0.243 | 0.0034 |
| entitlement → occupancy | 48 | +0.114 | 0.0033 | +0.065 | 0.0009 |
| p90 entitlement → permit | 50 | +0.082 | 0.0050 | +0.011 | 0.0001 |

Every ΔR² is under 0.01. The largest coefficient belongs to permit → occupancy,
which is mostly *construction* duration rather than administrative burden — the
clock least likely to be what drives someone to complain about a county office.

This does not prove κ is zero. The test has real limits: the delay measure is
entitlement-to-permit, which [starts at the completeness
date](scoping/2026-09-16-cross-scoping-audit.md) and is a lower bound; it
aggregates city and county jurisdictions within a county; the post window
(2022-09 onward) is shorter than the APR window (2018–2025); and county-level
aggregation can mask a within-county case-level effect, which is where the
mechanism actually lives — delayed *applicants* posting, not delayed *counties*.

But it does mean the spec is planting a strong mechanism the best available real
measurement cannot see. The plan's §6 rule applies exactly here: *"include zero
and alternative-sign sensitivity settings where the evidence does not identify
direction. Do not tune coefficients until a desired marginal correlation appears."*
So `V_DELAY` becomes a **scenario variable with 0.0 as its default**, and the
three-regime structure carries the alternatives: 0.0 in the reference regime,
0.55 in an evidence-constrained variant, and a negative setting in the
misspecification regime. If we later measure κ at case level we can promote it.

### 5.3 What the spec gets right, and should keep

`H0 = 2.10, H_POP = 1.35` for `county_sub` was calibrated against 9 of 58
counties having no candidate subreddit, and the spec rejected its own first draft
(`H0 = 1.55`, 13.6 expected) on the grounds that overstating the disappearing
commons "would flatter the paper's own hypothesis, the worst direction for a
generator to err in." That reasoning is right and the calibration holds. Note
only that the *candidate-subreddit* hurdle (49/58) and the *any-evidence* hurdle
(57/58) are different quantities: the statewide channel rescues 8 of the 9,
exactly as `H0 = +9.9, H_POP = 0` for `statewide_sub` intends.

The `grand_jury` row at `H0 = +9.9, H_POP = 0` is also right, and is the
best-evidenced inversion we have: mandated in all 58 counties, 8 of the 9
counties with no subreddit publish fetchable reports, and rural reports are more
on-topic per document. Permit Sonoma's 2025 report gives average days-to-review
by permit type and audits 5,000 task records; Modoc's 2024–25 report states that
16 of 45 departmental positions are unfilled; Sierra's 2025–26 report states
there is no public information about the building-permit process at all. **Volume
is not yet counted at title level, so it stays a `design_assumption` and must
not be given a fitted population slope.**

## 6. Observation defects with a measured incidence

The plan's §7 asks for "controlled versions of observed defects." These are the
ones we have actually hit, and they are cheap to plant because we know the rate:

| defect | measured incidence | source |
|---|---|---|
| same-date clock collapse (median span = 0 days) | **2 of 50** counties (Madera, Plumas) | APR |
| entitlement date present only by filing habit | p10 0.00 / median 0.50 / p90 1.00 within a route | APR discretion audit |
| reported zero that is a reporting artifact | 82 of 193 jurisdictions report exactly zero withdrawals | APR |
| HTTP 500 on a live official dataset | 1 of 13 recorded failures | P5 manifest |
| duplicate record IDs in a county export | Sonoma | wide-net retrieval |
| issuance date before opening date | San Diego | wide-net retrieval |
| image-only PDF needing OCR | ~1/3 of rural grand jury PDFs | forums scoping |
| 403 / JS shell / email-only / Drive-only access | 4 / 1 / 1 / 1 counties for grand jury | forums scoping |
| API result truncated at the limit | 10 of 58 counties | this sweep |

## 7. The register's own limits

- `official_page` counts come from matching a county name in a cached path, so
  they miss a document whose URL omits the county and over-count a page that
  mentions a neighbour. Tagged `derived_with_assumptions`, never `measured_anchor`.
- Reddit counts are a **lower bound** for 10 counties and are restricted to the
  post-2022-09 window and to 7 programmes' phrasings.
- CalGuns reply counts are all-time, so they are not comparable to reddit's
  three-year window in level — only in slope.
- `grand_jury` has an existence rate and no volume. It is the largest known
  unmeasured quantity in the register and the most likely to change the rural
  story.
- The funnel rates are joint with our own search budget and cannot be read as
  publication rates.

## 8. What this changes in the plan

1. Add the numbers above to §3's register as the numeric half; keep the existing
   qualitative table as the "must not infer" column.
2. §7 gets per-family slopes (0.75 / 0.99 / 1.16) and the per-family funnel,
   rather than "should not share one population slope."
3. §9's calibration tier must be sized against **1 timing-bearing post per
   median cell**, which is the quantitative case for its own 20-county render
   decision over a thin 58-county one.
4. W2 §7.3 `V_POP` rises to ≈1.31; `V_DELAY` drops to a scenario variable
   defaulting to 0.0.
5. The three regimes in §6 get concrete settings: reference uses the measured
   slopes, evidence-constrained adds the funnel and the defect table, and
   misspecification flips `V_DELAY` negative and makes the grand-jury inversion
   strong enough to reverse the rural ranking.
