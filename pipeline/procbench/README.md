# procbench scorer — process-model reconstruction

The current toy-statute experiment has [one active corrected implementation](toy_statute/README.md).
Its process fitter is SMC; the older `toy_statute.fit` command delegates to it.
Historical implementations are kept in run snapshots, not selectable production backends.

## Current integration and infrastructure (2026-09-16)

V6 is the integration target. V3–V5 are historical controls, not parallel new model
directions. Start with the [audit implementation record](../../docs/2026-09-16-bayesian-audit-implementation.md).

The package reorganization is staged. Only `infra/` has been extracted so far:

- `infra/codex_runner.py`: isolated subprocess transport, raw attempt artifacts,
  version/hash/timing/status records. Validation and repair policy stay upstream.
- `infra/manifest.py`: JSON writing, hashing, static relative-import source snapshots,
  and the current workflow's versioned manifest lifecycle.
- `infra/scoring.py`: central interval score and log-duration scoring helpers.
- `bayes_trace_hierarchy.py`, `compact_visit_trace.py`, `latent_gaussian.py` and
  related kernels remain the current model, at their original import paths.
- `reconcile_evidence.py`, `audit_*.py`, `compile_visit_durations.py`,
  `semantic_calibration.py` and `evidence_baseline.py` remain evidence entry points.
- `run_visit_hierarchy.py`, `extend_visit_hierarchy.py`, `refine_visit_predictions.py`
  and comparison/validation commands retain their existing CLI paths.
- V3–V5 models, experiment drivers, and `score`/`align`/`metrics` benchmark code
  have not yet moved to `legacy/`, `experiments/` or `bench/`.

Old serialization helper imports still work, but new code should import directly
from `infra`. Do not import an inference driver just to write JSON. The separate
top-level `pipeline/llm.py` still serves the discretion and older benchmark paths;
it is not the process-evidence runner and is not deleted.

New current-workflow manifests contain `manifest_version: procbench-run/1` and a
common `provenance` object. Legacy top-level fields remain for saved-run consumers;
their old schemas are not retroactively rewritten. `provenance.input_sha256` lists
direct dependencies, while a top-level `input_sha256` may specifically identify
the original evidence for equal-information comparisons. Use the appropriate one.

No infrastructure change grants access to benchmark truth. A `hidden_truth_read`
flag records the caller's declared role; it cannot certify what a prompt contains.
See [run archive policy](../../runs/README.md) before moving any experiment records.

For new V6 runs, `run_visit_hierarchy --observed-channels-only` keeps elapsed
clocks and any directly observed payer/agency-hours channels, and omits independent
unobserved labor parameters and their case effects. Omission integrates those
unused priors out; it does not set burden to zero or produce labor posteriors.
`--preflight` reports the retained channels and dimensions. Legacy/default fits
retain all three channels and their saved layouts. Changing dimensions changes
the finite population-integration grid, so precision checks are still required.
This does not yet marginalize active-channel case effects or implement the
complete source-to-route/count/resource compiler.

`--hierarchy-sampler operation_centered` changes only the transition kernel: it
updates program operation means under their Gaussian conditional prior, then
refreshes likelihood-null hierarchy directions. Priors, latent coordinates and
the original likelihood are retained. The historical `blocked` mode remains the
default. The configured hierarchy scales must make the actual operation-mean
covariance positive definite; positive task or agency contrasts can satisfy this
without an operation effect. See the [same-target sampler and SolarTRACE source audit](../../docs/2026-09-19-solartrace-input-and-sampler-audit.md)
for verification and the distinction between numerical and source-semantic fixes.
The separate `case_scale_sampler=interwoven` option is also default-off. It
updates each active channel's case-spread coordinate by one-dimensional ESS
while rescaling every per-case operation residual to hold realized operation
effects fixed. Its callback uses the complete likelihood, residual Normal-prior
ratio and full Jacobian; the accepted state stores a freshly evaluated ordinary
likelihood. Common-case, phase, dwell and hierarchy coordinates are not part of
that transform. This is a transition reparameterization, not a spread prior or
new observation model.
New reports check operation log-location sums and represented agency inventory
means as well as marginal latent coordinates; cancellation between effects can
hide poor mixing of an estimand when only coordinates are checked.

