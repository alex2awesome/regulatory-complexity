# September 20 work recap and remaining work

Checkpoint: **2026-09-21 06:12 UTC / September 20, 11:12 p.m. Pacific**.
Written at Alex's request as a consolidated progress report and audit handoff.
This is a dated checkpoint, not a claim that the study is complete. Live run
status must be checked again before acting on it.

**Superseding work order, September 21:** Alex subsequently supplied Fable's
[process-structure plan](2026-09-21-process-structure-posterior-plan.md), requested
a first implementation, and said continue. See the
[current implementation/review](2026-09-21-process-structure-first-pass.md).
County-hierarchy/CF18 extension is deferred without a real run. Current effort
is the step model on real CalFresh and CCW; the running Joint47 finishes once
with failures retained. The historical CalFresh-first queue below is not the
new execution order.

**Priority addendum, 06:20 UTC:** Alex explicitly prioritizes solidifying the
full Bayesian statistical learning, especially agency capability and process
steps. Within CalFresh, county/agency identification and structure/count inference
now take precedence over further descriptive-summary expansion. The current
timing run continues unchanged; it is not a substitute for these targets.

**Statistical-learning checkpoint, 06:43 UTC:** The first collapsed Joint47
condition passed at 06:27; the second is running and the third is pending.
Root independently reproduced the accepted administrative fit's county-bin
probabilities and all 1,035 pairwise log-location intervals. The county effects
learn, but the separately named agency block is inactive. A learned county-scale
extension is prepared for guarded execution. The CF18 county/service/month
panel is prepared (58 counties × 58 months × two clocks; 6,238 positive integer
histograms), not fitted. A reusable overdispersion likelihood passes 30
source-free tests but is not yet connected to V6. Count metadata now retains
county information for 51 of 68 candidate facts; process-graph candidates are
under substantive review, not posterior results. The exact next sequence is in
the [statistical-learning work order](2026-09-20-calfresh-first-closeout-work-order.md).

## 1. Bottom line and scope

We have moved from reviewed text to actual, qualified CalFresh results: a
county-level administrative prediction comparison, seven applicant-reported
timing components, a small joint-timeline fit, and source-linked structural and
descriptive findings. We have **not** finished the unified burden model,
identified intrinsic agency delay, calibrated real source trust, or obtained
validated posteriors on the full process structure and number of steps.

The full objective remains three real program families—**solar, concealed
carry, and CalFresh**—with corresponding synthetic evaluations and defensible,
reproducible conclusions. These are program families, not three isolated legal
sections. The [approved three-family plan](2026-09-20-three-statute-parse-verify-analysis-plan.md)
remains the scope. Alex subsequently directed:

1. Real corpora before synthetic corpora.
2. **Finish real CalFresh before this coordinator resumes other families.**
3. Incorporate the useful forum evidence; do not require a named department or
   a matched administrative statistic for every applicant history.
4. Use Luna/Sol for routine parsing and verification.

All three current subordinate workers are Sol. Root handles model design,
difficult interpretation and review. Old worker names containing `synthetic`
are reused session labels, not their current assignments. No new general web
retrieval or synthetic rendering queue is running under this work order.

## 2. Source review and actual evidence use

### What is finished

The earlier **777-thread CalFresh reading backlog is closed**. All **945
captured logical forum threads** have review/disposition receipts. The twenty
new full-read batches form the exact disjoint 777-thread remainder; root
replayed 1,810 manifest bindings. This means the captured collection, not every
CalFresh discussion on the internet, and does not prove perfect extraction
recall from every sentence.

The wider frozen source census accounts for all **6,526 physical paths** in
its previously unrepresented-source frame. That is metadata accounting, not
6,526 useful documents or completed semantic reads. There are 1,228 candidate
paths and 1,352 uncertain/recovery representations in that frame. Empty queries,
failed downloads, aliases, derivatives and originals remain distinguished.
See the [census closeout](2026-09-20-three-family-source-census-closeout.md).

The historical CalFresh source ledger identifies **1,000 logical sources**:
945 threads, 29 documents, 20 workbooks and six oversight reports. Its original
reading-status counts predate the completed forum pass; use the current forum
receipt/register below for that status. Native workbook extraction is not a
complete semantic review of all definitions or a claim that every cell is an
independent observation.

### Current consumption, with denominators kept separate

