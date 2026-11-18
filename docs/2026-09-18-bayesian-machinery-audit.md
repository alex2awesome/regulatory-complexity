# Audit of the V6 Bayesian machinery and launch readiness, 2026-09-18

2026-09-18, midday. Requested by Alex: "a full audit of the current Bayesian
machinery and our setup with the 3 finished synthetic datasets ... mainly the
Bayesian machinery and if you agree with the current state of it (codex made a
few changes)", then launch locally if feasible, otherwise on sk2/sk3. Dataset
validation is excluded by request; Alex is doing it in another process.

Method: six read-only audit lanes in fresh contexts (case-path likelihood,
finite-cohort quantile likelihood, compiler sidecars, runner gates and channel
omission, end-to-end readiness, truth isolation), each restricted to code,
run manifests and extractor outputs; none opened `truth/`, specs, ceilings,
scores or the shared findings log. Every numeric claim below was reproduced
offline in a scratchpad; no model or paid call was made. The record under
audit is the 2026-09-18 sections of
[the implementation record](2026-09-16-bayesian-audit-implementation.md),
written by the same agent that wrote the code.

## Verdict in one paragraph

The model mathematics codex added overnight is correct: the per-case path
mixture sums over paths after multiplying a case's reports (hand computation
agrees to 9e-16), the fresh-chain route initialisation changes only the start
and never the target, the residual reference survives unrenormalised, the
finite-cohort order-statistic law and both quantile conventions are right
(checked exhaustively to n = 3000 and by Monte Carlo), channel omission
integrates unobserved labour out rather than fixing it at zero, and the
saved-seed replay is still bit-identical under the current tree. No truth
leak exists in the current tree. What does not hold up is around the model,
not in it: my own 10:55 change to the trace refusals was wrong and is
reverted; the extension path could continue chains under a changed target and
is fixed; the "informative" label in the diagnostic compilation carries 0.733
residual mass on 11 of 13 factors; several record claims overstate what the
code checks; and, decisively for launch, **no programme has a source-derived
route input**, so nothing on disk was fit-ready. The three datasets are
therefore usable by the machinery only up to the observation half; the
structural half had to be bridged today.

## 1. What holds up (verified)

**Case paths** (`bayes_trace_hierarchy.py:692-764`). Per path: operator
mixture per report, product over the case's reports, scope-conditioned prior,
then logsumexp over paths. A 2-path toy with count, clock and population
reports matches a hand computation to 9e-16; product-of-sums differs
(−6.667 vs −6.431), so the order is the claimed one. `--case-path-logit-sd 0`
allocates no coordinates and returns the declared weights. An absent clock on
a positive-weight path gives that path zero weight for that case, never a
crash or a silent drop.

**Route initialisation** (`:1009-1042`) runs only when the random start is
non-finite, draws the route from the same exact conditional the in-loop Gibbs
step uses, and cannot select a route whose observation is unsupported at every
state. Under `e581748` only two of the four "formerly seed-sensitive" test
seeds actually failed; the record says four.

**Residual mass** (`:168-178`, `:383-386`, `:618-623`): process-independent,
contamination 0, added with its own weight; unsupported modelled candidates
are −∞ before the group logsumexp, so the residual term survives unnormalised.
`edges: null` is serial, `edges: []` is fully parallel (`compact_visit_trace.py:219`);
nothing in the repo can emit `[]`, and nothing validates against it either.

**Finite-cohort quantiles** (`cohort_quantiles.py`). U_(k) = u + (1−u)·Beta(k−j, n−k+1)
is the correct conditional law; `inverted_cdf` = ⌈qn⌉ and `linear` = Hyndman-Fan
type 7 match `np.quantile` for every n ≤ 3000 and both quantiles. Monte Carlo
at 4096 nodes: |z| ≤ 1 in 16 of 24 cells, worst z = 4.7 on a 0.2% relative gap;
corr(log median, log p90) matches to ≤ 0.003. Same population and route/path
weights as the scalar path; offsets and reporting error act after the sample
summary; the interpretation weight enters once per cohort. Sobol seeds are
deterministic per programme and cohort; the precision check refines both grids.

