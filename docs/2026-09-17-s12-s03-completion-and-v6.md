# S12/S03 completion, spot audit, and V6 handoff

Started September 17, 2026, after Alex requested finishing S12/S03, lightly
auditing existing work, and then beginning Bayesian application. The worker
initially froze the **compact** 438-document slice. That is not proof that Alex
chose the compact alternative over the planning document's full release; the
full-versus-compact scope question was explicitly sent for clarification at
22:30 PDT. This is development work, not a 58-county release or a performance
result, and 438 documents must not be reported as full unthinned completion.

## Frozen scope and method

The completion manifest is
[`runs/w2_s12_s03_completion_20260917/manifest.json`](../runs/w2_s12_s03_completion_20260917/manifest.json).
It adds each implementing county's department directory to the existing compact
statute bundle (at most four user-source documents per county/program):

| Bundle | Implementing counties | Required documents |
|---|---:|---:|
| S12, contractor registration | 15 | 186 |
| S03, sidewalk vending | 21 | 266 |
| Deduplicated union | — | 438 |

At the freeze there were 20 missing directories, 212 rendered/unverified
documents, and 206 existing passing verdicts. Fifteen existing documents are
selected for independent spot review, including official statistics, staff
reports, forum/reddit reports, ordinances, fees, forms and directories. These are
not a random sample and cannot estimate a corpus-wide error rate.

The completion worker is
[`benchmark/synth/render/complete_slice.py`](../benchmark/synth/render/complete_slice.py).
It reuses the existing public-projection packet builder and shared Codex runner.
Every render/verify call receives an inline packet in an isolated working
directory; event logs are checked for tool use. Construction/verifiers may read
the licensed specifications and private verification context. Extractors may not.
New reviews retain required-fact quotes, failures, verbatim repair instructions,
artifact/spec hashes, prompts, responses, model settings and token usage.
Repairs preserve previous document bytes under the run's `rejected/` directory.

The queue does not rebuild the other agent's shared T/V batches or replace
`render_selection.txt`. Ownership is recorded as `W2-S12-S03-COMPLETE` in the
shared scoping log. The packet-builder regression test previously regenerated a
shared input file; it now constructs its packet in memory so future test runs
cannot overwrite a live worker's input.

## Gates and provenance qualifications

The compact slice count gate requires all 438 documents plus passing verdicts
and the requested spot audit. Final release is stricter: all verdicts must bind
the current document/spec/context, and every upstream consistency/scope hold
must be resolved. Legacy unbound passes are not sufficient for release. Full
unthinned completion additionally requires its larger selected document set.
Current counts, without modifying a liveness watermark:

```bash
python3 -B -m benchmark.synth.render.complete_slice report \
  --out runs/w2_s12_s03_completion_20260917
```

The current whole-world status command has side effects and reflects a different
single-statute render selection. Neither its `state` nor a lane-level count
should be reported as this slice's or the whole world's successful completion.

Old passing verdicts generally are not hash-bound. They are reused only while
the frozen source bytes remain unchanged and the latest verdict still passes,
and are explicitly labeled `pass_legacy_unbound`. Hashing a document now does
not retroactively prove which bytes an earlier reviewer saw. The new spot
reviews reduce this uncertainty for the reviewed documents, not all documents.

Manual spot-check: `C22__S12__official_stats` preserves the reported 159-case
decision median and the 79/165 observed-correction denominator, but its front
matter is dated July 23 while its body reports figures as of September 15. The
specification itself supplies these dates. This is a chronology/provenance issue,
not a reason to convert the denominator or silently alter the planted world.
The same specification-level chronology mismatch occurs in nine selected
dashboards: S03 in C02, C08, C25, C38, C46, C50 and C57; S12 in C22 and C55.
The independent reviews and final dispositions remain to be recorded. A passing
render-fidelity verdict alone would not resolve a contradictory specification.

At 21:27 PDT all 20 missing directories had been rendered; the scoped union had
438/438 document files, with 232 unverified documents and the 15 spot reviews
still pending. Existing packet-isolation/timing-contract tests passed (16 tests);
these are software checks, not independent verification of the new prose.

