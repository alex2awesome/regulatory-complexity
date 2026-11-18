# Prior work stops short of statutory-logic posteriors

No verified prior work does what this project proposes. Nobody has yet put a calibrated posterior over the logic a statute requires and over how each jurisdiction implements it, built by combining several formalizations, official documents and administrative timing records, and checked against planted truth. The closest analogues to Hoff, Raftery & Handcock's latent positions come from political science. **Clark & Lauderdale (2010) locate Supreme Court opinions in a one-dimensional "doctrine space" with MCMC credible intervals**. Clark & Lauderdale (2012) put a posterior over a discrete tree of precedent "parents", and they concede that the sampler struggles to move between modes describing very different trees. Outside law, the ingredients exist but nobody has assembled them for law:
- Bayesian CART and Bayesian Rule Lists give posteriors over decision structure, but in medicine and risk scoring.
- Dawid–Skene, Butts-style informant models and 2026 Ising models aggregate noisy and correlated readers.
- Process mining fits stochastic weights, including ABC-SMC posteriors, on control-flow skeletons it takes as given.
- Phylogenetics and Bayes-factor validation show how to run simulation-based calibration on discrete structures.

LLM-formalization research measures disagreement without modeling it. **Nine frontier models' encodings of ten EU provisions are logically equivalent only about half the time, and structural similarity barely predicts behavioral divergence (ρ = +0.09)**. The literature also sets limits the design must respect:
- Outcome records cannot identify conditions that cases never exercise.
- With a handful of correlated LLM readers, reader dependence is weakly identified or not identified at all.
- Fischman shows that indeterminacy and error trade off along a curve that outcome data alone cannot locate.

Every "no prior work found" claim below rests on searches that were cut short when several researchers' web-search budgets ran out. Before claiming novelty, the group needs a targeted check of ICAIL/JURIX, law reviews and applications of Bayesian trees.

## Nine literatures give posteriors to actors and weights, not to rule logic

The question has a clean answer once you ask of every candidate paper: *what is latent?* In each neighboring literature the latent object is something other than the rule:

| Literature | What is latent |
|---|---|
| Court measurement | A judge's ideal point or an opinion's location |
| AI & Law | The truth of a fact |
| Process mining | A routing weight on a control-flow skeleton the miner fixed in advance |
| Annotation | A categorical label |

The project's latent object falls in the gaps between these literatures. It is the set of conditions, branches and required steps a statute imposes, plus each jurisdiction's implementation of those steps with their timing. The table below gives the closest verified work in each strand. Sources and quotations are in the sections that follow.

| Strand | Closest verified work | What it does not do, relative to the project | What to borrow |
|---|---|---|---|
| 1. Latent-variable / IRT / latent-space models in law | Clark & Lauderdale 2010, 2012; Pang et al. 2012; Hangartner, Lauderdale & Spirig 2025; Arnold, Engst & Gschwend 2023 | The latent object is a 1-D opinion location, a precedent tree, a regime break or a panel's aggregation rule. It is never the internal logic of a statute. None checks coverage against known truth | Tie latent components to text; multirater IRT with formalizations as raters; null-model comparisons; partial identification |
| 2. Rules as functions of facts; Bayesian trees | Kastellec 2010; case-space theory; Bayesian CART/BRL; the welfare-benefit rule-recovery benchmark | Legal tree work is frequentist and uses one tree. Bayesian trees have never been applied to doctrine. Accurate learners recover the wrong rule | Tree and rule-list priors from formalizations; likelihoods that allow non-compliance; "rationale unit tests" |
| 3. AI & Law uncertainty | Riveret et al. 2007; Neil et al. 2019; precedential-constraint models | Probabilities on rules are assumed, never estimated. Model averaging is applied only to evidence | Treat probability as "acceptance by the adjudicator"; Bayesian model averaging over inconsistent models; precedent as a support constraint |
| 4. LLM formalization and rules-as-code | Vernie & Grabmair 2026; Graus 2026; Witt et al. 2021/2023 | Disagreement is measured pairwise and never aggregated into a posterior | SAT-enumerated edge cases; agree on predicates first; behavioral equivalence classes |
| 5. Noisy and correlated reader models | Dawid–Skene; Butts 2003; Ising LLM judges 2026; V-Dem | Structured outputs are aggregated assuming independent readers. No coverage studies for aggregated LLM judges | Element-level latent classes; a shared LLM factor; collapse redundant readers; synthetic anchors |
| 6. Ambiguity vs vagueness vs discretion | Fischman 2014; Farnsworth et al. 2010; *Loper Bright* 2024; Chan, Gentzkow & Yu 2022 | No joint estimate of textual ambiguity and delegated discretion | Delegation lexicon as a prior; the indeterminacy–error curve; elicitation that splits own uncertainty from expected disagreement |
| 7. Process mining under uncertainty | Cry et al. 2025; Leemans et al. 2024; Mannhardt et al. 2016/2023; Buijs et al. 2013 | Posteriors cover weights only, not structure. Logs are assumed nearly complete | Stochastic-language likelihoods; configurable models across jurisdictions; queueing and censoring components; BPIC 2015 |
| 8. Validating structured posteriors | Modrák et al. 2025; Mendes et al. 2025; Karimi Mamaghan et al. 2024; Kim & Ročková | No calibration study (SBC or coverage) of DAG, decision-graph or LLM-proposal posteriors | Graph-appropriate test quantities; exact enumeration on small cases; run-agreement diagnostics; larger structural moves |
| 9. Complexity and administrative burden | Colliard & Georg 2025; Dong & Wiser 2013; Manville et al. 2023 | No study links a statute's decision-logic complexity to processing times | Effect-size priors; exposures derived from the rule text; APR and SolarTRACE timing data |

Three patterns run across all nine strands:
- **Samplers get trapped in modes wherever structure receives a posterior.** This happens in the Genealogy of Law, in Bayesian CART and in phylogenetic tree space.
- **Dependence among readers is the binding identification constraint** wherever many readers measure one object.
- **Validation is almost never coverage against planted truth.** Martin–Quinn scores were validated by correlation with Segal–Cover scores, and Clark & Lauderdale by correlation with Martin–Quinn. A synthetic-statute benchmark with known structure would go beyond the standard of every literature reviewed here.

## Law's latent-variable models locate judges, opinions and precedents

### Doctrine space is the closest Hoff analogue, and it is one-dimensional (strand 1)

The standard court models put the posterior on people. Martin & Quinn's dynamic item-response model covers **3,450 non-unanimous Supreme Court cases**:
- Each justice gets a random-walk ideal point.
- Each case gets a cutpoint and a discrimination parameter that are never linked to its facts.
- Unanimous cases are dropped because they "contribute no information to the likelihood."
- Semi-informative priors on "certain justices" ensure that "only one of the posterior modes has nonnegligible mass."
- Validation is by correlation with external scales.

