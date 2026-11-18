# One real family first: CalFresh closeout

**Superseded execution order, 2026-09-21:** Alex supplied Fable's
[process-structure plan](2026-09-21-process-structure-posterior-plan.md) and asked
for its first implementation. The [review and implementation note](2026-09-21-process-structure-first-pass.md)
is current: real CalFresh and CCW structure work, no county-hierarchy extension,
no new retrieval/descriptive queues, and no further Joint47 attempt after the
one now running. Historical accomplishments and completion caveats below remain;
the 06:43 county-learning sequence is no longer the execution queue.

Alex's latest instruction on 2026-09-20 is to **fully finish one real family
before moving on**, with particular concern that applicant/forum evidence is
being excluded. CalFresh is first because it already has an administrative
source-to-prediction loop. Solar and CCW remain in the broader objective but
are deferred; synthetic work remains deferred too. This order supersedes the
parallel real-family execution order without altering earlier frozen protocols.

Latest priority addendum (2026-09-21 06:20 UTC): Alex prioritizes the full Bayesian
statistical learning, especially agency capability and process structure/step
counts. Within CalFresh, these now precede more descriptive-summary expansion.
The running joint timing fit stays frozen; successful timing computation alone
does not fulfill this instruction. See the
[consolidated recap and revised next work](2026-09-20-progress-and-remaining-work.md).

### Statistical-learning execution, 06:43 UTC

The immediate sequence is now:

1. Finish the already-running collapsed 47-case timing/path fit. The first
   condition passed at 06:27 UTC; two remain. Preserve the same target and all
   47 frozen dependencies through post-fit analysis. Case-path probabilities
   are a limited structure result, not a posterior over the entire process.
2. Learn the between-county scale instead of leaving it fixed at one. The
   [accepted county-learning audit](../runs/three_family_20260920/calfresh_county_learning_audit_v1/root_adoption.md)
   establishes that county coarse-phase effects learn while the separate agency
   block is inactive. The pending prior-change calculation uses original
   posterior draws with a prior-density ratio, not a second likelihood on
   posterior summaries. Three predeclared scale priors and overlap/Monte Carlo
   checks are required; poor overlap calls for direct sampling, not a result.
3. Fit a crossed county/service/month extension using the reviewed CF18 panel:
   58 counties, 58 months, two approval clocks and 6,238 positive integer
   histograms. Ordinary and expedited clocks remain distinct. Before fitting,
   implement native reported-day units, conditional panel dependence and
   overdispersed count likelihoods. Keep approved-only selection and uncertain
   zero reporting explicit. This is an extension of V6's existing duration
   hierarchy and observation operators, not an unrelated model architecture.
4. Test whether a shared county effect improves prediction across services and
   time against a no-sharing county/service baseline. Learn its spread rather
   than equating a label called "agency" with capability. Report this as
   operational county performance conditional on recorded cohorts; staffing,
   case mix and reporting can still confound intrinsic capability.
5. Compile source-supported process alternatives and count observations into
   the same case trace. Distinguish jurisdiction rules from case-specific
   branching/bundling, successful-approval paths from denial/withdrawal, and
   required actions from repetitions or document-slot counts. Silence is not
   evidence of absence. Infer only the hypotheses the evidence can distinguish,
   with explicit prior sensitivity for unresolved structure/reporting.
6. Compare prior/posterior uncertainty, numerical diagnostics and predictive
   checks for the county and structure/count quantities themselves. A passing
   timing diagnostic alone is insufficient. Continue accounting for the 167
   open supported forum uses without another blanket source reread.

`pipeline/procbench/overdispersed_histograms.py` now implements the reusable
Dirichlet-multinomial factor with 30 source-free probability-law tests passing.
It is not yet imported by V6 or applied to real evidence. Extra dispersion does
not repair duplicated cohorts, source bias or missing reporting. The native-unit
contract and crossed-panel adapter remain implementation work, not fitted results.

## Worker cost routing

