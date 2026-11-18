# Latent-variable, item-response (ideal-point) and latent-space models applied to law

Verification note (2026-10-05). Every citation below was checked against Crossref or OpenAlex DOI metadata (authors, year, title, venue, volume, pages), or against the publisher or author PDF. Method details marked "(read in PDF)" were read in the full text. Items marked **[UNVERIFIED]** could not be confirmed from a primary or repository page. The session's shared web-search quota (200 calls, shared with parallel researchers) ran out partway through. After that, discovery relied on Crossref and OpenAlex queries and direct PDF downloads, so coverage of 2020+ machine-learning venues (ACL, NeurIPS, ICAIL) is thinner than coverage of political-science journals.

## Q1. Ideal-point and IRT models of courts: what is latent, and does any of this work model rules or doctrine rather than actors?

### Takeaway
In the standard court IRT models (Martin–Quinn; Clinton–Jackman–Rivers; Bafumi et al.; Bailey; and the Judicial Common Space family), the latent objects of interest are actors' ideal points. Each case does get latent cutpoint and discrimination parameters, but these are nuisance parameters that are never linked to the case's facts or doctrine. Doctrine enters the IRT tradition in three ways:
- as weights that define which cases share a dimension (Lauderdale & Clark 2012, 2014, 2016);
- as identified "legal value" effects (Bailey & Maltzman 2008);
- as latent regime change-points in the mapping from case facts to outcomes (Pang, Friedman, Martin & Quinn 2012). This is the closest thing in the IRT family to a latent decision model with a posterior over its structure.

