# Process validity under a decision model

Living design note. It started from Alex's question on 2026-09-28: "do we have a sense for whether a process model is VALID under a decision model?"

- Code: `pipeline/procbench/toy_statute/validity.py` (truth-blind) and `design_optimum.py`.
- Tests: `tests/test_toy_statute.py` (the validity tests are included in its 20 passing tests).
- Toy outputs: `runs/toy_statute_20260926/validity001.json` and `runs/toy_statute_20260926/W0/design_optimum_tau*.json`.

## Three things that are easy to conflate

| | Question | Unit | Evidence |
|---|---|---|---|
| **Validity** | Does the process, as designed, satisfy what the statute requires? | Design × reading of the statute | Statute text and interpretive sources |
| **Compliance** | How often does the town actually do what the design and the statute require? | Cases | Admin records, applicant reports |
| **Optimality** | Among valid designs, which costs least in burden and externalities? | Design × jurisdiction | Burden posterior plus outcome data |

Observed processes are presumptively valid, not guaranteed valid. Contestation is rare and costly, so a legally weak practice can persist. Validity is also not compliance. In the toy's common-sense world W0, all three towns run plausibly valid designs, yet the truth deadline-miss rates are:
- Alder: 3%;
- Birch: 48%;
- Cedar: 55%.

## Constraints a decision model places on a process

A process design is a DAG of p-steps. Each step records:
- the d-steps it serves;
- which steps must finish before it;
- any waiting period the design itself mandates (its floor);
- whether it is conditional (e.g. a hearing only on objection);
- whether it contributes to a determination.

A design also lists the burdens it places on the applicant (documents, attendance, fees) and the grounds on which it may deny.

| Constraint | Checks | Source in the toy statute |
|---|---|---|
| C1 coverage | Every d-step is served by some p-step. | The decision model |
| C2 sufficiency | The evidence gathered before the decision is enough for the determination. | Sec. 3 (vague) |
| C3 precedence | Every determining step finishes before the permit issues. | Sec. 3 ("before issuing") |
| C4 deadline feasibility | The design's own mandated waits fit inside the clock. The check is best case: agency work takes zero time. | Sec. 4 |
| C5 authority | Every applicant burden traces to an authorizing clause; no phantom requirements. | Secs. 2, 3, 5 |
| C6 grounds | Denial rests only on authorized grounds. | Secs. 1, 3, 4 |

C4 is a *design* check: a design is infeasible by construction if its mandated waits alone exceed the clock. Whether a town meets the deadline in practice is compliance, measured by the estimand `deadline.p_miss`.

## Vague text means validity is uncertain: readings

Each vague clause raises interpretive questions. A **reading** is one answer to each question. Validity is computed per reading. This makes Alex's sub-question (a) concrete: *the same statute admits multiple decision models*, one per reading.

| Question | Clause | Illustrative P(yes) |
|---|---|---|
| Q1: can a desk review of the site plan alone support the nuisance determination? | Sec. 3 | 0.7 |
| Q2: must adjoining owners get notice and a chance to comment? | Sec. 3, "to adjoining properties" | 0.3 |
| Q3: may the town require the applicant's attendance or site access for an inspection? | Sec. 3, implied power | 0.9 |
| Q4: does the 30-day clock run through the determination? | Sec. 4 | 0.8 |
| Q5: does "a reasonable application fee" allow separate notice or inspection fees? | Sec. 5 | 0.5 |

**The probabilities are illustrative placeholders, not estimates.** Every result below at τ = 1 ("valid under every reading") uses none of them. Candidate sources for real reading probabilities:
- case law;
- attorney-general opinions;
- agency guidance;
- calibrated legal readers, with the same calibration concerns as any LLM measurement.

Observed town practice is evidence about which readings *agencies* hold, not about which reading a court would adopt.

Declared design assumptions:
- A comment period lasts 14 days (the H3 variant uses 30).
- A hearing needs 10 days' notice.
- Attending a neighbour hearing is voluntary. It still costs hours, but it is not a compelled burden.
- Fee schedules are a town choice, separate from the structure.

## Toy results

### 1. Validity of the menu and of designs outside it

| Design | P(valid) | Depends on |
|---|---|---|
| S1 desk review only | 0.49 | Q1, Q2 |
| S2 / S3 desk + inspection | 0.63 | Q2, Q3 |
| S4 notice + comment + desk + hearing on objection | **1.00** | none |
| S5 / S6 (S4 + inspection) | 0.90 | Q3 |
| S2c–S6c: same D2 steps run concurrently | Same as serial | — |
| H7: neighbours notified at submission | 1.00 | none |
| H3: 30-day local comment period | 0.20 | Q4 (infeasible whenever a neighbour objects) |
| H5: inspection only, decided on the spot | 0.63 | Q2, Q3 |
| H8: S3 plus a separate inspection fee | 0.315 | Q2, Q3, Q5 |
| H2: applicant must collect neighbour signatures | 0 | C5: phantom requirement |
| H4: permit issued, inspection afterwards | 0 | C3: determination after issuance |
| H6: may deny an "unsightly" coop | 0 | C6: unauthorized ground |

**Concurrency never changes validity** (this is tested). The statute orders the determination before issuance, not the determination's parts among themselves. So the concurrency lever is available to towns *now*, with no statute change.

