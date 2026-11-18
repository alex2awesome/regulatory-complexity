# The toy-statute full-chain model: complete implementation record (2026-09-29)

Written for an independent code audit. It describes the whole approach as implemented in `pipeline/procbench/toy_statute/` (24 modules, ~5,050 lines) and `tests/test_toy_statute.py` (18 test functions, 32 cases), every implementation decision and why it was made, the data and run layout under `runs/toy_statute_20260926/`, what has been verified, and what is known to be wrong or untested. It supersedes nothing: the dated plans and results it cites are the primary records; this is the map.

Suggested audit order: §2 (chain and invariants) → §4 (process model) → §7 (reading layer) → §9 (known flaws) → §10 (reproduction).

**Update 2026-09-30.** The independent audit (`2026-09-29-toy-statute-full-chain-audit.md`) and the response (`2026-09-30-audit-response.md`) changed the following since this record was written: F1 joint outcome likelihood (`outcomes._joint_denied_unpermitted`); F2 completion selection in `Model._completed_gap_loglik` with the posting window published in `public_spec.json`; F3 `NFFT = 8192` with tail lumping and no renormalization; corrected `readings.score_readings` (P(yes | known reading), `exclude=`); normalized risk model; single unexplained-choice mass in the Stage-C grid; Dirichlet fee split on the default answer path; Stage-C assertion of a uniform Stage-B prior. Everything fitted before 2026-09-30 00:11 PDT used the earlier likelihood; the round-6 recovery experiment (`2026-09-30-toy-statute-round6-plan.md`) refits on the corrected one. Statute-agnosticism progressed: `validity_rules.py` (author and reader rule formats), `truth_package.py` (package-driven worlds, shared agencies), package-driven `estimands` roll-ups, `spec.use_design_space` restores the full hen catalog.

---

## 1. Purpose and scope

Goal (`docs/CORE_GOAL.md`): help a statute drafter answer *if I write this differently, how does the burden on the public change?* The frame is

```
statute text → decision model → per-jurisdiction process models → partial observations (→ outcomes)
```

The toy statute is a five-section invented law (Backyard Hen Keeping Act, `spec.STATUTE_TEXT`) used to build and test the machinery end to end against known truth before applying it to real permitting data. Everything in the toy is synthetic; no real jurisdiction is described.

Two methods answer identical estimands on identical evidence: a Bayesian model with an exact likelihood, and a tool-less LLM (Claude Opus, `claude -p --tools ""`, 3 repeats averaged). Both are scored against the generator's truth.

Rounds so far:

| Round | Date | Question | Plan / results |
|---|---|---|---|
| 1 | 09-26 | Does the machinery work at all? | `2026-09-26-toy-statute-plan.md`, `-results.md` |
| 2 | 09-26 | Scaling, adversarial world, milestones, LLM priors | `2026-09-26-toy-statute-round2-plan.md`, `-results.md` |
| Validity | 09-28 | Is a process valid under a decision model? | `process-validity.md` |
| Outcomes | 09-28 | Externalities: screening, deterrence, complaints | `2026-09-28-toy-statute-outcomes-plan.md`, `-results.md` |
| 3 / 3b | 09-28/29 | Composite reparameterization; Monte Carlo precision | `2026-09-28-toy-statute-round3-plan.md`, `-results.md` |
| 4 | 09-29 | The reading layer (text → decision model with uncertainty) | `2026-09-29-toy-statute-round4-plan.md`, `-results.md` |

Design rationale and literature: `2026-09-29-full-chain-model-proposal.md`, `2026-09-29-reading-layer-audit.md`, `LITERATURE.md`, `process-model-causal-frame.md`, `2026-09-26-complexity-measures-survey.md`.

---

## 2. The chain as implemented, and its invariants

