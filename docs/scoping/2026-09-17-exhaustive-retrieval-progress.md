# Exhaustive retrieval: progress and unresolved coverage

2026-09-17. Packet **N12-EXHAUSTIVE-RETRIEVAL remains open**. This is an
incremental evidence inventory, not a claim that all public material has been
retrieved. The [protocol](2026-09-17-exhaustive-retrieval-protocol.md) covers 58
counties, 14 program families and six source channels: 4,872 open checks.
The matrix now maps 782 lead references: 409 inherited P5/N11 references,
58 county-forum entry records, 173 reconciled P3/P1 references and 30 qualified
ADU follow-up references, plus 96 qualified well/discussion follow-ups and 16
retrieved well child references. Three forum
entries explicitly link earlier snapshots of the same thread. CalFresh county
references point to shared workbooks, not distinct documents per county.
The newest increment includes repeated URLs, related versions, blocked sources
and still-unreviewed applicability; these are reference IDs, not distinct
relevant documents. One Santa Cruz Mountains discussion is retained without a
forced county assignment. Ledger QA checked 83 new source hashes and 119
relative documentation links with no mismatches or broken targets.
[Integrity check](../../corpus/counties/raw/exhaustive_2026_09_17/well_ledger_integrity_audit.json).
The subsequent 16-reference import separately rechecks all 16 byte hashes and
all 4,872 matrix keys, mapped references and counts with no mismatches; all
channels remain open. It preserves portal shells, exact-byte aliases and
conflicting forms instead of treating each URL as independent evidence.
[Child import check](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_ledger_integrity_audit.json).

## Completed inventory work

| Source traversal | What is retained | What this does not establish |
|---|---|---|
| Grand-jury directory | All 58 county directory entries reconciled; 20 earlier snapshots reused; new requests, failures and replacement URLs recorded | A readable report for each county, year or program |
| Grand-jury linked indexes | 61 archive/report-page requests, plus 15 replacement/index/document requests | Exhaustion of every linked archive or every report |
| Oversight discovery | 6,852 county–URL candidates with index provenance | 6,852 reports, relevant documents, distinct cases or current sources |
| Keyword report candidates | All 284 candidate requests attempted: 279 HTTP 200, five HTTP 404 | HTTP 200 does not mean a PDF or usable evidence |
| First PDF validation snapshot | 289 PDF-named files including supplements; 232 have PDF headers and open successfully, totaling 2,600 pages; 87 have fewer than 30 extractable characters on every page; 16 raise parser warnings | Successful parsing does not establish legibility, currentness or relevance; no OCR completed here |
| CalGuns county threads | Readable entry pages for all 58 county starter threads; 43 advertise multiple pages; 4,557 pages advertised in total | First-page coverage is not full-thread or current-period coverage. One directory link was actually page 2; canonical-URL correction is recorded below |
| Reddit discovery | 1,982 keyword candidates from 4,664 unique previously retained OP IDs; 51 already have identified comment snapshots | Keywords are not semantic relevance; earlier capped and failed searches still need follow-up |
| First Reddit comment batch | 274 snapshots, 7,188 unique comment IDs; 6,918 available bodies and 270 removed/deleted/empty bodies; no overlap with 22,408 comment IDs in 1,286 earlier snapshots | These are archive contents, not 7,188 relevant claims or independent cases |
| Remaining Reddit comment batch | All 1,657 selected attempts inspected: 1,656 HTTP 200 and one timeout/API error; a separate successful retry recovers 11 comments. Original successful snapshots contain 24,992 unique IDs, 744 unavailable bodies and 127 empty readable trees | Attempt completion is not live-site completeness, relevant claims or independent cases; the original error is retained, not treated as an empty tree |
| Additional CalGuns topics | 245 entry pages plus 564 further pages inspected; the original additional requests had 562 readable pages, one timeout and one 502, with both gaps recovered in separately retained, canonically checked retries | This covers the then-advertised pages of those located topics, not all venues, later posts, hidden/deleted content or semantic relevance |
| Legacy P3/P1 reconciliation | 48 ADU primary-source leads, nine other downloaded ADU/building sources, and two CalFresh series references per county; 22 original-file hashes rechecked unchanged | Search-only, general-hub, code-only and historical-source qualifications remain; no source channel closed |
| Generic-title report follow-up | 338 selected candidates now have validated PDF references, totaling 18,533 pages and 338 distinct byte hashes; 337 are from the selected original links and one is a separately recorded Del Norte newspaper mirror | Not all 6,852 catalog links; generic relevance and publication dates remain unreviewed; mirror equivalence is unverified |
| Additional ADU discussions | 19 retained OPs/comment trees, 418 unique comment IDs; 104 already occur in a prior snapshot, leaving 314 new to that frozen prior collection | Not 19 cases or 314 relevant claims; comments were semantically read for only three trees |

