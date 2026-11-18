# PLAN: generating the next synthetic process corpus

2026-09-16. Handoff for the implementation agent, requested by Alex after the
county retrieval and audit passes. **This is a proposed execution plan, not a
record of a generated W2 corpus.** It incorporates the findings below and keeps
W1's backwards-generation workflow: construct truth, simulate cases, decide
what becomes public, render documents, independently verify them, then expose a
mock web to the systems being evaluated.

The deliverable is a reusable corpus for measuring recovery of **process
structure, elapsed time, payer effort, agency effort, institutional effects and
uncertainty** from heterogeneous documents. It is not a world constructed to
make Bayesian inference win. V6 remains the integration target; building this
corpus does not require another competing inference architecture.

## 1. What we need to demonstrate

There are three different questions, and they need different experiments:

1. **Mechanics:** Can the simulator, observation operators, compiler and scorer
   agree on a known case, including repeat visits, parallel work, multiple
   agencies, partial observation and contradictory reports?
2. **Information and scale:** As independent cases, programs, agencies and source
   families increase, what becomes learnable? Where does uncertainty correctly
   remain broad? Can evidence about shared agencies help a sparsely documented
   program without confusing agency effects with task mix?
3. **Text-to-posterior performance:** Given the same available documents, does a
   Bayesian system improve calibrated predictions or replication over LLM and
   simpler pooling controls? A tie on a well-documented program is acceptable.

The corpus must support all three. A successful oracle-data fit establishes
mechanics, **not** extraction accuracy, realistic transfer or superiority over an
LLM. More rendered pages are not necessarily more independent information.

## 2. Starting point and precedence

Read these first:

- [Existing synthetic design](../benchmark/synth/DESIGN.md),
  [generator map](../benchmark/synth/generator/README.md), and
  [render workflow](../benchmark/synth/render/README.md).
- [County scale-up plan](2026-09-16-county-scale-up-plan.md) and
  [detailed W2 specification](2026-09-16-w2-generator-spec.md).
- [Retrieval handoff](scoping/2026-09-16-county-scale-execution.md),
  [cross-scoping audit](scoping/2026-09-16-cross-scoping-audit.md), and
  [P12 spot-check](scoping/2026-09-16-p12-independent-spotcheck.md).
- [Overnight audit](2026-09-16-bayesian-overnight-audit.md) and its
  [implementation/qualification report](2026-09-16-bayesian-audit-implementation.md).

The deterministic W1 generator, decision layer, event-clock/visit-accounting
additions, render packaging, verifier briefs and mock web exist. At the final
retrieval handoff, concurrent work in the shared tree also includes
`counties.py`, `capacity.py`, `lineage.py` and a `world_model_version` branch in
`world.py`. This retrieval pass has not validated that implementation against
this plan. The implementation agent should reconcile existing work with the
gates below, not start a duplicate
county generator or infer that file existence demonstrates a validated W2.
The [semantic-label bridge](scoping/2026-09-16-calibration-bridge.md) exercises
four decision-criterion classes with simulated extractor errors; it is not a
measured text-extractor calibration, and does not cover the full burden schema.

Use the detailed W2 spec as an implementation reference, with the corrections
and proposed scope changes in this plan made explicit in a small decision log.
Do not silently implement conflicting instructions from both documents.
Recheck the shared [findings log](scoping/FINDINGS.jsonl) before editing: other
agents may have fixed findings since this snapshot.

### Corrections that must precede a production render

| Earlier assumption or defect | Required treatment |
|---|---|
| RUCC ≥ 6 means noncore | Use the corrected USDA UIC classification for that concept; the audited real panel has 11 noncore counties, not 15. Preserve RUCC as a separate variable. |
| QCEW local-government employment measures county staffing | It includes other local governments. Keep its identity as a proxy; do not relabel it agency staffing or FTE. |
| All missing covariates in the W2 draft remain missing | Re-read current files and source reports. Unincorporated share, city counts, broadband and consortium labels have since been collected; budgets are not complete for every county. |
| A county's population/capacity determines its intrinsic speed or disclosure | These are hypotheses, not established causal estimates. Plant null, weak and alternative relationships; document their provenance. |
| APR begins at initial filing | Its defined application clock can begin at receipt of a complete application. Linkage and selected cohorts remain issues. |
| Every county must have a LAMP and publish a usable annual report | False. Separate program authority, lawful route, publication obligation, publication found and document accessibility. |
| Rental-inspection correction deadline has a legal maximum of 30 days | The current synthetic text instead states a minimum. Repair the bound direction separately from the applicant comparison, and review the two overlapping deadline predicates. |
| Predicted matches can determine the planted reading histogram | Gold populations and histograms must be constructed independently of predictions; missing predictions remain scored missingness. |
| Normalized distinct-reading count measures concentration at 58 counties | It can give a constant predictor a perfect contrast. Use frequency-sensitive distribution recovery and per-county accuracy; report both contrast components. |
| 38 spec-only counties provide measured extraction error or text-based transfer | They do not. They support generator/oracle experiments only. Text claims are restricted to rendered, verified evidence. |
| A planted spec alone verifies an extracted sentence-to-truth link | It verifies intended provenance, not successful rendering or extraction alignment. Add verified claim spans. |
| W2-learned hierarchy scales become empirical priors for real counties | Synthetic recovery validates a method under a simulation. Real-world scale priors need compatible real observations and uncertainty. |
| A single availability slope fits every source family | Measured slopes differ by more than 50%: reddit 0.75, administrative records 0.99, an administratively-created forum 1.16 (log-log on population). Use a per-family slope. |
| Channel existence and channel volume are one mechanism | The CalGuns forum assigned a thread to all 58 counties in one batch in October 2010, so existence carried no population signal while volume spanned three orders of magnitude, and three counties have a thread with zero replies. Separate hurdle from volume. |
| `V_DELAY = 0.55`: delay generates posts | Not supported. After controlling for population the delay coefficient is +0.076 with a ΔR² of 0.004, and it turns **negative** for timing-bearing posts. Default it to zero and carry 0.55 and a negative value as named scenarios. |
| `V_POP = 0.85` reproduces the population gradient | It implies a log-log slope of 0.539 against a measured 0.75–0.83, making rural counties look better supplied than they are. |
| Per-cell post counts are Poisson | They are strongly overdispersed: mean 39.6 against median 13. Poisson has variance equal to its mean and cannot produce that; use a Poisson-lognormal mixture. |
| A constant applicant count per process is fine at 58 counties | It is not. Real caseloads scale with population at a log-log slope of 0.989, and a flat caseload also truncates the user-evidence gradient, because a post has to come from a case. |