The first eight-document pilot returned seven failures and one pass (the new
directory). This is a selected pilot, not an estimated failure rate for all W2.
Failures included invented application attachments, unauthorized departmental
assignments, extra operating standards, altered timing endpoints and an upstream
date conflict. Original verdicts and every quoted finding are preserved under
the run's `reviews/` directory. Repairs have not been accepted merely because a
model suggested them.

The pilot also exposed missing verifier context: DESIGN.md allows staff reports
and council minutes to restate public statutory mandates, but their packets did
not supply the statute. The shared packet builder now supplies only the document's
own public-field-projected statute under `public_statutory_context`; no local-rule
values, hidden actors, private readings or sibling statutes are added. This is
not authority to assert actual local compliance. The older council-minutes pilot
verdict must be rechecked with that context before using its legal-boilerplate
findings as a repair instruction.

Another upstream contradiction is substantive: twelve selected S03 county
implementations have an added element named **“Attend the mandatory pre-submittal
consultation”**, but its `mandatory` flag is false and the process activity is
optional. In the inspected C02 example the simulator uses `p_occurs=0.35` while
the public instructions require attendance. Counties: C02, C08, C11, C23, C33,
C36, C37, C38, C42, C45, C52 and C58. This finding required explicitly designated
development-truth inspection by the coordinator; it must not enter extractor or
fitter context. Alex approved correcting descriptions/specifications to preserve
the sampled optionality, timing values and case draws, retaining originals and
rerendering/reverifying affected documents. He also approved correcting the nine
dashboard publication dates to their stated data cutoff without changing figures.
Neither upstream correction has been applied yet; the active verification phase
must not accept a verdict against inputs changed during its review.

The S12 spot audit also confirmed that C03's structured public appeal-body choice
is Current Planning Division, while the process/specification names Zoning
Administrator. Its fee metadata says the $210 amount is administratively set
and absent from adopted instruments, while its drafting instruction demands
adoption of that amount. Those input contradictions must not be repaired by
inventing a division/officer relationship or a fee-adoption history.

## 22:00 PDT checkpoint

The saved [checkpoint](../runs/w2_s12_s03_completion_20260917/checkpoint_20260917_2200.json)
records 438 rendered documents: 191 unchanged legacy passes, 11 new hash-bound
passes, 37 failing review verdicts, and 199 pending reviews (including two remaining
spot checks). Automated failures are findings for adjudication, not automatically
confirmed bugs; generic boilerplate judgments especially need care. The bounded
verification queue is still running. No upstream specifications have been edited.

Two narrow repairs have been applied after inspection: C03/S12's form no longer
invents required uploads, payment/completeness rules or continuing notifications;
C07's fee schedule no longer asserts unsupported per-application charging and
receipt rules. All licensed amounts remain unchanged. Exact original bytes were
archived and their hashes checked against the failed reviews. Both repairs await
independent re-verification; neither was marked passing by its editor.

The existing V6 preflight, transport/provenance and packet/timing checks pass
**50 offline tests**. W2 extraction, parsing-agent launch and posterior fitting
remain unstarted. Upstream consistency decisions are required before claiming a
finished realistic corpus or releasing it as a clean benchmark input.

Completed model calls at this checkpoint used 588,538 input tokens (including
35,456 cached) and 167,880 output tokens; the separately reported 104,400 reasoning
tokens are a subset of output, not added again. The earlier completion estimate
assumed mostly reusable/passing prose and understated CLI context overhead. At
the observed pilot rate, initial verification alone makes this closer to a
3.2-million-token construction/review pass, before substantive repairs and repeat
verification. This is a revised projection, not a metered total or spending cap.

## 22:30 PDT correction and regression checkpoint

The approved date/optionality correction is staged, not yet applied, in
[`corrections/approved_dates_optionality_v1/plan.json`](../runs/w2_s12_s03_completion_20260917/corrections/approved_dates_optionality_v1/plan.json).
Its immutable before/after archive covers 183 files: twelve local rules, twelve
process descriptions, two verification contexts, 148 specifications and nine
dashboard artifacts. Only consultation labels and the nine publication dates
change. It also preserves original affected prose for the subsequent rerender.
All 979 world/case-log files covered by its protection register are hashed; apply
will reject changed inputs and requires the active completion-worker lock.
Forty-seven existing documents require rerendering and 56 require fresh review;
all are within the current compact slice. Changes to future, unrendered specs
are enumerated separately rather than silently leaving their labels inconsistent.

