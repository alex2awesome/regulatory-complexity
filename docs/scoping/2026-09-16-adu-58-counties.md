# ADU process documents: California's 58 counties

As of 2026-09-16. Packet P3-ADU-PROCESS-DOCS; owner `codex-adu`.
Status: bounded scoping pass complete; acceptance checks met, with verification
gaps retained below. Scope is the county government's
unincorporated permitting process. City material is not counted as county
coverage; San Francisco is a consolidated city and county and needs a distinct
scope flag rather than an invented unincorporated process.

Coverage: **58 unique county rows** match the existing county roster. Of the
57 ordinary county rows, **36** have an opened/read official ADU source, **10**
have an official source located only in search, and **11** have an explicit
not-verified applicant-page result. Thus **46** have a located county ADU
page/document, not 46 fully verified procedures. San Francisco has a separately
flagged, opened city/county source. Code-only and dated-handout rows count as
documents, not dedicated applicant hubs. All three packet acceptance checks
pass: the minimum 45-row threshold, located HCD findings evidence, and three
source-supported sketches.

## Evidence and limits

This inventory separates an official page located in search from a page opened
and read, a linked document from its contents, and a stated legal deadline from
observed elapsed processing time. `NV` means **not verified by the specified
searches**, never that a program or document does not exist. Document dates are
retained where visible. A 2022 handout is historical evidence, not assurance of
2026 compliance. The packet's maximum is 60 searches, 200 fetches and 180 minutes.

The existing [AB 2533 sources](../../corpus/ab2533/SOURCES.md) and
[declared processes](../../corpus/ab2533/process/declared_processes.json) are
reused. They cover San Mateo County and the cities of Hayward, El Cerrito and
Lafayette. The three cities are useful extension cases but do not fill county
rows. The previously cached Hayward HCD review letter is also retained without
redownloading it.

Tool retrievals, requests and failures are cached under
`corpus/counties/raw/adu_docs/`; these JSON files preserve the retrieved tool
content, not necessarily original HTML or PDF bytes. Raw downloads, where made,
are identified separately. The live claim/search/finding log is
`docs/scoping/FINDINGS.jsonl`. Permit vendor and code-host observations are in
[a separate P3 CSV](../../corpus/counties/adu_portal_code_observations.csv) for
reviewed merging; the shared covariate CSV is untouched.

The CSV has 58 rows, with **10 vendor observations, 11 portal-platform
observations and 22 code-host observations**. Shasta has only a platform
observation, not a verified vendor company. Some vendors are inferred from an
officially linked hostname; code observations mix named publishing services
with two county-hosted code/document indexes. Evidence levels and these
qualifications travel with each value; do not merge them as equally verified
categorical covariates. Empty fields remain unknown.

The [cache manifest](../../corpus/counties/raw/adu_docs/MANIFEST.json) records
coverage classifications and URLs, byte counts and SHA-256 for 11 original
downloads. There are 23 tool-request caches. Budget used: **60 searches** and
**97 fetch actions** (66 opens + 13 clicks + 7 text finds + 11 raw downloads),
within the 60/200 limits. This was a bounded approximately 25-minute pass,
not a source-exhaustion claim.

### Retrieval failures retained

