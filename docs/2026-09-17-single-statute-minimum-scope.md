# Scoping: one-statute completion and the token-ranked statute backlog

2026-09-17. Proposed completion plan, not a new render or a model result.
Requested by Alex after the W2 renderer reached its session limit.
This document scopes the work; it does not change the running selection,
partitions, truth, artifacts or other agents' workflows.

## 0. All statutes, ordered by estimated remaining token work

### How many statutes were we attempting?

**Twelve target statutes**, S01–S12, in the fictional State of Marisol.
There are also **twelve neighboring-state look-alike statutes**, C01–C12,
used as distractors: **24 modeled statutes in total**, not 24 target programs.
This is separate from the broader real-source scoping program-family list.

The [current world counts](../benchmark/synth/worlds/W2_DEV_001/counts.json)
confirm 12 Marisol statutes, 24 total and 24,442 specifications. Older prose
reports 24,868 specifications; that is an earlier build, not the current count.

None of the twelve target statutes is finished. The ranking below covers all
twelve, not just the ones in the interrupted render's next batches.

### Completion boundary and estimate meaning

For the main table, “full” means **every existing target document for that
statute in the 58-county panel**, including **all planted user threads**,
existing state-level documents, direct shared-page dependencies and department
directories for the modeled implementing counties. There is no 20-county limit
or four-thread cap. Legacy J/K jurisdictions, unrelated filler, full recursive
web expansion and separate look-alike process corpora are excluded explicitly.

Not every statute has 58 implementations. Completing S12's 15 modeled county
implementations is not the same achievement as S11's 58. Do not invent the
other 43 implementations, or label absent documents proof of nonimplementation.
A full 58-county applicability/negative-case experiment needs a separately
verified applicability/public-evidence design; it is not included by silently
filling these rows.

“End-to-end” budgets completion of the existing development corpus, verification,
one extraction/reconciliation pipeline, a bounded semantic-calibration allowance,
three matched-source LLM baseline runs and a domain scoping/release allowance.
It does **not** mean the code gaps listed below have already been fixed, or that
a valid reserved-world comparison has already been funded. Shared engineering
and any fresh reserved world are separate below.

**These are planning estimates, not metered usage.** M means one million
input-plus-output token equivalents across calls, not unique corpus tokens.
Existing logs record words/verdicts, not actual input, output or reasoning-token
usage. Ranges are deliberately broad; they are not statistical confidence
intervals or hard upper bounds. Nearby ranks can readily swap.

### Full, unthinned completion ranking

| Rank | Target statute | County implementations | Documents: total / still to render | Render + verify, M tokens | End-to-end central, M | Planning range, M |
|---:|---|---:|---:|---:|---:|---:|
| 1 | S12 — Local contractor registration | 15/58 | 891 / 875 | 15.6 | 24.8 | 14.9–49.6 |
| 2 | S03 — Sidewalk vending | 21/58 | 951 / 943 | 16.6 | 26.5 | 15.9–53.0 |
| 3 | S05 — Home-based business permits | 30/58 | 1,391 / 1,357 | 23.5 | 37.8 | 22.7–75.6 |
| 4 | S04 — Protected-tree permits | 28/58 | 1,387 / 1,362 | 23.9 | 38.2 | 22.9–76.4 |
| 5 | S01 — Unpermitted dwelling-unit legalization | 30/58 | 1,427 / 1,396 | 24.7 | 39.4 | 23.6–78.8 |
| 6 | S09 — Domestic-fowl permits | 24/58 | 1,521 / 1,508 | 25.8 | 41.5 | 24.9–83.0 |
| 7 | S02 — Short-term rental registration | 35/58 | 1,561 / 1,527 | 27.0 | 43.1 | 25.9–86.3 |
| 8 | S10 — Special-event permits | 38/58 | 1,709 / 1,669 | 29.7 | 47.3 | 28.4–94.7 |
| 9 | S11 — Water-well construction permits | 58/58 | 2,261 / 2,209 | 37.9 | 61.3 | 36.8–122.5 |
| 10 | S06 — Mobile food facilities | 58/58 | 2,429 / 2,370 | 41.3 | 66.2 | 39.7–132.5 |
| 11 | S08 — Rental housing habitability inspections | 58/58 | 2,427 / 2,377 | 42.6 | 67.6 | 40.6–135.3 |
| 12 | S07 — Residential solar permits | 57/58 | 2,526 / 2,465 | 43.0 | 69.0 | 41.4–138.1 |

