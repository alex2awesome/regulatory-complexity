# Solar: from separate clocks to shared action journeys

Status: shared-action implementation and both eight-case fits complete, 2026-09-23.
Numerical checks passed; an important report-versus-prior conflict remains. This is a bounded integration, not
adoption of all 6,463 episodes or completion of the county-level structure model.

## What this changes

The bulk adoption fit estimated separate contract-to-installation and
installation-to-PTO distributions. Those were **not** a recovered process graph,
and their posterior medians cannot be added to reconstruct one installation.

This increment uses the existing V6 joint visit hierarchy. A reviewed installation
has explicit actor/action occurrences and a dependency graph. Every timing report
observes that same case's latent timeline. A correction followed by another filing
can therefore appear twice in the timeline without becoming two unique action
types. The implementation is not a replacement statistical architecture.

Three different quantities must remain separate:

- Availability: which actions a jurisdiction's process can contain. The existing
  occupancy/detection model addresses this within a supplied action universe.
- Participation and repetition: what this installation actually did, including
  repeated actions. The new compiler carries reviewed occurrences into V6.
- Time: elapsed cycles and event-to-event intervals on the same installation's
  graph. These include unseparated waiting when the source does not distinguish
  waiting from active work.

An incomplete narrative does not identify the full installation step count. A
fixed reviewed path is not a learned posterior over every possible path. In
particular, positive reports of revisions cannot estimate the population
probability of needing any revision without an ascertainment/denominator model.

## Implemented mechanisms

- `pipeline/procbench/solar_panel/compile_action_journeys.py`: merge explicitly
  linked case aliases across packets; use semantic event IDs rather than dates
  as identity; retain geography and source bindings; represent observed repeat
  occurrences; retain completed and pending clocks; separate algebraically
  derived totals from likelihood factors.
- `pipeline/procbench/compact_visit_trace.py`: new `activity_event_interval`
  operator. Each endpoint names an action, its start or end, and its first or last
  occurrence. It uses the actual schedule, including intervening waits and repeat
  loops, rather than summing endpoint durations or adding parallel branches.
- `pipeline/procbench/solar_panel/summarize_action_journeys.py`: summaries of the
  **same reported cases** from joint V6 draws. It distinguishes materialized
  occurrences from unique actor/action concepts and leaves full process counts,
  active work and intrinsic agency capability unknown when unsupported.

Compilation must not drop an inconvenient structural hypothesis and renormalize
the others, or delete an absent predecessor and create a parallel root. The
bounded compiler rejects an unsupported graph as a whole instead. A report that
really sums separate cycle times must say so; an elapsed span uses endpoints.

## Evidence and scope

Frozen input: `runs/solar_bulk_adoption_20260923/adopted001/`, with the original
228 completed packets bound by `frozen_inputs001.json` in its parent directory.
This contains 6,463 contributor episodes and 7,671 extracted action entries.
An entry is not necessarily an observed action: planned, refused, failed,
post-installation service, and descriptive statements are also present.

Work and receipts for this increment live in
`runs/solar_step_model_20260923/`. The initial case selection deliberately seeks
linked timelines and correction journeys to exercise the missing integration;
it is not a representative sample of installations. Broad corpus mapping remains
separate from this bounded first fit and must be counted explicitly.

The inventory audit lives in `action_inventory_audit_luna.json` and `.md` in that
run directory. The existing 50-action occupancy input has only two authorities
with positive readings in both the requirements matrix and agency-document
instruments: Oakland and San Diego. That is a coverage diagnosis, not permission
to discard other counties or impute silence as absence. The previous expanded
occupancy fit failed its numerical gates and is not promoted by this increment.

## Verification boundary

No repeat corpus-wide verification is planned. Checks are restricted to new
clock/compiler regressions, native model input validation, a small source-semantic
spot-check of the selected journeys, and ordinary numerical checks of the fit.
The original packets are not edited. Any changed interpretation is itemized in
the new reviewed declarations.

One concrete correction found already: “within a week” is an upper bound, not an
approximate point at seven days. It must not be fed back as the latter.

## Remaining after the first joint fit

1. Expand semantic action/endpoint mappings across the frozen corpus, with a
   disposition for every entry. Compilation/adoption and likelihood use are
   different counts.
2. Add uncertainty only through explicit supported route, action-identity and
   repeat alternatives; label prior-sensitive alternatives. Silence must not
   fabricate a zero-repeat denominator or an absent action.
3. Connect an adequately identified availability posterior to executable path
   hypotheses without assuming availability means mandatory participation or
   using the same evidence twice.
4. Evaluate shared-case predictions and step counts on held-out evidence against
   a same-evidence baseline. No superiority claim follows from convergence.
