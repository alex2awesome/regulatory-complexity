# Related work: Bayesian machinery for a latent process inferred from partial evidence

Assembled 2026-09-15. Companion to `docs/2026-09-15-generative-model.md` (the model we are building) and
`docs/2026-09-15-process-benchmarks-plan.md` (what we have measured). `docs/related-work.md` covers the
*substantive* axes — complexity metrics, burden, discretion. This file covers only the **statistical
machinery**, and only the parts that bear on inference.

**Verification.** This session's WebSearch budget was exhausted before the review began, so every work
below was verified by direct fetch against the Crossref REST API, the arXiv API and abstract pages,
OpenAlex, the ACL Anthology, JMLR/PMLR, Project Euclid, or a publisher page. Crossref returns title,
full author list, venue, volume, pages and DOI in one record, which is a stricter check than a search
snippet. Legend: unmarked = verified against at least one authoritative record; **UNVERIFIED** = flagged
inline with the specific field that could not be confirmed. Nothing here is cited from memory alone.
IMS/ISBA journals (*Annals of Statistics*, *Annals of Applied Statistics*, *Bayesian Analysis*) do not
supply page ranges to Crossref; those are omitted rather than guessed.

---

## 0. The map, and the two findings that reorganise it

Our problem, stated so that analogues are findable: **a latent multi-actor workflow — a partial order of
steps, each with an actor from a known-ish universe, a duration distribution, a fee, and a visibility
class — must be inferred from heterogeneous partial evidence.** The evidence is (a) published documents
whose kind determines what they disclose, (b) selection-biased user reports generated from individual
cases, (c) occasional case traces. The number of steps is unknown; evidence arrives sequentially and each
document may confirm, refine, contradict or extend; sources conflict, sometimes because the rule genuinely
changed; timing is non-stationary; and an LLM is the extractor, so its error rates are model parameters.

### 0.1 Which literature owns which latent

| latent quantity | literature that owns it | closest single work | verdict |
|---|---|---|---|
| how many steps exist | **not** BNP mixtures — occupancy / multiple-systems estimation | Dorazio & Royle 2005 (§8.11) | reframe the estimand (§0.2) |
| is this a new step or one I hold | Bayesian entity resolution with a nonparametric prior | Yang, Cardie & Frazier 2015 (§2.9) | closest existing machinery, as the brief guessed |
| does step *s* exist | site-occupancy models with covariate-dependent detection | MacKenzie et al. 2002 (§8.10) | exact structural match for this layer |
| who owns step *s* | Dawid–Skene / truth discovery | Egami & Shin 2026 (§4.15) | gold-free identification now exists |
| a document's silence | truth discovery with a silent rate; open-world KB completeness | Zhi et al. 2015 (§3.8) | one paper, and it is ours to extend |
| the partial order | Bayesian partial orders from linear extensions | Nicholls et al. 2025 (§6.1) | **best structural analogue overall** |
| rework loops | nothing in the poset literature — structurally impossible | process trees (§7.6); Mutual Hazard Networks (§6.8) | genuinely open |
| durations, drifting and jumping | hierarchical shrinkage first, intervention analysis second | Jones & Ackerson 1990 (§9.3) | it is not a per-series time-series problem (§9.1) |
| duration evidence of five kinds | coarse data; multi-parameter evidence synthesis | Heitjan & Rubin 1991 (§9.8); Ades & Sutton 2005 (§11.3) | assembled, with one bias we are exposed to |
| selection tilt in user reports | **not** selection bias — measurement/estimand mismatch | Mathiowetz & Duncan 1988 (§10.11) | our wrong sign is the *modal* finding |
| which document to read next | Bayesian experimental design | Rainforth et al. 2023 (§11.6) | unused by us so far |
| the extractor's own error | weak supervision; prediction-powered inference | Egami & Shin 2026 (§4.15) | strongest new result in the review |

### 0.2 Finding one: "how many steps" must not be a mixture-component count

Two areas of the review converged on this independently, which is why it leads.

Our design says the step count comes from a CRP/DP posterior over partitions. The nonparametric literature
says that posterior is not trustworthy. Miller & Harrison (§1.7) **prove** that DP and Pitman–Yor mixture
posteriors on the number of components do not concentrate on the truth; Cai, Campbell & Broderick (§1.9)
prove that the finite-mixture alternative loses its consistency under *arbitrarily slight*
misspecification. Our likelihood contains a LogNormal duration, an estimated LLM confusion matrix and a
disclosure propensity: it is misspecified with certainty. So a sentence of the form "the posterior says
this permit has 14 ± 2 steps" is not defensible from a mixture model, and the number will drift upward as
the corpus grows.

The reframing that *is* defensible: **step count is a population size under a source-specific detection
model.** Our own measurement is the giveaway — documents disclose 100% of applicant-facing steps and 43%
of staff-only ones. That is a detection probability indexed by document kind and visibility class, which
is exactly the structure of site-occupancy modelling (§8.10) and of multiple-systems estimation
(§8.7–§8.9). The 43% stops being the thing that contaminates the estimate and becomes the parameter that
identifies it. Concretely: latent z_s ∈ {0,1} for "step s exists" ↔ site occupancy; reading document d ↔ a
visit; π(reveal | kind k, visibility v) ↔ covariate-dependent detection; and the number of never-disclosed
steps is estimated by data augmentation (§8.11) rather than by a nonparametric lower bound.

The cost of this move is stated honestly in §8.5: Link (2003) shows that with *unobserved* detection
heterogeneity, population size is effectively unidentified — different reasonable models predict
near-identical observations and substantially different totals, and more data does not help. Our escape
is that our heterogeneity is partly **observed** (we know the document kind; we measured π by visibility
class), which is precisely the model restriction Holzmann, Munk & Zucchini (§8.6) show restores
identifiability. That is the whole identification argument of the project, and it should be written down
as one.

### 0.3 Finding two: the wrong-signed selection tilt is not a bug

We measured the community-vs-official log-ratio at **−0.47** (applicants report *faster* than agencies
publish), noted that complaint selection predicts the opposite, and applied no correction. The
self-report-versus-administrative literature says our result is not anomalous but **modal**: validated
against employer records, retrospective reports of spell length are systematically *shorter* than
administrative measures (§10.11), and the regularity holds across many validation studies (§10.12). Three
named mechanisms all push our way: reference-period anchoring and compression (§10.13), forward
telescoping (§10.14), and salience-dependent recall (§10.15).

Two further points make the case decisive. First, the MNAR tilt parameter is **not identified** from
observed data (§10.9) — it is a sensitivity parameter by construction, so any procedure that appears to
estimate it is recovering a bridge assumption, which is very likely what produced −0.47. Second, our
pooled ratio is computed only on step keys carrying *both* community and official evidence, i.e. the
high-visibility steps, so it is estimated on the least representative slice available. The fix is not a
correction factor: it is to declare applicant-experienced and agency-published durations as **different
estimands** (§10.17) and give each source its own measurement map (§10.16).

Also worth recording: Patil & Rao (§10.3) give the closed form that turns this into a *test*. Length-biasing
a LogNormal(μ, σ²) shifts μ by exactly σ² and leaves σ unchanged. We measured a shift of the wrong sign, so
length bias is rejected on sign, not on judgement. Run it and report it.

### 0.4 What the code does now, and where each borrow lands

For concreteness, since most "borrow" notes below point at these two files:

- `pipeline/procbench/incremental.py` — `decide_offline()` is greedy nearest-neighbour assignment with a
  fixed similarity threshold of 0.42; `decide_llm()` is a single LLM verdict; `merge_into()` resolves field
  conflicts by "better tier wins". That is hard assignment plus a hand-set reliability order: exactly the
  two things Bayesian entity resolution (§2) and truth discovery (§3) replace.
- `pipeline/priors/latent_timing.py` — empirical-Bayes LogNormal with a 3-year recency half-life.
  `pipeline/priors/drift_model.py` — a continuous-time local-level Kalman filter with variance shocks at
  known changepoints, which is already the right shape (§9.2) and needs a pooled posterior over its
  variances rather than fixed constants.

---

## 1. Bayesian nonparametric structure learning

The formal version of "is this a new step or one I already hold" — and the literature on why the obvious
answer is wrong.

### 1.1 The canon, grouped

- Ferguson, T. S. "A Bayesian Analysis of Some Nonparametric Problems." *Annals of Statistics* 1(2), 1973, 209–230. DOI [10.1214/aos/1176342360](https://doi.org/10.1214/aos/1176342360)
- Antoniak, C. E. "Mixtures of Dirichlet Processes with Applications to Bayesian Nonparametric Problems." *Annals of Statistics* 2(6), 1974, 1152–1174. DOI [10.1214/aos/1176342871](https://doi.org/10.1214/aos/1176342871)
- Sethuraman, J. "A Constructive Definition of Dirichlet Priors." *Statistica Sinica* 4, 1994, 639–650.
- Aldous, D. J. "Exchangeability and related topics." *École d'Été de Probabilités de Saint-Flour XIII*, LNM 1117, 1985, 1–198. DOI [10.1007/BFb0099421](https://doi.org/10.1007/BFb0099421)
- Pitman, J. & Yor, M. "The two-parameter Poisson-Dirichlet distribution derived from a stable subordinator." *Annals of Probability* 25(2), 1997, 855–900. DOI [10.1214/aop/1024404422](https://doi.org/10.1214/aop/1024404422)

Ferguson defines the DP; Antoniak works out the mixture posterior and is the origin of the "number of
distinct values" distribution people still use as a prior on *K*; Sethuraman's stick-breaking is what makes
truncated HMC implementations possible; Aldous §11 is the origin of the restaurant metaphor and the
exchangeable partition probability function (EPPF) view; Pitman–Yor adds a discount giving power-law
cluster growth.

**Borrow:** the EPPF is the right abstraction level for us, because it is where a *non-CRP* prior on
partitions of document-mentions plugs in. Stick-breaking is the representation to write the model in if we
go the NumPyro route.

**Breaks:** cited for notation. None of them models selective observation. Pitman–Yor is an active trap:
it looks attractive ("power law, many small clusters") and is one of the two families proven inconsistent
for component count (§1.7) while still failing microclustering (§1.10).

### 1.2 Neal, R. M. "Markov Chain Sampling Methods for Dirichlet Process Mixture Models." *JCGS* 9(2), 2000, 249–265. DOI [10.1080/10618600.2000.10474879](https://doi.org/10.1080/10618600.2000.10474879)

The reference catalogue of DP-mixture Gibbs samplers, including non-conjugate cases; Algorithm 8 introduces
auxiliary "empty table" components so a new cluster can be proposed when the component marginal has no
closed form.

**Borrow:** Algorithm 8 is the principled replacement for the thresholded verdict in `decide_offline()`, at
the level of one move. Instead of "new: yes/no", evaluate the full conditional for mention *i* joining each
existing step versus *m* fresh steps, where the fresh-step likelihood integrates over the actor, LogNormal
duration and fee priors. The decision becomes a probability that can be resampled later.

**Breaks:** single-site, so it mixes badly when a *group* of documents should collectively have been split
off — which is our case (a fee study and a consultant report may jointly describe a staff-only step no
applicant page mentions). Our parameter block has no tractable marginal, so we are in Algorithm 8's slow
regime from the start.

### 1.3 Jain, S. & Neal, R. M. "A Split-Merge MCMC Procedure for the Dirichlet Process Mixture Model." *JCGS* 13(1), 2004, 158–182. DOI [10.1198/1061860043001](https://doi.org/10.1198/1061860043001) — non-conjugate companion: *Bayesian Analysis* 2(3), 2007. DOI [10.1214/07-BA219](https://doi.org/10.1214/07-BA219)

Metropolis–Hastings moves that split one cluster into two or merge two into one, using restricted Gibbs
sweeps to build the proposal; the 2007 paper handles the non-conjugate case.

**Borrow:** the most directly actionable item in this area. Our loop is **irreversible**: an early document
that conflated "plan check" and "structural plan check" can never be undone. Split-merge is the repair.
Concretely — propose merges between steps whose actor posteriors overlap and whose duration posteriors are
consistent; propose splits when a step's log-duration posterior is bimodal, which is what a conflation
looks like under a LogNormal likelihood.

**Breaks:** acceptance rates collapse when clusters are small, which is our regime — a 3-mention step gives
the restricted Gibbs sweep almost nothing. Expect to need informed proposals driven by the LLM similarity
scores. Neither paper touches the partial order: splitting a step must split its precedence edges, and that
proposal density is ours to derive.

### 1.4 Blei, D. M. & Jordan, M. I. "Variational inference for Dirichlet process mixtures." *Bayesian Analysis* 1(1), 2006, 121–143. DOI [10.1214/06-BA104](https://doi.org/10.1214/06-BA104)

Mean-field variational inference for DP mixtures with a truncated stick-breaking family.

**Borrow:** the truncation diagnostic (raise the truncation, check the mass on the last stick stops moving)
is a cheap sanity check regardless of method, and it is a fast initialiser.

**Breaks:** mean-field over assignments factorises away exactly the correlations that constitute "is this a
new step". It cannot represent "these two mentions are either both step 7 or both a new step 12, never one
each" — and that bimodality *is* the posterior we want to report. Do not use it as the reporting engine.

### 1.5 Teh, Y. W., Jordan, M. I., Beal, M. J. & Blei, D. M. "Hierarchical Dirichlet Processes." *JASA* 101(476), 2006, 1566–1581. DOI [10.1198/016214506000000302](https://doi.org/10.1198/016214506000000302)

Multiple grouped datasets share one unbounded set of mixture components, with group-specific mixing weights
drawn from a shared DP-distributed base measure; the Chinese Restaurant Franchise gives the sampler.

**Borrow:** structurally the right shape for document-kind heterogeneity — one global step set, per-kind
mixing weights. The franchise representation makes "new step" and "step new *to this document kind*"
distinct events, a distinction our single threshold cannot express at all.

**Breaks:** the HDP *reweights*; it does not *censor*. It has no notion of a step existing but being
deliberately undisclosed. If per-kind HDP weights absorb our 43%, the step set and the disclosure
propensity become entangled and the reported step count becomes an artifact of corpus composition. We want
an explicit π with its own likelihood term layered on a shared step set.

### 1.6 Griffiths, T. L. & Ghahramani, Z. "The Indian Buffet Process: An Introduction and Review." *JMLR* 12(32), 2011, 1185–1224. <https://www.jmlr.org/papers/v12/griffiths11a.html> — with Thibaux, R. & Jordan, M. I. "Hierarchical Beta Processes and the Indian Buffet Process." *AISTATS 2007*, PMLR 2, 564–571. <http://proceedings.mlr.press/v2/thibaux07a.html>

The IBP is a prior over binary matrices with infinitely many columns, so each object possesses an unbounded
number of latent features; Thibaux & Jordan identify the beta process as the underlying de Finetti mixing
measure, supplying conjugacy.

**Borrow:** underrated for us, and arguably the honest generative shape for the **disclosure matrix**. Our
data are not "each document is generated by one step" — each document reveals a *subset* of steps and,
within each, a subset of fields. That is a binary (documents × steps) matrix, possibly three-way with
fields. The beta-process view gives each step a conjugate "popularity" parameter that reads directly as
*how disclosable this step is*, with visibility class as a hierarchical prior on it. Use the hierarchical
version, one level per document kind.

**Breaks:** exchangeable over documents, no partial order, no durations, no fees — allocation and nothing
else. Crucially it also cannot distinguish "step absent" from "step present but undisclosed", which is our
central identification problem; that tie is broken only by case traces or by an informative prior on π.
Tooling is thinner than for CRP inference; expect to write the sampler.

### 1.7 Miller, J. W. & Harrison, M. T. "Inconsistency of Pitman-Yor Process Mixtures for the Number of Components." *JMLR* 15, 2014, 3333–3370. arXiv:[1309.0024](https://arxiv.org/abs/1309.0024) — companion: "A simple example of Dirichlet process mixture inconsistency for the number of components." *NIPS 26*, 2013. arXiv:[1301.2708](https://arxiv.org/abs/1301.2708)

Proves that for data from a finite mixture, the DPM/PYM posterior on the number of components represented
in the data does **not** concentrate on the truth — it keeps mass on too many components, for essentially
all discrete families and for well-behaved continuous exponential families. The companion gives the minimal
example: one standard normal, and P(one cluster) → 0.

**Borrow:** the warning, and it is load-bearing exactly as the brief guessed. Use it to justify *in writing*
why we are not using a DP prior for the step count; reviewers in this area will ask.

**Breaks:** nothing — it is a theorem. Two scope notes: it concerns the number of *components*, and DPM
clustering can still be consistent in other senses (§1.11); and it assumes a true finite mixture, whereas
our truth is a workflow. The practical implication survives the mismatch, because the spurious mass comes
from the CRP's rich-get-richer tail, which every near-duplicate FAQ page will feed.

### 1.8 Miller, J. W. & Harrison, M. T. "Mixture Models With a Prior on the Number of Components." *JASA* 113(521), 2018, 340–356. DOI [10.1080/01621459.2016.1255636](https://doi.org/10.1080/01621459.2016.1255636). arXiv:[1502.06241](https://arxiv.org/abs/1502.06241) *(Crossref records online year 2017; print issue 2018.)*

The mixture of finite mixtures: put a prior on *K*, then Dirichlet weights. Shows MFMs inherit nearly all
the DP's convenient machinery — an EPPF, a restaurant process, a random-measure representation — so DP
samplers including Jain–Neal split-merge transfer with changed coefficients.

**Borrow:** the default replacement for the CRP. Two gains: the *K* posterior is consistent under a correct
likelihood, so there is a defensible "how many steps" story; and p(K) takes real domain information — a
mid-size city's permitting workflow has a plausible range, which the CRP can only express through a
concentration parameter with no interpretable units.

**Breaks:** the consistency is conditional on a correct component likelihood, and ours is not (§1.9). Still
an exchangeable partition model, so still no microclustering. And the "open a new step" probability is no
longer a simple α/(n+α) — the coefficients depend on the current number of occupied clusters.

### 1.9 Cai, D., Campbell, T. & Broderick, T. "Finite mixture models do not reliably learn the number of components." *ICML 2021*, PMLR 139. arXiv:[2007.04470](https://arxiv.org/abs/2007.04470)

Proves that under **arbitrarily slight** misspecification the FMM component-count posterior diverges: the
posterior probability of any fixed finite number of components goes to zero as data accumulate. Notably,
posterior-density consistency is *not* sufficient to avoid this. Supplies checkable sufficient conditions.

**Borrow:** this should set our reporting policy, and it is more damaging than §1.7. That paper says "don't
use DP for *K*"; this one says MFM does not save you unless the likelihood is exactly right. Consequence:
**do not publish a point estimate of the number of steps as if it were a consistent estimator.** Report it
as a posterior under a stated model, report its sensitivity to corpus size, and prefer functionals that are
robust — which is the argument for §0.2.

**Breaks:** asymptotic in *n*; with 200 documents we are not near the asymptote, so it is a warning about
drift and overclaiming rather than proof that the finite-sample answer is garbage.

### 1.10 Zanella, G., Betancourt, B., Wallach, H., Miller, J., Zaidi, A. & Steorts, R. C. "Flexible Models for Microclustering with Application to Entity Resolution." *NIPS 2016*. arXiv:[1610.09780](https://arxiv.org/abs/1610.09780) — workshop precursor: Miller, Betancourt, Zaidi, Wallach & Steorts, arXiv:[1512.00792](https://arxiv.org/abs/1512.00792), 2015

Defines the microclustering property — cluster sizes grow sublinearly in *n* — observes that CRP, PY and
MFM all violate it, and constructs Kolchin-partition / "exchangeable sequences of clusters" models that
satisfy it by putting a prior directly on cluster sizes and on the number of clusters.

**Borrow:** **take the prior.** Our steps are microclusters by construction: a step is mentioned by 2–10
documents whether the corpus has 50 documents or 5,000, while the *number* of steps grows as jurisdictions
are added. Specifying the cluster-size distribution directly is also where real knowledge goes — the
applicant-facing size distribution should sit well to the right of the staff-only one, which is our
100%/43% finding expressed as a prior instead of bolted on afterwards.

**Breaks:** inference is harder and the reference samplers were built for categorical record-linkage
fields, not our mixed continuous/categorical/ordering block. No selective disclosure, no partial order.
Cite the 2016 NIPS paper for the models; the 2015 note is thin.

### 1.11 Ascolani, F., Lijoi, A., Rebaudo, G. & Zanella, G. "Clustering consistency with Dirichlet process mixtures." *Biometrika* 110(2), 2023, 551–558. DOI [10.1093/biomet/asac051](https://doi.org/10.1093/biomet/asac051)

A partial rehabilitation: if the DP concentration parameter is given a prior with suitable behaviour near
zero, the DPM posterior on the number of clusters *can* be consistent — §1.7's inconsistency is not
unavoidable within the DP family but depends on how α is treated.

**Borrow:** a one-line experiment worth running before rewriting the prior: put a prior on α with the right
tail behaviour rather than fixing it or using a vague Gamma.

**Breaks:** the conditions are technical and derived for well-specified mixtures. Combined with §1.9,
fixing the α prior does not protect against misspecification, which is our actual regime, and it does
nothing about microclustering. A caveat to §1.7, not a solution.

### 1.12 Alamichel, L., Bystrova, D., Arbel, J. & Kon Kam King, G. "Bayesian mixture models (in)consistency for the number of clusters." *Scandinavian Journal of Statistics* 51(4), 2024, 1619–1660. DOI [10.1111/sjos.12739](https://doi.org/10.1111/sjos.12739). arXiv:[2210.14201](https://arxiv.org/abs/2210.14201)

Extends the inconsistency results beyond DP/PY to further Gibbs-type and normalised-random-measure priors,
and proposes post-processing remedies for recovering a usable cluster count from an inconsistent posterior.

**Borrow:** the cleanest single citation for the whole (in)consistency landscape, plus the post-processing
recipes (broadly: merge negligibly-occupied clusters before counting) if pipeline constraints leave us with
a DP-shaped prior.

**Breaks:** the remedies are after-the-fact corrections with thresholds of their own — replacing one
threshold with another, which is a poor trade when the stated goal is to eliminate a thresholded decision.
Use it as a robustness check, not a design.

### 1.13 Streaming and sequential BNP inference

- Fearnhead, P. "Particle filters for mixture models with an unknown number of components." *Statistics and Computing* 14(1), 2004, 11–21. DOI [10.1023/B:STCO.0000009418.04621.cd](https://doi.org/10.1023/B:STCO.0000009418.04621.cd)
- Wang, L. & Dunson, D. B. "Fast Bayesian Inference in Dirichlet Process Mixture Models." *JCGS* 20(1), 2011, 196–216. DOI [10.1198/jcgs.2010.07081](https://doi.org/10.1198/jcgs.2010.07081)
- Broderick, T., Boyd, N., Wibisono, A., Wilson, A. C. & Jordan, M. I. "Streaming Variational Bayes." *NIPS 2013*. arXiv:[1307.6769](https://arxiv.org/abs/1307.6769)
- Campbell, T., Straub, J., Fisher III, J. W. & How, J. P. "Streaming, Distributed Variational Inference for Bayesian Nonparametrics." *NIPS 2015*. arXiv:[1510.09161](https://arxiv.org/abs/1510.09161)

Fearnhead gives an exact-then-resampled particle filter for mixtures with unknown *K*. Wang & Dunson's SUGS
assigns each observation greedily in one pass, then averages over orderings to blunt the greediness.
Broderick et al. give streaming/asynchronous posterior updates from batch primitives; Campbell et al. extend
this to BNP models and confront the fact that BNP components have **no inherent ordering**, so each
minibatch update requires solving a combinatorial correspondence between local and central components.

**Borrow:** Campbell et al. is the one to read closely, because its central technical problem *is* ours in
another vocabulary: before merging new evidence into the global model, decide which local components
correspond to which global components — solved as explicit combinatorial optimisation with uncertainty,
not a greedy per-item threshold. Fearnhead gives the resampling discipline that lets us carry **multiple
competing step-partitions** forward as the corpus streams; our current design carries exactly one
hypothesis. SUGS is the right cheap baseline, and its ordering-averaging trick mitigates our scrape-order
dependence.

**Breaks:** particle filters degenerate when the state is a high-dimensional partition plus our parameter
block; expect collapse without a rejuvenation move (bolt on §1.3). SUGS is greedy, which is what we are
escaping. Both streaming-VB papers share §1.4's defect. And all four assume the stream is i.i.d. from one
fixed process — whereas our sources conflict *because the rule changed*, and an update that silently
absorbs a 2019 fee schedule into a 2024 step is the exact failure we need to avoid.

### 1.14 Kulis, B. & Jordan, M. I. "Revisiting k-means: New Algorithms via Bayesian Nonparametrics." *ICML 2012*. arXiv:[1111.0352](https://arxiv.org/abs/1111.0352) — with Miller, J. W. & Dunson, D. B. "Robust Bayesian Inference via Coarsening." *JASA* 114(527), 2019, 1113–1125. DOI [10.1080/01621459.2018.1469995](https://doi.org/10.1080/01621459.2018.1469995). arXiv:[1506.06101](https://arxiv.org/abs/1506.06101)

Kulis & Jordan take the small-variance limit of the DP-mixture Gibbs sampler and obtain DP-means: hard
k-means with a threshold λ above which a new cluster opens. Miller & Dunson's coarsening conditions on a
neighbourhood of the empirical distribution instead of the exact data — implementable as a fractional power
on the likelihood — making cluster-count inference far less misspecification-sensitive.

**Borrow:** Kulis & Jordan is worth reading for one reason: it shows **our current thresholded LLM verdict
is the small-variance limit of the Bayesian model we want**, with λ playing the role of our 0.42. That is a
precise characterisation of what we are giving up and a clean way to frame the contribution — we are
relaxing a hard λ back to the posterior it came from. Miller & Dunson is the direct remedy to §1.9: if we
must report a count under a likelihood we know is wrong, a tempered-likelihood c-posterior gives a
materially more stable count for a one-line change.

**Breaks:** DP-means is not Bayesian output and λ must be tuned, so adopting it is a lateral move from where
we already are. Coarsening's exponent ζ is itself a tuning parameter, and tempering widens *all*
inferences, fee and duration posteriors included. Use it as a robustness column, not the headline.

### 1.15 Summarising a posterior over partitions

- Wade, S. & Ghahramani, Z. "Bayesian cluster analysis: Point estimation and credible balls." *Bayesian Analysis* 13(2), 2018. DOI [10.1214/17-BA1073](https://doi.org/10.1214/17-BA1073). arXiv:[1505.03339](https://arxiv.org/abs/1505.03339)
- Dahl, D. B., Johnson, D. J. & Müller, P. "Search Algorithms and Loss Functions for Bayesian Clustering." *JCGS* 31(4), 2022, 1189–1201. DOI [10.1080/10618600.2022.2069779](https://doi.org/10.1080/10618600.2022.2069779). arXiv:[2105.04451](https://arxiv.org/abs/2105.04451)

Wade & Ghahramani develop decision-theoretic point estimates for a partition (minimising posterior expected
Variation of Information) and **credible balls** in partition space. Dahl et al.'s SALSO finds those
minimisers efficiently and supports Binder loss with unequal misclassification penalties.

**Borrow:** this is the reporting layer, needed the moment we have a posterior over partitions instead of one
answer. The credible ball is the right object for a policy audience: "here is the modal workflow, and here
is the set of workflows the evidence cannot distinguish from it." Dahl et al.'s **asymmetric penalties** are
the sleeper feature — splitting one real step in two and merging two real steps into one have very
different costs when the output is a complexity metric, and Binder loss lets us say so explicitly.

**Breaks:** both are agnostic to what generated the partition, so a credible ball from an inconsistent *K*
posterior is a precise summary of an untrustworthy object. Both treat mentions as exchangeable, whereas a
statute is stronger evidence than a FAQ, so the loss needs weighting. And neither handles the order: two
partitions can be VI-identical and imply different workflows, so we need a loss on (partition, order)
jointly — which I found nowhere.

---

## 2. Bayesian entity resolution and record linkage

The brief's guess was right: this is the closest existing machinery for the new-vs-existing-step decision.

### 2.1 Fellegi, I. P. & Sunter, A. B. "A Theory for Record Linkage." *JASA* 64(328), 1969, 1183–1210. DOI [10.1080/01621459.1969.10501049](https://doi.org/10.1080/01621459.1969.10501049)

For each candidate record pair, form a comparison vector, model its distribution under match
(*m*-probabilities) and non-match (*u*-probabilities), and use the likelihood ratio with two thresholds to
declare match / non-match / clerical review.

**Borrow:** two things. The *m*/*u* decomposition is the right skeleton for our extractor error model — our
per-kind sensitivity and false-positive rates *are* m- and u-probabilities on "does this mention refer to
step s", and FS shows they are estimable from the mixture without labels. And the **clerical-review
region** — the third decision — is what our binary threshold is missing: some step-identity questions
should be routed to a human, and FS gives the principled way to size that set.

**Breaks:** pairwise and therefore **non-transitive** — it can declare A~B, B~C, A≁C, which is incoherent
when the object is a partition. It also assumes conditional independence of comparison fields given match
status, which fails badly for us: if a document discloses a step's actor it very likely discloses its fee
too, because both flow through the same disclosure mechanism. Cited as the ancestor; do not implement.

### 2.2 Sadinle, M. "Detecting duplicates in a homicide registry using a Bayesian partitioning approach." *Annals of Applied Statistics* 8(4), 2014, 2404–2434. arXiv:[1407.8219](https://arxiv.org/abs/1407.8219)

Reframes duplicate detection from pairwise decisions to inferring a **partition of the file** as the
parameter of interest, which makes decisions transitive by construction, with per-field reliability priors
and no training data. Applied to the UN Truth Commission for El Salvador.

**Borrow:** the cleanest short statement of the move we are trying to make. Its argument — pairwise verdicts
produce non-transitive garbage that then gets reconciled ad hoc, so make the partition the parameter — is
verbatim the case against `decide_offline()`. Per-field reliability priors are the direct analogue of
per-kind disclosure propensities, and the no-training-data setting matches ours.

**Breaks:** single-file dedup on categorical name/date/place fields; no continuous parameters, and no notion
that a field can be *systematically suppressed* rather than merely unreliable. Unreliability and censoring
are different likelihoods, and our 43% is censoring. Records are exchangeable, so no version changepoints.

### 2.3 Sadinle, M. "Bayesian Estimation of Bipartite Matchings for Record Linkage." *JASA* 112(518), 2017, 600–612. DOI [10.1080/01621459.2016.1148612](https://doi.org/10.1080/01621459.2016.1148612). arXiv:[1601.06630](https://arxiv.org/abs/1601.06630)

Targets the bipartite matching between two files as the parameter and derives Bayes point estimators under
different losses — including **partial** estimates that deliberately leave ambiguous parts unresolved.

**Borrow:** the partial Bayes estimate. Rather than forcing every mention into a step, return "these three
mentions are one step, and this fourth is undetermined" — the right output when a fee study mentions an
activity that may or may not be the plan-check step we hold. It makes abstention a decision-theoretic
object instead of a pipeline hack.

**Breaks:** the one-to-one bipartite constraint is wrong for us and must not be imported — many mentions
map to one step, one document mentions many steps, and the number of latent targets is unknown. Strictly
two files. Cited for the loss function only.

### 2.4 Steorts, R. C., Hall, R. & Fienberg, S. E. "A Bayesian Approach to Graphical Record Linkage and Deduplication." *JASA* 111(516), 2016, 1660–1672. DOI [10.1080/01621459.2015.1105807](https://doi.org/10.1080/01621459.2015.1105807). arXiv:[1312.4645](https://arxiv.org/abs/1312.4645)

Links across files and deduplicates within them by positing **latent true entities**; records connect only
indirectly, through the entity they are distortions of. Linear-time hybrid MCMC, with uncertainty
propagable downstream.

**Borrow:** the latent-entity architecture is our architecture — latent steps, documents emitting partial
distorted observations. Routing everything through the latent layer makes comparisons linear in records
rather than quadratic in pairs, which matters as the corpus grows. Their explicit distortion model is the
slot where π(reveal field F | kind k, visibility v) belongs, and they demonstrate propagating linkage
uncertainty into downstream estimates, which is what a defensible complexity metric requires.

**Breaks:** entities have a fixed shared schema of categorical fields; ours have heterogeneous, partly
continuous parameters and a relational structure (the order) with no counterpart here. The distortion model
treats missing and distorted as interchangeable noise, whereas we need censoring that depends on visibility
class. The linkage prior in this version is not microclustering-aware (that is §2.6).

### 2.5 Steorts, R. C. "Entity Resolution with Empirically Motivated Priors." *Bayesian Analysis* 10(4), 2015. DOI [10.1214/15-BA965SI](https://doi.org/10.1214/15-BA965SI). arXiv:[1409.0643](https://arxiv.org/abs/1409.0643)

Uses the **empirical distribution of the observed data** as the prior for latent entities' field values, with
a mechanism for how observed strings deviate from the entity's true string.

**Borrow:** directly applicable and cheap. Our "known-ish universe" of actors is exactly this: a published
department directory is an empirical prior on every step's actor field, and the string-distortion mechanism
handles "Dept. of Building & Safety" / "LADBS" / "Building and Safety". Probably the fastest real
improvement available to the current model.

**Breaks:** an empirical prior built from the *corpus* is selection-biased in our setting — with staff-only
steps disclosed at 43%, a corpus-derived prior skews toward applicant-facing actors, feeding our central
bias into our prior. Use the **directory** (an external, near-complete frame) as the empirical prior, never
the corpus. No microclustering, categorical/string fields only.

### 2.6 Aleshin-Guendel, S. & Sadinle, M. "Multifile Partitioning for Record Linkage and Duplicate Detection." *JASA* 118(543), 2023, 1786–1795. DOI [10.1080/01621459.2021.2013242](https://doi.org/10.1080/01621459.2021.2013242). arXiv:[2110.03839](https://arxiv.org/abs/2110.03839)

General multi-file linkage plus within-file duplication, with a novel partition representation and a
**structured prior that encodes knowledge about the data-collection processes** of the different files, plus
losses permitting partially unresolved output. R package `multilink`.

**Borrow:** the Area-2 work whose *prior* best matches our evidence structure. "A structured prior informed
by how each file was collected" is our document-kind disclosure propensity in the record-linkage idiom: a
statute, a FAQ and a consultant fee study are three files with different generating processes, different
duplication behaviour and different field reliabilities, and this gives a partition prior that takes all of
it as input. Working code exists.

**Breaks:** "data collection process" there means structural constraints on the partition (*this file has no
duplicates*), not a per-field, per-visibility reveal probability that must itself be inferred. Our π is a
parameter with a likelihood; theirs is closer to a fixed constraint. Categorical comparison vectors, no
continuous step parameters, no order, no changepoints.

### 2.7 Betancourt, B., Sosa, J. & Rodríguez, A. "A prior for record linkage based on allelic partitions." *Computational Statistics & Data Analysis* 172, 2022, 107474. DOI [10.1016/j.csda.2022.107474](https://doi.org/10.1016/j.csda.2022.107474). arXiv:[2008.10118](https://arxiv.org/abs/2008.10118)

Builds ER partition priors from **allelic partitions** — representations counting how many clusters have
each size — yielding microclustering-satisfying priors with direct constraints on the cluster-size
distribution.

**Borrow:** the operational bridge between §1.10's theory and a working ER model. Because the prior is
specified through the cluster-size profile, our pilot finding becomes a prior rather than a correction:
applicant-facing steps concentrate on larger mention counts, staff-only on 1–3.

**Breaks:** least mature and least tooled of the Area 2 entries. The allelic representation makes
conditioning on covariates awkward, so making the size profile depend smoothly on a *latent* visibility
class — which is what we actually want, since visibility is inferred — is not something the paper does.

### 2.8 Taylor, I., Kaplan, A. & Betancourt, B. "Fast Bayesian Record Linkage for Streaming Data Contexts." *JCGS* 33(3), 2024, 833–844. DOI [10.1080/10618600.2023.2283571](https://doi.org/10.1080/10618600.2023.2283571). arXiv:[2307.07005](https://arxiv.org/abs/2307.07005)

Generalises a two-file Bayesian Fellegi–Sunter model to many files and develops **streaming updates**, so a
new file updates existing link estimates instead of refitting the joint model, at near-equivalent posterior
inference for a fraction of the compute.

**Borrow:** the most direct methodological answer to "we fit one document at a time and want to stop doing
it badly" — a Bayesian ER model built for sequential arrival whose explicit goal is to *match* the batch
posterior rather than drift from it, with the gap quantified. **Adopt its evaluation design even if we do
not adopt the model:** fit the joint model on the full corpus, fit incrementally, report the divergence.
That one experiment would tell us what our greedy loop is costing.

**Breaks:** built on an FS comparison-vector likelihood, so it inherits §2.1's conditional-independence
assumption, which our disclosure mechanism violates. Streaming updates assume new files are exchangeable
with old — no changepoints, so an amended ordinance is absorbed as noise rather than flagged as a version
boundary. And their "files" are coherent batches of person-records; our documents are heterogeneous in kind,
and the *kind* determines the error model.

### 2.9 Yang, B., Cardie, C. & Frazier, P. "A Hierarchical Distance-dependent Bayesian Model for Event Coreference Resolution." *TACL* 3, 2015, 517–528. DOI [10.1162/tacl_a_00155](https://doi.org/10.1162/tacl_a_00155). arXiv:[1504.05929](https://arxiv.org/abs/1504.05929)

Resolves whether event mentions across documents refer to the same underlying **event** using a hierarchical
distance-dependent CRP: pairwise distances come from a feature-rich learnable distance function, which is
then encoded as the ddCRP prior driving nonparametric clustering within and across documents.

**Borrow:** the architecture, and this is the closest structural analogue for the *assignment* decision
specifically. It is the only work I verified in either area where the entities resolved are **activities
described in text** rather than persons; the number of them is inferred rather than fixed; resolution is
hierarchical within and across documents; and — decisively — **a learned pairwise similarity is folded into
a prior over partitions instead of being thresholded into a verdict.** Swap their distance function for our
LLM's pairwise judgment and this is a recognisable first draft of what we described wanting. The hierarchy
(mention → within-document event → cross-document event) also maps onto mention → step-as-described-here →
step.

**Breaks:** ddCRP is non-exchangeable, so scrape order leaks into the answer — a genuine liability, since
corpus assembly order is an accident. The cluster-count posterior inherits §1.7's inconsistency. The
distance function is trained on labelled coreference data we do not have, and ECB+ is small. Most
importantly: **no selective disclosure, no per-source error model, no durations, fees or order, no
changepoints.** It gives the resolution mechanism and none of the generative content.

Companion, cited for lineage and as the unsupervised precursor: Bejan, C. A. & Harabagiu, S. "Unsupervised
Event Coreference Resolution." *Computational Linguistics* 40(2), 2014, 311–347. DOI
[10.1162/COLI_a_00174](https://doi.org/10.1162/COLI_a_00174). DP/HDP clustering of event mentions with rich
linguistic features, no labels. **Breaks:** feature engineering now obsolete, DP/HDP count pathology, and a
coreference chain is a flat cluster with no internal parameters or ordering. Read §2.9 instead.

### 2.10 Blei, D. M. & Frazier, P. I. "Distance Dependent Chinese Restaurant Processes." *JMLR* 12(74), 2011, 2461–2488. <https://www.jmlr.org/papers/v12/blei11a.html>

Generalises the CRP by letting each customer sit *with a particular other customer* with probability
proportional to a decay function of an arbitrary pairwise distance; the partition is the connected
components of the link graph. Non-exchangeable; covers sequential and spatial CRPs as special cases.

**Borrow:** the mechanism that converts our LLM from a *decision* into a *prior*. Feed the LLM's pairwise
similarity into the decay function and the model emits a posterior over partitions rather than a
thresholded verdict — keeping the signal, losing the brittle cutoff. The sequential special case matches
incremental arrival, and distances can encode more than text: actor identity, publication date (useful for
version changepoints), fee proximity.

**Breaks:** non-exchangeability means order dependence. The cluster-count posterior inherits §1.7. And the
link representation makes split-merge awkward, since one link flip can merge two large components
discontinuously.

### 2.11 Unique-entity estimation and propagation into a population size

- Chen, B., Shrivastava, A. & Steorts, R. C. "Unique Entity Estimation with Application to the Syrian Conflict." *Annals of Applied Statistics*, 2018. arXiv:[1710.02690](https://arxiv.org/abs/1710.02690)
- Sadinle, M. "Bayesian propagation of record linkage uncertainty into population size estimation of human rights violations." *Annals of Applied Statistics* 12(2), 2018. DOI [10.1214/18-AOAS1178](https://doi.org/10.1214/18-AOAS1178)

Chen et al. attack **unique entity estimation** — how many distinct entities are in a set of duplicated
noisy databases — directly with a near-linear-time LSH estimator that is unbiased with provably low
variance, rather than deriving the count from a full ER solution. Sadinle carries linkage uncertainty
coherently into a capture–recapture population size, so the final count reflects uncertainty about *which
records matched*.

**Borrow:** the **estimand**, which is the §0.2 reframing done properly. Chen et al. make the case that if
the quantity you want is "how many distinct things exist", you should target it directly where it has a
bounded variance, rather than reading it off a clustering. Sadinle then does it Bayesianly, and that
construction is what makes our 43% an asset: each document kind is a capture occasion with its own detection
probability, visibility class is a covariate on detection, and the number of steps including never-disclosed
ones is the population size, with our pilot measurement as an informative prior.

**Breaks:** Chen et al.'s estimator itself is not usable — LSH on string fields, frequentist, no posterior,
so it cannot absorb a disclosure model; and it estimates entities among records we *have*, whereas our
hardest steps appear in no document. Sadinle's capture–recapture rests on independence across occasions,
which our corpus violates badly (the FAQ is derived from the ordinance — they are not independent captures,
and this biases *N* downward), and on detection homogeneity within strata. Both are persons-in-lists with
no structured entity parameters and no ordering.

### 2.12 Linkage-error-corrected downstream analysis

- Copas, J. B. & Hilton, F. J. "Record Linkage: Statistical Models for Matching Computer Records." *JRSS Series A* 153(3), 1990, 287. DOI [10.2307/2982975](https://doi.org/10.2307/2982975)
- Lahiri, P. & Larsen, M. D. "Regression Analysis With Linked Data." *JASA* 100(469), 2005, 222–230. DOI [10.1198/016214504000001277](https://doi.org/10.1198/016214504000001277)

Copas & Hilton give early explicit models of the matching process, including the "hit-miss" model later ER
work inherits. Lahiri & Larsen show that regression on linked data is **biased** when linkage error is
ignored, and construct corrected estimators from the linkage probabilities.

**Borrow:** the warning, and it is the one most likely to bite us at publication. Our complexity metric is a
downstream functional of an inferred structure, and this is the canonical demonstration that plugging in a
point-estimated linkage and then analysing it produces confidently wrong numbers. If we report a complexity
score computed from the MAP partition, we are making exactly this error. The fix in a Bayesian setting is
better than theirs: **compute the metric inside the sampler, once per posterior draw, and report its
posterior.**

**Breaks:** frequentist bias correction for linear regression with estimable error rates — a narrow target
that does not generalise to a nonlinear functional of a partition plus a partial order. The hit-miss model
as usually cited is now known to be logically inconsistent (corrected in Marchant/Rubinstein/Steorts,
*JSSAM* 11(3), 2023, 569–596, DOI [10.1093/jssam/smac030](https://doi.org/10.1093/jssam/smac030), whose
partially-collapsed Gibbs sampler is also worth reading for mixing). Cite Copas & Hilton historically.

### 2.13 Canonicalising textual descriptions of activities

- Galárraga, L., Heitz, G., Murphy, K. & Suchanek, F. M. "Canonicalizing Open Knowledge Bases." *CIKM 2014*, 1679–1688. DOI [10.1145/2661829.2662073](https://doi.org/10.1145/2661829.2662073)
- Vashishth, S., Jain, P. & Talukdar, P. "CESI: Canonicalizing Open Knowledge Bases using Embeddings and Side Information." *WWW 2018*, 1317–1327. DOI [10.1145/3178876.3186030](https://doi.org/10.1145/3178876.3186030). arXiv:[1902.00172](https://arxiv.org/abs/1902.00172)

Both address the fact that open information extraction produces redundant, ambiguous noun-phrase and
**relation-phrase** clusters needing canonicalisation — Galárraga et al. by hierarchical agglomerative
clustering on engineered similarity, CESI by jointly learned embeddings plus side information.

**Borrow:** these address the sub-problem person-ER does not have: deciding whether "submit plans for
review", "plan check submittal" and "application intake" denote the same underlying *activity*.
Relation-phrase canonicalisation is the nearest existing analogue to canonicalising an administrative
action, and CESI's side information maps to our actor directory and fee data as disambiguating evidence.

**Breaks:** neither is Bayesian, neither produces a posterior, and both fix the number of canonical clusters
by a similarity threshold or an agglomerative stopping rule — the same class of decision we are escaping.
No error model, no source heterogeneity, no uncertainty output. Cited because they are the only work I found
directly on activity/relation canonicalisation; the methods are a step backwards from what we have.

**Orientation:** for the whole ER landscape in one paper, Binette, O. & Steorts, R. C. "(Almost) all of
entity resolution." *Science Advances* 8(12), 2022. DOI [10.1126/sciadv.abi8021](https://doi.org/10.1126/sciadv.abi8021)

---

## 3. Truth discovery from conflicting sources

**Two systematic caveats apply to almost everything here, stated once.** (C1) **Closed claim set.** Truth
discovery is formulated as object → candidate value set → a bipartite "who claimed what" matrix. A source
that asserts nothing about an object simply does not appear in that object's likelihood. There is no term
π(source s asserts about o), and therefore no way for silence to be evidence. **Only §3.8 breaks this.**
(C2) **Flat objects.** The object is an attribute–value cell whose *existence* is assumed; only its value is
contested. Nothing here has a latent *structured* object with latent element existence and continuous fields
attached.

### 3.1 Yin, X., Han, J. & Yu, P. S. TruthFinder. *KDD 2007*. DOI [10.1145/1281192.1281309](https://doi.org/10.1145/1281192.1281309); journal version *IEEE TKDE* 20(6), 2008. DOI [10.1109/TKDE.2007.190745](https://doi.org/10.1109/TKDE.2007.190745)

A fixpoint iteration where source trustworthiness is the average confidence of its facts and fact confidence
is a function of its asserters' trustworthiness, plus an "implication" term so similar values reinforce
rather than compete.

**Borrow:** the *implication function* is the one piece that maps cleanly onto us — it is how "Planning
Dept." and "Dept. of City Planning" reinforce each other instead of splitting the posterior, and how a
30-day and a 28-day claim partially corroborate. That is the seed of our directory-linking plus
LogNormal-duration likelihood.

**Breaks:** not a probabilistic model — unnormalised scores from an ad-hoc fixpoint with a damping constant,
so no posterior, no interval, nothing to feed into a generative model. Single-truth-per-object, wrong for us
whenever two departments genuinely co-own a step. C1 and C2 in full.

### 3.2 Galland, A., Abiteboul, S., Marian, A. & Senellart, P. "Corroborating information from disagreeing views." *WSDM 2010*. DOI [10.1145/1718487.1718504](https://doi.org/10.1145/1718487.1718504)

Three fixpoint algorithms (Cosine, 2-Estimates, 3-Estimates) estimating fact truth and view trust jointly;
3-Estimates adds a per-fact **hardness** parameter so a source is not punished for missing a fact everybody
misses.

**Borrow:** two things. Hardness is the ancestor of item difficulty (§4.2) and the right shape for "some steps
are genuinely obscure" — a per-step difficulty that decouples step obscurity from document unreliability.
And this is the one classical paper that *manufactures negative assertions* from schema functional
dependencies rather than treating absence as missing — a weak structural form of what we want.

**Breaks:** its negative facts come from functional dependencies (asserting X implicitly denies Y), never from
a propensity to disclose. It gives "asserted ¬Y", never "could have asserted and chose not to". Fixpoint, not
generative; C1, C2.

### 3.3 Pasternack, J. & Roth, D. — fact-finding to Latent Credibility Analysis

- "Knowing What to Believe (when you already know something)." *COLING 2010*, 877–885. <https://aclanthology.org/C10-1099/>
- "Generalized fact-finding." *WWW 2011 Companion*, 99–100. DOI [10.1145/1963192.1963243](https://doi.org/10.1145/1963192.1963243)
- "Latent credibility analysis." *WWW 2013*. DOI [10.1145/2488388.2488476](https://doi.org/10.1145/2488388.2488476)

LCA replaces heuristic fact-finding scores with actual **probabilistic generative models** of source
credibility, then argues the earlier score-based fact-finders are uninterpretable by comparison. The 2010
paper adds mechanisms for injecting prior knowledge as constraints on the truth.

**Borrow:** LCA is the rhetorical and technical move of our paper, performed once already in another domain —
take a hand-set reliability weighting, show it is an unprincipled surrogate, replace it with a latent-variable
model whose parameters are estimated. Also borrow the **prior-knowledge-as-constraints** mechanism: "a step
has exactly one owning department", "fees are non-negative", "the order is acyclic", and the directory as
support.

**Breaks:** credibility is a single scalar per source, not a confusion matrix, so it cannot express "program
pages systematically attribute permitting steps to Building when the true owner is Fire". C1 applies.

### 3.4 Zhao, B., Rubinstein, B. I. P., Gemmell, J. & Han, J. "A Bayesian Approach to Discovering Truth from Conflicting Sources for Data Integration." *PVLDB* 5(6), 2012, 550–561. arXiv:[1203.0058](https://arxiv.org/abs/1203.0058)

A proper Bayesian graphical model (the Latent Truth Model) with **two separate error types per source** —
false-positive and false-negative rates — over multi-valued attributes, Gibbs sampling, Beta priors,
unsupervised.

**Borrow:** the most directly reusable *model* in Area 3. The two-sided error decomposition is precisely our
extractor's (sensitivity, false-positive rate) per document kind; multi-valued attributes handle co-owned
steps; the Beta priors are the natural place to plant the rates we calibrate on the synthetic world; and
sampling-based inference composes with our other latents.

**Breaks:** LTM's false-negative rate **conflates two things we must keep apart** — "the source knows the fact
and doesn't say it" (disclosure) and "the source wrongly believes it false" (error). One parameter for both
means the model reads a program page's silence about a department as evidence the department is *wrong*
rather than *back-office*. That conflation is exactly the bug we are fixing, and it is instructive: the fix
is to factor LTM's false-negative rate into π(disclose | kind, visibility) × (1 − sensitivity). Flat objects,
no time.

### 3.5 Dong, X. L., Berti-Équille, L. & Srivastava, D. — source dependence, copying, and an evolving world

- "Integrating conflicting data: the role of source dependence." *PVLDB* 2(1), 2009, 550–561. DOI [10.14778/1687627.1687690](https://doi.org/10.14778/1687627.1687690)
- "Truth discovery and copying detection in a dynamic world." *PVLDB* 2(1), 2009. DOI [10.14778/1687627.1687691](https://doi.org/10.14778/1687627.1687691)
- Dong, Berti-Équille, Hu & Srivastava. "SOLOMON: Seeking the truth via copying detection." *PVLDB* 3(2), 2010, 1617–1620 (demo). DOI [10.14778/1920841.1921054](https://doi.org/10.14778/1920841.1921054)

Bayesian analysis of whether source S2 copied S1, using the insight that **sharing a false value is much
stronger evidence of copying than sharing a true one**; the dynamic-world paper extends this to values that
change over time, so agreement on a *stale* value is also evidence of copying.

**Borrow:** the most load-bearing borrow in Area 3, and the brief was right to flag it. (i) The shared-error
copying signal: when a city FAQ and a permit-expediter page both name the wrong department, that co-error
should collapse them into ~one effective observation. **Our Beta-Binomial denominator must count independent
documents, not documents.** (ii) The stale-agreement diagnostic is the right lens on version changepoints: a
document agreeing with a pre-change value is either a copy or a correctly-dated old document, and
distinguishing those is our problem in miniature.

**Breaks:** the copying inference is driven by shared *false* values, so it is bootstrapped off an estimate of
what is false — and with one or two documents per field there is not enough co-error signal to identify the
dependence. Worse, **we often know the dependence a priori and directionally**: the FAQ derives from the
ordinance, the program page paraphrases the fee study. Dong et al. spend their modelling budget inferring
what we can largely declare; the right adaptation is a *prior on the derivation DAG over document kinds*.
And their "dynamic world" is a value drifting under a decay kernel, not a **changepoint on a rule version**
with a posterior over the change date, which is what a dated contradiction demands.

### 3.6 Pochampally, R., Das Sarma, A., Dong, X. L., Meliou, A. & Srivastava, D. "Fusing Data with Correlations." *SIGMOD 2014*. DOI [10.1145/2588555.2593674](https://doi.org/10.1145/2588555.2593674). arXiv:[1503.00306](https://arxiv.org/abs/1503.00306)

Fuses sources under positive and negative correlations among them, estimating correlations from a sample of
ground truth and then doing approximate inference over correlated source sets.

**Borrow:** the cleanest formalisation of "how much independent evidence do N correlated documents carry",
which is exactly what our denominator needs — scoring a *set* of correlated sources rather than summing
per-source votes.

**Breaks:** it estimates the correlation structure from a ground-truth sample, and we have none for the real
corpus. Our only ground truth is synthetic, and correlation structure among document kinds is precisely the
thing least likely to transfer, because it is a property of the actual municipal publishing process. Borrow
the inference; get the correlations from a prior over the derivation DAG.

### 3.7 The Dong programme: coverage, Knowledge Vault, Knowledge-Based Trust

- Dong, X. L., Saha, B. & Srivastava, D. "Less is More: Selecting Sources Wisely for Integration." *PVLDB* 6(2), 2012, 37–48. DOI [10.14778/2535568.2448938](https://doi.org/10.14778/2535568.2448938)
- Dong, X. L., Gabrilovich, E., Heitz, G., Horn, W., Lao, N., Murphy, K., Strohmann, T., Sun, S. & Zhang, W. "Knowledge Vault: A Web-Scale Approach to Probabilistic Knowledge Fusion." *KDD 2014*. DOI [10.1145/2623330.2623623](https://doi.org/10.1145/2623330.2623623)
- Dong, X. L., Gabrilovich, E., Murphy, K., Dang, V., Horn, W., Lugaresi, C., Sun, S. & Zhang, W. "Knowledge-Based Trust: Estimating the Trustworthiness of Web Sources." *PVLDB* 8(9), 2015. arXiv:[1502.03519](https://arxiv.org/abs/1502.03519)

"Less is More" shows that integrating *more* sources can reduce accuracy once redundancy and cost are
counted, with an explicit source **coverage** parameter. Knowledge Vault fuses multiple *extractors* over
multiple *web sources* with per-(extractor, predicate) reliability plus a prior from an existing graph.
Knowledge-Based Trust estimates trustworthiness endogenously from the correctness of extracted facts using
"a novel multi-layer probabilistic model" that **distinguishes errors made in extraction from factual errors
in the source itself, by joint inference** — validated on synthetic data with known trustworthiness, then run
on 2.8B facts.

**Borrow:** KBT is the closest analogue to our overall research *design*, on three counts. (i) The **two-layer
extractor/source decomposition** is our problem exactly: the LLM's per-kind sensitivity and FPR are one layer,
the document's own reliability the other, jointly identified rather than assumed. (ii) They **validate on
synthetic data with known truth and then move to the real corpus** — our methodology. (iii) They
hierarchically **pool by bucket** (source × predicate), which is the mechanism that makes "document kind as
annotator" estimable when any single document asserts a field once. From Knowledge Vault, the (extractor,
source, predicate) indexing is the template for our (LLM, kind, field) indexing, and the prior-from-graph
move is the template for the directory prior. From "Less is More", the marginal-value framing is directly
useful for deciding which document kind to fetch next.

**Breaks:** trust is a scalar accuracy, not a confusion matrix — no "which wrong department does this kind
tend to name". Knowledge Vault's calibration is supervised, leaning on Freebase as effective ground truth;
we have no Freebase for municipal workflows. KBT's synthetic-to-real transfer validates the *estimator*, not
the *parameters* — they do not carry synthetic error rates over as priors, which is the step we need and
nobody here licenses (see §4.17). "Less is More" uses coverage for *source selection*, not inside the truth
likelihood, and it is a scalar not conditioned on a latent property of the object. And C1 in a painful form:
a page that covers permits and doesn't mention a Fire sign-off is treated as out of scope, never as evidence.

### 3.8 Zhi, S., Zhao, B., Tong, W., Gao, J., Yu, D., Ji, H. & Han, J. "Modeling Truth Existence in Truth Discovery." *KDD 2015*, 1543–1552. DOI [10.1145/2783258.2783339](https://doi.org/10.1145/2783258.2783339)

**The most important entry in Area 3 for us, and the only work anywhere that puts silence in the model.**
Handles "no-truth questions" — objects whose true answer is absent from every source's candidate set — and to
do so decomposes source quality into three fine-grained measures: **silent rate, false spoken rate, and
spoken rate**. A probabilistic graphical model infers truth and all three rates jointly, with no ground
truth, initialised by a "truth existence score" built from participation rate and consistency rate.

**Borrow:** the only prior art for π(reveal) × confusion in one unsupervised latent-variable model. Take (i)
the three-way factorisation of source behaviour into speak / stay-silent / speak-falsely, which maps onto our
disclosure propensity × sensitivity × FPR; (ii) the "truth existence score" as the shape of our "does step
*s* exist?" question, since their no-truth case *is* our no-step case; and (iii) the initialisation strategy
— they found the joint model needs a decent initialisation from cheap aggregate statistics, a warning worth
heeding for our sampler, and one that §4.7 independently repeats.

**Breaks:** the silent rate is a **single unconditioned scalar per source**. It cannot express π(reveal field F
of step s | kind k, visibility v(s)) — no dependence on the field, on the object, or on a latent visibility
class, and no pooling across sources of a kind. So it gives us the *parameter* and not the *structure*: their
model says "this source is often quiet"; ours must say "this kind of document is systematically quiet about
back-office steps and loud about applicant-facing ones, **and that asymmetry is how we infer which steps are
back-office**." Flat objects, no time, no changepoints.

### 3.9 Heterogeneous types and the long tail

- Li, Q., Li, Y., Gao, J., Zhao, B., Fan, W. & Han, J. "Resolving Conflicts in Heterogeneous Data by Truth Discovery and Source Reliability Estimation." *SIGMOD 2014*. DOI [10.1145/2588555.2610509](https://doi.org/10.1145/2588555.2610509) (CRH)
- Li, Q., Li, Y., Gao, J., Su, L., Zhao, B., Demirbas, M., Fan, W. & Han, J. "A Confidence-Aware Approach for Truth Discovery on Long-Tail Data." *PVLDB* 8(4), 2014, 425–436. DOI [10.14778/2735496.2735505](https://doi.org/10.14778/2735496.2735505) (CATD)

CRH resolves conflicts jointly over categorical and continuous data in one objective, with per-type loss
functions and a shared source weight. CATD observes that source-claim distributions are long-tailed — most
sources make very few claims — so small-source reliability estimates are meaningless, and fixes this with a
chi-square **confidence interval** on each source's weight.

**Borrow:** CRH's per-type loss with a shared source weight is the right factorisation for our mixed fields
(categorical agency, continuous duration and fee, binary existence) and is the honest baseline our Bayesian
model has to beat. CATD is the field's own recognition of our central statistical problem, and the move of
**propagating uncertainty in the reliability estimate into the truth estimate** rather than plugging in a
point estimate is essential — and free in a Bayesian treatment.

**Breaks:** CRH's source weight is a Lagrange-multiplier-flavoured scalar with no probabilistic reading, so
you cannot put a prior on it or make it depend on kind and visibility; replacing "better tier wins" with one
scalar per source is a lateral move for us. CATD **discounts** small sources rather than **pooling** them,
which is backwards: a program page making three claims should borrow strength from every other program page,
because the parameter we care about is a property of the *kind*. CATD has no notion of source type, so it
would down-weight our sparse kinds into irrelevance. The fix is hierarchical pooling (§4.10, §4.13).

### 3.10 Li, Y., Li, Q., Gao, J., Su, L., Zhao, B., Fan, W. & Han, J. "On the Discovery of Evolving Truth." *KDD 2015*. DOI [10.1145/2783258.2783277](https://doi.org/10.1145/2783258.2783277)

Truth discovery where the truth itself changes over time, with sources reporting at different times and lags;
models temporal smoothness of the truth and estimates reliability across the timeline.

**Borrow:** the closest classical prior art to our version changepoints, and its lesson is the one our tier
ladder currently gets wrong: a dated contradiction is **not** necessarily a reliability signal — it may be a
timing signal — so reliability estimation must condition on the document's date or it will systematically
punish correct-but-old documents.

**Breaks:** the truth evolves under a *smoothness* prior — it drifts. Regulatory rules do not drift; they
change discretely on an effective date and then stay put. We need a changepoint model with piecewise-constant
field values and a posterior over effective dates, and a smoothness prior will actively smear our
changepoints. Also, their documents are timestamped reports; our publication dates are often absent, wrong,
or a last-touched CMS field rather than the substantive revision — so **our time covariate is itself latent**,
which they do not model.

### 3.11 Wang, D., Kaplan, L., Le, H. & Abdelzaher, T. "On truth discovery in social sensing: A maximum likelihood estimation approach." *IPSN 2012*. DOI [10.1109/IPSN.2012.6920960](https://doi.org/10.1109/IPSN.2012.6920960) — with Wang, D., Abdelzaher, T., Kaplan, L. & Aggarwal, C. C. "Recursive Fact-Finding: A Streaming Approach to Truth Estimation in Crowdsourcing Applications." *ICDCS 2013*. DOI [10.1109/ICDCS.2013.54](https://doi.org/10.1109/ICDCS.2013.54)

The first casts binary social-sensing claims as EM with per-source reliability and derives **Cramér-Rao
confidence bounds** on the resulting estimates. The second makes it recursive/streaming, updating reliability
and truth incrementally as claims arrive. *(Correction to the brief: Aggarwal is on the 2013 streaming paper,
not the 2012 IPSN paper.)*

**Borrow:** the streaming formulation is the right shape for sequential evidence — a filtering recursion over
the posterior, not a batch refit per document. And the Cramér-Rao bound is a cheap rigorous check on whether
our posterior widths are honest, making explicit how estimator variance blows up as claims-per-source falls
— the analytic version of §3.9's sparsity worry.

**Breaks:** binary claims, one latent bit per object, and the social-sensing framing assumes each source
independently *observes*. Our document kinds do not observe; they **disclose selectively from a shared
underlying truth**, and they copy each other. The independence that makes the EM and the bound work is
exactly what our corpus violates.

### 3.12 Ma, F., Li, Y., Li, Q., Qiu, M., Gao, J., Zhi, S., Su, L., Zhao, B., Ji, H. & Han, J. "FaitCrowd: Fine Grained Truth Discovery for Crowdsourced Data Aggregation." *KDD 2015*, 745–754. DOI [10.1145/2783258.2783314](https://doi.org/10.1145/2783258.2783314)

Jointly models question **topics** via a topic model over question text and per-source, per-topic expertise, so
a source can be reliable on one topic and not another, with topics discovered rather than given.

**Borrow:** topic-conditioned expertise is structurally the same object as our kind-and-visibility-conditioned
reliability — reliability as a function of a latent property of the item. Borrow the joint-inference pattern,
and the demonstration that inferring the partition is feasible when item text is available; our documents
have text, and "which visibility class is this step" is our latent partition.

**Breaks:** their partition is over *questions* by topic and its purpose is to let expertise vary; ours is over
*steps* by visibility class and its purpose is to govern **whether a source speaks at all**. No silence term,
so the mechanism we need — the partition driving disclosure — is absent. And it needs enough answers per
(source, topic) cell; ours are far sparser.

### 3.13 Empirical reality checks, and the survey

- Li, X., Dong, X. L., Lyons, K. B., Meng, W. & Srivastava, D. "Truth finding on the deep web: is the problem solved?" *PVLDB* 6(2), 2012, 97–108. DOI [10.14778/2535568.2448943](https://doi.org/10.14778/2535568.2448943)
- Waguih, D. A. & Berti-Équille, L. "Truth Discovery Algorithms: An Experimental Evaluation." arXiv:[1409.6428](https://arxiv.org/abs/1409.6428), 2014
- Zheng, Y., Li, G., Li, Y., Shan, C. & Cheng, R. "Truth inference in crowdsourcing: is the problem solved?" *PVLDB* 10(5), 2017, 541–552. DOI [10.14778/3055540.3055547](https://doi.org/10.14778/3055540.3055547)
- Li, Y., Gao, J., Meng, C., Li, Q., Su, L., Zhao, B., Fan, W. & Han, J. "A Survey on Truth Discovery." *SIGKDD Explorations* 18(2), 2016. arXiv:[1505.02463](https://arxiv.org/abs/1505.02463)

The survey is the taxonomy to position against. The three evaluations give the honest baseline: Zheng et al.
conclude **no single algorithm consistently outperforms the others**, and the deep-web paper found large
inconsistency among real sources that fusion only partially fixes. Waguih & Berti-Équille's framework
explicitly controls **source coverage**, conflict distribution and true-positive rate.

**Borrow:** cite these when arguing that "better tier wins" is not obviously worse than the off-the-shelf
alternatives, and therefore that **the case for our model has to rest on structure — silence, kinds,
changepoints — not on beating CRH by two F1 points.** That is the right framing for our contribution.

**Breaks:** every one of these benchmarks satisfies C1 — flat objects, dense-ish claim matrices, no silence
semantics, no time — so their conclusions do not transfer and **there is no existing benchmark we can
evaluate on.** That is an argument for our synthetic world, and it should be made explicitly rather than
apologetically.

### 3.14 Galárraga, L., Razniewski, S., Amarilli, A. & Suchanek, F. M. "Predicting Completeness in Knowledge Bases." *WSDM 2017*, 375–383. DOI [10.1145/3018661.3018739](https://doi.org/10.1145/3018661.3018739)

Investigates signals indicating **where a knowledge base is complete** versus where facts are missing,
combines them by rule mining, and shows completeness predictions improve downstream fact prediction.

**Borrow:** the KB literature's direct confrontation of our thesis — absence is informative only once you have
a model of where the source is complete. Borrow the framing: **learn a coverage model first, then read silence
through it.** That is literally π, and this is the existence proof that it is learnable from observable
signals; their signals (class/predicate popularity, cardinality patterns, sibling entities) are the analogue
of our kind and visibility covariates. See also §11.5 for the open-world/negation survey.

**Breaks:** discriminative rule mining producing a completeness *prediction*, not a generative model in which
completeness and truth are jointly inferred — so uncertainty in the completeness model does not propagate
into the fact posterior, which for us is essential (if we are unsure whether program pages disclose
back-office steps, the step-existence posterior must widen). One KB, one extraction process, so no
per-source-kind heterogeneity.

### 3.15 The LLM-era slice — thin, and honestly so

- Kucuk, H. B., Paton, N. W., Chen, J. & Wu, Z. "Single and Multi Truth Data Fusion using Large Language Models." arXiv:[2606.28062](https://arxiv.org/abs/2606.28062), 2026. Prompts LLMs directly to do the fusion task on tabular data and reports that prompting beats unsupervised truth discovery (DART, LTM) on three benchmarks. **Borrow:** a necessary baseline — if "just ask the LLM to resolve the conflict" matches our model, we need to know. **Breaks:** no source-reliability parameters at all, so no estimated reliabilities, no silence, no time, nothing to carry forward; it replaces the model with a prompt.
- Xie, J., Zhang, K., Chen, J., Lou, R. & Su, Y. "Adaptive Chameleon or Stubborn Sloth: Revealing the Behavior of Large Language Models in Knowledge Conflicts." arXiv:[2305.13300](https://arxiv.org/abs/2305.13300), 2023. **UNVERIFIED venue** (ICLR 2024 per the arXiv comments field only). **Borrow:** the finding that LLMs show "a strong confirmation bias when the external evidence contains some information that is consistent with their parametric memory" is a direct threat to our extractor — it will preferentially extract whatever matches its priors about how permitting works. That is a **correlated, non-random extractor error**, so our sensitivity/FPR parameters cannot be assumed independent across documents. **Breaks:** a behavioural audit of QA, no estimator.
- Wan, A., Wallace, E. & Klein, D. "What Evidence Do Language Models Find Convincing?" *ACL 2024*, 7468–7484. DOI [10.18653/v1/2024.acl-long.403](https://doi.org/10.18653/v1/2024.acl-long.403). arXiv:[2402.11782](https://arxiv.org/abs/2402.11782). **Borrow:** the finding that models rely heavily on a source's *relevance* while largely ignoring the stylistic markers humans use for credibility is the strongest available evidence that an LLM's implicit source weighting is **not** our evidence-tier ladder — it does not privilege statutory or official text. So if the LLM is doing any conflict resolution inside extraction, it is doing it on the wrong axis, and **extraction must be per-document and tier-blind**, with reliability weighting happening only in our model. **Breaks:** ConflictingQA is controversial web claims, not regulatory text; no estimator.
- Xu, R., Qi, Z., Guo, Z., Wang, C., Wang, H., Zhang, Y. & Xu, W. "Knowledge Conflicts for LLMs: A Survey." *EMNLP 2024*, 8541–8565. DOI [10.18653/v1/2024.emnlp-main.486](https://doi.org/10.18653/v1/2024.emnlp-main.486). **Borrow:** the taxonomy is useful terminology, and distinguishing its three cases matters: **inter-context** conflict is our real problem (two documents disagree), **context-memory** conflict is our *extractor's* problem (the LLM's priors fight the document), and **intra-memory** conflict is why the same LLM re-run gives different extractions. Only the first is data; the other two are extractor noise the confusion matrix must absorb.
- Hwang, J., Park, J., Park, H., Kim, D., Park, S. & Ok, J. "RA-RAG: Retrieval-Augmented Generation with Estimation of Source Reliability." *EMNLP 2025*, 34267–34291. DOI [10.18653/v1/2025.emnlp-main.1738](https://doi.org/10.18653/v1/2025.emnlp-main.1738). arXiv:[2410.22954](https://arxiv.org/abs/2410.22954). Estimates per-source reliability by cross-checking sources against each other, then retrieves from the top-κ reliable sources and aggregates by reliability-weighted voting. **Borrow:** the closest existing instantiation of "estimate source reliability over LLM-extracted claims", and therefore the right modern related-work anchor; its cross-checking estimator is a cheap initialiser. **Breaks:** scalar reliability, majority voting, retrieval-time heuristic with no posterior, no kind-level pooling, no time — and decisively, cross-checking presumes sources *overlap* on the same questions. Our kinds systematically do not overlap, which is what π encodes, so cross-checking has nothing to check on exactly the fields where we need it most.
- Pan, R., Cao, B., Lin, H., Han, X., Zheng, J., Wang, S., Cai, X. & Sun, L. "Not All Contexts Are Equal: Teaching LLMs Credibility-aware Generation." arXiv:[2404.06809](https://arxiv.org/abs/2404.06809), 2024. **UNVERIFIED venue** (EMNLP 2024 per arXiv comments only). Cited as a cautionary contrast: it is the "feed the tier ladder to the LLM" design, i.e. our hand-set weighting moved inside the prompt. Credibilities are inputs, not estimated.

**Blunt assessment of this slice:** an arXiv abstract search for `"truth discovery" AND "large language model"`
returns a handful of on-topic hits; a search for truth discovery combined with source coverage, abstention or
silence returns essentially one (Waguih & Berti-Équille). **There is no existing work that estimates
per-source-kind, covariate-conditioned reliability for LLM-extracted claims with an informative-silence
model.** The gap is real rather than a gap in the search — with the caveat that WebSearch was unavailable, so
the sweep covered arXiv, ACL Anthology, Crossref, OpenAlex, PMLR and JMLR but not the open web. One
confirming search-engine pass is worth doing before the paper asserts novelty.

---

## 4. Crowdsourcing label aggregation, and LLM-annotator calibration

We treat each document kind as an annotator with a confusion matrix. This is the literature that tells us
when that is identified and when it is not.

### 4.1 Dawid, A. P. & Skene, A. M. "Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm." *JRSS Series C (Applied Statistics)* 28(1), 1979, 20–28. DOI [10.2307/2346806](https://doi.org/10.2307/2346806)

The origin. Each observer *j* has a full **confusion matrix** π⁽ʲ⁾ₖₗ = P(observer says *l* | truth is *k*);
items have a class prior; EM alternates between soft-labelling items and re-estimating confusion matrices,
with no gold labels anywhere.

**Borrow:** the shape of our agency-ownership posterior, essentially unmodified — document kind *k* plays the
role of observer *j*, the published directory is the label set, and the per-kind confusion matrix is π⁽ᵏ⁾.
Also borrow the class prior, which for us is directory-derived and genuinely informative rather than uniform.

**Breaks:** three ways, all of which we must handle explicitly. (i) **Redundancy** — EM identifies π⁽ʲ⁾ from
*repeated* labelling of the same items by the same observers, and our sparsest cells have one document of a
kind asserting a field once. (ii) **Label switching** — the likelihood is invariant to permuting latent class
labels, so the solution is identified only up to permutation without an informative prior or an anchor; for
us the directory prior and lexically-observed department names largely pin this down, but it must be said.
(iii) **Silence** — the observers label every item they are given; there is no cell for "declined". Our π is
an addition to, not a variant of, this model. Note also the parameter count: with *K* departments a full
confusion matrix has K(K−1) free parameters per kind, so a 30-department directory means ~870 parameters per
document kind. Hopeless without severe structure (§4.10, §4.18).

### 4.2 Whitehill, J., Wu, T., Bergsma, J., Movellan, J. R. & Ruvolo, P. "Whose Vote Should Count More: Optimal Integration of Labels from Labelers of Unknown Expertise." *NeurIPS 22*, 2009 (GLAD)

Adds **item difficulty** alongside annotator ability: P(label correct) is logistic in ability × (1/difficulty),
so a hard item forgives disagreement and an easy item punishes it.

**Borrow:** item difficulty is what keeps a document kind from being penalised for missing a genuinely obscure
step — the annotation twin of §3.2's hardness. For us, **tie difficulty to visibility class rather than
leaving it free per step**: a back-office step is hard for every applicant-facing document by construction.
That tying is both more interpretable and vastly more identifiable.

**Breaks:** one-dimensional ability and difficulty, binary labels, no confusion matrix. And free per-item
difficulty is unidentified at our sparsity — with one or two labels per item, difficulty and ability trade off
and neither is recoverable.

### 4.3 Raykar, V. C., Yu, S., Zhao, L. H., Hermosillo Valadez, G., Florin, C., Bogoni, L. & Moy, L. "Learning From Crowds." *JMLR* 11(43), 2010, 1297–1322. <https://www.jmlr.org/papers/v11/raykar10a.html>

Learns a classifier *and* per-annotator sensitivity/specificity simultaneously, with features: the item's
covariates inform the latent label, which in turn sharpens the annotator parameters. Binary, categorical and
ordinal labels.

**Borrow:** the key structural insight for our near-degenerate cells — **when you have a model of the item,
you no longer need annotator redundancy to estimate annotator quality, because the model supplies the second
opinion.** For us the model of the item *is* the rest of the workflow posterior: the partial order, the
directory prior, the duration and fee structure. That is how a kind's confusion matrix stays estimable when
only one document asserts a field. The most important conceptual borrow in Area 4 after Dawid–Skene itself.

**Breaks:** two-sided rates, not a full K-way confusion matrix, and the guarantee is asymptotic in
items-per-annotator. **Circularity is a real hazard:** if the model of the item is wrong in a structured way,
the annotator parameters absorb the error and then reinforce it — and our model of the item is the very thing
we are inferring, with strong priors. Needs the check in §4.14.

### 4.4 Welinder, P., Branson, S., Belongie, S. & Perona, P. "The Multidimensional Wisdom of Crowds." *NeurIPS 23*, 2010

Embeds annotators and items in a shared Euclidean space, so annotator behaviour decomposes into competence,
expertise (*which* dimensions they attend to) and bias (*where* they put the boundary).

**Borrow:** conceptually the right decomposition for our disclosure problem. A program web page is not
*incompetent* about departments — it is *biased* (it names applicant-facing departments, not back-office
ones) and has restricted *expertise* (it attends to the applicant-visible dimensions of a step). Modelling a
document kind as attending to a subspace of the step's fields is a defensible, low-parameter alternative to a
full confusion matrix, and it gives visibility class a geometric interpretation.

**Breaks:** the embedding needs many annotations per annotator and per item; badly over-parameterised for our
volume. The bias/expertise separation is not identified without many items or a strong prior, and the paper
offers nothing for the sparse regime.

### 4.5 Karger, D. R., Oh, S. & Shah, D. "Iterative Learning for Reliable Crowdsourcing Systems." *NeurIPS 24*, 2011 — and "Budget-Optimal Task Allocation for Reliable Crowdsourcing Systems." *Operations Research* 62(1), 2014, 1–24. DOI [10.1287/opre.2013.1235](https://doi.org/10.1287/opre.2013.1235). arXiv:[1110.3564](https://arxiv.org/abs/1110.3564)

Message-passing on the task-worker bipartite graph, with matching upper and lower bounds on the budget
(labels per task) needed to reach a target error, establishing the **redundancy–accuracy frontier**.

**Borrow:** the most directly useful *answer* to "how many annotators per item are needed". Accuracy degrades
gracefully with redundancy above a threshold set by collective worker quality, and below it aggregation is no
better than random. Use the bounds to compute, per field type, **the minimum number of independent documents
below which the per-kind confusion matrix contributes nothing and the posterior is just the prior — and then
report that number honestly per field** rather than pretending the model is learning.

**Breaks:** a spammer-hammer single-parameter worker model with binary tasks (**UNVERIFIED** as strictly
one-coin — widely attributed but I could not confirm from a fetched page), and decisively it assumes you
*control the assignment* of workers to tasks, which is the whole point of "budget-optimal". We control
nothing; the corpus is what a city happened to publish. A diagnostic, never a design.

### 4.6 Zhou, D., Basu, S., Mao, Y. & Platt, J. C. "Learning from the Wisdom of Crowds by Minimax Entropy." *NeurIPS 25*, 2012

Aggregates by a minimax-entropy principle over the worker-item-label tensor with constraints on observed
marginals, rather than positing a generative annotator model.

**Borrow:** a model-free sanity check — if our Dawid–Skene-shaped posterior disagrees with a minimax-entropy
aggregate on the same claim matrix, the disagreement is attributable to our modelling assumptions and is
worth reporting. The "assume as little as possible" baseline.

**Breaks:** being assumption-light is the problem — no interpretable confusion matrix to carry forward,
nothing to put a prior on, no place to hang a disclosure propensity. Needs a reasonably filled tensor, which
ours is not.

### 4.7 Zhang, Y., Chen, X., Zhou, D. & Jordan, M. I. "Spectral Methods Meet EM: A Provably Optimal Algorithm for Crowdsourcing." *NeurIPS 27*, 2014; *JMLR* 17(102), 2016, 1–44. arXiv:[1406.3824](https://arxiv.org/abs/1406.3824)

Two-stage estimator for Dawid–Skene: a spectral/tensor method gives a consistent initial estimate of the
confusion matrices, then EM refines it, achieving the minimax rate up to a log factor. The abstract identifies
the problem precisely: the Dawid–Skene log-likelihood is **non-convex**, so vanilla EM has no guarantee.

**Borrow:** the practical warning. Our sampler will be exploring a multimodal posterior over confusion
matrices, and initialisation determines which mode we land in. Take the two-stage discipline: get a
moment-based or heuristic initial estimate per kind — e.g. from the synthetic-world calibration — and start
the sampler there, not from the prior mean. Note this echoes §3.8's independent finding.

**Breaks:** rates are asymptotic in both items and labels-per-item, and the spectral stage needs third-order
moments, i.e. items labelled by three or more annotators. **UNVERIFIED:** the commonly cited three-group
worker partition is in the full text only; I confirmed non-convexity and the spectral+EM structure from the
abstract but not that mechanism. Either way the binding constraint stands — three co-asserting document kinds
per field is a luxury we rarely have.

### 4.8 Allman, E. S., Matias, C. & Rhodes, J. A. "Identifiability of parameters in latent structure models with many observed variables." *Annals of Statistics* 37(6A), 2009, 3099–3132. DOI [10.1214/09-AOS689](https://doi.org/10.1214/09-AOS689). arXiv:[0809.5032](https://arxiv.org/abs/0809.5032)

The algebraic result underneath Dawid–Skene. Using **Kruskal's theorem** on three-way arrays, establishes
identifiability for latent-class models with conditionally independent observed views. Critically, classical
identifiability is "typically too strong"; what holds is **generic identifiability** — "the set of
nonidentifiable parameters has measure zero" — which is what rescues finite mixtures of Bernoulli products.

**Borrow:** the paper to cite for the exact answer to "how does Dawid–Skene degenerate when only one document
of a kind asserts a field". The honest answer, grounded here: identifiability of the per-kind confusion
matrices is a property of the *whole* claim array, not any one cell; it needs enough three-way co-assertion
structure; and it holds only **generically**, meaning there are measure-zero configurations where it fails
outright (two kinds with identical confusion matrices; a uniform confusion matrix) and a neighbourhood where
it is arbitrarily ill-conditioned. **Our situation — several document kinds that are genuinely similar
because they are derived from each other — sits uncomfortably close to that failure set.** So pooling by kind
is not a variance-reduction convenience: it is what moves us from non-identified to weakly identified, and
the prior is doing real identification work, not just regularisation. Say that in the paper rather than
hiding it.

**Breaks:** algebraic, silent on finite samples, and the observed views must be **conditionally independent
given the latent class** — which our copying kinds flatly violate, and conditional dependence is exactly what
destroys the Kruskal argument. **UNVERIFIED:** the "minimum three observed variables" and "up to label
permutation" phrasings are in theorem statements in the full text; verified here only at the level of the
generic-identifiability claim and the Kruskal basis.

### 4.9 Ibrahim, S., Fu, X., Kargas, N. & Huang, K. "Crowdsourcing via Pairwise Co-occurrences: Identifiability and Algorithms." *NeurIPS 2019*. arXiv:[1909.12325](https://arxiv.org/abs/1909.12325) — with Ibrahim, S. & Fu, X. "Crowdsourcing via Annotator Co-occurrence Imputation and Provable Symmetric Nonnegative Matrix Factorization." *ICML 2021*. arXiv:[2106.07193](https://arxiv.org/abs/2106.07193)

Prior tensor methods hinge on third-order statistics — three annotators co-labelling an item. This shows
Dawid–Skene is identifiable from **second-order (pairwise) statistics only**, under realistic conditions, via
structured/convex-geometry matrix factorisation. The 2021 follow-up recasts it as symmetric NMF and handles a
co-occurrence matrix that is "often (largely) incomplete, due to the lack of co-labeled items by some
annotators".

**Borrow:** the direct citable answer to the brief's question, and better news than expected: **two**
co-asserting document kinds per field suffices for identifiability, not three. Borrow the diagnostic — build
the document-kind co-assertion matrix for our corpus (how many fields are asserted by both kind *i* and kind
*j*) and read identifiability off its support. The 2021 paper tells us the binding constraint is not "few
documents per field" but **missing overlap between kinds**: pairs of kinds that never assert the same field.
That is the concrete, checkable degeneracy condition for our corpus, and it implies a targeted collection
strategy — **go find the documents that create the missing overlaps.**

**Breaks:** the conditions include a sufficiently-scattered / separability-type condition on the confusion
matrices that our derived-from-each-other kinds may violate. And these are moment-matching estimators, not
Bayesian, so they give conditions we can check rather than an estimator we can use. Neither handles silence.

### 4.10 The near-degenerate case head-on

- Khetan, A., Lipton, Z. C. & Anandkumar, A. "Learning From Noisy Singly-labeled Data." arXiv:[1712.04577](https://arxiv.org/abs/1712.04577). **UNVERIFIED venue** — widely cited as ICLR 2018, but the arXiv page carries no journal-ref and OpenReview is behind a bot check.
- Venanzi, M., Guiver, J., Kazai, G., Kohli, P. & Shokouhi, M. "Community-Based Bayesian Aggregation Models for Crowdsourcing." *WWW 2014*, 155–164. DOI [10.1145/2566486.2567989](https://doi.org/10.1145/2566486.2567989). *(Title, authors, venue, pages and DOI verified via Crossref; the mechanism description rests on background knowledge, as ACM DL returns 403 and Crossref supplies no abstract.)*
- Kim, H.-C. & Ghahramani, Z. "Bayesian Classifier Combination." *AISTATS 2012*, PMLR 22, 619–627. <https://proceedings.mlr.press/v22/kim12.html>

Khetan et al. is the explicit **one-label-per-item** result: worker quality is estimable with single
annotations by substituting the model's own predictions for inter-annotator redundancy, and labelling many
examples *once* beats labelling fewer examples many times once worker quality exceeds a threshold. Venanzi et
al. is the **clustered-annotator** answer: workers are pooled into latent communities that share
confusion-matrix behaviour. Kim & Ghahramani build on Dawid–Skene with MCMC requiring "neither probabilistic
base models, nor shared training data, nor error independence".

**Borrow:** together these resolve our sparsity problem, and the mapping is worth being precise about.
**Venanzi et al.'s community = our document kind — except that for us community membership is *observed*
(we know a page is an FAQ), which makes the model strictly better identified than theirs.** So: a full
confusion matrix at the *kind* level, individual documents as exchangeable draws within kind, and a
hierarchical prior shrinking toward the kind mean. Khetan et al. licenses the singly-asserted case and gives
a design implication that is good news: broad-and-shallow coverage (many fields asserted once) beats
narrow-and-deep, and broad-and-shallow is what a municipal corpus actually is. Kim & Ghahramani's relaxation
of error independence is the entry point for the copying problem.

**Breaks:** Khetan et al.'s guarantee is asymptotic in items and depends on a worker-quality threshold — below
it, single annotation provably fails, and we will not know a priori which side a kind is on. Its mechanism is
also §4.3's circularity: the model's predictions stand in for redundancy, so a structurally wrong prior
becomes self-confirming. Venanzi et al. still needs enough workers per community and items per worker; with
six kinds and a few hundred field assertions the shrinkage will be doing almost all the work, **which must be
reported**. None of the three models silence.

### 4.11 Models of annotation, and the pooling question

- Passonneau, R. J. & Carpenter, B. "The Benefits of a Model of Annotation." *TACL* 2, 2014, 311–326. DOI [10.1162/tacl_a_00185](https://doi.org/10.1162/tacl_a_00185)
- Paun, S., Carpenter, B., Chamberlain, J., Hovy, D., Kruschwitz, U. & Poesio, M. "Comparing Bayesian Models of Annotation." *TACL* 6, 2018, 571–585. DOI [10.1162/tacl_a_00040](https://doi.org/10.1162/tacl_a_00040)
- Hovy, D., Berg-Kirkpatrick, T., Vaswani, A. & Hovy, E. "Learning Whom to Trust with MACE." *NAACL-HLT 2013*, 1120–1130. <https://aclanthology.org/N13-1132/>

Passonneau & Carpenter argue that a probabilistic annotation model beats conventional inter-annotator
agreement statistics — replacing an agreement *statistic* with a *model* of the annotation process. Paun et
al. systematically compare six Bayesian annotation models across three axes — annotator ability, item
difficulty, and **parameter pooling (tying) across annotators and items** — ending with model-selection
guidelines. MACE is the widely-used generative spam-detection variant.

**Borrow:** Paun et al. is the most practically useful paper in Area 4 for us. Its pooling axis is exactly our
design decision — how much to tie confusion matrices across kinds and across steps — with empirical guidance
instead of rediscovery, and its model-selection guidelines give a defensible procedure for choosing between
one-coin and full confusion matrix per kind, which is the brief's explicit question. Passonneau & Carpenter is
the argument template for replacing "better tier wins" with a model.

**Breaks:** all three assume a fixed item set, annotators who label what they are given, categorical labels,
no item structure, no time, no silence. The pooling results are for annotators from a homogeneous pool; our
kinds are *systematically* different in ways we can name in advance, which is both an advantage (informative
priors) and a departure from the regime the guidelines came from.

### 4.12 Structured outputs and item-response theory

- Nguyen, A. T., Wallace, B., Li, J. J., Nenkova, A. & Lease, M. "Aggregating and Predicting Sequence Labels from Crowd Annotations." *ACL 2017*, 299–309. <https://aclanthology.org/P17-1028/>
- Lalor, J. P., Wu, H. & Yu, H. "Building an Evaluation Scale using Item Response Theory." *EMNLP 2016*, 648–657. <https://aclanthology.org/D16-1062/>

Nguyen et al. move crowd aggregation from independent items to **structured outputs** (sequence labels), where
annotator errors are correlated along the sequence and aggregation must respect the output structure. Lalor et
al. bring proper IRT (difficulty, discrimination, ability) to NLP evaluation-set construction.

**Borrow:** Nguyen et al. is the closest thing in Area 4 to aggregating *structured* annotations and the right
precedent for our partial order. The transferable idea: when the latent object has structure, aggregating
field-by-field independently is wrong, because annotator errors are correlated along the structure and the
structure constrains which combinations of field values are admissible. For us: a document that gets the
department wrong for step 3 is more likely to get it wrong for step 4 (correlated within-document error), and
**the partial-order constraint belongs in the aggregation likelihood, not in post-hoc cleanup.** Lalor et al.
supplies the IRT **discrimination** parameter that GLAD lacks — a step whose ownership is diagnostic of a
kind's quality versus one everybody gets right.

**Breaks:** Nguyen et al.'s structure is a linear sequence with a tractable dynamic program; a partial order
with latent step existence has no such factorisation, so their inference does not transfer. IRT needs many
respondents per item to identify difficulty and discrimination jointly — orders of magnitude more than we
have — so discrimination must be tied to observable step properties, not estimated freely.

### 4.13 Weak supervision with abstaining sources

- Ratner, A., De Sa, C., Wu, S., Selsam, D. & Ré, C. "Data Programming: Creating Large Training Sets, Quickly." *NeurIPS 29*, 2016, 3567–3575. arXiv:[1605.07723](https://arxiv.org/abs/1605.07723)
- Ratner, A., Bach, S. H., Ehrenberg, H., Fries, J., Wu, S. & Ré, C. "Snorkel: Rapid Training Data Creation with Weak Supervision." *PVLDB* 11(3), 2017, 269–282. DOI [10.14778/3157794.3157797](https://doi.org/10.14778/3157794.3157797). arXiv:[1711.10160](https://arxiv.org/abs/1711.10160)
- Ratner, A., Hancock, B., Dunnmon, J., Sala, F., Pandey, S. & Ré, C. "Training Complex Models with Multi-Task Weak Supervision." *AAAI* 33(01), 2019, 4763–4771. DOI [10.1609/aaai.v33i01.33014763](https://doi.org/10.1609/aaai.v33i01.33014763). arXiv:[1810.02840](https://arxiv.org/abs/1810.02840)
- Fu, D. Y., Chen, M. F., Sala, F., Hooper, S. M., Fatahalian, K. & Ré, C. "Fast and Three-rious: Speeding Up Weak Supervision with Triplet Methods." *ICML 2020*, PMLR 119, 3280–3291. arXiv:[2002.11955](https://arxiv.org/abs/2002.11955)
- Bach, S. H., He, B., Ratner, A. & Ré, C. "Learning the Structure of Generative Models without Labeled Data." *ICML 2017*, PMLR 70. arXiv:[1703.00854](https://arxiv.org/abs/1703.00854)
- Varma, P., Sala, F., He, A., Ratner, A. & Ré, C. "Learning Dependency Structures for Weak Supervision Models." *ICML 2019*, PMLR 97, 6418–6427. arXiv:[1903.05844](https://arxiv.org/abs/1903.05844)

The one literature where **partial coverage is native**. Labeling functions are "programs that label *subsets*
of the data" — every source abstains on most items by construction — and accuracies are recovered with **no
gold labels**: "by solving a matrix completion-style problem, we can recover the accuracies of these
multi-task sources given their dependency structure, but without any labeled data". FlyingSquid gives a
**closed-form** triplet-based solution. Bach et al. and Varma et al. then learn the **dependency structure
itself** without labels — Bach et al. by regularised marginal pseudolikelihood, Varma et al. by robust PCA
with unlabelled-data requirements growing only logarithmically in the number of sources.

**Borrow:** the most technically transferable cluster in either area, on four counts. (i) **Abstention is
built in** — and read carefully, this is *still not* our informative silence: in Snorkel, abstention is
uninformative by design, coverage is a nuisance rather than a signal. But the machinery for estimating
accuracies from a partially-observed source-agreement matrix is exactly what π needs, and the gap between
"abstention is a nuisance" and "abstention is a signal" is a clean, statable contribution. (ii) The
matrix-completion recovery of accuracies with no gold labels is the direct alternative to our EM/Gibbs and
is worth implementing as a fast initialiser (§4.7). (iii) FlyingSquid's triplet method connects to §4.9 —
identify the triples of document kinds that co-assert enough fields and read accuracies straight off them as
a prior. (iv) **Bach et al. and Varma et al. are the best available route to the copying problem**: learning
the dependency structure among correlated sources without gold labels is what §3.5 needed co-errors for and
what §3.6 needed a ground-truth sample for.

**Breaks:** all of it assumes conditional independence given the latent label unless the dependency structure
is supplied or learned — and the robust-PCA recovery needs many items to separate the low-rank dependency
signal, more than our field count. Labels are discrete and mostly binary or small-cardinality; a
30-department directory is a stretch. No item structure, no time. And the objective throughout is a *training
set* for a downstream discriminative model: the latent label is a means, not the quantity of interest. We want
the posterior itself.

### 4.14 One label, no gold: class-conditional noise identifiability

- Natarajan, N., Dhillon, I. S., Ravikumar, P. & Tewari, A. "Learning with Noisy Labels." *NeurIPS 26*, 2013
- Patrini, G., Rozza, A., Menon, A. K., Nock, R. & Qu, L. "Making Deep Neural Networks Robust to Label Noise: a Loss Correction Approach." *CVPR 2017*. DOI [10.1109/CVPR.2017.240](https://doi.org/10.1109/CVPR.2017.240). arXiv:[1609.03683](https://arxiv.org/abs/1609.03683)
- Liu, T. & Tao, D. "Classification with Noisy Labels by Importance Reweighting." *IEEE TPAMI*, 2015. DOI [10.1109/TPAMI.2015.2456899](https://doi.org/10.1109/TPAMI.2015.2456899)

The complement to Dawid–Skene: **exactly one noisy label per item, no redundancy**, and the question is
whether the class-conditional noise is recoverable. Patrini et al. state the structure precisely — loss
correction "amount[s] to at most a matrix inversion and multiplication, provided that we know the probability
of each class being corrupted into another", and they show how to estimate those probabilities in the
multi-class setting.

**Borrow:** this is the literature that actually answers "how does Dawid–Skene degenerate at one document per
field". The answer: it degenerates into the class-conditional-noise problem, where the confusion matrix is
**not** identified from the noisy labels alone. Identification requires one of three extra ingredients: (a)
items whose clean class is known with near-certainty (the anchor-point route, estimated from the extremes of
the noisy posterior), (b) known noise rates supplied externally, or (c) a parametric link from features to
the clean label. For us those are: (a) steps whose owning department is certain from the statute — **our
anchors**; (b) LLM error rates carried from the synthetic world; (c) the workflow model itself. **So the
synthetic-world calibration is not a nice-to-have; it is an identification requirement for the
singly-asserted cells.** That is a strong, precise, citable claim. Also borrow the forward/backward
loss-correction algebra: given the confusion matrix, correcting a downstream estimate is a matrix inversion.

**Breaks:** a single noise process, not per-kind processes, so it tells us about identification and not about
estimating several confusion matrices at once. Anchor-point estimation is notoriously unstable in finite
samples (a max/min over a posterior, driven by the tail), and with a 30-class directory the estimate will be
very noisy. The noise is assumed **instance-independent given the class**, which for us is false — a kind's
error rate depends on the step's visibility class, which is the whole point. **UNVERIFIED:** the terms
"anchor points" / "perfect examples" are in the body, not the fetched abstract; cite the mechanism, not the
terminology.

### 4.15 Egami, N. & Shin, S. "Debiased Inference for AI-Generated Data without Gold-Standard Labels: Identification via Multiple Imperfect Measurements." arXiv:[2608.18294](https://arxiv.org/abs/2608.18294), 18 August 2026, stat.ME. **Preprint, no venue.**

**The strongest new result in the review, and the closest structural analogue for the extractor layer.**
Starts from the same premise as DSL — "ignoring prediction errors in automated measurement leads to
substantial bias and invalid confidence intervals in downstream analyses, even if AI measurement accuracy is
high, e.g., above 90%" — then removes the gold-label requirement: DMM "combines multiple error-prone AI
measurements to enable valid downstream inference **without gold-standard labels**". Three details matter
enormously. It builds on **CP decomposition**; it assumes measurements are "independent conditional on the
latent true label **and observed unit-level features**"; and it allows "**unknown misclassification rates to
vary across annotation methods and across units of annotation**". It proves consistency and asymptotic
normality, and — the part that closes our biggest hole — develops **diagnostics to assess the
conditional-independence assumption**.

**Borrow:** essentially the whole thing, and it resolves three problems otherwise open in this review. (i) It
is the **gold-free identification result for covariate-conditioned confusion matrices**, which is exactly our
"document kind as annotator whose confusion matrix depends on the step's properties" — identified without the
real-corpus gold sample that PPI and DSL require. That materially weakens the §4.17 objection to our
synthetic-calibration plan. (ii) Its CP-decomposition basis connects straight to §4.8 and §4.9 — the same
algebra, now with covariates and an inference theory attached, which is precisely the identifiability argument
our paper needs to make. (iii) The **conditional-independence diagnostics** are the first principled test I
found for our copying problem.

**Breaks:** be clear-eyed. (i) It needs **multiple measurements per unit** — at least three for CP
decomposition to bite — the same redundancy requirement as everything else; DMM makes the redundant cells much
better and does nothing for the singly-asserted ones, which still fall back to §4.14. (ii) Its "multiple
measurements" are multiple *annotation methods applied to the same text*, not several *different documents*
about the same latent fact. That distinction is substantive: **several LLMs reading one program page share the
page's silence, so re-measuring does not recover a fact the page never stated.** DMM buys down *extractor*
error, not *source* error, and we need both. Encouragingly, the cheapest real improvement available to us
follows directly — **run several extractors over each document and treat them as DMM measurements**, which is
orthogonal to and composable with the document-kind model. (iii) The copying dependency is between
*documents*, not methods, so the diagnostics apply more cleanly to the extractor layer than the source layer.
(iv) The estimand is a downstream scalar or regression parameter, not a posterior over a latent partial order.
(v) No disclosure propensity anywhere.

### 4.16 LLM-as-annotator: capability, bias, and Bayesian Dawid–Skene

- Gilardi, F., Alizadeh, M. & Kubli, M. "ChatGPT outperforms crowd workers for text-annotation tasks." *PNAS* 120(30), 2023, e2305016120. DOI [10.1073/pnas.2305016120](https://doi.org/10.1073/pnas.2305016120). arXiv:[2303.15056](https://arxiv.org/abs/2303.15056)
- Kristensen-McLachlan, R. D., Canavan, M., Kardos, M., Jacobsen, M. & Aarøe, L. "Are chatbots reliable text annotators? Sometimes." *PNAS Nexus* 4, 2025. DOI [10.1093/pnasnexus/pgaf069](https://doi.org/10.1093/pnasnexus/pgaf069). arXiv:[2311.05769](https://arxiv.org/abs/2311.05769)
- Zheng, L., Chiang, W.-L., Sheng, Y., *et al.* "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." *NeurIPS 2023 Datasets and Benchmarks*. arXiv:[2306.05685](https://arxiv.org/abs/2306.05685) (13 authors)
- Gao, Y., Xu, G., Wang, Z. & Cohan, A. "Bayesian Calibration of Win Rate Estimation with LLM Evaluators." *EMNLP 2024*. arXiv:[2411.04424](https://arxiv.org/abs/2411.04424)
- Wang, P., Li, L., Chen, L., *et al.* "Large Language Models are not Fair Evaluators." *ACL 2024*, 9440–9450. DOI [10.18653/v1/2024.acl-long.511](https://doi.org/10.18653/v1/2024.acl-long.511)
- Panickssery, A., Bowman, S. R. & Feng, S. "LLM Evaluators Recognize and Favor Their Own Generations." *NeurIPS 37*, 2024, 68772–68802. DOI [10.52202/079017-2197](https://doi.org/10.52202/079017-2197). arXiv:[2404.13076](https://arxiv.org/abs/2404.13076)
- Wataoka, K., Takahashi, T. & Ri, R. "Self-Preference Bias in LLM-as-a-Judge." arXiv:[2410.21819](https://arxiv.org/abs/2410.21819), 2024. **UNVERIFIED venue** (NeurIPS 2024 workshop per arXiv comments only)

Gilardi et al. establish that a zero-shot LLM can beat crowd workers at ~1/20th the cost;
Kristensen-McLachlan et al. are the replication-style counterpoint showing reliability is strongly
**task-dependent**. Zheng et al. enumerate the systematic failures — "position, verbosity, and
self-enhancement biases, as well as limited reasoning ability". Gao et al. close the loop by proposing
**Bayesian Dawid–Skene** to correct the intrinsic bias of LLM evaluators, validated on six datasets. Wang et
al. quantify positional bias and calibrate it away by balanced position swapping; Panickssery et al. show
self-recognition ability correlates **causally** with self-preference; Wataoka et al. define a
**perplexity-based** self-preference metric.

**Borrow:** five concrete things. (i) Gao et al. is the peer-reviewed precedent for the exact move we are
making — putting an LLM into a Bayesian Dawid–Skene model as an annotator whose error rates are parameters.
(ii) Zheng et al.'s bias taxonomy is the checklist for what our per-kind confusion matrix must absorb:
verbosity bias predicts over-extraction from long staff reports; position bias predicts fields mentioned early
are extracted more reliably; self-enhancement predicts favouring phrasings matching the model's own priors.
All three are **document-kind-correlated**, which is why the per-kind matrix is the right unit. (iii) Wang et
al.'s swap-and-average calibration generalises cheaply to extraction — randomise the order in which candidate
departments or document sections are presented across repeated extractions, and the order-induced component
averages out. Free variance reduction; do it regardless. (iv) Panickssery et al. is a specific named hazard
for our synthetic calibration: **if the synthetic corpus is LLM-generated and the extractor is the same model
family, measured sensitivity on the synthetic world is biased upward**, so the transferred priors are
overconfident in the direction that hurts. Mitigation: generate the synthetic corpus with a different model,
or better, from templates derived from real documents. (v) Wataoka et al. is the most actionable of the bias
papers because perplexity is **measurable per document** — a dense fee study with unusual formatting is
higher-perplexity than a clean program page, which is a cheap legitimate predictor of extraction error rate,
better than document kind alone. Kristensen-McLachlan et al. independently argue that a *single* global
extractor error rate is indefensible, which supports our per-field parameterisation without relying on any of
our own commitments.

**Breaks:** Gilardi et al. is four annotation tasks on political-communication text with short labels — its
accuracy numbers must not be borrowed as priors for structured extraction from long heterogeneous documents.
Gao et al.'s Dawid–Skene is over *pairwise preference* judgements in the dense redundant regime, not ours.
And **none of these has any notion of an annotator that declines to answer** — an LLM judge always emits a
verdict, whereas our extractor's most informative output is often "the document does not say", which here
would be a parse failure rather than data.

### 4.17 Valid inference from an imperfect annotator, and what it costs us

- Angelopoulos, A. N., Bates, S., Fannjiang, C., Jordan, M. I. & Zrnic, T. "Prediction-powered inference." *Science* 382(6671), 2023, 669–674. DOI [10.1126/science.adi6000](https://doi.org/10.1126/science.adi6000). arXiv:[2301.09633](https://arxiv.org/abs/2301.09633)
- Angelopoulos, A. N., Duchi, J. C. & Zrnic, T. "PPI++: Efficient Prediction-Powered Inference." arXiv:[2311.01453](https://arxiv.org/abs/2311.01453), 2023. *(Correction to the brief: Bates is not an author on PPI++.)*
- Egami, N., Hinck, M., Stewart, B. M. & Wei, H. "Using Imperfect Surrogates for Downstream Inference: Design-based Supervised Learning for Social Science Applications of Large Language Models." *NeurIPS 2023*. arXiv:[2306.04746](https://arxiv.org/abs/2306.04746)
- Egami, N., Hinck, M., Stewart, B. M. & Wei, H. "Using Large Language Model Annotations for the Social Sciences: A General Framework of Using Predicted Variables in Downstream Analyses." **PARTIALLY VERIFIED** — listed on the authors' pages (<https://naokiegami.com/dsl>) as *AJPS*, conditionally accepted; no DOI, volume or Crossref record. **Cite as a working paper.**
- Ludwig, J., Mullainathan, S. & Rambachan, A. "Large Language Models: An Applied Econometric Framework." arXiv:[2412.07031](https://arxiv.org/abs/2412.07031), 2024
- Baumann, J., Röttger, P., Urman, A., Wendsjö, A., Plaza-del-Arco, F. M., Gruber, J. B. & Hovy, D. "Large Language Model Hacking: Quantifying the Hidden Risks of Using LLMs for Text Annotation." arXiv:[2509.08825](https://arxiv.org/abs/2509.08825), 2025. **No venue listed.**
- Zrnic, T. & Candès, E. J. "Active Statistical Inference." *ICML 2024*, PMLR 235, 62993–63010. arXiv:[2403.03208](https://arxiv.org/abs/2403.03208) — with Li, P., Zrnic, T. & Candès, E. "Robust Sampling for Active Statistical Inference." *NeurIPS 38*, 2025, 76645–76674. DOI [10.52202/085713-2312](https://doi.org/10.52202/085713-2312). arXiv:[2511.08991](https://arxiv.org/abs/2511.08991)
- Zrnic, T. & Candès, E. J. "Cross-Prediction-Powered Inference." arXiv:[2309.16598](https://arxiv.org/abs/2309.16598), 2023
- Kilian, V., Cortinovis, S. & Caron, F. "Anytime-valid, Bayes-assisted, Prediction-Powered Inference." arXiv:[2505.18000](https://arxiv.org/abs/2505.18000), 2025. **No venue listed.**
- Fisch, A., Maynez, J., Hofer, R. A., Dhingra, B., Globerson, A. & Cohen, W. W. "Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation." arXiv:[2406.04291](https://arxiv.org/abs/2406.04291), 2024 — with Hofer, R. A., *et al.* "Bayesian Prediction-Powered Inference." arXiv:[2405.06034](https://arxiv.org/abs/2405.06034), 2024
- Kluger, D. M., Lu, K., Zrnic, T., Wang, S. & Bates, S. "Prediction-Powered Inference with Imputed Covariates and Nonuniform Sampling." arXiv:[2501.18577](https://arxiv.org/abs/2501.18577), 2025

PPI gives provably valid confidence intervals when a large unlabelled set carries ML predictions and a smaller
set carries gold labels, with **no assumptions on the ML algorithm**; PPI++ makes it light and
quality-adaptive, always improving on the gold-only interval. Egami et al.'s DSL is the sharper warning and
the doubly-robust fix: "direct use of surrogate labels in downstream statistical analyses leads to
**substantial bias and invalid confidence intervals, even with high surrogate accuracy of 80–90%**", and DSL
restores validity "even when surrogates are arbitrarily biased" — crucially "by **controlling the probability
of sampling documents for gold-standard labeling**". Ludwig et al. reach the same conclusion from
econometrics. Baumann et al. supply the empirical scale: 13 million labels from 18 LLMs across 2,361
hypotheses replicating 37 tasks from 21 published studies, finding configuration choices alone produce
**incorrect conclusions in ~31% of hypotheses for state-of-the-art LLMs**, that "with just a handful of prompt
paraphrases, virtually anything can be presented as statistically significant", that risk falls as effect
sizes grow, and that of 21 mitigations tested **human annotations provide crucial protection against false
positives**.

**Borrow:** five things, and this entry should change what we do, not just what we cite.
1. **Quote the 80–90% result and the 31% figure.** Together they are the strongest available justification for
   modelling extractor error as a parameter rather than assuming it away.
2. **Baumann et al. imply a process commitment:** prompt and model choice are researcher degrees of freedom
   with p-hacking-scale consequences, so fix and report the extraction configuration before looking at
   results, and report sensitivity across a few prompt paraphrases as a robustness column. Their effect-size
   finding also tells us where to be careful — our fragile claims are the small differences (is this fee $340
   or $410; 2 days or 4), not the large structural ones.
3. **PPI++'s adaptivity is the property to state and test:** when the extractor is good the posterior should
   approach the all-documents posterior; when bad it should fall back gracefully to the gold subset, never
   worse.
4. **Active inference answers "we can only hand-verify 50 assertions — which 50?"** Sample the verification
   set from high-posterior-entropy fields, using our own posterior as the uncertainty signal; the 2025
   robustness result means we are not punished when those uncertainty estimates are themselves miscalibrated,
   which they will be. This makes hand-labelling a designed component rather than a cost, and it composes
   with sequential arrival: each new document changes which fields are most worth verifying.
5. **Kilian, Cortinovis & Caron is the rigorous home for our synthetic calibration.** It extends PPI "to the
   sequential setting, where labelled and unlabelled datasets grow over time", giving confidence sequences
   "asymptotically valid uniformly over time" that "naturally accommodate prior knowledge on the quality of
   the predictions". Both halves matter: **anytime validity** is required because we report intervals
   continuously as documents are found, and a fixed-time PPI interval recomputed after every new document is
   invalid by optional stopping — a mistake we would otherwise have made. And **Bayes-assisted** means a prior
   on predictor quality buys efficiency if right and costs only efficiency, not validity, if wrong. That is
   exactly the role the synthetic world should play.
   Also: stratified PPI's strata are **our document kinds**; cross-prediction removes the need for a predictor
   pre-trained on the real corpus (which is precisely our situation); and Kluger et al. handle **imputed
   covariates** (our visibility class and step identity are LLM-imputed, so the standard clean-covariate PPI
   setup does not describe us) and **nonuniform gold sampling** (ours will be nonuniform by construction) —
   which disciplines us to log exactly how verification targets were chosen, an easy thing to get wrong
   retroactively and impossible to fix after the fact.

**Breaks — and this is the most important "breaks" in the review, so it deserves bluntness. All of these
require a gold sample drawn from the real corpus by a known, controlled sampling design.** Egami et al.'s
validity rests explicitly on controlling the sampling probability for gold labelling; Ludwig et al. insist on
a validation sample; PPI needs labelled pairs from the same distribution. **Our plan — calibrate LLM error
rates on a synthetic world with known truth and carry them to the real corpus as priors — is not an instance
of any of these methods, and none of them licenses it.** It is a *transfer* assumption, and it is exactly the
assumption PPI was invented to avoid needing: the synthetic world is not a random subsample of the real
corpus, and its documents were generated by our own model of how cities publish, so error rates measured
there are error rates against our generative assumptions, not against reality. Two implications to accept
rather than argue around: (a) synthetic calibration can legitimately supply prior means and the *shape* of
the confusion matrices, but the priors must be weak enough for real evidence to move them, and prior
sensitivity must be reported; (b) **we should hand-label a genuinely random sample of real documents — even
50–100 field assertions — and run PPI++ or DSL on the headline estimates.** That converts our strongest
methodological vulnerability into a checkable claim. Note also that these methods target scalar or
low-dimensional estimands, so they apply to summary quantities extracted from our posterior, not to the
posterior itself.

### 4.18 Supporting and orienting entries

- Ibrahim, S., Traganitis, P. A., Fu, X. & Giannakis, G. B. "Learning From Crowdsourced Noisy Labels: A Signal Processing Perspective." arXiv:[2407.06902](https://arxiv.org/abs/2407.06902), 2024. The best entry point to the identifiability landscape — reviews identifiability of tensor and NMF methods from Dawid–Skene through deep methods, extending to RLHF/DPO. **Read this first; it is the map for §4.7–§4.9.**
- Gao, C. & Zhou, D. "Minimax Optimal Convergence Rates for Estimating Ground Truth from Crowdsourced Labels." arXiv:[1310.5764](https://arxiv.org/abs/1310.5764), 2013. Rates for projected EM on Dawid–Skene with a matching lower bound. **Breaks:** the abstract makes no claim about one-coin vs full confusion matrix or raters-per-item; do not cite it for redundancy requirements.
- Bonald, T. & Combes, R. "A Minimax Optimal Algorithm for Crowdsourcing." *NeurIPS 2017*. arXiv:[1606.00226](https://arxiv.org/abs/1606.00226). A minimax lower bound on worker-reliability estimation error valid for *any* procedure, plus a non-iterative streaming-capable estimator matching it. **Borrow:** the bound tells us the best any method could do at our redundancy, and the streaming property suits sequential arrival.
- Traganitis, P. A., Pagès-Zamora, A. & Giannakis, G. B. "Blind Multiclass Ensemble Classification." *IEEE TSP*, 2018. DOI [10.1109/TSP.2018.2860562](https://doi.org/10.1109/TSP.2018.2860562). arXiv:[1712.02903](https://arxiv.org/abs/1712.02903). Gold-free multiclass confusion-matrix estimation by joint tensor and matrix factorisation, with a performance analysis.
- Sheng, V. S., Provost, F. & Ipeirotis, P. G. "Get another label? Improving data quality and data mining using multiple, noisy labelers." *KDD 2008*, 614–622. DOI [10.1145/1401890.1401965](https://doi.org/10.1145/1401890.1401965). The canonical empirical treatment of "how many labels per item is worth it".
- Raykar, V. C. & Yu, S. "Eliminating Spammers and Ranking Annotators for Crowdsourced Labeling Tasks." *JMLR* 13(16), 2012, 491–518. <https://www.jmlr.org/papers/v13/raykar12a.html>. Defines a spammer score and prunes random responders — **the operational test for whether a document kind carries any signal at all, worth running on each kind before trusting its confusion matrix.**
- Shah, N. B., Balakrishnan, S. & Wainwright, M. J. "A Permutation-based Model for Crowd Labeling: Optimal Estimation and Robustness." *IEEE Trans. Information Theory*, 2020. DOI [10.1109/TIT.2020.3045613](https://doi.org/10.1109/TIT.2020.3045613). arXiv:[1606.09632](https://arxiv.org/abs/1606.09632). **Important warning:** "permutation" here means the unknown *ordering of worker abilities*, a generalisation of Dawid–Skene with weaker parametric assumptions — **not** label-switching non-identifiability. Do not cite it for the latter.
- Feng, Y., Zhang, K., Ouchouid, H., Kaniamparambil, A., Souflas, I. & Angeloudis, P. "Strategic Fusion of Vision Language Models: Shapley-Credited Context-Aware Dawid-Skene for Multi-Label Tasks in Autonomous Driving." arXiv:[2510.01126](https://arxiv.org/abs/2510.01126), 2025. Learns "per-model, per-label, **context-conditioned** reliabilities" and fuses reports into calibrated posteriors, with a reputation state that adapts to drift. **Borrow:** the only work I found making the confusion matrix an explicit function of *context covariates* — structurally our move — plus a drift-adaptive reliability state relevant to changepoints. **Breaks:** reliabilities are learned from labelled history, i.e. fully supervised, which is the ingredient we lack.
- Ghiasvand, S., Beliaev, M., Alizadeh, M. & Pedarsani, R. "REALM: Reliable Expertise-Aware Language Model Fine-Tuning from Noisy Annotations." arXiv:[2604.17289](https://arxiv.org/abs/2604.17289), 2026. Jointly learns model parameters and a **scalar** expertise per annotator, "entirely unsupervised and requiring nothing beyond annotator identity", beating majority vote and Dawid–Skene aggregation across 12 configurations on real data. **Borrow:** a clean current empirical answer to the one-coin-vs-full-matrix question — under realistic sparsity a *one-coin* model outperformed full Dawid–Skene, which argues for **starting with one-coin per document kind and escalating to a full confusion matrix only for the kinds where the co-assertion matrix (§4.9) supports it.** **Breaks:** scalar expertise cannot express directional confusion (which department gets named instead), which is a substantive question for us; and the mixture-with-uniform error model is implausible for our extractor, whose errors are structured.

**Negative result worth recording.** An arXiv abstract search for `"Dawid-Skene" AND "language model"` returns
five hits total, none closer than §4.16's Gao et al. and §4.15's DMM. No paper's abstract frames Dawid–Skene
label-switching non-identifiability as its subject — that claim must be cited to the full text of §4.8 or
§4.9, not to a dedicated work.

---

## 5. Bayesian network / DAG structure learning, and sequential variants

**Read this framing first, because it governs the area.** Our object is a **precedence DAG over
activities**, not a conditional-independence DAG over random variables. Three consequences:

- **The scoring functions do not transfer at all.** BDe/BDeu/K2 score the marginal likelihood of data
  columns given parent columns. We have no data columns per step and no notion of a step's value being
  generated from its parents'. Anything whose central contribution is a score gives us vocabulary and
  priors, not machinery.
- **The MCMC state spaces transfer almost completely, and this is the prize.** The sequence DAG-space →
  linear-order-space → partition-space → partial-order-space is exactly our representational question,
  already worked out with mixing diagnostics and known failure modes.
- **One bridge is worth more than the rest of the area.** Friedman & Koller's order-MCMC is *biased*:
  sampling node orders induces a non-uniform prior over DAGs, because a DAG consistent with more linear
  extensions is counted more often. Partition-MCMC exists to remove that bias. The bias term is **the number
  of linear extensions of the DAG** — the identical object that appears as the *normalising constant of our
  likelihood* in §6. This field spent fifteen years building machinery to compute and cancel |L(G)|. For us
  it is not a nuisance but the signal. Mine it for the counting, not the correction.

### 5.1 Foundations, grouped

- Cooper, G. F. & Herskovits, E. "A Bayesian method for the induction of probabilistic networks from data." *Machine Learning* 9(4), 1992, 309–347. DOI [10.1007/BF00994110](https://doi.org/10.1007/BF00994110)
- Heckerman, D., Geiger, D. & Chickering, D. M. "Learning Bayesian networks: the combination of knowledge and statistical data." *Machine Learning* 20(3), 1995, 197–243. DOI [10.1007/BF00994016](https://doi.org/10.1007/BF00994016)
- Madigan, D. & York, J. "Bayesian graphical models for discrete data." *International Statistical Review* 63(2), 1995, 215–. DOI [10.2307/1403615](https://doi.org/10.2307/1403615) — **UNVERIFIED end page**: Crossref and OpenAlex record only first page 215, and both list a third contributor ("Denis Allard") who is the discussant, not a co-author.

Cooper & Herskovits originate closed-form Bayesian scoring (K2) plus greedy search **given a known node
ordering**. Heckerman–Geiger–Chickering introduce BDe/BDeu, likelihood equivalence, and a way to build a
structure prior from an expert's **prior network**. Madigan & York introduce MC³, Metropolis–Hastings over
graph space with single-edge moves.

**Borrow:** the prior-network construction is the right template for our document-asserted precedences —
treat a document's claims as a prior network G₀ and put p(P) ∝ ∏ κ^δ(pair) over deviations, with κ a learned
per-source credibility. That is far better calibrated than hard-constraining the poset to obey documents,
which conflicting sources make impossible anyway. From Madigan & York, take the **model-averaging posture**:
report posterior edge probabilities, not one MAP graph, which for us means reporting P(i ≺ j | evidence) and
honestly returning ≈ prior mass for the majority of pairs with no evidence.

**Breaks:** the scores are unusable. K2's fixed-order assumption is the assumption we cannot make. And
likelihood equivalence — Markov-equivalent DAGs scoring identically — is a *feature* there and a disaster
framing for us: `A→B` and `A←B` are genuinely different claims about the world, so we must not import any
scoring convention that cannot distinguish them. Naive MC³ also mixes badly once *n* grows, which is what
§5.3–§5.5 exist to fix.

### 5.2 Friedman, N. & Koller, D. "Being Bayesian about network structure." *Machine Learning* 50(1–2), 2003, 95–125. DOI [10.1023/A:1020249912095](https://doi.org/10.1023/A:1020249912095)

Order-MCMC: run the chain over **linear orders** on nodes rather than over DAGs, because conditional on an
order the posterior over DAGs factorises and edge probabilities have closed form. Mixes far better than MC³.

**Borrow:** the collapsing idea — sample the *order*, integrate out the rest analytically — is the single most
important structural move available to us, and the direct ancestor of the samplers in §6. Read the
order-space-prior section as documentation of our likelihood normaliser.

**Breaks:** the closed form needs a decomposable score. And order-MCMC's state is a **total** order, so it
cannot express incomparability — the wrong end of the very axis we care about. §5.4 is its correct
generalisation.

### 5.3 Grzegorczyk, M. & Husmeier, D. "Improving the structure MCMC sampler for Bayesian networks by introducing a new edge reversal move." *Machine Learning* 71(2–3), 2008, 265–305. DOI [10.1007/s10994-008-5057-7](https://doi.org/10.1007/s10994-008-5057-7)

Shows why single-edge MCMC in DAG space mixes badly and introduces the REV move: reverse an edge while
simultaneously resampling both endpoints' parent sets, letting the chain cross valleys that single-edge moves
cannot.

**Borrow:** the most immediately implementable item in Area 5 *if* we keep a pairwise-Bernoulli-with-
transitivity representation, because we will hit exactly the trap REV addresses — flipping `i ≺ j` alone
almost always violates transitivity or lands in a near-zero-probability state, and the chain freezes. The
transferable principle: **make a compound move that repairs the constraint inside the proposal rather than
rejecting.** Reverse a precedence relation and recompute the transitive closure in the proposal, with the
correct Hastings ratio.

**Breaks:** the acceptance ratio is derived for a modular score, so the formulas need rederiving. And note
the better answer: the latent-position prior in §6.1 eliminates the problem entirely by making transitivity
automatic, which beats fixing the sampler.

### 5.4 Niinimäki, T., Parviainen, P. & Koivisto, M. "Structure discovery in Bayesian networks by sampling partial orders." *JMLR* 17(57), 2016, 1–47. <https://jmlr.org/papers/v17/15-140.html> — precursor: *UAI 2011*, 557–564. arXiv:[1202.3753](https://arxiv.org/abs/1202.3753)

MC³ and annealed importance sampling with the chain state being a **partial order on the nodes**; conditional
on a sampled partial order, quantities of interest are computed exactly by dynamic programming, tractable
"when the partial orders contain relatively few down-sets". Beats both DAG-space and linear-order-space
samplers empirically, and includes a DP algorithm for **counting topological sorts** so arbitrary
(non-modular) priors can be handled.

**Borrow:** the only place in Area 5 where the MCMC state space is literally our latent object. Four takes:
(i) the **poset-space proposal kernel** and its Hastings ratio, needed regardless of likelihood; (ii)
**"few down-sets" as the governing complexity parameter** — the thing to control is poset *width*, not step
count, which is actionable because permitting workflows really are narrow and deep; (iii) the **DP for
counting topological sorts** is reusable directly as our likelihood normaliser, and is the single most
transferable piece of code in Area 5; (iv) the empirical finding that partial-order space dominates
linear-order space is strong prior evidence against a distribution-over-linear-extensions representation.

**Breaks:** everything inside the conditional-on-poset step is BDe scoring. And the partial order here is a
*computational device* — a relaxation to make DAG-space integration tractable — not an object of inference;
there is no observation model for order evidence, because the data are variable observations. *n* is fixed
and known. Take the state space, the proposals and the counting DP; discard the target.

### 5.5 Kuipers, J. & Moffa, G. "Partition MCMC for inference on acyclic digraphs." *JASA* 112(517), 2017, 282–299. DOI [10.1080/01621459.2015.1133426](https://doi.org/10.1080/01621459.2015.1133426)

The chain state is an ordered **partition** of nodes into levels (an antichain decomposition), mixing nearly
as well as order-MCMC but **without** inducing the linear-extension bias, so it samples the true posterior.

**Borrow:** two high-value items. (i) The **ordered-partition state space is very likely a better
representation for us than either candidate in our design.** A workflow is naturally a sequence of stages
with steps inside a stage mutually incomparable — that is exactly an ordered partition. It gives genuine
incomparability (unlike a linear extension) while making transitivity structurally free (unlike pairwise
Bernoulli indicators, where transitivity is a painful constraint). (ii) The bias analysis is the clearest
exposition anywhere of *why* the linear-extension count appears.

**Breaks:** the bias removal is the paper's point and is exactly backwards for us — we *want* that weight,
because for us it is the likelihood of an observed trace. So read the analysis and deliberately do not apply
the fix. An ordered partition is also strictly less expressive than a general poset, and §6.1 explicitly
tested and **rejected** the comparable bucket-order restriction on real data. Treat it as a tractable
approximation whose adequacy must be checked.

Related, for the search-space-restriction pattern: Kuipers, J., Suter, P. & Moffa, G. "Efficient sampling and
structure learning of Bayesian networks." *JCGS* 31(3), 2022, 639–650. DOI
[10.1080/10618600.2021.2020127](https://doi.org/10.1080/10618600.2021.2020127); software Suter, Kuipers,
Moffa & Beerenwinkel, *JSS* 105(9), 2023, DOI [10.18637/jss.v105.i09](https://doi.org/10.18637/jss.v105.i09).
**Borrow** the restrict-then-sample-then-**correct** loop: restrict each step's candidate predecessors to
those with documentary or trace support, sample within that, then run the iterative expansion step to recover
relations no source asserted. The iterative correction is what protects us against one bad source
permanently pruning a true relation — worth copying carefully, since our sources conflict by construction.
**Breaks:** the restriction step is CI testing on variable data; our screening rule has no calibrated error
rate, and BiDAG is not reusable as code.

### 5.6 Koivisto, M. & Sood, K. "Exact Bayesian structure discovery in Bayesian networks." *JMLR* 5, 2004, 549–573. <https://www.jmlr.org/papers/v5/koivisto04a.html> — with Eaton, D. & Murphy, K. "Bayesian structure learning using dynamic programming and MCMC." *UAI 2007*. arXiv:[1206.5247](https://arxiv.org/abs/1206.5247)

Koivisto & Sood compute exact posterior edge probabilities in O(n·2^n) by DP over subsets under an
order-modular prior, no MCMC, for *n* up to roughly 25–30. Eaton & Murphy use that tractable-but-biased
posterior as an MCMC **proposal** targeting the correct posterior.

**Borrow:** Eaton & Murphy's two-stage pattern is directly usable and I would prioritise it. We have a cheap
biased surrogate for free: the transitive closure of all document-asserted precedences, with unasserted pairs
incomparable. Use that as the MCMC proposal and let case traces correct it through the MH ratio. This puts
the documents to work as *proposals* rather than as likelihood, which matches their actual reliability, and
means we never propose wildly implausible posets. From Koivisto & Sood, note that the tractability envelope
(n ≈ 25–30) brackets our plausible step counts, and that the same down-set recursion reappears in §6.10's
linear-extension counting.

**Breaks:** the O(n·2^n) result depends entirely on score decomposability over (node, parent set), which our
document-factorised likelihood lacks, so we cannot get the exact posterior this way. The order-modular prior
required by the DP is precisely the one that introduces the linear-extension bias — we cannot have both
exactness and an unbiased structure prior. And *n* is unknown and growing, which breaks any fixed 2^n table.

### 5.7 Sequential and non-stationary structure

- Friedman, N. & Goldszmidt, M. "Sequential update of Bayesian network structure." *UAI 1997*. arXiv:[1302.1538](https://arxiv.org/abs/1302.1538)
- Robinson, J. W. & Hartemink, A. J. "Learning non-stationary dynamic Bayesian networks." *JMLR* 11(118), 2010, 3647–3680. <https://www.jmlr.org/papers/v11/robinson10a.html>
- Lèbre, S., Becq, J., Devaux, F., Stumpf, M. P. H. & Lelandais, G. "Statistical inference of the time-varying structure of gene-regulation networks." *BMC Systems Biology* 4, 2010, 130. DOI [10.1186/1752-0509-4-130](https://doi.org/10.1186/1752-0509-4-130) (ARTIVA)
- Grzegorczyk, M. & Husmeier, D. "Non-homogeneous dynamic Bayesian networks for continuous data." *Machine Learning* 83(3), 2011, 355–419. DOI [10.1007/s10994-010-5230-7](https://doi.org/10.1007/s10994-010-5230-7)

Friedman & Goldszmidt is still, nearly thirty years on, the reference on incremental BN structure learning:
maintain a summary of past observations rather than the data, with an explicit knob trading network quality
against retained information. Robinson & Hartemink put a prior on the number and placement of structural
changepoints with information sharing between adjacent segments. ARTIVA puts an **independent changepoint
process on each node's incoming edge set** by reversible-jump MCMC. Grzegorczyk & Husmeier allocate
observations to segments by mixture models rather than contiguous changepoints.

**Borrow:** three things. From Friedman & Goldszmidt, the honest lesson that incremental structure learning
needs a *declared* memory/fidelity tradeoff — you cannot refit incrementally and claim to have refit exactly,
so parameterise the gap. From ARTIVA, the **per-node changepoint process**, which is the right granularity
for us and a real improvement on a global changepoint: regulations change piecemeal, a fee step gets added
while the inspection sequence is untouched, so model changepoints on each step's incoming-precedence set
independently. From Grzegorczyk & Husmeier, non-contiguous allocation covers sources disagreeing for reasons
*other than time* — two jurisdictions, one process — which lets one mechanism serve both version drift and
jurisdictional variants, and lets the posterior decide which explanation the data prefer. That unification is
genuinely attractive for our conflict layer.

**Breaks:** Friedman & Goldszmidt works because the score is built from sufficient statistics of i.i.d. data.
Our documents are neither i.i.d. nor exchangeable — they conflict, they are dated, the process changes — so
retained sufficient statistics would silently average across a changepoint. **The correct enabler of coherent
incremental refitting for us is not a sufficient-statistics trick but a projective (marginally consistent)
prior, which is what §6.2 supplies.** That is the most important cross-area conclusion in this review. The
changepoint papers all index time by *observations of a time series* with many time points per segment; our
per-segment evidence is far thinner, so the changepoint count will be prior-dominated and must be reported as
such.

### 5.8 Deleu, T., Góis, A., Emezue, C., Rankawat, M., Lacoste-Julien, S., Bauer, S. & Bengio, Y. "Bayesian structure learning with generative flow networks." *UAI 2022*, PMLR 180, 518–528. <https://proceedings.mlr.press/v180/deleu22a.html>. arXiv:[2202.13903](https://arxiv.org/abs/2202.13903)

DAG-GFlowNet amortises the posterior over DAGs by learning a policy that builds a graph **edge by edge**,
with flow matching making terminal-state probability proportional to score.

**Borrow:** amortisation speaks to our refit-per-document pain, and edge-by-edge construction with an
acyclicity action mask is a clean way to enforce the constraint inside the generative process rather than by
rejection.

**Breaks:** poor fit, and I would not pursue it. It needs a cheap score per candidate graph — we would be
calling a linear-extension counter inside the reward, which is the expensive thing. It has no mechanism for a
**growing node set**, a first-class requirement for us, and retraining as *n* grows defeats the amortisation.
Nothing for changepoints. Revisit only if *n* stabilises and we have a cheap surrogate score.

---

## 6. Partial order learning from linear extensions and sequence observations

**This is where our problem has actually been solved, in another domain, with a proper likelihood.** It is
also the area with the sharpest negative result: every model here infers a poset or a DAG, and a rework loop
is a cycle, so none of it can represent our measured hard case.

### 6.1 Nicholls, G. K., Lee, J. E., Karn, N., Johnson, D., Huang, R. & Muir-Watt, A. "Bayesian inference for partial orders from random linear extensions: power relations from 12th Century Royal Acta." *Annals of Applied Statistics* 19(2), 2025, 1663–1690. DOI [10.1214/24-AOAS2002](https://doi.org/10.1214/24-AOAS2002). arXiv:[2212.05524](https://arxiv.org/abs/2212.05524)

**The best structural analogue in the review.** Witness lists in medieval Royal Acta are *dated total orders*
of bishops, constrained by an unobserved social hierarchy the authors decline to assume is a total order.
They build an HMM whose hidden state is an **evolving poset** and whose emissions are **random total orders
respecting the poset in force at the time of observation**, with a "queue-jumping" noise process for
violations. The latent-variable prior over posets is **marginally consistent**; a parameter controls poset
depth; actor covariates inform position. They fit it, estimate posets, detect change over time, and
explicitly **reject** bucket-order and vertex-series-parallel restrictions in favour of general posets, with a
time-series Plackett–Luce baseline for comparison. Software is public.

**Borrow:** almost the entire architecture; treat it as our reference implementation.
1. **The likelihood we need.** p(observed total order | poset) = 1/|L(P)| in the noiseless case, generalised
   by queue-jumping. A proper, normalised observation model for case traces. Our traces *are* their witness
   lists: a total order over the subset of actors that this observation saw.
2. **The latent-position prior, which dissolves our transitivity problem.** Actors get positions in R^K and
   i ≺ j iff j dominates i in all K coordinates. Transitivity and acyclicity are then **automatic**, MCMC
   moves are on continuous latent positions rather than the discrete poset lattice, and no constraint repair
   is ever needed. This is strictly better than our "pairwise Bernoulli with a transitivity constraint"
   candidate and than any sampler fix in §5.
3. **K as an interpretable complexity dial.** K controls poset depth/dimension, i.e. how much genuine
   parallelism is permitted. For a project whose deliverable is a defensible complexity metric, having the
   latent dimension of the precedence structure as an estimated parameter is a substantive result.
4. **Covariates on position.** Step attributes (owning agency, fee vs inspection vs review) inform where a
   step sits, which is how we get traction on the majority of pairs with no direct evidence.
5. **The HMM over time is a better version-changepoint model than anything in §5**, because it is already
   defined on posets rather than regression segments.
6. **The negative result matters.** They tested bucket orders and VSP and rejected both. Before adopting a
   tractable subclass (§6.3) we must run the same comparison rather than assume it.

**Breaks:** three gaps, the first fundamental.
1. **A poset cannot represent a rework loop.** Their hidden state is a partial order; ours needs cycles back
   to earlier steps. Since rework is our measured hard part (recall 0.00–0.25, versus order agreement already
   0.90–0.99), this literature helps most with what we have already solved and not at all with what we have
   not. Say so plainly in any write-up.
2. **No document-assertion likelihood.** They have one evidence type. Our pairwise precedence claims in prose
   and numbered lists of unknown fidelity need a second observation model (§6.9).
3. **The actor set is fixed and known** — bishops are enumerated in advance. §6.2 fixes exactly this.

Inherit their computational constraint too: *n* is modest (tens of actors), limited by the 1/|L(P)|
normaliser.

**UNVERIFIED, and a correction to the brief:** I could not confirm any paper titled "Partial order models for
episcopal social status" by Nicholls & Muir Watt, nor any "Nicholls, Muir Watt, Dean" combination — neither
appears in Crossref, OpenAlex or arXiv. Muir-Watt is confirmed on §6.1 and on the 2012 randomized-acceptance
preprint (§6.10) but **not** on the 2023–2026 papers, contrary to the brief. The correct citations for this
line are §6.1–§6.4.

### 6.2 Jiang, C. & Nicholls, G. K. "Non-parametric Bayesian inference for partial orders with ties from rank data observed with Mallows noise." *Computational Statistics & Data Analysis* 224, 2026, 108445. DOI [10.1016/j.csda.2026.108445](https://doi.org/10.1016/j.csda.2026.108445). arXiv:[2408.14661](https://arxiv.org/abs/2408.14661)

Extends §6.1 with a prior over posets **with ties**, clustering tied actors via a **Poisson–Dirichlet
process**; the family is **projective**; a **Mallows observation model** for posets is proposed with a
**recursive likelihood evaluation algorithm**.

**Borrow:** closes three of our four remaining gaps, and should be read immediately after §6.1.
1. **A Poisson–Dirichlet / CRP-style nonparametric prior over the element set** — our "unknown and growing
   number of steps" requirement, already worked out in the poset setting. Ties additionally give us something
   we need independently: genuinely simultaneous steps, and near-duplicate steps described differently by two
   sources.
2. **Projectivity is the licence for incremental refitting.** A projective family means the marginal law over
   the elements seen so far does not change when new elements are added — precisely the coherence property
   that makes "refit as each document arrives" a well-defined Bayesian operation rather than an
   approximation, superseding the sufficient-statistics approach of §5.7.
3. **The recursive likelihood evaluation algorithm** is the concrete artefact we need for |L(P)|-type
   quantities. Implement this first.
4. **Mallows noise on a poset** is the right way to use Mallows for us: a per-source *noise model* layered on
   a genuine partial order, with dispersion interpretable as **source reliability**. A numbered web-page list
   becomes a high-dispersion observation; a statute's explicit "after X, then Y" becomes low-dispersion. The
   cleanest available answer to conflicting sources.

**Breaks:** still a poset, so still no loops. Still one evidence channel. The recursion's cost is controlled
by poset width, so it is exact-but-exponential in the wrong regime — narrow deep posets are cheap, wide
shallow ones are not, and a workflow with many parallel independent steps is the expensive case. No
changepoints in this paper (that is §6.1's HMM).

### 6.3 Jiang, C., Nicholls, G. K. & Lee, J. E. "Bayesian inference for vertex-series-parallel partial orders." *UAI 2023*, PMLR 216, 995–1004. <https://proceedings.mlr.press/v216/jiang23b.html>. arXiv:[2306.15827](https://arxiv.org/abs/2306.15827)

Restricts the latent poset to the **vertex-series-parallel** class — posets built recursively by series and
parallel composition — and exploits that decomposition for inference.

**Borrow:** the main tractability escape hatch, and worth evaluating early. For a VSP poset the
series-parallel decomposition tree gives |L(P)| by closed-form recursion (multinomial coefficients at
parallel nodes, products at series nodes), so the #P-complete counting wall simply does not apply. And VSP is
arguably a *better inductive bias for an administrative workflow* than a general poset: permitting really is
built from sequential stages containing parallel independent sub-tasks, which is the definition of
series-parallel composition. The decomposition tree also reads directly as the decision-tree-of-a-rule
artefact the project wants, and its depth and branching are natural complexity metrics — which is our
instrument. A rare case where the convenient model class is also the substantively right one.

**Breaks:** VSP excludes the "N" poset (a≺c, b≺c, b≺d with a,d and a,b and c,d incomparable) and everything
containing it as an induced subposet. Real workflows contain N-patterns whenever one prerequisite is shared by
two downstream steps and the other is not — which happens constantly with shared fee or intake steps. **And
§6.1 tested VSP on real data and rejected it.** So: implement VSP as a fast baseline and a proposal
distribution, test it against the general poset by predictive comparison as §6.1 did, and be prepared for it
to lose. Do not adopt it on tractability grounds alone.

### 6.4 Li, D., Nicholls, G. K., Lee, J. E. & Jiang, C. "Hierarchical partial-order models for ranking." arXiv:[2606.25062](https://arxiv.org/abs/2606.25062), 23 June 2026. **Preprint only — no peer-reviewed venue.**

Introduces **hierarchical partial order** models: a hierarchy of latent posets so grouped data share
information while preserving partial-order structure. Shows **Plackett–Luce and its hierarchical variants are
special cases**. Adds HCPO, a hierarchical clustering extension for unknown group labels. Evaluated on
synthetic data, pairwise acoustic preferences, **and LLM agent traces**.

**Borrow:** this is the "different jurisdictions run different variants of the same process" paper. (i) The
hierarchy of latent posets is our multi-jurisdiction structure: one global process poset, per-jurisdiction
deviations, principled partial pooling — which solves the problem that each jurisdiction alone has too little
evidence to identify its own poset. (ii) HCPO's unsupervised clustering handles not knowing which sources
describe the same variant, a cleaner mechanism for that ambiguity than §5.7's changepoints. (iii) The
PL-as-special-case result settles the ranking-model question analytically in our favour: adopting a poset
model loses nothing, because the ranking model is nested and the restriction is testable. (iv) Validating on
agent traces means the trace-shaped regime is already in scope.

**Breaks:** three-month-old unrefereed preprint with no independent replication — do not put it on the
critical path before reading the code. The hierarchy is over *groups*, not *time*, so it does not subsume
§6.1's temporal HMM; we would need both, and combining them is unproven work. Poset, so no loops. And
hierarchical poset models are hungrier for data than §6.1, so with few traces per jurisdiction the per-group
posets will be prior-dominated.

### 6.5 Mannila, H. & Meek, C. "Global partial orders from sequential data." *KDD 2000*, 161–168. DOI [10.1145/347090.347122](https://doi.org/10.1145/347090.347122) — with Gionis, A., Kujala, T. & Mannila, H. "Fragments of order." *KDD 2003*, 129–136. DOI [10.1145/956750.956768](https://doi.org/10.1145/956750.956768)

Mannila & Meek fit a **global partial order** (mixtures of series-parallel posets) to a collection of observed
sequences, with a likelihood and a bottom-up fitting algorithm. Gionis et al. take many small, partial,
mutually inconsistent order fragments and find the global structure they best support, characterising when
fragments are combinable.

**Borrow:** Mannila & Meek is the earliest and still cleanest statement of *our exact problem shape* — many
observed sequences, one latent global partial order, a genuine likelihood rather than a heuristic — and its
series-parallel restriction independently corroborates the §6.3 recommendation from a different literature.
Gionis et al. is the **document-assertion** paper: local precedence claims, incomplete and conflicting. Its
combinability analysis is the formal core of our source-conflict problem, and running a fragment-consistency
check over our corpus *before* fitting anything would tell us immediately whether conflicts are localised (a
few bad sources) or pervasive (genuine version drift) — which changes the model we should build.

**Breaks:** Mannila & Meek is frequentist EM with no posterior, so no uncertainty on the order, which is the
whole point of our unobserved-pair channel; fixed known event alphabet; no loops; no modern implementation.
Gionis et al. is combinatorial optimisation with no noise model, so a single erroneous fragment can drive the
answer. Use both as diagnostics and baselines, not foundations.

### 6.6 Beerenwinkel, N., Eriksson, N. & Sturmfels, B. "Conjunctive Bayesian networks." *Bernoulli* 13(4), 2007, 893–909. DOI [10.3150/07-BEJ6133](https://doi.org/10.3150/07-BEJ6133). arXiv:[math/0608417](https://arxiv.org/abs/math/0608417)

The mathematical foundation of the CBN family. A poset of events induces the **distributive lattice of its
order ideals (down-sets)**; the CBN is a graphical model on that lattice, and each observation is a down-set —
a set of events closed under the precedence relation. Gives the algebraic geometry and closed-form ML.

**Borrow:** a second likelihood, for a different and very common observation type. **A case trace's
completed-steps-so-far must be a down-set of the latent poset.** An applicant cannot have done plan review
without the prerequisite, so an observation that is *not* a down-set is either evidence against the poset or
evidence of noise — a sharp, cheap, well-founded constraint that uses partial traces without needing their
internal ordering at all. It is complementary to §6.1: that uses the *order* within a trace, this uses the
*membership set*, and a trace gives both. Also: **CBN is conjunctive — an event occurs only when ALL
predecessors have — which is exactly AND-join semantics**, the correct default for permitting and more
informative than generic DAG semantics.

**Breaks:** fixed known event set. The likelihood requires summing over order ideals, which is 2^n in the
worst case — **the same counting wall as linear extensions in a different guise**. The conjunctive assumption
is too strong alone: our documents assert soft precedence, and OR-joins and optional steps exist (§6.8
relaxes this). And the set-of-events representation is precisely what forbids rework — a repeated step cannot
be represented in a set at all — so **no member of this family can ever address our hard case.**

### 6.7 Gerstung, M., Baudis, M., Moch, H. & Beerenwinkel, N. "Quantifying cancer progression with conjunctive Bayesian networks." *Bioinformatics* 25(21), 2009, 2809–2815. DOI [10.1093/bioinformatics/btp505](https://doi.org/10.1093/bioinformatics/btp505) — sampler: Sakoparnig, T. & Beerenwinkel, N. "Efficient sampling for Bayesian inference of conjunctive Bayesian networks." *Bioinformatics* 28(18), 2012, 2318–2324. DOI [10.1093/bioinformatics/bts433](https://doi.org/10.1093/bioinformatics/bts433) — waiting times: Gerstung, M. & Beerenwinkel, N. "Waiting time models of cancer progression." *Mathematical Population Studies* 17(3), 2010, 115–135. DOI [10.1080/08898480.2010.490994](https://doi.org/10.1080/08898480.2010.490994)

H-CBN adds an **error model** (ε) so observations may violate the poset, an EM/annealing scheme to learn the
poset, and continuous-time **waiting times** per event so the model predicts timing as well as order.
Sakoparnig & Beerenwinkel supply a proper MCMC sampler giving a posterior over posets.

**Borrow:** the most practically useful cluster in the cancer family, for four reasons.
1. **The ε error model is the template for "this trace violates the poset".** Do not treat a violating trace
   as impossible; assign it probability ε and *learn* ε. This is what keeps the sampler from collapsing when
   one applicant genuinely skipped a step.
2. **Waiting times.** Our traces carry dates, not just order — strictly richer than either §6.1 (order only)
   or §6.6 (set only) can use. The continuous-time formulation lets elapsed duration be evidence about
   precedence: two steps 90 days apart in every trace are more likely genuinely ordered than two that swap
   within a day. **This is probably our largest unexploited source of signal**, and it yields a directly
   policy-relevant output (expected time-to-completion under the inferred poset).
3. **Sakoparnig & Beerenwinkel's sampler** is the CBN analogue of the Nicholls sampler and a useful
   cross-check on proposal design.
4. The pathway-level companion (Gerstung et al., *PLoS ONE* 6(11), 2011, e27136, DOI
   [10.1371/journal.pone.0027136](https://doi.org/10.1371/journal.pone.0027136)) is a **coarsening
   argument**: aggregating events to a higher abstraction buys identifiability when per-event data is thin.
   Directly applicable — fit the poset over step *categories* (intake / fee / review / inspection / issuance)
   before individual steps, and we will likely find the categorical poset identified where the fine-grained
   one is not.

**Breaks:** fixed known event set; conjunctive throughout; the order-ideal sum wall. And **no loops** — a
mutation is irreversible and occurs once, which is baked into the waiting-time construction, so the timing
machinery we most want to borrow is exactly the machinery that assumes no repetition. Adapting it to
recurrent events is research, not a port.

### 6.8 Schill, R., Solbrig, S., Wettig, T. & Spang, R. "Modelling cancer progression using Mutual Hazard Networks." *Bioinformatics* 36(1), 2020, 241–249. DOI [10.1093/bioinformatics/btz513](https://doi.org/10.1093/bioinformatics/btz513)

Replaces the hard conjunctive constraint with a **continuous-time Markov chain in which every event
multiplicatively promotes or inhibits every other event's hazard rate**, so precedence becomes a matter of
degree; it can also express mutual exclusivity.

**Borrow:** the right fix for our biggest modelling mismatch. Our documents assert *soft* precedence — "after
the fee is paid, plan review begins" is usually but not always true, and a numbered list is a weak hint.
MHN represents "usually after" natively, with an estimable magnitude, instead of forcing every pair into
{before, after, incomparable}; and an unobserved pair gets an interaction shrunk toward zero rather than a
hard "incomparable" claim we cannot defend. Second, and more important: **because MHN is a CTMC over states,
an event can in principle recur, so this is the one model in the entire progression family not structurally
incapable of representing rework** — the most promising lead in §6 for our stated hard problem.

**Breaks:** n² interaction parameters from cross-sectional data makes it data-hungry and
regularisation-dependent; at our evidence density the interaction matrix will be largely prior-driven. The
output is a hazard matrix, **not a poset**, so it does not directly produce the decision-tree artefact and
extracting one is an extra lossy step. The state space is 2^n, so exact likelihood evaluation is worse than
the poset models and the published work relies on tensor/low-rank tricks. Fixed event set, no nonparametric
extension, no changepoints. Read it as the design answer for soft precedence and recurrence; do not expect to
adopt it wholesale.

Adjacent and worth one line, for a feature we currently cannot express at all: Constantinescu, S., Szczurek,
E., Mohammadi, P., Rahnenführer, J. & Beerenwinkel, N. "TiMEx: a waiting time model for mutually exclusive
cancer alterations." *Bioinformatics* 32(7), 2016, 968–975. DOI
[10.1093/bioinformatics/btv400](https://doi.org/10.1093/bioinformatics/btv400). **Borrow:** mutual
exclusivity is real in our domain as **alternative compliance pathways** — prescriptive *or* performance
path; inspection waived *or* performed. These are not ordering relations, and forcing them into a poset will
produce incoherent precedence estimates and may well contribute to our low loop recall by mistaking
alternation for repetition. TiMEx distinguishes "unordered" from "alternatives", a distinction that matters a
great deal for a simplify-with-least-harm deliverable, since an alternative path is exactly the thing you
must not delete. **Breaks:** narrow — it detects one pattern and learns no order; use it as a pre-processing
detector that partitions step pairs into ordered / parallel / mutually-exclusive before poset fitting.

### 6.9 Event-based progression models, and ranking models

- Fonteijn, H. M., Modat, M., Clarkson, M. J., Barnes, J., Lehmann, M., Hobbs, N. Z., Scahill, R. I., Tabrizi, S. J., Ourselin, S., Fox, N. C. & Alexander, D. C. "An event-based model for disease progression and its application in familial Alzheimer's disease and Huntington's disease." *NeuroImage* 60(3), 2012, 1880–1889. DOI [10.1016/j.neuroimage.2012.01.062](https://doi.org/10.1016/j.neuroimage.2012.01.062)
- Young, A. L., Marinescu, R. V., Oxtoby, N. P., *et al.* "Uncovering the heterogeneity and temporal complexity of neurodegenerative diseases with Subtype and Stage Inference." *Nature Communications* 9, 2018, 4273. DOI [10.1038/s41467-018-05892-0](https://doi.org/10.1038/s41467-018-05892-0) (SuStaIn; 30 authors)
- Mallows, C. L. "Non-null ranking models. I." *Biometrika* 44(1–2), 1957, 114–130. DOI [10.1093/biomet/44.1-2.114](https://doi.org/10.1093/biomet/44.1-2.114)
- Fligner, M. A. & Verducci, J. S. "Distance based ranking models." *JRSS-B* 48(3), 1986, 359–369. DOI [10.1111/j.2517-6161.1986.tb01420.x](https://doi.org/10.1111/j.2517-6161.1986.tb01420.x)
- Vitelli, V., Sørensen, Ø., Crispino, M., Frigessi, A. & Arjas, E. "Probabilistic preference learning with the Mallows rank model." *JMLR* 18(158), 2018, 1–49. <https://jmlr.org/papers/v18/15-481.html>
- Lu, T. & Boutilier, C. "Effective sampling and learning for Mallows models with pairwise-preference data." *JMLR* 15(117), 2014, 3963–4009. <https://www.jmlr.org/papers/v15/lu14a.html>
- Meilă, M. & Chen, H. "Dirichlet process mixtures of generalized Mallows models." *UAI 2010*. arXiv:[1203.3496](https://arxiv.org/abs/1203.3496)
- Fagin, R., Kumar, R., Mahdian, M., Sivakumar, D. & Vee, E. "Comparing partial rankings." *SIAM J. Discrete Math.* 20(3), 2006, 628–648. DOI [10.1137/05063088X](https://doi.org/10.1137/05063088X); conference version *PODS 2004*, 47–58, DOI [10.1145/1055558.1055568](https://doi.org/10.1145/1055558.1055568)

Fonteijn et al.'s EBM infers the **ordering** of N events from purely cross-sectional data by MCMC over
permutations, with each subject's position along the sequence a latent stage. SuStaIn extends it to a mixture
of C distinct sequences (subtypes), jointly inferring subtype count, each subtype's ordering, and each
subject's subtype-and-stage. Mallows is the exponential-family model on permutations concentrating around one
consensus total order; Fligner–Verducci generalise the distance; Vitelli et al. give full Bayesian inference
including **incomplete and partial rankings by data augmentation**; Lu & Boutilier handle **arbitrary
pairwise preferences** as observations (#P-hard in general) via the AMP sampler; Meilă & Chen add a
**Dirichlet-process** mixture for an unbounded number of clusters; Fagin et al. give the metric theory for
rankings with ties.

**Borrow:** these are the right **noise and evidence models**, once attached to a poset rather than used in
place of one.
1. **Lu & Boutilier is the best available machinery for document-asserted order.** Their entire contribution
   is tractable inference from a pairwise preference set, which is exactly what a document gives us. Read
   alongside §6.2.
2. **Vitelli et al.'s data augmentation for incomplete rankings** is the mechanism for a trace covering only
   a subset of steps — impute the unobserved part of the linear extension inside the sampler. Mature
   software (`BayesMallows` on CRAN).
3. **Mallows dispersion as per-source reliability**, already proven inside a poset model by §6.2.
4. From the EBM, the idea of **sampling the order and marginalising each observation's latent stage**: our
   traces are snapshots of applicants at different points in an unknown process, exactly their
   subject-at-unknown-stage setup, and the scheme is simple enough to give us a strong baseline in days.
   Their positional-variance diagnostic is a ready-made interpretable presentation of order uncertainty.
5. From SuStaIn, the **subtype-plus-stage factorisation** for jurisdictional variants, plus — the part I
   would insist on importing — their **identifiability discipline**. SuStaIn needs many subjects per subtype
   to separate variants from noise, and the literature is candid about it. We will have very few traces per
   jurisdiction, so we should expect to support far fewer variants than we intuitively believe exist, and
   should run their style of cross-validated subtype-count selection rather than asserting a variant per
   jurisdiction.
6. **Fagin et al.** supply the metrics for evaluating output against gold when both have ties and
   incomparabilities — which our current "order agreement" number almost certainly does not handle
   correctly. Worth auditing our metric against their definitions.

**Breaks — and this is the central point, stated bluntly. A ranking model is a poor substitute for a partial
order and must not be our latent representation.** Mallows, Plackett–Luce, the EBM and SuStaIn all posit a
**total** order plus noise. They therefore cannot distinguish genuine incomparability from noisy tie-breaking:
two truly parallel steps and two ordered steps frequently observed out of sequence get the same
representation, differing only in dispersion. Since the deliverable is a complexity metric whose meaning
depends on how much of the process is genuinely parallel, that conflation is disqualifying — it destroys the
quantity we are measuring. The evidence is not speculative: §6.1 built a poset model because the total-order
assumption was wrong for their data, and §6.4 **proves** Plackett–Luce is a strict special case of the
hierarchical partial-order model, with both reporting poset models winning on real data. Bucket orders and
ties narrow but do not close the gap, since a bucket order still forces a total order *on the buckets*. And a
specific trap worth naming: **given that our order agreement is already 0.90–0.99, a permutation model will
look deceptively good on our current evaluation while being unable to represent what we need.** Conclusion:
adopt Mallows as the noise layer on top of a poset, as §6.2 does, and never as the latent structure.

Also verified and useful as an algorithmic companion for detecting whether traces fall into distinct variants
at all: Ukkonen, A. "Clustering algorithms for chains." *JMLR* 12(38), 2011, 1389–1423.
<https://www.jmlr.org/papers/v12/ukkonen11a.html>. **UNVERIFIED — a correction to the brief:** I could not
confirm any publication titled "Ukkonen, *Mining local orderings*" in Crossref, OpenAlex or arXiv; the
brief's reference should be replaced with this or with Ukkonen, A., Fortelius, M. & Mannila, H. "Finding
partial orders from unordered 0-1 data." *KDD 2005*, 285–293, DOI
[10.1145/1081870.1081904](https://doi.org/10.1145/1081870.1081904) — which is itself directly relevant, since
it recovers a partial order from observations recording only *which* elements co-occur, i.e. what we face when
a document lists the required steps and says nothing about sequence.

### 6.10 The computational wall: counting and sampling linear extensions

- Brightwell, G. & Winkler, P. "Counting linear extensions." *Order* 8(3), 1991, 225–242. DOI [10.1007/BF00383444](https://doi.org/10.1007/BF00383444); conference version "Counting linear extensions is #P-complete", *STOC 1991*, 175–181, DOI [10.1145/103418.103441](https://doi.org/10.1145/103418.103441)
- Karzanov, A. & Khachiyan, L. "On the conductance of order Markov chains." *Order* 8(1), 1991, 7–15. DOI [10.1007/BF00385809](https://doi.org/10.1007/BF00385809)
- Bubley, R. & Dyer, M. "Faster random generation of linear extensions." *Discrete Mathematics* 201(1–3), 1999, 81–88. DOI [10.1016/S0012-365X(98)00333-1](https://doi.org/10.1016/S0012-365X(98)00333-1)
- Nicholls, G. K., Fox, C. & Muir Watt, A. "Coupled MCMC with a randomized acceptance probability." arXiv:[1205.6857](https://arxiv.org/abs/1205.6857), 2012. **Preprint only** — no journal reference or DOI recorded.

Brightwell & Winkler prove **counting the linear extensions of a poset is #P-complete**. Karzanov &
Khachiyan bound the conductance of the natural Markov chain on linear extensions, establishing rapid mixing;
Bubley & Dyer improve this to an O(n³ log n)-type bound, giving a practical **FPRAS** for the count and a
near-uniform sampler.

**Borrow:** the honest statement of our computational situation plus the four escapes, all of which should go
in the design doc.
1. **|L(P)| is #P-complete, so there is no exact polynomial normaliser.** Any design that assumes we can
   evaluate the linear-extension likelihood exactly at scale is wrong, and this is the citation that settles
   it.
2. **Bubley–Dyer gives a rapidly-mixing near-uniform sampler**, so |L(P)| is *approximable*, and an unbiased
   estimate suffices: drop it into **pseudo-marginal / randomized-acceptance MCMC** and the chain still
   targets the right posterior. The Nicholls–Fox–Muir Watt preprint is the methodological bridge, and its
   coming from the same group as §6.1 is not a coincidence — it is how they made that model run.
3. **Exact DP over down-sets** (§5.4, §5.6, and §6.2's recursion) is exponential in poset **width**, not in
   *n*. For narrow deep posets — what a permitting workflow with a few parallel branches actually is — this is
   exactly evaluable. **Width, not step count, is the quantity to watch and to constrain a priori.**
4. **VSP posets (§6.3) have closed-form |L(P)|**, sidestepping the wall at the cost of excluding N-shaped
   posets.

**Breaks:** nothing — these are theorems. Two practical caveats: the FPRAS constants are large enough that
naive use inside an inner MCMC loop will be slow; and pseudo-marginal MCMC pays for noisy likelihood
estimates with worse mixing, which interacts badly with already-difficult poset proposals. Realistic plan:
route 3 or 4 as the primary evaluator, route 2 as the fallback for wide posets.

---

## 7. Probabilistic and Bayesian process mining

**The headline judgement, before the entries: process mining does not survive the loss of the log, and the
failure is definitional rather than gradual.** Every inference object in this field factorises through
p(log | model), where a log is a multiset of *complete traces of recorded events*. Discovery algorithms do not
consume documents and degrade — they are *undefined* without a directly-follows graph, which is a count over
event adjacencies. Conformance measures, the stochastic ones included, are two-argument distances requiring an
empirical stochastic language on one side; with three anecdotes that language is a three-atom spike and the
distance is sampling noise. **Nobody in this field has ever computed a posterior over process structures.**

Three things do transfer and are worth real effort: the GDT_SPN as a ready-made non-Markovian timing
likelihood (§7.2); single-trace inference in the event-log-repair line, which runs in our direction (§7.4);
and queueing inference, the only sub-area that was *born* without a log and the only one that speaks to our
measured failure (§7.16–§7.18).

### 7.1 Ajmone Marsan, M., Conte, G. & Balbo, G. "A class of generalized stochastic Petri nets for the performance evaluation of multiprocessor systems." *ACM Transactions on Computer Systems*, 1984. DOI [10.1145/190.191](https://doi.org/10.1145/190.191) — companion book *Modelling with Generalized Stochastic Petri Nets* (Ajmone Marsan, Balbo, Conte, Donatelli, Franceschinis), Wiley. **UNVERIFIED**: the book's year (commonly 1995), publisher ISBN and pagination; confirmed only via the *SIGMETRICS Performance Evaluation Review* notice, DOI [10.1145/288197.581193](https://doi.org/10.1145/288197.581193).

GSPNs partition transitions into immediate (zero delay, weight-resolved conflict) and timed (exponential
delay), giving a net whose reachability graph is a CTMC.

**Borrow:** copy the structural separation verbatim — a **weight** parameter per branch governs which path a
case takes, a **duration** parameter governs how long it takes, and they are inferred from different
evidence. Document evidence ("applicants must then do X") is evidence about *weights and structure*; user
reports and traces are evidence about *durations*. Keeping these in separate parameter blocks with separate
likelihood terms is the cleanest piece of architecture in this area. Also borrow the immediate-transition
device for zero-duration bookkeeping steps (a filing "deemed complete") so they do not contaminate duration
estimation.

**Breaks:** exponential delays are wrong for us in a way that matters — an exponential has its mode at zero
and CV = 1, so it cannot represent "review takes 4–6 weeks, essentially never 2 days". Our LogNormal choice is
right and puts us outside the Markovian analysis machinery immediately: no CTMC, no closed-form steady state.
GSPN analysis is also a *forward* tool (given net and rates, compute performance), not an inference tool, and
the net structure is assumed known, which is our hardest unknown.

### 7.2 Rogge-Solti, A. & Weske, M. "Prediction of Remaining Service Execution Time Using Stochastic Petri Nets with Arbitrary Firing Delays." *ICSOC 2013*, 389–403. DOI [10.1007/978-3-642-45005-1_27](https://doi.org/10.1007/978-3-642-45005-1_27) — journal version "Prediction of business process durations using non-Markovian stochastic Petri nets." *Information Systems* 54, 2015, 1–14. DOI [10.1016/j.is.2015.04.004](https://doi.org/10.1016/j.is.2015.04.004)

Defines GDT_SPN — a stochastic Petri net whose transitions carry *arbitrary* (generally non-exponential)
duration distributions — and predicts remaining cycle time by conditioning on the elapsed observed prefix.

**Borrow:** the most directly reusable single work in the area. (a) The GDT_SPN **is** our timing likelihood,
already formalised, already non-Markovian, already fitted with LogNormal marginals per transition. (b) The
**conditioning-on-a-prefix** machinery is what our occasional case traces need: an applicant six weeks in who
has cleared 3 of 7 steps is a truncated observation, and this gives the correct likelihood contribution rather
than discarding it or treating it as complete. (c) The paper's honest finding — that prediction quality is
governed by how well the *duration distributions* are estimated, not by net topology — matches our pilot
exactly (order agreement 0.90–0.99 and easy; duration off 1.5× and hard) and is a citation for de-prioritising
further structural work in favour of timing.

**Breaks:** durations are fitted from a log by per-transition MLE on observed start/complete pairs. We have
neither, so only the generative half transfers. More seriously, **a GDT_SPN transition duration is a single
random variable — there is no touch/queue decomposition inside it.** Fit this to elapsed times and you get one
blended LogNormal that silently absorbs the queue, after which no counterfactual about staffing, batching or
backlog is answerable. That blending is arguably the formal statement of our 1.5× bug: whoever fits a
transition to a document's "a few weeks" fits the *service* distribution and then uses it as the *sojourn*
distribution. Every transition in our model must split into two stacked random variables; this literature does
not.

### 7.3 Rogge-Solti, A., van der Aalst, W. M. P. & Weske, M. "Discovering Stochastic Petri Nets with Arbitrary Delay Distributions from Event Logs." *BPM Workshops 2013*, LNBIP. DOI [10.1007/978-3-319-06257-0_2](https://doi.org/10.1007/978-3-319-06257-0_2)

Given a known control-flow net plus a log, estimates per-transition delay distributions and branching weights,
handling the case where a transition's duration is not directly observable because only some events are
recorded.

**Borrow:** the treatment of **partially observable transition durations**. When you see only event *k* and
event *k+3*, the observed gap is a convolution over the intervening transitions, and they set up the
estimation accordingly. That convolution-over-unobserved-intermediate-steps structure is precisely our
situation for every step a document does not disclose, and it is the template for the likelihood term linking
"submitted in March, approved in July" to a latent chain of five steps.

**Breaks:** the net is an input, not an unknown. Estimation is frequentist point estimation, so at our sample
sizes it produces degenerate fits (a LogNormal MLE from two observations). And the identifiability problem it
papers over is fatal at our *n*: **a convolution of five LogNormals observed once does not identify five
parameter pairs.** They can ignore this with thousands of traces; we cannot, and the answer must be informative
priors plus cross-step parameter sharing (a hierarchical prior over "discretionary review" steps), which is
not in the paper.

### 7.4 Rogge-Solti, A., Mans, R. S., van der Aalst, W. M. P. & Weske, M. "Improving Documentation by Repairing Event Logs." *PoEM 2013*, LNBIP. DOI [10.1007/978-3-642-41641-5_10](https://doi.org/10.1007/978-3-642-41641-5_10) — companion "Repairing Event Logs Using Timed Process Models." *OTM 2013 Workshops*, LNCS. DOI [10.1007/978-3-642-41033-8_89](https://doi.org/10.1007/978-3-642-41033-8_89)

Takes a timed process model, aligns an incomplete trace to it, and **reconstructs the missing events and their
most likely timestamps**, using the model's timing distributions to place the inserted events. Motivated
explicitly by activities that were performed but never documented.

**Borrow:** the one work in process mining whose inferential *direction* is ours, and it should be a primary
citation. The generative move — a structural prior plus a timing model jointly imply a posterior over
unobserved events — is our "documents disclose steps selectively" problem restated. Two concrete borrows: (a)
**inserted-event posteriors as our missing-step mechanism** — an undisclosed step is formally identical to a
missing event, and the timing model is what identifies it, i.e. **a long elapsed time is positive evidence
for an unmentioned step**; (b) converting the timed net into a graphical model over timestamps so timestamp
inference is ordinary belief propagation — a tractability trick worth copying before reaching for generic
MCMC.

**Breaks:** it repairs *one trace against a known, complete, correct model*; the only unknown is which events
are missing. We have the opposite asymmetry. And their "missing" is missing-at-random-ish (a logging failure);
ours is **missing by design** — a form page omits the rework loop because disclosing it is embarrassing, a fee
study omits the queue because the queue is not billable. That is informative, non-ignorable, *source-type
dependent* missingness, which their model has no slot for and which for us is the whole point: **the
missingness mechanism is the interesting parameter, not a nuisance.**

### 7.5 Leemans, S. J. J., Maggi, F. M. & Montali, M. "Enjoy the silence: Analysis of stochastic Petri nets with silent transitions." *Information Systems*, 2024. DOI [10.1016/j.is.2024.102383](https://doi.org/10.1016/j.is.2024.102383)

Handles nets containing *silent* (unlabelled, unobservable) transitions, so the net's stochastic language must
be obtained by marginalising over invisible firings — including silent loops, which can make the
marginalisation non-terminating.

**Borrow:** the formal home of our **visibility class**. A step appearing in no document is a silent
transition, and this paper is about exactly the operation we need: computing the distribution over
*observable* traces induced by a net containing unobservable steps. That marginalisation is our forward model
— p(what a document could disclose | true workflow). Their treatment of silent *loops* is unexpectedly
on-point given our rework problem: an unmentioned rework cycle is a silent loop, and they show why such loops
are the hard case and how to handle the infinite sums.

**Breaks:** silence here is a fixed property of the net assigned by the modeller (a transition is labelled τ or
not). For us visibility is a *latent, source-dependent* variable — a step is visible in the fee study,
invisible on the FAQ, half-visible in a staff report — so our observation model is a per-source visibility
channel, not a global labelling, which is a strictly larger model. And the net is given; nothing here infers
it.

### 7.6 Leemans, S. J. J., Fahland, D. & van der Aalst, W. M. P. — the Inductive Miner and process trees

- "Discovering block-structured process models from event logs — a constructive approach." *Petri Nets 2013*, LNCS, 311–329. DOI [10.1007/978-3-642-38697-8_17](https://doi.org/10.1007/978-3-642-38697-8_17)
- "…from event logs containing infrequent behaviour." *BPM Workshops 2013*, LNBIP, 66–78. DOI [10.1007/978-3-319-06257-0_6](https://doi.org/10.1007/978-3-319-06257-0_6)
- "…from incomplete event logs." *Petri Nets 2014*, LNCS, 91–110. DOI [10.1007/978-3-319-07734-5_6](https://doi.org/10.1007/978-3-319-07734-5_6)
- Journal synthesis: "Scalable process discovery and conformance checking." *Software & Systems Modeling* 17(2), 2018, 599–631. DOI [10.1007/s10270-016-0545-x](https://doi.org/10.1007/s10270-016-0545-x)

Discovers a **block-structured process tree** using explicit sequence, parallel, exclusive-choice and **LOOP**
operators, with guaranteed soundness; IMf filters infrequent directly-follows edges, and IMc is the
incompleteness-tolerant variant that reasons about which "never follows" entries are genuine constraints
versus sampling gaps.

**Borrow:** two things, and the first is the most important single item in §7 for our hard problem. (i) **This
is the only cited work whose representation contains a loop operator by construction.** A process tree is a
recursive series / parallel / exclusive-choice / **loop** decomposition — i.e. VSP (§6.3) plus choice (§6.8's
alternatives) plus loops — which is a strikingly good description of what we want to infer. **Put an explicit
loop operator into the latent structure rather than hoping loops emerge from a poset model: they cannot.** It
is also a proper prior over *sound* workflows, so with a distribution on operators and a branching process on
depth it becomes a generative prior we can do transdimensional inference over. (ii) IMc's problem statement is
ours with a different noun: "absence of evidence for an edge is weak evidence of absence, and how weak depends
on how much you looked". Borrow the framing that **incompleteness is a property of the observation process,
not of the model**, and borrow the specific diagnosis that **loops and long-distance dependencies are the
first structures lost under incompleteness.**

**That diagnosis supports what may be the most important inference in this review: our 0.00–0.25 rework recall
and our systematically-too-fast duration are probably the same defect, not two.** A missed resubmission cycle
simultaneously drops a rework edge (recall failure) and removes an entire queue wait from the predicted
duration (the 1.5×, and it explains the *direction* — always too fast, never too slow). The modelling
consequence is concrete: **the prior on loop existence must not be learned from document evidence at all** —
give each step a Beta prior on "has a rework loop" with a high mean for discretionary review steps — and
crucially **let duration evidence update loop existence**, so a reported 14-week elapsed time is positive
evidence for an undisclosed resubmission cycle. That inverts the usual direction (structure → timing) and is
the one place where our unusual evidence mix is an advantage rather than a handicap.

**Breaks:** the mechanics are unusable — everything runs off a directly-follows graph built by counting
adjacent event pairs, and we have no counts. The "probabilistic" reasoning in IMc is thresholds and
heuristics, not a probability model: no posterior, no calibration. It returns one model, cannot use document
assertions at all, has no changepoints and no nonparametric prior over activities. **So it is not a substitute
for the Nicholls line — it is the *representation* we should be fitting with the Nicholls line's *inference
machinery*.** That hybrid appears to be unbuilt.

### 7.7 Stochastic conformance checking

- Leemans, S. J. J., Syring, A. F. & van der Aalst, W. M. P. "Earth Movers' Stochastic Conformance Checking." *BPM Forum 2019*, LNBIP 360. DOI [10.1007/978-3-030-26643-1_8](https://doi.org/10.1007/978-3-030-26643-1_8) — journal extension with Brockhoff and Polyvyanyy, *Information Systems*, 2021. DOI [10.1016/j.is.2021.101724](https://doi.org/10.1016/j.is.2021.101724)
- Leemans, S. J. J. & Polyvyanyy, A. "Stochastic-Aware Conformance Checking: An Entropy-Based Approach." *CAiSE 2020*, LNCS. DOI [10.1007/978-3-030-49435-3_14](https://doi.org/10.1007/978-3-030-49435-3_14) — journal extension "Stochastic-aware precision and recall measures for conformance checking in process mining." *Information Systems*, 2023. DOI [10.1016/j.is.2023.102197](https://doi.org/10.1016/j.is.2023.102197)

EMSC treats both model and log as *distributions over traces* (stochastic languages) and scores conformance as
an optimal-transport distance with a trace-edit ground metric. The entropy-based work gives *separate*
stochastic precision and recall with axiomatic monotonicity guarantees.

**Borrow:** the reframing "a process model *is* a distribution over traces" is the correct generative stance
and the vocabulary to adopt — it is what licenses talking about a posterior predictive over workflows at all.
EMSC is the right **reporting metric** for posterior predictive versus gold: sample traces from the posterior
predictive, compute earth-mover distance to the gold stochastic language, and get one number sensitive to both
structure and probability mass, with a customisable ground metric so a missed rework loop can be weighted as
expensive. Better than an order-agreement statistic we are already saturating at 0.90–0.99. And the
**precision/recall separation** is the diagnostic EMSC's single number lacks: our two measured failures are of
opposite type — high order agreement is a recall success, 0.00–0.25 rework recall is a recall failure, and
1.5×-too-fast is a *precision* failure (the model puts mass on fast traces the world does not produce).
Reporting them separately would have made the pilot diagnosis immediate. Borrow the axiomatic discipline too:
state up front what our metric must do monotonically.

**Breaks:** these are evaluation metrics, not likelihoods, and they need two stochastic languages. Our
empirical side is 1–5 traces, so the log-side distribution is an atomic measure and the distance is dominated
by which three anecdotes we happened to collect; entropy estimation is *more* sample-hungry still. There is no
inference here and no treatment of a document as evidence. **Do not mistake "stochastic conformance checking"
for "a probabilistic model of process evidence".** And stochastic recall presumes the log is a faithful sample
from the true process, which for our selection-biased forum corpus is flatly false — our anecdotes
over-represent pathological long cases, so naive stochastic recall would *penalise* a correctly-calibrated
model. Any use needs an explicit selection-weighting layer the papers do not provide.

### 7.8 Burke, A., Leemans, S. J. J. & Wynn, M. T. "Stochastic Process Discovery by Weight Estimation." *ICPM 2020 Workshops*, LNBIP. DOI [10.1007/978-3-030-72693-5_20](https://doi.org/10.1007/978-3-030-72693-5_20) — with "Discovering Stochastic Process Models by Reduction and Abstraction." *Petri Nets 2021*, LNCS, 312–336. DOI [10.1007/978-3-030-76983-3_16](https://doi.org/10.1007/978-3-030-76983-3_16)

Estimates the *transition weights* (routing probabilities) of a discovered net from a log, comparing
frequency-based, alignment-based and structural estimators; the second paper does it via net reduction so
weights can be estimated on a simplified net and lifted back.

**Borrow:** the honest comparison tells us which observable quantities actually pin routing probabilities, and
the answer — you need *counts of how many cases took each branch* — is a direct specification of what a
document cannot give us and a forum post can. That motivates an explicit evidence design: a document saying
"if plans are deficient, staff will issue a correction notice" gives branch *existence*; only the ratio of
posters mentioning a correction notice gives branch *weight*, and only with a selection model. Also borrow
reduce-then-lift as a computational strategy: collapse chains of never-separately-disclosed steps into one
super-step for inference, then expand.

**Breaks:** pure MLE from branch counts with structure given. At our evidence density most branches have zero
or one observation, so the MLE is 0 or 1 and every counterfactual is degenerate. No prior, no regularisation
in Bayesian terms, no notion of a weight that is *reported* rather than *observed*, and weights are assumed
stationary, contradicting our non-stationarity requirement.

### 7.9 Cry, P., Ballarini, P., Horváth, A. & Le Gall, P. "Statistical process discovery." arXiv:[2504.21390](https://arxiv.org/abs/2504.21390), 2025

The only genuinely Bayesian stochastic process discovery I could find. Combines "a simulation-based Bayesian
parameter inference scheme, used to search for the 'optimal' instance of a stochastic model, with an expressive
statistical model checking engine, used (during inference) to approximate the language of the considered
model's instance", with runtime tradeable against accuracy.

**Borrow:** two things. (a) **The methodological precedent for likelihood-free inference over process models.**
Their bottleneck diagnosis is identical to ours: the stochastic language of a nontrivial model is not
analytically available, so exact likelihood evaluation is hopeless, and the answer is to *simulate* and compare
summaries. Our model — a partial order with LogNormal durations, batching cadence, fees and visibility
channels — is at least as intractable, and this is the citation establishing that simulation-based inference is
the accepted move in this literature rather than an exotic one. (b) The accuracy/runtime dial is practical:
cheap low-replicate simulation in early SMC rounds, tighter later.

**Breaks:** it is a posterior over the *parameters of a fixed structure* — the net comes from elsewhere and the
number of steps is not a random variable. Our hardest unknown is outside its scope, and moving from parameter
to structure inference is not a tuning change: it is transdimensional inference over partial orders, which
nobody in this field has done. The observed data is still a log. And simulation-based inference needs enough
data for the summaries to be informative; with three traces plus documents the ABC acceptance surface is
nearly flat in most directions, so the posterior will be prior-dominated — which is fine and honest, but means
**the prior elicitation from documents is where the real work is**, and they offer nothing there.

### 7.10 Predictive models, quality dimensions, and the field's own admission

- Breuker, D., Matzner, M., Delfmann, P. & Becker, J. "Comprehensible Predictive Models for Business Processes." *MIS Quarterly* 40(4), 2016, 1009–1034. DOI [10.25300/MISQ/2016/40.4.10](https://doi.org/10.25300/MISQ/2016/40.4.10)
- Buijs, J. C. A. M., van Dongen, B. F. & van der Aalst, W. M. P. "Quality Dimensions in Process Discovery: The Importance of Fitness, Precision, Generalization and Simplicity." *IJCIS*, 2014. DOI [10.1142/S0218843014400012](https://doi.org/10.1142/S0218843014400012) — conference version *CoopIS 2012*, LNCS, 305–322. DOI [10.1007/978-3-642-33606-5_19](https://doi.org/10.1007/978-3-642-33606-5_19); genetic search *IEEE CEC 2012*. DOI [10.1109/CEC.2012.6256458](https://doi.org/10.1109/CEC.2012.6256458)
- Herbst, J. & Karagiannis, D. "Integrating machine learning and workflow management to support acquisition and adaptation of workflow models." *DEXA 1998*. DOI [10.1109/DEXA.1998.707491](https://doi.org/10.1109/DEXA.1998.707491) — journal version *Int. J. Intelligent Systems in Accounting, Finance & Management* 9(2), 2000, 67–. DOI [10.1002/1099-1174(200006)9:2<67::AID-ISAF186>3.0.CO;2-7](https://doi.org/10.1002/1099-1174(200006)9:2%3C67::aid-isaf186%3E3.0.co;2-7) (**UNVERIFIED end page**)
- Rozinat, A. & van der Aalst, W. M. P. "Conformance checking of processes based on monitoring real behavior." *Information Systems* 33(1), 2008, 64–95. DOI [10.1016/j.is.2007.07.001](https://doi.org/10.1016/j.is.2007.07.001)
- Janssenswillen, G. & Depaire, B. "Towards Confirmatory Process Discovery: Making Assertions About the Underlying System." *BISE*, 2018. DOI [10.1007/s12599-018-0567-8](https://doi.org/10.1007/s12599-018-0567-8)

Breuker et al. argue predictive process monitoring should use an explicitly *generative* probabilistic model
(RegPFA, a latent-state probabilistic finite automaton) rather than a mined net or a black box. Buijs et al.
state the four quality dimensions and show a user-weighted combination of them yields materially different
models from the same log. Herbst & Karagiannis is the earliest stochastic-automaton workflow induction, with a
**model-merging search scored by likelihood times prior**. Rozinat & van der Aalst found conformance on
token-based replay. Janssenswillen & Depaire argue from inside the field that process discovery has conflated
*describing the log* with *inferring the system*, and needs confirmatory, uncertainty-quantified inference.

**Borrow:** four things. (i) Buijs et al.'s **process trees as a sound, always-valid hypothesis space** — see
§7.6; and their demonstration that the weighting materially changes the answer is the field's own admission
that its objective is not identified, which is the argument *for* replacing it with a likelihood and a prior.
(ii) Breuker et al.'s stance and their **model selection by held-out predictive performance**, which is the
closest thing in this literature to a principled answer to "how many steps?" and a template for our structure
selection via posterior predictive on held-out documents. (iii) Herbst & Karagiannis's **merge/split search
scored by marginal likelihood** is the right move set for transdimensional structure search, and the in-domain
precedent for it. (iv) Rozinat & van der Aalst's **token-replay diagnostic decomposition** localises
disagreement to a specific place in the net — for a project whose instrument is the metric seam, "our
posterior and the gold disagree at the fire-review step" is actionable in a way a scalar is not. (v)
Janssenswillen & Depaire is the citation that says out loud, from inside the field and in a respectable venue,
that process mining lacks exactly what we are building; use their log-level/system-level distinction
consistently, because it disciplines what our metrics are allowed to mean.

**Breaks:** RegPFA is a *sequential* automaton and cannot compactly represent concurrency — a partial order
with *k* independent steps needs *k*! paths — and for us the parallel-vs-sequential distinction is a primary
object of inference. "Regularised" is MAP, not a posterior. **On the brief's explicit question — is
"generalization" ever a genuine posterior-predictive statement? No, not here or anywhere else in this
literature.** Buijs et al.'s generalization is a heuristic penalty computed from how frequently each model
element was visited in the log: Good-Turing-*flavoured* in spirit, but no probability model, no held-out
predictive likelihood, no marginal likelihood, and no statement of the form "the probability a fresh case
exhibits unseen behaviour is *p*". The four dimensions are a multi-objective *scoring rubric* standing in for a
likelihood the field never wrote down. Token counting likewise has no sampling distribution and cannot be
inverted into an inference, and it gives non-deterministic results on nets with silent transitions — the case
we care about. Janssenswillen & Depaire is an agenda with no method, and even its agenda assumes a log as the
sample from the system: the gap it names is "log → system", whereas ours is "documents + anecdotes → system",
one step further out.

### 7.11 Pegoraro, M., Uysal, M. S. & van der Aalst, W. M. P. — uncertain event data

- "Conformance checking over uncertain event data." *Information Systems* 102, 2021, 101810. DOI [10.1016/j.is.2021.101810](https://doi.org/10.1016/j.is.2021.101810)
- "Mining Uncertain Event Data in Process Mining." *ICPM 2019*, 89–96. DOI [10.1109/ICPM.2019.00023](https://doi.org/10.1109/ICPM.2019.00023)
- "Discovering Process Models from Uncertain Event Data." *BPM Workshops 2019*, LNBIP. DOI [10.1007/978-3-030-37453-2_20](https://doi.org/10.1007/978-3-030-37453-2_20)
- "Efficient Time and Space Representation of Uncertain Event Data." *Algorithms* 13(11), 2020, 285. DOI [10.3390/a13110285](https://doi.org/10.3390/a13110285)

The field's only sustained programme on making an *event* something other than a recorded fact. An uncertain
event carries a set of possible activity labels, a timestamp *interval*, and possibly uncertain case
membership; algorithms then compute **best-case and worst-case** conformance bounds and discover uncertain
directly-follows graphs with possible/certain edges.

**Borrow:** the **data model** is directly reusable and the right shape for LLM output — an extracted claim is
not "step X exists at time t" but a distribution over (label, actor, time-interval). Two specifics: their
taxonomy of uncertainty types (activity-label, timestamp, case-membership, and **indeterminate events** — an
event that may not have happened at all) maps almost one-to-one onto our LLM error modes, with indeterminate
events being exactly a hallucinated or hedged extraction; and the possible/certain edge distinction is a cheap
interpretable intermediate representation for order evidence.

**Breaks:** blunt — **this is imprecise probability, not Bayesian inference.** The uncertainty is set-valued and
the outputs are *bounds*, a much weaker object than a posterior, and **bounds do not compose over many pieces
of weak evidence**: combine 40 documents' interval uncertainty and the bounds go vacuous, whereas 40 noisy
likelihood terms concentrate. That non-composition is fatal for us, because sequential accumulation of many
weak sources is the entire point of our design. The uncertainty is also treated as *given* — an oracle hands
you the label set — whereas our extractor's error rates are parameters to be inferred. Take the ontology,
leave the calculus.

### 7.12 van Hee, K. M., Liu, Z. & Sidorova, N. "Is my event log complete? — A probabilistic approach to process mining." *RCIS 2011*. DOI [10.1109/RCIS.2011.6006848](https://doi.org/10.1109/RCIS.2011.6006848) — with Pei, J., Wen, L., Yang, H., Wang, J. & Ye, X. "Estimating Global Completeness of Event Logs: A Comparative Study." *IEEE Transactions on Services Computing*, 2018. DOI [10.1109/TSC.2018.2805912](https://doi.org/10.1109/TSC.2018.2805912)

Poses completeness as a genuine estimation problem — given a log, what is the probability the underlying process
can produce behaviour we have not seen, and how many more traces would we need — with Pei et al. comparing the
available estimators, species-richness ones among them.

**Borrow:** the **only** place in process mining making something close to a real predictive statement about
unseen behaviour, and directly relevant to our unknown step count. The species framing is the right import:
treat each newly-encountered step as a sighting, and the rate of first-sightings across sources bounds how
much remains undisclosed. Concretely — track the **singleton rate** (steps mentioned by exactly one source) as
documents accumulate; a high singleton rate is direct evidence more undisclosed steps exist, giving a
principled computable prior for the step-count parameter and a rigorous answer to "when do we stop
collecting?". Cheap, and usable.

**Breaks:** the sighting model assumes sources sample behaviour **exchangeably and independently**, which is
exactly what ours do not do. Documents are selectively disclosing *and* correlated: every ordinance-derived
page omits the same internal routing steps, so the singleton rate is biased downward and a naive Chao-type
estimator will confidently under-estimate. Fixing this needs a source-type-indexed detection probability —
standard in ecology (§8.10–§8.13), absent here. Also their "completeness" is of *trace-level behaviour* given a
log; we want completeness of the *step inventory* given documents. Related but not the same estimand, and the
estimator properties do not transfer.

### 7.13 Partially ordered event data

- Lu, X., Fahland, D. & van der Aalst, W. M. P. "Conformance Checking Based on Partially Ordered Event Data." *BPM Workshops 2014*, LNBIP. DOI [10.1007/978-3-319-15895-2_7](https://doi.org/10.1007/978-3-319-15895-2_7) — with Mans, *IEEE ETFA 2014*. DOI [10.1109/ETFA.2014.7005060](https://doi.org/10.1109/ETFA.2014.7005060)
- van der Aa, H., Leopold, H. & Weidlich, M. "Partial order resolution of event logs for process conformance checking." *Decision Support Systems*, 2020. DOI [10.1016/j.dss.2020.113347](https://doi.org/10.1016/j.dss.2020.113347)

Lu et al. observe that recorded timestamps are often too coarse to totally order events, and redefine alignment
over *partially ordered* traces. Van der Aa et al. go further and treat the partial order itself as uncertain,
**probabilistically resolving** the order — estimating a distribution over linearisations — before conformance
checking.

**Borrow:** the only part of process mining where the observation is a partial order, and van der Aa et al. is
the more valuable: **it puts a probability distribution over orderings and marginalises**, which is the correct
handling of a document that says "you must obtain A, B and C" without saying in what order. Take it directly as
our order-evidence likelihood — a document constrains the partial order to a *set* of consistent
linearisations, and the evidence term is a marginal over that set rather than a commitment to one. Also take
the conceptual point: the recorded order is a lossy projection of the true partial order, not the truth —
**which raises the possibility that our 0.90–0.99 order agreement is partly measuring agreement on arbitrary
linearisations rather than on real precedence.** Worth checking.

**Breaks:** both need a reference model plus a log; neither infers structure. Van der Aa et al. estimate ordering
probabilities *from the log's empirical statistics*, and with no log there is nothing to estimate them from, so
for us those must come from priors and documents — a different, unaddressed problem. Alignment cost is also a
poor likelihood in one specific way: it is a min-cost objective reporting only the single best explanation of a
trace, and a likelihood needs the sum over explanations. And their partial orders arise from *timestamp
coarseness*, a benign accident; ours from genuine concurrency and selective disclosure.

### 7.14 Bose, R. P. J. C., van der Aalst, W. M. P., Žliobaitė, I. & Pechenizkiy, M. "Dealing With Concept Drifts in Process Mining." *IEEE TNNLS* 25(1), 2014, 154–171. DOI [10.1109/TNNLS.2013.2278313](https://doi.org/10.1109/TNNLS.2013.2278313) — with Carmona, J. & Gavaldà, R. "Online Techniques for Dealing with Concept Drift in Process Mining." *IDA 2012*, LNCS, 90–102. DOI [10.1007/978-3-642-34156-4_10](https://doi.org/10.1007/978-3-642-34156-4_10)

Defines drift types (sudden, gradual, recurring, incremental), builds feature representations of trace windows,
and applies change detection to localise when the process changed and characterise what changed.

**Borrow:** the right vocabulary and the right warning. The drift taxonomy tells us our conflict layer must
distinguish (i) **sudden** drift — a statutory amendment, which our setting timestamps for us — from (ii)
**recurring/seasonal** drift, which is exactly our batching cadence (monthly council calendar) and must not be
mistaken for a rule change, from (iii) **incremental** drift in durations, i.e. queue growth under rising load.
Those three demand different model components and conflating them is a real risk. **And we have an advantage
this literature lacks: document effective dates.** We largely *know* when the rule changed, so drift
*detection* is mostly unnecessary; what we need is to condition each document's likelihood on the version in
force at its date, which turns a hard change-detection problem into an easy indexing one. A cheap win worth
stating explicitly.

**Breaks:** every technique is a windowed statistical test over a *stream of traces* — no stream, no window, no
test statistic. Drift is *detected*, not *modelled*: you get a changepoint and a characterisation, not a
time-varying generative process, so you cannot pool evidence across regimes, which we must do since pre- and
post-amendment documents both inform the steps that did not change. Nothing addresses non-stationary
*durations* under load, which is our actual timing non-stationarity.

### 7.15 Queueing inference: the queue inference engine

- Larson, R. C. "The Queue Inference Engine: Deducing Queue Statistics from Transactional Data." *Management Science* 36(5), 1990, 586–601. DOI [10.1287/mnsc.36.5.586](https://doi.org/10.1287/mnsc.36.5.586)
- Bertsimas, D. & Servi, L. D. "Deducing Queueing from Transactional Data: The Queue Inference Engine, Revisited." *Operations Research* 40(3 Supp. 2), 1992, S217–S228. DOI [10.1287/opre.40.3.s217](https://doi.org/10.1287/opre.40.3.s217)
- Jones, L. K. & Larson, R. C. "Efficient Computation of Probabilities of Events Described by Order Statistics and Applications to Queue Inference." *INFORMS Journal on Computing* 7(1), 1995, 89–. DOI [10.1287/ijoc.7.1.89](https://doi.org/10.1287/ijoc.7.1.89)

Larson shows that from *only* service-completion epochs plus knowledge of when each busy period began — with
arrivals never observed — one can deduce the queue's waiting-time statistics, by assuming Poisson arrivals and
exploiting the fact that conditional on the number of arrivals in a congestion period, their arrival times are
distributed as the order statistics of i.i.d. uniforms over that period. Bertsimas & Servi reduce the cost from
O(n⁵) to O(n³) and give **per-customer waiting-time distributions**.

**Borrow:** the identification idea is the one we need. (a) It licenses the general move: **the queue is
identifiable from service-completion timing alone, given a load model** — the formal answer to "we never see
the queue". (b) It tells us precisely what public data would unlock this: **permit-issuance date series are
QIE-shaped data.** Many permitting authorities publish permit databases with issue dates; a dense series of
issuance epochs plus a busy-period model is exactly Larson's input, and it is public, cheap, and needs no
agency cooperation. **I would rate this the highest-value data-acquisition recommendation in the review.** (c)
Bertsimas & Servi's per-customer distribution is the right output shape, because our evidence is per-applicant
— a reddit post is one customer's sojourn time, and we need p(this applicant's wait | load) as a likelihood
term, not an aggregate mean. The O(n³) efficiency also decides feasibility if the term sits inside an MCMC
loop.

**Breaks:** QIE needs the *set* of completion epochs within an identified busy period, and the busy period's
start. We have neither — we have one applicant saying "it took 11 weeks", which is a *sojourn time*, not a
completion epoch, carrying no busy-period boundary. The assumptions are also specifically wrong for
permitting: Poisson arrivals (applications are seasonal and bunch before code changes take effect), FCFS
(emphatically violated by expedited review, political priority and applicant-caused delay), a single
continuously-busy server, and no abandonment (applicants do abandon permits). Each violation biases the
inferred wait, mostly downward. And nothing handles a **multi-step network** of queues or **batched/calendared
service** — the latter is a hard break, since QIE assumes a server that works whenever there is work and a
monthly-meeting step violates that at the foundations.

### 7.16 Queue mining

- Senderovich, A., Weidlich, M., Gal, A. & Mandelbaum, A. "Queue mining for delay prediction in multi-class service processes." *Information Systems* 53, 2015, 278–295. DOI [10.1016/j.is.2015.03.010](https://doi.org/10.1016/j.is.2015.03.010) — conference version *CAiSE 2014*, LNCS, 42–57. DOI [10.1007/978-3-319-07881-6_4](https://doi.org/10.1007/978-3-319-07881-6_4)
- Senderovich, A., Leemans, S. J. J., Harel, S., Gal, A., Mandelbaum, A. & van der Aalst, W. M. P. "Discovering Queues from Event Logs with Varying Levels of Information." *BPM Workshops 2015*, LNBIP, 154–166. DOI [10.1007/978-3-319-42887-1_13](https://doi.org/10.1007/978-3-319-42887-1_13)
- Senderovich, A., Beck, J. C., Gal, A. & Weidlich, M. "Congestion Graphs for Automated Time Predictions." *AAAI* 33(1), 2019, 4854–4861. DOI [10.1609/aaai.v33i01.33014854](https://doi.org/10.1609/aaai.v33i01.33014854)

Queue mining mines queueing structure (service stations, customer classes, priority) from a log and predicts
delay using queueing-derived predictors. The degraded-information paper studies **which queueing quantities
remain identifiable as information is stripped out** of the log. Congestion graphs take a middle path: don't
model the discipline, model *load*, propagated through an annotated graph.

**Borrow:** three things. (i) The central empirical finding is the strongest external support for our
diagnosis: **queueing/congestion features dominate control-flow features for delay prediction.** Knowing the
process structure perfectly tells you much less about duration than knowing current load. That is our
1.5×-too-fast result, obtained independently in another domain, and it justifies moving effort from structure
extraction (saturated at 0.90–0.99) to load modelling (broken). (ii) The **multi-class** insight maps cleanly:
a permitting authority serves several application classes (over-the-counter, plan-check, discretionary) with
different service distributions and effectively different priorities, and a single-class model mis-prices all
of them. Their snapshot predictors also suggest an obtainable covariate — **current backlog or application
volume, which many jurisdictions publish**, turning an unconditional duration prior into a conditional one.
(iii) The degraded-information paper is effectively an **identifiability ladder**, and we should use it to
place our evidence regime on that ladder and state what we can and cannot hope to recover. It also gives the
honest ceiling: at their least-informative level you can still recover aggregate load and utilisation-driven
delay but lose per-case decomposition — a defensible target for us. And from congestion graphs, the design
philosophy I would adopt: when the true discipline is unknown, **give each step a single scalar
congestion/utilisation parameter with an informative prior, make queue time a known function of it (mean wait
∝ ρ/(1−ρ)), and refuse to model discipline, priority or abandonment at all.** Far more identifiable from our
evidence than a full queueing network.

**Breaks:** everything is mined from a log containing *queue-entry and service-start events* — that is, the log
must distinguish "waiting" from "being worked on", which is the very distinction we cannot observe and are
trying to infer. **Their touch/queue decomposition is not inferred; it is read off the log.** Their
least-informative level still has many completion events with case identifiers, which is more than we have —
**we are one full rung below the bottom of their ladder.** The predictors are point predictors evaluated by
MAE/RMSE with no uncertainty, so nothing plugs into a Bayesian model; information loss shows up as estimator
bias rather than posterior widening, which is the wrong failure mode for us. And the setting is
high-throughput service where thousands of cases per week make snapshot statistics reliable; a municipal
permitting step may process 30 cases a year.

### 7.17 Bayesian inference for queues from partial data

- Sutton, C. & Jordan, M. I. "Bayesian inference for queueing networks and modeling of internet services." *Annals of Applied Statistics* 5(1), 2011. DOI [10.1214/10-AOAS392](https://doi.org/10.1214/10-AOAS392)
- Wang, W., Casale, G. & Sutton, C. "A Bayesian Approach to Parameter Inference in Queueing Networks." *ACM TOMACS*, 2016. DOI [10.1145/2893480](https://doi.org/10.1145/2893480)
- Armero, C. & Bayarri, M. J. "Prior Assessments for Prediction in Queues." *JRSS Series D (The Statistician)*, 1994. DOI [10.2307/2348939](https://doi.org/10.2307/2348939)

Sutton & Jordan give a fully Bayesian treatment of a queueing *network* in which only boundary arrivals and
departures are observed; per-station service times, waiting times, routing, and the *ordering* of latent events
are all inferred jointly by MCMC with the queueing dynamics as a prior. Wang, Casale & Sutton target the case
where only **end-to-end response times** are observed and infer per-station service demands from them. Armero
& Bayarri address how to place priors on queueing parameters so the induced *predictive* distributions for
waiting time are sensible.

**Borrow:** this is the methodological gold standard for our timing layer and should be a cornerstone citation.
(a) Sutton & Jordan **demonstrate that elapsed-time decomposition into service and wait is a well-posed
Bayesian inference problem** when only boundary times are observed — i.e. exactly our applicant-reported
elapsed times — provided the queueing dynamics supply the structural constraint. (b) The latent-variable design
is directly transplantable: latent per-step service times, latent queue waits, latent routing, with the
deterministic queueing identity (departure = max(arrival, previous departure) + service) as a hard constraint
that couples them and does most of the identification work. (c) Their MCMC for sampling **latent event
orderings** subject to those constraints is precisely the sampler our latent partial order needs, and it is a
solved problem. (d) Wang/Casale/Sutton's data type matches ours exactly, and their handling of the intractable
response-time likelihood by approximation is the right engineering move — we will not have closed form for the
sojourn distribution of a LogNormal-service batched step, so plan for an approximation or a simulator from the
start. (e) **Armero & Bayarri contain a trap worth knowing in advance, and it may matter more than any
structural improvement:** because waiting time goes as ρ/(1−ρ) × service time, an innocuous-looking prior on ρ
that puts mass near 1 induces a predictive waiting time with infinite mean, and a prior "uninformative" on the
rates is strongly — often absurdly — informative on the wait. Their discipline is to **elicit on the
predictive scale**: put the prior on the observable (the queue-to-touch ratio, or expected wait in weeks) and
back out ρ, never the reverse. **This is a live candidate cause of our 1.5×.**

**Breaks:** the identification comes from *volume*. Sutton & Jordan observe thousands of boundary
arrival/departure pairs, and it is the aggregate load pattern — busy periods, congestion build-up, correlation
between successive delays — that separates service from wait. **With three anecdotal elapsed times the
service/wait convolution is not identified, full stop:** elapsed = touch + queue is a convolution of two
positive random variables, and a handful of sums cannot recover the summands without an external constraint.
Be blunt with the team — do not expect a Sutton–Jordan decomposition on reddit posts to return anything but
the prior. Wang/Casale/Sutton's identification additionally relies on **observing response times at multiple
load levels**, since varying throughput is what separates load-independent service demand from the
load-dependent queueing term. That points at a concrete, nearly free change to our collection strategy:
**date-stamp every user report and join it to published application-volume series.** Reported durations at
varying load identify the decomposition in a way that any number of reports at unknown load never will.
Network topology and station count are given in both. Armero & Bayarri is single-station M/M/1-family with
exponential service and steady state, so no closed-form result survives our setting — its contribution reduces
to the prior-specification lesson. And none of the three handles batched availability.

Also worth one line, because it names the third term we are missing: Martin, N., Depaire, B., Caris, A. &
Schepers, D. "Retrieving the resource availability calendars of a process from an event log." *Information
Systems*, 2019. DOI [10.1016/j.is.2019.101463](https://doi.org/10.1016/j.is.2019.101463). **Borrow:** the
three-way split is better than our two-way one — **elapsed = touch + queue + unavailability**, where
unavailability is calendar-driven and near-deterministic (business hours, holidays, and above all the monthly
council calendar), and is identifiable from timing patterns alone because gaps cluster at predictable phases.
**Breaks:** needs per-resource event timestamps, and it treats the calendar as a nuisance to be removed so
"real" durations can be measured — whereas for us the monthly council meeting is not noise obscuring the
duration, it *is* a large part of the duration and a prime candidate for the simplify-with-least-harm
intervention. Nothing models batching as a queueing discipline.

### 7.18 LLM process-model extraction with uncertainty

**Negative result worth recording:** a systematic arXiv sweep for LLM-based BPMN/process extraction with
probabilistic output, confidence scores, distributions over models, or quantified uncertainty finds the field
overwhelmingly committed to **deterministic single-BPMN emission**. Representative of the mainstream: Kourani,
H., Berti, A., Schuster, D. & van der Aalst, W. M. P. "Process Modeling With Large Language Models."
arXiv:[2403.07541](https://arxiv.org/abs/2403.07541), 2024 — iterative LLM generation and refinement of one
model, no uncertainty quantification. The only works quantifying uncertainty at all come from one group:

- Menaka Sekar, P. K., Matei, I., Zhenirovskyy, M., Wong, H. Y., Kohmura, S., Hotta, S. & Inomata, A. "Automatic Generation of Executable BPMN Models from Medical Guidelines." arXiv:[2604.07817](https://arxiv.org/abs/2604.07817), 2026
- Matei, I., Menaka Sekar, P. K., Zhenirovskyy, M., Wong, H. Y., Kohmura, S., Hotta, S. & Inomata, A. "Ambiguity Detection and Elimination in Automated Executable Process Modeling." arXiv:[2604.10884](https://arxiv.org/abs/2604.10884), 2026

The first converts **healthcare policy documents** into executable, data-aware BPMN for simulation-based
*policy evaluation*, with data-grounded generation plus syntax auto-correction, KPI instrumentation, and
**entropy-based uncertainty detection**; evaluated on diabetic nephropathy guidelines from three Japanese
municipalities, 100 models per backend across three LLMs, 1,000 synthetic patients, reporting 100%
ground-truth match for well-structured policies and >92% per-patient decision agreement across all conditions.
The second detects behavioural inconsistency from the **empirical distribution of KPIs across regenerations**,
localises divergence to **gateway logic** by model-based diagnosis, maps it back to verbatim narrative
segments, and repairs the source text — explicitly "in the absence of ground-truth BPMN models".

**Borrow:** startlingly close to our project — policy documents in, executable simulatable model out,
municipality-level variation, evaluation by simulated case outcomes rather than graph-edit distance — and it
should be cited as the nearest neighbour. Four takes: (i) **KPI instrumentation as the evaluation target** is
the right instinct and a better primary metric than order agreement; (ii) **entropy over repeated generations**
is a zero-architecture way to get a first uncertainty estimate and, more usefully, to *locate* which parts of a
document are underdetermined; (iii) **localisation** — attributing behavioural variance to a specific gateway
and then to a specific verbatim sentence — is precisely the instrument our project wants ("this clause of HSC
17920.3 is the seam where the workflow is underdetermined"), and it turns model uncertainty into a
*regulatory-text* finding, which is our deliverable; (iv) the finding that agreement is near-perfect for
well-structured policies and degrades otherwise gives us a document-quality covariate we could plausibly
measure and condition on.

**Breaks:** **entropy over an ensemble of LLM generations is not a posterior.** It measures decoder variance
under a fixed prompt, conflating sampling temperature, prompt sensitivity and genuine ambiguity, with no
calibration guarantee and no prior — and crucially **it cannot get more confident as evidence accumulates**,
because it is not conditioning on anything: feed it a second document and you get another ensemble, not an
updated belief. Neither paper has a sequential-evidence mechanism, cross-source conflict resolution, or any
timing model (durations are assumed in simulation), so they say nothing about our hardest problem. The second
paper's framing is also diagnostic rather than inferential: its objective is to *remove* ambiguity by rewriting
the source text, whereas we must *represent* ambiguity as a posterior and carry it forward — **we cannot
rewrite a statute to make it unambiguous.** Its ambiguity is localised only to gateway logic, whereas our
underdetermination is mostly about step existence, actor assignment and duration. And clinical guidelines are
far better structured and more complete than municipal permitting documents — they are written to be followed
step by step, whereas an ordinance is written to be legally binding and deliberately omits internal routing —
so the 100% ground-truth match must not be read as transferable.

Also relevant, as the only pre-LLM work treating a document and a process model as two pieces of evidence about
one reality: van der Aa, H., Leopold, H. & Reijers, H. A. "Comparing textual descriptions to process models —
the automatic detection of inconsistencies." *Information Systems* 64, 2016, 447–460. DOI
[10.1016/j.is.2016.07.010](https://doi.org/10.1016/j.is.2016.07.010). **Borrow:** the inconsistency taxonomy
(missing activity, extra activity, order disagreement) is a ready-made typology for our conflict layer, and
behavioural rather than purely textual comparison is the right level at which to declare a conflict.
**Breaks:** needs a model as one of its two inputs so it cannot build one; deterministic, with no probability
that the text or the model is the one in error; no source credibility, so it cannot **adjudicate** between a
statute and a FAQ; and it cannot attribute a conflict to genuine temporal change.

---

## 8. Capture–recapture, unseen-species estimation, and occupancy models

The brief asked whether the equal-catchability assumptions survive our setting. They do not, and the right
response is a model-based estimator with covariates on detection rather than a nonparametric lower bound. The
occupancy sub-area (§8.10–§8.13) was not in the brief and is, in my judgement, a closer analogue than classical
capture–recapture.

### 8.1 Good, I. J. "The Population Frequencies of Species and the Estimation of Population Parameters." *Biometrika* 40(3–4), 1953, 237–264. DOI [10.1093/biomet/40.3-4.237](https://doi.org/10.1093/biomet/40.3-4.237) — with Gale, W. A. & Sampson, G. "Good-Turing frequency estimation without tears." *Journal of Quantitative Linguistics* 2(3), 1995, 217–237. DOI [10.1080/09296179508590051](https://doi.org/10.1080/09296179508590051)

Good introduces the Good–Turing estimator: the probability mass of unseen species is f₁/n, the singleton
fraction. Gale & Sampson give Simple Good–Turing, with log-linear smoothing of the frequency-of-frequencies for
when high-frequency counts are sparse and erratic.

**Borrow:** Ĉ = 1 − f₁/n as a per-document-kind **coverage** statistic — applied *within* a kind it is the right
one-number summary of "what fraction of the revealable step-mass has this kind given us". SGT's smoothing is
the concrete fix for "Chao1 blows up when f₂ = 0", which is our regime.

**Breaks:** Good–Turing estimates mass over **the support the sampling process can reach.** A staff-only step
with near-zero disclosure probability in every public document contributes to neither f₁ nor f₂, so it is
outside the support and Good–Turing is *silent* on it — not uncertain about it, silent. And it assumes i.i.d.
draws from a fixed distribution; our documents are neither i.i.d. nor identically distributed. Smoothing
manufactures stability, not information.

### 8.2 Good, I. J. & Toulmin, G. H. "The Number of New Species, and the Increase in Population Coverage, When a Sample is Increased." *Biometrika* 43(1–2), 1956, 45–63. DOI [10.1093/biomet/43.1-2.45](https://doi.org/10.1093/biomet/43.1-2.45)

The canonical extrapolator: how many *new* species a sample enlarged by factor *t* will yield, via an
alternating binomial series in the frequency counts.

**Borrow:** the exact quantity we want — "how many new steps will document 6 give me?" — has a closed form here,
and it is the correct target for a stopping rule.

**Breaks:** two hard failures. The alternating series is numerically unstable for *t* ≳ 2, so it answers only
"what does one more document buy", never "how many steps exist". And it is defined on an *exchangeable*
accumulation curve. **Our measured curve is back-loaded — 6 of 10 steps on document 5 — which is a direct
falsification of the exchangeability this estimator is built on.** Feed our document-ordered curve to
Good–Toulmin and it will produce a confidently wrong number.

### 8.3 Chao, A. "Nonparametric estimation of the number of classes in a population." *Scandinavian Journal of Statistics* 11(4), 1984, 265–270 *(author, year, title, volume, issue and pages confirmed via OpenAlex; the commonly cited JSTOR stable id could not be confirmed)* — with Chao, A. "Estimating the Population Size for Capture-Recapture Data with Unequal Catchability." *Biometrics* 43(4), 1987, 783–. DOI [10.2307/2531532](https://doi.org/10.2307/2531532) *(Crossref records first page only)*

Chao 1984 derives Chao1 = S_obs + f₁²/(2f₂) and — the part people forget — proves it as a **lower bound** on
richness, valid under arbitrary detection heterogeneity. Chao 1987 adds a coefficient-of-variation correction
for unequal catchability.

**Borrow:** **the lower-bound property is genuinely robust and survives our heterogeneity.** Reported honestly
as "we have found at least this many and there are at least Chao1 − S_obs more", it is defensible and should be
our assumption-free floor. The CV-correction idea is also the right instinct: estimate the *spread* of
disclosure propensities and inflate accordingly — and we can estimate that CV directly from our measured
per-kind, per-visibility π table rather than from frequency counts.

**Breaks:** Chao1 is unbiased only under homogeneous catchability; under strong heterogeneity it is biased low,
and the bias grows with the mass of near-undetectable classes. With staff-only steps at 43% per-document
disclosure (and plausibly ~0% for some kinds), it will understate materially. And f₂ is tiny in our regime, so
f₁²/(2f₂) has enormous variance and is undefined when f₂ = 0. Blunt: **at our sample size Chao1 is a number
with no usable standard error.** The CV correction is a second-order fix for *moderate* heterogeneity; ours is
a discrete, near-deterministic class structure with structural zeros, which a single scalar CV cannot
represent.

### 8.4 Coverage-based estimation and extrapolation

- Chao, A. & Lee, S.-M. "Estimating the Number of Classes via Sample Coverage." *JASA* 87(417), 1992, 210–217. DOI [10.1080/01621459.1992.10475194](https://doi.org/10.1080/01621459.1992.10475194)
- Burnham, K. P. & Overton, W. S. "Estimation of the size of a closed population when capture probabilities vary among animals." *Biometrika* 65(3), 1978, 625–633. DOI [10.1093/biomet/65.3.625](https://doi.org/10.1093/biomet/65.3.625)
- Bunge, J. & Fitzpatrick, M. "Estimating the Number of Species: A Review." *JASA* 88(421), 1993, 364–373. DOI [10.1080/01621459.1993.10594330](https://doi.org/10.1080/01621459.1993.10594330)
- Chao, A. & Jost, L. "Coverage-based rarefaction and extrapolation: standardizing samples by completeness rather than size." *Ecology* 93(12), 2012, 2533–2547. DOI [10.1890/11-1952.1](https://doi.org/10.1890/11-1952.1)
- Chao, A., Gotelli, N. J., Hsieh, T. C., Sander, E. L., Ma, K. H., Colwell, R. K. & Ellison, A. M. "Rarefaction and extrapolation with Hill numbers." *Ecological Monographs* 84(1), 2014, 45–67. DOI [10.1890/13-0133.1](https://doi.org/10.1890/13-0133.1)

Chao & Lee build richness estimators on estimated sample coverage plus a CV term (the ACE family). Burnham &
Overton give the jackknife estimator for model Mh with data-driven selection of how much heterogeneity
correction the data support. Bunge & Fitzpatrick review the field and catalogue when each family fails. Chao &
Jost argue samples should be compared at equal *coverage* rather than equal size; Chao et al. 2014 add analytic
variance and confidence bands.

**Borrow:** two operationally important things. (i) **"Standardise by completeness, not by document count."**
Our saturation log should be indexed by estimated coverage, not document index — which also dissolves the
back-loading artifact, since coverage is not a function of reading order. (ii) Chao et al. 2014's analytic
confidence bands are the reference for putting an interval on any extrapolated count. Burnham & Overton's
order-selection is a defensible way to say "our evidence supports correcting this far and no further", and
Bunge & Fitzpatrick is the citation for the field-level conclusion that richness estimation is only as good as
the assumed detectability model.

**Breaks:** coverage-based inversion estimates the number of classes *in the sampled universe* — if public
documents are the frame, the sampled universe excludes some staff-only steps by construction, and no coverage
accounting recovers them. Burnham & Overton needs enough capture occasions to estimate the frequency vector
(5 documents, ~10 steps: the jackknife orders are not separable) and assumes exchangeable occasions, which our
fee-schedule-versus-ordinance contrast flatly violates. Chao & Jost recommend extrapolating at most to roughly
double the reference sample; we want to go from 5 documents to "all steps", far outside the sanctioned range.
And Bunge & Fitzpatrick predates the identifiability results that actually decide our case.

### 8.5 Link, W. A. "Nonidentifiability of Population Size from Capture-Recapture Data with Heterogeneous Detection Probabilities." *Biometrics* 59(4), 2003, 1123–1130. DOI [10.1111/j.0006-341X.2003.00129.x](https://doi.org/10.1111/j.0006-341X.2003.00129.x)

**The load-bearing result, so here is exactly what it claims, from the abstract:** "Individual heterogeneity is
especially problematic, in that reasonable alternative models may predict essentially identical observations
from populations of substantially different sizes. Thus even with very large samples, the analyst will not be
able to distinguish among reasonable models of heterogeneity, even though these yield quite distinct inferences
about population size." Illustrated for closed and open populations.

Note precisely what it does and does not prove: it does *not* prove a formal non-identifiability theorem over
all models; it exhibits distinct, individually reasonable heterogeneity models generating near-identical
observable capture-history distributions while implying substantially different N. **The conclusion is that
more data does not fix this — the ambiguity is in the model class, not the sample size.**

**Borrow:** the correct interpretive frame for our whole "how many steps are we missing" question. It licenses
— in fact requires — reporting the undiscovered-step count as *conditional on a stated detection model*, with
sensitivity across plausible detection models rather than a single posterior. It also kills, with a citation,
any reviewer demand for a single assumption-free number.

**Breaks:** a negative result with no constructive estimator. And it concerns *unobserved* individual
heterogeneity — **our heterogeneity is partly observed** (we know the document kind; we measured π by
visibility class), which is the one escape hatch Link's setup does not close. See §8.6.

### 8.6 Holzmann, H., Munk, A. & Zucchini, W. "On Identifiability in Capture–Recapture Models." *Biometrics* 62(3), 2006, 934–936. DOI [10.1111/j.1541-0420.2006.00637_1.x](https://doi.org/10.1111/j.1541-0420.2006.00637_1.x) — with Aleshin-Guendel, S., Sadinle, M. & Wakefield, J. "The central role of the identifying assumption in population size estimation." *Biometrics* 80(1), 2024. DOI [10.1093/biomtc/ujad028](https://doi.org/10.1093/biomtc/ujad028)

Holzmann et al. is a direct technical response to Link: identifiability *does* hold within suitably restricted
mixture families (notably binomial mixtures under constraints on the number of components relative to capture
occasions), so the problem Link exhibits is a property of the model *class* entertained, not an absolute
barrier. Aleshin-Guendel et al. argue that in multiple-systems estimation the **identifying assumption** — not
the estimator, not the prior — determines the answer, and should be made explicit and interpretable.

**Borrow:** together these are the constructive counterweight and the reporting stance. Holzmann et al. names
the exact lever: **identification is bought by restricting the mixture, and our visibility classes give us a
principled, substantively motivated three-component mixture instead of an arbitrary one.** It also names the
binding constraint — number of capture occasions versus number of mixture components — so with three visibility
classes we need meaningfully more than three independent evidence sources: five documents plus reddit plus case
traces is marginal but not hopeless. Aleshin-Guendel et al. gives the template: **state the identifying
assumption in substantive terms** ("staff-only steps have disclosure propensity bounded below by ε in kind
k"), report the estimate as a function of it, and stop pretending model averaging launders it away.

**Breaks:** the identifiability is parametric and fragile — misspecifying the number of components reintroduces
Link's ambiguity — and it gives identifiability in principle, not precision at *n* = 5. Aleshin-Guendel et al.
is aimed at list-intersection MSE with no covariates on detection, so it supplies no machinery for a
covariate-indexed propensity.

### 8.7 Model structure and design in capture–recapture

- Otis, D. L., Burnham, K. P., White, G. C. & Anderson, D. R. *Statistical Inference from Capture Data on Closed Animal Populations.* Wildlife Monographs, 1978. **UNVERIFIED** volume and pages — title and author list confirmed via two indexed reviews (Chapman, *Biometrics* 36, 1980, 362, DOI [10.2307/2530001](https://doi.org/10.2307/2530001); Green, *JASA* 76, 1981, 498, DOI [10.2307/2287873](https://doi.org/10.2307/2287873)).
- Pollock, K. H. "A Capture-Recapture Design Robust to Unequal Probability of Capture." *Journal of Wildlife Management* 46(3), 1982, 752–. DOI [10.2307/3808568](https://doi.org/10.2307/3808568)

Otis et al. define the M0/Mt/Mh/Mb/Mth/Mtbh hierarchy — does detection vary by occasion, by individual, or
both. Pollock's robust design nests short closed-population secondary periods inside longer primary periods, so
heterogeneity and turnover are estimated from different parts of the design.

**Borrow:** (i) the naming discipline: **our problem is Mth with observed covariates on both axes** — detection
varies by occasion (document kind) *and* by individual (visibility class). Saying that out loud immediately
tells a reader which literature applies. (ii) Pollock's design idea is executable: **read documents in
deliberate clusters by kind** (all ordinances, then all program pages, then all forms), treating each cluster
as a secondary period, which makes per-kind propensity estimable from within-cluster recaptures rather than
confounded with reading order. That is the direct fix for our back-loading artifact.

**Breaks:** Otis et al. is pre-covariate and its estimators are superseded. Pollock buys robustness with
*design*, i.e. more sampling — and if a jurisdiction's corpus is 5 documents total there is nothing to nest.

### 8.8 Heterogeneity-aware and Bayesian nonparametric capture–recapture

- Dorazio, R. M. & Royle, J. A. "Mixture Models for Estimating the Size of a Closed Population When Capture Rates Vary among Individuals." *Biometrics* 59(2), 2003, 351–364. DOI [10.1111/1541-0420.00042](https://doi.org/10.1111/1541-0420.00042) — see also the contested 2005 exchange, *Biometrics* 61, 874–876, DOI [10.1111/j.1541-020X.2005.00411_2.x](https://doi.org/10.1111/j.1541-020x.2005.00411_2.x)
- Manrique-Vallier, D. & Fienberg, S. E. "Population Size Estimation Using Individual Level Mixture Models." *Biometrical Journal* 50(6), 2008, 1051–1063. DOI [10.1002/bimj.200810448](https://doi.org/10.1002/bimj.200810448)
- Manrique-Vallier, D. "Bayesian Population Size Estimation Using Dirichlet Process Mixtures." *Biometrics* 72(4), 2016, 1246–1254. DOI [10.1111/biom.12502](https://doi.org/10.1111/biom.12502); R package `lcmcr`, DOI [10.32614/CRAN.package.lcmcr](https://doi.org/10.32614/CRAN.package.lcmcr)

Dorazio & Royle put a parametric (beta/logit-normal) mixture on individual capture probability and estimate N by
likelihood. Manrique-Vallier & Fienberg replace log-linear list-interaction models with an individual-level
latent-class mixture, so list *dependence* arises from unobserved subpopulation membership rather than fitted
interaction terms. Manrique-Vallier 2016 (LCMCR/NPLCM) learns the number of heterogeneity classes
nonparametrically with a Dirichlet process.

**Borrow:** Dorazio & Royle 2003 is the template for our detection sub-model: a continuous random effect on
per-step disclosure propensity with visibility class as a fixed effect shifting its mean. Manrique-Vallier &
Fienberg's reframing is exactly ours — **documents do not "interact"; they co-disclose because steps belong to
latent visibility classes**, and modelling dependence as arising from class membership is both more
parsimonious and substantively true for us. And `lcmcr` is the best off-the-shelf comparator available: run it
on our step × document incidence matrix and report it alongside our structured model — agreement is
reassuring, divergence localises the assumption doing the work. Cheap, and it pre-empts the obvious reviewer
question.

**Breaks:** Dorazio & Royle is notoriously sensitive to the assumed mixing distribution — which *is* Link's
point restated — and a beta mixture cannot represent a structural zero without degenerating. Latent-class
models fix the number of classes by model selection and the classes are *unlabelled*, so you learn "there is a
hard-to-see class" without knowing whether it is staff-only. `lcmcr` needs ≥4–5 lists *and* enough observed
units to populate capture patterns; ~10 steps across 5 documents is below the regime where a DP can distinguish
classes from noise. **And it cannot use our covariates** — it will rediscover "there are easy and hard steps"
without exploiting the fact that we already *measured* π by kind and visibility. Throwing that away is a real
cost.

### 8.9 Multiple-systems estimation with systematically different coverage

- Fienberg, S. E., Johnson, M. S. & Junker, B. W. "Classical Multilevel and Bayesian Approaches to Population Size Estimation Using Multiple Lists." *JRSS Series A* 162(3), 1999, 383–405. DOI [10.1111/1467-985X.00143](https://doi.org/10.1111/1467-985X.00143)
- Manrique-Vallier, D., Ball, P. & Sadinle, M. "Capture-Recapture for Casualty Estimation and Beyond: Recent Advances and Research Directions." In *Statistics in the Public Interest*, Springer, 2022, 15–31. DOI [10.1007/978-3-030-75460-0_2](https://doi.org/10.1007/978-3-030-75460-0_2); see also the `dga` Bayesian model-averaging implementation, DOI [10.32614/CRAN.package.dga](https://doi.org/10.32614/CRAN.package.dga)

Fienberg et al. connect log-linear multiple-recapture models to Rasch-type multilevel measurement models,
showing list-by-individual heterogeneity is formally an item-response problem. Manrique-Vallier, Ball & Sadinle
review MSE as practised for human-rights casualty counts, where lists (NGOs, morgues, press) have
systematically different coverage of different subpopulations.

**Borrow:** the **Rasch connection is genuinely useful and under-exploited**: treat "does document *d* disclose
step *s*" as an IRT item response with document *easiness* and step *difficulty*. Our fee schedule is a hard
item, the ordinance an easy one; staff-only steps are high-difficulty. That is one parameter per document and
one per step — far more estimable at our *n* than a full mixture, and it degrades gracefully. And the casualty
MSE review is the closest applied analogue in the entire review, with the right lesson: **when list coverage is
systematically tied to subpopulation identity, stratify, model the coverage mechanism explicitly, and report
that some strata are simply not estimable.**

**Breaks:** Rasch additivity in logits is an assumption, and the classic non-identifiability of the population
total under a Rasch model with an unknown ability distribution is the same wall as §8.5. Casualty MSE has lists
numbering in the thousands of records, nowhere near our regime, and their lists all attempt to record the
*same* event type whereas our document kinds have genuinely different scopes.

### 8.10 MacKenzie, D. I., Nichols, J. D., Lachman, G. B., Droege, S., Royle, J. A. & Langtimm, C. A. "Estimating Site Occupancy Rates When Detection Probabilities Are Less Than One." *Ecology* 83(8), 2002, 2248–2255. DOI [10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2](https://doi.org/10.1890/0012-9658(2002)083%5B2248:ESORWD%5D2.0.CO;2)

Separates true occupancy ψ from per-visit detection probability p using repeat visits to the same sites, with
both allowed to depend on covariates.

**Borrow:** **the best structural match in the review for the existence layer, and the correspondence is
exact.** Latent z_s ∈ {0,1} for "does step *s* exist in this jurisdiction's process" ↔ site occupancy; our
measured π(reveal | kind k, visibility v) ↔ covariate-dependent per-visit detection; reading document *d* ↔ a
visit. The likelihood factorises into (existence × disclosure) precisely as ours does, and **non-detection is
correctly treated as ambiguous rather than as absence** — which is the whole point of our could-have-disclosed
denominator. Adopt this as the core parameterisation.

**Breaks:** three real problems. (i) **Repeat visits are mandatory** — ψ and p separate only because the same
site is visited multiple times, and our "visits" are heterogeneous documents, so the repeat-visit variance must
come from *kinds* re-covering the same step. Which is exactly what our fee schedule (zero new steps, every
time) provides: **keep it in the corpus, because a zero-yield re-read is not a wasted read, it is a
detection-probability observation.** (ii) **Closure** — the process must not change while we read, which fails
if documents span an amendment; date-stamp them and treat amendments as a break. (iii) The classic formulation
has a fixed, known site list, and we do not know our step list — which is why §8.11 is needed.

### 8.11 Dorazio, R. M. & Royle, J. A. "Estimating Size and Composition of Biological Communities by Modeling the Occurrence of Species." *JASA* 100(470), 2005, 389–398. DOI [10.1198/016214505000000015](https://doi.org/10.1198/016214505000000015) — with Dorazio, Royle, Söderström & Glimskär. "Estimating species richness and accumulation by modeling species occurrence and detectability." *Ecology* 87(4), 2006, 842–854. DOI [10.1890/0012-9658(2006)87[842:ESRAAB]2.0.CO;2](https://doi.org/10.1890/0012-9658(2006)87%5B842:ESRAAB%5D2.0.CO;2)

Models community richness with a species-level random effect on **both** occurrence and detectability, and
augments the observed species list with a pool of potentially-present-but-never-detected species, estimating
how many of those are real. The 2006 paper builds **model-based** species-accumulation curves from the fitted
model.

**Borrow:** **this is the estimator we actually want** — the model-based replacement for Chao1, solving the
specific problem Chao1 cannot: it estimates the number of never-detected species *as a parameter*, with
detectability driven by covariates, inside a coherent Bayesian model. Its data-augmentation device — append
M − S_obs all-zero rows and estimate the inclusion probability — drops straight into our sampler as "candidate
steps we have never seen", yielding **a posterior over the number of undiscovered steps rather than a point
lower bound**. It also correctly propagates the correlation between rarity and low detectability, which is the
exact confound that makes staff-only steps dangerous. And the 2006 accumulation curve is the direct fix for our
back-loading problem: instead of interpreting the observed curve, generate the *model-implied* curve and
compare. Under a fitted model with per-kind propensities a back-loaded empirical curve is unsurprising if
document 5 happened to be a high-propensity kind, and the model-implied curve, marginalised over kind order,
will be properly decaying. **That converts our anomaly into a posterior predictive check.**

**Breaks:** the augmentation requires choosing M, the super-population size, and the posterior for N can be
sensitive to it and to the priors on the random-effect variance — **this is Link's ambiguity reappearing as
prior sensitivity**, so it must be reported as a sensitivity curve over M and the hyperpriors, never as a
single number. And the unobserved steps' *visibility class* is itself latent, so the model estimates "how many
undetected steps" only under an assumed class-composition prior. **Be explicit that this prior, not the data,
determines the staff-only count.** The 2006 curve additionally assumes units exchangeable *given covariates*,
so residual non-exchangeability persists if propensity depends on unmodelled features (drafting era, author
office).

Related and worth knowing, for the count-valued generalisation and its documented fragility: Royle, J. A.
"N-Mixture Models for Estimating Population Size from Spatially Replicated Counts." *Biometrics* 60(1), 2004,
108–115. DOI [10.1111/j.0006-341X.2004.00142.x](https://doi.org/10.1111/j.0006-341x.2004.00142.x), and the
caution in Barker, R. J., Schofield, M. R., Link, W. A. & Sauer, J. R. "On the Reliability of N-mixture Models
for Count Data." *Biometrics* 74(1), 2018, 369–377. DOI [10.1111/biom.12734](https://doi.org/10.1111/biom.12734).
**Borrow:** the relevant generalisation if we ever want *counts* of steps of a kind rather than presence of
specific steps — e.g. "how many distinct fee-bearing steps exist" when step identity is not resolvable across
documents, which is a real situation for us. **Breaks:** N-mixture estimates are sensitive to the assumed
abundance distribution and can be poorly identified or inflate without bound when detection is low; with low
disclosure and few replicates this is the wrong risk to take, and it loses the step identity we need for the
order.

### 8.12 Wenger, S. J. & Freeman, M. C. "Estimating species occurrence, abundance, and detection probability using zero-inflated distributions." *Ecology* 89(10), 2008, 2953–2959. DOI [10.1890/07-1127.1](https://doi.org/10.1890/07-1127.1) — with MacKenzie, D. I., Nichols, J. D., Royle, J. A., Pollock, K. H., Bailey, L. L. & Hines, J. E. "Modeling Heterogeneous Detection Probabilities." In *Occupancy Estimation and Modeling*, 2nd ed., 2018, 313–338. DOI [10.1016/B978-0-12-407197-1.00009-0](https://doi.org/10.1016/B978-0-12-407197-1.00009-0)

Zero-inflated formulations separate **structural zeros** (the species genuinely cannot occur) from **sampling
zeros** (it occurs but was not detected). The textbook chapter is the practical reference for finite-mixture and
covariate approaches to heterogeneous detection, including the identifiability hazards.

**Borrow:** the mechanism for our structural-zero concern, and it is the right one. **A staff-only step in an
applicant-facing web page is a structural zero, not a low-probability sampling zero, and conflating the two is
what makes naive estimators overconfident.** Implement disclosure as a two-part model: an indicator of whether
kind *k* can *ever* disclose visibility class *v*, times a propensity given that it can. Our measured 0% cells
should be modelled as structural, with the distinction estimated where we have evidence and assumed where we do
not. The textbook chapter gives the practical guidance on how many mixture components the data support and the
diagnostics for unidentified heterogeneity.

**Breaks:** zero-inflation and detection parameters are weakly separated without a lot of data, so with 5
documents the structural/sampling split for the staff-only × fee-schedule cell will be essentially
prior-determined. **Say so rather than reporting a posterior as if it were learned.**

### 8.13 Integrated models: a structured survey plus a large biased opportunistic sample

- Fithian, W., Elith, J., Hastie, T. & Keith, D. A. "Bias correction in species distribution models: pooling survey and collection data for multiple species." *Methods in Ecology and Evolution* 6(4), 2015, 424–438. DOI [10.1111/2041-210X.12242](https://doi.org/10.1111/2041-210x.12242)
- Dorazio, R. M. "Accounting for imperfect detection and survey bias in statistical analysis of presence-only data." *Global Ecology and Biogeography* 23(12), 2014, 1472–1484. DOI [10.1111/geb.12216](https://doi.org/10.1111/geb.12216)
- Diggle, P. J., Menezes, R. & Su, T.-L. "Geostatistical Inference Under Preferential Sampling." *JRSS Series C* 59(2), 2010, 191–232. DOI [10.1111/j.1467-9876.2009.00701.x](https://doi.org/10.1111/j.1467-9876.2009.00701.x)
- Pacifici, K., Reich, B. J., Miller, D. A. W., Gardner, B., Stauffer, G., Singh, S., McKerrow, A. & Collazo, J. A. "Integrating multiple data sources in species distribution modeling: a framework for data fusion." *Ecology* 98(3), 2017, 840–850. DOI [10.1002/ecy.1710](https://doi.org/10.1002/ecy.1710)
- Miller, D. A. W., Pacifici, K., Sanderlin, J. S. & Reich, B. J. "The recent past and promising future for data integration methods to estimate species' distributions." *Methods in Ecology and Evolution* 10(1), 2019, 22–37. DOI [10.1111/2041-210X.13110](https://doi.org/10.1111/2041-210x.13110)

**This is the most direct existing machinery for combining our official corpus with our reddit corpus.** Fithian
et al. show a small unbiased structured survey can identify and remove the sampling bias in a large
opportunistic presence-only collection, by fitting a *shared* response surface with a separately parameterised,
species-independent observer-effort term. Dorazio 2014 formalises presence-only data as a thinned point process
combining occurrence, detection and effort, and shows what is and is not separable. Diggle et al. show that when
sampling locations depend stochastically on the latent surface being measured (**preferential sampling**), naive
inference is badly biased, and give a joint model that corrects it. Pacifici et al. compare three fusion
strategies; Miller et al. review the linkage assumptions.

**Borrow:** four things, and they are substantial. (i) Fithian et al.'s key insight transfers cleanly: **the
bias term is identified because it is shared across species while the signal is species-specific.** For us the
reddit posting-propensity term is shared across steps (a property of the forum and the case outcome) while step
existence is step-specific — so **pooling over many steps and many jurisdictions is what makes the reddit
selection term estimable, not more reddit data on one step.** That is a concrete design implication: widen
across jurisdictions, do not deepen within one. (ii) Diggle et al. is the sharpest statement of our reddit
problem in generative form — posts occur *because of* the latent process value (bad outcome, long wait → more
likely to post), which is preferential sampling exactly — and their remedy, jointly modelling the data and the
mechanism that generated the sampling, is the same architecture as our generative model. Cite it as the formal
justification for **modelling the posting mechanism rather than reweighting.** (iii) Dorazio 2014 is the
rigorous statement that occurrence, detection and effort are confounded in presence-only data and that
separating them requires either external effort information or a second data type — we *have* the second data
type, which rules out reddit-only inference. (iv) Pacifici et al. identify the failure mode to avoid: **naive
full pooling lets the large biased source dominate and actively degrade the estimate**, and their intermediate
"shared random effect with source-specific parameters" is the right default for us, with "use one source as a
covariate" as a cheap fallback. They also show the small good dataset can be worth more than the large bad one
— the same lesson as §10.18 from another direction.

**Breaks:** and here is the honest gap. Fithian et al.'s identification rests on a **covariate-indexed intensity
surface shared between the two data types, with geography providing the common index. We have no spatial
covariates and no natural shared index.** The nearest substitute is the *visibility-class × step-type* space —
both official documents and reddit posts "sample" from a common step-attribute space — but unlike geography that
space is latent and low-dimensional, so the shared-surface identification is much weaker. **Do not claim this
method transfers until a shared index is specified.** Diggle et al. additionally require a shared latent
Gaussian field, and correcting preferential sampling substantially raises the information demand, so with a
handful of posts per jurisdiction the joint model will be prior-dominated. All of them also assume the sampled
and target quantities are the *same* quantity, which is precisely what our segment mismatch denies (§10.11–
§10.17). And Pacifici et al.'s "high-quality" source is design-unbiased whereas ours (official documents) is
itself systematically censored by visibility class: **we have two biased sources with different biases, which
is a harder problem than the one they solve — though it is also why the biases are potentially mutually
identifying.** Miller et al.'s taxonomy of linkage assumptions is the checklist to run our model against, and it
flags the assumption we are most at risk of violating: that the data types observe the *same* underlying
process.

### 8.14 Unseen support in language, ML and knowledge bases

- Efron, B. & Thisted, R. "Estimating the number of unseen species: How many words did Shakespeare know?" *Biometrika* 63(3), 1976, 435–447. DOI [10.1093/biomet/63.3.435](https://doi.org/10.1093/biomet/63.3.435)
- Valiant, G. & Valiant, P. "Estimating the unseen: an n/log n-sample estimator for entropy and support size, shown optimal via new CLTs." *STOC 2011*, 685–694. DOI [10.1145/1993636.1993727](https://doi.org/10.1145/1993636.1993727); journal version *JACM* 64(6), 2017, 1–41. DOI [10.1145/3125643](https://doi.org/10.1145/3125643)
- Orlitsky, A., Suresh, A. T. & Wu, Y. "Optimal prediction of the number of unseen species." *PNAS* 113(47), 2016, 13283–13288. DOI [10.1073/pnas.1607774113](https://doi.org/10.1073/pnas.1607774113)
- Zou, J., Valiant, G., Valiant, P., *et al.* "Quantifying unobserved protein-coding variants in human populations provides a roadmap for large-scale sequencing projects." *Nature Communications* 7, 2016, 13293. DOI [10.1038/ncomms13293](https://doi.org/10.1038/ncomms13293)
- Luggen, M., Difallah, D., Sarasua, C., Demartini, G. & Cudré-Mauroux, P. "Non-parametric Class Completeness Estimators for Collaborative Knowledge Graphs — The Case of Wikidata." *ISWC 2019*, LNCS, 453–469. DOI [10.1007/978-3-030-30793-6_26](https://doi.org/10.1007/978-3-030-30793-6_26)

Efron & Thisted use an empirical-Bayes negative-binomial/gamma model on word frequencies with careful attention
to how far extrapolation can honestly be pushed. Valiant & Valiant give an LP estimator for the unseen portion
of a distribution with provably optimal sample complexity. **Orlitsky et al. establish the fundamental limit:
a smoothed Good–Toulmin estimator predicts new species reliably for samples enlarged by a factor of about
O(log n), and no estimator can do essentially better.** Zou et al. apply the machinery to exome data explicitly
to size a sequencing project. Luggen et al. apply Chao-type and coverage estimators to Wikidata class
membership, validated against known ground truth.

**Borrow:** four things. (i) **Orlitsky et al. is our quantitative licence for a modest extrapolation and our
defence against an immodest one** — it converts "we cannot say how many steps exist" from hand-waving into a
cited impossibility, and with 5 documents log n is tiny, so we can honestly forecast the next document or two
and nothing beyond. (ii) Valiant & Valiant's **LP formulation naturally accommodates constraints**, so we could
encode "steps in visibility class v have propensity in [a_v, b_v]" as LP constraints and read off the feasible
*range* of total step counts — bounds rather than a point, which suits our epistemic position. (iii) Zou et
al.'s decision framing is the best precedent for turning an unseen-species estimate into a stop/continue
decision: not "how many exist" but "what will the next N samples buy, and is that worth the cost". (iv) Luggen
et al. is the closest existing "how many facts are we missing" application and a direct precedent for
transferring species estimators to extraction coverage — and their use of **class-conditional** estimation (a
separate estimate per class rather than one global number) is exactly the move we need for per-visibility-class
step estimation. Efron & Thisted's methodological honesty — a *bounded* extrapolation, explicit about
dependence on the mixing family — is the model to imitate.

**Breaks:** Orlitsky et al.'s bound is for exchangeable i.i.d. sampling; under our non-exchangeable,
kind-dependent sampling the achievable range is *worse*, so use it as an upper limit on ambition, never a
promise. Valiant & Valiant's guarantees assume i.i.d. sampling and need a support-size cutoff parameter;
honestly, at *n* = 5 it is a theoretically beautiful tool with no purchase. Zou et al. work with ~60,000 exomes,
well inside the O(n log n) regime, and have no structural zeros. Efron & Thisted have one homogeneous corpus and
enormous n. And Wikidata edits are many and roughly exchangeable within a class, with thousands of capture
occasions and **no analogue of a staff-only step no editor can see.**

### 8.15 Decision-theoretic stopping

- Tran, V.-T., Porcher, R., Tran, V.-C. & Ravaud, P. "Predicting data saturation in qualitative surveys with mathematical models from ecological research." *Journal of Clinical Epidemiology* 82, 2017, 71–78.e2. DOI [10.1016/j.jclinepi.2016.10.001](https://doi.org/10.1016/j.jclinepi.2016.10.001); companion Tran, Porcher, Falissard & Ravaud, *JCE* 80, 2016, 88–96, DOI [10.1016/j.jclinepi.2016.07.014](https://doi.org/10.1016/j.jclinepi.2016.07.014)
- Callaghan, M. W. & Müller-Hansen, F. "Statistical stopping criteria for automated screening in systematic reviews." *Systematic Reviews* 9, 2020, 273. DOI [10.1186/s13643-020-01521-4](https://doi.org/10.1186/s13643-020-01521-4)

Tran et al. import species-accumulation and richness estimators from ecology to predict when a qualitative
interview study has reached thematic saturation, and how many more respondents a target coverage needs.
Callaghan & Müller-Hansen develop a hypergeometric-based stopping criterion for machine-assisted literature
screening that bounds the probability that more than a tolerated number of relevant records remain unscreened,
giving a recall-target guarantee.

**Borrow:** Tran et al. is the best methodological precedent for our saturation curve — it establishes in a
peer-reviewed venue that treating "new themes per interview" as a species-accumulation curve is legitimate, and
produces the operational output we want ("n more units to reach coverage c"). Callaghan & Müller-Hansen is the
most directly transplantable stopping rule in the review: **stop reading documents when we can reject, at a
stated confidence, the hypothesis that more than k recoverable steps remain undisclosed.** Endogenous,
explicitly decision-theoretic, and it sidesteps point-estimating the total, which we cannot do anyway.

**Breaks:** Tran et al.'s respondents are exchangeable by design and their themes have no structural zeros;
their saturation curves decay, ours is back-loaded, which is the crux. Callaghan & Müller-Hansen's guarantee
holds over a **closed, enumerable candidate pool** (the search results), which is what makes the hypergeometric
valid; our step universe is open and unenumerated, so the recall guarantee must be restated as conditional on
the revealable universe — the same caveat Chao1 needs.

---

## 9. Non-stationary time series for durations

### 9.1 First, the arithmetic that reframes the area — our 3-year half-life cannot work

The formal correspondence between our recency weighting and a state-space model, worked out, because it settles
the whole question.

**Local-level model.** θₜ = θₜ₋₁ + wₜ, wₜ ~ N(0, W); yₜ = θₜ + vₜ, vₜ ~ N(0, V). Signal-to-noise ratio r = W/V.
In steady state the filter is exactly an EWMA with limiting Kalman gain A, and the steady-state algebra
(R = C+W, Q = R+V, A = R/Q, C = AV) reduces to A² + Ar − r = 0, hence

> **r = W/V = A² / (1 − A)**, with δ = 1 − A the discount factor, and half-life h satisfying δʰ = ½.

**Continuous-time version, which is the one that matters because our observations are irregular.** For a Wiener
signal of variance rate W observed with noise variance V, the Wiener filter has impulse response (α/2)e^(−α|τ|)
with α = √(W/V), so the smoothing kernel is exponential with rate √(W/V) and

> **half-life h ⟺ W/V = (ln 2 / h)².**

For h = 3 years: W/V = (0.6931/3)² = **0.0534 per year**. The discrete calculation gives δ = 2^(−1/3) = 0.7937,
A = 0.2063, W/V = 0.0536 — agreeing to three significant figures. Use the continuous one.

**Now the damaging part.** Take σ_s ≈ 0.5 (a modest log-sd for durations). Then W = 0.0534 × 0.25 = 0.0133/yr,
so the drift sd of μ_s is **0.115 per year** on the log scale — about a 12% median move per year. Our measured
moves are log(1.73) = +0.548 for plan review over ~2 years and log(0.41) = −0.892 for records determinations
over ~1 year. Under our own half-life those are **+3.4σ and −7.7σ events.**

Run it the other way: to make the records-determination move a 1σ event we need drift sd ≈ 0.89/yr, i.e.
W/V = 3.17, i.e. **h ≈ 0.39 years ≈ 5 months** — which discards essentially the entire 1999–2026 corpus.

> **No single half-life can do both jobs.** Long enough to use the data ⇒ too smooth to represent the jumps;
> short enough to catch the jumps ⇒ no data left. This is a proof that the recency weighting in
> `pipeline/priors/latent_timing.py` is not merely crude but **structurally misspecified**, and that what we
> need is a **drift + jump** decomposition with the jumps anchored on known dates — not a retuned half-life.
> The finding is robust to σ, since it follows from the ratio of measured log-shifts to the implied drift sd.

Everything below should be read against that conclusion.

### 9.2 Dynamic linear models and the local-level model

- Harrison, P. J. & Stevens, C. F. "Bayesian Forecasting." *JRSS Series B* 38(3), 1976, 205–228. DOI [10.1111/j.2517-6161.1976.tb01586.x](https://doi.org/10.1111/j.2517-6161.1976.tb01586.x)
- West, M. & Harrison, J. *Bayesian Forecasting and Dynamic Models*, 2nd edn. Springer, 1997. ISBN 0-387-94725-6. DOI [10.1007/b98971](https://doi.org/10.1007/b98971). Ch. 2 "Introduction to the DLM: The First-Order Polynomial Model", 32–67; **Ch. 11 "Intervention and Monitoring", 369–426**; Ch. 12 "Multi-Process Models", 427–488
- Durbin, J. & Koopman, S. J. *Time Series Analysis by State Space Methods*, 2nd edn. OUP, 2012. DOI [10.1093/acprof:oso/9780199641178.001.0001](https://doi.org/10.1093/acprof:oso/9780199641178.001.0001)
- Petris, G., Petrone, S. & Campagnoli, P. *Dynamic Linear Models with R*. Springer, 2009. DOI [10.1007/b135794](https://doi.org/10.1007/b135794). Ch. 4 "Models with unknown parameters", 143–206

Harrison & Stevens found the Bayesian DLM and already contain the **multi-process** idea: at each time the model
is one of several candidates (no change / level shift / slope change / outlier) with a discrete prior, and
inference averages over them. West & Harrison Ch. 2 is the local-level model and its EWMA/discount reading;
Ch. 11 is automatic monitoring plus *feed-forward* intervention when an event is known in advance and
*feed-back* when detected after the fact; Ch. 12 is the multi-process machinery. Durbin & Koopman is the
definitive treatment, and handles **missing observations and irregular spacing by skipping the observation step
and iterating the prediction step**. Petris et al. give forward-filtering-backward-sampling and Gibbs samplers
for unknown V and W.

**Borrow:** four concrete things. (i) The **discount factor ↔ W/V correspondence** in book form — cite it as the
formal version of our half-life and replace the ad-hoc weighting with an estimated δ. (ii) **West & Harrison's
feed-forward intervention is the cheapest implementable idea in this entire area:** at a statutory amendment
date, inflate the state variance for one step (or add a jump with its own prior), letting the level move without
contaminating the pre-period. (iii) The **multi-process Class II** framing is the cleanest formalisation of
"usually drifting, occasionally jumping", and its outlier regime gives free robustness to the one bad permit log
we will inevitably have. (iv) Durbin & Koopman's missing-observation device is the correct and trivially simple
way to handle irregular spacing: put the state on a monthly grid and let transition variance accumulate as
W·Δ across gaps; their diffuse initialisation is the honest way to start a key whose first observation is its
only anchor, and **disturbance smoothing gives exactly the object we want to report — a posterior for *where*
the level moved — without committing to a discrete changepoint.** Petris et al.'s FFBS is the right inner Gibbs
step, since conditional on pooled (V, W) the latent path is exactly conjugate.

**Breaks:** all four are relentlessly about **one reasonably long univariate series at a time**, with hierarchy
either thin or absent — and hierarchy is where all our information lives. The monitoring machinery needs a run
of observations to accumulate evidence; on a key with 3 points the cumulative Bayes factor never leaves its
starting value. Conjugate updating also assumes a Gaussian observation, which our quantile-constraint and
interval-censored objects are not, so we lose closed form and with it the reason to prefer a DLM over HMC. And
the discount idiom makes W a *deterministic* function of the current posterior variance, which is elegant in a
filter and awkward in a joint hierarchical posterior where we want one pooled W across keys. Durbin & Koopman's
missing-data treatment assumes missingness is incidental, not that 99.9% of the monthly grid is empty.

### 9.3 Irregular spacing done properly, and the one structural match

- Särkkä, S. & Solin, A. *Applied Stochastic Differential Equations*. CUP, IMS Textbooks 10, 2019. DOI [10.1017/9781108186735](https://doi.org/10.1017/9781108186735)
- Kelly, B. C., Becker, A. C., Sobolewska, M., Siemiginowska, A. & Uttley, P. "Flexible and Scalable Methods for Quantifying Stochastic Variability in the Era of Massive Time-Domain Astronomical Data Sets." *The Astrophysical Journal* 788(1), 2014, 33. DOI [10.1088/0004-637X/788/1/33](https://doi.org/10.1088/0004-637X/788/1/33)
- **Jones, R. H. & Ackerson, L. M. "Serial correlation in unequally spaced longitudinal data." *Biometrika* 77(4), 1990, 721–731. DOI [10.1093/biomet/77.4.721](https://doi.org/10.1093/biomet/77.4.721)** — with Jones, R. H. & Boadi-Boateng, F. "Unequally spaced longitudinal data with AR(1) serial correlation." *Biometrics* 47(1), 1991, 161–. DOI [10.2307/2532504](https://doi.org/10.2307/2532504)

Särkkä & Solin give the exact discretisation of linear SDEs over arbitrary Δ and the Matérn/OU ↔ state-space
correspondence. Kelly et al. is the reference implementation of Bayesian **CARMA** fitted to irregularly
sampled, heteroscedastically-noisy light curves via a state-space representation and MCMC. **Jones & Ackerson
is the closest structural match in the entire review, and it is 35 years old:** many short, unequally spaced
series, modelled as a continuous-time AR(1) (Ornstein–Uhlenbeck) latent process observed with noise, fitted by a
Kalman filter whose transition and innovation variance are functions of the observed gap, and — the key point —
**with the dynamics parameters pooled across subjects while the levels are random effects.**

**Borrow:** the recipe, essentially as the architecture we should build. State evolves as OU or Wiener in
continuous time; over a gap Δ the transition is e^(−Δ/τ) with innovation variance depending on Δ; each series
contributes its own likelihood via a Kalman filter on its own irregular times; **and (τ, W, V) are shared across
all series and estimated from the panel.** Take Jones & Ackerson as the template and the "does state-space work
with n = 3?" question dissolves: it works if and only if the dynamics are pooled. From Särkkä & Solin take the
two discretisation formulae that make our irregular-time likelihood exact (Wiener: identity transition,
innovation variance W·Δ; OU: e^(−Δ/τ), innovation (Wτ/2)(1 − e^(−2Δ/τ))), plus the GP↔SSM correspondence, which
means we lose nothing by writing drift as a GP prior over calendar time — a form that composes much more
naturally with a hierarchical model in a PPL. From Kelly et al. take the state-space CARMA representation, which
gives a legitimate likelihood at arbitrary observation times with no grid discretisation and accommodates
**per-observation measurement-error variances** — which maps directly onto our heterogeneous object types, where
a published p50 over 4,000 permits has far smaller effective observation variance than a single forum post.

**Breaks:** Jones & Ackerson is Gaussian-observation only, its pooling is a simple random intercept rather than a
six-dimensional crossed hierarchy, it is frequentist REML so gives no posterior, and **it has no jump
component** — OU drifts and reverts, it does not jump, so it handles our backlog drift but not our
amendment jumps. Kelly et al.'s entire scalability argument is about *n* being large (10²–10⁵ points per
object), with no hierarchy across objects and no jumps: applying CARMA per step key on 3 points is not a small
extrapolation but a category error. Särkkä & Solin is a methods text with no statistical-modelling content.

### 9.4 Switching and regime change

- Hamilton, J. D. "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle." *Econometrica* 57(2), 1989, 357–. DOI [10.2307/1912559](https://doi.org/10.2307/1912559) *(**UNVERIFIED end page** — neither Crossref nor OpenAlex records one)*
- Kim, C.-J. & Nelson, C. R. *State-Space Models with Regime Switching.* MIT Press, 1999. DOI [10.7551/mitpress/6444.001.0001](https://doi.org/10.7551/mitpress/6444.001.0001) *(the MIT Press Crossref record lists a garbled second author; the pair Chang-Jin Kim and Charles R. Nelson is confirmed via OpenAlex and a JASA review, DOI [10.2307/2669796](https://doi.org/10.2307/2669796))*
- Frühwirth-Schnatter, S. *Finite Mixture and Markov Switching Models.* Springer, 2006. DOI [10.1007/978-0-387-35768-3](https://doi.org/10.1007/978-0-387-35768-3)
- Ghahramani, Z. & Hinton, G. E. "Variational Learning for Switching State-Space Models." *Neural Computation* 12(4), 2000, 831–864. DOI [10.1162/089976600300015619](https://doi.org/10.1162/089976600300015619)
- Fox, E. B., Sudderth, E. B., Jordan, M. I. & Willsky, A. S. "A sticky HDP-HMM with application to speaker diarization." *Annals of Applied Statistics* 5(2A), 2011. DOI [10.1214/10-AOAS395](https://doi.org/10.1214/10-aoas395)

Hamilton's Markov-switching autoregression has an unobserved discrete state following a Markov chain, with
observation parameters changing with the state. Kim & Nelson is the practitioner's manual combining Kalman
filtering with switching, including the Kim filter and Gibbs sampling over the discrete path.
Frühwirth-Schnatter is the comprehensive Bayesian reference on label switching, identifiability, priors on
transition matrices, and model selection for the number of components. Ghahramani & Hinton give a structured
variational approximation decoupling the discrete and continuous chains. Fox et al. add a self-transition bias κ
to the HDP-HMM so the nonparametric model prefers **persistent** states rather than fragmenting into spurious
short-lived regimes.

**Borrow:** three things, all conceptual. (i) Two states — "normal" and "backlogged" — with a persistent
transition matrix is a **far better description of a permit process than a random walk**: backlogs are
*episodes*; they build and clear, and the process returns to a baseline rather than wandering. (ii)
Frühwirth-Schnatter's treatment of **label switching and identifying constraints** is what stops a two-regime
backlog model from being nonsense (you need an ordering constraint such as μ_backlogged > μ_normal), and her
discussion of priors on transition matrices under sparse data matters because **with our data the persistence
prior *is* the posterior**, so choose it deliberately and report it as an assumption. (iii) Fox et al.'s
diagnosis is the transferable part and applies directly: without a stickiness prior, a nonparametric regime
model creates many redundant short-lived states — so **if we ever fit an unknown number of regimes, a
persistence prior is mandatory, not optional.** Kim & Nelson's exposition of why the exact filter for a
switching state-space model is intractable (paths growing as K^T) is the clearest available.

**Breaks:** Hamilton has ~130 quarters to estimate a 2×2 transition matrix; **we would observe approximately
zero transitions per key**, and Markov-switching is defined on a regular index — with gaps of 1 month to 8
years there is no "period". Exponentiating a generator over Δ fixes that formally, but then we are estimating a
generator from a panel where most keys have one or two observations. Frühwirth-Schnatter's honest message is
discouraging for us: mixture and switching models need substantial data per component, marginal likelihoods for
the number of components are prior-sensitive, and posteriors are frequently multimodal — **on 620 observations
across 86 keys, the number of regimes will not be identified by the data under any prior we could defend.**
Ghahramani & Hinton's variational approximation understates posterior uncertainty, which is the failure mode we
are leaving empirical Bayes to escape. And a sticky HDP-HMM is flatly unusable at our scale: with ≤2
observations in 51 of 86 keys it would return the prior with a much harder sampler. Cite Fox et al. for the
persistence insight; do not implement it.

### 9.5 Bayesian changepoints with unknown times

- Chib, S. "Estimation and comparison of multiple change-point models." *Journal of Econometrics* 86(2), 1998, 221–241. DOI [10.1016/S0304-4076(97)00115-2](https://doi.org/10.1016/S0304-4076(97)00115-2)
- Barry, D. & Hartigan, J. A. "Product Partition Models for Change Point Problems." *Annals of Statistics* 20(1), 1992. DOI [10.1214/aos/1176348521](https://doi.org/10.1214/aos/1176348521) — with "A Bayesian Analysis for Change Point Problems." *JASA* 88(421), 1993, 309–319. DOI [10.1080/01621459.1993.10594323](https://doi.org/10.1080/01621459.1993.10594323)
- Fearnhead, P. "Exact and efficient Bayesian inference for multiple changepoint problems." *Statistics and Computing* 16(2), 2006, 203–213. DOI [10.1007/s11222-006-8450-8](https://doi.org/10.1007/s11222-006-8450-8) — with Fearnhead, P. & Liu, Z. "On-Line Inference for Multiple Changepoint Problems." *JRSS Series B* 69(4), 2007, 589–605. DOI [10.1111/j.1467-9868.2007.00601.x](https://doi.org/10.1111/j.1467-9868.2007.00601.x)
- Adams, R. P. & MacKay, D. J. C. "Bayesian Online Changepoint Detection." arXiv:[0710.3742](https://arxiv.org/abs/0710.3742), 2007. **Preprint only.**
- Saatçi, Y., Turner, R. D. & Rasmussen, C. E. "Gaussian Process Change Point Models." *ICML 2010*, 927–934. No DOI *(verified via OpenAlex and by direct text extraction from the author copy at <https://mlg.eng.cam.ac.uk/pub/pdf/SaaTurRas10.pdf>)*
- Ko, S. I. M., Chong, T. T. L. & Ghosh, P. "Dirichlet Process Hidden Markov Multiple Change-Point Model." *Bayesian Analysis* 10(2), 2015. DOI [10.1214/14-BA910](https://doi.org/10.1214/14-ba910)

Chib recasts a K-changepoint model as an HMM on K+1 states with an **upper-triangular, forward-only** transition
matrix, so inference is standard forward-backward and Gibbs, and models with different K are compared by
marginal likelihood. Barry & Hartigan place a prior directly on the *partition* of the time index into
contiguous blocks, factorising as a product of block-specific cohesions. Fearnhead shows that with independent
segments and computable segment marginal likelihoods, the posterior over the number and positions of
changepoints can be computed **exactly** by an O(n²) recursion with direct simulation — no MCMC, no reversible
jump; Fearnhead & Liu make it online by a particle filter with optimal resampling. Adams & MacKay's BOCPD
maintains a recursive posterior over **run length** given a hazard function and a segment predictive. Saatçi et
al. add GP segment models so the predictive can carry **within-regime temporal correlation**. Ko et al. add a
Dirichlet-process prior over segment parameters so segments can *share* parameters.

**Borrow:** four things, in descending practical value. (i) **Chib's forward-only HMM representation is the most
implementable idea in the changepoint literature for us:** it means we can **marginalise the discrete regime
assignment analytically with the forward algorithm inside Stan or NumPyro** — no reversible jump, no discrete
sampling, full HMC on the continuous parameters. Fix K small (0, 1, 2) per task type, anchor the transition
probabilities on known event dates, and compare K by a bridge-sampled or stacking criterion. (ii) **Barry &
Hartigan's cohesions can be set independently for each gap**, so we can encode "0.7 prior probability of a level
shift at the gap containing the 2024 ordinance revision, 0.02 at every other gap" with no special machinery —
our known/unknown changepoint mixture, expressed in a prior, for free. And a posterior over *partitions* is a
more honest reporting object than point-estimated changepoint locations. (iii) **Fearnhead's exact recursion on
a coarse grid is attractive and cheap:** our corpus spans 1999–2026, which is 108 quarterly candidate points, so
the O(n²) recursion over ~10⁴ segment likelihoods is instantaneous, and it is by far the cleanest way to get an
unknown-changepoint posterior for our handful of data-rich keys. From Fearnhead & Liu take one structural
advantage over BOCPD: **their particles carry changepoint *times*, not run *lengths* in observation counts**, so
the extension to irregular calendar time is natural — replace the geometric run-length prior with a
continuous-time hazard exp(−λΔt). (iv) Ko et al.'s **parameter sharing across segments** is the feature we
actually want and that Barry–Hartigan and Fearnhead lack: a backlog builds and then *clears*, returning the
level to roughly where it was, so a model where segment 3 can share segment 1's parameter captures this whereas
independent-segment models must re-learn the baseline from post-clearance data we do not have. And Saatçi et al.
supply the essential warning: **plain BOCPD assumes observations within a regime are exchangeable, which is
false when the level drifts inside a regime** — so a changepoint model with i.i.d. segments will mistake slow
drift for a sequence of small changepoints and **over-segment**.

**Breaks:** marginal likelihoods on 620 observations with 86 group-level parameters are prior-sensitive enough
that K-selection becomes an artefact of our hyperpriors. Barry & Hartigan's **block independence is badly wrong
for us** — after an amendment processing time changes *somewhat*, it does not redraw from the prior, and with 3
observations a prior-independent post-change block mean is just the prior mean; replacing block independence
with a jump prior (μ_new = μ_old + jump, jump ~ N(0, ω²), ω pooled across keys) means we are no longer using a
product partition model, only its partition prior. Fearnhead's exactness depends on conjugacy *and* segment
independence, both of which fail for us — our five object types destroy conjugacy, and while segment
likelihoods can be computed numerically, the O(n²) recursion then becomes O(n²) numerical integrations and the
appeal evaporates; there is also no hierarchy, so the segment prior cannot be learned from the panel inside the
recursion. Fearnhead & Liu's "online" solves a problem we do not have — we have a static corpus of 620
historical observations, and at that size the exact recursion is faster than setting up a particle filter.
Saatçi et al. need enough points per regime to fit a GP length-scale; with 3 points the drift-vs-jump
distinction their model is designed to make is exactly the distinction our per-key data cannot support. And Ko
et al.'s DP-HMM infers a changepoint count driven by the concentration parameter, not the data — a good idea in
a package we cannot afford to run.

Demoted, with one-line verdicts, all verified: **Green, P. J. "Reversible jump Markov chain Monte Carlo
computation and Bayesian model determination." *Biometrika* 82(4), 1995, 711–732. DOI
[10.1093/biomet/82.4.711](https://doi.org/10.1093/biomet/82.4.711)** — **do not use it.** RJMCMC needs
hand-designed trans-dimensional proposals, mixes poorly with short segments, gives no gradient-based inference,
and **cannot be expressed in Stan or any HMC-based PPL**, so adopting it means abandoning our hierarchy's
sampler. Every objective it serves here is better served by a spike-and-slab or regularised-horseshoe prior on
jump magnitudes over a fixed dense grid of candidate dates — dimension-fixed, differentiable, composable.
**Killick, R., Fearnhead, P. & Eckley, I. A. "Optimal Detection of Changepoints With a Linear Computational
Cost." *JASA* 107(500), 2012, 1590–1598. DOI
[10.1080/01621459.2012.737745](https://doi.org/10.1080/01621459.2012.737745)** (PELT) — run it only as a named
baseline on the data-rich keys; its penalty and consistency are asymptotic in *segment length*, so at 3
observations the penalty is arbitrary and the method returns whatever the penalty dictates, with no uncertainty.
**Truong, C., Oudre, L. & Vayatis, N. "Selective review of offline change point detection methods." *Signal
Processing* 167, 2020, 107299. DOI
[10.1016/j.sigpro.2019.107299](https://doi.org/10.1016/j.sigpro.2019.107299)** — use as the map of the area.

### 9.6 Known changepoints: intervention analysis and interrupted time series — *the sub-area to build on*

- Box, G. E. P. & Tiao, G. C. "Intervention Analysis with Applications to Economic and Environmental Problems." *JASA* 70(349), 1975, 70–79. DOI [10.1080/01621459.1975.10480264](https://doi.org/10.1080/01621459.1975.10480264)
- Lopez Bernal, J., Cummins, S. & Gasparrini, A. "Interrupted time series regression for the evaluation of public health interventions: a tutorial." *International Journal of Epidemiology* 46(1), 2017, 348–355. DOI [10.1093/ije/dyw098](https://doi.org/10.1093/ije/dyw098); **corrigendum** *IJE* 50(3), 2020, 1045, DOI [10.1093/ije/dyaa118](https://doi.org/10.1093/ije/dyaa118); controls companion *IJE* 47(6), 2018, 2082–2093, DOI [10.1093/ije/dyy135](https://doi.org/10.1093/ije/dyy135)
- Brodersen, K. H., Gallusser, F., Koehler, J., Remy, N. & Scott, S. L. "Inferring causal impact using Bayesian structural time-series models." *Annals of Applied Statistics* 9(1), 2015. DOI [10.1214/14-AOAS788](https://doi.org/10.1214/14-aoas788); R package `CausalImpact`, DOI [10.32614/CRAN.package.causalimpact](https://doi.org/10.32614/CRAN.package.causalimpact)

Box & Tiao: **when the intervention date is known you do not need to detect anything** — write the series as a
noise process plus a deterministic intervention component (step, pulse, or gradually-accruing response) and
estimate its magnitude and shape as ordinary parameters. Lopez Bernal et al. give the applied-policy version: a
regression with a time trend, a level-change indicator, and a slope-change term, with guidance on
autocorrelation, seasonality, lag/transition periods and required numbers of points. Brodersen et al. fit a
local-level state-space model with regression on control series to the *pre*-intervention period, forecast the
counterfactual with full posterior uncertainty, and use spike-and-slab priors for control selection.

**Borrow:** five things, and this is where I would start.
1. **Our statutory amendment dates are known, so the changepoint locations are data, not parameters.** That
   removes the model-dimension problem entirely — no RJMCMC, no run-length posterior, no marginal-likelihood
   comparison over K. Add one jump parameter per known event and estimate it.
2. Box & Tiao's **taxonomy of response shapes** is directly useful and defensible from institutional facts
   rather than estimated: a fee change is a *step*; a software launch is a *pulse followed by recovery*
   (transient degradation while staff learn the system, then improvement); a staffing cut is a *ramp*.
3. The ITS **level-change + slope-change** parameterisation separates our two phenomena cleanly — the slope term
   is drift, the level term is the jump — and it is two coefficients.
4. Their insistence on an explicit **transition/lag period** around the intervention (exclude, say, ±6 months)
   addresses the effective-date ambiguity, which is real: an amendment's effective date, its compliance date,
   and the date agencies actually change practice can differ by a year or more.
5. **The 2018 controls companion maps onto a real design opportunity and is the single highest-value idea in
   this section for our data volume:** when an amendment affects plan review but not records determinations, the
   unaffected step keys are a control group, and a difference-in-differences on the pooled panel identifies the
   jump far better than the affected keys' own 3 observations do.
   From Brodersen et al., take the **spike-and-slab prior over which controls matter** and re-purpose it: put a
   sparsity prior over *which candidate jump dates actually produced a jump*. A dense grid of candidate times,
   each with a spike-and-slab or regularised-horseshoe prior on its magnitude, with much higher prior inclusion
   probability at dated statutory events than at arbitrary quarters, gives us **known and unknown changepoints
   in one differentiable model with no reversible jump** — the modern, gradient-friendly replacement for
   everything in §9.5, and it composes directly with our hierarchy.

**Breaks:** the ITS tutorial targets regularly-spaced aggregate series with a rule of thumb of ~8+ points each
side, and it is frequentist OLS/GLM with Newey–West or ARIMA errors and no hierarchy, so borrow the *design*,
not the estimator. Box & Tiao's noise model is ARIMA on a regular moderately long single series, and with 3
observations per key the intervention effect is not estimable *per key* — it must be pooled across keys sharing
that event. `CausalImpact` needs a long pre-period (hundreds of daily points) and good *contemporaneously
measured* controls; our controls are other step keys with their own 3-observation sparsity, so the
regression-on-controls component has no data, and the model is single-series-with-covariates on a regular grid,
not a panel. **One more caution: ITS is a *causal* design with strong assumptions (no concurrent shocks,
correct counterfactual trend) that we are not positioned to defend. We want a descriptive non-stationarity
model, and the ITS framing must not tempt us into causal claims about the amendments — that is a different
paper.**

### 9.7 Duration- and calendar-specific non-stationarity

- Friedman, M. "Piecewise Exponential Models for Survival Data with Covariates." *Annals of Statistics* 10(1), 1982. DOI [10.1214/aos/1176345693](https://doi.org/10.1214/aos/1176345693)
- Ibrahim, J. G., Chen, M.-H. & Sinha, D. *Bayesian Survival Analysis.* Springer, 2001. DOI [10.1007/978-1-4757-3447-8](https://doi.org/10.1007/978-1-4757-3447-8)
- Demarqui, F. N., Loschi, R. H. & Colosimo, E. A. "Estimating the grid of time-points for the piecewise exponential model." *Lifetime Data Analysis* 14(3), 2008, 333–356. DOI [10.1007/s10985-008-9086-0](https://doi.org/10.1007/s10985-008-9086-0); dynamic version *JSPI* 142(3), 2012, 728–742, DOI [10.1016/j.jspi.2011.09.006](https://doi.org/10.1016/j.jspi.2011.09.006)
- Carstensen, B. "Age–period–cohort models for the Lexis diagram." *Statistics in Medicine* 26(15), 2007, 3018–3045. DOI [10.1002/sim.2764](https://doi.org/10.1002/sim.2764)

Friedman establishes the asymptotic theory for piecewise-constant hazards with covariates; Ibrahim, Chen & Sinha
is the standard Bayesian survival reference (gamma-process and correlated hazard increments, AFT models,
interval-censored likelihoods). Demarqui et al. make the interval boundaries unknown, importing a **product
partition prior** onto a survival model's time axis. Carstensen sets out how rates depend simultaneously on
time-since-entry, calendar period and cohort, and confronts the fundamental **non-identifiability** (age +
cohort = period exactly).

**Borrow:** three things. (i) The **correlated prior on hazard increments** (each interval's log-hazard a random
walk on the previous) is the survival analogue of the local-level model and the correct way to make a piecewise
model behave — independent gamma priors per interval produce wildly noisy estimates on sparse data. (ii) The
interval-censored likelihood in a survival idiom is exactly the term for our prose ranges: L = S(t_lower) −
S(t_upper), which for a lognormal is Φ((log t_u − μ)/σ) − Φ((log t_l − μ)/σ). Exact, no approximation. (iii)
Demarqui et al. confirm that PPM-partition-prior-plus-duration-model is a known working construction rather
than something we would be inventing. (iv) **Carstensen's conceptual correction, which is a live threat to our
headline finding and should be checked.** Our durations live on a Lexis diagram: a permit has a *duration* axis
and a *calendar* axis, our non-stationarity is a **period effect on the calendar axis**, and we must decide
whether μ_s is indexed by the *application* date or the *completion* date. **A permit filed in 2024 and
completed in 2026 is evidence about 2024–2025 conditions; indexing by completion date systematically attributes
slow permits to later periods, manufacturing a spurious slowdown trend — and we have reported a 1.73×
slowdown.** He also warns that a smooth calendar trend and a duration-dependent hazard are partially
confounded.

**Breaks:** the piecewise-exponential apparatus discretises *duration* time (the hazard of a permit still being
open at day 40), not *calendar* time, which is the wrong axis for our question, and its exponential
within-interval hazard contradicts the non-monotone hazard of our LogNormal — trading a defensible parametric
assumption for flexibility we cannot afford at 3 observations per key. Demarqui et al.'s partition is likewise
over duration time, with hundreds of subjects in a single population and a custom Gibbs sampler not expressible
in a gradient-based PPL; their own sensitivity analyses show that with sparse data the inferred grid is largely
the prior's. Carstensen is epidemiological, aggregate, count-data, and non-Bayesian: one conceptual borrow plus
one warning, not a method.

### 9.8 Fitting from quantiles, intervals and coarse data — *the most actionable sub-area, and the one to avoid*

- **Heitjan, D. F. & Rubin, D. B. "Ignorability and Coarse Data." *Annals of Statistics* 19(4), 1991. DOI [10.1214/aos/1176348396](https://doi.org/10.1214/aos/1176348396)**; applied companion *Biometrics* 49(4), 1993, 1099, DOI [10.2307/2532251](https://doi.org/10.2307/2532251)
- Hozo, S. P., Djulbegovic, B. & Hozo, I. "Estimating the mean and variance from the median, range, and the size of a sample." *BMC Medical Research Methodology* 5, 2005, 13. DOI [10.1186/1471-2288-5-13](https://doi.org/10.1186/1471-2288-5-13)
- Wan, X., Wang, W., Liu, J. & Tong, T. "Estimating the sample mean and standard deviation from the sample size, median, range and/or interquartile range." *BMC Medical Research Methodology* 14, 2014, 135. DOI [10.1186/1471-2288-14-135](https://doi.org/10.1186/1471-2288-14-135)
- McGrath, S., Zhao, X., Steele, R., Thombs, B. D., Benedetti, A. *et al.* "Estimating the sample mean and standard deviation from commonly reported quantiles in meta-analysis." *SMMR* 29(9), 2020, 2520–2537. DOI [10.1177/0962280219889080](https://doi.org/10.1177/0962280219889080); and "Standard error estimation in meta-analysis of studies reporting medians." *SMMR* 32(2), 2022, 373–388. DOI [10.1177/09622802221139233](https://doi.org/10.1177/09622802221139233)
- Gómez, G., Calle, M. L., Oller, R. & Langohr, K. "Tutorial on methods for interval-censored data and their implementation in R." *Statistical Modelling* 9(4), 2009, 259–297. DOI [10.1177/1471082X0900900402](https://doi.org/10.1177/1471082x0900900402)
- O'Hagan, A., Buck, C. E., Daneshkhah, A., Eiser, J. R., Garthwaite, P. H., Jenkinson, D. J., Oakley, J. E. & Rakow, T. *Uncertain Judgements: Eliciting Experts' Probabilities.* Wiley, 2006. DOI [10.1002/0470033312](https://doi.org/10.1002/0470033312)
- Jackson, C., Best, N. & Richardson, S. "Hierarchical Related Regression for Combining Aggregate and Individual Data in Studies of Socio-Economic Disease Risk Factors." *JRSS Series A* 171(1), 2008, 159–178. DOI [10.1111/j.1467-985X.2007.00500.x](https://doi.org/10.1111/j.1467-985X.2007.00500.x); R package `ecoreg`, DOI [10.32614/CRAN.package.ecoreg](https://doi.org/10.32614/CRAN.package.ecoreg)
- Drovandi, C. C. & Pettitt, A. N. "Likelihood-free Bayesian estimation of multivariate quantile distributions." *CSDA* 55(9), 2011, 2541–2556. DOI [10.1016/j.csda.2011.03.019](https://doi.org/10.1016/j.csda.2011.03.019)

**Borrow, in four parts.**

1. **Heitjan & Rubin give the unifying framework and the right vocabulary.** Our five object types are five
   *coarsening mechanisms* applied to the same latent duration, and the general likelihood contribution is
   P(D ∈ Cᵢ | μ_s, σ_s) for the coarsening set Cᵢ. That one expression unifies samples (C = {d}),
   interval-censored prose (C = [t_l, t_u]) and rounding (C = [d − 0.5, d + 0.5] on whatever grid the source
   used) — and it justifies rounding-aware likelihoods, which we need, because fitting a continuous lognormal to
   month-rounded data inflates σ̂.
2. **Do NOT use the meta-analysis quantile-to-moment methods; they lose information we do not have to lose.**
   Those methods exist because meta-analysts need a mean and SD for an inverse-variance combination under a
   normality assumption. We have a parametric model, and for D ~ LogNormal(μ, σ²) published percentiles invert
   in closed form with zero approximation: **μ = log p₅₀ and σ = (log p₉₀ − log p₅₀)/1.28155.** Better still,
   treat the published pair as a **bivariate noisy order statistic**: for log-durations ~ N(μ, σ²) from an
   underlying sample of size n, (log p̂₅₀, log p̂₉₀) is approximately bivariate normal with mean
   (μ, μ + 1.28155σ) and covariance (σ²/n)·Σ where Σ₁₁ ≈ 1.5708, Σ₂₂ ≈ 2.9221, Σ₁₂ ≈ 0.7142. That is a
   two-line, exact, uncertainty-propagating likelihood for a published-percentile observation; it degrades
   gracefully when n is only bounded rather than known; and it is strictly better than anything in
   Hozo/Wan/McGrath. **Cite those papers to explain what we are not doing and why** — and take from McGrath et
   al. 2022 the one idea that matters: **a published quantile carries sampling uncertainty depending on the
   underlying n, so a p50 over 40 permits must not enter with the same weight as a p50 over 40,000.**
3. **O'Hagan et al. is the correct home for prose ranges, and this is the framing we were missing.** "Typically
   4 to 6 weeks" in an agency FAQ is **not data; it is an elicited judgement from a non-calibrated expert.**
   The elicitation literature then tells us what to expect: elicited ranges are *reliably too narrow*
   (overconfidence is the field's most robust finding), so treating "4 to 6 weeks" as p10–p90 will understate σ
   and we should widen it or treat the endpoints as p25–p75; round numbers signal coarse judgement, so "4 to 6
   weeks" deserves less weight than "18 to 23 days"; and the right likelihood shape is a **soft constraint with
   an elicitation-error variance, not a hard interval.** Gómez et al. supply the complementary practical
   warning: **"4 to 6 weeks" as a statement about the distribution (a quantile anchor) is a different object
   from a single permit known to have taken between 4 and 6 weeks (an interval-censored observation), and the
   two are not interchangeable.** Decide which it is, per source, and state it — and avoid midpoint imputation,
   whose bias they document.
4. **Jackson, Best & Richardson names what may be our largest single source of bias.** An aggregate statistic
   constrains an *integral* of the individual-level model over the composition of the aggregated population,
   and that composition must be modelled. Concretely: **if an agency publishes one p50 "for building permits"
   and our log is specifically tenant-improvement plan review, that p50 constrains a mixture over step keys
   with unknown weights — not our key's μ_s. Assigning an agency-wide published percentile to one of our 86 step
   keys is precisely the ecological fallacy this paper exists to prevent — and published percentiles are our
   most precise object type.** The fix is theirs: write the aggregate likelihood as a mixture, with weights from
   known application volumes or a Dirichlet prior.

**Breaks.** Heitjan–Rubin ignorability requires the coarsening to be **at random, and ours is almost certainly
not.** An agency writes "4 to 6 weeks" rather than a number precisely *because* the number is variable,
uncertain or unflattering; a forum poster reports an exact day count when the wait was memorable. **The
coarsening mechanism depends on the very quantity being coarsened**, so the face-value interval-censored
likelihood is biased, and the direction is predictable: prose ranges will be systematically narrower and more
optimistic, biasing μ̂ and σ̂ downward. The paper tells us this is a problem; it does not tell us how to fix it,
and the fix requires a selection model with an unidentifiable sensitivity parameter — so the honest move is a
sensitivity analysis across a few assumed tilts, reported as such. Drovandi & Pettitt's ABC route is worth
knowing as a fallback for an object type whose likelihood we genuinely cannot write, and its g-and-k family is a
flexible alternative if durations turn out skew *and* heavy-tailed beyond the lognormal — but **ABC is the wrong
tool here and we should not need it:** it requires many simulations per proposal, is orders of magnitude less
efficient than HMC, introduces a bias-inducing tolerance, and for the lognormal **the quantile likelihood is
available in closed form.** Jackson et al.'s aggregate data come from a known enumerated population with
census-derived covariate distributions; we usually do not know what population a published percentile
aggregates over, so **the mixing weights are unidentified rather than merely uncertain** — the idea is
essential, the machinery is not. And O'Hagan et al.'s debiasing protocols all require a *cooperating* expert who
can be asked follow-up questions, which an archived web page cannot be.

### 9.9 Queue time versus touch time, in continuous time

- Eick, S. G., Massey, W. A. & Whitt, W. "The Physics of the M_t/G/∞ Queue." *Operations Research* 41(4), 1993, 731–742. DOI [10.1287/opre.41.4.731](https://doi.org/10.1287/opre.41.4.731); sinusoidal companion *Management Science* 39(2), 1993, 241–252, DOI [10.1287/mnsc.39.2.241](https://doi.org/10.1287/mnsc.39.2.241); networks, Massey & Whitt, *Queueing Systems* 13(1–3), 1993, 183–250, DOI [10.1007/BF01158933](https://doi.org/10.1007/bf01158933); Erlang-loss MOL, *Annals of Applied Probability* 4(4), 1994, DOI [10.1214/aoap/1177004908](https://doi.org/10.1214/aoap/1177004908)
- Newell, G. F. "Queues with time-dependent arrival rates," I–III. *Journal of Applied Probability* 5, 1968: I, 436–451, DOI [10.2307/3212264](https://doi.org/10.2307/3212264); II, 579–590, DOI [10.2307/3211923](https://doi.org/10.2307/3211923); III, 591–606, DOI [10.2307/3211924](https://doi.org/10.2307/3211924)
- Ibrahim, R. & Whitt, W. "Real-Time Delay Estimation Based on Delay History." *M&SOM* 11(3), 2009, 397–415. DOI [10.1287/msom.1080.0223](https://doi.org/10.1287/msom.1080.0223); time-varying sequel *POM* 20(5), 2011, 654–667, DOI [10.1111/j.1937-5956.2010.01196.x](https://doi.org/10.1111/j.1937-5956.2010.01196.x)

Eick, Massey & Whitt give the exact solution for an infinite-server queue with time-varying Poisson arrivals:
the number in system at *t* is Poisson with mean E[λ(t − Sₑ)]·E[S], where Sₑ is the equilibrium residual service
time. Newell gives diffusion/fluid approximations for queues whose arrival rate crosses capacity. Ibrahim &
Whitt compare estimators of a new arrival's delay built from *observed recent delays* against ones built from
queue length and staffing.

**Borrow:** three things. (i) **The lag structure is the single most useful exact result here:** the system's
state at *t* responds to the arrival rate at a lag equal to the mean residual service time, with amplitude
damped by the ratio of service time to arrival-rate period. Translated: a workload shock shows up in durations
*smeared and delayed by roughly the mean service duration*, so a 2024 staffing cut appears in our 2025
durations, not our 2024 ones — which tells us the **shape** of the response function for §9.6's intervention
model (a lagged, damped, smeared response, not a step), and the network paper is the right formalism for our
multi-stage workflow, where the lag compounds. (ii) **Newell Part I gives the most important qualitative fact
about our problem:** the transition through saturation is *sharply nonlinear*, so a small increase in
application volume past capacity produces a disproportionately large and *persistent* backlog, and the return
to equilibrium is slower than the build-up. **That asymmetry is a testable prediction about our drift and argues
for an asymmetric jump prior — slowdowns larger and more persistent than speedups.** (iii) Ibrahim & Whitt is
directly encouraging: their finding that **recent-delay-history estimators are competitive with, and sometimes
better than, queue-length-based estimators** — because they implicitly absorb unobserved staffing and
service-rate variation — is a formal licence for inferring backlog state from observed durations rather than
acquiring staffing data. Their 2011 sequel shows those estimators degrade under strong time-variation, which
tells us how to hedge: **use a short recency window for the backlog component specifically, even while pooling
the long-run level.**

**Breaks:** infinite-server means **there is no queueing delay at all** — every arrival begins service
immediately — so M_t/G/∞ models the composition of our *touch* time, not our *queue* time, the opposite of what
we want. The finite-server/Erlang-loss extension addresses this but needs the server count *s* and the arrival
rate λ(t), **neither of which we observe**: we observe only elapsed times, so a queueing model is not
identifiable from durations alone without staffing and application-volume data, which is a data-acquisition task
rather than a modelling one. All of it assumes Poisson arrivals, wrong for permit applications with seasonal
construction cycles and deadline-driven bunching. Newell's heavy-traffic asymptotics assume ρ → 1 and a long
window. And Ibrahim & Whitt's "recent delay history" is the last few minutes in a call centre; ours is the last
few years, with three observations in it.

### 9.10 Hierarchical shrinkage for sparse groups — *where our model actually lives*

- Efron, B. & Morris, C. "Data Analysis Using Stein's Estimator and its Generalizations." *JASA* 70(350), 1975, 311–319. DOI [10.1080/01621459.1975.10479864](https://doi.org/10.1080/01621459.1975.10479864); theory companion *JASA* 68(341), 1973, 117–130, DOI [10.1080/01621459.1973.10481350](https://doi.org/10.1080/01621459.1973.10481350)
- Gelman, A. & Hill, J. *Data Analysis Using Regression and Multilevel/Hierarchical Models.* CUP, 2007 *(Crossref dates the monograph 2006)*. DOI [10.1017/CBO9780511790942](https://doi.org/10.1017/cbo9780511790942)
- Betancourt, M. J. & Girolami, M. "Hamiltonian Monte Carlo for Hierarchical Models." In *Current Trends in Bayesian Methodology with Applications*, Chapman & Hall/CRC, 2015, 79–101. DOI [10.1201/b18502-5](https://doi.org/10.1201/b18502-5). arXiv:[1312.0906](https://arxiv.org/abs/1312.0906)
- Gelman, A. "Prior distributions for variance parameters in hierarchical models." *Bayesian Analysis* 1(3), 2006. DOI [10.1214/06-BA117A](https://doi.org/10.1214/06-ba117a)
- McNeish, D. M. & Stapleton, L. M. "The Effect of Small Sample Size on Two-Level Model Estimates: A Review and Illustration." *Educational Psychology Review* 28(2), 2016, 295–314. DOI [10.1007/s10648-014-9287-x](https://doi.org/10.1007/s10648-014-9287-x); companion Hox & McNeish, in *Small Sample Size Solutions*, 2020, 215–225, DOI [10.4324/9780429273872-18](https://doi.org/10.4324/9780429273872-18)

**Borrow:** five things, and together they are the core of the right model.
1. **Efron & Morris give the sanity check, and our numbers are sobering in the right direction.** The shrinkage
   weight on a key's own data is nτ²/(nτ² + σ²). With σ ≈ 0.5 and τ ≈ 0.4, a key with n = 2 gets weight 0.56 on
   its own mean; with n = 1, weight 0.39. So **for our 51 sparse keys roughly half to two-thirds of the
   posterior mean comes from the hierarchy, not the key's own data** — which is the correct answer and also why
   any per-key *time-series* claim for those keys is fiction.
2. **Gelman & Hill's group-level predictors are the answer to sparse cells and the single most important
   structural change I would make.** Rather than 86 independent μ_s, model
   μ_s = α + β_agency[s] + β_task[s] + β_channel[s] + … + ε_s with each β vector partially pooled — an additive
   crossed decomposition of the six-dimensional key that borrows strength across every margin, so a key with 2
   observations inherits nearly all of its estimate from six marginal effects each estimated from dozens of
   observations. **That makes the 51 sparse keys a non-problem.** Their treatment of non-nested (crossed)
   effects is what we need, since agency_class and task_type are crossed, not nested.
3. **Non-centre, but not everywhere.** With 51 of 86 keys at ≤2 observations, the centered parameterisation will
   not sample: divergences concentrate at small τ and τ̂ is biased downward, which over-pools and hides exactly
   the between-key variation we are trying to measure. But Betancourt & Girolami's less-known second half
   matters: non-centering is **not** universally better — for a group with many observations the likelihood
   dominates and centering is better conditioned. **Our keys span 2 to dozens of observations, so the right move
   is a per-group choice: non-centre the sparse keys, centre the data-rich ones.** Few people do this. And their
   divergence diagnostics are our acceptance test: if we cannot sample without divergences, the intervals we
   report are not the intervals of the model we wrote down.
4. **The prior on τ does real work at our sparsity**, so use a half-normal or half-t on the *standard deviation*
   scale, with a scale we can argue for (half-normal(0, 0.5) on the log scale says a 1-sd difference between
   keys is about a 65% difference in median duration). **The same argument applies with more force to the drift
   variance W** — which per §9.1 is the parameter we cannot identify — so choose its prior explicitly, state it,
   and report a sensitivity analysis over it. Do not let W be set by a default.
5. **McNeish & Stapleton answers the brief's "how few observations per group is too few", and the answer is
   better news than expected.** The literature's consistent finding is that **the number of groups is the
   binding constraint, not the group size**: variance components degrade badly below roughly 30–50 groups,
   whereas small within-group n mainly inflates the *uncertainty* of group-specific estimates without biasing
   the variance components. We have 86 groups — comfortably clear — and small within-group n, the benign
   direction. So our hierarchical *mean* structure is fine and groups of size 1–2 are legitimate contributors.
   What is **not** fine is any per-key claim about a key-specific σ_s or a key-specific trend — and the same
   logic says **σ should be pooled far more aggressively than μ.** Estimating 86 separate σ_s from 620
   observations is the part of the current specification I would change first after non-centering.

**Breaks:** Efron & Morris assume a single exchangeable group structure, known V, normal observations, and
empirical Bayes — which is the procedure producing our non-posterior intervals — and with six crossed key
dimensions "the grand mean" is the wrong shrinkage target; we need a structured target (shrink toward the
task_type mean, which shrinks toward the grand mean), which is not in these papers. Gelman & Hill is lme4/BUGS
era with nothing on time dynamics, mixed likelihood types, or the sampling pathologies we will hit, and its
variance-prior advice is dated. Betancourt & Girolami analyse the *simple one-way* normal hierarchical model;
our posterior has six crossed dimensions, a latent time component and five likelihood types, and **the geometry
of that posterior is not characterised anywhere** — in particular a pooled W will have its own funnel with
respect to the per-key latent paths, and the interaction of two funnels is unstudied, so expect to reparameterise
the time component too and to spend real time on it. Gelman 2006 is a four-page comment on the simplest
hierarchical model, and its half-Cauchy recommendation has itself been partly superseded. McNeish & Stapleton
review frequentist ML/REML in two-level nested designs with continuous outcomes — not crossed six-way keys,
censored/quantile likelihoods, or time-varying effects — so its thresholds are orientation, not rules.

---

## 10. Selection-biased sampling, length bias — and, as it turns out, estimand mismatch

### 10.1 Fisher, R. A. "The Effect of Methods of Ascertainment Upon the Estimation of Frequencies." *Annals of Eugenics* 6(1), 1934, 13–25. DOI [10.1111/j.1469-1809.1934.tb02105.x](https://doi.org/10.1111/j.1469-1809.1934.tb02105.x)

The origin of the weighted-distribution idea: when units enter the sample with probability proportional to some
function of their own characteristics, the observed distribution is a *weighted* version of the population one,
and the weight must be part of the likelihood.

**Borrow:** the framing discipline — write the observed community-report distribution explicitly as
g(t) ∝ w(t) f(t) and **name w.** Once w is named it becomes obvious whether we are estimating it or assuming it.
Our wrong-signed tilt is a symptom of having estimated w without having written it down.

**Breaks:** ascertainment there is a known function of an *observed* characteristic. Our w depends on case
outcome and elapsed time, both partially unobserved — and, critically, no weight can repair a mismatch in what
*t* means across sources.

### 10.2 Rao, C. R. "On discrete distributions arising out of methods of ascertainment." 1965. **UNVERIFIED venue** — OpenAlex confirms title, author (C. Radhakrishna Rao) and year but returns no journal, volume or pages; the commonly cited *Sankhyā Series A* 27, 311–324 could **not** be confirmed. Prefer the verified extended treatment: Rao, C. R. "Weighted Distributions Arising Out of Methods of Ascertainment: What Population Does a Sample Represent?" In *A Celebration of Statistics*, Springer, 1985, 543–569. DOI [10.1007/978-1-4613-8560-8_24](https://doi.org/10.1007/978-1-4613-8560-8_24)

Generalises Fisher's ascertainment into the formal theory of weighted distributions, w(x)f(x)/E[w].

**Borrow:** the 1985 chapter's *title* is the question to put at the top of our selection section — **what
population does our reddit sample represent?** If the answer is "applicants whose experienced segment differs
from the published segment", that is a different population *and* a different measurement, and no weight fixes
it.

**Breaks:** weighted-distribution theory presumes the sampled and target variables are the same random variable,
differently weighted. That presumption is what fails for us.

### 10.3 Patil, G. P. & Rao, C. R. "Weighted Distributions and Size-Biased Sampling with Applications to Wildlife Populations and Human Families." *Biometrics* 34(2), 1978, 179–. DOI [10.2307/2530008](https://doi.org/10.2307/2530008) *(Crossref records first page only)*

The applied consolidation: works out size- and length-biased forms for standard families and shows the
characteristic distortions (inflated means, changed shape).

**Borrow:** **the worked LogNormal case turns our anomaly into a falsification test.** Length-biasing a
LogNormal(μ, σ²) yields another LogNormal with μ shifted by **exactly σ²** and σ unchanged. So if community
durations were length-biased we would expect a pure location shift of +σ² in log space with no variance change.
**We measured −0.47 — the wrong sign for length bias entirely.** Run the test, report that length bias is
rejected on sign rather than on judgement, and move on to measurement mismatch.

**Breaks:** size bias with w(t) = t predicts *longer* observed durations. Ours are shorter. So this literature,
applied naively, predicts the opposite of what we see — informative, but not corrective.

### 10.4 Length-biased and prevalent-cohort sampling

- Cox, D. R. "Some sampling problems in technology." In *New Developments in Survey Sampling*, Wiley, 1969. **UNVERIFIED** — not indexed in Crossref, OpenAlex or Semantic Scholar; chapter title, editors and the commonly cited pages 506–527 could not be confirmed. Prefer Vardi (below) or Zelen & Feinleib as the citable anchors.
- Vardi, Y. "Nonparametric Estimation in the Presence of Length Bias." *Annals of Statistics* 10(2), 1982, 616–620. DOI [10.1214/aos/1176345802](https://doi.org/10.1214/aos/1176345802)
- Vardi, Y. "Empirical Distributions in Selection Bias Models." *Annals of Statistics* 13(1), 1985. DOI [10.1214/aos/1176346585](https://doi.org/10.1214/aos/1176346585); extended in Gill, Vardi & Wellner, *Annals of Statistics* 16, 1988, DOI [10.1214/aos/1176350948](https://doi.org/10.1214/aos/1176350948)
- Wang, M.-C. "Nonparametric Estimation from Cross-Sectional Survival Data." *JASA* 86(413), 1991, 130–143. DOI [10.1080/01621459.1991.10475011](https://doi.org/10.1080/01621459.1991.10475011)
- Asgharian, M., M'Lan, C. E. & Wolfson, D. B. "Length-Biased Sampling With Right Censoring: An Unconditional Approach." *JASA* 97(457), 2002, 201–209. DOI [10.1198/016214502753479347](https://doi.org/10.1198/016214502753479347); asymptotics in Asgharian & Wolfson, *Annals of Statistics* 33, 2005, DOI [10.1214/009053605000000372](https://doi.org/10.1214/009053605000000372)
- Zelen, M. & Feinleib, M. "On the theory of screening for chronic diseases." *Biometrika* 56(3), 1969, 601–614. DOI [10.1093/biomet/56.3.601](https://doi.org/10.1093/biomet/56.3.601)

Cox gives the renewal-theoretic inspection paradox. Vardi 1982 derives the nonparametric MLE under length bias;
Vardi 1985 generalises to a broad class of **known** biased-sampling models with multiple samples from
differently-weighted versions of one distribution. Wang handles cross-sectionally sampled (prevalent) cases with
induced length bias and truncation; Asgharian et al. handle length bias combined with right censoring. Zelen &
Feinleib originate length bias in screening, where screen-detected cases over-represent slowly-progressing
disease.

**Borrow:** four things. (i) The inspection paradox is worth stating as **the null we reject**: if our forum
sample were a cross-section of in-progress cases, long cases would be over-represented and reported durations
biased *long*. They are not. (ii) **Vardi 1985's multi-sample structure is formally very close to ours** —
several samples (document kinds, forum, traces) drawn from differently-weighted versions of one underlying
duration distribution, with a common NPMLE. It is the cleanest existing formalism for *pooling* our
heterogeneous sources, and it tells us exactly what we would need: the weight functions up to known form. (iii)
**Wang's truncation bookkeeping is the one selection story consistent with our sign:** our forum posts are
left-truncated in a real sense, because cases that have not yet reached the posting-triggering event cannot
appear, which systematically excludes the longest in-progress cases and pushes observed durations *shorter*.
Worth separating explicitly from segment mismatch. Asgharian et al. is then the right reference for the fact that
*unresolved* cases are informatively absent — treating observed durations as complete is the error. (iv) Zelen
& Feinleib is the cleanest pedagogical example of a selection artifact that **masquerades as a real effect**, and
the discipline of decomposing an observed difference into length bias, lead time and true effect is exactly the
three-way decomposition we should do on the −0.47: truncation of unresolved cases, segment mismatch, and any
residual outcome-dependent selection.

**Breaks:** renewal-theoretic length bias assumes a stationary renewal process observed at a random time point;
our posts are *event-triggered* (at or after case resolution), not cross-sectional, so the inspection paradox
does not straightforwardly apply. Vardi's weight functions must be **known** — ours is what we failed to
estimate — and all of it assumes one common underlying distribution, which segment mismatch denies. Wang and
Asgharian et al. assume a known cross-sectional sampling time and stationary incidence; ours is event-triggered
with outcome-dependent probability. Zelen & Feinleib has a known detection mechanism and a defined natural
history, with no document-disclosure analogue.

### 10.5 Heckman, J. J. "Sample Selection Bias as a Specification Error." *Econometrica* 47(1), 1979, 153–. DOI [10.2307/1912352](https://doi.org/10.2307/1912352)

Recasts selection as an omitted-variable problem and gives the two-step correction via the inverse Mills ratio.

**Borrow:** the conceptual reframing (selection = omitted variable) is what licenses our generative approach:
model the posting decision jointly with the duration and the bias handles itself. That is the *structural*, not
the two-step, reading of Heckman, and it is the right one for a Bayesian generative model.

**Breaks:** identification leans hard on joint normality and/or an exclusion restriction — a variable affecting
posting but not duration — and we have no credible instrument, which makes the two-step estimator notoriously
unstable. Bluntly: **do not run a Heckman correction here. A wrong-signed λ is exactly what a weakly-identified
selection equation produces.**

### 10.6 Manski, C. F. "Anatomy of the Selection Problem." *Journal of Human Resources* 24(3), 1989, 343–. DOI [10.2307/145818](https://doi.org/10.2307/145818) — and *Partial Identification of Probability Distributions.* Springer, 2003. DOI [10.1007/b97478](https://doi.org/10.1007/b97478) *(Crossref's record omits the author field; chapter DOIs such as [10.1007/0-387-21786-x_2](https://doi.org/10.1007/0-387-21786-x_2) confirm the volume and structure)*

Decomposes the selection problem into what the data identify without assumptions and what only assumptions
deliver; the identified set is an interval whose width is governed by the selection probability. The book gives
the graded-assumption treatment across missing, contaminated and selected outcomes.

**Borrow:** **the honest answer for our situation.** With P(post) known or bounded, worst-case bounds on the
duration distribution follow with *no* assumption about the selection mechanism — and given that we cannot
credibly sign the tilt, reporting a bound is strictly better science than reporting a point estimate we do not
believe. The bound width is itself informative: it tells readers how much the forum data can possibly matter.
And the book's **layers-of-assumption methodology is the reporting structure we should adopt**: report the
no-assumption bound, then the bound under monotone selection, then the point estimate under a full model, and let
the reader see what each assumption buys. **That *is* the answer to "what should we do about a wrong-signed
estimate".**

**Breaks:** worst-case bounds can be uninformatively wide when the selection rate is low, which ours is — expect
wide intervals and be prepared to say they are wide. Partial identification also gives bounds, not the point
estimate a downstream simulator needs, so we still need a point somewhere; bounds discipline it rather than
replace it.

### 10.7 Sharp bounds, cheaply

- Horowitz, J. L. & Manski, C. F. "Nonparametric Analysis of Randomized Experiments with Missing Covariate and Outcome Data." *JASA* 95(449), 2000, 77–84. DOI [10.1080/01621459.2000.10473902](https://doi.org/10.1080/01621459.2000.10473902)
- Lee, D. S. "Training, Wages, and Sample Selection: Estimating Sharp Bounds on Treatment Effects." *Review of Economic Studies* 76(3), 2009, 1071–1102. DOI [10.1111/j.1467-937X.2009.00536.x](https://doi.org/10.1111/j.1467-937x.2009.00536.x)

Horowitz & Manski derive sharp worst-case bounds when outcomes and covariates are missing in ways that may depend
on the missing values. Lee derives sharp bounds under a **monotonicity** assumption on selection, by trimming the
selected sample from each tail by the excess selection rate — much tighter than worst-case.

**Borrow:** Horowitz–Manski gives the operational formula: bounds by imputing the extremes of the outcome's
support to the missing units, which for a LogNormal duration with a defensible support cap (a statutory
deadline, say) is directly computable, needs no selection model, and is immediately reportable. **Lee is the best
bounds/tightness trade-off available to us, and if I had to pick one estimator for the selection side of the
paper it would be this one.** Monotonicity here would read: any applicant who would post under a good outcome
would also post under a bad one (or the reverse) — a *substantively arguable* assumption we could defend — and
Lee trimming then gives tight sharp bounds on the duration distribution.

**Breaks:** Horowitz–Manski needs a bounded outcome support to be finite, so we must justify a maximum plausible
duration, and the bounds discard all the shape information in the forum data, so they are conservative. Lee
requires monotone selection — an assumption about an unobserved counterfactual posting decision — and a
comparison group with a higher selection rate, which our design lacks unless we can define a subpopulation with
plausibly higher posting propensity.

### 10.8 Copas, J. & Eguchi, S. "Local Sensitivity Approximations for Selectivity Bias." *JRSS Series B* 63(4), 2001, 871–895. DOI [10.1111/1467-9868.00318](https://doi.org/10.1111/1467-9868.00318); extended *JRSS-B* 67, 2005, DOI [10.1111/j.1467-9868.2005.00512.x](https://doi.org/10.1111/j.1467-9868.2005.00512.x)

First-order approximations to the bias induced by non-random selection as a function of a sensitivity parameter,
so one can trace how conclusions move without fitting a full selection model.

**Borrow:** **the right technique for a parameter we cannot estimate.** The sensitivity parameter is meant to be
*varied over a plausible range*, not estimated. Report our duration conclusions as a curve over the selection
parameter, note that the data-implied value came out at −0.47 with the wrong sign for any complaint-selection
story, and let the curve show whether it matters. **This converts our failed estimate into a legitimate
sensitivity analysis.**

**Breaks:** a local approximation, valid only for modest departures; if the real selection effect is large the
first-order expansion misleads.

### 10.9 Scharfstein, D. O., Rotnitzky, A. & Robins, J. M. "Adjusting for Nonignorable Drop-Out Using Semiparametric Nonresponse Models." *JASA* 94(448), 1999, 1096–1120. DOI [10.1080/01621459.1999.10473862](https://doi.org/10.1080/01621459.1999.10473862) *(with published discussion and rejoinder, DOI [10.2307/2669930](https://doi.org/10.2307/2669930))*

Introduces the exponential-tilt sensitivity parameterisation for MNAR: missingness odds tilted by exp(α·y), with
α a **non-identified** sensitivity parameter varied across a range, yielding inference indexed by α.

**Borrow:** **the single most useful formal result for our problem, and it explains our failure.** α is not
identified from the observed data; it is a sensitivity parameter *by construction*. So **any procedure that
appears to "estimate the tilt" from observed data alone is recovering the parametric bridge assumption, not the
tilt** — and that is very likely what produced −0.47. Adopt the exponential-tilt parameterisation, place a prior
on α informed by substantive reasoning about who posts, and report posterior sensitivity. **Do not estimate α.**

**Breaks:** requires committing to a tilt functional form, and the results are only as good as the prior on α.
It also assumes the outcome is the *same* quantity in respondents and non-respondents — again the mismatch
premise.

### 10.10 Recoverability, and the selection-vs-pattern-mixture choice

- Bareinboim, E., Tian, J. & Pearl, J. "Recovering from Selection Bias in Causal and Statistical Inference." *AAAI* 28, 2014. DOI [10.1609/aaai.v28i1.9074](https://doi.org/10.1609/aaai.v28i1.9074); reprinted in *Probabilistic and Causal Inference*, 2022, 433–450, DOI [10.1145/3501714.3501740](https://doi.org/10.1145/3501714.3501740); see also Bareinboim & Pearl, *AAAI* 25, 2011, 1754–1755, DOI [10.1609/aaai.v25i1.8056](https://doi.org/10.1609/aaai.v25i1.8056), and Bareinboim & Tian, *AAAI* 29, 2015, DOI [10.1609/aaai.v29i1.9679](https://doi.org/10.1609/aaai.v29i1.9679)
- Little, R. J. A. & Rubin, D. B. *Statistical Analysis with Missing Data*, 3rd edn. Wiley, 2019. DOI [10.1002/9781119482260](https://doi.org/10.1002/9781119482260); "Nonignorable Missing-Data Models", DOI [10.1002/9781119013563.ch15](https://doi.org/10.1002/9781119013563.ch15)

Bareinboim et al. give graphical criteria for **recoverability**: when a distribution can be consistently
recovered from selection-biased data alone, and when external unselected data on some margin is required. Little
& Rubin is the standard reference for MCAR/MAR/MNAR and for the distinction between *selection models* (factor
the joint as outcome × missingness-given-outcome) and *pattern-mixture models* (missingness × outcome-given-pattern).

**Borrow:** two results that change what we do. (i) **Applied to us, the recoverability verdict is decisive.**
Our selection node S (post / no-post) has parents *outcome* and *elapsed time*, and elapsed time is a
deterministic function of the durations we want — so selection is a child of the outcome variable itself, which
is the canonical **non-recoverable** configuration. **P(duration) is not recoverable from the forum sample alone,
at any sample size, and no reweighting of reddit data can fix it.** Recoverability requires either s-admissible
covariates that d-separate S from the outcome, or external data on an unselected margin. We have the latter:
official documents. **So the literature's verdict is that combining sources is not merely convenient, it is
necessary — and it tells us precisely what the official corpus is for: not a second opinion, but the identifying
margin.** (ii) **Little & Rubin's pattern-mixture factorisation is a better fit for us than a selection model**,
and this is under-appreciated: it lets us say outright that posted and unposted cases have different duration
distributions, with the difference governed by an explicit non-identified sensitivity parameter, **without
requiring us to believe there is one common distribution being differentially sampled.** Given that our working
hypothesis is that community and official reports measure *different things*, pattern-mixture is the honest
factorisation.

**Breaks:** two serious limitations. The recoverability framework assumes the variable is the *same* variable in
both sources — it presupposes away our segment mismatch, so **if the official corpus measures a different
interval it is not a valid external margin, and recoverability fails for a reason the graph cannot express.** And
the criteria concern asymptotic identifiability, not estimability: "recoverable in principle" and "estimable
from 5 documents" are very different claims. Pattern-mixture parameters are non-identified by construction, so
it relocates the problem into a prior rather than solving it, and MNAR theory still assumes a shared outcome
definition across patterns.

### 10.11 Mathiowetz, N. A. & Duncan, G. J. "Out of Work, Out of Mind: Response Errors in Retrospective Reports of Unemployment." *Journal of Business & Economic Statistics* 6(2), 1988, 221–229. DOI [10.1080/07350015.1988.10509656](https://doi.org/10.1080/07350015.1988.10509656) *(Crossref misspells the second author as "Greg J. Ouncan"; the correct name is Greg J. Duncan)*

Validates retrospective survey reports of unemployment against employer and administrative records, finding
substantial response error that grows with recall length, with short and less salient spells disproportionately
omitted or understated.

**Borrow:** **this is the closest analogue in the literature and it should be the anchor citation for our −0.47.**
It establishes, with record validation, that retrospective self-reports of spell length are biased *downward*
relative to administrative measures, and names the mechanisms: omission of spells, foreshortening,
salience-dependent recall. Our finding that applicants report faster durations than agencies publish is exactly
the direction this literature predicts. **That converts our "wrong sign" from an embarrassment into a
confirmation that we are looking at measurement error rather than complaint selection — and it means the honest
move is not to divide out a tilt but to model a recall/definition process.**

**Breaks:** their validation had genuine linked administrative truth for the same individual and the same spell.
We have no linkage: our official "measure" is a published *typical* duration for a possibly different segment,
not a record of the same applicant's case. So we can borrow the direction and the mechanism but cannot replicate
the validation design.

### 10.12 Bound, J., Brown, C. & Mathiowetz, N. "Measurement Error in Survey Data." In *Handbook of Econometrics*, 2001, 3705–3843. DOI [10.1016/S1573-4412(01)05012-7](https://doi.org/10.1016/s1573-4412(01)05012-7)

The definitive survey of survey-measurement error, synthesising validation-study evidence across earnings,
hours, transfers and spell durations, and developing the econometric consequences of non-classical measurement
error.

**Borrow:** two things. The empirical regularity **across many validation studies** that self-reported durations
are shorter and mean-reverting relative to records — cite this for the general claim rather than resting on one
paper. And methodologically more important: the treatment of **non-classical measurement error**, where error
correlated with the true value does not merely attenuate but *shifts and rotates*. **A single multiplicative
tilt is therefore the wrong correction *form* for our problem even if we could estimate it** — which
independently explains why our pooled log-ratio is uninterpretable.

**Breaks:** framed around regression coefficients in linear models; we need distributions of durations, not
slopes. And its remedies — validation subsamples, instrumental variables, multiple indicators — all require data
we do not have.

### 10.13 Rips, L. J., Conrad, F. G. & Fricker, S. S. "Straightening the Seam Effect in Panel Surveys." *Public Opinion Quarterly* 67(4), 2003, 522–554. DOI [10.1086/378962](https://doi.org/10.1086/378962)

Investigates seam bias — the artifactual concentration of reported transitions at the boundary between panel
reference periods — and shows it arises from how respondents reconstruct and anchor event timing rather than from
real behaviour.

**Borrow:** **the cognitive mechanism for exactly our hypothesis, with an established name and a documented
cause.** Respondents anchor timing to salient boundaries and reconstruct intervals between them, which
**displaces and compresses reported durations** according to the *respondent's* mental reference period rather
than the record's. Applied to us: an applicant anchors on "when I submitted" and "when I got the permit", a
narrower interval than the agency's published span from intake-completeness to final issuance. That is our
segment mismatch. Cite it for the mechanism rather than asserting segment mismatch bare.

**Breaks:** seam bias is defined relative to a panel design's reference periods, and we have no panel and no
reference-period structure. Transfer the cognitive mechanism, not the diagnostic.

### 10.14 Neter, J. & Waksberg, J. "A Study of Response Errors in Expenditures Data from Household Interviews." *JASA* 59(305), 1964, 18–55. DOI [10.1080/01621459.1964.10480699](https://doi.org/10.1080/01621459.1964.10480699)

The classic experimental study of telescoping and bounded recall: unbounded recall pulls events forward in time
and inflates reported recent activity, while bounded-recall interviewing substantially reduces the error.

**Borrow:** telescoping is a **second distinct mechanism generating a negative duration bias** — forward-telescope
the start of a step and the reported interval shrinks. And the remedy is a design fix: bounded recall, i.e.
anchoring on an explicit prior event. For us that means **preferring forum posts that state explicit dates or
anchor events over posts giving bare durations, and modelling the two differently** — an implementable
data-quality distinction in our reddit ingestion.

**Breaks:** expenditures, not durations, and the bounded-recall remedy requires controlling the instrument, which
we cannot do with found text.

### 10.15 Sudman, S. & Bradburn, N. M. "Effects of Time and Memory Factors on Response in Surveys." *JASA* 68(344), 1973, 805–815. DOI [10.1080/01621459.1973.10481428](https://doi.org/10.1080/01621459.1973.10481428)

Models response error as a joint function of elapsed time since the event and event salience, showing omission
rises and dating accuracy falls with the recall interval, with salience moderating both.

**Borrow:** a directly usable functional form — accuracy declining in elapsed time, moderated by salience. And it
exposes a specific, checkable hazard: **elapsed time enters our likelihood twice**, once in the selection
mechanism (posting probability depends on elapsed time) and once in the measurement error. **If we have been
fitting only the selection channel, the measurement channel's contribution will be absorbed into it with the
wrong sign** — a concrete candidate explanation for the −0.47 arising as a *fitting artifact of an omitted
channel*.

**Breaks:** descriptive and pre-modern; the functional forms are illustrative rather than calibrated.

### 10.16 Manzoni, A., Vermunt, J. K., Luijkx, R. & Muffels, R. "Memory Bias in Retrospectively Collected Employment Careers: A Model-Based Approach to Correct for Measurement Error." *Sociological Methodology* 40(1), 2010, 39–73. DOI [10.1111/j.1467-9531.2010.01230.x](https://doi.org/10.1111/j.1467-9531.2010.01230.x)

Compares retrospective life-history employment data with panel data on the same people and fits a
latent-class/latent-Markov **measurement model** to correct the retrospective reports, estimating the memory-bias
process rather than assuming it.

**Borrow:** **the single most transplantable modelling strategy in Area 10.** It does exactly what we need: treat
the discrepancy between a retrospective self-report and an institutional record as a *measurement model with
estimable parameters*, embedded in a latent-state model. Our architecture is already a latent-state model of a
workflow, so adding a **per-source measurement layer — a document/report emission model with a source-specific
interval-definition parameter — is the same move, and it dissolves the wrong-sign problem by construction**,
because there is no longer a single duration being differentially sampled: there is a latent duration and two
source-specific measurement maps. Adopt this.

**Breaks:** their correction is identified because the same individuals appear in both data sources. We have no
overlap at the case level — our step keys overlap across sources but the *cases* do not — so the measurement map
is identified only through cross-source comparison at the step-key level, which is weaker and requires assuming
step keys mean the same thing in both sources, arguably the very thing in doubt.

### 10.17 Estimand alignment — the framing that resolves the wrong sign

- Lundberg, I., Johnson, R. & Stewart, B. M. "What Is Your Estimand? Defining the Target Quantity Connects Statistical Evidence to Theory." *American Sociological Review* 86(3), 2021, 532–565. DOI [10.1177/00031224211004187](https://doi.org/10.1177/00031224211004187)
- Mallinckrodt, C. H., Bell, J., Liu, G., Ratitch, B., O'Kelly, M., Lipkovich, I., Singh, P., Xu, L. & Molenberghs, G. "Aligning Estimators With Estimands in Clinical Trials: Putting the ICH E9(R1) Guidelines Into Practice." *Therapeutic Innovation & Regulatory Science* 54, 2020, 353–364. DOI [10.1007/s43441-019-00063-9](https://doi.org/10.1007/s43441-019-00063-9); companion Ratitch et al., same journal, 54, 324–341, DOI [10.1007/s43441-019-00061-x](https://doi.org/10.1007/s43441-019-00061-x); background Akacha, Bretz & Ruberg, *Statistics in Medicine* 36(1), 2017, 5–19, DOI [10.1002/sim.7033](https://doi.org/10.1002/sim.7033). **The ICH E9(R1) guideline document itself is UNVERIFIED** — the database.ich.org PDF returned binary content and the ich.org efficacy-guidelines page rendered without its table; cite these three peer-reviewed implementations rather than the guideline.

Lundberg et al. argue that much empirical social science skips defining a theoretical estimand and jumps to an
estimator, so many apparent disputes are undeclared disagreements about the target quantity. The ICH E9(R1)
papers operationalise a five-attribute estimand specification: population, variable/endpoint **including its
exact timing and start/stop rules**, handling of intercurrent events, and population-level summary — with
estimators then chosen to match.

**Borrow:** **the framing paper for our wrong-sign result, and the answer to the brief's "estimand alignment"
search.** Lundberg et al.'s sequence — theoretical estimand, then empirical estimand, then estimator —
immediately exposes our problem as a mismatch at the *empirical estimand* layer: "median duration of step *s* as
experienced by an applicant" and "median duration of step *s* as published by the agency" are **two different
empirical estimands for one theoretical quantity, and a ratio between estimates of two different estimands is
not a bias and cannot be corrected as one.** That is the sentence our paper needs. The ICH framework then gives
the rigorous template: publish an **estimand specification for each duration source** — one for
document-published intervals, one for applicant-reported intervals — with explicit start/stop rules, and state
that they are non-identical and therefore not pooled. That is a far stronger and more defensible position than
either correcting or ignoring the tilt. Its central lesson is precisely ours: **two "time to event" quantities
with different start points or different handling of intervening events are different estimands, and any
discrepancy between them is a specification difference, not bias.**

**Breaks:** Lundberg et al. is methodological and rhetorical — it supplies the diagnosis and the vocabulary but
no estimator, and is written for observational causal inference rather than measurement reconciliation. ICH
E9(R1) is built for regulated randomised trials with a protocol that *defines* the endpoint prospectively; we
are reverse-engineering estimands from found text where start/stop rules are implicit and must be inferred, so we
can adopt the specification discipline but not the prospective control that makes it work.

### 10.18 What a biased sample is worth, and how to decompose the gap

- Meng, X.-L. "Statistical paradises and paradoxes in big data (I): Law of large populations, big data paradox, and the 2016 US presidential election." *Annals of Applied Statistics* 12(2), 2018. DOI [10.1214/18-AOAS1161SF](https://doi.org/10.1214/18-aoas1161sf)
- Bradley, V. C., Kuriwaki, S., Isakov, M., Sejdinovic, D., Meng, X.-L. & Flaxman, S. "Unrepresentative big surveys significantly overestimated US vaccine uptake." *Nature* 600, 2021, 695–700. DOI [10.1038/s41586-021-04198-4](https://doi.org/10.1038/s41586-021-04198-4)
- Meyer, B. D., Mok, W. K. C. & Sullivan, J. X. "Household Surveys in Crisis." *Journal of Economic Perspectives* 29(4), 2015, 199–226. DOI [10.1257/jep.29.4.199](https://doi.org/10.1257/jep.29.4.199)
- Poterba, J. M. & Summers, L. H. "Reporting Errors and Labor Market Dynamics." *Econometrica* 54(6), 1986, 1319–. DOI [10.2307/1914301](https://doi.org/10.2307/1914301)
- Olteanu, A., Castillo, C., Diaz, F. & Kıcıman, E. "Social Data: Biases, Methodological Pitfalls, and Ethical Boundaries." *Frontiers in Big Data* 2, 2019, 13. DOI [10.3389/fdata.2019.00013](https://doi.org/10.3389/fdata.2019.00013)
- Heckathorn, D. D. "Respondent-Driven Sampling: A New Approach to the Study of Hidden Populations." *Social Problems* 44(2), 1997, 174–199. DOI [10.1525/sp.1997.44.2.03x0221m](https://doi.org/10.1525/sp.1997.44.2.03x0221m); estimator theory Salganik & Heckathorn, *Sociological Methodology* 34, 2004, 193–240, DOI [10.1111/j.0081-1750.2004.00152.x](https://doi.org/10.1111/j.0081-1750.2004.00152.x)

Meng introduces the data-defect index d_dc = ρ(R,Y), the correlation between inclusion and outcome, and shows
estimation error decomposes into d_dc × a population-size factor × problem difficulty; the "law of large
populations" means **a large biased sample can be worth vanishingly little**, with effective sample size
n_eff ≈ n/(1 + (N−1)ρ²). Bradley et al. demonstrate it empirically: two very large online surveys were
dramatically more biased about vaccine uptake than a small probability sample. Meyer et al. document, by linking
surveys to administrative records, that surveys increasingly under-report transfer receipt, and **decompose the
gap into unit nonresponse, item nonresponse and misreporting.** Poterba & Summers show reporting errors generate
large *spurious* transition flows, changing estimated spell durations and turnover. Olteanu et al. taxonomise
platform-data biases. Heckathorn's RDS recovers identification from a non-probability sample via a model of the
recruitment mechanism.

**Borrow:** four things, and two of them may resolve our problem outright. (i) **Meng's d_dc and n_eff are the
principled way to say what our forum corpus is worth relative to a random sample of cases, in one interpretable
number, and to decide how much weight community timing should get.** It also supplies a much better framing than
"correct the bias": **if n_eff is ~2, a tilt correction is beside the point because the data barely move the
posterior anyway — which may be the cleanest resolution of the wrong-sign problem.** Bradley et al. is the
rhetorical anchor and the imitable methodology (compute d_dc against a benchmark, report n_eff). (ii) **Meyer et
al.'s decomposition discipline is the concretely useful export:** they do not report one "survey bias" number but
split the gap into separately-estimated channels. We should do exactly that with the −0.47 — partition it into
(a) which cases get posted (selection), (b) which steps get mentioned (item-level disclosure), (c) how the
mentioned interval is defined and recalled (measurement). **Our current single pooled log-ratio collapses all
three, and a pooled statistic over three channels with opposing signs is uninterpretable — which is very likely
the direct cause of the wrong sign.** (iii) **Poterba & Summers is a decisive warning for a workflow model built
from reported step transitions:** misreported step boundaries create phantom steps and phantom transitions,
systematically *shortening* each apparent step while *multiplying* their number. That mechanism would produce
our −0.47 *and* our back-loaded step discovery **simultaneously, from a single cause** — worth testing as a
unified explanation, since it would make a much stronger paper than treating them separately. (iv) Olteanu et
al.'s three-way split is useful because it names our case: our −0.47 is plausibly **content-production bias**
(applicants narrate the interval they lived through) rather than population or behavioural selection, and having
a citable category strengthens the segment-mismatch argument considerably. From RDS, borrow only the logic by
analogy — a model of the recruitment mechanism buys back identification — plus the loose degree-weighting idea
(our reddit thread that disclosed 3 steps nothing else did is a high-degree, high-value observation).

**Breaks:** **d_dc is not estimable from the biased sample alone** — it requires a benchmark, and ours (official
documents) is itself censored; worse, if the two sources measure different segments then ρ is not even well
defined, because there is no single Y. Meng's framework also targets finite-population means, not latent duration
distributions, so the n_eff heuristic transfers but the exact error decomposition does not. Bradley et al. had
trustworthy administrative ground truth (CDC records); **we do not — our "benchmark" is the other biased source,
and that asymmetry is the core difficulty of our setup.** Meyer et al. have true record linkage, so our
decomposition will be model-based and only partially identified. Poterba & Summers use a discrete classification
model over a small state space with repeated observation of the same individuals; our steps are numerous,
unlabelled and observed once. Olteanu et al. is a taxonomy with no correction machinery. And RDS needs the
referral chains that forum posts do not provide, with guarantees known to be fragile to homophily — a poor fit
mechanically, useful only as an argument by analogy.

---

## 11. Five adjacent literatures the brief did not name

These are my own additions. Each covers a part of our problem that none of the ten areas reaches.

### 11.1 Script and event-schema induction — the NLP twin of our whole task

- Chambers, N. & Jurafsky, D. "Unsupervised Learning of Narrative Event Chains." *ACL-08: HLT*, 2008, 789–797. <https://aclanthology.org/P08-1090/>
- Chambers, N. "Event Schema Induction with a Probabilistic Entity-Driven Model." *EMNLP 2013*, 1797–1807. <https://aclanthology.org/D13-1185/>
- Cheung, J. C. K., Poon, H. & Vanderwende, L. "Probabilistic Frame Induction." *NAACL-HLT 2013*, 837–846. <https://aclanthology.org/N13-1104/>
- Frermann, L., Titov, I. & Pinkal, M. "A Hierarchical Bayesian Model for Unsupervised Induction of Script Knowledge." *EACL 2014*, E14-1006. <https://aclanthology.org/E14-1006/> *(page range not shown on the volume page)*

This literature induces latent **scripts** — ordered sets of events with typed participants — from many
documents, without labels. Chambers & Jurafsky learn narrative chains with participant coreference; Chambers
2013 makes it a probabilistic entity-driven generative model; Cheung, Poon & Vanderwende induce frames
probabilistically; Frermann, Titov & Pinkal put a **hierarchical Bayesian** model over event sequences with
participants, sharing structure across related scenarios.

**Borrow:** this is, in NLP terms, *our exact problem* — a latent ordered multi-actor procedure induced from many
texts — and it is startling that our design documents do not cite it. Four things: (i) the **event-plus-typed-
participant** structure is our step-plus-actor structure, with the participant type playing the role of our
agency class; (ii) Frermann et al.'s **hierarchy across scenarios** is the direct analogue of our hierarchy
across jurisdictions and is a proven construction; (iii) the whole line is unsupervised with no gold scripts,
which is our situation; (iv) it is the right literature to position our contribution against in an NLP venue,
because the obvious reviewer question is "how is this not script induction?" and we should have a crisp answer.

**Breaks:** and the answer to that question is the list of breaks. These models induce a *prototypical* script
from a corpus of texts each *narrating an instance* — a news story describing an arrest. **We have documents
that describe the procedure itself, not instances of it**, which is a different likelihood. They have no notion
of a source that selectively discloses, no per-source reliability, no durations, no fees, no changepoints, and
their "order" is typically a total order or a chain rather than a partial order with genuine incomparability.
Evaluation is also intrinsic (held-out cloze) rather than against a ground-truth procedure. So: cite it as the
nearest NLP neighbour and as the source of the hierarchical-script construction; do not expect the machinery to
transfer.

### 11.2 Downey, D., Etzioni, O. & Soderland, S. "Analysis of a probabilistic model of redundancy in unsupervised information extraction." *Artificial Intelligence* 174(11), 2010, 726–748. DOI [10.1016/j.artint.2010.04.024](https://doi.org/10.1016/j.artint.2010.04.024) *(the URNS model; earlier IJCAI 2005 version)*

An urn model giving the probability that an extraction is correct as a function of **how many times it was
extracted from how many distinct sources**, with the urn's composition — including the number of *unseen* correct
extractions — estimated from the observed repetition distribution.

**Borrow:** this is the missing formal link between §3 (how much does repeated mention tell us about truth) and
§8 (how many things have we not seen), and it does both in one model. It gives a principled answer to "a step
mentioned by 5 documents versus a step mentioned by 1" that is *not* a reliability-weighted vote but a
consequence of the sampling model — and crucially it estimates the unseen mass from the *same* repetition
statistics, which is exactly the coupling our step-count question needs. Cheap to implement as a baseline and a
prior.

**Breaks:** the urn assumes draws are i.i.d. from a fixed composition, i.e. exchangeable sources with no
selective disclosure and no copying — the same failure as Good–Turing (§8.1), for the same reason. Extractions
are flat strings with no structure, no actor, no order. And it is a per-relation model, so it has no analogue of
our visibility class. Cite it for the framing and the coupling, not the estimator.

### 11.3 Multi-parameter evidence synthesis, and conflict diagnostics

- Ades, A. E. & Sutton, A. J. "Multiparameter Evidence Synthesis in Epidemiology and Medical Decision-Making: Current Approaches." *JRSS Series A* 169(1), 2005, 5–35. DOI [10.1111/j.1467-985X.2005.00377.x](https://doi.org/10.1111/j.1467-985x.2005.00377.x); see also Ades et al., *J. Health Services Research & Policy* 13(3 suppl), 2008, 12–22, DOI [10.1258/jhsrp.2008.008020](https://doi.org/10.1258/jhsrp.2008.008020)
- Presanis, A. M., Ohlssen, D., Spiegelhalter, D. J. & De Angelis, D. "Conflict Diagnostics in Directed Acyclic Graphs, with Applications in Bayesian Evidence Synthesis." *Statistical Science* 28(3), 2013, 376–397. DOI [10.1214/13-STS426](https://doi.org/10.1214/13-STS426)

Ades & Sutton set out the framework in which **heterogeneous data sources each inform a different function of a
shared parameter vector**, combined in one Bayesian model with all the evidence contributing simultaneously.
Presanis et al. develop principled diagnostics for **where in such a model the evidence sources conflict**, node
by node on the DAG.

**Borrow:** this is the framework our §9.8 problem has been waiting for, and it is often overlooked outside
biostatistics. Our five duration object types are not five samples from one distribution — they are **five
constraints on different functions of (μ_s, σ_s)**: a published p50 constrains a quantile, an observed value is
a draw, a prose range constrains two quantiles softly, a statutory cap is a policy. MPES is exactly the
formalism for combining constraints on functions of parameters rather than repeated measurements of one
quantity, and it is the principled version of what `latent_timing.py` currently does by hand. Second, and
equally valuable: **Presanis et al. give us node-level conflict diagnostics**, which is precisely the "are two
sources in conflict?" question in `2026-09-15-generative-model.md` §5 — and it answers it *per parameter* rather than per
source pair, which is the right granularity, and it does so inside the fitted model rather than as a
preprocessing step. It is also the natural home for our version-changepoint test: a conflict that disappears
once a version boundary is introduced is drift, and a conflict that survives is error.

**Breaks:** MPES assumes the *functional* relationship between each source and the parameters is known and
correctly specified, which is exactly what our estimand mismatch (§10.17) denies for community reports — so MPES
does not solve the mismatch, it makes the mismatch the thing you must specify. Its applications are
low-dimensional parameter vectors (prevalence, incidence, transmission rates) with a handful of well-understood
sources, not 86 step keys with a latent structure. The conflict diagnostics are also computed on a *fixed* DAG
with a fixed parameter set, so they do not extend to a model whose dimension is unknown.

### 11.4 Shin, J., Wu, S., Wang, F., De Sa, C., Zhang, C. & Ré, C. "Incremental knowledge base construction using DeepDive." *PVLDB* 8(11), 2015, 1310–1321. DOI [10.14778/2809974.2809991](https://doi.org/10.14778/2809974.2809991) — journal version *VLDB Journal* 26(1), 2016, 81–105. DOI [10.1007/s00778-016-0437-2](https://doi.org/10.1007/s00778-016-0437-2)

A system for building a probabilistic knowledge base from text by declaring extraction and inference rules,
compiling them to a factor graph, and doing marginal inference — with **incremental** re-inference so that new
documents or new rules update the KB without a full refit.

**Borrow:** the closest existing *system* to what `pipeline/procbench/incremental.py` is trying to be, and it
gets one thing right that we do not: **the output is a marginal probability per fact, produced by joint
inference over a factor graph, rather than a verdict produced by a greedy loop.** Two specific borrows: the
declarative separation of extraction rules from inference (which keeps the LLM in the instrument role our design
document insists on), and the incremental-inference machinery, which is an engineering solution to the same
problem §2.8 solves statistically. Worth reading before we build our own incremental sampler.

**Breaks:** DeepDive's factor graph is over flat relational facts with hand-written factors and learned weights;
it has no latent structured object, no unknown dimension, no per-source disclosure model and no time. Its
"incremental" is a *computational* guarantee (recompute the same posterior faster), not a statistical one about
sequential evidence. And the weight learning is distantly supervised, which imports a different bias problem.

### 11.5 Razniewski, S., Arnaout, H., Ghosh, S. & Suchanek, F. "Completeness, Recall, and Negation in Open-world Knowledge Bases: A Survey." *ACM Computing Surveys*, 2024, 1–42. DOI [10.1145/3639563](https://doi.org/10.1145/3639563) — see also *PVLDB* 14(12), 2021, 3175–3177, DOI [10.14778/3476311.3476401](https://doi.org/10.14778/3476311.3476401)

A survey of exactly the problem our silences pose: under the open-world assumption, absence of a fact from a
knowledge base means nothing, and the survey collects the approaches that make absence informative —
completeness metadata, cardinality assertions, recall estimation, and explicit **negation**.

**Borrow:** the right orientation for our "silence is data" claim, and the vocabulary to use for it. Its
organising insight is ours: **the open-world assumption is a choice, and the interesting middle ground is a
partially-closed world where you know which regions are complete.** For us, π *is* the completeness metadata,
and visibility class is the region. The survey also catalogues how negation is represented and evaluated, which
matters because our `silences` field in the extraction schema is an interesting-negation store and we have no
principled way to score it yet. Read alongside §3.14 and §8.14.

**Breaks:** a survey, so no estimator, and the completeness metadata in this literature is largely *asserted*
(by editors, by schema constraints) rather than *inferred jointly with the facts*, which is our whole
contribution. Also KB-centric: one extraction process, no per-source-kind heterogeneity, no latent structure.

### 11.6 Bayesian experimental design and value of information — which document to read next

- Chaloner, K. & Verdinelli, I. "Bayesian Experimental Design: A Review." *Statistical Science* 10(3), 1995. DOI [10.1214/ss/1177009939](https://doi.org/10.1214/ss/1177009939)
- Rainforth, T., Foster, A., Ivanova, D. R. & Bickford Smith, F. "Modern Bayesian Experimental Design." arXiv:[2302.14545](https://arxiv.org/abs/2302.14545), 2023; accepted in *Statistical Science*

Chaloner & Verdinelli is the canonical review of choosing a design to maximise expected utility — typically
expected information gain — under a prior. Rainforth et al. is the modern treatment, covering the computational
advances (nested Monte Carlo estimators of expected information gain, amortised and policy-based design) that
make sequential BED practical.

**Borrow:** we are already *doing* sequential experimental design and not calling it that. The saturation curve,
the endogenous stopping rule, and the "marginal information value per document kind" statistic in
`trajectory.jsonl` are all crude expected-information-gain computations, and **the formal version is a
one-step-ahead EIG over document kinds, which we can compute from the posterior we will already have.** Two
concrete consequences: it turns retrieval prioritisation into a decision-theoretic quantity ("read the fee study
next, because its EIG for the fee and touch-time parameters is highest"), which is directly useful given that
**retrieval error dominates reading error by an order of magnitude** in our Benchmark 2 results; and it composes
with §4.17's active inference, since which *field* to hand-verify and which *document* to fetch are the same
kind of decision under the same posterior. This is probably the largest piece of unclaimed low-hanging fruit in
the review.

**Breaks:** EIG is expensive — a nested expectation over posterior and predictive — and our likelihood is
already intractable, so the estimator will be noisy; Rainforth et al.'s amortised methods assume a
differentiable simulator, and ours is partly discrete and structural. EIG also optimises for *information*, not
for the thing we care about, which is a decision about regulatory simplification; a proper utility would weight
information about steps that are candidates for removal. And greedy one-step-ahead design is known to be
suboptimal for sequential problems, though it is what everyone does.

### 11.7 Where π comes from: the economics of voluntary disclosure

- Milgrom, P. R. "Good News and Bad News: Representation Theorems and Applications." *Bell Journal of Economics* 12(2), 1981, 380–. DOI [10.2307/3003562](https://doi.org/10.2307/3003562)
- Dye, R. A. "Disclosure of Nonproprietary Information." *Journal of Accounting Research* 23, 1985, 123–. DOI [10.2307/2490910](https://doi.org/10.2307/2490910)
- Verrecchia, R. E. "Discretionary Disclosure." *Journal of Accounting and Economics* 5, 1983, 179–194. DOI [10.1016/0165-4101(83)90011-3](https://doi.org/10.1016/0165-4101(83)90011-3) — and "Essays on Disclosure." *JAE* 32(1–3), 2001, 97–180. DOI [10.1016/S0165-4101(01)00025-8](https://doi.org/10.1016/s0165-4101(01)00025-8)

Milgrom's unravelling result: with verifiable information and a sceptical audience, a sender is driven to
disclose everything, because withholding is itself informative. Dye and Verrecchia give the conditions under
which **partial** disclosure survives in equilibrium: when the audience cannot tell whether the sender *has* the
information (Dye), or when disclosure is costly (Verrecchia) — and in both, withheld information is
systematically the *unfavourable* information, with a threshold structure.

**Borrow:** this is a genuinely different kind of contribution to our model and I think it matters for the paper.
It says the disclosure propensity π **is not an arbitrary nuisance parameter to be fitted — it is the equilibrium
of a disclosure game, and equilibrium theory predicts its shape.** Three testable implications for us: (i)
disclosure should be *threshold*-structured in the favourability of the fact, so an agency should publish its
processing time when it is good and go vague when it is bad — which makes π a function of the *value* of the
field, not only of the field's identity and the step's visibility, and gives us a principled reason to expect
exactly the non-ignorable coarsening §9.8 warns about; (ii) the unravelling logic predicts π should be *higher*
where an audience knows the information exists and can punish silence (statutorily mandated disclosures, items
on a published checklist) and lower where existence is itself unknown (back-office routing) — which is our
visibility gradient, derived rather than assumed; (iii) it supplies the **welfare interpretation** the project
needs, since a regulator choosing what to publish is choosing a π, and that is a policy lever, not a fact of
nature. This converts a nuisance parameter into a finding.

**Breaks:** these are stylised single-sender single-audience games with verifiable information and a
well-defined payoff — a municipal planning department publishing a web page is not obviously maximising anything,
and the more likely explanations of a missing field are inertia, CMS limitations and staff time. So treat this as
**a source of priors and testable predictions about the shape of π, not as a model of municipal behaviour.** The
literature is also entirely about a *single* strategic disclosure decision, with nothing about multiple document
kinds with different audiences, nothing about inference from silence by a third party, and no estimation theory
at all.

### 11.8 Our identification strategy has a name: simulation-based calibration and inference

- Talts, S., Betancourt, M., Simpson, D., Vehtari, A. & Gelman, A. "Validating Bayesian Inference Algorithms with Simulation-Based Calibration." arXiv:[1804.06788](https://arxiv.org/abs/1804.06788), 2018
- Cranmer, K., Brehmer, J. & Louppe, G. "The frontier of simulation-based inference." *PNAS*, 2020. DOI [10.1073/pnas.1912789117](https://doi.org/10.1073/pnas.1912789117). arXiv:[1911.01429](https://arxiv.org/abs/1911.01429)

Talts et al. give SBC: draw parameters from the prior, simulate data, refit, and check that the rank statistics
of the true parameters within their posteriors are uniform — a necessary condition that catches both
implementation bugs and model-implementation inconsistencies. Cranmer et al. review simulation-based inference,
where the model is available only as a simulator and the likelihood is intractable.

**Borrow:** two things, and they are the right frame for the whole synthetic-world workstream. (i) **SBC is the
validation we should be running on our own sampler and are not.** We have a generator (`benchmark/synth/`) that
samples truth and then documents, which is precisely an SBC harness — so the four goodness-of-fit checks in
`2026-09-15-generative-model.md` §6 should be joined by a fifth that is standard, cheap and diagnostic: **draw a world from
the prior, run the full pipeline, and check posterior rank uniformity for the disclosure propensities, the step
count, and the duration parameters.** If those ranks are not uniform, our posteriors are miscalibrated by
construction and no amount of real-corpus validation will reveal it. (ii) Cranmer et al. is the right citation
for what our synthetic world *is* methodologically — a simulator standing in for an intractable likelihood — and
it names the honest alternative to hand-derived likelihoods if our forward model outruns our ability to write
one down (see also §7.9, which does exactly this for process models).

**Breaks:** and here is the important caveat, because it is easy to overclaim. **SBC validates that an inference
algorithm is consistent with the model it implements; it says nothing about whether that model describes
reality.** Passing SBC on our synthetic world would confirm the sampler works and would *not* license carrying
synthetic-world disclosure propensities to the real corpus as calibrated parameters — that remains the transfer
assumption §4.17 flags. Simulation-based inference likewise assumes the simulator is correct; ours encodes our
own beliefs about how cities publish, so SBI would give us a well-calibrated posterior *under our own
assumptions*, which is a weaker claim than it sounds. Use SBC as an internal check and say so precisely.

---

## What is genuinely unclaimed

The honest headline: **most of this is assembled from existing parts, and the assembly is the contribution.**
Nine of the ten latents in `2026-09-15-generative-model.md` §8 have a literature that owns them, and for seven of those
there is a specific paper we should be building on rather than reinventing. Anyone claiming a wholly novel
statistical framework here would be wrong, and reviewers in any one of these ten areas would say so.

That said, four things are genuinely unclaimed, and they are worth stating precisely because they are what the
paper is actually about.

**1. The joint identification of step count against disclosure propensity, with synthetic calibration as the
identification strategy.** Each half exists: occupancy models identify existence against detection using
**repeat visits**; Bayesian record linkage identifies confusion matrices using **a labelled training sample**;
PPI and DSL identify downstream estimates using **a controlled gold sample**; DMM (§4.15) identifies them using
**multiple measurements per unit**. We have none of those four. Our identification comes from a fifth source
nobody uses: **a simulator of the evidence-generating process with known ground truth, whose nuisance parameters
transfer to the real corpus as priors.** Nobody licenses this (§4.17 is explicit that PPI exists precisely to
avoid needing it), and nobody has characterised when it works. That is a real methodological question with a
real answer available to us — we can *measure* the transfer gap by hand-labelling a small real sample — and it
is the most defensible novel claim in the project. It also has a sharp failure mode we should name first
(§4.16): if the synthetic corpus and the extractor share a model family, measured sensitivity is biased upward.

**2. Field-level informative silence, conditional on detection.** Occupancy models handle non-detection of a
species. Zhi et al. (§3.8) handle a source staying silent about an object, with an unconditioned scalar rate.
Weak supervision handles abstention, explicitly as a nuisance. **Nobody handles "the document described the step
and named no department, therefore the department is not applicant-facing information" — a silence about one
*field* of an object that *was* detected, whose probability depends on a latent class of the object, and from
which that latent class is inferred.** That inversion — the visibility class both governs disclosure and is
identified by the pattern of silences — is the genuinely new mechanism, and it is the one thing in our model that
I could not find anywhere in six areas of search.

**3. A likelihood for documents *about* a process, rather than traces *of* one.** Process mining has
p(log | model) and nothing else (§7). Script induction has p(narrative of an instance | script) (§11.1). Truth
discovery has p(claim | truth, source reliability) but a flat object (§3). What we need and nobody has is
p(municipal web page | true workflow, document kind), factorising through a disclosure model, a fidelity model,
and an extractor model. This is not deep theory — it is a modelling choice with several defensible forms — but it
is unwritten, and writing it down carefully is most of the work.

**4. Structural drift over an unknown-dimension object.** Changepoint models handle parameters in a series
(§9.5). Robinson & Hartemink and ARTIVA handle a *structure* changing over time with a fixed node set (§5.7).
Nicholls et al. handle an evolving poset with a fixed element set (§6.1). **Combining a changepoint process with
a nonparametric prior over steps — so that an amendment can add a step, not merely change a parameter — is
unclaimed.** §6.2's projectivity is the right foundation, but the temporal and nonparametric pieces have not
been put together.

And two things are unclaimed but should probably stay that way, because they are hard for good reasons rather
than because nobody thought of them:

**Rework loops.** The negative result of the review: §6 is *structurally incapable* of loops (a poset has no
cycles; a down-set cannot contain a repeated event), and §5 makes acyclicity a hard constraint. The only leads
are Mutual Hazard Networks (§6.8), where recurrence is at least expressible in a CTMC, and process trees
(§7.6), which have an explicit loop operator and no inference theory. **Fitting a process-tree representation
with Nicholls-line inference machinery appears to be unbuilt, and that is where our structural contribution most
plausibly lies.** It is also where we are weakest empirically (recall 0.00–0.25), and §7.6 suggests it is the
same defect as our systematically-too-fast durations.

**Touch/queue decomposition from anecdotes.** Sutton & Jordan (§7.17) prove this is a well-posed Bayesian problem
and that identification comes from *volume observed at varying load*. With three elapsed times it is a
convolution of two positive variables and **it is not identified, full stop.** The literature does not have a
trick we are missing; it has a data requirement we do not meet. What it does tell us is exactly what would fix
it, and all three routes are cheap: consultant **fee studies state staff-hours per review** (a near-direct
observation of touch time, which we should model as such rather than as generic text); **date-stamping every user
report and joining it to published application-volume series** supplies the load variation; and **batching
cadence is a free identifying signature**, since a step gated on a monthly council meeting contributes a queue
component that is deterministically ≈ Uniform(0, 30) days plus an agenda-deadline offset, so reported elapsed
times cluster at multiples of the cadence with uniform phase while touch time stays smooth. That is a genuine
likelihood with a real identification argument, and nothing in either literature exploits it.

---

## Bottom line

**The single best structural analogue is the Nicholls / Jiang Bayesian partial-order line** — Nicholls et al.
(AOAS 2025, §6.1) plus Jiang & Nicholls (CSDA 2026, §6.2). It is the only work where a latent, time-varying,
unknown-size *structured* object is inferred from dated documents each giving a partial, noisy view, and it
ships a normalised likelihood, a prior that makes transitivity automatic, a temporal HMM for version change, a
nonparametric prior over an growing element set, projectivity (which is what makes our incremental refitting a
coherent Bayesian operation rather than an approximation), Mallows dispersion as per-source reliability, and
public code. Its two gaps are our two contributions: it has no selective disclosure, and it cannot represent a
loop.

For the disclosure layer specifically, the best analogue is instead the ecological occupancy line —
MacKenzie et al. (§8.10) for the existence-times-detection factorisation, Dorazio & Royle (§8.11) for a posterior
over never-detected steps. For the extractor layer it is Egami & Shin (§4.15). Those three, plus Zhi et al.
(§3.8) for the only existing silent-rate model, are the load-bearing citations.

Five changes to our plan follow from this review and are worth doing regardless of what we write:

1. **Stop reporting the step count as a mixture-component count** (§1.7, §1.9); reframe it as a population size
   under a stated detection model (§8.11), and report a Chao1 floor, a model-based posterior per visibility
   class, and a sensitivity curve over the super-population size.
2. **Replace the 0.42 threshold in `decide_offline()` with a posterior over partitions** — ddCRP-style with the
   LLM similarity in the decay function (§2.10), a microclustering or allelic prior rather than a CRP (§1.10,
   §2.7), split-merge moves so early conflations are reversible (§1.3), and a credible ball with asymmetric
   split/merge penalties as the reporting object (§1.15).
3. **Replace the 3-year half-life with drift plus dated jumps** (§9.1 proves the half-life cannot work), pool the
   drift variance across keys (§9.3), decompose μ additively over the six key margins (§9.10), pool σ hard, and
   non-centre only the sparse keys.
4. **Treat the −0.47 as an estimand mismatch, not a bias** (§10.11, §10.17): publish a separate estimand
   specification per duration source, add a per-source measurement map (§10.16), decompose the gap into
   selection / item-disclosure / measurement (§10.18), and report Lee bounds (§10.7) plus a sensitivity curve
   (§10.8) instead of a correction.
5. **Hand-label ~50–100 field assertions from a genuinely random sample of the real corpus** and run PPI++ or
   DSL on the headline numbers (§4.17). This is the cheapest available fix for the review's sharpest criticism of
   our design, and it converts the synthetic-calibration transfer assumption from a vulnerability into a
   measured quantity.
