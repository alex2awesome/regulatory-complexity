# A generative model of process evidence

**2026-09-16 update:** The current joint agency/task/case implementation is in
[2026-09-16-bayesian-process-v4.md](2026-09-16-bayesian-process-v4.md), with
[experiments and unresolved limitations](2026-09-16-bayesian-process-v4-results.md).
The earlier finite-step/detection-model pilot remains documented in
[2026-09-16-bayesian-process-v3.md](2026-09-16-bayesian-process-v3.md).
An alternate, fully glossed [simplified TikZ package](figures/latex_plate_diagram_simplified/README.md)
keeps elapsed timing, payer work and agency work separate. Sections below retain
the historical design discussion; “built” and “calibrated” claims should not be
read as the current implementation status. Synthetic end-to-end scoring was also
corrected: the scorer had ignored the LLM's `process_timing` field.

Alex's framing, 2026-09-15: *"extract a structured package [from every piece of evidence], then a complex generative story — sample agencies, sample steps, sample timing — and calculate posteriors over everything."*

That is the right division of labour, and it settles the question underneath it ("do we need actual models, or can we rely on LLM interpretations?"). **The LLM is an instrument, not a judge.** It converts unstructured evidence into structured packages with measurable error rates. A probabilistic model, not the LLM, decides what is true.

## 1. The two layers

```
  evidence  --LLM extractor-->  structured package  --generative model-->  posterior over the process
  (page, PDF, reddit post)      (claims + metadata)   (latent steps,         (steps, actors, durations,
                                                       actors, timing)        with credible intervals)
```

The extractor never aggregates, never reconciles, never fills a gap. It reports what one document says, with a verbatim quote, and records what the document does **not** say — a missing actor is data, not a hole to fill. Everything else is inference.

## 2. The structured package (per piece of evidence)

```
{ doc_id, kind, publisher, audience, date, jurisdiction,
  claims: [ { about: "step" | "process",
              name, actor|null, occasion|null,
              duration: {value_days, kind: statutory_cap|target|observed|reported, quote} | null,
              fee: {amount, when} | null,
              order: {before:[...], after:[...]},
              rework: {back_to, reason} | null,
              quote, extractor_confidence } ],
  silences: ["states no actor for the review step", "gives no fee"],
  reliability: { tier, first_or_second_hand, is_dated, internal_consistency, hedging_level } }
```

`silences` matter as much as claims: under the generative model, a program page that describes a step **without** naming its department is evidence that the department is not applicant-facing information, not absence of evidence.

## 3. The generative story

Sample, in this order:

1. **Agencies.** `A_j ~ P(actors | jurisdiction type, population, department directory)`. With an agency map published (see `benchmark/synth/DESIGN.md`), `A_j` is *observed*, and actor attribution collapses from open-vocabulary generation to a selection problem with a chance baseline — which is exactly why adding directories to the world is a modelling decision, not decoration.
2. **Steps.** The statute's mandated skeleton is observed. Local additions are drawn from a nonparametric prior (CRP-like): the number of steps is not fixed, and "is this a new step or one I already hold" is a posterior over partitions rather than a thresholded LLM verdict.
3. **Attributes per step.** actor `a(s) ∈ A_j`; visibility `v(s)`; fee; and duration `D_s ~ LogNormal(μ_s, σ_s)` with `μ_s` drawn from a **hierarchical prior over the step key** `(agency_class, task_type, channel, blocking_party, cadence, jurisdiction_class)` — the priors in `pipeline/priors/`. Hierarchy is what lets an unmeasured step in a new jurisdiction borrow strength.
4. **Order.** A partial order over steps; rework edges as loops.
5. **Versions.** A changepoint process over time. Fees, departments and steps change, so parameters are indexed by version — this is what makes a contradiction between a 2023 and a 2026 source *informative* rather than noise.
6. **Cases.** Each applicant is a trace: a path through the graph with realised durations, an outcome, and rework rounds.
7. **Documents.** For each document kind `k`, a **disclosure propensity** `π(reveal field F of step s | k, v(s))` and a **fidelity** distribution (exact / approximate / vague / wrong). A user post is generated from a *case*: the applicant posts with probability depending on their outcome and elapsed time (complaint selection), and mentions a subset of the steps they personally saw.
8. **Extraction.** The LLM reads a document and emits the package above with per-field sensitivity and false-positive rates that depend on `k`.

## 4. Why every nuisance parameter is identifiable

