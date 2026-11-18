# One agency, complete: Ventura County Sheriff concealed-carry licensing

**Superseded 2026-09-20 by the [two-statute split plan](2026-09-20-two-statute-split-plan.md).**
Alex asked for two statutes, one per agent, not one agency split by function.
Ventura survives as the deepest authority inside the concealed-carry leg, and
the evidence measurements below still hold. The Codex/Claude division here is
not the current one.

Alex's decision: stop spreading effort across families, take a single real
agency to completion, and split the work between Codex and Claude. This is the
work order. It supersedes nothing about the three-family plan's standards; it
narrows what gets finished first.

## Why Ventura County Sheriff

Measured across the 73-ledger snapshot, it is the densest single-agency record
in the corpus, and the only candidate that carries all three of Alex's
priorities at once.

| | Ventura CCW | LA County CCW | best CalFresh county | best solar authority |
|---|---:|---:|---:|---:|
| applicant cases | 112 | 100 | 5 | 4 |
| individual elapsed rows | 139 | 182 | 14 | 9 |
| individual applicant-effort rows | 24 | 14 | 1 | 2 |
| fee rows | 19 | 41 | 0 | 10 |
| statutory caps and published targets | 16 | present | present | none |

Los Angeles is comparable in size but splits across the Sheriff, the LAPD and
several city departments, so "the agency" is ambiguous. Ventura is one issuing
authority, one fee schedule, one set of published promises. CalFresh and solar
are excluded as single-agency candidates for the opposite reason: their
administrative data is strong and their per-jurisdiction applicant evidence is
four or five cases.

**It is a bounded document set.** 169 frozen forum pages mention Ventura across
the three concealed-carry slices, plus 4 agency documents: **173 documents, not
4,548 pages.** One agent can read all of them properly in a day. That is the
whole point of narrowing.

**What the evidence already contains.** Steps, with counts: interview 53
references, application submission 41, determination notice 26, renewal 22,
issuance decision 14, licence issuance 13, appointment scheduling 13, firearms
training 11, Live Scan 10. Money, to four different payees: the sheriff, the
Department of Justice, a training vendor and a psychological examiner. Effort,
24 individual rows, which is the scarcest channel in the project. And a
published promise to measure against, 13 statutory caps plus 3 targets and 25
typicals.

**What it does not contain, and the estimand that follows.** There is no
administrative median for Ventura. The 112 cases are forum-selected. So the
estimand is *reported applicant experience under a stated selection model*,
compared against *what the agency and the statute promise*. That is a
promise-versus-experience comparison, not an unbiased population estimate, and
it is the more interesting claim. Selection correction is mandatory here, not
optional.

**Era is mandatory.** The Bruen decision of June 2022 moved California from
good-cause discretion to shall-issue, and SB 2 of 2023 changed training and
fees. A single pooled estimate across those eras would be meaningless. 2,285
frozen artifacts carry era markers, so the evidence exists.

## The split

Two tracks, one shared object, no shared files otherwise.

### Track A, Codex: the evidence

Codex owns this because it has the parsing and review machinery, the forum
companions with separated post bodies and signatures, the cross-ledger
duplicate candidates, and it is already mid-flight on concealed-carry episode
reconciliation.

1. **Enumerate and account.** All 173 Ventura-mentioning frozen documents, each
   accounted for, including those with no usable claim. Add the county's own
   published packet if the freeze lacks it: application instructions, fee
   schedule with payees, and the statutory deadline citations. Say what is
   missing rather than working around it.
2. **Case registry.** One row per applicant episode, deduplicated *across the
   fifteen ledgers that currently carry Ventura rows*, each with author
   identity, episode type (initial, renewal, amendment) and policy era
   (pre-Bruen, post-Bruen pre-SB 2, post-SB 2). The existing cross-ledger
   duplicate findings must be **applied here**, not left in a sidecar.
3. **Effective evidence.** One contract-valid evidence file containing only
   Ventura rows, with every existing hold and correction applied rather than
   referenced. This is the shared object.
4. **Route and money.** The Ventura step inventory with required, conditional
   and repeated marked, and the fee schedule with a payee per step. Renewal is
   the natural repeat block.
5. **Published versus observed table.** The statutory cap, the agency's
   published typicals, and the observed reports, as three columns of the same
   estimand, with each cell traced to a quotation.

Deliverable, under one new run directory: `effective_evidence.json`,
`case_registry.json`, `route.json`, `fee_schedule.json`,
`published_vs_observed.json`, one manifest. One packet, not two hundred.

### Track B, Claude: the model and the comparison

I own this because I have the diagnosis of why the clock fails, the source-trust
specification, and the list of row types the compiler currently drops.

1. **Admit the dropped rows.** A typical range needs its own likelihood, not a
   residual constant; start-of-process wording needs binding to a modelled
   event. On Ventura this is 25 typicals and 7 estimates now contributing
   nothing.
2. **Source trust, minimally.** Reference-source parameterisation with one type
   anchored, per-type report precision, and selection on for forum cases. Not
   the full hierarchy; the smallest version that makes the promise-versus-
   experience comparison well posed.
3. **Fit Ventura** as one programme with a renewal repeat block, stratified by
   era, reporting applicant-facing step count, fee total and trips beside the
   clock.
4. **Baselines on the same 173 documents.** The statutory 90 days, the agency's
   published typical, the corpus's own sentence, and an LLM given the same
   material. Same documents, same clock, same population.
5. **A held-out test, which this project has never had.** Hold out 25 of the 112
   cases by author, fit on the rest, and score predictive coverage against every
   baseline. Freeze the split before looking at it.

I can start on 1 and 2 immediately against the Ventura rows that are already
parsed, and refit when Track A's file lands. That removes the dependency stall.

### Interface and collision rules

- The only shared object is Track A's `effective_evidence.json`. Codex writes
  it; I read it. I do not edit it, and I report anything I think is wrong rather
  than fixing it.
- Codex writes only under its own run directory. I write only under
  `pipeline/procbench/` and my own run directory.
- Neither track touches `runs/rw_parse_20260918/`, `runs/rw_parse_20260919/` or
  the running three-family fits.
- The running CalFresh and solar conditions finish on their own and are released
  as agency processing time, separately from this. They are not blocked on
  Ventura and Ventura is not blocked on them.

## Timeline and the stopping rule

| | time |
|---|---|
| Track A, 173 documents to a frozen evidence file | 1 to 2 days |
| Track B, compiler and model changes on existing rows | 1 day, in parallel |
| Track B, fit plus baselines plus held-out score | half a day after Track A lands |

Two days to a complete single agency, with a held-out comparison against
baselines. The stopping rule: when the held-out score exists, the study is
reportable whether or not the model wins. If it loses to the statute's own
number, that is a finding about process modelling and it gets published as one.

## What this deliberately gives up

Everything outside Ventura, for now. No additional forum megathreads, no
grand-jury semantic reading, no Reddit batches beyond those already accepted,
no synthetic recovery work. Those stay preserved and unblocked, and none of them
is a gate on this result.
