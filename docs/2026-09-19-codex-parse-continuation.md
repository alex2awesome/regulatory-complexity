# Real-corpus parse continuation and audit

The current task is to finish the interrupted real-corpus parse, extend it to
the entire on-disk source corpus, and establish what is and is not covered.
This continues alongside the earlier S12/S03 synthetic verification and V6 work;
completion of one does not certify the other.

Latest selected snapshot (2026-09-19, updated 22:10 Pacific): **73 ledgers / 10,141
measurement rows**, at `runs/rw_parse_20260919/review_sweeps_73_ledgers/`.
This snapshot binds all 73 selected manifests and 70 mandatory review sidecars
by hash; previous snapshots remain unchanged. Hash binding preserves a review,
not proof that it is correct.
This is not a completed corpus or a fit-ready ledger. Fourteen of the 19 whole
megathreads are now completed (1,753 main pages), including San Joaquin 324104's
preserved endpoint-label revision. The 358-page thread 324089 is active.
Thread 324060 remains unselected: parent review found additional omissions and
incorrect default agency assignments in its expanded native packet. Its preserved
v3 corrects the seven identified defects and leaves 2,704 candidate clauses
requiring individual semantic review. The first 600 now have scoped parent
acceptance with mandatory correction overlays; 2,104 remain. This is not a
completed thread or a fit-ready packet.
Exhaustive Reddit batches 001–023 are
selected (419 threads, 8,372 comments), with preserved revisions where needed.
The 78 rows from 021/022 passed scoped parent review after structured semantic
corrections. Batch 023's seven-point revision is accepted; 024 is held for
semantic corrections and 025 is active.
The native CF18 and ten-workbook CF296 packets are complete, with independent
parent raw-cell checks. The other nine public-program workbooks have also been
extracted and independently replayed by both worker and parent.
None of those administrative cells inflate the 10,141 canonical measurement rows.
Reddit batch 011's preserved semantic revision is selected, with mandatory parent
holds. The fresh 22-document artifact-only C29/C44 synthetic
extraction is complete and passes parent integrity and scoped semantic checks;
source-only revisions restore the C29 omissions, C44 fee scope, document source
families and explicit legal order. A fresh strong-model, source-only reconciliation
now has a preserved parent correction of case outcomes and scoped acceptance, while
retaining unresolved inventories/timing identities;
neither fresh ledger is fit-ready. The second cheaper worker completed the 99-capture
legacy packet and its 191-selected-page OCR supplement. Preserved native-evidence
revisions now pass parent review; a preserved three-row canonical derivative is
selected. The original nine-row ledger remains unselected because six rows have
unsupported clock/population mappings. See the
[V6 scoring and controlled-selection work](2026-09-19-v6-evaluation-and-selection-progress.md)
for the parallel model work and remote running jobs. Older checkpoints below are
preserved, not current totals.

### Remaining queue at the 73-ledger checkpoint

These units are deliberately not added into one completion percentage. A raw
file, converted page, native spreadsheet cell, retained measurement and
independent fit observation are different things.

| Queue | Accepted / reviewed coverage | Still to do |
|---|---|---|
| Whole forum megathreads | 14 of 19; 1,753 of 4,548 main pages | 324060 (292 pages, revision), 324089 (358, active), 324094 (372), 324096 (621), 324077 (1,152): **2,795 pages** |
| Exhaustive captured Reddit comments | 23 of 88 batches; 419 of 1,799 threads; 8,372 of 32,669 comments | 65 batches / **1,380 threads / 24,297 comments**; 024 held, 025 active |
| Well-source response queue | Independently reviewed native revisions: first ten sources (105 claims / 132 table rows), eight El Dorado sources (117 claims), batch003's ten sources (58 claims), and batch004's ten sources (95 claims); earlier sparse-page/Word checks preserved | The 66-document queue and canonical semantic bindings remain incomplete; these native packets add no canonical measurement rows |
| Grand-jury reports | 613 PDFs / 21,380 pages indexed; selected OCR and native supplements preserved | Full report-level semantic coverage remains incomplete; OCR alone is not parsing |
| Administrative workbooks | 25 workbooks / 14,996 rows preserved and mechanically replayed | Cohort/statistic/endpoint bindings for model use; 1,468,922 native values are not that many independent observations |
| Compact synthetic S12/S03 experiment | 428 of 438 documents have current passing verification | Ten release holds, including five unresolved authority decisions; do not alter sampled processes without the required decisions |

This table is a view of established major queues, not a declaration that every
physical file on disk has been semantically classified. Source aliases, failed
retrievals, missing attachments, conversion gaps and cross-ledger dependence
remain in the detailed receipts. The model's synthetic recovery gate is also
still unmet, independently of parse completion.

### Reddit023 selected; well004 reviewed; further forum checks, 22:10 Pacific

Batch023's preserved revision removes the questioned eight-hour class from the
canonical ledger while retaining it natively. The other six corrections are
materialized in the structured fields. Parent replay passes 70 manifest bindings,
318 core literal references, 433 source spans and one calendar derivation; an
additional 104 sidecar references replay. The new selected snapshot replays all
143 manifest/review bindings, with ten cross-ledger candidates and 60 automated
fee flags among 1,915 fee rows. Flags are not confirmed errors.

Well004's ten sources and nine PDF pages were fully read by parent and independent
reviewer. The preserved `batch004/reviewed_v2/` materializes seven corrections,
including fuller compound-claim anchors, missing native quantities and removal
of an unsupported “minimum” qualifier from Napa's 3,000-gallon rule. All 95
original anchors remain unchanged; six supplemental anchors replay. The revision
has zero canonical rows. Napa's public water-system operating-permit guide is
kept separate from well construction, and Mono's redirected HHS landing page
remains a missing intended source, not evidence of absent requirements.

324060 shards four and five cover the next 400 clauses. Mechanical replay passes;
parent review of all 116 new interpretations and 24 seeded rows requests two
small overlays: a reported current class fee separated from hypothetical agency
finances, and an agency-email event date separated from the next day's report.
Those 400 remain under parent review until the overlays are verified. A new
checker version recognizes explicitly attributed cross-post BBCode quotations;
the original same-post-only checker is preserved. No raw source or sealed packet
was changed to make validation pass.

Batch024's 37 retained rows pass mechanical replay but await source-bound fixes
for a “within ten minutes” upper bound, an anticipated year treated as completed,
recoverable root-author identity, operator-versus-issuer scope, cross-thread case
dependence and two omitted nonnumeric process claims. No rows are fit-ready.
Local disk check at 05:10 UTC found 29 GiB available; no cleanup is authorized.

### Manual forum review and native well003 accepted, 21:53 Pacific

The first three 324060 shards cover exactly the first 600 original pending
clauses, without overlap. Mechanical replay and seeded parent source checks
support scoped acceptance, not a second full independent reading. The first
shard requires a preserved overlay correcting scheduled interviews and
qualification appointments that had been treated as completed. The second
requires an overlay correcting a generic $35 amendment/range-fee instruction
that had been labeled a personal payment. The third retains conflicting mailing
dates, DOJ-versus-sheriff status differences and later superseding milestones.
Neither linked old claims nor prose cautions may silently override these holds.
Receipts: `calguns_324060_manual_shard{1,2,3}_parent_review_v1.json`.

Well003's 58 native claim groups received full parent source reading, eight
distinct page-image reviews and independent semantic review. The preserved
`batch003/reviewed_v2/` clarifies that only the San Francisco application's first
page prints December 2020; the attached procedure pages are undated. Its two
retrieved PDF copies have different raw hashes but identical reviewed page
images/text, and are dependent evidence. All 58 literal claim anchors and 17
source spans replay; the 12 base image hashes have a separate replay receipt.
No numbers or quotations changed and no canonical measurement rows were added.

