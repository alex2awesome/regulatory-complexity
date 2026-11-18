# Making the model measure the burden we actually care about

2026-09-18. Alex re-ranked what the measurement is for, and this records the
changes that follow and why each one is worth doing. The audit of the machinery
is [separate](2026-09-18-bayesian-machinery-audit.md); this is about what the
machinery is pointed at.

## Why

What matters absolutely is **burden to the applicant**. We do not need to
estimate the whole process model to get there. In priority order: how many steps
the applicant goes through, how onerous each step is, and how much money the
process costs including the risk of external costs from delay. Explicitly lower
priority: bureaucratic cost and agency labour hours, back-office steps, and
exact completion boundaries, where estimates are fine.

Measured against the five bridged programmes, the current model is pointed
somewhere else. 48 of its 93 operations are agency-side. Its one well-identified
output is an operation count that is largely structural. Its headline quantity
is a clock whose statutory definition no document can pin down. Meanwhile 51 fee
claims, roughly 19 resolved count claims and every applicant-effort claim sit in
the ledgers unused.

The reason is not that the model lacks the machinery. It is that one line keeps
the evidence away from it:

```python
# audit_measurement_semantics.py:66
return [m for m in evidence['measurements'] if m['metric']=='elapsed' ...]
```

Everything downstream sees only what survives that filter. The evidence contract
already allows `fee`, `payer_work`, `agency_work`, `staffing_fte` and
`annual_volume`. The model already has a `payer_hours` channel and a working
count likelihood in `count_log_probability`. Both halves exist; they have never
been introduced. That is why we measured zero direct payer-hours observations
while `payer_hours` was a modelled channel all along.

A second, smaller reason: the semantic audit exists because *durations* are
ambiguous. A number attached to a fee is not. "$190 at submittal" needs no
reading-disambiguation, so fees do not need the audit that durations need, and
requiring one has kept them out for no benefit.

## What changes

### 1. Money becomes a path functional, not a channel

An operation may carry an optional published `fee`. A case's total is the sum of
the fees on the operations it actually traverses, multiplied by how many times it
traverses them. A new `payer_fee_total` basis reads that sum off the trace.

This is deliberately **not** a fourth resource channel. A fee is published, not
random: it needs no agency, task or operation hierarchy and adds no sampled
coordinates. All of its uncertainty comes from structure the model already has,
namely which path the case took and how many correction rounds it incurred.

The payoff is that cost becomes path-dependent for free, which is the burden
claim the project rests on: a case that stops at the first gate never pays for
the inspection. It also means a fee schedule, which is the most reliable and
least ambiguous document in the corpus, finally enters the likelihood.

Contract: `payer_fee_total` joins a new `MONEY_BASES`, handled like
`COUNT_BASES` — it may not mix with duration or count operators in one
observation, and it is an individual (per-case) report. Reported totals are
round ("about $350"), so the likelihood is a relative-error report model.

### 2. Counts reach the likelihood they already have

`count_log_probability` is implemented, tested and unused on W2, because count
claims live in `burden_counts/audit.json` and no compiler reads that file. The
compiler gains a path from that audit to individual count observations over
`COUNT_BASES`. No new mathematics. This serves the first priority directly.

### 3. The elapsed-only gate is lifted

The compiler stops scoping itself to `metric == 'elapsed'`. Fee and effort
claims compile without requiring a semantic audit they do not need; duration
claims keep requiring it, because they remain genuinely ambiguous. Every claim
that still cannot be modelled keeps a recorded disposition, as now.

### 4. Source families are grouped into types

Today every document is its own source family, so the FAQ's offset is learned
from two observations and each reddit thread gets its own. Grouping into
`agency_official`, `agency_dashboard`, `news`, `forum` and `third_party` pools
the bias into one identified contrast per type.

This is the measurement Alex asked about: the gap between what an agency states
and what applicants report. It is real and large in this corpus. C38's dashboard
states a median of about three months over the 868 cases that reached a
decision, explicitly excluding withdrawn and in-progress cases, while individual
applicants in the same programme report spans up to 1017 days. Part of that gap
is clock definition and part is selection. Neither part is measurable while the
bias is scattered across per-document offsets.

### 5. Agencies are pooled where they are genuinely the same body

