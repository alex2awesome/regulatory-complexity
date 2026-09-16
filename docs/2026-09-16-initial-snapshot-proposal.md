# Initial Git snapshot proposal

2026-09-16. **Proposed file list only. Nothing is staged or committed.** Alex approved preparing this list, not committing it. Review and explicit approval of this scope are required before an initial commit or package moves.

This snapshots the current source, tests, documentation and small reference/result files **after the first audit-repair tranche and before package reorganization**. It cannot create a retrospective pre-overnight baseline. It is not a backup of the full research corpus or experiments.

## Scope

324 proposed files; approximately 9.47 MiB before this proposal file. Counts include this proposal.

| Group | Files |
|---|---:|
| Root files | 5 |
| benchmark/ | 2 |
| benchmark/realworld/ | 20 |
| benchmark/synth/ (excluding worlds) | 39 |
| dashboard/ | 17 |
| docs/ | 44 |
| examples/ | 1 |
| pipeline/ | 149 |
| runs/ | 1 |
| tests/ | 45 |
| worlds/ | 1 |

Included deliberately:

- All current process and discretion source modules, including legacy V3–V5 code for an import-stable starting point.
- Tests and requirements; benchmark generators, schemas, render/verification briefs and curated real-world task/gold JSON.
- Documentation, original and simplified TikZ/LaTeX sources, six rendered figure PDFs, HTML/SVG diagrams and meeting notes.
- Dashboard code/templates and the existing small `dashboard/data/*.json` summaries (including `real_docs.json`, about 1.5 MiB); these are results/reference files, not raw draws.
- The small `worlds/ab2533_sanitation.json` example, not generated synthetic world directories.
- Project conventions and `runs/README.md` archive policy.

Excluded and left untouched:

- `runs/**`, except `runs/README.md`: raw draws, fit outputs, snapshots, prompts and new audit artifacts need a separate verified archive.
- `corpus/**`: downloaded documents and research data, including its nested dependency copies.
- `benchmark/synth/worlds/**`: W1/W2/generated specifications, rendered corpora, logs and truth.
- `benchmark/sources/**`, except its `.gitignore`: six nested vendor repositories; do not accidentally create gitlinks.
- Generated `dashboard/out/**`, generated example directories, virtual environments, bytecode and caches.
- Git internals. No external symlink targets are followed.

The experimental evidence linked from documentation will still be local after this source commit. The archive destination and tracked experiment registry remain pending; see [archive policy](../runs/README.md). Before staging, re-enumerate this exact allowlist and review any files created or changed since this proposal. Do not use `git add .`.

## Exact proposed paths

