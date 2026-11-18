# The synthetic test-bed, and what it proves the real corpus cannot

2026-09-21, overnight. Claude's Y1: a solar test-bed with ground truth, built
to answer the one question the real corpus cannot, which is whether the
occupancy model works at all.

## Why this was needed

Real solar failed. The five-fold held-out fit at 440 authorities never came
close to converging, and the burden table had to fall back to directly observed
presence. Two very different explanations fit that failure: the model is wrong,
or the evidence cannot support it. Telling them apart needs a corpus where the
answer is known, which is what a synthetic world is for.

## What was built

Statute S07 in world W2_DEV_001, implemented by four counties, with 31
rendered documents already in the world. One agent read the statute and the
bill analysis and produced a 19-step vocabulary. Four more agents, one per county
and each blind to the others and to all truth, read their county's documents in
full and reported which steps each document mentions and which steps their
county performs that the statute never names.

| | |
|---|---:|
| counties | 4 |
| documents read | 31 |
| steps in the universe | 34 |
| reading opportunities | 1,054 |
| positive detections | 199 |
| **repeat readings per county-step** | **7.75** |

That last row is the whole point. Real solar has about one reading per
authority-step: a single survey answer, with no second instrument that could
have missed the step. Here every county is read by six to nine documents of
four or five different kinds.

Counties added steps the statute never mentions, which is the mechanism the
design exists to catch. Fire authority sign-off, registering an account before
filing, counter screening, a staff reviewer queue, correction-and-resubmittal
loops, publishing a permit register, a rapid-shutdown placard. Two are worth
naming because they cost applicants real time and appear in no official
document: C12's counter screen and fire marshal sign-off show up only in
applicant threads, running one to eighteen and four to twenty-four days.

Where the agents named the same step differently, only plain synonyms were
merged, three of them. Two near-misses were deliberately left apart, with
reasons recorded, because merging them would have manufactured exactly the
cross-county agreement the model is trying to estimate.

## The model converges here

| | |
|---|---:|
| worst R-hat | 1.0049 |
| minimum effective sample size | 1364 |
| structural parameters flagged | 0 |
| numerically usable | True |

It took four chains, 10,000 warmup and 30,000 draws. A first run at 4,000 and
12,000 landed at R-hat 1.0126, just outside the gate, and is kept beside the
final one.

And the detection probabilities come out in the order they should:

| source type | probability it mentions a step that is present |
|---|---:|
| local law | 0.62 |
| agency instruction | 0.55 |
| agency internal | 0.51 |
| applicant account | 0.31 |
| press | 0.30 |

An ordinance mentions a step that exists about twice as often as a forum post
does. Nothing told the model that; it is estimated from the pattern of who
mentions what. This is the parameter the entire three-layer design rests on,
and the real solar corpus cannot identify it at all.

Posterior expected steps per county: C03 13.2, C06 14.2, C09 12.2, C12 14.8, out of a universe of 34.

## Scored against the world's truth

Scoring was done by a separate agent so that this session stayed truth-blind.
It read `benchmark/synth/worlds/W2_DEV_001/truth/` and recorded that it did, as
the project's rule for evaluation utilities requires.

**Reading 31 documents recovers 94 percent of the process.** Forty-nine of the
52 true activities across the four counties appear in the universe. The three
that do not are back-office: configuring the platform's review rules, and
routing a case to a reviewer queue. No document describes them, so no reader
could have found them. That is the floor on what documents can tell you, and it
is higher than I expected.

Presence, on the 19 universe steps that correspond to a distinct truth activity:

| | model | base-rate baseline |
|---|---:|---:|
| Brier | **0.134** | 0.229 |
| log loss | 0.526 | 0.651 |
| area under curve | **0.941** | — |

That is a 42 percent Brier skill over knowing nothing, on 76 cells. The model
ranks well.

Two honesty notes on that table, both from the scorer rather than from me.
**The matched-19 restriction was chosen with truth in hand**, so the all-34
figure below is the honest end-to-end number and this one is the diagnosis.
And **the four counties are not independent tests**: C12 received no new
readings in the repair yet its register step still moved from 0.60 to 0.98
through cross-county pooling, which is the hierarchy working as designed and
also a reason not to read four counties as four replications.

On all 34 universe steps the picture changes: Brier 0.237 against a baseline of
0.230, which is no better than knowing nothing, with area under the curve 0.81.
The whole gap sits in one place. Fifteen of the 34 universe steps match no
distinct truth activity, and **all 21 confident false positives fall on those
fifteen**. They are statutory sentences: deemed approval, proceeding with
installation, review under other law, the structural screen. The statute
mentions them as things that happen; the truth's activity list does not treat
them as separate activities.

So the binding constraint is not the sampler and not the evidence. It is the
**granularity of the step universe**. Building it from statutory sentences
produces steps finer than the process actually has, and the model then
confidently asserts them everywhere because every county's law repeats the
statute. This is the most transferable lesson of the night: build the universe
at the granularity of activities someone performs, not of sentences someone
wrote.

