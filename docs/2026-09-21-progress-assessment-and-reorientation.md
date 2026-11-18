# Progress assessment, review of Codex's checkpoint, and a reorientation

2026-09-21, 23:30 Pacific on the 20th. Written at Alex's request: what this
thread accomplished, an audit of Codex's 20 September checkpoint and its
marginalisation note, whether the CalFresh structure report holds a posterior,
and how to continue against Alex's stated priorities, which are the number of
process steps and the time, repeats and burden attached to each.

## 1. What this thread accomplished

**Audits.** V6 was scored against synthetic truth for the first time and found
to overestimate the process clock by 1.8 to 4.2 times, with the cause traced to
whole-process statements being dropped before the likelihood
(`2026-09-19-bayesian-burden-audit.md`). Codex's 19 September work was audited
and every number reproduced (`2026-09-20-audit-of-codex-work.md`). A blind
reader found label errors on about one row in five of either agent's ledgers,
with no wrong numbers, which established that the error is a property of the
task. A source-trust note showed every per-source offset in every fit sits at
its prior and that the precision floor was inverted.

**Solar leg, executed end to end.** Estimands frozen before any fit; a
9,586-cell panel built from Codex's corrected matrix after I found my own count
inflated 3.4 times by repeated utility rows; a converged crossed hierarchical
model, verified against an independent closed-form computation to 0.0023; a
verified forum dataset; held-out scoring; twenty tests. The results
(`2026-09-20-solar-bayesian-results.md`): authorities differ by 2.39 times
between the tenth and ninetieth percentile; load elasticity is −2.3 percent per
doubling; the authority-specific elasticity is not estimable; the model
**fails its own frozen decision rule** against the raw cell median on both
splits while predicting centres better; and the forum reporting offset is −42
percent on twelve reports, in the direction opposite to the project's standing
assumption. That last number was corrected twice under validation, each time
for a defect of mine, and the direction held through both.

**What I left undone on solar, and it is the part Alex ranks first.** Stage A
discovered per-authority step and cost channels in the source's companion file:
a required-inspection count for 240 authorities, a structural-review flag for
439, a median permit cost for 383. They are joined into the panel and I never
analysed them. I fitted timing, which is Alex's second priority, and stopped.
The composed applicant clock and the literature check are also outstanding.

## 2. Does the structure report contain a valid posterior?

**No, and it does not claim to.**
`calfresh_integrated_applicant_structure_results_v1/report.md` is a descriptive
inventory: 220 claim references and 103 numeric fact rows under thirteen action
headings, six requirement headings and eleven obstacle headings. There is no
model, no likelihood, no draws and no posterior in the directory, and the report
says plainly that the headings are "descriptive categories, not thirteen
mandatory steps or a learned process graph." It is honestly labelled.

It is also, unnoticed, the closest thing to a step vocabulary CalFresh has. The
thirteen action headings with their claim counts:

| action | claim refs |
|---|---:|
| contact or escalate | 56 |
| monitor notices, portal or mail | 37 |
| provide verification or documents | 33 |
| participate in interview | 16 |
| submit periodic report or renewal | 16 |
| report change, transfer or closure | 14 |
| manage card or account | 14 |
| review, sign, attest or correct | 13 |
| apply or reapply | 11 |
| visit office | 11 |
| appeal or request hearing | 8 |
| respond to review, investigation or overissuance | 8 |
| report theft or seek reimbursement | 2 |

And the obstacle headings are the onerousness channel the project has never had
anywhere else: 40 references to phone access failure, 30 to document rework, 34
to notice conflicts. Nobody has turned this into a step-level burden table.

## 3. Audit of Codex's checkpoint

Codex's document is accurate, exhaustively hedged, and honest about every
failure. I checked the live joint run (PID 42245, running 23 minutes, first
condition not yet writing draws) and the structure directory contents. Nothing
in the checkpoint overstates. The problems are in emphasis and allocation.

**3.1 The priority order is inverted.** Alex's addendum at 06:20 UTC names
agency capability and process steps as the priorities. Codex's ordered
remaining work puts "finish the live joint run" first, county hierarchy second,
and structure and count inference third, described as "not yet an explicit
deliverable." The step count is the last thing on the list.