Do not delete visit accounting to save space, as the older W2 compact-log
proposal suggests. Visit index, charged fees and observation-time accounting are
necessary for repeat/count/labor checks. Compress losslessly or maintain an
explicit complete private archive and a documented projection.

## 3. Convert the retrieval findings into an evidence design

> **Implemented, 2026-09-16.** The numeric half of this register now exists:
> [How much data each real channel actually yields](2026-09-16-source-volume-register.md),
> built by `pipeline/recon/source_volume.py`. It supplies the rates this section
> asks for, corrects our own reddit count (the previously reported 16,037 posts
> was an inflated sum of per-query rows; the true distinct count is **4,998**),
> and flags two W2 spec coefficients the data contradicts. The coefficients
> themselves live in `benchmark/synth/generator/capacity.py`, each tagged with
> one of the three provenance labels below, and
> `pipeline/procbench/audit_corpus_anchors.py` checks a built corpus against
> them. Read that document together with the qualitative table here: this
> section states what must not be inferred, that one states the measured rates.

Create a versioned **source-to-design register** before coding new coefficients.
Each entry records source path/hash, jurisdiction, period, observed unit,
clock/statistic/cohort, evidence state, selection, source lineage, limitations,
and its allowed synthetic use. Mark every numeric setting as `measured_anchor`,
`derived_with_assumptions`, or `design_assumption`. An estimated reporting mean
is not automatically the latent population mean to plant.

This table is the required coverage checklist for that register:

| Findings and source report | What the corpus should reproduce | What it must not infer |
|---|---|---|
| [APR timing and linkage audit](scoping/2026-09-16-cross-scoping-audit.md) | Distinct completeness, entitlement and permit clocks; project/parcel mismatch; ambiguous links; selected completed cohorts | Initial application time, route identity or a causal county effect from a date difference alone |
| [CalFresh](scoping/2026-09-16-calfresh-58-counties.md) | Approval means, issuance bins, discovery-start expedited clocks, county-error attribution, form revisions, suppressed/error cells | One interchangeable duration for all fields; population-weighted statewide means without checking the method |
| [ADU process documents](scoping/2026-09-16-adu-58-counties.md) | Local requirements, versioned ordinances, separate departments, variation in source depth | 58 inventory rows = 58 verified operative processes; an unincorporated SF process |
| [Environmental health](scoping/2026-09-16-county-environmental-health-58.md) | Septic route differences, delegated/district authority, food plan checks and inspection outcomes, incomplete currentness | A guaranteed LAMP, county-only authority everywhere, or measured rural evidence superiority |
| [CCW](scoping/2026-09-16-ccw-remaining-43-counties.md) | Vendor boilerplate plus local overrides; optional evaluations; training/referral/payment stages; city versus county issuers | Silence means no extra step; all fees include training; all stated clocks are observed waits |
| [General Assistance](scoping/2026-09-16-general-assistance-58-counties.md) | Thin official descriptions, copied policy lineage, bounded choices, local grant/loan distinctions and missing amounts | A universal cap without exceptions, or a proven causal explanation for disclosure differences |
| [Forums and other venues](scoping/2026-09-16-forums-beyond-reddit.md) | Family-specific channel existence, volume, complaints, staff perspectives, oversight reports, shared templates and blocked retrieval | A readable county site has no relevant page anywhere; report existence guarantees relevant topic coverage; access failure measures nonpublication |
| [Other-program sweep](scoping/2026-09-16-other-58-county-statutes-sweep.md) | Renewal aggregates, platform lineage, child-support performance, pesticide workload and elections as additional document/table patterns | Sweep rankings or inferred forum volume are validated effect sizes; every table is a burden-duration dataset |
| [IHSS timing](scoping/2026-09-16-ihss-timing-target.md) | Application→approval and approval→service as different stages; cases never served; historical versus current periods | Completed-case means describe everyone, or service waiting is agency labor |
| [Medi-Cal application timing](scoping/2026-09-16-medical-application-timing-target.md) | Defined 45/90-day channels, review samples and an inaccessible-but-known workbook | Numeric timing rows from a workbook that was not retrieved; a deadline as a measured mean |
| [Agency workload](scoping/2026-09-16-agency-workload-target.md), [methods detail](scoping/2026-09-16-workload-detail-target.md) | Historical CWS self-recorded work, differing staff roles and report/referral/case denominators, travel-conditioned summaries, time-allocation claims | CWS hours are IHSS hours; all-staff totals are primary-worker means; allocation costs are direct task time |
| [Permit labor studies](scoping/2026-09-16-permit-labor-target.md) | Recorded/edited time estimates, manager standards, travel/office labor, hourly rates and fee calculations as distinct channels | Fee divided by rate is automatically measured labor; a retainer is actual hours worked |
| [CalWORKs](scoping/2026-09-16-calworks-target.md) | Stocks/flows, denial reasons, suppression and signed adjustments | Counts provide pending ages; negative accounting adjustments are negative cases |
| [Assessment appeals](scoping/2026-09-16-assessment-appeals-target.md), [capacity extension](scoping/2026-09-16-appeals-capacity-target.md) | Filings/dispositions/backlogs, boards and hearing officers, staffing and workload, nonreporting and contradictory totals | One board equals one agency; raw nonreporter No/zero means absence; fiscal and assessment years coincide |
| [State hearings/complaints](scoping/2026-09-16-state-hearings-target.md) | Closed-case means, formal/informal routes, residence versus responsible jurisdiction, repeated publications and inconsistent revisions | County complaint ratios identify county processing times; annual and quarterly copies are independent evidence |
| [New wide-net sources](scoping/2026-09-16-wide-net-retrieval.md) | County permit event exports, duplicate IDs, anomalous date order, stale feeds, government-unit headcounts, department-review aggregates | A refreshed landing page implies fresh cases; headcounts equal FTE; overlapping review cohorts are independent |
| [Targeted user-evidence enrichment](scoping/2026-09-16-county-user-evidence-enrichment.md) | Mixed-county replies, same-case followups, separate approval/NOA/provider/payment clocks, city comparators, published interview estimates, worker-facing scripts and missing reply bodies | A county-name search result is relevant to every program; a forecast is a case duration; assigned care hours are administrative labor; a quote is a paid cost |

