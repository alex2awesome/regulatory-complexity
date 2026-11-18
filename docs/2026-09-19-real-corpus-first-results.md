# First results from the real corpus

**Later review:** the [continuation audit](2026-09-19-codex-parse-continuation.md)
reproduces the extraction totals but finds semantic and case-linkage errors.
Treat all outputs of the unconverged solar fit below, including route weights,
as provisional diagnostics. A quote/schema pass is not a correctness or coverage
guarantee, and manifest declarations do not establish technical access isolation.

2026-09-19. Five real California processes were parsed to the evidence
contract, two were compiled into model inputs, and one produced a posterior.
This records what the real documents can and cannot measure, which is a
different question from whether the machinery works, and a more important one.

Nothing here used a paid extraction transport. The Codex CLI has been out of
credits since 2026-09-18, so each parse was done by a fresh-context agent
reading a frozen document set. That is also stronger isolation than the CLI
offered: an agent's file access is auditable, where the CLI recorded
`hidden_truth_read: null` because it could never prove what it read.

## What was parsed

| process | measurements | cases | quotes verified | fee | elapsed | effort |
|---|---:|---:|---:|---:|---:|---:|
| CPRA request | 67 | 9 | 378 | 13 | 54 | 0 |
| CSLB licence | 241 | 22 | 581 | 55 | 149 | 1 |
| food facility | 182 | 14 | 826 | 118 | 46 | 4 |
| solar permit | 476 | 132 | 830 | 39 | 399 | 5 |
| ADU permit | 116 | — | 583 | 40 | 58 | 11 |

Every ledger passes the contract validator with all documents supplied, every
quote was sliced back out of its artifact and checked verbatim, and every
artifact hash was recomputed against its index. Forum quotes additionally had to
lie inside a single rendered field, so none can span a comment boundary and
silently merge two speakers.

Two preparation steps made this possible and are reusable. A freeze withholds
every file containing prior analysis: across nine processes it withheld 627
`reveals` blocks, a per-source register naming the activities, sequence, fees
and timings each document contains, with quotes. That is a partial extraction
sitting beside the documents, and handing it to a parser would have scored an
answer key. An artifact index then renders each source and each forum thread as
a document with a hash the pipeline verifies at read time.

## What the documents establish, by channel

**Money is abundant and mostly published.** 265 fee claims across the five
processes. But the permit fee is usually not the burden: in ADU permitting a
$3,000 building permit sits against $4,000 of school fees, sewer connections of
$2,000 to $20,000, and one case totalling $26,000 plus a $10,000 survey.
Meanwhile no published ADU fee schedule exists in the corpus for any
jurisdiction: every agency dollar figure there is a forum anecdote, and the
city's own advice is to phone for an estimate.

**Counts are stated but the contract cannot carry them.** `process-evidence/3`
has no count metric, so one parser had to record 37 count claims as free-text
markers in activity notes, including a county stating outright that its plan
check fee covers two plan reviews and two inspections. Those are exactly the
step counts the project ranks first, and they are stranded upstream of the
model rather than missing from the documents.

**Applicant effort exists, is described, and is never quantified.** Across all
five processes: 21 effort claims, almost all qualitative. ADU permitting has
eleven and not one carries a magnitude. The corpus can tell you effort consists
of repeated in-person trips, phone chasing, drawing your own site plan and
fixing your designer's errors. It cannot tell you how many hours. Four separate
target documents in the wider corpus record the same absence. This is not an
extraction gap and no retrieval pass fixes it.

**Durations are published as spans, not as work.** Every phase figure in the
solar dataset is a submission-to-decision span with its queue already inside it.
That distinction decides whether a number measures an agency's work or an
applicant's wait, and it is not visible without reading the variable
definitions.

## Three findings about regulation

1. **Automation collapses the step, not the process.** Under instant solar
   permitting, median permit review falls from seven business days to zero, but
   permit-to-passed-inspection only falls from 49 to 37, measured contractor
   time per permit rose slightly, and inspection failure rates are unchanged or
   higher. Removing a review step barely moved the applicant's experience.
2. **Several of the longest waits are not the permitting agency's.** ADU permits
   are gated by sewer availability, fire, address assignment, water-flow
   letters, sanitary districts and utilities; two cases waited two and six
   months on a utility that never responded.