| Quantity | Current count | Meaning |
|---|---:|---|
| Captured forum threads with review/disposition receipts | 945 | Source-review coverage |
| Effective review items / registry rows | 776 / 778 | Evidence accounting, not people |
| Threads linked to executed timing inputs | 100 | Includes aliases, dependent reports and failed conditions |
| Primary single-clock component records | 117 | Overlapping case/clock records |
| Records including the extra card sensitivity | 118 | Not 118 independent applicants |
| Component sensitivity conditions | 29, of which 28 numerically usable | Excludes the separate joint-model experiments |
| Descriptive claim-reference union | 284 | Overlaps timing and structural evidence |
| Structural claim-reference union | 220 | Not 220 steps or a posterior graph |
| Supported-use queue | 187 original; 20 closed; **167 open** | Uses, not unread threads or required separate models |

The authoritative current source-use entrypoint is
[interview-access successor v2](../runs/three_family_20260920/calfresh_forum_source_use_interview_access_successor_v2/consumer_entrypoint.json),
with its [root adoption](../runs/three_family_20260920/calfresh_forum_source_use_interview_access_successor_v2/root_adoption.md).
It directly selects the effective files; consumers should not reconstruct a
mixture of historical sidecars. Root checked all 54 bindings, preserved all
151 previous use records, and compared all 187 queue states.

**Reviewed is not model-consumed.** Using one fact from a thread does not close
its other clocks, counts or structural claims. The separate administrative
fit still contains **zero forum factors**; the forum components do not yet
form a unified administrative-plus-applicant posterior.

## 3. Actual CalFresh results

### Administrative prediction

The expanded positive-count experiment uses July 2025 recorded timing categories
for 46 counties, totaling 59,036 categorized reports. Its retrospective temporal
comparison evaluates 481 positive-count county-months from August 2025 through
July 2026; 71 zero-containing county-months remain outside that scoring frame.
The categories describe recorded expedited-benefit issuance under their
published definitions, not all applicants or every CalFresh process.

| July-trained method | Mean categorical log loss; lower is better |
|---|---:|
| County-specific Dirichlet half-count baseline | **0.252282** |
| Free-spread V6, target-preserving ridge sampler | 0.252749 |
| Three frozen LLM attempts | 0.252880 / 0.253034 / 0.253007 |
| County empirical proportions | 0.253356 |
| Pooled half-count baseline | 0.266509 |
| Numerically usable fixed-spread V6 | 0.276854 |

There is real predictive information in county-specific category distributions.
The repaired V6 base is competitive but **does not beat the simple Bayesian
baseline**. Its small point-score advantage over the three LLM attempts is not
a general superiority claim. The LLM attempts received the same July counts
and were all retained; no winning attempt was selected.

The fixed-spread model converged but poorly reproduced the recorded bins.
The later free-spread ridge-sampler base passes numerically and puts 135/138
training bin counts inside their marginal 90% predictive intervals; tighter
pooling still fails and is not scored. This is an in-sample compatibility check,
not calibrated simultaneous coverage. Earlier failed fits and continuations
remain failures. The temporal exercise uses one later-released workbook: it is
not a blind forecast from an as-of-July data vintage.

Sources: [current findings](2026-09-20-calfresh-current-findings.md),
[temporal evaluation](../runs/three_family_20260920/calfresh_temporal_prediction_v1/README.md),
[ridge comparison](../runs/three_family_20260920/calfresh_histogram_ridge_analysis_v1/README.md).

### Applicant-reported timing

These are posterior intervals for the working distribution's **median within
each selected report frame**, not prediction intervals for individual people,
statewide service times, causal effects, or additive parts of a burden total.

| Clock | Main-frame records | Median and 90% posterior interval |
|---|---:|---|
| Phone queue to answer, abandonment or disconnect | 35 | 149.73 minutes [118.55, 190.54] |
| Application to interview encounter | 28 | 9.12 days [5.58, 14.65] |
| Application to first observed eligibility decision | 26 | Main mixed fit fails convergence; no accepted headline estimate |
| Application to reported benefit availability | 6 | 2.14 days [0.47, 8.44] |
| SAR7 submission to material response | 11 | 17.43 days [9.94, 32.46] |
| Recertification to observed decision | 3 | 31.27 days [15.72, 68.01] |
| Approval/notification to physical card possession | 8 | 21.80 days [11.24, 49.34] |

