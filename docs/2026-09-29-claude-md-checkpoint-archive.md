# CLAUDE.md checkpoint archive (moved 2026-09-29)

Verbatim copy of CLAUDE.md as of 2026-09-29, before it was trimmed to standing rules at Alex's request.
These dated checkpoints are historical status, not current instructions. sha256 of the original file:

    6365d070b4ae833e2881203c15bfcddd9261ea93343c7484eb5b3e95a32bcbb4

---

# Project working conventions

- CORE GOAL (Alex, 2026-09-26) — read docs/CORE_GOAL.md first. The lever is
  BETTER-WRITTEN STATUTES. Frame: statute -> decision model (d-steps read from
  text, tagged concrete/vague) -> per-jurisdiction process models (p-steps that
  refine each d-step; may be shared) -> partial observations. Bayesian model and
  LLM baseline answer the SAME estimands: (1) burden per p-step (elapsed days,
  applicant hours, dollars kept distinct) rolled up to d-steps and the statute;
  (2) complexity of the decision model and of the process models, incl.
  cross-jurisdiction implementation variety of vague steps; (3) counterfactual
  statute edits (make vague step concrete, change deadline) -> burden change.
  Current step: toy statute, docs/2026-09-26-toy-statute-plan.md.

- Toy statute 2026-09-26 RESULTS: docs/2026-09-26-toy-statute-results.md.
  Code pipeline/procbench/toy_statute/ (15 tests), runs runs/toy_statute_20260926/W0/.
  Bayes: fit001 RWM FAILED, fit002 SMC FAILED, fit003 SMC narrow FAIL (SMD .119>.1,
  Rhat pass); preserved, no more attempts under that protocol. Bayes wins structure
  (logscore -.001 vs LLM -.21) and per-p-step interval scores; tool-less Opus avg3
  wins roll-ups + drafting counterfactual (statute cf truth -10.6: LLM -11.0, Bayes
  -8.0, too wide). Whole-process clocks do not identify per-step burden (ridge).
  LLM prompt leaked "14-day-style comment period" (disclosed). Next: LLM-elicited
  priors hybrid, random-world replication, V6 adapter. Weekly Claude limit hit
  2026-09-26 (resets 09-30 11am PT); Solar packets 0721-0729 unread, relaunch fresh.

- Toy statute OUTCOMES + VALIDITY (2026-09-28): validity checker docs/process-validity.md
  (toy_statute/validity.py, design_optimum.py): C1-C6 per reading of vague clauses; only
  notice-and-hearing S4 valid under every reading ("defensive proceduralism"); safe harbour
  makes S1 safe. Outcome layer docs/2026-09-28-toy-statute-outcomes-{plan,results}.md
  (outcomes.py, score_outcomes.py; worlds W0o/W0o_adv reuse W0/fit004 process posterior via
  a CUT). 4 fits PASS. Design tradeoffs (S1->S5: +44-57 burden day-eq, -4 nuisances/100 W0o)
  recovered; shared-pi model breaks under confounding (W0o_adv cov .65), hier fixes (.92);
  deterrence beta biased low via burden-input error (replication W0o_rep, cov 4/10). LLM
  again wins head-to-head. Per-step ledger (step_ledger001.json): step outcome effects are
  context-dependent (overlapping safeguards), composites only where steps co-occur.
  Round-3 composite reparam results docs/2026-09-28-toy-statute-round3-results.md: 8/8 done,
  gate v2 1/8 PASS (W0m) but failing params 5-17 -> 0-7, worst SMD .22-.42 -> .10-.22; remaining
  fails look like MC noise floor (hypothesis; test = predeclared bigger run). W0x25 score .555->.394
  (per-step 1.27->.68): round-2 25x degradation was a sampler artefact; Bayes beats LLM 74:12 at 25x.

- Toy statute ROUND 2 (2026-09-26): docs/2026-09-26-toy-statute-round2-results.md.
  Worlds W0,W0m(milestones),W0x5,W0x25,W1(adversarial),W1m. Centered model fit004 PASSED
  both gates; all other round-2 SMC fits FAIL gate v2 exactly on unidentified directions
  (sampler failure = non-identification). LLM wins common-sense world with thin data;
  Bayes wins with more data (h2h 16:64 -> 53:32 -> 73:13) and in adversarial W1/W1m.
  Milestones (deemed complete/inspection) fix W1 per-step for both methods. Step-linking
  diagnostic toy_statute/identify.py: step burden identified iff bounding events observed;
  key real-world milestone = plan-check/review complete. LLM priors helped at x1.5
  widening; conflict flag insensitive. Fee split bug fixed post hoc (R2-B). Fits ran on
  sk3 (/dfs/scratch0/alexspan/toy_statute) after Mac load ~500. Next: composite
  reparameterization of jointly-identified blocks; identification status per estimate.

- Solar September23 STEP INTEGRATION, newer than the bulk two-clock result below:
  user requested remaining actual step/process work. Read
  docs/2026-09-23-solar-step-level-integration.md. New reviewed-action compiler
  and activity_event_interval operator bind reports to one shared case graph;
  actual-case summarizer separates occurrences/concepts/residuals and leaves
  unseen full counts, population rework and intrinsic capability UNKNOWN.
  Work in runs/solar_step_model_20260923/. Four-case joint4_fit001 PASSED generic
  and 89 actual-case gates (LL Rhat1.00151, ESS2599). First rightwinger_fit001
  FAILED; core2 generic prediction precision FAILED though actual-case passed.
  joint8_fit001 (45clocks46components) and joint8_fit002 (48clocks50components)
  COMPLETED/PASS; same8people, NOT16cases.002 is primary, adds
  Concord whole-clock under explicit top-reading boundary assumption. Immutable
  compiler receipts identify exact packets. DO NOT mutate Sol originals or
  include followup001 alongside successor002. 50components is across8journeys,
  NOT50steps per installation or the separate50-action occupancy universe.
  Sampler case-update-block-size1 +exact case-local updates target unchanged;
  no agency/source learning claimed (scales0), elapsed only. Claude bulk fetch
  untouched. No renewed corpus verification;73 focused tests passed.
  Primary worstRhat1.00232/minbulkESS1077;all156 actual-case checks pass.
  Final result001.json +joint8_case_posterior002.json bind inputs/draws.
  SUBSTANTIVE OPEN ISSUE: Concord under-month report is admitted but whole
  posterior37.2[23.6,90.5]days;73.3%above31days. Sept29 diagnostic correction:
  native Student-t broad-error responsibility18.7%, not the older Gaussian
  diagnostic's27.3%; saved posterior unchanged. Native check also finds
  same-day approval median4.21[.62,22.22]days with61.5% broad-error
  responsibility. See runs/solar_model_20260929/concord_historical_report_checks001.json.
  The original concord_whole_clock_check001.json is retained, superseded for
  these report-kernel diagnostics. Not a compiler drop
  now: report-error/gap-prior tension. No good-recovery/full-model claim.
  37/40tasktypes singleton; conditional pooled permit-review5.06[2.61,9.54]
  days from4cases6occurrences, NOTintrinsicagencycapability. Next meaningful
  statistical task is frozen-evidence report-kernel/gap-prior sensitivity,
  alongside broader compiler adoption, NOTmore sampling/quoteverification.
  Both previous same-evidence comparisons now SCORED: admin002 Bayes51.01148
  vsLLM47.95344, forum_comparison002 Bayes2.65124 vsLLM2.68135. BOTH bootstrap
  intervals include0; no Bayeswin, no step-model validation. See
  docs/2026-09-23-solar-existing-baseline-results.md. Admin scalar-serialization
  repair only, no changed scientific score. Do not restart old baseline jobs.

- Solar September23 user override: quick-check Claude's completed bulk reads,
  then apply existing Bayesian model; do NOT interrupt Claude downloads or
  restart exhaustive verification. Read docs/2026-09-23-solar-bulk-adoption-and-fit.md.
  Frozen228packets (226Reddit/3818threads/76674comments +2externalpagepackets)
  at runs/solar_bulk_adoption_20260923/frozen_inputs001.json. Luna ONE checker
  pass202PASS/26FAIL: geographyfieldformatting +external locatoradapter only;
  no sourcehashmismatches. FINAL adopted001:2713elapsedreports; every15335
  extractedfieldentry routed. Fit001 COMPLETED/PASS:contract→install21reports,
  median106[74,156]days;install→PTO94reports,86[67,113]. California001subset22,
  100[58,193],PASS. Intervals90%credibleforMEDIAN,notindividualpredictions.
  WorstRhat1.00075/minESS4009;2coords4x(1000warmup+2000draws),sameV6kernel.
  Only115distinctobservations ACTUALLYfit;161heterogeneous/non-target +2437
  low-support labelsretained. Top100numeric-labelcrosswalk only;singleton
  endpointreconciliation remains compilerwork,NOTnewreading/verification.
  No county gate;no population/agencycapability/structure/LLMwinclaim. NewClaude
  snapshotONLY,notcumulativeoldCodex. Finalclaimconsumption+results in
  runs/solar_bulk_adoption_20260923/result001/. Keepallstagedoriginals.

- Evaluation18:36UTC: administrative admin002 baselines root78110:2/5 complete,
  remaining live, no scoreyet. Forum comparison002 baselines root74682 live;
  comparison001 metadata superseded beforeexecution, actualprompt byteidentical.
  Forum001/fit003_exact_marginal PASS Rhat1.00145/minbulkESS4471.23, 2coords
  same scientific likelihood/prior as102coord fit002 FAILED (bulk198.11).
  q128→256 maxΔLL2.92e-8; BayesianreportCDF +simpleMLCDFsavedcomparison002.
  Score only afterall5repeat answers/failurereceipts exist. Commands:
  python -m pipeline.procbench.solar_panel.evaluate_same_evidence score --out runs/solar_evaluation_20260922/admin002
  python -m pipeline.procbench.solar_panel.evaluate_forum_predictions score --out runs/solar_evaluation_20260922/forum_comparison002
  Use uv requirements-bayes env. Do notstartduplicatejobs/retryfromsilence.
  BulkAPIhandoff nowacceptedbyClaude (record18:14UTC); Codexnoacquisition.

- Solar evaluation override 2026-09-22 18:29UTC: user says Claude is doing bulk
  acquisition; Codex now focuses on Bayesian evaluation/comparison. Read
  docs/2026-09-22-solar-evaluation-progress.md. admin002 has frozen2238 rawtrain
  permit-review cells/64heldout queries, five Astra xhigh baselines RUNNING
  root session78110 (2concurrent), no scoresyet. admin001 CANCELLED before scoring
  for two input/scope defects; same64ids in002, no sample shopping. Full50fit001
  TERMINAL FAILED Rhat1.08024, minbulkESS43.13; no structureposteriors valid.
  Forum00148train9test split; correctedfit ownedmodelSol, CDFcomparison001frozen.
  Do not revive acquisition/parsing, rerun failed structurefit, or claim these
  component comparisons validate intrinsicagencycapability/fullprocess.

- Solar bulk handoff September 22: Alex requests Claude's help with mass download
  and reading. Read docs/2026-09-22-solar-download-and-reading-handoff.md and
  docs/scoping/SOLAR_BULK_HANDOFF.json FIRST. Codex API session31389 completed;
  API RELEASED for Claude acceptance at18:10UTC, no new Codex Arctic jobs.
  Latest93,627posts/2,621trees/91,006pending (status18:06:19UTC).
  Claude takes sole archive
  ownership only after checking the handoff record and live collector processes.
  Claude owns new unreserved reads; subtract SOL040/SOL041 as well as all other
  reservations and coverage. Codex owns statistical integration/evaluation.
  Plan docs/2026-09-22-solar-same-evidence-evaluation-plan.md distinguishes
  exploratory reused data from a fresh test and case-predictive intervals from
  uncertainty about a population median. No claim of LLM superiority yet.
  Latest model state:024 COMPLETE576claims/233clocks;025 PREPARED620claims/
  359contributors/259clocks, NOT fitted. shared_journeys004 is preflight only
  (5journeys25irredundant observations), not a calibrated population posterior.
  Full50 occupancy fit001 remains live at last check; no new fit authorized by
  this documentation task. No new verification campaign, commits or deletions.

- Solar 2026-09-22 17:31 UTC: active goal, not complete. timing024 COMPLETE
  233/233 usable separate clocks,576 claims329 contributors374 registry.
  SOL036(9), SOL037(6 after four itemized root corrections), ROOT018(1 pending
  SF survey/install clock;3 trees36 comments) adopted, NOT024. Next batch waits
  for SOL038/LUNA039 live parsing; do not repeatedly refit unchanged tiny packets.
  Full50 structure fit001 LIVE agent solar_model_bridge_sol session6333:
  model_bridge/full_universe_successor001/forum_positive_anchor_candidate/;
  440 contexts4098 readings863 anchors4x500warmup1500draws,collapsed block4.
  Four new forum-positive existential cells, no new negatives. Historical2017–24
  availability only; unknown-identity positive anchors still unsupported.
  Evidence_v15/alignment_v16 bind024+county_instructions_v15_consolidated_adopted:
  35solar3historical11general1narrow3snippet1directory3nonsubstantive1unresolved.
  Yuba general .gov body adopted; Tuolumne blocked, no scope substitution.
  Root sole Arctic API session15816 comments90/pause7; last86,034posts2531trees
  60695treecomments. commentindex01062670unique22204overlap, never addcounts.
  Manual web016/017 seeded; root ROOT018 read newly capturedSF threads.
  Manifest585entries=582Reddit+3olderexternal; EXTERNAL00513professionalposts
  separately adopted descriptive-only. No numeric clocks/legal rules invented.
  Narrow timing bridge exact receipt route bug fixed (2 rows now reachable),
  bounded compile passed, no new joint fit. Oldbridge003FAILED remains frozen.
  NoCalFresh/synthetic/commits/deletions/full verification. Pending goal broad.

