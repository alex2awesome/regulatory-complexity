# Uncertain hypothesis spaces: bounded implementation plan

2026-09-30. Implements the [workflow](2026-09-30-uncertain-hypothesis-space-workflow.md).
This is a toy reading-layer experiment, not a new real-corpus collection queue.

## Scope and stopping rule

One implementation pass: hypothesis loader, canonicalization, shared-hypothesis
Stage C, Bayesian model averaging (BMA), runner, evaluator, focused tests, GPT
readers and a Claude reader packet. One Stage-C pass per available compatible
world/condition. No new Stage-B jobs, retries of failed readers, or polling for
missing fits. Close with a results document even if empirical results are blocked.

At planning time no completed v2-target fit for HEN2, HK2 or HK1b is available
locally. Old-target particles are not substitutes. A mechanics fixture is not
posterior recovery. Claude-family readers must come from Claude, not GPT agents
labelled Claude. Budget: seven new GPT reads, one validation per reader, the
focused toy tests, and one bounded fit-availability check.

## Frozen experiment

- Worlds: HEN2, HK2, HK1b; target `toy-process-v2-20260930`. Kitchen evidence
  must use corrected fee generation. Fit evidence/model hashes must match.
- Eight readers per statute, **including** the existing kitchen reader in the
  kitchen eight. This resolves the workflow's conflicting "16 + existing 1"
  deliverable in favor of its K=8 specification. Four GPT and four Claude per
  statute; no claim of a completed cross-family experiment before Claude arrives.
- Two prompt variants per family: neutral and explicit meta-rule elicitation.
  New readers use only an isolated public file and schema; blindness is by
  instruction, not a filesystem sandbox. The inherited reader's original
  timestamp/prompt are unknown, not fabricated. Its existing notes state a
  meta-rule; its original prompt stratum is unknown and reported separately.
- P-reader: uniform over valid readers. P-class: uniform over distinct model
  classes, then uniform within class. These are correlated candidate predictors,
  not independent votes. Oracle conditions add one author hypothesis, supplied
  explicitly by the evaluator, never obtained secretly by a fitter.
- Choice grid: uniform; cost tau=15/40; risk beta=2/5. Epsilon .05/.15/.30;
  kappa independent (`None`, historically labelled infinity) / 10; rho .05.
  Uniform **prior** over grid cells; posterior averaging weights cells by evidence.
- Same Stage-B particles for all H and psi, at most 2,000 selected once with
  seed 20260930; 200 population-weight draws for finite kappa. No adaptive
  doubling until a desired answer appears. Report importance ESS and limitations.
- Report readers-only and readers-plus-oracle conditions separately.

## Mathematical qualifications decided before results

1. H is global: integrate it **outside** the product over towns. Within H,
   kappa controls whether towns share a population-weight vector.
2. Equal prior-weighted lawful-set distributions alone do **not** imply equal
   likelihood under risk choice: the unweighted share of original readings
   permitting each design also matters. Class signatures retain this profile.
3. Finite kappa currently floors each original Dirichlet coordinate at 1e-6.
   Canonicalization aggregates those actual alpha values, not just nominal
   probabilities. Classes across this grid must agree in both representations.
   This preserves the existing target rather than silently changing the floor.
4. Canonical rows are sorted; equivalent hypotheses reuse the same finite-kappa
   integration. Independent Monte Carlo noise must not manufacture Bayes factors
   between copies. Finite-kappa integration and Stage-B importance reweighting
   are approximations, not exact posterior sampling or a convergence certificate.
5. Residual reading means **unknown lawful set**, not an empty set. Report
   known-set subprobabilities, residual mass, conditional-known lawful probability
   and lower/upper lawful bounds. Score Brier conditional on known and report
   unconditional true-set log score with floor 1e-12 (and zero-support count).
6. Different readers' questions have no privileged alignment. Reader accuracy
   means that reader's lawful-set posterior score against the true lawful set,
   not matching answers to questions with coincidentally similar names.
7. Burden BMA must retain the joint particle/design weights; separately averaging
   marginal particles and designs would lose their dependence. Report conditional
   estimand means/intervals, not newly sampled process fits. Fee uncertainty remains
   the existing declared plug-in/fee-split convention, not a fee-reading likelihood.
8. Reader schema uses a conjunction of per-question constraints. It cannot encode
   arbitrary interactions. Existing free-text `valid_when` expressions are not
   executable rules; do not silently claim they were fitted. This limitation and
   inherited provenance gaps must accompany reader results.

## Evaluation and completion

Evaluator only: true lawful-set log score/Brier, design log score/MAP, Spearman
posterior reader rank versus individual posterior accuracy, oracle rank, burden
roll-ups/per-step summaries and hen counterfactual where defined. Compare BMA,
individual readers, hindsight best and median, oracle, and a **no-data** prior
lawful-set BMA. Compare an LLM only where its existing outputs match the estimand.
Predeclared directions: BMA improves on median reader true-set log score;
reader weight/accuracy correlation positive; oracle ranks in top two. Report
holds/fails/unavailable without tuning. No inferential claim from an incomplete
reader roster or failed particle diagnostics.

Identification: distinct classes, predictive design-law separation on supported
designs, observed log Bayes-factor range, and importance ESS. Support overlap
alone is not evidence that these observations distinguish the hypotheses.

Outputs: `runs/toy_statute2_20260929/readers_hs001/`, separate `hs001/` run
directories, `hypotheses.py`, runner/evaluator, focused tests, and one
[results document](2026-09-30-hypothesis-space-results.md). Existing fit directories
are read-only. No commits or deletes.

Optional A (edited-text forward prediction): deferred until the original-text
experiment is evaluated. Posterior compatibility with behavior is not general
reader reliability, and transfer to edits needs a separate predeclared test.
Optional B (text likelihood/RSA): deferred; an uncalibrated factor can dominate
the behavioral evidence. Neither is necessary to implement uncertainty over H.

Execution clarification (before any fitted-world Stage C): Claude has supplied
all eight Claude readers and launched v2 fits on HEN2, HK1b_v2, HK2_v2. The `_v2`
kitchen directories are the corrected-evidence versions required above. Oracle
answer priors are flat .5, not author-planted frequencies. The inherited kitchen
reader's model identity is also unknown, so do not claim verified family balance.
