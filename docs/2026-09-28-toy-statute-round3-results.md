# Toy statute round 3: composite reparameterization, results (2026-09-28)

Protocol: `docs/2026-09-28-toy-statute-round3-plan.md`. There are 8 fits on sk3, one execution each. All 8 are complete; W0x25/fitB001 finished at 05:16 PDT.

- Fits: `runs/toy_statute_20260926/{W0,W0m,W0x5,W1,W1m}/fitB00{1,2}/`.
- Fee-fix answers (addendum R2-B), computed with `recompute_answers_feefix_r3.py`.
- Scores: `*/scores_round3/`.
- Block contraction: `round3_block_contraction.json`.

## Primary: gate v2 (predeclared)

| World | Round 2: pass, R-hat, worst SMD, failing params / estimands | Round 3 (blocks): pass, R-hat, worst SMD, failing params / estimands |
|---|---|---|
| W0 | **PASS**, 1.0044, 0.099, 0 / 0 | fail, 1.0018, 0.115, 1 / 1 (σ completeness check) |
| W0m | fail, 1.0533, 0.257, 8 / 4 | **PASS**, 1.0019, 0.095, 0 / 0 |
| W0x5 | fail, 1.0197, 0.231, 12 / 9 | fail, 1.0057, 0.161, 5 / 2 |
| W1 (vague) | fail, 1.0133, 0.246, 8 / 3 | fail, 1.0196, 0.219, 5 / 2 |
| W1 (LLM prior) | fail, 1.0256, 0.358, 13 / 12 | fail, 1.0076, 0.188, 3 / 2 |
| W1m (vague) | fail, 1.0151, 0.298, 5 / 1 | fail, 1.0060, 0.175, 2 / 2 |
| W1m (LLM prior) | fail, 1.0216, 0.221, 9 / 2 | fail, 1.0051, 0.173, 1 / 0 |
| W0x25 | fail, 1.0426, 0.422, 17 / 18 | fail, 1.0042, 0.132, 7 / 1 |

Round 3 passes 1 of 8, the same count as round 2 (1 of 8), but a different fit passes. Mixing improved substantially and consistently:
- Failing parameters fell from 5–17 per fit to 0–7.
- The worst between-run SMD fell from 0.22–0.42 to 0.10–0.22.
- R-hat is ≤ 1.008 everywhere except W1 vague, at 1.020.

The ridges that defeated round 2 (notice + comment, desk + decision) are largely gone from the failure lists. What remains is spread over spread parameters (σ), the mention false-positive rate and block totals.

**Reading (not predeclared, stated as a hypothesis).** The remaining failures sit near the gate's own Monte Carlo noise floor. With 2 runs × 3,000 particles, the between-run SMD of a well-mixed parameter is roughly √(2/ESS). The maximum of that over 36 parameters is about 2.7√(2/ESS), which is about 0.1 when ESS ≈ 1,500.

W0 went from pass to a narrow fail (0.115 on σ_completeness_check) under a reparameterization that does not touch that parameter. That fits a noise-floor reading.

If Alex wants the gate settled, the test is a predeclared rerun with more particles or runs (e.g. 4 runs × 10,000 particles), at unchanged gates. It has not been run.

## Secondary: scores (same posterior, so they should agree where round 2 mixed)

Non-trivial mean scaled interval score (90% coverage):

| World | Round 2 vague | Round 3 vague | Round 2 LLM prior | Round 3 LLM prior | LLM avg3 |
|---|---|---|---|---|---|
| W0 | 1.171 (0.99) | 1.166 (0.99) | — | — | 0.897 (1.00) |
| W0m | 1.079 (0.90) | 1.040 (0.92) | — | — | 0.882 (0.91) |
| W0x5 | 0.586 (1.00) | 0.584 (1.00) | — | — | 0.638 (0.97) |
| W1 | 5.793 (0.86) | **5.219** (0.88) | 4.370 (0.89) | 4.447 (0.89) | 5.504 (0.71) |
| W1m | 2.990 (0.93) | 3.016 (0.96) | 2.962 (0.92) | 2.961 (0.93) | 3.399 (0.78) |
| W0x25 | 0.555 (0.96) | **0.394** (0.98) | — | — | 0.528 (0.97) |