Three explicit 403 results were observed: [Amador Planning](https://www.amadorcounty.gov/departments/planning),
[Fresno ADUs](https://www.fresnocountyca.gov/Departments/Public-Works-and-Planning/divisions-of-public-works-and-planning/development-services-division/building-safety/Accessory-Dwelling-Unit-ADU),
and [Shasta plans](https://www.shastacounty.gov/planning/page/shasta-county-pre-approved-adu-plans).
[Calaveras](https://planning.calaverasgov.us/Accessory-Dwelling-Units) returned a
fetch timeout (tool status 400). Generic internal failures affected the Amador
handout, Madera building hub, San Benito residential hub, San Bernardino handout,
Sonoma ordinance and HCD sitemap. Their URLs are retained in the county rows
and request caches. The [Modoc publisher page](https://library.municode.com/ca/modoc_county/codes/code_of_ordinances?nodeId=TIT18ZO_CH18.100SPUS)
and HCD dashboard yielded no readable text. These are source-specific retrieval
outcomes, not findings that those governments lack documents; generic failures
are not relabeled as access-control blocks. No county-level block rate is
estimated from these heterogeneous/repeated requests.

## HCD ordinance-review evidence

HCD's [Technical Assistance and Enforcement Letters Dashboard](https://www.hcd.ca.gov/hau/enforcement-letters)
is the official index. It identifies jurisdiction, date, housing law and letter
type, with PDF links where available. Some entries instead ask readers to
contact HCD; those are discovery records, not downloaded letters. The dashboard
includes multiple housing laws, so ADU findings letters require filtering by
both law and letter type. The embedded Power BI dashboard returned a JavaScript
shell without readable records; the sitemap also failed. No exhaustive count
can be inferred from this retrieval.

The verified lower bound is **one county with a findings letter (Kings)**, plus
**two other counties with technical-assistance letters (Merced, Solano)**.
These are different letter types, not three equivalent findings of violation.
All three PDFs were opened and downloaded to the raw cache.

| County | HCD letter | What the dated evidence establishes |
|---|---|---|
| Kings | [Findings, 2024-09-16](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/kings-county-adu-findings-091624.pdf) | HCD identified noncompliant provisions in ordinance 668-2-23, including conversion setbacks and JADU requirements. This does not establish unresolved violations in 2026. |
| Merced | [Technical assistance, 2025-10-08](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/merced-county-adu-ta-100825.pdf) | HCD's most recent ordinance on file was from 2020 and might be outdated; it requested newer material if its records were incomplete. The county code now references a 2026 amendment. |
| Solano | [Technical assistance, 2025-12-05](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/solano-county-adu-ta-12052025.pdf) | Also concerns an older ordinance on file, possible outdated provisions and statutory changes; not a verified present-day enforcement outcome. |

Ventura's [county hub](https://rma.venturacounty.gov/accessory-dwelling-units/)
reports HCD compliance confirmation in January 2025, but the underlying letter
was not verified and is excluded from the count. The cached Hayward review is
a **city** letter and is also excluded. HCD's [ordinance guidance](https://www.hcd.ca.gov/building-standards/adu/ordinance)
explains the review/submission mechanism and that a local ADU ordinance is not
mandatory; missing local ordinances therefore cannot be coded automatically as
noncompliance.

## County inventory

`O` = opened/read; `S` = official search-index result only; `L` = document linked
from the cited official hub, contents not separately checked; `NV` = not verified
by the county-name ADU search and linked-page inspection used in this pass. A
hub citation supports the linked resources in its row, not their substantive
accuracy. Where a dedicated ADU hub was not found, an official handout qualifies
as an ADU document but is labeled as such.

| County | Official ADU source / access | Ordinance | Checklist / handout | Pre-approved plans | AB 2533 / legalization | Stated timing, not observed |
|---|---|---|---|---|---|---|
| Alameda | [County hub](https://www.alamedacountyca.gov/cda/planning/landuseprojects/secondary-units.htm) O | Ordinance L, explicitly archived | Process graphic L; older handout archived | NV | NV | NV |
| Alpine | [County handout, Feb 2022](https://www.alpinecountyca.gov/DocumentCenter/View/4389/Accessory-Dwelling-Unit--Information-Sheet-2022_Final) O | Says ch. 18.69 then conflicted with state law; historical statement | Same PDF | NV | NV | 60 days after complete application with existing primary dwelling, historical legal-clock statement |
| Amador | [County process handout](https://www.amadorcounty.gov/home/showpublisheddocument/51660/638349607939670000) S; planning hub 403 | [Ch. 19.72](https://ecode360.com/46592403) S; lists July 2026 amendment | [County guidebook](https://www.amadorcounty.gov/home/showpublisheddocument/51658/638349607934370000) S | NV | NV | NV |
| Butte | [County ADU program](https://www.buttecounty.net/2084/Accessory-Dwelling-Unit-ADU-Program) O | NV | DBP-30 / DBP-33 L | County no-cost and designer plans; site review still required | NV | NV |
| Calaveras | [County ADU hub](https://planning.calaverasgov.us/Accessory-Dwelling-Units) S; open timed out | Ch. 17.66 L | [Development checklist, Aug 2024](https://building.calaverasgov.us/Portals/Building/Documents/Plan%20Submittal%20Checklists/Single%20Family%20and%20Accessory%20Dwelling%20Developmental%20Packet.pdf) S | NV | NV | NV |
| Colusa | Not verified by `Colusa County accessory dwelling unit ADU official`; results included city page and old county housing documents | NV | NV | NV | NV | NV |
| Contra Costa | [County ADU hub](https://www.contracosta.ca.gov/ADU) O | Ch. 82-24 on Municode L | Separate planning and building checklists L | PADU program and approved-plan catalog | Pre-2020 evidence and substandard-conditions checklist on hub; optional contractor inspection | NV |
| Del Norte | [County ADU hub](https://www.co.del-norte.ca.us/departments/Planning/AccessoryUnits) O | Non-coastal ordinance L; municipalcodeonline host | County brochure L | [County program](https://www.co.del-norte.ca.us/departments/BuildingInspection/Pre-ApprovedADUProgram) S | NV | NV |
| El Dorado | [County ADU hub](https://www.eldoradocounty.ca.gov/Land-Use/Planning-and-Building/Building-Division/ADU) O | Zoning ordinance L | Permit/site checklists and flow chart L | Unincorporated plans gallery and pre-reviewed plans | AB 2533 guide and affidavit L | Review Timing Requirements L; duration not yet extracted |
| Fresno | [County ADU hub](https://www.fresnocountyca.gov/Departments/Public-Works-and-Planning/divisions-of-public-works-and-planning/development-services-division/building-safety/Accessory-Dwelling-Unit-ADU) S | NV | Sample plan sets linked | County plans free; explicitly unincorporated area | NV | NV |
| Glenn | Not verified by `Glenn County accessory dwelling unit ADU official` | NV | NV | NV | NV | NV |
| Humboldt | [County ADU permit hub](https://www.humboldtgov.org/3690/Accessory-Dwelling-Unit-ADU) O | Inland/coastal ordinances L; [county ordinance archive](https://humboldtgov.org/2448/2019-Housing-Element) S | Type-specific minimum documents L | NV | NV | NV |
| Imperial | Dedicated county ADU hub not verified by `Imperial County accessory dwelling unit ADU official`; city result excluded | [Official state notice of county's 2024 ordinance revisions](https://ceqanet.lci.ca.gov/2024060948) S; adoption text NV | NV | NV | NV | NV |
| Inyo | [County ADU hub](https://www.inyocounty.us/housingservicesandsupport) O | [County code ch. 18.78](https://ecode360.com/44466603) S | [Guide, Feb 2026](https://www.inyocounty.us/sites/default/files/2026-03/ADU%20Guideline%20-%202.24.2026%20V4_0.pdf) S | County engineered plan sets L; site work remains | NV | NV |
| Kern | County ADU applicant hub not verified by `Kern County accessory dwelling unit ADU official` | Ch. 19.90 returned on third-party mirror; adopted official source NV | NV | NV | NV | NV |
| Kings | County ADU applicant hub not verified by `Kings County accessory dwelling unit ADU official`; King County WA results excluded | [HCD county findings, Sept 2024](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/kings-county-adu-findings-091624.pdf) O; not the county's applicant page | NV | NV | NV | NV |
| Lake | Dedicated ADU page not verified by `Lake County California accessory dwelling unit ADU official`; [zoning permits hub](https://lakecountyca.gov/577/Zoning-Permits) O does not establish an ADU program | NV | NV | NV | NV | NV |
| Lassen | Not verified by `Lassen County California accessory dwelling unit ADU official` | NV | NV | NV | NV | NV |
| Los Angeles | [County ADU hub](https://planning.lacounty.gov/planning-permits/accessory-dwelling-units/) O | [Aug 2025 staff memo](https://planning.lacounty.gov/wp-content/uploads/2025/08/ADU-OrdinanceAmendment-Certified-Ordinance.pdf) O reports July adoption / Aug effectiveness; memo is not full ordinance text | [County step guide, Apr 2023](https://planning.lacounty.gov/wp-content/uploads/2022/10/adu_step-by-step-guide.pdf) O | County/free and private designer catalogs L | NV | [Dec 2025 memo](https://planning.lacounty.gov/wp-content/uploads/2025/12/ADU_memo_sb543_ab1154.pdf) O: 15 business-day completeness / 60 calendar-day decision from complete receipt, effective Jan 2026; supersedes contrary older guidance |
| Madera | [County building hub](https://www.maderacounty.com/government/community-economic-development-department/divisions/building-division) S; open failed | [County guide](https://www.maderacounty.com/home/showpublisheddocument/41105/638622670190300000) references ch. 18.50.020; city code result excluded | Same guide S | County hub advertises unincorporated pre-approved plans | NV | NV |
| Marin | [County ADU hub](https://www.marincounty.gov/departments/cda/housing-and-grants/creating-housing/accessory-dwelling-units-adus?lang=en) O | §22.32.120, Municode L | [ADU fact sheet](https://www.marincounty.org/-/media/files/departments/cd/planning/currentplanning/planning-applications/adu/adu-fact-sheetv01051021.pdf) S | NV | [AB 2533 inspection checklist landing page, June 2025](https://www.marincounty.gov/node/22961) O; PDF L | NV |
| Mariposa | [County ADU hub](https://ca-mariposacounty.civicplus.com/2899/Accessory-Dwelling-Units-ADUs) O | Page says state law used without local ADU ordinance; links an update; current adoption independently NV | County brochure on hub; [handouts](https://www.mariposacounty.gov/861/Informational-Handouts) S | [Plans gallery program](https://www.mariposacounty.org/2939/ADU-Pre-Approved-Plans) S | NV | NV |
| Mendocino | [County ADU hub](https://www.mendocinocounty.gov/departments/planning-building-services/accessory-dwelling-units) O | [Coastal ch. 20.458](https://library.municode.com/ca/mendocino_county/codes/code_of_ordinances?nodeId=MECOCO_TIT20ZOOR_DIVIIMECOCOZOCO_CH20.458ACDWUN) S | [County checklist](https://www.mendocinocounty.gov/home/showpublisheddocument/73116/638896636878600000) S | NV | NV | NV |
| Merced | Dedicated hub NV; [county code ch. 18.62](https://ecode360.com/43025247) O explicitly unincorporated | Same; references June 2026 amendment and state-law precedence | NV | NV | NV | NV |
| Modoc | Dedicated hub NV; [county code §18.100.070](https://library.municode.com/ca/modoc_county/codes/code_of_ordinances?nodeId=TIT18ZO_CH18.100SPUS) S; open has no text | Same | NV | NV | NV | Search excerpt states 15 business days to determine completeness; legal clock |
| Mono | [County prescriptive designs](https://monocounty.ca.gov/adu-prescriptive-designs-2) O | Chapter 16 update material found; current adoption NV | [ADU submittal checklist](https://www.monocounty.ca.gov/sites/default/files/fileattachments/building_division/page/32699/adu_submittal_checklist_and_development_standards.pdf) S | Final prescriptive designs L | NV | NV |
| Monterey | [County QuickStart guide](https://www.countyofmonterey.gov/home/showpublisheddocument/124764/639052031505970000) O | [County ordinance-update hub](https://www.countyofmonterey.gov/government/departments-a-h/housing-community-development/planning-services/advance-planning/ordinances-plans-under-development/accessory-dwelling-unit-adu-and-junior-accessory-dwelling-unit-jadu-update-ref210034-coastal-zoning-area) S; coast/inland distinguished | Same guide | Guide advertises county detached floor plans | NV | NV |
| Napa | [County ADU hub](https://www.napacounty.gov/2750/Accessory-Dwelling-Units-ADUs) O | County code references on hub | Residential submittal checklist L; FAQs read | NV | Eligibility, optional third-party inspection, county inspection/corrections described on hub | Published 15 business-day completeness / 60-day decision claims; also conditions completeness on payment. Not elapsed-time evidence or an independent legal conclusion |
| Nevada | [County ADU hub](https://nevadacountyca.gov/3228/Accessory-Dwelling-Units-ADUs) O | 2025 ADU Policy L | County guidebook and FAQ L | NV | NV | NV |
| Orange | [OC Development Services ADU hub](https://pwds.oc.gov/service-areas/oc-development-services/planning-development/accessory-dwelling-units) O | §7-9-90, Municode L | Fact sheet and building plan-check process L | County pre-approved plans L | AB 2533 Safe ADU/JADU Legalization Program L | NV |
| Placer | [County ADU hub](https://www.placer.ca.gov/5670/ADU) O | [Approval process, June 2026](https://www.placer.ca.gov/10886/ADU-Approval-Process-Standards) S says updated ordinance, signed copy placeholder | [FAQs](https://www.placer.ca.gov/DocumentCenter/View/65355/ADU-FAQs?bidId=) S | County pre-reviewed plans advertised | NV | NV |
| Plumas | [County ADU hub](https://plumascounty.us/3285/Accessory-Dwelling-Units-ADU-Pre-Approve) O | Ordinance L | [Idea book, Mar 2024](https://www.plumascounty.us/DocumentCenter/View/49279/PlumasADU_IdeaBook_FINAL_rev-3-28-24_reduced?bidId=) S | Pre-approved program on hub | NV | NV |
| Riverside | Not verified by `Riverside County California accessory dwelling unit ADU official`; City of Riverside results excluded | NV | NV | NV | NV | NV |
| Sacramento | Not verified by `Sacramento County California accessory dwelling unit ADU official`; broadcast result not substituted for official procedure | NV | NV | NV | NV | NV |
| San Benito | [County residential applications hub](https://www.sanbenitocountyca.gov/departments/resource-management-agency/building-and-code-enforcement-division/building-services-forms-and-applications/residential-projects) S; open failed | [County §25.08.002](https://codelibrary.amlegal.com/codes/sanbenitocounty/latest/sanbenito_ca/0-0-0-37529) S | ADU submittal requirements L; [county handbook](https://www.sanbenitocountyca.gov/home/showpublisheddocument/11082/638231100063270000) S | NV | NV | NV |
| San Bernardino | [County handout, Feb 2026](https://lus.sbcounty.gov/wp-content/uploads/sites/48/LUS-ADU-Handout-2.13.2026.pdf) S; open failed | Draft amendment linked from [county Planning](https://lus.sbcounty.gov/planning-home/), adoption NV | Same handout | [County Building](https://lus.sbcounty.gov/building-safety-home/) S advertises pre-approved plans | NV | NV |
| San Diego | [County ADU hub](https://www.sandiegocounty.gov/content/sdc/pds/bldg/adu.html.html) O; explicitly unincorporated | [County zoning hub](https://www.sandiegocounty.gov/content/sdc/pds/zoning.html.html) S | County handbook L | NV | NV | NV |
| San Francisco | **Scope exception:** consolidated City and County; [SF Planning bulletin, June 2026](https://sfplanning.org/es/node/1005) O, not a separate unincorporated county process | Planning Code §§207.1/207.2 L | Bulletin | NV | NV | NV |
| San Joaquin | [County ADU processing guide](https://www.sjgov.org/docs/default-source/community-development/planning/adu-plans/processingguide4adus.pdf) O, from [county document hub](https://www.sjgov.org/department/cdd/planning/documents) | NV; City of San Joaquin code excluded | Same guide | County plan program described | NV | NV |
| San Luis Obispo | [County ADU hub](https://www.slocounty.ca.gov/departments/planning-building/how-to-apply-for-a-permit-in-unincorporated-slo-co/land-use%2C-subdivision%2C-zoning/land-use-permit/land-use-permit/acessory-dwelling-units/accessory-dwelling-units) O | June 2025 amendments L; hub distinguishes inland effective date from pending coastal certification | Pre-screening checklist L | County pre-reviewed program; site work remains | [Unpermitted ADU checklist, Nov 2025](https://www.slocounty.ca.gov/departments/planning-building/forms-documents/building-%28construction%29-forms-and-documents/unpermitted-construction-forms/bld1063-11052025-unpermitted-adu-checklist) S; AB2533 specificity NV | NV |
| San Mateo | [County ADU hub](https://www.smcgov.org/planning/accessory-dwelling-units-adus) O | Non-coastal ch. 8.392 / coastal 8.396 L; updates underway | Hub says summary/checklist forthcoming; [permit requirements](https://www.smcgov.org/planning/accessory-dwelling-unit-permit) O | NV | [Amnesty page](https://www.smcgov.org/planning/accessory-dwelling-unit-amnesty) O, reused corpus | [General building process](https://www.smcgov.org/planning/building-permit-process) O: 30-day comment letter / allow 30 days for resubmittal review; published service statements, not measured ADU times |
| Santa Barbara | Not verified by `Santa Barbara County California accessory dwelling unit ADU official`; city guide excluded | NV | NV | NV | NV | NV |
| Santa Clara | [County ADU hub](https://plandev.santaclaracounty.gov/accessory-dwelling-units) O | 2020 adopted ordinance archived on hub; current code separately NV | ADU information sheet L | County pre-approved program L | [AB 2533 program](https://plandev.santaclaracounty.gov/services/development-services/building/ab-2533-accessory-dwelling-unit-legalization-program) S | NV |
| Santa Cruz | [County ADU hub](https://cdi.santacruzcountyca.gov/Planning/Housing/adu.aspx) O | Hub warns portions of 2022 local rules superseded; update underway | Basics/development standards/how-to L | County pre-designed plans L | NV; city AB2533 result excluded | NV |
| Shasta | [County pre-approved ADU plans](https://www.shastacounty.gov/planning/page/shasta-county-pre-approved-adu-plans) S; open 403 | Feb 2026 draft found, adopted text NV | Plan-set checklists L | Seven designs advertised for unincorporated area | NV | NV |
| Sierra | Dedicated hub NV; [county housing-policy ordinance PDF](https://www.sierracounty.ca.gov/DocumentCenter/View/10713) S has ADU provisions; final adoption/date NV | Same | NV | NV | NV | NV |
| Siskiyou | [County pre-approved plans FAQs](https://www.siskiyoucounty.gov/community-development/page/pre-approved-plans-faqs) O | NV | FAQs include well/septic capacity review | County plans usable as ADUs except largest model | NV | NV |
| Solano | [County ADU guide](https://www.solanocounty.gov/government/resource-management/building-safety-services/adu-guide) O | Ch. 28 linked on Code Publishing | Submittal lists on guide | NV | AB2533 section on guide | NV |
| Sonoma | Dedicated hub not verified by `Sonoma County California accessory dwelling unit ADU official`; [county ordinance 6352](https://sonomacounty.gov/a/98633) S; open failed | Same; date/currentness NV | NV | NV | NV | NV |
| Stanislaus | [County ADU hub](https://www.stancounty.com/planning/ADUs/) O; explicitly unincorporated | Ch. 21.74 L; [publisher edition](https://ecode360.com/43733819) S | Process/interactive permit guide L | County/city joint plans; hub distinguishes available from forthcoming sets | NV | NV |
| Sutter | Not verified by `Sutter County California accessory dwelling unit ADU official` | NV | NV | NV | NV | NV |
| Tehama | [County ADU page](https://www.tehama.gov/accessory-dwelling-units-adus/) O | Official ordinance NV; third-party mirror excluded | County brochure L | [Building hub](https://www.tehama.gov/government/departments/building-and-safety/) S lists three floor plans | NV | NV |
| Trinity | Dedicated applicant hub NV; [county ordinance 315-860, Dec 2025](https://www.trinitycounty.ca.gov/DocumentCenter/View/3731/Ordinance-315-860---State-Housing-Laws-Compliance---ADUs-and-Residential-Land-Uses-PDF) O; redline presentation | Same | [County resources](https://www.trinitycounty.org/646/Resources-and-FAQs) S links state handbook, not county checklist | NV | NV | Ordinance describes 60-day decision/comment requirement; legal clock |
| Tulare | [County ADU hub](https://tularecounty.ca.gov/rma/permits/adu) O | NV | Permit requirements on hub | County pre-approved plans | NV | NV |
| Tuolumne | [County Building information](https://www.tuolumnecounty.ca.gov/982/Building-and-Safety-Information-Page) O | [County code index](https://tuolumnecounty.ca.gov/165/Tuolumne-County-Ordinance-Code) S links ch. 17.36 | Pre-approved plan instructions L | ADU/SFD pre-approved program | NV | NV |
| Ventura | [County ADU hub](https://rma.venturacounty.gov/accessory-dwelling-units/) O | Non-coastal ordinance L; county reports July 2024 effective date / Jan 2025 HCD compliance | [County FAQs](https://rmadocs.venturacounty.gov/building-and-safety/permit-application-information/building-and-safety-accessory-dwelling-units-and-junior-accessory-dwelling-units-frequently-asked-questions.pdf) S | NV | NV | NV |
| Yolo | Dedicated hub NV; [county code §8-2.506](https://codelibrary.amlegal.com/codes/yolocounty/latest/yolo/0-0-0-28897) O | Same; [county-hosted Title 8](https://www.yolocounty.gov/home/showpublisheddocument/75745/639063277210570000) S | NV | NV | NV | NV |
| Yuba | [County ADU program](https://www.yuba.gov/departments/community_development/planning/accessory_dwelling_unit_programs.php) O | Development Code L, ADU section NV | County ADU handbook L | County plan program; public files via Egnyte; full plans requested from Building | NV | NV |

## Three source-supported process sketches

These are document-grounded **declared-process** sketches, not validated case
traces. Large/mid/tiny refer to county size, not department staffing or the size
of the unincorporated service population. Every branch remains conditional on
the project; no source below establishes actual average elapsed time.

### Los Angeles — large county, staged review and applicant-carried clearances

The county's [April 2023 step guide](https://planning.lacounty.gov/wp-content/uploads/2022/10/adu_step-by-step-guide.pdf)
supports this sequence for unincorporated projects:

1. **Applicant:** verify jurisdiction/zoning; optional planning consultation;
   submit plans, land-use application and photos through EPIC-LA.
2. **Regional Planning:** completeness/fee intake, review and corrections;
   approve planning plans. Planning-first is recommended, not stated as an
   unconditional prerequisite for every building submission.
3. **Applicant → Building and Safety:** submit architectural, structural and
   energy plans; pay plan-check fees. **Plan checker ↔ applicant:** corrections,
   written responses and resubmittals.
4. **Applicant + referral agencies:** obtain required clearances and upload
   approvals; **Building and Safety:** verify all clearances, collect issuance
   fees and issue permit.
5. **Builder + inspector:** any required preconstruction meeting, phased
   inspections, final sign-offs and certificate of occupancy.

Version caveat: the [December 2025 memo](https://planning.lacounty.gov/wp-content/uploads/2025/12/ADU_memo_sb543_ab1154.pdf)
supersedes contrary older guidance, with 15 business days for incompleteness
notice and 60 calendar days from complete receipt for a decision. It also adds
an applicant appeal branch for incompleteness/denial. These are legal-clock
statements, not a 60-day estimate for the whole construction process.

### San Mateo — mid-size county, consolidated comment/resubmittal loop

1. **Applicant → Building:** identify the site, designer and proposed work;
   supply site, construction, floor/elevation and supporting engineering/energy
   documents. The published page still describes four paper plan sets.
   [ADU permit requirements](https://www.smcgov.org/planning/accessory-dwelling-unit-permit).
2. **Intake staff ↔ applicant:** supply missing intake items. **Review agencies:**
   review applicable requirements; **Building Inspection:** consolidate comments.
3. **Applicant:** wait for all agency comments, address all of them and resubmit
   through Building rather than individual agencies. **Review agencies:** repeat
   review; all required approvals precede issuance. The general guide states a
   30-day first comment letter and asks applicants to allow 30 days per
   resubmittal. Those are published service statements, not ADU observations.
   [Building permit process](https://www.smcgov.org/planning/building-permit-process).
4. **Legalization branch:** the county's AB 2533 page routes eligible older
   unpermitted units through the new-ADU application process; **county inspector**
   checks substandard conditions and recommends corrections. This is the same
   branch retained in the existing AB 2533 corpus.
   [County amnesty procedure](https://www.smcgov.org/planning/accessory-dwelling-unit-amnesty).

Currentness caveat: the [ADU hub](https://www.smcgov.org/planning/accessory-dwelling-units-adus)
announces ordinance updates. Paper-copy instructions and the generic building
service statements require reconciliation with the current electronic portal
before treating this as an executable 2026 procedure.

### Alpine — tiny county, direct building route with water/septic checks

1. **Applicant → Building Safety / Community Development:** submit the proposed
   ADU's location, size and type. The **February 2022** ADU sheet describes a
   direct building application route while then-conflicting local provisions
   were being updated.
2. **Applicant + Environmental Health / utility provider:** obtain well capacity
   or water-provider adequacy confirmation; obtain septic capacity review or
   community wastewater-provider confirmation, as applicable.
3. **County:** the dated sheet describes a 60-day decision after completeness
   for an ADU with an existing primary dwelling. It supplies neither measured
   duration nor proof of the ordinance's current status.
   [Dated county ADU sheet](https://www.alpinecountyca.gov/DocumentCenter/View/4389/Accessory-Dwelling-Unit--Information-Sheet-2022_Final).
4. **Current submission channel:** the live Building Safety page directs the
   applicant to iWorQ and well/septic questions to Environmental Health;
   **plan checker** reviews before permit issuance, and **inspector** checks
   construction phases. [Building Safety](https://www.alpinecountyca.gov/157/Building-Safety-Division).

This is a useful tiny-county declared-process seed, not evidence that Alpine is
faster, simpler in practice, or exempt from other site-specific approvals.

## Recommendation and remaining work

ADU remains a strong flagship **candidate**: the inventory supports a broad
county document layer, the reused AB 2533 material supplies a legalization
branch, and HCD letters add independently authored oversight evidence. It is
not yet a gold 58-county executable process corpus. Start document coding with
**Los Angeles, San Mateo and Alpine** for the three scale contrasts above, then
**Contra Costa, Napa and Butte** for explicit legalization or pre-approved-plan
variants documented in their county rows. This is a source-readiness shortlist,
not a ranking of outcomes or a population-representative sample.

P0's [APR timing audit](2026-09-16-apr-permit-timing.md) owns measured timing and
date quality; do not substitute this table's deadlines for those observations.
In particular, zero entitlement-to-permit spans do not by themselves establish
absence of a discretionary step. Newer process pages must not be treated as
the cause of older APR outcomes without aligning jurisdiction and effective
date. Duplicate-APN application/permit joins need linkage sensitivity, and weak
marginal correlations do not identify policy causes. CalFresh's verified
operational data may also support a flagship; this
packet does not assert ADU is uniquely measurable.

Remaining work, deliberately outside this completed bounded pass: resolve NV
and search-only rows; check the contents/currentness of linked checklists and
ordinances; enumerate the HCD dashboard in a working interactive view without
assuming unobserved rows absent; validate sketches against dated case traces;
expand vendor/code-host coverage; and reconcile changing state/local rules
before legal or process-model use. No account creation, outreach or access
control bypass was attempted.