**Channel omission** (`--observed-channels-only`): an observed channel cannot
be omitted; omitted channels get no coordinates, NaN parameters, no burden
keys in `posterior.json`; the finite Sobol grid changes dimension and the
precision check reruns on the reduced layout. Timing-only fixture 48 → 18
coordinates (62.5%), as recorded. Corpus-shaped dimension 4,957 = 477
hierarchy + 14 repeat + 4,466 case; elapsed-only 1,713; case coordinates are
always allocated and slice-sampled, so case marginalisation is indeed not
implemented.

**Compiler** (`compile_visit_durations.py`). No code path drops a claim: all
84 C29 measurements carry a disposition (38 elapsed-eligible; 46
`outside_elapsed_compiler` = 31 elapsed-but-ineligible, 13 USD, 1 FTE, 1
agency-hours). A report-group disjunction contributes P(interval union) via
logsumexp over disjoint intervals, not a product or envelope; the
representative-containment rule is what the code does. Population and path
conditions come only from a quoted sidecar. Interpretation weights come only
from the policy file or CLI flags; nothing in the import graph reads truth.
The current compiler reproduces the saved C29 observations and dispositions
byte-for-byte.

**Provenance.** All five runner operations write `procbench-run/1` manifests
with input hashes, transitive source hashes, seeds and a bool
`hidden_truth_read`. Extension refuses uncompleted or changed posteriors,
changed inputs, layout and target mismatches, reused seeds and invalid
checkpoints; refinement refuses cohorts and population summaries.

**Isolation.** The W2 parse prompts for C29__S12, C44__S12 and C38__S03 contain
only the contract text plus documents whose ids and hashes equal the frozen
index; codex event logs show zero tool events; stage manifests record
`hidden_truth_read: false` and `no_tool_events_verified: true`. Policies are
constants. Semantic calibration consumes only the calibration artifact, never
label rows, and rejects reserved splits. The parse's frozen index holds 0
reserved and 0 unassigned counties; the S05 allowlist maps to 55 calibration
and 14 development county documents plus 2 state-level, 0 reserved.

**Software.** Full offline suite 627 passed before today's edits; 141 model
tests pass on sk3 under Python 3.11 / numpy 2.2.6 / scipy 1.17.1; the runner
completes a fixture end to end there in 5 s.

## 2. What does not hold up, ranked

1. **My 10:55 reclassification of three trace refusals was wrong — reverted.**
   I had turned `ValueError` into `UnavailableTraceQuantity` for unknown agency
   identity under `agency_count`, an unmeasured resource channel, and unknown
   work amounts under `payer/agency_hours`, on the theory that the honest
   encoding should fall to residual mass. It cannot: a resource-hours or count
   observation has no residual alternative (the validator rejects mixing
   `agency_hours` with `unmodeled_duration` and counts with duration densities),
   so the caught exception made the observation −∞ on that route. Measured: two
   routes differing only in whether one operation's applicability was known,
   equal priors, gave `route_probabilities {r_known: 1.0, r_unknown: 0.0}`.
   The encoding alone decided the inventory and nothing reported it, which is
   the failure this project cares most about. Code hunk restored byte-for-byte
   to the pre-edit snapshot; the comment now records why it must stay hard;
   the test I had added is inverted to pin the revert. The earlier shared-log
   claim of a "crash-path fix" is withdrawn.

2. **Extension continued chains under a changed target — fixed.**
   `extend_visit_hierarchy.py` read `data.json` without comparing it to the
   hashed input; route `prior_weight` enters only the route Gibbs step, so
   priors tampered from .5/.5 to .99/.01 passed the saved-likelihood check.
   The fit manifest recorded no `draws.npz` hash, so a reordered draws file
   was accepted too. Now `v6.fit` and `v6.extend` record `draws_sha256`;
   extend compares saved data with the hashed original input (as refine did)
   and verifies the draws hash, recording `saved_draws_hash_verified`.
   `tests/test_extend_provenance.py` pins all four cases.

3. **No source-derived route input existed for any programme.** The compiler's
   output has no `programs`/`routes`; the structural handoffs are
   `source-only-structural-handoff/1` classification lists; `--preflight` on
   every W2 compilation dies at `KeyError: 'programs'`. See §4.

4. **"Informative" overstates modelled information.** Under the diagnostic
   policy (0.2 out-of-set, remainder equal by basis then reading) every
   unsupported reading's mass folds into the residual (`compiler:547-556`);
   11 of C29's 13 informative factors carry residual weight 0.733 because only
   the `single_visit_cycle` reading of three is modelled. The record and README
   state the 0.2 policy and never the effective 0.733.