Because the synthetic world is generated from exactly this story with known truth, the disclosure propensities, the fidelity distribution, the complaint-selection function and the **LLM's own sensitivity and false-positive rates per document kind** can all be estimated there, then carried to the real corpus as priors. That is the point of the synthetic environment: not to benchmark, but to **calibrate the instrument**.

## 5. What the posteriors answer

- *Does a step exist?* Beta-Binomial over documents that **could have** disclosed it — the denominator is the set of documents whose kind has non-zero propensity for that visibility class, not all documents read. Without that correction, a staff-only step looks unlikely simply because nobody publishes it.
- *Which agency owns it?* A categorical posterior over `A_j`, with the directory as prior support, evidence as observations, and the LLM's confusion rates as the noise model — a Dawid–Skene structure in which each document kind is an annotator with its own reliability.
- *How long does it take?* A posterior duration distribution, with statutory caps excluded from the fit and re-entering as a derived `P(exceed)`, and a drift term. Already implemented in `pipeline/priors/latent_timing.py`.
- *Are two sources in conflict?* Only if no version boundary separates them. Otherwise the disagreement is **drift**, and both are right about their own period.

## 6. Goodness of fit, without gold

Four checks that do not need an answer key, all applicable to the real corpus:

1. **Held-out disclosure.** Hold documents out; a well-fitted model should mostly be *confirmed* by them. The new-node rate on held-out documents is the fit statistic.
2. **Order stability.** Permute the reading order and refit. Agreement between the fits (Jaccard over aligned steps) bounds how much the result is an artifact of what was read first.
3. **Posterior predictive coverage on timing.** Do held-out duration observations fall inside the predicted intervals at the nominal rate?
4. **Residual evidence.** The share of accumulated claims whose asserted values the fitted model does not reproduce, after drift is accounted for.

## 7. What exists now, and what does not

| piece | state |
|---|---|
| structured extraction per document, with silences and quotes | `pipeline/procbench/prompts/extract_candidates.md` — built |
| assignment step (existing node / new node / refines / contradicts) | `pipeline/procbench/incremental.py` — built, LLM with a deterministic fallback |
| update step, contradictions recorded with tier | built (deterministic code, no LLM) |
| saturation curve and endogenous stopping rule | built |
| latent duration distributions, caps as derived P(exceed), drift | `pipeline/priors/latent_timing.py` — built |
| hierarchical prior over step keys sharing strength | partly: the step key exists and is populated; pooling is currently median-based, not hierarchical |
| Beta-Binomial existence with a could-have-disclosed denominator | **not built** — needs the disclosure propensities |
| disclosure propensities and LLM error rates, calibrated on the synthetic world | **not built** — this is the next real piece of work, and everything above depends on it |
| posterior over partitions (CRP) rather than thresholded verdicts | **not built** — currently a verdict from one LLM call |
| the four goodness-of-fit checks | **not built** |

## 8. Which latent gets which family (corrected 2026-09-15)

Alex's correction: the sketch was hand-wavy, and not everything is binomial — timing in particular is continuous. Right. The model is **mixed-type**, and reaching for one family is the error. The inventory:

| latent quantity | support | family | why not something else |
|---|---|---|---|
| does step *s* exist | binary | Bernoulli(θ), θ ~ Beta | the **denominator** is what matters: trials are documents that *could have* disclosed it, not all documents read |
| how many steps there are | unbounded count | Dirichlet process / CRP | the dimension is unknown; "new step or one I hold" must be a posterior over partitions, not a threshold |
| **duration of step *s*** | positive, right-skewed | **LogNormal: log D ~ Normal(μ_s, σ_s²)** | a plain Gaussian puts mass on negative days; delays are multiplicative and heavy-tailed |
| **step-key location μ** | real | **Normal(μ_family, τ²)** — partial pooling | this is the second Gaussian layer, and it is what lets a key with two observations borrow strength from its family |
| which agency owns *s* | categorical over A_j | Categorical(π), π ~ Dirichlet | selection from a published universe, with the LLM's confusion matrix as the noise model (Dawid–Skene) |
| fee | positive, administered | **unknown constant + observation noise**, not a random draw | a fee is a parameter of the rule. It only becomes a distribution *across jurisdictions*, where it genuinely is a draw |
| rework rounds per case | count ≥ 0 | Geometric / Negative-Binomial | repeated Bernoulli trials with a per-round failure probability |
| outcome (approve / deny / abandon) | categorical | Categorical, Dirichlet prior | |
| order among steps | partial order | distribution over linear extensions, or pairwise Bernoulli with transitivity | the hardest piece and the least developed |
| version changepoints | times | changepoint process | what makes a dated contradiction informative rather than noise |
| disclosure propensity π(kind, visibility, field) | probability | Beta, hierarchical over kind × visibility | calibratable on the synthetic world |
| LLM sensitivity / false-positive rate per kind | probabilities | Beta | the instrument's error, estimated not assumed |
| selection tilt γ | real ≥ 0 | Gamma or truncated Normal | measured at the wrong sign so far; see §5 |

