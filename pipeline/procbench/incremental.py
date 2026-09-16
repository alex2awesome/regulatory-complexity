#!/usr/bin/env python3
"""Incremental process-model fitting: read one document at a time, decide what is new.

The one-shot solver reads everything and writes a model once, so it cannot say whether a document
taught it anything. This fits the model the way you would fit a latent structure — alternating between
an assignment step and an update step, which is what Alex called the EM shape:

  E-step (assignment)  for each candidate step extracted from the new document, decide whether it is an
                       existing node, a refinement of one, a contradiction of one, or a new node. The
                       "new node" option is what makes this nonparametric: the number of steps is not
                       fixed in advance, and opening a node is the model's own decision.
  M-step (update)      merge confirming evidence into the matched node (sharpening actor, timing, fee,
                       order, and accumulating provenance), append new nodes, and record contradictions
                       rather than silently overwriting.

What falls out that a one-shot run cannot give:
  * a saturation curve — new steps per document read, so the stopping rule can be endogenous
    (stop when novelty dies) instead of an arbitrary step cap;
  * marginal information value per document KIND — which classes of document actually teach anything;
  * contradictions, with both sources and their evidence tiers, which are currently invisible.

  python3 pipeline/procbench/incremental.py --docs docs.json --out runs/inc/<id> \
      [--budget-docs 12] [--stop-after-quiet 3] [--backend codex] [--offline-align]

`docs.json`: [{"id","title","kind","tier","text","url"}, ...] in the order they should be read.
Writes model.json, trajectory.jsonl (one line per document), contradictions.json, state.json.
"""
import argparse, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))
try:
    from procbench import align as A
except ImportError:
    from pipeline.procbench import align as A

TIER_RANK = {"observed": 4, "verifiable_official": 4, "inferred": 3, "designed": 3,
             "designed_document": 3, "statute": 2, "statutory": 2, "declared": 2,
             "user_report": 1, "community_reported": 1}


def _llm():
    import llm
    return llm


def extract(doc, model_name=None, max_chars=24000):
    """One call: what does THIS document say? No reconstruction from prior knowledge."""
    body = (f"DOCUMENT id={doc.get('id')} kind={doc.get('kind')} tier={doc.get('tier')}\n"
            f"title: {doc.get('title')}\n\n{(doc.get('text') or '')[:max_chars]}")
    # llm_json takes a prompt FILE (resolved under pipeline/prompts unless absolute), not prompt text
    out = _llm().llm_json(str(HERE / "prompts" / "extract_candidates.md"), body, model=model_name)
    if isinstance(out, str):
        out = json.loads(out)
    steps = (out or {}).get("steps") or []
    for s in steps:
        s["_doc"] = doc.get("id")
        s["_kind"] = doc.get("kind")
        s["_tier"] = doc.get("tier")
    return steps, ((out or {}).get("order_statements") or [])


def decide_offline(cands, state, thresh=0.42):
    """Deterministic fallback for the assignment step: reuse the scorer's similarity."""
    pred = {"activities": [{"id": f"c{i}", "name": c.get("name", ""), "actor": c.get("actor") or "",
                            "local_name": "", "idx": i} for i, c in enumerate(cands)]}
    gold = {"activities": [{"id": n["id"], "name": n["name"], "actor": n.get("actor") or "",
                            "local_name": "", "idx": j} for j, n in enumerate(state["nodes"])]}
    for m in (pred, gold):
        for a in m["activities"]:
            a["toks"] = A.toks(a["name"])
            a["toks_local"] = set()
            a["actor"] = A.canon_actor(a["actor"])
            a["rank"] = a["idx"] / max(1, len(m["activities"]) - 1)
    out = []
    for i, c in enumerate(cands):
        best, bs = None, 0.0
        for g in gold["activities"]:
            s, _ = A.sim(pred["activities"][i], g)
            if s > bs:
                bs, best = s, g["id"]
        out.append({"candidate": i, "verdict": "match" if bs >= thresh else "new",
                    "node": best if bs >= thresh else None, "why": f"offline sim {bs:.2f}"})
    return out


