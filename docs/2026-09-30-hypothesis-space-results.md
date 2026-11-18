# Hypothesis-space implementation: mechanics complete, world results pending

2026-09-30. Implements the [predeclared plan](2026-09-30-hypothesis-space-plan.md).
**The layer and reader pool are ready. No claim of improved posterior recovery is
possible yet: the compatible Stage-B jobs have not produced particles.** This
closes the bounded implementation pass; it does not close the empirical experiment.

## What was implemented

`pipeline/procbench/toy_statute/hypotheses.py` adds uncertainty over the reader's
questions, validity matrix and answer prior. It calls the existing Stage-C kernel;
there is no new process sampler or competing likelihood implementation.

The hypothesis H is shared across towns. Each H supplies its own within-town
reading model. H and the choice-model grid receive joint posterior weights,
proportional to their priors times their estimated marginal likelihood ratios.
Grid cells are **not** averaged uniformly after observing data. Both P-reader and
P-class priors are reported, alongside single-reader comparators.

Canonicalization preserves the original risk-choice reading measure and the
finite-kappa Dirichlet floor. Equivalent hypotheses share a calculation, preventing
Monte Carlo differences from masquerading as Bayes factors between copies.
Chunking reuses the same population-weight draws across particle chunks. Residual
reading probability stays unknown, rather than becoming evidence of unlawfulness.

Stage C optionally returns joint particle/town/design weights. These support
burden means, per-step and decision-step roll-ups, applicant interactions, expected
step executions, and the declared hen counterfactual. Parameter/design dependence
is retained. Conditional-mean uncertainty intervals are **not** predictive
individual-case timing intervals. Fee splits retain the existing Dirichlet(1)
residual allocation convention; no fee-reading likelihood has been invented.

The runner rejects old-target particles, incomplete/failed fits, changed evidence,
mismatched likelihood/model projections, and old kitchen fee evidence. It reads
only public mechanics projections, reader outputs and fitted artifacts. Author
rules enter only as an explicitly declared oracle hypothesis exported by the
separate evaluator. That oracle uses flat .5 answer priors, not planted frequencies.

## Reader pool

Seven new GPT readers completed one blind pass each. The existing kitchen reader
was preserved. Claude concurrently supplied its eight readers; these are genuine
Claude-session outputs, not GPT replacements.

| Statute | Usable readers | Distinct grid-wide classes | Designs |
|---|---:|---:|---:|
| Hens v2 | 8 | 8 | 11 |
| Kitchen | 8 | 8 | 12 |

New GPT readers supplied 6–7 major questions each. All seven passed their one
schema/compiler check. Claude's own validation receipts are retained; the common
compiler accepted all eight. The inherited kitchen output passed the compiler;
its meta-rule lives in its original NOTES.md. Its original model, prompt variant
and timestamps are **unknown**, so kitchen is not demonstrably a perfectly
balanced model/prompt factorial. We did not regenerate or relabel it.

Blindness is by instruction, not filesystem sandbox. Public-only input files
were placed in isolated temporary directories; prompt hashes and observed timing
records are retained. No reader saw another reader's output or author truth in
its assigned task. Correlated readers are not independent votes. Here all eight
are distinct classes, so P-reader and P-class coincide within each statute;
that is a property of this pool, not a universal equivalence of the priors.

Artifacts: `runs/toy_statute2_20260929/readers_hs001/`:

- `<statute>/<reader>/reading.json`, metadata, prompt, timing where available;
- `validation.json` for our seven new plus inherited reader; Claude's separate
  `claude_readers_filed.json` records its eight;
- public reader inputs and `model_public.json`/`model_projection.json`;
- `oracles/hen2.json` and `oracles/kitchen.json`, evaluator exports only.

The original preparation roster's `claude_pending` is a historical scheduling
field; it is superseded by `claude_readers_filed.json`, not a current missing count.

## Bounded verification and actual results

