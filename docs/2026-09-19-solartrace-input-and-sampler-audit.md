# SolarTRACE: input semantics and a same-target sampler repair

2026-09-19. This review reads public SolarTRACE source files and the saved real
12- and 60-jurisdiction fits. No benchmark labels are read by its diagnostic
scripts. The author has inherited development-truth audit context; this is not
a fresh blinded extraction or an evaluation of reserved data.

## What the independent replay establishes

`runs/rw_parse_20260919/solartrace_chain_audit_v1.json` records hashes of every
frozen source file, original compiled input, posterior and draws. Replaying
32 states per fit with its own saved implementation gives maximum likelihood
differences of 2.6e-11 and 2.0e-10, respectively. The saved arrays are usable
for diagnosing the saved target, not for treating its estimates as settled.

| Quantity | 12 jurisdictions | 60 jurisdictions |
|---|---:|---:|
| Hierarchy coordinates | 76 | 364 |
| Operation-mean design rank | 48 | 240 |
| Likelihood-null hierarchy directions | 28 | 124 |
| Worst R-hat, null directions | 2.46 | 3.49 |
| Worst R-hat, latent operation log-location sums | 1.95 | 1.74 |
| Worst R-hat, sums including reporting-source offset | 2.33 | 2.08 |
| Existing centered-transition acceptances in 48 probes | 0 | 0 |

These are additional diagnostics, not alternative passing thresholds. In
particular, the claim in the separate burden audit that the per-agency sums
"converge in effect" is not established. Even the sums entering the measurement
model disagree across chains. The reported agency rankings/spreads remain
provisional. This note does not rewrite that independent audit.

The proper Gaussian priors make the hierarchical posterior proper despite the
likelihood's null directions. It does not follow that operation effects must be
removed or equated across agencies for the sampler to work. Pooling identical
steps, learning hierarchy scales, and separating task mix from agency effects
remain substantive modeling decisions, distinct from computational mixing.

## Source errors, independently measured

`runs/rw_parse_20260919/solartrace_source_audit_v1.json` compares every numeric
California timeline cell in the original XLSX against the long CSV. All 59,022
rows match, with zero missing/extra cells. The workbook-to-CSV conversion is not
the fault. There are 837 California AHJ–utility rows.

The workbook's **Information** sheet states that permit/inspection summaries are
calculated for the AHJ and interconnection summaries for the utility, and are
repeated in their joined AHJ–utility rows. The existing importer treats these
repetitions as independent observations:

| Existing fit | Positive timing rows | Distinct owner/year/size/technology/phase cells | Repeated rows |
|---|---:|---:|---:|
| 12 jurisdictions | 1,477 | 793 | 684 |
| 60 jurisdictions | 6,298 | 2,665 | 3,633 |

Across the complete California table, 32,238 numeric timing rows collapse to
9,586 owner-specific timing cells, with **zero conflicting values within those
documented identities**. The full-table grouping retains separate unknown
utilities instead of equating every `NA` actor.

Other confirmed problems in `import_solartrace.py`:

1. **Business days are not declared.** All four published clocks use business
   days. Importing bare numbers into a calendar-day analysis is not a unit
   conversion. A corrected phase-only analysis must label its units; a joint
   calendar-day fit needs an explicit calendar conversion/observation model.
2. **Zeros disappear.** The importer drops `value <= 0`. The source explicitly
   counts same-day permit approval as zero. There are 612 permit-zero *rows*
   in the California join, plus 3,904 pre-install-zero rows, 24 final-IX zeros
   and two inspection zeros. These counts include joined repetitions. Some
   pre-install zeros mean no approval-to-build requirement, so not all zeros
   represent a performed, instantaneous task.
3. **Utility identity is wrong.** The importer assigns one fictitious utility
   per AHJ and combines all named utilities within it. A real utility should
   share an identity across the jurisdictions it serves; unknown utilities must
   not be pooled without evidence.
4. **Denominators do not bind the timing sample.** The installation counts are
   for AHJ–utility combinations, while timing medians are marginal AHJ or
   utility summaries. Automatically using an adjacent installation count as
   the timing cohort's n would be a new error, even after duplicate removal.
   Cross-phase/size/year cohort overlap also needs an explicit contract.
5. **The permit span includes rework.** Its definition runs from first
   submission to final approval, including resubmission. It is not a primitive
   one-visit service duration. A one-operation representation can denote an
   aggregate phase, but cannot silently supply primitive-step/rework evidence.
6. **Listing order is not a process graph.** The importer sets four phases
   serial although the source does not establish that route for every project.
   Independent phase measurements do not justify a total process clock.
7. **`--cohort-phase` was inert.** It was written to the report but did not change
   the returned model input. It now raises an explicit unsupported-option error.

All source definitions and duplicate observation IDs are retained in the audit
receipt. None of the original inputs, fits or source files was overwritten.

## Implemented sampler option: no changed statistical target

V6 now has an opt-in `--hierarchy-sampler operation_centered`; the default remains
`blocked` for historical reproducibility. The hierarchy, priors, coordinates,
case effects, population grid and likelihood are unchanged.

For whitened hierarchy coordinates h, let m = A h be the vector of operation
log-location deviations. Since h has a standard-normal prior, m has covariance
A A'. The new transition samples each program's m block by elliptical slice
sampling from its Gaussian conditional given the other blocks, evaluating the
original program likelihood. A' (A A')^-1 maps the mean change back to h. It then
refreshes the independent standard-normal component in ker(A). This explores
the agency/task/operation decomposition without inventing information about it.