- Solar17:09UTC ACTIVEgoal. timing023COMPLETE235/235,563claims321contributors366registry.
  timing024LIVE32391:576claims329contributors374registry233clocks; addsSOL035+
  EXTERNAL004(6claims inclEric30daydesign/permitbound/3monthcontractPTO), eight
  source-scoped aliases map9claims; originalvalues/clockIDs preserved. Maincmd
  --clock-aliases parse/clock_aliases024_adopted.json opt-in; unreviewedIDs unchanged.
  SOL036adopted9datedclocks (saultenutzBayArea2022/23), NOT024; appendnextbatch.
  Evidence_v14/alignment_v15bindprepared024 +county_instructions_v14_consolidated_adopted;
  aliasesrecognizedinlossaccounting,event_yearslistskept,reportdatenotusedasera.
  Reviewedcoverage558unique=555Reddit+3oldexternal; EXTERNAL00460posts2pagesseparate,
  HOATalk30711750posts/99replies implies50unheld, nopublicpaginationroutefound.
  RootsoleArcticAPI2725discover64/pause4; completedcomments77812added75trees;
  latest85963posts2531trees60695comments.63registrycommunities,fuckHOAnew;
  refine+extend_historyadd2005–2026queries. NotInternetcomplete;1976heldtreesunread.
  ModelSolunknown-identityadapterDONEopt-in(1-u)w+u*q,18focusedchecks,noinputadoption
  orfit. Current/2026officialanchorscannotbackdate2017–24one-stateoccupancy;
  official_v13NOTRUN; bridge003FAILED1.010251, earlierbridge002fit004frozenPASS.
  Agentsfinishedboundedtasks; no pending synthetic/CalFreshwork. No commits/delete.

- Solar16:55UTC: REAL SOLAR active. 552distinctReddit trees read+3oldexternalroots;
  previous ROOT013 duplicated ROOT005 count corrected. 63communities (fuckHOAnew,
  HOAalreadyheld). Latestcompletedretrieval76494posts2456trees58871comments;
  commentindex00956216unique20132treeoverlap, neveraddcounts. RootsoleArcticAPI
  session26122national-list; pause4. timing023LIVE77780:563claims321contributors
  366registry235clocks;022COMPLETE485/275/318/196allpass. SOL035adopted7claims
  pendingnextbatch; external004Luna convertingfew-monthinterval/pendingHOA,
  no45daydeadline-as-observation. Evidence_v13/alignment_v14 bindprepared023
  andinstructions_v14_consolidated_adopted:35solar3historic10general1narrow
  3snippet1directory3nonsubstantive2unresolved(Tuolumne403,Yuba404).
  Jointbridge003FAILED Rhat1.010251; no retries/gatechanges. Earlierbridge002
  fit004passesonfrozen32obs, notallcurrentclaims. Officialv13structurecandidate
  NOTRUN temporal2017–24vs2026mismatch. Sol implementing opt-in source-independent
  unresolvedidentity mixture adapter, noautomaticuniform/pointerror. Do not
  resumeCalFresh/synthetic, commit/delete, orfullverification. Goalunfinished.

- Solar 16:21 UTC: timing021 COMPLETE176/176,441claims258contributors301registry.
  timing022 LIVE session62801:485claims275contributors318registry196clocks,
  adds new_clocks023_adopted,024_adopted,external_clocks003_adopted. Source/title
  and external003 own-body references supported; labor hours remain effort,
  Leia1979 alias17qsxwv; itemized adoption corrections preserved. Manifest445
  entries=442Reddit+3olderexternalroots; external00354posts5pages separately
  covered (TMC236853only1/24;other23pages403,notempty). ROOT013staff33comments
  typednotapplicant. Jointbridge003sampled,postprocessing/gatespending agentSol.
  Latest76428posts2396trees57798comments; rootAPIresolve_ties live, lastlisting
  finished83885. LunaSOL032 and SolSOL031 disjoint reservedreading. NoCalFresh,
  synthetic,commit,delete orfullverification. GoalACTIVE, notInternetcomplete.

- Solar16:02UTC: timing021 LIVE session46384,176clocks441claims258contributors;
  019completed165/165. Jointbridge003fit001 LIVE session78982 afterzero-drawCLI
  switchfailure preserved;39forum+7admin=46obs19programs70coords. ModelSolmonitoring
  singleproductionrun, noretries/extensions. All402outofsliceclaims routed.
  RootAPIseed18426(comment_batch_leads008), previouscommentindex4075finished.
  Latestacquisition67607posts2352trees56118comments; separatecommentindex008
  49680unique,17508overlap;72newpriorityparents. Manifest432entries=429Reddit+
  3external. SOL029new023adopted1clock NOT yet timing021; rootcosttable012image
  boundtranscription samecase d773ts (equipment/fees/creditdistinct).
  Flairrecovery002 reconciles258contributors,0newgeo;001onlypartial5OPs preserved.
  Renderer now includesauthor/topicflairforfuturetasks. SolSOL030next20reserved;
  Lunaindependentforums external003capturetask. NoCalFresh/synthetic/commits/delete.

- Latest Solar15:55UTC: completed timing019406claims/233contributors/274registry/
  165of165passing clocks. timing021 PREPARED441claims/258contributors/301registry/
  176clocks, NOT fitted. 020prepfailed unsupported thread-prefixedcommentlocator;
  baregloballyuniqueIDs corrected in012_reconciled, nofit020. Futurebase004:
  older12tnelt rig2dumbass merges143huic; March10 reportedsubmission→July10PTO
  supersedes40/54/64daypendingduplicates, distinctMarch27finaldocsclock retained.
  New022adopted25claims +ROOT01011claims (Temecula/LongBeach/unknown commenters).
  ROOT011 practitioner29comments typedseparately, notapplicant likelihood.
  Manifest429entries=426Reddit+3external; ROOT010 one linked image unreaddeclared.
  Evidence_v10/alignment_v10 bind completed019, v11 bind PREPARED021.
  Countyweights compiler corrected explicit unknownmass ignored withcandidates;
  threebounded checks pass; timinglikelihoodunchanged. Frozenolderoutputsintact.
  Registry62venuesincludesTemecula. Historicalfrontier extendedto2005 preserving
  pagecounters+oldfrontiers;7nationalpostfrontiersexhausted4paging, notallInternet.
  Acquisition67607posts/2352trees/56118comments. RootsoleAPIowner nowcommentindex
  sessionpending(lasttool); allotherretrievalsessionsfinished. SolSOL029reading
  d773ts/d778svcrosspost+1krnwno. ModelSol authorized ONE expanded bridge003fit
  onv11: samepriors4x(1000+2000),GH256check512, noretry/newcore/priorfixing.
  Must reportselectedinputbeforestart. NoCalFresh/synthetic/commits/deletions.

- Solar checkpoint 2026-09-22 15:43 UTC: goal ACTIVE. Completed timing017:
  351 claims, 212 timing contributors, 253 identities, 134/134 usable conditional
  clocks. Timing019 LIVE session17201: 406 claims, 233 contributors, 274 registry
  identities, 165 clocks; not completed yet. Draft018 INVALID_UNFITTED (Gaijin
  duplicate installation + capture metadata corrected during preparation).
  Future inputs use root_decisions_combined003 and new_clocks020_reconciled:
  Hayward Gaijin reports alias directly to 1ozqnan, initial vs corrected upload
  distinguished, repeated three-day corrected-upload timing counted once.
  Explicit post revision preserves archive bytes and adds updated OP by opt-in
  reference only. Read manifest422 entries =419 Reddit +3 older external roots.
  evidence_v9/source_alignment_v9 bind completed017 + instructions_v12: all351
  retained,102 county-weighted/249 no county weights;257 some unresolved mass.
  County instruction layer32 solar,3 historical,9 general,3 search snippets,
  1 directory,3 non-substantive,7 unresolved; not additional likelihood factors.
  Joint fit004 remains PASS on frozen32 observations (not all406), model frozen.
  Root exclusively owns Arctic API: seed session33660, pause4 after429; latest
  completed acquisition62627 posts/2317 trees/55176 comments. Registry61 venues,
  not all queried or Internet complete. Sol SOL028 reading next unread rich
  trees; Luna broader local web leads012; model Sol bounded joint-input proposal
  only. No synthetic/CalFresh work, commits, cleanup or audit campaign.

- Solar checkpoint 2026-09-22 15:12 UTC (supersedes runtime states below):
  timing016 COMPLETE: 330 claims, 204 timing contributors, 245 registry identities,
  124/124 passing separate conditional clock fits. SOL024 adds12 fully read trees
  (375 Reddit +3external roots); root_adopted_new_clocks018_adopted adds21 pending-
  next-input timings after one correction pass (future inspections not completed,
  pending design waits included, whole owner-delayed project retained).
  Joint bridge002 fit004_collapsed_q256 PASSED all predeclared numerical gates in
  398s: Rhat1.00647, minimum bulkESS1023, tailESS1393; 256->512 GH weightTV6.7e-5.
  It uses same frozen32 observations, 16phaseprograms,56 sharedcoordinates; all
  earlier failures preserved. Not fullcountygraph, intrinsiccapability, or proof
  source/context effects separately learned. FIT004_RESULT_REVIEW and static
  EVIDENCE_IDENTIFICATION_MAP document limitations. Model core frozen.
  Officialv8+v9 gapfills returned; v9 search-index quotations being distinguished
  from authored summaries before consolidation. Luna readingSOL025next20. Model
  Sol proposing scope-safe combined004 structure input, NO fit authorized yet.
  Root owns Arctic national-list session15058; completed74396 had59886posts,
  2242trees/51994comments. No otherAPI callers, commits, deletions, synthetic work.

- Live Solar checkpoint 2026-09-22 14:59 UTC: goal ACTIVE. Reading manifest363
  Reddit fulltrees (+3oldexternalroots). ROOT009/SOL021–023 add34 adopted timings;
  timing016 is LIVE session75501:330claims/204 timing contributors/245registry
  identities/124clocks, do not call completed until124 fit-summary entries.
  Model fit003 collapsed terminated BEFORE retained draws on missing-case
  coordinate sampler plumbing; preserved and documented FIT003_RUNTIME_FAILURE.
  Model Sol fixing only that branch + tinyactual-input sampler smoke, no prior
  change. No usable jointposterior yet. Collapsed mode correctly keeps Student-t4
  report kernel; Gaussian design note was wrong and superseded. Actual fixed-
  parameter256→512node maxLLdelta3.75e-5, not convergence/identification proof.
  Root owns Arctic discovery session74396; session9243 finished (59,803posts,
  2,242trees/51,994comments). Discovery fairness bugfixed: cumulative requestlog
  attempts across restarts, not reset counters starvinglater localvenues.
  Registry60venues; 7/11national listingfrontiers exhausted, notInternetcomplete.
  Sol readingSOL02412reserved IDs; Luna sixcounty officialgapfillv8. Parse rules
  at parse/SOLAR_PARSE_HANDOFF_RULES.md. No synthetic/CalFresh/commits/deletions.

- Runtime checkpoint 2026-09-22 14:38 UTC: timing015 COMPLETE, 108/108
  conditional clock fits numerically usable, 296 measurements, 183 timing
  contributors, 203 registry identities. Separate fits, not joint process draws.
  Evidence_v7/source_alignment_v7 bind that completed fit: 88 county-weighted,
  208 with no county weights, 212 with some unresolved geographic mass. All
  296 retained. Instruction consolidation: 58 attempts, 29 solar-specific,
  7 general, 3 non-substantive, 19 unresolved. Earlier versions preserved.
  Session57875 finished; canonical retrieval at that checkpoint 54,418 posts,
  2,202 full archive trees, 50,369 tree comments. Root now owns listing15
  session89044; enphase ordinary older-page returned zero after tie resolution.
  Queue_current12 building in session60263. No concurrent Arctic API callers.
  Sol parsing SOL021 next30, Luna venue-gap web search010. Model Sol implementing
  exact-collapse opt-in path plus bounded deterministic checks, NO production
  fit yet. Joint retry sequence stopped after two failures; this is a precise
  marginalization change, not a claim of statistical identification.

- Latest Solar checkpoint 2026-09-22 14:26 UTC: goal ACTIVE, not finished.
  Completed timing014:272 measurements/170 timing contributors/190 registry
  identities/100 passing conditional clock fits. Run015 LIVE with296/183/203/108
  respectively; wait for108 fit_summary entries before completion claim.
  Inputs add SOL02021timings and geographic recovery0013timings. Recovery fixes
  old138x5lh California-only exclusion; unknown geography retained, month-only
  intervals widened, installation duration only known completed-lower-bound.
  Read manifest now327 Reddit fullthreads (plus3 older external roots), while
  frozen queue_current11 has282. SOL019 adds15 read/no timings; explicit Orange
  and BayArea county clues corrected in019_geography_corrected successor.
  Canonical acquisition50,430posts/2,167trees/49,465treecomments;35treepass LIVE.
  Root alone owns ArcticAPI. Commentindex00743,858unique/11,786treeoverlap,
  all149prioritylead parents alreadyheld; listingtiesSolarbusiness/SunPower
  resolved but needordinaryolder queries before exhausted. No internetcompleteness.
  Jointbridge002fit002 FAILED as001 did: maxRhat1.0415/minESS161.5, likelihood
  precision passes butpredictionprecisionfails3.405%. RETRYSEQUENCESTOPPED,
  no further modelrun or agencycapabilityheadline. Agent resultreview saved.
  Officialgapfill recovered Marin/Monterey/Yolo via declared reader-service
  transformedcaptures, notrawpublisherPDFs. Instructions_v7_consolidated retains
  latest58attempts and supersededbindings; evidence_v6 building againstcompleted014.
  Newparsebatches allagents finished. No commits/deletion/synthetic/CalFreshwork.

