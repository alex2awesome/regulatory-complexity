# General Assistance / General Relief across the 58 California counties

Collected 2026-09-16 by scoping packet **P4-GENERAL-ASSISTANCE** (owner
`ga-agent`; continues a stalled `codex-ga` pass whose header and three cached
search transcripts are preserved in `corpus/counties/raw/general_assistance/`).

Statute: **Welf. & Inst. Code §17000**: "Every county and every city and county
shall relieve and support all incompetent, poor, indigent persons, and those
incapacitated by age, disease, or accident, lawfully resident therein, when
such persons are not supported and relieved by their relatives or friends, by
their own means, or by state hospitals or other state or private institutions."
§17001 then says the board of supervisors "shall adopt standards of aid and
care." That is the entire delegation. There is no state grant table, no state
application form, no state time limit, no state work requirement and no state
appeal to a state agency. Everything in the table below is a county's own
invention.

This is the **maximal-discretion case** in the project: one sentence of statute,
58 locally designed programmes, and — as recorded in the coverage audit at the
end — the thinnest documentation of any programme swept so far.

## Method and caveats

**WebSearch was exhausted (200/200) before this packet resumed.** Nothing here
came from the WebSearch tool. Discovery used two means only:

1. **URL-pattern guessing** against county human-services hosts and the three
   county-code platforms (Municode, American Legal, `*.county.codes`), fetched
   with `curl` under a browser user-agent.