The generator now normalizes optional consultation names, including its alias
pool without changing seeded draws, and dates future dashboards at their cutoff
while consuming the previous random draw. This code change does **not** rebuild
the saved world. The completion runner checks the actual spec and document
context before accepting a response, can recover context hashes from retained
old input packets, and supports immutable manifest revisions and rerender queues.
The packet builder now supplies a public county name for an explicitly licensed
neighbor comparison; a verifier must not demand an internal county ID in prose.

Two additional narrow forum repairs retain archived originals and await fresh
verification: C11/S03/reddit_1 loses an invented two-encounter anecdote; C03/S12/
reddit_1 retains its noisy amounts while correcting visit-sum/decision-clock
wording and removing invented payment/history claims. These are not new passes.

The full offline command `python3 -B -m pytest tests
benchmark/synth/generator/test_generator.py -q -p no:cacheprovider` passed
**482 tests**, with one existing warning about a test returning a non-None value.
The six correction checks include seeded non-label-field invariance and stale
review rejection. These tests do not certify corpus prose.

The requested world status check still reports `observed.complete_by_counts:
false`; its selected lane remains S03, not the union or full release. Verification
session 57070 remains live. Two policy questions are pending while unaffected
work continues: authority for 28 county appeal-body and nine fee-drafting
contradictions, and final full-versus-compact scope. A fresh inventory confirms
full S12 = 891 documents, full S03 = 951, deduplicated union = **1,828**, versus
the current 438-document compact union. No full-release completion claim is made.

## V6 steps after the corpus gate

### Fidelity checkpoint, 22:10 PDT

The latest 76 distinct fresh reviews contain 12 passes and 64 flagged documents.
Of the 15 deliberately selected spot audits of previously passing documents,
14 have returned: two pass and twelve are flagged. These are neither random
samples nor adjudicated error rates. Some findings concern verifier context or
overstrict boilerplate judgments; others identify substantive added obligations,
unsupported agency assignments or changed timing semantics. The earlier 191
unrechecked legacy passes do not establish fresh verification of those documents.

Fidelity must be checked across two boundaries: sampled process/case logs to
visibility specifications, then specifications to prose. Intended omissions,
stale descriptions, approximate timings, wrong user claims and cross-program
contamination are licensed observation noise, not necessarily renderer errors.
Unspecified additions are not licensed noise. Passing a render/spec check alone
does not establish that its specification agrees with the sampled process:
C22/S12's dashboard passed that check while retaining its July-publication /
September-data contradiction. No defensible corpus-wide fidelity percentage is
available yet, and no Bayesian performance conclusion should rest on these
unresolved records. The approved upstream corrections preserve numerical process
parameters and sampled cases; they repair inconsistent descriptions/metadata,
not resample the benchmark or tune it to model predictions.

### Handoff steps

1. Export immutable artifact bytes and a public-only index; keep specifications,
   verification explanations and labels outside the export. Record any unresolved
   validity qualifications separately.
2. Spawn the user-requested parsing subagent **without conversation history**,
   with only the source export, evidence contracts and source-only code. Use
   explicit per-program document indexes, including shared pages; do not rely on
   filename-prefix discovery. County IDs and contrast-statute IDs can collide.
3. Preserve exact quotes, case/source-family links, endpoints, repeated visits,
   counts, fees and unsupported claims. Do not force counts into annual volume or
   convert elapsed time into payer/agency hours. Keep unknown agency assignment.
4. Compile a declared supported subset into the existing integrated V6. The
   existing elapsed compiler is not a complete route/count/resource bridge.
   Missing dependencies default to serial, not unsupported parallelism; unknown
   semantic weights are assumptions, not measured calibration.
5. Measure dimension, likelihood cost, memory and informative claim coverage
   before a short, explicitly diagnostic local fit. A smoke fit is not a
   converged posterior, full-corpus analysis or Bayesian-versus-LLM comparison.
   Preserve all unsupported claims and label prior-determined outputs.

No V6 fit or new extraction had started when this document was created.
The existing [V6 handoff](scoping/2026-09-17-w2-v6-handoff.md) remains the detailed
contract; this document narrows the requested completion scope, not the model.

