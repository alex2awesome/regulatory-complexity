# Case fact extraction

You are given the input schema of a compiled statute (field names, types, questions) and the narrative facts of one case. Fill in the schema's fields from the narrative. Output JSON: `{"case_id": "...", "facts": {field_name: value, ...}}`.

Rules:

- **Closed world.** These case narratives are complete: if the narrative does not mention a condition, event, or status, it did not happen / does not hold. Booleans default to `false`, not to unknown, unless the field's question is about something the narrative genuinely cannot settle — then use `null`.
- Fill every field whose value is stated or directly computable from the narrative (dates, amounts, counts — compute them; a person "born March 2, 1955" has a determinable age in any given year).
- Match types exactly: dates as `YYYY-MM-DD` strings, numbers as numbers, enums from the listed values.
- Do not decide the legal question. You are recording facts, not applying the statute — if a field's name smuggles a legal conclusion you cannot derive from raw facts, set it `null`.
- The question being asked about the case (e.g. which year, which person) is given; resolve person- and year-relative fields for that person and year.
