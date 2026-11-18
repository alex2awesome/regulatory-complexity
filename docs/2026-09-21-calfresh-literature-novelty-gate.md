# CalFresh process-structure contribution: literature novelty gate

Date: 2026-09-21. Adversarial review — the brief was to find evidence the
contribution is already taken. Method, failed queries and unreachable sources
are in §6; **read §6 before treating any gap below as a finding.**

## 1. Bottom line

**PARTIALLY NOVEL, and considerably less novel than the project's framing
assumes. Three of the four planks are taken; one narrow plank survives.**

- **The substantive headline is scooped.** That CalFresh's enacted process turns
  on the intake interview, and that this produces procedural rather than
  eligibility denials, is established in California with a randomised experiment:
  Giannella, Homonoff, Rino & Somerville (*AEJ: Economic Policy* 2024) identify
  the intake interview as *the* barrier using 65,000 Los Angeles County
  applicants. Their Figure 1 already publishes a step-level denial decomposition
  (missed interview = 33.7% of all applications). Code for America has published
  the documented-versus-enacted version of the same finding in plain terms:
  1 in 3 LA CalFresh applications denied for a missed interview against 6%
  denied for ineligibility, **19% of surveyed applicants received their
  interview date and time only after the date had passed**, and 45% tried to
  reschedule and could not.
- **Per-county procedural measurement is largely taken too, and this is the
  find that most changes the picture.** Heflin, Fannin & Lopoo (*American Review
  of Public Administration* 2023) telephoned all 626 SNAP local information
  lines across the ten county-administered states — **California included** —
  calling each up to three times on separate days, succeeding 88% of the time,
  and "were able to document conditions for submitting a new application for
  SNAP in **647 counties**." That is primary, per-county, enacted procedural
  data on a repeat-contact design, in a public administration journal, with 20
  citations. Any claim of the form "nobody has measured SNAP procedure per
  county" is false.
- **The methods transfer is unclaimed under its name but not in substance.**
  MacKenzie et al. 2002 has 4,499 citations with essentially zero
  public-administration, law or organisational uptake, so "occupancy model for
  administrative process" is an unused phrase. But Cook, Blas, Carroll & Sinha
  (*Political Analysis* 2017) already publish latent binary presence with
  per-source, covariate-dependent failure-to-report probabilities — an occupancy
  model minus the name and the random effect — and Weidmann (*AJPS* 2015) cites
  MacKenzie and **explicitly declines** the transfer because it fails when all
  sources share a bias. That objection is waiting for us in print.
- **What survives.** The defensible residual claim is narrow and specific:
  **a fixed universe of ~20 procedural actions, scored per county against
  *published county instructions* and *claimant accounts* as two distinct
  evidence genres with different disclosure probabilities, so that documentary
  silence is an observation rather than a missing value — and with the resulting
  divergence reported per county and per step.** Each clause is doing work.
  Heflin et al. measured one procedural condition by asking the county on the
  phone and treating the answer as true; we would score twenty actions against
  what counties *publish* and what applicants *report*, and model the
  disclosure process. Giannella et al. and Code for America have the enacted
  side for one county from administrative data; nobody has the *documentation*
  side at all. Code for America's Safety Net Benefits Field Guide is the closest
  existing scan of documented application requirements, and it is state-level and
  about interface features, not procedural actions.

Two cautions that are not about the literature. First, the project's own morning
audit records that the fitted model loses to a pooled Beta baseline (0.072 vs
0.061), that county contrasts are confounded with source genre (Alameda is three
Reddit posts, Los Angeles a staff manual), and that the forum-only model read
silence as absence. "Per-county process structure" is therefore not yet an earned
empirical result regardless of what the literature says. Second, the strongest
number actually in hand — the procedural share of CalFresh denials — is an
administrative descriptive statistic that needs no occupancy model, and its
county-level analogue has already been published for LA by others.

## 2. The six questions

### Q1. Administrative burden operationalised as per-jurisdiction discrete process structure

**Verdict: PARTIALLY DONE — operationalised as survey scales, cost categories,
form-level coding, single-program sludge audits, and (in one case) a per-county
procedural fact; not as a multi-action per-jurisdiction step structure.**

