# Three machinery gaps the real corpus exposed

Later update: the count-only identity restriction in section 2 is repaired by
backward-compatible `burden-count-evidence/2` declarations and compiler support.
Eight source-reviewed DROS claims have been restored. See the
[continuation and validation record](2026-09-19-codex-parse-continuation.md).
This does not resolve count semantics, historical transport or multiple loops;
the original measurements and diagnosis below are preserved as a dated audit.

Written 2026-09-19, while the real-corpus parse is running. Companion to
`2026-09-19-real-corpus-first-results.md`, which covers what the documents say.
This one covers what the machinery can and cannot carry, measured rather than
asserted. Every number here comes from a script in the repository run against
the nine accepted ledgers, not from an impression.

## 1. The count channel was reachable all along, and I said otherwise

For three parses I reported that counts had nowhere to go because the evidence
contract (`process-evidence/3`) carries only elapsed time, payer work, agency
work, fees, staffing and volume. That is true of the contract and false of the
pipeline. `compile_visit_durations.py --count-audit` accepts a separate
`burden-count-evidence/1` file, validated by
`audit_burden_counts.validate_counts`, carrying a `basis` enum
(`observed_case`, `administrative_summary`, `informal_summary`,
`enumerated_inventory`, `normative_rule`, `hypothetical`, `unclear`), the
`additional_correction_rounds` versus `total_attempts` distinction, and a
`rate_claims` section that requires a real denominator. Two processes already
have conformant audits.

What was actually missing is that parse agents were never told this format, so
two of them invented `process-evidence-counts-sidecar/1` instead and their
counts sat outside the pipeline. The running agents now have the schema.

`convert_counts_sidecar.py` moves the existing sidecars into the validated
format. It converts only rows whose denominator is one case's passage through
the process and routes everything else to `unresolved` with its verbatim quote
and a reason, because a refused count is not a zero count.

| sidecar | rows | converted | refused |
|---|---|---|---|
| dros_firearm | 82 | 13 | 69 |
| ui_claim | 59 | 11 | 48 |
| cpra_request | 16 | 0 | 16 |

The records-request result is correct rather than disappointing: every row there
is a retention period, a fee basis or an output page count, and none of those is
a burden count.

The refusals themselves carry a finding. Every ad-hoc sidecar invented its own
`kind` vocabulary, and five of them produced more than forty distinct terms for
the same handful of ideas. The converter's policy table has to name each one,
which is why an unlisted kind is refused rather than guessed. Parsers now write
the validated format directly, so the table is a rescue for what was already
written rather than a growing dependency.

## 2. Count evidence is censored by duration evidence, and not at random

Eleven of the DROS refusals share one reason: the case identity is not a case of
the accepted ledger. They are real burden counts. Two dealers visited after the
first refused. Six gun shops telephoned to locate one firearm. An extra trip for
a second proof of residency. Three submissions, all delayed or undetermined. One
dealer employee asking the same question three times.

They are refused because `validate_counts` builds its case set from the ledger's
**measurements**, and a measurement exists only for elapsed time, work, fees,
staffing or volume. **Thirty of the forty-eight cases in the firearms sidecar
have no measurement at all.** An applicant who says they went back three times
but never says how long it took, or what it cost, has no existence in the
ledger, so their count cannot attach to them.

The figure replicated when the unemployment sidecar was converted. Across the
three converted sidecars, 24 burden counts reached the validated format and 21
more were refused solely because their case has no measurement. **Forty-seven
percent of the reachable burden counts are lost to this**, and the rate held
across two unrelated processes.

The unemployment loss is the more telling one, because the burden it drops is
that process's most distinctive: the telephone. The agency's own figures are at
least ten dial attempts per unique caller, 6.7 million calls a week from about
600,000 distinct people, under one percent answered. For many claimants a call
is the only thing that moves the claim, and it is the step the model cannot
currently hold.

This matters more than its size. The project's first priority is how many steps
the applicant goes through. The machinery makes count evidence conditional on
duration or money evidence, so the cases dropped are precisely the ones whose
whole complaint is the number of trips. The censorship is correlated with the
quantity of interest.

