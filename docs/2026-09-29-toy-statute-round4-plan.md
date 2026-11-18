# Toy statute round 4: the reading layer, predeclared (2026-09-29)

Alex approved on 2026-09-29: "do you have an implementation / process in mind to faithfully implement this, consistent with the literature? if so, please do it, and please run it on the hen example." Design: `docs/2026-09-29-full-chain-model-proposal.md`; audit: `docs/2026-09-29-reading-layer-audit.md`. Written before any Stage-B fit or Stage-C reweighting was run. Implementation smoke checks (32 tests; a single log-posterior evaluation on W4 at 45 ms) were run for correctness and timing only.

## What is new in code

- `spec.use_design_space("full")`: the compositional design space of all non-empty safeguard subsets in canonical serial order, with an issue-at-inspection variant wherever an inspection exists: 11 designs (S1–S6 plus S7 inspection only, S8 inspection only issuing on site, S9 notice only, S10 notice + inspection, S11 notice + inspection issuing on site). Concurrent arrangements are excluded from this round: the process likelihood does not yet support parallel branches.
- `readings.py`: readings as answers to Q1–Q5 (32) plus a residual; admissibility hook; validity matrix from `validity.check`; log-linear pooled prior; three choice models with slack; Stage-C exact reweighting of Stage-B particles, with an optional Dirichlet population of readings (κ); scoring.
- `rsa_vagueness.py`: the Lassiter–Goodman threshold model for "nuisance", used as one prior source for Q1 through the declared mapping P(Q1 = yes) = P(θ > x_plan).
- `parse_elicit.py`: K tool-less LLM parses of the statute (elements with confidence; Massey-taxonomy ambiguities; direct P(yes) for Q1–Q5).
- `truth_w4.py`: the round-4 world.

## World W4 (truth; generator only)

- 12 towns. Each town's true reading is drawn with P(yes) = 0.6 / 0.35 / 0.9 / 0.8 / 0.5 for Q1–Q5, independently.
- Each town chooses a design by **cost-softmax** among the designs valid under its reading: p(S) ∝ exp(−B(S)/15) on V_r, with slack ε = 0.05 spread uniformly over all 11 designs. B is the truth burden index (days + 4·hours + $/5).
- Step laws as W0. Town speed ~ lognormal(0, 0.25); P(incomplete) ~ U(0.08, 0.35); P(objection) ~ U(0.15, 0.30); fees drawn per town.
- Evidence: admin records in 6 towns (40 each); 15 applicant reports per town; a web page per town. 500 held-out cases per town.
- Realised: designs S3 ×4, S9 ×3, S7 ×2, S4, S5, S11; every town's choice was valid under its reading. No town chose S1: in W0's step laws an inspection-only process is cheaper than a desk review.
- Seed 20261004; `runs/toy_statute_20260926/W4/`.

## Stage A: elicitation (no evidence)

1. `parse_elicit` with K = 6, Opus. Outputs: element reliabilities (share of parses marking each skeleton element present; correlated votes, reported as such), two question-prior sources (direct probabilities averaged; parse frequency of yes), ambiguity counts by taxonomy type, and unmapped ambiguities (residual candidates).
2. RSA prior for Q1 at medium density; other questions have no scale and get no RSA source.
3. Pooled priors (log-linear per question), three variants:
   - **P-llm**: direct probabilities only, λ = 1.
   - **P-pool**: direct (λ = 1) + parse frequency (λ = 0.5) + RSA for Q1 (λ = 0.5).
   - **P-flat**: 0.5 for every question (no elicitation).
   Residual ρ = 0.05 in all; sensitivity ρ = 0.15 on P-pool.

## Stage B: process fit (sk3)

`smc.py --design-space full --center-towns --blocks desk_review+decision_issue,neighbor_notice+comment_period`, 2 runs × 3,000 particles × 30 moves, seed 20261001, gate v2 unchanged, 32 workers. Run id `W4/fitB001`. Uniform prior over the 11 designs. One execution; a gate failure is reported and Stage C still runs on the pooled particles, labelled accordingly.

## Stage C: reading layer

For each prior variant × choice model × slack:
- choice models: uniform-valid; cost-softmax with τ ∈ {15 (true), 40}; risk-averse with β = 1;
- slack ε ∈ {0.05 (true), 0.15};
- readings per town independent from the prior (κ = ∞), and hierarchical with κ ∈ {3, 10, 30} (200 Dirichlet draws), compared by log marginal ratio.
Cost for the cost model is the per-particle burden index of each design in each town, using the town's fee table under the model's fee split. Stage C uses all pooled particles.

## LLM baseline

Tool-less Opus, 3 repeats averaged, given the statute, the 11 design descriptions, the 12 towns' evidence, and Q1–Q5. Asked, per town: P(yes) for each question ("the reading this agency appears to act on") and a probability over the 11 designs. Output: `W4/llm_readings001/`.

