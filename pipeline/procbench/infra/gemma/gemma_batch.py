#!/usr/bin/env python3
"""Offline batch inference with a local open model under vLLM. Runs ON sk2.

Standalone on purpose: sk2 has no copy of this repo. Copy this file next to your
input and run it with the gemma4 environment's python (see docs/gemma-runbook.md;
use gemma_remote.sh rather than invoking this by hand).

Input  (JSONL): {"id": str, "messages": [{"role": "system"|"user"|"assistant", "content": str}, ...],
                 optional "max_tokens": int}
Output (JSONL): {"id", "text", "prompt_tokens", "gen_tokens", "finish_reason", "json": <parsed or null>}
plus <output>.meta.json with model, timing and token totals.

Deterministic by default (temperature 0). A system message is folded into the
first user turn, because Gemma chat templates do not reliably accept a system role.
`json` is a best-effort parse of the first JSON object/array in the reply
(code fences stripped); callers must still validate it.
"""
import argparse, json, re, sys, time

def fold_system(msgs):
    sys_txt = "\n\n".join(m["content"] for m in msgs if m["role"] == "system")
    rest = [dict(m) for m in msgs if m["role"] != "system"]
    if sys_txt:
        if rest and rest[0]["role"] == "user":
            rest[0]["content"] = sys_txt + "\n\n=====\n\n" + rest[0]["content"]
        else:
            rest.insert(0, {"role": "user", "content": sys_txt})
    return rest

def parse_json(text):
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M).strip()
    for pat in (r"\{.*\}", r"\[.*\]"):
        m = re.search(pat, t, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-model-len", type=int, default=32768)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--gpu-mem", type=float, default=0.88)
    ap.add_argument("--tp", type=int, default=1, help="tensor parallel size (GPUs)")
    a = ap.parse_args()

    from vllm import LLM, SamplingParams
    rows = [json.loads(l) for l in open(a.input) if l.strip()]
    kw = dict(model=a.model, max_model_len=a.max_model_len, gpu_memory_utilization=a.gpu_mem,
              tensor_parallel_size=a.tp, seed=0)
    try:    # Gemma 4 is multimodal; disable image/audio inputs to save memory
        llm = LLM(**kw, limit_mm_per_prompt={"image": 0, "audio": 0})
    except Exception:
        try: llm = LLM(**kw, limit_mm_per_prompt={"image": 0})
        except Exception: llm = LLM(**kw)          # text-only models

    by_max = {}
    for i, r in enumerate(rows):
        by_max.setdefault(r.get("max_tokens", a.max_tokens), []).append(i)
    results = [None] * len(rows)
    t0 = time.time()
    for mt, idxs in by_max.items():
        sp = SamplingParams(temperature=a.temperature, max_tokens=mt)
        outs = llm.chat([fold_system(rows[i]["messages"]) for i in idxs], sp, use_tqdm=True)
        for i, o in zip(idxs, outs):
            c = o.outputs[0]
            results[i] = {"id": rows[i]["id"], "text": c.text, "prompt_tokens": len(o.prompt_token_ids),
                          "gen_tokens": len(c.token_ids), "finish_reason": c.finish_reason,
                          "json": parse_json(c.text)}
    dt = time.time() - t0
    tmp = a.output + ".tmp"
    with open(tmp, "w") as f:
        for r in results: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    import os; os.replace(tmp, a.output)          # atomic: a killed run never leaves a truncated file
    meta = {"model": a.model, "n": len(rows), "seconds": round(dt, 1),
            "prompt_tokens": sum(r["prompt_tokens"] for r in results),
            "gen_tokens": sum(r["gen_tokens"] for r in results),
            "truncated_at_max_tokens": sum(r["finish_reason"] == "length" for r in results),
            "unparseable_json": sum(r["json"] is None for r in results),
            # vLLM returns finish_reason "abort" with empty text for every request still queued
            # when its engine shuts down; those are failures, not answers. Rerun them by id.
            "aborted": sum(r["finish_reason"] == "abort" for r in results)}
    json.dump(meta, open(a.output + ".meta.json", "w"), indent=1)
    if meta["aborted"]:
        print("INCOMPLETE", json.dumps(meta), flush=True)
        sys.exit(5)
    print("DONE", json.dumps(meta), flush=True)

if __name__ == "__main__":
    main()
