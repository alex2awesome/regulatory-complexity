# Audit: real-data process fits, inference, and the speedup review

2026-10-01. Audit only: no production changes, refits, job cancellation, input repairs, or commits.

## Verdict

The ingestion and execution work is substantial, and the results document correctly withholds Solar step-level conclusions. But **none of the three real-data process packages currently has a validated full posterior**. Interconnection is not an exception. There are numerical and sampling failures in addition to weak identification and imperfect observation semantics.

Two new findings are decisive:

1. **The completed ADU run is numerically invalid.** Every one of its 256 saved particles produces an all-zero correction-duration PMF. The survival calculation treats missing numerical probability mass as survival, creating an unintended mechanism for permanently open cases.
2. **The blocked runs fail an exact, truth-free posterior check.** Parameters with no observations have independent priors and must retain those priors. In ADU, one such parameter's posterior mean is 11.87 prior standard deviations from its prior mean. Solar blocked runs also fail badly. Solar HMC passes this check, but agreement among its three seeds does not establish coverage of other process configurations.

Accordingly, I would not promote the interconnection review-step/correction claims, the ADU posterior, or any intrinsic-agency-capability estimate. The administrative timing summaries and exploratory reporting-offset calculations remain useful with their stated population and clock limitations. The previous numerical speedups are not disproved by this: evaluating a faulty or misspecified target faster and more consistently is different from validating that target or obtaining a representative posterior sample.

## Scope and receipts

Reviewed the three requested documents, their input builders, packages and configuration, the process likelihood, blocked moves, SMC and JAX implementation, answer/scoring paths, standalone source-offset fit, and available saved particles, launch manifests and logs. Also reviewed the linked execution handoff and earlier speedup evidence. This is **not** a new document-by-document audit of the raw acquisition corpus or a re-audit of every historical model generation.

Primary documents:

