# Process-structure posterior: review and first implementation

2026-09-21. Response to Fable's
[process-structure posterior plan](2026-09-21-process-structure-posterior-plan.md).
This work order supersedes the county-hierarchy extension proposed earlier in
the night. Scope: real CalFresh and concealed carry; Solar and synthetic work
remain with Claude. No new retrieval. The final Joint47 attempt and its postfit
analysis have finished; failures are retained, with no further sampler attempt.

## Current checkpoint: logical support completed, 12:30 UTC

**13:00 UTC closeout:** the supported-result assembly is now generated at
`runs/process_structure_20260921/calfresh_phase5/supported_result_v1/`.
It contains all nine expanded-inventory conditions, separate applicant-facing
and agency-only counts, current clock/result links, repeats and source metadata.
It is not a complete joint burden posterior. Start with the shorter
[results and next-decision note](2026-09-21-calfresh-process-results-and-next-decision.md).
The next step requires a choice between targeted evidence collection, an
explicitly assumption-driven full model, or accepting this partial result and
moving to concealed carry. That question has been sent; no new work order is
inferred from the completed reporting artifact.

The two predeclared receipt-implies-filing fits and their analysis have finished.
Both pass the numerical gate (maximum R-hat 1.0072, minimum bulk ESS 1,023),
with no retry, gate waiver, additional observation or hard presence anchor.
All 613 input reading cells are unchanged from the matched administrative
controls. The normalized constraint is a modeling assumption about the meanings
of these two actions, **not evidence that all applicants take the same path**.

| Reused eight-account development comparison | Brier, lower is better |
|---|---:|
| Pooled forum-by-action Beta baseline | 0.06066 |
| Administrative input, no logical constraint | 0.07257–0.07266 |
| Administrative input, receipt implies filing | 0.07213–0.07220 |

The tiny improvement does not reverse the baseline result. These are the same
153 previously scored cells, not fresh validation, an LLM comparison, or a
test against latent process truth. Both conditions remain reported; none was
selected as the winner. Whole-episode prediction integrates aligned joint
inventory draws, preserving dependence between the constrained actions.

Every retained draw satisfies the declared implication. Filing-absent inventory
mass falls from roughly 8% to 0.023% or 0.131%, depending on the source-error
assumption. **That reduction is substantially imposed by the constraint**, not
an empirical recovery score. Residual mass is retained. An available filing
action still supplies neither case participation nor a complete route.

The county-effect block removes only about 9.1–9.2% of its marginal prior
variance on average. It is not an identified agency-capability result. Example
available-action counts are Alameda 8.18–8.27, Los Angeles about 16.69, and
Sacramento 8.69–8.82; these are not mandatory steps or county burden rankings.

The frozen fits and terminal analysis live in
`runs/process_structure_20260921/calfresh_phase2/logical_support_development/`.
The analysis summary SHA-256 is
`a29e8cec4b98e398a5e49e1238dcfff77812c9868dc48ee0e7def12a1ef4cc12`.
The pre-fit [methods note](2026-09-21-calfresh-logical-support.md) is unchanged.
The current full test run passed **2,362 tests** in 106 seconds; these are
engineering checks, not a claim that the statistical goal has been met.

**The full CalFresh goal is still unfinished.** Remaining work is to assemble
the supported step-level findings and expose the exact missing links to a
complete model: participation, executable ordering, and per-operation clocks.
Further prior tuning on these same eight accounts would not constitute new
validation. No new retrieval, forum queue, timing fit, Joint47 retry, Solar
work or synthetic generation has been started.

## Earlier checkpoint: fresh-account failure and operational evidence, 11:55 UTC

The full CalFresh goal remains **unfinished**. There are two substantive new
results, not just verification progress.

**Fresh-account prediction fails the simple baseline again.** The frozen
expanded-inventory fits were tested without refitting on eight source-reviewed
accounts from the already-staged005–007 slices:153 cells,20 positives. The
pooled forum-by-action Beta(1,1) baseline scores0.06066 Brier; occupancy scores
0.07762(base),0.06778(low detection), and0.10461(high detection). Episode-macro
and log scores agree on the ordering. All settings and individual predictions
are retained. This is a developmental fresh-account mention check, not latent
presence truth or untouched held-out-county validation. Five whole accounts
and seven cells remain held, with itemized reasons rather than invented zeros.

This baseline is itself a simple Bayesian Beta-Bernoulli predictor. The test
compares a structural hierarchy with a simpler model of what sources mention;
it is **not** Bayesian-versus-LLM timing evaluation and does not directly score
unobserved process truth. Its negative result is a warning about the richer
observation model, not proof that Bayesian aggregation is intrinsically worse.

Status-monitoring contributes about45% of the base model's excess Brier loss:
it predicts0.691 in a Santa Clara account that does not mention monitoring,
but0.069 in each of two San Diego accounts that do. A poor county contrast,
learned from sparse selected accounts, hurts more than the statewide mean.
Source/author/boundary review, sealed inputs, scores and decomposition live in
`calfresh_phase3/fresh_episode_prediction/`.

**Existing administrative records materially inform three agency actions.**
The July2025 CF-296 workbook supports receipt, approval-decision and expedited-
service entitlement-result activity in all58 counties. Its PartA excludes
recertifications but includes newly filed reapplications, matching our adopted
episode scope—not first-ever enrollment. Exactly174 positive source readings
were added; an aggregate count of thousands is still one source reading, not
thousands of independent trials. No hard presence anchors or administrative
nondetections were added. The original439 readings are unchanged.

Four predeclared source assumptions crossed administrative detection Beta(2,2)
or Beta(9,1) with false-positive probabilities0.02 or0.10. All four fits passed,
with no retry: maximumR-hat1.0063, minimum bulkESS838. The three directly
supported actions have model-conditional presence probabilities above0.982
in every county under every setting. This is robust to those four assumptions,
not proof of calibrated trust or contemporary implementation truth. Conditional
forum detection for receipt and ES evaluation is about0.09, distinct from
whether those functions exist.

