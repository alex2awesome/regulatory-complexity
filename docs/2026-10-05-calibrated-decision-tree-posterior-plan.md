# Calibrated posterior over decision-tree models: plan (2026-10-05)

Alex, 2026-10-05: "Central goal: a calibrated posterior over different decision-tree models that uses
agency documents, timing analysis, clues and hints from social media commentary. The calibrated model
can use the same Hoff approach that Dan likes, Grabmair's too." Constraints already agreed: archive first
(done: `runs/archive_toy_statute_v3_20261005/`), change the engine minimally, keep timing from the
start, order = synthetic calibration, then a real anchor, then ADU. Rules-as-code is a null check
only. Background: `reports/Uncertainty over legal decision models.md`.

**Deliverable of this doc:** the model, the inference, the validation protocol and the change list,
for sign-off before code. **Status:** proposal; nothing built.

## 1. What is estimated
For each jurisdiction j, its **decision tree** T_j: the reading it gives every predicate the statute
and local rules create (setback, unit size, parking, owner occupancy, fire access ...), and from that
its **behavior**: for any case facts x, approve, send back for correction, or deny. The posterior is
over T_j for every jurisdiction, plus a statewide layer that says how much of the cross-jurisdiction
variation the statute permits. "Calibrated" means: across planted synthetic truths, events the
posterior gives 70% happen 70% of the time, at every level and for every reported quantity.

Behavior, not tree syntax, is the identified object. Two trees that decide every case the same way
cannot be told apart by any data, so they form one hypothesis class (Vernie & Grabmair's equivalence
over a shared interface). This is the same move as Hoff, Raftery & Handcock, who report distances,
never coordinates, because positions are identified only up to rotation.

## 2. Model

**2.1 Tree hypotheses.** A predicate catalogue k = 1..K per domain. Each predicate has an ordered
reading space R_k (e.g. rear setback: none / 4 ft / 10 ft), with a strictness score per reading; local
and optional predicates include "not applied". Each predicate also has a kind κ_k (crisp, standard,
delegated, capped), an evaluating step and a fixability flag. Fixability decides the consequence of
failing: a fixable failure triggers a correction round, a fatal one a denial. T_j = (r_j1..r_jK). Step 1
uses conjunctive trees (deny on any fatal failure; correct fixable failures), which is how
`benchmark/synth/generator/decision.py` plants them. Step 2 adds OR and exemption structure, using
trees that LLM readers propose from the statute (Vernie & Grabmair-style formalizations, matched to
the catalogue by node equivalence).

**2.2 Hoff layer: latent-space prior over readings.** Jurisdictions and readings sit in one latent
space: P(r_jk = r | z_j) ∝ exp(α_kr − ||z_j − w_kr||), with z_j ~ N(0, I_D). This is a bipartite form
of the Hoff et al. model, in which a tie means "jurisdiction j adopts reading r". It pools across
predicates: a town strict on parking is likelier strict on setbacks, so a town with few observations
borrows from similar towns. At D = 1 it reduces to an ideal-point (strictness) scale. Crisp predicates
get a misimplementation prior instead: P(statutory reading) = 1 − ε_mis. Reported quantities are
invariant to rotation and reflection: P(r_jk = r), pairwise behavioral distances, and dispersion.

**2.3 Grabmair layer: behavior space.** A scenario set X holds:
- draws from the applicant distribution;
- every boundary fact pattern where two candidate readings disagree. This is Vernie & Grabmair's SAT
  edge cases; with threshold predicates these are enumerable, so no solver is needed.

From X we get:
- **behavioral distance** between trees = the share of scenarios decided differently;
- **equivalence classes** = trees at distance 0 on X;
- **per-scenario posteriors**: P(outcome | x, j) with intervals.

The scenarios carrying the most posterior uncertainty are reported as "where the law is uncertain".
They are also the targets for the next document or question.

