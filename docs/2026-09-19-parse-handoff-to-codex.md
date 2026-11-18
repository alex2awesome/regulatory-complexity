# Real-corpus parse: handoff

**Subsequent audit:** see [Codex continuation](2026-09-19-codex-parse-continuation.md)
and [source inventory](2026-09-19-real-corpus-inventory-audit.md). The original
4,400-measurement total reproduces, but semantic spot checks found duplicate cases,
misclassified applicant deadlines and unsupported timing/route interpretations.
The remaining 3,971 pages form 19 unique threads (20 slice entries). The route
weights below are provisional because the cited fit failed convergence/usability;
the capacity-versus-design conclusion is not established. This handoff is retained
as the historical record, with corrections tracked separately.

Written 2026-09-19 10:50 Pacific, at Alex's request, to hand off to Codex.
Parsing is stopped. Nothing is committed; `runs/` is gitignored.

Companion documents, all current:
`2026-09-19-real-corpus-machinery-gaps.md` (what can and cannot reach the model),
`2026-09-19-real-corpus-first-results.md` (what the documents say, plus the fit),
`2026-09-18-bayesian-machinery-audit.md` (the V6 audit this grew out of).
The running narrative is `docs/scoping/FINDINGS.jsonl`, packet `W2-V6-WATCH`,
now 505 lines.

## Where it landed

**20 of 23 frozen processes parsed, plus 7 of 8 ordinary forum batches.**
4,400 validated measurements across 27 trusted ledgers. Every one passes
`evidence_contract.validate` against its own documents, and every parser
independently re-sliced each quote from the artifact bytes with a
re-implemented normaliser. Total quote checks across the run are in the
thousands with zero mismatches reported.

Corpus shape, counting the forum units separately:

| | forum units (828 pages) | everything else | forum share |
|---|---|---|---|
| measurements | 1,577 | 2,823 | 36% |
| audit-eligible durations | 665 | 801 | 45% |
| distinct cases | 574 | 513 | 53% |
| applicant-effort claims | 150 | 90 | 62% |
| fee measurements | 380 | 760 | 33% |

**The single most useful thing learned:** official corpora are made largely of
deadlines, targets and caps, and a forum is made of things that happened. Two
thirds of the forum's elapsed figures survive the pipeline's eligibility rule
against under half elsewhere. 828 pages of forum, twelve percent of the
document corpus, nearly doubled the fittable duration evidence. The biggest
lever on estimating burden was not a modelling change.

## What is left to do, in priority order

### 1. Redo three megathread units. Do not complete them.

A session limit killed three agents mid-run at 08:46. What is on disk:

| unit | pages | state |
|---|---|---|
| `calguns_a/mega_1302365` | 187 | `evidence.json` + `burden_counts.json`, 230 measurements, contract PASSES |
| `calguns_a/mega_1754542` | 74 | `evidence.json` only, 140 measurements, contract PASSES |
| `calguns_q/mega_324113` | 216 | nothing written; the agent had read all 216 pages |

**Those 370 measurements are excluded from the 4,400 and must not be trusted.**
They pass the contract, which only means quotes are verbatim and references
resolve. They have no manifest, so they cannot state `hidden_truth_read`,
`network_used` or coverage, which are the guarantees the parse rests on. They
have no independent verification pass, no coverage statement and no
`case_link_risk` block, and both agents were still linking cases across page
ranges when they died, so case identity is incomplete by construction. Redo
from scratch. `PARSE_QUEUE.json` records this under
`calguns_plan.partial_megathreads` and `calguns_plan.REDO_REQUIRED`.

### 2. Parse the remaining 20 megathreads: 3,971 pages

Nearly five times the 828 pages parsed so far, and on current density the
richest evidence left in the repository. `PARSE_QUEUE.json` lists each with its
page count and signal score. Three rules are already written into the plan:

- **Megathreads are read in ascending page windows**, because a case spans
  dozens of pages. Keep a running author-to-`case_id` index and reuse an
  earlier id when a later window continues that author's story. Declare a
  `case_link_risk` block. This is why megathreads matter: they are where
  end-to-end durations with a real start and end live.
- **Policy changes inside a multi-year thread.** Never merge an early statement
  with a late one. A rule change visible inside one thread is a before-and-after
  on one process in one county, which is the most valuable comparison available.
- **Thread 324077 must be parsed as ONE 709-page unit across two slices.** See
  the decision log below.

One ordinary batch remains, `calguns_a` batch 5, and it is a single page. Fold
it into another brief rather than spending an agent.

### 3. Make a ledger fit-ready, which is now 753 decisions and no clerical work

Everything mechanical is done. `derive_structural_handoff.py` has written a
derived handoff for all 17 eligible ledgers and `derive_audit_skeletons.py` has
written 32 skeleton files, one work-order row per audit-eligible measurement,
each carrying its verified quotes, activity ids, statistic, unit and observation
context, with every judgement field an explicit `__DECIDE__` placeholder named
in that row's `to_decide`.