5. Estimate source effects or intrinsic agency capability only with crossed,
   boundary-matched evidence; the current conditional forum frame cannot establish
   those quantities on its own.

## What the fitted hierarchy learns

For this bounded elapsed-only fit, an occurrence's log duration has a global
location, a pooled action-type effect, an occurrence-specific effect, a common
case effect, and case/occurrence variation. In shorthand:

\[
 \log d_{ci}=\mu+a_{t(i)}+u_i+0.25h_c+\sigma z_{ci},
 \qquad \log\sigma\sim N(\log 0.6,0.4^2).
\]

Here `c` is the reported installation, `i` is a materialized occurrence, and
`t(i)` is the reconciled action type. The global prior is `N(log(7), 2²)`;
action effects have SD 1 and occurrence effects SD 0.25. The common-case and
occurrence noise coordinates are standard normal. Repeated reviews share an
action type but have separate occurrence durations. Explicit alias mappings
pool the two reviewed spellings of permit-plan review without merging an
inspection-to-PTO gap into an application-review cycle.

The dependency graph schedules each occurrence after its predecessors; a report
observes an event-to-event interval on that **same case trace**. The current
report kernel is a log-scale error mixture, 95% SD 0.25 and 5% SD 2.0. An upper
bound is interval mass from zero; a lower bound is survival mass. These are
assumptions, not source-calibrated reliability estimates. Adjacent date
increments share latent events, but correlated timestamp-reporting errors are
not explicitly modeled. A reconstructed sum is not added as new evidence.

Agency and source effect scales are fixed to zero in this pilot. This deliberately
does **not** estimate intrinsic agency capability or forum bias; it does not
establish that agencies are equal or forums unbiased. Labor channels are omitted.
All current routes are fixed reviewed realizations. Their posterior mass of one
is a conditioning choice, not successful learning of the unseen process inventory.

Sampling is four-chain MCMC, using the existing operation-centered transition,
interwoven case-scale transition and elliptical-slice case updates. New
`--case-update-block-size 1` chunks case coordinates, and `--case-local-updates`
evaluates the exact affected program likelihood. Neither changes the posterior
target. Scalar proposals avoid the poor mixing seen when an entire tightly
constrained long journey moved as one block.

## Frozen inputs and itemized revisions

All paths in this section are relative to `runs/solar_step_model_20260923/`.

- `reviewed_rightwinger_root001.json`: a permit-revision, failed-inspection,
  reinspection and utility-deficiency journey. Ten timed action occurrences,
  seven actor/action concepts and three repeat occurrences; a separate 58-day
  private/project gap is not assigned to the AHJ. Modeled window is permit
  submission to PTO, not contract signing through later meter work.
- `reviewed_irvine_root001.json`: installer revision within one week, then
  approximately one week of city review. Corrects an upper bound previously
  extracted as an approximate seven-day point. Irvine belongs to this commenter,
  not the thread author's different location.
- `reviewed_journeys_sol.json`: sealed J673hdudg and Legitimate_Bobcat450
  declarations. `reviewed_j673_patch_root001.json` adds two omitted adjacent
  increments without editing the original or duplicating its derived total.
- `reviewed_journeys_sol_002.json`: four additional reviewed cases, preserved
  unchanged. `reviewed_followup_root001.json` is the itemized successor: scheduled
  installation is not actual installation; California local dates replace UTC
  dates for two contemporaneous updates; a technical-approval milestone is not
  pure installer time; direct overlapping evidence is not automatically dropped.
- `reviewed_followup_root002.json` restores Concord's plans and permit clocks,
  and its explicit under-a-month whole-journey statement. The boundary is an
  **uncalibrated top-reading assumption**: the concluding sentence summarizes
  the preceding plans-through-PTO account. Both unreported handoff gaps remain
  latent rather than zero. The earlier scoped fit is retained as a sensitivity,
  not an independent replication or a basis for selecting the nicer result.
- `identity_aliases_root001.json`: exact reviewed pooling changes, hash-bound in
  each compilation receipt. Original source labels remain intact.

The two successor eight-case inputs contain the same people, not 16 cases.
`joint8_compiled001/` has 45 observations and 46 components. The fuller
`joint8_compiled002/` has 48 observations and 50 components. These are components
**across eight case graphs**, not 50 steps in one solar-permitting process, and
not the separate occupancy model's 50-action universe. Mixed residuals are
excluded from timed-action counts. A known installation action can be retained
in the reviewed packet without a separately identified installation duration.

For example, RightWinger's reviewed window is the following sequence. Each box
here is an elapsed cycle, not measured active labor:

```text
permit review 1 → correction → permit review 2
  → [58-day mixed project/preparation gap]
  → inspection 1 (failed) → repair/re-request → inspection 2 (passed)
  → PTO filing → utility review 1 → deficiency response → utility review 2
```

That is ten modeled action occurrences but seven actor/action concepts, plus one
mixed gap. All these counts are fixed by the reviewed narrative. Neither the
three repeats nor the seven concepts are population/count posteriors learned
from an ascertainment model. The same person reports later meter work, outside
this fitted window, so even this detailed record is not an exhaustive project.

## Reproduction and numerical outcomes

Run the compiler with repeated `--declarations` flags for the first three root
packets, the sealed Sol001 packet and exactly one follow-up successor above,
plus `--identity-aliases`. Receipts bind every actual input path/hash and enumerate
all non-likelihood dispositions. Do not include a superseded follow-up alongside
its successor.

Common fit options:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --with-requirements requirements-bayes.txt python3 -m pipeline.procbench.run_visit_hierarchy \
  --data runs/solar_step_model_20260923/joint8_compiled002/data.json \
  --out <new immutable run directory> \
  --observed-channels-only --agency-sd 0 --task-sd 1 --operation-sd 0.25 --source-sd 0 \
  --hierarchy-sampler operation_centered --case-scale-sampler interwoven \
  --case-update-block-size 1 --case-local-updates \
  --population-size 8192 --chains 4 --warmup 1000 --draws 4000 --workers 4 --seed 2026092311
```

| Run | Cases / clocks | Outcome |
| --- | ---: | --- |
| `rightwinger_fit001` | 1 / 11 | Failed: likelihood R-hat 1.041, ESS 155; population-grid sensitivity also failed. Preserved, not promoted. |
| `core2_fit001` | 2 / 13 | MCMC passed; exact observed-case quantities passed. New-population prediction grid failed at 3.23% sensitivity. Generic numerical status remains false. |
| `joint4_fit001` | 4 / 29 | Passed generic MCMC/precision and all 89 actual-case quantity gates. Likelihood R-hat 1.00151, bulk ESS 2,599; population-quantile refinement 1.845%. |
| `joint8_fit001` | 8 / 45 | Passed generic gates and all 149 actual-case quantity checks; likelihood R-hat 1.00368, bulk ESS 1,979; grid refinement 1.330%. Scoped Concord window. |
| `joint8_fit002` | 8 / 48 | Passed generic gates and all 156 actual-case quantity checks; worst generic R-hat 1.00232, minimum bulk ESS 1,077, minimum tail ESS 2,574; grid refinement 1.225%. Fuller Concord window and stated whole-clock assumption. |

Four-case sampling took 314 seconds; report generation added several minutes.
The primary eight-case run took 655.5 seconds sampling and 1,075.4 seconds total,
including prediction summaries and precision checks, on the local machine while
the scoped comparison was also running. Both runs are finished, not background
promises. Their saved draws and manifests are in their respective fit directories.
The CLI's new-population summaries must not be mistaken for the reported
installations' own posterior timelines. Use `summarize_action_journeys` for those:

```text
uv run --with-requirements requirements-bayes.txt python3 -m pipeline.procbench.solar_panel.summarize_action_journeys \
  --run runs/solar_step_model_20260923/joint8_fit002 \
  --out <new case-posterior JSON>