Phone35 includes 27 completed exits, six pending spells and two lower bounds
with unknown terminal status. Queue exit is not successful contact or active
labor. The card-admission sensitivity adds a ninth history under an explicit
business-date counting assumption; its median is 22.07 days [11.42, 48.45].
The small benefit/recertification samples are especially prior-sensitive.

Including pending interview histories changes the median from 4.69 to 9.12
days. This demonstrates sensitivity to the observed sample definition, not a
learned correction for selective forum posting. The 26-case decision base fails
R-hat at 1.01048 against the unchanged 1.01 gate; a passing sensitivity does not
replace it. Sources and all conditions are linked from the
[current findings](2026-09-20-calfresh-current-findings.md).

### Linked histories and nonparametric event bounds

A [five-case joint V6 model](2026-09-20-calfresh-joint-timeline-results.md)
completed both specified reporting-error conditions, in about three minutes
total. Fifteen projected intervals enter as five dependent case factors, not
fifteen independent measurements. In three completed histories, posterior
median post-interview shares are 79.7%, 87.2% and 84.3%. The source-derived
intervals already force a post-interview majority in those three histories;
the fit is not independent validation of that fact or proof of agency causation.

The broader 47-history observed-event analysis has only twelve finite total-time
upper bounds. Its finite-record lower-median envelope is [9 days, infinity);
for the 26 histories with explicit whole-process reports it is [18 days,
infinity). These are source/coarsening bounds, not posterior intervals or
population estimates. Independent linear programs reproduced all 74 path bounds.

Additional adopted descriptive analyses cover benefit disruption, unsuccessful
telephone contact, office/travel burden, renewal problems and interview access.
The latest interview-access addition supplies thirteen descriptive links and
nine event chronologies with nineteen constraints. It closes no timing uses.
An eight-case benefit-disruption analysis permits nonarrival indefinitely and
keeps theft reimbursement, postapproval availability and contact-chasing separate.
None of these derived bounds becomes an extra independent likelihood factor.

## 4. Model implementation and numerical work

**V6 remains the integration target.** The seven clock components are bounded
applications of that model, not seven replacement architectures. They are also
not yet one combined fitted system.

Implemented or repaired in this workstream:

- Source-type/document reporting-bias hierarchy, explicit source-type precision
  declarations, and exact administrative histograms as eligible reference
  anchors. These mechanisms do not establish empirical source calibration.
- Preservation of reviewed finite-quantile cohorts through the structural
  bridge. Previously the bridge could drop them. Added guards prevent duplicate
  identities, generated-key collisions and silent unit reinterpretation.
- Conditional reported-case models that retain completed and pending cases;
  case marginalization reduces the original phone/interview sampled dimension
  from 68/62 to two without replacing their priors or evidence.
- Shared-report-error joint timing likelihoods, optional/absent event handling,
  explicit case-specific path-prior sensitivities, and neutral lower-bound
  admission when terminal status is unknown.
- Exact case-local likelihood updates and same-target sampler transitions.
  Local evaluation speed is not automatically whole-fit speed.
- A collapsed 47-case evaluator and four-coordinate MCMC driver, described below.

The [source precision/cohort handoff](2026-09-20-source-precision-and-cohort-handoff.md)
documents the bias/precision/selection distinction and actual integration bugs.
The [source-bias mechanics](2026-09-20-source-bias-mechanical-results.md) recover
relative planted shifts in six deliberately aligned mathematical fixtures.
A [supplemental control run](2026-09-20-source-bias-control-followup-results.md)
eventually converged, but does not rewrite the original protocol's failed gate.
These are mechanics experiments, not realistic text-recovery or real-data trust
validation. Clean-condition performance did not uniformly improve.

### Failures and the current 47-case attempt

The joint input has 47 histories, 61 timing facets, 49 report-error groups and
74 allowed case-path combinations. Nineteen cases have known interviews, one
has a source-known direct outcome, and 27 retain both alternatives.

| Experiment | Status at this checkpoint |
|---|---|
| Original three path-prior conditions, 02:18–03:30 UTC | All three failed convergence |
| Equal-budget transition repair, 03:51–05:02 UTC | All three failed; two improved, one worsened |
| Four-coordinate collapsed model, started 05:57:48 UTC | **Running; no accepted new result yet** |