The broader count posterior also moves: Alameda's mean available action types
is8.20–8.28, versus3.71 before these records, with all other source settings
unchanged. Sacramento becomes8.74–8.80. This illustrates why empirical
operational evidence matters; it does **not** identify required applicant
steps. County effects remain weakly informed (about9–10% mean marginal variance
contraction), and roughly8% of county-draw inventories still omit filing while
containing other actions. Those states are retained, not silently conditioned
away or turned into zero-burden cases.

Inputs/source assumptions are in `calfresh_phase1/admin_operational_adopted/`;
fits and exact numerical replay are in
`calfresh_phase2/admin_operational_detection_development/` and its `analysis/`.
The methods note is `calfresh_phase2/admin_operational_adopted_note.md`.

The administrative fits also improve predictions on the **same eight previously
scored accounts**, from Brier0.07762 to0.07257–0.07266. They still lose to the
pooled baseline's0.06066; log scores agree. This is a reused-account development
comparison, not fresh validation, and no condition was selected. Labels,
exclusions and scoring cells were unchanged. Results and the frozen comparison
plan are in the fit directory's `reused_account_development/`.

Thirty source-scoped stringency facts are now adopted as descriptive metadata,
with nine other facts explicitly held and all100 source/action cells preserved.
Unknown cells are not zero. S5's interview prerequisite is approval-path-only,
not a prerequisite for every denial. The original39 facts and intermediate
corrections remain archived. See `calfresh_phase1/stringency_adopted/`.

The occupancy-to-V6 bridge still lacks reviewed participation, complete ordering,
and individual-operation clocks. A new diagnostic compatibility layer preserves
all draw mass and leaves undefined burden undefined; it is not an executable
route model or an end-to-end fit. Its source-based rationale is
`calfresh_phase2/bridge_next_step_review.md`. No intrinsic agency-capability,
operation-time or burden-share claim follows from the new administrative fit.

The full test directory now passes2330 tests, including the compatibility
utility, in96seconds. These are engineering checks, not recovery evidence. The11:33
UTC read-only synthetic watch remains unchanged: selectedS03 counts complete
245/245 but two failed verdicts; whole corpus incomplete. No synthetic job was
launched. No new retrieval, forum queue, Solar work, administrative timing-
hierarchy extension, or Joint47 retry.

Claude's shared sampler note was read. Its sparse-data warning remains useful,
but nine repeated readings are not a demonstrated universal requirement for
convergence: our collapsed58-county fits pass while retaining even zero-positive
actions. Conversely, convergence has not established predictive or structural
validity, as the two real mention comparisons above show. The earlier augmented-
sampler results and our collapsed results should not be conflated.

**12:10 UTC extension, not another timing fit.** The seven unconstrained
inventory conditions now have a completed mass-preserving compatibility
report in `calfresh_phase5/`: all supplied draws remain, and execution/burden
is undefined for all of them. The report does not substitute zeros for missing
routes. An opt-in normalized logical-support extension is now being tested,
using only receipt-implies-filing as a separately declared modeling assumption,
not58filing anchors. The original fits remain untouched. Its rationale,
mathematical target, bounded two-condition experiment and reporting limits are
in [the logical-support methods note](2026-09-21-calfresh-logical-support.md).

The existing CF296 disposition fields also reconcile in all58counties:
194534disposed=110809approved+73700denied+10025voluntarilywithdrawn.
Root replay caught and corrected old-form cell numbers in the new source-review
metadata, preserving its earlier bytes; all406values, current workbook headers
and four PDF quotes now replay. Fifty-five counties have positive counts in
all three branches; the three zero-withdrawal counties cannot be declared to
lack that branch. These are observed July2025 disposition proportions, not
future filing-to-outcome risks or representative step participation. No new
branch posterior, route weight, observation or duplicated approval factor was
added. Source review lives inside the existing `admin_operational_adopted/`
packet as `disposition_branch_review.*`.

## Earlier checkpoint: expanded inventory fitted, 11:12 UTC

The full CalFresh goal remains **unfinished**. The expanded20-action input is
now root-adopted and fitted:439 usable readings,87positive and352nondetected,
from the unchanged five local documents and eighteen forum episodes. One
ambiguous follow-up cell contributes neither positive nor negative evidence.
All original15-action readings are preserved. Two root semantic overrides are
actually consumed, with before/after/source receipts, rather than left in
sidecars. The source/contract audit is in
`calfresh_phase1/expanded_root_adoption.md` and its bound JSON/manifest files.

Four predeclared conditions completed with no sampling retry, all numerical
PASS (maximum R-hat1.0065; minimum bulk ESS1030). A first invocation failed
**before sampling** on historical compiler bindings; its exact source/driver
and failure note are archived. Historical code is now resolved by its exact
archived digest, separately from the current frozen fit implementation. Inputs,
seeds and statistical settings were unchanged by that archival repair.

| Condition | Los Angeles | Santa Clara | San Francisco | Sacramento | Alameda |
|---|---:|---:|---:|---:|---:|
| Prior-only reference |10.03|9.99|9.95|9.98|10.00|
| Forum detection Beta(2,2) |18.28|14.95|11.69|4.43|3.71|
| Forum detection Beta(1,4) |18.50|16.61|12.56|5.02|6.81|
| Forum detection Beta(4,1) |18.66|12.58|11.18|3.52|1.92|

These are posterior means of **available action types within the expanded
initial-episode vocabulary**, not required applicant steps, visits, rankings,
or a full CalFresh lifecycle inventory. The prior conditions are deliberately
retained sensitivities, not calibrated source trust or a selected best model.
They differ from the earlier15-action sensitivity settings; changes between
experiments cannot be attributed solely to vocabulary expansion. Alameda's
90% count intervals are[1,7],[2,13] and[1,4], respectively. The count
distributions come from aligned joint draws, not independent marginal products.

In the base fit, the mean marginal variance contraction is38.5% for step
locations and12.9% for county white effects. The county-scale coordinate moves,
but its contrasts can reflect source composition and narration, not intrinsic
agency capability. Unknown counties remain diffuse: the largest posterior
candidate weights range from2.1% to13.9%. No hard assignment is made.