## Predeclared readings

1. **Recovery under the true choice model (cost, τ = 15, ε = 0.05, P-pool).** Mean log score of each town's true reading beats the prior's, and the per-question Brier score beats the prior's for Q1 and Q2 (the questions that constrain designs most). Q3–Q5 are expected to stay near their priors: Q3 only matters when an inspection's attendance is at issue, Q4 only when mandated waits approach the deadline, Q5 only through fees, which are town choices.
2. **Wrong choice model.** Under uniform-valid, Q1's posterior is biased toward "desk insufficient" wherever towns chose inspection-only designs for cost reasons (the size principle misreads a cost preference as a strict reading). Under risk-averse, readings are pulled toward permissive answers. Report the shift in each town's MAP reading.
3. **Design recovery** should be nearly unchanged across choice models: the evidence, not the prior, decides S_t where records exist.
4. **Population κ.** The hierarchical variants should not beat κ = ∞ decisively (12 towns, readings drawn independently in truth); report the log marginal ratios without selecting.
5. **Elicitation.** Report element reliabilities and the share of LLM ambiguities that map to none of Q1–Q5. That share is the residual's empirical footing.
6. **LLM baseline.** Descriptive comparison of per-town question probabilities against Stage C under the true choice model, with Brier scores. No superiority claim from one world.

## Limits declared in advance

- Truth uses the same question set Q1–Q5 that the model uses, so this round tests inference, not question discovery. Residual mass therefore measures slack, not missing questions.
- Serial designs only.
- The RSA mapping to Q1 is a stipulation; its influence is bounded by λ = 0.5 and is switched off in P-llm.
- One world; no calibration of elicitors is possible from one statute.

## Addendum 4-A (2026-09-29, after Stage A, before Stage B/C results)

Stage A ran as declared: 6 Opus parses, $0.23–0.34 each, all parsed. Two findings change the plan's reporting, neither the fits.

1. **The parse disagrees with my hand-coded skeleton on one element.** All six parses mark E7 ("denial may rest only on ineligibility, incompleteness or the nuisance determination") as *absent* (mean confidence 0.80): the text names no exhaustive list of denial grounds. My validity constraint C6 treated limited grounds as a concrete requirement. C6 is therefore a *question*, not a skeleton element, and should join Q1–Q5 in later rounds ("Q6: does the statute limit the grounds for denial?"). It does not affect this round's results: none of the 11 designs adds a denial ground, so V_r is unchanged. E1–E6 were marked present by 6/6 parses (confidence 0.77–0.97; lowest for the implied completeness check and the eligibility scope).
2. **The parse-frequency source is degenerate.** Across six parses every direct probability fell on the same side of 0.5, so parse frequency is 0 or 1 for every question. In a log-linear pool that source, clipped at 0.001, would dominate. P-pool is run exactly as declared and reported, and one additional variant **P-pool2** (direct probabilities λ = 1 plus RSA for Q1 at λ = 0.5, no parse frequency) is added. P-pool2 is the variant used for the predeclared reading 1 if P-pool is shown to be degenerate.

Other Stage-A numbers, for the results: 26.3 ambiguities per parse in an 8-line statute (Massey et al. report ~33 per 104 lines with human analysts); by type 64 incompleteness, 36 lexical, 26 semantic, 18 vagueness, 14 referential; **80% of ambiguities map to none of Q1–Q5** (scope of "resident" and "single-family dwelling", per-lot vs per-resident cap, permit renewal and revocation, site-plan precision, which property lines). Direct P(yes): Q1 0.64, Q2 0.18, Q3 0.45, Q4 0.81, Q5 0.16, against the truth-generating 0.60 / 0.35 / 0.90 / 0.80 / 0.50.

## Addendum 4-B (2026-09-29, after the LLM baseline, before Stage B/C results)

**Generator flaw, Q5.** In `truth_w4.py` each town's fee schedule (whether it charges separate notice or inspection fees) is drawn independently of its reading of Q5. A town whose true reading says separate fees are *not* authorized can still charge them. So in W4, fee evidence carries no information about Q5, and any method that infers Q5 from fees (the LLM does: P ≈ 0.85 where a separate fee is listed, ≈ 0.27 otherwise) is penalized for a plausible inference. Q5 is therefore reported but excluded from the headline reading-recovery comparison. The fit already running uses this world, so the world is not regenerated; the flaw is fixed in the next world (fees conditional on Q5).

**LLM baseline (3 repeats, $0.61–0.65 each):** correct top design in 12/12 towns. Question probabilities are driven by the observed design: towns using notice get P(Q2 = yes) ≈ 0.85, though only 2 of the 5 notice-using towns hold that reading in truth; this is the size-principle attribution error the plan predicted for uniform-valid choice, made by the LLM.