def decide_llm(cands, state):
    prompt = (HERE / "prompts/merge_decide.md").read_text()
    mod = "\n".join(f"{n['id']} | {n.get('actor') or '?'} | {n['name']}" for n in state["nodes"]) or "(empty)"
    cs = "\n".join(f"{i} | {c.get('actor') or '?'} | {c.get('name','')} | {str(c.get('quote') or '')[:110]}"
                   for i, c in enumerate(cands))
    user = prompt.replace("{{MODEL}}", mod).replace("{{CANDIDATES}}", cs)
    # the prompt carries substitutions, so it cannot be a file: use the inline path
    out = A._llm_json_inline(user)
    if isinstance(out, str):
        out = json.loads(out)
    return (out or {}).get("decisions") or []


def new_node(state, c):
    nid = f"N{len(state['nodes']) + 1:02d}"
    state["nodes"].append({
        "id": nid, "name": c.get("name", ""), "actor": c.get("actor"),
        "occasion": c.get("occasion"), "timing": c.get("timing"), "fee": c.get("fee"),
        "rework": c.get("rework"), "support": 1, "first_seen": c.get("_doc"),
        "evidence": [{"doc": c.get("_doc"), "kind": c.get("_kind"), "tier": c.get("_tier"),
                      "quote": str(c.get("quote") or "")[:300]}],
        "field_sources": {k: {"doc": c.get("_doc"), "tier": c.get("_tier")}
                          for k in ("actor", "timing", "fee") if c.get(k)},
    })
    return nid


def merge_into(state, node, c, contradictions, verdict):
    """M-step for one candidate. Better-tiered evidence wins a field; disagreement is recorded."""
    node["support"] += 1
    node["evidence"].append({"doc": c.get("_doc"), "kind": c.get("_kind"), "tier": c.get("_tier"),
                             "quote": str(c.get("quote") or "")[:300], "verdict": verdict})
    for field in ("actor", "occasion", "timing", "fee", "rework"):
        newv = c.get(field)
        if newv in (None, "", {}):
            continue
        oldv = node.get(field)
        if oldv in (None, "", {}):
            node[field] = newv
            node.setdefault("field_sources", {})[field] = {"doc": c.get("_doc"), "tier": c.get("_tier")}
            continue
        same = json.dumps(oldv, sort_keys=True) == json.dumps(newv, sort_keys=True)
        if same:
            continue
        src = node.get("field_sources", {}).get(field, {})
        old_rank = TIER_RANK.get(str(src.get("tier")), 0)
        new_rank = TIER_RANK.get(str(c.get("_tier")), 0)
        contradictions.append({
            "node": node["id"], "field": field,
            "held": oldv, "held_doc": src.get("doc"), "held_tier": src.get("tier"),
            "offered": newv, "offered_doc": c.get("_doc"), "offered_tier": c.get("_tier"),
            "resolution": "replaced" if new_rank > old_rank else "kept",
            "quote": str(c.get("quote") or "")[:200],
        })
        if new_rank > old_rank:
            node[field] = newv
            node["field_sources"][field] = {"doc": c.get("_doc"), "tier": c.get("_tier")}


def emit_prompts(docs, out_dir, max_chars=24000):
    """Write one extraction prompt per document, for an agent fleet to answer.

    Used when no LLM backend is available to this process. Extraction is per-document and independent,
    so it parallelises cleanly; the assignment and update steps still run here, in order.
    """
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    prompt = (HERE / "prompts" / "extract_candidates.md").read_text()
    for i, d in enumerate(docs):
        body = (f"DOCUMENT id={d.get('id')} kind={d.get('kind')} tier={d.get('tier')}\n"
                f"title: {d.get('title')}\n\n{(d.get('text') or '')[:max_chars]}")
        (out / f"prompt_{i:02d}.txt").write_text(
            prompt + "\n\n" + body +
            f"\n\nWrite ONLY the JSON object to {out}/cand_{i:02d}.json — no prose, no fences.\n")
    (out / "index.json").write_text(json.dumps(
        [{"i": i, "id": d.get("id"), "kind": d.get("kind"), "tier": d.get("tier")} for i, d in enumerate(docs)], indent=1))
    print(f"{len(docs)} extraction prompts -> {out}/prompt_*.txt")