The first PDF snapshot found **48 Riverside archive notices**, not downloaded
reports, behind successful HTTP responses. Their public “Continue to PDF” button
adds `archive-consent=true`; the site's own JavaScript is retained. All 48
follow-up documents are now validated PDFs: 470 additional pages, six entirely
text-sparse documents and seven parser warnings. Together with the initial
snapshot that is 280 validated PDF files and 3,070 pages, **not 280 reviewed
relevant reports**. This is an accessibility notice, not a login. Original
notice bytes remain unchanged. Three Marin downloads are Cloudflare error pages;
separately retained browser-tool PDF text must not be described as local PDF bytes.
One Sonoma file is a malformed PDF fragment despite a PDF content type.

Pagination validation found that San Bernardino's discovery URL ended in
`/page2`. The initially named `calguns_324096_page1.html` therefore holds page 2,
and appending another page suffix produced a retained HTTP 404. Preserve those
attempts, fetch the actual first/last pages with a normalized thread URL, and
use the HTML canonical URL—not the filename—as the page-number check.

The first Reddit batch has 29 empty comment trees, no returned `more` placeholders
and one tree with an absent parent comment (`1i17zf1`). None has fewer comments
than its older OP snapshot advertised, but that comparison does **not** prove
live-site completeness or recover removed text. The 1,286 prior-input hashes
were retained in `reddit_prior_dependencies_*.json` and their combined digest
verified. All 1,657 remaining uncached keyword candidates are now queued, with
no overlap with this first batch; CalFresh and permitting precede CCW in execution
order, not in final coverage scope.

That remaining queue is now finished and inspected. Its original 24,992 IDs
have no overlap with the first 274-tree batch, the frozen 22,408-ID prior set,
the 19 ADU trees or the six well/building trees. All 1,286 prior-file hashes and
new inventory hashes were rechecked unchanged. The successful timeout retry
adds 11 disjoint IDs: the two new batches together contain 32,191 unique IDs,
not cases. The first audit counter included the error among zero-comment
records; the corrected count explicitly separates 127 empty readable trees
from that one API failure. Sixty-two repeated-body groups of at least 80
characters are dependence-review candidates, not proven duplicate cases.

No `more` placeholders or foreign-thread comments were returned. Missing
parent links remain in `1i17zf1` (one) and `1pwoasy` (two). A separate documented
ID lookup returned no records for those parents; that is archive unavailability,
not proof of deletion or absence on every public source. Selection reconciliation
also checked the 51 reused candidates' 55 existing snapshots: every selected
candidate is assigned once, with no omitted or overlapping selection groups.
[Remaining-batch audit](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_remaining_inventory_summary.json);
[timeout recovery](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_1o66dph_timeout_retry_inventory.json);
[all-candidate accounting](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_candidate_queue_accounting_audit.json);
[parent-lookup attempt](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_missing_parent_lookup_attempt.json).

Reviewing the OPs of all five IHSS-keyword hits in that first batch illustrates
why the hints cannot become program-volume labels: three primarily concern
CalFresh with IHSS employment/income context; one is an IHSS provider-search
account with a qualitative worker-list delay; one lists programs in a funding
discussion. None of these **OPs** gives a numeric IHSS processing duration.
The provider-search account's San Mateo mention is a future job-location
preference, not the stated county of the past case. Comments remain separately
unreviewed; this diagnostic stratum is not an estimate of overall relevance
accuracy or proof that IHSS timing evidence is absent.
[Statement-scope spot check](../../corpus/counties/raw/exhaustive_2026_09_17/ihss_keyword_op_spotcheck.json).

