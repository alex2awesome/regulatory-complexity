# Supplemental public-source freeze (2026-09-19)

## Result

The run-local supplemental freeze at
`runs/rw_parse_20260919/supplemental_sources/` contains 40 public source
documents omitted from the 2026-09-18 freezes. All 40 converted successfully;
none was unreadable. A clean verification recomputed 120 hashes (origin,
rendered source, and parser artifact for every document) with zero mismatches.
Existing freezes, artifact indexes, and queues were not changed.

| Process | Selected | Readable | Unreadable | Parser index |
|---|---:|---:|---:|---|
| `calguns_g` | 1 | 1 | 0 | `calguns_g/artifact_only_index.json` |
| `n400_naturalization` | 37 | 37 | 0 | `n400_naturalization/artifact_only_index.json` |
| `ui_claim` | 1 | 1 | 0 | `ui_claim/artifact_only_index.json` |
| `solar_permit` | 1 | 1 | 0 | `solar_permit/artifact_only_index.json` |

The set-level entry point is `supplemental_sources/manifest.json`. Each process
also has a `manifest.json`, `frozen_index.json`, `source/`, and `artifacts/`.
The process manifests contain compact per-document provenance. The frozen
indexes are authoritative for the raw parent path, origin/source/artifact
SHA-256 values, byte counts, conversion method and disposition. The
artifact-only indexes contain public artifacts only and can be handed to fresh
source-only parsers independently.

## Exact scope and conversion dispositions

- CalGuns: `corpus/counties/raw/exhaustive_2026_09_17/calguns_324095_page6.html`.
  The structured renderer produced 14 post records from canonical logical page
  6, preserving ordinal, author, timestamp, node ID, five quote boundaries and
  six signature boundaries.
- N-400: 35 HTML captures with no same-stem frozen text, USCIS
  `uscis/n400_form.pdf`, and the Office of Immigration Statistics performance
  CSV. HTML is rendered in document order after non-content executable/style
  elements are removed. PDF text uses `pdftotext -layout` and retains page
  breaks. CSV values and quoting are retained with newline normalization.
- UI claims: `corpus/realworld/ui_claim/raw/edd_lmid_ui_claims.html`, rendered
  with the same public-HTML conversion.
- Solar permitting:
  `corpus/realworld/solar_permit/raw/solartrace_dataset_2025-09-09.xlsx`.
  All six worksheets and all 2,422,341 nonempty cells are rendered without
  analytical summarization. Explicit start/end markers retain worksheet
  boundaries; row numbers and JSON arrays retain cell positions; header rows,
  raw values and Excel column number formats retain labels and units. The
  workbook has 22,544 nonempty rendered rows and no formula cells.

Three alternate representations are explicitly excluded, not silently
dropped: `8cfr316_full.xml` and `8cfr335_full.xml` duplicate already-frozen
same-stem text sources, and the N-400 performance XLSX represents the same
table selected losslessly as CSV. These exclusions are listed in the set-level
manifest.

No source register fields, answer keys, gold files, derived analyses, or hidden
truth were read or copied. The build used no network access or external model
calls.

## Reproduction and verification

From the repository root, using the Conda Python environment that provides
Beautiful Soup and openpyxl:

```sh
python runs/rw_parse_20260919/supplemental_sources/build_supplemental_freeze.py
python runs/rw_parse_20260919/supplemental_sources/build_supplemental_freeze.py --check
```

The first command rebuilds only the supplemental run directory. The second is
read-only and refuses success if an origin, source, artifact, or artifact-index
hash differs.

## Parser judgment still required

The SolarTRACE artifact is a faithful 13,839,064-byte tabular rendering. It is
complete and indexed, but is too large for many single-prompt parsing contexts.
A downstream parser should stream it or deterministically divide it at the
recorded worksheet/row boundaries. Choosing analytical subsets or aggregations
would change the task and is intentionally not done by this source freeze.

## Later cached Reddit comment supplement