The fix is a declared case registry in the ledger, so a case can exist without a
measurement. That is a schema bump and nine ledgers are at `process-evidence/3`,
so it is recommended here rather than made. Loosening the validator instead
would drop a real typo check on case identities.

## 3. V6 carries one repeat block per programme; no real process has one loop

`bridge_structural_routes.build_loop` raises `Nested or multiple repeat loops
are not supported by the trace model` on the second repeat link. Counting the
connected groups of `rework` relations in each accepted ledger:

| process | rework relations | disconnected loop groups |
|---|---|---|
| ab2533 | 2 | 2 |
| adu_permit | 7 | 7 |
| ccw_counties | 2 | 2 |
| cpra_request | 4 | 4 |
| cslb_license | 4 | 3 |
| dros_firearm | 8 | 4 |
| food_facility | 4 | 3 |
| n400_naturalization | 10 | 4 |
| solar_permit | 3 | 3 |

Forty-four rework relations form thirty-two independent loops. The model can
represent nine of them, one per programme, and only if a person chooses which.
Not one of the nine processes has a single loop.

Repetition is the burden the project ranks first, and the architecture holds one
kind of going-back per process. A failed inspection and a rejected resubmission
are different repetitions with different costs, and today they compete for one
slot.

## 4. Nearly half of the elapsed evidence cannot be fitted as duration

This one is about the corpus rather than the code, but it belongs here because
it is the same question: what can reach the model. Applying the pipeline's own
eligibility rule, which drops statutory caps and targets, standing scope,
amountless rows, and historical or hypothetical contexts:

| fate of an elapsed measurement | count | share |
|---|---|---|
| eligible for the duration channel | 753 | 53.4% |
| a statutory cap or a target | 447 | 31.7% |
| no amount stated | 117 | 8.3% |
| historical or hypothetical | 76 | 5.4% |
| standing scope | 18 | 1.3% |
| total elapsed across 13 ledgers | 1,411 | |

Of the 753 that survive, 412 are individual-case observations and the rest are
typicals, means and estimates.

**Three processes contribute zero, and one of them is the pilot statute.** The
accessory dwelling unit amnesty has eight elapsed figures and all eight are
deadlines. Its public corpus prices the process, states what the city promises,
and never once records how long anything took. The records-request process has
fifty-four elapsed figures and none eligible, which makes sense for a process
that is largely constituted by its own statutory response clock. Assessment
appeals has three, all caps.

The concealed-carry agency side is nearly as stark, at 43 caps against 7 usable
figures. That is the clearest argument for the forum corpus: the agency
publishes what it promises, and the 4,800 forum pages are the only place the
same process is observed.

Five processes hold 88% of the fittable duration evidence: solar permitting 248,
naturalization 175, the contractor licence 90, food benefits 80, and
unemployment 66.

**That table was computed before the forum corpus was parsed, and the forum
corpus changed it.** Counting the seven concealed-carry forum units separately,
the corpus holds 4,400 measurements, 2,687 elapsed and 1,466 audit-eligible. The
forum units are 828 pages, twelve percent of the document corpus, and they carry

| | forum units | everything else | forum share |
|---|---|---|---|
| measurements | 1,577 | 2,823 | 36% |
| eligible durations | 665 | 801 | 45% |
| distinct cases | 574 | 513 | 53% |
| applicant-effort claims | 150 | 90 | 62% |

They nearly doubled the fittable duration evidence on their own, and the
mechanism is visible in the eligibility rate: 66% of their elapsed figures
survive the eligibility rule against 48% elsewhere. Official corpora are made
largely of deadlines, targets and caps. A forum is made of things that happened.

The largest single lever on this project's ability to estimate burden turned out
not to be a modelling change but reading the applicant side of a process whose
agency side was already parsed. Twenty forum megathreads holding 3,971 pages
remain unparsed, which is nearly five times what has been read.

