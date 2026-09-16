# Process-model inference: the big update (planned 2026-09-15)

Owner: Alex. Scope agreed in conversation 2026-09-15. Three workstreams, two benchmarks.

## 0. What we are measuring

A **process model** (schema: `pipeline/schemas/process_model.schema.json`) = actors (lanes) × activities (who does what, on what occasion, producing which artifact) × edges (sequence / handoff / rework / optional) × a terminal artifact, plus — new in this update — **timing** (per-activity duration distributions and end-to-end elapsed time) and **fees**. Three tiers of evidence (design.md §9–10): *declared* (applicant-facing pages, forms), *designed* (staff reports, SOPs, audits, consultant studies), *observed* (permit logs, user reports, official processing-time statistics).

**The inference task**: given a (statute, jurisdiction) pair and access to a corpus (the real web, or a synthetic one), produce the process model + timing, with per-element confidence and provenance.

## 1. Sources of process-modeling error (Alex listed 1–2; 3–8 added)

| # | Error source | How we isolate it |
|---|---|---|
| 1 | **Information availability** — the artifact simply does not encode the element (back-office steps are invisible to applicants) | Synthetic: the *information ceiling* (what the public artifacts provably reveal) vs. the full truth. Real: designed-tier docs vs. declared-tier docs on the same process. |
| 2 | **Retrieval / search** — the element is encoded somewhere public but the agent did not find it | Oracle-retrieval condition (hand the agent every relevant doc) vs. agentic-search condition; log every query and fetch. |
| 3 | **Reconciliation / model capacity** — the agent found the evidence but built the wrong graph (wrong order, merged actors, missed rework, misattributed to the wrong process) | Oracle-retrieval + no-distractor condition isolates this. |
| 4 | **Disentanglement** — evidence from *other* processes/jurisdictions contaminates the model (a reddit post about the county's process, not the city's) | Distractor-density knob in the synthetic world; provenance labels on every artifact. |
| 5 | **Gold error** — the "true" process model is itself an artifact (a staff report is a *design*, not the practice; audits are dated) | Real benchmark reports agreement with *each* tier separately; the synthetic benchmark has exact truth by construction. |
| 6 | **Temporal drift** — sources from different dates describe different versions of the process | Version stamps on artifacts; synthetic worlds include stale artifacts with known staleness. |
| 7 | **Selection bias in user reports** — reddit oversamples complaints, delays, edge cases; timing estimates from posts are biased upward | Synthetic: user posts are sampled from the true timing distribution through a known complaint-selection function, so the bias is measurable and the de-biasing can be scored. |
| 8 | **Granularity / alignment** — the same process can be cut into 6 or 16 activities; scoring requires aligning predicted to gold activities, and the alignment is itself noisy | Scorer uses k-vote LLM alignment (as in `crosswalk_eval.py`) with human-checkable alignment tables; report metrics at the gold's granularity. |
| 9 | **Elicitation variance** — the same agent gives different models on re-runs | k runs per condition; report reliability alongside accuracy. |

Decomposition we will report: `total error = (truth − ceiling) + (ceiling − oracle-retrieval score) + (oracle − agentic score)` ≈ availability + reconciliation + retrieval, each measured under a stated distractor density.

## 2. Workstream A — real-world reconnaissance (Wave 1, running now)

Goal: for ~9 real statute-backed processes, collect the *full public footprint* the way we did for AB 2533, extended to user reports (reddit, forums, MuckRock) and timing. Output per process: `corpus/realworld/<slug>/` with `sources.json` (manifest, schema in `corpus/realworld/README.md`), `notes.md`, `raw/`, `reddit/`. Every source is labeled by tier and by *what process elements it reveals* — so the real corpus has the same provenance discipline as the synthetic one.

Processes (chosen for statute→local-rule structure, reddit footprint, and available gold):

