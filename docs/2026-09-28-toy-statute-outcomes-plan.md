# Toy statute: outcome layer (externalities), predeclared 2026-09-28

Alex approved on 2026-09-28 ("sure") the proposed next step: "add an outcome layer to the generator: nuisance incidence, how often each safeguard catches a real nuisance, deterrence, and a mechanical validity checker". The validity checker is done: `docs/process-validity.md`.

This protocol was written after a 3-second smoke run (2 process draws, 500 particles; its output was used for timing only) and before any real fit.

## Purpose

This serves guiding points 1 and 2 of `docs/CORE_GOAL.md`: optimal processes measured by burden *and* externalities, and statute edits. Questions:
- **Q1.** Can outcome data separate how well each safeguard (desk review, site inspection, neighbour comment) catches a real nuisance, given that only three towns vary their processes?
- **Q2.** Is deterrence (burden → fewer applications → more unpermitted coops) identified from three towns?
- **Q3.** Is the answer robust when nuisance incidence differs by town and is confounded with the town's choice of process?
- **Q4.** Which design minimizes operating nuisances per would-be keeper, and does a heavier process help or hurt once deterrence is counted?
- **Q5.** How do the Bayesian model and the LLM compare on these estimands?

## Generative outcome model (truth)

This is implemented in `generate.generate_outcomes` and `truth_world.OUTCOMES_*`. It is documented in the `outcomes.py` docstring.

**Arrivals and nuisances.** Would-be keepers arrive as M_t ~ Poisson(m_t). Each coop is a nuisance with probability π_t.

**Deterrence.** Each would-be keeper applies with probability p_t = expit(α − β(B_t − 60)).
- B_t is the town's true expected applicant burden index in day-equivalents: days + 4 × hours + dollars / 5.
- Applicants respond to the town's true expected burden (its reputation).

**Screening.** Every safeguard g in the town's process flags a nuisance coop with probability d_g and a harmless one with f_g.
- The safeguards are desk review, site inspection, and the neighbour comment period.
- Any flag means denial.
- Hearings add no screening. In this toy, objections are independent of nuisance; that is a stated limitation.

**Unpermitted keeping.** People who do not apply, or are denied, keep hens anyway with probability u.

**Complaints.** An operating coop draws at least one complaint over the period with probability k1 (nuisance) or k0 (harmless). Enforcement verifies complained coops without error.

**Survey.** 400 households per town are sampled with replacement. The survey records whether each keeps hens.

**Observed per town:**
- applications and denials;
- verified and unfounded complaints, separately at permitted and unpermitted addresses;
- survey keepers.

The file is `evidence/outcomes.json`, with public notes.

**Worlds.** Both reuse W0's process world and seed; the outcome layer uses its own random stream, seed + 7919.
- Admin records, reports and web pages are byte-identical to W0 (verified).
- public_spec.json differs only by the round-2 leak fix to the S4 wording. The process likelihood does not use that text.
- So the converged process posterior `W0/fit004` (the round-2 gate-v2 pass) is reused.

| | W0o (common sense) | W0o_adv (adversarial) |
|---|---|---|
| π by town (Alder / Birch / Cedar) | 0.15 / 0.15 / 0.15 | 0.05 / **0.30** / 0.15 (confounded: the inspecting town has the most nuisances) |
| Catch rates d (desk / inspection / comment) | 0.35 / 0.75 / 0.55 | **0.60 / 0.25** / 0.70 (perfunctory inspections) |
| False flags f (desk / inspection / comment) | 0.02 / 0.03 / 0.06 | 0.05 / 0.01 / 0.15 |
| k1, k0 | 0.80, 0.05 | 0.50, 0.10 |
| α, β | 0.8, 0.04 | 0.3, **0.08** |
| u | 0.40 | 0.70 |
| m (Alder / Birch / Cedar) | 600 / 700 / 500 | 400 / 900 / 600 |

## Bayesian outcome model (`outcomes.py`)

**Likelihood.** Poisson thinning makes the observed cells independent Poisson counts: denials, verified and unfounded complaints at permitted and at unpermitted addresses, and approved-but-never-complained. So the likelihood is exact.
- The unpermitted, never-complained cell is summed out inside the survey binomial. This is exact to < 1e-4 nats against the full sum (tested).
- The survey is modelled as binomial with the true keeper count.

**Cut model.**
- J = 24 process draws, evenly spaced over the pooled fit004 particles.
- Each draw supplies each town's structure (sampled from its exact structure posterior), its fee table (Dirichlet split), and the burden index under all six designs.
- One outcome SMC runs per draw, and draws are pooled with equal weight.
- Outcome data do not update the process posterior.

**Models** (priors are normal on the unconstrained scale, listed in `outcomes.PRIOR`):
- **M_shared**: one π for all towns.
- **M_hier**: logit π_t = μ + τ z_t (non-centred).