Three tiers, and only the first two may pool:

| tier | example | pool? |
|---|---|---|
| state-level body | Marisol Contractors State License Board, in all three S12 programmes | yes |
| same county, two statutes | Ulverston County, in C44__S12 and C44__S03 | yes |
| same name, different counties | an Auditor-Controller, Revenue Division in seven programmes | **no** |

The third tier is a trap the handoff document warned about, and pooling it would
invent a shared agency that does not exist. Only one agency currently pools
across programmes, so nearly all the available cross-programme information flow
is unused. This is what lets a task effect learned in one county inform another.

### 6. Effort units widen

A claim like "a few weeks of my time" was extracted and then discarded because
no work-week unit exists in the validator. Applicant effort is the second
priority; it should not be dropped on a unit technicality.

## What is deliberately not changing yet

**Selection-aware population likelihood.** The dashboard medians over 868 and
2,905 decided cases are the best agency-side anchors in the corpus and both are
refused, because covering decided cases only is duration-dependent selection,
which the model explicitly does not support. This is the hardest item and the
one most worth doing next, since the selection is much of the seam we want to
measure. Guessing at it now would manufacture the very number we are trying to
observe.

**A single agency-responsiveness factor.** Alex raised collapsing an
overspecified cluster we care less about. The safe mechanics are already in
place: hierarchical shrinkage makes many sub-values map to nearly one posterior
when data is thin, and the information report already marks blocks below 25%
marginal contraction as ineligible for a headline. Those change what we claim,
not what we model, so they cannot be wrong. An explicit reduced-rank factor
hard-codes a structure that might be, and it is the brittle option. Deferred by
agreement.

**Cross-case `copied_from` and the `basis` field.** Both remain real contract
gaps. `copied_from` is partly mitigated already: `audit_copied_claims.py`
detects duplicated claims and `dedup_copied_cases.py` builds the sensitivity
variant, so the double count is measured rather than silent.

## How this will be reported

Headline the applicant-experienced span from when they began preparing, not the
statutory clock from "a complete submittal", which is agency bookkeeping and
which no document pins to an activity. Report p90 beside every median, because
delay risk is a tail question. Suppress coordinates below the contraction gate
rather than collapsing structure to hide them.

## Outcome, measured (2026-09-18T18:36:37)

Implemented and tested; suite 729 passing, up from 656. Every change defaults to
the previous behaviour and byte-identity with saved outputs was verified in all
three lanes. But the diagnosis that "one filter is starving everything" was only
partly right, and two of the six items rested on premises that turned out to be
false.

| change | outcome |
|---|---|
| money as a path functional | **works**, and is the real win |
| counts into the existing likelihood | plumbing done, 1 observation of 19 claims |
| elapsed-only gate lifted | done, opt-in per channel |
| source families grouped | done, opt-in, not yet exercised |
| agency pooling | correct, buys nothing today |
| effort units widened | compiler side done, blocked upstream |

### What genuinely improved

Money. Of 51 fee claims, C29 turned 13 into 4 case observations plus 4 route
inputs, and C35 turned 6 into 4 plus 2. C44__S12 is now fully priced, $175 and
$205 on two steps with 16 steps priced at zero by recorded judgement and none
unstated, so a fee total is available on every route and all 12 paths. The model
side carries it with no new coordinates and demonstrates the payoff: a reported
total of $140-180 versus $380-420 moves the posterior over which path a case
took from below 0.1 to above 0.9.

C29 initially produced no fee total, and that turned out to be my error rather
than a property of the documents. Its application fee is $180 on a form and $225
on a fee schedule, and I wrote that nothing dates the change. The corpus dates
both: the measurements carry "Amount printed on the application created August
7, 2021" and "Schedule current as of March 30, 2026" in their own fields, and a
third source reporting $180 for a 2020 case is annotated by the extractor as
explicitly historical and not a current rate. The bridge was comparing bare
numbers and discarding all of that.

Fee resolution now applies dated precedence. Where every disagreeing amount
dates itself and one is unambiguously latest, it supersedes, and the earlier is
recorded as a superseded amount with the basis rather than dropped. Undated
disagreement still refuses, because then there is genuinely nothing to rank on.
This also matches how the benchmark scores: predicting a `prior_version` amount
is counted as `stale_fee`, an error, so preferring the current value is what the
scorer already rewards. C29's application step resolves to $225 with $180
recorded as superseded, no operation is left unpriced, and a fee total is now
available on all four routes where before it was available on none.