None of this means the evidence is poor. A deadline is real evidence about a
process, and the distance between what is promised and what is observed is the
object of study rather than noise in it. What it does mean is that a burden
estimate cannot be assembled uniformly: for five processes the model fits
observations, and for three it would fit nothing.

## What was built, and what it is fit for

`derive_structural_handoff.py` writes a `source-only-structural-handoff/1` from
what a ledger already records: scope, stage, task type, actor role, rework and
parallel relations, source families, and the ledger's own quotations re-verified
against the artifacts. It refuses to invent. Merge hypotheses, clock boundary
markers, agency identity notes, distinct-case warnings and jurisdiction scoping
come out empty and are named in `derivation.not_derived`. Output carries
`variant: "derived_default"` and `reviewed: false`.

Against the one hand-authored handoff, on solar_permit, the derived
classification agrees with the author on whether an activity is an operation for
**43 of 45 activities, 95.6%**. Both disagreements are the same kind, and they
are not benign: `nem2_extension_request` and `utility_detailed_study` are
ledger-conditional activities the author excluded because they sit on a
different route, a superseded tariff and a non-residential scale. Route
membership is not a ledger field. The error direction is over-inclusion, and
over-inclusion inflates burden by putting operations on a path that does not
traverse them.

That label comparison is the easy test, and on its own it flatters the module.
The real test is bridging one ledger and one compilation twice, once with each
handoff, and diffing the V6 inputs:

| | routes | operations | case paths | repeat block |
|---|---|---|---|---|
| authored | 3 | 35 / 34 / 34 | 8 per route | the correction round |
| derived | 1 | 37 | 3 | none |

The 267 observations are byte-identical, which is correct, because the
compilation is untouched. Everything structural differs. The derived input
reproduces all 35 authored operations and adds the two off-route ones, as the
labels predicted, but it also drops the repeat block, every optional toggle and
two of three routes.

In the derived model **every case traverses every operation exactly once**.
Nobody skips a conditional step, nobody goes round a correction loop, and no two
activities may turn out to be the same thing. Three errors push in different
directions and the net effect on a headline number is not predictable, but the
structure that carries burden heterogeneity is simply absent. A derived fit
cannot express that some applicants have it easy and some go round three times,
which is the distribution the project exists to measure.

So the verdict is narrower than it first looked. A derived handoff answers
whether a ledger can reach V6 at all, and it must not be fitted for a burden
result. It works for that purpose: `cslb_license`, which had a compilation and
no handoff, bridged into a V6 input of 48 operations and 2,615 dimensions, the
second real process ever to reach the model.

Its durable value is as a review checklist. Everything mechanical is done, and
what a reviewer must still supply is exactly three things no ledger field
records: which rework group is the repeat block, which conditional groups are
optional toggles, and which activities are identity-merge candidates. That is a
real reduction from six hundred lines of authoring, and an honest one.

## What still blocks the rest, and what was taken off it

The two per-measurement audits. Each eligible measurement needs a row deciding
what its figure means: waiting or service, where the clock starts and stops,
whether the case was still open when it was reported. None of that is in the
ledger and none of it is derivable, because it is the semantic judgement the
project exists to make.

What was clerical has been removed. `derive_audit_skeletons.py` writes a work
order per ledger: every eligible measurement, already carrying its verified
quotations, its activity identities, its stated unit, its statistic, and its
observation context, with each judgement field left as an explicit placeholder
and named in that row's `to_decide`. Four hundred and fifteen such rows are now
written across eight ledgers.

Two defences keep a placeholder from passing as a decision. The files declare
`visit-audit-skeleton/1` and `semantic-audit-skeleton/1`, schemas no consumer
accepts, so a skeleton cannot reach the compiler by accident. And every
placeholder field also appears in `to_decide`, so an unfilled row is visible
without reading its values.

Exactly one field is filled without judgement: `original_precision_unit`, which
restates the unit the ledger already recorded. `reporting_sample` is left as a
placeholder specifically because its enum has no abstention value, and
defaulting it to `other` would be answering rather than declining.

What remains is 753 decisions across thirteen ledgers, and they are the
decisions that matter.
