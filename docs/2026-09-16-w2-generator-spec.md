# W2: the 58-county synthetic world — implementation specification

2026-09-16. Implements §3 of [the county scale-up plan](2026-09-16-county-scale-up-plan.md)
and extends [`benchmark/synth/DESIGN.md`](../benchmark/synth/DESIGN.md). Written to
be coded from without further design decisions: every change names a file and a
function, every functional form names its coefficients and their default values,
and every judgement call records the alternative that was rejected and why.

This spec **post-dates** three real-data results the plan does not have:
[county covariates](scoping/2026-09-16-county-covariates.md),
[APR permit timing](scoping/2026-09-16-apr-permit-timing.md), and
[the measured discretion residual](scoping/2026-09-16-apr-discretion-variation.md)
(which lands five explicit instructions for W2 in its own "What this changes for
the plan"). Where those results contradict the plan the spec follows the data and
says so; §14 collects every such correction in one place so the plan can be
amended. Sections 5, 8 and 9 were rewritten after the discretion report landed;
if you are re-reading an earlier draft, those are the three that changed.

Prerequisite reading for the implementer: plan §3 (the W2 target), plan §4
(where the covariates enter the Bayesian model — W2 exists to make those
parameters recoverable), audit §3 (the 66%-at-prior measurement that motivates
scale), and `benchmark/synth/generator/README.md` (the module map).

---

## Contents

| § | section | the decision it fixes |
|---|---|---|
| 0 | What W2 is for | why the planted coefficients must be *small* |
| 1 | The version knob and the module map | one `world_model_version`, three new modules |
| 2 | The county panel from covariates | stratified decade draw; every covariate's distribution and real anchor |
| 3 | Names, departments, hosts, fee instruments | derived from size class, not authored |
| 4 | The hard-coded tables that must become functions | six of them, not the plan's two |
| 5 | **Speed and cost from covariates, with the right sign** | the section the plan gets wrong |
| 6 | Load assignment by covariate fit | non-implementation becomes informative |
| 7 | Capacity-dependent disclosure | the logit, the shared county effect, the user-evidence hurdle |
| 8 | Discretion dispersion at 58 draws | ordered-logit strictness, reading lineage, statute shapes |
| 9 | Outcome structure | withdrawal, abandonment, and pending as a *mixture* |
| 10 | Fetch-blocking | a fifth error term: reachability |
| 11 | Volume, rendering budget, partitions | 20 rendered, 38 spec-only, 14/29/15 |
| 12 | Backward compatibility and validation | what stays byte-identical; 8 new test files |
| 13 | What `world.json` records | the planted-parameter contract |
| 14 | **Where the plan is wrong** | twelve corrections from the real data |
| 15 | Build order and acceptance | nine steps, and the definition of done |

---

## 0. The one-paragraph statement of what W2 is for

W1 answers "how much of one jurisdiction's process is recoverable from its
public documents". It cannot answer the cross-county question because it has at
most four implementers per statute, so a predicate's reading dispersion is
estimated from four draws and the hierarchy has nothing to pool (audit §3: 199
of 302 latent coordinates under 10% learned, agency effects at 13%). W2 plants
**58 county implementations of the same small statute set**, with county
covariates, capacity-dependent disclosure, covariate-dependent strictness and
lineage clustering, all with **known coefficients recorded in `world.json`**.
The deliverable is not a harder benchmark; it is a world in which
covariate-coefficient recovery, disclosure-propensity recovery, discretion-
dispersion recovery and transfer accuracy have ground truth, so the Bayesian
layer's §4 claims become falsifiable by simulation-based calibration rather than
argued.

**The discipline that makes this safe**: the planted coefficients must be
*small where the real data say they are small*. If W2 plants a strong
covariate-to-speed relationship, a model that recovers it proves nothing about
California, and any headline "the model learns which counties are slow" is an
artefact of the generator. §5 is therefore the most important section in this
document, and its central instruction is negative: do not plant the
relationship the plan assumed.

---

## 1. What changes, what must not, and the single version knob

### 1.1 The knob

One new integer knob in `benchmark/synth/generator/world.py:DEFAULT_KNOBS`:

```python
"world_model_version": 1,   # 1 = the six hand-written jurisdictions (W1);
                            # 2 = covariate-generated county panel (W2)
```

Default **1**, exactly as `decision_model_version` was introduced at default 2
only after its version-1 path was proven byte-identical. Here the default stays
1 permanently: W1 and every existing world keep replaying, and W2 is built with
`--knob world_model_version=2`.

Rejected alternative: a separate knob per feature (`county_panel_version`,
`disclosure_model_version`, `discretion_model_version`, `outcome_model_version`,
`retrieval_model_version`). Rejected because the features are not independent —
capacity-dependent disclosure has no meaning without a covariate panel, and the
cross-product of five knobs is 32 code paths nobody will test. One version knob,
with sub-knobs (§13) that only take effect at version ≥ 2, gives two tested
paths.

Every new sub-knob listed in this spec is read only inside a
`if int(knobs.get("world_model_version", 1)) >= 2:` branch, or inside a module
that is only imported on that branch. A version-1 build must not consume a
single extra RNG draw (the decision layer's precedent: added metadata does not
consume draws).

### 1.2 New modules

| new file | contents |
|---|---|
| `benchmark/synth/generator/counties.py` | the county panel: covariate draws, derived naming/departments/hosts/fee instruments, size class, partition assignment. ~450 lines. |
| `benchmark/synth/generator/capacity.py` | **every planted coefficient in one place**, plus the pure functions that consume them: `speed_factor`, `hourly_rate`, `caseload`, `staff_per_case`, `publish_logit`, `channel_exists`, `post_volume`, `strictness_propensity`, `p_fetch_blocked`, `p_withdraw`, `p_go_quiet`. ~350 lines. |
| `benchmark/synth/generator/lineage.py` | reading-lineage clustering (§8.2), extracted from `local_rules.py` so that choice lineage and reading lineage share one cluster assignment. ~120 lines. |

Rejected alternative: putting the coefficients next to the code that uses them
(speed coefficients in `processes.py`, publication coefficients in
`visibility.py`). Rejected because `world.json` must serialise the complete
planted-parameter block for the scorer, and a single `capacity.PLANTED` dict
serialises in one line and cannot drift out of sync with what the code used.

### 1.3 Modules that change

| file | change | §|
|---|---|---|
| `world.py` | `build_world` branches on `world_model_version`; `JURISDICTIONS`/`JUR_BY_ID` become a lookup built from `counties.draw_panel` at version 2; `KIND_FIT`/`BROAD`/`TARGET_LOAD`/`NEIGHBOR_LOAD` gain covariate equivalents; `_fit`, `_assign`, `_implementer_counts`, `_why_implements`, `_why_not` take a county record instead of a hand-written dict | 2,3,6 |
| `processes.py` | `SPEED` dict → `capacity.speed_factor(county, domain, program_key)`; three call sites (`_timing`, `_timing_added`, the back-office `f =` line) | 4,5 |
| `local_rules.py` | `HOURLY` dict → `capacity.hourly_rate(county)`; `_cite` and `_instrument` keyed on size class; lineage delegated to `lineage.py` | 4,5,8 |
| `visibility.py` | `plan_artifacts` reads per-county probabilities from `capacity.publish_logit` instead of global knobs; `select_personas` gains the user-evidence hurdle | 7 |
| `specs.py` | `JUR_BY_ID["J1"]` literal removed; per-county artifact counts; `fetch` block on every spec; thread count from `capacity.post_volume` | 4,7,10 |
| `simulate.py` | withdrawal and go-quiet channels; `outcome` enum gains `withdrawn`; `pending` is the censored state and is a *mixture* | 9 |
| `decision.py` | `resolve_readings` takes a strictness propensity; `SHAPE_SPREAD` per statute shape | 8 |
| `ceiling.py` | `retrieval_ceiling` block separating unreachable from unavailable | 10 |
| `build.py` | writes `world.json.planted`, `partitions.json`, `render_manifest.json`; per-county applicant counts | 11,13 |
| `schemas/validate.py` | the version-2 invariant checks | 12 |
| `schemas/*.schema.json` | new fields (`county`, `fetch`, `withdrawn`, `partition`, `planted`) | 12 |

---

## 2. The county panel: covariates instead of a list

### 2.1 Target shape

58 target counties in the State of Marisol, 8 look-alike counties in the
neighbour State of Corvane. Every jurisdiction is `kind: "county"`; W2 has no
cities (plan risk 2: restrict to the 58 counties' unincorporated processes and
treat cities as an extension). Ids `M01`…`M58` for Marisol and `N01`…`N08` for
Corvane.

Rejected alternative: keeping `J*`/`K*` ids. Rejected because a two-character
id space collides at 66 jurisdictions and because every existing test, fixture
and saved run that greps for `J1` should keep meaning W1's Halvern.

### 2.2 `counties.py:draw_panel(seed, knobs) -> list[dict]`

Deterministic, stdlib only, one `sub_rng(seed, "county", i)` stream per county
so adding a county does not reshuffle the others (the generator's existing
invariant).

The **size axis is drawn by stratified decade allocation**, which reproduces
California's bimodality exactly rather than approximately. Measured from
`corpus/counties/ca_counties_covariates.csv` (58 rows, 2026-09-16):

| log₁₀ population decade | real count | real range of log₁₀ pop |
|---|---:|---|
| 10³–10⁴ | 3 | 3.057 – 3.929 |
| 10⁴–10⁵ | 19 | 4.116 – 4.991 |
| 10⁵–10⁶ | 26 | 5.009 – 5.961 |
| 10⁶–10⁷ | 10 | 6.007 – 6.985 |

Procedure (`_draw_population`):

1. Fix the decade counts to `DECADE_COUNTS = (3, 19, 26, 10)` for 58 counties;
   for other panel sizes scale proportionally and give the remainder to the
   10⁵ decade.
2. Within decade *d* with *n_d* members, place county *k* (0-indexed) at
   `u = (k + 0.5) / n_d` and set
   `log10_pop = lo_d + (hi_d - lo_d) * u`, using the real ranges above.
3. Jitter: `log10_pop *= 1.0` then `log10_pop += rng.gauss(0, 0.035)`, clipped
   to `[lo_d - 0.05, hi_d + 0.05]`.
4. `pop = int(round(10 ** log10_pop, -1))` rounded to the nearest 10 so no
   synthetic county carries a real county's exact population.

Result: population spans a factor of ≈8,400 (real: 8,469 — Alpine 1,141 to Los
Angeles 9,663,345), median ≈190,000 (real 186,290), mean ≫ median (real mean
671,814 against median 186,290: five counties hold more than half the state).

Rejected alternative: draw 58 i.i.d. values from a fitted two-component
lognormal mixture. Rejected because i.i.d. draws at n=58 leave the tails ragged
— a third of seeds produce no county above 3 million or four below 5,000 — and
the whole point of the panel is that the *shape* is held fixed while the noise
varies. Stratified placement fixes the shape and lets the jitter and the
non-size covariates carry the randomness. Also rejected: copying the real 58
population values verbatim. Rejected because it makes every synthetic county
re-identifiable (`pop == 1141` is Alpine), which invites the paper's synthetic
results to be read as claims about named counties.

### 2.3 The covariate vector, term by term

Each county record carries a `cov` sub-dict. Every entry has a
`real_coverage` tag (`"complete"` = all 58 real rows present; `"blocked"` = the
real column is empty and the synthetic distribution is an **assumption**), which
`world.json` serialises and which §14.5 explains is load-bearing.

| field | draw | real anchor | coverage |
|---|---|---|---|
| `pop` | §2.2 | 1,141–9,663,345, median 186,290 | complete |
| `log_pop_z` | standardised `ln pop`; mean `LN_POP_MEAN = 12.0614`, sd `LN_POP_SD = 1.838` | measured | complete |
| `land_sqmi` | `exp(rng.gauss(7.46, 0.971))` clipped to `[45, 20100]`, **independent of population** | real corr(ln land, ln pop) = **0.041** | complete |
| `density` | derived `pop / land_sqmi` | real 1.5–17,323 | complete |
| `rucc` | ordered probit on `log_pop_z`, §2.4 | marginal 18/12/7/5/1/5/4/5/1; corr(rucc, ln pop) = **−0.877** | complete |
| `is_noncore` | `rucc >= 6` | real 15 noncore, `rucc>=6` gives 15 | complete |
| `rural_member` | `Bernoulli(logistic(-0.15 + 0.62 * rucc_z))`, then forced true if `rucc >= 6` | 32 of 58 are RCRC members and the sets disagree with USDA (Napa is RCRC at RUCC 2) | complete |
| `staff_abs` | `exp(9.1965 + 0.86 * (ln pop - 12.0614) + rng.gauss(0, 0.21))` | OLS slope 0.86, resid sd 0.21; geo-mean 9,863; range 220–442,433 | **proxy** (see below) |
| `staff_per_1k` | derived `1000 * staff_abs / pop` | real 33.3–192.8, median 53.7, **corr with ln pop = −0.73** | complete |
| `wage` | `exp(11.1643 + 0.066 * (ln pop - 12.0614) + rng.gauss(0, 0.132))` | slope 0.066, resid sd 0.132; geo-mean 70,569; range 53,216–114,981 | complete |
| `median_income` | `84634 + 6757 * (ln pop - 12.0614) + rng.gauss(0, 20171)`, clipped `[48000, 160000]` | corr 0.52 with ln pop | complete |
| `pct_bachelors` | `29.86 + 2.42 * (ln pop - 12.0614) + rng.gauss(0, 11.5)`, clipped `[12, 62]` | mean 29.86, sd 12.35, range 13.2–60.5; corr with ln pop **0.361**, with median income **0.840** | complete |
| `poverty_rate` | `13.25 + rng.gauss(0, 3.69) - 0.30 * (median_income - 84634)/20171`, clipped `[6, 22]` | corr(poverty, ln pop) = **−0.29**: rural counties are not uniformly poor (Modoc 20.1% at $51,996; Alpine 15.6% at $83,265) | complete |
| `pct_unincorporated` | `100 * logistic(0.35 - 0.55 * log_pop_z + rng.gauss(0, 0.8))`, clipped `[4, 100]`; forced 100 for `rucc == 9` | **blocked** — DOF E-1 not yet pulled | blocked |
| `n_cities` | `max(0, int(round(exp(0.55 + 0.75 * log_pop_z + rng.gauss(0, 0.5)))))` | **blocked** | blocked |
| `budget_per_capita` | `exp(7.05 - 0.22 * log_pop_z + rng.gauss(0, 0.30))` — **inverse in size, like staffing** | **blocked** — State Controller returns 403 to scripts | blocked |
| `broadband_pct` | `100 * logistic(1.35 + 0.42 * log_pop_z + rng.gauss(0, 0.45))`, clipped `[55, 97]` | **blocked** — Census API now needs a key | blocked |
| `portal` | see §2.5 | CCW: 13 of 15 on one vendor portal, 2 paper-only | blocked (CCW-seeded) |
| `site_platform` | see §2.5 and §10 | CCW: 6 of 15 sites block a scripted fetch | blocked (CCW-seeded) |
| `n_candidate_subreddits` | §7.3 | marginal 9/18/20/7/4 for 0/1/2/3/4; corr with ln pop = **0.741** | complete |
| `consortium` | `weighted(rng, [("A",0.38),("B",0.29),("C",0.19),("D",0.14)])`, independent of size | **blocked** — CalSAWS legacy column empty | blocked |
| `region` | `weighted` over 6 named regions, with a size-conditioned tilt (§8.2 uses it for lineage) | proxy for ABAG/MTC/CSAC template geography | n/a (synthetic) |

`pct_bachelors` earns its place because it is the **single strongest covariate
predictor of realised duration in the real data** (+0.583 against the ADU
applicant clock, +0.755 against the SFD applicant clock,
[discretion §4](scoping/2026-09-16-apr-discretion-variation.md)). It correlates
with median income at 0.840, so the two must **never both** enter the planted
regression; W2 uses education and carries income as a covariate that the model
may try and fail to use — a deliberate collinear decoy, since a real analyst will
face exactly that choice.

One caveat on `staff_abs` that must travel with it into the Bayesian layer: the
real column is **BLS QCEW local-government employment**, which counts cities and
school districts alongside county government, because the State Controller's
per-county FTE figure returns 403 to scripts
([covariates, opening section](scoping/2026-09-16-county-covariates.md)). It is
therefore a *proxy* for county-government depth with a size-correlated
measurement error of unknown magnitude. W2 plants the proxy, not the truth, and
records `cov_real_coverage.staff_abs = "proxy"` — a third tag value alongside
`complete` and `blocked`. When P8-COVARIATE-GAPS supplies the real county FTE,
the planted panel should be rebuilt against it, and the difference between the
two fits is itself a measurement-error result worth reporting.

`budget_per_capita` is drawn **inverse in population** on purpose. It has no
real anchor yet (the State Controller wall), and the only measured capacity
gradient in the table runs inverse to size (staffing per capita, r = −0.73),
driven by fixed costs: a county needs a sheriff, an assessor, a recorder and an
environmental-health specialist whatever its population. Drawing budget per
capita *positively* in size would contradict the one thing we do know about
county capacity per resident. The `real_coverage: "blocked"` tag records that
this is an assumption, not a measurement.

### 2.4 `counties.py:_draw_rucc`

Ordered probit, because the rurality code is an ordered category strongly but
imperfectly predicted by size and because the same machinery is reused for
strictness in §8.1:

```
latent_c = -BETA_RUCC * log_pop_z_c + rng.gauss(0, 1)         BETA_RUCC = 1.83
rucc_c   = 1 + sum(1 for t in TAU_RUCC if latent_c > t)
TAU_RUCC = (-1.032, 0.090, 0.736, 1.241, 1.351, 1.970, 2.632, 4.409)
```

`BETA_RUCC = 1.83` gives an implied correlation of
`1.83 / sqrt(1 + 1.83²) = 0.878`, matching the measured −0.877 (sign carried by
the minus). `TAU_RUCC` is `sqrt(1 + 1.83²) = 2.0854` times the standard-normal
quantiles of the real cumulative RUCC shares (18, 30, 37, 42, 43, 48, 52, 57 of
58), so the marginal distribution of `rucc` reproduces the real one in
expectation. Verify in `tests/test_generator_county_panel.py` (§12.3): over
seeds 1–40, the mean count in `rucc ∈ {1,2}` is 30 ± 4 (real 30) and at least
one county has `rucc >= 8` in ≥ 90% of seeds.

### 2.5 Systems: portal, platform, code host

Three correlated categorical draws, one stream `sub_rng(seed, "systems", cid)`:

```
p_portal      = logistic(-0.4 + 1.25 * log_pop_z)          # any online permit portal
portal_vendor = "Aperture Permitting"  with 0.62     # the dominant vendor (CCW: 13/15)
              | "Tyler EnerGov-like"   with 0.20
              | "OpenGov-like"         with 0.10
              | county-built           with 0.08
site_platform = weighted over ("municipal_cms_a", "municipal_cms_b",
                               "wordpress_selfhost", "legacy_aspx",
                               "cdn_fronted") with weights that shift by size:
                cdn_fronted weight = 0.10 + 0.35 * logistic(log_pop_z)
```

A county with `p_portal` failing gets `permit_system = "paper applications; forms
by mail or email"`, which `local_rules._choice_value` already branches on (it
looks for `"paper"` in `permit_system`). Keep that string contract.

`site_platform` is the *only* covariate that drives fetch-blocking (§10), which
is why it must be drawn here and not inside the retrieval layer: the same
platform must explain every document on that county's host, so blocking is
correlated within county, as it is in reality (Colusa's site 403s to scripts for
every page, not for one page).

Rejected alternative: draw `p_fetch_blocked` directly per county from a Beta.
Rejected because the CCW finding is a *platform* fact ("six of fifteen county
sites block a scripted fetch outright") and platform is also what a solver could
in principle detect and route around, which is the behaviour we want measurable.

---

## 3. Names, departments, hosts and fee instruments: derived, not authored

W1's six jurisdictions are hand-written dicts of about 30 keys each, roughly 40
lines of prose per jurisdiction. Authoring 66 of those is both infeasible and
wrong: the naming must be a *function of the covariates* so that a solver cannot
learn county identity from a stylistic tell that has no covariate meaning, and
so that department structure carries the real signal (a 1,100-person county has
one Community Development office; a 9-million-person county has a Department of
Regional Planning with bureaus).

### 3.1 `counties.py:derive_name(rng, cov)`

Two syllable tables and a suffix table, composed:

```python
HEAD = ["Ard", "Bel", "Cal", "Dun", "El", "Far", "Gil", "Hal", "Inn", "Jor",
        "Kel", "Lan", "Mar", "Nev", "Oak", "Pel", "Quar", "Rav", "Sen", "Tarn",
        "Ul", "Ver", "Wex", "Yar", "Zan", "Cor", "Bry", "Mel", "Sol", "Tre"]     # 30
TAIL = ["ford", "mont", "wick", "dale", "ridge", "bourne", "haven", "cross",
        "field", "mere", "stead", "worth", "combe", "moor", "shire"]             # 15
```

`name = pick(HEAD) + pick(TAIL)`, rejecting on collision with any name already
issued **and** with the six W1 names (`Halvern`, `Ellinsport`, `Calder
Springs`, `Sennet`, `Tarnbrook`, `Wexley`) **and** with any real California
county name (a 58-entry deny-list read from
`corpus/counties/ca_counties_covariates.csv`, column `county`). 450 combinations
against 66 draws, so rejection terminates; assert it does within 200 attempts.

Derived from the name, deterministically:

```
short        = name                                   # "Ardmont"
full         = "County of " + name                    # DESIGN's `name` field
host         = "www.%s-county.gov" % slug(name)
email        = "permits@%s-county.gov" % slug(name)
code_host    = "library.municodex.com/mr/%s" % slug(name)
legislative_host = "%s-county.legistream.com" % slug(name)   if cov.portal else
                   "%s-county.gov/agendas" % slug(name)
seat         = pick(HEAD) + pick(SEAT_TAIL)            # a second, different draw
news         = ("The %s %s" % (seat, pick(["Ledger","Beacon","Register","Sentinel",
                "Courier","Tribune","Bulletin","Chronicle"])),
                "www.%s%s.com" % (slug(seat), <outlet word>))
subreddit    = "r/%sCounty" % name  if channel exists (§7.3) else None
council      = "Board of Supervisors"                  # every county
council_cycle= size-conditioned: weekly (pop > 1e6), "first and third Tuesday"
               (1e5..1e6), "second Tuesday" (< 1e5)
```

**A county with no subreddit must carry `subreddit: None`, not a dead string.**
`specs.py` currently uses `jur["subreddit"]` unconditionally in
`_url_for("reddit_thread", ...)`, `select_personas`'s callers, the off-topic
filler and `_style(...)`. Every one of those sites must guard on `None` and fall
back to the statewide sub `r/Marisol` for filler only (never for a target
thread — a county with no channel produces no county-channel user evidence; that
is the planted fact).

### 3.2 `counties.py:derive_departments(rng, cov)`

Department naming is a function of **size class**, which is the one place the
generator should let population show through, because it is real: the plan's §5
"shared by agency class, not department name" only works if the names differ
while the classes do not.

```python
SIZE_CLASS = "mega"  if pop >= 2_000_000
             "large" if pop >= 500_000
             "mid"   if pop >= 100_000
             "small" if pop >= 20_000
             "tiny"  otherwise
```

Expected counts at the planted distribution, measured over 80 seeds:
**mega 7.0, large 10.1, mid 18.9, small 15.0, tiny 7.0**. The real table gives
5 / 11 / 20 / 14 / 8 at the same thresholds, so the panel reproduces the real
size structure to within one or two counties per class.

For each of the 20 `world.DEPT_ROLES`, a per-class template:

| role | mega / large | mid | small / tiny |
|---|---|---|---|
| `lead_permits` | "Permit Center, {umbrella}" | "Permit Center" | "Community Development front counter" |
| `building` | "Building and Safety Division" | "Building Inspection Division" | "Building Official (contract, {vendor})" for `tiny` |
| `planning` | "Department of Regional Planning, Current Planning Bureau" | "Current Planning Division" | "Planning Technician" |
| `health` | "Department of Public Health, Environmental Health Division" | "Environmental Health Division" | "Environmental Health Specialist (0.5 FTE)" |
| `hearing` | "Office of Administrative Hearings" | "Zoning Administrator" | "Planning Commission sitting as the appeals body" |
| `attorney` | "Office of County Counsel" | "Office of County Counsel" | "County Counsel (contract, {firm})" |
| … | one row per role, same pattern | | |

Three structural rules, all with real analogues and all recorded in the county
record so the truth is checkable:

1. **`umbrella`** is `"{name} County Planning and Building Department"` for
   mid and up, `"{name} County Community Development Department"` for small,
   and `"{name} County Community Development"` for tiny.
2. **Contracting out** (`contracts_out: [roles]`): for `tiny`, and for `small`
   with probability 0.45, `building` and/or `attorney` and/or `arborist` are
   named as contracts to a private firm or to a neighbouring county. This is the
   Lake County pattern (it trains its own applicants because there is no local
   vendor) and the Calder Springs pattern already in W1.
3. **Missing roles**: a `tiny` county omits `housing`, `parks`, `animal` and
   `arborist` from `depts` entirely. `world.actor_name` already falls back to
   `depts["lead_permits"]`, and `processes._element_actor` already checks
   `role in jur["depts"]`, so omission is safe — but the fallback must now be
   *recorded* as a deviation in the process notes, because "the same person does
   intake and inspection" is a structural fact a solver should be able to
   recover, not a generator accident. Add to `processes.build_process`:
   `proc["role_collapses"] = [{"role": r, "collapsed_to": lead, "why": "..."}]`.

`world.actor_name`'s two hard-coded strings
`"Sennet County Environmental Health Division (by agreement)"` and
`"Sennet County Assessor's Office"` must become
`"%s County Environmental Health Division (by agreement)" % <the county itself>`
— in W2 every jurisdiction *is* a county, so the city-contracts-to-county
fallback never fires; keep the branch for version 1 and assert it is unreachable
at version 2.

### 3.3 `counties.py:derive_fee_instrument(rng, cov)`

Four instruments, weighted by size class, because the instrument governs whether
a fee is discoverable at all (W1's `p_publish_fee_resolution` logic keys on it):

```
mega/large : "Countywide Master Fee Schedule, adopted annually by the Board"   0.80
             "Fee Ordinance, Title 3, amended by the Board"                    0.20
mid        : "Master Fee Schedule, adopted by resolution"                      0.55
             "County Fee Ordinance, Title 3, amended by the Board"             0.30
             "Unified Fee Resolution"                                          0.15
small/tiny : "Master Fee Schedule, Resolution updated when the Board directs"  0.45
             "fees set by departmental memorandum (no adopted schedule)"       0.35
             "County Fee Ordinance, Title 3"                                   0.20
```

The `"no adopted schedule"` branch matters: `local_rules` already writes
`"NOT FOUND in any adopted instrument (administratively set)"` with probability
0.25, and in W2 that probability must become a **function of the instrument** —
0.05 where a master fee schedule exists, 0.75 where fees are set by memorandum.
That is the disappearing commons at the level of a single fact, and it is
exactly the CCW observation that fees vary 4.6-fold ($118 Siskiyou to $549 Lake)
with no central source.

---

## 4. Every hard-coded jurisdiction table that must become a function

Found by `grep -rn '"J[0-9]"\|"K[0-9]"\|JUR_BY_ID' benchmark/synth/generator/`.
The plan names two (`SPEED`, `HOURLY`); there are **six** plus two structural
tables:

| # | site | today | becomes |
|---|---|---|---|
| 1 | `processes.py:189` `SPEED` | `{"J1": 1.0, "J2": 1.25, "J3": 1.4, "J4": 1.15, "K1": 1.0, "K2": 1.1}` | `capacity.speed_factor(county, domain, program_key, rng)` — §5.2. Three call sites: `_timing` (line 237), `_timing_added` (line 747), and the inline `f = SPEED[jur["id"]] * dom["pace"] * ...` in the back-office block (line 524). All three must take the *same* value for one (county, program), so `speed_factor` must be memoised per `(cid, model_id)` or called once in `build_process` and passed down. **Call it once**: add `pace = capacity.speed_factor(...)` at the top of `build_process` and thread it as an argument. |
| 2 | `local_rules.py:24` `HOURLY` | `{"J1": 190, ...}` | `capacity.hourly_rate(county)` — §5.4. One call site: `_fee_amount` (line 280). Change its signature from `(rng, jur_id, domain)` to `(rng, county, domain)`. |
| 3 | `world.py:322` `TARGET_LOAD` | `{"J1": 7, "J2": 7, "J3": 6, "J4": 6}` | `world._target_load(counties, statute_set, knobs)` — §6.3, derived from per-(county, statute) implementation probabilities. |
| 4 | `world.py:323` `NEIGHBOR_LOAD` | `{"K1": 6, "K2": 6}` | same function, applied to the 8 Corvane counties with `knobs["neighbor_statutes_per_county"]` (default 3). |
| 5 | `world.py:303` `KIND_FIT` | per-domain `{"city": x, "county": y}` | `world.COVARIATE_FIT[domain]` — a dict of coefficients on the *covariates*, §6.1. `KIND_FIT` is dead at version 2 because every W2 jurisdiction is a county, so the table degenerates to one column and carries no information. |
| 6 | `world.py:319` `BROAD` | `{"rental_inspection", "solar_auto_permit"}` | subsumed by `COVARIATE_FIT[domain]["intercept"]`: "broad" is just a high intercept. Keep the set for version 1. |
| 7 | `specs.py:271` `JUR_BY_ID["J1"]` | the bill-analysis URL is built from a literal jurisdiction | `_url_for("bill_analysis", ...)` does not read the jurisdiction at all (it uses `statutes[...]` only), so pass `None` and delete the parameter's use; add an assertion in the function that `kind == "bill_analysis"` never dereferences `jur`. This is a latent bug, not only a W2 blocker: at version 1 with `only_jurisdictions=["J3","J4"]` the line raises `KeyError`. |
| 8 | `world.py:402-412` `_why_not` | branches on `jur["pop"] < 40000`, `> 200000`, and `jur["kind"] == "city"` | `world._why_not(county, domain)` rewritten against the covariates, §6.4. The existing population literals happen to be city-scaled and are meaningless for counties. |
| 9 | `visibility.py:182` `KIND_META` knob column | each kind names one global knob | the knob becomes the *intercept* of a per-county logit; `KIND_META` keeps the knob name as the key into `capacity.PLANTED["publish"]["intercept"]`. §7.1. |
| 10 | `processes.py:208` `DENIAL_BASE` | per-domain denial rate | at version 2 the denial rate is already derived from predicates (`decision.py`); `DENIAL_BASE` is dead except on the version-1 path. Additionally §9 makes withdrawal, not denial, the informative outcome. |

Also **not** a jurisdiction table but worth the same treatment:
`world.py:499-507` hard-codes the two states' populations (8,420,000 and
2,110,000). At version 2, Marisol's population is `sum(c.pop for c in
marisol_counties)` and Corvane's likewise, because a solver can add up the
counties and a mismatch is a tell.

---

## 5. Speed and cost from covariates, with the right sign

**This is the section where the plan is wrong and the spec must not follow it.**

### 5.1 What the real data say, and what the plan assumed

Plan §3.1 item 2: "speed as a function of staff per capita and caseload".
Plan §4.1: covariates `x_c` include "staff per capita", and the section's whole
framing is that `gamma_rural` will be "the estimated slowness attributable to
rurality".

Three measurements contradict this:

1. **Staffing per capita runs inverse to county size**: corr(ln pop, local-
   government employees per 1,000 residents) = **−0.73**; corr(rurality code,
   staff per 1,000) = **+0.69**
   ([covariates §2](scoping/2026-09-16-county-covariates.md)). Alpine has 192.8
   staff per 1,000 residents; Solano has 33.3. A generator that plants "more
   staff per capita means faster" plants "tiny rural counties are the fastest
   and best-resourced", the opposite of the mechanism (fixed costs, not
   capacity), and any covariate-recovery result would be an artefact of that
   inversion.
2. **Covariates barely predict timing**: against the median ADU entitlement-to-
   permit days rolled up to 35 counties, corr = **0.21** for log population,
   **0.18** for log local-government staff, **−0.27** for the rurality code —
   and the rural sign is *negative*, i.e. more rural counties are slightly
   **faster** ([APR §3](scoping/2026-09-16-apr-permit-timing.md)). Implied R² ≈
   **0.04–0.07**. Eightfold timing variation is not explained by size, staffing
   or rurality.
3. **Log absolute staff and log population are collinear**: corr = **0.991** in
   the real table (OLS slope 0.86, residual sd 0.21). They are not two
   regressors; they are one size axis measured twice.
4. **But it depends entirely on which clock you measure**
   ([discretion §4, "A reconciliation the prior report requires"](scoping/2026-09-16-apr-discretion-variation.md)).
   The same builder recomputes the permit-record construction exactly and then
   repeats it on the applicant's clock:

   | predictor | entitlement→permit (35 counties) | **application→permit (30 counties)** |
   |---|---:|---:|
   | log population | +0.212 | **+0.335** |
   | log local-government staff | +0.180 | **+0.318** |
   | rurality code | −0.269 | **−0.398** |
   | log population density | +0.334 | **+0.688** |
   | pct bachelor's degree | +0.308 | **+0.583** |

   The strong covariates roughly **double** on the applicant clock while the weak
   ones stay weak. For single-family detached, education reaches **+0.755** on
   the applicant clock. The mechanism is the one both reports identify: the
   missing time is pre-entitlement intake, completeness review and resubmission,
   and *that* is where capacity and caseload bite; the permit-record clock starts
   after the queue and is nearly capacity-free by construction.

**So the plan is wrong about the sign (item 1) and the earlier APR report is
right only about its own clock (item 4).** W1/W2's `elapsed_days` —
"beginning preparation or filing through the last recorded decision" — is an
**applicant** clock. The covariate coefficients must therefore be calibrated to
the *right-hand* column, and the generator must additionally reproduce the
*left-hand* column on its post-decision sub-clock. That double requirement is
what §5.2's phase split exists to satisfy, and getting it wrong in either
direction invalidates the plan's §4.1 `gamma`: "fitted against the wrong clock
it recovers `gamma` near zero and looks useless".

### 5.2 The planted form

`capacity.speed_factor(county, domain, model_id, phase, rng) -> float`, a
multiplier on an activity's median and p90 (replacing `SPEED[jur_id]`). It is
built on the log scale so the coefficients are elasticities, and it is
**phase-dependent**, which is the whole point of §5.1 item 4:

```
# queue phases (activity phase < 7.0: submittal, intake back-office, referrals,
# inspection, corrections -- everything the applicant waits through before a
# decision is recorded)
ln speed_c,p = B0
             + B_DEPTH   * z_log_staff_abs(c)          # depth / specialisation
             + B_LOAD    * z_log_staff_per_case(c, p)  # congestion
             + B_DENSITY * z_log_density(c)            # the urban office
             + B_EDU     * z_pct_bachelors(c)
             + B_PORTAL  * portal(c)
             + B_RURAL   * z_rucc(c)
             + policy_c + policy_c,p
             + DISCRETIONARY * route_is_discretionary(case)   # PER CASE, not per county (S5.5)

# post-decision phases (phase >= 7.0: decision, mailing, records, referrals,
# appeal, renewal) -- NO covariate terms at all
ln speed_c,p = B0 + policy_c + policy_c,p
```

with defaults in `capacity.PLANTED["speed"]`:

| coefficient | default | sign meaning | why this value |
|---|---:|---|---|
| `B0` | `0.0` | scale anchor (speed 1.0 = W1's Halvern pace) | |
| `B_DEPTH` | **−0.22** | more absolute staff ⇒ **faster** (dedicated program staff, parallel review stations, a plan-check queue rather than one person) | negative on log-duration; sized to hold the population correlation down while density carries the congestion signal |
| `B_LOAD` | **−0.28** | more staff per case ⇒ **faster** (less queueing) | large, because queueing effects *are* large: a 1-sd fall in staff per case adds about 28% to the queue |
| `B_DENSITY` | **+0.30** | denser ⇒ **slower** | density is the strongest single real predictor of the applicant clock (**+0.688**) |
| `B_EDU` | **+0.18** | more graduates ⇒ **slower** | the strongest predictor for single-family (**+0.755**), and +0.583 for ADU |
| `B_PORTAL` | **−0.06** | a portal shaves intake | matches W1's paper-city being slowest |
| `B_RURAL` | **−0.04** | more rural ⇒ marginally **faster**, over and above its size and density effects | the measured sign (−0.398 on the applicant clock) |
| `TAU_POLICY_COUNTY` | **0.50** | sd of `policy_c ~ N(0, τ²)`, a county-level policy effect **independent of every covariate**, applied at **every** phase | must still carry about half the variance |
| `TAU_POLICY_PROGRAM` | **0.30** | sd of `policy_c,p ~ N(0, τ²)` within county | the plan's §5 "route is not shared" tier |
| `DISCRETIONARY` | **+1.05** | per-*case* effect of a discretionary route, §5.5 | calibrated to the measured **+104 days** within-office difference |

**Why the phase split is mandatory, not a refinement.** Without it, one
coefficient set has to reproduce two measured correlation vectors that differ by
a factor of two. With it, each clock has its own generative story: covariates act
on the queue, the county policy effect acts everywhere, and so

- the **applicant clock** (`elapsed_days`, arrival → last decision) inherits the
  full covariate expression, and
- the **post-decision sub-clock** (decision → terminal issuance and closeout)
  inherits only `policy_c`, hence is nearly covariate-free — reproducing the
  earlier report's max |r| = 0.27 without any extra tuning.

**What the calibration lands on.** Simulated over 60 seeds on the planted panel
(58 counties, four programs each), against the real ADU applicant-clock values
and their n=30 sampling intervals:

| statistic | planted | real (ADU, applicant clock) | approx 95% CI at n=30 |
|---|---:|---:|---|
| corr(log pop, log median days) | **+0.49** | +0.335 | [−0.03, +0.62] |
| corr(log density, ·) | **+0.53** | +0.688 | [+0.43, +0.84] |
| corr(log staff_abs, ·) | **+0.46** | +0.318 | [−0.04, +0.61] |
| corr(pct bachelors, ·) | **+0.40** | +0.583 | [+0.27, +0.78] |
| corr(rucc, ·) | **−0.45** | −0.398 | [−0.67, −0.05] |
| R² of the five covariates | **0.48** | ≈ 0.47 (best single predictor 0.688²) | — |
| share of variance from `policy_c` | **0.52** | not identified in the real data | — |

Every planted value sits inside the real interval. That is the honest target:
**the real point estimates are not jointly reproducible by any linear model with
a substantial policy effect** — density at +0.688 while population is at +0.335,
given that the two correlate at 0.88, requires a large negative land-area
coefficient that alone would take covariates to ≈ 70% of the variance. So W2
calibrates to the *intervals*, not the points, and `planted.notes` records that
the panel is a deliberately conservative reading of a 30-county measurement.

Rejected alternative 1: `B_DEPTH = -0.09, B_LOAD = -0.38` with no density or
education term (this spec's second draft, calibrated to the *permit-record*
clock). It gives corr(log pop, days) = +0.335 — exactly the applicant-clock
figure, by coincidence — but corr(density) = +0.30 and corr(education) = +0.20,
i.e. it misses the two strongest real predictors entirely, and its R² of 0.13 is
a quarter of the measured one. Rejected because the plan's headline transfer
metric is a covariate prediction, and planting a world in which covariates carry
13% of the variance when the real figure on the same clock is ≈ 47% would make
transfer accuracy look far worse than it is.

Rejected alternative 2: `B_DEPTH = -0.10, B_LOAD = -0.12` (the first draft).
Net elasticity −0.018, hence corr(log pop, days) ≈ −0.05: the wrong *sign* on
both clocks. Recorded here because it is the natural thing to write if you read
only the plan.

**The mechanism under the numbers**, for `planted.notes` and for the paper:
depth and congestion oppose each other along the size axis
(`staff_abs ∝ pop^0.86` so `staff_per_case ∝ pop^−0.14`), and their near-
cancellation is why *population* is a weak predictor on either clock. What
survives is **compactness**: a dense office serving many cases per acre queues,
and a sprawling rural office does not. That is a substantive claim, it is the
strongest one the real data support, and it is not in the plan.

### 5.3 Identification by design: `staff_per_case` varies within county

`B_LOAD` would be nearly unidentifiable if `staff_per_case` were a pure function
of county size, because it would be collinear with `staff_abs` at |r| ≈ 0.69.
It is not, because the county *allocates* staff across programs:

```
caseload(c, p)        = BASE_RATE[p] * exposed_population(c, p) / 1000
exposed_population    = pop                                    for most programs
                      = pop * pct_unincorporated / 100         for well_permit,
                                                               unpermitted_unit_amnesty
                                                               (county jurisdiction
                                                                is outside cities)
alloc_share(c, p)     = softmax over the county's implemented programs of
                        (SALIENCE[p] + rng.gauss(0, 0.35))      # stream ("alloc", cid)
staff_on_program      = max(0.15, staff_abs * PROGRAM_STAFF_SHARE * alloc_share)
staff_per_case(c, p)  = staff_on_program / max(1.0, caseload(c, p))
```

`PROGRAM_STAFF_SHARE = 0.004` (four permit-program staff per thousand
local-government employees), `BASE_RATE` per domain in
`capacity.PLANTED["caseload"]` (e.g. `unpermitted_unit_amnesty: 0.9` cases per
1,000 exposed residents per year, `well_permit: 0.35`, `mobile_food: 0.6`,
`rental_inspection: 3.2`, `home_business: 2.1`, `str_registration: 1.4`).

The `rng.gauss(0, 0.35)` allocation noise is **within-county across programs**,
so with 4–6 programs per county the design has a within-county contrast in
`staff_per_case` that is close to orthogonal to `staff_abs` by construction.
Computed at these dispersions:
`corr(ln staff_abs, ln staff_per_case) = -0.3626 / (1.645 * 0.483) = -0.46`, so
the two regressors share 21% of their variance, against the 98% that log
population and log absolute staff share. Target for the test:
`|corr| < 0.55`, across all (county, program) cells. Assert it in `tests/test_generator_county_panel.py`;
if the build fails the assertion, raise the allocation noise rather than
shipping a non-identified design. This is the one place W2 deliberately
*improves* on reality for identification, and it must be declared as such in
`world.json.planted.notes`.

### 5.4 Hourly rate and fees

`capacity.hourly_rate(county) -> int`, replacing `HOURLY`:

```
rate = round( WAGE_TO_HOURLY * wage_c * (1 + B_OVERHEAD * z_log_staff_abs(c)) )
WAGE_TO_HOURLY = 0.00269        # equivalently, annual wage / 371
B_OVERHEAD     = 0.10
```

`WAGE_TO_HOURLY = 0.00269` maps the panel's geometric-mean wage of $70,569 to
**$190/h**, W1's Halvern value and the middle of the real municipal
fully-burdened plan-review range. The implied multiplier is large — a
1,880-hour year at the direct rate would give $37.50/h, so the constant carries
a 5.0x factor — and that is right for two compounding reasons: benefit and
overhead loading is 2.2–2.6x, and the QCEW *average local-government wage*
mixes school, part-time and seasonal employment, so it understates a licensed
plan reviewer's salary by roughly a further factor of two. Both reasons go in
`planted.notes`, because the constant is otherwise unexplainable to a reader. `B_OVERHEAD` makes big counties charge more per hour
(bigger overhead pools), which is the mechanism behind the CCW fee spread; the
*net* fee spread then also inherits the cost-allocation noise already in
`_fee_amount`. Target: the ratio of the 90th to the 10th percentile of the
program fee across 58 counties is **3.5–6.0**, bracketing the CCW-measured
4.6-fold spread ($118 Siskiyou to $549 Lake). Check in
`tests/test_generator_capacity.py`.

Note the sign trap here too: wage correlates with size (r = 0.65), so the fee
gradient runs *with* size while the staffing-per-capita gradient runs against
it. Both are in the real data, and W2 plants both, so a model that conflates
"capacity" with "per-capita staffing" gets the fee gradient backwards as well.

### 5.5 The discretionary route: a case-level predicate with a county reading

This subsection was rewritten after
[the discretion report](scoping/2026-09-16-apr-discretion-variation.md) measured
the real thing. Six measured facts constrain it, and together they rule out the
simple per-county Bernoulli the earlier draft specified:

1. **It is a spike, not a split.** 89.1% of the 596 jurisdiction-years with ≥ 20
   labelled ADU applications are within 0.05 of all-ministerial; the pooled ADU
   ministerial share is **0.974**; only 1.5% are all-discretionary. 156 of 236
   jurisdictions never file a single discretionary ADU application.
2. **The dispersion is real and concentrated.** Cross-jurisdiction variance of
   the ministerial share is **45×** the binomial expectation under one statewide
   rule (0.02121 against 0.00047). The top 10 jurisdictions hold **71%** of all
   discretionary ADU applications. The population is "five standing dissenters
   plus 38 conditional jurisdictions out of 291".
3. **A jurisdiction that labels *some* of its own applications each way is
   running a conditional rule** — the discretion sits in a predicate evaluated
   case by case, not in a fixed jurisdiction effect.
4. **Within an office the label is worth +104 days** (median of paired
   differences collapsed to one per jurisdiction, 95% bootstrap [+3, +185],
   sign-test p = 0.021), and a discretionary ADU is **29.6 pp** less likely to
   reach a permit within 365 days.
5. **Between offices the label explains almost nothing**: pooled share against
   median clock, Pearson **−0.163** (n = 250), Spearman −0.110. Los Angeles city
   and its county's unincorporated area agree to 0.01 on the rule and differ by
   **243 days**; Monterey city and county disagree almost completely on the rule
   (0.94 vs 0.01) and differ far less in time.
6. **There is a project-size gradient across categories**: ministerial share
   0.974 for ADU, 0.878 single-family detached, 0.823 for 2–4 units, **0.484**
   for 5+ units.

So the route must be **a predicate on a case attribute, with a county-specific
reading**, not a county coin flip. That is exactly the object `decision.py`
already models, which makes this an addition to the predicate catalogue rather
than a new mechanism:

```python
# decision.py:PREDICATES[<each W2 domain>] gains one predicate
_standard("P4", "The project is within the ministerial-review envelope",
          "project_scale", "<the decision element>",
          ("lognormal", 1.0, 3.2),          # case attribute: relative project scale
          "ministerial review",
          [_r("projects of any scale are processed ministerially", "always", None, 0, 0.86,
              "they just process it over the counter"),
           _r("projects above about three times the typical scale go to discretionary review",
              "le", 3.0, 1, 0.11, "bigger jobs go to a hearing"),
           _r("any project requires discretionary review", "always", None, 2, 0.03,
              "everything goes to a hearing here")],
          "What is the project's scale relative to a typical application?", "scale_ratio",
          fixable=False)
```

Planted weights **(0.86, 0.11, 0.03)** reproduce fact 1 and fact 2 directly: 86%
of counties are all-ministerial, 11% run a conditional rule (a threshold inside
the case-attribute distribution, so *some* of their cases route each way), 3%
route everything. With the `project_scale` attribute drawn lognormal(median 1.0,
p90 3.2), the conditional counties send about 12% of their own cases to
discretionary review, and the statewide pooled ministerial share lands at
**0.965–0.975**. Assert that in `tests/test_generator_outcomes.py` against the
real 0.974.

Consequences to implement:

1. `route_class` becomes a **per-case** field in the log
   (`rec["route_class"] ∈ {"ministerial","discretionary"}`), and a **per-process**
   field only as a summary (`proc["ministerial_share_expected"]`). The earlier
   draft's per-process binary is wrong and must not be shipped: it would plant a
   between-county timing correlation with the route where the real data show
   −0.163.
2. When a case routes discretionary, the extra `discretionary_review` activity
   (phase 6.95, actor `hearing` or `council`, visibility `applicant_facing`,
   timing class `hearing`) fires **for that case only** — `flow_gate:
   "if_discretionary"`, a new gate alongside `if_denied`/`if_appealed`/`if_rework`
   in `simulate.py` and `processes.py`. Total planted within-office effect must
   land at **+90 to +130 days** on the applicant clock; `DISCRETIONARY = 1.05`
   plus the hearing activity's own duration achieves that at the default pace.
   Verify against +104 [+3, +185].
3. The activity exists in `process_truth` for every county that *could* route
   discretionary (any county whose reading is not "always ministerial"), with
   `p_occurs` set to the planted routing share — so a solver reconstructing the
   process has to discover a step that only 12% of cases take. That is a new and
   realistic recovery problem: the step is real, documented nowhere prominently,
   and invisible in most forum posts.
4. `administrative_simultaneity: bool` per case, as before, with the measured
   leak rates (0.45 of ministerial cases show a zero span, 0.29 of discretionary
   ones), so the noisy-observable/partial-label calibration pair exists
   synthetically with a known confusion matrix.
5. `world.json.planted.route` records the reading weights, the attribute
   distribution, the planted pooled ministerial share, the planted within-office
   day effect, and the two leak rates.

Rejected alternative: keep the per-county Bernoulli at `p ≈ 0.30` for minimal
statutes (the earlier draft). Rejected on three measured grounds — the real
distribution is a spike at 1.0 rather than a 30% split; the real variation is
case-level inside a minority of offices rather than office-level; and the real
between-office correlation of route with duration is ≈ 0, which a per-county
switch with a 2.9× multiplier would make strongly positive by construction.

### 5.6 The self-check that keeps the coefficients honest

`build.py` computes, after `build_processes` and `simulate_all`, a diagnostic
block written to `world.json.planted.diagnostics`. **Per clock**, because §5.1
item 4 is the whole reason the phase split exists:

```
# applicant clock: elapsed_days (arrival -> last recorded decision)
r_logpop_vs_median            target in [ 0.15,  0.65]   (real +0.335, CI [-0.03, 0.62])
r_logdensity_vs_median        target in [ 0.35,  0.75]   (real +0.688, CI [ 0.43, 0.84])
r_logstaff_vs_median          target in [ 0.15,  0.65]   (real +0.318)
r_bachelors_vs_median         target in [ 0.25,  0.70]   (real +0.583)
r_rucc_vs_median              target in [-0.70, -0.20]   (real -0.398)
R2_covariates_on_log_median   target in [ 0.30,  0.60]   (real approx 0.47)
share_variance_policy         target in [ 0.40,  0.65]

# post-decision sub-clock: last decision -> terminal issuance and closeout
r_logpop_vs_postdecision      target abs <= 0.30         (real +0.212 on the
r_logdensity_vs_postdecision  target abs <= 0.40          entitlement->permit clock,
r_rucc_vs_postdecision        target abs <= 0.35          max abs r 0.334)

# route
pooled_ministerial_share      target in [0.95, 0.985]    (real 0.974)
share_all_ministerial_counties target in [0.78, 0.94]     (real 0.891)
within_office_discretionary_days target in [80, 140]      (real +104, CI [3, 185])
between_office_r_share_vs_days   target abs <= 0.30       (real -0.163)
```

If any target is missed the build **fails**, naming the coefficient to adjust.
Rejected alternative: warn only. Rejected because the failure modes this guards
against — a W2 in which covariates explain 13% of applicant-clock variance (too
little, making the plan's transfer metric look hopeless) or 70% (too much, making
it look trivial), or in which the route orders counties by speed when in reality
it does not — would each silently invalidate a headline result. The band, not the
point, is the contract.

## 6. Load assignment by covariate fit

Plan §3.1 item 3: "extend `_fit` so implementation probability is a function of
covariates ... Non-implementation becomes informative rather than filler."

### 6.1 `world.COVARIATE_FIT`

Per domain, a coefficient vector on the standardised covariates, consumed by
`world._fit(county, domain) -> float` (a probability, not a weight):

```
logit p_implement(c, d) = F0[d]
                        + F_POP[d]     * z_log_pop(c)
                        + F_RURAL[d]   * z_rucc(c)
                        + F_UNINC[d]   * z_pct_unincorporated(c)
                        + F_INCOME[d]  * z_median_income(c)
                        + F_THRESHOLD[d] * applicability_met(c, d)
```

`applicability_met` is the statute's own text, so it is a **hard** term: the
statute says "an agency serving a population of 75,000 or more shall adopt", and
a county below the threshold gets `F_THRESHOLD` = −2.2 while one above gets 0.
Defaults for the six-statute W2 set (§11.1):

| domain | `F0` | `F_POP` | `F_RURAL` | `F_UNINC` | `F_INCOME` | statutory threshold |
|---|---:|---:|---:|---:|---:|---|
| `unpermitted_unit_amnesty` | 2.00 | +0.35 | −0.10 | +0.55 | 0 | none (permissive) |
| `well_permit` | 1.70 | −0.20 | **+0.95** | **+0.80** | 0 | none (county is the permitting agency) |
| `mobile_food` | 2.90 | +0.15 | 0 | 0 | 0 | none (county is the LEA — near-universal) |
| `rental_inspection` | 0.10 | **+0.90** | −0.35 | −0.30 | −0.25 | ≥ 5,000 rental units (proxy: pop ≥ 120,000) |
| `home_business` | 2.40 | +0.10 | 0 | +0.25 | 0 | none |
| `str_registration` | 0.40 | +0.30 | +0.45 | +0.50 | +0.40 | none; `F_RURAL` and `F_INCOME` positive together stand for the **visitor economy** (a high-income rural county is a resort county) |

Expected implementer counts at these defaults, measured over 80 seeds: amnesty
**51.1** (range 42–56), well **43.4** (37–50), mobile food **54.7** (50–58),
rental inspection **24.9** (18–32), home business **53.5** (48–58), STR
**33.4** (22–40) — total **261** target processes, inside the plan's 250–300
band. The `F0` values are tuned to those targets; if the implementer changes any
panel dispersion, re-tune `F0` and update this table rather than accepting a
drift. `build.py` prints the realised counts;
`tests/test_generator_county_panel.py` asserts each statute has **≥ 20**
implementers (below that the per-predicate dispersion estimate degrades toward
W1's problem) and that **≥ 2** statutes have ≥ 45.

### 6.2 `_assign` becomes independent Bernoulli draws

Today `_assign` is a greedy matcher that forces exact implementer counts against
fixed per-jurisdiction loads. At 58 counties that machinery is both unnecessary
and harmful: it induces negative correlation between a county's programs (taking
one slot denies another), which would plant a spurious substitution effect.

Replace with, in `world.build_world` at version 2:

```python
pairs = [(c["id"], d)
         for c in marisol_counties for d in statute_set
         if chance(sub_rng(seed, "impl_draw", c["id"], d), _fit(c, d))]
```

Then enforce two floors so no county and no statute is empty:

1. any county with zero implementations takes its highest-`_fit` statute;
2. any statute with fewer than `min_implementers` (knob, default 20) takes the
   highest-`_fit` non-implementing counties until it reaches the floor.

Both repairs are recorded in `world.json.assignment_repairs` with the county,
statute and reason, because a forced implementation is not a covariate-driven
one and the Bayesian layer should be able to exclude them from a
selection-model check.

`_implementer_counts` and `TARGET_LOAD`/`NEIGHBOR_LOAD` are then dead at version
2; `world._target_load` exists only to report the realised load.

### 6.3 Neighbour state

8 Corvane counties, drawn from the same panel machinery with
`knobs["neighbor_counties"] = 8`, `knobs["neighbor_statutes_per_county"] = 3`,
and a **shifted** size distribution (decade counts `(1, 4, 3, 0)`) so the
look-alikes are mid and small counties: a distractor is most confusing when it
resembles a data-poor target. Corvane statutes keep the existing `C**` look-alike
mechanism (different cite, 1–3 different elements, a different crisp constant).

### 6.4 `_why_not` rewritten on covariates

Non-implementation is now informative, so its `why` must state the covariate
reason, in the county's own institutional voice, because these strings are
rendered into documents and are the only evidence a solver has that the absence
is deliberate:

| condition | `why` |
|---|---|
| threshold not met | "the chapter applies to an agency serving a population of 75,000 or more; the county's population is {pop:,}" |
| `pct_unincorporated < 12` | "almost all of the county's population is inside incorporated cities, which permit their own {domain}; the county's program would serve {unincorporated:,} residents" |
| `rucc <= 2` and domain is `well_permit` | "the county is served by municipal water districts; fewer than {n} active domestic wells are on record" |
| `staff_abs` in the bottom decile | "no dedicated staff: the program would fall to the {lead_permits} counter, which the Board declined to fund in the {year} budget" |
| otherwise | "optional under {cite}; not adopted (no Board sponsor, no dedicated staff)" |

Keep the existing version-1 `_why_not` verbatim behind the version branch.

---

## 7. Capacity-dependent disclosure: the disappearing commons, planted

Plan §3.2, with the CCW correlation made explicit and the user-evidence hurdle
added.

### 7.1 The publication logit

`capacity.publish_logit(kind, county, rule, proc) -> float`, consumed by
`visibility.plan_artifacts` in place of `p = knobs[knob]`:

```
logit p_publish(k, c) = A0[k]
                      + A_SIZE   * z_log_staff_abs(c)
                      + A_LOAD   * z_log_staff_per_case(c, p)
                      + A_PORTAL * portal(c)
                      + A_RURAL  * z_rucc(c)
                      + A_BUDGET * z_log_budget_per_capita(c)
                      + SIGMA_U  * u_c                      # shared county effect
                      + KIND_ADJ(k, rule, proc)             # the existing per-kind logic
```

`A0[k] = logit(knobs[<the kind's existing knob>])`, so **the DESIGN table's
values become the population-average publication rates** and a version-2 world
with all slope coefficients zero and `SIGMA_U = 0` reproduces W1's expected
artifact mix. That is the compatibility hinge: the knobs keep their meaning.

| coefficient | default | why |
|---|---:|---|
| `A_SIZE` | **+0.55** | absolute staff, not staff per capita. A county with 200 planning staff has a webmaster, a public-information officer and a policy analyst; a county with 3 does not. |
| `A_LOAD` | **+0.20** | slack time is what gets a page written |
| `A_PORTAL` | **+0.45** | a portal vendor ships a program-page template |
| `A_RURAL` | **−0.35** | rural counties are *information-different*, not information-free (CCW): the coefficient is modest and the kind intercepts do the rest — a rural county still publishes an ordinance (it must) and often a fee schedule, but rarely a FAQ, a dashboard or an SOP |
| `A_BUDGET` | **+0.15** | small, and tagged `real_coverage: "blocked"` |
| `SIGMA_U` | **1.10** | the shared county random effect, §7.2 |

`KIND_ADJ` is the existing per-kind logic in `plan_artifacts`, converted from
probability overrides to logit offsets: statute-mandated checklist `+3.4`
(≈0.97), `admin_policy` instrument for ordinance/fee resolution `−3.9`
(≈0.12), `admin_policy` for staff report/minutes `−4.4`, adopting instrument is
itself a fee resolution `+1.3`, newsworthy `+1.1`. Preserve every existing
`note` string; append the logit arithmetic to it so `spec.why` still explains
the draw.

Three intercept exceptions, all from CCW:

- `official_stats` (the county dashboard, i.e. a real processing-time statement):
  `A0` lowered to `logit(0.18)` and `A_SIZE` raised to **+0.95**. Real: four
  real processing-time statements out of fifteen counties, against eleven
  instances of vendor boilerplate.
- **Vendor boilerplate is a new artifact kind**, `vendor_boilerplate`: a page
  that *looks* like a processing-time statement but states the vendor's generic
  language, published with probability `logistic(logit(0.55) + 0.7*portal(c))`.
  Its single `reveals` entry is a `process`-level `timing` fact at fidelity
  **`wrong`**, value drawn from a fixed vendor string ("most applications are
  processed within 10 business days"), with `source_family: "vendor_boilerplate"`.
  This is the highest-value cheap addition from CCW: eleven of fifteen counties
  had one, it is the single most common timing "source" in the real corpus, it is
  uninformative, and no current benchmark artifact models a confidently wrong
  uniform claim. It must also appear in `ceiling.json` as `only_wrong` for the
  timing field when it is the sole timing source.
- `sop`: `A0` stays at `logit(0.10)` but `A_SIZE` = **+0.80** — an SOP surfaces
  through a records request or an audit, and only large counties get audited.

### 7.2 The shared county effect: why timing disclosure correlates with process disclosure

[The CCW research](scoping/2026-09-16-ccw-15-small-counties-findings.md) found
that **four of fifteen counties published a policy and those were the same four
that published a real processing time**. Drawing kinds
independently cannot produce that; a shared county effect can.

```
u_c ~ Normal(0, 1)        # one draw per county: sub_rng(seed, "disclose_u", cid)
```

entering **every** kind's logit with the same coefficient `SIGMA_U = 1.10`. So
`u_c` is a single latent "this county publishes things" propensity, exactly the
`u_c` in the plan's §4.2 estimand `logit pi(kind, c) = b_kind + lambda' x_c +
u_c`. Planting the estimand's own structure is deliberate: recovery of
`SIGMA_U` and of `lambda` is then a well-posed simulation-based-calibration
exercise.

Acceptance target (`tests/test_generator_disclosure.py`): across 58 counties the
phi coefficient between `has(sop | staff_report | audit_excerpt)` ("published a
policy") and `has(official_stats)` ("published a real processing time") is
**≥ 0.45**. The real 4-of-15-and-the-same-4 is a point estimate from fifteen
counties with a wide interval, so demanding φ ≈ 1.0 would overfit an anecdote;
0.45 reproduces the qualitative finding without pretending to its precision.

Consequences the plan predicts and that the implementer should see in
`counts.json`: a mega county produces **20–26** target artifacts for one program
and a tiny county **3–5**; the information ceiling becomes county-varying, with
mean `exists_exact` falling from ≈0.86 in the top size class to ≈0.45 in the
bottom. `build.py` must print ceiling coverage **by size class**, not only the
global mean, or the headline fairness quantity is invisible.

### 7.3 User evidence: a hurdle, then a volume

Nine of 58 real counties have **no candidate subreddit at all** (Alpine, Amador,
Calaveras, Colusa, Glenn, Mariposa, Modoc, Sierra, Trinity — 183,972 people,
0.47% of California), and the count of candidate subreddits correlates with log
population at **r = 0.741**. A single continuous "fewer posts in small counties"
term would misfit those nine to *approximately* zero rather than modelling them
as *structurally absent*, which is a different claim and the one the paper makes.

Two stages, in `capacity.py`:

```python
def channel_exists(county, channel, rng) -> bool:
    # channel in {"county_sub", "statewide_sub", "regional_forum", "review_site",
    #             "grand_jury", "staff_review_site"}
    return chance(rng, logistic(H0[channel] + H_POP[channel] * z_log_pop(county)))

def post_volume(county, proc, channel, rng) -> int:
    if not channel_exists(county, channel, rng):
        return 0
    lam = exp(V0[channel] + V_POP * z_log_pop(county) + V_CASELOAD * z_log_caseload
              + V_DELAY * z_log_median_days + SIGMA_V * v_c)
    return rng_poisson(rng, lam)
```

| channel | `H0` | `H_POP` | expected zero counties | real anchor |
|---|---:|---:|---:|---|
| `county_sub` | **+2.10** | **+1.35** | **9.7 of 58** | measured exactly: 9 of 58 |
| `statewide_sub` | +9.9 | 0 | 0 | `r/California` always exists |
| `regional_forum` | +0.4 | +0.6 | ≈ 18 | City-Data county subforums thin out |
| `review_site` | +2.2 | +0.9 | ≈ 3 | Google/Yelp reviews of county offices exist almost everywhere (plan A9) |
| `grand_jury` | **+9.9** | 0 | **0** | every county publishes a civil grand jury report annually (plan A9: the best candidate for rural coverage) |
| `staff_review_site` | −0.2 | +1.1 | ≈ 28 | Glassdoor/Indeed reviews by county staff exist only where there are enough staff |

`H0 = 2.10`, `H_POP = 1.35` puts the expected number of `county_sub`-less
counties at **9.7 of 58** (measured over 80 seeds, per-seed range 3–15) against
the real 9. `H0 = 1.55`, this spec's first draft, gives 13.6 and so overstates
the disappearing commons by 50% — which would flatter the paper's own
hypothesis, the worst direction for a generator to err in. Verify the mean to
±2 over seeds 1–40 and allow the per-seed range 3–15.

Volume defaults: `V0["county_sub"] = 0.35`, `V_POP = 0.85`, `V_CASELOAD = 0.30`,
`V_DELAY = 0.55` (delay generates posts — this is the selection mechanism the
plan's κ is meant to estimate), `SIGMA_V = 0.6` with `v_c` a **second** shared
county effect, correlated with the disclosure effect `u_c` at ρ = 0.3 (draw
`v_c = 0.3*u_c + sqrt(1-0.09)*rng.gauss(0,1)`), because a county that publishes
nothing also tends to have a thin civic internet.

`rng.py` gains `poisson(rng, lam)`: Knuth's product-of-uniforms for `lam <= 30`,
normal approximation with rounding and a zero floor above. Adding a function
consumes no draws in existing streams.

**`select_personas` must change shape.** Today it is a pure complaint-selection
filter over the whole log, so a 200-case process always yields personas and the
thread count is `len(posters) // 3`. At version 2:

1. draw `n_posts = post_volume(county, proc, "county_sub", rng)`;
2. rank the eligible cases by complaint propensity (the existing
   `complaint_selection` weights) and take the top `n_posts` **by weighted
   sampling without replacement**, so the *selection* is still the planted κ but
   the *volume* is the planted availability;
3. `n_posts == 0` produces no thread, and `ceiling.json.timing_ceiling`
   correctly reports `n_posts_with_timing: 0` and
   `best_estimate_from_posts: null` — the validator already asserts that pair.

The plan's §4.4 identification of κ then works exactly as it says: κ is
estimable on the counties that have both `official_stats` and forum posts, and
transferable to the counties that have only posts. Because `u_c` and `v_c` are
correlated at only 0.3, a reasonable number of counties (≈14 at these defaults)
have both. Assert **≥ 10** such counties in
`tests/test_generator_disclosure.py`; that number is the sample size for the
single most important measurement parameter in the plan, and if it is small the
coefficients must be retuned, not the claim weakened.

### 7.4 Other channels become artifact kinds

The four non-reddit channels are cheap to add and they carry the plan's A9
argument (if grand jury reports and Google reviews cover rural counties where
reddit does not, "the commons moves" rather than "vanishes" — a different and
better paper). Add to `visibility.KIND_META` and `decision.CRITERION_RULES`:

| new kind | audience | register | what it reveals | notes |
|---|---|---|---|---|
| `vendor_boilerplate` | applicant | municipal_web | one `process.timing` at `wrong` | §7.1 |
| `grand_jury_report` | public | bureaucratic_memo | 1–3 `staff_only` steps at `exact` plus one `process.timing` at `approximate` with a **backlog** framing, and volumes | exists for **every** county; raises the rural ceiling; the strongest argument that rural counties are information-different rather than information-free |
| `office_review` | public | reddit_casual | 1–2 `applicant_facing` steps at `vague` plus counter wait time | Google/Yelp reviews; near-universal |
| `staff_review` | public | reddit_casual | one `staff_only` step at `vague`, `is_staff_insider: true` | Glassdoor/Indeed; the corpus currently has **no** staff-side evidence class at all |

Each needs: a `KIND_META` row, a branch in `visibility.reveals_for`, a URL
pattern in `specs._url_for`, a `_links_for` row, a style-guide stub under
`benchmark/synth/style/`, and a paragraph in
`benchmark/synth/briefs/RENDER_BRIEF.md` and `VERIFY_BRIEF.md`. The render brief
must state that a `vendor_boilerplate` page is *confidently wrong* and must not
hedge, because its whole function is to be a plausible trap.

---

## 8. Discretion dispersion at 58 draws

`decision.py` already draws each county's reading of a standard from a weighted
ordered space via `discretion_spread`. Three changes make the dispersion
*measurable* and *structured* at 58 draws.

### 8.1 Strictness as an ordered logit on covariates

Today `resolve_readings` picks the modal reading with probability
`1 - discretion_spread` and otherwise draws from the planted weights — so
strictness is i.i.d. across counties and carries no covariate signal. Replace,
at version 2, with a **county strictness propensity** that is shared across all
of that county's predicates:

```python
# capacity.py
def strictness_propensity(county, rng) -> float:
    return (D_RURAL   * z_rucc(county)
          + D_STAFF   * z_log_staff_abs(county)
          + D_EDU     * z_pct_bachelors(county)
          + D_LINEAGE * lineage_offset(county)          # §8.2
          + SIGMA_S   * rng.gauss(0, 1))                # eps_c
```

| coefficient | default | direction and rationale |
|---|---:|---|
| `D_RURAL` | **−0.30** | more rural ⇒ marginally **more lenient**. Chosen to match the one real signal we have on the same axis: rural counties are slightly *faster* (corr(rucc, days) = −0.27), and a lenient reading corrects and denies less, hence is faster. The plan's §3.3 asks "are rural counties stricter" and expects yes; the data say the reverse, weakly. |
| `D_STAFF` | **+0.25** | more absolute staff ⇒ **stricter**: a county with a plan-check bureau can afford to enforce a 7'6" ceiling standard; a county with one technician cannot. |
| `D_EDU` | **+0.30** | better-educated counties read standards **more strictly**. Measured: pct bachelor's correlates with the county ministerial share at −0.427 (ADU) and −0.564 (single-family), i.e. educated counties are *less* likely to route housing ministerially. Education replaces median income, which predicts the same thing slightly less well and correlates with it at 0.840. |
| `D_LINEAGE` | **+0.85** | the copied cluster's strictness, §8.2 |
| `SIGMA_S` | **0.80** | county idiosyncrasy: must dominate, for the same reason as §5 |

Implied share of strictness variance explained by covariates ≈ **0.22**, and
unlike this spec's earlier drafts there is now a real measurement to calibrate
against. [The discretion report §4](scoping/2026-09-16-apr-discretion-variation.md)
correlates the county ministerial share — a directly observed *reading* of a
statute — against the 26 populated covariate columns:

| statute / category | best predictor of the county's reading | best abs r | implied R² |
|---|---|---:|---:|
| ADU (30 counties) | pct bachelor's degree, **−0.427** | 0.43 | 0.18 |
| single-family detached (42 counties) | median income **−0.572**; education −0.564; rurality **+0.395** | 0.57 | 0.33 |
| 5+ units (11 counties, too few to use) | rurality +0.65 | — | — |

Covariates explain **18–33%** of the variance in the real observed reading, and
the planted 0.22 sits inside that range. Two of the three signs are now measured
rather than guessed: **poorer, more rural, less-educated counties are more likely
to call housing ministerial**, i.e. *more lenient*. That confirms `D_RURAL < 0`
(rural ⇒ more lenient) and means the income and education terms should be
**positive** on strictness. Revised defaults: `D_RURAL = −0.30`,
`D_STAFF = +0.25`, and **`D_EDU = +0.30`** on `z_pct_bachelors` in place of
`D_INCOME` — education is the stronger real predictor for ADU, and the two
correlate at 0.840 so only one may enter. `SIGMA_S = 0.80` still dominates,
which is right: even the best real predictor leaves two thirds of the reading
variance unexplained.

Record in `planted.notes` that these are calibrated to a 30–42-county
measurement of one program family and must not be read as a general law about
county strictness.

Then per predicate, an **ordered logit over the reading space's strictness
ranks**, replacing the direct `weighted(rng, ...)` draw:

```python
# decision.py:resolve_readings, version-2 branch
def _ordered_reading(space, propensity, spread, rng):
    # space entries carry `strictness` (0 = most lenient) and `weight` (the
    # planted marginal). Cutpoints are the weight-implied cumulative logits, so
    # with propensity 0 and spread 1 the marginal reproduces today's weights.
    taus = _cutpoints_from_weights(space)
    latent = propensity * spread + rng.logistic(0, 1)
    return space[sum(1 for t in taus if latent > t)]
```

`_cutpoints_from_weights` sorts the space by `strictness`, accumulates the
weights, and sets `tau_k = logit(cumulative_k)`. Two invariants that must hold
and be tested:

- **`spread = 0` ⇒ every county draws the modal reading** (the existing knob
  semantics: "0 = every jurisdiction reads alike"). Implement as an explicit
  early return, not as a limit.
- **`propensity = 0, spread = 1` ⇒ the marginal over counties equals the planted
  `weight` vector** to within Monte-Carlo error. Test with 4,000 synthetic
  counties in `tests/test_generator_discretion.py`.

`rng.py` gains `logistic(rng, mu=0, s=1)` as `mu + s*log(u/(1-u))`.

`local_rule_truth.readings[pid]` gains `"propensity": round(propensity, 3)` and
`"rank": strictness` so the scorer can regress recovered strictness on
covariates without re-deriving anything.

### 8.2 Template lineage extended from choices to readings

`local_rules.py` already copies **choices, added elements and stricter standards**
from an earlier adopter with probability `p_template_lineage` (0.4), leaving a
tell. It does **not** copy *readings of standards*, so today a lineage cluster
agrees on its ordinance text and disagrees on how it reads the ordinance —
backwards.

New module `lineage.py`, called from `world.build_world` (so the clusters exist
before local rules are built):

```python
def assign_clusters(counties, statute_set, seed, knobs) -> dict:
    """(statute, county) -> {"cluster": int, "role": "origin"|"adopter",
                             "source": cid|None, "region": str}"""
```

Algorithm, per statute:

1. Order the implementing counties by adoption date (as `local_rules` already
   does via `dated`).
2. The first `n_origin = max(2, round(0.18 * n_impl))` counties are **origins**
   (own draw, no source). At 52 implementers that is 9 origins.
3. Each later county copies with probability
   `p_lineage(c) = logistic(logit(p_template_lineage) + L_SMALL * (-z_log_staff_abs(c)))`
   with `L_SMALL = 0.55`: **small counties copy more** (they have no staff to
   write an ordinance — the CSAC model-ordinance and ABAG/MTC regional-template
   mechanism). This is a planted covariate effect on lineage itself and must be
   recorded.
4. A copier picks its source with weights `region_match * 3.0 + size_class_match
   * 1.5 + 1.0` over all earlier adopters — so clusters are **regional**, which
   is the realistic and adversarial part.
5. `lineage_offset(county)` used by §8.1 is the cluster's origin propensity, so
   a cluster shares strictness: `propensity_c = D_LINEAGE * propensity_origin +
   (other terms)`.

What gets copied at version 2, in `local_rules.build_local_rules` pass 2:

| copied | already | new |
|---|---|---|
| `choices` (minus fee and portal) | yes | unchanged |
| `added_elements`, `stricter_standards` | yes | unchanged |
| **readings of `standard` predicates** | no | **yes** — copy the source's `reading` for every `standard` predicate, then re-draw with probability 0.25 (a county that copies an ordinance still sometimes applies it differently) |
| **the route reading (`P4`)** | no | **yes** — it is a `standard` predicate, so the row above covers it; a lineage cluster therefore shares its *routing rule*, which is the mechanism behind the real concentration of discretionary review in a handful of neighbouring jurisdictions |
| the tell | yes | add two: "the findings recite {source}'s unit count" already exists; add "the checklist's threshold table still carries {source}'s figure" (a **reading**-level tell, which is the new discoverable) |

**Why this matters and why it is a trap.** It plants *spatial correlation in the
discretion residual*. The plan's §4.3 estimand
`reading_{p,c} ~ OrderedLogit(theta_p + delta' x_c + xi_{p,c})` with
`xi ~ Normal(0, omega_p²)` assumes the `xi` are independent across counties.
Under lineage they are not: the effective number of independent readings is far
below 58. Concretely, at `p_template_lineage = 0.4` and these cluster weights,
the expected number of distinct clusters per statute is ≈ 14–18, so the
effective sample size for `omega_p` is closer to 15 than to 52. Two required
consequences:

1. `world.json.planted.lineage` records, per statute, the cluster partition, the
   number of clusters, and the **planted effective number of independent
   readings** `n_eff = (sum_k n_k)² / sum_k n_k²` per predicate.
2. `pipeline/procbench/decision_metrics.py:cross` must report the entropy ratio
   **against `n_eff`, not against 58**, and a model that reports a
   58-independent-draw interval must be scored as overconfident. Add a
   `lineage_aware` field to its output and a test that the naive and
   lineage-aware intervals differ.

Rejected alternative: draw readings i.i.d. and add a separate spatial random
effect at fit time. Rejected because the clustering is *mechanistic* (one county
literally copied another's document, and the copy carries a tell that a solver
can find), so planting it as a lineage graph gives the benchmark a recoverable
object — "which counties copied which" — that a spatial covariance matrix does
not.

### 8.3 Statute shapes spanning prescriptive to minimal

`domains.py` already carries `shape ∈ {prescriptive, mid, minimal}`. Two
additions make dispersion track shape:

```python
# decision.py
SHAPE_SPREAD = {"minimal": 1.30, "mid": 1.00, "prescriptive": 0.55}
```

multiplying `knobs["discretion_spread"]` per statute, so a minimal statute's
readings disperse widely and a prescriptive one's barely. And the W2 statute set
(§11.1) is chosen to span shapes: 2 minimal, 1 mid, 3 prescriptive, with
`rental_inspection` (prescriptive) contributing **two** standard predicates and
the others one.

**The spike-plus-tail requirement.** The discretion report's first instruction
to W2 is blunt: "a synthetic world calibrated to a *wide* dispersion of readings
on a strongly-ministerial statute would be miscalibrated: the real dispersion is
a spike with a thin, concentrated tail. §3.3's 'discretion dispersion at 58
draws' should be re-specified to reproduce a mass point plus a tail, not a broad
distribution." Today's `decision.PREDICATES` weights are broad — (0.30, 0.50,
0.20), (0.35, 0.40, 0.25) and similar — which puts 60–70% of counties off the
modal reading. That is right for a genuinely open standard and wrong for a
standard the statute has effectively closed.

Fix with an explicit per-statute weight transform in `decision.py`, applied
before `_cutpoints_from_weights`:

```python
CONCENTRATION = {"prescriptive": 4.0, "mid": 1.6, "minimal": 0.8}

def _concentrate(space, shape):
    # Sharpen (or flatten) the planted reading weights toward the modal one:
    # a tempered categorical. k > 1 makes a mass point; k < 1 flattens.
    k = CONCENTRATION[shape]
    w = [r["weight"] ** k for r in space]
    s = sum(w)
    return [x / s for x in w]
```

At `k = 4.0` a (0.30, 0.50, 0.20) space becomes **(0.11, 0.86, 0.03)** — a mass
point with a thin tail, matching the measured 89.1% all-modal share and the
45×-binomial concentrated residual. At `k = 0.8` a broad space stays broad, the
intended behaviour for a minimal statute where the text really does leave the
question open. `SHAPE_SPREAD` modulates *how often* a county leaves its modal
reading; `CONCENTRATION` fixes *how concentrated the space itself is*. They are
separate knobs because the first is a property of the world's hardness and the
second is a property of the statute.

Required consequence for the metrics: with a mass point, **agreement is high by
construction and entropy is low**, so the cross-county headline must not be
"recovered entropy tracks planted entropy" on a prescriptive statute — that is
satisfiable by predicting the modal reading for all 58 counties.
`pipeline/procbench/decision_metrics.py:cross` must additionally report **tail
recall**: of the counties whose planted reading is *not* modal, what share did
the model identify? On a prescriptive statute that is a handful of counties and
it is the entire signal. Add it, and make it the reported quantity whenever
`CONCENTRATION >= 1.6`.

`statute_truth` gains `planted_dispersion`, computed in `statutes.build_statutes`
as the per-predicate Shannon entropy (in nats) of the reading distribution
implied by `weight × SHAPE_SPREAD[shape]`, plus the statute-level mean. The
headline cross-county result the plan asks for — "recovered dispersion tracks
planted dispersion across statutes of different shapes" — is then a
six-point regression with a known slope of 1.0, and
`decision_metrics.cross` must emit both numbers per statute.

Expected planted dispersion at these defaults (nats, mean over a statute's
standard and delegated predicates): `home_business` 1.02, `unpermitted_unit_amnesty`
0.98, `well_permit` 0.88, `str_registration` 0.62, `mobile_food` 0.60,
`rental_inspection` 0.58. Compute and assert in
`tests/test_generator_discretion.py` rather than trusting these to the decimal;
what must hold is the **ordering** (minimal > mid > prescriptive) and a spread
of at least 0.35 nats between the extremes, or the six-point regression has no
leverage.

---

## 9. Outcome structure matching the real data

### 9.1 What the real outcomes are

From the Table A / Table A2 join, per-jurisdiction ADU outcomes: **194,347
approved, 54,382 pending, 1,219 withdrawn, 89 disapproved**
([APR, "The applicant's clock"](scoping/2026-09-16-apr-permit-timing.md)). As
shares of 250,037: approved 77.7%, **pending 21.8%**, withdrawn 0.49%,
disapproved **0.036%**.

[The discretion report §5](scoping/2026-09-16-apr-discretion-variation.md)
measures the same thing on the *application* register (Table A, status stated),
a different and larger base:

| | ADU | single-family detached | 5+ units |
|---|---:|---:|---:|
| applications with a stated status | 130,538 (77.8%) | 90,468 (61.7%) | 8,748 (63.8%) |
| approved | 61.04% | 72.87% | 42.34% |
| **pending** | **38.20%** | 26.62% | **56.70%** |
| withdrawn | 0.66% | 0.44% | 0.73% |
| disapproved | **0.09%** | 0.07% | 0.23% |

and, per jurisdiction with ≥ 100 stated outcomes (193 ADU jurisdictions): median
withdrawal share **0.0035**, p90 0.0273, max 0.1148; median pending share
**0.293**, p90 0.678; **82 jurisdictions (42%) report exactly zero
withdrawals**; only 24 report any disapproval at all.

So denial is a 1-in-1,100 event on this base and 1-in-2,800 on the permit join.
Disapproval is the *wrong outcome to model* for a ministerial program; the
informative outcomes are the **pending backlog** (22–38%, depending on base) and
**withdrawal** — which two fifths of jurisdictions do not report at all, §9.4.

### 9.2 The three-channel outcome model

`simulate.py:simulate_process` gains two channels alongside the existing
predicate-driven denial. The crucial modelling point is that **pending is a
mixture**:

| planted outcome | observable in a permit register | target share | mechanism |
|---|---|---:|---|
| `approved` | approved | **74%** | as today |
| `denied` | disapproved | **0.5%** | as today: a fatal predicate failure or a fixable failure surviving the retry cap. §9.3 makes this rare. |
| `withdrawn` | **withdrawn** | **1.0%** | an explicit applicant act: `p_withdraw` hazard at each applicant-facing step, and the case is *recorded* as withdrawn |
| `abandoned` | **pending, forever** | **10%** | the applicant stops responding: the case sits in the register as pending and is never closed. **Indistinguishable from a live case in the observed data.** |
| `in_progress` | pending | **14.5%** | genuine right-censoring at `as_of`, as today |

`pending` as observed = abandoned + in_progress = **24.5%**, between the real
21.8% (permit-join base) and 38.2% (application-register base), and close to the
real per-jurisdiction **median** pending share of 0.293. Because the two real
bases disagree by 16 points the acceptance band is wide: `register_shares.pending`
in **[0.20, 0.40]**, and the per-county distribution must have a p90 of at least
0.55 (real 0.678) — the backlog is highly unequal across counties, and a
generator that gives every county the same pending share misses the finding.

This is the substantive addition: the real 21.8% pending is a mixture of live
and dead cases, and no administrative dataset distinguishes them. W2 plants the
mixture with **known proportions**, so "estimate the share of the pending backlog
that is actually dead" becomes a scoreable task with ground truth — a new metric
the plan does not have, and one that matters for any real backlog claim.

Implementation:

```python
# capacity.py
p_withdraw_step(county, proc, step_index)  = W0 * (1 + W_DELAY * z_log_wait_so_far)
p_go_quiet_step(county, proc, step_index)  = Q0 * (1 + Q_REWORK * rounds_so_far
                                                     + Q_DELAY  * z_log_wait_so_far)
W0 = 0.0012 per applicant-facing step        # ~1.0% overall
Q0 = 0.0110 per applicant-facing step        # ~10% overall
W_DELAY = 0.8, Q_REWORK = 0.9, Q_DELAY = 1.2
```

Both hazards must be **normalised by the number of applicant-facing steps** the
way `p_abandon_total` already is (`hazard = p_abandon_total /
(n_applicant_steps * 2.4)`), so a 16-step county does not abandon five times as
often as a 7-step county for purely structural reasons. Keep
`knobs["p_abandon_total"]` as the *target overall* and add
`knobs["p_withdraw_total"] = 0.01`, `knobs["p_go_quiet_total"] = 0.10`, with the
same division.

Record per case:

```
rec["outcome"] ∈ {"approved", "denied", "withdrawn", "abandoned", "in_progress"}
rec["closure"] = {"recorded_as": "approved"|"disapproved"|"withdrawn"|"pending",
                  "true_state": <outcome>,
                  "dead_but_pending": bool}       # the planted mixture label
```

and per summary:

```
summ["outcome_shares"]        = {...}             # planted truth
summ["register_shares"]       = {...}             # what a permit extract would show
summ["pending_mixture"]       = {"pending": n, "dead": n, "live": n,
                                 "dead_share_of_pending": x}
```

### 9.3 How this interacts with predicate-driven denial

`decision.py` sets `proc["denial_rate"] = max(0.005,
expected_fatal_fail_rate)` and the simulator denies on a fatal failure or an
unresolved fixable one. To land denial at 0.5% for a ministerial statute without
gutting the decision layer, **change what a fatal failure does, not whether it
happens**:

1. Add `knobs["p_fatal_becomes_withdrawal"] = 0.55`. When a case would be denied,
   with that probability the county instead **invites withdrawal** ("staff advise
   the applicant to withdraw rather than take a denial to the Board"), the case
   is recorded as `withdrawn`, and `rec["decision_basis"]["advised_withdrawal"]`
   records the predicate that caused it. This is real administrative behaviour
   and it is *why* disapprovals are vanishingly rare under a ministerial
   statute: the denial is converted, not avoided.
2. Add `knobs["p_fatal_becomes_quiet"] = 0.25`. Otherwise the applicant simply
   stops (the fixable failure they cannot cure), and the case goes to
   `abandoned` / recorded `pending`.
3. The residual 20% are recorded denials. With a per-statute
   `expected_fatal_fail_rate` of 3–10%, that gives a recorded disapproval rate
   of 0.6%–2.0% — an order of magnitude above the real ADU 0.036% but the right
   *order* for a program set that includes non-ministerial statutes
   (`rental_inspection` and `str_registration` genuinely deny). Per-statute
   targets in `capacity.PLANTED["outcomes"]`: amnesty and home business 0.4%,
   well permit 0.8%, mobile food 1.2%, STR 2.5%, rental inspection 3.5%.

**Consequences that must be honoured elsewhere**:

- `visibility.complaint_selection` gains a `"withdrawn"` class (default 0.45,
  between `denied` 0.5 and `abandoned` 0.25): someone advised to withdraw posts
  about it, and that post is the *only* public evidence the conversion happened.
  This is a new and genuinely interesting availability asymmetry: the register
  says "withdrawn", the forum says "they told me I'd be denied so I pulled it",
  and only the join recovers the decision.
- `official_stats` must report the **register** shares, not the planted ones,
  and must state its population explicitly (the existing `measurement_clock`
  machinery already does this; add `population: "register_recorded_closures"`).
- `ceiling.py` gains `outcome_ceiling`: whether the planted dead-share of
  pending is recoverable at all from the artifacts about this process (usually
  not — which is the finding).
- `simulate.summarize`'s existing `denial_rate` / `denial_rate_all` pair keeps
  its meaning; add `withdrawal_rate`, `withdrawal_rate_advised` and
  `dead_share_of_pending`.

### 9.4 Withdrawal-reporting propensity: a disclosure model on an outcome field

The discretion report's fifth instruction to W2: "**W2 needs a
withdrawal-reporting propensity, not just an abandonment channel.** 42% of
jurisdictions reporting zero withdrawals is a disclosure model, identical in form
to §4.2's `pi(kind, c)`, and it must be fitted before the withdrawal field can
calibrate anything."

This is the same object as §7.1's publication logit, applied to a **field of an
administrative dataset** rather than to a document — which is a genuinely new
kind of missingness for this benchmark, and the one that matters most for any
real backlog claim:

```python
# capacity.py
def reports_withdrawals(county, rng) -> bool:
    return chance(rng, logistic(RW0 + RW_SIZE * z_log_staff_abs(county)
                                    + RW_PORTAL * portal(county)
                                    + SIGMA_U_W * u_c))       # the SAME u_c as §7.2
RW0        = 0.35      # -> about 58% report, matching 111 of 193 real jurisdictions
RW_SIZE    = 0.55
RW_PORTAL  = 0.40
SIGMA_U_W  = 0.60
```

`u_c` is deliberately the **same** shared county disclosure effect as §7.2, at a
lower loading: a county that publishes no policy and no processing time also
tends not to populate the optional fields of its state filing. That makes
withdrawal-reporting, document publication and forum volume three manifestations
of one latent, which is the structure the plan's §4.2 estimates and exactly the
structure a real analyst would wrongly treat as three independent facts.

Implementation: when `reports_withdrawals(c)` is false, every `withdrawn` case in
that county is recorded as `closure.recorded_as = "pending"` while
`closure.true_state` stays `withdrawn`. Consequences:

- `summ["register_shares"]` for such a county shows **zero** withdrawals and an
  inflated pending share, reproducing the 42%-report-zero pattern and the
  p90 pending share of 0.678.
- `summ["reporting"] = {"reports_withdrawals": bool, "withdrawals_suppressed": n}`
  is the planted truth for scoring.
- The **union** of the two mixtures is now what "pending" means: live cases,
  dead-and-quiet cases, and withdrawn-but-unreported cases. Three components,
  with planted proportions, from one observable. That is the measurement problem
  in its real form, and it is the strongest available answer to "what does a
  Bayesian layer buy over reading the dashboard".
- Acceptance: share of counties reporting zero withdrawals in **[0.32, 0.52]**
  (real 0.42); correlation between `reports_withdrawals` and
  `has(official_stats)` **≥ 0.25** (they share `u_c`); withdrawal share against
  median applicant clock, Pearson in **[0.00, 0.30]** (real +0.125, Spearman
  +0.236 — the right sign, too weak to build on, and W2 must not plant it
  stronger than the data support).

---

## 10. The fetch-blocking error source

### 10.1 Why it is a third error source, not a variant of the two we have

DESIGN's error decomposition is availability / retrieval / reconciliation /
disentanglement, and `ceiling.json` implements availability as "no artifact
reveals this fact". Fetch-blocking is neither:

- **not availability**: the document exists, is indexed, and *does* reveal the
  fact. The ceiling should still credit it as *in principle* available.
- **not retrieval failure**: the solver's query was right and the document
  ranked first. Nothing about the search strategy was wrong.
- it is **reachability**: the host refuses the client. The consequence is that
  the achievable ceiling is strictly below the information ceiling, by an amount
  that is a property of the *county*, not of the solver.

Real anchors: **six of fifteen county sheriff sites blocked a scripted fetch
outright** ([CCW](scoping/2026-09-16-ccw-15-small-counties-findings.md)), **the State Controller returns HTTP 403 to scripts** (blocking
county FTE and general-fund columns in A7 — the keystone covariate table), and
the real-corpus collection hit Justia, LADBS, sanjoseca.gov and El Dorado County
the same way (DESIGN "Remaining, unfixed discrepancies", item 1, which already
proposes `p_403_to_bot`). W2 implements the county-correlated version.

### 10.2 The planted form

`capacity.p_fetch_blocked(county, spec_kind, publisher_class) -> float`:

```
p = PLATFORM_BASE[site_platform(c)] * KIND_MULT[kind] * PUBLISHER_MULT[class]
```

| `site_platform` | `PLATFORM_BASE` | rationale |
|---|---:|---|
| `cdn_fronted` | **0.72** | a Cloudflare-style challenge page; the mega/large-county pattern |
| `legacy_aspx` | **0.45** | a WAF that 403s any non-browser user agent (the El Dorado pattern) |
| `wordpress_selfhost` | 0.18 | sporadic |
| `municipal_cms_a` | 0.06 | a vendor CMS that serves scripts fine |
| `municipal_cms_b` | 0.10 | |

`KIND_MULT`: 1.0 for anything on the county host (`program_page`, `form`,
`checklist`, `faq`, `fee_schedule`, `official_stats`, `vendor_boilerplate`,
`sop` when self-hosted, `audit_excerpt`, `grand_jury_report`); **0.25** for
`legislative_host` documents (Legistar-style systems are usually open); **0.0**
for off-host artifacts (`third_party_guide`, `news`, `reddit_thread`,
`forum_thread`, `office_review`, `staff_review`, `bill_analysis`, the statute
text and the code host).

`PUBLISHER_MULT`: 1.0 for a county; **2.0** for the one **state-agency**
publisher class, capped at 0.95 — the State Controller wall. Concretely: the
Marisol state agency's dashboard (the state-level `official_stats` equivalent,
which reports per-county volumes and is the *unselected sample* the plan's §4.4
needs to identify κ) is blocked with probability 0.85. That is an unpleasant,
realistic and deliberately chosen trap: the single most valuable document in the
world is the hardest to reach, exactly as it is in reality.

Because `site_platform` is drawn once per county, blocking is **correlated within
county**: either most of a county's own documents are reachable or most are not.
Measured over 80 seeds at the platform weights of §2.5: **13.4 of 58** counties
(range 7–24) are `cdn_fronted` and so block ≥ 60% of their own documents, and
**21.1 of 58** (range 13–31) are `cdn_fronted` or `legacy_aspx` and block ≥ 40%.
The CCW anchor is 6 of 15 county sites blocking outright, i.e. 40% of counties
or 23 of 58, which the ≥ 40% figure brackets. Assert 13–31 for the ≥ 40% count
and 7–24 for the ≥ 60% count in `tests/test_generator_retrieval.py`.

### 10.3 Representation

Every `artifact_spec` gains a `fetch` block (schema
`benchmark/synth/schemas/artifact_spec.schema.json`):

```json
"fetch": {
  "blocked": true,
  "mode": "http_403" | "cloudflare_challenge" | "js_shell" | "pdf_scanned",
  "status": 403,
  "body_if_blocked": "<the challenge/denial text a scraper would receive>",
  "workaround": "wayback" | "browser" | "none",
  "wayback_snapshot_date": "2024-07-11" | null,
  "why": "site_platform=cdn_fronted (PLATFORM_BASE 0.72) drew 0.34"
}
```

Four modes, not one, because they differ in what a solver can do:

| mode | share of blocked | what the solver gets | workaround |
|---|---:|---|---|
| `http_403` | 0.45 | a one-line denial | `wayback` with p 0.4, else none |
| `cloudflare_challenge` | 0.30 | a challenge page with no content | `browser`, i.e. never for a scripted agent |
| `js_shell` | 0.15 | **navigation only** — the real LADBS/Socrata/PowerBI pattern: the fetch succeeds, returns 200, and contains no program facts | none; the trap is that it looks like a success |
| `pdf_scanned` | 0.10 | garbled extracted text (the Sonoma grand jury "wi6in l5" for "within 15") | none; the facts are present but corrupted, so this one degrades *fidelity* rather than removing the document |

`js_shell` and `pdf_scanned` are the important ones because a solver cannot
detect them by status code. For `pdf_scanned`, the render brief must instruct
the renderer to emit a *deliberately OCR-corrupted* variant of the text
(digit/letter substitutions: 1↔l, 0↔O, 5↔S, plus 8% character dropout), and the
verifier must be told that a corrupted document's facts count as fidelity
`vague`, not `exact` — so `ceiling.py` must downgrade their contribution.

### 10.4 Consequences in the ceiling, the mock web, and the metrics

1. `ceiling.py:build_ceiling` splits the existing coverage block:
   - `information_ceiling` — unchanged, computed over **all** specs (what a
     perfectly-reaching agent could learn). This preserves every W1 number's
     meaning.
   - `reachable_ceiling` — computed over specs with `fetch.blocked == false`,
     plus `pdf_scanned` specs at downgraded fidelity.
   - `reachability_gap` = the difference, per field and overall, and the list of
     `unreachable_ids`. **The gap is a per-county quantity and is the headline
     number for the fairness claim**: report it by size class and by platform.
2. `pipeline/procbench/web.py:fetch` must honour `fetch.blocked`: return the
   `body_if_blocked` with the status, log the block in `trace.jsonl`, and offer
   `web.py --wayback <url>` as an explicit alternate tool so that
   workaround-seeking behaviour is measurable. **Search must still return the
   blocked document** (it is indexed) — the whole point is that ranking and
   reachability are separate failures.
3. `pipeline/procbench/score.py` gains a fourth error term
   `reachability_loss = information_ceiling_recall - reachable_ceiling_recall`,
   reported alongside availability. The four-way decomposition in DESIGN §1
   becomes five-way, and DESIGN.md must be amended to say so.

---

## 11. Volume, rendering budget and partitions

### 11.1 The statute set

Six statutes from the existing twelve domains, chosen for shape spread, for
county-appropriateness, and for real-program correspondence. `knobs["statute_set"]
= "w2_core"` resolves to:

| statute | domain | shape | standard preds | real analogue | expected implementers |
|---|---|---|---:|---|---:|
| S01 | `unpermitted_unit_amnesty` | minimal | 1 | ADU amnesty / AB 2533 §66311.7 — the flagship | 51 |
| S05 | `home_business` | minimal | 1 | the maximal-discretion, minimal-evidence contrast (the General Assistance role) | 54 |
| S11 | `well_permit` | mid | 1 | county environmental health: wells, and the rural inversion | 43 |
| S02 | `str_registration` | prescriptive | 1 | visitor-economy gating; a genuine denial rate | 33 |
| S06 | `mobile_food` | prescriptive | 1 | the county as local enforcement agency — near-universal | 55 |
| S08 | `rental_inspection` | prescriptive | **2** | the most-standards statute, so the widest per-statute predicate set | 25 |

Total ≈ **261 target processes** (measured over 80 seeds, §6.1), 24 look-alike
Corvane processes. Every county
performs the same **task types** across its programs (intake screen, review,
inspection, decision), which is the crossed design the audit says is the
structural fix for the 13%-learned agency block — the plan's §4.5. Assert in
`tests/test_generator_county_panel.py` that every `task_type` appears in ≥ 40
counties and that no (agency_class, task_type) cell is empty.

Rejected alternative: four statutes. Rejected because `rental_inspection` at 26
implementers and `str_registration` at 33 are the two that gate on covariates
strongly, and dropping either removes the only statutes where non-implementation
is informative; with six, the median county runs 4 programs, which is what §5.3
needs for the within-county `staff_per_case` contrast.

### 11.2 Applicant volume

`simulate_all` takes `n` from `capacity.n_applicants(county, proc, knobs)`
instead of the flat `knobs["n_applicants"]`:

```
n = clip(round(N_BASE * caseload(c, p) / CASELOAD_REF), N_MIN, N_MAX)
N_BASE = 120, CASELOAD_REF = median caseload over all cells, N_MIN = 25, N_MAX = 200
```

matching the plan's "200 for the largest down to 25 for the smallest". Expected
total ≈ **15,000 records** over 261 processes plus ≈ 1,200 for the neighbour
state. At W1's rate (5,800 records ≈ 9 MB of log) that is ≈ 26 MB of logs, which
is fine, but `build.py` must gain `--knob log_detail=compact` writing
`path` steps without the `visit_index`/`loop_triggers_before`/`fee_charged_dollars`
trio for the spec-only counties, because those fields triple the line length and
nothing in the spec-only tier reads them.

### 11.3 Which 20 counties get rendered, and why spec-only is enough

`build.py` writes `render_manifest.json`:

```json
{"render_tier": ["M03", "M07", ...],        // 20 counties
 "spec_only_tier": [...],                   // 38 counties
 "strata": {"mega": 3, "large": 3, "mid": 6, "small": 5, "tiny": 3},
 "selection_rule": "maximin coverage of the standardised covariate space",
 "why": "..." }
```

Selection (`counties.select_render_tier`): a deterministic greedy **maximin**
over the standardised covariate vector — start from the county closest to the
panel centroid, then repeatedly add the county maximising the minimum Euclidean
distance to those already chosen, subject to the stratum quotas above. This
guarantees the rendered 20 span the covariate space rather than clustering, and
it is deterministic given the panel (no RNG), which matters because the render
budget is spent once.

Additional hard constraints on the render tier, because it is the only tier that
supports text-extraction metrics:

1. ≥ 3 counties with **no** county subreddit (else the zero-user-evidence
   condition is never rendered);
2. ≥ 4 counties with ≥ 60% of their documents fetch-blocked (else the
   reachability term is never exercised on real text);
3. ≥ 2 counties in the same lineage cluster for the same statute (else the
   copied-document tell is never renderable);
4. ≥ 1 county whose `P4` route reading is **non-modal** (so it sends some of its
   cases to discretionary review) and ≥ 1 all-ministerial county, for the same
   statute — the pair is what makes the route recoverable at the text tier, and
   §5.5's weights put only 14% of counties in the first group, so this constraint
   binds;
5. the render tier must include counties from **all three partitions**, in the
   partitions' own proportion (§11.4), or the reserved partition has no
   text-tier evaluation when it is finally opened.

**Why spec-only counties support every structural and cross-county metric.**
The ceiling, the readings, the predicates, the timing truth, the outcome mixture
and the reachability gap are all computed from `specs/` and `truth/`, with no
reference to `artifacts/`. Specifically:

| metric family | needs rendered text? | why |
|---|---|---|
| activity recall/precision vs truth and ceiling | no | `reveals` entries are the ceiling |
| criterion recall, `reading_exact`, `reading_direction` | no | `decision_ceiling` is computed from specs |
| cross-county entropy ratio, per-county agreement, `n_eff` | no | planted readings, from `local_rule_truth` |
| covariate-coefficient recovery (`gamma`, `lambda`, `delta`) | no | the planted coefficients and the realised per-county quantities are in `world.json` and the truth files |
| transfer accuracy (predict a held-out county from covariates) | no | uses the truth timing, not the documents |
| disclosure-propensity recovery (`pi`) | no | "which documents exist" is the spec set |
| reachability gap, availability-aware fairness curve | no | `fetch.blocked` is a spec field |
| **extraction error `epsilon`, LLM controls, search traces, staleness detection, OCR corruption, disentanglement against rendered distractors** | **yes** | these are properties of text |

So the 38 spec-only counties are full participants in the plan's §6 metrics
except the extractor-error and retrieval-strategy families, which is exactly the
split the plan asserts. State it in `render_manifest.json.why` so nobody later
renders 58 counties "to be safe".

### 11.4 The three partitions

`counties.assign_partitions(counties, seed)` writes `partitions.json` and a
`partition` field on every county record:

| partition | counties | purpose | opened |
|---|---:|---|---|
| `calibration` | **14** | the semantic confusion matrices and the compiler's mixture priors and `epsilon` (audit §4's decision rule; plan stage 4) | now |
| `development` | **29** | model fitting, iteration, every published-during-development number | now |
| `reserved` | **15** | opened **once**, after a model is frozen | never until then |

Disjoint by county, **shared by statute and predicate** (the plan's §3.6:
"Predicates and statutes are shared across partitions; counties are not").

Assignment must be **stratified, not random**: within each size class, allocate
counties to partitions in the ratio 14:29:15 by a deterministic round-robin over
the size-sorted order, offset by `sub_rng(seed, "partition")` so the stratum
starts vary with the seed. This guarantees each partition spans the size
distribution — a reserved partition of 15 tiny counties would make the frozen
comparison a different question from the development fit. Validator check
(§12.4): for each partition and each covariate in
`(log_pop, rucc, staff_per_1k, wage)`, the partition mean is within 0.4 sd of
the panel mean, and each partition contains ≥ 1 county from each size class.

Hard rule for the implementer and for every downstream agent: nothing in
`pipeline/` may read a file under a reserved county's id. Enforce it
mechanically — `build.py` writes reserved-county truth under
`worlds/W2/reserved/` with a `RESERVED_DO_NOT_OPEN.md` at the root, and
`pipeline/procbench/*.py` gains a shared loader that refuses paths containing
`/reserved/` unless `PROCBENCH_OPEN_RESERVED=1` is set in the environment. A
convention nobody can violate by accident is worth more than a paragraph in a
plan.

### 11.5 Spec-count arithmetic, and the plan's estimate

W1: 1,315 specs for 38 processes, of which 263 target — so ≈ 6.9 target specs
per process and a 4.0 distractor ratio.

W2 with capacity-dependent disclosure: the mean per-process target artifact
count falls (tiny counties publish 3–5) but the median county is `mid`/`small`,
so the mean lands at ≈ **6.2**. With 261 target processes plus 24 look-alikes:

```
target specs           261 * 6.2                  ≈ 1,620
per-county shared       58 * (2 + 8 generic)      ≈   580
new kinds (§7.4)        261 * 1.4                 ≈   365   (grand jury, reviews, boilerplate)
threads                 261 * 1.1                 ≈   290
--------------------------------------------------------------
target-ish subtotal                               ≈ 2,855
at distractor_ratio 4.0: total                    ≈ 11,400
at distractor_ratio 2.0: total                    ≈  5,700
at distractor_ratio 1.0: total                    ≈  3,800
```

**The plan's §3.5 estimate of "2,500–3,500 specs" is not reachable at
`distractor_ratio = 4.0`**; disclosure capacity reduces target artifacts, but the
spec total is driven by the distractor ratio, which the plan does not change.
Set `knobs["distractor_ratio"] = 2.0` and `knobs["filler_cap"] = 2500` for W2,
giving ≈ 5,700 specs, and record the change as a **deliberate benchmark
difference**: every W1 retrieval number was measured at 4:1 and is not
comparable. DESIGN already flags that the 4:1 ratio may *overstate* difficulty
("for a real permit query the city's own page usually ranks first"), and at 58
counties the *structured* distractors — the same statute in 57 other counties —
are far more confusing than filler, so a lower filler ratio makes the corpus
harder in the way that matters. Say this in `counts.json.notes`.

---

## 12. Backward compatibility and validation

The decision layer set the precedent: a version knob, a version-1 path that is
byte-identical to what came before, and a regression test that asserts it
(`tests/test_generator_decision_model.py`, which pins
`V1_PROCESSES_SHA256 = "bb62658e..."` and the six legacy summary tuples). W2
follows it exactly.

### 12.1 What must stay byte-identical

**Before writing any code**, capture the current output as the version-1
baseline. Two hashes, not one:

```python
# tests/test_generator_county_world.py
# Captured 2026-09-16 from the generator *before* the county layer existed.
V1_LEGACY_SHA256 = "<sha256 of concatenated truth/processes/*.json,
                     TINY_KNOBS, seed 3, decision_model_version=1>"   # must equal
                                     # the existing bb62658e... constant
V2_DECISION_SHA256 = "<same, with decision_model_version=2>"          # NEW constant,
                                     # capture it now; this is today's default output
```

The first already exists and must not move. The second is new and is the one
that catches an accidental change to the *current* default path — the real risk,
since `world_model_version=1` + `decision_model_version=2` is what W1-era worlds
and the whole test suite use.

Byte-identity requirements, in order of importance:

1. `world_model_version=1` builds must produce identical bytes for
   `truth/statutes/`, `truth/local_rules/`, `truth/processes/`, `truth/log/`,
   `specs/`, `ceiling.json`, `tasks.json` and `provenance.jsonl` to the
   pre-change generator at both decision-model versions.
2. `world.json` may gain keys at version 1 **only** if they are absent
   (`None`/not written) rather than present-and-null — the decision layer's rule
   that added metadata does not alter version-1 files. Concretely: do **not**
   write `"planted": null` or `"partitions": null` into a version-1 world.
3. No new RNG stream may be drawn on the version-1 path. The test asserts this
   indirectly through the hash; the implementer should also check by running
   with a patched `sub_rng` that records every path and diffing the path list
   before and after.
4. `benchmark/synth/worlds/W1/` is never regenerated (README: "Never regenerate
   W1 in place"). All version-1 checks build into a temp directory.

### 12.2 New knobs, all defaulting to the version-1 behaviour

```python
# world.py:DEFAULT_KNOBS additions (every one inert at world_model_version 1)
"world_model_version": 1,
"n_counties": 58,
"neighbor_counties": 8,
"neighbor_statutes_per_county": 3,
"statute_set": None,                 # "w2_core" selects the six of §11.1
"min_implementers": 20,
"p_withdraw_total": 0.01,
"p_go_quiet_total": 0.10,
"p_fatal_becomes_withdrawal": 0.55,
"p_fatal_becomes_quiet": 0.25,
"disclosure_county_effect_sd": 1.10,
"user_channel_hurdle": True,
"fetch_blocking": True,
"lineage_readings": True,
"render_tier_size": 20,
"partition_sizes": {"calibration": 14, "development": 29, "reserved": 15},
"log_detail": "full",                # "compact" for spec-only counties
"planted_overrides": {},             # per-coefficient override, for SBC sweeps
```

`planted_overrides` matters for the plan's §6 covariate-coefficient recovery
metric: simulation-based calibration needs **many worlds with different planted
values**, so every coefficient in `capacity.PLANTED` must be overridable by a
dotted path (`--knob 'planted_overrides={"speed.B_DEPTH": -0.25}'`) and the
override must be recorded in `world.json.planted`. Without this the SBC exercise
requires editing source per replicate, which nobody will do.

### 12.3 New tests

| file | asserts |
|---|---|
| `tests/test_generator_county_world.py` | version-1 byte identity at both decision-model versions (§12.1); a version-2 tiny world (`n_counties=6`, `statute_set="w2_core"`, `only_domains` two statutes) builds and validates with 0 errors; `world.json.planted` round-trips through `planted_overrides`; no `J*`/`K*` id appears in a version-2 world and no `M*`/`N*` id in a version-1 world |
| `tests/test_generator_county_panel.py` | the panel reproduces the measured marginals over seeds 1–40: decade counts exactly (3,19,26,10); `corr(ln pop, staff_per_1k)` in [−0.80, −0.62] (real −0.73); `corr(rucc, staff_per_1k)` in [0.58, 0.78] (real 0.69); `corr(ln land, ln pop)` in [−0.25, 0.30] (real 0.04); RUCC marginal within ±4 per code; 9.7±2 counties with no subreddit (mean over seeds; per-seed range 3–15); `abs(corr(z_log_staff_abs, z_log_staff_per_case)) < 0.55` (§5.3); every statute ≥ 20 implementers; every `task_type` in ≥ 40 counties; names collide with no real California county, no W1 name and no other synthetic county |
| `tests/test_generator_capacity.py` | **the sign tests** — this is the file that exists to stop the plan's error being coded: `speed_factor` is *decreasing* in `staff_abs` holding caseload fixed; *increasing* in caseload holding `staff_abs` fixed; and **not monotone in `staff_per_1k`** across the panel (a test that fails if someone "fixes" the model to make per-capita staffing predict speed). Plus: `R2_covariates_on_log_median` in [0.02, 0.15]; `abs(corr(ln pop, median_days)) <= 0.30`; `corr(rucc, median_days)` in [−0.40, 0.00]; fee p90/p10 ratio in [3.5, 6.0]; `hourly_rate` median in [150, 240]; **every §5.6 diagnostic inside its band, on both clocks** — in particular `abs(r)` of every covariate with the post-decision sub-clock ≤ 0.40 while the applicant-clock R² is ≥ 0.30, which is the test that the phase split works |
| `tests/test_generator_disclosure.py` | artifact count increases with size class (mega mean ≥ 18, tiny mean ≤ 6); φ(policy published, real processing time published) ≥ 0.45; ≥ 10 counties have both `official_stats` and ≥ 1 forum post; counties with no channel have exactly 0 `reddit_thread` specs and `timing_ceiling.n_posts_with_timing == 0`; every `vendor_boilerplate` spec has exactly one `wrong`-fidelity timing reveal and no other reveals |
| `tests/test_generator_discretion.py` | `discretion_spread=0` ⇒ one reading per predicate across all counties; `propensity=0, spread=1` ⇒ the marginal matches the planted weights (4,000 synthetic counties, χ² p > 0.01); recovered-from-truth strictness regresses on covariates with the planted signs; lineage clusters share readings at ≥ 0.70 within-cluster agreement against ≤ 0.45 between-cluster; `n_eff` per predicate is in [10, 30] and strictly below the implementer count; planted dispersion ordering minimal > mid > prescriptive with a ≥ 0.35-nat spread; after `CONCENTRATION`, a prescriptive statute puts ≥ 0.78 of counties on the modal reading and a minimal one ≤ 0.55; `cross` reports tail recall whenever `CONCENTRATION >= 1.6` |
| `tests/test_generator_outcomes.py` | register shares within ±0.03 of (approved 0.74, disapproved 0.005–0.02, withdrawn 0.010, pending 0.245); `dead_share_of_pending` in [0.35, 0.50]; every `withdrawn` case has either a withdrawal hazard draw or an `advised_withdrawal` predicate; the simultaneity confusion matrix matches (0.45 ministerial-zero, 0.29 discretionary-zero) to ±0.06; no case is both `denied` and `withdrawn`; pooled ministerial share in [0.95, 0.985] and the share of all-ministerial counties in [0.78, 0.94]; the within-office discretionary effect in [80, 140] days and the between-office correlation of route share with median days `abs(r) <= 0.30`; the share of counties reporting zero withdrawals in [0.32, 0.52] |
| `tests/test_generator_retrieval.py` | 13–31 counties with ≥ 40% and 7–24 with ≥ 60% of own-host documents blocked; blocking is within-county correlated (mean within-county variance < half the between-county variance); `information_ceiling >= reachable_ceiling` for every task; the state-agency dashboard is blocked in ≥ 70% of seeds; `js_shell` specs return status 200 with no process facts; off-host kinds are never blocked |
| `tests/test_generator_partitions.py` | partitions disjoint and exhaustive; sizes 14/29/15; each partition's mean of each of four covariates within 0.4 sd of the panel mean; each partition has ≥ 1 county per size class; every statute appears in all three; the render tier satisfies all five constraints of §11.3; no reserved county's files exist outside `worlds/W2/reserved/` |

Total ≈ 60 new assertions across 8 files. The suite is 409 tests today; W2 should
leave it green and add these.

### 12.4 World-validator additions

`benchmark/synth/schemas/validate.py:check_world`, all inside
`if world.get("world_model_version", 1) >= 2:`:

1. **Panel integrity**: `n_counties` records; ids match `M\d\d`/`N\d\d`; every
   county has all covariate fields and a `real_coverage` tag on each; every
   `cov` numeric field is finite and inside its declared clip range.
2. **Planted block**: `world.json.planted` exists, contains every coefficient
   the code read (compare against `capacity.PLANTED` keys — a missing key is an
   error, because it means a coefficient is in the code but not in the recorded
   truth), and `planted.diagnostics` passes every §5.6 target.
3. **Derived quantities are consistent with the planted form**: recompute
   `speed_factor`, `hourly_rate`, `publish_logit` and `strictness_propensity`
   from `world.json.planted` plus the county record, and check they reproduce
   the values used in the truth files to within 1e-9. This is the check that
   catches the worst possible failure — the recorded coefficients not being the
   ones the generator used — and it is cheap.
4. **Partitions**: disjoint, exhaustive, sized, stratified (§11.4), statutes
   shared.
5. **Reachability**: every spec has a `fetch` block; `fetch.blocked` implies a
   `mode` and a `body_if_blocked`; off-host kinds are unblocked;
   `ceiling.information_ceiling >= ceiling.reachable_ceiling` field by field;
   `unreachable_ids ⊆ artifacts_about_process`.
6. **User-evidence hurdle**: a county with `subreddit == None` has zero
   `reddit_thread` target specs and no spec whose `publisher` starts `r/` on its
   own behalf; a county with a channel and `post_volume == 0` likewise, and both
   cases have `timing_ceiling.n_posts_with_timing == 0`.
7. **Outcomes**: `summ["register_shares"]` sums to 1.0 ± 1e-6;
   `pending_mixture.dead + .live == .pending`; no record has
   `closure.recorded_as == "withdrawn"` with `outcome == "denied"`.
8. **Lineage**: every `lineage_from` resolves to a county that adopted earlier
   and implements the same statute; a lineage child's copied readings equal the
   parent's except where a re-draw is recorded; `n_eff <= n_implementers`.
9. **Role collapses**: every `role_collapses` entry names a role absent from
   `depts` and an activity that actually uses the collapsed-to role.
10. **Print by size class**: the existing summary block gains ceiling coverage,
    artifact counts, reachability gap and user-evidence counts **per size class
    and per partition**. The global mean is the number that hides the finding.

Also add the **missing `world.schema.json`**: there is no schema for
`world.json` today (the validator reads it unvalidated), which is how a
58-county record could ship with a silently missing covariate. Write one,
covering knobs, states, counties (with `cov` and `real_coverage`), statutes,
implementations, non-implementations, partitions and `planted`.

---

## 13. What `world.json` records

The scorer's contract. `build.py` writes, at version 2 only:

```json
"world_model_version": 2,
"counties": [ { "id": "M07", "name": "Ardmont", "kind": "county", "state": "Marisol",
                "size_class": "mid", "partition": "development",
                "render_tier": true, "region": "North Coast",
                "cov": { "pop": 186290, "log_pop_z": -0.01, "rucc": 3, ... },
                "cov_real_coverage": { "pop": "complete", "budget_per_capita": "blocked", ... },
                "derived": { "staff_abs": 9100, "staff_per_1k": 48.8, "wage": 71200,
                             "hourly_rate": 188, "speed_factor": {"S01": 1.12, ...},
                             "staff_per_case": {"S01": 0.31, ...},
                             "publish_u": 0.44, "post_volume_v": 0.12,
                             "strictness_propensity": -0.21,
                             "p_fetch_blocked": 0.45, "site_platform": "legacy_aspx" },
                "depts": {...}, "contracts_out": [...], "umbrella": "...", ... } ],
"partitions": {"calibration": ["M02", ...], "development": [...], "reserved": [...]},
"planted": {
  "speed":     {"B0": 0.0, "B_DEPTH": -0.22, "B_LOAD": -0.28, "B_DENSITY": 0.30,
                "B_EDU": 0.18, "B_PORTAL": -0.06, "B_RURAL": -0.04,
                "TAU_POLICY_COUNTY": 0.50, "TAU_POLICY_PROGRAM": 0.30,
                "DISCRETIONARY": 1.05,
                "covariate_phases": "phase < 7.0 only"},
  "cost":      {"WAGE_TO_HOURLY": 0.00269, "B_OVERHEAD": 0.10},
  "caseload":  {"PROGRAM_STAFF_SHARE": 0.004, "BASE_RATE": {...}, "ALLOC_SD": 0.35},
  "route":     {"predicate": "P4", "attribute_dist": ["lognormal", 1.0, 3.2],
                "reading_weights": [0.86, 0.11, 0.03],
                "pooled_ministerial_share": 0.970,
                "within_office_days": 104,
                "leak_ministerial_zero": 0.45, "leak_discretionary_zero": 0.29},
  "publish":   {"intercept": {"program_page": 0.847, ...}, "A_SIZE": 0.55,
                "A_LOAD": 0.20, "A_PORTAL": 0.45, "A_RURAL": -0.35,
                "A_BUDGET": 0.15, "SIGMA_U": 1.10},
  "user":      {"H0": {...}, "H_POP": {...}, "V0": {...}, "V_POP": 0.85,
                "V_CASELOAD": 0.30, "V_DELAY": 0.55, "SIGMA_V": 0.60, "RHO_UV": 0.30},
  "strictness":{"D_RURAL": -0.30, "D_STAFF": 0.25, "D_EDU": 0.30,
                "D_LINEAGE": 0.85, "SIGMA_S": 0.80,
                "SHAPE_SPREAD": {"minimal": 1.30, "mid": 1.00, "prescriptive": 0.55},
                "CONCENTRATION": {"minimal": 0.8, "mid": 1.6, "prescriptive": 4.0}},
  "lineage":   {"L_SMALL": 0.55, "clusters": {"S01": [[...], ...]},
                "n_eff": {"S01": {"P2": 16.3, ...}}},
  "outcomes":  {"W0": 0.0012, "Q0": 0.0110, "W_DELAY": 0.8, "Q_REWORK": 0.9,
                "Q_DELAY": 1.2, "p_fatal_becomes_withdrawal": 0.55,
                "p_fatal_becomes_quiet": 0.25, "target_disapproval": {...},
                "RW0": 0.35, "RW_SIZE": 0.55, "RW_PORTAL": 0.40, "SIGMA_U_W": 0.60},
  "retrieval": {"PLATFORM_BASE": {...}, "KIND_MULT": {...},
                "PUBLISHER_MULT": {...}, "MODE_SHARES": {...}},
  "fit":       {"F0": {...}, "F_POP": {...}, "F_RURAL": {...}, "F_UNINC": {...},
                "F_INCOME": {...}, "F_THRESHOLD": -2.2},
  "standardisation": {"LN_POP_MEAN": 12.0614, "LN_POP_SD": 1.838, ...},
  "overrides": {},
  "diagnostics": { "r_logpop_vs_median_days": 0.19, "R2_covariates_on_log_median": 0.05,
                   "share_variance_policy": 0.63, ... },
  "notes": [ "B_DEPTH and B_LOAD oppose along the size axis; net elasticity of duration
              on log population is approximately -0.01, matching APR corr 0.21 (R2 ~ 0.04).",
             "staff_per_case carries deliberate within-county allocation noise (sd 0.35)
              so that B_LOAD is identified separately from B_DEPTH (planted corr
              -0.46, against the real log-pop / log-staff corr of 0.991); reality
              is far more collinear than this.",
             "WAGE_TO_HOURLY = 0.00269 absorbs both benefit loading (2.2-2.6x) and the
              QCEW average-wage understatement of a licensed reviewer's salary (~2x).",
             "Covariate terms act on queue phases only (phase < 7.0); the
              post-decision sub-clock carries policy_c alone. This is what lets one
              coefficient set reproduce BOTH measured clocks (applicant-clock
              density +0.688, permit-record-clock max abs r 0.33).",
             "Coefficients are calibrated to the 95% intervals of a 30-county
              measurement, not to its point estimates, which are not jointly
              reproducible by a linear model with a substantial policy effect.",
             "D_* magnitudes are calibrated to the measured covariate association
              with the county ministerial share (best abs r 0.43 for ADU, 0.57 for
              single-family), on one program family only.",
             "Reading spaces are tempered by CONCENTRATION so a prescriptive statute
              gives a mass point plus a thin tail (89% all-modal), per the measured
              ADU distribution, not a broad spread.",
             "budget_per_capita, broadband_pct, pct_unincorporated, n_cities, portal,
              site_platform and consortium are drawn from ASSUMPTIONS; the real columns
              are empty (Census key / State Controller 403). See cov_real_coverage." ]
}
```

Two rules about this block:

1. **Every coefficient the code reads must appear here**, enforced by validator
   check §12.4.2. A coefficient in code but not in `planted` is a parameter the
   scorer cannot score against, which is the failure mode that turns SBC into
   theatre.
2. **Standardisation constants are part of the planted truth.** A recovered
   `gamma` is only comparable to a planted `gamma` if both are on the same
   scale, and the scale is `(LN_POP_MEAN, LN_POP_SD, ...)`. W1 has no analogue of
   this and it is the commonest way a recovery comparison silently fails.

---

## 14. Where the plan is wrong in light of the real data

The plan was written before [the covariate
analysis](scoping/2026-09-16-county-covariates.md), [the APR timing
analysis](scoping/2026-09-16-apr-permit-timing.md) and [the discretion
analysis](scoping/2026-09-16-apr-discretion-variation.md) landed. **Twelve
corrections**, ordered by how much damage following the plan literally would do.
The first three are sign errors that would invert a planted relationship; 14.10
is the one that would most change a published number.

### 14.1 §3.1 item 2 and §4.1: "speed as a function of staff per capita" — wrong sign

The plan says derive speed from **staff per capita**, and §4.1 puts staff per
capita in the model's covariate vector `x_c`. Staffing per capita correlates
**−0.73** with log population and **+0.69** with rurality: it is a measure of
*smallness*, not of capacity. Planting "more staff per capita ⇒ faster" plants
"the 1,141-person county is the best-resourced in the state", and a model that
recovers that coefficient recovers a generator artefact. **Correction**: log
absolute staff (depth) and staff per case (congestion), with opposing signs, per
§5.2. The covariate doc already says this; the plan has not been amended.

### 14.2 §4.1: the expectation that covariates predict speed is not supported

"`gamma_rural` is the estimated slowness attributable to rurality." Measured:
corr(rurality code, median ADU days) = **−0.27** — rural counties are slightly
*faster* — and no covariate exceeds |r| = 0.27, implying R² ≈ 0.04–0.07. The
covariate regression should still be fitted (it borrows strength for data-poor
counties, which is the plan's real argument) but **it must not be presented as
the mechanism for timing variation**, and W2 must not plant it as one. The plan's
own §6 "transfer accuracy: predict a held-out county's timing using only its
covariates" is therefore a much weaker criterion than it reads: with R² ≈ 0.05
the covariate-only prediction beats the grand mean by a few percent. **Correction**:
transfer accuracy must be scored against *two* baselines — the panel grand mean
and a same-statute mean — and reported **per clock**, because on the applicant
clock the covariates do far better than this section's numbers suggest (see
14.10, which supersedes the pessimistic reading). The route class is *not* a
useful transfer predictor between counties: its between-office correlation with
duration is −0.163.

### 14.3 §3.2: `beta_staff * staff_per_capita` in the disclosure logit — same sign trap

Plan §3.2's logit is
`beta0_kind + beta_pop*log(pop) + beta_staff*staff_per_capita + beta_portal*has_portal + beta_rural*rural_class + eps_county`.
With a positive `beta_staff`, the tiniest counties get the *largest* staffing
term and the model plants tiny counties publishing more, partly cancelling
`beta_pop` and destroying the disappearing-commons signal the section exists to
create. **Correction**: `A_SIZE * z_log_staff_abs` (§7.1). Note also that
`log(pop)` and `log(staff_abs)` are collinear at r = 0.991, so the plan's logit
cannot identify `beta_pop` and `beta_staff` separately even with the right sign —
one size term, not two.

### 14.4 The covariate doc's "record all three" is not identifiable as stated

[Covariates §2](scoping/2026-09-16-county-covariates.md) concludes: "The right
regressors are log absolute staff, staff per case, and the average wage. Record
all three in W2 as planted coefficients so recovery can be scored." Measured
here: **corr(ln pop, ln staff_abs) = 0.991**, and wage's correlation with size is
0.65. So of those three, only two directions are estimable from 58 counties
(size, and the staff-per-case residual), and wage adds a third only weakly.
**Correction**: W2 plants three coefficients but must (a) build deliberate
within-county variation into staff per case so `B_LOAD` is identified (§5.3),
(b) never put log population and log absolute staff in the same planted
regression, and (c) record in `planted.notes` that the real panel is more
collinear than the synthetic one, so a recovery success on W2 is *necessary but
not sufficient* for a recovery success on California.

### 14.5 §4.1's covariate vector names columns that do not exist yet

Plan §4.1 sets `x_c` = (log population, staff per capita, budget per capita,
rurality class, portal, consortium). Of those, **budget per capita, portal and
consortium are 0-of-58 complete** in
`corpus/counties/ca_counties_covariates.csv`, along with unincorporated share,
city counts, broadband, subreddit subscribers, vote share, county FTE and EH
structure — 13 empty columns. The blockers are a Census API key and the State
Controller's 403. **Correction**: (a) W2 tags every covariate with
`real_coverage` and the Bayesian layer's **default** covariate set must be
restricted to the 26 complete columns, with the blocked ones behind an explicit
opt-in; (b) P8-COVARIATE-GAPS is a hard dependency for the plan's §4.1 as
written, not a nice-to-have, and should be re-ranked above the remaining scoping
packets; (c) unincorporated share is the highest-value missing column, because
the county only has jurisdiction outside cities and it gates `F_UNINC` for the
two flagship programs.

### 14.6 §3.5's spec-count estimate is out by 3–4×

"250 processes produce roughly 2,500–3,500 specs rather than a flat 8,000." The
arithmetic in §11.5 gives ≈ 11,400 at the unchanged `distractor_ratio = 4.0` and
≈ 5,700 at 2.0. Capacity-dependent disclosure reduces *target* artifacts by
about 10%; it does not touch the distractor multiplier, which is what dominates.
**Correction**: set `distractor_ratio = 2.0` for W2, declare the benchmark
difference, and do not compare W2 retrieval numbers to W1's.

### 14.7 §3.3's "are rural counties stricter" now has a measured answer, and it is "no"

The plan says making strictness covariate-dependent means "'are rural counties
stricter' has a known answer", meaning known *because we planted it*. Since the
plan was written the question has been answered on real data:
[discretion §4](scoping/2026-09-16-apr-discretion-variation.md) correlates the
county ministerial share — an observed reading of a statute — with the covariate
table and finds rurality at **+0.395** against the ministerial share for
single-family housing, i.e. **more rural counties are more likely to call housing
ministerial: more lenient, not stricter**, with poverty +0.350 and education
−0.564 pointing the same way. Best |r| is 0.43 for ADU and 0.57 for
single-family, so covariates explain 18–33% of the reading.

**Correction**: `D_RURAL` stays *negative* but is now a calibration rather than a
judgement, `D_EDU` replaces `D_INCOME` (education is the stronger predictor for
ADU and the two correlate at 0.840), and the planted covariate share of
strictness variance (0.22) is inside the measured 0.18–0.33. The paper may now
state the direction as an empirical finding about *housing entitlement* readings
in California, with the caveat that it is one program family measured on 30–42
counties — and that the synthetic recovery result is evidence about the
estimator, not additional evidence about counties.

### 14.8 The denial-rate framing, already partly corrected in the plan's §9.5

The plan's body derives outcomes from predicate failure and treats denial as the
outcome of interest; the APR finding (89 disapprovals against 194,347 approvals)
makes denial rate the wrong outcome and the **pending backlog (21.8%) and
withdrawal** the informative ones. The plan's §9.5 records this but §3 was not
updated. **Correction**: §9 of this spec, and specifically the point the APR doc
does not make — that the 21.8% pending is a **mixture** of live and dead cases
that no administrative dataset separates, so W2 should plant the mixture with
known proportions and add "estimate the dead share of the backlog" as a metric.

### 14.9 Two smaller factual notes

- The covariate doc says "density spans 1.5 to 2,380 per square mile". The
  table's maximum is **17,323** (San Francisco, a consolidated city-county);
  2,380 is Los Angeles. Four orders of magnitude, not three. W2's land-area draw
  (independent of population, `exp(N(7.46, 0.971))` clipped to `[45, 20100]`)
  reproduces the real range including one very small, very dense county —
  deliberately, because a consolidated city-county is a real institutional form
  and its process is a city's, not a county's. Give it
  `pct_unincorporated = 4` and let §6.1's `F_UNINC` term do the rest.
- The plan's §3.1 item 1 lists "code host" in the county record but §4.1's model
  vector omits it while including "consortium". Both are systems covariates with
  the same role (shared platform ⇒ shared channel structure and timing, per §5's
  "shared by cluster" tier). W2 carries `portal_vendor`, `site_platform`,
  `code_host` and `consortium`, and the model should pool on **platform**, which
  is the one with a measured consequence (fetch-blocking).

### 14.10 The covariate-timing relationship depends on the clock, and the plan picks no clock

The largest correction, and the one that changes a number the project would
otherwise publish. The plan's §4.1 says `mu_i = m + alpha_agency + ...` without
specifying which duration `mu_i` is. Measured
([discretion §4, reconciliation](scoping/2026-09-16-apr-discretion-variation.md)):
the same covariates against the same counties reach **max |r| = 0.33** on the
entitlement→permit span and **max |r| = 0.69** on the application→permit clock —
density +0.334 → +0.688, education +0.308 → +0.583. The earlier APR report's
"covariates barely predict timing (r ≈ 0.2)" is true of the permit-record clock
and false of the applicant clock, and the report's own builder reproduces both to
three decimals, so this is not a disputed measurement.

**Consequences, all of them load-bearing:**

1. The plan's §4.1 `gamma` is **identifiable on the applicant clock and nearly
   unidentifiable on the permit-record clock**. "Fitted against the wrong clock
   it recovers `gamma` near zero and looks useless." Every fit must declare its
   clock in the results document, which the existing `measurement_clock`
   machinery already supports and which no §4 text currently requires.
2. This spec's own §5 premise, written before the discretion report, was
   calibrated to R² ≈ 0.04. That is wrong for the clock W2 actually simulates
   (`elapsed_days` is an applicant clock), and §5.2 is now calibrated to
   R² ≈ 0.48 on the applicant clock with a near-covariate-free post-decision
   sub-clock. An implementer working from an earlier draft of this document would
   have planted a world in which the plan's flagship transfer metric could not
   work.
3. The mechanism is where the plan's value actually lies: the covariate-
   predictable time is **intake, completeness review and resubmission** — the
   part permit records cannot see (70 days) and the applicant lives (156 days),
   and the part forum posts describe best. That is an argument for the mixed
   evidence ledger, not merely for a covariate regression.
4. The best single real predictor is **population density**, not population,
   staffing or rurality — none of which the plan lists as a covariate of
   interest, and density is in the covariate table already. Add it to `x_c`
   explicitly, and note that it is 0.88 correlated with log population so only
   the compactness residual is separately identified.

### 14.11 §3.3's "discretion dispersion" should be a mass point, not a spread

The plan asks for wide cross-county dispersion of readings and makes recovered
dispersion the headline cross-county result. Measured for the flagship program:
**89.1%** of jurisdiction-years are within 0.05 of all-ministerial, the pooled
share is **0.974**, and the residual disagreement — though real at **45×**
binomial noise — is concentrated in five standing dissenters and 38 conditional
jurisdictions out of 291, with the top 10 holding 71% of it. **Correction**:
§8.3's `CONCENTRATION` transform, plus a metric change — on a concentrated
statute, entropy recovery is satisfiable by predicting the mode for all 58
counties, so `decision_metrics.cross` must report **tail recall** (did the model
find the dissenters?) as the headline instead. The plan's expected result
("recovered dispersion tracks planted dispersion") survives only across statutes
of *different* concentration, which is why the W2 statute set must span shapes.

### 14.12 The withdrawal channel needs a reporting model, not only a behaviour model

Both the plan and this spec's first draft treated withdrawal as a behaviour to
simulate. **82 of 193 real ADU jurisdictions (42%) report exactly zero
withdrawals**, and only 24 report any disapproval, so the field is not missing at
random — it is a disclosure decision of the same form as the plan's §4.2
`pi(kind, c)`. **Correction**: §9.4's `reports_withdrawals` propensity, sharing
the county disclosure effect `u_c`, so that "pending" is a three-component
mixture (live, dead-and-quiet, withdrawn-but-unreported) with planted
proportions. Without this the withdrawal field cannot calibrate anything, and a
model fitted to the raw register will read a reporting gap as a behavioural
difference between counties.

---

## 15. Build order and acceptance

Nine steps, each independently testable. Do not start step *n+1* with step *n*'s
tests red.

| # | step | files | acceptance |
|---:|---|---|---|
| 1 | capture the version-1 baselines | `tests/test_generator_county_world.py` | both hashes pinned; suite green |
| 2 | the county panel | `counties.py`, `world.py` (branch only) | `test_generator_county_panel.py` green; a version-2 world builds with W1's global knobs and validates |
| 3 | naming, departments, hosts, fee instruments | `counties.py`, `world.actor_name`, `specs._url_for` | no name collisions; `subreddit: None` handled at every call site |
| 4 | the six hard-coded tables become functions | `capacity.py`, `processes.py`, `local_rules.py`, `specs.py` | `test_generator_capacity.py` green, **including the three sign tests**; version-1 hashes unchanged |
| 5 | load assignment and the statute set | `world.py` | ≈ 261 target processes; every statute ≥ 20 implementers; crossed-design assertions |
| 6 | capacity-dependent disclosure and the user hurdle | `visibility.py`, `specs.py`, `capacity.py`, four new kinds | `test_generator_disclosure.py` green; ceiling coverage by size class printed |
| 7 | strictness, reading lineage, statute shapes | `decision.py`, `lineage.py`, `local_rules.py`, `decision_metrics.py` | `test_generator_discretion.py` green; `n_eff` recorded and used by `cross` |
| 8 | outcomes and fetch-blocking | `simulate.py`, `ceiling.py`, `specs.py`, `web.py`, `score.py` | `test_generator_outcomes.py` and `test_generator_retrieval.py` green; five-way error decomposition |
| 9 | partitions, render manifest, `world.json.planted`, validator, docs | `build.py`, `counties.py`, `validate.py`, `world.schema.json`, `DESIGN.md`, `RENDER_BRIEF.md`, `VERIFY_BRIEF.md`, `generator/README.md` | `test_generator_partitions.py` green; full W2 builds and validates with 0 errors; every §5.6 diagnostic inside its target |

**Definition of done for W2 itself** (not for the code):

```
python3 -m benchmark.synth.generator.build --world W2 --seed 2 \
    --knob world_model_version=2 --knob statute_set=w2_core \
    --knob distractor_ratio=2.0 --knob filler_cap=2500 \
    --out benchmark/synth/worlds/W2
python3 benchmark/synth/schemas/validate.py --world benchmark/synth/worlds/W2
```

with: 58 + 8 jurisdictions; 6 + 6 statutes; **≈ 261** target and ≈ 24
look-alike processes; ≈ 15,000 log records; ≈ 5,700 specs; 0 validator errors; every
diagnostic in §5.6 inside its target band; and the printed summary showing
ceiling coverage, artifact count, reachability gap and user-evidence volume
**by size class and by partition**, with the largest-to-smallest decile gap in
recall reported as the headline fairness number.

Then, and only then, stage 4 of the plan (calibrate on the 14 calibration
counties) and stage 5 (fit V6 with the covariate layer on the 29 development
counties). The 15 reserved counties stay shut.
