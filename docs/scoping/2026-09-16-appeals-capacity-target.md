# Assessment appeals: organizational capacity follow-up

2026-09-16, Codex, packet N9-APPEALS-CAPACITY. Retrieval continuation from
[N2 assessment appeals](2026-09-16-assessment-appeals-target.md), reusing its
official catalog, annual report and definitions. Budget used: no searches and
five distinct source fetches. Bounded collection complete; no model or test work.

## What is now retained

All five official API responses contain **696 unique county-year slots**, with
58 county names and 12 years per table. No next-page pointer was returned.
The browser tool could not open the first two API URLs; direct public downloads
succeeded and their JSON structure was inspected. Originals are retained under
[`raw/appeals_capacity_target/`](../../corpus/counties/raw/appeals_capacity_target/),
alongside field coverage, source-quality flags, an inventory and
[hashed manifest](../../corpus/counties/raw/appeals_capacity_target/SOURCE_MANIFEST.json).
Ten retained files are cataloged, including five originals; the previously
cached catalog/report dependencies are separately hashed without re-downloading.

| Source | Raw year labels | Useful observations | Latest nonnull coverage |
|---|---|---|---|
| [J: boards and hearing officers](https://www.boe.ca.gov/dataportal/api/odata/Appeals_Boards_and_Hearing_Officers) | FY2013–14 to FY2024–25 | Supervisor-board dual role; assessment appeal board count; hearing officer count | 58 Yes/No strings, **not 58 verified responses**; 37 board counts; 40 officer counts |
| [C: temporary positions](https://www.boe.ca.gov/dataportal/api/odata/Budgeted_Temporary_Positions) | FY2013–14 to FY2024–25 | Seven assessor staffing categories and total budgeted temporary positions | 17–27 numeric values per role; 33 numeric totals |
| [F: property transfers](https://www.boe.ca.gov/dataportal/api/odata/Real_Property_Workload_Data_Transfers) | AY2014–15 to AY2025–26 | Recorded documents and transfers by property class | 48 document counts; 47 counts for each transfer field |
| [F: new construction](https://www.boe.ca.gov/dataportal/api/odata/Real_Property_Workload_Data_New_Construction) | AY2014–15 to AY2025–26 | Permit-issuing source count; permits received by assessor; new assessments | 48 source counts, 47 received-permit counts, 46 new-assessment counts |
| [I: business-property audits](https://www.boe.ca.gov/dataportal/api/odata/Business_Property_Workload_Data_Audits) | FY2013–14 to FY2024–25 | Audit pools/completions, reported net value effect, audits prepared for other counties | 48 completed-audit totals; other fields have 58 numbers, including numbers for documented nonreporters |

The original JSON preserves field names, nulls and numbers. The derived files
are `latest_field_coverage.csv` (26 fields), `data_quality_flags.csv` (68 flags),
and `INVENTORY.json` (years, fields, coverage, hashes and cautions). No missing
values were filled, and no questionable totals were silently recomputed.

## What changes our interpretation

### Organizational evidence is real, but the unit is not simply agency count

Los Angeles's latest Table J row reports **11 appeal boards and 12 hearing
officers**. Del Norte reports the supervisor-board role but no separate numeric
appeal-board count. A county with null separate-board count is not thereby a
county with no appeals authority. These are structures and roles, not an
enumeration of independent agencies or steps per applicant.

The [2026 annual report](https://www.boe.ca.gov/proptaxes/pdf/lta26017.pdf)
also names Del Norte's six permit-reporting sources: county building and
environmental health departments, Crescent City, HCD, state health, and the
Coastal Commission. Its Table F source count is correspondingly six. Thus
`JurisdictionsIssuingBuildingPermits` is not safely interchangeable with
municipality count; it can capture multiple departments and state entities.
This is relevant to the proposed actor hierarchy, but does not establish that
all six actors participate in every case.

Temporary staff are **budgeted positions**, not observed filled capacity or
worker hours. The report's Monterey narrative explicitly describes vacancies
and hiring constraints in the auditor-appraiser team. That illustrates why
authorized positions and actual labor supply must remain separate variables.

### Do not join fiscal and assessment years by identical numbers

The annual report says FY2024–25 budget, staffing and workload produced the
AY2025–26 assessment roll. That explains a one-year difference in these latest
table labels. Keep the raw `FiscalYearFrom/To` and `AssessmentYearFrom/To`
fields and an explicit period map, not an undocumented same-year join. This
pass did not recheck all twelve questionnaires for historical definition changes.
New-construction assessment counts are also not APR building-permit case counts.

## Source-quality checks

1. **Numeric/boolean-looking defaults do not establish reporting.** The annual
   report names ten FY2024–25 nonreporters: Alpine, Glenn, Imperial, Lake,
   Lassen, Marin, Mendocino, Plumas, Santa Barbara and Trinity. All ten have
   `No` in Table J's supervisor-board field but null board/officer counts. Their
   Table I audit components contain zeros, while completed-audit totals are
   null and another audit-count field remains nonzero. Preserve these raw
   values, but do not infer no board role or no audits from them. The exact
   defaulting/provenance mechanism was not verified.
2. **Monterey has a corroborated source contradiction.** FY2024–25 audit
   components are **9 + 13**, the total field is **0**, and the report's
   narrative (PDF p.17, visually checked) says **22** audits were completed.
   Retain and flag all three
   representations. It is not an extraction error we can resolve by pretending
   the published zero was the intended count.
3. **There are additional arithmetic discrepancies, not all proven errors.**
   Across the 12-year audit table, 46 rows with numeric components and totals
   fail simple addition (including Monterey). Most are in the earliest two
   vintages, so an older definition or coverage difference needs investigation
   before enforcing that identity. Latest Modoc is 1 + 2 versus total 2.
   Transfer components differ from their totals in Mono AY2023–24 (924 versus
   1,556) and Tulare AY2024–25 (6,522 versus 6,536). The flags preserve the
   original pieces; no correction is asserted for these unexplained cases.
4. **Negative value effects are not negative event counts.** The audit table has
   69 negative values in `NetResultAuditsCompleted`, a value-effect field,
   not a count of completed audits. None of the retrieved count fields has a
   negative numeric value. The annual report's Table I commentary describes
   dollar effects and warns that their year-to-year changes can be large.
5. **Null temporary staffing is not necessarily zero.** Twenty-five counties
   have all eight temporary-position fields null in the latest year, including
   fifteen outside the ten documented nonreporters. There are 253 historical
   rows with every staffing component and total numeric; their sums match
   within 0.01. This confirms those particular arithmetic relationships, not
   the meaning of missing entries or actual filled staffing.

## Use and remaining gaps

These five tables expand the material available for organizational role,
task-mix and workload modeling and can join the N2 budget/permanent-position
and appeals-outcome tables with explicit period/provenance rules. They do not
provide case timestamps, employee task logs, applicant effort, or intrinsic
agency completion times. A hierarchy still needs a design that separates
agency effects from task mix, staffing, case selection and reporting methods.

Remaining retrieval priorities are source questionnaires/field definitions for
the older audit vintages and public case-level appeal timing records. They were
not fetched beyond this five-source budget. The 696-row structure must not be
advertised as complete numeric reporting, and no externally reported source
defects were repaired during this pass.
