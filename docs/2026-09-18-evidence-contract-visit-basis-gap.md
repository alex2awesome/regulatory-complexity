# The evidence contract cannot carry the distinction the corpus was built to teach

2026-09-18. Found while freezing the source-only input set for the V6 track, and
confirmed by direct inspection of `pipeline/procbench/evidence_contract.py`. This
is a finding and a proposal, not a change: extending the contract is a version
bump that touches a shared tree and a live session, so it needs Alex's decision.

## The gap

A `measurements[]` entry in `process-evidence/2` — the schema
`reconcile_evidence.interpret()` actually constrains the model to — carries:

```
scope      step | segment | process | standing
start      activity_start | preparation_start | submission | complete_application | unspecified
end        activity_end | decision | closeout | unspecified
metric     elapsed | payer_work | agency_work | fee | staffing_fte | annual_volume
statistic  individual | typical | mean | median | p90 | statutory_cap | target | estimate
```

with `additionalProperties: False`, so the model cannot add a field. Searching
the whole schema for `visit`, `repeat`, `round`, `cycle`, `basis` and `span`
returns nothing, in **either** v2 or `SCHEMA_V3`. v3 adds genuinely useful
things — `observation_contexts` with `required_activity_ids`,
`excluded_activity_ids`, `segment_mode`, `temporal_scope` and
`clock_start_after_activity_ids` — but none of them answers the question here.

So for a step-level duration the contract offers exactly one encoding,
`scope=step, start=activity_start, end=activity_end`, and these three claims
land in the ledger identically:

1. that step took 6 days the one time it happened;
2. that step was open for 6 days in total, added up over three separate rounds;
3. that step ran 6 days from the first contact about it to the last time
   somebody came out.

## Why that is the expensive one to lose

The generator plants these as different quantities and labels them. In the
reddit specs alone `measurement_clock.basis` is `sum_visit_cycles` on 354,394
occurrences against 82,169 `whole_case`, with
`start: each_activity_visit_start`, `end: each_activity_visit_end` — i.e. nearly
every *step-level* figure in the corpus is a sum over repeat visits, and the
contract's only step encoding means a single visit.

It is also the distinction the documents were most expensively taught to state.
The measurement-basis class was the single largest source of verification
failures in the S05 lane: four artifacts in one batch, and the same error had
already failed `C09__S10__reddit_1` and `C55__S12__reddit_101` in earlier lanes,
which is why `style/reddit_style.md` gained §3a and the render brief gained the
step-attribution rule in item 8. The corpus now says "6 days of that step
actually being open if you add up every visit" rather than "6 days from setting
it up to it being done" — and a parser reading that sentence has nowhere to put
the difference except the free-text `interpretation` field, which no validator
checks and no downstream consumer reads.

The loss is precisely at the seam. It is not that the model has nowhere to use
the information: `VisitHierarchy` has repeat blocks and `rework` relations, and
the project's own conventions insist that elapsed waiting, elapsed service,
payer hours and agency hours stay distinct. The corpus encodes the basis and the
fitter can consume a repeat structure; the ledger between them drops it.

## Proposed minimal extension

Add to `measurements[]`, as a required field on a new schema version:

```
basis    single_visit | sum_visit_cycles | first_to_last_span | unspecified
```

and extend the marker enums with `each_activity_visit_start` /
`each_activity_visit_end`, so a summed claim is self-describing rather than
inferred from `basis` alone. `unspecified` matters as much as the other three:
a document that genuinely does not say which basis it means must be recordable
as ambiguous, not silently coerced — that ambiguity is a real property of the
real corpus and the benchmark should measure how often it occurs.

Three consequences to accept deliberately:

- It is a version bump, not an added optional key: `additionalProperties: False`
  plus a `required` list means every existing consumer and fixture moves with it.
- `compile_visit_durations` would need to route a `sum_visit_cycles` claim to a
  repeat block rather than a single interval. That is the same boundary the V6
  handoff already flags as an incomplete bridge, so the work lands in a place
  that is being rebuilt anyway rather than adding a new seam.
- Until it exists, any source-only run should report basis recovery as
  **structurally zero** rather than as a model failure. Reporting it as a model
  score would blame the extractor for a field the contract never offered.

## Three further collapses in the same contract

Recorded from the same inspection; smaller, but they bear on the same "keep the
quantities distinct" convention.

1. **`observation_contexts` is unreachable as wired.** `interpret()` passes
   `SCHEMA`, and `validate()` only selects `SCHEMA_V3` when the object declares
   `process-evidence/3`, which the constrained output forbids. So route
   membership and `temporal_scope` cannot be emitted at all, and a historical
   claim and a current one are indistinguishable in the ledger. The v2 prompt
   never mentions those fields either, so the wiring is at least coherent — but
   if V6 expects v3 contexts, this step cannot supply them.
2. **One money metric, no payee.** An application fee, a private consultant
   charge, a refundable deposit and a penalty are all `metric=fee, unit=USD`.
   The project keeps payer cost as a scored channel, and these are four
   different burdens on two different parties.
3. **No jurisdiction on an actor.** `actors[]` carries `id`, `name`, `role`
   (`payer|agency|third_party|unknown`), `aliases`, `evidence` and nothing
   geographic, while V6 pools actor ids literally. Two counties' "Planning
   Division" merge unless the model happens to choose distinct free-text ids.
   That is the first distinction the parsing brief asks to preserve, and the
   contract leaves it to chance.

Also worth noting for its own sake: a measurement carries one `doc_id` and one
verbatim `quote`, while the prompt requires a quote to contain both the quantity
and its meaning with no ellipsis. Where a document puts the number in a table
and its basis in a footnote — which fee schedules and dashboards routinely do —
the model must drop the basis or fail the verbatim check.
