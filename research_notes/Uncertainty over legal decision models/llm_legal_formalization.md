# LLM-based legal formalization, rules-as-code, statutory reasoning, and uncertainty over formalizations

*How citations were checked (2026-10-05).* Every entry below was checked against a primary or repository record. The tags mean:
- **[arXiv]**: title, authors, date and abstract taken from the arXiv API record (export.arxiv.org). Venue claims come from the authors' own arXiv comment or journal-ref field.
- **[arXiv-HTML]**: specific numbers or quotes taken from the arXiv full-text HTML through a fetch-and-summarize tool. These are correct in substance, but a number could have been garbled in summarization, so re-check against the PDF before quoting it.
- **[DOI]**: title, authors and venue confirmed from Crossref or Semantic Scholar metadata for the DOI. The publisher page itself was not fetched, because ACM DL returned 403 and Springer redirected to a login.
- **[GitHub]**: repository metadata from the GitHub API.
- **[PARTIAL]**: found only as a bibliographic-database record with no DOI or abstract.

The session's WebSearch budget was used up before this task began. All discovery therefore went through the arXiv API, Crossref, OpenAlex, Semantic Scholar, the GitHub API and direct page fetches. Expect lower recall for law-review and non-arXiv venues.

## Q1. Statutory reasoning benchmarks (SARA and follow-ups, Blair-Stanek et al., LegalBench): what do they show about LLM reliability?

### Takeaway
The JHU line of work (SARA, 2020 onward) shows the same thing every time. End-to-end LLMs are unreliable on statutory reasoning: they do poorly on synthetic statutes they cannot have memorized, they give unstable answers to identical prompts, and their scores can be inflated by data contamination. Hand-written or verified Prolog encodings, by contrast, solve the tasks. As a result the field has moved toward "LLM translates, solver executes" pipelines (DeonticBench, Jurayj et al., Law&Order, OpenExempt). Even in those pipelines the formalization step is the bottleneck: hard-subset accuracy is 44–47% on DeonticBench, and an unaided LLM gets 66% on tax forms.

