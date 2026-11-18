# Solar: a posterior over the process itself, and where it broke

2026-09-21, overnight. Claude's leg of
`docs/2026-09-21-process-structure-posterior-plan.md`: phases 1 to 5 on solar
permitting, real data. Codex owns CalFresh and concealed carry. Written as the
work ran, so the failures are in their place in the order rather than tidied
into an appendix.

Status: phase 1 complete. Phase 2 run and **failed its convergence gate**, and
the follow-up shows the sampler does not mix at any problem size, so phase 3
has nothing to stand on and is not attempted. Phase 5, the burden table, is
complete using directly observed presence instead, and the stringency cross the
solar leg has owed since Stage A is complete. The two substantive findings are
in sections 3 and 4; section 2 is a negative result about the model the plan
was built on, and it is the most consequential thing here.

## 1. The step universe and the detection matrix

`runs/process_structure_20260921/solar_phase1`.

The universe is the union of every step any source names, which is the design
decision the whole plan rests on: build it from the statute alone and a step a
county adds on its own can never appear. It holds **50 steps** over **440
California authorities**, labelled by the layer they were observed in.

| layer | steps | what presence means |
|---|---:|---|
| statutory | 11 | mandated burden |
| administrative-only | 10 | burden the authority added |
| other party or applicant | 29 | burden carried by the installer, engineer or utility |

Five of the 50 steps exist in the universe only because the SolarTRACE
requirements survey asks about them: structural review, electrical review,
third-party plan review, over-the-counter same-day permitting, and online
portal submission. The parsed ledger's 45 activities do not contain them. That
is the mechanism working as intended.

Four source types were considered and three carry evidence:

| source | authorities | reading opportunities |
|---|---:|---|
| requirements matrix | 440 | 3,998 |
| the authority's own documents | 2 | 100 |
| applicant accounts | 0 | 0 |

**Applicant accounts contribute nothing to solar, and that is a finding rather
than an omission.** The verified solar forum dataset locates a report against
authorities as a weighted candidate distribution, because posters name a
utility or a region and almost never a building department. Of 234 rows only 26
have a single candidate authority. A weighted candidate set is not a reading of
one authority, and turning it into one would have invented the evidence the
model is most short of.

**Only two authorities have their own documents**, Oakland and San Diego. The
plan expected the authority side to be near-complete detection. It is
near-complete in the *survey*, which is one instrument, not in independent
documents.

Missing survey answers are recorded as no reading opportunity, never as a "No".
Third-party review is unanswered for 334 of 440 authorities and the inspection
count for 281. A model that read those blanks as absence would find a tidy,
false process.

### Where detection is actually estimated

Occupancy needs repeated looks at the same jurisdiction and step, or a known
answer, to tell "the step is absent" apart from "the source missed it". Solar
has both, thinly:

- **883 cells with repeated readings.** The survey ran in waves, and the 2024
  and 2025 online-permitting questions are two looks at one step. The 2019 and
  2022 waves are deliberately excluded: Government Code 65850.52 required
  authorities to stand up automated permitting on a staggered deadline through
  2024, so a change across those waves is a real change in the process, not a
  detection difference.
- **859 anchors** from the timeline panel. A reported permit or inspection
  timeline is explicit evidence that the phase happens. Anchors are inputs, so
  they are never also scored.
- **156 calibration opportunities**, where the panel anchors a step present and
  the survey also answers for it. That is the entire basis on which the
  survey's detection probability is estimated rather than assumed, and it
  exists for one step, the final inspection.

## 2. The held-out test, and its failure

`runs/process_structure_20260921/solar_phase2`.

Design as specified: five folds over the 440 authorities, the requirements
matrix removed entirely for the held-out fold, their answers then scored
against the posterior. A held-out answer is never an anchor, because an anchor
is an input and an input cannot be a test.

**All five folds failed the convergence gate.** Worst R-hat 4.31 to 4.45
against a threshold of 1.01; minimum effective sample size about 4 against a
threshold of 400. Every structural parameter is flagged, not a tail of them.

The predictive numbers are therefore diagnostics, not findings, and they look
exactly like a chain sitting near its prior:

| step | scored | true rate | mean posterior | Brier | area under curve |
|---|---:|---:|---:|---:|---:|
| structural review | 369 | 0.539 | 0.706 | 0.280 | 0.49 |
| electrical review | 388 | 0.010 | 0.264 | 0.081 | 0.35 |
| third-party review | 106 | 0.217 | 0.485 | 0.236 | 0.63 |
| rough-in inspection | 436 | 0.055 | 0.584 | 0.336 | 0.55 |
| same-day counter | 408 | 0.422 | 0.548 | 0.263 | 0.46 |

Discrimination is at chance. Presence is over-predicted everywhere, most
starkly for rough-in inspection, where the file says 5.5 percent of authorities
require one and the posterior says 58 percent.

