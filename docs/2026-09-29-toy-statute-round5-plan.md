# Toy statute round 5: a second statute, blind question discovery (predeclared, 2026-09-29)

Alex asked (2026-09-29) whether to extend the hen statute or generate a new one, and to use Opus/Sonnet subagents for generation. Decision: a second statute, because question discovery, cross-statute calibration and statute-agnostic code all need one. Written before any Stage-B fit, Stage-C reweighting or LLM baseline run on this statute. Smoke checks done: generation, model construction and one log-posterior on HK1; the generic validity evaluator reproduces the author's validity counts for all 12 designs.

## Roles (two subagents, isolated)

- **Author** (Opus): wrote the statute package `runs/toy_statute2_20260929/statute_package.json` and `AUTHOR_NOTES.md`: text, referenced-law summary, step catalog, 12 designs, **hidden** questions (7) with author probabilities, validity rules in data form, and the truth block. The hidden keys are `questions`, `validity_rules`, `truth`.
- **Blind reader** (Opus): saw only `statute_public.json` (text, referenced-law summary, catalog without d-step tags, designs, no notes), in a directory outside the repo, with an instruction to read nothing else. Output `runs/toy_statute2_20260929/blind_reader001/reading.json`: decision steps, skeleton elements, 28 questions (7 marked major, with p_yes), per-design validity under each major question's yes/no, unexplained steps. Residual isolation risk: the agent had repository tools; the instruction, not a sandbox, enforced blindness.

## The statute (public)