The twelve standalone bundles overlap. Their union contains **19,398 distinct
documents**, of which **237 currently exist** and **19,161 need rendering**.
There are **16,560 target forum/thread documents** across these county programs.
That is why a full unthinned budget is much larger than the current
3,543-document selection.

Do not sum standalone rows as an exact portfolio budget: 1,083 document
memberships repeat across bundles, and shared extraction/engineering can be
reused. Baseline and reconciliation work also depend on whether each program
reads its context separately.

### Compact alternative: four threads per county

This is the same budget-sampled design as the S11 recommendation below, applied
to each statute. All non-forum core documents and required context remain.
These are not complete natural-volume corpora. The lexical-first-four sets are
inventory proxies, not the final randomized selection.

| Statute (same full-budget ordering) | Compact documents | Still to render | End-to-end central, M tokens |
|---|---:|---:|---:|
| S12 | 186 | 170 | 4.0 |
| S03 | 266 | 258 | 5.8 |
| S05 | 353 | 319 | 7.4 |
| S04 | 342 | 317 | 7.4 |
| S01 | 350 | 319 | 7.4 |
| S09 | 305 | 292 | 6.5 |
| S02 | 409 | 375 | 8.9 |
| S10 | 464 | 424 | 9.9 |
| S11 | 664 | 612 | 13.8 |
| S06 | 725 | 666 | 15.2 |
| S08 | 672 | 622 | 14.6 |
| S07 | 709 | 648 | 14.9 |

The same 0.6×–2.0× planning range applies to compact central estimates.
For S11 that is approximately **8.3–27.7 M** tokens, with **13.8 M** central,
before shared engineering. **S12 is cheapest overall; S11 is cheapest among
the statutes that already have all 58 county implementations.**
S06 and S08 are the other full-58 options.

### How the token estimates were constructed

The [machine-readable estimate snapshot](scoping/2026-09-17-statute-completion-estimates.json)
contains exact counts, per-phase estimates, assumptions and input hashes.

For each document, use its specification rather than a single flat cost:

- **Input proxy:** serialized packet/specification characters divided by four.
  Renderer inputs remove private persona timelines using the current
  `prepare_batch.py` projection. Verifiers receive the full permitted spec.
- **Text output proxy:** 1.5 tokens per word, using the midpoint of
  `style.length_words`, plus 60 words per forum reply and 100 header tokens.
  Existing document character counts replace this proxy where text is present.
  The reply allowance follows the existing batch size estimator, not a measured
  promise about final thread length.
- **Amortized context:** 800 tokens/document for rendering and 1,050 for
  verification. Prepared packets gave median character-based proxies of 798.5
  across 18 render packets and 1,052 across eight verify packets. The latter
  are backlog packets, not a representative target-only calibration sample.
- **Render:** sanitized spec + context + output, only for missing artifacts.
- **Verify:** full spec + context + text + a verdict allowance of
  `250 + 100 × required-reveal count`. Count top-level and comment reveals.
  Budget fresh verification for every released artifact until existing passes
  can be tied to its exact current bytes. Only 30 detailed verifier files were
  found despite 1,226 latest verdict records; log presence is not a complete
  claim-span/hash audit.
- **Extraction:** one text read plus 800 prompt tokens, an evidence output
  allowance of 60% of text size plus 300 tokens/document.
- **Reconciliation:** one evidence-ledger read plus 6,000 tokens per modeled
  county implementation. This requires chunking/reconciliation work for large
  cells; the current whole-program reader is not an unlimited-context solution.
- **Baselines:** three full text reads plus a combined 6,000 tokens per county
  for prompts and outputs. Fair context/chunking budgets must be frozen.
- **Calibration:** add 25% of extraction plus reconciliation work for a bounded
  repeated-reading/adjudication pass. This is a budget allowance, not proof of
  enough labels for every ambiguity class.
- **Repairs/retries:** add 20% to render/verify and downstream LLM phases.
  This is an assumption; revise from the pilot instead of interpreting today's
  two unresolved failures as the historical failure rate.
- **Domain scoping and release review:** add 0.1 M per standalone statute.
  Also an allocation, not a measured prediction.
