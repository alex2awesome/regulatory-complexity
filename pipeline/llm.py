"""Shared LLM helper: one call -> schema-validated JSON, with one repair retry.

Models are GENERATORS here, never references: everything they emit is checked
downstream by execution, invariants, or human-audited samples.

Backends (select with --backend on the CLIs, or env RC_LLM_BACKEND):
  codex      (default) — shells out to the Codex CLI (`codex exec`), which
             authenticates via the user's ChatGPT login: no API key needed.
             Model defaults to the CLI's configured default; override with
             --model (e.g. gpt-5.1-codex).
  glm        — Zhipu GLM via its OpenAI-compatible endpoint. Needs
             GLM_API_KEY (or ZHIPUAI_API_KEY); optional GLM_BASE_URL
             (default https://api.z.ai/api/paas/v4). Default model glm-4.6.
  anthropic  — Anthropic API. Needs ANTHROPIC_API_KEY and the `anthropic`
             package. Default model claude-fable-5.

Env overrides: RC_LLM_BACKEND, RC_LLM_MODEL.
"""

import json
import os
import pathlib
import re
import subprocess
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).parent

BACKEND_DEFAULT_MODELS = {"codex": None, "glm": "glm-4.6", "anthropic": "claude-fable-5"}

CONFIG = {
    "backend": os.environ.get("RC_LLM_BACKEND", "codex"),
    "model": os.environ.get("RC_LLM_MODEL"),
}


def set_backend(backend=None, model=None):
    if backend:
        if backend not in BACKEND_DEFAULT_MODELS:
            raise ValueError(f"unknown backend: {backend}")
        CONFIG["backend"] = backend
    if model:
        CONFIG["model"] = model


def model_desc():
    b = CONFIG["backend"]
    m = CONFIG["model"] or BACKEND_DEFAULT_MODELS[b] or "cli-default"
    return f"{b}:{m}"


def extract_json(text):
    m = re.search(r"```(?:json)?\s*([\[{].*[\]}])\s*```", text, re.DOTALL)
    return json.loads(m.group(1) if m else text)


# ---------------------------------------------------------------- backends

def _call_codex(prompt_text, model, timeout=int(os.environ.get("RC_CODEX_TIMEOUT", "2400"))):
    """Non-interactive Codex CLI run. Read-only sandbox, ephemeral session;
    the prompt is self-contained, so the agent is told not to explore."""
    preamble = ("Answer directly from the prompt below. Do not read files, run "
                "commands, or explore the repository.\n\n")
    with tempfile.NamedTemporaryFile(mode="r", suffix=".txt", delete=False) as out:
        out_path = out.name
    cmd = ["codex", "exec", "--sandbox", "read-only", "--ephemeral",
           "--skip-git-repo-check", "--color", "never", "-o", out_path, "-"]
    if model:
        cmd += ["-m", model]
    try:
        proc = subprocess.run(cmd, input=(preamble + prompt_text).encode(),
                              capture_output=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"codex exec failed (rc={proc.returncode}): "
                               f"{proc.stderr.decode()[-500:]}")
        return pathlib.Path(out_path).read_text()
    finally:
        pathlib.Path(out_path).unlink(missing_ok=True)


def _call_openai_compat(messages, model, base_url, api_key, max_tokens, timeout=600):
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps({"model": model, "messages": messages,
                         "max_tokens": max_tokens}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _call_glm(messages, model, max_tokens):
    key = os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPUAI_API_KEY")
    if not key:
        raise RuntimeError("GLM backend needs GLM_API_KEY (or ZHIPUAI_API_KEY) set")
    base = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/paas/v4")
    return _call_openai_compat(messages, model, base, key, max_tokens)


def _call_anthropic(messages, model, max_tokens):
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(model=model, max_tokens=max_tokens, messages=messages)
    return resp.content[-1].text


def _complete(messages, model, max_tokens):
    """messages: [{'role','content'},...]. Returns raw text."""
    backend = CONFIG["backend"]
    model = model or CONFIG["model"] or BACKEND_DEFAULT_MODELS[backend]
    if backend == "codex":
        # codex exec is single-shot: flatten the conversation into one prompt
        text = "\n\n".join(
            (f"[Your previous response]\n{m['content']}" if m["role"] == "assistant"
             else m["content"])
            for m in messages
        )
        return _call_codex(text, model)
    if backend == "glm":
        return _call_glm(messages, model, max_tokens)
    if backend == "anthropic":
        return _call_anthropic(messages, model, max_tokens)
    raise ValueError(f"unknown backend: {backend}")


# ------------------------------------------------------------------- llm_json

def llm_json(prompt_file, body, schema_file=None, model=None, extra="", max_tokens=16000):
    import jsonschema

    schema = json.loads((HERE / "schemas" / schema_file).read_text()) if schema_file else None
    prompt = (HERE / "prompts" / prompt_file).read_text()
    user = f"{prompt}\n\n{extra}\n\n"
    if schema:
        user += f"Output schema (JSON Schema):\n```json\n{json.dumps(schema, indent=1)}\n```\n\n"
    if body:
        user += f"SOURCE TEXT:\n{body}\n\n"
    user += "Respond with a single JSON value in a ```json fenced block" + (", valid against the schema." if schema else ".")

    messages = [{"role": "user", "content": user}]
    for attempt in range(2):
        raw = _complete(messages, model, max_tokens)
        try:
            obj = extract_json(raw)
            if schema:
                jsonschema.validate(obj, schema)
            return obj
        except Exception as e:
            if attempt == 1:
                raise
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"Your output failed validation: {e}. Emit the corrected full JSON only."},
            ]