**Implemented so far** (`pipeline/priors/latent_timing.py`): the LogNormal duration family, and the Gaussian hierarchy over step keys by empirical Bayes — a key's log-mean is shrunk toward its (agency_class, task_type) family with weight τ²/(τ² + σ²/n). Measured effect: 51 of 86 keys rest on two anchors or fewer and shrink by a median factor of 0.25 toward their family, while well-evidenced keys (n ≥ 9) move by 0.00–0.10 and keep their own estimate. Intervals are reported at 68% and 95%.

**Honest limit**: this is empirical-Bayes point estimation with a normal-approximation interval, not a posterior. τ² is estimated from between-key spread and floored, σ is taken from a p50/p90 pair where one exists and from weighted spread otherwise. A real posterior over (μ, σ, τ) needs sampling, and the fee, rework, order and changepoint components above are specified but unimplemented.

## 9. Non-stationarity: one distribution that moves (2026-09-15)

Alex: *"we can have draws from one non-stationary distribution, right? like a normal that transitions through time?"* Yes, and that is strictly better than what was there. `pipeline/priors/latent_timing.py` handled drift with two hacks — exponential recency weighting and a refit on the recent half. Both are crude approximations to a **continuous-time local-level model**, now implemented in `pipeline/priors/drift_model.py`:

```
state        mu_t | mu_s ~ Normal(mu_s, tau^2 * (t - s))     random walk in continuous time
observation  y_t = log(duration) ~ Normal(mu_t, r_k^2)       r_k set by the evidence tier
```

Three properties matter for this corpus. Evidence is **irregularly spaced** (1999–2026), so the state variance grows with the elapsed gap rather than per observation. Observation variance is **tier-dependent**: an audited figure enters at r²=0.10, a forum post at 0.55, so a single audit outweighs several anecdotes without any hand-set weights. And **known changepoints** — a fee resolution superseded, an ordinance amended — are injected as a variance shock at that date, so the process is permitted to jump there instead of having to explain the jump as noise. A changepoint we know from a document is far better identified than one the model must discover.

Fitted on 23 step keys with four or more dated observations. Drift is large and goes both ways:

| step key | then | now | drift |
|---|---|---|---|
| state agency / decision | 67.6 d | 22.7 d | 0.34× |
| caseworker / decision | 17.6 d | 10.4 d | 0.59× |
| plan review / document review | 58.1 d | 33.6 d | 0.58× |
| background check / records check | 10.9 d | 16.5 d | 1.51× |
| records unit / decision | 186.1 d | 224.9 d | 1.21× |

The filter also reports an interval at the current date rather than a point, which is what a prior needs to be usable.

## 10. How steps get assigned to agencies — and why a universal prior will not do it

The generative form. A statute names an actor in some elements and is silent in others; the jurisdiction resolves the silence. Three mechanisms are visible in the corpus: **existing machinery** (whoever already does the nearest thing absorbs the new duty — the Hayward retrofit), **lineage** (the ordinance is copied from a neighbour, and the assignment comes with it), and **explicit delegation** (the local code names an officer). So:

```
a_i ~ Categorical( softmax( affinity(act_type_i, role(d)) + lineage_j + structure_j ) ),  d in D_j
```

The question is whether `affinity` is a transferable object — learn it once, apply it to an unmeasured jurisdiction. **Measured across all nine real processes (551 observations with both fields), it mostly is not.** Normalised entropy of the agency distribution per act type, where 0 means one agency class always performs that act and 1 means uniform:

| act type | n | distinct agency classes | normalised entropy |
|---|---|---|---|
| interview | 19 | 2 | 0.30 |
| appeal | 18 | 3 | 0.38 |
| inspection | 25 | 3 | 0.65 |
| payment | 28 | 3 | 0.91 |
| decision | 105 | 10 | 0.81 |
| issuance | 43 | 7 | 0.95 |