Reddit023's 41 retained rows pass mechanical replay but remain unselected. Parent
review found an approximate maximum encoded as a minimum, an interrogative
eight-hour class claim, an ambiguous two-month review endpoint, issuer mixing,
an omitted pending-renewal milestone, a time-version conflict, and SNAP advice
mis-scoped to General Relief. Corrections are requested after the active 024
batch. Selected totals remain 72 ledgers / 10,101 retained rows.

### Reddit021/022 revisions selected, 21:33 Pacific

Batch021's selected `reviewed_v2` preserves all 47 numeric measurements and case
bindings while correcting provider/payee versus issuing-agency assignments,
whole-process versus single-agency scope, a 90-day validity window mislabeled
as a statutory processing cap, and scheduled MEDICUP hours. Batch022's selected
`reviewed_v1` preserves all 31 numeric measurements while correcting generic
waiting-rule authority, unknown actors, overlapping purchase/transfer costs,
approval versus card-access endpoints, and three reference letters mislabeled
as three distinct operations. The letters remain native evidence; they are not
deleted or converted into zero burden.

Parent replay passes 73 hashes / 318 core quotes / 395 source spans / seven date
derivations for 021 and 73 / 285 / 393 / seven for 022. Separate scoped semantic
reviews inspect all retained interpretations, cases and native claims, including
113 and 84 supplementary quote anchors respectively. This is not a second
independent reading of all 732 comments. Unknown actor placeholders must not
be counted as additional agencies; overlapping clocks and costs must not be
summed. The 72-ledger selection replays all 135 manifest/review bindings.
Receipts: `exhaustive_reddit_batch021_parent_semantic_review_v1.json` and
`exhaustive_reddit_batch022_parent_semantic_review_v1.json`.

At this historical checkpoint, the first 200 individually reviewed 324060 clauses remained under parent review.
A seeded source check found an inherited linked claim that treats a scheduled
interview as completed merely because no later contradiction appeared. A preserved
correction and broader scan are requested; this is not a completed thread or a
reason to silently reduce its pending queue.

### Native well revisions; Reddit021/022 semantic holds, 21:16 Pacific

Well001's independently reviewed revision is preserved at
`well_response_parse_parent_v1/batch001/reviewed_v2/`. Parent replay checks 100
manifest bindings, 105 exact claim spans and 55 page spans. All original 83 claims
and all existing table fields/numbers are unchanged. Five annotations distinguish
the four printed `--` depth markers from the total row's literal blank; neither
becomes zero or an inferred meaning. The 22 additions are supplementary public
requirements, not 22 independent outcomes. Six image files in the base image
index were replayed by this checker; the earlier nine-image visual-review receipt
remains separate.

Eight El Dorado sources (31 native PDF pages and two HTML documents) received
full parent reading and independent review, including ten selected page images.
The reviewer found four compound claims with incomplete short anchors; the
supporting facts were present on the bound pages. The preserved revision at
`well_response_parse_parent_v1/batch002_eldorado/reviewed_v2/` expands two anchors,
splits two plan-check windows, and adds 13 native requirements/fee entries.
All 117 resulting claims and 33 page spans replay exactly. The signed 2019 and
2026 editions remain distinct, minimum deposits are not final fees, struck-out
PDF fees are not adopted, and 30- versus 60-day reporting instructions remain an
explicit version conflict. Neither this subset nor its original generic batch
is claimed as the whole well-response queue.

324060 v3 passes 1,916 ancestral hash checks, 12 correction-quote checks, 3,088
clause-reference checks and 1,616 evidence-post replays. Parent source inspection
supports the three agency/episode repairs and four omitted-claim additions.
It is accepted **as a corrected partial checkpoint only**: 384 explicit/manual
clause links versus 2,704 programmatic candidates still awaiting real judgments.
Receipt: `calguns_324060_reviewed_v3_parent_review_v1.json`.

Reddit021 (47 rows, 15 roots/365 comments) and Reddit022 (31 rows, 13 roots/367
comments) pass mechanical replay but remain unselected pending semantic repairs.
The issues include issuer versus provider/payee roles, generic waiting rules
mislabeled as statutory caps, and three reference letters mislabeled as three
distinct operations. Exact quotations alone do not catch these errors. Numeric
values and originals are preserved; revisions must update the structured fields,
not merely add cautionary prose. Cross-batch author/episode dependence remains a
required step before any global fit.

### Reddit020 selected; well001 draft and 324060 v2 hold, 20:41 Pacific

Reddit020 adds nine retained rows from one root and 613 captured comments.
Parent checks replay 26 hashes, 77 original and nine additional sidecar literal
references, and 615 source spans. All nine interpretations, three case summaries,
16 native claims and four count safeguards received scoped parent review, not
a second complete reading of all comments. A police nonresponse report is not
evidence that dispatch accepted the call; its clock needs that distinction
before fitting. The same episode's one-hour confinement is dependent evidence,
not another case or active labor. Political schedules, generic backlog and
counterfactual housing volume remain held. Receipt:
`exhaustive_reddit_batch020_parent_semantic_review_v1.json`.

The parent separately read all ten well001 artifacts (52 native PDF pages and
three HTML documents), inspecting nine selected image pages. A new native draft
at `well_response_parse_parent_v1/batch001/` retains 83 authored claim groups
and 132 administrative table rows. Separate replay checks 83 literal UTF-8
spans, 55 source-page spans, all table rows and nine image hashes. Another agent
is performing independent semantic review; this is **not yet accepted or
canonical**, and the parent's context is not blind. Butte source discrepancies
are preserved: WY2016 small permits 69 versus 113 across tables, repair months
summing to nine versus printed four, and the 2026 dry-well community column
showing one versus its zero total (which also makes its grand-total row disagree).
Issued and finaled totals are not a matched case cohort; backlog updates are
explicit. Rule deadlines, technical test durations, conditional fees and agency
routes do not become empirical processing-time observations.

324060 reviewed_v2 adds 120 useful typed claims but still fails completion review.
Parent replay passes 1,845 bound-file checks across its three generations; source
inspection finds the old Orange County history assigned to Beanie's later
Contra Costa episode, and WCPD routing rejection treated as the county episode's
single issuer. A third authority citation quotes another person's coworker.
A new seeded 20-row exclusion sample exposes omitted Pleasant Hill psychological
test time/cost, a staff-reported backlog, and conditional scheduling claims.
Keyword-generated exclusions and token-matched links were frozen and relabeled
as authored; freezing is not manual semantic review. The source files and useful
additions are preserved, but the thread remains unselected. Exact receipt and
revision request: `calguns_324060_reviewed_v2_parent_hold_v1.json`.

### Reddit019 selected; blank-page recheck, 20:25 Pacific

`exhaustive_reddit_parse_v1/batch019_reviewed_v2/` adds 31 retained rows from
seven roots and 202 captured comments; originals and both revisions are preserved.
Parent replay checks 56 hashes, 215 original literal references, 34 additional
sidecar references, 216 source spans and 13 calendar calculations. The final
revision changes only the unresolved six-month dispute's scope: an ongoing
episode is not a standing recurring obligation. Three Los Angeles roots repeat
one applicant, whose stated 561 days differs from date subtraction (560), and
whose stated $478 total exceeds listed components ($468). Both discrepancies
remain explicit. Attendance and five-hour failed telephone contact are not
automatically active labor; unknown counties remain unresolved. Receipt:
`exhaustive_reddit_batch019_parent_semantic_review_v1.json`. The packet remains
globally held from fitting. The new sweep has ten cross-ledger candidates and
60 automated fee flags among 1,897 fee rows.

The 102 grand-jury pages previously pixel-white at 75 dpi were re-rendered:
101 at 300 dpi and one oversized page with a 6,600-pixel long-side cap. All remain
exactly white in RGB. An independent histogram replay checks all 102 images and
306 source/receipt/image hashes. This is a pixel-blankness check, not semantic
reading or proof that hidden layers and attachments contain nothing. The first
uncapped attempt stopped at Pillow's oversized-image guard and is preserved,
unselected. Accepted receipt:
`grand_jury_reports_v1/missing_page_ocr_v1/white_page_recheck_300dpi_capped_v2/parent_replay.json`.
No canonical measurements were added by this check; unresolved map and faded
letter transcriptions remain held.