A separate frozen inspection of 807 completed forum-page requests found 9,520
post containers, none without a body element, but **206 empty text bodies across
133 pages**. These are HTML occurrences, not necessarily distinct posts or cases.
Three empty-body examples were inspected directly; their cause is not known.
No nested-comment indicators were detected, which does not prove that no
server-only or inaccessible comments exist. The first edit-count selector missed
the site's actual class and its zero result is explicitly invalidated; the
read-only QA helper is corrected without changing the running collector.
One checked page uses Windows-1252, so decoding every page as strict UTF-8 is
unsafe. [QA qualification and examples](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_node_audit_qualification.json).
The corrected edit inspection finds 958 edit markers on 504 of those 807 pages,
including three posts created before September 2022 but edited within the
window. These examples make the historical-page gap concrete. A
[full-history follow-up plan](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_historical_followup_plan.json)
records 3,890 then-unvisited starter-thread pages; some are still being handled
by the active creation-date crawler, so reconcile completed requests before
launching that follow-up. This is a pending queue, not a completed retrieval.
[Corrected edit inspection](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_edit_followup_summary.json).

A later frozen audit covers the first2,124 full-history continuation pages.
After a separately retained one-page parser recovery, it accounts for31,860
distinct post IDs/containers, including799 empty bodies on531 pages and2,721
edit markers on1,452 pages. Source hashes did not change. On LA thread page805,
the default lxml/auto-encoding path stopped after7 posts; other parsers and
explicit valid-UTF-8 decoding recover15. The literal charset declaration and
autodetection disagree, so intended text encoding remains qualified. Original
counts and bytes are preserved; this is not a whole-corpus text-equivalence or
live-site completeness claim, and the3,241-page collector is still running.
[Reconciled node audit](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_history_node_audit_01_reconciled.json)
and [encoding check](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_history_parser_encoding_check.json).

## CalFresh timing-source follow-up

All five previously unfetched CF 18 workbooks linked by the current CDSS index
were retrieved successfully. The earlier FY 2024–25 source/export is unchanged.
The new files open and contain all 58 county names, but neither their fiscal-year
filenames nor a successful download establishes a complete annual panel:

| Workbook | Months in the literal `Date` column | County rows | Rows whose `Date` and `Report Month` disagree, including statewide |
|---|---|---:|---:|
| FY 2020–21 | February–June 2021 | 290 | 0 |
| FY 2021–22 | July 2021–June 2022 | 696 | 27 |
| FY 2022–23 | July 2022–April 2023 | 580 | 27 |
| FY 2023–24 | July 2023–June 2024 | 696 | 0 |
| FY 2025–26 | July 2025–January 2026 | 406 | 0 |

The mismatches include July 2021/2022 `Date` values paired with July 2020
`Report Month` values. Preserve both columns; do not silently select one. The
FY 2020–21 data also include June while its release-summary rows end at May.
Across these files, 74 county rows have all 68 measure cells blank. Missing
months/rows are not zero burden, and these raw files are **not harmonized or
merged into the earlier export**. Approval-conditioned timing, expedited-clock
definitions, suppression and overlapping means/bins still require their source
qualifications. [Requests](../../corpus/counties/raw/exhaustive_2026_09_17/calfresh_cf18_followup_attempts.json);
[hashes, literal date pairs and release notes](../../corpus/counties/raw/exhaustive_2026_09_17/calfresh_cf18_followup_inventory.json).

## Source spot checks and implications for synthetic documents

These are document-specific observations, not population estimates. Historical
reports remain explicitly historical. PDF page numbers are one-based.

