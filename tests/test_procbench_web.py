"""Mock web + solver harness tests against the hand-written fixture world.

Run:  python3 tests/test_procbench_web.py
No LLM calls: the solver test monkeypatches pipeline.llm.llm_json with a canned
tool call followed by a finish.
"""

import json
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pipeline import llm
from pipeline.procbench import solve, web

WORLD = "_fixture"
WORLD_DIR = REPO / "benchmark" / "synth" / "worlds" / WORLD
RUNS = pathlib.Path(tempfile.mkdtemp(prefix="procbench_runs_"))
PROGRAM = "https://www.halvern.gov/building/unit-legalization"
REDDIT = "https://www.reddit.com/r/Halvern/comments/8fq2k1/legalizing_an_unpermitted_unit_in_halvern_61_days/"

# ---------------------------------------------------------------- build
shutil.rmtree(WORLD_DIR / "web", ignore_errors=True)
stats = web.build(WORLD_DIR)
assert stats["pages"] == 10 and stats["reddit"] == 2, stats
assert stats["targets"] == 9, stats                         # 3 of the 12 artifacts are distractors
for name in ("pages", "reddit", "links", "bm25"):
    assert (WORLD_DIR / "web" / f"{name}.json{'l' if name != 'bm25' else ''}").exists(), name
rows = [json.loads(l) for l in (WORLD_DIR / "web" / "links.jsonl").read_text().splitlines()]
assert {r["to_url"] for r in rows if r["from_url"] == PROGRAM} == {
    "https://www.halvern.gov/finance/fee-schedule-2025",
    "https://www.halvern.gov/forms/bld-214-unit-legalization.pdf",
    "https://www.halvern.gov/building/unit-legalization/faq",
    "https://library.halvern.gov/ordinances/24-118"}, rows

# ---------------------------------------------------------------- search (default condition)
w = web.World(WORLD, "search", run_id="t_search", runs_root=RUNS)
hits = w.search("how do I legalize an unpermitted unit in Halvern", k=5)
assert hits[0]["url"] == PROGRAM, [h["url"] for h in hits]           # natural query finds the program page
assert hits[0]["snippet"] and hits[0]["kind"] == "program_page"
fees = w.search("how much does unit legalization cost in Halvern", k=5)
assert fees[0]["url"] == "https://www.halvern.gov/finance/fee-schedule-2025", [h["url"] for h in fees]
# the county look-alike is reachable in `search` — that is the disentanglement trap
assert any("marisolcounty" in h["url"] for h in w.search("unpermitted structure septic evaluation", k=5))

page = w.fetch(PROGRAM, max_chars=100000)
assert "Certificate of Legalization" in page["text"] and len(page["links"]) == 4, page.get("links")
assert w.fetch("https://www.halvern.gov/no-such-page")["error"].startswith("404")

r = w.search("how long did the unit legalization take", k=5, reddit_only=True)
assert [h["kind"] for h in r] == ["reddit_thread"] * len(r) and r
th = w.thread("t_8fq2k1", max_chars=100000)
assert "I work at the counter" in th["text"] and th["subreddit"] == "r/Halvern"
assert w.thread("t_nope")["error"].startswith("404")
assert w.search("unpermitted unit", k=5, reddit_only=True, sub="r/MarisolValley")[0]["thread_id"] == "t_3kd92m"

# ---------------------------------------------------------------- condition filters
d = web.World(WORLD, "declared_only", run_id="t_declared", runs_root=RUNS)
kinds = {h["kind"] for h in d.search("unpermitted unit legalization timeline fee", k=12)}
assert not (kinds & {"reddit_thread", "forum_thread", "staff_report", "news"}), kinds
assert d.search("unit legalization how long did it take", k=5, reddit_only=True) == []
assert d.fetch(REDDIT)["error"].startswith("404")                    # hidden, not just unranked
assert d.fetch(PROGRAM).get("text")                                  # city pages still reachable

