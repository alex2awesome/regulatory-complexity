# CalFresh: process results and the next scientific decision

21 September 2026. This is the short current handoff; the chronological detail
is in [the implementation record](2026-09-21-process-structure-first-pass.md).
The full end-to-end CalFresh goal is **not complete**. Only **10 of 58 counties
have county-resolved structure readings beyond the three administrative
functions**; the other 48 have effectively indistinguishable, pooled profiles.
This is not 58 independently learned county process inventories.

Updated after the [morning audit](2026-09-21-morning-audit-and-evidence-recommendations.md):
the current work order is **CalFresh county instructions first**, reusing held
documents before retrieval, with a small action-grain review. No concealed-carry,
Solar, synthetic, broad forum queue, assumption-driven full fit, or Joint47
retry is part of this pass. The frozen fitted artifacts remain unchanged.

## What the model now does

There is a working joint availability posterior over 20 action types in 58
counties. It separates whether an implementation contains an action from
whether a particular source mentions it. Unknown county identity remains a
categorical latent variable shared across an account, not a guessed department
name or independent county guesses for every sentence. The action universe
includes applicant reports as well as administrative documents.

The fitted structure evidence is still small: five local documents collapsed
into four publisher groups, 18 adopted initial-episode forum accounts (10 with
known counties, eight with uncertain counties), and the administrative source
readings. This is **not all 945 forum threads**. Other fitted clock components
use their own reviewed cases. The already-staged later structure slices supplied
the eight-account development check; no successor reading queue was opened
under the current work order. More corpus coverage is not being represented as
model coverage.

Consequently, this fit's failure is not an empirical test of all 945 held
threads or proof that the entire held corpus is uninformative. The constraint
demonstrated here is the small, confounded **adopted evidence set**. Existing
case narratives may still contain useful occurrences or timestamps; they are
not being discarded, and no new broad forum collection is needed to keep them.

Of 1,160 county/action cells, **817 (70.4%) have no county-resolved reading**.
The 453 resolved readings cover 343 distinct cells: 174 administrative readings,
199 forum readings, and 80 readings from the four document publisher groups.
Another 160 readings belong to eight accounts with uncertain counties; these
enter through the account-level county mixture, not as observations in each of
58 counties. The ten counties with additional resolved evidence are Alameda,
Butte, Los Angeles, Orange, Riverside, Sacramento, San Bernardino, San Diego,
San Francisco and Santa Clara. Even these ten are sparse, not identified ground
truth. For the other 48, available applicant-facing count means are about
5.10–5.15 with 90% intervals [2, 8]; their similarities reflect the same evidence
pattern and hierarchical pooling, not measured county equivalence.

This inventory is deliberately bounded to the initial application through
decision/withdrawal and first outcome communication. It is not the entire
CalFresh lifecycle. Its 20 action types include 9 applicant-only actions, one
joint interview encounter, and 10 agency-only actions. Accordingly, the maximum
available applicant-facing count in this vocabulary is 10, not 20. Neither count
is the number of actions every applicant must perform.

Existing county administrative records now inform receipt, decision and
expedited-service functions. Each county/field supplies one source observation;
thousands of applications are not replicated as thousands of independent
presence labels. A separately declared, normalized logical constraint allows
receipt to inform filing availability. This is neither a hard filing anchor nor
a complete execution path.

All 174 administrative readings are positive. They support those three common
functions, but do **not distinguish county implementations**. Their effect on
other actions and on the county scale is pooling, not new county-specific
evidence. Before their inclusion, forum silence drove Alameda's receipt-action
probability to about 0.05. Adding administrative positives repairs that symptom
for three actions; it does not establish that the remaining source-detection
model is calibrated. The logical implication propagates uncertain receipt
availability to filing; it does not itself assert that either is present.