2. **DuckDuckGo's HTML endpoint** (`https://html.duckduckgo.com/html/?q=...`)
   fetched by `curl`. This is a fetch, not a WebSearch call. It **rate-limits
   aggressively**: the second and third queries in quick succession returned
   DuckDuckGo's `anomaly.js` challenge page, so it was used sparingly with gaps.
   Mojeek returned a CAPTCHA on the first query. Bing's `&format=rss` endpoint
   returned 200 but ignored the query terms (a search for
   `"general assistance" "Sierra County" California welfare` returned
   Merriam-Webster's definition of "general"), so it is useless.

Every row carries its URL. Three provenance tiers are marked, as in the
[CCW sweep](2026-09-16-ccw-remaining-43-counties.md):

- **(opened)** — the document was fetched and its text read.
- **(search result only)** — the fact appeared in a search-result snippet and
  the underlying page was not successfully fetched.
- **not verified** — the fetch failed, or nothing was found by the means above.
  It never means the rule does not exist. A county with no reachable GA page is
  recorded as not verified across the row, **not** as having no programme; §17000
  is mandatory, so every one of the 58 has one.

Cached under `corpus/counties/raw/ga/`. Nothing was git-committed.

## The statewide picture: there is no register of what the counties do

**Verdict: no statewide compilation of county GA/GR *rules* exists that this
pass could find.** What exists is a statewide compilation of *counts*.

- **CDSS publishes caseloads and dollars, not rules.** The
  [GR 237 statistical report](https://www.cdss.ca.gov/inforesources/research-and-data/disability-adult-programs-data-tables/gr-237)
  (opened) is a monthly county-by-county workbook of GR and SSI/SSP Interim
  Assistance cases added, discontinued and carried forward, with cash and
  in-kind expenditure, published for FY 2015-16 through FY 2025-26. The
  [report form and instructions](https://www.cdss.ca.gov/research/res/pdf/blankforms/GR237.pdf)
  (opened) — still on its **1982 form revision, "GR 237 (6/82)"** — define
  General Relief as "a county funded and administered program... The aid granted
  by the county contains no state or federal funds. The GR program is referred
  to as General Assistance in some counties." The form collects **no rule
  fields at all**: no grant amount, no time limit, no work requirement, no
  loan-versus-grant flag. A researcher can learn from CDSS how many people each
  county aided and what it spent, and nothing whatever about what the county
  decided.
- **CDSS's own programme page disclaims knowledge.** The
  [General Assistance overview](https://www.cdss.ca.gov/general-assistance)
  (opened) states that county boards of supervisors fund and establish these
  programmes and that eligibility and benefit levels vary among the 58 counties.
  It links no county-by-county table.
- **`data.ca.gov` has nothing.** The keyless CKAN API
  `https://data.ca.gov/api/3/action/package_search?q=general+relief&rows=8`
  returns `count: 1`, and the single hit is *"Shallow Rock and Kelp Forest
  Ecosystems, California South Coast MPA Baseline Study"* — a false match on the
  word "relief". Queried 2026-09-16.
- **The nearest thing to a compilation is a legal-aid fact sheet, and it is
  qualitative.** Legal Services of Northern California's
  [General Assistance / County Aid](https://lsnc.net/self-help/general-assistance-county-aid)
  (opened) states the shape of the typical programme without naming a single
  county: "Each county has its own rules for its GA program"; "Most people can
  only get GA for 3 months out of a 12 month period"; "Most counties require
  that you do job search or a work program"; "If you cannot work because of a
  disabling condition, there is no time limit"; "**Think of GA as a loan**",
  with a lien on any home owned and reimbursement from retroactive SSI; and
  counties may bar an applicant from GA "for up to 180 days" as a sanction.
  This is the statewide modal design, and it is the correct prior for any county
  in the table below that could not be verified — but it is a prior, not a
  reading of that county's rules.

**So the headline stands: the most discretionary programme in California has no
central register of what its 58 implementations actually do.** A statute that
delegates everything is accompanied by a state data collection that records
only volume and cost. The variation is real and it is unmeasured.

## County inventory

Columns: programme name; grant for a **single employable adult** unless noted;
eligibility (residency / assets / income / employability); receipt time limit;
grant or repayable loan; application steps; work or job-search requirement;
SSI-advocacy requirement; source.

| County | Programme | Grant, single adult | Eligibility (residency / assets / income / employability) | Time limit | Grant or loan | Application steps | Work / job-search | SSI advocacy | Source |
|---|---|---|---|---|---|---|---|---|---|
| **Los Angeles** | General Relief (GR) | **$221/mo** maximum (couple $375) | Resident of LA County; net income below $221; personal property ≤$2,000; **one vehicle ≤$4,500, or ≤$11,500 if homeless and living in it**; cash on hand ≤$100 at application and ≤$1,500 after approval; real property assessed ≤$34,000 **and applicant must sign a lien** | not stated on the page — not verified | **lien on real property required**; page does not use the word "loan" for cash aid | BenefitsCal online; phone to Customer Service Center (866) 613-3777; in person at any DPSS district office or outreach site; or print the GR Application Packet and fax to (310) 215-8220 or mail. Four channels, the most of any county read. | not stated on this page — not verified | not stated on this page — not verified | [DPSS General Relief](https://dpss.lacounty.gov/en/cash/gr.html) (opened); a "General Relief Fact Sheet", "General Relief Application Packet" and a **"General Relief Redesign Project"** are linked from it |
| **San Diego** | General Relief (GR) | not verified — the page states only the **income limit**: net income under **$598** single, **$819** married couple | Resident of San Diego County **for at least 15 days** and intending to remain; property limit **$1,500**; proof of SSN or application for one | not stated on the pages read — not verified | **loan**: "Any aid received... may count toward repayment of the debt" | Eligibility Requirements page, How to Apply page and a **General Relief Program Guide** hosted on a separate file server | not verified | not verified | [GR overview](https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/general_relief.html), [eligibility](https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/general_relief/eligibility_requirements.html) (both opened); [Program Guide](https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=572) |
| **Contra Costa** | General Assistance (GA) | **$336/mo** maximum for a single **employable** person; **$454** for an employable couple. The page warns the maximum is not what recipients get: "grant amounts vary according to the number of people in the household, income, and the employability status" | Resident of Contra Costa County **for at least 15 days**; personal property **up to $500**; must apply for all potentially available income; receipt of SSI, SSDI, UIB or SDI may disqualify | **90 days in any 12-month period** for anyone determined **employable**, "unless permanently or temporarily disabled and unable to work" | **loan.** "All GA benefits are considered a loan to the individual receiving aid. GA applicants/recipients must sign a reimbursement agreement **as a condition of eligibility**." | BenefitsCal online, or phone (866) 663-3225. Then an assigned interview appointment plus a named form packet: **GA 201 E** (Statement of Facts), **GA 201 B** (Agreement of Cooperation), **SSP-14** (Authorization for Reimbursement of Interim Assistance) — the SSP-14 original must be wet-signed and returned by mail or in person. Ongoing: **quarterly QR7 report**, annual redetermination with interview, QR3 change report | implied by the employability determination; a work programme is not described on this page — not verified | **yes, mandatory**: applicants "determined to be unemployable and/or 65 years and older **are required to apply** for Supplemental Security Income"; non-citizens 65+ must apply for CAPI. A dedicated **SSI advocacy page** is linked | [EHSD General Assistance](https://ehsd.org/aging-and-adult-services/general-assistance/) (opened; note the path redirected from `/benefits/general-assistance/`), plus GA brochures in English and Spanish |
| **San Joaquin** | General Assistance (GA) | not verified as a dollar figure. **The benefit is not a cash grant**: rent is paid **direct to the property owner or payee**, plus a "Personal Needs Benefit (digital cash distribution)" for hygiene, household goods and food, plus **travel assistance to return to a former residence** | US citizen or legal resident; resident of San Joaquin County; 18+, or under 18 if married to someone 18+ | not stated on the page — not verified | **loan.** "General Assistance (GA) is a loan program... **all assistance received under GA must be repaid**" | In person only, at 333 E Washington St, Stockton, Mon–Fri 8–5. Appointments first-come, first-served; **GA clients are given a same-day appointment**; packet completed before the interview; **face-to-face interview and benefits may be issued the same day**. Named documents to bring include a **parole card** | **yes, both**: employable recipients must complete a **monthly job search** *and* "are required to work at a County assigned **Work Project** site which is credited towards their GA payment" — i.e. workfare | not stated on the page — not verified | [HSA General Assistance](https://www.sjchsa.org/Benefits-and-Assistance/Cash-Aid-and-Financial-Assistance/General-Assistance) (opened) |
| **Ventura** | General Relief (GR) | **up to $310/mo** for a household of one — and paid as **direct payments to the landlord and/or utility company**, not to the recipient | Adults **aged 18 to 64** with no dependent children; property value **≤$1,000**; liquid resources (cash, checking, savings, stocks) **≤$100**; income within limits; an **employability assessment** is conducted | not stated on the page — not verified | **loan.** "General Relief payments are considered a loan and must be repaid to the County" | **In person only.** Then an assigned **orientation** *and* an interview. Applicant must sign a **Personal Responsibility and Services Contract** that sets the assigned activities. Ongoing: comply with activities, keep appointments, report changes **within 5 days** | yes — employment workshops, job-search assistance and rehabilitation referrals assigned through the Personal Responsibility contract | **yes**: "If you are disabled, you will be required to apply for Social Security Disability benefits"; the county also assists with Veterans' benefits, Social Security, Workers' Compensation and SSI | [Ventura County HSA General Relief](https://venturacounty.gov/human-services-agency/general-relief/) (opened) |
| **Sonoma** | General Assistance (GA) | not verified as a dollar figure; described as "a monthly cash grant... paid on an EBT card" | Resident of Sonoma County **for at least 15 days**; US citizen or Lawful Permanent Resident; **cash and bank balances ≤$50**; personal property ≤$500; **one vehicle (or two) with total value under $3,000**, a vehicle used as a home not counted; minors ineligible for other aid may qualify | **up to 90 days in a 12-month period**, "and possibly longer for people with disabilities" | not stated on the page — not verified | Apply Mon–Fri 8–5 at the Human Services office; other named locations can supply an application; interpreters on request | yes — "Assistance through **Job Link** to prepare for and find a job" is listed as part of the programme | **yes** — "Help with applying for Supplemental Security Income (SSI)" listed as a programme benefit | [Sonoma County HSD General Assistance](https://sonomacounty.gov/health-and-human-services/human-services/jobs-money/general-assistance-cash-assistance-for-individuals) (opened) |
| **Lake** | General Relief (GR) | not verified as a dollar figure — and **GR in Lake County is not cash at all: "General Relief benefits are provided in the form of vouchers"**, covering housing and/or utilities, food, incidentals and transportation | US citizen or Lawful Permanent Resident; **Lake County resident with intent to continue residing there**; income and resource limits; sponsored immigrants must disclose sponsor information | **3 full calendar months in a calendar year**, extendable in **further 3-month increments** only "if you have been fully participating in your employment plan" | **loan.** "you will be required to sign a repayment agreement... Once you are no longer receiving GR, you will receive a **bill in the mail for the entire amount**"; payment plans offered; a separate agreement lets the county recover from the **initial SSI lump sum** | Six application channels named: hand to reception Mon–Fri 8–5; **drop boxes**; mail; **fax to 707-995-4204**; **by phone** on 707-995-4200. Ongoing: a **monthly in-person meeting with the Eligibility Specialist to collect the GR vouchers**; report changes within **10 calendar days**. Programme redesigned **effective 1 May 2020** | yes — mandatory employment services and an employment plan; schooling or training permitted only while "available and willing to accept employment of **at least thirty (30) hours per week**"; up to **3 months of GR toward a security deposit** | **yes, mandatory** — must "Apply for Supplemental Security Income/State Supplemental Payment (SSI/SSP) and/or other disability benefits that the program department considers appropriate" | [Lake County General Relief](https://www.lakecountyca.gov/1666/General-Relief) (opened) |
| **Mono** | General Assistance (GA) | not verified as a dollar figure | **Indigent adults and emancipated minors who are legal residents of Mono County** with no other means of support; personal property **up to $1,000**, and "the cash value of a life insurance policy counts toward this limit" | not stated on the page — not verified | **loan.** "All GA benefits are considered a loan. Recipients must sign a reimbursement agreement to qualify" | Request an application by mail or collect one at any county office | not stated on the page — not verified | **yes, mandatory, with an age trigger**: "If you are permanently disabled **or age 62+**, you must apply for Social Security or Supplemental Security Insurance (SSI)" | [Mono County General Assistance](https://www.monocounty.ca.gov/2016/General-Assistance) (opened) |
| **Nevada** | General Assistance (GA) | not verified as a dollar figure | Ineligible for any federal or state programme designed to meet all needs (CalWORKs, SSI/SSP); verification of residence, citizenship, identity, income and property required | not stated on the page — not verified | **repayable grant, stated as such and stated not to be an entitlement**: "General Assistance is a **repayable grant, not an entitlement program**" | BenefitsCal online or in person; bring bills in own name, SSN card or licence, lease, birth certificate, pay stubs, bank statements, vehicle proof | **yes, both, and named**: "**Cal-JOBS work registration and proof of weekly job search are mandatory**" | not stated on the page — not verified | [Nevada County Cash Assistance for Individuals](https://www.nevadacountyca.gov/1626/Cash-Assistance-for-Individuals) (opened) |
| **Siskiyou** | General Assistance (GA) | not verified as a dollar figure | Needy individuals; verification required before approval, including SSN or SSN application for all household members | **"a time-limited County program"** — the length is not stated on either page read; not verified | **loan.** "This is a loan program and must be repaid by the recipient"; the FAQ repeats: "Do I have to pay back my General Assistance benefits? **Yes, General Assistance is a loan and must be repaid to the County**" | In person at 818 S Main St, Yreka; by mail to the same address; or **by fax to 530-841-2723**. An Eligibility Worker verifies before approval | **yes** — the FAQ answers the complaint "My neighbor receives General Assistance but doesn't attend **Job Connection** or job search. Why do I?", so both a work programme and job search exist and are unevenly applied | **yes** — the programme has two tracks, and the disabled track includes "support from an **Agency liaison** who will assist recipients with the application process for Social Security Disability Programs... at no cost" | [Siskiyou GA](https://www.siskiyoucounty.gov/eta/page/general-assistance) and [GA FAQ](https://www.siskiyoucounty.gov/eta/page/general-assistance-frequently-asked-questions) (both opened) |
| **Colusa** | General Assistance (GA) | not verified as a dollar figure | Needy residents of Colusa County "who are not supported by their own means, by relatives or friends, by a federal, state or county hospital or correctional facility, or by other public or private sources" — near-verbatim §17000. Two categories only: **incapacitated person** or **employable person** | not stated on the page — not verified | **loan.** "The General Assistance program is a loan program" | The page gives **no procedure**: "For more information on how to apply please contact the Department of Health and Human Services". A phone call is the whole published process | not stated on the page — not verified | **partial**: all applicants "are required to apply and or receive Medical Assistance Programs and CalFresh benefits"; SSI is not mentioned — not verified | [Colusa County General Assistance (GA)](https://www.countyofcolusaca.gov/798/General-Assistance-GA) (opened) |
| **Mariposa** | General Assistance (GA), plus a separately-branded **General Assistance Advocacy Program (GAAP)** | not verified as a dollar figure | "County residents who are **unemployed or disabled** and are not eligible for or supported by any other cash assistance program" — that is the entire published eligibility statement | not stated on the page — not verified | not stated on the page — not verified | BenefitsCal online; in person at 5362 Lemee Lane, Mariposa or 5026 Broadway, Coulterville; or by phone to the Customer Service Center **with an electronic signature taken over the telephone**; or request a mailed application | not stated on the page — not verified | **yes, as a named programme**: Mariposa publishes a separate **General Assistance Advocacy Program (GAAP)** page — the only county in this pass to brand its SSI advocacy function as its own programme | [Mariposa GA](http://www.mariposacounty.gov/339/General-Assistance-GA) and [GAAP](http://www.mariposacounty.gov/332/General-Assistance-Advocacy-Program-GAAP) (both opened) |
| **Placer** | General Relief / General Assistance (the page carries both names) | not verified as a dollar figure. The page has an FAQ entry literally headed *"If I am eligible, how much will my benefits be?"* whose answer is **loaded by script and is not in the served HTML** — a present-but-unparseable failure, not a missing rule | 18+; **resident of Placer County for at least 15 days** with verification of intent to remain; **combined value of real and personal property must not exceed $75**, one vehicle exempt — the **lowest property limit found in this sweep, by a factor of 6.7 against Contra Costa's $500 and 26.7 against LA's $2,000**; all income counted in the month received and deducted from the grant; must apply for Unemployment Insurance if eligible | not stated on the page — not verified | **lien.** "If you own your home, you will be required to sign a lien on the property. If and when this property is sold, the county will seek reimbursement" | **Interview with an Eligibility Specialist is mandatory for every applicant** — "Interviews can now be completed by phone but may also be done in office". Application forms completed at one of the named offices, or online at BenefitsCal | yes — "If you are able to work you will need to **register with the Employment Development Department**". If not able to work, "the county will tell you what you must do to prove you cannot work" | not stated in the readable text — not verified | [Placer County General Relief / General Assistance](https://www.placer.ca.gov/2150/General-Relief-General-Assistance) (opened) |
| **San Luis Obispo** | General Assistance (GA), split into a **GA Employable Program** and a **GA Disabled Program** | not verified as a dollar figure, but the **income limit is published: $355.00 for one person**. Benefits are "money, vouchers and job-related services", issued on an **EBT debit card** | Resident of SLO County, not eligible for any other cash aid; no children under 18 in the home; **property limit $500 at application, $1,000 for ongoing cases**; the Disabled programme requires a physician or mental-health professional to certify short-term (<12 months) or long-term (12+ months) disability | **the Employable programme is a 12-week time-limited programme** — an explicit, unusual unit (12 weeks, not 3 months) | not stated on the page — not verified | **In person only**, at any DSS office, Mon–Fri 8–5. **A face-to-face interview is required of every applicant, and all GA interviews are held in the San Luis Obispo office only**; applicants living outside the city "will be offered a bus pass to allow the applicant to travel to San Luis Obispo for the interview" — a documented geographic access cost in a large rural county. The case manager then issues a written verification list with a due date | **yes** — "applicants must perform job search activities at the local Job Center" | **yes, staffed and named**: long-term-disabled participants must apply for SSI/SSP and RSDI, and are referred to a **"Benefits Arch Advocate"** who completes the SSI application with them; a separate **General Assistance Benefit Advocate** page and a *General-Assistance-Disability-Program-Benefits-Arch* form are published | [SLO GA Cash Aid](https://www.slocounty.ca.gov/departments/social-services/cash-assistance-programs/services/general-assistance-cash-aid) and [GA forms index](https://www.slocounty.ca.gov/departments/social-services/forms-documents/participant-services/general-assistance/forms) (both opened) |
| **Butte** | General Assistance (GA) | not verified as a dollar figure | Employable adults, and adults who are temporarily disabled or awaiting SSI. The page **quotes §17000 verbatim** as the authority — one of only two counties in this pass to publish the statutory text | **three months** of cash assistance for **eligible employable adults**; "longer-term assistance to eligible adults who are temporarily disabled or who are awaiting Supplemental Security Income (SSI) approval" | not stated on the page — not verified; an "Overpayment Repayment Options" page exists alongside it | **In person** at a **Butte Community Employment Center** in Chico or Oroville — the intake point is an employment centre, not a welfare office | implied by the employable/disabled split and by intake at an employment centre; the specific activity is not stated — not verified | **yes, as a grant category**: "awaiting Supplemental Security Income (SSI) approval" is an explicit longer-term aid category | [Butte County General Assistance](https://www.buttecounty.net/406/General-Assistance) (opened) |
| **Merced** | General Assistance (GA) | not verified as a dollar figure | "individuals that need financial assistance, but do not meet CalWORKs deprivation needs **and do not have a child in the home**" | "General Assistance is a **temporary solution**" — no number given; not verified | not stated on the page — not verified | **Walk in and apply** at the Merced office | **yes** — "does have work requirements. Recipients are expected to **actively search for work** while they are receiving General Assistance **unless an exemption has been granted**" | not stated on the page — not verified | [Merced County General Assistance](https://www.countyofmerced.com/778/General-Assistance) (opened) |
| **Solano** | General Assistance (GA) Program | not verified as a dollar figure | Adults 18+ without children; emancipated youth. **No asset, income or residency figure is published on the page at all** | "short-term cash assistance" — no number; not verified | **loan.** "Cash assistance is provided in the form of a **loan, which must be paid back**" | Two channels: **by phone with county assistance**, or in person at a county office. Ongoing: a **GA Income Report form** | "GA helps people find employment and connect to helpful resources" — no mandatory activity stated; not verified | **yes, as a named programme**: "The **Supplemental Security Income (SSI) advocacy program** is available to assist individuals with disabilities and significant barriers to employment apply for SSI benefits" | [Solano County General Assistance](https://www.solanocounty.gov/government/health-social-services-hss/employment-eligibility/cash-aid/general-assistance) (opened) |
| **Santa Barbara** | General Relief (GR) | not verified | not verified | not verified | not verified | not verified | not verified | not verified | [DSS General Relief](https://www.countyofsb.org/dss-general-relief) — **fetched 200 OK at 296 KB and the page contains no programme text**: the readable content is the page title, the heading "General Relief", and the site's navigation listing RCA, CAPI, Tribal TANF and TCVAP. A present-but-unparseable / empty-page failure, not a block |
| **Alameda** | General Assistance (GA), with a named sub-programme, the **Alternative General Assistance Program (AGAP)**, for drug- and alcohol-dependent recipients | **$336/mo** for 1 adult, **$548/mo** for 2 adults (GA Regulations §9-5-2 schedule). Housing allowance separately scheduled: **$145** for 1 person, **$235** for 2, **+$100 per additional dependent**. "Maximum allowance is $100 per recipient" for a further category | Legal resident of Alameda County, indigent adult or emancipated minor, no other means of support. **Net market value of personal property must not exceed $1,000** for an individual; a burial trust up to $500 is exempt; excess property may be aided against a **signed lien form**. An individual may be aided for **90 days on secondary identification** pending primary ID | **3 months of cash assistance in any 12-month period** for anyone "mentally and physically able to work" (§9-2-4). Partial months do not count. **Temporary exemptions**: temporary disability (excluding "colds, flu, sprains, bruises, blisters, minor infections, minor aches and pains" lasting under one calendar month); outpatient drug and alcohol treatment approved by the Agency; AGAP participation; **former foster youth and ILSP participants from 18 up to the 25th birthday**. **Permanent exemptions**: permanent disability verified by a medical provider or mental-health clinician; **anyone 64 or older** | **loan.** All applicants must sign a reimbursement agreement, kept by the Agency with a copy to the Auditor-Controller, and the **SSI/SSP Authorization for Reimbursement of Interim Assistance**. A **legal sponsor of a non-citizen must also sign a reimbursement agreement to repay all aid paid**. Lien on excess property | Governed by a published, sectioned regulation with a **"PROMPTNESS REQUIREMENT" (§9-1-6)**, necessary documentation (§9-1-7) and verification (§9-1-8) sections, a **presumptive-eligibility policy (Handbook 90-01.61)**, and **separate medical-evaluation appointment policies for the Hayward and Oakland offices (90-02.321, 90-02.322)** | yes — Employment Services (§9-2-3) and a Sanctions section (§9-2-5); CalFresh Employment and Training handbook published alongside | **yes** — "Assistance with the SSI, SSDI, and/or CAPI application for low or no income aged, blind, and disabled people"; the Interim Assistance reimbursement authorisation is mandatory for all | **The best-documented county in this sweep.** [GA programme page](https://socialservices.alamedacountyca.gov/our-services/Work-and-Money/General-Assistance/index) (opened) links a **complete 2,667-line GA Regulations PDF**, [GA-Regulations.pdf](https://socialservices.alamedacountyca.gov/acssa-assets/PDF/GA-Policies/GA-Regulations.pdf) (opened; "Revised: January 8, 2019", "**Pursuant to Alameda County General Code – Title 7**"), **plus 14 separately numbered GA Handbook sections** as individual PDFs, **plus a standing public-comment process**: "When substantial changes to the General Assistance regulations are proposed, the Social Services Agency will make them available for public review and comment, prior to implementation" |
| **San Francisco** | **County Adult Assistance Programs (CAAP)** — not called GA or GR at all. An umbrella covering the county's cash programmes for adults without dependent children | **up to $714/mo** — the **highest verified grant in this sweep, 3.2× Los Angeles's $221** | San Francisco residency (verifiable for a homeless applicant "through shelter stay and/or with **EBT transactions made in San Francisco**"); **net income under $714/mo**; personal property **$2,000 single / $3,000 couple**; **one vehicle**; student status limited to high school/GED, a two-year associate degree or vocational school; CalFresh and Medi-Cal applications auto-bundled | not stated in the fact sheet — not verified | not stated in the fact sheet — not verified | **In person at 1460 Mission St.** (relocated from 1235 Mission St.): tell the lobby receptionist, take a **numbered ticket and a short screening form**, complete it while waiting, hand it in at the counter, receive a CAAP application and an **initial appointment**. Then a **one-week Presumptive Eligibility (P.E.) period** running from the date P.E. is established to the **Final Intake interview** or benefit authorisation, extended for intervening weekends or holidays; during P.E. a homeless applicant "will be offered shelter reservation at an HSA shelter" and a housed applicant facing eviction may get **direct rent payment to the landlord, issued during the P.E. period only**. Denial appeal: **Fair Hearing requested no later than the 10th calendar day** after the Notice of Action. Renewal every **six months** by phone interview | **yes, and unusually rich**: Voluntary Intensive Employment Services (VIES), immediate access to **JobsNOW!**, and "placement in a job with a guaranteed starting pay of at least San Francisco's minimum wage" | **yes** — "Assistance with applying for SSI from **on-site case managers**, if disabled" | [CAAP programme page](https://www.sfhsa.org/services/financial-assistance/county-adult-assistance-programs-caap), [eligibility](https://www.sfhsa.org/services/county-adult-assistance-programs-caap/check-caap-eligibility) (both opened) and the [CAAP Information Sheet PDF, updated 3/1/2026](https://www.sfhsa.org/sites/default/files/media/document/2026-03/factsheet_caap_english_03.1.26.pdf) (opened). A **CAAP Eligibility Handbook** is referenced. Published in six languages. **Unique local rule: "Beginning January 1, 2025, CAAP clients with a substance use disorder who want to access county-funded cash assistance are required to be enrolled in treatment and services."** The fact sheet also names **Bay Area Legal Aid** as the advocate to call |
| **Humboldt** | General Relief (GR) | not verified as a dollar figure | County residents "who lack minimum resources for food, shelter and medical care"; **a person with health issues preventing work "must be actively seeking medical treatment as a condition of General Relief eligibility"** — a locally added condition found nowhere else in this sweep | **three months in a 12-month period for employable individuals** | **loan.** "These benefits must be repaid" | not stated on the page — not verified. The page instead carries an **ADA non-compliance notice**: the Social Services Branch at 929 Koster St., Eureka "is currently not in full compliance with the Americans with Disabilities Act" and applicants needing curbside assistance must call 877-410-8809 in advance | **yes, and named**: non-disabled customers "must be available to meet GR work requirements, complete **monthly job searches** and participate in **Helping Humboldt**, an occupational empowerment program to gain job skills and work experience" | **yes** — a person with a verifiable disability preventing even light work "may be excused from work activities and be **provided with assistance through the application process for SSI/SSP**"; the stated goal of GR is self-sufficiency through employment "or, if disabled, **to secure federal assistance**" | [Humboldt County General Relief](https://humboldtgov.org/527/General-Relief) (opened) |
| **Inyo** | General Assistance / General Relief (the page uses both, hyphenated as one programme) | not verified as a dollar figure | "eligible county residents who have no other means of support" — the entire published eligibility statement | not stated on the page — not verified | **loan.** "Any aid received must be repaid to the county" | "To apply for General Assistance, contact our office." A phone call is the whole published process | **yes, implicitly and unusually**: "**Completed hours of required Job Training may count toward repayment of the debt**" — so job training exists and functions as debt credit | not stated on the page — not verified | [Inyo County Apply for Public Assistance](https://www.inyocounty.us/aging-social-services/apply-public-assistance) (opened). **Template lineage — see the finding below: Inyo's GA paragraph is word-for-word San Diego's.** A fraud hotline for "CalWORKs, Cal Fresh, General Assistance/Relief, or Medi-Cal" is published at 760-873-3305 |
| **Sierra** | General Assistance | not verified as a dollar figure | "individuals **or families** that do not qualify for other cash programs" — Sierra is one of the few to admit families to GA in its published text | **up to 3 months in a 12-month period, "unless they are exempt from these time limits"** | not stated on the page — not verified | not stated on the page — not verified | not stated for GA (the page states the work requirement for CalWORKs, not GA) — not verified | not stated on the page — not verified | [Sierra County Public Assistance](https://www.sierracounty.ca.gov/306/Public-Assistance) (opened). **GA is a single paragraph inside a page listing five programmes.** Separately confirmed: the [Sierra County Code](https://sierra.county.codes/) (opened) has **no welfare, social services or public assistance title** — its 21 titles run General Provisions, Administration, Personnel, Revenue and Finance, Business Licenses, Health and Sanitation, Public Places, Roads, Building, Land Use, Zoning, Permits, General Plan, Subdivision, Development Agreements, Easements, Fire Safe, Floodplains, Surface Mining, Abandoned Vehicles. **Sierra's GA rules are not in Sierra's code** |
| **Plumas** | General Assistance | not verified as a dollar figure. **Aid is partly in kind**: "provides **repayable cash aid and in-kind aid** for the subsistence and needs of the county's disadvantaged citizens" | not stated on the page — not verified | not stated on the page — not verified | **repayable, stated in the programme's one-sentence definition** | not stated on the page — not verified; a separate "BenefitsCal Online Application for Benefits" page exists | not stated on the page — not verified | not stated on the page — not verified | [Plumas County Eligibility](https://www.plumascounty.us/241/Eligibility) (opened). **GA is one sentence**, on a page that gives CalWORKs, CAPI, RCA and TCVAP a paragraph each |
| **Modoc** | **General/Interim Assistance (GA/IA)** — the only county in this sweep to brand GA and SSI Interim Assistance as a single programme in its public name | not verified as a dollar figure | Eligible employable adults; adults temporarily disabled or awaiting SSI. **The document quotes §17000 verbatim** | **three months** of cash assistance for eligible employable adults; "longer-term assistance to eligible adults who are temporarily disabled or who are awaiting Supplemental Security Income (SSI) approval" | not stated — not verified | **In person only**, at Modoc County Department of Social Services, 120 N Main Street, Alturas. Note that CalWORKs and CAPI on the same sheet each offer **in person, by mail and by telephone**, while **GA/IA offers in person only** — a documented channel restriction specific to GA | not stated — not verified | **yes, built into the programme name and the aid category**: "awaiting Supplemental Security Income (SSI) approval" is an explicit longer-term aid category | [Modoc County Cash Assistance Programs (PDF)](https://www.countyofmodoc.gov/DocumentCenter/View/621/Cash-Assistance-Programs-PDF) (opened; footer "Rev. 11/2021"), linked from [Social Services](https://www.countyofmodoc.gov/615/Social-Services). **A one-page PDF leaflet is Modoc's entire published GA documentation.** **Template lineage — Modoc's GA paragraph is word-for-word Butte's, including the lower-case typo "Welfare and institutions Code".** |
| **Alpine** | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | **No GA page found.** The [county sitemap](https://www.alpinecountyca.gov/sitemap.xml) (opened, 50 KB, every page listed) contains **no General Assistance, General Relief or indigent-aid page**; it does contain "Cash Assistance for Refugees and Non-Citizens", "Adult Services", "Utility Assistance" and "Social Services". The [Social Services page](https://www.alpinecountyca.gov/203/Social-Services) (opened) names CAPI/RCA but **not GA**. The CivicPlus site search for "general assistance" returns 1,002 results, none of them a GA programme page. Alpine is **not** on Municode. §17000 is mandatory, so Alpine has a programme; **nothing about it is published on the county website** |
| **Trinity** | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | **No GA page found.** The [sitemap](https://www.trinitycounty.org/sitemap.xml) (opened) lists Public Assistance, Family Assistance, Food Assistance, Healthcare Benefits and Immigrant & Refugee Assistance but **no General Assistance page**; the [Public Assistance page](https://www.trinitycounty.org/251/Public-Assistance) (opened) names CAPI and RCA only. Trinity **is** a Municode client (ClientID 17035) but Municode serves an Angular shell to a script, so the code text was not reachable by these means |
| **Calaveras** | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | **No GA page found.** [socialservices.calaverasgov.us](https://socialservices.calaverasgov.us/) (opened, 64 KB) contains **no mention of General Assistance, General Relief, indigent aid or cash aid**. `calaverasgov.us/sitemap.xml` returns **404**, so sitemap discovery is unavailable. Calaveras **is** a Municode client (ClientID 773), same shell problem |
| **Marin** | General Relief (GR) | **maximum loan $387/mo** for a single person, **$636/mo** for a married couple; paid on an EBT card. "Income and resources may reduce the amount loaned" | Live in Marin and intend to stay; **US citizen, lawful permanent resident, or residing under PRUCOL** (the only county in this pass to name PRUCOL on its public page); **liquid assets ≤$400 single / $800 couple**; **income ≤$387/mo single / $636 couple**; **personal property ≤$600 single / $1,200 couple**, some items exempt; 18 or older; applicants must apply for and accept any available income (UI, Workers' Comp, pensions, Social Security) and apply for CalFresh and Medi-Cal | **up to 6 months in a 12-month period** — **double the modal 3 months, and the longest employable limit found in this sweep** — "and possibly longer for people with disabilities" | **loan, and the page says so in the grant sentence itself**: "The maximum **loan** for a single person is $387 a month" | In person at 120 N Redwood Drive, San Rafael; online at BenefitsCal.org; or download the application and instructions. Accommodation requests by voice or TDD/TTY; documents available in alternative formats | **yes** — "Assistance through **CalFresh Employment & Training** program to prepare for and find a job"; a published **GR 61 Employability Assessment** form; employment assessments, barrier remediation, an employment plan and employer connections | **yes** — "Help with applying for Supplemental Security Income (SSI)"; if disability is verified "you can receive assistance in filing your claim for Social Security Disability benefits"; 65+/blind/disabled non-citizens ineligible for SSI/SSP solely on immigration status get help applying for **CAPI** | [Marin HHS General Relief](https://www.marinhhs.org/general-relief) (opened — note the **county's main host `marincounty.gov` 403s to scripts while `marinhhs.org` serves everything**), the [GR Brochure PDF rev. 6.9.25](https://www.marinhhs.org/sites/default/files/files/servicepages/2025_06/hhs_gr_brochure_6.9.25.pdf) (opened; Spanish version published), and the [GR 61 Employability Assessment](https://www.marinhhs.org/sites/default/files/files/servicepages/2023_05/gr_61_employability_assessment.pdf) |
| **San Mateo** | General Assistance Program | not verified as a dollar figure | "eligible county residents who are not supported by their own means, other public funds, or assistance programs"; **resident of San Mateo County for at least 15 consecutive days** | not stated on the page — not verified | **loan** by implication: the **SSP-14 Authorization for Reimbursement of Interim Assistance** is published as an application form in English and Spanish; the word "loan" is not used — not verified | In person at any regional office, or submit online. **Notably applicant-friendly**: "If you do not have all the documents listed, you can still apply. The County will provide you with a list of what is needed, give you some time to provide, and can help you obtain missing verification" | **yes** — "**Employable adults are required to participate in Employment Services**" | **yes, by form**: the SSP-14 Interim Assistance reimbursement authorisation is a published GA application document | [San Mateo County HSA General Assistance](https://www.smcgov.org/hsa/general-assistance) (opened; `smchsa.org` and `hsa.smcgov.org` both redirect away, so the path had to be recovered from the HSA hub page) |
| **Napa** | General Assistance (GA) | not verified as a dollar figure — and **GA in Napa is vouchers, not cash**: "General Assistance benefits are provided in the form of vouchers", covering housing and/or utilities, food, incidentals and transportation | US citizen or Lawful Permanent Resident; **Napa County resident with intent to continue to reside** there; income and resource limits not published as figures; sponsored immigrants must disclose sponsor information | **3 full calendar months in a calendar year**, continuable in **3-month extensions** only with full participation in the employment plan | **loan.** "you will be required to sign a repayment agreement... you will receive a **bill in the mail for the entire amount** of GA you received"; payment plans on request; a separate agreement lets the county recover from the **initial SSI lump sum** | Complete **form SSSD 4005 (General Assistance application)** and hand it to a receptionist at any location Mon–Fri 8–5, or submit by the other listed means; a valid phone or mailing address is needed so an interview can be scheduled. Ongoing: **monthly in-person meeting with the Eligibility Specialist to collect the GA vouchers**; report changes within **10 calendar days**. Programme redesigned **effective 1 May 2020**. A separate **Forms & Publications for General Assistance** page publishes the application and a **job-search tracking form** | **yes** — mandatory employment services and employment plan; school or training allowed only while "available and willing to accept employment of **at least thirty (30) hours per week**"; up to **3 months of GA toward a security deposit** | **yes, mandatory** — must "Apply for Supplemental Security Income/State Supplemental Payment (SSI/SSP) and/or other disability benefits that the program department considers appropriate" | [Napa County General Assistance](https://www.napacounty.gov/376/General-Assistance) and [GA Forms & Publications](https://www.napacounty.gov/3717/Forms-Publications-for-General-Assistance) (both opened). **This page was absent from Napa's own sitemap.xml and was found only through the CivicPlus site-search endpoint.** **Template lineage — Napa's GA page is word-for-word Lake County's General Relief page, including the same "Effective May 1, 2020" redesign date. Napa and Lake are adjacent counties.** |
| **Orange** | General Relief (GR) | not verified as a dollar figure | "eligible **indigent adult lawful residents** who are ineligible for Federal or State programs" | not stated in the readable text — not verified | not stated in the readable text — not verified | Phone 1-800-281-9799 or visit "select SSA locations". **A channel is being removed: "Attention: Effective May 1, 2026, online General Relief applications will no longer be available on BenefitsCal."** Orange is the only county in this sweep observed **withdrawing** an application channel | **yes, as a named programme**: "If you receive General Relief you may be required to participate in the **CalFresh Employment & Training / General Relief Work Program (GRWP)**" | not stated in the readable text — not verified | [Orange County SSA Cash & CalFresh](https://ssa.ocgov.com/cash-calfresh) and [General Relief](https://ssa.ocgov.com/cash-calfresh/general-relief) (both opened). Note `ssa.ocgov.com/financial-assistance/general-relief` and three other guessed paths returned **404 with a 150 KB body**, the same "200-OK page that is not what its URL promises" failure mode the CCW sweep recorded for Orange |
| **Santa Cruz** | General Assistance Program | not verified as a dollar figure | "You will be required to apply for other types of available income **as a condition of eligibility**" | not stated on the page — not verified | **loan.** "The General Assistance Program is a **County-funded loan program** designed to assist adults in meeting their basic needs for housing, utilities, personal needs, and transportation" | A "How to Apply for General Assistance" page exists; a **General Assistance PDF (95.5 KB)** and a **Spanish version (104 KB)** are published | not stated on the page — not verified | **yes, as a named beneficiary group**: "**Disabled individuals who need support until their Supplemental Security Income (SSI) benefits are awarded**". Also "Assistance for homeless applicants to a place of residence" | [Santa Cruz County HSD, What is General Assistance?](https://www.santacruzhumanservices.org/EmploymentBenefits/GeneralAssistance/WhatisGeneralAssistance) (opened). Four other guessed paths (`santacruzcountyca.gov`, `hsd.santacruzcountyca.gov`, `/BenefitsServices/GeneralAssistance`, `sitemap.xml`) returned 404 or failed DNS |
| **San Bernardino** | General Relief, run by the **Transitional Assistance Department (TAD)** | not verified | not verified | not verified | not verified | not verified | not verified | not verified | [wp.sbcounty.gov/tad/programs/general-relief/](https://wp.sbcounty.gov/tad/programs/general-relief/) — **fetched 200 OK at 160 KB and the readable content is the page title, the heading "General Relief" and the department name.** The programme text is not in the served HTML. The canonical host `hs.sbcounty.gov/tad/general-relief/` **403s to both curl and WebFetch**; the working host was recovered only from a redirect. Present-but-unparseable, plus a hard block on the canonical host |

### Table B — the other 24 counties, and exactly how each attempt failed

These complete the 58. **Every one of them has a §17000 programme** — the statute
is mandatory. Nothing was verified about any of them by the means available, and
the failure mode is recorded because the availability model is itself a finding.

| County | Attempts | Failure mode |
|---|---|---|
| **Santa Clara** | `socialservices.sccgov.org/general-assistance`, `/sitemap.xml`, `www.sccgov.org/sites/ssa/Pages/ssa.aspx`, `www.santaclaracounty.gov/services/social-services`, `ssa.sccgov.org` (DNS), Wayback snapshot, `r.jina.ai` proxy, Municode client 7623 | **Hard WAF 403 to curl *and* to WebFetch** on every sccgov host. The 2nd-largest GA programme in the Bay Area is unreadable by script |
| **Fresno** | `fresnocountyca.gov/Departments/Social-Services/General-Relief` (2 casings), `co.fresno.ca.us/...`, Wayback, `r.jina.ai`, amlegal, Municode client 5936 | 403 to curl and to the reader proxy |
| **Riverside** | `dpss.rivco.org` (DNS failure), `rivcodpss.org/general-relief` (403), `dpss.rivcocha.org` (DNS failure), Wayback | **Two of three guessed hosts do not resolve at all; the one that does, 403s** |
| **Tulare** | `tularehhsa.org/general-relief/` → redirects to `tchhsa.org/` (403), `tularecounty.ca.gov/hhsa/` (403), Wayback, amlegal | 403 |
| **Kern** | `kernhumanservices.com` (DNS), `kerncounty.com/government/county-departments/human-services` (403), `kcdhs.org` (403), `kernbhrs.org` (403), `kcdhs.kerncounty.com` (DNS), Wayback, amlegal, Municode 6459 | Mixed DNS failure and 403 |
| **Sacramento** | `dhs.saccounty.gov` root (200, but **no assistance links in the served HTML**), `/PRI/Pages/General-Assistance/GA-General-Assistance.aspx`, `/PRI/Pages/General-Assistance/default.aspx`, `/PRI/Pages/GA/...`, `/PRI/Pages/default.aspx`, `/PRI/Pages/General-Assistance.aspx`, `/sitemap.xml`, `saccounty.gov/sitemap.xml`, amlegal | **404 on six guessed SharePoint paths and no sitemap.** The root page fetches but its navigation is script-rendered. *Sacramento is the county litigated in Hunt v. Superior Court* — see the litigation map |
| **Stanislaus** | `stancounty.com/csa/services/general-assistance.shtm`, `/csa/assistance/...`, `/csa/program/...`, `/csa/general-assistance.shtm`, `/csa/`, and **`stancounty.com/sitemap.xml` (200, 253 KB, read in full)** | The sitemap is complete and readable and **contains no General Assistance or General Relief page**. Stanislaus appears to publish no GA page at all |
| **Yolo** | `yolocounty.gov/sitemap.xml` (403), `yolocounty.org/...` (403), `yolocounty.gov/.../adult-aging/general-assistance` (403) | 403 on every path and on the sitemap. *Yolo is the county in Guidotti v. County of Yolo* |
| **Shasta** | `shastacounty.gov/sitemap.xml` (403), `/health-human-services/program/general-relief` (403), `co.shasta.ca.us/...` (connection refused) | 403 plus a dead legacy host. Municode client 7682 |
| **Mendocino** | `mendocinocounty.gov/sitemap.xml` (403), `/government/social-services` (403), `mendocinocounty.org/...` (403) | 403. Municode client 6834 |
| **Monterey** | `countyofmonterey.gov/sitemap.xml` (403), `/government/departments-a-h/social-services` (403), `co.monterey.ca.us/...` (403) | 403. Municode client 6930 |
| **El Dorado** | `edcgov.us/sitemap.xml` and `/Government/HumanServices` and `/Government/hhsa`, all redirecting to `eldoradocounty.ca.gov` (403) | 403. Municode client 5775 |
| **Kings** | `countyofkings.com/sitemap.xml` and `/sitemap_index.xml` and `/departments/health-welfare/human-services-agency`, all redirecting to `countyofkingsca.gov` (403) | 403. Municode client 11687 |
| **Madera** | `maderacounty.com/sitemap.xml` (403), `/government/social-services` (403) | 403. Municode client 6694 |
| **Sutter** | `suttercounty.org/sitemap.xml` and `/government/county-departments/human-services`, both redirecting to `sutter.gov` (403) | 403. Municode client 7874 |
| **San Benito** | `sanbenitocountyca.gov/sitemap.xml` (403), `/departments/health-human-services` (403), `cosb.us/...` (403) | 403. Note the only "San Benito" Municode client is **San Benito County *Water District*** (17368), not the county |
| **Tuolumne** | `tuolumnecounty.ca.gov/sitemap.xml` (403), `/sitemap_index.xml` (403), `co.tuolumne.ca.us` (connection reset) | 403 plus a dead legacy host |
| **Glenn** | `countyofglenn.net/sitemap.xml` (403), `/dept/health-human-services/welcome` (403), `/dept/health-human-services/social-services` (403) | 403 on every path including the sitemap |
| **Amador** | `amadorgov.org/departments/social-services` and `amadorcounty.gov/sitemap.xml`, both 403 | 403. Amador is **not** a Municode client |
| **Imperial** | `imperialcounty.org/sitemap.xml` (**404 with a 394 KB body** — a 404 page four times the size of most counties' whole GA page), `/departments/social-services/`, `/departments/dss/`, `icdss.imperialcounty.org` (DNS), `co.imperial.ca.us` (DNS) | **Misrouted 404s plus two non-resolving hosts.** Municode client 6325 |
| **Tehama** | `co.tehama.ca.us` (DNS), `tehamacountysocialservices.org` (DNS), `.com` (DNS), `tehamacohealthservices.net` (200, 269 KB, **contains no General Assistance link or text**) | **Three non-resolving hosts and one live host with no GA content.** Municode client 7911 |
| **Del Norte** | `co.del-norte.ca.us/GeneralAssistance`, `/GeneralRelief`, `/DHHS-PA-GeneralAssistance`, `/DHHS-PA-GeneralRelief`, `/DHHS-PublicAssistance`, `/DHHS` (all 404), **`/sitemap.xml` (200, 239 KB, read in full)**, and the site search (200, **no GA result**) | The sitemap is complete and readable and lists `CashAssistance-CalWORKs`, `CalWORKsWelfaretoWork`, `DHHS-PA-HomelessAssistance` and five other assistance pages but **no General Assistance or General Relief page**. Del Norte appears to publish none |
| **Yuba** | `yuba.org/sitemap.xml` (404, zero bytes), `/departments/health_and_human_services/`, `/departments/`, `/hhs`, `/search/?q=` (all 404 zero-byte) | **Every path returns a zero-byte 404.** Municode client 11240 |
| **Lassen** | `lassencounty.org/sitemap.xml` → `lassencounty.gov` (200, read in full), `/306/Community-Social-Services` (200), site search for "general assistance" (200, **1,098 results, none a GA programme page**) | The site is fully readable and **has no GA page**. Its sitemap lists Food Assistance, Health & Social Services and Community Social Services, but no General Assistance |

## The statute bounds the discretion at named seams, and the counties pile up on them

This was not expected and it is the most important analytic finding in the packet.
§17000 delegates everything, but **two later sections legislate the outer edges of
the delegation**, and the observed county rules **cluster exactly on those edges**.

**[§17000.5](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WIC&sectionNum=17000.5.)
(opened) creates a safe harbour, not a floor.** A board of supervisors "may adopt
a general assistance standard of aid, including the value of in-kind aid which
includes... the monthly actuarial value of up to forty dollars ($40) per month of
medical care, **that is 62 percent of a guideline that is equal to the 1991
federal official poverty line**", adjustable in line with the CalWORKs maximum
aid level. And then subdivision (b): "**The adoption of a standard of aid pursuant
to this section shall constitute a sufficient standard of aid.**" That single
sentence is the legislative answer to Boehm: a county that sets its grant by this
formula is immunised from an adequacy challenge without ever conducting a needs
study. It converts an open-ended judicial standard into a number.

**[§17001.5](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WIC&sectionNum=17001.5.)
(opened) enumerates the permitted restrictions and caps each one.** A board may:

- **(a)(1)(A)** adopt a residency requirement, and "**Any residence requirement
  under this paragraph shall not exceed 15 days**" — with (B) barring any
  requirement that an applicant have an address or that a homeless person acquire one.
- **(a)(2)(A)** reduce the single-adult standard for shared housing by **not more
  than 15% (one other person), 20% (two), 25% (three or more)** — and (C)
  grandfathers counties whose larger reductions predate **19 August 1992**.
- **(a)(3)** discontinue aid **for not more than 180 days** for an employable
  recipient who has had three months of aid and refuses job training or
  appropriate employment without good cause, where "lack of good cause" may be
  shown by willful refusal **or "not less than three separate acts of negligent
  failure"**.
- **(a)(4)** "**Prohibit an employable individual from receiving aid under this
  part for more than three months in any 12-month period**, whether or not the
  months are consecutive... **This paragraph shall apply only to those individuals
  who have been offered an opportunity to attend job skills or job training
  sessions.**"
- **(c)** "A county may provide aid... **either by cash assistance, in-kind aid, a
  two-party payment, voucher payment, or check drawn to the order of a
  third-party provider of services** to the recipient."

Now compare the table:

- **Five counties set the residency requirement at exactly 15 days** — Contra
  Costa, Sonoma, Placer, San Diego and San Mateo ("15 consecutive days"). Not 14,
  not 30. **Every verified residency rule sits precisely on the statutory ceiling.**
- **Nine of the eleven counties with a verified time limit set it at three months
  or 90 days in a 12-month period** — Contra Costa, Sonoma, Alameda, Humboldt,
  Lake, Napa, Sierra, Butte, Modoc — which is §17001.5(a)(4) verbatim. San Luis
  Obispo restates it as **12 weeks**. **Marin is the single outlier at 6 months**,
  i.e. twice as generous as the statute allows it to be stingy.
- **The loan-versus-grant question, the voucher question and the landlord-direct
  question are not open at all: §17001.5(c) pre-authorises every form observed.**
  Lake and Napa issue vouchers; Ventura pays the landlord and utility directly;
  San Joaquin pays rent to the property owner; Plumas gives "cash aid and in-kind
  aid"; San Luis Obispo gives "money, vouchers and job-related services". Each is
  a menu item the Legislature wrote down.
- **The sanction ceiling shows up in the legal-aid guide, not on county pages.**
  LSNC tells applicants the county "can bar you from GA for up to 180 days" and
  that three "negligent" failures suffice — both lifted straight from
  §17001.5(a)(3). No county page read in this sweep states its own sanction length.

**What this means for the project.** The naive version of the thesis — a one-line
statute produces unbounded variation — is wrong here, and wrong in an informative
way. **§17000 delegates the *level* and leaves the *structure* to a second statute
that enumerates the permissible moves and caps them.** The counties then do not
scatter; they **stack on the caps**. Where the statute names a maximum, the modal
county adopts the maximum. Where the statute names a menu (§17001.5(c)), counties
pick different items and the variation is real but *bounded by enumeration*. And
where the statute names nothing at all — the **grant amount**, the **asset
limit**, the **SSI-advocacy staffing model** — the spread is enormous:

| Dimension | Statutory treatment | Observed spread |
|---|---|---|
| Grant, single adult | §17000.5 safe harbour formula only; no floor, no ceiling | **$221 (Los Angeles) to $714 (San Francisco) — 3.2×**, on 6 counties that publish it |
| Personal-property limit | nothing | **$75 (Placer) to $2,000 (Los Angeles and San Francisco) — 26.7×** |
| Liquid-asset limit | nothing | **$50 cash (Sonoma) to $2,000 (San Francisco) — 40×** |
| Residency | capped at 15 days | **every verified county sits at exactly 15 days** |
| Employable time limit | capped at 3 months per 12 | **9 of 11 at exactly 3 months; 1 at 12 weeks; 1 at 6 months** |
| Form of aid | menu of 5 enumerated in §17001.5(c) | cash/EBT, vouchers, landlord-direct, utility-direct, in-kind — **all five in use** |

**This is the sharpest instrument the project has found so far**, because the same
statute contains both a capped dimension and an uncapped one, in the same
programme, measured on the same counties. Variance on the capped dimensions is
near zero. Variance on the uncapped dimensions is 3× to 40×. That is a *within-programme*
control for everything that distinguishes counties from one another, and it isolates
the effect of the statutory text itself. **Neither the ADU nor the CCW sweep can do
this**, because in those programmes the state either caps everything (solar permits)
or caps nothing that matters.

## Four template-lineage pairs, caught word for word

The CCW sweep found **one** copy-paste tell (Plumas's portal text referring to
"the LCSO CCW Unit", i.e. Lassen's sheriff — plan §10.7). General Assistance has
**four, all verified by reading both documents in this pass**, and unlike the CCW
case none of them involves a shared vendor: these are counties copying each other's
prose for a programme each is supposed to have designed itself.

**1. San Diego → Inyo (or the reverse).** Identical sentence, three clauses long:

> "General Relief provides temporary cash assistance for eligible county residents
> who have no other means of support. Any aid received must be repaid to the
> county. Completed hours of required Job Training may count toward repayment of
> the debt."
> — [San Diego](https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/general_relief.html)

> "General Assistance/Relief provides temporary cash assistance for eligible
> county residents who have no other means of support. Any aid received must be
> repaid to the county. Completed hours of required Job Training may count toward
> repayment of the debt."
> — [Inyo](https://www.inyocounty.us/aging-social-services/apply-public-assistance)

San Diego has **3.3 million** residents; Inyo has about **19,000**, and they are
not adjacent. The only edit is the programme name.

**2. Butte → Modoc (or the reverse), including a shared typo.** Both publish:

> "provides three months of cash assistance to eligible, employable adults and
> provides longer-term assistance to eligible adults who are temporarily disabled
> or who are awaiting Supplemental Security Income (SSI) approval. California
> Welfare and **institutions** Code Section 17000 states, 'Every county and every
> city and county shall relieve and support all incompetent, poor, indigent
> persons...'"

— [Butte](https://www.buttecounty.net/406/General-Assistance) (web page) and
[Modoc](https://www.countyofmodoc.gov/DocumentCenter/View/621/Cash-Assistance-Programs-PDF)
(PDF leaflet, "Rev. 11/2021"). **The lower-case "institutions" in a statute name
is the fingerprint.** Butte has ~210,000 residents, Modoc ~8,700.

**3. Sonoma → Marin (or the reverse), with the policy number changed.** This is
the most instructive of the four:

> "General **Assistance** provides temporary cash assistance for individuals who
> have little or no money. It can be approved for up to **90 days** in a 12-month
> period, and possibly longer for people with disabilities."
> — [Sonoma](https://sonomacounty.gov/health-and-human-services/human-services/jobs-money/general-assistance-cash-assistance-for-individuals)

> "General **Relief** provides temporary cash assistance for individuals who have
> little or no money. It can be approved for up to **6 months** in a 12-month
> period, and possibly longer for people with disabilities."
> — [Marin](https://www.marinhhs.org/general-relief)

Adjacent counties, identical sentence, **the one substantive parameter doubled**.
The shared text does not merely fail to disclose the difference — it *actively
disguises* it, because a reader who has seen Sonoma's page will not re-read
Marin's closely enough to notice the number moved.

**4. Lake → Napa (or the reverse), an entire page and a shared redesign date.**
Lake County's General Relief page and Napa County's General Assistance page are
**the same document end to end**: the same "Effective **May 1, 2020**, the
programme will be changing" banner, the same required **monthly in-person meeting
with the Eligibility Specialist to collect vouchers**, the same **ten calendar
day** change-reporting rule, the same "**3 full calendar months in a calendar
year**... continue in **3 month extensions** if you have been fully participating
in your employment plan", the same "available and willing to accept employment of
**at least thirty (30) hours per week**" schooling rule, the same **3 months of
aid toward a security deposit**, and the same repayment paragraph ending in a
**bill in the mail for the entire amount**. Both pay in **vouchers**. Lake and Napa
are adjacent. Two counties redesigned their §17000 programmes identically,
effective the same day.
— [Lake](https://www.lakecountyca.gov/1666/General-Relief), [Napa](https://www.napacounty.gov/376/General-Assistance)

**Why four pairs matters more than one.** The CCW finding was that *a vendor*
manufactures false agreement. Here there is no vendor: county staff copied
neighbouring counties' text, or a shared consultant did. **The false-agreement
channel therefore is not vendor-specific — it is a general property of how small
public bodies write their public documents**, and it should be modelled as a
county-to-county copying process, not only as a platform effect. Pair 3 is the
dangerous case for a solver and for a Bayesian model: **the text is identical and
the policy is not**, so textual similarity is actively anti-correlated with
informational independence.

## The litigation map, and the natural experiment it creates

The three cases named in the packet all resolve to specific counties, and the
docket is far more concentrated than the packet assumed.

| Case | County | What it did | Provenance |
|---|---|---|---|
| **Boehm v. County of Merced** (1985) and **Boehm v. Superior Court (County of Merced)** (1986) 178 Cal.App.3d 494 | **Merced** | Merced cut GA from **$198 to $175** a month for an individual in July 1983, then to $185 after two needs studies. Held: a county acts "arbitrarily and capriciously" if it cuts GA without a needs study, **and** that a study covering only food and housing is legally insufficient — "without a study which establishes that the other basic necessities — **clothing, transportation and medical care** — are otherwise provided," the grant "as a matter of law, do[es] not conform to the mandate of... section 17000". Writ granted compelling a preliminary injunction | opened by the earlier `codex-ga` pass and cached at `corpus/counties/raw/general_assistance/002-state-and-opinions.json`; `law.justia.com` now **403s to this session** |
| **Hunt v. Superior Court (Guimbellot)** (1999) 21 Cal.4th 984 | **Sacramento** | Sacramento limited county medical care to residents financially eligible for GA, and argued that declining the §17000.5 **$40/month medical credit** let it stop providing medical care altogether. Supreme Court **reversed the Court of Appeal**: "**Section 17000 — not section 17000.5 — prescribes the extent of a county's obligation to provide medical care**", the duty extends beyond the GA-eligible class, and §17000.51 confirms the §17000.5 standard of aid "is **not intended to satisfy, in whole or in part**, a county's duty to provide health care services under section 17000" | [scocal.stanford.edu](https://scocal.stanford.edu/opinion/hunt-v-superior-court-guimbellot-31966) (opened) |
| **Bell v. Board of Supervisors** (1994) 23 Cal.App.4th 1695 | **ALAMEDA** — not, as often assumed, a generic case | Full caption: "**CHARLES BELL et al. v. BOARD OF SUPERVISORS OF ALAMEDA COUNTY**", consolidated with **Burks v. Knudson** (Helen Knudson, as Director) and **Beal v. Board of Supervisors of Alameda County** | CourtListener search API (opened) |

Three further §17000 GA cases surfaced in the same search and locate more counties:

- **Bell v. Board of Supervisors of SAN JOAQUIN COUNTY** (1976) 55 Cal.App.3d 629 — a second, much earlier *Bell*, different county. Anyone citing "Bell" in this literature must say which.
- **A Contra Costa case on §17000.5 shared housing**, whose opinion text reads: "Judgment was entered against **Contra Costa County**, its board of supervisors and the director of its social service department... which prevented the County from reducing general assistance benefits to recipients living with family members who are not responsible for their support. **We hold that Welfare and Institutions Code section 17000.5 authorizes reduced benefits if the recipient shares housing with relatives**" — i.e. the shared-housing reduction in §17001.5(a)(2) was litigated in Contra Costa.
- **Gardner v. County of Los Angeles** (1995) 34 Cal.App.4th 200 — held Los Angeles **could not** deduct the value of participation in a county health plan (**$73/month**) from GA grants, discussed at length in *Hunt*.

**The county docket, by frequency of appearance in the CourtListener §17000 /
general-assistance result sets** (case names are reliable; individual
date-and-citation pairings in the browsable API output were not cleanly separable
and are therefore not reported):

- **Alameda — 5**: Bell, Burks, Beal, *Watkins v. County of Alameda*, *McCormick v. County of Alameda*, *Cleary v. County of Alameda*, plus *County of Alameda v. State Board of Control*
- **Contra Costa — 3**: *Oberlander v. County of Contra Costa*, *Freitas v. County of Contra Costa*, *Taylor v. County of Contra Costa*
- **Los Angeles — 4**: *Zobriscky v. Los Angeles County*, *Mendly v. County of Los Angeles*, *Gardner v. County of Los Angeles*, *La Alliance for Human Rights v. County of Los Angeles*
- **San Diego — 2**: *Alford v. County of San Diego*, *County of San Diego v. State*
- **Merced — 1** (Boehm), **Sacramento — 1** (Hunt), **San Joaquin — 1** (Bell 1976), **Yolo — 1** (*Guidotti v. County of Yolo*)
- Also in the result sets, county not verified by this pass: *Tailfeather v. Board of Supervisors*, *Whitfield v. Board of Supervisors*, *Welfare Rights v. Frank*, *Poverty Resistance Center v. Hart*, *Sagaser v. McCarthy*

**The natural experiment lands, and it lands hard.** Rank the 58 counties by how
much they publish about their GA programme, and the top two are **Alameda** and
**Contra Costa** — the two most-litigated counties in the state:

- **Alameda** is the only county in the 58 that publishes a **complete GA
  regulation manual** (2,667 lines, sectioned 9-1 through 9-6, "Pursuant to
  Alameda County General Code – Title 7"), **fourteen separately numbered handbook
  sections** as individual PDFs, a **grant schedule**, an **administrative-hearing
  chapter**, and a **standing public-comment process for regulation changes**.
  Alameda lost *Bell*, *Burks* and *Beal* and has been sued at least four more times.
- **Contra Costa** is one of only six counties that publish a **dollar grant
  figure** ($336 single / $454 couple), and it publishes its **named forms**
  (GA 201 E, GA 201 B, SSP-14, QR7, QR3), its **90-day time limit**, its **$500
  property limit**, its **15-day residency rule** and its **SSI-advocacy mandate**.
  Contra Costa litigated the shared-housing reduction and has been sued at least
  twice more.
- By contrast **Merced**, litigated in *Boehm* — the case that created the whole
  adequacy doctrine — publishes **three sentences**: that GA is for people without
  a child in the home, that it is "a temporary solution", and that recipients must
  look for work. **No grant, no time limit, no loan status, no process beyond
  "walk in and apply".**
- And **Sacramento**, litigated in *Hunt*, is one of the 24 counties in Table B:
  **six guessed paths 404, no sitemap, no readable GA page at all.**

So the relationship is **not** "litigation → disclosure" as a simple rule. It is
better described as: **litigation over the *standard of aid* produces a published
standard of aid** (Alameda, Contra Costa — both litigated on grant computation and
shared-housing reductions, both now publish grant tables), **while litigation over
*adequacy* or *medical care* leaves the published record untouched** (Merced,
Sacramento). That is a testable distinction, and it is exactly the kind of
mechanism the project wants: the *subject* of the court's order, not the mere fact
of litigation, is what becomes legible afterwards. **A clean design is available**:
Alameda vs. its neighbours on grant-schedule publication, with Merced and
Sacramento as litigated-but-non-publishing controls.

## Coverage audit: how thin is the evidence, honestly

Every count below is a count of what **this** pass reached, with WebSearch
unavailable and every search engine blocked. A better-resourced pass would do
better on the blocked hosts. It would not do much better on the counties that
publish nothing, because those were reached and read.

| Outcome | Counties | Share |
|---|---|---|
| Readable GA/GR programme text located | **29** | 50% |
| A GA/GR page exists and serves **no programme text** (Santa Barbara, San Bernardino) | 2 | 3% |
| Website fully readable, **no GA page anywhere on it** (Alpine, Trinity, Calaveras, Stanislaus, Del Norte, Lassen) | **6** | 10% |
| Every official host **403s or fails DNS** | **20** | 34% |
| Hosts resolve but no path found (Sacramento: 6 × 404, no sitemap) | 1 | 2% |
| **Total** | **58** | 100% |

And within the 29 that yielded text:

| Fact | Counties publishing it | Share of 58 |
|---|---|---|
| **A dollar grant figure for a single adult** | **6** — LA $221, Ventura $310, Alameda $336, Contra Costa $336, Marin $387, San Francisco $714 | **10%** |
| An income limit (not the grant) | 4 — San Diego $598, SLO $355, Marin $387, SF $714 | 7% |
| A personal-property or asset limit | 11 | 19% |
| An explicit time limit with a number | **11** | **19%** |
| Explicit loan / repayable status | **17** | 29% |
| A lien provision but not the word "loan" | 2 — LA, Placer | 3% |
| **Any statement that GA is a non-repayable grant** | **0** | **0%** |
| A work or job-search requirement | 18 | 31% |
| An SSI-advocacy function | 17 | 29% |
| **A published policy, handbook or regulation document** | **1 — Alameda** | **2%** |

### Comparison with the ADU and CCW sweeps

| | ADU | CCW | **General Assistance** |
|---|---|---|---|
| Counties with a substantive published page | 48 / 58 | **48 / 58** (vendor-authored) | **29 / 58** |
| Counties publishing a policy document | — | 6 / 43 in the large pass | **1 / 58** |
| Counties publishing the headline number (fee / grant) | — | **35 / 35 live portals published a fee** | **6 / 58 published a grant** |
| Scripted-fetch block rate | — | **14 / 58 = 24%** | **20 / 58 = 34% fully blocked; 22 / 58 = 38% block at least one official host** |
| Who authored the text | county / consultant | **one vendor for 48** | county staff, with **4 verified copy-paste pairs between counties** |

**The contrast on the headline number is the finding.** For CCW, **every single
one of the 35 live portals published its fee** — because a fee is a payment the
applicant must make, so it has to be on the page for the transaction to work.
For General Assistance, **6 of 58 publish the grant** — because the grant is a
payment the county must make, and nothing in the transaction requires the
applicant to know it in advance. **The direction of the money determines whether
the number is published.** That is a general mechanism, it is testable on any
other programme pair, and it is a much better explanation of disclosure than
county capacity: San Francisco (population 810,000) publishes its grant and
Los Angeles (9.7 million) publishes its grant, while Fresno, Kern, Riverside,
Sacramento and Santa Clara — all large — publish nothing reachable.

**The block rate rose from 24% to 34%, on the same 58 counties, three weeks
apart.** Same method, same user-agent, largely the same hosts. In CCW the sheriff's
*vendor* was reachable even when the county was not — Permitium has no WAF — so
the county's own block was survivable. General Assistance has **no vendor**, so a
county WAF is terminal. **A shared platform is, perversely, an availability
guarantee**, and its absence is why this programme reads as so much darker than
CCW even though both sets of counties block at similar rates.

### Failure modes observed, extending plan §10.6

The CCW sweep named four non-403 failure modes. This sweep confirms all four and
adds three:

1. **Blocked** — 20 counties, 403 to both curl and WebFetch.
2. **Present-but-unparseable** — Santa Barbara's GR page (296 KB, no text), San
   Bernardino's (160 KB, no text), Placer's FAQ answer to "how much will my
   benefits be?" (the question is in the HTML, the answer is not).
3. **Misrouted** — Orange returns **404 with a 150 KB body** on four guessed
   paths; Imperial returns **404 with a 394 KB body**.
4. **Stale / dead host** — `co.tehama.ca.us`, `tehamacountysocialservices.org`,
   `icdss.imperialcounty.org`, `dpss.rivco.org`, `kernhumanservices.com`,
   `co.shasta.ca.us`, `co.tuolumne.ca.us`, `hsd.santacruzcountyca.gov` — **eight
   official-looking county human-services hosts that no longer resolve**.
5. **NEW — zero-byte 404.** Yuba returns a **0-byte body with a 404** on every
   path including `/sitemap.xml`. Nothing to parse, nothing to diagnose.
6. **NEW — readable site, absent programme.** Six counties' sites were read in
   full (sitemap and/or site search) and simply **have no GA page**. This is not a
   retrieval failure and must not be scored as one: the document does not exist.
   It is the strongest single form of evidence about disclosure, and only an
   exhaustive read can establish it.
7. **NEW — the canonical host blocks and a non-canonical one serves.** Marin's
   `marincounty.gov` 403s while `marinhhs.org` serves the whole programme;
   San Bernardino's `hs.sbcounty.gov` 403s while `wp.sbcounty.gov` answers — and
   `wp.` is a WordPress back-door hostname no pattern would predict. **The
   reachable host is not the advertised one**, which generalises the CCW lesson
   that the vendor's slug was more guessable than the county's URL.

### Retrieval infrastructure notes for later packets

- **WORKS, keyless:** `https://www.courtlistener.com/api/rest/v4/search/?q=...&type=o`
  — full case metadata including `caseNameFull`, which is how *Bell* was pinned to
  Alameda. **This is a new verified asset and should be added to WORK_PACKETS.**
- **WORKS, keyless:** `https://api.municode.com/Clients/stateAbbr?stateAbbr=CA`
  returns all 237 California Municode clients with IDs, of which **37 are counties**
  (full list in `corpus/counties/raw/ga/api_mc_ca.json`). `Clients/{id}` also works.
  But `library.municode.com/...` serves a **6,095-byte Angular shell** to every
  script, and `codesToc` / `CodesContent` require a `jobId` with no discoverable
  index, so **the code text itself stayed out of reach**.
- **WORKS:** **county `sitemap.xml`** (12 of 24 counties tried) and the
  **CivicPlus site-search endpoint** `/-/Search/Results?searchPhrase=...`. The
  search endpoint found Napa's GA page, which is **absent from Napa's own sitemap**,
  so the two channels are complementary and both are worth trying.
- **WORKS, one-shot only:** `https://html.duckduckgo.com/html/?q=...` via curl.
  It answered the **first** query of the session and then returned DuckDuckGo's
  `anomaly.js` challenge to every subsequent query, permanently. Treat it as a
  single-use resource, not a search tool.
- **DEAD:** `codelibrary.amlegal.com` (403 all paths); `r.jina.ai` reader proxy
  (Cloudflare-gated, 403); `law.justia.com` (403, though it served the same page
  to the earlier pass hours before); `web.archive.org/cdx` (**still** returning
  "Internet Archive: Temporarily Offline" — the P8 note that this looked transient
  should be revised); `bing.com/search?...&format=rss` (200 but discards the query);
  Mojeek (CAPTCHA), Ecosia (403), Brave (429), searx.be (JS challenge),
  priv.au and searxng.site (429), Startpage (no parseable results).
- **NOTHING THERE:** `data.ca.gov` CKAN has **no** General Relief dataset
  (`package_search?q=general+relief` → `count: 1`, a kelp-forest study).

## Verdict: is General Assistance the best test of the rural-data-poverty question?

**No — but it is the best test of something more valuable, and the reason it fails
the rural test is itself the answer.**

### Why it is not the best rural-data-poverty test

The rural-data-poverty hypothesis is that **small counties are dark because they
are small**: no local newspaper, no forum, no vendor, thin staff. To test that you
need the *size* signal to be separable from everything else. In this programme it
is not:

1. **The publication gradient does not track population.** The six counties that
   publish a grant amount are Los Angeles (9.7 m), San Francisco (810 k), Alameda
   (1.6 m), Contra Costa (1.1 m), Marin (260 k) and Ventura (840 k) — but the
   large counties that publish **nothing reachable** are Santa Clara (1.9 m),
   Riverside (2.4 m), San Bernardino (2.2 m), Fresno (1.0 m), Kern (920 k) and
   Sacramento (1.6 m). **Six of the ten largest counties in California are dark on
   General Assistance.** Meanwhile tiny Mono (13 k), Sierra (3 k), Colusa (22 k),
   Mariposa (17 k), Inyo (19 k), Plumas (19 k) and Modoc (8.7 k) all have readable
   GA pages. **Sierra County — population 3,000, the smallest but one — publishes
   its time limit. Santa Clara, 630 times larger, publishes nothing at all.**
2. **The block rate confounds it fatally.** 20 of 58 counties are dark because of
   a **web application firewall**, which is a procurement decision, not a capacity
   one — and the WAF-blocked set skews *large*. You cannot measure rural darkness
   through an instrument whose loudest signal is "this county bought Cloudflare".
3. **The tiny counties are not dark; they are terse.** Alpine, Trinity and
   Calaveras publish nothing, which supports the hypothesis. But Sierra, Modoc,
   Mono, Colusa, Mariposa, Inyo and Plumas publish a paragraph each — thin but
   present, and *more* than Santa Clara or Riverside publish. Of the nine tiny
   counties the packet named, **six have a readable GA statement and three do not.
   That is a 2:1 split, not a blackout**, and it will not carry a covariate model.
4. **The confound cannot be removed by better retrieval**, because the mechanism
   found in §"the direction of the money" above — that counties publish numbers
   the applicant must pay and withhold numbers the county must pay — operates at
   *every* county size. Size is not the variable doing the work.

**For the rural-data-poverty question, the CCW sweep remains the better
instrument**, precisely because the vendor removes the availability confound: with
Permitium authoring 48 of 58 pages, a county's *own* darkness is measurable
against a constant baseline, and the residual really is county-specific. General
Assistance has no such baseline.

### What General Assistance *is* the best test of

It is the best available test of the project's actual thesis — **that
cross-jurisdiction variation measures what a statute leaves undetermined** —
because it is the only programme found so far where **the statute itself
partitions its own dimensions into capped and uncapped**, on the same counties, in
the same document, at the same time:

- **Capped dimensions** (§17001.5: 15-day residency, 3-month employable limit,
  15/20/25% shared-housing reduction, 180-day sanction, five enumerated forms of
  aid) → **variance collapses onto the cap**. Every verified residency rule is
  exactly 15 days. Nine of eleven time limits are exactly 3 months.
- **Uncapped dimensions** (grant amount, asset limit, liquid-asset limit,
  SSI-advocacy staffing, work-programme design, whether the grant is even money)
  → **variance of 3.2× to 40×**.

That is a within-programme, within-county, within-statute control. Every
alternative explanation for between-county variation — wealth, politics, staff
capacity, urbanity, caseload, vendor, legal exposure — is **held constant across
the two sets of dimensions**, because they are the *same counties* on the *same
day* in the *same programme*. The only thing that differs is whether the
Legislature wrote a number down. **This is the cleanest identification of the
"statutory silence → variation" mechanism the project has.**

Three further reasons to keep it:

- **It is the only programme in the sweep where the form of the benefit varies.**
  Lake and Napa pay vouchers; Ventura pays the landlord; San Joaquin pays the
  property owner; Plumas pays partly in kind; San Francisco pays cash on an EBT
  card with free MUNI passes. A decision tree over "what does the applicant
  receive" has five distinct leaves, all statutorily pre-authorised. No other
  programme swept has that.
- **It is the only programme where the aid is a debt.** 17 counties state the
  benefit is a repayable loan, two more impose a lien, and **not one county in the
  58 states that GA is a non-repayable grant.** A programme in which the benefit
  creates a liability, and a homeowner must sign a lien to receive subsistence aid,
  is a decision tree with a *post-hoc* branch — the outcome depends on events after
  the decision (does the applicant later get SSI, sell a home, or find work).
  Nothing in the synthetic world models that.
- **The litigation gives traceable causation on a subset.** Alameda and Contra
  Costa publish their standards of aid because they were sued over how they
  computed them. That is a rare case where a document's *existence* has a known
  cause.

### Recommendation

1. **Adopt General Assistance as the primary real-world case for the
   statutory-silence mechanism**, replacing the assumption that variation breadth
   alone is the measurement. The measurement is the **contrast** between capped and
   uncapped dimensions of one statute. Report it as the ratio of between-county
   variance on uncapped dimensions to that on capped dimensions.
2. **Keep CCW as the primary case for the rural-data-poverty question** and drop
   GA from that role. Record in the county-covariate work that **GA darkness is
   WAF-driven and size-inverted**, so it must not be used as a rural-information
   covariate.
3. **W2 generator change.** The synthetic statute currently delegates
   dimension-by-dimension. It should instead have **two statutes in a hierarchy**:
   a one-line mandate plus a **second, later "restriction-enabling" statute** that
   enumerates permitted local restrictions and caps each. Jurisdictions should then
   be given a strong prior toward **adopting the cap exactly** on capped dimensions
   and a wide policy effect on uncapped ones. Without this, the generator cannot
   produce the single most striking real-world pattern found today: near-zero
   variance where the law names a number and 40× variance where it does not.
4. **W2 generator change.** Add a **county-to-county document copying process**
   distinct from the vendor channel: a jurisdiction adopts a neighbour's document
   verbatim and edits **only the parameters it disagrees with** (the Sonoma/Marin
   90-days-vs-6-months case). This is strictly harder for a solver than the vendor
   channel, because the surviving differences are exactly the load-bearing ones.
5. **Add to `blocked_sources` / `verified_assets` in WORK_PACKETS.json**: the
   CourtListener keyless search API and `api.municode.com/Clients/stateAbbr` as
   verified assets; `codelibrary.amlegal.com`, `r.jina.ai`, every search engine,
   and the still-offline Wayback CDX as blocked.
6. **What a follow-up pass should do first**, in priority order: (a) the 20
   WAF-blocked counties need a real browser — the `claude-in-chrome` tooling, not
   curl; (b) Alameda's 14 GA Handbook PDFs are fetched-able and would give the
   only complete decision tree available for any county; (c) the CDSS **GR 237
   workbooks** for FY 2024-25 and 2025-26 give per-county caseload and expenditure,
   from which **average grant per case can be computed for all 58 counties** —
   that is the one route to a 58-county grant number, and it was not attempted
   here because it is an arithmetic derivation rather than a published rule and
   deserves its own packet; (d) county board-of-supervisors resolutions, since
   §17001 requires the board to adopt the standards of aid, so **every county's
   grant amount exists in a board minute** even where no web page carries it.

## Provenance summary

- 29 counties read from their own published text; 2 with a page that served none;
  6 with fully-read sites and no GA page; 20 blocked; 1 with no reachable path.
- 4 template-lineage pairs verified by reading both documents.
- 4 statutory sections opened at leginfo (§17000, §17001, §17000.5, §17001.5).
- 3 cases pinned to counties (Merced, Sacramento, Alameda) plus 5 more counties
  identified from case captions.
- Roughly 165 fetches, above the ~120 budgeted; the overage is entirely the
  alternate-host retries forced by the 34% block rate and the search-engine
  outage.
- All artifacts cached under `corpus/counties/raw/ga/`; the earlier pass's search
  transcripts remain at `corpus/counties/raw/general_assistance/`.
- Nothing committed. `benchmark/synth/` and `pipeline/procbench/` untouched.