Alex explicitly requested Luna or Sol for easier parsing/verification. All three
current CalFresh workers are confirmed `gpt-5.6-sol` with high reasoning in local
thread metadata (18:43 UTC). Use Luna for new bounded mechanical jobs and Sol for
contextual parsing; reserve root/Astra for model design, difficult ambiguity and
reviewing conclusions. No active worker needs a restart. Keep the already-frozen
three-attempt Astra prediction baseline unchanged: it is an experimental
comparison, not a production parsing assignment.

## Execution change, 18:21 UTC

- All three worker assignments now concern CalFresh: numerical/temporal analysis;
  claimant/forum evidence; complete source accounting and ordinary-process
  definitions. No new Solar, CCW or synthetic tasks are authorized by this order.
- Solar's launcher and live base sampler were reversibly suspended with
  `SIGSTOP` after verifying their dedicated process group80419. Six members
  (80419,80441,80442,80443,80444,80445) showed stopped state afterward. Later
  conditions cannot launch while the group is stopped. Existing files remain.
  This preserves in-memory work, **not a durable restart checkpoint**; do not
  claim the base fit completed. Before eventual resumption, verify live PID,
  command/group identity and input/source consistency; never resume a reused PID
  or restart merely because a status file is stale.
- Solar's second structural tranche and CCW whole-process candidate are retained
  as partial. The CCW candidate contains only two unexecuted draft files, not a
  model input, preflight or fit. Their partial state is not a CalFresh blocker.
- Existing CalFresh fits, their individually authorized single continuations,
  and evaluation continue. Neither convergence nor an administrative result
  alone completes the CalFresh burden study.

## Correcting the interpretation of forum exclusion

The previous [CalFresh match review](../runs/three_family_20260920/calfresh_cf296_narrative_match_review_v1/report.md)
asked a **narrow calibration question**: can particular narratives be aligned
to twelve July2025 expedited application-to-issuance histograms? It examined
25 threads (17 extracted timing records), plus29 oversight records. None
provided that particular matched comparison. The forum clocks instead concern
phone access, callbacks, reinstatement, notices, periodic reports/rework,
replacement benefits and other processes. They are not therefore irrelevant.

There is no rule that every useful forum claim must have an administrative
match, nor that all forum evidence requires an identified bias correction
before it can enter the study. Keep three uses separate:

1. Source-grounded applicant actions, requirements, rework and reported burden
   components, with individual histories and uncertainty preserved.
2. Conditional distributions of comparable reported episodes, explicitly not
   estimates for all applicants; lack of selection calibration is a limitation.
3. Population-level administrative/reporting-bias inference, which needs actual
   overlap or explicit identifying assumptions and sensitivities. Unlike clocks
   must not be treated as interchangeable to manufacture that overlap.

An unmatched report is excluded from an incompatible likelihood—not deleted
from the evidence ledger or excluded from the entire burden analysis. The
expanded study must account for it and give its supported use or specific hold.
Administrative expedited timing is **one burden component**, not total burden.

## What counts as finishing CalFresh

- **Forum-to-model integration is a required deliverable, not a later optional
  expansion.** Alex explicitly reiterated this on 2026-09-20 after learning
  that the 945 captured threads were not feeding the current fit. At that
  checkpoint, 168 were reviewed and 777 unread; the expanded primary model's
  saved input contains 46 administrative histogram factors and **zero ordinary
  observations or forum-case factors**. Do not describe these fits as the full
  CalFresh burden model. Track captured, read, extracted, semantically resolved,
  compiled, actually consumed and dispositioned evidence separately. Descriptive
  retention is valuable but is not equivalent to likelihood consumption.
- **No named-department admission rule.** A claimant need not name an internal
  department. Preserve text, functional task, known jurisdiction, candidate
  actor identities and an unknown/unlisted alternative. County/process timing
  can be useful without fine organizational attribution. For genuinely ambiguous
  assignments, the intended Bayesian likelihood marginalizes one shared
  assignment over the related case reports; it does not independently reassign
  each sentence or duplicate a case across candidates. LLM confidence/votes are
  not calibrated probabilities. Measured weights or explicit sensitivity priors
  are needed, with unknown mass retained. The guarded one-phase categorical
  assignment mechanism is now implemented in
  [case_path_priors.py](../pipeline/procbench/case_path_priors.py), with shared
  case weighting and an unknown alternative. It is not yet fitted/calibrated
  for real CalFresh department assignments; the current joint47 actors remain
  unknown. Broader multi-phase organizational attribution is not established.
