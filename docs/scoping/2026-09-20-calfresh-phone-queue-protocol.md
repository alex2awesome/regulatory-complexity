# CalFresh reported phone-queue burden: bounded analysis protocol

Fixed before any phone-queue posterior is fitted. CalFresh remains first; no
Solar, CCW, synthetic production, or new retrieval is required for this analysis.

## Target and source boundary

The primary target is elapsed time in one reported continuous outbound phone
queue spell until its first exit: a live representative answers, the claimant
abandons the queue, or the line disconnects. A post made while that same spell
is ongoing supplies a pending lower bound. A failed terminal attempt is a
completed queue-duration observation, **not** an uninformatively censored
time-to-success observation. The model does not estimate the success rate.

This measures reported elapsed access burden, not active applicant labor, staff
work, approval time, whole-process burden, or all applicants' average wait.
Keep terminal outcome labels in the source-to-input lineage. One observation
per reconciled case in this first component; do not multiply a per-attempt
duration by a call count or add distinct waits without source support.

Candidate universe: the phone-elapsed inventory from sealed fullread001–011.
The initial65-label compilation proposal is preserved at
`runs/three_family_20260920/calfresh_phone_contact_compiler_v1/`.
An additive queue-exit successor supplies proposed mappings, including failed
terminal attempts. Root inspects the consequential splits and consumes a frozen
reviewed-input specification before sampling. Every candidate receives a use or
specific disposition for this clock; other supported uses remain in scope.

Unknown internal department or county is allowed. Shared-event clusters, such
as several commenters on one mass-letter incident, are retained separately when
their dependence is not represented; do not pick the shortest/longest or call
all commenters independent. This limited first input is not the final source
coverage boundary and does not supersede the945-thread completion requirement.

## Observation and inference assumptions

Use the existing V6 conditional-case-frame/2 contract and existing Student-t(4)
log-report interval/survival likelihood. No new model or outcome-hazard kernel.
Pending reports require the explicit assumed-ignorable-coarsening declaration;
frustration posting and observation times may violate it. Include failed exits
to avoid conditioning the primary completed set on eventual successful contact.

Source minutes convert to calendar days by minutes/1440 exactly, with the prior
converted too. This is a unit identity, not calendar/business conversion or an
inference about active work. Explicit minute reports use stated minute precision;
coarse hours receive conservative declared rounding intervals, not spurious
minute precision. Ongoing rounded statements use the lower rounding edge.
Any genuinely ambiguous or cumulative interval stays distinct from a single
queue spell.

Only elapsed is modeled. Agency, task, operation, common-case, source-offset and
selection-effect scales remain zero for this selected-report component. A zero
source offset defines the report-frame scale; it does not assert truthful,
unbiased or representative reporting. Case spread is learned under the existing
prior. Location prior median is60minutes; location log-SD is2.0. These are declared
analysis assumptions, not empirical source calibration. No unknown actor is
converted into a measured agency effect.

## Fixed comparison conditions

All source-admissible cases and conditions are frozen before fitting:

1. `completed_only`: all completed queue exits, any terminal outcome;
   prior median60minutes, report log-scale0.25.
2. `mixed`: the completed set plus historical ongoing queue spells;
   same priors/report scale.
3. `mixed_report_noise_05`: the same mixed cases, report log-scale0.5.
4. `mixed_prior_15min`: the same mixed cases and base report scale, but location
   prior median15minutes; tests a fourfold prior-location change.

Use four independent chains,1,000 warmup and2,000 retained draws per chain,
256 population nodes, two local workers. Seeds2026092301–2026092304 in the order
above. Record exact defaults and all configurations in the prepared plan.
No automatic continuation, tuning to a result, or best-condition selection.

## Checks and outputs

One source-meaning pass plus literal quote/hash/schema replay; corrected mappings
are additive to sealed originals. The shared compiler checks the complete
candidate registry and ensures every admitted claim enters at least one condition.
It does not certify meaning, independence or representativeness.

Use the existing numerical gates and replay saved likelihoods. Failed conditions
remain reported; do not headline their estimates or silently extend them.
Numerical success is not model adequacy. Report posterior median/interval in
minutes, completed/pending counts, terminal-outcome composition, source/era scope,
and sensitivity to pending inclusion, report noise and prior location. Do not
claim a population burden estimate, empirical bias correction, causal county
ranking, or Bayesian superiority. Adequacy and any predictive comparison require
their own evidence, not a numerical PASS label.