```

It preserves the original generic numerical flag, adds an explicitly scoped
actual-case numerical gate, reports every derived clock on the shared trace,
and leaves full installation counts, population rework incidence, active hours
and intrinsic capability null. The case gate requires posterior convergence,
likelihood precision, and R-hat <= 1.01 / bulk ESS >= 400 / tail ESS >= 200 for
every reported actual-case quantity. Unsupported conditional-route diagnostics
cannot silently pass it. A passing gate certifies neither semantics nor calibration.

The same report also contains `pooled_elapsed_task_type_baselines`: posterior
summaries of `exp(global location + task effect)`, with the operation-specific,
agency and source offsets fixed at zero for that estimand. Each type lists its
distinct cases, materialized occurrences, directly named clock rows and raw
posterior diagnostics. Singleton types are explicitly low-support, and residual
types are not tagged as actor/action cycles. These are conditional task-location
medians, not averages over the applicant population or intrinsic agency speed.
The report returns typed unavailability if a different enabled hierarchy makes
this simple formula inappropriate. The semantic action tag is not an
identification or headline-eligibility gate.

## Actual results and the unresolved statistical issue

The consolidated machine-readable closeout is `result001.json` in the run
directory. The full primary case report is `joint8_case_posterior002.json`;
`joint8_case_posterior001.json` is the scoped comparison. They bind the input,
posterior and draw hashes. The source-bound declarations and all failed pilots
remain available.

In RightWinger's shared timeline, the posterior permit-submission-to-PTO duration
is **93.3 [56.7, 130.4] calendar days**. Within it, the repeated permit-review and
correction sequence is 13.4 [9.4, 20.5] days; the inspection/fix/reinspection
sequence is 12.2 [6.6, 23.1]; and the utility-review/response/review sequence is
13.1 [9.2, 19.9]. These are 90% credible intervals for this reported case's
latent durations under the reporting-error model. They are not independent
phase distributions or held-out predictions. The broad project gap remains in
the timeline, separately from these action sequences.

Across four cases and six review occurrences, the conditional pooled permit-plan
review location is **5.06 [2.61, 9.54] days**. Only two action types have support
from more than one case: this type and permit correction/resubmission (two cases,
5.20 [1.83, 14.04] days). A third shared type is a mixed residual, not an action.
**37 of the 40 task types occur in just one case.** These estimates do not
establish generally good step posteriors, calibrated source trust, or agency
capability. The ordinary identification report is preserved in `posterior.json`:
120 of 195 stored standardized coordinates have less than 25% marginal variance
contraction, including nuisance/prior directions. That diagnostic is not an
information-theoretic identification certificate.

The informative failure is Concord. Its installation-to-PTO posterior changes
from 23.6 [7.5, 110.2] days in the scoped fit to 12.2 [5.7, 40.5] days after
including the earlier stages and the under-a-month statement. The endpoints
match for this comparison; the full modeled windows do not. This is conditional
information propagation, not an independent validation or a pure one-factor
ablation.

But the fuller fit's **whole-journey median is still 37.2 [23.6, 90.5] days**,
despite the admitted under-a-month report. The bound is no longer dropped by the
compiler: the issue is downstream. The existing kernel treats it as a noisy
report, not a hard constraint; priors on the unreported interior gaps matter.
The bounded check in `concord_whole_clock_check001.json` shows 73.3% posterior
mass above the declared 31-day bound, and 27.3% posterior responsibility for the
broad contamination component on this report (versus its 5% prior weight).
The actual-case timeline can converge perfectly while remaining scientifically
unsatisfactory. No prior or error-scale change was chosen after seeing this
result to make it look recovered.

**2026-09-29 correction to that diagnostic, not the fitted posterior:**
`check_concord_whole_clock.py` used Gaussian `ndtr`, whereas the native report
likelihood uses Student-t(4) interval probabilities. The 73.3% latent mass above
31 days and the posterior intervals above are unchanged. Reusing the actual
native kernel gives **18.7%**, not 27.3%, broad-component responsibility for the
whole-clock report, and a 32.5% mean probability of reproducing its upper-bound
report. The original diagnostic is preserved as a superseded calculation.
The native-kernel replacement is
`runs/solar_model_20260929/concord_historical_report_checks001.json`, generated
from unchanged saved draws and bound to their hashes. It checks all six Concord
reports, without new sampling or additional evidence.

That calculation also exposes a stronger local mismatch: the admitted same-day
inspection-to-approval interval is [0,1] day, but its latent posterior median is
**4.21 [0.62,22.22] days**. Only 17.8% of draws are inside the stated bound;
the model assigns 61.5% broad-component responsibility to this report despite
a 5% prior mixture weight. This interval is present in the compiled input; it
was not dropped. These are in-sample model checks, not estimates of whether
the poster was wrong. Root re-read the held post and all 98 comments; the
source and all existing input declarations remain unchanged. The qualifier in
the separate "a little over a week" report is still not modeled beyond its
seven-day lower bound. Do not invent a hard upper bound from that phrase.

This puts **measurement-kernel and gap-prior sensitivity ahead of any accuracy
claim**: distinguish date coarsening, approximate recollection, explicit bounds
and genuinely unreliable reports; compare declared reporting-error assumptions
on frozen cases; and check whether whole-clock constraints are reproduced.
The start-boundary interpretation also remains an explicit assumption. More
sampling will not resolve that modeling question. Broader corpus compilation,
learned structural alternatives and source/agency identification remain open as
listed above; the complete county-by-county goal is not finished.

Focused implementation checks: 73 passed in 4.60 seconds. No corpus-wide
verification was repeated. The source-semantic review was restricted to the
newly compiled journeys, with amendments preserved rather than overwritten.

## Baseline comparisons closed during this work

The earlier frozen comparisons now have all five LLM runs and final scores.
Neither establishes a Bayesian advantage: the administrative score favors the
LLM on average; the small forum score slightly favors Bayes, but both paired
uncertainty intervals include zero. These comparisons concern earlier timing
components, **not this new shared-action fit**. See
[the score tables and qualifications](2026-09-23-solar-existing-baseline-results.md).
