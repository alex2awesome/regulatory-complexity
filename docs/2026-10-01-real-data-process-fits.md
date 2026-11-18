# First real-data fits of the process engine: ADU permits, solar permits, solar interconnection (2026-10-01)

Alex (overnight): "get everything to the stage where the bayesian model can run, then audit what
codex has done, and run the fast sped-up version". This is the task's one results document.
Inputs, mapping and assumptions: `runs/real_process_20261001/README.md`. Audit:
`docs/2026-10-01-audit-of-codex-speedups.md`. Codex handoff:
`docs/2026-10-01-handoff-for-codex-real-data-model.md`.

> **Status after Codex's audit (2026-10-01, `docs/2026-10-01-real-data-model-and-inference-audit.md`):
> no fit below is a validated posterior. Quarantine the headlines.** Claude reproduced its two decisive
> findings from the saved particles (`/dfs/scratch0/alexspan/real_process_20261001/runs/claude_verify_codex_audit.json`):
> (1) ADU: the correction-step PMF has total mass exactly 0 in every checked particle (the discretizer
> returns all zeros when every CDF underflows; it does not renormalize), so all correction paths carry
> zero mass and the pending-survival term reads the missing mass as permanent survival -- the ADU run is
> numerically invalid, and the "grid cap / renormalization" explanation given below is wrong;
> (2) parameters with no observations (hour terms) must keep their exact priors but moved up to 11.9 prior
> SDs in ADU (also distorted in the Solar CPU and interconnection runs; fine in Solar HMC) -- a sampling
> failure at these budgets. Corrections to this document: `pinc` is a geometric tilt on the number of
> correction rounds (conditioned on at most 5), not a per-review correction probability (as pinc -> 1 the
> count is uniform on 0-5); interconnection's I2 choice is a decomposition of the complete -> PTO
> duration under an authored menu, not evidence that PG&E/SCE perform an extra task; a mean log-likelihood
> gap does not measure posterior mode mass; reported step "medians" are exp(mu), not medians of the
> truncated daily PMFs; forum intervals were recoded to midpoints (narrowing them); and only three
> runnable subsets are model-ready, not "everything". The forum-vs-admin offsets and descriptive
> administrative summaries stand with their stated limits.

## Summary (morning of 2026-10-01, superseded in part by the status note above)
- **Everything is model-ready** for the process engine: three real packages (ADU permits, solar
  permits, solar interconnection) with every input record ledgered. Extraction finished (SolarAPP+,
  Terner incl. the 2021 survey, CPUC Rule 21 counts, permit linkage, Houzz triage).
- **The engine needed five fixes to run on real records** (audit); defaults unchanged, 123 tests.
- **Interconnection (1.3M applications): the clearest result.** Two independent runs agree on structure (strict gate still fails mildly, R-hat 1.36): PG&E and
  SCE add a review step after "application complete" that SDG&E does not; the chance a review
  returns the application for correction was steady through 2022 and jumped in 2023 (NEM-3.0 rush).
- **Solar permits: totals fit, structure not identified.** Independent runs (CPU and GPU) fit each
  city's durations but land in different local modes ~1,000 log-likelihood units apart; no
  step-level claims. Of six runs, the best-likelihood configuration appeared once; three GPU HMC
  runs agreed exactly with each other on a worse one.
- **ADU permits (467 jurisdictions): misspecified.** One run finished: totals partly fit, but steps
  hit the 512-day grid cap and the design posterior is an artifact (A2 almost everywhere); the
  held-out Ministerial/Discretionary check is weak (rho 0.12). Second run stopped pending respecification.
- **Forum vs records:** forum permit timelines match the same city-year's records; interconnection
  reports run ~23% shorter than their utility-year (partly definitional).

