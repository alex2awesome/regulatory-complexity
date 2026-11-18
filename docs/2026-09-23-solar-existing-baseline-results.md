# Solar existing-baseline scoring checkpoint

Scoring was attempted on 2026-09-23 using only the already-frozen five-repeat
answer packets. No predictions, models, retrieval, selection, or input files
were changed.

## Commands and outputs

Before each command, the target comparison output was absent.

```text
uv run --with-requirements requirements-bayes.txt python -m pipeline.procbench.solar_panel.evaluate_same_evidence score --out runs/solar_evaluation_20260922/admin002
uv run --with-requirements requirements-bayes.txt python -m pipeline.procbench.solar_panel.evaluate_forum_predictions score --out runs/solar_evaluation_20260922/forum_comparison002
```

The administrative scorer initially reached scoring but failed while serializing
its result: `TypeError: Object of type bool is not JSON serializable` in
`pipeline/procbench/infra/manifest.py`. The only repair was serialization-only:
cast `fractional_improvement` to a native float when non-null and
`practical_and_uncertainty_gates` to a native bool. Formula, thresholds, data,
and inputs were unchanged. The frozen scorer was then run once successfully;
the result is at
`runs/solar_evaluation_20260922/admin002/comparison.json`. Its five answer
files remain under `runs/solar_evaluation_20260922/admin002/llm_repeat_01..05/answer.json`.

The forum scorer completed and wrote:

`runs/solar_evaluation_20260922/forum_comparison002/comparison.json`

## Administrative result

Lower interval score is better. Across the 64 balanced held-out queries:

| predictor | mean 90% interval score |
| --- | ---: |
| Bayesian predictive interval | 51.01148 |
| training-only simple ML interval | 49.74244 |
| five-repeat LLM mean | 47.95344 |

LLM minus Bayesian was `-3.05804` (Bayesian worse), with paired county-cluster
bootstrap 95% interval `[-10.50734, 3.65430]` for that same difference; the practical/uncertainty gate
was false. The administrative component therefore does not support a Bayesian
win.

## Forum result

This is the frozen nine-contributor final-inspection-to-PTO pilot. Lower loss is
better:

| predictor | mean loss |
| --- | ---: |
| Bayesian predictive CDF | 2.65124 |
| training-only simple ML CDF | 2.65215 |
| five-repeat LLM mean | 2.68135 |

Bayesian minus simple is only about -0.00091. LLM minus Bayesian is 0.03011,
but the paired contributor bootstrap 95% interval is [-0.14482, 0.32590], which
includes zero. This pilot does not support a Bayesian win with meaningful
uncertainty evidence.

The score is a negative log interval-mass/survival score over eight bounded
intervals and one right-censored report, using a common interpolated report CDF.
It is not evidence for the full county-by-county process model, AHJ capability,
or representative California applicant prediction.

## Interpretation boundary

These are component-level, same-evidence comparisons. They do not validate the
new shared-action journey model or establish superiority for step-level
prediction. Both component comparisons now have scores; neither establishes a
Bayesian advantage. The forum result is small, selected,
contributor-grouped, and inherits source rounding/approximation; adjacent
timing reports are not independent source documents.

Scorer source hashes at this checkpoint:

- `evaluate_same_evidence.py`: `10445aff434fa51da1e654c29417d1e7c469b3a87a04972c79030b07d7dc35e9` (serialization-only scalar cast)
- `evaluate_forum_predictions.py`: `cd0dbcc7664afbb7217d2112a0ca24c3856ec7d907ba59b395a3f49aa4f32416`

The agent's first test invocation could not import `pipeline`. Root reran it
through `python3 -m pytest` from the repository root, alongside the new clock,
compiler and sampler checks: 73 tests passed in 4.60 seconds. No corpus-wide
verification or test-suite repair was performed.