- Solar checkpoint 2026-09-22 14:12 UTC: ACTIVE/UNFINISHED. Completed run013:
  252 timings, 154 timing-contributing installations, 174 registry identities,
  97/97 usable conditional-clock fits; not joint process draws. Evidence_v5 and
  alignment_v5 retain all252 (79 county-weighted,173 county-unresolved); v5's
  fit-state labels were captured mid-run, use final fit_summary for completion.
  Read manifest updated to282 Reddit full threads; ROOT008 adds6 unfitted timings
  and SOL01830threads/16staged measurements is getting one alias/scope correction.
  External0024timings now consumed, including idle/operating periods; tag receipt
  not PTOgrant. National NJOP thread supplied actual NorthernCalifornia commenter
  timeline; do not filter all comments by OPgeography or require nameddepartment.
  Canonical acquisition last38,489posts/2,132trees/48,390treecomments; latest
  35-tree pass running. Root exclusively owns ArcticAPI. One accidental extra
  acquisition root preserved; all6 unheldIDs seeded canonically. queue_current9
  INVALID, current10 valid, current11 generating against updated manifest.
  Bridge002fit001 FAILED Rhat1.0689/minESS59.9 and QMCprecision. Source/context
  contrast is nonidentified; do not quote failed posterior. fit002_joint_ess_qmc1024
  LIVE fixed4x(1000+2000),2workers, samepriors/data plus optional14coord ESSblock.
  Core frozen while running. Added sampler_joint_blocks.py,17focusedtests passed;
  archive includes module. No automaticextension or priorfixing. Userstill wants
  broad realSolar, not CalFresh/synthetic/commits/deletions. 41GiBfree; no bulkpayload.

- Solar checkpoint 2026-09-22 13:48 UTC: goal still ACTIVE/UNFINISHED. Completed
  timing012:228measurements/137contributors/153registryidentities/86passingclockfits.
  evidence_v4 and source_alignment_v4 preserveall228,68countyweighted (onepartial),
  160withoutcountyweights. Explicit soft priors override richer-but-stale packet
  locations; county weighted_readings now SUMweights, candidate_readings separate.
  queue_current8 records226Redditfullthreadsread; SOL017 adds24=250, currently
  correcting its stagedtiming011 for actualendpoints/aliases. Do not silently
  excludeunknowngeography or whole-processclaims. New009_adopted links luniz97
  usingroof+assessment chronology, supports years;010_adopted admitsweakgeography.
  Sharednormalizer supports days/completed_approximate/datedstart+censoredlower.
  Sourcecollection36,675posts,2,062trees at lastcompletedpass;35treejob live.
  Root exclusivelyownsArcticAPI; nationalcommentindex006 has40,050uniquecomments
  (7,772overlap withfulltrees);197priorityleads seeded. resolve_ties newfiniteAPI
  action fixesoverlapstallswithoutskippingequal-timestamp rows. NoInternetexhaustion.
  Externalcaptures002:9SolarPanelTalkroots/14pages/143partitionedposts, partial
  coverageexplicit; Luna parsingstagedexternal002. DIY403challenges notbypassed.
  ExistingV6 median factor reused; optional operation_location_design implemented
  (fixedprior,notlearnedscale; undeclaredtargetunchanged;11focusedtestspassed).
  joint_phase_bridge002/fit001 LIVE4chains1000warmup2000draws,2workers,QMC128,
  32obs=6admin+26forum,16phaseprograms,108coords. Actualthreadsourcegroups,
  soleownerprior. Bridge001 preservedunfitteddraft. Sourcevsunknowncovariates
  confounded; noagencycapability/fullprocessheadline. Keepmodelcorefrozenuntil
  fitfinishes. Analytic-single-phase rejectedindividuals beforefit; useQMC.
  Bulkmetadata180sattemptfailedwith0payload;44→42GiBfree. Noarchivepayload,
  commits,deletions,CalFreshorsyntheticwork. Seeupdateddocs forlimitations.

- Solar checkpoint 2026-09-22 13:20 UTC (supersedes counts below): run011 now
  COMPLETE, 79/79 numerically usable conditional-clock fits, 219 measurements,
  131 timing-contributing installations, 147 registered identities. Not a joint
  process posterior. evidence_v3 binds these plus all 58 county-guide attempts:
  26 solar-specific, 7 general, 3 non-substantive, 22 unresolved. It preserves
  62 county-weighted forum timings and 157 with unknown county; all 219 accounted
  in source_alignment_v3. Earlier county fits remain bound to evidence_v1.
  Latest acquisition 31,132 posts, 2,062 full trees, 44,863 tree comments;
  only 186 Reddit threads fully read as of queue_current7, SOL015 next16 in flight.
  Root owns API; national listing active. Do not infer exhaustion from registry
  coverage. Goal active: retrieval, parsing and unified county process model
  remain unfinished. No synthetic/CalFresh work or commits authorized.

- Solar active checkpoint 2026-09-22 13:02 UTC (supersedes older counts below):
  retrieval/parsing and unified county process model remain UNFINISHED; goal active.
  Latest completed forum timing run009:175measurements/107 TIMING-CONTRIBUTING
  installations/73 passing conditionalclockfits.123 is registry size, NOT fitted
  cases. Prior008 likewise145measurements/88contributors, not104; see packet
  TIMING_CASE_COUNT_CORRECTION.md. Run011 preparing/fitting219measurements/
  131contributors/79clocks; do not call complete before fit_summary reaches79.
  Run010 failed preparation (missing packet threads), no fit; use011. New007
  reconciled and008_adopted preserve originals, linkedjourneys and genuinebounds.
  Acquisition last completed pass31,111posts/2,027trees/43,215treecomments;
  registry57venues:11national,30local,16adjacent. Dynamic county/AHJ/utilitylexicons
  prioritize only; nationalOP geography never drops relevantcommenters.
  Readcounts are much smaller; queue_current7/manifest being refreshed.
  County methods/results:docs/2026-09-22-solar-county-model.md. Newcollapsed
  Gaussian admin timingcomponent fits9,531cells acrossfourphases, all pass.
  county_model/county_report001 gives58county/116phase rows; noobserved-AHJ
  estimate for10panel-emptycounties. This component uses noforumlikelihood yet.
  Legacy panel sampler had missinglog-Jacobian and conflictingelasticitypriors;
  preservedoldresults not validundertheirstatedpriors. Newcode avoidsboth.
  Training001's 'forward'flag is2022 but2023/24 also trained: INTERPOLATION only.
  Corrected through2021 forecast2022 n2051 logscoredelta -0.0103 vsbaseline,
  coverage97.4%; no superiority claim/tuning. Within-eraheldoutAHJs +.0783.
  Halfdayzero sensitivity shiftspermitlevels18–24%. Inspectioncolumn has
  source-endpointcontradiction; not silently equated withforuminspectionwait.
  Latest county evidence_v2_locationfix all175claims semanticallylinked;
 56countyweighted,119unknown retained; source_alignment_v2 preservesallroutes.
  Structure combined003 stillFAILED; no stepcount/capabilityheadline. HOA-only
  narratives must not generate11government-nondetectionopportunities.
  Root exclusively owns ArcticAPI; check live sessions/cooldown before retrieval.
  Officialcountyguide passes v1–v4 cover44targets; v5final14 in flight.
  Counts distinguish solar-specific/generalheld/failed sources, notallretrieved.

- Solar checkpoint 2026-09-22 12:10 UTC: full retrieval/parsing UNFINISHED.
  Packet runs/solar_forum_20260922/. All enumerated national posts now queue
  comments, without an OP keyword gate. 25,104 posts,1,917 archived trees,
  40,022 tree comments; 138 Reddit trees read,1,779 captured unread.
  Search registry53 communities (NOT all searched/exhausted); all40 concrete
  manual_web_leads006 now captured. Batch comment pages are partial
  windows and must not be counted as complete trees/read cases. Root owns
  Arctic Shift API, honors rate limits. Latest completed timing_combined008:
  145 observations,104 linked installations,62 numerical passes in existing
  conditional V6, NOT population burden/capability. combined003 structure fit
  FAILED Rhat1.01776/ESS334.6; no automatic extension, no step-count headline.
  Whole-thread manifest lives in queue_latest; dated queue_current5 snapshot
  is one new post earlier than acquisition. ROOT007/SOL009/SOL010_HOA are
  staged, NOT in latest fit. HOA-only narratives need their own action/scope
  representation, not eleven government-action absences. Preserve
  out-of-likelihood costs, professional accounts, weak contextual geography,
  pure planning stages and cross-thread aliases explicitly. New DataSF1,000
  text-filtered rows/Tesla aggregate are captured, NOT clean fitted cohorts.
  Main methods/progress: docs/2026-09-22-solar-forum-expansion-and-fit.md.

- Work order 2026-09-22: user has pivoted to **real Solar permitting**. This
  supersedes earlier CalFresh-only restrictions below. Collect broadly across
  national and California Reddit communities and other solar sources; retain
  California relevance inferred from utilities, local subreddits, city names,
  and episode context without requiring a named department. Relevance is not
  exact AHJ identity: keep weighted candidates and utility-scoped clocks.
  Parse commenters' separate journeys, not only thread authors. Reuse held
  evidence and actually feed it into Bayesian fits. No endless verification,
  no new synthetic work, no silent omission of eligible forum evidence.
  Working packet: runs/solar_forum_20260922/. Preserve previous fits and shared
  edits. No commit, deletion, outreach, or claim of complete internet coverage.

- Checkpoint 2026-09-21 17:46 UTC: CalFresh-only morning-audit response and
  bounded county-instruction inventory completed. Short results now includes
  omitted comparisons/coverage caveats and observed procedural-denial share.
  All58 distinct counties inventoried;34 locally bound sources (30 new,
  4 reused),20 uncaptured leads,1 Kern limited/directory lead,3 substantive
  source gaps (San Joaquin, Sonoma, Tehama). Local34 includes3 shared state
  forms (Modoc/Nevada/Sierra),1 Santa Barbara dynamic shell and partial pages:
  NOT34 complete independent guides or new fitted readings. Root's8 direct
  gap searches improved first-half coverage; no unbounded retry loop.
  Sol22-action crosswalk is proposal-only, preserving joint interview clock
  and instrument selection/dependence caveats. No fit/code/sampler changes,
  no full-suite/per-source verifier campaign. Supported-result SHA remains
  f55b46a7cf8cb8c3f4a320483c7efc6f63cee9b8484e863b3ed24278e54f0941.
  Packet README has counts/gaps and next ordinary reading pass. Do not wait
  for all blocked sources or start another broad audit; use substantive local
  sources, predeclare opportunity scope and keep date/template limits inline.
  No other-statute work, commit, deletion or outreach. All3 bounded agents done.

- Work order 2026-09-21 17:30 UTC: apply **CalFresh-only** parts of Claude's
  morning audit. Do not touch concealed carry, Solar or synthetic work. User
  explicitly asks NO large verification or reformatting digression. Short
  CalFresh result corrected for 10 counties with resolved nonadmin evidence,
  48 near-exchangeable admin-only profiles, 817 cells without resolved readings,
  omitted low-detection/earlier-loss comparisons, and 71.3% observed procedural
  denial share (not a repeat rate). Existing CalFresh fits already use collapsed
  hierarchy updates/block4; no global sampler change or refit needed now.
  Luna agents inventory existing official county guides first, fill accessible
  gaps in two alphabetic halves; Sol proposes source-backed one-act-one-actor
  crosswalk without editing frozen inputs or double-counting shared encounters.
  Packet: runs/process_structure_20260921/calfresh_county_guides_20260921/.
  Source/county/date/meaning check once; no broad test/verification queue.
  Copied documents are not independent; not-required is not absent; silence
  is not absence. Hold assumption-driven full fit pending this evidence pass.
  Preserve frozen result and targeted-evidence closeout bindings. No commit,
  deletion, agency outreach, broad forum queue, or new work on other statutes.

- Checkpoint 2026-09-21 17:02 UTC: targeted real-CalFresh evidence pass
  completed; full process/capability goal remains unfinished. New LA2024 study
  and SF2020 working-paper captures supply historical behavioral anchors,
  not a contemporary full event log. Native LA nested rounded-call multinomial
  calibration completed and independently replayed; exact Dirichlet mixture,
  no MCMC, no existing fit changed. Offered-line probability .5300 with iid
  90% [.5263,.5337], NOT interview completion/current-county probability.
  Native plan/result/source records under
  runs/process_structure_20260921/calfresh_targeted_evidence_20260921/.
  Sol qualified PASS; caveats clustering, Beta(2,1) any-call marginal induced
  by Dirichlet111, fixed transport shifts. Root caught final LA outcome's
  pending-at-day30 coding, SF2022 interview-waiver regime, QC period mismatch,
  CF18 initial-only scope. Legacy prior calfresh_018 creates a spurious12-day
  duration; flagged, not rewritten, not used by new calculation. Assumptions
  and exact missing data requirements documented in
  docs/2026-09-21-calfresh-targeted-evidence-and-assumptions.md.
  No new broad queue, synthetic/Solar work, Joint47 retry, county timing fit,
  outreach, commit or deletion. Product goal tool still reports historical
  BLOCKED status and cannot be resumed with update_goal; user's new scope
  authorization resolves that old choice blocker, not the scientific gaps.

- User authorization 2026-09-21 16:40 UTC: reopen **targeted real-CalFresh
  evidence collection** for case participation, action/phase timings, and
  workload/capability. First seek evidence; where public evidence cannot be
  found, state the missing evidence and proceed with explicit assumptions and
  sensitivity analysis. This supersedes the no-retrieval restriction for these
  gaps and resolves the prior scope-choice blocker below. It does not authorize
  broad forum queues, synthetic/Solar work, outreach/records requests, commits,
  or a Joint47 retry. Preserve frozen results and retain unknowns in the
  evidence-supported result; assumption-conditional outputs must be separate.
  Bounded Luna/Sol source discovery is running. Working record:
  docs/2026-09-21-calfresh-targeted-evidence-and-assumptions.md.

