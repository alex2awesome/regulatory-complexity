# Morning audit: both legs, what they establish, and what evidence to collect next

2026-09-21, morning. Alex asked for an audit of everything Claude did
overnight, everything Codex did, and the next steps, with recommendations on
the kind of evidence to collect. Written by Claude. Every number here was
re-derived from files this morning, not carried over from the night's
write-ups, and three of the night's own claims were corrected in the process.

## The short version

Both legs reached the same conclusion from opposite directions, and neither
write-up says it as plainly as the files do. **The occupancy model is sound
and now converges at thirty jurisdictions with every step included. The
corpora are the constraint.** Real solar has one reading per authority-step;
real CalFresh has no reading at all in 70 percent of its county-action cells
and 48 of its 58 counties share a single indistinguishable posterior. The
synthetic test-beds, with about nine independent readings per cell, are the
only place a step-presence posterior has been earned. What to collect next
follows from that directly, and it is not more of what has been collected.

## 1. Claude's leg, audited

### What stands

- **Solar phase 1.** 440 authorities, 50 steps, 4,098 reading opportunities,
  859 anchors. Contract-validated, source-bound, reproducible. The decision to
  exclude forum accounts, because their authority attribution is a weight
  distribution rather than an identification, was right.
- **Solar phase 2 failure, preserved.** Five folds, R-hat 4.3 to 4.5. Kept as
  a result and removed from the retry loop.
- **The stringency cross.** Structural review about 14 percent slower, a
  same-day counter about 10 percent faster, on 259 authorities, with
  requirements explaining 7 percent of between-authority speed variance.
  Survives audit with one caveat added below.
- **S07 test-bed.** Four counties, 31 documents, converges at R-hat 1.0067.
  Detection probabilities ordered as they should be. Universe recall 94
  percent against truth; area under the curve 0.94 on steps that map to a
  distinct activity.
- **S05 test-bed.** Thirty jurisdictions, 266 documents, 87 raw labels
  reconciled to 45. Universe recall 100 percent against truth. The plan's
  sparsity gate passes.
- **Process.** Depth-first as instructed. The in-flight marker scheme
  prevented duplicate extractions once it existed. Thirty-six subagents,
  roughly 3.3 million subagent tokens.

### Corrected on this audit

1. **The burden table double-counted inspections.** It multiplied the
   inspection phase time by the mean number of inspections required, 1.30.
   The source's inspection clock already runs to the *last* completed
   inspection, so it spans every required one. Corrected share: **71 percent
   post-installation, 29 percent permit review**, not 76 and 24. The
   qualitative claim survives; the number was wrong.
2. **The burden table ignored a warning the panel carries.** The source's
   inspection endpoint is flagged in the panel as ambiguous and "must not be
   silently resolved". I resolved it silently. It is now carried on the row.
   The post-installation interval also contains the installer's own
   scheduling delay, and the write-up now says so instead of implying the
   agency's inspection takes 22 days.
3. **The solar failure diagnosis was incomplete.** The scored steps are each
   asked about once per authority, with no second instrument and no anchor.
   For exactly those cells presence and detection were confounded by
   construction. The held-out test could not have passed with a perfect
   sampler. The night's write-up blamed the sampler; the sharper reason is the
   corpus, and it is now recorded.
4. **The scaling ladder was measured on the old sampler.** Codex added a
   partially collapsed hierarchy update and block splitting at 05:07, after
   every rung was run. Re-measured this morning, see section 3.
5. **Stringency coefficients are attenuated.** The outcome is a shrunk random
   effect, so the magnitudes are lower bounds. Added.

### Errors made and caught overnight, for the record

Three over-claims from partial evidence, each corrected by the next
measurement: that only the step block hurt mixing; that the sampler mixes at
no size; that the two-document jurisdiction had the highest step count. Two
evidence-assembly bugs caught by truth scoring rather than by me: county-added
steps that never reached the detection table, and a filename prefix that typed
forum threads as agency forms. One cross-statute alias contamination that
silently renamed an S05 step. One converged fit destroyed by a smoke test and
recomputed. Three reconciliation calls that truth says were wrong, recorded and
not applied. The pattern is worth naming: I state a conclusion one measurement
early, and the discipline that saved it each time was the next measurement.

## 2. Codex's leg, audited

A fresh-context agent audited the packets against the write-up
`2026-09-21-calfresh-process-results-and-next-decision.md`; its full report is
`runs/process_structure_20260921/CLAUDE_OVERNIGHT/audit_codex_calfresh.json`.
I checked the sampler changes and the closeout assessment myself.

### What stands, and it is substantial

- **Every headline number reproduces.** Brier 0.0607 baseline against
  0.0721 model, minimum effective sample size 1,023, the county count
  intervals, the 9.1 percent contraction, 174 administrative readings, 2,362
  tests. One rounding slip in R-hat, 1.00712 reported as 1.0072.