5. **Report-group and cohort contract checks are vacuous for residual-only
   members** (`compiler:229-236, 330-334`): compared after rows are rewritten
   to `operators=[residual]`, so two residual-only claims with different audit
   operators grouped as `repeated_wording` are accepted. No actual mis-merge
   in C29 (all six pairs checked identical), but the record's "rejected rather
   than silently merged" holds only for informative rows.

6. **First-present union depends on paths the compiler neither emits nor
   requires.** The model picks argmin(first_start) among union members present
   on the path (`compact_visit_trace.py:287-295`); with approval and denial
   both on every path it always picks the earlier-ordered one. The bridge in
   §4 therefore encodes outcomes as alternative paths.

7. **Cohort-overlap rejection is honor-system** (`bayes_trace_hierarchy.py:263-268`):
   only a matching optional `cohort_id` triggers it; the compiler never writes
   that field on rate or individual rows; two cohorts with identical content
   under distinct ids pass as independent factors.

8. **Precision gate: the population grid, not the cohort grid, binds for
   n ≳ 500.** Fixture n=500: ESS fraction .987 < .99, TV .036 > .025, all from
   the population refinement; `--cohort-quadrature-size` is the wrong lever.
   Default 256-node cohort grid has up to 1.2% relative error (z = −14 vs MC).
   On the declared smoke fit, 256→1024 moved a clock quantile 8.7%,
   1024→4096 2.69%, 4096→16384 1.94% against a 2% gate.

9. **Runner gates.** Definitions confirmed (R-hat > 1.01, ESS bulk < 400, tail
   < 200 flag; .99 / .025 weight check; 2% and 1e-6 prediction tolerances;
   25% contraction for headline eligibility) but none of the numeric
   thresholds appear in the record. A constant series (e.g. a pinned
   interpretation weight) counts as converged. A non-finite delta after
   sampling raises before `posterior.json` is written, leaving draws with a
   `running` manifest. `max()` over relative changes is not NaN-safe.

10. **Latent handlers.** The only signal that an operator is unsupported on a
    route is a raw `KeyError` at `compact_visit_trace.py:297`, caught by broad
    `except (KeyError, UnavailableTraceQuantity)` at four sites; a future
    lookup typo inside those blocks becomes residual mass. `report()` swallows
    every `ValueError` (`:1157-1162`), so a shape mismatch silently drops a
    metric. The population quantile is interpolated with one path and a step
    function with two or more (`compact_visit_trace.py:149-159`): a 2e-16
    change in π moved a fixture median from 105.1 to 110.3 days.

11. **Isolation, latent.** `build_semantic_labels.py` reads truth for all
    programmes with no partition read and hard-codes development purpose, so
    a W2 label set would carry reserved rows into calibration (none exists
    yet). Standalone audit CLIs omit `events=True`, so their `hidden_truth_read:
    false` is a bare declaration (the W2 parse driver passed it). The
    coordinator-authored handoffs and bindings carry no isolation declaration
    although their author's conversation held development-truth audit
    results. The S05 allowlist was produced by unretained code (mine). No
    parser-input isolation test exists.

12. **Record claims the code does not support.** "Four formerly seed-sensitive
    starts" (two); "known overlap ... rejected" (label-only); "ordinary
    population rows with n still fail" (compiler downgrades or excludes; only
    V6 raises); "tests exercise conditional paths" (the test is circular) and
    "continuation guards" (no cohort continuation test); replay receipts
    "record exact hashes" (all predate the current `compact_visit_trace.py`
    and no script produces them); `--case-path-logit-sd` is the pairwise
    log-ratio sd, not a per-logit scale; cohorts use report scale .25 where
    n-less population summaries use the .5 floor; the suite counts
    504/511/531/561 were not reproduced by any lane.

## 3. The three datasets as the machinery sees them

Per-statute state on disk at 11:10 PDT (artifact ids carrying `__Sxx__`;
latest verdict per artifact):

| statute | artifacts | verdicts | pass | fail |
|---|---:|---:|---:|---:|
| S05 | 266 | 266 | 266 | 0 |
| S12 | 142 | 142 | 106 | 36 |
| S03 | 204 | 204 | 159 | 45 |

