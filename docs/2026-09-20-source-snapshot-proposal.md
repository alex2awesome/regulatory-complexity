# Source snapshot proposal — 2026-09-20

**Status: exact file list prepared; not staged, committed or pushed.**

This proposes the working-tree delta from `e581748`: **251 files**,
4,461,826 bytes (4.26 MiB) before these two generated proposal records.
It includes existing work by both agents; it does not claim all changes are mine.

Alex authorized list preparation only. Approval of this exact path scope is still
required before staging or committing. Recheck file hashes and report any drift
before committing; do not use `git add .`. There is no push authorization.

## Included and excluded

| Group | Changed/new paths |
|---|---:|
| CLAUDE.md | 1 |
| README.md | 1 |
| benchmark | 44 |
| docs | 78 |
| pipeline | 85 |
| tests | 42 |

Included: source, tests, generator/rendering tools, schemas, documentation,
planning/audit records and small source-level assets already within this scope.
This is a preservation snapshot, not a statement that every research result
passes its gate or that the refactor is complete.

Excluded: raw corpora, generated synthetic worlds and fixture outputs, raw
runs/draws/prompts, logs, caches, vendored repositories and dependencies.
The existing tracked `runs/README.md` is eligible if changed; no other run file is.
The ignored data trees are excluded by policy, not exhaustively scanned here.

**This commit would not back up the evidence or free significant disk space.**
Data archiving still needs an approved destination, checksums and a restore test.
No deletion or external transfer is authorized.

The [machine-readable inventory](scoping/2026-09-20-source-snapshot-files.json)
records hashes/sizes for every proposed content path and grouped exclusions.
The two proposal records list themselves without recursive self-hashes.

## Exact proposed paths

