# Solar bulk reading: bounded adoption and Bayesian fit

September 23, 2026. Requested by Alex: quickly check what Claude has already
downloaded and read, then apply the Bayesian model. Leave ongoing collection
alone; do not launch another exhaustive verification campaign.

## Frozen evidence

The snapshot contains 228 completed reading packets: 226 Reddit packets covering
3,818 distinct threads and 76,674 held comments, plus two external-forum page
packets containing 16 posts. External pages are not asserted to be complete
threads. This is Claude's completed reading snapshot, not all downloaded trees,
all older Codex reads, or every packet Claude will finish subsequently.

There are 6,463 contributor episodes, 5,033 timing entries, 2,284 monetary entries,
347 effort entries and 7,671 process-action records. These are not independent
applicants. Every episode and extracted entry is preserved in adoption outputs.

Snapshot and source hashes:
`runs/solar_bulk_adoption_20260923/frozen_inputs001.json`.

## One quick check, now finished

Luna ran the existing mechanical packet checker once against the frozen list:
202 packets passed, 26 had errors. These were geographic probability-field
formatting or an external text-locator adapter issue. There were no missing
sources, source SHA mismatches, duplicate within-packet case IDs or invalid
numeric timing/date fields reported by that check. Twelve timing claims across
six packets received a source-level semantic spot-check. This is a small check,
not an estimated corpus-wide semantic error rate or a semantic gold standard.

Receipts: `runs/solar_bulk_adoption_20260923/quick_check_luna/quick_check.{json,md}`
and `check_packet_once.txt`. Geographic errors do not discard otherwise supported
timing: county probabilities are not used in this first pooled timing fit.
Original Claude packets are not rewritten.

## Adapter and fit scope

`pipeline/procbench/solar_panel/adopt_bulk_forum.py` freezes completed packets,
translates the explicit censoring vocabulary, preserves original values and
quotes, and records one route for every extracted entry. Policy deadlines,
future appointments, isolated dates, active effort and money are not completed
elapsed durations. A missing county is not an exclusion rule. Business days
remain distinct from calendar days. Verbal month/year conversion and rounding
widths are recorded assumptions, not newly observed precision.

The principal integration problem is clock-label fragmentation: the raw adapter
found 2,370 distinct clock/unit groups among 2,667 adopted elapsed reports.
Clear endpoint synonyms receive an explicit, source-reviewed clock crosswalk;
ambiguous starts stay ambiguous and do not become a different measured phase.
No broad rereading queue is started to accomplish that normalization.

`pipeline/procbench/solar_panel/fit_bulk_forum.py` uses the existing V6 duration
likelihood and priors, with independent case effects integrated out by the
existing exact-marginal implementation. Each supported clock has two sampled
parameters: log location and log spread. There is at most one outcome-blind
hash-selected report per exact contributor/clock/unit. Other reports remain
in the ledger rather than being counted as independent people. A contributor
can have distinct installations; this thinning is a conservative dependence
convention, not a claim that all their installations are identical.

Only groups with at least 15 contributors and five finite completed intervals
are queued. Frames are fitted separately; overlapping clocks are not multiplied
together or summed to manufacture whole-process totals. Each numerical result
must pass the unchanged sampler and quadrature checks.

These are selected-forum duration distributions across the stated evidence
frame, **not** representative California population estimates, intrinsic agency
capability, a learned source-selection correction, or a fitted process graph.
Structure, money, effort, sparse clocks and unresolved interpretations remain
explicitly routed for the appropriate components. The earlier failed full
50-action occupancy fit is neither rerun unchanged nor relabeled successful.

## Execution status

Completed. The bounded crosswalk reviewed the 100 most frequent numeric-bearing
clock labels (410 entries); 37 labels received aliases, covering 219 entries.
Sixteen labels were explicitly heterogeneous; others described different or
non-target quantities. Singleton expansion was not pursued in this pass.
This is an important remaining compiler limitation, not proof that the corpus
contains only the two estimable clocks below.

