# Audit of the Bayesian model against the three burden priorities, 2026-09-19

Requested by Alex: a full audit of the Bayesian model, the data, what we are
likely to learn, and any mistakes, measured against the three things that
matter in order: how many steps the applicant goes through, how long it takes,
and what it costs. Plus whether the model can carry hierarchical priors over
agency speed or culture, in service of the larger goal of projecting how complex
a statute is and reading its decision model through its process model.

This audit reads three earlier ones and does not repeat them: the overnight
audit (2026-09-16), the machinery audit (2026-09-18) and the real-corpus gaps
note (2026-09-19). Everything here is new, and every number comes from a script
run today against saved posteriors, saved inputs and, for the first time,
benchmark truth.

**Isolation record.** This audit read `benchmark/synth/worlds/W2_DEV_001/truth`
(per-case event logs, log summaries and the world's knobs) to evaluate
posteriors that were saved on 2026-09-18, before any of this was written. That
is permitted for a development world and is recorded here, in
`docs/scoping/FINDINGS.jsonl`, and in the receipt
`runs/w2_v6_fits_20260918/truth_comparison.json` written by
`runs/w2_v6_fits_20260918/compare_to_truth.py`. No extractor, compiler, bridge
or fitter was touched, and this conversation must not be used to spawn a parser
or author a handoff.

## Verdict in one paragraph

The model's mathematics still hold up, and the earlier audits' verification of
that stands. What does not hold up is what the posteriors say. **V6 had never
been compared with the benchmark's known truth.** Doing so today shows that on
every synthetic programme the estimated process clock is 1.8 to 4.2 times too
long, and on four of five the truth lies outside the 90 percent interval, while
the estimated number of visits per case is close on four of five. The clock
error has three causes with known direction, all of them defaults rather than
bugs: forum posters are modelled as unselected although the benchmark plants
complaint selection and the real corpus has it too; operations are serial by
default although the truth overlaps them by 18 to 38 percent; and an operation
nobody reports falls to a seven-day prior whether it is a payment or a
technical review. The one real posterior, on solar permitting, was fitted to 92
forum reports alone because a compile rule discarded all 69 published
administrative medians, so its headline comparison against a published figure
compares a number the model never saw with an estimate from delay-selected
posters. Step counts look right for a reason that should worry us: the repeat
parameters sit at their prior, and the count is the inventory size plus a prior
repeat rate, not a measurement. Money is carried exactly where a schedule
publishes it, recovered to the dollar on both synthetic programmes, and then
never reported as a burden; the costs that dominate real cases have no channel.
The hierarchical agency effect the question asks for already exists in the
model with a fixed spread. The one design that exercised it, two fits of the
same four-step solar process across 12 and then 60 jurisdictions on
SolarTRACE's published medians, collected from sk3 today, identifies each
jurisdiction's total step time well (a 2.5 to 2.9 ratio between the slowest
and fastest deciles) and cannot separate the agency's share from the
operation's, because operations are keyed per programme and every operation
belongs to one agency; every hierarchy coordinate is flagged at R-hat up to
3.3. Data for a proper version are waiting: 574 concealed-carry forum cases
across 119 issuing authorities under one statute, and a synthetic world with
58 counties per statute and a planted county speed spread of 0.37 on the log
scale. With the current
evidence density the model learns one number per process, the overall scale of
a step, and leaves every structural quantity at its prior. It says so itself in
its identification report, and that report has been read correctly.

## 1. What the model is, in the terms that matter here

`bayes_trace_hierarchy.VisitHierarchy` samples, per resource channel, a log
duration for every operation as

    log d(op) = location + agency(actor of op) + task(task type of op) + operation(op)