- **The held-out scoring is genuinely held out.** The eight scored accounts
  are disjoint from the 18 used to fit.
- **The identification argument is correct.** Participation times detection
  is what a forum likelihood sees, and more of the same evidence pins the
  product without separating the factors. This is the most important
  sentence in either leg's write-up.
- **The closeout assessment is rigorous.** Its table of what each evidence
  block identifies, and its seven reasons a unified posterior is not currently
  honest, are right. Its recommended artefact, a typed partial-identification
  report rather than another fit, is the correct call.
- **The sampler changes work.** Codex acted on my overnight note and added a
  partially collapsed hierarchy update and block splitting, both opt-in.
  Measured this morning on the S05 evidence that failed overnight, same
  budget, rare steps included:

| S05, all 45 steps, 30 jurisdictions | augmented | collapsed, blocks of 8 |
|---|---:|---:|
| worst R-hat | 1.0848 | **1.0052** |
| minimum effective sample size | 68 | 318 |
| flagged parameters | 52 | 2 |
| at 30,000 draws | not run | **1.0053, ESS 531, usable** |

### What the write-up does not say, and should

1. **The "58-county posterior" is a 10-county posterior.** 817 of 1,160
   county-action cells have no reading of any kind. Forty-eight counties have
   only three CF296 administrative readings, all positive, and share one
   posterior row: count means within 0.08 of each other, presence
   probabilities within 0.009. Their county effects contract 1.6 to 9.1
   percent from the prior. Convergence is a real achievement for 20 step
   locations, one scale and 10 county effects, and a formality for the other
   48 coordinates.
2. **The administrative evidence is tautological.** Every county receives
   applications, approves some and evaluates for expedited service, so those
   three readings pin three actions near 1.0 everywhere and halve the
   between-county scale without discriminating among counties. The
   receipt-implies-filing constraint then fixes filing at 0.9998 statewide by
   construction. The write-up presents this as evidence helping; it is
   evidence that could not have hurt.
3. **A simpler prior beat every later fit and is missing from the table.**
   The low-detection Beta(1,4) condition scored 0.0678 on the same 153 cells,
   better than every administrative and logical-support fit at 0.0721 to
   0.0727. All later work was built on the worse Beta(2,2) base.
4. **Two earlier held-out comparisons also lost to the pooled baseline**,
   0.295 against 0.211 and 0.147 against 0.119, and are not mentioned.
5. **The county contrasts are source-genre contrasts.** Alameda is three
   Reddit posts, Los Angeles a staff manual, Sacramento a public guide. The
   loss to the baseline is concentrated on the four known-county accounts,
   0.076 against 0.057, which is exactly what it looks like when
   county-specific structure learned from one to three posts does not
   generalise.
6. **The forum-only model read silence as absence.** Alameda's
   accept-and-date step sat at 0.05 before the administrative readings
   arrived. This is the failure the plan feared, and it appeared, and it was
   then masked by tautological evidence rather than resolved.
7. **52,570 of 73,700 July 2025 denials are procedural.** Seventy-one percent
   of denials are missed interviews and missing verification, not
   ineligibility. This is the closest thing to a headline burden finding in
   the CalFresh evidence and it is in a packet, not in the write-up.

### A note on scale

Codex's leg produced about 1,400 files and a 56,000-character
implementation record for a fitted result that rests on 18 forum accounts and
five documents. The mechanics are careful and the hedging is honest; the
denominators are enormous and the evidence is tiny. The night's most useful
Codex output is two pages of the closeout assessment and forty lines of
sampler change.

## 3. What the two legs establish together

| corpus | jurisdictions | readings per cell | sampler | R-hat | usable | scored against truth |
|---|---:|---:|---|---:|:--|---|
| real solar | 440 | 1.0 | augmented | 4.33 | no | scored steps confounded by construction |
| real CalFresh | 58, 10 informed | about 1 where any | collapsed | 1.007 | yes, for 10 | loses to pooled Beta baseline |
| synthetic S07 | 4 | 7.8 | augmented | 1.0067 | yes | recall 94%, AUC 0.94 matched |
| synthetic S05 | 30 | 8.9 | augmented | 1.0848 | no | recall 100%, AUC 0.89 matched |
| synthetic S05 | 30 | 8.9 | collapsed | 1.0053 | **yes** | same posterior, now earned |

Three things are now settled and one is not.

**Settled: the model works.** It converges at thirty jurisdictions with every
step in, recovers every true activity from documents, ranks steps within a
jurisdiction well, and estimates a detection ordering across source types
that nobody told it. The overnight worry that the sampler was broken is
resolved by Codex's change.

**Settled: the real corpora cannot support it yet.** The number that predicts
whether a fit means anything is independent readings per jurisdiction-step.
Solar has one. CalFresh has one where it has any and zero in 70 percent of
cells. Both real fits either fail or lose to a baseline that knows nothing,
and the closeout's identification argument says why more of the same
evidence will not change that.

