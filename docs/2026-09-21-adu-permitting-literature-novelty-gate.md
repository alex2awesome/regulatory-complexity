# ADU permitting process-structure contribution: literature novelty gate

Date: 2026-09-21. Adversarial review — the brief was to find evidence the
contribution is already taken, after a companion review found the CalFresh
candidate substantially scooped. Method, blocked queries and unreachable sources
are in §6; **read §6 before treating any gap below as a finding.** OpenAlex was
unusable for this entire session (§6).

Companion documents: `docs/2026-09-21-calfresh-literature-novelty-gate.md` (the
comparison baseline). A parallel agent covers solar permitting; this review
deliberately does not.

## 1. Bottom line

**ADU permitting is LESS saturated than CalFresh for our purposes, but the margin
is narrower than it first looks, and it is entirely concentrated in two of our
three planks.** The CalFresh gate's decisive finding was that per-county
*procedural* measurement had already been done by primary collection — Heflin,
Fannin & Lopoo phoned all 626 SNAP local information lines across the ten
county-administered states including California and documented new-application
conditions in 647 counties. **There is no ADU equivalent and I looked hard.**
California's only statewide jurisdiction-level land-use instrument is the Terner
California Residential Land Use Survey (single wave, 2017–18, never repeated,
271 of 539 jurisdictions responding, 207 variables), whose **entire ADU block is
six items, all substantive**; it has **no ADU approval-time variable at all**,
**zero procedural-step variables**, and the word "hearing" appears **exactly once
in the whole instrument**, inside a staff-headcount question. Likewise, **nobody
codes ministerial/60-day compliance per California jurisdiction** — Mercatus
codes it at state-statute level for 18 states, Terner folds "timely ministerial
review" into one 3-category question, Pfeiffer and the Terner owner survey both
*note* noncompliance without coding it, and the Casita Coalition's own page tells
readers to "Contact HCD to find out" whether their local ordinance meets state
law. So planks (d) per-jurisdiction procedural step structure and (e)
per-jurisdiction mandate compliance are **genuinely open, and no existing data
source even contains the fields**.

**Three corrections against our optimism, in order of how badly each hurts.**
First, **the timeline plank is substantially exposed and must be re-scoped.**
Terner has *already published* ADU application→permit durations computed from
exactly the join we would use — HCD APR Table A merged to Table A2 — in
Underriner's March 2024 coastal-zone analysis (LA 260 days inside the Coastal
Zone vs 147 outside; Orange 233 vs 101; ~29,000 applications with both dates).
It is aggregated to three counties × coastal/non-coastal rather than per
jurisdiction, and it does not test 60-day compliance, but the method is published
and its footnote 5 records that **HCD staff themselves clean APR data "to
calculate application and permitting timelines" for their dashboard**. "We
computed ADU permitting days per jurisdiction" is therefore not a defensible
contribution on its own. Second, **the methods plank is identically taken**: Cook
et al. (2017) is an occupancy model without the name and Weidmann (2015)
published the shared-bias objection, exactly as in the CalFresh gate — ADUs buy
us nothing, and I confirmed the lineage never left conflict-event data by
resolving all 20 papers citing Cook et al. Third, **the City of Seattle already
publishes our burden decomposition** — 80.9 days intake-to-issuance, 58.7 in
agency review, 22.2 out with the applicant, 2.7 correction cycles — annually, for
one jurisdiction, which makes "elapsed time by phase, applicant vs agency" a
municipal reporting practice rather than a discovery. A ~12-step ADU task
inventory is also already published prescriptively by the Casita Coalition, and
commercial operators (SnapADU, Napa Sonoma ADU Center) maintain per-jurisdiction
Yes/No requirement tables with coarse timelines for 16–19 jurisdictions each.

So the defensible claim is not "we invented per-jurisdiction ADU process
measurement." It is **the step-resolved, within-stage structure that no data
source contains — completeness review, corrections cycles, referrals, plan-check
iterations — inferred across hundreds of jurisdictions from heterogeneous
documents with a modelled detection process, and scored against a statutory
mandate that is unusually precise.**

That last clause is a structural advantage over CalFresh worth stating, because
it changes what the paper can claim. CalFresh's mandate is diffuse; **ADU
procedure is legally specified to the step.** Gov. Code § 66317 mandates
ministerial approval with no hearing; a completeness determination within **15
business days** with a cure list that may not later be added to; **deemed
complete** on agency lateness; approve-or-deny within **60 days**; **deemed
approved** on agency lateness; and an appeal decided within **60 business days**.
That is a ~9-node mandated process with three clocks and two self-executing
remedies — and the 15-business-day and appeal clocks are **new as of SB 543,
effective 2026-01-01** (§ 66314 likewise amended by AB 1170), so no existing
empirical study can have covered the current regime. Divergence from mandate is a
legally consequential quantity here, not merely a descriptive gap. Also note
delay, not denial, is the binding constraint: roughly 20 disapprovals a year
against ~27,000 ADU applications. Importing CalFresh's procedural-*denial*
framing would be a category error.

## 2. The six questions

### Q1. ADU permitting timelines and compliance with the ministerial/60-day mandates

**Verdict: PARTIALLY DONE for timelines (aggregated, not per jurisdiction);
ALREADY DONE for permit counts; GENUINELY OPEN for mandate compliance.**

Scale check first. OpenAlex was unavailable, but OpenAIRE returns **52
publications** in total for "accessory dwelling unit", and five differently
phrased Crossref searches return the same ~20-item cluster. The peer-reviewed ADU
literature is small; the grey literature is where the work is, and Terner
dominates it (all 214 Terner `research-and-policy` items plus blog posts were
enumerated via `sitemap.xml` and the WordPress REST search API).

- **Underriner (2024), "Comparing ADU Permitting Time Inside and Outside the
  Coastal Zone", Terner Center**,
  `https://ternercenter.berkeley.edu/blog/adus-coastal-zone/`, 21 Mar 2024.
  **The single most threatening item for our timeline claim.** Measures ADU
  permitting time **in days**, from HCD APR **Table A** (applications) merged to
  **Table A2** (permits) **by APN**, deduplicated to parcel, geocoded against the
  Coastal Zone boundary, 2018–2022; ~29,000 applications had both dates.
  LA Coastal 260 days vs 147 outside; Orange 233 vs 101; San Diego no significant
  difference. **Aggregated to 3 counties × coastal/non-coastal — not per
  jurisdiction.** Invokes the 60-day limit as a policy referent but **does not
  test compliance**. Its footnote 5 records that HCD staff clean APR data "to
  calculate application and permitting timelines" for their dashboard.