The completed repair comparison reproduced all 48 checked saved likelihoods
exactly. Correct likelihood evaluation did not fix poor mixing. No failed
posterior is presented as a usable scientific result or used to close the queue.

The current approach integrates approximately 200 original sampled coordinates
down to four: three correlated operation-location coordinates and one spread.
It preserves the induced hierarchy prior, case dependence, censoring, shared
reporting errors and fixed candidate paths. This is integration, not setting
case effects to zero or making three independent replacement priors.

Quadrature is numerical: independent references, broad-spread probes, exact
support boundaries and tail bounds were needed. Some earlier integration
prototypes failed and remain preserved. The final checked likelihood fixtures
cost about 0.179–0.185 seconds, versus roughly 1.5 seconds initially; eighteen
base/refinement probes differ by at most 7.50e-8 in log likelihood. These finite
checks are not a uniform accuracy theorem or a full-run speed benchmark.

Live execution details:

- [Frozen plan](../runs/three_family_20260920/calfresh_joint47_collapsed_runner_v1/plan.json):
  SHA-256 `bbe657c548305aedd52fbbe19e30f98eabad6e7f32f4643c8ac3d76675b0b7b0`.
- Launcher PID **42245**, session **62389**; actual process checked live, not
  inferred from a stale status file. First condition is still running.
- Three ambiguous-path priors: 50/50, 90/10 and 10/90; four chains each,
  2,500 warmup and 6,000 retained draws per chain, four local worker processes.
- This changes the draw budget: it is **not** an equal-budget speed comparison.
- Unchanged numerical gates: R-hat at most 1.01, bulk ESS at least 400,
  tail ESS at least 200, plus specified numerical-integration checks.
- All **47 dependency bindings remain frozen through fits and postfit analysis**.
  Do not restart on an observation timeout, edit a live binding, inspect partial
  draws to choose a condition, or extend automatically.
- [Execution receipt](../runs/three_family_20260920/calfresh_joint47_collapsed_runner_v1/actual_fits/execution.json)
  and [prepared postfit analyzer](../runs/three_family_20260920/calfresh_joint47_collapsed_analysis_v1/README.md)
  are the continuation entrypoints. The analyzer is prepared, not executed or
  root-adopted as a completed analysis. It requires all three conditions terminal.

Method: [joint-case marginalization](2026-09-21-calfresh-joint-case-marginalization.md).

## 5. Structure, step counts, actors and trust: what is NOT established

Alex specifically asked whether we also have good posteriors on process
structure and number of steps. **We do not yet.** Timing success cannot satisfy
that part of the burden-model objective by itself.

The [structural inventory](../runs/three_family_20260920/calfresh_integrated_applicant_structure_results_v1/report.md)
contains 220 canonical claims and 103 native numeric fact rows, under thirteen
action, six requirement/advice and eleven obstacle headings. These are descriptive
categories, not thirteen mandatory steps or a learned process graph.

The 47-case model compares supplied coarse interview/direct routes. Its two
serial elapsed phases are not two primitive tasks. Conditional path probabilities
can be inferred within those candidates if computation succeeds; population
route frequencies, missing graph nodes and a full topology are not being learned.

The unfinished structural targets must remain distinct:

1. **Required distinct steps** in an applicable process template.
2. **Encountered steps** on an applicant's optional/conditional route.
3. **Actions actually performed**, including repeated calls, uploads and visits.

Counts need an episode/window, task granularity, dependency handling and explicit
complete versus partial reporting. Silence about a step is not evidence of its
absence. Step-identity uncertainty should use source-supported alternative
inventories, with declared or calibrated weights, not unconstrained graph search
or an arbitrary probability attached to every possible edge. This remains
within the existing inventory/path uncertainty design, not a new architecture.

Other unestablished quantities:

- Real intrinsic agency delays and department assignments. Unknown actors are
  admitted; categorical candidate machinery exists but is not a validated
  CalFresh attribution result. Agency effects are disabled in the present
  bounded joint-timing experiment, not empirically estimated to be zero.
- Selection-corrected applicant-population timing. Posting and censoring may
  depend on experience; source offsets alone do not solve that problem.
- Empirically calibrated source bias, precision or contamination. Earlier
  bounded administrative/forum matching reviews found no eligible overlap for
  their particular clocks; this is not a universal exclusion of forum evidence.
