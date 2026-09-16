# Static looseness screening (typology classification)

You are given one discourse span from a legal text (typically a TEST, EXCEPTION, or DEFINITION). Classify its linguistic looseness typology. This produces a HYPOTHESIS to be calibrated against a behavioral instrument — do not treat your output as a measurement, and do not reason about how a court "would probably" resolve the language.

For the span, report:

1. **gradable_heads**: each gradable adjective/adverb doing predicative work, classified `relative` (context-supplied threshold: "adequate", "reasonable", "substantial") or `absolute` (endpoint-fixed: "closed", "complete") per Kennedy's relative/absolute distinction.
2. **multidimensional**: does the predicate aggregate multiple underlying dimensions with unspecified weights ("adequate sanitation" spans plumbing, waste, ventilation, mold...)? List the implicit dimensions.
3. **delegation**: any explicit assignment of the standard to an official's judgment ("in the opinion of", "to the satisfaction of", "as determined by") — a distinct mechanism from semantic vagueness; name the delegate.
4. **open_enumeration**: non-exhaustive lists ("including, but not limited to", "any other").
5. **thin_anchors**: numbers, dates, dimensions, named external standards that pin part of the predicate down.
6. **looseness_hypothesis**: 0–1, your prior that a reading ensemble would show a wide cutoff band, with one sentence of reasoning grounded ONLY in the typology features above.

Output JSON:
```json
{"span_id": "...", "gradable_heads": [{"word": "...", "class": "relative|absolute"}],
 "multidimensional": {"is": true, "dimensions": ["..."]},
 "delegation": {"present": false, "delegate": null},
 "open_enumeration": ["..."], "thin_anchors": ["..."],
 "looseness_hypothesis": 0.0, "reasoning": "...",
 "status": "HYPOTHESIS"}
```
