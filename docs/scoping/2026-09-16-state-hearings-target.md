# State hearings: source retrieval and measurement scope

2026-09-16, Codex, packet N8-STATE-HEARINGS. Bounded continuation after the
[independent P12 spot-check](2026-09-16-p12-independent-spotcheck.md).
Budget used: three search queries and twelve distinct source fetches; no outreach,
unit tests or model changes. Bounded collection complete, **not** a completed
county-timing panel. Original downloads and web inspection of the same URL count
as one distinct source; browser caches and local derivatives are listed separately.

## Retained sources

The official [CDSS State Hearings data index](https://www.cdss.ca.gov/inforesources/data-portal/state-hearings-data-statistics)
links annual and quarterly reports. Cached the index, FY2025–26 annual report,
its fourth-quarter report, and FY2024–25 annual report under
`corpus/counties/raw/state_hearings_target/`, with text derivatives for PDFs.

The [FY2025–26 report](https://www.cdss.ca.gov/Portals/9/SHD/SHD%20Hearing%20Data%20Summary%20Report%20FY%202025-2026.pdf)
is 23 pages dated July 7, 2026; the prior annual and latest Q4 report are each
22 pages. They report program/quarter activity, including filings, withdrawals,
scheduling, postponements, nonappearances, decisions and rehearings. The ten
selected count tables have 15 program categories. No county or elapsed-duration
columns were found in these three reports.

Following an older official timing table led to CDII's
[annual complaint report index](https://www.cdii.ca.gov/consumer-reports/complaint-data-reports/annual-complaint-data-reports/).
Its newest listed release is June 2026, for **measurement year 2023**. Cached:

- The [main MY2023 report](https://www.cdii.ca.gov/wp-content/uploads/2026/06/MY-2023-Complaint-Data-Report_Final.pdf),
  109 pages.
- The [MY2023 numeric tables](https://www.cdii.ca.gov/wp-content/uploads/2026/06/MY-2023-Complaint-Report-Data-Tables.pdf),
  39 pages.
- The [detailed MY2023 methods](https://www.cdii.ca.gov/wp-content/uploads/2026/06/MY-2023-Complaint-Report-Detailed-Methodology.pdf),
  33 pages.
- The 2017 data tables (40 pages), as the discovery/historical source, **not**
  current performance, plus four CDII navigation/method-context pages.

Together these are seven PDFs and five HTML originals. The data tables reproduce
the main report: they are not independent observations. Likewise the CDII
hearing information originates in the state-hearing process, not a wholly
independent measurement system from CDSS.

## Three retained numeric tables

All paths below are under
[`corpus/counties/raw/state_hearings_target/`](../../corpus/counties/raw/state_hearings_target/).
The [inventory](../../corpus/counties/raw/state_hearings_target/INVENTORY.json)
records table pages, row counts and cross-publication discrepancies; the
[source manifest](../../corpus/counties/raw/state_hearings_target/SOURCE_MANIFEST.json)
hashes 29 originals/derivatives (excluding the manifest itself).

| File | What was extracted | What it is not |
|---|---|---|
| `shd_program_quarter_counts.csv` | Two fiscal years × ten measures × 15 programs: 300 program rows, each with four quarterly counts and an annual total; 20 additional statewide-total rows | A linked cohort, unique-person panel, county panel, or 1,600 independent observations |
| `hearing_resolution_means.csv` | 16 mean-day values: five annual DHCS and five annual Covered California means for 2019–2023, plus formal/informal Covered California means for 2021–2023 | Microdata, waiting-time quantiles, worker hours, or a complete sampling-error specification |
| `complaint_county_ratios_2023.csv` | 30 selected DHCS counties and 15 selected Covered California counties, with displayed complaints per 10,000 members | County hearing durations or zero complaint rates for omitted counties |

### Actual timing, with selection and actor boundaries

For complaints **closed in 2023**, the report gives DHCS State Fair Hearings a
60-day mean. Covered California reports 64 days for formal hearings and 20 days
for informal resolution; its combined mean is 26 days. It reports 85% of its
5,075 complaints were resolved informally (main report pp.90–91, 96–97).
These are observed summary durations, distinct from the adjacent 90- and 45-day
standards. Source pages/figures accompany each CSV row.

The important distinctions are:

- The **2023 closure cohort** can include cases opened before 2023 and excludes
  still-open cases. It cannot directly estimate the wait for all new applicants.
- Durations reflect recorded complaint opening/closing dates. The methods
  require dates in order and a closing date in the measurement year, but the
  report warns that agencies' date definitions differ: first contact versus
  complete complaint, original versus reopened date, and consumer resolution
  versus later oversight closure (main report pp.12–13). Do not assume the
  legal deadline clock equals the measured duration clock.
- **DHCS is the reporting entity**, while CDSS conducts State Fair Hearings.
  Covered California handles referred informal resolutions and participates in
  formal hearings. These spans are multi-actor process outcomes, not intrinsic
  DHCS or county-agency service times (main report pp.41, 91).
- The appendix provides no variance or full per-stratum sample sizes alongside
  these means. Annual volumes elsewhere are not automatically usable denominators
  for every timing subset. CSV sample-size/variance fields remain blank.
- The 2023 report also gives six DHCS delivery-system means (main report p.51),
  retained in the PDF but not exported here. Those strata overlap the overall
  DHCS mean; they are not six independent replications of it.

This is useful evidence for a timing model with an explicit observation/cohort
layer. It does not yet identify county-specific or intrinsic agency delay.

### County ratios are selected, and definitions disagree

The county is the **complainant's residence**, not necessarily the agency
performing the task. DHCS figure 5.18 displays 30 counties satisfying its
70,000-member and at-least-11-complaint criteria. Covered California figure
7.16 displays 15 counties and excludes informal resolutions; its footnote uses
10,000 members and at least 11 formal hearings. Missing counties remain
unpublished/filtered, never zero.

There is an unresolved source inconsistency: detailed methods p.8 states a
70,000-member display threshold for DHCS **and Covered California**, whereas
both the main report p.101 and table appendix p.38 give Covered California's
10,000-member threshold. The CSV flags this conflict. The methods also mention
June Covered California enrollment (p.6), while the main report's overall
enrollment note says July (p.7). These may involve different denominators;
the available notes do not establish their reconciliation. No hidden county
counts or memberships were back-calculated.

## Source spot-checks and discrepancies

The 20 annual program tables' row sums and column totals all reconcile: 1,280
quarter cells plus 320 printed annual-total cells across 320 rows. Of these,
1,200 quarter cells concern individual program categories; the rest are
statewide totals. Annual totals are redundant sums, not extra evidence.

Comparing Q4 in the annual report with the separately published April–June
report gives **158 matches out of 160 program/total comparisons**, after the
explicit `Rehabilitation Services` → `Rehabilitation` label crosswalk:

| Appeals administratively dismissed, Q4 2025–26 | Annual report p.6 | Q4 report p.6 |
|---|---:|---:|
| Covered California | 3 | 1 |
| MAGI Medi-Cal | 22 | 24 |

Both still total 899 for the quarter. The discrepancy could be reclassification
or another source error; no revision explanation was verified. Both originals
and page renders are retained, and the two annual CSV rows are flagged. These
are source differences, not a claim that either publication is ground truth.

The prior annual report p.11 labels its hearing table as monthly, although its
column headers are quarters. Its extracted rows are flagged accordingly.
The word *untimely* in the rehearing-determination table denotes rejected
rehearing requests; it is not an agency-processing timeliness observation.

The two CDSS discrepant pages and the two CDII threshold pages were also
visually inspected. No PDF layout inference was used to silently repair them.

## Use and remaining gaps

The retrieved material supplies appeal/rehearing branches, formal versus
informal pathways, administrative outcome counts, multiple responsible actors,
and measured aggregate elapsed time. This expands the evidence beyond initial
application processing. It supplies **no worker-hour measurements or case-linked
county timestamp panel** in this pass. Period filings, hearings held and
decisions released have different event dates and must not be divided into
transition probabilities as if they were one followed cohort. Repeated
hearings/postponements can also generate multiple events for one case.

Next targeted retrieval could pursue published county hearing logs or confirmed
open aggregate exports. Earlier annual/quarterly links are preserved in the
indexes; a full historical backfill was not attempted within this budget.
No individual confidential complaint records, authenticated systems or public
records requests were accessed.