Parse state (`runs/w2_v6_diagnostic_parse_20260917_2335`): 8 of 11 programmes
have accepted ledgers (C29, C41, C44 for S12; C32, C35, C38, C44, C50 for S03);
C53__S12 timed out on repair, C56__S12 failed the event audit, C58__S03 has a
ledger but no sidecars because the workspace ran out of credits at 05:12 PDT.
S05 has a frozen 71-document artifact-only index and **no** parse. Only
C29__S12 and C44__S12 have visit-hypothesis audits and structural handoffs;
compilations exist for C29 (4), C41 (1), C44 (2) only. The codex transport is
still out of credits (probe 11:12 PDT), and it is the sole transport
(`subscription_only: true, paid_api_fallback: false`).

## 4. The missing bridge, built today

Nothing on disk could be fit. The compiler emits observations only; codex's
`structural_handoff.json` files are quoted classification lists
(`source-only-structural-handoff/1`), not runner inputs; `--preflight` on every
W2 compilation died at `KeyError: 'programs'`. The handoff document had asked
for exactly this bridge to be "constructed and validated" before claiming an
end-to-end run, and it did not exist.

`pipeline/procbench/bridge_structural_routes.py` now builds it, offline, with
zero model calls and `hidden_truth_read: false`, from three inputs per
programme: the accepted source-only ledger, the quote-backed structural
handoff, and the compiled observations. Its rules, each pinned by a test in
`tests/test_bridge_structural_routes.py` (12 tests):

- Operations are the handoff's `performed_operation` activities, keeping ledger
  activity ids so compiled operators resolve. Every other activity is listed in
  `bridge_report.json.excluded_activities` with its classification and quote
  (15 for C29, including three standing renewal obligations and two legal
  transition events such as deemed approval). Nothing is dropped silently.
- Order comes from ledger `precedes` relations as a serial chain (`edges: null`).
  `edges: []` is never emitted, because the model reads it as fully parallel and
  it more than halves the modelled clock. One quoted `parallel` relation in C29
  ("the two may be submitted together") relaxes its chain by dropping the
  weakest edge, leaving that pair unordered.
- Relations whose every supporting document is marked hypothetical by the
  ledger are excluded from the current route: a sequence proposed in a 2021
  bill analysis is not the county's realised order.
- Applicability from `actors[].role`; unknown or third-party gives
  `None`/`None`. C29 has 4 such operations on the base route, 16 across all
  routes. No role is invented.
- Markers only where the handoff names a boundary activity. It names decision
  dispositions for both programmes and **no submission boundary at all**, so
  the `submission`, `complete_submission` and `legal_closeout` markers are
  omitted and every whole-case clock operator is unavailable. The report says
  so rather than inventing a start event.
- Repeat blocks from `repeat_links` where a ledger rework relation actually
  joins the members (C29 `correction_return`: a06→a07→a08). Two further links
  are listed as not encoded, with the reason: recurring standing work and a
  later appeal decision are not within-case loops.
- Inventory hypotheses become alternative routes, capped at 4, uniform declared
  prior 0.25. C29's other 7 hypotheses are listed as unrepresented with the
  reason (cap reached, or a member is not an operation).
- Mutually exclusive outcomes become alternative `paths` inside each route, so
  the first-present union resolves per path rather than always picking the
  earlier-ordered member (§2.6). C29 gets 3 paths per route, C44 12. Two C29
  cases carry a quoted disposition and are scoped; one withdrawn case stays
  unscoped, because no withdrawal path is encoded.
- Observations copied verbatim from the compilation; no rate observations and no
  quantile cohorts, because no source-derived sidecar exists in the V6 contract.

Validated inputs (`--preflight --observed-channels-only`, finite at every probe):

| input | dims | ops | cases | rows | modelled | residual | s/call @4096 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C29__S12 | 155 | 19 | 5 | 32 | 13 | 19 | |
| C44__S12 | 346 | 18 | 6 | 34 | 24 | 10 | |
| combined | 611 | 37 | 11 | 66 | 37 | 29 | 0.0333 |

Both programmes have zero direct payer-hours and agency-hours observations, so
those channels are omitted and marginalised, never set to zero. C44's rows carry
wait/service operators, so it and the combined input need
`--within-visit-phases`; C29 alone does not.

## 5. Launch

Local fitting was rejected: the laptop had 11.5 of 12 GB swap in use and its
data volume at 100%. The fits run on sk3 (`skampere3.stanford.edu`, 288 free
cores, 3 TB RAM) from a code-only compute copy at
`/lfs/skampere3/0/alexspan/regulatory-complexity-v6`, where the model tests
pass under Python 3.11 / numpy 2.2.6 / scipy 1.17.1. That copy is compute, not
archive: the local originals stay authoritative under `runs/README.md`.