What a human or an agent must still supply per measurement is the semantic
judgement: `duration_basis` (wait-only against service), `censoring`,
`start_event`, `end_event`, `population_scope`, `reporting_sample`,
`statistic_interpretation`, and on the visit side `basis`, `visits`,
`identification` and `activity_mapping`. That is the seam the project exists to
measure and nothing automates it.

**A derived handoff is not a substitute for an authored one.** Measured on the
one process that has both: it reproduces 43 of 45 operation classifications, but
bridging with it gives 1 route instead of 3, 3 case paths instead of 8, and
**no repeat block at all**. Every case then traverses every operation exactly
once. Use it to answer whether a ledger can reach V6, never to produce a burden
number. What a reviewer must add is exactly three things no ledger field holds:
which rework group is the repeat block, which conditional groups are optional
toggles, and which activities are identity-merge candidates.

### 4. Two contract changes recommended and deliberately not made

- **A declared case registry.** A count claim's `case_id` must appear in a
  ledger measurement, and a measurement exists only for time, work, fees,
  staffing or volume. Across three converted sidecars, 24 burden counts reached
  the validated format and 21 more were refused solely because their case
  reported no duration or cost: 47%, replicated across unrelated processes. The
  cases dropped are precisely those whose whole complaint is the number of
  trips. This is a schema bump and 20 ledgers are at `process-evidence/3`, so it
  is a decision for Alex.
- **A metric for money flowing *to* the applicant.** The grand jury ledger
  records a year of service at 20 to 25 hours a week against a $15 per diem, and
  the parser had to record it as neither fee nor wage because no metric fits.
  This recurs wherever a process pays a stipend, reimburses mileage or awards
  costs.

### 5. Long-running work

**Updated later on 2026-09-19.** Both items below changed after the handoff was
written.

- **Solar chain extension**, `runs/rw_parse_20260918/solar_permit/fit_full_ext`.
  Chains 1 and 2 finished 4,000 extra draws; chains 3 and 4 were at 1,300 of
  4,000 at 18:50 UTC, roughly 3 to 4 hours left. A waiter (`wait_extend.sh`)
  will print diagnostics and run `analyse_posterior.py fit_full_ext` when it
  lands. Read the audit below before quoting anything from it.
- **sk3 is reachable again and the eight remote fits are collected**, 1.2 GB
  under `runs/w2_v6_fits_sk3_20260919/`. Four converged clean at population
  8,192 with three times the draws (C29, C29 deduplicated, combined, combined
  deduplicated); the S03 and five-programme fits did not; the two SolarTRACE
  multi-jurisdiction fits did not, for a structural reason recorded in the
  audit. Codex's `collect_remote_fit_reports.py` need not transfer them again.
- **The hourly parse cron is deleted.** It re-issued the original parse
  instruction after Alex had stopped the parse for this hand-off; recreate it
  only if the parse returns to Claude.

### 6. What the model audit changed about the plan

The consolidated sequence with owners and gates is `docs/2026-09-19-next-steps-plan.md`.

`docs/2026-09-19-bayesian-burden-audit.md`, written after this handoff, scored
V6 against the synthetic world's truth for the first time and found the
process clock overestimated 1.8 to 4.2 times, with three causes of known
direction. Three consequences for the fit-readiness chain in section 3:

- **Declare forum cases `delay_selected`** in the compiler policy and turn on
  `selection_sd`, rather than the current `default_case_sampling: unselected`.
  Validate on W2 first, where the selection is planted.
- **Write cohort bindings for published medians that state their n.** The
  solar fit dropped all 69 SolarTRACE and dashboard medians because none had
  one, and was fitted to forum reports alone. The audit's "published 4 days
  versus posterior 37" comparison in the first-results note is void for that
  reason.
- **Score every synthetic fit against truth before quoting it.**
  `runs/w2_v6_fits_20260918/compare_to_truth.py --runs DIR` is the stopgap
  until `evaluate_burden.py` reads the V6 layout. No real-corpus clock should
  be quoted as a burden estimate until the synthetic ratio is near one.

## The fit result, stated plainly

The 3,000-iteration solar fit **did not converge**: `posterior_converged: false`,
262 of 2,527 coordinates flagged. The failure is sampling effort, not
construction: R-hat median 1.002 and p90 1.009, with only 16 coordinates over
1.05 and 3 over 1.10; bulk effective sample size median about 1,900 with 202
under the gate. The numerics are clean, and one precision gate misses by 4.7% of
its tolerance.

Provisionally only, the whole process to initial decision has a median of 226
days against a published 113, with a 90 percent interval of 130 to 388. Permit
review moves 4 to 37 days, inspection 11 to 40, installation *down* from 16 to
5.5.

**The one genuine inference is the route posterior.** The hypothesis that
automated review *replaces* the authority's plan review carries 0.513 of the
weight against 0.221 for the ledger's literal reading that every named activity
is distinct. The model prefers, better than two to one, that two separately
named activities are the same work.

**The identification figure is the answer to "will the data get there".** Of
2,514 coordinates, 2,418 contract by less than 25 percent against the prior and
2,191 by less than 10 percent. On the best-covered process, with 476
measurements, about ninety-six coordinates reach the contraction headline
eligibility requires. Much of the remainder is nuisance structure no data would
pin down, so that overstates the problem, but a process median known only to lie
between 130 and 388 days is a factor of three.