**Settled: the step universe is the recurring defect.** S07 contained
statutory sentences nobody performs, and every confident false positive sat on
them. S05 described the same act twice from two offices, and the counts came
out right only by cancellation. CalFresh's 20 actions include agency-only
steps that applicant evidence can never detect. The rule that falls out: a
step is one act by one actor, and the universe should be built at that grain
before anything is fitted.

**Not settled: calibration.** Even the converged synthetic fits are
well-ranked and poorly calibrated. Presence probabilities are not yet numbers
to act on. Fixing that needs known presence and known absence, which is an
evidence question, not a modelling one.

## 4. What evidence to collect

The question the project needs answered is "which steps does jurisdiction j's
process contain, how demanding is each, and how often does it repeat". The
night established what the model needs to answer it. Three kinds of evidence,
in priority order.

### First: one agency-instruction document per jurisdiction, all three families

This is the single highest-leverage collection and it is cheap. A county's
own applicant guide or checklist is an independent instrument with a
different detection profile from a survey answer or a forum post. Adding one
per jurisdiction turns a one-reading corpus into a two-reading corpus, which
is the difference between confounded and identified. The synthetic worlds
showed agency instructions detect a present step about 50 percent of the
time and law about 60, so two such readings plus a forum reading is already
enough structure to start.

| family | what exists | what to add | source |
|---|---|---|---|
| CalFresh | 5 documents for 58 counties | one applicant guide or checklist per county, 58 documents | county human-services websites; CDSS county handbook as the statutory layer |
| solar | one survey answer per authority | the authority's own solar permit checklist, target 100 of 440 | city and county building-department websites |
| concealed carry | county documents for 30 authorities, not yet counted | count readings per authority-step first; fill gaps | sheriff's office pages |

Rule of thumb from the test-beds: the fit is usable somewhere between two
and nine independent readings per cell. Aim for three.

### Second: a small verified anchor set with explicit absence

Calibration cannot come from more detections; it needs cells whose answer is
known. For each family, ten to twenty jurisdictions whose full step inventory
is established directly, by reading the complete document set or by asking
the agency, with **explicit absence** recorded as carefully as presence. The
solar requirements matrix is the model for this: a survey that asks "is
structural review required" and records No is worth more than any number of
documents that fail to mention it. Codex's recommendation of "genuine absence
labels" is the same point. The synthetic worlds show what this buys: known
presence on one step pinned that step's detection probability, and nothing
else did.

### Third: case journeys with timestamps, and the CCW cases first

Repeats and participation are not identifiable from presence evidence. They
need cases: a county-linked journey with which steps occurred, which did not,
how many rounds, and when. Concealed carry already has 2,011 case identities
across 30 authorities. Mine those for per-step occurrence and repeat counts
before collecting anything new; that corpus was never fitted for structure
and it is the richest repeat evidence the project holds. For CalFresh, the
July 2025 CF296 procedural-denial share, 71 percent, is a repeat-and-rework
signal sitting in administrative data, and the question is whether any county
publishes it by reason.

### What not to collect

More forum threads of the kind already held. The closeout's identification
argument is decisive: a hundred more posts describing the same episode shape
pin the same product and separate nothing. The 945 CalFresh threads did not
produce a usable structure posterior and 945 more would not either. Forum
evidence is the applicant-only layer, valuable for finding steps no document
names, and it has done that job. It cannot do the calibration job.

## 5. Immediate actions, in order

1. **Adopt the collapsed sampler as the default.** It is Codex's module and
   the change is theirs to make. The augmented default is now known to fail
   at thirty jurisdictions where the collapsed update passes at the same
   budget.
2. **Count readings per jurisdiction-step for concealed carry** before
   fitting it. One script, one afternoon. It decides whether CCW is a
   synthetic-S05 situation or a real-solar one.
3. **Rebuild the CalFresh universe at one-act-one-actor grain** and split the
   report by informed versus uninformed county. Ten counties have evidence;
   say so in the first line.
4. **Collect the 58 CalFresh county guides.** This needs the no-new-retrieval
   work order reopened, and it is the reopening most worth making.
5. **Do not authorise the assumption-driven full model.** The closeout is
   right that it would encode choices as if learned. A typed partial result is
   the honest artefact until the evidence in section 4 exists.

## Where everything is

- This morning's corrections: `solar_phase5/burden_table.json` rebuilt,
  `2026-09-21-solar-process-structure-results.md` sections 2 to 4 corrected,
  `synthetic_s05/scaling_ladder.json` revised with the collapsed rung.
- The Codex audit in full: `CLAUDE_OVERNIGHT/audit_codex_calfresh.json`.
- The collapsed-sampler fits: `synthetic_s05/occupancy_fit_collapsed_b8.json`
  and `_30k.json`.
- Full test suite this morning: 2,119 on Claude's checkout before Codex's
  additions; Codex reports 2,362 with theirs.