| slug | statute | implementers | user-report venues | gold timing / designed docs? |
|---|---|---|---|---|
| `adu_permit` | Gov. Code § 66314 et seq. (ministerial ADU) | cities | r/bayarea, r/LosAngeles, r/ADU, r/HomeImprovement | 60-day shot clock; SF/LA permit logs (observed_data_scan.md) |
| `ui_claim` | Unemp. Ins. Code § 1326 et seq. (EDD) | one state agency, many paths | r/Unemployment, r/EDD | EDD published metrics; State Auditor reports (flowcharts) |
| `calfresh` | Welf. & Inst. Code § 18900 et seq.; 7 CFR 273 | 58 counties | r/foodstamps, r/CalFresh | 30-day federal clock; county processing-time reports (CDSS) |
| `dros_firearm` | Penal Code §§ 26815, 28220 (DROS, 10-day wait) | DOJ + dealers | r/CAguns (very detailed) | DOJ BOF statistics; dealer-facing DROS manual (designed tier, public) |
| `cslb_license` | Bus. & Prof. Code § 7065 et seq. | CSLB (one agency) | r/Contractor, r/Construction | CSLB published application processing times |
| `food_facility` | HSC § 113700 et seq. (CalCode) | county env. health | r/foodtrucks, r/smallbusiness, r/Cooking | county plan-check timelines; Ho's work |
| `solar_permit` | Gov. Code § 65850.5 (expedited permit); § 65850.52 (SB 379 automated permitting) | cities | r/solar, r/solardiy | SolarAPP+ = a *coded* process (designed tier is literally public software); utility PTO timing |
| `cpra_request` | Gov. Code § 7920.000 et seq. (10-day determination) | every agency | MuckRock (request logs with timestamps = observed tier), r/foia | MuckRock per-agency response-time statistics |
| `n400_naturalization` | 8 U.S.C. § 1421 et seq. (USCIS) | one federal agency, per field office | r/USCIS ("my timeline" posts) | USCIS publishes per-office processing times = **official observed gold** |

Plus a **gold hunt** agent: where do *back-office* process models exist publicly for California-style processes? (State Auditor reports, civil grand jury reports, Matrix Consulting permit studies, Lean/process-improvement reports, SOP manuals, MuckRock-released procedures, court records.) Those become Benchmark 1's designed-tier gold.

## 3. Workstream B — Benchmark 1: real-world process reconstruction

Unit: a task `(process, jurisdiction, information condition)`. Gold: the best designed-tier document we have (e.g., Hayward's 16-activity design; an auditor's flowchart), plus observed timing where it exists. Conditions: (a) declared-only, (b) declared + user reports, (c) + designed docs (oracle), (d) agentic web search. Metrics: aligned activity P/R/F1, actor accuracy, ordering agreement (footprint/follows relations), rework-loop recall, mandated-element coverage vs. statute skeleton, timing error (log-ratio of predicted vs. gold median elapsed), and k-run reliability. Files: `benchmark/realworld/`.

## 4. Workstream C — Benchmark 2: the synthetic ecosystem

Design in `benchmark/synth/DESIGN.md`. Backwards generation: truth (statute skeleton → local ordinance → full designed process incl. back-office) → artifact *specs* with a **visibility model** (which elements each artifact reveals, at what fidelity, how stale) → rendered artifacts (pages, forms, FAQs, staff reports, ordinances, reddit threads, news) → a **mock web** (URLs, links, subreddits, a search index) with distractors from other processes and jurisdictions → per-task **information ceiling** computed from provenance. Everything generated is logged with *why* in `provenance.jsonl`.

## 5. Sequencing

1. Wave 1 (now, parallel): 9 recon agents + gold-hunt agent. In parallel: generator, scorer, mock-web/solver skeletons (Opus).
2. Calibrate the synthetic visibility model and artifact style guides from Wave 1 (real reddit post exemplars; real page structures; real staleness).
3. Wave 2: render artifacts (many Sonnet agents from specs) → Wave 3: verify provenance (Opus, leakage check).
4. Baseline solver runs under the four conditions; report the error decomposition.

## 6. Findings from Wave 1 (running log, 2026-09-15)