The existing Reddit sweep was substantial; enrichment is not a fresh broad
sweep. Its regional/statewide county-name queries reuse results under multiple
program labels without program-content filtering. **Do not use those summary
counts as calibrated program-by-county availability coefficients.** The N11
ledger separates reviewed examples from search yields and already-cached
comments. Thread participants can discuss different counties, renewals versus
new applications, and multiple cases by the same author. Preserve that structure
in rendered forums and require statement-level attribution. Include conditional
recipient/provider routes for IHSS without treating a single user's report as
a verified county-wide policy; care-service hour awards are not agency labor.

The newest downloads are not yet calibrated population estimates. In particular,
the Census individual-unit files supply full-/part-time **headcounts**,
not unit-level FTE. The downloaded 2022 census covers 57 California county-type
units plus San Francisco, separately classified as a municipality; the 2024
and 2025 samples each cover 41 county-type units plus San Francisco. Preserve
imputation flags and the source's warning against interpreting unit records as
validated individual-government time series. Sonoma's retrieved permit export has duplicate record IDs;
San Diego County's retrieved export has some issuance dates before opening and
old latest opening dates. These are useful observation defects to model, not
values to silently clean and treat as truth.

## 4. World and program scope

### Recommended scope change from the six-domain W2 draft

Keep **one** W2 world schema and generator. Use 58 fictional target county-like
jurisdictions and eight neighboring-state distractor jurisdictions. Preserve
real geography only as distributional inspiration; do not attach synthetic
burdens or inferred efficiency rankings to real county names.

Recommend a final **ten-family** corpus, introduced in stages, rather than
using the six existing mostly permit-like domains as substitutes for all the
benefits findings. This is a proposed revision to W2 §11.1; the first handoff
decision log should record it before implementation. Do not count variants of
the same program as ten independent programs.

| Family | Reuse/extension | Main experimental contribution |
|---|---|---|
| Housing permit/legalization | Extend existing unpermitted-unit template; keep new-construction and legalization routes distinct | Completeness, referrals, project linkage, discretionary route, multiple clocks |
| Food-facility/mobile-food approval | Extend existing mobile-food template | Plan check, inspection, correction, fees and operator effort |
| Well construction | Existing well domain | Site/technical review, third parties, conditional authority |
| Septic approval | New domain sharing EH tasks but distinct rules | Tier/route variation, plans, site evaluation and inspections |
| Nutrition-benefit eligibility | New CalFresh-like domain | Expedited/regular route, issuance versus approval, aggregate bins |
| Health-benefit eligibility/renewal | New Medi-Cal-like domain; renewal is a branch, not an independent agency | External verification, alternative clocks, automation and renewal status |
| County assistance | New GA-like domain, not a relabeled home-business permit | Sparse documents, bounded local policy, grants/loans and work obligations |
| Home-support enrollment | New IHSS-like domain | Assessment, authorization and finding service as separate stages |
| License with training/background review | New CCW-inspired administrative template with fictional rules | External checks, appointments, third-party training and local route choices |
| Assessment appeal | New domain | Filing, scheduling, hearing, disposition, backlog and multi-member bodies |

