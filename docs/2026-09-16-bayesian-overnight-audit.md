# Audit of the overnight Bayesian work (V3–V6), 2026-09-16

2026-09-16, afternoon. Independent audit of the work recorded in
`bayesian-process-v3..v6*.md`, the code under `pipeline/procbench/`, the
generator repairs, and the run artifacts under `runs/bayes_v*`. Six auditors
worked in parallel (numeric claims, V6 code, V4 code and calibration, V5
measurement models, evidence extraction and LLM controls, scoring and
generator). Nothing in the repository was modified by the audit; scratch
outputs are outside the project.

Scale of the overnight work: about 12,900 lines of Python under
`pipeline/procbench/` and 4,450 lines of tests carry a Sep 16 mtime, written
continuously from 00:00 to 12:33. `runs/bayes_v4` alone is 5.9 GB. No W1 file
was modified. No commit exists on the branch.

## 1. What holds up

**Numbers.** All 87 artifacts linked from the four results documents exist.
Every cited number that could be located matches its artifact to the stated
precision, including every posterior median, interval, absolute log error,
interval score, R-hat, ESS, coverage count, compile count and speedup, with
one exception: the "11.3x saved-state microbenchmark" has no artifact anywhere
(recorded speedups are 5.40x and 2.33x). The four interpretation-experiment
fits (4/9/8/7 flagged quantities) exist and are marked unconverged; they are
not yet in `2026-09-16-bayesian-process-v6-results.md`, whose mtime precedes them.

**Freezing discipline.** The reserved J2/S07 posterior's SHA-256 in
`runs/bayes_v4/comparisons/reserved/manifest.json` equals the file on disk;
its fit completed at 12:59:54Z, both sensitivity refits by 13:33:10Z, and the
first gold read is stamped 13:34:09Z. The joint posterior likewise predates
its evaluation by 52 seconds with matching hash.

**No truth leakage.** The extractor globs only
`benchmark/synth/worlds/W1/artifacts/*.md`; the saved `inputs.json` files list
exactly the public documents. Zero hits for `truth/`, `/log/`, `summary.json`,
`/specs/`, `ceiling`, or generator field names in any of the 80 saved prompts.
Codex event logs show no tool use. The LLM control received byte-identical
ledger files (same SHA-256) to the Bayesian fit in both the joint and reserved
comparisons and was asked the same initial-decision median.

**Samplers.** Both hand-rolled samplers are valid MCMC.
- V6 (`bayes_trace_hierarchy.py`): every sampled coordinate is a priori
  standard normal, so elliptical slice sampling needs no Jacobian; the
  likelihood contains no prior terms; the centered duration update is the exact
  prior conditional with the correct MH ratio (verified: individual-claim parts
  unchanged to 1e-15, population part is exactly the correction); the route
  step is an exact finite conditional; hurdle-geometric, discrete-Laplace count,
  contamination and residual kernels all sum to one; batched and scalar
  likelihoods agree in tests and in the three 200-state frozen audits with
  difference 0.0. A flat-likelihood prior-recovery run reproduces N(0,1) on all
  48 coordinates. R-hat/ESS are rank-normalized split R-hat with Geyer ESS and
  match ArviZ to 1e-16.
- V4 (`bayes_hierarchy.py`): half-Normal scale priors moved by ESS and by
  centered log-scale MH with correct Jacobians (derived independently);
  attribution and common-shock moves are exact Gibbs steps; swap and
  redistribute moves are involutive with unit Jacobian; a process total is the
  DAG longest path plus serial hidden stages. The SeedSequence collision
  (`SeedSequence([s,0]) == SeedSequence(s)`) is real: replicate 0's chain 0 was
  initialised at the truth. The fix and the program-local actor key fix are
  both tested.