V6 post-fit development scoring is now supported by `evaluate_burden --run ...
--world W2_DEV_001 --out <fresh directory>`. It checks fit completion, posterior
hashes and every program's calibration/development assignment before reading
truth, and emits hash-bound evaluation/release receipts. Numerical convergence
alone is never a recovery certificate. See the
[scoring and selection experiment record](../../docs/2026-09-19-v6-evaluation-and-selection-progress.md).
Source-type ascertainment is an explicit compiler `source_type_sampling` policy;
`run_visit_hierarchy --selection-sd` enables its existing sensitivity model, not
an automatically known forum inclusion probability.

The optional compiler `source_type_report_scales` policy separately declares
fixed elapsed reporting-error scales. A `calibration_id` is an unverified
reference, not learned trust. The structural bridge now preserves explicitly
compiled finite-quantile cohorts as joint factors, including their reviewed
denominators and reporting scales; it does not infer a cohort from a bare `n`.
See [source precision and cohort handoff](../../docs/2026-09-20-source-precision-and-cohort-handoff.md)
for contracts, controlled checks and outstanding real-data calibration limits.

For SolarTRACE, `import_solartrace --panel-only --definitions <Information.csv>`
prepares unique agency phase summaries with business-day units, zeros and joined
source provenance retained. Its output is evidence, not a compiled process graph.
The known-invalid historical graph export requires explicit `--legacy-unsafe`
for diagnostic replay; adjacent joined installation counts never establish a
timing cohort denominator automatically.

V6 routes are program-wide inventory hypotheses. A route may instead of `blocks`
provide `paths: [{id, probability_weight, blocks}, ...]` over subsets of its shared
`operations`. One path is marginalized jointly across each case's reports;
`case_path_scope` conditions known labels without treating anecdotes as prevalence
counts. Population observations may carry an explicit `population_path_scope`.
`--case-path-logit-sd` controls the logistic-normal path-frequency prior (zero fixes
the supplied weights). This is not withdrawal/competing-risk support, and path
weights still need calibration or an explicit sensitivity declaration.

Optional `case_path_priors[case_id][inventory_id]` provides context-hashed,
fixed case-specific sensitivity weights in the same joint mixture. Its guarded
actor-assignment subtype retains an unknown alternative and rejects paths that
differ in process structure rather than actor identity. It does not calibrate
LLM confidence or learn population actor frequencies. See the
[contract, likelihood and current limitations](../../docs/2026-09-20-calfresh-case-path-priors.md).

Optional `joint_duration_reports` replaces explicitly grouped individual elapsed
factors by one integrated common-log-error factor. It is a strict, opt-in
shared-error sensitivity, not learned correlation or an automatic grouping of
sentences. See [joint timeline assumptions and status](../../docs/2026-09-20-calfresh-joint-reported-timelines.md).

Block schedules remain serial by default. A reviewed scheduling hypothesis may
instead declare `predecessors` on **every** block: a list of predecessor block
IDs, with `[]` for an explicit root. Dependencies form a validated DAG; an
entire repeat block completes before any dependent block starts. This permits
explicit overlap between blocks without changing within-block operation order,
repeat counts, fees or work amounts. Partial declarations, unknown IDs and
cycles are rejected. Preflight and posterior reports expose the schedule and
state that overlap is not thereby learned. Unknown dependencies do not become
parallel automatically, and these schedules impose no shared-staff capacity
constraint. Serial/relaxed sensitivity fits require separately frozen inputs;
running snapshots are never changed in place.