with fixed prior spreads of 2, 1, 0.75 and 0.5 on the log scale
(`Config`, lines 40-56) and a prior median step of seven days. A case draws
per-operation noise with a learned spread (`case_log_sd`) plus a shared
per-case shift. Operations sit in blocks; blocks are serial; within a block the
order is a declared DAG, and `edges: null` means serial. One block per
programme may repeat under a hurdle-geometric law with a probit-normal prior on
the probability of any repeat and a Beta(2,3) prior on continuing. A route is
one inventory of operations; a route may carry alternative case paths that
toggle optional steps and are marginalised per case. Fees are fixed inputs on
operations and sum along the traversed path (`compact_visit_trace.py`, lines
34-43 and 461-469). Counts of visits, operations, agencies and additional
rounds are deterministic functions of the same trace. Reports enter through a
log-scale kernel with spread 0.25 for an individual and at least 0.5 for a
population summary, a per-source bias per channel, and a five percent
contamination mixture. Observations that no reading of the route can explain
carry a process-independent reference density and contribute a constant.

So the model already contains the three priorities: a visit count, a clock,
and a path fee total. And it contains a per-agency random effect. The question
is what the evidence lets each of them move from its prior, and whether the
defaults push the answer in a direction.

## 2. Mistakes found, ranked by consequence for the three priorities

### 2.1 Every synthetic clock is 1.8 to 4.2 times too long, and nobody had checked

`evaluate_burden.py` compares a posterior with truth, but it reads the V3/V4
posterior layout and has never been run on a V6 output. The eight V6 fits from
2026-09-18 were judged on convergence gates alone. Comparing them with the
development world's event logs, using the same clock the model estimates
(arrival to first decision) and the same population (uncensored decided cases):

| fit | programme | truth median | posterior median | ratio | truth in CI90 | truth visits | posterior visits | in CI90 |
|---|---|---:|---:|---:|---|---:|---:|---|
| C29, converged | C29__S12 | 46.0 | 83.2 | 1.81 | yes | 16.9 | 17.2 | yes |
| C29, deduplicated | C29__S12 | 46.0 | 105.5 | 2.29 | yes | 16.9 | 17.2 | yes |
| C44, converged | C44__S12 | 41.0 | 103.2 | 2.52 | **no** | 17.0 | 15.1 | yes |
| S03 combined | C32__S03 | 104.5 | 348.7 | 3.34 | **no** | 19.9 | 15.6 | yes |
| S03 combined | C35__S03 | 198.5 | 494.8 | 2.49 | **no** | 26.2 | 17.0 | **no** |
| S03 combined | C38__S03 | 84.5 | 350.7 | 4.15 | **no** | 22.1 | 19.1 | yes |
| all five pooled | C29__S12 | 46.0 | 256.3 | 5.57 | **no** | 16.9 | 17.2 | yes |
| all five pooled | C44__S12 | 41.0 | 197.8 | 4.82 | **no** | 17.0 | 15.0 | yes |

The eight sk3 fits collected today, at population 8,192 and three times the
draws, reproduce these ratios almost exactly (C29 1.77, combined 1.98 and
2.42, deduplicated 2.27 to 3.28, S03 2.47 to 4.80, all five 2.13 to 5.40; receipt in
`runs/w2_v6_fits_sk3_20260919/truth_comparison.json`), so the bias is in the
model and the evidence, not the sampler. The S03 and pooled fits had not converged, and their numbers are weaker
evidence than the two converged S12 fits. But the direction is the same in
every row, and the two fits that passed every gate are off by 1.8 and 2.5
times. The 90 percent interval on C29 is 28 to 334 days, which covers 46 only
because it covers nearly everything.

**Pooling made it worse.** C29 alone gives 83 days; C29 fitted jointly with
C44 gives 84; C29 fitted jointly with all five gives 256. The shared task and
agency effects transmit the upward bias between programmes rather than
cancelling it, because every programme's evidence has the same bias. This
matters for the agency-culture question below: pooling across jurisdictions is
exactly what that design does, and it will amplify rather than average out any
shared selection bias.