### Cited Findings
- **SARA (StAtutory Reasoning Assessment).** Holzenberger, Blair-Stanek & Van Durme (2020) frame statutory reasoning as applying natural-language statutes to natural-language case facts. They note that "much of the information needed for deciding a case is declared exactly once (a law)." Machine-reading models score low out of the box, whether or not they are fine-tuned on legal text. A "hand-constructed Prolog-based system" was "designed to fully solve the task." [arXiv] — [arXiv:2005.05257](https://arxiv.org/abs/2005.05257)
- **SARA v2 decomposition.** Holzenberger & Van Durme (ACL 2021) note that the original resource treated statutory reasoning "as a monolithic textual entailment problem, with neural baselines performing nearly at-chance." They break it into four language-understanding subtasks "through the introduction of concepts and structure found in Prolog programs," and this added structure improves models. [arXiv] — [arXiv:2105.07903](https://arxiv.org/abs/2105.07903)
- **GPT-3 on SARA.** Blair-Stanek, Holzenberger & Van Durme (2023) found that text-davinci-003 beat the previous best published SARA results but made clear errors and had "imperfect prior knowledge of the actual U.S. statutes." On "simple synthetic statutes, which GPT-3 is guaranteed not to have seen," it "performs poorly." [arXiv] — [arXiv:2302.06100](https://arxiv.org/abs/2302.06100)
- **GPT-4 and tax.** The same authors (Tax Notes Federal 180:1101, Aug 2023) report that the GPT-4 livestream tax example came from their dataset, that GPT-4 got the wrong answer, and that it "fails to reliably calculate taxes." [arXiv] — [arXiv:2309.09992](https://arxiv.org/abs/2309.09992)
- **BLT benchmark.** Blair-Stanek et al. (2023) find that GPT-4 and Claude "perform poorly on basic legal text handling," such as looking up a line in a deposition or a subsection of a contract. Fine-tuning brings even a small model to near-perfect performance. [arXiv] — [arXiv:2311.09693](https://arxiv.org/abs/2311.09693)
- **Instability.** Blair-Stanek & Van Durme (2025) built a dataset of 500 hard two-party legal questions distilled from real cases. At temperature 0, gpt-4o, claude-3.5 and gemini-1.5 "sometimes say one party should win, while other times saying the other party should win." [arXiv] — [arXiv:2502.05196](https://arxiv.org/abs/2502.05196)
  - Full text: each question was asked 20 times. Share of questions with inconsistent answers: Claude-3.5 10.6%, GPT-4o 43.0%, Gemini-1.5 50.4%. o1 (temperature fixed at 1) was unstable on 28% of a 50-question subset. Between-model correlations of instability were only 0.123–0.181, which the authors read as instability being "idiosyncratic and specific to that model." [arXiv-HTML] — [arXiv:2502.05196 HTML](https://arxiv.org/html/2502.05196v1)
- **Tax-abuse discovery.** Blair-Stanek, Holzenberger & Van Durme (2025) test whether LLMs can discover and analyze U.S. tax-minimization strategies. [arXiv] — [arXiv:2508.20097](https://arxiv.org/abs/2508.20097)
- **SARA as analogy.** Zou et al. (2024) recast SARA as analogical reasoning, which makes the dataset about 100 times larger. The analogy task is "roughly as difficult" for NLP models as the original. [arXiv] — [arXiv:2401.06715](https://arxiv.org/abs/2401.06715)
- **LLMs plus logic programs for tax (AAAI 2026).** Jurayj, Holzenberger & Van Durme combine LLMs with a symbolic solver on SARA. They add a cost model based on real IRS penalties and show that "up-front translation of plain-text rules into formal logic programs," together with retrieved exemplars for case representations, "can dramatically improve performance" and push costs "well below real-world averages." [arXiv] — [arXiv:2508.21051](https://arxiv.org/abs/2508.21051)
  - Full text: the system treats agreement as an abstention rule ("an answer is only accepted if it is reached via two independent reasoning processes"). A program that fails to execute or exceeds 10 s counts as a refusal. Refusals are charged $270 (the IRS average filing cost); errors are charged a 20% substantial-understatement penalty. [arXiv-HTML] — [arXiv:2508.21051 HTML](https://arxiv.org/html/2508.21051v3)
- **DeonticBench (2026).** Dou et al. built 6,232 tasks covering U.S. federal tax, airline baggage policy, U.S. immigration administration and U.S. state housing law, with reference Prolog programs for every instance. The best hard-subset results are "only 44.4% on SARA Numeric and 46.6 macro-F1 on Housing." SFT and RL improve Prolog generation, but "current RL methods still fail to solve these tasks reliably." [arXiv] — [arXiv:2604.04443](https://arxiv.org/abs/2604.04443)
- **OpenExempt (2026).** Servantez, Lawsky, Jain, Linna & Hammond generate tasks dynamically from "expert-crafted symbolic representations of U.S. Bankruptcy Code statutes," yielding 9,765 samples across nine suites. Across 13 models they find "sharp performance cliffs that emerge only under longer reasoning paths and in the presence of obfuscating statements." [arXiv] — [arXiv:2601.13183](https://arxiv.org/abs/2601.13183)
- **Contamination (2026).** Kordjamshidi et al. show that tax-law reasoning "performance can be inflated by contamination." Hybrid systems that translate statutes into formal representations generalize better to unseen case and rule variations. [arXiv] — [arXiv:2605.16052](https://arxiv.org/abs/2605.16052)
- **Law&Order tax autoformalization (2026).** Han, Takashima, Wei, Li & Genesereth formalize tax forms and instructions into executable programs. They use LLM synthesis plus cell-level verification and localized repair, checked against human-written OpenTaxSolver returns. On held-out TaxCalcBench returns, "the most advanced LLM achieves only 66% accuracy," while Law&Order reaches 100% cell- and form-level accuracy on 51 returns. [arXiv] — [arXiv:2610.02792](https://arxiv.org/abs/2610.02792)
- **LLMs as tax attorneys.** Nay, Karamardian, Lawsky, … Choi, Kasai (2023) find capability improving with each OpenAI release. Retrieval and few-shot prompting help GPT-4, which reaches "high levels of accuracy but not yet at expert tax lawyer levels." [arXiv] — [arXiv:2306.07075](https://arxiv.org/abs/2306.07075)
- **LegalBench.** Guha, Nyarko, Ho, Ré, et al. (2023) assembled 162 tasks covering six types of legal reasoning, hand-crafted by legal professionals, and evaluated 20 LLMs. A 2022 short paper prototyped the collaborative design. [arXiv] — [arXiv:2308.11462](https://arxiv.org/abs/2308.11462); [arXiv:2209.06120](https://arxiv.org/abs/2209.06120)
- **Defeasible scope parsing (2026).** NormBench (Chen et al.) has 2,290 provisions in Chinese, English (U.S. tax, GDPR, corporate policies) and cross-lingual settings. It names "Silent Scope Omission," where a model applies a general rule but drops nested exceptions. It also reports "Recursion Decay," with performance falling sharply as defeater depth grows, and an "Auditability Trap," where models retrieve the right spans but assemble the wrong control flow. [arXiv] — [arXiv:2606.08932](https://arxiv.org/abs/2606.08932)
- **Hierarchical legal reasoning.** Zhang, Grabmair, Gray & Ashley (CSLAW 2026) find accuracy falls from 64.82–92.09% on hierarchical reasoning to 11.46–33.99% on integrated analysis. Models "consistently expend more computational resources on incorrect responses than correct ones." [arXiv] — [arXiv:2510.08710](https://arxiv.org/abs/2510.08710)
- **Sensitivity to irrelevant changes.** Chen et al. (2026) find that existing legal LLMs are "systematically sensitive to legally irrelevant variations." They argue that legal trustworthiness requires "calibrated sensitivity to legally material changes." [arXiv] — [arXiv:2605.26530](https://arxiv.org/abs/2605.26530)

### Inferences
- Across SARA, DeonticBench, OpenExempt and Law&Order, accuracy improves when an LLM writes a formal program, but formalization errors then dominate the error budget. For a latent-decision-model project, the formalization step is therefore where uncertainty has to be modeled.
- The instability results (10–50% of questions flip under identical prompts, with low cross-model correlation) suggest that per-model sampling variance and between-model disagreement are separate sources of noise. A model should treat them separately rather than pool all samples.
- Recursion Decay (NormBench) and the cliffs under longer reasoning paths (OpenExempt) suggest that formalization reliability falls with exception depth. Exception-heavy provisions such as ADU and solar permitting rules should get wider priors.

### Gaps
- Not checked: the Holzenberger 2023 NLLP paper connecting symbolic statutory reasoning to information extraction, COLIEE statute-entailment ensemble results, and Chinese benchmarks (LawBench appeared only incidentally, as EMNLP 2024 in [DOI](https://doi.org/10.18653/v1/2024.emnlp-main.452)).
- The final venue of "Can GPT-3 Perform Statutory Reasoning?" (reportedly ICAIL 2023) was not confirmed. Only the arXiv record was.

## Q2. LLM legal formalization (Janatian, Nguyen, Graus, Dal Pont; Prolog/ASP/Catala/L4/KG targets; neurosymbolic methods; Chain of Logic)

### Takeaway
Since 2023, LLMs have been used to produce JusticeBot pathways, Prolog and PROLEG, Logical English, defeasible deontic logic, Pythen condition–exception rule trees, SMT/Z3 constraints, Catala-like calculi and Dutch production decision models. Reported quality is moderate:
- about 60% of JusticeBot pathways rated equivalent or better than manual ones;
- 51–53% of test scenarios matched by Graus's generated decision models;
- 55–75% of traffic rules correctly formalized in Prolog.

Two 2026 results matter most for this project. Graus (ICAIL 2026) and Vernie & Grabmair (EMNLP 2026) independently find that structural similarity does not predict behavioral (outcome) equivalence. And human-verification studies trace failures mainly to abstraction and interpretive choices rather than to logic errors.

### Cited Findings
**Primary comparison paper**
- **Vernie & Grabmair (2026), "By Their Fruits You Will Know Them" (accepted at "EMNLP PROC 2026" per the arXiv comment).** Their method:
  - match multiple formalizations of one provision at the node level;
  - derive a shared interface for each pair;
  - use a SAT solver to enumerate the edge cases where any two disagree;
  - verbalize those cases into scenarios for experts.
  Applied to ten EU provisions formalized by nine frontier LLMs, "behavioral divergence between formalizations is essentially uncorrelated with their structural agreement." Some divergences "mirror genuine controversies in the legal commentary." [arXiv] — [arXiv:2605.25186](https://arxiv.org/abs/2605.25186)
  - Full text:
    - **Representation.** Rooted, labeled Boolean trees using AND/OR/NAND/NOR; leaves are assessable facts or concepts.
    - **Provisions.** GDPR Arts. 6, 9, 17 and 22; UCTD Art. 3; UCPD Arts. 6–7; DMA Art. 3; AI Act Art. 5; Procurement Directive Art. 57; TFEU Art. 107.
    - **Models.** Claude Opus 4.6, GPT-5.4, Gemini 3.1 Pro, DeepSeek-V3.2, Qwen 3.5, Kimi K2.5, Mistral Large 3, MiniMax M2.7 and GLM-5.1.
    - **Equivalence rate.** For pairs with coverage ≥0.4, "the equivalence rate flattens near 50%." Even at the highest coverage only 42% of pairs are logically equivalent.
    - **Structure vs. behavior.** Rank correlation between coverage and edge-case count is ρ = +0.09.
    - **Disagreement types.** (i) Genuine controversy: the models split 4–4 on whether law-enforcement biometric categorization falls under AI Act Art. 5. (ii) Encoding errors: one model treated a procedural burden-of-proof rule in UCTD Art. 3 as a substantive condition. (iii) Operator-level structural divergence with no outcome difference.
    - **No aggregation.** The paper proposes no probabilistic, Bayesian or majority-vote aggregation; the method "needs no reference encoding."
    [arXiv-HTML] — [arXiv:2605.25186 HTML](https://arxiv.org/html/2605.25186v2)

**Decision-model and pathway generation**
- **Janatian, Westermann, Tan, Savelka & Benyekhlef (JURIX 2023).** GPT-4 extracted JusticeBot-style decision pathways from legislation. In a blind comparison, "60% of generated pathways [were] rated as equivalent or better than manually created ones." [arXiv] — [arXiv:2311.04911](https://arxiv.org/abs/2311.04911)
- **Graus (ICAIL 2026).** Uses 95 production decision models paired with legal text from the Dutch Environment and Planning Act; these power the Omgevingsloket permit-check platform.
  - Adding I/O constraints to the input raised structural similarity by 37–54% over baseline. Semantic role labels helped only modestly.
  - Generated models "match the gold standard on 51-53% of test scenarios."
  - LLMs remove redundant pass-through logic that makes up 45–55% of nodes.
  - "structural similarity does not guarantee outcome equivalence, and vice versa."
  [arXiv] — [arXiv:2604.17153](https://arxiv.org/abs/2604.17153)
- **Lopez et al. (IBM, 2022).** Position paper on semi-automatically building "executable, interpretable and standardised decision models" from social-services eligibility policies, using NLP and knowledge graphs. [arXiv] — [arXiv:2212.06882](https://arxiv.org/abs/2212.06882)
- **Toles et al. (2025), BeNYfits.** A benchmark for interactive eligibility across overlapping social benefits. GPT-4o with ReAct scores 35.7 F1. ProADA, which maps dialog planning to program synthesis, reaches 55.6 F1. [arXiv] — [arXiv:2502.19610](https://arxiv.org/abs/2502.19610)
- **Kim et al. (CIKM 2026), Code-as-Auditor.** Translates regulations into "formalized checklists and executable decision trees" with a self-verification loop, applied to privacy and data-protection compliance. [arXiv] — [arXiv:2609.19199](https://arxiv.org/abs/2609.19199)

**GDPR and PROLEG / Pythen line (JAIST / Satoh group)**
- **Nguyen, Fungwacharakorn, Wehnert, Zin, Kong, Xue, Araszkiewicz, Goebel & Satoh (ICAIL 2026).** Multi-agent LLM generation of legal scenarios, formal rules and atomic facts, followed by verifier modules and human review. They conclude that "structured verification and targeted human oversight are essential." [arXiv] — [arXiv:2604.14607](https://arxiv.org/abs/2604.14607)
  - Full text:
    - **Representation.** Rules are Pythen condition–exception "rule trees" in JSON (keys `conditions` and `exceptions`, using negation-as-failure).
    - **Verification.** Four verifier agents score each sample 0–100 and the mean is used. 400 samples passed the ≥70 threshold and 120 went to human review.
    - **Failures** "arise primarily from abstraction choices rather than logical errors": controller-agnostic modeling, procedural–substantive conflation and fact-extraction misalignment.
    - **No agreement statistics.** No inter-annotator or inter-agent agreement was computed.
    [arXiv-HTML] — [arXiv:2604.14607 HTML](https://arxiv.org/html/2604.14607v2)
  - Vernie & Grabmair cite this paper as "Nguyen et al. (2026)." It appears to be the "condition-exception rule trees" paper named in the brief.
- **Zin et al. (2026), "Can Legislation Be Made Machine-Readable in PROLEG?"** A single prompt compiles GDPR Art. 6 into if-then rules and PROLEG. Legal experts validate and refine the result. [arXiv] — [arXiv:2601.01477](https://arxiv.org/abs/2601.01477)
- **Nguyen & Satoh (2026), PYTHEN.** A Python framework for defeasible legal reasoning. [arXiv] — [arXiv:2603.15317](https://arxiv.org/abs/2603.15317)
- **KRAG (2024).** Knowledge-representation-augmented generation. [arXiv] — [arXiv:2410.07551](https://arxiv.org/abs/2410.07551)
- **"Beyond Logic Programming for Legal Reasoning" (2023).** Position paper. [arXiv] — [arXiv:2306.16632](https://arxiv.org/abs/2306.16632)
- **Xue et al. (ICAIL 2026), Legal2LogicICL.** Diverse few-shot retrieval for case-to-PROLEG translation, with a new Legal2Proleg dataset. They report improved "accuracy, stability, and generalization." [arXiv] — [arXiv:2604.11699](https://arxiv.org/abs/2604.11699)

**Prolog, Logical English, defeasible deontic logic and ASP targets**
- **Dal Pont, Sartor, Wyner & Sartor (ICAIL 2025), "You Take the High Road, and I'll Take the Low Road."** Uses LLMs, prompt engineering and Logical English to translate UK Highway Code rules into executable rules for autonomous vehicles. An error-correction phase "improves rule accuracy," and the rules are validated in simulation. [DOI] — [doi:10.1145/3769126.3769254](https://doi.org/10.1145/3769126.3769254)
- **Sartor, Wyner & Contissa (2025).** Logical English, Prolog and multi-agent systems for Highway Code junction rules. [arXiv] — [arXiv:2502.09216](https://arxiv.org/abs/2502.09216)
- **Zin, Fungwacharakorn, Satoh & Nitta (NLL2FR 2025).** On 20 traffic rules, a structured four-stage prompt correctly formalized 75% in Prolog, against 60% for direct NL→Prolog and 55% for Logical English→Prolog. [arXiv] — [arXiv:2609.20334](https://arxiv.org/abs/2609.20334)
- **Horner, Mateis, Governatori & Ciabattoni (2025).** LLM formalization into defeasible deontic logic (DDL) on the Australian Telecommunications Consumer Protections Code. Uses a two-stage pipeline with a refinement step. "When guided effectively, LLMs can produce formalizations that align closely with expert-crafted representations." [arXiv] — [arXiv:2506.08899](https://arxiv.org/abs/2506.08899)
- **Sehgal & Liu (ICLP 2024 / EPTCS 416), LogicLease.** LLM fact extraction plus Prolog reasoning for New York landlord–tenant law. The authors report 100% accuracy on their own tests. [arXiv] — [arXiv:2502.09204](https://arxiv.org/abs/2502.09204)
- **Kant et al. (2024).** GPT-4o "fails to encode a simple health insurance contract into logical code," but o1-preview succeeds. [arXiv] — [arXiv:2410.09904](https://arxiv.org/abs/2410.09904)
- **Kant et al. (2025).** Compares a vanilla LLM, unguided LLM encoding of contract and claim, and guided encoding. The guided LLM+logic approach is the promising one. LLMs "still lack the accuracy and consistency required." [arXiv] — [arXiv:2502.17638](https://arxiv.org/abs/2502.17638)
- **Bao et al. (2026), NAFBench.** Shows that negation semantics (SLDNF, well-founded, credulous or skeptical stable-model) is itself an interpretive choice. The strongest open models reach 59–74% across viewpoints. All models are order-sensitive on more than half of logically identical rule shufflings. [arXiv] — [arXiv:2609.27517](https://arxiv.org/abs/2609.27517)

**SMT, Z3 and Catala-like neurosymbolic pipelines**
- **Chen, Cai, Hou & Dong (2025), L4L.** LLMs autoformalize statutes into SMT constraints validated by case-level tests. Prosecutor and defense agents extract arguments, and the solver adjudicates them. [arXiv] — [arXiv:2511.21033](https://arxiv.org/abs/2511.21033)
- **LexGuard (2026).** A follow-up from the same group. [arXiv] — [arXiv:2605.26530](https://arxiv.org/abs/2605.26530)
- **Wang et al. (2026), "Know Your Limits" (ICML AI4Law/AI4Math workshops).** On re-annotated ContractNLI, "a substantial proportion of legally sound inferences are not formally grounded without additional unstated assumptions." Failure modes:
  - "scope laundering": solver-inconsistent conclusions presented as if formally derived;
  - implicit-constraint blindness;
  - Z3 synthesis errors.
  [arXiv] — [arXiv:2606.16118](https://arxiv.org/abs/2606.16118)
- **Heydari & Leowald (2026).** LLM autoformalization into "a formal legal calculus extending Catala" with a verification kernel, proposed as an RL reward signal. [arXiv] — [arXiv:2606.23913](https://arxiv.org/abs/2606.23913)
- **Hsia, Yu & Jiang (2026).** LLM plus SMT for financial-regulation compliance. [arXiv] — [arXiv:2601.06181](https://arxiv.org/abs/2601.06181)

**Prompting methods and knowledge graphs**
- **Servantez, Barrow, Hammond & Jain (2024), Chain of Logic.** Inspired by IRAC, the prompt decomposes a compositional rule into elements and then recomposes the logical expression. It beats chain-of-thought and self-ask on eight LegalBench rule tasks. [arXiv] — [arXiv:2402.10400](https://arxiv.org/abs/2402.10400)
- **de Martim (2025), SAT-Graph RAG.** An ontology-driven, temporal knowledge graph of legal norms for retrieval. [arXiv] — [arXiv:2505.00039](https://arxiv.org/abs/2505.00039)

### Inferences
- **The same error appears independently in two studies.** Vernie & Grabmair's UCTD encoding error (a procedural burden-of-proof rule treated as a substantive condition) matches Nguyen et al.'s "procedural-substantive conflation." This is apparently a recurring LLM formalization error and could be given its own error-type prior.
- **Behavior should define the target.** Graus (structure and outcome are "complementary") and Vernie & Grabmair (ρ ≈ 0.09) agree. A posterior over latent decision models should be defined over decision functions, meaning behavior on the fact space, rather than over tree topology. Structural metrics such as graph kernels or node matching are poor proxies for equivalence.
- **Constraining the interface helps.** Graus's I/O constraints (+37–54% similarity) and Vernie's shared-interface derivation both suggest that fixing the predicate vocabulary up front makes formalizations comparable and reduces spurious disagreement. This parallels the human finding in Q3 that agreeing on "atoms" first increases coder agreement.

### Gaps
- The "L4" route (smucclaw/Legalese) has repositories (see Q3) but no LLM-to-L4 evaluation paper turned up.
- No LLM-to-Catala evaluation was found except the Heydari & Leowald architecture paper.
- Logical English foundational papers (Kowalski et al.) were not checked.

## Q3. Rules-as-code projects and tools (Catala, L4, Blawx, OpenFisca, PolicyEngine) and their documented limitations

### Takeaway
Rules-as-code (RaC) tools are mature and open source: Catala (with a proven-correct compiler core), OpenFisca, PolicyEngine, Blawx (s(CASP)) and L4. The empirical record shows two things about them. Encoding forces explicit interpretive choices, and formal analysis exposes ambiguities in the source law. Catala found a bug in an official French benefits implementation and date ambiguities in the housing-benefit code. Independent coders of the same statute diverge unless they first agree on key terms, and some indeterminacy, such as factual indeterminacy, cannot be fixed in advance.

### Cited Findings
- **Catala (2021).** Merigoux, Chataing & Protzenko present a DSL for "a straightforward and systematic translation of statutory law into an executable implementation." The core compilation steps are proven correct in F*. Evaluated on U.S. IRC §121 and French family benefits, it "uncover[ed] a bug in the official implementation." [arXiv] — [arXiv:2103.03198](https://arxiv.org/abs/2103.03198)
  - Repository: "Programming language for literate programming law specification," created 2020. [GitHub] — [CatalaLang/catala](https://github.com/CatalaLang/catala)
- **Catala in AI and Law (2022).** Huttner & Merigoux, "Catala: Moving towards the future of legal expert systems." [DOI] — [doi:10.1007/s10506-022-09328-5](https://doi.org/10.1007/s10506-022-09328-5)
- **Date arithmetic ambiguity (2024).** Monat, Fromherz & Merigoux give formal semantics for date arithmetic and a static analysis by abstract interpretation that "automatically detect[s] ambiguities." Run on the Catala French housing-benefits code, it led to "the discovery of several date-related ambiguities." [arXiv] — [arXiv:2403.08935](https://arxiv.org/abs/2403.08935)
- **CUTECat (2024).** Concolic testing for Catala programs that handles default logic, the base-case-plus-exceptions pattern. It generates "hundreds of thousands of testcases covering all branches" of French housing benefits and U.S. tax §132. [arXiv] — [arXiv:2410.18212](https://arxiv.org/abs/2410.18212)
- **Lawsky on formalization.**
  - "Formalizing the Code" (2017) studies the problem of "definitional scope," where the Code's structure "leaves unclear to what a term refers." [DOI] — [doi:10.2139/ssrn.2987065](https://doi.org/10.2139/ssrn.2987065)
  - "Coding the Code: Catala and Computationally Accessible Tax Law," SMU Law Review 75(3), 2022. [DOI] — [doi:10.25172/smulr.75.3.4](https://doi.org/10.25172/smulr.75.3.4)
  - "Tax Law and Flexible Formalizations" (2024) argues that LLMs and tax-domain programming languages make "flexible formalizations" of tax law possible and realistic. [DOI] — [doi:10.2139/ssrn.5026598](https://doi.org/10.2139/ssrn.5026598)
- **Blawx and s(CASP).** Morris (ICAIL 2021), "Constraint answer set programming as a tool to improve legislative drafting: a rules as code experiment." [DOI] — [doi:10.1145/3462757.3466084](https://doi.org/10.1145/3462757.3466084)
  - Blawx repository: "A user-friendly web-based tool for Rules as Code," created 2020. [GitHub] — [Lexpedite/blawx](https://github.com/Lexpedite/blawx)
- **L4.** "L4 - rules-as-code - is an open-source programming functional language for legal contracts and legislation/regulation." [GitHub] — [legalese/l4-ide](https://github.com/legalese/l4-ide). An earlier SMU repository is "Domain Specific Languages for Computational Law." [GitHub] — [smucclaw/dsl](https://github.com/smucclaw/dsl)
- **OpenFisca.** "OpenFisca core engine. See other repositories for countries-specific code & data," created 2013. [GitHub] — [openfisca/openfisca-core](https://github.com/openfisca/openfisca-core)
- **PolicyEngine.** "A rules engine of the US tax-benefit system, and microdata generation for microsimulation analysis," created 2021. [GitHub] — [PolicyEngine/policyengine-us](https://github.com/PolicyEngine/policyengine-us)
- **OECD (2020).** Mohun & Roberts, *Cracking the Code* (OECD Working Papers on Public Governance), defines RaC as governments creating "an official version of rules … in a machine-consumable form" and covers its "potential, limitations and implications." [DOI] — [doi:10.1787/3afe6ba5-en](https://doi.org/10.1787/3afe6ba5-en)
- **Human coders diverge (ICAIL 2021).** Witt, Huggins, Governatori & Buckley ran a two-week experiment in which legally trained participants encoded Australian Copyright Act provisions. "Coders collaboratively agreeing on key legal terms, or atoms, before commencing independent coding work can significantly increase the similarity of their encoded rules." Participants nonetheless "made a range of divergent interpretive choices," which the authors attribute to:
  - "the complexity of statutory interpretation";
  - "encoded provisions having varying levels of granularity";
  - "the functionality of our coding language."
  [DOI] — [doi:10.1145/3462757.3466083](https://doi.org/10.1145/3462757.3466083)
- **Same experiment, journal version (AI and Law 2023).** Manual plus automated coding validation "can significantly increase the similarity of encoded rules between coders." Interpretive difficulties remained, including "syntactic ambiguity, and intra- and intertextuality." "Some difficulties cannot be overcome in advance, such as factual indeterminacy." The authors distinguish "technical validation" from "legal alignment." [DOI] — [doi:10.1007/s10506-023-09350-1](https://doi.org/10.1007/s10506-023-09350-1)
- **Follow-up encoding methodology (2025).** Bhuiyan, Governatori & Saqi report a DDL encoding methodology with "a significant improvement over the previous experiment." This is a preprint (Preprints.org). [DOI] — [doi:10.20944/preprints202504.2295.v1](https://doi.org/10.20944/preprints202504.2295.v1)

### Inferences
- Witt et al. is the human counterpart of Vernie & Grabmair. Both find that independent encoders of the same provision diverge. In both, part of the divergence is irreducible legal or factual indeterminacy and part is avoidable vocabulary or granularity mismatch. This supports a model that separates "interpretive mass" (several legally defensible readings) from "encoding error."
- Catala's ambiguity detection and CUTECat's test generation are tools for locating where formalizations diverge. The divergent edge cases are the "scenarios" whose outcomes, for example timing records, could be checked against administrative data.

### Gaps
- No quantitative inter-coder agreement figure (for example, a percentage of identical rules) was taken from the Witt et al. full text, because the publisher pages were blocked.
- The ICFP venue for Catala (2021) was not confirmed from the publisher.
- No published evaluation of OpenFisca or PolicyEngine fidelity against official calculators was found in this pass.

## Q4. Which works measure agreement or divergence across multiple LLM formalizations or samples? Does any put a probability distribution over formalizations or aggregate them in a principled (Bayesian) way?

### Takeaway
In legal settings, agreement is measured but not modeled.
- Vernie & Grabmair compute pairwise SAT-based equivalence.
- Graus computes outcome equivalence against a gold model.
- Blair-Stanek & Van Durme measure answer instability.
- Engel & McAdams treat 100 samples as a distribution of "ordinary meaning."
- Jurayj et al. abstain when two independent reasoning routes disagree.

No legal work found places a posterior over formalizations or aggregates them in a Bayesian way. The closest methodological templates come from outside law:
- LINC: K=10 majority vote over first-order-logic formalizations.
- Li et al. (NeurIPS 2024): clustering autoformalizations by symbolic equivalence.
- Sharma & David (2025): semantic entropy with symbolic-execution equivalence classes for code.
- Wong et al. (2023): LLM translation into probabilistic programs with Bayesian inference.
- Panossian (2026): structural uncertainty in autoformalization, where formalizer identity is recoverable from outputs.

### Cited Findings
**Legal: agreement measured but not modeled**
- **Vernie & Grabmair (2026).** Pairwise disagreement enumeration over nine LLMs' formalizations, about 50% non-equivalence, ρ = 0.09 against structure. No probabilistic aggregation (see Q2). [arXiv] — [arXiv:2605.25186](https://arxiv.org/abs/2605.25186); [arXiv-HTML](https://arxiv.org/html/2605.25186v2)
- **Graus (2026).** Outcome equivalence on pre-configured test scenarios, 51–53% match to gold. [arXiv] — [arXiv:2604.17153](https://arxiv.org/abs/2604.17153)
- **Nguyen et al. (2026).** Four verifier agents' scores are averaged. No disagreement statistics. [arXiv-HTML] — [arXiv:2604.14607 HTML](https://arxiv.org/html/2604.14607v2)
- **Jurayj et al. (2026).** Accept an answer only if two independent reasoning processes agree; otherwise refuse, with refusals and errors priced by IRS-penalty costs. [arXiv-HTML] — [arXiv:2508.21051 HTML](https://arxiv.org/html/2508.21051v3)
- **Blair-Stanek & Van Durme (2025).** Repeated-sampling instability of 10.6–50.4% at temperature 0 (see Q1). [arXiv] — [arXiv:2502.05196](https://arxiv.org/abs/2502.05196)
- **Engel & McAdams (2024), "Asking GPT for the Ordinary Meaning of Statutory Terms."** They argue "the most useful evidence for interpretation involves a distribution of replies rather than only what GPT regards as the single 'best' reply." They ran each prompt 100 times on GPT-3.5 Turbo and benchmarked against Tobia's survey of more than 2,800 people on "vehicle." [DOI] — [doi:10.2139/ssrn.4718347](https://doi.org/10.2139/ssrn.4718347)
- **Arbel & Hoffman (99 NYU L. Rev. 2024), "Generative Interpretation."** LLMs can "quantify ambiguity" and "calculate the probative value of individual pieces of extrinsic evidence" in contract interpretation. [arXiv] — [arXiv:2308.06907](https://arxiv.org/abs/2308.06907)
- **Purushothama, Min, Waldon & Schneider (FAccT 2026; earlier title "Not ready for the bench").** "slight changes to the format of a question can lead to wildly different conclusions." Models are "at best moderately correlated to human judgments." [arXiv] — [arXiv:2510.25356](https://arxiv.org/abs/2510.25356); FAccT [DOI](https://doi.org/10.1145/3805689.3812346)

**Outside law: methods for comparing and aggregating formalizations**
- **LINC (EMNLP 2023 Outstanding Paper).** Olausson et al. use the LLM as a semantic parser to first-order logic and a theorem prover for inference. The full text uses "K-way majority voting, in which K samples are taken i.i.d. from the model and the mode is used as the final prediction," with K=10 by default; samples with syntax errors are filtered out by the prover. Formalization failure modes include implicit information that must be made explicit and information lost through representation choices. [arXiv] — [arXiv:2310.15164](https://arxiv.org/abs/2310.15164); [arXiv-HTML](https://arxiv.org/html/2310.15164v2)
- **Li et al. (NeurIPS 2024).** Autoformalization shows "a considerable discrepancy between pass@1 and pass@k." They select among k candidates using "symbolic equivalence," meaning logical homogeneity checked by automated theorem provers, plus "semantic consistency" via informalization and embedding similarity. Relative gains are 0.22–1.35x. [arXiv] — [arXiv:2410.20936](https://arxiv.org/abs/2410.20936)
- **Sharma & David (2025).** Adapt entropy-based and mutual-information-based uncertainty to code, with "a semantic equivalence check based on symbolic execution." They find "a strong correlation between the uncertainty … and correctness." A simplified variant assumes "a uniform distribution over the LLM's responses." Abstention reduces incorrect outputs "to near zero" on LiveCodeBench. [arXiv] — [arXiv:2502.11620](https://arxiv.org/abs/2502.11620)
- **Wong, Grand, Lew, Goodman, Mansinghka, Andreas & Tenenbaum (2023), "From Word Models to World Models."** LLMs translate natural language into a probabilistic programming language, and "Bayesian inference with the generated programs supports coherent and robust commonsense reasoning." This is rational meaning construction. [arXiv] — [arXiv:2306.12672](https://arxiv.org/abs/2306.12672)
- **Hypothesis Search (ICLR 2024).** Wang, Zelikman, Poesia, Pu, Haber & Goodman have the LLM propose multiple natural-language hypotheses, implement them as programs, and filter them against observed examples. [arXiv] — [arXiv:2309.05660](https://arxiv.org/abs/2309.05660)
- **Panossian (2026), "Two-Stage Structural Uncertainty in LLM-Based Scientific Autoformalization."** Across 320 generated response maps, formalizer identity could be recovered at 96.3% accuracy (chance 50%) and source-account identity at 78.8% (chance 20%). "A common mathematical language did not erase translation provenance." The author argues the generated ensemble is part of the model specification. [arXiv] — [arXiv:2609.14808](https://arxiv.org/abs/2609.14808)
- **Emmenegger, Olausson, Solar-Lezama & Podimata (2026).** Conformal risk control obtained by sampling from an approximate LLM posterior conditioned on a calibrated high-scoring region, applied to biographies and math. [arXiv] — [arXiv:2606.03731](https://arxiv.org/abs/2606.03731)
- **Logic-LM (EMNLP Findings 2023).** Solver error messages drive self-refinement of formalizations. [arXiv] — [arXiv:2305.12295](https://arxiv.org/abs/2305.12295)

### Inferences
- **The project's niche looks open.** No legal paper found treats multiple LLM formalizations as noisy observations of a latent decision model, with a posterior updated by outcome or timing data. Current legal practice stops at pairwise equivalence (Vernie), gold-standard outcome match (Graus), agreement-based abstention (Jurayj) or averaging verifier scores (Nguyen).
- **The building blocks exist.** One plausible pipeline:
  - cluster formalizations into behavioral equivalence classes, using SAT or symbolic-execution equivalence as in Vernie, Li et al. and Sharma & David;
  - put a prior over classes;
  - weight classes by likelihood against official documents and administrative records, in the spirit of Wong et al.'s Bayesian inference over LLM-generated programs and of Law&Order and Graus's verification against outcomes.
- **Samples are not exchangeable.** Panossian (formalizer identity recoverable at 96%) and Blair-Stanek (cross-model instability correlation about 0.12–0.18) imply that LLM formalizations are not exchangeable draws. A principled aggregator likely needs per-formalizer bias or random effects. Treating the samples as independent votes, as in LINC-style majority voting, would overstate confidence when models share training-data biases.
- **Rival readings are not all errors.** Vernie's 4–4 AI Act split shows that some disagreement reflects real legal indeterminacy. A posterior should be able to keep mass on several readings instead of collapsing to the mode.

### Gaps
- No legal study was found that reports formal calibration (for example ECE or coverage) of a distribution over formalizations, or applies conformal prediction to legal rule extraction.
- No Bayesian or Dawid–Skene-style aggregation of multiple LLM legal annotations or formalizations was found. Because WebSearch was unavailable, law-review and SSRN coverage is thin, so a relevant paper may have been missed.

## Q5. Uncertainty quantification for LLM outputs (semantic entropy, conformal prediction, self-consistency, verbalized confidence) in legal settings; calibration findings

### Takeaway
General LLM uncertainty methods are well established:
- semantic entropy (ICLR 2023; Nature 2024);
- self-consistency (ICLR 2023);
- conformal language modeling and conformal factuality (2023–2024);
- verbalized confidence (2022–2024).

Legal applications are sparse. The main legal calibration evidence is from Ho's group. Dahl et al. (2024) estimate confidence from agreement among 10 samples and find all models systematically overconfident about legal hallucinations: ECE ranges from 0.057 for PaLM 2 to 0.421 for Llama 2, and GPT-4 is worse calibrated than PaLM 2 even though it hallucinates less. Verbalized confidence is generally overconfident, and especially weak on professional-knowledge tasks.

### Cited Findings
**Legal settings**
- **Large Legal Fictions (Journal of Legal Analysis 16(1):64–93, 2024).** Dahl, Magesh, Suzgun & Ho find hallucination rates between "58% of the time with ChatGPT 4 and 88% with Llama 2" on verifiable questions about federal cases. "LLMs cannot always predict, or do not always know, when they are producing legal hallucinations." [arXiv] — [arXiv:2401.01301](https://arxiv.org/abs/2401.01301); [DOI](https://doi.org/10.1093/jla/laae003)
  - Full text: confidence is estimated "by sampling 10 responses from the model at temperature 1 and assessing their agreement with the model's greedy response." ECE by model: PaLM 2 0.057, GPT-3.5 0.099, GPT-4 0.190, Llama 2 0.421. Models "systematically overestimate their confidence." [arXiv-HTML] — [arXiv:2401.01301 HTML](https://arxiv.org/html/2401.01301v2)
- **Hallucination-Free? (2024).** Magesh, Surani, Dahl, Suzgun, Manning & Ho ran a preregistered evaluation. Lexis+ AI, Westlaw AI-Assisted Research and Ask Practical Law AI "each hallucinate between 17% and 33% of the time," and RAG reduces but does not eliminate hallucination. [arXiv] — [arXiv:2405.20362](https://arxiv.org/abs/2405.20362)
- **Instability as an uncertainty signal.** See Blair-Stanek & Van Durme (2025) in Q1 and Engel & McAdams (2024) in Q4. [arXiv](https://arxiv.org/abs/2502.05196); [DOI](https://doi.org/10.2139/ssrn.4718347)
- **Waldon, Schneider, Wilcox, Zeldes & Tobia (2025), "Large Language Models for Legal Interpretation? Don't Take Their Word for It."** SSRN working paper, title and authors confirmed from an OpenAlex/Crossref record; abstract not retrieved. [DOI] — [doi:10.2139/ssrn.5123124](https://doi.org/10.2139/ssrn.5123124)
- **Choi, "Measuring Clarity in Legal Text."** Crossref lists DOI 10.2139/ssrn.4151849 under this title (2022), and the abstract concerns empirically measuring textual clarity. Semantic Scholar returns the title "Computational Corpus Linguistics" for the same DOI. The metadata conflict is unresolved. [DOI, conflicting] — [doi:10.2139/ssrn.4151849](https://doi.org/10.2139/ssrn.4151849)
- **Yu et al. (2026).** Semantic-level reward for calibration, motivated by consequential settings including "legal reasoning." [arXiv] — [arXiv:2605.15588](https://arxiv.org/abs/2605.15588)

**General UQ methods that could be transferred**
- **Semantic entropy.** Kuhn, Gal & Farquhar (ICLR 2023) compute entropy over clusters of semantically equivalent outputs; it is "more predictive of model accuracy" than baselines. [arXiv] — [arXiv:2302.09664](https://arxiv.org/abs/2302.09664). Extended in Farquhar, Kossen, Kuhn & Gal, "Detecting hallucinations in large language models using semantic entropy," Nature (2024). [DOI] — [doi:10.1038/s41586-024-07421-0](https://doi.org/10.1038/s41586-024-07421-0)
- **Self-consistency.** Wang et al. (ICLR 2023) sample diverse reasoning paths and marginalize them to pick "the most consistent answer," gaining +17.9% on GSM8K among other results. [arXiv] — [arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
- **Conformal language modeling.** Quach et al. (ICLR 2024) calibrate stopping and rejection rules so that a sampled set "contains at least one acceptable answer with high probability." [arXiv] — [arXiv:2306.10193](https://arxiv.org/abs/2306.10193)
- **Conformal factuality.** Mohri & Hashimoto (2024) back off to less specific outputs to obtain "80-90% correctness guarantees." [arXiv] — [arXiv:2402.10978](https://arxiv.org/abs/2402.10978)
- **Verbalized confidence.**
  - Lin, Hilton & Evans (2022): GPT-3 can be taught to express calibrated uncertainty in words. [arXiv] — [arXiv:2205.14334](https://arxiv.org/abs/2205.14334)
  - Tian et al. (EMNLP 2023): for RLHF models, verbalized confidences are "typically better-calibrated than the model's conditional probabilities," with ECE often about 50% lower in relative terms. [arXiv] — [arXiv:2305.14975](https://arxiv.org/abs/2305.14975)
  - Xiong et al. (ICLR 2024): LLMs "tend to be overconfident" when verbalizing, and all methods "struggle in challenging tasks, such as those requiring professional knowledge." [arXiv] — [arXiv:2306.13063](https://arxiv.org/abs/2306.13063)
- **Structured outputs and code.** See Sharma & David (2025) in Q4, which adds symbolic-execution equivalence to semantic entropy and abstains when uncertain. [arXiv] — [arXiv:2502.11620](https://arxiv.org/abs/2502.11620)

### Inferences
- For structured legal formalizations, the natural analog of semantic entropy is entropy over behavioral equivalence classes, with equivalence decided by SAT or symbolic execution as in Vernie, Sharma & David and Li et al. Nothing found has computed this for statutes.
- Dahl et al.'s finding that sample agreement can be badly calibrated, and differently by model, means that self-consistency frequencies should not be used directly as posterior probabilities. They need calibration against labeled outcomes, or explicit modeling of per-model reliability.
- Verbalized LLM confidence is overconfident on professional-knowledge tasks (Xiong et al.). It is a weak source of prior weights for formalizations.

### Gaps
- No paper was found applying semantic entropy, conformal prediction or verbalized-confidence calibration to statute formalization or legal decision trees specifically.
- COLIEE and LegalBench calibration studies were not located.

## Q6. Critiques of rules-as-code: over-specification, loss of discretion and ambiguity, interpretive choices

### Takeaway
The critical literature (Hildebrandt, Diver, the COHUBICOL/CRCL community, Merigoux et al., Witt/Huggins/Burdon) argues that code-driven law fixes one interpretation in advance. In doing so it removes the interpretive "delay" and discretion that legal institutions rely on, and makes programming choices that are political but go unnoticed. The empirical encoding studies support the narrower point that interpretive choices are unavoidable and partly irreducible. A newer strand warns that machine-readable rules make strategic boundary-search by regulated parties cheaper.

### Cited Findings
- **Hildebrandt (2020), "Code-driven Law: Freezing the Future and Scaling the Past."** Book chapter in *Is Law Computable?* (Hart). It examines code-driven law's assumptions "concerning our ability to sufficiently foresee the future at the moment of codifying legal norms" and connects this to legal certainty. [DOI] — [chapter doi:10.5040/9781509937097.ch-003](https://doi.org/10.5040/9781509937097.ch-003); [SSRN abstract doi:10.2139/ssrn.3522079](https://doi.org/10.2139/ssrn.3522079)
- **Diver (2021), *Digisprudence: Code as Law Rebooted*** (Edinburgh University Press). [DOI] — [doi:10.1515/9781474485340](https://doi.org/10.1515/9781474485340)
- **Diver (2018), "Law as a User: Design, Affordance, and the Technological Mediation of Norms."** SCRIPTed. [DOI] — [doi:10.2966/scrip.150118.4](https://doi.org/10.2966/scrip.150118.4)
- **Journal of Cross-disciplinary Research in Computational Law (CRCL).** Main venue for these critiques. Vol. 1(3) (2023) is titled "Code-driven Computational Law." Vol. 2(2) (2024), "The Future of Computational Law," has position papers by Hildebrandt, Lawsky, Kapoor/Henderson/Narayanan, Merigoux, Bennett Moses, Bex, Pasquale & Malgieri and others. [Archive page] — [journalcrcl.org archive](https://journalcrcl.org/crcl/issue/archive)
- **Witt et al. (2021, 2023).** Divergent interpretive choices by coders; the gap between "technical validation" and "legal alignment"; indeterminacy that "cannot be overcome in advance." The authors argue that RaC requires legal subject-matter, statutory-interpretation and programming expertise. [DOI] — [doi:10.1145/3462757.3466083](https://doi.org/10.1145/3462757.3466083); [doi:10.1007/s10506-023-09350-1](https://doi.org/10.1007/s10506-023-09350-1)
- **Huggins, Witt & Burdon (2024), "Digital distortions arising when encoding regulation."** Research Features, a dissemination outlet. Crossref title record only. [DOI] — [doi:10.26904/rf-151-6106305305](https://doi.org/10.26904/rf-151-6106305305)
- **OECD (2020).** *Cracking the Code* explicitly covers RaC "limitations and implications." [DOI] — [doi:10.1787/3afe6ba5-en](https://doi.org/10.1787/3afe6ba5-en)
- **Strategic gaming.** He (2026), "When Firms Learn to Game the Rules," uses a synthetic reinforcement-learning simulation to ask "whether machine-readable rules make boundary search cheaper" for regulated firms. [arXiv] — [arXiv:2606.04617](https://arxiv.org/abs/2606.04617)
- **Formalization and pragmatic interpretation.** Wang et al. (2026) find that many "legally sound inferences are not formally grounded without additional unstated assumptions," a measurable gap between pragmatic legal interpretation and strict formal entailment. [arXiv] — [arXiv:2606.16118](https://arxiv.org/abs/2606.16118)
- **Interpretation in AI and Law research.** Janeček & Sartor (2026), "Legal interpretation and AI: from expert systems to argumentation and LLMs," surveys how the field has handled legal interpretation. [arXiv] — [arXiv:2603.05392](https://arxiv.org/abs/2603.05392)
- **Ambiguity in the law itself.** Catala's date-ambiguity analysis (Monat et al. 2024) and Lawsky's "definitional scope" problem (2017) show ambiguity in the source law that any single encoding must silently resolve. [arXiv](https://arxiv.org/abs/2403.08935); [DOI](https://doi.org/10.2139/ssrn.2987065)

### Inferences
- These critiques support the project's premise. If any single encoding over-specifies the law, the honest representation is a distribution over admissible encodings, with mass placed on genuinely contested readings such as Vernie's AI Act split and Witt's factual indeterminacy. A point estimate should not be presented as "the" rule.
- The "legal alignment" step in Witt et al. (checking encodings against how courts actually read the statute) is conceptually the likelihood step in a Bayesian treatment. Administrative timing records and official guidance would play the role that judicial interpretation plays there.

### Gaps
- Not verified at the primary page:
  - Diver's CRCL article "Computational legalism and the affordance of delay in law"; it is not in Crossref and the CRCL archive page did not list it.
  - Merigoux, Alauzen & Slimani, "Rules, Computation and Politics." An OpenAlex record lists it as 2022, Journal of Cross-disciplinary Research in Computational Law, with no DOI. It reportedly concerns programming choices in French housing-benefit implementations, but neither its content nor a stable URL could be confirmed. [PARTIAL]
  - Hildebrandt's 2018 "Law as computation in the era of artificial legal intelligence."
- Not found in this pass: other rules-as-code critiques such as Waddington's drafting-side work and the New Zealand and Canadian government RaC evaluations. WebSearch was unavailable.
