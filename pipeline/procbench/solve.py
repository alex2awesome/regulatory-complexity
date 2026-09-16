#!/usr/bin/env python3
"""Model-under-test loop for the synthetic process benchmark.

  oracle  (oracle_docs / oracle_no_distractors): one llm_json call over the
          permitted documents, BM25-ordered against the task prompt.
  agent   (search / declared_only / declared_plus_users): ReAct loop, one
          llm_json call per step returning a tool call or {"op":"finish", ...}.
  manual  print the task + tool instructions so a human (or a Claude subagent)
          can be the solver by shelling out to web.py.

  python3 pipeline/procbench/solve.py --world _fixture --task _fixture__J1__S03 \
      --condition search --mode agent --run-id r1 --backend glm

Writes runs/<run_id>/{pred.json,transcript.json,meta.json}; web calls also land
in runs/<run_id>/trace.jsonl.
"""

import argparse
import datetime as dt
import json
import pathlib
import sys
import traceback

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipeline import llm                                    # noqa: E402
from pipeline.procbench import web                          # noqa: E402

PROMPTS = pathlib.Path(__file__).parent / "prompts"
ORACLE_CONDITIONS = {"oracle_docs", "oracle_no_distractors"}
MODE_FOR = {c: ("oracle" if c in ORACLE_CONDITIONS else "agent") for c in web.CONDITIONS}
CONDITION_NOTE = {
    "search": "the full public web is reachable",
    "declared_only": "only applicant-facing city documents are reachable; no reddit, news, or staff documents",
    "declared_plus_users": "city documents and user reports are reachable; no staff/council/audit documents",
    "oracle_docs": "every relevant document was handed to you, mixed with documents about other jurisdictions and programs",
    "oracle_no_distractors": "every relevant document was handed to you, and nothing else",
}


def load_task(world_dir, task_id=None, jur=None, stat_id=None, prompt=None):
    tasks = []
    p = pathlib.Path(world_dir) / "tasks.json"
    if p.exists():
        tasks = json.loads(p.read_text())
    for t in tasks:
        if task_id and t.get("task_id") == task_id:
            return t
        if not task_id and jur and t.get("jur") == jur and (not stat_id or t.get("stat_id") == stat_id):
            return t
    if prompt or (jur and stat_id):
        return {"task_id": task_id or f"{jur}__{stat_id}", "jur": jur, "stat_id": stat_id,
                "prompt": prompt or f"Construct the process model and expected timeline for {stat_id} in {jur}."}
    raise SystemExit(f"task not found in {p} (have: {[t.get('task_id') for t in tasks]}); "
                     f"pass --task, or --jur/--stat-id/--prompt")


def task_block(task, condition, extra=""):
    return (f"TASK: {task['prompt']}\n"
            f"target jurisdiction: {task.get('jur')}   target statute: {task.get('stat_id')}\n"
            f"model_id to use: {task.get('task_id')}\n"
            f"information condition: {condition} — {CONDITION_NOTE.get(condition, '')}\n" + extra)


def render_docs(docs):
    out = []
    for i, d in enumerate(docs, 1):
        head = (f"=== DOCUMENT {i} === url: {d['url']} | kind: {d['kind']} | date: {d['date'] or 'undated'}"
                + (f" | {d['subreddit']} thread_id: {d['thread_id']}" if d.get("subreddit") else ""))
        out.append(f"{head}\ntitle: {d['title']}\n\n{d['text']}")
    return "\n\n".join(out)


def normalize(model, task, condition):
    if not isinstance(model, dict):
        model = {"activities": [], "notes": f"solver returned {type(model).__name__}"}
    model.setdefault("model_id", task.get("task_id", "pred"))
    model.setdefault("source", "declared")
    model.setdefault("actors", sorted({a.get("actor", "") for a in model.get("activities", []) if a.get("actor")}))
    model.setdefault("activities", [])
    model.setdefault("edges", [])
    model.setdefault("unknowns", [])
    model["task_id"] = task.get("task_id")
    model["condition"] = condition
    return model


def schema_errors(model):
    try:
        import jsonschema
        schema = json.loads((REPO / "pipeline" / "schemas" / "process_model.schema.json").read_text())
        jsonschema.validate(model, schema)
        return []
    except ImportError:
        return []
    except Exception as e:
        return [str(e).splitlines()[0]]


