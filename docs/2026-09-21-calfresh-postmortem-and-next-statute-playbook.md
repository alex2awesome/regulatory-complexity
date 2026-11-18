# CalFresh postmortem: what went wrong, why it burned tokens, and how to do the next statute faster

2026-09-21. Written after a full day on CalFresh process structure. This is a
defect postmortem and a playbook, not a results document.

## Bottom line

Roughly two thirds of the day went to discovering and repairing defects, not to
producing evidence. **Every single defect shared one property: it produced a
plausible number instead of raising an error.** None of them crashed. They were
all found by a person noticing that a figure looked odd, which is the slowest
and most expensive detector available, and which is what the "circling" was.

The fix is not more care. It is to make the plausible-wrong-value path
*impossible*, using four techniques that each caught a real error today:

1. **Reconciliation identities.** An arithmetic identity that must hold. The
   single highest-value technique of the day: `approved + denied + withdrawn ==
   disposed` instantly exposed a bad cell mapping that had already produced a
   headline number.
2. **Retained sources with replayable quotes.** Every claim carries
   `path + sha256 + char offsets` that reproduce. The forum pipeline has this
   and its numbers held. The county sweep did not and its whole table had to be
   withdrawn.
3. **Explicit "blocked" and "unmapped" classes.** Never let a retrieval
   failure, a JS shell, or an unknown field become a zero.
4. **Fail loud on unknown.** An unrecognised cell number, workbook, filename
   kind or field name must raise, never fall through to a default.

## Defect catalogue

Grouped by root cause, because the groups are what generalise.

### A. Silent coercion — a lossy read returned a plausible value (9 defects)

| defect | what it produced |
|---|---|
| `Path.read_text` collapses CRLF to LF; contract decodes raw bytes | every quote offset short by the count of preceding CRLF pairs |
| CF296 workbook with no data-dictionary entry, cells used anyway | "2.09M applications/year" and a disposition table that did not sum |
| `county_id` normaliser stripped `_` | `San_Francisco` never matched the registry; every multi-word county silently lost |
| filename-kind matched by prefix | `forum_thread` typed as `form` |
| decimal vs binary units | MiB reported as MB |
| HTTP 200 with a JavaScript shell | Alameda counted as "publishes nothing", biasing every rate down |
| API paging cap divided by a date span | "~68 submissions/month, corpus nearly exhaustive" — wrong by ~7x |
| `Python-urllib` User-Agent 403'd by Arctic Shift | zero rows, indistinguishable from "no data exists" |
| retry loop swallowed `'permalink' is not a valid field` | zero rows, read as an empty result |

**Rule:** any function that maps input to a category or a number needs an
explicit failure branch. `present_flag()` in `solar_sources.py` is the pattern
to copy — `None` means the survey did not answer and is not a No.

### B. Gate applied at the wrong level of the hierarchy (4 defects)

- A thread classified out of scope took its **commenters' own** initial-application
  episodes down with it — the gate was on the thread, the unit of analysis is the
  episode. Cost: 10 episodes, 18 action rows, silently.
- Statutory-layer check hardcoded to S07, so no S05 step was ever labelled statutory.
- Alias map shared across statutes, so an S07 entry renamed an S05 step that four
  counties had named independently.
- `--emit-occupancy` defaulted off, so a rebuild wrote the packet but not the
  model input, which looked exactly like a silent drop.

**Rule:** for every gate, write down which entity it is a property of. Scope is a
property of an episode, not of its container.

### C. Extraction that did not retain its source (3 defects)

The county sweep stored `steps_mentioned`, short quotes and notes — and **zero
page text for all 58 counties**. Consequences:

- The step-publication table could not be checked against anything, so all ten
  rows were assertions. One row ("1 of 58 counties publish missed-interview
  procedure") turned out to be an artifact of what extractors chose to record;
  the county credited with it had no such language on its page.
- The denominator was wrong too: 54 counties had readable pages, not 58.
- 27 of 54 county-guide quotes failed verification because they were recorded
  against rendered text with ellipses, not the captured bytes.

**Rule:** an extraction that does not retain its source cannot be audited, so its
outputs are assertions, not measurements. The capture *is* the deliverable.

### D. Order-dependent classification (1 defect, 2 wrong answers)

A first-match-wins label map with broad patterns silently made pattern **order**
part of the definition. `missed_interview` reported 0/58, then 1/58 after a
"fix"; both were wrong.

**Rule:** specific patterns before general ones, and assert that no label matches
two patterns. Better: cross-check any near-zero rate against the raw source,
because near-zero rates are usually coding artifacts.

### E. Concurrency and overwrite (2 defects)

- A 200-draw smoke test overwrote a converged 30,000-draw fit at its canonical
  output path.
- A shell supervisor started its own copy of a task and overwrote queue statuses
  edited by hand.

**Rule:** results paths are write-once. A failing run diverts to
`*_exploratory.json`. A status string is not a lock.

### F. Claims that outran the evidence (4 instances)

"Only the step block hurt mixing", "the sampler mixes at no size", "the
two-document jurisdiction had the highest step count", "the corpus is close to a
fair sample". Each was corrected by the next measurement — three of them by
someone else's check, not mine.

**Rule:** state the measurement, not the generalisation, until a second
observation exists.

### Own-goal checks

Two checks written *to catch* these were themselves wrong: an invariant that
conflated the evidence closure with a reading's own quotes (970 false failures),
and a coded-vs-raw diagnostic with a nested-loop bug that also regexed the JSON
record instead of a page, so the "raw" column was contaminated by the labels it
was meant to validate. **A new check is guilty until it has produced a known-true
negative.** Run every check against a case you know the answer to before
believing its output.

## What the forum pipeline got right

Worth copying wholesale. It survived the day with its numbers intact because:

- every quote carries `path + sha256 + char_start + char_end` and must replay
  byte-exact, `json_path` for values inside JSON;
- `detected: false` is defined as *a reviewed nondetection inside a valid reading
  opportunity*, and unread cells are **not rows at all**;
- the acceptance check runs the compiled input through the real adapter and
  contract **before writing**, so a compilation that would not load produces no
  file — this is what refused the rebuild and surfaced the CRLF defect instead of
  shipping 160 mislocated readings;
- identity scopes are case-scoped (`$case[...]`), so two commenters in one thread
  cannot both claim the file.

## Playbook for statute #2

Ordered. Do not start extraction before step 3 exists.

1. **Literature gate first, before any collection.** Today it ran last and
   returned "substantially scooped" after the collection was built. One agent,
   two hours, and it changes what you collect. Brief it with working API routes
   (OpenAlex with `mailto`, Crossref, arXiv, PMC; *not* WebSearch, *not* Semantic
   Scholar) and an identifying User-Agent, and require it to distinguish blocked
   from absent.
2. **Find the administrative census before the forum corpus.** For CalFresh,
   CF296 is 121 months x 58 counties of application dispositions and was used at
   one month and three fields, while a day went into forum threads that cannot
   reach 40 counties at all. Identify the equivalent series and its data
   dictionary *first*. Then write its reconciliation identity and run it.
3. **Write the three reconciliation identities before extracting anything.**
   (a) coverage partitions the corpus exactly once; (b) recorded rows equal
   consumed rows plus stated drops; (c) a domain arithmetic identity such as
   parts summing to a published total. These are cheap and they are what catches
   the errors a reader would otherwise catch weeks later.
4. **Fix the capture contract before the first fetch.** Retain bytes, hash them,
   record HTTP status, and separate `captured` / `captured_but_no_text` /
   `blocked`. Derive claims from the retained artifact with offsets that replay.
   `calfresh_county_captures_20260921/{capture,derive}.py` is a working template.
5. **Decide the unit of analysis and write it down.** Episode, not thread.
   Jurisdiction-step cell, not jurisdiction. Every gate then names its entity.
6. **Fix the action vocabulary once, with "one act by one actor", and freeze it.**
   Two of the recurring defects were vocabulary churn (15 vs 20 vs 22 actions).
   The recurring model failure was never inference — it was a step universe
   containing statutory sentences nobody performs, or the same act described twice
   from two offices.
7. **Estimate density before scaling collection.** Readings per
   jurisdiction-step is the number that predicts whether a fit means anything:
   ~9 converged in synthetic tests at 30 jurisdictions; real CalFresh has 1.11
   per cell at 58, and the 4-county pilot contracted county variance 54-67% where
   the 58-county fits managed ~9%. Compute this from a pilot slice, then decide
   how many jurisdictions to model.
8. **Only then scale extraction**, with the invariant suite running on every
   rebuild (`check_invariants.py`, 14 checks, each one a defect that actually
   reached a reported number).

## Cheapest high-value habits

- Put the denominator in the sentence. "1 of 58" was wrong twice; "1 of 41
  readable captures, 16 blocked" cannot be.
- Never report a rate whose numerator you have not spot-read at the source.
- When a number surprises you, check the extraction before believing the finding.
  Every surprising number today was a bug, not a discovery.
- A tool exit code is not a job result. A `nohup` wrapper exiting 0 was read as a
  sweep completing.
- `print(..., flush=True)` in anything that may be killed by a timeout.
