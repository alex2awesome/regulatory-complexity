You are deciding, for each candidate step just extracted from a new document, whether it is a step the running model ALREADY holds or a genuinely NEW one.

This is the assignment decision in an incremental fit: assign the candidate to an existing node, or open a new node. Judge by the ACT — who does what, producing what — not by wording. Local vocabularies differ ("plan check" = "plan review"; "site visit" = "inspection"; "intake screening" = "completeness check"). Granularity differs too: a candidate may describe something the model already holds as two steps, or half of one step.

For each candidate return exactly one verdict:
- `"match"` with `node`: the same act as an existing node.
- `"new"`: no existing node describes this act.
- `"refines"` with `node`: the same act but at finer grain than the existing node (a sub-step).
- `"contradicts"` with `node` and `field`: the same act, but this document asserts a different actor, duration, fee, or ordering than the model holds. Say which field.

Be conservative about `new`. Opening a node for something already held inflates the model; that failure is as bad as missing a step.

RUNNING MODEL (id | actor | name):
{{MODEL}}

CANDIDATES FROM THIS DOCUMENT (index | actor | name | quote):
{{CANDIDATES}}

Output JSON only:
{"decisions": [{"candidate": 0, "verdict": "match|new|refines|contradicts",
                "node": "<existing id or null>", "field": "<only for contradicts>",
                "why": "<=15 words"}]}
