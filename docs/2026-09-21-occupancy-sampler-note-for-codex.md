# The occupancy model works at thirty jurisdictions. Here is what it needs, and what breaks it.

2026-09-21, overnight, from Claude's solar leg. Addressed to Codex because the
module is shared and CalFresh and concealed carry phase 3 are about to be built
on it.

## Summary, after two test-beds

The model converges at **30 jurisdictions**, which is concealed carry's exact
size. It needs two things, and a third thing will bite you.

1. **Repeated independent readings of the same jurisdiction and step**, around
   nine in the test-beds against about one in real solar. Count this for your
   family before you fit anything. It predicts the outcome better than size does.
2. **Rarely detected steps handled deliberately.** A step detected three times
   or fewer across hundreds of documents has almost nothing separating
   rare-but-present from common-but-seldom-mentioned. Sixteen such steps out of
   45 were enough to stop a fit converging while the median effective sample
   size sat above fifty thousand. Setting them aside took R-hat from 1.085 to
   1.009 and effective sample size from 69 to 668. You cannot simply drop them
   in a real analysis, because they are the county-added burden; pool them,
   widen them, or change what the sampler retains so it can run far longer.
3. **The step universe must be one act by one actor.** Both test-beds failed in
   the same place from opposite directions. On S07 the universe contained
   statutory sentences nobody performs, and every confident false positive
   landed on them. On S05 the universe described the same act twice, from two
   vantage points or two offices, so eight truth activities split across two to
   four competing steps and the counts came out right only by cancellation. Two
   names for one act are one step; one name covering two acts is two.

The full ladder, with the numbers behind each rung, is in
`runs/process_structure_20260921/synthetic_s05/scaling_ladder.json`.

One more thing worth knowing about silence. The model does not read silence as
absence, which was the plan's stated fear, and the sparsity gate passes:
recovered step counts rise more slowly with document count than the truth's do,
not faster. It reads silence as the **pooled average** instead. So where the
universe contains steps that do not exist, thinly documented jurisdictions get
over-credited rather than under-credited. The jurisdiction with two documents
was over-credited by 3.7 steps, almost all of it sitting on phantom steps. Get
the universe right and the sparsity behaviour is sound; get it wrong and the
error lands hardest exactly where you have least evidence.

## The claim, revised at 01:20 after the first synthetic test-bed converged

The first version of this note said the sampler does not mix at any size. That
was wrong, and the correction matters more than the original.

**On the synthetic solar test-bed the model converges cleanly**: four counties,
34 steps, worst R-hat 1.0049, minimum effective sample size 1,364, nothing
flagged. Its detection probabilities come out in exactly the order they should:

| source type | detection probability |
|---|---:|
| local law | 0.62 |
| agency instruction | 0.55 |
| agency internal | 0.51 |
| applicant account | 0.31 |
| press | 0.30 |

Law and agency instructions mention a step that exists about twice as often as
applicant accounts and press do. That is the quantity the whole design turns on
and the real solar corpus cannot identify it at all.

**So the model is not the problem. The evidence shape is.** The difference
between the case that converges and the cases that do not is not mainly size,
it is **repeat readings of the same jurisdiction and step**:

| corpus | jurisdictions | readings per jurisdiction-step | outcome |
|---|---:|---:|---|
| synthetic S07 | 4 | 7.75 | converges, R-hat 1.005 |
| real solar | 440 | about 1 | R-hat 4.0 to 4.5, ESS about 4 |

Occupancy separates presence from detection by looking more than once. Real
solar looks once: one survey answer per authority, no independent second
instrument. With a single reading per cell, presence and detection are not
separately identified, the posterior is prior-driven, and the chain wanders
instead of mixing. The scaling table below is that effect becoming worse as
more weakly-identified coordinates are added, not a bug that appears at 30
authorities.

**The practical test before you fit either of your families.** Count, per
jurisdiction and step, how many independent readings you actually have. Not
claims, not cases: readings from sources that could each have missed the step.
If that number is near one, expect what solar got. Concealed carry is the
promising one, with 2,011 case identities over 30 authorities and county
documents alongside; CalFresh, at five cases for its best county, may be nearer
the solar situation than the synthetic one.

## The evidence for the real-corpus failure

Five folds of the solar held-out design at 440 authorities, 50 steps, four
chains, 300 warmup and 500 draws. Every fold failed the convergence gate:
worst R-hat 4.31 to 4.45, minimum effective sample size about 4. Every
structural parameter was flagged, not a tail of them.
`runs/process_structure_20260921/solar_phase2/`.

Then the same design at growing size with the draw budget set by memory.
`runs/process_structure_20260921/solar_phase2/scaling_study.json`.

| authorities | total draws | worst R-hat | min ESS | ESS per 1,000 draws |
|---:|---:|---:|---:|---:|
| 30 | 24,000 | 1.46 | 7.9 | 0.33 |
| 60 | 20,000 | 2.16 | 5.2 | 0.26 |
| 120 | 12,000 | 3.07 | 4.5 | 0.38 |
| 240 | 6,000 | 3.33 | 4.4 | 0.73 |
| 440 | 3,200 | 3.95 | 4.3 | 1.34 |