`run_visit_hierarchy --elapsed-task-priors <file.json>` optionally supplies fixed
task-specific elapsed prior baselines. The JSON requires
`schema_version: "elapsed-task-priors/1"`,
`clock: "single_visit_cycle_calendar_days_including_wait_and_service"`, a nonempty
`medians_days` map from exact model task names to positive numbers, and a nonempty
`rationale`. The runner hashes the input and saves its specification. Unknown
task names fail rather than silently falling back; omitted tasks explicitly retain
the global seven-day baseline. Leaving this option unset preserves the historical target.
This changes prior log locations, not the shared hierarchy scales or parameter
count. Reports disclose every baseline and fallback. These are complete-visit
elapsed days, not hands-on hours: a short payment action does not itself establish
a short payment queue. Values require independent elicitation/calibration or an
explicit sensitivity protocol; this interface does not supply calibrated values.

`compile_visit_durations` also accepts quote-backed `--source-bindings` and
`--report-groups` sidecars. Bindings can declare a first-visit population and a
first-present approval/denial operation union; these are explicit observation
conditions, not an implicit default population. Report groups preserve repeated
wording or disjunctive intervals as one likelihood factor, retaining every source
claim. Coverage reports separate claims from factors and informative from
residual-only evidence. These interfaces do not calibrate semantic weights or
complete the route compiler. See the dated implementation record for the W2
diagnostic results and the still-unimplemented observation/structure contracts.

Finite sample medians and p90s now enter through program-level
`quantile_cohorts`, not ordinary plug-in population observations. A cohort has
one observed `sample_size`, one explicit `quantile_method` (`linear` or
`inverted_cdf`), shared clock/operator alternatives, and a `reports` list of
quantile intervals. Its summaries share the same integrated sample order
statistics and interpretation; their marginal likelihoods are not multiplied.
The source compiler accepts `--cohort-bindings` with quoted cohort membership
and declared IID/non-overlap/conditional-reporting assumptions. It preserves n,
refuses unsupported means and unreconciled shared-clock alternatives, and counts
one likelihood factor per cohort. No independence or quantile convention is
inferred from a reported denominator. `--cohort-quadrature-size` controls the
power-of-two integration grid, refined along with the population grid by the
precision check. Overlapping cohorts with different operators, duration-dependent
recording/cutoff selection and finite-sample means remain unsupported. This is
not evidence that a W2 dashboard satisfies the IID/non-overlap assumptions.

## Scorer and historical benchmark documentation

New: [joint Bayesian agency/task/case inference](../../docs/2026-09-16-bayesian-process-v4.md),
[reserved-evaluation protocol](../../docs/2026-09-16-bayesian-process-v4-protocol.md),
[experiments and limitations](../../docs/2026-09-16-bayesian-process-v4-results.md),
[historical negative pilot](../../docs/2026-09-16-bayesian-process-v3-results.md), and
[simplified TikZ model](../../docs/figures/latex_plate_diagram_simplified/README.md).

Scores a *predicted* process model against a gold one (`process_truth`,
`benchmark/synth/DESIGN.md`) and, when a `ceiling.json` is supplied, against the
**information ceiling** — the subset of the truth that public artifacts provably
reveal. Ceiling-relative numbers are what separate *model* error from
*availability* error (docs/2026-09-15-process-benchmarks-plan.md §1).

```
python3 pipeline/procbench/score.py --pred pred.json --gold truth/processes/J2__S03.json \
    [--ceiling ceiling.json --task W1__J2__S03] \
    [--distractors truth/processes/J2__S07.json truth/processes/J3__S03.json] \
    [--statute truth/statutes/S03.json] [--log-summary truth/log/J2__S03.summary.json] \
    [--align offline|llm|both] [-k 3] [--condition oracle_docs] [--run-id r01] \
    --out runs/r01/score.json

python3 pipeline/procbench/score.py aggregate --runs 'runs/*/score.json' --out summary.json
```

Outputs: `score.json` (every metric as `{num, den, value}` so runs re-aggregate by
summing numerators and denominators, never by averaging averages) and
`alignment.json` next to it (the full pair list with scores/votes, plus unmatched
predicted and unmatched gold activities — meant to be read by a human).

