# Solar: first forum-vs-administrative calibration (interconnection application -> PTO), 2026-09-30

Follows `docs/2026-09-30-solar-results-reconciliation.md` (its recommended next fit). Code and outputs:
`runs/solar_ix_calibration_20260930/` (`build_dg_anchor.py`, `fit_ix_offset.py`, `dg_anchor.json`,
`ix_classify_out/`, `fit_results.json`). Standalone exact-grid model, not yet a V6 program.

## Question
Do forum reports of "interconnection submitted -> permission to operate" describe what actually
happens to residential applications at the same utility, or are they biased (e.g. toward long waits)?

## Data
- **Administrative anchor (DG Stats, extract 2026-08-31):** 1,301,743 approved + 355 terminal residential PV applications
  (<=10 kW AC, received 2017–2025, Expansion applications and applications superseded by a
  resubmission excluded, withdrawn/replaced/terminated counted as terminal). Median received ->
  approved by utility-year: PG&E 3–15 d, SCE 3–24 d, SDG&E 5–25 d, except **2023 (90–141 d)**, the
  pre-NEM-3.0 rush when applications were filed before installation. DG Stats publishes only resolved
  applications (every row carries an approval date), so the anchor is completion-conditioned and the
  latest year is right-truncated.
- **Forum reports:** the 286 claims on this clock (clock crosswalk), screened by Gemma for (a) the
  interval starting at a submission made *after* installation, (b) truly this interval, (c) utility
  PG&E/SCE/SDG&E, (d) not outside California: **77 reports, one per contributor** (69 completed,
  8 still waiting; PG&E 34, SCE 36, SDG&E 7). Hand check of 12: 11 correct (one was an installer's
  delay before submission). Project years are unknown, so each utility's anchor is its yearly
  distributions mixed by application volume.

## Model
log(reported days) = log(actual days) + delta + sigma * t4 noise, actual days ~ the utility's DG
Stats distribution (Kaplan–Meier over fine log bins), 5% contamination (log-uniform 0.5–3,650 d);
priors delta ~ N(0,1), sigma ~ HalfNormal(1); completed reports are intervals, waiting reports are
lower bounds. Two parameters -> exact posterior on a grid (no sampler, no convergence question).
exp(delta) = reporting ratio (forum / actual).

## Result

| fit | reports | reporting ratio exp(delta), median [90%] | extra report noise sigma (log), median [90%] |
|---|---:|---|---|
| primary (anchor 2017–2025) | 77 | **0.89 [0.62, 1.15]** | 0.25 [0.07, 0.57] |
| anchor without 2023 | 77 | 1.02 [0.80, 1.32] | 0.21 [0.07, 0.51] |
| anchor without 2023 and 2025 | 77 | 1.06 [0.85, 1.35] | 0.21 [0.07, 0.51] |
| + reports with unclear start | 114 | 1.02 [0.80, 1.30] | 0.25 [0.07, 0.55] |
| PG&E only | 34 | 1.04 [0.67, 1.52] | 0.27 [0.07, 0.63] |
| SCE only | 36 | 0.79 [0.42, 1.30] | 0.39 [0.07, 1.03] |

**For this clock, forum reports are statistically indistinguishable from what the utilities'
records show**: the reporting ratio is ~1 (90% intervals include 1 in every variant) and the extra
reporting noise is small (a typical report is within ~25% of an actual-duration draw). Forum
posters about interconnection are not measurably drawn from the slow tail. Anchor medians: PG&E
10 d, SCE 18 d, SDG&E 14 d; forum completed reports raw median 8 d.

## What this does and does not show
- It is ONE clock where the admin match key (utility) is available for most reports; it does not
  show forum reports are unbiased for permit, inspection or whole-project clocks (no matched admin
  keys yet: only ~13 forum claims carry city + year).
- Year is integrated over (not observed); 2023 matters (ratio 0.89 with it, ~1.0 without), because
  pre-NEM-3.0 early filings lengthen that year's actual durations.
- Admin data are completion-conditioned; forum "still waiting" reports enter as lower bounds.
- Contradicts the September 20 "-42% reporting offset" (flagged as internally inconsistent in the
  reconciliation doc, error 2). Supports treating DG Stats as the anchor for this clock, with forum
  reports informative about the burden around it (installer delays before submission, e.g. the
  "Tesla didn't submit the final permits for 3 weeks" case), not about the utility step itself.

## Next
Port to V6 (`source-offset-hierarchy/2` with DG Stats histogram cohorts as reference) and repeat for
permit application -> issued and issued -> final once forum claims carry city/year keys (Gemma key
extraction from thread context).
