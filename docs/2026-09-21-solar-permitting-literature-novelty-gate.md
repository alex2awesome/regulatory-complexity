# Solar permitting (Cal. Gov. Code § 65850.5) — literature novelty / saturation gate

Date: 2026-09-21
Scope: adversarial novelty check on candidate #2 (residential rooftop solar permitting in
California), run as a comparison against the CalFresh candidate that a companion review
found substantially scooped.
Method note: OpenAlex was exhausted before this run began and never returned a row.
Crossref, arXiv, OSTI and Wayback carried the work. See §6 for the full blocked list.

---

## 1. Bottom line

**Verdict: residential solar permitting is MORE saturated than CalFresh, not less — and the
part that is saturated is precisely the part we proposed to contribute.** Recommend against
transferring the method here as the headline claim. Three independent programmes have already
built per-jurisdiction process measurements for California: (i) NREL's **SolarTRACE** publishes
a public per-AHJ `AHJ requirements` table — 8,606 AHJs nationally, **535 of California's ~540
jurisdictions** — coding structural review required, electrical review required, third-party
review, number of inspections required, rough-in inspection required, over-the-counter
availability, online and online-instant permitting, and median permit cost, alongside per-AHJ
median durations for four process phases (permit, pre-install interconnection, inspection,
final interconnection→PTO); **432 California AHJs already have both the requirement coding and
observed phase timings in one released file**. (ii) **Kaatz & Anders (2016)** coded 374 adopted
ordinances against ~13 statutory criteria across a frame of all 540 California jurisdictions,
including the written-correction-notice and single-inspection-plus-reinspection provisions we
wanted as steps. (iii) The **California Energy Commission runs a statutory per-jurisdiction
SB 379 compliance dashboard**, every city and county, last updated 2026-08-03. Our claim #1
(a step universe measured per jurisdiction) is therefore largely pre-existing, and our claim #3
(documented vs enacted) has been executed at the compliance layer twice, once by the state
itself. Worse, the identification premise is *weaker* here than in CalFresh: **365 of 386
adopting jurisdictions used, modified or took language from a single model ordinance**, so our
documentary sources are near-collinear by construction — the Weidmann shared-bias objection is
not a hypothetical for this corpus, it is a measured fact. And a fourth programme got there
first: the DOE-funded **National Solar Permitting Database** (Clean Power Finance / Vote Solar,
c. 2013) held **jurisdiction pages for over 18,000 US cities and counties with 100+
installer-reported fields each**, including inspection processes and "common errors" — i.e. our
installer-experienced per-jurisdiction census, attempted a decade ago and since abandoned. And
the sharpest blow is the oldest: the **2011 DOE SunShot Rooftop Solar Challenge questionnaire**
surveyed **>290 jurisdictions** with a check-all over 8 departmental approvals, 6 professional-
engineer reviews and **5 named inspection-trip types** — our fixed step universe, for our exact
subject matter — and then collapsed it into an unpublished 0–250 scalar (Dong & Wiser 2013).
What survives is narrow: the rework/resubmittal and reinspection loop as a *modelled* quantity
(NREL deliberately absorbs it into durations), and joining the de jure and de facto halves that
exist separately and have never been joined. Note also that the step-structure *representation*
is independently precedented outside solar — Doing Business publishes ~17 numbered procedures for
Los Angeles, WRLURI codes nine named approval entities at 0/1/2 across ~2,450 communities, and
CoSeLoG fits one configurable permit process model with per-municipality configurations across
five Dutch cities — so only the *inference under an observation model* is ours to claim.

**Plain answer to the question you flagged:** SolarAPP+ alone is **not** a per-jurisdiction
process census (264 adopting/piloting AHJs nationally, 225 in California, and per-AHJ detail
published for as few as 29). But **SolarTRACE is close to one for California**, and the **CEC
SB 379 dashboard is a literal official per-jurisdiction census** of the automated-permitting
mandate. Taken together with Kaatz & Anders, yes — the census substantially exists. This
candidate is worse than CalFresh, and the reason is specifically that the grey literature we
would be competing with is a funded, ongoing federal measurement programme with installer
data we cannot match.

---

## 2. The six questions

### Q1. Solar soft costs and permitting (NREL / LBNL "PII") — **PARTIALLY DONE, and the gap is smaller than expected**

The *published journal* literature is cost-and-duration regressions on jurisdiction covariates,
as you suspected. But the *dataset* behind it is a per-jurisdiction requirement census, which is
the part that hurts.