## What was run
Engine: `pipeline/procbench/toy_statute/` (`model.py` likelihood, `smc.py` adaptive tempered SMC,
`blocked.py` exact town-local blocked moves -- Codex's CPU speedup). Two independent runs per
package (seeds 20261001, 20262001) on sk3 CPUs, so between-run agreement can be checked with the
engine's own gate (`smc.compare_runs`, `smc.gate_v2`). Runs were stopped after sampling; the
driver's serial 1,000-draw answer step was replaced by `runs/real_process_20261001/combine_runs.py`
with fewer answer draws (declared below).

| package | towns | parameters | particles x moves per run | workers per run |
|---|---:|---:|---|---:|
| ADU application -> permit (`adu_fit003`) | 467 | 1,423 | 256 x 3 | 96 |
| Solar application -> permit (`solar_fit002`, runs 0-3) | 19 | 79 | 1,024 x 6 | 24-40 |
| Solar application -> permit, GPU HMC (`solar_jaxhmc002-004`) | 19 | 79 | 1,024 x 6 HMC trajectories | 1 GPU |
| Solar interconnection -> PTO (`ix_fit001`) | 27 (utility x year) | 98 | 512 x 4 | 28 |

The GPU path (`jax_backend.py`, HMC kernel) ran the 19-town Solar permit package after two fixes
(open-case contamination; `JaxPool.map` operation matching): 35 stages in ~2 h on one GPU, the same
wall time as 24 CPU workers. It could not build the 467-town ADU model (compile unfinished after
43.5 minutes; towns with differently shaped evidence compile separately; see the audit). Earlier
attempts kept for the record: `adu_fit001`/`solar_fit001` (stopped: open cases uncontaminated),
`adu_fit002` (stopped after 2-3 stages to restart with more workers).

## Forum vs administrative reporting offsets (separate exact-grid fit)
`runs/forum_admin_calibration_20261001/` -- each forum report compared with its OWN admin cell
(utility x year, or city x year) using the Gemma cell keys:

| clock | reports | reporting ratio forum/admin, median [90%] | report noise sigma |
|---|---:|---|---|
| interconnection -> PTO | 68 | 0.77 [0.54, 1.00] | 0.27 [0.09, 0.69] |
| solar permit submission -> issued | 15 | 0.74 [0.33, 1.62] | 0.89 [0.19, 1.76] |
| ADU first submission -> issued | 19 | 0.98 [0.57, 1.58] | 0.61 [0.25, 1.31] |
| permit clocks pooled | 34 | 0.89 [0.56, 1.35] | 0.67 [0.31, 1.29] |

Forum permit timelines match the records of the same city and year (intervals include 1).
Interconnection reports run ~23% shorter than their utility-year records; the forum screen keeps
clocks that start after installation while DG Stats "received" can precede installation, so this
is at least partly a definitional difference.

## Results
### Solar permits (application -> permit issued): fit002, 2 runs x 1,024 particles x 6 moves
Both runs reached the posterior (beta = 1) in 39 and 38 tempering stages (~2 h each on 24 CPU
workers); log evidence -447,260 and -446,226.

**Totals are reproduced** (posterior predictive vs each town's completed records; `ppc_check.json`):

| town | completed | open | observed median days | predicted median days | share of records inside predictive 5-95% |
|---|---:|---:|---:|---:|---:|
| SAN DIEGO | 55,981 | 858 | 12 | 11 | 0.93 |
| LOS ANGELES COUNTY | 30,160 | 4,207 | 7 | 6 | 0.95 |
| SACRAMENTO | 13,088 | 841 | 6 | 7 | 0.96 |
| LOS ANGELES | 1,062 | 0 | 117 | 103 | 0.82 |
| SAN FRANCISCO | 398 | 97 | 72 | 101 | 0.92 |

**The split of time among steps is NOT converged.** The engine's between-run gate fails
(`comparison.json`): between-run R-hat up to 1.96 on the
step-duration parameters (review round, correction, issuance) and design probabilities that are
exactly 0.5/0.5 in San Diego and Sacramento -- one run puts each town wholly in the administrative
design, the other wholly in the use-permit design. Both runs fit the totals; they divide the same
totals differently. This is the known weakness of whole-clock data: total durations do not identify
how time splits among steps. Intermediate milestones would (San Diego and LA County deemed-complete
dates exist, `admin_model_inputs_20260930/profiles/deemed_complete_dates.json`, but this package does
not use them because its loop is plan-check rounds, not completeness review).

Pooled across the two runs -- **not stable**: between-run R-hat for these town parameters is
1.8-1.96 except LA City (1.08-1.11), so read them as "where the two runs ended up", not estimates:

| town | P(administrative design A1) | per-review correction probability (pinc) | speed factor (1 = average town) |
|---|---:|---|---:|
| SAN DIEGO | 0.50 | 0.68 [0.54, 0.86] | 0.14 |
| LOS ANGELES COUNTY | 1.00 | 0.68 [0.51, 0.84] | 0.06 |
| SACRAMENTO | 0.50 | 0.26 [0.00, 0.58] | 0.61 |
| LOS ANGELES | 1.00 | 0.99 [0.96, 1.00] | 5.48 |
| SAN FRANCISCO | 1.00 | 0.88 [0.52, 1.00] | 7.83 |

Only LA City agrees between runs: slow (speed ~5x the average town) with plan-check reviews almost always
returning corrections (pinc ~0.99), consistent with its ~110-day median. Everything
step-level or design-level is unidentified until a milestone-bearing or longer run agrees between runs.

**A third run on the GPU and what the disagreement is.** The same package fitted with the JAX HMC
kernel (`solar_jaxhmc002`, one GPU, 1,024 particles, 6 HMC trajectories per stage, 35 stages) landed
in a third configuration (`results/solar_three_run_comparison.json`):

| run | mean log-likelihood | P(A1) San Diego / Sacramento / LA / SF | per-review correction prob. San Diego / LA / SF |
|---|---:|---|---|
| CPU blocked run 0 | -447,114 | 1 / 1 / 1 / 1 | 0.85 / 0.99 / 0.63 |
| CPU blocked run 1 | **-446,094** | 0 / 0 / 1 / 1 | 0.56 / 1.00 / 0.98 |
| GPU HMC | -446,752 | 1 / 1 / 0 / 0 | 0.96 / 0.03 / 0.14 |
| CPU blocked run 2 (extra seed) | -447,024 | 1 / 1 / 1 / 1 | 0.96 / 0.99 / 0.70 |
| GPU HMC, two more seeds (003, 004) | -446,752 / -446,752 | 1 / 1 / 0 / 0 (both) | 0.96 / 0.03 / 0.15-0.17 |

The three are not equally good explanations: they differ by up to ~1,000 log-likelihood units, so
this is not a posterior with comparable modes -- each run got trapped in a local mode, and run 1
found the best of the three. A fourth (extra-seed CPU) run returned to run 0's configuration. **All three GPU HMC runs
(three seeds) reached exactly the same configuration** (mean log-likelihood -446,752 each, same town
parameters): the HMC kernel is reproducible across seeds where the CPU blocked kernel is not -- but it
reproducibly lands ~660 log-likelihood units below the best configuration found (CPU run 1). Agreement
between runs, the gate HMC passed on W0, therefore does not establish a correct posterior on real data.
All six runs: `results/solar_all_run_comparison.json`. With likelihoods of 10^5-10^7 units the real-data posterior is extremely
peaked, and these particle/move budgets do not let particles cross between modes. Fixes, in order:
intermediate milestones (identify the step split directly), many more independent runs with the
best-evidence mode reported and its weight checked, or a tempering schedule with more moves per stage
near beta = 1. No step-level or design-level Solar permit result should be quoted from tonight.

### Solar interconnection (application -> permission to operate): fit001, 2 runs x 512 particles x 4 moves
Both runs reached beta = 1 in 81 stages (~2.6 h each on 28 CPU workers); log evidence
-8,540,598.4 and -8,540,596.6 (difference 1.8 on 8.5 million). Runs agree far better than for solar
permits, but the strict gate still fails: worst between-run R-hat 1.36
(completeness-review and correction step medians), worst estimand difference
3.3 SD.

**Structure (same in both runs):** every PG&E and SCE utility-year is design I2 (an extra utility
review step between "application complete" and PTO), every SDG&E year is I1 (none); posterior
probabilities 0 or 1. This is learned from the received / complete / approved dates of 1.3M
applications. Pooled step medians at average speed: completeness review 0.19 d, installer correction
18.4 d, extra review 10.8 d, PTO issuance 0.25 d (speed factors are not comparable across designs).

**Per-review probability that an application is returned for correction** (engine `pinc`; the number of
correction rounds is a truncated geometric in it), posterior median, by year 2017-2025:

| utility | design | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|
| PGE | I2 | 0.27 | 0.15 | 0.21 | 0.28 | 0.34 | 0.33 | 0.94 | 0.46 | 0.50 |
| SCE | I2 | 0.30 | 0.36 | 0.40 | 0.49 | 0.46 | 0.45 | 1.00 | 0.55 | 0.62 |
| SDGE | I1 | 0.18 | 0.11 | 0.06 | 0.04 | 0.07 | 0.06 | 0.27 | 0.11 | 0.10 |

The 2023 jump (pre-NEM-3.0 rush, applications filed before installation) shows up as PG&E and SCE reviews almost always returning the
application for correction. Whether those are document corrections or
waiting for installation that the model labels "correction" is not distinguishable from these dates.

**Fit to totals:** median predicted/observed ratio 1.00, 94% of records inside
their utility-year's predictive 5-95% range, 81% of utility-years
within a factor 1.5. The misfit is 2023:

| utility-year | completed | observed median d | predicted median d | inside 5-95% |
|---|---:|---:|---:|---:|
| PGE_2022 | 99,253 | 11 | 10 | 0.95 |
| PGE_2023 | 111,638 | 90 | 65 | 0.93 |
| SCE_2022 | 83,666 | 10 | 11 | 0.95 |
| SCE_2023 | 105,907 | 141 | 85 | 0.85 |
| SDGE_2022 | 33,226 | 6 | 7 | 0.95 |
| SDGE_2023 | 44,066 | 114 | 56 | 0.84 |

### ADU permits (application -> permit issued, 467 jurisdictions): one completed run -- misspecified
`adu_fit003_run0` reached beta = 1 in 160 stages (~7 h on 96 CPU workers, 256 particles x 3 moves).
`adu_fit003_run1` crashed at stage 120 (beta 0.40) on a second float-boundary bug (mention/web
probabilities; fixed, bit-identical, 125 tests) and was relaunched as `adu_fit004_run1` and then stopped at stage ~10 once run 0 showed the misfit, so there is
**no between-run check yet**. Summary: `runs/real_process_20261001/results/adu_single003/` (40 answer draws).

**The fit is not usable for structure or step burden.** Per-step "medians" run to 10^4-10^6 days:
each step's distribution is truncated at the 512-day grid (`day_grid_size`) and renormalized, so the
sampler parks steps at the cap. The design posterior is A2 (notice + comment + hearing on objection)
in 382 of 467 jurisdictions, which a ministerial-approval statute makes implausible: the extra steps
act as extra duration capacity, not as learned procedure.

Totals: 90% of completed records fall inside their jurisdiction's
predictive 5-95% range, but predicted medians are typically ~1.9x the
completed-only median (only 24% within a factor 1.5). Part of that
is correct (open cases make completed-only medians short); most of it is the stale-open-case and
grid-cap problem. LA City, which has no open cases, fits (125 vs 133 days).

| jurisdiction | completed | open | observed median d | predicted median d | inside 5-95% |
|---|---:|---:|---:|---:|---:|
| LOS ANGELES | 50,398 | 0 | 133 | 125 | 0.86 |
| LOS ANGELES COUNTY | 7,807 | 2,593 | 226 | 330 | 0.90 |
| SAN DIEGO | 5,593 | 1,366 | 304 | 380 | 0.92 |
| LONG BEACH | 2,334 | 595 | 170 | 241 | 0.92 |
| SACRAMENTO | 1,823 | 155 | 95 | 122 | 0.94 |
| SAN FRANCISCO | 1,481 | 434 | 443 | 454 | 0.91 |
| OAKLAND | 1,451 | 846 | 162 | 315 | 0.90 |
| GARDEN GROVE | 1,397 | 432 | 131 | 201 | 0.90 |
| SAN JOSE | 1,196 | 1,005 | 153 | 380 | 0.91 |
| GLENDALE | 1,117 | 176 | 159 | 204 | 1.00 |

**Held-out check** (APR Ministerial/Discretionary labels, never given to the model): weak.
Spearman rho 0.12 (p = 0.024, 371 jurisdictions);
0.09 (p = 0.10) where the model had no web evidence.
Mean P(non-ministerial) 0.90 vs 0.89 for jurisdictions with vs without any Discretionary filings:
the model is not recovering local structure from ADU timing in this specification.

**What would fix it:** a larger step grid (`day_grid_size` 2048, ~4x cost) or a weekly time unit;
terminal/abandonment outcomes instead of contaminated stale "open" cases; milestones (APR
entitlement dates, deemed-complete dates) to pin the step split; then many independent runs.
