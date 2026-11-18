# Current status (living document -- replace, don't append history)

Last updated: 2026-09-30 (Codex: Solar/ADU; Claude owns toy status). Dated detail goes in dated docs.

## Repository and data (2026-11-17)
- Code: private GitHub repo `alex2awesome/regulatory-complexity`; branch `organize-20261117`, PR #1 into
  `main`. All code, tests and docs committed; data is gitignored.
- Data: private Hugging Face dataset `alex2awesome/regulatory-complexity-data`, one `.tar.gz` per top-level
  folder of `corpus/`, `benchmark/synth/worlds/`, `runs/` and the project's sk3 scratch folders
  (`scripts/archive_to_hf.py push`, resumable; log in `runs/hf_archive_20261117/`).

## Solar
- Acquisition (Claude, sk3): multi-topic census of 528 California + 31 national subreddits
  running, ~37M of ~89M items; batches -> `runs/solar_census_20260928/SOLAR_TRIAGE_LEDGER.md`.
- Burden-first work: `docs/2026-09-30-solar-adu-admin-burden-execution.md`.
  Two full-read packets: 60 threads / 686 comments, 35 episodes staged (not yet model-consumed).
- Working clock crosswalk raises old-clock eligibility 1,225 → 3,277 pooled reports; not semantic
  gold and not refitted. Three new burden-time fits (125 reports) pass numerical gates on sk3.
- Admin comparison prepared: 527 timing candidates, 13 with candidate cell keys. Claude-owned
  `admin_model_inputs_20260930` absent locally/sk3 at check; no admin-anchored/source-offset fit yet.

- 2026-09-30: all Solar results reconciled (`docs/2026-09-30-solar-results-reconciliation.md`);
  first forum-vs-admin calibration: forum reports of interconnection->PTO match DG Stats
  (reporting ratio 0.89 [0.62,1.15]; ~1.0 excluding 2023) -- `docs/2026-09-30-solar-interconnection-calibration.md`.

- 2026-10-01: Gemma cell keys for 555 forum claims (`runs/forum_cell_keys_20260930/`): Solar city+year
  13 -> 65 (26/33 in admin permit cells), utility+year 194 (all in DG Stats cells); ADU city+year 4 -> 20.
  Not yet used in a fit.

## ADU
- Collection done except census batches (pre-2019, national comments) and Houzz answers
  (1,113 recovered, unparsed). Triage ledger: `runs/adu_counties_20260926/TRIAGE_LEDGER.md`.
- Coded: 1,166 legacy episodes + Codex A1–A52 (1,281 threads). HCD letter categories complete
  (2026-09-29). Fits: 4 pooled clocks, 161 claims.
- New A54: 25 threads, 3 episodes + 3 additions, 42 action rows staged. Admin preparation retains
  475 readings; 28 admin-clock candidates, 4 with qualified geography/year candidates, none bound.
- Handoff: `docs/2026-09-29-adu-parsing-handoff-for-codex.md`.
- 2026-10-01 (Claude): admin APR fix -- HCD permit rows without a matching application and
  applications without permits were being dropped; now kept (APR ADU projects 108k -> 214k; ADU
  issued->final completed 96k -> 130k, app->issued censored 22k -> 57k). See
  `runs/admin_model_inputs_20260930/README.md` "Fix 4". City x requirement table joining all HCD
  letter findings + ordinance provisions + APR ministerial/discretionary labels to admin cohorts:
  `runs/adu_city_requirements_20260930/` (524 jurisdictions joined; covariates, not yet in a model).

## Real-data process fits (Claude, overnight 2026-10-01; Alex: "finish everything ... run the fast sped-up version")
- **2026-10-02 Codex refit complete, not validated:** repaired zero-mass PMFs and survival;
  native forum intervals, opt-out reporting mask/selection, exact labor/web-prior refresh.
  Fresh target `toy-process-v3-20261002`; no old-particle promotion. Four isolated sk3 CPU
  attempts (two seeds each for five-city Solar/ADU), 512 particles × 8 sweeps, all finished
  in 22–23 minutes. Normalization/cached-likelihood checks pass; paired R-hat fails
  (Solar 2.169, ADU 1.852). ADU whole-clock timing agrees but step decomposition does not.
  Scope/settings/results: `docs/2026-10-02-solar-adu-process-refit.md`.
  Root `/dfs/scratch0/alexspan/real_process_refit_20261002/`; no new posterior accepted.