Median across 15 act types: **0.83**. Only `interview` and `appeal` are concentrated, and those are concentrated by definition rather than by practice — an interview is what a caseworker does, an appeal is what a hearing officer hears. For everything that matters (decisions, document review, issuance, intake, scheduling) the act type barely narrows the actor.

Two consequences. First, **actor attribution is genuinely jurisdiction-specific**, which is consistent with the statutes explicitly leaving "which department administers" open, and it means the prior has to come from the jurisdiction's own structure — its department roster and what those departments already do — not from a global act-to-agency table. Second, this raises the value of publishing an **agency map** in the world (DESIGN.md): without the roster, actor is close to unidentifiable, since documents state it for only 36% of steps and the act type adds little.

One caveat against over-reading this: the `agency_class` taxonomy mixes organisational level with role (`state_agency` and `caseworker` are not the same kind of category), so some of that entropy is taxonomy artifact rather than real dispersion. Re-measuring under a cleaner role/level split is a to-do.

## 11. How many steps have we not found?

Capture-recapture. Treat each document as a capture occasion and each step as a species: steps seen once (`f1`) and twice (`f2`) give the Chao1 lower bound `S_obs + f1²/(2·f2)` on the true number. On the current fits this reads 26 observed to 44 estimated (truth 13) and 99 to 174 (truth 30) — useless, because the assignment step over-split and every duplicate looks like a fresh singleton. The estimator is only meaningful once assignment is right. Even then, its equal-catchability assumption fails here by construction: a staff-only step is far harder to capture than an applicant-facing one, so it needs the **stratified** version, with a separate richness estimate per visibility class.

## 12. Code and model review (2026-09-15, Fable reviewing Opus's work)

A line-by-line audit of the statistical code, testing each numerical routine against cases with known
answers rather than re-reading it. **Four defects found and fixed, and two published claims retracted.**

### Defects in the code

| # | where | defect | direction of the error | fixed |
|---|---|---|---|---|
| 1 | `drift_model.py` | observation variance passed through `** 0.5`, so a variance was used where the filter expects a variance | every observation under-trusted, and the tier spread compressed from 5.5× to 2.3× — the tier weighting barely operated | yes |
| 2 | `drift_model.py` | the first observation served as **both** the prior mean and an observation, with a non-diffuse prior (P₀=1) | estimates pulled toward the earliest evidence, which inflates the drift factor the module exists to report. Verified: a no-drift filter on 1..5 returned 2.92 instead of 3.00 | yes, diffuse prior |
| 3 | `latent_timing.py` | between-key variance taken as the raw spread of key means | Var(observed means) = τ² + mean(s²ₖ), so τ² was over-stated and every key **under-shrank** | yes, subtract the within-key term |
| 4 | `incremental.py` | `docs.index(doc)` used to map a document to its extraction | two identical document dicts both resolve to the first, silently mis-assigning candidates | yes, positional index |

Effect on published numbers: median change in a drift factor 0.030, median change in a "now" estimate
**9.7%**, worst cases large — plan review's drift moved 0.58× → **0.35×** and state-agency decision
0.34× → **0.21×**. Median shrinkage rose 0.127 → 0.149 as the τ² correction predicts. Verified after
fixing: the no-drift filter recovers the sample mean exactly; a tight observation is tracked; a loose one
is ignored; the smoother beats the filter mid-path; the shrinkage formula matches a hand computation;
P(exceed cap) moves in the right direction.

### Two claims retracted

**Retraction 1 — "the act type barely narrows the actor."** I reported a median normalised entropy of
0.83 and concluded that only `interview` and `appeal` are concentrated, so a transferable affinity prior
will not work. The method was wrong: H/Hₘₐₓ is not comparable across act types whose category count K
runs from 2 to 10, and small-n rows are biased. Tested properly against a same-n same-K uniform null
(200 draws), **8 of 14 act types are informative at z < −2**, carrying 0.61 bits on average:

| act type | n | K | H observed | H null | bits gained |
|---|---|---|---|---|---|
| document_review | 64 | 7 | 1.64 | 2.74 | **1.10** |
| appeal | 18 | 3 | 0.61 | 1.50 | 0.89 |
| interview | 19 | 2 | 0.30 | 0.96 | 0.67 |
| decision | 105 | 10 | 2.68 | 3.26 | 0.57 |
| inspection | 25 | 3 | 1.04 | 1.53 | 0.49 |
| records_check | 80 | 4 | 1.52 | 1.97 | 0.45 |
| issuance | 43 | 7 | 2.67 | 2.71 | 0.04 (none) |
| intake_screen | 34 | 7 | 2.61 | 2.68 | 0.06 (none) |