- Latest goal status 2026-09-21 13:02 UTC: **BLOCKED**, not complete.
  Third consecutive audit confirmed the same scope/evidence impasse; the goal
  tool returned blocked. Previous continuation was NO PROGRESS, not a verified
  live-job wait. The completed partial bundle is unchanged and all model jobs
  are terminal. Need user choice: reopen targeted evidence collection, authorize
  an explicitly assumption-driven full-model target, or accept the partial
  CalFresh result and move to CCW. No new authorization or new supporting
  evidence appeared in current state/shared log. Preserve the full goal; on an
  explicit user resume start a fresh blocker audit. Do not restart sampling or
  claim the supported-result bundle completes the joint process/capability goal.

- Goal continuation audit 2026-09-21 13:02 UTC: second consecutive turn with
  the same scientific scope/evidence blocker. Previous turn was PROGRESS
  (completed fits/analysis/result bundle), this continuation is NO PROGRESS
  toward the full model after revalidation. Current plan still prohibits new
  retrieval/queues; no user target/prior decision arrived. Shared S05/S07
  results contain no new real-CalFresh participation or step-timing evidence.
  Authoritative bundle still has all execution unresolved and no capability;
  process listing shows no live matching CalFresh fit/report jobs. Leave goal
  ACTIVE now; if the same blocker remains on the next goal turn and no safe
  meaningful work appears, the three-turn blocked threshold will be met.

- Latest checkpoint 2026-09-21 13:00 UTC: real CalFresh full goal remains
  ACTIVE/unfinished, now awaiting a scientific scope decision rather than
  another fit. Supported result generated at calfresh_phase5/supported_result_v1
  (result SHA f55b46a7cf8cb8c3f4a320483c7efc6f63cee9b8484e863b3ed24278e54f0941):
  all9 conditions,1160 county/action rows,522 actor-count rows, original aligned
  draws, current7 clock families incl failed main decision,30 source-scoped
  requirements,3 selected-positive repeat sensitivities,observed CF296 shares.
  No missing burden filled with zero, no new posterior over unobserved paths,
  no county capability or ranking. Applicant-facing universe is9 applicant-only
  plus1 joint, not20 required steps. First full-goal blocking turn: current
  no-new-retrieval/scope prevents learning missing participation/operation clocks;
  async user question offers targeted evidence (recommended), explicit prior-
  driven full-model sensitivities, or CalFresh partial closeout then CCW. Do not
  choose a new target, restart fits/queues, or mark the goal complete without
  resolving that decision. Goal tool not marked blocked (three-turn threshold
  not reached). All fitting jobs/analyses finished; no live root model sessions.
  Last read-only synthetic watch12:30UTC selectedS03 counts complete with2FAIL,
  full corpus incomplete; next hourly watch due13:30UTC, no synthetic launch.
  Short handoff: docs/2026-09-21-calfresh-process-results-and-next-decision.md.
  No commit/deletion; disk51GiB free at12:49UTC. Agents idle after bounded work.

- Current checkpoint 2026-09-21 12:30 UTC: real CalFresh goal remains ACTIVE
  and unfinished. Both normalized receipt-implies-filing fits and analysis are
  terminal PASS; no retry or hard anchors. Max R-hat 1.0072, min bulk ESS 1023.
  Same eight-account/153-cell development Brier improves slightly to
  .07213–.07220 from .07257–.07266 but still loses pooled baseline .06066.
  No selected winner or fresh-validation claim. All joint support violations
  zero by declared assumption, not empirical recovery; filing-absent mass
  .023%/.131% retained. County effects only 9.1–9.2% mean marginal variance
  contraction, no agency-capability claim. Results in
  calfresh_phase2/logical_support_development/analysis; frozen methods unchanged.
  Full tests 2362 PASS, 106 seconds. Next is supported step-level result
  assembly and a precise scientific completion-gap assessment, not another
  fit/verification queue. Luna handles existing metadata/clock crosswalks;
  Sol assesses the smallest defensible remaining integration. No retrieval,
  new forum queue, Joint47 retry, synthetic/Solar work or county timing fit.

- Current checkpoint 2026-09-21 12:12 UTC: CalFresh goal ACTIVE/unfinished.
  Seven original20-action conditions now have completed mass-preserving
  calfresh_phase5 compatibility report: all draws retained, all executions and
  burden undefined, not zero. Root replay43bindings/class masses. Narrow
  receipt=>filing normalized logical support implemented OPT-IN/default unchanged;
  independent target/integration review PASS, fullsuite2362PASS106seconds.
  No58filinganchors, no universalfiling, no post-hoc pruning. Methodsdoc
  docs/2026-09-21-calfresh-logical-support.md predeclares2developmentconditions
  Beta22 adminFP.02/.10,4chain2000warm6000drawseed2026092108, no retries/waivers.
  TwofitsLAUNCHED12:15UTCsession81017; frozenplan c869bc38f2f823ec7ef864f086108b4ef46adadd1e4ee8d01e4b3a545addc685.
  Sol prepares terminal analysis incl SAME8account153cell dev comparison;
  constrainedjointpredictionusesalignedjointzMC, notproductq.
  NewCF296branchreview rootreplayed406values/58rows/currentheaders/4PDFquotes;
  metadataoldcellnumbererrorscorrected+archived; no branchposterior/additional
  factors/routeweights. July2025dispositioncohort is not futurefilingrisk.
  Prior2330PASS/adminresult details below. Disk54GiBfree; no cleanup.

- Current checkpoint 2026-09-21 11:55 UTC: CalFresh goal ACTIVE/unfinished.
  Fresh8-account/153-cell developmental mention test losesbaseline again:
  Brier .06066baseline vs .07762base/.06778low/.10461highdetector; allretained,
  no refit/selection. Statusmonitoring badcountycontrast drives45% excessloss.
  Artifact calfresh_phase3/fresh_episode_prediction sealedbeforeprediction.
  Source-scoped stringency30facts adopted9held,100cells, no scalar/fittedscore.
  July2025CF296 PartAexcludesrecerts/includesnewreapps (matchesinitialepisode,
  NOTfirstever);174softpositiveoperationalreadings=3actions x58countiesadded,
  noanchors/countpseudo-replication/adminnegatives.4predeclaredadminpriors
  ALLPASS maxRhat1.0063/minESS838;3supportedactions q>.982 inallcounties,
  Alamedaavailabletypes8.20–8.28 vs3.71withoutadmin. Countywhitecontraction
  only9–10%;~8%filingabsentstatesretained; no executableburden/capability.
  Fits calfresh_phase2/admin_operational_detection_development; sourceinput
  calfresh_phase1/admin_operational_adopted. No retries/newtimingfit/retrieval/
  descriptionqueue/Solar/synthesis/Joint47retry. Newcompatibilityhelperpreserves
  allunmappedmass/undefinedburden; latestfull2330PASS in96seconds.
  Adminprediction on SAME8accounts improvesBrier .07762 to .07257–.07266,
  still losespooledbaseline .06066; reuseddevelopment, notfreshvalidation,
  no labelchanges orconditionselection. Results underadminfitdirectory/
  reused_account_development.11:33UTCstatuswatch selectedS03counts245/245with2FAIL,
  wholecorpusincomplete; no syntheticlaunch. Currentdocfirstpasshasdetails.

- Current checkpoint 2026-09-21 11:12 UTC: full CalFresh goal ACTIVE/unfinished.
  Expanded20initial-actions input adopted439readings87positive352nondetect,
  one ambiguouscell excluded, original15rows unchanged; root2overlays consumed.
  Fourfrozen fits completed ALL numericalPASS (prioronly,Beta22/14/41forum),
  maxRhat1.0065/minbulkESS1030. Alameda meanavailabletypes3.71/6.81/1.92,
  notrequiredsteps orcapability. Basecountywhitecontraction12.9%, identities
  max2.1–13.9%. Fits calfresh_phase2/expanded_twenty_actions; exactreplay and
  identification expanded_twenty_analysis. First invocation failed BEFOREfit
  on historicalcodebinding; preserved/fixed archivedresolution, unchangeddata/
  settings/seeds. Poolingdevelopmentterminal8/10strongerPASS1/10weakerPASS,
  bothaggregatesnull, no retry/waiver/winner. Fullgoal stillNOTcomplete.
  Next: rootreviewalready-staged005–007 ONLY (no newqueue), freshcasepredictive
  helper withsharedunknowncounty, source-scoped stringencymetadata corrections,
  positive CF296countyrecords operationalaction-support check (not hardanchors,
  newtimingfit or administrativecountyhierarchyextension). Currentfit inputs
  frozen. No retrieval/Solar/synthetic work/Joint47retry. Fulltestlatest2284PASS
  pluslater42focused; newfulltests running. Mainfirstpassdoc hascurrentresults.

- Current checkpoint 2026-09-21 10:50 UTC: full CalFresh goal ACTIVE,
  unfinished. Opt-in logit source-detection partial pooling added; default
  independent-Beta seeded replay exact. Frozen two-setting x ten already-seen
  county DEVELOPMENT comparison running calfresh_phase3/detection_pooling_development;
  stronger setting8PASS2FAIL, weaker started with a failure too. No retries,
  waived gates, selected winner or fresh-validation claim. Methods in
  docs/2026-09-21-detection-pooling-development.md. Saved-draw diagnosis rules
  out marginal-product bug as staff-loss cause. Original heldout predictions
  replay exactly with archived modules (new frozen-code receipt; old unchanged).
  Full tests2284PASS; later forum/subset30PASS. V6 linked-draw burden aggregator
  tested, diagnostic-only/no real complete burden fit. Expanded20-action
  adoption same18episodes+5docs in progress, with unresolved cells omitted,
  original15pilot untouched. No new retrieval/descriptive queues/synthetic work,
  Solar work, administrative county hierarchy extension or Joint47 retry.

- Current checkpoint 2026-09-21 10:20 UTC: CalFresh goal remains ACTIVE,
  no complete joint burden posterior. Count-only completed-positive repeat
  factor now integrated into V6, optional/default unchanged; independently
  reviewed, no q/case/duration/visit leakage. One deduplicated 1uqglol K=3
  paperwork-redo report yields Beta(4,4) from Beta(2,3) at zero severity tilt;
  r mean .50,95% [.184,.816]. All0/log2/log10 fixed severity sensitivities
  retained; exact quadrature and IID draws in repeat_blocks_phase4/
  positive_count_component_v1. It is NOT assigned to correct_information,
  not population rework risk or county capability. Root integration review
  has receipts. Step-burden utility independently PASS; no real fit claim.
  Optional reviewed fixed-subset checklist support prevents unread added
  actions becoming nondetections; lineage byte-binding gap independently
  found/fixed. Old frozen fits replay archived code, not current source.
  Next: same18 adopted episodes +5 local docs four additional function review,
  especially generic status followup missing from15 pilot; executable
  semantics review and saved-draw source-loss diagnosis. No new queues,
  retrieval, synthetic work, Solar work or Joint47 retry.

- Current checkpoint 2026-09-21 09:55 UTC: CalFresh goal ACTIVE/unfinished.
  Ten mixed-source county-heldout folds COMPLETE, all numerical PASS,529sec.
  Occupancy loses source-type mention baseline: Brier.14646 vs.11848;
  ignoring-type baseline.16315. This tests210 source mentions/14groups/10counties,
  NOT latent step truth; noLLMbaseline. All8 unknowncountyepisodes excluded whole
  in everyfold(no candidate renormalization). Exactarchive+rootreplay in
  calfresh_phase3/mixed_source_prediction; frozen experiment nowterminal.
  Four claimant histories/five timingfacets overlap adoptedoccupancy+Joint47;
  43cases/56facets registry-disjoint, notproofpersonindependence. 1k7qx6o is
  follow-up alias1k4thai. These clocksarecoarsephases,not individualactiontimes.
  evidence_partition_preflight.json/md hasreceipts; noexclusion/refitperformed.
  Inventorybridge many-to-one mapping/replay tested27PASS, moduleoptional.
  New step_burden.py underSolreview: linkedV6draw conditionalmeans, unknownsnull,
  onlyserialclockattribution. Notreleasedtable/notrealjointburdenfit.
  Lunas finish localfederalcrosswalk/actionunionadoptiondraft/countsourcefields;
  no newretrieval/forumqueues/synthetic/Solarfit/Joint47retry.

- Current checkpoint 2026-09-21 09:30 UTC: real CalFresh goal ACTIVE, no retrieval
  or synthetic work. Corrected mixed-source six conditions COMPLETE, all
  numerical PASS (max Rhat1.0083/min bulkESS680); no scientific release.
  Results calfresh_phase2/mixed_sources_corrected; archived exact inputs/code.
  Two unsaved all_forum attempts lost at JSON NumPy-bool serialization, repaired
  only output path with original statistical code/seeds; original receipts kept.
  Production support-report bool fixed after terminal completion; strict test
  passes. Frozen experiment code no longer equals current code; use archive.
  Source-prior sensitivity substantial: Alameda mean available action types
  3.36 vs8.48 under high/low forum detection (15-action universe). Unknown county
  identities remain diffuse, max base probability2.8–10.5%, no hard assignment.
  Next: conservative county-heldout source-mention checks; action union/count
  adoption; reviewed executable route/participation/evidence partition into V6.
  Joint-inventory bridge optional, independently target/runner tested; upstream
  replay and empirical support diagnostics added; many-to-one mapping review
  pending. No real joint burden fit, no intrinsic-capability claim. Full tests
  2111 PASS before latest bridge/serializer tests. New 71 runner/bridge and20
  identity/forum tests PASS. Later forum005–007 remain staging,120threads fitted.
  All13 enriched-only count pointers resolved; duplicate1uqglol paperwork
  claims must become ONE factor; pending consuming root count adoption.
  Full current context/results in docs/2026-09-21-process-structure-first-pass.md.

