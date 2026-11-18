# Toy statute round 3: composite reparameterization (predeclared, 2026-09-28)

Alex approved the composite reparameterization on 2026-09-28 ("great, do
composite reparameterization"). Written before any round-3 fit is run.

## Change

`Model(blocks=[...])` samples each jointly-identified block of adjacent steps
in new coordinates:
- `blkT = log(E_a + E_b)`, the log block mean;
- `blkU = logit(E_a / (E_a + E_b))`, the first step's share;
- where `E = exp(mu + sigma^2/2)`.

These replace `mu_a` and `mu_b`. The map back is
`mu_a = T + log p − s_a²/2` and `mu_b = T + log(1−p) − s_b²/2`, with
`p = expit(U)`. It has |Jacobian| = 1 (proved analytically and tested
numerically in `tests/test_toy_statute.py`), so the prior on the original
parameters is evaluated unchanged. **Same model, same posterior, different
sampler geometry.** Tests also confirm an exact round trip and identical log
posterior at matching points.

**Blocks:** (desk_review, decision_issue) and (neighbor_notice,
comment_period). These are the pairs that are always adjacent with no
observed boundary event in W0/W1 without a "review complete" or "notice
mailed" record. They are the pairs the identifiability diagnostic flags, and
they fail most often in round 2.

## Runs (sk3, parallel, 8 workers each)

All runs use the town-centered model, `--blocks
desk_review+decision_issue,neighbor_notice+comment_period`, 2 runs × 3,000
particles × 30 moves, seed 20261001, gate v2, and one execution each.

| id | world | prior |
|---|---|---|
| W0/fitB001 | W0 | vague |
| W0m/fitB001 | W0m | vague |
| W0x5/fitB001 | W0×5 | vague |
| W0x25/fitB001 | W0×25 | vague |
| W1/fitB001 | W1 | vague |
| W1m/fitB001 | W1m | vague |
| W1/fitB002 | W1 | LLM prior (llm_prior001) |
| W1m/fitB002 | W1m | LLM prior |

## Predeclared reading

- **Primary:** how many fits pass gate v2, compared with round 2 (1 of 10
  passed). Gate v2 treats `blkU` like any other parameter. It is expected to
  be prior-dominated (posterior SD ≥ 0.8 × prior SD) when unidentified, so it
  gets the R-hat check only. `blkT` is expected to be data-informed.
- **Secondary:** scores compared with round 2 on the same worlds. They
  should be similar where round 2 had mixed well, because it is the same
  posterior. Differences mean round 2's answers were distorted by poor mixing.
- **Reporting:** estimands that depend on a block's split (e.g. separate desk
  review vs decision-issuance days) are labelled *prior-driven* in results
  where the identifiability diagnostic does not identify them. The block total
  is the data-driven estimand.

## Addendum 3b (2026-09-29, predeclared before launch): Monte Carlo precision test

Alex approved the larger run on 2026-09-29 ("sure, you can run the larger run").

**Question.** Are round 3's remaining gate failures Monte Carlo noise, or sampler geometry?

**Design.** The same 8 fits are rerun, identical except for particles:
- the same code on sk3 (unchanged since round 3);
- the same evidence, blocks, priors, seed 20261001, 2 runs, 30 moves, and gate v2 unchanged;
- **10,000 particles** instead of 3,000;
- workers raised to 12 (24 for W0x25), for speed only.

Run ids: `fitC001` (vague) and `fitC002` (LLM prior), matching fitB001 and fitB002.

**Predeclared reading:**
- If the failures are noise, the worst between-run SMD should shrink by about √(10000/3000) ≈ 1.8, from 0.10–0.22 to about 0.06–0.12, and most fits should pass.
- If SMD does not shrink materially (less than 1.3×) on the failing parameters, the failures reflect geometry or mixing, and more particles are not the fix.
- Scores should match round 3 within Monte Carlo error.

There is one execution each, and no further escalation without a new addendum.
