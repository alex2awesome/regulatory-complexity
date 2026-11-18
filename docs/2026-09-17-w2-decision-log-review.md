# Independent review of the W2 decision log and model readiness

2026-09-17. Requested by Alex. Reviewed the
[decision log](2026-09-16-w2-decision-log.md),
[release report](2026-09-16-w2-dev-001-release-report.md), source-volume register,
and current generator/anchor-audit code. Read-only diagnostics inspected the
explicitly development-only `W2_DEV_001` specifications, one process and one case
row, plus tiny in-memory worlds. **No reserved world, inference run, LLM call,
new unit tests or generator/model edits.** Original documents remain unchanged.
[Diagnostic values and source hashes](scoping/2026-09-17-w2-decision-review-diagnostics.json).

## Verdict

The direction is sensible, but **the built world is not yet a valid test of the
complete Bayesian burden model**. It is a larger development scaffold. Matching
five marginal counts does not establish faithful information content, working
sensitivity scenarios, source dependence, labor truth or agency identification.
The release report correctly says it is unrendered, development-only and not
evidence of Bayesian advantage. Keep those qualifications; do not promote
“all anchors reproduced” to scientific validation.

The highest-priority problems are not a need for a different Bayesian model.
They are defective calibration targets, disconnected generator mechanisms, a
selection artifact, and missing parts of the benchmark measurement contract.

## Readiness follow-up, September 17 at 04:13 PDT

Two additional source-code checks matter before interpreting the requested V6
run. They do not authorize restarting the active rendering workflows or
changing their frozen selection.

- **The new split selector is not round-robin as documented.**
  `benchmark/synth/render/select.py: stratify` constructs all calibration labels,
  then all development labels, then all reserved labels, and assigns them to a
  descending population-ranked list. A read-only 58-county dummy-rank check with
  20 selected counties gives calibration ranks 1/3/6/9/12/15/18/21, development
  24/27/30/32/35/38/41, and reserved 44/47/50/53/56. Selecting counties across the
  overall range does not make each split cover that range. This is evidence of
  a code/documentation mismatch; the frozen run's split provenance must also
  be checked. If retained, describe it as population-size extrapolation, not a
  balanced within-size held-out comparison. Do not silently rewrite partitions
  after rendering or seeing results.
- **Count completion is not verification of the frozen bytes.** `status.py`
  and `verify_batches.py` track verdicts by artifact ID, not content hash. The
  652 verification-log records present during this schema-only check have no
  top-level artifact-hash field. A replacement can therefore inherit the
  existence of an earlier verdict until it is verified again. The user's
  `observed.complete_by_counts` gate remains the operational trigger, but record
  content hashes, verification provenance and any unresolved freshness at the
  subsequent freeze. A saved input hash created now does not retrospectively
  prove which bytes a verifier saw.

[Read-only diagnostics and selector hash](scoping/2026-09-17-w2-readiness-followup.json).
No inference, extraction, generator change, truth read or paid call was needed
for these checks. The earlier audit's development-truth access is separately
disclosed above; a parsing agent must still start without that conversation.

At 04:42 PDT the frozen `render_manifest.json` partitions were also checked:
they match the population-block assignment implied by the current selector
and the county builder's monotone population-quantile ID ordering. This reads
only orchestration metadata and code, not world/truth/spec files. The manifest
and both source hashes are retained in the
[frozen split check](scoping/2026-09-17-w2-frozen-split-check.json).
It confirms the actual split IDs, not the complete historical build provenance;
no partitions were changed.

## Findings, in priority order

### 1. D2/D4/D5 calibrate to program counts that are not program-specific

[source_volume.py](../pipeline/recon/source_volume.py) fixes repeated query hits
within a cell, but its `reddit_volume()` still places generic county-name hits
from regional/statewide subreddits into each program without relevance review.
An exact counterexample from the retained bytes: the sole r/California Modoc
hit is **a map of the October 2023 eclipse** (`1774vnw`). It contributes to
CalFresh, Medi-Cal, GA, ADU, septic/well and building-permit cells, as well as
the CCW cell. It is not one document about each program.

Reproduction gives the documented median 13 and mean 39.554 across 406 cells,
but those are **retrieved candidate counts**, not verified process evidence.
The stated 4,998 distinct posts are actually county/post memberships: the
register selects **4,591 globally unique IDs**, 269 of which are credited to
multiple counties, creating 407 extra memberships. A post can legitimately
discuss multiple counties; the error is calling their sum globally distinct.
The earlier N11 number, 4,664 IDs, refers to the entire raw cache including
additional probes, a different universe.