- Current checkpoint 2026-09-21 09:10 UTC: full CalFresh goal remains ACTIVE.
  Root still owns real CalFresh first; no retrieval or synthetic work. See top
  of docs/2026-09-21-process-structure-first-pass.md. First county pilot and
  heldout source-mention results below are preserved, with 38-file exact archive.
  Optional shared categorical county identity is implemented/independently
  exact-enumeration tested; one identity per complete episode, all58 candidates
  for unknown CalFresh counties, no borrowed commenter/subreddit hard labels.
  Uniform action reviews have228/945 threads in staging, but only first120
  selected threads are root-adopted. Full19-episode independent audit caught
  missed root-author comments and a lifecycle mismatch. Corrected consuming
  forum_root_adoption.json has18episodes (10known8unknown),44positives/270rows.
  Combined county+forum evidence330rows (77positive253nondetected),0truth anchors.
  Original mixed_sources experiment STOPPED during condition3, two completed
  numericalPASS outputs retained as diagnostics, exact code/evidence archived.
  Corrected same-six-condition experiment running mixed_sources_corrected;
  occupancy/forum/identity code and phase1 adopted inputs are frozen until done.
  New joint_inventory_prior.py optional V6 bridge preserves full cross-program
  structural support, downstream feedback explicit, default unchanged. 59
  joint-prior/trace/repeat tests PASS; independent review in progress. No real
  occupancy-to-V6 burden fit yet. Eight proposed scope additions/39 stringency
  facts/68count reviews are candidates, not automatically admitted. Follow root
  correction overlays that code actually consumes, not stale worker labels.

- Latest checkpoint 2026-09-21 08:30 UTC: user explicitly asked overnight
  persistence; ACTIVE goal is full CalFresh end-to-end Bayesian process model,
  including structure/agency learning. Real CalFresh first; no new retrieval,
  no root synthetic generation, no Joint47 retry. Actual first occupancy pilot
  finished: calfresh_phase2 has 8 predeclared conditions, 7 numerical PASS,
  narrow county-scale ESS386.7 FAIL (not retried/waived). Four counties, 15
  bounded initial-decision action types, 5 captured docs collapsed to4groups,
  33positive+27nondetection cells; zero repeated independent readings/anchors.
  Large prior sensitivity (Sacramento mean2.73–9.27 across detection priors).
  Four-fold source-mention prediction calfresh_phase3 allPASS, but occupancy
  Brier .295 loses to source-type Beta baseline .211. This is NOT latent
  presence recovery, complete inventory, county ranking, agency capability,
  LLM comparison, or scientific release. Optional collapsed hierarchy update
  in occupancy.py preserves target/default augmented kernel, independently
  Sol-reviewed, enumeration/quadrature tests; ~8–10 seconds per real fit.
  Frozen pilot inputs/scope must not be edited under saved manifests.
  Uniform forum occupancy frame945 established; first12 read yields3knowncounty
  initialepisodes and1unresolvedcounty, staging only. Sol ranks13–48 andLuna
  ranks49–84 in progress. Count68 provisional crosswalk rejected byroot for
  genericcontact/renewal mislabels; Luna correcting withsourcecontext, nofit.
  Expandedinitialactions17 candidates preserved separately, not yetcanonical.
  Read docs/2026-09-21-process-structure-first-pass.md top checkpoint for
  exact results, methods, limitations and remaining work. Historical entries
  below describe earlier states and do not override this checkpoint.

- Latest checkpoint 2026-09-21 07:36 UTC: continuing the process-structure
  first pass, no new retrieval or root synthetic generation. Joint47 final
  attempt AND postfit are complete: equal-weight numerical PASS; both 90/10
  path sensitivities precision-probe FAIL. No further attempt. Postfit root
  review lives in calfresh_joint47_collapsed_analysis_v1/root_review.md; all
  66 analysis bindings checked. The former 47-file live freeze is released,
  archived results/inputs preserved. Ambiguous case paths remain ambiguous;
  no agency-capability or population-burden claim. New structure validation
  helpers have outcome-independent jurisdiction splits, separate label-only
  versus unseen-jurisdiction holdouts, declared-lineage leakage protection,
  same-cell baselines, proper Brier/log scores. Sol independently reviewed
  these and consumed-byte CLI binding fixes; manifests remain in the same
  occupancy_phase2/review packet. Full tests 2017 PASS before four new alias
  regressions; current focused suite 51 PASS. CalFresh count adapter now
  preserves all 68 claim-scoped facts and their identities/context/mechanisms;
  none silently admitted as repeated actions. CF reading scopes are proposals,
  not an adopted nondetection denominator. CCW Phase1 is under final source,
  identity/dependence review and canonical alias reconciliation; raw activity
  IDs are not canonical steps. Zero Codex real occupancy fits. Claude's Solar
  occupancy report fails its convergence gate; not validated recovery. Shared
  burden-table schema confirmation requested in scoping log, still pending.
  Read docs/2026-09-21-process-structure-first-pass.md for current limits/gates.

- Current work order 2026-09-21 07:04 UTC: user asked to review and implement
  `docs/2026-09-21-process-structure-posterior-plan.md`, then twice said continue.
  Root accepted its process-posterior direction with statistical corrections in
  `docs/2026-09-21-process-structure-first-pass.md`. This SUPERSEDES the county
  hierarchy/CF18 extension below. No real county-scale importance run occurred.
  Scope now real CalFresh + CCW phases1–5, Solar/synthetics with Claude, no new
  corpus retrieval. Finish current Joint47 once and postfit, then no eighth
  attempt. FirstconditionPASS; second executionFAILED at06:55 numericalprobe;
  third running. Keep all47bindings frozen throughpostfit. New unimported
  process_structure package has logistic occupancy hierarchy, imperfect source
  detection, jointcountdraws and proposed typedburdentable. Not realfit/validated.
  Existing V6 already supports independent multiple repeatblocks; regression
  confirms, no corepatch. Fullrepositorysuite1994PASS atthischeckpoint.
  Sol workershitusage limits; Luna CalFresh/CCW Phase1 nowprepare candidate
  unions and detectionopportunities, Sol independentmodelreview continues.
  Onepacket perphase/family under runs/process_structure_20260921; no successor
  sprawl. Missing source≠nondetection≠absence; samecase/copydedup mandatory.
  No automaticrelease fromconvergence; sourcecalibration/heldoutchecks pending.

- User priority addendum 2026-09-21 06:20 UTC: prioritize full Bayesian
  statistical learning of agency capability and process structure/step counts,
  within real CalFresh first. Continue live collapsed Joint47 unchanged, but do
  not equate timing convergence with completion. Sol tracks are now count
  evidence inputs, ordinary-application structure/county differences, and an
  audit of county learning from the accepted administrative ridge fit. Further
  descriptive-summary expansion is lower priority. New consolidated audit
  handoff: `docs/2026-09-20-progress-and-remaining-work.md`. Structure/count and
  intrinsic-capability posteriors remain unvalidated. Official web context for
  county variation in that note is NOT added to frozen model inputs.

- Current checkpoint 2026-09-21 06:02 UTC: ACTUAL Joint47 collapsed MCMC is
  running, session62389/PID42245, launched05:57:48 UTC. Four chains each have
  2500 warmup and6000 retained draws; allthree original path sensitivities run
  once. Plan `calfresh_joint47_collapsed_runner_v1/plan.json` SHA
  bbe657c548305aedd52fbbe19e30f98eabad6e7f32f4643c8ac3d76675b0b7b0.
  All47 planbindings are FROZEN throughfits andpostfit analysis; no restart or
  automaticextension. Backendperf_v8 changesintegration only, notscientifictarget.
  Current source-use entrypoint is now
  `runs/three_family_20260920/calfresh_forum_source_use_interview_access_successor_v2/consumer_entrypoint.json`
  SHA031cc84535f83a130470507ab2c307e8ea05bc2acc1b9853cd4a966ce9f5d42e.
  Root54bindingsPASS, all151previoususerecordspreserved, all187queuestatesunchanged.
  284descriptive refs,118componentrecords,100linkedthreads,167openuses. Nine
  additional event chronologies/19constraints are descriptive, notnewlikelihoods.
  All945 reviewed stilldoesNOTcompleteintegration. CalFreshfirst,otherfamilies
  deferred. W2poll05:37:55UTC unchangedincomplete;next06:37:55UTC.

- Current checkpoint 2026-09-21 05:29 UTC (supersedes historical entries below):
  CalFresh first; all 945 captured threads have review/disposition receipts,
  but forum integration is NOT complete. Authoritative source-use entrypoint:
  `runs/three_family_20260920/calfresh_forum_source_use_office_travel_successor_v1/consumer_entrypoint.json`
  SHA cae60b4c1dbc31b8a1a4c2342a1359facf329221ec4d0e8cef3bb73604a6940b.
  Current counts: 100 source-linked threads in attempted/fitted components,
  118 component records, 271 descriptive claim references, 220 structural
  references, 167 open supported uses. These are different denominators and
  include numerical failures; do not claim 100 independent usable cases.
  The administrative fit still contains ZERO forum factors. Separate forum
  timing analyses are selected-report estimates, not statewide total burden.
  Missing department names or matched administrative statistics are NOT blanket
  exclusion gates. Reading a thread or using one claim does not close its other
  supported uses. Keep actual consumption and numerical usability explicit.
  Joint47 original and repaired runs each failed all three conditions. Repair
  comparison is complete (48 exact likelihood replays); source freeze released,
  archived sources immutable, no automatic extension or queue closure.
  Remaining work: integrate reviewed evidence, fix the joint sampler through
  same-target case marginalization, and resolve specific interpretation holds.
  Do not restart all-thread verification or resume other statutes/synthesis.

- Current-use promotion 2026-09-21 04:54 UTC: adopted complete reason-refresh
  successor `runs/three_family_20260920/calfresh_forum_source_use_reason_refresh_successor_v1/consumer_entrypoint.json`
  SHA c2c414ecfdcd3dc3ad164c1a5511f98aa9e37347e1d043d8653da5569dee899f.
  Root replayed 73 bindings and all 187 queue rows; only q002's stale compiler
  reason changed, preserving its historical reason and genuine hold-stage
  ambiguity. All 148 use records unchanged; 100 linked threads, 118 component
  records, 268 descriptive refs, 220 structural refs and 170 open uses remain.
  All 945 reviewed does NOT mean all supported evidence integrated. Named
  department or matched administrative statistic is NOT an admission gate.
  Joint47 repair first TWO conditions failed; third runs under the same frozen
  29-file closure, session22548/PID82927. No restarts or automatic extensions.
  Isolated 4D marginal evaluator preserves the original correlated prior,
  47 cases/49 groups/74 paths; modest fixed probes pass refinement, but broad
  prior stress/performance and independent review remain. No marginal MCMC yet.
  Root47 prior-free event bounds independently checked by LP: 74/74 path bounds,
  all47 lower-median envelope [9,infinity] days; source-report envelope, not a
  population or posterior claim. CalFresh remains first; goal active.

- Current-use promotion 2026-09-21 04:36 UTC: adopted complete benefit-bounds
  successor `runs/three_family_20260920/calfresh_forum_source_use_benefit_bounds_successor_v1/consumer_entrypoint.json`
  SHA5ffd94f1224ad5b01ec07a9e59f63d69e7f926fa67193434b1fadb5ae02319fe.
  Root70bindingsPASS/all187 oldqueuefields/all139 previoususerecords unchanged.
  Descriptive union268 (was259), 9records/8cases; modelcounts unchanged118records,
  100linkedthreads/29conditions/432rows;170uses remainopen. Full33-file map.
  Joint47repair secondcondition stillrunning PID82927; firstFAIL preserved;
  frozen29sourcefiles stilluntouched. Numerical prototypesv2 andbridgev2 isolated,
  notproductionapproved. Root47case observed-event analysis executed, independently
  underreview: totalclock lower-median envelope[9,infinity], only12finiteupper
  bounds; not a posterior/population result or new observation. Goal staysactive.

- 2026-09-21 04:28 UTC continuation: CalFresh stays first. Live joint47 repair
  launcher PID82927/session22548 confirmed; first condition terminal FAIL at
  04:15 (LL Rhat1.065, ESS49; spread Rhat1.057, ESS61), second runs unchanged.
  Do NOT restart or edit its frozen29-file closure through all3fits/analysis.
  Root adopted calfresh_benefit_disruption_observed_bounds_v1 as DESCRIPTIVE:
  eight cases/nine clockrecords, four clocks/two scopes,32 boundrows independently
  recomputed,17bindingsPASS. Pending can never resolve; q049/q050 onecase;
  q013 contact-chasing17–18days, q066 unknownstate. No fit/queue closures.
  Current-use successor adding descriptive links is in prep; phone35 remains
  authoritative100linkedthreads/118records/170openuses. No +9 assumption.
  Root exact-ratio support prototype calfresh_joint_ratio_support_v1 passed8
  tests incl12,000 membership probes and a thin interval missed by the earlier
  grid. Sol builds isolated marginalization v2 and same-target group/prior bridge;
  no livecore or realfit changes. Original partial prototype cc31c23b retained.
  Topology audit:47cases/49groups; two multi-groupcases,26 need path/absence
  composition; zero production approval. Disk20GiB04:27, no cleanup authority.
  W2 read-only monitor next04:35:56UTC. Goal active; all945 supported-use gate open.

