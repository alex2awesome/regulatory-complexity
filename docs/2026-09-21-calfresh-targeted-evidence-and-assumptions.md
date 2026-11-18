# CalFresh: targeted evidence first, explicit assumptions second

21 September 2026. Working record opened 16:40 UTC.

## Authorization and scope

Alex approved seeking targeted evidence for participation, individual-step
timings, and agency capability. His follow-up: first collect evidence; if it
cannot be found, (1) state the kind of evidence needed and (2) make assumptions
and be clear about them. This supersedes the earlier no-new-retrieval work
order for these CalFresh gaps only. No agency outreach, records requests,
broad forum queue, synthetic work, Solar work, or Joint47 retry is included.

The [supported result](2026-09-21-calfresh-process-results-and-next-decision.md)
remains frozen and partial. Unknown quantities there remain unknown. Any
assumption-conditional extension must be separately labeled, preserve the
original population and clock boundaries, and retain all declared sensitivity
conditions rather than selecting the most attractive result.

## Evidence sought

| Missing link | Useful observation | What does not suffice |
|---|---|---|
| Participation versus narration | Case-linked action occurrence/nonoccurrence with an observation window and denominator | More unstructured mentions without a sampling frame |
| Rework | Completed rounds including zero-round cases, same action and lifecycle | Counts of quotes, contacts, or selected complaints alone |
| Time allocation | Matched action start/end or phase boundary timestamps, including pending cases | Dividing a total evenly or calling application-to-interview the interview duration |
| Agency contribution | Repeated compatible clocks, case mix, active staffing/workload and common-period overlap | Treating a county residual or action-availability effect as intrinsic capability |
| Effort/cost | Direct active-time and payment/payee observations in the same case frame | Calendar waiting as labor, absent fee evidence as zero fees |

## Bounded discovery and admission

Root investigates primary CalFresh administrative-record experiments and
replication materials. Luna reviews actual action/event administrative measures;
a second Luna reviews county workload and service operations; Sol checks
already-retrieved sources and candidate assumption families. Shared candidate
records live under
`runs/process_structure_20260921/calfresh_targeted_evidence_20260921/`.

For each candidate record: original URL and captured source/hash where
available; jurisdiction; period; lifecycle; counting unit; sample frame;
numerator/denominator; event boundaries; publication versus observation date;
overlap with existing data; accessible aggregates versus restricted microdata;
and exactly which latent quantity the evidence can inform. Discovery is not
automatic model admission. Repeated publications of one study count as one
evidence family. Historical experiments cannot silently calibrate all current
counties, and aggregate means cannot be converted to invented case records.

## Fallback rule

After the targeted pass, enumerate remaining gaps and the collection design
that would close each. Specify any transport, route, detection, timing-allocation
or capability assumptions before fitting. Show which outputs are sensitive to
them and which are actually updated by compatible evidence. Prefer partial
identification or explicit unknowns where a numerical posterior would hide the
absence of support. User authorization permits assumptions; it does not turn
them into observations.

## Findings and next action

### Useful evidence found

The first pass found useful **historical behavior**, not a complete contemporary
case panel. No new source has entered the existing county availability/V6 fits.

| Evidence | What it adds | Boundary retained |
|---|---|---|
| LA flexible-interview experiment, 2020–21 | Actual optional-line use including noncallers; call-count/time summaries | GetCalFresh/contactable sample, not every applicant; long calls are not observed completed interviews |
| SF recertification study, 2014–16 | First/any interview completion and scheduled/rescheduled events | Recertification, not initial application; repeated events within households; working-paper version captured |
| LA pre-experiment denial categories, 2018–19 | Conditional bounds on interview completion under explicit coding assumptions | Different cohort from experiment; no borrowed sample size |
| Existing CDSS CF18 parse | Approval-cohort timing means and complete bin counts | Approved initial applications, not all decisions or individual steps |
| County workload, staffing, and budget reports | Staffing-pressure context and a route to activity-specific cost assumptions | Budgeted FTE is not active CalFresh staff; workload changes can coincide with interview waivers |

