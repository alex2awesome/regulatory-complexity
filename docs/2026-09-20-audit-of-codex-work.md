# Audit of Codex's work of 2026-09-19 and 20

Requested by Alex after Codex's end-of-day summary. Four things are audited:
the model experiments, the parse and its corrections of the earlier ledgers,
the source inventory, and the synthetic verification. The model part is mine;
the other three were checked by fresh-context, read-only agents working from
files alone, whose receipts are under the session scratchpad and summarised
here. The closing sections answer Alex's follow-up: concrete next steps, and
whether this has hit a ceiling.

**Isolation record.** This conversation has read W2_DEV_001 development truth
(recorded 2026-09-19). Nothing here authors a handoff, a ledger or a fit input.
The one new computation, an importance reweighting of an archived posterior,
reads no truth and is labelled a development sensitivity. The three audit
agents were given the standing forbidden-path list and no truth. All five
programmes scored so far are calibration or development partition
(`render_manifest.json`: C29, C32, C35 development; C44, C38 calibration); no
reserved label has been read by this conversation.

## Verdict in one paragraph

Codex's work is careful, honestly reported and mostly right, and its summary
to Alex understates rather than overstates. Every number checked reproduces:
all seven model results to two decimals, 73 ledgers and 10,141 rows, every
hash, every contract check, all 32,688 quotations under the contract's
normaliser, 14,915 files, 1,799 threads and 32,669 comments, 613 PDFs and
21,380 pages, 428 of 438, and 978 tests. Its model code is sound and
default-off, its truth boundary is better than the one it inherited, and it
caught two real errors in my burden audit. Four things are thinner than the
summary suggests: eight of 28 revisions do not itemise their edits; the
semantic corrections live in sidecars that nothing consumes, so the snapshot
still holds the rows they flag; "ten held" synthetic documents is the
non-passing subset of 29 under hold; and two facts exist only in conversation
and not on disk, Alex's approval of the two synthetic repairs and any
authorisation for the live network retrieval of 590 pages. One finding is
about the task rather than about Codex: a blind reader found a misleading
label on one row in five of Codex's own ledgers, the same classes Codex found
in mine, with no wrong numbers in either. And one finding goes past Codex's
diagnosis: the model's clock fails recovery because the sentences that state
the whole-process time are dropped before the likelihood, so the total is
free, every intervention on the parts is absorbed by one loose global
parameter, and a one-sentence baseline beats the model on both programmes.
That is fixable, and it is the next experiment.

## 1. The model experiments

### 1.1 Every reported number reproduces

| experiment | reported | recomputed from the archived posterior | converged | usable |
|---|---:|---:|---|---|
| C29 control | 81 | 81.13 | yes | yes |
| C29 selection on | 81 | 81.31 | yes | yes |
| C29 one-day task priors | 103 | 102.88 | yes | yes |
| C44 control | 103 | 103.24 | yes | yes |
| C44 decision-scope repair | 84 | 83.56 | yes | yes |
| C44 block-order sensitivity | 98 | 98.06 | yes | yes |
| C44 one-day task priors | 107 | 107.19 | yes | yes |

Codex's framing is also right: each is a single-intervention sensitivity
against a frozen control, none is combined, none is presented as a repair, and
every one is reported as failing the 0.7 to 1.4 recovery gate. Its summary to
Alex does not overstate anything in its own log.

### 1.2 The code changes are sound and default-off

Diffed against the code snapshot frozen with the 18 September solar fit:
`bayes_trace_hierarchy.py` +352 lines, `compact_visit_trace.py` +45,
`run_visit_hierarchy.py` +62; `latent_gaussian.py` and `cohort_quantiles.py`
unchanged.

- **Task-prior baselines** add a fixed per-task log offset to the elapsed
  location and no coordinate. Empty by default.
- **Explicit block DAG.** Either every block declares predecessors or none
  does; partial graphs, unknown ids and cycles fail. Block start is the
  maximum of predecessor ends, the modelled end is the maximum over blocks,
  and a repeated block stays atomic. Correct, and honest about what it is: a
  supplied hypothesis, reported with `overlap_learned: False`.
- **Selection caches** key on immutable trace identity, path probabilities and
  strength. Codex's replay of 2,512 likelihood factors at zero difference is
  the right test.
