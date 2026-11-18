# Complexity metrics (living document)

Consolidates the 17-measure survey (`2026-09-26-complexity-measures-survey.md`, applied in
`2026-09-26-complexity-measures-applied.md`) with what the toy model now represents: the reading layer,
lawful sets, agency choice, and per-step burden. Organized by the chain
text → readings (decision models) → lawful designs → chosen process → burden and outcomes.
Status: **computed** = produced by current code; **defined** = computable from current objects, not yet
reported; **needs data** = needs evidence or modelling we do not yet have.

## 1. Text and readings: how determinate is the law?

| Metric | Definition | Status |
|---|---|---|
| Open questions | Number of interpretive questions the text leaves open (per hypothesis space; varies by reader). | computed (reader outputs) |
| Reading entropy (determinacy) | Entropy of the prior over readings P(r \| text). A question answered with near-certainty adds almost nothing; counts overstate indeterminacy. | defined |
| Reader disagreement | Spread across independent readers' hypothesis spaces (distinct lawful-set classes; P(H_k \| y) concentration). | in progress (hypothesis-space experiment) |
| Statutory openness K(P \| statute) (M4) | Description length of the process given the statute, per D-step. | defined (toy) |
| Text complexity (M16) | Sections, cross-references, undefined terms. Covariate only. | defined |

## 2. Decision model: what must be decided?

| Metric | Definition | Status |
|---|---|---|
| Decision-tree size | Required determinations, exits and loops in the decision model under a reading. | defined |
| Deadline coverage (M9) | Which steps the statutory clock covers, by reading. | computed (validity checks) |
| Self-assessability (M3) | Can an applicant predict the outcome from the rule? | defined |

## 3. Lawful sets: how much room do implementers have?