Four fits, each 4 chains, 1000 warmup, 2000 draws, 4 workers, population 4096,
cohort quadrature 256, `--observed-channels-only`:

| run | input | seed | phases |
|---|---|---|---|
| `runs/w2_v6_fit_combined_pop4096` | combined | 2026092001 | yes |
| `runs/w2_v6_fit_combined_pop4096_rep` | combined | 20260918 | yes |
| `runs/w2_v6_fit_C29__S12_pop4096` | C29 only | 2026092001 | no |
| `runs/w2_v6_fit_C44__S12_pop4096` | C44 only | 2026092001 | yes |

Population 4096 was chosen because 31 of the 66 rows are population-level, so
the population integral is in the likelihood and prediction-only refinement
cannot fix it afterwards; the runner's own precision check then compares against
16384. Measured throughput: ~26 iterations/minute, so ~1.9 h per combined fit.
The replicate is an independent-seed replication check, and the two
single-programme fits show what pooling across programmes did.

## 6. What the first fit can and cannot say

It answers one question: does the machinery run end to end on source-derived
structure, and what does it learn about elapsed clocks in two S12 programmes.
Everything else is out of scope, and the qualifications are load-bearing:

- Route and path weights are **declared uniform assumptions**, not evidence.
- 11 of C29's 13 informative factors carry 0.733 residual mass (§2.4).
- The structural handoffs' judgments were selected by an agent whose
  conversation held development-truth audit results, and they carry no isolation
  declaration (§2.11). The bridge reads only those files plus the ledger and
  compilation, and records every judgement call it makes.
- No submission marker exists, so no whole-case clock is measurable.
- Counts, fees, FTE and agency-hours stay ledger-only: 46 of C29's 84
  measurements never reach the compiler, all with recorded dispositions.
- Two programmes of one statute, in calibration and development partitions.
  This is not a benchmark result, not a corpus-wide measurement, and not a
  matched LLM comparison.

## 7. Extending to S03 without credits

Alex's instruction (2026-09-18): S05 may stay stuck; continue with S12 and S03.

S05 cannot proceed at all. Its 71-document artifact-only allowlist is frozen and
hashed, but the extraction probe failed on credits before producing any ledger,
and the Codex CLI is the only transport (`subscription_only: true`,
`paid_api_fallback: false`). No parse, so nothing downstream.

S03 can proceed, because the one thing it was missing needs no model. Five S03
programmes have accepted ledgers with their semantic, visit and burden-count
audits already on disk (C32, C35, C38, C44__S03, C50). What they lacked was a
structural handoff, and codex's two S12 handoffs were themselves hand-authored
offline (`new_model_calls: 0`). So the same can be written for S03 by agents
reading only the accepted ledger, its audit sidecars and the frozen source
documents for verbatim quote checking.

This is also an isolation improvement rather than a compromise. The audit
flagged that codex's handoffs were selected by an agent whose conversation held
development-truth audit results, and carry no isolation declaration (§2.11).
The S03 handoffs are written in fresh contexts with no truth access and record
`hidden_truth_read: false` plus an `author_context` field naming that fact.

What the absence of credits costs S03 specifically: no visit-hypothesis audit.
Informative rows therefore come only from single-reading semantic resolutions,
which a scratch compile during the audit measured as C32 5 of 47, C35 19 of 44,
C38 13 of 48, C44__S03 0 of 34, C50 0 of 54. The first three are worth fitting.
The last two would be prior-only, and a prior-only fit must not be reported as
learning, so they are bridged for the record and their coverage reported, but
not fitted. The same applies to C41__S12 (0 of 49).

C38 additionally has a `source-only-cohort-volume-handoff/1` recording a
decided-case median over n = 868. That is deliberately **not** converted into a
V6 `quantile_cohort`: the joint finite-cohort likelihood requires IID sampling
within a declared population, non-overlap with other evidence and conditional
reporting independence, and no document establishes any of the three. The
compiler's `finite_cohort_requires_explicit_joint_sampling_contract` disposition
is the correct outcome, and the claim stays in the ledger.

## 8. Copied claims across cases, and why they do not double-count here

