# Bayesian process pilot: results and limits

2026-09-16. **This first implementation does not beat the saved one-pass LLM
baseline.** It improves activity F1 over the old incremental reconstruction,
but overestimates the number of steps and substantially underpredicts time to
decision. These are diagnostic results on one program, not a calibrated or
equal-information benchmark.

## What was run

The [implementation/design](2026-09-16-bayesian-process-v3.md) and
[fully defined TikZ diagram](figures/latex_plate_diagram_simplified/README.md)
separate uncertain process structure, selective/error-prone evidence, case
variation, and payer versus agency burden.

The final run is [`runs/bayes_v3_final/`](../runs/bayes_v3_final/), with
[manifest](../runs/bayes_v3_final/manifest.json),
[posterior](../runs/bayes_v3_final/posterior.json), and
[evaluation](../runs/bayes_v3_final/evaluation.json).

- W1/J1/S03, Street Vending Program: 10 cached document extractions, 89 mentions.
- Four chains, 800 sweeps each, 300 burn-in, thinning 10: 200 retained draws.
- Sixty simulated cases per draw: 12,000 cases in the primary run.
- Seed 20260916. Prespecified count-prior means 10/20/40; 20 is the primary run.
- No new LLM calls. No hidden truth, generator specifications or solver answers
  enter inference. Posterior files are saved before evaluation opens truth.
- Source hashes and input hashes are in the manifest. Runtime for the primary
  run, rescoring and two sensitivity runs was approximately six minutes.

Only this program has the existing document-level cache needed by the adapter.
The one-pass LLM read documents directly; the Bayesian pilot receives legacy
extractions that omit process-level timing and reliable case/scope identifiers.
The comparison does **not** isolate the inference method's causal contribution.
The final directory supersedes development runs `bayes_v3_smoke` and `bayes_v3`.

## Reconstruction and timing

| Measurement, W1/J1/S03 | Old incremental | One-pass LLM, supplied docs | Bayesian pilot |
|---|---:|---:|---:|
| Activities in reported point graph | 25 | 14 | 16 |
| Benchmark activity F1 | 0.5959 | **0.9258** | 0.7952 |
| Explicit end-to-end median estimate | unavailable | **55 days** | 17.9 days |
| Synthetic case-log median | 74 days | 74 days | 74 days |

Sources: [rescored incremental](../runs/bayes_v3_final/rescored/incremental/W1__J1__S03.score.json),
[rescored one-pass baseline](../runs/bayes_v3_final/rescored/oracle_docs/W1__J1__S03.score.json),
and [pilot evaluation](../runs/bayes_v3_final/evaluation.json).
F1 uses the existing lexical, split/merge-tolerant alignment; it is not a
one-to-one graph-identity score. Historical ordering metrics also allow
list-position fallback and should not be treated as proof of recovered edges.

The Bayesian time-to-decision comparison is particularly limited: its prediction
is conditional on represented steps and a decision being reached, whereas the
gold log includes the full generated workflow. The 17.9-day estimate has a
90% future-case interval of **0.88–133.79 days**. Decision time was defined for
76.8% of simulated cases; this is not an estimated real-world approval rate.
The approximate posterior interval for the population median is 0.90–124.06
days and also contains finite case-simulation error. Neither wide interval
establishes calibration.

Closeout of all included activities has a different predictive median,
**93.4 days**. We do not substitute that quantity for time to decision simply
because it is closer to 74 days.

The posterior step-count median is **26.5**, with a 90% interval **[20, 37]**;
the truth is **13**, outside the interval. Count CRPS is 10.894 steps. No retained
draw equals 13; that is zero Monte Carlo hits, not proof of zero posterior mass.
The median represented count is 18, with 8 additional undisclosed steps. These
are ensemble summaries, distinct from the 16-node representative point graph.

For the aligned per-step duration estimates, mean absolute log error is 0.657
and 8/12 pairs are within a factor of two. All 12 matched-pair median intervals
contain their targets, but these intervals are broad, the alignment includes a
duplicate gold step, and many clusters have no usable timing observation. This
is not twelve independent calibration trials. In `model.json`, `n_claims` and
`prior_only` describe the representative partition's cluster; duration quantiles
also average over other partitions using a reference mention and are conditional
on that mention not being clutter.