([Martin & Quinn 2002](https://www.cs.princeton.edu/courses/archive/fall09/cos597A/papers/MartinQuinn2002.pdf))

Ho & Quinn's warning applies with extra force to any latent rule this project estimates: such scores are "descriptive summaries" that are "widely misinterpreted, and commonly misused." They add that measurement models "empower meaningful examination, data collection, and incorporation of doctrine and jurisprudence" ([Ho & Quinn 2010](https://www.law.berkeley.edu/files/Ho-Quinn_HowNotToLie.pdf)). Hanretty supplies a negative result: a well-specified hierarchical IRT of the British Law Lords was **"no better than a null model"**, and its positions captured only a propensity to dissent ([Hanretty 2013](https://doi.org/10.1017/s0007123412000270)).

Clark & Lauderdale (2010) apply every Hoff, Raftery & Handcock ingredient to legal texts ([Clark & Lauderdale 2010](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf)):
- Opinions get latent positions x_k ~ N(0,1).
- The probability that one opinion cites another positively is Φ(κ − λ(x_k − x_k′)²).
- The citation model is fit jointly with a vote IRT in JAGS.
- They report **95% highest-density intervals** for 851 search-and-seizure opinions and 217 freedom-of-religion opinions.

Its limits match the project's problems one for one:
- It works in one dimension, one issue area at a time.
- Citation polarity is hand-coded.
- Identification comes from placing dissents at their authors' ideal points, which the authors call "the most plausible assumption which identifies" the space.
- κ and λ are constant across opinions, which the authors concede will "underestimate or overestimate the uncertainty" for narrow or broad opinions.

"The Genealogy of Law" goes further. It puts a posterior over a discrete tree in which each majority opinion has one latent parent precedent. The authors chose MCMC for two reasons: maximum likelihood over trees is infeasible because their number "grows as (n − 1)!", and MCMC yields "an uncertainty estimate over possible trees." They then warn that with "multiple modes that describe very different trees, the sampler will still have a difficult time moving between the two modes" ([Clark & Lauderdale 2012](https://www.tomclarkphd.com/files/ClarkLauderdalePA2012.pdf)). That sentence is the closest published precedent for the mode trapping that a posterior over decision graphs will face.

Arnold, Engst & Gschwend scale German lower-court decisions from a decision × legal-source matrix whose columns include statutory norms such as BGB §823. They draw 8,000 posterior samples, flip signs to resolve rotational invariance, test recovery on toy data against rewired null matrices, and run posterior predictive checks ([appendix](https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/AEG_JLC.pdf); [Arnold et al. 2023](https://doi.org/10.1086/717420)). It is the first verified model in which statutory provisions are measurement items. The positions of the provisions themselves do not appear to be a primary output; the researcher flagged that reading as unverified.

Three papers come closest to a posterior over decision logic itself:
- **Pang, Friedman, Martin & Quinn** estimate "the locations of many possible change-points along with structural parameters" in a multivariate probit of outcomes on case facts, and choose the number of regimes by Bayesian model comparison ([Pang et al. 2012](https://doi.org/10.1093/pan/mps024)). This is a posterior over the structure of the mapping from facts to outcomes, but the structure is temporal, not about which conditions enter.
- **Hangartner, Lauderdale & Spirig** infer which aggregation rule governs three-judge Swiss asylum panels; **chair-as-dictator fits 45% of cases**. They show that under some rules the most extreme judges can be bounded but not point-identified ([Hangartner et al. 2025](https://doi.org/10.1017/S0007123425100574)).
- **Clinton & Lapinski** give each of 21,741 public statutes a latent "importance" score, with standard errors, from nine rater lists ([Clinton & Lapinski 2006](https://doi.org/10.1111/j.1540-5907.2006.00181.x)). It is the closest statute-level multirater design.

Peress observes that ideal-point methods "only recover cutpoints" unless cosponsorship data are added ([Peress 2013](https://doi.org/10.1017/s0022381613000571)). That is the identification problem in miniature: outcomes alone do not locate the rule.

The project should borrow four things from this strand:
- **Tie latent rule components to the statute text**, as Clark & Lauderdale tie dissents to their authors, and then test the tie.
- **Treat formalizations as raters** in a multirater model with per-rater bias.
- **Always fit a null model.**
- **Accept bounds** where point identification fails.

None of these papers checks interval coverage against known truth. Lauderdale & Clark state outright, "we have not found a way to generate satisfactory measures of uncertainty for our estimator" ([Lauderdale & Clark 2012](https://www.tomclarkphd.com/files/LauderdaleClarkAPSR2012.pdf)).

The Hoff, Raftery & Handcock citation itself is confirmed in Crossref ([Hoff et al. 2002](https://doi.org/10.1198/016214502388618906)). However, the only copy available to the researchers was a scan without extractable text, so its content was not checked. The details usually attributed to it (identification only up to rotation, reflection and translation; Procrustes alignment of posterior draws) should be checked against the paper before the group cites them.

### Outcome data pin down decisions on observed cases, not the rule's structure (strand 2)

The empirical fact-pattern tradition estimates one mapping from coded facts to outcomes, and the analyst chooses its form:
- Segal's probit explains search-and-seizure reasonableness from the justification for the search, the nature of the intrusion and "a few mitigating circumstances" ([Segal 1984](https://doi.org/10.2307/1955796)).
- Kastellec offers classification trees as "a flexible way to study legal doctrine" ([Kastellec 2010](https://doi.org/10.1111/j.1740-1461.2010.01176.x)).

Neither reports a distribution over alternative rule structures. How Kastellec pruned trees or handled their instability is unverified because the full text was paywalled.

Case-space theory supplies the generative meaning the project needs:
- A rule is a partition of "fact-filled legal cases into different dispositions" ([Lax 2011](https://doi.org/10.1146/annurev.polisci.042108.134842)).
- Judges refine that partition case by case and may stop early, leaving "residual uncertainty in the law and some cases wrongly decided" ([Cameron & Kornhauser 2023](https://doi.org/10.1628/jite-2023-0001)).
- "With positive probability, identical cases are treated differently" ([Baker & Mezzetti 2012](https://doi.org/10.1086/666655)).

Empirically, the economic loss rule across 461 state appellate decisions "did not converge to any stable resting point and evolved differently in different states" ([Niblett, Posner & Shleifer 2010](https://doi.org/10.1086/652908)). That argues for drawing jurisdiction-level rules hierarchically around a statewide rule, rather than assuming one latent rule.

The machinery for posteriors over rule structure is mature but has not been pointed at law:
- Bayesian CART explores "a probability distribution over the space of possible trees" by reversible-jump MCMC ([Denison, Mallick & Smith 1998](https://doi.org/10.1093/biomet/85.2.363); [Chipman, George & McCulloch 1998](https://doi.org/10.1080/01621459.1998.10473750)).
- BART adds variable-inclusion frequencies ([Chipman et al. 2010](https://arxiv.org/abs/0806.3286)).
- Bayesian Rule Lists "yields a posterior distribution over possible decision lists," applied to stroke risk ([Letham et al. 2015](https://doi.org/10.1214/15-aoas848)).
- Rashomon-set enumeration lists every near-optimal sparse tree ([Xin et al. 2022](https://arxiv.org/abs/2209.08040)).

The legal-adjacent uses are non-Bayesian risk tools, such as rule lists that match COMPAS accuracy ([Angelino et al.](https://arxiv.org/abs/1704.01701)) and pretrial-release checklists ([Jung et al.](https://arxiv.org/abs/1702.04690)). **No verified paper applies Bayesian CART, BART or Bayesian Rule Lists to doctrine, benefits eligibility or administrative adjudication and reads the structure posterior as uncertainty about the legal rule.**

The most consequential result in this strand comes from AI & Law's synthetic welfare-benefit benchmark: an eligibility rule with six conditions and known truth.
- **Možina et al.** pose the project's inverse problem directly: "Is there a way of deciding what the rule being followed is from an automated consideration of the data?" Neural nets, defeasible-logic induction and CN2 all classify accurately, yet **"none of the techniques produced rules which faithfully reflected the conditions for the benefit."** No system found the sex condition, and none could have, because the "learning data only contains male applicants between 60 and 65 that fail to qualify also for other reasons" ([Možina et al.](https://intranet.csc.liv.ac.uk/~tbc/publications/ArgumentBasedMachineLearningAp.pdf)).
- **Steging, Renooij & Verheij** replicate the result. Networks above 98% accuracy failed to learn two of the six conditions, and **four conditions alone classify 98.95% of instances** ([Steging et al. 2021](https://arxiv.org/abs/2105.06758)).

Neighboring approaches return point estimates or work outside legal corpora:
- **Symbolic theory construction.** AGATHA scores candidate case-law theories for simplicity and explanatory power by A* search, but returns a single best theory ([Chorley & Bench-Capon](https://cgi.csc.liv.ac.uk/~tbc/publications/agatha.pdf)).
- **Bayesian norm induction.** Methods that learn from both compliant and violating behavior exist only for multi-agent systems, not legal corpora ([Cranefield et al. 2016](https://doi.org/10.3233/978-1-61499-672-9-622); [Oldenburg & Zhi-Xuan 2024](https://arxiv.org/abs/2402.13399)).
- **LLM "legal rule induction."** Inducing rules from 38,088 Chinese cases, frontier LLMs "struggle with over-generalization and hallucination" ([Fan et al. 2025](https://arxiv.org/abs/2505.14104)).

The project should borrow the following from this strand:
- Bayesian tree or rule-list samplers whose priors come from formalizations rather than generic split priors.
- A likelihood with explicit non-compliance and error terms.
- Steging's "rationale unit tests" (fact patterns built to fail exactly one condition), used as posterior predictive checks and as active-learning queries.
- Rashomon enumeration as a baseline for whether a structure posterior is too concentrated.
- Ellis's pattern, in which "a language model first proposes candidate hypotheses expressed in natural language, which are then re-weighed by a prior and a likelihood" ([Ellis 2023](https://arxiv.org/abs/2306.02797)).

### AI and Law keeps probability on facts and leaves the law crisp (strand 3)

AI & Law's probabilistic work is overwhelmingly about evidence:
- Legal Bayesian networks openly encode "a subjective account of a legal case." Their likelihoods are supplied by experts and their priors are "difficult to elicit" ([Vlek et al. 2014](https://webspace.science.uu.nl/~prakk101/pubs/VlekAILJ14.pdf)).
- Verheij names the core problem: "More numbers are needed than are available" ([Verheij 2017](https://doi.org/10.1007/s10506-017-9199-4)).
- Dung & Thang state the division of labor. "The judge as the arbiter of law determines the legal permissibility of the presented arguments" without probabilities, while jurors weigh the facts probabilistically ([Dung & Thang 2010](https://doi.org/10.3233/978-1-60750-619-5-171)).

The project's target, probability over the law itself, sits on the underdeveloped side of that line.

The exception is the line of work by Riveret, Rotolo, Sartor and Prakken.
- **The 2007 paper puts probability on an adjudicator's acceptance of a rule**, Pr(accepted(q)), arguing that "it makes sense to assign probabilities to normative statements or rules." In their worked example, the acceptance probabilities of the premises, including a contested force-majeure rule, propagate through a dialogue tree to a 0.4941 probability of success. But "a probability distribution is assumed," and the paper closes by asking "where do the numbers for the probabilities come from?" Its suggestion is to count "the number of same-level courts that accepted a specific rule" ([Riveret et al. 2007](https://webspace.science.uu.nl/~prakk101/pubs/jurix07.pdf)).
- Later work separates three kinds of uncertainty: the credibility of premises, which arguments to consider, and an argument's acceptance status ([Riveret et al. 2018](https://doi.org/10.1007/s10472-018-9574-1)).
- A 2020 paper defines probabilistic obligation and illustrates it without data ([Riveret, Oren & Sartor 2020](https://doi.org/10.1016/j.ijar.2020.08.012)).

**The only verified AI & Law paper that weights competing models** is Neil, Fenton, Lagnado & Gill. They apply Bayesian model comparison and averaging to evidence models "built independently and with no attempt to make them consistent in terms of variables, causal assumptions or parameterization" ([Neil et al. 2019](https://doi.org/10.1007/s10506-019-09250-3)). Allen & Saxon raised the statutory version of the problem in 1991 without a probabilistic remedy: "legal rules are characteristically susceptible to multiple structural interpretations, but current legal expert systems embody only one of the many possible interpretations" ([Allen & Saxon 1991](https://openalex.org/W2595407821)).

Rule-level probabilities have essentially never been calibrated against outcomes. Two related findings bear on validation design:
- ECHR outcome predictors fall from 75% accuracy to 58–68% when trained on past cases and tested on future ones, and **judges' surnames alone give 65%** ([Medvedeva, Vols & Wieling 2020](https://doi.org/10.1007/s10506-019-09255-y)).
- A single-author, unreviewed 2026 preprint reports that naively fusing LLM per-fact estimates with Bayesian-odds or Dempster–Shafer pipelines raised expected calibration error from about 0.16 to 0.46, with no gain in AUROC ([Saka 2026](http://arxiv.org/abs/2608.14617v1)).

The project should borrow five things:
- **Riveret's acceptance semantics.** It turns "is this reading true?" into an observable institutional act, which maps onto a jurisdiction-level random effect for "implements reading k."
- **Precedential-constraint models as constraints on the prior.** These are now robust to inconsistent case bases ([Canavotto 2022](https://doi.org/10.3233/faia220445)) and can serve as hard or soft limits on which rules the prior allows.
- **Odekerken, Bex & Prakken's "stability" and "relevance"** ([2023](https://doi.org/10.1145/3594536.3595136)). Once a distribution sits on the possible fact values, these become posterior predictive certainty and expected information gain.
- **Keep intermediate concept nodes.** Canavotto & Horty show that flattening a hierarchy of open-textured predicates can either lose or create constraints ([2023](https://doi.org/10.1145/3594536.3595148)).
- **Hold out data forward in time or by jurisdiction**, not at random.

## LLM readers disagree half the time and err together

### Formalizations are compared pairwise but never aggregated (strand 4)

Research on LLM formalization now documents disagreement precisely, and then stops.

**Vernie & Grabmair** had nine frontier models formalize ten EU provisions as Boolean trees ([Vernie & Grabmair 2026](https://arxiv.org/abs/2605.25186)). They matched nodes, derived a shared interface for each pair, and used a SAT solver to enumerate every fact pattern on which two formalizations disagree. The results†:
- Among 304 pairs with matching coverage ≥ 0.4, the equivalence rate flattens near 50%.
- **Only 42% of pairs are logically equivalent even at the highest coverage.**
- Coverage correlates with edge-case count at **ρ = +0.09**: "structural alignment does not predict behavioral divergence" ([full text](https://arxiv.org/html/2605.25186v2)).
- Disagreement varies by model, from 71% of pairs for Gemini 3.1 Pro to 32% for Qwen 3.5, and by provision, from 0% to 100%.
- Some splits mirror genuine controversies in the legal commentary. The models divide evenly on whether race-based biometric categorization falls under AI Act Article 5.
- Others are encoding errors, such as a burden-of-proof rule encoded as a substantive condition.

The paper proposes no aggregation. It is an arXiv preprint whose EMNLP acceptance is reported in its own arXiv comment.

**Graus** finds the same thing independently, using 95 production decision models behind the Dutch Omgevingsloket permit-check platform ([Graus 2026](https://arxiv.org/abs/2604.17153)):
- Adding input/output constraints raises structural similarity by 37–54%.
- Generated models still **match the gold standard on only 51–53% of test scenarios**.
- "Structural similarity does not guarantee outcome equivalence, and vice versa."

Human coders behave the same way. In Witt et al.'s two-week experiment encoding Australian copyright provisions, agreeing on key terms ("atoms") first "can significantly increase the similarity" of the encodings. Even so, coders made "a range of divergent interpretive choices," which the authors trace to interpretive complexity, granularity and the expressiveness of the coding language ([Witt et al. 2021](https://doi.org/10.1145/3462757.3466083)). The journal version adds that "some difficulties cannot be overcome in advance, such as factual indeterminacy" ([Witt et al. 2023](https://doi.org/10.1007/s10506-023-09350-1)). Nguyen et al. find that LLM failures "arise primarily from abstraction choices rather than logical errors," including conflating procedural and substantive rules ([Nguyen et al. 2026](https://arxiv.org/abs/2604.14607)). Vernie & Grabmair observed the same error, which justifies a prior on that error type.

Reliability results argue for modeling the formalization step explicitly:
- **Synthetic statutes.** On statutes it cannot have memorized, GPT-3 "performs poorly" ([Blair-Stanek et al. 2023](https://arxiv.org/abs/2302.06100)).
- **Instability.** At temperature 0, frontier models change which party wins on **10.6% (Claude 3.5) to 50.4% (Gemini 1.5) of 500 legal questions**, and between-model correlations of instability are only 0.12–0.18† ([Blair-Stanek & Van Durme 2025](https://arxiv.org/abs/2502.05196)).
- **Benchmarks.** DeonticBench includes a U.S. state housing-law subset with a reference Prolog program for every instance. Its best hard-subset result reaches only 46.6 macro-F1 on housing ([Dou et al. 2026](https://arxiv.org/abs/2604.04443)).
- **Exceptions.** NormBench documents "Silent Scope Omission" of nested exceptions and "Recursion Decay" as defeater depth grows ([Chen et al. 2026](https://arxiv.org/abs/2606.08932)).
- **Calibration.** Dan Ho's group found that agreement among sampled answers is systematically overconfident about legal hallucinations, with expected calibration error from 0.057 (PaLM 2) to 0.421 (Llama 2)† ([Dahl et al. 2024](https://arxiv.org/abs/2401.01301)). Self-consistency frequencies therefore cannot be used as posterior probabilities without calibration.

Aggregation in practice is crude:
- Inside law, systems abstain unless two independent reasoning routes agree ([Jurayj et al.](https://arxiv.org/abs/2508.21051)).
- Outside law, LINC uses majority voting over K = 10 samples† ([Olausson et al. 2023](https://arxiv.org/abs/2310.15164)).
- Yet the formalizer's identity can be recovered from its outputs 96.3% of the time ([Panossian 2026](https://arxiv.org/abs/2609.14808)). The samples are not exchangeable draws.

The project should borrow the following:
- Behavioral equivalence classes computed by SAT, as in Vernie & Grabmair and in the symbolic-equivalence selection of [Li et al. 2024](https://arxiv.org/abs/2410.20936).
- Entropy over those classes, the structured analogue of semantic entropy ([Sharma & David 2025](https://arxiv.org/abs/2502.11620)).
- A fixed predicate vocabulary agreed before formalization.
- Wider priors for provisions with many exceptions.
- Random effects for formalizer and prompt format.
- Wong et al.'s translation of language into probabilistic programs as the inference template ([Wong et al. 2023](https://arxiv.org/abs/2306.12672)).
- DeonticBench's housing subset as an external testbed.

### Correlated readers cap what agreement can identify (strand 5)

The measurement-model literature supplies the reader model, and its sharpest limits.

Dawid–Skene gives each reader a confusion matrix and assumes readers are conditionally independent given the latent class ([Dawid & Skene 1979](https://doi.org/10.2307/2346806)). Hierarchical Bayesian versions with annotator structure "came out on top in all evaluations," though label switching "makes the models nonidentifiable" for convergence checks ([Paun et al. 2018](https://aclanthology.org/Q18-1040/)).

Identification rests on Kruskal's uniqueness theorem, as generalized by Allman, Matias & Rhodes ([Allman et al. 2009](https://arxiv.org/abs/0809.5032)):
- At least three conditionally independent, informative views give generic identifiability, up to label swapping.
- **An r-class mixture of p binary readers needs p ≥ 2⌈log₂ r⌉ + 1.**
- Counting degrees of freedom is not enough to establish identifiability ([Jones et al. 2010](https://doi.org/10.1111/j.1541-0420.2009.01330.x)).

For a decision model with many possible configurations, these bounds force a factorization into small latent variables, one per element. Each element then needs enough independent readings.

Dependence among readers is the binding constraint:
- **Dendukuri & Joseph** show that with conditional dependence, classical inference "requires that results from at least four different tests be used in order to obtain an identifiable solution." With fewer tests, "the posterior distributions are strongly dependent on the prior information ... even with large sample sizes" ([Dendukuri & Joseph 2001](https://doi.org/10.1111/j.0006-341X.2001.00158.x)).
- **Albert & Dodd** show that with few tests, "likelihood comparisons and other model diagnostics may not be able to distinguish between models with different dependence structures," and that misspecifying the dependence biases the estimates ([Albert & Dodd 2004](https://doi.org/10.1111/j.0006-341X.2004.00187.x)).

LLMs violate independence badly. Across more than 350 models, "models agree 60% of the time when both models err" on one leaderboard dataset, and **"larger and more accurate models have highly correlated errors"** ([Kim et al. 2025](https://proceedings.mlr.press/v267/kim25e.html)). Mistakes "are becoming more similar with increasing capabilities" ([Goel et al. 2025](https://proceedings.mlr.press/v267/goel25b.html)).

The 2026 Ising model for LLM judges ([Balasubramanian et al. 2026](https://arxiv.org/abs/2601.22336); presented at ICML 2026 per [Amazon Science](https://www.amazon.science/blog/when-llm-judges-agree-should-we-believe-them)) formalizes the cost:
- Aggregators that assume conditional independence can "flip the Bayes label despite matching per-annotator marginals."
- They remain "strictly suboptimal as the number of judges grows" when errors share a latent factor.
- The dependence-aware model improves accuracy (0.90 against 0.82 on WikiQA relevance).
- It reports **no calibration error, Brier score or coverage**.

For structured truths, the best templates come from network inference:
- **Butts (2003)** places an exponential-family prior on the latent network and gives each informant beta-distributed false-positive and false-negative rates ([Butts 2003](https://doi.org/10.1016/S0378-8733(02)00038-2)). Young, Cantwell & Newman extend this to data "in any format" ([Young et al. 2020](https://arxiv.org/abs/2008.03334)). Applied here, each condition, branch and cross-reference would be treated like an edge.
- **Welinder et al.** embed annotators in a latent space that reveals "schools of thought." This is the crowdsourcing analogue of Hoff-style positions ([Welinder et al. 2010](https://proceedings.neurips.cc/paper_files/paper/2010/file/0f9cafd014db7a619ddb4276af0d692c-Paper.pdf)).

Every structured-aggregation model found assumes readers are independent given the structure.

Political science's coder models show what misspecification does to coverage. In V-Dem's own simulations ([Marquardt & Pemstein WP 2017:41](https://v-dem.net/media/publications/v-dem_working_paper_2017_41.pdf)), nominal 95% intervals cover the truth at these rates:

| Data-generating process | Fitted model | Coverage of nominal 95% intervals |
|---|---|---|
| Fitted model matches the generator | Same model | 0.95 |
| Reader reliability varies | Model that treats reliability as fixed | 0.84 |
| Intercept differential item functioning (reader-specific level shifts) | Model without a term for it | **roughly 0.48–0.54** |

V-Dem concedes that temporally dependent rater errors violate conditional independence and would make intervals "too liberal (too certain)." Its fix is to collapse any stretch with no differing ratings into a single observation, which it admits is "probably too conservative" ([Pemstein et al. 2026](https://v-dem.net/media/publications/wp21_2026.pdf)). Design-based alternatives guarantee coverage only with a gold-labeled subset ([prediction-powered inference](https://doi.org/10.1126/science.adi6000); [design-based supervised learning](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d862f7f5445255090de13b825b880d59-Abstract.html)). When the judge is no more accurate than the model being evaluated, **"no debiasing method can decrease the required amount of ground truth labels by more than half"** ([Dorner, Nastl & Hardt 2025](https://arxiv.org/abs/2410.13341)).

## Ambiguity and discretion differ in doctrine but blur in data (strand 6)

**The collaborator's question has a doctrinal answer: yes, an ambiguous provision and a provision that grants discretion are different things.** The *Loper Bright* majority, quoting Sunstein, holds that "an ambiguity is simply not a delegation of law-interpreting power." It adds that "many or perhaps most statutory ambiguities may be unintentional" and that statutes "do—in fact, must—have a single, best meaning." Express delegations look different. They use phrases such as "as defined by regulations which the Commission shall promulgate" and "in the judgment of the [EPA] Administrator," or terms like "appropriate" and "reasonable" that "leave[] agencies with flexibility" ([*Loper Bright* slip op.](https://www.supremecourt.gov/opinions/23pdf/22-451_7m58.pdf)).

So the two differ in what the reviewer must do:
- **Ambiguity** is uncertainty about which rule the text states, and the reviewer must find the best reading.
- **Discretion** is a rule whose best reading delegates a choice, and the reviewer polices only the boundaries of that choice.

Justice Kagan's dissent treats ambiguities and gaps as implicit delegations. The mapping from "uncertain text" to "permitted choice" is therefore itself a legal rule, and it changed in 2024. Dworkin's "strong" discretion, where an official is "simply not bound by standards," matches explicit delegation; this rests on the standard reading, since the researchers could not re-read the text past a bot check ([Dworkin 1967](https://chicagounbound.uchicago.edu/uclrev/vol35/iss1/3/)). Hart's lost 1956 essay treats discretion as "a special mode of reasoned, constrained decisionmaking" between arbitrary choice and determinate rule application ([Harvard Law Review](https://harvardlawreview.org/print/vol-127/the-path-not-taken-h-l-a-harts-harvard-essay-on-discretion/)).

Four refinements matter for modeling:
1. **Ambiguity often shows up as heterogeneity, not shared uncertainty.** Farnsworth, Guzior & Malani separate *internal* ambiguity (a reader's own uncertainty) from *external* ambiguity (expected disagreement among ordinary readers). In a survey of about 1,000 law students, only the internal version was "strongly biased by their policy preferences" ([Farnsworth et al. 2010](https://academic.oup.com/jla/article-lookup/doi/10.1093/jla/2.1.257)). Solan's "pernicious ambiguity" is confident but divergent readings ([Solan 2004](https://scholarship.kentlaw.iit.edu/cklawreview/vol79/iss3/22)).
2. **Vagueness cannot be removed by better reading.** Endicott argues that because law is vague, judges "cannot always treat like cases alike" ([Endicott 2000](https://api.philpapers.org/rec/ENDVIT)). Choi separates unclarity caused by missing information, which is reducible, from fundamental indeterminacy, which is not ([Choi 2024](https://chicagounbound.uchicago.edu/uclrev/vol91/iss1/1/)). Borderline cases of vague terms therefore behave like discretion in Dworkin's weak sense.
3. **Evaluative standards such as "reasonable" and "appropriate" are both vague and delegating.** *Loper Bright* treats them as delegations.
4. **Adjudicators differ on when to call a text ambiguous at all.** Kavanaugh describes applying "something approaching a 65-35 rule," while some colleagues apply "90-10" and others "55-45" ([Kavanaugh 2016](https://harvardlawreview.org/wp-content/uploads/2016/06/2118-2163-Online.pdf)). Doctrines triggered by ambiguity can therefore turn shared uncertainty into differences between judges.

Measurement follows the same split.

**Textual ambiguity is measured as dispersion**: across survey respondents, corpora, embedding models or repeated LLM samples ([Tobia 2020](https://harvardlawreview.org/2020/12/testing-ordinary-meaning/); [Arbel & Hoffman 2024](https://nyulawreview.org/wp-content/uploads/2024/05/99-NYU-L-Rev-451-1.pdf); [Engel & McAdams 2024](https://doi.org/10.2139/ssrn.4718347)). The instruments themselves are unstable:
- **Different LLMs' judgments on identical interpretive questions correlate at r = 0.051** ([Choi 2025](https://doi.org/10.2139/ssrn.5188865); [HKU summary](https://www.lawtech.hku.hk/?p=648)).
- "Slight changes to the format of a question can lead to wildly different conclusions" ([Purushothama et al.](https://arxiv.org/abs/2510.25356)).

**Discretion is measured as variance between adjudicators under random assignment:**
- In Ho's restaurant-inspection experiment, "observing identical conditions, inspectors disagreed 60% of the time," and peer review raised violations detected by 17–19% and "appeared to decrease variability across inspectors" ([Ho 2017](https://law.stanford.edu/publications/does-peer-review-work-an-experiment-of-experimentalism)).
- Chan, Gentzkow & Yu partially separate preference from diagnostic skill. Skill explains 39% of the variation in decisions ([Chan et al. 2022](https://doi.org/10.1093/qje/qjab048)).
- Frakes & Wasserman show that the time patent examiners are allotted shifts their grant rates ([Frakes & Wasserman 2017](https://doi.org/10.1162/rest_a_00605)).

Between-adjudicator variance, Var(u_j), therefore measures inconsistency from any source: permitted choice, divergent readings, skill or workload. It does not measure discretion as such. On the statute side, text-derived measures can supply a prior on how much a provision delegates. Vannoni, Ash & Morelli parse syntax trees to identify delegated agents and actions ([Vannoni et al. 2021](https://www.cambridge.org/core/journals/political-analysis/article/measuring-discretion-and-delegation-in-legislative-texts-methods-and-application-to-us-states/281BC160DE55EE6A214C570F713EFC6A)).

Fischman's framework is the formal version of this confound ([Fischman 2014](https://doi.org/10.1093/aler/aht011); [NBER draft](https://conference.nber.org/conf_papers/f66640/f66640.pdf)). He defines three quantities:
- *Inconsistency* is "the probability that two judges would differ in their disposition of a randomly selected case." It can be estimated from outcomes.
- *Indeterminacy* is "the proportion of cases in which the law fails to require a unique result."
- *Error* is the proportion of cases in which the decision conflicts with the result the law requires.

Indeterminacy and error cannot be estimated separately. They can only be traced jointly along an "indeterminacy-error curve." His application is Chinese affirmative asylum claims in the New York Immigration Court. Inconsistency there lay between 26.6% and 51.7%. If every case had one legally correct result, at least 20% were wrongly decided, and **the expected error rate stays positive "unless at least 84% of the cases are indeterminate."** These figures come from the conference draft; the published version was not checked.

No study found estimates textual ambiguity and delegated discretion as separate variance components. The literature points to four levers that could separate them:
- **Variation in rule text with case mix held fixed**, as with the Sentencing Guidelines, *Booker* and the SSA vocational grid.
- **Elicitation that splits a reader's own confidence from predicted agreement among others.**
- **Replicating identical cases with a deliberation step**, which reveals how much of the variance can be reduced.
- **Outcome feedback**, such as reversals on appeal.

One testable signature, proposed in the notes and not established in any source: ambiguity among discrete senses should produce clustered, multimodal adjudicator behavior, while delegated discretion over a continuous standard should produce continuous dispersion of decision thresholds.

## Process, validation and burden work supplies machinery, not the target

### Process mining fits weights on skeletons it takes as given (strand 7)

Stochastic process mining adds routing weights and duration distributions to Petri nets. It scores a model against the frequencies of traces in an event log, for example with the Earth Mover's distance between their stochastic languages ([Leemans et al. 2021](https://doi.org/10.1016/j.is.2021.101724)). Discovery mostly fits weights to a skeleton produced by a conventional miner:
- Burke, Leemans & Wynn take "a Petri net model and an event log as input" and output a generalized stochastic Petri net ([Burke et al. 2021](https://doi.org/10.1007/978-3-030-72693-5_20)).
- Leemans et al. give optimal stochastic discovery, both with and without a given control-flow model ([Leemans et al. 2024](https://doi.org/10.1007/978-3-031-61057-8_3)).

**The closest object to the project's posterior is Cry et al.'s simulation-based Bayesian inference.** It is an ABC-SMC scheme "providing a posterior distribution over model weights" of a fixed stochastic workflow net or process tree ([Cry et al. 2025](https://doi.org/10.1007/978-3-032-05792-1_22); [doctoral consortium paper](https://ceur-ws.org/Vol-4088/paper_246.pdf)). Structure search remains optimization: log-likelihood-guided split operators ([Herbst 2000](https://doi.org/10.1007/3-540-45164-1_19)), or Bayesian optimization over subsets of candidate places that "does not guarantee optimal solutions" ([Brockhoff et al. 2026](https://ceur-ws.org/Vol-4236/paper17.pdf)). The field's 2026 survey frames uncertainty as a four-level specification covering log attributes and model elements ([Leemans et al. 2026](https://doi.org/10.1109/TKDE.2026.3715402)). No verified method puts a posterior over the structure of a Petri net or process tree.

The project's data, a few milestones per permit plus forum narratives, amount to massively missing events. Process mining handles this only in part:
- **Uncertain attributes.** Pegoraro & van der Aalst attach sets or intervals to uncertain events and return bounds on conformance ([Pegoraro et al. 2021](https://doi.org/10.1016/j.is.2021.101810)).
- **Partial orders.** van der Aa et al. turn partially ordered events into "a probability distribution over all possible total orders" ([van der Aa et al. 2020](https://doi.org/10.1016/j.dss.2020.113347)).
- **Missing events.** Rogge-Solti et al. repair missing events and timestamps "by combining stochastic Petri nets, alignments, and Bayesian networks," but they assume the process model is known ([Rogge-Solti et al. 2013](https://doi.org/10.1007/978-3-642-41033-8_89)).
- **Missing start times.** Fracca et al. impute them by simulating alternative activity-duration profiles ([Fracca et al. 2022](https://doi.org/10.1007/978-3-031-07472-1_17)).
- **Censoring.** Right-censored (still-open) cases appear only in predictive monitoring, where Baskharon et al. note that earlier methods "learn from complete traces" ([Baskharon et al. 2021](https://doi.org/10.1007/978-3-030-72693-5_8)).
- **Waiting time.** Queue mining treats delay as a resource effect, with "queues as first-class citizens" ([Senderovich et al. 2015](https://doi.org/10.1016/j.is.2015.03.010)). Lashkevich et al. decompose waiting time into named causes ([Lashkevich et al. 2023](https://doi.org/10.1007/978-3-031-34560-9_11)).

Decision mining admits that existing methods "assume that decision making is fully deterministic, and all factors influencing decisions are recorded," and learns overlapping rules instead ([Mannhardt et al. 2016](https://doi.org/10.1007/978-3-319-39696-5_23)). Data-aware stochastic Petri nets make routing probabilities functions of case attributes ([Mannhardt et al. 2023](https://doi.org/10.1007/978-3-031-33620-1_5)). Neither gives posterior uncertainty over the mined decision rules (guards).

Government applications supply a benchmark. **The BPI Challenge 2015 log contains "all building permit applications over a period of approximately four years" from five Dutch municipalities** ([van Dongen 2015](https://doi.org/10.4121/uuid:31a308ef-c844-48da-948c-305d167a0ec1)). Buijs, van Dongen & van der Aalst motivate configurable process models with exactly this case: "instead of discovering a process model per municipality, we want to discover one configurable process model showing commonalities and differences among the different variants" ([Buijs et al. 2013](https://doi.org/10.1007/978-3-642-40176-3_5)). That is the process-mining counterpart of a hierarchical model over jurisdictions implementing one statute, but it is fit by genetic search with no uncertainty quantification. No process-mining study of U.S. building, ADU or solar permitting was found.

The project should borrow the following:
- **Stochastic-language likelihoods**, simulated as in Cry et al. or computed exactly, for posterior predictive checks.
- **Configurable, hierarchical structure** across jurisdictions.
- **Queueing components kept separate from service durations.** This matches the project's existing rule of keeping elapsed waiting and elapsed service distinct.
- **Censored durations** for open permits.
- **Latent-branch inference** for correction loops that milestones never record, using EM or MCMC rather than classification. Ferreira & Gillblad's EM over latent case identifiers is a model ([Ferreira & Gillblad 2009](https://doi.org/10.1007/978-3-642-03848-8_11)).
- **Partial-order resolution** for tied or coarse milestone dates.

### Calibration tools exist for trees and model indices, not decision graphs (strand 8)

Simulation-based calibration (SBC) is the right core check, but its default form misses failures that structured posteriors produce.
- **Talts et al.** prove that, when computation is correct, the rank of any scalar f(θ) among posterior draws is uniform. A ∪-shaped rank histogram signals an underdispersed (overconfident) posterior. Their theory assumes continuous parameters ([Talts et al.](https://arxiv.org/abs/1804.06788)).
- **Modrák et al.** show that test quantities based on parameters alone "could never detect ... when the posterior is equal to the prior." Data-dependent test quantities fix this, and "the joint likelihood of the data is an especially useful test quantity." Ties from discrete parameters are broken by "choosing the rank randomly among the tied positions." They also show that SBC and the data-averaged-posterior check constrain different things, so either can pass while the other fails ([Modrák et al. 2025](https://arxiv.org/abs/2211.02383)).
- **For a discrete model index**, checking calibration of the posterior model probability against the true index (as a binary prediction) is "typically more sensitive" than SBC. The authors recommend "at least several hundred simulations" ([Modrák, Stroppel & Bürkner 2025](https://arxiv.org/abs/2508.11814)).

Phylogenetics is the working template for trees:
- Clade posterior probabilities have the correct frequentist meaning when the analysis model matches the generator, and are "much too large" when the model is under-specified ([Huelsenbeck & Rannala 2004](https://doi.org/10.1080/10635150490522629)).
- Mendes et al. validate tree models with 100 prior simulations, requiring 90–99 of them to fall inside 95% intervals. They handle trees through Robinson–Foulds distance to a *reference* phylogeny and through clade calibration. Rank-uniformity caught a misspecification that coverage missed ([Mendes et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11809579/)).
- Klawitter & Drummond define α-credible sets over discrete tree topologies and test whether they cover the true tree ([Klawitter & Drummond 2025](https://arxiv.org/abs/2505.14532)).

No paper was found that applies SBC to DAG or decision-graph posteriors.

Structure posteriors trap samplers, and standard diagnostics miss it:
- **DAG samplers.** Independent structure-MCMC runs give "very different estimates in the posterior probabilities of structural features" ([Friedman & Koller](https://ai.stanford.edu/~nir/Papers/FK1.pdf)). Runs "arrive at different plateaux, some of which are very far away from the global maximum" ([Kuipers & Moffa 2017](https://arxiv.org/abs/1504.05006)).
- **Trees.** Bayesian CART with only grow and prune moves **"cannot reach deep isolated signals in faster than exponential mixing time,"** while moves that attach or detach whole twigs mix polynomially ([Kim & Ročková](https://arxiv.org/abs/2306.00126)).
- **Effective sample size.** Weight-based ESS measures degeneracy among particles, not whether any particle reached a given mode; even as an estimate of ESS, the standard approximation is weak ([Elvira, Martino & Robert 2022](https://arxiv.org/abs/1809.04129)).
- **Stacking.** Stacking parallel runs is pragmatic but "not necessarily equivalent, even asymptotically, to fully Bayesian inference" ([Yao, Vehtari & Gelman 2022](https://jmlr.org/papers/v23/20-1426.html)).

Evaluation metrics also fail in exactly the regime that matters. Karimi Mamaghan et al. used exhaustive enumeration of DAGs with fewer than six nodes as the reference posterior. **With as few data points as nodes, the standard graph metrics (E-SHD, AUROC) had near-zero correlation with MMD to the true posterior**, and "the true posterior itself is evaluated to be worse on these metrics than their approximations" ([Karimi Mamaghan et al. 2024](https://proceedings.mlr.press/v235/karimi-mamaghan24a.html)). There are 29,281 labeled DAGs on five nodes ([OEIS A003024](https://oeis.org/A003024)), so exact enumeration is feasible only for small synthetic statutes.

Program-induction work offers no calibration precedent:
- Saad et al. give sufficient conditions for sound Bayesian synthesis of probabilistic programs, but validate by thresholded property probabilities and density estimation ([Saad et al. 2019](https://people.csail.mit.edu/rinard/paper/popl19.pdf)).
- Textual Bayes concedes that its Metropolis–Hastings sampler with LLM proposals "requires approximations, which will inevitably cause deviations from the true posterior" ([Ross et al. 2026](https://arxiv.org/abs/2506.10060)).

### Complexity metrics have never been tested against permit clocks (strand 9)

**Legal-complexity metrics** mostly measure size, hierarchy, cross-reference networks and linguistic entropy ([Katz & Bommarito 2014](https://doi.org/10.1007/s10506-014-9160-8); [Coupette et al. 2021](https://doi.org/10.3389/fphy.2021.658463)). Measures based on decision logic exist but have rarely been tested against outcomes. The exception is Colliard & Georg, whose computer-science measures of Basel I, Dodd–Frank and EBA rules were "tested using experiments and a survey on compliance costs" ([Colliard & Georg 2025](https://ideas.repec.org/a/eee/jfinec/v174y2025ics0304405x25001941.html)). Volume counts can fail outright: rising federal regulation measured by RegData "cannot explain secular trends in economic dynamism" ([Goldschlag & Tabarrok 2018](https://doi.org/10.1093/epolic/eix019)).

**Administrative-burden research** splits burden into learning, psychological and compliance costs ([Moynihan, Herd & Harvey 2015](https://doi.org/10.1093/jopart/muu009)). It identifies effects from changes in process, never from a measured complexity score of the rule text:
- Later SNAP recertification interview slots cut recertification success by 22% ([Homonoff & Somerville 2021](https://doi.org/10.1257/pol.20190272)).
- Closing Social Security field offices cut disability recipients by 16% but applications by only 10% ([Deshpande & Li 2019](https://doi.org/10.1257/pol.20180076)).

**Permitting evidence supplies priors on effect sizes.**

For rooftop solar:
- Across 44 California cities in 2011, the most streamlined permitting cut residential PV prices by $0.27–$0.77/W and **development times by about 24 days, 25% of the median**. The development-time models were "less robust" ([Dong & Wiser 2013](https://ideas.repec.org/a/eee/enepol/v63y2013icp531-542.html)).
- NREL's SolarTRACE data cover 22% of U.S. residential installs since 2017. A typical permit takes 1–2 weeks of review by the local permitting authority (from same-day to 6+ weeks), and contract-to-permission-to-operate times averaged 4.5–6 months in 2023 ([Cruce et al. 2025](https://www.osti.gov/biblio/3011864)).
- Nearly all SolarAPP+ permits are issued the same day, against a 7-day median for traditional permits. Median application-to-inspection time was 12 business days shorter in 2024 ([NLR 2026](https://www.osti.gov/biblio/3016084)). This is a descriptive contrast within adopting jurisdictions, with installers choosing which projects go through SolarAPP+, not a randomized effect.

For housing and ADUs:
- In Los Angeles, **by-right multifamily projects were permitted 28% faster than discretionary ones, with lower variance** ([Manville et al. 2023](https://doi.org/10.1080/01944363.2022.2106291)). In decision-tree terms, that is a single split at the root.
- Survey-based process indices are compromised. The Wharton index's Approval Delay Index is itself survey-reported review time: 3.7 months in the least-regulated quartile against 8.4 months in the most-regulated ([Gyourko, Hartley & Krimmel 2021](https://realestate.wharton.upenn.edu/wp-content/uploads/2022/04/w835.pdf)). Repeat surveys of the same California municipalities gave "strikingly different responses" ([Lewis & Marantz 2019](https://doi.org/10.1080/01944363.2019.1643253)). And "places with more development are more likely to report delays" ([Monkkonen, Lens & Manville 2020](https://ternercenter.berkeley.edu/wp-content/uploads/2023/04/MLM-Built-Out-Cities-2020.pdf)).
- Gov. Code §66317 requires a completeness decision within 15 business days and approval or denial within 60 days of a complete application ([leginfo §66317](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=66317&lawCode=GOV)). Yet HCD Annual Progress Report (APR) records show **mean application-to-permit times of 260 against 147 days inside and outside Los Angeles County's Coastal Zone, and 233 against 101 in Orange County**. Only about 29,000 of 60,000 ADU projects with valid permit dates also have application dates ([Underriner 2024](https://ternercenter.berkeley.edu/blog/adus-coastal-zone/)).

**The design consequence.** An exposure derived formally from the rule text escapes the reporting endogeneity that undermines survey indices. But state law makes the ADU and solar pathways nearly uniform: ADU review is ministerial, and §65850.5 requires nondiscretionary permits for solar ([leginfo §65850.5](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=65850.5&lawCode=GOV)). Variation across jurisdictions must therefore come from formalizing local ordinances, overlays and capacity, not the state statute alone. The notes describe SB 379's automated-permitting mandate and its reporting to the California Energy Commission only from search snippets of the [CEC page](https://www.energy.ca.gov/publications/2022/residential-solar-permit-reporting-senate-bill-379-sb-379-wiener-chapter-356), so those details need verification.

## The unclaimed object, and how far to trust "not found"

Stated precisely, the unclaimed object is a joint posterior over:
- a discrete decision model D: conditions, branches and exceptions over a fact space;
- a process model P_j for each jurisdiction: steps, orderings, correction loops, and waiting and service durations.

The posterior is conditioned on:
- several LLM formalizations, treated as correlated noisy readers;
- official documents, treated as readers with different failure modes;
- censored, milestone-only administrative timing records.

Its calibration is certified on synthetic statutes with planted truth. Each component has a nearest neighbor that stops one step short:

| Component | Nearest verified work | Where it stops |
|---|---|---|
| Posterior over a discrete legal structure | [Clark & Lauderdale 2012](https://doi.org/10.1093/pan/mps019); [Pang et al. 2012](https://doi.org/10.1093/pan/mps024) | A precedent genealogy and temporal regime breaks, not statutory conditions |
| Posterior over decision-rule structure | [Bayesian CART](https://doi.org/10.1080/01621459.1998.10473750); [Bayesian Rule Lists](https://doi.org/10.1214/15-aoas848) | Never applied to doctrine or eligibility; validated by accuracy, not coverage |
| Multiple formalizations as evidence | [Vernie & Grabmair 2026](https://arxiv.org/abs/2605.25186); [Graus 2026](https://arxiv.org/abs/2604.17153); [Witt et al. 2021](https://doi.org/10.1145/3462757.3466083) | Disagreement measured, never aggregated into a posterior |
| Correlated-reader aggregation | [Ising LLM judges](https://arxiv.org/abs/2601.22336); [Butts 2003](https://doi.org/10.1016/S0378-8733(02)00038-2) | Categorical labels, or independent readers of a structure; no coverage reported |
| Competing models weighted by fit | [Neil et al. 2019](https://doi.org/10.1007/s10506-019-09250-3) | Evidence models, not statutory logic |
| Posterior over a process model | [Cry et al. 2025](https://doi.org/10.1007/978-3-032-05792-1_22) | Weights only, on a fixed skeleton, from near-complete logs |
| Variants across jurisdictions | [Buijs et al. 2013](https://doi.org/10.1007/978-3-642-40176-3_5) | Genetic search, no uncertainty |
| Calibrating discrete-structure posteriors | [Mendes et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11809579/); [Modrák et al. 2025](https://arxiv.org/abs/2211.02383) | Phylogenetic trees and model indices, not decision graphs or posteriors built from LLM proposals |
| Linking complexity to timing | [Colliard & Georg 2025](https://ideas.repec.org/a/eee/jfinec/v174y2025ics0304405x25001941.html); [Dong & Wiser 2013](https://ideas.repec.org/a/eee/enepol/v63y2013icp531-542.html) | CS complexity measures tested against survey costs; process scores tested against time; never rule logic against processing time |

**These absence claims are weaker than they look.** Several researchers' web-search budgets, including one shared 200-call quota, ran out partway through. After that, discovery fell back to Crossref, OpenAlex, Semantic Scholar and arXiv API queries and direct PDF fetches. DBLP, Springer HTML and SSRN sat behind bot checks or returned 403 errors, and the researchers did not bypass them. Coverage is therefore thinnest exactly where a competing paper would most likely appear: ICAIL and JURIX 2024–2025 tables of contents, law reviews and SSRN, and machine-learning venues from 2020 on. Many 2025–2026 items cited here are arXiv preprints whose venues come from the authors' own comments. Figures marked † were read through an HTML summarizer and should be re-checked against the PDF before quotation.

Before the group asserts novelty, it should run these checks:

| Absence claim | Targeted check before claiming novelty |
|---|---|
| No Bayesian CART, BART or Bayesian Rule Lists applied to legal rules | Google Scholar sweep of those methods × court, sentencing, asylum, disability, benefits, administrative adjudication. Resolve the unverified Utah juvenile-justice BART dissertation and whether Dunn et al.'s 2017 asylum-prediction paper uses BART |
| No probabilistic aggregation of several LLM formalizations of one statute | Page-by-page scan of ICAIL 2025, JURIX 2024–2025, AI & Law 2024–2026 and NLLP |
| No SBC or coverage study of DAG, decision-graph or program posteriors | Search SBC × graph, DAG and structure learning. Open "Scaling Up Bayesian DAG Sampling" (PMLR v337) and BCD Nets, both unverified |
| No coverage or calibration study of crowdsourcing or LLM-judge posteriors | Search "calibration of crowdsourcing posteriors" and "coverage of truth inference" |
| No posterior over process-model structure; no discovery from interval-censored milestones | Retry the Hasselt record (handle 1942/49547) that returned HTTP 503; check the Pegoraro and Bazhenova dissertations |
| No joint estimate of ambiguity and delegated discretion | Targeted queries combining ambiguity, judge random effects and statutory text features; Fischman's panel-voting papers |
| No Hoff-type latent-space model (two or more dimensions) or Bayesian stochastic block model of case-citation networks | Resolve the unverified CJEU stochastic-block-model record ([arts.units.it](https://arts.units.it/handle/11368/3118138)) and Miller (2021), whose content is unverified |
| No study relating the decision-tree complexity of permit rules to processing time | Check State RegData, the World Bank construction-permit indicators and entitlement-timeline studies, none of which were verified |

## Design choices the literature already justifies

**Define the latent object behaviorally.** Three independent findings converge:
- Vernie & Grabmair's ρ = +0.09 between structural coverage and behavioral divergence.
- Graus's "structural similarity does not guarantee outcome equivalence."
- The welfare-benefit result that many structurally different rules reproduce the same decisions.

So the posterior should live over decision functions: behavior on the fact space, with distances between rules measured as the probability that they assign different outcomes under a distribution of fact patterns. It should not live over tree topology. Summarize the posterior by posterior-predictive disagreement on SAT-enumerated edge cases, and fix the predicate vocabulary before formalizing. Witt et al.'s agreed atoms and Graus's input/output constraints both cut spurious disagreement. Defining distance behaviorally is the notes' synthesis, not a claim made by any cited paper.

**Factor the decision model into elements before relying on reader identifiability.** The Allman–Matias–Rhodes bound requires at least three conditionally independent views per latent variable, and the number needed grows with the size of the latent space. Dendukuri & Joseph raise that to four once readers are dependent. Model each condition, branch and cross-reference as its own latent element in the Butts style, with hierarchical false-inclusion and false-omission rates per reader. Then reassemble a coherent decision model from the element marginals, for example by reparsing.

**Model reader dependence explicitly, and report it as a sensitivity analysis.**
- With three to five LLM readers, the dependence structure cannot be learned from the readings alone (Albert & Dodd), so the posterior will reflect whatever dependence is assumed.
- Fit conditional-independence, shared-latent-factor and Ising variants. Report the spread between them as the share of uncertainty that is not identified.
- Include an LLM consensus factor that official documents do not load on.
- Following V-Dem, collapse readings that share a model and prompt template into one observation.
- Anchor reader error rates with synthetic fact patterns of known outcome, used as anchoring vignettes.
- Budget expert adjudication knowing that cheaper judges can at most halve the gold labels needed (Dorner et al.).

This follows the project's existing rule that convergence is not identification.

**Expect outcome and timing data to be silent about conditions that cases never exercise.** Možina's sex condition and Steging's four-of-six result show that outcomes identify the decision function only where observed fact patterns fall, not the rule's structure. Peress's "only recover cutpoints" says the same thing for votes. A calibrated posterior should stay near its prior on unexercised conditions, where statute text and formalizations are the only information. Validation should test this directly by planting conditions in synthetic statutes that the simulated records never trigger.

**Report Fischman-style bounds where discretion and error are confounded.** Outcome and timing records alone cannot separate "the law left this open" from "this adjudicator got it wrong." So the deliverable should report an indeterminacy-error curve, or a posterior conditional on stated assumptions about the share of determinate cases. It should not report a single discretion estimate. Hangartner et al.'s bounds for extreme judges are the precedent for publishing bounds in place of forced point posteriors.

**Encode ambiguity and discretion as different parameters.**
- Code explicit delegation markers (the *Loper Bright* list, and Vannoni et al.'s parse-tree features) as a prior on jurisdiction-level variance, Var(u_j).
- Code genuine ambiguity as a mixture over discrete readings θ, which better readings can collapse.
- Treat vague evaluative standards conservatively as delegations.
- Keep intermediate legal concepts as nodes rather than flattening them (Canavotto & Horty).

The clustered-versus-continuous behavioral signature then becomes a model comparison the synthetic benchmark can test.

**Build SBC around test quantities suited to graphs.**
- Use per-gate and per-edge inclusion indicators, node count, depth and distance to a *fixed* reference graph. Never use distance to the true graph: it is zero at the truth by construction, so its rank is degenerate.
- Add the joint log-likelihood of the timing data and of the formalization data, which catches a posterior that simply returns the prior.
- Break ties at random.
- Check inclusion probabilities with reliability diagrams.
- Test whether α-credible sets of whole structures cover the true structure.
- Run several hundred simulations.
- On synthetic statutes with five or six decision nodes or fewer, enumerate the exact posterior and compare against it, rather than relying on E-SHD or AUROC.

**Treat disagreement between runs as non-convergence and fix the moves.** The SMC mode trapping the project has observed is what Kim & Ročková's exponential-mixing result predicts for local grow/prune rejuvenation. The literature supports these responses:
- Use larger moves: twig- or subtree-level moves, block-resampling a gate together with its downstream steps, or top-down SMC construction.
- Add tempering.
- Run four to eight independent runs, and compare their log-evidence and structural marginals with multi-sample ECDF bands.
- Label any stacked mixture as not exact Bayes.

When parameters the likelihood never touches drift from their priors, that is a failure of the Geweke or data-averaged-posterior type. It points to a missing Hastings or Jacobian term, or a mismatched SMC weight, in trans-dimensional moves. Gandy & Scott's exact unit tests can isolate which kernel is responsible ([Gandy & Scott](https://arxiv.org/abs/2001.06465); [Geweke 2004](https://doi.org/10.1198/016214504000001132)).

**Use LLMs as data, or as proposals whose density is known.** Textual Bayes shows that Metropolis–Hastings with intractable LLM proposal densities drifts from the true posterior. Using formalizations as noisy observations in the likelihood, or as independence proposals with computable density, keeps the target exact. Prompt format should enter as a nuisance effect: Baumann et al. find that "with just a handful of prompt paraphrases, virtually anything can be presented as statistically significant" ([Baumann et al. 2025](https://arxiv.org/abs/2509.08825)).

**Use BPI Challenge 2015 as a real-data recovery test.** Degrade the five-municipality Dutch building-permit log to milestone-only records (application, completeness, decision). Then test whether the latent-process posterior recovers each municipality's known structure and durations. This gives a ground-truth check on real administrative data that complements the synthetic statutes. The researchers did not check whether the log's attributes cleanly identify milestone events, so verify that first.

## A prioritized reading list

Priority 1 papers define the closest prior work and the hard limits. Priority 2 papers supply methods the build will reuse. Priority 3 papers frame interpretation and the link to burden. The verification column records what the researchers actually confirmed.

| # | Work | Why it matters here | Verification |
|---|---|---|---|
| 1 | Clark & Lauderdale, "Locating Supreme Court Opinions in Doctrine Space," *AJPS* 54(4):871–890 (2010) — [PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf) | The legal Hoff analogue: latent opinion positions, distance link, highest-density intervals, anchoring by assumption | Full text read |
| 2 | Clark & Lauderdale, "The Genealogy of Law," *Political Analysis* 20(3):329–350 (2012) — [PDF](https://www.tomclarkphd.com/files/ClarkLauderdalePA2012.pdf) | Posterior over a discrete legal tree; documents mode mixing | Full text read |
| 3 | Vernie & Grabmair, "By Their Fruits You Will Know Them," arXiv 2605.25186 (2026) — [arXiv](https://arxiv.org/abs/2605.25186) | Behavioral comparison of nine LLMs' formalizations; ρ = +0.09 | Full text read; preprint (EMNLP per arXiv comment); figures† |
| 4 | Fischman, "Measuring Inconsistency, Indeterminacy, and Error in Adjudication," *ALER* 16(1):40–85 (2014) — [DOI](https://doi.org/10.1093/aler/aht011) | Proves indeterminacy and error are only jointly bounded | Crossref metadata; content read in NBER draft; published figures unchecked |
| 5 | Možina, Žabkar, Bench-Capon & Bratko, "Argument Based Machine Learning Applied to Law," *AI & Law* 13(1):53–73 (2005/06) — [PDF](https://intranet.csc.liv.ac.uk/~tbc/publications/ArgumentBasedMachineLearningAp.pdf) | Accurate learners miss true conditions; unexercised conditions are unidentifiable | Full text read; volume year 2005 vs 2006 unresolved |
| 6 | Steging, Renooij & Verheij, "Discovering the Rationale of Decisions," ICAIL 2021 — [arXiv](https://arxiv.org/abs/2105.06758) | Four of six conditions give 98.95% accuracy; rationale unit tests | Full text read (arXiv); ICAIL DOI verified in one note, flagged unverified in another |
| 7 | Balasubramanian, Podkopaev & Kasiviswanathan, "Dependence-Aware Label Aggregation for LLM-as-a-Judge via Ising Models," arXiv 2601.22336 (2026) — [arXiv](https://arxiv.org/abs/2601.22336) | Why aggregation assuming conditional independence fails for correlated LLM readers | Full text read; ICML 2026 per Amazon Science blog |
| 8 | Dendukuri & Joseph, *Biometrics* 57(1):158–167 (2001) — [DOI](https://doi.org/10.1111/j.0006-341X.2001.00158.x); with Albert & Dodd, *Biometrics* 60(2):427–435 (2004) — [DOI](https://doi.org/10.1111/j.0006-341X.2004.00187.x) | Identifiability limits for dependent readers | Abstracts via Europe PMC |
| 9 | Butts, "Network Inference, Error, and Informant (In)accuracy: A Bayesian Approach," *Social Networks* 25(2):103–140 (2003) — [DOI](https://doi.org/10.1016/S0378-8733(02)00038-2) | Template for a latent structure read by error-prone informants | Crossref metadata; content from abstract and package documentation |
| 10 | Modrák et al., "Simulation-Based Calibration Checking for Bayesian Computation," *Bayesian Analysis* 20(2):461–488 (2025) — [arXiv](https://arxiv.org/abs/2211.02383) | Data-dependent test quantities; tie-breaking; prior-equals-posterior blind spot | Full text read |
| 11 | Mendes, Bouckaert, Carvalho & Drummond, "How to Validate a Bayesian Evolutionary Model," *Syst. Biol.* 74(1):158–175 (2025) — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11809579/) | Working protocol for calibrating tree posteriors | Full text read (PMC) |
| 12 | Pang, Friedman, Martin & Quinn, "Endogenous Jurisprudential Regimes," *Political Analysis* 20(4):417–436 (2012) — [DOI](https://doi.org/10.1093/pan/mps024) | Posterior over structure of the fact-to-outcome mapping | Abstract |
| 13 | Hangartner, Lauderdale & Spirig, "Inferring Individual Preferences from Group Decisions," *BJPolS* 55:e163 (2025) — [DOI](https://doi.org/10.1017/S0007123425100574) | Posterior over a latent decision procedure; bounds for extreme judges | Full text read |
| 14 | Letham, Rudin, McCormick & Madigan, "Interpretable Classifiers Using Rules and Bayesian Analysis," *AoAS* 9(3):1350–1371 (2015) — [DOI](https://doi.org/10.1214/15-aoas848) | Posterior over decision lists, the closest analogue to statutory gate logic | Abstract |
| 15 | Kim & Ročková, "On Mixing Rates for Bayesian CART," arXiv 2306.00126 — [arXiv](https://arxiv.org/abs/2306.00126) | Explains mode trapping under local moves; twig-level fix | Abstract; *EJS* 19 (2025) per UChicago repository record |
| 16 | Karimi Mamaghan et al., "Challenges and Considerations in the Evaluation of Bayesian Causal Discovery," ICML 2024 — [PMLR](https://proceedings.mlr.press/v235/karimi-mamaghan24a.html) | Proxy metrics fail in high-entropy regimes; use enumeration | Abstract and HTML full text |
| 17 | Marquardt & Pemstein, V-Dem WP 2017:41 — [PDF](https://v-dem.net/media/publications/v-dem_working_paper_2017_41.pdf); Pemstein et al., V-Dem WP 2026:21 — [PDF](https://v-dem.net/media/publications/wp21_2026.pdf) | Coverage under misspecified reader models; conservative collapsing of dependent readings | Full text read (working-paper versions) |
| 18 | Neil, Fenton, Lagnado & Gill, "Modelling Competing Legal Arguments Using Bayesian Model Comparison and Averaging," *AI & Law* 27(4):403–430 (2019) — [DOI](https://doi.org/10.1007/s10506-019-09250-3) | Model averaging over mutually inconsistent, independently built models | Abstract |
| 19 | Cry, Ballarini, Horváth & Le Gall, "Statistical Bayesian Inference for Stochastic Process Discovery," LNCS pp. 409–428 (2025) — [DOI](https://doi.org/10.1007/978-3-032-05792-1_22) | Closest process-mining posterior (weights on a fixed skeleton) | Abstract; arXiv record |
| 20 | Buijs, van Dongen & van der Aalst, "Mining Configurable Process Models from Collections of Event Logs," BPM 2013 — [DOI](https://doi.org/10.1007/978-3-642-40176-3_5); with van Dongen, BPI Challenge 2015 dataset — [DOI](https://doi.org/10.4121/uuid:31a308ef-c844-48da-948c-305d167a0ec1) | Variants across municipalities; a real building-permit benchmark | Abstract; DataCite metadata (schema not inspected) |
| 21 | *Loper Bright Enterprises v. Raimondo*, slip opinion (2024) — [PDF](https://www.supremecourt.gov/opinions/23pdf/22-451_7m58.pdf) | The doctrinal line between ambiguity and delegation; lexical delegation markers | Full text read; U.S. Reports page unverified |
| 22 | Farnsworth, Guzior & Malani, "Ambiguity About Ambiguity," *J. Legal Analysis* 2:257–300 (2010) — [OUP](https://academic.oup.com/jla/article-lookup/doi/10.1093/jla/2.1.257) | Elicitation design separating internal from external ambiguity | Publisher abstract |
| 23 | Witt, Huggins, Governatori & Buckley, "Converting Copyright Legislation into Machine-Executable Code," ICAIL 2021 — [DOI](https://doi.org/10.1145/3462757.3466083) | Human coders diverge; agreeing on atoms first helps | Abstract |
| 24 | Manville, Monkkonen, Gray & Phillips, "Does Discretion Delay Development?," *JAPA* 89(3):336–347 (2023) — [DOI](https://doi.org/10.1080/01944363.2022.2106291); with Colliard & Georg, "Measuring Regulatory Complexity," *JFE* 174:104186 (2025) — [RePEc](https://ideas.repec.org/a/eee/jfinec/v174y2025ics0304405x25001941.html) | Effect sizes for structural process differences; complexity measures validated against outcomes | Abstracts (RePEc) |

## Conclusion

The defensible contribution is narrower and stronger than "the first Bayesian model of law." Martin–Quinn, Clark–Lauderdale, Pang et al. and Hangartner et al. already put posteriors on legal quantities. What none of them does is move the latent object from *actors* to the *logic of the rule and its implementation*, or move validation from correlation with external scales to *coverage on planted truth*. That framing survives the search caveats better than a blanket novelty claim, because each missing piece has a named nearest neighbor.

The literature's sharper lesson is that identification, not computation, will bind first. Three unrelated fields reach the same conclusion: the welfare-benefit rule-recovery experiments, diagnostic-test latent-class theory and Fischman's partial identification of adjudication. Some of what the project wants to know is not in the data: conditions no case exercises, dependence among similar LLM readers, and whether a split decision reflects discretion or error. A calibrated posterior that stays wide in exactly those places, and says so across dependence assumptions, is the result to aim for, not a failure to fix. The ambiguity-versus-discretion question follows the same pattern. Doctrine draws the line clearly, outcome data blur it, and only design choices can recover it: variation in rule text, replication of identical cases, and elicitation that separates a reader's own confidence from expected disagreement.
