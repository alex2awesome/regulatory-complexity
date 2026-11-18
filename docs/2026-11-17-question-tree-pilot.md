# Question-asking interpreter: pilot (2026-11-17)

**Exploratory.** One prompt, two generators, three samples each, one LLM matcher. No human check.

## Result

Models find the questions about what a word means, and miss the questions about procedure.

| Law | Planted | Sonnet 5.5, found per sample | Luna, found per sample | Never raised by any sample |
|---|---|---|---|---|
| Procurement (term meanings) | 4 | 3, 3, 4 | 3, 3, 3 | none (W raised once in 6) |
| Hens act (procedure) | 6 | 4, 2, 3 | 0, 0, 2 | Q3 power to require attendance; Q4 clock runs through the nuisance step |

- **Procurement:** PURCHASE, EMERGENCY and BID were raised in all 6 samples. The window W was raised once.
  Of the 11 planted answers, 6 to 10 appeared per sample. All four emergency readings and both bid readings
  show up. For PURCHASE, "same need" aggregation appears in 5 of 6 samples, but "same description of need"
  and "same vendor per year" only once each. Those two are the loophole readings.
- **Hens:** the planted questions are all about procedure: what the nuisance determination requires, who must
  be heard, what powers it implies, whether the clock runs through it, what fees it allows, and whether the
  grounds for denial are limited. The models instead ask what "nuisance", "adjoining", "complete" and
  "reasonable" mean. Luna asked 17 to 24 questions per sample and matched no planted question in two samples.
- **Most generated questions were not planted:** 6 to 22 per sample on the hens act, 7 to 9 on procurement.
  Many are real issues our toys never modelled (calendar or business days, deemed approval on a missed
  deadline, conditional permits, whether the emergency must relate to the purchase, sole source). See the
  draft assumption set below.
- **Scripted check passed:** every node quote and every "open words" span is verbatim in the rule (0 failures
  in 12 replies).
- **Spot check of the matcher** (Luna hens s0, Sonnet hens s1): its no-match calls hold; one borderline miss
  (Sonnet's evidence-standard question also mentions neighbour objections, which touches Q2). Recall is if
  anything a slight undercount.
- **Spend:** $2.21 on Claude (generation and matching); Luna through the codex subscription.

**What it means for the interpreter.** For administrative law, a generic "what is ambiguous here?" prompt
is not enough. It surfaces word meanings and misses implied procedure. The generator needs question templates
per node type: for a determination, what steps, evidence and participation it requires; for a deadline, when
it starts, what tolls it and what happens on a miss; for a fee, its scope and amount; for an exception, who
invokes it and how far it reaches.

## What was tested

From the 2026-11-12 meeting with Isabel: instead of translating a rule straight into code, ask a model
which interpretive questions an official would need answered, and branch on the answers. The pilot asks:
given only the text of a synthetic administrative rule, does a model raise the questions we planted?

- **Laws:** two synthetic administrative-law toys with planted interpretive questions.
  - Backyard Hen Keeping Act (permit procedure). Six planted yes/no questions, from the toy's statute
    package: desk review sufficient, neighbour input required, power to require attendance, clock runs
    through the nuisance step, separate fees allowed, grounds for denial limited.
  - Procurement bidding rule, open draft: "Any purchase over $100,000 requires three competitive bids,
    unless there is an emergency." Four planted questions, one per open term of `procurement_v1.yaml`
    (PURCHASE, window W, EMERGENCY, BID), with the spec's printed readings as answers (11 in total).
- **Generators:** `codex:gpt-5.6-luna` and `claude:claude-sonnet-5-5`, 3 samples each per law, blind to the
  planted questions. Each returns (a) nodes that quote the rule verbatim, (b) interpretive questions with
  two to five candidate answers labelled by textual support, (c) words treated as settled.
- **Matcher:** `claude:claude-opus-5-5` maps each generated question to a planted one or to none, and lists
  which planted answers appear among the generated answers.
- **Scripted check:** every node quote and every question's "open words" must be a verbatim span of the
  rule (`anchor_failures`).

Code: `benchmark/rulegap/question_tree.py`. Run: `runs/rulegap_20261117/question_tree/` (`launch.sh`,
`generated/`, `matched_opus/`, `rows.json`, `summary.json`, `settled.json`, `new_questions.json`).

## Failures kept

- The first matcher, `codex:gpt-5.6-sol`, returned 403 Forbidden on all six calls it got
  (`matched/*.error.json`). The matcher was switched to Claude Opus 5.5, which is not one of the generators.
- The claude CLI does not enforce the output schema; Sonnet chose its own key names (`node_id`,
  `rule_words`, `candidates`, `label`, `phrase`). `normalize` maps them; no reply was dropped.

## Caveats

- The matcher is one LLM. A wrong match moves recall directly. Spot-check before citing numbers.
- Planted spaces are ours. A generated question the toy did not plant is not wrong; many are real open
  issues our toys never modelled. They are listed in `new_questions.json` as input to the assumption set.
- Three samples per cell; no seeds on either CLI.

## Draft assumption set

The issues below were raised by the models but are not planted. For each, a conservative default we would
adopt as agreed, or a flag to plant it as a real question. Defaults apply only to the synthetic toys.

**Hens act**

| Issue raised | Default | Plant it? |
|---|---|---|
| Who is a resident; what is a single-family dwelling | Anyone living in a detached one-household house, owner or tenant | no |
| Is the six-hen cap per dwelling or per person; are roosters or chicks hens | Per dwelling; female chickens of any age; roosters excluded | no |
| What the site plan must show; to scale or surveyed | Coop location and distance to every property line; no survey | no |
| Calendar or business days; what counts as receipt | Calendar days from the day a complete application is received | no |
| What happens if the authority misses the 30 days | Silent text: no deemed approval | yes: deemed approval is a live administrative-law question (California's ADU law has one) |
| May the permit carry conditions | Grant or deny only | yes: conditions are how agencies resolve nuisance in practice |
| What "nuisance" covers | Left open as a judgment node (noise, odour, pests) | already open by design |
| Must a denial give reasons; appeal rights | Written reasons; no appeal in the act | no |
| Is the fee discretionary; may it vary | Discretionary; one flat amount per application | covered by Q5 |

**Procurement rule**

| Issue raised | Default | Plant it? |
|---|---|---|
| Which transactions are purchases (leases, services, renewals) | Goods and services, including leases and renewals | no |
| Does the amount include tax and shipping; estimated or final | Total estimated price at request, including tax and shipping | no |
| "Three" bids: exactly or at least | At least three | no |
| What makes bids competitive (independent, responsive vendors) | Independent vendors quoting the same specification | no |
| Fewer than three respond, or one supplier exists | Not covered: the rule forbids the order | yes: sole source is the standard real-world exception |
| Does the emergency exception reach only the purchase that answers the emergency | Only that purchase | yes: buying unrelated goods during a declared emergency is a loophole reading |
| Does the emergency waive bidding entirely or only shorten it; how long it lasts | Waives it for that purchase only | no |
| Documentation of bids | Not modelled | no |