| Source | Observed material | Modeling/retrieval qualification |
|---|---|---|
| [Modoc 2024–25 report, p. 8](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_06049_repair_14.pdf) | The jury could not locate two prior years' reports | Distinguish institutional existence, publication and discoverability; not proof the reports never existed |
| [Napa building department, 2024, pp. 2, 5–6](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06055_22dd9d2541a7.pdf) | Cross-division review, fire-review bottlenecks and competing priorities | Relevant agency-side constraints, but no identified intrinsic agency effect or numeric service distribution |
| [Napa use permits, 2025, pp. 5–6](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06055_893a9acd471f.pdf) | Completeness review and hourly cost recovery | A completeness-review clock is not end-to-end approval; billable hours are not elapsed days |
| [Contra Costa agricultural contracts, 2023, pp. 5, 8, 10–11](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06013_71c1770fa69f.pdf) | County/city administration, pending cases and departmental workload | Agricultural-preservation contracts are **not** restricted-material permits. Workload totals cover other processes; reported 105/108-day figures require denominator/version reconciliation |
| [Nevada CalFresh, 2020, pp. 2, 5–6](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06057_78602ac61c1c.pdf) | Interview access, staffing, turnover and training | Historical mechanism evidence, not a measurement of the 2026 route or current delay |
| [Contra Costa IHSS, 2011–12](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06013_1ad426483f1c.pdf) | Manual timesheets and oversight workload | Historical only; do not transplant the manual workflow into a contemporary process without checking changes |
| [Lake IHSS response, July 29, 2014, p. 1](../../corpus/counties/raw/exhaustive_2026_09_17/gj_06033_4415c58c8936.pdf) | Contracts assigning a full-time investigator and half-time prosecutor to IHSS fraud work; visually verified after OCR | Staffing allocation is not measured hours per case; oversight agencies need not be on every recipient's route; historical, not current staffing |
| [Tulare 2025–26 consolidated report, pp. 12–15](../../corpus/counties/raw/exhaustive_2026_09_17/tulare_grand_jury_2025_26.pdf) | Mobile-food oversight, inspections, complaints and multiple enforcing authorities; pp. 12–14 visually verified after OCR | Department-wide businesses/programs are not food-permit applications; parent agency/division are not automatically two actors; enforcement is not every applicant's route |

Reports and their agency responses are separate sources about related claims,
not automatically independent observations. A title containing “medical” or
“agriculture” is insufficient for a Medi-Cal or restricted-material label.
Government mirrors and historical copies require version comparison. Forum
quotes, edits and reposts require statement-level case and source linkage.

Review of the Alameda jury's 2021–22 report, PDF pp.149–161, adds another
jurisdiction warning: the chapter concerns **Oakland city's** plan-check office,
not Alameda County's unincorporated permit program. It separates assignment
queues, expedited service and revision cycles, and reports mismatches between
payroll overtime and applicant billing. These are attributed historical audit
findings, not verified per-case labor measurements. Publication county cannot
become the administering agency, and fees cannot be converted mechanically to
staff hours. [Chapter review and input hash](../../corpus/counties/raw/exhaustive_2026_09_17/oakland_plan_check_chapter_review.json).

A Kern FY2022–23 aging-services report provides a useful scope check on IHSS
keyword matches. Its urgent-response/caseload discussion concerns **Adult
Protective Services**; its jury-observed phone hold concerns a nonprofit-run
general referral line. Neither is an IHSS application-processing mean. Department
staffing, IHSS client counts, partner lists and oversight-response deadlines
measure different things. Embedded text across all19 pages was read; follow-up
reads cover page13 visually and OCR on pages14 and17–19. The appendix's budgeted
positions are not the same quantity as reported employees. The Board's response
reports call-center changes but does not independently measure improved waits.
No numerical IHSS observation was created; complete layout review remains open.
[Statement-scope review](../../corpus/counties/raw/exhaustive_2026_09_17/kern_aging_statement_scope_review.json).

An embedded-text keyword index has traversed all 338 generic-title PDFs to
locate passages for semantic review. Coverage QA found no missing, extra or
duplicated source records, no failed extraction commands and no changed input
hashes across the 18,533 pages. This is discovery, not program labeling:
medical services do not imply Medi-Cal, ballot-measure finance does not imply
ballot-processing evidence, and sparse/garbled pages still require OCR or
visual work. No corpus-volume or calibration parameter is updated from hits.
[Index coverage audit](../../corpus/counties/raw/exhaustive_2026_09_17/generic_program_index_coverage_audit.json).