| Metric | Definition | Status |
|---|---|---|
| Permissiveness | Lawful-set size \|V_r\|: number of designs lawful under reading r. | computed |
| Safe set | Designs lawful under every plausible reading (or with probability ≥ 1−α under the agency's belief over readings). What a hedging agency chooses from. | computed (validity section: only S4/S9 under the vague hen text) |
| Cost of the cheapest safe design | Burden of the cheapest design in the safe set minus the cheapest lawful design under the agency's own reading. The price of indeterminacy for a hedging agency. | defined |
| Phantom requirements | Designs or burdens no reading authorizes, observed in practice. | defined (validity rules) |

## 4. Chosen processes: what do towns actually run?

| Metric | Definition | Status |
|---|---|---|
| Expected steps, applicant interactions | Per town, expected executions of steps and applicant-facing contacts. | computed (estimands) |
| Path entropy | Unpredictability of a case's route (loops, conditional hearing). | computed |
| Implementation variety | Entropy of designs across towns implementing the same D-step; between-town SD of D-step burden. | computed (statute estimands) |
| Error sensitivity (M10), serialisation excess (M8), interaction rounds (M7), exposure (M11) | As in the survey. | defined |
| Cyclomatic (M14), structuredness (M15), zig-zag (M17) | Static shape measures. Kept for screening only; not burden. | defined; low priority |

## 5. Burden and outcomes: what does it cost, and what does it buy?

| Metric | Definition | Status |
|---|---|---|
| Per-step burden | Elapsed days, applicant hours, dollars per p-step, rolled up to D-steps and the statute. Kept distinct. | computed |
| Identification flag | Whether a step's burden is identified on its own (both boundary events observed) or only as part of a sum. | computed (`identify.py`) |
| Monetised burden (M13) | Volume × (hours × wage + fees + delay cost). | needs volume and wage inputs |
| Outcome trade-off | Nuisances caught / harmless coops flagged / applicants deterred per design. | computed (outcome layer; refit pending) |
| Kaplow break-even (M12), ordering regret (M2), extensional disagreement (M5) | As in the survey. | needs data |

## Statute edits as interventions (two axes)

Edits move the text along two independent axes. **Determinacy**: how many readings the text admits and how
spread out they are. **Permissiveness**: how many designs each reading makes lawful.

| Edit type | Example (hens §3) | Determinacy | Permissiveness | Expected effect |
|---|---|---|---|---|
| Concrete, permissive (safe harbour) | "The authority may make this determination from the site plan alone." | up (settles desk-review and notice questions) | up (desk-only becomes lawful under every remaining reading) | safe set grows; cheap design becomes safe |
| Concrete, restrictive (mandate) | "The authority shall mail notice to adjoining owners." | up | down (non-notice designs unlawful) | burden up; variety down |
| Vaguer | Replace a specific requirement with an undefined standard | down (more readings) | varies by reading | safe set shrinks; hedging agencies add procedure |
| Repeal of a requirement | Delete §3 | up (question disappears) | up | burden down; outcome risk up |

Determinacy and permissiveness are independent: settling a question can enlarge or shrink lawful sets,
depending on which answer the edit fixes. Which agencies hedge (choose from the safe set) and which act on
their own reading (choose from V_r) is an empirical question; the model compares the two choice rules.

Deferred extension (Alex, 2026-09-30; revisit after the first successful real-data fit on Solar/ADU): agency values enter only through the choice rule
(values → design given reading). Motivated interpretation (values → reading, e.g. a NIMBY town reading
"nuisance to adjoining properties" as requiring neighbour input) is not modelled. The two channels are nearly
observationally equivalent from process data; separating them needs town covariates or stated readings
(ordinance text, staff reports). The synthetic generator plants readings independently of values.

## Bounding the space (rule-following)

Any rule is consistent with indefinitely many readings and implementations (Wittgenstein; Kripke). The model
bounds both spaces by practice, not by logic: readings are answers to a finite set of questions raised by
readers; designs are compositions of a step catalogue built from observed practice (see
`2026-09-30-toy-statute-blind-process-plan.md`); designs are distinguished only at the granularity of
observable steps; and everything outside is carried as explicit residual mass (residual reading ρ, choice
slack ε). These residuals are where an unanticipated reading or implementation shows up.

## 6. Agent rule-following experiments (added 2026-11-06)

Same objects, read at the agent layer: text c, readings I in Adm_text(c), intended reading I*, behaviour x,
`Legal(x) = I(c)(x)`. The letter-vs-spirit experiments (math / procurement / AI-safety specs) report every
rule variant on all of the following. Names below map onto sections 1–4 where a metric already exists.

| Space | Metric | Computed from | Existing name |
|---|---|---|---|
| Surface | tokens, defined terms, cross-reference hops, restriction words | rendered text | Text complexity (M16) |
| Decision, page | leaves, depth, distinct predicates, expected predicates evaluated per case | skeleton tree read from the text | Decision-tree size |
| Decision, operative | same measures on I*(c); number of distinct trees across readings | each reading's tree | Decision-tree size under a reading; Implementation variety |
| Interpretive | open terms; readings per term; \|Adm\|; entropy of P(I \| c) under the simplicity prior | spec | Open questions; Reading entropy |
| Tacit load | bits to pick I* out of Adm: −log2 P(I* \| c); or count of bridging axioms needed to match human verdicts (real text) | spec / formalizer runs | analogue of K(P \| statute) (M4) at the reading layer |
| Rule-ness | **settled share s(c)** = P_x[ all I in Adm_text(c) agree on x ] over the case distribution | simulation over facts | new; case-space twin of the Safe set (safe set = actions every reading accepts; settled share = cases every reading decides alike) |

`s(c)` is written s, not ρ, because ρ is already the residual-reading mass in "Bounding the space". s(c) is a
property of text **and** case distribution: for "flag if the 90th percentile of latency exceeds 500 ms" under
the nine Hyndman–Fan percentile definitions, s rises from 0.60 at 5 samples to 0.99 at 200 samples
(lognormal latencies, median 300 ms, sigma 0.5). Kaplow's rule/standard axis (content fixed ex ante vs ex
post) is s(c); his complexity axis (number of distinctions) is decision-tree size; they are independent.
Together with Permissiveness (section 3) that gives three axes for any edit: determinacy, distinctions,
permissiveness.

**Lowering complexity** is three different operations, reported separately:
1. Remove dominated complexity: surface and page measures fall, Adm and I* unchanged. Expected: fewer
   mode-1 (overload) failures, nothing lost.
2. Relocate: delete or add a printed definition. Page tree shrinks/grows, Adm grows/shrinks, s(c) moves.
   Not a reduction; a move along the determinacy axis.
3. Change the target function: fewer distinctions, more over/under-inclusion against the purpose function
   P(x). Priced as P-mismatch rate. Example: replace the p90 rule by "flag if any sample exceeds 500 ms":
   one reading, s = 1, but error vs purpose 0.82 for a healthy service at 50 samples (0.006 for the p90 rule)
   and 0.00 for an unhealthy one (0.18 for p90). Needs a declared P(x) in every spec.

Each domain spec carries a **complexity ladder**: variants ordered along one axis with the other two held
fixed (pure standard → open rule → rule with definitions → fully settled rule; and fewer → more
distinctions at fixed s). Outcomes (mode 1, 3a, 3b, conflicts, flag rate) are plotted against the ladder,
by model size. Two thresholds to look for: a page-complexity level above which readers stop applying the
text, and a tacit-load level above which appliers diverge. Motivated interpretation (values → reading,
deferred for towns above) is mode 3b here and is measured directly: conflicting-goal vs no-goal runs.