- **Fee total and spread.** The between-case variance uses
  q(1+r-q)/(1-r)^2 for the hurdle-geometric repeat count, which is the correct
  variance of that law, and path mixtures combine by total variance rather
  than averaging standard deviations. C29 and C44 can now report the $400 and
  $380 the burden audit asked for.
- **Applicant-facing counts** suppress the total when any operation's
  applicability is unknown, rather than counting unknown as zero. Right call.
- **Operation-centred sampler.** An opt-in transition kernel that proposes in
  operation-mean space and then refreshes the null space of the hierarchy
  design exactly. This is a direct and correct answer to the ridge that made
  every coordinate of the two SolarTRACE fits fail at R-hat 3. It has not been
  run on them yet; that is the obvious first use.
- **Truth boundary.** `evaluate_burden.py` now checks fit completion, the
  posterior hash and every programme's partition before opening any truth, and
  rejects reserved and unassigned programmes. No inference-side module gained
  a truth path.

Two things Codex found that correct my own work, both accepted:

- My scratch `compare_to_truth.py` treated `event_clocks.initial_decision` as
  a number when it is an object, and silently fell back to the last-decision
  clock. Codex's standard evaluator reproduces all 29 of my rows with zero
  difference because first and last decision coincide on these five
  programmes, so my numbers stand and my clock handling does not.
- "69 dropped medians" in the burden audit and Codex's "56 finite-cohort
  holds" are different predicates. More important, Codex's readiness review of
  the solar medians shows my recommendation to "bind cohorts automatically
  when n is stated" was naive: eleven rows put a count of jurisdictions in
  `n`, seventeen copy a year's project total onto endpoints that only half the
  projects have, and twenty-five quote a derived summary. The field says n;
  it does not say n of what.

Codex also disclosed one truth-access slip of its own, an ad hoc read of an
unassigned programme's log, and built the partition guard that prevents it.
That is how such a thing should be handled.

### 1.3 What Codex's diagnostics did not identify, and this audit does

Codex shows that one-day task priors shorten the clock by 38 percent when
parameters are held fixed and lengthen it slightly on refit, and says the
diagnostic "does not identify which parameters cause that compensation". It
is one parameter, the global location.

| fit | location, days | filing | payment | notification | decision | technical review | sum of step medians |
|---|---:|---:|---:|---:|---:|---:|---:|
| C44 control | 3.8 | 1.9 | 6.6 | 3.9 | 5.6 | 6.3 | 76 |
| C44 one-day task priors | 6.7 | 1.0 | 2.5 | 0.9 | 12.0 | 14.6 | 95 |
| C29 control | 3.5 | 3.7 | 2.3 | 3.1 | 4.6 | 4.0 | 70 |
| C29 one-day task priors | 8.5 | 3.2 | 1.6 | 1.1 | 7.6 | 8.0 | 91 |
| C44 block order | 5.1 | 2.0 | 6.2 | 4.3 | 10.0 | 9.7 | 96 |

The mechanism is structural. Every operation's log duration is one shared
location plus agency, task and operation effects, and the location has by far
the loosest prior (spread 2 against 1, 0.75 and 0.5). The steps that get
reported are the applicant's own short ones. In the control, those short
reports pull the shared location down to under four days, and that low
location is then inherited by every unreported agency step: the model's
technical review is short because the applicant's filing was short. Tell the
model that filing is inherently a one-day step and the short filing reports
stop arguing for a low location, which relaxes to its seven-day prior, and the
unreported reviews and decisions double. The clock gets longer.

So the control's 81 days was already flattered by an accident: evidence about
fast applicant steps was shrinking unobserved agency steps. The task-prior
experiment did not fail; it removed the accident. The block-order result has
the same shape for a different reason: C44 has two whole-case totals, so when
the schedule is allowed to overlap, the location rises from 3.8 to 5.1 days to
keep filling those totals.

Both point at the same fact. **Nothing in these inputs pins the total except,
in C44, two forum totals of about 90 and 218 days against a true median of
41.** Interventions on the parts are absorbed because the whole is free.

### 1.4 The documents state the whole clock, and the pipeline drops it

Reading the archived control inputs, not truth:

| programme | statement in the documents | days | fate |
|---|---|---:|---|
| C29 | news: "around eight to ten weeks" from starting to the last decision | 56 to 70 | residual: `typical_range` unmodelled, clock boundary unknown |
| C29 | poster: "8 to 10 weeks start to finish" | 56 to 70 | residual: clock boundary unknown |
| C29 | poster: "whole thing ... 8 to 10 weeks" | 56 to 70 | residual: clock boundary unknown |
| C29 | poster: "TOTAL ELAPSED: 353 days" | 353 | residual |
| C29 | poster who abandoned: "23 days total" so far | 23 or more | residual |
| C44 | programme page: "usually 3 to 5 weeks" | 21 to 35 | residual: `typical_range` unmodelled |
| C44 | posters: 5 to 7 weeks, 3 to 5 weeks, 209 days | | residual until Codex's decision-scope repair restored these three |
| C44 | posters: about 3 months, 218 days | | **the only whole-case clocks in the control** |

C29's control has thirteen informative rows, all single steps, and zero
whole-case clocks. Every sentence in its corpus that says how long the process
takes is a constant in the likelihood. That is why selection correction moved
C29 from 81.13 to 81.31: the correction reweights a case by its whole clock,
and no case has one. Codex's information audit says this precisely, and its
conclusion that the result is "not evidence that selection is generally
irrelevant" is correct. My burden audit's ranking of selection as the largest
single bias was premature; on C29 it was untestable with these inputs.

A cheap test of how much the dropped rows matter, without a refit:
`runs/codex_audit_20260920/reweight_whole_process.py` importance-reweights
1,500 archived C29 control draws by the likelihood the dropped rows would have
had as whole-case clocks, using the model's own report kernel, each case's
latent durations and its posterior path weights. It reads no truth, and it
restores every dropped whole-process row rather than a chosen few.

| rows restored | median, days | 90 percent interval | importance sample, of 1,500 |
|---|---:|---|---:|
| none (control, this subsample) | 83.9 | 29.7 to 366.3 | |
| the two 8 to 10 week totals | 70.4 | 41.2 to 128.2 | 366 |
| plus the 353-day total | 98.7 | 47.7 to 168.3 | 28 |
| all five | 84.7 | 47.7 to 168.3 | 50 |

Two honest readings. The two ordinary totals alone move the median a sixth of
the way and cut the interval's width by three quarters, which is what an
anchored total does. And the 353-day report collapses the importance sample,
so its effect cannot be read from reweighting and needs a refit; it is one
report from the complaint-selected tail, and it is exactly what a selection
model with whole-case clocks exists to discount.

Which gives the experiment nobody has run: **whole-process evidence in and
selection on, together.** Each alone fails for a reason the other removes.
Selection alone has nothing to act on. Whole-process evidence alone anchors the
clock to the posters, who are the slow cases.

### 1.5 The floor the model is currently under

A one-sentence baseline: take the corpus's own typical-range statement at its
midpoint.

| programme | document's own sentence | true median | ratio | V6 control | ratio |
|---|---:|---:|---:|---:|---:|
| C29 | 63 | 46 | 1.37 | 81 | 1.76 |
| C44 | 28 | 41 | 0.68 | 103 (84 with decision scope) | 2.52 (2.04) |

Both sentences sit at the edge of the recovery gate, one above and one below,
which is itself a planted feature: the agency's page is optimistic and the
news report leans on slow cases. Both beat the model. That is not because the
model is a bad idea; it is because the sentence that carries the answer is
removed before the model sees it. No LLM baseline has been run on these two
source editions, so Codex's statement that superiority is undemonstrated is
accurate and, for the clock, understated.

## 2. The parse

### 2.1 The mechanical claims hold

Checked over the whole snapshot by script, not by sample
(`runs/rw_parse_20260919/review_sweeps_73_ledgers/selected_ledgers.json`):

| claim | result |
|---|---|
| 73 ledgers, 10,141 measurement rows | 73 and 10,141 |
| ledger, manifest and sidecar hashes bound | 73 of 73, 73 of 73, 70 of 70 match |
| every ledger passes the evidence contract against frozen sources | 73 of 73, with 4,358 documents supplied and none missing |
| every quotation matches its source | 32,688 references checked independently; 37 fail a whitespace-only match and all 37 pass the contract's normaliser, because the source has Markdown emphasis the quote omits |
| corrections are linked revisions, not overwrites | 28 revisions over 35 parent-to-child steps; no original missing, 467 recorded parent hashes all match, no original modified after its revision |
| my three partial megathread ledgers | none selected; all three threads were re-parsed from scratch (548, 343 and 757 measurements against my partial 230, 140 and 0) |

So "not silent overwrites" is true in the sense that matters: every original
is intact and hash-bound.

### 2.2 Where the record is thinner than it says

