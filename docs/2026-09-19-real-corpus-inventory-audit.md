# Real-corpus inventory and parse-queue audit

Snapshot: 2026-09-19. This report reconciles the physical `corpus/` tree, the
23 source-only freezes under `runs/rw_parse_20260918/`, their rendered
artifacts, the old CalGuns partitions, and the current forum work plan. The
machine-readable result is
`runs/rw_parse_20260919/real_corpus_inventory_audit.json`.

**Later continuation:** the original snapshot and arithmetic below are
preserved, not silently updated. The 577 known missing forum pages have since
been retrieved and validated; the joined plan contains 4,548 pages across
19 megathreads. Independent inspection of all 4,548 pages found no remaining
gaps within their observed page ranges, no later navigation page, and no
duplicate post IDs (68,090 post occurrences; 9,136 hash checks). This does not
establish attachment or live-web exhaustiveness. Supplemental N-400, Reddit,
CPRA and legacy county capture work is documented in
[the supplemental freeze report](2026-09-19-supplemental-source-freeze.md),
with current accepted parsing totals in
[the continuation log](2026-09-19-codex-parse-continuation.md).
The initial suggestion below to scrub the two CPRA JSON summaries was
superseded: their prose was AI-derived, so fresh primary captures were made
instead. None of those summaries is a source-only parser input.

**Important coverage correction (14:18 Pacific):** the 4,258 files labeled
“explicitly withheld” below are not all excluded analyses or duplicate formats.
Some were merely outside one CalGuns slice, with no other freeze selecting them.
Every one of 735 `gj_*.pdf` paths was in that category. The 109-document
grand-jury freeze selected index/archive pages, not those report PDFs. Of the
735 files, 613 open as PDFs (21,380 pages), 121 are non-PDF responses despite
their suffix, and one has a broken PDF cross-reference table. The 613 reports
now have a separate source-only freeze, with native-page and bound-OCR checks;
they are **queued, not parsed**. Scanned portions still require OCR/image review.

The same correction applies to 1,956 archived Reddit comment responses:
1,799 contain 32,669 comments and 157 are empty/error responses. All 1,799
whole-thread views are now frozen and independently checked. Their 1,774
cached root-post views are reused context, not independent new evidence;
25 roots and three comment-parent links remain absent. This adds a reading
queue, not completed extraction. Thus the original inventory arithmetic was
correct, but its “withheld” category was **not** a defensible full-corpus scope
exclusion. Other withheld-file groups still need the same source-level review.
The 25 missing roots were subsequently recovered from additional existing
caches in a separate `root_context_v1/` supplement; only the three comment
parents remain absent. The original 1,799-thread freeze was not overwritten.

Receipts: `runs/rw_parse_20260919/grand_jury_reports_v1/independent_validation.json`
and `runs/rw_parse_20260919/exhaustive_reddit_comments_v1/independent_validation.json`.

Reproduce it with:

```sh
python runs/rw_parse_20260919/audit_real_corpus_inventory.py
```

The audit does not open synthetic truth/spec files, hidden files, or the
contents of `corpus/realworld/_gold`. It does not modify freezes, ledgers, or
queues.

## Result

The apparent `14k on disk` versus `6,783 frozen` discrepancy is primarily a
units problem, not 8,000 silently dropped parse documents. There are, however,
specific silent source-selection omissions described below.

| inventory layer | files / documents |
|---|---:|
| every physical file below `corpus/` | 14,915 |
| unique physical origins supplied by the 23 freezes | 6,783 |
| existing files explicitly withheld and not supplied by any freeze | 4,258 |
| files outside every current freeze | 3,874 |

These rows are disjoint and sum to 14,915. “Every physical file” includes
retrieval JSON, scripts, HTTP headers, paired PDF/text copies, spreadsheets,
images, analysis, cache/repository files, and gold material, so it is not a
document denominator. A further 3,310 supplied origins appear in a sibling
freeze's withheld list (mostly one CalGuns slice withholding another); the
table gives supplied status precedence and therefore does not double-count
them.

