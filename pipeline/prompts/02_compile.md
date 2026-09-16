# Compile the rule

Compile the SOURCE TEXT into an executable decision tree, as JSON valid against the provided schema. You are one of several independent compilers of this rule; produce YOUR single best faithful reading. Do not enumerate alternatives, do not hedge between readings — commit to one. (Divergence between independent compilations is the experiment's signal; a compiler that hedges destroys the measurement.)

## Node discipline

- **Span-ground every node.** Each node's `span.quote` is a verbatim quote from the source; `span.cite` is the subdivision. A node you cannot anchor to a span does not belong in the tree.
- **Type every predicate honestly:**
  - `objective` — a clerk could decide it from the listed inputs with NO discretion. You MUST supply an executable `expr` (JsonLogic over the input field names). If you cannot write the expr, the predicate is not objective.
  - `judgment` — deciding it requires a discretionary assessment by the `decider` (e.g. "adequate sanitation", "good and safe condition"). No expr. Do not invent thresholds the text does not contain — inventing a threshold is silently resolving the legislature's delegation, which corrupts the measurement.
  - `reference` — the text delegates to another provision whose text you were NOT given. Set `target`. If the delegated text IS in the source, compile it inline instead.
- **Declare monotonicity.** For each predicate, for each numeric/boolean input, declare `+`/`-`/`0`: the direction in which increasing that input can move the predicate. These are testable claims about the statute and will be checked mechanically against your tree.
- **Decisions vs. conditions (schema v3).** A node is a DECISION — a choice point with a decider and outcome effect. A boolean decision is a `predicate` node; when a decision aggregates several distinct testable propositions, list them as `atoms` (each span-pinned) under the predicate. When the source uses a POINT SYSTEM (violations with weights summed against thresholds — score sheets, grade cutoffs), use a `score` node: items with points (objective items carry an expr; judgment items stay judgment) and threshold bands mapping to targets. Never flatten a point system into boolean branches.
- **Input operationalizations.** Where a fact admits more than one defensible definition (an "age", "previously permitted"), list the alternatives in the field's `operationalizations` with who fixes the choice — do not silently pick one.
- **Granularity is fixed by the statute's own structure.** One condition per operative subdivision or clause: each lettered/numbered subdivision stating a distinct condition becomes its own node — never collapse an enumeration like (a)–(o) into a single catch-all node, and split a subdivision into multiple nodes when it states conditions with independent inputs.
- **Coverage contract.** Every subdivision of the source must appear either as node(s) or in the top-level `non_operative` list with a reason (definition, fee provision, notice requirement, severability...). Nothing is silently dropped.
- **Build the full input schema — as raw observable facts.** Every input any predicate consumes gets a field: its `question` as asked of a real applicant, `supplier`, `provenance_class` (a=known offhand, b=existing household document, c=requested from an institution, d=applicant-created artifact, e=professional-created artifact, f=government act), `sensitive` if supplying it exposes the party to legal or financial risk, and `range`/`enum_values` so cases can be generated. Two hard rules:
  - **No conclusion-shaped inputs.** A field must be something a form, document, or inspection could literally record ("has_working_toilet", "wiring_installation_year"), NEVER a restatement of the predicate it feeds ("evidence_inadequate_sanitation" is forbidden — it smuggles the answer into the input). If a judgment predicate has no raw observable inputs, give it the observable facts a decider would consider, and let the predicate stay `judgment`.
  - **Numbers live in exprs, not field semantics.** Thresholds and dates go in the objective predicate's `expr`; fields carry raw quantities. Reuse a field across predicates rather than minting near-duplicates.
- **Bundle inputs by acquisition event.** Set `acquisition` on each field to the real-world act that yields it: "application_form", "site_inspection", "records_request", "professional_report", etc. Fields sharing one act share its cost — one site inspection observes many facts. Do not invent one inspection per fact.
- **Order matters.** Sequence nodes as the process would actually encounter them (threshold/applicability questions first). The tree's shape determines the expected burden a case pays before resolution.
- **Flag, don't guess.** Where the text leaves something you cannot compile, attach a flag: REF, LOCAL, EMPIRICAL, or TACIT, with a note.

## Outcomes

Use `approve` / `deny` / `conditional_approve` (with `conditions`) / `refer` / `not_applicable` (the rule does not govern this case). Every leaf is an outcome node; every path from the root must reach a leaf.
