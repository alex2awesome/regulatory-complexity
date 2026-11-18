# CalWORKs county counts and application-timing search

2026-09-16. Owner `codex`, N7-CALWORKS-TIMELINESS. Bounded retrieval complete;
four searches and ten downloads, at the four-search/ten-fetch cap. No tests,
production code or W2 program changes.

## Result: useful outcome counts, not current processing durations

The [CA 237 CW data page](https://www.cdss.ca.gov/inforesources/research-and-data/calworks-data-tables/ca-237-cw)
publishes county caseload workbooks. FY2025–26 and FY2026–27 originals are
saved with their embedded dictionaries. The latter currently contains July
2026, not a completed fiscal year.

The 149 dictionary fields are counts: applications, dispositions, month-end
pending stocks and caseload categories. **No elapsed-time or pending-age
field was found in these two workbooks.** A stock divided by that month's
approvals is not directly observed application waiting time. Historical
reporting requirements are being retained separately, not used to manufacture
current timeliness observations.

The [CA 255 CW page](https://www.cdss.ca.gov/inforesources/Data-Portal/Research-and-Data/CalWORKs-Data-Tables/CA-255-CW)
provides cash-grant denial and other nonapproval counts. Its two corresponding
workbooks are also saved. These distinguish reported reasons and family/status
groups, including income/resources, compliance, diversion, withdrawal and
unlocatable applicants. A recorded reason is not independently verified case
truth, and differences do not by themselves measure policy strictness.

## Actual workbook coverage

Counts below come from the downloaded files, not the landing-page inventory.
`Data_External` row 5 contains field IDs; dated rows begin at row 6. County
code `00` is retained separately as statewide. Embedded dictionaries are in
`DataDictionary 237` and `DataDictionary 255`.

| Workbook | County-month rows | Statewide rows | Measure fields | Numeric county cells | Suppressed county cells |
|---|---:|---:|---:|---:|---:|
| CA237CW FY2025–26 | 696 | 12 | 149 | 70,800 | 32,904 |
| CA237CW FY2026–27, July only | 58 | 1 | 149 | 5,955 | 2,687 |
| CA255CW FY2025–26 | 696 | 12 | 60 | 33,754 | 8,006 |
| CA255CW FY2026–27, July only | 58 | 1 | 60 | 2,848 | 632 |

Each report family covers 58 counties × 13 months, July 2025–July 2026, with
unique county-month keys. This is **754 county-month rows per report family**,
not independent samples across every scalar field. The families describe
overlapping applications; sums and components also overlap.

The 157,586 county measurement cells contain numeric values or `*`; no blank
or spreadsheet-error measurement cells were found in this snapshot. This does
not establish correctness. The `Release Summary` title contains `#N/A`, outside
the measurement grid. Releases are July 23, 2026 for FY2025–26 and August 21,
2026 for July 2026; all listed months say all counties reported.

There are 1,797 negative **county** values in CA237CW, all in adjustment
fields 3 and 24–28. They are not negative application counts and were not
clipped to zero. Explicit zeros remain distinct from suppression. The
publication's de-identification rule is retained; no hidden cell was
reconstructed or replaced with a guessed value.

The complete per-workbook coverage counts, source-state counts and embedded
field descriptions are preserved in
[WORKBOOK_INVENTORY.json](../../corpus/counties/raw/calworks_target/WORKBOOK_INVENTORY.json).
This is a source inventory, not a harmonized modeling dataset.

## Clock and denominator cautions

- Month-end pending is a stock, not an age distribution or elapsed-time mean.
  Applications received and dispositions in the same month are not one closed
  arrival cohort.
- CA237CW separates applications and restoration requests, and records transfers,
  adjustments and overlapping category totals. Match the reporting item before
  constructing a denominator or pooling with another program.
- “TANF timed-out” names a benefit-status category, not slow application processing.
- Diversion is a distinct denial reason; a cash-grant denial is not necessarily
  absence of all assistance. Withdrawal, failure to comply and inability to
  locate an applicant are separate reported categories, not interchangeable
  observations of abandonment.

## Historical timeliness reporting is a separate source

[ACL 93-29](https://www.cdss.ca.gov/lettersnotices/entres/getinfo/acl93/93-29.PDF)
documents historical AFDC reporting of 45-day application processing and
agency-attributed delay through ABCD 257. It includes restorations,
cancellations and withdrawals and describes assigning mixed-cause delays
without counting an incident twice. The letter and text derivative are cached.

This 1993 instruction is evidence of a historical measurement definition, not
a current CalWORKs compliance dataset or a check of present law. No current
county ABCD 257 outcome file was verified. Search results, reporting duties
and the current caseload workbooks must not be combined into a fictitious
modern timing series.

## Originals and remaining targets

Ten originals are in [the source cache](../../corpus/counties/raw/calworks_target/):
four workbooks, four index pages, the combined XLS reporting template and
the historical letter. [MANIFEST.json](../../corpus/counties/raw/calworks_target/MANIFEST.json)
records URLs, hashes, vintages and derivative status. The legacy XLS template
was saved but not parsed; the four XLSX dictionaries were read directly.
No macros were executed and no extra software was installed.

The index lists older annual workbooks back to FY2015–16; those were not
downloaded in this bounded pass. A current application-timeliness report or
an explicit account of its replacement remains the higher-priority next
target. No county contacts or records requests were sent.