- V5 (`bayes_process_measurement.py` and siblings): selection normalizer is
  closed-form and exact; per-case integrals use Gauss–Hermite on the
  standardized log scale and are cross-checked against `scipy.quad`; censoring
  uses the Student-t survival function; the outcome mixture conditions
  known-outcome stories without counting them toward prevalence and uses a
  Binomial on admissible admin counts only.

**Scorer bug.** Real and correctly repaired. The old predicted end-to-end
values equal the sum of step medians in all 11 saved runs; the current code
reads the explicit process prediction and returns null when absent. The
rescored medians recompute to 1.0750 and 1.3214.

**Generator clock defect.** Real. `simulate.py:127` overwrites `decision_end`
on every repeat decision. Re-running the audit reproduces 111/128, 74/74,
17/21 and the 74/0/45 repeat counts. The clock-extension verification reruns
in 0.2 s and reproduces all 600 cases and every legacy summary field. All 79
W1 truth files carry a Sep 15 mtime.

**Real-corpus leak fix.** `pipeline/priors/compare_models.py` now trains the
global comparator on the other keys; 44 keys, global 0.7050 vs hierarchical
0.9708, coverage 38/44.

**Tests.** 326 pass in 11 s (327 with the generator test; one benign
warning). The simplified TikZ package audits 20 nodes, 20 definitions, 38
edges and compiles.

## 2. What does not hold up, ranked

1. **Extraction lineage was changed after the fact and not disclosed.** All
   three extraction runs' first responses (`attempt_0.json`) failed the
   validator at the time (fee claims lacking case IDs, a self-loop rework, a
   decision-merge rule, and for J2/S07 a quote that was not verbatim because
   it sat inside italics). The validator was then loosened
   (`evidence_contract.py:86` strips emphasis; `:108` allows self-rework;
   `:127` narrows the case-ID rule; the merge rule is gone) and the rejected
   `attempt_0` files were imported unchanged into `extraction/*_first_validated/`.
   Everything downstream (granularity, context, clocks, every fit, every LLM
   control) consumed those, while `2026-09-16-bayesian-process-v4.md` documents commands
   that name `extraction/J1__S03/evidence.json`, a different file with a
   different hash. The repaired `attempt_1` ledgers exist and are unused; no
   selection criterion is recorded. No gold was seen, so this is a provenance
   defect, not contamination, but it must be recorded before any result is
   quoted.

2. **"0 of 146 claims compile" is mostly configuration, not text.** Both v6
   compilation runs have an empty policy block. Of the rejection reasons: 123
   are `case_sampling_assumption_not_declared`, which the existing
   `--assume-case-sampling` flag resolves; 92 are `unmodeled_duration_basis:unknown`,
   where `audit_visit_observations.py:63-66` *instructs* the LLM to emit
   `unknown` for "task name plus duration" and `compile_visit_durations.py:65-66`
   then rejects it; 35 are clock boundaries because the compiler's `EVENTS`
   list (`:22-23`) is narrower than the audit schema it consumes, which is why
   the single most informative claim in the corpus, the S01 dashboard median
   over 182 cases, is unusable by construction; 24 are business-day calendars
   for want of a declared 5/7 convention. Declaring policy compiles 5; adding
   the calendar 7; accepting `unknown` through the residual mixture 93; adding
   the missing events 102 of 146. Example: "Staff review the file internally.
   Review takes a few months" from the program page, encoded [2,4] months, is
   rejected as basis-unknown and typical-range.

3. **The V5 selection variant is a prior-determined discount.** Selection
   strength κ has posterior 1.12 [0.10, 3.25], 1.14 [0.11, 3.29], 0.90 [0.09,
   2.76] on S01/S03/S07 against a prior of 1.01 [0.09, 2.94]: unidentified.
   The "with selection" medians equal the no-selection medians times
   exp(−0.48σ) to within 2–8%. In the recovery grid the generator uses the
   same family with σ known, and the κ prior alone supplies about 60% of the
   correction at n=10 (E_prior[shift] 0.25 of the 0.43-nat bias). The
   defensible statement is "a misspecified ascertainment model's bias does not
   shrink with n"; the documents' framing that the data adjudicate between
   variants is not supported. On the real programs the discount worsened S01
   and S03 and improved S07.

