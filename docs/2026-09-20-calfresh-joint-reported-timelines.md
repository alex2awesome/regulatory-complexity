# CalFresh: linked timelines in the existing V6 model

Status: grouped likelihood implemented and
[independently reviewed](../runs/three_family_20260920/calfresh_joint_duration_reports_implementation_review_v2/report.md);
233 focused/adjacent tests pass. The initial review found boolean-value and
caller-mutation defects; both were repaired and the failed review preserved.
Both five-case real sensitivity conditions have now completed and passed the
declared numerical gates; see [results and qualifications](2026-09-20-calfresh-joint-timeline-results.md).
The separate saved-state/support review is adopted with its strict-JSON encoding
correction. CalFresh's remaining-use gate stays open; these overlapping cases
do not become new independent evidence.

## Why this changes the model's use of text

One applicant may report an interview date, a pending snapshot and a later
decision. Those constrain one timeline. Multiplying an independent error model
for each sentence, then adding their implied differences, counts the same
information more than once. Conversely, dropping every secondary timing loses
information about where the wait occurred.

The new opt-in `joint_duration_reports` field groups explicit observations in
ordinary V6. It replaces their scalar factors; it never adds a group factor
beside its members. A case still shares its latent process durations and one
path/actor assignment across all reports. The existing single-clock conditional
frame schemas and default targets remain unchanged.

## Exact integration of a declared common reporting error

For latent durations `d[j]` and reported intervals `[l[j], u[j]]`, declare
`reported[j] = d[j] * exp(e)` for one group error `e`. The allowed error interval is

`A = max_j(log(l[j]) - log(d[j]))`,
`B = min_j(log(u[j]) - log(d[j]))`.

One Student-t4 CDF difference integrates `e` over `[A,B]`. The broad reporting
component is also mixed once per group, not once per sentence. An empty
intersection has probability zero even with contamination enabled. A duplicate
constraint does not square the likelihood. The error adds no sampled coordinate.

This is a **strong sensitivity assumption**, not automatically a better or more
conservative error model. Relative timing is exact within the supplied rounded
bounds. A shared error cannot explain independently misremembering one date;
calendar-endpoint rounding and approximate-hour phrases do not inherently share
a multiplicative error. Group membership therefore needs an explicit rationale.
Source-family equality does not certify common authorship, artifact or error.
The model does not learn a correlation, source trust or population selection.

The strict version-1 contract binds the program, declaration and complete member
observations by hash. It requires one case/source-family/ascertainment label,
individual elapsed intervals and single operators, rejects boolean numeric
fields, and freezes the observation view against subsequent caller edits.
Its declaration explicitly says sensitivity-only. Existing actor/path priors
remain outside the entire same-case group likelihood and occur once per case.

## Real-data application, not a new independent sample

Five already-reviewed narratives have both application-to-interview information
and an observed or pending decision endpoint. The proposed application projects
each complete source-event constraint system onto application, interview and
outcome events. Upload, phone-call and observation-snapshot nodes are eliminated
algebraically, not given fictitious process-duration priors. Projection must
preserve the feasible set on the retained events.

The resulting bounds on interview time, outcome time and their difference enter
**one group per case instead of their parent constraints**. This is not adding
derived observations beside the original evidence. It deliberately merges eight
source report-group IDs into five case-common-error groups; that change is a
declared sensitivity, not a claim that the sources establish common error.

The two modeled phases remain mixed/unknown-actor elapsed intervals. They do
not imply two statutory tasks, agency ownership of post-interview delay, or
observed future outcomes for pending cases. Posting/coarsening selection remains
unmodeled. The five histories overlap existing component fits and must not be
counted as five new applicants or their projections as fifteen independent cases.

The [deterministic phase-share findings](2026-09-20-calfresh-current-findings.md#shared-histories-locate-some-waiting-without-identifying-a-department)
already locate substantial post-interview time in three completed narratives.
They are source-coarsening bounds, not posterior intervals or agency effects.
The joint fit is intended to retain that structure while propagating the
declared timing uncertainty; neither numerical convergence nor a source hash
would establish population representativeness or recovery of hidden agency delay.
