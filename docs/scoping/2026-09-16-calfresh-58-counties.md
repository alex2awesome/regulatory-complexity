# CalFresh county timeliness: P1 execution record

Started 2026-09-16, owner `codex`, packet `P1-CALFRESH-DATA`. This report is being
written incrementally under the [shared work protocol](../2026-09-16-county-scale-up-plan.md#9-the-shared-work-queue-how-two-agents-run-this-together).
Status: **acceptance checks completed**, with limitations below. No Bayesian or
generator code, model fit, or reserved data is changed.

## Verdict

**Keep CalFresh near the top of the shortlist.** It has verified county-month
timing aggregates, not just statutory deadlines. Common software has **not made
reported county performance uniform**. A causal estimate of how much the rollout
reduced variation, or an inventory proving which local routes remain different,
is not established by this packet. Treat performance variation and process-graph
variation as separate questions.

The reproducible extraction is [calfresh_cf296.csv](../../corpus/counties/calfresh_cf296.csv),
with [measure definitions and reproduction instructions](../../corpus/counties/calfresh_README.md),
[CF 296 provenance/quality flags](../../corpus/counties/calfresh_cf296_provenance.json),
and a [CF 18 timing companion](../../corpus/counties/calfresh_cf18.csv).

## Scope and current verification

The immediate question is whether the published CF 296 workbooks contain actual
county-level monthly processing-timeframe counts, and what their denominators
mean. A statutory deadline is not an observed mean or median; statewide and county
rows must remain distinct; suppressed counts must not become zeros.

The [CDSS CF 296 landing page](https://www.cdss.ca.gov/inforesources/research-and-data/calfresh-data-tables/cf296)
lists annual files from FY 2016–17 through FY 2024–25 and an ongoing July 2025+
file. It describes applications, expedited service, processing timeframes and
recertifications. It also warns of revisions and suppression of cells below 11.
**County rows are verified.** Both requested fiscal-year workbooks contain 708
rows: 12 months × (58 counties + a separate statewide row), with 123 report cells.
FY 2024–25 explicitly marks Alameda as not reporting in all twelve release notes;
its measure cells are blank, not zero. The older files use `FinalData`, newer ones
use `Data_External`, and metadata columns move. Parsing must use headers.

The [report-form index](https://www.cdss.ca.gov/inforesources/research-and-data/report-form-and-instructions)
lists both a CF 296 form effective July 2016 and a newer form effective July 2025.
This requires checking definitions across vintages before concatenating a series.
The July 2025+ workbook has 135 cells and renumbers existing measures. Its 13
published months run July 2025–July 2026. Keep versioned measure identifiers.

The [CF 18 companion](https://www.cdss.ca.gov/inforesources/data-portal/research-and-data/calfresh-data-tables/cf-18)
is especially useful: the FY 2024–25 workbook has average approval days for initial
expedited and non-expedited applications, plus timing-bin counts. The expedited
clock can start at discovery of expedited eligibility, not necessarily original
application. These are approval-conditioned aggregates, not all-applicant elapsed
burden, step durations, or staff/payer work hours.

The dictionaries alone omit a material qualifier present in CF 296's worksheet
headers: over-30-day approvals/denials count **county-welfare-department-caused**
delays. They do not measure all cases taking more than 30 days.

## Access log

- Web access to the CF 296 landing page, form index and CalFresh data-table index
  succeeded. A web fetch of the general `/calfresh` page timed out; it does not
  establish that the page or program evidence is absent.
- The first local `curl` request failed on sandbox DNS resolution. That is a
  local execution restriction, **not a county/CDSS website availability failure**.
- Public-source downloads succeeded after network approval. The automated XLS
  forms are encrypted according to `xlrd`; published ACL instruction PDFs are
  the fallback. No protection is bypassed and no project dependency is changed.
- The Santa Clara August 2025 eligibility audit returned HTTP 403 to local
  download, but its full PDF is readable through the web reader. Preserve this
  distinction between retrieval paths.

## Deliverables and checks

| Extract | Coverage verified from files | Important limit |
|---|---|---|
| CF 296 | July 2016–July 2026; 58 counties × 121 months; 872,262 county measure cells | Repeated totals/subsets are not independent observations; 15 wholly missing county-months |
| CF 18 timing | FY 2024–25; 58 counties × 12 report months × 10 cells | Initial approvals only; ES clock may begin at discovery; report month is preserved literally |
| CF 256 companion, cached but not flattened | May 2024–July 2026; 27 months × (58 counties + statewide) | Participation/issuance volume, not processing duration |

CF 296 contains 704,994 numeric county cells, 165,413 suppressed cells, 1,845
blanks and 10 spreadsheet-error cells. Statewide aggregates are exported
separately. Missing months are Placer March 2020 and Alameda May 2024–June 2025;
all agree with release notes. Published numeric zeros are retained, not certified
as absence of activity. Publication/suppression practice visibly varies by file;
do not model every star as a value between one and ten.

CF 18 has 30 channel/month records with zero summed timing-bin denominators,
plus one internally questionable mean (Modoc October 2024, non-expedited).
San Luis Obispo's July 2024 non-expedited mean of 222 days is retained as reported,
not silently capped or turned into a “typical” county effect. The open-ended
upper bin alone cannot prove it erroneous. Source validation and robust
observation modeling remain necessary.

An additional aggregation check found that the published CF 18 statewide means
numerically match the unweighted mean of county means. For July 2024 non-expedited
approvals the statewide value is 15.5528 days, but weighting county means by the
matching 12,796 application-bin counts gives 12.2229 days. The worksheet publishes
values rather than formulas, so this is a diagnostic numerical match, not a
verified statement of the producer's implementation. Preserve the aggregation
target and do not interpret the statewide value as an applicant-weighted mean.
The per-month calculations are retained in CF 18 provenance.

Verification passed: source hashes; one row per county/report month; expected
form-cell inventories; unique long-table keys; publisher code consistency;
preservation of suppression, missingness and error tokens; and equality of ES
bin totals wherever the relevant cells are numeric. A separate seeded round-trip
check compared 100 CSV cells per table to the original workbook coordinates
(200 checks, all passed). These are extraction checks, not administrative-data
validation or a Bayesian benchmark result.

## All timing fields in the two requested workbooks

FY 2023–24 and FY 2024–25 contain six groups, each with PACF, NACF and total:
late approvals caused by the county (cells 5–7), late denials caused by the county
(17–19), expedited benefit issuance in 1–3 days (29–31), 4–7 days (32–34), over
7 days (35–37), and overdue recertifications caused by the county (121–123).
There is no elapsed-days mean or median. Denominators, cohort alignment and exact
clock definitions are in the [README](../../corpus/counties/calfresh_README.md),
checked against [ACL 16-39E2](https://www.cdss.ca.gov/portals/9/acl/2016/16-39e2.pdf).

The July 2025 revision adds overdue federally funded application/recertification
bins and renumbers cells. It is extracted under a separate schema version. New
bins' detailed clock/cohort semantics remain unverified because the automated
form is encrypted; **do not use these new fields as elapsed durations yet**.

The stronger direct-duration source is CF 18: cells 59 and 63 are mean approval
days, with associated counts in 60–62 and 64–68. Means are not labor hours, denied
cases are excluded, and the expedited clock is not necessarily application-to-
issuance. Its instructions also explicitly allow zero when counties cannot track
a service. See [ACL 18-117E](https://www.cdss.ca.gov/portals/9/acl/2018/18-117E.pdf),
PDF pp. 22, 24 and 29–31. Means and histograms from the same cases must not be
fed to the model as independent evidence.

## Companion/access/audit sources

- [CF 256 / DFA 256 index](https://www.cdss.ca.gov/inforesources/Research-and-Data/CalFresh-Data-Tables/DFA256):
  participation and benefit issuance; historical links from FY 2015–16 to April
  2024 and a revised May 2024+ series. The current workbook's county coverage is
  verified above; historical links are inventoried, not all downloaded. It can
  supply volume context but is not an expedited-service turnaround table.
- [CF 18 index](https://www.cdss.ca.gov/inforesources/data-portal/research-and-data/calfresh-data-tables/cf-18):
  links FY 2020–21 through FY 2025–26, including churn plus approval timing.
  Only FY 2024–25 timing cells were extracted here. Other blocks use distinct
  reference cohorts; retain the published report label until a clock crosswalk
  has been checked.
- [CFPA Program Access Index report](https://nourishca.org/CalFresh/CFPAPublications/PAI-FullReport-2017.pdf):
  despite the filename, its cover says **2015 index, published October 2018**.
  Tables 1–2 (PDF pp. 7–8) provide all 58 counties' index and rank. The index
  compares receipt with a population meeting selected eligibility criteria; it
  is neither a fully eligible participation rate nor a timing/performance score.
  Its historical SSI adjustment makes it unsuitable as an unchanged contemporary
  eligibility denominator. Cached for provenance, not merged into modern timing.
- [State Auditor 2015-503](https://information.auditor.ca.gov/pdfs/reports/2015-503.pdf):
  the located county-administration report is about **antifraud oversight**,
  cost-effectiveness methodology, match-list handling and corrective actions.
  Its tables track recommendation implementation, not a 58-county application-
  time panel. It points back to report 2009-101; that predecessor was not fetched
  within this budget. Do not claim a county timing series from either title.
- [State Auditor 2025-601](https://www.auditor.ca.gov/reports/2025-601/):
  the CalFresh section discusses statewide payment-error rates and financial
  exposure. It does not provide the sought 58-county timing/step-count matrix.
  Error-rate evidence could inform a different observation channel, with its
  own definition; it is not a processing-delay measurement.

The bounded search did **not** verify the plan's implied State Auditor source
with a broad per-county CalFresh timing matrix. This is an unresolved source lead,
not proof that no such report exists. CDSS workbooks already establish the main
timing-data acceptance condition without relying on that assumption.

## Has the common platform erased county variation?

**No for reported performance; not established for every process route.** The
July 2024 source rows provide a simple counterexample to identical outcomes:

| County | CF 18 non-expedited initial approval mean (days) | CF 296 CWD-caused >30-day approvals / all approvals |
|---|---:|---:|
| Los Angeles | 7 | 307 / 39,042 = 0.79% |
| Sacramento | 16 | 1,031 / 5,558 = 18.55% |
| Santa Clara | 10 | 961 / 3,070 = 31.30% |
| Merced | 30 | 305 / 998 = 30.56% |

These are two **different** published cohorts/estimands placed side by side, not
a merged sample. The mean uses initial non-expedited approvals; the percentage
uses CF 296 approvals and the specific county-caused-delay classification. Both
vary; neither alone separates staffing, selection, complexity, county reporting
practice and intrinsic service speed. Sources:
[CF 18 FY 2024–25](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/CF18FY24-25.xlsx)
and [CF 296 FY 2024–25](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/CF296FY24-25.xlsx).

Independent process evidence comes from the
[Santa Clara August 2025 eligibility audit](https://files.santaclaracounty.gov/exjcpb1666/2025-08/department-of-employment-and-benefits-eligibility-audit-public-final-08-01-25_0.pdf?VersionId=3Hj.MpdWSL5OkCyqNTY1YBMC.oTsZZzy).
Its executive summary and processing-delay section discuss staffing, local
workload arrangements, CalSAWS procedural issues, backlogs and proposed local
changes. This supports retaining county implementation/operational variation
even with common technology. A one-county audit is not a 58-county topology study,
and before/after observations without case-mix controls are not a causal estimate
of the platform's effect.

## What this changes for W2 / the eventual fit

1. CalFresh is a strong **aggregate timing anchor** and a test of heterogeneous
   clock/cohort handling. Use approval-conditioned means, interval counts and
   volumes as their actual measurement types; never convert a deadline into a
   duration or an overdue count into days.
2. Keep software/platform, county capacity, applicant mix and reporting practice
   distinct. County timing differences are not automatically agency causal effects.
3. Retain document/claim evidence for interviews, verification, branches and
   rework. These aggregates alone cannot recover number of steps, responsible
   agencies, payer hours or agency hours.
4. Freeze a county/program holdout before using these sources for calibration or
   evaluation. Give the LLM control the same evidence and cross-county summaries;
   shared information must not be an advantage reserved for the Bayesian method.
5. Report information per learnable block, not the number of scalar cells. The
   872,262 cells contain accounting identities, repeated totals and dependent
   month-to-month measures; they are not 872,262 independent cases.

## Budget and completion boundary

Eight searches and 40 fetch attempts, counting failed/local/web repeat attempts
conservatively; no further fetching after that limit. Twenty-seven public source
files were cached. An offline reproducibility helper lives next to the data;
production code and the stable work-packet definitions are unchanged.

All three acceptance checks are met: county timing verified; tidy CSV plus
definitions/provenance saved; post-platform variation verdict supported and
bounded. Remaining follow-ups are current instructions for the new 2025 bins,
full CF 18 historical extraction/event-month mapping, and deeper investigation
of the audit source lead. None is represented as completed.