One thing is worth saying carefully, because it is the opposite of the failure
the plan was most worried about. The gate asked whether the model reads silence
as absence. It does not: with the survey withheld, recovered step counts go
**up**, to 2.1 times the file's own count of Yes answers. The model's error
here is credulity, not deafness. That is the right direction to fail in, and it
is still a failure.

### A sharper reason, found on audit

The synthetic test-beds later showed the sampler works when evidence has
repeat readings. That points at something the first draft of this section did
not say clearly enough. The five scored steps, structural review, electrical
review, third-party review, rough-in inspection and the same-day counter, are
each asked about **once** per authority by a single survey column. There is no
second instrument for any of them and no anchor on any of them. The 883
repeated readings in the evidence sit on the online-permitting steps, and the
156 calibration cells sit on the final inspection, which every authority
performs. So for exactly the cells the held-out test scores, presence and
detection are confounded by construction: a "No" in the survey is
indistinguishable from a missed mention, no matter how long the chain runs.
The test could not have passed with a perfect sampler. That is a property of
the corpus and it is the first thing to check before this design is used on
any other family.

### Why it failed, and why more compute will not fix it

Running longer was the obvious move, so I measured whether it would help before
spending the night on it. The same design at growing size, with the draw budget
set by what the sampler's retained arrays will fit in memory:

| authorities | total draws | worst R-hat | min ESS | ESS per 1,000 draws |
|---:|---:|---:|---:|---:|
| 30 | 24,000 | 1.46 | 7.9 | 0.33 |
| 60 | 20,000 | 2.16 | 5.2 | 0.26 |
| 120 | 12,000 | 3.07 | 4.5 | 0.38 |
| 240 | 6,000 | 3.33 | 4.4 | 0.73 |
| 440 | 3,200 | 3.95 | 4.3 | 1.34 |

**Effective sample size does not grow with draws.** Twenty-four thousand draws
at 30 authorities buys an effective sample of eight. That is not a slow
sampler, and no overnight run would have rescued it. It also fails at 30 and 60
authorities, which are concealed carry's and CalFresh's sizes, so this is not
about solar being large.

I suspected the presence logit's unconstrained overall level, since
`alpha[s] + u[j]` lets a constant move freely between the two halves. Measured,
the correlation between the mean step effect and the mean jurisdiction effect
is 0.05, -0.10, -0.22, 0.28, 0.38 across the five sizes: small, and changing
sign. That hypothesis is not supported and I have said so rather than let a
plausible story stand in for a measurement.

What the evidence does point at is the width of the elliptical slice blocks.
Measuring how far the whitened hierarchy travels between retained draws, the
distance falls monotonically as the table grows, in both directions: from 0.317
at 10 steps and 30 authorities to 0.103 at 50 steps and 30 authorities, and on
to 0.060 at 50 steps and 120 authorities. The chains never freeze; they creep.
That is what a slice update looks like when it proposes rotating a whole block
at once and must stay consistent with every binary observation the block
touches.

The full argument, the numbers, and what I deliberately did not change, are in
`docs/2026-09-21-occupancy-sampler-note-for-codex.md`. The module is Codex's,
they have a review packet open against it, and a sampler change made underneath
them overnight would have been worse than the bug.

## 3. What stringency costs in time

`runs/process_structure_20260921/solar_phase5`. This is the Stage A cross the
solar leg has owed since the timing fit, and it does not depend on the
occupancy model.

The fitted timing model gives a posterior for each authority's own speed once
year, phase, size class and technology are removed. Regressing that posterior
on what the authority demands, once per draw so the timing model's uncertainty
carries through:

| requirement | 259 authorities | 45 authorities |
|---|---|---|
| structural review required | **+13.8%** [+9.4, +18.3] | +3.3% [-6.3, +14.1] |
| same-day counter available | **-10.5%** [-13.9, -7.0] | **-15.5%** [-22.0, -8.4] |
| rough-in inspection required | +2.5% [-4.8, +10.0] | **+15.3%** [+0.1, +32.1] |
| online instant permitting | -0.5% [-4.7, +4.0] | -6.0% [-14.8, +3.9] |
| third-party review | not in this specification | **-9.8%** [-18.1, -0.3] |
| log inspections required | not in this specification | +0.9% [-13.3, +17.4] |

Two specifications because requiring every question to be answered leaves only
45 authorities. The signs agree across both on every shared term, but only the
same-day counter excludes zero in both, and the two disagree on which of
structural review and rough-in inspection carries the effect. The 259-authority
result is the one to lead with: it has 5.8 times the sample and does not
condition on having answered the two questions most authorities skipped.

