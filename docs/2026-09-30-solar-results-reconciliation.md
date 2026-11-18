# Solar results: reconciliation and audit (2026-09-30)

One bounded read-only pass over saved summaries and result JSONs. No fits, no quote
re-verification, no raw-thread reading, no edits to other files. Raw-completed medians
quoted in §2 as "raw" are descriptive statistics of saved fit inputs, not new fits.

**Admin inputs used.** `runs/admin_model_inputs_20260930/` as found locally: cohorts CSVs
written 2026-09-30 01:25:56, README 01:32:16. This version is **not de-duplicated**
(EPIC-LA 15% duplicate `project_id`), its DG Stats interconnection clock is
**completed-only** (0 open/terminal rows), and its SolarTRACE comparison matched **0 cells**
(README "Data problems"). Any later fix to these supersedes the admin-cohort numbers below.
Admin numbers restricted to 2017–2025; SolarTRACE covers 2017–2024.

**Units.** Forum fits and admin cohorts: calendar days (cd). SolarTRACE, the Sept 20 panel,
the county model and the Sept 21 burden table: business days (bd). Where shown, "≈cd" is
bd × 7/5, the same approximate conversion the forum pipeline uses; it is not exact.

**Denominators.** Threads, contributor episodes, claims, reports (post-thinning), cells and
admin projects are different units and are never summed here. "n" in forum rows = fitted
reports (one outcome-blind report per contributor/clock/unit). "CA" in the Sept 29/30 scope
= parser California-supported **plus** county-candidate tags.

## 1. Inventory of every Solar statistical result

Status key: **CUR** current; **SUP** superseded (by); **FAIL** failed, kept as history;
**ACC** accounting/preparation only, never fitted; **HIST** passed numerically but no longer
citable (reason given).

