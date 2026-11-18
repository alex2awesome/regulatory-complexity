"""Gemma 4 31B as a third agent in the airline and constitution studies (2026-11-11).

Runs ON the GPU host (sk3: /lfs/skampere3/0/alexspan/envs/gemma4, vLLM in-process, offline;
no server, no network). The study modules run unchanged: their get_model is pointed at a
micro-batcher that gathers concurrent episode turns into one vLLM call. Transport differs
from the CLI models: the system text is folded into the first user turn (Gemma's template
has no reliable system role) and earlier turns stay as native chat turns. Sampling follows
Gemma's recommended settings, with a seed per call derived from its stem.

    CUDA_VISIBLE_DEVICES=1 python -m benchmark.rulegap.gemma_agents --model DIR --out DIR
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import threading
import time

from . import agent_airline as AIR
from . import agent_constitution as CON

NAME = 'gemma:gemma-4-31b-it'


def fold(system, messages):
    msgs = [dict(m) for m in messages]
    if system:
        msgs[0]['content'] = system + '\n\n=====\n\n' + msgs[0]['content']
    return msgs


class Batcher:
    name = NAME

    def __init__(self, llm, window=1.5, max_tokens=2048):
        self.llm, self.window, self.max_tokens = llm, window, max_tokens
        self.cv, self.q, self.n_batches = threading.Condition(), [], 0
        threading.Thread(target=self._loop, daemon=True).start()

    def call(self, system, messages, schema, stem, out):
        item = dict(msgs=fold(system, messages), stem=stem, ev=threading.Event())
        with self.cv:
            self.q.append(item)
            self.cv.notify()
        item['ev'].wait()
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{stem}.gemma.json').write_text(json.dumps({k: item.get(k) for k in
                                                            ('text', 'finish_reason', 'prompt_tokens', 'gen_tokens', 'err')}))
        if item.get('err'):
            raise RuntimeError(item['err'])
        if item['finish_reason'] == 'length':
            raise RuntimeError(f'reply cut off at {self.max_tokens} tokens')
        return dict(text=item['text'], cost_usd=None)

    def _loop(self):
        from vllm import SamplingParams
        while True:
            with self.cv:
                while not self.q:
                    self.cv.wait()
            time.sleep(self.window)                     # let the other episodes' turns arrive
            with self.cv:
                batch, self.q = self.q, []
            sps = [SamplingParams(temperature=1.0, top_p=0.95, top_k=64, max_tokens=self.max_tokens,
                                  seed=int(hashlib.sha256(b['stem'].encode()).hexdigest()[:8], 16)) for b in batch]
            try:
                outs = self.llm.chat([b['msgs'] for b in batch], sps, use_tqdm=False)
                for b, o in zip(batch, outs):
                    c = o.outputs[0]
                    b.update(text=c.text, finish_reason=c.finish_reason, prompt_tokens=len(o.prompt_token_ids),
                             gen_tokens=len(c.token_ids))
            except Exception as e:                      # kept: every episode in the batch records the error
                for b in batch:
                    b['err'] = f'{type(e).__name__}: {e}'[:500]
            self.n_batches += 1
            for b in batch:
                b['ev'].set()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--gpu-mem', type=float, default=0.85)
    a = ap.parse_args(argv)
    from vllm import LLM
    kw = dict(model=a.model, max_model_len=32768, gpu_memory_utilization=a.gpu_mem, seed=0)
    try:
        llm = LLM(**kw, limit_mm_per_prompt={'image': 0, 'audio': 0})
    except Exception:
        llm = LLM(**kw, limit_mm_per_prompt={'image': 0})
    b = Batcher(llm)
    t0 = time.time()
    for mod, sub in ((AIR, 'airline'), (CON, 'constitution')):
        mod.MODELS, mod.get_model = [NAME], (lambda name: b)
        out = a.out / sub
        out.mkdir(parents=True, exist_ok=True)
        n = len(mod.jobs())
        mod.run(out, workers=n)                         # every episode in flight at once; turns batch together
        mod.probes(out, workers=64)
        print(f'{sub}: done at {time.time() - t0:.0f}s, {b.n_batches} batches', flush=True)
    cfg = Path(a.model) / 'config.json'
    (a.out / 'meta.json').write_text(json.dumps(dict(model=NAME, path=a.model, seconds=round(time.time() - t0),
                                                     batches=b.n_batches, config_sha256=hashlib.sha256(cfg.read_bytes()).hexdigest())))
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