```
L0 text            spec.STATUTE_TEXT (fixed)
L1 questions       validity.QUESTIONS Q1–Q5 (pre-registered) + residual          [readings.py]
L2 reading r_t     answers to Q1–Q5 per town; prior pooled from elicitors        [readings.py, parse_elicit.py, rsa_vagueness.py]
L3 decision model  D(r): required steps, order, deadline, authorized burdens      [validity.py]
L4 valid designs   V_r ⊂ design space, from checks C1–C6                          [validity.py, readings.validity_matrix]
L5 design S_t      p(S | r_t, ψ): choice-model family with slack ε                [readings.choice_logprob]
L6 parameters θ    step laws, town speeds, loop rates, observation noise           [model.py]
L7 observations    admin records, applicant reports, web pages                     [generate.py → model.py likelihood]
L8 outcomes        screening, deterrence, complaints, survey                        [outcomes.py]
```

**Invariants the auditor should check hold everywhere:**

1. **Truth-blindness.** `spec, grid, model, estimands, fit, llm_baseline, validity, outcomes, readings, rsa_vagueness` never import `truth_world`, `truth_w4` or `truth_eval`. Enforced statically by `test_fitter_and_baseline_never_import_truth`. Generators and scorers may read truth; nothing else may.
2. **Same estimands, same evidence.** Every LLM prompt is built from `evidence/` only (`llm_baseline.build_prompt`); every Bayesian answer is computed from the same directory. Scorers (`score.py`, `score_outcomes.py`, `readings.score_readings`) apply one rule to both.
3. **Discrete latents are summed, never sampled.** Designs S_t, case paths (k, h), unobserved outcome cells and readings r_t are enumerated exactly. Only continuous θ (and outcome parameters) are sampled.
4. **Predeclaration.** Each round's plan is written before its fits run; deviations are addenda, and failed fits are preserved and reported, never re-run silently (`runs/README.md` conventions).
5. **Statute package loader (added 2026-09-29 evening).** `spec.load_package(pkg)` replaces the module-level statute (text, d-steps, p-step catalog with per-step `events`, design space, mention→event map, admin milestone map, event order) so a second statute can be run without code changes to the model; step events now come from the catalog rather than literals in `chain()`, `generate.make_report` and `model.compile_town`. The hen statute round-trips through the loader with identical chains and identical log posterior on W4 (`test_hen_package_round_trip`). W0/W0m evidence regenerates byte-identically; only `public_spec.json` (catalog now carries events; S4 wording fix) and `truth/case_latents.json` (desk review emits `review_complete` since round 2) differ from the round-1 files. `validity.py`, `outcomes.py`, `estimands.py` roll-ups and `extended.py` still contain hen-specific rules and are the remaining work for statute-agnosticism (§9 item 13).
6. **Design-space switch.** `spec.use_design_space("menu6" | "full")` mutates module-level `STRUCTURES / STRUCTURE_IDS / STRUCTURE_TEXT / D2_REFINEMENT` in place. Default is `menu6` so rounds 1–3 reproduce byte-for-byte. `Model(design_space=...)` applies the switch before building, including in multiprocessing workers.

---

## 3. Public specification (`spec.py`)

Shared knowledge for the Bayesian model, the LLM and the generator.

- `STATUTE_TEXT`; `D_STEPS` (D1 application, concrete; D2 nuisance determination, vague; D3 issue/deny within 30 days, concrete); `DEADLINE_DAYS = 30`.
- P-step catalog `P_STEPS`: prepare, completeness_check, correction, neighbor_notice, comment_period, desk_review, hearing, site_inspection, decision_issue, each with the d-steps it serves, actor, and whether it carries days / hours / a fee item. `DAY_STEPS` (8) and `HOUR_STEPS` (4) fix parameter layout. `TOWN_SCALED` marks agency steps scaled by a town speed factor.
- Design space. `menu6`: S1 desk; S2 desk+inspection; S3 desk+inspection, decision issued at the inspection ("shared decision"); S4 notice→comment→desk→(hearing if objection); S5 = S4 + inspection; S6 = S5 with shared decision. `full` adds S7 inspection only, S8 inspection only shared, S9 notice only, S10 notice+inspection, S11 notice+inspection shared: every non-empty subset of the three safeguards in canonical serial order. Concurrent arrangements are *not* in the likelihood (see §9).
- `chain(s, k, h)`: the ordered day-steps of one case with the events that fire at step ends (`app_complete`, `notice_mailed`, `review_complete`, `hearing`, `inspection`, `decision`). `segment_counts(seq, e1, e2)` gives the step-count vector between two events; this is what turns an observed interval into a sum of step durations. `combos(s)`: paths (k ∈ 0..4 loops, h ∈ {0,1} if a hearing is possible).
- Report rounding convention (`report_unit_bins`): days < 14, weeks < 70, months otherwise.

