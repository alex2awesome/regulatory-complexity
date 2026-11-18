# Toy statute round 6: recovery experiment on the corrected likelihood, and shared agencies (predeclared, 2026-09-30)

Written after the audit response (`docs/2026-09-30-audit-response.md`) and before any fit on the corrected likelihood. Alex's requests of 2026-09-29: expand the hen world, share agencies across statutes so agency posteriors can be learned, and (from the audit) correct the target before adding compute.

## What changed in the likelihood (all fits below use it)

F1 joint outcome counts; F2 completion selection on applicant reports (posting window published in `public_spec.json`); F3 FFT padding and tail lumping; corrected reading scorer (F6/F7); normalized risk model (F8); single unexplained-choice mass (F4); Dirichlet fee split on the default answer path. 39 tests pass, including counterexample tests for F1–F3.

## Worlds

| World | Statute | Towns | Purpose |
|---|---|---|---|
| W0, W0m | hens (6-design menu) | 3 | continuity with rounds 1–3: does the corrected likelihood change the baseline results? |
| W4 | hens (11 designs) | 12 | round-4 reading layer, now at 10,000 particles |
| HK1b | home kitchen | 14 | round-5 blind-reader test (HK1 deferred: its 4 invalid choices are a separate question) |
| **HEN2** | hens v2 package (11 designs, Q6 added, fees conditional on Q5, density → Q1) | 14 | linked to HK2 by `agencies.json` |
| **HK2** | home kitchen | 14 | linked to HEN2: same 14 agencies (speed, error rate, τ, strictness) |

HEN2/HK2 share exactly the agency traits; their readings shift by each agency's strictness s_t on questions with a declared strict answer; τ_t is per agency. Generated 2026-09-30 00:05 PDT; no invalid choices in either.

## Stage B (sk3, code snapshot `toy_statute_r6`)

Every fit: `--center-towns --blocks desk_review+decision_issue,neighbor_notice+comment_period --gate v2`, 2 runs × **10,000** particles × 30 moves, seed 20261001, uniform design prior. Run ids `fitD001`. Workers 24 each (six fits, 144 cores). One execution each; failures reported.

## Stage C and scoring

- W4: reader layer as round 4 (P-pool2, P-flat; uniform / cost τ∈{15,40} / risk β∈{2,5}; ε∈{0.05,0.15,0.30}; κ∈{∞,10}); corrected scorer; joint over Q1–Q4.
- HK1b, HK2: blind reader's questions and matrix, plus the author-oracle matrix; corrected scorer with the declared mapping (round-5 plan).
- HEN2: hen v2 package questions; validity from the package rules (identical to `validity.py` on Q1–Q5, verified); Q6 has no trace by construction and is excluded from the joint.
- Outcomes: W0o and W0o_adv refit (shared and hier) on the corrected W0/fitD001 process posterior, with the F1 likelihood; replication of the deterrence-bias check.

## Shared agencies: what this round can and cannot learn

The two linked worlds are fitted **separately** (no joint model yet). Agency posteriors are then compared across statutes:
1. **Speed.** Each agency's log-speed posterior from HEN2 vs from HK2; truth is identical. Agreement (posterior overlap, correlation of medians across the 14 agencies) is the first test that an agency-level parameter transfers across statutes.
2. **Strictness.** Per agency, the posterior P(yes) on strict-answer questions in both statutes, correlated across agencies with the true s_t. This is descriptive: separate fits cannot pool the two statutes' evidence about s_t.
3. **Cost sensitivity τ_t.** Compare log marginal ratios of cost τ=15 vs τ=40 per agency; expected to be uninformative with 14 towns.

A joint model with tied agency parameters (shared la_t across statutes; a shared strictness shift on the reading prior; a per-agency τ_t) is the planned round 7, once separate fits show the linked worlds behave.

## Predeclared readings

1. W0/W0m: gate outcomes and scores compared with round 3b (fitC001). The corrected likelihood should change per-step days modestly (completed reports are 20–45 of 80–125 records per world) and not change design identification.
2. W4: corrected-scorer reading recovery at 10,000 particles; the round-4 direction (Q2/Q3 learned, Q1/Q4 prior-driven, Bayes above prior and LLM on the Q1–Q4 joint) is expected to hold; the risk models at β∈{2,5} are compared by log marginal ratio without a rejection claim unless the ratio exceeds 5 nats under both ε and κ settings.
3. HK1b and HK2: the discovery cost (reader vs oracle) on the mapped questions; the meta-rule divergence towns.
4. HEN2 vs HK2 speed agreement: Spearman correlation of posterior median log-speeds across agencies > 0.7 if the process layer transfers.
5. Density test on both HEN2 (Q1) and HK2 (Q1) with the corrected scorer, for Bayes and the LLM.
6. Outcomes: whether the deterrence slope β is still biased low under the F1 likelihood (10-replicate check as before).

## Limits

- Separate fits: agency traits are compared, not pooled.
- HK1 (four invalid choices) left for a dedicated slack test.
- One reader, one author; no calibration of elicitors.
- The survey term's conditional-expectation approximation (F1) is declared, not exact.

## LLM baselines on the linked worlds (run before the fits returned; recorded 2026-09-30 ~00:40 PDT)

Scores use the corrected mapped scorer (P(yes) per question; joint over the listed questions), truth from each world's hidden readings.

| World | LLM design MAP accuracy | Joint log score: LLM vs prior | Brier per question, LLM (prior) | Density test |
|---|---|---|---|---|
| HEN2 (hen v2, Q1–Q5) | 14/14 | −2.52 vs −3.02 | Q1 0.28 (0.26); Q2 0.07 (0.29); Q3 0.10 (0.01); Q4 0.32 (0.25); **Q5 0.08 (0.25)** | ρ(density, P(Q1)) = +0.14; truth −0.23 |
| HK2 (kitchen, reader's Q1–Q7) | 13/14 | −4.44 vs −5.70 | Q1 0.30 (0.27); Q2 0.06 (0.27); Q3 0.16 (0.30); Q4 0.14 (0.29); Q5 0.35 (0.38); Q6 0.25 (0.25); Q7 0.25 (0.38) | ρ(density, P(Q4)) = −0.59; truth −0.37 |

Notes: with fees now conditional on the fee reading, the LLM learns Q5 from fee schedules (Brier 0.25 → 0.08), the path the audit said needed a likelihood edge; the Bayesian model still lacks that edge. On HEN2 the LLM overturns a near-certain correct prior on Q3 (0.01 → 0.10). Density correlations are descriptive: HK2's −0.59 exceeds the truth's own −0.37 because the LLM reads Q4 off zoning/notice designs, which are themselves density-linked through τ and strictness.
