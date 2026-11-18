# Handoff to Codex: real Solar/ADU data is model-ready; next model work (2026-10-01)

From Claude (ADU session), overnight 2026-09-30 -> 10-01, at Alex's request ("finish all
extraction, write a handoff for Codex ... refer to the code"). Code is named by file, not by
"V6". Results of the first real-data fits: `docs/2026-10-01-real-data-process-fits.md`.
Audit of the speedup work: `docs/2026-10-01-audit-of-codex-speedups.md`.

## Two model codebases this refers to
- **Process engine** (full process: designs, correction loops, town hierarchy, admin + forum +
  web-page likelihoods; the accelerated one): `pipeline/procbench/toy_statute/` -- `model.py`
  (likelihood), `smc.py` (driver), `blocked.py` (town-local blocked moves), `jax_backend.py` /
  `jax_pool.py` (GPU), `config.py` (ModelConfig/ExecutionConfig), `compression.py`, `spec.py`
  (catalog; `load_package` takes a real-statute package).
- **Conditional-frame timing fitter** (per-clock forum timing frames with source offsets):
  `pipeline/procbench/bayes_process.py` (likelihood/fit), `marginal_conditional_frames.py`
  (the marginal frame fit used for the 2026-09-30 burden frames), `conditional_case_frames.py`
  (admission contract), `source_offset_hierarchy.py` (source offsets with exact histogram
  anchors), `cohort_histograms.py`, `forum_admin_cells.py` (forum claim -> admin cell keys).

## What is now ready (all paths under `runs/`)
| item | where | state |
|---|---|---|
| Admin timing cohorts, 9 sources | `admin_model_inputs_20260930/` (sk3 authoritative) | **Fix 4 (10-01):** HCD APR rows no longer dropped for lacking an A<->A2 match; APR ADU projects 108k -> 214k; open/terminal applications kept |
| Per-project permit linkage | `admin_model_inputs_20260930/linked_permits/{src}_links.jsonl` (sk3) | every selected ADU/solar project in 6 city sources -> other permits on the same parcel within [-180 d, +730 d], revision-like flags, journey span |
| Deemed-complete dates | `admin_model_inputs_20260930/profiles/deemed_complete_dates.json` | San Diego 89,826 / EPIC-LA 29,541 projects |
| City x requirement table | `adu_city_requirements_20260930/` | 524 jurisdictions joined; HCD findings, ordinance provisions, APR Ministerial/Discretionary counts per jurisdiction-year |
| Forum cell keys (Gemma) | `forum_cell_keys_20260930/cell_keys.jsonl` | Solar city+year 65, utility+year 194; ADU city+year 20 |
| SolarAPP+ (3 NREL reports) | `admin_pdf_extraction_20261001/solarapp_values.json` | 1,692 rows incl. per-AHJ medians read from charts (precision recorded) |
| Terner/CCI reports incl. 2021 homeowner survey | `admin_pdf_extraction_20261001/terner_values.json` | 730 rows; Q22 months approval-start -> completion bins (n=660) |
| CPUC Rule 21 quarterly reports (84) | `admin_pdf_extraction_20261001/cpuc_rule21_values.json` | 4,836 count rows (no timeline tables exist in these reports) |
| Houzz ADU threads with all answers | `houzz_triage_20261001/packets.json` | rendered + Gemma-triaged: 1,718 threads, 286 kept, 71 strong; ready to code |
| Forum-vs-admin offsets with own-cell anchors | `forum_admin_calibration_20261001/` | interconnection 0.77 [0.54,1.00], permits pooled 0.89 [0.56,1.35] |
| **Engine-ready real evidence** | `real_process_20261001/{adu_permit,solar_permit,solar_interconnection}/` | packages + evidence + priors + ledgers; first fits launched on sk3 |

## Tasks for Codex, in order
1. **Review the five engine changes** in `toy_statute` (web-listing mask; opt-in
   `milestone_contamination`; opt-in `pending_contamination`; float-boundary branch in
   `Model.combo_logw`; `JaxPool.map` matching driver operations by name so the documented
   `python -m ...smc` GPU command runs) and the real-data mapping in
   `real_process_20261001/README.md`. One bounded review; defaults are bit-identical
   (`checks/web_mask_equivalence.json`, 123 tests). Accept, reject or amend in one pass.
2. **Read the first fit results** (results doc). Do not silently extend failed runs; a bigger
   budget is a new declared run. The ADU fit (1,423 parameters) at 256 particles is a
   first pass, not a certified posterior. **Mode trapping is the main inference problem:** independent
   Solar permit runs ended in different local modes ~1,000 log-likelihood units apart (CPU and GPU
   alike); interconnection runs agreed. Before trusting any step- or design-level number, run many
   independent fits and report how many reach the best mode, add intermediate milestones, and/or add
   moves near beta = 1.
3. **Engine extensions the real data needs** (highest value first; each a declared target change):
   a. **Source offset for reports.** `model.py` has report noise (`lsig_r`) but no reporting bias;
      the standalone calibration (`docs/2026-09-30-solar-interconnection-calibration.md`) showed
      how to add delta. Put it in the engine, separately for forum vs admin.
   b. **Terminal outcomes** (withdrawn/expired/denied: ~5k ADU, ~7k solar cases in ledgers) as a
      competing exit from the loop, not dropped. Same mechanism for stale "open" records (ADU:
      10,046 open cases older than 4 years), which tonight's fits absorb only through
      `pending_contamination`.
   c. **Post-permit phase** (issued -> final: ADU 130k completed, solar 82k): a second package
      with a construction step and an inspection-failure loop (SolarAPP+ gives inspection
      failure rates per AHJ for checking).
   d. **Case-level design evidence:** APR labels each ADU application Ministerial/Discretionary;
      the engine has one design per town. A per-case design mixture would use this directly.
   e. **Forum reports the engine cannot place:** partial intervals (e.g. submission -> first
      corrections) and reports without a city need a partial-report likelihood and a
      geography mixture (ledgers list them).
   f. **JAX at real scale:** towns only share a compiled bucket when every evidence array has the
      same shape, so 467 real towns compile one by one (measured in the audit). Pad per-town
      arrays to a few shape classes with zero-weight cases before promoting the GPU path.
   g. **DG rework:** 129,519 superseded interconnection applications are resubmissions; link each
      to its replacement as a correction round instead of excluding it.
   h. **Eras:** towns are jurisdiction (permits) or utility x year (interconnection); add era
      splits for the ADU law changes (2020, 2023) and NEM 3 where the data support it.
4. **Covariates** from `adu_city_requirements_20260930/` (HCD findings, ordinance provisions,
   Ministerial/Discretionary shares): as town design priors (`struct_prior`) or a regression on
   town speed / correction probability. Record which.
5. **Aggregate anchors** not yet in any likelihood: SolarAPP+ per-AHJ medians, Terner Q22 bins
   (whole-journey ADU), CPUC application/withdrawal counts. They need an aggregate-statistic
   likelihood (median/binned share), not per-case records.
6. **Step counts and rework from permit linkage** (`linked_permits/`): companion and
   revision-like permits per project are direct step/rework counts for the burden tables.

## Working rules (unchanged)
One scripted check per artifact; no verification campaigns; conservative default + one-line
note when ambiguous; keep failures; one results doc per task; no commits/deletions.
