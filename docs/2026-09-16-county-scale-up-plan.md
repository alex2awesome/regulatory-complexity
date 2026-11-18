# Scaling to 58 counties: the plan

2026-09-16. Consolidates ten scoping workstreams, the decision-layer work that
already landed in the generator, the synthetic scale-up, and the Bayesian model
changes that the scale-up is for. Written because nine of the ten scoping agents
died on a session rate limit (resets 9:50pm Pacific) before writing their
reports; this document holds their briefs so nothing is lost, and sequences the
work.

The research question this serves, from Alex and from Dan Ho's feedback: **the
decision model is measurable through process variation, without anyone's coded
segments.** One statute, 58 county implementations, is 58 draws from the
posterior over the decision function the statute underdetermines. Cross-county
disagreement at the discretionary predicates *is* the discretion residual. The
process-reconstruction pipeline is the instrument. Scale is not a nice-to-have
here: with two programs the hierarchy has nothing to pool and 66% of its latent
coordinates sit at their priors ([audit §3](2026-09-16-bayesian-overnight-audit.md)).
58 counties is the regime in which agency effects, measurement parameters, and
discretion dispersion all become estimable.

---

## 1. What already landed today

### 1.1 The decision layer in the generator (done, tested)

`benchmark/synth/generator/decision.py` (about 700 lines) plants the chain
statute → decision function → jurisdiction readings → process → simulated
outcomes → artifacts, behind a `decision_model_version` knob (default 2; 1
reproduces the old generator byte-for-byte).

- **Four predicate kinds.** `crisp` (the statute fixes the test exactly;
  look-alike statutes in the neighbour state carry a different constant, and
  `p_misimplement` lets a county restate it wrongly), `standard` (the statute
  uses a standard word and states no number, so each county draws a reading from
  an ordered lenient-to-strict space with planted weights, spread by
  `discretion_spread`), `delegated` (an existing `open_choices` entry, so the
  reading follows the ordinance the county already adopted), `local` (a testable
  `stricter_standards` entry becomes an added predicate `Q*`).
- **36 predicates across the 12 domains**, each with a case-fact distribution, a
  question, a unit, a fixable-versus-fatal flag, and 2–3 candidate readings.
- **Attachment**: every predicate binds to the activity that evaluates it,
  including back-office steps (a zoning check, a licence verification), so a
  reading evaluated at a staff-only step is disclosed only by staff documents.
  `activity.evaluates` and `activity.inputs_required` are new truth fields.
- **Outcomes are now derived.** The simulator samples case facts once per
  applicant, evaluates each predicate at its checkpoint, sends fixable failures
  round the rework loop (cured with `p_cure`), and denies on a fatal failure or
  an unresolved fixable one. `denial_rate` stopped being a free parameter and
  became `expected_fatal_fail_rate`. Each log record carries
  `case_attributes`, `predicate_results` and `decision_basis`; each summary
  carries a `predicate_summary` with first-pass and eventual pass rates.
  Verified: a strict reading fails 30+ points more often, corrects more, and
  denies more than a lenient one on identical case facts.
- **Disclosure of readings** follows the same visibility model as everything
  else: a new `criterion` reveal field, per-kind rules (a checklist states the
  inspection criterion exactly, an ordinance states delegated and local
  criteria but only names the standard, a third-party guide gets it wrong with
  probability `p_wrong_fact_third_party`, a news item is vague), a
  `must_not_reveal_criteria` list, contamination that carries *another county's
  reading of the same standard*, and reddit posters who describe the criterion
  they personally failed on.
- **A decision ceiling** per task, partitioning the predicates into
  exact/approximate/only-wrong/hidden with per-kind coverage, so reading
  recovery is scored against what the documents actually permit.
- **Task prompts** now also ask for the criteria as the jurisdiction applies
  them, and `tasks.json` gold gains a `decision_model` pointer.

Guards: schemas, the world validator (predicates attach to real activities,
readings are well-formed, corrections point backwards, decision buckets
partition, criterion leaks are errors), the render and verify briefs, and
`tests/test_generator_decision_model.py` (8 tests). Full suite 409 passing; the
tiny world validates with 0 errors; W1 replays byte-identical under version 1
and the 600-case legacy verification still passes.

### 1.2 A scorer for reading recovery (done)

`pipeline/procbench/decision_metrics.py`:

- **`score`** matches predicted criteria to planted predicates (attribute
  equality first, then the activity aligner's token F1), then reports criterion
  recall and precision, `reading_exact` (operator and value within 5%),
  `reading_direction`, whether the right step was named, hallucinated criteria,
  per-kind breakdown, and ceiling-relative recall with an availability gap.
- **`cross`** takes many counties of one statute and reports, per predicate, the
  planted versus recovered number of distinct readings, the planted versus
  recovered entropy, the entropy ratio, and per-county agreement. This is the
  discretion-recovery measurement.

Self-tested: a perfect prediction scores 1.0 on everything; a prediction that
drops attributes, perturbs half the thresholds and adds one invented criterion
scores recall 1.0, precision 0.75, `reading_exact` 0.67, direction 1.0. Cross:
perfect recovers entropy ratio 1.0, the perturbed version collapses agreement to
0.0 on the predicate whose values it moved.

### 1.3 One scoping result (preserved)

[CCW in 15 small and mid-size counties](scoping/2026-09-16-ccw-15-small-counties-findings.md):
fees varying 4.6-fold ($118 Siskiyou to $549 Lake), 13 of 15 on the same vendor
portal and 2 paper-only, one county that trains its own applicants, four
published policies out of fifteen, four real processing-time statements against
eleven instances of vendor boilerplate, per-county counts buried in sheriff
annual reports rather than any central dataset, and six of fifteen county sites
blocking a scripted fetch outright. Design implications are in that file's §"What
this already settles"; the most important are that **disclosure of timing
correlates with disclosure of process** (so the generator should not draw them
independently), that **rural counties are information-different rather than
information-free**, and that **403/Cloudflare walls are an unmodelled retrieval
failure mode**.

---

## 2. Real-world scoping: the ten workstreams

Each is stated as the question, the sources to hit, the deliverable, and the
effort. Status: **A2 partly done** (15 of 58 counties), everything else pending.
All were written as agent briefs; the briefs are reproduced in enough detail
here to relaunch without re-deriving them.

### A1. CalFresh across 58 county welfare departments
**Question.** Welf. & Inst. Code §18900 et seq., MPP Division 63, 7 CFR 273,
supervised by CDSS and administered by 58 counties. Which parts of the applicant
process are state-uniform (form CF 285, BenefitsCal/CalSAWS since 2023) and
which are county policy (intake channel, interview scheduling from same-day to
call-centre, verification practice, expedited three-day service, semi-annual
reporting, recertification, office structure and consortium legacy)?
**Sources.** County policy handbooks that are public (LA DPSS, SF HSA,
Sacramento DHA, Santa Clara SSA). CDSS CalFresh Data Dashboard and monthly
caseload (CF 256). **Application Processing Timeliness (CF 296 / APT): percent
of applications processed within 30 days and expedited within 3 days, by
county** — this is the single most valuable dataset in the entire scoping
exercise, because it is per-county, per-month, official processing *timing*.
Also churn, PRI, California Food Policy Advocates' Program Access Index, State
Auditor reports on county CalFresh administration, CDSS County Expense Claim and
CWDA data for staffing, Code for America's GetCalFresh county metrics.
**Deliverable.** `docs/scoping/2026-09-16-calfresh-58-counties.md` with a
per-county table (page, handbook, notable process detail) for at least 25
counties spanning size classes, the dataset inventory with years and
granularity, and a gold-process sketch for a large, a mid and a tiny county.
**Effort.** One agent, heavy web use, ~200 fetches.
**Risk to check.** BenefitsCal may have flattened the variation that existed
under the four legacy consortia; if so, say so, because a program whose process
became uniform is a negative result worth knowing.

### A2. CCW across 58 sheriffs — **15 counties done**
**Question and sources.** As in the completed file. Remaining: the 43 other
counties, the large ones especially (LA, San Diego, Orange, Riverside, San
Bernardino, Santa Clara, Alameda, Sacramento, Fresno, Kern, Contra Costa,
Ventura, San Joaquin, San Mateo, Stanislaus, Sonoma, Tulare, Santa Barbara,
Solano, Monterey, Placer, San Luis Obispo, Merced, Santa Cruz, Marin, Butte,
Yolo, El Dorado, Imperial, Del Norte, Glenn, Colusa, Plumas, Inyo, Mono,
Mariposa, Amador, Lassen, Trinity, Modoc, Sierra, Alpine, plus the city chiefs
that issue). Also: DOJ OpenJustice CCW statistics by county and year, the DOJ
annual CCW report, sheriff dashboards (Orange and San Diego publish some), and
**CRPA/FPC litigation dockets and declarations**, which contain internal sheriff
procedure and timeline evidence that is otherwise unpublished — a designed-tier
source with no analogue in the current corpus.
**Deliverable.** Extend the existing file to all 58, plus the dataset inventory
and three gold sketches (a large permissive, a large historically restrictive,
a tiny rural).
**Effort.** Three agents by size class, ~150 fetches each. Note the 403 walls.

### A3. ADU permitting across 58 counties and ~482 cities
**Question.** Gov. Code §66310–66342 (the 2024 recodification of §65852.2), the
§66311.7 amnesty (AB 2533), SB 1211 and AB 976. Build on the existing
`corpus/ab2533/` (Hayward, El Cerrito, Lafayette, San Mateo County) rather than
duplicating it. Dimensions: planning clearance versus building permit only,
over-the-counter versus plan check, checklist contents, impact fees and the
750-sq-ft rule, utility and fire referrals, the 60-day ministerial clock
(§66317) and compliance, pre-approved plan programs (AB 1332), and the §17920.3
amnesty checklists.
**Sources.** **HCD Annual Progress Report data** (ADU permits applied, approved,
issued per jurisdiction per year — per-jurisdiction outcome data, statewide,
downloadable). **HCD ordinance-review findings letters**, which are
oversight-body assessments of local process defects: designed-tier evidence
with no equivalent elsewhere. Terner Center and Casita Coalition reports, civil
grand jury reports on permitting.
**Deliverable.** `docs/scoping/2026-09-16-adu-58-counties-and-cities.md`: the
58-county unincorporated-process table (page, ordinance, checklist,
pre-approved plans, amnesty page, stated processing time), the dataset
inventory, three gold sketches, and a recommendation on whether ADU should be
the flagship case and which subset to start with.
**Effort.** One lead agent plus four parallel table-fillers by region.
**Why it may be the flagship.** It is the only candidate where we already have
a gold corpus, a statewide per-jurisdiction outcome dataset, and an oversight
body publishing process critiques.

### A4. General Assistance across 58 counties
**Question.** Welf. & Inst. Code §17000–17030.1. Every county must relieve and
support its indigent residents; each designs its own program. This is the
maximal-discretion case: same one-line mandate, 58 locally invented programs,
with grant amounts, time limits, work requirements, SSI advocacy requirements
and loan-versus-grant status all local. Landmark cases (Boehm v. Superior
Court, Hunt, Bell) set floors, so litigated counties differ from unlitigated
ones in a traceable way.
**Sources.** County code chapters (Municode and equivalents), LA DPSS GR
handbook, SF CAAP, CDSS General Relief monthly caseload reports, Western Center
on Law & Poverty, legal-aid guides (LSNC, BayLegal, LAFLA).
**Deliverable.** `docs/scoping/2026-09-16-general-assistance-58-counties.md`:
per-county table (program name, grant, eligibility, time limit, process steps,
document URL) for 30+ counties, and an explicit verdict on whether this is the
best test of the rural-data-poverty question.
**Expected shape.** Variation very high, official timing data poor, user data
thin and urban-skewed. That combination is itself the finding: the program with
the most discretion has the least evidence.

### A5. County environmental health: septic, wells, retail food
**Question.** Three programs every county runs, with strong rural relevance.
(a) Onsite wastewater (septic) under the State Water Board OWTS Policy: each
county adopts a **Local Agency Management Program (LAMP)** approved by its
regional board, so there are 58 documents that each describe one county's
implementation of one state policy, and counties file **annual LAMP reports
with permit counts**. (b) Water wells under Water Code §13750 and DWR Bulletin
74, with county well ordinances often stricter — this maps directly onto the
synthetic `well_permit` domain. (c) Retail food under the California Retail Food
Code, where the placarding and grading systems differ county by county (LA
letter grades, SF scores, Sacramento placards).
**Sources.** The State Water Board's approved-LAMP list, DWR's well-completion
report database, county EH fee schedules and plan-check pages, county inspection
databases.
**Deliverable.** `docs/scoping/2026-09-16-county-environmental-health-58.md`
with a 58-row table per program and a verdict on which best tests the rural
question.
**Why it matters.** Regional boards publish LAMP approval tables that describe
each agency's own implementation of one state policy, which is designed-tier
evidence at scale.
**Correction, 2026-09-16, from packet P5 and verified independently:** an
earlier draft of this plan asserted that regulation guarantees a LAMP for all 58
counties. That is wrong. **Tier 1 is the default route used *without* an
approved LAMP, and Tier 2 is the optional alternative that requires one.** The
Central Valley board's own table lists Lake County as "pending currently Tier 1",
and lists cities (Fresno, Clovis, Visalia) under Tier 1 separately from their
counties, so a city approval is not a county approval. What *is* universal is
annual reporting by every agency issuing OWTS permits; approved-LAMP agencies
carry extra reporting duties. The inventory is therefore a mix of Tier 1 and
Tier 2 agencies, which is more interesting than a uniform set: **the tier choice
is itself a jurisdiction-level decision of exactly the kind this project
measures.** And the rural hypothesis may *invert* here: septic and well
activity is concentrated in rural counties, so rural user-evidence may exceed
urban.

### A6. Sweep of every other 58-county process
**Question.** Make sure nothing is missed, then rank. Candidates to assess, each
with basis, department, variation, per-county outcome data, user data, and
designed-tier documents: **Medi-Cal eligibility** (county offices, 45-day
standard, DHCS county performance dashboards — a strong candidate),
**CalWORKs**, **IHSS** enrollment, **property tax assessment appeals** (R&T
§1603, 58 appeals boards, two-year clock, per-county rules of procedure, BOE
oversight), Prop 19 claims, Williamson Act, **county recorder and vital
records**, **registrar of voters** (58 registrars, Elections Code, rich SOS
data), **child support** (LCSAs with excellent federal per-agency performance
data), TB clearance, body art, pool permits, tobacco retail licences, **LPS
conservatorship and public guardian**, veterans service offices, **agricultural
commissioner restricted-materials permits** (58 CACs under DPR, with published
per-county permit and inspection data), animal licensing, encroachment permits,
unincorporated building and grading permits, cannabis licensing,
transient-occupancy-tax registration, tax payment plans and excess-proceeds
claims.
**Deliverable.** `docs/scoping/2026-09-16-other-58-county-statutes-sweep.md`
with a 1–5 score per candidate on variation, official timing data, user data,
gold feasibility and rural coverage, then a **ranked shortlist of eight across
all candidates including A1–A5**, and a recommendation of the 3–4 program
combination that best supports (i) cross-county decision-model variation, (ii)
the rural-data question, (iii) county-covariate modelling.
**Effort.** One agent, broad and shallow, then a second pass on the top three.

### A7. The 58-county covariate table
**Question.** What county attributes plausibly drive process variation, and
where are they published?
**Columns.** Identity (name, FIPS, seat, region, number of incorporated
cities); scale (population from DOF E-1, land area, density); **rurality**
(USDA Rural-Urban Continuum Code 2023, OMB metro/micro/noncore, RCRC
membership, share of population unincorporated); socioeconomic (median
household income, poverty rate, limited-English households, **broadband
subscription rate**, median age); **government capacity** (total county
employees and wages from the State Controller's Government Compensation in
California, general fund appropriations from the Counties Financial
Transactions Report, general fund per capita, department-level staffing where
available); systems (CalSAWS consortium history, single-office social services,
online permit portal vendor, website platform, code host); **user-data
availability** (county subreddit and subscriber count); politics (2024
presidential vote share as a proxy for sheriff and board stance); health
department structure.
**Deliverable.** `corpus/counties/ca_counties_covariates.csv` (58 rows),
`corpus/counties/README.md` documenting every column with source URL, year and
caveats, and a distribution summary with the modelling implications.
**Method.** Start from authoritative single tables and merge with python; only
subreddit and portal require per-county lookup. Never invent a value; leave
blank and record coverage honestly.
**Why this is the keystone.** Without it, nothing in §5 can be estimated.
Do this one first.
**Status: DONE**, 26 of 40 columns for all 58 counties. See
[the covariate analysis](scoping/2026-09-16-county-covariates.md). Three results
change the design: population is bimodal by a factor of 8,470; **staffing per
capita runs inverse to county size** (r = -0.73 with log population), so
per-capita staffing is the wrong speed regressor and W2 must plant the inverse
relationship rather than a naive one; and forum availability scales with
population (r = 0.74), with nine counties having no subreddit at all, so the
availability model needs a hurdle for channel existence before volume. Blocked
columns: the Census API now needs a key, and the State Controller returns 403
to scripts (the same wall as six county sheriff sites).

### A8. Reddit coverage per county and program
**Question.** Quantify the rural-data hypothesis. How many user timing reports
exist per county per program?
**Method.** `pipeline/recon/reddit_fetch.py` (Arctic Shift; keyword search needs
a subreddit, so query county subs directly and statewide subs with the county
name). Programs: CalFresh, CCW, ADU, septic/well, General Assistance, Medi-Cal,
building permits, 2–3 phrasings each. Window: three years. Flag posts containing
timing words. Record cap hits. Save raw JSON so nothing is refetched.
**Deliverable.** `corpus/counties/reddit_coverage.csv`, a README, and
`docs/scoping/2026-09-16-reddit-coverage-by-county.md` with posts per county,
posts per 100k population, share with timing words, the counties with zero
evidence per program, and the ratio of the top five counties' volume to the
bottom thirty.
**Budget.** 1,033 unique queries; the archive API runs 5–21 s per query, so
about 2.6 hours. **Status: RUNNING** (`pipeline/recon/county_coverage.py`,
detached, results cached per query under `corpus/counties/reddit_raw/` so a
restart never refetches; `analyse` rebuilds the csv and summary from the cache
with no network).

### A9. Forums beyond reddit (never launched; hit the concurrency cap)
**Question.** Alex's note: reddit is one forum among many; cast wide.
**Families to assess.** Special-interest forums (**CalGuns.net county CCW
timeline threads**, BiggerPockets for ADU, Houzz, Permies, Contractor Talk,
septic and well-drilling forums, restaurant-owner forums, **City-Data county
subforums**); **legal Q&A** (Avvo tagged by county, JustAnswer, Nolo, LawGuru);
**reviews of government offices** (**Yelp and Google Maps reviews of county
offices**, which contain wait times and step sequences and exist for rural
offices); **staff-side** (**Glassdoor and Indeed reviews by county eligibility
workers, permit techs and EH specialists**, which is staff-only process evidence
of a kind the corpus currently lacks entirely); social (Facebook public groups,
YouTube and TikTok permit vlogs with timeline-bearing comments, Quora);
**civic records carrying citizen accounts** (**civil grand jury reports**, which
every county publishes annually and which frequently address permit and benefit
backlogs — the best candidate for rural coverage; Board of Supervisors public
comment on Legistar/Granicus; MuckRock threads; local news letters); and
aggregators (311 data, county satisfaction surveys in budget documents).
**Deliverable.** `docs/scoping/2026-09-16-forums-beyond-reddit.md` and
`corpus/counties/forum_sources.csv` with per-source program coverage, access
method, volume, urban/rural skew and example URLs; with **concrete spot checks**
(Avvo "ADU" plus Sacramento versus Trinity; Yelp reviews of LA DPSS versus
Modoc social services; CalGuns posts in the San Bernardino versus Alpine
thread).
**Why it matters most for the fairness claim.** If grand jury reports and Google
reviews cover rural counties where reddit does not, the disappearing-commons
story becomes "the commons moves" rather than "the commons vanishes", which is a
different and better paper.

### A10. Deferred: SNAP across 50 states
Parked by Alex for v2. Same shape one level up: one federal statute, 50 state
implementations, with FNS per-state timeliness data. Revisit once the 58-county
machinery works.

---

## 3. Synthetic environment: the W2 specification

W1 is 6 jurisdictions, 12 statutes, 38 processes, 571 activities, 1,315 artifact
specs, 5,800 simulated applicants. It was built for a different question
(availability and retrieval within one jurisdiction) and it cannot answer the
cross-county one: with 4 target jurisdictions there are at most 4 readings per
predicate, and most statutes have 2–3 implementers.

**W2 target: depth over breadth.** 58 counties in one state, **4 to 6 statutes**
rather than 12, each implemented by 40–58 counties, giving roughly **250–300
target processes**. Plus a neighbour state of 8 look-alike counties for
distractors.

### 3.1 Generalise the jurisdiction layer
Currently `world.py` hard-codes six hand-written jurisdictions and several
modules key off their ids (`SPEED` in `processes.py`, `HOURLY` in
`local_rules.py`, `TARGET_LOAD`, `NEIGHBOR_LOAD`, a literal `JUR_BY_ID["J1"]`
in `specs.py`). Work:
1. **Generate jurisdictions from covariates** rather than listing them. A county
   record becomes: covariate vector (population, rurality class, staff per
   capita, budget per capita, unincorporated share, portal yes/no, code host,
   broadband, subreddit-exists) plus derived naming (departments, umbrella,
   hosts, fee instrument, council). Seed the covariate distributions from
   `ca_counties_covariates.csv` (A7) so the synthetic county size distribution
   matches California's real bimodal one, without copying county names.
2. **Derive `SPEED` and `HOURLY` from covariates** instead of a lookup table:
   speed as a function of staff per capita and caseload, hourly rate as a
   function of wage level. This is the substantive change — it makes the
   covariate-to-timing relationship a planted ground truth with a known
   coefficient, which §5 can then try to recover.
3. **Load assignment by covariate fit**: `_fit` already multiplies a kind-fit by
   a per-jurisdiction preference; extend it so implementation probability is a
   function of covariates (population thresholds in the statute's applicability,
   rurality for well and septic programs, visitor economy for short-term
   rentals). Non-implementation becomes informative rather than filler.

### 3.2 Make disclosure a function of county capacity
This is the disappearing commons, planted. Today the publication knobs are
global constants (`p_publish_program_page` 0.7 and so on). Change them to
per-county functions:

```
logit p_publish(kind, county) = β0_kind + β_pop·log(pop) + β_staff·staff_per_capita
                              + β_portal·has_portal + β_rural·rural_class + ε_county
```

with the coefficients planted and recorded in `world.json`. Consequences, all
desirable: a large county produces 20+ artifacts and a tiny one produces 3; the
information ceiling becomes a **county-varying** quantity; and the CCW finding
that *timing disclosure correlates with process disclosure* is reproduced by
giving the kinds a shared county random effect rather than independent draws.
Add the same treatment to user evidence: expected reddit posts per process scale
with population and with whether the county has a subreddit at all, so some
counties have zero user evidence by construction.

### 3.3 Discretion dispersion at 58 draws
`decision.py` already draws each county's reading of a standard from a weighted
space via `discretion_spread`. At 58 counties this becomes measurable, so:
1. **Make strictness covariate-dependent**: `strictness_c ~ ordered logit(δ'x_c
   + ε_c)`, so rurality or budget can predict strictness, with the coefficient
   planted. Then "are rural counties stricter" has a known answer.
2. **Add template lineage to readings.** `local_rules.py` already copies choices
   from an earlier adopter with probability `p_template_lineage`. Extend it to
   readings, so clusters of counties share a reading because they copied one
   another. This plants *spatial correlation in the discretion residual*, which
   is both realistic (ABAG/MTC regional templates, CSAC model ordinances) and a
   trap for any model that assumes counties are independent draws.
3. **Vary the statute shape** so the set spans prescriptive (few standards,
   little dispersion) to minimal (mostly standards, wide dispersion). The
   headline cross-county result should be that recovered dispersion tracks
   planted dispersion across statutes of different shapes.

### 3.4 Retrieval realism from the CCW finding
Add a `p_fetch_blocked` per county (correlated with the site platform) so some
county documents exist in the index but cannot be fetched, reproducing the
403/Cloudflare wall that stopped six of fifteen real counties. This is a new
error source: the document is in the ceiling but unreachable, which is distinct
from both availability and retrieval failure and currently unmodelled.

### 3.5 Volume and rendering budget
Specs: with capacity-dependent disclosure, 250 processes produce roughly
2,500–3,500 specs rather than a flat 8,000. Rendering all of them with agents is
still too much. Plan: **render a stratified 20 counties in full** (say 6 large,
8 mid, 6 small, chosen to span the covariate space) and keep the rest
spec-only. Spec-only counties still support every structural and cross-county
metric, because the ceiling, the readings and the truth are all computed from
specs; only the text-extraction tier needs rendered artifacts. Simulated
applicants: scale by county size, 200 for the largest down to 25 for the
smallest, ≈15,000 records total.

### 3.6 Calibration and evaluation partitions, declared up front
Per `CLAUDE.md` and the audit's §5: W2 ships with **three disjoint county
partitions** — calibration (for the semantic confusion matrices), development,
and **reserved**, never opened until a model is frozen. Predicates and statutes
are shared across partitions; counties are not.

---

## 4. Where the county covariates enter the Bayesian model

The audit measured that in the V6 mixed fit, 199 of 302 latent coordinates were
under 10% learned, with agency effects at 13%, task effects 9%, operation
effects 9% and source offsets 8%. Every one of those blocks is a *pooling*
block: it can only be learned from many programs and agencies. Here is where the
58 counties and their covariates go.

### 4.1 The county effect becomes a regression
Today: `mu_i = m + alpha_agency + beta_task + gamma_program + delta_i`, with
`gamma_program` a weak fixed scale. Change to

```
alpha_c = gamma' x_c + eta_c,      eta_c ~ Normal(0, tau_county^2)
```

where `x_c` is the standardised covariate vector (log population, staff per
capita, budget per capita, rurality class, portal, consortium). Three things
follow:
- **Borrowed strength.** A county with two forum posts is predicted by its
  covariates plus the 58-county mean, not by a prior centred on seven days.
- **The rural question becomes a parameter.** `gamma_rural` is the estimated
  slowness attributable to rurality, with an interval, rather than an anecdote.
- **The identification report becomes interpretable.** It can separate "this
  county's own effect `eta_c` is learned" from "this county is predicted from
  covariates", which is exactly the distinction the audit says we must publish.

### 4.2 Disclosure propensity becomes a modelled, covariate-driven quantity
The audit's highest-value missing piece was π, the disclosure propensity, and ε,
the extractor error. With 58 counties:

```
logit pi(kind, c) = b_kind + lambda' x_c + u_c
```

estimated from *which documents were found* across counties, calibrated against
the synthetic world where the truth is known. This does real work: it converts
"we recovered 4 of 12 steps in Modoc" into a statement about whether that is
model failure or a ceiling of 5, **and it makes the fairness claim quantitative**:
the expected recoverable share of a process as a function of county capacity,
with an interval.

### 4.3 Reading dispersion: the discretion residual as a variance
For each standard predicate `p` of statute `s`, with counties indexed `c`:

```
reading_{p,c} ~ OrderedLogit(theta_p + delta' x_c + xi_{p,c}),   xi ~ Normal(0, omega_p^2)
```

`omega_p` is the **discretion residual for that predicate** and `delta` says who
is strict. With 58 draws per predicate these are well identified. Aggregate over
a statute's predicates and you have a statute-level discretion measure that is
estimated from implementations rather than asserted from text — Dan's question,
answered with a number and an interval. Add a spatial or lineage term to absorb
§3.3's template clusters, and report the effective number of independent
readings rather than the raw count.

### 4.4 Measurement parameters finally get their sample size
The single biggest gain, and the least glamorous. `report_sd`, `contamination`,
`count_error_scale`, the source-family offsets, and the selection strength κ are
currently either fixed constants or unidentified. They are **shared across all
counties**, so with 58 counties and several source families each they have
hundreds of observations instead of thirteen. In particular:
- **κ becomes identified** where a county has both official statistics and forum
  posts: the gap between the two is the selection effect, estimable across the
  counties that have both, then applied to the counties that have only forum
  posts. This is the anchor the audit said was missing and the reason the V5
  selection variant was just a prior.
- **Source offsets become genre-level**: a "county dashboard" offset, a "forum
  post" offset, a "third-party guide" offset, shared across 58 counties instead
  of one offset per thread. That is the Dawid-Skene structure with genres as
  annotators, which is what makes reliability weighting principled rather than
  hand-set.

### 4.5 Task effects get a crossed design
The audit's identification problem was that each agency performed disjoint
tasks. With one statute across 58 counties, **every county performs the same
task types** (intake screen, review, inspection, decision). The design becomes
crossed by construction, which is precisely the condition under which agency
and task effects separate. This is the structural fix for the 13%-learned
agency block; no amount of extra documents in a two-program world would have
done it.

---

## 5. What can be shared across counties with different processes

Alex's question, and the crux. Sharing must happen at the level of the key, not
the activity. Concretely, three tiers:

**Shared across all 58 counties (the pooling win).**
- Task-type effects, keyed on `task_type` from the existing taxonomy.
- Agency-class effects, keyed on `agency_class` (front counter, plan review,
  field inspection, records unit, fiscal), *not* on the county's own department
  name. LA's "Department of Regional Planning" and Alpine's "Community
  Development" are both `plan_review`.
- Every measurement parameter: reporting noise, contamination, genre offsets,
  selection strength, extractor error.
- The covariate coefficients `gamma`, `lambda`, `delta`.
- The reading space of each predicate (it comes from the shared statute).

**Shared by cluster.**
- Template lineage: counties that copied one ordinance share a reading and often
  a route, so a lineage random effect pools them.
- Consortium or platform: counties on the same permit portal share channel
  structure and, realistically, timing.
- Region, for anything spatially correlated.

**Not shared, estimated per county.**
- The route: which steps exist, in what order, with what rework loops. Each
  county keeps its own structural hypothesis, exactly as V6 already does.
- The county residual `eta_c` and per-operation residuals.

So a county whose process is genuinely unusual is not forced toward the mean on
*structure*, while still borrowing everything about *measurement* and *task
timing*. That combination is what turns 13 cases into a usable sample: the 302
coordinates become perhaps 500, but the blocks that matter go from 13
observations to 58 counties times several sources each, and the blocks that
cannot be shared are the ones we do not need to pool.

Marginalising the per-case latents (audit §3's recommendation) matters more at
this scale, not less: 250 processes with case-level coordinates would be
enormous, and quadrature over the case effect keeps the sampled dimension near
the number of structural and hierarchical parameters.

---

## 6. Metrics and the pre-registered criterion

Existing: activity recall and precision against truth and ceiling, actor
accuracy, order agreement, rework recall, fee and timing error, hallucination,
disentanglement, staleness, element coverage.

New, from today's work: criterion recall and precision, `reading_exact`,
`reading_direction`, step-attribution accuracy, ceiling-relative reading
recovery, and the cross-county entropy ratio and per-county agreement.

New, needed for the county question:
- **Covariate-coefficient recovery**: planted versus estimated `gamma`,
  `lambda`, `delta`, with coverage. This is the cleanest test that the
  covariate layer works, and it is a simulation-based-calibration exercise, not
  an accuracy contest.
- **Transfer accuracy**: predict a held-out county's timing using only its
  covariates and the other 57 counties. The LLM baseline cannot do this at all,
  which makes it the first criterion on which the Bayesian model should win by
  construction rather than by luck.
- **Availability-aware fairness metric**: recall as a function of county
  capacity, with the ceiling as the reference. The headline number is the gap
  between the largest and smallest decile, and whether the model *knows* it is
  in a low-information county.

**Pre-registered criterion for the frozen comparison** (per the audit's §5 item
6): coverage and interval score across all counties; transfer accuracy on
counties with no timing documents but shared task types; reading recovery and
dispersion recovery; count and labour accuracy where evidence exists; matched
LLM controls on the identical mixture ledger. Point accuracy on
well-documented counties is reported but is not the criterion.

---

## 7. Sequencing

**Stage 0, now, no dependencies.** A7 the covariate table, then A8 reddit
coverage (needs A7's populations). These two are cheap, mostly deterministic,
and everything else keys off them.

**Stage 1, scoping in parallel.** A1 CalFresh, A3 ADU, A5 environmental health,
A6 the sweep, A9 forums, and finishing A2's remaining 43 counties. Six agents.
Output is six scoping documents and a ranked shortlist.

**Stage 2, choose.** Pick the 3–4 programs. Current expectation, to be tested
rather than assumed: **ADU** (existing gold, HCD per-jurisdiction data, HCD
findings letters), **CalFresh** (CF 296 per-county timeliness is the best
official timing data in the set), **septic/LAMP** (a designed-tier process
document for all 58 counties by regulation, and the rural inversion), and
**General Assistance** as the maximal-discretion, minimal-evidence contrast.

**Stage 3, build W2.** §3 in order: generalise jurisdictions from covariates,
capacity-dependent disclosure, covariate-dependent strictness and lineage,
fetch-blocking, partitions. Then validate, then render the stratified 20.

**Stage 4, calibrate.** Semantic confusion matrices on W2's calibration
partition per the audit's §4 decision rule; the compiler's mixture priors and ε
come from there.

**Stage 5, fit.** V6 with the covariate layer, case latents marginalised, on the
development partition. Identification report on every fit. Then freeze and open
the reserved partition once.

**Stage 6, real data.** Apply to the chosen programs with the real
`ca_counties_covariates.csv`, and report the fairness curve.

---

## 8. Risks

1. **BenefitsCal may have flattened CalFresh variation.** Check before
   committing; if it has, CF 296 timeliness is still valuable as a covariate
   validation set even if the process is uniform.
2. **ADU spans 540 jurisdictions**, not 58. Restrict to the 58 counties'
   unincorporated processes for the cross-jurisdiction design, and treat cities
   as an extension.
3. **Fast-changing law.** ADU recodified in 2024; CCW reshaped by SB 2 in 2024
   and AB 1948 from 2027. Pin an as-of date and record it per document.
4. **Rate limits.** Today's lesson: ten concurrent web-heavy agents exhausted
   the session. Run at most four, stagger them, and have each write its file
   incrementally rather than at the end, so a death loses one section instead of
   everything.
5. **Scale is not a substitute for identification.** 58 counties fixes the
   pooling blocks and the crossed design. It does not make staff hours estimable
   from elapsed days, and it does not identify selection without an unselected
   sample in at least some counties. Keep the audit's list of
   never-learnable quantities in view.
6. **Political sensitivity** on CCW. It is an excellent measurement case with a
   clean statutory clock; if it is a distraction for the paper, use it for
   method development and lead with ADU and CalFresh.

---

## 9. The shared work queue: how two agents run this together

Added 2026-09-16 evening at Alex's request. The scoping is too big for one
session and the session limits bite (see the budget note below), so it runs as a
shared queue that several agents work at once without colliding or duplicating.

### 9.1 Three files, three jobs

| file | what it is | who writes it |
|---|---|---|
| `docs/scoping/WORK_PACKETS.json` | The **stable** definitions: nine packets, each with a priority, a budget, verified input URLs, a task list, an output contract and acceptance checks. Plus a registry of **verified assets** (URLs already confirmed to work, with what they contain) and **blocked sources** (with the symptom and the workaround). | Rarely edited. Edit only to add a packet or a verified asset. |
| `docs/scoping/FINDINGS.jsonl` | The **live** log: one JSON object per line. Who claimed what, what they are searching right now, what they found, what is blocked. Append-only, so concurrent writers cannot corrupt it and a crash costs one line. | Every agent, constantly. |
| the packet's own output file | The deliverable, written **incrementally** section by section. | The packet's owner. |

### 9.2 The protocol

```sh
# before starting anything at all
python3 pipeline/recon/scoping_log.py status          # per-packet state, owners, counts
python3 pipeline/recon/scoping_log.py tail -n 40      # what just happened

# take a packet nobody owns
python3 pipeline/recon/scoping_log.py claim P3-ADU-PROCESS-DOCS --by codex

# the running list: say what you are about to search, before you search it
python3 pipeline/recon/scoping_log.py looking P3-ADU-PROCESS-DOCS --by codex \
    --note "HCD ordinance findings letters, trying the HCD letters index"

# record each finding as you get it, with its URL
python3 pipeline/recon/scoping_log.py found P3-ADU-PROCESS-DOCS --by codex \
    --note "Sonoma County ADU page and ordinance" --url https://... \
    --value "60-day ministerial, no pre-application meeting"

# record every wall, they are findings about the availability model
python3 pipeline/recon/scoping_log.py blocked P3-ADU-PROCESS-DOCS --by codex \
    --note "Colusa County site returns 403 to scripts" --url https://...

# pick up what the other agent has added since you last looked
python3 pipeline/recon/scoping_log.py since 2026-09-16T18:30 --not-by codex

# finish
python3 pipeline/recon/scoping_log.py done P3-ADU-PROCESS-DOCS --by codex \
    --note "48 of 58 counties; 10 have no ADU page" --output docs/scoping/...md
```

Rules that matter:

1. **Claim before working.** One packet, one owner. If a packet is claimed and
   stale, `release` it rather than working it silently.
2. **`looking` before searching.** That is the running list Alex asked for: it
   lets the other agent see the query you are about to spend budget on and skip
   it. Poll with `since` every dozen fetches or so.
3. **Respect the budget** in the packet. If you run out, log `note` with what
   remains and `release` the packet. A `partial` result honestly labelled is
   worth more than an exhausted session.
4. **Write the output file incrementally.** Today nine agents died holding
   everything in their heads and nine reports were lost. Write section 1, then
   go and get section 2.
5. **"Not verified" is a real answer.** It means nothing was found by the means
   used. It never means the thing does not exist.
6. **Never invent a value.** Empty stays empty, and coverage is reported.
7. **Collision rules** are in the manifest: only P8 and P3 touch the covariate
   csv and only P3 writes two named columns of it; only the A8 sweep writes
   `reddit_raw/`; no scoping packet edits `benchmark/synth/` or
   `pipeline/procbench/`; nobody rewrites the audit.
8. **No commits.** Alex authorises those.

### 9.3 The nine packets, in priority order

| id | title | needs search? | budget | why it is ranked here |
|---|---|---|---|---|
| **P0-APR-TIMING** | Mine the HCD APR data into per-jurisdiction permit timing | **no** | 5 fetches, 90 min | The file is already on disk and it is the project's external-validity benchmark. Runnable with no search budget at all. |
| **P1-CALFRESH-DATA** | Confirm and extract the CalFresh per-county timeliness series | yes | 15 searches, 40 fetches | If CF 296 is per-county it is the best official timing series in the set: monthly, all 58 counties. |
| **P3-ADU-PROCESS-DOCS** | The 58-county ADU process document inventory | yes | 60 searches, 200 fetches | P0 gives the timing, this gives the process that produced it. The pair is what makes ADU the flagship. |
| **P5-ENV-HEALTH-LAMP** | Septic LAMPs, wells, retail food | yes | 60 searches, 180 fetches | Regional boards publish per-agency LAMP approval tables. Note the correction in §2 A5: a LAMP is optional Tier 2, not universal, and the tier choice is itself the jurisdiction-level decision worth measuring. Tests the rural inversion. |
| **P2-CCW-REMAINING** | The 43 counties the CCW sweep did not reach | yes | 60 searches, 200 fetches | 15 are already done to a good standard; finishing is mechanical. |
| **P7-FORUMS-BEYOND-REDDIT** | Where else people describe county processes | yes | 50 searches, 120 fetches | The rural-coverage answer probably lives in grand jury reports and Google reviews, not on reddit. |
| **P4-GENERAL-ASSISTANCE** | The maximal-discretion, minimal-evidence case | yes | 40 searches, 120 fetches | Highest process variation, worst evidence. The contrast case. |
| **P8-COVARIATE-GAPS** | Fill the 14 empty covariate columns | yes | 20 searches, 60 fetches | Needs a Census key and a manual State Controller download. |
| **P6-OTHER-STATUTES-SWEEP** | Rank every other 58-county process | yes | 50 searches, 100 fetches | Insurance against having picked the wrong programs. |

### 9.4 Budget reality, 2026-09-16 18:10 PDT

- **WebSearch: 200 of 200 used.** Spent by the ten agents before they died.
  Raise with `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` or use a fresh session.
- **Subagent model rate-limited until 21:50 PDT.** Nine of ten agents failed on
  this. Concurrency was the cause: run at most four.
- **WebFetch still works**, which is why the verified-asset registry grew after
  search died: if you know the URL you can still get the document. That is the
  argument for the registry.
- **P0 needs no web access at all** and is therefore the work to do now.

### 9.5 What the registry already holds

The highest-value find of the day, verified: **HCD Annual Progress Report Table
A2** is a 293 MB, 1,005,689-row unit-level permit file covering every California
jurisdiction from 2018 to 2023, with an entitlement-approval date, a
building-permit issue date and a certificate-of-occupancy date per project.
281,322 rows are ADUs. 35,729 of those have a usable entitlement-to-permit span,
and 40 counties have 30 or more. Per-county medians run from 0 days (Orange,
Santa Clara, Amador, Plumas) to 111 days (San Benito).

**Table A**, the companion application register, then turned out to carry
`APP_SUBMIT_DT` on 100% of its 358,264 rows plus a `PROJECT_TYPE` label that
says **Ministerial** or **Discretionary** in the jurisdiction's own words.
Joining the two gives three things at once:

1. **A much longer clock**, complete-application to building permit: a median
   of per-jurisdiction medians of **156 days across 275 jurisdictions**, against
   70 days on the permit records alone. Corrected naming: HCD defines the field
   as the application date *or* the date the agency found the application
   complete, so this is a **lower bound** on the applicant's experience and
   excludes the completeness back-and-forth in every case that arrived
   incomplete. Los Angeles city 152 days on 51,293
   projects; Los Angeles County's unincorporated area 331. Anyone
   reconstructing a process from permit records sees less than half the time
   the applicant lived through, and the missing part is pre-entitlement intake
   and resubmission: the part documents describe worst and forum posts describe
   best. This is independent real-data evidence for the audit's finding that
   end-to-end duration is underestimated.
2. **A calibration pair for the decision model.** A zero entitlement-to-permit
   span is a *noisy observable* of whether a discretionary step exists, and
   `PROJECT_TYPE` is a *sparse ground-truth label* for it. Measured: projects
   labelled Ministerial have a median span of 9 days with 45% at zero; those
   labelled Discretionary have a median of 108 days with 29% at zero. A
   twelve-fold separation, but both directions leak, so the zero span is
   evidence and not proof. That noisy-signal-with-partial-label structure is
   exactly what §4's calibration programme needs, and it now exists in real
   data rather than only in the synthetic world.
3. **Per-jurisdiction outcomes**: 194,347 approved, 54,382 pending, 1,219
   withdrawn, 89 disapproved. Disapproval is vanishingly rare, which is what a
   ministerial statute should produce and which means **denial rate is the wrong
   outcome to model for this program**; the pending backlog and withdrawal are
   the informative ones. The synthetic world currently derives a denial rate
   from predicate failure, so W2 needs a withdrawal and abandonment channel to
   match this program's real outcome structure.

Together these make ADU the strongest candidate to lead with, ahead of the
plan's original ranking. Full analysis:
[the APR permit-timing report](scoping/2026-09-16-apr-permit-timing.md).

---

## 10. What the real-world sweeps changed about the W2 design

Added 2026-09-16 evening, as the scoping packets returned. Each item is a
generator or model change forced by a measured fact, with the source.

### 10.1 A shared vendor platform manufactures false agreement

**The finding.** [CCW across 58 counties](scoping/2026-09-16-ccw-remaining-43-counties.md):
one vendor, Permitium, authors the public process text for **48 of 58 counties**,
and **32 of 35 live portals carry the identical sentence** "processing times can
take multiple weeks". Only nine counties say anything more specific.

**Why it matters more than it looks.** A model reading twenty counties sees the
same sentence twenty times and has every reason to treat it as corroborated
consensus. It is one vendor's boilerplate, and it carries no county-specific
information at all. This is a failure mode the synthetic world does not model:
its distractors are *wrong* facts about *other* processes, whereas this is the
*same* text across many processes, which is worse, because agreement is the
normal signal of reliability.

**W2 change.** Add a **shared-platform text channel**: a vendor serves a
configurable share of counties, contributes an identical templated document to
each, and that document discloses the process *structure* faithfully while
disclosing timing and fees only as vendor boilerplate. The scorer must then
distinguish genuine cross-county agreement from platform agreement, and the
Bayesian model must not treat n identical vendor sentences as n observations.
This is a concrete instance of the audit's warning that many reports of the same
thing are not many independent observations, and the vendor is the mechanism.

### 10.2 Fee variation far exceeds what cost recovery can explain

**The finding.** A new CCW licence costs **$84 in Lassen and $976 in Santa
Clara**, a factor of 11.6, rising to $1,093 in Alameda with its mandatory
psychological fee. **Santa Clara at $976 and San Mateo at $128 are twenty miles
apart.** Verified directly on both portals.

**W2 change.** The generator currently derives a fee from cost-recovery
arithmetic on a per-jurisdiction hourly rate, which cannot produce an 11.6-fold
spread between adjacent, similarly wealthy counties. Add a **fee policy effect**
independent of the cost basis, on the same footing as the timing policy effect
in §10.5. The statutory cap remains the ceiling where one exists, which is why
solar permits behave differently from CCW.

### 10.3 Timing disclosure tracks policy disclosure, on a second sample

**The finding.** Only **6 of 43** counties publish a CCW policy document, and
only **9 of 43** state a real processing time. They are substantially the same
counties. The first 15-county pass found the same pattern (4 of 15 published a
policy, and those 4 gave the real numbers).

**W2 change.** This confirms the shared county random effect across document
kinds already specified in §3.2, now on a sample of 58 rather than 15. Keep it,
and set the correlation from these two samples rather than by assumption.

### 10.4 A mandatory psychological evaluation is a jurisdiction-level decision rule

**The finding.** Five of 43 counties require a psychological examination of every
new applicant: Marin, San Mateo, Santa Clara, **Santa Barbara at $625** and
**Alameda at $400**. Three more make it discretionary with a cost cap. Thirty-four
never mention it. The earlier 15-county pass found none mandatory, so this is a
genuine large-county pattern rather than a universal one.

**Why it is the decision layer in the wild.** The same statute, the same
authorising section, and five counties have added a step with a fee, a
scheduling delay and its own failure mode, while 34 have not. That is exactly a
`local` predicate in `decision.py`: a locally added, testable requirement that
gates the outcome. The mechanism the generator already plants is confirmed to
exist, at a measurable prevalence of about 12%.

### 10.5 Policy, not capacity, drives the variation, and this now has three independent confirmations

The ADU permit timing showed covariates explaining about a quarter of the
between-county variance at best ([APR report](scoping/2026-09-16-apr-permit-timing.md)).
Staffing per capita runs *inverse* to county size
([covariates](scoping/2026-09-16-county-covariates.md)). And CCW fees vary
11.6-fold between adjacent counties with similar wealth. Three different
programs, three different measures, the same conclusion: **the between-county
variation is dominated by local policy choice, not by resources.**

**W2 change.** As §3.1 now specifies, the covariate coefficient on timing must be
deliberately small and the jurisdiction policy effect large, with both recorded
in `world.json` so recovery is scored against the true small value. A generator
that plants a strong covariate effect would make the model look good for the
wrong reason.

### 10.6 Retrieval failure is richer than a 403

**The finding.** Across both CCW passes, **14 of 58 counties (24%)** block a
scripted fetch of an official host. But four non-403 failure modes also appeared:
a 200-OK page that is not what its URL promises (Orange, Modoc, Santa Clara);
process published as **JPEG images** (Orange) or a scanned PDF (Sierra); a dead
policy link inside a live page (Marin); and paths no pattern predicts, such that
**the vendor's slug is more guessable than the county's own URL**, and even the
vendor's slugs are irregular (`lasd`, `sbcsd`, `scso`, `sfso`). The State
Controller and the Census API block us too.

**W2 change.** Replace the planned binary `p_fetch_blocked` with a **typed
retrieval-failure channel**: blocked, present-but-unparseable (image or scan),
stale-link, and misrouted. Each is in the ceiling and unreachable, but they are
distinguishable to a solver and should be distinguishable in the error
decomposition. Nothing in the current nine error sources covers them.

### 10.7 Template lineage, caught in the wild

Plumas County's portal text prices Plumas fees while referring to "the LCSO CCW
Unit" — Lassen County Sheriff's Office. That is a copy-paste tell of one county
adopting another's text, which is precisely the `lineage_note` mechanism
`local_rules.py` already plants. **Keep it, and extend it to readings** as §3.3
specifies, now with a real example to cite.

### 10.8 A LAMP is optional, so the tier choice is the measurement

Recorded in §2 A5: Tier 1 is the default *without* an approved septic LAMP and
Tier 2 the optional alternative requiring one. So the counties do not all hold
the same document, and **which tier a county chose is itself a jurisdiction-level
decision** of the kind this project measures. W2 should plant an analogous
optional-regime choice: a statute offering a default standard and a
locally-tailored alternative, with the county's choice observable only from
whether the tailored document exists.

### 10.9 Denial is the wrong outcome for a ministerial programme

Recorded in §9.5: 194,347 ADU approvals against **89 disapprovals**, with 54,382
pending. W2 needs the withdrawal and abandonment channel specified in the
[W2 spec](2026-09-16-w2-generator-spec.md), and the scorer should report backlog
and withdrawal rather than a denial rate for ministerial programmes.

### 10.10 The rural answer: the commons moves, it does not vanish, and it changes genre

**The finding**, from [forums beyond reddit](scoping/2026-09-16-forums-beyond-reddit.md).
Of the nine counties with no subreddit at all, **all nine publish civil grand
jury pages, seven post downloadable reports, and five are machine-readable
without OCR**. Grand juries are mandated in all 58 counties, so their supply is
**decoupled from population** — the only source family found with that property.

What changes is the *genre* of evidence, not merely its volume:

- Rural counties lose **first-person applicant durations**. CalGuns has a CCW
  thread for all 58 counties, created in one batch in 2010, and San Bernardino's
  holds **9,307 posts against Alpine's 15**, a ratio of 620 to 1; the nine
  no-subreddit counties hold 212 of 71,065 posts, 0.3%.
- They keep **institutional capacity evidence**. Modoc's 2024-25 grand jury:
  "approximately 16 of the 45 positions in the department remain unfilled."
  That is a staffing measurement for a county with no forum and no dashboard.
- And they sometimes document **the absence of process information itself**.
  Sierra County's grand jury: "There is no information about the building
  permits process or how to apply for one." An official source measuring the
  availability gap, which is the ceiling being reported from inside.
- Grand juries also carry **designed-tier timing**. Sonoma's 2025 report on
  Permit Sonoma prints average days-to-review by permit type — **well 123 down
  to 18, septic 98 down 79%, building 71 down 68%** — and describes the switch
  from serial to parallel plan-check routing that produced it.

**W2 changes.** This is the most consequential scoping result for the
availability model, and it makes §3.2's hurdle richer in three ways.

1. **Two document families with opposite supply curves.** Applicant-facing user
   evidence scales steeply with population and hits zero in the smallest
   counties. **Oversight evidence is population-independent**, because a statute
   mandates it. W2 must generate both, with different coefficients: the existing
   publication knobs for the first, and a near-flat probability for a mandated
   oversight document. That single change is what makes the fairness question
   answerable rather than foregone: a model that knows to look for the grand jury
   report can recover a rural process that a forum-only model cannot.
2. **Genre determines which slots a document can fill.** A forum post carries a
   case duration and a fee; an oversight report carries staffing, aggregate
   timing by step type, and process-structure change, but no individual case.
   The visibility model already assigns fields per artifact kind, so add an
   `oversight_report` kind whose reveals are aggregate timing, staffing and
   structure, and which can also reveal **the absence of a public description**.
3. **A document that reports the ceiling.** Sierra's finding has no analogue in
   the generator: an artifact whose content is that no artifact exists. Adding it
   lets a solver legitimately infer "this step is undocumented here" from
   evidence, instead of only from failing to find anything, which is what
   distinguishes a calibrated unknown from an unexamined one.

**Also recorded**: Glassdoor and Indeed, the only staff-side evidence anywhere,
are fully bot-walled, so the synthetic world's staff-only tier has no real-data
counterpart to calibrate against and must stay an assumption. And there was **no
working general web search** during this packet, so all discovery ran through
per-site indexes; the Board of Supervisors Legistar Web API is open and keyless
and embeds hearing chronologies in agenda titles, which is a harvest route worth
keeping.

### 10.11 Availability spans five orders of magnitude, so presence is the wrong measure

Counting *whether* a county has a subreddit understates the gradient badly.
Subscriber counts, now in the covariate table for 44 counties:

| county | subscribers |
|---|---:|
| Los Angeles | 724,594 |
| San Mateo | 657,747 |
| San Francisco | 545,320 |
| … | |
| Marin | 198 |
| Del Norte | 117 |
| Siskiyou | 42 |
| Plumas | **2** |

Log population against log subscribers gives **r = 0.823**, against 0.74 for
mere presence. W2's user-evidence volume should therefore be driven by a
subscriber-like audience parameter spanning five orders of magnitude, not by a
binary channel flag plus a modest count.

**A measurement caution this produced**, and a bug it caught in our own sweep:
three candidate subreddit names are not unique to California — r/hanford is
overwhelmingly the Washington nuclear site, r/Roseville is Michigan and
Minnesota, r/marysville is Washington and Ohio. A bare program-term query in
those returns out-of-state content attributed to a California county. They are
now queried only with the county name, as are the five subreddits shared by
several counties (r/bayarea serves six). Both fixes are in
`pipeline/recon/county_coverage.py`.

---

## 11. Stage 2 closed: the programmes to model

2026-09-16. The [other-statutes sweep](scoping/2026-09-16-other-58-county-statutes-sweep.md)
scored every candidate on variation, official timing data, user evidence, gold
feasibility and rural coverage. **Nothing beats ADU on timing**: no other
programme is case-level with both ends of a clock. But two datasets nobody had
identified change the combination, and both are verified below.

**The chosen four**, each carrying something none of the others can:

| programme | what only it contributes |
|---|---|
| **ADU permitting** | Continuous case-level duration for every jurisdiction over eight years, plus the jurisdiction's own ministerial/discretionary label. The external-validity benchmark, with the caveat that its long clock starts at *completeness*, not initial submission. |
| **Medi-Cal eligibility** | A structurally complete **58 × 98-month panel** (2018-01 to 2026-02), so panel length and completeness that ADU's 40 counties over 8 years cannot match. Plus a real platform-migration treatment variable. |
| **Registrar of voters (EAVS)** | **Which predicate failed, and whether it was cured.** ADU cannot teach failure at all: 89 disapprovals in 194,347 decisions. |
| **Agricultural commissioner permits** | The only clear **rural inversion**, plus a written state reference process (the DPR Compendium) as designed-tier gold. |

Deliberately left uncovered, and recorded so it is a choice rather than an
oversight: a zero-official-data maximal-discretion arm (General Assistance,
where the sweep verified that the GR 237 report carries no processing time and
every county row reads not-verified), fee-policy variation with written county
policy (CCW, already swept, keep it), the typed retrieval-failure channel,
staff-side evidence, and a denial-heavy adjudication.

### 11.1 EAVS observes the decision layer's failure-and-cure structure

**Verified**: the 2024 Election Administration and Voting Survey is one row per
local election jurisdiction, 6,461 rows and 535 columns, of which **California
is exactly 58**. Its codebook carries **61 itemised rejection items**, 37
provisional-ballot items, and critically `C7b Mail Ballots Successfully Cured`
and `C7c Mail Ballots Unsuccessfully Cured`.

That is precisely the structure `decision.py` plants: a predicate fails, the
failure is either fixable or fatal, and a fixable failure is cured with some
probability. **No other dataset in the project observes it.** The sweep measured
mail rejection rates from 0.0017 in Inyo to 0.0292 in Trinity, and the
signature-mismatch share of rejections from 0.000 in Kern to 0.871 in Colusa —
the same predicate, weighted seventeen-fold differently across counties.

**W2 consequence.** The `p_cure` knob and the fixable/fatal split now have a real
calibration target, and the scorer should report per-predicate failure and cure
rates, not just outcomes.

### 11.2 The Medi-Cal renewals file unblocks a covariate and supplies a natural experiment

**Verified and better than the sweep claimed.** The DHCS renewals-by-county file
carries a `SAWS` label on every county-month. All 58 counties appear and **all
58 change label during the migration**, so it names the consortium that
`calsaws.org` publishes counts for but never identifies by member.

Derived and now in the covariate table as `calsaws_legacy_consortium` and
`calsaws_live_from`:

| legacy consortium | counties |
|---|---:|
| C-IV | 39 |
| CalWIN | 18 |
| LRS (Los Angeles) | 1 |

Those counts **match CalSAWS's own published figures exactly**, which is
independent corroboration of a roster nobody publishes. The go-live months give
a staggered rollout: 40 counties in June 2021, then 2, 3, 3, 4 and 6 in six
later waves through June 2023.

**Why the staggering matters more than the label.** A common platform arriving
in six waves is a **natural experiment on §10.1's false-agreement problem**. If
shared software makes county process text converge, the convergence should
appear at each county's own go-live month and not before. That is a testable
prediction about whether platform agreement is real agreement, on real data,
with the treatment date known per county. The covariate column
`calsaws_legacy_consortium` went from 1 of 58 to **58 of 58**; the table is now
33 of 41 columns complete.

### 11.3 Rural data poverty exists inside official statistics too

The sweep found that the Medi-Cal call-centre file publishes real wait times in
hours, minutes and seconds, but for **34 of 58 counties — and the 25 missing are
all rural**.

This extends §10.10 in an uncomfortable direction. That section established that
the *user-generated* commons thins with population while *mandated oversight*
does not. Here a state agency's own operational dataset thins with population as
well. So availability is not merely a property of what the public writes; it is a
property of what government measures about itself, and the two gaps compound in
the same counties.

**W2 consequence.** The availability model's hurdle must apply to
**official-statistics artifacts too**, not only to forum posts. A small county
should sometimes lack a dashboard for the same structural reason it lacks a
subreddit, which makes the information ceiling itself covariate-dependent across
both evidence tiers rather than just one.

---

## 12. The identification strategy: capped versus uncapped dimensions of one statute

2026-09-16, from [the General Assistance sweep](scoping/2026-09-16-general-assistance-58-counties.md).
**This is the cleanest identification of the project's central thesis that we
have, and it is better than anything the plan proposed.** It should shape both
the real-data design and W2.

### The mechanism

The project's thesis is that cross-jurisdiction variation measures what a
statute leaves undetermined. The problem with testing it across programmes is
confounding: counties differ in wealth, politics, staffing, urbanity, caseload,
vendor and legal exposure, so any between-county variation has a dozen
candidate explanations besides statutory silence.

General Assistance solves that, because **the statute partitions its own
dimensions into capped and uncapped, for the same counties, in the same
document, at the same time.** Welf. & Inst. Code §17000 delegates everything,
but §17001.5 then enumerates the permitted restrictions and **caps each one**.
Verified against the statute text:

| dimension | what §17001.5 says | what counties do |
|---|---|---|
| Residency | "Any residence requirement under this paragraph **shall not exceed 15 days**" | Five verified counties set **exactly 15 days**. Not 14, not 10 |
| Employable time limit | "**more than three months in any 12-month period**" | **Nine of eleven** verified limits are exactly 3 months |
| Shared-housing reduction | "not more than" **15% / 20% / 25%** by household size | Counties sit on the caps |
| Sanction | "**not more than 180 days**" | ditto |
| Forms of aid | five enumerated: cash, in-kind, two-party payment, voucher, third-party check | counties choose among the five |
| **Grant amount** | **uncapped** (§17000.5 offers only a safe harbour) | **3.2× to 40× variance** |
| **Asset and liquid-asset limits** | **uncapped** | wide variance |
| **Work-programme design, SSI-advocacy staffing** | **uncapped** | wide variance |

**Variance collapses onto the cap wherever the Legislature wrote a number, and
spreads 3.2 to 40-fold wherever it did not.**

Every alternative explanation is held constant across the two sets of
dimensions, because they are the same counties, on the same day, in the same
programme, administered by the same staff. The only thing that differs is
whether a number appears in the statute. That is a within-statute,
within-county control for the statutory-silence mechanism, and no cross-programme
comparison can match it.

Related and worth keeping: **§17000.5 is a safe harbour, not a floor.** A grant
set at 62% of the 1991 federal poverty line "shall constitute a sufficient
standard of aid". That sentence is the Legislature's answer to *Boehm*: it
converts an open-ended judicial adequacy standard into a number a county can
comply with without ever conducting a needs study. A statute closing a
discretionary predicate by legislating a safe harbour is itself a mechanism the
project should model.

### W2 consequence, and it fixes a real weakness

The W2 spec criticised §3.3's dispersion target on the ground that a
distribution with 89% of its mass on one reading makes **entropy recovery
trivially satisfiable**, so `cross()` should report tail recall instead. The
capped/uncapped partition is a better answer than either.

**W2 should plant both kinds of dimension in the same statute**: some predicates
with a legislated bound that counties pile onto, and some with no bound at all.
Then the scored quantity is not generic dispersion but the **contrast**: does
the model recover that variance is near-zero on capped dimensions and wide on
uncapped ones? That is a sharper test, it cannot be satisfied by predicting the
modal reading everywhere, and it measures the thing the project actually claims.

Concretely, in `decision.py` terms: a `capped` predicate kind whose reading
space is a bound plus a small number of values at or under it, against the
existing `standard` kind whose space is wide and unbounded. The scorer then
reports recovered variance by kind, and the headline result is the ratio.

### Why General Assistance is not the rural test, and why that matters

The same packet demolished the rural hypothesis *for this programme*, with a
fact worth quoting: **Sierra County, population 3,000, publishes its time limit;
Santa Clara, 630 times larger, publishes nothing at all.** Six of the ten
largest counties in California are dark on General Assistance, while seven of
the smallest publish a readable paragraph each.

And the instrument is confounded at the root: **20 of 58 counties are dark
because of a web application firewall, which is a procurement decision, not a
capacity one**, and the blocked set skews large. As the packet puts it, you
cannot measure rural darkness with an instrument whose loudest signal is that a
county bought Cloudflare.

So the rural question stays with the programmes in §11, and General Assistance
earns its place for the identification strategy above. That also sharpens
§10.6's typed retrieval-failure channel: a firewall block must be modelled as
**uncorrelated with county capacity**, or it will contaminate exactly the
fairness estimate it looks like evidence for.
