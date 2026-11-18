# CalFresh joint timelines: marginalize nuisance variables, retain the model

Status: the four-coordinate fit **started at 05:57:48 UTC on 2026-09-21**;
there is no new completed fitted result yet. The
[frozen execution plan](../runs/three_family_20260920/calfresh_joint47_collapsed_runner_v1/plan.json)
runs all three original path-prior conditions, four chains per condition,
2500 warmup and 6000 retained draws per chain. This is a new inference attempt,
not an equal-budget sampler comparison. All 47 source/input bindings stay frozen
through sampling and analysis; no automatic extensions are planned. All three
equal-budget sampler-repair conditions failed convergence; their fixed post-fit
comparison is complete. Their failure must not be hidden by this work or used
to select a more favorable scientific prior.

The intended change is a different computation of the **existing** posterior,
not another process architecture. It preserves all 47 histories, the three
operation clocks, fixed path-prior sensitivities, censoring, shared reporting
errors, report contamination and original hierarchy prior.

## What can be integrated without deleting the hierarchy

Write the original whitened hierarchy as xi ~ Normal(0,I), and the three
operation log locations as mu = mu0 + A xi. The exact induced prior is

    mu ~ Normal(mu0, K),                 K = A A'.

For this fixed real-data experiment K = 4 * 11' + 2.25 * I: the shared location
scale is 2 and each of the three distinct task scales is 1.5. The operation
means must **not** receive three independent replacement priors. A Cholesky
parameterization of K needs three standard-normal coordinates. The original
log case-spread prior needs one more, for four coordinates after integrating
case effects and inactive directions, rather than 200 sampled coordinates.

Integration is not setting every case residual to zero. Nor does it prevent
later recovery of hierarchy uncertainty. Given eta = mu-mu0, the original
hierarchy has the exact conditional distribution

    xi | eta ~ Normal(A' K^-1 eta, I - A' K^-1 A).

Draws from this conditional restore the original hierarchy's unresolved
directions. In this experiment agency effects have scale zero; no method can
turn that into a learned intrinsic agency delay. More generally, integrating
Gaussian hierarchy directions preserves their posterior, but does not make a
confounded agency/task design identifiable.

## The case likelihood remains joint

For case i and allowed path p, let z be its independent standard-normal
operation-duration residuals and D_p(mu,sigma,z) its duration vector. Let G_ip
be the independent reporting-error groups, not the individual sentences. Then

    L_i(mu,sigma) = sum_p pi_ip * integral phi(z)
                     * product_{g in G_ip} L_g(D_p(mu,sigma,z)) dz.

The fixed case-specific path prior pi_ip is applied **once per case**, after
group multiplication and integration. A shared group gets one Student-t4 error
and one contamination indicator. Multiplying separately integrated factors that
share case residuals would change the model. An explicitly absent pending event
contributes one on that path; it is not a completed event of duration zero.

The [source-only inventory](../runs/three_family_20260920/calfresh_joint47_marginalization_inventory_v1/README.md)
finds 49 groups from 61 observation facets: seven shared groups consume 19
facets, and 42 singleton groups remain. Nineteen cases have one allowed path and
one group; 26 additionally need path/absent-event composition; two have multiple
groups. Across 74 allowed case-path combinations, 63 have one active group,
nine are structurally neutral, and two have two groups.

The two multi-group cases have different dependence:

- `captainfairenough`: separate A and B reporting groups. Their integrals can
  factor because the case residuals are independent conditional on mu and sigma.
- `16y6dan_root`: separate A and T=A+B reporting groups. They share A, so the
  product must be integrated jointly. On the direct path the absent interview
  report is neutral and the total report remains informative.

## One shared group: rotate and integrate

For a two-phase path, write independent residuals as

    g=(z_A+z_B)/sqrt(2),  h=(z_A-z_B)/sqrt(2),
    A=exp(mu_A+sigma*h/sqrt(2)) * exp(sigma*g/sqrt(2)),
    B=exp(mu_B-sigma*h/sqrt(2)) * exp(sigma*g/sqrt(2)).

A, B and their sum have the same g multiplier. With one shared log reporting
error e, all report intervals constrain q=sigma*g/sqrt(2)+e. Student-t4 error
is a normal/gamma mixture. Conditional on the gamma precision, q is Gaussian,
so its admissible interval has an analytic normal-CDF probability. Only h and
the precision integral remain. The narrow and broad contamination components
are combined once after their probabilities are evaluated.