A separate, non-overwriting freeze at
`runs/rw_parse_20260919/reddit_comment_supplement_v1/` preserves four comment
caches omitted from the initial parse: three solar threads (32, 10 and 23
comments) and one UI-claims search response (60 comments). All **125 comment
records** are retained in their original order, including deleted bodies and
moderator posts. No semantic filtering was performed. Author, thread, parent,
timestamp and score metadata are retained; each literal body has a recorded
UTF-8 byte span and hash in the artifact. The three previously parsed solar root
posts are repeated as explicitly marked context, not three new independent
documents or cases. UI search results span multiple threads.

The build script is `runs/rw_parse_20260919/freeze_omitted_reddit_comments.py`;
`--check` verifies the existing freeze without overwriting it. The fresh build
and read-only verification each pass **24 hashes and 128 literal body checks**
(125 comments plus three root posts). Per-process artifact-only indexes are
ready for a source-only parser. No new network retrieval was performed, and this
cache-level completeness does not establish live-thread or corpus completeness.

## Primary CPRA replacements, not scrubbed AI summaries

Closer inspection showed that merely removing `headline_finding` from the two
CPRA JSON files would not produce source-only inputs. The request file explicitly
describes seven of eight timelines as AI paraphrases. Even its claimed verbatim
first timeline has no bound primary capture in that file. Neither JSON enters the
parser supplement; only their public URLs were used for fresh retrieval.

The existing frozen `S13_sf_sunshine_article3_summary` also explicitly identifies
itself as an AI-tool summary. The accepted CPRA ledger has ten measurements and
27 evidence references to that document. None of those complete reference strings
matches the separately captured primary text, even after presentation
normalization. This is a provenance failure, not a finding that every underlying
claim is false. A fresh parse and claim-by-claim reconciliation are required.

`runs/rw_parse_20260919/cpra_source_provenance_v1/` now contains **13 new primary
captures**: the archived official ordinance, four MuckRock agency dashboards and
eight MuckRock request timelines. Direct HTTP retrieval succeeded for all 13;
the browsing tool's attempted opens had failed. Raw bytes, capture times, URLs,
rendered text and hashes are retained. No summaries or prior claim labels are in
the artifact-only index. Live dashboard figures are a new observation date, not
proof of the older values. The subsequent source-only parse and preserved
`cpra_supplement_parse/reviewed_v1/` are complete; the latest receipt and
qualifications are in the [parse continuation](2026-09-19-codex-parse-continuation.md).
`reviewed_fit_holds_v2.json` adds the source-wide hold while preserving
the five earlier holds; it remains a required review work order, not an automatic
compiler filter.

## Legacy county Reddit search responses

All **1,072** files in `corpus/counties/reddit_raw/` are accounted for in the
separate `runs/rw_parse_20260919/legacy_reddit_posts_v1/` manifest:

- 692 empty search arrays;
- 25 retrieval-error/support files;
- 355 nonempty arrays containing 5,105 post occurrences, or **4,664 distinct
  post-content records** after exact ID/title/body deduplication.

All source occurrences and metadata variants remain linked to each retained
post. Fifty-nine records match indexed posts already present in the earlier
freeze. Repeated matches are not additional independent evidence. There are no
captured authors or comments in these legacy records; neither is invented.
Search filenames do not establish substantive program or county relevance.
The 110 bounded source-only batches still need full reading, relevance review
and extraction; their existence does not count as a completed parse.

Independent verification in
`runs/rw_parse_20260919/additional_source_freezes_independent_validation.json`
passes 7,116 Reddit input/output hashes, checks all 5,105 source rows exactly
once against literal title/body spans (10,210 checks), and checks every retained
post's batch assignment exactly once. The CPRA freeze passes 48 hashes and 13
page-class/body checks. No original freeze, source or ledger was rewritten.

## Legacy county web captures and scanned pages

The separate `runs/rw_parse_20260919/legacy_county_captures_v1/` accounts for
all **351** files in the older `raw/ga` and `raw/forums` collections (200 and
151 respectively). Its first source-only index queues 120 captures, preserving
raw-source hashes, conversion methods and known source URLs. Twenty captures
have no recoverable URL in the associated metadata; no URL is invented.
Failed responses, empty captures, search/navigation pages, alternate
representations and unresolved formats receive explicit dispositions.