- **Uncertainty range:** 0.6×–2.0× the central total. Hidden reasoning,
  tool/context rereads, changed truth, and persistent failures can exceed it.
  Prompt caching may reduce monetary cost without reducing this token-work
  count. No subscription quota, dollar price or wall-clock conversion is implied.

The snapshot does not credit an existing pass as hash-bound certification.
Confirmed reuse can lower the budget; material semantic/resource changes can
require rerendering documents counted as reusable today.

### All known remaining steps, with cost treatment

Every statute inherits this checklist. Rendering the missing Markdown files
alone does not complete the experiment.

| Step | Missing work / acceptance condition | Cost treatment |
|---|---|---|
| A — scope and empirical anchors | Freeze exact program, authority, case types and clock definitions; review representative cached sources; label unsupported timing/labor assumptions; reconcile source versions | 0.1 M per-statute allocation plus bounded human/source review; expand explicitly if insufficient |
| B — generator and burden contract | Close activity/actor/clock issues; generate payer and agency effort separately from elapsed time; retain fees, conditional routes, repeats, censoring and outcomes; license observations without truth leakage | Shared engineering reserve; simulation is CPU/disk work, not LLM tokens |
| C — observation metadata | Stable case/cohort/lineage IDs, units, endpoints, visit basis, sample sizes and publication/reachability states; finite-sample aggregates are not exact population parameters | Shared engineering; affects render/verify packets |
| D — release/split manifest | Immutable source allowlist and hashes, dependency boundary, selected-versus-planted counts, provenance and partition policy; isolate public text from truth | Shared engineering; do not rewrite existing W2 partitions |
| E — pilot and budgeting | Six-county compact pilot, independent checks, actual per-stage token/latency/retry measurements; resolve inconsistent verifier rules before expansion | Included as reusable corpus work where compatible; redo costs belong to retry allowance |
| F — render all missing artifacts | Resume per artifact with frozen batch membership; validate nontruncation; targets and required context first | Render column |
| G — verify, repair and verify again | Complete required-claim/span and forbidden-fact checks; every final pass references current artifact bytes; retain rejected originals and all repair attempts | Verify column plus retry allowance |
| H — source-only extraction/reconciliation | Artifact-only parser; complete source index; scalable chunking; semantic step merges, actor identities, case duplicates, contradictions and unknown dependencies | Extraction/reconciliation estimate; shared compiler work still needed |
| I — semantic calibration | Designated development/calibration labels only; classwise top-reading accuracy and uncertainty, calibrated candidate mixtures where justified; no treating K votes as independent labels | 25% allowance; insufficient cells must remain explicit rather than declared calibrated |
| J — V6 compilation/support | Finish source-derived route/count/resource bridge; preserve unsupported finite-cohort, selected-population, monetary and outcome claims in a coverage ledger; do not delete denominators to make a likelihood accept them | Shared engineering; not secretly assumed complete in token table |
| K — inference and identification | Resource preflight, independent chains, Monte Carlo/integration checks, posterior predictive checks, prior sensitivity and observed actor–task identification | Primarily local CPU/RAM/disk; no defensible run-time estimate until the pilot |
| L — matched comparisons | Same released information for V6, simple pooling controls and three LLM repetitions; frozen endpoints, counts and proper interval scores; retain bad/failed runs | Three LLM passes included; statistical fits/scoring are CPU work |
| M — release report and retention | All 58 selected county bundles complete where the statute has 58 implementations; all verdicts pass with hashes; coverage, assumptions and methods linked; follow existing retention policy | Domain release allowance; no external archive or deletion authorized |
| N — genuinely held-out validation | Freeze the pipeline, then generate a fresh, uninspected world/partition and repeat the required corpus/inference comparison; current W2 is development data | **Additional**, not included in the main row; requires a separately sized fresh-corpus budget |
| O — cross-program agency transfer | A real donor program sharing an agency, observed overlapping tasks and held-out target evidence | **Additional hypothesis**, impossible to certify from one-statute completion alone |

**Shared engineering reserve:** allocate **0.5–2.0 M** coding/audit token
equivalents once (central 1.0 M), not once per statute, for B–D/H/J and the
release machinery. This is a management allowance for known gaps, not an
empirical estimate or a guarantee; a six-county preflight must re-budget it.
Human review, CPU time, storage and unavailable empirical evidence cannot be
reduced to an honest LLM-token count.

