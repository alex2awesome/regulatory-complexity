# Modeling legal rules as functions of case facts: case-space models, fact-pattern analysis, tree/rule classifiers, and Bayesian structure uncertainty

Verification legend used below. **[V-abs]** means I checked the claim against the publisher, repository or arXiv abstract, or against full text I retrieved. **[V-bib]** means I verified only the bibliographic record (title, authors, venue, year, DOI) through the Crossref, OpenAlex or arXiv API; any description beyond the title comes from my own background knowledge and is labelled. **[UNVERIFIED]** means I could not confirm it against a primary page.

Process note for the report writer: this session's shared WebSearch budget ran out partway through the work. After that I checked citations only by fetching publisher, DOI, arXiv, Crossref, OpenAlex and Semantic Scholar records for works I already knew about. As a result, the claims that something does not exist (for example, "no Bayesian-tree application to legal doctrine found") rest on a narrower search than I would like. They are flagged in Gaps.

---

## Q1. Fact-pattern and case-space tradition (Kort, Segal, Lax, Kornhauser, Cameron & Kornhauser, Kastellec, Beim/Hirsch/Kastellec): what do they estimate, and how is uncertainty handled?

### Takeaway
The empirical fact-pattern tradition (Kort 1957, Segal 1984, the jurisprudential-regimes work, Kastellec 2010, and the forecasting work) estimates one mapping from coded case facts to outcomes: a weighted formula, a probit or logit, or a single classification tree. The analyst fixes the structure in advance (which facts, what functional form). Uncertainty is reported only as parameter standard errors or predictive accuracy. Two partial exceptions put structural uncertainty in time rather than in the logic of the rule:
- Pang, Friedman, Martin & Quinn (2012) give a Bayesian posterior over the number and location of regime change-points.
- Lax & Rader (2010) use a randomization test for structural breaks.

The theoretical case-space literature (Kornhauser; Lax; Cameron & Kornhauser; Callander & Clark; Baker & Mezzetti; Beim) does treat the rule itself (a partition of case space) as unknown and learned case by case. It is formal theory, though, not an estimator.