- **Herd & Moynihan**, *Administrative Burden: Policymaking by Other Means*,
  Russell Sage 2018. DOI [10.7758/9781610448789](https://doi.org/10.7758/9781610448789).
  ~519 Crossref citations. The learning/compliance/psychological-cost taxonomy.
  The costs are categories of *experience*, never a step inventory attached to a
  named jurisdiction.
- **Halling & Bækgaard**, "Administrative Burden in Citizen–State Interactions:
  A Systematic Literature Review", *JPART* 2023. DOI
  [10.1093/jopart/muad023](https://doi.org/10.1093/jopart/muad023). 164
  citations. Reviews 119 articles and working papers. Decisive for this
  question: the measured objects are *experiences* of burden and *causal
  effects* of state actions on them. Their forward agenda explicitly calls for
  work connecting burden tolerance to "**actual state actions**" — measurement
  of what agencies actually do is named as underdeveloped.
- **Daigneault, Journeault, Lauzon-Rhéaume & Birch**, "Measuring Administrative
  Burden: Bringing the State 'Back in' as a Reflexive Actor in Burden
  Reduction", *Public Administration* 2025. DOI
  [10.1111/padm.70036](https://doi.org/10.1111/padm.70036). Scoping review of 38
  academic and grey sources plus 11 expert interviews; identifies **six**
  measurement approaches in government use and finds all six partial — "none
  encompasses all four dimensions (time, money, effort, psychological) and none
  integrates both subjective and objective data". Best single citation for the
  claim that a structural per-jurisdiction operationalisation is missing, and
  also the item most likely to pre-empt it. **Full text could not be retrieved
  (§6); read the six approaches before asserting the gap in print.**
- **Jilke, Bækgaard, Herd & Moynihan**, "Short and sweet: Measuring experiences
  of administrative burden", *Journal of Behavioral Public Administration* 2024.
  DOI [10.30636/jbpa.71.340](https://doi.org/10.30636/jbpa.71.340). The state of
  the art in burden *measurement* is a one-item and three-item **survey scale**.
- **Heflin, Fannin & Lopoo**, "Local Control, Discretion, and Administrative
  Burden: SNAP Interview Waivers and Caseloads During the COVID-19 Pandemic",
  *American Review of Public Administration* 2023. DOI
  [10.1177/02750740231186423](https://doi.org/10.1177/02750740231186423).
  20 citations. Open access on PMC
  ([PMC10352665](https://pmc.ncbi.nlm.nih.gov/articles/PMC10352665/)).
  **The counter-example to this question's gap.** Burden operationalised as a
  discrete per-county procedural fact, collected primarily. Detail in Q3.
- **Brown, Carey & Malbon**, "What is in a form? Examining the complexity of
  application forms and administrative burden", *Australian Journal of Public
  Administration* 2021. DOI
  [10.1111/1467-8500.12531](https://doi.org/10.1111/1467-8500.12531). 21
  citations. The closest existing "decompose burden into discrete units" move: a
  framework for question complexity on one NDIS form. One form, one
  jurisdiction, no latent structure — but it stakes the "smallest unit of
  administration" framing.
- **Lades, Lentz & Augustenborg**, "Administrative burdens as barriers to
  afforestation: a sludge audit of Ireland's afforestation scheme", *Journal of
  Rural Studies* 2026. DOI
  [10.1016/j.jrurstud.2026.104078](https://doi.org/10.1016/j.jrurstud.2026.104078).
  A sludge audit *is* a step-by-step enumeration of an administrative process,
  so the genre exists; single-scheme diagnostic walkthrough, no statistical model
  over jurisdictions.
- **De Jong, Graefe, Irving & St. Pierre**, "Measuring State TANF Policy
  Variations and Change After Reform", *Social Science Quarterly* 2006. DOI
  [10.1111/j.1540-6237.2006.00432.x](https://doi.org/10.1111/j.1540-6237.2006.00432.x)
  (38 citations), with "The Whole is the Sum of its Parts: Theory, Technique,
  and Measurement Science Applied to TANF Rules", DOI
  [10.1111/j.1540-6237.2006.00437.x](https://doi.org/10.1111/j.1540-6237.2006.00437.x).
  The real precedent for **latent-variable measurement of jurisdiction-level
  welfare rules**: hand-coded state TANF rules tested for common underlying
  dimensions. De jure only, adopted *policy options* rather than procedural
  steps, no observation model — but a reviewer who knows this literature will
  ask why we are not a descendant of it.

**Covered:** burden as experienced cost (surveys); as monetised time and money
(Standard Cost Model lineage, PRA burden hours); as form-level question
complexity; as a single-program sludge walkthrough; as one per-county procedural
condition (Heflin et al.); jurisdiction rule codings reduced to latent policy
dimensions.
**Not covered:** a *multi-action* fixed step ontology applied across all
jurisdictions of one program; treating documentary silence as an observation
rather than a missing value; uncertainty quantification over which steps a given
jurisdiction's process contains.

### Q2. Documented vs. enacted / de jure vs. de facto, at the level of discrete procedural steps

**Verdict: PARTIALLY DONE — the phenomenon is the founding claim of an entire
literature and is thoroughly established; it has been measured for *one* step in
*one* CalFresh county already; the multi-step, multi-county measurement is not
done.**

- **Brodkin & Majmundar**, "Administrative Exclusion: Organizations and the
  Hidden Costs of Welfare Claiming", *JPART* 2010. DOI
  [10.1093/jopart/mup046](https://doi.org/10.1093/jopart/mup046). 275 citations.
  The canonical statement of our thesis in prose: organisations are "informal
  gatekeepers, developing modes of operation", and "operational practices — both
  prescribed and informally created" add hidden costs. The prescribed/created
  gap is named, never measured per jurisdiction or per step. **Our framing must
  be built on this.**
- **Code for America**, "Think Big, Start Small: How Implementing Flexible
  Interviews Improves Benefit Delivery",
  <https://codeforamerica.org/news/think-big-start-small-how-implementing-flexible-interviews-improves-benefit-delivery/>.
  **The closest published documented-versus-enacted comparison, and it is for
  our flagship step.** Los Angeles County: 1 in 3 CalFresh applications denied
  for a missed interview against only 6% for ineligibility; ~40% among students
  and working families; 34% among applicants experiencing homelessness. The
  enacted-vs-documented evidence proper: **19% of respondents received
  information about the date and time of their interview after the date had
  already passed**; 45% tried to reschedule and could not; 30% spoke with
  call-centre staff but never heard back from a caseworker. Pilot outcomes 61%
  vs 58% approval, 15 vs 19 days to determination. LA only, no multi-county
  comparison. Grey literature, but a reviewer or referee from this world will
  know it.
- **Riccucci**, "Street-Level Bureaucrats and Intrastate Variation in the
  Implementation of TANF Policies", *JPART* 2005. DOI
  [10.1093/jopart/mui005](https://doi.org/10.1093/jopart/mui005). 124 citations.
  Michigan: formally centralised, counties have "very little formal discretion",
  yet implementation varies. De jure/de facto divergence demonstrated across
  counties within one state — our exact design setting, twenty years earlier,
  qualitatively.
- **Herd & Johnson**, "Rationing Rights: Administrative Burden in Medicaid
  Long-Term Care Programs", *Journal of Health Politics, Policy and Law* 2025.
  DOI [10.1215/03616878-11567708](https://doi.org/10.1215/03616878-11567708).
  10 citations. **The closest work on the documented side:** systematically
  "document[s] state administrative procedures that indirectly and directly
  ration access" across state Medicaid waiver programs, and makes opacity itself
  the finding — "states strategically deploy opaqueness to provide political
  cover". Multi-jurisdiction, procedure-level, about documentation failure. Does
  not put claimant experience on the same ontology, quantify uncertainty, or
  model non-disclosure.
- **Peeters & Widlak**, "Administrative exclusion in the infrastructure-level
  bureaucracy: the case of the Dutch daycare benefit scandal", *PAR* 2023. DOI
  [10.1111/puar.13615](https://doi.org/10.1111/puar.13615). 79 citations.
  Enacted procedure diverging catastrophically from formal entitlement, at scale.
  Single case.
- **Einstein & Glick**, "Does Race Affect Access to Government Services? An
  Experiment Exploring Street-Level Bureaucrats and Access to Public Housing",
  *AJPS* 2016. DOI [10.1111/ajps.12252](https://doi.org/10.1111/ajps.12252).
  133 citations. The audit/correspondence method pointed at a benefit
  bureaucracy. Measures differential responsiveness, not process composition.
  Companion: **Jilke & Van Dooren**, "Discrimination and Administrative Burden
  in Public Service Markets", *JPART* 2018, DOI
  [10.1093/jopart/muy009](https://doi.org/10.1093/jopart/muy009).
- **Pager & Quillian**, "Walking the Talk? What Employers Say Versus What They
  Do", *ASR* 2005. DOI
  [10.1177/000312240507000301](https://doi.org/10.1177/000312240507000301).
  506 citations. Not about agencies, but the canonical methodological template
  for a stated-versus-enacted design. Expect it to be invoked; the honest
  difference is that their enacted benchmark was experimental and ours is
  self-selected forum text.
- **Jang-Trettien & Bolger**, "Racialized Administrative Burden in Disability
  Assistance Programs in Two Rural Counties", *Social Service Review* 2024. DOI
  [10.1086/730819](https://doi.org/10.1086/730819). County-comparative enacted
  burden, qualitative, two counties.

**Covered:** that enacted practice diverges from formal rule; that it varies
across counties inside one state; that agency documentation is strategically
incomplete; audit-experimental measurement of frontline behaviour; and — for
CalFresh interviews in LA specifically — the divergence itself, with numbers.
**Not covered:** a common step ontology letting a published county instruction
and a claimant account be scored as agreeing or disagreeing about the same
procedural action, across all counties of a program, with the two streams
carrying different disclosure probabilities.

### Q3. County/local variation in SNAP/CalFresh administration

**Verdict: ALREADY DONE for county variation in outcomes; ALREADY DONE for one
procedural step across counties including California; PARTIALLY OPEN only for
multi-action process composition.** This verdict is a downgrade from what the
project appears to assume.

**The threat.** **Heflin, Fannin & Lopoo 2023** (above) is the paper to read
first. Method, verbatim from the PMC full text: "Between January 5 and April 30,
2021, trained interviewers telephoned all 626 SNAP local information lines (112
counties shared telephone lines) across the 10 states that administer SNAP at
the county level (**California**, Colorado, Minnesota, New Jersey, New York,
North Carolina, North Dakota, Ohio, Virginia, and Wisconsin)... for a sampling
frame of 738 counties. To reach county offices, interviewers called each phone
number up to three times on separate days... Interviewers were successful 88% of
the time... In total, we were able to document **conditions for submitting a new
application for SNAP in 647 counties**." Finding: only **27%** of counties
implemented the COVID interview waiver; public-health risk, need and political
orientation were not significant predictors; adopters saw a 5% caseload
increase.

Read it precisely: this is per-county primary collection of an *enacted*
procedural condition, on a **three-attempt repeat-contact protocol**, covering
California's counties, already published. Two implications. (i) The claim "no
per-county procedural inventory exists" is dead. (ii) More subtly, the repeat-call
design is structurally a repeat-visit occupancy design that was analysed as if
the phone answer were ground truth — which is an argument *for* our model but
also proof that the data-collection idea is not ours.

Other established county/local variation:

- **Cook & East**, "The Effect of Means-Tested Transfers on Work: Evidence from
  Quasi-Randomly Assigned SNAP Caseworkers", NBER w31307, 2023. Caseworker
  variation in helpfulness navigating the application process affects receipt —
  the within-office analogue of between-county variation.
- **Unrath**, "Pushed Out by Paperwork: Why Eligible Californians Leave
  CalFresh", California Policy Lab 2021,
  <https://capolicylab.org/pushed-out-by-paperwork-why-eligible-californians-leave-calfresh/>.
  55% of exiting households still likely eligible; 6× more likely to exit in a
  recertification month; ~500,000 households a year. **Includes a county-level
  data table** (`Table-of-CalFresh-Exits-at-County-Level-2016-2019.pdf`).
  County-disaggregated CalFresh churn is already public.
- **Shimada**, "Measuring County Food Stamp Performance 2008: The Program Access
  Index", California Food Policy Advocates 2010,
  `http://cfpa.net/foodstamps/2008_PAI/2008_PAI.pdf`. A **county-level index for
  California** modelled on USDA's state Program Access Index, with ~58 per-county
  profile PDFs. A county-level CalFresh performance product already exists; our
  claim must be "process structure", never "first county-level CalFresh measure".
- **Cuffey, Newby & Smith**, "Social inequity in administrative burdens:
  Evidence from SNAP", *PAR* 2023. DOI
  [10.1111/puar.13701](https://doi.org/10.1111/puar.13701). 17 citations.
- **Wu & Meyer**, "Certification and Recertification in Welfare Programs: What
  Happens When Automation Goes Wrong?", NBER w31437, 2023.
- **De Jong & Graefe 2006** (above) for the per-state adopted-options tradition.

**The granularity argument, stated against the right sources.** The federal data
that could substitute for a county process inventory does not exist at
sub-state level, and this should be cited precisely rather than asserted: the
USDA ERS **SNAP Policy Database** is **state-level only, 1996–2020**
(<https://www.ers.usda.gov/data-products/snap-policy-data-sets/>), though it does
include online-application availability and recertification/reporting
requirements; and FNS **Application Processing Timeliness / Recertification
Processing Timeliness** rates are **state-level**, derived from QC reviews,
FY2012–2025 with 2020–21 missing
(<https://www.fns.usda.gov/snap/qc/timeliness>). By contrast the CDSS CF 296
series is county-level, which is why California can support a county design that
most states cannot. Note also, from the agent's inspection of the CDSS data-tables
page, that the listed county series (CF 18 churn, CF 296 caseload, CF 256,
CF 358F/S, STAT 47, WINS 2, ABCD 350) contain **no** application-timeliness,
denial-reason or interview-outcome table — the CalFresh Data Dashboard was not
checked and may add some (§6).

### Q4. Social media / forum text as evidence about administrative process

**Verdict: (a) ALREADY DONE for sentiment/topic/self-reported outcomes —
including on r/foodstamps, for CalFresh, filtered to California. (b) GENUINELY
OPEN for process structure.**

(a) The baseline, and one uncomfortably exact predecessor:

- **Deets**, "Using Computational Modeling for Analyzing Social Media Data",
  *SIGDOC '25* (43rd ACM International Conference on Design of Communication),
  258–259. DOI [10.1145/3711670.3764659](https://doi.org/10.1145/3711670.3764659).
  **Same subreddit, same program, same state.** Verbatim: "examines how SNAP
  (food stamp) recipients use Reddit's r/foodstamps community to navigate
  administrative challenges when official government channels prove inadequate.
  Narrowing posts which are from California, findings reveal that users
  increasingly turn to this informal online [community] during specific periods
  related to benefit timing, particularly experiencing documentation issues,
  payment delays, or technical problems with EBT cards." A two-page extended
  abstract: descriptive and temporal, no latent structure, no county model, no
  step inventory. It does not pre-empt the model but must be cited.
- **Kowalski, Esteve & Jankin Mikhaylov**, "Improving public services by mining
  citizen feedback: An application of natural language processing", *Public
  Administration* 2020. DOI
  [10.1111/padm.12656](https://doi.org/10.1111/padm.12656). 48 citations.
  Public administration's canonical user-generated-text paper (NHS patient
  comments); satisfaction and topic, not process.
- **Zhou & Ren**, "Public Voices on Social Security: A Reddit-Based LDA Analysis
  of Peer Support and Information Exchange", 2026 preprint. DOI
  [10.2196/preprints.100793](https://doi.org/10.2196/preprints.100793).
- **Higgins, Lands et al.**, "Real-Time Effects of Payer Restrictions on
  Reproductive Healthcare... among U.S. Abortion Seekers on Reddit", *IJERPH*
  2021. DOI [10.3390/ijerph18179013](https://doi.org/10.3390/ijerph18179013).
  41 citations. Reddit as evidence about Medicaid coverage barriers.
- HCI on the right object with the wrong instrument (interviews, not corpora):
  "Precarious Experiences: Citizens' Frustrations, Anxieties and Burdens of an
  Online Welfare Benefit System", arXiv:[2405.08515](https://arxiv.org/abs/2405.08515)
  (2024); **Jo, Zhang & Cai**, "AI Trust Reshaping Administrative Burdens",
  arXiv:[2505.22418](https://arxiv.org/abs/2505.22418) (2025).

(b) Nothing found uses Reddit or comparable user-generated content to recover a
process graph, a step inventory, or agency procedural behaviour. But note who
owns the documented-vs-enacted contrast *methodologically* — business process
management, from machine event logs rather than user reports:

- **de Leoni, Maggi & van der Aalst**, "Aligning Event Logs and Declarative
  Process Models for Conformance Checking", 2012. DOI
  [10.1007/978-3-642-32885-5_6](https://doi.org/10.1007/978-3-642-32885-5_6).
  63 citations. Model-versus-log deviation is a mature subfield; no
  imperfect-detection layer, and the log is machine-recorded.
- **Grohs, van der Aa & Rehse**, "Beyond Log and Model Moves in Conformance
  Checking", 2024. DOI
  [10.1007/978-3-031-70396-6_22](https://doi.org/10.1007/978-3-031-70396-6_22).
- **Friedrich, Mendling & Puhlmann**, "Process Model Generation from Natural
  Language Text", 2011. DOI
  [10.1007/978-3-642-21640-4_36](https://doi.org/10.1007/978-3-642-21640-4_36).
  155 citations. Recovers the *documented* side from text only. Also Bellan,
  Dragoni & Ghidini 2022, DOI
  [10.1007/978-3-031-17604-3_11](https://doi.org/10.1007/978-3-031-17604-3_11).
- Process mining under noisy logs treats missing events as data-quality noise to
  filter, never as a modelled detection probability (Benevento et al. 2022, DOI
  [10.1016/j.jbi.2022.104083](https://doi.org/10.1016/j.jbi.2022.104083)).

**Not covered:** user-generated content → process structure; forum accounts and
official agency documents inside one measurement model; any subnational
comparison of benefit-program process structure from forum text; forum silence
treated as a modelled non-detection.

### Q5. Occupancy / imperfect-detection models outside ecology

**Verdict: PARTIALLY DONE — the label is free, the machinery is taken.**

The citation-graph result, the strongest single piece of evidence either way:
MacKenzie et al. 2002 has **4,499 citations** in OpenAlex. Filtering its citing
works by field gives 20 in Social Sciences, 45 in Economics, 11 in Computer
Science, and **0 in Business/Management and 0 in Decision Sciences**. On
inspection of the highest-cited works in each slice, the Economics slice is
essentially misclassified ecology ("Economic and Environmental Valuation"), the
CS slice is vision/games/ML, and the Social Sciences slice is mostly
misclassified ecology. **Exactly two genuine political-science citers surfaced,
and zero public administration, law, organisational-studies or health-systems
applications.** See the caveat in §6: well-supported for high-citation work, not
exhaustive for the long tail.

- **Cook, Blas, Carroll & Sinha**, "Two Wrongs Make a Right: Addressing
  Underreporting in Binary Data from Multiple Sources", *Political Analysis*
  25(2), 2017. DOI [10.1017/pan.2016.13](https://doi.org/10.1017/pan.2016.13).
  **The closest cousin and the most dangerous methods item in this review.**
  Latent binary true event; multiple overlapping sources; separate
  covariate-driven models for the true-event process *and* for each source's
  probability of failing to report. An occupancy model with source-specific
  detection, minus the name and the hierarchical random effect, in a top methods
  journal, nine years ago.
- **Weidmann**, "A Closer Look at Reporting Bias in Conflict Event Data", *AJPS*
  59(2), 2015. DOI [10.1111/ajps.12196](https://doi.org/10.1111/ajps.12196).
  297 citations (OpenAlex; Crossref reports 236). Cites MacKenzie 2002, mis-describes it as capture-recapture, and
  **explicitly declines to use it**: "this approach... may not be suitable for
  problems where all sources are similarly prone to a particular bias." The
  transfer was considered and rejected in print; that objection is ours to answer.
- **Lum, Price & Banks**, "Applications of Multiple Systems Estimation in Human
  Rights Research", *The American Statistician* 67(4), 2013. DOI
  [10.1080/00031305.2013.821093](https://doi.org/10.1080/00031305.2013.821093).
  74 citations (OpenAlex; Crossref 45). With Manrique-Vallier, Price & Gohdes 2013, DOI
  [10.1093/acprof:oso/9780199977307.003.0009](https://doi.org/10.1093/acprof:oso/9780199977307.003.0009).
  Capture-recapture over overlapping documentary lists; same "silence is not
  absence" logic; **list dependence is their central identification worry**.
- **Feldman, Gruskin, Coull & Krieger**, "Quantifying underreporting of
  law-enforcement-related deaths in United States vital statistics and
  news-media-based data sources: A capture–recapture analysis", *PLOS Medicine*
  2017. DOI [10.1371/journal.pmed.1002399](https://doi.org/10.1371/journal.pmed.1002399).
  92 citations. **Official administrative records versus news media as two
  imperfect systems** — the exact official/informal source pairing we propose.
- **Stoner, Economou & Drummond Marques da Silva**, "A Hierarchical Framework for
  Correcting Under-Reporting in Count Data", *JASA* 114(526), 2019. DOI
  [10.1080/01621459.2019.1573732](https://doi.org/10.1080/01621459.2019.1573732).
  55 citations. The count-data analogue of our structure.
- **Hepler & Kaufeld**, "Estimating coccidioidomycosis endemicity while
  accounting for imperfect detection using spatio-temporal occupancy modeling",
  *American Journal of Epidemiology* 2024. DOI
  [10.1093/aje/kwae199](https://doi.org/10.1093/aje/kwae199). The closest use of
  the occupancy *name* outside ecology journals — but the site is still a place
  and the species still an organism.
- **Pemstein, Marquardt, Tzelgov et al.**, "The V-Dem Measurement Model", V-Dem
  Working Paper 21. DOI
  [10.2139/ssrn.3167764](https://doi.org/10.2139/ssrn.3167764). ~100 citations.
  Ordinal IRT over several noisy coders per country-year with coder-specific
  thresholds and reliabilities, for latent **institutional** attributes. The
  canonical "institutions from multiple imperfect raters" model.
- **Cook & Weidmann**, "Lost in Aggregation: Improving Event Analysis with
  Report-Level Data", *AJPS* 2018. DOI
  [10.1111/ajps.12398](https://doi.org/10.1111/ajps.12398). Models each *report*
  as a detection opportunity. Econometric root: Hausman, Abrevaya &
  Scott-Morton 1998 on misclassified dependent variables.

**Covered:** latent binary presence with source-specific false negatives and
covariates on both layers; detection probability by source type for text corpora
(the event-data reporting-bias literature); multiple imperfect documentary
systems → latent count; multiple noisy raters → latent institutional attribute;
hierarchical under-reporting correction; occupancy by name in epidemiology.
**Not covered:** the `z[j,s] × p[s,k]` factorisation applied to organisational,
administrative or legal *procedural-step* presence; any multi-"species" analogue
where the species is a discrete procedural action and the site a jurisdiction
(event-data work carries one latent event type at a time; V-Dem has ordinal
traits, not a fixed action universe; MSE estimates counts of individuals); any
model putting official agency documents and applicant self-reports into one
occupancy likelihood as distinct detection streams.

Two notes from inside the project. `docs/related-work-bayesian.md` §8.10 already
calls MacKenzie et al. 2002 "the best structural match in the review for the
existence layer, and the correspondence is exact", and §8.9 already records the
MSE lineage as "the closest applied analogue in the entire review". The team's
methods map is correct and ahead of this gate; what it is missing is **Cook et
al. 2017 and Weidmann 2015**, which should be added to §8 immediately.

### Q6. CalFresh-specific

**Verdict: ALREADY DONE for process, timeliness, churn, take-up, interviews and
waivers. This is a crowded, well-funded field with top-journal RCTs, a dedicated
administrative-data shop, and a decade of operator-side research.** Any framing
implying "nobody has studied CalFresh application friction" will not survive.

- **Giannella, Homonoff, Rino & Somerville**, "Administrative Burden and
  Procedural Denials: Experimental Evidence from SNAP", *AEJ: Economic Policy*
  2024. DOI [10.1257/pol.20220701](https://doi.org/10.1257/pol.20220701)
  (22 citations); NBER WP 31239, DOI
  [10.3386/w31239](https://doi.org/10.3386/w31239), open PDF at
  nber.org/papers/w31239. Field experiment, 65,000 LA County applicants, run
  with LA DPSS and with CDSS permission. Three details from the PDF, which was
  retrievable and which matter more than the abstract:
  1. **The sample is GetCalFresh**, and "GetCalFresh operates in **all 58
     counties in California** and currently receives roughly half of all SNAP
     applications in Los Angeles." Code for America therefore holds
     application-level data for every county in our design.
  2. **Figure 1 is already a step-level outcome decomposition** — "Outcomes and
     denial codes for all GetCalFresh applications submitted to Los Angeles
     County between October 8, 2018 and May 15, 2019": Approved 43.5%, **Missed
     Interview 33.7%**, Missing Income Verification 8.3%, Withdrawn 4.6%, Over
     Income 3.8%, Other Denial 3.4%, Other Ineligible Status 2.7%.
  3. **They state the county-comparison gap themselves**, footnote 7: "We do not
     have data on how the ease of rescheduling in Los Angeles compares to that
     in **other counties** or states; however, prior research suggests that even
     in particularly well-staffed offices, relatively few individuals who miss
     their caseworker interview reschedule their appointment (Homonoff and
     Somerville, 2021)." This is the best external warrant for our residual
     claim: the nearest prior work names cross-county variation in the
     missed-interview/reschedule step as something it cannot observe.
- **Moynihan, Giannella, Herd & Sutherland**, "Matching to Categories:
  Learning and Compliance Costs in Administrative Processes", *JPART* 2022. DOI
  [10.1093/jopart/muac002](https://doi.org/10.1093/jopart/muac002). 49
  citations. GetCalFresh
  field experiment: clearer category presentation raised self-employed
  self-identification from 8.8% to 12.1%; a self-attestation template raised
  acceptable documentation. A verification-step burden paper.
- **Homonoff & Somerville**, "Program Recertification Costs: Evidence from
  SNAP", *AEJ: Economic Policy* 2021. DOI
  [10.1257/pol.20190272](https://doi.org/10.1257/pol.20190272). 44 citations. Later interview
  assignment — less time to reschedule a missed interview — cuts recertification
  success by ~22%. The canonical "interview scheduling is the mechanism" paper.
- **Homonoff, Lee & Meckel**, "The Financial Consequences of Being Denied
  Benefit Access", NBER w34434, 2025. DOI
  [10.3386/w34434](https://doi.org/10.3386/w34434). Uses variation in
  flexibility of mandatory intake interviews (same LA setting) linked to credit
  records; procedural screen-outs suffer downstream economic harm.
- **Chabot & Hell**, "Using Technology and Iterative Research to Strengthen the
  Social Safety Net", *Annals of the AAPSS* 2023. DOI
  [10.1177/00027162231205391](https://doi.org/10.1177/00027162231205391).
  Code for America authors; stage-by-stage (outreach / application / renewal)
  account of benefits delivery — the nearest thing to a CfA process map in a
  peer-reviewed venue.
- **Unrath**, "Pushed Out by Paperwork", California Policy Lab 2021 (above).
- **Daw, Pache & Zhou**, "Due Process on Hold: A Queueing Framework for
  Improving Access in SNAP", arXiv:2605.15165 (2026). Models procedural denials
  as endogenous call-centre congestion using court-disclosed Missouri
  call-centre data from *Holmes v. Knodell*, where "nearly half of all denials
  [were] procedural, caused by applicants' inability to complete required
  interviews, rather than underlying ineligibility". **A live competing
  formalism** for why procedural denials happen, arguing the failure is
  system-level rather than process-step-level.
- **California Food Policy Advocates**, "Best Practices to Improve the Food
  Stamp Program in California" (Manalo-LeClair, Chen & McLaughlin, c. 2001),
  archived at `http://www.cfpa.net/foodstamps/BestPractices.pdf`. Explicitly
  motivated by county process autonomy: "Because the 58 counties have
  considerable autonomy in implementing the Food Stamp Program... **CFPA has
  visited roughly half of the counties in California** to see what steps they
  are taking." Catalogues named-county practices including non-traditional office
  hours (Sacramento), clerical application assisters (Santa Cruz/Watsonville),
  customer-service standards, and **"Appointments or No Appointments"**. Old,
  qualitative, non-exhaustive — and a prior attempt at a 58-county process
  practice inventory.

**Code for America / GetCalFresh, in detail.** CfA ran GetCalFresh 2014–2025,
reaching all 58 counties by June 2019 and roughly 70–73% of all online SNAP
applications statewide; 6.2–7M households and ~$12.8B in benefits
(<https://codeforamerica.org/success-stories/simplifying-californias-online-application-for-food-benefits/>,
<https://codeforamerica.org/news/reflecting-on-10-years-of-getcalfresh/>). Their
publications are blog/news posts rather than reports:

- "Think Big, Start Small" — the interview-step documented-vs-enacted findings
  quoted under Q2.
- "Overcoming Barriers: How GetCalFresh Helps Applicants Submit Verifications",
  <https://codeforamerica.org/news/overcoming-barriers-how-getcalfresh-helps-applicants-submit-verifications/>.
  **17% of applications denied for missing verification documents**; 47% of
  applicants upload at least one document; including 3+ verification documents
  correlates with a 20% higher approval probability; an auto-reminder experiment
  raised 48-hour upload from 15.2% to 22.6%. Draws on "six counties" for
  approval outcomes but gives **no per-county breakdown**, and never states
  "counties demanding verification not required by rule" as a finding.
- "Overcoming Barriers: Setting Expectations for CalFresh Eligibility",
  <https://codeforamerica.org/news/overcoming-barriers-setting-expectations-for-calfresh-eligibility/>.
  ~15% denied over-income; 30.2% of 1,103 denied survey respondents said income
  too high; cross-validated against **county staff reading eligibility case
  notes for a random sample of 400 denied applications** (~30% over-income).
  Methodologically adjacent to our detection model — a source-agreement exercise
  between applicant self-report and county case notes — but one county sample,
  one denial reason, no per-county estimates.
- **Safety Net Benefits Field Guide**, <http://codeforamerica.org/FieldGuide>
  (announced <https://codeforamerica.org/news/safety-net-benefits-field-guide-release/>).
  A systematic scan of benefits applications across **all 50 states + DC + PR**
  on mobile responsiveness, time to complete, Spanish support, account-registration
  requirement and program integration; "nearly 77% of programs analyzed now have
  applications online, and of those 2 out of 3 can be filled out on a mobile
  phone." **This is the structural-scan-of-documented-requirements idea already
  executed** — at state granularity, on interface features rather than
  procedural actions. The single best precedent for our documented side.
- County process variation they documented only as background: pre-BenefitsCal
  California ran **three different online application systems depending on the
  applicant's county**, and the state application was "more than 50 web pages
  long, filled with over a hundred questions... Most who start it don't finish
  it" (archived
  <https://web.archive.org/web/2019/https://www.codeforamerica.org/featured-stories/california-counties-make-it-easier-to-apply-for-calfresh>).

**Direct answers to the three CfA questions.** (i) **No** — CfA never published a
per-county characterisation of procedural steps; their county-disaggregated
publication is essentially nil, with no county conversion, approval or
timeliness tables surfaced. (ii) **Partially** — they documented enacted-vs-documented
divergence for the *interview* step in LA County and for *verification* in
statewide aggregate, but never "counties demanding verification not required by
rule" as an explicit finding. (iii) **No** county-practice survey, policy scan or
process map was found on codeforamerica.org. Dave Guarino (GetCalFresh lead)
writes at <https://daveguarino.substack.com/> but the archive is 2024-onward and
mostly AI/benefits-navigation; his one procedural piece is on *Holmes v.
Knodell*, i.e. Missouri.

## 3. Nearest prior work

There are **two** nearest works, on different axes, and the project is boxed in
between them.

**On the substance and mechanism: Giannella, Homonoff, Rino & Somerville 2024
(AEJ: Economic Policy)**, with Code for America's "Think Big, Start Small" as its
grey-literature twin. Same program, same state, same county-administered system,
same mechanism, a causal design we cannot match, and a published step-level
denial decomposition.

**On the estimand and design: Heflin, Fannin & Lopoo 2023 (American Review of
Public Administration).** Per-county procedural data, primary collection,
repeat-contact protocol, California included, in a public administration journal.

| dimension | Giannella et al. 2024 | Heflin et al. 2023 | proposed contribution |
|---|---|---|---|
| jurisdictions | 1 county (LA) | 647 counties, 10 states, incl. all CA | 58 CA counties |
| procedural actions | 1 (interview), outcomes decomposed | 1 (interview waiver / new-application conditions) | ~20 |
| evidence | agency admin records, RCT | telephone calls to county offices, ≤3 attempts, 88% success | published county instructions, staff handbooks, Reddit accounts, aggregate reports |
| observation model | none needed (randomised) | none — phone answer treated as truth | detection probability per source genre; silence is a non-detection |
| documented side | not studied | not studied (asks the agency, not its publications) | the object of the headline claim |
| estimand | causal effect of a redesign | county waiver adoption + its caseload effect | latent step-presence matrix + documentation gap |

So the daylight is genuinely narrow and it is all in the same three places:
**many actions rather than one**, **what counties publish rather than what a
phone call elicits**, and **a modelled observation process rather than assumed
ground truth**. Everything else on the proposed contribution's face has been
done by one of these two papers. The mitigation is to stop treating the
missed-interview mechanism as our finding, cite Giannella et al. and CfA for it,
cite Heflin et al. as the prior per-county procedural measurement we extend, and
make the **documentation gap** the claim — since that is a fact about what
counties publish, which neither paper studies.

## 4. Threats to the claim

Ordered by how badly each would have hurt.

1. **Heflin, Fannin & Lopoo 2023, ARPA.** Per-county, primary-collected,
   published procedural data for SNAP across ten county-administered states
   **including California** — 647 counties, three-attempt telephone protocol,
   88% success. Kills "no per-county procedural inventory exists" outright.
   Verified from the PMC full text; the state list is quoted in Q3.
2. **Giannella, Homonoff, Rino & Somerville 2024 / NBER w31239.** Fatal to an
   "interviews cause CalFresh denials" headline. Also a governance point: they
   ran with LA DPSS under CDSS permission, so the bar for claims about LA is high.
3. **Code for America, "Think Big, Start Small".** The documented-vs-enacted
   headline already exists in print for the interview step: 1 in 3 procedural
   denials against 6% ineligibility, and 19% of respondents receiving their
   interview time only after the date had passed. Presenting documented-vs-enacted
   divergence as an unanticipated discovery would be embarrassing.
4. **Code for America, Safety Net Benefits Field Guide.** An existing systematic
   scan of documented application requirements across 52 jurisdictions.
5. **Cook, Blas, Carroll & Sinha 2017, *Political Analysis*.** An occupancy model
   in all but name. Any sentence like "we are the first to model latent presence
   with source-specific detection in the social sciences" is false.
6. **Weidmann 2015, *AJPS*, ~240-300 citations, already published the identification
   objection.** He cites MacKenzie and rejects multi-source correction precisely
   when *all* sources share a bias. If Reddit applicants and county instruction
   pages both systematically omit the same steps, source multiplicity cannot
   identify detection.
7. **CFPA c. 2001, "Best Practices".** A county-visit-based inventory of
   CalFresh process practices across roughly half of California's 58 counties,
   framed exactly on county implementation autonomy. A reviewer who knows it
   will ask why we do not cite the prior 58-county practice-inventory attempt.
8. **Brodkin & Majmundar 2010.** 275 citations for the proposition that
   prescribed and informally created operational practices diverge. Only the
   measurement can be new, never the idea.
9. **Riccucci 2005.** Cross-county implementation variation inside one state's
   welfare program, already demonstrated.
10. **List/source dependence.** Occupancy and MSE both require detections
    independent given latent presence. Applicants read the county page, so the
    two streams are dependent by construction. Lum, Price & Banks 2013 make list
    dependence the central threat in exactly this setting. The project's own
    "copied documents are not independent" note is the same problem and needs an
    explicit model, not a caveat.
11. **Design identifiability with few sources per county.** With ~20 actions and
    a handful of sources per county, expect Guillera-Arroita & Ridout 2010 on
    occupancy study design (DOI
    [10.1111/j.2041-210x.2010.00017.x](https://doi.org/10.1111/j.2041-210x.2010.00017.x),
    221 citations), Lele et al. 2012 on single-survey detection error (DOI
    [10.1093/jpe/rtr042](https://doi.org/10.1093/jpe/rtr042)), and above all
    Martin et al. 2005, "Zero tolerance ecology: improving ecological inference
    by modelling the source of zero observations", *Ecology Letters* (DOI
    [10.1111/j.1461-0248.2005.00826.x](https://doi.org/10.1111/j.1461-0248.2005.00826.x),
    **937 citations in OpenAlex, 762 in Crossref**) — the canonical "which zeros are real" paper, directly on
    point for "not-required is not absent".
12. **Herd & Johnson 2025.** Multi-jurisdiction documentation of administrative
    procedure with opacity as the finding — the same rhetorical structure.
13. **Daigneault et al. 2025, *Public Administration*.** If one of its six
    government burden-measurement approaches is a process or journey map, our
    "burden has never been operationalised as process structure" sentence is
    wrong as written. **Unread — see §6.**
14. **Code for America holds the county-complete data.** GetCalFresh "operates
    in all 58 counties". Whoever holds that data can do a per-county
    application-outcome analysis far better than we can from forum posts, and has
    already published the LA version. Our claim must be about what counties
    *publish*, which their data cannot show.
15. **De Jong & Graefe 2006.** Latent-variable measurement models fitted to
    per-jurisdiction welfare rule codings. Undercuts any claim that applying a
    measurement model to jurisdiction-level rules is novel.
16. **Pager & Quillian 2005.** The stated-vs-enacted design template; their
    enacted benchmark was experimental, ours is self-selected forum text.
17. **Business process management owns "documented vs enacted."** Conformance
    checking is a mature subfield built on exactly that contrast.
18. **Deets 2025, SIGDOC.** Same subreddit, same program, same state. Only a
    poster, but an uncited exact-corpus predecessor looks like a missed scoop.
19. **4,499 citations and ~2 social-science uptakes.** A reviewer may read the
    emptiness of the occupancy transfer as evidence it is *unattractive*, not
    merely unattempted. We need an affirmative argument for why occupancy beats
    the existing misclassification/MSE machinery: the fixed action universe, the
    jurisdiction random effect, and genre-indexed detection are the candidates.
20. **County-level CalFresh products already exist** — CPL's county exit table
    2016–2019 and CFPA/Shimada's 2010 county Program Access Index with ~58
    per-county profiles. Never claim "first county-level CalFresh measure".
21. **Internal, not literature, but decisive:** the project's own morning audit
    records the fit losing to a pooled Beta baseline (0.072 vs 0.061), county
    contrasts confounded with source genre, and the forum-only model reading
    silence as absence. A novelty claim about per-county process structure is
    not currently supported by the fit.

## 5. What would make this publishable

Ranked by survival against the literature above.

1. **The documentation-gap paper (strongest, and the only one clearly clear of
   prior work).** Claim: across California's 58 counties, publicly published
   CalFresh application instructions systematically omit procedural steps that
   state regulation and legal-aid guidance treat as mandatory — with the
   missed-interview notice-and-reschedule sequence as the flagship — while CDSS
   administrative data show the omitted steps are exactly where denials happen.
   This needs no occupancy model and no forum data; it is a fact about
   government publications paired with administrative counts. Herd & Johnson
   2025 is the template; CfA's Field Guide is the state-level precedent to
   extend downward; Heflin et al. 2023 is the prior per-county procedural
   measurement to extend across actions. Positions against the Q1 measurement
   gap and the Q3 structure gap at once.

   *One caveat on the flagship number.* The "1 of 58 county instruction pages
   mentions missed-interview procedure" figure was not independently verified
   here, and the bounded county inventory in
   `runs/process_structure_20260921/calfresh_county_guides_20260921/` does not
   quite say it. Searching both halves finds the Notice of Missed Interview
   (NOMI / CF 386) in exactly **two** captured sources, one self-labelled
   "substantive staff policy, not applicant-facing guide" and the other a "county
   post-application handout" — so the count for *applicant-facing county
   instruction pages* is 0 or 1 depending on classification. The O–Y half
   contains no NOMI or reschedule language at all. The direction is as claimed,
   but the denominator is not 58 comparable applicant-facing guides (the
   checkpoint records 34 locally bound sources, 3 substantive gaps, 20 uncaptured
   leads). This is the paper's central number and it needs a stated denominator
   and capture rate before anything is drafted.

2. **The instrument paper (viable, methods venue).** Claim: a reviewed-silence
   observation model for inferring institutional practice from heterogeneous
   documents, where detection probability is indexed by *document genre* and a
   zero-yield re-read is an informative observation. Frame as a descendant of
   Cook et al. 2017 and of multiple-systems estimation with systematically
   different list coverage — **not** as a fresh import from ecology, which is
   both less honest and easier to attack. Must answer Weidmann's common-bias
   objection and model source dependence explicitly. Requires the synthetic
   recovery results to carry the validation, since the real fit currently does
   not.
3. **The county-variation paper (blocked today).** Claim: counties differ in
   process composition. Blocked by the confounding the internal audit
   identified — with ~1 reading per cell and source genre varying by county,
   county effects are not separable from genre effects. Would need balanced genre
   coverage per county, or an explicit genre-by-county design. Note that Heflin
   et al. show how to get balanced per-county coverage cheaply: call every
   county, three times.
4. **Reframings that do NOT survive.** "Administrative burden has never been
   measured structurally" (Brown et al. 2021; sludge audits; De Jong & Graefe
   2006; Heflin et al. 2023). "Documented and enacted process diverge" as a
   finding (Brodkin & Majmundar 2010; CfA "Think Big, Start Small"). "Counties
   vary in implementation" as a finding (Riccucci 2005; Heflin et al. 2023).
   "First county-level CalFresh measure" (CFPA 2010 PAI; CPL 2021 exit table).
   "The intake interview drives CalFresh procedural denials" (Giannella et al.
   2024). "First application of imperfect-detection models outside ecology"
   (Cook et al. 2017; Feldman et al. 2017; Hepler & Kaufeld 2024).

## 6. Blocked, and limits on coverage

Read this before treating any absence above as a finding.

**Search infrastructure.**

- **WebSearch: not used at all**, by the lead reviewer or either subagent
  (briefed as exhausted at 200/200). There is **zero search-engine coverage** in
  this review; everything is API or direct fetch.
- **OpenAlex: hard-blocked partway through, for all three reviewers.** Worked for
  roughly the first half, then returned `{"error":"Rate limit exceeded",
  "message":"Insufficient budget... free daily budget shared by everyone on your
  network's IP address... resets at midnight UTC"}`. Confirmed still blocked
  after a wait. Everything attributed to OpenAlex was retrieved before the
  cutoff; **no post-cutoff OpenAlex query returned rows, and none of those
  failures is evidence of absence.** Largest single consequence: citation-graph
  traversal was available for only two seeds (Giannella et al., 13 citing works;
  MacKenzie et al. 2002, field-sliced) and then lost. **Undone and highest-value
  follow-up: `cited_by_api_url` on Heflin et al. 2023 and on Giannella et al.
  2024**, plus compound `cites:W2116665868` filters intersected with
  institution/organisation/policy/bureaucracy/administrative/human-rights terms,
  and the citing works of the MacKenzie *Occupancy Estimation and Modeling* book.
- **Semantic Scholar: fully blocked.** HTTP 429 on every attempt across all three
  reviewers, including after 6 s and 25 s sleeps. **Zero rows obtained.** No
  conclusion rests on it.
- **arXiv: intermittent and partly misleading.** The `http://` endpoint
  301-redirects and silently returns zero entries; `https://` with `-L` works.
  Relevance ranking is poor for social-science phrasing, and quoted-phrase syntax
  (`all:"occupancy model"`) returned total=0 *while the API was live*, so those
  specific results are **uninformative, not negative**. Later in the run it
  returned empty bodies for everything. Unrun: `r/foodstamps`; `online community
  benefits navigation bureaucracy`; `social media public benefits applicants
  experience`; `social media AND unemployment insurance AND claimants`; and
  several similar.
- **Crossref: worked, but is a metadata matcher, not a concept search.**
  `query.bibliographic` returns near-random results for conceptual queries
  (million-plus result counts are meaningless, and hits are polluted by decision
  letters and figure captions). `query.title` and DOI-keyed lookups were reliable
  and are the source of the verified metadata and several abstracts. **Assume low
  recall for concept discovery.**
- **Unpaywall worked well** (`api.unpaywall.org/v2/<DOI>?email=...`) and should be
  the first stop next time; it is how the Heflin PMC copy was found.
- **An OpenAlex semantics error worth recording:** OpenAlex relevance `search`
  ANDs its terms after stemming. Several early multi-term queries returned 0 or 1
  results not because the literature is empty but because the conjunction was
  unsatisfiable (e.g. "CalWORKs CalFresh county administrative data California
  Policy Lab churn" → 0). Short queries were substituted once diagnosed, but some
  early long queries were never re-run before the rate limit hit.

**Publisher and site blocks.**

- **Wiley** (`onlinelibrary.wiley.com`, including `pdfdirect`) and **Duke**
  (`read.dukeupress.edu`) return HTTP 403 with a Cloudflare JavaScript
  challenge. No CAPTCHA was attempted. Consequence: **Daigneault et al. 2025 and
  Herd & Johnson 2025 are confirmed open access and still could not be read.**
  NBER and PMC PDFs *are* fetchable, which is why Giannella et al. and Heflin et
  al. could be read in full.
- **Sage** (`journals.sagepub.com`) blocked — but Heflin et al. was recovered via
  PMC, so the California-inclusion question is **resolved**, not open.
- **Completely uncovered organisations:** **CBPP** (`cbpp.org` — a likely
  publisher of SNAP interview-waiver and procedural-denial analysis; treat as a
  known gap), **PPIC** (`ppic.org/?s=CalFresh`), **Western Center on Law and
  Poverty** (`wclp.org` — a plausible home for a 58-county legal-aid scan),
  **Urban Institute** (not attempted), **UCLA Center for Health Policy Research**
  and **UC Berkeley Labor Center** (not attempted).
- **California State Auditor: completely inaccessible.** `auditor.ca.gov/reports/recent`,
  `/reports/recent_reports`, `/reports/search`, `/reports/reports_by_subject` and
  the `information.auditor.ca.gov` redirect targets all returned 404. An
  individual report shell was reachable but no report could be enumerated.
  **Unresolved gap — a State Auditor CalFresh county-administration audit, if one
  exists, would be a direct hit.**
- **California Policy Lab:** `capolicylab.org/publications/` and the
  `wp-json/wp/v2/publications` endpoint were Cloudflare-blocked; coverage was
  obtained via `wp-json/wp/v2/search`, which may have missed publications.
- **Code for America:** `sitemap.xml` and `sitemap_index.xml` bot-challenged,
  `/resources/` 404. Enumerated via `wp-json/wp/v2/search` across 19 query terms,
  so coverage is good but not provably exhaustive. **The Field Guide tool itself
  (`codeforamerica.org/FieldGuide`) was not opened.**
- **CDSS:** the **CalFresh Data Dashboard** was **not opened**; only the parent
  data-tables page was confirmed. Whether the dashboard adds county application,
  denial-reason or interview-outcome metrics is **unverified**.
- **Nourish California:** publication listing renders poorly; only three
  CalFresh-adjacent briefs recovered, and the annual CalFresh Forum materials
  (<https://nourishca.org/calfresh-forum/>) were not opened.
- **`web.archive.org` via WebFetch** is hard-blocked by the harness; worked
  around with `curl` against the CDX API and `/web/<ts>id_/` replay.
- **`digitalbenefitshub.org`** redirect chain 404'd; only the Digital Government
  Hub homepage was read.

**Specific records not retrieved.**

- Full text of **Daigneault et al. 2025** — its six measurement approaches are
  the highest-value unread item in this review.
- Full text of **Herd & Johnson 2025**; of **Cook et al. 2017** (no OA location);
  of **Deets 2025** (ACM OA PDF URL recorded, not fetched); of **Halling &
  Bækgaard's** 119-article coding scheme.
- Abstract of **Jang-Trettien & Bolger 2024** (not in Crossref; publisher page
  not fetched).
- **Hendrix & Salehyan 2015, "No News Is Good News?"** — found only inside
  Weidmann's bibliography; no DOI or venue record retrieved.
- **Bagozzi, "Modeling Two Types of Zeros"** — 0 hits; likely a chapter or
  differently titled.
- **Daw, Pache & Zhou 2026** — arXiv id 2605.15165 recorded from the subagent;
  not independently located by title search on the arXiv API, and only the
  truncated OpenAlex abstract snippet was read.

**Not searched at all.** Non-English literature; books and edited volumes beyond
those surfaced incidentally; law reviews (poorly covered by all APIs used);
dissertations; ACM DL / CSCW / CHI proceedings search, which is where
forum-text-about-benefits work is most likely to live.

**One caveat on the headline Q5 result.** OpenAlex `primary_topic.field.id`
misclassifies heavily — many ecology papers land in "Social Sciences" and
"Economics". The top ~12 works by citation count in each of five field slices
were inspected, not all works in those slices. "Zero public administration, law
or organisational applications of occupancy models" is well-supported for
high-citation work and **not exhaustive for the long tail.**
