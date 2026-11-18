# Scaling the toy-statute inference to real-world structure: recommendations (for Codex review)

2026-09-30. Drafted by Claude at Alex's request; Codex to review, accept, reject or reorder. Nothing here is
implemented. Builds on the speed audit (`2026-09-30-audit-response-and-inference-speed-audit.md`) and the v2
repairs (`2026-09-30-toy-statute-audit-repairs.md`), which already delivered ~2.5–3.4x per likelihood.

## The scaling problem

Wall time ≈ runs × tempering stages × particles × moves × (one full likelihood evaluation) / workers.

| Driver | Toy now | Real statute (e.g. Solar) | Effect |
|---|---|---|---|
| Jurisdictions T | 3–14 | ~500 AHJs | evaluation cost ∝ T; parameters ∝ T; random-walk moves needed grow with dimension |
| Designs D per jurisdiction | 6–12, flat menu | combinatorial in optional steps and orderings | evaluation cost ∝ D |
| Records N | ~125–400 | 10^3–10^4, very unequal per AHJ | cost ∝ N; more records -> more tempering stages |
| Steps / grid | ~8 steps, 512-day grid | 10–20 steps | convolution work per design |

Today every move of every particle re-evaluates every town under every design. A naive extrapolation from
W4 (12 towns, ~100 ms per v2 evaluation) to 500 towns is on the order of hundreds of days per fit.
The recommendations below remove that multiplicative structure without changing the posterior target.
Each item is labelled **exact** (same target, same numbers up to floating point), **same target**
(different Monte Carlo kernel), or **approximate** (changes the target; only with explicit declaration).

## A. Use the conditional independence of towns (highest payoff)

1. **Per-town likelihood cache (exact).** loglik = Σ_t ℓ_t(θ_shared, φ_t), where φ_t are town parameters.
   Store ℓ_t per particle; after any move re-evaluate only towns whose inputs changed.
2. **Blocked moves (same target).** Alternate (a) shared-block moves (step laws, report noise, contamination)
   and (b) town-block moves on φ_t. A town-block move costs one town's evaluation, so a sweep over all towns
   costs about one full evaluation instead of T. The centered town-speed parameterization couples towns;
   use orthonormal contrasts or non-centered hierarchical speeds so a town move is truly local
   (speed audit §4.3).
3. **Towns without data (exact).** A town with no records contributes a constant; do not evaluate it.
   Its posterior is the (hierarchical) prior. Real corpora have long tails of AHJs with zero or one record.
4. **Parallelize over towns within an evaluation** for shared-block moves, not only over particles.

## B. Better moves and fewer particles (same target)

5. **Gradient-based moves.** After exact summation over designs and paths the marginal likelihood is a smooth
   function of θ (discretized lognormal CDFs and convolutions). Port the likelihood to JAX: autodiff gives
   gradients for HMC/MALA moves inside SMC (or NUTS for the final tempering stage), and `vmap` batches
   particles. Random-walk move counts grow roughly linearly with dimension; gradient moves much more slowly.
6. **Particle count and move budget.** 10,000 particles × 30 moves was a precision experiment. Use ~2,000
   particles, adaptive moves (stop when a mixing statistic stabilizes), and waste-free SMC. Report Monte
   Carlo error from independent runs rather than buying it with particles.
7. **Hierarchy updates.** With φ_t drawn from a population, update hyperparameters given φ by
   Gibbs-within-SMC (conditionally conjugate where the prior allows) instead of joint random walk.

## C. Keep the design sum tractable (exact unless stated)

8. **Share structure across designs.** Designs are sets/orders of steps. Extend the cached convolution
   (count-vector prefixes, `grid.sum_pmfs`) across designs and across towns with the same speed-scaled steps,
   so shared sub-paths are computed once.
9. **Factorize the design likelihood.** A record constrains only the steps between its two bounding events.
   Group designs by the step multiset each record spans; evaluate each distinct span once per town and
   reuse it for every design with that span. This turns D × records into (distinct spans) × records.
10. **Factorized design priors for combinatorial menus.** Represent a design as inclusion/order features
    and sum by dynamic programming over features where the likelihood factorizes (9 makes this possible),
    instead of enumerating a flat menu.
11. **Bounded pruning (approximate, declared).** Skip designs whose likelihood upper bound falls more than
    a declared margin (e.g. 30 nats) below a town's best design; report the dropped mass bound.

## D. Compress the data (exact)

12. **Sufficient statistics.** Collapse records with identical (event pair, reported value, unit, source
    type) into counts. Real reports are heavily rounded (days, weeks, months), so the number of distinct
    likelihood terms is far below N.
13. **Admin data as histograms.** Aggregated administrative clocks enter as multinomial histograms
    (as V6 already does), not per-case records.

## E. Stage C and the hypothesis-space experiment

14. Stage C cost ∝ particles × towns × readings (× hypotheses K). Keep Codex's reading-class collapse,
    reuse one particle subsample for all hypotheses, and cache per-particle town-design likelihoods from
    Stage B (write them at the end of the fit so Stage C never recomputes them). For finite κ with hundreds
    of towns, the exact count-state expansion is infeasible; keep grouped Monte Carlo with reported error.

## F. Engineering and proof

15. **Vectorize across particles** (batched convolutions/FFTs, numba or JAX) instead of per-particle Python
    calls; the profile shows most time in per-call overhead and convolution.
16. **Scaling benchmark before any real fit.** Generate synthetic worlds at T = 12, 50, 200, 500 with a
    realistic long tail of records per town; measure time per evaluation, per sweep and per effective
    sample. Predeclare: every exact change must match the reference log likelihood to 1e-10 on fixed points;
    every kernel change is compared on Monte Carlo error per CPU-hour and interval stability, not speed alone.
17. **Order of work (suggested):** A1–A3, D12, E14 (exact, cheap) → A2 blocked moves → benchmark (16) →
    B5 JAX + gradient moves → C8–C10 for combinatorial menus. Approximate items (C11) only if the benchmark
    shows they are needed, and never silently.

## What not to do

Shrink priors, drop rare designs, replace sums by MAP choices, cut particles without measuring Monte Carlo
error, or fit towns fully independently and call it the joint posterior. These change the target.