Decision: the "14-day-style" wording leak in S4's description was removed in round 2 after it was found to give the LLM information the Bayesian model did not have (results round 2, Q5: it did not change the LLM's scores).

---

## 4. Process model (`grid.py`, `model.py`, `estimands.py`, `smc.py`, `fit.py`)

### 4.1 Likelihood

- Step durations are lognormal, discretized to integer days on a grid of length `grid.L_DAYS` (`grid.discretized_lognormal`). Sums of steps are exact convolutions via FFT (`grid.log_fft`, `grid.conv_from_counts`), with `test_fft_convolution_matches_direct` checking exactness.
- Per town, `compile_town` turns evidence into segment types: admin records (submission→decision totals; with milestones, exact gaps between logged events), applicant reports (rounded gaps between the events the applicant timed; mention indicators; hours; fees; pending reports censored at days-since-submission), and the web page (listed steps with false-positive/negative rates λ, ε_w).
- `Model.town_struct_loglik(theta, town)` returns log p(data_t | S, θ) for **every** design S. It sums over case paths with truncated-geometric loop weights and objection probability, mixes a 2% contamination component, and applies the report-rounding likelihood. `struct_posterior` normalizes with the structure prior (uniform by default; `struct_prior` hook for LLM-elicited priors).
- Milestone records (W0m/W1m) must match the design's milestone event set exactly, otherwise only the contamination component applies (a design that cannot produce the logged events is penalized).
- `loglik` sums over towns; `logpost` adds the prior.

### 4.2 Parameters and priors

`param_names(towns)`: `mu_<step>, lsig_<step>` (8 day-steps), `muh_<step>` (4) and shared `lsigh`, per town `la_t` (log speed), `lpinc_t` (logit incompleteness), `lqobj_t` (logit objection), and observation terms `lsig_r, lsig_rh, ldelta, leps, llam, lepsw`. 36 for 3 towns, 63 for 12. Priors are vague normals on transformed scales (`prior_spec`), with `prior_overrides` for LLM-elicited priors (mixnormal: widened ×1.5 and mixed 80/20 with the vague prior; `prior_elicit.py`).

**Decisions:**
- **Town centering** (`center_towns=True`, round 2): speeds constrained to sum to zero in log space, removing the non-identified trade-off between a common step scale and town speeds. This is what made W0/fit004 pass the gate.
- **Composite blocks** (round 3, `blocks=[("desk_review","decision_issue"),("neighbor_notice","comment_period")]`): for step pairs that are always adjacent without an observed boundary event, sample `blkT = log(E_a + E_b)` and `blkU = logit(E_a/(E_a+E_b))` instead of `mu_a, mu_b`, with E = exp(μ + σ²/2). |Jacobian| = 1, so the prior is evaluated on the base parameters unchanged (`to_base`, `from_base`, `logprior`). `test_block_reparameterization_is_exact_and_volume_preserving` checks the round trip, identical log-posterior and unit determinant. Same posterior, straighter ridge.
- **Fee split** (addendum R2-B): when several fee items share an unlisted residual, the split is drawn Dirichlet(1) per posterior draw (`fee_table(town, s, rng)`); the earlier equal split was overconfident. Answers recomputed as `answers_feefix.json`.

