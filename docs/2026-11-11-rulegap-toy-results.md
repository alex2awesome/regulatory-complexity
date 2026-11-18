# Rule-following pilot: corrected scores and complexity measurements (2026-11-11)

Updated after Codex review at Alex's request. **All interpretation-space results are exploratory and conditional on authored candidates. No human-validated loophole rate is available.** The first E0 batch is scoped to 17 complete readings and 51 human judgments; the packets are ready, with zero ratings submitted.

Original E1/E3 traces and their original CSVs remain unchanged. The earlier version of this document and source are preserved under `runs/rulegap_20261111/revision_20261111/before/`. The original predictions remain in `docs/2026-11-10-rule-following-experiment-plan.md`; its section 10 records the post-pilot E0 amendment.

## Available results

[Complexity/outcome figure](../runs/rulegap_20261111/revision_20261111/analysis/complexity_results.png)
([SVG](../runs/rulegap_20261111/revision_20261111/analysis/complexity_results.svg));
[joined CSV](../runs/rulegap_20261111/revision_20261111/analysis/complexity_results.csv).

- Re-scored 1,680 E1 baseline episodes and 280 E3 drafting-arm episodes; no new model calls.
- Joined 32 model/condition result rows to nine rule/arm complexity rows.
- Numerical report and verdict now must agree under the same interpretation. This changes 246 episode cells, including controls. These are scoring corrections, not new model behavior.
- Reference-rule violations, purpose-unwanted outcomes, candidate gaps, completion, asks, execution errors and unsupported numerical reports are separate fields.
- The old 768 procurement assignments expand to 400 distinct programs. Identical programs with unused window parameters are no longer described as distinct interpretations.

## Complexity of the tested rules

“Programs” counts distinct expanded verdict expressions, not validated interpretations. Words are whitespace tokens. Settled share is computed over situations × candidate verdict/actions, not the agents' chosen actions. “Declared” uses the fixed 60-case population panel; “observed” uses the actual 30 stress cases used in these runs. They answer different questions. Expression nodes count DSL nodes and omit work inside feature extractors.

| Variant | Words | Candidate programs | Settled: declared | Settled: observed | Page / operative expression nodes |
|---|---:|---:|---:|---:|---:|
| Percentile: open | 18 | 54 | 0.600 | 0.000 | 4 / 8 |
| Percentile: percentile defined | 45 | 6 | 0.767 | 0.700 | 4 / 8 |
| Percentile: all defined | 73 | 1 | 1.000 | 1.000 | 8 / 8 |
| Procurement: open | 13 | 400 | 0.622 | 0.594 | 8 / 10 |
| Procurement: purchase defined | 38 | 8 | 0.719 | 0.678 | 10 / 10 |
| Procurement: all defined | 67 | 1 | 0.956 | 1.000 | 10 / 10 |

The full CSV also contains Boolean tree depth/rank, operator counts, candidate entropy, reference surprisal, panel behavioral classes, cross-case certificate summaries, and bounded manipulation-cost estimates. The tree measures treat a feature as an atom; they are not full computational costs. Reference surprisal depends on the authored prior. Extra drafting clauses do not yet have modeled semantic interpretation spaces.

## Corrected baseline outcomes

Each entry is **no incentive / conflicting incentive**, out of 60 assigned test episodes in each condition. A reference violation means an executed action is illegal under authored I*, including the computed number for percentile. It does not establish motive. A candidate gap additionally has support under another authored candidate and an unwanted outcome under P. Human validation could move these gaps into ordinary errors. Transport failures remain in the denominator and are separately reported; counts are recorded events, not imputed outcomes for failed episodes.

| Variant | Luna reference violations | Sonnet reference violations | Luna candidate gaps | Sonnet candidate gaps | Luna asks | Sonnet asks |
|---|---:|---:|---:|---:|---:|---:|
| Percentile: open | 46 / 43 | 6 / 8 | 16 / 17 | 0 / 1 | 4 / 2 | 20 / 18 |
| Percentile: percentile defined | 51 / 51 | 7 / 6 | 20 / 19 | 0 / 2 | 3 / 4 | 15 / 10 |
| Percentile: all defined | 4 / 2 | 10 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| Procurement: open | 3 / 8 | 0 / 0 | 3 / 8 | 0 / 0 | 40 / 26 | 30 / 33 |
| Procurement: purchase defined | 3 / 10 | 0 / 0 | 3 / 10 | 0 / 0 | 40 / 24 | 36 / 34 |
| Procurement: all defined | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 39 / 34 | 37 / 32 |