**The copied-claim correction pushed the estimate away from truth.** The
2026-09-18 audit found that removing double-counted forum claims lengthened
the clock by a quarter and concluded that the contamination "was biasing
measured burden downward, the worst direction for this project." Deduplication
was methodologically right, and the double counting was real. But against
truth, the deduplicated fit is further off (105 versus 83 against 46), and
the reason is that the duplicated claims were short reports that happened to
lie nearer the truth than the rest of the forum evidence. The overall bias is
upward and large, and a correction that moved the estimate the same way as
the bias was read as a warning in the wrong direction. That conclusion is
withdrawn; the deduplication itself is not.

### 2.2 Why the clock is long: three defaults with a known direction

Decomposing the converged C29 fit, using the saved draws and the truth log:

| quantity | days |
|---|---:|
| truth: median arrival-to-decision clock | 46 |
| truth: median sum of visit durations along a case's path | 60 |
| posterior: sum of per-operation medians | 71 |
| posterior: median clock | 83 |

Three factors multiply to the 1.8:

1. **Overlap the model cannot see, 1.30.** The truth's path sum exceeds its
   clock by 30 percent because activities overlap. Across the five programmes
   the overlap ratio is 1.18 to 1.38. The bridge assigns `parallel` only where
   a document states independent simultaneity, which is the right rule for
   a claim and the wrong default for a clock: silence is treated as serial.
   In C29 one block of four applicant steps is parallel and the other fifteen
   operations are serial.

2. **Unreported operations at the prior, 1.18 on the sum and wrong step by
   step.** Ten of nineteen operations have no informative observation. Their
   posterior medians are 2.4 to 4.8 days each with 90 percent intervals from
   0.3 to 50 days. The truth for those ten is mostly under two days, except
   the agency's technical review, which is 16 days and is the longest step in
   the process. The model gives that step 4.7 days and gives a payment step 2.4
   days. It cannot tell them apart, because nothing in the documents times
   either, and the task-type effect that could have distinguished them sits at
   its prior (contraction 0.10). The sum comes out only 18 percent high
   because the errors partly cancel; the per-step picture, which is what a
   burden map shows, is wrong in both directions.

3. **Skew and the repeat block, 1.17.** The sum of independent lognormal steps
   has a median above the sum of medians, and the repeat block adds a prior
   0.8 extra rounds of a three-step block. Neither is an error, but both
   compound the first two.

On the real solar fit the same mechanisms act with different weights: twelve
of 35 operations have no observation, but the learned location is low enough
that they add only 18 days, and the clock is instead carried by span reports
from forum cases, with a single operation, the inspection scheduling request,
absorbing a 34-day posterior median because it is the only place the model can
put the inspection queue.

### 2.3 Forum posters are modelled as unselected, and both corpora select them

The benchmark plants complaint selection (`visibility.py:596-613`): a decided
case posts with probability 0.50 if denied, 0.35 if slower than the 75th
percentile, and 0.08 otherwise. A slow case is therefore 4.4 times as likely to
post as a normal one, and in a programme with no denials about 59 percent of
posters come from the slowest quartile. Every informative observation in the
C29 fit is from a forum post (11 of 13; the other two are published medians
that did survive). In the solar fit all 92 informative observations are forum
reports from 67 cases. Every one of them is compiled as `sampling:
unselected`, because the diagnostic compiler policy sets
`default_case_sampling: unselected` and no case-sampling file was written.

The model has the mechanism: `delay_selected` cases and a `selection_sd`
parameter that reweights a case by where its decision clock falls relative to
the population's 75th percentile (`bayes_trace_hierarchy.py:836-848`). It is
off by default (`selection_sd: 0.`) and has been off in every fit. The
correction is available, its direction is known, and the benchmark plants the
parameter it would be validated against.

### 2.4 The solar posterior never saw the administrative data

`runs/rw_parse_20260918/solar_permit/fit_full` was reported as "permit review
moves from a published 4 days to 37" and "the whole process to initial
decision has a median of 226 days against a published 113". Reading the fit's
input:

| observations | count | contribution |
|---|---:|---|
| individual forum reports, 67 cases | 92 | the entire likelihood |
| published population medians (SolarTRACE, dashboards, reviews) | 69 | residual only, a constant |
| other residual-only rows | 88 | a constant |

All 69 published medians were dropped by two compile rules:
`finite_cohort_requires_explicit_joint_sampling_contract` (a population median
with a stated n needs a hand-written cohort binding, and none was written) and
`conditional_or_unknown_population_scope` (the audit did not resolve which
permits the figure covers). So the published four days was never in the
likelihood. The 37-day posterior is not the model disagreeing with a dataset
of thousands of permits; it is the model's reading of 92 forum spans, in which
plan review appears only inside six multi-step spans and never alone. The
comparison in the results note is between a number the model did not see and
an estimate from the population least likely to match it.

Two further details. The model's `initial_decision` event on this bridge is
the utility's permission-to-operate grant, the only operation carrying a
`decision` marker, so the 226-day "process to initial decision" is the whole
process through interconnection, and the published figure it is compared with
must use the same endpoint. And a population median, when it does enter,
carries a report spread of at least 0.5 on the log scale against 0.25 for one
forum post (`_observation_parts`, `scales[j]=max(scales[j],.5)`), so a median
over ten thousand permits is given a wider error band than one applicant's
recollection unless someone writes the cohort binding that unlocks the
finite-sample likelihood. That rule is defensible when n is unknown; SolarTRACE
states n.

### 2.5 Step counts are right because the inventory is right, not because anything was measured

On C29 the posterior mean visit count is 17.2 against a truth of 16.9, and
the fit reports a repeat probability of 0.50 and a continuation probability of
0.38. Those are the prior's medians exactly: a standard normal through the
probit gives 0.5, and the Beta(2,3) median is 0.386. The identification report
confirms it, with contraction 0.03 on the repeat block and 0.01 to 0.03 on
every path logit. The count is the handoff's operation inventory, which the
author sized correctly, plus a prior 0.8 extra rounds that happens to sit near
the truth's 1.02. One count observation reached the likelihood in C29, and one
in solar.

That is not a failure of the model. It is a statement that the first priority
is currently answered by the structural handoff, a hand-authored document, and
by the prior, and that a change in either would move the answer with nothing
in the evidence to resist it. Count evidence that could resist it was being
lost at 47 percent to the case-registry gap; Codex's `burden-count-evidence/2`
repair, landed today, removes that gap, and the number of count observations
per fit is the figure to watch next.

The model also reports total operations and total visits, not applicant-facing
ones. An applicant-facing count is derivable from the route today (operations
whose actor role is `payer` or whose `payer_work` is true, times visits) and is
not reported. Given the priority ordering it should be the headline count.

### 2.6 Money is exact where published, never reported, and blind to what dominates

The fee machinery works: with dated precedence the bridge prices C29 at $400
and C44 at $380, and the benchmark's per-case `fees_paid` is exactly $400 and
$380. Two things follow. First, the benchmark cannot test cost heterogeneity,
because every case in a programme pays the same amount, so a correct total is
weak evidence about the model. Second, and more important, `expected_burden`
and `report()` never emit a fee total, so a posterior carries the fee inputs,
uses them to identify which path a case took, and reports nothing about cost.
Adding a `mean_fee_total` with its spread over paths and repeats is a small
change with no new coordinates.

The real fit dropped fees entirely because nine of 35 operations had no stated
amount and the trace refuses to sum an unknown as zero, which is correct. And
the real burden is not the permit fee: the ADU ledger has a $3,000 permit
beside $4,000 of school fees, $2,000 to $20,000 of sewer connection, and a
$26,000 case with a $10,000 survey. None of that is a fee on an operation.
The contract has no channel for money that flows to third parties, money that
flows to the applicant, or the cost of delay, and the third priority names
exactly those.

### 2.7 Onerousness of a step has no data