- Engine-ready real evidence for the process engine `pipeline/procbench/toy_statute/`:
  `runs/real_process_20261001/{adu_permit,solar_permit,solar_interconnection}/` (467 / 19 / 27 towns;
  119k / 101k / 1.3M exact admin records + open cases + forum reports; ledgers count every record).
- Engine changes for real data (defaults bit-identical, 122 tests): web-listing mask, opt-in
  milestone contamination, float-boundary fix in `Model.combo_logw` (real-data crash).
- **Codex audit 2026-10-01 (`docs/2026-10-01-real-data-model-and-inference-audit.md`): no real-data fit is a
  validated posterior** -- ADU numerically invalid (zero-mass correction PMF), blocked sampler fails exact
  prior-only checks; headlines quarantined. Repair order in that doc, section 10.
- SMC fits on sk3 (`/dfs/scratch0/alexspan/real_process_20261001/runs/`); results doc
  `docs/2026-10-01-real-data-process-fits.md`. Interconnection: runs agree (PG&E/SCE extra-review design,
  SDG&E direct; correction probability jumps in 2023). Solar permits: totals fit, but independent runs
  (CPU and GPU) trapped in different local modes; no step-level claims. ADU: one run, misspecified
  (512-day step grid cap, stale open cases); held-out structure check weak. Next: respecify, rerun. Audit: `docs/2026-10-01-audit-of-codex-speedups.md`.
  Codex handoff (refers to code paths, not "V6"): `docs/2026-10-01-handoff-for-codex-real-data-model.md`.
- Extraction finished: SolarAPP+ 1,692 rows, Terner 730 (2021 survey Q22 bins), CPUC Rule 21 4,836 count
  rows (`runs/admin_pdf_extraction_20261001/`); permit linkage for 6 city sources
  (`runs/admin_model_inputs_20260930/linked_permits/`).

## Calibrated decision-tree posterior (Alex's central goal, 2026-10-05)
- Plan for sign-off, nothing built: `docs/2026-10-05-calibrated-decision-tree-posterior-plan.md` (engine archived at `runs/archive_toy_statute_v3_20261005/`, local only).

## Rule-following / letter-vs-spirit paper (Alex + Isabel, active since 2026-11-05)
- Full experiment plan, original hypotheses plus 2026-11-11 E0 amendment: `docs/2026-11-10-rule-following-experiment-plan.md`
  (three domains: percentile definitions / procurement / coding-agent sandbox; five-cell classifier; nine
  treatment arms mapped to resolutions of the rule-following paradox; complexity in six spaces; settled share
  s(c) as the rule-standard axis). Agent-layer complexity measures: `docs/complexity-metrics.md` section 6.
- Lit review (2026-10-14): `reports/Letter versus spirit in AI agents.md`.

### Implementation status (2026-11-11)

- Code: `benchmark/rulegap/` (spec, three-valued DSL, compile/classify, metrics, trees, two solvers, harness, CLI).
  Tests: `tests/test_rulegap.py`, `tests/test_rulegap_admissibility.py` (28 passed, offline).
  Original implementation plan: `~/.claude/plans/greedy-finding-moonbeam.md`.
- Specs: `specs/percentile_v1.yaml`, `procurement_v1.yaml`, `kripke_addition_v1.yaml`, `completion_30d_v1.yaml`;
  real case `real/percentile/spec.yaml` (SRE Workbook SLO line, sourced readings, rater packet in `e0/`).
- Historical metric tables: `runs/rulegap_20261111/measures/`. Completed original traces:
  `runs/rulegap_20261111/E1/` (1,680) and `E3/` (280). Preserve these original results.
- Codex correction at Alex's request: `runs/rulegap_20261111/revision_20261111/analysis/`.
  Re-scored all 1,960 episodes and joined 32 condition rows to nine complexity rows. Numerical report and
  verdict must match the same interpretation; 246 cells change. Primary table: `complexity_results.csv`.
  Candidate gaps are explicitly unvalidated; reference violations and purpose outcomes are separate.
- Interpretation-space scope: candidate / sourced / human-validated. Whole-program validation,
  explicit compatibility constraints, frozen catalogs, provenance and pairwise panel witnesses implemented.
  First E0 batch: nine `percentile_only` readings and eight procurement `defined_purchase` readings,
  requiring 51 judgments from three independent humans. Packets and blank forms:
  `runs/rulegap_20261111/revision_20261111/E0/`. Zero ratings submitted; no outreach performed.
  The source-backed real-percentile view now excludes authored extensions (10, not 20 candidates).