**89 focused tests pass** (4.51 seconds): the previous 68 and 21 new cases.
Tests cover all five requested invariants, risk-measure and alpha-floor
counterexamples, chunking, joint-weight marginals, residual handling, the
truth-blind runner's old-target rejection, scoring ties, and fast burden means
against the existing estimands. Canonical/uncollapsed finite-kappa equality is
tested with **coupled, aggregated Dirichlet draws**, not a spurious 1e-12 comparison
of independent Monte Carlo runs.

One integration fixture ran all 30 grid cells with all eight readers per statute:

| Mechanics fixture | Runtime | Largest posterior-minus-prior H weight |
|---|---:|---:|
| Hens v2 | 0.68 s | 1.11e-16 |
| Kitchen | 0.83 s | 1.11e-16 |

This deliberately uses three fabricated particles, two towns, and **constant
likelihoods with no information**. Correctly, no reader gains weight. It is not
a fitted-world speed benchmark or evidence of recovered truth. Artifact:
`runs/toy_statute2_20260929/hs001/mechanics.json`.

## Empirical results still unavailable

The bounded sk3 availability check found v2 `fitE001/launch_manifest.json` for
HEN2, HK1b_v2 and HK2_v2, but no saved particle files in any of the three.
The kitchen suffixes denote Claude's regenerated fee-evidence corpora, corresponding
to the plan's HK1b/HK2 worlds. Existing jobs were not changed, stopped or duplicated.

| Required result | HEN2 | HK1b_v2 | HK2_v2 |
|---|---|---|---|
| Lawful-set Brier / true-set log score | pending particles | pending particles | pending particles |
| Design log score / MAP accuracy | pending | pending | pending |
| Reader ranking / oracle top two | pending | pending | pending |
| BMA burden / step / counterfactual recovery | pending | pending | pending |
| Observed Bayes-factor separation and importance ESS | pending | pending | pending |

None of the predeclared directional hypotheses has a holds/fails verdict yet.
Eight distinct classes does not establish empirical identifiability. Finite-kappa
integration is Monte Carlo, and importance ESS is not a convergence certificate.
Independent Stage-B runs and marginal-likelihood Monte Carlo error still matter
when interpreting any future Bayes factors. No same-evidence LLM victory is claimed;
the kitchen LLM runs need the regenerated evidence. The evaluator accepts matched
burden outputs but explicitly marks unverified evidence parity.

## Remaining limitations and next action

The per-question reader schema is conjunctive. It cannot express arbitrary
interactions; free-text `valid_when` descriptions are not executed. Several readers
also condition their interpretation on typical traffic, fee or timing assumptions.
These are candidate-model limitations, not evidence that those assumptions hold.
Uncertainty is over a finite supplied candidate pool, not every possible meaning.
For independent town readings, residual rho and epsilon still confound through
`rho + (1-rho)*epsilon`; the declared sensitivity grid does not separately learn them.
Edited-text transfer and text-likelihood/RSA remain deferred as recorded in the plan.

When completed v2 fits pass their numerical gate, run each world exactly once per
condition (readers only; readers + explicitly exported oracle). Example, from the
repository root, with a copied/completed HEN2 fit:

```sh
python runs/toy_statute2_20260929/run_hypotheses_hs001.py \
  --fit runs/toy_statute2_20260929/HEN2/fitE001 \
  --evidence runs/toy_statute2_20260929/HEN2/evidence \
  --model-public runs/toy_statute2_20260929/readers_hs001/hen2/model_public.json \
  --readers runs/toy_statute2_20260929/readers_hs001/hen2 \
  --out runs/toy_statute2_20260929/HEN2/hs001/readers

python runs/toy_statute2_20260929/evaluate_hypotheses_hs001.py score \
  --package runs/toy_statute2_20260929/hen_package.json \
  --truth runs/toy_statute2_20260929/HEN2/truth/world.json \
  --run runs/toy_statute2_20260929/HEN2/hs001/readers \
  --out runs/toy_statute2_20260929/HEN2/hs001/readers/scores.json
```

For the oracle condition add `--oracle readers_hs001/oracles/hen2.json` with its
full repository-relative prefix, and choose a fresh sibling output directory.
Kitchen uses its own public projection/readers and corrected `_v2` evidence.
No waiting or polling loop was started. Source/tests/docs remain uncommitted.