Across the five synthetic programmes there is one quantified applicant-effort
claim. Across the real corpus the forum units carry 62 percent of the 240
effort claims, and nearly every new magnitude is mandated training hours, not
time the applicant spent. The `payer_hours` channel is modelled, omitted from
every fit for lack of observations, and correctly reported as absent. The
handoff already recommends measuring onerousness structurally, from what each
step demands; nothing in the model opposes that, and nothing in it does it.

### 2.8 Smaller items

- **Population medians outweighed by single posts** (2.4 above) is a policy
  choice in `_observation_parts` and should be a compile-time decision per
  source type, not a floor.
- **One repeat block per programme** against 32 disconnected loops in nine
  ledgers is recorded in the gaps note and stands; the model's repeat count
  is one kind of going back.
- **Fixed hierarchy spreads.** `agency_sd`, `task_sd` and `operation_sd` are
  constants. Only the case spread is learned. For the agency-culture question
  this is the wrong way round: the between-agency spread is the estimand.
- **Identification report dominated by nuisance.** Of 2,514 whitened
  coordinates in the solar fit, 2,412 are per-case noise (67 cases by 36).
  "2,418 contract by less than 25 percent" is almost exactly that block, and
  says nothing about the estimands. The per-block table is the honest view:
  location 0.92, agency 0.31, task 0.26, operation 0.06, source 0.00, path
  logits 0.01 to 0.05.

## 3. The three priorities, each on its own

### 3.1 Steps

*What the data hold.* 4,400 measurements across 27 ledgers, 574 forum cases
in the concealed-carry corpus alone; count claims in validated form for the
firearms and unemployment processes, now 21 for firearms after Codex's
registry repair; per-case rework rounds in every synthetic event log.

*What the model does.* Visit and operation counts are exact functions of the
route and the repeat law. Individual count reports enter through a discrete
Laplace kernel with a geometric outlier mixture. Population count summaries
("on average 2.3 rounds") are refused by design.

*What we would learn today.* The inventory size, from the handoff, plus a
prior repeat rate. The synthetic comparison says the inventory has been sized
well by hand on four of five programmes and undersized on C35 (17 modelled
visits against 26 in truth, outside the interval), which is the programme with
2.4 rework rounds per case. The model under-counts exactly where repetition is
heaviest, because the prior on repeats is uninformative and the one repeat
slot cannot hold two kinds of going back.

### 3.2 Time

*What the data hold.* 1,466 audit-eligible elapsed rows, two thirds of them
from forums; published medians with stated n in solar, naturalisation and
food benefits; statutory caps and targets on the agency side, which are
evidence about promises rather than about clocks.

*What the model does.* Everything in section 1. It learns the location well
(contraction 0.83 to 0.92) and nothing else.

*What we would learn today.* A process clock biased upward by a factor of
about two under current defaults, with an interval wide enough to cover the
truth on the one converged single-programme fit and not on the others. The
three causes each have a fix whose direction is known and a synthetic world in
which to validate it.

### 3.3 Cost

*What the data hold.* 1,201 fee rows across 30 ledgers, 33 flagged by the
fee-scope audit as contradicting their own scope; published schedules for
most agency-side processes; forum totals that include the costs no schedule
lists.

*What the model does.* Sums published operation fees along the path; compares
an applicant's reported total to that sum; reports nothing.

*What we would learn today.* Nothing, because nothing is reported. After a
twenty-line change: the schedule fee total per path, exact where the schedule
is complete, refused where a step is unpriced. Never the external costs.

## 4. Hierarchical priors over agency speed and culture

*What exists.* One random effect per agency per channel, shared across every
operation that agency performs and across every programme in a joint fit, with
a fixed prior spread of 1.0 on the log scale. `hierarchy_design_audit`
correctly warns that an agency effect is separable from task mix only when
the actor-by-task design is connected. In a single-programme fit it is
absorbed by the location and is unidentified; in the process fits its
contraction is 0.13 to 0.31.