### Reddit018 revised and selected, 20:03 Pacific

`exhaustive_reddit_parse_v1/batch018_reviewed_v1/` adds 77 retained rows from
33 roots and 357 captured comments. The original packet is unchanged. Six
measurement interpretations/representations are corrected; every row now has
an observation-semantics sidecar. Parent replay checks 100 hashes, 616 original
literal references, 84 new sidecar references, 423 source spans and 21 calendar
calculations. Counts, cases, coverage, fee dependencies and source documents are
byte-identical to the original. Coarse dates remain coarse, the 17-day pending
case stays a lower bound, and same-day renewal is not exact zero elapsed time.
The two counts concern staff people contacted, not trips or distinct operations.
Source resolution, case dependence and global fit holds remain mandatory;
generic `n=1` fields are not observed cohort sizes. Receipt:
`exhaustive_reddit_batch018_parent_semantic_review_v1.json` under the runs parent.
Batch019 is active. The new sweep has ten cross-ledger candidates and 60
automated fee flags among 1,892 fee rows, not 60 adjudicated errors.

### 324104 selected; 324060 and Reddit018 held for corrections, 19:54 Pacific

The selected San Joaquin derivative is `calguns_324104_reviewed_v1/`, not the
original generic-event-code packet. All 299 derived-span labels and matching
context notes were reviewed; numerical values, case IDs and quotations remain
unchanged. Parent replay checks 1,396 hashes and 7,975 literal references with
zero mismatches. Scoped semantic acceptance is recorded in
`calguns_324104_parent_semantic_review_v1.json`. Its 695 rows are not independent
cases: overlapping spans share episodes, and 470 registry records include
author/history containers. Neither endpoint review nor quote integrity proves
exhaustive semantic recall. The 522 quoted documents are 265 main pages plus
257 local HTML projections, not additional independent retrieved pages.

The 292-page Contra Costa `calguns_324060/reviewed_v1/` passes 910 hash checks
but **does not pass parent semantic review**. Its builder assigns unmatched
episode keys to Contra Costa Sheriff; an explicitly Oregon episode is thereby
misassigned. Its 1,185 unlinked clause candidates receive a blanket context or
duplicate disposition. A seeded 18-row check found omitted completed training,
an application-return/refiling history, and prospective travel/training burden.
The worker is preserving v1 and producing a source-specific v2 review, including
all episode authorities and clause dispositions. The original 48 normalized
rows remain a partial checkpoint, not a complete thread ledger.

Reddit018 covers 33 roots and 357 captured comments and has 77 proposed rows.
It remains unselected pending preserved semantic corrections: coarse pending
ages must not become completed point durations, same-day renewal must not be
exact zero continuous duration, course frequency is not applicant elapsed time,
and waiting/attendance must not silently become active labor. A parent replay
assumption also needed correction: an exact date difference can legitimately
be an open-case lower bound, not a completed point observation.

The Colusa historical well-requirements Word capture has now been rendered to
five derivative pages and all five visually inspected (the original Word
metadata says four pages). Twelve native claims distinguish construction versus
destruction fees, conditional agency involvement, advance notice, technical
dimensions, and abandonment rules. They add **zero canonical measurements**.
Receipt: `well_response_captures_v1/colusa_word_visual_review_v2/parent_review_receipt.json`.
The 66-document well queue still needs a complete semantic parse; a first
batch was assigned, then deferred for the Contra Costa review corrections.

### Reddit017 selected; 324104 endpoint review, 19:39 Pacific

Reddit017 adds 53 measurements from 23 roots and 393 captured comments (seven
unavailable bodies retained). Parent replay independently checks 93 manifest
hashes, 431 literal references, 439 source spans and 15 calendar calculations.
The scoped semantic review covers the measurements, 28 case descriptions and
43 native status groups, not a second read of every comment. Overlapping Kern
and Riverside intervals remain dependent; the $448 fee-component sum is not
silently reconciled with the reported $480 total. Waiting/attendance is not
automatically active labor. The packet remains globally held before fitting,
even where its local endpoint audit has no remaining hold. Receipts are
`exhaustive_reddit_batch017_parent_validation_v1.json` and
`exhaustive_reddit_batch017_parent_semantic_review_v1.json` under the runs parent.
The cheaper worker has moved to batch018.

The 265-page 324104 packet passed parent replay of 1,370 input/output hashes,
7,097 literal references and both contracts. Parent semantic inspection found
interview dates mislabeled as submission dates by a generic event-code map.
The worker is preserving the original and reviewing labels across all 91
source timelines/299 derived spans before selection. Correct date arithmetic
alone does not establish the clock's meaning. Its 695 measurements are **not
yet included** in the selected total.

### Reddit016 selected; well-PDF sparse pages reviewed, 19:25 Pacific

Reddit016's preserved `reviewed_v1` adds seven measurements and no canonical
count claims. Parent replay checks 142 literal quotations and 92 hashes;
Pacific-time conversion independently confirms the Tulare two-day interval.
`exhaustive_reddit_batch016_parent_semantic_review_v1.json` records scoped
acceptance and mandatory corrections: the Section8 and SanJose hypothetical
waits are forecasts, not observed right-censoring despite the worker's status
label. Their existing fit holds remain. Seven lifetime renewals stay native-only,
and the Fresno case is an application correction before any stated decision.
Reddit017 is next with the cheaper worker.

All 17 sparse pages from four well-corpus PDFs have now been rendered, OCRed
and visually triaged. The formerly empty San Benito capture contains a complete
two-page Well Permit Procedure, revised April13,2018. A separate manual
transcription and ten native claims preserve fee/deposit/refund distinctions,
the business-day processing forecast, permit validity and notice requirements.
Six historic Del Norte well-completion forms contain construction/test dates,
not application-processing observations; one has a permit date after construction.
An overprinted permit/site plan remains partly unreadable. These source views
are not a full parse of the 66-document well queue and add no canonical rows.
Receipt: `well_response_captures_v1/sparse_visual_review_v1/parent_review_receipt.json`
under the runs parent, with 48 input hashes and independent 49-file digest replay.

### Cross-ledger source review extended, 19:13 Pacific

`runs/rw_parse_20260919/cross_ledger_linkage_review_v2/` extends the earlier
seven-group review to all ten exact-quote candidates in the 64-ledger snapshot.
The source-bound receipt checks 126 files and replays 24 claim quotations.
Nine groups support common application episodes. The tenth repeats a detailed
CalFresh narrative under two Reddit post IDs: dependence is supported, but
the two author identities are not proven to be one person. The previously
unresolved IHSS excerpt and Madera repost are now linked to their original
comment/post, not counted as independent new applicants.

The earlier corrections remain mandatory: a 2010 sixdays application does
not become a 2020 application when quoted; mid-December is not exactly
December 15; updated signatures are not dated by their containing post; and
same-case measurements with different endpoints must not all be deleted as
duplicates. This review does not establish duplicate-detection recall, mutate
the original ledgers, or make them fit-ready. It must be consumed before global
pooling; none of these cross-ledger decisions has yet changed a fitted model.

Reddit016 has completed its first parse (six threads, 355 comments, seven
measurements) and passed parent integrity replay. A preserved semantic revision
is in progress before selection: separate renewal episodes are not within-case
retries, a pending application correction is not necessarily permit amendment,
and exact source-author spelling and local-date arithmetic are being checked.

### Preserved legacy and Reddit derivatives selected, 18:48 Pacific

The selected snapshot adds 50 rows: three from
`legacy_forum_parse_v1/canonical_review_v1`, 38 from Reddit014 `reviewed_v1`,
and nine from Reddit015 `reviewed_v1`. Parent acceptance and bound hashes live in
`runs/rw_parse_20260919/latest_reviewed_packets_parent_acceptance_v1.json`.
Original artifacts and ledgers remain unchanged. Parent integrity replay checks
196 literal references / 76 hashes for Reddit014 and 109 references / 74 hashes
for Reddit015, plus 11 date calculations in Reddit014. These are scoped semantic
reviews, not a second reading of every comment or proof of complete recall.

