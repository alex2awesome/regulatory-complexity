# Gemma runbook: running a local open model for cheap bulk LLM work

How any process in this project (a Claude or Codex session, an agent, a script)
can send high-volume, low-judgment LLM work to a local open model instead of a
frontier API, and when it should not.

The short version: **use Gemma for triage and closed-codebook classification;
keep frontier models for extraction and anything needing judgment; verify
everything Gemma produces mechanically.**

## What is available

| | |
|---|---|
| Model | **Gemma 4 31B-it**, `/lfs/skampere2/0/alexspan/models/gemma-4-31b-it` (59 GB, bf16, 2 shards, complete) |
| Note, 2026-11-11 | That sk2 path is gone. Complete copies: sk3 `/lfs/skampere3/0/alexspan/models/gemma-4-31b-it` (env `/lfs/skampere3/0/alexspan/envs/gemma4`) and sk2 `/lfs/skampere2/0/alexspan/norm-research-silver-v3/models/gemma-4-31b-it-3548789868c5356dbf307c98e6f609007b82b3eb-mirror-v1`. Set `GEMMA_MODEL` for the launcher. |
| Host | **sk2**, 8x NVIDIA H200 (141 GB each). A 31B model fits on one GPU. |
| Serving | vLLM 0.23.0 in `/lfs/skampere2/0/alexspan/envs/gemma4/bin/python3.11` (torch 2.11, CUDA OK) |
| Job files | `/dfs/scratch0/alexspan/gemma_jobs/<job>/` (NFS scratch, visible from sk2 and sk3) |
| Tools | `pipeline/procbench/infra/gemma/gemma_remote.sh` (launcher) and `gemma_batch.py` (runs on sk2) |