- **Marantz, Elmendorf & Kim (2023), *Evaluating California's Accessory Dwelling
  Unit Reforms: Preliminary Evidence and Lessons for State Governments*, NYU
  Furman Center.** The most dangerous item by author team (Marantz planning +
  Elmendorf law). "Analyzes ADU permitting in the Bay Area and southern
  California" with "statistical models to describe the geography of ADU
  development and to identify the parcel-, neighborhood-, and
  **jurisdiction-level** characteristics that are associated with ADU
  permitting." A multilevel model with jurisdiction effects — but the outcome is
  permit **incidence**, not duration, steps or clock compliance. No mention of
  processing times, days-to-permit, APRs or the 60-day deadline in the abstract.
  **I could not read its methods section (Cloudflare 403; see §6) — the most
  important single gap in this review.**
- **Chapple, Garcia, Tucker & Valchuis (2020), *Reaching California's ADU
  Potential*, Terner Center.** Permit and completion **counts** per jurisdiction
  from HCD Annual Production Reports 2018–19 (5,911→15,571 permits;
  1,984→6,668 completions), linked to 12.5M-parcel assessor data, ACS, Zillow,
  LEHD, TCAC. No durations, no steps, no compliance. Earlier: **Garcia (2017),
  *ADU Update***, application counts 2015–17 collected directly from large cities.
- **Ichaki (2026), `permittimelines`, Zenodo 10.5281/zenodo.22079795**, dashboard
  `https://www.therenology.com/data/permit-timelines`. The only published
  DOI'd per-city ADU permit-timeline dataset. 72 published rows
  (`city, dimension, group, n, p25, median, p75, p90, within_30…within_365`) over
  64,427 records with `applied_date, issued_date, days_to_issue`. **Three
  California cities (LA, San Diego, SF), garage conversions only**, and it
  self-describes as "not a statutory compliance measure".
- **Fulton, Karlinsky & Underriner (2025), *Steps Local Governments Can Take to
  Unlock More Housing: Lessons from San Diego*, Terner.** Permits by **process
  type (ministerial vs discretionary)** from San Diego DSD, 2022–24, plus the
  richest narrative process description in the corpus (community planning group
  review now optional, Planning/DSD split, a 30-day corrections deadline under
  Executive Order 2023-1, ADU Bonus Program). One jurisdiction, narrative,
  uncoded. Companion: **Alameldin & Underriner (2023)** on the ADU Bonus Program.
- **California YIMBY, Gray (2024), *California ADU Reform: A Retrospective*.**
  HCD counts, statewide + LA + a 14-suburb panel. Notable because it **names our
  gap as an open problem** — "ministerial approvals, shot clock provisions, and
  impact fee exemptions" — without measuring any of it per jurisdiction.
- **HCD publishes no processing-time metric.** Its APR dashboard
  (`hcd.ca.gov/housing-open-data-tools/apr-dashboard`) is counts and RHNA
  progress; the ADU Handbook is guidance. Its Technical Assistance & Enforcement
  Letters dashboard (`hcd.ca.gov/hau/enforcement-letters`) *does* record
  per-jurisdiction housing-law violation findings (Case Number / Letter Date /
  Jurisdiction / Housing Law / Letter Type) — the closest published
  per-jurisdiction compliance record — but is Power BI with **no CSV export**.
- **No ADU scorecard, report card, ranking or "accelerator grade" exists** on any
  host enumerated (Casita Coalition 215 URLs, Terner 545, Lewis 543, SPUR,
  Mercatus, Othering & Belonging, HCD, Napa Sonoma ADU Center).

Does not cover: per-jurisdiction durations; completeness/resubmittal cycles;
share of applications exceeding 60 days; whether a jurisdiction imposes a step
§ 66317 forbids.

### Q2. Local ADU ordinance content analysis — substantive or procedural?

**Verdict: ALREADY DONE for substantive standards; GENUINELY OPEN for
procedure.** Every ADU ordinance-coding effort found codes what rules exist, not
what steps an applicant must take.

- **Terner California Residential Land Use Survey** (Mawhorter & Reid 2018,
  *Local Housing Policies Across California*). Microdata, codebook and instrument
  open at `https://ternercenter.berkeley.edu/california-land-use-survey-data/`
  and read directly. Universe 539 jurisdictions (482 cities + 57 counties);
  **271 responded** (252 cities + 19 counties), 50% response, 70% of state
  population; **single wave 2017–18, never repeated**; **207 variables**. The
  **entire ADU block is 6 items**: minimum lot size, maximum ADU size,
  off-street parking, total fees, one 3-category "has your jurisdiction adopted a
  local ADU ordinance [with] timely ministerial review, reduced fees, and reduced
  parking", plus `apl_adu` application frequency. Decisive negatives:
  **no ADU approval-time variable at all** (the `apt_*` approval-time variables
  are ordinal buckets and exist only for single-family and multifamily by
  entitlement path); **zero procedural-step variables** — grepping codebook and
  instrument for pre-application, completeness review, plan check, correction
  cycles, referrals and inspections returns nothing; "hearing" appears **exactly
  once**, in a planning-staff-headcount question. Process appears only as `fac_*`,
  a nine-item **Likert perception battery** on what "delays approvals". ADU
  coverage is thin even for substance: the median value of `adu_fees` and
  `adu_minlotsize` is a missing sentinel (−96/−97) — **over half of respondents
  gave unusable values** — and `adu_offstpark` has 94 of 271 unusable.
- **Pfeiffer (2019), *Regulating ADUs in California: Local Approaches &
  Outcomes*, Terner Center.** An "ADU Regulation Index" of exactly **four**
  z-scored indicators — minimum lot size ratio, maximum unit size, off-street
  parking spaces, total fees — for **n = 220 localities**. Outcome is ADU
  **application frequency**, dichotomised. Notes in a footnote only that "some of
  the surveyed jurisdictions reported having standards that are now out of
  compliance with state law" — flagged, never coded. Data is the 2017–18 survey,
  so it **predates** AB 68 / AB 881 / SB 13.
- **Wielga (2025), "Local Government Accessory Dwelling Unit Policies After State
  Preemption in California", *State and Local Government Review*,
  10.1177/0160323x241286459** (preprint 10.21203/rs.3.rs-3392407/v1;
  dissertation 10.32469/10355/105942). Terner survey plus his own ordinance
  review, comparing **maximum unit size** and **minimum lot size** before and
  after preemption. A genuine competitor for substantive coding and for a narrow
  numeric form of compliance movement; touches neither procedure nor the
  ministerial/60-day mandate.
- **Alameldin & Garcia (2022), *State Law, Local Interpretation: How Cities Are
  Implementing Senate Bill 9*, Terner.** Coding of SB 9 implementing ordinances
  in **10 cities** (height, max unit size, design standards, affordability,
  easements, setbacks, parking). SB 9, not ADU; describes the ministerial mandate
  as background only.
