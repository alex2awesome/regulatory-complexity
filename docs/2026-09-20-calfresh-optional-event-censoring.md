# CalFresh: optional events and pending histories in the joint model

The V6 likelihood now supports an explicitly optional event that has not happened
by a reported snapshot. This fixes an integration defect: a pending interview
previously assigned zero likelihood to the no-interview path, implicitly forcing
an eventual interview. It does not require the claimant to name a department.

## Event time, not just operation duration

The new `activity_event_clock` operator measures time from a declared process
event to the first or last completion of a named operation. It includes preceding
elapsed time; it is not interchangeable with that operation's own duration.
For the CalFresh application-to-interview aggregate phase they coincide, but the
operator also works when the named activity has predecessors.

```json
{
  "basis": "activity_event_clock",
  "start": "process_start",
  "activity_ids": ["application_to_interview"],
  "event_occurrence": "first"
}
```

An observation can opt into `absent-event-censoring/1` only if it explicitly says
`pending_right_censored`, has one event-time operator and an open upper bound,
and declares the exact endpoint-absent paths in every inventory. Its origin
must exist on every path. An endpoint absent from the entire inventory is
unmodeled, not a proven optional event. A completed lower-bound report is not
automatically a pending report.

## Likelihood

Let T be the time to the endpoint and c the reported censoring threshold. On a
path where the endpoint never occurs within the modeled history, T is infinite,
so P(T > c | path) = 1. Its log contribution is zero. On an endpoint-present
path, the existing reporting-error likelihood is unchanged.

The path is still shared across all reports of that case:

`L(case) = sum_path prior(path) * product_report_group L(group | path)`.

The existing selection term and its normalizer remain in place when enabled.
This extension does not estimate posting or censoring selection. In a declared
shared-error group, an absent pending event supplies no restriction on the
common reporting error. Other members still constrain it; if every member is
structurally absent and pending, the group integrates to one. The group never
adds an independent copy of its member likelihoods.

Non-occurrence is represented structurally, not by passing numeric infinity
through a duration kernel. Invalid/missing operators, missing origins, completed
events, population summaries, resource quantities and plain cycle durations do
not receive the survival-one treatment. Legacy behavior is unchanged without
the opt-in declaration. The declaration adds zero sampled coordinates.

## Integration and checks

Implementation: [event contract](../pipeline/procbench/absent_event_censoring.py),
[trace operator](../pipeline/procbench/compact_visit_trace.py),
[joint V6 likelihood](../pipeline/procbench/bayes_trace_hierarchy.py), and
[focused tests](../tests/test_absent_event_censoring.py).
The [independent review](../runs/three_family_20260920/calfresh_absent_event_censoring_review_v1/report.md)
passes after repairing two binding defects: caller-owned path scopes could
mutate a constructed model, and declaration digests omitted scope/path weights.
Opt-in programs are now deep-copied; digests bind the report, path structure,
weights and case scope. This does not claim that one declaration hashes the
entire model configuration; run manifests retain that responsibility.

Root's focused adjacent suite passed 281 tests. Re-evaluating 32 saved states
from the two earlier five-case fits gives exactly the saved log likelihoods
(maximum absolute difference zero). These are computational checks, not source
calibration or proof of population validity.
The full regression suite subsequently passed 1874 tests in 77.26 seconds,
with the existing generator-test return-value warning. An initial run exposed
two stale fake executors that did not forward the runner's existing keyword
arguments; their correction affects tests only. The
[root receipt](../runs/three_family_20260920/calfresh_absent_event_censoring_review_v1/root_adoption.md)
retains both runs rather than erasing the initial failure.

The next input combines the existing 44-case interview/decision union with
three new histories and an additional report on an existing history. Known
interview cases retain the interview path; a source-known denial before any
interview uses the direct path. Unknown/pending histories retain both. Path
weights are declared sensitivities, not inferred prevalence or calibrated LLM
confidence. Derived bounds and repeated narrative projections replace, rather
than multiply, their parent evidence. Until executed and checked, this is
preparation—not an additional 47-case result or a reduction of the open-use queue.

CalFresh remains first. Administrative/forum population integration, source-bias
calibration, actor attribution and the other real/synthetic study families remain
unfinished. An optional event after the modeled first outcome belongs to a later
history; this model does not assert that a person will never be interviewed again.