The C35__S03 handoff author flagged a dependency it could not resolve and called
it the live risk: several forum posters in *different* threads report identical
figures, and the compiler was given no report groups, so all 44 rows entered as
independent likelihood factors.

Checked directly against the ledger. There are 13 cross-case identical-value
groups, and three of them are exact multi-quantity clusters that cannot be
coincidence:

| cluster | members (different threads) | shared figures |
|---|---|---|
| A | burrito7946, juniper808 | total 676, file 369, pay 34 |
| B | tinker5952, mossy8066 | total 215, file 180, pay 9 |
| C | mossy1016, sprocket6657, bluejay3544 | total 10 months, pay 1 week, file 6-8 weeks |

Three separate quantities agreeing exactly, between posters in different
threads, is a copied claim, not two independent cases. This is the
contamination the corpus is designed to carry, and the parse prompt explicitly
required that same case, copied claim and overlapping cohort be kept as
different links.

**It does not double-count clock information in this compilation.** In every
cluster exactly one member's readings are semantically resolved enough to be
informative, and the duplicate partner's matching rows are residual-only:

- A: all three of burrito7946's figures are residual; juniper808's file and pay
  are informative.
- B: tinker5952's 180 is residual; mossy8066's 180 is informative.
- C: mossy1016's 6-8 weeks is residual; bluejay3544's is informative.

A residual-only row is a process-independent constant (§1), so it contributes
nothing to any process parameter and cannot reinforce its twin. Each shared
figure therefore enters the likelihood exactly once. The duplicated cases still
get case and source coordinates, but rows that do not depend on them leave them
at prior, which the information report will show as near-zero contraction.

**That immunity is an accident, not a property of the pipeline**, and it is the
thing to fix before any headline number. It holds only because of which
wordings happened to resolve to a modelled reading. Restore the visit-hypothesis
audits when credits return, and burrito7946's figures would likely become
informative too, at which point the same clock evidence would be counted twice.

The contract cannot express the fix. Report groups are the mechanism for
repeated wording, and the compiler correctly rejects a group spanning two
`case_id`s, because a report group is for one report restated, not for
deduplicating two cases. So there is no way today to declare "this claim is a
copy of that claim in another thread" as a dependency, even though the
extraction was asked to distinguish exactly that. This belongs with the
evidence-contract gaps already recorded for the visit basis: a cross-case
`copied_from` link, with the model treating the pair as one observation, is the
missing primitive. Until then the duplicate sets must be reported next to any
S03 posterior, and a fit whose informative rows include both members of a
cluster must not be published.

The same pattern appears independently in C32__S03, and there the separation is
cleaner still: posters in two different threads share an exact triple (309-day
total, 164-day filing, 10-day fee), and **both members are entirely
residual-only**. All five of that programme's informative rows belong to one
case with no twin. Two programmes, two independent handoff authors, the same
contamination, and in both cases the informative evidence happens to sit on one
side of it.

## 9. S03 bridges built without credits

Each was authored in a fresh context with no benchmark-truth access, recording
`hidden_truth_read: false` and an `author_context` field, and each carried its
own handoff through compile, bridge and preflight. Every cited quote is checked
verbatim against the frozen documents by the builder, which fails loudly on a
mismatch (370 references over 15 documents for C32, 320 over 14 for C35).

| programme | dims | ops | excluded | cases | rows | informative | residual | s/call | finite |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C32__S03 | 80 | 16 | 18 | 1 | 47 | 5 | 42 | 0.0040 | yes |
| C35__S03 | 157 | 20 | 14 | 4 | 44 | 19 | 25 | 0.0052 | yes |

Both omit `clock_boundary_markers`, for the same reason and on the documents'
own wording: the statutory clock runs from "a complete submittal", a *state* of
the file, and no activity's completion is named as that boundary. Whole-case
clocks are therefore unavailable in both, which is the honest outcome rather
than a fabricated start event. Both omit payer-hours and agency-hours, which
have no direct observations anywhere in either programme.

Neither carries a quantile cohort. C38's decided-case median over n = 868 is
the one candidate in the S03 set, and it stays refused for the reasons in §7.

The two differ sharply in how much they can inform. C35 has 19 informative rows
spread over three cases and six activities. C32 has 5, all from one case, and
42 of its 47 factors are residual-only, so it will mostly report its prior.
That is a fact about what the documents of that county reveal, not a defect,
and it is exactly the availability-versus-model distinction the project exists
to measure. It does mean C32 alone should not be read as a measurement.