Retain other W1 domains as immutable historical controls or clearly labeled
distractors. Child support, pesticide administration, elections and state
hearings can inform observation patterns or a later extension; their discovery
does not make each a required new truth generator in this release.

### Pilot and identification requirements

Start with six fictional counties spanning size/evidence strata and five
families: housing, food, well, nutrition eligibility and health eligibility.
This exercises shared permitting/EH agencies and shared benefits agencies.
Add the other families only after the pilot's semantics and rendering pass.

County, agency, organizational unit, task type and process operation are
different identifiers. An agency is reused across programs; an operation is a
program-specific instance of a shared task type. Keep third-party providers
separate from county agencies, with service roles and authority explicit.

For agency-transfer targets, require multiple observed task types and evidence
from at least two donor programs where feasible. Check the **observed**
agency-by-task graph and likelihood information, not just a dense truth table.
There must be connected, overlapping cells and repeated independent cases.
Do not force implausible tasks into every agency merely to fill every matrix
cell. Isolated agencies remain deliberate non-identifiable controls.

Separate county effects from agency effects only where several agencies per
county and cross-program observations support it; impose declared centering
constraints. Otherwise score their identifiable sum. A larger county count
alone does not identify both components or an 'intrinsic agency delay'.

## 5. Truth and observation contracts

Extend existing schemas rather than create a second representation. Use stable
IDs and keyed RNG streams. Version behavior changes, preserve saved W1, and
write every new build to a fresh destination.

### Truth to generate

- **Rules:** statute skeleton, upper/lower bounds and exceptions, delegated
  choices, local additions, prior versions, policy lineage, criteria, routes and
  effective dates. An applicant threshold operator is separate from the legal
  constraint on the jurisdiction's chosen policy.
- **Structure:** operation inventory, task types, agency/org-chart membership,
  payer/third-party roles, conditional presence, dependencies, parallel branches,
  handoffs, rework and terminal states. No edge means unspecified evidence only
  in the *observed* graph; the simulator always has a defined schedule.
- **Case events:** arrival, initial submission, completeness, each visit's
  request/start/end, first decision, last decision, issuance/service start,
  closeout, withdrawal/abandonment and observation cutoff. Preserve calendars,
  business-day conversions and explicit censoring indicators.
- **Resources:** active payer hours, active agency hours by role, third-party
  effort, travel/appointments and charges by visit. Elapsed duration and active
  labor are generated separately, with declared dependence where appropriate.
  Waiting, calendar time and labor cannot be substituted for one another.
- **Counts:** unique operations, executed visits, correction events, distinct
  responsible agencies and payer touchpoints, with per-case versus standing
  administrative obligations distinguished. Repeated aliases do not create new
  steps; a board's membership does not create that many agencies.

Keep burden as a vector of time, effort, money and counts. Do not invent a
single burden total by adding hours, dollars and agencies. Any utility-weighted
index is an explicitly separate downstream analysis.

### Evidence to generate from that truth

Each numerical or structural claim needs an observation record, not just text:

`claim_id`, source family/lineage, case or cohort reference, affected process,
quantity, unit, statistic, start/end events, visit basis, actor assignment,
population/denominator, observation date, policy version, rounding, censoring,
selection, report error, and licensed semantic alternatives.

Support at least these report types:

| Type | Required distinction |
|---|---|
| Case duration or ongoing wait | Completed interval versus right-censored lower bound; first visit versus repeated span |
| Cohort mean/median/quantile | Which cases qualify, sample size, reporting period, statistic and overlap with other publications |
| Timing-bin or event count | Numerator, denominator, time origin, eligibility and whether categories exhaust the population |
| Snapshot/backlog or administrative adjustment | Stock versus flow, observed state versus latent eventual outcome, signed accounting corrections |
| Labor/time-study observation | Active hours, worker role, task/case/report denominator, sampling and adjustment method |
| Cost standard or fee calculation | Estimated/normative resource requirement versus observed labor; overhead and billing conventions |
| Rule/target/forecast | Not an observed duration; lawful maximum/minimum distinct from operational estimate |
| Structural statement | Existence, responsibility, ordering, optionality or identity; missing statement is not a negative fact |

For source dependencies, retain three separate links: **same underlying case**,
**same aggregate/cohort**, and **copied document/template**. Each creates a
different dependence. Repeating a statistic across a report, FAQ and newspaper
must not generate three independent measurements.

## 6. Generation mechanisms: realistic, but not fitted to the answer

Use a small, declared set of effects initially: task/channel location, agency
effect, program/operation deviations, case heterogeneity and repeat/outcome
mechanisms. Add interactions only for a specific benchmark question. Hierarchy
scales and disclosure coefficients are private planted truth with provenance,
not values available to the estimator.

Generate a schedule from dependencies and case routes. A parallel branch ends
at its join; sequential work adds. Corrections cannot start before the triggering
result exists. Repeated visits accrue their own time and applicable labor/fees;
base fees are not charged repeatedly. At the observation cutoff, future work,
fees and corrections are not reportable as completed observations.

