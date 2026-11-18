# Workload-study methods and measurement boundaries

2026-09-16. Owner `codex`, N6-WORKLOAD-DETAIL. Bounded retrieval complete;
five searches and ten fetches, within the five-search/twelve-fetch cap. Follow-up to
[N4 agency workload](2026-09-16-agency-workload-target.md), not a new model.

## Important correction from the detailed report

The [SB 2030 findings chapter](https://www.cdss.ca.gov/cdssweb/res/cws/sb2030final/pdf/section5.pdf),
printed pages 43–49, clarifies that the 13,584 staff and 1,140,667.6 recorded
hours include primary case workers, other case-related workers and
administrative-only workers. The executive summary's case-carrying description
should not be applied to the whole sample. Its headline five program means
use the narrower primary-worker group.

Those means are not raw stopwatch averages: most are converted from two weeks
to a month and adjusted using cases touched, administrative caseload counts
and participation. Reports, referrals and cases are different denominators;
a case may appear in multiple service categories. Intake keeps its two-week
basis. These facts change the observation definition, not just confidence.

The reported 93.8% average county response excludes Yuba's unavailable eligible-
staff denominator. Participation by all counties still does not provide a
public county-by-task labor panel.

The chapter has 56 rendered PDF pages, numbered 43–98. A file-identification
utility misleadingly reported 98 pages; that preliminary count in the live log
is superseded here. Source originals are retained under
`corpus/counties/raw/workload_detail_target/`.

## Methods retrieved

The [methods chapter](https://www.cdss.ca.gov/cdssweb/res/cws/sb2030final/pdf/section4.pdf)
has 34 pages, printed 9–42. Staff entered daily activity end times; durations
were calculated from consecutive entries. Sub-two-minute activities could be
combined into the next activity. Logs included noncase activity, breaks and
explicit unpaid gaps. Entries could be retrospective. This is self-reported
time recording, not independently observed completion timestamps.

Table III.03 dates collection by geographic group between September 7 and
October 17, 1999, with different two-week windows and two Los Angeles phases.
Final server collection continued to November 2 for corrections. All-county
participation therefore does not mean simultaneous observation. The design
targeted all eligible staff, but nonresponse and classification problems remain.

The attempted parent-directory URL returned the general CDSS home page, not a
report index; it is retained as an unsuccessful discovery response. Some chapter
URLs were discovered by following the report's numbered public-file convention;
their actual content and page sequences were checked, not inferred from names.

## Additional measured aggregates

[Section 6](https://www.cdss.ca.gov/cdssweb/res/cws/sb2030final/pdf/section6.pdf),
printed pages 99–101, supplies travel means and medians by worker role and four
county-size groups. The grouping is **CWS staffing FTE**, not population or
rurality. The calculation excludes employees who recorded no travel tasks.
It combines client transportation, vehicle-related work and other travel.

The eight role-by-size rows are saved in
`sb2030_travel_by_staff_and_size.csv`, preserving HH:MM:SS units and the
two-week window. They are conditional worker totals, not hours per client or
unconditional agency travel costs. Source group definitions leave exact boundary
values ambiguous; no county was assigned to a group by this collection.

`sb2030_primary_program_aggregates.csv` preserves five program totals with the
different report/referral/case units and adjusted mean definitions. These and
the N4 summary are **the same underlying study**, not independent replications.
The source's roughly 1.5 million logged activities were not acquired as
microdata; only published aggregates and methodological descriptions were obtained.

## What is now cached

| Original | Content verified | Rendered pages |
|---|---|---:|
| Section 2 | Front matter/contents; image-only, selected pages rendered/OCRed | 8 |
| Section 3 | Opening main-report material, printed 1–8 | 8 |
| Section 4 | Methods, printed 9–42 | 34 |
| Section 5 | Findings, printed 43–98 | 56 |
| Section 6 | Further analysis, printed 99–130 | 32 |
| Section 7 | Further financial analysis, printed 131–142 | 12 |
| Section 8 | Recommendations, printed 143–160 | 18 |
| Section 9 | Future-study methods, printed 161–166 | 6 |
| Section 10 | Image-only references; first page rendered/OCRed | 5 |

The main report's pages 1–166 are therefore cached, but not its separate
appendices or underlying logs. The 29-page executive summary remains in the
N4 cache and was not downloaded again. Method and selected-table sections were
read; retained does not mean every page was independently audited.

[Section 9](https://www.cdss.ca.gov/cdssweb/res/cws/sb2030final/pdf/section9.pdf)
also discusses reporting fatigue and recommends periodic studies. That is a
historical methodological recommendation, not evidence that such follow-ups
were subsequently performed.

## Remaining gaps and provenance

The bounded CEC/CECRIS search found claiming instructions and references to
administrative expenditure data, but no verified public worker-pool hour export.
That is unresolved availability, not a claim that the records do not exist.
No authenticated claim system was accessed and no records request was sent.

The [catalog](../../corpus/counties/raw/workload_detail_target/MANIFEST.json)
separates nine report PDFs, the unsuccessful index response, text/render/OCR
derivatives and two small source tables. Image-only text-extraction outputs are
flagged as empty, not successful full-text extractions. No tests or model changes.
