# Duration priors over (agency, task) steps

**Question this answers.** Given a process model for a program nobody has measured, predict its timeline. That requires priors attached to *kinds of step*, not to programs.

**Why the step key is six-dimensional** (`taxonomy.json`): elapsed time is `touch + queue`. Touch time scales with the task type and the artifact; queue time scales with backlog, batching cadence, and which party is holding the ball. Two steps sharing an agency and a task but differing in cadence — a daily cashiering batch vs a monthly council calendar — have incomparable durations. So: `agency_class × task_type × channel × blocking_party × cadence × jurisdiction_class`, with `touch_days`, `queue_days` and `elapsed_days` recorded separately, plus `statutory_cap_days` kept strictly apart from any measurement.

**Evidence tiers**, best to worst: `verifiable_official` (the agency's own statistic or dataset), `inferred` (computed by us from records), `designed_document` (a staff report or SOP's intended duration), `statutory` (a legal ceiling — an intention, never a measurement), `community_reported` (forum accounts; selection-biased toward delay, and the bias is recorded in `notes`).

## Files

| path | what |
|---|---|
| `taxonomy.json` | the step key, duration fields, tiers, observation schema, and the rationale |
| `observations/<slug>.json` | `{slug, observations[], coverage}` — one observation per duration statement, each with a verbatim quote, `source_id`, date and tier; `coverage` lists per-tier counts, distinct step keys, and gold steps with no duration evidence at all |
| `rollup.py` | aggregates all slugs into step-key priors |
| `../../dashboard/data/priors.json` | the rollup: per key n, median, range, touch/queue medians, statutory cap, official-vs-community ratio, best tier, an example quote |

```
python3 pipeline/priors/rollup.py [--min-n 2]
```

## What the rollup reports, and why

- **`official_vs_community`** — the ratio of what applicants report to what officials publish, per step key. This is the selection-bias correction factor, measured rather than assumed.
- **`cap_breaches`** — step keys whose measured median exceeds the statutory cap. The first cut found the ratio tracks codability: a mechanical automated check runs 1.5× its cap, a discretionary search-and-review determination runs 15×. A shot clock binds in proportion to how codable the task is.
- **Gold steps with no duration evidence** (in each file's `coverage`) — the holes. Recordkeeping and internal routing steps almost never carry a public duration, which is what forces the queue term to be modelled.

## Known gaps

`touch_days` is far sparser than `elapsed_days` because sources rarely separate work from waiting. Some observations arrive with partial step keys (they aggregate under `unspecified`). Community medians on thin n should not be quoted as distributions; use `n` and `tiers` before citing a row.
