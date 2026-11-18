# Wide-net retrieval continuation

2026-09-16, Codex, packet N10-WIDE-NET. Alex requested continued broad source
collection after clarifying that previous bounded passes were not exhaustive.
This pass may use up to 20 search queries and 45 distinct source fetches.
No model code, unit tests, authenticated systems or outreach are in scope.

## Live scope and stopping rule

Prioritize actual timing, employee effort/capacity, case-event records, and
missing local process documents. Search across benefits administration,
permitting/environmental health and government workforce sources. Preserve
which sources were merely located, downloaded, read, or numerically checked.
Completion of this pass will **not** mean every public source has been obtained.

Raw originals, browser evidence and a hashed manifest will be saved under
`corpus/counties/raw/wide_net_target/`. Existing cached sources are reused rather
than fetched again. Any unresolved access failure or missing measurement stays
explicit. Detailed findings are added below as they are verified.

## Findings

Twelve public originals/API responses were retained in this bounded pass,
including two county permit-event exports, three Census government-unit
employment archives, two Alameda documents, definitions, metadata and source
counts. No model/generator edits or unit tests were made. The user also requested
a [synthetic corpus generation handoff](../2026-09-16-synthetic-corpus-generation-plan.md),
which now incorporates these sources and the earlier P/N/Q findings.

### 1. County-government headcounts: a substantially better unit than QCEW