Approval/denial, withdrawal, quiet abandonment and ongoing processing are
separate latent outcomes. A published pending status can mix those states when
withdrawal is unreported. Reporting errors should not rewrite the event truth.
Include case-mix and external-party delays so county means are not just agency
intercepts with decorative noise.

Implement three declared regimes with the same interfaces:

1. **Mechanics/reference:** simple known observation operators and a connected
   design; tests model recovery under compatible assumptions.
2. **Evidence-constrained:** sparse and overlapping reports, heterogeneous
   clocks, disclosure/access selection and source errors patterned after the
   retrievals. Parameters are anchored only to compatible real summaries.
3. **Misspecification:** held-out scenario families with alternative tails,
   bottlenecks, nonstationarity, source dependence or weak/absent sharing.
   Do not make every challenge exactly follow the fitted model's likelihood.

For proposed staffing/population/strictness/disclosure relationships, include
zero and alternative-sign sensitivity settings where the evidence does not
identify direction. Do not tune coefficients until a desired marginal
correlation or Bayesian advantage appears. Report simulation diagnostics across
seeds, with failures, rather than selecting a favorable world.

## 7. Visibility, reporting and the mock web

Generate these stages separately:

`process/case exists → source topic covered → claim reported → document published
→ indexed/linked → fetchable → text recoverable → claim extracted`.

The measured per-family rates are in
[the source-volume register](2026-09-16-source-volume-register.md) §3 and
implemented in `capacity.FUNNEL`. They are steep and they differ by family by a
factor of ten at the deepest stage — a directory row exists for 100% of
counties, instructions are readable for 28–34%, and the operative local policy
is establishable for 0% (wells), 3% (septic) and 12% (retail food). **Read them
as joint rates, not publication rates**: the packet that produced them spent
about one fetch per county-programme, so each is publication × indexing × our
own bounded search depth. That makes them the right calibration for what a
bounded solver finds and a lower bound on what is published.

Use per-source-family availability mechanisms. Official pages/forms, ordinances,
vendor portals, dashboards, oversight reports, staff reports, SOPs, user forums,
office reviews, news and third-party guides should not share one population
slope or one existence hurdle. Publication obligations do not guarantee a
relevant accessible report. Treat claimed rural advantages and venue slopes as
uncertain scenario inputs unless the retrieved sample supports estimation.

Include controlled versions of observed defects: wrong-body HTTP 200, redirect,
dead link, JS shell, scanned/OCR text, stale policy, rounded dates, omitted actor,
ambiguous clock, suppressed cell, erroneous zero, duplicate record, correction
notice, copied aggregate and delayed refresh. An inaccessible source may still
be indexed. Some sources have declared mirror/archive routes, not universal
access. Do not emulate live anti-bot circumvention.

Local vendor-template overrides and policy copying need separate lineage from
measurement copying. Two counties can share prose while genuinely having
different procedures; two publications can use different prose for the same
case. Include both.

Compute separate ceilings for information that is published, reachable,
text-recoverable and actually supplied in each evaluation condition. For
structural facts, a statute can reveal that a staff-only operation must exist
without disclosing its actor or duration. For continuous quantities, a noisy
claim does **not** reveal the latent parameter exactly: report evidence coverage
and an oracle-measurement reference, not a claim that the sample median is an
information-theoretic timing ceiling.

## 8. Render and verify as in W1, with a stronger provenance contract

The production sequence is:

1. Deterministically build statutes, local rules, org charts, processes and
   case logs in the private world bundle.
2. Apply observation/visibility mechanisms to create claims and artifact specs.
3. Build **allowlisted renderer packets**, containing only licensed public
   context and facts, plus style exemplars. Never provide full process truth,
   case truth, planted effects, private selection labels or reserved answers.
4. Render pages, forms, legal text, reports, tables and threads with the existing
   batch workflow. Extend style guides using retrieved document structures, not
   by transplanting real county names, actual applicant identities or whole
   copyrighted reports.
5. Save a private claim-span map: claim ID, rendered character offsets or stable
   table-cell location, quote, document hash, intended reading and truth link.
   A renderer's self-reported map is provisional until verified.
6. Independently verify required facts, fidelity, clock, denominator, visit
   basis, actors, policy version, contamination attribution and hidden-content
   leakage. Verify spans against the actual bytes. Unsupported precision is a
   failure even when the numerical value is plausible.
7. Re-render failures with narrow feedback; preserve every attempt and rejection.
   Do not silently remove difficult artifacts or loosen the spec to pass them.
8. Freeze passing artifacts and build the mock web from **only** their public
   bodies, ordinary public metadata and links. Keep verifier/spec/claim-map
   files out of the solver's filesystem and search index.

The existing render preparation currently supplies full statute/local-rule
objects to legal kinds. Replace that with a public-field projection before W2:
legal content is licensed, private sampling/lineage/decision annotations are not
automatically public. Also remove private fidelity/staleness/selection labels
from published front matter; the solver should infer them from text.

Verification must distinguish **a faithful rendering of an intentionally wrong
source** from an erroneous render. Both literal asserted content and underlying
world truth belong in private provenance. Likewise, extraction accuracy concerns
what the text says; source reliability concerns whether that assertion is true.
Do not score a correct extraction of a planted false statement as a parsing
mistake. The current criterion-label bridge needs this distinction before its
labels can stand for real extractor error.