### Cited Findings
**Core dynamic and Bayesian IRT models of the U.S. Supreme Court**
- Martin & Quinn (2002), "Dynamic Ideal Point Estimation via Markov Chain Monte Carlo for the U.S. Supreme Court, 1953–1999," *Political Analysis* 10(2):134–153. Bayesian dynamic IRT fit by MCMC (Albert–Chib data augmentation). The data are all nonunanimous cases, K = 3,450, coded as votes to reverse (1) or affirm (0) the lower court. Unanimous cases are dropped because they "contribute no information to the likelihood." Ideal points follow a random-walk prior whose evolution variance is "fixed a priori by the researcher." Setting it to 0 gives constant ideal points; letting it go to infinity makes terms independent (read in PDF). — [Martin & Quinn 2002 PDF](https://www.cs.princeton.edu/courses/archive/fall09/cos597A/papers/MartinQuinn2002.pdf); [DOI](https://doi.org/10.1093/pan/10.2.134)
- Martin & Quinn (2002), identification and validation. Scale invariance and rotational (reflection) invariance are "resolved through the use of semiinformative prior distributions… the informative priors on the ideal points for certain justices ensure that only one of the posterior modes has nonnegligible mass." They report posterior SDs and 95% credible intervals. In the constant-ideal-point model, posterior means correlate −0.86, −0.83, −0.70 and −0.60 with justices' percent-conservative voting in civil rights, civil liberties, economics and federalism. The Segal–Cover scores correlate 0.63, 0.60, 0.43 and 0.33 with the same measures (J = 29) (read in PDF). — [Martin & Quinn 2002 PDF](https://www.cs.princeton.edu/courses/archive/fall09/cos597A/papers/MartinQuinn2002.pdf)
- Martin & Quinn (2007), "Assessing Preference Change on the US Supreme Court," *JLEO* 23(2):365–385. Uses a Bayesian dynamic ideal-point model to test whether justices' positions change during their careers. — [DOI](https://doi.org/10.1093/jleo/ewm028)
- Martin–Quinn-type dynamic IRT is now available in fast EM form: `emIRT::dynIRT` ships the Martin–Quinn data (Imai, Lo & Olmsted 2016, "Fast Estimation of Ideal Points with Massive Data," *APSR* 110(4):631–656). — [DOI](https://doi.org/10.1017/s000305541600037x); [emIRT mq_data](https://rdrr.io/cran/emIRT/man/mq_data.html)

**General Bayesian IRT methodology**
- Clinton, Jackman & Rivers (2004), "The Statistical Analysis of Roll Call Data," *APSR* 98(2):355–370. A general Bayesian framework for spatial voting that "combin[es] the measurement of legislative preferences with tests of models of legislative behavior." — [DOI](https://doi.org/10.1017/s0003055404001194); [Vanderbilt PDF](https://cdn.vanderbilt.edu/vu-my/wp-content/uploads/sites/349/2011/10/14093745/CJR_APSR2004.pdf)
- Jackman (2001), "Multidimensional Analysis of Roll Call Data via Bayesian Simulation: Identification, Estimation, Inference, and Model Checking," *Political Analysis* 9(3):227–241. Verified from title and metadata only. — [DOI](https://doi.org/10.1093/polana/9.3.227)
- Bafumi, Gelman, Park & Kaplan (2005), "Practical Issues in Implementing and Understanding Bayesian Ideal Point Estimation," *Political Analysis* 13(2):171–187. Applied to legislators and Supreme Court justices. It names the problems as improper variance estimates, scale/translation invariance, reflection invariance and outliers. Its remedies are hierarchical modeling, linear transformations, informative regression predictors and explicit outlier models. — [Cambridge](https://www.cambridge.org/core/journals/political-analysis/article/practical-issues-in-implementing-and-understanding-bayesian-ideal-point-estimation/748E80D1DDD69FCF2EECEBFCE47FC355); [Columbia PDF](https://sites.stat.columbia.edu/gelman/research/published/171.pdf)
- Bailey (2007), "Comparable Preference Estimates across Time and Institutions for the Court, Congress, and Presidency," *AJPS* 51(3):433–448. Uses Bayesian MCMC with "bridging" observations so that presidents, legislators and justices can be compared across time. — [DOI](https://doi.org/10.1111/j.1540-5907.2007.00260.x)

**Dan Ho's own work in this strand**
- Ho & Quinn (2010), "How Not to Lie with Judicial Votes: Misconceptions, Measurement, and Models," *California Law Review* 98:813. They argue that such scores are "descriptive summaries" of voting behavior that are "widely misinterpreted, and commonly misused." They address how the scores relate to "ideology," dimensionality, intertemporal extrapolation and cardinal interpretation. They also argue that measurement models "empower meaningful examination, data collection, and incorporation of doctrine and jurisprudence" (read in PDF). — [Berkeley PDF](https://www.law.berkeley.edu/files/Ho-Quinn_HowNotToLie.pdf)
- Ho & Quinn (2010), "Did a Switch in Time Save Nine?," *Journal of Legal Analysis* 2(1):69–113. Uses dynamic measurement on newly collected 1931–1940 votes and finds that Roberts "shifted sharply to the left in the 1936 term." — [DOI](https://doi.org/10.1093/jla/2.1.69)

**Doctrine entering the IRT tradition**
- Bailey & Maltzman (2008), "Does Legal Doctrine Matter? Unpacking Law and Policy Preferences on the U.S. Supreme Court," *APSR* 102(3):369–384. Members of Congress' and presidents' positions on Court cases identify the policy component of voting. This isolates three legal doctrines (adherence to precedent, judicial restraint, strict speech protection), whose effects "var[y] across justices." The work was expanded into *The Constrained Court* (Princeton UP, 2011). — [DOI](https://doi.org/10.1017/s0003055408080283); [book chapter DOI](https://doi.org/10.23943/princeton/9780691151045.003.0002)
- Lauderdale & Clark (2012), "The Supreme Court's Many Median Justices," *APSR* 106(4):847–866.
  - Estimates case-specific justice orderings by kernel-weighting other cases by similarity: time, a three-level distance built from Spaeth issue codes, and distance in the Shepard's citation network. Bandwidths are chosen by in-sample prediction that excludes the focal case's votes. The median justice varies substantially across areas of law.
  - The authors state: "we have not found a way to generate satisfactory measures of uncertainty for our estimator." Their reason is that cases are interdependent through votes and citations, which obstructs the bootstrap (read in PDF).
  - [LSE/author PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAPSR2012.pdf); [DOI](https://doi.org/10.1017/s0003055412000469)
- Lauderdale & Clark (2014), "Scaling Politically Meaningful Dimensions Using Texts and Votes," *AJPS* 58(3):754–771.
  - LDA topic proportions λ_j of each opinion weight issue-specific ideal points θ_id. The authors call these "nontrivial identifying assumptions." The mixture restriction rules out cross-issue coalitions, and "nearly all of the possible rotations and reflections … do change predicted voting patterns under our model."
  - LDA and IRT are fit jointly by MCMC (collapsed Gibbs plus Jackman's Gibbs sampler). Topic hyperparameters are tuned for predicting votes (DIC), not text. Posterior means and SDs are reported per justice per issue (read in PDF).
  - [Author PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAJPS2014.pdf); [DOI](https://doi.org/10.1111/ajps.12085)
- Lauderdale & Clark (2016), "Estimating Vote-Specific Preferences from Roll-Call Data Using Conditional Autoregressive Priors," *JOP* 78(4):1153–1169. A CAR-prior model gives case-specific preferences for justices from 1946 to 2005. These are used to show that relative positions condition opinion assignment and joining. — [DOI](https://doi.org/10.1086/686309)

**Jurisprudential regimes**
- Pang, Friedman, Martin & Quinn (2012), "Endogenous Jurisprudential Regimes," *Political Analysis* 20(4):417–436. A multivariate multiple change-point probit estimates "the locations of many possible change-points along with structural parameters" by MCMC. Bayesian model comparison chooses the number of change-points. They find regimes in Establishment Clause and administrative-law cases and little support for several other hypothesized regimes. — [DOI](https://doi.org/10.1093/pan/mps024)
- Richards & Kritzer (2002), "Jurisprudential Regimes in Supreme Court Decision Making," *APSR* 96(2):305–320. Logistic regression with a pre-specified break at a key precedent (content-neutrality in free expression). — [DOI](https://doi.org/10.1017/s0003055402000187)
- Lax & Rader (2010), "Legal Constraints on Supreme Court Decision Making: Do Jurisprudential Regimes Exist?," *JOP* 72(2):273–284. They point out that the standard test treats votes as independent even though they cluster by case and term. A randomization test finds "little evidence that precedents affect voting." — [DOI](https://doi.org/10.1017/s0022381609990855)
- Bartels (2009), "The Constraining Capacity of Legal Doctrine on the U.S. Supreme Court," *APSR* 103(3):474–495. A multilevel model of levels of scrutiny finds that strict scrutiny (under *Grayned*) constrains ideological voting. — [DOI](https://doi.org/10.1017/s0003055409990049)

**Newer measurement-model variants (2020+)**
- Duck-Mayr & Montgomery (2023), "Ends Against the Middle: Measuring Latent Traits when Opposites Respond the Same Way for Antithetical Reasons," *Political Analysis* 31(4):606–625. A non-monotone (unfolding) item response model applied to Supreme Court votes. It accounts for liberal and conservative justices who dissent "for ideologically contradictory rationales," and it outperforms standard IRT in fit and qualitative congruence. — [DOI](https://doi.org/10.1017/pan.2022.33)
- Duck-Mayr, Garnett & Montgomery (2020), "GPIRT: A Gaussian Process Model for Item Response Theory," UAI 2020, PMLR 124:520–529. Places Gaussian-process priors on item response functions (Bayesian nonparametric IRT). — [PMLR](https://proceedings.mlr.press/v124/duck-mayr20a.html)
- Truscott & Romano (2026), "Measuring Judicial Ideology Through Text," *Journal of Law and Courts* 14(1):65–82. A hierarchical factor model on opinion text; validated by correlation with Martin–Quinn. — [DOI](https://doi.org/10.1017/jlc.2025.10004)
- Miwa (2025), "Assessing the Conservative Nature of the Supreme Court of Japan via Ideal Point Estimation of Justices," *JELS* 22(2):186–215. A dynamic IRT; the author validates that the estimates can be read as ideological positions. — [DOI](https://doi.org/10.1111/jels.12411)

**Comparative and international courts**
- Hanretty (2013), "The Decisions and Ideal Points of British Law Lords," *BJPolS* 43(3):703–716. A hierarchical IRT of non-unanimous Law Lords votes from 1969 to 2009 "is found to be no better than a null model." The locations "do not represent judges' political attitudes, only their propensity to dissent." — [DOI](https://doi.org/10.1017/s0007123412000270)
- Hanretty (2012), "Dissent in Iberia: The ideal points of justices on the Spanish and Portuguese Constitutional Tribunals," *EJPR* 51(5):671–692. — [DOI](https://doi.org/10.1111/j.1475-6765.2012.02056.x)
- Voeten (2008), "The Impartiality of International Judges: Evidence from the European Court of Human Rights," *APSR* 102(4):417–433. Based on ECtHR dissents; judges vary in how far they defer to member states. — [DOI](https://doi.org/10.1017/s0003055408080398)
- Malecki (2012), "Do ECJ judges all speak with the same voice?," *Journal of European Public Policy* 19(1):59–75. Extends IRT to "account for selective participation" in chamber judgments of the European Court of Justice, which publish no individual votes. — [DOI](https://doi.org/10.1080/13501763.2012.632143)

### Inferences
- In standard IRT, the only rule-like latent quantities are the case parameters (α_j, β_j), which put a cut line on each case. They are rarely linked to case facts or doctrine, and Clark & Lauderdale (2010) state explicitly that they do not link them to opinion locations (see Q2). These literatures therefore model who votes which way, not the logic that maps facts to outcomes.
- Pang et al. (2012) is the IRT-family paper closest to the project's target. The latent object is the fact→outcome mapping (probit coefficients on case characteristics). Its structure (number and location of regimes) gets a posterior, and models are compared by Bayesian model comparison. It is still a single court with a low-dimensional covariate set, and it has no tree or partition structure.
- Lauderdale & Clark show that side information about substance (text, citations, issue codes) can both identify a high-dimensional latent space and give its dimensions legal meaning. This is the same move as using statute text and LLM formalizations to pin down a latent decision model's coordinates.
- Hanretty (2013) is an important negative result: a well-specified Bayesian IRT can return precise but substantively meaningless latent positions. Comparing against a null model is essential.

### Gaps
- I could not confirm from the PDF excerpt which specific justices Martin & Quinn (2002) gave informative anchoring priors. The paper says only "certain justices."
- I did not verify whether GPIRT has been applied to court data.
- Bailey & Maltzman's exact likelihood is not described beyond the abstract.

## Q2. Doctrine-space, opinion-location and citation-network models of precedent (latent-space or block models)

### Takeaway
Clark & Lauderdale (2010) is the law-and-courts analogue of Hoff, Raftery & Handcock (2002). Legal texts (opinions) get latent positions, the probability that one opinion cites another positively falls with squared latent distance, and everything is estimated by MCMC with highest-density intervals. Two other papers treat a doctrinal object as latent with uncertainty:
- Clark & Lauderdale's "Genealogy of Law" (2012) puts a posterior over a discrete latent tree of precedent "parents."
- Arnold, Engst & Gschwend (2023) scale lower-court decisions from counts of references to statutory norms and case law.

Most other citation-network work in law uses descriptive centrality (Fowler et al.), geometric or PageRank constructions (Leibon et al.), community detection, or ERGMs (Schmid et al.). None of these gives a posterior over latent positions. I found no verified Hoff-style multi-dimensional latent-space model or Bayesian stochastic block model of U.S. case-citation networks.

### Cited Findings
- **Hoff, Raftery & Handcock (2002), "Latent Space Approaches to Social Network Analysis," *JASA* 97(460):1090–1098**, is the reference point. — [DOI](https://doi.org/10.1198/016214502388618906)

**Clark & Lauderdale (2010), "Locating Supreme Court Opinions in Doctrine Space," *AJPS* 54(4):871–890** (read in PDF):
- *Model.* Z is the K×K matrix of positive (1) versus negative (0) citations between opinions, with Pr(Z_kk′ = 1) = Φ(κ − λ(x_k − x_k′)²). Priors: x_k ~ N(0,1), κ ~ U(−10,10), λ ~ U(0,10). This is estimated jointly with a vote IRT, Pr(Y_ij = 1) = Φ(α_j − β_j x_i), where the case parameters have N(0, 5²) priors and "We do not link the case parameters to the estimated opinion locations." — [author PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf); [DOI](https://doi.org/10.1111/j.1540-5907.2010.00470.x)
- *Identification.* Opinions and justices are tied to a common space by assuming "that some opinions fall at certain points" — specifically, dissenting opinions are placed at their authors' ideal points. The authors call this "the most plausible assumption which identifies the relative positions of justices and opinions given our data" (read in PDF). — [author PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf)
- *Data and estimation.* Hand-coded citation polarity, refining Shepard's codes. Search and seizure: 851 opinions in 294 cases. Freedom of religion: 217 opinions in 78 cases, 1953–2006. Estimated in JAGS with 100,000 iterations thinned by 10 after a 2,000-iteration burn-in. Opinion locations are reported with 95% HDIs. The estimated ideal points correlate with Martin–Quinn at ρ ≈ 0.72; for religion, 0.87 excluding Douglas. The majority opinion locates at the median of the majority coalition (read in PDF). — [author PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf)
- *Stated limitations.*
  - κ and λ are constant across opinions, so "we will underestimate or overestimate the uncertainty in the opinion locations" of very narrow or very broad opinions. Hierarchical versions were tried, but "the priors governing shrinkage determine the results."
  - A pure proximity model is assumed rather than a directional one.
  - Uncited precedents are assumed missing at random.
  - "There are not enough precedents commonly cited across these two sets of cases to link the two dimensions" (read in PDF). — [author PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf)

**Clark & Lauderdale (2012), "The Genealogy of Law," *Political Analysis* 20(3):329–350** (read in PDF):
- Each majority opinion has one latent "parent" precedent. The probability that an opinion cites a precedent is logit-linear in their distance in the tree. Data are citation counts between majority opinions through the October 2009 term.
- Maximum likelihood over trees is infeasible because the number of trees "grows as (n − 1)!". Bayesian MCMC is chosen because it gives "an uncertainty estimate over possible trees." The authors warn that with "multiple modes that describe very different trees, the sampler will still have a difficult time moving between the two modes." They report the posterior probability of the most likely parent for each case.
- [Author PDF](https://www.tomclarkphd.com/files/ClarkLauderdalePA2012.pdf); [DOI](https://doi.org/10.1093/pan/mps019)

**Arnold, Engst & Gschwend (2023), "Scaling Court Decisions with Citation Networks," *Journal of Law and Courts* 11(1):25–44**:
- A latent-variable model places decisions in a common case space using "the widely available references in court decisions," as an alternative to voting records. The application is forum shopping and forum selling in German lower courts. — [DOI](https://doi.org/10.1086/717420); [MZES](https://www.mzes.uni-mannheim.de/en/publications/details/scaling-court-decisions-with-citation-networks)
- Appendix (read in PDF):
  - The input is a decision × legal-source matrix whose sources include statutory norms such as BGB §823 and KUG §§22–23, alongside case law. The model is Bayesian, with a Poisson link for counts and a logit link for binary toy data, and draws 8,000 posterior samples. Rotational invariance is handled by "flipping." Results are shown with central 90% credible intervals.
  - Validation includes toy recovery against randomly rewired null matrices, posterior predictive checks on resampled decision–source matrices, and agreement with hand-coded decision outcomes "accounting for the credible intervals."
  - [AEG appendix PDF](https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/AEG_JLC.pdf)

**Citation networks without latent positions**
- Fowler, Johnson, Spriggs, Jeon & Wahlbeck (2007), "Network Analysis and the Law: Measuring the Legal Importance of Precedents at the U.S. Supreme Court," *Political Analysis* 15(3):324–346. Covers 26,681 majority opinions from 1791 to 2005. Hub/authority "importance scores" are validated by correlation with future citations by state courts, the Courts of Appeals and the Supreme Court. No posterior uncertainty is reported. — [DOI](https://doi.org/10.1093/pan/mpm011)
- Fowler & Jeon (2008), "The authority of Supreme Court precedent," *Social Networks* 30(1):16–30. — [DOI](https://doi.org/10.1016/j.socnet.2007.05.001)
- Bommarito, Katz, Zelner & Fowler (2010), "Distance measures for dynamic citation networks," *Physica A* 389(19):4201–4208. — [DOI](https://doi.org/10.1016/j.physa.2010.06.003)
- Leicht, Clarkson, Shedden & Newman (2007), "Large-scale structure of time evolving citation networks," *Eur. Phys. J. B* 59(1):75–83. Fits a "stochastic mixture model of the citation process" by EM to Supreme Court citations: latent groups of opinions, each with its own time profile of incoming citations. It is compared with modularity-based community detection (read in PDF). — [arXiv PDF](https://arxiv.org/pdf/0706.0015); [IDEAS](https://ideas.repec.org/a/spr/eurphb/v59y2007i1p75-83.html)
- Schmid, Chen & Desmarais (2022), "Generative Dynamics of Supreme Court Citations: Analysis with a New Statistical Network Model," *Political Analysis* 30(4):515–534. Introduces the citation ERGM for dyad-level citations with network dependence, with software. Dependence effects are reported to be as important as case covariates. — [DOI](https://doi.org/10.1017/pan.2021.20); [arXiv](https://www.arxiv.org/abs/2101.07197)
- Leibon, Livermore, Harder, Riddell & Rockmore (2018), "Bending the law: geometric tools for quantifying influence in the multinetwork of legal opinions," *AI and Law* 26(2):145–167. A network combining citation and topic similarity, with a probabilistic search model that yields a PageRank-style geometry of the opinion corpus. — [DOI](https://doi.org/10.1007/s10506-018-9224-2)
- Dadgostari, Guim, Beling, Livermore & Rockmore (2021), "Modeling law search as prediction," *AI and Law* 29(1):3–34. Verified from metadata only. — [DOI](https://doi.org/10.1007/s10506-020-09261-5)
- Lupu & Voeten (2012), "Precedent in International Courts: A Network Analysis of Case Citations by the European Court of Human Rights," *BJPolS* 42(2):413–439. — [DOI](https://doi.org/10.1017/s0007123411000433)
- Katz & Bommarito (2014), "Measuring the complexity of the law: the United States Code," *AI and Law* 22(4):337–374. This is network and complexity analysis of statutes, not a latent model. Verified from metadata only. — [DOI](https://doi.org/10.1007/s10506-014-9160-8)
- At very large scale, Ovcharov (arXiv 2605.15362, May 2026) builds a citation graph of 99.5 million Ukrainian court decisions (502 million links). It uses Louvain community detection, not a stochastic block model or Bayesian method. — [emergentmind summary of arXiv 2605.15362](https://www.emergentmind.com/papers/2605.15362)

### Inferences
- Clark & Lauderdale (2010) has every Hoff–Raftery–Handcock ingredient: latent positions, a distance link and an MCMC posterior. Its limits relative to the project's needs:
  - one dimension and one issue area at a time;
  - hand-coded citation polarity;
  - identification by a substantive tethering assumption;
  - a latent object (opinion location) that is a one-dimensional summary of doctrine, not the rule's internal logic.
- "Genealogy of Law" is the closest precedent for a posterior over a discrete legal structure. Its admitted difficulty — MCMC mixing across modes that describe very different trees — is directly relevant to posteriors over decision trees or process graphs, which face the same combinatorial, multimodal posterior.
- Arnold, Engst & Gschwend (2023) is the first verified model in which statutory provisions are columns of the measurement matrix and decisions are scaled against them. A natural extension, which I did not find in the literature, is a joint latent space of provisions and decisions in which provisions also get interpretable positions with posterior uncertainty.

### Gaps
- No verified Hoff-type latent-space model (two or more dimensions, with posterior) or Bayesian stochastic block model of U.S. case-citation networks turned up.
- A search snippet mentioned a stochastic-block-model framework for "core clusters of precedents" in CJEU co-citation networks ([arts.units.it record](https://arts.units.it/handle/11368/3118138)), but I could not open or verify it. **[UNVERIFIED]**
- Miller (2021), "'Justice X, dissenting': A Citation-Network Approach to Mapping Judicial Ideology" (SSRN, [DOI](https://doi.org/10.2139/ssrn.3811403)): title and metadata verified, but I could not get the abstract or method. **[UNVERIFIED content]**
- I did not check whether Leicht et al. report uncertainty for group membership.

## Q3. Lower-court, collegial-panel and agency/administrative applications of latent-variable models

### Takeaway
- **Lower federal and state courts.** Latent positions mostly come from bridging (the Judicial Common Space) or from campaign-finance scaling (CFscores), not from votes. Vote-based IRT is used for state courts of last resort (Windett et al.).
- **Panels.** Latent preferences are recovered with structural models of consensus voting (Fischman) or of panel aggregation (Hangartner, Lauderdale & Spirig 2025). The latter puts a posterior over which aggregation rule governs a decision: a latent decision-procedure model, applied to asylum adjudication.
- **Agencies.** Latent agency preferences are measured by combining expert raters in a multirater IRT (Clinton & Lewis 2008).
- I found no IRT or ideal-point model of U.S. immigration judges or SSA ALJs. Most adjudicator-heterogeneity work treats judges as fixed effects or instruments.

### Cited Findings
**Lower federal and state courts**
- Epstein, Martin, Segal & Westerland (2007), "The Judicial Common Space," *JLEO* 23(2):303–325. Places lower-court judges and justices in one policy space to test models of the judicial hierarchy. — [DOI](https://doi.org/10.1093/jleo/ewm024)
- Windett, Harden & Hall (2015), "Estimating Dynamic Ideal Points for State Supreme Courts," *Political Analysis* 23(3):461–469. Combines CFscores with dynamic IRT on votes for all 52 state courts of last resort, 1995–2010, in a common space. — [Cambridge](https://resolve.cambridge.org/core/journals/political-analysis/article/abs/estimating-dynamic-ideal-points-for-state-supreme-courts/2A5D345E30195741693BCE72C8988C69); [IDEAS](https://ideas.repec.org/a/cup/polals/v23y2015i03p461-469_01.html)
- Bonica & Woodruff (2015), "A Common-Space Measure of State Supreme Court Ideology," *JLEO* 31(3):472–498. Based on campaign-finance records. — [DOI](https://doi.org/10.1093/jleo/ewu016)
- Bonica & Sen (2017), "A Common-Space Scaling of the American Judiciary and Legal Profession," *Political Analysis* 25(1):114–121. Covers 840 federal judges and 380,307 attorneys. — [IDEAS](https://ideas.repec.org/a/cup/polals/v25y2017i01p114-121_00.html); [Harvard](https://msen.scholars.harvard.edu/judges-scaling)
- Bonica & Sen (2021), "Estimating Judicial Ideology," *Journal of Economic Perspectives* 35(1):97–118. Reviews measures from the Supreme Court down to the lowest state courts. — [DOI](https://doi.org/10.1257/jep.35.1.97)
- Badas (2025), "Measuring Ideological Polarization on the Circuit Courts of Appeals 1953–2022," *Journal of Law and Courts* 13(2):463–478. — [DOI](https://doi.org/10.1017/jlc.2024.16)
- Robinson, Leslie & Sheppard (2022), "Judicial Ideology in the Absence of Rights," *Journal of Law and Courts* 10(2):239–264. Uses an ex ante ideology measure for every Australian High Court decision from 1995 to 2019. — [DOI](https://doi.org/10.1086/716187)

**Collegial panels and asylum adjudication**
- Fischman (2011), "Estimating Preferences of Circuit Judges: A Model of Consensus Voting," *Journal of Law and Economics* 54(4):781–809. A structural model with a "cost of dissent," applied to asylum appeals. Although 95% of decisions were unanimous, "roughly half of the cases could have been decided differently if assigned to different panels." — [DOI](https://doi.org/10.1086/661512)
- Fischman (2015), "Interpreting Circuit Court Voting Patterns: A Social Interactions Framework," *JLEO* 31(4):808–842. Each colleague's vote raises a judge's probability of voting the same way by about 40 percentage points. — [DOI](https://doi.org/10.1093/jleo/ews042)
- Fischman (2014; published online 2013), "Measuring Inconsistency, Indeterminacy, and Error in Adjudication," *American Law and Economics Review* 16(1):40–85. Using immigration adjudication data, he shows that inter-judge inconsistency "cannot be identified" as a point but can be bounded. Indeterminacy and error rates are only set-identified. — [DOI](https://doi.org/10.1093/aler/aht011)
- Hangartner, Lauderdale & Spirig (2025), "Inferring Individual Preferences from Group Decisions: Judicial Preference Variation and Aggregation on Collegial Courts," *BJPolS* 55, e163.
  - Setting: three-judge, per-curiam panels of the Swiss Federal Administrative Court on asylum appeals.
  - Method: estimate which decision-theoretic aggregation rule fits (majority rule, chair-as-dictator, minimum/maximum, or a mixture) and infer judges' thresholds. Estimation is Bayesian MCMC with hierarchical random-effects priors per judge, and models are compared by DIC.
  - Results: chair-as-dictator applies in 45% of cases. Under some rules the most extreme judges' preferences can be bounded but not point-identified. The assumption of exogenous assignment is validated (read in PDF).
  - [Open-access PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/730D69EA18C5ADDB29891E07588FA5A2/S0007123425100574a.pdf/inferring-individual-preferences-from-group-decisions-judicial-preference-variation-and-aggregation-on-collegial-courts.pdf); [DOI](https://doi.org/10.1017/S0007123425100574)

**Agencies and institutions**
- Clinton & Lewis (2008), "Expert Opinion, Agency Characteristics, and Agency Preferences," *Political Analysis* 16(1):3–20. A multirater item response model combines expert ratings of 82 executive agencies (1988–2005) with objective agency characteristics and reports standard errors. — [DOI](https://doi.org/10.1093/pan/mpm009)
- Linzer & Staton (2015), "A Global Measure of Judicial Independence, 1948–2012," *Journal of Law and Courts* 3(2):223–256. A dynamic latent-variable model for an institutional property of courts, not of individual judges: 200 countries. It handles temporal dependence, a bounded latent quantity, missing data and indicator measurement error. — [DOI](https://doi.org/10.1086/682150)
- Ho & Sherman (2017), "Managing Street-Level Arbitrariness: The Evidence Base for Public Sector Quality Improvement," *Annual Review of Law and Social Science* 13:251–272. A review of inconsistency in bureaucratic decisions and of quality-assurance tools; not a latent model. — [DOI](https://doi.org/10.1146/annurev-lawsocsci-110316-113608)
- Frandsen, Lefgren & Leslie (2023), "Judging Judge Fixed Effects," *AER* 113:253–277. Judge designs in economics treat adjudicators as fixed effects or instruments, not as latent positions. — [DOI](https://doi.org/10.1257/aer.20201860)

### Inferences
- Hangartner, Lauderdale & Spirig (2025) is the closest verified analogue to "posterior over a latent decision procedure." The procedure is how a panel aggregates individual thresholds, not the statute's logic, and the uncertainty is a mixture weight over a few candidate rules. Their partial-identification results (bounds for extreme judges) show the identification limits the project should expect when only aggregate outcomes are observed.
- Clinton & Lewis's multirater IRT (and Clinton & Lapinski's, Q4) is the nearest template for treating several LLM formalizations as noisy "raters" of one latent structure, each with its own bias and precision.
- Fischman's partial-identification results for immigration adjudication match the project's rule that convergence is not identification. Without random assignment or covariates, the true process can only be bounded from aggregate outcomes.

### Gaps
- I found no IRT or ideal-point model of individual U.S. immigration judges, SSA ALJs, the NLRB or other agency adjudicators. Search snippets pointed to NLRB panel-composition studies but no verified latent-variable paper. This may partly reflect the exhausted search quota.
- No latent-variable model of administrative processing timing (as opposed to decisions) turned up in this strand.

## Q4. Work placing legal rules or statutory provisions (not people) in a latent space or latent classes with posterior uncertainty

### Takeaway
This is rare. The verified cases where a legal rule, text or statute (rather than a person) is the latent object with quantified uncertainty are:
1. Opinion locations in doctrine space (Clark & Lauderdale 2010).
2. A latent precedent tree (Clark & Lauderdale 2012).
3. Decision positions scaled against statutory norms (Arnold et al. 2023).
4. Latent regime structure in the fact→outcome mapping (Pang et al. 2012).
5. Latent "significance" of every public statute, from a multirater IRT (Clinton & Lapinski 2006).
6. Bill, proposal and status-quo locations on the ideal-point scale (Clinton & Meirowitz 2001; Peress 2013; Battista, Peress & Richman 2022).

Two further strands frame rules as functions of facts but give no posterior over the rule itself:
- **Case-space theory** treats rules as partitions of fact space (Lax 2007, 2011; Callander & Clark 2017).
- **Empirical rule-fitting** is either frequentist or algorithmic (Segal 1984 probit fact patterns; Kastellec 2010 classification trees).

### Cited Findings
**Statutes and policies as latent objects**
- Clinton & Lapinski (2006), "Measuring Legislative Accomplishment, 1877–1994," *AJPS* 50(1):232–249. Item response theory over a dataset of every public statute estimates each statute's latent "legislative importance." Several scholars' and chroniclers' lists of notable enactments are aggregated as raters: nine assessments covering 21,741 public statutes from 1877 to 1948. The "estimates and associated standard errors" are reported. — [DOI](https://doi.org/10.1111/j.1540-5907.2006.00181.x); [Vanderbilt PDF](https://cdn.vanderbilt.edu/vu-my/wp-content/uploads/sites/349/2011/10/14093745/CL_AJPS2006.pdf)
- Caughey & Warshaw (2016), "The Dynamics of State Policy Liberalism, 1936–2014," *AJPS* 60(4):899–913. A dynamic latent-variable model over 148 state policies. States are the latent units and policies are the items, so item parameters describe each policy. They find "surprisingly little evidence of multidimensionality in state policy outputs." — [DOI](https://doi.org/10.1111/ajps.12219)
- Clinton & Meirowitz (2001), "Agenda Constrained Legislator Ideal Points and the Spatial Voting Model," *Political Analysis* 9(3):242–259. Standard estimators ignore "information that identifies the proposal locations"; using the sequential agenda recovers them. — [DOI](https://doi.org/10.1093/polana/9.3.242)
- Peress (2013), "Estimating Proposal and Status Quo Locations Using Voting and Cosponsorship Data," *JOP* 75(3):613–631. Standard ideal-point methods "only recover cutpoints." Jointly scaling votes and cosponsorship puts proposals, final bills and status quos on the ideal-point scale. — [DOI](https://doi.org/10.1017/s0022381613000571)
- Battista, Peress & Richman (2022), "Estimating the locations of voters, politicians, policy outcomes, and status quos on a common scale," *Political Science Research and Methods* 10(4):806–822. — [DOI](https://doi.org/10.1017/psrm.2021.42)

**Opinions, precedents and decisions as latent objects** (details in Q2)
- Clark & Lauderdale (2010) estimate opinion locations with 95% HDIs. — [DOI](https://doi.org/10.1111/j.1540-5907.2010.00470.x)
- Clark & Lauderdale (2012) estimate posterior parenthood probabilities in a latent precedent tree. — [DOI](https://doi.org/10.1093/pan/mps019)
- Arnold, Engst & Gschwend (2023) estimate decision positions from references to statutory norms and case law, with 90% credible intervals. — [DOI](https://doi.org/10.1086/717420)
- Carrubba, Friedman, Martin & Vanberg (2012), "Who Controls the Content of Supreme Court Opinions?," *AJPS* 56(2):400–412. Theory predicting that opinion content reflects the median of the majority coalition, tested empirically; Clark & Lauderdale (2010) find support for this prediction. — [DOI](https://doi.org/10.1111/j.1540-5907.2011.00557.x)

**Rules as functions of facts (case space)**
- Lax (2007), "Constructing Legal Rules on Appellate Courts," *APSR* 101(3):591–604. In a "case-space" model, preferences take the form of legal rules. He shows that a collegial "median rule" exists "even if there is no single median judge." — [DOI](https://doi.org/10.1017/s0003055407070347)
- Lax (2011), "The New Judicial Politics of Legal Doctrine," *Annual Review of Political Science* 14:131–157. The case-space model expresses ideological differences "in terms of legal rules that partition fact-filled legal cases into different dispositions." — [DOI](https://doi.org/10.1146/annurev.polisci.042108.134842)
- Lax (2012), "Political Constraints on Legal Doctrine: How Hierarchy Shapes the Law," *JOP* 74(3):765–781. Verified from metadata only. — [DOI](https://doi.org/10.1017/s002238161200045x)
- Callander & Clark (2017), "Precedent and Doctrine in a Complicated World," *APSR* 111(1):184–203. Judges learn a "complicated relationship between facts and legal outcomes" — a latent stochastic mapping — from cases, which yields path dependence in the common law. — [DOI](https://doi.org/10.1017/s0003055416000587)
- Baker & Mezzetti (2012), "A Theory of Rational Jurisprudence," *Journal of Political Economy* 120(3):513–551. Verified from metadata only. — [DOI](https://doi.org/10.1086/666655)
- Segal (1984), "Predicting Supreme Court Cases Probabilistically: The Search and Seizure Cases, 1962–1981," *APSR* 78(4):891–900. A probit of outcomes on case facts. — [DOI](https://doi.org/10.2307/1955796)
- Kastellec (2010), "The Statistical Analysis of Judicial Decisions and Legal Rules with Classification Trees," *JELS* 7(2):202–230. Classification trees as "a flexible way to study legal doctrine," applied to Supreme Court search-and-seizure cases and Courts of Appeals confession cases. — [DOI](https://doi.org/10.1111/j.1740-1461.2010.01176.x); [IDEAS](https://ideas.repec.org/a/wly/empleg/v7y2010i2p202-230.html)
- Kastellec & Lax (2008), "Case Selection and the Study of Judicial Politics," *JELS* 5(3):407–446. Simulations show that inferential problems from discretionary case selection "range from moderate to severe." This matters for whether doctrine can be identified from observed cases. — [DOI](https://doi.org/10.1111/j.1740-1461.2008.00129.x)
- Wahlbeck (1997), "The Life of the Law: Judicial Politics and Legal Change," *JOP* 59(3):778–802. Verified from metadata only. — [DOI](https://doi.org/10.2307/2998637)

### Inventory: what each closest paper treats as latent, and what it does not do

| Work | Latent object | Identifying data | Uncertainty and validation | Not done (relative to latent decision or process structure) |
|---|---|---|---|---|
| Martin & Quinn 2002 ([DOI](https://doi.org/10.1093/pan/10.2.134)) | Justice ideal points (dynamic); case cutpoints as nuisance | Merits votes, reverse/affirm | MCMC; posterior SD and 95% CI; correlation with external scales | No facts→outcome rule; case parameters not interpreted |
| Lauderdale & Clark 2012 ([DOI](https://doi.org/10.1017/s0003055412000469)) | Case-specific justice orderings | Votes + time, issue codes and citation similarity | In-sample prediction; **no uncertainty measure** (stated) | Doctrine only sets similarity weights |
| Lauderdale & Clark 2014 ([DOI](https://doi.org/10.1111/ajps.12085)) | Issue-specific ideal points; topic mixtures per case | Votes + opinion text (LDA) | Joint MCMC; posterior SDs; DIC | Topics stand in for doctrine; no rule structure |
| Pang et al. 2012 ([DOI](https://doi.org/10.1093/pan/mps024)) | Number and location of regime change-points; fact coefficients | Votes + case facts | MCMC; Bayesian model comparison | Linear probit within regimes; one court |
| Clark & Lauderdale 2010 ([DOI](https://doi.org/10.1111/j.1540-5907.2010.00470.x)) | **Opinion locations** + justice ideal points | Hand-coded citation polarity + votes | JAGS MCMC; 95% HDIs; correlation with Martin–Quinn | 1-D; tethered by assumption; no internal rule logic |
| Clark & Lauderdale 2012 ([DOI](https://doi.org/10.1093/pan/mps019)) | **Latent precedent tree** (discrete) | Citation counts between majority opinions | MCMC posterior parenthood probabilities | Single-parent tree; mixing across modes hard |
| Arnold, Engst & Gschwend 2023 ([DOI](https://doi.org/10.1086/717420)) | **Decision positions** in case space | Counts of references to statutes and case law | 8,000 posterior draws; 90% CI; posterior predictive checks; null models; hand-coded outcomes | Positions of the legal sources themselves not reported as primary output (my read; unverified) |
| Hangartner, Lauderdale & Spirig 2025 ([DOI](https://doi.org/10.1017/S0007123425100574)) | Judge thresholds + **latent aggregation rule** (mixture) | Per-curiam panel decisions with exogenous assignment | MCMC; DIC; bounds for extreme judges | Aggregation rule, not statutory logic |
| Clinton & Lapinski 2006 ([DOI](https://doi.org/10.1111/j.1540-5907.2006.00181.x)) | **Statute significance** | Nine rater lists × all statutes | IRT standard errors | 1-D importance, not content or logic |
| Clinton & Lewis 2008 ([DOI](https://doi.org/10.1093/pan/mpm009)) | Agency preferences | Multiple expert raters + covariates | Multirater IRT standard errors | Agencies, not rules |
| Peress 2013 ([DOI](https://doi.org/10.1017/s0022381613000571)) | **Proposal and status-quo locations** | Votes + cosponsorship + record | Ideal-point scale | Legislative, not legal-logic structure |
| Kastellec 2010 ([DOI](https://doi.org/10.1111/j.1740-1461.2010.01176.x)) | Rule as tree over case facts | Case facts + outcomes | Not Bayesian (uncertainty handling **[UNVERIFIED]**) | No posterior over trees |

### Inferences
- The literature has come closest to "rules as latent objects with posterior uncertainty" in three verified ways:
  - opinions as points in a one-dimensional doctrine space (2010);
  - a posterior over a discrete precedent genealogy (2012);
  - decisions scaled against statutory norms (2023).

  None places the decision logic of a statute (conditions, branches, required steps) in a latent space or latent class structure with a posterior. The theoretical object exists — the case-space partition, or Callander–Clark's latent mapping from facts to outcomes — but has not been estimated Bayesianly as a structure.
- The statute-level analogues (Clinton & Lapinski; Caughey & Warshaw) give each statute or policy a scalar latent trait (importance, liberalism), not a structure. Still, their multirater and multi-item designs map directly onto the project's setup: several LLM formalizations act as raters, and each provision or step is an item.
- Peress's point that standard ideal-point methods "only recover cutpoints" parallels the project's identification problem. Without extra data (cosponsorship there; statute text and timing records here), the locations of rules themselves are not identified from outcomes alone.

### Gaps
- **[UNVERIFIED]** Law & Versteeg, "The Evolution and Ideology of Global Constitutionalism": the SSRN record (2010) is verified ([DOI](https://doi.org/10.2139/ssrn.1633108)). I recall it being published in *California Law Review* (2011) and scaling constitutional rights provisions into latent dimensions, but I could verify neither the journal venue nor the method.
- I did not verify Kastellec (2010)'s treatment of uncertainty (pruning, cross-validation or bootstrap) beyond the abstract. The author's PDF link returned HTML.
- I found no verified Bayesian latent-class or latent-tree model of statutory provisions, nor any model combining several formalizations of one statute.

## Q5. How these papers handle identifiability (rotation/reflection, anchoring) and validate uncertainty

### Takeaway
**Identification** is handled by:
1. priors that fix scale and location, plus informative priors on known actors (Martin & Quinn);
2. hierarchical predictors (Bafumi et al.);
3. substantive tethering assumptions (dissents placed at their authors' ideal points in Clark & Lauderdale 2010);
4. side information that fixes rotation (topic mixture weights in Lauderdale & Clark 2014);
5. post-hoc sign flipping (Arnold et al.);
6. bridging actors or observations across institutions (Bailey; the Judicial Common Space; CFscores).

**Validation** is mostly:
- face validity and correlation with external measures;
- predictive performance;
- Bayesian model comparison (e.g., DIC);
- posterior predictive checks;
- comparison against null or randomized data.

Formal calibration checks of posterior intervals (coverage under known truth) are rare. Several key papers state openly that their uncertainty is missing, misstated or only partially identified.

### Cited Findings
**How identification is achieved**
- Martin & Quinn (2002): IRT parameters are "identified only up to an arbitrary scale factor" and suffer "rotational invariance." Prior variances on θ, α and β "define the metric," and informative priors on certain justices select one posterior mode (read in PDF). — [PDF](https://www.cs.princeton.edu/courses/archive/fall09/cos597A/papers/MartinQuinn2002.pdf)
- Bafumi et al. (2005): scale, translation and reflection invariance are addressed with hierarchical models, linear transformations and informative regression predictors. — [Cambridge](https://www.cambridge.org/core/journals/political-analysis/article/practical-issues-in-implementing-and-understanding-bayesian-ideal-point-estimation/748E80D1DDD69FCF2EECEBFCE47FC355)
- Lauderdale & Clark (2014): topic mixture weights act as "nontrivial identifying assumptions." They rule out some cutting lines and break nearly all rotations and reflections of multidimensional IRT (read in PDF). — [PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAJPS2014.pdf)
- Clark & Lauderdale (2010): opinions and justices share a scale through the assumption that dissenting opinions sit at their authors' ideal points. Hierarchical opinion-specific parameters are not identified ("the priors governing shrinkage determine the results") (read in PDF). — [PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf)
- Arnold, Engst & Gschwend (2023): "flipping to solve rotational invariance" (read in appendix). — [PDF](https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/AEG_JLC.pdf)
- Moser, Rodríguez & Lofland (2021), "Multiple Ideal Points: Revealed Preferences in Different Domains," *Political Analysis* 29(2):139–166. Applied to legislative voting. Their key move is to "*estimate* rather than *assume* the identity of 'stayers'" — the voters whose preferences are constant across domains and so anchor the common scale. — [DOI](https://doi.org/10.1017/pan.2020.21)
- Bridging approaches: Bailey (2007) ([DOI](https://doi.org/10.1111/j.1540-5907.2007.00260.x)); Epstein et al. (2007) ([DOI](https://doi.org/10.1093/jleo/ewm024)); Bonica & Sen (2017) ([IDEAS](https://ideas.repec.org/a/cup/polals/v25y2017i01p114-121_00.html)).
- Peress (2013): proposal and status-quo locations are not identified from votes alone, which "only recover cutpoints." Cosponsorship data are needed. — [DOI](https://doi.org/10.1017/s0022381613000571)
- Hangartner, Lauderdale & Spirig (2025): under some aggregation rules the most extreme judges can only be bounded. Identification relies on repeated, exogenous panel assignment (read in PDF). — [PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/730D69EA18C5ADDB29891E07588FA5A2/S0007123425100574a.pdf/inferring-individual-preferences-from-group-decisions-judicial-preference-variation-and-aggregation-on-collegial-courts.pdf)
- Fischman (2014): inter-judge inconsistency, indeterminacy and error are only set-identified from observational single-judge data. — [DOI](https://doi.org/10.1093/aler/aht011)

**How uncertainty is validated, or where it is admitted to be missing**
- Validation by external correlation:
  - Martin & Quinn (2002) against Segal–Cover and issue-area voting ([PDF](https://www.cs.princeton.edu/courses/archive/fall09/cos597A/papers/MartinQuinn2002.pdf));
  - Clark & Lauderdale (2010) against Martin–Quinn ([PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf));
  - Truscott & Romano (2026) against Martin–Quinn ([DOI](https://doi.org/10.1017/jlc.2025.10004));
  - Fowler et al. (2007) against future citation behavior ([DOI](https://doi.org/10.1093/pan/mpm011)).
- Model comparison:
  - Bayesian model comparison over the number of change-points (Pang et al. 2012) ([DOI](https://doi.org/10.1093/pan/mps024));
  - DIC for aggregation rules (Hangartner et al. 2025) ([PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/730D69EA18C5ADDB29891E07588FA5A2/S0007123425100574a.pdf/inferring-individual-preferences-from-group-decisions-judicial-preference-variation-and-aggregation-on-collegial-courts.pdf));
  - vote-prediction DIC (Lauderdale & Clark 2014) ([PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAJPS2014.pdf)).
- Posterior predictive checks and null models:
  - Arnold et al. (2023): toy recovery, rewired and resampled null matrices, and posterior predictive checks ([PDF](https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/AEG_JLC.pdf));
  - Hanretty (2013): IRT no better than a null model ([DOI](https://doi.org/10.1017/s0007123412000270));
  - Jackman (2001) has "Model Checking" in its title ([DOI](https://doi.org/10.1093/polana/9.3.227)).
- Prediction as validation:
  - Martin, Quinn, Ruger & Kim (2004), "Competing Approaches to Predicting Supreme Court Decision Making," *Perspectives on Politics* 2(4):761–767 ([DOI](https://doi.org/10.1017/s1537592704040502)), with the companion piece Ruger et al. (2004), *Columbia Law Review* 104(4):1150 ([DOI](https://doi.org/10.2307/4099370));
  - Katz, Bommarito & Blackman (2017), "A general approach for predicting the behavior of the Supreme Court of the United States," *PLOS ONE* 12(4):e0174698 (verified from metadata only) ([DOI](https://doi.org/10.1371/journal.pone.0174698)).
- Explicit admissions that uncertainty is absent or misstated:
  - Lauderdale & Clark (2012): "we have not found a way to generate satisfactory measures of uncertainty for our estimator" ([PDF](https://www.tomclarkphd.com/files/LauderdaleClarkAPSR2012.pdf));
  - Clark & Lauderdale (2010): constant κ and λ will "underestimate or overestimate the uncertainty in the opinion locations" ([PDF](https://www.tomclarkphd.com/files/ClarkLauderdaleAJPS2010.pdf));
  - Clark & Lauderdale (2012): MCMC may fail to move between modes describing very different trees ([PDF](https://www.tomclarkphd.com/files/ClarkLauderdalePA2012.pdf)).
- Case-selection bias: Kastellec & Lax (2008) use simulation to show that discretionary case selection can severely bias inferences about doctrine and compliance. — [DOI](https://doi.org/10.1111/j.1740-1461.2008.00129.x)
- Dependence among observations: Lax & Rader (2010) show that treating clustered votes as independent overstates the evidence for regime change ([DOI](https://doi.org/10.1017/s0022381609990855)). Schmid et al. (2022) argue that citation dependence must be modeled for covariate standard errors to be reliable ([DOI](https://doi.org/10.1017/pan.2021.20)).

### Inferences
- For discrete or structured latent objects such as decision trees or process graphs, the analogue of reflection and rotation invariance is label switching and equivalent re-parameterization: different trees that yield the same predictions. Genealogy of Law shows this shows up as poor MCMC mixing across modes, not as a simple sign flip.
- The analogue of Clark & Lauderdale's tethering for the project is anchoring latent rule structure to statute text: fixing some components to positions the text requires, the way dissents are fixed to their authors. This makes identification depend on the substantive anchor, and the 2010 paper does not test the anchor.
- None of the verified court papers reports interval coverage against known truth. The closest is Arnold et al.'s toy recovery and null comparisons. A synthetic benchmark with known structure, which the project has, would go beyond current practice in this literature.
- Partial identification (Fischman 2014; Hangartner et al. 2025) is the honest end state when only aggregate outcomes are observed. Reporting bounds rather than forcing point posteriors is precedented.

### Gaps
- I found no formal study of the calibration or coverage of court ideal-point posteriors (for example, simulation-based calibration). The search was cut short by the exhausted quota, so this is not conclusive.
- Whether Bailey & Maltzman (2008), Windett et al. (2015) or Miwa (2025) run posterior predictive checks is not verified.