### Where the premise was wrong

**Agency pooling buys nothing today, and the evidence I cited for it was a
misreading.** I said a two-programme fit allocated 11 agency coordinates where
the programmes separately need 12, so one agency was shared. That shared
coordinate is `role:payer`, the model's bucket for payer-role operations, not an
agency at all. Zero agencies pool. Implementing the rule correctly still yields
zero, for two reasons: no state-level body owns an operation in any bridged
programme, since the Marisol boards are registry and oversight actors only; and
the one genuine same-county pair, C44 across both statutes, cannot be bridged
because C44__S03 has no structural handoff. The rule is right and will pool the
moment either condition changes. It is not an information gain now.

**Applicant effort was never gated by the filter.** I wrote that lifting the
elapsed-only gate would unlock "every applicant-effort claim". There is exactly
one `payer_work` claim across all five programmes, and both it and the one
`agency_work` case claim were extracted with a null magnitude, marked
qualitative: "a few weeks of my time", "four or five actual working days", with
the extractor noting that hours per working day are unknown. The contract also
does not admit a work-week unit. So recovering effort needs a contract change
*and* a re-extraction, not a compiler change. The compiler side is built and
tested anyway, and the gap is pinned by a test rather than left implicit.

**Counts are starved upstream, not downstream.** One of 19 count claims resolves
to something countable on a route under a conservative reading. The rest are
hypothetical, normative, historical, population-level, or lack an activity
linkage. The lever is the burden-count audit's scope and activity linkage, not
the compiler, which now works.

### Reading this honestly

Money was worth doing and is done. The other five items are now unblocked
machinery waiting on evidence that the extraction does not currently produce.
That is a better position than before, because the blockage has moved from
places we control to places we can name, but it should not be reported as three
new measurable channels.

## Real data, and the first fits that are properly identified

The real corpus turned out to be blocked by format rather than collection, and
both blockers are now gone: a freeze that withholds every file containing prior
analysis (627 `reveals` answer blocks across nine processes), and an
`artifact-only-index/1` view that the existing pipeline reads with hash
verification. A fresh-context agent is the transport in place of the
out-of-credit CLI, which also strengthens isolation, because an agent's file
access is auditable where the CLI could never prove what it read.

Two real ledgers are validated. They differ enormously in what they can support:

| process | measurements | observations of a real case | fees paid by anyone |
|---|---:|---:|---:|
| CPRA request | 67 | 3, two of them the same case | 0 of 13 |
| CSLB licence | 241 | 19 across 22 case ids | some |

The CPRA corpus states what the law requires and almost nothing about what
happens. CSLB is fit-grade, and it independently reproduced two things the
synthetic work had found: dated fee supersession, where an application fee rose
to $450 from $330 and three documents of different vintages disagree until you
read their dates; and the clock-boundary problem, where the board's own form,
step page and statute use "approved", "accepted" and "posted" interchangeably
and pin an 18-month clock to all three. The second is the same defect as the
synthetic world's missing submission marker, which was our single largest
measurement limit. The synthetic corpus was right about the thing that
constrained us most, which is evidence for its realism where it counts.

And a bug of mine worth recording. The first freeze globbed only `.txt` and
silently dropped every data file beside the documents, so the CPRA parse
concluded it had three observed durations while a file of per-agency average
days to determination sat unread in the same directory. Solar lost SolarTRACE
entirely. Recovering it produced the best real evidence in the project: 536
California jurisdictions, eight years, median permit, interconnection and
inspection times, a quartile sheet, and requirement sheets that are
per-jurisdiction step structure.

That dataset now drives the first properly identified fits in the project, at
6,298 informative observations against 366 parameters with no case latents at
all. For comparison, the synthetic fits carried 13 informative observations
against 155 parameters. The limits are recorded in the importer rather than
argued away: the phase medians of one cell share their installs so no
`sample_size` is asserted, a median is not a case and the phases must not be
summed, and an installer-reported dataset makes the sampling declaration an
assumption.

## The model has no primitive for waiting between steps