- **Hamilton & Houseal (2023), *Legalizing ADUs at the State Level: A New
  Hampshire Case Study*, Mercatus.** ADU ordinances coded for **29 NH
  municipalities** plus permits for 8. Process enters as a **single binary**: 48%
  require discretionary review. The closest prior art in the think-tank slice —
  and it stops exactly one level above step structure. Also **Hamilton & Peterson
  (2025), *A Taxonomy of State ADU Laws*** — 18 variables × 18 states including
  ministerial/by-right, but at **state-statute level, not local ordinance**.
- **Furth & Gonzalez (2019), MATCHR index, Mercatus** (SSRN 10.2139/ssrn.3463421).
  **249 California cities + 16 unincorporated counties** — the largest CA
  jurisdiction count found — but substantive standards only (lot size, height,
  parking), **no ADU provisions, no process**, built partly on the same Terner
  survey.
- **Pham (2021), SJSU, 10.31979/etd.2bgv-svy5**; **Gagen (2019, 2023)** legal
  mapping of Massachusetts ADU bylaws. Single-county and out-of-state
  substantive/document compliance.
- **Napa Sonoma ADU Center** — 16 per-jurisdiction ADU rule pages (standards,
  fees, prose process), no durations. The closest existing per-jurisdiction ADU
  process inventory, and it is a nonprofit service page, not research.
- **Casita Coalition — the most consequential negative.** Their "State Law & Code
  Interpretation" page asks "Does your local ADU ordinance meet state law?
  **Contact HCD to find out**", linking HCD's Housing Accountability Unit. They
  publish **no per-jurisdiction ADU compliance scorecard** and explicitly defer
  the question. Their corpus (ADU Best Practices Guide, Preapproved ADU Plans
  Guidebook, AB 1033 memo, **AB 2533 unpermitted-ADU guidance — directly on the
  project's pilot statute**) is prescriptive guidance, uncoded.

### Q3. HCD Annual Progress Reports as a timing source

**Verdict: the DATA is excellent and fully public; the per-jurisdiction ANALYSIS
is open, but the METHOD is already published.** See §7 for the two-part direct
answer the brief demanded, with verified field names, row counts and caveats.

### Q4. Measuring local regulatory/permitting variation as structure rather than score

**Verdict: PARTIALLY DONE.** Procedural attributes are measured — but always as
an index, a scalar count, or a single binary/categorical flag, and always with one
source treated as ground truth.

- **Gyourko, Hartley & Krimmel (2021), "The local residential land use
  regulatory environment across US housing markets: Evidence from a new Wharton
  Index", *Journal of Urban Economics*** (WRLURI 2018 update; original Gyourko,
  Saiz & Summers 2008, *Urban Studies*). Survey-derived subindices including
  approval delay. Scalar index per jurisdiction.
- **O'Neill, Gualco-Nelson & Biber (2019), *Comparing Perceptions and Practice:
  Why Better Land Use Data is Critical to Ground Truth Legal Reform*, Terner /
  UC Berkeley Law.** **The closest methodological competitor in the grey
  literature.** Per-jurisdiction elapsed time **from administrative records** for
  **9 California cities** (SF, Oakland, San Jose, Redwood City, Palo Alto, LA,
  Santa Monica, Pasadena, Long Beach), all residential development of **5+ units**
  fully entitled 2014–2016, ~**25 characteristics per development** including
  entitlement types, environmental review, approval timeline, appeals and
  litigation. Sources: jurisdiction websites, public notices, environmental
  documents, commission/council agendas, approved-development lists, parcel maps,
  **plus public records requests**. Measures from the **application file date**,
  not the survey's "deemed complete". Headline: planners systematically
  **underestimate** approval times relative to administrative reality — which is
  our documented-vs-enacted finding, for a different statute. **Explicitly
  excludes ADUs**: they studied only subdivisions of 5+ homes.