| Work | What it actually does |
|---|---|
| Cruce, Lara, Frey, Dalecki & Cook (2025), *Residential and Small Commercial Solar PV and Storage PI&I Timelines: A Retrospective Review (2017–2023)*, NREL/TP-6A20-92539, [10.2172/3011864](https://doi.org/10.2172/3011864) | SolarTRACE. ~900k projects, 22% of US residential solar, installer-supplied **timestamped milestones**: contract, permit submit/approve, utility ATB, install, inspections, final PTO request, PTO. Reports six named phases. **California is 45% of the data.** Results published at national and state level; per-AHJ results live in the public file and viewer. |
| NREL, *Solar permitting, inspection, and interconnection cycletimes and requirements*, public data file, `data.nrel.gov/submissions/160` (v. 2024-09-13, retrieved via Wayback) | **The threat.** Sheet `AHJ requirements`: 8,606 AHJ rows (CA = 535) × structural review, electrical review, 3rd-party review, number of inspections, rough-in inspection, over-the-counter, online, online-instant, median permit cost, SolSmart status. Sheet `AHJ Utility Timeline Data`: 12,713 AHJ×utility rows, 153 columns, four median phase durations by year/size/type. Sheet `Utility requirements`: 98 utilities × ATB required, submission method, response-time mandate, offset policy, capacity map. |
| O'Shaughnessy, Dong, Cook, Cruce, Ardani, Fekete & Margolis (2022), "Effects of local permitting and interconnection requirements on solar PV installation durations", *Energy Policy* 161:112734, [10.1016/j.enpol.2021.112734](https://doi.org/10.1016/j.enpol.2021.112734) | The paper that **summarises the AHJ-level requirement coding** above and regresses durations on it: *"We combine data on local PII requirements with estimates of process durations for **248,741** PV systems … requirements that would be expected to reduce durations — such as instant online approvals — are generally associated with shorter durations, while requirements that would be expected to increase durations — such as **structural reviews** — are associated with longer durations."* Full text paywalled; the exact operationalised variable list remains **unconfirmed**. |
| O'Shaughnessy, Barbose & Wiser (2020), "Patience is a virtue: rooftop solar PV permitting timelines in the US", *Energy Policy* 144:111615, [10.1016/j.enpol.2020.111615](https://doi.org/10.1016/j.enpol.2020.111615) | BuildZoom permit records; permit-submission→passed-inspection durations; documents within-AHJ installer-specific variation. Durations, not structure. |
| Burkhardt, Wiser, Darghouth, Dong & Huneycutt (2015), "Exploring the impact of permitting and local regulatory processes on residential solar prices in the US", *Energy Policy* 78:102–112, [10.1016/j.enpol.2014.12.020](https://doi.org/10.1016/j.enpol.2014.12.020) | Price regression on jurisdiction permitting **scores**. Cost, not process. |
| Dong & Wiser (2013), "The impact of city-level permitting processes on residential PV installation prices and development times", *Energy Policy* 63:531–542, [10.1016/j.enpol.2013.08.054](https://doi.org/10.1016/j.enpol.2013.08.054); LBNL-6140E [10.2172/1171742](https://doi.org/10.2172/1171742) | **44 California cities**, >3,000 installs, 2011; permitting scores 71–223 of 250, mean 138. Streamlining worth **$0.27–$0.77/W (4–12%)** and **~24 days (25%)**. A scorecard-driven regression — **but see §3(0): the underlying DOE instrument was a per-jurisdiction step enumeration, and this paper is where it got collapsed into a scalar.** |
| Ardani, Davidson, Margolis & Nobler (2015), *A State-Level Comparison of Processes and Timelines for Distributed PV Interconnection*, NREL/TP-7A40-63556, [10.2172/1227804](https://doi.org/10.2172/1227804) | Interconnection **process** comparison — but the unit is the **state**, not the jurisdiction. |

**Covers:** dollar costs, elapsed days per phase, a 9-attribute per-AHJ requirement census,
per-AHJ median durations, within-AHJ installer heterogeneity.
**Does not cover:** a full step *sequence* (SolarTRACE codes attributes, not an ordered process);
the **corrections/resubmittal loop** — explicitly absorbed, "Permits that require changes and
resubmission are counted from the original submittal date"; **reinspection** — absorbed into
"last passed inspection"; applicant-side vs agency-side effort split; any measurement model for
the requirement census's own missingness (national non-missing rates run 5%–64%; number of
inspections required is populated for only 8.8% nationally, 50.3% in CA); and any link to
§ 65850.5 compliance.

### Q2. SolarAPP+ and automated permitting — **PARTIALLY DONE; on its own, NOT a process census**

| Work | What it actually does |
|---|---|
| Nissen, Dalecki, O'Shaughnessy, Xu, Akar, Frey, Botin, Castelao & Tagani (2026), *SolarAPP+ Performance Review (2024 Data)*, NREL/TP-6A20-95050, OSTI [3016084](https://www.osti.gov/biblio/3016084) | Adoption + cycle-time comparison. End-2024: **799 AHJs expressed interest, 264 adopting (215) or piloting (49), 13 states; 225 adopting AHJs in California**; 37,393 permits. Same-day issuance vs 7-day median for traditional permits; 12 business days shorter to passed inspection; ~31,300 staff-hours saved. Per-AHJ figures shown for permit counts and for **29 AHJs** on submission→inspection. |
| Cook, Akar, Chang, Fensch, Nissen, O'Shaughnessy & Xu (2024), *SolarAPP+ Performance Review (2023 Data)*, NREL/TP-6A20-89618 | Prior year; source of the widely cited 14.5-day / 31% saving. |
| Williams, Cook, Cruce, Xu, Crew, Qasim & Miccioli (2022), *SolarAPP+ Pilot Analysis*, NREL/TP-6A20-81603, [10.2172/1839593](https://doi.org/10.2172/1839593) | Five-community pilot. |
| Symbium (commercial), `symbium.com` — SB 379 page and SolarAPP+ comparison | A Stanford-derived computational-law firm that **encodes per-jurisdiction permitting and planning rules** for instant permitting, explicitly "highly configurable for local jurisdiction requirements". A proprietary per-jurisdiction rule encoding exists. Not published, no jurisdictions named publicly. |

**The key structural point:** SolarAPP+ is a *single canonical standardised* code-compliance
process. It succeeds by **replacing** jurisdictional variation, not by cataloguing it. So its
existence does *not* imply a process census — and the reports contain no SB 379 or § 65850.5
compliance assessment at all. SolarAPP+ is therefore **not** the thing that scoops us.
SolarTRACE (same lab, adjacent project) is.

### Q3. Compliance with § 65850.5 / AB 2188 / SB 379 — **ALREADY DONE for the compliance question; the step census is not**

This is where our "documented vs enacted" framing takes the most damage. It has been done
three times, including by the state.

| Work | What it actually does |
|---|---|
| **Kaatz & Anders (2016)**, *AB 2188 Implementation Report: A Review of Ordinances Adopted by Local Jurisdictions in California*, Center for Sustainable Energy + Energy Policy Initiatives Center (USD Law), DOE Rooftop Solar Challenge. [Wayback PDF](https://web.archive.org/web/20170112034118/http://energycenter.org/sites/default/files/docs/nav/policy/research-and-reports/AB-2188-Implementation-Evaluation.pdf) | **The nearest documented-side prior work.** Frame = all **540** CA jurisdictions; **386** documented adopters; **374 ordinances coded** against ~13 statutory criteria: eligibility definitions, checklist authorisation *and* access, administrative/nondiscretionary review, HOA-approval prohibition, **written correction notice for incomplete application**, electronic submittal, e-signature, **single inspection and subsequent inspection for failure**, fire-department inspection, municipal utility director review / interconnection information, structural requirements, solar thermal, historic/landmark review. Already finds authorise-but-don't-do gaps (225 post documents online vs 21 authorise but do not post; 373 authorise solar-thermal streamlining but 58 provide documents). Reported in **aggregate groups, no row-level per-jurisdiction table**. Explicitly excludes experience: *"Assessment of individual application submission, timeframes, or contractor experiences are outside the scope of this document."* |
| **Taylor, Fujita, Zhang, Harb, Tamerius, Jones & Price (2019)**, *Explaining jurisdictional compliance with California's top-down streamlined solar permitting law (AB 2188)*, LBNL, [10.2172/1572850](https://doi.org/10.2172/1572850) · [eScholarship](https://escholarship.org/uc/item/7n5169cj) | **Binary** compliant/non-compliant for **all 540 CA AHJs**, coded from AHJ websites, Municode and phone/email follow-up; five policy-diffusion hypotheses tested by logit. Headline ~**71% compliance two years past the deadline**. A peer-reviewed-grade academic treatment of exactly the de jure compliance question. |
| **California Energy Commission**, *Residential Solar Permit Reporting Program – SB 379* + Program Status Dashboard, [program](https://www.energy.ca.gov/programs-and-topics/programs/residential-solar-permit-reporting-program-sb-379) · [Tableau](https://tableau.cnra.ca.gov/t/CNRA_CEC_PUBLIC/views/ResidentialSolarPermittingProgram/ResidentialSolarPermittingProgram) | **A live official per-jurisdiction census**, every CA city and county, data as of **2026-08-03**: SB 379 deadline tier, platform status (With/Without Platform/Exempt), annual-report status, CalAPP award and amount. Statutory annual reporting fields: permits issued, subset issued via a compliant automated platform, same for paired storage. **Self-reported and uncertified** — *"the CEC does not certify whether a jurisdiction's online, automated permitting platform complies with the requirements of SB 379. Enforcement lies outside of CEC jurisdiction."* |
| Plaisted / Flagstaff Research for CALSSA (2022), *Potential of SolarAPP+ Automated Permitting to Reduce Costs & Increase Solar Adoption in California* | Installer data on >30,000 CA 2021 installs, 300+ jurisdictions; has a "typical process steps" figure; but collapses California into a **binary "Typical vs Challenging jurisdiction"** typology. Not a census. |
| Solar Rights Alliance, Solar Access Act compliance campaign, `solarrights.org/streamlinedpermitting/` | Advocacy; aggregate only ("281 jurisdictions moved to comply … 78% of all jurisdictions currently in compliance or piloting"). Internal colour-coded list implied, not published. |

**Verified real negatives (not blocks):** CALSSA publishes **no** permitting scorecard or
best/worst list (full 815-URL sitemap enumerated; three items only on its reports page).
Vote Solar's 48-report sitemap contains **no** local permitting scorecard; *Freeing the Grid*
grades **states**. CivicWell (ex-Local Government Commission) site search returns nothing for
solar permitting. Environment California's report cards are on drinking water and college
clean energy, not solar permitting. GO-Biz/OPR's *California Solar Permitting Guidebook* is the
**normative** model ordinance and recommended checklist the statute points to — i.e. the
canonical step universe already exists as a state document — not an audit.

### Q4. Local regulatory variation and its measurement — **PARTIALLY DONE, but the step-structure REPRESENTATION is substantially anticipated; only the INFERENCE is open**

Per-jurisdiction discrete step/requirement structures for permitting already exist in four
independent lineages, one of them for exactly our case. Our representational claim is not novel.

| Work | What it actually does |
|---|---|
| **World Bank *Doing Business*, "Dealing with Construction Permits"** (2004–2020, discontinued Sept 2021), `archive.doingbusiness.org/en/methodology/dealing-with-construction-permits` | **The direct structural precedent.** Publishes a **numbered procedure list per city** with agency, time and cost per procedure, where a procedure is "any interaction … with external parties". The US is covered as **two** cities, NYC *and* **Los Angeles**; LA itemises ~17 procedures: plan check and permit (LADBS) → service advisory (LADWP) → plumbing → sewer → fire sprinkler → **seven separate inspections** → water connection → final fire and building inspections → **certificate of occupancy** (our PTO analogue). Daylight: n = 2 US cities not 500; a standardised hypothetical **warehouse**; expert questionnaires, so **de jure only**; deterministic consensus with no uncertainty; discontinued after the data-irregularities review. |
| **World Bank *Business Ready* / B-READY** (2024–), `worldbank.org/en/businessready/methodology` | **Institutionalises our claim #3 as a design principle:** Pillar I Regulatory Framework captures **de jure** via expert consultation, Pillars II–III capture **de facto** via Enterprise Surveys, explicitly to enable comparison. Topic 2 "Business Location" covers building permitting. Daylight: economy-level scores, firm surveys not applicant text, no step structure, no subnational unit. |
| Gyourko, Saiz & Summers (2008), *Urban Studies* 45(3), [10.1177/0042098007087341](https://doi.org/10.1177/0042098007087341); **Gyourko, Hartley & Krimmel (2021)**, *JUE* 124:103337, [10.1016/j.jue.2021.103337](https://doi.org/10.1016/j.jue.2021.103337) | **Worse for us than expected.** WRLURI2018's **Local Project Approval Index** and **Local Zoning Approval Index** are literally a per-jurisdiction check-all over **nine named approval entities** (planning commission, zoning board, council, county board, county zoning board, environmental review board, public health office, design review board, other), each coded **0 = need not approve / 1 = simple majority / 2 = supermajority**, plus a Local Assembly Index and an **Approval Delay Index in months** over four project scenarios; n = 2,472 communities. The 2021 paper even analyses **change in the number of required entities across two waves** (45% increased, 15% decreased). Daylight: a structure over **actors/veto points**, not process steps — no submit, plan review, resubmittal, inspection, reinspection, interconnection, PTO — and everything collapses to a sum then a PCA-weighted scalar; planner self-report; non-response is missing, not modelled. |
| Bronin et al. (2023), *How to Make a Zoning Atlas 2.0*, [10.2139/ssrn.4476927](https://doi.org/10.2139/ssrn.4476927); dataset [10.4079/zoning-atlas](https://doi.org/10.4079/zoning-atlas) | Thinner than feared, and a **useful foil**. Unit is the **zoning district** (33,295 jurisdictions / ~102,000 districts), not the jurisdiction; process is **one ordinal** per housing type — Allowed as of right / Public hearing required / Prohibited. The deciding body is deliberately erased and distinct instruments (CUP vs special exception) deliberately merged. Critically, **"not explicitly mentioned" is coded *Prohibited*** — the exact inverse of our silence-≠-absence rule, and the cleanest contrast available to us. |
| O'Neill, Gualco-Nelson & Biber, *Getting It Right* (2018) and "Developing Policy from the Ground Up", 25 *Hastings Env't L.J.* 1 (2019); "Perspectives or Misperceptions?", *JPER* 45(2):441–455, [10.1177/0739456x231216693](https://doi.org/10.1177/0739456x231216693) | **16 California cities** (not ~20), unit = the **project** (~25 fields, including multi-valued entitlement types); jurisdiction tables are counts of *observed project instances* across a fixed approval-type column set, not required/not-required flags. **They publicly declare our artifact missing and call for it:** "Los Angeles alone has over 90 discretionary entitlement actions", and "Requiring cities to report on the function of their local entitlements through a standardized reporting key can help auditors enforce existing state law." Their 2024 JPER paper finds planners **systematically underestimate** local regulatory stringency — the standing critique of both WRLURI and Terner self-report. |
| Terner Center, *California Residential Land Use Survey* (Mawhorter & Reid 2018) | **Good news.** Process content is thin: one "who typically grants approvals" categorical, binned approval times for four scenarios, Likert delay-cause items, and a three-stage plan→permit→occupancy funnel in frequency bins. **Not a step structure.** |
| Halling & Bækgaard (2023), *JPART*, [10.1093/jopart/muad023](https://doi.org/10.1093/jopart/muad023) | Systematic review: administrative burden is measured by surveys and experiments, **never** as latent jurisdiction-level rule presence. Our field-state citation. |

**Not threats (checked):** RegData (Al-Ubaydli & McLaughlin, [10.1111/rego.12107](https://doi.org/10.1111/rego.12107)) counts binding-constraint words in the CFR; Kalmenovitz's *Regulatory Fragmentation* counts federal agencies per issue; *Regulatory Intensity* uses PRA burden-hours; Ganong & Shoag count land-use court cases by state. All federal, all counts/scores, no local step structure.

**Covers:** ordered per-city procedure lists; per-jurisdiction check-all coding over named
approval entities; de jure/de facto comparison as an instrument design; per-jurisdiction
substantive rule coding; project-level entitlement-type coding.
**Does not cover:** a many-jurisdiction within-country step structure at ~15–20 step granularity
that is **inferred with uncertainty** rather than recorded as observed flags, with
silence-≠-absence handling. **That — the inference, not the representation — is what is left.**

### Q5. Installer/applicant-reported process evidence — **ALREADY DONE, and earlier than we assumed**

| Work | What it actually does |
|---|---|
| **Clean Power Finance, *National Solar Permitting Database*, `solarpermit.org` (DOE Assistance Agreement DE-EE0005349, c. 2013–2017; Vote Solar and ~12 installers listed as contributors; retrieved via [Wayback 2017-10-14](https://web.archive.org/web/20171014101323/https://solarpermit.org/))** | **The Q5 scoop, and it is severe.** A crowd-sourced per-jurisdiction solar permitting database with **jurisdiction pages for over 18,000 US cities and counties** and **over 100 data fields each**, "populated primarily by solar installers based on their experiences in the Authorities Having Jurisdiction where they do business", with thumbs-up/down peer verification. Fields explicitly include turnaround times, fees, design specifications, **inspection processes** and **common errors**. Also ran a "nationwide study of **273 installers**". Now defunct. |
| NREL SolarTRACE `AHJ requirements` / `AHJ permits reqs` (see Q1) | The living successor to NSPD: installer-reported per-AHJ requirements, 8,606 AHJs (535 in CA), publicly released and **still being updated** — a **v. 2025-09-09** file carries 19 requirement columns, adding Online Permitting for 2019/2022/2024/2025 and Online-Instant for 2022/2024/2025 naming SolarAPP+ / Symbium / Other, plus `Utility IX reqs` for 101 utilities (19 in CA). |
| Cruce et al. (2022), *Residential Solar Adoption Timelines and Impacts from the COVID-19 Pandemic*, NREL/TP-6A20-83529, [10.2172/1889272](https://doi.org/10.2172/1889272) | Includes a **survey of 171 AHJs** (question bank published in Appendix A) on permit submission channel, review/inspection timelines and process changes, plus follow-up interviews; and classifies 938 AHJs as online / online-instant / in-person-only. Direct elicitation of process from the agencies themselves. |
| Cook, Cruce, O'Shaughnessy, Ardani & Margolis (2021), "Exploring the link between project delays and cancelation rates in the U.S. rooftop solar industry", *Energy Policy* 156:112421, [10.1016/j.enpol.2021.112421](https://doi.org/10.1016/j.enpol.2021.112421) | Installer survey: permitting and interconnection challenges as primary drivers of delay and customer cancellation. Experienced burden, self-reported. |
| Plaisted / Flagstaff Research for CALSSA (2022) (see Q3) | Installer data on >30,000 California 2021 installs across 300+ jurisdictions; same-day vs 14-day median permit review under automated vs manual. |
| **Project Permit** (Vote Solar + IREC, DOE SunShot "Solar 3.0", c. 2013–2016), `projectpermit.org` | Scored municipal solar permitting **Best / Good / Worst / Incomplete** by matching best-practice fields to SolarPermit.org data; downloadable scorecard. Its nine crowdsourced items include **plan-check service type** (over the counter / outsourced / in-house not same-day), turnaround time, fee structure, inspection time window and **number of inspections required**. Domain resolves but serves nothing. |
| Meier & Taylor (2019), LBNL/DOE final technical report, [10.2172/1617035](https://doi.org/10.2172/1617035) | **Discrete choice experiments using individual PI&I reforms as attributes**, run on AHJs, utilities *and* installers, to find reform bundles fitting AHJ/utility preferences "as mediated through the preferences of PV installers". Attribute-level decomposition of the permitting process elicited from installers — but preference elicitation, not per-jurisdiction measurement. |
| Sinitskaya, Gomez, Bao, Yang & MacDonald (2019), "Designing linked journey maps to understand the complexities of the residential solar energy market", *Renewable Energy* 145:1910–1922, [10.1016/j.renene.2019.06.018](https://doi.org/10.1016/j.renene.2019.06.018); Bao et al. (2020), [10.1016/j.renene.2019.11.047](https://doi.org/10.1016/j.renene.2019.11.047) | **Journey maps** of the residential solar process across customer/installer/AHJ/utility, plus a CA+MA homeowner survey. A qualitative step diagram of residential solar already exists; what does not is per-jurisdiction measurement of which steps are present. |
| **BPI Challenge 2015 / CoSeLoG** — van Dongen, TU Eindhoven, [10.4121/uuid:31a308ef-c844-48da-948c-305d167a0ec1](https://doi.org/10.4121/uuid:31a308ef-c844-48da-948c-305d167a0ec1); **Buijs, van Dongen & van der Aalst (2013)**, "Mining Configurable Process Models from Collections of Event Logs", [10.1007/978-3-642-40176-3_5](https://doi.org/10.1007/978-3-642-40176-3_5); **Bolt, de Leoni & van der Aalst (2018)**, *Information Systems*, [10.1016/j.is.2017.12.006](https://doi.org/10.1016/j.is.2017.12.006) | **A threat we had not listed.** Four years of **building permit applications from five Dutch municipalities**, where "the processes in the five municipalities should be identical, but may differ slightly", posing verbatim: **"What are the differences in control flow between the municipalities?"** Buijs et al. output **one configurable process model plus per-municipality configurations** — a shared step universe with per-jurisdiction variation. Bolt et al. compare process variants on control flow *and* decision rules. |
| **Fauth & Soibelman (2022)**, *Buildings* 12:638, [10.3390/buildings12050638](https://doi.org/10.3390/buildings12050638); Fauth, Bloch & Soibelman (2023), [10.1108/ecam-06-2023-0593](https://doi.org/10.1108/ecam-06-2023-0593); Nisbet & Fauth (2026), [10.1080/09613218.2026.2613845](https://doi.org/10.1080/09613218.2026.2613845) | As-is **building permit process models**, Germany vs USA, by-right and non-by-right, from expert interviews; then a validated framework for cross-jurisdiction permit-process benchmarking, and a reference permit process model. This group reconstructs documented process structure and compares it across jurisdictions — **entirely from officials, never from applicants**. |

**Positioning warning.** The **de jure / de facto model** vocabulary is native to process mining —
van der Aalst, "Conformance Checking", [10.1007/978-3-662-49851-4_8](https://doi.org/10.1007/978-3-662-49851-4_8) —
so that phrasing will not read as our framing to a BPM referee. See also van der Aa, Leopold &
Reijers, "Comparing textual descriptions to process models"
([10.1016/j.is.2016.07.010](https://doi.org/10.1016/j.is.2016.07.010)) and "Checking process
compliance against natural language specifications"
([10.1016/j.is.2018.01.007](https://doi.org/10.1016/j.is.2018.01.007)) — but in both, neither
side is ever *experiential*.

**Verified negatives:** **EnergySage** Marketplace Intel Reports contain **zero permitting
content** (prices, quotes, equipment, financing, shopping behaviour only). **LBNL Tracking the
Sun** (3.7M systems) has **zero occurrences of "permit"** on its project page. **No
mystery-shopper or audit study of permit offices exists** — the nearest are single-touchpoint
municipal correspondence experiments (Porter & Rogowski 2018 *JPART*
[10.1093/jopart/muy025](https://doi.org/10.1093/jopart/muy025)).

**Covers:** installer-reported per-jurisdiction requirements at national scale (three times:
NSPD, Project Permit, SolarTRACE), AHJ self-report surveys, installer delay/cancellation
surveys, installer preference elicitation over process attributes, qualitative journey maps, and
per-municipality permit process models from agency event logs.
**Does not cover:** homeowner/forum narrative text as a source (no such study found); and
**nothing compares an experienced process reconstructed from applicant-generated text against a
documented official process.** The four nearest each fail one leg — B-READY (economy-level firm
surveys), O'Neill et al. 2024 (planner survey vs objective data, housing not permitting),
O'Shaughnessy et al. 2022 (documented requirements as *regressors* on experienced durations, not
two measurements of one structure), and Trautendorfer, Hohensinn & Hilgers 2024, *Regulation &
Governance*, [10.1111/rego.12615](https://doi.org/10.1111/rego.12615) (a de jure→de facto FOI
"compliance gap", but compliance *rates*, not process structure).
**Caveat:** NSPD and Project Permit are both dead and their item-level data is unrecoverable;
Dong & Wiser explicitly rejected NSPD as unusable ("None of these sources enabled the ready
creation of a comprehensive, comparable, current, geographically broad, quantitative permitting
'score'"). So the *artifacts* existed; *usable, modelled* versions do not.

### Q6. Occupancy / imperfect-detection models applied to institutions — **PARTIALLY DONE, and closer to done than we assumed**

The model class has already been transferred to social science twice, independently, and one of
the two cites MacKenzie. We must not claim a first transfer. Supporting statistic: of ~3,617
COCI-indexed citations of MacKenzie et al. (2002), only two are political science (Weidmann
2015; Eck 2015) — the ecology lineage genuinely did not cross over, but the social-science side
reinvented it.

| Work | What it actually does |
|---|---|
| **Cook, Blas, Carroll & Sinha (2017)**, "Two Wrongs Make a Right: Addressing Underreporting in Binary Data from Multiple Sources", *Political Analysis* 25(2), [10.1017/pan.2016.13](https://doi.org/10.1017/pan.2016.13) | Known to us. Latent **binary presence**, **false-negative-only** source error, per-source failure-to-report with covariates. Cites MacKenzie et al. 2006. Unit = country-month; **no item dimension**, no hierarchy, MLE not hierarchical Bayes. |
| **Feinstein (1990)**, "Detection Controlled Estimation", *Journal of Law and Economics* 33(1), [10.1086/467205](https://doi.org/10.1086/467205) (also *JPE* 1989, [10.1086/261595](https://doi.org/10.1086/261595)) | **The find.** Latent binary presence of a **regulatory violation** per plant-period, FN-only by construction, with an explicit **detection equation** on inspector covariates. Predates MacKenzie and is already in a regulatory-compliance setting. |
| **Caughey & Warshaw (2016)**, "The Dynamics of State Policy Liberalism", *AJPS* 60(4), [10.1111/ajps.12219](https://doi.org/10.1111/ajps.12219) | A literal **jurisdiction × binary-policy-item matrix** — our lattice — but items assumed observed without error, and the estimand is a continuous state-year scalar. Has the design, lacks the detection model. |
| **Gibilisco & Steinberg (2022)**, "Strategic Reporting: A Formal Model of Biases in Conflict Data", *APSR*, [10.1017/s0003055422001162](https://doi.org/10.1017/s0003055422001162) | **The sharpest threat.** Derives that underreporting bias in government disclosures is *positively correlated* with bias in NGO reports. Mechanism for exactly our worry: official jurisdiction pages and the statute both documenting the de jure process. |
| **Rainey & Jackson (2017/2018)**, "Unreliable Inferences About Unobserved Processes: A Critique of Partial Observability Models", *PSRM* 6(3), [10.1017/psrm.2017.3](https://doi.org/10.1017/psrm.2017.3) | Identification attack: when a covariate enters both the presence and the observability equation, estimates are highly sensitive to mild misspecification with large-sample bias. |
| Hui & Walter (1980) *Biometrics* [10.2307/2530508](https://doi.org/10.2307/2530508); Joseph, Gyorkos & Coupal (1995); Albert & Dodd (2004) [10.1111/j.0006-341X.2004.00187.x](https://doi.org/10.1111/j.0006-341X.2004.00187.x) | Latent binary presence with test-specific sensitivity/specificity. **Occupancy is this with specificity pinned at 1.** Albert & Dodd: estimates are not robust to misspecified conditional dependence between tests. |
| **Halling & Bækgaard (2023)**, "Administrative Burden in Citizen–State Interactions: A Systematic Literature Review", *JPART*, [10.1093/jopart/muad023](https://doi.org/10.1093/jopart/muad023) | Use as our field-state citation: administrative burden is measured by surveys and experiments, **never as latent jurisdiction-level rule presence**. |

**Weidmann's objection is NOT answered — it has been strengthened.** No model-based fix exists.
Gibilisco & Steinberg (2022) derive the shared-bias correlation formally; Parkinson (2023, *APSR*,
[10.1017/s0003055423001181](https://doi.org/10.1017/s0003055423001181)) finds biases
"not directionally predictable"; Dawkins (2020, *JPR*) concludes point estimates may be
impossible in the worst cases; Broache & Cronin-Furman (2025, *JoGSS*) show shared statist bias
empirically. The only workarounds in use are **external anchoring/validation** (Bagozzi et al.
2018 *PSRM* [10.1017/psrm.2018.11](https://doi.org/10.1017/psrm.2018.11); Cook & Fortunato 2022
*APSR* [10.1017/s0003055422000624](https://doi.org/10.1017/s0003055422000624)) and **declared
sensitivity analysis**. Real negatives: multiple-systems estimation is uniformly
population-size-valued (Lum/Price/Banks 2013; Manrique-Vallier 2016; Bird & King 2018) and nobody
frames it as latent practice presence; the National Zoning Atlas and the Wharton index treat
absence as absence.

---

## 3. The nearest prior work

There is no single nearest item, because the claim decomposes and each part has a different
closest competitor in a different referee pool; the combination is what closes the gap.
**Item (0) is the single closest overall**, and the one we would most have regretted missing.

**(0) The DOE SunShot Rooftop Solar Challenge permitting questionnaire (2011)** — the instrument
behind Dong & Wiser (2013), *Energy Policy* 63:531–542 / LBNL-6140E
[10.2172/1171742](https://doi.org/10.2172/1171742), reproduced verbatim as its **Appendix A**,
and extended nationally by Burkhardt et al. (2015).
**This is our representational claim, for our exact case, in 2011.** DOE surveyed **>290
participating US jurisdictions** with a 21-question instrument across seven categories
(application, information access, process time, fees, best-practice processes, inspection, utility
communication). Its items are a **fixed universe of ~19 discrete named process elements recorded
as presence/absence per jurisdiction, for residential rooftop solar**:
- **Q2** "What types of departmental approvals are required for a typical installation? (check
  all that apply)" — Building, Electrical, Fire, Mechanical, Planning, Plumbing, Structural,
  Zoning, Other
- **Q3** PE reviews required — Civil, Electrical, Environmental, Fire Protection, Mechanical,
  Structural
- **Q20** "How many separate inspection trips are required for a typical installation? (check all
  that apply)" — Single Comprehensive Inspection, **Electrical Rough-in**, **Electrical Final**,
  **Roof Penetrations (pre-install)**, Structural/Building Final, Other
- plus submission channels, a ≤3-day issuance policy flag, fee structure, and Solar ABCs
  expedited-permit-template adoption.

**Daylight left:** the item-level responses were **never released** — "the specific scoring and
weighting methodology is not publicly available" — and everything was collapsed into a single
weighted 0–250 scalar used only as a regressor. Participating jurisdictions **self-selected**.
It is **jurisdiction self-report only**, so documented process with no experienced counterpart.
One wave, 2011, now 15 years stale. No uncertainty, no detection model.
**Consequence for us: our representational claim was substantially anticipated in 2011–13 for
this exact statute's subject matter and then thrown away as a scalar.** We must say so in the
introduction ourselves. What remains open is recovering it as an *inferred* structure with
uncertainty across ~500 California jurisdictions and comparing it against experienced process.

**(a) Measurement — NREL SolarTRACE, `data.nrel.gov/submissions/160` + Cruce et al. 2025 +
O'Shaughnessy et al. 2022.** This is the closest item overall. It already publishes, for
**535 of ~540 California jurisdictions**, a per-jurisdiction coding of structural review,
electrical review, third-party review, number of inspections required, rough-in inspection
required, over-the-counter availability, online/online-instant permitting and median permit
cost; and for **432 of those same California AHJs** it publishes observed median durations for
the AHJ permit, pre-install interconnection, inspection and final-interconnection→PTO phases.
California non-missing rates are high (structural review 97.9%, rough-in 97.0%, electrical
93.5%, online 92.5%, number of inspections 50.3%, third-party 20.9%).
**Daylight left:** (i) attributes, not an ordered step structure; (ii) the **rework loop is
deliberately erased** — resubmittals are counted from the original submittal date and
reinspections collapse into "last passed inspection", so corrections/resubmittal and
reinspection are genuinely unmeasured; (iii) **no measurement model** — NREL's own front matter
says "errors may exist and it may not be comprehensive. Errors in the sources (e.g. AHJ
permitting requirements lists from data partners) may be duplicated", and invites email
corrections; missingness is coded NA and left there; (iv) provenance is **installers only**
(plus a 171-AHJ COVID-era survey), so there is no de jure source and hence no divergence
measure; (v) AHJ timelines are duplicated across every AHJ×utility row, a pseudo-replication
NREL flags but does not model. That is a real strip of daylight, but it is a *refinement of an
existing federal dataset*, not a new measurement.

**(a-bis) Historical precedent — National Solar Permitting Database (2013).** Strictly the
closest *conceptual* match to our proposed artifact — 18,000 jurisdictions × 100+ installer-
reported process fields with peer verification — but defunct and unretrievable, so it functions
as a priority claim and a cautionary tale (a crowdsourced census with no measurement model
decayed and died) rather than as a competing dataset.

**(b) De jure side — Kaatz & Anders (2016).** Already enumerates, per jurisdiction, the
statutory process elements including the two we thought were ours (written correction notice;
single inspection plus subsequent inspection for failure), across a 540-jurisdiction frame, and
already reports authorise-but-don't-do divergence. **Daylight:** aggregate-only reporting,
2016, pre-SB 379, 10 kW scope, no statistical model, one source genre (ordinances).

**(b-bis) Representation — CoSeLoG / BPI Challenge 2015.** The only prior work that outputs a
**per-jurisdiction permitting step structure over a shared step universe** and explicitly
compares control flow across jurisdictions for the same nominal process (five Dutch
municipalities' building permit applications). **Daylight:** (i) its evidence is the agency's own
case-management event log — nobody reconstructs a permitting process from **applicant-generated
text**; (ii) it compares municipalities *to each other*, never to the documented process;
(iii) event logs are treated as complete and correct, so there is no analogue of our detection
layer. Weakest leg: applicant burden as the estimand is *not* strong novelty, since Fauth covers
official structure and NREL covers durations.

**(c) Method — Cook et al. (2017) and Feinstein (1990).** Both are the same model class. A
political-methods referee will say "this is my estimator with documents instead of newswires";
a law-and-economics referee will say "this is detection-controlled estimation with documents as
detectors". Both will be substantially right. Our incremental margin is the jurisdiction × step
**lattice** with a latent binary per cell, partial pooling across both margins, a **durable
structural** latent (no colonisation/extinction) rather than a dated event, and detection
indexed by **document genre**. Narrow, and defensible only if stated as a refinement.

---

## 4. Threats to the claim — things that would have embarrassed us

1. **SolarTRACE's public `AHJ requirements` sheet.** The single worst one. Had we published a
   "first per-jurisdiction census of California solar permitting process steps", a reviewer
   would have pointed at a released federal spreadsheet covering 535 of ~540 CA jurisdictions
   with 9 process attributes and 4 observed phase durations. Non-negotiable citation.
2. **The CEC SB 379 dashboard.** A live state per-jurisdiction compliance census, updated
   2026-08-03. Publishing a "documented vs enacted" compliance finding without it would be
   indefensible.
3. **Kaatz & Anders (2016) and Taylor et al. (2019).** The de jure compliance census exists
   twice, once academically, covering all 540 jurisdictions.
4. **The model-ordinance collinearity.** **365 of 386** adopting jurisdictions used, modified or
   took language from one model ordinance, and the state Guidebook supplies the canonical
   checklist. Our official-document sources are therefore near-duplicates. Conditional
   independence of detectors given z fails, ψ and p are weakly identified, and Gibilisco &
   Steinberg (2022) supplies a formal mechanism for why the bias is *shared* rather than
   averaging out. This is the same failure mode our CalFresh corpus hit with shared state forms
   across Modoc/Nevada/Sierra — it is structural to this project, not incidental.
5. **Feinstein (1990) / Cook et al. (2017).** Method priority, from two directions.
6. **Rainey & Jackson (2017)** and **Albert & Dodd (2004).** If jurisdiction covariates enter
   both z[j,s] and p[source], we are in the documented non-robust regime.
7. **Symbium.** A Stanford-lineage firm has already computationally encoded per-jurisdiction
   California permitting rules commercially. Not published, so not a literature scoop, but a
   referee or a seminar audience will ask why we did not simply use it.
8. **SolSmart is not a census** — 37 of 535 CA AHJs designated, 505 of 8,606 nationally,
   voluntary and self-selected. Worth stating explicitly so we are not accused of ignoring it,
   and worth *not* overclaiming as a competitor.
9. **The National Solar Permitting Database (SolarPermit.org, 2013).** An 18,000-jurisdiction,
   100+-field, installer-populated permitting census with a peer-verification layer, DOE-funded.
   Any claim that installer-reported per-jurisdiction process evidence is novel dies here.
   Note also that its "common errors" field anticipates the corrections/resubmittal content we
   identified as our clearest remaining gap — so frame that gap as *modelling*, not discovery.
10. **World Bank *Doing Business*, "Dealing with Construction Permits".** Enumerated permitting
   as an ordered numbered list of procedures per city, with days and cost per procedure, for
   ~190 economies — **including Los Angeles at ~17 procedures**, plan check through certificate
   of occupancy. A reviewer will cite it as the precedent for representing permitting as a step
   sequence; distinguish on census vs standardised hypothetical case and on uncertainty — do not
   claim priority for the representation.
11. **The DOE SunShot Rooftop Solar Challenge questionnaire (2011).** The worst single omission
   risk in this whole review: a >290-jurisdiction, ~19-element presence/absence process
   enumeration for residential rooftop solar, published as Appendix A of LBNL-6140E. See §3(0).
12. **WRLURI's Local Project / Local Zoning Approval Indices.** A per-jurisdiction check-all over
   **nine named approval entities** at 0/1/2 across ~2,450 communities, with the 2021 wave
   analysing change in the *count* of required entities. Our "nobody records approval structure
   per jurisdiction" line would not have survived contact with this.
13. **CoSeLoG / BPI Challenge 2015** (five Dutch municipalities' building permits; one
   configurable model plus per-municipality configurations) and **van der Aalst's conformance
   checking**, where **"de jure model" vs "de facto model" is standing vocabulary**. Our framing
   sentence is, verbatim, a process-mining term of art. Also **Fauth & Soibelman (2022)**, who
   build as-is cross-country permit process models from officials.
14. **World Bank B-READY (2024–)**, which makes de jure (expert) vs de facto (survey)
   comparison an explicit pillar design, with building permitting in scope. Our claim #3 is a
   subnational, text-based instance of a principle a flagship instrument already institutionalised.
15. **National Zoning Atlas codes "not explicitly mentioned" as *Prohibited*.** Useful to us as
   a foil — but only if we cite it; otherwise it looks as though we did not know the closest
   large-scale coding effort took the opposite convention.

---

## 5. What would make this publishable

Given the above, the following framings survive, in descending order of strength.

1. **The rework loop as the measured object.** NREL erases it by construction (resubmittals
   counted from original submittal; reinspection collapsed into last passed inspection) and
   Kaatz & Anders only records whether a correction notice is *authorised*. A per-jurisdiction
   posterior over **correction/resubmittal and reinspection incidence**, with applicant-side
   effort, is genuinely unmeasured and is the burden component our project already cares about.
   Caveat: NSPD carried a "common errors" field, so this is unmeasured, not unnoticed.
2. **Joining the two existing halves.** The de jure census (ordinances/checklists, Kaatz &
   Anders) and the de facto census (installer-reported requirements + observed durations,
   SolarTRACE) exist separately at the same 540-jurisdiction unit and have **never been
   joined**. A jurisdiction-level divergence measure is a real contribution, but it is a
   data-linkage contribution and must be framed as such, not as new measurement.
3. **A measurement model for an existing federal census's missingness, externally anchored.**
   NREL's own requirement table is 5%–64% non-missing nationally, coded NA with no model, and
   NREL explicitly solicits corrections. Fitting detection to that table and **validating
   against SolarTRACE's observed durations and the CEC's self-reports as external anchors** is
   exactly the Bagozzi/Cook-&-Fortunato template that the reporting-bias literature accepts as
   the only defensible route past Weidmann. This turns our weakness into the design.
4. **The self-report pathology in the state's own compliance data.** SB 379 reporting is
   triggered only "within one year of implementing", is self-reported, is uncertified by the
   CEC, is unenforced except by private claim, and jurisdictions reporting "0" online permits
   are simply classified "Without Platform". Absence from the dashboard is not non-compliance.
   That is a policy-relevant latent-presence problem with a named statutory decision riding on
   it — the strongest *policy* framing available.

**Framings that do NOT survive:** "first per-jurisdiction process census"; "first
documented-vs-enacted audit of § 65850.5"; "first transfer of occupancy models to
institutions"; "first use of installer-reported evidence to characterise permitting as
experienced"; "first representation of a permitting process as a step structure per
jurisdiction"; "de jure vs de facto process" as though it were our coinage; and any claim
resting on official jurisdiction webpages as independent detectors.

**The one-paragraph version for an introduction, if we proceed.** Do not claim the
*representation*. Per-jurisdiction discrete permitting-step structures already exist in Doing
Business (numbered procedures per city, LA included), in CoSeLoG's configurable models over five
Dutch municipalities, in WRLURI's nine-entity 0/1/2 approval coding across ~2,450 US communities,
in NREL SolarTRACE's public 8,606-AHJ requirements table, and — most damagingly — in the 2011 DOE
Rooftop Solar Challenge questionnaire, which recorded a fixed universe of 8 departmental
approvals + 6 PE reviews + 5 inspection-trip types per jurisdiction for residential rooftop solar
and then collapsed it into an unpublished 0–250 scalar. Claim instead the **inference**: step
presence as a latent per-jurisdiction quantity estimated jointly from documentation and
applicant-generated text under an explicit observation model in which a missing mention is not an
absent step — against a literature that codes NA and leaves it (NREL), assigns zero (NREL's ATB
rule), or codes "not explicitly mentioned" as *Prohibited* (National Zoning Atlas). And claim the
**comparison of documented against experienced as two noisy views of one structure**, which
nobody does — while conceding that B-READY institutionalises the de jure/de facto split at
economy level and that "de jure vs de facto model" is standing process-mining vocabulary, so the
novelty is the applicant-text observation model, not the phrase.

**Recommendation.** Do not make solar the flagship transfer. If the method needs a second
empirical case, solar is usable only as framing (3)+(4) — a measurement-model contribution on
top of an existing federal census, with the applicant/installer narrative corpus as the
oppositely-biased detector class that supplies identification. If the goal is a novelty win,
neither CalFresh nor solar is it, and the binding constraint is the same in both: a domain with
a funded incumbent measurement programme leaves us refining, not measuring.

---

## 6. Blocked and limitations

Every item here is a **blocked query, not a negative finding**.

- **OpenAlex: fully exhausted before this run and never returned a single row.** HTTP 429 on
  every attempt, both `?mailto=` and header forms: *"Insufficient budget … free daily budget
  shared by everyone on your network's IP address … resets at midnight UTC"*, retryAfter
  ~13,200 s. No conclusion in this report rests on OpenAlex. Citation-graph traversal via
  OpenAlex `referenced_works` / `cited_by_api_url` was therefore **not possible**; partially
  substituted with OpenCitations COCI and reference lists extracted from PDFs.
- **All `nrel.gov` hosts DNS-unresolvable** from this environment (`www.nrel.gov`, `docs.nrel.gov`,
  `data.nrel.gov`, `solarapp.nrel.gov`, `solartrace.nrel.gov`) via both curl and WebFetch.
  Worked around via OSTI full-text mirrors and Wayback. **Consequence: the interactive
  SolarTRACE viewer and the official SolarAPP+ adoption tracker (`/adoption_at_a_glance`) were
  never seen directly** — our characterisation of per-AHJ publication rests on the public data
  file and the NREL data-catalogue description.
- **O'Shaughnessy et al. (2022), *Energy Policy*** — full text and abstract unobtainable.
  Elsevier redirect to `linkinghub.elsevier.com`; no abstract in Crossref, OSTI ("Not
  Available") or OpenAIRE; DOE PAGES 404. Characterised indirectly from NREL's own statement
  that it summarises the SolarTRACE AHJ requirement data. **Flagged as unverified.**
- **Burkhardt et al. (2015)** abstract/full text not retrieved (OSTI purl 404; no Crossref
  abstract). Characterised from citing descriptions only.
- **`emp.lbl.gov` blocked by Cloudflare (403)**; **`eScholarship` 403 via curl (CloudFront)**.
  Taylor et al. 2019 recovered via OSTI metadata + subagent WebFetch.
- **`solsmart.org` 403**; not archived at the designation-criteria path in Wayback. SolSmart
  characterised from NREL's variable documentation and counts.
- **`solarapp.org` / `www.solarapp.org` connection timeout**; **`gosolarapp.org` 403**.
- **`web.archive.org` unavailable through WebFetch** ("Claude Code is unable to fetch from
  web.archive.org"); curl to Wayback did work and carried the NREL and CSE retrievals.
  Wayback **CDX** returned "Internet Archive services are temporarily offline" on two queries.
- **`environmentcalifornia.org` / `environmentamerica.org` — Cloudflare 403 on every path**,
  curl and WebFetch. Never reached directly; the "no solar permitting report card" finding
  rests on a Wayback CDX enumeration, so treat it as strong but not airtight.
- **California State Auditor not successfully searched** — `auditor.ca.gov/reports/recent` 404;
  `information.auditor.ca.gov/reports?search=...` returned only the server-side form.
  **Little Hoover Commission** `lhc.ca.gov/reports/` 403.
- **CEC Tableau row-level export partial** — the `.csv` endpoint returns the aggregate summary
  sheet only; the full jurisdiction × status table needs the interactive viz. Per-jurisdiction
  aggregates quoted above (345 CalAPP awards; $4.07M paid of $18.92M awarded; 66,011 online PV
  and 59,836 online PV+storage permits) come from the dashboard page, not a clean export.
- **GO-Biz / OPR California Solar Permitting Guidebook PDF not retrieved** — original OPR URLs
  redirect-loop to `lci.ca.gov`; the CSE-hosted copy 404s. Characterised from Kaatz & Anders.
- **CSE self-report compliance survey** (`energycenter.org/permitting/guidebook/implementation/survey`)
  timed out and was never read.
- **Semantic Scholar** — not used; reported as 429/zero-rows before this run.
- **WebSearch** — not used, per instruction.
- **National Solar Permitting Database data itself is unreachable** — `solarpermit.org` has no
  DNS A record, last Wayback capture 2017-10-14, archived browse pages return 500, and
  jurisdiction detail pages required an account. The 100+ field schema is known only from the
  archived About page. **Project Permit** (`projectpermit.org`) resolves but serves nothing.
- **WRLURI item-level release unconfirmed.** `real-faculty.wharton.upenn.edu/gyourko/land-use-survey/`
  301→404; the public `.dta` files sit behind Dropbox links that served an HTML interstitial and
  then 403'd. Whether the per-entity q4 responses ship in the public release is **inferred from
  the paper's variable names**, not verified from the file.
- **`californialanduse.org` domain resold** (301s to a wallpaper site) — the O'Neill/Terner
  California Land Use portal cited in NBER w26573 is dead.
- **`papers.ssrn.com` 403** to curl and WebFetch (two Zoning Atlas papers recovered via Wayback;
  SSRN 5335143 has no capture, Crossref abstract only). **`journals.sagepub.com` 403 + Cloudflare
  with no Wayback snapshot** — the O'Neill et al. 2024 *JPER* unit of analysis and variable list
  are **unverified**. **`zoningatlas.org/methodology` has no capture** and no public column-level
  data dictionary exists; current NZA methodology has moved to a non-public internal wiki.
- **Subnational *Doing Business* US coverage unverified** (`subnational.doingbusiness.org` 302→404)
  and **B-READY US inclusion unverified** (`worldbank.org/en/businessready/economies` 404).
- **`law.berkeley.edu` and `clee.berkeley.edu` PDFs all 404 live** — the O'Neill/Biber entitlement
  work reached only via Wayback; one Wayback CDX query 504'd domain-wide.
- **`sciencedirect.com` 403 throughout, and Crossref carries no abstracts for Elsevier *Energy
  Policy* or *Information Systems***, so several items are characterised indirectly (flagged
  inline). **Open lead we could not close: Hsu (2018), *Energy Policy*,
  [10.1016/j.enpol.2018.03.008](https://doi.org/10.1016/j.enpol.2018.03.008), "Predictors for
  adoption of local solar approval processes and impact on residential solar installations in
  California cities" — abstract not retrieved, measurement unverified. This is in our exact
  empirical setting and should be chased before drafting.**
- **`www.seia.org` 403** — SEIA / Wood Mackenzie *Solar Market Insight* not checked.
- **Not searched at all:** SolarReviews; r/solar and r/solarDIY text mining (no academic study
  found via Crossref/arXiv, but no dedicated forum-corpus search was run); Bozeman red-tape
  measurement; Mast/Molloy/Shoag beyond Ganong & Shoag.
- **Tool gotchas worth recording:** arXiv over `http://` returns a 301 with an empty body — must
  use `https://`. OSTI's API accepts only `q=`, returns XML unless sent
  `Accept: application/json`, and ranks by date not relevance; `report_number=` silently returns
  unrelated rows. Crossref does not index 4TU/BPIC datasets — DataCite does.
- **arXiv: verified working, and its negatives are real.** Controls returned 141 rows
  ("occupancy model") and 17 ("site occupancy" AND detection); probes returned **0** for
  `"solar permitting"`, `"occupancy model" AND "administrative"`, and
  `"administrative burden" AND "latent"`, and 1 unrelated row for
  `"rooftop solar" AND "permitting"`. These are genuine absences.
- **Crossref: verified working** (real rows, high yield on named-author queries). But
  `query.bibliographic` is fuzzy and floods conceptual queries with irrelevant historical
  matches; conceptual negatives from Crossref should be treated as weak.
- **OpenCitations COCI** returned malformed/truncated JSON for MacKenzie et al. 2002 (recovered
  by regex over a 1.03 MB partial payload; 3,617 citing DOIs is a **lower bound**) and was not
  recovered for MacKenzie et al. 2003. **COCI coverage lags ~2024**, so 2025–26 forward
  citations are under-sampled: a 2025–26 paper doing exactly our transfer could exist and be
  invisible to every tool available in this run. **This is the main residual risk.**