So the affinity prior **is** partially learnable, and §10's conclusion is wrong as written. The defensible
version: knowing the act type genuinely narrows the agency for review, decision, records-check,
inspection, interview and appeal, and tells you nothing for issuance and intake screening — which are
exactly the acts any department can perform. The agency map is still valuable, but as a complement to a
real affinity prior rather than as a replacement for one.

**Retraction 2 — "there is no bunching below deadlines."** I compared the 13% of durations sitting in
the band just under the cap against nothing at all. Against the fitted log-normal's own expectation for
that band, observed mass is **1.88× expected** (17 observed against 9.0 expected over 167 durations) —
weak evidence *for* a deadline effect, the opposite of what I claimed. It is not decisive at n=17, and
the test is partly circular because the distribution was fitted to the same points. The honest statement
is that the clock may partially bind and a clean test needs the band excluded from the fit, or a
discontinuity design. The compliance figure itself (53% under cap) stands.

### What survived the audit

The log-normal family and the queue/touch split; the empirical-Bayes shrinkage algebra (matches hand
computation exactly); the Kalman filter and RTS smoother after fixes 1–2; `P(exceed cap)`; the
`actor_selection` metric (canonicalisation, chance baseline and lift verified on a constructed case);
`decide_offline` (matches an obvious paraphrase, opens new nodes otherwise); all 9 pytest cases, the web
fixture tests, the generator smoke test, and the W1 validation at 1,467 objects with 0 errors. Every
module imports and every CLI parses.

### Known weaknesses left standing, in priority order

1. **Effective sample size is a weight sum, not a count.** `n = weight_total` treats one audited figure
   (weight 3.0) as three independent draws, so every interval is optimistic. Now documented in the code;
   the fix is to carry a real count alongside the weight.
2. **σ is estimated three different ways** (from a p50/p90 pair, else from a range, else from weighted
   spread across heterogeneous sources) and with two anchors it is close to arbitrary. σ should be pooled
   hierarchically the way μ now is.
3. **Not a posterior.** Empirical-Bayes point estimates with normal-approximation intervals, with τ²
   estimated from the same data it shrinks.
4. **The incremental fit over-splits badly** (26 nodes for 13 true steps; 99 for 30) because assignment
   ran deterministically. Every number from those runs is a floor pending the LLM-assignment ablation.
5. **Chao1 is unusable** until assignment is fixed, and needs stratifying by visibility class regardless.
6. **`agency_class` mixes organisational level with role**, so part of the affinity signal above is
   taxonomy artifact.

## 13. The model the diagram entails: factorisation, priors, posteriors (v2, 2026-09-15)

`docs/figures/plate_diagram.svg` was audited and redrawn. **Five structural errors, three missing nodes,
one misparented node, one inconsistency with the text.** What v1 got wrong: steps were nested under the
jurisdiction alone though they depend on the statute too; the realised duration sat in the case plate
though it is indexed by case *and* step; disclosure propensity and extractor error were drawn per
document, which asserts a separate propensity for every document rather than one per kind; the duration
state had no time index though §9 makes it a random walk; and the fee floated with no parent.

### The joint, factorised

```
p(everything) =
   p(Φ) p(α_τ) p(μ_fam, τ²) p(τ²_walk) p(π) p(ε) p(α_CRP)                              globals
 · Π_s  p(E_s, c_e, prec_s, O_s)                                                        statute (observed)
 · Π_j  p(A_j) p(L_j) p(F_j) · Π_d p(δ_d) p(ρ_d) p(κ_d) p(ψ_d) p(v_d)                   jurisdiction, departments
 · Π_js p(R_js | O_s, L_j) p(Z_js | E_s, R_js, α_CRP)                                   local rule, which steps exist
 · Π_i∈Z p(a_i | τ_i, A_j, Φ, L_j) p(τ_i | E_s) p(b_i | τ_i) p(v_i | a_i, b_i)
        p(W_i | α_τ, δ_d) p(Q_i | ρ_d, κ_d, b_i) p(μ_i,t | μ_fam, τ², τ²_walk, v_d)
        p(σ_i) p(f_i | F_j) p(≺ | prec_s)                                                steps
 · Π_n  p(path_n | ≺) p(R_n) · Π_i p(T_n,i | μ_i,t, σ_i) · p(Y_n | ·) p(S_n | Y_n, ΣT)   cases, selection
 · Π_m  p(k_m) p(t_m) p(claim_m | Z, a_i, v_i, f_i, k_m, π) p(y_m | T, S, μ_i,t, k_m) p(pkg_m | claim_m, ε_k)
```