The learning machinery is Gibbs sampling for discrete availability and source
detection, with elliptical slice sampling for the whitened Gaussian hierarchy.
The current hierarchy update integrates out availability during its update,
then samples aligned joint inventories. It is Monte Carlo inference, but not
NUTS/HMC and not a wholly conjugate beta-binomial model. Count distributions
come from sums within these original joint draws. The one selected-positive
repeat component also has a direct quadrature calculation, not just MCMC.

## What improved—and what did not

All four administrative-evidence fits and both receipt-implies-filing fits
passed the numerical gates. The latest two took about eight minutes each,
concurrently on the local machine. Their maximum R-hat is 1.0071 and minimum
bulk ESS is 1,023. No failed gate was waived and no condition was selected.

On the same eight development accounts, with 153 scored action-mention cells:

| Model | Brier score; smaller is better |
|---|---:|
| Pooled forum-by-action Beta baseline | 0.06066 |
| Original occupancy, low-detection Beta(1,4) prior | 0.06778 |
| Original expanded occupancy, base source prior | 0.07762 |
| Occupancy plus administrative evidence | 0.07257–0.07266 |
| Above, plus receipt-implies-filing | 0.07213–0.07220 |
| Original occupancy, high-detection Beta(4,1) prior | 0.10461 |
| Prior-only reference | 0.13056 |

The added evidence improves on the Beta(2,2) base, but **does not beat the
earlier low-detection condition**, and every fitted condition loses to the
pooled baseline. The original short table wrongly omitted this comparison.
The baseline is itself Bayesian. This is not an LLM comparison, a timing score, or recovery of
unobserved process truth. These accounts have been reused for development;
further tuning on them would not be new validation.

Earlier 15-action comparisons also lost: four document-publisher holdouts
(60 cells) scored 0.29500 versus 0.21111 for the step-and-source-type Beta
baseline; ten mixed-source folds (210 cells) scored 0.14646 versus 0.11848.
These are different evaluation sets, not entries on the 153-cell leaderboard.
The numerical record also retains a failed narrow-county-scale pilot and
11 failed detection-pooling folds out of 20. Passing later fits does not erase
these failures. Sources: `calfresh_phase3/summary.json`,
`calfresh_phase3/mixed_source_prediction/summary.json`, and
`calfresh_phase3/detection_pooling_numerical_diagnosis.json` under
`runs/process_structure_20260921/`.

The latest county-effect coordinates show only about 9.1–9.2% mean marginal
prior-variance contraction. That is a diagnostic, not an exact fraction of
information learned. More importantly, these are effects on **availability**,
not service speed or intrinsic agency capability. No capability ranking is
supported.

Separating actors changes how the counts should be read. For the two latest
logical-support settings (administrative false-positive assumptions 0.02 and
0.10, respectively), the available applicant-facing counts are:

| County | FP 0.02: mean [90% interval] | FP 0.10: mean [90% interval] |
|---|---:|---:|
| Alameda | 3.57 [2, 6] | 3.53 [2, 5] |
| Los Angeles | 7.51 [6, 9] | 7.52 [6, 9] |
| Sacramento | 3.36 [1, 6] | 3.30 [1, 6] |

Alameda's remaining roughly 4.6–4.7 action types are agency-only. These examples
illustrate the counting unit; they do not validate county contrasts or establish
a ranking. In particular, Alameda's resolved nonadministrative evidence is
three forum accounts, Los Angeles's is a staff document, and Sacramento's is
a public guide: county and source genre are confounded here. On the four
known-county development accounts the latest constrained model's Brier score
is about 0.0757 versus the baseline's 0.0568. Uncertain-county assignments can
also feed back from these weak inventories; they are not validated geographic
identifications. The earlier source-prior sensitivities are retained separately, not
averaged into these intervals. Count intervals are calculated from aligned
joint binary inventories; an individual action's availability probability is a
different output.

## What the other evidence contributes