- Latest current-use promotion (2026-09-21): Phone35 complete successor is adopted.
  Use `runs/three_family_20260920/calfresh_forum_source_use_phone35_successor_v1/consumer_entrypoint.json`
  (SHA e91f8c2508dec242447125263ac620c51703f53629333f6b12d7924f7ee51ee6).
  Root checked 69 bindings and all 187 queue states; only q018/q116 newly close.
  Current: 118 component records, 100 source-linked threads, 170 open uses,
  29 conditions, 432 condition-factor rows; 259 descriptive refs / 220 graph refs.
  These are different denominators, not independent people. Joint47 repair
  session22548/PID82927 still runs; keep its 29-file live source closure frozen.
  Benefit7 membership addendum is prepared, not a fit: four California cases
  have context-inferred benefit channel, two commenters have unknown state,
  one explicitly says CalFresh/CA. Do not impose a literal-word gate or borrow
  another author's state. Membership assumptions and pooling remain unresolved.
  All945 supported-use requirement remains open; CalFresh first, goal active.

- 2026-09-21 03:58 UTC: ACTUAL same-targetjoint47repair RUNNING session22548,
  launcherPID82927,started03:51:39UTC. Currentcondition50/50 chains1/2 reached
  1700/1800iterations; do NOTrestart. Packetcalfresh_joint47_sampler_repair_v1,
  finalplan2082c0a7a6387aa968957586fa7aeb0be9bfcaf028986bf08e3a290ba6a87395,
  auth e098fd75a873cb93dda2cde363fa9070433601270c2d0ed6f5b2ad949b42396d.
  NEW29fileliveclosure FROZEN throughall3fitsandanalyses. Original3failures+
  bothanalyses DONE;48savedLLreplayedexactunderoldandnewcore. Combinedpatch
  APPLIED,1940testsPASS79.92s; onelegacyhash test correctedonlyfornewdefault
  metadata, originaldigestretained. See calfresh_integration_patch_v1/root_adoption.md.
  Phone35live ACTUALLYdone4/4PASS session6144closed; mixedmedian149.73min
  [118.55,190.54],rootadopted calfresh_phone35_live_v1/root_adoption.md. Onlyq018/
  q116timingusesnoweligibleclose; globalregistersuccessorbeingbuilt, current
  consolidated172untilpromotion. No population/successfulcontact/activehoursclaim.
  Repairpostfitwrappercalfresh_joint47_sampler_repair_analysis_v1 frozeninert,
  plan6f70248e...,analyzerf05a9d8a...; requiresall3terminalmanifests+rootauth.
  Benefit7candidate3clockinputpreparedNOTfit; rootfoundq066programmembership
  uncertainty(commenterdoesnotnameCalifornia;rootauthorisNOTsamecase),Solchecks
  ONLY7candidatecases/sourceoverlap. Do notborrowrootcounty/state. Uncertain
  programme scope differs from missinginternaldepartment; no blanketforumgate.
  SolarPGID80419sixmembersstillpaused03:50. Disk24GiB03:43, nodeletionauthorized.
  W2next04:35:56UTC. CalFreshfirst; otherfamiliesdeferred;goalactive.

- 2026-09-21 03:43 UTC addendum: corrected baseanalysis finished (session94176
  exit0),48savedLLreplays exact; all3 originalnumericalFAIL preserved. Mixture
  analysis ACTUALLY RUNNING session34865, firstconditionchain1 reported. Keep
  livecorefrozen untilitfinishes. Rootreviewedcombined37bindings and math/runner
  composition, but patchNOTapplied. Combinedpatch7475bea8...,manifest8e5f3bd9...
  Same-targetrepair preparation now manifest44f07307...; exactconditionkeySET
  guard corrected (JSONobjectorderisnotexperimentalorder),5testsPASS. No prepare
  ornewfit. Next: finishmixture,applycombinedwithapply_patch,run`pytest tests -q`,
  freshphone35compile/fits andguardedfixed-budgetrepair. Current172usesremain.

- 2026-09-21 03:38 UTC: all945-thread supported-use completion gate STILL OPEN.
  Current consumer is `runs/three_family_20260920/calfresh_forum_source_use_renewal8_successor_v1/consumer_entrypoint.json`
  (SHA37c1260b81b53023050379e780cf5c963fe9a883e97eb402993f467ccef00d62).
  Root replayed65bindings and all187queue states; ONLYq072 newly closes.
  172openuses,99fittedsource threads,116componentrecords;259descriptiveclaim refs,
  preserved220structuralclaims. Threads/cases/factors/descriptions differ.
  q114 native>1month NOT30daybound; q145 pendingprocessing NOTfirstresponse.
  Effective semantic overrides supersede historical routing details. Adminfit
  still0forums; unknown department/admin-match are NOT admission gates.
  Originaljoint47 session77247 CLOSED03:30; all3conditions numericalFAIL.
  Keep29livecodefiles frozen until baseANDmixture analyses complete. Baseanalysis
  stopped before draws on tuple/list Config equality; Sol repairing representation
  check with originals preserved. Combinedneutralbound/sampler/initialization patch
  isolatedonly,303testsPASS; NOTlive. No numerical improvement claimed.
  Phone35sourceadopted andshadowcompilePASS, NOTproductionfit. Same-targetrepair
  launchguard prepared, NOTexecuted. No automaticextension or relaxedgates.
  W2readonlypoll03:35:56UTC:selectedS03countscomplete2fails,wholecorpusincomplete;
  next04:35:56UTC. CalFreshfirst, Solar/CCW/synthetics deferred. Goalactive.

- 2026-09-21 03:07 UTC: DO NOT LOSE the all945-thread supported-use completion
  gate. All captured threads have review records; inference integration remains
  unfinished. Current source-use entrypoint is now
  `runs/three_family_20260920/calfresh_forum_source_use_sar11_successor_v1/consumer_entrypoint.json`
  (SHA21056d94da1c3fd5041aad40a3b0106e6918a2e615a2daaaedd3cdb687e28458).
  Root adopted after checking 64 file bindings and corrected queue semantics.
  SAR11 replaces SAR10, all four inherited conditions PASS:116 component records,
  99 linked captured threads,173 open uses; onlyq067 newly closes. These are
  different denominators, not people. Admin fit still0forums; no named-department
  or matched-admin admission gate. Joint47 session77247/PID32996 continues:
  first50/50 condition FAILED convergence; second condition running at03:05.
  All29 live source files MUST remain frozen through all3 terminal conditions
  AND their base/mixture analyses. Preserve failures; no automatic extension.
  Neutral-bound compiler proposal passed64 isolated tests but is NOT applied;
  phone35 successor prepared by Sol but NOT compiled/fitted. Exact sigma/residual
  interweave prototype passed7 tests; rank-guard repair is also proposal-only.
  Neither changes the live fit or establishes improved mixing. CalFresh first;
  no Solar/CCW/synthetic restart. W2 read-only poll next03:38:06UTC. Goal active.

- 2026-09-21 02:32 UTC: Alex again asks why all945threads are not feeding the
  model and says not to lose track. Root confirmed livejoint47 session77247,
  PID32996; firstcondition chains1/2 sampled,3/4 underway, no terminalresult.
  Current96linkedthreads/115singleclockrecords/174openuses unchanged. Integration
  document now records the concrete pipeline bottleneck and three new unfitted
  candidates: calfresh_phone_lower_bound_event_inputs_v1,
  calfresh_benefit_disruption_joint_input_v1, and
  calfresh_sar7_joint_program_candidate_v1 (q067 compiled, not consumed).
  First two packets await root adoption. Joint47 postfit analyzer is prepared
  at calfresh_joint47_analysis_v1 but inert until all3terminalmanifest hashes
  are authorized. Do not confuse these preparations with evidence-use closure;
  all29live-source files remain frozen. No other-family/synthetic restart.

- 2026-09-21 02:18 UTC: ACTUAL joint47 execution started, root session77247,
  PID32996. Packet `runs/three_family_20260920/calfresh_joint47_execution_v1`;
  finalplan ae0d1e346ea5eba729422b0584b1160df8d000742fc2e7233639f91c39178d6e,
  driver5bbfcd7f01bdc289d5634fddf5552a85123e76be80ef02aaf471d0236827d447.
  ALL29 source-closure files, driver/plan/input/protocol/initializer/addendum
  MUST REMAIN FROZEN until all3conditions terminal. Exactly50/50,90/10,10/90
  ambiguous-case path weights,4chains1000warmup2000draws,2workers, sequential.
  Root added opt-in exact case-local likelihood evaluation to avoid all-case
  recomputation during one-case updates; defaults unchanged, no new model/prior.
  Independentkernel+launchreviewsPASS,15focusedtestsPASS,`pytest tests -q`
  1888PASS78.06s. Initial unscopedpytest hit21archived/vendor collection errors;
  recorded, no deletion. One-case factor~17.5xfaster atinitialstate, NOTwholefit
  speedpromise. Complete-target checks precede nonlocalupdates; failuresstop.
  Primarycasegroups47;61facets/49reportgroups, no double-count of20oldparents.
  Consumptionproposal closes onlyq012/q016/q074/q150 AFTERexecutedresultadoption;
  13parallelusesremainopen. For now115singleclockrecords/96linkedthreads/
  174openuses unchanged. Adminfit still0forums; no population/sourcebiasclaim.
  Nextmonitor77247, do not restart merelybecausea pollingcall yields. Preserve
  every condition and failure; no automaticextension/gaterelaxation. CalFresh
  first; no Solar/CCW/syntheticrestart. W2nextcheck02:38:41UTC. Goalactive.

- 2026-09-21 01:59 UTC: the user's all945-thread actual-use gate remains open.
  Existing V6 now handles explicitly pending optional interview events without
  forcing an interview on the direct path. Independent review PASS;1874 full
  tests PASS (six stale fake-executor tests corrected, not model regressions).
 32 oldjoint5 likelihood states replay exactly. Root adopted
  `runs/three_family_20260920/calfresh_joint47_model_input_v1/root_adoption.md`:
  47cases/61facets/49reportgroups,19standard-only/1direct-only/27ambiguous,
  seven shared-error groups and11absence declarations. No new fit launched yet;
  source-supported execution initialization and frozen driver remain in prep.
  Candidate's finite-only default initialization must NOT masquerade as the
  protocol's source-interior/inactive-zero initializer. Three approved scientific
  sensitivity conditions use fixed ambiguous-case weights50/50,90/10,10/90;
  no learned path frequency or selection correction. Current115fitted component
  records/96linkedthreads/174openuses are unchanged until actual execution.
  See docs/2026-09-20-calfresh-optional-event-censoring.md. CalFresh only;
  Solar/CCW/synthetic deferred. W2checked01:38–01:43UTC,selectedS03complete
  with2fails,wholecorpusincomplete; nextcheck02:38UTC. Goal active.

- Latest forum-coverage checkpoint (2026-09-21 01:32 UTC): Alex asked again why
  the roughly 900 threads are not all feeding the model; DO NOT LOSE this gate.
  All945 captured threads are reviewed, but only96 distinct registry thread IDs
  link to115 current single-clock records (includes dependent reposts, not96
  people). Joint5 reuses five of those threads.174 recorded uses remain open;
  primary administrative fit still has zero forum cases. The bottleneck is
  evidence integration, not a remaining945-thread reading queue. No named
  department/admin-match admission gate. Current single entrypoint:
  `runs/three_family_20260920/calfresh_forum_source_use_v7_thread_links01/consumer_entrypoint.json`;
  root adoption beside it records verified counts and source links. It selects
  correction02's complete effective-file map plus one factor-scoped thread typo
  repair.26 corrected/supplemental claim flags now correctly stay effective;
  historical fits/lineage unchanged. Stop reconstructing current use from v6
  plus historical deltas. The two design workers finished44-case reconciliation
  and15-row candidate review; neither is a compiled/fitted expansion. Next work
  is honest joint-case integration (including possibly absent interview events),
  not new generic verification or more separate tiny clock fits. No live fit.
  CalFresh stays first; Solar/CCW/synthetics deferred. Goal remains active.

- Latest joint-model checkpoint (supersedes running/preparation notes below):
  both CalFresh five-case joint conditions completed and passed, in 93.8 and
  86.2 seconds. Session 30590 is closed with exit 0. Root adopted the independent
  analysis at `calfresh_joint_timing5_analysis_v1/root_adoption.md`: 32 saved
  likelihood states replay exactly; independent t4 calculation agrees to 1.78e-14.
  Use `strict_results.json`, not the preserved permissive-JSON predecessor.
  The correction changes only 128 open-bound encodings, no fitted numbers.
  Shared-error cancellation makes stable phase shares partly by construction;
  no population, agency-cause, or source-calibration claim. Five cases overlap
  existing records, so the 115 single-clock records remain 115. Joint analysis
  adds two usable conditions and ten grouped-factor executions, not 15 new
  independent observations. Eight phone reports now have descriptive use;
  root accepted only six queue closures, retaining q059/q060 for cluster-aware
  timing. Current queue: 174 open rows. Effective phone delta is
  `calfresh_phone_elapsed_burden_descriptive_v1/effective_source_use_delta.json`.
  V7 current-use consolidation is underway. Two other Sol workers assess a
  coherent union of existing 28 interview/26 decision inputs and 15 remaining
  partial timeline uses. Outcomes before/no interview need explicit paths;
  never invent an interview to force a two-phase graph. No live fit remains.
  See docs/2026-09-20-calfresh-joint-timeline-results.md. Goal remains active;
  CalFresh first, other real families and synthetics still deferred. W2 hourly
  monitor remains due 01:38:46 UTC; Solar is still paused, not resumed.

- 00:58 UTC: previous turn verified remaining-use reconciliation and corrected
  tracking; this turn actually launched the two fixed joint-timing conditions.
  Live root exec session30590 / PID94214, packet
  `calfresh_joint_timing5_sensitivity_v1`; corrected effective input is
  `calfresh_initial_application_joint_timing_input_v1_erratum_v1/model_input.json`.
  Core, driver, plan and all 27 imported source dependencies MUST stay frozen
  until both reports complete. Two sequential conditions, four chains each,
  1000 warmup/2000 retained, two workers; no automatic extension or gate change.
  No new independent case/count claimed. Two Sol workers handle phone8 actual
  descriptive integration and current-delta-aware five-case use mapping.
  Current remaining-use queue is187 minus q057,q065,q127,q128,q178,q186,q187 =180;
  v6 alone is stale, mandatory26/SAR10/card deltas apply. Other families remain
  deferred; Solar group80419 verified six stopped processes at00:56UTC.

