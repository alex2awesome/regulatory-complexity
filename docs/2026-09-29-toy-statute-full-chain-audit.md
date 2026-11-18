# Audit of the toy-statute full-chain model

Date: 2026-09-29. Scope: design, implementation, mathematical sampling, saved results, and hand-set parameters.

Primary document: [full-chain implementation](2026-09-29-toy-statute-full-chain-implementation.md).

**Report only. No model code, existing documentation, evidence, saved results, or fit configuration was changed. No new fits were launched.**

## 1. Verdict

The architecture is worth retaining. Marginalizing small discrete process spaces, sharing step-duration laws across towns, distinguishing legal interpretation from observed practice, and propagating process uncertainty into outcomes are sensible choices. The composite reparameterization is mathematically correct. Several saved numerical results reproduce.

However, this is not yet an exact, validated, end-to-end Bayesian model of the advertised chain. There are confirmed likelihood and scoring defects, as well as identification limits that more particles cannot solve:

1. The outcome likelihood multiplies Poisson probabilities for counts that overlap. It is not the joint likelihood of its own generator.
2. The applicant-report likelihood omits completion selection inside the integration over noisy, latent durations.
3. The reading scorer silently treats residual/unknown reading mass as a “No” answer to every question. Its headline joint score also includes Q5 despite the documented exclusion.
4. Residual-reading probability and compliance slack are exactly confounded in the independent-town reading model. Their separate posteriors cannot be learned from these observations.
5. The claim that risk-averse behavior is rejected concerns one extremely strong, arbitrarily scaled risk model, not risk aversion in general.
6. FFT convolution can wrap long durations into short ones and renormalizes away tail mass. This is a real defect, although the inspected posterior draws suggest small effects on the current toy fits.
7. Fees and several behavioral/legal assumptions are supplied by rules or plug-ins, not learned jointly. “Full chain” currently means connected modules with some cut and plug-in links, not one unified posterior.

The immediate priority should be correcting the target distribution and scoring, not another large W4 run with more particles. Sampling the wrong likelihood more precisely does not address these findings.

### What the current results establish

They show promising recovery of a supplied process-design menu, useful identification of some duration composites, and a workable computational framework. They do **not** yet establish calibrated recovery of the full chain, separately learned legal interpretation and agency preferences, intrinsic agency capability, or a general Bayesian advantage over a same-evidence LLM.

## 2. Audit scope and evidence

I traced the implementation document through the process, readings, validity, outcomes, generator, estimand, scoring, elicitation, and sampling modules in [the toy-statute package](../pipeline/procbench/toy_statute/). I also inspected the round-3, round-4, and outcome result documents and the corresponding local saved artifacts.

Checks performed:

- Ran `tests/test_toy_statute.py`: **32 passed**.
- Recomputed saved score summaries and inspected fit gates.
- Replayed log priors and likelihoods for three saved particles apiece from W0/fitB001, W1/fitB001, and W4/fitB001. Current calculations matched stored values to approximately floating-point precision, at worst about `2e-13`.
- Enumerated the reading-validity matrix and checked which questions can change it.
- Compared saved Stage-C configurations exhibiting exact residual/slack confounding.
- Recomputed question probabilities with residual mass separated.
- Reproduced an FFT wraparound counterexample and bounded its effect on a small sample of saved posterior draws.
- Derived the covariance of overlapping outcome counts and evaluated it at the saved synthetic truths.

These are bounded diagnostic checks, not a full refit or a new calibration experiment. Several current code hashes differ from historical manifests. The likelihood replays establish agreement at the inspected points, not byte-for-byte reproduction of every historical module. Findings about present defaults are distinguished below from claims about specially recomputed historical answers.

Relevant result sources:

- [Round 3 results](2026-09-28-toy-statute-round3-results.md), [saved W0 scores](../runs/toy_statute_20260926/W0/scores_round3/summary.json), and [saved W0x25 scores](../runs/toy_statute_20260926/W0x25/scores_round3/summary.json).
- [Round 4 results](2026-09-29-toy-statute-round4-results.md), [W4 diagnostics](../runs/toy_statute_20260926/W4/fitB001/diagnostics.json), [Stage-C results](../runs/toy_statute_20260926/W4/stage_c001/stage_c.json), and [Stage-C scores](../runs/toy_statute_20260926/W4/stage_c001/scores.json).
- [Outcome results](2026-09-28-toy-statute-outcomes-results.md), [ordinary-world scores](../runs/toy_statute_20260926/W0o/scores_outcomes001/summary.json), and [adversarial-world scores](../runs/toy_statute_20260926/W0o_adv/scores_outcomes001/summary.json).

## 3. Design: what is actually unified, and what is not

The intended core can be written schematically as

