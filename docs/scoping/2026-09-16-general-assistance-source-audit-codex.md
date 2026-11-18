# General Assistance source audit — Codex handoff snapshot

As of 2026-09-16. Packet P4-GENERAL-ASSISTANCE; owner `codex-ga`.
Status: **partial source audit / handoff**, not P4 completion. The external
`ga-agent` owns the main report after a concurrent claim. This preserves the
first-pass source checks and adds independent cached-data QA; do not interpret
its 12-row snapshot as satisfying the 30-county acceptance check.

No further broad county searches or writes to the shared P4 report are made.
The 23 search queries and 33 fetch actions before handoff are cached and should
be reused against the packet budget, not restarted.

## Scope and evidence rules

County GA/GR is distinct from CalFresh, CalWORKs, SSI/SSP and county medical
assistance. A cash amount requires its household/employability category, period
and source; maximum entitlement is not an observed payment. A time limit on
receiving aid is not an application-processing time. `NV` means not verified by
this bounded pass, never no rule or no program. Omitted time limits are not
treated as unlimited eligibility. Undated live pages are observations at the
retrieval date, not legal certification of every current rule.

CDSS's [program overview](https://www.cdss.ca.gov/general-assistance) says
county boards fund and establish GA/GR, with eligibility and benefit levels
varying among the 58 counties. This motivates source-by-source comparison, but
does not establish that all differences reflect discretion rather than program
categories, legal constraints, or reporting dates.

All new retrievals are cached in `corpus/counties/raw/general_assistance/`.
Tool-response JSON preserves requests and extracted content; original files
are identified separately. The append-only scoping log records ownership,
searches, findings and failures. No shared covariate/model output is edited.

## Statewide compilation and timing verdict

