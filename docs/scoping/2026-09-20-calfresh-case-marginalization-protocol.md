# CalFresh case marginalization within V6

2026-09-20. Development protocol, fixed before the new real-data fits. Earlier
phone/interview fits and their numerical failures remain unchanged. This is an
inference change for the existing guarded conditional-case-frame contract, not
a new scientific architecture, new evidence selection, or source-bias model.

## Same target, fewer sampled coordinates

The current contract supplies one independent case per reported interval, one
aggregate operation, no paths/repeats, and zero agency/task/operation/source/common
effects. For each case, log duration is Normal(mu, sigma squared), and V6's
report error is Student-t(4), mixed with the existing broad Student-t(4) error
with scale2. Location and case-spread priors remain exactly those in each frozen
condition. Integrating the case durations and inactive independent priors leaves
two coordinates, or one when case spread is fixed. No case posterior is imputed
or presented as measured by this implementation.

Use the identity T4 = Z / sqrt(lambda), lambda ~ Gamma(shape2, rate2). Conditional
on lambda the case-plus-report log duration is Normal(mu, sigma squared +
report_scale squared/lambda). Integrate this interval/survival probability over
lambda separately for the regular and broad reporting mixture. This is an
alternative evaluation of the existing likelihood, not Gaussian report error.
Use deterministic Gauss-Legendre integration in log(lambda) over [-36,8],128
nodes initially and256 for refinement. The omitted Gamma mass is below1.1e-31;
quadrature error is separately measured, not bounded by this tail calculation.
Exploratory source-free checks rejected ordinary Gauss-Laguerre quadrature:
even256 nodes badly underestimated some Student-t tail probabilities. Log-scale
integration128/256 agreed much more closely with independent Gaussian-case
integration. Preserve that distinction rather than calling all quadrature exact.

## Scope and gates

- Reject inputs outside the existing conditional-frame contract; do not silently
  apply this independent-case reduction to repeated reports or a richer hierarchy.
- Test against adaptive integration of the existing V6 report kernel over a
  standard-normal case effect, including finite, upper and lower intervals,
  narrow reports, heavy tails, both contamination components and fixed spread.
- Keep the ordinary V6 runner/default target unchanged; explicitly opt into the
  marginalized path and record the integration settings and source snapshots.
- After code review, run all four full-scope phone conditions and all three
  full-scope interview conditions, cold, with their existing evidence, priors,
  seeds, four chains,1000 warmup and2000 retained draws per chain. No continuation
  and no best-condition selection. These are development comparisons, not new
  untouched validation data.
- Require the unchanged R-hat<=1.01, bulk ESS>=400 and tail ESS>=200 thresholds
  on every sampled coordinate, likelihood and reported location/spread/quantile.
  Also require the shared posterior-weight integration check on256 chain-spanning
  states, and independent adaptive reference checks on eight chain-spanning
  states. The latter must also agree within1e-5 in total log likelihood. This
  finite check is not a uniform numerical error certificate.
- Report exact lognormal conditional-frame median/p90 functionals, not finite
  population-QMC quantiles. Disclose this numerical reporting difference from
  predecessors; compare at matched saved parameters before interpreting changes.
- A numerical pass does not establish representative sampling, ignorable posting,
  accurate semantic mappings, a joint administrative/forum posterior, or intrinsic
  agency speed. Lower-bound-only inputs still cannot support a typical-time headline.

Implementation belongs in the existing V6 runner with a small marginal-likelihood
helper and shared diagnostics/provenance. General multistep/shared-case
marginalization and categorical actor inference remain separate unfinished work.
