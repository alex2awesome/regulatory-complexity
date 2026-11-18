# Solar permitting: the Bayesian model, executed, with forum evidence

Stages B, C and part of G of `docs/2026-09-20-solar-leg-plan-for-claude.md`,
against the estimands frozen before any fit. **The headline is that the model
fails its own prespecified decision rule on both held-out splits.** That is
reported first because the rule said a loss is a finding and does not license
acquiring more data.

No benchmark truth was read. No network was used. Nothing outside this leg's run
directory was modified.

| artefact | path |
|---|---|
| frozen estimands, v1 and v2 | `runs/solar_panel_20260920/estimands_frozen_v{1,2}.json` |
| panel, 30,016 rows, 9,586 present | `runs/solar_panel_20260920/panel_v1.csv` |
| verified forum dataset | `runs/solar_panel_20260920/forum_v1.json` |
| primary fit and draws | `runs/solar_panel_20260920/fit_primary.json`, `draws_primary.npz` |
| sensitivities | `fit_sameday_half.json`, `fit_floor_n.json` |
| failed random-slope fit, preserved | `fit_random_slope_FAILED.json` |
| held-out scores and the reporting offset | `score_and_offset_v1.json` |
| code | `pipeline/procbench/solar_panel/` |

## 1. The model fails the decision rule

The rule, frozen before fitting: beat the raw cell median and two-way fixed
effects on 90 percent interval score on **both** splits, with coverage between
0.85 and 0.95.

| split | model | raw median | fixed effects | model coverage |
|---|---:|---:|---:|---:|
| held-out authorities, 910 cells | 4.260 | **4.046** | 4.780 | 0.81 |
| forward year 2022, 1,595 cells | 3.604 | 3.553 | **3.501** | 0.89 |

Lower is better. The model loses to the raw cell median on both splits, and its
coverage is outside the band on the authority split. Verdict: **fail**.

One detail is worth more than the verdict. On the forward-year split the model
has the best point predictions of the three, a median absolute log error of
0.415 against 0.504 for the raw median and 0.493 for fixed effects. It loses on
the interval score, which penalises width. So the hierarchy predicts the centre
better and quantifies its uncertainty worse. That is a specific, fixable defect
rather than a general failure of the approach, and naming it is the point of
having frozen a proper scoring rule instead of an accuracy headline.

## 2. What the model does say, where it converged

Crossed hierarchical lognormal on log median business days, 4,101 training cells
across 333 authorities, four chains of 1,500 draws. Deliberately not the V6 trace
model: there are no cases, no repeat blocks and no route uncertainty in this
panel, so the trace machinery would have added nothing.

| quantity | estimate |
|---|---|
| between-authority spread, log scale | 0.340 |
| ratio of a 90th-percentile authority to a 10th-percentile one | 2.39 times |
| load elasticity, per doubling of local installations | −2.3%, 90% interval −3.8 to −0.8 |
| convergence | max R-hat 1.0012, minimum bulk effective sample size 1,022 |

Two results in that table deserve separate treatment.

**Authorities differ by a factor of 2.4 between the tenth and ninetieth
percentile**, after year, phase, size class and technology are accounted for.
That is the cross-jurisdiction variation the project exists to measure, and it
is the one estimate here that is both well identified and robust across both
sensitivities.

**More local demand associates with slightly faster processing, not slower.**
This is the opposite of a congestion story. The effect is small and the interval
excludes zero. I would not read it causally: authorities with high volume are
plausibly the ones that invested in staff or automation, so this is association
under an exposure assumption, not a capacity result.

### The random-slope model failed, and the failure is informative

The plan specified an authority-specific load elasticity. Fitted, its spread
parameter collapsed to 0.008 with R-hat 1.45 and an effective sample size of 13,
while every other parameter converged. That is a variance parameter pinned at
the boundary: the data do not support authorities differing in how their times
respond to load. The failed fit is preserved rather than deleted, and the
reported model carries a common elasticity. Estimand E2's authority-specific
form is therefore **not estimable from this panel**, which is a stronger and more
useful statement than a wide interval would have been.

### Sensitivities, both prespecified

| condition | elasticity | authority spread | converged |
|---|---|---|---|
| primary, same-day censored at one business day, denominator bounded by installs | −2.3% | 0.340 | yes |
| same-day censored at half a business day | −2.4% | 0.340 | yes |
| every denominator set to the source floor of ten | −2.0% | 0.349 | no, R-hat 1.015 |

The same-day convention, which I had flagged as potentially larger than the
effects being estimated, turns out not to matter here. The denominator
assumption moves the elasticity by a fifth of its size and costs convergence.

## 3. The forum evidence, and the defect that finding it first prevented

Doing the forum preparation before the fit, at Alex's instruction, caught a
defect that would have produced a fabricated result. The administrative panel is
entirely in **business days**. Forum reports are calendar days (139), months
(53), weeks (27), and business days (11). Comparing them unconverted inflates the
forum side by about 1.4 times, which is the same order as the offset being
estimated.

The forum dataset: 234 elapsed rows, every quote re-sliced from its frozen
artifact and verified, zero mismatches. 43 usable for the comparison, of which 33
name their utility outright. That last point corrected a second error of mine:
the latent entity depends on the phase, and because interconnection belongs to a
utility rather than a building department, most forum rows need no latent
assignment at all. The median effective candidate count is 1.0, not the 30 I
first reported.

**E4, the reporting offset: −42 percent, 90 percent interval −59 to −18, on 12
paired reports.** Applicants report permission to operate arriving roughly
40 percent sooner than the administrative panel records for the same utility,
phase and year.