Both models share the following priors:

| Parameter | Prior |
|---|---|
| Catch rates d | logit N(0, 1.2) |
| False flags f | logit N(−3, 1) |
| k1 | logit N(0.5, 1.2) |
| k0 | logit N(−2.5, 1) |
| α | N(0, 1.5) |
| log β | N(log 0.03, 1) |
| u | logit N(0, 1.2) |
| log m_t | N(log 600, 1) |

**Sampler.** Vectorized tempered SMC: 2,000 particles, adaptive tempering at ESS/2, 10 random-walk moves per stage with an adapted scale. Two independent runs with seeds 20261101 + 1000r and the same process draws.

**Gate:**
- the largest between-run standardized mean difference over parameters is < 0.1;
- the largest between-run median shift over estimands is < 0.2 SD.

There is no automatic retry. A failure is reported, and any rerun gets an addendum.

**Fits:** 4 fits (2 worlds × 2 models) → `runs/toy_statute_20260926/{W0o,W0o_adv}/outfit_{shared,hier}001/`.

## LLM baseline

Tool-less `claude -p --model opus` with 3 repeats, averaged, as in round 2. The prompt contains:
- the statute and process evidence, as in `llm_baseline002`;
- `outcomes.json`;
- the outcome definitions.

It answers the same outcome estimand keys as [q05, q50, q95]. Outputs go to `runs/toy_statute_20260926/{W0o,W0o_adv}/llm_outcomes001/`.

## Estimands (`outcomes.estimand_keys`)

**Global:**
- catch rates d_desk, d_insp, d_nb;
- false-flag rates f_desk, f_insp, f_nb;
- u and β.

**Per town, under its current design:**
- π;
- P(detect | nuisance) and P(wrongful denial | harmless);
- the nuisance share among permits;
- P(apply);
- operating nuisances per 100 would-be keepers;
- wrongful denials per 100;
- unpermitted keepers per 100;
- the burden index.

**Per town × design S1–S6 (counterfactuals):** P(apply), operating nuisances per 100, wrongful denials per 100, and the burden index.

**Scoring.** Scaled 90% interval score with floors: probabilities 0.05, per-100 quantities 1, burden index 1, β 0.01. We also report coverage and head-to-head wins, as in round 2.

## Predeclared expectations (to be checked, not tuned toward)

1. **W0o, M_shared.** Posterior SD contraction ≥ 50% for d_desk, d_insp and d_nb. Structure variation plus complaint data identify them.
2. **β contraction < 50%.** With three towns, and two of them at similar burden, deterrence is weakly identified. If it contracts more, report why.
3. **W0o_adv.**
   - M_shared attributes Birch's excess nuisances to its inspection: d_insp is biased upward, and its 90% interval misses the truth, 0.25.
   - M_hier covers d_insp. Complaints at unpermitted addresses reveal π_t independently of screening.
4. **Design ranking.** In both worlds, compare operating nuisances per 100 across S1–S6 for each town. Report whether the ranking by operating nuisance differs from the ranking by burden (deterrence counteracting screening). Combine with validity (τ = 1) as in `docs/process-validity.md`.
5. **LLM.** In W0o, where the truths are close to common sense, the LLM is competitive on catch rates. In W0o_adv it is worse on d_insp and π_Birch. This is descriptive: one world per condition.

## Limits declared in advance

- **Deterrence is modelled as a response to expected burden only.** No heterogeneity; no learning.
- **Enforcement verifies perfectly.** Complaints are independent of permit status.
- **Hearings do not screen.** Objections are independent of nuisance.
- **One outcome period.** No dynamics, and no feedback from complaints to the town's process choice.
- **Counterfactual fees.** A design keeps the town's current fee amounts for items whose step it contains. New steps carry no fee. Truth uses the same rule.
- **Simulated behaviour.** Real deterrence and screening would be estimated from observational data across jurisdictions, with the confounding problem that W0o_adv caricatures.

## Addendum O-A (2026-09-28, after the W0o fits; diagnostic, not a retry)

Both W0o fits passed the gate. All three methods (M_shared, M_hier, LLM) put the desk-review catch rate below its truth of 0.35. For M_shared the estimate is 0.145, with a 90% interval of [0.05, 0.27].

Suspected mechanism: denial counts identify π·d + (1 − π)·f, so a safeguard's catch rate trades off against its false-flag rate. The false-flag prior (median 0.047) sits above the truth (0.02).

To tell a systematic bias from one unlucky dataset, we fit 10 replicate outcome datasets from the same W0o truth:
- seed offsets 7920–7929;
- M_shared, J = 4 process draws, N = 1,000 particles, 2 runs, no gate;
- we report the 90% coverage of key estimands.

Outputs are in `runs/toy_statute_20260926/W0o_rep/` and `W0o_rep.log`. This is not a replacement fit: the predeclared W0o results stand as scored.