\[
p(\theta,w,\psi,\{r_t,S_t\}\mid E,x)
\propto p(\theta)p(w\mid x)p(\psi)
\prod_t p(r_t\mid w)\,p(S_t\mid r_t,\psi,\theta)\,p(E_t\mid S_t,\theta),
\]

where `x` is statute text, `E` is process evidence, `r` is an interpretation, `S` is a process design, and `theta` describes timings, participation, and reporting. In the implementation, some of these distributions are fixed hypotheses rather than inferred quantities.

### Good design choices

- **Process structure is not inferred from timing alone.** Step mentions, agency listings, and boundary events contribute separate evidence.
- **Case paths are marginalized.** Enumerating correction counts and hearing participation avoids hundreds of weakly informed case-level coordinates.
- **Shared step laws can borrow strength across towns.** A design with a separately observed step can help identify the same step elsewhere, conditional on the sharing assumption.
- **Interpretation is distinguished from behavior.** Observing a hearing does not automatically mean the agency believes a hearing is legally mandatory.
- **The code exposes important assumptions.** The documentation already acknowledges serial-only designs, the failed W4 gate, the Q5 generator problem, and fixed choice parameters. Those disclosures should be retained.

### Limits of the current unification

**The process universe is supplied.** The fitter chooses among 11 hand-enumerated serial designs, using a supplied step vocabulary and a maximum of four correction loops. It does not discover an arbitrary graph, missing step types, alternative actor assignments, or parallel branches. Its posterior on step counts is conditional on that menu and repeat cap. A residual legal reading still chooses among the same 11 designs; it is not an unknown-process component.

**The parser does not compile the whole graph.** Elicitation assesses prelisted skeleton elements and questions, but uncertainty in those skeleton elements is not generally carried into the fitted graph. The six elicitors' disagreement with the hand-coded denial-ground restriction is a useful example already acknowledged in the round-4 report.

**The outcome link is intentionally a cut.** It approximates

\[
p_{\mathrm{cut}}(\theta,\phi\mid E,O)
=p(\theta\mid E)\,p(\phi\mid O,\theta),
\]

not the full joint posterior in which outcome evidence can update process parameters. Equal pooling of conditional outcome fits is appropriate for that cut target. A cut is a defensible modularization, but should not be described as unrestricted full-chain learning.

**Town speed is not intrinsic agency capability.** It is a common log-duration shift for a prescribed set of agency-paced steps. Without workload, case difficulty, staffing, and comparable task assignments, it also absorbs these differences. It does not establish a task-by-agency capability hierarchy, and the toy does not estimate agency labor effort separately from elapsed time.

**Source heterogeneity is only partly represented.** Mention/listing sensitivity, false positives, and report noise are modeled. There is not yet a general source-type bias, document dependence, and forum-selection hierarchy comparable to the broader real-data ambitions.

**Counterfactuals assume stable mechanisms.** Replacing a process with S1 while holding remaining step laws, case composition, fees, and outcome mechanisms fixed is an intervention assumption. A legal edit permitting S1 does not prove an agency will adopt S1, or that the remaining work will take the same time. Variation across towns alone also does not identify causal safeguard effects without assumptions about selection and confounding.

## 4. Confirmed likelihood defects

### F1. Outcome counts overlap; independent Poisson thinning does not apply

Severity: high. Sources: [outcomes.py](../pipeline/procbench/toy_statute/outcomes.py), `rates` and `loglik` (approximately lines 137 and 206); [generate.py](../pipeline/procbench/toy_statute/generate.py), `generate_outcomes`.

The generator allows a denied applicant to keep hens without a permit and subsequently generate a complaint. Therefore a person can contribute to both:

- the denial count `D`; and
- the verified or unfounded unpermitted-complaint count `Vu` or `Nu`.

The likelihood multiplies independent Poisson terms for all these counts. Independent thinning applies to **disjoint** person-level categories, not overlapping totals.

Let `m` be the Poisson arrival mean, `p` the application probability, `pi` the nuisance prevalence, `c` the nuisance detection probability, `f` the harmless-coop false-flag probability, `u` the probability of keeping without permission, and `k1/k0` complaint probabilities. Then

\[
\operatorname{Cov}(D,V_u)=mp\pi c u k_1,\qquad
\operatorname{Cov}(D,N_u)=mp(1-\pi)fu k_0.
\]

Both are generally positive. The hidden uncomplained-unpermitted cell also overlaps denials, so its survey contribution is not independent of `D` either.

At the saved ordinary-world truth, the implied correlations between denials and verified unpermitted complaints are **0.384, 0.324, and 0.286** for Alder, Birch, and Cedar. These are not just hypothetical corner cases.