A second, independent pass resolves the 15 initially unrecognized formats:
six are public Legistar XML responses, seven are site-search fragments, and
two are literal rate-limit errors. The six XML responses have their own
artifact-only index in `independent_review_v1/`, bringing the queued set to
**126 captures**. That pass verifies 639 input/output hashes, replays all 120
initial conversions exactly, checks 11 aliases against earlier frozen origins,
and confirms complete batch assignment. This is capture accounting, not a
completed semantic parse or proof that every source is substantively relevant.

Eight PDFs require additional page review: six have partly missing text and
two are image-only. `ocr_legacy_county_captures.py` processes their 191 sparse
pages, reusing earlier OCR only where the original PDF hash matches exactly.
New page images stream directly into OCR rather than accumulating on disk.
The page receipts and source-only supplements are stored separately under
`ocr_supplement_v1/`. Machine transcription is explicitly **unverified**:
quantitative claims require comparison with the bound original page image.
These supplements are alternate views of the same eight PDFs, not eight
independent new sources; an empty OCR result is not evidence of a blank page.

The OCR pass is complete: **35 existing page transcriptions reused and 156
new ones**, with 435 independent hash checks and eight exact artifact replays.
Three pages produced empty OCR; independently rendering and viewing all three
confirmed blank white pages (Butte 2019–2020 grand-jury report, PDF pages 2,
131 and 132). The other 188 transcriptions have not received that visual
verification. `ocr_supplement_v1/independent_validation.json` records the scope.

## Grand-jury reports omitted by the original slice selectors

`runs/rw_parse_20260919/grand_jury_reports_v1/` accounts for all 735 archived
`gj_*.pdf` files: **613 PDFs open successfully**, 121 are non-PDF responses,
and one fails conversion with a broken cross-reference table. None was an
origin in the original 23 freezes. Seven successful PDFs are exact source
aliases of reports in the newer legacy-capture freeze; they are dependent views.
The successful reports contain **21,380 pages**. Native text and 2,915 existing
hash-bound OCR page views are preserved separately inside their artifacts;
the 2,753 nonempty OCR views remain unverified machine transcriptions.

An independent pass verifies 2,523 hashes, replays native text on every page,
confirms every PDF page count with a second reader, checks all 2,915 OCR-page
receipt links and confirms exactly-once batch assignment. It does not read the
reports semantically. Five-report batches retain whole documents.

The 1,597 sparse native-text pages without nonempty prior OCR have now been
processed into the separate, resume-safe `missing_page_ocr_v1/` supplement,
covering 278 PDFs. Independent verification passes 3,754 hashes, checks all
1,597 page receipts and reconstructs all 278 supplemental artifacts exactly.
There are 174 empty OCR results, still requiring image review; emptiness does
not establish blank source pages. Two inspected examples are clearly legible
scanned agency letters despite empty native text, so sparse text cannot be
treated as a blank document. Quantitative claims still require visual checks.
No original file or earlier freeze was changed.

`source_identity_supplement_v1.json` adds whitelisted retrieval identity
fields for 228 reports, recovering missing URL/title/county context for 141 of
183 previously unidentified captures. All receipt byte counts match the bound
archived files, but the old retrieval receipts lack capture-time content
digests; filename/size agreement is not cryptographic proof of remote origin.
The supplement contains no burden findings or relevance labels and does not
rewrite the original freeze. Report identity still requires its own text/image.

## Exhaustive-sweep Reddit comment captures

`runs/rw_parse_20260919/exhaustive_reddit_comments_v1/` freezes all **1,956**
archived `reddit_*_comments.json` responses. Of these, 1,799 contain source
nodes and 157 are empty/error responses. The 1,799 whole threads contain
**32,669 distinct captured comments**, preserving authors, timestamps, parents,
literal bodies, source JSON pointers and hashes. The 1,774 available root
posts are reused from the legacy post freeze as context only. Twenty-five
threads lack a captured root and three comment-parent links are unresolved.
No `more` nodes were present; that does not establish live-thread completeness.

An independently implemented all-field tree traversal accounts for all 32,669
source nodes exactly once, verifies 36,217 literal comment/title/root spans
and 5,617 hashes, and confirms exactly-once whole-thread assignment across 88
bounded batches. No jurisdiction, relevance, case identity or burden claim is
inferred by this freeze. At freeze time these comments were **queued, not parsed**. The existing
4,664-post legacy queue overlaps through reused roots and must not be added as
though the two queues represented independent observations.

