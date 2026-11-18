# Audit of the proposed "reading layer" (2026-09-29)

Alex asked (2026-09-29) for an audit of the reading-layer proposal in the conversation of 2026-09-28/29: whether the probability calculations are actually Bayesian, what G-Sim contributes, and what linguistics, cognitive science and legal scholarship say about actions taken under vague directives. This note records the audit, the corrections, and the references checked.

## 1. What was proposed

A layer above the process model:

- **Reading.** A reading is one answer to each interpretive question the statute raises (Q1–Q5 in `docs/process-validity.md`). Each reading is a decision model.
- **Prior.** p(reading | text), from an LLM or legal sources.
- **Choice model.** p(town's process | reading): a town uses a design valid under its reading with probability 1 − ε, otherwise something else.
- **Posterior.** p(reading | text, processes) ∝ p(reading | text) × Π_towns p(process_t | reading).

## 2. Audit findings

### 2a. The posterior is Bayesian, but my worked table was wrong

The update rule is ordinary Bayes over a discrete latent. Two corrections:

1. **The ε model I used was distorted.** I gave the invalid-practice probability ε to the invalid designs *only*, spread uniformly among them. Under a reading where exactly one design is invalid, that design then receives all of ε (0.1), which is more than any valid design gets. That artefact is what kept "desk review insufficient" at 27–28% in the earlier table. The defensible form is a mixture with uniform practice: p(S | r) = (1 − ε)·1[S ∈ V_r]/|V_r| + ε/|all designs|.
2. **The result depends heavily on the choice model.** With the same prior (0.49 / 0.21 / 0.30) and the same three observed processes (S1, S3, S4):

   | Choice model | Desk suffices, no neighbour input | Desk insufficient, no neighbour input | Neighbours must be heard |
   |---|---|---|---|
   | Earlier table (ε concentrated on invalid designs) | 0.68 | 0.28 | 0.04 |
   | Uniform within the valid set, ε mixed with uniform | 0.93 | 0.06 | 0.01 |
   | Softmax cost-minimizer within the valid set | 0.91 | 0.07 | 0.02 |

   The direction is robust: observed practice without neighbour input is strong evidence that agencies do not read §3 as requiring it. The magnitudes are not robust. The "size principle" (readings that allow fewer designs get more credit) is a consequence of the uniform-choice assumption, not of the data.

3. **The table treated each town's process as known.** In the fitted model, processes are latent, so the correct likelihood is the marginal p(data | reading) = ∫ Π_t Σ_S p(S | r) p(data_t | S, θ) p(θ) dθ. This is computable from the saved SMC particles by importance reweighting, since each particle already carries p(data_t | S, θ) for every S. The reweighting also updates θ, slightly. It is not a free reweighting of the structure posterior alone.

### 2b. Where the non-Bayesian parts are

- **Tempering the LLM score** (score^λ, plus residual ρ) is not a generative model. It is a calibration map, the same device as temperature scaling of classifiers or a logarithmic opinion pool with weight λ. The fully Bayesian version is the **supra-Bayesian** treatment: the LLM's parse is *data*, with a likelihood p(LLM output | true reading) whose parameters (its calibration) are learned across many statutes. With one statute, λ and ρ are unidentified and must be sensitivity settings. See Genest and Zidek (1986) for opinion pools, Lindley (1983/1985) for the supra-Bayesian idea, and Hartmann and Carvalho (2022, *Bayesian Analysis*) for Bayesian inference over pooling weights.
- **The choice model is the crux, and it is a behavioural model, not a legal one.** This is inverse planning: the reading is the agency's latent belief, the process is its action, and we need a model of how agencies act given beliefs (Baker, Saxe and Tenenbaum 2009). Cost-minimizing, risk-averse, imitative and habitual agencies imply different likelihoods, and hence different reading posteriors. Any result must be reported under several choice models, or the choice model's parameters must be learned, e.g. from law changes.
- **Readings versus preferences are confounded.** A town that adopts the heaviest process might read §3 strictly, or might read it loosely and be risk-averse ("defensive proceduralism", `docs/process-validity.md`). Cross-sectional practice cannot separate the two. Text changes can: a safe harbour changes the valid set without changing risk aversion.

### 2c. Verdict

The proposal is sound as a model *class*, but two things must be made explicit before it is built or reported:

1. The choice model p(S | r) is an assumption that drives the answer. Run it as a predeclared sensitivity family, at minimum uniform-within-valid, cost-softmax and risk-averse (valid under the most readings).
2. The prior p(r | text) is an elicited quantity, and its calibration cannot be learned from one statute. Report it as sensitivity.

The reading posterior should be read as "which readings the agencies are acting on, under an assumed choice model", not as a legal finding.

## 3. G-Sim: parallels

G-Sim (Holt et al., arXiv:2506.09272) alternates three steps. An LLM proposes a simulator's structure; the numerical parameters are calibrated to data by gradient-free optimization or simulation-based inference; fit diagnostics are turned into text and fed back so the LLM revises the structure.

The reading layer maps onto that loop almost exactly:
1. **Propose:** the LLM parses the statute into candidate readings.
2. **Calibrate:** observed practice updates the reading weights, and the process model is fitted below.
3. **Refine:** the residual class and unexplained steps (practice no reading accounts for) are the diagnostics. They go back to the reader as "find the missing requirement or reading".

Two differences remain, both in our favour. Our calibration step has an exact likelihood where G-Sim needs simulation-based inference. And we keep every proposed reading with a weight, so structural uncertainty stays in the posterior. G-Sim's authors list the loss of structural uncertainty as a limitation.

## 4. Literature checked

### Legal scholarship on precision and vagueness
- Diver (1983), *The Optimal Precision of Administrative Rules*, 93 Yale L.J. 65. Distinguishes transparency, accessibility and congruence of a rule and analyses the trade-off among them. It is the closest antecedent to our "cost of vagueness". The three properties map onto our measures: openness (transparency), self-assessability and guidance deficit (accessibility), and the wrongful-denial and missed-nuisance rates (congruence).
- Kaplow (1992), *Rules versus Standards*, 42 Duke L.J. 557: standards defer the cost of giving content to the law to the enforcement stage. Our finding that vagueness shifts burden through legal risk is the same mechanism.
- Ehrlich and Posner (1974), *An Economic Analysis of Legal Rulemaking*; Sunstein (1995), *Problems with Rules*; Endicott (2000), *Vagueness in Law*.
- Nou and Nyarko (2022), *Regulatory Diffusion*, 74 Stan. L. Rev. 897: agencies copy each other's rule text, which is relevant to the choice model. Imitation is a plausible mechanism for how a town picks a process.

### Empirical implementation variation
- The literature repeatedly reports that vaguer directives produce more variance in implementation when implementation is local (e.g. Staton and Vanberg's positive theory of judicial vagueness, and the state-policy heterogeneity literature). Little of it measures the variation at the level of *process steps*, which is exactly the gap our estimands fill.

### Regulatory ambiguity in requirements engineering
- Massey, Rutledge, Antón and Swire (2014), *Identifying and Classifying Ambiguity for Regulatory Requirements*, RE 2014: an ambiguity taxonomy, with analysts finding about 33 ambiguities per 104 lines of legal text. This is a ready-made procedure for step 1 of the reading layer, enumerating the interpretive questions, and a source for the residual class.
- Kempe et al. (2024), *Modeling, Analyzing and Communicating Regulatory Ambiguity*.

### Linguistics and cognitive science
- Lassiter and Goodman (2017), *Adjectival vagueness in a Bayesian model of interpretation*, Synthese 194:3801. In the Rational Speech Acts framework a vague predicate has an uncertain threshold, and the listener infers a distribution over it. "Nuisance" is such a predicate: a reading is a threshold setting. This is the direct theoretical model for p(reading | text) as a distribution rather than a point.
- Goodman and Frank (2016), *Pragmatic language interpretation as probabilistic inference*, TiCS. The RSA framework more generally.
- Baker, Saxe and Tenenbaum (2009), *Action understanding as inverse planning*, Cognition 113:329. Inferring latent beliefs from actions via a rational-choice likelihood is exactly our reading inference, and it makes explicit that the inference is only as good as the assumed choice model.
- Tenenbaum and Griffiths (2001), *Generalization, similarity, and Bayesian inference*: the size principle, which appears in our reading posterior under uniform choice.

## 5. Consequences for round 4

- Enumerate the questions with a taxonomy (Massey et al.), and include a residual reading.
- Predeclare a family of choice models and report the reading posterior under each.
- Treat λ and ρ as sensitivities. Across statutes, plan to learn them supra-Bayesianly.
- Use the exact particle reweighting for p(data | reading), not the known-process shortcut.
- Use the G-Sim style loop only as a documented procedure: diagnostics → new candidate readings, added with explicit prior weight, never replacing the set.