3. **Some of the missing data is missing by regulatory design.** A CPUC decision
   exempted systems under 30 kVA, exactly the residential solar cohort, from
   timeline reporting. And every "hours saved" headline in that corpus rests on
   assumed review and inspection times rather than measurements.

## What the first posterior showed, and what it did not

The solar bridge produced 35 operations on three routes with 91 informative
duration claims over 67 cases, the most real informative evidence in the
project. A short unconverged fit inflated per-operation durations badly, permit
review to 39.5 days against a published 4, and overshot the process total.

I initially read that as the model having nowhere to put waiting, and built an
inter-operation dwell term on that basis. That motivation is retracted. The
dataset's own aggregate disproves it: its pre-install total is defined as
exactly design plus review plus install, so nothing can be missing from it, and
yet its published median of 57 business days exceeds its components' medians
summed at 45. Twelve days appear inside a span that is exhaustive by
definition, because the median of a sum exceeds the sum of medians when
components are right-skewed. The apparent gap was arithmetic, not queueing.

The dwell term survives as a capability, off by default and provably inert, but
it is not supported by this evidence.

## The long fit, which also did not converge

Four chains, 1,000 warmup and 2,000 draws at population 4,096, about five hours
and 726,000 likelihood calls per chain. It reports `posterior_converged: false`
and `numerically_usable: false`, with 262 of 2,527 coordinates flagged. Nothing
below is a result.

The shape of the failure is worth separating from the fact of it. R-hat has a
median of 1.002 and a p90 of 1.009; 227 coordinates exceed the 1.01 gate but
only sixteen exceed 1.05 and only three exceed 1.10. Bulk effective sample size
has a median near 1,900, with 202 coordinates under the gate of 400. So roughly
nine coordinates in ten are mixed and a tail of about two hundred is not. That
is sampling effort, not construction.

The numerics are clean, which is a different question and passes. Importance
effective sample size is a full fraction of states, weight total variation is
1.2e-16 against a ceiling of 0.025, and the log-likelihood does not move at all
between population 4,096 and 16,384. One precision gate fails by a hair: the
largest relative clock-quantile change between quadrature 256 and 1,024 is
0.0262 against a tolerance of 0.025.

Provisionally, and only provisionally, the whole process to initial decision has
a median of 226 days with a 90 percent interval of 130 to 388, against a
published 113. Permit review moves from a published 4 days to 37, inspection
from 11 to 40, and installation *down* from 16 to 5.5. The short run gave 206,
39.5 and 28.6 for the same three quantities, so permit review is stable across
run lengths, the process total moved a tenth, and inspection moved by 40
percent. Inspection is the least settled quantity in the model.

The route posterior is the most interesting output and it is a genuine
inference. The hypothesis that automated review *replaces* the authority's plan
review carries 0.513 of the weight, the hypothesis that pre-install approval is
not a separate utility work unit carries 0.266, and the ledger's literal reading
that all these activities are distinct carries only 0.221. The model prefers, by
better than two to one, a reading in which two separately named activities are
the same work. That is precisely what the identity hypotheses were built to ask,
and it is the part a mechanically derived structural handoff discards.

The identification figure is the sobering one. Of 2,514 whitened coordinates,
2,418 contract by less than 25 percent against the prior and 2,191 by less than
10 percent. On the best-covered process in the corpus, with 476 measurements and
248 audit-eligible durations, about ninety-six coordinates reach the contraction
that headline eligibility requires. Much of the remainder is nuisance structure
that no quantity of this data would pin down, so the figure overstates the
problem for the quantities anyone cares about. But those are not well determined
either: a process median known to lie between 130 and 388 days is a factor of
three.

The chains are being extended by 4,000 draws rather than restarted, because the
bulk is already mixed and the draws are on disk.

## What to do next

- Add a count metric to the evidence contract. **Partly superseded:** the
  compiler already accepts a validated count audit, so what was missing was that
  parsers were never told the format. What the contract still lacks is a
  declared case registry, so that a case reporting only a count can exist.
- Carry a declared source **type** per source family in the contract. The
  taxonomy can pool real documents when ids happen to carry a kind, and cannot
  when a parser invents semantic family names, which is the normal case.
- Stop treating applicant hours as an extraction problem. Measure onerousness
  structurally, from what each step demands, and count trips, which forums do
  report.
- Before quoting any published figure, read its variable definition. Three
  separate errors today came from not doing so.
