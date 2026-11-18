# Solar evaluation: execution checkpoint

September 22, 2026, 18:36 UTC. Alex has assigned bulk acquisition/reading to
Claude and explicitly prioritized Bayesian evaluation/comparison for Codex.
No new download or parsing queue was started by Codex for this experiment.

## Administrative timing comparison: running, no score yet

`runs/solar_evaluation_20260922/admin002/` freezes the first matched comparison:

- Existing through-2021 county/AHJ permit-review fit; all four original phase
  gates passed. This test uses only the independent permit-review component.
- Exactly 2,238 original training rows, including 206 raw zeros and 104 raw
  positive one-day reports. No training values or source rows are summarized away.
- 64 metadata/hash-selected held-out queries: 32 unseen-authority cells through
  2021 and 32 future-2022 cells. The latter include 31 previously observed owners
  and one unseen owner. The aggregate deliberately weights the strata equally.
- Five independent GPT-6 Astra, xhigh direct-estimation runs; two concurrent.
  All get the same frozen, lossless anonymized table, no test values or Bayesian
  outputs. Shell/web/app/agent tools are disabled for this opt-in baseline mode;
  a fail-closed event audit checks for any remaining tool use.
- Primary comparison: predictive 90% interval score in **business days for a
  reported administrative cell median**, not a confidence interval for a pooled
  median, an individual case duration, or whole-project burden. Both methods use
  the same declared test-outcome coarsening at one business day.
- Simple baseline, repeated LLM variability, coverage and paired county-cluster
  uncertainty are included. The split was previously inspected, so this is
  exploratory, not a fresh confirmatory test.

`admin002/INPUT_AUDIT.md` records the one bounded independent input check.
`admin001/INVALIDATED_BEFORE_SCORING.md` preserves two corrected setup defects:
coarsening the training table incorrectly, and calling every future owner known.
The two in-flight admin001 calls were stopped before scoring; admin002 retains
the exact same 64 test IDs. No favorable sample reselection occurred.

## Forum timing comparison: split and scoring contract frozen

`runs/solar_evaluation_20260922/forum001/` holds a contributor-grouped split of
the most-supported existing forum clock, final inspection to PTO: 48 training
reports and nine held-out contributors. Eight test outcomes are bounded intervals
and one is right-censored. None is an exact uncoarsened point label.

`runs/solar_evaluation_20260922/forum_comparison002/` freezes the matching LLM
packet and a common 19-point predictive report CDF. Both methods use the same
piecewise interpolation; scoring is interval probability or survival probability,
not error against an invented midpoint or completed pending wait. Five baseline
runs are running. This is a small selected-forum pilot, not county capability,
source-bias calibration, or representative California applicant prediction.

The source-frame's declared approximate unit/rounding transformations are
inherited by both predictors; no new conversion or extraction is performed.
The initial native fit attempt stopped before sampling on a stale ledger digest.
The corrected 102-coordinate native execution completed but failed its mixing
gate (case-spread bulk ESS 198.11). The already implemented exact marginalization
of independent case effects then fitted the **same prior and likelihood** in two
coordinates: `forum001/fit003_exact_marginal/` passed, worst R-hat 1.00145 and
minimum bulk ESS 4,471.23. The 128-to-256-point integration check also passed
(maximum log-likelihood change 2.92e-8). No held-out result was used to choose
scientific assumptions or loosen a gate; failed attempts remain recorded.

The Bayesian new-report CDF, including Student-t reporting noise/contamination,
and a training-only maximum-likelihood baseline CDF are saved in
`forum_comparison002/`. Held-out labels have not yet been scored against LLM
results. Comparison001 was superseded before execution only because the source
packet gained quotation metadata; comparison002's actual LLM prompt is
byte-identical, as documented beside the earlier manifest.

Live root jobs at this checkpoint: administrative repeats session78110 (two of
five completed), forum repeats session74682 (running). All completed baseline
transport audits so far report zero tool calls. No comparative win/loss result
has been declared. The scorer retains the fixed 50/50 administrative-stratum
weighting inside the paired county bootstrap as well as in the point estimate.

## Structure result: failed, not used as a validated posterior

The full 50-action, 440-AHJ fit completed at 18:08:49 UTC and failed its gate:
worst R-hat 1.08024, minimum bulk ESS 43.13, 6,599 of 22,220 diagnostics flagged.
The detection likelihood and jurisdiction scale also failed; this is not just
an unimportant isolated prior coordinate. No retry/extension was launched.

Receipts: `runs/solar_forum_20260922/model_bridge/full_universe_successor001/fit001_positive_anchors/RESULT_REVIEW.md`.
No step-count or agency-capability superiority claim follows from this run.
The earlier shared-journey preflight is marked do-not-fit pending compiler repairs;
it is not substituted for a validated full process model.

## Code and next output

- `pipeline/procbench/solar_panel/evaluate_same_evidence.py`: frozen administrative
  packets, repeated baseline execution and paired scoring.
- `pipeline/procbench/solar_panel/prepare_forum_evaluation.py`: contributor-grouped
  forum train/test split with source bindings.
- `pipeline/procbench/solar_panel/evaluate_forum_predictions.py`: matching new-report
  CDF prediction and interval/censor scoring.
- `pipeline/procbench/infra/codex_runner.py`: existing shared transport, with an
  opt-in restricted-tool baseline mode; ordinary parsing calls are unchanged.

The OpenAI Docs skill informed the opt-in runner's controls, checked against the
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
No broad test-suite or corpus-verification campaign was run: only targeted
transport, split-selection and scorer checks.

Next deliverable is an actual score table with all five repetitions, failures /
fallbacks and uncertainty. The full county-by-county process-model goal remains
unfinished; these evaluations test usable components rather than redefining
that goal as a pair of passing timing fits.