```text
.gitignore
CLAUDE.md
README.md
benchmark/MANIFEST.md
benchmark/realworld/README.md
benchmark/realworld/build_tasks.py
benchmark/realworld/gold/README.md
benchmark/realworld/gold/adu_permit__city_of_san_jose.json
benchmark/realworld/gold/adu_permit__sonoma_county_permit_sonoma.json
benchmark/realworld/gold/calfresh__la_county_dpss.json
benchmark/realworld/gold/calfresh__santa_clara_county_ssa.json
benchmark/realworld/gold/cpra_request__city_county_sf.json
benchmark/realworld/gold/cpra_request__lapd.json
benchmark/realworld/gold/cslb_license__cslb.json
benchmark/realworld/gold/dros_firearm__ca_doj_bof_dealer.json
benchmark/realworld/gold/food_facility__city_and_county_of_san_francisco.json
benchmark/realworld/gold/food_facility__la_county_dph_environmental_health.json
benchmark/realworld/gold/food_facility__san_diego_county_dehq_food_and_housing.json
benchmark/realworld/gold/n400_naturalization__uscis_field_office.json
benchmark/realworld/gold/solar_permit__oakland_solarapp.json
benchmark/realworld/gold/solar_permit__san_diego_expedited.json
benchmark/realworld/gold/solar_permit__traditional_generic_ca.json
benchmark/realworld/gold/ui_claim__edd.json
benchmark/realworld/tasks.json
benchmark/sources/.gitignore
benchmark/synth/DESIGN.md
benchmark/synth/briefs/RENDER_BRIEF.md
benchmark/synth/briefs/VERIFY_BRIEF.md
benchmark/synth/briefs/render_agent_prompt.md
benchmark/synth/briefs/verify_agent_prompt.md
benchmark/synth/generator/README.md
benchmark/synth/generator/__init__.py
benchmark/synth/generator/build.py
benchmark/synth/generator/ceiling.py
benchmark/synth/generator/domains.py
benchmark/synth/generator/local_rules.py
benchmark/synth/generator/processes.py
benchmark/synth/generator/rng.py
benchmark/synth/generator/simulate.py
benchmark/synth/generator/specs.py
benchmark/synth/generator/statutes.py
benchmark/synth/generator/test_generator.py
benchmark/synth/generator/visibility.py
benchmark/synth/generator/world.py
benchmark/synth/render/README.md
benchmark/synth/render/batches.py
benchmark/synth/render/prepare_batch.py
benchmark/synth/schemas/artifact_spec.schema.json
benchmark/synth/schemas/ceiling.schema.json
benchmark/synth/schemas/local_rule_truth.schema.json
benchmark/synth/schemas/process_truth.schema.json
benchmark/synth/schemas/statute_truth.schema.json
benchmark/synth/schemas/tasks.schema.json
benchmark/synth/schemas/validate.py
benchmark/synth/schemas/verify.schema.json
benchmark/synth/style/distill_exemplars.py
benchmark/synth/style/forms.md
benchmark/synth/style/legal_text.md
benchmark/synth/style/municipal_pages.md
benchmark/synth/style/news_and_forums.md
benchmark/synth/style/reddit_exemplars.md
benchmark/synth/style/reddit_stats.json
benchmark/synth/style/reddit_style.md
benchmark/synth/style/staff_reports.md
dashboard/_toy_process_snippet.html
dashboard/build.py
dashboard/build_process.py
dashboard/data/bayes.json
dashboard/data/drift.json
dashboard/data/hier_posterior.json
dashboard/data/latent_timing.json
dashboard/data/model_comparison.json
dashboard/data/priors.json
dashboard/data/real.json
dashboard/data/real_docs.json
dashboard/data/richness.json
dashboard/data/synth.json
dashboard/data/synth_pred.json
dashboard/data/synth_results.json
dashboard/process_template.html
dashboard/template.html
docs/2026-09-02-plan.md
docs/2026-09-10-benchmarks-inventory.md
docs/2026-09-15-generative-model.md
docs/2026-09-15-process-benchmarks-plan.md
docs/2026-09-16-bayesian-audit-implementation.md
docs/2026-09-16-bayesian-overnight-audit.md
docs/2026-09-16-bayesian-process-v3-results.md
docs/2026-09-16-bayesian-process-v3.md
docs/2026-09-16-bayesian-process-v4-protocol.md
docs/2026-09-16-bayesian-process-v4-results.md
docs/2026-09-16-bayesian-process-v4.md
docs/2026-09-16-bayesian-process-v5-protocol.md
docs/2026-09-16-bayesian-process-v5-results.md
docs/2026-09-16-bayesian-process-v5.md
docs/2026-09-16-bayesian-process-v6-protocol.md
docs/2026-09-16-bayesian-process-v6-results.md
docs/2026-09-16-bayesian-visit-clocks.md
docs/2026-09-16-initial-snapshot-proposal.md
docs/design.md
docs/figures/latex_plate_diagram/README.md
docs/figures/latex_plate_diagram/generative_model.pdf
docs/figures/latex_plate_diagram/generative_model.tex
docs/figures/latex_plate_diagram/plate_diagram.pdf
docs/figures/latex_plate_diagram/plate_diagram.tex
docs/figures/latex_plate_diagram/plate_diagram_caption.tex
docs/figures/latex_plate_diagram/plate_diagram_standalone.pdf
docs/figures/latex_plate_diagram/plate_diagram_standalone.tex
docs/figures/latex_plate_diagram_simplified/.gitignore
docs/figures/latex_plate_diagram_simplified/README.md
docs/figures/latex_plate_diagram_simplified/architectures_v4_v5.pdf
docs/figures/latex_plate_diagram_simplified/architectures_v4_v5.tex
docs/figures/latex_plate_diagram_simplified/audit_terms.py
docs/figures/latex_plate_diagram_simplified/generative_model.pdf
docs/figures/latex_plate_diagram_simplified/generative_model.tex
docs/figures/latex_plate_diagram_simplified/plate_diagram.tex
docs/figures/latex_plate_diagram_simplified/plate_diagram_caption.tex
docs/figures/latex_plate_diagram_simplified/plate_diagram_standalone.pdf
docs/figures/latex_plate_diagram_simplified/plate_diagram_standalone.tex
docs/figures/plate_diagram.html
docs/figures/plate_diagram.svg
docs/meetings/2026-09-02-dan-ho.md
docs/references.md
docs/related-work-bayesian.md
docs/related-work.md
examples/.gitkeep
pipeline/burden_priors.json
pipeline/common.py
pipeline/crosswalk_eval.py
pipeline/divergence.py
pipeline/executor.py
pipeline/instrument.py
pipeline/llm.py
pipeline/looseness.py
pipeline/metrics.py
pipeline/priors/README.md
pipeline/priors/compare_models.py
pipeline/priors/drift_model.py
pipeline/priors/harvest_structured.py
pipeline/priors/hier_fit.py
pipeline/priors/latent_timing.py
pipeline/priors/observations/adu_permit.json
pipeline/priors/observations/calfresh.json
pipeline/priors/observations/cpra_request.json
pipeline/priors/observations/cslb_license.json
pipeline/priors/observations/dros_firearm.json
pipeline/priors/observations/food_facility.json
pipeline/priors/observations/n400_naturalization.json
pipeline/priors/observations/solar_permit.structured.json
pipeline/priors/observations/ui_claim.json
pipeline/priors/richness.py
pipeline/priors/rollup.py
pipeline/priors/taxonomy.json
pipeline/procbench/README.md
pipeline/procbench/README_web.md
pipeline/procbench/__init__.py
pipeline/procbench/align.py
pipeline/procbench/align_agent.py
pipeline/procbench/approximation_checks.py
pipeline/procbench/audit_benchmark_clocks.py
pipeline/procbench/audit_burden_counts.py
pipeline/procbench/audit_calibration_target.py
pipeline/procbench/audit_case_outcomes.py
pipeline/procbench/audit_clocks.py
pipeline/procbench/audit_context.py
pipeline/procbench/audit_extraction_lineage.py
pipeline/procbench/audit_granularity.py
pipeline/procbench/audit_measurement_semantics.py
pipeline/procbench/audit_preparation_clocks.py
pipeline/procbench/audit_visit_hypotheses.py
pipeline/procbench/audit_visit_likelihood.py
pipeline/procbench/audit_visit_observations.py
pipeline/procbench/bayes_effort.py
pipeline/procbench/bayes_evidence.py
pipeline/procbench/bayes_hierarchy.py
pipeline/procbench/bayes_outcome_measurement.py
pipeline/procbench/bayes_preparation_measurement.py
pipeline/procbench/bayes_process.py
pipeline/procbench/bayes_process_measurement.py
pipeline/procbench/bayes_repeat_timing.py
pipeline/procbench/bayes_trace_hierarchy.py
pipeline/procbench/bayes_variable_preparation.py
pipeline/procbench/calibrate_hierarchy.py
pipeline/procbench/check_effort.py
pipeline/procbench/check_hierarchy.py
pipeline/procbench/check_process_quadrature.py
pipeline/procbench/compact_visit_trace.py
pipeline/procbench/compare_evidence_runs.py
pipeline/procbench/compare_process_measurement.py
pipeline/procbench/compare_visit_integration.py
pipeline/procbench/compare_visit_phases.py
pipeline/procbench/compile_visit_durations.py
pipeline/procbench/diagnose_process_reports.py
pipeline/procbench/evaluate_burden.py
pipeline/procbench/evidence_baseline.py
pipeline/procbench/evidence_contract.py
pipeline/procbench/evidence_support.py
pipeline/procbench/extend_hierarchy.py
pipeline/procbench/extend_process_measurement.py
pipeline/procbench/extend_validation.py
pipeline/procbench/extend_visit_hierarchy.py
pipeline/procbench/generate_visit_integration.py
pipeline/procbench/generate_visit_interpretations.py
pipeline/procbench/generate_visit_phases.py
pipeline/procbench/incremental.py
pipeline/procbench/latent_gaussian.py
pipeline/procbench/measurement_kernel.py
pipeline/procbench/metrics.py
pipeline/procbench/phase_mixture.py
pipeline/procbench/policies/w1_development_compiler.json
pipeline/procbench/prepare_semantic_labels.py
pipeline/procbench/prior_predictive.py
pipeline/procbench/prompts/extract_candidates.md
pipeline/procbench/prompts/merge_decide.md
pipeline/procbench/prompts/reconcile_evidence_v2.md
pipeline/procbench/prompts/solve_agent.md
pipeline/procbench/prompts/solve_oracle.md
pipeline/procbench/reconcile_evidence.py
pipeline/procbench/refine_visit_predictions.py
pipeline/procbench/refresh_synth_scores.py
pipeline/procbench/repair_calibration_rng.py
pipeline/procbench/rework_counts.py
pipeline/procbench/run_bayes_synth.py
pipeline/procbench/run_bench.py
pipeline/procbench/run_hierarchical.py
pipeline/procbench/run_process_measurement.py
pipeline/procbench/run_visit_hierarchy.py
pipeline/procbench/schedule_kernel.py
pipeline/procbench/score.py
pipeline/procbench/semantic_calibration.py
pipeline/procbench/sensitivity_hierarchy.py
pipeline/procbench/solve.py
pipeline/procbench/summarize_calibration.py
pipeline/procbench/summarize_hierarchical.py
pipeline/procbench/timing_contract.py
pipeline/procbench/validate_hierarchy.py
pipeline/procbench/validate_kernels.py
pipeline/procbench/validate_mixed_sources.py
pipeline/procbench/validate_process_selection.py
pipeline/procbench/validate_reference.py
pipeline/procbench/validate_repeat_timing.py
pipeline/procbench/verify_generator_clock_extension.py
pipeline/procbench/visit_clocks.py
pipeline/procbench/visit_observation_operators.py
pipeline/procbench/web.py
pipeline/process_model.py
pipeline/prompts/01_intake.md
pipeline/prompts/02_compile.md
pipeline/prompts/03_burden.md
pipeline/prompts/04_cases.md
pipeline/prompts/05_adjudicate.md
pipeline/prompts/06_render_vignette.md
pipeline/prompts/07_reading_decision.md
pipeline/prompts/07b_reading_decision_batch.md
pipeline/prompts/08_screen_span.md
pipeline/prompts/09_tag_discourse.md
pipeline/prompts/10_normalize_checklist.md
pipeline/prompts/11_direct_read.md
pipeline/prompts/12_case_facts.md
pipeline/prompts/13_crosswalk.md
pipeline/prompts/14_process_compile.md
pipeline/recon/reddit_fetch.py
pipeline/run.py
pipeline/sara_eval.py
pipeline/schemas/burden_audit.schema.json
pipeline/schemas/case.schema.json
pipeline/schemas/decision_tree.schema.json
pipeline/schemas/discourse.schema.json
pipeline/schemas/intake.schema.json
pipeline/schemas/latent_world.schema.json
pipeline/schemas/process_model.schema.json
pipeline/schemas/readings.schema.json
pipeline/screener.py
pipeline/simplify.py
pipeline/worlds.py
requirements-bayes.txt
requirements.txt
runs/README.md
tests/smoke.py
tests/test_approximation_checks.py
tests/test_bayes_hierarchy.py
tests/test_bayes_process.py
tests/test_bayesian_audit_repairs.py
tests/test_burden_counts.py
tests/test_burden_evaluation.py
tests/test_calibration_rng.py
tests/test_compact_visit_trace.py
tests/test_compare_visit_integration.py
tests/test_compile_visit_durations.py
tests/test_generator_rework_contract.py
tests/test_generator_timing_contracts.py
tests/test_generator_visit_accounting.py
tests/test_information_report.py
tests/test_instrument.py
tests/test_latent_gaussian.py
tests/test_mixed_sources.py
tests/test_outcome_measurement.py
tests/test_posterior_postprocessing.py
tests/test_preparation_clocks.py
tests/test_preparation_measurement.py
tests/test_prior_comparison.py
tests/test_procbench_score.py
tests/test_procbench_web.py
tests/test_process_measurement.py
tests/test_process_quadrature_reference.py
tests/test_repeat_timing.py
tests/test_report_attributions.py
tests/test_rework_counts.py
tests/test_score.py
tests/test_semantic_calibration.py
tests/test_synth_dashboard_scores.py
tests/test_timing_contract.py
tests/test_trace_hierarchy.py
tests/test_variable_preparation.py
tests/test_visit_clocks.py
tests/test_visit_hypotheses.py
tests/test_visit_interpretation_experiment.py
tests/test_visit_interpretation_likelihood.py
tests/test_visit_observation_audit.py
tests/test_visit_observation_operators.py
tests/test_visit_phase_experiment.py
tests/test_visit_phase_hierarchy.py
tests/test_visit_prediction_refinement.py
worlds/ab2533_sanitation.json
```

