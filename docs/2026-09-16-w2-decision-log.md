# W2 decision log: where the implementation diverges from the spec

2026-09-16. Required by the
[corpus-generation plan](2026-09-16-synthetic-corpus-generation-plan.md) §2:
*"Use the detailed W2 spec as an implementation reference, with the corrections
and proposed scope changes in this plan made explicit in a small decision log.
Do not silently implement conflicting instructions from both documents."*

The [W2 spec](2026-09-16-w2-generator-spec.md) and the plan disagree in places,
and both predate the
[source-volume register](2026-09-16-source-volume-register.md). This log records
every point where the built code follows neither document verbatim, with the
reason. Where the spec is right, it says so and cites nothing further.

Implemented: `benchmark/synth/generator/{counties,capacity,lineage}.py` plus the
`world_model_version` knob in `world.py`. Tests:
`tests/test_generator_county_panel.py`, `tests/test_generator_lineage.py`.
Corpus check: `pipeline/procbench/audit_corpus_anchors.py`.

## D1. Version 1 is preserved by addition, not by branching

**Spec:** a `world_model_version` knob with 1 as legacy.
**Built:** the same, and the county panel is **appended** to the four
hand-written jurisdictions rather than replacing them.
**Why:** every W1 process, artifact, test and saved snapshot keeps its identity,
so the county world is a strict superset and the byte-identity test on the v1
process hashes keeps passing. All 439 existing tests pass unchanged.

## D2. `V_POP` rises from 0.85 to 1.25, and the unit changes

**Spec:** `V0["county_sub"] = 0.35`, `V_POP = 0.85`, one draw per county.
**Built:** `V0 = 2.159`, `V_POP = 1.250`, one draw per **county × programme ×
channel**, plus a `statewide_sub` draw at `V0 = 1.800` that is summed with it.
**Why:** three separate errors, each found by trying to reproduce a measurement.

1. `V_POP = 0.85` on a z-score implies a log-log slope of 0.539 against a
   measured 0.747. The spec's error direction made rural counties look
   *better* supplied than they are.
2. Drawing one volume per county and reusing it for every programme applies the
   county's whole post budget to each process. Realised slope: **0.32**.
3. Calibrating `county_sub` alone puts **22%** of cells at zero against a
   measured 7%, because it charges the nine counties with no forum of their own
   with having no user evidence at all. The sweep deduplicated a post to one
   county whichever venue carried it, so the quantity to reproduce is the union.
   This is the same overstatement of the disappearing commons that the spec
   itself rejected when it tuned `H0` from 1.55 to 2.10 — the right instinct,
   applied to the wrong stage.

The union now reproduces four moments: per-cell median 14 (measured 13), mean
38.1 (39.6), zero share 7.4% (7%), county-total slope 0.701 (0.747), and 57.7 of
58 counties with any user evidence (57).

## D3. `V_DELAY` drops from 0.55 to 0.0 and becomes a scenario variable

**Spec:** `V_DELAY = 0.55`, described as "delay generates posts — this is the
selection mechanism the plan's κ is meant to estimate" and as "the single most
important measurement parameter in the plan."
**Built:** `V_DELAY = 0.0` by default, with 0.55 retained as the
`evidence_constrained` scenario and −0.40 as `delay_suppresses`.
**Why:** it is now testable and does not survive. Regressing county post volume
on population and delay across 50 counties with at least 30 measured spans, the
delay coefficient is **+0.076 with a ΔR² of 0.004**, and for timing-bearing
posts specifically the sign is **negative** (−0.034). The raw correlation of
+0.44 is population confounding, since delay itself correlates with population
at r = +0.50. The result holds under three domain matchings.

This does not prove κ is zero, and the log says so: the test is at county level
and the mechanism plausibly lives at case level — delayed *applicants* posting,
not delayed *counties*. The plan's §6 rule decides the default: *"include zero
and alternative-sign sensitivity settings where the evidence does not identify
direction."* A result that survives both the zero and the 0.55 scenario does not
depend on κ's direction, which is a stronger claim than either alone.

## D4. Per-cell counts are Poisson-lognormal, not Poisson

**Spec:** `rng_poisson(rng, lam)`.
**Built:** Poisson with a lognormal cell-level term, `SIGMA_CELL = 0.3`, on top
of the county effect `SIGMA_V`.
**Why:** the measured counts have mean 39.6 against median 13, a ratio of 3.0.
Poisson has variance equal to its mean and cannot produce that skew. Note the
real maximum of 303 is **censored** by the search API's 100-result limit, so the
upper tail is not a calibration target.

## D5. The thread count follows post volume; the old cap destroyed the gradient

**Spec:** `select_personas` should draw `n_posts` and take the top `n_posts` by
weighted sampling. Correct, and implemented.
**Built additionally:** `max_threads_per_process` is replaced for counties by
`max_threads_per_county_process`, a pure render backstop set above the real
observed maximum.
**Why:** the old `n_threads = min(3, len(posters) // 3)` put every county at the
ceiling regardless of its availability draw, realising a slope of **0.23**. A
cap of 12 still bound and gave 0.54; the corpus max cell landed on exactly
121 = 120 + 1, which is how the cap was caught. Anything the cap drops is
counted per county rather than silently applied, per the plan's rule against
asserting a coverage a cap prevented.