The legacy derivative keeps two legal completeness/review caps separate from
observed timings and retains a four-to-eight-hour staff estimate as an estimate.
Unsupported Sonoma means and volume mappings remain native-only with the corrected
tables. Reddit014 repairs missing endpoint quotations and cross-author labeling;
an unresolved almost-two-year fragment remains native-only. Reddit015 preserves
two denial **events** without asserting two distinct operations, repairs two
native quotations, and separates prospective costs from incurred costs.
None of these packets is fit-ready. The combined sweep reports ten cross-ledger
case candidates and 56 automated fee flags among 1,800 fee rows; those are review
queues, not independently adjudicated errors.

Thread 324060 is deliberately not counted complete: its full 292-page reading
checkpoint preserves substantial source text, but the parent found supported
quantitative claims in the reading notes that were not yet individually extracted.
The worker is extending the semantic ledger in `reviewed_v1/` rather than treating
text retention, regex clause candidates or quote matching as extraction completeness.
Its original frozen packet remains a partial checkpoint. Reddit016 is active with
a separate cheaper worker; it does not enter the selected counts yet.

### Legacy native supplements accepted, 18:20 Pacific

`legacy_reviewed_supplements_parent_v1.json` records the parent's read-only replay
and scoped semantic acceptance of `legacy_forum_reviewed_v1/` and
`legacy_pdf_ocr_parse_reviewed_v1/`. The former exactly reproduces all 23 Sonoma
PDF text pages and binds 25 unique input/output files. The latter binds 49 files,
replays 24 complete supporting page projections, checks 74 scalar provenance
pointers across 31 native claims, and regenerates three original-PDF page images.
Parent visual review covers the two corrected Sonoma tables, both Butte landfill
tables and the Glenn sampling date. This is not a second full visual reading of
all reports. The OCR supplement covers 191 selected pages out of 499 PDF pages.

These are native supplements, not a replacement canonical ledger or new fitted
observations. The corrected adoption clock, unspecified day convention, mixed
department-wide volume, internal date conflict and printed-versus-summed landfill
total are explicit. Original packets remain unchanged. The selected measurement
total therefore stays at 9,101.

### Santa Clara and Reddit reviews, 18:11 Pacific

Santa Clara 324113 contributes 757 measurements and 45 count claims from
216 main pages. Its 193 supplemental quote documents are exact projections of
already captured HTML fields, not additional pages. Parent replay independently
checks all 193 complete projections, 673 source fields, 6,133 literal references,
915 unique bound files and 428 calendar differences. A scoped semantic review
adds mandatory exclusions for 17 forecasts, scheduled windows or availability
reports whose worker hold flag was false. Their quantities remain retained, but
they are not observed completed timing/payment evidence. The selected snapshot
requires both the worker sidecars and
`calguns_324113_parent_semantic_review_v1.json`; it is not fit-ready.

Reddit012's original parse had a material jurisdiction error (a city MyCCW case
assigned to Sacramento County), a cross-author Yolo phone-case merge, and pending
or authorized quantities treated too much like completed observations. The selected
`reviewed_v1` corrects these, preserves original sources and ledgers, and restores
the membership-dependent zero marginal training charge. It contains 53 measurements;
parent checks pass 316 literal references and 132 hashes, plus 13 date calculations.
Reddit013 has zero timing/fee measurements but two retained count claims: a
commenter-described normative three-interview requirement and one observed
interviewer-requested statement rewrite. Those are not interchangeable count
likelihoods. Its 435 captured comments include 63 unavailable bodies. Neither
packet claims complete live-web coverage.

### Source-native PDF review, 17:58 Pacific

The five legacy batches cover 93 ordinary captures plus six legislative XML
captures, not 99 new independent sources. The parent found that nonempty OCR had
dropped several Sonoma review-time table entries, changed 67% to 57%, and read a
2024 year heading as 2021. Original PDF pages govern these corrections; their
internal February/December chronology conflict remains explicit. Nine draft
canonical rows are not selected pending the preserved revision. The parent hold
is `runs/rw_parse_20260919/legacy_forum_parent_semantic_hold_v1.json`.

The separate OCR supplement covers **191 selected pages from eight PDFs**, not
all pages of those PDFs. Its 31 native claims and two transcribed landfill tables
remain outside the canonical measurement count. Worker validation replays all
191 projections and 208 source hashes. The parent found an adoption/publication
unit mismatch and incomplete quote support for several compound numerical claims;
a preserved derivative is requested. A printed landfill grand total differs by
two from its displayed row sum; both numbers remain recorded. These checks show
why literal quote integrity alone does not certify semantic accuracy.

### Native tables and supplemental review, 17:28 Pacific

`calfresh_cf296_cohort_parse_v1/` retains 7,139 county/statewide-month rows and
887,301 native values across ten workbooks. The parent independently replays all
887,301 values, 47,141 identifier cells and 8,332 documentation cells from raw
OOXML, with 45 matching bound hashes. Negative adjustments, suppressed cells,
blanks and errors remain distinct; statewide totals overlap their counties.
Receipt: `calfresh_cf296_parent_validation_v1.json`. This verifies extraction,
not every semantic mapping or suitability for a timing likelihood.

`remaining_program_workbooks_parse_v1/` covers the other nine frozen workbooks:
CF256, CalWORKs, General Assistance and IHSS. Its 348,925 native values across
4,435 form/cohort rows passed the worker's separate raw-OOXML replay. The parent
also replayed all 348,925 native values and 399,132 projected stored cells,
including formula expressions/caches, against raw OOXML; 103 bound hashes match.
Receipt: `remaining_program_workbooks_parent_validation_v1.json`. Formula
caches, absent caches, suppression, benefit amounts and authorized service hours
remain explicit. These are not applicant fees or agency labor by default.

All 72 nonwhite pages that produced empty grand-jury OCR have now been visually
triaged by the parent. One readable repair recommendation and 21 regional-center
map labels are retained natively. The map's full geographic transcription and
one badly faded letter remain unresolved; 102 pixel-white pages were not
individually visually reviewed. This is not a semantic reading of all reports.
The hash-bound receipt is
`grand_jury_reports_v1/missing_page_ocr_v1/visual_review_v1/parent_review_receipt.json`.

Fresh C29/C44 synthetic extraction preserves 37 and 44 measurements respectively.
Parent checks pass 119/139 literal references and 33/32 bound hashes. Those checks
do not settle step identity: several review labels may refer to shared operations.
Two omitted C29 short-duration reports are restored in a preserved revision;
C44's $210 named-step fee is being corrected from an unsupported process-total
reading. Default document-level source families and explicit statutory ordering
are also being preserved before the final parent check.
These current-source parses are not interchangeable with the older frozen inputs
used by the running controlled fits.

A subsequent full-corpus check found a material scope omission in the original
freezes: “withheld from the CalGuns slice” did not mean a source was selected
elsewhere. New queues now include 613 grand-jury PDFs (21,380 pages, including
scanned material) and 1,799 whole Reddit threads (32,669 captured comments).
Only Reddit batches 001–013 (4,688 comments and 270 root contexts,
395 measurement rows) have entered the selected parse snapshot. The rest remains
outside that completion declaration. Their independent
source-preservation checks and remaining OCR/gap limitations are documented in
the [inventory correction](2026-09-19-real-corpus-inventory-audit.md) and
[supplemental freeze report](2026-09-19-supplemental-source-freeze.md).

Two earlier completions have preserved parent revisions:

- Placer 324090: 99 pages, 429 measurements, 14 count claims. The independent
  check passes 2,066 literal evidence/count references and 330 bound hashes on
  `calguns_324090/reviewed_v1/`. A pending-word rule in the original assembler
  incorrectly censored completed stages when annotation text mentioned another
  pending endpoint. Ten endpoint/semantic annotations are corrected: four
  reported completed values and a same-day callback upper bound are restored;
  forecasts are distinguished from current ages; approval-to-notification is
  not submission-to-approval. Historical routes and rounded conflicting reports
  still require compilation review.