The old centered case-duration move is still used when there are individual
cases. With no individual cases it proposes the entire hierarchy from its prior;
the 48 probes above accepted none. The new mode avoids that ineffective proposal
and retains the existing source/location interweaving move.

Seven new source-free tests cover target/layout equality, conditional Gaussian
algebra, null variance, a known analytic joint posterior, and real case/population
likelihood replay. The full suite passes: **870 tests**, one pre-existing warning
about the generator test returning a value.

`runs/rw_parse_20260919/solartrace12_sampler_probe_original_input/` is a short
four-chain mechanics probe with exactly the old input/grid/prior and the new
transition. Its scope file explicitly disqualifies it as a source-corrected
agency result. Better mixing will not repair the input problems above.

The short probe completed in 161 seconds, with 100 warmup and 300 retained draws
per chain. Its original report has seven flags versus 79 in the archived fit,
but **still fails convergence and numerical usability**. Comparing different
draw budgets is a diagnostic clue, not a matched efficiency claim. Independent
derived diagnostics show worst operation-location R-hat 1.28 and worst
source-adjusted R-hat 1.43, despite worst marginal-coordinate R-hat 1.13. Null
directions now have variances 0.93–1.05 and worst R-hat 1.006. Thus the new move
fixes the decomposition ridge but the short chain has not resolved all measured
directions. Increasing the integration grid changes posterior importance weights
by total variation 0.034, above the 0.025 gate; that failure remains visible.

`solartrace12_sampler_full_original_input/` is the subsequent four-chain,
1,000-warmup/3,000-retained-draw check matching the archived run's draw budget.
It was confirmed running, not restarted. Both runs preserve the old data errors
for a same-target computational comparison; neither is a corrected agency study.

New V6 reports also check operation log-location sums and fully represented
agency inventory means directly, rather than inferring their mixing from
coordinate diagnostics. The already-launched diagnostic uses its frozen earlier
report code; its derived sums will be checked independently on completion.

## Corrected evidence preparation implemented

`import_solartrace --panel-only --definitions <Information.csv>` now produces a
`solartrace-phase-panel/1` table, with all years, sizes, technologies and four
phases retained separately. The generated panel is
`runs/rw_parse_20260919/solartrace_phase_panel_v1/phase_panel.json`:

- 59,022 input rows, including 32,238 timing rows;
- 9,586 unique timing cells, with 22,652 repeated joined rows retained as
  provenance rather than independent observations;
- 585 unique zero cells retained with phase-specific zero semantics;
- 15 unidentified-utility timing cells retained without global unknown pooling;
- source hashes, literal CSV fields/line numbers, actual owner IDs, definitions
  and joined install counts preserved, but no invented sample size or route.

The older graph export now requires `--legacy-unsafe` and labels its report
diagnostic-only. Both modes refuse output-directory overwrites. Six source-free
table-contract tests check ownership, zero/epoch retention, unknown actors,
conflict rejection, CLI scope and the formerly inert cohort option.
After the added table tests and derived-estimand diagnostics, the full suite
passes **876 tests**, with the same pre-existing generator-test warning.

This is a prepared **phase-evidence table**, not a full applicant-process parse
or a fit-ready V6 graph. It does not parse the workbook's other five sheets into
evidence ledgers, solve temporal transport, establish independent finite cohorts,
or resolve every no-required-step zero. Those requirements remain open.

The subsequent `2026-09-19-next-steps-plan.md` should be read with these findings:
existing SolarTRACE inputs cannot support an agency-culture release even after
convergence; a visible n does not automatically bind a timing cohort; and tuning
changes against C29/C44 truth is development/calibration, not held-out validation.
The plan's recovery gates should not substitute for an untouched evaluation split
or independently specified source-semantic decisions. Likewise, a source
describing delayed posting does not establish a quantitative selection function
for every real forum case.

## Longer same-target sampler diagnostic

The four-chain operation-centered run completed with 1,000 warmup and 3,000
retained draws per chain at population size 4,096. Its frozen report passes its
then-implemented chain diagnostics, but **not numerical precision**: importance
ESS fraction 0.98953 (threshold 0.99), total variation 0.03776 (threshold 0.025),
and maximum checked clock change 3.64% (threshold 2%).

Independent replay of its frozen source verifies all 32 checked saved likelihoods
exactly. Worst operation-location R-hat improves to 1.00843 from 1.946 in the
old 12-jurisdiction fit; worst null-direction R-hat improves to 1.00037 from
2.457. The source-adjusted operation location still reaches **1.01246**, above
the 1.01 gate. Therefore the broader independently checked convergence criterion
does not pass, despite the older report's `posterior_converged: true` field.
Nothing about these improved diagnostics repairs the input-semantic defects.

Run: `runs/rw_parse_20260919/solartrace12_sampler_full_original_input/`.
Independent receipt:
`runs/rw_parse_20260919/solartrace_full_sampler_chain_audit_v1.json`.
Original draws, source snapshots and flags are preserved.

## Next work

Keep parsing and synthetic verification moving. Complete the sampler probe and
compare its diagnostics to the same frozen target, then prepare a source-bound
phase panel with unique agency cells, actual actor identities, explicit units,
zero semantics and temporal strata. Do not manufacture process totals or precise
finite-cohort likelihoods from a joined summary table. Only after the repaired
inputs and diagnostics pass should the hierarchical estimates be interpreted.
