# Toy statute outcome layer: results (2026-09-28)

Protocol: `docs/2026-09-28-toy-statute-outcomes-plan.md`, including addendum O-A.

Runs are in `runs/toy_statute_20260926/`:
- **Fits:** `{W0o,W0o_adv}/outfit_{shared,hier}001/`
- **LLM:** `{W0o,W0o_adv}/llm_outcomes001/` (answers_avg3)
- **Scores:** `{W0o,W0o_adv}/scores_outcomes001/`
- **Tradeoffs:** `outcome_tradeoffs001.json`
- **Replication:** `W0o_rep/calibration.json`

There is one world per condition. Results are descriptive.

## Headlines

1. **The tradeoff between designs is recovered even where levels are not.** Moving a town from desk review only (S1) to notice + desk + inspection (S5), M_hier (per-town nuisance share, with partial pooling) gives:

   | World and town | Burden index change (day-equivalents per applicant) | Change in operating nuisances per 100 would-be keepers |
   |---|---|---|
   | W0o, Alder | +44 [28, 68] (truth +43) | −4.1 [−7.4, −1.5] (truth −4.5) |
   | W0o, Birch | +57 (truth +57) | −3.9 (truth −4.1) |
   | W0o, Cedar | +49 (truth +46) | −3.9 (truth −4.2) |
   | W0o_adv (all towns) | +44 to +57 | −0.4 to −1.3 (truth −0.5 to −2.3) |

   Every burden interval covered the truth. For the drafting question ("what does an extra safeguard buy, at what burden?") this difference estimand is the one that matters.

2. **Deterrence nearly cancels screening in the adversarial world.**
   - In the adversarial world, 70% of deterred or denied people keep hens anyway, and burden deters steeply (β = 0.08). The heaviest design then prevents at most about 2 operating nuisances per 100, while costing about 50 day-equivalents per applicant.
   - In the common-sense world, the same move prevents about 4 nuisances per 100 and roughly triples wrongful denials (Alder: +2.6 per 100).
   - Every method, and the truth, ranks S5 best on operating nuisances and S1 best on burden. So the two objectives always conflict here, and the choice is a weighting question that data can inform but not settle.

3. **Confounding breaks the shared model. A per-town nuisance share mostly repairs it.**
   - In W0o_adv, the town that inspects (Birch) has twice the nuisance incidence. M_shared then has 90% coverage of 0.65 (mean scaled interval score 3.10):
     - it puts u at 0.27 (truth 0.70);
     - it puts Birch's operating nuisances at 4.0 per 100 (truth 21.5).
   - M_hier: coverage 0.92, score 1.46.
   - Even M_hier and the LLM underestimate Birch's nuisance share (0.19 and 0.17 against 0.30). Partial pooling shrinks an outlying town toward the others.

4. **Deterrence (β) is biased low, and the bias comes from the burden input.**
   - In 10 replicate outcome datasets (addendum O-A), β's 90% interval covered the truth only 4 times out of 10. The median estimate was 0.017 against a truth of 0.04.
   - The process posterior (one fixed process dataset) puts Birch's burden at 93 [76, 122] day-equivalents against a truth of 82. So the gap in application rates is spread over a wider gap in burden, and the slope flattens.
   - The replicates share that process posterior, so the bias does not average out. This is error in a predictor, carried through the cut.
   - **Lesson:** deterrence estimated from three towns' cross-sectional burden is fragile. It needs within-town variation in burden, such as the same town before and after a statute or fee change.

5. **Catch rate and false-flag rate trade off.**
   - Denials identify π·d + (1 − π)·f. In the main W0o dataset all three methods put the desk-review catch rate below its truth of 0.35; M_shared gave 0.145.
   - The replicates show this was mostly one unlucky dataset: covered 10 of 10, median 0.26, so there is still a mild downward pull.
   - **Data-design fix:** record why an application was denied, or follow denied applicants, e.g. complaints at addresses whose application was denied. Either separates a safeguard's catch rate from its false-flag rate.

6. **The LLM again did well.**
   - Mean scaled interval score:
     - W0o: LLM 1.27, M_shared 1.50, M_hier 1.52;
     - W0o_adv: LLM 1.40, M_hier 1.46.
   - Head-to-head, the LLM won most estimands in both worlds, against M_hier 69:38 and 81:26. The Bayesian intervals are wider.
   - The LLM also underestimated Birch's nuisance share in W0o_adv, and it was not worse on the inspection catch rate (predeclared expectation 5 not confirmed).
   - Where the Bayesian model is clearly worth having is structure: it states exactly which parameters the data identify and which the prior fills in, via contraction, replication and the plate diagram. The LLM gives no such account.

## Gates

All four fits passed on a single execution each:

| Fit | Worst parameter SMD | Worst estimand median shift (SD) | Time |
|---|---|---|---|
| W0o shared | 0.045 | 0.068 | 417 s |
| W0o hier | 0.057 | 0.046 | 422 s |
| W0o_adv shared | 0.039 | 0.058 | 458 s |
| W0o_adv hier | 0.070 | 0.075 | 474 s |

## Scores

