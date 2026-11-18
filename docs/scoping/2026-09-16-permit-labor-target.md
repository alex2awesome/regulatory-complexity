# Permitting agency labor: source collection

2026-09-16. Owner `codex`, packet N5-PERMIT-LABOR-SOURCES. Bounded retrieval
complete: three searches, ten successful downloads, six PDF-text derivatives.
No model changes, fits or unit tests. This complements the
[social-services workload collection](2026-09-16-agency-workload-target.md).

## Result

Agency-side hours are published in county cost studies, but their measurement
basis varies considerably. This collection covers five counties, not a statewide
labor panel. It contains historical task-average estimates, some informed by
time records, plus current fee/context documents. It does not contain raw
case-level worker logs, waiting times, sampling variances or payer labor.

Originals and text derivatives are in
[the source cache](../../corpus/counties/raw/permit_labor_target/), with URLs,
SHA-256 hashes, vintages and source classes in
[MANIFEST.json](../../corpus/counties/raw/permit_labor_target/MANIFEST.json).

## 1. Contra Costa: recorded time plus adjusted estimates

The [June 6, 2025 NBS study](https://contra-costa.legistar.com/View.ashx?M=F&ID=14306502&GUID=838FB956-70B8-476D-B865-84759D9DBC47),
PDF pages 7–8, uses three fiscal years of time records, subsequently reviewed
and revised by managers. Missing or unrepresentative records were supplemented
with estimates. The inspected methodology does not identify those three years
or flag every adjusted cell. Cost inputs use the FY2024–25 adopted budget.

Appendices separate office administration, travel and the column labeled
EHS-DARS. Selected **published estimated hours**, transcribed directly:

| Activity / source location | Office | Travel | EHS-DARS | Published total |
|---|---:|---:|---:|---:|
| Conventional septic plan review, PE 4242, PDF 27 | 1.10 | 0.00 | 5.10 | 6.20 |
| Alternative septic plan review, PE 4243, PDF 27 | 1.10 | 0.00 | 7.22 | 8.32 |
| Restaurant plan review, 0–25 seats, PE 901, Appendix A.9 | 2.84 | 0.01 | 6.55 | 9.40 |
| Restaurant operating permit, 0–25 seats, RC3, PE 603, PDF 37 | 1.25 | 0.85 | 3.57 | 5.66 |

Preserve rounding differences; the estimated activity-volume column is not a
verified sample size. Operating-permit and plan-review units differ. A zero
allocated travel value does not establish no physical travel. Fully burdened
fees also allocate overhead; they are not wages multiplied by observed hours.

The [supporting June 24, 2025 program report](https://contra-costa.legistar.com/View.ashx?M=F&ID=14306501&GUID=2E253EA9-DBFB-42A6-AAD5-E3AEAB2C342E),
pages 5–6, separates operating oversight from construction review. It describes
a 15-working-day local review goal and a 20-working-day statutory review clock;
neither is measured turnaround. Its 2024 facility counts are contextual annual
program totals, not labor-study denominators. The
[hearing record](https://contra-costa.legistar.com/LegislationDetail.aspx?FullText=1&GUID=F1255547-8892-4572-8E38-349B2B96F9F4&ID=7442925)
links the originals and records adoption with amendments.

## 2. Sonoma: useful task estimates, with historical boundaries

The [August 24, 2021 NBS study](https://sonoma-county.legistar.com/View.ashx?GUID=36BAC7A5-37CB-4EA6-B282-8621553EA1DB&ID=10644223&M=F),
PDF pages 8–9, combines available time tracking with interviews and
questionnaires. It explicitly notes incomplete fee-level tracking. These are
typical-activity estimates, not uniformly measured durations.

Appendix A.5, PDF page 79, reports septic construction-plan review at 5 hours
for a standard system, 6 for an alternative system and 7 for an experimental
system; soil-profile/pre-percolation evaluation is 4 hours for up to five holes.
The appendix is labeled FY2019–20. Its distinct design-review, construction-
review and inspection categories must not be collapsed or automatically added
to every applicant's path.

The 18,388 direct hours used in the section's cost model are available/allocated
annual capacity, not 18,388 case observations. The $250 hourly cost includes
overhead and support, not just a worker's compensation.

The [April 14, 2026 fee-revision item](https://sonoma-county.legistar.com/LegislationDetail.aspx?GUID=ABD64FF4-2380-40FC-B5C1-DD721C66CFD6&ID=7972897&Options=&Search=)
reports omitted administrative effort in an earlier **fire-services** analysis.
That finding is not evidence that all well/septic estimates are wrong. Its
[attached FY2026–27 well/septic schedule](https://sonoma-county.legistar.com/View.ashx?M=F&ID=15368914&GUID=39D011BF-6097-4D5B-A51F-1A1171C914D1)
is retained for vintage and activity-identity checking. The attachment is labeled
proposed in the docket and still has an ordinance-number placeholder: it is
not independently verified as the executed final schedule. Prices are not
new measurements of labor, and the 2021 estimates are not labeled current.

## 3. El Dorado: explicit evidence of time-record quality problems

The [2019 Environmental Management staff report](https://eldorado.legistar.com/View.ashx?M=F&ID=7806764&GUID=3CD8AFDE-78FF-4B7D-BCC8-2C0E71E74E07),
pages 1–3, describes EnvisionConnect program-code records. In the FY2015–16
study, 92% of fee categories lacked adequate evidence for revising their hour
inputs: nonbillable work, turnover and training complicated interpretation,
and interviews did not resolve it. This is not a statement that 92% of all
individual time entries were erroneous.

The report presents updated FY2018–19 averages after accounting improvements.
Its restaurant/bar annual-permit example changes from 3 to 4.5 staff hours;
restaurants under 650 square feet change from 2.5 to 3.5 hours. These include
inspections, follow-up and qualifying consultations but exclude routine support
staff assistance classified as overhead. The report attributes additional food
inspection work to changed training/practices; it is not an efficiency ranking.

The same document describes adding routine onsite inspection to well-permit
work. Activity boundaries changed, so an apparent hour increase can reflect
new work rather than slower execution. The
[docket](https://eldorado.legistar.com/LegislationDetail.aspx?FullText=1&GUID=2D5075FC-4B79-48C9-97A0-C3D1C3DDF51F&ID=4196113&Options=&Search=)
and original attachment are both cached; underlying logs were not retrieved.

## 4. Placer: expert estimates, not a time-and-motion dataset

The [March 17, 2024 cost study, within the April 23 board packet](https://www.placer.ca.gov/DocumentCenter/View/78931/20A),
printed study pages 10–15 (PDF pages 28–33), says activity times primarily
come from experienced staff estimates because actual time data are unavailable.
Some estimates describe a desired minimum professional service level rather
than current practice. Fixed-fee averages intentionally do not retain
applicant-to-applicant time variation.

Its approximately 1,411 annual billable hours per position are a capacity
calculation after nonbillable allowances, not an observed case duration or
universal public-worker standard. Costs use the FY2023–24 budget and include
indirect support and overhead. These estimates may inform an explicitly
uncertain expert-evidence channel, not an empirical labor-outcome likelihood
with thousands of independent samples.

The original is a 130-page packet; text extraction produced an optional-content
warning but readable methodology. No claim is made to have validated every
appendix cell or a later revised schedule.

## 5. San Mateo: billing standards are a separate source class

The [EHS fee page](https://www.smchealth.org/pod/environmental-health-services-fees)
lists January 1, 2026 amounts, including a $328 land-use hourly rate and a
12-hour retainer for an unsewered subdivision application. The page describes
average resource requirements and inflation/workforce adjustments. The retainer
is a billing provision, not an observed twelve-hour case, and fee/rate division
does not recover a measured task time.

## Handoff

Retain source-specific units, activity scope, actor, vintage and measurement
method. Distinguish records revised for fee setting, expert service estimates,
funding/capacity allocations and billing provisions. Shared consultant methods
and reused time records can also correlate evidence across documents.

The best next retrieval is the underlying Contra Costa time-record definitions
and aggregation methods, or El Dorado program-code totals with denominators
and exclusions. These are leads, not data already obtained. No public-records
request, authentication or external outreach was performed. The source-finding
budget is exhausted; this is a completed bounded collection, not complete
statewide labor coverage.
