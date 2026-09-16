# Compile the mandated process skeleton

From the SOURCE TEXT (a statute), extract the PROCESS the law mandates or presupposes — not the decision logic, but who must do what, in what order, producing which artifacts. Output JSON valid against the provided schema with `source: "statute"`.

Rules:
- One activity per mandated or presupposed act, each with a verbatim `span` quote. Typical elements: publication of a checklist, notice of an option to the public, application submission, inspection (note if the text says "may"), issuance of permits to correct noncompliance (a REWORK loop back to inspection), fee provisions, the final decision and what the applicant ends up holding.
- Tag each activity with `mandated_element` from: checklist_publication, notice, third_party_option, application, inspection, correction_permits, fee_waiver, decision, terminal_issuance. Use `optional: true` where the text says "may" or offers rather than requires.
- Actors as lanes from the canonical list (applicant, third_party, planning, building, inspector, official, local_agency, county, state_agency). Use `local_agency` when the text does not specify a department.
- Edges: `sequence` for ordering the text implies, `rework` for correct-and-reinspect loops, `optional` for offered-not-required branches, `handoff` where an artifact passes between actors.
- Do NOT invent steps the text does not mandate or presuppose; a statute usually underdetermines the process — leave the gaps, and list what it leaves open in `notes`.