There are also **25 cached error sidecars**. The legacy collector stores failed
requests as empty result arrays, so downstream zeros need their retrieval
states restored. A time-word regex is not validation that a post measures a
process duration. API limits, unequal search effort, venue geography and
cross-program overlap further limit population-level interpretation.

**Consequence:** reproduce these numbers only as a search-retrieval experiment,
not as identified availability parameters. Build the relevance/jurisdiction/
case review layer and pagination-aware coverage first. Mark currently fitted
coefficients provisional/derived, rather than empirically measured process
rates. D6's increase in simulated caseload should not be justified by the need
to supply these contaminated post-count targets.

### 2. D3's sensitivity scenarios do not change the implemented mechanism

Both [world.py](../benchmark/synth/generator/world.py) `_channel_draws()` and
[visibility.py](../benchmark/synth/generator/visibility.py) `select_personas()`
call `capacity.post_volume()` without `delay_z` or `caseload_z`. Both default to
zero. Therefore `V_DELAY` and `V_CASELOAD` contribute zero to every such call.

Reproduced for seed 101, 58 counties and the two Reddit channels: `reference`,
`evidence_constrained` and `delay_suppresses` yield **identical count vectors**,
each totaling 2,009 for the well-permit family. A comparison among those builds
cannot demonstrate robustness to the direction of selection.

Separately, case-level complaint selection remains active and does not use
`V_DELAY`. The ecological regression of county volume on county delay cannot
identify that applicant-level mechanism. A zero county-volume slope is a
reasonable *sensitivity reference*, not a measured zero ascertainment bias.
The log recognizes the ecological limitation but the current wiring does not
implement the promised test.

### 3. Poster selection is priority truncation, not weighted sampling

`select_personas()` first probabilistically filters cases, then sorts them
**denied → delayed → abandoned → normal**, and takes `posters[:n_posts]`.
When the volume quota is small relative to the eligible pool, the earliest
classes consume the quota. This is not the weighted sampling described in D5;
it imposes an additional, strong and quota-dependent outcome selection.

The development world's 16,908 target Reddit OPs contain:

| OP class | Count |
|---|---:|
| denied | 14,713 (87.0%) |
| delayed | 1,910 |
| abandoned | 123 |
| normal | 162 |

These are all target jurisdictions, including the retained hand-written ones.
The skew is a mechanical consequence to audit, not a measured real denial
posting rate. The code also excludes **every censored/pending case**, despite
the newly retrieved IHSS and Medi-Cal accounts illustrating precisely that
source type. Independently declare case selection, outcome selection and
publication volume, then check their joint realized distribution.

### 4. D7's speed cache contaminates repeated builds

[processes.py](../benchmark/synth/generator/processes.py) stores generated speed
in module-global `_SPEED_CACHE`, keyed only by county ID. It is neither scoped
to world/seed/scenario nor cleared at build entry.

Reproduced in one Python process: build reference, then speed-inverse. For C01
and C02 the second build retains **0.723 / 1.620**, although inverse should be
**1.452 / 0.816**. Clearing the in-memory cache before the second build produces
the expected values and different process dictionaries. The same problem can
affect different seeds using reused county IDs. Separate fresh CLI processes
avoid this particular cross-build contamination; library/multi-seed experiments
do not. Fix isolation before interpreting scenario or recovery sweeps.

### 5. Several advertised mechanisms currently stop at metadata

The source graph in `W2_DEV_001` has **34 `copied_text` links, zero `same_case`
links and zero `same_cohort` links**. The latter helper functions exist but are
not called by the world/spec build. The new source-lineage graph does not feed
the document-spec renderer. W1's older `local_rules.lineage_from` path remains
a separate copying mechanism; that is not implementation of all three new
links. An independently drawn county-level consortium star is not yet a set of
actual copied documents with verified shared and overridden facts.

Likewise, `admin_forum`, `grand_jury`, office-review and staff-review volume
draws, the family retrieval funnel, `INFORMATIVE_SHARE`, and `DEFECTS` are
recorded in capacity/world metadata but not used to realize corresponding
artifact behavior. The `rural_commons_moves` override changes a grand-jury
volume draw but does not generate grand-jury report artifacts. None exist in
the inspected target specs. The ordinary forum remains an older per-process
publication coin flip, not the calibrated CalGuns mechanism.

Every one of the **16,908 target Reddit specs includes a timing reveal**.
That is not the register's 32% duration-word rate, nor its mostly empty
timing-bearing cells. The two measurements are not perfectly equivalent, but
the core missing mechanism is direct: non-timing/question-only user posts are
not produced by this OP path. Population-scaled document counts alone do not
produce the intended information scarcity.