- **Eight of 28 revisions do not itemise their edits.** Two Reddit batches
  changed 39 and 31 measurements and record one narrative sentence each. The
  originals exist, so the edits are recoverable by diff, but "preserved as
  revisions with links to the originals" reads as though the edit list were
  part of the record, and for these it is not. A further six record some edits
  by narrative without measurement ids.
- **Access declarations are uneven.** Of 73 manifests, 39 carry a structured
  `hidden_truth_read: false`, 24 say so only in free text and 9 not at all;
  the network, paid-call and subagent declarations are weaker still, and eight
  manifests carry none of the four. One (`calguns_a_batch5`) declares
  `hidden_truth_read: null` with an independent review pending. These are
  self-declarations either way, but a snapshot that binds manifests by hash
  should not bind empty ones.
- **Measurement ids collide across ledgers.** 410 sequential `ccwf__mNNNN` ids
  are reused by two megathread ledgers with no shared text. Any merge keyed on
  measurement id will collide silently. Prefix them before compilation.
- **One later revision is on disk and not selected.** Reddit batch 003 has a
  `reviewed_v2` finished hours before the snapshot, with identical evidence
  and a different `burden_counts.json` that the snapshot does not bind.
- **One document id names two different byte strings.** `reddit_1rmnmlt` is
  cited by the solar ledger and by its Reddit supplement, and the two frozen
  artifacts differ.

### 2.3 Semantic accuracy, measured by reading sources

A fresh reader with no project context drew 60 numeric measurements from
Codex's own new ledgers with a fixed seed (25 forum, 25 Reddit, 10 other),
opened each source, read the whole post, and judged six things. It then
judged 25 of Codex's corrections the same way.

**Codex's own ledgers: 12 of 60 carry a wrong label, none a wrong number.**
A 95 percent interval on that rate is roughly 12 to 32 percent; the sample is
stratified, not proportional, so it is not a corpus rate.

| check | wrong of 60 |
|---|---:|
| value and unit, including ranges, bounds and date arithmetic | 0 |
| statistic: completed experience versus pending wait, rule, forecast | 5 |
| completed versus merely scheduled | 1 |
| case identity: right speaker, not a repeat of another case | 3 |
| what is measured: start, end, activity, actor | 5 |
| money: a personal payment versus a generic price (13 rows) | 1 |

By family: forum megathreads 4 of 25, Reddit batches 6 of 25, other 2 of 10.
The clearest examples: a two-year wait-to-reapply rule still running,
recorded as a completed 24-month individual duration; a $45 fee the poster
says they have not yet paid, recorded as a payment; a San Francisco
48-hour minutes-posting deadline attached to a records-production step whose
actor is the Highway Patrol; 31 days between two sub-results recorded as the
whole background check; and a 15-day interview-to-pickup span recorded as
starting at submission, in a batch with fourteen such rows.

These are the same classes Codex reported finding in my ledgers: pending
treated as completed, rules treated as observations, one applicant split into
two cases, a component recorded as a whole. Codex's parses are not worse than
mine, and its arithmetic and quotation are clean. The point is that the error
is a property of the task, not of the parser. **Roughly one row in five
carries a label that would mislead a likelihood, whoever parses it**, and the
labels at fault (statistic, start event, case identity) are exactly the ones
the compiler acts on.

**Codex's corrections: 21 of 25 right, 1 unnecessary, 1 wrong, 2 undecidable.**
The right ones include every cross-ledger duplicate it named (BlacknWhite,
jimster716, guymenton, InfragableKrunk, the repeated IHSS comment, all
verified in the source posts), the Mikeg2503 span whose own quote contains a
Live Scan submission inside the "pure agency queue", and a DROS applicant
deadline I had recorded as a 30-day duration. The wrong one moves "I called 6
local gun shops" into accepted counts as six encounters on the payment step,
against the review's own note that these are not six visits. One hold may be
over-cautious: "I had to go pick up my renewal within 3 weeks" reads equally
as a deadline or a turnaround, and Codex records the deadline reading as
confirmed.

**The corrections are not yet in the snapshot.** Every sampled correction to
an earlier ledger is a sidecar hold or disposition, and the files say no fit
consumes them. The 73-ledger snapshot therefore still contains the rows the
sidecars flag, including both copies of each duplicated applicant. "10,141
retained measurement rows" is accurate, and Codex says they are not
independent or fit-ready; a reader should take that literally.


