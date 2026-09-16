# Rule intake

You are performing a structured intake of a legal rule. Answer six questions about the SOURCE TEXT below, producing JSON valid against the provided schema.

1. **Who does the rule affect?** Every population with a stake: regulated parties, beneficiaries, implementing agencies, third parties.
2. **What inputs does the rule's process require?** Every piece of information someone must supply for the process to run.
3. **Who collects or produces each input?**
4. **What is the decision-making process?** Steps, actors, handoffs between actors.
5. **What conditions does the process turn on?** List every predicate in the `predicate_inventory`, each with a HYPOTHESIS about its character (objective / judgment / reference).
6. **How are outcomes decided and communicated?** Outcome space, who communicates, what recourse exists.

## Discipline

- **Ground everything.** Every entry must carry a verbatim `span` quoted from the source text. If you cannot quote a span for a claim, do not make the claim.
- **Do not measure vagueness.** Your `hypothesis` labels in the predicate inventory are predictions to be tested by a downstream compilation-divergence experiment, not findings. Never assert that language "is vague" or "is ambiguous" — that is measured behaviorally, not by inspection.
- **Type what the text does not settle.** Anything unanswerable from the text goes in `open_questions` with a flag: REF (delegated to another provision), LOCAL (settled by the implementing jurisdiction), EMPIRICAL (needs real-world data), TACIT (needs practitioner expertise).
- If the source contains multiple provisions (e.g. a statute plus a provision it delegates to), treat them as one composite rule and cite spans precisely.