- One reconciled frozen-source ledger: every relevant captured source accounted
  for, readable originals processed, summaries distinguished from originals,
  aliases deduplicated, unread/missing/uncertain items resolved or explicitly
  documented as unavailable. Native spreadsheet extraction is not by itself a
  semantic review of all field definitions.
- Effective reviewed evidence covering ordinary applications, expedited service,
  interviews/documentation, renewals/reporting and other supported claimant
  pathways. Retain all forum records, including nonnumeric and unmatched facts;
  distinguish actions, elapsed waits, service, labor and costs without inventing
  conversions. Describe actual covered populations and eras.
- Source-to-model mappings for supported quantities, including compatible
  applicant-side clocks where possible; descriptive results for evidence that
  cannot support population inference. Report unidentified components and source
  bias as limits, not learned effects. No pressure to force every row into V6.
- Completed bounded model analyses and numerical/adequacy checks, every
  prespecified condition/failure retained, same-information simple and LLM
  comparisons, and explicit predictive evaluation. No endless continuation or
  claims of untouched held-out data after exposure.
- One consolidated CalFresh methods/results package that distinguishes
  administrative timing, applicant-reported burden, structural demands and
  unmeasured quantities, with reproducible evidence and a final focused audit.
  Negative findings are reportable; uncompleted source coverage is not.

Verification should have a stopping rule: mechanically replay an immutable
batch, review substantive meaning, fix itemized errors, then use it. Reopen
unchanged work only for a concrete defect or new dependency. Parsing, fitting
and analysis may proceed together **within CalFresh**; no need to finish every
document before analyzing an accepted subset, but the subset is not the final
coverage boundary. No new broad retrieval queue or extra model architecture.

## Throughput and direct consumption

Current checkpoint **2026-09-21, after interview-access adoption**: all 945 captured threads
have review records; 100 threads link to current timing fits, and **167 supported-use
rows remain unfinished**. There are 118 component records, not 118 people. The
284 descriptive claim references overlap timing evidence and the preserved
220-claim structural graph. Do not add these denominators. The administrative
fit still contains zero forum cases. The new 47-case joint run finished all
three sensitivity conditions, but all failed convergence and close no uses.
Its equal-budget transition repair and full comparison are also finished; all
three repaired conditions still fail. Office/travel descriptive use—not a new
fit—closes q081/q093/q138. The remaining numerical work targets integration of
case effects under the same scientific model, not another process architecture.
That four-coordinate fit launched at05:57:48UTC with allthree conditions,
fourchains and2500warmup/6000retained draws each. It has no completed result yet.
The thirteen added interview-access descriptions and nine event chronologies
close no timing uses; pending integration remains explicitly tracked.

The [current integration register](2026-09-20-calfresh-forum-model-integration.md)
and its linked complete consumer entrypoint are authoritative. Finish translating
the existing reviewed evidence into appropriate likelihoods or descriptive
analyses; do not restart all-thread verification. Unknown departments and absent
administrative matches are not exclusion rules. Every supported parallel use
must be accounted for; using one fact from a thread does not close the others.