- **O'Neill, Gualco-Nelson & Biber, *Examining the Local Land Use Entitlement
  Process in California* (Working Paper #2), UC Berkeley CLEE/IURD + Columbia.**
  Median and mean approval time in months **per jurisdiction**, disaggregated by
  project size and CEQA review type, for 4 SoCal cities. Contains the **closest
  thing anyone has to per-jurisdiction procedural coding**: Figure 2 codes the
  **Primary Discretionary Review Mechanism** per jurisdiction (LA = Site Plan
  Review; Santa Monica = Architectural Review; Long Beach = Site Plan Review;
  Pasadena = Design Review) plus the exemption threshold — but that is **one
  categorical variable for 4 jurisdictions**, not a step sequence. The parent
  project spans 16 cities in 3 phases. **Zero ADU mentions.**
- **Monkkonen, Lens & Manville (2020), *Built-Out Cities? How California Cities
  Restrict Housing Production through Prohibition and Process*, Terner/UCLA**
  (SSRN 10.2139/ssrn.3630447). Appendix B read directly: its **"Process Index"**
  has five sub-indexes built **entirely from the self-report Terner survey** —
  discretion, approval time (ordinal months + Likert), impact fees, public
  opposition, CEQA. **It counts no procedural steps.** The body text's claim that
  the index captures "how many hearings they must attend" is **rhetorical
  framing, not measurement — there is no hearings variable in the survey.**
  Multifamily, not ADU. Their own finding is that the process index is *not*
  associated with permitting — an argument for a better instrument, not against
  one. The published version, **Monkkonen, Manville & Lens (2024), "Built out
  cities? A new approach to measuring land use regulation", *Journal of Housing
  Economics* 74:101982, 10.1016/j.jhe.2024.101982, drops process entirely** and
  measures self-reported zoned capacity instead.
- **Manville, Monkkonen, Gray & Phillips (2022), "Does Discretion Delay
  Development? The Impact of Approval Pathways on Multifamily Housing's Time to
  Permit", *JAPA* 89(3), UCLA Lewis Center/ITS.** **N = 352 multifamily (10+ unit)
  projects, City of LA only**, 2018–Q1 2020, from LA City Planning entitlement
  cases plus LADBS permit records. Median non-TOC discretionary **748 days** vs
  by-right under 500. Process is a **binary by-right/discretionary label × TOC
  flag** — not steps, not ADU, one jurisdiction. **UCLA owns the "approval
  pathway → time to permit" framing and is the group most likely to extend it to
  ADUs.**
- **Bronin et al., National Zoning Atlas** (10.2139/ssrn.4476927;
  10.2139/ssrn.5335143; 10.2139/ssrn.3792544). >200 regulatory characteristics
  per district, and it **does** code process — minimally: "Allowed (As of Right)"
  = administrative staff review vs "**Public Hearing Required**". One binary
  procedural attribute, human review treated as producing truth.
- **World Bank *Doing Business*, "Dealing with Construction Permits"**
  (e.g. 10.1596/978-1-4648-0667-4_dealing_with_permits). **The strongest prior
  art on counting steps**: for a standardised warehouse it records the number of
  **procedures**, days and cost per economy, and per city in Subnational Doing
  Business. Per-jurisdiction step enumeration — but expert-coded from one
  respondent set, deterministic, no uncertainty about whether a step exists.
- **Fauth & Soibelman (2022), "Conceptual Framework for Building Permit Process
  Modeling: … Germany and the United States", *Buildings* 12(5):638,
  10.3390/buildings12050638**; **Fauth, Bloch & Soibelman (2023), ECAM
  10.1108/ecam-06-2023-0593**; **Nisbet & Fauth (2026), "Developing a reference
  building permit process model", *Building Research & Information*
  10.1080/09613218.2026.2613845.** As-is and reference building-permit process
  models from expert interviews, covering **by-right and non-by-right** cases,
  with cross-jurisdiction comparability as the stated aim. The reference
  step-model literature; we must cite it.
- **Mleczko & Desmond (2023), *Urban Studies*, 10.1177/00420980231156352** — NLP
  over ordinances at near-universe scale for two MSAs, output a scalar Zoning
  Restrictiveness Index. **Pendall et al. (2018), *Housing Policy Debate*,
  10.1080/10511482.2018.1494024** (NLLUS) and **Pendall (2020), *JAPA*,
  10.1080/01944363.2020.1725237** — the "measure what's on the books" argument,
  still provision inventories and indices.
- **Rice, Siddiki, Frey, Kwon & Sawyer (2021), "Machine coding of policy texts
  with the Institutional Grammar", *Public Administration*, 10.1111/padm.12711.**
  Parses policy text into structured institutional statements at scale — the
  nearest methodological cousin for extracting structure from legal documents,
  but deterministic extraction of syntactic rule statements, not latent step sets.
- Duration studies, single jurisdiction: **Gabriel & Kung (2024), "Development
  Approval Timelines, Approval Uncertainty, and New Housing Supply: Evidence from
  Los Angeles", 10.2139/ssrn.4872147**; **Mussalli (2026), Providence RI,
  10.2139/ssrn.6091668** (original dataset scraped from the city permitting
  portal, 2015–2025); **Goggin (2018), *Measuring the Housing Permitting Process
  in San Francisco*, Terner** (2,474 developments but only **167 with
  permitting-time data**, and the author warns the dataset "is error-prone").

Nobody has a per-jurisdiction *set-valued* representation of procedural steps,
inferred rather than read off one source, across many jurisdictions, with
uncertainty.

### Q5. Applicant-reported process evidence

**Verdict: PARTIALLY DONE — thinner than CalFresh's equivalent, but not empty,
and one item is closer than expected.** There is qualitative and survey work on
ADU owners and builders; nothing compares experienced process against documented
or mandated process, and nothing is resolved per jurisdiction.

- **Chapple, Ganetsos & Lopez (2021), *Implementing the Backyard Revolution:
  Perspectives of California's ADU Owners*, UC Berkeley Center for Community
  Innovation** (HCD-funded; the **first statewide ADU owner survey**).
  n ≈ **694–724** ADU owners, recruited by postcard to permitted-ADU addresses.
  Median construction cost $150,000 / $250 psf; median rent $2,000. Critically,
  **Q22 does ask a duration** — "from the beginning of the approval process start
  to completion of the ADU, how many months did it take?" — reported as a
  statewide histogram in 5-month bins (1–5: 14%; 6–10: 28%; 11–15: 25%; 16–20:
  14%; 21–25: 19%). That is approval-start through **construction completion**,
  self-reported, **pooled statewide, not per jurisdiction**. **Q23 collapses
  "duration of permitting timelines, number of plan revisions required, and code
  changes impacting design mid-city review" into a single 5-point Likert**,
  reported by region. Recommends fixing local "requirements that are out of
  compliance with [state law]" without coding compliance. This is the nearest
  applicant-reported item and it is exactly one aggregation level too coarse.
- **Greenberg, Phalen, Chapple, Garcia & Alameldin (2022), *ADUs for All:
  Breaking Down Barriers to Racial and Economic Equity in ADU Construction*,
  Terner.** Four 90-minute focus groups (~23 homeowners) plus **30 practitioner
  interviews**. Reports "deep frustration with months-long delays at several
  points in the process" — the phenomenon we would measure, stated qualitatively
  and not quantified or attributed to jurisdictions.
- **Proussaloglou (2024), "Architecture and the Accessory Dwelling Unit
  Revolution: Perspectives from Builders", *Critical Planning* (UCLA),
  10.5070/cp827063133**, open access. **Ten interviews** with LA architects,
  contractors and ADU technology firms after AB 2299; "few inquiries turn into
  finished buildings", and successful builders succeed by "mastering building
  codes and regulations, engaging directly with local governments".
- **Volker & Handy (2022), *JAPA*, 10.1080/01944363.2022.2036222** — Sacramento
  homeowner survey about **willingness**, not permitting experience. **Crane
  (2020), UCLA dissertation, *Is Granny in that Flat?*** — LA permit counts,
  unpermitted-ADU enumeration and an original **permit-puller survey**, one city.
  **Mukhija, Cuff & Serrano (2014), *Backyard Homes & Local Concerns*, UCLA
  cityLAB**; **Wasserman (2019), Lewis Center**; **Wegmann & Nemirow (2011),
  UC Berkeley IURD**.
- **Moynihan, Herd & Harvey (2014), "Administrative Burden", *JPART*,
  10.1093/jopart/muu009** — 852 citations, and Crossref shows **no application to
  land-use or ADU permitting**. The theory is established; its transfer here is
  not made. No forum/online-text-based measurement of permitting experience
  appears in Crossref at all.

### Q6. Occupancy / imperfect-detection models applied to institutions

**Verdict: GENUINELY OPEN as to priority, but IDENTICAL to the CalFresh position —
ADUs buy us nothing here, and the published objection still awaits us.** Strong
adversarial check: all **20** OpenCitations-indexed papers citing Cook et al.
(2017) were resolved and every one is conflict/event-data or event-coding
measurement (Wegenast & Schneider; von Borzyskowski & Wahman; Daxecker et al.;
Croicu & Eck; Demarest & Langer; Cook & Weidmann; Chenoweth et al.). The lineage
never left media-reported events. Crossref/arXiv/Zenodo sweeps for occupancy +
policy/institutions/organizations/governance returned only ecology.

- **Cook, Blas, Carroll & Sinha (2017), *Political Analysis*,
  10.1017/pan.2016.13** (known). Latent binary presence with source-specific
  reporting probabilities — the structural template, but units are events,
  sources are media outlets, no site hierarchy over a set of steps.
- **Weidmann (2015), *AJPS*** (known). Cites MacKenzie and **declines** the
  transfer because it fails when all sources share a bias. This bites harder here
  than for CalFresh: municipal pages, checklists and ordinances demonstrably copy
  one another and may all omit the same internal routing step.
- **Caughey & Warshaw (2016), "The Dynamics of State Policy Liberalism,
  1936–2014", *AJPS*, 10.1111/ajps.12219.** Dynamic latent-variable model over
  **148 binary policy-adoption indicators** across states and years —
  structurally very close to our z[j,s] matrix, except the indicators are treated
  as observed without error. The strongest "someone has the matrix but not the
  detection" citation.
- **Fariss (2014), *APSR*, 10.1017/s0003055414000070.** Latent state-level trait
  from multiple imperfect documentary monitors with an explicitly time-varying
  reporting standard. Best institution-level analogue; continuous trait, not a
  discrete step set.
- **Pemstein et al., "The V-Dem Measurement Model"** (10.2139/ssrn.3167764 and
  successors). Ordinal IRT with coder-specific reliability over institutional
  characteristics per country-year. Models coder error, not source *silence*;
  commissioned experts, not found documents.
- **Bird & King (2018), *Annual Review of Statistics and Its Application*,
  10.1146/annurev-statistics-031017-100641**; **Worthington, McCrea, King &
  Vincent (2020), *Crime & Delinquency*, 10.1177/0011128720974319.** A
  self-aware ecology→social-science transfer of the same family; estimand is
  population size, not presence of a practice at a site. **Stoner, Economou &
  Drummond Marques da Silva (2019), *JASA*, 10.1080/01621459.2019.1573732** —
  hierarchical under-reporting for counts.
- **Albert & Dodd (2004), *Biometrics*, 10.1111/j.0006-341x.2004.00187.x** (and
  Albert 2021, *Statistics in Medicine*, 10.1002/sim.9085). The
  latent-class-without-a-gold-standard identification warning a referee will cite.

## 3. Nearest prior work

Four items on four axes. None is close on more than one — but together they
enclose the proposal more tightly than the CalFresh gate's two did.

**On the ADU timeline itself: Underriner (2024), Terner, "Comparing ADU
Permitting Time Inside and Outside the Coastal Zone".** Same statute, same state,
same data (APR Table A joined to Table A2), same quantity (ADU application→permit
days), and ~29,000 observations. Daylight: aggregated to three counties ×
coastal/non-coastal instead of per jurisdiction; no compliance test against the
60-day clock; no step structure; a short blog post rather than a measurement
paper. **But this is the item that most changes our framing: the APR join is
published method, not our discovery, and HCD reportedly computes these timelines
internally.**

**On the documented-vs-enacted finding: O'Neill, Gualco-Nelson & Biber (2019),
"Comparing Perceptions and Practice".** Nine California cities, all 5+ unit
residential entitlements 2014–2016, ~25 coded characteristics per development from
administrative records and public records requests, measuring from the
application file date — and the headline is that **planners systematically
underestimate approval times relative to administrative reality**. That is our
documented-vs-enacted claim, executed, for multifamily entitlements. Daylight:
**explicitly excludes ADUs and all single-family**; 9 jurisdictions; hand-coded;
no latent-variable model; process captured as entitlement types and one
categorical review mechanism, not a step set.

**On the burden decomposition: City of Seattle OPCD, *2023 Accessory Dwelling
Unit Report*.** Figure 12: for pre-approved detached-ADU plans 2020–2023,
**80.9 days average intake-to-issuance, 58.7 days in agency (SDCI) review, 22.2
days out for correction with the applicant, 2.7 correction cycles**; for other
2023 DADUs, 133 days, 74 with the agency, 59 with the applicant, 3.2 correction
cycles. Our exact decomposition, published annually, used to evaluate a
procedural intervention. Daylight: one jurisdiction, not California, agency
self-report, averages without uncertainty, no cross-jurisdiction comparison, no
mandate comparison. Seattle can do this because it owns the event log; our whole
problem is that ~500 California jurisdictions do not publish one.

**On the estimand: Pfeiffer (2019) ADU Regulation Index over the Terner survey.**
Per-jurisdiction ADU regulatory coding, n = 220, with outcomes. Daylight: four
substantive components collapsed to a restrictiveness index; zero procedural
items; zero ADU duration items; pre-2020-reform data.

| dimension | Underriner 2024 | O'Neill et al. 2019 | Seattle OPCD 2023 | Pfeiffer 2019 / TCRLUS | proposed contribution |
|---|---|---|---|---|---|
| statute | ADU | 5+ unit entitlements (ADUs excluded) | ADU | ADU | ADU |
| jurisdictions | 3 counties × coastal/not | 9 CA cities | 1 | 220–271 CA | ~400–500 CA with usable data |
| procedural steps | 0 | entitlement types + 1 categorical review mechanism | 3 phases + corrections cycles | 0 | ~15–20, per jurisdiction |
| elapsed time | yes, aggregated | yes, per jurisdiction, from file date | yes, phase-decomposed, agency vs applicant | 4-band self-report; none for ADUs | yes, per jurisdiction per phase |
| evidence | HCD APR administrative dates | administrative records + PRA requests | the agency's own event log | one survey response per jurisdiction | municipal ADU pages, ordinances, checklists, fee schedules, statute, applicant/architect reports |
| observation model | none — dates observed | none — records taken as truth | none needed | none — survey answer is truth | detection probability per source genre; silence is a non-detection |
| mandate comparison | 60-day cited, not tested | no | no | noted in a footnote, not coded | § 66317's 15-business-day / 60-day / 60-business-day clocks and the no-hearing rule |

The daylight is real but specific: **many steps rather than phases, a categorical
label, or none**; **hundreds of jurisdictions rather than one, three or nine**;
**documents with a modelled disclosure process rather than one source taken as
truth**; and **scored against a precise statutory mandate**. Everything else on
the proposal's face belongs to one of these four.

## 4. Threats to the claim

Ordered by how badly each would have hurt.

1. **Underriner (2024), Terner.** Already published ADU application→permit
   durations from the exact APR Table A→A2 join, and its footnote says HCD
   computes such timelines internally. Any framing in which "we can compute ADU
   permit durations from state data" is the contribution is dead.
2. **City of Seattle OPCD ADU Annual Reports (2022, 2023).** Publishes
   phase-decomposed, agency-vs-applicant, corrections-cycle-counted ADU permit
   timelines. Presenting that decomposition as novel would be embarrassing.
3. **O'Neill, Gualco-Nelson & Biber (2019).** Already published the
   documented-vs-enacted result (planners underestimate approval times) from
   administrative records across 9 California cities. Our headline is their
   headline for a different project class.
4. **Manville, Monkkonen, Gray & Phillips (2022), *JAPA*.** UCLA owns the
   "approval pathway → time to permit" framing with a published 748-vs-500-day
   result, and is the group most likely to extend it to ADUs next.
5. **Ichaki (2026), Zenodo 10.5281/zenodo.22079795.** A published, DOI'd,
   per-city ADU permit-timeline dataset with percentiles and within-N-day shares.
   Narrow (3 CA cities, garage conversions) but it kills "no ADU timeline dataset
   exists". Cite and extend, do not ignore.
6. **World Bank Doing Business, "Dealing with Construction Permits."** Counts
   permitting **procedures**, days and cost per jurisdiction, including
   subnationally. "Nobody has enumerated permitting steps per jurisdiction" is
   false.
7. **Casita Coalition (2024), *Preapproved ADU Plan Programs: Essential
   Elements*.** Publishes a "partial table of ADU development tasks" in three
   phases with ~12 tasks (site feasibility, surveying/soils, design, financing;
   site plan & application, **work with all authorizing agencies — fire, public
   health, utilities**, full plan set, required changes; subcontractors,
   materials, **order inspections and make requested changes**, tenanting). Our
   ~15–20 step universe is an elaboration of an already-published inventory.
8. **SnapADU** (`snapadu.com/regulation_community-sitemap.xml`, 19 San Diego
   County jurisdictions) and **Napa Sonoma ADU Center** (16 jurisdictions).
   Per-jurisdiction Yes/No tables of required submittals and reviews — the same
   shape as z[j,s] — plus coarse timelines ("Standard Timeline: 4–5 months") and
   fee rates. Commercial and unsourced, but "nobody has represented an ADU
   process per jurisdiction" is false.
9. **Chapple, Ganetsos & Lopez (2021) ADU owner survey, n ≈ 700.** Already asks
   applicants for duration and for a combined permitting-timeline /
   plan-revisions / mid-review-code-change rating. One aggregation level coarser
   than ours, but the instrument exists and is HCD-funded.
10. **Fauth and colleagues' reference building-permit process models (2022, 2023,
    2026).** An entire literature on as-is and reference permit process models
    including by-right cases, with cross-jurisdiction comparability as its stated
    aim. Not knowing about it would look bad.
