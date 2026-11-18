# Running literature review (living)

Index of the reading we have done and still need to do, by theme. Detailed notes live in the linked documents. Add to this file rather than starting new lists.

- Complexity measures, Blum, process mining, public administration: `docs/2026-09-26-complexity-measures-survey.md` (17 candidate measures M1–M17).
- Causal framing of statute edits: `docs/process-model-causal-frame.md`.
- Reading layer audit and the vagueness literature: `docs/2026-09-29-reading-layer-audit.md`.
- Novelty gates for the three real families: `docs/2026-09-21-*-literature-novelty-gate.md`.

## ★ Alex: return and read (added 2026-09-29)

Found during the reading-layer audit. Each one bears directly on the text → decision → process → outcomes model (`docs/2026-09-29-full-chain-model-proposal.md`). Marked ★ so they are easy to find; remove the star once read.

| ★ | Paper | Why it matters to us |
|---|---|---|
| ★ | Diver, C. (1983). *The Optimal Precision of Administrative Rules*. 93 Yale L.J. 65. [OUP reprint](https://academic.oup.com/book/10561/chapter/158510821) | The closest antecedent to our "cost of vagueness". Separates a rule's transparency, accessibility and congruence and analyses the trade-off; these map onto openness, guidance deficit, and the wrongful-denial / missed-harm rates. Four worked agency cases. |
| ★ | Kaplow, L. (1992). *Rules versus Standards: An Economic Analysis*. 42 Duke L.J. 557. | Standards push the cost of giving the law content to the enforcement stage. Our finding that vagueness moves burden through legal risk ("defensive proceduralism") is this mechanism. |
| ★ | Lassiter, D. & Goodman, N. (2017). *Adjectival vagueness in a Bayesian model of interpretation*. Synthese 194:3801. [Springer](https://link.springer.com/article/10.1007/s11229-015-0786-1) · [PDF](https://cocolab.stanford.edu/papers/LassiterGoodman2015-Synthese.pdf) | A vague predicate has an uncertain threshold, and the listener infers a distribution over it. "Nuisance" is such a predicate; a *reading* is a threshold setting. This is the theoretical model for p(reading \| text) as a distribution rather than a point. |
| ★ | Goodman, N. & Frank, M. (2016). *Pragmatic language interpretation as probabilistic inference*. TiCS 20:818. Practical intro: [Scontras, Tessler & Franke](https://arxiv.org/pdf/2105.09867) | The Rational Speech Acts framework behind Lassiter & Goodman. Read second. |
| ★ | Baker, C., Saxe, R. & Tenenbaum, J. (2009). *Action understanding as inverse planning*. Cognition 113:329. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010027709001607) | Inferring a latent belief (an agency's reading) from an action (its process) requires a model of how the agent acts given beliefs. Makes explicit that our reading posterior is only as good as the assumed choice model. |
| ★ | Tenenbaum, J. & Griffiths, T. (2001). *Generalization, similarity, and Bayesian inference*. BBS 24:629. | The size principle: hypotheses that allow fewer observations get more credit. It appears in our reading posterior under uniform choice, and disappears under other choice models. |
| ★ | Massey, A., Rutledge, R., Antón, A. & Swire, P. (2014). *Identifying and Classifying Ambiguity for Regulatory Requirements*. RE 2014. [PDF](https://www.cc.gatech.edu/~aianton/assets/2014_re14_ambiguity.pdf) | An ambiguity taxonomy for legal text; analysts found ~33 ambiguities per 104 lines. Ready-made procedure for enumerating a statute's interpretive questions (step 1 of the reading layer). |
| ★ | Nou, J. & Nyarko, J. (2022). *Regulatory Diffusion*. 74 Stan. L. Rev. 897. [PDF](https://review.law.stanford.edu/wp-content/uploads/sites/3/2022/05/Nou-Nyarko-74-Stan.-L.-Rev.-897.pdf) | Agencies copy each other's rule text. Imitation is a real candidate choice model for how a jurisdiction picks a process, and a confound for reading inference. |
| ★ | Carvalho, L. & Hartmann, M. (2022+). *Bayesian inference for the weights in logarithmic pooling*. Bayesian Analysis. [Project Euclid](https://projecteuclid.org/journals/bayesian-analysis/advance-publication/Bayesian-Inference-for-the-Weights-in-Logarithmic-Pooling/10.1214/22-BA1311.pdf) | How to treat an elicitor's (the LLM's) probabilities as data with learnable reliability, rather than tempering by hand. The supra-Bayesian route for calibrating LLM readings across statutes. |
| ★ | Holt, S., Ruiz Luyten, M., Berthon, A. & van der Schaar, M. (2025). *G-Sim: Generative Simulations with LLMs and Gradient-Free Calibration*. [arXiv:2506.09272](https://arxiv.org/abs/2506.09272) | Flagged by Alex. The propose → calibrate → refine loop maps onto reading enumeration → practice-based reweighting → residual-driven re-parse. Note its stated limitation: SBI posteriors ignore structural uncertainty. |

Lower priority, seen only as citations: Ehrlich & Posner (1974) *An Economic Analysis of Legal Rulemaking*; Sunstein (1995) *Problems with Rules*; Endicott (2000) *Vagueness in Law*; Kempe et al. (2024) *Modeling, Analyzing and Communicating Regulatory Ambiguity*; Staton & Vanberg, *The Value of Vagueness* (judicial opinions).

## Earlier reading (2026-09-26 survey)

See `docs/2026-09-26-complexity-measures-survey.md` §1–2 for Blum & Vempala (human computation, PREP/PROC), Blum's strategic-classification and screening work with Stangl, process-mining complexity measures, and the public-administration burden literature.