- No new model runs launched during the correction. A run without completed E0 now requires explicit
  `--exploratory`; validated runs require matching complete human ratings. The emergency-definition
  follow-up remains queued behind E0. Exact commands and acceptance policy: experiment plan section 10.
- Articulated components: a reading may contain named judgment leaves (`{judgment: name}`) whose value is a
  practice label or open. Open leaves make the verdict undefined; `articulated_share` reports how often.
- Update for Dan: Claude Doc https://claude.ai/artifact/VoBohT5pm13mMaJreCWwD2 (local copy
  `docs/2026-11-11-rule-following-update-for-dan.md`).
- Toy results (baseline 1,680 episodes, first drafting arms 280): `docs/2026-11-11-rulegap-toy-results.md`.
- Red-team trial (2026-11-11, exploratory, LLM judges in place of E0 humans): `docs/2026-11-11-rulegap-redteam-trial.md`,
  run `runs/rulegap_20261111/redteam/`. 194 model-written readings of 5 procurement drafts; 42 valid, all differ from I*,
  41 open a loophole; definitions shrink the loophole surface (19.5% open, 10.6% purchase defined, 0% all defined),
  branches grow it. Concise pilot doc (new account): https://claude.ai/artifact/M1gg9Ph1uD9Phb4ZeFcYfT; slides
  https://claude.ai/artifact/EpsbUix5SXUuvif84ctWrN. The earlier docs live under the other claude.ai account.
- Agent reading studies (2026-11-11, exploratory): `docs/2026-11-11-rulegap-agent-readings.md`. tau2 airline
  "modify" clause and a Model Spec letter-and-spirit study; Luna, Claude, Gemma 4 31B (sk3). Behavior identifies
  the reading: Luna acts on the letter, Gemma on whatever serves the customer; loopholes mostly when the customer
  proposes them; Luna acts against its own judge verdict (14 of 16 own traces not permitted). Claude airline arm
  failed: 50 platform-safeguard refusals in 60 episodes, not rerun. Gemma activation probe designed, not run.
- Question-asking interpreter pilot (2026-11-17, exploratory): `docs/2026-11-17-question-tree-pilot.md`,
  run `runs/rulegap_20261117/question_tree/`. Models raise the planted term questions (procurement 3-4 of 4 per
  sample) but miss implied procedure (hens act 0-4 of 6; two never raised). Draft assumption set in the doc.
  Share package for Isabel: `benchmark/rulegap/README.md` + `python -m benchmark.rulegap.export_share DEST`
  (standalone tests 36 pass, 1 skip); not pushed, no git remote, destination pending from Alex.
- Pilot, plan and timeline with decisions pending from Alex (models and spend, raters, API keys):
  Claude Doc https://claude.ai/artifact/QbY5J5dvWKY2SaQCn17PK4. Baseline at full scale targeted Nov 16 to 20.
- Not done: remaining E3 arms, grammar-generated readings, mechanical elicited-reading probe, Phase B real cases
  (procurement text, ADU clauses, coding sandbox; tau2 airline has a first agent study), E0 human ratings.

## Toy statute (full-chain model; Alex's active thread 2026-09-26 → 09-30)
- Audit `docs/2026-09-29-toy-statute-full-chain-audit.md` (independent) found likelihood defects F1–F3 and
  scoring defects F6–F8; all fixed and counterexample-tested (39 tests), see `docs/2026-09-30-audit-response.md`.
  Withdrawn: "risk aversion rejected"; round-4 reading scores re-scored (Bayes −2.13 vs LLM −2.67 on Q1–Q4);
  outcome-layer claims suspended pending refit. Implementation record: `docs/2026-09-29-toy-statute-full-chain-implementation.md`.
- Round 6 v2 (LIVE, sk3 since 03:38 PDT 09-30; launcher `runs/toy_statute2_20260929/round6v2_sk3_launch.sh`,
  snapshot `toy_statute_v2`, target toy-process-v2-20260930): W0, W0m, W4, HEN2, HK1b_v2, HK2_v2 -> `fitE001`,
  same settings as round 6 (10k particles, 30 moves, 2 runs, seed 20261001). All six preflights passed. Kitchen
  evidence regenerated (same seeds, identical hidden worlds). Kitchen LLM baselines used old evidence: rerun needed.
  Old-target round-6 `fitD001` jobs STOPPED 03:37 (logs kept; only W0 run0 particles). Log `sk3_round6v2.log`.
