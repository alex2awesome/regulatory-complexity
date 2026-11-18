# Response to the full-chain audit (2026-09-30)

Audit: `docs/2026-09-29-toy-statute-full-chain-audit.md` (independent agent, report only). This note records, finding by finding, what was confirmed, what was changed, how the change was verified, and which earlier claims are withdrawn or re-labelled. Code changes are in `pipeline/procbench/toy_statute/`; each has a counterexample test in `tests/test_toy_statute.py` (39 tests).

## Confirmed and fixed

| Finding | Verdict | Fix | Verification |
|---|---|---|---|
| **F1** outcome likelihood multiplied Poisson terms for overlapping counts (denied applicants reappear in unpermitted complaints) | Correct; my "independent by thinning" claim was wrong | `outcomes.loglik`: exact joint p(D, Vu, Nu) by marginalizing the denied applicants' later fates (`_joint_denied_unpermitted`, a double sum ≤ D² terms); the survey's hidden cell uses the conditional expectation of the denied-quiet count given (a, b) — a declared approximation, binomial variance ≤ D/4 against survey sampling variance of order (H/n)²·np | `test_outcome_joint_normalizes_and_has_poisson_denial_marginal`: joint sums to 1 over a grid; D-marginal equals Poisson(λ_D) |
| **F2** completed applicant reports omitted the completion-selection factor P(posting day ≥ total) inside the latent-duration sum; pending survival wrongly mixed contamination | Correct | `Model._completed_gap_loglik`: each report's gaps partition submitted→decision, so their latent sum is T; likelihood = Σ_T [q_1 ∗ … ∗ q_G](T)·P(C ≥ T) with q_i(d) = seg_i(d)·[(1−c0)p(Y_i|d) + c0·ref_i], by FFT over combos, truncated at the posting window's end (P(C ≥ T) = 0 beyond it). Pending: P(T > N) only. The posting window is published in `public_spec.json["posting"]` and stated in the public model notes (the LLM sees it too). | `test_completed_report_selection_matches_brute_force`: agrees with direct summation to 1e-9 on 1- and 2-gap reports. Evaluation time unchanged (41 ms on W0). |
| **F3** FFT length 1,024 aliases long sums; cropping renormalized tail mass away | Correct (three 400-day steps landed at day 176) | `grid.NFFT_DAYS/HOURS = 8192` with an assertion on the longest sum; totals beyond the grid are lumped into the last bin (observations are clipped there), no renormalization beyond numerical error | `test_fft_no_aliasing_and_tail_lumped` |
| **F4** residual reading mass ρ and choice slack ε exactly confounded | Correct (saved log evidences identical to 1e-14) | Stage-C grid holds ρ = 0.05 and varies ε ∈ {0.05, 0.15, 0.30}; results are indexed by η = ρ + (1−ρ)ε; documented in the results json | Reproduced from saved results |
| **F6** scorer treated residual mass as "No" | Correct (Q4 conditional on a known reading is exactly its prior in every town) | `readings.score_readings`: per-question P(yes \| known reading); residual reported separately; MAP over known readings | Re-scored round 4 (below) |
| **F7** Q5 in the headline joint score despite the stated exclusion | Correct | `score_readings(exclude=...)` marginalizes excluded questions out of the joint | Re-scored round 4 (below) |
| **F8** risk model used raw reading counts (e^24 preference ratios) | Correct; "risk aversion rejected" is withdrawn | `choice_logprob("risk")` uses the *share* of readings under which the design is valid; the grid runs β ∈ {2, 5} | New fits required before any statement about risk preference |
| Fee-split fix not on the default output path (§8) | Correct | `smc.py` now calls `answers_from_draws(..., random_fee_split=True)` | Old fits keep their files; new fits use it |
| Stage C assumes a uniform Stage-B design prior without checking (§6) | Correct | `run_stage_c` raises if the fit used `prior_json` | — |

## Confirmed, accepted as stated (no code change)

- **F5** 32 readings collapse to 5 validity patterns in W4; Q4/Q5 leave no trace by construction. Adopted as the reporting frame: results now state which questions can move at all. Q5 also needs a fee-reading likelihood edge, not only the generator fix (statute 2's packages carry fees conditional on the fee reading; the likelihood edge is still absent).
- SMC "R-hat" is not an MCMC certificate; the between-run SMD is the informative part. The estimand gate's 1,000-draw quantile jumps explain the W0/W0x5 estimand-only failures in round 3b.
- Method-dependent "non-trivial" sets in `score.summarize` (92 vs 96 items); the head-to-head is the common-set comparison and should be quoted first.
- "Full chain" = connected modules with cuts and plug-ins; town speed ≠ agency capability; the design menu is supplied.
- Finite-κ integration used 50 population draws over 2,000 particles; the ESS reported is weight concentration over pairs.

## Claims withdrawn or re-labelled

1. **"Risk-averse choice rejected by a Bayes factor of e^10"** → withdrawn. It rejected an absurdly scaled model.
2. **"Residual mass works as a misspecification detector"** → re-labelled: a conditional lack-of-fit indicator; not identified separately from slack.
3. **Round-4 headline reading scores** (−3.36 Bayes vs −3.91 LLM, all five questions, residual as "No") → replaced by corrected scores of the same saved posteriors, Q1–Q4 joint over known-reading mass: P-pool2 with cost τ=15: **−2.13**; P-flat with uniform choice: −2.27; P-pool2 prior alone: −2.59; LLM: −2.67; flat prior: −2.77. Per-question Brier given a known reading: Q4 equals its prior in every setting (0.14 with P-pool2, 0.25 flat), as it must. The direction (Bayes beats prior and LLM; Q2/Q3 learned; Q1/Q4 prior-driven) survives; the magnitudes are those above. **The W4 fit itself used the pre-F2/F3 likelihood and failed its gate**, so these remain corrected scores of a defective fit until the recovery experiment reruns it. File: `runs/toy_statute_20260926/W4/stage_c001/scores_corrected_F6F7.json`.
4. **Outcome-layer results** (`2026-09-28-toy-statute-outcomes-results.md`): the fits used the overlapping-count likelihood. Their numbers stand as a record of that fit; the deterrence-bias attribution and the interval claims are suspended until the refit under F1.
5. **"Exact likelihood" / "exact for the generator"** → "exact given the grid, with the declared survey approximation"; the FFT tail now lumps at the last bin rather than being renormalized.
6. **All round 3/3b/4/5 process fits** used the F2/F3 likelihood. Design identification and the sampler-precision conclusions (round 3b) are unaffected in kind; per-step duration numbers may shift and are superseded by the recovery experiment.

## Not adopted (with reasons)

- **Learning τ, contamination, posting-time and elicitor calibration now.** Agreed in principle, deferred: the audit's own sequencing puts correctness first, and with one or two statutes these are weakly identified. τ becomes learnable across the linked worlds (HEN2/HK2, same agencies).
- **Replacing the scaled interval score.** Kept for continuity with rounds 1–4, now reported alongside the common-set head-to-head; unscaled per-family scores can be added to the recovery experiment.

## Recovery experiment

`docs/2026-09-30-toy-statute-round6-plan.md`: the corrected likelihood on W0, W0m, W4, HK1b and the linked shared-agency worlds HEN2/HK2, outcome refits on the corrected W0 posterior, Stage C with the corrected scorer, and the first shared-agency comparison.