Frozen fits live in `calfresh_phase2/expanded_twenty_actions/`; exact input/code,
draw-to-count and probability-summary replay plus identification reports are in
`calfresh_phase2/expanded_twenty_analysis/`. No scientific release or complete
joint burden fit is claimed.

The separate source partial-pooling development experiment is also terminal:
stronger pooling passed8/10county folds; weaker pooling passed1/10. Neither
condition passed its full numerical gate, so both overall score aggregates are
null. All20manifests and98input/7code bindings replayed. White-coordinate
failures concern different logit contrasts; passing probability marginals do
not establish joint mixing or justify waiving them. See
[the methods and terminal-results note](2026-09-21-detection-pooling-development.md).

Next work is bounded to existing evidence: close out already-staged forum
slices005–007 for a separate fresh-case prediction check; compile corrected
source-scoped stringency without fabricated scores; and investigate whether
positive county administrative records directly support a few actions. No new
retrieval/description queue, administrative timing-hierarchy extension, Solar
work, synthetic work or Joint47 retry. Existing administrative counts are not
being promoted to hard structural anchors without a field/era/meaning review.

## Earlier checkpoint: source pooling and expanded input, 10:50 UTC

The full CalFresh goal is still active and unfinished. The current development
comparison tests whether pooling detection across actions helps the particularly
poor staff-document predictions. Saved-draw diagnosis found that this loss was
not a product-of-marginals bug: aligned versus multiplied means differed by at
most 0.0045 on a staff reading. Holding out a staff document leaves only one
other staff reading per action, so independent per-action detection parameters
cannot use the documents' substantial cross-action agreement efficiently.

The opt-in Gaussian-logit detection hierarchy and its exact covariance,
transition, assumptions and frozen comparison are documented in
[the detection-pooling methods note](2026-09-21-detection-pooling-development.md).
The original independent-Beta implementation remains the default, with exact
seeded replay. The new comparison uses the same ten already-seen county folds,
two predeclared pooling settings, and unchanged source evidence. It is model
development, not fresh validation or a test against latent process truth.
At this checkpoint it is still running: stronger pooling has eight numerical
passes and two failures; weaker pooling has begun and also has a failed fold.
No failed-gate waiver, aggregate success claim or selected winner is permitted.
All inputs, implementation and original-baseline artifacts are archived in
`calfresh_phase3/detection_pooling_development/`.

The original held-out result also replays exactly using **its archived code**,
rather than incorrectly requiring today's implementation to match old hashes.
The new replay receipt is
`calfresh_phase3/mixed_source_prediction/root_results_replay_frozen_code.json`;
the original receipt and result are unchanged.

The five-action expansion is being adopted into a separate consuming input,
not substituted into the original 15-action fits. The existing eighteen forum
episodes and five local documents are unchanged as a source frame. Later-life
card use and years-later account checks do not become initial-case monitoring;
interview recontact does not become a second generic follow-up action; original
authors' same-episode comments do count where they supply evidence. Truly
unresolved cells are omitted explicitly using a reviewed subset contract, not
recoded as negative readings. The forum compiler now supports that contract for
both known and uncertain county identities. No new descriptive queue was opened.

The V6 linked-draw burden-table aggregator is implemented and independently
tested. It preserves route and parameter dependence, distinguishes availability
from case participation, leaves unknown fees/labor as null, and does not label
summed elapsed exposure as a parallel process clock. It is diagnostic-only;
there is no real complete joint burden-table result yet.

The full repository test directory passed **2,284 tests in 97 seconds**, followed
by 30 focused checks covering the newly extended forum/subset compiler. These
are engineering checks, not evidence of calibrated scientific recovery.

## Earlier checkpoint: count component and integration, 10:20 UTC

The full CalFresh goal remains unfinished. The substantive new result is a
source-bound **completed-positive repeat-count component**, integrated into V6
without turning a selected complaint sample into population risk. One original
account, `1uqglol`, says paperwork was redone three times before approval. Its
duplicate is not counted again. The precise underlying action and initial-versus-
renewal lifecycle are unresolved, so this is a coarse paperwork-redo family,
**not** an executable `correct_information` repeat block.

Conditional on a positive completed episode, the existing hurdle-geometric law
reduces to `P(K=k | K>=1,r)=(1-r) r^(k-1)`: the hurdle probability cancels.
The ordinary V6 `Beta(2,3)` continuation prior becomes `Beta(4,4)` for this one
exact K=3 report under no additional severity selection. Its posterior mean
continuation probability is 0.50, with a 95% interval [0.184,0.816]. The
posterior mean expected additional rounds **given a positive episode** is 2.33,
with a 95% parameter interval [1.23,5.43]. These are not prediction intervals
for the count in a new case, and not the risk/mean across all applicants.

All three predeclared reporting sensitivities are retained, with no selected
winner. Weighting reports with K>=3 by 2x or10x changes the posterior mean
continuation probability to0.479 or0.425, and the posterior mean conditional
expected additional rounds to2.21 or1.95. This is a sensitivity assumption,
not learned/calibrated selection. Adaptive quadrature and independent rejection
draws agree within the frozen tolerances. Full source/config/code snapshots,
draws and results are in
`runs/process_structure_20260921/repeat_blocks_phase4/positive_count_component_v1/`.

V6 allocates just one continuation coordinate per such family, appends it after
the historical layout, and evaluates the factor once regardless of route/path.
It allocates no hurdle, case-duration or source-offset coordinates for these
rows, and it cannot change executable visits, time, labor or fees. Explicit
cross-factor case/group overlap and factor-key collisions are rejected. The
runner checks source hashes and literal quotes. The separate marginal timing
reducer rejects this extra evidence rather than dropping it. Independent review
and same-factor comparisons are in `repeat_blocks_phase4/root_integration_review.*`.
This is one new real component, **not a complete joint process-burden fit**.