11. **Cook et al. 2017 and Weidmann 2015.** Identical exposure to CalFresh. Cook
    et al. is an occupancy model in all but name; Weidmann already published the
    shared-bias objection; Albert & Dodd compound it with the LCA-identification
    warning.
12. **Monkkonen, Lens & Manville built a process index and then dropped it** from
    the published version after finding it uncorrelated with permitting and its
    base data incomplete. That is a warning about our construct's predictive
    value, not merely about priority — and the CalFresh gate already recorded a
    fitted model losing to a pooled Beta baseline.
13. **Measurement semantics in the APR data — the ugliest way to be wrong.** The
    Table A dictionary defines `APP_SUBMIT_DT` as the submittal date *"If the
    application was incomplete at the time of submittal, this will reflect the
    date the application was determined to be complete."* The APR clock is
    therefore **left-truncated past exactly the completeness/resubmittal loop
    that § 66317(a)(2) regulates** and that is plausibly the largest applicant
    burden — and jurisdictions differ in which convention they record. Raw
    per-jurisdiction output is visibly corrupt: San Fernando mean
    entitlement→permit **−434 days**, Monterey −5, Anaheim 0; Anaheim's
    application→permit median is 0 days across 1,163 records (100% zero);
    Glendale 34.8% zero-day plus 61 negative durations; 31.3% zero-day in a raw
    pooled statewide sample, against clean jurisdictions like San Diego (0.3%)
    and San Jose (0.0%). Publishing a per-jurisdiction compliance ranking off
    this without a reporting-convention model would be indefensible.