# ------------------------------------------------------------------ oracle mode

def run_oracle(w, task, args):
    docs = w.oracle_docs(task.get("jur"), task.get("stat_id"), query=task["prompt"],
                         budget_chars=args.budget_chars,
                         include_distractors=(args.condition != "oracle_no_distractors"))
    body = render_docs(docs)
    model = llm.llm_json(str(PROMPTS / "solve_oracle.md"), body,
                         schema_file="process_model.schema.json", model=args.model,
                         extra=task_block(task, args.condition,
                                          f"\n{len(docs)} documents follow, most relevant first.\n"),
                         max_tokens=args.max_tokens)
    return model, [{"step": 1, "action": {"op": "oracle_docs", "args": {"n_docs": len(docs)}},
                    "observation": f"{len(docs)} documents, {len(body)} chars: "
                                   + ", ".join(d["url"] for d in docs)}]


# ------------------------------------------------------------------ agent mode

def exec_tool(w, op, a, max_chars):
    a = a if isinstance(a, dict) else {}
    if op == "search":
        return web.render(w.search(str(a.get("query", "")), int(a.get("k", 8) or 8)))
    if op == "fetch":
        return web.render(w.fetch(str(a.get("url", "")), max_chars))
    if op == "reddit_search":
        return web.render(w.search(str(a.get("query", "")), int(a.get("k", 8) or 8),
                                   reddit_only=True, sub=a.get("sub")))
    if op == "reddit_thread":
        return web.render(w.thread(str(a.get("thread_id") or a.get("id", "")), max_chars))
    return (f"error: unknown op {op!r}. Use search | fetch | reddit_search | reddit_thread | finish, "
            f"as one JSON object.")


