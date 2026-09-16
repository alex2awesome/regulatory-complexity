# Render a vignette

You are generating one realistic inspection vignette for a measurement instrument. You are given a latent position between two anchored condition descriptions, plus context fields.

Write 4–8 sentences in the style of a building inspector's field notes describing ONE dwelling unit whose condition sits at the stated position between the two anchors: interpolate the *severity* faithfully — if the position is 30% of the way from the lower to the upper anchor, the described conditions should be clearly worse than the lower anchor and clearly better than the upper one, in proportion.

Hard rules:

- **Never state or hint at the latent position numerically.** No percentages, no scores, no "moderately substandard" meta-language. Only concrete observable conditions.
- Describe observations, not conclusions: "the trap under the sink drips onto a warped cabinet floor," never "the plumbing is inadequate" — verdict words would contaminate the measurement.
- Weave in the context fields naturally.
- Vary sentence structure and incidental details between vignettes; do not reuse phrasing from the anchors verbatim.
- Include one or two condition details of your own invention *consistent with the interpolated severity* — but never introduce hazards from other domains (no electrical, structural, or fire conditions if the axis is sanitation): the vignette must vary ONLY along the stated axis plus harmless color.

Output JSON: `{"case_id": "...", "vignette": "..."}`
