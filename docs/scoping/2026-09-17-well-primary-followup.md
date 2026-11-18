# Well-permit retrieval: primary sources and statement scope

2026-09-17. Part of the open N12 exhaustive retrieval, not a closure claim.
The P5 environmental inventory had instructions for 16 counties and gaps for
42. LA's follow-up was already retained; searches now cover the other 41 gap
counties. Search coverage is not document coverage. Wrong-state, oil/gas-well
and similarly named county results remain discovery records, not accepted
program evidence.

## Retained requests and access gaps

The first two download selections contain 87 references: 78 requests were made,
50 returned HTTP 200, 28 failed, and nine were skipped after an earlier access
block on that host. Byte validation found **17 PDFs totaling 126 pages**.
Successful HTML includes an OpenGov shell containing only the product name;
HTTP 200 does not establish readable instructions. These references, the four
extra primary/related sources below and five geographically qualified discussion
leads were mapped in the first import: 96 additions brought the ledger to 766 reference
IDs, with no channel closed. Four reuse prior URLs; related versions and
adjacent program scopes are explicit. The Santa Cruz Mountains discussion
remains retained but unmapped rather than forced into one county.
[Import and qualifications](../../corpus/counties/raw/exhaustive_2026_09_17/well_followup_matrix_leads.json).

The first selection's 23 references meant **19 requests plus four skips**, not
23 attempted downloads. The shared log contains a correction to earlier prose.

- [First selection and request records](../../corpus/counties/raw/exhaustive_2026_09_17/well_gap_download_summary_01.json)
- [First byte/PDF inspection](../../corpus/counties/raw/exhaustive_2026_09_17/well_gap_inventory_01.json)
- [Second selection, transport and PDF inspection](../../corpus/counties/raw/exhaustive_2026_09_17/well_gap_inventory_02_summary.json)
- [Additional discovery queue](../../corpus/counties/raw/exhaustive_2026_09_17/well_gap_extra_discovery.json)

The four additional URLs were subsequently fetched: all returned HTTP 200.
They add one readable Alameda FAQ and three PDF files totaling 72 pages.
The two four-page San Francisco PDFs have different byte hashes but identical
`pdftotext -layout` output, so they are related versions, not independent
instructional evidence. The Del Norte/Crescent City proposal has 64 pages,
11 without useful embedded text. Initial shell-quoting failures made no network
requests; those records were preserved separately from successful retries.
[Requests](../../corpus/counties/raw/exhaustive_2026_09_17/well_extra_retry_summary.json);
[byte/PDF checks](../../corpus/counties/raw/exhaustive_2026_09_17/well_extra_pdf_inventory.json);
[text comparison and discovery contexts](../../corpus/counties/raw/exhaustive_2026_09_17/well_extra_text_discovery.json).

Access problems remain explicit: government sites returned 403; Alameda's
legacy host had a certificate hostname mismatch; old application links returned
404; an Imperial hearing PDF exceeded the initial size cap. No access control
or TLS verification was bypassed. Some official search text is available where
local bytes are not, including Valley Water's robots-blocked pages; these are
not described as locally retrieved documents.

## What has been read and what it means

These are bounded source checks. Unread PDFs and HTML are not semantic evidence
merely because they downloaded successfully.

| Source / review extent | Supported interpretation | Do not infer |
|---|---|---|
| Alameda indexed primary instructions/FAQ | Advance notice and application-channel instructions; sources conflict on online-only versus mail/fax submission | Ten working days is not observed mean processing time; a stale channel instruction is not resolved by a footer date |
| Butte application packet, first two of 16 pages; ordinance, first two of 12 pages | Packet is dated June 6, 2022 and describes emergency-order/GSA conditions; ordinance has 2021 adoption/effective dates | That every historical emergency condition remains operative in September 2026 |
| El Dorado application, both pages | Inspector options, advance notification, completion reporting, and conditional city/building/Tahoe/CEQA dependencies | A listed actor or conditional step occurs in every case; notice or reporting deadlines equal staff hours |
| El Dorado fee-page headings | Existing schedule runs through September 18, 2026; new schedule starts September 19 | The future schedule is current on the September 17 retrieval date; a listed fee was actually paid |
| Inyo historical 2020 form and current program hub | Historical form plus announced October 2025 portal change; downloaded portal itself has no usable application text | Old form is current, or a successful portal response means the application was retrieved |
| Valley Water indexed primary pages | Announced February 2026 paperless transition and current-year fee information; older payment instructions conflict | Footer year reconciles versions; Valley Water and county Environmental Health are the same actor |
| Santa Barbara small-private-water-system material | Water-system oversight material | A well-drilling instruction packet; search hits for San Bernardino are Santa Barbara sources |

Subsequent reading of the full retained Alameda FAQ confirms the online
application instruction and separates card payment after approval, pre-issue
cancellation, issued-permit refund and expiration. Its service-area panel
assigns different locations to county Public Works, Berkeley, Alameda County
Water District and Zone 7. Neither county population nor an incorporated/
unincorporated flag alone identifies the permit authority. The notice period
is a requested lead time, not a measured processing mean.

