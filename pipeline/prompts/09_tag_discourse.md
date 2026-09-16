# LegalDiscourse span tagging

Tag the SOURCE TEXT with the LegalDiscourse span schema (Spangher et al., NAACL 2024). Output JSON valid against the provided schema.

Span labels:

- **SUBJECT** — entity that gains powers or restrictions under the law ("a local agency shall not deny…").
- **CONSEQUENCE** — the specific power or restriction conferred ("shall not deny a permit").
- **OBJECT** — entity affected by the subject under the law (the applicant, the unit).
- **TEST** — an explicit condition applied to an entity that determines when a SUBJECT–CONSEQUENCE–OBJECT relation holds ("constructed before January 1, 2020"; "Inadequate sanitation").
- **PROBE** — entity a TEST is applied to that is not a SUBJECT or OBJECT.
- **EXCEPTION** — a corollary to a TEST; when the law does NOT apply ("unless correcting the violation is necessary to comply with…").
- **DEFINITION** — text fixing the meaning of a term.
- **CLASS** — a category of entity mentioned in the law.

Rules:

- Span `text` must be verbatim; parse to the lowest sensible level (split conjoined TESTs into separate spans).
- Tag every TEST and EXCEPTION exhaustively — downstream, these spans are routed to a looseness screener, so a missed TEST is a missed measurement site.
- Where a TEST or EXCEPTION delegates by cross-reference ("the standards specified in Section 17920.3"), still tag it as a TEST/EXCEPTION span; record the reference in a relation `{"head": span_id, "tail": "<citation>", "relation": "references"}`.
- Record TEST→PROBE (`entityTested`), EXCEPTION→TEST (`modifies`), and TEST→CLASS (`usesDefinedTerm`) relations where evident — the DEFINITION-multiplier analysis runs on these edges.