### Priors — what goes in

| parameter | prior | grounded how |
|---|---|---|
| Φ act→agency affinity | Dirichlet rows over agency classes | estimable: 8 of 14 act types informative, 0.61 bits mean (§12) |
| α_τ act-type touch time | Normal, hierarchical over act types | from the priors corpus |
| μ_fam, τ² step-key family | Normal–Inverse-Gamma | empirical Bayes now; τ² corrected for within-key noise (§12) |
| τ²_walk drift rate | Inverse-Gamma; currently fixed at 0.05/yr | should be estimated, is not |
| π(k,v,F) disclosure | Beta, hierarchical over kind × visibility | **calibratable on the synthetic world** — the whole point of it |
| ε_k extractor sensitivity / FPR | Beta per document kind | same; not yet done |
| α_CRP new-step rate | Gamma | controls over-splitting, which is the fit's worst failure |
| δ_d, ρ_d, κ_d, ψ_d department practice | Normal; Beta; Categorical; Beta | ψ_d anchored at the measured 0.53 compliance |
| A_j department roster | observed where a directory is published, else CRP | the agency-map addition turns this latent into data |
| σ_i log-duration shape | should be hierarchical; currently three ad-hoc rules | weakness 2 in §12 |

### Posteriors — what comes out

| posterior | form | state |
|---|---|---|
| does step *i* exist | Beta-Binomial, denominator = documents that **could have** disclosed it (π > 0 for that kind × visibility) | not built; needs π |
| how many steps there are | CRP partition posterior; richness stratified by visibility | not built; Chao1 unusable until assignment is fixed |
| which department owns *i* | Categorical over A_j, with Φ as prior and ε_k as the noise model (Dawid–Skene) | metric built (`actor_selection`), model not |
| duration μ_i,t, σ_i | log-Normal; filtered/smoothed at any date, with intervals | **built** (`drift_model.py`, `latent_timing.py`) |
| P(exceed the shot clock) | derived from the fitted log-Normal and c_e | **built**; but see the bunching retraction (§12) |
| order i ≺ i' | from case traces as linear extensions, plus document order statements | not built |
| π, ε (nuisance) | Beta posteriors, identified on the synthetic world | not built — the highest-value missing piece |
| predictive for an unseen jurisdiction | via the hierarchy: borrow Φ, α_τ, μ_fam | partially: pooling exists, Φ does not |

### Does the story make sense? Three places it is still wrong or unsupported

1. **Duration is drawn per (step, case) but reported per step.** The generative side is right — each case
   realises its own T. The inference side still fits one (μ_i, σ_i) per *step key*, not per step, so the
   model as coded pools across steps that share a key even within a program. That is a deliberate
   simplification, not what the diagram says.
2. **`b_i` (who waits) is drawn as a child of τ_i**, implying the act type determines who waits. That is
   too strong: the same act can block on either party (a third-party inspection blocks the applicant in
   one jurisdiction and the agency in another). It should be a child of the local rule R_js.
3. **`S_n` (whether a case gets posted) is drawn from outcome and total elapsed** — the complaint-selection
   story. The measured log-ratio of community to official durations came out **negative** (§5), which this
   structure cannot produce. Either the selection function is not the dominant effect, or applicants and
   agencies are timing different intervals, in which case the model needs a per-source *scope* variable
   saying which segment a reported duration covers. That variable is missing, and it is the most likely
   single reason the timing layer under-performs.

## 14. The six weaknesses, addressed (2026-09-15)