Historical checkpoint 2026-09-21 01:29 UTC: all 945 captured threads are reviewed;
the bottleneck is actual evidence use. There are 115 single-clock records in
29 executed conditions (28 usable, one preserved failure), plus two completed
five-case joint sensitivities that overlap those records. The joint fits do not
add five independent cases. Eight phone reports also have adopted descriptive
use; six narrow closures leave **174 recorded open uses**, not unread threads.
The primary administrative fit still contains zero forum cases. The
[integration register](2026-09-20-calfresh-forum-model-integration.md#required-closeout--do-not-lose-this-work)
records the remaining work by type and the user's explicit completion gate.
No named-department or administrative-match requirement is permitted for
admitting an otherwise interpretable applicant timeline. Other statutes and
synthetics remain deferred; do not reopen a blanket source-verification queue.

Current checkpoint23:52UTC: all945 captured threads have review receipts;
seven primary timing components use114 records across28 terminal conditions;
one added card-admission sensitivity makes115records/29conditions in total.
Twenty-eight conditions pass; the expanded26-case first-decision mixed base
fails the unchanged R-hat gate and is not a headline result. The ten-case SAR7
successor passes all four conditions. The220-claim descriptive union overlaps
timing uses. The earlier777-thread reading backlog is closed, not the model-use
gap. Nine shared event histories now yield deterministic phase bounds under the
mandatory semantic erratum; they are not a joint fit or new independent factors.
The finite remaining-use register initially records187 rows/185 work items;
seven specifically consumed uses leave180 recorded open rows, not180threads
or independent observations. Successor consumption closes uses, not claims. See the
[integration ledger](2026-09-20-calfresh-forum-model-integration.md) for source-use
v6 and consumption deltas. The single native-business-day admission sensitivity
is now fitted and passes, using an explicit conservative bound rather than
exact unit conversion; the old8case card base is unchanged. No new blanket
review, named-department gate or synthetic queue.
General categorical actor attribution and joint/source-selection inference
remain unfinished; the units already used must not be presented as total burden.

Checkpoint22:06UTC: six timing families now consume87 component records,
including33 phone and8 physical-card records. All23 current conditions pass
numerically. The phone update replaces the old31-case component; do not add
both versions. The32-case intermediate input was never fitted. The
[integration ledger](2026-09-20-calfresh-forum-model-integration.md) tracks actual
source use, current gaps and the source-bound results. Root adopted the16-claim
semantic resolution with causal actor explanations kept hypothetical. Sol
workers are finishing215 clock-routing and47 qualitative-use rows plus updated
source accounting. These are finite pending-use queues, not a945-thread reread.

Checkpoint21:39UTC: all five conditional clock families now have actual terminal
fits:31 phone,28 interview,6 benefit-availability,9 SAR7 and3 recertification
records. All19 prespecified marginal fits pass numerical gates. These are77
component records, not77 independent people or an additive burden total. The
[additional-clock results](2026-09-20-calfresh-additional-forum-clocks.md) explicitly
flag sparse samples, censoring and prior-sensitive spreads. The original
seven-fit results also passed a later independent numerical/provenance review.
The structural inventory has been adopted descriptively, and all60 rows in the
remaining descriptive queue now have uses or explicit dispositions. Current
work consolidates actual source use, card-access evidence and remaining clocks;
it does not reopen a generic945-thread verification queue.

Latest inference update: the [marginalized V6 successors](2026-09-20-calfresh-case-marginalization-results.md)
fit the same31 phone and28 interview cases with all seven conditions passing.
Two sampled coordinates replace68/62 without changing priors or case intervals.
The earlier failures below are preserved. Root and an independent Sol reviewer
checked the bounded marginal-target implementation; real-fit summaries are
root-checked, not a new source audit or population calibration.
The [remaining-use plan](../runs/three_family_20260920/calfresh_forum_remaining_use_plan_v1/README.md)
now separates genuinely pending evidence work from already completed descriptive
use. Sol workers are preparing benefit-availability and SAR7/recertification
clocks and a source-grounded structural-demand inventory. No new blanket reading
queue, synthetic prerequisite or named-department gate.

Checkpoint20:50UTC: all945 captured threads are reviewed and explicitly
dispositioned. The [source-use index](../runs/three_family_20260920/calfresh_forum_source_use_v2/README.md)
links actual factors to source claims:31 phone-queue cases and28 interview cases
are in terminal fits. These supersede the respective17-case inputs below; one
case contributes two distinct clocks, not two independent applicants. Phone has
two numerical passes/two failures; interview has one pass/two failures. All
conditions remain visible, with no passing sensitivity promoted to base.
Descriptive analysis uses40 count facts and20 structural facts separately.
The index has776 effective review items, including21 new initial-thread items;
these include dependent fragments, not776 independent measurements. Its718
items outside current likelihoods are not718 mandatory future numeric factors:
some already have descriptive uses. Remaining work is to distinguish those
completed uses from actual integration work, then consume supported other clocks
and structural evidence. Full-scope cross-source overlap is also being assessed.
There is no further blanket reading queue or named-department gate.

Historical checkpoint20:16UTC: root replayed1,810 manifest bindings for sealed fullread
batches001–020 and their exact disjoint original rank1–777 union, with no
remaining hash mismatches. **All945 logical threads have source-review receipts;
source-to-use integration is not complete.** The consolidation also checks for
additional captured comments absent from the original143-thread review. **The
expanded administrative fit still contains46 administrative factors and0
forum factors.** Reading progress is not fitting progress. The separate
[conditional claimant successor](../runs/three_family_20260920/calfresh_forum_interview_pending_v2/README.md)
has155 candidate labels dispositioned for this particular clock and **17 unique
case clocks actually consumed** by V6:12 completed encounters and5 historical
pending cases. All three prespecified conditions completed and passed numerical
gates; saved likelihoods replay exactly. Its
[results and source-to-input trace](../runs/three_family_20260920/calfresh_forum_interview_pending_v2/analysis_v1/README.md)
remain conditional on selected reports, not joint source-bias calibration.
The original10 cases overlap this successor; do not add them to obtain27.
The separate [phone-queue-exit component](../runs/three_family_20260920/calfresh_phone_queue_exit_compiler_v2/compiled_preflight_v1/analysis_v1/README.md)
also consumed17 cases, in four numerically passing conditions. Its clock ends
at answer, abandonment or disconnection; ongoing holds remain lower bounds.
It is not successful-contact time, active labor or a population estimate.
These two components are not a joint posterior or additive total burden.
Other clocks, structural/count uses and categorical actor identity remain
integration work. Most reviewed evidence still has not entered a fit.
Use the mandatory fullread020 semantic replacement, including the corrected
by-September30 lower-bound direction; the original sealed receipt is provenance,
not permission to reuse superseded semantics.

Alex reiterated "why not? don't lose track of this" on2026-09-20. The gap is
unfinished semantic compilation and coverage, not a rule that forums require
named departments or an administrative match. Every captured thread must reach
a traceable model use, other supported analysis, or a specific disposition;
not every thread contains a valid independent numeric observation. A blanket
fit_ready=false or unmatched label is not a final disposition. The
[integration record](2026-09-20-calfresh-forum-model-integration.md) remains on
the critical path until this source-to-use accounting is complete.

For every future checkpoint, report these columns separately: captured threads,
fully read threads, unresolved claim mappings, compiled claims, **claims in
actually launched fit inputs**, and qualified uses outside likelihoods. Never
substitute an extraction/verification count for the last two. The remaining
forum queue and pending-case/categorical-identity support stay required even
after this first small component runs.

Use disjoint complete-thread batches of approximately40, packing future batches
by text size where appropriate without splitting case context. Sol handles one
substantive parsing pass; scripts replay quotations, schemas and hashes. Root
reviews consequential ambiguities and targeted samples, not a second full parse
of every unchanged row. The first40 unread IDs are frozen in
`calfresh_claimant_fullread_001/selection_freeze.json`; other workers take the
next disjoint40 slices after their bounded in-flight tasks. All ranks refer to
the frozen source ledger's unread selector, sorted by `logical_key`.

Consume accepted same-clock cases as batches arrive; do not wait for all945
threads, another synthetic corpus or identified source bias. Conditional reported-
case distributions and structural/effort/count observations have their own
declared use. Population generalization, ambiguous clocks and case duplication
still require honest treatment. Every source ultimately receives a supported
use or specific reason it does not inform a model quantity. Merely increasing
the reviewed-thread count does not complete this work.
