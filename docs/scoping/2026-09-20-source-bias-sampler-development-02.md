# Source-bias sampler development, round 2

Declared after the first clean fixture's blocked-kernel fits, before any
interwoven fit. This is an explicitly outcome-informed **numerical development
round**, not an unseen recovery test or an amendment that erases a failure.
The [original protocol](2026-09-20-source-bias-mechanics-protocol.md), its six
frozen inputs and every saved blocked-kernel fit remain unchanged.

The clean seed 73101 legacy fit passed the existing numerical gate after its
single allowed extension to 6,000 draws per chain. The source hierarchy still
failed: coordinate 27 had R-hat 1.0150 and bulk ESS 358.6; coordinate 34 had
R-hat 1.0101. Both integration checks passed. More draws beyond that declared
extension are not an unreported rescue. No recovery scores are released from
the unconverged hierarchy fit.

## Change under test

Keep the statistical target, exact likelihood, observations, source memberships,
priors, integration settings and random seeds fixed. Add an opt-in
`source_hierarchy_sampler=interwoven` mode; `blocked` remains the default.
The optional mode may split the source coordinates into prior-correct ESS
blocks, and adds two fixed-effect scale moves per sweep: one for the type
spread and one for the shared document spread (when allocated). Each uses a
fixed symmetric normal increment with standard deviation 0.5; no tuning from
posterior outcomes. Other operation-centered updates remain unchanged.

For a whitened scale coordinate x, log-scale prior width s, and K governed
standardized effect coordinates v, propose x' = x + epsilon and
v' = exp(-s epsilon) v. Include the full normal-prior change, the evaluated
likelihood difference, and log Jacobian **-K s epsilon**. For document effects,
K is the total number of Helmert contrasts, not the number of documents.
All governed document groups move together. Reject nonfinite proposals without
clipping or mutating the saved state. The independent derivation is preserved
in `runs/three_family_20260920/source_sampler_review_v1/`.

Before fitting, require source-free tests of inverse moves, Jacobian sign and
dimension, actual-effect and likelihood invariance, analytic zero-effect
conditionals, prior stationarity, and numerical rejection. Absent a source
hierarchy, the new mechanism must leave the historical RNG path unchanged.
Also add direct convergence diagnostics for the transformed source effects,
spreads, centered document residuals and effective document offsets; whitened
coordinate diagnostics alone do not certify these reported quantities.

## Fixed execution and interpretation

Start with the same clean seed 73101 hierarchy input and the original settings:
four chains, 1,000 warmup, 2,000 retained draws, seed 2026092001. Preserve it in a
new run directory. If needed, allow exactly one extension to 6,000 total
retained draws with continuation seed 2026392001. Apply the unchanged R-hat
1.01, bulk ESS 400 and tail ESS 200 gates, including transformed quantities.
Record likelihood calls, elapsed time, retained draws and every failed gate.

If this first numerical gate passes, apply the same frozen sampler/settings
to the other five hierarchy fixtures and run the remaining legacy controls.
Each retains the same one-extension limit. Do not skip failed seeds or score
only favorable ones. Report the full original six-fixture recovery table and
its original criteria, distinguishing the sampler-development fixture from the
remaining replications. The original blocked failure remains a result.

If it fails again, retain the failure and diagnose the geometry explicitly;
do not loosen convergence gates, change the target, or relabel it a lack of
documents. No real-corpus fit, synthetic-document pipeline success, empirical
source-trust learning or transportability claim follows from this exercise.
