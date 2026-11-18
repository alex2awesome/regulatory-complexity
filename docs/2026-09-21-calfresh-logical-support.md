# CalFresh: logical support is a model assumption, not extra evidence

2026-09-21. Development sensitivity within the existing occupancy model. Real
CalFresh only; no new retrieval, reading queue, timing fit or synthetic work.

## Why this is worth testing

The initial-application action vocabulary defines filing as submitting an
application and receipt as receiving/registering/dating that filing. Independent
binary availability indicators nevertheless allow receipt without filing.
Adding existing administrative evidence does not eliminate this inconsistency:
roughly eight percent of county/draw cells omit filing while retaining other
actions. This is not proof that county applicants bypass filing.

We will test **only** the narrow implication

`accept_and_date_application => file_application`.

Its basis is the adopted action meanings in the same initial-application
scope. It is not a new county observation, a current-law claim, or an inference
that every applicant personally completes filing. Receipt and submission can
be one transaction; no separate visit, duration or administrative resource
cost follows. Filing without recorded receipt and all-zero inventories remain
in support. Other actions do not acquire prerequisites automatically.

The declaration binds the expanded action definitions and source-reviewed
execution semantics. The target still pools the historical source snapshots,
includes newly filed reapplications, and excludes recertification. This does
not resolve the historical-transport assumption. Universal filing is a
stronger target definition and is **not** being imposed.

## Statistical target

For county j, the unconstrained occupancy prior is a product of Bernoulli
probabilities with `logit(psi[j,s]) = alpha[s] + u[j]`. Under implication set C:

`p_C(z[j] | alpha,u) = 1_C(z[j]) p(z[j] | alpha,u) / Z_j(alpha,u)`.

For this single implication, with A=receipt and F=filing,

`Z_j = 1 - psi[j,A] (1 - psi[j,F])`.

The hierarchy and source-detection priors remain unchanged. This normalizer
is essential: without it the condition supplies artificial evidence favoring
hyperparameters under which the unconstrained prior already satisfies the
rule. In a county without readings or anchors the integrated likelihood must
remain exactly one, for every hyperparameter value.

Existing evidentiary anchors, if supplied by another caller, restrict the
likelihood, not this prior normalizer. This CalFresh experiment adds no anchors.
Structural assumptions cannot be submitted through `known_presence`.

Small connected groups of constrained actions are enumerated exactly. For
the receipt/filing pair there are three allowed states. Unrelated actions retain
their independent conditionals. The collapsed hierarchy transition integrates
the allowed states, including the normalizer; a subsequent **joint** inventory
draw precedes updating detection. An optional augmented transition uses the
same normalized prior. This changes the scientific model's support, not just
its numerical implementation.

Marginal presence probabilities remain useful for individual predictions, but
their product is no longer a valid whole-episode probability. Joint episode
prediction must preserve aligned inventory draws, source parameters and the
single shared county identity. Existing unconstrained fits and their frozen
scoring code remain unchanged.

## Bounded experiment, declared before fitting

Reuse the adopted 20-action input: the original439 reading cells and174
administrative positive cells. Do not add the newly reviewed disposition
counts, change any label, or use the eight evaluation accounts in fitting.

Fit two constrained conditions, keeping administrative detection Beta(2,2)
and crossing administrative false-positive probabilities0.02 and0.10. All
other source assumptions match their already-completed unconstrained controls.
These are selected **development sensitivities**, not a fresh validation split
or calibrated source-error estimates. The additional Beta(9,1) administrative
conditions remain in the earlier experiment; no earlier result is replaced.

Each new condition uses four chains,2000 warmup iterations,6000 retained draws,
seed2026092108, collapsed hierarchy updates in blocks of four and independent
Beta detection. Freeze code, input bytes, declaration, settings and comparison
references before the first fit. No retry, longer run selected after a failure,
failed-gate waiver, or selected winning condition.

Report all terminal numerical gates, constraint violations, joint count
distributions, marginal variance contraction and sensitivity to the two source
error settings. Only numerically usable draws may be summarized. Check the
same eight already-scored accounts with their unchanged153 cells as a clearly
labeled **reused-account development comparison**. Preserve all outcomes,
including any loss to the pooled source/action baseline. Monte Carlo joint
episode scores use a different integration estimator from the earlier exact
cellwise integration; that distinction must be stated.

## What this cannot deliver

Enforcing a logical relationship can repair inventory support. It does not
identify actual case participation, branch frequencies, complete ordering,
per-operation elapsed time, active labor, fees or intrinsic agency capability.
Any decrease in incompatible mass is partly imposed by the assumption and is
not a recovery score. Unresolved routes still cannot be dropped, assigned zero
burden, or converted to executable V6 paths by this change.

The full end-to-end CalFresh goal remains unfinished until those bridge
requirements are resolved. Code tests and successful chain diagnostics do not
turn prior-determined quantities into learned burden posteriors.

## Locations

- Model: `pipeline/procbench/process_structure/occupancy.py` and
  `logical_support.py`; the option is off unless explicitly declared in data.
- Derivation review:
  `runs/process_structure_20260921/calfresh_phase2/structural_constraints_review.md`.
- Existing source adoption:
  `runs/process_structure_20260921/calfresh_phase1/admin_operational_adopted/`.
- New run, once authorized by root checks:
  `runs/process_structure_20260921/calfresh_phase2/logical_support_development/`.
- Overall status: [first-pass results](2026-09-21-process-structure-first-pass.md).