The published LA paper and appendix were downloaded from the author's linked
copy and the publisher. Earlier versions and the already-local Code for America
implementation story are one source family, not independent replications.
The final paper's Table 3 has 48,557 treatment applications and 16,241 controls.
Its main outcome regressions use a different denominator. The determination-time
analysis treats cases pending at the deadline as determined on day 30, so that
mean is not an uncensored decision clock. The original microdata were not
obtained. [Published study](https://www.aeaweb.org/articles?id=10.1257/pol.20220701),
[appendix](https://www.aeaweb.org/content/file?id=21668),
[replication catalogue](https://www.openicpsr.org/openicpsr/project/194727/version/V1/view).

For SF, the captured 2020 working paper reports 67.8% first-attempt and 76.3%
any-interview completion among 39,702 recertification events for 30,420 cases.
The difference is about 8.5 percentage points completing after a failed first
attempt, not the number of all rescheduling attempts. The authors had scheduled
and completed-interview records, but not verification/form submission records.
The published 2021 PDF fetch failed; the public replication folder lists a
national QC comparison dataset, not the event panel. Downloading its README
redirected to login, so its access conditions remain unverified—not presumed
public or impossible to obtain. [Working paper](https://www.nber.org/system/files/working_papers/w27311/w27311.pdf),
[replication listing](https://www.openicpsr.org/openicpsr/project/124381/version/V1/view).

### Small reference calculation completed

The [predeclared calculation](../runs/process_structure_20260921/calfresh_targeted_evidence_20260921/NATIVE_CALIBRATION_PLAN.md)
and [result](../runs/process_structure_20260921/calfresh_targeted_evidence_20260921/native_reference_result_v1.json)
use the LA call rates in their **native historical frame**. An exact mixture
over all integer counts compatible with the published rounding preserves
the nesting of any call and a call longer than five minutes. No MCMC is needed.

Under the declared iid application model and Dirichlet(1,1,1) prior, optional
line-use probability in the offered-line arm is 53.00%, with a conditional
90% interval of 52.63–53.37%. This describes a generating probability for that
frame, not uncertainty about its already-observed finite cohort. Phone linkage,
independence and reporting accuracy are assumptions. It is **not** a posterior
for current CalFresh interview completion or agency capability.

An illustrative change in participation odds by factors 0.5, 1 and 2 moves the
median to 36.05%, 53.00% and 69.28%, respectively. Those are fixed, hypothetical
changed-regime scenarios, not estimated transport effects or county results.
They show how population/era assumptions can dominate the narrow native
sampling interval. No transfer into the current model is enabled by default.
The Dirichlet prior implies a Beta(2,1) marginal on any-call, not a uniform
participation prior. The iid intervals omit office/time/household clustering.
Control-arm shifts, retained in the machine-readable result, concern crossover
to the line without the offer message, not take-up among offered applicants;
they are not a transport headline. None of these conditional intervals includes
uncertainty about whether a proposed odds shift is correct.

### Missing evidence and fallback assumptions

This is a bounded feasibility pass, not proof that no other public evidence
exists. The following are the explicit assumptions for the next integrated
specification, not claims that the current fits already implement them:

| Quantity still missing | Evidence that would resolve it | Assumption route if unavailable |
|---|---|---|
| Current initial-case participation | Linked application IDs with actual action occurrences and explicit observed nonoccurrences, opportunity windows, pending status, county and policy era | Separate participation from narration. Use weak priors for unanchored actions; historical anchors require distinct era/lifecycle/channel shifts. Compare no borrowing with declared borrowing sensitivities. |
| Full sequence and repeat hurdles | All cases including zero-rework cases; request/receipt/resubmission and appointment attempts, not just success histories | Enumerate feasible branch/order alternatives; do not let missing edges silently imply parallelism. Unobserved branch weights and repeat hurdles remain assumption-driven. |
| Individual step elapsed time | Matched start/end timestamps inside the same cases, with censoring and active-service versus queue boundaries | First preserve measured phase totals; allocate within a phase only under explicit simplex-weight priors. Vary concentration and plausible agency/applicant waiting allocations; call such shares prior-determined. |
| Agency capability | Compatible clocks across agencies and periods, actual productive staffing, inflow/backlog, case mix and cross-source overlap | Model an agency-associated residual conditional on measured covariates. Calling it intrinsic capability additionally assumes away unmeasured confounding and needs a separate sensitivity; no causal ranking from an unadjusted county effect. |
| Active applicant/agency effort and cost | Time-and-motion or diary observations, sampled payments/payees and observed zeros | Keep elapsed waiting distinct from labor. Budget cost factors may anchor an explicit cost scenario, not observed hours. Unmeasured channels stay outside evidence-backed headline totals. |
| Source bias and detection | Same event boundaries and population recorded by multiple source types, including a probability-sampled applicant frame | Use source-type bias/selection sensitivities; do not infer reliability rankings from incomparable agency and forum clocks. |

The integration must retain dependence: availability is not participation;
nested events are not independent rows; a phase and its component durations
cannot be counted twice; and the CF296 cells already used for availability
cannot become independent new evidence again without an explicit joint
observation model. A post-hoc table of unrelated marginal fits does not meet
the full-model goal.

A concrete regime warning emerged in root review: the SF December 2022 minutes
discuss interview/signature waivers immediately before reporting processing
timeliness and workload. Faster processing in such a period need not mean more
capable staff. A waived requirement also does not prove an interview action is
unavailable. Record requirement status and participation by policy era instead
of turning a waiver into a county-wide absence label.
[SF commission minutes, PDF page 5](https://www.sfhsa.org/sites/default/files/media/document/2023-01/iii._12.15.22_hsc_meeting_minutes.pdf).

The source audit also caught a legacy extraction problem: `calfresh_018` in
`pipeline/priors/observations/calfresh.json` invents a 12-day duration by
subtracting an approximately seven-day treatment/complier effect from a
19-day comparison and calling the latter a median. This is not an observed
case duration. Root confirmed that older prior-building scripts consume that
field; it must not be reused as a valid timing anchor. The current reviewed
decision-clock manifests have an empty task-prior map, and the new reference
calculation does not consume this file. The legacy row was not silently
rewritten and no claim is made here to have re-audited every historical fit.

For the next implementation, the bounded assumption families are:

1. **Historical participation borrowing:** the no-borrowing model is retained.
   Only genuinely corresponding actions can share information. A historical
   rate may center a target prior with total effective concentration 10, 50,
   or 200, separately, rather than bringing tens of thousands of historical
   cases into the current likelihood. Those concentrations are modeling
   choices, not estimated sample sizes. Compare target participation odds at
   0.5, 1 and 2 times the historical center; no preferred scenario or averaging
   without an independently specified transport model. The optional E2E call
   rate cannot stand in for all interview attendance.
2. **Unanchored participation:** use explicit weak Beta(1,1) and boundary-heavy
   Beta(0.5,0.5) sensitivities conditional on availability and feasible case
   path. They are prior-determined unless a compatible event observation
   updates them. Conditional action choices need not be independent.
3. **Unobserved allocation within a measured phase:** if a declared serial
   partition has K nonoverlapping elapsed components, compare symmetric
   Dirichlet concentration totals 1, K and 10K. Each allocation sums to the
   *same* measured phase total. This is an exchangeability assumption, not
   learned equality of steps. Do not apply this construction to overlapping
   activities, parallel clocks, or to labor hours. Where the partition itself
   is uncertain, retain separate structural hypotheses.
4. **Agency residual:** a zero-centered log-time effect with prior standard
   deviation 0.25, 0.5 or 1 is a sensitivity family, not a calibrated capability
   scale. Before any such fit, require compatible repeated clocks, an explicit
   source reference and case-mix/workload covariates, and report residual
   confounding. If the hierarchy cannot be identified, retain its prior
   unchanged and exclude agency rankings. This is not authorization to
   silently revive the superseded county-timing comparison.

These declarations identify the numerical choices before their eventual use.
They are not a Cartesian grid of expensive fits: prior-only allocation and
transport blocks should use direct propagation, with their unchanged priors
reported, not repeated sampling runs advertised as learning.
Only the much narrower native LA reference calculation above has run in this
pass. They are not yet an integrated fit or a claim that every combination is
scientifically admissible. Admission still depends on a feasible event graph,
compatible population and observations, and avoiding duplicate factors.

### Artifact map

The smallest useful additional extract would have anonymized case ID, county
or a county candidate set, policy period, initial/reapplication/recertification
indicator, observed-from/observed-through dates, and event records for filing,
interview scheduling/attempt/completion, verification request/receipt/rework,
decision, withdrawal and notice. For each event, distinguish an observed zero
from not recorded, not yet observable, and not applicable. Include case outcome
and pending cases; record selection/sampling and coarse relevant case-mix
fields. Active service duration needs a separate start/end or time-use field;
an event's calendar timestamp does not supply it. Agency workload requires a
county/office-period table with productive staff hours, inflow and backlog,
not total departmental authorized FTE. No personal names or contact details
are needed. Applicants need not know a named department: unresolved identity
can remain categorical rather than becoming an exclusion rule.

- New primary studies, source hashes and admission decisions:
  `runs/process_structure_20260921/calfresh_targeted_evidence_20260921/root_study_evidence.json`.
- Reproducible native calculation: `calibrate_native_events.py` in that directory.
- Luna action/event discovery: `action_events_luna.json` and `.md`.
- Luna workload discovery: `workload_luna.json` and `.md`.
- Sol existing-source audit: `local_evidence_sol.json` and `.md`.
- Captured primary-study bytes:
  `corpus/counties/raw/calfresh_targeted_evidence_20260921/`.

### Review completed

Luna independently regenerated the native result byte-for-byte; Sol returned
a qualified scientific PASS with the prior, clustering and transport caveats
above. Root visually checked both main study tables, independently checked
the exact-count special case against beta quantiles, and replayed 28 source
bindings across the four candidate records, plus the native result's six
input bindings. These are bounded checks of the new evidence/calculation,
not a rerun of the full repository suite or validation of a full process model.

The substantive review repairs were: CF18's initial-only timing scope;
duplicate/version-specific LA evidence; the SF minutes' PDF page and waiver
regime; the QC scorecard's October–December 2018 period and linked row ID;
and unsupported claims that unlocated data were definitely restricted.
Original candidate versions remain archived. The legacy 12-day observation
was flagged, not changed. No existing fitted input or posterior was rewritten.

Next: pin the integration population and observation model using these anchors
and the stated assumptions. No additional broad
parsing queue, new county timing hierarchy, or retry of the failed joint fit
is implied by this evidence pass. The full process/capability goal remains
unfinished.