### 6. D9's statistical rule needs to operate at claim level

The three dependence types are a useful design. But “same case means one
observation” is too coarse, and “copied text means never deduplicate facts” is
also too coarse.

Two reports of one case may reveal different steps or different endpoints;
two noisy measurements of the same step may provide additional information
conditional on a shared latent duration. They should share **one latent case**,
not automatically be collapsed to one observation. Identical copied claims
should not be counted as independent measurements; locally overridden claims
may be new information. Reports on one cohort may contain distinct statistics
or partially overlapping populations, not just duplicate means.

The principled target is a shared latent case/cohort with claim-specific
observation operators and explicitly dependent reporting errors. Preserve
which *claim* was copied, which was revised locally, and which reports share
the underlying units. This is exactly a reason to retain the Bayesian layer.

### 7. The full burden/hierarchy experiment remains missing

The simulator currently produces elapsed dates, fees, routes, rework and
decisions. The inspected activity timing is `median_days`/`p90_days`; the
case/path schema has no separate payer-person-hours or agency-person-hours.
Fee derivations mentioning staff hours do not create an independent labor truth
channel. There is no new county-based text-to-V6 fit or matched LLM evaluation.

The larger county panel also does not by itself identify **intrinsic agency
delay**. Current activity locations largely combine a shared county pace,
domain pace, task-class constants and operation jitter; some shot-clock branches
replace that calculation. This is not a separately planted agency random effect
with a documented recovery target. Agency names reused across programs help
define a potential design, but the actually observed agency×task graph still
needs its rank/information and transfer check. A county speed multiplier is not
an agency effect merely because an agency performs a task there.

The decision log honestly says the benefits families remain absent. W2 still
uses the twelve W1 domains, so CalFresh/IHSS/GA findings are inspiration rather
than faithful tests of those routes. This scope decision should be settled
before rendering thousands of documents.

## Assessment of individual decisions

| Decision | Assessment |
|---|---|
| D1, preserve V1 | Sensible compatibility approach. A process-hash regression is narrower than byte identity of an entire world, all cases and all artifacts. Do not overstate it. |
| D2, county×program×channel volume | Sensible unit, invalid relevance-calibration targets and unresolved overlap. A union requires document identity/overlap, not automatically summing independent channel counts. |
| D3, zero and opposite-sign scenarios | Sensible sensitivity principle. Current scenarios are inert; ecological coefficients cannot identify case selection. |
| D4, Poisson-lognormal | Plausible family, not established by a pooled mean/median ratio. A heterogeneous Poisson regression already has marginal variance `E[lambda] + Var(lambda)` and can be highly skewed. Estimate residual overdispersion conditional on population, program, county and retrieval exposure. |
| D5, remove tiny render cap | Sensible to expose cap losses. Fix priority truncation and information mix; a larger cap alone is not representative sampling. |
| D6, scale caseload | Reasonable design assumption. APR projects aggregated over cities, years and housing categories do not identify each county-administered program's applicant incidence. Label the conversion and horizon. |
| D7, speed/wage/rurality | Keeping RUCC and UIC distinct is sound. Aggregated permit delays and all-local-government wages are not intrinsic county-agency parameters. Compression, clipping, proxy transport and fitting constants require derived/assumed labels; the speed cache is a concrete bug. |
| D8, implementation versus missing documents | Correct distinction. `COUNTY_MANDATE` values for the fictional W1 domains are design choices, not measured from GA or optional LAMP adoption. In particular, a fictional adoption probability is not an estimate of real ADU legality. |
| D9, three link types | Useful schema, incomplete integration and over-coarse deduplication rule. Require claim-level, artifact-realized dependencies. |
| D10, declared universal institution | Use an explicit invariant where justified, not a magic logit threshold for “measured 58/58.” Institution existence, relevant-topic coverage, publication, access and readable text remain different stages. |

On D10, California Penal Code §933 requires a final report of a grand jury's
findings and provides filing/response duties; it does not promise a web-readable
report on every county program every year. That is why a universal institution
cannot close each program's evidence cell. [Primary statute](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PEN&sectionNum=933.).

