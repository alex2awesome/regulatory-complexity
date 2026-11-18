# Detection partial-pooling development comparison

Date: 2026-09-21. This methods note is a bounded follow-up to the
[process-structure posterior plan](2026-09-21-process-structure-posterior-plan.md)
and the saved-draw
[staff-source loss diagnosis](../runs/process_structure_20260921/calfresh_phase3/source_loss_diagnosis.md).
It documents an opt-in source-detection prior and a fixed development
comparison on already-seen holdout folds. It is not a fresh validation study,
a latent-presence test, or a released result.

## Model

The default occupancy model retains independent detection probabilities

`p[s,k] ~ Beta(a[k], b[k])`

for step `s` and source type `k`. The opt-in model replaces that prior—not its
evidence likelihood—with a Gaussian logit hierarchy:

`logit(p[s,k]) = c[k] + mu[k] + delta[s,k]`,

where

`c[k] = log(a[k] / b[k])`,

`mu[k] ~ Normal(0, sigma_type^2)`, and

`delta[s,k] ~ Normal(0, sigma_step^2)` independently across steps and source
types. The existing Beta shapes supply only the center `c[k]`; this is not a
Beta reparameterization, no Beta Jacobian is used, and the Gaussian-logit prior
must not be described as the same prior family.

The source-type effect is integrated in the prior. For the `S`-vector of logits
for one source type,

`eta[k] ~ Normal(c[k] 1, sigma_type^2 11' + sigma_step^2 I)`.

The implementation forms the exact Cholesky factor `L` of this covariance and
sets `eta[k] = c[k] 1 + L w[k]`, with `w[k] ~ Normal(0,I_S)`. Thus each source
type has exactly `S` standard-normal detection coordinates, saved separately
as `detection_white`; the existing occupancy `hierarchy_white` layout and
meaning do not change.

For reporting only, the integrated type effect has the analytic conditional
moments

`E[mu[k] | eta[k]] = sigma_type^2 / (sigma_step^2 + S sigma_type^2)
                     * sum_s (eta[s,k] - c[k])`

and

`Var(mu[k] | eta[k]) = 1 / (sigma_type^-2 + S sigma_step^-2)`.

These moments are reported without adding an arbitrary sampled `mu` coordinate.
Posterior variance uses the law of total variance; full-mixture quantiles are
not claimed from conditional-mean draws.

## Transition and likelihood

Conditional on current latent presence indicators `z`, the sufficient counts
for detection are the reviewed positive and negative readings in cells where
`z=1`. For each source type the exact log likelihood is

`sum_s n1[s,k] log(sigmoid(eta[s,k]))
       + n0[s,k] log(sigmoid(-eta[s,k]))`.

It is evaluated with stable log-sigmoid arithmetic. A step with no reviewed
reading opportunity contributes exactly zero; it is not turned into a
nondetection. One elliptical-slice update moves the complete `S`-coordinate
block for each source type under its standard-normal white prior. No clipping,
jitter, learned scale, or trust ranking is introduced.

The partially collapsed sweep order remains:

1. update the occupancy hierarchy conditional on the current detection state,
   integrating unanchored `z` where the existing collapsed transition does so;
2. draw fresh `z` conditional on the updated occupancy hierarchy and current
   detection state;
3. update each source-type detection white block conditional on that fresh `z`;
4. draw the shared uncertain-jurisdiction assignment conditional on the fresh
   `z` and updated detection probabilities; and
5. recompute saved conditional-presence and assignment probabilities at the
   resulting joint state.

The augmented occupancy transition remains available and retains its existing
placement; the development comparison uses the collapsed transition. Detection
probabilities keep the public `S x K` output shape. Detection probabilities,
white coordinates, analytic conditional type-effect means, presence
probabilities, and identity assignments all retain numerical diagnostics.

The default `independent_beta` branch has exact seeded draw and result replay
against the archived pre-extension sampler. It allocates no detection-white
coordinates and exposes no inactive hierarchy output. The opt-in detector also
does not add or alter V6 repeat-count, case, duration, route, labor, fee, or
burden coordinates. In particular, it has no effect on the separate
completed-positive repeat-count component except through a future explicitly
reviewed joint model, which is not part of this comparison.

## Frozen development comparison

The fixed comparison launched at 10:37 UTC under
[`calfresh_phase3/detection_pooling_development`](../runs/process_structure_20260921/calfresh_phase3/detection_pooling_development/).
Its plan was frozen before aggregate comparison:

- the same ten already-seen county holdout folds used in the completed mixed
  source-prediction experiment;
- two conditions only: `sigma_step=0.5` (stronger pooling) and
  `sigma_step=1.5` (weaker pooling);
- `sigma_type=1.5` in both conditions;
- four chains, 2,000 warmup iterations and 6,000 retained draws per chain;
- seed `2026092105`, collapsed occupancy transition, and hierarchy block size 4;
- unchanged evidence, fixed 15-step vocabulary, false-positive probabilities,
  county candidates, held-out units, and baseline algorithm; and
- all 20 condition-by-fold jobs retained, with no winner selection, numerical
  retry, failed-gate waiver, or outcome-driven prior change.

This is model development against folds whose outcomes have already been
examined. It cannot be labeled external, prospective, or fresh validation. The
comparison may test whether the proposed source model improves prediction of
held-out *mentions* under the same frame; it cannot validate latent process
presence.

At this documentation checkpoint, six of the 20 jobs had completed. Four
stronger-pooling folds passed the numerical gate; Orange and Riverside failed
it on saved detection-white diagnostics. Those failures are retained. The
remaining jobs were still in progress, so there is no aggregate success claim,
scientific condition ranking, or result reported here.

## Identification limits

Partial pooling addresses a concrete opportunity imbalance: after a staff
source is held out, an individual step has only one remaining staff-policy
reading, while a staff document supplies readings across the full step list.
Sharing a source-type intercept lets those cross-step readings inform the
detection distribution without forcing every step to have identical detection.

It does not identify whether a nondetection means action absence, source
omission, nonparticipation in the observed episode, observation before the
action, or vocabulary mismatch. A better source-mention score would not prove
that `p` is calibrated or that latent county actions were recovered. Step-level
pooling can also be wrong when source coverage is genuinely action-specific;
that is why both fixed scales are reported rather than choosing the better
looking condition.

Known statewide legal functions are not automatically latent-presence anchors
for county implementation. They require separate jurisdiction, era,
applicability, and estimand review and must not be reused as both a detection
reading and a truth anchor. The experiment contains no new legal-function
anchors and makes no intrinsic agency-capability, complete-process, or total
burden claim.