Not available: **Llama 3.3 70B** (only a broken 12/15-shard FP8 mirror exists; a
real copy needs an HF token with Meta's license accepted, ~140 GB). **sk3's B200s**
are normally full. No hosted open-model API keys are configured.

## Quick start

```bash
G=pipeline/procbench/infra/gemma/gemma_remote.sh
$G gpus                                  # which sk2 GPUs are free right now
$G run my_input.jsonl my_job_20260923    # picks a free GPU, uploads, launches
$G status my_job_20260923                # RUNNING / DONE {...} / NOT RUNNING + errors
$G fetch my_job_20260923 ./my_results/   # output.jsonl, .meta.json, run.log
```

Extra arguments after the job name go to `gemma_batch.py`, for example
`--max-tokens 4096`, `--max-model-len 65536`, `--temperature 0.2`, `--tp 2`.

### Input format (JSONL, one task per line)

```json
{"id": "task-001",
 "messages": [{"role": "system", "content": "instructions..."},
              {"role": "user", "content": "the item to process"}],
 "max_tokens": 512}
```

`max_tokens` is optional per line. System messages are folded into the first
user turn automatically, because Gemma chat templates do not reliably accept a
system role.

### Output format

`output.jsonl`, one line per input, same order:

```json
{"id": "task-001", "text": "<raw reply>", "prompt_tokens": 812, "gen_tokens": 40,
 "finish_reason": "stop", "json": {...parsed first JSON object, or null...}}
```

plus `output.jsonl.meta.json` with timing, token totals, `truncated_at_max_tokens`
and `unparseable_json`. **Check both counts before using the results**: a
`finish_reason` of `length` means the answer was cut off, and `json: null` means
the reply had no parseable JSON (code fences are already stripped).

## Throughput

Measured on one H200 at temperature 0: **220 prompts, 376k prompt tokens and 17.5k
generated tokens in 53.5 s**, after about 3 minutes of model loading. A 3-prompt
job took 5.7 s of inference. Load time dominates small jobs, so **batch work into
one job** rather than launching many small ones.

It costs no API usage at all. On a day when frontier agents burned through session
and weekly limits, this is the point.

## What it is good for: measured, not assumed

Smoke test against existing frontier outputs (`runs/open_model_smoketest_20260923/`,
`RESULTS.md` there has the detail):

| task | Gemma | frontier-vs-frontier ceiling | use it? |
|---|---|---|---|
| **Closed-codebook classification** (HCD letter findings, 120 items) | 85.6% same primary category as the first frontier coder (kappa 0.845); 97.5% pre-submittal flag; 100% ADU scope | 90.1% (kappa 0.894) between two blind frontier coders | **yes** |
| **Triage / relevance screening** (80 Reddit threads) | recall 92.5%, precision 84% (understated: only 3 of 7 "false positives" were wrong on adjudication) | not measured | **yes, as a high-recall pre-filter** |
| **Structured extraction with quotes** (20 threads) | finds 63% of the first frontier coder's action ids; 2 of 48 quotes not in the source | a second frontier coder also finds 63%; 44 of 44 quotes replay | **no, not as a replacement** |

Frontier labels are not ground truth. The "ceiling" column is a blind second
frontier pass on the same items; see the last section for the adjudication.

Where Gemma falls short on extraction: it under-reports agency-side acts (plan
check, corrections, permit issuance, certificate of occupancy) and loses
multi-step narratives. Its triage misses are threads whose only relevant content
is a commenter buried in an off-topic discussion.

### Production use: ADU thread triage + span locating (2026-09-24)

Gemma screened 4,629 new Reddit threads in 31 minutes on one GPU and listed, per
thread, the comments that hold evidence (citing the `[$.path]` labels shown in
the prompt). Checked on 617 threads frontier coders had already coded: **96.9%
thread recall**; showing coders only short threads whole plus Gemma-selected
excerpts of long threads kept **97.1% of the paths frontier coders quoted at 59%
of the text**. Net: frontier coders read 5.5M characters instead of 24.8M. Code,
prompt and numbers: `runs/adu_gemma_triage_20260924/`. This pattern (Gemma
locates, frontier codes from the raw source, a verifier replays quotes) is the
recommended way to cut frontier reading tokens on large corpora.

### Recommended division of labour

1. **Gemma pre-filters** the pool (high recall, drops about half the volume).
2. **Gemma does closed-codebook classification** where the label set is fixed.
3. **Frontier models do extraction, adjudication, provenance and design**, on
   the filtered set only.

## Rules that are not optional

- **Verify everything mechanically.** In the smoke test Gemma produced 2 quotes
  that do not exist in the source. Any quote Gemma extracts must be replayed
  against the source before it is used. The project verifiers (quote replay plus
  junk screen) catch this; a Gemma output that skips them is not evidence.
- **Treat Gemma's JSON as untrusted input.** Validate field names and enum values
  against your schema; drop or flag anything that doesn't conform.
- **Measure before you switch a task over.** Agreement on one task says nothing
  about another. Run Gemma and the current model on the same ~50 items, compare,
  and look at the disagreements before routing a new task type to Gemma.
- **Keep extractors blind to truth.** The project rule that extractors and fitters
  never read benchmark `truth/`, generator specs or scores applies to Gemma jobs
  exactly as to any other model.

## Operational gotchas (each one broke a real run)

- **sk2's HOME is on AFS and is not writable.** vLLM, Triton and the torch compiler
  write caches under HOME, and the engine dies at startup with `Engine core
  initialization failed` / `Permission denied: /afs/.../.cache/vllm`. The launcher
  points every cache at `/lfs/skampere2/0/alexspan/.cache_vllm`. If you run
  `gemma_batch.py` by hand, set `XDG_CACHE_HOME`, `VLLM_CACHE_ROOT`,
  `TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR` and `HF_HOME` yourself.
  The September 29 launcher preserves the user's `HOME`; dedicated cache
  variables provide writable locations without repurposing a home directory.
- **Wrap ssh in `timeout` with stdin from `/dev/null`.** A job backgrounded on the
  remote side otherwise holds the connection open and the local call hangs.
- **`&` breaks a remote `cd` chain.** The background part runs in a subshell, so
  later commands run in the (unwritable) home directory. Use absolute paths.
- **`pgrep -f PATTERN` inside a remote shell matches that shell itself**, because
  the shell's command line contains PATTERN. That made the launcher think every
  job was already running. Bracket one character (`[g]emma_batch.py`).
- **Gemma copies label brackets.** Asked to cite a label shown as `[$.post.selftext]`,
  it returned the brackets in 1,553 of 3,619 items. An exact-match validator then
  silently dropped them and recall read as 52.5% instead of 96.9%. Normalize
  obvious formatting before matching, and always count what the validator rejects.
- **Two jobs launched back to back can land on the same GPU**, because a job still
  loading weights looks free. Pin with `GEMMA_GPU=<index>`.
- **`/lfs/skampere3/0` fills up without warning** (shared 84 TB volume). Job files
  live on `/dfs/scratch0`, and the batch runner writes output atomically, so a
  killed or full-disk run never leaves a truncated file.

- **FlashInfer sampler JIT can fail to link (`ld: cannot find -lcuda`).** On 2026-09-24 the cached
  `flashinfer/.../cached_ops/sampling` build was invalidated and every job died at engine start
  (`Engine core initialization failed`, `Ninja build failed`). The launcher now sets
  `VLLM_USE_FLASHINFER_SAMPLER=0` (PyTorch-native sampler; no JIT; greedy decoding is unaffected).
  Also: `/lfs/skampere2/0` was at 100% that day.

- **`run` exited silently with no "launched" line (2026-09-24).** The GPU picker's `awk ... {print; exit}`
  closed the pipe early; under `set -euo pipefail` the SIGPIPE on ssh aborted the script right after
  choosing a GPU whenever the free GPU was not the last one listed. Fixed in `gemma_remote.sh` (awk reads
  all lines; backup `gemma_remote.before_sigpipe_fix.sh`). If `run` prints nothing, the job did not start.

## Shared-cluster etiquette

sk2 is shared. The launcher only uses a GPU with under 2 GB in use and under 5%
utilization, and refuses to start a duplicate of a live job. **Prefer offline
batch jobs.** Do not leave a long-running vLLM server holding a GPU without
checking with Alex first. If you genuinely need a server (many small interactive
calls), start one with `vllm serve` on a free GPU with the same cache
environment, note it in the project status file, and shut it down when done.

## Adding another model

Put the weights on sk2 local disk or `/dfs/scratch0`, confirm every shard in
`model.safetensors.index.json` is present (the Llama mirror is a warning), then
run with `GEMMA_MODEL=/path/to/model $G run ...`. Re-run the smoke test
(`runs/open_model_smoketest_20260923/build_inputs.py` then `score.py <tag>`)
before trusting it on any task.

## Noise ceiling and adjudication

From `runs/open_model_smoketest_20260923/RESULTS.md` (`compare.py`,
`adjudication.json`). A blind second frontier coder recoded tasks A and C; a
separate frontier adjudicator judged each Gemma-vs-frontier disagreement against
the source.

- **Classification:** Gemma is 3–4 points below frontier-vs-frontier agreement on
  primary category. 18 of 22 disagreements were judged both defensible (the
  codebook lists some topics under two categories); 4 were Gemma errors, all on
  is_finding (it counts typo fixes, "please review this memo" and bare lists of new
  bills as findings). If you use it here, tighten the is_finding definition in the
  prompt with those negative examples.
- **Triage:** of 10 disagreements, 3 were Gemma errors, 3 were gold errors, 4 were
  both defensible. The misses are threads whose only relevant content is one
  commenter in an off-topic discussion. Keep the threshold recall-oriented.
- **Extraction:** Gemma's raw recall looked worse than it is: a second frontier
  coder recovers exactly the same share of the first coder's action ids. But of 27
  adjudicated action ids, 14 went to the frontier coder and 6 to Gemma. Gemma misses
  stated agency acts (a permit issued, city-required changes), dropped one episode
  entirely, coded a non-ADU project, and was the only coder to produce quotes that
  are not in the source.

Bottom line: Gemma is close to frontier consistency for fixed-codebook
classification and triage; frontier models are still better at extraction, and
nothing Gemma extracts is usable without replay verification.