`--align offline` is the default and needs no network: the Codex backend takes
minutes per call, so nothing in the metric path depends on an LLM.

Inputs are tolerant: activities may carry `name`, `local_name`, `actor`,
`visibility`, `element_ref`, `timing.median_days`, `fee.amount` (or a bare
number, or `"$430"`), `rework.back_to`, `confidence`, `evidence`; edge `type`
strings outside the schema's enum (`gate`, `substitute`, `sequence_optional`,
`loop?`, `revocation`, …) are bucketed into **order** vs **rework** by keyword, so
the real-world golds in `corpus/` score without editing.

Scorer version 3 also accepts canonical `source`/`target`/`kind` edges, preserves
explicit payer/third-party roles, and does not treat parallel edges as precedence.
Historical result files are not overwritten. The v4 evaluation additionally reports
one-to-one-backbone F1, raw count error, and proper log-median posterior scores;
the lexical alignment still needs semantic auditing.

## Alignment

Many-to-one and one-to-many are allowed: granularity is a known error source (#8),
so the scorer never assumes the prediction cut the process into the same number of
pieces as the gold. Both aligners emit the same pair records
(`pred, gold, score, text_sim, relation, votes, actor_match, …`).

**Offline (deterministic).** Score every (pred, gold) pair:

```
sim = 0.72·text + 0.18·actor + 0.10·order            ∈ [0, 1]
text  = max over {name, local_name}² of  F1(tokens)  = 2|A∩B| / (|A|+|B|)
actor = 1.0 same canonical lane | 0.6 one lane is generic/unknown
        | 0.35 both city-side lanes | 0.0 otherwise
order = 1 − |rank(pred) − rank(gold)|,  rank = normalized position in the
        longest-path topological order over that model's order edges
```

Tokens are lowercased, stopworded, phrase-folded (`site visit`/`site inspection` →
`inspection`; `plan check`/`plan review` → `review`) and mapped through a synonym
table to concepts — `inspect` (inspect/inspection/site visit/reinspection),
`submit` (submit/apply/file/application/intake), `issue` (issue/grant/approve/
issuance/recognize), `review` (plan check/plan review/screening/completeness/
verify), plus `fee`, `correct`, `notice`, `certificate`, `record`, `referral`,
`meeting`, `eligible`, `decision`, `hearing`, `appeal`. Lane names go through a
canonicalization map (`Building Division`/`building_official`/`DSD` → `building`;
`homeowner`/`Property Owner` → `applicant`; `code_enforcement` → `inspector`; …).

Then: a greedy 1-1 backbone over pairs sorted by `sim` (accept while both sides
are free and `sim ≥ 0.32`), followed by a **granularity extension pass** that adds
a pair when exactly one side is still free, `sim ≥ 0.40`, `text ≥ 0.40` *and* the
lanes are compatible — so a merge/split claim needs real content overlap, not just
the same lane at the same position. Extensions are labelled `split` (one predicted
activity covers several gold ones) or `merge` (several predicted cover one gold).

**LLM (`--align llm`, `--align both`).** k independent matchings, both lists
shuffled per run so position cannot leak (the `crosswalk_eval.py` pattern), via
`pipeline/llm.py` (backends codex/glm/anthropic). A pair is kept with
`≥ ceil(k/2)` votes; `votes` is recorded per pair. `both` runs the offline aligner
as well and reports the Jaccard agreement of the two pair sets — an estimate of
alignment noise for that task. Metrics under `both` are computed on the LLM
alignment; `alignment.json` keeps the offline pairs for comparison.

## Metrics (all in `score.json`, each with num/den)

Let `M` = pairs, `MG` = gold ids in `M`, `MP` = predicted ids in `M`.

| metric | formula |
|---|---|
| `activity.precision` | \|MP\| / \|pred\| |
| `activity.recall_all` | \|MG\| / \|gold\| |
| `activity.f1` | harmonic mean of the two |
| `activity.recall_visible` | \|MG ∩ V\| / \|V\|, V = gold with `visibility ∈ {applicant_facing, applicant_inferable}` (`null` + a note when the gold carries no visibility field) |
| `activity.recall_ceiling` | \|MG ∩ C\| / \|C\|, C = `recoverable_exact ∪ recoverable_approx` resolved to gold activity ids (entries may name an activity `A04`, an element `E2`/`L1`, or `A04.fee` — the field suffix is stripped). **This is the number that isolates model error from availability.** |
| `actor_accuracy` | matched pairs with the same canonical lane / \|M\| (`compatible` counts the softer city-side-vs-city-side agreement) |
| `order_agreement` | over the transitive closure of gold **order** edges (rework ignored): pairs (i,j) with i before j, both matched, whose representative predicted activities (highest-scoring pair per gold) appear in the same order in the predicted closure. A gold pair that collapses onto one predicted activity has no internal order and is reported as `conflated`, excluded from the denominator. Pred pairs with no path either way fall back to list position. |
| `rework.recall` | gold rework edges (u,v) with some predicted rework edge (p,q), p aligned to u and q to v / \|gold rework edges\| (`rework.precision` is the mirror) |
| `fee` | per matched pair with both fees: `abs_err`, `rel_err = abs_err/gold`; reported as means, plus `exact_matches` and `total_fee_rel_err` over the whole model |
| `timing` | Per matched pair with both duration estimates: \|log(pred / gold)\|, `mean_abs_log_ratio`, and `within_2x`. Version 2 reads typed `value_days` but excludes caps/targets. End-to-end prediction must be explicit (`process_timing.median_days`, `end_to_end.median_days`, or `end_to_end_median_days`); gold may additionally come from the ceiling or log summary. Missing end-to-end estimates stay null: **sums of step medians are not process medians**. |
| `hallucination` | predicted activities in no pair / \|pred\| |
| `disentanglement.failures` | predicted activities whose best offline `sim` to any `--distractors` activity is ≥ 0.32 **and** exceeds their best `sim` to gold by > 0.05 / \|pred\| — evidence from another process/jurisdiction (#4). Split into `among_unmatched` / `among_matched`; always scored with the offline similarity so it is deterministic and comparable across runs |
| `staleness` | counted separately: `stale_fee` (a predicted fee equal to a `prior_version` amount and not to any current one), `stale_actor` (a matched pair with the wrong lane, where that lane is the one the prior version named), `stale_missing_added_element` (a `prior_version.changes` entry of the form "no X" whose corresponding gold activity the prediction missed — i.e. the prediction still describes the old design). `total_stale_facts` sums them (#6) |
| `element_coverage` (`--statute`) | mandated non-optional `statute_truth.skeleton` elements whose implementing gold activity is matched / all mandated elements (an element absent from the truth graph falls back to a name match against the prediction). If the statute file is a statute-sourced *process model* instead, `pipeline/process_model.coverage` is reused verbatim |
| `confidence_evidence` | mean predicted `confidence` on matched vs unmatched activities (calibration signal) and the share of predicted activities carrying `evidence` URLs |

## Aggregation and the error decomposition

`aggregate` reads many `score.json` files (glob it, quoted or shell-expanded):

* `by_condition[cond].means` — per-metric means over runs; `.pooled` — the same
  metrics recomputed from summed numerators/denominators.
* `decomposition.per_task`
  * `availability    = 1 − |ceiling| / |truth|`
  * `reconciliation  = 1 − ceiling-relative recall (oracle condition)`
  * `retrieval       = ceiling-relative recall(oracle) − ceiling-relative recall(search)`

  Oracle = the condition named `oracle_no_distractors` / `oracle_docs` / anything
  containing `oracle`; search = anything containing `search`. Pass `--condition`
  when scoring so these are identifiable.
* `reliability` — for each (task, condition) with ≥ 2 runs, the mean pairwise
  Jaccard of (a) the matched gold-id sets and (b) the predicted activity
  signatures (`lane|sorted concept tokens`). (a) is elicitation variance measured
  through the alignment, (b) measures it on the raw prediction (#9).

## Known limits

1. **Alignment noise is a measurement, not a solved problem (#8).** Every pair
   carries its `score`/`text_sim`/`votes` and `relation`, unmatched activities on
   both sides are listed, and `--align both` reports the offline-vs-LLM Jaccard.
   Report that Jaccard next to any headline metric; treat differences smaller
   than the alignment disagreement as noise.
2. The offline aligner is lexical. A gold activity described in entirely
   different words with a compatible lane can be missed (a false "missing
   activity"), and a predicted step that conflates two gold steps is only
   credited for both when the text overlap clears `T_EXTEND_TEXT` — see the
   worked example below, where `a1` ("Applicant submits application with Required
   Submittals…") was matched to gold `A3` ("Assemble required submittals") but
   not also to `A4` ("Submit application"), costing a recall point that a human
   would award.
3. `order_agreement` uses one representative predicted activity per gold; a
   prediction whose edges are absent is ordered by list position.
4. `staleness` only sees what the gold's `prior_version` block states. If the
   synthetic world does not record the old value, a stale prediction is scored as
   plain error.
5. `disentanglement` needs the distractor processes passed explicitly, and it
   uses the lexical similarity, so a *paraphrased* contamination can slip through.
6. Real-world golds (`corpus/`) carry no `visibility` and usually no timing or
   fees: those metrics come back `null` with a note rather than 0, and
   `recall_visible` is only meaningful on synthetic worlds.

## Worked example (offline alignment, real AB 2533 data)

Gold: `corpus/ab2533/process/hayward/designed_process.json` — the 16-activity
reconstruction of Hayward's ADU-amnesty process. Prediction: the *declared*-tier
model built mechanically from the city's program page, i.e.
`pipeline/process_model.declared_to_model` on the Hayward entry of
`corpus/ab2533/process/declared_processes.json` (7 activities: 6 published steps
plus the `j0` jurisdiction-level credit). Distractor: the same transform on the
**El Cerrito** entry (same statute, different jurisdiction). Ceiling: a
declared-tier ceiling derived from the gold's own citations — an activity is
recoverable iff the gold cites it to D1 (current program page) or D2 (published
checklist); `recoverable_exact` = cited only to D1/D2 (9 activities),
`recoverable_approx` = cited to D1/D2 plus an archived doc (3), `hidden` = cited
only to archived earlier-version pages/handouts D3/D4 (`A2b`, `A8b`, `A9b`, `A12`).

```
python3 pipeline/procbench/score.py \
  --pred /tmp/hayward/declared_city_of_hayward__ca.json \
  --gold corpus/ab2533/process/hayward/designed_process.json \
  --ceiling /tmp/hayward/ceiling_declared_tier.json --task RW__hayward__ab2533 \
  --distractors /tmp/hayward/declared_city_of_el_cerrito__ca.json \
  --align offline --condition declared_only --out /tmp/hayward/score.json
```

| metric | value | num/den |
|---|---|---|
| activity precision | 0.857 | 6/7 |
| activity recall (all gold) | 0.375 | 6/16 |
| activity F1 | 0.522 | |
| recall, applicant-visible gold | `null` | real gold has no `visibility` field |
| **ceiling-relative recall** | **0.500** | 6/12 |
| availability gap (1 − \|ceiling\|/\|truth\|) | 0.250 | 12/16 recoverable at the declared tier |
| actor accuracy | 0.833 | 5/6 |
| order agreement | 0.933 | 14/15 |
| rework recall / precision | 0.333 / 0.500 | 1/3, 1/2 |
| hallucination rate | 0.143 | 1/7 (`j0`) |
| disentanglement failures | 0.143 | 1/7 (`j0`) |
| staleness | 0 | gold has no `prior_version` block |
| fee / timing error | `null` | the declared tier states the $570 fee only in prose and no durations, so the transform emits no `fee`/`timing` fields |

Reading it: the declared tier recovers half of what it *could* recover — even the
public page's own steps are cut coarser than the gold (the one alignment slip in
limit 2 above), and `A1` (confirm eligibility), `A2` (optional confidential
third-party inspection), `A10` (JADU deed restriction), `A11` (post-issuance
enforcement) and `A13` (the Path-1 alternative) are on the page but absent from
the 6-step summary. The remaining quarter of the truth is below the ceiling and no
declared-tier agent could get it. The single order violation is real: the page
lists document review before the fee, the gold has staff requesting payment first.
The one hallucination *is* the one disentanglement failure — `j0` is a
jurisdiction-level pseudo-activity the transform appends, identical across cities,
so it aligns at 0.996 to El Cerrito's `j0` and to nothing in the gold. That is the
metric working, and also a reminder that `declared_to_model` output is a baseline,
not a solver.

Reproduce the two inputs (both derived, both tiny):

```python
import json, pathlib, sys; sys.path.insert(0, "pipeline")
import process_model as pm
OUT = pathlib.Path("/tmp/hayward"); OUT.mkdir(parents=True, exist_ok=True)
d = json.load(open("corpus/ab2533/process/declared_processes.json"))
for j in d["jurisdictions"]:                       # writes .../declared_city_of_*.json
    m = pm.declared_to_model(j)
    (OUT / f"{m['model_id']}.json").write_text(json.dumps(m, indent=1))

g = json.load(open("corpus/ab2533/process/hayward/designed_process.json"))
DECL, ex, ap, hid = {"D1", "D2"}, [], [], []
for a in g["activities"]:
    c = {a[k]["cite"].split()[0] for k in ("span", "span2", "span_earlier") if a.get(k)}
    (ex if c <= DECL else ap if c & DECL else hid).append(a["id"])
(OUT / "ceiling_declared_tier.json").write_text(json.dumps(
    {"task_id": "RW__hayward__ab2533", "elements_total": len(g["activities"]),
     "recoverable_exact": ex, "recoverable_approx": ap, "only_wrong": [], "hidden": hid}, indent=1))
```

## Tests

`python3 -m pytest tests/test_procbench_score.py -q` (or run the file directly).
Offline only — the LLM k-vote path is covered with a stubbed backend, so the
suite never touches the network.

## Aligner changes after the Benchmark-1 pilot (2026-09-15)
- `f1()` is now max(Dice, 0.85 × overlap coefficient) with the overlap boost gated on ≥2 shared concept tokens.
- Added `_EXTRA_PHRASES` (domain acronyms) and extra `ACTOR_FAMILIES` (dealer, instructor, state agencies, records units, more applicant synonyms); `canon_actor` also tries prefix/substring family matches.
- `toks()` applies a crude suffix stemmer to words outside `SYN`.
- The alignment file is written next to the score file as `<stem>.alignment.json` (was a fixed `alignment.json` in cwd).

## Agent-backed alignment (`align_agent.py`, 2026-09-15)
When no LLM backend is keyed, `align_agent.py emit` writes k shuffled prompts; an orchestrator spawns k
independent Claude subagents (one ballot each, no repo access); `align_agent.py merge` keeps pairs with
≥⌈k/2⌉ votes and writes an alignment file; `score.py --align file --alignment-in <file>` scores against it.
Merge output includes `offline_vs_agent_agreement` and `rejected_below_threshold`.

**Write the merge output and the scorer's alignment dump to different paths** — `--alignment-out` defaults to
`<out stem>.alignment.json` and will otherwise overwrite the merged votes.

Measured on the 16 Benchmark-1 pairs: offline vs agent k-vote alignments agree at median Jaccard 0.37, and
median recall differs by 23 points (0.46 → 0.69). Alignment choice is the largest single source of metric
variance; publish the alignment with any score, and report gold-per-predicted fan-out (median 3, max 8)
alongside recall.