The first prototype's finite h-grid could miss an entire thin support interval.
The [root exact-support helper](../runs/three_family_20260920/calfresh_joint_ratio_support_v1/README.md)
replaces this search algebraically. A common reporting-error interval exists
iff q_i/q_j > L_i/U_j for all positive lower and finite upper bounds. All ratios
among A, B and T are monotone in d=log(A/B) or constant, so these inequalities
intersect to **one interval**, not disconnected support. The helper also
computes changes of active lower/upper envelopes.

Eight source-free tests pass, including 12,000 randomized membership comparisons
and a feasible interval missed by all 4,801 points of the old grid. This checks
support, **not full marginal-likelihood accuracy or posterior convergence**.

## Remaining acceptance work

The [guarded bridge](../runs/three_family_20260920/calfresh_joint47_marginal_bridge_v2/README.md)
now preserves the correlated prior and rejects unsupported richer inputs.
The [all-case marginal evaluator](../runs/three_family_20260920/calfresh_joint47_marginal_evaluator_v1/README.md)
composes all 47 cases, 49 report groups and 74 allowed case-path pairs. At four
modest, prior-defined probes, refinement from order 192 to 256 changes the total
log likelihood by at most 2.60e-12; the scalar and vectorized providers agree at
equal order. These checks read no posterior and run no new fit.

At that stage this was not sufficient for a sampler: the probes were close to the prior
origin, and a full likelihood evaluation takes roughly 1.5 seconds. Broader
prior stress tests found the singleton A/T Gaussian rule needed refinement.
An independent adaptive integral of the original kernels now agrees with
Gaussian order 768 to 1.07e-8 in the factor and 7.98e-9 in its whole-target
contribution on three checked states. This is not an all-state certificate.
Independent composition review passed, while requiring a strict numerical
guard before sampling. Measured performance optimization remains in progress.
The extended [high-spread reference](../runs/three_family_20260920/calfresh_joint47_singleton_at_adaptive_reference_spread_v1/README.md)
checks four states with case spread 3.63–4.43. Those states extend beyond the
earlier grid: failed full-dimensional chains visited spreads up to 3.56, which
is a computational-domain warning, not a trustworthy posterior conclusion.
At these four probes, Gaussian orders 768/1024/1536 have maximum factor errors
6.04e-4/1.82e-4/1.70e-6 against the adaptive reference. Only 1536 passes that
packet's local 1e-5 comparison, and it costs about 1.55 seconds for this case
alone. Thus the earlier 768-order result must not be generalized to this range.
Refining numerical integration preserves the target; these checks are not a
license to narrow the prior or turn numerical failures into rejected proposals.

An isolated [adaptive random-walk Metropolis candidate](../runs/three_family_20260920/adaptive_random_walk_metropolis_prototype_v1/README.md)
uses one target evaluation per proposal. It adapts covariance and scale only
during warmup and freezes a symmetric proposal for retained draws. Root read
the implementation and reran its four focused tests (all pass). The worker's
correlated-Gaussian fixture passes diagnostics, but this is neither a CalFresh
fit nor evidence that this sampler solves the joint posterior. The subsequent
real run is now executing under the separate frozen plan linked above.

The final [combined backend](../runs/three_family_20260920/calfresh_joint47_marginal_evaluator_perf_v8/README.md)
uses direct-h shared-group integration, vectorized total-only integration, and
composite A/T integration. Direct-h integration replaces the failed Gaussian-CDF
segment approximation; the latter's failures remain preserved. Whole-likelihood
evaluation costs 0.179–0.185 seconds on the measured fixtures. Its 18 final
base/refinement probes differ by at most 7.50e-8 in log likelihood. Truncated
Gaussian tail effects are bounded separately; empirical quadrature refinement
is not called a uniform theorem. The live runner also checks 64 retained states
plus coordinate extremes after sampling and preserves the original R-hat/ESS
gate. More retained draws than the old fit are declared explicitly, so this is
not an equal-budget speed or mixing comparison.

The evaluator also bounds the difference between the mathematical
Gaussian integral and production's +/-650 log-duration guard / 1e-300 interval
floor. A missing or excessive numerical bound must stop computation, not become
a statistical rejection. Quadrature refinement is empirical, not a uniform
error certificate. No real collapsed fit is authorized by this methods note.

The reviewed execution protocol retains the same scientific target and all
three sensitivity conditions. A numerically
usable fit would still require source-selection, adequacy and predictive
checks before any population-burden claim. Current forum-use accounting remains
100 linked threads, 118 component records and 167 open uses; these are different
denominators and this numerical work closes none of them.