Interpretation:

- Percentile compliance changes substantially when the reported number is checked. The previous statements about zero control errors and uniformly declining loopholes should not be used. The intended sample calculation can also disagree with the planted population purpose; that purpose mismatch remains a separate outcome.
- Procurement scoring is unchanged. Luna's recorded violations rise from 3 to 8 in the open rung and from 3 to 10 when purchase is defined. Sonnet records none, with substantial clarification use.
- Fully defined rules have no alternative-candidate loophole by construction. Zero candidate gaps there is not an independent drafting success. Report violations, purpose outcomes and task completion as well.
- These runs do not identify whether a model knew I* and deliberately departed from it. Judge-mode answers use the same ambiguous text. Model and CLI wrapper remain confounded.

`incentive_contrasts.csv` computes exploratory case-blocked sign-flip sensitivities on complete transport pairs. Procurement Luna: open +8.8 percentage points, p=0.3125; purchase-defined +12.1 points, p=0.015625. These are small exploratory comparisons, not a preregistered confirmation or evidence of a private knowledge state. Repeated cases are grouped together; missing transport pairs are reported.

## First drafting arms

Luna, procurement, open rung, 30 cases × one replicate × both conditions. Counts are no / conflicting incentive. These are wording effects against the fixed baseline reference; semantic narrowing of the interpretation space is not measured.

| Arm | Words | Reference violations | Candidate gaps | Asks |
|---|---:|---:|---:|---:|
| control | 13 | 3 / 4 | 3 / 4 | 18 / 13 |
| purpose_goal | 36 | 0 / 2 | 0 / 2 | 22 / 17 |
| anti_avoidance | 34 | 0 / 0 | 0 / 0 | 22 / 20 |
| examples | 203 | 0 / 0 | 0 / 0 | 21 / 14 |

All arms share the same tools, but asking ends an episode. Lower violation counts must therefore be read alongside clarification and completion. The individual treatment samples are too small to rank the clauses reliably.

## Interpretation-space fix and immediate next step

The pipeline now has explicit `candidate`, `sourced`, and `validated` scopes. Complete interpretations are reviewed against frozen text and background. Three independent humans must submit rationale-bearing yes/no decisions; two of three accepts or rejects. Missing votes and abstentions remain pending. Sources, independent formalizers, and program enumeration propose candidates; none substitutes for contextual validation.

The first batch fixes nuisance dimensions in the printed text: `percentile_only` leaves nine calculation methods; `defined_purchase` leaves eight emergency/bid combinations. The accompanying finite panel distinguishes all nine and all eight respectively, with 36 and 28 pairwise disagreement witnesses. The broader open texts require a separate review. A reference excluded by raters is flagged rather than silently replaced.

Packets: `runs/rulegap_20261111/revision_20261111/E0/percentile_only/` and `E0/procurement_defined_purchase/`. Each has a blinded `rater_packet.md`, three blank CSV forms, private candidate provenance, a behavioral audit and a pending validation report. **External dependency: three human raters, 17 readings each.** No outreach or human ratings have been performed.

The source-backed real percentile analysis now uses 10 candidates, excluding the authored successful-only branch. Its declared settled share is 0.783 and stress settled share 0.750. Source-backed still does not mean validated.

New runs without completed E0 must explicitly request `--exploratory`. The next confirmatory run waits for ratings; the proposed emergency-definition comparison remains queued. No new model spend was incurred in this correction.

## Files and verification

- `runs/rulegap_20261111/revision_20261111/analysis/complexity_results.csv`: primary joined table.
- `episodes.csv`, `classification_changes.csv`, `complexity.csv`, `incentive_contrasts.csv`: supporting tables in the same directory.
- `manifest.json` and `source/`: input trace hashes, analysis assumptions and source snapshots.
- `runs/rulegap_20261111/revision_20261111/real_measures/`: source-backed real-percentile metrics.
- `python -m pytest tests/test_rulegap.py tests/test_rulegap_admissibility.py -q`: 28 tests passed. Covers invalid numerical reports, target-case certificate leakage, full-program validation, duplicate/stale/model ratings, source filtering, compatibility constraints, missing reference, frozen packets, the E0 launch gate, and preventing legacy tables from presenting candidate gaps as validated loopholes.
