# Case panel generation

Generate a panel of synthetic cases (households/units) as JSON valid against the provided schema, with `facts` fields exactly matching the given input schema.

## Coverage mode (default)

- Realistic, diverse cases spanning the input space: clear approvals, clear denials, and — most importantly — **boundary cases**: units sitting near every threshold in the rule (dates just before/after cutoffs, conditions at the edge of each standard).
- Correlate facts realistically (an older unit is more likely to have older wiring; a garage conversion is more likely to lack a fire-rated separation). Do not generate impossible combinations.
- Give each case a `demographics` block including a one-line `narrative` — divergent cases become witness exhibits and the narrative is what makes a witness legible ("retired couple in East San Jose, garage conversion built by prior owner in 2014, one bedroom window below egress size"). Demographics must never appear in `facts`.

## Adversarial mode (when a second compilation is provided)

You are given two decision trees compiled independently from the same rule. Generate cases you expect to receive **different outcomes** under the two trees. Target their structural differences: predicates present in one but not the other, different thresholds, different orderings of exceptions. State nothing about which tree is "right" — the disagreement itself is the datum.