- [Results](2026-10-01-real-data-process-fits.md)
- [Claude's speedup audit](2026-10-01-audit-of-codex-speedups.md)
- [Real-data handoff](2026-10-01-handoff-for-codex-real-data-model.md)
- [Package assumptions and inventory](../runs/real_process_20261001/README.md)

Audit receipts: [checks.json](../runs/real_process_audit_20261001/checks.json), [numerical_probes.json](../runs/real_process_audit_20261001/numerical_probes.json), and their scripts in [the audit directory](../runs/real_process_audit_20261001/). The receipts include particle hashes and the checked source hashes. Scoped copies of remote particles, manifests, summaries and logs are there; no hidden synthetic truth was used. Remote originals are under `/dfs/scratch0/alexspan/real_process_20261001/` on sk3.

One focused test invocation: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest tests/test_toy_statute*.py -q` → **125 passed, 1 skipped**, in 8.30 seconds. The skipped module needs local JAX. I did not rerun GPU sampling. Passing these tests does not cover the failures below.

The run inventory is a snapshot. At **21:07 UTC / 14:07 PDT**, Claude's replacement `adu_fit004_run1` was at stage 7, beta 0.00042, with 160 workers; ADU single-run postprocessing was also running. I did not interfere with either. The earlier completed particles, not this unfinished replacement, are the basis of the ADU findings.

## 1. What actually ran, and what it establishes

| Package / sampler | Completed saved ensembles checked | Tempering stages | Present conclusion |
|---|---:|---|---|
| ADU, blocked CPU | `adu_fit003_run0`: 256 particles, 1,423 coordinates | 160 | Invalid PMFs and severe prior-only control failure; no validated posterior |
| Solar permits, blocked CPU | `solar_fit002_run0/1/2`: 1,024 each, 79 coordinates | 39 / 38 / 39 | Different configurations; prior-only controls fail |
| Solar permits, GPU HMC | `solar_jaxhmc002/003/004`: 1,024 each | 35 each | Prior-only controls good; same configuration across these seeds; global mode coverage unestablished |
| Interconnection, blocked CPU | `ix_fit001_run0/1`: 512 each, 98 coordinates | 81 each | Both select the same designs, but fail parameter and estimand agreement; not certified |

`adu_fit003_run1` crashed around stage 120 on a shared mention-probability floating-point boundary. The replacement uses a subsequent boundary fix. Earlier stopped fits and partial Solar attempts should remain historical attempts, not additional independent posterior replications.

The saved comparison files show:

- Solar CPU pair: **45 parameter failures, 336 estimand failures**, worst estimand median difference **37.25 posterior-SD units** under the existing gate.
- Interconnection pair: **33 parameter failures, 217 estimand failures**, worst estimand difference **3.29 SD**, largest particle-based R-hat **1.361**.
- ADU single-run comparison correctly says `pass: null`; no between-run assessment exists for that completed run.

The 100-draw answer budget inflates noise in the estimand gate; see Section 5. It does not explain the large parameter differences or the exact-prior failures.

The nine completed saved ensembles above have launch manifests but no final `manifest.json`, consistent with stopping the driver after saving particles and before its expensive closeout. That preserves useful results, but it also leaves diagnostics/provenance closure incomplete.

## 2. Blocking numerical failure: ADU has zero-mass duration distributions

Location: [grid.discretized_lognormal](../pipeline/procbench/toy_statute/grid.py), also mirrored by `jax_backend.discretized`; downstream `Model.town_struct_loglik_from_params` in [model.py](../pipeline/procbench/toy_statute/model.py).

The intended step distribution is a lognormal rounded to days and conditioned to fit the 0–511 day grid. The code computes differences of normal CDFs and divides by their sum. When all CDF values underflow to zero, it instead divides by 1 and returns **all zeros**, not a probability distribution.

This is not just a constructed edge case:

- In **256/256 saved ADU particles**, the correction-step distribution has total mass exactly 0.
- A bounded eight-particle check across all 467 jurisdictions found **3,736 zero-mass correction PMFs**: every checked town/draw combination. Other checked step PMFs normalized.
- The posterior median of the underlying correction `exp(mu)` is about **2.77 million days**; its small spread places all representable-grid mass below floating-point range.
- The shared grid file has the same hash as the ADU launch snapshot. This is not a later postprocessing change.

For a normalized distribution, `1 - cumsum(pmf)[N]` is survival. For a deficient distribution with mass `m < 1`, it approaches `1-m`, not zero. All paths containing a correction acquire zero mass here. Their mixture weight is then incorrectly available as perpetual survival in the pending-case likelihood. The contamination option does not repair that missing normalization.

For example, the missing positive-correction mixture weight has median about **0.238 in Agoura Hills** and **0.238 in San Francisco** in this ensemble. These are numerical residual masses, **not inferred abandonment rates**. The calculation explains a mechanism by which the model can accommodate old open records through an unintended numerical defect. I have not quantified how much of its total likelihood gain comes from this mechanism.

Necessary repair before an ADU refit: stable log-CDF/log-difference evaluation of the *same truncated distribution*, normalization checks at proposed and retained states, and rejection/error rather than silently accepting an all-zero PMF. Survival needs stable tail evaluation too. Simply refreshing priors, increasing particle counts, or adding more contamination will not fix this target defect. A mathematical truncation may itself be inappropriate for some real steps, but changing the truncation is a separate scientific decision.

The earlier speedup tests compared implementations on ordinary parameter regions. CPU/JAX agreement there cannot certify normalized distributions at these extreme saved real-data states. This is a gap in the shared machinery, including my earlier validation scope.

## 3. Blocking sampling failure: parameters with a known exact posterior are wrong

All three packages contain **zero hour observations**. Therefore the independent `muh_*`, `lsigh`, and `lsig_rh` coordinates do not enter their likelihoods. Solar and interconnection also have zero observed web steps, so `llam` and `lepsw` are additional prior-only controls.

If `u` is such a coordinate and `v` denotes all the others, the model factorizes as

\[
p(u,v\mid y)\propto p(u)p(v)L(y\mid v),\qquad p(u\mid y)=p(u).
\]

This holds even if the duration model is misspecified. It needs no synthetic truth, external data, or agency assumptions. No composite parameter blocks were used in the checked launches. Code inspection establishes likelihood independence; the numerical probe also perturbed all applicable controls at a saved Solar point and an ADU point and got **exactly zero change** in the selected town's structure likelihoods.

The receipt reports mean displacement in prior-SD units and posterior/prior SD ratio:

| Ensemble / coordinate | Mean displacement | SD ratio | Interpretation |
|---|---:|---:|---|
| ADU `muh_prepare` | −6.706 | 0.404 | Impossible to interpret as data learning |
| ADU `muh_correction` | −6.796 | 0.494 | Same |
| ADU `lsig_rh` | +11.872 | 0.689 | Severe failure on an exactly known marginal |
| Solar CPU run 1 `muh_prepare` | +2.214 | 0.563 | Inadequate mixing/particle diversity |
| Solar CPU run 2 `lsig_rh` | −3.079 | see receipt | Same |
| Interconnection prior-only controls | Up to about 0.46 SD | As low as about 0.65 | Also materially distorted |
| Solar HMC controls, all three runs | Largest absolute shift about 0.063 SD | About 0.958–1.031 | Good on this diagnostic, not a global convergence certificate |

For normally distributed controls these moments are analytic. For logit-Beta controls, the reference moments use digamma/trigamma identities, not another fitted sampler.

The evidence supports a **finite-budget sampling failure**. It does not by itself prove a detailed-balance error in blocked MH. Shared parameters receive one joint proposal per sweep while hundreds of local proposals determine the aggregate acceptance rate. Shared covariance is estimated from repeatedly resampled particles. That combination can preserve collapsed or displaced shared coordinates, and overall acceptance can look healthy while shared movement is poor. This mechanism is plausible from the code; separate shared/local acceptance and genealogy were not saved well enough to quantify it here.

Unobserved hour parameters should be analytically marginalized from the sampling state or independently refreshed from their priors. Keep their outputs explicitly prior-driven if retained. This is an exact efficiency improvement, but **repairing these easy controls alone would not prove that the informed timing parameters mix**.

## 4. Structural and observation-model claims exceed what was fitted

### 4.1 The design menu is authored, not discovered

The packages offer ADU three designs, Solar permits two, and interconnection two. They share a hard-coded review/correction loop. The sampler averages over those catalog alternatives; it does not infer an unrestricted sequence of agencies, filings, branches and dependencies.

Interconnection has abundant received / app-complete / approved dates, but no observed `review_complete` milestone for the added desk-review step. Choosing I2 rather than I1 therefore selects a decomposition of the post-complete duration distribution under the menu and shared parameter assumptions. It is **not direct evidence that PG&E and SCE perform a particular extra administrative task that SDG&E omits**. A more flexible one-phase distribution, case mix, or a different menu could change that answer.

The results acknowledge that "correction" may absorb waiting for installation. That caveat should govern the headline too. `decision_issue` in the interconnection package includes waiting for customer sign-off but is labelled agency work; its time is not automatically agency-caused delay.

Each permit jurisdiction has one design across the pooled historical window. Case-level ministerial/discretionary variation and policy-era changes are not modeled. APR case labels and permit revision links have not yet supplied the missing case-level structure likelihood.

### 4.2 The correction parameter is mislabeled

For maximum `K=5`, [grid.truncated_geometric](../pipeline/procbench/toy_statute/grid.py) implements

\[
P(N=k\mid p)=\frac{p^k}{\sum_{j=0}^{K}p^j},\quad 0\leq k\leq K.
\]

This is a geometric distribution **conditioned on not exceeding K**, not a loop forced to stop after K failures. Its observed continuation probability is not simply `p` at every round. In the limit `p→1`, it is uniform over 0,…,5:

\[
P(N\geq1)\to5/6,\qquad E[N]\to2.5.
\]

Thus `pinc≈1` does **not** mean almost every review returns corrections. Report probabilities/counts from the actual distribution, label `pinc` as a latent geometric tilt, or change the model to an explicitly intended stopping mechanism. Do not silently substitute a different distribution.

There is also a remaining implementation hole: the shared `truncated_geometric(1,5)` returns NaNs. The new likelihood branch handles this limit, but prediction/estimand paths still call the shared helper. I reproduced the boundary failure; I did **not** find evidence that this particular limit corrupted the saved real-data answers, whose checked correction logits were below that rounding threshold.

### 4.3 The reported step median is often not the modeled step median

[combine_runs.py](../runs/real_process_20261001/combine_runs.py) reports `exp(mu)` as `median_days_at_average_speed`. That is the untruncated lognormal median, not generally the median of the truncated, rounded daily PMF used by the likelihood.

For interconnection, a reported 0.19-day completeness median corresponds to a whole-day model concentrated enough that its checked discrete median is **0 days**. In Solar HMC, notice/comment underlying medians around 40–50 days coexist with checked discrete medians of **0 days**, owing to extremely broad spreads and truncation. These comparisons use 16 evenly spaced saved particles per run; they are diagnostic comparisons, not freshly converged posterior estimates. ADU's zero PMF has no median at all; a search routine returning 512 is an invalid-distribution sentinel, not a duration.

Compute summaries from the actual modeled distributions and distinguish a parameter median, a population median, and a posterior predictive interval.

### 4.4 Forum intervals are not preserved

Builders take the midpoint of an extracted interval, choose a synthetic day/week/month reporting unit, and round it. The likelihood consumes that recoded report, not the retained `native` bounds.

Examples from actual inputs:

- Solar `[28,56]` days becomes a rounded-report interval `[38.5,45.5]` days.
- Interconnection `[0,7]` becomes `[3.5,4.5]` days.
- All 12 completed ADU reports, 25 Solar reports, and 60 interconnection reports have altered interval endpoints. In 10, 20, and 48 respectively, the encoded interval excludes some of the original interval. This count includes small endpoint shifts; the examples above show the more consequential narrowing.

The report-noise kernel adds uncertainty afterward, but it does not restore the stated observation interval. A direct interval likelihood is the appropriate adapter. There is also a latent status bug in `prepare_ix_forum.py`: any absent upper bound becomes "pending", even if an eventual input is a completed lower-bound report. **None of the current 68 included interconnection reports triggered that bug**; their eight pending rows were genuinely labelled pending upstream.

### 4.5 Synthetic reporting and selection assumptions remain active

Every included completed forum case is emitted as one submitted→decision gap. Yet the likelihood retains fixed `p_total_only=0.2`, `p_time_mentioned_event=0.7` and scores the absence of intermediate timestamps. An adapter that intentionally omits intermediate timing cannot treat that omission as an observed decision by the author. This can change structure probabilities.

Completed forum reports also retain the toy posting model `C ~ Uniform{1,…,1095}`. The likelihood includes `P(C≥T)` inside its duration integral. That is meaningful for the declared joint sampling scheme, not automatically for a harvested, screened, often completion-selected forum corpus. The actual acquisition/selection frame and conditioning need to be specified before treating this as an empirically calibrated selection correction.

Pending forum reports use survival at a reported age; unknown locations and partial clocks remain excluded rather than integrated as uncertain geography or partial observations. These are disclosed limitations, but they contradict an expansive reading of "everything is model-ready."

### 4.6 Administrative censoring, eras and source populations are unfinished

Completed and genuinely open cases can support a survival model. But LADBS issued-only and DG Stats resolved-only populations are already selected by outcome, and recent completed cohorts are truncated by the extraction window. The current completed likelihood does not condition on those inclusion mechanisms. Withdrawn/denied/expired records and superseded DG applications are excluded rather than modeled as exits or linked resubmissions.

Five-percent contamination is not an identified abandonment model. Old open records may be stale, abandoned or truly unresolved; age alone does not tell us which. The one-source-per-city policy usefully avoids obvious double counting, but between-city source and case-mix differences remain.

ADU web anchors additionally map `discretionary_review_or_hearing` to hearing presence, and ministerial wording to absence of hearing, notice and comment. Those are semantic assumptions beyond the source labels themselves. Combining current ordinances and historical findings with one 2017–2025 town design risks attributing changes across time to timeless structural differences. The new missingness mask is correct; it cannot validate these semantic recodings.

### 4.7 "Agency capability" is still a relative duration multiplier

The town log-speed coordinates are centered and assigned fixed-width priors. Global step durations are shared. This gives partial pooling conditional on a common step model, but it does not learn an intrinsic agency capability independent of task mix, customer delay, source, year and selected process design. The model also does not learn the population variance of agency effects in these packages.

Do not interpret a narrow posterior for this multiplier as identification of intrinsic capacity. Add crossed task/agency observations and relevant case mix where available, or report the conditional jurisdiction effect with those qualifications.

## 5. Mathematical sampling assessment

The SMC target is

\[
\pi_\beta(\theta)\propto p(\theta)L(y\mid\theta)^\beta,
\quad0\leq\beta\leq1,
\]

with town designs and finite loop alternatives summed inside the likelihood. Incremental weights are `exp((beta_new-beta_old)*LL)`. The code chooses temperatures using an incremental ESS criterion, resamples, and performs a fixed number of mutation moves.

The blocked kernel's locality is mathematically appropriate: local correction/objection changes affect one town; paired zero-sum speed changes affect two towns under centering; shared moves reevaluate all towns; the raw speed grand mean gets a conditional prior update. I did not find a new cache/Metropolis-ratio error in this review. The JAX HMC code uses the preconditioned leapfrog/Metropolis construction previously checked on W0. These are reasons to retain the implementations as candidates, not reasons to certify these real fits.

Important distinctions:

- **Beta=1 means the schedule ended**, not that particles represent the posterior.
- Incremental ESS is a weight-degeneracy control, not a within-mode mixing or global-mode-coverage diagnostic.
- `unique_ancestors` counts distinct parents at the current resampling stage, not full ancestral diversity.
- The R-hat calculation treats SMC ensembles like chains. Its between-run disagreement is a useful warning, but its usual time-chain interpretation does not directly apply to dependent, resampled particles. A value near 1 is not a convergence certificate.
- The postprocessor uses 100 answer draws per run, whereas the estimand gate's 0.2-SD tolerance was justified for 1,000. Independent-sample median Monte Carlo differences would grow from roughly 0.056 to 0.177 SD under the same normal approximation. Numerous small threshold failures can therefore be noise. Large parameter failures, the 37-SD Solar discrepancy, and the analytic controls remain decisive.
- Mean log likelihood is not posterior mass. Mode mass is an integral of likelihood times prior over a region. The results' claim that a ~1,000-unit mean-LL difference *proves* modes cannot have comparable posterior probability is not established by that statistic alone. Nor should "the best-likelihood run" be selected and reported as the posterior.
- SMC log-evidence estimates are more relevant than mean LL, but unreliable mode exploration can compromise them too. A log-evidence difference of 1.8 is not negligible merely because both logs are near −8.5 million. Report replicate uncertainty, not relative magnitude against that baseline.

There is a smaller exactness issue in initialization: `sample_prior` clips Beta draws to `[1e-4,1-1e-4]`, while `log_prior` evaluates the unclipped continuous Beta/logit density. Thus the initial sample is not exactly from the stated prior. This is not a plausible explanation for the enormous ADU control errors, but it should be resolved before making strict exact-SMC claims.

The priority is numerical validity and observable-based sampling diagnostics, not an unbounded series of extra seeds followed by selecting the largest likelihood. New starts in distinct configurations can diagnose barriers; their results need a valid exploration/weighting method before pooling.

## 6. Assessment of Claude's changes and the earlier speedup audit

| Change or claim | Audit judgment |
|---|---|
| Mask unobserved web steps | Accept in principle. Correctly distinguishes missing evidence from negative readings; source-to-step semantics still need care. |
| Stable logit branches | Accept the direction. The additional shared-logit fix addresses the live crash. The shared geometric helper remains inconsistent at the boundary. |
| Pending contamination | Legitimate **declared model extension**, not a numerical survival fix or evidence of abandonment. Does not repair deficient PMFs. |
| Milestone contamination | Legitimate optional observation assumption; an over-grid gap is not necessarily erroneous data. Keep event-set support exact and distinguish measurement error from duration support. |
| `JaxPool.map` operation-name matching | Real bug fix. The former function-identity dispatch could fail under the documented `python -m` entry point. My earlier smoke coverage did not establish this real JAX CLI path. |
| Default likelihood equivalence | The saved prior-point checks and focused tests support the stated checked cases. Not a certificate for all extreme parameter regions, new contamination settings, or real-data posterior sampling. |
| Exact duplicate compression / town caching | Retain: exact arithmetic/layout optimizations when complete observation signatures are preserved. They do not license subsampling or scalar-count reinterpretation. |
| W0 HMC results | Useful, scoped evidence. Not a guarantee for this much more concentrated real-data target. |
| GPU scaling limit | Credible and expected from shape heterogeneity. The ADU compile attempt did not finish; padding/bucketing is an engineering next step, not a demonstrated ADU speedup. |

The proposed shape padding must mask all padded observation terms and preserve whole-record weights. Merely multiplying an impossible padded likelihood by zero can produce `0 * -inf`. Benchmark compilation and end-to-end effective inference separately from warm likelihood throughput.

I agree with the speedup audit's recognition of the CLI and real-data support gaps. I do **not** agree that mode trapping is the only main remaining problem, or that interconnection's agreement on a menu label validates its substantive interpretation.

## 7. What the source-offset fit establishes

The standalone finite-grid fit is separate from the process engine. Its reported ratios reproduce from the saved output: interconnection 0.77 [0.54,1.00], Solar permits 0.74 [0.33,1.62], ADU 0.98 [0.57,1.58], pooled permits 0.89 [0.56,1.35]. **Those corrections are not applied inside the process fits.**

Several qualifications are necessary:

- "Own city-year" is not universal: **7/34 permit reports use a year mixture**, one Solar and six ADU. All 68 interconnection anchors use their keyed utility-year.
- An interval containing 1 does not establish equality or equivalence. The wide permit intervals allow sizable differences in both directions.
- The interconnection screen starts after installation, whereas the administrative received clock can start earlier. A ratio below one mixes clock-boundary differences, selection, case mix and reporting behavior; it is not a clean trust score.
- The administrative anchor is a binned Kaplan–Meier plug-in. Remaining tail mass is put in the final bin; anchor sampling uncertainty is not propagated. Issued/resolved-only input selection does not disappear by applying KM to the available data.
- The "exact-grid" calculation is deterministic finite-grid quadrature for that declared approximation, not an exact continuous posterior. Its sigma grid begins at 0.05; the saved edge-mass check omits the lower-sigma edge. I did not run a refinement study in this bounded audit.

Use these as exploratory matched-cell reporting comparisons. Learn source effects only after clock alignment, overlap and the observation populations are sufficiently specified; do not encode a universal Reddit-versus-agency trust ranking.

## 8. Hand-set quantities: which should be learned?

Not every constant should become another weakly identified latent parameter. Distinguish learned process variation, calibrated observation behavior, and scientific support choices.

| Current choice | Current status | Recommended treatment |
|---|---|---|
| Town speed SD 0.7 | Fixed across the real packages | A learned hyper-scale is plausible with many comparable towns, after fixing clock/source/case-mix confounding; otherwise declare sensitivity. |
| Global step location/spread priors | Set to log-14-day / log-0.6 families | Proper priors are necessary. Run bounded prior-predictive and sensitivity checks; do not regard wide priors as neutral under truncation. |
| Per-town correction and objection probabilities | Learned with independent Beta(1,1) priors | Learn occurrence/count mechanisms from actual repeats and hearings where available; fix geometric interpretation first. Hierarchical pooling may be useful. |
| Design menu and equal design priors | Authored structural support | Add observed case-level alternatives and explicit uncertainty. Data cannot learn a process excluded from the menu. |
| Five-loop cap / 512-day step grid | Hard support choices | Not ordinary hyperparameters to estimate casually. Test numerical support and sensitivity; justify or change the process model explicitly. |
| Five-percent contamination and 3,650-day contamination horizon | Fixed | Calibrate with reviewed status/error evidence or vary transparently. Cannot identify an abandonment rate by relabeling this knob. |
| Uniform posting horizon, total-only/timed-event probabilities | Borrowed observation scheme | Replace with the actual inclusion/reporting model or calibrate from full source records. Do not learn extractor-induced omissions as human behavior. |
| Mention detection/false-mention and web detection rates | Already learned in principle | Without observations they remain priors; conditional on the wrong design menu their estimates can compensate for misspecification. Anchors help. |
| Source offset/noise | Standalone exploratory fit; no process offset | Integrate a matched-clock source model with uncertainty when overlap supports it; avoid double-using the same data for calibration and fitting. |
| Hour coordinates | No observations | Marginalize or refresh from priors; no learned-hours headline. |

The objective is an identifiable hierarchy, not simply more parameters. A jurisdiction effect, a source effect and a case-mix effect cannot all be separated merely by increasing the number of same-source totals.

## 9. Reproducibility and reporting gaps

1. `combine_runs.py` reconstructs the model from current code/inputs without checking launch hashes, parameter order, scientific target or final beta. The main engine has target compatibility machinery; this shortcut does not invoke it. The live ADU rerun already demonstrates that the shared remote `code/` directory is not one immutable snapshot for every run. Per-run `source_snapshot/` and launch hashes are the appropriate references.
2. The postprocessor pools runs even when agreement fails. A 50/50 mixture of trapped ensembles is **not** an inferred 50/50 posterior mode probability. `posterior_summary.json` carries `pass`, but `answers_pooled.json` lacks the normal driver's diagnostic-pass marker, making downstream misuse easier.
3. `make_priors.py` regenerates model configurations without the deployed `pending_contamination` / `milestone_contamination` overrides. Re-running the advertised builder can undo the fixes necessary for these runs. A reproducible builder must encode the full declared settings.
4. Stopping after particle saving bypasses final stage-metadata/manifest closure. A cheap finalize-before-answers path would retain diagnostics without requiring a thousand serial answer draws.
5. Hours, zero-dollar outputs from absent fee schedules, deadline probabilities and counterfactuals are still generated by the generic answer path. "No fee evidence" is not "zero cost". Hour summaries are prior-driven and, in the blocked runs, numerically mis-sampled. For permit packages, `app_complete` is repurposed as the end of plan-check correction rounds, so its deadline clock must not be read automatically as the source's legal application-complete boundary.
6. Posterior predictive reproduction of fitted totals is useful but in-sample. It is not a held-out score, proof of step recovery, or evidence that this model beats a same-evidence LLM baseline. The ADU project-type check is a worthwhile unused-label diagnostic, but it tests association with a coarse administrative label, not exact recovery of a process graph; its results were not complete in this audit snapshot.

"Everything model-ready" should be narrowed to **three runnable subsets**. SolarAPP+, Terner, Rule 21 counts, permit linkages, partial forum clocks and Houzz coding are not all consumed by these likelihoods. The handoff's detailed table is much more accurate than the results summary's opening sentence.

## 10. Recommended next pass — bounded and ordered

1. **Quarantine the existing full-posterior headlines.** Preserve all artifacts. Label ADU numerically invalid; Solar not globally validated; interconnection provisional and gate-failing. Keep descriptive administrative timing results separate.
2. **Repair the zero-mass PMF and shared boundary paths first.** Use saved failing states as regression fixtures, check normalization and stable survival, and compare CPU/JAX at those states. No new multi-hour fit before that check passes.
3. **Repair the evidence adapter without rereading the entire corpus.** Preserve interval endpoints and status types, remove extractor-created timing-mask evidence, and explicitly declare inclusion/clock assumptions. Use the existing reviewed rows and ledgers.
4. **One small observable-anchored inference experiment.** Start with a bounded interconnection subset and its observed received→complete and complete→approved phases. Do not claim the unobserved extra step is identified. Remove prior-only dimensions, record shared/local acceptance and genealogy, and test against analytic controls plus a simpler reference fit. Add crossed configurations only with a valid exploration/weighting strategy.
5. **Then restore the scientific extensions in priority order:** meaningful case-level design/repeat evidence; outcome and completion-window handling; aligned source offsets; era/case-mix effects; an agency hyper-scale where supported. Report unidentified components as such.
6. **Only then scale and compare.** Pad JAX buckets with exact masks, benchmark end-to-end inference, and score a held-out administrative clock against simple empirical/survival and same-evidence LLM baselines. Keep a predefined stopping rule rather than choosing whichever seed has the largest likelihood.

No changes in this list have been implemented by this audit. The present recommendation is not to abandon the Bayesian architecture: it is to repair a concrete numerical defect, require an exact-posterior sanity check, and connect structural claims to observations that actually distinguish them.