The final adapter adopted 2,713 elapsed reports from 1,562 contributor groups.
All 15,335 extracted timing/cost/effort/action entries have a final route.
Of the elapsed reports, 115 entered the two pooled fits, 161 had explicitly
heterogeneous/non-target clock labels, and 2,437 remained below the 15-contributor
threshold for their current clock labels. Many need endpoint reconciliation,
not additional retrieval or a new verification pass. Thirty-one additional
same-contributor/clock reports were retained without an independent likelihood.

### Actual results

All three runs used four chains, 1,000 warmup and 2,000 retained draws per chain,
with two sampled coordinates per fit. All passed the unchanged diagnostics
and 128-to-256-node plus independent adaptive-integral checks. Worst R-hat was
1.00075 (rounded up); minimum bulk ESS was 4,009. The largest checked likelihood
difference was 5.72e-8. These are numerical checks, not semantic or population
validation.

| Clock and report frame | Contributors | Posterior median duration, calendar days | 90% credible interval for that median |
|---|---:|---:|---:|
| Contract signing to installation; pooled forum | 21 | 106 | 74–156 |
| Installation to permission to operate; pooled forum | 94 | 86 | 67–113 |
| Installation to permission to operate; California-supported subset | 22 | 100 | 58–193 |

The California subset is included in the pooled sample; it is not an independent
replication. California support comes from the parser's location/context labels,
not a new requirement to name a county or department. The subset contains ten
finite completed intervals, one completed lower bound and eleven pending waits.
Pooled installation-to-PTO contains 58 finite completions, one completed lower
bound and 35 pending waits. Results assume ignorable report coarsening within
this selected forum sample; selective posting and unknown case mix remain
unmodeled. They must not be presented as statewide typical waits or agency-only
processing time. Credible intervals above concern the inferred median, **not**
an individual applicant's predictive interval.

These fits use Claude's newly adopted snapshot only, not a silently merged
successor of all older Codex packets. They therefore do not constitute a
same-evidence comparison against the older fits or the LLM baseline.

### Exact artifacts and reproduction

- Frozen source decisions: `runs/solar_bulk_adoption_20260923/frozen_inputs001.json`.
- Adopted observations, original episodes and every claim's initial route:
  `runs/solar_bulk_adoption_20260923/adopted001/`.
- Frozen alias copy: `adopted001/clock_aliases_snapshot.json` under that run root.
- Pooled fit inputs, draws and posteriors: `runs/solar_bulk_adoption_20260923/model/fit001/`.
- California-supported sensitivity: `runs/solar_bulk_adoption_20260923/model/california001/`.
- Final numbers and per-claim **actual fitted consumption**, including unmodeled
  routes: `runs/solar_bulk_adoption_20260923/result001/results.json` and
  `claim_consumption.json`. Exactly 115 distinct observations, from 111 contributor
  groups and 91 threads, entered at least one usable fit. The 22 sensitivity
  observations are not added again to that total.

The repeatable commands are the `freeze`, `compile` and `report` subcommands of
`pipeline.procbench.solar_panel.adopt_bulk_forum`, followed by preparation and
`--fit` in `pipeline.procbench.solar_panel.fit_bulk_forum`. The latter accepts
`--scope california_supported` for the declared sensitivity. Existing output
directories are write-once. Six narrow adapter examples checked future/deadline
separation, pending intervals, business-day preservation, completed upper bounds
and hours/effort ambiguity; no broad test or verification campaign was run.

### What remains

The next integration work is semantic normalization of the remaining relevant
clock labels, preserving genuinely different starts, repairs, equipment ages,
installer work and utility phases. The evidence is already read. Separately,
the 7,671 action records still need an actor/action adapter for process-structure
inference. This run does not advance the failed occupancy fit, estimate step
counts, or establish intrinsic agency capability. No such result is claimed.
Claude's download/reading queue was not modified or interrupted.