The existing V6 runner now accepts `--preflight`. It validates already compiled
source-only inputs and reports three reproducible likelihood probes, latent
dimension by block, supplied modeled/residual/count/resource claim coverage and
uncompressed retained-draw storage estimates. It does not sample, establish
identification/convergence, or estimate peak memory. This adds no new model and
does not claim that these corpora have yet reached the input gate.

## Active continuation, 22:50 PDT

The [active handoff](../runs/w2_s12_s03_completion_20260917/ACTIVE_HANDOFF.json)
records verifier session **57070** and approved-correction follow-up session
**23922**. The latter is genuinely running and waiting on the former's lock;
it is not a duplicate verifier. After the lock releases, it applies the archived
corrections, rerenders non-conflicted affected documents, and independently
reviews them plus the manual repairs. It defers conflicting ordinance and
fee-resolution packets pending the authority decision. Poll these handles before
launching anything else. A wait observation timeout does not mean either process
has stopped. No extractor or fitter has launched.

Seven manually repaired documents now await independent review. The last three
are C02/C08/C11 fee schedules: all 39 fee rows are byte-identical to their archived
versions, with amounts and due events preserved. Unsupported policy/payment
boilerplate is removed. Their unit column now means program administration, which
is what the generator's `proc.lead_department` supplies, not an invented payment
collection responsibility. Their publication dates are not claimed to be new
fee-effective dates.

The [22:38 fidelity checkpoint](../runs/w2_s12_s03_completion_20260917/fidelity_checkpoint_20260917_2238.json)
separates required-fact presence from faithful meaning: in 132 reviewed versions,
1,659/1,661 required facts were found, 1,505 were judged faithful, and only 242/377
timing facts passed that judgment. Added-fact flags occurred in 115 documents.
This is a nonrandom automated audit of versions, not an adjudicated corpus-wide
accuracy estimate; four source versions had already been repaired when sampled.
The large document-level failure count is not evidence that every planted fact
was lost, but timing semantics and invented obligations remain material defects.

The source-only export now contains explicit per-program memberships, including
shared dependencies and directories, and the existing reconciliation reader
validates frozen hashes. It cannot select a contrast statute merely because its
ID resembles a county or escape the source directory through a path/symlink.
These are handoff preparations, not claims of successful W2 extraction or fitting.

At 22:51 PDT the complete offline suite passed **486 tests**, with the same one
existing test-return warning. Both session handles were polled and remained live;
the approved follow-up was still waiting for the original verification lock.

## Continuation, 23:25 PDT

The initial verifier and approved-correction follow-up are still confirmed live
by polling their actual session handles. The corrections remain staged, not
applied. A third live session, **73135**, waits for the approved follow-up's
terminal receipt before doing any model work. It then reviews eligible older
unbound passes and pending reviews, performs one repair pass over **all** eligible
failures, and independently verifies the changed artifacts. It uses the existing
completion worker and subscription transport, four workers and batches of three;
it does not create a new shared selection or change the final scope. Originals,
failures and unresolved holds remain retained. This broader review is necessary
because the spot checks did not support treating old unbound passes as certified.

Nine distinct documents now have coordinator repairs awaiting independent
review. In this continuation, C32's directory lost invented reporting lines,
co-location and departmental duties while retaining its public names and contact
details. A second, separately archived C07 fee-schedule repair retains all eleven
fee rows byte-for-byte while distinguishing administration from payment
collection and removing unsupported adoption/effective-date assertions.

A newly enumerated visibility defect is recorded as `empty_checklist_visibility`
in the release holds: **eight S12 checklists and C08/S03's checklist** have zero
`reveals`, no contamination, and a 400–1100-word requirement. The generic checklist
projection looks for inspections, third-party work and corrections; it does not
necessarily expose the public rules an actual instructional checklist needs.
For example, C08's renderer supplied sixteen rules and a fine-policy paragraph
that its packet did not license. Padding a fact-free checklist with directory
text would satisfy a narrow verification contract but not finish a realistic
corpus. Alex has been asked whether to correct these visibility specifications
using appropriate already-public statutory/local rules and update the ceilings,
preserving sampled processes, timings and cases. No such policy change has been
applied. The remaining follow-up explicitly defers these nine artifacts.