### Cited Findings
**Foundational empirical fact-pattern work**
- **Kort (1957)**, "Predicting Supreme Court Decisions Mathematically: A Quantitative Analysis of the 'Right to Counsel' Cases," *APSR* 51(1):1–12 [V-bib]. Kort identified factual elements in state right-to-counsel cases (for example, youth of the defendant, absence of counsel at various stages, coercion to plead guilty), assigned them numerical values with a formula derived from decided cases, and predicted the remaining cases. — [Cambridge abstract page](https://resolve.cambridge.org/core/journals/american-political-science-review/article/abs/predicting-supreme-court-decisions-mathematically-a-quantitative-analysis-of-the-right-to-counsel-cases/5446CD6450A211885AB6A0AAFCCF17C6); [DOI 10.2307/1951767](https://doi.org/10.2307/1951767). The factor list comes from a search-result summary, not the article text.
- **Segal (1984)**, "Predicting Supreme Court Cases Probabilistically: The Search and Seizure Cases, 1962–1981," *APSR* 78(4):891–900 [V-abs].
  - The "legal model" uses variables for the prior justification of the search, the nature of the intrusion, and "a few mitigating circumstances" to explain reasonableness decisions.
  - "The parameters are estimated through probit." The cases are "much more ordered than had commonly been believed," and the Court acts more favorably toward the federal government than toward the states.
  - Source: [Crossref/APSR record, DOI 10.2307/1955796](https://doi.org/10.2307/1955796).
  - Secondary summaries say the model predicted 76% of decisions and explained 57% of the variance, and that the article won the Wadsworth Award (2002). These figures are **not verified against the article**. — [Wikipedia: Jeffrey A. Segal](https://en.wikipedia.org/wiki/Jeffrey_A._Segal)
- **George & Epstein (1992)**, "On the Nature of Supreme Court Decision Making," *APSR* 86(2):323–337 [V-bib]. From background knowledge (not checked): it combines legal and extralegal factors in one fact-based model. — [DOI 10.2307/1964223](https://doi.org/10.2307/1964223)
- **Wahlbeck (1997)**, "The Life of the Law: Judicial Politics and Legal Change," *Journal of Politics* 59(3):778–802 [V-bib]. From background knowledge: it models expansion and contraction of legal rules. — [DOI 10.2307/2998637](https://doi.org/10.2307/2998637)

**Jurisprudential regimes (structural change in the fact-to-outcome mapping)**
- **Richards & Kritzer (2002)**, "Jurisprudential Regimes in Supreme Court Decision Making," *APSR* 96(2):305–320 [V-abs]. Jurisprudential regimes "identify relevant case factors and/or set the level of scrutiny or balancing the justices will use." The candidate regime is content-neutrality in free expression, tested with "a series of statistical tests using logistic regression." — [DOI 10.1017/s0003055402000187](https://doi.org/10.1017/s0003055402000187). A follow-up treats the Lemon regime in Establishment Clause cases (Kritzer & Richards 2003, *Law & Society Review* 37(4):827–840) [V-bib]. — [DOI](https://doi.org/10.1046/j.0023-9216.2003.03704005.x)
- **Lax & Rader (2010)**, "Legal Constraints on Supreme Court Decision Making: Do Jurisprudential Regimes Exist?," *Journal of Politics* 72(2):273–284 [V-bib]. The critique, from a summary: the standard regime test assumes votes are independent although they cluster by case and by term; the authors use a nonparametric randomization test and find "little evidence that precedents affect voting." — [DOI 10.1017/s0022381609990855](https://doi.org/10.1017/s0022381609990855); [summary](https://pollux-fid.de/r/sw-4ef41e3cc8508a91)
- **Pang, Friedman, Martin & Quinn (2012)**, "Endogenous Jurisprudential Regimes," *Political Analysis* 20(4):417–436 [V-abs].
  - Method: "a multivariate multiple change-point probit model ... estimating the locations of many possible change-points along with structural parameters ... using Markov chain Monte Carlo methods, and use Bayesian model comparison to determine the number of change-points."
  - This is the clearest case in this literature of a **posterior over the structure** of the fact-to-outcome mapping, but the structure is temporal (where the coefficient vector changes), not which conditions or branches enter.
  - Sources: [Cambridge page](https://www.cambridge.org/core/journals/political-analysis/article/endogenous-jurisprudential-regimes/7F85B6DDCA6FEBDD35C4C67025A6028A); [DOI 10.1093/pan/mps024](https://doi.org/10.1093/pan/mps024)

**Case-space theory (rules as partitions of fact-filled cases)**
- **Kornhauser (1992)**, "Modeling Collegial Courts I: Path-Dependence," *International Review of Law and Economics* 12(2):169–185 [V-bib]. — [DOI 10.1016/0144-8188(92)90034-o](https://doi.org/10.1016/0144-8188(92)90034-o)
  - The companion "Modeling Collegial Courts II: Legal Doctrine" (usually cited as *JLEO* 8 (1992)) is **[UNVERIFIED]**: Crossref did not return it.
- **Kornhauser (2009)**, "Modeling Courts," in M. D. White (ed.), *Theoretical Foundations of Law and Economics* (Cambridge UP) [V-abs]: "Policy space models treat policies as fundamental and cases as nonexistent. Models grounded in case space, by contrast, take cases as fundamental; policies are described in terms of case dispositions." — [NYU faculty page](https://gretchen.law.nyu.edu/fac-chapt/1025)
- **Lax (2007)**, "Constructing Legal Rules on Appellate Courts," *APSR* 101(3):591–604 [V-abs]. It uses "a 'case-space' model to show that there will exist a collegial rule that captures majoritarian preferences, and ... a median rule even if there is no single median judge." It also studies how appellate review and separate opinions affect the stability and enforceability of rules. — [DOI 10.1017/s0003055407070347](https://doi.org/10.1017/s0003055407070347)
- **Lax (2011)**, "The New Judicial Politics of Legal Doctrine," *Annual Review of Political Science* 14:131–157 [V-abs]: the case-space model "allows for ideological differences between judges while expressing those differences in terms of legal rules that partition fact-filled legal cases into different dispositions." It focuses on collegiality and hierarchy. — [DOI 10.1146/annurev.polisci.042108.134842](https://doi.org/10.1146/annurev.polisci.042108.134842)
- **Lax (2012)**, "Political Constraints on Legal Doctrine: How Hierarchy Shapes the Law," *JOP* 74(3):765–781 [V-bib]. — [DOI](https://doi.org/10.1017/s002238161200045x)
- **Jacobi & Tiller (2007)**, "Legal Doctrine and Political Control," *JLEO* 23(2):326–345 [V-bib]. — [DOI](https://doi.org/10.1093/jleo/ewm022)
- **Cameron & Kornhauser**, "Modeling Collegial Courts (3): Adjudication Equilibria," SSRN 2009, revised 2012 [V-bib]. — [SSRN DOI](https://doi.org/10.2139/ssrn.1400838)
- **Cameron & Kornhauser (2023)**, "Learning the Law Together: Judges, Litigants, and Case-by-Case Adjudication," *JITE* 179(1):65–87 [V-abs].
  - "A judge hearing cases learns partial information about the best legal rule, gradually partitioning the case space." Doctrine is "path dependent but displays strong limit properties, converging to the best legal rule."
  - With costly information, judges may stop learning early, leaving "residual uncertainty in the law and some cases wrongly decided."
  - Sources: [Mohr Siebeck](https://www.mohrsiebeck.com/en/article/learning-the-law-together-judges-litigants-and-case-by-case-adjudication-101628jite-2023-0001); [DOI 10.1628/jite-2023-0001](https://doi.org/10.1628/jite-2023-0001)
- **Callander & Clark (2017)**, "Precedent and Doctrine in a Complicated World," *APSR* 111(1):184–203 [V-abs]. Judges "must simultaneously learn about (1) the particular facts and legal implications of any dispute; (2) discover the doctrine that appropriately resolves the dispute; and (3) attempt to articulate those rules in the context of a single case." The authors propose "a model of judicial learning ... in which there is a complicated relationship between facts and legal outcomes." — [DOI 10.1017/s0003055416000587](https://doi.org/10.1017/s0003055416000587)
- **Baker & Mezzetti (2012)**, "A Theory of Rational Jurisprudence," *JPE* 120(3):513–551 [V-abs]. A decision maker either investigates a new problem or decides "on the basis of similarity with precedent problems"; the law "may converge to efficient or inefficient rules," and "with positive probability, identical cases are treated differently." — [DOI 10.1086/666655](https://doi.org/10.1086/666655)
- **Beim (2017)**, "Learning in the Judicial Hierarchy," *JOP* 79(2):591–604 [V-abs]. The Supreme Court "learns to craft legal rules by relying on the Courts of Appeals as laboratories of law," and can draw inferences even from cases it chooses not to review. — [DOI 10.1086/688442](https://doi.org/10.1086/688442)
- **Beim, Hirsch & Kastellec (2014)**, "Whistleblowing and Compliance in the Judicial Hierarchy," *AJPS* 58(4):904–918 [V-abs from summary]. In this formal model a whistleblower can, at some cost, signal lower-court noncompliance. Whistleblowing is most informative when rare; past a point it reduces compliance; a "perfect ally" whistleblower blows the whistle too often. — [ISPS page](https://isps.yale.edu/research/publications/isps14-013); [DOI 10.1111/ajps.12108](https://doi.org/10.1111/ajps.12108)
- **Clark & Kastellec (2013)**, "The Supreme Court and Percolation in the Lower Courts: An Optimal Stopping Model," *JOP* 75(1):150–168 [V-bib]. — [DOI](https://doi.org/10.1017/s002238161200093x)
- Other formal models of rule development [V-bib]:
  - Bueno de Mesquita & Stephenson (2002), "Informative Precedent and Intrajudicial Communication," *APSR* 96(4):755–766 — [DOI](https://doi.org/10.1017/s0003055402000436)
  - Gennaioli & Shleifer (2007), "The Evolution of Common Law," *JPE* 115(1):43–68 — [DOI](https://doi.org/10.1086/511996)
  - Ellison & Holden, "A Theory of Rule Development," *JLEO* 30(4):649–682 (online 2013) — [DOI](https://doi.org/10.1093/jleo/ewt016)
  - Fox & Vanberg, "Narrow versus Broad Judicial Decisions," *JTP* 26(3):355–383 (online 2013) — [DOI](https://doi.org/10.1177/0951629813502709)
- **Niblett, Posner & Shleifer (2010)**, "The Evolution of a Legal Rule," *Journal of Legal Studies* 39(2):325–358 [V-abs]. This is an empirical rule-evolution study: "461 state court appellate decisions involving the economic loss rule in construction disputes," 1970–2005. "The law did not converge to any stable resting point and evolved differently in different states." — [DOI 10.1086/652908](https://doi.org/10.1086/652908)

**Classification trees of legal rules and tree-based forecasting**
- **Kastellec (2010)**, "The Statistical Analysis of Judicial Decisions and Legal Rules with Classification Trees," *JELS* 7(2):202–230 [V-abs].
  - "A key question in the quantitative study of legal rules ... is the structure of the relationship between case facts and case outcomes. Legal doctrine and legal rules are general attempts to define this relationship."
  - Classification trees "can better capture many aspects of the relationship between case facts and case outcomes." Applications: Supreme Court search-and-seizure cases (re-analysing Segal's domain) and courts-of-appeals confession cases.
  - Sources: [DOI 10.1111/j.1740-1461.2010.01176.x](https://doi.org/10.1111/j.1740-1461.2010.01176.x); [IDEAS](https://ideas.repec.org/a/wly/empleg/v7y2010i2p202-230.html). Replication data: [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/QSICEX)
- **Ruger, Kim, Martin & Quinn (2004)**, "The Supreme Court Forecasting Project: Legal and Political Science Approaches to Predicting Supreme Court Decisionmaking," *Columbia Law Review* 104(4):1150 [V-bib]. From summaries: classification-tree models fitted to about 10 years of Rehnquist Court data predicted 75% of affirm/reverse outcomes for the 2002 Term, against 59.1% for legal experts. — [DOI 10.2307/4099370](https://doi.org/10.2307/4099370); companion piece Martin, Quinn, Ruger & Kim (2004), *Perspectives on Politics* 2(4):761–767 — [DOI](https://doi.org/10.1017/s1537592704040502); [Martin PDF](https://andrewdmartin.washu.edu/app/uploads/2019/01/Competing-Approaches-to-Predicting-Supreme-Court-Decisionmaking-10ykk73.pdf)
- **Katz, Bommarito & Blackman (2017)**, "A General Approach for Predicting the Behavior of the Supreme Court of the United States," *PLOS ONE* 12(4):e0174698 [V-bib]. From background knowledge: random-forest prediction. — [DOI](https://doi.org/10.1371/journal.pone.0174698)
- **Kaufman, Kraft & Sen (2019)**, "Improving Supreme Court Forecasting Using Boosted Decision Trees," *Political Analysis* 27(3):381–387 [V-abs]. AdaBoosted decision trees "outperform existing predictive models" of Supreme Court rulings. — [DOI 10.1017/pan.2018.59](https://doi.org/10.1017/pan.2018.59)
- **Clark & Lauderdale (2010)**, "Locating Supreme Court Opinions in Doctrine Space," *AJPS* 54(4):871–890 [V-abs]. This is a latent-space scaling of **opinions** (not facts). Opinion locations and justice ideal points are estimated "along a common spatial dimension using data derived from the citations between opinions." Citations to precedent are classified as applying or disputing it, in search-and-seizure and freedom-of-religion cases, 1953–2006. — [DOI 10.1111/j.1540-5907.2010.00470.x](https://doi.org/10.1111/j.1540-5907.2010.00470.x)

### Inferences
- Across the empirical tradition the estimand is E[outcome | coded facts], with the fact coding and functional form chosen by the analyst (Segal's probit; Richards & Kritzer's logit), or a single greedy partition (Kastellec; Ruger et al.). Uncertainty is sampling uncertainty in coefficients or out-of-sample accuracy. I found no paper in this tradition that reports a distribution over alternative rule structures (different condition sets or branch orders) consistent with the cases.
- Pang et al. (2012) is the methodological bridge to the project. It already uses MCMC plus Bayesian model comparison to put a posterior on a discrete structural feature of doctrine (regime breaks). Replacing "change-point locations" with "tree or rule-list topology" is a natural extension, and Bayesian CART (Q2) supplies the machinery.
- Case-space theory supplies the generative semantics a structural posterior would need. A rule is a partition of case space into dispositions (Lax 2011; Kornhauser 2009). Judges observe the partition only partially and refine it case by case (Cameron & Kornhauser 2023; Callander & Clark 2017; Baker & Mezzetti 2012; Beim 2017). The theory also predicts residual uncertainty and inconsistently decided identical cases. That argues for a likelihood with explicit noise or "wrongly decided" terms rather than a deterministic rule fit.
- Niblett, Posner & Shleifer (2010) show non-convergence and jurisdictional divergence. A single latent rule per doctrine may therefore be misspecified; a hierarchical model (jurisdiction-level rules drawn around a doctrine-level rule) is the obvious alternative.

### Gaps
- I could not open the Kastellec (2010) full text (Wiley paywall, Cloudflare block on the Princeton copy). So I cannot confirm how he pruned trees (cross-validation or cost-complexity), whether he discussed tree instability or used bootstrapping or ensembles, or which splits he reported for search and seizure.
- Callander & Clark (2017): from background knowledge, the true fact-to-outcome mapping is modeled as a realized Brownian motion that judges learn through precedents. This is **not verified**; the abstract only says "a complicated relationship between facts and legal outcomes."
- Segal's 76% / 57% figures come only from secondary summaries.
- Kornhauser (1992) "Modeling Collegial Courts II: Legal Doctrine" has no verified record.
- I found no empirical paper that estimates a case-space partition with a posterior over its structure. Because of the search-budget limit, this is weaker evidence than a full search would give.

---

## Q2. Bayesian decision trees, BART, Bayesian CART, Bayesian rule lists and rule sets: any applications to legal outcomes, judicial decisions, sentencing, benefits eligibility or administrative adjudication?

### Takeaway
Methods that give a posterior over partition and rule structure are mature:
- Bayesian CART (Chipman, George & McCulloch 1998; Denison, Mallick & Smith 1998)
- treed models and BART (Chipman, George & McCulloch 2002, 2010); sparse BART (Linero 2018)
- SMC trees (Lakshminarayanan, Roy & Teh 2013)
- Bayesian Rule Lists and Scalable BRL (Letham et al. 2015; Yang, Rudin & Seltzer)
- Bayesian Rule Sets (Wang et al. 2017)
- Rashomon-set enumeration, a non-Bayesian analog (Xin et al. 2022)

In law, the interpretable-rule work I could verify is non-Bayesian risk prediction: COMPAS and recidivism rule lists (Angelino et al.; Zeng, Ustun & Rudin) and pretrial-release checklists (Jung et al.). Tree methods in judicial politics are frequentist CART, boosting or forests. **I did not find a verified application of Bayesian CART, BART or BRL to legal doctrine, benefits eligibility or administrative adjudication in which the posterior over tree or rule structure is read as uncertainty about the legal rule.**

### Cited Findings
**Bayesian tree methods (posterior over tree structure)**
- **Chipman, George & McCulloch (1998)**, "Bayesian CART Model Search," *JASA* 93(443):935–948 (with discussion, through p. 960) [V-bib]. It pairs a prior on trees with stochastic search "designed to guide the search toward more promising CART models." — [DOI 10.1080/01621459.1998.10473750](https://doi.org/10.1080/01621459.1998.10473750); [Penn repository](https://repository.upenn.edu/entities/publication/1c520978-df61-4f59-a0cb-6c5b84a0dc07)
- **Denison, Mallick & Smith (1998)**, "A Bayesian CART Algorithm," *Biometrika* 85(2):363–377 [V-abs]. "An approximation to a probability distribution over the space of possible trees is explored using reversible jump Markov chain Monte Carlo." — [DOI 10.1093/biomet/85.2.363](https://doi.org/10.1093/biomet/85.2.363)
- **Chipman, George & McCulloch (2002)**, "Bayesian Treed Models," *Machine Learning* 48:299–320 [V-bib]. — [DOI](https://doi.org/10.1023/a:1013916107446)
- **Chipman, George & McCulloch (2010)**, "BART: Bayesian Additive Regression Trees," *Annals of Applied Statistics* 4(1):266–298 [V-abs]. A "sum-of-trees" model fitted by Bayesian backfitting MCMC. It enables "full posterior inference including point and interval estimates of the unknown regression function," and "by keeping track of predictor inclusion frequencies, BART can also be used for model-free variable selection." — [arXiv 0806.3286](https://arxiv.org/abs/0806.3286); [DOI](https://doi.org/10.1214/09-aoas285)
- **Linero (2018)**, "Bayesian Regression Trees for High-Dimensional Prediction and Variable Selection," *JASA* 113(522):626–636 [V-bib]. — [DOI](https://doi.org/10.1080/01621459.2016.1264957)
- **Lakshminarayanan, Roy & Teh (2013)**, "Top-down Particle Filtering for Bayesian Decision Trees," ICML 2013, JMLR W&CP 28(3):280–288 [V-abs]. An SMC alternative to MCMC over tree structure that works "in a top-down manner, mimicking the behavior and speed of classic algorithms." — [arXiv 1303.0561](https://arxiv.org/abs/1303.0561)

**Bayesian rule lists and rule sets (posterior over logical rule structure)**
- **Letham, Rudin, McCormick & Madigan (2015)**, "Interpretable Classifiers Using Rules and Bayesian Analysis: Building a Better Stroke Prediction Model," *Annals of Applied Statistics* 9(3):1350–1371 [V-abs]. Bayesian Rule Lists is "a generative model ... that yields a posterior distribution over possible decision lists." The application is stroke risk (an alternative to CHADS2), not law. — [DOI 10.1214/15-aoas848](https://doi.org/10.1214/15-aoas848); [arXiv 1511.01644](https://arxiv.org/abs/1511.01644v1)
- **Yang, Rudin & Seltzer**, "Scalable Bayesian Rule Lists" [V-abs]: "two orders of magnitude faster than previous work," and it fully optimizes over rule lists "instead of using greedy splitting and pruning." — [arXiv 1602.08610](https://arxiv.org/abs/1602.08610). The ICML 2017 venue is **[UNVERIFIED]**; the arXiv record gives none.
- **Wang, Rudin, Doshi-Velez, Liu, Klampfl & MacNeille (2017)**, "A Bayesian Framework for Learning Rule Sets for Interpretable Classification," *JMLR* 18(70):1–37 [V-abs]. Bayesian Rule Sets give a small number of short rules in disjunctive normal form, with "scalable MAP inference" and bounds; the application is in-vehicle recommender behavior. — [JMLR](https://www.jmlr.org/papers/v18/16-003.html). Short version at ICDM 2016 — [DOI](https://doi.org/10.1109/icdm.2016.0171)
- Note: BRS reports a MAP rule set, not a full posterior summary. BRL samples a posterior over decision lists (per its abstract).

**Non-Bayesian structure-multiplicity analogs**
- **Xin, Zhong, Chen, Takagi, Seltzer & Rudin (2022)**, "Exploring the Whole Rashomon Set of Sparse Decision Trees," NeurIPS 2022 (oral) [V-abs]. It is "the first technique for completely enumerating the Rashomon set for sparse decision trees," that is, the set of all almost-optimal models. — [arXiv 2209.08040](https://arxiv.org/abs/2209.08040); [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/5afaa8b4dd18eb1eed055d2d821b58ae-Abstract.html)
- **Semenova, Rudin & Parr (2022)**, "On the Existence of Simpler Machine Learning Models," FAccT 2022, pp. 1827–1858 [V-bib]. — [DOI](https://doi.org/10.1145/3531146.3533232)

**Interpretable rule models in criminal-justice settings (risk prediction, non-Bayesian)**
- **Angelino, Larus-Stone, Alabi, Seltzer & Rudin**, "Learning Certifiably Optimal Rule Lists for Categorical Data," *JMLR* 18(234):1–78 (2018); short version at KDD 2017 [V-abs]. "Optimal sparse rule lists that are approximately as accurate as the COMPAS proprietary risk prediction tool on data from Broward County, Florida, but that are completely interpretable." — [arXiv 1704.01701](https://arxiv.org/abs/1704.01701); [KDD DOI](https://doi.org/10.1145/3097983.3098047)
- **Zeng, Ustun & Rudin**, "Interpretable Classification Models for Recidivism Prediction," *JRSS-A* 180(3):689–722 (2017; online 2016) [V-bib]. — [DOI](https://doi.org/10.1111/rssa.12227)
- **Jung, Concannon, Shroff, Goel & Goldstein**, "Simple Rules to Guide Expert Classifications," *JRSS-A* 183(3):771–800 (2020); arXiv title "Simple rules for complex decisions" [V-abs]. "Select-regress-and-round" builds weighted checklists, with "a detailed case study of judicial decisions to release or detain defendants while they await trial." — [arXiv 1702.04690](https://arxiv.org/abs/1702.04690); [DOI](https://doi.org/10.1111/rssa.12576)

**Tree methods introduced to political science**
- **Montgomery & Olivella (2018)**, "Tree-Based Models for Political Science Data," *AJPS* 62(3):729–744 [V-abs]. An overview of "a family of tree-based nonparametric techniques" with three illustrative analyses. From background knowledge, the family includes BART. — [DOI 10.1111/ajps.12361](https://doi.org/10.1111/ajps.12361)

**Possible legal applications of BART (not confirmed)**
- A search result pointed to a 2019 University of Utah dissertation, "Bayesian additive regression trees and the next generation of juvenile justice risk assessments," comparing BART, random forests and logistic regression for reoffending risk. The repository page returned HTTP 418, so this is **[UNVERIFIED]**. — [Utah collections record](https://collections.lib.utah.edu/details?id=1714100). That kind of use would be risk prediction in any case, not rule recovery.
- Dunn, Sagun, Şirin & Chen (2017), "Early Predictability of Asylum Court Decisions," ICAIL 2017, pp. 233–236 [V-bib], appeared in a search for BART and asylum. I did **not** verify that it uses BART. — [DOI](https://doi.org/10.1145/3086512.3086537)

### Inferences
- The tools that answer "which conditions, which branches, with what posterior probability" exist and are well understood: Bayesian CART and BRL give posteriors over discrete structure, BART gives variable-inclusion frequencies, and SMC is an alternative sampler. Their legal-adjacent uses are risk scores (recidivism, pretrial release), where the target is a predictive tool, not the latent rule a statute or doctrine requires.
- To carry them over to latent legal decision models, at least three changes appear necessary (my inference):
  1. The prior over trees or rule lists should come from formalizations (LLM readings, official guidance) rather than generic split priors.
  2. The likelihood needs noise, compliance and error components, because observed decisions deviate from the rule (Cameron & Kornhauser's "wrongly decided" cases).
  3. Posterior summaries should be behavioral: the probability two rules disagree on a fact pattern, or the posterior probability that a condition is necessary. Raw tree topology is a poor summary, consistent with Vernie & Grabmair in Q5.
- Rashomon-set enumeration is a ready-made non-Bayesian way to show how many materially different rules fit the case record equally well. It is a useful baseline for judging whether a Bayesian structural posterior is over- or under-concentrated.

### Gaps
- I could not run broad searches for "Bayesian CART / BART / Bayesian rule list" combined with "court / sentencing / asylum / disability / benefits / administrative adjudication" after the search budget ran out. The absence claim is therefore provisional, and a targeted Google Scholar sweep is recommended.
- The Utah BART dissertation is unverified.
- I did not verify whether Montgomery & Olivella's illustrations include any legal or judicial data.

---

## Q3. Inverse learning of rules and norms from decisions: learning eligibility rules from administrative decisions, norm or rule induction, IRL of norms

### Takeaway
AI and Law has spent three decades asking whether the rule being followed can be recovered from decided cases. Its benchmark is a fictional welfare-benefit eligibility rule with six conditions (Bench-Capon 1993), later used by Možina et al. (2005/06), Wardeh et al. (2009) and Steging et al. (2021). The consistent finding is that **classifiers reach about 98–99% accuracy without recovering the true conditions**: "none of the techniques produced rules which faithfully reflected the conditions." Conditions the data never exercise are unidentifiable.

Symbolic theory-induction work searches over candidate theories and scores them by explanatory power and simplicity, but returns a single best theory, not a posterior:
- defeasible-logic induction (Johnston & Governatori 2003)
- AGATHA's A* search (Chorley & Bench-Capon 2005)
- Bench-Capon & Sartor's (2003) theory construction

Genuinely Bayesian norm induction exists in multi-agent systems (Cranefield et al. 2016; Oldenburg & Zhi-Xuan 2024) and in specification inference from demonstrations, but not on legal corpora. LLM-based "Legal Rule Induction" from precedents (Fan et al. 2025) is new and reports over-generalization and hallucination.

### Cited Findings
**The welfare-benefit "rule recovery" benchmark line**
- **Bench-Capon (1993)**, "Neural Networks and Open Texture," ICAIL '93, pp. 292–297 [V-abs]. It asks three questions: "can a net classify cases successfully; can an acceptable rationale be uncovered by an examination of the net; and can we derive rules describing the problem from an examination of the net?" — [DOI 10.1145/158976.159012](https://doi.org/10.1145/158976.159012)
- **Možina, Žabkar, Bench-Capon & Bratko**, "Argument Based Machine Learning Applied to Law," *Artificial Intelligence and Law* 13(1):53–73 [V-abs, full text read]. The PDF header reads "(2006) 13: 53–73"; Springer lists the volume as 2005.
  - The paper states the inverse problem directly. In administrative law "many thousands of cases are routinely decided ... Is there a way of deciding what the rule being followed is from an automated consideration of the data?" One use is to "discover the 'real' rule from a database recording the actual practice," as distinct from "the rule which exists in theory."
  - The benefit is payable if six conditions hold (Boolean necessary conditions, a continuous threshold, and an interaction between distance and in-patient status), with 12 relevant attributes.
  - Comparing neural nets (Bench-Capon 1993), defeasible logic (Johnston & Governatori 2003) and CN2: all classify very accurately, but "none of the techniques produced rules which faithfully reflected the conditions for the benefit."
  - No system discovered the significance of the claimant's sex. The authors note this was unavoidable because the "learning data only contains male applicants between 60 and 65 that fail to qualify also for other reasons."
  - Argument-based CN2 (ABCN2), which uses expert justifications attached to selected examples, beat CN2 at 20% class noise by 3.3 points (p < 0.001).
  - Sources: [author PDF](https://intranet.csc.liv.ac.uk/~tbc/publications/ArgumentBasedMachineLearningAp.pdf); [DOI 10.1007/s10506-006-9002-4](https://doi.org/10.1007/s10506-006-9002-4)
- **Steging, Renooij & Verheij (2021)**, "Discovering the Rationale of Decisions," ICAIL 2021, pp. 235–239; extended arXiv version "Discovering the Rationale of Decisions: Experiments on Aligning Learning and Reasoning" [V-abs, full text read].
  - Replicating Bench-Capon (1993): multilayer perceptrons reached above 98% accuracy but "were unable to properly learn two of the six conditions." "Using only 4 out of 6 conditions was shown to be sufficient for classifying 98.95% of the instances correctly."
  - The authors propose "dedicated test cases, similar to unit-testing," to evaluate rationale. They also test a Dutch tort-law domain (5 conditions, 10 Boolean features). Networks average about 99% accuracy yet "do not necessarily learn the conditions."
  - Sources: [ICAIL DOI](https://doi.org/10.1145/3462757.3466059); [arXiv 2105.06758](https://arxiv.org/abs/2105.06758)
- **Wardeh, Bench-Capon & Coenen (2009)**, "PADUA: A Protocol for Argumentation Dialogue Using Association Rules," *AI and Law* 17(3):183–215 [V-bib]. It mines association rules from datasets and uses them as arguments; Steging et al. cite it as another welfare-domain experiment. — [DOI](https://doi.org/10.1007/s10506-009-9078-8)

**Symbolic theory induction from precedents**
- **Johnston & Governatori (2003)**, "Induction of Defeasible Logic Theories in the Legal Domain," ICAIL '03 [V-abs]. Exact induction is "expensive and computationally intractable," so they use a heuristic algorithm "automatically deriving its knowledge from databases of precedents." — [DOI 10.1145/1047788.1047834](https://doi.org/10.1145/1047788.1047834)
- **Bench-Capon & Sartor (2003)**, "A Model of Legal Reasoning with Cases Incorporating Theories and Values," *Artificial Intelligence* 150(1):97–143 [V-abs, full text read].
  - It rejects the naive model "R x F = D" (decision = rules applied to facts) and recasts reasoning with cases as "constructing, evaluating and applying a theory."
  - Theories are compared by explanatory power, coherence and simplicity.
  - Sources: [author PDF](https://intranet.csc.liv.ac.uk/~tbc/publications/aijsartor.pdf); [DOI](https://doi.org/10.1016/S0004-3702(03)00108-5)
- **Chorley & Bench-Capon**, "AGATHA: Using Heuristic Search to Automate the Construction of Case Law Theories," *AI and Law* 13(1):9–51 (2005 per Crossref; PDF header 2006) [V-abs, full text read].
  - A theory is a five-tuple: cases, factors (each tied to an outcome and a value), defeasible rules, rule preferences and value preferences. The space is searched with A* and alpha/beta pruning.
  - Theories are scored on "Simplicity," "Explanatory Power" (the percentage of background cases explained) and "Completion Explanatory Power."
  - Sources: [author PDF](https://cgi.csc.liv.ac.uk/~tbc/publications/agatha.pdf); [DOI](https://doi.org/10.1007/s10506-006-9004-2)
- **Precedential constraint applied to data**
  - van Woerkom, Grossi, Prakken & Verheij (2022), "Landmarks in Case-Based Reasoning: From Theory to Data" (FAIA/JURIX) [V-abs]. They evaluate the theory of precedential constraint "on a real world dataset" and identify "landmark cases" that characterize which datasets suit the theory. — [DOI](https://doi.org/10.3233/faia220200)
  - Extended version: "A Fortiori Case-Based Reasoning: From Theory to Data," *JAIR* 81:401–441 (2024) [V-abs]. — [DOI](https://doi.org/10.1613/jair.1.15178)
  - Related [V-bib]: Horty (2011), "Rules and Reasons in the Theory of Precedent," *Legal Theory* 17(1):1–33 — [DOI](https://doi.org/10.1017/s1352325211000036); Prakken & Ratsma, "A Top-Level Model of Case-Based Argumentation for Explanation: Formalisation and Experiments," *Argument & Computation* 13(2):159–194 — [DOI](https://doi.org/10.3233/aac-210009); Peters, Bex & Prakken (2023), "Model- and Data-Agnostic Justifications with A Fortiori Case-Based Argumentation," ICAIL 2023, pp. 207–216 — [DOI](https://doi.org/10.1145/3594536.3595164)

**Bayesian norm and specification induction from behavior (not legal corpora)**
- **Cranefield, Meneguzzi, Oren & Savarimuthu (2016)**, "A Bayesian Approach to Norm Identification," ECAI 2016 (FAIA) [V-abs]. It learns obligations and prohibitions "from both norm compliant and norm violating behaviour," which lets "norms to be learned with fewer observations." — [DOI](https://doi.org/10.3233/978-1-61499-672-9-622)
- **Oldenburg & Zhi-Xuan (2024)**, "Learning and Sustaining Shared Normative Systems via Bayesian Rule Induction in Markov Games," AAMAS 2024 [V-abs]. A new agent "can infer the norms of an existing population from observations of compliance and violation" through "approximately Bayesian rule induction of obligative and prohibitive norms." — [arXiv 2402.13399](https://arxiv.org/abs/2402.13399)
- **Specification inference from demonstrations**
  - Kasenberg & Scheutz (2017), "Interpretable Apprenticeship Learning with Temporal Logic Specifications," IEEE CDC, pp. 4914–4921 [V-bib]. — [DOI](https://doi.org/10.1109/cdc.2017.8264386)
  - Kim, Muise, Shah, Agarwal & Shah (2019), "Bayesian Inference of Linear Temporal Logic Specifications for Contrastive Explanations," IJCAI, pp. 5591–5598 [V-bib]. — [DOI](https://doi.org/10.24963/ijcai.2019/776)
  - Shah et al. (2023), "Supervised Bayesian Specification Inference from Demonstrations," *IJRR* 42(14):1245–1264 [V-bib]. — [DOI](https://doi.org/10.1177/02783649231204659)

**LLM-era rule induction from cases**
- **Fan, Zheng, Hu, Deng, Wang, Xu, Li, Li, Shen & Song**, "Legal Rule Induction: Towards Generalizable Principle Discovery from Analogous Judicial Precedents," arXiv 2505.14104 (May 2025) [V-abs].
  - Task: "deriving concise, generalizable doctrinal rules from analogous precedents, distilling their shared preconditions, normative behaviors, and legal consequences."
  - Data: 5,121 case sets (38,088 Chinese cases) plus 216 expert-annotated gold test sets.
  - Finding: state-of-the-art LLMs "struggle with over-generalization and hallucination."
  - The arXiv comment reads "Accepted by EMNLP2026 Main Conference"; that venue and year are as stated by arXiv, not checked independently.
  - Source: [arXiv](https://arxiv.org/abs/2505.14104)

### Inferences
- The welfare-benefit line shows that **outcome data identify the decision function on the support of observed fact patterns, not the rule's structure**. Several structurally different rules (4 of 6 conditions, or rules that never mention sex) fit observed decisions almost perfectly. This is exactly where a posterior over structure should stay wide, and where readings of the statutory text must supply the prior. A model that reports a confident structure from outcome data alone should be distrusted.
- Steging et al.'s "rationale unit tests" (fact patterns built to fail exactly one condition) are the experimental analog of Vernie & Grabmair's SAT-enumerated edge cases (Q5). They are natural candidates for (a) posterior predictive checks and (b) active-learning queries to experts or agencies.
- Theory-construction systems (AGATHA; Bench-Capon & Sartor) already define a scored space of discrete rule-and-preference theories. Turning "explanatory power + simplicity" into "likelihood + prior" and sampling rather than searching would give a structural posterior. I found no work that does this.
- The Bayesian norm-induction papers (Cranefield; Oldenburg & Zhi-Xuan) show the inference pattern for learning from both compliant and violating behavior. That matters for behavioral records, where observed outcomes mix rule application with non-compliance.

### Gaps
- I found no verified study that learns eligibility rules from real administrative decision records (for example, benefits or immigration determinations) and compares them with the statutory rule; the welfare-benefit domain is synthetic. Further searches were not possible (budget exhausted).
- I found no inverse-reinforcement-learning paper on legal norms specifically. The IRL and specification items above are general-purpose and were verified only bibliographically, except Oldenburg & Zhi-Xuan and Cranefield et al.
- The year discrepancy (2005 vs 2006) for AI & Law volume 13 papers is noted rather than resolved.

---

## Q4. Legal judgment prediction that recovers interpretable rules or quantifies uncertainty over them

### Takeaway
Most legal judgment prediction (LJP) is black-box text classification; Medvedeva & McBride (2023) criticize it. The interpretable strand puts predictions on an explicit legal knowledge structure:
- issue/factor hierarchies: IBP and SMILE (Ashley & Brüninghaus 2009)
- value-based argument graphs with learned weights: VJAP (Grabmair 2017)
- Angelic Domain Models / ADFs for ECHR Article 6: Collenette et al. 2023; Mumford et al. 2022/2023

In all of these the rule structure is **hand-specified** from doctrine, and data supply factor ascriptions or weights. **No verified LJP work places a posterior over the rule structure itself.** The nearest probabilistic analog is Bayesian model comparison and averaging over independently built Bayesian-network models of competing legal arguments (Neil, Fenton, Lagnado & Gill 2019), which concerns evidence and arguments rather than doctrinal logic.

### Cited Findings
- **Ashley & Brüninghaus (2009)**, "Automatically Classifying Case Texts and Predicting Outcomes," *AI and Law* 17(2):125–165 [V-bib]. It combines IBP prediction with SMILE text classification (per the Semantic Scholar summary). — [DOI 10.1007/s10506-009-9077-9](https://doi.org/10.1007/s10506-009-9077-9)
  - IBP structure, from a secondary description: in IBP "the issues formed a top layer of necessary and sufficient conditions (termed the logical model), with factor based reasoning used to determine the status of the leaf issues." — [Using Issues to Explain Legal Decisions, arXiv 2106.14688](https://arxiv.org/pdf/2106.14688). This quote comes from search-result text; I did not fetch the full document.
- **Grabmair (2017)**, "Predicting Trade Secret Case Outcomes Using Argument Schemes and Learned Quantitative Value Effect Tradeoffs," ICAIL 2017, pp. 89–98 [V-abs]. VJAP "creates an argument graph for each case using argument schemes and a representation of values underlying trade secret law and effects of facts on these values." It "predicts case outcomes using a confidence measure computed from the graph," with "quantitative weights learned from past cases," and is "competitive with common machine learning models" on a limited dataset. — [DOI](https://doi.org/10.1145/3086512.3086521)
- **Collenette, Atkinson & Bench-Capon (2023)**, "Explainable AI Tools for Legal Reasoning about Cases: A Study on the European Court of Human Rights," *Artificial Intelligence* 317:103861 [V-bib]. Earlier ADF version at JURIX 2020 — [DOI](https://doi.org/10.3233/faia200488). — [DOI](https://doi.org/10.1016/j.artint.2023.103861)
- **Mumford, Atkinson & Bench-Capon (2023)**, "Combining a Legal Knowledge Model with Machine Learning for Reasoning with Legal Cases," ICAIL 2023, pp. 167–176 [V-abs]. Hierarchical BERT models "ascribe to an Angelic Domain Model (ADM) that is able to represent the legal knowledge of a domain in a structured way." Ascription is evaluated "at three different levels of abstraction" on ECHR cases. — [DOI](https://doi.org/10.1145/3594536.3595158). Earlier version: "Reasoning with Legal Cases: A Hybrid ADF-ML Approach," JURIX 2022 [V-bib] — [DOI](https://doi.org/10.3233/faia220452)
- **Branting et al.**, "Scalable and Explainable Legal Prediction," *AI and Law* 29(2):213–238 (2021; online 2020) [V-bib]. Per the Semantic Scholar TLDR, it describes explainable outcome prediction that "obviate[s] both annotation of an entire decision corpus and manual processing of new cases." — [DOI](https://doi.org/10.1007/s10506-020-09273-1)
  - Related [V-bib]: Branting et al. (2019), "Semi-Supervised Methods for Explainable Legal Prediction," ICAIL — [DOI](https://doi.org/10.1145/3322640.3326723); Branting (2017), "Data-Centric and Logic-Based Models for Automated Legal Problem Solving," *AI and Law* 25(1):5–27 — [DOI](https://doi.org/10.1007/s10506-017-9193-x)
- **Text-classification LJP** [V-bib]:
  - Aletras, Tsarapatsanis, Preoţiuc-Pietro & Lampos (2016), "Predicting Judicial Decisions of the European Court of Human Rights: A Natural Language Processing Perspective," *PeerJ CS* 2:e93 — [DOI](https://doi.org/10.7717/peerj-cs.93)
  - Chalkidis et al. (2021), "Paragraph-level Rationale Extraction through Regularization: A Case Study on European Court of Human Rights Cases," NAACL, pp. 226–241 — [DOI](https://doi.org/10.18653/v1/2021.naacl-main.22)
  - Medvedeva & McBride (2023), "Legal Judgment Prediction: If You Are Going to Do It, Do It Right," NLLP Workshop, pp. 73–84 — [DOI](https://doi.org/10.18653/v1/2023.nllp-1.9)
- **Neil, Fenton, Lagnado & Gill (2019)**, "Modelling Competing Legal Arguments Using Bayesian Model Comparison and Averaging," *AI and Law* 27(4):403–430 [V-abs].
  - The paper drops the assumption of "a single integrated model." It compares and averages "Bayesian models of legal arguments that have been built independently and with no attempt to make them consistent in terms of variables, causal assumptions or parameterization."
  - Models "more heavily disconfirmed by the facts are given lower weight, as model plausibility measures."
  - Source: [DOI 10.1007/s10506-019-09250-3](https://doi.org/10.1007/s10506-019-09250-3)
- **Fenton, Neil & Lagnado**, "A General Structure for Legal Arguments About Evidence Using Bayesian Networks," *Cognitive Science* 37(1):61–102 (2013; online 2012) [V-bib]. — [DOI](https://doi.org/10.1111/cogs.12004)
- **Survey context** [V-bib]: Atkinson, Bench-Capon & Bollegala (2020), "Explanation in AI and Law: Past, Present and Future," *Artificial Intelligence* 289:103387. — [DOI](https://doi.org/10.1016/j.artint.2020.103387)

### Inferences
- The interpretable LJP pattern (doctrinal structure fixed by experts, data used for factor ascription and weights) is the "single reading" version of the project's target. Adding a posterior over several candidate domain models (several ADMs or issue trees from different LLM or official readings) would generalize it. Neil et al. (2019) provide a worked template: Bayesian model averaging across independently built, mutually inconsistent models, with weights from fit to the facts. That is close to what "combining several LLM formalizations" needs, provided the models are cast as rule structures.
- The absence of uncertainty quantification in LJP means calibrated structural posteriors would be a distinct contribution, and it could be evaluated with the rationale tests from Q3.

### Gaps
- I could not retrieve the abstracts of Ashley & Brüninghaus (2009) or Branting et al. (2021); Springer blocked access and Crossref, OpenAlex and Semantic Scholar have the abstracts elided. Their descriptions rest on TLDRs and a secondary source.
- I did not verify any LJP paper on calibration or conformal prediction (the search budget was exhausted), so "no UQ over rules in LJP" is provisional.
- I did not verify accuracy figures for Aletras et al. or Chalkidis et al. and do not report them.

---

## Q5. Does any work combine textual readings of the rule with outcome data to infer the rule?

### Takeaway
Partially, in four forms; none produces a calibrated posterior over rule structure from multiple readings plus behavioral records:
1. **Expert or doctrinal structure plus learned parameters from outcomes**: IBP; VJAP; ADM + BERT. Argument-based ML (Možina et al.) is the closest to "text constrains rule induction": expert justifications attached to examples restrict which rules CN2 may learn, and this improves robustness to noise.
2. **Text plus votes in latent-space scaling**: Lauderdale & Clark (2014) combine LDA on opinions with votes; Kim, Londregan & Ratkovic (2018) combine votes and text; Clark & Lauderdale (2010) use citations to locate opinions in "doctrine space." These are the closest relatives of Hoff–Raftery–Handcock-style latent structure in judicial data, but they place actors and opinions in space, not rules over facts.
3. **Comparing several formalizations by the decisions they encode**: Vernie & Grabmair (2026) compare 9 LLM formalizations of 10 EU provisions with SAT-enumerated disagreement cases. Structural alignment does not predict behavioral divergence (ρ = +0.09 between coverage and edge-case count). There is no outcome data and no posterior.
4. **LLM-proposed hypotheses reweighted by a Bayesian prior and likelihood** (Ellis 2023; not legal), the cleanest computational template for "LLM readings as proposal distribution, decisions as likelihood."

### Cited Findings
- **Vernie & Grabmair (2026)**, "By Their Fruits You Will Know Them: Comparing Formalizations of Law by the Decisions They Encode," arXiv 2605.25186 (submitted 24 May 2026, revised 17 Sep 2026) [V-abs, full text read]. The arXiv comment reads "accepted at EMNLP PROC 2026."
  - Method: match formalizations at the node level, derive a shared interface per pair, "use a SAT solver to enumerate the edge cases on which any two formalizations disagree," and verbalize the cases for expert review.
  - Scale: nine frontier LLMs × ten EU provisions (GDPR, AI Act, DMA and others). N = 304 pairs remain at matching coverage ≥ 0.4.
  - Disagreement by model: Gemini 3.1 Pro disagrees with its peers on 71% of its pairs, Qwen 3.5 on 32%. Per-provision disagreement swings from 0% to 100%.
  - Structure vs behavior: the rank correlation between coverage and edge-case count is "negligible (ρ = +0.09)," and "even at the highest-coverage end, 42% of pairs are logically equivalent." "Structural alignment does not predict behavioral divergence."
  - Example interpretive split: the models "split evenly into two camps" on whether race-based biometric categorization for law enforcement is prohibited under AI Act Art. 5, mirroring the commentary.
  - Example encoding error: Kimi K2.5 encodes two alternative conditions as conjunctive.
  - Stated limits: the method relies on LLM node matching whose "correctness we cannot" assess, and "not all structural differences lead to a final difference in outcome."
  - The paper cites Graus (2026) as reporting high structural but low outcome similarity; I did not verify that work.
  - Source: [arXiv 2605.25186](https://arxiv.org/abs/2605.25186)
- **Možina et al. (2005/06)** [V-abs, full text]. ABML attaches expert arguments to examples; a rule covers an argued example only if "all the reasons of the argument of E are included among conditions" of the rule. The method "makes use of the justifications of decisions which are available," and ABCN2 was more robust to noise than CN2. — [author PDF](https://intranet.csc.liv.ac.uk/~tbc/publications/ArgumentBasedMachineLearningAp.pdf)
- **Grabmair (2017)** VJAP (argument schemes and value model plus weights learned from past cases) and **Mumford et al. (2023)** (ADM knowledge model plus H-BERT) are both described in Q4 [V-abs].
- **Lauderdale & Clark (2014)**, "Scaling Politically Meaningful Dimensions Using Texts and Votes," *AJPS* 58(3):754–771 [V-abs]. The authors use "votes and opinion texts from the U.S. Supreme Court, using latent Dirichlet allocation to discover the extent to which different issues were at stake in different cases and estimating justice preferences within each of those issues." — [IDEAS](https://ideas.repec.org/a/wly/amposc/v58y2014i3p754-771.html); [LSE eprint](https://eprints.lse.ac.uk/55929/); [author PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAJPS2014.pdf)
- **Kim, Londregan & Ratkovic (2018)**, "Estimating Spatial Preferences from Votes and Text," *Political Analysis* 26(2):210–229 [V-bib]. — [DOI](https://doi.org/10.1017/pan.2018.7)
- **Clark & Lauderdale (2010)** citation-based doctrine space (Q1) [V-abs]. — [DOI](https://doi.org/10.1111/j.1540-5907.2010.00470.x)
- **Ellis (2023)**, "Human-like Few-Shot Learning via Bayesian Reasoning over Natural Language," NeurIPS 2023 (oral) [V-abs]: "a language model first proposes candidate hypotheses expressed in natural language, which are then re-weighed by a prior and a likelihood." — [arXiv 2306.02797](https://arxiv.org/abs/2306.02797)
- **Fan et al. (2025)** LLM rule induction from precedent texts (Q3) [V-abs]. Text only, with no likelihood over outcomes. — [arXiv 2505.14104](https://arxiv.org/abs/2505.14104)
- **Formalization substrates** (where the "readings" come from) [V-bib except SARA]:
  - Sergot et al. (1986), "The British Nationality Act as a Logic Program," *CACM* 29(5):370–386 — [DOI](https://doi.org/10.1145/5689.5920)
  - Merigoux, Chataing & Protzenko (2021), "Catala: A Programming Language for the Law," *PACMPL* 5(ICFP):1–29 — [DOI](https://doi.org/10.1145/3473582)
  - Holzenberger, Blair-Stanek & Van Durme (2020), "A Dataset for Statutory Reasoning in Tax Law Entailment and Question Answering" (SARA) [V-abs]: "Legislation can be viewed as a body of prescriptive rules expressed in natural language." — [arXiv 2005.05257](https://arxiv.org/abs/2005.05257)
  - Blair-Stanek, Holzenberger & Van Durme (2023), "Can GPT-3 Perform Statutory Reasoning?," ICAIL, pp. 22–31 — [DOI](https://doi.org/10.1145/3594536.3595163)
  - Verheij (2017), "Formalizing Arguments, Rules and Cases," ICAIL, pp. 199–208 — [DOI](https://doi.org/10.1145/3086512.3086533)
- **Motivating analogy** [V-bib]: Hoff, Raftery & Handcock (2002), "Latent Space Approaches to Social Network Analysis," *JASA* 97(460):1090–1098. — [DOI](https://doi.org/10.1198/016214502388618906)

### Inferences
- The pieces of the target model exist separately but have not been assembled:
  1. a space of discrete rule structures with a prior (Bayesian CART/BRL; AGATHA's theory space);
  2. proposals from textual readings (LLM formalizations, Catala-style encodings, Ellis-style NL hypotheses);
  3. a likelihood from behavioral records that tolerates non-compliance (norm-induction likelihoods; Cameron & Kornhauser's residual error);
  4. model averaging across inconsistent readings (Neil et al. 2019).
  I found no paper that combines all four for legal rules.
- Vernie & Grabmair's result (structure uncorrelated with behavior), together with the welfare-benefit result (many structures, identical behavior), suggests the "latent space" for rules should be defined behaviorally. A candidate distance between two rules is the probability, under a distribution of fact patterns, that they assign different outcomes. Posteriors would be summarized by posterior-predictive disagreement on specific edge cases rather than by edit distance over trees. This is my synthesis, not a claim made by any cited paper.
- Outcome data constrain the rule only on regions of case space that decisions actually exercise (the Možina "sex" condition; Steging's 4 of 6 conditions). Readings of the text are therefore the only information on unexercised conditions. A calibrated posterior should show near-prior uncertainty there, and validation should test that.

### Gaps
- I found no work that fits a single statistical model taking several textual formalizations and outcome records jointly and returning a posterior over rule structure. Given the search-budget cutoff, this is a provisional finding rather than an exhaustive one.
- I did not verify Graus (2026), which Vernie & Grabmair cite as a related structural-versus-outcome similarity result.
- I did not check whether Lauderdale & Clark or Kim, Londregan & Ratkovic report posterior uncertainty in a form that could transfer to rule structures. Both are cited here only as text-plus-votes latent-space precedents.