- Codex response-audit repairs are now LOCAL PRODUCTION CODE: `docs/2026-09-30-toy-statute-audit-repairs.md`.
  R1/R3 guards retained and completed; R2 catalog fees/burden, R4 exact event/mask likelihood, R5 uncapped sums,
  R6 conditional survey mixture implemented. 66 focused tests; 24-point reference difference <= 4.55e-13.
  Per-likelihood runtime 2.55–3.42× faster than pre-edit code; new target `toy-process-v2-20260930`.
  Remote round-6 snapshot/jobs UNCHANGED. Old particles cannot silently enter new Stage C/outcome cuts;
  R4/R5 require new fits. Old kitchen fee evidence remains defective and needs a new versioned corpus.
  No new posterior recovery/convergence result is claimed; fee-reading likelihood is still absent.
- Single-path refactor complete locally: `docs/2026-09-30-toy-statute-single-path-refactor.md`.
  Removed legacy/reference production backends and old MAP/MCMC process fitter; `fit` delegates to SMC.
  68 focused tests; corrected-target before/after likelihoods/answers unchanged in bounded checks.
  Runtime gain retained (~2.5–3.4× versus buggy pre-repair code). Test-only oracles and historical snapshots retained.
- HTML: `docs/html/hen-permit.html` is the durable copy (Version 10 content; older versions in
  `docs/html/archive/`). The published link https://claude.ai/artifact/NX6rH7dFsrCpGMxLYGiqEK was reported
  missing on 2026-10-06 (as were the two earlier links); republish from the local file when needed.