The largest collections outside every freeze are 1,288 files in the exhaustive
capture directory, 1,072 legacy `counties/reddit_raw` captures, 476 files under
`corpus/tax` (including repository support files), 345 county support files,
200 legacy `raw/ga` files, and 151 legacy `raw/forums` files. These are a
selection-scope backlog, not evidence that the current 23 freezes are missing
their own inputs. They need their own source-selection decision before they can
be called parse work.

The generic `freeze_real_sources.py` also silently ignores formats other than
`raw/**/*.txt` and `reddit/posts/*.json`; it records HTML/PDF as withheld only
when a same-stem TXT exists. That leaves 46 `raw/` files inside already-frozen
realworld processes outside both `documents` and `withheld`: 40 for
naturalization, one UI HTML page, one SolarTRACE workbook, two CPRA JSON files,
and two SF.gov 404 captures. This is a real freeze-coverage gap.

Naturalization is the material case. Its neutral source register names the
omitted statutes, USCIS pages, N-400 form, and performance data. After treating
two XML files as alternate representations of already-frozen same-stem TXT and
preferring the CSV over its same-stem XLSX, there are **37 supplemental source
candidates**: 35 HTML documents, the N-400 form PDF, and the performance CSV.
They should receive a supplemental source-only freeze and parse; the accepted
125-document ledger is not the full on-disk N-400 corpus.

The UI claims HTML and SolarTRACE workbook are also named in neutral source
registers. Three expanded solar Reddit captures contain comment material beyond
their smaller frozen post records, and one UI comment-search capture contains
60 rows; review these as supplemental/replacement inputs. The CPRA JSON files
contain derived fields such as a headline finding, so they require a
source-only scrub before use. The two food-facility HTML files are 404 pages,
and six other UI comment-search arrays are empty; those are not recommended
parse additions. Exact paths appear in the audit JSON.

All 6,783 frozen origins exist. All 6,783 frozen source copies and all 6,783
rendered artifacts exist, and every rendered artifact matches the SHA-256 in
its artifact index. There are 40 exact rendered-content duplicate groups (44
excess document rows): 36 are within one process and four cross process. The
four cross-process groups are enumerated in the JSON; they agree with the prior
cross-ledger duplicate audit. No frozen or queued document is missing from
disk.

## Why 6,783 frozen becomes 3,971 remaining

The complete arithmetic is:

```text
6,783 frozen documents
  = 1,983 documents in 20 non-forum processes marked parsed
  +   829 ordinary CalGuns documents in 8 batches
  + 3,971 CalGuns megathread documents
```

Seven old ordinary batches account for 828 trusted documents. The one-page
eighth batch now has an output under
`runs/rw_parse_20260919/calguns_a_batch5/`. Source review has completed with
declared provenance limitations; its on-disk manifest still says
`independent_reviewer_pending: true` at this snapshot. Thus the strict
manifest-derived remainder is 3,972, while the operational remainder after
accepting that source review is 3,971. The three old partial/empty megathread
attempts remain untrusted and do not reduce either number.

The old partitions assign every one of the 4,800 frozen CalGuns artifacts
exactly once: no missing assignment, extra assignment, or duplicate document
assignment. `runs/rw_parse_20260919/FORUM_WORK_PLAN.json` independently matches
the audited 829 ordinary and 3,971 megathread counts.

## There are 19 megathreads, not 20

The old slice partitions contain 20 **rows**, but only 19 unique thread IDs.
Thread 324077 appears once in `calguns_a` (32 artifacts) and once in
`calguns_g` (677 artifacts). The two sets are document-disjoint and combine to
one 709-page work unit. Therefore:

- 20 partition rows minus the second 324077 row = 19 parse units.
- The 3,971-page total is still correct; it never double-counted a document.
- Thread 324077 must retain one case-ID namespace across both slices.

For thread 324077, the frozen/raw pages on disk are exactly page 1 and pages
445–1152. Pages 2–444 (443 pages) are absent from disk. The combined work unit
has no overlap, but it is not a complete page-1-through-1152 archive.