## 5. What would make this publishable

1. **Claim the step-resolved within-stage structure, because no data source
   contains it.** APR has four milestones and no within-stage events. Seattle has
   corrections cycles for one city. The Terner survey has zero step variables.
   Our contribution should be the per-step latent structure — which referrals,
   which pre-application requirement, which plan-check and corrections loops a
   jurisdiction actually runs — precisely because no index, survey or
   administrative extract can see it.
2. **Make § 66317 as amended the comparison, and say why it is now.** The mandate
   is unusually explicit (ministerial, no hearing, 15 business days to
   completeness with a non-expandable cure list, deemed complete, 60 days to
   decide, deemed approved, appeal in 60 business days), plus AB 1332's 30-day
   preapproved-plan review. SB 543 and AB 1170 take effect 2026-01-01, so the
   current regime is unstudied and the compliance question is live. **Nobody codes
   ministerial/60-day compliance per California jurisdiction** — Casita Coalition
   explicitly defers it to HCD, and HCD's own per-jurisdiction enforcement record
   is trapped in a Power BI widget.
3. **Do not claim the timeline as the finding; claim the documentation gap.**
   The timeline is computable by anyone from APR — Terner already published the
   method — and parts of it exist for Seattle and three CA cities. What nobody has
   is *what jurisdictions publish about their own process*, and the divergence
   between that, the adopted ordinance, the statute, and what applicants report.
   That is a fact about municipal documentation, which is our corpus's comparative
   advantage and the one thing O'Neill et al. could not do at scale.
4. **Position against O'Neill/Biber and against UCLA explicitly.** O'Neill et al.
   own "hand-code entitlement processes from administrative records"; UCLA owns
   "approval pathway → time to permit". Differentiate on: **ADUs vs 5+ units**,
   **hundreds of jurisdictions vs 4–9 vs 1**, **coded step structure vs a binary
   or categorical pathway label**, and **modelled documentary detection vs records
   taken as truth**.
5. **Answer Weidmann before a referee does.** A shared-bias / conditional
   dependence story is mandatory: municipal pages, checklists and ordinances are
   not independent draws. Build a validation subset where true step presence is
   known — jurisdictions where the actual permit routing table is obtainable
   (SF's addenda/routing table `87xy-gk8d`, LA County's `WORKCLASS_NAME`) — and
   check recovered step presence against it. A convergent posterior is not
   recovery.
6. **Use APR as external validation, not as the outcome, and pre-register the
   screens.** Report APR-derived application→permit durations as a check on the
   model's burden predictions, with left-truncation and degenerate-reporter
   screens stated inline. Tracking-ID join primary, APN fallback flagged (Terner
   used APN; the tracking-ID join is cleaner but loses 68 jurisdictions). Exclude
   or model zero-day and negative-duration reporters and report how many
   jurisdictions are lost. The LA cross-validation is worth reporting as a methods
   contribution in itself: an APR-join median of 141 days (n = 29,977) against a
   city-portal median of 144 days (n = 15,689), agreeing within 1–3 percentage
   points at every threshold.

## 6. Blocked, and limits on coverage

**A blocked query is not a negative finding.** Everything below is unresolved,
not absent.

**Scholarly APIs**
- **OpenAlex: entirely unusable this session.** Two attempts, both HTTP 429:
  "Insufficient budget. This request has no API key, so it counts against the
  free daily budget shared by everyone on your network's IP address, and that
  budget is used up ($0.0003 remaining; resets at midnight UTC)", `retryAfter`
  ≈ 12,940 s. No OpenAlex search or citation-graph traversal was possible;
  coverage rests on Crossref, OpenAIRE, arXiv, Zenodo, OpenCitations, sitemaps,
  WordPress REST search and direct fetches.
