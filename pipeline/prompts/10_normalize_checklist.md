# Normalize a city checklist

You are given one city/county AB 2533 (§ 17920.3) checklist — the raw text of a real jurisdiction's operationalization of the statute. Normalize it for cross-city divergence analysis.

For every checklist item, output:

```json
{"jurisdiction": "...", "items": [
  {"item_id": "...", "item_text": "verbatim item text",
   "hsc_17920_3_subdivision": "a|b|c|...|o|none",
   "as_written": "objective|judgment",
   "operationalization": "if the item resolves a statutory judgment predicate into a concrete standard (e.g. 'hot water at every fixture' for 'inadequate sanitation'), state the concrete standard; else null"}
]}
```

Rules:

- `hsc_17920_3_subdivision`: map each item to the § 17920.3 subdivision it implements; `none` if the city added an item with no statutory basis (these are findings — cities importing their standard building code through the amnesty door).
- `as_written` judges the ITEM text, not the statute: "smoke alarm present in each sleeping room" is objective; "sanitation adequate" is judgment (the city passed the discretion through).
- `operationalization` is the payload: where a city turned a loose statutory predicate into a concrete bar, that bar is one real human reading — a cutoff sample for the reading ensemble.
- Preserve item order; do not merge items.

These normalized items feed two analyses: (1) cross-city divergence per statutory subdivision (the external validation of the looseness measure), and (2) checklist-sourced readers in the reading ensemble (`source: "checklist"` in readings JSON).
