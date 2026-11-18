# rulegap: rules, readings and loopholes

Code for the letter-versus-spirit project at Stanford RegLab. A **rule** is a
text `c`. A **reading** `I` turns the text into a decision: given a raw case and an action, it returns
legal, illegal or undefined. `Adm(c)` is the set of readings the text admits. `I*` is the governing
reading and `P` the rule's purpose. An action is a **loophole** when some admissible reading allows it,
`I*` forbids it, and `P` does not want it.

Everything here is synthetic or exploratory. Nothing has passed the human rater check (E0).

## Two synthetic administrative-law toys

| Toy | Text | What is planted |
|---|---|---|
| Procurement bidding rule | "Any purchase over $100,000 requires three competitive bids, unless there is an emergency." (`specs/procurement_v1.yaml`, rung `open`; other rungs add definitions, drop the exception or add a tier) | Open terms PURCHASE, its window W, EMERGENCY, BID, each with printed readings and an intended one; raw cases of past orders, bids and declarations |
| Backyard Hen Keeping Act | Five sections: permit, application with site plan, nuisance determination, 30-day deadline, reasonable fee (`toys/hens/hen_package.json`, `text`) | Six yes/no interpretive questions (`questions`), validity rules per answer, and the six candidate procedures towns choose from (`design_space`) |

The hens package also carries the hidden world used by the Bayesian process fits (`truth`). Ignore it for
interpretation work.

## Layout

| File | What it does |
|---|---|
| `spec.py`, `dsl.py` | Load a YAML spec; readings are expressions in a three-valued (legal / illegal / undefined) logic over named features of the raw case |
| `compile.py` | Turn a spec plus one choice of reading per term into an executable decision function; classify an action into the five cells |
| `render.py`, `arms.py` | Render each rule variant to text deterministically; parse the definitions back out as a check |
| `cases.py`, `domains/` | Raw case generators for procurement, percentile and the Kripke "add" control |
| `readings.py`, `search.py`, `trees.py`, `metrics.py` | Behavioural classes of readings, loophole and conflict search (exhaustive, or Z3 if installed), decision trees, complexity measures |
| `admissibility.py`, `real.py` | Candidate versus sourced versus human-validated readings; the E0 rater packet |
| `harness/` | Agent episodes with JSON tool calls over the `codex` and `claude` CLIs |
| `redteam.py`, `sandbox_exec.py` | Models write readings of each draft as code; we run them on the case panel and judge them |
| `agent_airline.py`, `agent_constitution.py`, `gemma_agents.py` | Which reading do agents act on (tau2 airline "modify" clause; a store policy under the OpenAI Model Spec) |
| `question_tree.py` | Question-asking interpreter pilot: text to a tree that keeps the rule's words, plus the interpretive questions and candidate answers; recall against the planted questions in both toys |
| `real/` | Real cases: percentile (SRE Workbook SLO line), airline policy, Model Spec, each with a source manifest |

## Running

```sh
pip install -r requirements-rulegap.txt pytest
python -m pytest tests/test_rulegap*.py -q            # offline; no model calls
python -m benchmark.rulegap.cli validate benchmark/rulegap/specs/procurement_v1.yaml
python -m benchmark.rulegap.cli measure  benchmark/rulegap/specs/procurement_v1.yaml --out /tmp/measures
python -m benchmark.rulegap.question_tree prompts      # print the interpreter prompts
python -m benchmark.rulegap.question_tree run --out runs/question_tree   # needs codex and claude CLIs
```

Model calls go through the `codex exec` and `claude -p` command-line tools (`harness/model.py`). Runs
write raw replies, parsed replies and errors next to each other and never retry silently.

## Results so far (in `docs/`)

- `2026-11-11-rulegap-toy-results.md`: agents on the toy rules.
- `2026-11-11-rulegap-redteam-trial.md`: 194 model-written readings of five procurement drafts; 42 pass
  the judges, 41 of those open a loophole; definitions shrink the loophole surface.
- `2026-11-11-rulegap-agent-readings.md`: behaviour on designed cases shows which reading an agent acts on.
- `2026-11-17-question-tree-pilot.md`: how many planted interpretive questions a model raises unprompted.

## Not included

Run outputs, the internal experiment plan, and fetched third-party web pages for the percentile case
(their URLs and hashes are in `real/percentile/sources/manifest.jsonl`).
