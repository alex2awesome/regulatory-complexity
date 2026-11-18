# Assessment appeals: new outcome and agency-resource material

2026-09-16. Owner `codex`; target `N2-ASSESSMENT-APPEALS`. Source retrieval,
not a new model or test suite. Four searches and fifteen public-source fetches;
all originals and text derivatives are in
[`raw/assessment_appeals_target/`](../../corpus/counties/raw/assessment_appeals_target/).
The [manifest](../../corpus/counties/raw/assessment_appeals_target/MANIFEST.json)
records URLs, hashes, bytes, table fields, year coverage and missingness.

## What this adds

**A statewide county appeals panel does exist.** The BOE's *Report on Budget,
Personnel, Appeals and Roll Data* is separate from its agency annual report,
`pub306.pdf`. The latter's state-assessed docket does not establish whether
county appeals data are available. The [report index](https://www.boe.ca.gov/proptaxes/reports.htm)
and [budget/staffing resources](https://www.boe.ca.gov/proptaxes/budget-staffing/resources.htm)
lead to the actual county material.

Four downloaded JSON tables each contain **696 unique county-year rows: 58
counties × 12 years, 2013–14 through 2024–25**, with no next-page link in the
returned response. This is structural coverage, **not complete measurements**.
The [April 22, 2026 report, LTA 2026/017](https://www.boe.ca.gov/proptaxes/pdf/lta26017.pdf)
states that only 48 counties supplied the latest fiscal year's data in time.
The prior [LTA 2025/003](https://www.boe.ca.gov/proptaxes/pdf/lta25003.pdf)
is also cached for subsequent vintage/definition checks.

| Downloaded table | Useful variables | Local original |
|---|---|---|
| [K: appeal distribution](https://www.boe.ca.gov/dataportal/api/odata/Distribution_of_Assessment_Appeals_by_Property_Types) | New filings by property type; prior-year filings; opening carryover; total to resolve | `boe_appeals_distribution.json` |
| [L: appeals activity](https://www.boe.ca.gov/dataportal/api/odata/Assessment_Appeals_Activity) | Withdrawals with/without/unknown value change; no-shows; invalid cases; stipulations; heard outcomes; resolved total; closing carryover | `boe_appeals_activity.json` |
| [B: budgeted permanent positions](https://www.boe.ca.gov/dataportal/api/odata/Budgeted_Permanent_Positions) | Managers, certified real/business appraisers, mapping, computing, other professional and support positions | `boe_permanent_positions.json` |
| [A: gross/net budget](https://www.boe.ca.gov/dataportal/api/odata/Gross_and_Net_Budget) | Assessor gross and net budgets; prior-year net budget; reported change | `boe_gross_net_budget.json` |

The [public catalog API](https://www.boe.ca.gov/dataportal/api/odata/catalog)
is cached too. Its `ApiCall` field supplies the exact endpoint names used by the
public table viewer. The report links additional tables not downloaded in this
bounded pass, including [J: boards and hearing officers](https://www.boe.ca.gov/dataportal/dataset.htm?url=PropTaxAppealsBoardsHearingOfficers),
temporary positions, budget components, appraisal workload and property claims.

## What these observations do—and do not—measure

These tables support **outcome, workload, organizational-resource and reporting
comparisons**. They do not contain application/decision timestamps, mean elapsed
days, or worker handling hours. Do not turn the two-year legal hearing/decision
rule into an observed duration, infer that every carryover is overdue, or estimate
mean waiting time from a single annual backlog/throughput ratio without additional
cohort and stationarity assumptions.

The [BOE process description](https://www.boe.ca.gov/proptaxes/assessment-appeals/)
describes application to the clerk, board hearing and determination, and the
statutory two-year rule with exceptions. These are normative process facts, not
measurements of compliance. An informal Assessor review, a formal assessment
appeal and subsequent judicial review are different routes.

Budgeted positions are **not filled positions or observed FTE effort**, and the
Assessor is not the whole appeals board/clerk operation. These department-level
resources are nevertheless more directly relevant than all-local-government
employment. The report asks combined assessor/recorder/clerk offices to report
only assessor functions; its notes show that separation is not always easy.

The API calls Table L's year fields `AssessmentYearFrom/To`, while the report
describes fiscal-year activity. Those original field names are retained.
Underlying questionnaires and period rules need checking before constructing
cross-table flow identities or harmonizing older vintages. “Rural” in Table K
is a **property category**, not a county rurality classification.

## Missingness and source-quality evidence retained

The ten latest-year nonreporters listed in LTA 2026/017 are **Alpine, Glenn,
Imperial, Lake, Lassen, Marin, Mendocino, Plumas, Santa Barbara and Trinity**.
Their Table L outcome and Table B staffing measure rows are entirely null.
Table K can still contain a prior-year count, and Table A can contain a
prior-year budget; a row with one nonnull field is not proof of current reporting.

Latest-year coverage differs by field:

- Appeals resolved and closing carryover: 48 numeric county totals each.
- Current gross/net budget: 48 counties each.
- Individual staffing categories: 45–48 counties.
- Total new filings, opening carryover and total to resolve: 47 counties each.
  Sierra reports one residential filing but its total-filings field is null.
- Sierra's closing carryover is **−2**, an invalid raw count. It is preserved,
  not corrected to zero or used as a burden outcome.

The report's appendix supplies unusually useful evidence about **why** data
are missing or difficult to compare:

- **Orange:** certain withdrawal/value-change fields are not tracked. Published
  zeros must not automatically be interpreted as verified absence of that event.
- **San Luis Obispo:** the Assessor receives only applications accepted by the
  clerk, so an upstream invalid-application field cannot be fully observed there.
- **Yuba:** a blank often means the information is unavailable; the reporting
  field does not accept an explanatory text comment.
- **Tuolumne:** a software change allowed assessor salary/benefit reporting to be
  separated from recorder costs more accurately than in prior years.
- **Monterey:** the narrative connects vacancies in its auditor-appraiser team
  with missed mandatory appraisal-audit workload. This concerns assessor audits,
  not necessarily appeal waiting time, and is an agency explanation, not a causal
  estimate.

These are actual documented reporting mechanisms. They can inform future
observation-model assumptions without pretending the aggregate counts identify
all those mechanisms on their own. Raw nulls, zeros and negative values remain
unchanged in the JSON originals.

## Small- and large-county source examples

**Alpine:** the [September 2025 assessment-practices survey](https://www.boe.ca.gov/proptaxes/pdf/02apsr0925.pdf)
contains five fiscal years of assessor budgets, permanent positions and appeal
filings. In 2022–23 it reports a $463,838 gross budget, three budgeted permanent
positions (Assessor, real-property appraiser and cadastral draft person), and
five appeals filed. It records source references to the same BOE tables. This
is historical department evidence despite Alpine's missing latest-year panel
fields; a current missing row does not imply no department or no earlier data.

**Los Angeles:** the [September 2022 survey](https://www.boe.ca.gov/proptaxes/pdf/19apsr0922.pdf)
reports, for 2019–20, $236,853,312 gross budget, 1,398 budgeted permanent positions
and 18,335 appeals filed, with role breakdowns and operational recommendations.
Its current hosted PDF includes later-updated source-reference text, so retain
both the report's nominal date and retrieval hash. Do not compare its old fiscal
year to Alpine's newer one as a controlled staffing/performance contrast.

The downloaded latest tables also report Los Angeles's 2024–25 new filings
(17,600), resolutions (10,749), and closing carryover (25,967). These are
different annual stocks/flows, not one application cohort or an elapsed-time
distribution. They should not be used to derive a simple success rate.

## Recommendation and remaining material

Retain assessment appeals as a stronger **agency-resource and outcome** target
than P6's original annual-report search suggested. It is not yet a strong
individual elapsed-time benchmark. This retrieval does not override another
agent's program-selection decision; it supplies the missing source family for
that decision to consider.

Next useful retrievals, not performed under this target's exhausted fetch
budget: underlying questionnaire/field definitions; Table J organizational
structure; county clerk hearing calendars, case status or dated decisions;
and time-extension/waiver fields. These would connect formal step variation
to actual case timing. No new statistical model, unit tests, imputation or
reserved-world work was performed for this target.