def render_transcript(transcript, obs_chars):
    if not transcript:
        return "(no steps yet — this is your first action)"
    out = []
    for t in transcript:
        obs = t["observation"]
        cap = obs_chars if t is transcript[-1] else max(600, obs_chars // 4)   # older steps shrink
        out.append(f"--- step {t['step']} action ---\n{json.dumps(t['action'])}\n"
                   f"--- step {t['step']} observation ---\n{obs[:cap]}"
                   + ("\n[observation truncated]" if len(obs) > cap else ""))
    return "\n\n".join(out)


def run_agent(w, task, args):
    transcript, model = [], None
    for step in range(1, args.max_steps + 1):
        last = step == args.max_steps
        extra = task_block(task, args.condition,
                           f"\nstep {step} of {args.max_steps}."
                           + (" THIS IS YOUR LAST STEP: emit {\"op\": \"finish\", \"model\": …} now, "
                              "with whatever you have." if last else ""))
        try:
            act = llm.llm_json(str(PROMPTS / "solve_agent.md"), render_transcript(transcript, args.obs_chars),
                               model=args.model, extra=extra, max_tokens=args.max_tokens)
        except Exception as e:
            transcript.append({"step": step, "action": {"op": "error"},
                               "observation": f"llm call failed: {e}"})
            break
        if not isinstance(act, dict):
            act = {"op": "?", "raw": act}
        if act.get("op") == "finish" or "model" in act:
            model = act.get("model")
            transcript.append({"step": step, "action": {"op": "finish"},
                               "observation": f"finished with {len((model or {}).get('activities', []))} activities"})
            break
        obs = exec_tool(w, act.get("op"), act.get("args"), args.max_chars)
        transcript.append({"step": step, "action": act, "observation": obs})
    return model, transcript


# ------------------------------------------------------------------ manual mode

MANUAL = """# procbench manual solver — run {run_id}

{task}
## Tools (shell out; every call is traced to {run_dir}/trace.jsonl)

    W="python3 {web} --world {world} --condition {condition} --run-id {run_id}"
    $W search "<query>" --k 8
    $W fetch "<url>" --max-chars 12000
    $W reddit search "<query>" [--sub r/Somewhere]
    $W reddit thread "<thread_id>"

Add `--json` to any call for machine-readable output. Fetch only urls that a search result or a
fetched page's `links:` line gave you; unknown urls 404. Some document kinds are hidden in this
condition — that is the experiment, not a bug.

## What to produce

Write `{run_dir}/pred.json`: a process model with `model_id` `{model_id}`, `source: "declared"`,
`jurisdiction`, `actors`, `activities`, `edges`, `terminal_artifact`, `process_timing`, `unknowns`.
Every activity carries `id, name, actor, occasion, visibility, timing {{median_days, range, basis}},
fee, rework, confidence (0-1), evidence (urls you actually read)`. Rework edges count.

The full instructions given to the model-under-test — including the required skepticism about
contamination (other jurisdictions and programs) and staleness — are in
{agent_prompt}. Read them and follow them; they are the task definition.
"""


def run_manual(w, task, args, run_dir):
    text = MANUAL.format(run_id=args.run_id, task=task_block(task, args.condition) + "\n",
                         run_dir=run_dir, web=pathlib.Path(__file__).parent / "web.py",
                         world=w.world, condition=args.condition, model_id=task.get("task_id"),
                         agent_prompt=PROMPTS / "solve_agent.md")
    (run_dir / "TASK.md").write_text(text)
    print(text)
    return None, [{"step": 0, "action": {"op": "manual"}, "observation": f"wrote {run_dir}/TASK.md"}]


# ------------------------------------------------------------------ driver

def solve(args, run_id):
    w = web.World(args.world, args.condition, run_id, args.worlds_root, args.runs_root)
    task = load_task(w.dir, args.task, args.jur, args.stat_id, args.prompt)
    run_dir = w.runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    mode = args.mode or MODE_FOR[args.condition]
    t0 = dt.datetime.now()
    err, model, transcript = None, None, []
    try:
        if mode == "manual":
            model, transcript = run_manual(w, task, args, run_dir)
        elif mode == "oracle":
            model, transcript = run_oracle(w, task, args)
        else:
            model, transcript = run_agent(w, task, args)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    meta = {"run_id": run_id, "world": w.world, "task_id": task.get("task_id"), "condition": args.condition,
            "mode": mode, "backend": llm.model_desc(), "steps": len(transcript),
            "started": t0.isoformat(timespec="seconds"),
            "seconds": round((dt.datetime.now() - t0).total_seconds(), 1), "error": err,
            "finished": model is not None}
    (run_dir / "transcript.json").write_text(json.dumps({"meta": meta, "steps": transcript}, indent=1))
    if model is not None:
        pred = normalize(model, task, args.condition)
        meta["schema_errors"] = pred["schema_errors"] = schema_errors(
            {k: v for k, v in pred.items() if k not in ("task_id", "condition")})
        pred["procbench"] = meta
        (run_dir / "pred.json").write_text(json.dumps(pred, indent=1))
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=1))
    return meta


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True)
    ap.add_argument("--task", default=None, help="task_id from the world's tasks.json")
    ap.add_argument("--jur", default=None); ap.add_argument("--stat-id", default=None)
    ap.add_argument("--prompt", default=None, help="ad-hoc task prompt (bypasses tasks.json)")
    ap.add_argument("--condition", default="search", choices=web.CONDITIONS)
    ap.add_argument("--mode", default=None, choices=["oracle", "agent", "manual"],
                    help="default: oracle for oracle_* conditions, else agent")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--k", type=int, default=1, help="repeat the run k times (reliability)")
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--budget-chars", type=int, default=120000, help="oracle document budget")
    ap.add_argument("--obs-chars", type=int, default=4000, help="observation kept in the transcript")
    ap.add_argument("--max-chars", type=int, default=8000, help="chars per fetch/thread")
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--backend", default=None, choices=["codex", "glm", "anthropic"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--worlds-root", default=None); ap.add_argument("--runs-root", default=None)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.backend or a.model:
        llm.set_backend(a.backend, a.model)
    base = a.run_id or f"{a.task or a.jur or a.world}__{a.condition}"
    out = []
    for i in range(1, max(1, a.k) + 1):
        a.run_id = base if a.k == 1 else f"{base}__r{i}"
        out.append(solve(a, a.run_id))
        print(json.dumps(out[-1], indent=1))
    return out


if __name__ == "__main__":
    main()
