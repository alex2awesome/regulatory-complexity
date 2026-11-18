# Proposal: fitting the whole chain, text → decision model → process → outcomes (2026-09-29)

Alex asked (2026-09-29) to consolidate the reading-layer discussion, its audit (`docs/2026-09-29-reading-layer-audit.md`) and the literature (`docs/LITERATURE.md`) into a new way of fitting the full chain. Today the Bayesian model covers only process → observations, with the decision model and the design menu hand-coded from one reading of the text (see the audit, §1). This proposal makes the first two links explicit, with stated uncertainty, without trying to model language probabilistically.

## 1. The model, layer by layer

```
L0  text                          observed, fixed
L1  interpretive questions Q      enumerated (taxonomy + LLM + human), incl. a residual
L2  reading r  ∈ ×_q answers      per jurisdiction: r_t ~ Cat(w);  w ~ Dir(κ · p0(r | text))
L3  decision model D(r)           deterministic from r: required steps, order, deadline, authorized burdens
L4  valid design set V_r          deterministic: validity checker over a compositional design space
L5  process S_t ~ p(S | r_t, ψ)   choice model, family {uniform-valid, cost-softmax, risk-averse, imitative}, slack ε
L6  process parameters θ          step laws, town speed, loop rates (existing model)
L7  observations                  admin records, reports, web pages (existing exact likelihood)
L8  outcomes                      safeguard catch/false-flag, deterrence, complaints, survey (existing model)
```

Only L5–L8 are probabilistic models of behaviour and measurement. L1–L4 are deterministic constructions plus one elicited prior, p0(r | text). That is where the LLM and the cognitive model enter.

### L1. Enumerating the questions

- Run the Massey et al. (2014) ambiguity taxonomy over the statute: each vague term, scope ambiguity, undefined procedure, and cross-reference becomes a question with a small answer set.
- Have the LLM propose questions independently, then merge, with a human pass to drop non-questions.
- Always include a **residual** answer ("some reading not listed"). Practice that no listed reading explains flows there, and it is the diagnostic that triggers re-reading (the G-Sim loop, §4).

### L2. The reading prior, grounded in a cognitive model of vagueness

Most of a statute's interpretive questions come from gradable or threshold predicates: "nuisance", "reasonable fee", "complete application", "adjoining". Lassiter and Goodman (2017) model such a predicate as having an uncertain threshold on a scale. The listener infers a distribution over the threshold from the word's use and from a prior over the scale. Two consequences for us:

1. **A reading is a threshold setting, so p0(r | text) is naturally a distribution, not a point.** For "nuisance", the scale is a nuisance degree that setback, coop size and hen count map onto. The reading "desk review of the site plan suffices" is the claim that the threshold is checkable from plan features.
2. **The prior over the scale is local.** A dense town has more mass at high nuisance degrees, so the inferred threshold, and hence the reading, shifts. The model *predicts* systematic, not random, variation in how the same words are read, correlated with local conditions.

The prior is then a pooled elicitation:

> p0(r | text) ∝ admissible(r) × Π_k score_k(r)^λ_k, plus residual mass ρ

- Elicitors k: the RSA-style threshold model where a scale can be defined; LLM direct probabilities per question; LLM parse frequencies over K samples (correlated, so down-weighted); legal sources where they exist (case law, AG opinions, agency guidance).
- Admissibility (mechanical): the reading preserves every concrete clause, is internally consistent, and its mandated waits fit the statute's own deadline.
- λ_k and ρ are the elicitors' calibration. With one statute they are sensitivities. Across statutes they are learned supra-Bayesianly: the elicitor's output is data with a likelihood whose reliability is estimated (Carvalho and Hartmann; the audit §2b).

**Does the cognitive model hold up?** It was fitted to adjective judgments in the lab. Whether institutions read statutory predicates the same way is open, and our data can test it. Predictions:
- Across the 58 California counties reading the same solar or CalFresh words, inferred readings should correlate with the local prior over the scale, e.g. stricter nuisance or fire-setback readings where density is higher.
- Readings elicited from the LLM should track the threshold model's predictions where the scale is well defined, and diverge where it is not (procedural vagueness such as "shall determine").
- If neither holds, the threshold model is dropped from the pool and the prior falls back to the LLM and legal sources.