4. **Hard-coded hyperparameters, set while inspecting the same three
   programs, drive the headline comparisons.** V5: cohort-offset prior SD 0.6
   at `bayes_process_measurement.py:238` is undocumented and makes the n=182
   dashboard median informative only to about ±1.8×, which is why S01 lands at
   98–117 rather than near 122; contamination 0.08, source 0.35, preparation
   0.10, coverage Beta(1,1), t(4). V6 fixes `report_sd=.25`, `contamination=.05`,
   `count_error_scale=.5`, `common_case_sd=.25` and, unlike V4, fixes the
   hierarchy scales (`agency_sd=1`, `task_sd=.75`, `operation_sd=.5`) rather
   than learning them. Every "Bayes vs LLM" number is therefore in-sample on
   the Bayesian side and zero-shot on the LLM side.

5. **The pooled 96-replicate calibration mixes a clean batch with an
   anomalous one.** Batch 1 (seed 68210) has global-location ranks
   [6,9,9,8,1,5,1,2,4,3], KS p = 0.0007, mean rank 0.37; batch 2 is flat
   (p = 0.61). The kernel diff between the batches does not explain it. Three
   of the five functionals are scored from fits that fail the protocol's own
   diagnostics (52/69/70 of 96). The SBC fixture is a single fully-ordered
   nine-step chain with one graph variant, no population claims, no gates, no
   outcomes: it exercises the timing core only. The clean evidence for the
   current sampler is batch 2 alone. A cheap decisive check is to rerun seed
   68210 with current code.

6. **The interpretation-hypotheses import cannot run for J2/S07.** The three
   saved Codex responses are schema-valid and source-only, but full
   validation fails for S07 on `M25_H1`/`M54_H1`: a parent operator with
   `visits=all_completed_by_observation` can never be refined to a
   single-visit reading because `audit_visit_hypotheses.py:129-132` forbids
   changing `visits` while `audit_visit_observations.py:119-120` requires it.
   The event-validation fix is real and narrow; none of this is documented.

7. **The default generator no longer regenerates W1 from seed 1.**
   `world.py:56` defaults `visit_accounting_version` to 2; W1's `world.json`
   lacks the key and records no generator version. Reproducing W1 requires
   `--knob visit_accounting_version=1`.

8. **Rendered artifacts contradict the truth on actors more widely than one
   staff report.** The S03 staff report assigns completeness and technical
   review to Revenue (truth: Permit Services and Building); the renderer
   invented this from `lead_department` because the spec disclosed no actor,
   and verification checks required facts and leaks only, so it cannot catch
   invented actors. Across the 1,315 specs: 6 fee-resolution agency
   mismatches (`visibility.py:373` discloses `lead_department` for every fee
   step), 4 program-page specs whose "actor" for the decision step is a fee
   string (`visibility.py:298-299` with `local_rules.py:497-509`), and 18
   payer steps disclosed with an agency name. Separately, the S01
   official-statistics document is a rendering of the truth summary (200
   received, 137 issued, 37 denied, "about 4 months" from 182), so the LLM
   control's 140 days is essentially that anchor plus preparation.

9. **Scorer residue.** Process-level `process_timing` is never checked for
   `kind`, so a statutory cap written as `median_days` scores as a realized
   duration (`align.py:231-238`); `score.py:33` says version 3 while the
   rescoring file and docs say 2; `_sum_medians` is dead code; `_find_median`
   is dict-order dependent. The v2 timing semantics are covered only in
   `tests/test_bayes_process.py:48-63`, not the three test files the docs
   name.

