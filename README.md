# regulatory-complexity

Measure what a rule costs the people subject to it, and find drafting changes that cut that cost while
changing outcomes for as few people as possible. Stanford RegLab: Alexander Spangher, Dan Ho, Sanmi Koyejo;
the rule-following work is with Isabel.

**Start here:** `docs/CURRENT_STATUS.md` (what is running, what is done, what is next) and
`docs/CORE_GOAL.md` (the goal and the estimands). `CLAUDE.md` holds the working rules for agents.
The former README, a running log of results through September 2026, is `docs/project-history.md`.

## Three research threads

| Thread | Question | Code | Key docs |
|---|---|---|---|
| **Process and burden models** (Solar and ADU permitting) | How many steps, how long and how costly is a permit process, with calibrated uncertainty, from forum reports, admin records and agency documents? | `pipeline/procbench/` | `docs/2026-10-05-calibrated-decision-tree-posterior-plan.md`, `docs/2026-10-02-solar-adu-process-refit.md` |
| **Synthetic benchmark** | Can the models recover planted statutes, processes and burdens from rendered evidence? | `benchmark/synth/`, `pipeline/procbench/toy_statute/` | `benchmark/synth/DESIGN.md`, `docs/2026-09-26-toy-statute-plan.md` |
| **Rules, readings and loopholes** (letter versus spirit) | Which readings does a rule's text admit, which do agents act on, and how do definitions change the loophole surface? | `benchmark/rulegap/` | `benchmark/rulegap/README.md`, `docs/2026-11-10-rule-following-experiment-plan.md` |

## Layout

| Path | What it holds |
|---|---|
| `pipeline/` | Original compile-side stack: `run.py` (compile a rule into decision trees), `executor.py`, `metrics.py`, `divergence.py`, `simplify.py`; looseness instrument (`instrument.py`, `looseness.py`, `worlds.py`, `screener.py`); `llm.py` (Codex, GLM or Anthropic backends); `prompts/`, `schemas/` |
| `pipeline/procbench/` | Process inference. By prefix: `bayes_*` and `run_*` fit models; `audit_*`, `check_*` and `validate_*` test them; `compare_*` and `summarize_*` report; `import_*` load admin data; `web.py`, `solve.py` run agents. Subpackages: `toy_statute/` (full-chain toy model and SMC fitter), `solar_panel/`, `adu_panel/`, `process_structure/`, `infra/` (Codex runner, Gemma launcher, run manifests). See `pipeline/procbench/README.md` |
| `pipeline/recon/` | Real-data reconnaissance: HCD APR permit timing, county covariates, Reddit fetch, coverage |
| `pipeline/priors/` | Burden priors from structured observations |
| `benchmark/synth/` | Synthetic world generator (`generator/`), LLM rendering of evidence (`render/`), schemas, briefs, style guides. `worlds/_fixture/` is the only world kept in git |
| `benchmark/realworld/` | Real-world benchmark tasks and gold |
| `benchmark/rulegap/` | Rule specs, readings as code, loophole search, complexity metrics, agent harness, red-team and agent studies, question-asking interpreter |
| `benchmark/MANIFEST.md` | Third-party statute-to-code sources and how to reclone them into `benchmark/sources/` (gitignored) |
| `dashboard/` | Inspection dashboard: `template.html` and `build.py`; `data/` holds its inputs |
| `docs/` | Plans, results, audits (dated `YYYY-MM-DD-...`), living design docs (undated), `meetings/`, `html/` |
| `research_notes/`, `reports/` | Literature reviews and their notes |
| `scripts/oneoff/` | One-off build scripts kept for provenance |
| `tests/` | Pytest suite |
| `worlds/` | Latent-world spec for the first priced word ("adequate sanitation") |

## Data (not in git)

Code is in git; data is not. Everything below lives in the private Hugging Face dataset
`alex2awesome/regulatory-complexity-data`, one `.tar.gz` per top-level folder at the same path, plus the
working copies on the RegLab servers (`/dfs/scratch0/alexspan/` on sk2 and sk3). `scripts/archive_to_hf.py`
uploads (`push`) and unpacks (`restore`) it.

| Path | What it holds |
|---|---|
| `corpus/` | Gathered sources: statute texts, county records (HCD APR tables, grand jury reports, CalFresh, permit portals), process pages for nine real-world programs, forum pulls |
| `benchmark/synth/worlds/` | Generated synthetic worlds (evidence, renders and truth) |
| `runs/` | Every run: inputs, model transcripts, parses, fits and results (`runs/README.md` explains the layout) |
| `scratch/` | Data collected on the servers: Solar and ADU forum censuses, procurement exports (SCPRS, CSCR), admin data |

Many tests read `runs/` or `corpus/`, so pull the dataset before running the full suite:

```sh
hf download alex2awesome/regulatory-complexity-data --repo-type dataset --local-dir data_download
python scripts/archive_to_hf.py restore data_download   # then move corpus/, runs/ ... into the repo root
```

## Setup

```sh
pip install -r requirements.txt            # core
pip install -r requirements-bayes.txt      # process fits
pip install -r requirements-rulegap.txt    # rule-following work
python -m pytest tests benchmark/synth/generator/test_generator.py -q
```

LLM stages call the `codex` and `claude` command-line tools by default (no API keys in the repo). Long
jobs run on sk2 and sk3; see `docs/gemma-runbook.md` for the local Gemma 4 31B model.

## Conventions

- Dated docs for plans, results and audits; undated docs are living design notes.
- One results doc per task. Status goes in `docs/CURRENT_STATUS.md`.
- Failures are kept and reported, never silently rerun.
- Fitters and extractors never read benchmark truth, generator specs or gold sources.