- Applicant active labor, agency person-hours, hidden-task times and broad
  external costs where the sources do not observe them. Waiting is not labor.
- A scalar overall burden score, causal blame or a validated simplification
  recommendation. These do not follow from conditional timing summaries.

## 6. Verification: what it did, and its stopping rule

Verification has several different jobs; a pass in one does not certify the rest:

1. **Source/provenance:** immutable bytes, quotes, hashes, coverage, aliases and
   missing representations. This establishes what was read and quoted.
2. **Semantic review:** units, endpoints, author/case identity, reported versus
   scheduled actions, pending status, populations, and independence.
3. **Compiler checks:** retained factors, compatible clocks/channels, dependence,
   neutral/absent events and no dropped or duplicated observations.
4. **Numerics:** likelihood replay, integration refinement, chain convergence
   and effective sample sizes. This does not establish model adequacy.
5. **Scientific checks:** prior sensitivity, identifiability, predictive behavior,
   same-information comparisons and limits from missing or selected evidence.

Concrete semantic corrections included future appointments mislabeled as
completed interviews; schedule windows treated as labor; notice receipt used
as an underlying decision time; one commenter inheriting another author's
location; and repeated descriptions being counted as separate evidence.
The latest review also restored an explicitly named Sacramento jurisdiction
and a same-report-group calendar constraint missed by projected intervals.

The last recorded scoped project regression run passed **1,940 tests** after
the combined core repair. Later collapsed-runner checks passed 22 focused tests;
the prepared analyzer passed three. These are dated code checks, not claims
that every scientific inference or all current unrelated work was tested.

The stopping rule is: replay a bounded immutable packet, review its meaning,
itemize and correct concrete defects, then use it. Do not restart all-thread
verification merely because new downstream work is possible. Do not close
timing uses simply by adding descriptive prose.

## 7. Exactly what remains for CalFresh

The current 167-row evidence-use queue records these work states (not permanent
exclusion reasons or independent people):

| Remaining state | Rows |
|---|---:|
| Clock-family implementation | 118 |
| Interpretation/coarsening candidates | 22 |
| Dependent phases or descriptive uses | 12 |
| Specific semantic/contract holds | 7 |
| Compiled but not fitted | 8 |

The rows overlap sources and include support for different quantities. They do
not authorize 167 separate models. Close a use only through its supported result
or a specific justified disposition, without pretending all data can identify
every desired latent quantity.

Ordered remaining work:

1. **Finish the live joint run and its fixed postfit analysis.** Preserve all
   conditions/failures; check the actual operation and path summaries, not just
   a runner's success flag. No automatic continuation. A numerical pass still
   does not establish source selection, graph recovery or population validity.
2. **Identify and estimate the county/agency hierarchy.** First derive what the
   accepted administrative fit actually learns about county contrasts, with
   posterior uncertainty and decomposition into identifiable versus confounded
   quantities. Then extend the common model using repeated tasks, periods and
   source-supported county procedures where compatible evidence exists. County
   delay is not automatically intrinsic capability: process, caseload, case mix,
   reporting and period effects must remain explicit. Do not introduce a second
   indistinguishable county/agency offset merely to give it the desired name.
3. **Implement structure/count inference as an explicit deliverable.** Complete the
   source-bound count input and ordinary-initial-application candidate graph,
   distinguish required/encountered/repeated actions, then run a bounded
   candidate-inventory analysis with sensitivity and independent checks.
   An underidentified count should be reported as such, not made precise by fiat.
4. **Integrate the reviewed evidence needed by these learning targets.** Keep
   compatible histories together and preserve parallel uses. Complete the finite
   remaining-use queue without making descriptive packet production the main
   objective; an unrelated clock does not become approval time for convenience.
5. **Resolve the remaining nonforum coverage/semantic ledger.** Reconcile native
   workbook extraction versus full definition review, CF18/reporting-zero/unit
   holds, CF256 context, and uncertain physical representations. The completed
   forum reading pass does not automatically close these source obligations.
6. **Assess legitimate source combination.** Match endpoints, populations,
   periods and memberships before combining administrative and forum evidence;
   distinguish overlap from duplicate cases. If bias/selection cannot be
   identified, preserve conditional components and state that limit. Do not
   demand a named internal department as a general admission rule.
