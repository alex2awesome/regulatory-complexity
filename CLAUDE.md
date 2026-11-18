# Project working conventions

Standing rules only. Current status lives in `docs/CURRENT_STATUS.md`; the full history of dated
checkpoints (through 2026-09-29) is in `docs/2026-09-29-claude-md-checkpoint-archive.md`.
**Never append status or checkpoints to this file** -- update `docs/CURRENT_STATUS.md` instead.

## How to work (Alex, 2026-09-29)
- Every task has a deliverable, a definition of done, and a budget. When done: report and stop.
- Verification = one scripted mechanical check per artifact, at creation. Do not re-verify,
  re-audit or re-derive anything already checked unless Alex asks. No verification campaigns.
- When something is ambiguous, pick the conservative default, record it as one line in the task's
  ASSUMPTIONS / notes, and keep going. Do not open a proposal, erratum or hold for it.
- No successor sprawl: overwrite your own working files; keep originals only of inherited or
  already-reported artifacts. One results doc per task.
- Measure progress by what reaches a model or result table (claims fitted, estimates produced),
  not by receipts, hashes or reviewed-item counts.
- Report failures plainly and keep them; do not silently extend or rerun exhausted attempts.

## Ownership
- Claude (ADU session): acquisition -- the ONLY Arctic Shift API caller, from sk3 -- and Gemma
  triage. Codex: parsing/reading and Bayesian modeling for Solar and ADU. Handoffs:
  `docs/2026-09-29-solar-parsing-handoff-for-codex.md`, `docs/2026-09-29-adu-parsing-handoff-for-codex.md`.
- Priority: real corpora first (Solar, ADU; CalFresh/CCW work is parked). Synthetic work deferred.
- Cost routing: routine parsing and checks on GPT-5.6 Luna/Sol, not Astra; Astra only for model
  design and consequential ambiguity. High-volume closed-codebook labeling and triage: Gemma 4 31B on
  sk2 (`docs/gemma-runbook.md`; replay-verify any quote Gemma produces; offline batch jobs only).

## Hard rules
- Do not commit, stage broad directories, delete files, or move packages without Alex's approval.
  Preserve unrelated user changes. No outreach, logins, CAPTCHA/paywall/bot-protection bypass.
- Extractors and fitters must not read benchmark `truth/`, generator specs, scores,
  `corpus/realworld/**/sources.json` or any `process_draft.json`. Calibration never reads reserved labels.
- Quotes in evidence are sliced programmatically from retained source bytes and replay exactly;
  a quote must also be real text (junk screen).
- Follow `runs/README.md`. Gitignored runs are not backed up by a commit; no external archive or
  deletion without a reviewed destination. Run long jobs on sk2/sk3 scratch
  (`/dfs/scratch0/alexspan`), not the laptop.

## Modeling conventions
- Read `README.md` and `docs/2026-09-16-bayesian-audit-implementation.md` before process-model work.
  V6 is the integration target; V3–V5 are historical controls.
- Date plans/results/audits `YYYY-MM-DD-...`; living design docs undated.
- Keep elapsed waiting, elapsed service, payer hours and agency hours distinct. An unsupported
  report stays in the ledger; it is not zero burden. Unknown geography or a missing department
  name is not an exclusion rule.
- Source heterogeneity is not one trust score (bias, precision, contamination, selection differ).
  Convergence is not identification; marginal contraction is not causal identification.
- `pipeline/procbench/` holds process inference; shared helpers in `procbench/infra/`.
  Tests: `python -m pytest tests benchmark/synth/generator/test_generator.py -q` (no paid network
  calls in tests).
