# CalFresh reported application-to-observed-decision component

Declared before fitting this component. This is part of the CalFresh-first
closeout, not a new architecture or permission to restart other families.

## Estimand and eligible observations

Elapsed calendar days from a reported CalFresh application/reapplication
submission to the claimant's first observed eligibility approval or denial.
Both outcomes count as observed decisions; approval-only histories must not
stand in for all decisions. The origin is submission, not an assertion that
the application was administratively complete or that no more documents were
needed. A subsequent document request does not silently restart the clock.

No-response statements can support absence of a claimant-observed decision,
but not absence of an internal administrative decision. Distinguish a portal
decision date from when a claimant discovers it. Application-to-interview,
card possession, benefit availability, promised processing deadlines and
recertification are not interchangeable endpoints. An unknown county or
internal department is not an exclusion criterion.

The candidate review combines the215 pending-clock rows with supported parallel
timings from the47 qualitative rows. Every candidate must have a source-bound
use or target-specific disposition, with previous exclusions reconsidered for
their actual reason. A retained different-clock label is not a finished analysis.
Use one representative observation per reconciled case for this component.
An observed completion supersedes that case's earlier pending snapshot; keep
both source records in provenance, not two independent likelihood factors.
Case overlap with other components remains explicit. Do not add component
medians or sample sizes to obtain whole-process burden or independent people.

## Coarsening and semantic uncertainty

Freeze source interpretations and each interval before sampling. Source review
must bind native metadata for relative dates. For two date-only events separated
by D calendar dates, continuous elapsed time lies within D−1 to D+1 days,
intersected with nonnegative time. Pending date-only bounds use the conservative
lower edge, not the integer date difference. A later comment's posting date
does not automatically become an event date.

Reported approximate day/week durations need an explicit rounding rule. Seven
days per week is a unit identity; a phrase such as "a few weeks" is a semantic
interpretation, not an exact2–4-week source interval. Months are not invariably
30days. Any month/lexical conversion must disclose its envelope and uncertainty;
never turn "over a month" into an upper bound of one month. Broad supported
intervals are acceptable; exact dates are not required. Genuinely unsupported
boundaries remain descriptive or enter an explicitly declared interpretation
sensitivity, not a guessed precise base observation.

Before admission, check lifecycle, author/case aliases, prospective versus
observed events and whether the claimed endpoint actually occurred. If status
is unknown, retain it as unknown rather than relabeling it pending or complete
to satisfy the current compiler. Such records remain implementation work where
they contain a usable bound. Missing named departments never justify a hold.

## Fixed inference conditions

Use the existing guarded V6 elapsed-only conditional-case likelihood and its
same-target independent-case marginalization. This component has location and
spread coordinates; it does not yet identify agency, task, source-bias,
selection or organizational assignment effects. Zero source offset defines
the selected-report scale, not source accuracy or representativeness.

Use the same reference configuration as the other calendar-day components:
location-prior median30days and log-SD2; case-spread prior median0.6 and log-SD0.4;
Student-t4 report scale0.25 and contamination0.05. Four fixed conditions:

1. Completed observed decisions only, with the reference configuration.
2. All admitted completed and historically pending decisions, same configuration.
3. The same mixed cases with report scale0.5.
4. The same mixed cases with location-prior median7days.

Seeds2026092331–2026092334 respectively; four chains,1000 warmup,2000 retained
draws per chain, two local workers and128 case-quadrature nodes, refined to256
for the existing numerical check. Freeze all memberships and configs in one
compiled packet, then run once. No automatic extension, best-condition selection
or gate override. Source corrections discovered before sampling are itemized;
do not secretly narrow the candidate universe to obtain easier fits.

## Interpretation and required outputs

This is a conditional distribution of selected captured reports. Ignorable
coarsening and the report distribution are assumptions; informative posting and
observation times can violate them. A proper finite-duration distribution also
assumes eventual observation of a decision. The captured pending reports do not
establish that eventual outcome. State these limits next to numerical results.

Report all conditions, exact source-to-factor consumption, completed/pending
counts, native source coverage, finite-record median bounds, posterior intervals,
numerical diagnostics, and prior/report-scale sensitivity. If the direct median
has no finite upper bound, say so; do not present a finite model interval as a
data-only bound. Numerical success does not establish model adequacy, selection
calibration, population burden, agency performance or superiority to an LLM.

This component does not finish CalFresh by itself. Shared-event dependence,
remaining supported clocks, heterogeneous-source inference, actor uncertainty,
adequacy/comparisons and the consolidated structural analysis remain part of
the broader closeout wherever not already supported by completed evidence.