This is the largest structural finding of the day, it came out of real data,
and it is bigger than the money channel.

California's published solar phase medians are 4 days for permit review, 0 for
pre-install interconnection, 16 for installation, 11 for inspection and 12 for
final interconnection, against a total of 113. I described the roughly 70-day
remainder as 62%% of the elapsed time being unaccounted for. **That was
overstated and the correction matters.** About 22 of those days are not
unaccounted at all: the five California columns simply omit the design phase,
which is separately published at a 20-business-day median and a 13-week 90th
percentile nationally, and they omit the post-inspection stretch. On the
dataset's own national decomposition the genuinely between-phase share is 37 of
97 days, about 38%%, not 62%%. Comparing a total against a subset of phases
inflated the gap, and I should have checked which phases the columns covered
before quoting a share.

The finding survives the correction, and it is architectural. Of the four places
the remaining time could live, three do not exist:

- **Between-operation waiting has no primitive at all.** `CompactTrace`
  concatenates blocks with no gap term, so every day in a modelled process
  belongs to some operation. There is nowhere to put time during which nothing
  is happening.
- **The correction-round repeat is unavailable on this input**, and for an
  interesting reason: the ledger's one quoted `parallel` relation produces a
  nine-operation DAG block that absorbs the encoded repeat block, so no route
  carries a `repeat_key` and every operation runs exactly once. A single quoted
  parallelism silently removed the model's only mechanism for repeated rounds.
- **The post-decision stretch cannot absorb pre-decision time**, by construction.

The only home left is four operations no published phase span covers, plus case
variance and a report-scale term that is not process time at all.

So the model can represent a process whose duration is the sum of its steps, and
regulatory delay is largely not that. A fit on this input will necessarily
attribute the between-phase time to the steps themselves, inflating
per-operation durations to cover waiting that the documents attribute to no
step. That is not a defect in the data or the extraction; it is the shape of the
model, and it is the thing to change next.

What changing it means concretely: an explicit inter-operation gap term, or
equivalently a queue or dwell operation between named steps, with its own prior
and its own evidence channel. Until that exists, any per-operation duration this
model reports on real data should be read as "this step plus whatever waiting
preceded it", and the whole-process clock should be reported from whole-case
observations rather than assembled from step posteriors.

### The prediction, confirmed on the first real posterior

The short solar fit finished: 4 chains of 200 warmup and 300 draws, 1,913 of
2,514 coordinates flagged, so unconverged by construction and directional only.
Its likelihood check passed, so the numbers below are about the model's shape
rather than its arithmetic. Published California medians against what the model
inferred, in days:

| phase | published | posterior |
|---|---:|---:|
| AHJ permit review | 4.0 | **39.5** |
| pre-install interconnection | 0.0 | 2.8 |
| installation | 16.0 | 4.3 |
| inspection | 11.0 | **28.6** |
| post-inspection clearance | 2.0 | 2.2 |
| final interconnection to PTO | 12.0 | 8.9 |
| **whole process** | **113.0** | **205.8** |

This is exactly the failure the missing gap primitive predicts. The two phases
that sit next to the longest waits, permit review and inspection, absorb it:
review inflates tenfold, inspection more than doubles. The phases with little
waiting around them land close, post-inspection clearance at 2.2 against 2.0 and
final interconnection at 8.9 against 12. And the assembled whole-process clock
overshoots badly, 206 days against a published 113, because the waiting is
counted once inside the inflated steps and again in the case-level variance that
the whole-case observations pull upward.

So the model does not fail by falling short of 113 days. It fails by having
nowhere to put waiting except inside the steps, and then double-counting it.
That is a sharper diagnosis than the one I expected to get, and it makes the
remedy specific: an explicit dwell term between operations would give the
between-phase days their own home and let both the step medians and the total
land at once.

The converged run on identical evidence is still sampling and will say whether
these magnitudes hold. The pattern should not change, because it follows from
the model's structure rather than from chain length.

### Where the waiting actually is: not the agency's queue, the applicant's

The dwell primitive is built and provably inert when off, and the agent who
built it flagged an uncertainty that turned out to be decisive. It placed eight
gaps before the published phases, and asked whether a published "phase" might
already include its own queue, in which case matching it against a span that
excludes the queue would move time into the gap that the document meant inside
the phase.

