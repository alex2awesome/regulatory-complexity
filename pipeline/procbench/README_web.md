# procbench mock web + solver harness

The retrieval half of Benchmark 2 (`benchmark/synth/DESIGN.md`). `web.py` turns a world's
rendered artifacts into a closed, searchable web; `solve.py` is the model-under-test loop over
it; `run_bench.py` sweeps tasks × information conditions × k and hands each run to the scorer
(`score.py`, documented in `README.md`).

Nothing here needs the network except the model call itself, and everything is stdlib
(BM25 is ~40 lines in `web.py`).

```
python3 pipeline/procbench/web.py --world W1 build              # artifacts/ + specs/ -> web/
python3 pipeline/procbench/web.py --world W1 search "unit legalization Halvern"
python3 pipeline/procbench/solve.py --world W1 --task W1__J2__S03 --condition search \
        --run-id r01 --backend glm                              # -> runs/r01/pred.json
python3 pipeline/procbench/run_bench.py --world W1 --dry-run     # the grid it would run
```

## Inputs and outputs

`build` reads `benchmark/synth/worlds/<W>/artifacts/*.md` (front matter `url, kind, title, date,
jur`, plus `subreddit`/`thread_id` for reddit; reddit comments as
`--- comment by u_xxx (score N, date) ---` blocks) joined by `artifact_id` to
`specs/<artifact_id>.json` (`kind, url, target, jur, stat_id, links_to, date, stale, audience`).
Spec fields win; a missing spec falls back to the front matter with `target: true`. It writes:

| file | one row per | fields |
|---|---|---|
| `web/pages.jsonl` | non-reddit artifact | id, url, kind, title, date, jur, stat_id, target, published, stale, links, text |
| `web/reddit.jsonl` | reddit/forum thread | the same plus subreddit, thread_id |
| `web/links.jsonl` | edge | from_id, from_url, to_url, to_id |
| `web/bm25.json` | — | df, per-doc term frequencies, doc lengths, avgdl |

Outgoing links are the spec's `links_to` **plus** any in-world url that appears in the artifact's
text, so one-hop link following works even when a spec omits them. The index is rebuilt
automatically if `web/pages.jsonl` is missing; rerun `build` after re-rendering artifacts.

Solver runs land in `runs/<run_id>/` (override with `--runs-root`, or `$PROCBENCH_RUNS_ROOT`;
`runs/` is not meant to be committed): `pred.json`, `transcript.json`, `meta.json`,
`trace.jsonl`, and `score.json` + `alignment.json` once scored.

## CLI

```
web.py --world W [--worlds-root DIR] [--condition C] [--run-id ID] [--runs-root DIR] [--json]
   build
   search "<query>" [--k 10]
   fetch <url> [--max-chars 12000]
   reddit search "<query>" [--sub r/Halvern] [--k 10]
   reddit thread <thread_id>
```

Global flags come before the subcommand (`--json` is accepted on either side). `search` covers
pages **and** threads and returns url, title, kind, date, snippet, artifact_id, score;
`reddit search` restricts to threads. An unknown or hidden url returns a 404-like message
instead of text, which is itself information for the solver (record it in `unknowns`).
`--world` also accepts a path to a world directory.

Python API — `solve.py` imports this rather than shelling out:

```python
from pipeline.procbench import web
w = web.World("W1", condition="declared_only", run_id="r01")
w.search(q, k=8, reddit_only=False, sub=None); w.fetch(url, max_chars); w.thread(tid)
w.oracle_docs(jur, stat_id, query, budget_chars, include_distractors)   # -> [doc dicts]
```

## Information conditions

The filter is computed from the spec's `kind` + `target`, and applies to search **and** fetch
(hiding a document means its url 404s, not merely that it ranks low).

| condition | mode | hidden | isolates (plan §1) |
|---|---|---|---|
| `search` | agent | nothing public; an unpublished `sop` stays staff-only | retrieval + everything downstream |
| `declared_plus_users` | agent | `staff_report`, `sop`, `audit_excerpt` | availability of the *designed* tier |
| `declared_only` | agent | the above plus `reddit_thread`, `forum_thread`, `news`, `council_minutes` | availability of *observed* evidence (timing) |
| `oracle_docs` | oracle | nothing; every target doc is handed over, mixed with distractors | reconciliation + disentanglement (retrieval removed) |
| `oracle_no_distractors` | oracle | every non-target artifact | reconciliation alone |

An `sop` counts as published when its spec says `published: true` or its `audience` is
public/applicant/council — the `p_publish_sop` knob decides whether it leaks at all.
"Target" is the spec's own flag; `oracle_docs` additionally treats *other* jurisdictions' and
programs' artifacts as contamination rather than as task documents, so the same artifact can be
a target for its own task and a distractor for this one.

## Trace format

Every web call appends one line to `runs/<run_id>/trace.jsonl` when a run id is set
(`--run-id`, or `$PROCBENCH_RUN`, which lets a manual/subagent solver be traced without passing
flags):