7. **Consolidate the scientific report and comparison.** Retain negative results,
   identify prior-determined outputs, separate administrative/applicant/structural
   targets, and audit the resulting coverage and claims once. The existing
   administrative LLM comparison does not evaluate the full text-to-burden system.

Current bounded worker assignments, **not yet completed results**:

- Case-count inputs from the already-reviewed native count facts.
- Source-supported ordinary initial-application graph/candidate identities.
- Derived county-learning audit of the already accepted administrative fit,
  including what posterior variation can and cannot mean about agency capability.

The expanded descriptive benefit-disruption packet has since been prepared by
the worker (fifteen records/fourteen case IDs, inherited bounds retained), but
is not root-adopted or fitted and changes none of this note's consumption counts.
Further descriptive expansion is deferred in favor of the statistical tasks above.

Two just-finished candidate packets also need root review before use: the
[13-use benefit reconciliation](../runs/three_family_20260920/calfresh_benefit_disruption_queue13_delta_v1)
identifies five additional source-bound candidate histories; the
[nine-use card reconciliation](../runs/three_family_20260920/calfresh_card_remaining9_input_delta_v1)
finds no compatible additions to the existing approval-to-possession clock.
Those nine uses remain open for their actual clocks, not rejected for missing
department names. Neither packet by itself changes current consumption counts.

### County process differences: evidence and the modeling implication