The conditional step-burden reporting utility has passed independent tests
(`calfresh_phase2/step_burden_review.*`). It preserves joint-draw dependence,
repeat-weighted work/fees, unknown channels and serial-versus-parallel clock
attribution. It does not establish that the real evidence identifies those
quantities. Optional reviewed-subset checklists now let a vocabulary expand
without converting unread new steps in old forum reviews into nondetections.
An independent review found and fixed omitted lineage-reference hash checks;
the original finding and follow-up receipt remain under `occupancy_phase2/review/`.

The 15-action pilot remains a bounded inventory, not the promised observed
union. In particular, generic applicant progress follow-up/escalation was not
represented by its specific interview-rescheduling action. A fixed additional
checklist on the same five local documents and eighteen adopted forum episodes
is in progress, with no new queue/retrieval. Copy offers, verification assistance,
attestation fields, document counts and failed attempts are being reconciled as
attributes/subtypes where appropriate, not automatically promoted to new steps.
Unknown ordering/participation, coarse-clock-to-action mapping and source
calibration still prevent a complete, empirically supported burden posterior.

## Earlier checkpoint: held-out mixed-source result, 09:55 UTC

The ten-county source-mention experiment is complete: all ten folds passed the
predeclared numerical gate, with no retry, in 529 seconds of sampling. The
occupancy model again loses to the source-type-specific mention baseline.

| Method | Brier score (lower is better) | Mean log loss |
|---|---:|---:|
| Hierarchical occupancy/detection | 0.14646 | 0.45890 |
| Beta mention rate by step and source type | **0.11848** | **0.39033** |
| Beta mention rate by step, ignoring source type | 0.16315 | 0.50903 |

These are 210 checklist readings in fourteen source groups over ten held-out
counties, **not 210 independent truths about process presence**. All eight
uncertain-county episodes were excluded whole from each training fold because
their candidate sets included its test county; no candidates were removed or
hard-assigned. The fixed vocabulary was reviewed before this test. There is no
LLM baseline or latent-presence recovery result here.

By source type, occupancy's Brier scores are 0.0871 (forum), 0.1797 (public
guides), and 0.4099 (staff policy); the source-specific baseline scores 0.0814,
0.2444, and 0.1778 respectively. The large staff-policy loss matters: the sparse
source model is not reliably distinguishing an action's absence from a source's
failure to mention it. This is a diagnosis consistent with the prior-sensitivity
results, not proof that the decomposition is uniquely identified or a reason to
pick a better-looking prior after seeing the held-out answers. Further model
changes against these same folds are development comparisons, not fresh tests.

Results and frozen inputs/code are in
`runs/process_structure_20260921/calfresh_phase3/mixed_source_prediction/`.
`inspect_mixed_prediction.py` replays saved predictions, baselines, scores and
hashes; it does not refit or change the completed experiment.

The downstream evidence-partition preflight found four applicant histories and
five timing facets shared by the adopted occupancy sample and Joint47: 43 of47
timing cases and56 of61 facets have no explicit overlap at the current registry
scope. These are registry checks, not proof of person-level independence. The
follow-up `1k7qx6o` belongs to the `1k4thai` episode, not a new independent case.
Every overlapping clock measures elapsed time between coarse boundaries; none
measures one detected action's duration. Nothing was excluded or refitted.
See `calfresh_phase2/evidence_partition_preflight.{json,md}`.

The V6 bridge now preserves full empirical inventory support through reviewed
many-to-one route mappings and checks aligned replay. A conditional step-burden
reporting utility was then under independent review: availability versus participation,
repeat-weighted resource means, explicit unknown costs/labor, and clock shares
only for provably serial schedules. These mechanics do **not** make a real
joint CalFresh burden fit complete. Action-union reconciliation, executable
conditional paths, source/selection calibration and usable count evidence remain
substantive work. No intrinsic agency-capability or complete-burden claim is
released. No new retrieval, synthetic work, or Joint47 retry has been started.

## Earlier checkpoint: mixed-source results, 09:30 UTC

The six corrected mixed-source conditions are complete and all pass the
predeclared numerical gate (maximum R-hat 1.0083; minimum bulk ESS 680).
Results are under `runs/process_structure_20260921/calfresh_phase2/mixed_sources_corrected/`.
The complete conditions took about seven minutes of sampling in total; two
unsaved attempts additionally failed at JSON output, not in inference. The
NumPy-boolean serialization error, preserved receipts, and serializer-only
continuation are documented in that directory's `SERIALIZATION_FAILURE.md`.
The production reporting field is now fixed, with a strict-JSON regression.
The frozen statistical code used for these fits remains archived exactly.

The model is incorporating forum evidence, including the eight episodes with
uncertain counties. It is **not learning their locations precisely**: in the
base all-forum condition the largest county probabilities range from 2.8% to
10.5%, with entropy-equivalent candidate counts of roughly 49–57 counties.
Those remain distributions, not hard assignments.

More importantly, the step-count result is not stable to defensible source
assumptions. Examples below are posterior **mean available action-type counts
within the fixed 15-action initial-decision vocabulary**, not required steps
per applicant, rankings, or a complete process inventory.

| Condition | Los Angeles | Santa Clara | San Francisco | Sacramento | Alameda |
|---|---:|---:|---:|---:|---:|
| Official only | 14.72 | 13.77 | 11.22 | 4.74 | 8.07 |
| Known-county forum added | 14.52 | 12.23 | 9.84 | 4.58 | 4.04 |
| All forum, uncertain counties integrated | 14.38 | 11.99 | 9.17 | 4.59 | 4.18 |
| All forum, low-detection prior | 14.48 | 12.96 | 10.24 | 5.51 | 8.48 |
| All forum, high-detection prior | 14.43 | 11.74 | 8.81 | 4.25 | 3.36 |

Alameda's change from about three to eight actions illustrates the unresolved
availability-versus-narration confounding. Sparse applicant accounts cannot be
treated as exhaustive journeys. Neither numerical success nor narrower
intervals establishes calibrated structure or intrinsic agency capability.
The next real check is a county-held-out **source-mention** comparison, excluding
any uncertain episode whose candidate set could contain the test county.
It will not be labeled a latent-presence truth test.