Pin render/verifier model identifiers, prompts, code/config hashes, seeds where
supported, attempts, tool inputs and costs. Frozen text artifacts, not a promise
that an LLM will regenerate identical prose, are the reproducible corpus.

## 9. Partitions, calibration and fair comparisons

**The sizing case for rendering a subset rather than thinning 58 counties is
now quantitative.** The median county-programme cell yields **one**
timing-bearing reddit post and 38% of cells yield none, so the entire user tier
across all 58 counties and 7 programmes holds 1,597 timing-bearing posts —
about 1.5× what *one* ambiguity class needs to reach a 0.80 confusion diagonal.
Label volume therefore has to come from criterion reveals in the declared and
designed document tiers; the user tier's role in the design is to be the sparse,
heavy-tailed, population-skewed nuisance channel it measurably is.

Retain the draft's **14 calibration / 29 development / 15 reserved counties**
as the initial target. Freeze assignments before rendering, stratified on public
design covariates; do not choose them after viewing posterior performance.

Separate build permissions from evaluation permissions. A builder/verifier may
need private truth; an extractor/fitter must not. Use separate private and
public bundles plus allowlisted loaders, not just a `reserved/` directory name
or an environment variable that any solver can set. Reserved public documents
are released for inference only under the frozen evaluation protocol; reserved
truth is read only by its scorer.

For the first budgeted text corpus, propose 20 fully rendered target counties
distributed **8 calibration / 7 development / 5 reserved**, selected for
covariate and program coverage. The remaining counties remain oracle/spec-only.
Render the public law, donor evidence and structured distractors those tasks
actually need as well. This allocation is a budget proposal, not proof of
adequate calibration: enlarge the calibration text tier if the pilot shows
sparse cells. Never report a 58-county end-to-end comparison from five rendered
reserved counties.

Use two distinct transfer masks:

- **Within-county, held-out-program:** disclose donor programs using the same
  agency but withhold a target program's timing/labor reports. This tests whether
  learned agency information transfers; labels remain hidden until scoring.
- **Held-out-county:** supply only the protocol's allowed target-county evidence
  and public covariates. This tests population-level generalization, not knowledge
  of an unseen agency's individual effect.

Have a separate unseen-template/lineage stress condition. Shared public statute
language across county partitions is legitimate; copied local policies or the
same underlying case should not accidentally cross calibration fit/validation
boundaries and inflate measured semantic accuracy. Declare whether policy
lineage is shared or held out in each condition.

Measure real extraction on rendered calibration documents, using verified spans.
Cover quantity typing, normative/observed status, clock endpoints, visit basis,
cohort, step identity, agency identity and criterion interpretation—not just the
four existing criterion classes. Include unknown/out-of-chart and missed-claim
outcomes. Repeated votes from one LLM are correlated predictors.

The approximately 90% top-reading rule is a routing heuristic with uncertainty,
not automatic certification. High-accuracy classes can stay upstream; other
classes get calibrated finite alternatives only if paired downstream timing/count
validation supports them. Report sparse calibration cells instead of claiming
that 58 counties automatically supply enough examples. Do not pool `wrong` and
`vague` solely to improve sample counts: they describe different mechanisms.

Compare on identical released information:

1. LLM-only document aggregation, including an incremental-update condition;
2. simple pooled/partially pooled statistical controls with explicit priors;
3. V6 with calibrated top readings;
4. V6 with the validated ambiguity mixtures;
5. oracle-claim/structure controls, labeled as diagnostic upper references.

Give the LLM the same donor evidence or equivalent access to it; record context
and tool budgets. Use repeated runs to measure instability for both text systems
and numerical inference. Do not claim an LLM is inherently incapable of pooling.

Score structure/counts, clock-matched predictive error, interval coverage and
proper interval scores, supported labor predictions, transfer and incremental
updates. Score policy readings against fixed gold populations, with coverage and
frequency-sensitive distributions. Include modal-reading, prior-only and no-
pooling controls. Report results by evidence level, source family, county size,
route and prior sensitivity, with both population and equal-county summaries.

Use a small scale ladder that varies **independent cases and donor cells**, not
only document copies; also include a duplicated-document control that should
not tighten uncertainty as though it added cases. Predeclare replication counts
and a meaningful paired score difference after the development pilot, before
opening reserved truth. Numerical convergence, marginal variance contraction,
joint identification and predictive success are separate diagnostics.

## 10. Implementation packets and stop/go gates

The paths below are proposed additions unless already present. Keep one
generator/build route; do not introduce separate run/extend/check scripts per
experimental variation. Configuration and manifests should select variations.