### L3–L4. Decision model and valid designs, generated rather than hand-written

- Each reading fixes a decision model: required d-steps, ordering, deadline, authorized burdens, permitted denial grounds.
- The design space is compositional, not a menu: subsets of safeguards × serial or concurrent arrangement × where the decision issues × fee items. For the hen statute that is a few dozen designs instead of six.
- The validity checker (`docs/process-validity.md`, C1–C6) computes V_r for every reading. Designs invalid under every admissible reading are still in the space, with mass only through ε.

### L5. The choice model

This is the crux (audit §2b). A jurisdiction's process is the action; its reading is the latent belief; p(S | r, ψ) is the rational-actor model in inverse planning (Baker, Saxe and Tenenbaum 2009). Predeclared family, all with slack ε for invalid practice:

| Model | p(S | r) ∝ | What it assumes about agencies |
|---|---|---|
| Uniform-valid | 1[S ∈ V_r] | No preference among valid designs. Produces the size principle. |
| Cost-softmax | 1[S ∈ V_r] · exp(−cost(S)/τ) | Agencies minimize their own or applicants' burden. |
| Risk-averse | exp(β · #{readings under which S is valid}) | Agencies buy legal safety ("defensive proceduralism"). |
| Imitative | mixture with neighbours' or the state's modal design | Nou and Nyarko's regulatory diffusion. |

Reading and preference are confounded in cross-sectional data. The reading posterior is reported under each model, and ψ is learned only where text changes or many jurisdictions give leverage.

### L6–L8. Process and outcomes

Unchanged: the exact enumeration and FFT likelihood for the process model, and the Poisson-cell outcome model. Two changes:
- The structure prior is no longer uniform over six designs; it is Σ_r p(r_t) p(S | r_t, ψ) over the compositional space.
- Outcomes are fitted jointly with the process posterior where the cost allows, not cut. The 2026-09-28 results showed the cut passes burden-estimation error into the deterrence slope.

## 2. Inference: staged, with the cuts made explicit, then a joint check

| Stage | What is computed | Cut? |
|---|---|---|
| A | Questions, admissible readings, elicited p0(r \| text), V_r | No data |
| B | Process model fitted with a uniform prior over the full compositional design space. Particles carry p(data_t \| S, θ) for every town and design. | — |
| C | Reading and choice layer by **exact importance reweighting** of Stage-B particles: weights Π_t Σ_S p(S \| r_t, ψ) p(data_t \| S, θ) / Σ_S p(data_t \| S, θ)/\|designs\|. Gives p(r_t, w, ψ, θ \| data) under each choice model. | None; exact given B |
| D | Outcome layer on the same particles, jointly weighted (outcome likelihood × Stage-C weight). Compared with the cut version. | Reported both ways |
| E | Statute edits as interventions on L1–L4: an edit fixes answers or changes constraints, so V_r and p0 change; everything below is re-evaluated with the θ, ψ posterior held. Effects reported per choice model, with prior-driven parts labelled. | — |

Stage C is cheap because the process model already enumerates structures exactly. It is a reweighting, but of the full particle set, not of the structure posterior alone (audit §2a).

**What is identified, by layer.**
- θ: as established in rounds 2–3 (boundary events or structural variation).
- Readings: weakly, from cross-sectional practice, and always relative to the choice model. Text changes (AB 2188, SB 379) identify readings and ψ far better than more jurisdictions do.
- κ (agreement among agencies): with enough jurisdictions. This is a statute-level complexity measure: how much of implementation variety is interpretive.
- Outcomes: as in `docs/2026-09-28-toy-statute-outcomes-results.md`.

## 3. Estimands added by the new layers

- p(r_t | data): which reading each agency acts on, per choice model.
- w and κ: the population of readings and how concentrated it is; **interpretive variety** as distinct from preference variety.
- Residual mass: how much practice no listed reading explains.
- For each question q: the burden and outcome difference between its answers, i.e. what resolving that ambiguity is worth. This is the "cost of vagueness" per clause, now computed rather than asserted.
- Edit effects with uncertainty through readings, choice and θ.

## 4. The refinement loop (from G-Sim)

Diagnostics → re-reading, as a documented procedure:
1. Fit stages B–D.
2. If residual mass is high, or a step is common in practice but required by no reading, hand the LLM the specific pattern ("every town does X; no reading requires it") and ask for a candidate reading or a missing decision step, possibly from another law.
3. Add it to the reading set with explicit prior weight. Never replace the set. Refit.

## 5. Validation plan

**Toy round 4** (predeclared before running):
- Generator: 15 towns, each with a true reading drawn from a known w; a true choice model (cost-softmax with a risk-aversion term); the compositional design space; the existing process and outcome layers.
- Elicitation: LLM direct probabilities and parse frequencies; the threshold model for the "nuisance" scale.
- Fits: Stage C under all four choice models, λ ∈ {0.5, 1, 2}, ρ ∈ {0.02, 0.1}.
- Predeclared readings: recovery of r_t and w under the true choice model; the bias under the wrong ones; how much the edit effects move across choice models.
- LLM baseline: asked the same questions, including each town's reading.

**Real data:** the 58-county solar corpus with AB 2188 / SB 379 as text changes; county guides give observed designs, permit logs give θ, and complaints or enforcement give outcomes.

## 6. What changes relative to today

| Today | Proposed |
|---|---|
| One hand-coded reading | A distribution over admissible readings, elicited and calibrated |
| Six hand-written designs | A generated compositional design space, filtered by validity per reading |
| Uniform structure prior | Reading × choice-model prior, with slack |
| Statute edits forced by hand (everyone to S1) | Edits as interventions on readings and constraints |
| Outcomes cut from the process posterior | Joint weighting, with the cut reported for comparison |
| No account of *why* towns differ | Interpretive variety (κ) separated from preference variety (ψ) |

## 7. Limits stated in advance

- Readings are inferred only relative to a choice model. No cross-sectional design escapes this.
- The cognitive model of vagueness is a hypothesis to be tested, not an assumption; the pooling handles its failure.
- Elicitor calibration is not learnable from one statute.
- A residual reading absorbs misspecification; a large residual is a finding, not a fit.

## 8. The inverse-planning reading of the whole chain (added 2026-09-29, after Alex's question)

All three components are Bayesian inversions of an approximately rational agent.

- **RSA (Lassiter & Goodman).** L0(x | u, θ) ∝ P(x)·[[u]](x; θ); S1(u | x, θ) ∝ exp(α(log L0 − cost(u))); L1(x, θ | u) ∝ S1 · P(x) · P(θ). The listener inverts a planning speaker to recover meaning jointly with the latent threshold θ. Vagueness is uncertainty about θ.
- **Inverse planning (Baker, Saxe & Tenenbaum).** P(goal, belief | action) ∝ P(action | goal, belief) · P(goal, belief).
- **Ours.** The legislature is the speaker; the agency is the listener (forming a reading r, i.e. θ for the vague predicates) and a planner (choosing an implementation S given r and its goals ψ); we invert the agency from partial observations of S:

  P(ψ, r, S, θ | data, text) ∝ P(data | S, θ) · P(θ) · P(S | r, ψ) · P(r | text) · P(ψ)

  | slot | ours |
  |---|---|
  | goal | ψ: the choice model (cost, risk, imitation) |
  | belief | r: the reading; prior from the RSA-style listener and other elicitors |
  | action | S: the process design, **unobserved** |
  | dynamics | θ: step laws; needed because actions are seen only through emissions |
  | observation | records, reports, web pages: intervals that each span a *subset* of S's steps |

Consequences: (i) actions are inferred from partial emissions, so two designs differing only in a step no record spans are indistinguishable (the boundary-event rule, restated); (ii) goals and beliefs are confounded within one situation, and are separated by watching the same agency across statutes or across an amendment (AB 2188 / SB 379), exactly as Baker et al. use the same agent across situations; (iii) the legislature's choice of vague wording is itself a planning act (Kaplow), a third inversion left out of scope.