10. **V6 robustness.** An absent clock event on a route raises
    `ValueError` from `compact_visit_trace.py:138-139`, which the likelihood
    does not catch (`bayes_trace_hierarchy.py:396-410, 452-470` catch only
    `KeyError`), contradicting the protocol's "absent → residual mass"
    semantics; malformed operators become silent −inf with a misleading
    error; a route sampled at frequency exactly 0 or 1 in all chains passes
    convergence because `_rhat` returns 1.0 when within = between = 0.

11. **Numerical gates that carry no statistical content.** The 0.01-nat
    quadrature threshold is one to two orders of magnitude too strict (an
    error of 0.03 nats reweights posterior density by 3% against posterior
    SDs of 0.35 nats); the 200-state scan under-reports the maximum (0.031
    scanned vs 0.099 over all states); the 1,024-node "refit" is the same
    trajectory as the 512-node run (identical draws and call counts), a valid
    coupled realization but not a replication. Several hours of the night went
    to refits triggered by this gate.

12. **Smaller items.** The ambiguous-completion mixture is applied per
    observation rather than per case (`bayes_process_measurement.py:295-307`;
    latent, no effect on current data). The partial-preparation coverage prior
    is a 1/P soft lower bound, not "uninformative". The LLM control never
    produced the requested p90 (null in 15 of 15 responses), so Bayesian p90s
    have no counterpart. The "140/140/140" repeats are stochastic decoding
    (all 15 raw responses differ; intervals vary), n = 3, on a ledger with a
    strong anchor. V4's undocumented-stage mechanism can only lengthen totals
    and there is no move that merges or deletes a represented operation,
    which the documents state accurately.

## 3. Why the work is not converging

The night produced four model generations because each one exposed a defect
in the measurement contract or the benchmark rather than in inference. That is
informative, but it also means the acceptance criterion was never reachable:

- **There is no valid evaluation left.** Three programs, all now development
  data; the truth clock is last decision while both estimators target first
  decision; one of the three programs ships a document that is the truth
  summary. A median from 174 cases has its own log-scale sampling error of
  roughly 0.06, so differences such as 0.089 vs 0.097 are inside the noise of
  the target.
- **The criterion measured the wrong thing.** A Bayesian layer can only beat a
  well-anchored LLM point estimate through calibrated uncertainty, pooling
  across agencies and programs, or selection correction. On three programs
  with about nine forum cases each and no shared named department, pooling has
  nothing to pool, selection is unidentified, and only calibration remains,
  which the interval scores already show. "Not better on point accuracy" was
  overdetermined before any code was written.
- **Strictness was applied on the wrong side.** The compiler enforces "no
  unstated assumptions" by rejecting, so coverage went to zero, while the LLM
  control makes exactly those default assumptions implicitly and scores well.
  The model needs declared default interpretations with priors, not
  refusals. The generator knows the true operator behind every rendered
  persona and dashboard claim, so those priors can be calibrated rather than
  guessed, which is the piece that has been missing since before the overnight
  run.
- **Iteration is too expensive.** Fits of 40–96 minutes on ten cases, a
  hand-rolled sampler with more than fifteen bespoke moves, self-written
  diagnostics, and an over-strict numerical gate meant a large share of the
  night was spent proving the sampler correct rather than learning about the
  problem. The auditors confirm the sampler is correct; that certainty was
  bought at the cost of the comparison.

### Is the model overspecified? Measured, yes, in this data regime

Alex asked whether there is any way to fit so many latent parameters. The
saved fits answer directly. Every sampled coordinate has a standard-normal
prior, so one minus its posterior variance is exactly the fraction of prior
uncertainty the data removed. Latent dimension versus information:

| Fit | Latent coordinates | Observations | Cases | Coordinates with under 10% learned |
|---|---:|---:|---:|---:|
| V6 mixed evidence (integration, extended) | 302 | 41 + 2 cohorts | 13 | 199 (66%) |
| V6 timing only (integration, extended) | 302 | 13 | 13 | 259 (86%) |
| V4 S03 single program | 381 | 51 | 9 | 323 (85%) |
| V4 joint S01 + S03 | 874 | 95 | 18 | not computed |