The dataset answers this in its own variable descriptions, and the answer is
that it does:

- **Median AHJ Permit Time** is "business days between first permit submission
  to the AHJ and final permit approval", with resubmitted permits counted from
  the original submittal.
- **Median Pre-Install IX Time** is "between pre-install interconnection
  application to the utility and approval".
- **Median Final IX to PTO** is "between final interconnection request to the
  utility and granting of permission to operate".

Every one is a submission-to-decision span. The queue is already inside it. So
a dwell placed before those operations would double-count the wait, and the
eight-gap placement in the demonstration is wrong for exactly the four phases
that matter.

**This relocates the finding, and makes it more interesting.** If each agency
phase already contains its own queue, the unexplained time is not agency queue
at all. It is the time between one phase's decision and the next phase's
submission: after the permit is approved and before the inspection is
requested, after installation completes and before the final interconnection
request goes in. Those gaps are applicant-side and installer-side turnaround.

The dataset supports the reading directly. It publishes a separate **Design
Phase (sign-submit)**, "business days between customer signing and first permit
or interconnection application submission", at a 20-business-day median, which
is pure applicant-side preparation before any agency sees anything. The missing
days are of the same kind.

So the corrected picture is that a large share of the elapsed burden in this
process is time the applicant and their installer spend between agency
interactions, not time agencies spend deciding. For a project whose subject is
what a rule costs the person subject to it, that is a better answer than the one
we were chasing, and it is only visible because the phase definitions were read
rather than assumed.

What this means for the dwell work: the primitive is right and stays, and the
gap placement must be evidence-led rather than assumed. Dwells belong on the
decision-to-next-submission boundaries, not before the submission-to-decision
phases. That placement should come from the documents, as the structural
handoffs do, not from a modeller's judgement.

### Retraction: the 70-day gap was mostly an artifact of adding medians

I have now stated the solar timing gap three ways and the first two were wrong.
The third is checkable and it retracts the premise the dwell work was built on,
so it belongs here in full.

California 2023 publishes five phase medians summing to 43 business days
against a project median of 113, and I called the 70-day difference time the
steps do not explain. Two separate errors produced that number.

**The state sheet is not the whole chain.** It omits the design phase, national
median 19 business days, and the post-inspection phase, median 2. Those are
published, they are part of the process, and they were simply absent from the
columns I summed.

**Medians do not add, and the dataset proves it on its own aggregate.** The
Pre-Install Phase Total is *defined* as contract signing to install complete,
which is exactly design plus review plus install. No time can be missing from it
by construction. Its components' medians are 19, 11 and 15, summing to 45. The
published aggregate median is 57.

| | business days |
|---|---:|
| design + review + install, medians summed | 45 |
| published Pre-Install Phase Total median | 57 |
| excess | **12 (27%)** |

Twelve days appear from nowhere inside a span that is exhaustive by definition.
That is the median of a sum exceeding the sum of medians, which is what happens
when components are right-skewed and imperfectly correlated. It is arithmetic,
not queueing.

So the honest reading of 43 against 113 is: part is two phases the state sheet
does not publish, and most of the rest is the same median-of-a-sum effect,
larger here because the chain is longer. There is no large pool of unexplained
waiting to discover.

**What this costs and what survives.** The empirical motivation I gave for the
dwell term is retracted. I built a model feature on a number I had not checked,
and the check was available in the dataset's own variable descriptions the whole
time. The feature itself is sound, off by default, provably inert, and may still
be right for processes where documents evidence real queues, but it is no longer
supported by this evidence and should not be enabled on this basis.

What does survive is narrower and still worth having. The model genuinely has no
inter-operation gap primitive, which remains true regardless of whether this
dataset needed one. And the posterior's inflated per-operation durations, permit
review at 39.5 days against a published 4, are now better explained as an
unconverged fit reconciling step observations against whole-case observations
without capturing the skew that makes a sum of short phases produce a long
total. Whether that resolves with convergence is exactly what the running fit
will show, and it is the right question to ask of it.

The general lesson is the one that keeps recurring today: check what a published
figure measures before doing arithmetic on it. It cost me a wrong claim about
measurement bases, a wrong claim about pooling, and now a model feature built on
a phantom.
