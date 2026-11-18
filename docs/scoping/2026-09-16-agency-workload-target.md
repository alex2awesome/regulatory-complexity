# Agency-side workload: bounded source retrieval

As of 2026-09-16. Owner `codex-workload`, N4-AGENCY-WORKLOAD.
Status: bounded source collection complete. Used five searches and fifteen
fetch actions; stopped at those limits. No tests, models, shared covariate
changes, or other packet edits.

## Scope

Seek actual sampled/measured county-worker time. Distinguish time studies,
funding assumptions, budgeted positions, caseload ratios and expenditure claims.
IHSS caregiver-authorized service hours are not county-worker labor hours.
The N1 State Auditor 2020-109 cached material is reused, not re-downloaded.

## Verdict

**A credible historical county-worker time study was found.** It concerns
Child Welfare Services (CWS), not IHSS. The retrieved summary provides statewide
program-level measured time and a clearly separated comparison with funding
and recommended standards. A current 58-county IHSS worker-hour/task panel
was **not verified**. County expense claims offer another promising source
family, but claim allocations cannot automatically be read as direct labor.

## Historical measured worker time: SB 2030

The [official CDSS report, April 2000](https://www.cdss.ca.gov/cdssweb/res/cws/sb2030final/pdf/section1.pdf)
describes time-log collection over two weeks, participation by all 58 counties,
13,584 staff and 1,140,667.6 recorded hours. **Correction after retrieving the
detailed chapters:** the summary calls these case-carrying staff, but the
[methods and findings](2026-09-16-workload-detail-target.md) explicitly include
primary, non-primary and administrative-only staff in those totals. They are
not all frontline case-service hours. This is recorded activity time, not
stopwatch observation. The overall evaluation ran
June–December 1999; that is not six months of worker-time observations.
The source is a 29-page executive summary, despite the cover's final-report
title. Its county participation count does not provide 58 county-specific
time estimates.

| Program | Measured hours | 1984 allocation standard | Recommended minimum | Recommended optimum |
| --- | ---: | ---: | ---: | ---: |
| Screening/hotline/intake | 0.78* | 0.36 | 1.00 | 1.69 |
| Emergency response | 7.19 | 7.35 | 8.91 | 11.75 |
| Family maintenance | 3.97 | 3.32 | 8.19 | 11.44 |
| Family reunification | 4.97 | 4.30 | 7.45 | 9.72 |
| Permanent placement | 2.37 | 2.15 | 4.90 | 7.07 |

Source: printed page iii, PDF page 5. The detailed chapter clarifies that these
means concern **primary workers**, with reports/referrals/cases as the relevant
service units rather than one uniform case denominator. Most use adjusted
monthly calculations; **measured intake remains a two-week value**.
The footnote is preserved, not harmonized. Recommended values combine policy
review and focus-group judgment; they are not observed durations. Other staff's
contributions are not part of these headline primary-worker means. These
historical service-unit averages are neither modern IHSS task minutes nor
end-to-end client waiting times.

`sb2030_time_comparison.csv` also preserves the source's caseload-per-worker
figures. The report uses 116.10 monthly hours available for direct case
services for those conversions. Do not treat the two-week intake row as
comparable without resolving its special basis. N6 subsequently retrieved the
detailed collection/adjustment methods; independent task timestamps,
individual logs and a county-by-task time panel remain unverified. The original
N4 CSV and its hash are preserved; N6 supplies the refined actor/unit definitions.

The [CWDA workload-study index](https://www.cwda.org/publication/child-welfare-services-workload-studies)
links another copy of the same summary and the
[UC Davis November 2006 budgeting report](https://www.cwda.org/sites/main/files/file-attachments/cppr_cws_final_report_111306.pdf?1450974927).
The latter 74-page report is retained as a methodology lead, not represented
as a second measured worker-time dataset. The duplicate summary was not
mistaken for the full technical report.

## County Expense Claim: the unit is hours **or observations**

The [November 2020 CEC manual](https://www.cwda.org/sites/main/files/file-attachments/cec_manual_-_november_2020_final.pdf?1604440032=)
was written by CDSS and participating counties and hosted by CWDA. Its
272-page original is cached. Relevant printed pages 74–78 (PDF 82–86)
describe DFA 10 inputs and DFA 55 outputs: social-worker, employment-service,
eligibility-determination and fraud-worker pools report program-coded
time-study hours/observations, which generate salary-allocation ratios.
Salary/benefit inputs come from payroll records.

The glossary distinguishes continuous daily recording from random-moment
activity sampling (printed pages 204 and 210). Therefore an observation count
must not be labeled hours. Generic cost redistribution and funding-ratio
splits mean reported program dollars need not be directly clocked effort.
The manual is a training resource; its examples are not real county
observations, and many section vintages predate its 2020 cover. It directs
users to newer fiscal letters and county-specific source-document procedures.

[CFL 24/25-83, June 26, 2025](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Letters-and-Notices/CFLs/2025/24-25_83.pdf)
documents CECRIS time-study/claim changes for July–September 2025.
The [December 4, 2025 erratum](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Letters-and-Notices/CFLs/2025/24-25_83E.pdf)
corrects allocation methods and adds CARES-Live guidance. Its explicit
funding-ratio reallocations reinforce the distinction between recorded
activities and allocated costs. Both originals were downloaded; the web
reader rejected the version-query URL for the first, so that reader failure
is retained. These are verified dated instructions, not a claim to have
checked every subsequent amendment or obtained counties' actual claim files.

## IHSS administrative expenditures: actual dollars, not worker hours

Reused [State Auditor 2020-109, Table 7](https://information.auditor.ca.gov/reports/2020-109/chapters.html)
from the N1 cache. For FY2014–15 through FY2018–19 it reports combined county
and public-authority administrative costs of $21m Butte, $33m Kern, $143m
San Diego and $36m Stanislaus; statewide $2,768m. These are five-year totals,
not annual observations. The source names county accounting records and the
CDSS County Expense Claim system. `ihss_audit_admin_expenses.csv` preserves
the reported values, unit and period. No division by an assumed wage was used
to manufacture labor hours; nonlabor costs and mixed administrative actors
would make that conversion unsafe.

The [LAO February 16, 2018 analysis](https://lao.ca.gov/Publications/Report/3757)
explains that IHSS administrative budgeting formerly used 2001 worker-cost
and workload estimates and was being updated using assumptions about wages
and staffing needed at prevailing caseloads. Those are allocation assumptions,
not newly observed worker-minute measurements. Caregiver service-hour
guidelines in IHSS likewise measure a different actor's work.

## Source coverage, limits and next material

| Evidence class | Located | Not established |
| --- | --- | --- |
| Historical measured worker effort | Five CWS program means, time-log study reported across 58 counties | Modern IHSS transferability; county-specific hours; independent timestamps |
| Accounting measurement procedure | CEC worker pools, hours/observations, salary allocation and 2025 changes | Public raw 58-county claim/hour panel |
| Actual IHSS administrative spending | Four reviewed counties plus statewide five-year totals | Case-level effort; cost of an individual application |
| Funding/workload expectations | Separate SB 2030 recommendations and LAO administrative assumptions | Observed compliance or actual effort represented by those expectations |

All new sources and hashes are in `corpus/counties/raw/agency_workload_target/`.
`MANIFEST.json` distinguishes downloaded originals, the duplicate summary,
request caches, two derived source tables, and reused N1 sources. No missing
county or unobserved hour was imputed. Two web-reader failures did not prevent
successful PDF downloads; neither failure is evidence of absent publication.

The [N6 follow-up](2026-09-16-workload-detail-target.md) now retains the SB 2030
main report and its technical methods. Individual logs, county-by-task tables
and a public CEC/CECRIS export with worker-pool unit definitions remain follow-up
leads. The historical-source find does not establish those datasets' availability.