**Validity of the actual W0 practices:**
- Alder (S1): 0.49, depending on Q1 and Q2.
- Birch (S3 plus an inspection fee): 0.315.
- Cedar (S4 plus a notice fee): 0.5, depending only on Q5.

Separate fees are a recurring exposure.

### 2. Defensive proceduralism

A notice-and-hearing design (S4, or its concurrent version) is the only menu option that is valid under every reading. If a town wants legal safety (τ = 1), vagueness pushes it toward notice-and-hearing procedures. This is one concrete mechanism by which vague text creates burden: it is the *cost of vagueness* expressed through legal risk rather than implementation variety.

### 3. Optimal valid design, before and after statute edits

The next table uses W0 and ranks designs by the round-2 posterior median of expected total days. Truth values are shown for evaluation only.

**Admissible designs:** those valid under every reading the edit leaves open (τ = 1). This uses no reading probabilities.

| Scenario | Alder | Birch | Cedar |
|---|---|---|---|
| Current text | S4c: 29.5 d [23.7, 45.6], truth 33.0 | S4c: 43.5 d [27.8, 64.5], truth 40.3 | S4c: 38.0 d [33.4, 44.4], truth 37.4 |
| E1 safe harbour | **S1: 24.0 d** [21.9, 26.8], truth 23.1 | **S1: 36.1 d** [19.9, 52.9], truth 30.8 | **S1: 30.7 d** [21.4, 39.3], truth 26.3 |
| E5 investigation power | S6c: 28.7 d, truth 29.3 | S6c: 41.2 d, truth 36.2 | S6c: 35.2 d, truth 33.8 |
| E2, E3, E4 | Unchanged from current text (S4c) | Unchanged | Unchanged |

The E1 safe harbour reads: "a coop ≥ 10 ft from every property line is deemed not a nuisance". It makes the cheapest design safe:
- It saves 5.5–7.4 posterior-median days per application (truth: 9.5–11.1 days).
- It also removes the hearing hours.

E2 (a notice requirement) confirms S4-type designs, which are already the safe choice, so the optimum does not change. It does, however, make every desk-only design invalid.

At τ = 0.9 the optimum moves to S6c. At τ = 0.6 it moves to S3c. Those τ < 1 results depend on the illustrative reading prior.

Guiding point 2 in `CORE_GOAL.md` appears here as a two-level problem:
- the drafter picks the text, which fixes the set of valid designs;
- each town picks a design from that set, with some appetite for legal risk (τ);
- burden follows from the design.

The toy gives the smallest working instance.

## Limits and next steps

1. **The objective here is days only.** Hours and fees are available in the posterior. Externalities (missed nuisances, wrongful denials, deterrence) need an outcome layer, which the generator does not yet have.
2. **Town choice is modelled as "fastest admissible design".** Real towns follow practice, inertia and staffing. A choice model should be learned from real law changes (AB 2188 / SB 379 adoption), per `docs/process-model-causal-frame.md`.
3. **Sufficiency (C2) is coded as evidence-type sets.** Real sufficiency standards are richer. The C2 check is where an LLM legal reader is most useful, and most in need of calibration.
4. **Real data.** Solar permitting has checkable constraints already:
   - AB 2188 checklist requirements and its shot clocks;
   - phantom requirements, as C5 violations visible in forum reports;
   - deadlines, as compliance.

## Simulating externalities: G-Sim (flagged by Alex)

Holt, Ruiz Luyten, Berthon and van der Schaar, *G-Sim: Generative Simulations with Large Language Models and Gradient-Free Calibration* (arXiv:2506.09272):
- An LLM proposes a simulator's structure and causal relations.
- Its parameters are then calibrated to data by gradient-free optimization or simulation-based inference (SBI), giving a posterior over the parameters.

This matches our split: the LLM supplies the structure menu, and an exact Bayesian likelihood calibrates it. It becomes directly useful for the externality layer, where the simulator cannot be exact. The LLM would propose mechanisms, for example:
- a nuisance occurs → a neighbour complains → enforcement follows;
- expected burden → the applicant is deterred → keeps hens without a permit.

Those mechanisms would then be calibrated by SBI to sparse outcome data (complaint counts, enforcement actions, permitted versus actual installations). The same caution applies as to our LLM priors: LLM-proposed mechanisms encode common sense and may not transfer across jurisdictions. We would keep the structure menu explicit and test it against held-out outcome data, as we do for process structures.

**Assessment after reading the method (2026-09-28).** Most of G-Sim is what we already do: an LLM supplies the structure and data calibrate it. Our exact likelihood and averaging over structures are stronger on uncertainty. G-Sim's own limitations section says its SBI posteriors ignore structural uncertainty.

Two ideas are new for us:
1. **A structure-revision loop.** Failed fit diagnostics are turned into text, and the LLM proposes a revised mechanism. Our analogue: when posterior predictive checks fail, or a design or phantom requirement falls outside the menu, an LLM proposes an additional design or mechanism. We add it to the menu with explicit prior weight, rather than replacing the menu.
2. **SBI for simulators without a tractable likelihood.** This is needed once externalities involve heterogeneous behaviour or feedback. The first outcome layer (`docs/2026-09-28-toy-statute-outcomes-plan.md`) still has an exact likelihood, so SBI is deferred.