Seven timing families remain attached to their actual endpoints. An
application-to-interview interval spans a phase; it is not the duration of the
interview. Phone-queue exit includes answer, abandonment or disconnection, not
just successful contact. SAR7, recertification, benefit availability and card
delivery have their own lifecycle scopes. The application-to-decision main
condition failed its numerical gate and has no headline estimate.

One deduplicated account supports three completed additional paperwork rounds.
It informs continuation conditional on a positive reported episode, under the
retained reporting-severity sensitivities. It does not identify how often
applicants need rework, and its lifecycle/action identity is unresolved. It
therefore cannot be assigned to the initial `correct_information` action.

Thirty adopted source-scoped requirement facts are retained, with nine held
facts. Channel alternatives are not cumulative requirements; conditional
document requests are not universal checklists. These are descriptive features,
not a scalar stringency score or extra independent likelihood factors.

The CF296 fields also reconcile into 110,809 approvals, 73,700 denials and
10,025 withdrawals among 194,534 recorded July 2025 dispositions. Those realized
shares are already observed, conditional on the month's disposed cohort.
**52,570 of the 73,700 denials (71.3%) are recorded as procedural**, versus
21,130 recorded as ineligible. This is an important observed administrative
outcome, not a fitted latent burden measure. The aggregate does not split the
procedural category into missed interviews, missing verification or other
reasons, nor identify repeat counts, eligibility absent the procedure, or the
cause of failure. The 918 CWD-caused denials taking over 30 days are a subset
of denials, not an additional exclusive outcome or all late denials.
A Dirichlet fit would require a different, explicitly declared generating or
future-cohort target; it would not create uncertainty about the observed census
shares or identify intermediate paths. No new branch fit was added.

