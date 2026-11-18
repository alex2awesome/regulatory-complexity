# Toy statute round 2: results (2026-09-26)

Protocol: `docs/2026-09-26-toy-statute-round2-plan.md`, including addenda
R2-A (move to sk3; milestone worlds) and R2-B (fee-split fix). Round 1:
`docs/2026-09-26-toy-statute-results.md`.

Related:
- `docs/process-model-causal-frame.md`;
- `docs/2026-09-26-complexity-measures-survey.md`;
- `docs/2026-09-26-complexity-measures-applied.md`.

Runs: `runs/toy_statute_20260926/{W0,W0m,W0x5,W0x25,W1,W1m}/`. Scores are in
`scores_round2_feefix/` (primary) and `scores_round2/` (pre-fix). One world
per condition, so everything is descriptive.

## Headlines

1. **Common sense is a strong estimator when the world matches it.** With thin,
   aggregate data in the common-sense world (W0 and W0m), the LLM average beats
   the Bayesian model on most continuous estimands. Head-to-head it wins 64–16
   in W0 and 50–29 in W0m.
2. **When the world defies common sense, the Bayesian model wins.**
   - W1: Bayes with LLM priors wins 65–33 head-to-head.
   - W1m, with milestone evidence: Bayes wins 69–26. Its time-based interval
     score is 0.82, against 1.30 for the LLM.
   - The LLM's 90% intervals cover only 71–78% of true values in W1 and W1m.
     The Bayesian intervals cover 86–93%.
3. **More data favours the Bayesian model.** Its head-to-head record against
   the LLM goes from 16–64 at 1× to 53–32 at 5× and 73–13 at 25×.
   - Roll-ups improve sharply: total-days scaled interval score 0.37 → 0.14 →
     0.07; deadline 1.74 → 0.83 → 0.55.
   - The LLM plateaus or worsens on the same estimands (deadline 1.40 → 0.81 →
     2.28).
   - Per-step burden does *not* improve with volume for either method. That is
     the identification limit, not a data-size limit.
4. **Step linking needs boundary evidence, and then works for both methods.**
   Adding status-change milestones to the admin records, for the same
   underlying cases, fixes the W1 failure:
   - Bayes per-step days 13.1 → 1.18, per-decision-step days 8.2 → 0.99;
   - LLM 12.0 → 1.39 and 9.3 → 1.40.
   - Desk review is recovered at 36.4 days [27.7, 45.6] against a truth of 35,
     and the completeness check at 1.5 [1.3, 1.7] against 1.5.
5. **LLM priors helped, and did not harm, at the declared widening.**
   - W0: non-trivial interval score 1.17 → 1.14.
   - W1: 5.79 → 4.37 overall, and 4.05 → 2.44 on time estimands.
   - W1m: prior sensitivity nearly vanishes (0.85 → 0.82), because data
     dominate once steps are linked.
   - The prior–data conflict flag never fired. It fails silently: the ×1.5
     widening makes the priors too broad to flag even a 6-day prior median
     against a 36-day posterior. A sharper conflict statistic is needed.
6. **Convergence is solved only where the data identify the parameters.** The
   town-centering fix made W0/fit004 pass both gates. Every other fit failed
   gate v2, and the failing parameters are the unidentified directions:
   notice + comment period, desk review + decision issuance, and the speed
   factors that trade off against them. **Sampler failure is diagnostic of
   non-identification.** The fix is the composite reparameterization below,
   not more particles.

## Q1: convergence (gate v2)

| fit | gate v1 | gate v2 | failing parameters (data-informed) | estimands failing |
|---|---|---|---|---|
| W0/fit004 (vague) | PASS | **PASS** | — | 0 |
| W0/fit005 (LLM prior) | fail | fail | completeness, comment, desk, la_Cedar | 11 |
| W1/fit001 | fail | fail | comment, σ notice, σ decision, la ×2, … | 3 |
| W1/fit002 | fail | fail | 13 parameters | 12 |
| W0x5/fit001 | fail | fail | 12 parameters | 9 |
| W0x25/fit001 | fail | fail | 17 parameters | 18 |
| W0m/fit001 | fail | fail | notice, comment, decision, … | 4 |
| W0m/fit002 | fail | fail | notice, comment, σ report hours | 1 |
| W1m/fit001 | fail | fail | comment, σ comment, la_Cedar, … | 1 |
| W1m/fit002 | fail | fail | notice, comment, desk, … | 2 |

In every run, the two independent runs' log evidence agrees to within about
1 nat. The big posterior mass is found; the runs disagree along the
unidentified ridges.

