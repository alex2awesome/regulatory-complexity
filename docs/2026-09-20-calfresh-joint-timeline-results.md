# CalFresh: linked applicant timelines now fit in V6

Both predeclared five-case conditions finished and passed the numerical gates.
This is a working joint-timeline implementation on real reports, not a finished
population burden model. It uses three histories with observed approval/denial
endpoints and two histories still pending at their source snapshots. No named
internal department is required.

The [run packet](../runs/three_family_20260920/calfresh_joint_timing5_sensitivity_v1/README.md)
contains the frozen plan, authorization, source snapshots, draws, and both
posterior reports. Inputs are the
[corrected five-case successor](../runs/three_family_20260920/calfresh_initial_application_joint_timing_input_v1_erratum_v1/root_adoption.md).
The [method note](2026-09-20-calfresh-joint-reported-timelines.md) defines the
shared-report-error assumption and its limitations. The
[independent saved-state/support review](../runs/three_family_20260920/calfresh_joint_timing5_analysis_v1/root_adoption.md)
is now adopted: 32 saved likelihood states replay exactly, and an independent
Student-t calculation agrees within 1.78e-14. Root also checked all 160 replayed
operator triples satisfy total = interview + post-interview duration. Use that
packet's `strict_results.json`; its original auxiliary infinity serialization
was corrected without changing any fitted result. Numerical convergence and
these checks are not semantic or statistical calibration.

## What changed from separate clock fits

Each case has two serial elapsed phases: application to interview, and interview
to the first claimant-observed eligibility outcome. Its interview, total, and
post-interview constraints enter one grouped likelihood. Fifteen projected
intervals therefore form five case factors, not fifteen independent reports.
The projection replaces its parent constraints jointly. Previously fitted
single-clock components remain separate comparisons; they are not multiplied
into this likelihood again.

The source intervals retain uncertain dates, approximate durations and pending
lower bounds. All actor assignments remain unknown/mixed. This does not equate
the two aggregate phases with two statutory tasks or agency-only work.

## Numerical result

Each condition used four chains, 1,000 warmup iterations and 2,000 retained draws
per chain, with two worker processes. No continuation, gate relaxation or
post-result prior change occurred. All 56 reported diagnostics, including 20
case-specific duration/share diagnostics, were checked.

| Shared log-report-error scale | Runtime | Maximum R-hat | Minimum bulk / tail ESS | Maximum predictive-grid change |
|---|---:|---:|---:|---:|
| 0.25 | 93.8 seconds | 1.00903 | 969 / 1,386 | 0.294% |
| 0.50 | 86.2 seconds | 1.00315 | 1,167 / 1,560 | 0.537% |

The frozen gates were R-hat at most 1.01, bulk ESS at least 400, tail ESS at
least 200, and predictive-grid changes below 2%. Likelihood values did not change
when the population integration grid increased from 4,096 to 16,384 points, as
expected for these individual-case factors with selection adjustment disabled.

## What the completed narratives support

These are posterior medians and 90% intervals for the three supplied cases,
not population medians. Reported times are allowed multiplicative error, so
latent-duration intervals can extend beyond the literal date/coarsening bounds.

| Case / observed outcome | Post-interview days, scale 0.25 | Post-interview share, scale 0.25 | Share, scale 0.50 |
|---|---:|---:|---:|
| 1tc7tz1 / approval | 23.9 (15.7–35.9) | 79.7% (69.7–84.9%) | 79.5% (69.2–84.8%) |
| 1u6vw37 / denial letter observed | 27.8 (18.9–42.5) | 87.2% (84.2–90.0%) | 87.3% (84.2–90.0%) |
| 1w6b46j / denial observed | 22.8 (15.5–35.1) | 84.3% (80.4–87.7%) | 84.5% (80.5–87.7%) |

Wider report error produces wider absolute-duration intervals. For example,
1u6's post-interview interval becomes 15.7–53.6 days at scale 0.50.

The stable shares are **not an independent calibration success**. A common
multiplicative reporting error cancels in the ratio of post-interview to total
time. The likelihood therefore enforces the source-derived relative-timing
support by construction. The underlying deterministic bounds already establish
a post-interview majority in these three narratives. This fit demonstrates that
the implementation retains their linked structure and propagates its declared
absolute-time uncertainty; it does not independently validate that error model.

For 1n004ul and 1ow8vx3, no eventual outcome was observed. Their saved posterior
endpoint functions are extrapolations conditional on the model and right
censoring, not newly discovered completion dates. In particular, the source
constraints alone do not force a post-interview majority for 1n004ul, even though
the model favors one. That extra inference depends on pooling and priors.

## What has not been learned

Marginal prior-variance contraction is about 76–77% for the shared location,
59% for the aggregate-phase task block and 40–47% for the case-spread coordinate.
This is parameterization-dependent contraction, not a percentage of truth
recovered or a general identifiability certificate. Eleven of 24 coordinates
have less than 25% contraction in the scale-0.25 condition.

Agency, operation, source-offset and common-case scales were fixed to zero in
this declared experiment. Their unused coordinates remaining near their priors
does not show that real agency differences or source bias are absent. Aggregate
phase effects are explicitly excluded from intrinsic-agency/primitive-task
headlines. Posting selection, source reliability and actor assignment were not
estimated.

## Coverage and next integration

These five cases overlap the 115 records in the existing single-clock
components. They add two executed joint sensitivity conditions, not five new
applicants. The [per-use mapping](../runs/three_family_20260920/calfresh_joint_timing5_source_use_mapping_v1/README.md)
finds zero additional closures in the remaining-use queue: q186 was already
consumed by the 26-case decision fit. Joint reporting is a new supported use of
existing evidence, not a reduction in that queue by relabeling old cases.

Separately, [eight phone elapsed-burden reports](../runs/three_family_20260920/calfresh_phone_elapsed_burden_descriptive_v1/root_adoption.md)
now have adopted descriptive use. Six named descriptive queue uses close; two
shared-event timing uses remain open. The remaining queue is 174 recorded rows.
The next model expansion evaluates compatible partial and pending timelines
within this same two-phase model, rather than assuming every case must report
both phases. CalFresh remains open, and other statutes/synthetics stay deferred.