*What has been tried.* Two fits launched on sk3 on 2026-09-18 and collected
today, `runs/w2_v6_fits_sk3_20260919/rw_fit_solartrace12` and
`rw_fit_solartrace60`, are the agency-culture design in miniature: the same
four-step solar route as one programme per jurisdiction, for the 12 and then
the 60 California jurisdictions with the most installs, fitted to 6,298
SolarTRACE published medians per jurisdiction, phase and year. No forum data,
no truth read. What they show:

| | 12 jurisdictions | 60 jurisdictions |
|---|---:|---:|
| agencies (authority plus its utility) | 24 | 120 |
| spread of per-agency mean step time, log-sd | 0.43 | 0.40 |
| ratio of 90th to 10th percentile agency | 2.9 | 2.5 |
| fastest authority, days per step | San Diego County 7.3 | Dublin 3.7 |
| slowest authority, days per step | Los Angeles County 28.5 | Housing and Community Development 28.9 |
| contraction: location / agency / task / operation | .95 / .86 / .78 / .52 | .96 / .89 / .84 / .59 |
| hierarchy coordinates flagged | 76 of 78 | 364 of 366 |
| worst R-hat, agency block | 2.30 | 3.05 |

The per-agency totals are identified, and the spread they show is real and
large: a permit step in the slowest authorities takes four to eight times what
it takes in the fastest. The decomposition is not identified. Operations are
keyed by programme (`identities` in `VisitHierarchy.__init__` includes the
programme id), so no operation is shared between jurisdictions, every
operation belongs to exactly one agency, and any shift in an agency's effect
can be absorbed by its four operation effects. Only the sum moves the
likelihood; the sampler walks the ridge, and every coordinate in the
hierarchy fails its gate while the sums it reports are stable. This is the
design audit's warning realised, and it says exactly what the model needs
before it can answer the culture question: an operation effect shared across
jurisdictions for the same step, so that the agency effect is what remains
after the step is accounted for. That is a change to how operations are
identified, not to the likelihood. It is also worth noting that the spread
these fits find, 0.40, sits beside the synthetic world's planted 0.37; that
is a coincidence of two independent choices, but it means the benchmark is
in the right regime.