Read plainly: **authorities that require structural review are about 14 percent
slower, and authorities offering a same-day counter are about 10 percent
faster.** Neither is causal. One statistical caveat added on audit: the outcome
is a hierarchical random effect, already shrunk toward zero by the timing
model, so these coefficients are attenuated relative to what an unshrunk
authority effect would show. The direction and the ordering survive that; the
magnitudes are lower bounds in the usual sense. An authority that staffs a counter differs from one
that does not in ways no column here records.

The more important number is how little this explains. Requirements account for
**7 percent** of the variance in authority speed in the wide-sample
specification, 19 percent in the small one. The 2.39-fold spread between the
tenth and ninetieth percentile authority found in the timing fit is
overwhelmingly *not* explained by what those authorities demand on paper. What
makes one building department slow than another is mostly not in its
requirements.

## 4. Where the burden sits

`runs/process_structure_20260921/solar_phase5/burden_table.json` and its CSV.

**Corrected on audit, 21 September morning.** The first version of this section
multiplied the inspection phase time by the mean number of inspections
required and reported inspection at 76 percent of measured time. That
double-counted: the source's inspection clock runs from installation complete
to the *last* completed inspection, so it already spans every required
inspection. The inspection count is a stringency feature and is no longer
applied to the clock. The first version also failed to carry a warning the
panel itself records: the source's inspection endpoint is ambiguous, its
published definition being self-referential and its quartile sheet giving a
different one. Both are fixed below and the earlier numbers are superseded.

Time in solar permitting is measured as a phase clock, not a step clock: the
source times a phase from its start to its end and nothing times the steps
inside it. Splitting a phase across its steps would invent numbers, so the
table reports phase time against every step in the phase and says so. Do not
add steps within a phase together.

| phase | median business days | share of measured time | endpoint | steps | applicant actions |
|---|---:|---:|---|---:|---:|
| permit review | 9.1 | 29% | clear | 13 | 5 |
| inspection | 22.0 | 71% | ambiguous in source | 5 | 1 |

**The post-installation interval, from installation complete to the last
completed inspection, carries about seven tenths of the measured elapsed time,
and permit review about three tenths.** That still points away from where the
reform effort has gone. Government Code 65850.5 and 65850.52, SolarAPP+,
instant permitting and the three-day permit target all act on the phase that
accounts for under a third of the clock.

Read the larger share carefully, because it is not "the agency's inspection
takes 22 days". The interval starts when the installer declares the system
complete and ends at the last passed inspection. It contains the installer's
own scheduling delay, any wait for an inspection slot, the inspection, any
failed inspection and its return visit, and whatever the ambiguous endpoint
adds or removes. Which of those the applicant experiences as agency delay is
not separable from this source. Among the 159 authorities that answer the
question, the mean number of inspections required is 1.30, and the only
statutory lever aimed at this phase is the sentence in 65850.5 saying only one
inspection shall be required.

Two limits on the share, both real. It covers the two authority phases only:
the timing model fitted no coefficient for utility pre-install approval or
permission-to-operate, so the utility side of the process is absent from the
denominator rather than shown to be small. And permit resubmission is inside
the permit clock by the source's definition, which measures from the original
submittal, so the permit phase's round count is unmeasured rather than one.

Cost is one number and it belongs to one step. 384 authorities report a median
permit cost, median $371, paid by the applicant to the authority, normally
through the installer. No solar source records applicant effort in hours or
the cost of an engineer's stamp, so both are absent here rather than assumed
away.

Presence in this table comes from direct evidence, not from the occupancy
posterior, because that posterior failed its gate. The field `presence_basis`
in the JSON records which was used. Read as the fraction of readings that
detected a step, it makes no correction for a source staying silent about a
step that is present, which is the correction the occupancy model exists to
supply and has not yet earned the right to.

## 5. Open

- **Phase 3 is blocked**, not skipped. There is no occupancy posterior to
  report for any family until the sampler mixes. When it does, rebuild the
  burden table: it reads `presence_basis` and will switch from observed
  fractions to the posterior automatically.
- The utility side of the clock. The timing model fitted coefficients for the
  permit and inspection phases only, so pre-install approval and
  permission-to-operate are outside the burden share's denominator.
- Applicant effort in hours and the cost of an engineer's stamp. No solar
  source records either.
- The literature check, which still gates any write-up beyond this repository.

## 6. Reproducing this

    python3 -m pipeline.procbench.process_structure.solar_phase1
    python3 -m pipeline.procbench.process_structure.solar_phase2          # fails its gate, by design preserved
    python3 -m pipeline.procbench.process_structure.solar_phase2_scaling
    python3 -m pipeline.procbench.process_structure.solar_occupancy_mixing
    python3 -m pipeline.procbench.process_structure.solar_burden

Tests: `python3 -m pytest tests/test_solar_process_structure.py -q`, 31 passing.
Full suite at this checkpoint: 2,053 passing.