- San Mateo 324064: 155 pages, 124 measurements, six count claims. The independent
  check passes 488 hashes and 385 evidence/count references on `reviewed_v1/`:
  265 literal and 120 presentation-normalized, with no contract mismatch. The
  parser's original all-literal claim is explicitly corrected, not repeated.
  Five source-grounded revisions separate future training from observed effort,
  fix a derived 315-day calculation to 316, and preserve two author-stated day
  counts while exposing conflicts with their dated chronologies. A source's
  reported count is not silently replaced with the reviewer's arithmetic.

The new snapshot contains 1,793 fee rows and 56 automated fee candidates.
The three new Solano candidates are reviewed in
`calguns_324124_parent_semantic_review_v1.json`: two false recurrence flags
confuse monthly class availability with billing, while a remembered $320 bundle
already has the appropriate scope/dependence limitation. No ledger change is
needed to preserve those readings.
Fourteen candidates added after the earlier 49-ledger snapshot now have a
source-bound review in `fee_semantic_review_alameda_v1.json`: eleven false
recurrence alarms caused by neighboring amounts in long quotes, one explicitly
annual renewal, one mixed-horizon hypothetical bundle, and one renewal-cadence
claim corrected by its author's later post. Existing Alameda interpretations
already preserve these restrictions, so the review changes no ledger and grants
no fit release. The cross-ledger case screen still has ten candidates.
The original 35 have an authored, source-bound review in
`fee_semantic_review_v1/review.json`: 11 false alarms, 22 confirmed scope issues,
and two partly confirmed. Class availability is not fee recurrence, and an annual
inspection frequency is not necessarily the financial billing period. Private
rent, government fees, taxes, bundles, subtotals and hypothetical charges remain
distinct. This sidecar does not change the money schema or automatically enforce
compiler restrictions. Unflagged fees have not all been semantically audited.
The additional free-monthly-MUNI-pass flag is reviewed in
`legacy_ga_parse_v1/parent_fee_review.json`: recurrence is real, but a zero
recipient price does not become nonzero with repetition. The substantive
restriction is benefit eligibility/category, not a claimed arithmetic error.
The $50/month repayment candidate is confirmed in batch 005's parent
review: its recurrence is real, and it is benefit recoupment rather than an
administrative fee. The full alleged debt and installment payments overlap.

The Solano packet `calguns_324124/` adds 200 pages, 2,996 posts, 692 measurements,
34 count claims and 296 attributed episodes. Parent validation independently
passes all 12,205 evidence/count/sidecar quotations and 669 input/output hashes;
eight supplemental body/signature/edit views replay from the original captured
HTML. The reviewer recomputes 16 date intervals and two fee-component sums.
Four count claims require a requested-versus-performed correction hold, and a
generic renewal-course duration must not silently become an individual case
observation. These holds and cohort/dependence restrictions are mandatory review
inputs, not automatically enforced compiler rules. Existing 628 measurement
semantic-gate entries remain; the other 64 are not thereby certified fit-ready.
The 91 empty captured bodies remain documented gaps. This is a spot check, not
a second exhaustive reading or a claim of recovered live-forum completeness.

The latest Alameda packet selects `calguns_324054/reviewed_v2/`: 196 pages,
2,926 posts, 475 measurements and 23 count claims. Independent parent validation
passes 1,597 literal evidence/count references and 645 hashes. Six aggregate
attendance/group-window records are revised from active work to elapsed time;
one group endpoint becomes an upper bound. A seventh correction recognizes a
captured September 1 edit supporting reported issuance, but does not confuse
issuance with physical pickup or legal closeout. Parent review recomputes four
date intervals and three fee-component sums. Historical route changes, repeated
updates, partial fee bundles, 56 empty captured bodies and unresolved segment
mappings remain explicit. The next thread is being read as one complete unit.

Reddit 004/006/008 now have preserved reviewed packets; 007 has a parent hold
sidecar. Independent revised checks pass 53/175/171 literal references and
88/100/79 hashes respectively; batch 007 passes 62 references and 40 hashes.
The reviews correct UTC-versus-local date subtraction, separate a next-day
censoring date from an interview date, keep unauthorized ATM withdrawals out of
procedural counts, and distinguish blocked phone attendance from active work.
Batch 008 adds three previously omitted numerical claims and holds Sonoma's
May 25 pickup as unresolved against a May 18 root without a captured edit date.
Its source-reported 462-day total and 461-day subtraction remain distinct;
fee totals, components and refunds are dependent, not additive observations.
Parent receipts are mandatory inputs to the new selected snapshot.

Batch 009 now selects `reviewed_v2`: 22 threads, 293 comments, 50 timing/fee
rows and five count claims. Parent checks pass 255 literal references and 76
hashes. The eight-day ready-for-pickup interval no longer claims closeout;
previously omitted pending ages and two unanswered online appointment requests
are retained. The conflicting 13-month/Jan-to-Jan chronology and unresolved
issuing authority are explicitly held, as is an ordinal “on day 7” pending age.

Batch 010 also selects `reviewed_v2`: 22 threads, 396 comments, 42 measurements
and one count claim. Parent checks pass 180 literal references and 74 hashes.
The four-week wait is now interview-to-approval, not a whole application; the
three-week forecast is an upper estimate after psychological evaluation; a later
denial supersedes an older pending snapshot. An indirectly attributed agency
stays qualified. Hypothetical staff-hours move out of elapsed time into a native
agency-labor claim; omitted training and completed-stage reports are retained.

Batch 011 selects `reviewed_v1`: 28 threads, 400 comments, 69 measurements,
four count claims and 32 attributed episodes. Independent parent checks pass
328 literal references and 81 hashes, and recompute 21 date intervals and two
fee sums. Corrections distinguish prospective pickup from completed closeout,
restore an exact reported interview total, fix invented/truncated author names,
link the captured submitter's qualification comments to the root episode, and
retain a previously omitted dated application-to-qualification timeline. The
root's later update, conflicting stated/calendar duration and $20 fee-sum
discrepancy remain explicit. Parent receipt:
`exhaustive_reddit_batch011_parent_semantic_review_v1.json`. This is a targeted
semantic audit, not a second exhaustive reading of all 400 comments or fit release.

The parent independently recomputes all 24 date intervals across these packets
and their two fee-component sums. Original packets and intermediate revisions
remain intact. Source-bound revision requests and final parent receipts are
saved separately; quotation integrity is not complete recall or fit readiness.

### Supplemental source and administrative checks, 16:13 Pacific

`calfresh_cf18_cohort_parse_v1/` accounts for the six fiscal-year data workbooks,
one blank reporting form, the reporting-instruction letter and captured release
page. It retains **3,422 county/statewide-month rows × 68 variables = 232,696
native cells**. Fifty-eight reporting months are represented; missing months and
nonreporting cells remain visible. These are not 232,696 independent observations,
and the packet's canonical evidence ledger has zero numeric measurements.

The parent's separately written OOXML replay passes all 232,696 exact stored
type/value/formula checks, 59 manifested hashes, all six matching dictionaries,
6,844 mean/bin feasibility checks and 22 literal evidence/count references.
Receipt: `calfresh_cf18_parent_validation_v1.json`. Visual spot checks of the
instruction letter's physical pages 29–30 confirm the application-or-discovery
origin for expedited approvals and the need for county comments to interpret
zeros. This is not a second full reading of the letter.

Important retained limitations: 39,603 ambiguous published zeros, 5,032 stored
blanks, 13 literal `BLANK` values, 54 date/report-month conflicts, 331 zero-bin
cohorts, 16 mean/bin feasibility flags and 158 incomplete mean/bin pairs.
No suppressed values are imputed. County and statewide summaries overlap;
the latter are not another independent sample. Means are not medians, report
months are not automatically every churn measure's cohort month, and the
native aggregates are not yet a supported V6 likelihood.