The page-level index finds 2,956 sparse pages across the generic-title set.
Exact-PDF-hash and page matching reuses existing OCR for 1,819; another 1,137
pages across 123 mixed PDFs have now finished. The combined check covers all
2,956 selected source-hash/page pairs with no missing, extra or duplicate new
records, failed commands, incomplete chunks or changed source hashes across
338 inputs. However, 332 selected pages still yield fewer than30 OCR characters;
these have not all been visually classified and are not assumed blank. OCR
cannot establish semantic relevance or resolve every garbled font.
[Reconciled remaining queue](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_generic_remaining_sparse_queue.json).
[Completed coverage audit](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_generic_sparse_coverage_audit.json).

The sparse-text rule also misses some mixed pages: Kern page13 has a selectable
appendix heading/footer but its substantive budget table is an image, confirmed
visually. A separate read-only image-layout inventory is checking all338 PDFs
for large embedded images on pages outside the sparse selection. Image size is
a discovery heuristic, not proof of unread text or an exhaustive layout check.
That inventory now covers all338 references/18,533 pages with unchanged hashes
and flags3,474 candidate pages across215 documents. Some have embedded OCR
overlays or photographs; this is not3,474 missing-text pages. Native parser
warnings, crop/rotation cautions and two interrupted transports are retained.
No additional bulk image files are generated by that inventory. A separate
word-location screen is prioritizing text-poor image regions for review.
[Image-layout audit](../../corpus/counties/raw/exhaustive_2026_09_17/mixed_image_index_coverage_audit.json).
The region screen now covers all3,474 candidates and identifies1,200 pages in
154 documents with at least one large image containing fewer than30 existing
word-center characters. Other pages may have text overlays, not necessarily
complete transcriptions; low-text images may be photographs or maps. No source
hash changed, and native warnings are retained. The additional OCR queue is
**prepared but not started**: shared disk fell to9.5GiB at06:37 PDT.
[Region screen](../../corpus/counties/raw/exhaustive_2026_09_17/mixed_image_regions_summary.json)
and [held queue](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_mixed_image_regions_queue.json).

All2,956 retained sparse-page OCR outputs have also been keyword-indexed:
35 documents have at least one program hint, without asserting relevance,
independent cases or measurements. Full transcripts remain linked for review.
[OCR discovery index](../../corpus/counties/raw/exhaustive_2026_09_17/generic_sparse_ocr_program_index.json).

Colusa's OCR IHSS hit is only a brochure-catalog entry; nearby delay complaints
concern Child Welfare Services and family reunification. Reading pages33–35
does not retrieve the underlying brochure or validate the complaint cases.
[Partial-chapter scope check](../../corpus/counties/raw/exhaustive_2026_09_17/colusa_brochure_statement_scope_review.json).

Tehama's2022 report contains older response letters about the IHSS Public
Authority advisory committee. They concern meeting publication, quorum and
website updating, not recipient application times. Its cover, inherited index
title and individual letter dates differ; the response attributes an apparent
absence of meetings to an outdated website. Preserve that as an attributed
publication-lag claim, not verified absence of agency activity. The Board
letter and attached department response are dependent sources within one PDF.
[Dated statement-scope review](../../corpus/counties/raw/exhaustive_2026_09_17/tehama_ihss_continuity_statement_scope_review.json).

