# Disagreement adjudication

You are given: a case, two (or more) independent compilations of the same rule, the outcome each compilation reaches for this case, and the span-grounded path each took. Classify the disagreement. Disagreement alone does not establish ambiguity — that is the point of this step.

Sort into exactly one bin:

1. **`compilation_bug`** — at least one compilation misreads the text: it violates a span (the quoted text does not support the predicate as written), violates a declared monotonicity invariant, drops an exception the text states, or invents a threshold the text does not contain. Name the offending compilation, node, and the violated constraint. The fix is mechanical; this is NOT discretion.

2. **`schema_gap`** — the compilations disagree because they demand different inputs and the case lacks a fact both readings would need. The input vocabulary was incomplete. Name the missing field. NOT discretion.

3. **`genuine_underdetermination`** — both readings are defensible applications of the text to this case: the text's language does not determine which branch governs. Quote the span(s) whose application the case falls between, and state each reading in one sentence. This — and only this — counts as discretion, and the case is a certified witness of it.

Output JSON:

```json
{
  "case_id": "...",
  "bin": "compilation_bug | schema_gap | genuine_underdetermination",
  "offending_compilation": "v2 (bugs only)",
  "violated_constraint": "(bugs only)",
  "missing_field": "(gaps only)",
  "contested_span": "(underdetermination only) verbatim quote",
  "reading_a": "one sentence",
  "reading_b": "one sentence",
  "rationale": "2-4 sentences"
}
```

A sample of your classifications will be audited by human experts; calibrate accordingly — when torn between `compilation_bug` and `genuine_underdetermination`, check whether a careful lawyer could defend the disputed reading with a straight face. If yes, it is underdetermination.