- As predicted, scores are essentially unchanged where round 2 mixed acceptably.
- W1 with vague priors improved (5.79 → 5.22). Round 2's poor mixing there distorted its answers.
- **W0x25 improved most.** Overall score went 0.555 → 0.394, and per-step days 1.27 → 0.68.
  - Round 2 reported that per-step estimates *degraded* from 5× to 25× data. That was the sampler failing on a razor-thin ridge, as suspected, not a data effect.
  - With the ridge straightened, Bayes beats the LLM at 25× on every summary: 0.394 against 0.528, head-to-head 74:12.
- Head-to-head against the LLM is unchanged in substance. The LLM still wins W0 and W0m. Bayes wins W0x5, W1 (r3 vague 59:40; r3 LLM prior 63:36) and W1m (65:31; 70:26).

## Reporting: which estimands are data-driven (predeclared rule)

The posterior-to-prior SD ratio of the block coordinates. The plan's rule: ≥ 0.8 means prior-driven.

| Fit | notice + comment: total | notice + comment: split | desk + decision: total | desk + decision: split |
|---|---|---|---|---|
| W0 | 0.28 | 0.57 | 0.19 | 0.47 |
| W0m | 0.08 | 0.63 | 0.09 | 0.21 |
| W0x5 | 0.18 | 0.53 | 0.14 | 0.28 |
| W1 vague | 0.30 | 0.69 | 0.28 | 0.52 |
| W1 LLM prior | 0.34 | 0.78 | 0.32 | 0.52 |
| W1m vague | 0.11 | **0.87** | 0.06 | 0.27 |
| W1m LLM prior | 0.13 | **0.90** | 0.07 | 0.26 |

- **Block totals are data-driven everywhere.**
- **The notice/comment split** is prior-driven in W1m, and only partly informed elsewhere (0.53–0.78). Per-step notice and comment-period days should carry a *prior-driven* label in W1m and a *partly informed* label elsewhere.
- **The desk-review/decision split is more informed than the means-only diagnostic predicted.** In the towns that issue the permit at the inspection (S3/S6), desk review is not followed by a decision step. That structural variation separates desk review from decision issuance, as the step-linking rule says: variation across towns links steps even without a boundary event.

## Conclusion

The composite reparameterization did what the diagnosis said it would. The unidentified ridges stopped dominating the sampler's failures, and scores were unchanged except where the old mixing had distorted them.

It did not produce a clean sweep of the strict gate. The remaining failures look like Monte Carlo precision rather than geometry. That is testable with a larger predeclared run.

## Round 3b: Monte Carlo precision test (addendum 3b; all 8 fits back, 2026-09-30 02:30 PDT)

Same fits, 10,000 particles instead of 3,000, gate unchanged. Predicted SMD shrink if the failures were noise: ≈ 1.8×.

| Fit | 3k: worst SMD, fails (params/estimands) | 10k: worst SMD, fails | Shrink | Gate at 10k |
|---|---|---|---|---|
| W0 | 0.115, 1/1 | 0.067, 0/1 | 1.7× | fail (one estimand median only) |
| W0m | 0.095, 0/0 | 0.051, 0/0 | 1.9× | **PASS** |
| W0x5 | 0.161, 5/2 | 0.074, 0/3 | 2.2× | fail (estimand medians only) |
| W1 vague | 0.219, 5/2 | 0.131, 1/3 | 1.7× | fail |
| W1 LLM prior | 0.188, 3/2 | 0.208, 5/4 | **0.9×** | fail |
| W1m vague | 0.175, 2/2 | 0.055, 0/0 | 3.2× | **PASS** |
| W1m LLM prior | 0.173, 1/0 | 0.059, 0/0 | 2.9× | **PASS** |
| W0x25 | 0.132, 7/1 | 0.133, 2/1 | **1.0×** | fail |

Reading: six of eight fits shrank by the predicted factor or more, and three now pass; the remaining misses in W0 and W0x5 are estimand-median checks with no parameter failing. Those were Monte Carlo noise. Two fits did not improve: W1 with LLM priors (0.9×) and W0x25 (1.0×, though its failing parameters fell from 7 to 2). Both are genuine mixing problems rather than noise: the mixture prior interacting with the block coordinates in one case, and the razor-thin ridge that 25× data produces in the other. They stay reported as failures. All 3b fits used the pre-audit likelihood; the sampler-precision conclusion does not depend on that.