## 3. The source inventory

Every count reproduces from the file system.

| claim | recount |
|---|---|
| 14,915 physical files, not "14,000 documents" | 14,915: 6,783 frozen origins, 4,258 withheld-only, 3,874 outside every freeze; 84 byte-duplicate groups holding 1,009 excess files |
| 1,799 archived Reddit thread views, 32,669 comments | 1,799 and 32,669, all already on disk from 17 September |
| 613 grand-jury PDFs, 21,380 pages | 613 and 21,380; a 614th has a broken cross-reference table |
| 577 missing forum pages retrieved and checked | 577 receipts, all HTTP 200, 1,731 files rehashed with no mismatch |

Codex also corrected an error of mine that it is too polite to name in its
summary: my freeze placed 735 grand-jury PDFs and 1,956 Reddit comment files in
a "withheld" bucket with no defensible reason to exclude them. They are source
documents and they were simply missed.

**One thing Alex should know rather than discover.** The 577 forum pages, and
13 public-records pages, were fetched from the live network on 19 September by
Codex's coordinator scripts (`retrieve_known_forum_gaps.py`, Python `requests`,
www.calguns.net at one request per second; twelve pages from muckrock.com and
one from sunshine.archive.sf.gov). The receipts are exemplary: every page has a
hash, a freeze record and `network_used: true`. But no authorisation is
recorded anywhere on disk, the "no network" rule I was given applied to parse
workers and was never written into `CLAUDE.md`, and 153 of 196 manifests in
the run directory carry no network field at all. This is a record-keeping gap,
not a finding of misconduct: the retrieval was by the coordinator, not by a
source-only parser, and the pages are what the corpus was missing. It needs one
line from Alex on disk saying it was permitted.

## 4. The synthetic corpus

- **428 of 438 passing holds**, as 428 passing, 5 failed and 5 unverified. A
  hash-only recount gives 430 and 8, because two news documents are marked
  unverified although each has a passing review of its current bytes, which is
  consistent with a stale spec or context hash.
- **"Ten held" undercounts the holds.** The five open hold reasons cover 29
  artifacts, and 19 of those sit inside the 428.
- **"You have just approved" is not on disk.** Both repair records say
  `awaiting_explicit_approval`, and the C25 record carries an earlier proposal
  marked `not_approved_do_not_apply`. If Alex approved them in conversation,
  the record should say so before they are applied. Neither has been applied:
  nothing under the world's truth or specs is newer than 13:03.
- **The development world was edited in place on 19 September**: 31 truth
  files, 48 specs and 228 artifacts, between 11:44 and 13:26, with before and
  after copies under `corrections/approved_*/`. Codex's evaluator later
  reproduced my truth comparison with zero differences, so the five programmes'
  clocks were not among the changes. But any fit scored before 13:26 and any
  scored after are against slightly different worlds, and a release should
  carry the manifest revision it was scored against.
- **Spec-derived outputs share a tree with source-only work.** Four
  construction-side scripts read generator specs, correctly flagged, and their
  outputs (`compact_news_count_cohort_audit_v1.json` among them) sit in the
  same run directory that source-only parsers are pointed at. The separation
  is by label. Most worker briefs were never saved, so what the workers were
  told cannot be audited.

## 5. Housekeeping

- **978 tests pass**, reproduced, one pre-existing warning. The suite rewrites
  four fixture files under `benchmark/synth/worlds/_fixture/web/` each run.
- **Nothing is committed.** One commit, `e581748`. 93 tracked files modified,
  114 untracked entries, none deleted, nothing staged. Twelve tracked model and
  test files were edited in place since the handoff, recoverable only to that
  baseline. Two days of work by two agents rests on a working tree.
- **Disk is at 99 percent**, 27 GiB free. `runs/bayes_v4` is 5.9 GiB and holds
  one exact 53 MiB duplicate draws file; `runs/rw_parse_20260919` is 1.8 GiB in
  21,855 files. Nothing was deleted by anyone.


## 6. Has this hit a ceiling?

No. It is below a floor, which is a better place to be. A ceiling would mean
the documents do not contain the answer. For the three headline quantities
they do, and the pipeline is discarding the sentence that carries it.

The gaps divide three ways, and the division should shape the project.

