# Toy statute round 4: the reading layer, results (2026-09-29)

Protocol: `docs/2026-09-29-toy-statute-round4-plan.md` with addenda 4-A and 4-B. Design: `docs/2026-09-29-full-chain-model-proposal.md`.

Status: complete. Stage B (`W4/fitB001`) finished at 20:50 PDT; Stage C (`W4/stage_c001/`, 160 runs) and scoring followed.

Runs: `runs/toy_statute_20260926/W4/` — `parse_elicit001/`, `rsa_q1_prior.json`, `llm_readings001/`, `scores_llm_and_priors001.json`, `fitB001/`, `stage_c001/` (stage_c.json, scores.json).

## Stage A: what the LLM sees when it reads the statute

Six independent Opus parses of the 8-line statute, no evidence shown.

**Skeleton elements.** Six of six parses marked E1–E6 present (application with site plan; implied completeness check; nuisance determination before issuance; 30-day clock from a complete application; fee authorized; eligibility scope). Mean confidence 0.77–0.97, lowest for the *implied* completeness check (0.78) and the eligibility scope (0.77).

**One disagreement with my hand-coded skeleton.** Six of six parses marked E7, "denial may rest only on ineligibility, incompleteness or the nuisance determination", as *absent* (confidence 0.80): the text lists no exhaustive denial grounds. My validity checker had treated limited grounds as concrete (constraint C6). This is exactly the case Alex raised, a skeleton element that is really a parse. C6 becomes a question in later rounds. It changes nothing in this round because no candidate design adds a denial ground.

**Ambiguities.** 26.3 per parse in 8 lines: 64 incompleteness, 36 lexical, 26 semantic, 18 vagueness, 14 referential across the six parses. Human analysts in Massey et al. (2014) found about 33 per 104 lines, so the LLM is far more prolific; many of its items are fine-grained scope questions (who counts as a resident; townhouses; per-lot vs per-resident cap; renewal and revocation; site-plan precision; which property lines).

**80% of the ambiguities map to none of Q1–Q5.** Our five questions covered the process-relevant ambiguities only. That share is the empirical footing for the residual reading, and the first list of candidate questions for the refinement loop.

**Question priors.** Direct P(yes), averaged over parses: Q1 0.64, Q2 0.18, Q3 0.45, Q4 0.81, Q5 0.16, against the truth-generating 0.60 / 0.35 / 0.90 / 0.80 / 0.50. The LLM doubts the implied investigative power (Q3) and separate fees (Q5) more than the world that generated the towns.

**Parse frequency was degenerate**: every parse fell on the same side of 0.5 for every question, giving 0/1 frequencies. The declared pool P-pool inherits this (pooled probabilities 0.99 / 0.01 / 0.03 / 0.99 / 0.01) and scores a log score of −10.9 against the towns' true readings, versus −3.5 for a flat prior. Addendum 4-A added P-pool2 (direct + RSA for Q1), which gives 0.69 / 0.18 / 0.45 / 0.81 / 0.16.

**RSA threshold model.** For the "nuisance" scale, the pragmatic listener's threshold posterior has mean 3.4 (sparse town), 4.5 (medium) and 5.6 (dense) on a 0–10 degree scale; the derived P(desk review suffices) is 0.63, 0.61 and 0.54. The direction is the predicted one (denser towns read the word more strictly), and its influence on the prior is bounded by λ = 0.5.

## LLM baseline: readings from evidence

Three Opus runs on the 12 towns' evidence ($0.61–0.65 each), averaged.

| | LLM | flat prior | P-llm prior | P-pool2 prior |
|---|---|---|---|---|
| Mean log score of the true reading | −3.91 | −3.47 | −3.66 | −3.73 |
| Towns with the true reading as MAP | 1/12 | 0 | 0 | 0 |
| Mean log score of the true design | **−0.50** | −2.40 | −2.40 | −2.40 |
| Towns with the true design as MAP | **12/12** | — | — | — |
| Brier Q1 / Q2 / Q3 / Q4 | 0.26 / 0.25 / 0.10 / 0.33 | 0.25 each | 0.32 / 0.14 / 0.29 / 0.14 | 0.35 / 0.14 / 0.29 / 0.14 |

