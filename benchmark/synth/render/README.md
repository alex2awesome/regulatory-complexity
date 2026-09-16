# Rendering and verification waves

1. `python3 benchmark/synth/render/batches.py --world W1` → `batches/<id>.json` (groups T target / D structured distractor / F filler; skips specs already rendered).
2. `python3 benchmark/synth/render/prepare_batch.py --world W1 --batch T00` → `batches/T00.input.json` (one self-contained file per renderer: specs + render_context + states + legal_truth for legal kinds + style-guide paths).
3. Launch one renderer agent per batch with `briefs/render_agent_prompt.md` (substitute {WORLD}/{BATCH}). Order: T (Opus or Sonnet, high fidelity) → D → F (Sonnet/Haiku). Renderers never see truth/.
4. `prepare_batch.py --verify` → `batches/T00.verify_input.json`; launch verifier agents with `briefs/verify_agent_prompt.md` (Opus). Verifiers see hidden-element descriptions.
5. Failed artifacts: re-run `batches.py` after deleting the failed `.md` files (or move them to `artifacts/_rejected/`) — the failed specs re-batch automatically; pass the `fix` strings along.
6. `python3 pipeline/procbench/web.py --world W1 build` → mock web; `run_bench.py` → runs.
Logs: `render_log.jsonl`, `verify_log.jsonl` in the world dir.

Observation-contract update (2026-09-16): renderer batches now remove persona
`true_timeline`, per-step `true_days`, and the internal `total_days_reported` helper.
Renderers receive the intentionally noisy reported phrases; independent verifiers
retain the full spec. Supplied public-law content for legal documents is still
available, but hidden process truth is not. Both briefs now explicitly require
clock, repeat-visit basis, cohort and actor-assignment fidelity, not just matching
numbers. Existing rendered W1 artifacts are unchanged.
