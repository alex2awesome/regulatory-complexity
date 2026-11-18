#!/usr/bin/env python3
"""Split a world's artifact specs into renderer batches.

Groups: T (target artifacts — high fidelity), D (structured distractors: modelled non-target processes and
look-alike statutes — same brief), F (filler: unmodelled programs / off-topic threads — short, cheap).
Batches are balanced by word budget so one agent finishes a batch in one run.
  python3 benchmark/synth/render/batches.py --world W1 [--words-per-batch 14000]
Writes worlds/<W>/batches/<batch_id>.json {batch_id, group, spec_ids, words, kinds, jurs} and batches/index.json.
Already-rendered specs (artifacts/<id>.md exists) are skipped, so re-running after a partial wave batches the rest.
"""
import argparse, json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[3]


def group_of(s):
    if s.get("target"):
        return "T"
    return "F" if "filler" in (s.get("why") or "").lower() else "D"


def words_of(s):
    lo, hi = (s.get("style") or {}).get("length_words", [250, 450])
    n = (lo + hi) / 2
    if s.get("kind") in ("reddit_thread", "forum_thread"):
        n += 60 * len(s.get("thread") or [])
    return int(n)


def _write(out, bid, g, cur, cw):
    rec = {"batch_id": bid, "group": g, "spec_ids": [s["artifact_id"] for s in cur], "words": cw,
           "kinds": dict(collections.Counter(s["kind"] for s in cur)), "jurs": sorted({s.get("jur") or "" for s in cur})}
    (out / f"{bid}.json").write_text(json.dumps(rec, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--world", default="W1"); ap.add_argument("--words-per-batch", type=int, default=14000)
    # A frozen render selection (benchmark/synth/render/selection.py) restricts the
    # batches to the chosen text tier and user-tier sample. Without it every
    # spec is batched, which at world_model_version 2 means 24,868 documents,
    # 70% of them forum threads.
    ap.add_argument("--selection", default="render_selection.txt",
                    help="file of artifact_ids to render; 'none' to batch everything")
    # STATUTE PRIORITY. The default packing sorts target specs by county, which
    # smears every statute across every batch: after 1,864 rendered artifacts no
    # statute was more than 2% verified-complete, so no benchmark task could run
    # end to end. `--priority statute` orders target specs smallest-statute-first
    # and pulls each statute's dependencies (its state-level documents and the
    # shared pages its artifacts link to) into the same early batches, so one
    # statute finishes, then the next.
    ap.add_argument("--priority", choices=["county", "statute"], default="statute")
    # Batches already dispatched to running agents must not be rewritten under
    # them. `--keep` names batch ids to leave byte-identical; their spec_ids are
    # excluded from repacking, and repacking fills only the remaining ids.
    ap.add_argument("--keep", default="", help="comma-separated batch ids to leave untouched")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even if render agents look live")
    # A second agent's lane needs its own batch namespace. With --prefix X the
    # groups become XT00/XD00/XF00 and the delete step only ever removes files
    # with that prefix, so two lanes can be batched side by side.
    ap.add_argument("--prefix", default="", help="prefix batch ids (concurrent lane)")
    a = ap.parse_args()
    keep = {k.strip() for k in a.keep.split(",") if k.strip()}
    wd = ROOT / "benchmark/synth/worlds" / a.world
    specs = [json.load(open(f)) for f in sorted((wd / "specs").glob("*.json"))]
    sel = None
    if a.selection and a.selection.lower() != "none":
        sf = wd / a.selection
        if sf.exists():
            sel = {ln.strip() for ln in sf.read_text().splitlines() if ln.strip()}
            specs = [s for s in specs if s["artifact_id"] in sel]
            print("selection %s: %d of the world's specs" % (sf.name, len(specs)))
        else:
            print("no %s; batching every spec" % sf.name)
    # Only a COMPLETE artifact counts as done. An agent killed mid-batch (this
    # render has been interrupted three times by usage limits) could leave a
    # truncated file, and treating that as rendered would quietly bake a broken
    # document into the corpus.
    def _complete(path):
        body = path.read_text()
        return body.startswith("---") and body.count("\n---") >= 1 and len(body.split()) >= 60

    done = set()
    if (wd / "artifacts").exists():
        for p_ in (wd / "artifacts").glob("*.md"):
            if _complete(p_):
                done.add(p_.stem)
            else:
                print("re-batching incomplete artifact: %s" % p_.name)
    out = wd / "batches"; out.mkdir(exist_ok=True)

    # RACE GUARD, learned the hard way. This function deletes and rewrites the
    # batch files, and its glob also removes the *.input.json packets that
    # `prepare_batch.py` wrote. An agent that has already read its packet into
    # context is unaffected, but an agent that has not yet prepared will read a
    # batch id whose contents have changed under it. Rewriting mid-wave while
    # render agents were still writing artifacts is exactly what happened once.
    # `verify_batches.py` and `repair.py` already refuse on a warm log; this is
    # the same rule applied to the render side, keyed on the newest artifact.
    # Guard on artifact COUNT over a live sample, not on mtime. A render agent
    # ADDS artifacts, so the count grows; `repair.py` rewrites existing ones in
    # place, so it does not. Keying on mtime made this refuse 34 s after a repair
    # pass, which is the third time a guard mistook my own tooling's write for a
    # live wave -- mtime is simply the wrong signal for "is someone else working".
    # A PREFIXED lane does not need the liveness guard, and forcing past it is
    # the wrong way to say so. The guard exists to stop this function rewriting
    # batch files that a live agent is about to read; with --prefix, the delete
    # step only ever touches files carrying that prefix, so a lane whose prefix
    # has no batch files yet cannot disturb anybody. Another agent rendering in
    # the unprefixed namespace is exactly the situation this is meant to allow.
    art = wd / "artifacts"
    fresh_lane = bool(a.prefix) and not list((wd / "batches").glob("%s*.json" % a.prefix))
    if fresh_lane:
        print("prefixed lane '%s' with no existing batch files: the liveness guard does "
              "not apply, because this rebuild can only touch '%s*'." % (a.prefix, a.prefix))
    if art.exists() and not a.force and not fresh_lane:
        import datetime, time
        def count():
            return len(list(art.glob("*.md")))
        newest = max((f.stat().st_mtime for f in art.glob("*.md")), default=0.0)
        if datetime.datetime.now().timestamp() - newest < 600:
            first = count()
            time.sleep(20)
            if count() > first:
                print("render agents are live: artifact count grew from %d to %d during a "
                      "20 s sample." % (first, count()))
                print("Rebuilding batch files now would change what an unprepared agent "
                      "reads and deletes the .input.json packets.")
                print("Wait for the wave to drain, or pass --force if you are sure it is dead.")
                return 1

    kept_specs, kept_recs = set(), {}
    for k in keep:
        f = out / f"{k}.json"
        if f.exists():
            rec = json.load(open(f)); kept_recs[k] = rec
            kept_specs |= set(rec["spec_ids"])
    by = collections.defaultdict(list)
    for s in specs:
        if s["artifact_id"] not in done and s["artifact_id"] not in kept_specs:
            by[group_of(s)].append(s)
    pref = a.prefix
    for old in out.glob("*.json"):
        if old.stem in keep or old.stem == "index":
            continue
        if pref:
            if old.stem.startswith(pref):
                old.unlink()      # only this lane's own namespace
        elif not old.stem.startswith("V") and not any(
                old.stem.startswith(c) and old.stem[len(c):len(c)+1] in "TDF"
                for c in ("A", "B", "X", "Y", "Z")):
            old.unlink()          # V* belong to verify_batches.py; kept ids stay
    index = [dict(kept_recs[k]) for k in sorted(kept_recs)]
    by_id = {s["artifact_id"]: s for s in specs}

    def statute_rank(items):
        """Smallest statute lane first. A lane is the statute's target specs,
        the selection specs they link to, and its state-level documents."""
        lanes = collections.defaultdict(set)
        for s in items:
            sid = s.get("stat_id")
            if sid and s.get("target") and s.get("jur"):
                lanes[sid].add(s["artifact_id"])
                for tgt in s.get("links_to") or []:
                    if tgt in by_id: lanes[sid].add(tgt)
        for s in specs:
            sid = s.get("stat_id")
            if sid and not s.get("jur") and sid in lanes: lanes[sid].add(s["artifact_id"])
        order = sorted(lanes, key=lambda k: (len(lanes[k]), k))
        rank = {sid: i for i, sid in enumerate(order)}
        first_lane = {}
        for sid in order:
            for aid in lanes[sid]:
                first_lane.setdefault(aid, rank[sid])
        return lambda s: (first_lane.get(s["artifact_id"], len(order)),
                          s.get("jur") or "", s.get("stat_id") or "", s["kind"])

    for g, items in by.items():
        if a.priority == "statute" and g == "T":
            items.sort(key=statute_rank(items))
        else:
            items.sort(key=lambda s: (s.get("jur") or "", s.get("stat_id") or "", s["kind"]))
        budget = a.words_per_batch if g != "F" else int(a.words_per_batch * 1.4)
        used = {int(k[1:]) for k in keep if k.startswith(g) and k[1:].isdigit()}
        n = 0
        def next_id():
            nonlocal n
            while n in used: n += 1
            used.add(n); return f"{pref}{g}{n:02d}"
        cur, cw = [], 0
        for s in items:
            w = words_of(s)
            if cur and cw + w > budget:
                index.append(_write(out, next_id(), g, cur, cw)); cur, cw = [], 0
            cur.append(s); cw += w
        if cur:
            index.append(_write(out, next_id(), g, cur, cw))
    (out / "index.json").write_text(json.dumps(index, indent=1))
    for g in "TDF":
        bs = [b for b in index if b["group"] == g]
        print(f"group {g}: {len(bs)} batches, {sum(b['words'] for b in bs)} words, {sum(len(b['spec_ids']) for b in bs)} specs")
    print(f"{len(index)} batches -> {out.relative_to(ROOT)} (skipped {len(done)} already rendered)")


if __name__ == "__main__":
    main()