u = web.World(WORLD, "declared_plus_users", run_id="t_users", runs_root=RUNS)
assert u.thread("t_8fq2k1").get("text")                              # user reports allowed
assert u.fetch("https://www.halvern.gov/council/agendas/2025-03-11/item-7-staff-report.pdf"
               )["error"].startswith("404")                          # designed tier hidden
assert web.World(WORLD, "search", runs_root=RUNS).fetch(
    "https://www.halvern.gov/council/agendas/2025-03-11/item-7-staff-report.pdf").get("text")

nd = web.World(WORLD, "oracle_no_distractors", runs_root=RUNS)
assert not [h for h in nd.search("unpermitted structure sidewalk vending", k=12)
            if h["artifact_id"] in ("J3__S03__program_page", "J1__S07__program_page")]

# ---------------------------------------------------------------- oracle document sets
docs = w.oracle_docs("J1", "S03", query="unit legalization Halvern", include_distractors=True)
ids = [d_["id"] for d_ in docs]
assert {i for i in ids if i.startswith("J1__S03")} == {
    f"J1__S03__{s}" for s in ("program_page", "fee_schedule", "form", "faq", "ordinance",
                              "staff_report", "reddit")}, ids
assert ids[0] == "J1__S03__program_page" and len(ids) > 7, ids       # targets first, then contamination
clean = [d_["id"] for d_ in w.oracle_docs("J1", "S03", include_distractors=False)]
assert len(clean) == 7 and all(i.startswith("J1__S03") for i in clean), clean

# ---------------------------------------------------------------- trace
trace = [json.loads(l) for l in (RUNS / "t_search" / "trace.jsonl").read_text().splitlines()]
ops = [t["op"] for t in trace]
assert ops[:3] == ["search", "search", "search"] and "fetch" in ops and "reddit_thread" in ops, ops
assert all(set(t) == {"ts", "condition", "op", "args", "result_ids"} for t in trace)
assert trace[0]["condition"] == "search" and trace[0]["result_ids"][0] == "J1__S03__program_page"
miss = [t for t in trace if t["op"] == "fetch" and not t["result_ids"]]
assert miss, "the 404 fetch should be traced with no result_ids"
dtrace = [json.loads(l) for l in (RUNS / "t_declared" / "trace.jsonl").read_text().splitlines()]
assert {t["condition"] for t in dtrace} == {"declared_only"}
assert not (RUNS / "nd").exists()                                    # no run_id -> no trace

# ---------------------------------------------------------------- solver with a fake backend
CALLS = []
CANNED = [
    {"op": "search", "args": {"query": "Halvern unit legalization", "k": 3}},
    {"op": "fetch", "args": {"url": PROGRAM}},
    {"op": "reddit_thread", "args": {"thread_id": "t_8fq2k1"}},
    {"op": "bogus_op", "args": {}},
    {"op": "finish", "model": {
        "model_id": "_fixture__J1__S03", "source": "declared", "jurisdiction": "City of Halvern",
        "actors": ["applicant", "permit_center", "plans_examiner", "inspector"],
        "activities": [
            {"id": "A01", "name": "Pre-application meeting", "actor": "permit_center", "occasion": "counter",
             "visibility": "applicant_facing", "timing": {"median_days": 11, "range": [3, 20], "basis": "reddit"},
             "fee": None, "rework": None, "confidence": 0.9, "evidence": [PROGRAM]},
            {"id": "A02", "name": "Submit BLD-214", "actor": "applicant", "occasion": "online",
             "visibility": "applicant_facing", "timing": {"median_days": 1, "range": [1, 1], "basis": "page"},
             "fee": {"amount": 430, "when": "at submittal"}, "rework": None, "confidence": 0.95,
             "evidence": [PROGRAM]},
            {"id": "A05", "name": "Plan review", "actor": "plans_examiner", "occasion": "internal",
             "visibility": "applicant_inferable", "timing": {"median_days": 21, "range": [10, 60], "basis": "reddit"},
             "fee": None, "rework": {"p_trigger": 0.35, "back_to": "A02", "reason": "corrections"},
             "confidence": 0.8, "evidence": ["t_8fq2k1"]}],
        "edges": [{"from": "A01", "to": "A02", "type": "sequence"},
                  {"from": "A02", "to": "A05", "type": "handoff"},
                  {"from": "A05", "to": "A02", "type": "rework", "condition": "corrections issued"}],
        "terminal_artifact": "Certificate of Legalization",
        "process_timing": {"median_days": 55, "p90_days": 98, "range": [38, 98], "basis": "one reddit timeline, debiased"},
        "unknowns": [{"what": "internal routing steps", "why_unknown": "no public document states it"}]}},
]