- **Semantic Scholar** not used (429 with zero rows per the brief).
- **Crossref** returned HTTP 429 after ~12 queries and again when two agents
  queried concurrently; it tolerates roughly one serial stream, and needs
  `mailto=` for the polite pool. One query — "permit approval times single family
  housing days jurisdictions United States variation" — was **never completed**.
- **OpenAIRE** `title=` with long multi-word strings returns 200 with 0 rows
  because it converts to an exact-title match; use `keywords=`. Two such 0-row
  results are **not** absence.
- **Recodification search hazard.** ADU law was moved by Stats. 2024, Ch. 7,
  Sec. 20 out of former Gov. Code **§ 65852.2** into Gov. Code Ch. 13,
  §§ 66310–66342. Nearly all existing literature cites § 65852.2, so any coverage
  check keyed on "66314"/"66317" under-counts prior work. Both were searched.
- **Weak negatives, reported as weak**: arXiv returns 0 entries for
  `"occupancy model" AND "imperfect detection" AND (policy OR institutions OR
  administrative)` and four related phrase queries; Zenodo returns 0 for
  `"occupancy model" AND "public policy"` and `"imperfect detection" AND
  institutions` against working controls (`zoning` → 1,501). Both corpora cover
  the relevant journals thinly.
- **Not searched at all**: law reviews (poorly covered by Crossref, no HeinOnline
  access), so legal commentary on § 66317 compliance and the deemed-approved
  remedy is unassessed; SSRN full texts; planning conference proceedings (ACSP).

**Publishers and repositories**
- **Taylor & Francis: HTTP 403** for 10.1080/09613218.2026.2613845 (Nisbet &
  Fauth) and 10.1080/01944363.2022.2036222 (Volker & Handy) — characterised from
  title and secondary description only.
- **furmancenter.org: HTTP 403** via curl (Cloudflare) for the publication page,
  the guessed PDF path and the publications index; retrieved via WebFetch, which
  returned the abstract only. **I have not read the Marantz, Elmendorf & Kim
  (2023) methods section.** Given it is the nearest prior work on the model axis,
  this is the most important single gap in this review. Treat "no other Furman ADU
  work" as unverified.
- **eScholarship: entire HTML/PDF/search layer is CloudFront 403.** No methods
  section was read from any eScholarship PDF; its GraphQL API worked for ~15
  minutes then 403'd; OAI endpoints returned 403 or "identifier unknown".
  **Genuine coverage gap: the `ucla_etd` corpus (14,009 UCLA theses) was cut off
  by rate-limiting at 0 records retrieved** — other UCLA theses on ADU permitting
  may exist unenumerated (the one found, Crane 2020, surfaced only via a podcast
  show-note).
- **ICPSR: 403 via both curl and WebFetch — genuinely unverified.**
- **RAND entirely unassessed** (`rand.org` 403 to curl and WebFetch).
  **HUD PD&R / huduser.gov entirely unassessed** (202 with 0-byte Imperva
  interstitials on every path). This matters: *Cityscape* is a HUD journal and may
  host a Marantz/Elmendorf ADU-compliance piece.
- **mercatus.org** and **urban.org** content pages 403 to curl, retrieved via
  WebFetch; `urban.org/publications/sitemap.xml?page=6–8` 429'd then recovered.
  **Brookings and AARP on-site search are robots-disallowed**, so the AARP/APA
  ADU guide was never read (characterised from its landing page plus Casita's
  summary); AARP PDFs are robots-disallowed and were not fetched.
- **Terner/CLEE link rot**: `law.berkeley.edu/.../Getting_It_Right.pdf` and
  `clee.berkeley.edu/wp-content/uploads/archive/2026/01/Getting_It_Right.pdf` both
  **404** — **"Getting It Right" (O'Neill et al., Feb 2018) was never read**;
  Working Paper #2 was substituted. `ternercenter.berkeley.edu/.../2021/04/Implementing-the-Backyard-Revolution.pdf`
  **404**; `www.ternercenter.berkeley.edu` is **NXDOMAIN** (drop the `www.`);
  `ternercenter.berkeley.edu/research-and-policy/california-land-use-survey/`
  **404** (the working path is `/california-land-use-survey-data/`).
  `aducalifornia.org` **403** to curl and WebFetch — the ADU owner survey was
  **recovered via web.archive.org**; `archive.org/wayback/available` 429'd once
  then succeeded.
- **HCD**: `hcd.ca.gov/planning-and-community-development/{accessory-dwelling-units,
  housing-element-compliance-report, housing-open-data-tools/apr-dashboard,
  housing-element-implementation-and-apr}` all **404** (correct path is
  `hcd.ca.gov/housing-open-data-tools/apr-dashboard`); the APR dashboard is an
  **embedded widget** so its metric names could not be read, and the Technical
  Assistance & Enforcement Letters dashboard is **Power BI with no CSV export**,
  so per-jurisdiction enforcement findings could not be extracted. The only
  verified statement that HCD computes ADU timelines is Terner's footnote 5.
- **City portals**: `data.sfgov.org` `$select`/`$where` **403** (WAF; bypass with
  `$query=` plus `Accept: application/json`); `data.lacity.org/api/views/…json`
  **403**; `data.sandiego.gov/api/3/action/*` **404** (static S3, not CKAN);
  `seshat.datasd.org/` root **403**;
  `data.{sandiego,sanjoseca,cityofsacramento}.gov/api/catalog/v1` and
  `data.lacounty.gov/api/catalog/v1` **404**; `data.longbeach.gov` four API paths
  **404**; Santa Cruz hubs **401** ×3;
  `api.census.gov/data/timeseries/eits/bps/variables.json` **404**;
  `api.github.com/search/code` **401**. **Genuine negatives for bulk city data**
  (a scalability limit, not a block): Oakland has no permit dataset in its
  313-item catalog (Accela Citizen Access, login required, per-record lookup
  only); Long Beach has 15 datasets and zero permits; Santa Cruz County's
  176-dataset hub has no permit records; San Jose has the cleanest ADU code found
  (`SUBTYPEDESCRIPTION='ADU   Accessory Dwelling Unit'`) but **publishes no
  application date**.
- **Symbium** (`symbium.com`) fetched 200 but `/adus` is **404** and its sitemap
  contains no ADU page; its public product line is now solar/energy instant
  permitting, so historical ADU rule-codification is unverifiable. Symbium is
  primarily a solar story and is left to the parallel solar review.
- **auditor.ca.gov** `/reports/recent` and `information.auditor.ca.gov/reports/recent`
  **404** — the California State Auditor was not searched. LAO site search (2,937
  results) surfaces ADUs only in budget handouts; no LAO ADU permitting study.
- **Resolved inter-agent conflict, recorded for transparency**: one agent
  described the Monkkonen et al. process index as counting required steps and
  hearings across 540 Housing Elements. Reading Appendix B directly shows it is
  built **entirely from the self-report Terner survey**, and that the report's
  "how many hearings" language is rhetorical because **the survey contains no
  hearings variable**. The first description was wrong; §2 Q4 reflects the
  verified reading.

## 7. Direct answer: does HCD APR data already provide per-jurisdiction ADU processing timelines?

The brief asked for both facts stated separately. They point in opposite
directions and both are true.

**Good news as a timing data source — yes, the raw material is fully public,
large, and ADU-identifiable.** Verified by live API calls returning real rows.
The dataset is "Housing Element Annual Progress Report (APR) Data by Jurisdiction
and Year", California HCD, on `data.ca.gov` (dataset
`81b0841f-2802-403e-b48e-2ef4b751f77c`), filed under Gov. Code § 65400, with 24
resources — Tables A, A2, C, D, E, F, F2, G, H, I, K, L, each CSV plus a DOCX data
dictionary — queryable through the CKAN `datastore_search_sql` endpoint.