- **Designs: excellent.** The LLM names the true design in every town, with probabilities 0.54–0.77.
- **Readings: worse than a flat prior.** The LLM reads intentions off the observed design: every town that uses neighbour notice gets P(neighbours must be heard) ≈ 0.85, though only two of the five such towns hold that reading; the others chose notice because it was cheap under their step laws. This is the size-principle attribution error the plan predicted for a uniform-valid choice model, made by the LLM.
- Q5 is excluded from the headline comparison (addendum 4-B): the generator drew fee schedules independently of the town's Q5 reading, so fees carry no information about Q5 in this world.

## Stage B: process fit

`fitB001`: 12 towns, 11 designs, 63 parameters, 2 runs × 3,000 particles, 84 minutes on 32 workers. **Gate v2: FAIL** (worst R-hat 1.037, worst SMD 0.47, 39 parameters). With 63 parameters, 3,000 particles are far too few (the round-3b result says 10,000 barely suffices for 36). As predeclared, Stage C runs on the pooled particles and every number below rests on a failed-gate fit. What that failure does *not* touch: design identification. The true design has the highest posterior in all 12 towns (0.74–1.00), and Stage C's per-town design posteriors are 12/12 correct under every prior and choice model.

## Stage C: reading posteriors

Scores are the mean log score of each town's true reading over 12 towns (higher is better), and per-question Brier scores (lower is better). Baselines: flat prior −3.47; P-llm prior −3.66; P-pool2 prior −3.73; LLM baseline −3.91.

| Prior | Choice model (ε = 0.05) | Log score | Brier Q1 | Q2 | Q3 | Q4 | Q5† | Residual mass | log Z vs Stage B |
|---|---|---|---|---|---|---|---|---|---|
| P-pool2 (prior) | — | −3.73 | 0.35 | 0.14 | 0.29 | 0.14 | 0.42 | — | — |
| P-pool2 | cost, τ = 15 (true) | **−3.36** | 0.27 | **0.11** | **0.19** | 0.15 | 0.43 | 0.09 | −2.5 |
| P-pool2 | cost, τ = 40 | −3.35 | 0.29 | 0.12 | 0.18 | 0.14 | 0.43 | 0.08 | −1.6 |
| P-pool2 | uniform-valid | −3.39 | 0.30 | 0.12 | 0.19 | 0.14 | 0.44 | 0.08 | −1.9 |
| P-pool2 | risk-averse, β = 1 | −4.21 | 0.28 | 0.12 | 0.50 | 0.22 | 0.49 | **0.35** | **−12.1** |
| P-flat (prior) | — | −3.47 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 | — | — |
| P-flat | cost, τ = 15 | −3.11 | 0.23 | 0.16 | 0.16 | 0.28 | 0.27 | 0.09 | −2.3 |
| P-flat | uniform-valid | −3.06 | 0.24 | 0.14 | 0.18 | 0.27 | 0.28 | 0.09 | −2.7 |
| P-pool (degenerate) | any | −9.6 to −11.9 | | | | | | 0.16–0.53 | −4.5 to −13.1 |
| LLM baseline | — | −3.91 | 0.26 | 0.25 | 0.10 | 0.33 | 0.47 | — | — |

† Q5 is uninformative in this world by a generator flaw (addendum 4-B).

**What the data taught the model, per question:**
- **Q2 (neighbours must be heard):** the clearest success. Towns without notice go to P ≈ 0.02; towns with notice go to 0.28–0.35 from a prior of 0.18. In truth 2 of the 5 notice towns hold the reading, so 0.3 is about right. The LLM put 0.85 on all five.
- **Q3 (implied power to require inspection attendance):** Brier 0.29 → 0.19. Not predicted: I expected Q3 to stay near its prior, but inspection-based designs are valid only if Q3 is yes, and 8 of 12 towns inspect.
- **Q1 (desk review suffices):** barely moves (0.69 → 0.55–0.60 everywhere), and the population estimate stays at 0.59 against a realised 0.33. No town uses a desk-only design, and inspection designs are valid under both answers, so the practice in this world says almost nothing about Q1. Correctly prior-driven.
- **Q4 (clock runs through the determination):** unchanged, as predicted; no design's mandated waits approach 30 days.
- **MAP over the 32 joint readings** is right in 0–2 towns out of 12 under every setting. The joint reading is dominated by Q4 and Q5, which the data cannot inform; per-question posteriors are the meaningful output.