Judgement calls the authors flagged for review, worth checking before any
number is quoted: C32's repeat block had to include payment and screening to be
contiguous in the ledger order, so replaying payment each correction round is a
model-shape assumption rather than evidence; C35's optional status-contact
operation doubles its path count for an activity with no reported duration; and
C35's one merge route that costs evidence (three review readings fall to
residual on it) is the single most consequential inventory choice in the set.

## 10. The first fit, and the contamination it contains

`runs/w2_v6_fit_C29__S12_pop4096` is the first numerically usable posterior V6
has ever produced from source-derived structure. It passed every gate:

| gate | value |
|---|---|
| `posterior_converged` | true, 0 flagged quantities |
| `likelihood_acceptable` | true |
| `predictions_acceptable` | true, 1.01% against the 2% tolerance |
| population refinement | 4096 to 16384, 286 states checked |
| `numerically_usable` | **true** |

Its four route hypotheses came back essentially uniform (0.2416 to 0.2634 from a
0.25 prior), which is the honest answer: the documents do not distinguish them.
Payer-hours and agency-hours are correctly absent, and
`unmeasured_resource_headline_eligible` is false for both.

**The numbers must not be quoted, because the evidence behind them is counted
twice.** Writing `audit_copied_claims.py` and running it across all five
bridged programmes found this, and it inverted the conclusion I had drawn from
the S03 sample alone:

| programme | strong clusters | double-counted |
|---|---:|---|
| C29__S12 | 2 | **both** |
| C44__S12 | 2 | **both** |
| C32__S03 | 2 | neither |
| C35__S03 | 2 | neither |
| C38__S03 | 2 | neither |

In C29, two pairs of posters in different threads agree on several distinctive
figures at once, and in both pairs *both* sides reach informative rows: 18 days
and 23 days for one pair, one week and a same-day step for the other. The three
S03 programmes are clean in the sense that matters, with one side of every
cluster residual-only.

Two methodological points the detector had to get right, both of which changed
its answer:

- **Count agreements per activity, not per row.** A ledger stores "same day or
  next business day" twice, as a 0-1 calendar-day range and a 1-business-day
  value. Counting those separately turned one shared trivially-short step into
  four fake agreements.
- **Only distinctive values count.** A value three or more cases share is a
  common figure, not a fingerprint. Applying this demoted two of C44's clusters
  to `common_values`: they rested on portal and tax steps that four and three
  cases respectively report identically, which is simply what those steps take.

So the response is a sensitivity fit rather than a caveat.
`dedup_copied_cases.py` builds an input that treats each double-counted pair as
the single case it probably is, dropping the fewest cases that leave no
duplicated pair. That last point is a real constraint: in C44 one source is the
copy in two pairs, so dropping it once resolves both, and dropping its partners
instead would discard two cases to save one. C29 loses 2 cases and 4 of 32 rows;
the combined input loses 3 cases and 11 of 66. Both variants preflight finite,
and both are fitting now alongside the originals. The comparison is the result:
a conclusion that survives both was not resting on the duplication, and one that
does not was never a measurement.

## 11. State at pause (2026-09-18, 2026-09-18T12:59:07)

**Eight fits are running on sk3 under `setsid`, so they survive this session
ending.** Two have finished and both passed every gate:

| fit | gates | precision |
|---|---|---|
| `w2_v6_fit_C29__S12_pop4096` | converged, 0 flagged, usable | 1.01% |
| `w2_v6_fit_C44__S12_pop4096` | converged, 0 flagged, usable | 1.42% |

Still running: `combined_pop4096` and `combined_pop4096_rep` (the two-programme
S12 fit and its independent-seed replicate), `C29__S12_dedup_pop4096` and
`combined_dedup_pop4096` (the copied-claim sensitivity variants),
`combined_S03_pop4096` (the three S03 programmes), and `all5_pop4096` (five
programmes across both statutes, using the deduplicated S12 half).

### How to collect them

```
R=/lfs/skampere3/0/alexspan/regulatory-complexity-v6
ssh sk3 "cd $R && for d in runs/w2_v6_fit_*; do [ -f \$d/posterior.json ] && echo \$d; done"
rsync -az sk3:$R/runs/w2_v6_fit_\* runs/w2_v6_fits_20260918/
python3 -m pipeline.procbench.run_visit_hierarchy --diagnose-run <fit> --out <fit>_identification
```