### This number moved twice under validation, and both moves were my defects

| version | offset | interval | reports | what was wrong |
|---|---:|---|---:|---|
| first reported | −36% | −52 to −16 | 27 | dropped cases still in progress |
| after retaining censored rows | −22% | −42 to +8 | 31 | phase mapping admitted gaps between phases |
| **after requiring a complete phase traversal** | **−42%** | **−59 to −18** | **12** | current |

The first defect: 24 forum rows carried a lower bound with no upper, meaning a
case that had not finished when the post was written. Dropping those removes
precisely the slow cases. They are now retained as right-censored, each
contributing the probability that its true duration exceeds the stated bound.

The second defect was worse and only a semantic spot-check found it. I mapped a
forum row to a panel phase by activity membership alone. Reading twelve mapped
rows against their sources showed about a third were not that phase at all:
some were gaps *between* phases, and several were the post-inspection phase,
which the dataset's own quartile sheet lists separately, recorded as if it were
submission to permission to operate. A row now maps to a phase only if it
contains the activity that ends that phase and carries both an opening and a
completing endpoint. Phase-mapped rows fall from 157 to 29 and paired reports
from 31 to 12. I then read **all twelve** remaining pairs against their sources;
every one is a genuine submission-to-permission-to-operate duration.

Separately, one row stating "48 business hours" was being converted as clock
hours, giving 1.4 days where the author meant six working days. Hour-denominated
rows are now excluded rather than converted under a guess.

Three caveats stand.

- **Twelve reports, eleven of them PG&E.** This is a calibration on one utility.
- **The unit conversion moves it.** Without the calendar-to-business conversion
  the same twelve read −19 percent rather than −42.
- **No duplicate cases**, checked: twelve distinct case identities across eight
  threads, though one author contributes two separate installations.

The direction is now consistent across all three versions and is the opposite of
what this project has assumed throughout, including in my own source-trust note:
these posters report **faster** experiences than the administrative record, not
slower. With twelve reports from one utility I would not build on it, but it is
the first time the assumption has been checked against anything.

## 3a. Validation

**The sampler is verified against an independent computation.** Conditional on
the variances the model is a linear Gaussian mixed model with a closed-form
solution. Recomputing that solution directly from the panel, averaged over 120
posterior draws of the variance parameters to match what the sampler integrates,
agrees with the sampler's posterior means to a worst difference of **0.0023**
against a tolerance of 0.05. An earlier version of this check appeared to fail
at 0.23; the cause was the check itself, which evaluated the closed form at a
point estimate of the variances and excluded the censored cells the sampler
augments. Both were fixed rather than explained away.

**Prior recovery** at a second seed and a larger simulated panel: a planted
elasticity of −0.18 recovered inside [−0.19, −0.16], and a planted authority
spread of 0.55 recovered as 0.55.

**Twenty source-free tests** in `tests/test_solar_panel.py`. Three pin defects
actually made here, including one asserting that dropping censored reports
biases the offset downward. Full suite 1,654.

**Extraction coverage.** 63 of 198 frozen solar documents are cited by nothing
in the ledger. Classifying them: 12 are off-topic for permitting, 29 are topical
with no duration phrase, and 22 are topical and contain one. Reading ten of
those 22 shows they are mostly out of state (Missouri, the Carolinas, Wisconsin,
New Jersey) or about warranties and payment terms rather than permitting
timelines. Perhaps one or two are genuine misses. Coverage looks appropriate; it
is not certified, because I did not read all 63.

## 4. What this leg has and has not established

Established: the panel is built and hash-bound; the design separates authority
from year and phase; authorities differ by a factor of about 2.4; the
authority-specific elasticity is not estimable; the forum quotes are verified and
their units are reconciled; and a reporting offset has been estimated for the
first time in this project, with the answer that no offset is detectable.

Validated: twenty source-free tests in `tests/test_solar_panel.py`, covering the
unit conversion, the phase partition, the censoring direction, the interval
score, the exposure centring, recovery of a planted elasticity and authority
spread from simulated data, and the convergence diagnostics. Three of them pin
defects that were actually made during this work rather than hypothetical ones.
The full suite is 1,654 tests.

**Not validated: extraction coverage.** 66 of the 198 frozen solar documents are
cited by no measurement and no activity in the ledger. Whether those were read
and found empty, or never read, cannot be told from the ledger, and I did not
re-parse them. Of 234 forum elapsed rows, 47 reach the comparison; 75 carry no
numeric bound at all and are correctly excluded, but 62 fail only on phase
mapping and 86 on locating evidence, and those are extraction gaps rather than
absences in the sources.

Not established: any causal claim, since the elasticity is association under an
exposure assumption; anything about 2023 or 2024, which exist in the panel only
to give the offset a contemporaneous counterpart; the inspection endpoint, which
is ambiguous in the source itself; and any claim of novelty, because the
literature check the plan requires could not run in this session.

Not attempted here: estimands E3, the composed applicant clock, and E5 and E6,
the step counts and permit cost that Stage A discovered in the source's
companion file.

## 5. What I would do next, in order

1. **Fix the uncertainty, not the point estimate.** The model already predicts
   centres better than both baselines and loses on interval width. The
   likely cause is the sampling-error term, where the denominator is bounded
   between ten and the installation count and I used the optimistic end.
   Re-score with the interval widened to the bound rather than the point.
2. **Re-run the decision rule after that**, and report again whether it passes.
3. **E5 and E6**, the step counts and permit cost, which are the applicant-facing
   channels and need no new modelling, only joining and describing.
4. **The literature check**, before any of this is written up outside the
   repository.