```text
CLAUDE.md
README.md
benchmark/synth/DESIGN.md
benchmark/synth/briefs/RENDER_BRIEF.md
benchmark/synth/briefs/VERIFY_BRIEF.md
benchmark/synth/briefs/render_agent_prompt.md
benchmark/synth/generator/README.md
benchmark/synth/generator/build.py
benchmark/synth/generator/capacity.py
benchmark/synth/generator/ceiling.py
benchmark/synth/generator/counties.py
benchmark/synth/generator/decision.py
benchmark/synth/generator/lineage.py
benchmark/synth/generator/local_rules.py
benchmark/synth/generator/processes.py
benchmark/synth/generator/simulate.py
benchmark/synth/generator/specs.py
benchmark/synth/generator/statutes.py
benchmark/synth/generator/visibility.py
benchmark/synth/generator/world.py
benchmark/synth/render/batches.py
benchmark/synth/render/complete_slice.py
benchmark/synth/render/correct_aggregate_chronology.py
benchmark/synth/render/correct_appeal_authorities.py
benchmark/synth/render/correct_deferred_appeal_authorities.py
benchmark/synth/render/correct_empty_checklists.py
benchmark/synth/render/correct_fee_due_description.py
benchmark/synth/render/correct_fee_instructions.py
benchmark/synth/render/correct_slice_inputs.py
benchmark/synth/render/launch_ledger.py
benchmark/synth/render/prepare_batch.py
benchmark/synth/render/reconcile_concurrent_hold.py
benchmark/synth/render/repair.py
benchmark/synth/render/selection.py
benchmark/synth/render/stale_verdicts.py
benchmark/synth/render/status.py
benchmark/synth/render/statute_order.py
benchmark/synth/render/verify_batches.py
benchmark/synth/schemas/artifact_spec.schema.json
benchmark/synth/schemas/ceiling.schema.json
benchmark/synth/schemas/local_rule_truth.schema.json
benchmark/synth/schemas/process_truth.schema.json
benchmark/synth/schemas/statute_truth.schema.json
benchmark/synth/schemas/validate.py
benchmark/synth/style/news_and_forums.md
benchmark/synth/style/reddit_style.md
docs/2026-09-16-bayesian-audit-implementation.md
docs/2026-09-16-county-scale-up-plan.md
docs/2026-09-16-initial-snapshot-proposal.md
docs/2026-09-16-source-volume-register.md
docs/2026-09-16-synthetic-corpus-generation-plan.md
docs/2026-09-16-w2-decision-log.md
docs/2026-09-16-w2-dev-001-release-report.md
docs/2026-09-16-w2-generator-spec.md
docs/2026-09-17-s12-s03-completion-and-v6.md
docs/2026-09-17-single-statute-minimum-scope.md
docs/2026-09-17-w2-decision-log-review.md
docs/2026-09-17-w2-resume.md
docs/2026-09-18-bayesian-machinery-audit.md
docs/2026-09-18-burden-channel-changes.md
docs/2026-09-18-evidence-contract-visit-basis-gap.md
docs/2026-09-19-bayesian-burden-audit.md
docs/2026-09-19-codex-parse-continuation.md
docs/2026-09-19-next-steps-plan.md
docs/2026-09-19-parse-handoff-to-codex.md
docs/2026-09-19-real-corpus-first-results.md
docs/2026-09-19-real-corpus-inventory-audit.md
docs/2026-09-19-real-corpus-machinery-gaps.md
docs/2026-09-19-recovered-sk3-fit-reports.md
docs/2026-09-19-solartrace-input-and-sampler-audit.md
docs/2026-09-19-supplemental-source-freeze.md
docs/2026-09-19-v6-evaluation-and-selection-progress.md
docs/2026-09-20-audit-of-codex-work.md
docs/2026-09-20-source-snapshot-proposal.md
docs/2026-09-20-two-statute-recovery-plan.md
docs/scoping/2026-09-16-adu-58-counties.md
docs/scoping/2026-09-16-agency-workload-target.md
docs/scoping/2026-09-16-appeals-capacity-target.md
docs/scoping/2026-09-16-apr-discretion-variation.md
docs/scoping/2026-09-16-apr-permit-timing.md
docs/scoping/2026-09-16-assessment-appeals-target.md
docs/scoping/2026-09-16-calfresh-58-counties.md
docs/scoping/2026-09-16-calibration-bridge.md
docs/scoping/2026-09-16-calworks-target.md
docs/scoping/2026-09-16-ccw-15-small-counties-findings.md
docs/scoping/2026-09-16-ccw-remaining-43-counties.md
docs/scoping/2026-09-16-county-covariates.md
docs/scoping/2026-09-16-county-environmental-health-58.md
docs/scoping/2026-09-16-county-scale-execution.md
docs/scoping/2026-09-16-county-user-evidence-enrichment.md
docs/scoping/2026-09-16-cross-scoping-audit.md
docs/scoping/2026-09-16-forums-beyond-reddit.md
docs/scoping/2026-09-16-general-assistance-58-counties.md
docs/scoping/2026-09-16-general-assistance-source-audit-codex.md
docs/scoping/2026-09-16-ihss-timing-target.md
docs/scoping/2026-09-16-medical-application-timing-target.md
docs/scoping/2026-09-16-other-58-county-statutes-sweep.md
docs/scoping/2026-09-16-p12-independent-spotcheck.md
docs/scoping/2026-09-16-permit-labor-target.md
docs/scoping/2026-09-16-state-hearings-target.md
docs/scoping/2026-09-16-wide-net-retrieval.md
docs/scoping/2026-09-16-workload-detail-target.md
docs/scoping/2026-09-17-adu-primary-followup.md
docs/scoping/2026-09-17-exhaustive-retrieval-progress.md
docs/scoping/2026-09-17-exhaustive-retrieval-protocol.md
docs/scoping/2026-09-17-statute-completion-estimates.json
docs/scoping/2026-09-17-w2-decision-review-diagnostics.json
docs/scoping/2026-09-17-w2-frozen-split-check.json
docs/scoping/2026-09-17-w2-readiness-followup.json
docs/scoping/2026-09-17-w2-v6-handoff.md
docs/scoping/2026-09-17-well-primary-followup.md
docs/scoping/2026-09-20-scope-and-repair-authorizations.json
docs/scoping/2026-09-20-source-snapshot-files.json
docs/scoping/FINDINGS.jsonl
docs/scoping/N12_RETRIEVAL_RUNTIME.json
docs/scoping/W2_V6_WATCH.json
docs/scoping/WORK_PACKETS.json
docs/scoping/w2_v6_watch/poll_20260917084324Z.json
docs/scoping/w2_v6_watch/poll_20260917094336Z.json
docs/scoping/w2_v6_watch/poll_20260917094432Z.json
docs/scoping/w2_v6_watch/poll_20260917104442Z.json
docs/scoping/w2_v6_watch/poll_20260917114455Z.json
docs/scoping/w2_v6_watch/poll_20260917124503Z.json
docs/scoping/w2_v6_watch/poll_20260917134951Z.json
pipeline/procbench/README.md
pipeline/procbench/audit_benchmark_clocks.py
pipeline/procbench/audit_burden_counts.py
pipeline/procbench/audit_calibration_target.py
pipeline/procbench/audit_case_outcomes.py
pipeline/procbench/audit_clocks.py
pipeline/procbench/audit_context.py
pipeline/procbench/audit_copied_claims.py
pipeline/procbench/audit_corpus_anchors.py
pipeline/procbench/audit_cross_ledger_cases.py
pipeline/procbench/audit_extraction_lineage.py
pipeline/procbench/audit_fee_scope.py
pipeline/procbench/audit_granularity.py
pipeline/procbench/audit_measurement_semantics.py
pipeline/procbench/audit_preparation_clocks.py
pipeline/procbench/audit_visit_hypotheses.py
pipeline/procbench/audit_visit_likelihood.py
pipeline/procbench/audit_visit_observations.py
pipeline/procbench/bayes_trace_hierarchy.py
pipeline/procbench/bridge_structural_routes.py
pipeline/procbench/build_semantic_labels.py
pipeline/procbench/burden_channels.py
pipeline/procbench/calibrate_hierarchy.py
pipeline/procbench/check_effort.py
pipeline/procbench/check_hierarchy.py
pipeline/procbench/check_process_quadrature.py
pipeline/procbench/cohort_quantiles.py
pipeline/procbench/compact_visit_trace.py
pipeline/procbench/compare_evidence_runs.py
pipeline/procbench/compare_process_measurement.py
pipeline/procbench/compare_visit_integration.py
pipeline/procbench/compare_visit_phases.py
pipeline/procbench/compile_visit_durations.py
pipeline/procbench/convert_counts_sidecar.py
pipeline/procbench/decision_metrics.py
pipeline/procbench/decision_scope_binding.py
pipeline/procbench/dedup_copied_cases.py
pipeline/procbench/derive_audit_skeletons.py
pipeline/procbench/derive_structural_handoff.py
pipeline/procbench/diagnose_process_reports.py
pipeline/procbench/evaluate_burden.py
pipeline/procbench/evidence_baseline.py
pipeline/procbench/extend_hierarchy.py
pipeline/procbench/extend_process_measurement.py
pipeline/procbench/extend_validation.py
pipeline/procbench/extend_visit_hierarchy.py
pipeline/procbench/generate_visit_integration.py
pipeline/procbench/generate_visit_interpretations.py
pipeline/procbench/generate_visit_phases.py
pipeline/procbench/import_apr_timing.py
pipeline/procbench/import_solartrace.py
pipeline/procbench/infra/__init__.py
pipeline/procbench/infra/codex_runner.py
pipeline/procbench/infra/manifest.py
pipeline/procbench/infra/scoring.py
pipeline/procbench/plan_forum_parse.py
pipeline/procbench/prepare_semantic_labels.py
pipeline/procbench/prior_predictive.py
pipeline/procbench/project_forum_structure.py
pipeline/procbench/reconcile_evidence.py
pipeline/procbench/refine_visit_predictions.py
pipeline/procbench/repair_calibration_rng.py
pipeline/procbench/run_bayes_synth.py
pipeline/procbench/run_hierarchical.py
pipeline/procbench/run_process_measurement.py
pipeline/procbench/run_visit_hierarchy.py
pipeline/procbench/semantic_calibration.py
pipeline/procbench/sensitivity_hierarchy.py
pipeline/procbench/summarize_calibration.py
pipeline/procbench/summarize_hierarchical.py
pipeline/procbench/validate_hierarchy.py
pipeline/procbench/validate_kernels.py
pipeline/procbench/validate_mixed_sources.py
pipeline/procbench/validate_process_selection.py
pipeline/procbench/validate_reference.py
pipeline/procbench/validate_repeat_timing.py
pipeline/procbench/verify_generator_clock_extension.py
pipeline/recon/apr_discretion.py
pipeline/recon/apr_join_clocks.py
pipeline/recon/apr_permit_timing.py
pipeline/recon/build_county_covariates.py
pipeline/recon/county_coverage.py
pipeline/recon/retrieval_closure.py
pipeline/recon/scoping_log.py
pipeline/recon/source_volume.py
tests/conftest.py
tests/procbench_fixtures.py
tests/test_agency_pooling.py
tests/test_bayesian_audit_repairs.py
tests/test_bridge_structural_routes.py
tests/test_burden_channels_compile.py
tests/test_burden_counts.py
tests/test_case_paths.py
tests/test_cohort_quantiles.py
tests/test_compact_visit_trace.py
tests/test_compile_visit_durations.py
tests/test_convert_counts_sidecar.py
tests/test_copied_claims.py
tests/test_corpus_anchor_audit.py
tests/test_decision_scope_binding.py
tests/test_derive_audit_skeletons.py
tests/test_derive_structural_handoff.py
tests/test_extend_provenance.py
tests/test_fee_scope_audit.py
tests/test_generator_county_panel.py
tests/test_generator_decision_model.py
tests/test_generator_lineage.py
tests/test_import_apr_timing.py
tests/test_import_solartrace_panel.py
tests/test_inter_operation_dwell.py
tests/test_lane_isolation.py
tests/test_money_channel.py
tests/test_operation_centered_sampler.py
tests/test_procbench_infra.py
tests/test_render_packet_isolation.py
tests/test_selection_population_cache.py
tests/test_semantic_calibration.py
tests/test_slice_input_corrections.py
tests/test_trace_hierarchy.py
tests/test_v6_burden_evaluation.py
tests/test_verdict_freshness.py
tests/test_visit_block_scheduling.py
tests/test_visit_interpretation_likelihood.py
tests/test_visit_phase_experiment.py
tests/test_visit_phase_hierarchy.py
tests/test_visit_prediction_refinement.py
tests/test_visit_task_priors.py
```

## Visible exclusions

| Root | Excluded paths | Reason |
|---|---:|---|
| benchmark | 33,844 | generated world, vendored dependency or generated dashboard |
| corpus | 14,430 | outside source/tests/docs snapshot scope |
| logs | 1 | outside source/tests/docs snapshot scope |

Counts are Git-visible changed/untracked path entries, not a document inventory.