## D6. Caseload scales with population — a requirement the spec did not state

**Spec:** §11.2 mentions applicant volume but the generator uses a constant
`n_applicants`.
**Built:** `capacity.caseload(county, median_caseload)` scales from a median
county at the measured log-log slope of **0.989** (r = 0.950), with a floor of
12 and a render ceiling of 6,000.
**Why:** two reasons, one realism and one mechanical. Real project counts run
from 61 in the smallest county to 195,483 in the largest, so per-capita demand
is effectively constant. And a forum post has to come from a case: with a flat
caseload, a county whose availability draw asks for 500 posts can only supply as
many posters as it has applicants, which held the realised slope at 0.50. **The
user-evidence anchor imposes a minimum caseload**, which is a derived sizing
requirement of the same kind as the calibration bridge's 1,056 rows per class.

## D7. `SPEED`, `HOURLY` and the rurality codes are functionised from real gradients

**Spec:** names `speed_factor`, `hourly_rate` and `caseload` among the functions
`capacity.py` should own. Correct; here is what they were anchored to.

- **Speed.** Population explains **25%** of between-county timing variance
  (slope +0.4988, r = +0.498, largest county ~6.3× the smallest). Bigger is
  slower. The log-scale spread is compressed to keep durations renderable while
  the *ratio* of explained to unexplained variance is held exactly, so the
  realised r is +0.499. The plan's warning is honoured with `speed_null` and
  `speed_inverse` scenarios; the residual is deliberately large because a
  generator that made speed covariate-predictable would hand the estimator
  information the real world withholds.
- **Hourly rate.** Derived from the measured wage gradient,
  ln(wage) = 10.371 + 0.0658·ln(pop), r = 0.675 — a **shallow** relationship, so
  fees barely track county size. The overhead multiplier of 5.5 is an
  assumption, labelled as one; fee divided by rate is not measured labour.
- **Rurality.** RUCC and UIC are kept as separate variables that genuinely
  disagree for about 6% of counties, against at least 4 of 58 in reality. A
  first implementation had them perfectly collapsed, which would have hidden
  that a rurality claim depends on which code was used — the error that
  mislabelled Alpine, Del Norte, Inyo and Lassen.

## D8. Implementation is a per-cell draw, not a balanced assignment

**Spec and W1:** a load-balancing assignment that fixes the total process count.
**Built:** for counties, a per-(county, domain) draw with a `COUNTY_MANDATE`
floor per domain and a modest population slope on the permissive ones.
**Why:** the real pattern is not a balanced design. General Assistance and the
civil grand jury are mandated in all 58 counties and vary only in local policy;
a septic LAMP is an **optional Tier 2** instrument, so a county without one may
lawfully be using Tier 1. A non-implementation is recorded with its reason and
an explicit note that no local programme is not the same as an unfound document.

## D9. Source lineage separates copied text from agreeing facts

**Plan §5:** three separate links — same case, same cohort, copied template.
Implemented as three types in `lineage.py`, with `facts_agree` as an
**independent** field.
**Why the independence matters:** copied prose may state a locally overridden
fee (two counties share text, run different procedures — the CCW vendor pages
and the consortium templates), and differently-worded documents may state one
identical aggregate (the hearings reports' annual and quarterly restatements).
Collapsing the two would destroy the distinction. The deduplication rules differ
accordingly, and the asymmetry is the point: `same_case` and `same_cohort` call
for one observation each, while `copied_text` must **not** have its facts
deduplicated, because a locally overridden number is real information.
Consortium copying forms a star, not a chain, so a solver cannot recover an
adoption order the real data does not reveal.

## D10. Universal channels are certain, not merely very likely

**Spec:** `H0 = +9.9` for channels that always exist.
**Built:** `H0 >= 9.0` with a zero population slope is treated as a declared
certainty.
**Why:** logistic(9.9) leaves a one-in-twenty-thousand failure, which over
enough seeds produces a county with no civil grand jury — a thing that cannot
happen, since the report is statutorily mandated in all 58. Found by a test.

## Still open

- **The ten-family scope change** in the plan's §4 is not implemented. The
  panel runs the twelve existing W1 domains. Adding the benefits-side families
  (nutrition, health eligibility, county assistance, home support, assessment
  appeal) is the next scope decision and needs its own approval, since it is a
  new truth generator rather than a parameter change.
- **Grand-jury volume is not counted** at title level, so `CHANNEL_VOLUME`
  carries it as a `design_assumption` with a deliberately shallow slope. It is
  the largest known unmeasured quantity and the most likely to change the rural
  story, and it must not be given a fitted population slope until counted.
- **No render has been bought.** Everything above is truth, specs and
  provenance, which are local CPU only.
- **Nothing is committed.** The repository has one approved snapshot and the
  W2 work is uncommitted pending Alex's review.