Thread 324096 initially appeared to lack page 2 and pages 11–144. The page-2
claim was a filename error: `calguns_324096_page1.html` has canonical and Open
Graph URLs ending in `/page2` and begins at post #16, while
`calguns_324096_page1_canonical.html` is true page 1. Across all 4,800 frozen
origin HTML files this is the only filename-to-canonical-page mismatch. With
that correction, thread 324096 has logical pages 1–10 and 145–621; only pages
11–144 (134 pages) are absent. The work plan should retain both artifacts and
order them as logical pages 1 and 2.

## Raw CalGuns omissions

There are 4,804 `calguns_*.html` captures on disk and 4,800 frozen artifacts.
The four omitted raw files are:

| raw path | disposition |
|---|---|
| `corpus/counties/raw/exhaustive_2026_09_17/calguns_1302365_page108.html` | 173-byte 502 capture; successful `_transport_retry` alternate is frozen |
| `corpus/counties/raw/exhaustive_2026_09_17/calguns_324060_page140.html` | 173-byte 502 capture; successful `_history_resume` alternate is frozen |
| `corpus/counties/raw/exhaustive_2026_09_17/calguns_324095_page6.html` | readable 247,997-byte forum page omitted at a slice boundary; no frozen alternate |
| `corpus/counties/raw/exhaustive_2026_09_17/calguns_324096_page621.html` | invalid-page response with no posts; successful `_canonical` alternate is frozen |

Only `calguns_324095_page6.html` is a real raw-to-freeze loss. Freeze it as
`calguns_324095_page6`, add it to the ordinary `calguns_g` batch-1 thread
324095, and re-review that thread. This would make the selected frozen corpus
6,784 documents and the forum selection 4,801.

The archive gaps are not queueable yet because no raw files exist. If retrieval
is resumed, target these exact logical ranges and only add successful captures:

- `corpus/counties/raw/exhaustive_2026_09_17/calguns_324077_page{2..444}*.html`
- `corpus/counties/raw/exhaustive_2026_09_17/calguns_324096_page{11..144}*.html`

Do not add the three bad captures that already have successful alternates, and
do not discard the misleading `calguns_324096_page1` artifact: it is page 2.

## Renderer and deduplication cautions

The CalGuns slices do not have a uniform text representation:

- `calguns_a` and `calguns_g` are flat tag-stripped text. They preserve text in
  document order but have no explicit post, author, quote-boundary, or
  signature-boundary markers.
- `calguns_q` segments posts with author/date/node metadata, marks quote blocks
  as `[[QUOTE from X]]...[[/QUOTE]]`, and drops signatures.
- The origin hash field is `origin_sha256` in `a` and `q`, but `raw_sha256` in
  `g`. Consumers need that fallback.

The audit verified all 23,482 declared `q` posts against rendered `[POST ...]`
headers with zero document-level count mismatches. Its 12,421 opening quote
markers equal its 12,421 closing markers. Raw `q` HTML contains 14,277
`bbcode_quote` blocks when signature content is included, so marker balance is
not proof of lossless raw-quote preservation; the signature-dropping renderer
is intentionally lossy. The flat `a` and `g` inputs contain 11,808 and 13,637
raw quote blocks respectively but expose no quote markers. These formats must
not be treated as interchangeable for quote propagation or author/case linkage.

Finally, document hashing answers only whether bytes repeat. It does **not**
prove claim or case disjointness: quoted posts and signatures can repeat across
different HTML pages, and the same applicant episode can be assigned different
computed quantities in different ledgers. The companion
`runs/rw_parse_20260919/cross_ledger_case_candidates.json` contains 10
exact-quote candidate groups. Each needs semantic review; none should be
automatically merged or excluded from a byte-hash result alone.

## Interpretation

The defensible current **selected-input** denominator is 6,783 frozen documents,
not 14,915 filesystem entries. Within that denominator the freeze and partition
chain is complete. It is not a claim that every relevant on-disk source was
selected: the audit finds the 37-document N-400 supplement and smaller
registered-source gaps above. The forum remainder is 3,971 megathread pages
after the one-page ordinary review. Separately, one readable CalGuns page
should be frozen, and 577 known logical pages were never captured (443 in
thread 324077 and 134 in thread 324096).