Step counts are over-predicted in all four counties, 63.1 expected against 52
true, with C06 and C12 outside the 90 percent interval. Same cause.

### One defect of mine, found by the scoring

The first scoring run came back worse than baseline everywhere, and the reason
was mine, not the model's. Three of the four county extractions had recorded
their county-specific steps only under `new_steps` and never in the detection
table, so 19 steps entered the universe with no positive reading anywhere and
the posterior pushed them to zero in the very counties that reported them.
Promoting those entries into the detection table, which is what they always
were, moved the matched-19 area under the curve from 0.797 to 0.941 and halved
the suppressed set: of 18 genuinely present activities sitting below
probability 0.20, nine crossed it, seven crossed 0.50, and nine are still
below. The lift tracked the strength of the promoted source almost perfectly:
a local-law reading moved a cell by 0.65 on average, an agency instruction by
0.18, and an applicant account by 0.017. Two C09 activities evidenced only by a
forum post did not move at all, which is the detection model doing exactly what
it should and is also a warning about how little a single weak reading buys.
The 21 confident false positives did not move at all; the largest change among
them was 0.01. Both the pre-repair fit and its score are kept beside the
repaired ones.

This is the argument for having a test-bed at all. On real solar that defect
would have been invisible; the numbers would simply have been worse and nobody
could have said why.

## What this settles

The occupancy model is not broken. It converges, and it recovers a sensible
detection ordering, when the evidence has repeat readings. The real solar
failure is a property of the corpus, not of the model: one survey answer per
authority cannot separate a step that is absent from a step nobody wrote down.

The practical consequence for the other two families is a single number to
check before fitting: independent readings per jurisdiction-step. Concealed
carry, with 2,011 case identities across 30 authorities plus county documents,
looks promising. CalFresh, with five cases for its best county, may be closer
to solar's position than to this one.

Full argument: `docs/2026-09-21-occupancy-sampler-note-for-codex.md`.

# Part two: S05, thirty jurisdictions

S07 showed the model works. It could not show whether it works at the size the
real families need. Concealed carry has 30 authorities and CalFresh 58, and
S07 had four. Statute S05 in the same world has 266 rendered documents across
30 jurisdictions, from 2 documents to 12, so it answers both the scale question
and the sparsity question the plan set as a gate.

The CalFresh synthetic pilot was examined for this and rejected before any
render budget was spent. Its process documents assert the same twelve facts in
every one of its twelve jurisdictions, so which steps exist does not vary and
occupancy would have had nothing to estimate. That world varies timing and
repeat rates, which is Phase 4 evidence, not Phase 2.

## Building it

Thirty agents, one per jurisdiction, each blind to the others and to all truth,
read their jurisdiction's documents in full against a nine-step vocabulary
built from the statute. The vocabulary was written at activity granularity
this time, with nine legal consequences and six pointers to other law
deliberately excluded, which is the lesson from S07 applied.

| | |
|---|---:|
| jurisdictions | 30 |
| documents read | 266 |
| steps after reconciliation | 45 |
| reading opportunities | 11,970 |
| positive detections | 1,241 |
| repeat readings per jurisdiction-step | 8.87 |

Thirty independent extractions produced 87 distinct labels for a nine-step
statute. Merging plain synonyms brought that to 45. Every near-miss kept apart
is recorded with its reason, and one of them earned its keep: a single
jurisdiction renews annually where the rest self-certify every two years, and
merging those would have hidden a doubling of a recurring burden.

## The scaling ladder, which is the result

| corpus | jurisdictions | steps | readings per cell | draws | R-hat | min ESS | usable |
|---|---:|---:|---:|---:|---:|---:|:--|
| real solar | 440 | 50 | 1.0 | 500 | 4.33 | 4 | no |
| synthetic S07 | 4 | 34 | 7.8 | 30,000 | 1.0067 | 1,320 | **yes** |
| synthetic S05, all steps | 30 | 45 | 8.9 | 20,000 | 1.0848 | 69 | no |
| S05, steps seen 4+ times | 30 | 29 | 8.9 | 20,000 | 1.0158 | 293 | no |
| S05, steps seen 4+ times | 30 | 29 | 8.9 | 34,000 | 1.0106 | 415 | no |
| S05, steps seen 4+ times | 30 | 29 | 8.9 | 52,000 | **1.0088** | **668** | **yes** |

**The model converges at thirty jurisdictions.** That is concealed carry's
exact size, and it is the single most useful thing to know before Phase 3.

Two conditions have to hold. The evidence needs repeated independent readings
of the same jurisdiction and step, about nine here against roughly one in real
solar. And rarely detected steps have to be handled: 16 of the 45 steps are
detected three times or fewer across 266 documents, and a step seen once has
almost nothing separating rare-but-present from common-but-seldom-mentioned.
Its prevalence and its detection probability trade off against each other, and
a handful of such coordinates is enough to stop the whole fit converging while
the median effective sample size sits above fifty thousand.