The continuing retrieval adds a concrete counterexample to equating institutional
existence with report availability: Modoc's 2024–25 grand-jury report, PDF page 8,
says its retrospective review could not locate reports from the 2021–22 and
2022–23 juries. That is a reported inability to locate them, **not proof they
never existed**. [Retained report, newspaper-hosted copy](../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_06049_repair_14.pdf);
[publication copy](https://modocrecord.com/wp-content/uploads/2025/06/Modoc-County-Grand-Jury-Report-2024-2025.pdf).

## What the next acceptance gate should show

1. Correct the empirical register's units, relevance, failed-query states and
   provenance labels. Freeze a versioned, reviewed source-to-design register.
2. Make scenario changes observable in generated cases/documents, in either
   fresh processes or isolated library calls. Preserve control RNGs where useful.
3. Realize claim-level case/cohort/template dependence, pending cases and an
   explicit mixture of timing-bearing and non-timing material.
4. Add distinct payer/agency labor truth and observation types. Define which
   agency/task/county quantities are identifiable, and which remain prior-driven.
5. Use the small multi-program pilot for rendering/claim-label verification,
   then test calibrated intervals, transfer, counts and labor against matched
   controls. Marginal corpus-count checks remain useful diagnostics, not the
   scientific acceptance criterion.

This is a review and repair order, **not permission inferred to rewrite another
agent's code**. The retrieval work continues separately under the
[exhaustive-coverage protocol](scoping/2026-09-17-exhaustive-retrieval-protocol.md).

## Follow-up: fixes and restart, 2026-09-17 00:50 PDT

The findings above describe the frozen diagnostic snapshot, not an assertion
that no repairs have happened. The shared `W2-RENDER` log now reports a restarted
render at 00:47, 145 batches, and an OP denial share of 5.4%. Those are the
rendering agent's claims; this follow-up checks source wiring, not the rebuilt
world or rendered text.

- **Finding 3's priority-truncation bug is repaired in source.** The second
  stage now draws uniformly from complaint-filtered eligible cases. However,
  every censored case is still excluded, including the newly introduced stalled
  outcome. The docstring still describes the old ordering/calibration story.
- **Finding 4's cache key is repaired in source.** Cache reads and writes use
  `(world, seed, speed_scenario, jur_id)` consistently.
- **Finding 2 is partly repaired.** `visibility.select_personas()` now supplies
  standardized county speed as a delay proxy. `world._channel_draws()` still
  omits `delay_z`, so its channel-volume metadata does not describe the same
  scenario-sensitive mechanism. County speed is also a proxy, not the realized
  median process delay. The original source-count/relevance caveats remain.
- **Finding 5 is not closed by the inspected code.** `restatements()` and
  `case_links()` still have no callers in the generator. No evidence here
  establishes artifact-realized case/cohort dependence, the intended mixture of
  timing/non-timing posts, or the new source families.

The new self-selection and stalled-case changes are plausible design choices,
not measurements proving outcome calibration. In the current
[resume runbook](2026-09-17-w2-resume.md), the four “after” percentages sum to
**109.21%** (88.8 + 0.81 + 15.7 + 3.9). Their denominators or overlap need to be
reconciled; do not interpret that table as one outcome distribution. The later
shared-log denial figure, 1.66%, also supersedes the runbook's 0.81% claim but
does not explain the denominator. Raw counts on a common cohort are needed.

There were seven main findings in this review. The shared-log statement that
“all 5 codex findings” are closed is therefore not an independently verified
closure of this audit. Source repairs, rebuilt-world diagnostics, render
completion and scientific validation are separate gates. This reviewer has not
changed the generator or stopped the restarted render. The requested
[hourly V6 handoff](scoping/W2_V6_WATCH.json) uses
`observed.complete_by_counts` for rendering completion, with the remaining
benchmark limitations retained in any subsequent fit report.

### Additional exposure-denominator issue found during retrieval

The [county-covariate README](../corpus/counties/README.md) generalizes county
environmental-health administration to unincorporated territory, then proposes
`population × unincorporated_share` as the exposure for retail food and OWTS as
well as county land-use permitting. That generalization is false. LA County's
well-approval page explicitly covers wells across the county except Long Beach,
Pasadena and Vernon. Its environmental-health contact page describes work
throughout the county with those independent departments distinguished. Housing
has further contract/code-adoption boundaries. [Official well program](https://publichealth.lacounty.gov/eh/safety/state-small-water-systems-wells.htm),
[official EH contact page](https://publichealth.lacounty.gov/eh/about/contact-us.htm),
[housing service-area explanation](https://admin.publichealth.lacounty.gov/EH/business/housing.htm).

The demographic column itself need not be wrong; its universal program
interpretation is. Use a verified program–administering-agency–service-area
crosswalk, including city contracts, rather than one countywide denominator
rule. Land-use boundaries do not automatically transfer to food or well permits,
and even population in the correct area is only a proxy for applicants or
facilities. The already retained Contra Costa report's discussion of county
services for cities reinforces the need to check delegation explicitly.
[Retained source/request records](../corpus/counties/raw/exhaustive_2026_09_17/la_program_jurisdiction_attempts.json).
