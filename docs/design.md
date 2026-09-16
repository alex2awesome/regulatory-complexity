# Design: measuring and simplifying regulatory complexity

*Working document. 2026-08-31.*

## 1. Formal objects

A rule `R` (text) does not define a single decision function; it defines an **identified set** `F(R)` of defensible decision functions — the readings a careful implementer could adopt. This is the Manski-style partial-identification view of a statute.

**The licensed relation (canonical framing, 2026-09-01).** Equivalently: the rule licenses a *relation*, not a function — `Lic(x) = {y : some f ∈ F(R) has f(x) = y}`, the set of outcomes a scenario `x` can validly execute to. A thin rule has `|Lic(x)| = 1` everywhere; **discretion = the plausible-scenario mass where `|Lic(x)| > 1`** (or, graded, `E_x[log|Lic(x)|]` under a calibrated case distribution). This is the quantity everything else serves. Three divergence levels must never be conflated:

1. **Structural divergence** — different trees/vocabularies parsed from the same text. NOT the target; instrument scaffolding noise (pin segmentation, crosswalk fields), though diagnostically interesting (readers disagree about what facts are even asked for).
2. **Within-reading openness** — one reading's judgment/reference nodes leave a scenario's outcome open (the executor's reachable-outcome set; per-tree P(discretion)).
3. **Cross-reading outcome divergence** — defensible readings assign a fixed scenario different outcomes (the k-compilation comparison, valid only on a shared scenario space).

Levels 2 + 3 together constitute `|Lic(x)| > 1`; level 1 matters only because uncontrolled structural divergence blocks running the *same* scenario through all readings, which is what makes levels 2–3 measurable. The looseness band is exactly this measurement for a single predicate: band mass = plausible-scenario mass with two valid executions.

- A **compilation** `f ∈ F(R)` is an executable decision tree (schema: `pipeline/schemas/decision_tree.schema.json`): span-grounded predicate nodes typed `objective` (executable expr), `judgment` (discretionary), or `reference` (delegated), over an input schema whose fields carry supplier, provenance class, and sensitivity.
- For a case `x`, one compilation yields a **reachable-outcome set** (judgment/reference nodes explored both ways). `|outcomes(f,x)| > 1` with pivotal judgment nodes ⇒ `x` is *discretion-exposed under f*.
- Across `k` independent compilations, `x` **diverges** if two compilations' outcome sets are disjoint. Divergent cases are **witnesses**: concrete households the text does not determine.
- Adjudication sorts each witness into `compilation_bug` (a reading violates a span or a declared monotonicity invariant — mechanical fix, not discretion), `schema_gap` (incomplete input vocabulary), or `genuine_underdetermination` (both readings defensible — the only bin that counts). Legal scholars are right that disagreement alone ≠ ambiguity; the adjudication step is what answers that objection. A sample of adjudications is human-audited.

Three complexity axes, never folded into one scalar:

| axis | quantity | measured by |
|---|---|---|
| size | nodes, depth, inputs, actors, unresolved references | `static_metrics` on a compilation |
| discretion | `P(D)` = population mass of genuinely underdetermined cases | k compilations × case panels × adjudication |
| burden | expected effort vector (hours, $, wait, trips, sensitive disclosures) along the realized path | `burden_of_run` under priors → data |

**Epistemic discipline (inherited from the metric-seam work's retraction lesson):** never measure vagueness by asking a model whether text is vague. Models appear only as *generators* — of compilations, cases, and adjudication proposals — and generators need no trust because every artifact they emit is checked by execution, by declared invariants, or by human audit of a sample. What is reported is always the behavior of executable artifacts.

**Metamorphic invariants:** compilers must declare, per predicate and input, the direction in which the input moves the predicate (`monotonicity`). These are testable claims about the statute ("adding a smoke alarm cannot flip approve→deny"), checked mechanically (`check_monotonicity`), in the style of metamorphic testing of tax software (Tizpaz-Niari et al., ICSE-SEIS 2023; arXiv:2205.04998, arXiv:2509.13471) — pointed at the statute rather than at software.

## 2. What this adds to the complexity debate

Prior work clusters into five literatures that do not compose:

1. **Static complexity metrics** — Katz & Bommarito (US Code), Ruhl & Katz (Iowa L. Rev. 2015), Colliard & Georg (*Measuring Regulatory Complexity*: regulation-as-code operator/operand counts on Basel rules), Coupette et al. (*Law Smells*). Text-only; discretion is invisible ("adequate" is one token); nothing is simplified.
2. **Rules as code** — Sergot et al.'s British Nationality Act in Prolog (1986) through Catala, OpenFisca, PolicyEngine; LLM frontier: Dutch permit decision models vs. 95 production models (arXiv:2604.17153), span-grounded deontic trees / NormBench (arXiv:2606.08932), IRC inconsistency detection (arXiv:2511.11954). Encoding is the *product*; discretion is an annoyance to be resolved, not a quantity to be measured. Evaluation stops at parsing fidelity.
3. **Software testing of legal-critical systems** — metamorphic/differential testing of tax software. The oracle-free validation machinery we import.
4. **Administrative burden** — Herd & Moynihan (learning/compliance/psychological costs), Sunstein's sludge audits, the PRA/ICR burden-hour inventory. Empirical and rich, but with no formal object to attach to.
5. **Reform microsimulation** — PolicyEngine, EUROMOD, TAXSIM: who gains/loses from a *given, hand-specified* reform. Nobody searches over candidate simplifications with a complexity objective.

The contribution is the composition, and specifically the middle of it: **discretion measured behaviorally as the diameter of the identified set on a case distribution** — a quantity none of the five literatures produces — plus the framing that follows from taking the *subject's* seat: complexity is the expected cost for a regulated person to learn their own outcome, which decomposes into reading cost (size), prediction cost (discretion), and production cost (burden). On this view "coded law vs. LLM-adjudicated law" is not an objectivity preference; it is Kaplow's ex ante/ex post cost allocation made measurable — a standard doesn't remove specification cost, it moves it onto the parties at decision time, and `P(D)` is its price tag. Conservation, not reduction: AB 2533 "simplified" by delegating to § 17920.3, and the deferred complexity reappears as hundreds of divergent city checklists.

The optimization half is then well-posed: choose a simple `g` minimizing size + expected burden subject to harm-weighted disagreement with `F(R)` (or with the empirical selection implementers actually made) ≤ ε on a calibrated population — asymmetric loss (wrong denial ≠ wrong approval), with the flipped cases reported *as people*, demographics attached. Two free-lunch families to demonstrate first: **reordering** (ask cheap, frequently-decisive questions first — zero outcome flips, pure expected-burden reduction) and **dead-branch pruning** (predicates that never bind on the calibrated population).

## 3. The burden pipeline (the time tax) and how to validate it

Two stages with different epistemic status, validated separately:

**Extraction** (does the audit find every demand?). An LLM pass over the text records every point where the process requires an input — explicit submissions, implicit proof obligations (a date cutoff silently demands proof of construction date), and process acts (inspections, appointments) — each span-grounded (`burden_audit.schema.json`). Validate by **recall**: hand-annotate 3–5 statutes exhaustively; additionally compare against implementers' own operationalizations (city checklists and application forms enumerate the demands cities believe the statute makes). Extraction errors are the cheap-to-fix kind.

**Effort model** (what does each demand cost?). Demands are classified on a six-rung provenance ladder (a: known offhand → f: government act); costs attach to *classes*, not items, which makes the model small, auditable, and transportable across rules (`pipeline/burden_priors.json`, all placeholder priors). Validation sources, best first:

1. **PRA/ICR burden-hour inventory** (reginfo.gov): every federal information collection carries a legally mandated burden-hours and cost estimate — thousands of labeled (form → hours) pairs. Held-out test: predict ICR estimates from form/statute text; agreement calibrates the class priors. IRS forms print per-form time estimates too.
2. **Published fee schedules** — dollar components validated exactly.
3. **Permit-record timestamps** (RegLab data): application→issuance elapsed time, resubmission counts. The real-world ground truth for wait and iteration burden.
4. **Market quotes** for class-e professional artifacts (engineer letters, third-party inspections).
5. **Ordinal validation**: absolute hours are hard, rankings are easy — pairwise "which demand is more burdensome" judgments from practitioners → Bradley–Terry, compared to the model's ordering. Cheap, do early.
6. Diary/time-use studies — gold standard, later, if ever.

Burden is **path-dependent** by construction: a case pays only for inputs demanded by nodes actually visited (`burden_of_run`). Derived quantities: expected burden under P(x); worst-case burden; **wasted burden** (effort demanded of cases whose only reachable outcome is deny — burden regressivity); count of `sensitive` disclosures (legal self-exposure, e.g. reporting an unpermitted unit to the agency empowered to cite it), reported separately and never folded into hours.

## 4. Validation plan for the discretion measure

- **Cross-implementer natural experiment.** AB 2533 forced every CA city to compile § 17920.3 into a checklist. Scrape 10–20 (collection point: `corpus/ab2533/checklists/`; ABAG/MTC publishes a regional template). Prediction: checklist divergence across cities concentrates on the predicates our k-compilation divergence flags; uniform items (smoke alarms) show neither.
- **Planted controls** (inherited discipline): rules with known-thin and known-thick predicates constructed by us; the pipeline must recover the plant. A compiler that resolves "adequate sanitation" into an invented threshold must be caught by adjudication (`compilation_bug` is for span violations; silent threshold-invention is the subtler failure the smoke test's vB illustrates — it surfaces as cross-compilation divergence, which is the point).
- **Order-invariance**: k compilations under different decomposition orders (document order / outcome-backwards / official's-eye order — see `run.py`); divergence attributable to prompt order rather than text is a measurement artifact to be reported.
- **External anchor, later**: real permit decisions; HCD noncompliance findings when they exist.
- **SARA as the planted-thin control corpus** (2026-09-01): SARA's 9 IRC sections were "moderately edited to make them self-contained and unambiguous" — i.e., an adversarially low-discretion statute corpus with gold Prolog. Run the full divergence instrument on SARA and it must read ≈0; a nonzero reading calibrates the instrument's noise floor. The two 2025 SARA-compilation papers (Jurayj/Holzenberger/Van Durre arXiv:2508.21051; SOLAR, arXiv:2509.00710, prompts at github.com/albsadowski/solar) both *name* formalization multiplicity and both deliberately suppress it as a nuisance variable ("a single ontology will ensure consistent knowledge base... isolating structured reasoning effects from ontology quality variations") — we measure as signal exactly what they control as confound; quotable positioning. Prompt techniques to adopt from SOLAR: the numerics/logic firewall ("extract rules WITHOUT encoding numeric thresholds — calculations handled separately by code") and vocabulary-shaping instructions (atomic properties over classes) to reduce structural divergence in our compile prompt. Anti-pattern to avoid: SOLAR's judge-agent loops Stage I until all *training cases* pass — fitting the formalization to gold answers destroys independence; our compilers must never see case outcomes.

## 5. Deep-research flags

Every node/answer the text cannot settle carries a typed flag rather than a guess: **REF** (delegated provision — resolve by bounded recursion through the reference graph), **LOCAL** (meaning fixed by the implementing jurisdiction — needs the local ordinance/checklist corpus), **EMPIRICAL** (needs real-world data — the burden validation sources above), **TACIT** (below the articulation floor — needs practitioner elicitation). The flag taxonomy is the router for "when is deep research needed."

## 6. Reconceptualization (2026-08-31): synthetic worlds as the primary instrument

The k-compilation divergence design (§1) measures discretion but inherits a residue of the transmitter–message–receiver problem from the metric-seam work: any measurement of the message (the rule text) is confounded by receiver quality (the compiler/adjudicator applying it). The fix is to promote the *planted-world controls* — the part of the prior work that carried its cleanest evidence — from sanity check to primary instrument: **plant the truth instead of trusting a judge.**

**The generative protocol.** Sample a latent world `z` (the unit's actual condition: wiring age, egress dimensions, plumbing state — fully specified by us), render observables `x = render(z)` (application documents, inspector notes, photo descriptions), and study decisions as a function of readings. Because `z` is known by construction, three tests separate that were previously confounded:

1. **Extractor test** (`x → ẑ`): can code / a model recover the facts from the observables? Scored exactly against planted truth. Measures input-thickness alone.
2. **Predicate test** (`z → decision`, no extraction): apply each predicate directly to the latent state, across an ensemble of readings. Measures criterion-thickness alone, uncontaminated by extraction.
3. **End-to-end** (`x → decision`): whether errors compound or cancel.

Planted truth is what fixes the receiver confound: calibrate the receiver on *anchor items* — thin predicates where the message fully determines the answer ("constructed before 2020" against a planted construction date). A receiver that passes anchors and fails on "adequate sanitation" localizes the failure in the predicate, not the receiver. Receiver quality becomes a measured calibration term instead of an assumption.

**Looseness of a word (IRT formulation).** For a judgment predicate over a latent severity axis (generate units spanning the axis: pristine → uninhabitable sanitation), each defensible reading `r_j` induces a cutoff `b_j` on the axis. Then:

- **looseness(predicate)** = dispersion of `{b_j}` across the reading ensemble — the width of the borderline band. A thin predicate has zero width (every reader cuts at Jan 1, 2020); "adequate" has a band.
- **discretion exposure of a case** = its probability mass inside the band under the case distribution — discretion in population units: *what fraction of real units live in the band where the word doesn't decide.*

This is item response theory with readings as raters and cases as items, and it operationalizes open texture (Hart; Endicott's *Vagueness in Law*) as a measurable borderline-region mass. A byproduct worth having on its own: a **looseness lexicon** of recurring regulatory terms ("adequate", "reasonable", "good repair", "to the satisfaction of the official"), each with a measured band width — a drafting tool that flags high-looseness terms in bills and prices the alternatives.

**Two protocols, two questions.** "Synthetic outputs" can mean two different things and they must not be mixed:

- **Reading-ensemble protocol** — no output is truth; the *distribution over defensible readings* is the object. Yields looseness and band mass. (An LLM ensemble may not span human readings; the city checklists are real human readings — the ensemble must cover them, and permit records later allow *revealed-reading estimation*: infer a city's operative cutoff from its decisions.)
- **Planted-reading protocol** — we fix a reading (a specific threshold function), generate (case, decision) pairs from it, and ask whether a coded system / a model can recover it. Answers "can code capture this?" with a known answer, on a ladder of constructed worlds: threshold world (code must succeed) → conjunction/exception world (code succeeds at larger L) → gestalt world (code fails by construction). The instrument is validated on the ladder before it is pointed at a real statute — the planted-kill-switch discipline, now the main axis. It also measures *identifiability*: whether a reading is recoverable from decisions at all, which bounds what revealed-reading estimation can ever get from permit data.

**What the reconstruction objective tells us**, concretely: (1) where discretion lives, per word, in population mass; (2) whether the discretion residual is *codable-in-practice* — if a fitted threshold captures most of the reading distribution's band, an "objective standards" rewrite is cheap and its cost is exactly the band cases it flips, named and counted (the harm term of the simplification loop); (3) failure localization across extractor/predicate/executor; (4) identifiability limits for inferring operative rules from outcome data.

**Three-layer scaling architecture (via LegalDiscourse).** The looseness instrument is expensive per predicate; Spangher et al.'s *LegalDiscourse* schema (NAACL 2024; SUBJECT/OBJECT/PROBE/CONSEQUENCE/TEST/EXCEPTION/DEFINITION/CLASS spans + 21 relations; trained taggers + ~100K scraped state laws) supplies the cheap segmentation layer above it: (1) tag discourse components at scale — TESTs are the dominant unit (28% of spans, 91% of documents); (2) score each TEST/EXCEPTION/DEFINITION span with a **static looseness screener** — linguistic typology (relative vs. absolute gradable adjectives per Kennedy 2007; multidimensional adjectives per Sassoon; explicit delegation markers "in the opinion of/to the satisfaction of" as a distinct assigned-discretion mechanism) plus LLM-rated priors, treated as hypotheses per the retraction lesson; (3) calibrate the screener against the synthetic instrument on a subsample, propagate uncertainty, apply nationally. Discourse role routes the *consequence type* of looseness: TEST → outcome discretion; EXCEPTION → discretion at the carve-out boundary; DEFINITION → a multiplier propagating through every TEST that references the defined CLASS (measurable on the relation graph); CONSEQUENCE ("reasonable conditions") → remedy discretion; scoping spans → coverage discretion. Precedent for word-level vagueness annotation: Lebanoff & Liu, EMNLP 2018 (privacy policies) — ratings-based, not consequence-based; the calibration step is what upgrades ratings to measurements.

**The validity assumption that replaces judge-trust is synthetic realism.** Latent marginals must be calibrated to real data (assessor/ACS/permit records), rendered observables validated against real inspection reports, and the external anchors of §4 (checklist divergence, later real decisions) remain the court of appeal.

## 7. Imposed thinness — over-formalization by coded artifacts (Alex, 2026-09-03)

New metric: **how often coded decisions enforce more thinness than the statute warrants.** Every coded artifact (city checklist, agency screener, OpenFisca variable, prior-auth criteria) must resolve the statute's judgment predicates into something executable — and each resolution is a choice the legislature declined to make. Measure it by diffing an *honestly typed* parse of the statute (judgment stays judgment) against the coded artifact:

- **Imposed-thinness rate** = fraction of statute-judgment predicates that the artifact renders as hard objective rules. (Prompt 10's `as_written` field on checklist items was built for exactly this.)
- **Band placement** = where the artifact's chosen cutoff falls relative to the reader-ensemble band for that predicate. *Inside* the band → a defensible resolution of licensed discretion; *outside* the band → the code has not resolved the law, it has **rewritten** it. That's the sharp version of the metric: unauthorized-rewrite rate.
- The reverse (**retained thickness**: code keeping human review where the statute is mechanical) is measured the same way and expected to be rarer.

Kaplow reading: the coder pays the ex ante specification cost the legislature deliberately deferred — a silent shift of the rules-vs-standards choice from lawmaker to implementer. Our smoke test's planted compiler bug (vB inventing "toilet AND hot water" for "adequate sanitation") is this phenomenon in miniature; SOLAR's frozen ontology and every rules-as-code parameter standing in for "reasonable" are it at scale, unmeasured. High-stakes wild instance: commercial utilization-review criteria (InterQual/MCG) thinning the legal standard of "medical necessity" — coded artifacts, statutory standard, dispute data exists.

## 8. Theoretical grounding & honest limits of the codification-space idea (2026-09-04)

The "score all valid codifications" idea has a name in philosophy: **supervaluationism** (Fine 1975). A vague predicate admits many *admissible precisifications*; a claim is determinately true iff true under all of them; the borderline region is where admissible precisifications disagree. Our band IS this structure operationalized. Three consequences:

1. **Degeneracy is real but harmless once quotiented.** The space of syntactic codifications is infinite ("2 toilets", "3 toilets", …), so never count codifications. Two moves tame it: (a) **admissibility** — a codification must reproduce the clear-case extension ("3 toilets" flunks every ordinary clean one-toilet house → inadmissible); (b) **behavioral quotient** — codifications differing only on measure-zero (or population-rare) cases are the same point in the quotient; the measured object is the *union of disagreement regions of admissible codifications, weighted by population*, which is bounded even when the codification set is infinite.
2. **The two real vulnerabilities** (state in any paper): admissibility is itself judged — we ground it behaviorally (clear-case verdicts, human artifacts like checklists), not by LLM opinion, but the regress is genuine and human anchors are load-bearing; and the space is searched, not enumerated — bands and disagreement masses are **lower bounds** (bounded-search evidence, the metric-seam lesson: non-codability is only negatively boundable). Adversarial generation (CUTECat-style) is the search engine.
3. **Kripkenstein is real but proves too much.** The rule-following paradox applies to "before Jan 1, 2020" as much as to "adequate" — yet practice coordinates on dates and splinters on "adequate." We don't solve the paradox; we *measure how well practice coordinates*, which is all the law ever had. The paradox's one operational bite: no finite test suite certifies two codifications equivalent — all equivalence claims are distribution-relative. Keep them so.

**Normative stance (anti-"vague = bad")**: discretion is a priced dimension, not a defect — it buys adaptability and case-equity and costs predictability and horizontal inequity; the instrument prices both sides so the rules-vs-standards trade can be made per provision. Ho's NY/SD result is the cautionary tale in both directions: SD's thin scoring degenerated into universal A's (thinness gamed), while NY's finer-grained points showed "little substantive consistency" across inspections — *apparent* thinness with high inter-inspector variance is **discretion wearing a rule costume**. Effective thinness is behavioral, never textual.

## 9. What is a node? The three-layer doctrine (2026-09-04)

There is no single privileged node. Three granularities serve three measurements, with the maps between them treated as data:

1. **Logical nodes** — minimal testable propositions, span-pinned (schema-v3 atoms). Text-determined. Serves discretion (per-proposition bands) and logic metrics.
2. **Evaluation nodes** — what one assessor judges in one act (Dan: "subconditions collapse… conducted in one evaluation"). Practice-determined, NOT text-determined. Serves consistency/error measurement (Mendling metrics apply here — humans err at the level they process). Schema implication: an **assessment map** `{act, actor, occasion}` grouping atoms, the decision-side twin of `acquisition` on inputs.
3. **Process nodes** — actor/occasion/handoff/rework units. Practice-determined. Serves burden and delay.

"Size" splits accordingly: logical size (what the law contains) vs. evaluative size (what a human must process) — Dan's "principled size" is plausibly the latter.

**Method consequence**: layers 2–3 are measured from artifacts, not parsed from text. Inspection forms/checklists ARE evaluation-layer documents (SD's 48 lines = San Diego's chunking of CalCode into one visit; NYC's 68 items = a different chunking of the same logical content; smart-answers question flows = the UK's chunking into askable units) — so statute→form alignment doubles as the observed collapse function. Joyce's rounds data gives revealed co-assessment; Ho's peer-review RCT (item-level disagreement, 60% on identical conditions) lets us test whether finer chunking buys consistency (his NY result suggests not necessarily). LLM-parsed groupings are hypotheses; artifact-practiced groupings are measurements; their divergence is a finding.

## 10a. Correction: El Cerrito, and the one-hop extraction rule (2026-09-10)

The page-only extraction gave El Cerrito a 2-activity declared process (coverage 0.33). Following the program page's own links one hop — the AB 2533 checklist PDF (a signed form: owner / licensed contractor / city building inspector, plus blank lines for field-identified violations) and the generic Building Permits page (eTRAKiT intake, application form, plan-submittal checklist, Planning consultation for ADUs) — yields 9 activities, 6 actors, 6 handoffs, 2 rework loops, coverage 0.89: the largest declared process of the four. Two consequences:

1. **Extraction rule**: a declared process = the program page PLUS every document it links one hop away (forms, checklists, the generic permit page). Page-only extraction systematically under-counts cities that reuse generic machinery.
2. **The confidentiality finding sharpened**: El Cerrito's form makes the licensed contractor a signatory on a document the city receives — the statute's *confidential* third-party inspection is not merely unmentioned but structurally not preserved. "Absent from the page" and "absent from the process" are different claims; this is the second.

## 10. Lessons from the Hayward records pull (2026-09-10)

1. **The "designed" tier can be empty at the legislative level.** Hayward's AB 2533 program has no council staff report, resolution, ordinance, or fee-schedule line (2,108 Legistar matters 2023–2026 and four adopted fee schedules checked). It is an administrative Building Division program; its only design documents are handouts, a questionnaire, and the webpage. So "designed process" must be sourced from administrative artifacts, and its absence from the legislative record is itself a datum (fee authority undocumented; Certificate of Compliance has no code basis).
2. **Implementations are not independent samples.** Hayward's program pre-dated AB 2533 (Jan 2024, $590, Certificate of Compliance already existed) and was retrofitted to the statute in 2025; its questionnaire still cites *Berkeley* Municipal Code § 19.40.040 — it was adapted from Berkeley's program. El Cerrito cloned Lafayette's page. Cross-city "readings" therefore have **template-lineage cluster structure**; divergence statistics must account for it (n cities ≠ n independent draws), and lineage itself becomes a measurable object (which city copied whom).
3. **State law was absorbed into existing local machinery, observably**: the retrofit consisted of light edits (fee $590→$570, add statute cite, add § 17920.3 checklist, add third-party option). Confirms the mechanism behind process discretion: silence in the statute is filled by whatever process already exists.
4. **Process models have a time dimension.** Wayback diffs (Feb 2025 vs Dec 2025) give process change over time; versioning belongs in the schema.
5. Richer artifacts → richer model: handouts+questionnaire yield 16 activities / 11 actors (Code Enforcement, Permit Services Center, Alameda County Assessor for JADU deed restrictions, post-issuance enforcement, a 5-year code-enforcement delay path) vs. 6 steps from the webpage alone — the information-tier gradient measured on one city.

## 10. Relation to the metric-seam work

(`../norm-research/methods/metric_seam`; spec at `../norm-research/notes/2026-07-01__metric-seam-proposal.md`.) Inherited: the two-axis complexity picture (description length vs. irreducible residual, the κ_e(L) profile shape), the retraction lesson, planted controls, and the Kaplow tiebreak. **Not** inherited: the frozen-LLM-reference as anchor (replaced by execution + invariants + implementer artifacts) and the frozen linear aggregator (the tree's compositional structure is here the object of study). Predicate-level codability questions ("could this judgment predicate be given a gate-passing objective proxy, and at what fidelity?") remain available as a *second-stage* analysis on the discretion residual — that is where the seam machinery proper re-enters, pointed at the predicates the divergence measure has already flagged.