**Larger data makes the ridge sharper and sampling harder.** W0×25 has the
worst failure (17 parameters). Its per-step estimates degrade relative to W0×5
(scaled interval score 1.33 → 2.03), a sampler artefact on a razor-thin
ridge. The aggregate estimands still improve.

## Q6 and the step-linking machinery

**Diagnostic** (`toy_statute/identify.py`). Mean durations add along a chain.
An estimand is identified from interval means iff its gradient lies in the
row space of the Jacobian of the observed interval means (at the prior
centre, given the structures). Non-trivial identified estimands:

| evidence design | W0 world | W1 world |
|---|---|---|
| admin totals + reports | 5 | 5 |
| + "deemed complete", inspection and hearing milestones | 10 | 10 |
| + hypothetical "review complete" milestone (W0) | 28 | — |
| + "notice mailed" (W0) | 30, all but deadline-miss probabilities | — |

**Rule:** a step's burden is linked to data only if its bounding events are
observed, or if structural variation across towns separates it. Deadline-miss
probabilities are never identified from means, because they depend on
distribution shape.

**The diagnostic is conservative.** The full likelihood also uses interval
*shapes* and cross-town sharing, so it recovers more. For example, W1m desk
review comes back tight and correct even though the means-only test does not
certify it.

**Data-design implication for real Solar data:** the single most valuable
milestone is the boundary of the vague step, i.e. "determination / plan check
complete". Then notice-mailed and deemed-complete.

## Q4: scaling (W0 truth; vague Bayes vs LLM average)

| n | Bayes non-trivial IS | LLM non-trivial IS | head-to-head Bayes:LLM | Bayes total-days IS | Bayes per-step days IS |
|---|---|---|---|---|---|
| 1× (80 admin, 45 reports) | 1.17 | 0.90 | 16:64 | 0.37 | 2.10 |
| 5× | 0.59 | 0.64 | 53:32 | 0.14 | 1.33 |
| 25× (2,000 admin, 1,125 reports, 120k-token prompt) | 0.56 | 0.53 | 73:13 | 0.07 | 2.03 (sampler failure) |

The LLM handled a 120k-token evidence prompt well (median error 0.10). It does
scale to this size.

## Q2, Q3: LLM priors (hybrid)

| world | vague | LLM prior | Δ |
|---|---|---|---|
| W0 | 1.171 | 1.143 | −0.03 |
| W0m | 1.079 | 1.010 | −0.07 |
| W1 | 5.793 | 4.370 | −1.42 |
| W1m | 2.990 | 2.962 | −0.03 |

All values are non-trivial scaled interval scores, after the fee fix. W1
helped rather than hurt because W1's step scales mostly fall inside the
widened LLM ranges. The vague prior (every step ~7 days) is also "wrong" for
W1. **This does not settle Alex's cultural-transfer concern.** A world outside
the LLM's ranges, or narrower (less widened) priors, would be the real test.
The conflict flag needs a sharper statistic before it can protect against that
case.

## Q5: the prompt leak did not matter

The leak-free W0 LLM average scored better than round 1's: 0.90 against 1.05
non-trivial interval score, and structure log score −0.12 against −0.21.
Run-to-run LLM variation dominates.

## Extended measures (W0; Bayes fit003 vs LLM, the survey's M-measures)

On the seven extended measures, Bayes and the LLM average are about tied
(interval score 0.887 against 0.889). Bayes is better calibrated (coverage 1.00
against 0.89). The LLM systematically overstates deadline coverage (0.83–0.89
against truths of 0.69–0.76) because it underweights time in correction loops.

## What to change next (proposed)

1. **Composite reparameterization, driven by the diagnostic.** For each block
   of steps that the diagnostic says are only jointly identified, sample the
   block's total mean and a share (prior-driven), instead of each median. This
   straightens the curved ridge that defeats the random-walk moves. Report
   block burdens as the primary estimand, and splits as "prior-driven" with
   their prior-to-posterior contraction.
2. **Report identification status alongside every estimate:** identified from
   data, partly, or prior-driven. Use the diagnostic plus posterior/prior
   contraction.
3. **A sharper conflict statistic,** e.g. the shift of the posterior median in
   units of the *unwidened* LLM prior SD. Also an out-of-range adversarial world
   to test cultural transfer properly.
4. **For real Solar data:** prioritize milestone logs (plan check or review
   complete, issued, inspection passed) from permit systems. The existing
   four-phase administrative panel is already phase-level milestone evidence.