The whole-thread parent checker now accepts explicitly manifested recovered
root indexes via `--root-context-index`, joined only to the exact missing
thread. It rejects replacement of existing roots, wrong identities and unbound
sources. `reddit_root_resolution_audit_v1.json` exercises all 88 frozen batches
(1,799 threads), including 25 recovered roots across 21 batches, and eleven
invalid dependency mutations. This is an inventory check, not a claim to have
parsed the remaining comments. The selected batch 008 still passes its 171
literal references and 79 hashes with the strengthened checker.

A separate solar denominator audit identifies eleven jurisdiction counts
misused as permit-case sample sizes and seventeen endpoint-denominator holds.
See the [administrative-cohort update](2026-09-19-v6-evaluation-and-selection-progress.md#administrative-cohort-readiness-2310-utc).

The first exhaustive Reddit batch has 24 within-thread cases and five count
claims. Parent validation passes 198 literal evidence/count references and 83
hashes across 64 artifacts. The parser's broader 238-reference check includes
additional sidecars, so the different denominators are not a discrepancy.
Eighteen of its measurement rows come from reused roots and remain dependent.
Parent semantic review holds a 4.5-hour shared buyer/seller visit whose ledger
incorrectly spans through pickup, and rejects qualification shots as procedural
attempts. Seven censored or chronology-uncertain durations require their endpoint
annotations before compilation; a core `individual` field alone must not turn
them into completed waits. Bundle components, refunds and prospective fees
also remain distinct. These decisions are bound in
`exhaustive_reddit_parse_v1/batch001/parent_semantic_review.json`.

Batch 002 adds two whole threads, 397 comments, six measurements and four count
claims. Parent checks pass 39 literal evidence/count references and 23 hashes.
Its review holds a pickup-notification interval incorrectly labeled `closeout`
and an uncertain observed-versus-normative reference-call count. The two-day,
16-hour course and its four-hour component are not additive burdens.

The selected revisions of batches 001–003 now resolve those specific errors:
the shared 4.5-hour transaction is an elapsed step, not summed person-hours
through pickup; eighteen qualification shots are removed from procedural
counts; batch 002's endpoint is pickup notification and its three-reference
claim is normative rather than observed completed calls. Batch 003 removes a
general LASD backlog claim falsely represented as a personal censored case and
an ADU project-age claim falsely anchored at permit submission, while explicitly
placing two subsequent waits after training/final-paperwork completion.
Independent revised checks pass 200, 39 and 150 literal evidence/count
references respectively, with 105, 43 and 85 hashes. Narrow resolutions and
remaining holds are bound in `reddit_parent_revision_review_v1.json`; nothing
releases root reuse, overlapping scopes, unknown authorities or censoring holds.

Batch 005 adds 18 threads, 393 comments, 15 measurements and one qualified
appeal-count claim. Parent validation passes 85 literal references and 55
hashes. Its review preserves uncertainty in month-resolution intervals,
benefit-recoupment versus fee categories, recurring repayments, total/component
fees, and whether a later-described appeal is included in the reported two.
This is semantic review of every extracted measurement and selected full roots,
not a second exhaustive reading of all comments.

San Diego 1302365 contributes 548 measurement rows, including 60 qualitative
observations, and 41 count claims. Its 326 case declarations are not 326
independent completed applications. The parent-selected `reviewed_v1/` corrects
one observed 45-day booking-to-rescheduling-callback interval that an overly
broad clock category had labeled counterfactual schedule savings. Values,
quotes, case IDs and original files remain unchanged. Parent validation passes
2,051 literal evidence/count references and 620 hashes on the revision. The
review covers eight reproducibly sampled numeric observations and selected
high-risk clock categories, not a second exhaustive reading of all 187 pages.

The 27-document legacy GA packet is complete, with 29 measurements, three
normative count claims and 53 separately typed numeric rules. Parent validation
passes 111 literal evidence/count references and 75 hashes. Crucially, **all four
substantive sources are exact text aliases of earlier GA artifacts**, and all
29 measurement rows come from those sources. The packet is a completed
re-reading/extraction, not 29 independent new observations. Its required
`parent_dependency_review.json` binds those aliases and the remaining unit,
recurrence and historical-applicability restrictions. Nothing establishes an
observed individual claimant wait in this packet.

The snapshot also selects `calguns_324103/reviewed_v2/` and
`calguns_324125/reviewed_v1/`, preserving both original packets. The San Francisco
revision restricts a zero-government-fee claim to its stated subset; it is not a
claim that the whole process is free. Independent checks pass 849 literal
evidence/count references and 231 hashes. The Sonoma original falsely passed a
quote check by appending captured HTML to the Markdown under the old document ID.
Its reviewed revision instead creates two separately identified, exact HTML byte
spans and retargets the references. Independent checks pass 168 evidence/count
references and 202 hashes across 79 main pages plus two source projections. The
original invalid receipt remains preserved and explicitly invalidated.

The earlier 38-ledger review found 1,333 fee rows, 35 fee-scope review candidates and ten
cross-ledger case-linkage candidates. All 125 cached Reddit comments omitted
from the first freeze are now read and included in the selected supplemental
packets; three already-parsed root posts are context only. The two packets add
three measurements and two item-count claims. Parent checks pass 30 literal
evidence/count references and 50 hashes. Fifty-two of the 60 UI comments are
dependent moderator boilerplate. All three retained measurements require fit
restrictions: a bundled project cost is not a government fee, a prospective
five-month increment is not an operation duration, and a two-hour response has
unresolved program/contact-route context. The correction/relocation counts
likewise need a granularity mapping, not conversion into visit counts.
`reddit_comment_supplement_parse_v1/parent_semantic_review.json` is a required
review, not an automatic compiler filter. Details:
[supplemental source freeze](2026-09-19-supplemental-source-freeze.md).

A later provenance check also puts ten old CPRA measurements and their source
document's structural claims on review hold: that frozen ordinance document is
an AI summary, not raw primary text. The new required hold set is
`runs/rw_parse_20260919/cpra_source_provenance_v1/reviewed_fit_holds_v2.json`.
It extends, rather than erases, the earlier holds. The 13 fresh CPRA primary
captures are now parsed in `cpra_supplement_parse/reviewed_v1/`: 50 measurements,
16 count claims and eight cases. Independent validation passes 172 literal
evidence/count references and 55 hashes. Parent reconciliation maps all ten
AI-summary measurements to primary support, preserving endpoint, fee-unit and
exception qualifications. Receipt: `cpra_source_provenance_v1/primary_claim_reconciliation_v1.json`.
Neither ledger is silently merged or rewritten; the ten older claims must not
be counted again as independent observations. Five public-tracker pending ages
remain status proxies, not verified unfinished agency processes. The archived
ordinance's applicability also needs version matching; capture date is not
legal effective date. Of the 4,664 legacy Reddit post records, 34 have now been
read as dependent root context in exhaustive batches 001–002; that queue as a whole
is not complete, and the remaining posts are not counted as parsed.

At 13:12 Pacific the known forum retrieval gaps were closed: **577 new pages /
8,655 surviving posts**, followed by a complete read-only byte/render check.
`FORUM_WORK_PLAN_v3.json` joins those pages and the earlier ordinary-page
supplement without modifying v2 or any existing sources. It covers **5,378
forum main documents: 830 ordinary and 4,548 megathread pages**, still 19 whole
megathread jobs. Los Angeles now covers pages 1–1,152, and San Bernardino 1–621;
both endpoints match navigation on freshly captured pages. Capture dates remain
mixed, and missing media/deleted posts are not reconstructed. These pages are
retrieved and queued, not yet parsed. The 876 completed megathread pages above
remain the accepted reading coverage, not 4,548 completed pages.

The independent joined-page audit subsequently checked all **4,548 megathread
pages / 68,090 post occurrences** and 9,136 hashes. It found no repeated post
IDs, no missing numbered pages, and no later page advertised by the checked
first/last/boundary navigation. It records 1,743 empty post bodies; those are not
recoverable statements or parsed evidence. Receipt:
`runs/rw_parse_20260919/joined_megathread_page_audit_v1.json`. This verifies the
known thread queue, not the completeness of every forum or source on the web.

The later [SolarTRACE input/sampler audit](2026-09-19-solartrace-input-and-sampler-audit.md)
independently replays the saved SK3 draws, identifies duplicated source summaries
and unit/actor/zero semantics, and records a same-target V6 sampler option. Those
fits are not accepted agency-speed results, and the new mechanics probe is not a
substitute for correcting their inputs.

## Scope and evidence

Starting point: [Claude's handoff](2026-09-19-parse-handoff-to-codex.md).
The reported 27 accepted ledgers and 4,400 measurements are undergoing independent
revalidation and semantic spot checks. A successful quotation/schema check proves
neither complete extraction nor correct interpretation of the quote. A manifest
declares provenance; it does not prove that an agent could access only its allowed
inputs. The root agent has inherited project context and records that limitation
on its authored parse.

At takeover, two bounded cheaper-model audits began checking the raw-to-frozen inventory and
the accepted ledgers. A fresh-context parser began thread 324062, reading
all 47 pages in numeric order and checkpointing case identity and claims per
window. Earlier forum conclusions are not included in that parser's instructions.

## Verified findings and work completed

- `pipeline/procbench/plan_forum_parse.py` verifies the hashes of all 4,800 frozen
  forum artifacts and assigns each exactly once. Its saved work plan is
  `runs/rw_parse_20260919/FORUM_WORK_PLAN.json`.
- The remainder comprises **19 unique megathreads / 3,971 artifacts**, rather than
  20 unique threads. Thread 324077 was counted in both slice inventories. The
  eight ordinary batches contain 829 artifacts; seven previously parsed batches
  contain 828.
- The final ordinary batch, `calguns_a` batch 5, was read in full and written to
  `runs/rw_parse_20260919/calguns_a_batch5/`. Its four Lassen posts contain no
  quantitative burden claim. Qualitative broken-link access friction is retained;
  the later quotation of that complaint is not another case. Both contracts pass
  and six literal quotations match. Independent review is pending.
- A substantive error occurs in batch 1's
  `calguns_a_b1__m__lasd_mikeg2503_filing_to_interview_call`: the interpretation
  calls the 265-day interval pure agency queue time and says the applicant did
  nothing, although the same quote includes Live Scan submission during that
  interval. The date arithmetic is correct; the attribution is unsupported.
- The HTML places Mikeg2503's timeline in `.post-signature`, separately from the
  post body. The rendered text loses that boundary. A post date therefore cannot
  date the signature's current contents or establish whether a pickup date was
  scheduled or observed when the post was made.
- `pipeline/procbench/project_forum_structure.py` creates public-source companions
  with post ID, author, post date, body, own-body view, attributed quotations, and
  signature separately. It verifies the original HTML and rendered artifact hashes
  against the existing freeze. The original artifacts remain available. Initial
  projection covered all 47 pages of thread 324062 and 22 of thread 1790537,
  producing 1,012 posts with no projection failures. A full version adding
  canonical-URL page identity is running under
  `runs/rw_parse_20260919/forum_structure_v2/`.
- The filename-based plan identifies page gaps, but these require checking against
  source metadata. The inventory audit found that `calguns_324096_page1.html`
  actually has canonical URL `/page2`; the separately named canonical page 1 is
  also present. Therefore this is not a missing page 2. Logical page order will
  use source URL/navigation evidence, retaining the original document IDs.

## Interpretation corrections required

The unconverged solar fit's route weights remain provisional; calling that output
an established inference is too strong. Its extension process was confirmed live
at takeover, with two chains saved and the second pair at 800 additional draws.

The causal statement that forum delays are a capacity failure rather than design
is not established by reading reports of operational causes or finding no explicit
policy of delay. Those reports may support operational explanations. They do not
exclude competing explanations or eliminate forum selection bias. Likewise, 21
agency vocabulary entries plus 54 forum entries do not establish 75 distinct
operations on an applicant's path.

## Remaining execution

1. Complete the inventory audit, including files outside the 6,783 frozen
   artifacts, capture failures, derived duplicates, and missing thread pages.
   Treat the claimed roughly 14,000 files as an inventory hypothesis until units
   are reconciled.
2. Complete source-structure projection, review every failed projection and
   contradictory page identity, and build the corrected work plan.
3. Finish all thread parses with persistent per-document coverage and
   author/application-episode registries. Preserve interrupted attempts; do not
   certify their partial ledgers from schema compliance alone.
4. Independently validate claims, scope, time endpoints, speaker attribution,
   duplicate reports and coverage. Create reviewed revisions for confirmed errors
   with before/after lineage instead of silently editing accepted artifacts.
5. Freeze additional public source documents that the inventory shows were left
   outside the initial parse. Partition by actual process/jurisdiction and source
   lineage, and process all of them, documenting unreadable or unavailable inputs.
6. Finish the semantic/count/visit audits and authored structural choices needed
   by V6. Report retained, residual and informative coverage separately. Complete
   the synthetic verification and model evaluation under the existing goal.

The project is not complete. No corpus-wide completeness, extraction-recall or
posterior-convergence claim follows from this checkpoint.

### Later 1700723 checkpoint

Thread 1700723 is complete in `runs/rw_parse_20260919/calguns_1700723/`: 55 pages,
823 posts, 69 measurements and four count claims. Parent validation independently
checks 198 input/output hashes and 466 evidence/count quotations, all literal
matches; source-derived companion/signature/residual quotations are additionally
covered by the parser's broader 881-check receipt. The 48 registry entries
include prospective/outcome/count-only episodes, not 48 completed applications.
Eight empty bodies and 61 media-bearing posts remain coverage limitations.

`review_sweeps_33_ledgers/selected_ledgers.json` is the newer selected snapshot:
**33 ledgers / 5,263 measurements**, 1,278 fee rows and 35 scope-review candidates,
with ten cross-ledger quote-linkage candidate groups. Earlier snapshots remain
unchanged. The set is still explicitly not fit-ready. Thread 324103 (64 pages)
is assigned next to the same source-only parser; thread 324126 remains with its
separate parser. No claim of complete corpus coverage is made.

Thread 324126 subsequently completed all 68 pages with 40 measurements and one
count claim. Parent validation passes 154 hashes and 76 literal evidence/count
quotations (the parser's larger receipt includes 124 references across sidecars).
`review_sweeps_34_ledgers/` contains **34 ledgers / 5,303 measurements**, 1,283
fee rows, 35 fee-review candidates and ten cross-ledger linkage candidates.

Parent semantic spot checks request a preserved 324126 revision: a reporting
date is not necessarily the approval date; a scheduled 89-day appointment wait
later shortened is not an observed 89-day wait; “maybe four weeks” is not a hard
four-week upper bound; and a derived span needs its endpoint as well as its start
quoted. A possible omitted 90-second phone-conversation effort claim also needs
review. The parser will address those after the two one-document CalGuns/UI
supplements. This snapshot deliberately remains not fit-ready; integrity checks
did not conceal the semantic errors.

## Independent review results

The completed independent spot check is saved at
`runs/rw_parse_20260919/parse_quality_audit/audit.md`. It reproduces the original
27-ledger totals exactly, including 4,400 measurements and 1,466 audit-eligible
elapsed rows. All 27 pass the evidence contract against frozen sources.

It also confirms a same-application cross-post (BlacknWhite), the Mikeg timing
and route errors, and two applicant deadlines entering the eligible-duration
pool. The resulting restrictions are recorded in
`runs/rw_parse_20260919/reviewed_fit_holds.json`; this is an explicit work order,
not yet an automatically consumed compiler filter.

The new `audit_cross_ledger_cases.py` checks matching individual-case quotations
across ledger boundaries. On the 27 ledgers it produces ten candidate groups,
including apparent repeated signatures and cross-program-source copies. Candidate
generation does not merge cases: the same timeline can describe different
segments, and quoted text can belong to another speaker. All groups require
semantic linkage review. The report is `cross_ledger_case_candidates.json` under
the new run directory.

The existing fee-scope audit has now run on all 27 ledgers: 1,140 money/fee-coded
rows, with 33 candidate scope problems. Previously the saved audit covered only
760 non-forum rows. The complete new review report is `fee_scope_all_27.json`.

The independent reviewer also accepted the one-page batch 5 source parse, with
its declared inherited-context limitation. That completes source review for the
eight ordinary batches; completion of the megathreads remains outstanding.

## Later checkpoint: source reconstruction, reviewed ledgers, count-only cases

The full source-structure projection is complete: **4,800 artifacts / 69,158
posts / zero remaining projection failures**. The initial projection failures and
empty-output archives remain available; successful retries did not erase them.
`FORUM_WORK_PLAN_v2.json` binds the source-derived logical page identities to the
same frozen documents. It assigns 19 megathreads once each and exposes 577 missing
numbered pages in threads 324077 and 324096. This is not exhaustive retrieval.
The q-slice's old text projection omitted signatures; the companions restore
those boundaries/content, which still require semantic review on older parses.

Two new full megathread parses are complete and independently contract/quote/hash
checked: 324062 (47 pages, 264 measurements) and 324063 (48 pages, originally 163).
The latter received a separately saved parent semantic revision at
`runs/rw_parse_20260919/calguns_324063_reviewed_v1/`, with 164 measurements and
12 before/after edits. Original outputs remain unchanged. Important corrections:

- Counterfactual four-month time excluding personal delays is an estimate, not
  observed wall-clock time. The omitted pending total, over one year, is restored.
- “Six–eight weeks or less” does not imply a six-week lower bound; “up to about
  three plus months” does not establish a three-month lower bound.
- An eleventh-week report does not establish eleven completed weeks. Another
  reported eleven-week wait contradicts the same-case dated timeline; the conflict
  remains explicit rather than selecting a precise censoring bound.
- Calendar normalization, business-day interpretation, and an off-by-one reported
  timeline are distinguished from exact date arithmetic.
- Sheriff intake is conditional on that route, not mandatory for Police applicants.

Parent review is not described as a fresh blinded extraction: the parent inherited
mixed project context. Quote integrity also is not a complete semantic audit.

The selected completed-ledger snapshot is
`runs/rw_parse_20260919/review_sweeps_30_ledgers/selected_ledgers.json`:
**30 ledgers / 4,828 measurements**, including the reviewed revision rather than
both versions. The expanded sweep covers 1,201 fee rows, with 33 review candidates,
and still finds ten exact-quotation cross-ledger case-linkage candidates. It is
explicitly **not fit-ready**: the known identity, semantic, route and temporal
issues still need adjudication. Newly parsed historical reports must not be
silently relabeled current to get past the compiler's temporal filter; fitting
historical epochs or transporting to a current population requires an explicit
estimand and assumption.

The count-only-case defect is repaired through backward-compatible
`burden-count-evidence/2`: a quoted `cases` list allows identities unsupported by
time/money measurements while preserving typo/reference checks. The converter
accepts `--case-registry`; the compiler accepts sampling declarations for these
cases; an end-to-end fixture reaches the existing V6 count likelihood. No fake
zero-duration row is introduced. V1 behavior remains unchanged.

Source review of the firearms corpus supports eight additional case identities.
`runs/rw_parse_20260919/dros_count_case_review_v1/` contains the registry, revised
audit, provenance and unresolved decisions. Structured count claims increase from
13 to 21; all 82 original rows remain represented. Three repeated questions are
not encoded as three visits, and pending resubmissions are lower bounds rather
than final totals. Planned resubmissions and ambiguous multi-purchase histories
remain unresolved. This repairs retention, not every downstream count operator.

Validation after these changes: **863 tests passed**, with the existing generator
return-value warning. No new posterior-performance claim is made. At this
checkpoint the 74-page thread 1754542 is fully read and undergoing reconciliation;
the 37-document naturalization supplement is being parsed. The synthetic worker
has resumed hash-bound verification, and the solar extension's remaining two
chains are live at 1,200/4,000 extension draws each.

### Subsequent completions and remote recovery

Thread 1754542 is now complete: 74 pages, 343 measurements, nine count claims,
65 case episodes. Parent validation checks 1,358 evidence/count references
literally, 184 file hashes, both contracts and all coverage IDs. The parser's
larger 1,655-reference check also covers residual/linkage sidecars. Thread
1700723 (55 pages) is the next packet owned by that worker.

The 37-document N-400 supplement is complete with 23 measurements, six count
claims and a preserved 172-row administrative table. Parent revalidation checks
113 evidence/count references (84 literal, 29 presentation-normalized) with no
normalized mismatch. Its declared validator code hash predates the parent's
concurrent count-only-case change; this drift is explicitly recorded and both
contracts rerun under current code. Source artifacts and output hashes match.
The parser's claim of an independent exact normalizer is too strong: its saved
validation says it reused the contract normalizer. Parent checking is independently
implemented. That worker has started thread 324126 (68 pages).

`review_sweeps_32_ledgers/selected_ledgers.json` now supersedes the earlier selected
snapshot: **32 ledgers / 5,194 measurements**, still not fit-ready or a completed
whole-corpus parse. The full 30-ledger snapshot remains intact.

SK3 is reachable through the configured SSH alias. Sixteen completed fit-report
bundles are recovered, with verified input/report hashes. See the
[remote results and remaining diagnostic work](2026-09-19-recovered-sk3-fit-reports.md).
Several later S12 runs pass their saved convergence and numerical gates, while
the larger S03/all-five and both SolarTRACE runs fail. No jobs were restarted and
no benchmark labels were opened. This supersedes the earlier unreachable-host
note, not the still-live local solar extension.

### Later source completions and semantic review

- Thread 1700723: 55 pages, 69 measurements, four count claims. Parent checks
  466 literal evidence/count references and 198 hashes. Its 48 registry episodes
  are not 48 completed cases; empty bodies, missing media and mutable signatures
  remain explicit.
- Thread 324126: 68 pages, initially 40 measurements. The preserved
  `calguns_324126/reviewed_v1/` now has 41: approval already reported by a date is
  an upper-bound event, a scheduled 89-day appointment is not an observed wait,
  an approximate four weeks has no hard four-week upper bound, both endpoints
  support a derived span, and an explicitly at-most-90-second phone conversation
  adds payer effort. Parent checks 86 literal references and 155 hashes.
- The omitted 324095 page 6: 13 measurements and one count claim; parent checks
  41 literal references and 16 hashes. The one-page UI supplement correctly has
  no canonical burden measurements: benefit-weeks, monthly levels and seasonal
  adjustments are not processing durations or independent claimant cohorts.
  Parent checks 17 references and 16 hashes; administrative information remains
  in residuals.
- Thread 324103: all 64 main pages / 957 posts, 224 measurements, 21 count
  claims. Four quoted HTML regions omitted by the old Markdown projection are
  restored as exact UTF-8 source-byte spans, not extra retrieved pages. Parent
  checks the source offsets/hashes, 849 literal evidence/count references and 232
  file hashes, with zero mismatch. The parser's wider 1,412-reference check also
  includes its other sidecars. A preserved review is pending for one government-
  fee subtotal wrongly tagged as the whole-process total; it must not become a
  zero-cost CCW observation. Pending-age and overlap sidecars also require the
  semantic compiler review; they are not automatically enforced guards.

The last snapshot selects the reviewed 324126 version, preserves both originals,
and leaves `fit_ready: false`. Thread 324125 (79 pages, cheaper worker) and
324090 (99 pages) are active. The synthetic worker is independently repairing
and reverifying the authorized compact 438-document S12/S03 bundle, not the full
unthinned corpus. Latest reported current-input-bound passes: 96, with approved
appeal-body description repairs proceeding. Count completion is not verification
success.