For a fresh same-sized reserved world, no existing artifact render can be
credited. Its specification/length profile and calibrated protocol must be
counted afresh. Do not call the main table the cost of a publishable generalization
claim and hide that second corpus. Likewise a complete one-statute benchmark
cannot claim cross-program transfer without step O.

### Domain-specific work still needed, in the same priority order

These are scoping/contract checks to close, not claims that every listed issue
is a demonstrated defect in the current implementation. Program-specific real
timing and labor calibration has not been established merely by generating
plausible documents.

| Statute | Additional domain-specific checks still to close |
|---|---|
| S12 | Separate state licensing from local registration, issuance from renewal, and insurance checks from registration decisions; find/qualify program-specific timing and work estimates. |
| S03 | Resolve county/city authority, food versus non-food routes, and the boundary between vending authorization and a separate health permit; do not count one requirement twice. |
| S05 | Separate home-occupation/zoning clearance, business licensing and enforcement; qualify any timing/effort anchors rather than borrowing a generic permit average. |
| S04 | Separate arborist/third-party reports, agency inspection, permit decision, work and appeal; preserve conditional protections and tree/parcel scope. |
| S01 | Separate legalization of an existing unit from new-ADU construction; retain pre-filing preparation, inspections, corrections and post-decision work as distinct clocks. |
| S09 | Confirm when a permit is required at all, household/flock thresholds, local additions and enforcement; do not turn sparse evidence into zero burden. |
| S02 | Separate initial registration, renewals, safety inspections, tax obligations and enforcement; resolve owner/operator roles and authority across jurisdictions. |
| S10 | Keep advance filing requirements separate from agency turnaround; distinguish coordinated review, event-day services and appeal, including conditional agencies. |
| S11 | Resolve service-area authority, issuance versus seal inspection/completion reporting, the 30/60-day source-version example and conditional public-water referrals; add honest labor truth. |
| S06 | Distinguish initial plan review, operating approval, renewal, commissary and fire/location permissions; scope contractor/vendor work separately from agency review. |
| S08 | Separate registration/inspection cycles, notice, correction, reinspection and enforcement; identify whether the payer is owner, operator or tenant for each claim. |
| S07 | Separate application/plan review, permit issuance, installation, inspection and utility authorization; do not assign installation or utility delay to county staff. |

The first receiving agent should complete A–D for the chosen statute, produce
the frozen artifact list, and measure E. It should not launch the entire
unthinned portfolio merely because this document now prices it.


## Recommendation

Finish **S11, the fictional Water Well Standards and Permitting Act**, across
**all 58 synthetic counties**, using the existing generator and retained real
sources. Do not finish all twelve statutes first.

The minimum additional *research* is a bounded synthesis of material already
retrieved: eight representative county process sketches, an explicit
source-to-assumption register, and one limited search/review for unresolved
timing and labor evidence. The minimum *rendering* package is approximately
**664 documents** using the current specifications and a four-thread-per-county
sample. These are different kinds of work.

This would be an **empirically informed, budget-sampled synthetic environment**,
not a reproduction of every real county or an empirically calibrated model of
all well-permit durations. Completing exhaustive real-world retrieval is not a
prerequisite. Unsupported numerical assumptions must remain visible.

## 1. What the current files actually contain

Read-only count at 12:05 PDT, September 17:

| Current W2 selection | Selected | Rendered | Latest passing verdict |
|---|---:|---:|---:|
| Target documents | 1,718 | 217 | 6 |
| Structured distractors | 1,505 | 1,505 | 1,131 |
| Filler | 320 | 320 | 87 |
| Total | 3,543 | 2,042 | 1,224 |

There are 1,501 missing documents, 816 rendered documents without a verdict,
and two with failing latest verdicts. `observed.complete_by_counts` is false;
the last write was about 129 minutes earlier. The label `in_progress` is stale.

The [current manifest](../benchmark/synth/worlds/W2_DEV_001/render_manifest.json)
selects **20 counties**, leaving **38 spec-only**. None of the twelve statutes
is completely rendered and verified over even its selected county scope.
Finishing that queue would not deliver a 58-county text benchmark.

The current queue prioritizes S12, contractor registration. That is a small
rendering lane, but its county-specific specifications cover only 15 counties.
S06, S08 and S11 each have county-specific specifications for all 58. S11 is
recommended because we also have substantial retained, reviewed well-permit
material, including authority boundaries and source-version conflicts.

These are counts of specifications and artifacts, not claims that every real
California county operates the same well program. State-level contrast-law IDs
also use `Cxx`; release membership must use document metadata, not a bare
county-prefix match.