A read-only recount before these latest repairs found 220 reviewed IDs, of which
212 still matched their reviewed document and spec hashes. Of 2,698 required facts,
2,692 were found and 2,386 judged faithful; timing was 451/720. There were 184
documents with added-fact flags. This excludes eight then-changed versions and
is still a nonrandom, unadjudicated automated render/spec audit, not an end-to-end
truth-fidelity estimate. Packet-context limitations remain relevant.

At 23:22 PDT the scoped status was 197 failures, 29 hash-bound passes, 191 legacy
passes, 14 unverified and seven audit-pending documents. These counts are not a
final result and change as reviews return. No source export, parser or V6 fit has
started. The full-versus-compact and upstream agency/fee choices remain unresolved.

## Continuation, 23:48 PDT: approved changes applied; diagnostic parsing started

The original verification phase completed at 23:29 PDT. The approved correction
follow-up then applied revision `0001`: all 183 changed files match their archived
approved replacements, and an independent recheck confirms all 979 protected
world/case-log files remain byte-identical. The local-rule/process changes are
strings only; no numerical or Boolean parameters or case draws changed. See the
[application receipt](../runs/w2_s12_s03_completion_20260917/corrections/approved_dates_optionality_v1/applied.json).
Thirty-two eligible affected documents have been rerendered; fifteen affected
ordinance/fee-resolution documents remain deferred on unresolved authority holds.
The follow-up is independently reviewing 51 affected/repaired documents. Sessions
23922 and 73135 were polled and confirmed live at 23:48; the latter still waits
for the former's terminal receipt and has not duplicated its work.

At 23:46 PDT, the compact union had 42 current hash-bound passes, 165 failing
verdicts, 185 older unbound passes, 15 deferred rerenders, 30 unverified documents
and one pending spot audit. A separate recount found 206 latest local reviews
whose document, specification **and context** hashes still match; 42 older
reviews were excluded. They contain 2,774 required facts, of which 2,769 are
present and 2,471 judged faithful. Timing accounts for 487 faithful judgments
out of 731 required timing facts; 161 documents have added-fact flags. This is
a nonrandom automated review, not adjudicated corpus-wide accuracy. The differing
denominator means it must not be read as a before/after repair improvement rate.

The world status tool had incorrectly let unverified documents outside its
selected lane prevent that lane's count gate from passing. It now separately
reports selected and global counts; a failed verdict still counts as a verdict,
not a pass. The selected S03 lane has 245 artifacts and 245 verdicts. The full
offline suite passed 490 tests with one existing warning; these tests do not
certify corpus fidelity. Release readiness remains false.

Under the existing count-gated diagnostic handoff, an immutable source-only copy
contains 136 public artifacts across all eleven calibration/development programs
in the compact slice. Selection did not filter on verification success. Reserved
and unassigned programs are excluded; quality findings and generation metadata
are kept outside the source directory. This is a mixed-quality diagnostic
snapshot, not the final verified release:
`runs/w2_v6_diagnostic_sources_20260917_2335/sources`.

The explicitly requested parser was spawned without conversation history and is
running under `/root/w2_source_only_parse`. Its saved driver and outputs are in
`runs/w2_v6_diagnostic_parse_20260917_2335`; the first source-only reconciliation
call began for C29/S12 at 23:42 PDT. It will save quote-validated canonical
evidence plus count, measurement-semantics and visit-operator sidecars. No V6
fit has started. In addition to the missing route/count/resource bridge, the
current V6's program-shared structural alternatives must not be mistaken for
per-case conditional-route frequencies. These remain implementation boundaries,
not grounds to fill gaps with generator truth or silently discard evidence.

## Midnight continuation (2026-09-18)

The approved correction follow-up completed at 23:54:39 PDT. Its immutable
[terminal receipt](../runs/w2_s12_s03_completion_20260917/approved_followup_completed.json)
records 64 current hash-bound passes, 172 failed reviews, 185 older unbound passes,
15 held rerenders and two pending reviews. This is not release completion. Six
of the nine coordinator-repaired documents now pass independent review; the
three fee schedules for C02/C08/C11 still have unsupported service/charging
labels and are included in the remaining all-eligible-failure repair pass.
Session 23922 is terminal and must not be restarted. Session 73135 has acquired
the lock and started the 167-document older/pending review phase before repairs.