The existing V6 joint-inventory bridge now has independent target/runner tests,
an explicit floating-point support-loss guard, aligned upstream-draw replay,
and a finite empirical-support concentration diagnostic. Replay uses one
upstream draw for its hierarchy, detection, presence and identity together.
The finite prior preserves supplied Monte Carlo draws, not all possible
continuous-posterior mass. A reviewed many-to-one inventory-to-route mapping is
being added so replay cannot confuse raw inventory IDs with aggregated V6
hypothesis IDs. No real joint burden fit has yet been run.

Source work is now directed at the gaps needed for that handoff, not a new
retrieval queue: the omitted agency expedited-service screen, conditional
assistance/notice actions, actual count denominators and duplicates, and the
relationship between available actions and executable case paths. All 13
previously enriched-only count rows were traced to their original sources.
The paperwork-redo claim appearing in two records is one household observation;
it must not become two independent likelihood factors. Staged forum slices
005–007 have an independent semantic review but are not silently added to the
completed 120-thread experiment. Full CalFresh remains unfinished.

## Earlier checkpoint: forum integration and joint inventories, 09:10 UTC

The full CalFresh goal remains active and unfinished. The completed county-only
pilot and source-prediction results below are preserved; their exact consumed
code, sources and configurations are also copied into
`calfresh_phase2/reproducibility_snapshot/` (38 files).

An optional categorical jurisdiction variable now assigns **one county to an
entire reviewed forum episode**, jointly across its step checklist. It does not
require a named internal department. Unknown counties retain all 58 registry
candidates under an explicitly uncalibrated symmetric sensitivity prior; no
other commenter's location or subreddit becomes a hard county label. The Gibbs
conditional multiplies the whole episode's likelihood, not independent county
guesses per step. Source-bound candidate context, canonical episode ownership,
complete checklists and quotation replay are checked before admission. Both
sampled county indicators and conditional county probabilities are diagnosed.
The independent two-county/two-step Gaussian/shared-Beta enumeration agrees with
joint sampler draws; legacy known-identity draws reproduce exactly. See
`occupancy_phase2/review/identity_extension_review.md`.

The first four uniform forum-reading slices cover exactly ranks1–120 of the
outcome-independent 945-thread frame. A consuming root-adoption compiler now
applies the itemized semantic corrections, instead of leaving them in an unused
sidecar. Root rejected two hard county labels, restored a representative's
filing, distinguished intended from submitted withdrawal, and held unsupported
prefiling/notice/verification interpretations. Independent full-source review
of all19 initially admitted episodes then found two missed root-author comment
actions, one missed filing, and one unresolved initial-versus-renewal lifecycle.
Root checked and corrected those findings too.

The corrected consumed input has **18 episodes:10 known county and8 uncertain**,
270 forum readings with44 positives. Together with the unchanged county panel
it has330 readings,77 positives,253 nondetections and no truth anchors. The
original mixed experiment was stopped during its third condition; two completed
numerical-PASS outputs and their original code/evidence archive remain under
`calfresh_phase2/mixed_sources/`, with a `STOPPED.md` receipt. They are not
released results. The same six conditions/seeds are running on corrected data
under `calfresh_phase2/mixed_sources_corrected/`; this is a declared source-data
correction, not a numerical retry. The source-review receipt is
`occupancy_phase2/review/calfresh_forum_admission_review.md`.

Uniform checklist reading has reached228/945 captured threads in worker
staging; only the corrected first120-thread slice is in this experiment. All945
had earlier general reading reviews; the new pass supplies the complete
action-detection denominator those positive-claim ledgers lacked. Later slices
are not automatically adopted. A captured narrative is not a completed journey:
forum detection combines participation, observation before posting, and mention.
The fit does not separately identify these factors or reconstruct current policy
from mixed historical eras.

V6 now has an optional **finite joint inventory prior**, currently source-free
tested and awaiting independent review. It preserves cross-program inventory
dependence and updates the whole structural vector in one exact Gibbs block.
Per-program marginal route weights must be neutral placeholders when this is
enabled, so the same inventory prior cannot be multiplied twice. Full upstream
inventory draws can be compressed without discarding supplied empirical mass or losing their draw
membership. This is an interface to the existing V6 model, not occupancy inside
V6 and not a new alternative architecture. It still requires reviewed executable
routes, case participation, ordering and a non-overlapping evidence partition.
No real occupancy-to-V6 burden fit has been claimed. Timing evidence is permitted
to update joint inventory weights under the explicitly declared feedback policy;
that is not a cut posterior with frozen structure probabilities.

The remaining substantive work is unchanged: expand the observed action union
beyond the bounded15, adopt count meanings and lifecycle/observation windows,
attach stringency and timing to compatible routes, check identification and
source/prior sensitivities, then report only supported burden channels. Unknown
cost, labor and intrinsic capability must not be reported as measured zero or
as well-identified posteriors.

## Earlier checkpoint: first real CalFresh occupancy fits, 08:30 UTC

The first **bounded real-document fits are now complete**. The full CalFresh
process model is not complete. Results and scripts live in
`runs/process_structure_20260921/calfresh_phase2/`; the separate four-fold
source-prediction experiment lives in `calfresh_phase3/`.

The root-adopted pilot has 15 explicitly defined initial-decision action types,
five captured county documents, and four independent publisher groups. SF's two
related pages are unioned once per action. This yields 60 reviewed county/action
readings: 33 detections and 27 nondetections, **no independent repeated readings
per cell and no truth anchors**. The observed-positive counts (LA14, Santa
Clara11, SF6, Sacramento2) are document-description counts, not known process
sizes. Internal agency actions are separated from applicant/joint actions.
The universe is deliberately bounded: additional observed actions, notably
expedited-service screening, remain to be incorporated before claiming complete
initial-process coverage. Renewals and other lifecycle branches are not in this
pilot. Effective policy eras remain unresolved; the target is captured-source
process description, not verified contemporaneous county practice.

