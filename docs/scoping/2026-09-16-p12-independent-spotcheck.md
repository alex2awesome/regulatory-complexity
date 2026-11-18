# Independent spot-check of P12 and the latest scoping corrections

2026-09-16, Codex, packet Q2-P12-SPOTCHECK. Requested review of the other
agent's completed work, followed by continued material retrieval. This is a
bounded inspection and tiny in-memory diagnostic exercise, **not** a rerun of
the reported 413 tests or validation of all generated worlds. No reserved world
truth was read, no model code was changed, and no new unit tests were written.
Line locations below refer to the working tree inspected around 20:20 PDT.

## What holds up

- The capped kind and bound are carried through the statute and process records,
  included in validation, and disclosed at statute level without claiming to
  disclose the exact local choice. This is useful schema plumbing.
- A gap avoids the division-by-zero problem when capped spread is zero. The
  existing four-jurisdiction example distinguishes its truthful and constant
  predictions. That example does not establish the metric's general adequacy.
- The latest rurality correction is incorporated: all **58** current
  `uic_2024` and `is_noncore` values exactly match the independently saved
  [audit join](../../corpus/counties/county_noncore_audit.csv); **11** counties
  are noncore. The builder reads the cached USDA UIC source rather than RUCC.
- The APR report and shared plan now identify the long timing clock as
  **complete-application to permit**, excluding the earlier incomplete phase.
  This corrects the important endpoint interpretation.

## Findings requiring attention

### 1. High: one synthetic statutory bound is reversed

In [decision.py](../../benchmark/synth/generator/decision.py), the
`rental_inspection` P4 definition (around line 283) says the correction period
must be **not less than 30 days**, but its available local deadlines are
30, 21 and 14 days. The latter two contradict its own statute text. Meanwhile
the validator (around line 169 in
[validate.py](../../benchmark/synth/schemas/validate.py)) rejects values above
30 for either applicant comparison direction. Thus a lawful 45-day deadline
would fail validation while an unlawful 14-day deadline passes that check.

The applicant test (`days_to_correct <= local_deadline`) and the legal bound
on the jurisdiction's policy (`local_deadline >= 30`) are different relations.
Store the latter explicitly, including direction, rather than inferring it
from the former. Also inspect the adjacent P3: it uses the same case attribute
and activity but supplies a second deadline, potentially making one predicate
redundant. I have not run the resulting case simulation to quantify that effect.

### 2. High: missing predictions change the reported planted distribution

In [decision_metrics.py](../../pipeline/procbench/decision_metrics.py), `score()`
adds `gold_value` to a row only when a prediction matches (around lines 144–150).
`cross()` then builds its planted histogram from those rows (around line 232),
not directly from the gold entries. Unmatched truth becomes the string `None`.

Reproduction used eight invented jurisdictions, all with a capped reading 15,
and standard readings `[0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.7]`:

| Prediction | Reported planted standard histogram |
|---|---|
| All readings supplied | `{"0.3": 7, "0.7": 1}` |
| Only final standard reading omitted | `{"0.3": 7, "None": 1}` |
| No criteria supplied | `{"None": 8}` |

With no predictions the contrast is null, not a perfect score; the defect is
that **the target itself changes with the predictions**. Compute truth
histograms independently, retain missingness separately, and keep a fixed
evaluation population. Recovered histograms currently also use a matched-only
denominator, so their distinct-count normalization changes when coverage falls.

### 3. High for scale-up: the new spread statistic does not measure concentration

The family statistic at `decision_metrics.py` around line 260 is
`(number_of_distinct_readings - 1) / (number_of_jurisdictions - 1)`.
It ignores the frequencies of those readings and their numeric separation.
Both planted kinds commonly have three possible readings. Once all three are
observed, both get the same spread, however different their concentration.

A second in-memory diagnostic used 58 jurisdictions and these lawful numeric
reading histograms:

- Capped: `{15: 40, 10: 10, 5: 8}` (69% at the cap).
- Standard: `{0.3: 20, 0.5: 19, 0.7: 19}` (approximately uniform).

Both planted spreads are **0.0351**, so the planted gap is **0**. Predicting
15 and 0.3 everywhere yields recovered spreads **0**, recovered gap **0**,
`gap_error=0`, and `direction_correct=true`. The separate mean-agreement fields
correctly fall to 0.6897 and 0.3448. Thus the headline contrast **can reward the
modal-everywhere strategy at the intended county scale**, contrary to the broad
claim in the plan/log. With a fixed finite reading space this normalized
distinct count also tends toward zero as the jurisdiction count grows.

Keep per-jurisdiction reading accuracy, coverage, and frequency-sensitive
distribution recovery primary. Compare calibrated predictions with the modal
baseline on the same held-out counties. A capped contrast can be secondary;
report its two components, not just a gap that allows their errors to cancel.
Use numeric distances only within commensurable predicates; discrete diversity
and duration/amount variance are not interchangeable units.

### 4. Medium: source and causal claims still need qualification

The official [WIC 17001.5 text](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WIC&sectionNum=17001.5.)
supports the 15-day residency limit. But subsection (a)(2)(C) explicitly retains
certain pre-August-19-1992 shared-housing reductions above the listed limits;
(a)(4)'s three-month provision has an offered-training condition. This is not a
complete legal analysis, but those exceptions already rule out a universal
context-free upper-bound encoding of the real statute. Synthetic simplification
is fine if declared; it is not empirical confirmation that every real dimension
obeys the simplified generator.

The programmed 70% weight at the bound is a **planted assumption**, not evidence
that statutory bounds causally produce concentration. The 400-draw test checks
sampling those weights; it does not test the complete `resolve_readings` path
or infer the mechanism. Within-county comparisons help with county-level
differences but still differ in outcome units, policy objectives, exceptions,
case mix and measurement. Section 12's all-confounders-held-constant claim
remains too strong.

### 5. Low: the recent corrections have not propagated to all prose

- [County README](../../corpus/counties/README.md) still defines `is_noncore`
  using RUCC {6,7,8,9}, despite the corrected UIC-based builder and table.
- The paragraph after the APR timing table (around lines 261–267 of
  [the APR report](2026-09-16-apr-permit-timing.md)) still interprets the
  difference between two differently selected median summaries as the
  applicant's experienced delay, including completeness review. Neither the
  omitted pre-completeness phase nor a paired per-case decomposition is
  established by those summaries. The main clock-definition correction is
  nevertheless valid.
- The shared plan still calls a ratio the headline although P12 now uses a gap.

## Handoff and scope

Findings were posted immediately to the append-only shared log for the owner.
This report does not overwrite the independent Q1 audit or other-owner outputs.
The code problems are review findings, not fixes implemented by this retrieval
pass. Source collection continues in N8-STATE-HEARINGS.