- 00:52 UTC user reminder: why are not all ~900 forum threads feeding the model?
  Keep actual evidence use a CalFresh completion gate. All 945 captured threads
  are reviewed, but only 115 component records reach separate conditional fits;
  the administrative fit still has zero forum cases. Latest finite reconciliation
  `calfresh_open_use_integration_reconciliation_v1` confirms 180 open use rows;
  root replayed five output hashes and queue arithmetic. Next ranked existing
  batches: benefit-disruption 9, descriptive phone elapsed records 8, renewal
  response 5; no rows closed by ranking. No named-department or matched-admin
  requirement for timing admission. Five-case joint input needs additive marker
  and embedded-provenance corrections before any fit; two Sol workers preparing
  successor/driver, no launch authorized yet. Do not restart synthetic queues.

- Latest 00:43 UTC: prior turn made progress (opt-in casepriors); this turn adds
  shared-log-error report groups INSIDE V6, no newarchitecture. Independent v2
  review PASS after boolean/member-mutation fixes;233adjacenttestsPASS. Code
  frozen while twoSol workers prepare five-case joint sensitivity input/runner;
  third ranks existing180uses. No realjointfit yet. Group factor REPLACES members,
  commonerror+contamination mixedonce; exact relative timings withinbounds is a
  strong declared sensitivity, not learneddependence orsourcebias. ExactDBM
  projection may eliminate unmodeled snapshot/call/upload nodes, but allparents
  must be replaced jointly and no priors placedon eliminatednodes. Fivecases
  comprise3observedoutcomes/2pending;8sourcegroups→5explicitcasegroups, notnewcases.
  Priors/configfixed ininputprotocol; two reportscales.25/.5; population4096 for
  unchanged2%predictionrefinementgate, nochangeindividualcase likelihood.
  Newsource-onlyfinding: completed1tc/1u6/1w6 postinterviewshares65–85.9%,
  83.3–90.6%,79.2–88.5%; notpopulation/agencycause. Jointphase-share rootadopted.
  Six document-response chronologies nowrootadopted WITH erratum01 fixing q115
  andq149; no new factors/queueclosures.115/29/180consumptioncounts unchanged.
  W2hourly00:38selected245/245complete_by_counts=true,2fails;wholeincomplete.
  Next01:38UTC. SolarPGID80419sixstillT;33GiBfree99%, no cleanup/resumeauthority.

- Latest 2026-09-21 00:19 UTC (supersedes statuses below): real CalFresh first.
  All945 captured threads reviewed; actual fit consumption remains115 component
  records across29conditions,28usable,180recorded open uses. This gap is a
  completion gate, not permission to discard unmatched or unknown-actor reports.
  Root implemented opt-in fixed-case-path priors in existing V6: one assignment
  per case, explicit unknown actor, declared sensitivity weights only. Independent
  review PASS with qualifications;197adjacent tests PASS;4old real marginal
  states replay exactly. No real actor-assignment fit or grouped-report kernel.
  See docs/2026-09-20-calfresh-case-path-priors.md and corresponding root receipt.
  First-decision26 deterministic reference UNRESOLVED:66,049evals/14.53s;
  tail-grid gate fails, old MCMC FAIL unchanged. No automatic retry.
  Six document-response chronologies NOT adopted: root found q115's two-weeks
  interval anchored to wrong endpoint and q149's BY8/16 mistaken for ON8/16.
  Sol preparing additive erratum; preserve v1 and180queuecount. No live fits.
  Core/runner changed only by this opt-in extension; new imports are snapshot
  dependencies. Solar group80419 remains paused, no resume or cleanup authority.
  W2 next read-only check00:38UTC; synthetic and other real families deferred.

- Latest23:52UTC (supersedes checkpoint counts below): CalFresh real remains
  first. All945 captured threads reviewed; seven timing components now use114
  records across28 terminal conditions,27numericalPASS. First-decision26
  supersedes17; mainmixed FAIL Rhat1.010483865, fouralternativesPASS. No extension,
  gate relaxation or sensitivity promoted tobase. Root checked26generic+69
  closeout bindings. SAR7ten supersedesnine,all4PASS,session84879closed0;
  root source review plus19analysisbindingsPASS. Current sourceuse is v6 plus
  fullscope26/SAR10 replacement deltas and card-business-bound addition.
  Remainingqueuev1 records187openrows/185workitems BEFORE those replacements;
  seven explicit closures leave180openrows,not180threads ormodels. Exact
  closure is by clock/use, notclaim.
  Businessdayq057 has explicitapproval/nonreceipt; v1claimed≥3calendar under
  inclusive dates incorrectly. Rootcounterexample Mon23:59→Thu00:01 is~2days.
  Corrected v2 proposes≥2 only under declared four-distinct-business-dates
  reading; nativefactretained, old8baseunchanged. One admission sensitivity
  (seed2026092341) nowterminalPASS, session5659closed0. With sensitivity115
  componentrecords/29conditions/422executions,28PASS+preserved26mixedFAIL;
  exact97caseIDs/107canonicalrefs are NOT people. Root35closeoutbindingsPASS.
  Current combineddelta calfresh_card_business_bound_closeout_v1; no livefits
  orworkers, no newcode/fullsuiteclaim. q096unknownoriginstillheld.
  No broad945reread, newretrieval or syntheticwork. Unknown departments are
  NOT an admission gate; general categorical actor/joint inference unfinished.
  W2read-only23:38selectedS03complete_by_counts=true245/245,2fails;wholeincomplete.
  Next00:38UTC. SolarPGID80419all6stillstopped,39GiBfree, no cleanup authority.
  Model/runner imports unchanged; workersSol handle finite evidence/consumption.

- Latest23:16UTC: administrative ridge experiment is terminal, session94761
  closed. BasePASS/scored; tighterFAIL(10runnerflags,6binfailures),unscored,
  no continuation. Root replayed26analysisbindings at
  `calfresh_histogram_ridge_analysis_v1`; importedmodelclosureunchanged.
  Standalone eventhelper repaired;24tests+bounded independent v2PASS,8bindings
  rootreplayed. Joint9 effectivev1+mandatoryerratum now root-adopted and used
  at `calfresh_joint_event_results_v1`:35constraints,36literalrefs,10nativehashes,
  all9feasible. Derivedphasebounds,NOTjointfit ornewindependentobservations.
 1w6unsupported1day upload boundremoved;1tcexplicit3weekprimitiveincluded as
  correlatedcoarsening. Sol now refreshes source-usev6(actual104/28 unchanged),
  and consolidates remaining first-decision same-target candidates with existing
  17 inputs preserved. No broad945 reread/newretrieval/syntheticqueue. See current
  findingsdoc for new admincomparison and postinterviewbounds. W2due23:38.

- Current update, 2026-09-20 23:10 UTC: Alex's forum-use requirement remains
  open, not forgotten. All945 captured threads reviewed; seven separate timing
  components fit104 records in28 conditions. Descriptive220 claims overlap;
  neither count is people or a joint burden posterior. Required accounting is
  source-use v5 PLUS application-decision source_use_delta.json. Unknown
  departments are not an admission gate; categorical attribution is unfinished.
  Nine-case `calfresh_joint_event_inputs_v1` is compiled, NOT fitted or adopted:
  root caught unsupported same-day document submission in1w6 and asked Sol for
  additive erratum;1tc's explicit three-week postinterview report also needs
  retained treatment. No extra factor for a bound derived from existing reports.
  New standalone event_constraints.py uses exact decimal-rational closure after
  independent review found floating-point equality/tolerance defects.24focused
  testsPASS; v2 independent repair review pending. It is not imported by liveV6.
  First-decision candidate1tkxd08 and newly recovered1u6 observed-denial remain
  unconsumed candidates for a consolidated successor, not included in current17.
  Administrative ridge base now passes numeric/bin gates, savedLLreplay exact;
  temporal positive-frame logloss.252748593 versus Dirichlethalf.252281923
  (slightly worse), not superiority. Tighter conditionPID38092/session94761
  is finishing posterior summaries; source/runner imports must remain frozen
  until its analysis finishes. No extensions. Oldfailures/fixedspreadnegative
  findings preserved. Otherfamilies/synthetic staydeferred; W2monitor due23:38.

- Current forum integration checkpoint, 2026-09-20 22:36 UTC, supersedes the
  historical queue statuses below: all 945 captured CalFresh threads reviewed;
  87 timing component records actually fitted across six clock families and
  23 conditions, plus an overlapping descriptive union of 220 canonical claims.
  Effective accounting is `runs/three_family_20260920/calfresh_forum_source_use_v5`;
  root replayed its 49 manifest bindings and the descriptive source index's
  203 artifact hashes. The 215 primary + 47 parallel clock routes are sealed,
  not all consumed. Application-to-observed-decision has 17 compiled cases
  (7 completed, 10 pending), NOT yet fitted. Preliminary 13 existing-frame
  additions were not all admissible; only one SAR7 candidate remains for
  target-specific reconsideration. The 154 distinct-clock rows still require
  supported integration, not a generic exclusion. No valid current global
  pending union is asserted; v3's 283 is historical. Alex's explicit requirement
  remains critical: track every thread/claim through actual supported use or
  specific disposition; reviewed/routed/descriptively used does not close a
  parallel timing use. Unknown departments are NOT an admission gate. General
  categorical actor attribution and joint/source-selection inference remain
  unfinished. Next: adopt and fit the 17-case component, then consolidate
  remaining supported clock groups. Do not resume other families/synthetic.
  UPDATE 22:51 UTC: first-decision17 now actually fitted in five conditions,
  all numerical PASS. Corrected first-decision cf240_012 from later approval
  [61,69] to earlier-denial completed-by [0,52] BEFORE sampling; retained all17.
  Fifth condition widens only "almost3months" [56,93] to[0,93]. Effective inputs
  `calfresh_application_decision_input_erratum_v1`; fits `calfresh_application_decision_marginal_v1`
  and `calfresh_application_decision_lexical_marginal_v1`. Main mixed median54.15d
  [30.29,96.94], completed-only11.95d; direct mixed record median25d–unbounded.
  Spread weak; no population/agency/source-selection claim. Effective source-use
  is v5 PLUS `calfresh_application_decision_closeout_v1/source_use_delta.json`:
  seven families104records,28conditions,367condition-factor rows,92exactcaseIDs,
  101canonicalclaimrefs, not people. All945 reviews remain; no global pending
  number asserted. Newbenefit-disruption4/2/3-case inputs compiled NOT fitted;
  assess joint event use, not arbitrary pooling or a portfolio of tiny fits.
  Sol workers: benefit-disruption completed, now analyze admin ridge fits;
  ambiguous31 source context; joint-case/uncertain-actor feasibility.
  Ridge sampler independent reviewPASS,94adjacenttestsPASS,12oldsavedstates
  replayed exactly; new two-condition target-preserving sampler experiment LIVE
  under `calfresh_histogram_ridge_fits_v1/plan.json`, session94761 initialPID31211.
  Same positive46 base/tighter inputs/priors/seeds/4x2000; fixedstep.05,workers2,
  no continuation. First condition still sampling; no success/adequacy claim.
  W2 check22:38selectedS03 complete_by_counts true245/245,2fail;wholeincomplete.
  No syntheticrestart; next23:38. Solar PGID80419 stillsixstopped;48GiBfree.
  See `docs/2026-09-20-calfresh-forum-model-integration.md` for the closeout gate
  and `docs/2026-09-20-calfresh-current-findings.md` for the qualified synthesis.

- Current checkpoint22:06UTC: card-access8 now reaches four terminal PASS fits
  at `calfresh_card_access_marginal_fit_v1`; six families currently87 records,
  23 conditions, not87 people or population burden. Five pending card histories
  mean no finite direct median upper bound; eventual possession is a model
  assumption. Phone successor33 is terminal, all4 PASS at `calfresh_phone_queue_exit_marginal_v5`;
  v4's32-case input was never fitted. Additions are191fg4u first3h and1ul7jyw
  approximate2h queues; old31 and all priors/configs unchanged. All776-record
  audit proves candidate-discovery omission, not the exact historical filter
  or raw945 extraction recall. Semantic16 source decisions root-adopted with
  automated-closure explanations explicitly commenter hypotheses, not observed
  system ownership. Sol workers now route215 remaining clock claims and
  consolidate current source use. Qualitative47 is root-adopted (35structure,
  7context,4dependencies,1non-target;16 episode-specific numeric facts), with
  mandatory reportingerratum46threads. Root replayed13manifest+48artifact+
  97normalizedquotes; no mismatches. Its zero pending qualitative uses is NOT
  global timing closure: worker now checks parallel timing uses (e.g.cf360_007
  earlyJuly application→approvalbyAug can be an interval). Preliminary215routing:
  13 compatible-frame candidates and15 application→observed-decision cases
  (5completed,10pending), NOT yet admitted/fitted. Check old exclusions/case
  dependence, combine all supported215+qual47 additions, then one successor
  per component; no sequence of tiny refits.150new/distinct clocks need concrete
  grouping/use, not an opaque terminal bucket. Existing sealedv3+
  mandatoryerratum is the earlier77-record checkpoint; its283pending count is
  not a refreshed count after these additions. General actor marginalization
  remains unfinished. CalFresh completion requires actual supported use or
  specific dispositions, not just reading945. Other families/synthetic deferred.