**Will close.** The whole-process clock, the applicant-facing step count and
the schedule cost, per jurisdiction. The documents state them. The synthetic
one-sentence baseline is at the gate's edge on both programmes. The SolarTRACE
fits already identify per-jurisdiction totals across sixty authorities with a
2.5 to 2.9 times spread. In the real corpus 412 of 2,562 duration statements
with an amount, 22 percent of the fittable set, are typical ranges or
estimates the compiler has no likelihood for, and 93 of them describe the
whole process; the same fix applies at scale.

**Can probably close.** Source bias. C44's agency page says 28 days, its
posters say 90 and more, and the truth is 41. Combining those with a
correction for forum selection and agency optimism is where a Bayesian model
earns its place over an LLM reading sentences. It requires whole-process
evidence and selection on together, which has not been run. Where
administrative data and forums cover the same process (solar, naturalisation,
food benefits, unemployment) the size of the forum bias can be measured and
carried as a prior to processes with no administrative data. I would put the
chance that C29 and C44 pass the gate under that model near two in three.

**Will not close, by any model.** Time in steps nobody reports, hours of
applicant effort, and external cost beyond anecdote. C29's longest step is a
16-day technical review that no document mentions. This is a property of
public documents, and it is a finding in its own right.

The third group constrains the larger goal. Simplifying a statute with least
harm needs the cost of each step, and that is what cannot be recovered. What
can be recovered supports a different route to the same question: compare the
step inventories of many jurisdictions implementing one statute, and relate
the presence of a step to the burden. That is the 58-county design in Dan's
notes, and it needs only the first group.

## 7. Is the project feasible, or misguided?

Feasible, and the question is a good one. The instrument is out of proportion
to the evidence, and the effort is allocated to two open-ended tracks with no
closed loop between them.

- The model carries 150 to 2,500 coordinates and identifies one. A fit takes
  3 to 12 hours. It needs hand-authored structure that exists for 5 of 489
  synthetic processes and 3 real ones.
- The parse has 10,141 rows, none fit-ready, one in five carrying a label
  that would mislead a likelihood, each needing a semantic review, with
  workers on both sides dying on usage limits.
- Neither track has produced one end-to-end number that passes against
  synthetic truth. Until one does, more rows and more draws are not progress.

What would be misguided is continuing both tracks as they are. What is not
misguided: the benchmark, which has now caught a twofold bias that no
convergence diagnostic could; the evidence contract; the hierarchical
cross-jurisdiction design; and V6 itself, run at the granularity the evidence
supports.

## 8. Concrete next steps

In order. The first three are one week.

1. **Commit a snapshot**, with Alex's approval of scope. Two days of work by
   two agents is uncommitted on a disk at 99 percent. Record on disk Alex's
   approval of the two synthetic repairs and a line on the network retrieval.
2. **Stop widening the parse.** Finish the units in flight; open no new
   queues. Redirect review effort to the rows the coarse model uses:
   whole-process durations, counts and totals, perhaps a fifth of the rows.
   Apply Codex's sidecar holds to a consumed view, prefix the colliding
   measurement ids, and require an itemised edit list on every revision.
3. **Close one loop on C29 and C44.** Admit typical-range statements with
   their own likelihood; map "from when I first sat down with the paperwork"
   to the modelled start where the route begins with preparation; forum
   selection on; an agency-optimism term by source type. Gate at 0.7 to 1.4
   with coverage. Score beside two baselines on the same documents: the
   corpus's own sentence, and an LLM. Decide beforehand that if the model does
   not beat the LLM on the clock, the contribution is the benchmark and the
   cross-jurisdiction analysis, and say so.
4. **Run V6 coarse.** A handful of operations per programme needs no
   hand-authored handoff and fits in minutes. That makes all 489 synthetic
   processes reachable. With operations shared across jurisdictions, a learned
   agency spread and Codex's operation-centred sampler, test recovery of the
   planted county spread of 0.37 on a statute with sixty implementations.
5. **Then the real data.** Rerun the 60-jurisdiction SolarTRACE fit under
   step 4, which should turn R-hat 3 into a result. Then the 14 concealed-carry
   authorities with ten or more cases. Then measure forum bias against
   administrative data on the four processes that have both.
6. **Keep the step-level trace model for where steps are observed**, solar
   above all, and report elsewhere that per-step agency time is not
   recoverable from public documents.
7. **Measure onerousness structurally**, from what each form and instruction
   demands, and take applicant hours out of the headline.
8. **Dan's comparison**, decision complexity against recovered burden across
   the synthetic statutes and counties, then across the concealed-carry
   authorities, once step 4 passes.