- **Gold quality and public footprint are anti-correlated** (gold hunt, 27 candidates): the best back-office flowcharts (State Auditor gambling-licensing report, city-auditor permit audits) attach to processes with no user-report venue; the richest reddit corpora (N-400, DROS, CalFresh) attach to processes whose staff-side documents carry no timing. Benchmark 1 tasks must be picked on the *product* of the two, and the synthetic world is where both can be dialed up together.
- **User reports recover staff-only facts through insiders and triangulation**: self-identified eligibility supervisors on r/CalFresh naming CalSAWS and a "disposition deadline"; an unpublished 10-business-day adjudication clock at EDD triangulated from three independent threads; dealer-side failures on r/CAguns. The synthetic `p_reveal_backoffice_in_comments` knob is real, and its value is not small in benefit programs.
- **Published designed-tier documents are often unknown to users**: DOJ's 193-page dealer system guide states the "undetermined" release rule that r/CAguns reverse-engineers from anecdotes. Retrieval error, not availability, dominates there.
- **Keyword-search noise is a real distractor class**: "plan check" on r/sanfrancisco returned 25 hits of pure noise (transit, utility rates). The synthetic distractor set must include high-lexical-overlap off-topic threads, not only sibling-process threads.
- **Concurrent API use throttled the recon**: several subreddits returned zero results for the ADU agent while nine agents shared the Arctic Shift rate limit; a serial re-sweep is needed before treating any zero as absence.
- **Consultant fee/process studies are the richest untapped gold** (a fee study is a process model with per-step staff minutes) and live in Legistar packets; the Hayward Legistar scraper can be pointed at Mountain View, West Sacramento, Santa Rosa, Pasadena.

### Benchmark 1 pilot (2026-09-15, offline alignment — treat as a floor)

Solver = the Wave-1 recon agent's `process_draft.json` (built from statute + declared pages + reddit, i.e. the *declared_plus_users* condition, with a Claude agent as solver). Gold = the 13 designed-tier models in `benchmark/realworld/gold/` (351 gold activities, 69 of them staff-only). Scored with `pipeline/procbench/score.py --align offline`; results in `runs/rw_pilot/summary.json`. The LLM k-vote alignment (the real mode) awaits a Codex re-login.

| gold model | pred | gold | staff-only | P | R(all) | R(visible) | actor | order | rework | halluc. |
|---|---|---|---|---|---|---|---|---|---|---|
| ui_claim / EDD | 27 | 34 | 4 | 0.89 | 0.74 | 0.80 | 0.62 | 0.77 | 0.14 | 0.11 |
| food_facility / LA County DPH | 23 | 30 | 3 | 0.87 | 0.70 | 0.70 | 0.38 | 0.91 | 0.33 | 0.13 |
| cslb_license / CSLB | 19 | 30 | 3 | 0.95 | 0.60 | 0.63 | 0.74 | 0.93 | 0.22 | 0.05 |
| dros_firearm / DOJ + dealer | 15 | 30 | 7 | 0.87 | 0.50 | 0.57 | 0.67 | 0.74 | 0.00 | 0.13 |
| food_facility / San Diego County | 23 | 29 | 3 | 0.52 | 0.48 | 0.50 | 0.50 | 0.93 | 0.11 | 0.48 |
| n400 / USCIS field office | 14 | 30 | 8 | 1.00 | 0.47 | 0.55 | 0.57 | 0.94 | 0.00 | 0.00 |
| calfresh / Santa Clara SSA | 12 | 24 | 7 | 0.67 | 0.46 | 0.47 | 0.82 | 0.28 | 0.00 | 0.33 |
| food_facility / San Francisco | 23 | 29 | 6 | 0.57 | 0.45 | 0.48 | 0.38 | 0.82 | 0.00 | 0.43 |
| adu_permit / San José | 14 | 30 | 4 | 0.79 | 0.43 | 0.42 | 0.43 | 0.89 | 0.00 | 0.21 |
| cpra_request / LAPD | 14 | 25 | 7 | 0.64 | 0.40 | 0.44 | 0.10 | 0.78 | 0.00 | 0.36 |
| calfresh / LA County DPSS | 12 | 31 | 6 | 0.83 | 0.35 | 0.36 | 0.27 | 0.93 | 0.00 | 0.17 |
| adu_permit / Sonoma County | 14 | 29 | 11 | 0.64 | 0.31 | 0.39 | 0.89 | 0.94 | 0.00 | 0.36 |
| **median (n=12)** | | | | **0.81** | **0.46** | **0.49** | **0.54** | **0.90** | **0.00** | **0.19** |