The earlier administrative timing comparison is also preserved, not discarded:
the county-specific Dirichlet half-count predictor scored 0.252282 categorical
log loss, versus 0.252749 for the passing V6 base. That comparison concerned
later recorded timing bins on an outcome-conditioned retrospective frame, not
intrinsic capability or blind forecasting. Its [results and limitations](2026-09-20-calfresh-current-findings.md#administrative-prediction-preserve-the-unfavorable-comparison)
remain available; no new county timing hierarchy was fitted.

## Why more sampler work cannot finish the current goal

For a simple illustration with an available action and no false-positive
mentions, let `r` be case participation and `d` the chance that a participating
person describes it. A forum likelihood sees `p = r*d`. Both `(r,d)=(0.9,0.1)`
and `(0.1,0.9)` give `p=0.09`. More observations of the same kind can pin down
the product without distinguishing the factors. This is an identification
example, not a fitted CalFresh parameterization.

Similarly, observing a phase total does not uniquely allocate it among the
activities inside that phase. A structural prior can produce such an allocation,
but the allocation then depends on that assumption. Source trust, case mix,
reporting selection and agency effects need overlapping, compatible evidence
before they can be separated.

This does **not** mean no larger Bayesian model can be written. It means a full
numerical posterior now requires additional scientific assumptions for paths,
participation, timing allocation and transport between populations/eras. Those
would not be harmless compiler defaults or measurements of agency capability.

## Current next steps

**Decision received, 21 September 2026:** Alex approved targeted evidence
collection first, followed by explicitly stated assumptions where the needed
evidence cannot be found. The previous no-new-retrieval restriction is lifted
for those missing CalFresh quantities only. See the
[targeted evidence and assumptions work record](2026-09-21-calfresh-targeted-evidence-and-assumptions.md).
The supported result above stays frozen and partial; assumption-conditional
results will not replace it or be described as data-identified quantities.
The subsequent CalFresh-only audit work order puts the evidence pass first
and holds the assumption-driven full fit. The historical calibration and
assumption scenarios already recorded there are not new county estimates.

Recommended: obtain targeted evidence for the missing links before expanding
the latent model again. Keep the supported posterior as a partial result.
The most useful additions would be:

- independently supported county action inventories, including conditional
  requirements and genuine absence labels, to assess detection;
- county-linked case journeys with observed action occurrences, nonoccurrences,
  repeat counts including zeros, and observation windows;
- timestamps on matched phases/activities, with case-mix and source overlap,
  to distinguish reporting effects from agency-associated delays;
- direct effort, fee/payee and waiting-versus-service observations for the
  resource channels the current text does not identify.

The immediate pass inventories one useful official application guide or staff
instruction per county, reusing existing captures first, plus the statewide
CDSS policy layer. New candidates receive one source/county/date/meaning check,
not a separate full verification campaign. Copied statewide instructions remain
one dependent source family. A document's publication/capture date is not proof
that it governed a historical applicant's case.

The successor vocabulary will separate actor actions where evidence supports
it, while preserving shared encounters so one interview does not become two
elapsed-time intervals. Agency-only work stays in scope and needs appropriately
scoped source detection; it is not deleted merely because applicants seldom
mention it. Explicit absence anchors must establish absence in the same scope:
"not required" is not "never available," and silence is not either.

The [first successor crosswalk](../runs/process_structure_20260921/calfresh_county_guides_20260921/action_grain_proposal_sol.md)
now proposes 22 actor-actions: split the joint interview into its two actor
sides, and distinguish active status checking from reading correspondence.
Other composites remain functional acts with attributes rather than being
split mechanically. This is a proposal, not newly fitted structure. Existing
composite positives cannot automatically become two successor positives.
Reading opportunities must be fixed independently of the observed mention:
removing agency nondetections while keeping only their positives would require
an explicit selection model, not the old Bernoulli detection likelihood.

There is no demonstrated universal document-count threshold. A second
independent, overlapping instrument improves the design but does not by itself
identify presence, detection, participation and trust. No new fit is justified
merely by reaching 58 downloaded pages. Contacting agencies or requesting
records would require separate authorization. Current acquisition and the
action-grain proposal live in
`runs/process_structure_20260921/calfresh_county_guides_20260921/`.

## Where to look

- **Consolidated result, now generated:**
  [readable guide](../runs/process_structure_20260921/calfresh_phase5/supported_result_v1/README.md),
  [complete JSON](../runs/process_structure_20260921/calfresh_phase5/supported_result_v1/result.json),
  [action probabilities CSV](../runs/process_structure_20260921/calfresh_phase5/supported_result_v1/step_availability.csv),
  [actor-specific count posteriors CSV](../runs/process_structure_20260921/calfresh_phase5/supported_result_v1/available_action_counts.csv).
  All nine model settings are retained separately across 1,160 county/action
  rows. This is a unified result/report, **not a joint posterior across the
  independently fitted components**.
- Latest fitted structure and scores:
  `runs/process_structure_20260921/calfresh_phase2/logical_support_development/`.
- Existing draw-preserving execution-compatibility report:
  `runs/process_structure_20260921/calfresh_phase5/compatibility_report.json`.
- Source-scoped requirements:
  `runs/process_structure_20260921/calfresh_phase1/stringency_adopted/`.
- Completed-positive repeat component:
  `runs/process_structure_20260921/repeat_blocks_phase4/positive_count_component_v1/`.
- The independent [completion-gap assessment](../runs/process_structure_20260921/calfresh_phase5/joint_process_closeout.md)
  separates what is currently supported from a possible new model target.

The last full repository test run performed for this CalFresh closeout passed
2,362 tests; no full-suite rerun is needed for this reporting/retrieval pass. Mechanical tests,
successful sampling and hash replay are not substitutes for statistical recovery.
The reporting code received an independent Sol review; Luna assembled the
existing source metadata and timing links. Root corrected omitted uncertain-
county source counts, stale phone33/SAR10 register labels, the finite-cohort
versus superpopulation distinction, and ambiguity between approval notification
and the internal decision instant. Earlier candidate versions are archived.
No commit, data deletion or raw-corpus rewrite was performed.