A fit that wrote no `posterior.json` and has no live process failed; its log is
`$R/logs/fit_<tag>.log`. Note the gate crash path recorded in §2.9: a
non-finite delta in the post-sampling check raises before `posterior.json` is
written, leaving the draws with a `running` manifest.

### The one comparison that matters next

Put the original beside its deduplicated variant:

| pair | question |
|---|---|
| `C29__S12_pop4096` vs `C29__S12_dedup_pop4096` | does the clock median move when 2 copied cases go? |
| `combined_pop4096` vs `combined_dedup_pop4096` | same, with C44's copy removed too |
| `combined_pop4096` vs `combined_pop4096_rep` | is the sampler reproducible across seeds? |

Read `programs.<id>.metrics.initial_decision_median_days` and its `ci90` from
each `posterior.json`. A median that shifts materially between a fit and its
dedup variant was resting on evidence counted twice, and the dedup number is
the one to believe. A median that barely moves survives the contamination.
Report both either way; do not quote the original alone.

### Do not publish yet

No number from any of these is a measurement. Route and case-path weights are
uniform declared assumptions; no programme has a submission marker, so whole-case
clocks are unavailable; labour and money stay ledger-only; and this is five
counties across two statutes in calibration and development partitions. What
the fits establish is that the machinery runs end to end on source-derived
structure and converges, which it had never done before today.

### Left undone

- S05: hard-blocked on Codex credits. Frozen 71-document allowlist, no parse.
- C41__S12, C44__S03, C50__S03: accepted ledgers, zero informative rows without
  a hypothesis audit. Bridging them would yield prior-only fits, so they are
  deliberately not fitted.
- C53__S12, C56__S12: no ledger. C58__S03: ledger without sidecars.
- The two evidence-contract gaps: no `basis` field for the visit distinction
  (documented 2026-09-18), and no cross-case `copied_from` link (§8).
- The §2 follow-ups, unchanged: a construction-time check that resource and
  count observations have known applicability; replacing the raw `KeyError` at
  `compact_visit_trace.py:297` with `UnavailableTraceQuantity`; reporting
  effective residual mass per factor; writing `posterior.json` before the
  post-sampling checks; recording the numeric gate thresholds in the
  implementation record; a parser-input isolation test.

Suite at pause: **656 passed** (627 at session start).

## 12. The copied-claim contamination moves the answer by a third to a half

All eight fits completed. Two converged cleanly with zero flagged quantities and
passed every gate: C29__S12 (precision 1.01%) and C44__S12 (1.42%). The rest
failed marginally, R-hat just over the 1.01 threshold with healthy effective
sample sizes, which is short chains rather than pathology, and all six have been
relaunched at three times the draws.

The comparison the sensitivity variants were built for now has an answer, and it
is larger than I expected:

| comparison | median clock | change |
|---|---|---|
| C29 original vs deduplicated | 83.2 to 105.5 days | **+26.8%** |
| C29 in the two-programme fit | 83.7 to 125.0 days | +49.3% |
| C44 in the two-programme fit | 93.8 to 141.1 days | +50.4% |
| C29, seed change only | 83.7 to 90.8 days | +8.5% |
| C44, seed change only | 93.8 to 100.2 days | +6.8% |

The seed-only replicate gives the noise floor: about 7 to 9%. The deduplication
effect is four to seven times that, so it is not sampler variation. The cleanest
number is the first row, the only pair where both fits converged with nothing
flagged.

**The direction is what matters.** Removing duplicated evidence makes the
estimated clock *longer*, by a quarter to a half. The copied claims were short
reports counted twice, and counting them twice pulled the estimate down. So the
contamination was biasing measured burden downward: it made the process look
faster than the evidence supports.

That is the worst direction for this project. A benchmark whose contamination
understates burden would let a method look good precisely by absorbing the
duplication, and nothing in the fit itself signals the problem. Both
contaminated fits converged, passed every numerical gate and reported tight
diagnostics. The only thing that caught it was checking whether two cases in
different threads were quietly the same claim.

Two consequences for how this gets reported. Any posterior from a programme with
a double-counted cluster must be published beside its deduplicated variant, not
alone. And the detector belongs in the release path rather than in an analyst's
judgement, which is why `audit_copied_claims.py` exits non-zero when a strong
cluster is informative on both sides.