Reading:
1. **Precise but shallow.** Median precision 0.81 against median recall 0.46 — the public footprint yields a third to three-quarters of the designed process, and what it yields is mostly right.
2. **The gap is not only hidden back-office steps.** Recall against *applicant-visible* gold is 0.49, barely above recall against all gold, so the drafts also missed or collapsed steps the applicant can see. That is granularity (error source #8) and retrieval, not availability.
3. **Order is nearly free; rework is nearly absent.** Order agreement 0.90 median, rework recall 0.00 in 8 of 12 models. Sequence is recoverable from public prose; loops are not. That asymmetry is the sharpest process-layer finding so far.
4. **Timing, when stated, was close.** 19 of 20 per-activity comparisons fell within 2× of gold.
5. **Caveat on hallucination:** one draft per *slug* was scored against up to three *implementers*, so a correct San Francisco step counts as hallucinated against San Diego. The 0.43–0.48 hallucination rates in the food-facility rows are mostly this artifact — which is itself error source #4 (disentanglement) measured accidentally, and is why Benchmark 1 tasks are keyed per implementer.

Aligner changes forced by the pilot (all in `pipeline/procbench/align.py`): overlap-coefficient similarity gated on ≥2 shared concept tokens (Dice alone penalised the gold's long names — DROS precision was 0.13 before, 0.87 after); domain acronym phrases (FSC, DROS, PTO, PPT, EH, FO…); actor families for dealers, instructors, state agencies, records units and county benefit-agency roles; a crude stemmer; per-run alignment files. Actor lanes feed the similarity score, so lane canonicalization moves the activity matches too (Santa Clara went from recall 0.25 / actor 0.00 to 0.46 / 0.82 when county roles were added). Remaining offline-alignment errors are visible in `runs/rw_pilot/*.alignment.json` (e.g. "Interview scheduled (notice)" → "neighborhood investigation").

### Alignment noise dominates the metric (2026-09-15) — the headline methodological result

The same 16 (prediction, gold) pairs were scored under two independent alignments: the deterministic offline aligner and a **k-vote alignment by 3 independent Claude voters each** (48 ballots, `pipeline/procbench/align_agent.py`; each voter saw only two shuffled activity lists and wrote a ballot, with no access to the repo).

| | offline aligner | agent k-vote (k=3) |
|---|---|---|
| median precision | 0.81 | 0.84 |
| median recall (all gold) | 0.46 | **0.69** |
| median recall (visible gold) | 0.49 | **0.73** |
| median order agreement | 0.90 | 0.95 |
| median rework recall | 0.00 | **0.25** |
| median hallucination | 0.19 | 0.16 |

**The two alignments agree at a median Jaccard of only 0.37** (range 0.06–0.74). So the choice of aligner moves median recall by 23 points — larger than the spread between most processes. Any single reported recall number is therefore an artifact of the aligner unless the alignment is published with it. Consequences for the benchmark, all now mandatory:

1. **Report both alignments, always**, plus their agreement. `runs/rw_pilot/summary.json` (offline) and `runs/rw_agent/summary.json` (agent k-vote) are the paired artifacts; per-pair ballots and merged votes live in `runs/align_votes/` and `runs/rw_agent/*.kvote.json`.
2. **The mechanism is fan-out, not disagreement about content.** The agent voters license many-to-one matches the offline aligner refuses: one predicted activity absorbs a median of 3 and up to **8** gold activities. Worst case, CalFresh Santa Clara: the single predicted step "Handle missed interview (notice + reschedule)" was matched by all three voters to eight separate gold activities (send the missed-interview notice, same-day text reminder, schedule a second appointment, review the three conditions, ask Clerical to reassign, schedule in CalSAWS, journal the contact, rescind the denial). Recall reads 1.00; the prediction contains one twelfth of the detail. That is a real granularity claim, not an error — and it is exactly why recall alone cannot be the headline number.
3. **Report a granularity statistic next to recall**: mean and max gold-per-predicted fan-out. A high recall with fan-out 8 is a coarse model, not a good one. Candidate headline metric instead: recall at fan-out ≤ 2, or a detail-weighted recall.
4. Codex k-vote alignment (`runs/rw_llm/`) is running as a third independent mode; three-way agreement will bound aligner variance rather than merely exhibiting it.

### Wave-2/3: what the synthetic documents disclose, and one self-correction (2026-09-15)

Target artifacts: 263 rendered, 241 passing leakage verification first time, 18 auto-repaired, 4 hand-fixed.
Measured coverage of the 26 target processes by the rendered documents, by visibility class:

| activity class | revealed as existing by rendered documents |
|---|---|
| applicant_facing | 174/174 = 1.00 |
| applicant_inferable | 82/90 = 0.91 |
| staff_only | 50/117 = 0.43 |

That is the intended gradient, and it brackets the real-world pilot (median recall 0.46–0.69 depending on
aligner). Per-process variation is realistic: one process discloses 6/6 staff-only steps because the city
published a procedure document; five disclose none.

**Self-correction worth recording** (the retraction-lesson discipline applied to ourselves): I first concluded
from the verify failures that `ceiling.json` under-credited statutorily-mandated staff-only steps and so biased
the availability term. That was wrong. Re-checking showed the statute-level reveal rule already credited all 16
such steps (7 exact, 9 approximate, 0 hidden) and the ceiling means did not move after the fix. The real defect
was narrower: 34 specs forbade legal documents from restating their own mandates. Both the wrong diagnosis and
the verified one are kept in `benchmark/synth/DESIGN.md` §"Wave-2/3 finding".

### Benchmark 2 first results: the error decomposition, measured (2026-09-15)

Solver = Codex (`gpt-5`-class via the Codex CLI) through `pipeline/procbench/solve.py`. 8 synthetic programs under `oracle_docs` (every target document supplied, one reading pass), 3 of them also under `search` (the model queries the mock web — 263 relevant documents among 1,052 decoys — with at most 10 tool calls). Scored against `truth/processes/` with `ceiling.json`. Raw: `runs/synth/`, `runs/synth_search/`, rollup `dashboard/data/synth_results.json`.

| median over programs | documents supplied | must search |
|---|---|---|
| recall of all true steps | 0.89 | 0.50 |
| recall of applicant-visible steps | **1.00** | 0.70 |
| **recall of what the documents disclose (ceiling-relative)** | **0.96** | **0.53** |
| order agreement | 0.99 | 0.82 |
| rework-loop recall | 1.00 | 0.33 |
| end-to-end duration error (corrected 2026-09-16) | 1.075× | 1.321× |

**Unequal-sample qualification (2026-09-16).** The oracle medians describe eight
programs; the search medians describe three. The 43-point difference in
ceiling-relative recall is therefore not a paired retrieval-loss estimate, and
the earlier claim that retrieval dominates reading error by an order of magnitude
is not established by this table. Availability and reconstruction remain useful
per-task measurements; retrieval effects should be computed on matched tasks.

**Timing correction (2026-09-16).** The earlier 1.5×/2.4× numbers did not score
the LLM's actual end-to-end predictions: `process_timing.median_days` was ignored
and replaced with a sum of step medians. Using the saved explicit predictions
gives 1.075× for oracle and 1.321× for search. For example, J3/S10 predicted 240
days against 230 gold, not the previously scored 101 days. The earlier claim
that the LLM believed optimistic pages and failed to price queues is retracted;
the original answers often explicitly discuss queues and measurement scope.
These are small, unequal task sets and point-prediction results, not calibration
evidence. See [the new pilot and scoring notes](2026-09-16-bayesian-process-v3.md).

**Calibration caveat, recorded against ourselves.** Synthetic rework recall under oracle is 1.00 while the real-world pilot is 0.00–0.25. The synthetic FAQs disclose correction loops more explicitly than real municipal FAQs do. `p_publish_faq` and the FAQ reveal-set are too generous about rework; tighten before treating synthetic rework numbers as predictive of the real task.

### First (agency, task) priors, and why the tuple needs six dimensions (2026-09-15)

Taxonomy in `pipeline/priors/taxonomy.json`; per-slug observations in `pipeline/priors/observations/`; aggregation in `pipeline/priors/rollup.py` → `dashboard/data/priors.json`.

**Alex's question was whether a step is an (agency, task) pair. It cannot be**, for one reason that the data makes concrete: elapsed time is `touch + queue`, and those two obey different laws. Touch time scales with the task and the artifact; queue time scales with backlog, batching cadence, and who is holding the ball. A daily cashiering batch and a monthly council calendar are the same (agency, task) and are never the same duration. The step key is therefore six-dimensional — agency class, task type, channel, blocking party, cadence, jurisdiction class — and durations are recorded as touch, queue and elapsed separately wherever a source supports the split. Evidence carries one of five tiers, from `verifiable_official` down to `community_reported`, so a prior can be quoted with the quality of its backing.

**First cut, 3 of 9 slugs (225 observations, 100 step keys):** 95 community-reported, 45 statutory, 42 verifiable-official, 39 designed-document, 4 inferred.

The immediately useful statistic is the ratio of measured duration to statutory cap, per step key — a general-purpose complexity finding, not a per-program anecdote:

| step key | measured median | statutory cap | ratio | n |
|---|---|---|---|---|
| records unit · decision (CPRA determination) | 150 d | 10 d | **15.0×** | 7 |
| caseworker · decision (UI determination) | 100 d | 35 d | 2.9× | 4 |
| background check · records check (DROS) | 15 d | 10 d | 1.5× | 10 |
| records unit · decision (SF, stricter local clock) | 25 d | 17 d | 1.5× | 6 |

Historical interpretation: these ratios motivated the hypothesis that clocks
bind differently across task types. They do not establish that causal claim,
and the Benchmark 2 timing failure previously cited here was partly a scoring
bug (see correction above). Matching the start/end events and statistic type is
required before comparing statutory clocks to measured practice.

Known gaps in the first cut: 5 observations arrived with an unspecified step key; `touch_days` is populated far less often than `elapsed_days` (sources rarely separate them, which is exactly why the queue term has to be modelled rather than read); 6 of 9 slugs still extracting.

### Retrieval realism (2026-09-15)

Search-process discrepancy raised by Alex and traced: the solver issues real-search syntax (`site:`, quoted phrases) which the mock BM25 was silently ignoring, penalising good search behaviour. Fixed in `pipeline/procbench/web.py` (operators honoured, operator use logged, authority prior by document kind). Remaining gaps and the calibration plan are in `benchmark/synth/DESIGN.md` §"Retrieval realism". Headline caveat to carry into any write-up: **the measured retrieval gap is a lower bound**, because the mock corpus has no 403s, no JS shells, no Wayback-only documents, no scanned PDFs, and a reddit search that works better than the real one.

### Fitting the model to the evidence, rather than writing it once (2026-09-15)

Alex's framing: search, decide what counts as evidence, ask whether the current model explains it, infer latent timescales, expect contradiction because processes change, expect distributions rather than point estimates, and infer the latent attributes that best explain everything. That is an EM shape, and two pieces now exist.

**1. `pipeline/procbench/incremental.py` — structure, fitted one document at a time.**
- *E-step (assignment)*: each candidate step extracted from a new document is assigned to an existing node, or judged a refinement, a contradiction, or a **new** node. The new-node option is what makes this nonparametric — the number of steps is not fixed in advance, and opening one is the model's own decision, which is the formal version of "are we finding new steps or old ones".
- *M-step (update)*: confirming evidence merges into the matched node, sharpening actor, timing, fee and order, and accumulating provenance. A field conflict is **recorded as a contradiction with both sources and their tiers**, and the better-tiered source wins, rather than being silently overwritten.
- Outputs `trajectory.jsonl` (per document: candidates, new, match, refines, contradicts, model size), giving a **saturation curve** and therefore an endogenous stopping rule (`--stop-after-quiet k`) instead of an arbitrary step cap, plus marginal information value per document kind.
- Retrospective saturation curves from the existing traces show why this matters: novelty is back-loaded, not decaying. The Ellinsport solar run gained 6 of its 10 recoverable steps on its fifth and final document, so the step cap, not the information, was binding. A fee schedule yielded zero new steps every single time it was opened; an ordinance yielded seven cold; a reddit thread yielded three that nothing else disclosed.

**2. `pipeline/priors/latent_timing.py` — durations as a latent distribution, not a point.**

Evidence about duration arrives as five different objects and must not be pooled: official p50/p90 are **moment constraints**; observed values are **samples**; community reports are **tilted samples**; ranges are **quantile anchors**; and a statutory cap is a **policy, not an observation** — it is excluded from the fit and instead yields a derived P(exceed). Model is LogNormal per step key; recency half-life 3 years, and the fit is reported weighted and unweighted so drift is visible. 86 step keys fitted from 620 observations.

Three results, two of them uncomfortable and therefore worth keeping:

- **The selection tilt is not identified, and its sign is wrong.** Pooling the step keys that carry both community and official evidence gives a median log-ratio of **−0.47**: applicants report *faster* durations than agencies publish. A selection story predicts the opposite. The estimator therefore applies **no correction** and says so, rather than clamping to zero and implying one. The likely cause is segment mismatch — an applicant times the interval they personally experienced, an agency times a broader one — which is a measurement-alignment problem, not a bias to divide out. Flagged per key wherever the two disagree by more than 3×.
- **Statutory caps are exceeded systematically, and the probability is now a number rather than a ratio of medians.** Records determinations exceed their 10-day cap with probability 1.00; benefits determinations exceed a 35-day cap with probability 0.93; a firearm background check exceeds its 30-day cap with probability 0.19. The ordering still tracks codability: the more mechanical the task, the more the clock binds.
- **Drift is real and large.** 23 step keys carry enough dated evidence to refit on the recent half. Records determinations have got **faster** (0.41× since 2026), while plan review has got **slower** (1.73× since 2025). Averaging over a 1999–2026 corpus would have hidden both.

Next: wire `incremental.py` into the real corpus (it currently needs a `docs.json`, which `real_docs.json` already almost is), log retrieval on the real side so the search budget is measured there too, and feed the fitted distributions back as priors so a solver predicts a duration *distribution* and is scored on calibration rather than on a point estimate.


### Corrections to earlier reported numbers (2026-09-15 review)

An audit of the statistical code found four defects (details in `docs/2026-09-15-generative-model.md` §12). Numbers
reported before that audit and now superseded:

- **Drift factors** were computed with an observation variance passed through a square root and with the
  first observation acting as its own prior. Median "now" estimate moved 9.7%. Specifically: plan-review
  document review drift **0.58× → 0.35×**; state-agency decision **0.34× → 0.21×**; background-check
  records check 1.51× → 1.33×.
- **"The act type barely narrows the actor" is retracted.** Normalised entropy is not comparable across
  act types with different category counts. Against a proper null, 8 of 14 act types are informative
  about the agency; document review gains 1.10 bits. A transferable affinity prior is partially viable.
- **"No bunching below statutory deadlines" is retracted.** Observed mass just below the cap is 1.88× the
  fitted distribution's expectation, i.e. weak evidence *for* a deadline effect, on 17 observations.
