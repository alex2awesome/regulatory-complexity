You are reading ONE document about a government process and reporting only what THIS document says.

Do not reconstruct the whole process. Do not carry over knowledge of how such processes usually work. Report only steps this document actually evidences, each with the verbatim sentence that evidences it.

For each step the document evidences, give:
- `name`: an action phrase, verb first ("Submit the application", "Route the case to plan review", "Pay the fee").
- `actor`: who performs it, in the document's own words (a department, a role, the applicant, a contractor, a utility). Use null if the document does not say. **Do not guess a department.** A missing actor is a finding, not a gap to fill.
- `occasion`: counter | online | mail | site_visit | phone | hearing | internal | automated, or null.
- `timing`: `{value_days: <number>, kind: "statutory_cap"|"target"|"observed"|"reported", quote: "<verbatim>"}` or null. Keep a legal ceiling separate from a measured duration.
- `fee`: `{amount: <number>, when: "<when charged>"}` or null.
- `precedes` / `follows`: ids or names of other steps IN THIS SAME LIST that this one comes before or after, only where the document states the order.
- `rework`: `{back_to: "<step in this list>", reason: "<why>"}` when the document describes going back a stage.
- `quote`: the verbatim sentence evidencing the step, 40 words or fewer.
- `confidence`: 0-1, how clearly the document states this step exists.

Also report:
- `order_statements`: verbatim sentences that establish sequence ("after the inspection is signed off, …").
- `contradicts_nothing_note`: leave empty; a later stage handles contradictions.

Output JSON only:
{"steps": [{"name": "...", "actor": null, "occasion": "...", "timing": null, "fee": null,
            "precedes": [], "follows": [], "rework": null, "quote": "...", "confidence": 0.9}],
 "order_statements": ["..."]}