Home Kitchen Food Business Act, 7 sections: registration with a list of products, labels and a food-safety course; determination that products are not potentially hazardous, labels adequate, kitchen sanitary; "may require a sample" of uncertain products; "may inspect"; operations with "significant customer traffic" must also comply with the fictional Home Occupation Standards Act (15-day comment, hearing on 10 days' notice); 20-day clock from receipt of the form; fee capped at reasonable cost. Designs K1–K12 combine desk review, lab test, zoning clearance, notice + comment (+ hearing), site inspection, with issue-at-inspection variants.

## Worlds (truth, generator only)

`truth_package.make_world` implements the author's truth block: 14 towns with a public density covariate; readings per town (independent questions except Q1_significant_traffic, whose P(yes) = expit(1.2 − 3·density), the Lassiter–Goodman direction); expected fees from the fee reading; cost-softmax choice among designs valid under the author's rules (τ = 15, ε = 0.05); realized fees conditional on the reading (the hen's fee flaw fixed); process step laws from the block; admin records in 6 towns (40 each), 15 reports per town.

- **HK1**: the author's seed. Realized designs K2 ×4, K1 ×3, K7 ×2, K3, K4, K9, K10, K11. **Four of 14 towns chose designs invalid under their own reading** (probability 0.4% each under the choice model; the builder is correct by seeds 1–3, which give 0, 0, 1 invalid). Kept as the main world without reselection; it is an unplanned test of the slack assumption.
- **HK1b**: seed 1. Designs K3 ×4, K6 ×3, K2 ×3, K10, K4, K7, K8; no invalid choices. Predeclared second world; both are reported.

## Question mapping (declared now, used only for scoring)

| Reader (model side) | Author (truth side) | Note |
|---|---|---|
| R-Q1 routine sampling of every product | A-Q6_routine_sampling | direct |
| R-Q2 sanitary finding without inspection | A-Q3_inspection_discretionary | direct |
| R-Q3 must the health authority itself determine HOSA compliance | — (author assumes yes) | reader-only; scored against constant "yes" |
| R-Q4 ordinary operation = significant traffic | A-Q1_significant_traffic | direct; density-dependent in truth |
| R-Q5 Sec. 5 imports HOSA's procedure | A-Q2_hosa_imports_procedure | direct |
| R-Q6 clock starts on the form even if incomplete | A-Q4_clock_starts_on_form | direct; affects compliance, not validity |
| R-Q7 clock pauses for corrections, sampling, neighbour procedure | A-Q5_clock_tolled_for_hosa | reader's is broader |
| (minor only) separate fees | A-Q7_separate_fees | author question the reader demoted; not modelled |

**Discovery result so far (Stage A):** the blind reader found 6 of the author's 7 hidden questions as major, demoted one (fees) to minor, and added one the author did not pose (R-Q3). It also reads the meta-rule differently: the reader treats unrequired procedure (zoning check, notice) as *unauthorized* unless a reading requires it, so no design is valid under every reading; the author treats agency-side procedure as permitted, so K9 is valid everywhere. This is a genuine interpretive divergence about agency discretion and will show as a systematic mismatch between the reader's validity matrix and the author's.

## Model side

- Design space: the package's 12 designs (`spec.load_package`).
- Questions: the reader's 7 majors. Validity matrix: conjunction of the reader's per-question valid_if_yes / valid_if_no (`validity_rules.reader_validity_matrix`). The reader's per-question judgements are marginal ("valid under some answers to the other majors"), so the conjunction is an approximation of the reader's joint view; declared.
- Priors: **P-reader** (the reader's p_yes per major) and **P-flat**; residual ρ = 0.05.
- Stage B: `smc.py --package … --center-towns --blocks desk_review+decision_issue,neighbor_notice+comment_period --gate v2`, **10,000 particles**, 2 runs, 30 moves, seed 20261001, 32 workers, one execution per world (`HK1/fitB001`, `HK1b/fitB001`). Parameters: 10 day steps + 6 hour steps + 14 towns × 3 + observation terms.
- Stage C: choice models uniform, cost τ ∈ {15, 40}, risk β = 1; ε ∈ {0.05, 0.15}; κ ∈ {∞, 10}. Cost uses the catalog-driven `readings.burden_indices`.
- **Oracle comparison:** Stage C also run with the author's validity matrix and questions (`validity_rules.author_validity_matrix`), P-flat prior. This is not a fair method (it uses hidden rules); it bounds what the reader's discovery error costs.
- LLM baseline: tool-less Opus × 3 with the package's design texts, the 14 towns' evidence and the reader's 7 major questions, asked per-town P(yes) and design probabilities.

## Predeclared readings

1. **Design identification** should be near-perfect for Bayes and good for the LLM, as in round 4.
2. **Discovery cost.** On the mapped questions, the reader-based Stage C (true choice model) should beat its prior on R-Q2 (inspection) and R-Q4/R-Q5 (traffic and notice), where designs differ; the oracle should beat the reader-based run, and the gap is the discovery-and-mapping cost. Report per question.
3. **The meta-rule divergence** should show as reader-based Stage C assigning "yes" to R-Q3/R-Q4/R-Q5 in towns that run zoning or notice designs for cost reasons, i.e. the same attribution error the LLM made in round 4, now built into the reader's validity matrix. Report the towns.
4. **Density test (Lassiter–Goodman).** Correlate each town's posterior P(R-Q4 = yes) with density, for Bayes and the LLM. Truth: P(yes) falls from 0.74 to 0.16 across the density range. Report the Spearman correlation and whether the prior alone (constant) would have scored better on R-Q4 than the posterior. This is the first test with any bearing on the RSA hypothesis; one world, so descriptive.
5. **HK1's invalid choices.** With ε = 0.05 the model will misread the four invalid-choosing towns' readings; ε = 0.15 should do better on them. Report per town; compare with HK1b.
6. **Gate.** 10,000 particles for ~70 parameters; a fail is reported and Stage C runs regardless, labelled.

## Limits declared in advance

- One reader; its p_yes are a single elicitor, uncalibrated. No parse-frequency source (degenerate in round 4).
- Conjunction approximation of the reader's validity.
- Serial designs only; outcomes not included this round.
- Reader-only R-Q3 has no truth variation (constant yes); scoring it is a check on false confidence, not on learning.
- Isolation of the blind reader rests on instruction, not a sandbox.

## Stage A numbers (recorded after the blind reading, before Stage B/C)

- Reader's validity matrix vs the author's, over the 128 author readings × 12 designs (reader-only R-Q3 set to yes): **62.5% agreement**. Per design: K1 0.75, K2–K4 0.50, K5 0.88, K6 0.75, K7 0.50, K8 0.62, K9 **0.25**, K10 0.88, K11 0.75, K12 0.62.
- Designs valid under every reading: author K9 (128/128); reader none (K2–K4 128/128 in the reader's matrix, but K9 only 16/128). The reader's matrix is much stricter on any design that adds zoning or notice.
- Towns whose *true* design is valid under the reader's matrix at their true reading: HK1 11/14, HK1b 12/14. The reader-based model will therefore treat 2–3 towns per world as slack (invalid practice) or misattribute their readings.
- Stage B launched 21:58 PDT on sk3: HK1/fitB001 and HK1b/fitB001, 10,000 particles, 32 workers each.

## Addendum 5-A (2026-09-29, ~22:45 PDT): fits stopped after the independent audit

`docs/2026-09-29-toy-statute-full-chain-audit.md` (independent agent) found two defects in the process likelihood that the round-5 fits were sampling: completed applicant reports omit the completion-selection factor P(posting day ≥ completion) inside the latent-duration sum (F2), and the FFT convolution can alias sums longer than the 1,024 grid and renormalizes tail mass away (F3). Both confirmed here (F3 reproduced: three 400-day steps land at day 176). The HK1/HK1b Stage-B fits were killed at temperature stage ~2 rather than spend hours sampling a target that will change. They will be relaunched, under the same predeclaration, after the likelihood corrections; the LLM baselines already run stay valid (they do not depend on the likelihood). The round-3b W0x25 fit was left running: it is a Monte Carlo precision comparison of an already-fitted target and remains informative for that purpose only.
