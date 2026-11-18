# Causal frame for process models and drafting counterfactuals

Living design note, started 2026-09-26 after Alex asked whether the drafting
counterfactuals have a do-calculus interpretation. Short answer: yes. The
process model is a structural causal model (SCM), and a statute edit is an
intervention on it. Writing it this way does not change the toy code. It makes
the assumptions behind every counterfactual explicit and testable. Serves
`docs/CORE_GOAL.md` §3 ("the link back to drafting").

## 1. The SCM

Variables, for jurisdiction j and case i:

| node | meaning | toy parameterization |
|---|---|---|
| T (policy) | statute text; which clauses are concrete or vague | fixed text; the counterfactual edits it |
| C_j (context) | jurisdiction context: staffing, local rules, neighbour density, culture | not modelled in the toy (absorbed into a_j, p_j, q_j) |
| R_j (refinement) | how j implements each d-step, i.e. a structure from the menu | categorical over S1–S6, prior π |
| a_j (capacity) | agency speed | town speed factor |
| θ_k (step laws) | duration, hours and fee laws for p-step k | lognormal (μ_k, σ_k), fees |
| p_j, q_j | incompleteness and objection propensities | Bernoulli rates |
| K_i, H_i | the case path: correction loops, hearing | geometric, Bernoulli |
| D_ik | realized step durations, hours, fees | draws from θ_k scaled by a_j |
| E_i | event times (sums of D along the chain) | deterministic given R_j, K_i, H_i, D_i |
| Y_i | observations: admin records, reports, pages | noisy, rounded, censored functions of E_i and R_j |

Structural equations, schematically:

```
R_j := f_R(T, C_j, U_Rj)              # how the jurisdiction solidifies vague text
K_i, H_i := f_path(p_j, q_j, R_j, U_i)
D_ik := f_k(θ_k, a_j, U_ik)            # step laws, invariant across R
E_i := Σ_{k in chain(R_j, K_i, H_i)} D_ik
Y_i := f_obs(E_i, R_j, U_obs)
```

The Bayesian model as built equals this SCM, with f_R replaced by a prior
over R_j (the menu), because T is fixed in the data we see.

## 2. Drafting counterfactuals are interventions

"Rewrite §3 as 'the authority shall review the site plan'" changes T, so it
changes the mechanism f_R. The simplest formalization is do(R_j = S1) for
every j: graph surgery that deletes the arrow T → R_j and sets R_j. The toy
estimand `counterfactual.delta_days_mean` is

```
E[E_total | do(R_j = S1)] − E[E_total | R_j = r_j*]   (posterior-averaged over θ, a_j, p_j and r_j*)
```

which is rung 2 of Pearl's ladder: an interventional, population-average
quantity for the town. It is not a unit-level counterfactual ("how long would
*this* case have taken?"). That would need rung-3 abduction of each case's
U_ik, which the drafting question does not require.

A more faithful model of a statute edit is an intervention on f_R, not on R_j
directly. Concrete text constrains the menu but may not be fully complied with
(a town keeps an inspection anyway). That would be modelled as

```
do(T = T'):  R_j := f_R(T', C_j, U_Rj),  e.g. P(R_j = S1 | T') = compliance rate c
```

where the compliance rate is itself uncertain. It could be learned from
jurisdictions that already face concrete text.

## 3. Assumptions the counterfactual rests on

These hold by construction in the toy world. On real data each one must be
argued or tested.

1. **Modularity or invariance of step laws.** f_k(θ_k, a_j) does not change
   when R_j changes. A desk review in Birch takes as long after dropping
   inspections as before. It fails if freed capacity speeds up remaining steps,
   if workload shifts, or if staff are reassigned. Sensitivity version:
   multiply the durations of the remaining steps by (1 + δ) with δ in
   [−0.3, +0.1].
2. **No confounding of the refinement choice.** R_j is independent of the step
   laws given what we model. On real data this probably fails. Jurisdictions
   add hearings where neighbours are contentious, and the same contentiousness
   slows everything else. Then comparing towns with and without hearings
   mixes the procedure's effect with the town's effect. The SCM makes this
   visible as a back-door path R_j ← C_j → (a_j, D_ik). Adjustment needs
   observed context C_j or within-town variation (before/after changes).
3. **Transportability of step laws.** Birch has no separate decision step
   today, so its S1 counterfactual borrows decision_issue durations from
   other towns through "shared step law × town speed". In Pearl–Bareinboim
   terms that is a transport from source towns to Birch. It is licensed if
   town-specific differences enter only through a_j (a selection diagram with
   selection nodes pointing only at a_j). If Birch's decision step would
   differ for other reasons, the borrowing is biased. The hierarchical
   step×town deviation term (round-2 design option) softens this assumption:
   Birch's own deviation is unknown, and the uncertainty is propagated.
4. **Applicant behaviour invariance.** p_j, the incompleteness rate, does not
   change when the procedure changes. That may fail if a concrete statute also
   clarifies what a complete application is. A statute edit can intervene on
   more than one mechanism.
5. **Measurement invariance.** How people report does not change with the
   procedure. This matters only if post-change data are used.

## 4. What this buys us

- **Clarity about what is identified.** The structure posterior and the
  within-structure step laws are identified from observational data under the
  model. The counterfactual additionally needs assumptions 1–4. The report
  should always show the counterfactual *with* its assumption list and a
  sensitivity band, never alone.
- **A route to validation.** Real statute changes are natural experiments on
  f_R. California's residential-solar streamlining laws are the obvious case,
  as they make a vague procedure concrete: AB 2188 (2014) required expedited
  permitting, and SB 379 (2022) requires automated online permitting
  (SolarAPP+ or equivalent) by stated deadlines. The exact dates and scope
  must be checked before use. Before/after timing in the Solar corpus, by
  jurisdiction and adoption date, would let us:
  - estimate the compliance rate;
  - test invariance (did non-streamlined steps change after adoption?);
  - compare the model's predicted do(R = streamlined) effect with the observed
    change. That is an out-of-sample test of the drafting counterfactual
    itself.
- **Where LLMs fit causally.** An LLM prior over R_j is a prior over f_R
  (how jurisdictions solidify text). An LLM prior over θ_k is a prior over
  step laws. The cultural-transfer worry is precisely that these priors are
  context-dependent: effectively f_R(T, C_j) and θ_k(C_j). The robust-mixture
  priors plus conflict diagnostics in round 2 are a first guard. The
  principled fix is to model the C_j dependence (hierarchical by jurisdiction
  type) and let data dominate where available.

## 5. Next steps

- Add a sensitivity band on assumption 1 to the toy counterfactual estimand.
  This is cheap: recompute with the remaining-step durations scaled.
- Implement the compliance version of the intervention (P(R_j = S1 | T') = c,
  with a prior on c) as an option.
- For Solar: a before/after design around streamlining adoption. This needs
  per-jurisdiction adoption dates as a data task, not a modelling one.