## 2. The minimal real-world scoping package

**Eight sketches is a pragmatic coverage target, not a statistical sample-size
guarantee.** Choose them for size, rurality, authority and publication variation,
before inspecting model performance. Start from the cache, not another sweep.

| Deliverable | Minimum useful content | Existing starting point |
|---|---|---|
| Law/process boundary | One dated account separating state constraints, local choices, permit issuance, construction inspection and completion reporting; identify conditional routes | S11 definition in [domains.py](../benchmark/synth/generator/domains.py); retained well sources |
| Eight county sketches | Roughly 2–3 genuinely informative documents per county, or a shorter complete packet; responsible authority, payer actions, agency tasks, dependencies, fees and clock meanings | [Environmental-health inventory](scoping/2026-09-16-county-environmental-health-58.md) already records 16 counties with actual well instructions read |
| Authority/variation table | Use the existing 58-row authority inventory; deeply verify the eight sketches, leaving other entries' uncertainty explicit | County EH, Public Works, city and water-district boundaries in the inventory and [well follow-up](scoping/2026-09-17-well-primary-followup.md) |
| Timing/effort evidence register | Separate realized durations, policy deadlines, advance notice, forecasts, active work, billing standards and costs; record missing empirical support | [Well follow-up](scoping/2026-09-17-well-primary-followup.md), [permit labor sources](scoping/2026-09-16-permit-labor-target.md) |
| Publication/selection examples | At least one sparse-source county, one rich-source county, a portal/access failure, copied material and a same-case follow-up; these illustrate mechanisms, not their population frequencies | Existing forum cache, well source conflicts, [source-volume register](2026-09-16-source-volume-register.md) |
| Frozen assumption register | For every numerical generator setting: source, vintage, quantity, uncertainty and label: measured anchor, derived with assumptions, or design assumption | Existing capacity provenance and [generation plan](2026-09-16-synthetic-corpus-generation-plan.md) |

Candidate sketch counties are Inyo, Colusa, Butte, El Dorado, Sonoma, Alameda,
Los Angeles and San Diego. Confirm readable, relevant cached material before
freezing this list. If one packet is unusable, record the reason and replace it
by a predeclared coverage criterion, not by how well the model fits.

Important already-known examples to carry forward:

- El Dorado's linked forms disagree on a 30- versus 60-day completion-report
  deadline. That is a source-version conflict, not a 45-day processing mean.
- Alameda's service area can change the responsible authority. A county name
  does not identify one universal county agency.
- Butte's issued/finaled counts are not a linked cohort and contain an internal
  count conflict. They do not establish elapsed time.
- A well-drilling duration, a contractor quote, a notice period and a permit
  processing duration are different quantities.
- Environmental-health cost studies mix records, adjusted estimates, expert
  standards and overhead. Neither fee/rate division nor a consultant budget
  is automatically observed agency labor.

### Stop rule for additional retrieval

Allocate **at most four focused hours** to unresolved source gaps after the
cached review: first the relevant legal/version boundary, then well-specific
realized timing and labor definitions. This is a proposed effort cap, not a
promise that evidence exists. No new all-program or all-county forum sweep.

If a gap remains, record it and proceed only with the weaker, explicit claim:
the mechanism is source-informed but its numerical distribution is assumed.
Do not borrow ADU, food-permit or benefits durations and label them measured
well-permit times. General source-volume estimates also need program-scope
qualification; keyword matches are not verified timing claims.

The scoping package is done when every required variable has either an
appropriate source or an explicit assumption/unknown designation. It is not
done merely because eight folders contain downloads.

## 3. Exact size of the proposed source bundle

Metadata-only inventory of the existing S11 specifications:

| Component | Documents |
|---|---:|
| County-specific non-forum S11 documents | 337 |
| Existing state S11 statute text | 1 |
| Up to four existing forum/Reddit threads per county | 167 |
| Directly referenced shared permit pages and fee schedules | 101 |
| County department directories for actor reconciliation | 58 |
| **Compact bundle** | **664** |

There are 3–9 non-forum S11 documents per county. Ten counties have no planted
S11 user threads; preserve those zeros. The specifications include 13
county official-statistics documents, eight SOPs and seven audit excerpts.
These are document counts, not independent cases or guarantees of labor data.

