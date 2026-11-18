# Reader / measurement models for multiple noisy annotators, coders and LLM judges: correlated errors, structured latent truths, and posterior calibration

How I checked citations (as of 2026-10-05). For each item I confirmed the bibliographic metadata on a primary page: the Crossref DOI registry (publisher-deposited metadata), ACL Anthology, PMLR, JMLR, NeurIPS proceedings, arXiv, Europe PMC, or the V-Dem Institute. Statements about what a paper says come from its abstract or full text. Where I read the full text (V-Dem working papers, Paun et al. 2018, Passonneau & Carpenter 2014, Benoit et al. 2016, the Ising paper, Allman et al., Simpson & Gurevych, Jaffe et al., MACE, Sagae & Lavie), the note says so. Anything I could not check is marked **UNVERIFIED**. The web-search budget for this session ran out partway through, so later checks went straight to known DOI or arXiv pages.

## Q1. Classic latent-class annotator models and their identifiability

### Takeaway
The standard reader model is Dawid–Skene: each item has a latent class, each reader has a confusion matrix, and readers are conditionally independent (CI) given the class. Later work extends it in two ways: reader and item effects (GLAD, MACE, logistic random effects, Raykar), and hierarchical Bayesian pooling (Paun et al. 2018). Identifiability rests on Kruskal's 3-way tensor uniqueness theorem as generalized by Allman–Matias–Rhodes. You need at least three conditionally independent "views" that are informative enough. Even then the guarantee is only generic identifiability, up to label swapping. Every one of these guarantees depends on CI.