def load_candidates(docs, cand_dir):
    """Read agent-produced extractions back in document order."""
    cd = pathlib.Path(cand_dir)
    got = {}
    for i, d in enumerate(docs):
        f = cd / f"cand_{i:02d}.json"
        if not f.exists():
            continue
        try:
            j = json.load(open(f))
        except Exception:                                               # noqa: BLE001
            continue
        steps = j.get("steps") or []
        for s in steps:
            s["_doc"] = d.get("id"); s["_kind"] = d.get("kind"); s["_tier"] = d.get("tier")
        got[i] = (steps, j.get("order_statements") or [])
    return got



def consolidate(state, thresh=0.52, text_min=0.34):
    """Agglomerative merge over the fitted nodes — the cheap repair for over-splitting.

    The assignment step is greedy and sees each candidate once, against the model as it stood at that
    moment. Two nodes opened from different documents can therefore describe the same act. This pass
    compares every fitted node against every other with the scorer's own similarity, merges above the
    threshold (transitively, via union-find), and sums support so the merged node carries all of its
    evidence. Returns the merge log so the operation is auditable rather than silent.
    """
    nodes = state["nodes"]
    if len(nodes) < 2:
        return []
    prep = [{"id": n["id"], "name": n["name"], "actor": A.canon_actor(n.get("actor") or ""),
             "local_name": "", "idx": i, "toks": A.toks(n["name"]), "toks_local": set(),
             "rank": i / max(1, len(nodes) - 1)} for i, n in enumerate(nodes)]
    parent = {n["id"]: n["id"] for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    merges = []
    for i in range(len(prep)):
        for j in range(i + 1, len(prep)):
            s, text = A.sim(prep[i], prep[j])
            if s >= thresh and text >= text_min:
                ri, rj = find(prep[i]["id"]), find(prep[j]["id"])
                if ri != rj:
                    parent[rj] = ri
                    merges.append({"kept": ri, "absorbed": rj, "score": s, "text_sim": text,
                                   "kept_name": nodes[i]["name"][:70], "absorbed_name": nodes[j]["name"][:70]})
    groups = {}
    for n in nodes:
        groups.setdefault(find(n["id"]), []).append(n)
    merged = []
    for root, members in groups.items():
        members.sort(key=lambda n: -n["support"])           # keep the best-supported wording
        head = dict(members[0])
        for m in members[1:]:
            head["support"] += m["support"]
            head["evidence"] = (head.get("evidence") or []) + (m.get("evidence") or [])
            for f in ("actor", "occasion", "timing", "fee", "rework"):
                if head.get(f) in (None, "", {}) and m.get(f) not in (None, "", {}):
                    head[f] = m[f]
        head["merged_from"] = [m["id"] for m in members[1:]]
        merged.append(head)
    merged.sort(key=lambda n: n["id"])
    state["nodes"] = merged
    return merges

def run(docs, out_dir, budget_docs=None, stop_after_quiet=None, offline=False, model_name=None,
        candidates=None, consolidate_after=True):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    state = {"nodes": [], "order_statements": []}
    contradictions, traj, quiet = [], [], 0
    read = 0
    for doc_i, doc in enumerate(docs):
        if budget_docs and read >= budget_docs:
            traj.append({"stopped": "budget", "docs_read": read}); break
        read += 1
        if candidates is not None:
            idx = doc_i           # positional, not docs.index(): identical document dicts would collide
            if idx not in candidates:
                traj.append({"doc": doc.get("id"), "error": "no extraction supplied"}); continue
            cands, orders = candidates[idx]
        else:
            try:
                cands, orders = extract(doc, model_name)
            except Exception as e:                                      # noqa: BLE001
                traj.append({"doc": doc.get("id"), "error": str(e)[:200]}); continue
        state["order_statements"] += [{"doc": doc.get("id"), "text": o} for o in orders]
        decisions = (decide_offline(cands, state) if (offline or not state["nodes"])
                     else decide_llm(cands, state))
        by_idx = {d.get("candidate"): d for d in decisions if isinstance(d, dict)}
        counts = {"new": 0, "match": 0, "refines": 0, "contradicts": 0}
        for i, c in enumerate(cands):
            d = by_idx.get(i) or {"verdict": "new"}
            v = d.get("verdict", "new")
            node = next((n for n in state["nodes"] if n["id"] == d.get("node")), None)
            if v == "new" or node is None:
                new_node(state, c); counts["new"] += 1
            else:
                merge_into(state, node, c, contradictions, v)
                counts[v if v in counts else "match"] += 1
        row = {"doc": doc.get("id"), "kind": doc.get("kind"), "tier": doc.get("tier"),
               "candidates": len(cands), **counts,
               "model_size": len(state["nodes"]), "contradictions_total": len(contradictions)}
        traj.append(row)
        print(f"  [{read:2}] {str(doc.get('id'))[:26]:26} {str(doc.get('kind'))[:16]:16} "
              f"cand={len(cands):2} new={counts['new']:2} match={counts['match']:2} "
              f"contra={counts['contradicts']:2} |M|={len(state['nodes']):2}")
        quiet = quiet + 1 if counts["new"] == 0 else 0
        if stop_after_quiet and quiet >= stop_after_quiet:
            traj.append({"stopped": "novelty_exhausted", "quiet_docs": quiet, "docs_read": read}); break
    merges = consolidate(state) if consolidate_after else []
    if merges:
        print(f"\n  consolidation merged {len(merges)} node pair(s); {len(state['nodes'])} nodes remain")
        (out / "merges.json").write_text(json.dumps(merges, indent=1))
    (out / "trajectory.jsonl").write_text("\n".join(json.dumps(r) for r in traj))
    (out / "contradictions.json").write_text(json.dumps(contradictions, indent=1))
    (out / "state.json").write_text(json.dumps(state, indent=1))
    model = {"model_id": out.name, "source": "declared", "actors": sorted({n["actor"] for n in state["nodes"] if n.get("actor")}),
             "activities": [{"id": n["id"], "name": n["name"], "actor": n.get("actor") or "unknown",
                             "occasion": n.get("occasion"), "timing": n.get("timing"), "fee": n.get("fee"),
                             "rework": n.get("rework"), "support": n["support"],
                             "evidence": [e.get("quote") for e in n["evidence"]][:4]} for n in state["nodes"]],
             "edges": [], "unknowns": []}
    (out / "model.json").write_text(json.dumps(model, indent=2))
    errs = [r for r in traj if r.get("error")]
    if errs:
        print(f"\n  !! {len(errs)} document(s) failed extraction; first: {errs[0]['error'][:160]}")
    print(f"\n{len(state['nodes'])} steps from {read} documents; {len(contradictions)} contradictions -> {out}")
    return model, traj, contradictions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--budget-docs", type=int, default=None)
    ap.add_argument("--stop-after-quiet", type=int, default=None)
    ap.add_argument("--offline-align", action="store_true", help="deterministic assignment step (no LLM)")
    ap.add_argument("--emit-prompts", metavar="DIR", help="write per-document extraction prompts and exit")
    ap.add_argument("--candidates", metavar="DIR", help="use agent-produced extractions from DIR")
    ap.add_argument("--no-consolidate", action="store_true", help="skip the post-fit merge of duplicate nodes")
    ap.add_argument("--backend", default=None)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    if a.backend:
        _llm().set_backend(a.backend, a.model)
    docs = json.load(open(a.docs))
    if a.emit_prompts:
        emit_prompts(docs, a.emit_prompts); return
    cands = load_candidates(docs, a.candidates) if a.candidates else None
    if a.candidates:
        print(f"loaded extractions for {len(cands)}/{len(docs)} documents")
    run(docs, a.out, a.budget_docs, a.stop_after_quiet, a.offline_align, a.model, cands,
        consolidate_after=not a.no_consolidate)


if __name__ == "__main__":
    main()