There is evidence of local implementation variation within a shared program,
not evidence that all 58 counties necessarily have 58 different process graphs.
CDSS describes CalFresh as state-supervised and county-operated
([program page](https://www.cdss.ca.gov/inforesources/calfresh/county-offices)).
Its SSI-expansion resource collection documents county-specific interview,
signature, verification, telephone and lobby workflows, including Marin's
on-demand process and Santa Clara's application flow chart
([CDSS toolkit](https://www.cdss.ca.gov/inforesources/calfresh/supplemental-security-income/resources)).
Those materials describe particular historical implementations, not a verified
current adoption census.

Current accessible Santa Clara instructions offer same-day interviews when
available and otherwise describe a mutually convenient scheduled interview
([county handbook](https://stgenssa.sccgov.org/debs/program_handbooks/calfresh/assets/CalFresh/Application/SchedIntrvw.htm)).
San Diego describes county-arranged telephone interviews and several submission
channels ([county application page](https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/food_stamps/submitting-your-calfresh-application.html)).
Different descriptions alone do not prove mutually exclusive policies: a county
may offer several routes, and a webpage may omit a route available in practice.

These official pages were checked online for Alex's side question. They are
contextual citations, **not silently added observations to the frozen fits**.
Any future admission needs source capture, date/era matching and the normal
evidence contract. The statistical design should share a common step vocabulary
and hierarchy, allow county-specific routes/rework, and separate those effects
from county timing contrasts. The existing administrative comparison supports
predictive variation among recorded county distributions; it does not yet
attribute that variation to process design or intrinsic capability.

## 8. Other real families and synthetic counterparts

### Solar

This coordinator's 401-authority, 2022 permit-phase V6 sweep is reversibly
suspended under CalFresh-first. Process group 80419 and all six members were
checked stopped at this checkpoint. This preserves in-memory work, **not a
durable restart checkpoint**. Check process identity and frozen input/code
consistency before any eventual resumption; no complete expanded result has
been adopted from that run.

Earlier work corrected SolarTRACE phase/owner/cohort interpretation and exposed
source-provenance issues: some captured TXT files were summaries, and a file
named as a San Diego PDF was original HTML. A 2026 requirement cannot silently
explain a 2022 timing statistic. Structural/fee parsing remains partial.

**Separate-agent work must not be confused with that paused run.** Claude's
[Solar panel report](2026-09-20-solar-bayesian-results.md) exists on disk and
reports a different panel analysis, held-out failures, and a twelve-pair forum
offset analysis. This recap locates it but does not independently adopt or
validate its estimates. Its existence also means the older bounded finding of
zero matched pairs must not be generalized to every Solar phase/source frame.

Remaining Solar work is to reconcile ownership with Claude, audit rather than
duplicate that leg, finish source/structural coverage, resolve experimental
scope and units, and release only appropriately qualified comparisons.

### Concealed carry

The bounded V6 pilot on four pre-training-approval-to-training histories passed
six specified conditions and independent result review. It measures a selected
applicant/provider scheduling phase, not issuer processing time. The base
working median was 31.3 days [16.4, 56.9].

A separate descriptive first-96-label view has eight exact-day initial
submission-to-physical-receipt episodes and nine additional coarse/held
completed histories. Whole-process reconciliation, broader source consumption,
era/issuer identity, pending cases and structural/fee analysis remain unfinished.
The deferred whole-process fit candidate is a draft, not an executed model.
See [bounded pilots](2026-09-20-calfresh-and-ccw-pilots.md) and
[real-corpus checkpoint](2026-09-20-real-corpora-first-results.md).

### Synthetic work: deferred, not abandoned or complete

Solar's counterpart is W2 S07; CCW and CalFresh require the new small analogues,
not relabeling unrelated W2 statutes. `THREE_FAMILY_PILOT_003` has 26 rendered
documents and verdicts, with 19 latest-version passes and seven presentation
failures under its recorded adoption hold. It is not a released corpus or a
completed recovery test. A fresh held-out S07 replica has not been generated;
the already-inspected W2 material is development data, not untouched validation.

The legacy W2 monitor was last checked at **06:35:45 UTC**. Its selected S03
lane has artifacts and verdicts for all 245 specs (`observed.complete_by_counts`
is true), but two verdicts fail. Across the world: 2,886 artifacts, 2,875
verdicts, eleven unverified and 45 failures; `corpus_complete` is false. The
writer's stale `state` is not completion evidence. This legacy S03 lane is not
the synthetic CalFresh counterpart and is not a prerequisite for real results.

The hourly monitor remains read-only; next due 07:35:45 UTC. Later synthetic
work must finish the agreed counterparts, protect hidden truth from extraction,
verify source-to-truth fidelity, and test timing, counts, structure, calibration
and same-information baselines. It must not widen into all unrelated W2 domains.

## 9. Reproducibility, handoff and completion boundary

Start with this note, then:

- [CalFresh current findings](2026-09-20-calfresh-current-findings.md): scientific
  summaries, failures and direct result links.
- [CalFresh closeout work order](2026-09-20-calfresh-first-closeout-work-order.md):
  current priority and completion requirements.
- [Forum integration register](2026-09-20-calfresh-forum-model-integration.md):
  the evidence-use gap and its lineage.
- [Current consumer entrypoint](../runs/three_family_20260920/calfresh_forum_source_use_interview_access_successor_v2/consumer_entrypoint.json):
  effective source-use files, not a historical sidecar stack.
- [Execution status](../runs/three_family_20260920/EXECUTION_STATUS.json):
  machine-readable checkpoint; dated historical fields remain historical.
- [Verification audit handoff](2026-09-20-verification-and-analysis-audit-handoff.md)
  and [earlier independent audit](2026-09-20-audit-of-codex-work.md): what the
  different checks establish, plus earlier findings and limitations.

Most experiment artifacts live under `runs/three_family_20260920/`; earlier
parse receipts are under `runs/rw_parse_20260919/`. Many runs/corpora are
gitignored. A source commit is not a data/draw archive. The earlier approved
pre-refactor snapshot exists, but substantial subsequent changes remain
uncommitted. The newer [snapshot proposal](2026-09-20-source-snapshot-proposal.md)
requires refreshing and approval before staging/commit; this note authorizes
neither a commit nor deletion/transfer of data.

To check, without restarting the current fit:

```bash
ps -o pid,ppid,pgid,stat,etime,command -p 42245
jq . runs/three_family_20260920/calfresh_joint47_collapsed_runner_v1/actual_fits/execution.json
python runs/three_family_20260920/calfresh_joint47_collapsed_analysis_v1/analyze.py
```

The analyzer invocation without `--run` is status/static checks only. The
current hourly synthetic check is recorded by
`python runs/rw_parse_20260919/record_hourly_render_poll.py`, which invokes the
requested `python3 benchmark/synth/render/status.py --world W2_DEV_001 --json`.

**Completion is still unproven.** CalFresh must have accounted-for relevant
sources and supported uses, finished qualified analyses, explicit structural/
count results or demonstrated limits, and a reproducible consolidated report.
Then the other real families and their synthetic evaluations must reach their
own requirements. A converged timing sampler, a fully read forum collection,
or this summary document does not complete the full objective.
