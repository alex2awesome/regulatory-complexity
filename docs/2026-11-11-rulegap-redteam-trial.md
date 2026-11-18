# Red-team trial: how many readings differ from I* (2026-11-11)

**Exploratory.** LLM judges stand in for the three human E0 raters, so run status is `exploratory`, not validated.

## Result

- 194 readings proposed. 192 ran, 147 matched the plain words on core cases, 90 were judged defensible, and 42 were valid (judged defensible and code faithful).
- All 42 valid readings differ from I* somewhere. 41 of them open a loophole: they permit an action that I* forbids and P does not want.
- None of the 20 best good-faith readings matched I*. They agree with it on a median 83% of case-moves (maximum 97%).
- 40 of the 42 valid readings behave unlike any reading we authored.

| Draft | Words | Defined terms | Page-tree leaves | Valid | Valid, open a loophole | Loophole surface |
|---|---:|---:|---:|---:|---:|---:|
| no_exception | 8 | 0 | 3 | 11 | 10 | 4.6% |
| open | 13 | 0 | 4 | 8 | 8 | 19.5% |
| more_distinctions (tiers) | 20 | 0 | 7 | 14 | 14 | 19.5% |
| defined_purchase | 38 | 1 | 4 | 9 | 9 | 10.6% |
| fully_settled | 67 | 3 | 4 | 0 | 0 | 0% |

Loophole surface is the share of the 795 to 828 case-moves where I* is defined and some valid reading opens a loophole.

**Definitions shrink loopholes and branches grow them; word count alone predicts neither.**
- Each definition closed the loopholes it targeted, and the rest moved to the term left open. Under defined_purchase, self-declared emergencies are 396 of 480 loophole case-moves (82%).
- Under no_exception, splitting and relabelling dominate.

**Reading complexity, measured as AST nodes of the reading's code:**
- Valid loophole readings are not larger than invalid ones: median 212 against 251.
- Among valid loophole readings, adversarial runs are smaller than good-faith runs: 202 against 336.
- The median reading grows with the draft: 185 nodes (no_exception), 240 (open), 268 (defined_purchase), 325 (fully_settled).

**Judges:**
- Fleiss' κ on defensibility is 0.50 over 192 readings, and the yes rate is 54%.
- Sonnet said yes to 49% of Claude-written and 62% of GPT-written readings, so it did not favour its own family. The two GPT judges leaned slightly toward GPT-written readings: Luna 60% against 56%, Sol 50% against 43%.

## Setup

- **Spec:** `benchmark/rulegap/specs/procurement_v1.yaml`, with five rungs as drafts. Code: `benchmark/rulegap/redteam.py` and `sandbox_exec.py`. Run: `runs/rulegap_20261111/redteam/` (`launch.sh`, `drafts.csv`, `readings.csv`, `judge_agreement.json`, raw transcripts).
- **Generators:** `codex:gpt-5.6-luna` and `claude:claude-sonnet-5-5`. Per draft, each ran 3 adversarial replicates (up to 6 readings each, as permissive as is defensible) and 2 good-faith replicates (best reading first, plus up to 2 alternatives). That makes 50 calls. Each reading is a definition sentence plus `def legal(situation, action)` over the visible case file.
- **Panel:** 60 declared, 60 stress, 10 control and 8 witness cases, each with 6 candidate moves (828 pairs).
- **Execution:** readings run in a separate `python -I` process with an import allowlist and reduced builtins.
- **Validity, all required:**
  1. The code runs with no errors.
  2. It matches the plain-words verdict on every core case for that draft (4 to 9 cases; `CORE` in `redteam.py`).
  3. At least 2 of 3 judges (`codex:gpt-5.6-luna`, `codex:gpt-5.6-sol`, `claude:claude-sonnet-5-5`) rate it defensible.
  4. At least 2 of 3 judges rate the code faithful to its stated definition.
- **Judging:** judges saw the draft text, the background, and shuffled chunks of 8 readings, without generator, arm or rationale. That was 75 calls.
- **Checks:**
  - At creation: I* gives every core verdict on every draft (asserted in `execute`). A hand-coded Python copy of I* matched I* on all 795 defined pairs and mapped back to the authored I* assignment.
  - Sensitivity: dropping the `declared_safety` core case leaves every valid count unchanged, and fully_settled still has 0 valid readings.
- **Transport:** no failures. 2 readings failed execution (kept). Claude calls cost $2.22; codex calls run on the subscription and report no cost.

## Caveats

- **Judges:** LLM judges are a proxy, and κ = 0.50 is moderate. The 42 valid readings should go to the human E0 raters.
- **Scope:** one toy domain, one run, and CLI wrappers, so model and wrapper are confounded.
- **Authored references:** I*, P and the core cases are ours. Some differences come from how the case generator writes descriptions: an unrelated prior order shares the "other" description used by the relabel move.
- **Fully defined draft:** 27 of 37 readings failed the plain safety case (24 failed only that case; corrected from 25 on 2026-11-11). They required the emergency declaration itself to mention safety and ignored the requester's note that people were at risk of injury. The zero for that draft rests on characterization failures as well as on narrowed readings.
- **Non-loophole differences:** many restrictive differences come from readings that treat the whole request as the purchase. Those readings forbid the first half of a split order, which I* allows.
- **Cells (Alex, 2026-11-11):** drafting failure (I* legal, P unwanted) is merged into loophole, where it is the strain-0 case. No panel pair is I*-legal and unwanted on any draft, so every count above is unchanged; every loophole here has strain 1 or more.