**3.2 The joint fit is the expensive validation loop again.** Forty-seven forum
histories, three operation clocks. Six sampler attempts have failed convergence.
The seventh, running now, required an adaptive quadrature scheme, an algebraic
exact-support helper, Gaussian orders up to 1,536, and a two-hundred-to-four
coordinate marginalisation, all documented across a 162-line methods note. The
mathematics in that note is correct. But the payoff if it converges is three
operation log-locations and a route split between an interview path and a
direct path, and the note itself states that agency effects are at scale zero
and "no method can turn that into a learned intrinsic agency delay." The fit
that is consuming the coordinator's attention cannot answer the priority
question by construction.

**3.3 V6 loses to a trivial baseline, and the implication is not drawn.** On
the administrative comparison, a county-specific Dirichlet half-count baseline
scores 0.25228 and the best V6 fit 0.25275. That is the same result as my solar
leg, on a different family, with a different model: the hierarchy does not beat
reading the table. Codex reports it faithfully and then proposes, as remaining
item two, to build more county hierarchy.

**3.4 The repeat evidence exists and is unused.** V6 already carries a count
channel. The inventory has 56 contact-or-escalate references, 40 phone-access
failures, 30 document-rework references. None has been turned into a
repeats-per-case distribution, which is the most direct measurement of the
burden Alex ranks first.

**3.5 Denominators as output.** The document reports 945 threads, 776 review
items, 778 registry rows, 100 linked threads, 117 records, 118 with a
sensitivity, 284 descriptive references, 220 structural references, 187 uses,
167 open. Codex's own earlier audit named excessive bookkeeping as a hazard.
This checkpoint is 554 lines, and most of the numbers in it are accounting
rather than findings.

**3.6 What is genuinely good and should be kept.** The seven clock components
are real burden-per-step numbers: 150 minutes in the phone queue before an
answer, abandonment or disconnect; nine days from application to interview; 17
days from periodic-report submission to a material response; 22 days from
approval to holding a card. Those are exactly what Alex asked for, per step,
with posteriors. The semantic corrections Codex made are the right ones. And the
inventory's ontology is a usable step vocabulary. The pieces of the priority
deliverable exist. They have not been assembled.

## 4. The reorientation

One deliverable per family, the same shape for all three:

**a step-level burden table.** Rows are the steps of the process. Columns are:
time in the step with a posterior interval; repeats per case where reported;
money at the step and to whom; the count of reported obstacles at the step as
the onerousness proxy; and the evidence count behind each cell. That is the
artefact this project exists to produce, and for two families most of it is
already on disk in pieces.

### Solar, half a day, mine

The panel already carries, per authority, the number of inspections required,
whether structural and electrical review are required, whether a rough-in
inspection is required, and the median permit cost. Cross those with the fitted
phase times. That yields, for 240 to 439 authorities, a table of required steps,
time per step and cost, and a direct test of whether authorities requiring more
inspections take longer. No new modelling. I should have done this before the
timing fit and did not.

### CalFresh, one to two days, Codex

Take the thirteen action headings as the step vocabulary. Attach each of the
seven fitted clocks to its step. Turn the contact, phone-failure and rework
references into per-case repeat counts through the count channel V6 already
has, reported as distributions with their selection caveat. Attach obstacle
counts per step. That is the CalFresh burden table, and it needs no new sampler.

Two things to stop. Let the seventh joint attempt finish and take its result or
its failure; do not attempt an eighth. And drop the county-hierarchy item: the
administrative comparison already shows the raw county proportions with a
conjugate posterior beat V6, so the county contrasts are readable from the
baseline that won.

### Concealed carry, after the other two

It is the richest steps-and-money evidence in the corpus, 2,011 case identities
across 30 authorities with fees to four separate payees, and it has no fit at
all. If the priority is steps and burden per step, this is where the data are,
and it should come before any further synthetic or verification work.

### What this does not require

More parsing. More sampler engineering. A unified administrative-plus-forum
posterior. Any of the three families "complete." A synthetic counterpart. The
literature check still gates any write-up, and it still has not run.