Seven of eight predeclared sensitivity/prior conditions passed the numerical
gate. Four chains ×1,000 warmup +4,000 retained draws took 5.5–9.5 seconds per
condition. The narrow county-scale condition failed bulk ESS (386.7, threshold
400); it is preserved and **not waived or retried**. The base condition had
maximum R-hat1.0043 and minimum bulk ESS870. Numerical success is not scientific
validation. Expected total action-type counts change substantially with the
detection prior:

| County | Base Beta(2,2) | Low detection Beta(2,8) | High detection Beta(8,2) |
|---|---:|---:|---:|
| Los Angeles | 14.73 | 14.80 | 14.46 |
| Santa Clara | 13.78 | 14.43 | 12.34 |
| San Francisco | 11.21 | 13.32 | 7.53 |
| Sacramento | 4.79 | 9.27 | 2.73 |

These are **diagnostics of prior sensitivity, not released county rankings**.
The base 90% intervals are LA[14,15], Santa Clara[12,15], SF[7,15],
Sacramento[1,10], within the supplied 15-action universe. Source genre and county
are confounded: the detailed staff handbooks and short public guides differ
systematically. The fitted county effects can contract substantially while
absorbing document-detail differences; this is not intrinsic agency capability
or proof of identified county complexity. Per-block contraction/mean-shift
reports and all posterior draws are saved with each condition.

A separate leave-one-county-source-group-out experiment predicted **mentions in
held-out documents**, not latent action presence. All four folds passed the
numerical gate. Lower scores are better:

| Method | Brier | Mean log loss |
|---|---:|---:|
| Occupancy, base assumptions | .2950 | .7915 |
| Beta(1,1) mention rate by step and source type | .2111 | .6134 |
| Beta(1,1) mention rate by step, pooled source types | .2693 | .7454 |

This comparison has four source groups, not 60 independent jurisdictions. It
conditions on the vocabulary already reviewed from this corpus; it is not a
blind step-discovery benchmark, a latent-presence validation, or an LLM
comparison. It shows that the richer decomposition has not earned a predictive
advantage on this panel. No baseline or prior was selected using these held-out
results and then relabeled as a preregistered winner.

The computational improvement is an **optional same-target partially collapsed
Gibbs/ESS update**, not another model architecture. Hierarchy moves integrate
unanchored presence exactly, then redraw presence before the Beta detection
update. Smaller ESS blocks are configurable. Defaults remain unchanged. Exact
binary enumeration and independent Gaussian-quadrature/shared-Beta checks agree
with both kernels; Sol's review passed under
`occupancy_phase2/review/collapsed_transition_review.md`. These checks do not
prove real-data identification. Shared-workspace input/code hashes are bound
and rechecked by each real experiment.

Applicant evidence is being compiled against a mention-independent frame of all
945 captured threads, not the seven previously positive-selected accounts. The
first fixed-hash 12-thread tranche found three county-supported initial episodes
and one otherwise relevant county-unresolved episode. Its source-bound readings
remain staging, not silently included in this document-only fit. Ranks13–84 are
in progress with Sol/Luna. All945 already had general source reviews; this work
adds the uniform action-detection denominator that those positive-claim ledgers
did not supply. Missing department names alone do not exclude an episode.

Next: integrate reviewed applicant readings with explicit source/stage/era and
identity uncertainty, expand the action union, resolve repeat-count subjects,
and connect compatible inventories to V6's timing/repeat model without turning
conditional action availability into mandatory case participation. Preserve
joint draws and declare evidence reuse/feedback at that interface. No claim of
good full-process, step-count or agency-capability posteriors is yet warranted.

## Verdict

The direction is right: infer the presence of actions under imperfect source
detection, carry joint inventory uncertainty into the process model, then attach
repeat, timing and cost evidence to those actions. Retain the observed union
across statutory, agency and applicant sources. A statute-only inventory misses
the very implementation burden the study is about.

The implementation needs the following corrections before the plan's outputs
can be called validated process posteriors:

1. **A valid probability link and sampler.** `Bernoulli(psi[s] + u[j])` is not
   generally a probability. Use `logit Pr(z[j,s]=1) = alpha[s] + u[j]`. With
   Gaussian hierarchy effects this is not wholly conjugate Gibbs. The first
   implementation uses Gibbs for presence/detection and elliptical slice
   sampling for Gaussian-white hierarchy coordinates.
2. **Reading opportunities, not one source-type cell.** Preserve repeated
   document/case reading units and their dependence groups. One positive claim
   repeated in five quotes is one detection, not five independent surveys.
   A missing source is no observation; reviewed nondetection is a possible zero;
   neither is known absence. A positive-only extraction ledger does not supply
   the denominator needed to estimate detection.