*What is missing.* Four things. Shared operation identities across
jurisdictions, as above. The spread is fixed, and the spread is the
quantity a culture question asks about; it needs a hyperprior and a
coordinate. The effect is indexed by the operation's actor, which answers
"which body does this step" and not "which of 58 bodies did this case's
step"; for one statute across jurisdictions the effect must be selected by the
case's jurisdiction, or each jurisdiction must be its own programme with a
shared task vocabulary. And the jurisdiction is not a ledger field: in the
concealed-carry ledgers it lives as free text in `cohort` ("Kern County
Sheriff initial licence, 2017") and as 48 declared per-county actors, while
every agency activity is attributed to `generic__county_sheriff`.

*What the data offer.* Exactly the design Dan describes. One statute, Penal
Code 26150 onward, implemented by 119 issuing authorities in the parsed forum
corpus, with 14 authorities at ten or more cases (Ventura 99, Los Angeles 51,
Kern 42, San Luis Obispo 24, Monterey 21, Merced 19, Tulare 19, Orange 18).
And a synthetic world built for the same question: 58 counties, twelve
statutes with 17 to 61 implementations each, a planted county speed effect
with log spread 0.37 around a centre of 1.15, and a planted
availability scenario for the rural-commons argument. The model's fixed agency
spread of 1.0 is 2.7 times the planted one, so a fit that could not identify
the spread would report county differences the prior invented.

*What blocks it.* Not the model. Five of 489 synthetic processes have ever
been bridged, because each needs a hand-authored structural handoff and two
per-measurement audits. The derived handoff removes the clerical half; the
semantic half is 753 decisions for the real corpus and unknown for the
synthetic one. Until that wall moves, a 58-county fit is not reachable, and
the pooling result in 2.1 says that when it is reached, shared forum selection
will be amplified across counties unless selection is modelled first.

## 5. What we are likely to learn, honestly

With the model as it stands and the evidence as it stands:

1. **One number per process**, the typical scale of a step, learned well.
   Everything structural stays at its prior and the model says so.
2. **A step count that is the author's inventory**, right when the handoff is
   right, unmoved by evidence until count claims reach the likelihood in
   numbers, which is now possible.
3. **A clock two to four times too long**, with three fixable causes.
4. **A schedule fee total**, once it is reported, exact where the schedule is
   complete, and silent on the costs that dominate.
5. **Agency totals but not agency culture.** The SolarTRACE fits show a
   2.5 to 2.9 spread across sixty authorities in total step time, and cannot
   say how much of it is the authority rather than the step. The data for
   the full question are parsed and the benchmark for it is rendered.
6. **A route posterior that is a mild update.** The solar fit's 0.51 for the
   merge reading against a 0.33 prior is a Bayes factor near 2.3. It is a
   genuine inference and a weak one, and it came from forum spans alone.

None of this is an argument against the model. It is an argument that the
model has been run in a regime where the prior does most of the work, and
that the defaults chosen for safety against false precision have a direction.
The benchmark exists so that this can be measured, and today is the first
day it was.

## 6. Recommended changes, ranked by value to the three priorities

Sequenced with owners and gates in `docs/2026-09-19-next-steps-plan.md`.

Not executed. In order:

1. **Score every synthetic fit against truth as part of its release path.**
   Add V6 support to `evaluate_burden.py`; until then
   `runs/w2_v6_fits_20260918/compare_to_truth.py` is the stopgap. A fit that
   passes its gates and misses truth by a factor of two should not be
   quotable.
2. **Model forum selection.** Declare forum cases `delay_selected`, turn on
   `selection_sd`, validate on W2 where the selection is planted with known
   strength. Known direction, small change, the largest single bias.
3. **Stop treating silence as serial.** Where the ledger states no order,
   report the clock under a serial and a critical-path reading, or put a
   prior on within-block overlap. Known direction, 18 to 38 percent.
4. **Report cost.** Add a fee total to `expected_burden` and `report()`. Then
   the contract change already recommended: a channel for money to third
   parties, money to the applicant, and the cost of delay.
5. **Report applicant-facing steps** separately from total operations, from
   the route's payer flags.
6. **Bind published cohorts automatically** when a measurement states its n
   and the audit resolves its scope, so administrative datasets are not
   discarded by default.
7. **Share operation identities across jurisdictions, learn the agency
   spread and index it by jurisdiction.** Rerun the 60-jurisdiction
   SolarTRACE fit first, since its inputs exist and its sums already
   converge in effect. Then fit the
   concealed-carry corpus across its fourteen well-covered authorities as the
   first agency-culture result, and validate on the S06 to S08 synthetic
   statutes with sixty counties each.
8. **Give unreported operations a task-informed prior.** A payment is not a
   seven-day step. The task effect exists; it needs either a learned spread
   with enough programmes to identify it, or elicited task medians.
9. **More than one repeat block.**

## 7. On Dan's notes, without acting on them

The question in the notes is whether decision-tree complexity tracks
outcomes, and whether process modelling is the right tree. Three things from
this audit bear on it. The synthetic world already varies both: it plants a
decision model per statute and a process per county, with county speed and
availability as separate knobs, so the comparison Dan proposes can be run on
ground truth before it is run on California. The real concealed-carry corpus
is the same design in the wild, one statute and 119 implementations, and its
forum side is where the outcome variation lives. And the measurement this
audit finds hardest, the time a step takes when nobody reports it, is the
same underspecification Dan names on the decision side: the primitive units
are not given by the text, and a process model that cannot tell a payment
from a technical review without evidence is making the same choice a
decision-tree representation makes when it collapses a node. Treating that
uncertainty as the object of study rather than as noise is what the
identification report already does; the audit's contribution is that the
report has now been read against truth once, and the prior was doing more
than it looked.