| Packet | Work / main files | Deliverable and gate |
|---|---|---|
| G0 — freeze inputs and reconcile | Source-to-design register; decision log; existing audits; current generator/scorer inspection | Hash/pin inputs and code state. Record accepted scope changes. Repair/verify the three P12 blockers before production scoring. Do not overwrite other-agent work. |
| G1 — contracts and identities | `schemas/`, `domains.py`, `processes.py`, `decision.py`, `simulate.py` | Clock/resource/count/authority/source contracts; valid legal bounds; one hand-checkable sequential, parallel, repeated and censored example. |
| G2 — county and crossed design **(IMPLEMENTED 2026-09-16)** | `counties.py`, `capacity.py`, `lineage.py` and the `world_model_version` knob now exist; v1 remains byte-identical | Versioned panel and parameter provenance; connected observed donor design; deliberately sparse control cells; legacy behavior preserved under its explicit versions. 58-county panel reproduces the real population skew, the **inverse** staffing gradient (r=-0.71 against -0.73), the UIC noncore count (11), the 39/18/1 consortium split and the RUCC/UIC disagreement. |
| G3 — case and observation simulation | `simulate.py`, `visibility.py`, `specs.py`, `ceiling.py`; small shared observation helpers if needed | Truth→claim round trips; labor independent of elapsed units; coherent aggregates and overlap; reporting errors separate from truth; scenario configs. |
| G4 — pilot rendering and labels | `render/prepare_batch.py`, existing briefs/style files, claim-map schema, verifier packaging | Six-county/five-family pilot; independent span verification; no unauthorized facts; estimates of tokens, failures, artifact counts and label-cell coverage. |
| G5 — scale and access isolation | `build.py`, schemas, public/private export and existing mock web | 58+8 panel, ten-family target after pilot acceptance; frozen partitions and masks; rendered subset explicit; solver cannot read private or reserved truth. |
| G6 — corpus release audit | Existing validation/evaluation entry points, manifests and release report | All released artifacts pass; reproducible logs and hashes; availability/reachability/text coverage by stratum; baseline protocol frozen. |

Do not begin a mass render while G1–G3 are unresolved. The pilot is a disposable
development world, never a reserved benchmark after it has been inspected.
Use fresh identifiers such as `W2_PILOT_001`, `W2_DEV_001` and
`W2_RESERVED_001` or equivalent private/public bundles linked by one release
manifest. These are release/split identities, **not competing architectures**.

### Budget control

Generate truth/specs and counts before buying a large render. For G4, target
roughly 100–150 target artifacts plus necessary public law and a bounded set of
structured distractors; determine the exact count from the pilot visibility
draw. If it exceeds the cap, reduce the declared pilot scope, not selectively
drop difficult documents. Independently verify every released artifact.

Measure tokens, wall time, retries and costs by document kind. Use those measured
rates to propose the full render budget and worker concurrency. The old estimate
of roughly 5,700 specs concerns the earlier six-domain design; it is **not** a
budget for this proposed ten-family release. Structured same-statute/county
distractors are primary; record the realized filler ratio rather than asserting
a ratio that a cap prevented. Stop after the pilot for budget approval if the
full run requires a materially new spending commitment.

Simulation, parsing and structural checks are local CPU tasks. Render/verify
latency and numerical inference are different costs; report them separately.
Do not move data or jobs to sk3, create accounts, use paid services, stage/commit
the shared tree or archive externally merely because they appear in this plan.

## 11. Definition of done and handoff artifacts

The release should contain or link to:

- Frozen configuration, source-to-design register and explicit assumption list.
- Versioned private truth, full event/resource logs, observation claims and
  provenance, including RNG stream/version information.
- Public text corpus and mock web; explicit rendered/spec-only membership.
- Private verified claim-span crosswalks, verifier outputs and rejected attempts.
- Partition/lineage/transfer masks and public/private access manifest.
- Quality report: units/clocks/count consistency, publication/reachability,
  source dependence, missingness, label coverage and identification diagnostics.
- A frozen comparison protocol and a small tracked results registry; no claimed
  Bayesian improvement until that comparison is actually run.
- File hashes and a stated retention location. Gitignored local artifacts are
  not backed up just because code is committed; follow [the run policy](../runs/README.md).

**Immediate assignment for the receiving agent:** inspect the latest shared log
and working tree; reconcile this plan with the detailed W2 spec; implement G0–G3
for the five-family pilot; report unresolved decisions and a concrete pilot
render estimate. Then run G4. Preserve W1 and all previous failures. Do not
quietly turn unavailable real measurements into measured synthetic anchors.

Full public-source retrieval is not a prerequisite for this pilot. Missing
evidence is itself part of the design, provided it stays explicit. A coherent,
auditable corpus with honest information limits is the target—not an exhaustive
simulation of every administrative process or a guaranteed Bayesian victory.

## 12. Retrieval follow-up, 2026-09-17

The [independent W2 review](2026-09-17-w2-decision-log-review.md) and
[exhaustive-retrieval progress record](scoping/2026-09-17-exhaustive-retrieval-progress.md)
add the following design constraints. These are inputs to a declared revision,
**not permission to mutate a world while it is rendering or being fitted**.

- Use program-specific agency/service-area mappings. LA County well approval
  includes incorporated cities except three independent jurisdictions; a blanket
  unincorporated-population exposure would be wrong for that program.
- Preserve non-case and non-timing discourse. IHSS keyword hits can be CalFresh
  income questions, recruitment posts or agency descriptions. County mentions
  can refer to a future job location rather than the reported case. Search hits,
  time words and comment counts are not calibrated process-evidence rates.
- Keep institution, report publication, access and readable transcription
  separate. A Modoc report itself could not locate two prior jury-year reports.
  Riverside serves an accessibility notice before public PDF links; many retained
  reports need OCR. An HTTP 200 or a `.pdf` filename is not accessible content.
  Selectable headings can coexist with image-only tables; completion of a
  character-count-based OCR queue does not establish full-page observability.