**Consequence:** the product is a composite/pseudo likelihood, not the advertised exact likelihood. It can distort uncertainty and parameter estimates. This audit has not quantified how much of each reported outcome error it causes. In particular, the existing attribution of deterrence bias entirely to the burden input is not established until this defect is separated from that explanation.

**Recommended repair:** construct exclusive latent categories distinguishing denied applicants from non-applicants, then marginalize the unobserved cross-tabulation. Alternatively, condition the denied-person subcategories on the observed denial count and combine them with independent non-applicant arrivals. Do not simply remove the observations. A small generator-versus-joint-likelihood check should precede any expensive refit.

### F2. Completed applicant reports require selection inside latent-time integration

Severity: high. Sources: [generate.py](../pipeline/procbench/toy_statute/generate.py), `make_report`; [model.py](../pipeline/procbench/toy_statute/model.py), `town_struct_loglik` (approximately lines 337–401).

The generator samples a posting day `C`. A report is pending when `C < T`, where `T` is actual completion time; otherwise it contains noisy, rounded completed gaps. The completed report does not retain `C`.

For a simplified total-time report `Y`, the joint contribution is

\[
p(Y,\mathrm{completed}\mid\theta)
=\sum_T p(T\mid\theta)\,P(C\geq T)\,p(Y\mid T,\theta).
\]

The current completed-report kernel integrates the time/reporting distribution without the `P(C >= T)` factor. Pending reports do contribute a survival term.

The qualification matters: **if actual completion time were observed exactly**, the independent-censoring factor could be a parameter-independent multiplier and safely omitted from inference. Here actual times are latent beneath noisy/rounded reports, so the factor sits inside the sum and cannot generally be dropped. With several gaps, selection must be applied to their latent total, not independently to each reported gap.

There is a second mismatch: pending survival is contaminated at the fixed 2% rate, although the generator determines pending status from the uncontaminated true total before report contamination is applied.

**Consequence:** this is not exactly the generator's observation model. It can affect inferred durations and path frequencies. Its numerical impact on the saved fits remains unmeasured; abundant administrative evidence may mitigate it.

**Recommended repair:** explicitly represent observation/posting time and integrate the selection event with latent durations, or use the correct coarsened-data likelihood for the available fields. This is separate from a future model of who chooses to post on a forum.

### F3. FFT sums can alias, and segment truncation changes the model

Severity: medium for inspected fits; potentially high outside their regime. Source: [grid.py](../pipeline/procbench/toy_statute/grid.py), `conv_from_counts` (line 58), with callers in the model and estimands.

Each individual duration has support 0–511, but the FFT length is 1,024 regardless of the number of summed durations. Multiplication in that FFT domain produces a circular convolution when the sum's support exceeds the padding. The result is then cropped to 0–511 and renormalized.

Direct reproduction: three deterministic 400-day durations produce a point mass at **176 days**, because `1200 mod 1024 = 176`, instead of 1,200 days.

Even without wraparound, cropping and renormalizing conditions a segment's total to remain below 512. The generator truncates individual steps, not their sum. Day observations are also clipped to the grid boundary. The hour grid has the analogous issue.

**Impact qualification:** comparing correctly padded sums for eight inspected saved particles per world, using each town's MAP design, found maximum mean discrepancies of about **0.055 days in W0, 0.206 days in W1, and 0.063 days in W4**. This is not evidence that FFT aliasing explains the major present failures. It is evidence that “exact for the generator” is too strong and that wider priors or slower processes can break the implementation.

The truth scorer calls the same estimand machinery, so a shared numerical error can disappear from a recovery comparison.

**Recommended repair:** sufficient padding for each supported sum, explicit treatment or bounds for overflow, and a grid-refinement check. Use independently simulated truth for at least one check. Grid length is a numerical accuracy choice, not a parameter to infer.

## 5. Reading inference: identification and scoring

### F4. Residual interpretation and compliance slack are exactly confounded

Severity: high for the interpretation claim. Source: [readings.py](../pipeline/procbench/toy_statute/readings.py), `reading_prior`, `choice_logprob`, and `stage_c`.

For independent town readings (`kappa = infinity`), let `rho` be residual-reading mass, `epsilon` the uniform choice slack, and `g_r(S)` a normalized choice distribution under a known reading. The residual chooses uniformly among `D` designs. Marginalizing the reading gives

\[
p(S)=(1-\rho)(1-\epsilon)\sum_r p_0(r)g_r(S)
 +[\rho+(1-\rho)\epsilon]/D.
\]

Only the combination

\[
\eta=\rho+(1-\rho)\epsilon
\]

is observable through design choice. This remains true with uncertain process parameters and costs because the equality holds at each parameter value.

The saved results provide a direct demonstration, under P-pool, cost temperature 15, and independent towns:

| Settings | Log marginal ratio | Mean residual posterior |
|---|---:|---:|
| `rho=.05`, `epsilon=.15` | −8.745461721045226 | 0.16434 |
| `rho=.15`, `epsilon=.05` | −8.745461721045196 | 0.49302 |

The largest difference in their design posteriors is approximately `2.3e-14`.

**Consequences:** the data cannot say whether an unexpected design means an unenumerated reading, noncompliance, or the stipulated choice model is wrong. The residual is a conditional lack-of-fit indicator, not an identified probability that the legal reading is missing. The finite-kappa hierarchy changes assumptions about cross-town dependence; it does not justify asserting that the independent-town confounding is resolved by process evidence.

**Recommended treatment:** learn a single unexplained-choice component, or separately anchor legal interpretation/compliance with additional evidence. Do not add free priors to both parameters and call their prior-dependent separation learned.

### F5. Thirty-two readings reduce to five validity patterns

Severity: high for claims of recoverable interpretation. Source: `validity_matrix` in [readings.py](../pipeline/procbench/toy_statute/readings.py).

Enumerating W4's 32 readings over its 11 designs yields **five distinct validity rows**. Flipping Q4 changes zero rows; flipping Q5 also changes zero rows. Thus readings in the same group induce the same design-choice distribution under the implemented choice families, at fixed costs.

Even infinitely many process records do not identify all 32 reading probabilities through this mechanism. At most the behavioral equivalence classes can be distinguished, and even those require sufficient design variation and an identified choice model.

Q5 has **two** obstacles, not one:

1. The generator draws fees independently of Q5, as the existing document acknowledges.
2. The validity matrix excludes fee items, and the fitted reading likelihood does not connect observed fees to Q5.

Changing the generator alone will not give the fitter a learning path. A fee-policy/reading likelihood, with a declared violation mechanism, is needed too.

**Recommended treatment:** report the equivalence classes and within-class prior dependence. Add information paths only where the observations genuinely distinguish readings. More process cases cannot replace a missing likelihood edge.

### F6. The question scorer treats “unknown” as “No”

Severity: high for reported reading scores. Source: [readings.py](../pipeline/procbench/toy_statute/readings.py), `score_readings` (line 189).

The scorer sums known-reading mass with `Q=yes` but leaves residual mass out, implicitly allocating it to `Q=no`. The residual has no defined answer to those questions.

Under P-pool2, cost temperature 15, slack .05, and independent towns:

- Q4's prior probability is **0.808333**.
- Conditional on a known reading, its posterior remains **exactly 0.808333 in every town**, as the design model implies.
- The reported unconditional Q4 probabilities range from **0.574594 to 0.796833**, solely because residual mass differs.

That apparent movement is a scoring/interpretation artifact, not learning about the clock. The MAP scorer also removes the residual from the competition rather than permitting an unknown outcome.

For known “Yes” mass `a` and residual mass `r`, honest options include reporting `P(yes | known reading)` alongside `r`, or reporting the unidentified unconditional range `[a, a+r]`. Assigning an answer distribution to residual readings is another option, but would be an additional explicit model.

### F7. Q5 remains in the headline joint score

The round-4 report says Q5 is excluded from the headline comparison. `score_readings` nevertheless indexes the full five-question true reading. Therefore the headline −3.36 versus −3.91 comparison includes Q5; only some displayed per-question comparisons omit it.

As a diagnostic, marginalizing Q5 out of the saved known-reading posterior gives Q1–Q4 joint log scores of **−2.226 for P-pool2/cost-15** and **−2.417 for P-flat/cost-15**. Applying the baseline's product-of-question-marginals convention to Q1–Q4 gives **−2.673 for the LLM**. The illustrative Bayesian advantage survives this particular correction, but the published values and scope statement are inconsistent, and the baseline joint score imposes independence rather than eliciting a joint reading distribution.

These corrected numbers do not cure the failed W4 gate, residual semantics, or other model defects. They are not a replacement validated result.

### F8. “Risk aversion rejected” is overgeneralized

Severity: high for the behavioral conclusion. Source: [readings.py](../pipeline/procbench/toy_statute/readings.py), `choice_logprob` (line 97).

The fixed risk preference is proportional to

\[
\exp\{\beta\times\text{number of enumerated readings allowing the design}\},
\qquad\beta=1.
\]

In W4, designs have 8, 16, or 32 allowing readings. A 32-reading design therefore gets `exp(24)`, approximately **26 billion**, times the preference of an 8-reading design before validity restrictions and slack.

Adding an irrelevant binary interpretive question would double all counts and change the effective risk preference, despite changing no substantive legal uncertainty. That is an arbitrary enumeration dependence.