**Population of readings (κ).** At κ = 10 the population P(yes) is 0.59 / 0.16 / 0.54 / 0.70 / 0.18 against a realised 0.33 / 0.17 / 0.92 / 0.83 / 0.58. Marginal likelihoods: κ = 3 is highest by 1–1.2 nats but has the worst per-town log score (−4.1: a sparse Dirichlet concentrates on the readings already implied by observed designs); κ = 10 ≈ κ = ∞. No decisive preference, as predeclared.

## Predeclared readings, checked

1. **Recovery under the true choice model.** Met. Log score −3.36 against the prior's −3.73; Brier better than the prior for Q1 (0.27 vs 0.35), Q2 (0.11 vs 0.14) and, unexpectedly, Q3 (0.19 vs 0.29). Q4 unchanged as predicted. P-pool was degenerate as flagged in addendum 4-A, so P-pool2 carries this reading.
2. **Wrong choice model.** *Not* confirmed for uniform-valid: uniform and cost give nearly identical posteriors (Q1 0.60 vs 0.55–0.60 in the inspection-only towns). With 11 designs and slack, the size principle is too weak to bite. *Confirmed in effect, wrong in direction* for risk-averse: it shifts Q1 to 0.34 everywhere (stricter, not more permissive as I predicted), because designs valid under few readings are surprising to a safety-seeking agency unless the reading rules out the safer ones. It is also decisively rejected by the data: log Z −12.1 against −1.6 to −2.7 for uniform and cost (a Bayes factor of order e^10), and its residual mass rises to 0.35. **Cost versus uniform is not distinguishable** (log Z within 1 nat), as expected from 12 towns.
3. **Design recovery unchanged across choice models.** Met: 12/12 under every setting; the evidence decides S_t.
4. **κ.** Met: no decisive preference.
5. **Elicitation.** Reported above: 6/6 skeleton agreement on E1–E6, E7 rejected, 80% of ambiguities unmapped.
6. **LLM baseline.** Designs 12/12 (same as Bayes). Readings −3.91 against Bayes −3.36 under the true choice model and −3.06 under a flat prior; the LLM's Q2 is the overconfident version of the model's correct inference.

## What round 4 says

- **The reading layer works as a mechanism.** From process evidence alone, and at almost no cost beyond the process fit, the model recovers per-town readings on the questions that constrain designs, stays at its prior on the questions that don't, and says which is which. That last property is the one the LLM lacks: it commits to readings the evidence cannot support.
- **The residual is a working misspecification detector.** It sits at 0.08–0.09 under plausible choice models and jumps to 0.35 under the rejected one.
- **Goals are partly testable after all.** With 12 towns the data cannot separate "picks any legal design" from "picks the cheapest legal design", but they can reject "picks the legally safest design" outright. That is a weaker claim than learning ψ, and a real one.
- **Practice is silent on some ambiguities.** Q1 and Q4 here. No amount of process data resolves a clause that no observed design turns on; only text changes or case law can.
- **The Stage-B gate failure is the main caveat.** Reading posteriors depend on the town-design likelihoods, which were stable (12/12 designs at high probability), more than on θ's fine posterior; but the per-particle burden indices feeding the cost model are from an unconverged θ. A rerun with 10,000+ particles is the obvious next step and was not run here.

## Corrections to the design so far

1. C6 (limited denial grounds) is a question, not a skeleton element (Stage A).
2. Parse frequency over K samples of one model is not a usable prior source; direct probabilities or a calibrated elicitor are (Stage A).
3. Fee schedules must be generated conditional on the Q5 reading (addendum 4-B).