- Model historical agency responses and staffing allocations with their dates
  and units. Lake's 2014 IHSS response describes investigator/prosecutor staffing,
  not labor hours per application or an agency every recipient encounters.
  Original recommendations and responses are linked claims.
- Retain removed/empty comments, missing parents, quotes and page boundaries as
  archive states. The first new 274-tree batch has 7,188 comment IDs but only
  6,918 available bodies; those numbers describe this archival increment, not
  population deletion rates, independent cases or relevant timing measurements.
- Treat administrative-source dates and panel coverage as observed metadata,
  not infallible truth. Five additional CF 18 workbooks have partial fiscal-year
  coverage, blank county rows and, in two vintages, conflicting `Date` and
  `Report Month` values. Preserve literal fields and source-level uncertainty;
  do not assign a case/cohort date by silently repairing the publisher's file.
  [Raw-source inventory](../corpus/counties/raw/exhaustive_2026_09_17/calfresh_cf18_followup_inventory.json).
- A visible forum post container may have an empty body, and older posts may
  be edited later. Creation-date pagination is not complete edit coverage;
  original encodings and source bytes matter. The new forum QA documents empty
  bodies and corrects its own initially inadequate edit selector rather than
  converting a parser limitation into a source-absence claim.
  [QA qualification](../corpus/counties/raw/exhaustive_2026_09_17/calguns_node_audit_qualification.json).
- Reconcile at claim/case level within discussions. A city-addition OP can
  contain replies about county ADUs, a withdrawn garage application and a
  separate pending city renovation. A reply can correct an earlier
  jurisdiction guess. One comment may contain multiple projects and clocks;
  quoted costs, fees paid, labor and elapsed time are not interchangeable.
  [Statement-scope examples](../corpus/counties/raw/exhaustive_2026_09_17/reddit_adu_statement_scope_review.json).
- Preserve conflicting representations within one source and across versions.
  SBCAG's regional ADU owner survey has a visually confirmed timing-table/chart
  label conflict in both its September draft and October publication, plus
  inconsistent sample totals. Region/city subsets overlap; optional questions
  leave unknown outcome-specific denominators. Versioning does not create an
  independent cohort, and a published table is not automatically calibration
  truth. [Version check](../corpus/counties/raw/exhaustive_2026_09_17/sbcag_adu_october_version_review.json).
- Vary time and monetary quantities without relabeling them as observations of
  the target. New well discussions distinguish advance notice, physical
  drilling, technical pump-test duration, long-run return on investment,
  contractor quotes and government fees. Prospective questions and a reply
  correcting a new-build story to an existing-house purchase are useful
  negative examples. Exact duplicate comment bodies are dependent reports,
  not replicated cases.
  [Statement-scope review](../corpus/counties/raw/exhaustive_2026_09_17/reddit_well_statement_scope_review.json).
- Represent project types and institutional roles explicitly. Alameda's well
  FAQ assigns different service areas to county, city and water-district
  authorities. San Francisco monitoring-well instructions distinguish
  construction, inspection, reporting and annual operation; a municipal
  water-project proposal is not a completed domestic-well permit. Related SF
  PDFs have different byte hashes but identical extracted text. County of
  publication, table-row count and distinct file hashes cannot identify actors,
  required steps or independent evidence by themselves.
  [Primary-source follow-up](scoping/2026-09-17-well-primary-followup.md).
- Agency-side documents can measure accounting systems rather than case work.
  An Alameda jury chapter is about Oakland city's plan-check office and
  distinguishes assignment queues, expedited service, revisions, payroll
  overtime and applicant billing. Its reported reconciliation problems are
  attributed historical audit findings, not directly observed per-case staff
  hours. Preserve the claim's target and uncertainty rather than forcing a
  labor observation from fees or payroll totals.
  [Chapter review](../corpus/counties/raw/exhaustive_2026_09_17/oakland_plan_check_chapter_review.json).
- Include unresolved version authority, not just noisy numeric measurements.
  Two currently linked El Dorado well applications require completion reports
  within 30 versus 60 days and have different conditions and department names.
  Their URL revision counters do not establish precedence. These are reporting
  deadlines, not mean permit durations; averaging them would answer neither
  question. A changed department heading is not automatically another actor.
- Separate administrative stocks, flows and record maintenance. Butte's well
  report distinguishes issued permits from finaled wells and describes backlog
  status updates. The two series are not a linked application cohort. Its
  cumulative and monthly tables also disagree on one historical issuance total
  (69 versus 113), confirmed visually. Preserve partial years, blank cells and
  source conflicts; do not manufacture completion probabilities or clean
  calibration truth from these aggregate counts.
  [Version and table review](../corpus/counties/raw/exhaustive_2026_09_17/well_children_statement_scope_review.json).

W2 parsing is gated separately on `observed.complete_by_counts`, as requested
by Alex. That count gate does not close the scientific audit, certify every
verdict as passing, or turn unsupported V6 burden channels into measured outputs.
The [source-only V6 handoff](scoping/2026-09-17-w2-v6-handoff.md) preserves that
distinction and keeps private generation/verification data out of extraction.