## Prior sensitivity and diagnostics

| Prior mean for total steps | Posterior median | 90% interval | Predictive decision median |
|---|---:|---:|---:|
| 10 | 24 | [18, 33] | 19.7 days |
| 20, primary | 26.5 | [20, 37] | 17.9 days |
| 40 | 27 | [20, 37] | 16.2 days |

The failure persists across these count-prior choices. This does not assess
sensitivity to disclosure exposure, entity-resolution likelihood, scope rules,
or source accuracy; those assumptions still need independent calibration.

Basic between/within-chain R-hat is approximately 1.00 for total and represented
counts, and 1.013 for clutter. No draw reaches the 100-step computational cap.
These diagnostics concern a few scalar summaries, **not convergence of the full
partition/graph posterior**; no rank-normalized ESS or simulation-based calibration
is claimed. Supported-edge sampling uses a short constrained Gibbs run and has
no separate convergence guarantee.

## Both sides of burden

The primary forecast, conditional on represented activities, includes:

- Agency task executions: predictive median 8, 90% interval [4, 12].
- Total step executions: median 12, interval [8, 16], including repetitions.
- Named agency labels in the inferred inventory: median 8; alias/catalog
  uncertainty and unknown organizations are not fully resolved.
- Documented-fee component: median $180, interval [$0, $355]. This is not a
  validated estimate of total cash burden; duplicated step identities and missing
  transaction IDs remain possible sources of double counting.
- Encounter upper-count proxy: median 3, interval [1, 5], not identified trips.
- Applicant and agency hands-on hours: **unmeasured, null**, not zero and not
  inferred by converting waiting days to labor.

W1 does not provide hands-on labor-hour truth to validate those channels.
Standing organizational overhead, staffing costs, entirely unseen-step burden,
and a full mutually exclusive outcome/abandonment model remain extensions.

## The baseline scoring bug

The old scorer ignored `process_timing.median_days` and substituted a sum of
step medians. Scorer v2 uses explicit process predictions and keeps missing
ones missing. Statutory caps and targets do not count as realized durations.

| Saved runs | Old median multiplicative error | Corrected |
|---|---:|---:|
| Supplied documents, 8 programs | 1.545× | **1.075×** |
| Search, 3 programs | 2.387× | **1.321×** |

These are `exp(median(abs(log(predicted/actual))))`, not average percentage
errors. All eleven saved predictions were rescored without making new LLM calls;
[per-run results](../runs/bayes_v3_final/baseline_rescoring.json) preserve links
to the originals. The synthetic dashboard now shows the corrected end-to-end
values, with historical structural metrics retained. The different task sets
preclude attributing the aggregate gap solely to retrieval.

## Separate real-corpus timing check

The earlier hierarchical timing model is a different experiment, not a synthetic
process-reconstruction result. I also fixed its global-median comparator to
exclude the held-out key, and reran leave-one-key-out evaluation on 44 keys
(`--draws 2500 --burn 600`). The [new output](../runs/bayes_v3_final/real_corpus_loo.json)
has median absolute log errors of **0.7050 global**, 1.1807 family, 0.8499
empirical Bayes and **0.9708 hierarchical Bayes**, with 86% nominal-90% interval
coverage. The global baseline still wins this point-prediction comparison.
The historical dashboard result (Bayes 0.9585) is preserved, not silently replaced.

## Interpretation and next experiment

The run rejects the claim that adding this Bayesian layer automatically improves
accuracy. A coherent posterior can still be confidently wrong under an
uncalibrated disclosure model and a poor activity/alias likelihood.

Plausible contributors, **not isolated causal findings**, are fragmented step
identities, weak agency alias resolution, missing precedence treated as parallel
work, and absent process-level timing/scope claims. Generic duration priors then
dominate many step estimates. Counting undisclosed activities does not identify
their location or burden.

The next useful experiment is an equal-evidence comparison: extract typed
step/segment/process measurements, agency identities/roles, applicability and
transaction/case IDs once; give the identical evidence to both the LLM baseline
and this posterior model; evaluate multiple held-out programs/worlds. Estimate
disclosure/error rates on a separate audited set. Add hierarchical duration
learning and conditional routing only with that measurement contract in place.
Do not tune priors against this one program and call the result held-out accuracy.