```json
{"ts": "2026-09-15T14:53:59", "condition": "search", "op": "search",
 "args": {"query": "unit legalization Halvern", "k": 10, "sub": null},
 "result_ids": ["J1__S03__program_page", "J1__S03__faq"]}
```

`op` ∈ `search | reddit_search | fetch | reddit_thread | oracle_docs`; `result_ids` are
artifact ids (empty on a 404), so retrieval can be scored separately from modelling: precision
and recall against each task's target artifact set, and how many queries it took.

## Solver

`solve.py --mode` defaults to `oracle` for the two oracle conditions and `agent` otherwise.

- **oracle** — one `llm_json` call. Documents are ordered target-first, then contamination by
  BM25 against the task prompt, up to `--budget-chars` (default 120k ≈ 30k tokens). Prompt:
  `prompts/solve_oracle.md`.
- **agent** — a ReAct loop of at most `--max-steps` (default 12) single-call steps, each returning
  one JSON object: `{"op": "search"|"fetch"|"reddit_search"|"reddit_thread", "args": {…}}` or
  `{"op": "finish", "model": {…}}`. The harness executes the tool, appends a truncated
  observation (`--obs-chars`, older steps shrink further) and re-sends the transcript; the last
  step is told to finish. A malformed op returns an error observation instead of aborting.
  Prompt: `prompts/solve_agent.md`.
- **manual** — prints, and writes `runs/<run_id>/TASK.md`, the task prompt plus the exact shell
  commands for this world and condition. Use it when the solver is a human or a Claude subagent:
  give the subagent `TASK.md`, let it shell out to `web.py` (its calls are traced like any
  other), and have it write `runs/<run_id>/pred.json` itself.

The predicted model asked for in both prompts is `pipeline/schemas/process_model.schema.json`
plus, per activity, `visibility` (`applicant_facing|applicant_inferable|staff_only`),
`timing {median_days, range, basis}`, `fee {amount, when}`, `rework {p_trigger, back_to, reason}`,
`confidence` 0–1, `evidence` (urls/thread ids), and at top level `process_timing`, `denial_rate`,
`unknowns [{what, why_unknown}]`. `pred.json` is that model with `task_id`, `condition`,
`schema_errors` and a `procbench` metadata block added — a scorer can read it as a process model
directly. Both prompts demand the skepticism the benchmark grades: contamination from other
jurisdictions/programs, staleness (dates, superseded fees and departments), complaint-selection
bias in reddit timing, and no invented steps (they go in `unknowns`).

## Sweeping

```
python3 pipeline/procbench/run_bench.py --world W1 [--tasks J2,J3] [--conditions search,oracle_docs] \
        [--k 3] [--backend codex|glm|anthropic] [--align offline|llm] [--dry-run] [--no-score]
```

Each task's own `conditions` list is used unless `--conditions` overrides it. Per run it calls
`solve.solve`, then `score.py --pred … --gold truth/processes/<jur>__<stat>.json` with
`--ceiling ceiling.json --task … --statute … --distractors <every other gold>` when those files
exist (a missing gold is reported, not fatal; override the whole invocation with `--score-cmd`).
`runs/summary.json` holds one row per run (finished, seconds, steps, score, score_error),
per-condition means of every numeric score field, and `score.py aggregate`'s own roll-up under
`aggregate`. **Codex is minutes per call** — `--dry-run` first, and keep `k` small.

## Plugging in a different model

1. A supported backend: `--backend codex|glm|anthropic [--model …]` (see `pipeline/llm.py`;
   env `RC_LLM_BACKEND` / `RC_LLM_MODEL` work too). `--k` repeats a run for reliability.
2. Another API: add a `_call_*` branch in `pipeline/llm.py` — everything here goes through
   `llm.llm_json(prompt_file, body, extra=…)`, so nothing else changes.
3. An agent you cannot drive programmatically (a hosted agent, another CLI, a Claude subagent):
   use `--mode manual`. The contract is exactly the four `web.py` commands plus a `pred.json`.
   Set `PROCBENCH_RUN=<run_id>` in its environment to get the same trace as an in-process run.

## Fixture world and tests

`benchmark/synth/worlds/_fixture/` is a hand-written world (not generated): 12 artifacts —
9 targets for two tasks (Halvern and Ardenmoor unpermitted-unit programs under the same statute)
including 2 reddit threads, plus 3 distractors (a same-city vending program, another city's
vending FAQ, and the surrounding county's look-alike program under the *same* statute). It plants
what the benchmark is meant to measure: a stale FAQ (old fee, old department), a staff report
that is the only source for four back-office steps, an insider comment, a wrong fee in a comment,
a complaint-selected 98-day timeline against a 47-day gold median, and cross-jurisdiction
contamination in both threads. It has no `truth/` or `ceiling.json` — those belong to the
generator.

`python3 tests/test_procbench_web.py` builds it and checks search/fetch/reddit, the condition
filters, the oracle document sets, the trace lines, and a full agent run against a fake backend
(`pipeline.llm.llm_json` monkeypatched with a canned tool call sequence then a finish). No LLM,
no network.
