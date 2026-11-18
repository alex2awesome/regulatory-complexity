# Complexity measures for statutes and their implementations: survey and candidates (2026-09-26)

Purpose: (1) record what we could and could not confirm about Avrim Blum's work
applying complexity-theory ideas to everyday domains (a lead from Kevin Stangl);
(2) survey complexity measures from law, theory of computation, process mining
and public administration; (3) propose candidate measures for our frame
(statute -> decision model -> per-jurisdiction process models -> observations,
`docs/CORE_GOAL.md`) and say how each would be computed on the toy hen-permit
statute (`docs/2026-09-26-toy-statute-plan.md`, sections 2, 3, 6).

Every citation below was found in a search result or fetched page on
2026-09-26. Where only the citation (not the paper text) was seen, that is
noted. Nothing here has been implemented or computed on data yet; toy numbers
are structure-only arithmetic that needs no truth values.

## 1. Avrim Blum and collaborators: what was found

**Could not confirm the specific work Kevin meant.** The findings, in order of
how well they fit "complexity ideas applied to colloquial domains":

1. **Human-computable passwords are Manuel Blum's, not Avrim's.** The
   humanly-usable password line is by Manuel Blum (Avrim's father) and
   collaborators: Blum and Vempala, "Publishable Humanly Usable Secure Password
   Creation Schemas", HCOMP 2015
   (https://ojs.aaai.org/index.php/HCOMP/article/view/13233; the title says
   "Schemas", not "Schemes"); Blocki, Blum, Datta and Vempala, "Towards Human
   Computable Passwords", ITCS 2017 (https://arxiv.org/abs/1404.0024); and
   Blum and Vempala, "The complexity of human computation via a concrete model
   with an application to passwords", PNAS 117(17), 2020
   (https://www.pnas.org/doi/10.1073/pnas.1801839117; full text
   https://pmc.ncbi.nlm.nih.gov/articles/PMC7196832/). The PNAS paper models a
   human as a processor with unbounded long-term memory and a short-term memory
   of two or three chunks. It measures the effort of using a scheme as a pair:
   PREP (one-time cost of memorising a key and learning the scheme) and PROC
   (per-input count of long-term reads plus short-term reads and writes).
   Avrim Blum's publication list
   (https://home.ttic.edu/~avrim/Papers/pubs.html) has no password paper and
   no paper co-authored with Manuel Blum. The user's note ("Avril Blum ... with
   Santosh Vempala on humanly usable password schemes") therefore probably
   mixes up the two Blums. **This is the closest match to "a complexity theory
   of what ordinary people can do", and the source for measure M3 below.**
2. **Avrim Blum's recent theory work on social and legal settings** (all listed
   on his publications page above):
   - "A Machine Learning Theory Perspective on Strategic Litigation" (with Dutz,
     Shao and Aloni Cohen), FORC 2026 (https://arxiv.org/abs/2506.03411). A
     lower court applies a decision rule learned from a higher court's past
     rulings, and a litigator chooses which cases to bring in order to shape
     it. This is the only law paper found. It bears on how vague standards
     harden through precedent, not on burden.
   - "Pessimism Traps and Algorithmic Interventions" (with Diana, Ravichandran
     and Tolbert), FORC 2025 (https://arxiv.org/abs/2406.04462), and "A
     Theoretical Model for Grit in Pursuing Ambitious Ends" (same authors),
     AAAI 2026 (seen only on the publications page). Information cascades and
     improving bandits applied to everyday social phenomena, with a
     philosopher co-author. Of Avrim's own work, this line best fits
     "colloquial".
   - "Revealing Positive and Negative Role Models to Help People Make Good
     Decisions", TMLR 2026: choosing examples for a brochure, framed as set
     cover (publications page).
   - "Proofs as Explanations: Short Certificates for Reliable Predictions",
     COLT 2025 (publications page): the smallest subset of the training data
     that certifies a prediction. Related to M1.
   - "Ignorance is Almost Bliss: Near-Optimal Stochastic Matching With Few
     Queries", EC 2015 (publications page): kidney exchange with a limited
     number of *rounds* of queries. Related to M7.
3. **Kevin Stangl's own co-authored work on screening pipelines.** Blum,
   Stangl and Vakilian, "Multi Stage Screening: Enforcing Fairness and
   Maximizing Efficiency in a Pre-Existing Pipeline", FAccT 2022 (publications
   page): cheap early screens followed by an expensive accurate test. Cohen,
   Sharifi-Malvajerdi, Stangl, Vakilian and Ziani, "Sequential Strategic
   Screening", ICML 2023 (https://arxiv.org/abs/2301.13397): with sequential
   tests, applicants can "zig-zag" between them instead of satisfying all at
   once. Both treat multi-step administrative screens as the object of study.

**Recommendation:** ask Kevin whether he meant (a) Manuel Blum and Vempala's
human-computation model, (b) Avrim's grit, pessimism-trap and litigation work,
or (c) something unpublished or given as a talk. No Avrim Blum paper on
bureaucracy or statutory complexity was found.

## 2. Survey of relevant measure families (short)

- **Legal-text complexity.** Katz and Bommarito measure US Code titles by
  structural size, citation flow and linguistic entropy
  (https://link.springer.com/article/10.1007/s10506-014-9160-8). Ruhl and Katz
  propose network "Legal Maps" for monitoring complexity
  (https://ilr.law.uiowa.edu/print/volume-101-issue-1/measuring-monitoring-and-managing-legal-complexity).
  Schuck breaks legal complexity into density, technicality, differentiation
  and indeterminacy (https://scholarship.law.duke.edu/dlj/vol42/iss1/1/).
  All of these measure the text only and cannot see implementation.
- **Formalisation.** Lawsky models statutory reasoning as default (defeasible)
  logic (https://scholarship.law.ufl.edu/ftr/vol21/iss1/2/). Catala compiles
  statutes into executable code (https://arxiv.org/abs/2103.03198). Both
  presuppose resolved ambiguity. Our frame keeps vagueness explicit instead.
- **Rules versus standards.** Kaplow: rules cost more to promulgate, standards
  cost more to interpret and apply case by case
  (https://scholarship.law.duke.edu/dlj/vol42/iss3/2/). Kaplow's model of
  optimal complexity covers the cost of acquiring information about a more
  detailed rule (https://academic.oup.com/jleo/article-abstract/11/1/150/814989).
  This is the economic backbone for a "cost of vagueness".
- **Boolean decision-rule complexity.** Deterministic query complexity D(f),
  certificate complexity C0/C1, sensitivity and block sensitivity (Buhrman and
  de Wolf survey,
  https://www.sciencedirect.com/science/article/pii/S030439750100144X). The
  cost-weighted version is sequential testing: order costly tests to learn a
  system's state (Ünlüyurt review,
  https://www.sciencedirect.com/science/article/pii/S0166218X04001404).
- **Interaction.** Communication complexity (Yao 1979, STOC,
  https://dblp.org/rec/conf/stoc/Yao79.html) and round hierarchies (Nisan and
  Wigderson, https://epubs.siam.org/doi/10.1137/0222016). Interactive proofs
  and "knowledge complexity", meaning what a verifier learns beyond the fact
  proved (Goldwasser, Micali and Rackoff,
  https://epubs.siam.org/doi/10.1137/0218012).
- **Learning and teaching.** Teaching dimension: the minimum number of
  examples that identifies a concept within a class (Goldman and Kearns,
  https://www.sciencedirect.com/science/article/pii/S0022000085710033).
  Description length: Kolmogorov complexity
  (https://link.springer.com/book/10.1007/978-0-387-49820-1) and MDL
  (Rissanen,
  https://www.sciencedirect.com/science/article/abs/pii/0005109878900055).
  Strategic classification covers applicants gaming a rule
  (https://arxiv.org/abs/1506.06980).
- **Process-model metrics.** McCabe cyclomatic complexity V(G)=E-N+2P
  (https://ieeexplore.ieee.org/document/1702388/). Cardoso's control-flow
  complexity, which scores XOR/OR/AND splits (paper page:
  https://www.semanticscholar.org/paper/Business-Process-Control-Flow-Complexity:-Metric,-Cardoso/be086d6da1ade765ffe7bdde49f1b2a5d95d180f;
  venue not verified). Mendling's structuredness, cyclicity and connectivity,
  which predict modelling errors
  (https://link.springer.com/book/10.1007/978-3-540-89224-3). Entropy of
  event-log variability (Back, Debois and Slaats,
  https://link.springer.com/article/10.1007/s13740-019-00105-3).
- **Parallelism.** Critical-path method (Kelley and Walker 1959,
  https://dl.acm.org/doi/10.1145/1460299.1460318) and work versus span
  (Blumofe and Leiserson, https://dl.acm.org/doi/10.1145/324133.324234).
- **Administrative burden.** Learning, compliance and psychological costs
  (Moynihan, Herd and Harvey, JPART 2015,
  https://academic.oup.com/jpart/article-abstract/25/1/43/885957; Herd and
  Moynihan's 2018 book,
  https://www.russellsage.org/publications/book/administrative-burden).
  "Matching to categories" as a source of learning and compliance cost
  (Moynihan, Giannella, Herd and Sutherland, JPART 2022,
  https://academic.oup.com/jpart/article/32/4/750/6503689). The Standard
  Cost Model computes price x quantity for information obligations
  (https://ec.europa.eu/eurostat/documents/64157/4374310/11-STANDARD-COST-MODEL-DK-SE-NO-BE-UK-NL-2004-EN-1.pdf/e703a6d8-42b8-48c8-bdd9-572ab4484dd3).
  Cognitive load theory (Sweller 1988,
  https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1202_4).

## 3. Toy decision model as a Boolean rule

Reading sections 1 and 2 of the toy plan, a permit issues iff
f = x1 AND x2 AND x3 AND x4, where x1 = single-family dwelling, x2 = at most
six hens, x3 = complete application with site plan (§2, §4) and
x4 = "will not create a nuisance" (§3, vague). The deadline (§4) and the fee
(§5, vague amount) sit on top of f.

For an AND of four variables, D(f) = 4, s(f) = 4, C1(f) = 4 (a grant needs
all four facts) and C0(f) = 1 (a denial needs one failed fact). What differs
between the variables is who can produce the certificate, and at what cost.
For x1–x3 the statute fixes the certificate, although "complete" leaves some
room. For x4 it does not: the S1–S6 menu is precisely a menu of certificate
procedures for x4. S1 uses the site plan already submitted. S2 and S3 use a
physical inspection. S4 uses notice, a 14-day comment period, and a hearing if
anyone objects. S5 and S6 combine notice with inspection.

## 4. Candidate measures

Notation: j = jurisdiction and S_j its structure. The already-computed
estimands are E[p-steps], applicant-facing interactions, path entropy, CV of
total days and D2 implementation variety.
"Vagueness-sensitive" means the measure separates what the statute leaves
open from what a jurisdiction chooses.

**M1. Cost-weighted grant certificate (C1^w) and denial asymmetry.** Source:
certificate complexity (Buhrman and de Wolf); short certificates (Blum et al.,
COLT 2025). (a) Decision model: for each d-step, is the certificate fixed by
the statute (concrete) or left open (vague)? (b) Process model: C1^w_j is the
applicant's minimum hours, dollars and days needed to establish f = 1 under
S_j. Separately, record whether the agency must state *all* failed conditions
at once, or may stop at a single C0 witness. What it adds: current measures
count steps. They do not say how much of the burden is irreducible proof of
eligibility and how much is procedure. Minimal (one-at-a-time) deficiency
notices are a mechanism behind correction loops. Toy: C1^w for x4 is about 0
under S1, 14 or more days under S4, and inspection hours plus fee under
S2/S3. Data: step burden posteriors (already estimated). Lever: specify the
evidence that satisfies §3; require a single consolidated deficiency notice.
Vagueness-sensitive: yes, because only x4 has an open certificate.

**M2. Ordering regret (expected evaluation cost, actual versus optimal
order).** Source: sequential testing (Ünlüyurt); "Multi Stage Screening"
(Blum, Stangl and Vakilian). (b) E_j[cost of the steps executed] minus the
minimum over statute-admissible orders. For an AND rule with independent
tests, the classical optimal order runs by ascending cost/P(fail), as the
review describes (not re-derived here). What it adds: it says whether a
jurisdiction spends burden on cases that will fail anyway. Toy: currently
degenerate. The toy generates no denials, so P(fail) is 0 for D2. It becomes
informative in a variant with denial probabilities, for example notice before
completeness. Data: failure rates per step. Lever: statutory ordering, such as
"determine completeness before notice". Vagueness-sensitive: partly.

**M3. Self-assessability (human computability of the rule).** Source: PREP
and PROC (Blum and Vempala, PNAS 2020); learning costs (Moynihan et al.).
(a) The fraction of d-steps whose outcome an applicant can compute in advance
from public text. PREP is the number of distinct facts to learn. PROC is the
number of look-ups and measurements per case. (b) The same after adding the
jurisdiction's published guidance. What it adds: the burden of *not knowing*
whether and how one qualifies, which none of our time, hour or dollar
measures capture. Toy: D1 is computable (checklist plus measuring distances).
D2 is not computable under §3 unless a town publishes criteria. So 2 of 3
d-steps are self-assessable from the statute, and D2's PROC is undefined.
Data: statute and web pages (already in the evidence). Lever: a
**safe-harbour clause** ("a coop at least N feet from property lines is
deemed not a nuisance"), which is the rules-versus-standards move. Strongly
vagueness-sensitive.

**M4. Statutory openness K(P | statute) per d-step.** Source: conditional
description length and MDL (Li and Vitányi; Rissanen). (a) The bits a
jurisdiction must add to the statute to fix the procedure. With a menu
prior π this is H(π_d) per d-step. Compare it with realised variety, the
entropy across towns of the chosen refinements, which we already compute.
What it adds: a property of the *text* that does not depend on how many
towns we observe. Openness minus realised variety shows how much of the
permitted freedom is actually used. Toy: D1 is about 0 bits (one refinement,
up to parameters). D2 plus D3 is log2 6 ≈ 2.58 bits under the uniform prior,
and lower under an LLM prior. Three towns can show at most log2 3 ≈ 1.58 bits
of realised variety. Data: the menu and the prior only. Lever: tells a
drafter which clause carries the openness. Vagueness-sensitive by
construction.

**M5. Extensional disagreement (outcome variety).** Source: Schuck's
"indeterminacy"; Kaplow's application costs of standards. (b) The
probability that a random case would get a different grant/deny decision in
two jurisdictions: E over case pairs and town pairs of 1[f_j(case) ≠
f_k(case)]. What it adds: our variety measure is procedural. Vagueness also
produces different *answers* for identical applicants, which is an equity
cost. Toy: not computable, because the generator has no denial model (for
example, objection-driven denials under S4). Data: denial outcomes by case
features. Lever: tighten the standard, or a safe harbour (M3). Vagueness-
sensitive: yes.

**M6. Applicant learning cost: guidance deficit and teaching dimension.**
Source: teaching dimension (Goldman and Kearns); learning costs (Moynihan et
al.). (b) The posterior entropy of S_j given only the agency's public page,
H(S_j | page). A related quantity is P(page-predicted path ≠ realised path).
Across the class, the teaching dimension is the minimum number of published
facts that identifies S_j among S1–S6. What it adds: transparency, meaning
whether applicants can predict their own path; that is a learning cost.
Toy: with the facts {notice?, inspection?, decided-at-inspection?}, S1, S3,
S4 and S6 each need 2 facts and S2 and S5 need 3, so the class teaching
dimension is 3. Birch's page omits the inspection by design. The guidance
deficit is computed by re-running the Bayes fit on page-only evidence. Data:
pages (already held). Lever: a publication mandate ("the authority shall
publish its review procedure"). Distinguishes jurisdictional opacity from
statutory vagueness; M3 is the statute-level counterpart.

**M7. Interaction rounds (blocking hand-offs).** Source: rounds in
communication complexity (Nisan and Wigderson); few-round querying (Blum et
al., EC 2015). (b) The expected number of alternations in which the case
waits on a different party: applicant, agency or third party. Report the
minimum achievable under the statute alongside. Toy: 1+k (S1), 2+k (S2/S3,
scheduling the inspection), 1+k+h (S4), 2+k+h (S5/S6), with k correction
loops and h = 1[hearing]; the minimum is 1. What it adds: only something if
applicant-facing interactions are counted as touches. Otherwise it is
**largely redundant**, so check the current definition before adopting it.
Neighbours as blocking parties (S4–S6) are the new element. Lever: allow
parallel or consolidated submissions. Mostly procedural.

**M8. Serialisation excess (span versus actual elapsed time).** Source:
critical path (Kelley and Walker); work and span (Blumofe and Leiserson).
(b) E[T_j] minus E[critical path of the same steps under only the
precedence the statute requires]. What it adds: time spent because a town
serialises steps the statute does not order. That is invisible to the mean
and the CV. Toy: in S2 and S5 the inspection could overlap the desk review or
the 14-day comment period. Declare a precedence DAG (D1 completeness before
the §4 clock; D2 before D3) and compute from the step-duration posteriors we
already sample. Lever: "the authority shall conduct notice and review
concurrently". Procedural; the statute sets the floor.

**M9. Deadline coverage.** Source: our own (no external citation). (a, b) The
share of the applicant's elapsed time covered by a statutory clock:
E[decision − complete-application date] / E[decision − first submission].
What it adds: P(>30 days), which we already compute, can be near 0 while most
of the waiting (correction loops) lies outside the clock. Toy: §4's clock
starts at *complete* application, so all D1 loop time is uncovered. Coverage
falls as a town's incompleteness rate rises. Data: already modelled. Lever:
"deemed complete unless notified within N days", or starting the clock at
first submission and pausing it only while the applicant corrects. Separates
the statute (where the clock starts) from the town (loop rate).

**M10. Error sensitivity (loop amplification).** Source: sensitivity of
Boolean functions (Buhrman and de Wolf), adapted to burden. (b) The marginal
change in E[total days] or hours per unit increase in the incompleteness
probability p_j, and the expected loops per applicant error. For geometric
loops (truncated at 4), this is roughly E[loop duration]/(1−p)^2. What it
adds: how harshly a process punishes small applicant mistakes, which matters
for less-resourced applicants. Toy: closed form from the loop posteriors.
Lever: specify the site-plan contents precisely (§2); cure without restart;
consolidated notice (M1). Mostly procedural, but the precision of §2 feeds p.

**M11. Exposure: intrusion and discretionary encounters.** Source:
psychological costs (Moynihan et al.; Herd and Moynihan); knowledge
complexity (Goldwasser, Micali and Rackoff) as the idea of "disclosure beyond
what eligibility requires". (b) The expected number of parties who learn of
the application, P(premises entry), and P(case meets a person with discretion
to deny in the applicant's presence), such as a hearing or an inspection.
Toy: neighbours are informed under S4–S6; premises are entered under S2, S3,
S5 and S6; a hearing occurs with probability P(objection) under S4–S6. What it
adds: burden with no time, hour or dollar trace. Data: structure posterior
plus the objection rate. Lever: forbid or require notice; desk review by
default. Vagueness-sensitive: exposure lives almost entirely in the vague
D2.

**M12. Kaplow break-even for specifying a vague step.** Source: Kaplow 1992
and 1995. (a) N* = (one-time drafting or rulemaking cost + value lost from
local tailoring) / (per-case burden saving from the concrete version). What
it adds: turns the counterfactual estimand into a drafting decision. Toy: the
per-case saving is estimand 7 (the S1 counterfactual). Drafting cost and
tailoring value are *not* in our data and would be declared assumptions.
Lever: statute versus rule versus leaving it vague. Vagueness-specific.

**M13. Monetised burden (Standard Cost Model).** Source: SCM. Total =
population × frequency × (hours × wage + fees), optionally plus a declared
value on waiting days. What it adds: aggregation to a statute-year cost that
drafters and regulatory-impact analysts already use. Toy: straightforward
from estimand 4 once N applications per year is assumed. Low novelty, high
communicative value. Not vagueness-sensitive.

**M14. Cyclomatic / control-flow complexity (V(G), CFC).** Sources: McCabe;
Cardoso. Toy: S1–S3 have V = 2 and CFC = 2 (one correction XOR). S4–S6 have
V = 3 and CFC = 4 (correction plus objection XOR). **Well-defined but likely
useless:** static, frequency-blind and dominated by path entropy. Only use:
data-free screening of real ordinances.

**M15. Structuredness and cyclicity (Mendling).** All six menu structures
are block-structured (structuredness 1), and cyclicity is 2/|N|. **Useless
for us:** these predict *modelling errors* by process designers, not burden.

**M16. Text complexity (Katz and Bommarito; Schuck).** Toy: 5 sections, 1
internal cross-reference ("complete application" links §4 to §2), 2 vague
terms ("nuisance", "reasonable"). **Useless at toy scale**; potentially useful
as a cheap covariate across real statutes. Blind to implementation.

**M17. Gaming and zig-zag vulnerability.** Source: Hardt et al.; Cohen,
Stangl et al. 2023. Defined for sequential screens where applicants can
manipulate features. **Probably irrelevant to burden** in the hen setting;
listed because it is the closest link to Stangl's own work, and it may matter
for benefit programmes.

## 5. Summary table

| # | Measure | Source idea | Level | Toy computable now? | Data beyond current | Drafting lever | Vagueness vs procedure |
|---|---|---|---|---|---|---|---|
| M1 | Cost-weighted grant certificate + denial asymmetry | certificate complexity | d + p | yes | none | specify evidence for §3; one consolidated notice | vague |
| M2 | Ordering regret | sequential testing | p | degenerate (no denials) | failure rates | statutory ordering | mixed |
| M3 | Self-assessability (PREP/PROC) | Blum–Vempala human computation | d (+p) | yes | none | safe harbour | vague |
| M4 | Statutory openness K(P given statute) | description length / MDL | d | yes | prior only | which clause to specify | vague (by construction) |
| M5 | Extensional disagreement | indeterminacy; rules vs standards | p across j | no | denial model | tighten standard | vague |
| M6 | Guidance deficit / teaching dimension | teaching dimension; learning costs | p | yes | none | publication mandate | procedural (opacity) |
| M7 | Interaction rounds | round complexity | p | yes | none | concurrent submission | procedural; maybe redundant |
| M8 | Serialisation excess | critical path; work/span | p | yes | declared precedence DAG | concurrency clause | procedural |
| M9 | Deadline coverage | ours | d + p | yes | none | clock start, deemed-complete | separates both |
| M10 | Error sensitivity | Boolean sensitivity | p | yes | none | precise §2; cure rules | mostly procedural |
| M11 | Exposure (intrusion, discretion) | psychological costs; knowledge complexity | p | partly | objection rate | notice/inspection rules | vague |
| M12 | Kaplow break-even | rules vs standards | d | partly | drafting cost, tailoring value | statute vs rule | vague |
| M13 | Monetised burden (SCM) | Standard Cost Model | p to statute | yes | volume, wage | impact assessment | neither |
| M14 | Cyclomatic / CFC | McCabe; Cardoso | p | yes | none | none (screening only) | likely useless |
| M15 | Structuredness / cyclicity | Mendling | p | yes | none | none | useless |
| M16 | Text complexity | Katz–Bommarito; Schuck | d (text) | yes | none | covariate only | useless at toy scale |
| M17 | Zig-zag vulnerability | strategic screening | p | no | manipulation model | screen design | irrelevant here |

## 6. Recommended first additions

The five measures most worth implementing next, because they are cheap on
the existing toy fit and expose burden the current estimands miss:

- **M3 self-assessability**, with safe harbour as its lever.
- **M4 openness versus realised variety**, the cleanest separation of the
  statute from the towns.
- **M9 deadline coverage**, a direct drafting lever on §4.
- **M8 serialisation excess**.
- **M6 guidance deficit**, which reuses the Bayes fit on page-only evidence.

M1 is a close sixth. M5 and M2 need a denial model, which would be a
worthwhile generator variant.