| # | weakness | status | where |
|---|---|---|---|
| 1 | effective sample size was a weight sum, so one audited figure counted as three draws | **fixed** | Kish n_eff = (Σw)²/Σw² in `hier_fit.py`; equals the count under equal weights, 11.64 for a 14-anchor key with mixed tiers |
| 2 | σ estimated three ad-hoc ways, arbitrary on two anchors | **fixed** | σ_k is now a sampled parameter with an Inverse-Gamma hierarchy, so a thin key inherits the family's shape and reports its own 90% interval |
| 3 | empirical-Bayes point estimates, τ² fitted to the data it shrank | **fixed** | conjugate Gibbs over (μ_k, σ_k, m_family, τ², s²) in `hier_fit.py`; τ² now has a posterior: mean 0.92, 90% CI [0.51, 1.42] |
| 4 | the incremental fit over-splits | **partially — and the partial fix is not legitimate** | see below |
| 5 | Chao1 unusable, needed stratifying | **fixed for gold, still blocked on fits** | `richness.py` |
| 6 | `agency_class` mixed organisational level with role | **fixed** | taxonomy v2 splits `agency_level` × `agency_role` |

### Sampler validated before use

On simulated data (40 distinct keys in 5 families, unequal weights, known truth): μ recovered to mean
absolute error 0.187 log-units against a truth spread of 0.786; **90% interval coverage exactly 0.90**;
τ² recovered 0.689 against 0.640; σ 0.644 against 0.600; and shrinkage is monotone in evidence — the
thinnest twelve keys move 0.27 of the way to their family mean, the thickest twelve only 0.06.

The honest consequence of fixing (1) and (3) together: **the old intervals were too narrow.** A well-evidenced
key like the background-check records check read 11–18 days at 68% under empirical Bayes and now reads
9.9–22.1 days at 90% with the shape uncertainty included. And τ² comes out far larger than the empirical-Bayes
point estimate, meaning step keys genuinely differ more than the old fit allowed — so the old version
over-shrank thin keys toward their family.

### (6) Splitting level from role does not wash the affinity out

`state_agency` names an organisational level; `plan_review` names a function. Separated:

| projection | act types informative at z<−2 | mean information |
|---|---|---|
| `agency_class` (v1, conflated) | 8 of 14 | 0.61 bits |
| `agency_role` (v2, role only) | 8 of 14 | **0.66 bits** |
| `agency_level` (v2, level only) | 9 of 12 | 0.34 bits |

So the §12 retraction survives the cleaner taxonomy, and the defensible claim sharpens: **the act tells you
the function, and rather less about the organisational level.** `agency_class` is retained for continuity,
with `agency_class_split` mapping it onto the two dimensions.

### (5) Stratified richness: our gold is probably missing two-thirds of the back office

Capture occasion = a distinct source document; species = a step. Plain Chao1 is invalid here because
catchability is structurally unequal — an applicant-facing step is disclosed by nearly every document kind,
a staff-only step by almost none — so the estimate is computed per visibility stratum and summed. Over the
16 real gold models (451 evidenced activities):

| stratum | observed | estimated | implied unseen |
|---|---|---|---|
| applicant_facing | 318 | 470 | +48% |
| applicant_inferable | 51 | 69 | +36% |
| **staff_only** | **82** | **232** | **+182%** |

The ordering is what theory predicts, and the size of the staff-only gap is the substantive finding: even
built from the best staff-side documents we could find, the gold models plausibly capture about a third of
the steps that exist. Caveats that matter: capture occasions are **not independent** (a city's fee schedule
and its program page share an author), each model rests on only 4–9 documents so f1/f2 are noisy, and the
three solar models return almost no unseen steps because their evidence is unusually evenly spread — a
different capture structure, not a complete process.

### (4) Over-splitting: a lexical merge cannot fix a semantic problem

A post-fit agglomerative consolidation was added (`incremental.consolidate`, union-find over the scorer's
similarity, support summed, merges logged to `merges.json`). Sweeping its threshold:

| threshold | synthetic F1 | real F1 |
|---|---|---|
| 0.60 | 0.60 | 0.40 |
| 0.52 (default) | 0.60 | 0.40 |
| 0.44 | 0.55 | 0.47 |
| 0.36 | **0.34** | **0.53** |
| 0.30 | 0.36 | 0.44 |

The two corpora want opposite thresholds. Real duplicates are lexically similar, because the dealer manual
repeats phrasing across chunks, so merging helps (0.40 → 0.53). Synthetic duplicates are **semantic
paraphrases** — which is exactly what the world generator's naming drift was built to produce — so merging
destroys real steps before it catches duplicates (0.60 → 0.34). A threshold that has to be tuned per corpus
against gold is a hyperparameter fit to the answer, not a fix. The default stays conservative at 0.52,
where it does no harm and little good.