| # | Date | Artifact (under `runs/` unless noted) | What was fitted | n | Numerical status | Status now |
|---|---|---|---|---|---|---|
| 1 | 09-20 | `solar_panel_20260920/design_audit_v1.json` | Stage A design audit (no fit) | 22,512 slots (2017–22 build) | gates: separability pass | ACC |
| 2 | 09-20 | `three_family_20260920/solar_coarse_fit_v1` | V6 QMC, 12 AHJ permit submit→approval medians, 2022, 0–10 kW PV (bd) | 12 cells | FAIL (prediction precision 6.36%) | FAIL |
| 3 | 09-20 | `…/solar_coarse_fit_analytic_v1` + `solar_phase_sensitivity_v1` | same, exact single-phase; SD of log AHJ medians 1.14 [0.83,1.45]; 4 sensitivities (floor-0.25 first FAIL, extension PASS) | 12 cells | PASS | HIST pilot; SUP by #13 |
| 4 | 09-20 | `solar_panel_20260920/fit_primary.json` | crossed lognormal, permit+inspection AHJ cell medians 2017–21 (bd); 2.39× p90/p10 AHJ spread; elasticity −2.3% [−3.8,−0.8] | 4,101 cells / 333 AHJ | MCMC PASS; **decision rule FAIL both splits**; **sampler invalid** (§3 E1) | FAIL/HIST; SUP by #13 |
| 5 | 09-20 | `fit_sameday_half.json`, `fit_floor_n.json`, `fit_random_slope_FAILED.json` | sensitivities of #4 | 4,101 | half-day PASS; floor-n FAIL (R̂ 1.015); random slope FAIL (R̂ 1.45) | FAIL/HIST |
| 6 | 09-20 | `score_and_offset_v1.json` (E4) | forum-vs-SolarTRACE final-IX→PTO offset −42% [−59,−18] | 12 paired reports | closed-form, no gate | HIST; contradicted (E2, E4) |
| 7 | 09-21 | `process_structure_20260921/solar_phase2` (+scaling) | 50-step occupancy, 5-fold held-out | 440 AHJ | FAIL (R̂ 4.31–4.45, ESS≈4) | FAIL |
| 8 | 09-21 | `…/solar_phase5` stringency regression | AHJ effect on requirements, per draw of #4 | 259 / 45 AHJ | inherits #4 | HIST (E1) |
| 9 | 09-21 | `…/solar_phase5/burden_table.json` | permit 9.1 bd, inspection 22.0 bd, 29%/71% share | from #4 | inherits #4; interval defect | HIST (E1, E3) |
| 10 | 09-22 | `solar_forum_20260922/timing_batch001_v2` | 11 separate forum clocks | 44 records | PASS | SUP by #11 series |
| 11 | 09-22 | `solar_forum_20260922/timing_combined002_reconciled`→`024` (18→233 clocks) | separate conditional forum clocks (Codex root-reviewed reading) | 024: 576 claims / 329 contributors / 233 clocks | 024: 233/233 PASS | 002–023 SUP by 024; **024 CUR for its evidence base only** (parallel, not merged with #22; E13); 025 prepared, never fitted |
| 12 | 09-22 | `model_bridge/interim_full_episode_fit_v1`, `production_fit_v1`, `combined003_production_fit` | whole-episode structure | 50–87 installations | FAIL / INVALID / FAIL | FAIL |
| 13 | 09-22 | `county_model/timing_full001` (+`timing_training001`, `timing_full_halfday001`, `timing_training_through2021_001`) | admin AHJ/utility cell-median timing, 4 phases, 58 counties (bd) | 9,531 cells | all PASS | **CUR** (admin descriptive; E6) |
| 14 | 09-22 | `county_model/timing_training001/heldout_scores_v2.json` | held-out log score vs simple baseline | 3,418 cells | county model loses overall (−0.083); through-2021 forecast −0.010 | CUR (negative result) |
| 15 | 09-22 | `county_model/county_report001` | per-county summaries of #13, ref year 2024 | 116 rows | from #13 | CUR with E6 caveat |
| 16 | 09-22 | `county_model/joint_phase_bridge002/fit001`, `fit002`, `fit003` | forum+admin two-phase bridge | 26 forum + 6 admin | FAIL, FAIL, runtime FAIL | FAIL |
| 17 | 09-22 | `joint_phase_bridge002/fit004_collapsed_q256` | same, collapsed cases; latent medians 5.0–32.2 cd across 16 programs | 32 obs | PASS | HIST (narrow frozen subset; source/context confounded) |
| 18 | 09-22 | `joint_phase_bridge003` | expanded bridge | 39 forum + 7 admin | FAIL (R̂ 1.010251) | FAIL |
| 19 | 09-22 | `model_bridge/full_universe_successor001/fit001_positive_anchors` | 50-action occupancy, 440 AHJ | 4,098 readings | FAIL (R̂ 1.080, ESS 43) | FAIL |
| 20 | 09-22 | `solar_evaluation_20260922/forum001/fit002`, `fit003_exact_marginal` | final inspection→PTO training frame; fit003 13.9 [9.2,21.1] cd | 48 train | fit002 FAIL (ESS 198); fit003 PASS | CUR only as evaluation input |
| 21 | 09-23 | `solar_evaluation_20260922/admin002/comparison.json`, `forum_comparison002/comparison.json` | Bayes vs simple vs 5×LLM | 64 cells; 9 contributors | admin: Bayes 51.01 > simple 49.74 > LLM 47.95 (lower better); forum: 2.651 / 2.652 / 2.681; both CIs include 0 | CUR (no Bayes win) |
| 22 | 09-23 | `solar_bulk_adoption_20260923/model/fit001`, `california001` | contract→install 106 [74,156]; install→PTO 86 [67,113]; CA install→PTO 100 [58,193] | 21 / 94 / 22 | PASS | SUP by #26/#27 (same corpus, expanded) |
| 23 | 09-23 | `solar_step_model_20260923/rightwinger_fit001`, `core2_fit001` | single/2-case journeys | 1 / 2 cases | FAIL; core2 population grid FAIL | FAIL |
| 24 | 09-23 | `…/joint4_fit001`, `joint8_fit001`, `joint8_fit002` | shared-action V6 journeys; pooled permit review 5.06 [2.61,9.54] d | 4 / 8 / 8 cases | PASS | SUP by #28 |
| 25 | 09-29 | `solar_model_20260929/concord_historical_report_checks001.json` | corrected Concord report check (Student-t): 18.7% not 27.3% | 6 reports | diagnostic | CUR (supersedes 27.3%) |
| 26 | 09-29 | `solar_model_20260929/pooled_s1_prepared001` | 14 pooled forum clocks (15 declared; deposit→PTO below support) | 1,225 reports / 899 dependence labels | 14/14 PASS (R̂≤1.0012, ESS≥4,196) | **CUR** |
| 27 | 09-29 | `solar_model_20260929/pooled_s1_california001` | 8 CA-supported clocks (scope chosen after seeing #26) | 321 reports | 8/8 PASS | **CUR** (development scope) |
| 28 | 09-29 | `solar_model_20260929/joint11_control_fit001` + `_summary001.json` | 11 shared journeys; pooled permit plan review 6.62 [3.35,12.99] d (5 cases, 7 occurrences; not reported in any doc) | 68 obs / 11 cases | 216/216 PASS | **CUR** (actual-case only) |
| 29 | 09-29 | `joint11_no_contamination_fit001`, `joint11_wider_task_fit001` | declared sensitivities | 11 cases | PASS; wider-task FAIL 214/216 | CUR / FAIL |
| 30 | 09-30 | `solar_admin_integration_20260930/legacy_pooled_accounting`, `legacy_california_accounting` | crosswalk re-admission, 15 / 13 eligible frames | 3,277 / 987 reports | not fitted | ACC |
| 31 | 09-30 | `solar_admin_integration_20260930/burden_frames` | contract→permit submission, order→design, order→cancellation | 125 reports | 3/3 PASS | **CUR** |
| 32 | 09-30 | `solar_admin_integration_20260930/solar/comparison_candidates.jsonl` | admin-clock candidates | 527 candidates; 13 cell-key-ready | none | ACC |
| 33 | 09-30 | `admin_model_inputs_20260930/cohorts/solar_*.csv` | per-project admin histogram cohorts | 111 / 111 / 372 cells | descriptive | ACC (unfitted; pre-fix version) |

## 2. Reconciled estimates per clock

Forum rows: posterior median of the reported-case distribution's **median** [90% CrI], cd,
pooled across eras/utilities/places incl. national and unknown geography unless marked CA.
SolarTRACE "cell" = median of AHJ (or utility) cell medians, CA, 0–10 kW PV-only, 2017–2024
pooled (computed from `…__ahj_utility_timelines__ca_long.csv`); "state" = CA state-level
medians by year (`…__state_level_timelines.csv`, 0–10 kW PV-only); "quartile sheet" =
dataset-wide (not CA-specific) yearly medians 2017–2024 from `…__data_quartiles.csv`.
Admin cohorts: n-weighted median of 2017–2025 cell medians (completed only).

### 2a. Headline table

| Clock | Forum pooled 09-29 (n) | Forum CA 09-29 (n) | Other forum fits | SolarTRACE (bd; ≈cd) | Admin cohorts 2017–25 (cd) |
|---|---|---|---|---|---|
| Contract→installation | 104.6 [83.5,131.1] (68) | 80.5 [53.1,120.5] (18) | 09-23: 106 [74,156] (21); t024: 115.8 [58,243] (11) | quartile pre-install total 34–63 bd (≈48–88) | — |
| Order→installation | 138.9 [124.9,154.8] (216) | 98.2 [80.7,119.8] (58) | t024: 57.2 [15,160] (6) | — (no "order") | — |
| Deposit→installation | 113.7 [79.8,161.6] (27) | below support | t024: 95.3 [32,233] (3) | — | — |
| Permit submission→approval | 15.1 [9.9,23.1] (39) | 17.1 [9.9,27.7] (16) | t024: 11.5 [3.9,29.4] (7); application→issuance 28.7 [13.8,64.0] (5); joint11 plan review 6.6 [3.4,13.0] | cell 7 bd (IQR 3–12; ≈10); state 1–8 bd by year | app→issued **11** (Sacramento 7, San Diego 8, LA Co. uninc. 13, SF 46, LA city/LADBS 129) |
| Permit approval→installation | 19.4 [12.0,31.6] (17) | below support | t024: 11.4 [2.9,40.5] (3) | quartile install phase 10–17 bd (≈14–24) | — |
| Physical installation duration | 2.15 [1.85,2.52] (137) | 2.27 [1.83,2.91] (34) | t024: 1.3 [0.6,3.0] (14); joint11 1.35 | — | — |
| Installation→final inspection | 14.1 [11.4,17.4] (110) | 17.4 [12.7,23.8] (41) | t024: 16.4 [10.0,27.6] (22) | cell 15.5 bd (IQR 10.5–23.5; ≈22); state 10–24; county model 15.8 (2024 ref); 09-21 burden table 22.0 (2017 ref, E1/E3) | issued→final **71** (different start; SD 39, LA Co. 98, SF 114.5) |
| Installation→IX submission | 73.9 [41.7,138.6] (17) | below support | — | quartile inspection + post-inspection ≈13–36 bd (do not add; indicative) | — |
| Final inspection→IX submission | 30.2 [20.1,46.2] (15) | below support | — | quartile post-inspection 2–13 bd (2–3 since 2019) | — |
| IX submission→PTO | 10.9 [6.9,17.3] (41) | 10.7 [6.2,20.2] (22) | t024: final docs→PTO 17.9 [11.7,27.4] (36); IX application→PTO 74.5 (13); initial IX application→PTO 111.3 (22); 09-20 E4 −42% vs admin | utility cell 6 bd (IQR 2–12; ≈8); county model PG&E 4.7 / SCE 3.7 / SDGE 1.9 (2024 ref); quartile 5–10 | **11** (PGE 12, SCE 13, SDGE 6); 2023 pre-NEM3 cells 105–156 |
| Installation→PTO | 74.4 [65.8,84.0] (403) | 79.3 [62.7,101.3] (102) | 09-23: 86 [67,113] (94), CA 100 [58,193] (22); t024: 68.0 [46.7,103.2] (33) | quartile post-install total 28–54 bd (28–36 since 2018; ≈39–50) | — |
| Final inspection→PTO | 18.6 [13.1,26.5] (66) | 14.7 [8.8,24.3] (30) | t024: 14.8 [10.0,22.2] (52); forum001 13.9 [9.2,21.1] (48) | not published directly (post-inspection 2–13 + final IX 5–10 bd; do not add) | — |
| Contract→PTO | 167.5 [124.8,222.9] (26) | below support | t024: 119.4 [73.2,186.2] (13) | state project time 65–153 bd by year (2021–23: 99–113; ≈139–158); quartile total 73–97 | — |
| Order→PTO | 128.7 [103.7,158.9] (43) | below support | t024: 440.6 (3, not headline) | — | — |
| Contract→permit submission (burden) | 09-30: 40.7 [21.3,83.4] (21) | 6 CA | t024: 22.3 [5.0,84.1] (3) | quartile design phase (contract→1st permit/IX submit) 6–20 bd; 19–20 in 2023–24 (≈27–28) | — |
| Order→design (burden) | 09-30: 45.3 [30.5,69.4] (76) | 22 CA | t024 order→design completion 15.0 (3) | — | — |
| Order→cancellation (burden) | 09-30: 228.1 [141.9,370.7] (28) | 5 CA | — | — | — |

Raw completed-interval medians (fit inputs, finite completed only; descriptive):
install→PTO 42 cd (268 of 403) vs posterior 74.4; contract→install 91 vs 104.6;
permit submission→approval 17 (09-29 input, 34 finite) vs **28** after the 09-30
crosswalk (151 finite); IX submission→PTO 9 (35) vs **14** after crosswalk (192).

### 2b. One-line explanation of each discrepancy

- **Contract→installation.** Forum 81–116 cd vs dataset-wide 48–88 cd: posting selection
  toward delayed projects and 2021–23 backlog eras; forum "contract" includes financing/loan
  dates; quartile sheet is not CA-specific.
- **Order→installation / deposit→installation.** No admin clock; "order" is dominated by one
  national installer's order flow, so the pooled 138.9 vs CA 98.2 gap is national-vs-CA case mix.
- **Permit submission→approval.** Forum 15–17 cd vs SolarTRACE ≈10 cd cell (≈1–11 cd
  install-weighted) and admin 11 cd: selection of problem permits, forum starts sometimes at
  installer's first submission incl. resubmission loops (same as SolarTRACE) but also at
  "applied" in plan-check cities; AHJ-equal cell medians exceed install-weighted state medians
  because high-volume AHJs are faster. LADBS 129 cd is a Gemma-selected ~100/yr subset (likely
  plan-check permits only), not LA's typical solar permit.
- **Permit approval→installation.** Agrees (19 cd vs ≈14–24 cd); small n.
- **Installation→final inspection.** Forum 14–17 cd vs SolarTRACE ≈22 cd cell: SolarTRACE's
  inspection endpoint is internally inconsistent ("inspection complete→last passed" vs
  "install→last completed"); admin issued→final (71 cd) includes the install wait and is a
  different clock.
- **Installation / final inspection →IX submission.** Forum 30–74 cd vs 3–4 cd post-inspection
  admin phase: almost certainly clock-label contamination (initial vs final application,
  whole utility wait) plus tiny n; the pooled rows are also internally inconsistent (E7).
- **IX submission→PTO.** Forum 11 cd ≈ DG Stats 11 cd but > SolarTRACE ≈3–8 cd: DG Stats
  "application received" can precede installation (2023 pre-NEM3 grandfathering spike
  105–156 d), so it is not SolarTRACE's final-IX clock; forum labels mix initial application
  (111 d) with final-document submission (18 d); the 09-20 −42% offset direction is not
  reproduced.
- **Installation→PTO.** Forum 74–100 cd vs ≈39–50 cd: mostly the 127/403 pending
  (right-censored) posts, treated as ignorable; completed-only raw median 42 cd agrees with
  admin. National mix and NEM3-era backlog add to it.
- **Final inspection→PTO.** Forum 14–19 cd; no directly published admin analogue; sum of
  SolarTRACE sub-phase medians is not a median of the sum.
- **Contract→PTO.** Forum 119–168 cd is inside the CA state range (≈91–214 cd by year); the
  09-29 vs t024 gap reflects two different evidence bases (E13), not a change.
- **Order→PTO** (128.7) below order→installation (138.9): different reporting groups, not a
  timeline (E7).
- **Burden intervals.** Contract→permit submission 41 cd vs SolarTRACE design phase ≈8–28 cd:
  forum "contract" often precedes site survey/redesign; only 6/21 CA; order→design and
  cancellation have no admin counterpart.

## 3. Errors and inconsistencies

- **E1 Legacy panel sampler presented as valid.** `runs/solar_forum_20260922/county_model/SAMPLER_REVIEW.md`
  ("Legacy sampler warning") finds `solar_panel/fit_hierarchy.py` omits the log-scale Jacobian
  and uses incompatible elasticity priors; its outputs are "not valid posterior results for the
  stated prior model". Still presented as findings: 2.39× AHJ spread and −2.3% elasticity
  (`docs/2026-09-20-solar-bayesian-results.md` §2, "well identified and robust"), the stringency
  coefficients and "7 percent of variance" (`docs/2026-09-21-solar-process-structure-results.md`
  l.188–219), and the 9.1/22.0 bd burden table (same doc l.242–252). None carry the warning.
- **E2 Internal contradictions in `2026-09-20-solar-bayesian-results.md`.** l.148 "eleven of them
  PG&E" vs `score_and_offset_v1.json` `E4_reporting_offset.by_utility` = PG&E 10, SCE 2;
  l.194 "no offset is detectable" vs the reported −42% [−59,−18] that excludes zero;
  l.180 "63 of 198" vs l.203 "66 of the 198" uncited documents; l.106 "43 usable" vs l.206
  "47 reach the comparison".
- **E3 Burden table interval and reference year.** `process_structure_20260921/solar_phase5/burden_table.json`
  `phase_clocks.inspection.ci90_business_days` = [22.04, 22.04] (zero width: the reference
  level's intercept uncertainty was dropped; should be ≈[20.6, 23.4]). Both 9.1 and 22.0 are one
  reference cell (**2017**, 0–10 kW PV-only, centred exposure; fit_primary year effects are
  2018–21 relative to 2017) with year effects forced common to both phases, yet presented as
  general phase times. Raw CA cell medians give an inspection share of 0.59–0.85 by year
  (2017: 4.25 vs 25 bd), so the "seven tenths" (process-structure doc l.247) is one point in a
  range, not a stable quantity.
- **E4 Reporting-offset direction reversed.** The 09-20 E4 (forum PTO 42% faster than admin, 12
  reports, 7/5 conversion; −19% without it) is not reproduced: 09-29 IX submission→PTO
  10.9 cd ≈ 7.8 bd vs SolarTRACE CA IOU 2–6 bd (forum slower), and ≈ DG Stats 11 cd (equal).
  E4 should not be cited as a source-bias estimate.
- **E5 One path, two files.** `runs/solar_panel_20260920/panel_v1.csv`: Stage A doc l.12/49
  describes 22,512 rows (2017–22); the file now has 30,016 rows (2017–24, 8 × 3,752), as
  `2026-09-20-solar-bayesian-results.md` l.15 says. Stage A counts do not describe the current file.
- **E6 County report reference year.** `county_model/timing_full001/summary.json`
  `manifest.config.reference_year` = 2024; 2024 has 18 CA 0–10 kW PV permit cells (median
  0.5 bd). County permit levels in `county_report001` (median across counties 1.9 bd) are
  extrapolations to a thin, fast year, not comparable to the 7 bd historical cell median.
  Not stated in `docs/2026-09-22-solar-county-model.md`.
- **E7 Pooled 09-29 rows read as one process are impossible.** Order→PTO 128.7 < order→install
  138.9; final inspection→IX submission 30.2 > final inspection→PTO 18.6; install→IX submission
  73.9 ≈ install→PTO 74.4 (`docs/2026-09-29-solar-adu-real-fit-results.md` l.97–110). The doc
  warns (l.112–118), but inspection→submission 30 cd vs admin 2–3 bd also indicates label
  contamination, not just selection.
- **E8 Pending-case assumption drives the forum/admin gap.** Install→PTO posterior 74.4 cd vs
  raw completed 42 cd, with 127/403 pending right-censored under "ignorable coarsening"
  (pooled_s1 `fit_results.json`). Headline tables do not say that the gap to admin is mainly
  this assumption.
- **E9 Crosswalk expansion is not "more of the same".** Re-admitted frames (#30) shift raw
  completed medians: permit submission→approval 17→28 cd, IX→PTO 9→14 cd. With ~80%
  declared-match precision (`docs/2026-09-29-audit-of-codex-model-cuts.md` l.22) and IX labels
  mixing initial application (t024 `initial_ix_application_to_pto` 111 d) with final submission,
  the 3,277/987 counts must not be refitted as-is for admin-comparable clocks.
- **E10 Admin summary number spans all years.** README / `GENERATED_SUMMARY_TABLE.md` IX→PTO
  33.1 d covers 1982–2026 incl. the 2023 pre-NEM3 backlog; 2017–2025 is 11 d (12/13/6 by IOU).
  Issued→final 64.7 (all years) vs 71 (2017–25). The table is labelled "sanity check only"
  but is the only place these appear.
- **E11 Denominator/label mismatches.** `docs/2026-09-30-solar-adu-admin-burden-execution.md`
  l.157 "8, 25, and 6" CA = parser-CA + county candidates; `burden_frames/fit_results.json`
  `geography.california_supported_by_parser` = 6/22/5. Crosswalk categories 1,879/3,509/87
  (audit l.22) vs 1,878/3,510/88 (09-30 doc l.47–48). "Same 15 historical clocks" (09-30 l.63)
  vs "14 frames" (09-29): 15 declared, 14 eligible (deposit→PTO at 11 contributors).
  09-23 bulk doc l.48 "2,667 adopted elapsed" vs l.83 "2,713" (pre/post adapter).
- **E12 Stale statements.** `docs/CURRENT_STATUS.md` l.13: `admin_model_inputs_20260930`
  "absent" — present locally (README 01:32). Concord broad-error 27.3%
  (`2026-09-23-solar-step-level-integration.md` l.299) superseded by 18.7% (l.305–311);
  joint8 pooled permit review 5.06 d (l.276) superseded by joint11 6.62 [3.35,12.99] d, which
  no doc reports.
- **E13 Two unmerged forum evidence bases.** Codex root-reviewed `timing_combined024`
  (576 claims, 329 contributors) vs the 968-packet `combined_s1` corpus (729 CLAUDE + 239 CODEX
  packets; 1,225 fitted). Same-clock medians differ (contract→PTO 119.4/13 vs 167.5/26;
  final docs→PTO 17.9 vs IX submission→PTO 10.9). Thread overlap is unmeasured; neither
  pooling nor choosing the nicer one is justified.
- **E14 Evaluation framing.** admin002: Bayes (51.01) also loses to the training-only simple
  interval (49.74), not only to the LLM (`admin002/comparison.json` `overall`); the county
  held-out score loses overall (−0.083). "No Bayes win" understates this: the admin hierarchy
  currently predicts held-out cells worse than a simple baseline.

## 4. What is valid now (citable with caveats)

1. **09-29 pooled forum clocks** (#26, 14 frames, 1,225 reports) and **09-30 burden frames**
   (#31, 125 reports): medians of selected-report distributions, cd, pooled national/unknown
   geography; pending posts assumed ignorable (E8); not California population clocks; rows are
   not additive (E7).
2. **09-29 CA-supported frames** (#27, 321 reports): development scope chosen after #26.
3. **County admin timing** (#13): cell-median variation, e.g. county spread (log) 0.268
   [0.181,0.387] permit, 0.292 [0.232,0.372] inspection; AHJ-within-county 0.685/0.276. Business
   days; zero-cap sensitivity shifts permit levels 18–24%; reference-year caveat (E6);
   held-out: no gain over simple baseline (#14).
4. **SolarTRACE descriptive medians** (§2) and **admin cohort medians 2017–2025** (§2, pre-fix
   version; completed-only; not de-duplicated).
5. **joint11 control** (#28): posteriors for the 11 reported journeys only; Concord
   report/model conflict unresolved; no population step counts.
6. **Negative results**: occupancy/structure fits failed (#7, #12, #19); no Bayes advantage in
   either same-evidence comparison (#21); county model does not beat the simple baseline (#14).
7. **timing024** (#11) only as a separate, parallel evidence base (E13).

Not citable: #4–#6, #8–#9 (E1–E4), #17 as a source/agency result, any whole-process sum.

## 5. What to fit next

**Recommendation: one admin-anchored source-offset fit for IX submission→PTO, by IOU.**

Why this clock: it is the only admin-comparable clock whose admin cell key is the utility, not
the AHJ. Of 527 admin-clock candidates, 286 are IX→PTO and **219 already carry a coded utility**
(vs 102 for permit submission→approval); all 13 cell-key-ready claims are IX→PTO. The year key
is the binding constraint (23 have one), and DG Stats makes year a nuisance that can be
integrated rather than matched: PGE/SCE/SDGE 2017–2025 cells hold ~1.69 M completed projects
(1.40 M of them 0–10 kW), with 0–10 kW cell medians of 3–23 d in every year
except 2023.

Design (declared before fitting):
- Admin reference: DG Stats histogram cohorts per IOU × year, 0–10 kW, 2017–2025,
  **excluding or separately programmed 2023 pre-NEM3 cells** (application precedes install;
  medians 105–156 d). Declared completed-only conditioning (no censored rows in this snapshot).
- Forum: the 09-30 crosswalk IX→PTO reports with a coded IOU, **re-split by endpoint** into
  final-document/PTO-request submission vs initial application (initial-application reports
  routed out or to their own program; cf. t024 111 d vs 18 d). Unknown year: declared mixture
  over 2017–2025 using DG Stats volumes (an assumption, stated), known year where coded.
- Model: forum source offset + Student-t reporting kernel relative to the exact cohorts
  (`source-offset-hierarchy/2`), same V6 priors/gates; one attempt, no extensions.
- Check: hold out 2024–2025 admin cells (or SDGE) and score forum-only vs forum+admin, with the
  existing same-evidence LLM baseline scorer.

Input files:
- `runs/admin_model_inputs_20260930/cohorts/solar_ix_submit_to_pto.csv` (bins; use the fixed
  version if Claude's de-dup/censoring update lands) and `projects/solar_dgstats.csv.gz` for hashes;
- `runs/solar_admin_integration_20260930/solar/comparison_candidates.jsonl` (286 IX candidates,
  219 with utility, 13 key-ready) and `solar/observations.json`;
- `runs/solar_admin_integration_20260930/legacy_pooled_accounting/fit_plan.json` (IX frame, 236)
  and `clock_crosswalk_review.jsonl` for the endpoint re-split.

Runner:
- The 09-29/09-30 forum-only fits were launched with
  `python -m pipeline.procbench.solar_panel.fit_bulk_forum --observations <observations.json> --out <dir> [--clock …] [--scope california_supported]`
  then `--fit --workers 4 --quadrature-size 128` (`runs/solar_admin_integration_20260930/run_burden_frames.sh`,
  sk3 `/dfs/scratch0/alexspan/solar_admin_integration_20260930/`). It calls
  `marginal_conditional_frames.run_marginal_frame`, which accepts exactly one conditional frame
  and **no histogram cohorts or source offsets**, so it cannot run this fit.
- The joint fit goes through `python -m pipeline.procbench.run_visit_hierarchy`, which already
  consumes `histogram_cohorts` (`cohort_histograms.py`) and the source-offset declaration
  (`source_offset_hierarchy.py`). Precedents: `--population-integration collapsed_single_phase_quadrature`
  with case reports plus admin population observations (`county_model/joint_phase_bridge002/fit004_collapsed_q256`,
  the one passing bridge), and histogram-only admin fits with `--population-integration analytic_single_phase --histogram-ridge-moves`
  (`runs/three_family_20260920/calfresh_histogram_ridge_fits_v1/positive46_base.process.json`).
  Missing piece: a small adapter writing that V6 `data.json` from the two inputs above
  (`pipeline/procbench/forum_admin_cells.py` currently prepares candidates only); confirm in
  preflight that histogram cohorts and collapsed forum cases coexist in one program.

Cheaper fallback if that adapter is out of budget: rerun the 15/13 accounting frames once with
`fit_bulk_forum` (the audit's pending task), but only after the IX and permit frames are
endpoint-split (E9); otherwise the rerun bakes label contamination into tighter intervals.
