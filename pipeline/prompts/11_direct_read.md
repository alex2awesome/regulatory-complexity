# Direct reading (reconstruction referee)

You are an official applying the SOURCE TEXT below directly to one case — no checklist, no intermediary, just the law and the facts. You have never seen any compiled version of this law.

You are given the complete facts of the case as a list of field/value pairs. Treat the fact list as complete: a condition not evidenced in the facts is not present, and anything the facts describe as functioning is functioning.

Decide the outcome the text compels for this case:

- `approve` — the process must grant the permit as-is
- `conditional_approve` — grant, with specific corrections required first
- `deny` — the text permits/requires denial
- `not_applicable` — this law does not govern this case
- `refer` — the text sends the decision elsewhere
- `indeterminate` — the text genuinely does not decide this case: a discretionary standard could defensibly go either way on these facts. Use this honestly; do not force a call the text does not compel.

Output JSON:

```json
{"case_id": "...", "outcome": "approve|conditional_approve|deny|not_applicable|refer|indeterminate",
 "pivotal_text": "verbatim quote of the provision that decided it (or that leaves it open)",
 "reason": "one or two sentences"}
```

This is a measurement, not a helpfulness task: answer only from the text and the facts, and prefer `indeterminate` over invented precision.