The approximately ten-nat rejection applies to this fixed, extreme model in the independent-town comparison. It is not uniformly that large under finite kappa, and it does not reject a weak or moderate risk preference.

**Recommended treatment:** use a normalized validity fraction or a specified probability mass of legal interpretations, then estimate or systematically vary a regularized risk-strength coefficient. Include zero risk strength as a nested comparison. With 12 towns and uncertain readings, expect weak identification, not a precise preference estimate.

## 6. Mathematical sampling audit

### What is correct

[smc.py](../pipeline/procbench/toy_statute/smc.py) implements tempered sequential Monte Carlo with targets

\[
\pi_b(\theta)\propto p(\theta)L(\theta)^b,\quad 0\le b\le1.
\]

Incremental weights are `L^(b_new-b_old)`, followed by systematic resampling and random-walk Metropolis moves. For the fixed symmetric proposal used within a process-model move stage, the acceptance log ratio is correctly

\[
\Delta\log p(\theta)+b\,\Delta\log L(\theta).
\]

Discrete designs and case paths are summed in the likelihood. Discrete designs are subsequently sampled when producing some estimands; “never sampled” should therefore refer to likelihood evaluation, not every downstream computation.

The block transformation is also correct. Let

\[
T=\log(E_a+E_b),\quad U=\log(E_a/E_b),\quad p=\operatorname{logistic}(U).
\]

Then

\[
\mu_a=T+\log p-\sigma_a^2/2,\qquad
\mu_b=T+\log(1-p)-\sigma_b^2/2.
\]

At fixed spreads, the Jacobian is

\[
\begin{pmatrix}1&1-p\\1&-p\end{pmatrix},
\]

with determinant −1. Including the unchanged spread coordinates preserves absolute determinant one. Evaluating the original prior without an additional Jacobian term is right. This improves geometry; it does not add information about an unobserved split.

Stage-C reweighting has the right algebra **when Stage B used the assumed uniform design prior and the same continuous prior**. Writing `L_tS(theta)` for each town/design likelihood, the ratio is

\[
R(\theta,w)=\prod_t
\frac{\sum_r w_r\sum_S p(S\mid r,\theta,\psi)L_{tS}(\theta)}
{D^{-1}\sum_S L_{tS}(\theta)}.
\]

Self-normalized importance weights then approximate the new posterior. The identity is exact; integration with a finite, potentially unconverged particle population is not.

### What the current diagnostics do not establish