- Earlier CalFresh forum integration checkpoint: all945 captured threads reviewed, but that
  is not completion of model consumption. Five conditional clock families now
  actually fit77 component records (31phone,28interview,6benefit,9SAR7,3recert),
  all19 fixed marginal conditions numerically PASS. Not77 independent people;
  selected report frames, not statewide timing or a joint burden posterior.
  New twelve fits: `calfresh_next_clock_marginalization_v1`, all terminal;
  `docs/2026-09-20-calfresh-additional-forum-clocks.md` records small-sample,
  censoring and prior-sensitive-spread limits. Corrected renewal inputs live in
  `calfresh_reporting_renewal_frames_effective_v3/*_compiled_preflight_effective_v3`;
  no universal annual cadence. The earlier seven phone/interview fit results
  passed a later independent numerical review, separate from source semantics.
  Structural inventory uses38 facts+25 contexts; remaining descriptive60 rows
  are26 newly used (42 standalone facts),28 contextual and6 specifically held.
  **Concrete open compiler gap:** fullread006/cf240_011 has3h/30min phone holds
  nested under effort but is absent from the frozen phone candidate packet.
  An all776-review-item field-routing audit is underway, not a945-thread reread.
  Do not label31phone cases an exhaustive compatible-case census. Source-use_v3
  is sealed and MUST be read with `calfresh_forum_source_use_v3_erratum_v1/root_adoption.md`:
  19fit conditions,257condition-by-factor rows,283unique claims still have a
  pending use (not unread threads). Descriptive use can coexist with pending
  timing integration. Its cf240_011 overlay key misleadingly says recertification-
  interview; root_adoption clarifies it is the PHONE QUEUE within that episode.
  All776-item scan preliminarily finds exactly one missed same-target phone case;
  additive phone32 compiler in progress, no fit. Card8 compiling, no fit. The16
  genuinely ambiguous claims are receiving targeted source-context resolution.
  Twelve additional-clock results review passed227 checks; it is numerical/
  provenance review, not independent renewal source semantics. No new full suite.
  Named departments are never an admission gate; categorical actor uncertainty
  and source-bias identification remain unfinished. Synthetic/Solar/CCW stay
  deferred. W2 monitoring21:38UTC: selectedS03 complete_by_counts true245/245
  but2fail; entire corpus incomplete; no restart. Next hourly check22:38UTC.

- Latest CalFresh numerical update: `calfresh_case_marginalization_v1/{phone,interview}/analysis_v1`
  now fits the same31 phone and28 interview histories with all7 conditions passing
  unchanged gates. This optional same-target V6 path integrates independent case
  effects and inactive priors (2 sampled coordinates vs68/62); it is not a new
  process model, source-bias calibration or a general richer-case marginalizer.
  Scientific priors and observations are unchanged. All older failures below stay
  historical, not reclassified. Independent code review passed;249 adjacent tests
  pass. Fits12.7–21.7seconds; results and limits:
  `docs/2026-09-20-calfresh-case-marginalization-results.md`.
  `calfresh_forum_remaining_use_plan_v1` distinguishes718 nonlikelihood items into
  actual pending work and supported other uses, including71 completed descriptive
  claims. The21-item initial143 supplement is consumed (18 structural uses/four
  count facts plus3 holds). All945 source reviews/dispositions remain accounted.
  Full-scope overlap found17 partial rows but0 strict July2025 CF296 matches;
  no forum exclusion follows. Benefit endpoint corrections are now adopted and
  fitted as recorded in the newer checkpoint above. No blanket reread or
  synthetic/other-family restart.

- CalFresh forum integration is on the critical path (Alex reiterated
  2026-09-20). The 945 captured threads must be accounted for through actual
  consumption/disposition, not merely reviewed or retained in sidecars. At the
  latest audit the expanded administrative fit had46 histogram factors and0
  forum-case observations; it is not the complete burden model. At20:50UTC the
  separate interview component actually consumes28 cases (18 completed,10
  historical pending) under `calfresh_forum_interview_fullscope_v3/compiled_preflight_v2/analysis_v1`.
  Only the prespecified wider-report-noise condition passes; completed-only and
  base mixed fail. The phone component consumes31 cases (25 completed,6 pending)
  under `calfresh_phone_queue_exit_fullscope_v3/compiled_preflight_v3/analysis_v1`:
  completed-only and wider noise pass; base mixed and prior15 fail. Never select
  a passing sensitivity as a replacement base or silently extend failed fits.
  Both successors include their respective previous17 cases; one case is shared
  across clocks. These are separate conditional components, not a joint posterior,
  additive total burden or population source-bias calibration. Phone's unfitted
  v1/v2 compiled packets have stale moved-directory paths: use effective v3 only.
  At20:16UTC all945 logical threads have source-review receipts after adoption
  of fullread001–020 (1,810 bindings; exact original777-thread union). This is
  not source-to-model completion. Source-use_v1 checked later captures of the
  older143 and found no added native comments in that frozen directory; the
  initial143 disposition closure reread38 fragmentless sources, adding21 items.
  Contact/rework_analysis_v1 uses40 count facts across34 cases plus20 structural
  facts descriptively, not as a likelihood or total step count. Those21 newer
  supplemental items are under separate assessment. Expanded source-use_v2 is
  sealed:945 explicit dispositions,776 effective review items,59 factor-component
  records/58 source claims. Its718 items outside likelihoods include53 already
  used descriptively; this is not718 independent fit-ready observations or718
  uniformly unfinished analyses. A remaining-use plan distinguishes actual work
  from supported nonnumeric uses and dependencies. Full-scope cross-source clock
  overlap is under review; no blanket reread or new retrieval queue.
  Apply `calfresh_claimant_fullread_020_semantic_erratum_v1` as a replacement,
  not an additional ledger: by-Sep30 implies a lower, not upper, duration bound;
  date gaps and portal observation gaps are not exact elapsed durations.
  Most reviewed evidence is still
  outside fitted inputs: other clocks and structural/count facts need explicit
  compilation/use, not indefinite fit_ready=false sidecars. Parse disjoint
  complete-thread batches with Sol/Luna and consume supported evidence as it
  arrives. Do not impose a named-internal-department requirement: known task and
  jurisdiction plus explicit actor uncertainty are valid inputs; never hard-
  guess a department or equate uncalibrated LLM confidence with a probability.
  Track this explicitly in `docs/2026-09-20-calfresh-forum-model-integration.md`
  and `runs/three_family_20260920/EXECUTION_STATUS.json`. Do not close CalFresh
  on an administrative result or a reviewed-thread count alone.
- Cost routing (Alex, 2026-09-20): routine parsing and verification should use
  **GPT-5.6 Luna or Sol**, not Astra. The three current CalFresh workers were
  checked against local thread metadata and are `gpt-5.6-sol` / high. Prefer
  Luna for bounded mechanical checks and straightforward extraction; Sol for
  contextual multi-document parsing. Reserve root/Astra for model design,
  consequential ambiguity and scientific conclusions. Do not change a frozen
  benchmark's model midway through its scheduled attempts to implement this
  preference; the three-attempt Astra LLM baseline is a comparison condition,
  not a routine parser. Do not restart active cheaper workers merely to rename
  their historical task labels.
- Latest priority override (Alex, 2026-09-20): **finish one real family first:
  CalFresh**. Complete its captured-source/effective-evidence/analysis/results
  chain, including applicant/forum burden, before returning to Solar or CCW.
  All three workers are reassigned to CalFresh. Synthetic work stays deferred.
  Follow `docs/2026-09-20-calfresh-first-closeout-work-order.md`; it supersedes
  the earlier parallel-family schedule. Solar's dedicated process group80419
  was reversibly SIGSTOP-suspended at18:21UTC; preserve it and verify identity
  before eventual resumption. Unmatched forum clocks are not excluded from the
  study: they may support separate phase/conditional/structural outputs even
  when they cannot calibrate bias against the July expedited-issuance cohort.
- Latest work-order update (Alex, 2026-09-20): **real corpora first**. Complete
  solar, concealed-carry and CalFresh source coverage, effective evidence,
  analyses and real-data validation before resuming synthetic construction,
  rendering or synthetic-only infrastructure. Synthetic counterparts remain
  part of the broader objective but are deferred, not required to begin or
  report qualified real-data analyses. Preserve interrupted synthetic work as
  partial; do not claim its pending reviews are complete. Current work order:
  `docs/2026-09-20-real-corpora-first-work-order.md`.
- Current execution scope (Alex approved 2026-09-20): fully parse, verify and
  analyze solar, concealed carry and CalFresh with corresponding synthetic
  setups. Follow `docs/2026-09-20-three-statute-parse-verify-analysis-plan.md`.
  This expands the proposed two-family work order to all captured material for
  these three families, not unrelated programs or open-ended retrieval. The
  latest approval is "great, please now get to work!" Preserve partial work.
  Solar has W2 S07; synthetic CCW and CalFresh need new versioned analogues.
  C29/C44 remain bounded S12 development diagnostics, not additional study families.
  First execution receipts and limitations:
  `docs/2026-09-20-three-family-execution-progress.md`. Source-read completion,
  effective semantic review, compiler acceptance and fit-readiness are distinct.
  Snapshot authority is file-list preparation only; wait for exact-list approval
  before staging or committing. Record of scope and two earlier synthetic repair
  approvals: `docs/scoping/2026-09-20-scope-and-repair-authorizations.json`.
- Read `README.md`, `docs/2026-09-16-bayesian-overnight-audit.md`, and
  `docs/2026-09-16-bayesian-audit-implementation.md` before process-model work.
- V6 is the integration target. V3–V5 are historical controls, not new competing
  architectures. Preserve their saved inputs, snapshots, draws and failures.
- Date plans, protocols, results and audits (`YYYY-MM-DD-...`). Keep living design
  documents undated. Do not rewrite the independent audit to manufacture agreement.
- Do not commit, stage broad directories, or move packages without Alex's approval
  of the snapshot/refactor scope. Preserve unrelated user changes.
- Extractors and fitters must not read benchmark `truth/`, generator specs, or
  scores. Label-review/evaluation utilities may read explicitly designated
  development truth and must record it. Calibration never reads reserved labels.
- Semantic ambiguity follows the audit's measured split: evaluate top readings
  per class; keep sufficiently accurate classes upstream; use calibrated candidate
  weights for others and validate timing/count gains against top-reading controls.
  K LLM votes are correlated predictors, not independent labels. Re-measure on new
  worlds/extractors. Include residual/out-of-chart possibilities.
- Report retained, residual-only, and informative claim coverage separately.
  An unsupported report must stay in the ledger; it is not zero burden.
- Keep elapsed waiting, elapsed service, payer hours and agency hours distinct.
  Marginal variance contraction is not total information or causal identification.
- Source heterogeneity is not one trust score: distinguish reporting bias,
  reporting precision, contamination and case/institution selection. A source
  type or declared calibration ID is not empirical calibration. Use the ordered
  gates in the three-statute plan and
  `docs/2026-09-20-source-precision-and-cohort-handoff.md`.
  Current bounded real-data results and consumption qualifications are in
  `docs/2026-09-20-calfresh-and-ccw-pilots.md`. Numerical eligibility flags do
  not imply model adequacy, population transport or study/publication release.
  Preserve completed protocols and failed sensitivities when developing a new
  sampler; never silently extend an exhausted continuation allowance.
  Optional `source-offset-hierarchy/2` can use hash-bound exact histogram
  cohorts as reference anchors without inventing a narrative report or adding
  a likelihood factor. Its independently reviewed implementation is not a real
  calibration: current bounded solar and CalFresh overlap reviews found zero
  eligible matched comparisons. Exact histograms have no reporting-offset
  parameter; same-family noisy documents may still have one. Prior real pilots
  retain their frozen V3 source and results.
  Case-to-cohort overlap is a separate dependence problem: current V6 has no
  joint ordinary-case/aggregate kernel. Private synthetic membership may audit
  the generator/evaluator but must never secretly select or weight blind model
  inputs. See the qualified dependence review linked in the cohort handoff.
- `pipeline/procbench/` currently contains process inference and its benchmark;
  the older top-level `pipeline/` modules include the discretion workstream.
  Shared runner, manifest and scoring helpers now live in `procbench/infra/`.
  Import them directly, not through a fitting/extraction driver. The planned
  model/evidence/experiments/legacy/bench moves are not complete; preserve old paths.
  Initial approved snapshot: `e581748`; refactor work is separate from that baseline.
- Run `python -m pytest tests benchmark/synth/generator/test_generator.py -q`.
  Source-only audit tests must use fakes/cached outputs, never paid network calls.
- Follow `runs/README.md`. Gitignored runs are not backed up by a source commit;
  no external archive or deletion is authorized without a reviewed destination.
- User request (2026-09-17): after the W2 decision-log audit, check W2_DEV_001
  rendering hourly with `python3 benchmark/synth/render/status.py --world
  W2_DEV_001 --json`. Trust `observed.complete_by_counts`, never `state` alone.
  Check the shared `W2-RENDER` log and `docs/2026-09-17-w2-resume.md`. An earlier
  stopped render was contaminated; do not generalize that label to later runs.
  The 03:33 restart identifies its retained 652 artifacts as the fixed-world
  wave. Check generation provenance and hashes; no cleanup or duplicate workflow
  is authorized by the monitoring request.
  When the count gate is true, spawn a parsing subagent with artifact-only inputs
  and then run integrated V6. No truth/specs/scores in extraction or fitting;
  record verification failures and frozen input hashes. Monitoring handoff and
  duplicate-run safeguards are in `docs/scoping/W2_V6_WATCH.json`.
  The artifact-only parsing and integrated-model handoff is in
  `docs/scoping/2026-09-17-w2-v6-handoff.md`; spawn the parser without history
  because this conversation contains development-truth audit results.
- Local open model (2026-09-23): Gemma 4 31B-it on sk2 H200s via
  `pipeline/procbench/infra/gemma/gemma_remote.sh`; read `docs/gemma-runbook.md`.
  Near frontier consistency for closed-codebook classification and recall-oriented
  triage; NOT for quote extraction (misses agency acts, 2/48 invented quotes).
  Replay-verify every Gemma quote. Offline batch jobs only; no idle GPU servers.
