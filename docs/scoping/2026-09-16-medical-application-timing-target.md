# Medi-Cal application timing: bounded source retrieval

As of 2026-09-16. Owner `codex-medical`, N3-MEDICAL-APPLICATION-TIMING.
Status: bounded retrieval complete; published source located, numeric data
retrieval blocked. Used five searches and eight fetch actions, within the
five-search/fifteen-fetch limit. Separate from P6; existing renewal/call-center
materials were not re-downloaded. No tests, models, or shared covariate changes.

## Scope

Find measured county application-determination durations or deadline-compliance
counts. Keep applications, people, cases and determinations distinct; separate
45/90-day requirements from actual performance and distinguish MAGI/non-MAGI
or disability cohorts where the source does. Preserve missing, suppressed,
not-applicable and zero values rather than treating them interchangeably.

## Result: the missing source family is now identified

The official [DHCS announcement dated June 22, 2026](https://www.dhcs.ca.gov/news/stakeholder-news-june-22-2026/)
states that County Medi-Cal Performance Data publishes calendar-year 2025
application-processing timeliness separately for non-disability and disability
applications, plus annual redetermination timeliness, with annual refreshes.
This materially advances P6's unresolved application-data search: the announced
source exists outside the renewal and call-center CSVs it located.

The announcement's application-data link resolves to the
[official 2025 performance workbook](https://www.dhcs.ca.gov/?p=204204&post_type=dhcs-file-manager&preview=true).
The web reader identified an XLSX MIME type but cannot parse it. Direct public
download returned a 957-byte Incapsula challenge page rather than a workbook.
The failed body is retained as `failed_workbook_download.html`, **not** as data.
No authentication, challenge solving, or access-control bypass was attempted.

The related [DHCS performance index](https://www.dhcs.ca.gov/data-statistics/county-medi-cal-call-center-data/)
was also blocked to direct download. The similarly named
[County Performance Reports](https://www.dhcs.ca.gov/services/county-performance-reports/)
concerns substance-use program compliance, not general Medi-Cal eligibility
application timing; it is not a substitute.

## Verified reporting definitions, not verified outcome values

[ACWDL 25-08, April 1, 2025](https://www.dhcs.ca.gov/wp-content/uploads/2025/10/25-08.pdf),
pages 2–10, documents the following methodology; retrieved readable PDF text
is cached in `006-acwdl-25-08-clock-definitions.json`:

- Unit: individual/CIN, not household case. Both approvals and denials enter
  the determination-month cohort. Clock: county application receipt → final
  eligibility determination.
- 45-day measure: non-disability determinations, including MAGI and relevant
  non-MAGI groups. Numerator is complete/error-free applications processed
  within 45 days; denominator is the corresponding complete/error-free cohort.
- 90-day measure: disability determinations; completeness and DDSD-delay
  exclusions apply. Non-MAGI is not synonymous with disability.
- Exclusions include cash-linked categories, intercounty transfers,
  Craig v. Bonta referrals and Covered California carry-forward records.
- CMSPI Indicator 12 is received monthly; the dashboard aggregates a calendar
  year. A 90% performance target is not an observed success rate.
- Pages 10–14 separately document a roughly 120-day renewal reporting lag.
  Therefore a renewal-period consortium label need not timestamp operational
  migration. This letter does not independently establish cutover dates.

The underlying identified-person dataset is described as available to counties
through CalSAWS, not established as public microdata. No attempt was made to
access the county SharePoint/application. The workbook's actual implementation,
county completeness, suppression and any later amendments remain unverified.

## Coverage and source-state ledger

| Item | Verified state | What is not established |
| --- | --- | --- |
| June 2026 announcement | Official text opened and cached | Numeric county values |
| 2025 performance workbook | Exact official link and XLSX content type identified | Downloaded workbook, row count, county count, rates, denominators, missingness |
| ACWDL 25-08 | Readable official PDF text, including clock/cohort definitions | Successful binary original download; later superseding guidance |
| Direct downloads | Four challenge/error HTML bodies retained and hashed | These are not source-document originals or numeric datasets |

No county application-timing row was successfully extracted. Do **not** code
58 verified counties, zero suppression, a 2025 monthly panel, or numerical
45/90-day compliance from the announcement/manual alone.

## Verdict and exact next retrieval

**Published dataset located; numerical availability remains unresolved in this
session.** Retry the exact officially linked workbook in an authorized normal
browser/download workflow, or request its public accessible copy. After receipt,
inspect sheets/footnotes and count actual county denominators and suppression
before upgrading coverage. No message or public-records request was sent.

Artifacts are under `corpus/counties/raw/medical_application_target/`:
seven request/response caches, four explicitly classified failed-download HTML
bodies, and `MANIFEST.json` with SHA-256 hashes and request accounting.
This is an honest retrieval limitation, not a claim that application-timing
data do not exist. The optional operational-cutover search was not expanded.
The final exact-title/XLSX search did not locate an additional published
workbook URL; it returned an unrelated CalSAWS maintenance financial report,
which was not substituted for eligibility-performance data.