### 4.3 Sampler and gate (`smc.py`)

Tempered SMC: N particles from the prior; adaptive temperature steps chosen by bisection so the ESS after reweighting is half of N; systematic resampling; `n_moves` random-walk Metropolis moves per stage with the particle covariance, scale adapted toward 25% acceptance; 2 independent runs. Likelihood evaluations are parallelized with `ProcessPoolExecutor` (`_init` builds the model in each worker, including the design-space switch). Set `OMP_NUM_THREADS=1` etc.; BLAS oversubscription made round-1 fits 10× slower (addendum B).

`gate_v2` (round 2): for every parameter, rank R-hat between the two runs < 1.01; for parameters the data inform (posterior SD < 0.8 × prior SD), the standardized mean difference between runs < 0.1; every reported estimand's median agrees across runs within 0.2 SD. `compare_runs` uses exactly two runs. Round 3b (10,000 particles, otherwise identical) tests whether remaining failures are Monte Carlo noise: expected SMD shrink √(10000/3000) ≈ 1.8×; observed 1.7–3.2× in 5 of 6 fits, 0.9× in one (W1 with LLM priors), with the 5× and 25× fits still running at the time of writing.

Round-1 estimators (`fit.py`: MAP + Laplace + random-walk Metropolis) are retained for the record; they failed their gates and are not used.

### 4.4 Estimands (`estimands.py`)

Per town under its design: per-p-step days, hours, dollars; roll-ups to D1/D2/D3 (a shared inspection counts in full toward both D2 and D3); totals and quantiles; `deadline.p_miss` (complete application → decision > 30 days); complexity (expected p-step executions, applicant interactions, path entropy, CV of total days); the drafting counterfactual (§3 written concretely → every town on S1). Statute level: D2 implementation entropy, between-town spread, counterfactual deltas. `estimand_keys` is the canonical list both methods must answer.

`answers_from_draws` (in `fit.py`) computes all estimands per posterior draw, sampling each town's design from its exact structure posterior, and reports 5/50/95 quantiles. Extended survey measures (`extended.py`, M1–M11 from the complexity survey) are post-hoc and unscored against the LLM except in `scores_ext001`.

### 4.5 Identification diagnostic (`identify.py`)

Mean durations add along a chain, so an estimand is identified from interval means iff its gradient lies in the row space of the Jacobian of the observed interval means at the prior centre. Counts in W0: 5 identified estimands with totals only, 10 with milestones, 28 with a "review complete" date, 30 with "notice mailed". The diagnostic is conservative (the full likelihood also uses shapes and cross-town sharing). Rule stated throughout: a step's burden is linked to data only if its bounding events are observed or structural variation across towns separates it.

---

## 5. Worlds and generator (`truth_world.py`, `truth_w4.py`, `generate.py`)

All truth lives in these modules and in `runs/.../<world>/truth/`. `generate.py` writes `evidence/` (admin_records, reports, webpages, public_spec, and `outcomes.json` when the world has an outcome block), `truth/` (world.json, case latents, outcome latents), `heldout/` (cases for predictive scoring) and a SHA-256 manifest.

| World | Contents | Decision |
|---|---|---|
| W0 | 3 towns (Alder S1, Birch S3, Cedar S4), common-sense timings | baseline |
| W1 | adversarial timings (backlogged desk review, certified-mail notice, 30-day comment), different designs | tests methods that lean on typical practice |
| W0m, W1m | same seed and cases; admin records also log deemed-complete / inspection / hearing dates, exactly (no contamination) | tests the boundary-event rule |
| W0x5, W0x25 | same truth, 5× and 25× evidence, fresh draws | scaling |
| W0o, W0o_adv | W0 process world + outcome layer from a separate RNG stream (seed + 7919); process evidence byte-identical to W0 (verified), so W0/fit004's posterior is reused | externalities; W0o_adv confounds nuisance incidence with design choice |
| W4 | 12 towns; each town's reading drawn with P(yes) 0.6/0.35/0.9/0.8/0.5; design chosen by cost-softmax (τ = 15) among designs valid under its reading, slack ε = 0.05; speeds, loop rates and fees drawn per town; admin records in 6 towns | reading layer |