Local OCR has completed all 93 entirely text-sparse PDFs (617 pages), with no
failed commands or detected output truncation. Per-document results are under
`raw/exhaustive_2026_09_17/ocr/`. Images were streamed
between the existing PDF renderer and OCR engine, not stored in bulk. These are
**unreviewed transcriptions**. The Lake page above was additionally inspected
visually; OCR had misread the IHSS acronym in several places, illustrating why
numeric values, dates and quotes require verification.
[Visual-review record](../../corpus/counties/raw/exhaustive_2026_09_17/lake_ihss_staffing_visual_review.json).
The Tulare food-cart pages now have a separate
[visual-review record](../../corpus/counties/raw/exhaustive_2026_09_17/tulare_food_cart_visual_review.json)
and OCR, resolving their garbled embedded font for the checked statements.
[OCR completion record](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_batch_summary.json).
All 93 original PDF hashes were rechecked unchanged. The batch contains
1,308,332 output characters, but one Mono assessor-response page remains
nearly empty after OCR. Visual inspection shows faint text, **not a blank
page**; a 400-dpi sparse-text retry is recorded separately and readability
remains unresolved. Command success is not complete information recovery.

The generic-title batch required another 66 Riverside public archive links;
all now open as PDFs (878 pages). Two large reports exceeded the initial size
cap and were retrieved after checking their advertised sizes. The Los Angeles
response has 702 pages, of which 701 lack usable embedded text: an
**entire-document image-only filter alone would miss that almost wholly scanned
document**. Del Norte's initial HTTP 200 was a Google Drive viewer, not PDF
bytes; a 41-page newspaper mirror is separately labeled and retained.
[Reconciled inventory](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_generic_reconciled_inventory.json).

Six additional entirely text-sparse reports have completed OCR (157 pages);
all six source hashes remain unchanged and no page command failed. These
remain unreviewed transcriptions. The next queue's 1,541 selected pages in
35 PDFs and the 121 pages in ten Riverside PDFs plus the Del Norte mirror
now all have retained OCR. An independent coverage check found no missing,
extra or duplicated page records, no failed page commands, and all 46 input
hashes unchanged. Twenty-nine pages still yield fewer than 30 characters;
success is not proof of legibility or a blank page. The interrupted worker's
1,200 saved pages were preserved; only its 341 missing durable pages were
resumed in smaller batches after an output-collection failure.
[Completed increment](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_generic_batch_summary.json);
[sparse-page queue](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_sparse_followup_queue.json);
[combined coverage audit](../../corpus/counties/raw/exhaustive_2026_09_17/ocr_sparse_and_notice_coverage_audit.json).

The [ADU follow-up](2026-09-17-adu-primary-followup.md) preserves new official
guides, fees, forum case-boundary examples and regional-survey versions. A
visually checked timing chart/table conflict persists from SBCAG's September
draft into its October publication; neither representation was silently
chosen as calibration truth.

The [well-permit follow-up](2026-09-17-well-primary-followup.md) records searches
across the remaining P5 instruction gaps, 87 selected references (78 actual
requests, 50 HTTP 200 responses, 28 failures and nine host-block skips), and
17 validated PDFs / 126 pages. These are not all reviewed instructions.
Six additional public discussion trees were read at statement level; 71
unique comment IDs include duplicated stories, prospective inquiries and
non-permitting costs/work. None was promoted to a processing-time datum.