- **Table A** (`c78b769d-…`, 358,268 rows) carries **`APP_SUBMIT_DT`**,
  `APPLICATION_STATUS`, `TOT_APPROVED_UNITS`. For `UNIT_CAT='ADU'`: **167,721
  rows, 467 jurisdictions, 2018–2025, 100% with a populated application date.**
- **Table A2** (`fe505d9b-…`) carries exactly three date fields —
  **`ENT_APPROVE_DT1`, `BP_ISSUE_DT1`, `CO_ISSUE_DT1`** — alongside
  `JURIS_NAME, CNTY_NAME, YEAR, APN, PROJECT_NAME, JURS_TRACKING_ID, UNIT_CAT,
  LATITUDE, LONGITUDE`. For `UNIT_CAT='ADU'`: **281,353 rows, 516 distinct
  jurisdictions, YEAR 2018–2025.** Date completeness on those rows:
  `BP_ISSUE_DT1` 202,314 (71.9%); `CO_ISSUE_DT1` 103,938 (36.9%);
  `ENT_APPROVE_DT1` only 69,722 (24.8%) — sparse precisely *because* ADUs are
  ministerial and mostly have no entitlement, which makes the entitlement→permit
  interval the weakest of the available clocks.
- **Joining Table A to Table A2 on `(JURIS_NAME, JURS_TRACKING_ID)` gives 74,189
  distinct ADU projects across 399 jurisdictions with a computable
  application→building-permit duration**, and 29,277 projects across 326
  jurisdictions with the full application→permit→occupancy chain. 281
  jurisdictions have ≥10 pairs, 152 have ≥50, 102 have ≥100. An APN fallback join
  (which is what Terner used) widens coverage to 441 jurisdictions / 92,829 pairs
  but conflates clocks and can link unrelated projects on one parcel.
- It cross-validates. For Los Angeles the APR join gives a median of **141 days
  (n = 29,977)** against **144 days** from an independent city-portal-derived
  dataset (n = 15,689), agreeing within 1–3 percentage points at every reported
  threshold; San Diego agrees directionally (172 vs 185 days).
- `UNIT_CAT` is an explicit flag (values observed: ADU, SFD, SFA, "2 to 4", "5+",
  MH), and ADUs are now **42.8% of all permitted housing rows** in the APR, up
  from 15.8% in 2018 — so this is a large object of study, not a niche.

**Bad news for novelty — real, and larger than I first judged.** **Terner has
already published ADU application→permit durations from this exact Table A→A2
join** (Underriner 2024), aggregated to three counties × coastal/non-coastal, and
its footnote 5 records that **HCD staff clean APR data "to calculate application
and permitting timelines" for their dashboard** — so the method is published and
the state agency may already run it internally. A separate published dataset
(Ichaki 2026, Zenodo 10.5281/zenodo.22079795) reports ADU permit-timeline
percentiles for three California cities from city portals. What remains unpublished
is the **per-jurisdiction** version at scale and any **compliance test against the
60-day clock**. Consequently: **we cannot claim to be first to measure a
Californian ADU permit wait, and "we computed ADU permitting days per
jurisdiction" is not on its own a defensible contribution.** It is a validation
instrument and a descriptive layer, not the paper.

**Three qualifications that stop APR from being either a scoop or a clean
instrument.**

1. **The APR clock is left-truncated in exactly the wrong place.** The Table A
   dictionary defines `APP_SUBMIT_DT` as the submittal date, *"If the application
   was incomplete at the time of submittal, this will reflect the date the
   application was determined to be complete."* The measured wait therefore
   **excludes the completeness and resubmittal loop** — the thing § 66317(a)(2)
   regulates with its 15-business-day clock and non-expandable cure list, and
   plausibly the largest single component of applicant burden. Jurisdictions
   almost certainly differ in which convention they record. This is a measurement
   seam, not noise, and it is the kind of thing our source-detection framing
   exists to handle. All APR-derived waits are therefore **lower bounds**.
2. **APR has four milestones and no within-stage events.** No completeness date,
   no resubmittal dates, no referral or plan-check events. **Our
   per-jurisdiction process-STEP goal is not served by APR at all** and remains
   genuinely open; only city portals offer within-stage structure (LA County
   `WORKCLASS_NAME`; SF's addenda/routing table `87xy-gk8d`; San Diego's
   `PROJECT_DEEMEDCOMPLETE_DATE`), and Oakland, Long Beach and Santa Cruz County
   publish no bulk permit data whatsoever.
3. **Degenerate reporting is widespread and would wreck a naive ranking.** Raw
   per-jurisdiction output is visibly corrupt: San Fernando mean
   entitlement→permit **−434 days**, Monterey −5, Anaheim 0. On the
   application→permit clock, Anaheim's median is 0 days across 1,163 records
   (100% zero); Glendale is 34.8% zero-day plus 61 negative durations; 31.3% of a
   raw pooled statewide sample is zero-day — against clean jurisdictions such as
   San Diego (0.3% zero) and San Jose (0.0%). This corruption is very likely
   *why* nobody has published the per-jurisdiction version, and it is where
   careful measurement earns its keep.

**A headline-sized preliminary number, flagged as ours and unvalidated.** On the
APR join, the share of ADU applications exceeding the 60-day statutory
ministerial clock runs Sacramento 74.5%, Los Angeles 76.6%, San Jose 86.7%, Long
Beach 88.1%, San Diego 93.0%, Torrance 94.9%, Pasadena 99.2%, Santa Monica 100%;
across 151 jurisdictions with n ≥ 30 (excluding LA), per-jurisdiction median waits
run **0 to 335 days** (p25 66, median 134, p90 219). This is a subagent probe
subject to every caveat above — especially the left-truncation, which makes these
lower bounds — and it is not yet a result. But it indicates that the divergence we
propose to measure is large, measurable, and very likely publishable if the
measurement semantics are handled honestly and the step-structure claim, not the
timeline, carries the paper.