**2.4 Channel A: agency documents (reader measurement model).** Each document d about j has a stated
reading ŷ_dk ∈ R_k ∪ {vague, absent}. The document is:
- exact with probability φ_exact(kind_d);
- an adjacent reading with probability φ_approx;
- another reading with probability φ_wrong;
- vague with probability φ_vague.

Here kind_d is the document kind: ordinance, checklist, FAQ, third-party guide, HCD letter, and so on.
Readers m (LLM families and prompts, a rules-as-code formalizer as the null-check reader, Gemma for
volume) report y_dkm given ŷ_dk with a Dawid–Skene confusion matrix C_m. Readers of the same document
share ŷ, so they share that document's errors. Several LLM readings of one page therefore count as
one noisy view, not several; independent evidence comes from distinct documents and channels. This
matters because LLMs choose the same wrong answer often (Kim et al. 2025; lit review). A family-level
shared-mistake component covers models of one family erring together. A Hoff latent space over
readers is added only if a posterior predictive check shows residual reader-pair agreement. The LLM
readings, which today enter `toy_statute` only as a pooled prior (`readings.pooled_question_probs`),
become measurements with a likelihood. **This is the main conceptual change.**

**2.5 Channel B: timing (existing engine, one link).** The engine's per-town, per-design
log-likelihood ℓ_j(s; θ) stays unchanged. It covers step durations, correction rounds, open cases,
mentions and web pages. The tree enters through two links:
- **Correction propensity.** logit-scale lpinc_j = η(T_j) + u_j, with u_j ~ N(0, τ²).
  - η(T) maps P(at least one correction round) = 1 − ∏_{k fixable} (1 − q_{k,r_k}) through the
    engine's truncated-geometric tilt. (lpinc is that tilt, not a per-review probability.)
  - q_kr = expit(β_k0 + β_k1 · strictness_kr), with β_k1 ≥ 0, so a stricter reading fails more cases.
  - u_j absorbs applicant-pool differences.
- **Design.** p(s | T_j) puts most of its mass on the design T_j implies: a predicate read as "not
  applied" removes the step that only it needed.

Timing therefore says how often cases fail fixable checks, at which step, and under which design. It
cannot say which predicate failed.

**2.6 Channel C: social-media commentary.** Gemma codes each post against a closed codebook, and every
quote is replay-verified. A post yields:
1. the predicates the poster says they failed, and whether they were fixed;
2. stated readings, which go to Channel A as a low-fidelity "forum" document kind;
3. timing statements, which go to the engine's existing mention terms.

For (1): given T_j, a case fails predicate k with q_{k,r_jk}. The same q as Channel B, and this is the
coupling: forums say which predicate, timing says how often, documents say which reading. A failed
predicate is mentioned with recall ρ_k, and an unfailed one with false rate ε. Posting is selective:
P(post) ∝ 1 + γ·[any failure], γ ≥ 0. γ is learned where admin timing pins the failure rate; elsewhere
it stays at its prior and widens intervals. Posts with unknown jurisdiction enter as a mixture over
jurisdictions weighted by their geographic hints, not dropped.