Retrieved the Census employment **individual government unit** archives for
[2022](https://www.census.gov/data/datasets/2022/econ/apes/2022.html),
[2024](https://www.census.gov/data/datasets/2024/econ/apes/annual-apes.html), and
[2025](https://www.census.gov/data/datasets/2025/econ/apes/annual-apes.html), plus
the [data guide](https://www2.census.gov/programs-surveys/apes/resources/ASPEP%20Data%20Guide%202024.pdf).
Each ZIP includes fixed-width values, government identifiers, an Excel copy,
technical documentation and a reliability disclaimer.

| Reference year | California county-type governments | Separately classified San Francisco | Selected function rows | All-functions total rows |
|---|---:|---:|---:|---:|
| 2022 census | 57 | 1 municipality | 1,113 | 58 |
| 2024 sample | 41 | 1 municipality | 825 | 42 |
| 2025 sample | 41 | 1 municipality | 825 | 42 |

The extracted [142-row headcount table](../../corpus/counties/raw/wide_net_target/census_ca_government_headcounts.csv)
keeps year, March reference period, unit identifiers/type, FIPS, full-time and
part-time counts, monthly payroll and each original data flag. The source's
internal state code is 05 for California; its FIPS state is 06. Selection uses
government type, not all entities geographically located in the county. SF is
included by its exact municipal identity, not by a substring that would also
include South San Francisco, a school district or BART.

Important limits:

- These unit files contain **headcounts, not FTE**; they do not contain the
  part-time hours needed to derive a unit-level FTE. Full-time plus part-time
  counts must not populate `county_employees_fte`.
- Counts and payroll concern March, not annual work hours. Function categories
  include public welfare, health, financial administration and other broad
  functions; they do not isolate a permit technician or eligibility task.
- 2024/2025 are samples. Their omitted counties are not zero employees.
- The 2022 count covers all 58 geographic county areas only with the explicit
  SF classification exception. It is not 58 county-type government records.
- Edited, prorated and imputed values are present. Retain flags rather than
  calling every total a directly reported measurement. The check file records
  flag distributions; a blank flag is retained, not reclassified as reported.
- Census cautions that unit records were edited for aggregate estimation, not
  validated as individual-unit longitudinal series; nonsampling error remains
  even in census years. Any derived analysis is ours, not Census-endorsed.

The shared county covariate table was **not** overwritten. This is a separately
documented replacement candidate for the broader QCEW staffing proxy, not an
automatic resolution of the FTE or agency-specific capacity gap.

### 2. Sonoma County: actual permit dates, with duplicates and a freshness gap

Downloaded the official [construction-permit view](https://data.sonomacounty.ca.gov/resource/88ms-k5e7.csv),
its [metadata](https://data.sonomacounty.ca.gov/api/views/88ms-k5e7.json), and a
separate count response. The cached CSV selects permit identifier, status,
record type, start/issue dates, fees and valuation; names, addresses and parcel
identifiers were not needed and were not collected in this export.

- **25,448 rows**, matching the independent API count.
- **24,946 distinct permit identifiers**. There are 227 repeated identifiers
  and 502 rows beyond one per identifier; those 502 are exact duplicates on
  the selected columns. This does not establish equality on uncollected fields.
- **21,359 rows with both dates**, no negative differences; 4,089 lack issuance.
- Start dates span **2022-09-16 to 2025-05-30**; the latest issuance is also
  2025-05-30. Metadata advertises the past 48 months and was refreshed on
  2026-09-16, so refresh time does not establish current case coverage.

The metadata describes `started` as application acceptance; its separate status
definitions distinguish entered applications, completeness/ready-for-plan-check,
plan-check approval, payment and issuance. Do not equate acceptance with HCD's
complete-application boundary without a crosswalk. Missing issuance includes
different statuses, not a uniformly active right-censored cohort. Do not average
dates over duplicate rows, mix wells/septic/building types without filtering, or
call the result active staff time. No population timing estimate is claimed here.

### 3. San Diego County: a large historical permit export, not a current feed

Downloaded the county's [building-permit view](https://data.sandiegocounty.gov/resource/dyzh-7eat.csv),
[metadata](https://data.sandiegocounty.gov/api/views/dyzh-7eat.json), and count.
This is **San Diego County Planning and Development Services**, not the City
of San Diego dataset that also appeared in search. Retained only identifiers,
dates, status and record classification, excluding contractor/contact fields.

- **236,722 rows and distinct record IDs**, matching the source count.
- **183,347 paired opening/issuance dates**, of which **164 run backwards**.
  Examples are preserved in the check file; no swapping or zero-clamping.
- **53,375 rows lack issuance**. Status and original cohort selection need
  review before treating these as pending applications.
- Opening dates span **2005-01-03 to 2023-12-05**; latest issuance is also
  2023-12-05. `rowsUpdatedAt` is 2024-08-28, notwithstanding the description's
  daily-update wording and a separate weekly metadata field.

The date-column descriptions are blank; `open_date` is not yet verified as
initial submission, accepted filing or completeness. Treat this as a historical
administrative snapshot. The current county services page points to other open
data/reporting routes, which remain leads rather than retrieved replacements.

For both counties, the selected-column query URLs and original source counts
are retained in the manifest. Fetch limits were set above the verified totals.
These checks establish response completeness for those views at retrieval, not
completeness of either county's administrative record universe.

### 4. Alameda: agency-stage timing and cross-agency process descriptions

The [May 6, 2024 Planning Commission draft minutes](https://www.acgov.org/board/bos_calendar/documents/CDAMeetings_05_20_24/MIN.pdf)
report Fire Department reviews from January 1 through the end of April. The
hosting path says May 20; the document's meeting date is May 6. PDF page 4 gives:

| Staff-reported review cohort | Reviews | Mean days | Maximum days | Late share |
|---|---:|---:|---:|---:|
| Building plans routed to Fire | 246 | 2.93 | 17 | 1% |
| Planning reviews routed to Fire | 59 | 2.25 | 11 | 0% |
| All Fire reviews, including sprinkler/alarm | 399 | 3 | not stated | not stated |

The last group reports 58% approvals. The first groups overlap the total:
**not three independent samples**. Exact start/end and business/calendar-day
definitions are not established. The reported maximum of 11 and 0% late for
planning reviews should not be silently reconciled against the mentioned
10-day goal; clock conventions may differ. These are staff-reported aggregates
in draft minutes, not downloaded raw review histories or payer labor.

Also retained the **121-page July 2023**
[Baker Tilly development-services review](https://www.acgov.org/board/bos_calendar/documents/DocsAgendaReg_8_10_23/GENERAL%20ADMINISTRATION/Regular%20Calendar/Item_2_Baker_Tilly_Permit_Process_rpt.pdf).
Inspected its methods, timing discussion, workflow sections and timeline tables;
not every page was substantively audited. It includes cross-department workflow,
11 applicant interviews, four Planning-selected case studies and explicit data
limitations. Printed pages 33–34 say Planning turnaround data were unavailable,
and EH turnaround data were not supplied. Complex-project delay discussion is
case-study/anecdotal, not a representative mean. Table 9 contains departmental
typical timelines and issued-permit mix; Tables 10–11 concern comparison-agency
goals/published targets, not observed Alameda review durations.

This pairing is valuable for the synthetic corpus: a process-review narrative,
selected case histories, published targets and later measured department-stage
aggregates about related work, each with different authority and scope.

## Remaining leads and boundaries

- **Medi-Cal CY2025 performance workbook remains unretrieved.** The known DHCS
  index failed again in the browser. No workbook timing cells were fabricated;
  official static-file/mirror discovery remains a target.
- Current replacements for the old San Diego County export; explanation of
  Sonoma's 2025 case cutoff and duplicates; explicit clock dictionaries.
- County-specific FTE or labor-hour data, and calibrated mapping from broad
  Census functions to actual agencies/programs. Headcounts are progress, not
  task-level labor observations.
- P5's remaining well, food and operative-LAMP coverage, and unread ADU source
  leads, remain open. This pass did not finish those statewide inventories.
- Located but not downloaded: state DPR review-time tables, HCAI review reports,
  City of San Diego approval-event data, and further EH turnaround pages. These
  are useful additional targets, with city/state scope kept distinct from county
  evidence. Search caches retain their exact URLs.
- Historical backfills and exhaustive grand-jury/forum harvests were not done.
  Accounts, authenticated APIs, challenge bypass and paid purchases were not used.

## Verification, source states and budget

[Manifest](../../corpus/counties/raw/wide_net_target/MANIFEST.json) records all
retained originals, selected-column URLs, derived files, browser evidence and
hashes. [Checks](../../corpus/counties/raw/wide_net_target/retrieval_checks.json)
record row/key/date/source-flag summaries. PDF-to-text conversions are separate
from original PDFs. ZIP members stay in their original archives.

Eight search queries and 17 distinct source URLs were attempted (12 retained
download/API URLs, three Census landing pages, one failed guessed older landing
path and the failed DHCS index). Browser inability to render ZIPs was resolved
by ordinary public downloads, not counted as source absence. Searches, repeat
opens and ZIP members are not additional distinct-source counts.

This bounded continuation stopped to hand off the requested generation plan,
well within its maximum retrieval budget. It is **not** a claim of exhaustive
retrieval, all-county process gold, or newly demonstrated Bayesian performance.
