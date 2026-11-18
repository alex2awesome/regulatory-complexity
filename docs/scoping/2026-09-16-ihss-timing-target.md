# IHSS: bounded timing-target validation

As of 2026-09-16. Owner `codex-ihss`, target N1-IHSS-TIMELINESS.
Status: bounded collection complete, 2026-09-16 19:02 PDT.
Budget used: six searches, eighteen fetch actions. Separate from P6's broad
program ranking. No model work or unit tests.

## Measurement scope

Separate recipient application → eligibility/needs assessment → service
authorization from provider enrollment → timesheet → payroll. A provider's
authorized care hours are not county social-worker labor hours. Statutory or
regulatory deadlines are not observed durations. County rows on an index do
not by themselves verify a 58-county timing panel.

Initial official leads: [CDSS monthly program data](https://www.cdss.ca.gov/inforesources/ihss/program-data),
[State Auditor report 2020-109](https://information.auditor.ca.gov/reports/2020-109/chapters.html),
and [CDSS program/assessment description](https://www.cdss.ca.gov/in-home-supportive-services).
The audit's historical application-delay evidence will not be presented as
current performance. Source text, downloads and failures are cached in
`corpus/counties/raw/ihss_target/`.

## Verdict

**Retain IHSS as a qualified target.** A statewide historical approval-time
table is genuinely available for all 58 counties. Current monthly workbooks
offer denial-duration bands and a reassessment-status stock, not a verified
current approval-duration panel. None measures county-worker labor time.

## Dataset, clock and denominator checks

| Source actually examined | Unit and clock | Verified coverage | Main restriction |
| --- | --- | --- | --- |
| State Auditor 2020-109, Appendix B.3 | New recipients: recorded application → approval, mean days and recipient count | 58 counties × 2015/2019 = 116 county-years with numeric means and positive counts | Historical approved-recipient cohort, not all applications or pending cases; no microdata here |
| Same audit, B.4 | New recipients whose first service occurred after approval: approval → first service, mean days and count | 116 county-years; 114 numeric means, two N/A with zero recipients | Omits recipients still unserved; not provider enrollment or first payroll |
| CDSS June/July 2026 program workbooks, Data GP:GS | Publisher's processing-time bands for denied applications; denial counts are the denominator | 58 counties × two report months; positive denominator in 56/55 counties | Reporting-window and band-label conflicts; no approval-time field verified |
| Same workbooks, Data GN and D | Outstanding reassessments and authorized-recipient stock | 116 county-months with numeric values and positive recipient stocks | Not mean reassessment delay, applications processed, or number of reassessments due that month |

### Historical measured durations

[Appendix B.3/B.4 and methodology](https://information.auditor.ca.gov/reports/2020-109/appendices.html)
provide actual county rows, not merely a county index. B.3 statewide means
are 82 days/74,846 new recipients (2015) and 72 days/87,711 (2019).
B.4's two N/A observations are Alpine 2015 and Mono 2019. Its 2019 cohort
omits over 12,700 approved recipients still unserved when data were reviewed
in June 2020; completed waits therefore are selected. The auditor rated the
CMIPS II data's reliability undetermined, while finding sufficient overall
evidence for its conclusions. The published tables do not supply case-level
date fields, restart rules, or an explicit business/calendar-day convention.

The [audit narrative](https://information.auditor.ca.gov/reports/2020-109/chapters.html)
describes a generally 30-day determination requirement and CDSS's then-used
90-day interpretation, which the auditor disputed. Those are historical
normative benchmarks, not measured durations or a verification of today's
law. Its five-year service-start statistic is not interchangeable with the
two annual B.4 cohorts. County explanations involving staffing or missing
certifications are not identified causal effects.

### Current workbook fields and source-state caveats

Opened originals: [June 2026](https://cdss.ca.gov/Portals/9/IHSS/Data/IHSS_Program_Data-Jun2026.xlsx)
and [July 2026](https://cdss.ca.gov/Portals/9/IHSS/Data/IHSS_Program_Data-Jul2026.xlsx).
Read Data rows 4–61; row 62 is statewide and rows 64–68 are size-group
aggregates, not additional counties. Seven selected columns × 116 county-months
give **812 numeric cells**, with no blank, suppressed, or error cell in that
selection. This is not a claim that all workbook cells are clean: other
display sheets contain cached `#N/A` values.

| Raw column | Interpretation supported by workbook | Guardrail |
| --- | --- | --- |
| D | Authorized recipients, including eligible, presumptively eligible and leave statuses | Stock, not applications decided |
| GN | Outstanding reassessments | Display rate is `(D − GN) / D`; not completions divided by this month's due assessments |
| GO | Applications received in report month, regardless of status/outcome | Do not divide denial counts by GO as a cohort denial rate |
| GP, GQ, GR | Denial duration bands | Display says 0–45, 46–90, over 90 days; raw headers instead say 0–45, 46–91, 90+ |
| GS | Total denials used by display as denominator | Display title says previous 90 days; raw header says monthly denials |

The conflicting window/boundary labels remain unresolved. Do not pool report
months, reinterpret band endpoints, or derive a denial mean. The clock's
underlying start-date field and treatment of pauses are not documented in
these workbooks. All three bands sum to GS in each county row, and selected
county totals equal statewide totals in both files; arithmetic consistency
does not resolve the semantic conflict.

Zero denial denominators: Sierra/Trinity in June; Alpine/Sierra/Trinity in
July. Preserve these as zero counts with undefined timing shares, not zero-day
waits. The reassessment definition refers to an annual timeframe without
specifying all outstanding-case inclusion rules. The July 2025 change log
also says home-visit date was renamed assessment date. Historical field
comparability should be checked before extending the panel.

The [current index](https://www.cdss.ca.gov/inforesources/ihss/program-data)
links January–July 2026; the cached
[prior-year index](https://www.cdss.ca.gov/inforesources/cdss-programs/ihss/program-data/previous-years-data)
links monthly program workbooks for 2019–2025. Those additional workbooks
were **not** opened or counted as verified timing coverage. No additional
DHCS county application-duration series was verified in this bounded search.

## County process examples

**Los Angeles, large.** The [official recipient-facing page](https://dpss.lacounty.gov/en/senior-and-disabled/ihss.html)
supports this sequence: applicant submits SOC 295 by mail, phone or secure
fax → county social worker interviews and assesses service needs/hours →
licensed clinician supplies health certification before authorization →
county issues approval/denial and authorized hours → approved recipient
hires and supervises a caregiver, with PASC referral help available. The
caregiver is distinct from the county worker deciding eligibility/services.

The public [assessment policy, released June 18, 2026](https://my.dpss.lacounty.gov/public/en/home/epolicy/program/ihss/assessment/assessment-process.html)
documents backend work: CMIPS functional-ability/limitation entries,
justification of functional ranks and task-guideline exceptions, household
and other evidence, and use of a monthly due report to prioritize CFCO
reassessments. Non-CFCO and CFCO reassessment provisions differ. A referenced
internal template was not accessed. These are specified duties, not measured
worker minutes or observed compliance. Direct public download succeeded
after the web reader returned a cache miss.

**Alpine, tiny.** Its [official Adult Services page](https://alpinecountyca.gov/375/Adult-Services)
identifies County HHS as administrator, links the state application and
provides an eligibility/contact route. It does not publish a local timed
workflow or comparable backend detail. Do not fill that gap by copying LA's
implementation. The [state overview](https://www.cdss.ca.gov/in-home-supportive-services)
separately describes county social-worker assessment and authorization, but
is not evidence of Alpine-specific staffing or timing. The tiny historical
sample matters: B.3 Alpine 2019 has four new recipients; July 2026 Alpine
has zero reported denials, so no denial timing share is estimable.

## Backend burden and useful next material

Observed recipient waiting, caregiver service hours and county labor hours
are three different quantities. The retrieved material documents workflow
steps and stocks of unfinished reassessments, not handling time, contact
counts, rework, or application-level worker effort. The audit methodology
mentions county expense claims, a possible administrative-expenditure lead,
but no county labor-time dataset was retrieved.

A [March 18, 2026 LAO analysis](https://www.lao.ca.gov/Publications/Report/5166)
reports, based on county discussions, a possible tradeoff between prioritizing
CFCO reassessments and application processing. It cites applications taking
over 90 days increasing from 1,600 to 4,600 in the first six months of the
penalty policy. This is a useful hypothesis and documentary lead, **not** a
verified county panel or a causal estimate. Budget proposals in that dated
analysis are not treated as enacted current law.

## Artifacts, retrieval limits and remaining work

Raw originals, request caches, hashes and the full extracted source rows are
under `corpus/counties/raw/ihss_target/`. `ihss_source_extract.json` preserves
both historical tables (all 58 counties, both years, plus statewide rows)
and selected current cells with source row/column identifiers and states.
`extract_cached_sources.py` reproduces that source extraction without network,
imputation or model changes; it is not a test suite. `MANIFEST.json` catalogs
URLs, original-file hashes, fetch counts and the recovered reader failure.

Collection stopped at six searches/eighteen fetch actions. The remaining
scientific work is definition clarification for current denial windows/bands,
case-level clock/selection documentation, and a current approval-duration
source or an authorized data request. Historical means cannot validate
current county performance or within-county duration distributions.