3. **False positives and calibration.** A detection in an imperfectly labeled
   ledger cannot automatically force presence to one. The first pass accepts
   explicit source-type false-positive sensitivities. These are not inferred
   from the earlier overall semantic error rate, which measures a different
   event. Independent truth anchors cannot reuse a detection's source support.
   Occupancy models rely on repeated detection histories, and allowing
   misidentification changes the inference materially; see
   [MacKenzie et al. (2002)](https://ecologia.ib.usp.br/ecopop/lib/exe/fetch.php?media=mackenzie_etal_2002.pdf)
   and [Miller et al. (2011)](https://pubs.usgs.gov/publication/70036361).
4. **Scope and meaning.** Presence means an implementation contains an action
   within the declared lifecycle/era. It does not mean every applicant must do
   it. Initial applications, renewals, modifications, denials and rework cannot
   be pooled into one required-step count. Unknown jurisdiction stays unresolved,
   not a fabricated statewide jurisdiction. Thirteen CalFresh headings are
   categories, not proof of exactly thirteen indivisible actions.
   The counting granularity must also be fixed: a training/evaluation bundle
   and its component actions cannot both be counted as independent extra steps.
   A survey's "not required" answer is not necessarily absence of a conditional
   action. Reference labels must match the presence estimand, or a separate
   required-step target is needed. An explicit negative assertion is also not
   automatically the same observation mechanism as failure to mention a step.
5. **Source layers are descriptive.** "Seen only in agency documents" does not
   prove a county added a legally unauthorized requirement; the statutory review
   may be incomplete or delegation may exist. Applicant-only does not establish
   absence from all possible agency records. The observed union is not proven
   complete, and no report of an unobserved step does not imply no burden.
6. **Do not multiply marginal means or unlike units.** Compute rounds × time
   and shares within linked joint draws. Time, money, documents and obstacles
   remain separate dimensions unless explicit valuation weights are supplied.
   Parallel elapsed durations do not add to the process clock. A regression on
   point estimates would also discard posterior uncertainty.
7. **No evidence double use at the handoff.** Presence-derived inventory weights
   may enter V6 only with a declared evidence partition. Reusing the same quote
   as an independent occupancy detection and a second structural/count factor
   can duplicate information. A modular posterior handoff needs its feedback
   policy stated; fixed plug-in weights are not automatically a full joint
   posterior over detection, inventory, repeats and timing.
8. **Validation must be specific.** Solar requirements are reference labels for
   their stated fields/eras, not universal process truth. Hold out the reference
   labels and their derivatives, retain other test-jurisdiction documents, and
   separately test hierarchy-only new-jurisdiction prediction. Score probabilities
   with Brier/log scores and calibration; covering a binary answer with a broad
   interval is not a useful recovery gate. Performance on a few requirement
   fields does not automatically validate all applicant-only steps.

## What is implemented now

[Occupancy implementation](../pipeline/procbench/process_structure/occupancy.py)
is outside V6. For a fixed reviewed scope and observed step universe:

```text
alpha[s] ~ Normal(0, step_logit_sd²)
tau      ~ LogNormal(log(jurisdiction_scale_median), scale_log_sd²)
u[j]     ~ Normal(0, tau²)
z[j,s]   ~ Bernoulli(logistic(alpha[s] + u[j]))
p[s,k]   ~ Beta(a[k], b[k])
y[j,s,r] ~ Bernoulli(p[s,k(r)]) if z[j,s] = 1
           Bernoulli(f[k(r)]) otherwise
```

Here `r` is an independently reviewed reading opportunity and `k(r)` its source
type. `f` is a declared false-positive sensitivity. Independent reviewed presence
or absence anchors can clamp `z`; they are not inferred from silence. Binary
presence, detection probabilities and hierarchy coordinates are jointly sampled.
Joint presence draws, rather than products of marginal probabilities, yield
the step-count distribution and empirical inventory masses.

The evidence contract rejects unresolved model identities, dependent duplicate
readings, reused truth/detection support, unreviewed nondetections, and inconsistent
zero-error claims. Source hashes are checked by the command-line runner; semantic
review remains a separate requirement. The sampler emits convergence diagnostics
for the hierarchy, detection, cell probabilities and counts. Failed diagnostics
do not become accepted results. Successful diagnostics do not establish scientific
validation either: `scientific_validation_complete` and `scientific_release_eligible`
remain false until the external validation/sensitivity protocol is completed.

The command-line runner binds the input/configuration/code bytes consumed before
sampling, and checks those bindings and source hashes again before saving results.
A shared-workspace edit cannot silently relabel draws as a fit of revised inputs.

[Held-out validation helpers](../pipeline/procbench/process_structure/validation.py)
now provide an outcome-independent jurisdiction split, two distinct experiments
(withhold reference labels while retaining other local evidence; or withhold all
local evidence), and removal of declared reference-source derivatives. They
require explicitly reviewed lineage; they cannot discover undeclared copies.
Declared aliases are resolved against the fit's source root, and byte-identical
copies are withheld by SHA-256 as well as path. The independent reviewer caught
and verified the repair of the original raw-path-only exclusion.
The scorer requires exactly matching reference cells and reports Brier/log loss,
both per-cell and equally weighted by jurisdiction, plus calibration-bin support.
Impossible predictions retain infinite log loss rather than being silently
clipped. Observed-only and smoothed training-reference prevalence baselines use
the same reference cells and do not read test outcomes. These are implemented
evaluation tools, **not completed real held-out validation**.

**First-pass limitations:** detection probabilities pool across jurisdictions
within each step/type, but their Beta hyperparameters are fixed. Learning a
cross-step source-detection hierarchy is not implemented. Calibration on one
step therefore does not yet learn detection for a different step. False-positive
rates are not learned. Dependence among distinct steps within a source, uncertain
jurisdiction, step-identity merges, era changes and inventory prerequisite
constraints need further modeling/reconciliation. Beta shapes below one are
currently rejected to avoid endpoint-underflow behavior; values are not clipped.
No real family has yet passed a held-out occupancy validation.

The proposed shared
[step-burden table and joint-inventory output](../pipeline/procbench/process_structure/burden_table.py)
keeps unestimated quantities null rather than zero. It will not produce a
scientific table from an unvalidated posterior. Inventory masks are not labeled
executable V6 routes until identity/order/lifecycle checks exist. Cross-family
schema agreement is **pending Claude's confirmation**, not claimed complete.

## Repeat blocks: the planned rewrite is unnecessary

The current V6 already supports multiple independent repeat blocks with separate
keys, hurdle/continuation parameters and case uniforms. The
[two-step regression and audit](../runs/process_structure_20260921/repeat_blocks_phase4/README.md)
checks independent count/rate effects, visits, serial elapsed time, per-visit fees,
expected fees and variance. Its focused/adjacent suite passed 76 tests.
Nested and visit-interleaved repeats remain unsupported. No frozen V6 code was
changed and no redundant repeat engine was introduced.

## Real evidence and execution boundaries

One packet per phase/family, under `runs/process_structure_20260921/`:

- `calfresh_phase1/`: action candidates, document/case units, detections, raw
  stringency features and native count pointers, from already reviewed evidence.
- `ccw_phase1/`: the same interface, retaining initial/renewal/modification scope
  and all observed agency/applicant activities rather than the agency 21 alone.
- `occupancy_phase2/`: source-free mathematical checks and independent review;
  no new rendered synthetic corpus or real recovery claim.
- `repeat_blocks_phase4/`: audit/regression for existing multi-block support.

The CalFresh graph/count candidate packets prepared earlier receive root review
in place; no successor chain or new descriptive queue. Reference counts such as
56 contacts or 40 phone-failure mentions are not applicant repeat observations.
Real count units, observation windows, dependence and completeness must survive.

The unrun county-scale importance extension and CF18/native-unit extension are
deferred. Their files remain preserved; the overdispersed histogram module is
unconnected to V6 and is not part of this first-pass result. The final Joint47
attempt finished at 07:22:55 UTC. The equal-path-weight condition passed; both
90/10 and 10/90 conditions failed their numerical precision probe
(`marginal report factor is nonfinite at requested probe`). Postfit analysis
finished at 07:25:17 UTC. The failed conditions emit no posterior conclusions.
There is no further attempt or automatic continuation.

The accepted equal-weight run has four chains of 6,000 retained states. Its
largest reported R-hat is 1.0038 and smallest bulk ESS is 1,143. Its working
lognormal median parameters are 6.83 days [3.39, 13.49] application→interview,
19.15 [5.15, 53.72] interview→observed outcome, and 46.56 [10.48, 189.66]
application→observed outcome on the direct path (90% intervals). These describe
the selected report model—not county population burden, intrinsic agency
capability, or a validated process inventory. The two phase medians cannot be
added to obtain the median total. None of the 27 ambiguous cases has an average
conditional path probability above 0.9 for either path: timing has not resolved
their structure. The path-weight sensitivity comparison is incomplete because
both alternatives failed. See the
[postfit root review](../runs/three_family_20260920/calfresh_joint47_collapsed_analysis_v1/root_review.md).

## Current input review

CalFresh preserves 19 initial-process primitive candidates and six unresolved
heading identities, not a claim of 25 canonical steps. All 220 integrated claim
rows have heading-level dispositions, not complete primitive-level resolution.
Root review corrected the count adapter: all 68 facts retain their case identity,
county context, count subject and observation mechanism; 51 have source-supported
county metadata, but none is silently marked repeat-fit-ready. Count-excerpt
metadata units are not whole reading opportunities. The 37 official-source claims
are kept separate from detections and are not independent implementation truth.

The next CalFresh extraction denominator is now fixed by the
[root opportunity protocol](../runs/process_structure_20260921/calfresh_phase1/root_opportunity_protocol.md):
all 20 frozen non-forum `source_text` documents, followed by genre/lifecycle
classification and a uniform candidate checklist within each admitted genre.
The frame includes official documents, LSNC guidance and Code for America
material; these are not all official sources and retain separate publisher roles.
The earlier four graph-selected documents and their 37 proposed candidate scopes
are not automatically an unbiased detection denominator. No nondetections or
county implementation labels are manufactured from the new source frame alone.
The [CalFresh root review](../runs/process_structure_20260921/calfresh_phase1/root_review.md)
accepts the source-bound staging packet and frame, not a fit-ready matrix: all
20 raw hashes/byte counts and 30 input/output bindings replayed; eight documents
are in the proposed uniform initial-extraction scope, with 12 explicit holds.

The CCW input audit found obsolete/untrusted ledgers in the broad file glob,
incorrect effective-episode parsing, copied reports counted under new identities,
city/county attribution errors and automatic nondetections from page headings.
Those are input defects, not evidence against the occupancy model. The repaired
packet now passes the [independent candidate/provenance review](../runs/process_structure_20260921/ccw_phase1/independent_review.md),
but the review explicitly rejects fit-readiness. All 33 input and 10 output
bindings replay. No Codex real occupancy fit has been run. Related authority
pages need reviewed dependence groups, not automatic independence, while
genuinely independent readings must remain separate.
The current CCW union contains 417 raw activity identifiers, not 417 resolved
steps. Proposed aliases still need action-boundary review: fingerprint capture
and applicant transmission of its confirmation can be a bundle; renewal intake
cannot be globally merged into initial intake; paying a fee is an action even
though a fee amount alone is not. Ambiguous mappings remain retained and visible.
Three scoped alias proposals cover seven raw IDs; 410 remain unresolved. The
bridge still must resolve 25 duplicated dependence-group/candidate pairs and
consume semantic hold fields rather than treating interval endpoints as step
occurrences. Effective episode registries remain metadata until linked to raw
measurement cases. These are specific remaining compiler/identity tasks, not
reasons to abandon applicant evidence.

Verification so far: the full repository suite passed 2,017 tests before the
four alias/copy regressions were added; the current focused occupancy/repeat/
validation/binding suite passes 51 tests. The independent validation/binding
review is sealed in the existing `occupancy_phase2/review` packet, with prior
reviews preserved. Source-free tests establish implementation mechanics, not
real-data structural recovery.

The shared scoping log now asks Claude to confirm the burden-table schema and
records the completed Joint47 result and new validation tools. Claude's new Solar
report documents failed occupancy convergence; that is not a passing real
calibration gate. Its data and runs remain Claude's responsibility. The first-pass
sampler must still demonstrate useful mixing at the intended real-data scale;
small exact fixtures alone do not establish that.

## Next acceptance gates

1. Root-review the two real Phase 1 matrices: observed union, canonical identity,
   reviewed reading opportunities, genuine negative detections, anchors,
   lifecycle/era/jurisdiction scope and source leakage/dependence.
2. Confirm the shared table schema with Claude. Establish a versioned validation
   split and baseline before occupancy fits: observed-only inventory, pooled
   step prevalence, and the detection-aware model on exactly the same scope.
3. Run bounded real fits and prior/false-positive sensitivities, report detection
   and presence identification separately, and score held-out reference labels.
4. Reconcile inventory masks with feasible V6 routes; declare the modular/joint
   evidence partition. Feed native per-step count observations into the existing
   independent repeat blocks, not claim-reference totals.
5. Attach compatible timing/fee evidence without recycling an earlier posterior
   as new data. Propagate linked uncertainty into channel-specific burden maps;
   leave unsupported step quantities explicitly unestimated.

This is a first implementation, not a completed structural recovery result or a
complete step-level burden posterior.