Setting those 16 aside is a **diagnosis, not a proposal**. They are precisely
the county-added burden the project exists to measure: the fire clearance, the
counter screen, the notarised affidavit. A real fit needs them in, which means
pooling rare steps under a shared prevalence, accepting wide intervals on them,
or a sampler that does not retain one draw per jurisdiction and step and can
therefore simply run far longer. At 45 steps the retained arrays alone would be
about 1.4 gigabytes, which is why draws cannot just be increased.

## Scored against truth

Again by a separate agent, which read 61 development-truth files and recorded
that it did. **Everything in this section is a diagnostic**: it scores the
45-step fit, which failed its gate.

**Universe coverage is perfect. Zero of 24 canonical truth activities were
missed**, across all 343 activity instances. Reading 266 documents recovered
every activity the world contains. S07 managed 94 percent; thirty jurisdictions
and richer document sets close the gap entirely.

The defect runs the other way. Fourteen of the 45 steps have no truth
counterpart at all, and eleven more restate an activity another step already
covers, so eight truth activities end up split across two to four competing
steps. The universe is not missing the process; it is describing it too many
times.

| | model | base-rate baseline |
|---|---:|---:|
| all 45 steps, Brier | 0.293 | 0.246 |
| all 45 steps, area under curve | 0.733 | — |
| 20 one-to-one steps, Brier | 0.238 | 0.245 |
| 20 one-to-one steps, area under curve | 0.890 | — |

Ranking within a jurisdiction is good. Calibration is not: 314 of the 960 cells
predicted below 0.2 are actually present, at a mean prediction of 0.011. The
counts come out roughly right only by cancellation, short about five real
activities per jurisdiction and offset by about 2.4 expected steps on
activities that do not exist. The misses concentrate in staff-only back-office
work, mean posterior 0.40 against 0.74 for applicant-facing steps, which is the
model correctly reflecting that nobody writes those down.

## The sparsity gate

The plan's gate was that the recovered step count must not fall with document
sparsity faster than the truth's own count does. **It passes.** Truth rises
0.1025 activities per document; recovery rises 0.0242 over all steps and 0.0901
over the matched ones, so recovery is flatter than truth, not steeper.

But the opposite failure is present and the plan did not anticipate it. Thin
jurisdictions are over-credited: mean error of +0.09 steps at six documents or
fewer against −0.60 at ten or more. The worst case is the jurisdiction with two
documents, over-credited by 3.7 steps, and 3.9 of its expected steps sit on
steps with no truth counterpart that its own extraction says it never mentions.
So the model does not read silence as absence. It reads silence as the pooled
average, and where the universe contains phantom steps, that average is wrong
in the generous direction.

One correction to something I said earlier in the night: that two-document
jurisdiction has the fifth-highest expected step count, not the highest. I
asserted the stronger version from a partial view and the scorer caught it.

## Three merge calls that truth says were wrong

The scorer reviewed the reconciliation against truth and found three deliberate
non-merges to be mistakes: counter screening really is the completeness
determination, the certificate really is the decision, and depositing the fee
really is the reconciliation. One merge is missing: the registry record and the
permit register are one activity.

These are **not** applied. Correcting a universe using truth and then scoring
it against the same truth is not a blind test, and the blind result is the one
that counts. They are recorded because they transfer: the recurring error is
treating two descriptions of one act, from two vantage points or two offices,
as two steps. That is the same failure as S07's statutory-sentence steps, seen
from the other side, and it is worth a rule. A step is one act by one actor.
Two names for it are one step; one name covering two acts is two.

## Two bugs found here

The summary reported the S07 alias map regardless of which statute was built,
so its own provenance block named steps that do not exist in S05. Worse, the
two alias maps were being merged, and an S07 entry silently renamed an S05 step
that four jurisdictions had named independently. Alias maps are now strictly
per statute. Step counts, readings and detections are unchanged by the repair,
so the fits above stand; only a label was wrong.

## Reproducing

    python3 -m pipeline.procbench.process_structure.synthetic_evidence --statute S07
    python3 -m pipeline.procbench.process_structure.synthetic_fit --statute S07 --chains 4 --warmup 10000 --draws 30000

    python3 -m pipeline.procbench.process_structure.synthetic_evidence --statute S05
    python3 -m pipeline.procbench.process_structure.synthetic_fit --statute S05 --chains 4 --warmup 8000 --draws 20000
    python3 -m pipeline.procbench.process_structure.synthetic_s05_rare_step_test --chains 4 --warmup 16000 --draws 52000

Artefacts in `runs/process_structure_20260921/synthetic_solar/` and
`.../synthetic_s05/`, with the ladder in `synthetic_s05/scaling_ladder.json`.
