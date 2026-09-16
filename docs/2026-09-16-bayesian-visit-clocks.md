# Visit-clock contract for the fuller Bayesian hierarchy

Status: tested deterministic trace/observation operators and source-audit schemas.
A new [joint visit hierarchy](2026-09-16-bayesian-process-v6-results.md) is implemented and in
controlled development fitting, **not yet a validated end-to-end model**. V4's
hierarchy and v5's fitted measurement models remain preserved separate experiments.
This contract prevents reintroducing clock/visit mistakes when joining their strengths.

## What is actually measured

Let a realized visit have activity identity, actor identity/role, start `s`, end
`e`, and optional service-start `b`. Times use one calendar-day axis for a case.
Person-hours and dollar charges are separate quantities, not conversions of days.
Repeated visits to one activity have distinct visit IDs; repeated document mentions
of the **same** visit must share an ID after reconciliation, not become new visits.

| Observation | Operator on a latent trace |
|---|---|
| First visit's cycle | `e_first - s_first` |
| All reported visit cycles | `sum(e_visit - s_visit)` over the specified visits |
| First-to-last activity span | `max(e_visit) - min(s_visit)`; can contain other work |
| Waiting / service elapsed | `sum(b-s)` / `sum(e-b)`, only when those boundaries are supplied |
| First / last decision clock | Earliest / latest marked decision end minus the stated starting event |
| First-filing clock | Subtract the **first** submission event, not all later correction durations |
| Complete-submission clock | Requires an explicit completeness marker; cannot be guessed from last filing |
| Payer / agency labor | Sum separately supplied person-hours for the relevant visits |
| Distinct operations / visits | Unique operation identities / number of executed visit instances |

End of modeled work is not automatically legal closeout. A missing event is `None`,
not a zero-day completion. Missing labor stays missing, with the sum of known amounts
reported only as a lower bound for the represented visits. Unknown actor roles or
agency identities do not produce a tight agency-count posterior by exclusion.

Counting backend work at an initial decision requires an explicit policy: work
already started versus work already completed. Nonblocking record work may straddle
that boundary. The current operators use closed timestamp boundaries; ties in
coarsely recorded dates do not identify a causal ordering. A future event model
must retain finer order where that distinction matters.

## Source contract and executable observation operators

[`audit_visit_observations.py`](../pipeline/procbench/audit_visit_observations.py)
preserves first, final and latest-recorded decision endpoints separately. Its
typed operators include single-visit cycles, sums of visit cycles and first-to-last
activity spans. Unresolved interpretations remain alternatives **without invented
LLM probability weights**. It also flags unsupported activity linkage rather than
silently attributing applicant preparation to an agency. This sidecar is separate
from the old v5 schema, so unsupported new endpoints cannot silently enter an
initial-decision likelihood.

[`visit_observation_operators.py`](../pipeline/procbench/visit_observation_operators.py)
evaluates each supported operator on a candidate latent trace. A cumulative cycle
claim of visits lasting two and three days yields five days even when the visits'
first-to-last span is eight days. An unspecified visit is not silently the first;
reported subsets require visit linkage. Latest-recorded decision requires an
explicit recording realization and can differ from a completed trace's final
decision. Unsupported activity identities, missing events and unknown coverage
return an unresolved reason, not zero. Alternative results stay separate for a
future likelihood to marginalize using a declared model.

[`audit_burden_counts.py`](../pipeline/procbench/audit_burden_counts.py) separately
types numerical counts and rework rates. Extra correction rounds are not total
attempts, a statutory single inspection is not an observed one-visit case, and
"four in ten" is not automatically a counted sample of ten. Counts of public
organizations retain the source's office/department/agency granularity. Listing
activities or actors does not by itself provide a completed-case inventory.

## How Bayesian information should propagate

The elapsed-claim boundary is now implemented in
[`compile_visit_durations.py`](../pipeline/procbench/compile_visit_durations.py).
It revalidates source quotations, preserves numerical precision and every clock
alternative, and emits either an actual joint-model observation or an explicit
reason further modeling is required. It cannot yet compile routes, agency identity,
case-specific branches, counts or work hours. Its strict W1 coverage findings are
in the [v6 results](2026-09-16-bayesian-process-v6-results.md); unknown meanings require
probabilistic interpretation models, not silent omission or invented certainty.

Agency/task parameters should generate **visit** timing distributions. A route,
repeat counts and dependency structure generate a trace from those visit draws.
Each textual claim observes a specified function of that same trace, with its own
rounding, source bias, censoring and selection mechanism. A total and breakdown
from one applicant are therefore coupled observations, not independent population
cases. Posterior information can then flow from a total or task report back to
shared agency parameters and onward to another task/program.

Report calendar wait, elapsed service and actual staff effort separately. An
agency's mean task cycle time is neither its mean staff hours nor its mean
cumulative per-case time across repeats. If a correlation among these channels is
learned, it needs paired evidence and explicit uncertainty; days cannot manufacture
hours. Compute program quantiles and critical-path burdens on posterior traces,
not by adding task medians or taking a critical path through mean durations.

### Implemented within-visit phase connection

The joint model now has an explicit `--within-visit-phases` option. It retains the
cycle-time hierarchy and adds a weak logistic-normal hierarchy for the service
fraction, sharing agency/task/operation effects across cases and programs.
One visit's wait and elapsed service sum to its cycle; both observe the same
case as its total and labor reports. Changing a fraction does not change the
cycle clock, visit count or person-hours. Source-family offsets remain shared.
The phase-disabled model preserves the earlier likelihood exactly at 200 checked
saved/prior states against an independently loaded frozen source package.

`CompactTrace` evaluates first/last/single-visit phases and complete-case phase
sums, including repeated blocks, and materializes matching service-start events
for the independent expanded trace. Missing phase support is an error, not a
zero wait or a claim that all elapsed time is service. The compiler accepts
supported phase boundaries and advertises the required phase-model feature.
Unknown booking-versus-attendance endpoints and partial preparation endpoints
remain unresolved; the word "waiting" alone does not fix those clocks.

This split assumes conditional cycle/fraction independence, fixed case-fraction
spread and the existing perfect within-case repeat correlation. Phase elapsed
time is not staff effort or an identified causal queue delay. Prior sensitivity
and broader source integration remain required. The frozen development test and
its numerical status are recorded in [v6 results](2026-09-16-bayesian-process-v6-results.md).

## Still required before an end-to-end source comparison

- Complete source validation and inference integration of the new observation
  operators. Their schema/trace evaluator alone does not define a probability
  model over unresolved alternatives or repair old ambiguous source wording.
- Alternative operation/actor identity hypotheses and a mapping from mentions to
  physical visits. The deterministic `operation_identity` argument supports one
  count hypothesis; it is not an inference algorithm or a de-duplication solution.
- Extend the normalized repeat model to case-specific branches and clock-specific
  censoring. The final decision
  in a latent completed trace differs from the latest recorded decision in an
  incomplete extract. Abandonment can compete with decision rather than complete it.
- Complete source integration into the existing joint observation/agency/task fit. Reusing a
  v5 posterior as independent evidence without removing its prior and overlapping
  observations would double-count information.
- Fresh, faithful synthetic documents with a frozen clock/cohort/count definition,
  matched LLM controls and separate timing/count/labor scores. The corrected
  generator alone does not make legacy W1 a valid new holdout.

These are continuing Bayesian implementation requirements, not a rationale for
switching to a different primary estimator.
