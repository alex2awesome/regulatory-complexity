# CalFresh: same-target case marginalization results

2026-09-20. All seven prespecified successor fits pass unchanged numerical gates.
The earlier expanded fits passed only three of seven. Their four failures remain
in their original directories; no threshold, observation, prior or failed result
was edited. This resolves an inference bottleneck for two conditional report
components, not the complete CalFresh study or source-selection problem.

## What changed

Under the existing narrow conditional-frame contract, each case has one reported
interval or lower bound, one phase, and independent Gaussian log-duration noise.
The optional V6 runner path integrates those case effects and inactive independent
priors instead of sampling them. The Student-t(4) report likelihood, contamination
mixture, location/spread priors and case intervals are unchanged. The retained
posterior has two coordinates instead of68 for mixed phone and62 for interview.

The [fixed protocol](scoping/2026-09-20-calfresh-case-marginalization-protocol.md)
and [marginal helper](../pipeline/procbench/marginal_conditional_frames.py) implement
`run_visit_hierarchy --marginalize-conditional-cases`. This is not a new process
model. Repeated reports, multistep routes, nonzero source/hierarchy effects and
richer dependencies remain on the ordinary V6 path. This helper rejects them,
not their evidence from the study. Individual case posteriors are not reconstructed.

The [independent code review](../runs/three_family_20260920/calfresh_case_marginalization_independent_review_v1/README.md)
passed after repairs to extreme-state handling, fixed-spread diagnostics and
provenance checks. Root's [pre-fit checks](../runs/three_family_20260920/calfresh_case_marginalization_v1/root_pre_fit_checks.json)
record50 focused and249 adjacent tests, plus126 unchanged likelihood-dependency
hash comparisons across the older fits. No new full-suite result is claimed.

## Actual fits

Four chains,1000 warmup and2000 retained draws per chain, with each condition's
original seed and scientific settings. All were cold fits; no continuation or
best-condition selection. These are development data, not held-out validation.

| Report frame | Cases | Median,90% posterior interval | Fit seconds | Gate |
|---|---:|---:|---:|---|
| Phone, completed exits | 25 | 127.85minutes (95.64–171.29) | 16.9 | PASS |
| Phone, completed plus pending | 31 | 146.93minutes (113.75–191.14) | 20.7 | PASS |
| Phone, same31,wider report noise | 31 | 147.76minutes (111.20–199.07) | 19.9 | PASS |
| Phone, same31,prior median15minutes | 31 | 145.57minutes (112.07–191.36) | 21.7 | PASS |
| Interview, completed encounters | 18 | 4.69calendar days (2.63–7.53) | 12.7 | PASS |
| Interview, completed plus pending | 28 | 9.12calendar days (5.58–14.65) | 18.6 | PASS |
| Interview, same28,wider report noise | 28 | 9.17calendar days (5.69–14.88) | 17.7 | PASS |

Times are fit-manifest wall times, including saved checks, excluding small
launcher/import overhead. They are measurements, not general runtime promises.
[Phone results and actual factors](../runs/three_family_20260920/calfresh_case_marginalization_v1/phone/analysis_v1/README.md)
and [interview results and actual factors](../runs/three_family_20260920/calfresh_case_marginalization_v1/interview/analysis_v1/README.md)
retain every condition. These are the same31/28 cases as their predecessors,
not new cases. One claimant contributes to both components; do not sum their
counts or clocks into independent people or total burden.

All sampled coordinates, log likelihood and reported location/spread/quantiles
pass R-hat<=1.01, bulk ESS>=400 and tail ESS>=200. Across the seven fits, the
smallest bulk ESS is1684 and largest R-hat is1.00184. Refining128 to256 quadrature
nodes on256 chain-spanning states per fit gives maximum absolute total
log-likelihood changes below2e-8 and passes the existing posterior-weight check.
Eight independent adaptive Gaussian-case integrals per fit agree within2e-8.
These finite checks are not uniform numerical proofs or model-adequacy checks.
The independent review covered code mechanics; root compiled and checked these
real results, without a new independent source audit.

Predictions use analytic lognormal quantiles, rather than finite-QMC quantiles.
At eight matched older states per component, the largest relative median/p90
difference was0.568% for phone and0.883% for interview. This reporting change is
declared; old reports are not silently recomputed.

## Interpretation and remaining work

Comparable central estimates became numerically usable without changing the
scientific prior or discarding cases. Integrating nuisance case effects resolved
the scale/case mixing problem here. This demonstrates a numerical remedy, not
superiority over an LLM or calibration of the assumed reporting-error scale.

Phone time ends at answer, abandonment or disconnection, not necessarily
successful contact. Interview time is not approval or benefits available.
Including pending histories changes the selected frame; it is not a learned
posting-selection correction. Ignorable coarsening remains an assumption.
Named departments are not required, but general categorical actor uncertainty
remains unfinished. The administrative fit, conditional forum components and
descriptive structural/count analyses are not yet one joint burden posterior.

Remaining work includes other supported clocks, structural demands, justified
source heterogeneity/identity treatment, model adequacy and matched comparisons.
Solar, CCW and synthetic construction remain deferred under CalFresh-first.