An additional jurisdiction spot check contradicts the county-covariate README's
blanket unincorporated-area interpretation for environmental health. LA County
well approval covers the county except three independently administering cities;
housing has additional contract/code-adoption boundaries. Population outside
cities is not a universal exposure denominator. Keep an agency–program–service-area
crosswalk, and do not transport a land-use boundary to food/well permitting.
[Official well-program source](https://publichealth.lacounty.gov/eh/safety/state-small-water-systems-wells.htm);
[retained request records](../../corpus/counties/raw/exhaustive_2026_09_17/la_program_jurisdiction_attempts.json).

## Work still in progress

- Last-page attempts are complete for the 43 multipage county threads, including
  the corrected San Bernardino URL. The descending creation-window traversal
  stopped after 1,005 intermediate-page attempts: Contra Costa hit a 502 at
  page 140, so an empty remaining-thread list does not prove window completion.
  Its gap and older pages are included in the full-history continuation.
  The 245 additional-topic entry pages and their 564 further advertised pages
  are inspected, with two original failures preserved and successful retries
  checked separately.
  The earlier prose incorrectly said 360: direct inspection of the saved queue
  shows 564 distinct thread/page pairs across 41 topics. The collector uses that
  full queue; this was a reporting error, not a 360-page retrieval cap.
  An initial full-history queue retrieved 223 pages before a timeout; that
  page succeeded on a separately checked retry. After the creation-window
  collector stopped, reconciliation produced 3,241 still-unvisited pages in
  27 starter threads, now running as one forum collector. This includes the
  previously deferred Los Angeles/Contra Costa history. Page canonicals,
  not filenames, prevent duplicate requests; transient failures remain explicit
  gaps even if every queue item is attempted.
  [Reconciled continuation](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_historical_resume_queue.json);
  [additional-page inspection](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_additional_pages_inventory_summary.json);
  [retry checks](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_transport_retry_inventory.json).
- The 1,657-comment-tree queue is retrieved and inspected, with its one timeout
  separately recovered. Continue unresolved county/program searches,
  capped/failed query follow-up and statement-level relevance review; the
  1,982-candidate accounting does not close the broader search matrix.
- Resolve image-only documents and garbled fonts; Riverside's 48 notices are
  resolved, but readability/currentness and claim review are separate steps.
- Inspect generic-title consolidated reports, not just title-keyword hits;
  resolve remaining archive navigation, blocked hosts and missing-year links.
  The 338 recent-looking generic-title candidates now have PDF references as
  qualified above. Other catalog links and years remain open. Disk space was
  about 59 GiB free at03:03 PDT but fell to9.5GiB by06:37. New bulk downloads
  and the prepared mixed-image OCR queue are held; recheck before resuming.
- Reconcile earlier official instructions, administrative datasets, advocacy
  materials and county-specific sources into the 4,872-row matrix. At present
  it imports P5/N11 references, the 58 forum-entry records and the P3/P1 primary
  sources/series, new ADU and96 well/discussion plus16 child references above,
  not the whole corpus.
  The 30 new references include blocked/not-fetched leads and related versions,
  not 30 fully reviewed independent documents. Matrix integrity
  checks still show 4,872 unique rows, 782 unique lead IDs, no unresolved mapped
  reference and zero closed channels.
- Resolve relevance, jurisdiction, currentness, copied facts, same-case claims
  and overlapping cohorts before converting retrieval counts into calibration
  targets. No corpus count here identifies real posting probabilities.

## Reproduction and provenance

All new raw material and request records are under
[`corpus/counties/raw/exhaustive_2026_09_17/`](../../corpus/counties/raw/exhaustive_2026_09_17/).
The following inventories describe completed steps, not complete channels:

- [Grand-jury candidate catalog](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_link_catalog.jsonl)
  and [input hashes](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_link_catalog_inputs.json).
- [Initial document request summary](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_document_batch_summary.json)
  and `grand_jury_document_attempts_*.json` request records.
- [Initial PDF readability inventory](../../corpus/counties/raw/exhaustive_2026_09_17/grand_jury_pdf_readability_inventory.json).
- [Riverside public-link follow-up](../../corpus/counties/raw/exhaustive_2026_09_17/riverside_archive_followup_attempts.json)
  and [its PDF validation](../../corpus/counties/raw/exhaustive_2026_09_17/riverside_archive_readability_inventory.json).
- [County-thread discovery](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_thread_discovery_queue.json),
  [first-page attempts](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_first_page_attempts.json)
  and [first-page inspection](../../corpus/counties/raw/exhaustive_2026_09_17/calguns_first_page_inventory.json).
- [Reddit candidate queue](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_comment_discovery_queue.json)
  and immutable `reddit_comment_attempts_*.json` checkpoints.
- [First comment inventory and comparison](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_comment_inventory.json),
  [first batch status](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_comment_batch_summary.json)
  and [remaining candidate queue](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_remaining_comment_queue.json).
- [P3/P1 reconciliation and unchanged input hashes](../../corpus/counties/raw/exhaustive_2026_09_17/legacy_p3_p1_reconciliation.json).

`extract_report_links.py` and `inspect_calguns_page.py` in that raw directory
reproduce link/HTML inventory from retained inputs without network or writes.
No model fits, unit tests, messages to source authors or access-control bypasses
are part of this retrieval increment.