Later local-cache recovery found **all 25 missing roots** without a network
request. Their source-only context artifacts live in
`exhaustive_reddit_comments_v1/root_context_v1/`, with supplemental indexes
for the 21 affected batch numbers. Parsers must bind both original and matching
context indexes; batch 001 is unchanged and needs no supplement. Independent
checks pass 49 hashes and 52 literal title/body comparisons, including the
duplicate prior ADU-root representation. The three missing comment-parent
links remain unresolved; the earlier cached lookup returned no matching nodes.
The v1 freeze remains unchanged as an auditable snapshot of the original join.

The first batch has subsequently been parsed: 32 whole threads, 271 comment
nodes and 32 reused roots, producing 39 measurement rows and five count claims.
Parent checks pass 83 hashes and 198 literal evidence/count references. Eighteen
measurements derive from reused roots and must not be double-counted. The
parent semantic review records scope, censoring and item-count holds, so this
completed extraction is not yet a fit-ready packet. Batch 002 subsequently adds
two threads and 397 comments; parent checks pass 23 hashes and 39 literal
evidence/count references on its six measurements and four count claims. The
other 86 batches remain outside these completion declarations.

## Archived well-program responses

`well_response_captures_v1/` now accounts for all 94 `.response` files in the
exhaustive capture directory. Sixty-six readable, raw-distinct documents are
queued: 33 HTML pages, 32 PDFs containing 254 pages, and one Word document.
Twenty-four captures have unsuccessful HTTP status, three are unavailable/empty
HTML and one is an exact raw duplicate. Every queued document has whitelisted
retrieval identity metadata; filenames/titles do not establish actual program,
jurisdiction, relevance or currentness.

Independent verification passes 277 input/output hashes, replays all 66
conversions exactly, independently confirms PDF page counts, and checks
exactly-once batch assignment. Seventeen sparse PDF pages in four sources need
image/OCR review, and Word embedded objects have not been visually reviewed.
The 66 documents are **queued, not parsed**, and this is not a claim of complete
58-county well coverage. Failed responses remain retrieval gaps. Cross-collection
source dependence still needs reconciliation.

## Empty grand-jury OCR results: image-level triage

The 174 empty OCR results now have a separate source-bound render audit at
`grand_jury_reports_v1/missing_page_ocr_v1/empty_page_render_audit_v1.json`.
At the checked 75-dpi grayscale resolution, 102 render entirely white and 72
contain non-white pixels. The latter still need visual reading; the former are
not a resolution-independent proof of blank originals. Nothing was deleted or
excluded from the source queue, and OCR emptiness was not used as a semantic
coverage decision.

## Public program workbooks omitted by index-page parses

`program_workbooks_v1/` accounts for 29 downloaded CalFresh, CalWORKs, general
assistance and IHSS workbooks/forms. Its 25 XLSX transcriptions preserve 93
worksheets and 1,587,354 stored cells, with formulas, cached values, coordinates,
number formats, workbook date system, worksheet visibility and notes kept
distinct. Independent validation passes 81 hashes, compares all stored cells
against a separate spreadsheet reader and all 16,533 formula expressions
against source XML, and checks exactly-once whole-workbook batch membership.
No formula, macro or external link was executed. These are **source-preserving
queues, not completed semantic parses or 1.6 million independent observations**.
Charts and other non-cell objects still need review.

Four older XLS forms initially raised an encrypted-workbook error. All four
open with Excel's documented standard key for read-only protected workbooks;
no password search was performed. A separate
`program_workbooks_legacy_readonly_v1/` supplement preserves 24 worksheets and
9,488 cached cells without changing the originals or earlier manifest. These
are reporting templates, not measured case datasets: their blank/zero cells
must not become observations. Formula expressions and embedded objects remain
in the original binary. Its independent verifier now passes 15 hashes and
replays all 9,488 cached cells and four default-key opens; it uses independently
written checking code but the same XLS decoding libraries. Semantic reading
and visual/embedded-object checks remain. The default read-only behavior is documented in
[Oracle's technical note, page 5](https://docs.oracle.com/en/middleware/standalone/outsidein/8.5/oiccd/technotes/Encryption_Support_Tech_Note.pdf).