- Hypothesis-space experiment (Alex's pick): workflow `docs/2026-09-30-uncertain-hypothesis-space-workflow.md`,
  Codex plan `docs/2026-09-30-hypothesis-space-plan.md`. Claude readers (Opus/Sonnet x neutral/meta, 4 per statute)
  in `runs/toy_statute2_20260929/readers_hs001/<statute>/claude_*`; it uses the fitE001 Stage-B particles.
- Hypothesis-space implementation complete; empirical comparison pending (`docs/2026-09-30-hypothesis-space-results.md`).
  16 usable readers including the inherited kitchen reader; eight distinct classes per statute. Shared-H BMA,
  joint burden weights, public-only runner and separate evaluator; 89 focused tests pass. No completed v2 particles
  at the bounded check; uninformative-likelihood mechanics only, no world recovery claim or polling loop.
- Exact scaling pass: `docs/2026-09-30-scaling-inference-review.md`. Joint timing/span reuse; optional saved
  Stage-B town/design likelihoods for Stage C. 94 focused tests; zero before/after likelihood difference at
  18 held-world points (+4 duplicate-fixture points). Ordinary-corpus runtime gain modest (1.01–1.07×);
  repeated-report fixture 2.33×. No sampler/prior/particle-budget change or running-job modification.
  Follow-up: `docs/2026-09-30-jax-gpu-pilot.md`. 12/50/200/500-town CPU benchmark complete;
  opt-in cached blocked SMC sweeps implemented, centered paired speeds + raw-mean update, 99 focused tests.
  At 500 towns/11 designs: full evaluation 1.03 s, cached complete sweep 4.20 s;
  naive local sweep projected 511 s (not an ESS/speedup comparison). Cache error <=5.46e-12.
  Experimental float64 JAX/CUDA-13 pilot completed on W0: 16/128/512 likelihood batches 45.7/166.9/206.1×
  faster than serial NumPy/SciPy (warm, single GPU; NOT fit speedups), error <=2.27e-13.
  JAX CPU lowering is slower. GPU HMC/RW chains and two 16-particle SMC runs per kernel executed;
  chains fail convergence and SMC loses ancestry. No sampler/default promotion; existing fits unchanged.
  All receipts, failures and next comparison in the GPU execution record. Use DFS for future uv caches:
  sk3 local cache filesystem nearly full; CUDA-13 retry succeeded with task-specific DFS cache.
- W0 posterior-equivalence follow-up **complete**: `docs/2026-09-30-posterior-equivalence.md`.
  Two full GPU-backed production SMC runs (10k particles, 30 moves) match the completed CPU
  `W0/fitE001` reference on all 36 parameters, design probabilities, timing, expected executions
  and relative speeds. Sampling 5.49 min vs historical CPU 64.15 min (different environments/load;
  not an equal-resource benchmark). Four longer GPU HMC chains also pass: max rank R-hat 1.0014,
  min bulk/tail ESS 10,027/6,224, matching posterior intervals. Blocked CPU chains still fail
  (R-hat 1.0348; bulk/tail ESS 106/84). Earlier tiny pilot failures remain historical results.
  11 targeted regression tests pass; no sampler/default promotion or other-world certification.
- Configurable acceleration (Codex, 2026-10-01): `docs/2026-09-30-configurable-inference-speedups.md`.
  Implemented exact whole-admin multiplicities, JAX town buckets, device-resident RW/HMC within the
  shared SMC driver, and manifest-bound model/execution JSON. CPU default unchanged. Numerical checks
  pass; 118 local tests + 3 optional remote JAX tests. Bucketing alone improves warm 50-town evaluation
  8.69x in the replicated public fixture; 500-town error <=2.91e-11. Two full device RW fits match pooled
  CPU parameter/derived posteriors, but narrowly FAIL their own between-run spread-quantile gate
  (0.2167 SD versus 0.2). Runtime 6.08 min combined, not faster than prior GPU 5.49 min. HMC-SMC pair
  COMPLETE: all declared parameter/derived posterior comparisons pass, without reference-fit covariance,
  but takes 49.09 min combined. Validated W0 option, no demonstrated speed win/default promotion.
  No general Solar/ADU adapter or large-town posterior-mixing claim. All outputs copied locally.
- Blind process round (Claude, Alex 09-30): plan `docs/2026-09-30-toy-statute-blind-process-plan.md`; world
  `runs/toy_statute3_20260930/HEN3` (out-of-catalogue signature step; S12/S13 in 4 towns), free-text render
  (`toy_statute/render_text.py`), blind compiler `toy_statute/blind_process.py`. Both builders recovered
  all 10 true steps (notice+comment merged); extraction near-exact on templated text. Oracle fit DONE
  (`HEN3/fit_oracle001`, 3.1 h: MAP 13/14, total-days MAE 3.0 d, but v2 gate FAILS, R-hat 1.33, on the
  notice/comment split). Blind fit attempt 1 failed preflight (one prior draw -inf on exact milestone
  gaps; log kept `blind001/fit_blind001_attempt1.log`); `smc.py` preflight now tries up to 20 prior
  draws (model unchanged); attempt 2 DONE (`blind001/fit_blind002`, 4.7 h): MAP 12/14 vs oracle 13/14,
  all four out-of-menu towns recovered, total-days MAE 2.8 d (oracle 3.0), coverage 13/14 both; the extra
  miss (Basalt) is a menu-order gap (no desk-before-hearing design), the other (Emery) is shared with the
  oracle. Gate v2 fails in both (blind milder: builder merged notice+comment). Blind text-only skeleton
  (Opus/Sonnet) adds a Sec. 1 eligibility determination no process step serves; roll-up recomputed from the
  blind particles (`rechunk_answers.py`). Results doc `docs/2026-09-30-toy-statute-blind-process-results.md`.
- Next (scientific-fit track): Stage C + scoring for completed fitE001 runs, hypothesis-space BMA,
  outcome refits, round 7 joint shared agencies. W0 is available; the equivalence task does not
  certify W0m/W4, which failed parts of their existing gates.

## Side notes
- Procurement timing (for Dan's students, 2026-10-15): `docs/2026-10-15-procurement-timing-measurement-ideas.md`.
  No California cycle-time data published; dates live in Cal eProcure events, SCPRS, FI$Cal (internal),
  Caltrans awards; threshold bunching and discontinuity designs need no timing. §4 (2026-10-19) = joinability onto
  the students' SCPRS scrape. Acquisition run `runs/procurement_20261021/` (2026-10-21, Alex: download everything
  with timing): FI$Cal SCPRS bulk export + CSCR event listing/details running on sk3 scratch; open-data PO 2012-15,
  Caltrans NOI (Wayback), DGS NIA PDFs, late-payment report pulled/pulling on the laptop. See its README.md.

## Parked
CalFresh, CCW, synthetic benchmark (history in `docs/2026-09-29-claude-md-checkpoint-archive.md`).