For a lexical-first-four inventory proxy, 52 of these 664 artifacts already
exist and 20 have passing verdict records: **612 still need rendering**.
The final selection must be frozen by a seeded, outcome-blind thread sample;
reuse and dependency counts must then be recomputed. Do not select threads
because their hidden timelines are informative or their extraction is easy.
The 664 count is an inventory estimate before semantic fixes, not a released
manifest. Existing passes also need artifact-hash freshness verification.

There is no S11 bill-analysis specification in the inspected world. Do not
invent one merely to fill a standard document checklist.

Keep required S11 links and public actor/fee context. Shared pages link to other
programs too; recursively expanding all such links would undo the scope cut.
For this milestone release a **bounded document bundle**, not an allegedly
complete mock web. Record external/out-of-scope link destinations in a boundary
manifest. Same-S11 links and necessary authority context must resolve. If open
web navigation is tested later, give both methods the same declared boundary.

The other 57 counties already provide same-statute retrieval distractors.
No new unrelated filler or twelve-domain distractor corpus is needed.
Existing contrast-state material can be an explicitly separate stress condition.

### What the four-thread cap changes

It is a budgeted observation design, not the natural distribution of posts.
Keep planted, selected, rendered and readable counts separate. Do not claim
the capped public bundle reproduces the original population/volume gradient,
and do not interpret omitted threads as nonpublication.

Keeping all existing S11 user threads instead would give **2,261 documents**:
2,102 core documents, 101 shared dependencies and 58 directories. This
unthinned option is appropriate only if native evidence-volume scaling itself
is the primary experiment. It is not necessary for a first text-to-burden
completion milestone. Four threads likewise do not guarantee four cases or
four informative timing observations.

Inventory provenance: current render-selection SHA-256
`cae2b2b2baff2f96fcca7cd15b5d60f0199d5eb5d5dbcf8be65856c6e71524fd`;
manifest SHA-256
`65036ff0452f9615bce15c6af5a3072d0f4691c04ced8c9b5ac35a465873b065`.
Counts were derived from specification identity/type/link metadata and artifact
presence/latest verdicts, not fitted outcomes. No case truth was used to choose
this recommendation.

## 4. Preserve the whole burden question, but bound the claims

The environment must distinguish:

- Elapsed time to initial decision, subsequent decision and post-issuance
  completion; pending/withdrawn/denied cases retain their own endpoints.
- Unique activities versus executed visits, rework, payer touchpoints and
  distinct responsible agencies.
- Payer active hours, agency active hours and third-party work.
- Fees and other monetary costs, without adding dollars, days and agency counts
  into an unexplained single burden number.
- Local interpretation, conditional agency involvement, missing evidence,
  conflicting versions, copying and uncertain case identity.

**The present W2 rendering is not already a complete labor benchmark.**
Inspection of `generator/simulate.py` shows event paths, elapsed clocks, fees
and repeats, but not separately simulated payer-hours/agency-hours channels.
Do not claim an hours recovery test by feeding elapsed time into those slots.

Before a full-burden release, add versioned per-visit effort truth and a small,
explicit observation mechanism in the existing generator. Keep it separate
from elapsed service/waiting; resource effort may be correlated with route and
case difficulty without being identical to calendar duration. Only publish
hours where the source design permits them. Numeric labor assumptions must
remain assumptions unless the well-specific evidence supports them.

This need not create hundreds more documents: selected existing SOP, audit and
case-report specifications can carry properly licensed effort claims, with
new hashes and independent verification. Do not silently amend W2 artifacts.
If the effort extension is deferred, call the release **elapsed/count/actor
development corpus**, not a completed full-burden environment.

Do not manufacture a time study in every county to make agency parameters
identifiable. If a separate dense-labor diagnostic is useful, label it as
controlled evidence enrichment, not the naturally observed corpus.

### What one statute can and cannot establish

It can test source reconciliation, uncertainty calibration, county-level
partial pooling, missing-data behavior and step/agency/rework recovery.

It cannot by itself demonstrate **cross-program agency transfer**. With one
dominant agency per county, an agency effect and a county effect may be
confounded. Repeated observations of overlapping task types can help within
the program, but 58 counties do not automatically identify intrinsic agency
delay, task effects and source bias separately. Report identifiable
combinations and prior-sensitive blocks, not 58 precise agency rankings.

A donor program using the same agency is a later, specifically scoped
extension if transfer is the next hypothesis. It is not a prerequisite for
finishing this one-statute environment.