def fake_llm_json(prompt_file, body, schema_file=None, model=None, extra="", max_tokens=16000):
    CALLS.append({"prompt_file": pathlib.Path(prompt_file).name, "body": body, "extra": extra})
    return CANNED[len(CALLS) - 1] if len(CALLS) <= len(CANNED) else CANNED[-1]


llm.llm_json = fake_llm_json
args = solve.build_parser().parse_args(
    ["--world", WORLD, "--task", "_fixture__J1__S03", "--condition", "search",
     "--run-id", "t_agent", "--runs-root", str(RUNS), "--max-steps", "8"])
meta = solve.solve(args, "t_agent")
assert meta["finished"] and meta["mode"] == "agent" and meta["error"] is None, meta
assert meta["steps"] == 5 and len(CALLS) == 5, (meta, len(CALLS))
assert not meta["schema_errors"], meta["schema_errors"]
pred = json.loads((RUNS / "t_agent" / "pred.json").read_text())
assert len(pred["activities"]) == 3 and pred["task_id"] == "_fixture__J1__S03"
assert any(e["type"] == "rework" for e in pred["edges"]) and pred["unknowns"]
assert pred["procbench"]["condition"] == "search" and pred["procbench"]["steps"] == 5
tr = json.loads((RUNS / "t_agent" / "transcript.json").read_text())
assert PROGRAM in tr["steps"][0]["observation"], tr["steps"][0]["observation"][:200]
assert "Certificate of Legalization" in tr["steps"][1]["observation"]
assert "unknown op" in tr["steps"][3]["observation"]                 # bad op -> error observation, loop continues
agent_trace = [json.loads(l) for l in (RUNS / "t_agent" / "trace.jsonl").read_text().splitlines()]
assert [t["op"] for t in agent_trace] == ["search", "fetch", "reddit_thread"], agent_trace
assert "step 2 of 8" in CALLS[1]["extra"] and "solve_agent.md" == CALLS[0]["prompt_file"]
assert "step 1 observation" in CALLS[1]["body"]                      # the transcript is fed back

CALLS.clear()
CANNED[:] = [CANNED[-1]["model"]]                                    # oracle returns the model directly
oargs = solve.build_parser().parse_args(
    ["--world", WORLD, "--task", "_fixture__J1__S03", "--condition", "oracle_no_distractors",
     "--run-id", "t_oracle", "--runs-root", str(RUNS)])
ometa = solve.solve(oargs, "t_oracle")
assert ometa["mode"] == "oracle" and ometa["finished"] and ometa["steps"] == 1, ometa
assert CALLS[0]["prompt_file"] == "solve_oracle.md"
body = CALLS[0]["body"]
assert body.count("=== DOCUMENT ") == 7 and "Second-level sign-off" in body
assert "marisolcounty" not in body and "22.190" not in body          # distractor docs removed
assert json.loads((RUNS / "t_oracle" / "pred.json").read_text())["condition"] == "oracle_no_distractors"

shutil.rmtree(RUNS, ignore_errors=True)
print("test_procbench_web OK")
print(f"  world {WORLD}: {stats['pages']} pages, {stats['reddit']} threads, {stats['links']} links, "
      f"{stats['targets']}/12 target artifacts")
print(f"  conditions checked: {', '.join(web.CONDITIONS)}")
print(f"  agent run: 5 steps, 3 traced web calls, {len(pred['activities'])} predicted activities")