`generate.simulate_case` is a mechanistic per-case simulation (paths, durations, hours, fees); `make_report` applies the applicant's rounding and reporting noise; `make_webpage` the listing rates. `generate_outcomes` simulates each would-be keeper individually (nuisance, apply, per-safeguard flag, keep-anyway, complaint) and then aggregates; the outcome likelihood's Poisson-cell form follows from Poisson arrivals and independent thinning.

---

## 6. Validity layer (`validity.py`, `design_optimum.py`)

A design is a DAG of `Step`s (serves which d-steps; predecessors; mandated floor days; conditional; determines). `check(design, reading)` evaluates six constraints: C1 coverage (every d-step served), C2 sufficiency (evidence before the decision acceptable under the reading: plan / site / neighbour input), C3 precedence (determining steps finish before issuance), C4 deadline feasibility (mandated floors from completeness to decision ≤ 30 when the reading says the clock runs; best case, agency work instantaneous), C5 authority (each applicant burden traces to a clause, some only under a reading), C6 grounds (denial grounds authorized).

Readings are answers to `QUESTIONS` Q1–Q5 (desk suffices; neighbour input required; investigative power; clock includes D2; separate fees authorized). `ILLUSTRATIVE_PRIOR` is labelled illustrative and is *not* used by round 4 (which elicits priors). `menu_design(s)` translates a `spec` structure into a `Design` (design floors: 14-day comment, 10-day hearing notice; fee items excluded, added by `with_fees`); `concurrent_design(s)` builds concurrent variants for the validity analysis only.

`design_optimum.py` ranks designs valid under every reading (τ = 1) by posterior median burden, before and after statute edits (`EDITS`: safe harbour, notice required, clock tolled, single fee, investigation power).

**Decisions and known issues:** hearing attendance is treated as voluntary (authorized always). Stage A of round 4 found that all six LLM parses reject C6's premise (the statute lists no exhaustive denial grounds): C6 is a *reading*, not a skeleton element, and should become Q6 (addendum 4-A). In round 4 no design adds a denial ground, so V_r is unaffected.

---

## 7. Reading layer (`readings.py`, `parse_elicit.py`, `rsa_vagueness.py`)

### 7.1 Readings, prior, choice models