All four SF pages were read. The application is marked revised December 2020
and concerns monitoring wells/soil borings, not a generic residential drinking-
water well. It distinguishes construction/destruction approval, inspection
notices, post-completion reporting, and an annual operating permit with Tax
Collector billing. These are multiple clocks and conditional interactions,
not one elapsed duration or a fixed count of independent agencies. Current
operative status and the separately linked current fee schedule remain open.

For the Crescent City proposal, PDF pp.11–12 and 44 were read in full;
keyword contexts elsewhere were only discovery. Dates describe a projected
project, costs are estimates, and the attached feasibility study includes a
draft warning. Its table lists county, city and state permitting roles, with
both health/human-services and environmental-health names: rows are not
automatically distinct independent actors. A planned municipal supply project
is not a realized domestic-well permit case. Numeric table values were not
promoted to calibration data; the sparse pages remain unreviewed.

Current legal status of emergency-order conditions still needs the complete
amendment/supersession chain. The later Governor order discovered in search was
not fully reviewed here. Do not turn these historical forms into legal advice
or silently update the active synthetic world.

Sixteen linked follow-ups from Butte, Colusa and El Dorado have also returned
HTTP 200: quarterly summary, manual, fee/VOC forms, portal pages, reporting
forms and dated resolutions. Literal links and parent hashes were checked
before requesting them. File-type, version and semantic inspection is separate;
this child increment is now mapped, bringing the ledger to 782 references. The four
extra URLs are retained as qualified above; currentness and full semantic
review remain open.
[Child requests](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_download_summary.json).
[Qualified import](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_matrix_leads.json)
and [integrity check](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_ledger_integrity_audit.json)
retain the byte aliases, portal-only responses and version uncertainty. All
16 hashes remain unchanged and no coverage channel is closed.

Child byte inspection validates 13 PDFs / 58 pages and a legacy Word document;
both Colusa portal responses contain only the same OpenGov shell. Two differently
labeled Butte document links yield identical PDF bytes. The Word instructions
are visibly revised in June 2014, not certified current.
[File inspection](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_inventory_summary.json).

The two El Dorado application versions disagree materially: one requires the
completion report within 60 days, the other within 30. Conditions and department
headings also differ. Both remain linked and both URL paths use `v/2`; neither
file size nor a URL counter establishes precedence. Keep this as unresolved
source-version uncertainty, not an averaged processing duration.

Butte's 13-page quarterly report provides actual administrative counts, but
they are not a linked applicant cohort. It distinguishes new permits issued
from finaled wells and explicitly discusses backlog status updates. All embedded
text was read; pages4–5 were additionally inspected visually. Those pages give
conflicting WY2016 small-diameter issuance counts: 69 in the cumulative table
versus 113 in the monthly table, whose cells sum to 113. Current-year rows are
partial, some cells are blank, and GSA/subbasin totals are not per-case actor
counts. No silently harmonized series or timing calibration was produced.
[Scope, version conflict and visual check](../../corpus/counties/raw/exhaustive_2026_09_17/well_children_statement_scope_review.json).

Further Santa Barbara searches locate GSA and water-district board packets,
a historical fee resolution and water plan, a form mirror and a tentative
court ruling with attributed permit chronology. The county-domain queries
returned no indexed results, not proof that instructions do not exist. These
eight follow-ups are retained as **not downloaded**, with role/date/scope
qualifications. New bulk downloads are on hold while shared-disk pressure is
checked; the relevant retrieval directory occupies3.1GiB and the system reports
about41GiB of swap in use. No source or run was deleted.
[Pending sources](../../corpus/counties/raw/exhaustive_2026_09_17/santa_barbara_well_pending_sources.json).

A bounded browser follow-up read the 2023 EMA meeting notice and the four-page
May 23 consultant proposal linked there, without retaining original PDF bytes.
They distinguish county EHS, the GSA and its external technical reviewer. The
proposal's budget and hourly rate are planned consultant work, not observed
processing time or automatically agency-staff hours. The approved-minutes link
returned a browser cache miss, so adoption was not established. The court page
returned 403; that host was not retried. These browser records do not turn the
eight original pending downloads into completed local retrievals or close a
county coverage channel.
[Browser reads and failures](../../corpus/counties/raw/exhaustive_2026_09_17/santa_ynez_2023_child_browser_attempts.json).

## Additional public discussions

Six newly retained Reddit OPs/comment trees contain 71 unique comment IDs,
two removed bodies, no returned `more` placeholders and no missing parents.
All six OPs and all available retained comment bodies were read. All 71 IDs
are new to the frozen 1,286-file / 22,408-comment-ID comparison set, whose
hashes remain unchanged. This does not prove live-site completeness.
Three pairs repeat identical bodies, so unique IDs do not imply independent
claims. One of the six discussions concerns a minisplit permit, not a well.

The [statement-scope review](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_well_statement_scope_review.json)
records prospective questions, jurisdiction uncertainty, cross-case replies,
historical costs, duplicated stories and a correction that an apparent new
permit was actually an existing-house purchase. It also separates physical
drilling hours and well-test duration from permitting time, and contractor
quotes from government fees. No numeric processing-time observation or
calibration parameter was added from this pass.

[Retrieval/duplicate inspection](../../corpus/counties/raw/exhaustive_2026_09_17/reddit_well_followup_inventory.json).