V6 now supports explicitly omitting unobserved independent labor channels through
`--observed-channels-only`; see the
[implementation and validation record](2026-09-16-bayesian-audit-implementation.md#2026-09-18-omit-unobserved-independent-labor-channels-in-v6).
All 504 offline tests pass, including target replay and reduced-channel run
continuation. This is not active-case marginalization, new W2 timing evidence or
a claim that posterior fitting has begun. The source-only parser's first
reconciliation remains live within its saved 40-minute timeout; do not duplicate
or replace it merely because generation is slow.

## 00:24 PDT checkpoint: legacy renderer overlap

The initial/approved follow-ups remain terminal; session 73135 was polled live at
00:21 PDT and continues the existing 167-document review phase. A fresh comparison
found **42 documents changed since the approved follow-up receipt** by overlapping
legacy T08/T09/T10 writes. This is not evidence that the new, separately namespaced
S05 lane caused the changes. The 54 compact-slice artifacts covered by those three
batches were individually archived with hashes under
[`concurrent_render_20260918_0022/`](../runs/w2_s12_s03_completion_20260917/concurrent_render_20260918_0022/snapshot.json).
No document changed during its individual capture; this is not an atomic snapshot
of the whole world. A temporary exact-artifact `concurrent_legacy_render` hold
defers our upcoming mutations until the old writer's owner confirms a terminal/
quiet handoff. In-flight verification may finish under the existing hash/context
guards. Other workers, S05 files, shared selections and batches were not changed
or stopped. A coordination request is in the shared `W2-RENDER` log.

At 00:19 PDT, all 979 protected world/case files still matched their registered
hashes. The 24 changed local-rule/process files still matched the approved
replacements; their 66 leaf edits are strings only. Two corrected dashboard
artifacts were subsequently rewritten, but both retain the approved September 15
publication date. Their old passes do not certify their new body text.

The same read-only check counted 234 latest local reviews matching current
document/spec/context hashes: 3,210 of 3,216 required facts found, 2,902 judged
faithful; 579 of 850 timing facts judged faithful; 168 documents with added-fact
flags. This remains a nonrandom, unadjudicated render/spec audit, not corpus-wide
truth accuracy or a before/after improvement estimate. The live slice had 59
hash-bound passes and was not release-ready. The frozen diagnostic parser sources
are unaffected by these live-corpus changes.

V6's fresh-chain initializer now searches finite-support route alternatives when
its initial random route cannot explain the observations, without dropping claims
or changing their prior weights. Unsupported saved checkpoints still fail. The
latest completed offline suite passed **511 tests**; see the implementation record.
The first source-only reconciliation candidate was not accepted: two explicitly
unidentified-step forecasts violate the legacy evidence contract. Its existing
repair call continues; there is no accepted W2 ledger or fitted W2 posterior yet.

## 00:55 PDT checkpoint: first accepted source ledger; compiler boundary exposed

C29/S12 now has an accepted source-only ledger (14 documents, 34 activity
references, 84 measurements) and independently checked count, semantic and visit
sidecars. The parser's retained calls contain no tool events. A separate quoted
structural handoff distinguishes work, legal outcomes, standing duties, uncertain
identity and same-report groups; it is not an asserted completed trace or a source
of numerical priors. C41/S12 and C44/S12 are the next two live parser calls.

Per-case path support is implemented inside V6, with 531 passing offline tests
and a saved-seed legacy replay; see the implementation record. The first actual
C29 elapsed compilation retains 38/38 eligible claims but all are residual-only.
It therefore cannot support an informative fit yet. Work now addresses the
source-to-model population/operator/structure boundary, not another model
generation. No W2 posterior or Bayesian-versus-LLM result is claimed.

A read-only recount at 00:54 PDT found 312 current document/spec/context-bound
local reviews: 4,327/4,333 required claims present, 3,908 faithfully expressed,
763/1,141 timing claims faithful, and 242 documents with unsupported-addition
flags. These remain nonrandom, unadjudicated automated checks, not corpus-wide
accuracy. All 979 protected files were rehashed unchanged; all 24 approved
process/local-rule replacements still match and their 66 leaf edits are strings.
The compact slice remains unreleased. Session 73135 was directly polled live at
00:55 PDT and is still reviewing the remaining older/pending documents before
its already scheduled repair/reverify phase. The 54-document overlapping-writer
hold and all unresolved authority/visibility/scope questions remain open.

## 01:45 PDT checkpoint: repair provenance, wider chronology, three source ledgers

The previous goal turn produced new fidelity evidence rather than just a status
restatement: at 01:26 PDT, 353 latest local reviews matched current artifact,
specification and context hashes. They contained 5,142 required facts, 5,136
present and 4,640 judged faithful; timing was 861/1,318 and non-timing 3,779/3,824.
There were 277 documents with unsupported-addition flags and eight with leakage
flags. Sixty-three older local reviews were excluded as stale. These remain
nonrandom, unadjudicated automated findings, not an end-to-end accuracy rate;
the live repair phase subsequently changes which reviews bind current bytes.
All 979 protected files and the 24 approved process/rule replacements were
rehashed unchanged at that check.

Session 73135 finished its 167-document review phase at 01:23 and began its
already scheduled fixed 281-document, 94-batch repair pass with four workers.
It was directly polled live at 01:39. The queue exposed a real lookup defect:
repair read only the latest shared verifier row even when that row lacked an
actionable fix and the local, current-hash review supplied one. At 01:40 all
72 then-error-affected IDs had a current artifact/spec/context-bound local
failure with an actionable fix. `complete_slice.py` now selects that bound
review, records its provenance, rejects stale review contexts and newer bound
passes, and refuses an unapproved publication-date change. **572 offline tests
passed** in 36.37 seconds with the existing generator-test warning.

Those edits do not hot-reload the running worker. Its current errors and raw
responses are preserved. After its terminal receipt, a fresh bounded retry must
use current code and all release holds, followed by independent verification;
no duplicate retry has launched. At 01:45, 96 latest artifacts from this repair
pass had landed, and all 96 retained their specification dates. That is not a
claim that their repaired prose passes review.

The [wider chronology audit](../runs/w2_s12_s03_completion_20260917/chronology_audit_20260918_0139.json)
examined the full 1,828-document S12/S03 bundle, not just the 438-document slice.
Beyond the nine corrected dashboards, **32 existing aggregate documents** have
first-visit cohort cutoffs later than their publication dates: fifteen FAQs,
sixteen guides and one audit excerpt. All 32 are in the compact slice. They are
now recorded in the `aggregate_observation_chronology` release hold. Approval
was requested for explicit dated timing updates preserving original publication
dates, stale policy versions, figures and case draws; none has been applied.
The fixed live queue may still visit these IDs, but a prose repair cannot grant
authority to resolve that upstream conflict. The same scan flagged 1,492
individual-story cutoff candidates (123 in the compact slice); these need
case-specific date/update interpretation and are **not** 1,492 adjudicated errors.
No publication dates, process parameters or case draws were changed by the scan.

Source-only C29, C41 and C44 ledgers and all three audit sidecars now independently
validate with no quote/hash/event errors; the retained event audits show no tool
use. See
[partial verification 3](../runs/w2_v6_diagnostic_parse_20260917_2335/source_only_verification_partial_3.json).
C29 and C44 also have quoted structural handoffs; unknown early/late identities
must not become extra mandatory tasks, and repeated wording remains linked to
the same case. C53 and C56 reconciliation calls are active; C44's separate visit
hypotheses audit is queued behind the existing two-call interlock.

The integrated V6 now supports first-visit population binding and interval-union
report grouping; the [implementation record](2026-09-16-bayesian-audit-implementation.md)
records the tests and saved-state replay. C29's explicit uncalibrated diagnostic
policy retains 38 claims in 32 factors, of which 16 claims/13 factors are
informative. Initial compilation under the unchanged base policy retains all
44 eligible C44 claims and 49 C41 claims, but both remain residual-only. Source
hypotheses, complete inventory/conditional-route compilation and calibrated
weights are still required; no W2 posterior or comparison is claimed.

The 01:41 hourly check found `observed.complete_by_counts: true` for the selected
245-document S03 lane, including 132 failed verdicts; `corpus_complete` remains
false. This is not the 438-document slice or the full 1,828-document release.
The [watch receipt](../runs/w2_s12_s03_completion_20260917/hourly_status_20260918_0141.json)
is an explicitly labeled excerpt of the actual command output. Next check is
due 02:41 PDT. The existing parser must not be duplicated.
