# Toy statute: blind process-model construction (predeclared, 2026-09-30)

Alex's request: the way inference builds process models must be the way we would build them on real data.
Until now the fitter used the generator's own step catalogue and design menu, and its evidence arrived
pre-coded in the generator's vocabulary. That is an oracle advantage. This round removes it for the process
layer (the multiple-readers experiment does the same for the decision-model layer).

## World HEN3 (generator side, hidden)

Hen statute v2 (`hen_package.json`), 14 towns, new seed 20261030, plus, in a generator-only package
`runs/toy_statute3_20260930/hen3_package.json`:
- an extra process step outside the standard catalogue: **neighbour signature collection** (applicant
  collects signed consent from adjoining owners before review; days and applicant hours; event
  `signatures_filed`);
- two designs outside the standard menu: **S12** = signatures + desk review; **S13** = neighbour notice +
  comment period + desk review with no hearing.
Two towns are forced onto them (Halite → S12, Mica → S13); the other towns choose as usual (they may also
pick S12/S13 by the generator's choice rule; recorded). Admin records include milestone dates.

## Free-text rendering

Deterministic templated rendering (`toy_statute/render_text.py`), no LLM: web pages as prose with
town-specific synonyms for each step; applicant reports as short narratives (gaps written as "about 3 weeks
later the inspector came out"); admin records as one CSV per town with town-specific column labels.
The synonym key is truth (evaluator only).

## Blind pipeline (inference side) — sees only the statute text, D-steps and rendered documents

1. **Catalogue + design builder** (one Opus subagent, primary; one Sonnet subagent, catalogue scored only):
   step list with synonyms, owner, D-step served, days/hours/fee flags, boundary events, which steps
   applicants mention and web pages list; event order; admin column → event map; a candidate design set
   (inclusive: combinations of observed middle steps in observed orders, plus issue-at-inspection variants).
2. **Compiler** (code): builder output → statute package. Fixed model conventions applied identically to the
   oracle: completeness-check/correction loop, a single objection-conditional step type, agency-owned steps
   scaled by town speed.
3. **Extraction** (Sonnet subagents, given only the catalogue and the documents): reports and web pages →
   the structured evidence schema in the builder's vocabulary. Admin CSVs are mapped by script.
   One scripted schema/vocabulary check per file; failures recorded, not hand-repaired.

## Fits (sk3, v2 target, identical settings)

- **Oracle**: true HEN3 package on the generator's structured evidence.
- **Blind**: compiled package on the extracted evidence.
Both: `--center-towns --gate v2`, no step blocks (block names are vocabulary-specific), 2 runs ×
4,000 particles × 20 moves, seed 20261030, uniform prior over each package's designs. One execution each.
Stage C (readings) is out of scope: readers' validity rules refer to the oracle menu.

## Scoring (evaluator only; may read truth)

1. Catalogue recovery: blind steps mapped to true steps through the synonym key; precision, recall,
   and whether the out-of-catalogue step was found.
2. Extraction accuracy: extracted vs true structured evidence (mentions, gap endpoints and values, listings,
   fees), field by field after mapping.
3. Design recovery per town: posterior probability of the true design (mapped by step set and decision
   placement), MAP accuracy; separately for the two out-of-menu towns.
4. Burden: per-town mean total days and per-step days (mapped steps), absolute error and 90% interval
   coverage, blind vs oracle.

Predeclared expectations (directions only): the builder finds every step that appears in the rendered text,
including signature collection; blind design MAP accuracy is lower than oracle; blind burden errors are
larger than oracle but intervals still cover. Reported as holds / fails.

## Limits

Templated rendering is cleaner than real text (one synonym per mention, no contradictions); it tests
vocabulary discovery and design-space construction, not messy-language extraction. One builder is fitted.
Blindness of LLM agents rests on instruction, not a sandbox.