Per block in the V6 mixed fit, the favorable condition: the three global
locations are 78–85% learned, the any-correction probabilities 93%, the
continuation probabilities 15–30%, the case spreads 23–34%. Everything that
makes it a hierarchy is at prior: agency effects 13% (24% on the elapsed
channel, 5% and 10% on the two hours channels), task effects 9%, operation
effects 9%, the 39 source offsets 8%, the 208 per-case coordinates 6–13%. In
the timing-only condition the model learns two things, the elapsed location
(84%) and the elapsed case spread (32%); agency effects reach at most 14%,
and the two labor channels, with no observations, sit at exactly 0%, which is
what the audit's "0.037–118 hours" payer interval was.

This is not a sampler or code defect. It is the regime: two programs, three
actors, four task types, thirteen cases. The design cannot move agency
effects because each agency performs a disjoint task set (the agent's own
SVD audit said so), and it cannot move source offsets because each of the 13
source families contributes one case. The V4 "agency propagation works"
result is real but came from a fixture built with three measured tasks per
agency. On the W1 ledgers the same block never left its prior. The reported
agency cycle times, per-operation timings and work hours are therefore
priors presented as posteriors, and the hyperparameters that govern them
(fixed constants in V6, weakly identified half-Normals in V4) are doing the
work.

What follows for the design:

- **An identification report with every fit.** One minus posterior variance
  per coordinate, grouped by block; any block under about 25% learned is
  labeled prior-determined and excluded from headline outputs. This is a
  ten-line addition given the whitened parameterization, and it would have
  flagged every overstated quantity in the V4 to V6 results documents.
- **A pre-fit identifiability check.** Linearize the likelihood at the prior
  mean and compute the expected information per block (the SVD design audit
  generalized to all blocks). Blocks the data cannot move are fixed at
  calibrated values and declared, not sampled.
- **Marginalize the case latents.** The 208 per-case coordinates are random
  effects; V5 already integrates its case duration by quadrature. Doing the
  same for the elapsed channel in V6 cuts the sampled dimension by two
  thirds, speeds the fits, and removes nothing the data could learn.
- **Do not carry channels with no observations.** A timing-only fit should
  not sample a hundred labor coordinates.
- **Match the model to its regime.** The hierarchy earns its parameters only
  when programs, agencies and sources are numerous enough to be pooled. For
  one program and ten documents, a two-parameter model (location and spread)
  with a calibrated interval is the honest Bayesian model, and it is roughly
  what the LLM baseline already computes in context.

The four items above change what is reported and how fast a fit runs; they
do not make anything more learnable. What W2 can supply is the reading
layer's error rates and a check that the machinery recovers known parameters
when a design is identifiable; it cannot say how much real agencies vary.
Some quantities are not learnable from public text about one program at any
document count: agency versus task effects when each agency has its own
task set; selection strength from selected anecdotes alone; staff hours from
elapsed days; source offsets with one case per source family; continuation
probability without observed repeat rounds. The ways around are changes to
the data design and the question, not to the estimator:

1. **Pool by design.** Choose real programs by agency overlap (Building does
   plan check for ADUs, solar and restaurants; EDD and DMV recur across many
   threads). Fifty programs sharing a dozen agencies is the regime in which
   agency effects exist as data.
2. **Fetch by estimand.** Population timing comes from official statistics,
   audits and records requests, where one unselected sample outweighs a
   hundred forum stories. Forum text's comparative advantage is structure:
   steps, rework, actors.
3. **Ask what the design can answer.** Report (agency, task) cell means,
   identifiable wherever a cell has data; decompose into agency and task only
   where the design crosses. This matches the earlier finding that
   conditioning on step kind cut error 46% while the hierarchy did not
   transfer.