The official [CDSS GR 237 collection](https://www.cdss.ca.gov/inforesources/research-and-data/disability-adult-programs-data-tables/gr-237)
publishes county caseload and expenditure workbooks. The
[report form](https://www.cdss.ca.gov/research/res/pdf/blankforms/GR237.pdf)
also includes a narrow SSI/SSP interim-assistance measure: disposition of SSA
checks within 1–10 working days of receipt. That is **not ordinary GA application
processing time**. The cached-data audit verifies the distinction below.

### Workbook QA

The [read-only script](../../corpus/counties/audit_gr237_codex.py) prints the
saved [machine audit](../../corpus/counties/raw/general_assistance/codex_gr237_source_audit.json),
including hashes, dictionary, release notes and anomaly coordinates. Reproduce
with `/Users/spangher/miniconda3/bin/python corpus/counties/audit_gr237_codex.py`
(that interpreter has openpyxl; no dependency was installed).

| CDSS source | County-month rows present | Entire rows blank | Suppressed cells | Other anomalies | Narrow timing pairs |
|---|---|---|---|---|---|
| [FY 2024–25](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/GR237FY24-25.xlsx) | 58 × 12 = 696, July 2024–June 2025 | 32 | 2,993 / 20,184 | Humboldt July: 29 `#REF!` cells; 3 literal `BLANK` tokens | 114 county-months / 15 counties |
| [FY 2025–26](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/GR237FY25-26.xlsx) | 58 × 8 = 464, only July 2025–February 2026 | 30 | 1,991 / 13,456 | Humboldt July: 29 `#REF!` cells; 2 literal `BLANK` tokens | 75 county-months / 13 counties |

Timing pairs require numeric Cell 19 > 0 and numeric Cell 20 between zero and
Cell 19; this is not independent validation of the reported counts. Reported
zeros, suppression, blanks and errors remain distinct. Release notes omit
**11** and **9** wholly blank county-months respectively. For example, July 2024
says all reporting despite Imperial's blank row; September 2025 says all
reporting despite Del Norte and Madera blanks. Both files show April 16, 2026
release dates. [FY 2024–25](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/GR237FY24-25.xlsx),
[FY 2025–26](https://www.cdss.ca.gov/Portals/9/Additional-Resources/Research-and-Data/DSSDS/Tables/GR237FY25-26.xlsx).

The [instructions](https://www.cdss.ca.gov/research/res/pdf/blankforms/GR237.pdf)
define Cell 19 as SSA checks disposed during the month, and Cell 20 as those
disposed within ten working days after county receipt. Disposition includes
cases where the entire check reimburses the county. This clock starts **after
SSA approval**, not at the county GA application. Cases added include
reapplications/restorations, not an applications-received denominator.
Administrative costs are excluded. The compilation therefore supports
caseload/expenditure analysis and a narrow reimbursement-disposition clock,
not an ordinary GA application-to-decision or agency-labor series.

## County inventory

Amounts are monthly maximums only where the source explicitly says so. Selected
eligibility criteria below are not exhaustive. `O` = official page/document
opened; `S` = official search text only; linked policy contents are not assumed
verified. `NV` in the timing column means no measured application timing was
verified from the cited sources, even if a service standard is published.

| County / official source | Program / grant category | Selected eligibility | Aid-receipt time limit | Application steps / timing evidence |
|---|---|---|---|---|
| Alameda — [GA hub](https://socialservices.alamedacountyca.gov/our-services/Work-and-Money/General-Assistance/index) O | GA loan; single maximum $336, couple $548 | Indigent adult/emancipated minor, legal county resident, no other means | [County regulations](https://www.alamedacountysocialservices.org/acssa-assets/PDF/GA-Policies/GENERAL%20ASSITANCE%20REGULATIONS%20Pursuant%20to%20Alameda%20County%20General%20Code-%20Title%207.%20General%20Assistance.pdf) S: employable 3 full months/12; temporary/permanent exemptions listed | Intake, verification, presumptive-eligibility and appeals policies linked; detailed steps/timing NV |
| Contra Costa — [EHSD GA](https://ehsd.org/aging-and-adult-services/general-assistance/) O | GA loan; employable single maximum $336, employable couple $454; other categories differ | Adult without dependent children; legal status; 15-day residence; income/property tests | Employable 90 days/12 months; disability exception stated | Office, BenefitsCal, phone or mail → interview → additional forms and reimbursement agreement; elapsed timing NV |
| Fresno — [County GR](https://www.fresnocountyca.gov/Departments/Social-Services/Assistance-Programs/General-Relief) O | GR; one-person maximum $245, two-person $400; shelter/income affect payment | County resident; adult with specified minor exceptions; legal status; resource limits | Employable at most 3 months/12; incapacity requires county-approved medical evidence of inability to work at least 30 days | County office/contact channel; work search or incapacity verification; measured timing NV |
| Kern — [County GA](https://www.kcdhs.org/services/apply-for-benefits/general-assistance) O | GA; amount NV | County residents without other support; single adults/couples without minor children | NV, not coded unlimited | In person, phone, mail or fax; application forms linked; long-term disability SSI advocacy; timing NV |
| Los Angeles — [DPSS GR](https://dpss.lacounty.gov/en/cash/gr.html) O | GR; maximum single $221, couple $375 | County residence; income and separate liquid/personal/vehicle/real-property tests | NV pending fact-sheet/ePolicy reading; proposed redesign not treated as adopted rule | BenefitsCal, office, fax/mail application; source's phone section offers mailed packet; measured timing NV |
| Orange — [SSA GR](https://ssa.ocgov.com/cash-calfresh/general-relief/what-general-relief) O | GR loan; employable, conditionally employable and incapacitated categories; amount NV | Adult without dependent children; county residence/legal status; income/property tests | NV | Effective May 1, 2026, page says BenefitsCal GR applications unavailable; phone, office or mail → mandatory interview (telephone possible); disability accommodations and SSI advocacy; measured timing NV |
| Sacramento — [DHA GA](https://ha.saccounty.gov/us/en/benefits/general_assistance.html) S; [Jan 2025 fact sheet](https://ha.saccounty.gov/benefits/GA/Documents/GA%20Fact%20Sheet%20January%202025.pdf) S, open failed | GA non-exempt single with no other unrelated adults: $326.64; household-sharing and disability-exempt schedules differ; stated schedule effective Jan 2020 | Adult without means; housing and net income affect eligibility/payment | Employable offered employment services: 3 months/90 days in 12; temporary/unemployable excluded | In-person SAWS 1 application; reasonable-accommodation request channels; measured timing NV |
| San Diego — [County GR](https://www.sandiegocounty.gov/hhsa/programs/ssp/general_relief/) O; [eligibility](https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/general_relief/eligibility_requirements.html) S | GR repayable aid; grant amount NV (income ceiling is not substituted) | Generally age 18–64; 15-day county residence; legal status; income/resource tests | NV | How-to-apply/benefits/program-guide links; completed job-training hours may offset repayment; measured timing NV |
| San Francisco — [CAAP eligibility](https://www.sfhsa.org/services/county-adult-assistance-programs-caap/check-caap-eligibility) O | CAAP umbrella; grant by subprogram NV; $714 published income ceiling is not labeled grant | Residency, income/property, education rules; page describes treatment/services condition for clients with substance-use disorder from Jan 2025 | NV | Online CAAP application includes CalFresh/Medi-Cal if absent; [September 2026 eligibility manual](https://www.sfhsa.org/reports-publications/handbooks-manuals) located, not yet read; measured timing NV |
| San Joaquin — [HSA benefits hub](https://www.sjchsa.org/Benefits-and-Assistance) O | GA loan for temporary housing/food need; amount NV | Individuals/families in temporary need; detailed criteria NV | NV | County BenefitsCal entry linked; dedicated GA procedure not yet read; timing NV; third-party $367 claim not adopted |
| Santa Clara — [Official GA information sheet](https://stgenssa.sccgov.org/debs/Forms/GA_62_en.pdf) O | GA; grant/category extraction pending | County residency/income/resources, employability distinctions in county policy | NV | [Application hub](https://ssa.santaclaracounty.gov/apply-public-benefits) S: BenefitsCal or office; [policy](https://stgenssa.sccgov.org/debs/program_handbooks/general_assistance/assets/01Policy/Policy.htm) S describes effective aid date, not measured decision time |
| Tulare — bounded query `Tulare County general assistance grant amount eligibility time limit official` | Official GA/GR applicant source not verified; unrelated emergency-management grants excluded | NV | NV | 211 lead retained only; no verified county process/timing claim |

## Litigation map

These are primary judicial opinions reproduced by legal/library hosts, not
county program pages or a comprehensive litigation registry.

| Case / directly affected county | Historical holding and coding limit |
|---|---|
| [Boehm v. County of Merced, 163 Cal.App.3d 447 (1985)](https://law.justia.com/cases/california/court-of-appeal/3d/163/447.html); [Boehm v. Superior Court, 178 Cal.App.3d 494 (1986)](https://law.justia.com/cases/california/court-of-appeal/3d/178/494.html) — **Merced** | Rejected grant reductions without adequate factual subsistence-needs assessment; the later opinion addresses necessities beyond food/shelter. Historical dollars are not current grants; subsequent law matters. |
| [Bell v. Board of Supervisors, 23 Cal.App.4th 1695 (1994)](https://law.justia.com/cases/california/court-of-appeal/4th/23/1695.html) — **Alameda** | Recognized the statutory safe-harbor alternative to a Boehm study and permissible in-kind/vendor benefits, but rejected deductions for shelter neither received nor realistically available. Litigation did not invalidate every challenged county rule or require all-cash aid. |
| [Hunt v. Superior Court, 21 Cal.4th 984 (1999)](https://scocal.stanford.edu/opinion/hunt-v-superior-court-guimbellot-31966/) — **Sacramento** | GA payment does not discharge the separate subsistence-medical-care duty; medical eligibility can extend beyond GA's financial threshold. This is principally a **medical-care eligibility** holding, not a current GA grant/time-limit schedule. San Diego and Tulare were amici, not the challenged county. |

The current [WIC §17000.5 text](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WIC&sectionNum=17000.5.)
uses a sufficient-aid framework tied to **the 1991 poverty guideline**, with
specified adjustments/in-kind rules—not simply 62% of today's poverty line.
It expressly separates the extent of the medical-care duty. This constrains
the packet's “maximal-discretion” label. Precedent and statewide amendments
also affect counties not directly sued; case selection does not identify a
clean treated/untreated causal contrast.

## Additional cached leads for the packet owner

No broad searches followed the collision. Existing batches 007–008 preserve:

- **Amador:** [code ch. 2.86](https://ecode360.com/46586631), indexed text;
  §2.86.210 lists $331 single / $541 two-person basic monthly grants with a 2023
  ordinance reference, work requirements and reimbursement agreement. The
  redline's obsolete $309 is not the current indexed amount.
- **Inyo:** [county public-assistance hub](https://www.inyocounty.us/aging-social-services/apply-public-assistance),
  indexed GA/GR section: temporary repayable aid, contact office to apply;
  amount/time limit NV.
- **Modoc:** [cash-program handout](https://www.co.modoc.ca.us/SocialServices/Cash%20Assistance%20Programs.pdf),
  indexed, **revised November 2021**, direct open failed. Three months for
  eligible employable adults, longer disability/SSI-pending branch, in-person
  application; amount/currentness NV.
- **Sierra:** [opened public-assistance page](https://sierracounty.ca.gov/306/Public-Assistance)
  names GA, three months/twelve unless exempt, and shared application channels;
  amount/exemption details NV.
- **Trinity:** [opened public-assistance hub](https://www.trinitycounty.ca.gov/251/Public-Assistance)
  describes other programs but does not establish a GA process. Omission is not
  program absence. Alpine, Del Norte and Lassen searches similarly leave
  specific GA rules unverified; unrelated CalWORKs/organizational grants were
  not substituted.

Sacramento's January 2025 PDF and old-host Modoc PDF returned generic web
internal errors, not verified 403 blocks. The CDSS XLSX web-click failure was
resolved using its exact official-index download link. County search-index
evidence is labeled separately from fully read documents.

## Recommendation and remaining work

**Provisional verdict:** GA is a useful local-rule/evidence-availability
contrast, but not yet the strongest standalone test of *rural* data poverty.
Official statewide counts/spending exist; a narrow clock exists but is sparse.
Ordinary application timing was not found in the inspected 29-field dictionary.
This partial source search does not establish a population gradient. A matched
size-stratified retrieval design must separate nonreporting, low counts,
suppression and retrieval failure before calling rural evidence absent.

For observed-timing validation, audited CalFresh sources are more directly
relevant. For rule variation, continue GA collection with household,
employability/disability categories and effective dates intact.

The external `ga-agent` retains P4 and its >=30-county deliverable. This appendix
is **not packet completion**: it preserves 12 initial rows, small-county leads,
three cases and the statewide-data QA. Remaining: complete county coverage,
read linked schedules/policies, resolve stale/index-only sources, and validate
any measured-timing claims. No shared-report edits followed the handoff. Own
usage stopped at **23 searches / 36 fetch actions**, including three final
text lookups on already opened case/statute pages; reuse these sources.
