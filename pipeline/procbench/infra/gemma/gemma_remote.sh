#!/bin/bash
# Launch / monitor / fetch local-open-model batch jobs on sk2. See docs/gemma-runbook.md.
#
#   gemma_remote.sh gpus                         show sk2 GPUs and which are free
#   gemma_remote.sh run   <input.jsonl> <job> [gemma_batch.py args...]
#   gemma_remote.sh status <job>
#   gemma_remote.sh fetch  <job> <local_dir>
#
# Every rule below was learned by breaking it:
#  * sk2's HOME is on AFS and NOT writable: vLLM/Triton/torch caches must point at local
#    disk or the engine dies at startup ("Engine core initialization failed").
#  * ssh must be wrapped in `timeout` with stdin from /dev/null, or a remote background
#    job holds the connection open and the local call hangs.
#  * `&` in a remote compound command breaks the `cd` chain: use absolute paths only.
#  * `pgrep -f PATTERN` inside a remote shell matches that shell itself (its command line
#    contains PATTERN). Bracket one character -- [g]emma -- so it only matches the real job.
#  * shared cluster: use a GPU only if it is free, never start a duplicate job, and do not
#    leave a long-running server holding a GPU without asking the owner.
set -euo pipefail
HOST=${GEMMA_HOST:-sk2}
PY=/lfs/skampere2/0/alexspan/envs/gemma4/bin/python3.11
MODEL=${GEMMA_MODEL:-/lfs/skampere2/0/alexspan/models/gemma-4-31b-it}
JOBS=/dfs/scratch0/alexspan/gemma_jobs
CACHE=/lfs/skampere2/0/alexspan/.cache_vllm
# GEMMA_GPU=<index> pins one GPU (still refused unless free). Use it when launching two jobs
# back to back: a job that is still loading its weights looks free for about a minute.
MAXUSED_MIB=${GEMMA_MAX_USED_MIB:-2000}      # a GPU with more memory in use than this is "busy"
HERE="$(cd "$(dirname "$0")" && pwd)"
# Own connection per call: a shared ControlMaster socket (other sessions use sk2 too) broke
# repeatedly with "mux_client_request_session: Broken pipe" and hung scp/ssh.
# The jump hop (whale) needs the same treatment, or its stale socket breaks the connection
# ("mux_client_request_stdio_fwd: Broken pipe"). Override with GEMMA_PROXY="" to use ssh config.
PROXY=${GEMMA_PROXY-"ssh -4 -o BatchMode=yes -o ControlMaster=no -o ControlPath=none -W %h:%p whale"}
SSHO=(-o BatchMode=yes -o ConnectTimeout=20 -o ControlMaster=no -o ControlPath=none)
[ -n "$PROXY" ] && SSHO+=(-o "ProxyCommand=$PROXY")
R() { timeout "${2:-60}" ssh "${SSHO[@]}" "$HOST" "$1" < /dev/null 2> >(grep -v "chdir\|bashrc" >&2); }

case "${1:-}" in
gpus)
  R "nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader" \
    | awk -F', ' -v m="$MAXUSED_MIB" '{u=$2+0; printf "GPU %s  used %6s MiB  util %4s  %s\n",$1,u,$4,(u<m?"FREE":"busy")}' ;;
run)
  IN="$2"; JOB="$3"; shift 3
  [ -f "$IN" ] || { echo "no input $IN"; exit 2; }
  if R "pgrep -f '[g]emma_batch.py.*$JOBS/$JOB/' >/dev/null" 30; then echo "job $JOB is already running; not starting a duplicate"; exit 3; fi
  GPU=$(R "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits" \
        | awk -F', ' -v m="$MAXUSED_MIB" -v want="${GEMMA_GPU:-}" '!g && (want=="" || $1+0==want+0) && $2+0<m && $3+0<5 {print $1; g=1}')  # no early exit: SIGPIPE+pipefail aborted silently
  [ -n "$GPU" ] || { echo "no free GPU on $HOST right now; not launching"; exit 4; }
  R "mkdir -p $JOBS/$JOB $CACHE" 30
  timeout 300 scp -q "${SSHO[@]}" "$IN" "$HOST:$JOBS/$JOB/input.jsonl"
  timeout 60 scp -q "${SSHO[@]}" "$HERE/gemma_batch.py" "$HOST:$JOBS/$JOB/gemma_batch.py"
  R "CUDA_VISIBLE_DEVICES=$GPU VLLM_USE_FLASHINFER_SAMPLER=0 XDG_CACHE_HOME=$CACHE VLLM_CACHE_ROOT=$CACHE/vllm TRITON_CACHE_DIR=$CACHE/triton \
     TORCHINDUCTOR_CACHE_DIR=$CACHE/inductor HF_HOME=$CACHE/hf \
     setsid nohup $PY $JOBS/$JOB/gemma_batch.py --model $MODEL --input $JOBS/$JOB/input.jsonl \
       --output $JOBS/$JOB/output.jsonl $* > $JOBS/$JOB/run.log 2>&1 < /dev/null &
     sleep 2; echo launched job=$JOB gpu=$GPU" 30 ;;
status)
  JOB="$2"
  R "if grep -qE '^(DONE|INCOMPLETE)' $JOBS/$JOB/run.log 2>/dev/null; then grep -E '^(DONE|INCOMPLETE)' $JOBS/$JOB/run.log;
     elif pgrep -f '[g]emma_batch.py.*$JOBS/$JOB/' >/dev/null; then echo RUNNING; tail -1 $JOBS/$JOB/run.log | cut -c1-160;
     else echo 'NOT RUNNING (failed?)'; grep -iE 'error|traceback|out of memory' $JOBS/$JOB/run.log | tail -5; fi" 30 ;;
fetch)
  JOB="$2"; OUT="$3"; mkdir -p "$OUT"
  timeout 600 scp -q "${SSHO[@]}" "$HOST:$JOBS/$JOB/output.jsonl" "$HOST:$JOBS/$JOB/output.jsonl.meta.json" "$HOST:$JOBS/$JOB/run.log" "$OUT/"
  echo "fetched to $OUT"; cat "$OUT/output.jsonl.meta.json" ;;
*) sed -n '2,8p' "$0"; exit 1 ;;
esac