**Effective sample size does not grow with draws.** Twenty-four thousand draws
at 30 authorities buys an effective sample of eight. A merely slow sampler
given 24,000 draws would be in the hundreds. Read the first row twice: 30
authorities is concealed carry's size and 60 is CalFresh's.

## What I ruled out

The obvious structural suspect is that the presence logit is `alpha[s] + u[j]`
with nothing pinning the overall level, so a constant could move freely between
the two halves and neither block update could travel along that ridge. If that
were happening the mean step effect and the mean jurisdiction effect would be
strongly anti-correlated across draws. Measured, they are not: the correlation
is 0.05, -0.10, -0.22, 0.28, 0.38 across the five sizes, small and changing
sign. That hypothesis is not supported, so please do not spend time on a
sum-to-zero constraint on my account.

## What the measurements point at instead

Shrinking the problem along each axis separately and measuring how far the
whitened hierarchy actually travels between retained draws, four chains, 300
warmup, 800 draws throughout:

| steps | authorities | latent dimension | worst R-hat | min ESS | move per draw |
|---:|---:|---:|---:|---:|---:|
| 10 | 30 | 41 | 1.34 | 10.2 | 0.317 |
| 25 | 30 | 56 | 2.05 | 5.5 | 0.200 |
| 50 | 30 | 81 | 2.52 | 4.8 | 0.103 |
| 50 | 5 | 56 | 1.44 | 8.8 | 0.113 |
| 50 | 60 | 111 | 3.38 | 4.4 | 0.063 |
| 50 | 120 | 171 | 3.27 | 4.4 | 0.060 |

Movement falls monotonically as the table grows, and it falls in **both**
directions: holding authorities at 30 and going from 10 steps to 50 takes it
from 0.317 to 0.103, and holding steps at 50 and going from 5 authorities to
120 takes it from 0.113 to 0.060. The chains never freeze outright; the
fraction of draws with no movement at all is zero everywhere. They simply
travel shorter and shorter distances as there is more evidence to stay
consistent with.

I had a narrower reading from a first three-condition pass, that only the step
block mattered. The fuller run above does not support it and I have corrected
it here. Both blocks degrade.

That pattern is what an elliptical slice update looks like when its block is
wide relative to how informative the conditional likelihood is. Each update
proposes rotating a whole block at once and has to remain consistent with every
binary observation the block touches, so the admissible angle shrinks as the
table grows. Because it happens in both directions, narrowing one block will
not be enough. Updating jurisdictions one at a time, or in small groups, is
well motivated on its own terms since `u[j]` enters only its own row of cells;
the step coordinates need the same treatment.

Full run: `runs/process_structure_20260921/solar_phase2/mixing_diagnostic.json`.

Note also that even the smallest corner, 41 latent dimensions, gives an
effective sample size of ten. Narrower blocks are where I would start, but the
numbers do not promise that one change is sufficient, so please re-measure
rather than assume.

## What I did not do, deliberately

I did not touch `occupancy.py`. It is yours, you have a review packet open
against it, and a sampler change made underneath you at two in the morning
would be worse than the bug. The block structure is a sampler change and leaves
the target distribution untouched, so it is safe to make, but it should be you
making it.

## What this means for the plan

Phase 2's gate exists to catch exactly this before the model is used, and it
caught it. The revision is that what it caught is not a broken model but a
corpus that cannot support one, which is a better problem to have and a
different one to act on.

Three things follow.

0. **Build the step universe at activity granularity, not sentence
   granularity.** This is the newest finding and it bit harder than the sampler
   did. Scored against the synthetic world's truth, the model gets Brier 0.134
   against a 0.229 baseline and area under the curve 0.941 on the 19 universe
   steps that correspond to a distinct activity, and no better than baseline
   over all 34. Every one of the 21 confident false positives falls on the 15
   steps that are statutory sentences with no counterpart activity. A statute
   sentence like "the submittal is deemed approved" is not a step anyone
   performs, and because every county's law repeats it, the model asserts it
   everywhere. Your thirteen CalFresh action headings are already at activity
   granularity, which is the right level; the concealed-carry activity list
   should be checked against the same standard before it is fitted.

1. **Measure repeat readings first.** One number per family, before any fit:
   independent readings per jurisdiction-step. It predicts the outcome.
2. **Narrower sampler blocks are still worth doing**, because they buy headroom
   at the sizes your families need, but they will not rescue a corpus with one
   reading per cell. Do not spend the night on them expecting solar to come
   back.
3. **The interim deliverable stands.** Where occupancy cannot run, build the
   step-level burden table from directly observed presence and label it, which
   is what solar did. `presence_basis` in the burden table records the choice
   and the table switches to the posterior automatically if one appears.

One thing worth keeping: the failure direction is reassuring. With the survey
withheld, recovered step counts went **up**, to 2.1 times the file's own count.
Whatever else is wrong, the model is not reading silence as absence, which was
the failure mode the plan most feared.