## Decisions I made

**Partitioning 4,800 forum pages by complete thread, not by page.** A forum case
is one person narrating one application across a thread, and the recipe requires
a stable `case_id` per author per case. Splitting a thread across two parsers
would double-count the case under two ids, which is the contamination the dedup
work measured at +26.8% on the clock. I built a triage (regex signal score, a
reading order only) and a partition into agent-sized batches of complete
threads, with megathreads separated out.

**I checked the wrong invariant, found it, and fixed the plan.** I validated
that the three slices were disjoint *at the file level* and told three agents
they shared no document and no thread. The document half is true; the thread half
is false for thread 324077, which my byte-sorted filename partition split across
two slices, 32 pages in one and 677 in the other, because "1000" sorts before
"445". Nothing was contaminated: page numbers do not overlap and no parsed batch
cites any of its pages. `PARSE_QUEUE.json` now requires it to be parsed as one
709-page unit with a single case-id namespace.

**Reusing the agency-side activity vocabulary on the forum side, with a
prefix.** Forum agents reuse the 21 `ccw__` ids from the already-parsed agency
ledger and prefix anything new `ccwf__`. That made a finding visible that no
single parse would have produced: the agency publishes 21 steps and applicants
describe 54 more. It also produced vocabulary drift, three genuine synonym
clusters across seven independently-minting agents. I wrote
`runs/rw_parse_20260918/ccwf_alias_proposal.json` as a review artefact rather
than editing seven accepted ledgers, and it records six pairs that look like
duplicates and must stay apart, the most important being that the appointment to
hand in an application must not merge with the appointment for the interview,
which can be a year later.

**Telling later agents an earlier agent's conclusion and asking them to attack
it.** Batch 1 concluded that every deadline runs against the applicant while the
statutory decision deadline is exceeded without consequence. I passed that to
every later batch and asked for contradictions. Four found them, and the finding
changed twice. The current reading is that **the delays are a capacity failure,
not a design**: every stated cause is operational, and no document describes a
policy of delay. The asymmetry that survives is structural, not temporal, and
counter-examples cluster in small rural counties while failures cluster in large
urban ones. I would have recorded the stronger and wrong version otherwise.

**Quarantining the scratchpad.** An agent flagged that the shared session
scratchpad root held 180 synthetic-benchmark `*.hidden.json` and `*.spec.json`
files, the answer side of the benchmark, in the directory every parse agent
writes to. It declined to open them. That was right and it is not a control. I
moved all 181 behind a README, along with a `numbers.py` that shadowed the
standard library. The source-only guarantee was being enforced on what agents are
told to read, not on what is lying where they write.

**Building four review tools rather than one big one.** `convert_counts_sidecar`
(44 tests) moves ad-hoc count sidecars into the validated format and refuses
anything whose denominator is not one case's passage.
`derive_structural_handoff` (17 tests) writes the mechanical part of a handoff
and leaves the judgement empty. `derive_audit_skeletons` (12 tests) writes the
per-measurement work order. `audit_fee_scope` (22 tests) flags fee measurements
whose own quotation contradicts their scope. Suite went from 765 to 859.

**Two things I got wrong and corrected in the log.** I said counts had nowhere to
go; the compiler already accepts a validated count audit and parsers were simply
never told the format. I said self-reported effort was close to a dead end; 153
of 240 effort claims now carry a magnitude, though nearly all of the new ones are
statutorily mandated training hours rather than self-timed effort, so the
corrected position is narrower than the number suggests. I also asserted a
cross-ledger contamination risk without checking it and it was wrong: zero strong
copied-claim clusters in any ledger, four byte-identical documents across 23
processes with none cited twice, and of 454 case authors exactly one shared token,
the generic word "commenter".

## Things worth knowing before touching this

- **The pilot statute has no applicant voice.** After 20 processes and 6,783
  documents, AB 2533 has zero observed durations (all eight elapsed figures are
  deadlines) and zero first-hand accounts of legalising an unpermitted unit. The
  county evidence set I hoped would supply it says "No. Not one." If the project
  needs that side, it must be collected.
- **`county_user_evidence` carries one `program_id` over five unrelated
  processes.** It must be split before fitting or left out.
- **No population rate survives review anywhere in the forum corpus.** Every
  candidate divides licences by residents, mixes renewals into the denominator,
  mixes revocations into the numerator, or omits open cases.
- **Seven separate instances of the metric seam are logged**, the sharpest being
  four published timeliness percentages on four different clocks giving 88% and
  75% on identical cases, and a medical timeliness measure that removes
  incomplete and delayed applications from both numerator and denominator.
- **Pacing.** Three session limits were hit. Four concurrent agents is within
  the instructed pace but these agents run 400 to 800 thousand tokens each, so
  four of them for forty minutes exhausts a session regardless. Incremental
  writing is what saved work each time; agents still in their reading phase lost
  everything.