4. **Retrieval as value of information.** The identification report gives
   the learned fraction per block; the expected gain from a candidate
   document is computable before fetching it. A new (agency, task) cell or a
   new source family is worth much, a fourth report of the same case nothing.
   The search agent should choose documents to move unlearned blocks, a
   capability the LLM baseline lacks.
5. **Use the prior harvest as the hyperprior.** `pipeline/priors/` already
   pools real reddit and reporting timings over the six-dimensional step key
   with empirical-Bayes shrinkage. V6's agency and task hyperpriors should
   come from there; it is built and not wired in.
6. **Partial identification is the deliverable.** A posterior that places an
   agency effect between 0.4 and 2.4 times baseline is a correct answer; the
   LLM point estimate hides the same ignorance. The model's value is that it
   states what it did not learn and what to fetch next.

## 4. Where ambiguity should live: the LLM versus the model

Agreed with Alex on 2026-09-16 after the audit. His framing: behind every
thin rule is a thick rule cleaning up after it, and the Bayesian model is the
thin rule here. The audit confirms it. The model holds almost no semantic
ambiguity: the LLM decides once, deterministically, what each sentence
measures, which step it belongs to, which agency did it, and whether two
mentions are the same operation. The model then receives a fixed inventory
and a fixed typing and can only wobble within it (which of two listed routes,
whether a report is contaminated, a 50/50 clock mixture). V4's own results
document says nothing in the posterior can merge or delete a represented
operation and that actor aliases are fixed upstream. The thick rule is the
Codex audit chain, about 255 cached calls, and it is unmeasured: no error
rate, no calibration, its outputs treated as facts. When the compiler met an
output it could not type, it rejected the claim, which is how coverage
reached zero.

The overnight principle "never use LLM confidence as a probability" was
defensible, but the alternative chosen gave the LLM no way to express
uncertainty at all. The fix is not to move semantics into the likelihood. It
is to make the thick step measurable and let its measured error enter the
model as a mixture weight. By kind of ambiguity:

| Ambiguity | Who resolves it | Why |
|---|---|---|
| Parsing and typing: value, unit, statistic kind, actual vs normative, document family | LLM, upstream, top reading only | Single-document judgments; the text usually settles them |
| Duration basis (one cycle vs cumulative vs span) and clock boundaries (preparation vs filing start; first vs last decision) | Model holds a mixture over 3–5 readings; weights learned, not declared | The text genuinely underdetermines these; the generator knows the true reading behind every rendered claim, so W1 is a labeled confusion matrix |
| Step identity ("are these the same step") | Model holds enumerated merge hypotheses; LLM k-vote frequencies, calibrated, are the priors | Noisiest judgment in the pipeline: two reasonable aligners agree at Jaccard 0.37 and recall moves 23 points. Cross-document by nature. V3 held an open partition and overcounted; V4–V6 froze the inventory and still overcounted; neither calibrated the pairwise same-step likelihood |
| Agency identity | LLM emits a distribution over a closed set (the jurisdiction's org chart, retrievable); model holds the categorical | Text evidence is thin (a rendered staff report contradicts the truth); a closed set makes the uncertainty representable |
| Source bias, same-case sharing, selection, censoring, pooling across programs and agencies | Model | This is where it earns its keep. An LLM aggregates ten documents in context nearly as well (140/80/28 showed it); it cannot aggregate two hundred posts, share one case across three reports, or borrow strength across programs |

That last row is part of why nothing improved: the model was tested in the
LLM's regime, one program and ten documents, instead of its own.

**Decision rule, per ambiguity class.** On W1, measure the LLM's top-reading
accuracy against the generator's truth. Where it exceeds roughly ninety
percent, resolve upstream and keep the model thin. Where it does not, hold
the mixture with the measured confusion matrix as weights, and check that the
mixture posterior beats the top-reading posterior on timing and counts. This
replaces taste with measurement, and it turns the compiler from a gate into a
translator that never drops a claim.

## 5. Unification plan

1. **One model.** Freeze V6 as the only model. Fold in the two things it
   lacks from V4 and V5: learned hierarchy scales (half-Normal priors on
   agency/task/operation SDs) and the outcome mixture with censoring. Keep V5's
   selection weight as a sensitivity knob, never as a variant. Retire V3;
   keep V4 and V5 directories as archived controls.
2. **Probabilistic compiler, 100% coverage.** Every eligible claim maps to a
   mixture over operators (single cycle, cumulative cycles, span, wait,
   service, residual) with weights from §4; a corpus-level policy file
   declares sampling, calendar and event conventions once; the compiler's
   event vocabulary equals the audit schema. A claim is never dropped; at worst
   it lands on the residual. Step-identity merges enter as enumerated
   inventory hypotheses with k-vote priors; agency identity enters as a
   categorical over the org chart.
3. **Calibrate interpretation and extractor error on the synthetic world.**
   Build the labeled set (rendered claim → true operator, true clock, true
   actor, true activity id) from the W1 specs and render log; estimate the
   confusion matrices per ambiguity class; apply the §4 decision rule to
   decide which classes stay upstream. Those matrices become the compiler's
   mixture priors and the model's ε. Report them as measured quantities with
   uncertainty, and re-measure them on every new world.
4. **Port V6 to NumPyro or Stan.** The model is about fifty whitened Gaussian
   coordinates plus a finite route variable that can be enumerated. NUTS fits
   this in seconds, standard diagnostics replace the bespoke ones, and
   simulation-based calibration becomes a few hundred cheap replicates, which
   resolves the batch-1 anomaly one way or the other. Keep the current
   implementation as the likelihood reference and require equality at saved
   states.
5. **A fresh benchmark W2 built for identifiability.** Ten or more programs;
   agencies that perform several task types across programs (crossed design);
   explicit first/last/closeout clocks; labor truth; rendered actors verified
   against truth; official statistics rendered noisy or withheld; half reserved
   and never opened until the model is frozen.
6. **A pre-registered criterion the Bayesian model can actually win.**
   Coverage and interval score across all programs; transfer accuracy on
   programs with no timing documents but shared agencies; count and labor
   accuracy where evidence exists; matched LLM controls on the identical
   mixture ledger. Point accuracy on well-documented programs is reported but
   is not the criterion.
7. **Housekeeping before any of the above.** Record the extraction lineage
   (which attempt, which validator) or rerun with the repaired ledgers; pass
   the compiler policy and fix the `unknown`-basis contradiction; resolve the
   S07 hypotheses contract; write the generator version into `world.json`;
   check `kind` on process-level timing in the scorer; catch `ValueError` in
   the V6 likelihood; replace the 0.01-nat gate with an importance-ESS
   criterion; add the four unconverged interpretation fits to the v6 results
   document. Then commit, with Alex's approval, since nothing on the branch is
   committed and `runs/` is gitignored.

## 6. Code health: sprawl and duplication (measured 2026-09-16)

**Inventory.** `pipeline/procbench/` holds 81 files and 14,647 lines, of which
58 are command-line scripts and 35 are imported by nothing else: one-off
experiment drivers. By prefix: 12 `audit_*`, 10 `bayes_*`, 6 `validate_*`,
5 `run_*`, 4 `compare_*`, 4 `extend_*`, 3 `generate_*`, 3 `check_*`,
2 `summarize_*`. Four model generations coexist as peers (`bayes_process`,
`bayes_hierarchy`, the four-file `bayes_*_measurement` family,
`bayes_trace_hierarchy`), each with its own run, extend, check, compare and
validate drivers. That multiplier, not copy-paste, is the sprawl. A reader
cannot tell library from experiment or current from archived. Tests are 42
files and 5,085 lines with no `conftest.py`; one generator test lives outside
`tests/`. `runs/` is 7 GB, of which 229 `draws.npz` files are 3.6 GB; all of
it is gitignored, so the experimental record the documents link to exists only
on this laptop. There is no `CLAUDE.md`; conventions live in chat memory.

**Verbatim duplication is low.** Only 35 distinct six-line windows appear in
more than one file, almost all among the `audit_*` scripts
(`audit_burden_counts` vs `audit_visit_observations` share 14;
`audit_case_outcomes` vs `audit_preparation_clocks` share 10).

**Structural duplication is high.** The same concern is re-implemented per
script instead of once:

| Concern | Files | Note |
|---|---:|---|
| Codex subprocess runner (`codex exec`, JSONL events, cache, hashes) | 11 + `pipeline/llm.py` | `llm.py` is unused by procbench and has different defaults; it misleads |
| Quote normalization and verbatim check | 11 | The post-hoc loosening in §2.1 had to be made in one copy and is absent from others |
| Manifest writing (`started_utc`, `completed_utc`, sha256) | 13 | Schemas differ: v4 manifests record `seconds`, v6 do not |
| Interval score and absolute log error | 8 | One named function, seven inline copies |
| `Config` dataclass | 8 | One per model; acceptable only once the models are archived |
| `worker` multiprocessing shim | 4 | |
| Sobol or Gauss–Hermite quadrature setup | 5 | |

The earlier-phase modules at the top of `pipeline/` (`executor`, `looseness`,
`screener`, `simplify`, `worlds`, `instrument`, `run`) are the discretion and
metric-seam workstream, imported through `sys.path` manipulation. They are not
dead, but they share a directory with procbench with no package boundary.

**Recommendations, in order.**

1. **Commit first, refactor second.** Nothing on the branch is committed.
   A snapshot commit of the current tree makes the refactor reviewable as a
   diff and gives a revert point; the rename scripts earlier today had none.
   Needs Alex's approval.
2. **Package layout.** Under `pipeline/procbench/`: `model/` (V6, the kernels,
   compact trace, operators), `evidence/` (contract, reconcile, one audit
   module per schema sharing one runner, compiler, hypotheses, baseline),
   `infra/` (`codex_runner.py`, `manifest.py`, `quotes.py`, `scoring.py`,
   `quadrature.py`), `experiments/` (one CLI with `fit`, `extend`, `refine`,
   `check`, `compare`, `sensitivity` subcommands replacing the 20 driver
   scripts, plus `validation/` for the SBC and recovery harnesses), `legacy/`
   (V3, V4, V5 and their drivers, frozen and import-stable so saved runs
   replay), `bench/` (score, align, metrics, web, solve, incremental).
3. **One runner, one manifest, one scorer.** Extract the three shared modules
   before anything else; every audit, fit and comparison imports them. Fix the
   manifest schema once (timings, input and source hashes, config, seeds, the
   `hidden_truth_read` flag). Add a unit test that the interval score is the
   Gneiting–Raftery form.
4. **Promote hidden constants to config.** Every number in §2.4 (report SD,
   contamination, cohort offset SD, hierarchy scales) becomes a `Config`
   field, so it is recorded in manifests and visible in sensitivity runs.
5. **Test scaffolding.** A `conftest.py` with a small V6 dataset fixture and
   a fake Codex runner; move the generator test into `tests/`; keep the suite
   under fifteen seconds.
6. **Separate the workstreams.** Move the discretion modules to
   `pipeline/discretion/` with package-relative imports; drop the `sys.path`
   inserts.
7. **Archive policy for `runs/`.** Keep manifests, `posterior.json` and
   `comparison.json` in the tree or in a small tracked archive; move
   `draws.npz` to external storage with hashes recorded in the manifests. Add
   `runs/README.md` saying which directories the documents depend on.
8. **`CLAUDE.md`.** Naming with dates, no commits without approval, no
   inference code reads `truth/`, where each workstream lives, the runs
   archive policy, and the §4 ambiguity split.

Steps 2 through 6 are mechanical with the test suite as the safety net, about
a day of agent work; the only replay risk is import paths, which the saved
source snapshots in each run directory already insulate against.