**The real fix is an LLM in the assignment step**, which is what the design always specified; it ran
deterministically only because the Codex account is over its usage limit. Every number from those fits
remains a floor until that ablation runs.

## 15. How much better is the Bayesian model? Measured, and mostly not (2026-09-15)

Head-to-head, leave-one-out, so that nothing is scored on data it was fitted to. Two different questions,
two different answers.

### Question 1: predict a step key we have never observed (transfer)

Hold out every observation of a key, fit on the rest, predict it. Median absolute log error:

| family definition | global median | family median (naive pooling) | hierarchical posterior |
|---|---|---|---|
| (agency_class, task_type) | **0.705** | 1.181 | 0.909 |
| task_type only | **0.735** | 0.955 | 0.762 |
| agency_class only | **0.728** | 0.795 | 0.790 |

**The global median wins under every family definition.** Ignoring the step entirely and quoting the
median of all durations in the corpus beats both naive pooling and the hierarchy. The hierarchy does not
transfer to unseen keys — with 44 testable keys spread over small, heterogeneous families, a family's
location is a worse guide than the corpus as a whole. This is a real negative result and it kills the
"learn a prior once, apply it to an unmeasured jurisdiction" story in its current form.

### Question 2: estimate a key we DO have evidence for (the normal use of pooling)

Hold out one observation, predict it from the rest, 152 held-out observations over 27 keys:

| predictor | median absolute log error |
|---|---|
| global median (no step model) | 0.837 |
| the key's own median | 0.453 |
| the key's median shrunk toward its family | **0.437** |

So **conditioning on the step key cuts error by 46%**, and that is the large, real win — but it is not
Bayesian, it is just using the right covariates. Bayesian shrinkage adds a further **3.6%** on top.

### What the Bayesian machinery actually buys

Not accuracy. Calibration and honesty:

- **Intervals that are close to nominal.** 90% predictive intervals cover 84% of held-out truths. No point
  estimator offers an interval at all, and the empirical-Bayes intervals it replaced were demonstrably too
  narrow (§14).
- **Posterior uncertainty in the hierarchy itself**: τ² = 0.92 with 90% CI [0.51, 1.42], rather than a
  single number estimated from the data it shrinks.
- **A shape parameter for thin keys** that is inherited rather than invented from two points.
- **P(exceed the shot clock) with an interval** instead of a ratio of medians.

### The honest summary to carry into any write-up

> Knowing what kind of step it is cuts duration error by nearly half. Bayesian pooling adds a few percent
> on top of that for steps we have data on, and makes things *worse* for steps we do not. What it adds
> that nothing else can is a calibrated interval. Report it as a calibration result, not an accuracy one.

Two caveats that could change this. The corpus is 620 observations over 9 processes, so families hold 1–7
keys; the hierarchy may simply be starved. And the step key was designed before any of this was measured —
if `blocking_party` and `cadence` matter more than `agency_class`, as the queue/touch split implies, then a
re-keyed hierarchy might transfer where this one does not. Both are testable and neither has been tested.

## 16. Four edges the diagram was missing (2026-09-15)

Checking in- and out-degree node by node, rather than by eye, found two nodes that pointed nowhere and
two missing parents. One was a genuine modelling error:

- **`f_i`, the fee, had no outgoing edge at all.** A latent that nothing observes is unidentifiable and
  does no work — it could take any value without changing the likelihood. Fees are disclosed by
  documents (measured: for only 9% of steps, which is precisely the kind of fact the disclosure
  propensity exists to represent), so `f_i → C_m`.
- **`a_i`, the actor, only fed visibility.** But actor disclosure is one of our central measurements —
  documents name the department for 36% of steps — so `a_i → C_m` as well.
- **Durations were observable only through a case.** `y_m` depended on `T_{n,i}` alone, which says every
  reported duration comes from someone's lived experience. A large share of our evidence is an agency's
  published median, which describes `μ_{i,t}` directly and not any one case. Added `μ_{i,t} → y_m`.
- **`τ_i`, the act type, had no parent.** It comes from the statute's mandated element: `E_s → τ_i`.

`g_m`, the extracted package, correctly points nowhere — it is the terminal observable, the leaf of the
whole model. The remaining parentless nodes are the globals, the observed statute inputs, and three
exogenous draws (`R_n`, `t_m`, and the jurisdiction-level variables), which is as intended.

The §13 factorisation is updated to match; both the TikZ figure and the SVG carry the new edges.