## 5. Execution order and hard completion gates

1. **Freeze the scope, without altering the old run.** Record parent world,
   code/source hashes and the chosen S11 definition. Create a separate
   development release manifest, tentatively `W2_S11_DEV_001`. This is a
   dataset identity, not a new model architecture. Preserve all existing W2
   artifacts, partitions, rejected versions and logs. Do not rebuild W2 in place.

2. **Finish the bounded scoping package and contract check.** Produce the
   eight sketches and assumption register. Resolve issuance versus
   post-issuance clocks, optional health/public-water-system referrals and
   agency identities before mass rendering. Audit claim operators and
   resource availability; add/version effort truth if claiming full burden.
   Any change to facts invalidates affected old text/verdicts.

3. **Freeze a small rendering pilot.** Use six counties spanning evidence and
   authority patterns, selected by design metadata rather than truth outcomes.
   Include ordinary cases, sparse disclosure, rework/censoring, a copied claim
   and a conflicting source where the specifications actually provide them.
   Render their complete selected bundles, independently verify every artifact,
   then measure tokens, retries and wall time. Do not promise a full-run time
   or subscription cost from document count alone.

4. **Finish the 58-county bundle.** Render targets and their dependencies first;
   render no new unrelated filler. Use the existing renderer/verifier path with
   immutable batch manifests and a disk-derived missing-work queue. Reuse only
   byte-compatible, provenance-verified artifacts. A stopped session must resume
   missing work rather than rebuilding completed batches.

5. **Release only after the stronger gate.** Every selected artifact exists,
   is nontruncated and has a passing independent verdict tied to its current
   hash; all required links/authority context resolve or have declared boundaries;
   all 58 counties have their full selected bundle. Retain failures and repairs.
   Report generated/published/selected/rendered/reachable separately.
   `complete_by_counts` alone is insufficient because it permits failing
   verdicts. Do not treat the old world's global status as this slice's status.

6. **Then parse and fit.** Spawn the previously requested parser with no
   conversation history and an artifact-only allowlist. It receives no generator
   specs, verifier explanations, case truth or scores. Follow the existing
   [V6 handoff](scoping/2026-09-17-w2-v6-handoff.md): the route/count/resource
   compiler bridge and unsupported cohort/selection operators remain real work.
   Corpus completion is not equivalent to an end-to-end V6 run.

Use current county memberships as provenance, not as proof of valid held-out
evaluation. The saved 20-county split is population-blocked, and W2_DEV_001
has already been inspected during construction. This slice remains development
data. Do not silently reassign its partitions or call its unrendered counties
pristine holdout data. A genuinely fresh reserved world comes after the
one-statute pipeline is frozen.

## 6. Minimal evaluation and handoff

For the development milestone, compare V6, a simple pooled/partially pooled
control and the LLM baseline on the **same released source bundle**. Separate
oracle-input mechanics diagnostics from source-only extraction results.
Predeclare clocks and completed-case versus all-case estimands. Retain unsupported
claims in coverage reporting; do not remove denominators to force model support.

Report proper interval scores/coverage, clock-matched predictive error,
inventory/count/actor errors, informative-versus-residual claim coverage, and
sensitivity to priors and source dependence. Do not keep extending the corpus
until Bayesian point accuracy wins. Learned ambiguity mixtures require actual
calibration evidence; eight real sketches are not a substitute for a semantic
confusion-matrix calibration set.

Handoff artifacts, preferably under one release directory rather than new
standalone drivers:

- Eight-sketch report and source/assumption register.
- Frozen release configuration, artifact allowlist and link-boundary manifest.
- Private event/resource truth and public text, kept access-separated.
- Hash-bound verification/rejection records and resume state.
- Coverage/quality report, including unsupported channels and prior-sensitive
  quantities.
- A fixed, matched-information development comparison protocol.

**Not required to finish:** exhaustive Reddit coverage; all twelve statutes;
a new Bayesian architecture; learning every hierarchy coordinate; a new
compute cluster; or proving a Bayesian advantage before release.

**Bottom line:** stop expanding retrieval for this milestone, finish the
eight-sketch synthesis, resolve the explicit timing/labor contract gaps, and
complete one approximately 664-document, 58-county development bundle. More
research is warranted only for a named unresolved variable, not because the
rest of the repository still has open scoping packets.