### Cited Findings
- **Dawid & Skene (1979)**, "Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm," *JRSS Series C (Applied Statistics)* 28(1):20–28. The model estimates an error rate for each observer even when the patient's "true" response is unavailable. EM is described as "a slow but sure way" to reach the MLE. — [RePEc/IDEAS](https://ideas.repec.org/a/bla/jorssc/v28y1979i1p20-28.html); metadata confirmed via [Crossref DOI 10.2307/2346806](https://doi.org/10.2307/2346806)
- **Raykar, Yu, Zhao, Valadez, Florin, Bogoni & Moy (2010)**, "Learning From Crowds," *JMLR* 11:1297–1322. It is a probabilistic approach to supervised learning when several annotators give noisy labels and there is no gold standard. The algorithm evaluates the experts and estimates the hidden labels, learning the classifier jointly with them. — [JMLR](https://jmlr.org/papers/v11/raykar10a.html)
- **Whitehill, Wu, Bergsma, Movellan & Ruvolo (2009)**, "Whose Vote Should Count More: Optimal Integration of Labels from Labelers of Unknown Expertise," *NIPS 22*. It infers image labels, labeler expertise and "the difficulty of each image" at the same time (the GLAD model). It is robust to adversarial and noisy labelers and beats majority vote. — [NeurIPS proceedings](https://papers.nips.cc/paper_files/paper/2009/hash/f899139df5e1059396431415e770c6dd-Abstract.html)
- **Hovy, Berg-Kirkpatrick, Vaswani & Hovy (2013)**, "Learning Whom to Trust with MACE," *NAACL-HLT 2013*, pp. 1120–1130. MACE is an item-response model that learns without supervision which annotators are trustworthy and what the correct labels are. Adding a prior and using Variational Bayes improves the trustworthiness estimates. Accuracy goes up further "by focusing on the instances our model is most confident in (trading in some recall)" and by adding annotated control instances (full text read). — [ACL Anthology N13-1132](https://aclanthology.org/N13-1132/)
- **Passonneau & Carpenter (2014)**, "The Benefits of a Model of Annotation," *TACL* 2:311–326 (full text read).
  - Standard agreement measures are "neither necessary nor sufficient" for corpus quality.
  - A Dawid–Skene model on crowd labels gives a certainty measure for every gold label, at less than half the cost of trained annotators.
  - Agreement-in-error is a known failure: "hard-to-identify names have correlated false negatives among annotators."
  - "Confidence intervals must be expanded as correlation among annotator responses increases due to item-level effects such as difficulty or subject matter."
  - — [ACL Anthology Q14-1025](https://aclanthology.org/Q14-1025/)
- **Paun, Carpenter, Chamberlain, Hovy, Kruschwitz & Poesio (2018)**, "Comparing Bayesian Models of Annotation," *TACL* 6:571–585 (full text read).
  - Six models are compared: pooled Multinomial; unpooled Dawid–Skene and MACE; partially pooled hierarchical D&S, item-difficulty, and logistic random effects (Carpenter 2008).
  - Models with annotator structure "came out on top in all evaluations."
  - Unpooled models match partially pooled ones against gold but "can overfit, affecting their predictive performance."
  - Ignoring annotator structure (pooled, item-difficulty-only, majority vote) generally does poorly.
  - Label switching "makes the models nonidentifiable" for MCMC convergence checks.
  - — [ACL Anthology Q18-1040](https://aclanthology.org/Q18-1040/)
- **Kim & Ghahramani (2012)**, "Bayesian Classifier Combination" (IBCC), *AISTATS*, PMLR 22:619–627. It is a Bayesian treatment of the Dawid–Skene model, fit by MCMC, that "explicitly models the relationship between each model's output and the unknown true label." It works with non-probabilistic sources, including humans. — [PMLR](https://proceedings.mlr.press/v22/kim12.html)
- **Zhang, Chen, Zhou & Jordan (2016)**, "Spectral Methods Meet EM: A Provably Optimal Algorithm for Crowdsourcing," *JMLR* 17(102):1–44. A spectral initialization followed by EM on the Dawid–Skene objective "achieves the optimal convergence rate up to a logarithmic factor." This addresses the problem that the D–S likelihood is non-convex. — [JMLR](https://jmlr.org/papers/v17/14-511.html)
- **Kruskal (1977)**, "Three-way arrays: rank and uniqueness of trilinear decompositions, with application to arithmetic complexity and statistics," *Linear Algebra and its Applications* 18(2):95–138. Uniqueness holds when the k-ranks of the three factor matrices sum to at least 2r + 2. — [Crossref DOI 10.1016/0024-3795(77)90069-6](https://doi.org/10.1016/0024-3795(77)90069-6)
- **Allman, Matias & Rhodes (2009)**, "Identifiability of parameters in latent structure models with many observed variables," *Annals of Statistics* 37(6A):3099–3132.
  - Kruskal's theorem "lies at the core" of their results.
  - In the parametric setting "generic identifiability holds" (the non-identifiable set has measure zero), so the classical definition of identifiability is "typically too strong."
  - Theorem 4: for p ≥ 3 conditionally independent observed variables, if there is a split into three groups with min(r,κ1)+min(r,κ2)+min(r,κ3) ≥ 2r+2, the parameters are generically identifiable up to label swapping.
  - Corollary 5: an r-class mixture of p Bernoulli products is generically identifiable if p ≥ 2⌈log₂ r⌉ + 1.
  - Read the full text on arXiv; — [arXiv 0809.5032](https://arxiv.org/abs/0809.5032); [Crossref DOI 10.1214/09-AOS689](https://doi.org/10.1214/09-AOS689)
- **Hui & Walter (1980)**, "Estimating the Error Rates of Diagnostic Tests," *Biometrics* 36(1):167. If two tests are applied to two populations with different prevalences, and the tests' errors are assumed conditionally independent, then both tests' error rates and both prevalences can be estimated by ML. — [Crossref DOI 10.2307/2530508](https://doi.org/10.2307/2530508) (abstract via Europe PMC, PMID 7370371)
- **Pepe & Janes (2007)**, "Insights into latent class analysis of diagnostic test performance," *Biostatistics* 8(2):474–484. With 3 tests under CI there is a closed-form MLE. It shows how observed 2- and 3-way associations identify prevalence and error rates. "Although interesting and reasonable under CI, the estimators clearly have no basis when it fails." — [Crossref DOI 10.1093/biostatistics/kxl038](https://doi.org/10.1093/biostatistics/kxl038) (abstract via Europe PMC)
- **Jones, Johnson, Hanson & Christensen (2010)**, "Identifiability of Models for Multiple Diagnostic Testing in the Absence of a Gold Standard," *Biometrics* 66(3):855–863. "It is commonly believed that if the degrees of freedom in the data meet or exceed the number of parameters ... then the model is identifiable. Goodman (1974) established that this was not the case." They extend Goodman's technique with geometric arguments about non-identifiable models. — [Crossref DOI 10.1111/j.1541-0420.2009.01330.x](https://doi.org/10.1111/j.1541-0420.2009.01330.x) (abstract via Europe PMC, PMID 19764953)

### Inferences
- In our setting there are a few LLM formalizations plus the official documents, and the latent truth is a decision model. The Kruskal/Allman guarantee needs at least three views that are conditionally independent given the latent truth. LLM readers almost certainly violate this (see Q2). So identifiability of reader error rates is not guaranteed, even though the parameter count suggests it should be (Jones et al.).
- Allman's bound shows that the number of informative views needed grows with the size of the latent space, roughly log₂(r) for binary readings. For a structured latent object with many possible configurations, CI-based identifiability needs either many views or a factorization into small local latent variables. Each local variable (for example one condition or one branch of the decision tree) needs its own ≥3 informative, conditionally independent readings.
- Paun et al. found that partial pooling helps prediction. Hierarchical reader parameters, shared across many statutory elements, are the natural default when each reader contributes one reading per element.

### Gaps
- I found no identifiability theorem for Dawid–Skene-type models where the latent class is a combinatorial structure (a tree or program) rather than a categorical variable. One would have to reduce to per-element latent classes.
- Carpenter (2008), "Multilevel Bayesian models of categorical data annotation," is cited by Paun et al. as the source of the logistic random-effects model. It is a technical report and I did not verify it independently (**UNVERIFIED**).

## Q2. Models for correlated annotators and dependent errors, including LLM judges

### Takeaway
There is a mature literature on conditional dependence among readers. Diagnostic-test latent class models use random effects and dependence terms, crowdsourcing has worker-correlation models, weak supervision has dependency-structure learning, and as of ICML 2026 there are Ising models for LLM judges. The strongest robust finding: with few readers, the dependence structure is weakly identified or not identified at all. Likelihood comparisons cannot tell competing dependence structures apart. Misspecifying the structure biases the estimates. Bayesian dependence models are then prior-driven and give wider intervals. Empirically, LLM errors are strongly correlated, more so for larger and more accurate models, so agreement among LLM readers is weak evidence of correctness.

### Cited Findings
**Dependence-aware aggregation and identifiability under dependence**
- **Balasubramanian, Podkopaev & Kasiviswanathan**, "Dependence-Aware Label Aggregation for LLM-as-a-Judge via Ising Models," arXiv 2601.22336 (submitted 2026-01-29). Amazon Science says it was presented at ICML 2026. — [arXiv](https://arxiv.org/abs/2601.22336); venue per [Amazon Science blog](https://www.amazon.science/blog/when-llm-judges-agree-should-we-believe-them). I read the full text.
  - Shared data, architectures, prompts and failure modes break CI. "Ignoring such dependencies can yield miscalibrated posteriors and even confidently incorrect predictions."
  - It defines a hierarchy: CI ⊂ class-independent Ising ⊂ class-dependent Ising, plus a latent-factor model in which judges are CI given (Y, Z) with Z a shared latent factor.
    - With class-dependent couplings, the Bayes log-odds is quadratic in the votes.
    - With class-independent couplings, it reduces to a linear weighted vote with correlation-adjusted weights.
  - There are finite-K examples where CI methods "flip the Bayes label despite matching per-annotator marginals."
  - Separation results show CI methods "remain strictly suboptimal as the number of judges grows, incurring nonvanishing excess risk under latent factors." In other words, adding more correlated judges does not rescue a CI model.
  - Fitting is "purely unsupervised" EM. The authors say it integrates with prediction-powered inference.
  - Six judges were used: Claude Sonnet 4.5, Claude Haiku 4.5, gpt-oss-120b, Llama 4 Maverick, Llama 4 Scout, DeepSeek-R1.
  - Test accuracy, class-dependent Ising vs CI weighted majority vote:

    | Task (dataset) | Class-dependent Ising | CI weighted majority vote |
    |---|---|---|
    | Relevance (WikiQA) | 0.90 | 0.82 |
    | Toxicity (Jigsaw) | 0.79 | 0.72 |
    | Summarization (CNN/DailyMail-derived) | 0.68 | 0.61 |

  - **No ECE, Brier or coverage metrics are reported.** The authors recommend "predictive calibration on small labeled validation sets" as a diagnostic for choosing the level of dependence.
  - The blog's framing: "Ten correlated votes should not always produce the same confidence as 10 independent votes."
- **Qu, Tan & Kutner (1996)**, "Random Effects Models in Latent Class Analysis for Evaluating Accuracy of Diagnostic Tests," *Biometrics* 52(3):797. It builds a latent class model with random effects to capture conditional dependence among multiple tests "(or readers)." It also offers a graphical method to check whether dependence matters and what its pattern is. — [Crossref DOI 10.2307/2533043](https://doi.org/10.2307/2533043) (abstract via Europe PMC, PMID 8805757)
- **Dendukuri & Joseph (2001)**, "Bayesian Approaches to Modeling the Conditional Dependence Between Multiple Diagnostic Tests," *Biometrics* 57(1):158–167.
  - Classical inference with conditional dependence "requires that results from at least four different tests be used in order to obtain an identifiable solution."
  - With fewer tests, "the posterior distributions are strongly dependent on the prior information ... even with large sample sizes."
  - Unless the correlation is known a priori, the method gives "adjusted inferences that incorporate all of the uncertainty ... typically resulting in wider interval estimates."
  - — [Crossref DOI 10.1111/j.0006-341X.2001.00158.x](https://doi.org/10.1111/j.0006-341X.2001.00158.x) (abstract via Europe PMC, PMID 11252592)
- **Albert & Dodd (2004)**, "A Cautionary Note on the Robustness of Latent Class Models for Estimating Diagnostic Error without a Gold Standard," *Biometrics* 60(2):427–435. When the conditional dependence is misspecified, the estimates of sensitivity, specificity and prevalence "can be biased." "With small numbers of tests, likelihood comparisons and other model diagnostics may not be able to distinguish between models with different dependence structures." Asymptotic results show the problem is general. — [Crossref DOI 10.1111/j.0006-341X.2004.00187.x](https://doi.org/10.1111/j.0006-341X.2004.00187.x) (abstract via Europe PMC, PMID 15180668)
- **Li, Rubinstein & Cohn (2019)**, "Exploiting Worker Correlation for Label Aggregation in Crowdsourcing" (EBCC), *ICML*, PMLR 97:3886–3895. A mixture of intra-class reliabilities, "connected to tensor decomposition and item clustering," induces correlation between workers. Inference is mean-field variational. EBCC had the highest mean accuracy against 10 baselines on 17 datasets. — [PMLR](https://proceedings.mlr.press/v97/li19i.html)
- **Venanzi, Guiver, Kazai, Kohli & Shokouhi (2014)**, "Community-based Bayesian aggregation models for crowdsourcing," *WWW 2014*, pp. 155–164. Workers are clustered into communities that share confusion matrices. — [Crossref DOI 10.1145/2566486.2567989](https://doi.org/10.1145/2566486.2567989) (metadata verified; the content summary is from the title only)
- **Welinder, Branson, Perona & Belongie (2010)**, "The Multidimensional Wisdom of Crowds," *NeurIPS 2010*, pp. 2424–2432. Annotators and items are embedded in a shared Euclidean space. Each annotator is "a multidimensional entity with variables representing competence, expertise and bias," which lets the model discover annotator groups ("schools of thought"). This is the closest crowdsourcing analogue to Hoff–Raftery–Handcock latent-space modeling. — [ML Anthology](https://mlanthology.org/neurips/2010/welinder2010neurips-multidimensional/) / [NeurIPS PDF](https://proceedings.neurips.cc/paper_files/paper/2010/file/0f9cafd014db7a619ddb4276af0d692c-Paper.pdf)
- **Hoff, Raftery & Handcock (2002)**, "Latent Space Approaches to Social Network Analysis," *JASA* 97(460):1090–1098. This is the motivating analogy. — [Crossref DOI 10.1198/016214502388618906](https://doi.org/10.1198/016214502388618906)
- **Jaffe, Fetaya, Nadler, Jiang & Kluger (2016)**, "Unsupervised Ensemble Learning with Dependent Classifiers," *AISTATS*, PMLR 51:351–360. When CI is violated, CI-based ensemble learners "can be severely sub-optimal." The paper gives unsupervised methods to "detect strongly dependent classifiers," estimate their accuracies better, and build a better meta-learner. Under CI, the conditional covariance structure of the classifiers is constrained, and violations of that structure are the signal used for detection (full text read). — [PMLR](https://proceedings.mlr.press/v51/jaffe16.html); [arXiv 1510.05830](https://arxiv.org/abs/1510.05830)
- **Parisi, Strino, Nadler & Kluger (2014)**, "Ranking and combining multiple predictors without labeled data," *PNAS* 111(4):1253–1258. This is the spectral meta-learner under CI that Jaffe et al. extend. — [Crossref DOI 10.1073/pnas.1219097111](https://doi.org/10.1073/pnas.1219097111)
- **Platanios, Dubey & Mitchell (2016)**, "Estimating Accuracy from Unlabeled Data: A Bayesian Approach," *ICML*, PMLR 48:1416–1425. It estimates classifier accuracies from unlabeled data alone, to "within a few percent of the true accuracy," using the relationship between agreement patterns and error rates. — [PMLR](https://proceedings.mlr.press/v48/platanios16.html)
- **Weak supervision dependency structure.**
  - **Bach, He, Ratner & Ré (2017)**, *ICML*, PMLR 70:273–282, learns dependency structure among labeling functions without labels via ℓ1-regularized marginal pseudolikelihood. The unlabeled data needed "scales sublinearly in the number of possible dependencies." — [PMLR](https://proceedings.mlr.press/v70/bach17a.html)
  - **Varma, Sala, He, Ratner & Ré (2019)**, *ICML*, PMLR 97:6418–6427, use robust PCA for structure learning and give an information-theoretic lower bound on sample complexity. They report up to 4.64 F1 over methods that assume conditionally independent sources. — [PMLR](https://proceedings.mlr.press/v97/varma19a.html)
  - **Fu, Chen, Sala, Hooper, Fatahalian & Ré (2020)**, "Fast and Three-rious," *ICML*, PMLR 119:3280–3291, give a closed-form triplet estimator for a class of latent variable models. It has generalization bounds "without assuming that the latent variable model can exactly parameterize the underlying data distribution." — [PMLR](https://proceedings.mlr.press/v119/fu20a.html)

**Empirical evidence that LLM errors are correlated, so agreement does not imply correctness**
- **Kim, Garg, Peng & Garg (2025)**, "Correlated Errors in Large Language Models," *ICML 2025*, PMLR 267. They studied more than 350 LLMs. "On one leaderboard dataset, models agree 60% of the time when both models err." "Larger and more accurate models have highly correlated errors, even with distinct architectures and providers." They show downstream effects on LLM-as-judge evaluation and on hiring (algorithmic monoculture). — [PMLR](https://proceedings.mlr.press/v267/kim25e.html); [arXiv 2506.07962](https://arxiv.org/abs/2506.07962)
- **Goel, Struber, Auzina, Chandra, Kumaraguru, Kiela, Prabhu, Bethge & Geiping (2025)**, "Great Models Think Alike and this Undermines AI Oversight," *ICML 2025*, PMLR 267:19621–19678. They propose CAPA, a chance-adjusted agreement measure on mistakes. "LLM-as-a-judge scores favor models similar to the judge." "Model mistakes are becoming more similar with increasing capabilities, pointing to risks from correlated failures." — [PMLR](https://proceedings.mlr.press/v267/goel25b.html); [arXiv 2502.04313](https://arxiv.org/abs/2502.04313)
- **Panickssery, Bowman & Feng (2024)**, "LLM Evaluators Recognize and Favor Their Own Generations." There is "a linear correlation between self-recognition capability and the strength of self-preference bias." — [arXiv 2404.13076](https://arxiv.org/abs/2404.13076). The NeurIPS 2024 venue is **UNVERIFIED**; the arXiv page I fetched did not show it.
- **Verga et al. (2024)**, "Replacing Judges with Juries" (PoLL). A panel of smaller models from disjoint families outperforms a single large judge, "exhibits less intra-model bias," and costs more than 7x less. — [arXiv 2404.18796](https://arxiv.org/abs/2404.18796)
- **Thakur, Choudhary, Ramayapally, Vaidyanathan & Hupkes**, "Judging the Judges," *GEM 2025 workshop*. Only the best and largest of 13 judges reach reasonable alignment with humans, and they still fall well short of inter-human agreement. "Judges with high percent agreement can still assign vastly different scores." Judges show leniency. — [arXiv 2406.12624](https://arxiv.org/abs/2406.12624)
- **Bavaresco et al.**, "LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks" (JUDGE-BENCH), *ACL 2025*. Across 11 LLMs, reliability varies "depending on the property being evaluated, the expertise level of the human judges, and whether the language is human or model-generated." LLMs "should be carefully validated against human judgments before being used as evaluators." — [arXiv 2406.18403](https://arxiv.org/abs/2406.18403)

**"LLMs as annotators" (2023–2026): accuracy and the validity of downstream inference**
- **Gilardi, Alizadeh & Kubli (2023)**, *PNAS* 120(30). On 6,183 tweets and news articles, ChatGPT's zero-shot accuracy beat crowd workers by about 25 points on average. Its intercoder agreement exceeded both crowd workers and trained annotators, at under $0.003 per annotation. — [Crossref DOI 10.1073/pnas.2305016120](https://doi.org/10.1073/pnas.2305016120) (abstract via Europe PMC)
- **Ziems, Held, Shaikh, Chen, Zhang & Yang (2024)**, *Computational Linguistics* 50(1):237–291. On 25 computational social science benchmarks with 13 models, LLMs "fail to outperform the best fine-tuned models but still achieve fair levels of agreement with humans." The authors recommend using them as zero-shot annotators on human teams. — [ACL Anthology](https://aclanthology.org/2024.cl-1.8/)
- **Baumann, Röttger, Urman, Wendsjö, Plaza-del-Arco, Gruber & Hovy (2025)**, "Large Language Model Hacking." They replicated 37 tasks from 21 studies, with 13M labels from 18 LLMs and 2,361 hypotheses. About 31% of hypotheses reached incorrect conclusions with state-of-the-art LLMs, and about half with small models. "With just a handful of prompt paraphrases, virtually anything can be presented as statistically significant." Human annotations are the critical safeguard. — [arXiv 2509.08825](https://arxiv.org/abs/2509.08825)
- **Calderon, Reichart & Dror (2025)**, "The Alternative Annotator Test for LLM-as-a-Judge," *ACL 2025*, pp. 16051–16081. It is a statistical test of whether an LLM can replace human annotators, using a modest annotated subset. On 10 datasets and 6 LLMs, closed models such as GPT-4o "can sometimes" replace humans. — [arXiv 2501.10970](https://arxiv.org/abs/2501.10970); [ACL Anthology 2025.acl-long.782](https://preview.aclanthology.org/setup/2025.acl-long.782)
- **Egami, Hinck, Stewart & Wei (2023)**, "Using Imperfect Surrogates for Downstream Inference: Design-based Supervised Learning," *NeurIPS 2023*. A doubly-robust estimator combines LLM surrogate labels with gold labels sampled by design. It guarantees "asymptotic unbiasedness and proper uncertainty quantification" even when the surrogates are arbitrarily biased. — [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d862f7f5445255090de13b825b880d59-Abstract.html)
- **Angelopoulos, Bates, Fannjiang, Jordan & Zrnic (2023)**, "Prediction-powered inference," *Science* 382(6671):669–674. It gives provably valid confidence intervals for means, quantiles and regression coefficients from a small gold set plus ML predictions, "without making any assumptions on the machine-learning algorithm." — [Crossref DOI 10.1126/science.adi6000](https://doi.org/10.1126/science.adi6000); [arXiv 2301.09633](https://arxiv.org/abs/2301.09633)
- **Gligorić, Zrnic, Lee, Candès & Jurafsky (2025)**, "Can Unconfident LLM Annotations Be Used for Confident Conclusions?," *NAACL 2025*. Confidence-driven inference uses LLM confidence to choose which items get human labels. It keeps validity and cuts the human labels needed by more than 25%. — [ACL Anthology](https://aclanthology.org/2025.naacl-long.179)
- **Dorner, Nastl & Hardt (2025)**, "Limits to scalable evaluation at the frontier: LLM as Judge won't beat twice the data," *ICLR 2025*. "When the judge is no more accurate than the evaluated model, no debiasing method can decrease the required amount of ground truth labels by more than half." Real savings fall short even of that bound. — [arXiv 2410.13341](https://arxiv.org/abs/2410.13341)
- **Ludwig, Mullainathan & Rambachan (2024/2025)**, "Large Language Models: An Applied Econometric Framework." For measurement problems, valid inference "requires combining LLM outputs with a small validation sample." "Absent a validation sample ... seemingly innocuous choices (which model, which prompt) can produce dramatically different parameter estimates." — [arXiv 2412.07031](https://arxiv.org/abs/2412.07031)

### Inferences
- Taken together, Albert & Dodd, Dendukuri & Joseph, and the Ising paper's separation results suggest that a model of 3–5 LLM readers of one statute cannot learn reader dependence from the readings alone. The posterior over the latent decision model will reflect the assumed dependence structure (or its prior), and that should be reported as a sensitivity analysis, not hidden.
- Ways to rebuild identifying power:
  - **Labeled anchors.** A small set of statute elements with an expert-adjudicated reading, as in the PPI/DSL/alt-test designs. This also gives the calibration check the Ising authors recommend.
  - **Structurally different readers.** Different model families and prompts, and especially the official documents, which have different failure modes. Kim et al. and Goel et al. show that same-provider or similarly capable models are not independent.
  - **A shared latent "LLM consensus factor".** In the spirit of Qu et al.'s random effects and the Ising paper's latent-factor model, add a factor Z that all LLM readers load on but the official documents do not. That lets the data separate "LLMs agree with each other" from "LLMs agree with the documents."
  - **Readers in a latent space.** In the Hoff/Welinder style, position LLM readers so that nearby readers count as partially redundant.
- Dorner et al. bound the gain from cheaper judges. If LLM readers are no more accurate than the target, human-adjudicated anchors can be cut by at most half. Budget expert review accordingly.

### Gaps
- I found no study that measures the *coverage or calibration* of dependence-aware aggregation posteriors (Ising, EBCC, Jaffe et al.) against ground truth. The Ising paper reports only accuracy.
- I found no work that applies correlated-reader models to *LLM formalizations of legal text*. The closest evidence is general LLM-judge and annotation studies.
- I could not verify independently the details of Carpenter's and others' "multilevel" correlated-reader models in Stan. The Stan User's Guide "data coding models" page appeared in search results but was not fetched.

## Q3. Aggregating structured (non-scalar) outputs from multiple annotators

### Takeaway
There are four families of methods:
1. **Sequence models**: HMM-style models with reader-specific (sometimes sequential) confusion (Nguyen 2017; Simpson & Gurevych 2019; Rodrigues 2014).
2. **Task-specific structure models**: coreference mention pairs (Paun 2018b), and latent networks with per-informant false-positive and false-negative rates (Butts 2003; Young–Cantwell–Newman 2020), which are the closest analogue to a latent graph or decision structure.
3. **Distance-based, task-agnostic models**: these model distances between annotations rather than the annotations themselves, and cover parses, rankings, translations and boxes (Braylan & Lease 2020/2021; Braylan et al. 2023).
4. **Ensemble combination methods**: these produce a consensus structure but have no reader-error model (parser reparsing; self-consistency, semantic-entropy clustering and behavior-based program clustering for LLM outputs).

None of the four handles correlated readers of a structured object.

### Cited Findings
- **Nguyen, Wallace, Li, Nenkova & Lease (2017)**, "Aggregating and Predicting Sequence Labels from Crowd Annotations," *ACL 2017*, pp. 299–309. An HMM variant aggregates crowd sequence labels (HMM-Crowd), and an LSTM predicts sequences. It is evaluated on news NER and biomedical information extraction. — [ACL Anthology P17-1028](https://aclanthology.org/P17-1028/)
- **Simpson & Gurevych (2019)**, "A Bayesian Approach for Sequence Tagging with Crowds," *EMNLP-IJCNLP 2019*, pp. 1093–1104. Bayesian sequence combination models "sequential dependencies between the annotations as well as the ground-truth labels." It accounts for uncertainty from sparse annotators. It is evaluated with span F1 and with token-level cross-entropy error (log-loss), which "evaluates the quality of the probability estimates ... as it penalises over-confident mistakes more heavily" (full text read). — [ACL Anthology D19-1101](https://aclanthology.org/D19-1101/); [arXiv 1811.00780](https://arxiv.org/abs/1811.00780)
- **Rodrigues, Pereira & Ribeiro (2014)**, "Sequence labeling with multiple annotators," *Machine Learning* 95(2):165–181. — [Crossref DOI 10.1007/s10994-013-5411-2](https://doi.org/10.1007/s10994-013-5411-2) (metadata only)
- **Paun, Chamberlain, Kruschwitz, Yu & Poesio (2018)**, "A Probabilistic Annotation Model for Crowdsourcing Coreference," *EMNLP 2018*. It aggregates crowdsourced anaphoric annotations. It is evaluated on mention-pair accuracy and on silver chains, which come out "of comparable quality to expert annotation." — [ACL Anthology D18-1218](https://aclanthology.org/D18-1218/)
- **Braylan & Lease (2020)**, "Modeling and Aggregation of Complex Annotations via Annotation Distances," *WWW 2020*, pp. 1807–1818. It models distances between labels instead of the labels. The approach is agnostic to the distance function, and reader reliability is estimated from distances to peers or gold. — [Crossref DOI 10.1145/3366423.3380250](https://doi.org/10.1145/3366423.3380250)
- **Braylan & Lease (2021)**, "Aggregating Complex Annotations via Merging and Matching," *KDD 2021*, pp. 86–94. — [Crossref DOI 10.1145/3447548.3467411](https://doi.org/10.1145/3447548.3467411) (metadata only)
- **Braylan, Marabella, Alonso & Lease (2023)**, "A General Model for Aggregating Annotations Across Simple, Complex, and Multi-Object Annotation Tasks," *JAIR* 78:901–973. A "task-agnostic method to model distances between labels" covers "sequence labeling, translation, syntactic parsing, ranking, bounding boxes, and keypoints." It adds a semi-supervised variant and "unit tests" for checking that an aggregation model is correctly specified. — [arXiv 2312.13437](https://arxiv.org/abs/2312.13437)
- **Butts (2003)**, "Network inference, error, and informant (in)accuracy: a Bayesian approach," *Social Networks* 25(2):103–140. A fully Bayesian network inference with exponential-family (ERGM-type) priors on the latent structure and informant-level error rates with beta priors. Multiple informants each report on a latent network. — [Crossref DOI 10.1016/S0378-8733(02)00038-2](https://doi.org/10.1016/S0378-8733(02)00038-2); implementation `bbnam` in the R package [sna](https://cran.r-project.org/web/packages/sna/refman/sna.html)
- **Young, Cantwell & Newman (2020/2021)**, "Bayesian inference of network structure from unreliable data," *Journal of Complex Networks* 8(6). It reconstructs networks from data "in any format," with substantial measurement error "when the nature and magnitude of that error is unknown." — [Crossref DOI 10.1093/comnet/cnaa046](https://doi.org/10.1093/comnet/cnaa046); [arXiv 2008.03334](https://arxiv.org/abs/2008.03334)
- **Newman (2018)**, "Network structure from rich but noisy data," *Nature Physics* 14(6):542–545. — [Crossref DOI 10.1038/s41567-018-0076-1](https://doi.org/10.1038/s41567-018-0076-1) (metadata only)
- **Chen, Bennett, Collins-Thompson & Horvitz (2013)**, "Pairwise ranking aggregation in a crowdsourced setting," *WSDM 2013*, pp. 193–202. This is the structured case of rankings. — [Crossref DOI 10.1145/2433396.2433420](https://doi.org/10.1145/2433396.2433420) (metadata only)
- **Sagae & Lavie (2006)**, "Parser Combination by Reparsing," *HLT-NAACL 2006 short papers*, pp. 129–132. Sentences are reparsed using the analyses of several parsers, for both dependency and constituent parsing. The result beats the best individual parser on WSJ. This is a way to guarantee that the consensus structure is well-formed (full text read). — [ACL Anthology N06-2033](https://aclanthology.org/N06-2033/)
- **Li et al. (2016)**, "A Survey on Truth Discovery," *SIGKDD Explorations* 17(2):1–16. This is the database and web-mining branch that estimates source reliability and the true value of each claim jointly. — [Crossref DOI 10.1145/2897350.2897352](https://doi.org/10.1145/2897350.2897352) (metadata only)
- **Aggregating LLM structured outputs without a reader model.**
  - Self-consistency (Wang et al., *ICLR 2023*) "samples a diverse set of reasoning paths ... and then selects the most consistent answer by marginalizing out the sampled reasoning paths." — [arXiv 2203.11171](https://arxiv.org/abs/2203.11171)
  - Semantic entropy (Kuhn, Gal & Farquhar, *ICLR 2023*; Farquhar, Kossen, Kuhn & Gal, *Nature* 630:625–630, 2024) clusters sampled generations into meaning-equivalence classes by bidirectional entailment, without supervision, and uses the entropy over clusters as uncertainty. — [arXiv 2302.09664](https://arxiv.org/abs/2302.09664); [Crossref DOI 10.1038/s41586-024-07421-0](https://doi.org/10.1038/s41586-024-07421-0)
  - AlphaCode (Li et al., *Science* 378:1092–1097, 2022) uses "large-scale model sampling ... followed by filtering based on program behavior to a small set of submissions." — [arXiv 2203.07814](https://arxiv.org/abs/2203.07814); [Crossref DOI 10.1126/science.abq1158](https://doi.org/10.1126/science.abq1158)

### Inferences
- The best template for a latent decision model read by several LLMs is the Butts / Young–Cantwell–Newman design:
  - a prior over the structured object, with each element (condition, branch, outcome, cross-reference) treated like an edge;
  - reader-specific false-inclusion and false-omission rates for each element;
  - a hierarchical prior on reader error rates.

  The Ising or latent-factor layer from Q2 can then sit on top, coupling readers' element-level errors.
- Formalizations will differ in surface form. Program equivalence (behavioral agreement on test fact patterns, as in AlphaCode clustering) or semantic-equivalence clustering (semantic entropy) defines when two readers "agree." A Braylan-style distance model can then use behavioral distance between decision models as the observation. This avoids writing a separate model for every structure type, at the cost of interpretability of each element.
- Sagae & Lavie's reparsing (and MBR-style combination in general) shows how to recover a single well-formed consensus structure from element-level posteriors. That matters if the marginal posteriors of each element combine into an incoherent decision model.
- Self-consistency and semantic entropy treat samples from one model as exchangeable draws. By Q2's evidence they will understate uncertainty when the samples share a failure mode. They measure the reader's own uncertainty, not error relative to the latent truth.

### Gaps
- I found no paper that aggregates crowdsourced or multi-annotator *parse trees* with a reader-error model, as opposed to ensemble parser combination. Braylan et al. (2023) say they cover syntactic parsing via distances, but I did not read their parsing experiments in detail.
- I found no correlated-annotator model for structured outputs. Every structured-aggregation paper above assumes readers are CI given the latent structure.
- I did not find literature specific to aggregating *multiple formalizations of legal rules or programs* into a posterior over the latent rule.

## Q4. Political science scaling of coder judgments (crowd-sourced text analysis, expert-survey IRT, V-Dem)

### Takeaway
Political science models coder error with ordinal IRT / multi-rater ordinal probit:
- a reliability (discrimination or error-variance) parameter for each coder;
- coder-specific thresholds, to handle differential item functioning (DIF);
- anchoring vignettes and bridge or lateral coders, to tie the thresholds together across contexts.

Coders are assumed conditionally independent given the latent trait. V-Dem says explicitly that this assumption is violated by temporally correlated coder errors. Its defense is a deliberately conservative choice of observation granularity that widens the intervals. Validation is mostly by convergent validity (correlation with expert surveys) plus simulation studies of recovery and HPD coverage.

### Cited Findings
- **Benoit, Conway, Lauderdale, Laver & Mikhaylov (2016)**, "Crowd-sourced Text Analysis: Reproducible and Agile Production of Political Data," *APSR* 110(2):278–295 (full text read).
  - Crowd workers' readings of manifesto sentences give results "comparable to those using experts."
  - The aggregation model is an IRT model with reader effects and sentence difficulty. Sentence positions are hierarchical within document positions, and "Simulating from the posterior also makes it straightforward to estimate Bayesian credible intervals."
  - Footnote 12: treating the choices as independent, under a logit, assumes IIA, and "it is not possible to identify a more general model that relaxes these assumptions without asking additional questions of readers."
  - Document positions from the scaling model correlate 0.96 (economic) and 0.97 (social) with the simple mean of means.
  - Lin's concordance between crowd and expert aggregates is 0.95 (economic) and 0.84 (social).
  - The number of crowd judgments needed per sentence was set by bootstrapping 100 subsamples for n = 1…20 workers from oversampled manifestos (at least 20 judgments per sentence).
  - — [Crossref DOI 10.1017/S0003055416000058](https://doi.org/10.1017/S0003055416000058); [LSE Research Online](https://eprints.lse.ac.uk/62242)
- **Marquardt & Pemstein (2018)**, "IRT Models for Expert-Coded Panel Data," *Political Analysis* 26(4):431–456. IRT beats simple averages when experts vary in reliability and show DIF, and is "generally robust" without them. — [Crossref DOI 10.1017/pan.2018.28](https://doi.org/10.1017/pan.2018.28). Simulation details are from the January 2017 working-paper version, which I read in full: [V-Dem WP 2017:41](https://v-dem.net/media/publications/v-dem_working_paper_2017_41.pdf).
- **Pemstein, Marquardt, Tzelgov, Wang, Medzihorsky, Krusell, Miri & von Römer**, "The V–Dem Measurement Model: Latent Variable Analysis for Cross-National and Cross-Temporal Expert-Coded Data," V-Dem Working Paper 2026:21 (March 2026 edition; full text read).
  - About five experts rate each country-year and "each of these raters works independently."
  - The model is written as multi-rater ordinal probit or ordinal IRT (citing Johnson & Albert 1999; Pemstein, Meserve & Melton 2010; Clinton & Lewis 2008; Treier & Jackman 2008). Each rater has a reliability σ_r or discrimination β_r and rater-specific thresholds τ_r for DIF.
  - It "largely assumes away the potential for systematic rater biases that are not covered by varying thresholds."
  - "Temporal dependence in rater errors violates the assumption described by Equation 2" (conditional independence). Treating ratings as yearly "could cause the model to produce estimates of uncertainty that are too liberal (too certain)."
  - Their fix: "we treat any stretch of time ... in which no expert provides two differing ratings as a single observation." This "yields the largest possible estimates of uncertainty." They admit it is "probably too conservative."
  - Cross-national comparability comes from bridge coders, lateral coders (treated as vignettes), and anchoring vignettes fielded since 2016. Vignettes get priors at even intervals between −1.5 and 1.5 on the latent scale. About 20% of the worst-performing vignettes were rewritten in the 2018 update.
  - They reject dynamic IRT priors as "inherently optimistic about model uncertainty."
  - — [V-Dem WP 2026:21](https://v-dem.net/media/publications/wp21_2026.pdf); [GUPEA record](https://gupea.ub.gu.se/handle/2077/67993)
- **Marquardt, Pemstein, Seim & Wang (2019)**, "What makes experts reliable? Expert reliability and the estimation of latent traits," *Research & Politics* 6(4). In coder-level data for six variables, there is little consistent relationship between most expert characteristics (including gender) and the model-estimated reliability. Attentive, confident experts with contextual knowledge are more reliable. — [Crossref DOI 10.1177/2053168019879561](https://doi.org/10.1177/2053168019879561)
- **Marquardt & Pemstein (2023)**, "Estimating latent traits from expert surveys: an analysis of sensitivity to data-generating process," *PSRM* 11(2):384–393.
  - They simulate under different data-generating processes and assess "(1) recover true values and (2) construct appropriate coverage intervals."
  - Hierarchical A–M and IRT beat the mean when expert error is high, and "IRT models are often more likely to include true values within their coverage intervals."
  - "The median and non-hierarchical latent variable models perform poorly under most assumed DGPs."
  - — [Crossref DOI 10.1017/psrm.2021.39](https://doi.org/10.1017/psrm.2021.39)
- **Lindstädt, Proksch & Slapin (2020)**, "When Experts Disagree: Response Aggregation and its Consequences in Expert Surveys," *PSRM* 8(3):580–588. Monte Carlo results say "it is better to aggregate expert responses using the median or modal response, rather than the mean." — [Crossref DOI 10.1017/psrm.2018.52](https://doi.org/10.1017/psrm.2018.52). **Conflicts with** Marquardt & Pemstein (2023), who find the median "perform[s] poorly under most assumed DGPs." The difference probably comes from the assumed DGP.
- **Pemstein, Meserve & Melton (2010)**, "Democratic Compromise: A Latent Variable Analysis of Ten Measures of Regime Type," *Political Analysis* 18(4):426–449. It treats 10 existing democracy indices as raters in a Bayesian latent variable model (the Unified Democracy Scores). The result is "at least as reliable as the most reliable component measure" and "accompanied by quantitative estimates of uncertainty." This is the closest political-science analogue to treating several *instruments* (LLM readers plus documents) as raters. — [Crossref DOI 10.1093/pan/mpq020](https://doi.org/10.1093/pan/mpq020)
- **Other ordinal IRT and expert-coding antecedents** (metadata confirmed; the role of each is as described in the V-Dem WP):
  - Clinton & Lewis (2008), "Expert Opinion, Agency Characteristics, and Agency Preferences," *Political Analysis* 16(1):3–20. — [Crossref DOI 10.1093/pan/mpm009](https://doi.org/10.1093/pan/mpm009)
  - Treier & Jackman (2008), "Democracy as a Latent Variable," *AJPS* 52(1):201–217. — [Crossref DOI 10.1111/j.1540-5907.2007.00308.x](https://doi.org/10.1111/j.1540-5907.2007.00308.x)
  - Fariss (2014), "Respect for Human Rights has Improved Over Time: Modeling the Changing Standard of Accountability," *APSR* 108(2):297–318. V-Dem cites it on raters applying different thresholds in different contexts. — [Crossref DOI 10.1017/S0003055414000070](https://doi.org/10.1017/S0003055414000070)
  - Anchoring vignettes: King & Wand (2007), *Political Analysis* 15(1):46–66, [DOI 10.1093/pan/mpl011](https://doi.org/10.1093/pan/mpl011); Bakker, Jolly, Polk & Poole (2014), "The European Common Space: Extending the Use of Anchoring Vignettes," *Journal of Politics* 76(4):1089–1101, [DOI 10.1017/S0022381614000449](https://doi.org/10.1017/S0022381614000449).

### Inferences
- V-Dem's "regime" collapse maps directly onto LLM readers. If several LLM formalizations come from the same model, prompt template, or upstream summary, a conservative default is to treat them as one observation (or one cluster with a shared random effect). Otherwise apparent inter-reader agreement will inflate the reliability estimates and shrink the intervals, which is the exact mechanism V-Dem describes.
- Anchoring vignettes translate naturally to synthetic fact patterns with known statutory outcomes. Every LLM reader evaluates them, which pins down reader-specific thresholds and error rates the way vignettes do in V-Dem. The project's synthetic/toy-statute work could supply these.
- UDS (Pemstein et al. 2010) is a precedent for treating heterogeneous instruments (here, official documents and different LLMs) as raters, each with its own reliability. It is also a precedent for reporting posterior uncertainty for every case.

### Gaps
- I did not find a political-science expert-coding model that explicitly models *cross-coder* correlated errors, such as shared ideological bias among coders of one country. V-Dem handles systematic shifts only through threshold offsets and says so.
- I did not check whether the published *Political Analysis* 2018 version of Marquardt & Pemstein keeps the HPD-coverage tables of the 2017 working paper.

## Q5. Evidence on whether these posteriors are calibrated, and how calibration was checked

### Takeaway
Direct coverage evidence is thin and comes mostly from political-science simulation studies. There, nominal 95% HPD intervals cover close to 95% only when the fitted model matches the data-generating process. Coverage falls to roughly 0.5–0.85 under misspecified reliability or DIF. In crowdsourcing and NLP, "calibration" is usually checked indirectly: held-out predictive log density, token log-loss, or accuracy after filtering low-confidence items. Diagnostic-test theory predicts that CI models with correlated readers will be overconfident. Dependence models with few readers will be prior-dominated and wide. I found no coverage study for LLM-judge aggregation posteriors.

### Cited Findings
- **V-Dem / Marquardt & Pemstein simulation coverage** (WP 2017:41, Appendix E.4 tables, full text read). The share of country-year 95% HPD intervals that contain the true value, by data-generating process and fitted model:

  | Data-generating process | Fitted model | Coverage |
  |---|---|---|
  | No DIF, fixed reliability | Fixed-reliability model | 0.95 |
  | No DIF, reliability ~ N(1,1) | Fixed-reliability model | 0.84 |
  | No DIF, reliability ~ N(1,1) | Expert-specific reliability model | 0.93 |
  | Threshold DIF ~ N(0,1) | Various models | 0.76–0.87 |
  | Intercept DIF ~ N(0,1) | Models with expert-specific reliability but no DIF term | ~0.48–0.54 |

  The models were run with 8 chains × 10,000 iterations, and convergence was judged by Gelman–Rubin. — [V-Dem WP 2017:41](https://v-dem.net/media/publications/v-dem_working_paper_2017_41.pdf)
- **Marquardt & Pemstein (2023).** Coverage was an explicit evaluation criterion. "IRT models are often more likely to include true values within their coverage intervals" than hierarchical A–M. — [DOI 10.1017/psrm.2021.39](https://doi.org/10.1017/psrm.2021.39)
- **V-Dem measurement model (2026).** The main calibration risk named is dependence in coder errors. Fine-grained observation units would make uncertainty "too liberal (too certain)," so the granularity is chosen to give "the largest possible estimates of uncertainty." — [V-Dem WP 2026:21](https://v-dem.net/media/publications/wp21_2026.pdf)
- **Paun et al. (2018).**
  - They state that "for a well-specified model ... Bayesian inference provides optimally calibrated inferences," and that for "only roughly accurate models, calibration may be measured for model comparison (Gneiting et al., 2007)."
  - In practice they compared models by held-out predictive log density (citing Piironen & Vehtari 2017 and Vehtari et al. 2017), and by accuracy as low-entropy posterior items are filtered out ("filtering out the items with low confidence improves the accuracy of all the models").
  - I found no reliability diagram or coverage table in the text.
  - — [TACL Q18-1040](https://aclanthology.org/Q18-1040/)
- **Passonneau & Carpenter (2014).**
  - With 20–25 crowd labels per item, 81%–97% of items (depending on the word) had posterior probability ≥ 0.99 for the estimated label.
  - They note that the intervals widen if items are not independent, and must widen as annotator correlation rises.
  - They say full Bayes would quantify estimation uncertainty, which is "substantial for the data sizes discussed here."
  - I found no external calibration check against held-out gold.
  - — [TACL Q14-1025](https://aclanthology.org/Q14-1025/)
- **Simpson & Gurevych (2019).** Token-level cross-entropy (log-loss) is used to score the probability estimates of the aggregation methods, alongside F1. — [ACL D19-1101](https://aclanthology.org/D19-1101/)
- **Hovy et al. (2013, MACE).** Restricting to the most confident instances raises accuracy, which shows the confidence ranking is useful, though it is not a calibration test. — [ACL N13-1132](https://aclanthology.org/N13-1132/)
- **Dendukuri & Joseph (2001).** Modeling dependence honestly with fewer than four tests gives prior-driven posteriors and "typically ... wider interval estimates." — [DOI 10.1111/j.0006-341X.2001.00158.x](https://doi.org/10.1111/j.0006-341X.2001.00158.x)
- **Albert & Dodd (2004).** Misspecified dependence biases the estimates, and model diagnostics cannot detect it with few tests. Coverage under misspecification therefore cannot be checked from the data alone. — [DOI 10.1111/j.0006-341X.2004.00187.x](https://doi.org/10.1111/j.0006-341X.2004.00187.x)
- **Balasubramanian et al. (2026).** The paper reports that CI "can yield miscalibrated posteriors and even confidently incorrect predictions" and argues it theoretically. It reports no calibration metric, and recommends "predictive calibration on small labeled validation sets." — [arXiv 2601.22336](https://arxiv.org/abs/2601.22336)
- **Frequentist alternatives with guaranteed coverage** require a gold subset: PPI ([Science](https://doi.org/10.1126/science.adi6000)), DSL ([NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d862f7f5445255090de13b825b880d59-Abstract.html)), confidence-driven inference ([NAACL 2025](https://aclanthology.org/2025.naacl-long.179)), and the alt-test ([arXiv 2501.10970](https://arxiv.org/abs/2501.10970)).
- **Simulation-based calibration (SBC).** Talts, Betancourt, Simpson, Vehtari & Gelman, arXiv 1804.06788, use rank statistics of prior draws within posterior samples to identify "inaccurate computation and inconsistencies in model implementations." — [arXiv 1804.06788](https://arxiv.org/abs/1804.06788)
- **Braylan et al. (2023).** They propose "unit tests" for checking that an aggregation model is correctly specified. — [arXiv 2312.13437](https://arxiv.org/abs/2312.13437)

### Inferences
- A defensible calibration protocol for the project would combine three checks:
  1. **SBC** of the reader model, to check computation. SBC only certifies the posterior under the model's own assumptions.
  2. **Misspecification simulations** in the V-Dem 2017 style. Generate readings with correlated reader errors (shared latent factor, Ising couplings, and DIF-like reader-specific thresholds), fit the CI model and the dependence-aware models, and report 50/80/95% coverage for each element of the latent decision model.
  3. **Out-of-model coverage** on a held-out set of expert-adjudicated statute elements or synthetic fact patterns with known outcomes. This is the PPI/DSL logic, and the only check Albert & Dodd's result leaves standing.
- From the V-Dem tables, expect a CI reader model to undercover badly when readers share failure modes, not mildly. A coverage drop from 0.95 to about 0.5 is plausible when the misspecified component (there, intercept DIF; here, shared LLM bias) affects every reader of a case in the same direction.
- Reporting a separate posterior for each dependence assumption (CI; latent factor; Ising), as Albert & Dodd's non-identifiability implies, is more honest than one posterior. The spread between them is a direct measure of how much of the uncertainty is identifiable.

### Gaps
- I found no published calibration or coverage evaluation of Dawid–Skene, MACE, IBCC or EBCC posteriors against gold labels (reliability diagrams or ECE) in the sources reviewed. It may exist in papers I did not reach.
- I found no coverage evaluation for any aggregation of LLM judges or LLM annotators with a latent-truth posterior. The 2023–2026 LLM-annotation literature uses design-based frequentist corrections (PPI, DSL), not posterior calibration of a latent reader model.
- The search budget ran out before I could search directly for "calibration of crowdsourcing posteriors" or for "coverage of Bayesian truth inference." Those searches are worth running in a follow-up.
