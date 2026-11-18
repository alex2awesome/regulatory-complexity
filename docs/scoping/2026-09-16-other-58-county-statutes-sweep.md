# Sweep and ranking of every other 58-county process

2026-09-16. Work packet **P6-OTHER-STATUTES-SWEEP** of
[WORK_PACKETS.json](WORK_PACKETS.json), covering
[plan §2 workstream A6](../2026-09-16-county-scale-up-plan.md#a6-sweep-of-every-other-58-county-process).
This file is insurance: it checks that the project has not picked the wrong
programmes to model, then ranks everything, including the five programmes that
already have their own packets.

## Method and its limits

**WebSearch was exhausted (200/200) before this packet started**, so nothing
below came from a search engine. Every fact came from one of three routes:

1. the **keyless CKAN APIs** of `data.ca.gov` and `data.chhs.ca.gov`
   (`package_search`, `package_show`, `organization_show`), which index most
   state datasets and can be searched programmatically;
2. `curl -L` with a browser user-agent against a department's own site, with
   link extraction from the returned HTML;
3. `WebFetch` as the fallback on a 403.

Where a candidate's outcome data was found, **it was downloaded and parsed**, and
the row counts, county counts, date spans and value ranges quoted here were
computed from the file rather than read off a landing page. Where it was not
found, the candidate says **"not verified"**, meaning not confirmed by these
means — never "does not exist".

Two axes are weaker than the others by construction and are labelled as such:

- **(c) user-generated evidence volume.** No per-programme forum measurement was
  made in this packet; that is packet A8's job and it was still running. Scores
  on (c) are reasoned from programme structure plus the one measured fact
  available, namely that forum availability scales with county population
  (r = 0.74) and nine counties have no subreddit at all
  ([covariates](2026-09-16-county-covariates.md)). Each (c) score therefore
  carries its basis. Where a programme's *client population* is itself concentrated
  in rural counties, that is stated as an expected inversion, not a measurement.
- **(d) gold-standard process-document feasibility** is scored on documents
  actually located, with URLs, not on an expectation that a county "must" publish
  something.

Scores are 1–5. A score of 5 on (b) is reserved for a per-county dataset that
carries an **elapsed duration or a deadline-compliance count**, not merely a
volume.

---

## 1. Medi-Cal eligibility determination — the strongest new find

Basis: Welf. & Inst. Code §14000 et seq.; 42 CFR 435.912 sets the 45-day
determination standard (90 days on a disability basis). Administered by the 58
county welfare departments under DHCS supervision, on the same statewide SAWS
platform as CalFresh.

### (a) Cross-county process variation — **4**

- The **SAWS consortium lineage is observable per county-month**, as a labelled
  column in the DHCS renewals dataset, with four values: `CalWIN`, `C-IV`, `LRS`
  and `CalSAWS`. This matters beyond Medi-Cal: plan §2 A7 lists legacy-consortium
  membership as **blocked** because calsaws.org names no member counties
  ([blocked_sources](WORK_PACKETS.json)). This dataset resolves it as a
  by-product — 58 counties × 98 months of consortium labels, so the migration
  date of every county is recoverable.
  [package](https://data.chhs.ca.gov/api/3/action/package_show?id=medi-cal-annual-renewals-by-county)
- **The ex parte automation rate is a county-level process choice and it varies
  by a factor of 1.5.** Pooling 2018–2026, automatic ex parte renewals as a share
  of completed renewals run from 0.362 (Napa) and 0.365 (Colusa) to 0.533
  (Alameda) and 0.526 (Sonoma). An ex parte renewal is one the county completes
  from data it already holds, without contacting the beneficiary; the
  auto-versus-manual split is exactly a "does this county's process include a
  human step here" observable. Computed from the dataset below.
- **Whether the county runs a reportable Medi-Cal call centre at all varies**: of
  58 counties, 34 report under SB 1289 and 25 do not (see (e)).

Risk, stated plainly and inherited from the CalFresh finding: Medi-Cal eligibility
rules are state-uniform and the platform is now single-vendor statewide, so this
is *performance and route* variation, not rule variation. The
[CalFresh packet](2026-09-16-calfresh-58-counties.md) reached the same verdict for
its programme: "no for reported performance; not established for every process
route". Medi-Cal inherits both halves of that.

### (b) Per-county official outcome or timing data — **5**

**[Medi-Cal Annual Renewals by County](https://data.chhs.ca.gov/dataset/6160a936-001a-4c45-a531-527e28096cee/resource/25736aa0-3f63-4d74-aaa6-5b432d53cbc0/download/med-abx11-5.1-renewal-jan-2026-and-feb-2026-cdo_v2.csv)**,
published under W&I Code §14102.5(3). Downloaded and parsed: **11,368 rows = 58
counties × 98 renewal-due months (2018-01 through 2026-02) × 2 eligibility
methods (MAGI, non-MAGI)**; 1,392 rows per complete year, which is exactly
58 × 12 × 2, so the panel is structurally complete. Columns: renewals due,
renewals completed, **renewals completed by the due date**, continued
eligibility, auto ex parte, manual ex parte, discontinued for failure to respond,
discontinued over income/property, discontinued other, reinstated, plus an
annotation code distinguishing "cell suppressed for small numbers" from
"complementary cell".

Pooled 2018–2026, the **share of renewals completed by the due date** runs:

| slowest | rate | fastest | rate |
|---|---:|---|---:|
| Colusa | 0.564 | Alpine | 0.842 |
| Napa | 0.590 | Sierra | 0.803 |
| Alameda | 0.590 | Kings / Imperial | 0.766 |
| Sonoma | 0.596 | Amador | 0.745 |
| San Mateo | 0.602 | Del Norte | 0.735 |

Median of the 58 county rates: **0.669**. This is a deadline-compliance measure
on a statutory clock, per county, per month, for eight years — the same
measurement type as CalFresh's CF 296 over-30-day counts, but monthly-by-county
in a single CSV rather than in per-fiscal-year encrypted workbooks.

Note the sign: **the small rural counties are at the fast end and three large Bay
Area counties at the slow end.** That replicates the APR finding that rurality
correlates *negatively* with processing time
([APR timing §3](2026-09-16-apr-permit-timing.md)), now on a completely different
programme and a completely different measurement. Two independent programmes
agreeing that rural is not slower is a real result for the plan's §10.5 claim.

**[County Medi-Cal Call Center Data](https://data.chhs.ca.gov/api/3/action/package_show?id=county-medi-cal-call-center-data)**,
published under SB 1289 (Roth, Ch. 792, Stats. 2024). Downloaded and parsed:
204 rows, **34 counties × 6 months (Jan–Jun 2026)**, three measures — total call
volume split into during/after working hours, **average call wait time as an
actual HH:MM:SS duration, stratified by 20 languages**, and average call
abandonment rate. January 2026 wait times for all languages: Alameda 0:25:24,
Butte 0:41:35, **Contra Costa 1:00:27**. This is a genuine elapsed duration of a
step an applicant experiences, per county, which almost nothing else in the
project's inventory has.

Caveats recorded, all of them verified against the files: the **call-centre**
CSVs carry a two-row title banner above the header, so a naive `csv.DictReader`
returns garbage and the header must be found by scanning; in the **renewals**
CSV all 58 counties are present but San Diego's label is `"San Diego "` with a
trailing space, which will silently break a join unless keys are stripped; the
first column name carries a UTF-8 BOM; counts are comma-formatted strings, not
numbers; and DHCS suppresses cells with underlying volume 1–10, flagging them
through the annotation code rather than by blanking.

**Not verified:** a per-county *application* processing-timeliness dataset — the
45-day standard's own compliance rate. Six `package_search` queries on
`data.chhs.ca.gov` ("Medi-Cal applications county", "Medi-Cal application
processing", "14102.5", "county eligibility", "renewals due", "county
performance") returned the renewals and call-centre datasets and enrolment
counts, but nothing on application determination time. The plan's reference to
"DHCS county performance dashboards" is **partly confirmed** (renewals and call
centre are exactly that) and **partly unconfirmed** (no application-timeliness
dashboard located by these means).

### (c) User-generated evidence volume and skew — **4** (inferred, not measured)

Medi-Cal is the largest county-administered programme in the state by client
count, so raw forum volume should exceed every other candidate here except
CalFresh. The expected skew is the standard one (population r = 0.74). Inferred
from programme scale and the covariate result, not measured in this packet.

### (d) Gold-standard process-document feasibility — **3**

County-specific eligibility policy is published by some large counties and not
by small ones. Confirmed by another packet on an adjacent programme: Santa Clara
publishes its DEBS **program handbooks** as browsable HTML
(`https://stgenssa.sccgov.org/debs/program_handbooks/...`) and LA DPSS publishes
ePolicy ([GA packet](2026-09-16-general-assistance-58-counties.md)). Statewide
process documents (ACWDLs, MEDILs) are abundant but do not distinguish counties,
which is the wrong axis for this project. So: two or three excellent gold
counties, a long tail with nothing county-specific.

### (e) Rural coverage — **4**, with a measured official-data gap

Renewals cover all 58 counties including Alpine (1,605 renewals due over eight
years) and Sierra (5,235), so the official panel is complete even at the
smallest scale. But the call-centre file covers **34 counties and omits 25**:
Alpine, Amador, Calaveras, Colusa, Del Norte, El Dorado, Glenn, Imperial, Inyo,
Lake, Lassen, Madera, Mariposa, Mendocino, Modoc, Mono, Nevada, Plumas,
San Benito, Sierra, Siskiyou, Tehama, Trinity, Tuolumne. Every one of the 25 is a
small or rural county. **That is the rural-data-poverty hypothesis appearing
inside official state data rather than in user data**, which is a sharper version
of the claim than the forum version, and it is new.

**Total: 20/25.**

---

## 2. Child support through the Local Child Support Agencies

Basis: Family Code §17000 et seq.; Title IV-D of the Social Security Act;
45 CFR 303 timeframes (e.g. case opening in 20 days, locate attempts in 75 days).
Administered by Local Child Support Agencies under DCSS on a single statewide
system (CSE).

### (a) Cross-county process variation — **2**

The programme is the most centralised of all the candidates: one statewide case
management system, federally prescribed timeframes, and state-issued forms. The
structural variation that does exist is **agency consolidation** — the plan notes
~47 LCSAs for 58 counties, so some agencies serve more than one county. **Not
verified:** the LCSA count and which counties share an agency.
`childsupport.ca.gov` returns **HTTP 403 to every `curl` path tried** (`/`,
`/data-and-reports/`, `/reports-and-data/`) and WebFetch resolved only its
navigation. A programme where the agency boundary does not match the county
boundary is also a poor fit for a design whose unit of analysis is the county.

### (b) Per-county official outcome or timing data — **3**

The state portals carry exactly **four** DCSS datasets — confirmed by
`organization_show`, which reports `package_count: 4`
([DCSS org](https://data.ca.gov/api/3/action/organization_show?id=california-department-of-child-support-services&include_datasets=true)).
All four are per-county annual counts, downloaded and parsed:

| dataset | shape verified | measure |
|---|---|---|
| [Case Overview](https://data.chhs.ca.gov/dataset/1270d2c8-4beb-4e14-a6b9-4e739ce1efe0/resource/13d8025d-0621-481a-b9db-84e01f8f60a0/download/dcss-case-overview.csv) | 2,552 rows = 58 counties × 11 years (2015–2025) × 4 case types | caseload by public-assistance status, with each type's share of the county caseload |
| [Paternity Establishment](https://data.chhs.ca.gov/dataset/60aabbbd-bd37-4e2d-aa5f-bbbc872e6310/resource/d9b60447-87b4-43ca-91c7-96476b70cb6d/download/dcss-paternity-establishment.csv) | 638 rows = 58 counties × 11 federal fiscal years 2015–2025 | children with paternity established in the year (Alpine 1 in 2015, Alameda 5,565) |
| Distributed Collections by Assistance Type | per county, by assistance status | dollars collected |
| Children in Child Support Cases | per county | children in caseload |

Paternity establishment is one of the five federal performance measures, so this
is genuine performance data. **But there is no clock in any of the four**, and
the plan's premise — "excellent federal per-agency performance data" — is
**not verified**. DCSS's own transparency page publishes two statewide-only
dashboards (["More Money to Families"](https://childsupport.ca.gov/supportdata/),
["Changes to California Law"](https://childsupport.ca.gov/passthroughdata/)) and
tells anyone wanting more to file a Public Records Act request
([transparency page](https://childsupport.ca.gov/transparency/)). It cites an
"FFY 2024 Comparative Data for Managing Program Performance" report, which is the
document that would contain per-LCSA measures; **it was not located** — the site
search returned nothing and `acf.gov/css/data` returns 403 to WebFetch. This is a
lead worth one fresh-session search, not a settled negative.

### (c) User-generated evidence volume and skew — **2** (inferred)

Child support is discussed heavily online but almost always as a legal-outcome
question rather than a county-process one, and posters have strong privacy
reasons not to name their county or agency. Inferred, not measured.

### (d) Gold-standard process-document feasibility — **2**

One statewide system and state-issued forms means the documents a solver would
retrieve are largely identical across agencies — the CCW "shared vendor
platform" failure mode (plan §10.1) but structural rather than accidental, and
therefore not even interesting as a measurement.

### (e) Rural coverage — **2**

Data covers all 58 counties, but the agency-to-county mismatch means small
counties may not be independent process draws at all.

**Total: 11/25.**

---

## 3. Property tax assessment appeals

Basis: R&T Code §1601–1645; the §1604(c) **two-year clock** within which the
county board must hear and decide an application or the applicant's opinion of
value becomes the assessed value; Property Tax Rules 301–326; BOE oversight under
Gov. Code §15640–15646.

### (a) Cross-county process variation — **5**, the highest of any candidate

- **Counties choose their adjudicating body.** The BOE states that "in all
  counties in California, either one or more assessment appeals boards **or** a
  county board of supervisors perform the duties of a local board of
  equalization"
  ([BOE assessment appeals](https://www.boe.ca.gov/proptaxes/asmappeal.htm)).
  One county convenes a specialist three-member board, another has several, a
  third has its elected supervisors hear valuation disputes. That is a
  jurisdiction-level structural decision on the same statute, visible in a public
  document, and it is the cleanest analogue in the whole sweep to the septic
  Tier 1/Tier 2 choice that plan §10.8 singled out.
- **Each county adopts its own rules of procedure** and its own local forms
  through the Clerk of the Board, on top of the state-prescribed BOE Form 305-AH.
  The BOE maintains the per-county Clerk of the Board directory that indexes them
  ([county contacts](https://www.boe.ca.gov/proptaxes/countycontacts.htm)).
- **The two-year clock has a waiver**, so whether a county routinely obtains
  written waivers versus deciding inside two years is a county practice with a
  statutory consequence.

### (b) Per-county official outcome or timing data — **2**

This is the candidate's weakness and it was checked hard. The BOE's open data
portal carries **only 12 datasets**, all of them annual-report tables 1–11 on
assessed values and none on appeals
([data portal](https://www.boe.ca.gov/dataportal/dataset.htm)). The FY 2024-25
BOE **Annual Report** was downloaded (8.1 MB) and converted to text: its appeals
section reports only the Board's *own* state-assessee docket — "the Board acted on
32 petitions filed by state-assessed companies, of which 10 were adjudicated" —
and contains **no table of county assessment appeals filed, heard or resolved**
([pub306](https://www.boe.ca.gov/legdiv/2024-2025/pub306.pdf)). A per-county
appeals panel would therefore have to be assembled from 58 Clerks of the Board
individually. **Not verified**, by these means, that a statewide per-county
appeals-count or appeals-timing dataset is published anywhere.

### (c) User-generated evidence volume and skew — **3** (inferred)

Appeals are salient to homeowners and to a professional tax-agent industry, so
there is real forum and blog volume (and the plan's A9 file already flags
BiggerPockets and City-Data as sources with county subforums). Expected skew
toward high-value urban and suburban counties, where both assessed values and
appeal volumes concentrate. Inferred.

### (d) Gold-standard process-document feasibility — **5**, and uniquely good

The BOE runs a statutory oversight programme whose output is a per-county
process critique, which is the same designed-tier evidence class as HCD's
ordinance-review findings letters, but with mandated statewide coverage:

- **Assessment practices surveys.** Gov. Code §15640–15646 and Property Tax Rules
  370/370.5/371 mandate them; §15645 requires a written report of findings and
  recommendations on each Assessor's procedures and practices, and the report may
  include the Assessor's response to each recommendation. The reports page carries
  **88 county survey PDFs covering 56 of the 58 county codes**, most counties
  holding a current and a prior vintage — so change-over-time within a county is
  observable, not just cross-section
  ([reports](https://www.boe.ca.gov/proptaxes/assessment-practices-survey-division/reports.htm)).
  Codes 34 (Sacramento) and 42 (Santa Barbara) were not matched by the
  `NNapsrMMYY.pdf` filename pattern and are recorded as not verified rather than
  absent.
- **A published five-year cycle** assigning counties to survey groups by total
  assessed value ([cycle](https://www.boe.ca.gov/proptaxes/assessment-practices-survey-division/cycle.htm),
  with the 2021-22–2025-26 and 2026-27–2030-31 cycle PDFs), and the BOE's own
  annual report confirming delivery: "In FY 2024-25, the BOE issued eight survey
  reports for the counties of Butte, Colusa, Contra Costa, Fresno…" (pub306).
- **A statewide reference process to measure deviation against**: the
  [Assessment Appeals Manual](https://www.boe.ca.gov/proptaxes/pdf/aam2003final.pdf),
  [Publication 30](https://www.boe.ca.gov/proptaxes/pdf/pub30.pdf), and the
  Letters To Assessors series.

That combination — a written intended process, plus an oversight body's
per-county audit of the actual process, for nearly all 58 counties, twice — is
the best gold-document position of any candidate in this sweep, ADU included.

### (e) Rural coverage — **4**

Every county has a board and a Clerk of the Board, and the survey cycle is
explicitly designed to reach the smallest counties (Colusa appears in the FY
2024-25 batch; codes for Alpine, Sierra and Modoc appear in the reports list).
Appeal *volume* in the smallest counties will be tiny, which limits outcome
modelling even if the process documents exist.

**Total: 19/25.**

---

## 4. Agricultural commissioner restricted-materials pesticide permits

Basis: Food & Agric. Code §11701, §14006.5 and §12979; 3 CCR §6400 et seq.
(restricted materials, permit conditions, notices of intent). Fifty-eight County
Agricultural Commissioners issue the permits under DPR's enforcement programme.

### (a) Cross-county process variation — **4**

The statute delegates *site-specific permit conditions* to the commissioner: the
permit is an annual authorisation, and each planned application additionally
requires a Notice of Intent reviewed locally. So the county decides both the
standing conditions and the per-application review, which is a two-stage local
decision on a state list of materials. The published data shows the counties
using structurally different permit instruments in different mixes — statewide
2020–2025 totals split **RMP-Agricultural 129,057 / Operator ID 74,718 /
RMP-Multi-Year 57,380 / RMP-Non-Agricultural 6,841** — and the multi-year permit
is an option a county can lean on or ignore.

### (b) Per-county official outcome data — **4** (volume and enforcement, no clock)

DPR publishes three per-county workbooks, all downloaded and parsed:

| workbook | rows | shape verified |
|---|---:|---|
| [Restricted Material Permits](https://www.cdpr.ca.gov/wp-content/uploads/2025/12/restricted_material_permits.xlsx) | 14,917 | county × month (2020-01 → 2025) × 4 permit types; 58 counties |
| [Inspections](https://www.cdpr.ca.gov/wp-content/uploads/2026/03/inspections.xlsx) | 82,711 | county × month × **9 inspection types** (field worker safety, pesticide use monitoring, commodity and soil fumigation, structural Branch 1 / Branch 2–3, pest control business HQ…) |
| [Enforcement Response](https://www.cdpr.ca.gov/wp-content/uploads/2025/12/enforcement_response.xlsx) | 47,546 | county × month × {Compliance, Enforcement, Judicial} actions × subtype |

Plus [county administrative civil penalties](https://www.cdpr.ca.gov/wp-content/uploads/2026/07/cac_admin_civil_penalties-062024_062026.xlsx)
and quarterly product-compliance workbooks. Agricultural RMPs 2020–2025 per
county: **Tulare 15,131, Stanislaus 10,638, Fresno 10,012** at the top;
**Marin 8, San Francisco 10, Mariposa 17, Trinity 17, Alpine 0** at the bottom.
The inspection-type split is the most useful part: it is a per-county monthly
record of *which kind of check the county actually performs*, which is process
structure rather than volume. There is **no elapsed permit-decision clock** in
any of the three, which caps this axis at 4.

### (c) User-generated evidence volume and skew — **2** (inferred, inverted)

Growers and pest control advisers are a small professional population, and
compliance runs through mandatory reporting rather than public discussion, so
forum volume should be the thinnest of the four priority candidates. Its skew
should invert: what discussion exists will sit in agricultural counties. Inferred.

### (d) Gold-standard process-document feasibility — **5**

DPR publishes the **Pesticide Use Enforcement Program Standards Compendium** as
the intended process, in volumes that map onto exactly the objects this project
models — **Volume 3 Restricted Materials and Permitting**, **Volume 4 Inspection
Procedures**, Volume 5 Investigation Procedures, Volume 6 Enforcement Response,
Volume 1 General Administration, Volume 2 Laws and Regulations
([CAC resources](https://www.cdpr.ca.gov/enforcement/resources-for-county-agricultural-commissioners/)) —
plus a
[County Agricultural Commissioner Letters](https://www.cdpr.ca.gov/enforcement/county-agricultural-commissioner-letters/)
series and a [County Citable Sections](https://www.cdpr.ca.gov/wp-content/uploads/2026/02/citsec.pdf)
list. So the *designed* process is documented at step granularity by the state,
and the *realised* process is measured monthly per county by the three workbooks
above. Very few programmes give both halves.

### (e) Rural coverage — **5**, the only clear inversion in the sweep

Permit and inspection activity is concentrated in agricultural counties and is
near zero in the densest urban ones — Marin 8 agricultural permits against
Tulare's 15,131 — and counties like Colusa, Glenn, Merced and San Joaquin carry
substantial volume. This is the one candidate where the *official* evidence base
is thickest exactly where the *user* evidence base is thinnest, which makes it
the natural control for the rural-data question. Note that the
[environmental health packet](2026-09-16-county-environmental-health-58.md)
looked for the same inversion in septic and found it **not established**; here
the permit counts make the activity concentration a measured fact, though the
*evidence-volume* inversion remains inferred.

**Total: 20/25.**

---

## 5. The rest of the A6 list

Ordered by score, not by the order the plan listed them. The first entry is the
surprise of the sweep and is written at the same depth as the four above.

### 5.1 Registrar of voters — **21/25**, the find the plan did not anticipate

Basis: Elections Code; §3019 (mail-ballot signature verification and the
statutory cure process); §4005 (Voter's Choice Act, which a county elects into
and which requires it to adopt and publish an Election Administration Plan).
Fifty-eight county elections officials.

**(a) Variation — 5.** Two structural choices are county-level: whether to run
elections under the Voter's Choice Act at all, and how to conduct signature
comparison. The second is *measured*, not asserted. From the federal EAVS 2024
file (below), the share of a county's rejected mail ballots that were rejected
for a **non-matching voter signature** runs from **0.000 in Kern and 0.083 in
Amador to 0.827 in Fresno, 0.869 in San Benito and 0.871 in Colusa**. Same
statute, same ballot envelope, and one county attributes almost none of its
rejections to signature mismatch while its neighbour attributes seven eighths of
them. *Honest caveat*: part of that spread is classification practice rather than
adjudication practice — counties differ in how they bin a rejection reason — which
is precisely the measurement-semantics hazard the CalFresh packet warned about,
and it means the reason mix must be modelled with a reporting-practice term, not
read straight off as a decision rule.

**(b) Per-county official outcome data — 5.** The **Election Administration and
Voting Survey (EAVS)** is collected per *local election jurisdiction*, which in
California is the county, and California's rows are complete:

- 2024 public release, downloaded and parsed: **6,461 jurisdictions × 535
  columns**, of which **exactly 58 rows are California** — every county, Alpine
  and Sierra included.
  [CSV release](https://www.eac.gov/sites/default/files/2026-02/2024_EAVS_for_Public_Release_nolabel_V2_csv.zip),
  [codebook](https://www.eac.gov/sites/default/files/2025-06/2024_EAVS_Codebook.xlsx),
  [index page](https://www.eac.gov/research-and-data/datasets-codebooks-and-surveys)
  (biennial waves 2004–2024, so **eleven waves**).
- The columns are a **failure-reason decomposition of a decision**, which nothing
  else in this sweep provides: `C9a` total mail ballots rejected and **twenty
  itemised reasons** `C9b`–`C9t` (late, missing voter signature, non-matching
  voter signature, unofficial envelope, ballot missing from envelope, voter
  already voted, voter not eligible, …), plus `C7b`/`C7c` **mail ballots
  successfully and unsuccessfully cured**, and `E1a`–`E3m` provisional ballots
  cast, fully counted, partially counted, rejected, with thirteen reasons.
- Verified California 2024 values: **all 58 counties report both mail ballots
  returned and mail ballots rejected.** Rejection rate runs Inyo 0.0017 and
  Amador 0.0018 to Modoc 0.0288 and Trinity 0.0292, median **0.0095** — a
  **17-fold spread**. Cure success share (successful / (successful +
  unsuccessful)) reaches 0.897 in Shasta and 0.888 in Kern.
- Caveat that must be handled: EAVS uses **−99 as a missing-data code**, and it
  appears in California rows (Del Norte, Nevada and San Diego all carry −99 in
  `C7b`), so a naive ratio produces negative "rates". Suppression and
  non-response are informative here, exactly as in CF 296.

Why this matters for the generator specifically: `decision.py` plants
predicate-level results, a fixable-versus-fatal flag, a rework loop with
`p_cure`, and a `predicate_summary` of first-pass versus eventual pass rates.
EAVS is the **only real dataset located in this whole sweep that observes those
objects directly** — per-county counts of which predicate failed, and how many
failures were cured. ADU gives the clock; this gives the predicate.

**(c) User evidence — 2** (inferred). Voters complain about elections online,
but almost never about the county's adjudication of their own envelope, and the
cure notice arrives by mail. Thin and urban-skewed.

**(d) Gold-document feasibility — 4.** Voter's Choice Act counties must adopt
and publish an Election Administration Plan with a public-comment record, which
is a county-authored process document with a statutory content list. Every
county also publishes its signature-verification and cure procedures in some
form. **Not verified in this packet:** the current list of VCA counties and a
count of published plans; that needs a fresh-session pass on sos.ca.gov, whose
`/elections/unprocessed-ballots-reports` path 404s.

**(e) Rural coverage — 5.** Complete. Modoc, Trinity, Alpine and Sierra all
report, and Trinity has the *highest* rejection rate in the state, so the small
counties are not merely present but load-bearing.

### 5.2 Cannabis licensing — **16/25**

Basis: MAUCRSA, Bus. & Prof. Code §26000 et seq.; §26200 preserves complete
local control, so a county may ban commercial cannabis outright. **(a) 5** — the
widest formal variation of any candidate, because the county's choice set
includes "no process at all", which no other programme here permits.
**(b) 2** — DCC publishes four dashboards (licence summary, harvest, sales, monthly
sales) at [cannabis.ca.gov/resources/data-dashboard](https://www.cannabis.ca.gov/resources/data-dashboard/)
and a [licence search](https://search.cannabis.ca.gov); **whether any of it
breaks out by county or local jurisdiction is not verified**, and no
`package_search` hit exists on either state portal (a `data.ca.gov` search for
"cannabis license" returns only water-rights datasets, and there is no
Department of Cannabis Control organisation among the portal's 62 orgs). No
processing-time measure located. **(c) 3**, **(d) 3** (county ordinances are
public and abundant; state guidance is thin on local process), **(e) 3**.

### 5.3 CalWORKs — **16/25**

Basis: W&I Code §11200 et seq. **(a) 3** — the same platform-flattening problem
as CalFresh for eligibility, with real county discretion concentrated in
Welfare-to-Work programme design. **(b) 3** —
[Counts and Status of CalWORKs Applications](https://data.chhs.ca.gov/api/3/action/package_show?id=counts-and-status-of-california-work-opportunity-and-responsibility-to-kids-calworks-applications)
was downloaded and parsed: **50,032 rows**, county × month, 58 counties plus a
`STATEWIDE` row, items A_2/A_3/A_4a/A_4b = applications received, **total
applications on hand** (a backlog stock, which is unusual and useful),
applications approved, applications denied; suppression marked as `-999`. But the
series on the portal runs **SFY 2000-01 through 2017-18 only** — it stops eight
years ago, and current CA 237CW data would have to come from the CDSS RADR site,
which was not fetched in this packet. There is no timing field.
[CalWORKs Welfare-to-Work Monthly Activities](https://data.chhs.ca.gov/api/3/action/package_show?id=calworks-welfare-to-work-monthly-activities)
is a second per-county file. **(c) 3**, **(d) 3** (county WTW plans and handbooks
exist for large counties), **(e) 4**.

### 5.4 Encroachment and grading permits in unincorporated areas — **15/25**

**(a) 4** — grading thresholds, engineered-plan triggers and public-works standards
are locally adopted and differ sharply. **(b) 1** — no statewide per-county
dataset found; the HCD APR covers housing units only, and the DWR
[i13 EncroachmentPermits](https://data.ca.gov/api/3/action/package_show?id=i13-encroachmentpermits-dwr)
dataset is state levee encroachments, not county road encroachments. **(c) 2**,
**(d) 4** (every county publishes a grading ordinance and improvement standards,
so 58 designed documents are obtainable), **(e) 4**.

### 5.5 LPS conservatorship and the public guardian — **13/25**

Basis: W&I Code §5150, §5250, §5350; §5402 reporting as amended by SB 929;
SB 43's expanded grave-disability definition, **which each county could adopt in
2024 or defer to 2026** — a county-level election of exactly the optional-regime
kind plan §10.8 wants planted. **(a) 4.** **(b) 3** —
[Lanterman-Petris-Short Act Data](https://data.ca.gov/api/3/action/package_show?id=lanterman-petris-short-act-data)
(DHCS) publishes, per county, the number of persons detained under the several
LPS sections, transfers under Penal Code §4011.6, and **the number of persons for
whom temporary and permanent conservatorships were established**, with SB 929
Phase I/Phase II data elements; last modified 2026-09-16. Counts, no clock, and
small-county cells will suppress. **(c) 1** — the client population is the least
able to post about its own process, which is a real fairness point but makes the
evidence channel nearly empty. **(d) 2**, **(e) 3**.

### 5.6 IHSS enrolment — **13/25**

Basis: W&I Code §12300 et seq.; the county social worker's hourly task-based
assessment authorises service hours, which is genuine per-case discretion inside
a state-uniform instrument. **(a) 3.** **(b) 2 — not verified.** Searches of both
portals for "IHSS", "IHSS caseload" and "In-Home Supportive Services county"
returned only DHCS long-term-services-and-supports and dual-eligible datasets;
`data.ca.gov` has no IHSS dataset and CDSS's eleven datasets there are community
care licensing, CalWORKs, DFA256 and child-maltreatment files. Per-county
*average authorised hours* would be an excellent discretion measure if CDSS
publishes it; that was not confirmed here. **(c) 3**, **(d) 2**, **(e) 3**.

### 5.7 Animal licensing — **13/25**

**(a) 4** (ordinance, fee and mandatory-spay variation is large and entirely
local), **(b) 1** (no state dataset located; shelter-intake data is not a
licensing process), **(c) 2**, **(d) 3** (county code chapters), **(e) 3**.

### 5.8 Body art registration — **13/25**

Basis: Safe Body Art Act, Health & Safety Code §119300 et seq., enforced by a
local enforcement agency the county designates. **(a) 4** (the local enforcement
agency designation itself varies), **(b) 1** (`package_search` for "body art" on
`data.chhs.ca.gov` returns **COUNT 0**), **(c) 2**, **(d) 3**, **(e) 3**.

### 5.9 Tobacco retail licensing — **13/25**

**(a) 4** — the state licence under the STAKE Act coexists with local retail
licence ordinances that vary from none to flavour bans and density caps.
**(b) 2** — the per-retailer state register exists
([CDTFA licensees](https://data.ca.gov/api/3/action/package_show?id=cigarette-tobacco-products-licensees-in-california-by-cdtfa),
monthly, point locations, so county aggregation is possible), and CDPH publishes
[Retailers that Sold Tobacco to Underage Youth](https://data.ca.gov/api/3/action/package_show?id=retailers-that-sold-tobacco-to-underage-youth-and-young-adults),
but the latter is the Synar/YTPS **sample survey**, whose published unit is not a
county process measure. No inventory of local licence ordinances was located.
**(c) 1**, **(d) 3**, **(e) 3**.

### 5.10 Tax payment plans and excess-proceeds claims — **13/25**

Basis: R&T Code §4216–4220 (instalment redemption plans) and §4675 (excess
proceeds claims, with a one-year claim window after the tax sale). **(a) 4** —
plan terms, default rules and the claim packet are county tax-collector practice.
**(b) 1** — no state dataset located. **(c) 2** (excess-proceeds claims attract a
small and vocal third-party claim-recovery industry), **(d) 3**, **(e) 3**.

### 5.11 Vital records and the county recorder — **12/25**

**(a) 2** — Health & Safety Code §103525/§103526 fix the authorised-copy rule, the
sworn statement and the notarisation requirement statewide, so this is the most
uniform candidate in the list; fees and channel (in person, mail, third-party
vendor) vary. **(b) 1** — CDPH publishes
[Live Birth Profiles by County](https://data.ca.gov/api/3/action/package_show?id=live-birth-profiles-by-county)
and similar, which are health statistics, not records-request process measures.
**(c) 2**, **(d) 3**, **(e) 4**.

### 5.12 Veterans service offices — **12/25**

Basis: Military & Veterans Code §970 et seq.; CalVet subvention is allocated on
county workload units, so a per-county workload measure exists administratively.
**(b) 2 — not verified**: there is no CalVet organisation among the 62 on
`data.ca.gov`, and no dataset was located by these means. **(a) 3**, **(c) 1**,
**(d) 2**, **(e) 4** (CVSOs exist in nearly every county and matter most in rural
ones).

### 5.13 Transient-occupancy-tax registration — **12/25**

**(a) 4** (ordinance, rate, short-term-rental permit coupling and enforcement all
local), **(b) 1** for process — though note that per-county **TOT revenue** is
obtainable from the State Controller's Socrata domain, which the P8 packet opened
(`bythenumbers.sco.ca.gov`, datasets `emxv-k8xv` revenues and `uctr-c2j8`
expenditures, FY 2002-03 to 2023-24; see
[blocked_sources](WORK_PACKETS.json)). Revenue is not a process observable.
**(c) 1**, **(d) 3**, **(e) 3**.

### 5.14 Public pool permits — **11/25**

**(a) 3**, **(b) 1**, **(c) 1**, **(d) 3**, **(e) 3**. Health & Safety Code
§116025 et seq. with county EH plan check; belongs with the A5 environmental
health family rather than as a programme of its own.

### 5.15 TB clearance — **10/25**

**(a) 3**, **(b) 1**, **(c) 1**, **(d) 2**, **(e) 3**. CDPH publishes
[TB cases and rates by local health jurisdiction](https://data.ca.gov/api/3/action/package_show?id=tuberculosis-cases-and-rates),
which is disease surveillance, not a clearance-process measure. The lowest-value
candidate in the list.

### 5.16 Assessed by reference only — Prop 19 claims and the Williamson Act

The plan's A6 list also names **Prop 19 base-year-transfer claims** and the
**Williamson Act**. Both are processed by the same county offices as §3 above
(assessor for Prop 19, board of supervisors plus assessor for Williamson Act
contracts) and are therefore best treated as **additional case types inside the
assessment-appeals/assessor programme** rather than as separate programmes.
Prop 19 in particular is attractive as a *second* task inside the same county
process, because the BOE issued county-facing guidance and a dedicated webpage
during its rollout (pub306, FY 2024-25 narrative), which is designed-tier
evidence on a rule that changed inside the observation window. Not separately
scored.


## 6. The five already-swept programmes, rescored against their own evidence

These are scored from the completed packets rather than from impressions, so
that the ranking in §7 is comparable.

### ADU permitting — **22/25**
**(a) 5**: the jurisdiction's own `PROJECT_TYPE` label splits ministerial from
discretionary, and the median entitlement-to-permit span differs twelve-fold
between them (9 days against 108); Los Angeles city 58 days against Los Angeles
County unincorporated 129 on identical statute and territory
([APR timing](2026-09-16-apr-permit-timing.md)).
**(b) 5**: per-project dates for every jurisdiction, 922,104 records, three
clocks, plus the applicant's own `APP_SUBMIT_DT` on 100% of Table A's 358,264
rows. Nothing else is close; see §9.
**(c) 4**: large homeowner and builder forum presence, urban-skewed.
**(d) 5**: an existing gold corpus (`corpus/ab2533/`), HCD ordinance-review
findings letters as oversight-tier critique, and 58 county ordinances.
**(e) 3**: the honest weakness. Only **40 counties have 30 or more** usable
entitlement-to-permit spans and only **18 unincorporated county processes** do
([verified_assets](WORK_PACKETS.json)), so the rural end of the panel is thin
exactly where the project's fairness question lives.

### CalFresh — **20/25**
**(a) 3**: the packet's own verdict is "no for reported performance; not
established for every process route" — real performance spread (CF 18 July 2024
non-expedited approval means: LA 7 days, Sacramento 16, Merced 30) but
platform-flattened rules.
**(b) 5**: CF 296 at 58 counties × 121 months, plus CF 18 mean approval days.
**(c) 5**: the largest and best-studied user-evidence base of any candidate
(GetCalFresh, legal aid, advocacy).
**(d) 3**: handbooks for a handful of large counties.
**(e) 4**: all 58 counties report, but with 165,413 suppressed cells and Alameda
missing May 2024–June 2025 ([CalFresh packet](2026-09-16-calfresh-58-counties.md)).

### CCW — **17/25**
**(a) 5**: the best-evidenced variation in the project. Five of 43 counties
require a psychological examination and 34 never mention it; a new licence costs
$84 in Lassen and $976 in Santa Clara, with $976 Santa Clara and $128 San Mateo
twenty miles apart
([CCW 43](2026-09-16-ccw-remaining-43-counties.md)).
**(b) 2**: only **9 of 43** counties state a real processing time and 32 of 35
live portals carry identical vendor boilerplate; LASD publishes monthly counts
(855 received, 627 issued in July 2026) and Imperial publishes a current
120-day queue, but there is no per-county panel — `openjustice.doj.ca.gov/data`
returned a 3-KB application shell, so DOJ per-county CCW statistics are **not
verified**.
**(c) 4**: CalGuns and gun-forum county threads reach rural counties better than
most channels.
**(d) 3**: only **6 of 43** publish a policy document, though portal text is
process-rich.
**(e) 3**: **14 of 58 counties block a scripted fetch**, three are paper-only and
one policy is a scanned image with no text layer.

### County environmental health (septic, wells, food) — **17/25**
**(a) 5**: the Tier 1 versus Tier 2 LAMP election is a county-level choice with an
observable document consequence (plan §10.8).
**(b) 2**: published 2019 permit counts were found for **10 counties**, from a
regional oversight summary, not a statewide panel
([EH packet](2026-09-16-county-environmental-health-58.md)).
**(c) 2**: the packet *tested* the rural-inversion hypothesis with matched
queries and reported it **not established** — Alpine returned no qualifying
threads, San Diego at least four. This is the only (c) score in the whole sweep
backed by a measurement rather than an inference, and it came out negative.
**(d) 4**: a 58-row LAMP inventory with 37 document leads, 47 listed approvals,
3 documents read.
**(e) 4**: official evidence demonstrably reaches Alpine, Modoc, Inyo and Sierra.

### General Assistance — **15/25**
**(a) 5**: a one-line mandate (W&I §17000) and 58 invented programmes; the
in-progress packet already documents single-adult grants from **$221 in Los
Angeles to $336 in Alameda and Contra Costa**, with employability time limits of
three months in twelve in several counties
([GA packet](2026-09-16-general-assistance-58-counties.md)).
**(b) 1**: the worst of any candidate, and this is now verified rather than
assumed. CDSS's GR 237 collection publishes caseload and expenditure only; the
single timing-shaped measure on the report form is the disposition of SSI/SSP
interim-assistance checks within 1–10 working days of receipt, which is **not**
application processing time. Every county row in that packet's inventory reads
`measured timing NV`.
**(c) 2**, **(d) 4** (county code chapters and regulations PDFs are obtainable
and the packet has a dozen already), **(e) 3**.

---

## 7. The ranked shortlist of eight

| # | programme | a | b | c | d | e | total | the one-line reason |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| 1 | **ADU permitting** | 5 | 5 | 4 | 5 | 3 | **22** | the only per-project elapsed clock for every jurisdiction, with a ministerial/discretionary ground-truth label attached |
| 2 | **Registrar of voters** | 5 | 5 | 2 | 4 | 5 | **21** | the only per-county data that names *which predicate failed* and how many failures were cured, complete for all 58 counties over eleven biennial waves |
| 3 | **Medi-Cal eligibility** | 4 | 5 | 4 | 3 | 4 | **20** | a structurally complete 58 × 98-month deadline-compliance panel, plus real call-wait durations, plus the SAWS platform label |
| 4 | **CalFresh** | 3 | 5 | 5 | 3 | 4 | **20** | the extraction already exists in-repo and the user-evidence base is the richest of any candidate |
| 5 | **Agricultural commissioner RMP permits** | 4 | 4 | 2 | 5 | 5 | **20** | the only programme whose official evidence is thickest in rural counties, and the only one with a state-published step-level intended process |
| 6 | **Property tax assessment appeals** | 5 | 2 | 3 | 5 | 4 | **19** | the best designed-tier document position in the sweep — an oversight body audits each county's process, twice, with the assessor's replies |
| 7 | **CCW** | 5 | 2 | 4 | 3 | 3 | **17** | the largest measured policy variation and the discovered vendor-boilerplate failure mode; already complete for 58 counties |
| 8 | **County environmental health** | 5 | 2 | 2 | 4 | 4 | **17** | the optional-regime (LAMP tier) choice, and the only rural hypothesis anyone has actually tested |

Ties were broken deliberately: **CalFresh above the pesticide programme** because
its CSV extraction is already built and verified in-repo and its (c) is the
strongest in the sweep, so the marginal cost of keeping it is near zero;
**the pesticide programme above assessment appeals** because it has real
per-county data and appeals does not; **CCW above environmental health** because
its 58-county coverage is finished and its variation is measured in dollars and
required steps rather than in document availability.

Just outside: **CalWORKs (16)** and **cannabis licensing (16)**. CalWORKs is the
better of the two and is the natural fifth social-services programme if the
CalSAWS-family evidence is ever pooled; cannabis has the widest formal variation
of anything in the sweep and would jump several places the moment a per-county
DCC dataset is confirmed. **General Assistance (15)** ranks ninth on these axes,
and that is *the point of it* rather than an argument against it — see §8.

---

## 8. The recommended combination

**ADU + Medi-Cal eligibility + registrar of voters + agricultural commissioner
restricted-materials permits.**

Each earns its place by contributing something none of the others can.

- **ADU contributes the continuous clock and the structural label.** It is the
  only member with per-case elapsed durations (entitlement → permit → occupancy,
  and application → permit), so it is the only one that can identify the
  duration-generating part of the model at all, and the only one carrying a
  jurisdiction-authored ministerial/discretionary label to calibrate a noisy
  structural signal against. It also supplies the covariate regression at
  n = 186 jurisdictions.
- **Medi-Cal contributes panel length and the platform-confound test.** 98
  monthly observations per county against ADU's 8 annual ones is what makes the
  measurement parameters and the county random effects estimable rather than
  prior-bound (plan §4.4). Uniquely, it carries the **SAWS consortium label per
  county-month**, so the §10.1 question — does a shared platform manufacture
  false agreement? — becomes testable with a real treatment variable and a real
  migration date, instead of being planted only in the synthetic world. Nothing
  else in the combination has a platform variable.
- **Registrar of voters contributes the predicate and the cure.** It is the only
  member that observes *which requirement a case failed* and *whether the failure
  was fixed*: `C9b`–`C9t` reasons, `C7b`/`C7c` cured and not cured, `E3b`–`E3m`
  provisional reasons. That is a direct observation of `predicate_results`, the
  fixable-versus-fatal flag and `p_cure`, which ADU cannot give (89 disapprovals
  in 194,347 decisions) and Medi-Cal gives only in aggregate. It is also the only
  member with genuinely complete rural coverage, with Trinity, Modoc, Alpine and
  Sierra all reporting and Trinity holding the state's highest rejection rate.
- **Agricultural RMP permits contribute the rural inversion and the reference
  process.** It is the one programme where official evidence is concentrated in
  rural and agricultural counties and user evidence is expected to be thinnest,
  which makes it the control arm for the rural-data-poverty question rather than
  another instance of it. It is also the only member where the state publishes
  the intended process at step granularity (Compendium Volumes 3 and 4), so
  cross-county deviation can be scored against a written standard instead of
  against other counties.

Together they cover: continuous timing, deadline compliance, predicate-level
failure and cure, activity volume, a platform confound, an intended-process
reference, and both directions of the rural gradient — including the newly
measured **rural gap inside official data** (Medi-Cal call centre: 34 of 58
counties) alongside the expected rural gap in user data.

### What the combination still leaves uncovered

1. **A zero-official-data, maximal-discretion arm.** All four members publish
   per-county data. The disappearing-commons claim needs at least one programme
   where neither official nor user evidence exists, and **General Assistance is
   that programme** on verified grounds: county-invented rules, and a timing
   verdict of `NV` in every row. If the paper argues that evidence poverty
   compounds discretion, GA must be in the design as the fifth arm, scored on
   document recovery rather than on timing.
2. **Fee variation and a written county policy.** None of the four has an
   applicant-facing fee that varies by policy (ADU fees are capped, Medi-Cal and
   voting are free, RMP fees are small and cost-based). The 11.6-fold CCW fee
   spread and the psychological-evaluation requirement are the evidence behind
   plan §10.2 and §10.4, and **CCW is already complete for all 58 counties**, so
   retaining it costs nothing and it is the only source for the fee-policy effect
   the generator now plants.
3. **The typed retrieval-failure channel.** The four members' data arrive through
   clean state portals. The blocked, image-only, stale-link and misrouted
   failures of plan §10.6 were observed in CCW and environmental health, not
   here; those two programmes remain the empirical basis for that channel.
4. **Staff-side evidence, still absent everywhere.** Nothing in this sweep
   located a staff-perspective source. The A9 brief's Glassdoor and Indeed idea
   remains the only candidate and remains unexecuted.
5. **A denial-heavy adjudication.** Only the voting arm has a meaningful adverse
   decision rate. If the project wants a programme where denial is the normal
   outcome, none of the four provides it, and assessment appeals — where the
   applicant loses most of the time — would be the natural addition, at the cost
   of having to build its per-county outcome panel from 58 clerks by hand.

---

## 9. Does anything beat ADU on per-jurisdiction timing data?

**No. Plainly no, and the gap is not close.** ADU's position is unchanged by this
sweep, and the project's plan does not need to change.

The APR gives, in one downloadable file, **per-project dates** — entitlement
approval, building-permit issue, certificate of occupancy, and via Table A the
applicant's own submission date on 100% of 358,264 rows — for **every
jurisdiction in the state over eight years**. Two properties make it unmatched:
it is **case-level**, so any statistic (median, quantile, hazard, variance) can
be computed rather than only the one the publisher chose; and it carries **both
ends of a clock for the same case**, so an elapsed duration exists without
assumption.

Every candidate assessed here fails one of those two tests. Ranked by how close
they come:

| candidate | what it publishes | why it does not beat ADU |
|---|---|---|
| CalFresh CF 18 | **mean approval days** per county per report month | a published mean, approval-conditioned, initial applications only; no case-level records, so no distribution and no quantiles |
| Medi-Cal call centre | **average wait time, HH:MM:SS**, per county per month, by language | a real duration, but for one telephone step, aggregated, and only **34 of 58 counties for 6 months** |
| Medi-Cal renewals | renewals **completed by the due date**, 58 counties × 98 months | deadline compliance, not elapsed time; a count, not a clock |
| CalFresh CF 296 | county-caused over-30-day approvals and denials | same: a threshold count, and explicitly only *county-caused* delay |
| EAVS | rejections **because late**, cure outcomes, 58 counties × 11 waves | a deadline-compliance count; biennial; no case-level dates |
| DPR RMP / inspections | permits and inspections per county per month | volume only; no decision date and no application date |
| CCW | 9 of 43 counties state a processing time in prose | not a dataset; mostly one vendor's "multiple weeks" boilerplate |
| Assessment appeals | the §1604 two-year statutory clock exists in law | **no published per-county appeals timing at all** was located; the BOE annual report has no such table and its data portal has no such dataset |

I specifically looked for a case-level register with both a submission and a
decision date, since that is the only shape that could compete, and found none
outside the APR. The nearest structural analogues — a court docket for child
support, a clerk-of-the-board appeals register, a DCC licence application
register — are either not published per county, or not published at case level,
or **not verified** as published at all by the means available in this session.

Two honest qualifications, because they change *how* ADU should be used rather
than *whether*:

1. **Medi-Cal beats ADU on panel length and on completeness.** 98 monthly
   observations for all 58 counties beats 8 annual years for 40 counties with
   usable spans, and ADU's 18 usable unincorporated county processes are the
   binding constraint on any analysis of *county-run* processes. For anything that
   needs a long, complete county panel — measurement parameters, county random
   effects, covariate regressions on county-administered programmes — Medi-Cal is
   the better instrument, and ADU is the better instrument for durations.
2. **EAVS beats ADU on decision structure.** ADU has essentially no adverse
   decisions to learn from; EAVS itemises twenty rejection reasons and the cure
   outcome. If the research question is the decision function rather than the
   clock, the voting data is the sharper instrument.

So the correct statement is not "ADU is best" but **"ADU remains uniquely best on
case-level elapsed timing, and two of the programmes found in this sweep are
better on two other axes that matter"**, which is an argument for the combination
in §8 rather than for a single flagship.

---

## 10. Unassessed, and what a fresh session should do first

Nothing in the A6 list was dropped. These are the items whose key question stayed
unresolved, with the reason:

| item | unresolved question | reason |
|---|---|---|
| Child support per-LCSA performance | the federal performance measures by agency, cited by the plan as "excellent" | `childsupport.ca.gov` returns **403** to every `curl` path; WebFetch reached only navigation and the statewide dashboards; the cited "FFY 2024 Comparative Data for Managing Program Performance" was not located; `acf.gov/css/data` returns **403** to WebFetch. Also unresolved: how many LCSAs there are and which counties share one |
| Medi-Cal application timeliness | the 45-day standard's per-county compliance rate | six portal queries found renewals and call-centre data but no application-timeliness dataset |
| IHSS | per-county average authorised hours, which would be an excellent discretion measure | no IHSS dataset on either portal |
| Cannabis | whether DCC's four dashboards break out by county | dashboards are JavaScript; the glossary page was not fetched |
| Veterans service offices | per-county CVSO workload units | no CalVet organisation on `data.ca.gov` |
| Voter's Choice Act county list and Election Administration Plans | how many counties publish a plan | `sos.ca.gov/elections/unprocessed-ballots-reports` 404s; the SOS site was not crawled in this packet |
| Assessment appeals per-county counts | filings, hearings and decisions by county | not published by BOE in any located form; would require 58 Clerks of the Board |
| BOE survey reports for codes 34 and 42 | Sacramento and Santa Barbara survey PDFs | not matched by the `NNapsrMMYY.pdf` filename pattern used by the other 56 |

**First three things a fresh session should do**, in order:
1. One search-engine pass on "Comparative Data for Managing Program Performance"
   and on `site:childsupport.ca.gov` reports. Child support is the only candidate
   whose score could move by more than a point on one document.
2. Download the **EAVS 2004–2022 waves** and build the California panel, handling
   the −99 missing code. That turns §5.1's single 2024 cross-section into an
   eleven-wave county panel, which is the cheapest large addition available to
   the project right now.
3. Confirm the DCC per-county licence breakdown and the VCA county list, both of
   which are single-page confirmations that unlock a score each.

## Budget and provenance

Roughly 80 network calls: CKAN `package_search`/`package_show`/`organization_*`
on `data.ca.gov` and `data.chhs.ca.gov`, `curl -L` against `boe.ca.gov`,
`cdpr.ca.gov`, `cannabis.ca.gov`, `eac.gov` and `childsupport.ca.gov`, and five
WebFetch fallbacks on 403s. **No WebSearch was used** (exhausted before the
packet started). Files downloaded and parsed rather than described: the Medi-Cal
renewals CSV, the Medi-Cal call-volume and call-wait CSVs, the DCSS case-overview
and paternity CSVs, the CalWORKs applications CSV, DPR's restricted-materials,
inspections and enforcement-response XLSX workbooks, the BOE FY 2024-25 annual
report PDF, and the EAVS 2024 public-release CSV with its codebook. Every number
in this file was computed from one of those files or quoted from a page whose URL
is given.

Everything downloaded is cached under **`corpus/counties/raw/p6/`** (18 MB, 13
files, `p6_` prefix) so that none of it needs refetching:
`p6_medical_renewals_by_county.csv`, `p6_medical_call_wait_time.csv`,
`p6_medical_call_volume.csv`, `p6_dcss_case_overview.csv`,
`p6_dcss_paternity.csv`, `p6_calworks_applications.csv`,
`p6_dpr_restricted_material_permits.xlsx`, `p6_dpr_inspections.xlsx`,
`p6_dpr_enforcement_response.xlsx`,
`p6_boe_annual_report_2024-25_pub306.pdf`,
`p6_boe_assessment_practices_survey_reports.html`,
`p6_eavs_2024_public_release_csv.zip`, `p6_eavs_2024_codebook.xlsx`.
