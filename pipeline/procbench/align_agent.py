#!/usr/bin/env python3
"""Agent-backed k-vote alignment: same protocol as align.llm_align, but the k
independent matchings are produced by Claude subagents instead of pipeline/llm.py.

Use when no LLM backend is keyed (Codex logged out, no GLM/Anthropic key) — the
orchestrator spawns k agents, each reads one prompt file and writes one JSON.

  # 1. emit k prompts (shuffled activity lists, one per vote)
  python3 pipeline/procbench/align_agent.py emit --pred P.json --gold G.json --k 3 --out-dir runs/x/align
  # 2. (orchestrator spawns k agents; each writes runs/x/align/vote_<i>.json)
  # 3. merge the votes into an alignment file score.py can consume
  python3 pipeline/procbench/align_agent.py merge --pred P.json --gold G.json \
      --votes runs/x/align/vote_*.json --out runs/x/pair.alignment.json
  # 4. score against it
  python3 pipeline/procbench/score.py --pred P.json --gold G.json --align file \
      --alignment-in runs/x/pair.alignment.json --out runs/x/pair.score.json
"""
import argparse, glob, json, math, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
try:
    from procbench import align as A
except ImportError:
    from pipeline.procbench import align as A


def emit(pred_path, gold_path, k, out_dir, seed=100):
    pred, gold = A.load_model(pred_path), A.load_model(gold_path)
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(k):
        rnd = random.Random(seed + i)
        p_lines, g_lines = A._lines(pred["activities"])[:], A._lines(gold["activities"])[:]
        rnd.shuffle(p_lines); rnd.shuffle(g_lines)
        body = (A.PROMPT + "\nPREDICTED activities (id | actor | name):\n" + "\n".join(p_lines)
                + "\n\nGOLD activities (id | actor | name):\n" + "\n".join(g_lines)
                + f"\n\nWrite ONLY the JSON object to {out}/vote_{i}.json — no prose, no code fences.\n")
        f = out / f"prompt_{i}.txt"; f.write_text(body); written.append(str(f))
    (out / "meta.json").write_text(json.dumps(
        {"pred": str(pred_path), "gold": str(gold_path), "k": k, "seed": seed,
         "n_pred": len(pred["activities"]), "n_gold": len(gold["activities"]),
         "prompts": written, "expected_votes": [str(out / f"vote_{i}.json") for i in range(k)]}, indent=1))
    print(f"{k} prompts -> {out}/prompt_*.txt  (pred {len(pred['activities'])} acts, gold {len(gold['activities'])} acts)")
    for w in written:
        print("  ", w)


def merge(pred_path, gold_path, vote_files, out_path, k=None):
    pred, gold = A.load_model(pred_path), A.load_model(gold_path)
    pmap = {a["id"]: a for a in pred["activities"]}
    gmap = {a["id"]: a for a in gold["activities"]}
    votes, used = {}, 0
    for vf in vote_files:
        try:
            d = json.load(open(vf))
        except Exception as e:                                        # noqa: BLE001
            print(f"  skip {vf}: {e}", file=sys.stderr); continue
        used += 1
        seen = set()
        for pr in d.get("pairs", []):
            key = (str(pr.get("pred")), str(pr.get("gold")))
            if key in seen or key[0] not in pmap or key[1] not in gmap:
                continue
            seen.add(key)
            votes[key] = votes.get(key, 0) + 1
    k = k or used or 1
    need = math.ceil(k / 2)
    pairs = []
    for (pid, gid), n in votes.items():
        if n < need:
            continue
        p, g = pmap[pid], gmap[gid]
        s, text = A.sim(p, g)
        pairs.append(A._pair(p, g, s, text, "agent_vote", votes=n, k=k))
    pg, gp = {}, {}
    for pr in pairs:
        pg.setdefault(pr["pred"], []).append(pr["gold"]); gp.setdefault(pr["gold"], []).append(pr["pred"])
    for pr in pairs:
        pr["relation"] = ("split" if len(pg[pr["pred"]]) > 1 else
                          "merge" if len(gp[pr["gold"]]) > 1 else "primary")
    pairs.sort(key=lambda d: (d["gold_idx"], d["pred_idx"]))
    off = A.offline_align(pred, gold)
    agree = A.agreement(off, pairs)
    outp = pathlib.Path(out_path); outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(
        {"mode_used": "agent", "k": k, "votes_used": used, "min_votes": need,
         "n_pairs": len(pairs), "pairs": pairs, "offline_vs_agent_agreement": agree,
         "rejected_below_threshold": sorted([{"pred": a, "gold": b, "votes": n}
                                             for (a, b), n in votes.items() if n < need],
                                            key=lambda d: -d["votes"])[:40]}, indent=1))
    print(f"{len(pairs)} pairs from {used}/{k} votes (>= {need} votes) -> {outp}")
    print(f"  offline-vs-agent agreement: {agree}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit"); e.add_argument("--pred", required=True); e.add_argument("--gold", required=True)
    e.add_argument("--k", type=int, default=3); e.add_argument("--out-dir", required=True); e.add_argument("--seed", type=int, default=100)
    m = sub.add_parser("merge"); m.add_argument("--pred", required=True); m.add_argument("--gold", required=True)
    m.add_argument("--votes", nargs="+", required=True); m.add_argument("--out", required=True); m.add_argument("--k", type=int)
    a = ap.parse_args()
    if a.cmd == "emit":
        emit(a.pred, a.gold, a.k, a.out_dir, a.seed)
    else:
        files = [f for pat in a.votes for f in (glob.glob(pat) or [pat])]
        merge(a.pred, a.gold, files, a.out, a.k)


if __name__ == "__main__":
    main()