| World | Method | Mean scaled IS | 90% coverage | Head-to-head vs LLM |
|---|---|---|---|---|
| W0o | M_shared | 1.50 | 0.94 | 45:62 |
| W0o | M_hier | 1.52 | 0.96 | 38:69 |
| W0o | LLM | 1.27 | 0.96 | — |
| W0o_adv | M_shared | 3.10 | 0.65 | 27:80 |
| W0o_adv | M_hier | 1.46 | 0.92 | 26:81 |
| W0o_adv | LLM | 1.40 | 0.91 | — |

## Predeclared expectations, checked

1. **Catch-rate contraction ≥ 50% in W0o (M_shared).** Met, narrowly: desk 0.52, inspection 0.62, comment 0.52.
2. **β contraction < 50%.** Not met: 0.62. β is constrained by the data but biased, via the burden input (headline 4).
3. **W0o_adv.**
   - M_shared's inspection catch rate biased up and missing: not met. It was 0.27 [0.07, 0.57], which covers 0.25. The misspecification surfaced instead in π, u, the desk-review catch rate and operating nuisances.
   - M_hier covering the inspection catch rate: met.
4. **Design ranking.** Nuisance ranking (S5 best) differs from burden ranking (S1 best) in every town and world. Combined with validity at τ = 1, only S4 and its concurrent variant are safe under every reading. S4 prevents about half of S5's nuisances (W0o: −2.1 against −3.9 to −4.1 per 100) at 33–43% of its burden increase.
5. **LLM worse in W0o_adv on the inspection catch rate and π_Birch.** Not confirmed for the inspection catch rate (covered). π_Birch was missed by the LLM and by M_hier alike.

## What this says about the guiding questions

**Guiding point 1: the optimal process.**
- Real outcome data identify what a safeguard buys when processes vary across jurisdictions and outcomes are recorded. The data needed are denials, complaints split by permit status and verification, and some count of unpermitted keepers.
- The optimum is still a weighting of burden against externalities. The toy shows that weighting's inputs can be estimated with honest intervals: "+45 burden-days for −4 nuisances per 100".

**Guiding point 2: statute edits.** The validity analysis says a safe harbour makes S1 legally safe. The outcome layer says S1 has the most operating nuisances. The safe harbour's real effect therefore depends on whether "≥ 10 ft from the property line" actually prevents nuisances, which this toy does not model. That is the next outcome question, and it needs data on the harbour's criterion (setback) against complaints.

**Data design for real permitting**, most valuable first:
1. Denial reasons.
2. Complaints and enforcement matched to permit status.
3. Some estimate of unpermitted activity (surveys, aerial imagery, interconnection records for solar).
4. **Before/after changes within a town**, for deterrence.

## Limits

- Everything listed in the protocol.
- One dataset per world, apart from the outcome-only replication.
- The process posterior is fixed across replicates, so the replication shows outcome-sampling calibration, not whole-pipeline calibration.
- In the LLM comparison, the LLM answered from the full evidence dump. Its intervals are narrower, and it wins most head-to-heads while matching the Bayesian models' coverage.

## Per-step ledger: projecting burden and outcomes back onto steps (added after Alex's question)

Alex asked whether this approach can isolate "problem steps", projecting nuisances and time back to single steps or composites. It can. Each p-step's contribution is the change in every estimand when the step is added, holding the rest of the town fixed. The menu offers two contexts for each toggle. The file is `runs/toy_statute_20260926/step_ledger001.json` (M_hier, all towns). Birch, posterior median and truth:

| Step | Context | Burden (day-eq.) | Operating nuisances per 100 | Wrongful denials per 100 |
|---|---|---|---|---|
| Site inspection | desk only → + inspection (S1→S2) | +36.7 (truth +31.7) | −3.4 (truth −3.6) | +0.5 (truth +0.6) |
| Site inspection | after notice (S4→S5) | +36.7 | −1.7 (truth −1.2) | −0.6 (truth −1.4) |
| Notice + comment (+ hearing), composite | S1→S4 | +18.6 (truth +25.2) | −2.1 (truth −3.0) | +1.6 (truth +2.0) |
| Notice + comment (+ hearing), composite | S2→S5 | +18.6 | −0.4 (truth −0.5) | +0.4 (truth +0.1) |
| Issue decision at the inspection | S2→S3 | −6.9 (truth −5.9) | +0.1 (truth +0.1) | +0.3 (truth +0.2) |

W0o_adv (Birch) keeps the same burden columns. In the outcome columns the inspection buys only −1.2 (S1→S2) and −0.3 (S4→S5) nuisances per 100.

What this shows:
- **Attribution works: every step gets a burden and an outcome price, with intervals.** In this table all medians are close to truth and most intervals cover it. Pricing a shared step (issuing at the inspection) makes clear it is a nearly free burden saving.
- **A step's value depends on its context.** Safeguards overlap: a nuisance caught by notice cannot be caught again by an inspection. So "the inspection's contribution" is not one number. Report it per context, or average over orders (a Shapley value) when a single attribution is needed.
- **Composite steps.** Notice, comment period and hearing always occur together in the menu. Only the composite is priced from data; any split is prior-driven, as with burden (round 2).
- **The identification rule carries over from time to outcomes.** A step's burden is identified when its boundary events are observed. Its outcome effect is identified when its presence varies across jurisdictions (or over time), or when outcomes are recorded per step, e.g. denial reasons naming the step that flagged the application.
- **Desk review is in every design, so its marginal effect is not identified by variation.** Its catch rate is learned only because Alder uses desk review alone. Removing it is outside the menu, and outside validity.