**2.7 Ambiguity vs discretion (Isabel's question).** Both show up as the same thing in outcomes:
jurisdictions deciding the same facts differently (Fischman 2014's bound). The model keeps them
separate by carrying κ_k as latent. Its prior comes from statute-text readers ("does this provision
fix a test, set a standard, or delegate?"). In real data, HCD findings that a local rule exceeds the
statute are direct evidence that the dimension is not delegated. Reported per predicate:
- dispersion of jurisdiction readings (behaviorally identified);
- P(κ_k) (identified only through text and HCD).

These are reported side by side and never multiplied into one number. Discretion = dispersion the
statute permits; ambiguity = uncertainty about what the statute fixes.

## 3. Inference
- **Continuous parameters**, sampled by the existing tempered SMC (`smc.py`) with the blocked town
  kernel (`blocked.py`):
  - the engine's timing parameters;
  - β, τ, φ, C, ρ, ε, γ, α, w, ε_mis;
  - z_j, which joins its town's block.
- **Discrete trees, exact.** For each town and each particle, T_j is enumerated exactly. The prior,
  Channel A and Channel C factor over predicates. The timing link depends on T only through
  Σ_k log(1 − q_{k,r_k}) and the design.
  - Step 1 (K ≤ 6, |R_k| ≤ 4): brute force, at most 4,096 trees per town.
  - Real ADU: dynamic programming over that sum, on a 256-bin grid; the binning error is checked once.
  - The town's log marginal replaces today's logsumexp over designs, in the same two places
    (`Model.loglik` and `blocked.TownCache._town`).
- **Reporting.** p(T_j | data) is the particle average of the exact conditionals (Rao–Blackwellized).
  Behavior classes, scenario outcomes, dispersion and κ are functionals of it.
- **Mode trapping**, the documented real-data failure: the discrete part cannot trap, because it is
  enumerated. The continuous part needs ≥ 2 independent runs passing the engine's estimand gate
  (`smc.gate_v2`), judged on invariant quantities only. If runs disagree, that is reported as a
  failure, as for Solar.

## 4. Validation protocol
| Tier | Data | What it tests | Pass |
|---|---|---|---|
| 0 | none (prior only) | sampler targets the prior | prior marginals recovered within MC error. Codex found the blocked kernel fails this today; fixing it, or using a passing kernel, is a precondition |
| 1 | simulated from this model (N = 200 replicates; 8 towns, K = 5, 150 cases, 3–6 documents and 10–30 posts per town) | inference code is calibrated (SBC) | rank ECDFs inside family-wise 95% simultaneous bands for every test quantity: reading indicators (randomized ranks for discrete), behavioral distance to a fixed reference tree, strictness sum, q, φ, log-likelihood; reliability diagram of P(r_jk = r) within binomial error |
| 2 | `benchmark/synth` decision-layer worlds (≥ 6 worlds × 64 jurisdictions; planted readings, attribute distributions, self-selection, back-office checks) | calibration under realistic misspecification (generator ≠ model) | 50/80/90% coverage and reliability within ±5 points per bin (n ≥ 200 per bin); log score vs baselines: one LLM tree, reader majority vote, literal-statute rules-as-code (null) |
| 3 | W2_DEV_001 rendered text (3,723 artifacts rendered so far) with LLM readers in place of the oracle reader | the text-reading step | calibration drop vs Tier 2 is attributed to reader error the model does not capture |
| 4 | ADU real, k-fold held out by jurisdiction (the final fit uses all data) | real anchor | calibrated on held-out HCD letter findings, quoted ordinance provisions (Channel A) and APR Ministerial/Discretionary labels (design) |

**Ablations** in Tiers 1–2, on the same replicates: all seven channel combinations (D, T, F, DT, DF,
TF, DTF). The reported table gives log score, posterior entropy and calibration per combination. Each
combination should be calibrated; they differ in sharpness. This table is the answer to "what does
timing add".

**What timing adds (expected).** Timing pins jurisdiction-level strictness on fixable checks: correction
frequency, with the step and design. A document that states some readings plus a timing-pinned
strictness total narrows the readings no document states. Without timing, those unstated readings rest
on the latent-space prior alone, borrowed from similar towns. Predicates that rarely bind are
unidentified by outcomes (lit review). Their posterior should stay at the prior, and Tier 1 checks
that it does not pretend otherwise.

## 5. Changes against the archived engine
| File | Change | Size | Default path |
|---|---|---|---|
| `toy_statute/config.py` | `decision_trees: bool = False`, tree-spec path | ~5 lines | off: bit-identical |
| `toy_statute/model.py` | tree mode: town term = `tree_posterior.town_logmarginal`; lpinc's Beta prior off (the link supplies its density); tree parameter names | ~40 lines | off: unchanged; fingerprint appended to `likelihood_compatibility.json` |
| `toy_statute/blocked.py` | town block includes z_j; `_town` calls the same town term | ~10 lines | unchanged when off |
| `toy_statute/jax_backend.py` | none in Steps 1–2 (CPU) | 0 | – |
| new `trees.py` | catalogue, reading spaces, enumeration, outcome function, scenario set, behavioral distance, equivalence classes (same pattern as `hypotheses.equivalence_classes`, but over behavior on scenarios) | ~250 | – |
| new `reader_model.py` | document fidelity, Dawid–Skene confusion, family shared mistakes; (j,k,r) log-lik tables | ~200 | – |
| new `latent_space.py` | Hoff prior tables | ~80 | – |
| new `tree_posterior.py` | exact per-town enumeration; Rao–Blackwellized outputs | ~200 | – |
| new `sim_trees.py` | Tier 1 simulator: θ from prior → trees → timing via `generate.py`'s case simulator, documents, posts | ~250 | – |
| new `calibrate_trees.py` | SBC ranks, reliability, ablations | ~200 | – |
| new `synth_adapter.py` (Step 2) | generator world → evidence package, observable fields only | ~250 | – |
| new `tests/test_toy_statute_trees.py` | default bit-identity; enumeration = brute force; simulator ↔ likelihood consistency | ~150 | – |

The engine changes are ~55 lines in three files. Everything else is new modules. Stage C reweighting
and the pooled reading prior stay for the old path; tree mode does not use them.

## 6. Steps, budgets, definitions of done
1. **Tiers 0–1 (Claude).**
   - Deliverable: the modules above except the adapter; `runs/tree_posterior_sbc_<date>/`; one results
     doc.
   - Done when: Tier 0 passes, SBC passes at N = 200, and the reliability and ablation tables are
     written.
   - Budget: about two working sessions of code; at most 12 h wall on sk3 (the laptop only runs tests).
     On an SBC failure: fix once, rerun once, then report.
2. **Tiers 2–3 (Claude).**
   - Done when: coverage, reliability and the baselines table exist on ≥ 6 generator worlds, plus a
     text-reader subset of W2_DEV_001.
   - Budget: at most 24 h on sk3, plus one overnight Gemma batch on sk2.
3. **Tier 4 + ADU fit.** Bayesian modeling for ADU is Codex's under CLAUDE.md. Claude builds the
   evidence package (catalogue from Gov. Code §§ 66310–66342 and the 302 quoted ordinance
   provisions; HCD letters; APR timing; triaged Reddit) and a handoff. Codex fits it after Steps 1–2
   pass.

## 7. Assumptions (conservative defaults)
- Conjunctive trees in Step 1; OR and exemption structure in Step 2.
- Evaluating step and fixability are statewide in Step 1, jurisdiction-specific later.
- D = 1 by default; D = 2 is compared by held-out log score in Tier 2.
- A "stale" document (one stating a superseded reading) is scored as wrong in Step 1.
- Step 1 links only correction rounds. Fatal predicates are informed by documents and forums; a
  denial-rate link follows once a timing package carries outcomes. The engine's timing likelihood has
  no denial path.
- lqobj (objection) stays free per town.
- Tier 2 uses an oracle-transcription reader:
  - it emits each generator reveal's stated value, with fidelity labels and every truth/spec field
    stripped;
  - it is a measurement simulator on the generator side, not a fitter;
  - a scripted check asserts that no truth or spec key reaches the evidence package.
- No data is dropped; Tier 4 holds out by k-fold, and the final fit uses everything.

## 8. Decisions for Alex
1. The Tier 2 oracle reader (§7, last bullets) sits next to the "fitters never read specs" rule. OK as
   written, or Tier 2 on rendered text only (slower, fewer worlds)?
2. Ownership: Steps 1–2 here, the ADU fit to Codex?
3. `runs/` is gitignored, so the archive is local only. A durable copy means committing the current
   `pipeline/procbench/toy_statute/` source (needs approval).
4. `docs/CORE_GOAL.md` says the decision model is "fixed and known with high confidence". Under this
   plan it becomes latent and is estimated with stated uncertainty. Edit once on sign-off.
