# Project working conventions

- Read `README.md`, `docs/2026-09-16-bayesian-overnight-audit.md`, and
  `docs/2026-09-16-bayesian-audit-implementation.md` before process-model work.
- V6 is the integration target. V3–V5 are historical controls, not new competing
  architectures. Preserve their saved inputs, snapshots, draws and failures.
- Date plans, protocols, results and audits (`YYYY-MM-DD-...`). Keep living design
  documents undated. Do not rewrite the independent audit to manufacture agreement.
- Do not commit, stage broad directories, or move packages without Alex's approval
  of the snapshot/refactor scope. Preserve unrelated user changes.
- Extractors and fitters must not read benchmark `truth/`, generator specs, or
  scores. Label-review/evaluation utilities may read explicitly designated
  development truth and must record it. Calibration never reads reserved labels.
- Semantic ambiguity follows the audit's measured split: evaluate top readings
  per class; keep sufficiently accurate classes upstream; use calibrated candidate
  weights for others and validate timing/count gains against top-reading controls.
  K LLM votes are correlated predictors, not independent labels. Re-measure on new
  worlds/extractors. Include residual/out-of-chart possibilities.
- Report retained, residual-only, and informative claim coverage separately.
  An unsupported report must stay in the ledger; it is not zero burden.
- Keep elapsed waiting, elapsed service, payer hours and agency hours distinct.
  Marginal variance contraction is not total information or causal identification.
- `pipeline/procbench/` currently contains process inference and its benchmark;
  the older top-level `pipeline/` modules include the discretion workstream.
  The planned model/evidence/infra/experiments/legacy/bench layout is not complete.
- Run `python -m pytest tests benchmark/synth/generator/test_generator.py -q`.
  Source-only audit tests must use fakes/cached outputs, never paid network calls.
- Follow `runs/README.md`. Gitignored runs are not backed up by a source commit;
  no external archive or deletion is authorized without a reviewed destination.