- `all_readings()`: the 32 answer vectors in fixed order; `reading_prior(qprobs, rho)` = product of per-question probabilities (independence across questions is a declared simplification) times admissibility, scaled to 1 − ρ, plus a residual reading with mass ρ. `admissible` is a hook (all 32 admissible in the toy).
- `validity_matrix()` → bool [32 × D] from `validity.check`.
- `pooled_question_probs(sources, lambdas)`: log-linear pool per question, probabilities clipped to [0.001, 0.999]. Sources: LLM direct probabilities (mean over K parses), LLM parse frequency (share of parses > 0.5; found degenerate 0/1 and dropped from P-pool2), RSA for Q1.
- `choice_logprob(V, model, eps, cost, tau, beta)` → log p(S | r) [33 × D]: `uniform` (1−ε)/|V_r| on valid designs; `cost` (1−ε)·softmax(−cost/τ) on valid designs; `risk` (1−ε)·softmax(β·#readings under which S is valid) on valid designs; ε/D everywhere; residual reading uniform over designs. A reading permitting nothing gets uniform mass.

### 7.2 Stage C: exact reweighting

`stage_c(L, prior, logchoice, kappa, n_w)` with `L[n, t, S] = log p(data_t | S, θ_n)` from `town_struct_logliks` over all pooled Stage-B particles. Stage B used a uniform design prior, so particle n's implicit town evidence is `base[n,t] = logsumexp_S L − log D`. Then

- `m[n,t,r] = logsumexp_S (L[n,t,S] + log p(S | r))`;
- κ = ∞: readings independent across towns from the prior; `ratio[n] = Σ_t (logsumexp_r (m + log prior) − base)`; particle weights ∝ exp(ratio);
- κ finite: `w_k ~ Dirichlet(κ·prior)`, n_w draws, the same with `log w_k` in place of `log prior`, weights over (n, k) jointly;
- outputs: per-town reading posterior E[w_r m_{n,t}(r) / Σ_r'], per-town design posterior Σ_r p(r | …) p(S | r, data_t), population weights, ESS, and `log_marginal_ratio` (log Z of the reading-and-choice prior relative to Stage B's uniform prior, used to compare choice models and κ).

`logchoice` may be [33×D] (shared), [N×33×D] (per particle) or [N×T×33×D] (per particle and town, used by the cost model, whose cost is `burden_indices(p, town, fees)`: a no-FFT expected-count × mean-duration burden index per design, with the town's fee table taken at its MAP design).

`run_stage_c` runs the predeclared grid: priors {P-flat, P-llm, P-pool, P-pool2} × ρ ∈ {0.05, 0.15 (P-pool only)} × choice {uniform, cost τ=15, cost τ=40, risk β=1} × ε ∈ {0.05, 0.15} × κ ∈ {∞, 3, 10, 30}; κ < ∞ runs use a 2,000-particle subsample and n_w = 50 for memory. Outputs `stage_c.json`; scoring in `scores.json` via `score_readings` (mean log score of the true reading, MAP accuracy, design log score and accuracy, per-question Brier).

`test_stage_c_recovers_reading_from_decisive_evidence` checks that overwhelming evidence for S1 drives Q1 → yes and Q2 → no, that S9 evidence yields the S9 design posterior, and that reading posteriors and population weights normalize. `test_reading_prior_and_choice_models_normalize` checks the prior sums to one with the residual and that every choice model has slack mass everywhere.

### 7.3 Elicitation (`parse_elicit.py`)

K tool-less Opus calls with the statute only. Each returns: presence and confidence for 7 pre-listed skeleton elements plus free additional elements; a list of ambiguities with a Massey et al. (2014) taxonomy type, the question raised, answers with probabilities, and a mapping to Q1–Q5 or "none"; direct P(yes) for Q1–Q5. `aggregate` produces element reliability (share present; correlated votes, labelled as such), the two question-prior sources, ambiguity counts by type, and the unmapped share (residual footing). Round 4: K = 6, $0.23–0.34 each.

### 7.4 RSA (`rsa_vagueness.py`)

Faithful discretized Lassiter–Goodman (2017): degree grid x ∈ (0, 10], 200 points; `degree_prior` lognormal indexed by density (median 2 / 3 / 4.5); θ uniform on the grid; utterances "nuisance" (x > θ) and null; L0 ∝ P(x)·[[u]]; S1 ∝ exp(α(log L0 − cost)) with α = 4, cost 1; L1 ∝ S1·P(x)·P(θ). Output: θ marginal. Mapping to Q1, a declared stipulation: P(Q1 = yes) = P(θ > x_plan), x_plan = the 70th percentile of the degree prior. Differences from the original: no fitting to judgments, one predicate, the object→rule reinterpretation (see the round-4 discussion). `test_rsa_threshold_shifts_with_degree_prior` checks the threshold rises with density.

---

## 8. Outcome layer (`outcomes.py`, `score_outcomes.py`)

Generative model per town: would-be keepers M ~ Poisson(m); nuisance with prob π (shared or per-town); applies with prob expit(α − β(B − 60)), B the burden index of the town's design; each safeguard present (desk, inspection, comment period) flags a nuisance with d_g, a harmless coop with f_g, any flag = denial; non-applicants and denied keep hens with prob u; complaints with k1 / k0; survey of n_s households with replacement. Observed cells (denials; verified/unfounded complaints at permitted and unpermitted addresses; approved-uncomplained) are independent Poisson by thinning, so the likelihood is exact; the one hidden cell is summed out inside the survey binomial over a ±10-SD window (`survey_loglik`, tested against the exact sum to 1e-4).

Inference is a **cut**: J = 24 process draws from W0/fit004 supply each town's design, fee table and burden indices for all designs; one vectorized tempered SMC per draw (`smc` in `outcomes.py`, N = 2,000, 10 moves), pooled equally; two runs; gate = worst parameter SMD < 0.1 and estimand median shift < 0.2 SD. Models `shared` (one π) and `hier` (non-centred logit-normal π_t). Estimands: per-safeguard d and f, u, β; per town π, detection, wrongful denial, nuisance share among permits, P(apply), operating nuisances / wrongful denials / unpermitted keepers per 100 would-be keepers, burden index; counterfactuals per design S1–S6.

Findings that shaped later decisions: design *differences* are recovered well while levels are not; the shared-π model breaks under confounding (coverage 0.65) and hier repairs it (0.92); β is biased low because the cut carries the process posterior's burden error (Birch 93 vs truth 82) into the deterrence slope, shown by a 10-replicate calibration check (`outcomes_replication.py`); catch and false-flag rates trade off in denial counts. Hence the proposal to fit outcomes jointly rather than cut, and the data-design recommendations (denial reasons; complaints matched to permit status).

---

## 9. Known flaws, limitations and untested parts

1. **Round-4 Stage-B fit failed its gate** (63 parameters, 3,000 particles; worst SMD 0.47). Design identification was unaffected (12/12 at 0.74–1.00) and Stage C rests mostly on it, but the cost model's burden indices come from an unconverged θ. Rerun at ≥ 10,000 particles is the obvious next step; not run.
2. **Generator flaw, Q5** (addendum 4-B): `truth_w4.py` draws fee schedules independently of the town's Q5 reading, so fees carry no information about Q5 in W4. Q5 excluded from headline scoring; fix by making fee items conditional on Q5.
3. **C6 is a parse, not text** (addendum 4-A). Becomes a question.
4. **Parse-frequency prior is degenerate**; P-pool reported as declared and P-pool2 added.
5. **Serial designs only**: the process likelihood has no parallel-branch kernel, so concurrent designs exist only in the validity and estimand layers (`extended.parallel_total_pmf`), not as hypotheses.
6. **Independence of questions in the reading prior**; readings independent across towns unless κ < ∞.
7. **Choice-model parameters ψ (τ, β, ε) are fixed hypotheses**, compared by marginal likelihood only; not inferred. Readings are identified only relative to the choice model.
8. **RSA step untested**: it contributed one prior number to Q1, which was unlearnable in W4; the object→rule and threshold→procedure mappings are stipulations.
9. **Elicitor calibration (λ, ρ) not learnable from one statute.**
10. **Toy stack ≠ V6.** None of this (blocks, milestones rule, validity, outcomes, readings) has been ported to the real-data V6 machinery.
11. **Illustrative reading prior in `validity.py`** is not an estimate; only τ = 1 results in `process-validity.md` are prior-free.
12. **The HTML page** (claude.ai artifact GVGscTDSXg7L8tqFpWKv9G) shows round-2 scores; round 3 changed the 25× result.
13. **Statute-agnosticism is partial.** `spec` loads a package, but `validity.py` (evidence sets, authorized burdens, grounds, floors, Q1–Q5), `outcomes.SAFEGUARDS`, the D1/D2/D3 roll-ups in `estimands.town_estimands`, and the hen-only analyses in `extended.py` / `identify.py` still hard-code hen names. A second statute (in preparation, `runs/toy_statute2_20260929/`) requires these to read from the package's `validity_rules`.

---

## 10. Reproduction

Environment: Python 3 with numpy, scipy, arviz; set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`; `PYTHONPATH` = repo root. Heavy fits ran on sk3 (`/dfs/scratch0/alexspan/toy_statute/code`, snapshots `toy_statute` for rounds ≤ 3b and `toy_statute_r4` for round 4). Launch scripts: `runs/toy_statute_20260926/round{2,3,3b,4}_sk3_launch.sh`, `outcomes_launch.sh`.

```
python -m pytest tests/test_toy_statute.py -q                                   # 32 cases
python -m pipeline.procbench.toy_statute.generate --world W0|W1|W0m|W1m|W0x5|W0x25|W0o|W0o_adv|W4 --out runs/toy_statute_20260926/<W>
python -m pipeline.procbench.toy_statute.smc --evidence .../W0/evidence --out .../W0/fit004 --runs 2 --particles 3000 --moves 30 --center-towns --gate v2 [--blocks desk_review+decision_issue,neighbor_notice+comment_period] [--prior-json .../llm_prior001/prior.json] [--design-space full]
python -m pipeline.procbench.toy_statute.llm_baseline --evidence .../evidence --out .../llm_xxx --repeats 3 --model opus [--extended|--outcomes|--readings --design-space full]
python -m pipeline.procbench.toy_statute.score --world .../W0 --answers name=path ... --out .../scores_xxx
python -m pipeline.procbench.toy_statute.validity --out .../validity001.json
python -m pipeline.procbench.toy_statute.design_optimum --burden .../W0/process_menu_burden.json --tau 1.0
python -m pipeline.procbench.toy_statute.outcomes fit --world-dir .../W0o --process-fit .../W0/fit004 --model shared|hier --out .../W0o/outfit_shared001
python -m pipeline.procbench.toy_statute.score_outcomes --world .../W0o --answers ... --out ...
python -m pipeline.procbench.toy_statute.parse_elicit --out .../W4/parse_elicit001 --k 6 --model opus
python -m pipeline.procbench.toy_statute.rsa_vagueness --out .../W4/rsa_q1_prior.json
python -m pipeline.procbench.toy_statute.readings --world-dir .../W4 --fit .../W4/fitB001 --elicit .../W4/parse_elicit001/aggregate.json --rsa .../W4/rsa_q1_prior.json --out .../W4/stage_c001
```

Every fit directory carries `manifest.json` (evidence hashes, code hashes, CLI args), `diagnostics.json` (gate), `particles_run*.npz` with arrays `X` (particles in the sampler's coordinates, i.e. block coordinates when `--blocks` was used), `LP` = **log prior** and `LL` = **log likelihood** (not the log posterior), and `answers*.json`. Verified 2026-09-29: `Model.loglik`/`Model.logprior` reproduce the stored `LL`/`LP` to 1e-13 for fit004, fitB001 (W0, W0m, W1m) and W4/fitB001 under current code. Preserve failed fits; never re-run into the same directory.

---

## 11. Results in one table

| Claim | Where | Status |
|---|---|---|
| Bayes identifies each town's design almost perfectly; LLM hedges | rounds 1–2 | robust across all worlds |
| Thin common-sense data: LLM wins burden estimands; 5–25× data or adversarial world: Bayes wins | round 2, round 3 (25×: 0.39 vs 0.53) | round-3 25× result reverses a round-2 sampler artefact |
| Per-step burden identified only with boundary events or structural variation | round 2, `identify.py` | stated rule; milestone worlds confirm |
| Composite reparameterization removes the identified ridges from failure lists; remaining failures mostly Monte Carlo noise | rounds 3, 3b | 3b 6/8 back; 1 genuine exception |
| Only notice-and-hearing designs valid under every reading; concurrency never changes validity; safe harbour makes S1 safe | `process-validity.md` | prior-free at τ = 1 |
| Design tradeoffs (burden vs nuisances) recovered; shared-π breaks under confounding; deterrence biased by the cut | outcomes results | one world per condition |
| Readings recoverable on design-constraining questions, prior-driven where practice is silent; risk-averse choice rejected; LLM over-attributes intent | round 4 | Stage-B gate failed; Q5 flaw |