**SMC particles are not an MCMC chain.** `compare_runs` feeds two arrays of ordered, resampled particles into rank R-hat as if they were chains. This may detect ensemble differences, but the ordering is not a Markov time series and systematic resampling introduces genealogical dependence. It is not the usual MCMC convergence certificate. Rank-normalized R-hat was developed for chains; SMC has its own variance theory. See [Vehtari et al.](https://arxiv.org/abs/1903.08008) and [Chopin](https://arxiv.org/abs/math/0508594).

**Two similar runs can agree on the same error.** Between-run standardized mean differences are useful, but cannot establish model adequacy or exclude missed modes. Two runs provide limited information about Monte Carlo error. The reported `unique_ancestors` is per resampling step, not full particle genealogy.

**The estimand gate adds its own noise.** `answers_from_draws` uses only 1,000 draws even when the fit contains many more particles, and samples discrete structures. The gate estimates standard deviation from a 90% interval divided by 3.29, assuming a roughly Gaussian shape. Discrete day quantiles can jump by one day and fail such a gate despite stable parameter means. W0/fitC001 passes the parameter part but fails one estimand. Conversely, passing this gate does not validate tail behavior.

**Finite-kappa integration has only 50 population-weight draws.** The 2,000 process particles are crossed with the same 50 Dirichlet draws. The resulting 100,000 pairs are not 100,000 independent posterior samples. The reported `1/sum(weight^2)` over pairs is a weight-concentration diagnostic, not a validated independent effective sample count. Replicating each process particle would multiply that ESS without adding information about population weights. Report marginal weight concentration for each axis and repeat the integration with independent seeds and more population-weight draws before interpreting small log-evidence differences.

**Outcome gate comparisons share their outer process approximation.** Both outcome runs use the same 24 selected process groups. Their agreement assesses conditional outcome Monte Carlo stability, not error from approximating the process posterior by 24 groups. This is a limitation of the diagnostic, not a reason to reject cut inference itself.

**Stage C has a reuse hazard.** It assumes a uniform Stage-B design prior; it does not enforce that assumption, and its `particle_logprior_correction` argument is unused. W4 did use a uniform prior, so this is not the cause of its current results. Reusing Stage C on an LLM-prior fit without the appropriate ratio would be wrong.

**A smaller initialization mismatch exists.** Beta draws are clipped to `[1e-4, 1-1e-4]` before conversion to logits, while `log_prior` represents the unclipped Beta distribution. Initial particles are therefore not exactly from the stated prior. This is likely a small effect in these settings, but is another reason not to claim finite-run exactness.

Recommended numerical checks are limited and targeted: independent repeated SMC runs with Monte Carlo error estimates on the actual outputs; a population-weight integration sensitivity; separate checks of discrete quantiles; and generator-versus-likelihood validation. Increasing particle counts is appropriate only after the target is corrected.

## 7. Hand-set parameters: which should be learned?

“Bayesian” does not mean every constant should receive a prior. Known facts, normative preferences, numerical tolerances, estimable scientific parameters, and unidentified assumptions need different treatment.

| Setting or assumption | Current treatment | Audit recommendation |
|---|---|---|
| Per-step duration locations/spreads; correction and hearing probabilities | Sampled with fixed prior families | Keep learning them where observations distinguish them. Report composite-only information and prior-sensitive splits separately. |
| Town log-speed spread | Fixed prior SD `0.3` | A hierarchical spread can be learned with enough comparable towns/tasks. With few towns, use externally calibrated priors plus sensitivity. Remove the unused common raw-town coordinate with a contrast parameterization. Do not call the remaining effect intrinsic capability. |
| Mention sensitivity/false positives and webpage listing sensitivity/false positives | Already sampled; Beta priors such as `(2,1)` and `(1,20)` | These are not fixed detection probabilities. Check their identification and transferability; calibration across labeled documents/statutes is more informative than adding unconstrained source-specific parameters. |
| Duration/hour report noise | Already sampled, globally | Source-specific bias and noise may be warranted with matched boundaries and independent source overlap. Do not confound them with case variability or treat repeated reports as independent corroboration. |
| Contamination rate | Fixed `0.02` | Learn a regularized rate, preferably by observation type, when there is enough information; otherwise calibrate externally and show sensitivity. First put contamination at the correct point in the observation model. |
| Posting-time distribution | Generator supplies it; completed likelihood does not implement it | Include the actual observation mechanism for the toy. For real data, infer or calibrate selection only with supporting information; otherwise report sensitivity/partial identification. |
| Choice temperature `tau` | Fixed at 15 or 40 | A candidate learned parameter, using repeated agency choices and fixed utility units. Twelve towns may not separate it from uncertain readings and costs; report weak identification rather than plug in the true generator value as a general solution. |
| Risk strength | Fixed `beta=1` multiplying raw reading counts | Normalize the risk measure, then estimate or vary strength. Current rejection is of an extreme setting. |
| Compliance slack `epsilon` and residual mass `rho` | Fixed grid values `.05/.15` | Do not freely learn both from this likelihood: exact confounding. Learn their combined unexplained-choice mass, or acquire independent anchors that distinguish them. |
| Population concentration `kappa` | Grid: 3, 10, 30, infinity | Could be inferred across enough informative jurisdictions/statutes. Current equivalence classes and integration precision limit interpretation. Integrate its uncertainty rather than select whichever grid value scores best against truth. |
| Question prior pooling weights | Hand-weighted LLM/direct/frequency/RSA sources | Calibrate on held-out interpretation tasks or multiple worlds/statutes. Repeated outputs of one LLM are correlated elicitation, not independent evidence. Same-statute choice data cannot generally identify elicitor reliability. |
| LLM duration-prior mix and widening | 80% LLM / 20% vague; width multiplied by 1.5 | Treat as calibration choices, not learned quantities. The elicitation asks for ranges across towns and cases, then uses them as uncertainty about a location parameter; separate population variability from epistemic uncertainty before calibration. |
| RSA parameters and Q1 mapping | Rationality 4, utterance cost 1, selected degree priors, plan quantile .7, pool weight .5 | These form an illustrative prior, not validated legal semantics. Need external language/interpretation data to learn them. Process data silent on the relevant reading cannot validate the mapping. |
| Burden weights | `days + 4*hours + dollars/5` | If normative policy weights, elicit and vary them; the timing likelihood cannot learn what society should value. If behavioral tradeoffs, learn from choices/outcomes with a scale normalization and adequate variation. Applicant burden is not automatically the agency's objective. |
| Outcome detection, false flags, complaint, keep-anyway, and deterrence parameters | Already sampled; shared or hierarchical nuisance prevalence | Repair the joint likelihood first. Add denial reasons, denied/non-applicant follow-up, and within-town changes for stronger identification. More arbitrary free parameters will not separate products observed only in aggregate. |
| Published fee amounts | Treated as known | Appropriate when the schedule is genuinely exact and applicable. Unknown fees/splits require a likelihood or an explicitly prior-driven uncertainty allocation, not a deterministic inferred fact. |
| Missing-fee allocation | Residual median, equal split or `Dirichlet(1)` split | Equal splitting hides ignorance; Dirichlet splitting expresses an assumption, not learning. Model fee evidence if the split matters. |
| Statutory 30-day limit | Fixed from explicit fictional text | Keep fixed. Uncertainty in clock scope belongs in interpretation; actual compliance belongs in the process model. |
| 14-day comment / 10-day hearing-notice design floors | Hand-specified validity properties | Justify with observed local rules or retain as explicit hypothetical design constraints. They are not consequences of the statute's literal text and are not generally enforced by the stochastic duration laws. |
| Serial design menu, known actors, repeat cap four | Fixed hypothesis space | Reasonable for a controlled toy, but not a learned complete process universe. Expand only when supported; check cap sensitivity or bound the omitted tail. |
| Grid sizes, particle counts, quadrature nodes, gate thresholds | Fixed numerical choices | Set by error control, computational diagnostics, and a predeclared evaluation protocol—not Bayesian learning. |

The key distinction is **learnable in principle versus identified by this dataset**. Putting a hyperprior on an unidentified setting does not make the resulting marginal posterior evidence-driven. Posterior contraction is useful, but not a proof of identification: it can arise from constraints, correlated parameters, and strong likelihood assumptions. Report predictive sensitivity and identified parameter combinations as well.

## 8. Fee implementation is still partly plug-in

Source: [model.py](../pipeline/procbench/toy_statute/model.py), `fee_table`; [fit.py](../pipeline/procbench/toy_statute/fit.py), `answers_from_draws`; [readings.py](../pipeline/procbench/toy_statute/readings.py), `run_stage_c`.

Fees do not enter the process likelihood. A missing item is reconstructed from the median reported total minus listed items. If multiple items are missing, a separately enabled random split expresses uncertainty.

Two implementation consequences deserve attention:

1. `answers_from_draws(..., random_fee_split=False)` remains the default, and the standard SMC driver does not override it. Historical `answers_feefix` recomputations may be corrected, but an ordinary new fit still defaults to equal splitting. The fix is not integrated into the normal output path.
2. Stage C selects each particle/town's maximum-likelihood design to construct a fee table, then uses that table for costs across every candidate design. This is a data-dependent plug-in, not integration over design/fee uncertainty in a fully generative model. Counterfactual fees for steps absent from the current process are also assumptions, not observations.

Recommendation: preserve exact schedule facts, model uncertain fee totals and itemization explicitly if required, and distinguish empirical reconstruction from posterior learning. The small toy does not need a large new fee hierarchy just to admit that a split is unknown.

## 9. Results audit: what reproduces and what follows

### Process and sampling results

| Saved result | Reproduced observation | Interpretation |
|---|---|---|
| W0/fit004 | Gate passes; worst reported R-hat 1.0044, SMD .09865 | Useful baseline numerical agreement, subject to the diagnostic and likelihood caveats above. |
| W0/fitB001 | Gate fails; worst SMD .11485 | The block transform did not make every run pass. |
| W0m/fitB001 | Gate passes; worst SMD .09537 | Supports the practical value of boundary information and improved geometry. |
| W0x25/fitB001 | Gate fails: seven parameters and one estimand; worst SMD .13246 | Improved scores are promising, not a cleanly certified posterior. |
| W4/fitB001 | Gate fails: **39 parameters, 53 estimands**; worst R-hat 1.0369, SMD .47059 | Reading/cost conclusions inherit substantial unresolved numerical uncertainty. |
| Six locally present round-3b fitC diagnostics | Three pass; three fail | More particles helped some conditions, but did not establish a universal cure. W0x5/W0x25 fitC results were not present locally in this audit. |

The W4 runs' estimated log normalizers differ by about **0.956 nats**. This does not translate directly into an error bar for every Stage-C comparison, but is another reason not to overinterpret small evidence differences without repeat calculations.

The fact that all 12 true designs are MAP choices is meaningful. It does **not** make their posterior probabilities immune to a failed gate, nor validate within-design duration, interpretation, or preference estimates. Many parameter distributions can imply the same MAP design.

### Bayesian versus LLM scores

The reported numerical pattern reproduces:

- W0 round 3: mean nontrivial scaled interval score **1.166 Bayes versus .897 LLM**.
- W0m: **1.040 versus .882**.
- W0x5: **.584 versus .638**.
- W0x25: **.394 versus .528**.
- W1 and W1m also show improvements for some Bayesian variants over the LLM.
- Outcome results reproduce the reported strong LLM baseline and the improvement from shared to hierarchical nuisance prevalence in the adversarial world.

Those observations are encouraging but are not a clean general superiority result, for four reasons:

**Method-dependent denominators.** In [score.py](../pipeline/procbench/toy_statute/score.py), `summarize` excludes a zero-truth estimand only when that particular method supplies a zero-width interval at zero. Thus methods average different item sets. W0 uses **92 Bayesian versus 96 LLM** “nontrivial” estimands; W0x25 uses **92 versus 95**. The paired `head_to_head` comparison has a more consistent common-set treatment. Headline means should also use a predeclared common set.

**Truth-dependent score scaling.** The interval score is divided by `max(abs(truth), floor)`. This is a useful relative-error convention if declared as such, but truth-dependent reweighting does not retain the usual proper-scoring guarantee across repeated outcomes. Report unscaled proper scores within families, or use fixed external scales. Family weights and floors are evaluation choices and should not be tuned to produce a preferred winner.

**Coverage across estimands is not repeated-sampling calibration.** Many entries are correlated functions of one fitted world. A reported 92% coverage across them is descriptive; it is not proof of calibrated 90% posterior intervals. The outcome replication holds the process posterior fixed, so it does not test calibration of the whole pipeline.

**Comparison scope.** The toy supplies a small correct step vocabulary, structured fields, and strong shared assumptions. It is a favorable test bed, not proof that the model can recover the same quantities from heterogeneous real forum records. Averaging LLM quantiles is an ensemble forecast convention, not a Bayesian posterior mixture; it should be labeled as such, with per-repeat scores retained.

The reading comparison needs the Q5/residual corrections described above. The outcome comparison must be rerun under a valid joint likelihood before its uncertainty claims are accepted.

## 10. Existing tests: useful, but not testing the failing assumptions

All 32 toy tests pass. That is evidence of internal consistency in tested cases, not a contradiction of this audit.

- The FFT test uses short distributions and compares with a similarly cropped/normalized convolution. It does not test wraparound or preservation of generator tail mass.
- The outcome partition test checks some marginal identities, not whether denials and unpermitted complaints are disjoint or their joint covariance matches the likelihood.
- The survey summation test checks a limited parameter regime. The production routine uses up to 241 selected integer nodes, with a renormalized Riemann-sum approximation when needed; it is not universally an exact sum.
- The reparameterization test is valuable and supports the unit-Jacobian conclusion.
- Stage-C tests establish normalization and simple design recovery, not residual/slack identification, residual question semantics, or finite-kappa integration precision.
- The truth-import guard does not establish complete historical provenance or end-to-end freedom from modeling choices informed by the generator. I found no demonstrated hidden-truth import in the audited fitting path; that is different from certifying all forms of benchmark leakage.

No broad testing/refactoring campaign is needed before fixing these issues. A few small counterexample tests directly tied to the mathematical claims would be more useful than another large verification queue.

## 11. Recommended sequence after approval

These are recommendations only; none was implemented as part of this audit.

1. **Repair correctness before increasing compute.** Fix the overlapping outcome likelihood, the coarsened completion-selection likelihood, residual question scoring, and Q5 scoring scope. Fix or explicitly bound FFT tails and aliasing.
2. **Correct the inferential claims.** State that unknown-reading mass is confounded with slack; report reading equivalence classes; qualify the risk-choice rejection; keep relative town speed distinct from intrinsic capability.
3. **Integrate small existing fixes.** Make uncertain fee allocation explicit in the normal answer path. Assert Stage-C prior compatibility. Stop calling a finite importance calculation an exact posterior.
4. **Use one compact recovery experiment.** Check the corrected generator/likelihood pair, run a small set of independent fits, and compare with the same-evidence LLM on a fixed common estimand set. Include an independently computed truth check. Preserve failed results rather than replacing them.
5. **Only then expand learning of hand-set quantities.** Start with identifiable reporting/contamination parameters and suitably normalized choice strength. Learn shared scales from multiple informative jurisdictions/statutes. Do not simultaneously free residual mass, noncompliance, elicitor reliability, and agency preferences on a single small world.
6. **Test what matters for the real-data objective.** Separate process-menu recovery, completed-case clock recovery, repeat counts, source bias, and relative agency effects. Require evidence at the relevant boundaries before promoting individual-step durations or capability to headline estimates.

### Bottom line

Keep the Bayesian architecture and the useful computational work. The main problem is not that Bayesian learning is inherently too weak or that every parameter needs to be hand-set. It is that several modeled observations do not currently have the claimed joint likelihood, some probabilities are scored with the wrong semantics, and multiple hand-set components are observationally indistinguishable.

Correct those issues first. Then a modest, well-defined recovery experiment can tell us what the data actually teach the model, instead of asking a larger sampler to settle a question the likelihood or design cannot answer.
